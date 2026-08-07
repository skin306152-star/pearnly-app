# -*- coding: utf-8 -*-
"""移动加权平均滚存金标(services/stockcard/rolling.py)。

金标用例逐行断言(需求方算例修正版 · 入100@250→出30→入50@260→出20→出10→退货入5→出5)+
无入先出/先退的成本未知诚实态 + 负库存照实滚存(拍板允许)。
"""

from __future__ import annotations

import unittest
from decimal import Decimal

from services.stockcard.rolling import Movement, ZERO_BALANCE, opening_balance, roll


def _mv(direction, qty, price=None, date=1, doc_no="D", line=1):
    return Movement(
        date=date,
        doc_no=doc_no,
        desc="",
        direction=direction,
        qty=Decimal(str(qty)),
        price=None if price is None else Decimal(str(price)),
        sort_key=(date, date, line),
    )


class GoldStandardRollTests(unittest.TestCase):
    """需求方算例修正版:逐行断言 price/amount/bal_*,末行核合计。"""

    @classmethod
    def setUpClass(cls):
        movements = [
            _mv("in", "100", "250", date=1, line=1),  # 入 100@250
            _mv("out", "30", date=2, line=1),  # 出 30
            _mv("in", "50", "260", date=3, line=1),  # 入 50@260
            _mv("out", "20", date=4, line=1),  # 出 20
            _mv("out", "10", date=5, line=1),  # 出 10
            _mv("in", "5", date=6, line=1),  # 退货入 5(credit_note · price=None → 当前 unit)
            _mv("out", "5", date=7, line=1),  # 出 5
        ]
        cls.final, cls.rows = roll(ZERO_BALANCE, movements)

    def test_row_1_purchase_in_100_at_250(self):
        r = self.rows[0]
        self.assertEqual(r["unit_price"], Decimal("250.00"))
        self.assertEqual(r["amount"], Decimal("25000.00"))
        self.assertEqual(r["bal_qty"], Decimal("100"))
        self.assertEqual(r["bal_unit_cost"], Decimal("250.00"))
        self.assertEqual(r["bal_value"], Decimal("25000.00"))

    def test_row_2_sale_out_30(self):
        r = self.rows[1]
        self.assertEqual(r["amount"], Decimal("7500.00"))
        self.assertEqual(r["bal_qty"], Decimal("70"))
        self.assertEqual(r["bal_unit_cost"], Decimal("250.00"))
        self.assertEqual(r["bal_value"], Decimal("17500.00"))

    def test_row_3_purchase_in_50_at_260_reweights_average(self):
        r = self.rows[2]
        self.assertEqual(r["amount"], Decimal("13000.00"))
        self.assertEqual(r["bal_qty"], Decimal("120"))
        self.assertEqual(r["bal_unit_cost"], Decimal("254.17"))
        self.assertEqual(r["bal_value"], Decimal("30500.00"))

    def test_row_4_sale_out_20_at_new_average(self):
        r = self.rows[3]
        self.assertEqual(r["amount"], Decimal("5083.40"))
        self.assertEqual(r["bal_qty"], Decimal("100"))
        self.assertEqual(r["bal_value"], Decimal("25416.60"))

    def test_row_5_sale_out_10(self):
        r = self.rows[4]
        self.assertEqual(r["amount"], Decimal("2541.70"))
        self.assertEqual(r["bal_qty"], Decimal("90"))
        self.assertEqual(r["bal_value"], Decimal("22874.90"))

    def test_row_6_credit_note_return_in_5_at_current_unit(self):
        r = self.rows[5]
        self.assertEqual(r["unit_price"], Decimal("254.17"))  # 退货价=当前结存单价
        self.assertEqual(r["amount"], Decimal("1270.85"))
        self.assertEqual(r["bal_qty"], Decimal("95"))
        self.assertEqual(r["bal_unit_cost"], Decimal("254.17"))
        self.assertEqual(r["bal_value"], Decimal("24145.75"))

    def test_row_7_sale_out_5_final(self):
        r = self.rows[6]
        self.assertEqual(r["amount"], Decimal("1270.85"))
        self.assertEqual(r["bal_qty"], Decimal("90"))
        self.assertEqual(r["bal_unit_cost"], Decimal("254.17"))
        self.assertEqual(r["bal_value"], Decimal("22874.90"))

    def test_totals_in_and_out(self):
        in_rows = [r for r in self.rows if r["kind"] == "in"]
        out_rows = [r for r in self.rows if r["kind"] == "out"]
        self.assertEqual(sum((r["qty"] for r in in_rows), Decimal("0")), Decimal("155"))
        self.assertEqual(sum((r["amount"] for r in in_rows), Decimal("0")), Decimal("39270.85"))
        self.assertEqual(sum((r["qty"] for r in out_rows), Decimal("0")), Decimal("65"))
        self.assertEqual(sum((r["amount"] for r in out_rows), Decimal("0")), Decimal("16395.95"))

    def test_final_balance_matches_last_row(self):
        self.assertEqual(self.final.qty, Decimal("90"))
        self.assertEqual(self.final.unit, Decimal("254.17"))
        self.assertEqual(self.final.value, Decimal("22874.90"))


