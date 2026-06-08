# -*- coding: utf-8 -*-
"""进项合计纯函数单测(services/purchase/totals.py · docs/purchasing/01)。

守两件事:① 后端合计与前端 purchase-calc.js 黄金值逐分一致(设计稿 10:13,600→VAT 952→
含税 14,552→WHT 300→实付 14,252)② 逐行半偶数取整(防 ±1 分漂移)+ dedupe_key 身份指纹。
"""

import unittest
from decimal import Decimal

from services.purchase import totals as t


def _s(d):
    return format(d, "f")


class GoldenTotalsTests(unittest.TestCase):
    # 与设计稿/前端 purchase-calc 一致:货品 3600(7% VAT)+ 服务 10000(7% VAT,3% WHT)。
    LINES = [
        {"item_type": "goods", "qty": 1, "unit_price": 3600, "vat_rate": 7, "wht_rate": 0},
        {"item_type": "service", "qty": 1, "unit_price": 10000, "vat_rate": 7, "wht_rate": 3},
    ]

    def test_golden_chain(self):
        r = t.compute_purchase_totals(self.LINES)
        self.assertEqual(_s(r["subtotal"]), "13600.00")
        self.assertEqual(_s(r["vat_amount"]), "952.00")
        self.assertEqual(_s(r["grand_total"]), "14552.00")
        self.assertEqual(_s(r["wht_amount"]), "300.00")
        self.assertEqual(_s(r["net_payable"]), "14252.00")

    def test_per_line_rounding_then_sum(self):
        # 两行各 0.005 → 逐行半偶数:0.005→0.00(偶),累计 0.00;非先汇总 0.01。
        lines = [
            {"qty": 1, "unit_price": Decimal("0.05"), "vat_rate": 10, "wht_rate": 0},
            {"qty": 1, "unit_price": Decimal("0.05"), "vat_rate": 10, "wht_rate": 0},
        ]
        r = t.compute_purchase_totals(lines)
        self.assertEqual(_s(r["vat_amount"]), "0.00")

    def test_line_discount_floors_at_zero(self):
        lines = [{"qty": 1, "unit_price": 100, "discount": 250, "vat_rate": 7}]
        r = t.compute_purchase_totals(lines)
        self.assertEqual(_s(r["subtotal"]), "0.00")
        self.assertEqual(_s(r["vat_amount"]), "0.00")

    def test_doc_discount_reduces_base_not_vat(self):
        # 镜像前端:整单折扣只减 base,不重算 VAT。
        lines = [{"qty": 1, "unit_price": 1000, "vat_rate": 7}]
        r = t.compute_purchase_totals(lines, doc_discount=100)
        self.assertEqual(_s(r["vat_amount"]), "70.00")  # 1000*7%,折扣不动 VAT
        self.assertEqual(_s(r["grand_total"]), "970.00")  # 900 + 70

    def test_vat_not_applicable_zeroes_vat(self):
        lines = [{"qty": 1, "unit_price": 1000, "vat_rate": 7, "vat_applicable": False}]
        r = t.compute_purchase_totals(lines)
        self.assertEqual(_s(r["vat_amount"]), "0.00")


class DedupeKeyTests(unittest.TestCase):
    def test_no_identity_returns_none(self):
        self.assertIsNone(t.dedupe_key(supplier_tax=None, doc_no=None, grand_total=100))
        self.assertIsNone(t.dedupe_key(supplier_tax="", doc_no="", grand_total=100))

    def test_stable_and_distinct(self):
        a = t.dedupe_key(supplier_tax="1234567890123", doc_no="INV-1", grand_total="100.00")
        b = t.dedupe_key(supplier_tax="1234567890123", doc_no="INV-1", grand_total=100)
        c = t.dedupe_key(supplier_tax="1234567890123", doc_no="INV-2", grand_total="100.00")
        self.assertEqual(a, b)  # 100 == "100.00" 归一
        self.assertNotEqual(a, c)


if __name__ == "__main__":
    unittest.main()
