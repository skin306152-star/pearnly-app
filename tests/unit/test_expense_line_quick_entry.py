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


class EditGuardTests(unittest.TestCase):
    """改错分流守卫(P2):「改成X/第N笔」是改错,不能被 L1 当新记一笔。"""

    def test_edit_phrases_detected(self):
        for t in (
            "上一笔改成550",
            "卖家改成7-11",
            "日期改成昨天",
            "第1张改成100",
            "แก้ยอดเป็น 200",
        ):
            self.assertTrue(lqe.is_edit_request(t), t)

    def test_normal_record_not_edit(self):
        for t in ("ค่าน้ำ 50", "打车 120", "咖啡 60", "买菜 40"):
            self.assertFalse(lqe.is_edit_request(t), t)

    def test_edit_amount_still_parses_amount(self):
        # 守卫只负责分流;parse_expense 仍会抽出 550(由 handle 流程用 is_edit 跳过记账)。
        self.assertEqual(lqe.parse_expense("上一笔改成550").amount, Decimal("550"))

    def test_ordinal_digits(self):
        self.assertEqual(lqe.parse_ordinal("第1张改成100"), 1)
        self.assertEqual(lqe.parse_ordinal("รายการที่ 3 แก้เป็น 50"), 3)
        self.assertEqual(lqe.parse_ordinal("item 2 change to 9"), 2)

    def test_ordinal_chinese_numeral(self):
        self.assertEqual(lqe.parse_ordinal("第一张改成100"), 1)
        self.assertEqual(lqe.parse_ordinal("第三笔改成50"), 3)

    def test_ordinal_absent(self):
        self.assertIsNone(lqe.parse_ordinal("上一笔改成100"))
        self.assertIsNone(lqe.parse_ordinal("改成100"))


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


class ParseMultiTests(unittest.TestCase):
    def test_splits_multiple(self):
        r = lqe.parse_multi("电费50 买菜40 电费10 吃饭50")
        self.assertEqual(
            [(i["name"], str(i["amount"])) for i in r],
            [("电费", "50"), ("买菜", "40"), ("电费", "10"), ("吃饭", "50")],
        )

    def test_strips_currency_unit(self):
        r = lqe.parse_multi("ค่าน้ำ50บาท ค่าไฟ100บาท")
        self.assertEqual([i["name"] for i in r], ["ค่าน้ำ", "ค่าไฟ"])

    def test_single_returns_none(self):
        self.assertIsNone(lqe.parse_multi("吃饭150"))
        self.assertIsNone(lqe.parse_multi("咖啡60"))

    def test_inline_seller_not_counted_as_item(self):
        # P1E-3:句中「ผู้ขาย 711」是卖家声明,不计入金额 → 3 项合计 150(非 4 项 861)。
        r = lqe.parse_multi("วันนี้ใช้จ่าย: กาแฟ 30 ทุเรียน 100 ปากกา 20 ผู้ขาย 711")
        self.assertEqual(len(r), 3)
        self.assertEqual(sum(i["amount"] for i in r), Decimal("150"))

    def test_hyphen_store_name_not_counted(self):
        # P1E-3:店名「ที่ 7-11」的 7/11 是编号不是金额 → 合计 550(非 557)。
        r = lqe.parse_multi("กาแฟ 300 ขนม 250 ที่ 7-11")
        self.assertEqual(sum(i["amount"] for i in r), Decimal("550"))
        self.assertNotIn(Decimal("7"), [i["amount"] for i in r])

    def test_hyphen_code_both_sides_excluded(self):
        # 连字号数字串两端都不计:「02-99」→ 02、99 均非金额,真金额 500 不受影响。
        r = lqe.parse_multi("ค่าโทร 500 เบอร์ 02-99 ค่าน้ำ 80")
        self.assertEqual(sum(i["amount"] for i in r), Decimal("580"))

    def test_extract_inline_vendor(self):
        self.assertEqual(lqe.extract_inline_vendor("... ปากกา 20 ผู้ขาย 711"), "711")
        self.assertEqual(lqe.extract_inline_vendor("ร้านค้า 7-11 กาแฟ 30"), "7-11")  # 长词先匹配
        self.assertEqual(lqe.extract_inline_vendor("กาแฟ 30 ข้าว 60"), "")  # 无声明 → 空


