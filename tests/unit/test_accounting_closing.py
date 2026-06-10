# -*- coding: utf-8 -*-
"""月末结账守门(docs/accounting/03 §5):期校验 / 待审挡结 / R9 结转 / 水位锁期。"""

import unittest
from datetime import date
from decimal import Decimal
from unittest import mock

from core.pos_api import PosError
from services.accounting import closing


class FakeCursor:
    def __init__(self, results=None):
        self.executed = []
        self._results = list(results or [])

    def execute(self, sql, params=None):
        self.executed.append((" ".join(sql.split()), params))

    def fetchone(self):
        return self._results.pop(0) if self._results else None

    def fetchall(self):
        return self._results.pop(0) if self._results else []


class PeriodHelpersTests(unittest.TestCase):
    def test_validate_period_accepts_yyyy_mm(self):
        self.assertEqual(closing.validate_period("2026-06"), "2026-06")

    def test_validate_period_rejects_malformed(self):
        for bad in (None, "", "2026-13", "2026-6", "202606", "2026-06-01"):
            with self.assertRaises(PosError) as ctx:
                closing.validate_period(bad)
            self.assertEqual(ctx.exception.code, "acct.unexpected")

    def test_period_end_handles_leap_and_short_months(self):
        self.assertEqual(closing.period_end("2026-02"), date(2026, 2, 28))
        self.assertEqual(closing.period_end("2024-02"), date(2024, 2, 29))
        self.assertEqual(closing.period_end("2026-06"), date(2026, 6, 30))


class VatTotalsTests(unittest.TestCase):
    def test_unmapped_roles_mean_zero_vat(self):
        cur = FakeCursor()
        with mock.patch("services.accounting.store.resolve_mappings", return_value={}):
            self.assertEqual(
                closing.vat_totals(cur, tenant_id="t", workspace_client_id=1, period="2026-06"),
                (Decimal("0"), Decimal("0")),
            )
        self.assertEqual(cur.executed, [])

    def test_sums_exclude_vat_closing_source(self):
        cur = FakeCursor(results=[{"output_vat": "700.00", "input_vat": "300.00"}])
        mappings = {"output_vat": "a-out", "input_vat": "a-in"}
        with mock.patch("services.accounting.store.resolve_mappings", return_value=mappings):
            out_vat, in_vat = closing.vat_totals(
                cur, tenant_id="t", workspace_client_id=1, period="2026-06"
            )
        self.assertEqual((out_vat, in_vat), (Decimal("700.00"), Decimal("300.00")))
        sql, params = cur.executed[0]
        self.assertIn("source_type != 'vat_closing'", sql)
        self.assertIn("workspace_client_id", sql)


def _open_settings(**over):
    s = {"closed_through": None, "auto_post": False}
    s.update(over)
    return s


class ClosePeriodTests(unittest.TestCase):
    def test_already_closed_period_rejected(self):
        cur = FakeCursor()
        with mock.patch(
            "services.accounting.settings.get_settings",
            return_value=_open_settings(closed_through="2026-06"),
        ):
            with self.assertRaises(PosError) as ctx:
                closing.close_period(cur, tenant_id="t", workspace_client_id=1, period="2026-05")
        self.assertEqual(ctx.exception.code, "acct.period_closed")

    def test_pending_review_blocks_close(self):
        cur = FakeCursor(results=[{"n": 2}])
        with mock.patch("services.accounting.settings.get_settings", return_value=_open_settings()):
            with self.assertRaises(PosError) as ctx:
                closing.close_period(cur, tenant_id="t", workspace_client_id=1, period="2026-06")
        self.assertEqual(ctx.exception.code, "acct.unbalanced")
        self.assertIn("pending_review:2", ctx.exception.detail)

    def test_zero_vat_closes_without_voucher_and_advances_watermark(self):
        cur = FakeCursor(results=[{"n": 0}])
        with (
            mock.patch("services.accounting.settings.get_settings", return_value=_open_settings()),
            mock.patch(
                "services.accounting.closing.vat_totals",
                return_value=(Decimal("0"), Decimal("0")),
            ),
            mock.patch("services.accounting.settings.update_settings") as upsert,
            mock.patch("services.accounting.posting.generate_for_source") as gen,
        ):
            result = closing.close_period(
                cur, tenant_id="t", workspace_client_id=1, period="2026-06"
            )
        gen.assert_not_called()
        upsert.assert_called_once()
        self.assertEqual(result["closed"], "2026-06")
        self.assertIsNone(result["voucher"])
        self.assertEqual(result["vat_payable"], Decimal("0"))
        watermark_sql = cur.executed[-1][0]
        self.assertIn("closed_through = %s", watermark_sql)
        self.assertIn("closed_through < %s", watermark_sql)

    def test_vat_closing_voucher_promoted_to_posted(self):
        cur = FakeCursor(results=[{"n": 0}])
        voucher = {"id": "v9", "status": "pending_review", "review_reason": "suggest_mode"}
        with (
            mock.patch("services.accounting.settings.get_settings", return_value=_open_settings()),
            mock.patch(
                "services.accounting.closing.vat_totals",
                return_value=(Decimal("700"), Decimal("300")),
            ),
            mock.patch("services.accounting.settings.update_settings"),
            mock.patch(
                "services.accounting.posting.generate_for_source", return_value=voucher
            ) as gen,
            mock.patch("services.accounting.vouchers.set_status") as set_status,
        ):
            result = closing.close_period(
                cur, tenant_id="t", workspace_client_id=1, period="2026-06", closed_by="u1"
            )
        ctx = gen.call_args.kwargs["context"]
        self.assertEqual(ctx["voucher_date"], date(2026, 6, 30))
        self.assertEqual(ctx["output_vat_total"], Decimal("700"))
        set_status.assert_called_once()
        self.assertEqual(set_status.call_args.kwargs["status"], "posted")
        self.assertEqual(result["vat_payable"], Decimal("400"))
        self.assertEqual(result["voucher"]["status"], "posted")

    def test_mapping_missing_shell_aborts_close(self):
        cur = FakeCursor(results=[{"n": 0}])
        shell = {
            "id": "v9",
            "status": "pending_review",
            "review_reason": "mapping_missing:vat_payable",
        }
        with (
            mock.patch("services.accounting.settings.get_settings", return_value=_open_settings()),
            mock.patch(
                "services.accounting.closing.vat_totals",
                return_value=(Decimal("700"), Decimal("300")),
            ),
            mock.patch("services.accounting.posting.generate_for_source", return_value=shell),
        ):
            with self.assertRaises(PosError) as ctx:
                closing.close_period(cur, tenant_id="t", workspace_client_id=1, period="2026-06")
        self.assertEqual(ctx.exception.code, "acct.mapping_missing")
