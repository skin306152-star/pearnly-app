# -*- coding: utf-8 -*-
"""出账本聚合守门(docs/accounting/03 §5):总账期初期末 / 试算表归栏且平 /
明细账分组 / VAT 报告符号与剔除结转 / 财报配平。"""

import unittest
from datetime import date
from decimal import Decimal
from unittest import mock

from services.accounting import books


class FakeCursor:
    def __init__(self, result_sets=None):
        self.executed = []
        self._result_sets = list(result_sets or [])

    def execute(self, sql, params=None):
        self.executed.append((" ".join(sql.split()), params))

    def fetchall(self):
        return self._result_sets.pop(0) if self._result_sets else []


def _acct_row(code, acct_type, debit="0", credit="0", opening="0", name=None):
    return {
        "id": f"id-{code}",
        "code": code,
        "name_zh": name or f"科目{code}",
        "name_th": None,
        "acct_type": acct_type,
        "period_debit": debit,
        "period_credit": credit,
        "opening_net": opening,
    }


class GeneralLedgerTests(unittest.TestCase):
    def test_closing_is_opening_plus_period_net(self):
        cur = FakeCursor([[_acct_row("1010", "asset", debit="100", credit="30", opening="50")]])
        gl = books.general_ledger(cur, tenant_id="t", workspace_client_id=1, period="2026-06")
        acct = gl["accounts"][0]
        self.assertEqual(acct["opening"], Decimal("50"))
        self.assertEqual(acct["closing"], Decimal("120"))
        self.assertEqual(gl["totals"], {"debit": Decimal("100"), "credit": Decimal("30")})
        sql, params = cur.executed[0]
        self.assertIn("status IN ('posted', 'auto_posted')", sql)
        self.assertIn("workspace_client_id", sql)

    def test_bad_period_rejected(self):
        from core.pos_api import PosError

        with self.assertRaises(PosError):
            books.general_ledger(FakeCursor(), tenant_id="t", workspace_client_id=1, period="junk")


class TrialBalanceTests(unittest.TestCase):
    def test_positive_net_goes_debit_negative_goes_credit_zero_skipped(self):
        rows = [
            _acct_row("1010", "asset", debit="107"),
            _acct_row("2030", "liability", credit="7"),
            _acct_row("4010", "revenue", credit="100"),
            _acct_row("9999", "expense"),
        ]
        with mock.patch.object(books, "_account_period_sums", return_value=rows):
            tb = books.trial_balance(
                FakeCursor(), tenant_id="t", workspace_client_id=1, period="2026-06"
            )
        by_code = {r["code"]: r for r in tb["rows"]}
        self.assertEqual(by_code["1010"]["debit"], Decimal("107"))
        self.assertEqual(by_code["2030"]["credit"], Decimal("7"))
        self.assertEqual(by_code["4010"]["credit"], Decimal("100"))
        self.assertNotIn("9999", by_code)
        self.assertEqual(tb["totals"]["debit"], tb["totals"]["credit"])
        self.assertTrue(tb["balanced"])


class SubsidiaryLedgerTests(unittest.TestCase):
    def test_groups_lines_by_account_with_running_totals(self):
        line = {
            "account_id": "id-1010",
            "code": "1010",
            "name_zh": "现金",
            "name_th": None,
            "acct_type": "asset",
            "voucher_no": "JV2606-0001",
            "voucher_date": date(2026, 6, 1),
            "description": "POS 日结",
            "memo": None,
            "dr_cr": "debit",
            "amount": "107.00",
        }
        cur = FakeCursor([[line, {**line, "dr_cr": "credit", "amount": "7.00"}]])
        led = books.subsidiary_ledger(cur, tenant_id="t", workspace_client_id=1, period="2026-06")
        self.assertEqual(len(led["accounts"]), 1)
        acct = led["accounts"][0]
        self.assertEqual(acct["debit_total"], Decimal("107.00"))
        self.assertEqual(acct["credit_total"], Decimal("7.00"))
        self.assertEqual(acct["lines"][0]["description"], "POS 日结")


class VatReportTests(unittest.TestCase):
    def _vat_line(self, dr_cr, amount):
        return {
            "voucher_no": "JV1",
            "voucher_date": date(2026, 6, 2),
            "source_type": "sale",
            "source_ref": "INV-1",
            "description": "卖货",
            "dr_cr": dr_cr,
            "amount": amount,
        }

    def test_red_reversal_lines_count_negative(self):
        cur = FakeCursor(
            [
                [self._vat_line("credit", "70"), self._vat_line("debit", "7")],
                [self._vat_line("debit", "30")],
            ]
        )
        mappings = {"output_vat": "a-out", "input_vat": "a-in"}
        with mock.patch("services.accounting.store.resolve_mappings", return_value=mappings):
            rep = books.vat_report(cur, tenant_id="t", workspace_client_id=1, period="2026-06")
        self.assertEqual(rep["sales"]["total"], Decimal("63"))
        self.assertEqual(rep["purchase"]["total"], Decimal("30"))
        self.assertEqual(rep["vat_payable"], Decimal("33"))
        for sql, _ in cur.executed:
            self.assertIn("source_type != 'vat_closing'", sql)

    def test_unmapped_roles_yield_empty_report(self):
        cur = FakeCursor()
        with mock.patch("services.accounting.store.resolve_mappings", return_value={}):
            rep = books.vat_report(cur, tenant_id="t", workspace_client_id=1, period="2026-06")
        self.assertEqual(rep["sales"]["rows"], [])
        self.assertEqual(rep["vat_payable"], Decimal("0"))
        self.assertEqual(cur.executed, [])


class FinancialsTests(unittest.TestCase):
    def test_balance_sheet_balances_with_current_earnings(self):
        rows = [
            _acct_row("1010", "asset", debit="107"),
            _acct_row("2030", "liability", credit="7"),
            _acct_row("4010", "revenue", credit="100"),
            _acct_row("5010", "expense", debit="40", credit="40"),
        ]
        with mock.patch.object(books, "_account_period_sums", return_value=rows):
            fin = books.financials(
                FakeCursor(), tenant_id="t", workspace_client_id=1, period="2026-06"
            )
        self.assertEqual(fin["pnl"]["revenue_total"], Decimal("100"))
        self.assertEqual(fin["pnl"]["expense_total"], Decimal("0"))
        self.assertEqual(fin["pnl"]["net_profit"], Decimal("100"))
        bs = fin["balance_sheet"]
        self.assertEqual(bs["asset_total"], Decimal("107"))
        self.assertEqual(bs["liability_total"], Decimal("7"))
        self.assertEqual(bs["current_earnings"], Decimal("100"))
        self.assertTrue(bs["balanced"])
