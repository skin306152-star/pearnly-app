# -*- coding: utf-8 -*-
"""销项拆税(services.sales_agg.vat):金标反推 + 两口径差异 + Decimal 类型。"""

import unittest
from decimal import Decimal

from services.sales_agg.vat import split_gross, split_report


class TestSplitGross(unittest.TestCase):
    def test_gold_sister_makeup_may(self):
        # SM 5月官方申报:销售额 858,780.16 / 销项税 60,114.61(毛额=两数之和)。
        sales, vat = split_gross(Decimal("918894.77"))
        self.assertEqual(sales, Decimal("858780.16"))
        self.assertEqual(vat, Decimal("60114.61"))

    def test_returns_decimal_never_float(self):
        sales, vat = split_gross(Decimal("107.00"))
        self.assertIsInstance(sales, Decimal)
        self.assertIsInstance(vat, Decimal)
        self.assertEqual((sales, vat), (Decimal("100.00"), Decimal("7.00")))

    def test_sales_plus_vat_equals_gross(self):
        # 减法拆保证恒等式;独立两次舍入(100/107 与 7/107)在此值会两边各进位差 0.01。
        for raw in ("100.00", "918894.77", "0.01", "10.01"):
            gross = Decimal(raw)
            sales, vat = split_gross(gross)
            self.assertEqual(sales + vat, gross, raw)

    def test_half_up_rounding(self):
        # 7.65 × 7/107 = 0.50046… → 0.50;7.70 × 7/107 = 0.5037…→ 0.50;107.5×7/107=7.032→7.03
        self.assertEqual(split_gross(Decimal("107.50"))[1], Decimal("7.03"))


class TestSplitReport(unittest.TestCase):
    def test_method_diff_reported(self):
        # 逐笔:10.01→0.65 ×3 = 1.95;先加总:30.03→1.96。差异必须如实报告,不藏。
        rep = split_report([Decimal("10.01")] * 3)
        self.assertEqual(rep["gross_total"], Decimal("30.03"))
        self.assertEqual(rep["output_vat"], Decimal("1.96"))
        self.assertEqual(rep["per_line_vat"], Decimal("1.95"))
        self.assertEqual(rep["vat_method_diff"], Decimal("0.01"))

    def test_empty_lines(self):
        rep = split_report([])
        self.assertEqual(rep["gross_total"], Decimal("0"))
        self.assertEqual(rep["output_vat"], Decimal("0.00"))

    def test_all_values_decimal(self):
        rep = split_report([Decimal("1070.00")])
        for key, value in rep.items():
            self.assertIsInstance(value, Decimal, key)
            self.assertNotIsInstance(value, float, key)


if __name__ == "__main__":
    unittest.main()
