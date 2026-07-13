# -*- coding: utf-8 -*-
"""工单后台推进器守门(services/workorder/runner.py)。

脱库:注入假 db/store/engine,验证 advance() ①给引擎的 ctx 带 cursor_factory(按步提交)+
deliverables_dir(工单目录)+ intake_files(取自已登记 items 的 file_ref);②落 run_started/
run_finished 台账;③进程内 in-flight 去重;④引擎抛异常时后台吞掉不崩、落 run_failed 且
状态同事务落 stuck(MC2-A1 ③,不许留 running 说谎)。request_run 推进原语(MC2-A1 ①):
抢租约 → run_requested → 派发,租约策略可参数化、派发默认守护线程 / BackgroundTasks 可选。
"""

from __future__ import annotations

import unittest

from services.workorder import engine, runner
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
    def __init__(self, items=()):
        self._items = items
        self.events = []
        self.released = []
        self.statuses = []
        self.acquired = []
        self.acquire_result = True
        self.ensured = 0

    def ensure_runtime(self):
        self.ensured += 1

    def list_items(self, cur, *, tenant_id, work_order_id):
        return list(self._items)

    def append_event(
        self, cur, *, tenant_id, work_order_id, step, event_type, payload=None, actor="system"
    ):
        self.events.append({"event_type": event_type, "payload": payload or {}, "actor": actor})

    def acquire_run_lease(self, cur, *, tenant_id, work_order_id, owner, ttl_seconds):
        self.acquired.append(owner)
        return self.acquire_result

    def release_run_lease(self, cur, *, tenant_id, work_order_id, owner):
        self.released.append(owner)

    def set_status(self, cur, *, tenant_id, work_order_id, status, current_step=None):
        self.statuses.append({"status": status, "current_step": current_step})


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

    def test_engine_exception_records_run_failed_not_finished(self):
        # P-8:后台 run 抛异常 → 落 run_failed(带原因)认账,而非冒充成功的 run_finished;
        # in-flight 释放不卡死后续。
        def _boom(ctx, *, handlers=None):
            raise RuntimeError("kaboom")

        runner.engine.run_work_order = _boom
        out = runner.advance("t-1", "wo-1")
        self.assertIn("error", out)
        self.assertEqual(runner._inflight, set())
        kinds = [e["event_type"] for e in self.store.events]
        self.assertIn("run_failed", kinds)
        self.assertNotIn("run_finished", kinds)  # 死了就不许落 run_finished
        failed = next(e for e in self.store.events if e["event_type"] == "run_failed")
        self.assertIn("kaboom", failed["payload"].get("error", ""))

    def test_run_failed_lands_status_stuck_in_same_finish(self):
        # MC2-A1 ③ 咬人:run_failed 认账必须把 status 落到 stuck(engine 现有词),
        # 不许留 running 对 UI 谎称「AI 在做」。去掉 _finish 里的 set_status 本测必红。
        def _boom(ctx, *, handlers=None):
            raise RuntimeError("kaboom")

        runner.engine.run_work_order = _boom
        runner.advance("t-1", "wo-1")
        self.assertEqual(
            self.store.statuses, [{"status": engine.STATUS_STUCK, "current_step": None}]
        )

    def test_run_finished_does_not_touch_status(self):
        # 成功收尾不动状态列(终态由引擎在步事务里落),_finish 只管 run_failed 的落实。
        runner.advance("t-1", "wo-1")
        self.assertEqual(self.store.statuses, [])

    def test_lease_owner_flows_into_ctx_for_heartbeat(self):
        # MC2-A1 ④:持约的 run 把 owner/ttl 放进 ctx.data,供 classify 逐件检查点心跳续约。
        runner.advance("t-1", "wo-1", "run:hb")
        lease = self.captured["ctx"].data["run_lease"]
        self.assertEqual(lease["owner"], "run:hb")
        self.assertEqual(lease["ttl_seconds"], runner.run_lease_ttl_seconds())

    def test_direct_call_has_no_heartbeat_lease(self):
        runner.advance("t-1", "wo-1")
        self.assertNotIn("run_lease", self.captured["ctx"].data)

    def test_lease_released_even_when_run_fails(self):
        # P-8 硬门:异常路径也必须释放 DB 租约(供另一终端接管),不让死 run 占租约到 TTL。
        def _boom(ctx, *, handlers=None):
            raise RuntimeError("boom")

        runner.engine.run_work_order = _boom
        runner.advance("t-1", "wo-1", "run:owner-x")
        self.assertEqual(self.store.released, ["run:owner-x"])

    def test_lease_owner_released_on_finish(self):
        # 路由抢到租约后把 owner 交 advance,收尾必须释放(供另一终端接管)。
        runner.advance("t-1", "wo-1", "run:abc")
        self.assertEqual(self.store.released, ["run:abc"])

    def test_no_owner_means_no_lease_release(self):
        # 直调(CLI/测试)不涉租约,不误调 release。
        runner.advance("t-1", "wo-1")
        self.assertEqual(self.store.released, [])


class RequestRunTests(RunnerTestBase):
    """推进原语(MC2-A1 ①):抢租约 → 落 run_requested → 派发,四个入口的单一事实源。"""

    def setUp(self):
        super().setUp()
        self.spawned = []
        self._patch("_spawn_advance", lambda t, w, o: self.spawned.append((t, w, o)))

    def test_acquired_appends_request_and_spawns_daemon(self):
        owner = runner.request_run("t-1", "wo-1", actor="user:u1")
        self.assertTrue(owner.startswith("run:"))
        self.assertEqual(self.store.acquired, [owner])
        evt = self.store.events[-1]
        self.assertEqual(evt["event_type"], runner.EVT_RUN_REQUESTED)
        self.assertEqual(evt["actor"], "user:u1")
        self.assertEqual(self.spawned, [("t-1", "wo-1", owner)])

    def test_lease_held_returns_none_without_event_or_spawn(self):
        self.store.acquire_result = False
        self.assertIsNone(runner.request_run("t-1", "wo-1", actor="user:u1"))
        self.assertEqual(self.store.events, [])
        self.assertEqual(self.spawned, [])

    def test_background_tasks_dispatch_replaces_thread(self):
        # 路由径优化:BackgroundTasks 在场时用之(响应返回后才起跑),不再另起守护线程。
        from unittest import mock

        bg = mock.Mock()
        owner = runner.request_run("t-1", "wo-1", actor="user:u1", background=bg)
        bg.add_task.assert_called_once_with(runner.advance, "t-1", "wo-1", owner)
        self.assertEqual(self.spawned, [])

    def test_custom_lease_strategy_and_payload(self):
        # 租约获取策略参数化(收尸 claim / 驳回同事务翻状态都走这一口)。闭包返 False = 不该跑。
        calls = []

        def lease(cur, *, tenant_id, work_order_id, owner, ttl_seconds):
            calls.append(owner)
            return False

        self.assertIsNone(runner.request_run("t-1", "wo-1", actor="x", lease=lease))
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.store.acquired, [])  # 缺省策略未被误用
        self.assertEqual(self.store.events, [])

    def test_explicit_owner_is_honored(self):
        owner = runner.request_run("t-1", "wo-1", actor="system:reaper", owner="reaper:abc")
        self.assertEqual(owner, "reaper:abc")
        self.assertEqual(self.spawned, [("t-1", "wo-1", "reaper:abc")])


if __name__ == "__main__":
    unittest.main()
