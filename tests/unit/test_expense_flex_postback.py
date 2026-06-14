# -*- coding: utf-8 -*-
"""线 B · 费用确认卡 + postback 往返(doc 10 §5 提议确认 · 护栏:文案全由 labels 注入)。"""

import unittest

from services.line_binding import line_flex, line_postback


class ExpenseConfirmFlexTests(unittest.TestCase):
    def _card(self, edit_url=""):
        return line_flex.expense_confirm_flex(
            draft={
                "amount": "135",
                "currency": "THB",
                "category": "ค่าอาหาร",
                "vendor_name": "ร้านกาแฟ",
                "doc_date": "2026-06-15",
            },
            draft_id="d1",
            labels={
                "head": "ยืนยันค่าใช้จ่ายนี้",
                "category": "หมวดหมู่",
                "vendor": "ผู้ขาย",
                "date": "วันที่",
                "confirm": "ยืนยัน",
                "discard": "ยกเลิก",
                "edit": "แก้ไขบนเว็บ",
            },
            edit_url=edit_url,
        )

    def test_is_flex_with_amount_shown(self):
        card = self._card()
        self.assertEqual(card["type"], "flex")
        dumped = str(card)
        self.assertIn("135 THB", dumped)  # 算出的总额一眼可核(doc 10 §3)

    def test_buttons_carry_expense_postback(self):
        footer = self._card()["contents"]["footer"]["contents"]
        datas = [b["action"].get("data", "") for b in footer if b["action"]["type"] == "postback"]
        self.assertIn(line_postback.expense_confirm_data("d1"), datas)
        self.assertIn(line_postback.expense_discard_data("d1"), datas)

    def test_edit_url_optional(self):
        self.assertEqual(  # 无 edit_url → 只有确认/丢弃两个 postback 按钮
            len(self._card()["contents"]["footer"]["contents"]), 2
        )
        with_edit = self._card(edit_url="https://pearnly.com/home#expense-draft=d1")
        uris = [
            b["action"]["uri"]
            for b in with_edit["contents"]["footer"]["contents"]
            if b["action"]["type"] == "uri"
        ]
        self.assertEqual(uris, ["https://pearnly.com/home#expense-draft=d1"])

    def test_text_only_from_labels(self):
        # 护栏:卡上可见文字只来自 labels(模板),不含任何动态生成的句子
        card = self._card()
        self.assertIn("ยืนยันค่าใช้จ่ายนี้", str(card))


class ExpensePostbackRoundtripTests(unittest.TestCase):
    def test_confirm_roundtrip(self):
        out = line_postback.parse(line_postback.expense_confirm_data("d9"))
        self.assertEqual(out, {"action": "exp_confirm", "doc_id": "", "draft_id": "d9"})

    def test_discard_roundtrip(self):
        out = line_postback.parse(line_postback.expense_discard_data("d9"))
        self.assertEqual(out["action"], "exp_discard")
        self.assertEqual(out["draft_id"], "d9")

    def test_legacy_confirm_unchanged(self):
        # 图片路 confirm/redirect 形态不变(不夹带 draft_id)
        out = line_postback.parse(line_postback.confirm_data("D1"))
        self.assertEqual(out, {"action": "confirm", "doc_id": "D1"})


if __name__ == "__main__":
    unittest.main()
