# -*- coding: utf-8 -*-
"""LINE 语言中枢:明说切换 / 按消息文本自动跟随 / 回落链(line-language-follow-p0)。"""

import unittest
from unittest import mock

from services.expense import line_lang


class DetectSwitchTests(unittest.TestCase):
    def test_chinese_requests(self):
        for t in ("我要说中文", "你可以说中文吗", "我跟你说中文", "麻烦说中文", "请用中文回复我"):
            self.assertEqual(line_lang.detect_lang_switch(t), "zh", t)

    def test_english_requests(self):
        for t in ("speak english", "please reply in english", "in english please"):
            self.assertEqual(line_lang.detect_lang_switch(t), "en", t)

    def test_thai_requests(self):
        for t in ("พูดไทยหน่อยค่ะ", "ตอบเป็นไทย", "speak thai"):
            self.assertEqual(line_lang.detect_lang_switch(t), "th", t)

    def test_japanese_requests(self):
        for t in ("日本語でお願いします", "speak japanese"):
            self.assertEqual(line_lang.detect_lang_switch(t), "ja", t)

    def test_accounting_not_a_switch(self):
        for t in ("咖啡 65", "ค่ากาแฟ 65", "Makro 500", "190", "ซื้อบะหมี่ผัดกุ้ง 95"):
            self.assertIsNone(line_lang.detect_lang_switch(t), t)

    def test_long_sentence_substring_not_switch(self):
        # 长句里偶含 "in thai" 子串不应被当成换语言指令(长度护栏)。
        self.assertIsNone(
            line_lang.detect_lang_switch("had lunch at an authentic in thai style restaurant today")
        )

    def test_empty(self):
        self.assertIsNone(line_lang.detect_lang_switch(""))
        self.assertIsNone(line_lang.detect_lang_switch("   "))


class SwitchAckTests(unittest.TestCase):
    def test_each_lang_in_its_own_language(self):
        self.assertIn("中文", line_lang.switch_ack("zh"))
        self.assertIn("English", line_lang.switch_ack("en"))
        self.assertIn("ไทย", line_lang.switch_ack("th"))
        self.assertIn("日本語", line_lang.switch_ack("ja"))

    def test_unknown_falls_back_thai(self):
        self.assertEqual(line_lang.switch_ack("xx"), line_lang.switch_ack("th"))


class ResolveReplyLangTests(unittest.TestCase):
    def test_strong_text_signal_follows_message(self):
        # 账号偏好是泰语,但这条打中文 → 回中文(自动跟随,治「中文求说中文却泰语顶回」)。
        self.assertEqual(line_lang.resolve_reply_lang("你是谁", "th", "th"), "zh")
        self.assertEqual(line_lang.resolve_reply_lang("สวัสดี", "zh", "en"), "th")
        self.assertEqual(line_lang.resolve_reply_lang("こんにちは", "th", "en"), "ja")

    def test_weak_or_no_signal_falls_to_preference(self):
        # 纯英文品牌名 / 纯数字 = 弱信号,不自动切 en → 用账号偏好。
        self.assertEqual(line_lang.resolve_reply_lang("Makro 500", "th", "en"), "th")
        self.assertEqual(line_lang.resolve_reply_lang("190", "zh", "en"), "zh")

    def test_fallback_chain_to_ev_then_thai(self):
        self.assertEqual(line_lang.resolve_reply_lang("190", None, "en"), "en")
        self.assertEqual(line_lang.resolve_reply_lang("", None, None), "th")


class CardLangTests(unittest.TestCase):
    """无文本触发的卡片(按钮 postback / 图片结果卡)跟随最近对话语言,不读账号偏好。"""

    @staticmethod
    def _recent(turns):
        return mock.patch("services.line_binding.line_chat_memory.recent", return_value=turns)

    def test_follows_recent_user_message_language(self):
        # 最近对话是泰语 → 卡片泰语(哪怕 ev_lang=中文·本函数刻意不看账号偏好)。
        with self._recent(
            [{"role": "user", "content": "ค่ากาแฟ 50"}, {"role": "bot", "content": "โอเค"}]
        ):
            self.assertEqual(line_lang.card_lang("U1", "t1", "zh"), "th")

    def test_uses_latest_user_turn(self):
        # 取最近一条用户消息:泰→中切换后收到中文卡(显式换语言自然被跟上)。
        with self._recent(
            [{"role": "user", "content": "สวัสดี"}, {"role": "user", "content": "你好"}]
        ):
            self.assertEqual(line_lang.card_lang("U1", "t1", "th"), "zh")

    def test_skips_weak_and_bot_turns(self):
        # 纯数字/机器人消息无强脚本 → 跳过,继续找更早的强信号用户消息。
        with self._recent(
            [
                {"role": "user", "content": "สวัสดีค่ะ"},
                {"role": "bot", "content": "hi"},
                {"role": "user", "content": "500"},
            ]
        ):
            self.assertEqual(line_lang.card_lang("U1", "t1", "en"), "th")

    def test_no_history_falls_to_ev_then_thai(self):
        with self._recent([]):
            self.assertEqual(line_lang.card_lang("U1", "t1", "ja"), "ja")
            self.assertEqual(line_lang.card_lang("U1", "t1", None), "th")

    def test_image_placeholder_turn_is_skipped(self):
        # 发图轮的系统占位("[ส่งรูปใบเสร็จ]"·写死泰文)不是用户的话——中文对话发图后
        # 点按钮,回执曾被它带偏成泰语(真机 2026-07-02)。占位轮必须跳过,继续找真话。
        with self._recent(
            [
                {"role": "user", "content": "帮我推这张"},
                {"role": "user", "content": "[ส่งรูปใบเสร็จ]"},
            ]
        ):
            self.assertEqual(line_lang.card_lang("U1", "t1", "th"), "zh")

    def test_memory_failure_falls_to_ev(self):
        with mock.patch("services.line_binding.line_chat_memory.recent", side_effect=RuntimeError):
            self.assertEqual(line_lang.card_lang("U1", "t1", "th"), "th")


if __name__ == "__main__":
    unittest.main()
