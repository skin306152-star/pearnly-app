# -*- coding: utf-8 -*-
"""tenant_entrances 回填 · 幂等 · 默认 dry-run(登录准入 Phase2)。

把每个 tenant 应有的授权入口集(main/pos/ai)写进显式表 tenant_entrances。判据【复用】
services.auth.entrance._derive_entrances —— 与登录时的 Phase1 推导同一套单一事实源(business_type
非 pos_only=main / pos 模块开=pos / 在 pearnly_ai_m1 名单=ai),不在此另写一份判据。

幂等:grant_entrance 走 ON CONFLICT DO NOTHING,复跑不重复行、不炸。

⚠️ prod 不自动跑迁移:必须先 `alembic upgrade head`(或让 0078_tenant_entrances 生效)建表,
   再跑本脚本;表不存在直接跑会报错。dry-run 只 SELECT + 打印统计,须显式 --apply 才真写。

用法(prod):
  ssh pearnly → cd /opt/mrpilot → set -a; . ./.env; set +a →
    PYTHONPATH=/opt/mrpilot venv/bin/python scripts/backfill_tenant_entrances.py
    PYTHONPATH=/opt/mrpilot venv/bin/python scripts/backfill_tenant_entrances.py --apply
"""

from __future__ import annotations

import argparse
import sys


def _all_tenant_ids(cur) -> list[str]:
    cur.execute("SELECT id::text AS id FROM tenants ORDER BY created_at")
    return [r["id"] for r in (cur.fetchall() or [])]


def plan_backfill(cur) -> list[tuple[str, set[str]]]:
    """遍历所有 tenant,按登录推导算出各自应有入口集。返回 [(tenant_id, {入口...})]。"""
    from services.auth import entrance

    plan: list[tuple[str, set[str]]] = []
    for tid in _all_tenant_ids(cur):
        ents = entrance._derive_entrances(tid, None)
        if ents:
            plan.append((tid, ents))
    return plan


def apply_backfill(cur, plan: list[tuple[str, set[str]]]) -> int:
    """把计划写入表(幂等)。返回 grant 调用次数(含已存在的 no-op 行)。"""
    from services.auth import entrance_store

    n = 0
    for tid, ents in plan:
        for ent in sorted(ents):
            entrance_store.grant_entrance(cur, tid, ent, granted_by="backfill")
            n += 1
    return n


def _print_plan(plan: list[tuple[str, set[str]]]) -> None:
    print(f"\n候选 {len(plan)} 个 tenant(有可授权入口):\n")
    tally = {"main": 0, "pos": 0, "ai": 0}
    for tid, ents in plan:
        for e in ents:
            tally[e] = tally.get(e, 0) + 1
        print(f"  将为 tenant {tid} 写 {{{','.join(sorted(ents))}}}")
    print(f"\n合计 · main={tally['main']} pos={tally['pos']} ai={tally['ai']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="回填 tenant_entrances(默认 dry-run)")
    parser.add_argument("--apply", action="store_true", help="真正写表(否则只报计划)")
    args = parser.parse_args()

    from core import db

    if args.apply:
        with db.get_cursor(commit=True) as cur:
            plan = plan_backfill(cur)
            _print_plan(plan)
            wrote = apply_backfill(cur, plan)
        print(f"\n已回填 · grant 调用 {wrote} 次(ON CONFLICT DO NOTHING · 幂等)。")
    else:
        with db.get_cursor() as cur:
            plan = plan_backfill(cur)
        _print_plan(plan)
        print("\ndry-run:未改动。确认后加 --apply 执行(须先 alembic upgrade 建表)。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
