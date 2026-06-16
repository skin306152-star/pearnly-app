# -*- coding: utf-8 -*-
"""待归类下线:把存量 pending intake_items 转成采购草稿,再 DROP 表 · 默认 dry-run。

背景:待归类(intake_items)模块下线 —— 识别完的票一律建成草稿落采购列表,用户在列表里
改方向/补金额/删,不再单独兜一个待归类桶。本脚本把表里仍 pending 的项(用户发过但没归类
的真票)按新口径转成 purchase_docs 草稿(status='draft'),不丢数据;全部转完后(--drop-table)
DROP 表。

复用 services.purchase.intake.build_draft_from_invoice + docs.create_doc(与 app 同一建单链路,
不重写)。每项独立 try/except:个别糊图/重复转换失败只记录跳过,不影响其它项。

⚠️ 动存量数据 + DROP 表:先 dry-run 报数 → --apply 转草稿 → 核对列表无误后 --apply --drop-table。
   有跳过项时不 DROP(防丢数据)。

用法(prod):
  ssh pearnly → cd /opt/mrpilot → set -a; . ./.env; set +a →
    PYTHONPATH=/opt/mrpilot venv/bin/python scripts/migrate_intake_inbox_to_drafts.py
    PYTHONPATH=/opt/mrpilot venv/bin/python scripts/migrate_intake_inbox_to_drafts.py --apply
    PYTHONPATH=/opt/mrpilot venv/bin/python scripts/migrate_intake_inbox_to_drafts.py --apply --drop-table
"""

import argparse
import os
import sys

import psycopg2
from psycopg2.extras import RealDictCursor

from services.purchase import docs as docs_svc
from services.purchase import intake as intake_svc
from services.purchase import settings as settings_svc


def _table_exists(cur) -> bool:
    cur.execute("SELECT to_regclass('public.intake_items') AS t")
    row = cur.fetchone()
    return bool(row and row["t"])


def _pending_items(cur) -> list[dict]:
    cur.execute(
        "SELECT id, tenant_id, workspace_client_id, source, raw, image_url "
        "FROM intake_items WHERE status = 'pending' ORDER BY created_at"
    )
    return [dict(r) for r in (cur.fetchall() or [])]


def _owner_id(cur, tenant_id) -> str | None:
    """租户 owner(建单归属人):优先 role=owner / 未被邀请 · 否则最早成员。"""
    cur.execute(
        "SELECT id FROM users WHERE tenant_id = %s "
        "ORDER BY (role = 'owner') DESC, (invited_by IS NULL) DESC, created_at ASC LIMIT 1",
        (tenant_id,),
    )
    row = cur.fetchone()
    return str(row["id"]) if row else None


def _to_draft(item: dict) -> dict:
    """intake_item.raw → 采购草稿 data(同 resolve_image_intake 的草稿构建·总额交 create_doc 自算)。"""
    raw = item.get("raw") or {}
    kind, _route = intake_svc.judge_direction(raw)
    draft = intake_svc.build_draft_from_invoice(raw, kind=kind)
    draft["source"] = item.get("source") or "line"
    draft["bill_image_ref"] = item.get("image_url") or ""
    return draft


def migrate(cur, apply: bool, drop_table: bool) -> dict:
    report = {"pending": 0, "created": 0, "skipped": [], "dropped": False}
    if not _table_exists(cur):
        return report

    items = _pending_items(cur)
    report["pending"] = len(items)
    if not apply:
        return report

    owner_cache: dict = {}
    for item in items:
        tid, ws, iid = item["tenant_id"], item["workspace_client_id"], str(item["id"])
        try:
            if tid not in owner_cache:
                owner_cache[tid] = _owner_id(cur, tid)
            owner = owner_cache[tid]
            if not owner:
                report["skipped"].append({"id": iid, "reason": "no_owner"})
                continue
            cfg = settings_svc.get_settings(cur, tenant_id=tid, workspace_client_id=ws)
            created = docs_svc.create_doc(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                created_by=owner,
                data=_to_draft(item),
                settings=cfg,
                status="draft",
            )
            doc_id = created["doc"]["id"]
            cur.execute(
                "UPDATE intake_items SET status = 'resolved', resolved_doc_id = %s WHERE id = %s",
                (doc_id, iid),
            )
            report["created"] += 1
        except Exception as e:  # 单项失败(糊图/重复/校验)→ 跳过留痕,不影响其它项
            report["skipped"].append({"id": iid, "reason": f"{type(e).__name__}: {e}"})

    if drop_table:
        if report["skipped"]:
            report["dropped"] = False  # 有跳过项 → 保留表,防丢数据
        else:
            cur.execute("DROP TABLE IF EXISTS intake_items")
            report["dropped"] = True
    return report


def _print_report(report: dict, apply: bool, drop_table: bool) -> None:
    print(f"\n待归类 pending 项:{report['pending']}")
    if not apply:
        print("dry-run:未改动。确认数字后加 --apply 转草稿。")
        return
    print(f"已转草稿:{report['created']} · 跳过:{len(report['skipped'])}")
    for s in report["skipped"]:
        print(f"  跳过 {s['id']}:{s['reason']}")
    if drop_table:
        if report["dropped"]:
            print("intake_items 表已 DROP。")
        else:
            print("有跳过项 → 未 DROP 表(先处理跳过项再 --drop-table)。")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="待归类下线:pending → 草稿 + DROP 表(默认 dry-run)"
    )
    parser.add_argument("--apply", action="store_true", help="真正转草稿(否则只报数)")
    parser.add_argument(
        "--drop-table", action="store_true", help="转完且零跳过则 DROP intake_items"
    )
    args = parser.parse_args()

    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("DATABASE_URL 未设置", file=sys.stderr)
        return 2

    conn = psycopg2.connect(url, sslmode="require")
    conn.autocommit = False
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            report = migrate(cur, args.apply, args.drop_table)
            _print_report(report, args.apply, args.drop_table)
            if args.apply:
                conn.commit()
            else:
                conn.rollback()
            return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
