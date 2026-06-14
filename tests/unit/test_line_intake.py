# -*- coding: utf-8 -*-
"""LINE 阶段三纯模块:postback 编解码 / 取链接命令 / OCR Flex 卡(阶段三)。

锁:postback 往返 + 非法拒 · 命令多写法归一 · Flex 结构 + 低置信着标 + 按钮带 postback/uri。
真 push / webhook 分流 / Rich Menu / LIFF 真鉴权 = 用户验收(需真 channel)。
"""

import unittest

from services.line_binding import line_commands as lc
from services.line_binding import line_flex as lf
from services.line_binding import line_postback as lp


class PostbackTests(unittest.TestCase):
    def test_confirm_roundtrip(self):
        out = lp.parse(lp.confirm_data("D1"))
        self.assertEqual(out, {"action": "confirm", "doc_id": "D1"})

    def test_redirect_roundtrip(self):
        out = lp.parse(lp.redirect_data("D1", "expense"))
        self.assertEqual(out, {"action": "redirect", "doc_id": "D1", "direction": "expense"})

    def test_redirect_invalid_direction_blanked(self):
        out = lp.parse(lp.redirect_data("D1", "bogus"))
        self.assertEqual(out["direction"], "")

    def test_bad_data_rejected(self):
        self.assertEqual(lp.parse("garbage")["action"], "")
        self.assertEqual(lp.parse("")["action"], "")


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


_LABELS = {
    "head": "识别完成",
    "vendor": "卖家",
    "no": "票号",
    "date": "日期",
    "amount": "金额",
    "confirm": "确认入采购",
    "expense": "记为费用",
    "edit": "修改",
    "review_mark": "(请核对)",
}


class FlexTests(unittest.TestCase):
    def _card(self, fc=None, liff=""):
        return lf.ocr_result_flex(
            fields={
                "seller_name": "Cafe",
                "invoice_number": "NZ01",
                "date": "2026-06-01",
                "total_amount": "110.00",
            },
            field_confidence=fc or {},
            doc_id="D1",
            labels=_LABELS,
            liff_url=liff,
        )

    def test_flex_structure(self):
        card = self._card()
        self.assertEqual(card["type"], "flex")
        self.assertEqual(card["contents"]["type"], "bubble")
        # 两个 postback 按钮(确认/记费用),无 LIFF 时无第三个
        footer = card["contents"]["footer"]["contents"]
        self.assertEqual(len(footer), 2)
        self.assertEqual(footer[0]["action"]["type"], "postback")

    def test_low_confidence_field_marked_and_ambered(self):
        card = self._card(fc={"invoice_number": 0.55})
        body = card["contents"]["body"]["contents"]
        no_row = body[3]  # head, separator, vendor, no
        val_cell = no_row["contents"][1]
        self.assertIn("(请核对)", val_cell["text"])
        self.assertEqual(val_cell["color"], "#D97706")

    def test_high_confidence_not_marked(self):
        card = self._card(fc={"invoice_number": 0.97})
        no_row = card["contents"]["body"]["contents"][3]
        self.assertNotIn("(请核对)", no_row["contents"][1]["text"])

    def test_liff_button_added_when_url(self):
        card = self._card(liff="https://liff/x")
        footer = card["contents"]["footer"]["contents"]
        self.assertEqual(len(footer), 3)
        self.assertEqual(footer[2]["action"]["type"], "uri")
        self.assertEqual(footer[2]["action"]["uri"], "https://liff/x")

    def test_confirm_button_carries_doc_postback(self):
        card = self._card()
        data = card["contents"]["footer"]["contents"][0]["action"]["data"]
        self.assertEqual(lp.parse(data), {"action": "confirm", "doc_id": "D1"})


class LineIntakeGlueTests(unittest.TestCase):
    def test_ocr_labels_four_langs(self):
        from services.line_binding import line_intake as li

        for lang in ("zh", "th", "en", "ja"):
            labels = li.ocr_labels(lang)
            self.assertIn("confirm", labels)
            self.assertIn("review_mark", labels)

    def test_flex_disabled_by_default(self):
        import os

        from services.line_binding import line_intake as li

        saved = os.environ.pop("LINE_FLEX_INTAKE", None)
        try:
            self.assertFalse(li.is_flex_enabled())
            os.environ["LINE_FLEX_INTAKE"] = "1"
            self.assertTrue(li.is_flex_enabled())
        finally:
            os.environ.pop("LINE_FLEX_INTAKE", None)
            if saved is not None:
                os.environ["LINE_FLEX_INTAKE"] = saved

    def test_link_reply_contains_url(self):
        from services.line_binding import line_intake as li

        msg = li.link_reply(li.line_commands.LINK_DRIVE, "en", web_url="https://x/y")
        self.assertIn("https://x/y", msg)

    def test_ack_reply_langs(self):
        from services.line_binding import line_intake as li

        self.assertTrue(li.ack_reply("purchase", "th"))
        self.assertTrue(li.ack_reply("expense", "ja"))

    def test_build_ocr_flex_wraps_labels(self):
        from services.line_binding import line_intake as li

        card = li.build_ocr_flex(
            lang="th", fields={"invoice_number": "X"}, field_confidence={}, doc_id="D1"
        )
        self.assertEqual(card["type"], "flex")

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
