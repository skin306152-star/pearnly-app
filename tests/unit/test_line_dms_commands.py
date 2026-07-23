# -*- coding: utf-8 -*-
"""DMS LINE 全局命令词形判定(commands.classify)· 纯函数,无会话无 IO。

菜单词曾在 flow 与 menu_flow 各写一份判据,分发顺序又让 editing 态先吃文本(P1-10)。
这里锁词形边界;分发顺序的回归断言在 test_line_dms_flow(e7/e8/e9)。
"""

import unittest

from services.line_dms import commands


class ClassifyTests(unittest.TestCase):
    def test_reset_word(self):
        self.assertEqual(commands.classify("เริ่มใหม่"), commands.CMD_RESET)
        self.assertEqual(commands.classify("  เริ่มใหม่  "), commands.CMD_RESET)

    def test_menu_word_and_typos(self):
        for text in ("เมนู", "เมน", "เมนB", " เมนู "):
            self.assertEqual(commands.classify(text), commands.CMD_MENU, text)

    def test_long_word_starting_with_menu_prefix_is_not_menu(self):
        # 以 เมน 起头的长句是闲聊,不是召唤菜单
        self.assertIsNone(commands.classify("เมนูอาหารกลางวันวันนี้"))

    def test_greeting_prefix(self):
        self.assertEqual(commands.classify("สวัสดีครับ"), commands.CMD_GREETING)

    def test_plain_text_and_phone_are_not_commands(self):
        for text in ("0812345678", "1", "ราคาเท่าไร", "", "   "):
            self.assertIsNone(commands.classify(text), text)

    def test_edit_cancel_is_not_global(self):
        """ยกเลิก 是 editing 态的取消,不许升格成全局命令。"""
        from services.line_dms import cards

        self.assertIsNone(commands.classify(cards.BTN_EDIT_CANCEL))


if __name__ == "__main__":
    unittest.main()
