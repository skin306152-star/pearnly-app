# -*- coding: utf-8 -*-
"""LINE 数量解析(#8)守门测试。

锁定:split_qty_price 把「总额+数量」拆成行 (qty, unit_price),且过 compute_purchase_totals
后 grand_total 仍等于原总额(per-line gross 量化吸收·总额不漂),含不整除场景。"""

import unittest
from decimal import Decimal

from services.expense.line_quick_entry import split_qty_price
from services.purchase.totals import compute_purchase_totals


def _grand(amount, qty=None, unit_price=None):
    q, up = split_qty_price(amount, qty, unit_price)
    line = {"qty": q, "unit_price": up, "vat_rate": 0, "wht_rate": 0, "vat_applicable": True}
    return q, up, compute_purchase_totals([line])["grand_total"]


class QtySplitTests(unittest.TestCase):
    def test_clean_divisible(self):
        q, up, grand = _grand(120, 2)  # 买2杯咖啡共120
        self.assertEqual(q, "2")
        self.assertEqual(up, "60")
        self.assertEqual(grand, Decimal("120.00"))

    def test_explicit_unit_price(self):
        q, up, grand = _grand(120, 2, 60)
        self.assertEqual((q, up), ("2", "60"))
        self.assertEqual(grand, Decimal("120.00"))

    def test_no_qty_keeps_total(self):
        q, up, grand = _grand(50)
        self.assertEqual((q, up), ("1", "50"))
        self.assertEqual(grand, Decimal("50.00"))

    def test_qty_one_keeps_total(self):
        q, up, grand = _grand(50, 1)
        self.assertEqual((q, up), ("1", "50"))
        self.assertEqual(grand, Decimal("50.00"))

    def test_non_divisible_total_does_not_drift(self):
        # 100÷3 不整除:单价取全精度,过 totals 后总额仍 100.00(per-line gross 量化吸收)
        q, up, grand = _grand(100, 3)
        self.assertEqual(q, "3")
        self.assertEqual(grand, Decimal("100.00"))

    def test_zero_qty_falls_back(self):
        self.assertEqual(split_qty_price(80, 0), ("1", "80"))


if __name__ == "__main__":
    unittest.main()
