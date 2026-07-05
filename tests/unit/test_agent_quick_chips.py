# -*- coding: utf-8 -*-
"""quick-reply chips(P2)契约。

铁三条:① 四语齐全、label 不超 LINE 20 字硬限、语言跟用户本条消息文字系统(与回复正文同源);
② 闸开 → 回复/安全兜底带 quickReply;③ 闸关/发送失败/异常 → 纯文本 say,绝不丢回复。
"""

import unittest
from unittest.mock import patch

from services.agent import quick_chips
from services.agent.loop import TurnResult
from services.line_binding import line_agent_route as route


class TestChipsPayload(unittest.TestCase):
    def test_four_langs_and_label_limit(self):
        for lang, chips in quick_chips._CHIPS.items():
            self.assertEqual(len(chips), 3, lang)
            for label, text in chips:
                self.assertLessEqual(len(label), 20, f"{lang}:{label}")  # LINE label 硬限
                self.assertTrue(text, f"{lang}:{label}")
        self.assertEqual(set(quick_chips._CHIPS), {"th", "zh", "en", "ja"})

    def test_language_follows_user_message_script(self):
        qr = quick_chips.quick_reply("เครดิตเหลือเท่าไหร่", "zh")  # 泰文消息 → 泰语 chips
        self.assertIn("ดูประวัติ", qr["items"][0]["action"]["label"])
        qr = quick_chips.quick_reply("查一下历史", "th")  # 中文消息 → 中文 chips
        self.assertEqual(qr["items"][0]["action"]["label"], "查看历史")

    def test_no_script_falls_back_to_entry_lang_then_en(self):
        qr = quick_chips.quick_reply("555", "th")  # 纯数字无脚本 → 回落入口 lang
        self.assertIn("ดูประวัติ", qr["items"][0]["action"]["label"])
        qr = quick_chips.quick_reply("ok", "th")  # 拉丁字母 → en(与 loop._reply_lang 同口径)
        self.assertEqual(qr["items"][0]["action"]["label"], "History")
        qr = quick_chips.quick_reply("555", "fr")  # 入口 lang 不认识 → en
        self.assertEqual(qr["items"][0]["action"]["label"], "History")

    def test_item_shape_is_line_message_action(self):
        item = quick_chips.quick_reply("สวัสดี", "th")["items"][0]
        self.assertEqual(item["type"], "action")
        self.assertEqual(item["action"]["type"], "message")

    def test_retry_chip_prepended_with_original_text(self):
        # crash 兜底:首位=「再问一次」重发原话;不传 retry_text 时形状不变。
        qr = quick_chips.quick_reply("这个月花了多少", "zh", retry_text="这个月花了多少")
        first = qr["items"][0]["action"]
        self.assertEqual(first["label"], "再问一次")
        self.assertEqual(first["text"], "这个月花了多少")
        self.assertEqual(len(qr["items"]), 4)
        long = "ก" * 400
        qr = quick_chips.quick_reply(long, "th", retry_text=long)
        self.assertLessEqual(len(qr["items"][0]["action"]["text"]), 300)  # LINE text 上限
        self.assertEqual(len(quick_chips.quick_reply("hi", "en")["items"]), 3)


class TestRouteChips(unittest.TestCase):
    def _call(self, res, *, chips_on):
        said, sent = [], []
        with (
            patch("services.line_binding.line_agent_bridge.try_agent_turn", return_value=res),
            patch("core.feature_flags.agent_quick_chips_enabled_for", return_value=chips_on),
            patch(
                "services.line_binding.line_reply.reply_messages_context",
                lambda rt, msgs, **k: (sent.append(msgs), True)[1],
            ),
        ):
            handled = route.route_gated(
                {"id": "u1"},
                "rt",
                "U1",
                "ดูประวัติ",
                "th",
                "t1",
                1,
                "qt",
                [],
                balance_ok=True,
                say=lambda body: said.append(body),
                charge=lambda: None,
                book=lambda *a, **k: True,
            )
        return handled, said, sent

    def test_reply_carries_quick_reply_when_gate_on(self):
        handled, said, sent = self._call(TurnResult("reply", "นี่ค่ะ"), chips_on=True)
        self.assertEqual(handled, "consumed")
        self.assertEqual(said, [])  # 走 chips 通道,不再纯文本
        msg = sent[0][0]
        self.assertEqual(msg["text"], "นี่ค่ะ")
        self.assertEqual(len(msg["quickReply"]["items"]), 3)

    def test_gate_off_stays_plain_text(self):
        handled, said, sent = self._call(TurnResult("reply", "นี่ค่ะ"), chips_on=False)
        self.assertEqual(handled, "consumed")
        self.assertEqual(said, ["นี่ค่ะ"])
        self.assertEqual(sent, [])

    def test_send_failure_falls_back_to_plain_say(self):
        said = []
        with (
            patch(
                "services.line_binding.line_agent_bridge.try_agent_turn",
                return_value=TurnResult("reply", "x"),
            ),
            patch("core.feature_flags.agent_quick_chips_enabled_for", return_value=True),
            patch(
                "services.line_binding.line_reply.reply_messages_context",
                side_effect=RuntimeError("line down"),
            ),
        ):
            handled = route.route_gated(
                {"id": "u1"},
                "rt",
                "U1",
                "hi",
                "th",
                "t1",
                1,
                "qt",
                [],
                balance_ok=True,
                say=lambda body: said.append(body),
                charge=lambda: None,
                book=lambda *a, **k: True,
            )
        self.assertEqual(handled, "consumed")
        self.assertEqual(said, ["x"])  # chips 失败绝不丢回复

    def test_safe_fallback_carries_chips_when_gate_on(self):
        handled, said, sent = self._call(TurnResult("crash"), chips_on=True)
        self.assertEqual(handled, "consumed")
        self.assertEqual(said, [])
        self.assertEqual(sent[0][0]["text"], route._SAFE_FALLBACK["th"])
        self.assertIn("quickReply", sent[0][0])


if __name__ == "__main__":
    unittest.main()
