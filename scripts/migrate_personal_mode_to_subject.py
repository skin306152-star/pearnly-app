# -*- coding: utf-8 -*-
"""个人模式 → 个人主体迁移 · 幂等 · 默认 dry-run。高敏(动存量用户数据)。

背景:用户引导闭环(docs/onboarding/00)用正经「个人主体」(subject_type=personal)
替代旧的脏「个人模式」(纯前端 work_mode=personal · 后端无此字段)。个人模式下用户
未选账套主体,其历史 ocr_history.workspace_client_id 为 NULL。

迁移:对【只用过个人模式】的账户(有 NULL-workspace 的 ocr_history 且无任何在用账套
主体)建一个 personal 主体,并把其 NULL-workspace 历史归入(正式归属)。注:在此之前
因隔离子句 `OR workspace_client_id IS NULL` 历史本就对该 scope 可见,数据不会丢;回填
只是把它正式挂到个人主体名下(计入统计、survive 后续 PO-8 收口)。

scope(与 workspace_clients 隔离一致):有租户按 tenant_id(主体租户共享)· 无租户按
user_id。每 scope 至多一个在用 personal 主体(T1 部分唯一索引兜底)。

幂等:建主体后该 scope 即有在用主体 → 复跑不再是候选;回填只动仍为 NULL 的行。

⚠️ 高敏:动存量用户数据。先 dry-run 报数交 Zihao 看,确认后才 --apply。
   未拍板前绝不对 prod --apply。

用法(prod):
  ssh pearnly → cd /opt/mrpilot → set -a; . ./.env; set +a →
    PYTHONPATH=/opt/mrpilot venv/bin/python scripts/migrate_personal_mode_to_subject.py
    PYTHONPATH=/opt/mrpilot venv/bin/python scripts/migrate_personal_mode_to_subject.py --apply
"""

import argparse
import os
import sys

import psycopg2
from psycopg2.extras import RealDictCursor

DEFAULT_PERSONAL_NAME = "ส่วนตัว"  # 个人 · 泰语(首发市场默认)


def find_tenant_candidates(cur):
    """有租户、有 NULL-workspace 历史、且无任何在用账套主体的租户(=只用过个人模式)。"""
    cur.execute("""
        SELECT oh.tenant_id AS tenant_id, COUNT(*) AS null_ocr_count
        FROM ocr_history oh
        WHERE oh.tenant_id IS NOT NULL
          AND oh.workspace_client_id IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM workspace_clients wc
              WHERE wc.tenant_id = oh.tenant_id AND wc.is_active = TRUE
          )
        GROUP BY oh.tenant_id
        ORDER BY oh.tenant_id
        """)
    return [dict(r) for r in (cur.fetchall() or [])]


def find_user_candidates(cur):
    """无租户用户(tenant_id NULL)、有 NULL-workspace 历史、且无在用个人 scope 主体。"""
    cur.execute("""
        SELECT oh.user_id AS user_id, COUNT(*) AS null_ocr_count
        FROM ocr_history oh
        WHERE oh.tenant_id IS NULL
          AND oh.workspace_client_id IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM workspace_clients wc
              WHERE wc.tenant_id IS NULL AND wc.user_id = oh.user_id AND wc.is_active = TRUE
          )
        GROUP BY oh.user_id
        ORDER BY oh.user_id
        """)
    return [dict(r) for r in (cur.fetchall() or [])]


