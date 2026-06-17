# -*- coding: utf-8 -*-
"""LINE 大脑契约(Brain OS · P1E-1 收口):LLM 只分类不开口 — chat_kind 枚举,无自由 reply、无 demo。"""

import unittest
from unittest import mock

from services.expense import line_agent


class PromptContractTests(unittest.TestCase):
    def test_no_user_facing_demo_in_prompt(self):
        p = line_agent._PROMPT
        for demo in ("coffee 65", "กาแฟ 65", "咖啡65", "ค่าน้ำ 50"):
            self.assertNotIn(demo, p, f"prompt 不应含可能漏给用户的 demo:{demo}")

    def test_prompt_has_chat_kind_not_reply(self):
        p = line_agent._PROMPT
        self.assertIn("chat_kind", p)
        self.assertNotIn('"reply"', p)  # 不再让 LLM 产出用户可见 reply

    def test_chat_kinds_enum_complete(self):
        for k in (
            "greeting",
            "capability",
            "receipt_help",
            "edit_help",
            "delete_help",
            "photo_failed_help",
            "out_of_scope",
            "unknown",
        ):
            self.assertIn(k, line_agent.CHAT_KINDS)


class UnderstandNormalizeTests(unittest.TestCase):
    """understand 归一:chat/out_of_scope 必出合法 chat_kind;其它意图 chat_kind 清空。"""

    def _run(self, raw):
        with mock.patch(
            "services.ocr.layer2_gemini._call_gemini_with_retry", return_value=(raw, {})
        ):
            return line_agent.understand("x", api_key="k")

    def test_chat_missing_kind_defaults_unknown(self):
        out = self._run({"intent": "chat", "speech_act": "question"})
        self.assertEqual(out["chat_kind"], "unknown")

    def test_out_of_scope_defaults_kind(self):
        out = self._run({"intent": "out_of_scope", "speech_act": "statement"})
        self.assertEqual(out["chat_kind"], "out_of_scope")

    def test_record_clears_chat_kind(self):
        out = self._run({"intent": "record", "speech_act": "statement", "chat_kind": "capability"})
        self.assertEqual(out["chat_kind"], "")

    def test_valid_capability_kept(self):
        out = self._run({"intent": "chat", "speech_act": "question", "chat_kind": "capability"})
        self.assertEqual(out["chat_kind"], "capability")


if __name__ == "__main__":
    unittest.main()
