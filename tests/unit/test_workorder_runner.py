# -*- coding: utf-8 -*-
"""工单后台推进器守门(services/workorder/runner.py)。

脱库:注入假 db/store/engine,验证 advance() ①给引擎的 ctx 带 cursor_factory(按步提交)+
deliverables_dir(工单目录)+ intake_files(取自已登记 items 的 file_ref);②落 run_started/
run_finished 台账;③进程内 in-flight 去重;④引擎抛异常时后台吞掉不崩、仍落 run_finished。
"""

from __future__ import annotations

import unittest

from services.workorder import runner
from services.workorder.engine import RunOutcome


class _FakeCur:
    pass


class _FakeCM:
    def __enter__(self):
        return _FakeCur()

    def __exit__(self, *a):
        return False


class _FakeDB:
    def get_cursor(self, commit=False):
        return _FakeCM()


class _FakeStore:
    def __init__(self, items):
        self._items = items
        self.events = []

    def list_items(self, cur, *, tenant_id, work_order_id):
        return list(self._items)

    def append_event(
        self, cur, *, tenant_id, work_order_id, step, event_type, payload=None, actor="system"
    ):
        self.events.append({"event_type": event_type, "payload": payload or {}})


class RunnerTestBase(unittest.TestCase):
    def setUp(self):
        runner._inflight.clear()
        self._patch("db", _FakeDB())
        self.store = _FakeStore(
            [{"file_ref": "/m/a.jpg"}, {"file_ref": "/m/b.xlsx"}, {"file_ref": None}]
        )
        self._patch("store", self.store)
        self.captured = {}

        def _fake_run(ctx, *, handlers=None):
            self.captured["ctx"] = ctx
            return RunOutcome(status="review", completed=True)

        self._orig_run = runner.engine.run_work_order
        runner.engine.run_work_order = _fake_run
        self.addCleanup(setattr, runner.engine, "run_work_order", self._orig_run)

    def _patch(self, name, value):
        orig = getattr(runner, name)
        setattr(runner, name, value)
        self.addCleanup(setattr, runner, name, orig)


class AdvanceTests(RunnerTestBase):
    def test_advance_builds_per_step_ctx_and_records_ledger(self):
        result = runner.advance("t-1", "wo-1")
        self.assertTrue(result["completed"])

        ctx = self.captured["ctx"]
        self.assertIsNotNone(ctx.cursor_factory)  # 按步提交开关必开
        self.assertIn("wo-1", ctx.data["deliverables_dir"])
        self.assertEqual(
            ctx.data["intake_files"], ["/m/a.jpg", "/m/b.xlsx"]
        )  # None 的 file_ref 被过滤

        kinds = [e["event_type"] for e in self.store.events]
        self.assertIn("run_started", kinds)
        self.assertIn("run_finished", kinds)

    def test_inflight_guard_skips_reentrant_run(self):
        runner._inflight.add(("t-1", "wo-1"))
        try:
            out = runner.advance("t-1", "wo-1")
        finally:
            runner._inflight.discard(("t-1", "wo-1"))
        self.assertEqual(out, {"skipped": "already_running"})

    def test_engine_exception_is_swallowed_and_finish_recorded(self):
        def _boom(ctx, *, handlers=None):
            raise RuntimeError("kaboom")

        runner.engine.run_work_order = _boom
        out = runner.advance("t-1", "wo-1")
        self.assertIn("error", out)
        self.assertEqual(runner._inflight, set())  # 释放了 in-flight,不会卡死后续
        self.assertIn("run_finished", [e["event_type"] for e in self.store.events])


if __name__ == "__main__":
    unittest.main()
