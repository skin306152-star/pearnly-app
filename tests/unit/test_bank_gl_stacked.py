# -*- coding: utf-8 -*-
"""Unit tests for the coordinate-driven stacked-GL parser, filename-based bank
detection, the chunked Gemini row mapping, and job-param secret stripping.

These lock the fix for the TTB reconciliation that failed in production: a
MR.ERP GL whose rows pdfplumber/text extractors couldn't reassemble, forcing a
Gemini call that truncated its JSON ("Unterminated string"). The headline
regression guard is _amount_and_balance: a credit figure ending one column
left of the balance must never be merged into it.
"""

import unittest

from services.recon.bank_gl_stacked import (
    _amount_and_balance,
    _build_rows,
    _row_fields,
)
from services.recon.bank_recon_utils import _bank_from_filename, _detect_bank
from services.recon.bank_gl_gemini import _row_from_dict


def _w(text, x0, x1):
    return {"text": text, "x0": float(x0), "x1": float(x1), "top": 0.0}


def _bf_row():
    # Balance Forward → opening 0
    return [
        _w("1/5/2026", 59, 95),
        _w("Balance", 98, 130),
        _w("Forward", 131, 160),
        _w("0", 511, 516),
    ]


def _deposit_row(date_s, doc, name, amt_text, amt_x0, bal_text, bal_x0):
    return [
        _w(date_s, 59, 95),
        _w(doc, 98, 150),
        _w(name, 165, 230),
        _w("C1111", 262, 286),
        _w(amt_text, amt_x0, 379),
        _w(bal_text, bal_x0, 512),
    ]


class TestAmountBalanceColumns(unittest.TestCase):
    def test_credit_not_merged_into_balance(self):
        # The production bug: credit "123.37" (x1=449) sat ~12px left of balance
        # "1,049,715.33" (x0=461); a gap-based merge produced 123371049715.33.
        words = [_w("123.37", 423, 449), _w("1,049,715.33", 461, 512)]
        amount, balance = _amount_and_balance(words)
        self.assertEqual(amount, 123.37)
        self.assertEqual(balance, 1049715.33)

    def test_split_balance_fragments_rejoined(self):
        # A balance split by a grouping glyph ("1" + ",727.46") must rejoin and
        # stay distinct from the debit amount in its own column.
        words = [_w("1,727.46", 345, 379), _w("1", 478, 483), _w(",727.46", 483, 512)]
        amount, balance = _amount_and_balance(words)
        self.assertEqual(amount, 1727.46)
        self.assertEqual(balance, 1727.46)

    def test_balance_only_row(self):
        amount, balance = _amount_and_balance([_w("0", 511, 516)])
        self.assertIsNone(amount)
        self.assertEqual(balance, 0.0)


class TestRowFields(unittest.TestCase):
    def test_requires_date_and_balance(self):
        self.assertIsNone(_row_fields([_w("Date", 65, 90), _w("Debit", 331, 360)]))

    def test_pulls_account_and_head(self):
        f = _row_fields(
            _deposit_row("2/5/2026", "SVTAX1", "name", "1,727.46", 345, "1,727.46", 473)
        )
        self.assertEqual(f["acct"], "C1111")
        self.assertEqual(f["balance"], 1727.46)
        self.assertIn("SVTAX1", f["head"])


class TestBuildRows(unittest.TestCase):
    def _sequence(self):
        return [
            _bf_row(),
            _deposit_row("2/5/2026", "SVTAX1", "n1", "1,727.46", 345, "1,727.46", 473),
            _deposit_row("3/5/2026", "SVTAX2", "n2", "1,048,111.24", 335, "1,049,838.70", 461),
            # credit: balance drops 1,049,838.70 → 1,049,715.33 ⇒ credit 123.37
            [
                _w("29/5/2026", 59, 95),
                _w("ปป.CARD", 98, 134),
                _w("10003", 272, 296),
                _w("123.37", 423, 449),
                _w("1,049,715.33", 461, 512),
            ],
        ]

    def test_direction_and_amounts_from_balance(self):
        rows, accounts, opening = _build_rows(self._sequence())
        self.assertEqual(opening, 0.0)
        self.assertEqual(len(rows), 3)  # Balance Forward is not a row
        self.assertEqual((rows[0].debit, rows[0].credit), (1727.46, 0.0))
        credit_row = rows[-1]
        self.assertEqual(credit_row.credit, 123.37)
        self.assertEqual(credit_row.debit, 0.0)
        self.assertIn("C1111", accounts)
        self.assertIn("10003", accounts)

    def test_account_code_filter(self):
        rows, _, _ = _build_rows(self._sequence(), account_code="C1111")
        self.assertTrue(all(r.account_code.startswith("C1111") for r in rows))
        self.assertEqual(len(rows), 2)  # the 10003 credit row is excluded


class TestBankFromFilename(unittest.TestCase):
    def test_ttb_filename_beats_content(self):
        self.assertEqual(_bank_from_filename("STM TTB.pdf"), "ttb")
        self.assertEqual(_bank_from_filename("GL TTB.pdf"), "ttb")

    def test_other_banks(self):
        self.assertEqual(_bank_from_filename("statement_kbank.pdf"), "kbank")
        self.assertEqual(_bank_from_filename("SCB-may.pdf"), "scb")

    def test_no_false_substring_match(self):
        # "may"/"bayfile" must not trip the "bay" (krungsri) signature.
        self.assertEqual(_bank_from_filename("MAY_payroll.pdf"), "")
        self.assertEqual(_bank_from_filename("bayfile.pdf"), "")
        self.assertEqual(_bank_from_filename("report.pdf"), "")

    def test_content_detection_still_works(self):
        self.assertEqual(_detect_bank("Kasikornbank statement"), "kbank")
        self.assertEqual(_detect_bank("TMBThanachart ttb"), "ttb")


class TestGeminiRowMapping(unittest.TestCase):
    def test_deposit_maps_to_debit(self):
        row = _row_from_dict(
            {
                "date": "2026-05-02",
                "doc_no": "X",
                "account_code": "C1111",
                "debit": 100,
                "credit": 0,
            },
            "",
        )
        self.assertEqual(row.debit, 100.0)
        self.assertEqual(row.credit, 0.0)

    def test_bad_date_dropped(self):
        self.assertIsNone(_row_from_dict({"date": "", "debit": 1}, ""))

    def test_account_filter(self):
        self.assertIsNone(
            _row_from_dict({"date": "2026-05-02", "account_code": "9999", "debit": 1}, "C1111")
        )


class TestSecretStripping(unittest.TestCase):
    def test_api_key_is_a_secret_param(self):
        from services.recon_jobs.store import _SECRET_PARAM_KEYS

        self.assertIn("api_key", _SECRET_PARAM_KEYS)

    def test_resolve_api_key_falls_back_to_env(self):
        import os
        from services.recon_jobs._handler_common import _resolve_api_key

        self.assertEqual(_resolve_api_key({"api_key": "from-params"}), "from-params")
        old = os.environ.get("GEMINI_API_KEY")
        os.environ["GEMINI_API_KEY"] = "from-env"
        try:
            self.assertEqual(_resolve_api_key({}), "from-env")
        finally:
            if old is None:
                os.environ.pop("GEMINI_API_KEY", None)
            else:
                os.environ["GEMINI_API_KEY"] = old


if __name__ == "__main__":
    unittest.main()
