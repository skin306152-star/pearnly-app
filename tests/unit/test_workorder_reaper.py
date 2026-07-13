# -*- coding: utf-8 -*-
"""部署中断工单收尸守门(services/workorder/reaper.py · MC2-0)。

脱库:注入假 db/store,验证 ①死亡判据只认 status=running+租约过期(状态词取
engine.STATUS_RUNNING,抢占单句条件 UPDATE 重验)②事件序列 run_failed(interrupted)
→ run_requested(auto)→ 续跑,租约 owner 原样交给 advance ③熔断:自动重跑限 3 次,
从事件流现算,超限停 stuck 不再爬(去掉熔断逻辑本组必红)④人工重跑重置熔断预算
⑤一单失败不连坐 ⑥同进程 in-flight 可证活不误收。
"""

from __future__ import annotations

import asyncio
import inspect
import unittest

from services.workorder import engine, reaper, runner


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
    def __init__(self, dead=None, events=None, claim=True):
        self.dead = list(dead or [])
        self.events_by_wo = dict(events or {})
        self.claim = claim  # True/False 或 callable(work_order_id) -> bool
        self.scan_calls = []
        self.claim_calls = []
        self.appended = []
        self.released = []
        self.statuses = []

    def ensure_runtime(self):
        pass

    def list_dead_runs(self, cur, *, status, limit):
        self.scan_calls.append({"status": status, "limit": limit})
        return list(self.dead)

    def claim_dead_run(self, cur, *, tenant_id, work_order_id, owner, ttl_seconds, status):
        self.claim_calls.append(
            {"work_order_id": work_order_id, "owner": owner, "ttl": ttl_seconds, "status": status}
        )
        return self.claim(work_order_id) if callable(self.claim) else self.claim

    def list_events(self, cur, *, tenant_id, work_order_id):
        return list(self.events_by_wo.get(work_order_id, []))

    def append_event(
        self, cur, *, tenant_id, work_order_id, step, event_type, payload=None, actor="system"
    ):
        self.appended.append(
            {
                "work_order_id": work_order_id,
                "step": step,
                "event_type": event_type,
                "payload": payload or {},
                "actor": actor,
            }
        )

    def release_run_lease(self, cur, *, tenant_id, work_order_id, owner):
        self.released.append(owner)

    def set_status(self, cur, *, tenant_id, work_order_id, status, current_step=None):
        self.statuses.append({"work_order_id": work_order_id, "status": status})


def _run_requested(actor):
    return {"step": runner.RUN_STEP, "event_type": runner.EVT_RUN_REQUESTED, "actor": actor}


_DEAD = {"id": "wo-1", "tenant_id": "t-1"}


class ReaperTestBase(unittest.TestCase):
    def setUp(self):
        self._patch("db", _FakeDB())
        self.spawned = []
        self._patch("_spawn_advance", lambda t, w, o: self.spawned.append((t, w, o)))

    def _patch(self, name, value):
        orig = getattr(reaper, name)
        setattr(reaper, name, value)
        self.addCleanup(setattr, reaper, name, orig)

    def _use(self, store):
        self.store = store
        self._patch("store", store)
        return store


class DeathCriterionTests(ReaperTestBase):
    def test_scan_and_claim_use_running_status_only(self):
        # 判据单一:扫描与抢占都只认 engine.STATUS_RUNNING(词汇不手打),抢占带收尸 owner。
        store = self._use(_FakeStore(dead=[_DEAD]))
        reaper.reap_dead_runs()
        self.assertEqual(store.scan_calls[0]["status"], engine.STATUS_RUNNING)
        claim = store.claim_calls[0]
        self.assertEqual(claim["status"], engine.STATUS_RUNNING)
        self.assertTrue(claim["owner"].startswith("reaper:"))
        self.assertEqual(claim["ttl"], runner.run_lease_ttl_seconds())

    def test_claim_lost_is_noop(self):
        # 幂等抢占:多 worker 同扫一单,抢不到的一方不落事件、不续跑。
        store = self._use(_FakeStore(dead=[_DEAD], claim=False))
        stats = reaper.reap_dead_runs()
        self.assertEqual(store.appended, [])
        self.assertEqual(self.spawned, [])
        self.assertEqual(stats, {"reaped": 0, "resumed": 0, "halted": 0})

    def test_inflight_alive_order_is_never_reaped(self):
        # 同进程可证活(超长跑批耗过期租约):不抢占、不认死。
        store = self._use(_FakeStore(dead=[_DEAD]))
        runner._inflight.add(("t-1", "wo-1"))
        try:
            reaper.reap_dead_runs()
        finally:
            runner._inflight.discard(("t-1", "wo-1"))
        self.assertEqual(store.claim_calls, [])
        self.assertEqual(store.appended, [])


