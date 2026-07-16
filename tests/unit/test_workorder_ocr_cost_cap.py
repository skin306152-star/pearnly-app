# -*- coding: utf-8 -*-
"""工单级 OCR 成本封顶参数与账守门(services/workorder/steps/ocr_cost_cap.py · R1 件三 + R1-R1)。

脱库:注入内存 store(sum_workorder_ocr_cost 脚本化)+ StepContext,断言 ①cap≤0/无料 →
不封顶(None);②基线重置语义(人工/自驱 run 给新预算;收尸 reaper 续跑不重置);③达 cap
即 exceeded()。R1-R1 死锁回归:预算回查必须走独立短事务、读完即释放 ai_usage 锁,绝不在长活
步事务(ctx.cur)里攥锁——否则与 worker 首写触发的 RLS-enable ALTER 循环互等。
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


class _ShortTxn:
    """假独立短事务:enter 给一个游标、exit 即提交释放锁(封顶预算读走的形态)。"""

    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


def _ctx(store, *, owner=None):
    # 带 cursor_factory:封顶预算读走独立短事务(真实路径恒有 factory,算术用例照此建)。
    data = {}
    if owner is not None:
        data["run_lease"] = {"owner": owner, "ttl_seconds": 180}
    return StepContext(
        cur=object(),
        tenant_id="t-1",
        work_order_id="wo-1",
        store=store,
        data=data,
        cursor_factory=_ShortTxn,
    )


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

    def test_none_when_no_cursor_factory(self):
        # 无 cursor_factory:预算读无法走独立短事务(攥长锁会死锁),故封顶整体不启用——
        # cap>0 且有料也返 None,把死锁风险从源头挡掉(见 ocr_cost_cap 模块 docstring)。
        ctx = StepContext(
            cur=object(),
            tenant_id="t-1",
            work_order_id="wo-1",
            store=_SumStore([50.0]),
            data={"run_lease": {"owner": "run:u1", "ttl_seconds": 180}},
        )
        self.assertIsNone(ocr_cost_cap.from_ctx(ctx, ["i1"]))

    def test_human_run_resets_baseline_fresh_budget(self):
        # 人工/自驱 run(owner 非 reaper:):基线=起跑已花(50),本次可再花整 cap(100)。
        store = _SumStore([50.0, 90.0, 160.0])  # from_ctx 回查基线50;后续 exceeded 逐次回查
        cap = ocr_cost_cap.from_ctx(_ctx(store, owner="run:u1"), ["i1"])
        self.assertFalse(cap.exceeded())  # 90-50=40 < 100
        self.assertTrue(cap.exceeded())  # 160-50=110 >= 100

    def test_reaper_run_does_not_reset_absolute_cap(self):
        # 收尸续跑(owner=reaper:):基线=0(from_ctx 不回查),cap 卡累计绝对值 → 立即 exceeded。
        store = _SumStore([120.0])
        cap = ocr_cost_cap.from_ctx(_ctx(store, owner="reaper:x"), ["i1"])
        self.assertTrue(cap.exceeded())  # 120-0 >= 100,续跑不重置预算


class ExceededTests(unittest.TestCase):
    def setUp(self):
        os.environ["PEARNLY_WORKORDER_OCR_COST_CAP_THB"] = "100"
        self.addCleanup(os.environ.pop, "PEARNLY_WORKORDER_OCR_COST_CAP_THB", None)

    def test_exceeded_when_spend_reaches_cap(self):
        # reaper 语义基线=0(from_ctx 不回查),台账逐步长到 >=cap → exceeded 翻真。
        store = _SumStore([60.0, 130.0])
        cap = ocr_cost_cap.from_ctx(_ctx(store, owner="reaper:x"), ["i1", "i2"])
        self.assertFalse(cap.exceeded())  # 60 < 100
        self.assertTrue(cap.exceeded())  # 130 >= 100


class _AiUsageLock:
    """ai_usage 表锁足迹模型:SHARE 计数 + 一个 EXCLUSIVE(RLS-enable ALTER)等所有 SHARE 释放。
    读=拿 SHARE(短事务提交时释放);worker 首写的 ensure DDL=要 EXCLUSIVE(SHARE 未清则等)。"""

    def __init__(self):
        self.share = 0
        self.peak_share = 0

    def acquire_share(self):
        self.share += 1
        self.peak_share = max(self.peak_share, self.share)

    def release_share(self):
        self.share -= 1

    def ddl_can_proceed(self) -> bool:
        return self.share == 0


class DeadlockRegressionTests(unittest.TestCase):
    """R1-R1 死锁根治:预算回查走独立短事务、读完即提交释放锁,绝不攥长活步事务的 ai_usage 锁。"""

    def setUp(self):
        os.environ["PEARNLY_WORKORDER_OCR_COST_CAP_THB"] = "100"
        self.addCleanup(os.environ.pop, "PEARNLY_WORKORDER_OCR_COST_CAP_THB", None)

    def test_budget_read_uses_short_txn_not_step_cursor(self):
        # 核心回归:回查游标来自 cursor_factory(短事务),绝非长活步事务 ctx.cur,且用后即提交。
        seen, commits = [], []
        step_cur = object()  # 长活步事务游标——预算读绝不该碰它

        class _ShortTxn:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                commits.append(1)  # 短事务提交/关闭=释放锁
                return False

        class _Store:
            def sum_workorder_ocr_cost(self, cur, *, tenant_id, item_ids):
                seen.append(cur)
                return 0.0

        ctx = StepContext(
            cur=step_cur,
            tenant_id="t",
            work_order_id="wo",
            store=_Store(),
            data={"run_lease": {"owner": "run:u"}},
            cursor_factory=_ShortTxn,
        )
        cap = ocr_cost_cap.from_ctx(ctx, ["i1"])  # prime 回查一次
        cap.exceeded()  # 再回查一次
        self.assertTrue(seen, "预算至少回查一次")
        self.assertNotIn(step_cur, seen)  # ★绝不用长活步事务游标
        self.assertTrue(all(isinstance(c, _ShortTxn) for c in seen))
        self.assertEqual(len(commits), len(seen))  # 每次读后短事务都提交释放

    def test_budget_read_releases_ai_usage_lock_between_reads(self):
        # 锁足迹:每次回查拿 SHARE、读完即释放 → 任意时刻 worker 的 RLS-enable ALTER 都拿得到
        # EXCLUSIVE(不互等)。修前(攥 ctx.cur 长锁)SHARE 永不归零 → DDL 永远等 → 本测必红。
        lock = _AiUsageLock()

        class _ShortTxn:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                lock.release_share()
                return False

        class _Store:
            def sum_workorder_ocr_cost(self, cur, *, tenant_id, item_ids):
                lock.acquire_share()
                return 50.0

        ctx = StepContext(
            cur=object(),
            tenant_id="t",
            work_order_id="wo",
            store=_Store(),
            data={"run_lease": {"owner": "run:u"}},
            cursor_factory=_ShortTxn,
        )
        cap = ocr_cost_cap.from_ctx(ctx, ["i1"])  # prime
        self.assertTrue(lock.ddl_can_proceed(), "prime 后 ai_usage SHARE 未释放,DDL 会互等")
        cap.exceeded()
        self.assertTrue(lock.ddl_can_proceed(), "exceeded 后 ai_usage SHARE 未释放,DDL 会互等")
        self.assertEqual(lock.peak_share, 1)  # 同一时刻至多攥一个 SHARE,读完即放


if __name__ == "__main__":
    unittest.main()
