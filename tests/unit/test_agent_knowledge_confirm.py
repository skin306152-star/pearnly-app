# -*- coding: utf-8 -*-
"""知识库问答 confirm-first 全链(备料 → 确认卡 → postback 消费 → 执行 → 扣费口径)。

钱路红线:工具备料绝不检索不扣费;未点确认 = 零检索零扣费;nonce 一次性(双击按
失效卡);no_answer 不扣费;检索/生成失败不扣费且诚实告知;细闸关 → 诚实拒。
"""

import json
import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from services.agent import knowledge_confirm
from services.agent.contracts import AgentContext
from services.agent.executor import AgentToolset
from services.line_binding import line_postback

_CTX = AgentContext(user={"id": "u1", "tenant_id": "t1", "plan": "pro"}, tenant_id="t1")
_BOUND = {"id": "u1", "tenant_id": "t1", "plan": "pro", "line_user_id": "U1"}


@contextmanager
def _fake_cursor(*a, **k):
    yield MagicMock()


class TestPrepare(unittest.TestCase):
    """executor.ask_knowledge 只备料:闸关诚实拒,任何分支不检索不扣费。"""

    def test_gate_closed_refuses(self):
        with patch("core.feature_flags.agent_knowledge_enabled_for", return_value=False):
            res = AgentToolset().ask_knowledge(_CTX, question="VAT คืออะไร")
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, "not_available_yet")

    def test_gate_open_passes_question(self):
        with patch("core.feature_flags.agent_knowledge_enabled_for", return_value=True):
            res = AgentToolset().ask_knowledge(_CTX, question=" ภาษีหัก ณ ที่จ่าย ")
        self.assertTrue(res.ok)
        self.assertEqual(res.data, {"question": "ภาษีหัก ณ ที่จ่าย"})

    def test_empty_question_refuses(self):
        with patch("core.feature_flags.agent_knowledge_enabled_for", return_value=True):
            res = AgentToolset().ask_knowledge(_CTX, question="  ")
        self.assertFalse(res.ok)


class TestConfirmCard(unittest.TestCase):
    def test_card_has_nonce_buttons_and_no_search(self):
        sent = []
        with (
            patch("core.db.get_cursor_rls", _fake_cursor),
            patch("services.line_binding.line_action_nonce.mint", return_value="TOK1") as mint,
            patch(
                "services.line_binding.line_reply.reply_messages_context",
                lambda rt, msgs, **k: sent.append(msgs),
            ),
            patch("services.knowledge.embedding.embed_texts") as embed,
        ):
            ok = knowledge_confirm.send_confirm_card(
                _BOUND, "rt", "VAT ขายของออนไลน์ต้องจดไหม", "th", "t1", "U1"
            )
        self.assertTrue(ok)
        embed.assert_not_called()  # 出卡 ≠ 检索
        ref = json.loads(mint.call_args.kwargs["action_ref"])
        self.assertEqual(ref["kind"], "agent_kb")
        self.assertIn("VAT", ref["q"])
        actions = sent[0][0]["template"]["actions"]
        self.assertIn("TOK1", actions[0]["data"])
        self.assertEqual(
            line_postback.parse(actions[0]["data"])["action"],
            line_postback.ACTION_AGENT_KB_CONFIRM,
        )
        self.assertEqual(
            line_postback.parse(actions[1]["data"])["action"],
            line_postback.ACTION_AGENT_KB_CANCEL,
        )

    def test_mint_failure_returns_false(self):
        with (
            patch("core.db.get_cursor_rls", _fake_cursor),
            patch("services.line_binding.line_action_nonce.mint", return_value=""),
        ):
            self.assertFalse(
                knowledge_confirm.send_confirm_card(_BOUND, "rt", "q", "th", "t1", "U1")
            )

    def test_empty_question_returns_false(self):
        self.assertFalse(knowledge_confirm.send_confirm_card(_BOUND, "rt", " ", "th", "t1", "U1"))


