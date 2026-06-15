# -*- coding: utf-8 -*-
"""LINE 阶段三纯模块:取链接命令 / glue(取链接回复 + Rich Menu)。

锁:命令多写法归一 · 取链接回复带 URL · Rich Menu 6 格 + uri 填充。统一智能通道下图/文均
直落采购,不再有 Flex 确认卡 / postback。真 push / webhook 分流 / LIFF 鉴权 = 用户验收。
"""

import unittest

from services.line_binding import line_commands as lc


class CommandTests(unittest.TestCase):
    def test_drive_command_variants(self):
        self.assertEqual(lc.parse_link_command("ขอ link drive"), lc.LINK_DRIVE)
        self.assertEqual(lc.parse_link_command("给我 网盘 链接"), lc.LINK_DRIVE)

    def test_sheet_command_variants(self):
        self.assertEqual(lc.parse_link_command("ขอ google sheet"), lc.LINK_SHEET)
        self.assertEqual(lc.parse_link_command("要 报表"), lc.LINK_SHEET)

    def test_sheet_wins_when_both(self):
        self.assertEqual(lc.parse_link_command("ขอ link drive sheet"), lc.LINK_SHEET)

    def test_non_command_returns_none(self):
        self.assertIsNone(lc.parse_link_command("สวัสดี"))
        self.assertIsNone(lc.parse_link_command("drive"))  # 无取链接意图词
        self.assertIsNone(lc.parse_link_command(""))


class LineIntakeGlueTests(unittest.TestCase):
    def test_link_reply_contains_url(self):
        from services.line_binding import line_intake as li

        msg = li.link_reply(li.line_commands.LINK_DRIVE, "en", web_url="https://x/y")
        self.assertIn("https://x/y", msg)

    def test_rich_menu_payload_six_areas(self):
        from services.line_binding import line_intake as li

        rm = li.rich_menu_payload(web_url="https://x")
        self.assertEqual(rm["size"], {"width": 2500, "height": 843})
        self.assertEqual(len(rm["areas"]), 6)
        # uri 格被填上 web_url
        uri_areas = [a for a in rm["areas"] if a["action"].get("type") == "uri"]
        self.assertEqual(uri_areas[0]["action"]["uri"], "https://x")


if __name__ == "__main__":
    unittest.main()
