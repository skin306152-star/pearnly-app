# -*- coding: utf-8 -*-
"""工单级 OCR 成本封顶参数与账守门(services/workorder/steps/ocr_cost_cap.py · R1 件三)。

脱库:注入内存 store(sum_workorder_ocr_cost 脚本化)+ StepContext,断言 ①cap≤0/无料 →
不封顶(None);②基线重置语义(人工/自驱 run 给新预算;收尸 reaper 续跑不重置);③达 cap
即 exceeded()。env 覆写用例锁死默认与可调。
"""

from __future__ import annotations

import os
import unittest

from services.workorder.engine import StepContext
from services.workorder.steps import ocr_cost_cap


class _SumStore:
    """sum_workorder_ocr_cost 脚本化:按调用序返回预置累计成本(模拟台账逐步长)。"""

    def __init__(self, sums):
        self._sums = list(sums)
        self.calls = 0

    def sum_workorder_ocr_cost(self, cur, *, tenant_id, item_ids):
        val = self._sums[min(self.calls, len(self._sums) - 1)]
        self.calls += 1
        return val


def _ctx(store, *, owner=None):
    data = {}
    if owner is not None:
        data["run_lease"] = {"owner": owner, "ttl_seconds": 180}
    return StepContext(cur=object(), tenant_id="t-1", work_order_id="wo-1", store=store, data=data)


class EnvDefaultsTests(unittest.TestCase):
    def test_cap_and_limit_defaults(self):
        for key in ("PEARNLY_WORKORDER_OCR_COST_CAP_THB", "PEARNLY_WORKORDER_OCR_FALLBACK_LIMIT"):
            os.environ.pop(key, None)
        self.assertEqual(ocr_cost_cap.cap_thb(), 150.0)
        self.assertEqual(ocr_cost_cap.fallback_limit(), 10)


class FromCtxTests(unittest.TestCase):
    def setUp(self):
        os.environ["PEARNLY_WORKORDER_OCR_COST_CAP_THB"] = "100"
        self.addCleanup(os.environ.pop, "PEARNLY_WORKORDER_OCR_COST_CAP_THB", None)

    def test_none_when_no_items(self):
        self.assertIsNone(ocr_cost_cap.from_ctx(_ctx(_SumStore([0])), []))

    def test_none_when_cap_disabled(self):
        os.environ["PEARNLY_WORKORDER_OCR_COST_CAP_THB"] = "0"
        self.assertIsNone(ocr_cost_cap.from_ctx(_ctx(_SumStore([0])), ["i1"]))

    def test_human_run_resets_baseline_fresh_budget(self):
        # 人工/自驱 run(owner 非 reaper:):基线=起跑已花(50),本次可再花整 cap(100)。
        store = _SumStore([50.0, 90.0, 160.0])  # from_ctx 回查基线50;后续 exceeded 逐次回查
        ctx = _ctx(store, owner="run:u1")
        cap = ocr_cost_cap.from_ctx(ctx, ["i1"])
        self.assertFalse(cap.exceeded(ctx))  # 90-50=40 < 100
        self.assertTrue(cap.exceeded(ctx))  # 160-50=110 >= 100

    def test_reaper_run_does_not_reset_absolute_cap(self):
        # 收尸续跑(owner=reaper:):基线=0(from_ctx 不回查),cap 卡累计绝对值 → 立即 exceeded。
        store = _SumStore([120.0])
        ctx = _ctx(store, owner="reaper:x")
        cap = ocr_cost_cap.from_ctx(ctx, ["i1"])
        self.assertTrue(cap.exceeded(ctx))  # 120-0 >= 100,续跑不重置预算


class ExceededTests(unittest.TestCase):
    def setUp(self):
        os.environ["PEARNLY_WORKORDER_OCR_COST_CAP_THB"] = "100"
        self.addCleanup(os.environ.pop, "PEARNLY_WORKORDER_OCR_COST_CAP_THB", None)

    def test_exceeded_when_spend_reaches_cap(self):
        # reaper 语义基线=0(from_ctx 不回查),台账逐步长到 >=cap → exceeded 翻真。
        store = _SumStore([60.0, 130.0])
        ctx = _ctx(store, owner="reaper:x")
        cap = ocr_cost_cap.from_ctx(ctx, ["i1", "i2"])
        self.assertFalse(cap.exceeded(ctx))  # 60 < 100
        self.assertTrue(cap.exceeded(ctx))  # 130 >= 100


if __name__ == "__main__":
    unittest.main()
