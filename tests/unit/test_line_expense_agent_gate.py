# -*- coding: utf-8 -*-
"""WP5 钥匙闸分流(保命绳):闸关=逐字节旧路 · 闸开+有工具=Agent 接管 · 无工具意图=defer 旧路。

★ 能力只增不减 + 关闸逐字节回退是 WP5 两条最硬约束,这里用真实 handle_expense_text 端到端验。
确定性前置过滤(闲聊/记账/改错路由)统一 mock 成"放行到大脑步",只在那一步观察分流。
"""

import unittest
from contextlib import ExitStack, contextmanager
from unittest.mock import MagicMock, patch

from services.line_binding import line_expense

_BOUND = {"id": "u1", "tenant_id": "t1"}


class _NoAmount:
    def has_amount(self):
        return False


@contextmanager
def _fake_cursor(*a, **k):
    yield MagicMock()


# 把确定性前置过滤一律放行到「大脑步」,使分流可观察。
_DETERMINISTIC = {
    "services.expense.line_classify.normalize_user_text": lambda x: x,
    "services.line_binding.line_chat_memory.recent": lambda **k: [],
    "services.line_binding.line_chat_memory.note": lambda **k: None,
    "services.expense.replies.detect_smalltalk": lambda t: None,
    "services.purchase.intake.line_expense_gate_open": lambda cur, tenant_id: True,
    "core.workspace_context.default_workspace_id": lambda cur, tid: 1,
    "services.expense.line_correct_flow.route": lambda *a, **k: False,
    "services.expense.line_quick_entry.l1_intent": lambda t: None,
    "services.expense.line_quick_entry.is_question": lambda t: False,
    "services.expense.line_quick_entry.is_nonassertive": lambda t: False,
    "services.expense.line_quick_entry.is_edit_request": lambda t: False,
    "services.expense.line_quick_entry.detect_income": lambda t: False,
    "services.expense.line_quick_entry.parse_multi": lambda t: None,
    "services.expense.line_quick_entry.has_item_context": lambda t: False,
    "services.expense.line_quick_entry.parse_expense": lambda t: _NoAmount(),
}


class TestAgentGate(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        for target, fn in _DETERMINISTIC.items():
            self.stack.enter_context(patch(target, fn))
        self.stack.enter_context(patch("core.db.get_cursor_rls", _fake_cursor))
        # 回复出口 + 老 LLM 入口可观察
        self.reply = self.stack.enter_context(
            patch("services.line_binding.line_reply.reply_text_context")
        )
        self.understand = self.stack.enter_context(
            patch("services.expense.line_agent.understand", return_value=None)
        )
        self.stack.enter_context(
            patch("services.expense.line_l2.resolve_api_key", return_value="k")
        )
        self.stack.enter_context(patch.object(line_expense, "_ocr_balance_ok", return_value=True))
        self.charge = self.stack.enter_context(
            patch.object(line_expense, "_charge_line_l2", return_value=None)
        )

    def tearDown(self):
        self.stack.close()

    def _call(self, text="ดูประวัติ"):
        return line_expense.handle_expense_text(_BOUND, "rt", "U1", text, "th")

    def test_flag_off_runs_legacy_untouched(self):
        # 闸关:Agent 完全不进,逐字节走旧 understand()。
        with (
            patch("core.feature_flags.agent_enabled_for", return_value=False),
            patch("services.agent.loop.handle_turn") as ht,
        ):
            self._call()
            ht.assert_not_called()
            self.understand.assert_called_once()

    def test_agent_owns_readonly_query(self):
        # 前门:模型撰写人话回复 → Agent 接管,原文直出(不套模板),旧 understand 不跑,计费扣 1。
        with (
            patch("core.feature_flags.agent_enabled_for", return_value=True),
            patch("services.agent.loop.handle_turn", return_value="คุณมีเอกสาร 3 ใบ"),
        ):
            ok = self._call()
        self.assertTrue(ok)
        self.understand.assert_not_called()
        self.charge.assert_called_once()
        body = self.reply.call_args.args[1]
        self.assertEqual(body, "คุณมีเอกสาร 3 ใบ")  # 模型原文,前门不再套模板/渲染 key

    def test_undo_defers_and_legacy_undo_runs(self):
        # ★ 灰度用户「撤销上一笔」:新 loop 无 undo 工具 → 真实 defer → 旧路成功撤销(能力不丢)。
        undo = self.stack.enter_context(
            patch("services.line_binding.line_expense_qa.reply_undo", return_value=True)
        )
        self.understand.return_value = {"intent": "undo"}
        with (
            patch("core.feature_flags.agent_enabled_for", return_value=True),
            patch("services.agent.loop.handle_turn", return_value=None),  # 模型 defer(无 undo 工具)
        ):
            ok = self._call("ยกเลิกรายการล่าสุด")
        self.assertTrue(ok)
        self.understand.assert_called_once()  # 落回旧大脑
        undo.assert_called_once()  # 旧撤销真的执行了

    def test_insufficient_balance_skips_agent(self):
        # 余额不够:Agent 不进(与旧 L2 同口径),不调新 loop。
        with (
            patch.object(line_expense, "_ocr_balance_ok", return_value=False),
            patch("core.feature_flags.agent_enabled_for", return_value=True),
            patch("services.agent.loop.handle_turn") as ht,
        ):
            self._call()
            ht.assert_not_called()


if __name__ == "__main__":
    unittest.main()
