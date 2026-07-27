# -*- coding: utf-8 -*-
"""管家单轮编排(services/steward/orchestrator.py · B3 异步)。

锁四件事:①参数接地拒编造值(模型给的客户名不在用户原话里 → 追问,工具一步不跑);
②期间线索解不出就追问,绝不拿猜的账期去查;③挑中工具的每一轮都真落任务行(入队
running + payload 带全执行上下文,请求内不跑工具 —— 执行归 worker,见
test_steward_async);④大脑降级/超范围不造假任务。
零真 DB:core.db.get_cursor 与 store 写函数是注入点。
"""

from __future__ import annotations

import unittest
from datetime import date
from unittest import mock

from services.steward import orchestrator, registry, tools
from services.steward.registry import ToolContext

_TODAY = date(2026, 7, 26)  # 佛历 2569-07


def _ctx():
    return ToolContext(
        user={"id": "u1", "tenant_id": "t-1"},
        tenant_id="t-1",
        user_id="u1",
        lang="zh",
        today=_TODAY,
    )


class _CurCM:
    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


class _TurnHarness:
    """一轮的注入面:planner.plan 结果注入,任务写库记在 tasks 列表里。
    tools.run 也挂了记录桩:B3 起请求内一步工具都不许跑,tool_calls 必须恒空。"""

    def __init__(self, plan):
        self.plan = plan
        self.tasks = []
        self.tool_calls = []

    def _create_task(self, _cur, **kw):
        self.tasks.append(kw)
        return {"id": "task-1"}

    def _run(self, name, ctx, args):
        self.tool_calls.append((name, args))
        raise AssertionError("tools.run must not be called inside the request")

    def turn(self, text, history=None):
        with (
            mock.patch.object(orchestrator.planner, "plan", return_value=self.plan),
            mock.patch.object(tools, "run", self._run),
            mock.patch.object(orchestrator.store, "create_task", self._create_task),
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM()),
        ):
            return orchestrator._turn(_ctx(), text=text, history=history or [], session_id="s-1")


def _plan(tool, args=None, *, degraded=False, reason=None, message=""):
    return {
        "degraded": degraded,
        "reason": reason,
        "tool": tool,
        "args": args or {},
        "message": message,
    }


class GroundingTests(unittest.TestCase):
    def test_fabricated_client_name_is_refused_and_asked_back(self):
        """模型把 "Sister" 补全成名录全名(用户没这么说)→ 接地闸拒 → 追问,工具零调用。"""
        h = _TurnHarness(_plan(registry.CLIENT_STATUS, {"client_name": "Sister Makeup Co.,Ltd."}))
        out = h.turn("Sister 这个月怎么样")
        self.assertEqual(h.tool_calls, [])
        self.assertIn("哪一家客户", out["reply"])
        self.assertEqual(out["task_status"], "waiting_user")
        self.assertEqual(h.tasks[0]["status"], "waiting_user")

    def test_grounded_client_name_reaches_task_payload(self):
        h = _TurnHarness(_plan(registry.CLIENT_STATUS, {"client_name": "Sister"}))
        out = h.turn("Sister 上个月怎么样")
        self.assertEqual(h.tool_calls, [])
        payload = h.tasks[0]["payload"]
        self.assertEqual(payload["tool"], registry.CLIENT_STATUS)
        self.assertEqual(payload["args"]["client_name"], "Sister")
        self.assertEqual(out["task_status"], "running")

    def test_period_hint_normalised_to_buddhist_period(self):
        h = _TurnHarness(_plan(registry.MATRIX_OVERVIEW, {"period": "上个月"}))
        h.turn("上个月谁缺料")
        self.assertEqual(h.tasks[0]["payload"]["args"]["period"], "2569-06")

    def test_unparsable_period_asks_back_instead_of_guessing(self):
        h = _TurnHarness(_plan(registry.MATRIX_OVERVIEW, {"period": "下辈子"}))
        out = h.turn("下辈子谁缺料")
        self.assertEqual(h.tool_calls, [])
        self.assertIn("哪一期", out["reply"])

    def test_missing_required_slot_asks_back(self):
        h = _TurnHarness(_plan(registry.HISTORY_QUERY, {}))
        out = h.turn("帮我找张票")
        self.assertEqual(h.tool_calls, [])
        self.assertEqual(out["task_status"], "waiting_user")
        self.assertIn("店名", out["reply"])


