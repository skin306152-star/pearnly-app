# -*- coding: utf-8 -*-
"""工单级 OCR 累计成本封顶 + 贵模型回落上限的参数与账(R1 · 件三)。

烧钱刹车:一张工单一次跑批的 OCR 累计成本以 ai_usage.cost_thb 为单一事实源(task=
workorder_classify,trace_id=item_id)。达 cap 即停止投料——已处理件保留、未处理件留
pending、run 落 stuck 点名 ocr_cost_cap_exceeded(诚实待续,人工 /run 重给预算)。

⚠️ 台账回查必须走【独立短事务】,读完即提交释放锁,绝不在长活步事务(ctx.cur)里攥
ai_usage 的 ACCESS SHARE 锁——否则主线程等首张 OCR future 期间锁不释放,与 worker 线程首写
ai_usage 触发的 RLS-enable ALTER(要 ACCESS EXCLUSIVE)循环互等成死锁(R1-R1 金标真跑
实锤:本地新库/进程首写场景必现)。每件一次短 SELECT 往返开销可接受(本来每件就有一次
OCR 网络调用)。无 cursor_factory(内存 / 单事务旧路)无法保证独立短事务,而 classify 的 OCR 无
条件并发——故封顶整体不启用(from_ctx 返 None),不留攥长锁死锁的 ctx.cur 回落读;真实路径
(routes/run→runner、CLI run_workorder)恒带 factory,封顶恒在。

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
    """一次跑批贵模型回落(升高精档)次数上限。默认 10。≤0 = 不封顶。
    env PEARNLY_WORKORDER_OCR_FALLBACK_LIMIT 覆写。"""
    try:
        return max(0, int(os.environ.get("PEARNLY_WORKORDER_OCR_FALLBACK_LIMIT", "10")))
    except ValueError:
        return 10


def from_ctx(ctx, item_ids: list):
    """按 ctx 建成本封顶账并即刻回查基线;cap≤0 / 无料 / 无 cursor_factory → None(不封顶)。
    无 factory 不启用封顶的死锁根因见模块 docstring。基线是否重置由 run_lease.owner 前缀判
    (reaper: = 续跑不重置;其余 = 人工/自驱给新预算)。"""
    cap = cap_thb()
    if cap <= 0 or not item_ids or ctx.cursor_factory is None:
        return None
    owner = (ctx.data.get("run_lease") or {}).get("owner") or ""
    reset_baseline = not str(owner).startswith("reaper:")
    cost_cap = CostCap(ctx, list(item_ids), cap=cap, reset_baseline=reset_baseline)
    cost_cap.prime()
    return cost_cap


class CostCap:
    """本工单 OCR 累计成本的封顶判据。spent 每次从 ai_usage 台账回查(独立短事务,读完即释放锁)。"""

    def __init__(self, ctx, item_ids: list, *, cap: float, reset_baseline: bool):
        self._ctx = ctx
        self._item_ids = item_ids
        self._cap = cap
        self._reset = reset_baseline
        self._baseline = 0.0

    def prime(self) -> None:
        """回查预算基线(人工/自驱 run 用起跑已花;reaper 续跑基线=0 卡累计绝对值)。"""
        if self._reset:
            self._baseline = self._spent()

    def exceeded(self) -> bool:
        """本次跑批已花(台账累计 − 基线)是否达到 cap。"""
        return (self._spent() - self._baseline) >= self._cap

    def _spent(self) -> float:
        ctx = self._ctx
        # 独立短事务读台账,读完即提交释放 ai_usage 锁(见模块 docstring 的死锁根因)。from_ctx
        # 已挡掉无 factory 的场景(封顶不启用),故这里 cursor_factory 必在。
        with ctx.cursor_factory() as cur:
            return _sum(ctx, cur, self._item_ids)


def _sum(ctx, cur, item_ids: list) -> float:
    total = ctx.store.sum_workorder_ocr_cost(cur, tenant_id=ctx.tenant_id, item_ids=item_ids)
    return float(total or 0.0)