class TestPostback(unittest.TestCase):
    def _ref(self):
        return json.dumps({"kind": "agent_kb", "q": "VAT คืออะไร"})

    def _run(self, action, consume, *, balance=100.0, exempt=False, runner=None):
        says = []
        ran = []
        runner = runner or (lambda fn: ran.append(fn))
        with (
            patch("core.db.get_cursor_rls", _fake_cursor),
            patch("services.line_binding.line_action_nonce.consume", return_value=consume),
            patch(
                "services.line_binding.line_reply.reply_text_context",
                lambda rt, body, **k: says.append(body),
            ),
            patch("services.line_binding.line_client.t_line", lambda lang, key, **k: f"[{key}]"),
            patch(
                "core.db.get_billing_status_combined",
                return_value={"is_exempt": exempt, "balance_thb": balance},
            ),
        ):
            knowledge_confirm.handle_postback(_BOUND, "rt", action, "TOK1", "th", runner=runner)
        return says, ran

    def test_confirm_acks_and_schedules_execution(self):
        says, ran = self._run(
            line_postback.ACTION_AGENT_KB_CONFIRM, {"status": "ok", "action_ref": self._ref()}
        )
        self.assertEqual(len(ran), 1)
        self.assertIn(says[0], knowledge_confirm._ACK.values())

    def test_cancel_never_executes(self):
        says, ran = self._run(
            line_postback.ACTION_AGENT_KB_CANCEL, {"status": "ok", "action_ref": self._ref()}
        )
        self.assertEqual(ran, [])
        self.assertTrue(says)

    def test_double_click_used_is_stale(self):
        says, ran = self._run(
            line_postback.ACTION_AGENT_KB_CONFIRM, {"status": "used", "action_ref": self._ref()}
        )
        self.assertEqual(ran, [])
        self.assertEqual(says[0], "[card_action_stale]")

    def test_insufficient_balance_blocks_before_spend(self):
        says, ran = self._run(
            line_postback.ACTION_AGENT_KB_CONFIRM,
            {"status": "ok", "action_ref": self._ref()},
            balance=0.2,
        )
        self.assertEqual(ran, [])
        self.assertIn(says[0], knowledge_confirm._NO_BALANCE.values())

    def test_exempt_low_balance_still_runs(self):
        says, ran = self._run(
            line_postback.ACTION_AGENT_KB_CONFIRM,
            {"status": "ok", "action_ref": self._ref()},
            balance=0.0,
            exempt=True,
        )
        self.assertEqual(len(ran), 1)


class TestAnswerChargePolicy(unittest.TestCase):
    def _answer(self, *, no_answer, citations=None, raise_search=False):
        charged = []
        hit_result = MagicMock(
            answer="คำตอบ [1]", no_answer=no_answer, citations=citations or [], model="m"
        )
        answer_row = MagicMock(id=7)
        with (
            patch("core.db.get_visible_client_ids_for_user", return_value=None),
            patch("core.db.get_cursor_rls", _fake_cursor),
            patch("services.knowledge.embedding.embed_texts", return_value=[[0.1]]),
            patch(
                "services.knowledge.search.search_chunks",
                (
                    MagicMock(side_effect=RuntimeError("boom"))
                    if raise_search
                    else MagicMock(return_value=[])
                ),
            ),
            patch("services.knowledge.ask.answer_question", return_value=hit_result),
            patch("services.knowledge.dal.create_answer", return_value=answer_row),
            patch(
                "services.knowledge.contract.charge_credits",
                lambda tid, kind, amount, meta: charged.append((kind, amount, meta)),
            ),
        ):
            text = knowledge_confirm._answer(_BOUND, "t1", "VAT คืออะไร", "th")
        return text, charged

    def test_answered_charges_50_satang_once(self):
        text, charged = self._answer(no_answer=False, citations=[{"n": 1}])
        self.assertEqual(len(charged), 1)
        kind, amount, meta = charged[0]
        self.assertEqual((kind, amount), ("rag_answer", 50))
        self.assertEqual(meta["channel"], "line_agent")
        self.assertIn("คำตอบ", text)

    def test_no_answer_not_charged(self):
        text, charged = self._answer(no_answer=True)
        self.assertEqual(charged, [])
        self.assertIn(text, knowledge_confirm._NO_ANSWER.values())

    def test_search_failure_not_charged_and_honest(self):
        says = []
        with (
            patch.object(knowledge_confirm, "_answer", side_effect=RuntimeError("boom")),
            patch(
                "services.line_binding.line_reply.push_text_context",
                lambda luid, text, **k: says.append(text),
            ),
        ):
            knowledge_confirm._execute_and_notify(_BOUND, "t1", "q", "th", "U1")
        self.assertIn(says[0], knowledge_confirm._FAIL.values())


if __name__ == "__main__":
    unittest.main()