class VendorDigitNotAmountTests(unittest.TestCase):
    """店名是数字(711/7-11)不当总额:剔除卖家品牌里的数字后再取金额。"""

    def test_store_number_not_amount(self):
        # 「昨天在 711 买榴莲」(没说价)→ 金额 None → 走「多少钱?」追问,不记 711 THB。
        t = "เมื่อวานซื้อทุเรียนที่ร้าน 711"
        self.assertIsNone(lqe._extract_amount(t, None, None))
        self.assertFalse(lqe.parse_expense(t).has_amount())

    def test_real_amount_kept_with_digit_vendor(self):
        # 「7-11 买咖啡 65」→ 65 是真金额,不被误删;卖家仍识别 7-Eleven。
        self.assertEqual(lqe._extract_amount("7-11 ซื้อกาแฟ 65", None, None), Decimal("65"))
        self.assertEqual(lqe.parse_expense("7-11 ซื้อกาแฟ 65").amount, Decimal("65"))

    def test_non_digit_vendor_unaffected(self):
        self.assertEqual(lqe._extract_amount("บางจาก 500", None, None), Decimal("500"))


class FourDigitAmountTests(unittest.TestCase):
    """裸 4+ 位金额不被 _NUM 逗号分支切碎(空调 1500→150 的真因·*→+ 修)。"""

    def test_four_digit_bare(self):
        for t, amt in (
            ("空调 1500", "1500"),
            ("เครื่องปรับอากาศ 9000", "9000"),
            ("ค่าเช่า 8000", "8000"),
        ):
            self.assertEqual(lqe.parse_expense(t).amount, Decimal(amt), t)

    def test_comma_grouped_still_parses(self):
        self.assertEqual(lqe.parse_expense("฿1,250.50").amount, Decimal("1250.50"))
        self.assertEqual(lqe.parse_expense("ค่าเช่า 12,000").amount, Decimal("12000"))


class AdjustAmountEditTests(unittest.TestCase):
    """调整金额(关键词 + 结构识别)算改错;绝不误伤罚款/空调/调味料/普通记账。"""

    def test_adjust_is_edit(self):
        for t in (
            "ปรับยอดเป็น 150",
            "ปรับจำนวนรวมเป็น 160",
            "จำนวนรวมเปลี่ยนเป็น 200",
            "金额改成150",
            "总额调成200",
            "调整金额150",
            "ลดยอด 100",
            "调到80",
        ):
            self.assertTrue(lqe.is_edit_request(t), t)

    def test_product_names_not_edit(self):
        # 罚款/空调/调味料/交通罚款/普通记账 无「金额名词+改成数字」结构 → 仍当支出。
        for t in (
            "ค่าปรับ 150",
            "ปรับอากาศ 1500",
            "เครื่องปรับอากาศ 9000",
            "空调 1500",
            "调味料 50",
            "ค่าปรับจราจร 500",
            "เนื้อหมู 300",
            "咖啡 60",
        ):
            self.assertFalse(lqe.is_edit_request(t), t)


class HasItemContextTests(unittest.TestCase):
    def test_bare_number_no_context(self):
        # 纯裸数字(含币种词)无物品/卖家 → False(不该当可信费用入账)。
        for t in ("1", "2", "65", "100 บาท", "3 THB"):
            self.assertFalse(lqe.has_item_context(t), t)

    def test_with_item_or_vendor(self):
        for t in ("咖啡 65", "ค่าน้ำ 50", "Starbucks 100", "买菜 40"):
            self.assertTrue(lqe.has_item_context(t), t)


if __name__ == "__main__":
    unittest.main()
