# -*- coding: utf-8 -*-
"""LINE 文本分类(line_classify):费用类型 + 付款方式 关键词归类(确定性·无信号不猜)。"""

import unittest

from services.expense import line_classify as lc


class ExpenseTypeTests(unittest.TestCase):
    def test_service_vs_goods(self):
        self.assertEqual(lc.classify_expense_type("ค่าซ่อม"), "service")
        self.assertEqual(lc.classify_expense_type("水费"), "service")
        self.assertEqual(lc.classify_expense_type("โค้ก"), "goods")
        self.assertEqual(lc.classify_expense_type(""), "goods")


class PaymentMethodTests(unittest.TestCase):
    def test_transfer(self):
        self.assertEqual(lc.detect_payment_method("ค่าของ 100 โอนเงิน"), "transfer")
        self.assertEqual(lc.detect_payment_method("买菜40 转账"), "transfer")

    def test_cash_card_promptpay(self):
        self.assertEqual(lc.detect_payment_method("กาแฟ 60 เงินสด"), "cash")
        self.assertEqual(lc.detect_payment_method("付了500 刷卡"), "card")
        self.assertEqual(lc.detect_payment_method("จ่ายผ่านพร้อมเพย์"), "promptpay")

    def test_no_signal_empty(self):
        self.assertEqual(lc.detect_payment_method("ค่าน้ำ 50"), "")


if __name__ == "__main__":
    unittest.main()
