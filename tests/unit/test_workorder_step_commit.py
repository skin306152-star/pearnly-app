# -*- coding: utf-8 -*-
"""按步提交事务守门(services/workorder/engine.py · L2 教训根治)。

M0 整跑单事务:进程中途被杀 = 全部回滚 = 已烧的 OCR 白烧。这里用一个「事务型」内存
store(每个 cursor_factory 单元 = 一个事务:块正常退出才把缓冲并入已提交状态,异常则丢弃)
证明改造后的语义:模拟第 N 步抛异常中断 → 前 N-1 步的 step_done 已永久提交、第 N 步整步
回滚(连 step_started 都不留);去掉故障后续跑从第 N 步继续,不重复落已完成步的事件。

对照组:不给 cursor_factory 时走单事务旧路(引擎行为逐字节不变),异常照样冒泡但事件不回滚
(由上层统一提交/回滚)—— 这条不测回滚,只锚定「无 factory = 旧编排」不被改坏。
"""

from __future__ import annotations

import unittest

from services.workorder import engine
from services.workorder.engine import StepContext, StepResult


class _Txn:
    """一个事务:读 = 已提交 + 本事务缓冲;写只进缓冲;commit 并入,异常丢弃(回滚)。"""

    def __init__(self, store):
        self.store = store
        self.buffered_events: list = []
        self.buffered_status = None

    def visible_events(self):
        return list(self.store.committed_events) + list(self.buffered_events)

    def buffer_event(self, row):
        self.buffered_events.append(row)

    def buffer_status(self, status, current_step):
        self.buffered_status = (status, current_step)

    def commit(self):
        self.store.committed_events.extend(self.buffered_events)
        if self.buffered_status is not None:
            self.store.status = self.buffered_status[0]
            if self.buffered_status[1] is not None:
                self.store.current_step = self.buffered_status[1]


class _UnitCM:
    """cursor_factory():进 __enter__ 开事务,正常 __exit__ 提交,带异常 __exit__ 回滚并放行异常。"""

    def __init__(self, store):
        self.store = store
        self.txn = None

    def __enter__(self):
        self.txn = _Txn(self.store)
        return self.txn

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.txn.commit()
        return False  # 不吞异常(回滚 = 丢弃缓冲,天然发生)


class _TxnStore:
    """事务型 store:engine 传入的 cur 是 _Txn;读写全落该事务,提交才可见。"""

    def __init__(self):
        self.committed_events: list = []
        self.status = None
        self.current_step = None
        self._seq = 0

    def factory(self):
        return _UnitCM(self)

    def list_events(self, cur, *, tenant_id, work_order_id):
        return [dict(e) for e in cur.visible_events()]

    def append_event(
        self, cur, *, tenant_id, work_order_id, step, event_type, payload=None, actor="system"
    ):
        self._seq += 1
        row = {"id": self._seq, "step": step, "event_type": event_type, "payload": payload or {}}
        cur.buffer_event(row)
        return dict(row)

    def set_status(self, cur, *, tenant_id, work_order_id, status, current_step=None):
        cur.buffer_status(status, current_step)

    # 断言辅助(只看已提交)
    def committed_done(self):
        return [e["step"] for e in self.committed_events if e["event_type"] == engine.EVT_DONE]

    def committed_count(self, step, event_type):
        return sum(
            1 for e in self.committed_events if e["step"] == step and e["event_type"] == event_type
        )


def _ctx(store, presets=None):
    data = {"_presets": presets} if presets else {}
    return StepContext(
        cur=None,
        tenant_id="t-1",
        work_order_id="wo-1",
        store=store,
        data=data,
        cursor_factory=store.factory,
    )


_BOOM = RuntimeError("simulated kill mid-step")


def _raise_at(step_name):
    def handler(ctx):
        raise _BOOM

    return {step_name: handler}


class InterruptAtStepCommitsPriorSteps(unittest.TestCase):
    def test_kill_at_reconcile_keeps_prior_done_and_resumes_without_dupes(self):
        store = _TxnStore()

        # 第一次:reconcile 步抛异常(模拟进程被杀)。异常必须冒泡(不被引擎吞)。
        handlers = engine.default_handlers()
        handlers.update(_raise_at("reconcile"))
        with self.assertRaises(RuntimeError):
            engine.run_work_order(_ctx(store), handlers=handlers)

        # intake/sort/classify 三步的 step_done 已永久提交。
        self.assertEqual(store.committed_done(), ["intake", "sort", "classify"])
        # 被杀的 reconcile 整步回滚:连 step_started 都没提交。
        self.assertEqual(store.committed_count("reconcile", engine.EVT_STARTED), 0)
        self.assertEqual(store.committed_count("reconcile", engine.EVT_DONE), 0)

        events_after_crash = len(store.committed_events)

        # 去掉故障后续跑:从 reconcile 继续跑到底,已完成三步一个事件都不再补。
        out = engine.run_work_order(_ctx(store))
        self.assertTrue(out.completed)
        self.assertEqual(store.status, "review")
        for step in ("intake", "sort", "classify"):
            self.assertEqual(store.committed_count(step, engine.EVT_STARTED), 1)
            self.assertEqual(store.committed_count(step, engine.EVT_DONE), 1)
        # 续跑首次真正跑 reconcile→package,各恰一对 started+done。
        for step in ("reconcile", "compute", "package"):
            self.assertEqual(store.committed_count(step, engine.EVT_STARTED), 1)
            self.assertEqual(store.committed_count(step, engine.EVT_DONE), 1)
        # 崩溃前已提交的事件一条没丢(只增不改)。
        self.assertGreater(len(store.committed_events), events_after_crash)

    def test_second_kill_at_later_step_still_only_loses_that_step(self):
        store = _TxnStore()
        handlers = engine.default_handlers()
        handlers.update(_raise_at("package"))
        with self.assertRaises(RuntimeError):
            engine.run_work_order(_ctx(store), handlers=handlers)

        # 一路到 compute 都提交了,只丢 package。
        self.assertEqual(
            store.committed_done(), ["intake", "sort", "classify", "reconcile", "compute"]
        )
        self.assertEqual(store.committed_count("package", engine.EVT_DONE), 0)

        out = engine.run_work_order(_ctx(store))
        self.assertTrue(out.completed)
        self.assertEqual(store.committed_count("package", engine.EVT_DONE), 1)
        # 前五步无一被重做。
        for step in ("intake", "sort", "classify", "reconcile", "compute"):
            self.assertEqual(store.committed_count(step, engine.EVT_DONE), 1)


class NoFactoryKeepsLegacySingleTxn(unittest.TestCase):
    def test_without_factory_engine_orchestration_unchanged(self):
        # 无 cursor_factory:走 _shared_unit,引擎正常跑到 review(旧路不被改坏)。
        store = _TxnStore()
        ctx = StepContext(cur=_Txn(store), tenant_id="t-1", work_order_id="wo-1", store=store)
        out = engine.run_work_order(ctx)
        self.assertTrue(out.completed)
        self.assertEqual(out.status, engine.TERMINAL_STATUS)


if __name__ == "__main__":
    unittest.main()
