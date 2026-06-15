# -*- coding: utf-8 -*-
"""线 B · 一句话记账 L1 确定性解析(doc 10 §3)+ ExpenseDraft 模型。

锁:金额/数量/单价/税号/发票号/日期/分类 的确定性映射(泰语优先);裸数字=总额;
@/单价 算总额;无金额→不当记账。统一智能通道下解析结果直接落采购草稿单(无独立草稿表)。
"""

import unittest
from datetime import date
from decimal import Decimal

from services.expense import line_quick_entry as lqe
from services.expense.expense_draft import ExpenseDraft


class ParseExpenseTests(unittest.TestCase):
    def test_thai_water_bill(self):
        d = lqe.parse_expense("ค่าน้ำ 50")
        self.assertEqual(d.amount, Decimal("50"))

    def test_amount_with_currency_word(self):
        d = lqe.parse_expense("โค้ก 30 บาท")
        self.assertEqual(d.amount, Decimal("30"))

    def test_expense_type_service_vs_goods(self):
        self.assertEqual(lqe.parse_expense("ค่าซ่อมรถ 500").expense_type, "service")
        self.assertEqual(lqe.parse_expense("ค่าเช่า 8000").expense_type, "service")
        self.assertEqual(lqe.parse_expense("โค้ก 30").expense_type, "goods")

    def test_utilities_are_service_not_goods(self):
        # 修「水费=商品」误判:公用事业(水/电/网/话费)= 服务。
        for t in ("水费 50", "电费 200", "ค่าน้ำ 50", "ค่าไฟ 300", "网费 600", "话费 100"):
            self.assertEqual(lqe.parse_expense(t).expense_type, "service", t)

    def test_baht_symbol(self):
        self.assertEqual(lqe.parse_expense("฿1,250.50").amount, Decimal("1250.50"))

    def test_qty_times_unit_price(self):
        d = lqe.parse_expense("กาแฟ x3 @45")
        self.assertEqual(d.qty, Decimal("3"))
        self.assertEqual(d.unit_price, Decimal("45"))
        self.assertEqual(d.amount, Decimal("135"))

    def test_chinese_taxi(self):
        d = lqe.parse_expense("打车 120")
        self.assertEqual(d.amount, Decimal("120"))

    def test_tax_id_and_invoice_number(self):
        d = lqe.parse_expense("0105546015062 IV69/00179 500 บาท")
        self.assertEqual(d.vendor_tax_id, "0105546015062")
        self.assertEqual(d.invoice_number, "IV69/00179")
        self.assertEqual(d.amount, Decimal("500"))

    def test_no_amount_not_expense(self):
        d = lqe.parse_expense("สวัสดีครับ")
        self.assertIsNone(d.amount)
        self.assertFalse(d.has_amount())
        self.assertFalse(lqe.looks_like_expense("สวัสดีครับ"))

    def test_looks_like_expense_true(self):
        self.assertTrue(lqe.looks_like_expense("ค่าน้ำ 50"))

    def test_date_today_word(self):
        d = lqe.parse_expense("ค่าน้ำ 50 วันนี้")
        self.assertEqual(d.doc_date, date.today().isoformat())

    def test_date_buddhist_two_digit(self):
        # 13/06/69 → 佛历 2569-543 = 2026
        d = lqe.parse_expense("ค่าน้ำ 50 13/06/69")
        self.assertEqual(d.doc_date, "2026-06-13")

    def test_date_digits_dont_pollute_amount(self):
        # 日期里的 13/06/69 不能被当成金额(回归:prod E2E 抓到 amount 取成 69)
        d = lqe.parse_expense("ค่าน้ำ 50 13/06/69")
        self.assertEqual(d.amount, Decimal("50"))

    def test_tax_id_digits_dont_pollute_amount(self):
        d = lqe.parse_expense("0105546015062 ค่าน้ำ 50")
        self.assertEqual(d.amount, Decimal("50"))

    def test_default_date_today(self):
        self.assertEqual(lqe.parse_expense("ค่าน้ำ 50").doc_date, date.today().isoformat())


class IntentGuardTests(unittest.TestCase):
    """L1 意图 + 问句护栏:别把问题/查账/求助当记账(治「我刚不是花了50吗」被误记)。"""

    def test_question_with_number_not_expense(self):
        # 关键回归:含数字的问句不能当记账。
        self.assertTrue(lqe.is_question("我刚刚不是花了50吗"))
        self.assertTrue(lqe.is_question("这个对吗?"))

    def test_plain_expense_not_question(self):
        self.assertFalse(lqe.is_question("ค่าน้ำ 50"))
        self.assertFalse(lqe.is_question("打车 120"))

    def test_l1_intent_support(self):
        self.assertEqual(lqe.l1_intent("人工客服"), "support")
        self.assertEqual(lqe.l1_intent("转人工"), "support")

    def test_l1_intent_query(self):
        self.assertEqual(lqe.l1_intent("本月花了多少"), "query")
        self.assertEqual(lqe.l1_intent("这个月花多少"), "query")

    def test_l1_intent_none_for_expense(self):
        self.assertIsNone(lqe.l1_intent("ค่าน้ำ 50"))
        self.assertIsNone(lqe.l1_intent("打车 120"))


class CategoryTreeMatchTests(unittest.TestCase):
    """LINE 归类走本套账真实科目树(intake._match_category + 共享关键词)· 不分叉。"""

    TREE = [
        {
            "id": "p1",
            "name": "ค่าสาธารณูปโภค",
            "children": [{"id": "c1", "name": "ค่าน้ำประปา"}, {"id": "c2", "name": "ค่าไฟฟ้า"}],
        },
        {
            "id": "p2",
            "name": "ค่าเดินทางและขนส่ง",
            "children": [{"id": "c3", "name": "ค่าแท็กซี่/แกร็บ"}],
        },
    ]

    def test_thai_water_maps_to_subcategory(self):
        from services.purchase import intake

        self.assertEqual(intake._match_category("ค่าน้ำ 50", self.TREE), ("p1", "c1"))

    def test_chinese_taxi_maps_to_subcategory(self):
        from services.purchase import intake

        self.assertEqual(intake._match_category("打车 120", self.TREE), ("p2", "c3"))

    def test_unknown_leaves_empty(self):
        from services.purchase import intake

        self.assertEqual(intake._match_category("อะไรไม่รู้ 30", self.TREE), (None, None))


class ModelTests(unittest.TestCase):
    def test_defaults(self):
        d = ExpenseDraft()
        self.assertEqual(d.currency, "THB")
        self.assertEqual(d.vat_mode, "included")
        self.assertFalse(d.has_amount())

    def test_has_amount(self):
        self.assertTrue(ExpenseDraft(amount=Decimal("1")).has_amount())
        self.assertFalse(ExpenseDraft(amount=Decimal("0")).has_amount())


if __name__ == "__main__":
    unittest.main()
