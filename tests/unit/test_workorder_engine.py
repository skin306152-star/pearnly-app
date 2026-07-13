# -*- coding: utf-8 -*-
"""工单状态机引擎守门测试(services/workorder/engine.py · 任务包 §6 状态机断言)。

用内存 FakeStore(实现 store 的三个引擎依赖:list_events/append_event/set_status)驱动整条
链,脱库验证编排逻辑本身——store 的 SQL 形状已由 test_workorder_store.py 单独锁。覆盖:
① 正常跑到 package 全绿、落 review;② 某步 stuck/needs 时停下、工单置 stuck、原因入事件;
③ 断点续跑:中途 stuck 修好后续跑从卡点继续,不重复已完成步的事件;④ 幂等:同状态重复
跑,事件不翻倍。
"""

import unittest

from services.workorder import engine
from services.workorder.engine import RunOutcome, StepContext, StepResult


class FakeStore:
    """事件流 + 状态的内存实现(替代真库 DAL)。忽略 cur;list_events 按追加顺序回放。"""

    def __init__(self):
        self.events = []
        self.status = None
        self.current_step = None

    def list_events(self, cur, *, tenant_id, work_order_id):
        return list(self.events)

    def append_event(
        self, cur, *, tenant_id, work_order_id, step, event_type, payload=None, actor="system"
    ):
        row = {
            "id": len(self.events) + 1,
            "step": step,
            "event_type": event_type,
            "payload": payload or {},
            "actor": actor,
        }
        self.events.append(row)
        return row

    def set_status(self, cur, *, tenant_id, work_order_id, status, current_step=None):
        self.status = status
        if current_step is not None:
            self.current_step = current_step

    # 测试断言辅助
    def types(self, step):
        return [e["event_type"] for e in self.events if e["step"] == step]

    def count(self, step, event_type):
        return sum(1 for e in self.events if e["step"] == step and e["event_type"] == event_type)


def _ctx(store, presets=None):
    data = {"_presets": presets} if presets else {}
    return StepContext(cur=None, tenant_id="t-1", work_order_id="wo-1", store=store, data=data)


class StepResultFactoriesTests(unittest.TestCase):
    def test_ok_carries_payload_and_is_not_halted(self):
        r = StepResult.ok(subtotal="123.45")
        self.assertEqual(r.status, engine.STEP_OK)
        self.assertFalse(r.halted)
        self.assertEqual(r.payload, {"subtotal": "123.45"})

    def test_stuck_and_needs_are_halted_with_reasons(self):
        s = StepResult.stuck(["amount_math_fail"])
        n = StepResult.needs(["bank_statement"])
        self.assertTrue(s.halted and n.halted)
        self.assertEqual(s.reasons, ("amount_math_fail",))
        self.assertEqual(n.missing, ("bank_statement",))


class FullChainTests(unittest.TestCase):
    def test_runs_to_package_and_lands_review(self):
        store = FakeStore()
        out = engine.run_work_order(_ctx(store))

        self.assertIsInstance(out, RunOutcome)
        self.assertTrue(out.completed)
        self.assertEqual(out.status, engine.TERMINAL_STATUS)
        self.assertEqual(store.status, "review")
        self.assertEqual(store.current_step, "review")

        # 每个 runnable 步恰好一对 started+done,顺序 = 固定流水线顺序。
        done_order = [e["step"] for e in store.events if e["event_type"] == engine.EVT_DONE]
        self.assertEqual(done_order, list(engine.RUNNABLE_STEPS))
        for step in engine.RUNNABLE_STEPS:
            self.assertEqual(store.count(step, engine.EVT_STARTED), 1)
            self.assertEqual(store.count(step, engine.EVT_DONE), 1)

    def test_ok_payload_flows_into_ctx_and_done_event(self):
        store = FakeStore()
        ctx = _ctx(store, presets={"compute": StepResult.ok(tax_due="30851.33")})
        engine.run_work_order(ctx)

        self.assertEqual(ctx.data.get("tax_due"), "30851.33")
        done = next(
            e for e in store.events if e["step"] == "compute" and e["event_type"] == engine.EVT_DONE
        )
        self.assertEqual(done["payload"], {"tax_due": "30851.33"})


class HaltTests(unittest.TestCase):
    def test_stuck_step_halts_and_marks_order_stuck(self):
        store = FakeStore()
        ctx = _ctx(store, presets={"reconcile": StepResult.stuck(["amount_math_fail"])})
        out = engine.run_work_order(ctx)

        self.assertFalse(out.completed)
        self.assertEqual(out.stopped_at, "reconcile")
        self.assertEqual(store.status, "stuck")
        self.assertEqual(store.current_step, "reconcile")

        # 卡点步:started + stuck,无 done;原因落进事件 payload。
        self.assertEqual(store.types("reconcile"), [engine.EVT_STARTED, engine.EVT_STUCK])
        self.assertEqual(store.count("reconcile", engine.EVT_DONE), 0)
        stuck_evt = store.events[-1]
        self.assertEqual(stuck_evt["payload"], {"reasons": ["amount_math_fail"]})

        # 卡点之后的步一步都不许起。
        self.assertEqual(store.types("compute"), [])
        self.assertEqual(store.types("package"), [])

    def test_needs_step_halts_with_missing_inputs(self):
        store = FakeStore()
        ctx = _ctx(store, presets={"sort": StepResult.needs(["bank_statement"])})
        out = engine.run_work_order(ctx)

        self.assertFalse(out.completed)
        self.assertEqual(out.stopped_at, "sort")
        self.assertEqual(store.status, "stuck")
        self.assertEqual(store.types("sort"), [engine.EVT_STARTED, engine.EVT_NEEDS])
        self.assertEqual(store.events[-1]["payload"], {"missing": ["bank_statement"]})


