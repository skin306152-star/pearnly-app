# -*- coding: utf-8 -*-
"""销项金额计算叶子(totals.py)直接守门:价外/价内 · 折扣 · WHT · 分位。"""

import unittest
from decimal import Decimal

from services.sales import totals


class TotalsTests(unittest.TestCase):
    def test_exclusive_vat(self):
        t = totals.compute_totals([{"qty": 2, "unit_price": "50"}], vat_rate=7)
        self.assertEqual(t["vat_amount"], Decimal("7.00"))
        self.assertEqual(t["grand_total"], Decimal("107.00"))
        self.assertFalse(t["price_includes_vat"])

    def test_inclusive_vat_extracted(self):
        t = totals.compute_totals(
            [{"qty": 1, "unit_price": "107"}], vat_rate=7, price_includes_vat=True
        )
        self.assertEqual(t["vat_amount"], Decimal("7.00"))
        self.assertEqual(t["subtotal_after"], Decimal("100.00"))
        self.assertEqual(t["grand_total"], Decimal("107.00"))

    def test_line_total_clamped_non_negative(self):
        t = totals.compute_totals([{"qty": 1, "unit_price": "50", "discount": "80"}], vat_rate=7)
        self.assertEqual(t["lines"][0]["line_total"], Decimal("0.00"))

    def test_reexported_from_document(self):
        """document.compute_totals 仍指向同一实现(re-export 契约)。"""
        from services.sales import document

        self.assertIs(document.compute_totals, totals.compute_totals)


if __name__ == "__main__":
    unittest.main()
