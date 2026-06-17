# -*- coding: utf-8 -*-
"""LINE 数据卡分区构建块(line_card_sections):字段行/税额拆解/明细折叠/卖家行 纯构建。"""

import unittest

from services.line_binding import line_card_sections as s
from services.line_binding.line_card_i18n import chrome

T = chrome("zh")


class FieldRowTests(unittest.TestCase):
    def test_low_confidence_marks_review_and_amber(self):
        row = s.field_row("日期", "2026-06-17", T, low=True, strong=False)
        val = row["contents"][1]
        self.assertIn("(请核对)", val["text"])
        self.assertEqual(val["color"], s.LOW)

    def test_empty_value_shows_na_without_review(self):
        row = s.field_row("日期", "", T, low=True, strong=False)
        self.assertEqual(row["contents"][1]["text"], T["na"])  # 空值不缀「请核对」


class BreakdownTests(unittest.TestCase):
    def test_subtotal_vat_wht_rounding(self):
        rows = s.breakdown_rows({"subtotal": "100", "vat": "7", "wht": "3", "rounding": "0.5"}, T)
        text = rows[0]["text"]
        self.assertIn("税前 ฿100", text)
        self.assertIn("VAT ฿7", text)
        self.assertIn("WHT ฿3", text)
        self.assertIn("舍入 ฿0.5", text)

    def test_zero_wht_and_rounding_dropped(self):
        rows = s.breakdown_rows({"subtotal": "100", "wht": "0", "rounding": "0.00"}, T)
        self.assertNotIn("WHT", rows[0]["text"])
        self.assertNotIn("舍入", rows[0]["text"])

    def test_all_empty_no_row(self):
        self.assertEqual(s.breakdown_rows({}, T), [])


class ItemsSectionTests(unittest.TestCase):
    def test_cap_and_overflow(self):
        items = [{"name": f"i{n}", "amount": "1"} for n in range(8)]
        rows = s.items_section(items, T, cap=5)
        flat = str(rows)
        self.assertIn("i4", flat)
        self.assertNotIn("i5", flat)
        self.assertIn("还有 3 行", flat)

    def test_within_cap_no_overflow(self):
        rows = s.items_section([{"name": "a", "amount": "1"}], T, cap=5)
        self.assertNotIn("还有", str(rows))

    def test_free_item_no_empty_text_node(self):
        # 免费/无价品项(amount 空)不渲染价格文本节点:LINE Flex text 必须非空,空串会让整卡被拒(400)。
        rows = s.items_section(
            [{"name": "Coffee", "amount": "60"}, {"name": "Free toy (แถมฟรี)", "amount": ""}], T
        )

        def has_empty_text(node):
            if isinstance(node, dict):
                if node.get("type") == "text" and node.get("text", "") == "":
                    return True
                return any(has_empty_text(v) for v in node.values())
            if isinstance(node, list):
                return any(has_empty_text(x) for x in node)
            return False

        self.assertFalse(has_empty_text(rows), "免费品项不应产生空 text 节点")
        self.assertIn("Free toy", str(rows))  # 免费品项名仍显示


class SellerRowsTests(unittest.TestCase):
    def test_only_present_fields(self):
        rows = s.seller_rows({"seller_tax": "0105551234567"}, T)
        self.assertEqual(len(rows), 1)
        self.assertEqual(s.seller_rows({}, T), [])


if __name__ == "__main__":
    unittest.main()
