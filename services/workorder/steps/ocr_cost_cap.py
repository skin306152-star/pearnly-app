# -*- coding: utf-8 -*-
"""工单级 OCR 累计成本封顶 + 贵模型回落上限的参数与账(R1 · 件三)。

烧钱刹车:一张工单一次跑批的 OCR 累计成本以 ai_usage.cost_thb 为单一事实源(task=
workorder_classify,trace_id=item_id)。达 cap 即停止投料——已处理件保留、未处理件留
pending、run 落 stuck 点名 ocr_cost_cap_exceeded(诚实待续,人工 /run 重给预算)。

台账回查一律用调用方当前绑定的游标(ctx.cur:classify 步事务 / 逐件检查点子事务),不另
开连接——避免逐件多一个事务往返,也不破坏「每件一个独立事务」不变式。

预算基线语义(与 reaper 自动重跑「人工重置」同哲学):
  - 人工 / 自驱 run(owner 非 reaper:)→ 基线=起跑时台账已花,故本次可再花整 cap。
  - 收尸自动续跑(owner=reaper:)→ 基线=0,cap 卡累计绝对值,续跑不重置预算防 crash-loop。
"""

from __future__ import annotations

import os


def cap_thb() -> float:
    """一张工单一次跑批 OCR 累计成本上限(泰铢)。默认 150(MC3 全链实测 ~฿82,~2x 裕量)。
    ≤0 = 关闭封顶。env PEARNLY_WORKORDER_OCR_COST_CAP_THB 覆写。"""
    try:
        return max(0.0, float(os.environ.get("PEARNLY_WORKORDER_OCR_COST_CAP_THB", "150")))
    except ValueError:
        return 150.0


def fallback_limit() -> int:
    """一次跑批贵模型回落(升 3.5-flash)次数上限。默认 10。≤0 = 不封顶。
    env PEARNLY_WORKORDER_OCR_FALLBACK_LIMIT 覆写。"""
    try:
        return max(0, int(os.environ.get("PEARNLY_WORKORDER_OCR_FALLBACK_LIMIT", "10")))
    except ValueError:
        return 10


def from_ctx(ctx, item_ids: list):
    """按 ctx 建成本封顶账并即刻回查基线;cap≤0 或无料 → None(不封顶)。基线是否重置由
    run_lease.owner 前缀判(reaper: = 续跑不重置;其余 = 人工/自驱给新预算)。"""
    cap = cap_thb()
    if cap <= 0 or not item_ids:
        return None
    owner = (ctx.data.get("run_lease") or {}).get("owner") or ""
    cost_cap = CostCap(list(item_ids), cap=cap, reset_baseline=not str(owner).startswith("reaper:"))
    cost_cap.prime(ctx)
    return cost_cap


class CostCap:
    """本工单 OCR 累计成本的封顶判据。spent 每次从 ai_usage 台账回查(单一事实源),用
    ctx.cur 现有游标读,不另开事务。"""

    def __init__(self, item_ids: list, *, cap: float, reset_baseline: bool):
        self._item_ids = item_ids
        self._cap = cap
        self._reset = reset_baseline
        self._baseline = 0.0

    def prime(self, ctx) -> None:
        """回查预算基线(人工/自驱 run 用起跑已花;reaper 续跑基线=0 卡累计绝对值)。"""
        if self._reset:
            self._baseline = self._spent(ctx)

    def exceeded(self, ctx) -> bool:
        """本次跑批已花(台账累计 − 基线)是否达到 cap。"""
        return (self._spent(ctx) - self._baseline) >= self._cap

    def _spent(self, ctx) -> float:
        total = ctx.store.sum_workorder_ocr_cost(
            ctx.cur, tenant_id=ctx.tenant_id, item_ids=self._item_ids
        )
        return float(total or 0.0)