class UnknownCostHonestyTests(unittest.TestCase):
    """没入过库就出/退 → 价格诚实为 None,qty 照记(不假造成本)。"""

    def test_sale_before_any_purchase_returns_none_price(self):
        final, rows = roll(ZERO_BALANCE, [_mv("out", "10")])
        r = rows[0]
        self.assertIsNone(r["unit_price"])
        self.assertIsNone(r["amount"])
        self.assertIsNone(r["bal_unit_cost"])
        self.assertEqual(r["bal_qty"], Decimal("-10"))
        self.assertIsNone(final.unit)
        self.assertIsNone(final.value)

    def test_return_in_before_any_purchase_returns_none_price(self):
        final, rows = roll(ZERO_BALANCE, [_mv("in", "10")])  # credit_note,price=None
        r = rows[0]
        self.assertIsNone(r["unit_price"])
        self.assertEqual(r["bal_qty"], Decimal("10"))
        self.assertIsNone(final.unit)

    def test_cost_established_once_a_real_purchase_happens(self):
        movements = [_mv("out", "5"), _mv("in", "10", "100")]
        final, rows = roll(ZERO_BALANCE, movements)
        self.assertIsNone(rows[0]["unit_price"])
        self.assertEqual(rows[1]["unit_price"], Decimal("100.00"))
        self.assertEqual(final.qty, Decimal("5"))
        self.assertIsNotNone(final.unit)


class NegativeStockTests(unittest.TestCase):
    """负库存照实滚存(拍板允许),unit_cost 一旦确立就沿用到出库。"""

    def test_sale_exceeding_stock_goes_negative_at_known_cost(self):
        movements = [_mv("in", "10", "50"), _mv("out", "15")]
        final, rows = roll(ZERO_BALANCE, movements)
        self.assertEqual(rows[1]["bal_qty"], Decimal("-5"))
        self.assertEqual(rows[1]["unit_price"], Decimal("50.00"))
        self.assertEqual(final.qty, Decimal("-5"))
        self.assertEqual(final.value, Decimal("-250.00"))


class OpeningBalanceTests(unittest.TestCase):
    def test_zero_qty_opening_is_cost_unestablished(self):
        bal = opening_balance(0, 100)
        self.assertEqual(bal.qty, Decimal("0"))
        self.assertIsNone(bal.unit)

    def test_nonzero_opening_establishes_cost(self):
        bal = opening_balance("20", "12.345")
        self.assertEqual(bal.qty, Decimal("20"))
        self.assertEqual(bal.value, Decimal("246.90"))
        self.assertEqual(bal.unit, Decimal("12.35"))


if __name__ == "__main__":
    unittest.main()
