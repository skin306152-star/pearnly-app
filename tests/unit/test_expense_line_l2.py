# -*- coding: utf-8 -*-
"""线 B 批2 · L2 LLM 兜底:JSON→ExpenseDraft 强转 + 意图枚举 + 护栏(prompt 只出数据)。"""

import os
import unittest
from decimal import Decimal
from unittest import mock

from services.expense import line_l2


class ToDraftTests(unittest.TestCase):
    def test_coerces_numbers_to_decimal(self):
        # 金额须在原文里有对应数字才保留(接地守卫);本例验逗号字符串→Decimal 强转。
        d = line_l2.to_draft(
            {"intent": "expense", "amount": "1,250.5", "qty": "3", "unit_price": "45"},
            "ซื้อกาแฟ 1,250.5 บาท",
        )
        self.assertEqual(d.amount, Decimal("1250.5"))
        self.assertEqual(d.qty, Decimal("3"))
        self.assertEqual(d.unit_price, Decimal("45"))

    def test_null_amount_means_no_amount(self):
        d = line_l2.to_draft({"intent": "other", "amount": None}, "สวัสดี")
        self.assertFalse(d.has_amount())

    def test_expense_type_whitelist(self):
        self.assertEqual(line_l2.to_draft({"expense_type": "service"}, "x").expense_type, "service")
        self.assertEqual(line_l2.to_draft({"expense_type": "weird"}, "x").expense_type, "")

    def test_keeps_invoice_and_tax(self):
        d = line_l2.to_draft(
            {"amount": 60, "vendor_tax_id": "0105546015062", "invoice_number": "IV69/00179"}, "x"
        )
        self.assertEqual(d.vendor_tax_id, "0105546015062")
        self.assertEqual(d.invoice_number, "IV69/00179")


class ApiKeyTests(unittest.TestCase):
    def test_own_key_first(self):
        self.assertEqual(line_l2.resolve_api_key({"gemini_api_key": "k1"}), "k1")

    def test_env_fallback(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "envk"}, clear=False):
            self.assertEqual(line_l2.resolve_api_key({}), "envk")

    def test_none_when_absent(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
            self.assertIsNone(line_l2.resolve_api_key({}))


if __name__ == "__main__":
    unittest.main()
