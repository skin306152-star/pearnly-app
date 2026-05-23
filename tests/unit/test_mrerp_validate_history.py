#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_mrerp_validate_history.py

Unit tests for mrerp_xlsx_generator.validate_history_for_sales_credit's
expanded preflight checks (P1-A §3.1-§3.5, landed 2026-05-18):

  - field-length ceilings: invoice_no/bill_no/customer_code/customer_bill
  - tax-rate enum (vat_7 / vat_0 / vat_exempt / non_vat)
  - negative-amount strict reject via fmt_number_strict
  - future-date hard reject (>+30d) + warnings (>+7d, <-730d)

Plus a coverage sweep of the legacy ERR_* codes so a regression in the
older logic also shows here.

Run:
    python -m unittest tests.unit.test_mrerp_validate_history -v
"""

from __future__ import annotations

import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import mrerp_xlsx_generator as gen  # noqa: E402


def _today_iso() -> str:
    return date.today().isoformat()


def _good_history(**overrides):
    h = {
        "client_id": 99,
        "invoice_number": "OK-001",
        "invoice_date": _today_iso(),
        "subtotal": "100.00",
        "vat": "7.00",
        "total_amount": "107.00",
        "items": [
            {
                "name": "TEST ITEM",
                "qty": 1,
                "unit_price": 100,
                "amount": 100,
            }
        ],
    }
    h.update(overrides)
    return h


def _good_mappings(customer_code: str = "0006"):
    return {
        "clients": [
            {
                "erp_type": "mrerp",
                "client_id": 99,
                "erp_code": customer_code,
            }
        ],
        "accounts": [],
        "taxes": [],
        "products": [],
    }


class HappyPathTests(unittest.TestCase):

    def test_legitimate_history_passes_with_no_warnings(self):
        ok, err, warns = gen.validate_history_for_sales_credit(
            _good_history(),
            _good_mappings(),
        )
        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertEqual(warns, [])

    def test_warning_for_near_future_date(self):
        # +14 days is within reject window (30) but past warn threshold (7).
        d = (date.today() + timedelta(days=14)).isoformat()
        ok, err, warns = gen.validate_history_for_sales_credit(
            _good_history(invoice_date=d),
            _good_mappings(),
        )
        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertIn("WARN_DATE_NEAR_FUTURE", warns)

    def test_warning_for_very_old_date(self):
        d = (date.today() - timedelta(days=900)).isoformat()
        ok, err, warns = gen.validate_history_for_sales_credit(
            _good_history(invoice_date=d),
            _good_mappings(),
        )
        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertIn("WARN_DATE_TOO_OLD", warns)


class LegacyErrorCoverageTests(unittest.TestCase):
    """Make sure existing ERR_* codes still fire on the same triggers."""

    def test_no_history(self):
        ok, err, _ = gen.validate_history_for_sales_credit(
            {},
            _good_mappings(),
        )
        self.assertFalse(ok)
        self.assertEqual(err, "ERR_NO_HISTORY")

    def test_no_client(self):
        ok, err, _ = gen.validate_history_for_sales_credit(
            _good_history(client_id=0),
            _good_mappings(),
        )
        self.assertFalse(ok)
        self.assertEqual(err, "ERR_NO_CLIENT")

    def test_no_customer_mapping(self):
        empty_mappings = {"clients": [], "accounts": [], "taxes": [], "products": []}
        ok, err, _ = gen.validate_history_for_sales_credit(
            _good_history(),
            empty_mappings,
        )
        self.assertFalse(ok)
        self.assertEqual(err, "ERR_NO_CUSTOMER_MAPPING")

    def test_no_invoice_no(self):
        h = _good_history()
        h["invoice_number"] = None
        h.pop("invoice_no", None)
        ok, err, _ = gen.validate_history_for_sales_credit(
            h,
            _good_mappings(),
        )
        self.assertFalse(ok)
        self.assertEqual(err, "ERR_NO_INVOICE_NO")

    def test_no_invoice_date(self):
        h = _good_history()
        h["invoice_date"] = None
        ok, err, _ = gen.validate_history_for_sales_credit(
            h,
            _good_mappings(),
        )
        self.assertFalse(ok)
        self.assertEqual(err, "ERR_NO_INVOICE_DATE")

    def test_zero_total_is_rejected(self):
        ok, err, _ = gen.validate_history_for_sales_credit(
            _good_history(total_amount="0"),
            _good_mappings(),
        )
        self.assertFalse(ok)
        self.assertEqual(err, "ERR_NO_TOTAL_AMOUNT")


class FieldLengthTests(unittest.TestCase):
    """P1-A §3.1 — field-length preflight."""

    def setUp(self):
        self._orig_derive = gen.derive_mrerp_invoice_no

    def tearDown(self):
        gen.derive_mrerp_invoice_no = self._orig_derive

    def test_invoice_no_too_long(self):
        gen.derive_mrerp_invoice_no = lambda h: "X" * 19  # 19 > 18 max
        ok, err, _ = gen.validate_history_for_sales_credit(
            _good_history(),
            _good_mappings(),
        )
        self.assertFalse(ok)
        self.assertEqual(err, "ERR_INVOICE_NO_TOO_LONG")

    def test_bill_no_too_long(self):
        # invoice_no 19 → bill_no = SI + 19 = 21 chars, exceeds 20.
        # But invoice_no=19 fires the invoice-length error first.
        # Use invoice_no exactly 18 to slip past the first check,
        # then watch bill_no fail.
        gen.derive_mrerp_invoice_no = lambda h: "Y" * 18
        # 18 invoice + "SI" prefix = 20 -> ok. Push 19 → invoice err.
        # To exercise bill_no error in isolation, lift the invoice
        # ceiling for this one test.
        orig_inv_max = gen.MRERP_INVOICE_NO_MAX
        gen.MRERP_INVOICE_NO_MAX = 25
        try:
            gen.derive_mrerp_invoice_no = lambda h: "Y" * 19
            ok, err, _ = gen.validate_history_for_sales_credit(
                _good_history(),
                _good_mappings(),
            )
            self.assertFalse(ok)
            self.assertEqual(err, "ERR_BILL_NO_TOO_LONG")
        finally:
            gen.MRERP_INVOICE_NO_MAX = orig_inv_max

    def test_customer_code_too_long(self):
        ok, err, _ = gen.validate_history_for_sales_credit(
            _good_history(),
            _good_mappings(customer_code="X" * 21),
        )
        self.assertFalse(ok)
        self.assertEqual(err, "ERR_CUSTOMER_CODE_TOO_LONG")

    def test_customer_bill_falls_back_to_customer_code(self):
        # Today customer_bill defaults to customer_code, so its own
        # length-overflow path requires customer_code overflow too.
        # Coverage: exercising the bill-length check is impossible
        # while bill = code by construction. Documented in the
        # validator's docstring.
        ok, err, _ = gen.validate_history_for_sales_credit(
            _good_history(),
            _good_mappings(customer_code="X" * 21),
        )
        # The first failure wins (customer_code), which is expected.
        self.assertFalse(ok)
        self.assertEqual(err, "ERR_CUSTOMER_CODE_TOO_LONG")


class TaxRateEnumTests(unittest.TestCase):
    """P1-A §3.2 — tax-rate enum gate."""

    def test_default_vat_7_is_valid(self):
        # No tax_rate_pct supplied → derive_tax_kind defaults to vat_7.
        ok, err, _ = gen.validate_history_for_sales_credit(
            _good_history(),
            _good_mappings(),
        )
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_explicit_vat_0_is_valid(self):
        ok, err, _ = gen.validate_history_for_sales_credit(
            _good_history(tax_rate_pct=0),
            _good_mappings(),
        )
        self.assertTrue(ok)

    def test_wht_kind_is_rejected_for_sales_credit(self):
        ok, err, _ = gen.validate_history_for_sales_credit(
            _good_history(wht_rate_pct=3),
            _good_mappings(),
        )
        self.assertFalse(ok)
        self.assertEqual(err, "ERR_TAX_RATE_INVALID")


class NegativeAmountTests(unittest.TestCase):
    """P1-A §3.3 — strict negative-amount reject."""

    def test_negative_total_rejected(self):
        ok, err, _ = gen.validate_history_for_sales_credit(
            _good_history(total_amount="-50.00"),
            _good_mappings(),
        )
        self.assertFalse(ok)
        self.assertEqual(err, "ERR_NEGATIVE_AMOUNT")

    def test_fmt_number_strict_raises_on_negative(self):
        with self.assertRaises(ValueError):
            gen.fmt_number_strict(-1)

    def test_fmt_number_strict_raises_on_overflow(self):
        with self.assertRaises(ValueError):
            gen.fmt_number_strict("1000000000.00")  # > 999_999_999.99

    def test_fmt_number_strict_accepts_normal(self):
        self.assertAlmostEqual(gen.fmt_number_strict("123.45"), 123.45)


class FutureDateTests(unittest.TestCase):
    """P1-A §3.5 — future-date hard reject."""

    def test_far_future_rejected(self):
        d = (date.today() + timedelta(days=60)).isoformat()
        ok, err, _ = gen.validate_history_for_sales_credit(
            _good_history(invoice_date=d),
            _good_mappings(),
        )
        self.assertFalse(ok)
        self.assertEqual(err, "ERR_DATE_FUTURE")

    def test_exactly_at_reject_threshold_is_accepted(self):
        # 30d exactly is still within the warn band (>= 7, <= 30), accepted.
        d = (date.today() + timedelta(days=30)).isoformat()
        ok, err, warns = gen.validate_history_for_sales_credit(
            _good_history(invoice_date=d),
            _good_mappings(),
        )
        self.assertTrue(ok)
        self.assertIn("WARN_DATE_NEAR_FUTURE", warns)


if __name__ == "__main__":
    unittest.main(verbosity=2)
