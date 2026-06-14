# -*- coding: utf-8 -*-
"""采购配置层纯函数单测(suppliers/settings/categories · 不连库 · docs/purchasing/02 §5-6)。

只覆盖无游标的纯逻辑:税号校验、率清洗/格式化、两级预设结构。DB 行为由 SQL 隔离闸
(test_purchase_sql_isolation)+ 真账号 E2E 守。
"""

import unittest
from decimal import Decimal

from services.purchase import categories as cat
from services.purchase import settings as st
from services.purchase import suppliers as sup


class TaxIdTests(unittest.TestCase):
    def test_blank_is_valid(self):
        # 小供应商可无税号。
        self.assertTrue(sup.is_valid_tax_id(None))
        self.assertTrue(sup.is_valid_tax_id(""))

    def test_13_digits_valid(self):
        self.assertTrue(sup.is_valid_tax_id("1234567890123"))
        self.assertTrue(sup.is_valid_tax_id(" 1234567890123 "))

    def test_wrong_length_invalid(self):
        self.assertFalse(sup.is_valid_tax_id("123"))
        self.assertFalse(sup.is_valid_tax_id("12345678901234"))
        self.assertFalse(sup.is_valid_tax_id("abcdefghijklm"))


class SettingsRateTests(unittest.TestCase):
    def test_rate_clamps_range(self):
        self.assertEqual(st._rate(-5, "3"), Decimal("0"))
        self.assertEqual(st._rate(150, "3"), Decimal("100"))
        self.assertEqual(st._rate(7, "3"), Decimal("7"))

    def test_rate_bad_input_falls_back(self):
        self.assertEqual(st._rate("xx", "3"), Decimal("3"))

    def test_rate_str_trims_zeros(self):
        self.assertEqual(st._rate_str(Decimal("10.00")), "10")
        self.assertEqual(st._rate_str(Decimal("8.50")), "8.5")
        self.assertEqual(st._rate_str(0), "0")


class PresetTreeTests(unittest.TestCase):
    def test_preset_is_two_level_only(self):
        # 子类不得再带孙(严格两级)。
        for parent_name, children in cat._PRESET:
            self.assertIsInstance(parent_name, str)
            self.assertIsInstance(children, tuple)
            for c in children:
                self.assertIsInstance(c, str)

    def test_preset_has_purchase_root(self):
        # 齐全树:采购根 + 至少 10 个大类(进项常用全覆盖)。
        roots = [p for p, _ in cat._PRESET]
        self.assertIn("ซื้อสินค้า/วัตถุดิบ", roots)
        self.assertGreaterEqual(len(roots), 10)


if __name__ == "__main__":
    unittest.main()
