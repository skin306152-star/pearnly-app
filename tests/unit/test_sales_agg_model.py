# -*- coding: utf-8 -*-
"""输入契约适配(services.sales_agg.model):佛历日期 / 缺字段诚实降级 / Decimal 类型。"""

import unittest
from datetime import date
from decimal import Decimal

from services.sales_agg import model
from services.sales_agg.model import BankCredit, EdcSettlement, SalesDoc, to_money


class TestToMoney(unittest.TestCase):
    def test_thai_formats(self):
        self.assertEqual(to_money("1,234.50"), Decimal("1234.50"))
        self.assertEqual(to_money("฿ 918,894.77"), Decimal("918894.77"))

    def test_missing_is_none_not_zero(self):
        # 缺失≠0:毛额缺失归 0 会静默吃掉销项,必须留 None 交点名。
        for raw in (None, "", "   ", "n/a", True, False):
            self.assertIsNone(to_money(raw), repr(raw))

    def test_never_float(self):
        for raw in ("12.5", 12.5, 12, Decimal("12.5")):
            value = to_money(raw)
            self.assertIsInstance(value, Decimal)
            self.assertEqual(value, Decimal("12.5") if raw != 12 else Decimal("12"))


class TestEdcSettlement(unittest.TestCase):
    # 贴近真实 EDC 结算单(SETTLEMENT REPORT)日切小票的形状。
    FIXTURE = {
        "settle_date": "31/05/2569",
        "gross_amount": "10,700.00",
        "fee_amount": "160.50",
        "net_amount": "10,539.50",
        "batch_no": "000123",
        "terminal_id": "70001234",
    }

    def test_adapt_buddhist_date_and_decimals(self):
        row, issues = EdcSettlement.adapt(self.FIXTURE, 0)
        self.assertEqual(issues, [])
        self.assertEqual(row.day, date(2026, 5, 31))
        self.assertEqual(row.gross, Decimal("10700.00"))
        self.assertEqual(row.fee, Decimal("160.50"))
        self.assertEqual(row.net, Decimal("10539.50"))
        self.assertEqual(row.batch_no, "000123")
        self.assertTrue(row.usable)
        for v in (row.gross, row.fee, row.net):
            self.assertIsInstance(v, Decimal)

    def test_two_digit_year_is_buddhist(self):
        row, _ = EdcSettlement.adapt(dict(self.FIXTURE, settle_date="15/05/69"), 0)
        self.assertEqual(row.day, date(2026, 5, 15))

    def test_gross_derived_from_net_plus_fee(self):
        payload = dict(self.FIXTURE)
        del payload["gross_amount"]
        row, issues = EdcSettlement.adapt(payload, 0)
        self.assertEqual(row.gross, Decimal("10700.00"))
        self.assertTrue(row.gross_derived)
        self.assertIn(model.ISSUE_GROSS_DERIVED, issues)

    def test_gross_unresolved_stays_none(self):
        row, issues = EdcSettlement.adapt({"settle_date": "31/05/2569"}, 3)
        self.assertIsNone(row.gross)
        self.assertFalse(row.usable)
        self.assertIn(model.ISSUE_GROSS, issues)
        self.assertEqual(row.ref, "edc:3")

    def test_date_unresolved(self):
        row, issues = EdcSettlement.adapt({"gross_amount": "100.00"}, 0)
        self.assertIsNone(row.day)
        self.assertFalse(row.usable)
        self.assertIn(model.ISSUE_DATE, issues)


class TestBankCredit(unittest.TestCase):
    def test_adapt_workorder_tx_dict_shape(self):
        # workorder_recon_adapter._tx_dict 的流水字典原样喂进来,零翻译。
        row, issues = BankCredit.adapt(
            {
                "tx_date": "2026-05-16",
                "amount": "10,539.50",
                "direction": "IN",
                "description": "EDC SETTLEMENT KBANK",
                "_tx_id": "ab12cd34ef56",
            },
            0,
        )
        self.assertEqual(issues, [])
        self.assertEqual(row.day, date(2026, 5, 16))
        self.assertEqual(row.amount, Decimal("10539.50"))
        self.assertEqual(row.tx_id, "ab12cd34ef56")
        self.assertTrue(row.usable)

    def test_row_hash_accepted_as_fingerprint(self):
        row, _ = BankCredit.adapt({"date": "2026-05-16", "deposit": "5.00", "row_hash": "x1"}, 0)
        self.assertEqual(row.tx_id, "x1")
        self.assertEqual(row.amount, Decimal("5.00"))

    def test_out_direction_rejected(self):
        row, issues = BankCredit.adapt(
            {"tx_date": "2026-05-16", "amount": "99.00", "direction": "OUT"}, 0
        )
        self.assertIn(model.ISSUE_NOT_CREDIT, issues)
        self.assertFalse(row.usable)

    def test_amount_unresolved(self):
        row, issues = BankCredit.adapt({"tx_date": "2026-05-16"}, 0)
        self.assertIn(model.ISSUE_AMOUNT, issues)
        self.assertFalse(row.usable)


class TestSalesDoc(unittest.TestCase):
    def test_adapt_classify_money_shape(self):
        # classify._money_fields 的 money 快照原样喂进来,零翻译。
        row, issues = SalesDoc.adapt(
            {
                "subtotal": "1,000.00",
                "vat": "70.00",
                "total_amount": "1,070.00",
                "invoice_number": "INV-001",
                "seller_tax": "0105561234567",
                "invoice_date": "15/05/2569",
                "vendor": "SISTER MAKEUP",
            },
            0,
        )
        self.assertEqual(issues, [])
        self.assertEqual(row.day, date(2026, 5, 15))
        self.assertEqual(row.gross, Decimal("1070.00"))
        self.assertEqual(row.invoice_no, "INV-001")
        self.assertTrue(row.usable)

    def test_gross_falls_back_to_net_plus_vat(self):
        row, issues = SalesDoc.adapt(
            {"subtotal": "100.00", "vat": "7.00", "invoice_date": "2026-05-15"}, 0
        )
        self.assertEqual(issues, [])
        self.assertEqual(row.gross, Decimal("107.00"))

    def test_all_amounts_missing_is_named(self):
        row, issues = SalesDoc.adapt({"invoice_date": "2026-05-15", "invoice_number": "X1"}, 0)
        self.assertIsNone(row.gross)
        self.assertFalse(row.usable)
        self.assertIn(model.ISSUE_GROSS, issues)


if __name__ == "__main__":
    unittest.main()
