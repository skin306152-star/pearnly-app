# -*- coding: utf-8 -*-
"""line_bind_i18n 文案/消息构建器单测:四语齐全、按钮 ≤20、URI 指向官网、结构正确。"""

import unittest

from services.line_binding import line_bind_i18n as b

LANGS = ("th", "en", "zh", "ja")


class CopyParityTests(unittest.TestCase):
    def test_all_copy_keys_have_four_langs(self):
        for key, table in b._COPY.items():
            self.assertEqual(set(table), set(LANGS), f"{key} 缺语言")
            for lang in LANGS:
                self.assertTrue(table[lang].strip(), f"{key}/{lang} 空")

    def test_all_button_keys_have_four_langs(self):
        for key, table in b._BTN.items():
            self.assertEqual(set(table), set(LANGS), f"按钮 {key} 缺语言")

    def test_button_labels_within_line_limit(self):
        for key, table in b._BTN.items():
            for lang in LANGS:
                self.assertLessEqual(len(table[lang]), 20, f"按钮 {key}/{lang} 超 20 字符")

    def test_t_bind_fallback_to_th(self):
        self.assertEqual(b.t_bind("xx", "need_bind"), b.t_bind("th", "need_bind"))
        self.assertEqual(b.t_bind(None, "need_bind"), b.t_bind("th", "need_bind"))


class MessageBuilderTests(unittest.TestCase):
    def _assert_text(self, msg):
        self.assertEqual(msg["type"], "text")
        self.assertTrue(msg["text"].strip())

    def _connect_button(self, msg):
        items = msg["quickReply"]["items"]
        self.assertTrue(items)
        action = items[0]["action"]
        self.assertEqual(action["type"], "uri")
        self.assertEqual(action["uri"], b.CONNECT_URL)
        return items

    def test_need_bind_msg_has_connect_uri(self):
        for lang in LANGS:
            msg = b.need_bind_msg(lang)
            self._assert_text(msg)
            self._connect_button(msg)

    def test_image_not_bound_msg_has_connect_uri(self):
        msg = b.image_not_bound_msg("th")
        self._assert_text(msg)
        self._connect_button(msg)

    def test_bind_invalid_msg_has_retry_button(self):
        msg = b.bind_invalid_msg("en")
        self._assert_text(msg)
        self.assertEqual(msg["quickReply"]["items"][0]["action"]["label"], "Get a new link")

    def test_bind_conflict_msg_has_two_buttons(self):
        msg = b.bind_conflict_msg("zh")
        items = msg["quickReply"]["items"]
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["action"]["label"], "查看绑定状态")
        self.assertEqual(items[1]["action"]["label"], "联系客服")

    def test_bind_success_msg_plain_text_no_buttons(self):
        msg = b.bind_success_msg("ja")
        self._assert_text(msg)
        self.assertNotIn("quickReply", msg)

    def test_connect_url_breaks_out_of_line_webview(self):
        self.assertIn("openExternalBrowser=1", b.CONNECT_URL)


if __name__ == "__main__":
    unittest.main()
