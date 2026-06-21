# -*- coding: utf-8 -*-
"""P1 确定性修复(模糊测试 V2 剩余 FAIL):数字词 / 退货找零 / 外币 / 押金。

- 数字词:1k→1000 · 2หมื่น→20000 · 欧式 1.250,50→1250.50(正确记)。
- 退货/找零:คืนของ/เงินทอน 不当支出记。
- 外币:$/USD/หยวน 不静默当 THB 记 → 早拦截澄清。
- 押金:มัดจำ 非普通费用 → 澄清不静默入账。
"""

import unittest
from decimal import Decimal

from services.expense import amount_extract as ae
from services.expense import line_guards as lc
from services.expense import line_quick_entry as lqe
from services.expense import replies


class NumberWordTests(unittest.TestCase):
    def test_k_shorthand(self):
        self.assertEqual(ae.extract_amount("จ่าย 1k", None, None), Decimal("1000"))
        self.assertEqual(ae.extract_amount("ค่าโฆษณา 1.5k", None, None), Decimal("1500"))

    def test_thai_magnitude(self):
        self.assertEqual(ae.extract_amount("ค่าเช่า 2หมื่น", None, None), Decimal("20000"))
        self.assertEqual(ae.extract_amount("เงินเดือน 3 หมื่น", None, None), Decimal("30000"))

    def test_eu_format(self):
        self.assertEqual(ae.extract_amount("ค่าของ 1.250,50", None, None), Decimal("1250.50"))

    def test_thai_numerals(self):
        # 泰数字(会计/正式文档常用)→ 阿拉伯。
        self.assertEqual(ae.extract_amount("กาแฟ ๕๐ บาท", None, None), Decimal("50"))
        self.assertEqual(ae.extract_amount("ค่าเช่า ๒หมื่น", None, None), Decimal("20000"))

    def test_roi_hundred(self):
        self.assertEqual(ae.extract_amount("ค่าของ 5ร้อย", None, None), Decimal("500"))

    def test_plain_unaffected(self):
        self.assertEqual(ae.extract_amount("กาแฟ 65", None, None), Decimal("65"))


class RefundIsNotExpenseTests(unittest.TestCase):
    def test_refund_and_change_detected_income(self):
        for t in ["คืนของ 100", "ได้เงินทอน 20", "ร้านคืนเงิน 300", "退款 500"]:
            self.assertTrue(lqe.detect_income(t), t)

    def test_repayment_with_pay_verb_still_expense(self):
        # 「จ่ายคืนเงินกู้ 500」有 จ่าย(付)→ 是支出·不当退款。
        self.assertFalse(lqe.detect_income("จ่ายคืนเงินกู้ 500"))


class FxDepositTests(unittest.TestCase):
    def test_fx_detected(self):
        for t in ["จ่าย $50", "ค่าโฆษณา USD 100", "ซื้อของ 100 หยวน", "¥1000"]:
            self.assertTrue(lc.is_fx(t), t)

    def test_fx_no_false_positive(self):
        for t in ["กาแฟ 65", "I used 50 baht", "50 บาท"]:
            self.assertFalse(lc.is_fx(t), t)

    def test_deposit_detected(self):
        for t in ["มัดจำ 1000", "วางเงินประกัน 2000", "押金 500"]:
            self.assertTrue(lc.is_deposit(t), t)

    def test_smalltalk_routes_fx_and_deposit(self):
        self.assertEqual(replies.detect_smalltalk("จ่าย $50"), "fx_foreign")
        self.assertEqual(replies.detect_smalltalk("มัดจำ 1000"), "deposit_clarify")

    def test_fx_deposit_pools_exist(self):
        self.assertTrue(replies.pick("fx_foreign", "x", "th"))
        self.assertTrue(replies.pick("deposit_clarify", "x", "th"))


if __name__ == "__main__":
    unittest.main()
