#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工单制 CLI 验收入口(M0 任务包 §2 · T7)。
一条命令把某客户某期的原始资料跑成「待签底稿 + 证据链」交付包:
    python scripts/run_workorder.py --client sister-makeup --period 2569-05 \
        --intake-dir C:\\...\\A_客户给的原料 --out C:\\...\\out
不做业务逻辑,只做:解析参数 → 开单(幂等)→ 组料 → 跑引擎 → 打印结果,重活全在 services/workorder/*。
首行必须先 import core.db(单脚本直调 services 会踩 dal_reexports 循环导入坑,详见 core/db.py 尾注)。
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):  # Windows 控制台非 UTF-8 时打中文会炸(prod 无感)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import core.db as db  # noqa: E402,F401 - 占坑防循环导入,必须先于其余 services import,见文件头
from services.workorder import engine, store  # noqa: E402
from services.workorder.steps import real_handlers

_INTAKE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".pdf", ".xlsx", ".xlsm", ".xls", ".csv"}


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Pearnly AI 工单制 CLI(M0)")
    p.add_argument("--client", required=True, help="客户名称(模糊匹配)或 workspace_client id")
    p.add_argument("--period", required=True, help="申报期,如 2569-05")
    p.add_argument("--intake-dir", help="原始资料目录(需要进 intake 步时给)")
    p.add_argument("--out", required=True, help="交付包输出目录")
    p.add_argument("--tenant-id", help="租户 UUID(缺省从匹配到的客户账套推导)")
    p.add_argument("--decide", action="append", default=[], help="item_id:decision[:k=v,...]")
    return p.parse_args()


def _resolve_client(cur, *, client: str, tenant_id: str) -> dict:
    """按 id 或名称模糊匹配唯一客户账套,零命中/多命中诚实报错列候选,不猜。"""
    if client.isdigit():
        where, params = "id = %s", (int(client),)
    elif tenant_id:
        where, params = "tenant_id = %s AND name ILIKE %s", (tenant_id, f"%{client}%")
    else:
        where, params = "name ILIKE %s", (f"%{client}%",)
    cur.execute(
        f"SELECT id, tenant_id, name, tax_id FROM workspace_clients "
        f"WHERE is_active = TRUE AND {where} ORDER BY id",
        params,
    )
    rows = cur.fetchall()
    if len(rows) != 1:
        print(f"客户匹配失败(命中 {len(rows)} 条):", file=sys.stderr)
        for r in rows:
            print(f"  {r['id']} {r['name']} tax={r['tax_id']} t={r['tenant_id']}", file=sys.stderr)
        raise SystemExit(1)
    return dict(rows[0])


def _intake_files(intake_dir: str) -> list:
    paths = Path(intake_dir).iterdir()
    files = sorted(str(p) for p in paths if p.is_file() and p.suffix.lower() in _INTAKE_EXTS)
    if not files:
        print(f"intake-dir 无可识别文件:{intake_dir}", file=sys.stderr)
        raise SystemExit(1)
    return files


def _parse_decide(raw: str) -> dict:
    """ "item_id:face_value" 或 "item_id:recalc:vat=4060,net=1000" → 事件 payload。"""
    item_id, _, rest = raw.partition(":")
    decision, _, extra = rest.partition(":")
    values = {}
    for pair in extra.split(",") if extra else []:
        k, _, v = pair.partition("=")
        values[k.strip()] = v.strip()
    return {"item_id": item_id, "decision": decision, "values": values}


def _format_outcome(out: engine.RunOutcome, deliverables: Optional[dict]) -> tuple[list, int]:
    """把 RunOutcome 渲染成(输出行, 退出码)。停机语义取自 out.result.status —— out.status
    是工单库状态,needs 与 stuck 同落 'stuck',拿它区分会把缺料打成卡点、清单还是空的。"""
    if out.completed:
        lines = [f"completed · 工单落 {out.status}"]
        lines += [f"  [{kind}] {path}" for kind, path in (deliverables or {}).items()]
        return lines, 0
    res = out.result
    if res is not None and res.status == engine.STEP_NEEDS:
        label, items = "needs", res.missing
    else:
        label, items = "stuck", res.reasons if res is not None else ()
    lines = [f"stopped at {out.stopped_at} ({label}):"]
    lines += [f"  - {x}" for x in items]
    return lines, 2


def _print_outcome(out: engine.RunOutcome, ctx: engine.StepContext) -> int:
    lines, code = _format_outcome(out, ctx.data.get("deliverables"))
    for line in lines:
        print(line)
    return code


def main() -> int:
    args = _parse_args()
    # 前置(解析客户 / 幂等开单 / 落人工裁决)走一个已提交事务,先于按步跑落库;
    # 引擎再以 cursor_factory 每步各开独立事务(L2 教训:进程中途被杀不整跑回滚、不重烧 OCR)。
    with db.get_cursor(commit=True) as cur:
        client = _resolve_client(cur, client=args.client, tenant_id=args.tenant_id)
        tenant_id = args.tenant_id or client["tenant_id"]
        if not tenant_id:
            print("匹配到的客户账套无 tenant_id,请用 --tenant-id 指定", file=sys.stderr)
            return 1
        wo = store.open_work_order(
            cur, tenant_id=tenant_id, workspace_client_id=client["id"], period=args.period
        )
        ev = dict(tenant_id=tenant_id, work_order_id=wo["id"], step="reconcile")
        for raw in args.decide:
            d = _parse_decide(raw)
            store.append_event(cur, event_type="human_decision", payload=d, actor="user:cli", **ev)

    data = {"deliverables_dir": args.out}
    if args.intake_dir:
        data["intake_files"] = _intake_files(args.intake_dir)
    ctx = engine.StepContext(
        cur=None,
        tenant_id=tenant_id,
        work_order_id=wo["id"],
        data=data,
        cursor_factory=lambda: db.get_cursor(commit=True),
    )
    out = engine.run_work_order(ctx, handlers=real_handlers())
    return _print_outcome(out, ctx)


if __name__ == "__main__":
    sys.exit(main())
