# -*- coding: utf-8 -*-
"""期初入参校验(services/stockcard/opening.py · _normalize)。

as_of_date 烂字符串必须在这一层被拦成 422,不许穿到 SQL 层才炸成 500(那是把「诚实
拒绝」变成「假装没这回事」)。
"""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from core.pos_api import PosError
from services.stockcard.opening import _normalize


class NormalizeIdentityTests(unittest.TestCase):
    def test_product_id_path(self):
        product_id, name_key, qty, unit_cost, as_of = _normalize(
            {"product_id": "p-1", "qty": "10", "unit_cost": "5", "as_of_date": "2031-01-01"}
        )
        self.assertEqual(product_id, "p-1")
        self.assertIsNone(name_key)
        self.assertEqual(qty, Decimal("10"))
        self.assertEqual(unit_cost, Decimal("5"))
        self.assertEqual(as_of, date(2031, 1, 1))

    def test_name_path(self):
        product_id, name_key, _, _, _ = _normalize(
            {"name": "  Coffee   Bean  ", "qty": "1", "unit_cost": "1", "as_of_date": "2031-01-01"}
        )
        self.assertIsNone(product_id)
        self.assertEqual(name_key, "Coffee Bean")

    def test_missing_identity_rejected(self):
        with self.assertRaises(PosError) as ctx:
            _normalize({"qty": "1", "unit_cost": "1", "as_of_date": "2031-01-01"})
        self.assertEqual(ctx.exception.detail, "missing_identity")


class NormalizeAsOfDateTests(unittest.TestCase):
    def test_missing_as_of_date_rejected(self):
        with self.assertRaises(PosError) as ctx:
            _normalize({"product_id": "p-1", "qty": "1", "unit_cost": "1"})
        self.assertEqual(ctx.exception.detail, "missing_as_of_date")

    def test_garbage_as_of_date_returns_422_not_raw_crash(self):
        with self.assertRaises(PosError) as ctx:
            _normalize(
                {"product_id": "p-1", "qty": "1", "unit_cost": "1", "as_of_date": "not-a-date"}
            )
        self.assertEqual(ctx.exception.http_status, 422)
        self.assertEqual(ctx.exception.detail, "as_of_date")

    def test_wrong_shape_as_of_date_rejected(self):
        with self.assertRaises(PosError) as ctx:
            _normalize(
                {"product_id": "p-1", "qty": "1", "unit_cost": "1", "as_of_date": "01/02/2031"}
            )
        self.assertEqual(ctx.exception.detail, "as_of_date")

    def test_date_object_passes_through(self):
        _, _, _, _, as_of = _normalize(
            {"product_id": "p-1", "qty": "1", "unit_cost": "1", "as_of_date": date(2031, 6, 1)}
        )
        self.assertEqual(as_of, date(2031, 6, 1))


class NormalizeMoneyTests(unittest.TestCase):
    def test_bad_qty_rejected(self):
        with self.assertRaises(PosError) as ctx:
            _normalize(
                {"product_id": "p-1", "qty": "abc", "unit_cost": "1", "as_of_date": "2031-01-01"}
            )
        self.assertEqual(ctx.exception.detail, "qty")

    def test_bad_unit_cost_rejected(self):
        with self.assertRaises(PosError) as ctx:
            _normalize(
                {"product_id": "p-1", "qty": "1", "unit_cost": "abc", "as_of_date": "2031-01-01"}
            )
        self.assertEqual(ctx.exception.detail, "unit_cost")


if __name__ == "__main__":
    unittest.main()
