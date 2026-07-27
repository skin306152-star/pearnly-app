# -*- coding: utf-8 -*-
"""销项拆税(services.sales_agg.vat):金标反推 + 两口径差异 + Decimal 类型。"""

import unittest
from decimal import Decimal

from services.sales_agg import vat
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


class TestSingleRateSource(unittest.TestCase):
    """7/107 只有这一份。三个消费者把它拼进三种介质,各写一份就会出现「底稿算的和申报表
    算的不一样」—— 而那种差异只在月末对不平时才暴露,查起来最贵。"""

    def test_the_rate_itself(self):
        self.assertEqual((vat.VAT_PART, vat.GROSS_PART), (7, 107))

    def test_decimal_split_derives_from_it(self):
        self.assertEqual(vat._VAT_PART, Decimal(vat.VAT_PART))
        self.assertEqual(vat._GROSS_PART, Decimal(vat.GROSS_PART))

    def test_excel_formula_and_purchase_reverse_derive_from_it(self):
        from services.ledger import xlsx_common
        from services.purchase import totals

        self.assertEqual(xlsx_common.VAT_NUMERATOR, vat.VAT_PART)
        self.assertEqual(xlsx_common.VAT_DENOMINATOR, vat.GROSS_PART)
        self.assertEqual((totals.VAT_PART, totals.GROSS_PART), (vat.VAT_PART, vat.GROSS_PART))
        self.assertEqual(totals._VAT_INCL_NUM, Decimal(vat.VAT_PART))
        self.assertEqual(totals._VAT_INCL_DEN, Decimal(vat.GROSS_PART))
        # 反证:公式串里真的用了这个比,不是巧合地各自写了同一个数字。
        self.assertIn(f"*{vat.VAT_PART}/{vat.GROSS_PART},2)", xlsx_common.vat_included("B5"))


if __name__ == "__main__":
    unittest.main()