class AcknowledgeAndResumeTests(ReaperTestBase):
    def test_reap_emits_run_failed_then_auto_requeues_with_same_lease(self):
        store = self._use(_FakeStore(dead=[_DEAD]))
        stats = reaper.reap_dead_runs()

        kinds = [e["event_type"] for e in store.appended]
        self.assertEqual(kinds, [runner.EVT_RUN_FAILED, runner.EVT_RUN_REQUESTED])
        failed, requested = store.appended
        self.assertEqual(failed["payload"]["reason"], reaper.REASON_INTERRUPTED)
        self.assertEqual(failed["actor"], reaper.ACTOR_REAPER)
        self.assertEqual(requested["payload"], {"auto_resume": 1})
        self.assertEqual(requested["actor"], reaper.ACTOR_REAPER)
        # 抢到的租约原样交给 advance(与 /run 同路径),不释放再重抢。
        self.assertEqual(self.spawned, [("t-1", "wo-1", store.claim_calls[0]["owner"])])
        self.assertEqual(store.released, [])
        self.assertEqual(stats, {"reaped": 1, "resumed": 1, "halted": 0})

    def test_one_dead_order_failure_does_not_block_next(self):
        dead = [_DEAD, {"id": "wo-2", "tenant_id": "t-1"}]

        def claim(work_order_id):
            if work_order_id == "wo-1":
                raise RuntimeError("db hiccup")
            return True

        store = self._use(_FakeStore(dead=dead, claim=claim))
        stats = reaper.reap_dead_runs()
        self.assertEqual(stats["resumed"], 1)
        self.assertEqual([e["work_order_id"] for e in store.appended], ["wo-2", "wo-2"])


class BreakerTests(ReaperTestBase):
    def test_breaker_trips_at_limit_and_halts_honestly(self):
        # 咬人测试:去掉熔断(无条件续跑)→ 这里必红。3 次自动重跑用尽 → 只认账不再爬:
        # run_failed(exhausted)+ step_stuck(人话原因)+ 工单置 stuck + 释放租约,不 spawn。
        history = [_run_requested(reaper.ACTOR_REAPER)] * reaper.AUTO_RESUME_LIMIT
        store = self._use(_FakeStore(dead=[_DEAD], events={"wo-1": history}))
        stats = reaper.reap_dead_runs()

        kinds = [e["event_type"] for e in store.appended]
        self.assertEqual(kinds, [runner.EVT_RUN_FAILED, engine.EVT_STUCK])
        self.assertTrue(store.appended[0]["payload"]["auto_resume_exhausted"])
        self.assertIn(reaper.REASON_EXHAUSTED, store.appended[1]["payload"]["reasons"][0])
        self.assertEqual(store.statuses, [{"work_order_id": "wo-1", "status": engine.STATUS_STUCK}])
        self.assertEqual(store.released, [store.claim_calls[0]["owner"]])
        self.assertEqual(self.spawned, [])
        self.assertEqual(stats, {"reaped": 1, "resumed": 0, "halted": 1})

    def test_breaker_resets_after_human_rerun(self):
        # 人工 /run 过一次 = 人已介入,自动重跑预算重置,继续收尸续跑。
        history = [_run_requested(reaper.ACTOR_REAPER)] * reaper.AUTO_RESUME_LIMIT
        history.append(_run_requested("user:zihao"))
        store = self._use(_FakeStore(dead=[_DEAD], events={"wo-1": history}))
        stats = reaper.reap_dead_runs()
        self.assertEqual(stats["resumed"], 1)
        self.assertEqual(len(self.spawned), 1)
        requested = store.appended[-1]
        self.assertEqual(requested["event_type"], runner.EVT_RUN_REQUESTED)
        self.assertEqual(requested["payload"], {"auto_resume": 1})

    def test_auto_resume_count_from_event_stream(self):
        count = reaper.auto_resume_count
        self.assertEqual(count([]), 0)
        self.assertEqual(count([_run_requested("user:a")]), 0)
        self.assertEqual(count([_run_requested(reaper.ACTOR_REAPER)] * 2), 2)
        # 人为请求重置;非 run 步/其它事件不计。
        self.assertEqual(
            count(
                [
                    _run_requested(reaper.ACTOR_REAPER),
                    _run_requested("user:a"),
                    _run_requested(reaper.ACTOR_REAPER),
                    {"step": "classify", "event_type": "item_classified", "actor": "system"},
                    {"step": runner.RUN_STEP, "event_type": runner.EVT_RUN_STARTED, "actor": "x"},
                ]
            ),
            1,
        )


class TickHookTests(ReaperTestBase):
    def test_run_tick_is_coroutine_running_shared_impl(self):
        self.assertTrue(inspect.iscoroutinefunction(reaper.run_tick))
        calls = []
        self._patch("reap_dead_runs", lambda: calls.append(1))
        asyncio.run(reaper.run_tick())
        self.assertEqual(calls, [1])

    def test_recovery_tick_reaches_reaper(self):
        # 巡检挂点:background_loops.run_recovery_tick 必须带到收尸(挂法照 LINE 恢复先例)。
        from services import background_loops as bl

        calls = []
        self._patch("reap_dead_runs", lambda: calls.append(1))
        asyncio.run(bl.run_recovery_tick())
        self.assertEqual(calls, [1])

    def test_startup_reap_runs_before_first_loop_sleep(self):
        # 启动挂点:erp_retry_loop(startup 起的常驻 task)开场即收一次死单,
        # 不等 30s 首 tick——部署重启后的认账/续跑立刻发生。
        import contextlib

        from services import background_loops as bl

        calls = []

        async def fake_tick():
            calls.append(1)

        self._patch("run_tick", fake_tick)
        # 收尸后 loop 进 30s sleep;wait_for 掐断它,只验证开场那一步。

        async def main():
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(bl.erp_retry_loop(), timeout=0.3)

        asyncio.run(main())
        self.assertEqual(calls, [1])

    def test_run_tick_swallows_failures(self):
        # 挂点安全:收尸失败只记日志,startup / 巡检 loop 不被炸死。
        def boom():
            raise RuntimeError("db down")

        self._patch("reap_dead_runs", boom)
        asyncio.run(reaper.run_tick())  # 不应 raise


if __name__ == "__main__":
    unittest.main()
