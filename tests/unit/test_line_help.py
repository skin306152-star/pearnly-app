# -*- coding: utf-8 -*-
"""能力问答确定性接住(line_help)守门。

铁三条:① 只接「无数字+短句」的 capability/upload 纯问法(contains 误伤面
「ค่าอาหารตามเมนู 250」绝不许被吃掉);② 泰语回 A2 图卡、其他语言回四语文案,
都挂第一单 chips;③ 任何故障 fail-open 返 False 回原路。
"""

import unittest
from unittest.mock import patch

from services.line_binding import line_help

_USER = {"id": "u1", "tenant_id": "t1"}


def _run(text, lang="th", kind="capability", reply_ok=True):
    sent = {}

    def fake_reply(reply_token, msgs, **kw):
        sent["msgs"] = msgs
        return reply_ok

    with patch("services.line_binding.line_reply.reply_messages_context", fake_reply):
        consumed = line_help.maybe_reply(_USER, "rt", "U1", text, lang, kind, "qt")
    return consumed, sent.get("msgs")


class TestLineHelp(unittest.TestCase):
    def test_thai_pure_ask_gets_card_with_chips(self):
        consumed, msgs = _run("ทำอะไรได้บ้าง", lang="th")
        self.assertTrue(consumed)
        self.assertEqual(msgs[0]["type"], "imagemap")  # A2 泰语能力图卡
        actions = [it["action"]["type"] for it in msgs[0]["quickReply"]["items"]]
        self.assertIn("camera", actions)  # 答完直通第一单

    def test_other_lang_gets_text_capability(self):
        consumed, msgs = _run("你能做什么", lang="zh")
        self.assertTrue(consumed)
        self.assertEqual(msgs[0]["type"], "text")
        self.assertTrue(msgs[0]["text"])
        self.assertIn("quickReply", msgs[0])

    def test_amount_sentence_never_eaten(self):
        # 「ตามเมนู 250」contains 命中 เมนู,但带数字=可能是记账 → 必须放行原路
        consumed, _ = _run("ค่าอาหารตามเมนู 250", kind="capability")
        self.assertFalse(consumed)

    def test_long_sentence_passes_through(self):
        consumed, _ = _run("ช่วยอะไร" + "ก" * 40)
        self.assertFalse(consumed)

    def test_non_help_kind_passes_through(self):
        for kind in (None, "greeting", "thanks", "fraud_refuse"):
            consumed, _ = _run("สวัสดี", kind=kind)
            self.assertFalse(consumed, kind)

    def test_reply_failure_falls_open(self):
        with patch(
            "services.line_binding.line_reply.reply_messages_context",
            side_effect=RuntimeError("line down"),
        ):
            self.assertFalse(line_help.maybe_reply(_USER, "rt", "U1", "help", "en", "capability"))


if __name__ == "__main__":
    unittest.main()