def owner_of_tenant(cur, tenant_id):
    """租户 owner(建主体归属人):优先 role=owner / invited_by 为空 · 否则最早成员。"""
    cur.execute(
        """
        SELECT id, company_name, email
        FROM users
        WHERE tenant_id = %s
        ORDER BY (role = 'owner') DESC, (invited_by IS NULL) DESC, created_at ASC
        LIMIT 1
        """,
        (tenant_id,),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def personal_name(owner):
    """个人主体名:公司名 → 邮箱前缀 → 泰语「个人」兜底。"""
    if owner:
        company = (owner.get("company_name") or "").strip()
        if company:
            return company[:200]
        email = (owner.get("email") or "").strip()
        if email and "@" in email:
            return email.split("@", 1)[0][:200]
    return DEFAULT_PERSONAL_NAME


def _existing_personal(cur, *, user_id, tenant_id):
    if tenant_id is not None:
        cur.execute(
            "SELECT id FROM workspace_clients WHERE tenant_id = %s "
            "AND subject_type = 'personal' AND is_active = TRUE ORDER BY id LIMIT 1",
            (tenant_id,),
        )
    else:
        cur.execute(
            "SELECT id FROM workspace_clients WHERE user_id = %s AND tenant_id IS NULL "
            "AND subject_type = 'personal' AND is_active = TRUE ORDER BY id LIMIT 1",
            (str(user_id),),
        )
    row = cur.fetchone()
    return int(row["id"]) if row else None


def create_personal_subject(cur, *, user_id, tenant_id, name):
    """建 personal 主体(零税号 · vat 未注册)。已存在则返回既有 id(幂等)。"""
    existing = _existing_personal(cur, user_id=user_id, tenant_id=tenant_id)
    if existing:
        return existing
    cur.execute(
        """
        INSERT INTO workspace_clients
            (user_id, tenant_id, name, subject_type, vat_registered, is_active)
        VALUES (%s, %s, %s, 'personal', FALSE, TRUE)
        RETURNING id
        """,
        (str(user_id), tenant_id, name),
    )
    row = cur.fetchone()
    return int(row["id"]) if row else None


def backfill_history(cur, *, subject_id, tenant_id, user_id):
    """把该 scope 仍为 NULL 的 ocr_history 归入个人主体。返回回填行数。"""
    if tenant_id is not None:
        cur.execute(
            "UPDATE ocr_history SET workspace_client_id = %s "
            "WHERE tenant_id = %s AND workspace_client_id IS NULL",
            (int(subject_id), tenant_id),
        )
    else:
        cur.execute(
            "UPDATE ocr_history SET workspace_client_id = %s "
            "WHERE user_id = %s AND tenant_id IS NULL AND workspace_client_id IS NULL",
            (int(subject_id), str(user_id)),
        )
    return cur.rowcount


def migrate(cur, apply):
    """扫候选 → (apply 时)建主体 + 回填历史。返回报告 dict。"""
    tenant_rows = find_tenant_candidates(cur)
    user_rows = find_user_candidates(cur)
    report = {
        "tenant_candidates": len(tenant_rows),
        "user_candidates": len(user_rows),
        "subjects_created": 0,
        "history_backfilled": 0,
        "details": [],
    }
    if not apply:
        for r in tenant_rows:
            report["details"].append(
                {"scope": "tenant", "id": str(r["tenant_id"]), "null_ocr": int(r["null_ocr_count"])}
            )
        for r in user_rows:
            report["details"].append(
                {"scope": "user", "id": str(r["user_id"]), "null_ocr": int(r["null_ocr_count"])}
            )
        return report

    for r in tenant_rows:
        tid = r["tenant_id"]
        owner = owner_of_tenant(cur, tid)
        if not owner:
            report["details"].append({"scope": "tenant", "id": str(tid), "skipped": "no_owner"})
            continue
        subj = create_personal_subject(
            cur, user_id=owner["id"], tenant_id=tid, name=personal_name(owner)
        )
        if not subj:
            report["details"].append(
                {"scope": "tenant", "id": str(tid), "skipped": "create_failed"}
            )
            continue
        moved = backfill_history(cur, subject_id=subj, tenant_id=tid, user_id=owner["id"])
        report["subjects_created"] += 1
        report["history_backfilled"] += moved
        report["details"].append(
            {"scope": "tenant", "id": str(tid), "subject_id": subj, "backfilled": moved}
        )

    for r in user_rows:
        uid = r["user_id"]
        subj = create_personal_subject(cur, user_id=uid, tenant_id=None, name=DEFAULT_PERSONAL_NAME)
        if not subj:
            report["details"].append({"scope": "user", "id": str(uid), "skipped": "create_failed"})
            continue
        moved = backfill_history(cur, subject_id=subj, tenant_id=None, user_id=uid)
        report["subjects_created"] += 1
        report["history_backfilled"] += moved
        report["details"].append(
            {"scope": "user", "id": str(uid), "subject_id": subj, "backfilled": moved}
        )
    return report


def _print_report(report, apply):
    print(
        f"\n候选:{report['tenant_candidates']} 租户 + {report['user_candidates']} 无租户用户"
        f"(只用过个人模式 · 有 NULL-workspace 历史 · 无在用主体)\n"
    )
    for d in report["details"]:
        print(f"  {d}")
    if apply:
        print(
            f"\n已建个人主体 {report['subjects_created']} 个 · "
            f"回填历史 {report['history_backfilled']} 行。"
        )
    else:
        print("\ndry-run:未改动。确认数字后加 --apply 执行。")


def main():
    parser = argparse.ArgumentParser(description="个人模式 → 个人主体迁移(默认 dry-run)")
    parser.add_argument("--apply", action="store_true", help="真正执行(否则只报数)")
    args = parser.parse_args()

    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("DATABASE_URL 未设置", file=sys.stderr)
        return 2

    conn = psycopg2.connect(url, sslmode="require")
    conn.autocommit = False
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            report = migrate(cur, args.apply)
            _print_report(report, args.apply)
            if args.apply:
                conn.commit()
            else:
                conn.rollback()
            return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
