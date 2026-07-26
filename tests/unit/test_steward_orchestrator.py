# -*- coding: utf-8 -*-
"""管家单轮编排(services/steward/orchestrator.py · B2-M1)。

锁四件事:①参数接地拒编造值(模型给的客户名不在用户原话里 → 追问,工具一步不跑);
②期间线索解不出就追问,绝不拿猜的账期去查;③挑中工具的每一轮都真落任务行(先 running
再终态),不许"回复里说查了、库里查无此任务";④大脑降级/超范围不造假任务。
零真 DB:core.db.get_cursor 与 store 写函数是注入点。
"""

from __future__ import annotations

import unittest
from datetime import date
from unittest import mock

from services.agent.contracts import ToolResult
from services.steward import orchestrator, registry
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
    """一轮的注入面:planner.plan 结果 + tools.run 结果,任务写库记在 tasks 列表里。"""

    def __init__(self, plan, tool_result=None):
        self.plan = plan
        self.tool_result = tool_result
        self.tasks = []
        self.tool_calls = []

    def _create_task(self, _cur, **kw):
        self.tasks.append(kw)
        return {"id": "task-1"}

    def _run(self, name, ctx, args):
        self.tool_calls.append((name, args))
        return self.tool_result

    def turn(self, text, history=None):
        with (
            mock.patch.object(orchestrator.planner, "plan", return_value=self.plan),
            mock.patch.object(orchestrator.tools, "run", self._run),
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

    def test_grounded_client_name_reaches_tool(self):
        h = _TurnHarness(
            _plan(registry.CLIENT_STATUS, {"client_name": "Sister"}),
            ToolResult(
                ok=True, data={"client_name": "Sister", "period": "2569-06", "has_order": False}
            ),
        )
        out = h.turn("Sister 上个月怎么样")
        self.assertEqual(h.tool_calls[0][0], registry.CLIENT_STATUS)
        self.assertEqual(h.tool_calls[0][1]["client_name"], "Sister")
        self.assertEqual(out["task_status"], "done")

    def test_period_hint_normalised_to_buddhist_period(self):
        h = _TurnHarness(
            _plan(registry.MATRIX_OVERVIEW, {"period": "上个月"}),
            ToolResult(ok=True, data={"period": "2569-06", "client_count": 0, "badges": {}}),
        )
        h.turn("上个月谁缺料")
        self.assertEqual(h.tool_calls[0][1]["period"], "2569-06")

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
    def test_task_written_running_first_then_finished(self):
        """先落 running(左窗立刻有得看/进程死也不骗人),终态随真实结果回填。"""
        h = _TurnHarness(
            _plan(registry.MATRIX_OVERVIEW, {}),
            ToolResult(
                ok=True,
                data={
                    "period": "2569-07",
                    "client_count": 3,
                    "missing_order": 1,
                    "badges": {"missing_materials": 2, "pending_review": 1, "in_progress": 0},
                    "attention": [],
                },
            ),
        )
        out = h.turn("本期谁缺料")
        self.assertEqual(h.tasks[0]["status"], "running")
        self.assertEqual([s["state"] for s in h.tasks[0]["steps"]], ["done", "running", "queued"])
        self.assertEqual(out["task_status"], "done")
        self.assertEqual([s["state"] for s in out["steps"]], ["done", "done", "done"])
        self.assertIn("3", out["reply"])
        self.assertTrue(any(a["kind"] == "deeplink" for a in out["artifacts"]))

    def test_tool_failure_marks_task_failed_and_explains(self):
        h = _TurnHarness(
            _plan(registry.CLIENT_STATUS, {"client_name": "Sister"}),
            ToolResult(
                ok=False,
                error_code="steward.client_not_found",
                data={"keyword": "Sister", "candidates": []},
            ),
        )
        out = h.turn("Sister 怎么样")
        self.assertEqual(out["task_status"], "failed")
        self.assertEqual(out["steps"][1]["state"], "failed")
        self.assertIn("Sister", out["reply"])
        self.assertEqual(
            out["tool_trace"],
            [{"tool": registry.CLIENT_STATUS, "ok": False, "error": "steward.client_not_found"}],
        )

    def test_degraded_turn_creates_no_task(self):
        h = _TurnHarness(_plan(registry.OUT_OF_SCOPE, degraded=True, reason="brain_timeout"))
        out = h.turn("本期谁缺料")
        self.assertEqual(h.tasks, [])
        self.assertIsNone(out.get("task_id"))
        self.assertIn("连不上", out["reply"])

    def test_out_of_scope_creates_no_task_and_uses_model_words(self):
        h = _TurnHarness(_plan(registry.OUT_OF_SCOPE, message="这一版我还不能改数据"))
        out = h.turn("帮我把这张票推进 ERP")
        self.assertEqual(h.tasks, [])
        self.assertIsNone(out.get("task_id"))
        self.assertEqual(out["reply"], "这一版我还不能改数据")

    def test_out_of_scope_without_message_falls_back_to_capability_list(self):
        h = _TurnHarness(_plan(registry.OUT_OF_SCOPE))
        out = h.turn("今天天气怎么样")
        self.assertIn("只能查", out["reply"])


if __name__ == "__main__":
    unittest.main()
