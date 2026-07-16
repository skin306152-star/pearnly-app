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
import threading
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
    p.add_argument(
        "--watch",
        action="store_true",
        help="跑批期间每 3 秒只读打印实时步位/已识别张数(观测用,不改跑批逻辑)",
    )
    return p.parse_args()


def _watch_progress(tenant_id: str, work_order_id: str, stop: threading.Event) -> None:
    """独立只读连接轮询 current_step + item_classified 事件数,滚动打印真实进度。

    只读、与引擎的按步事务互不干扰(引擎每进一步先独立提交 current_step,故这里能立刻看到);
    任何查询异常都吞掉继续下一轮——观测层绝不拖累跑批。
    """
    last = None
    while not stop.wait(3.0):
        try:
            with db.get_cursor() as cur:
                wo = store.get_work_order(cur, tenant_id=tenant_id, work_order_id=work_order_id)
                events = store.list_events(cur, tenant_id=tenant_id, work_order_id=work_order_id)
        except Exception:
            continue
        if not wo:
            continue
        classified = sum(1 for e in events if e.get("event_type") == "item_classified")
        line = (
            f"  … {wo['status']}/{wo['current_step']} · 已识别 {classified} 张 · 事件 {len(events)}"
        )
        if line != last:  # 只在变化时打,避免刷屏
            print(line, flush=True)
            last = line


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
    # 运行时加固列自愈必须先于任何锁工单表的事务(routes/runner 各自前置调,CLI 是第三个
    # 真实入口,漏调=缺列库上 dedupe_key 直接崩在金标路径)。
    store.ensure_runtime()
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
    if not args.watch:
        out = engine.run_work_order(ctx, handlers=real_handlers())
        return _print_outcome(out, ctx)

    # --watch:引擎跑后台线程,主线程只读轮询打印实时进度,引擎结束即收尾。
    result: dict = {}
    stop = threading.Event()

    def _run() -> None:
        try:
            result["out"] = engine.run_work_order(ctx, handlers=real_handlers())
        except BaseException as e:  # 让主线程看到崩因,不静默吞
            result["err"] = e
        finally:
            stop.set()

    worker = threading.Thread(target=_run, daemon=True)
    print(f"▶ 跑批开始(工单 {wo['id']})· 每 3 秒刷新真实进度:", flush=True)
    worker.start()
    _watch_progress(tenant_id, wo["id"], stop)
    worker.join()
    if "err" in result:
        raise result["err"]
    return _print_outcome(result["out"], ctx)


if __name__ == "__main__":
    sys.exit(main())
