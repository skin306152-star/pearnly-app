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


class PruneEmptyTextTests(unittest.TestCase):
    """空 text 节点剔除:防 LINE 400 must be non-empty text(整类防护)。"""

    def test_drops_empty_text_and_emptied_box(self):
        card = {
            "type": "flex",
            "altText": "a",
            "contents": {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "contents": [
                        {"type": "text", "text": "ok"},
                        {"type": "text", "text": ""},
                        {"type": "box", "contents": [{"type": "text", "text": "   "}]},
                    ],
                },
            },
        }
        out = s.prune_empty_text(card)
        body = out["contents"]["body"]["contents"]
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["text"], "ok")

    def test_keeps_non_empty(self):
        node = {"type": "box", "contents": [{"type": "text", "text": "x"}]}
        self.assertEqual(s.prune_empty_text(node), node)


class NoticesTests(unittest.TestCase):
    """P1F-2 卡顶异常提示:缺税号/总额不符/明细不全·按重要性 ≤2 条·普通小票不堆警告。"""

    T = {
        "warn_total": "总额不符",
        "no_taxid": "ไม่พบเลขภาษี",
        "items_partial": "รายการอาจไม่ครบ",
    }

    def test_missing_taxid_only_when_expected(self):
        self.assertTrue(s.missing_taxid({"vat": "34.27", "seller_tax": ""}))  # 有 VAT 无税号
        self.assertTrue(s.missing_taxid({"document_type": "tax_invoice", "seller_tax": ""}))
        self.assertFalse(s.missing_taxid({"vat": "", "seller_tax": ""}))  # 普通小票 → 不提示
        self.assertFalse(s.missing_taxid({"vat": "34", "seller_tax": "0107561000013"}))  # 有税号

    def test_notice_for_vat_receipt_without_tax(self):
        out = s.notices({"vat": "34.27", "seller_tax": ""}, False, self.T)
        self.assertEqual(len(out), 1)
        self.assertIn("ไม่พบเลขภาษี", out[0]["contents"][0]["text"])

    def test_plain_receipt_no_notice(self):
        self.assertEqual(s.notices({"vat": "", "seller_tax": ""}, False, self.T), [])

    def test_caps_at_two(self):
        out = s.notices({"vat": "34", "seller_tax": "", "items_unread": True}, True, self.T)
        self.assertEqual(len(out), 2)  # 三个信号都在 → 只显最重要 2 条


class GarbledItemNameTests(unittest.TestCase):
    """OCR 读不出的泰文细品名(?????)/POS 噪声 → 编号占位或清洗名,不露乱码(P2C)。"""

    def test_pure_question_marks_fall_back_to_numbered(self):
        self.assertEqual(s._display_item_name("????", 1, T), "项目 1")
        self.assertEqual(s._display_item_name("?? ??", 3, T), "项目 3")
        self.assertEqual(s._display_item_name("��", 2, T), "项目 2")

    def test_pos_prefix_only_falls_back(self):
        # 「TW ?????」剥乱码+POS 前缀后仅剩前缀 → 编号占位,不再裸露「TW」(P2C 验收①)
        self.assertEqual(s._display_item_name("TW ?????", 1, T), "项目 1")

    def test_readable_kept(self):
        self.assertEqual(s._display_item_name("TW Latte", 1, T), "Latte")
        self.assertEqual(s._display_item_name("Cake slice", 2, T), "Cake slice")

    def test_section_renders_numbered_placeholder(self):
        rows = s.items_section([{"name": "????", "amount": "30.00"}], T)
        # rows[0]=小标题,rows[1]=第一行 box → 名称节点 text 含「项目 1」不含「?」
        name_text = rows[1]["contents"][0]["text"]
        self.assertIn("项目 1", name_text)
        self.assertNotIn("?", name_text)

    def test_section_appends_unclear_hint(self):
        rows = s.items_section([{"name": "????", "amount": "30.00"}], T)
        self.assertEqual(rows[-1]["text"], T["items_name_unclear"])

    def test_section_no_hint_when_all_clear(self):
        rows = s.items_section([{"name": "Latte", "amount": "30.00"}], T)
        self.assertTrue(all(r.get("text") != T["items_name_unclear"] for r in rows if "text" in r))


if __name__ == "__main__":
    unittest.main()