class TaskPersistenceTests(unittest.TestCase):
    def test_tool_turn_enqueues_running_task_and_acks(self):
        """挑中工具即入队:任务行 running + 步骤全排队 + payload 带全执行上下文,
        请求内一步工具不跑(执行/收尾归 worker),回复是应承话不是冒领的结果。"""
        h = _TurnHarness(_plan(registry.MATRIX_OVERVIEW, {}))
        out = h.turn("本期谁缺料")
        self.assertEqual(h.tool_calls, [])
        self.assertEqual(h.tasks[0]["status"], "running")
        self.assertEqual([s["state"] for s in h.tasks[0]["steps"]], ["done", "queued", "queued"])
        payload = h.tasks[0]["payload"]
        self.assertEqual(payload["tool"], registry.MATRIX_OVERVIEW)
        self.assertEqual(payload["user_id"], "u1")
        self.assertIsNone(payload["allowed_client_ids"])
        self.assertTrue(out["deferred"])
        self.assertEqual(out["task_status"], "running")
        self.assertEqual(out["artifacts"], [])
        self.assertIn("查本期矩阵", out["reply"])
        self.assertEqual(
            out["tool_trace"], [{"tool": registry.MATRIX_OVERVIEW, "ok": None, "error": None}]
        )

    def test_scope_snapshot_travels_with_the_task(self):
        """被分派成员的账套作用域随任务定格 —— worker 没有请求可算,绝不放宽成看全租户。"""
        h = _TurnHarness(_plan(registry.MATRIX_OVERVIEW, {}))
        ctx = _ctx()
        ctx.allowed_client_ids = frozenset({7, 3})
        with (
            mock.patch.object(orchestrator.planner, "plan", return_value=h.plan),
            mock.patch.object(orchestrator.store, "create_task", h._create_task),
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM()),
        ):
            orchestrator._turn(ctx, text="本期谁缺料", history=[], session_id="s-1")
        self.assertEqual(h.tasks[0]["payload"]["allowed_client_ids"], [3, 7])

    def test_degraded_turn_creates_no_task(self):
        h = _TurnHarness(_plan(registry.OUT_OF_SCOPE, degraded=True, reason="brain_timeout"))
        out = h.turn("本期谁缺料")
        self.assertEqual(h.tasks, [])
        self.assertIsNone(out.get("task_id"))
        self.assertIn("无法处理指令", out["reply"])

    def test_out_of_scope_creates_no_task_and_uses_model_words(self):
        h = _TurnHarness(_plan(registry.OUT_OF_SCOPE, message="这一版我还不能改数据"))
        out = h.turn("帮我把这张票推进 ERP")
        self.assertEqual(h.tasks, [])
        self.assertIsNone(out.get("task_id"))
        self.assertEqual(out["reply"], "这一版我还不能改数据")

    def test_out_of_scope_without_message_falls_back_to_capability_list(self):
        h = _TurnHarness(_plan(registry.OUT_OF_SCOPE))
        out = h.turn("今天天气怎么样")
        self.assertIn("能查", out["reply"])
        # 能力清单必须与注册表实情一致:写工具挂上了就得说出来,不然产品在撒谎。
        self.assertIn("Express", out["reply"])


class WriteToolEnqueueTests(unittest.TestCase):
    """写工具入队走 confirm-first(审查缺陷:闸有了、铸卡方缺位):_enqueue 必须在同一
    事务里铸授权卡,应承说「先批后动」不说「开跑了」,步骤停 waiting_auth。"""

    _TOOL = "erp_push_draft"

    def setUp(self):
        from services.steward.registry import StewardTool

        spec = StewardTool(
            name=self._TOOL, desc="d", slots=(), handler=self._TOOL, risk=registry.RISK_WRITE
        )
        registry.TOOLS_BY_NAME[self._TOOL] = spec
        self.addCleanup(registry.TOOLS_BY_NAME.pop, self._TOOL, None)

    def test_write_tool_mints_a_card_and_parks_instead_of_running(self):
        from services.steward import authz, store

        h = _TurnHarness(_plan(self._TOOL, {}))
        opened = mock.Mock(return_value={"token": "tok"})
        with mock.patch.object(authz, "open_request", opened):
            out = h.turn("把这张草稿推进 ERP")
        self.assertEqual(h.tool_calls, [])
        kwargs = opened.call_args.kwargs
        self.assertEqual(kwargs["tool"], self._TOOL)
        self.assertEqual(kwargs["task_id"], "task-1")
        self.assertEqual(kwargs["requested_by"], "u1")
        self.assertEqual(out["task_status"], store.TASK_WAITING_USER)
        self.assertIn(store.STEP_WAITING_AUTH, [s["state"] for s in out["steps"]])
        self.assertIn("授权卡", out["reply"])
        self.assertNotIn("开跑", out["reply"])

    def test_readonly_tool_still_enqueues_running_without_a_card(self):
        from services.steward import authz, store

        h = _TurnHarness(_plan(registry.MATRIX_OVERVIEW, {}))
        opened = mock.Mock()
        with mock.patch.object(authz, "open_request", opened):
            out = h.turn("本期谁缺料")
        opened.assert_not_called()
        self.assertEqual(out["task_status"], store.TASK_RUNNING)


if __name__ == "__main__":
    unittest.main()
