# -*- coding: utf-8 -*-
"""孤儿用户清理 · 幂等 · 默认 dry-run。

孤儿用户 = users.tenant_id 指向已删租户(无 FK 约束,删租户时 tenant_id 不级联)。
这类行无法正常登录/工作,且会让 ensure_credits_tables 的 step 7 INSERT 违反
user_company_roles_tenant_id_fkey,导致整个建表事务回滚、启动日志每次报 ERROR
(代码侧已加 EXISTS 守门根治,见 services/billing/credits_schema.py;本脚本清存量)。

清理动作(停用而非删除,保留审计行,可逆):
  is_active = FALSE
  tenant_id = NULL                       ← 断开悬挂指针,清零孤儿计数
  notes    += " [orphan-cleanup <date> was tenant=<id>]"

幂等:清理后 tenant_id 为 NULL,再跑匹配 0 行,空操作。

用法(prod):
  ssh pearnly → cd /opt/mrpilot → set -a; . ./.env; set +a →
    PYTHONPATH=/opt/mrpilot venv/bin/python scripts/cleanup_orphan_users.py        # dry-run
    PYTHONPATH=/opt/mrpilot venv/bin/python scripts/cleanup_orphan_users.py --apply # 执行
"""

import argparse
import os
import sys

import psycopg2
from psycopg2.extras import RealDictCursor

ORPHAN_WHERE = """
    u.tenant_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM tenants t WHERE t.id = u.tenant_id)
"""


def _fetch_orphans(cur):
    cur.execute(f"""
        SELECT u.id, u.email, u.company_name, u.is_active,
               u.tenant_id, u.created_at, u.last_login_at
        FROM users u
        WHERE {ORPHAN_WHERE}
        ORDER BY u.created_at
        """)
    return cur.fetchall()


def _print_impact(rows):
    print(f"\n影响面:{len(rows)} 个孤儿用户(tenant_id 指向已删租户)\n")
    if not rows:
        return
    print(f"  {'user_id':36}  {'email':24}  {'company_name':36}  active  created")
    for r in rows:
        print(
            f"  {str(r['id']):36}  {(r['email'] or '—'):24}  "
            f"{(r['company_name'] or '—')[:36]:36}  {str(r['is_active']):6}  "
            f"{r['created_at']:%Y-%m-%d}"
        )
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="清理孤儿用户(默认 dry-run)")
    parser.add_argument("--apply", action="store_true", help="真正执行(否则只打印影响面)")
    args = parser.parse_args()

    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("DATABASE_URL 未设置", file=sys.stderr)
        return 2

    conn = psycopg2.connect(url, sslmode="require")
    conn.autocommit = False
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            rows = _fetch_orphans(cur)
            _print_impact(rows)

            if not rows:
                print("无孤儿用户,空操作。")
                conn.rollback()
                return 0

            if not args.apply:
                print("dry-run:未改动。加 --apply 执行上述停用。")
                conn.rollback()
                return 0

            cur.execute(f"""
                UPDATE users u SET
                    is_active = FALSE,
                    notes = COALESCE(u.notes, '')
                        || ' [orphan-cleanup ' || to_char(NOW(), 'YYYY-MM-DD')
                        || ' was tenant=' || u.tenant_id::text || ']',
                    tenant_id = NULL
                WHERE {ORPHAN_WHERE}
                """)
            affected = cur.rowcount
            conn.commit()
            print(f"已停用并断开 {affected} 个孤儿用户(is_active=FALSE, tenant_id=NULL)。")

            remaining = _fetch_orphans(cur)
            print(f"复查剩余孤儿:{len(remaining)}")
            return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
