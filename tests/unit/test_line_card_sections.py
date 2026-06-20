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
    """Phase B 诚实状态:posted(绿)中性提示不出「请核对前」;needs-review(琥珀)列待办清单。"""

    T = T

    def _text(self, out):
        return out[0]["contents"][0]["text"] if out else ""

    def test_missing_taxid_only_when_expected(self):
        self.assertTrue(s.missing_taxid({"vat": "34.27", "seller_tax": ""}))  # 有 VAT 无税号
        self.assertTrue(s.missing_taxid({"document_type": "tax_invoice", "seller_tax": ""}))
        self.assertFalse(s.missing_taxid({"vat": "", "seller_tax": ""}))  # 普通小票 → 不提示
        self.assertFalse(s.missing_taxid({"vat": "34", "seller_tax": "0107561000013"}))  # 有税号

    def test_plain_receipt_no_notice(self):
        self.assertEqual(s.notices({"vat": "", "seller_tax": ""}, False, self.T), [])

    def test_review_lists_concrete_todos(self):
        # 需确认态:列出具体待办(金额/税号/明细/品名)·条目来自 field_quality 信号。
        fields = {"vat": "34", "seller_tax": "", "amount_unreliable": True, "items_unread": True}
        out = s.notices(fields, True, self.T, posted=False)
        self.assertEqual(len(out), 1)
        txt = self._text(out)
        self.assertIn(self.T["review_todo_head"].format(n=4), txt)  # 需确认 4 件事
        for k in ("todo_amount", "todo_tax", "todo_items", "todo_name"):
            self.assertIn(self.T[k], txt)
        self.assertIn("①", txt)  # 编号清单

    def test_review_todos_from_field_quality(self):
        todos = s.review_todos({"seller_unclear": True, "dirty_fields": ["date"]}, False, self.T)
        self.assertEqual(todos, [self.T["todo_seller"], self.T["todo_date"]])

    def test_posted_neutral_note_no_review_wording(self):
        # 已入账绿卡有小瑕疵 → 仅中性提示,绝不含「请核对前 / ก่อนบันทึก」。
        out = s.notices({"items_unread": True}, False, self.T, posted=True)
        self.assertEqual(self._text(out), self.T["posted_note_neutral"])
        self.assertNotIn("ก่อนบันทึก", self._text(out))
        self.assertNotIn("请核对", self._text(out))

    def test_posted_clean_no_note_when_no_issue(self):
        self.assertEqual(s.notices({"vat": "", "seller_tax": ""}, False, self.T, posted=True), [])


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

    def test_section_posted_uses_neutral_hint(self):
        # 已入账绿卡:名称不清用【中性】文案(不说「请核对前再保存」)。
        rows = s.items_section([{"name": "????", "amount": "30.00"}], T, posted=True)
        self.assertEqual(rows[-1]["text"], T["items_name_unclear_neutral"])
        self.assertNotEqual(rows[-1]["text"], T["items_name_unclear"])


if __name__ == "__main__":
    unittest.main()