class ResumeTests(unittest.TestCase):
    def test_resume_continues_from_checkpoint_without_redoing_done_steps(self):
        store = FakeStore()

        # 第一次:reconcile 卡住,intake/sort/classify 已完成。
        first = engine.run_work_order(
            _ctx(store, presets={"reconcile": StepResult.stuck(["amount_math_fail"])})
        )
        self.assertEqual(first.stopped_at, "reconcile")
        done_before = {e["step"] for e in store.events if e["event_type"] == engine.EVT_DONE}
        self.assertEqual(done_before, {"intake", "sort", "classify"})

        # 修好预置结果后续跑(同一 store = 同一事件流)。
        second = engine.run_work_order(_ctx(store))
        self.assertTrue(second.completed)
        self.assertEqual(store.status, "review")

        # 已完成的三步不许再落任何事件(started/done 各仍为 1)。
        for step in ("intake", "sort", "classify"):
            self.assertEqual(store.count(step, engine.EVT_STARTED), 1)
            self.assertEqual(store.count(step, engine.EVT_DONE), 1)

        # 卡点步续跑重试:第一次的 started+stuck 之外,续跑再来一对 started+done。
        self.assertEqual(store.count("reconcile", engine.EVT_STARTED), 2)
        self.assertEqual(store.count("reconcile", engine.EVT_DONE), 1)
        # 卡点之后的步在续跑里首次执行,各恰好一对。
        for step in ("compute", "package"):
            self.assertEqual(store.count(step, engine.EVT_STARTED), 1)
            self.assertEqual(store.count(step, engine.EVT_DONE), 1)


class IdempotencyTests(unittest.TestCase):
    def test_rerun_of_completed_order_adds_no_events(self):
        store = FakeStore()
        engine.run_work_order(_ctx(store))
        n_after_first = len(store.events)

        engine.run_work_order(_ctx(store))
        self.assertEqual(len(store.events), n_after_first)

        # 每个 runnable 步的 step_done 全程只此一条(幂等键 = work_order_id+step)。
        for step in engine.RUNNABLE_STEPS:
            self.assertEqual(store.count(step, engine.EVT_DONE), 1)


class RegistryTests(unittest.TestCase):
    def test_missing_handler_raises_engine_error(self):
        store = FakeStore()
        handlers = engine.default_handlers()
        del handlers["classify"]
        with self.assertRaises(engine.WorkOrderEngineError):
            engine.run_work_order(_ctx(store), handlers=handlers)


class ReopenTests(unittest.TestCase):
    """驳回重做(MC1-b1):step_reopened 撤销 step_done「已完成」判定,令引擎重跑受影响步。"""

    def test_reopen_steps_from_slices_runnable_tail(self):
        self.assertEqual(engine.reopen_steps_from("reconcile"), ("reconcile", "compute", "package"))
        self.assertEqual(engine.reopen_steps_from("bogus"), ())  # 未知步不重开

    def test_reopened_step_reruns_and_reemits_done(self):
        store = FakeStore()
        engine.run_work_order(_ctx(store))  # 跑到 review,全步 step_done
        self.assertEqual(store.count("package", engine.EVT_DONE), 1)

        # 模拟驳回:对受影响步落 step_reopened(append-only)
        for step in engine.reopen_steps_from("reconcile"):
            store.append_event(
                None,
                tenant_id="t-1",
                work_order_id="wo-1",
                step=step,
                event_type=engine.EVT_REOPENED,
            )
        engine.run_work_order(_ctx(store))
        # 重开步各再跑一次(step_done 第二条);未重开步(sort)仍只一条,不重跑
        for step in ("reconcile", "compute", "package"):
            self.assertEqual(store.count(step, engine.EVT_DONE), 2)
        self.assertEqual(store.count("sort", engine.EVT_DONE), 1)
        self.assertEqual(store.status, "review")

    def test_no_reopen_events_preserve_completed_set(self):
        # 无 step_reopened 时行为与旧「step_done 存在即完成」逐字节一致(续跑/幂等不变)。
        store = FakeStore()
        engine.run_work_order(_ctx(store))
        n = len(store.events)
        engine.run_work_order(_ctx(store))
        self.assertEqual(len(store.events), n)


if __name__ == "__main__":
    unittest.main()
