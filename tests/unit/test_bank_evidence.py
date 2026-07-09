# -*- coding: utf-8 -*-
"""F6 银行佐证单测(services/erp/express_push/bank_evidence.py)。

钉死:金额精确 2dp + 方向(purchase→OUT / sales→IN)+ 日期 ±7 天窗才算命中;
表不存在/查询异常一律吞成空表(load_bank_index 绝不让票据推送因银行表缺失而炸)。
"""

from __future__ import annotations

import unittest
from unittest import mock

from services.erp.express_push.bank_evidence import (
    bank_paid_match,
    load_bank_index,
    load_bank_index_for_histories,
    load_bank_index_for_history,
)


class BankPaidMatchTests(unittest.TestCase):
    def test_exact_amount_within_window_matches(self):
        idx = [{"tx_date": "2026-07-05", "direction": "OUT", "amount": "107.00"}]
        self.assertTrue(
            bank_paid_match(idx, amount="107.00", invoice_date="2026-07-01", direction="purchase")
        )

    def test_wrong_direction_does_not_match(self):
        idx = [{"tx_date": "2026-07-05", "direction": "IN", "amount": "107.00"}]
        self.assertFalse(
            bank_paid_match(idx, amount="107.00", invoice_date="2026-07-01", direction="purchase")
        )

    def test_sales_direction_wants_in(self):
        idx = [{"tx_date": "2026-07-05", "direction": "IN", "amount": "107.00"}]
        self.assertTrue(
            bank_paid_match(idx, amount="107.00", invoice_date="2026-07-01", direction="sales")
        )

    def test_amount_mismatch_does_not_match(self):
        idx = [{"tx_date": "2026-07-05", "direction": "OUT", "amount": "108.00"}]
        self.assertFalse(
            bank_paid_match(idx, amount="107.00", invoice_date="2026-07-01", direction="purchase")
        )

    def test_outside_window_does_not_match(self):
        idx = [{"tx_date": "2026-07-20", "direction": "OUT", "amount": "107.00"}]  # 19 天外
        self.assertFalse(
            bank_paid_match(idx, amount="107.00", invoice_date="2026-07-01", direction="purchase")
        )

    def test_boundary_seven_days_matches(self):
        idx = [{"tx_date": "2026-07-08", "direction": "OUT", "amount": "107.00"}]  # 恰 7 天
        self.assertTrue(
            bank_paid_match(idx, amount="107.00", invoice_date="2026-07-01", direction="purchase")
        )

    def test_unparseable_amount_returns_false(self):
        idx = [{"tx_date": "2026-07-05", "direction": "OUT", "amount": "107.00"}]
        self.assertFalse(
            bank_paid_match(idx, amount="garbage", invoice_date="2026-07-01", direction="purchase")
        )

    def test_unparseable_date_returns_false(self):
        idx = [{"tx_date": "2026-07-05", "direction": "OUT", "amount": "107.00"}]
        self.assertFalse(
            bank_paid_match(idx, amount="107.00", invoice_date="not-a-date", direction="purchase")
        )

    def test_empty_index_returns_false(self):
        self.assertFalse(
            bank_paid_match([], amount="107.00", invoice_date="2026-07-01", direction="purchase")
        )

    def test_unknown_direction_returns_false(self):
        idx = [{"tx_date": "2026-07-05", "direction": "OUT", "amount": "107.00"}]
        self.assertFalse(
            bank_paid_match(idx, amount="107.00", invoice_date="2026-07-01", direction="refund")
        )

    def test_dd_mm_yyyy_invoice_date_matches(self):
        # OCR 票面常见记法(非 ISO)· common.parse_invoice_date 双格式解析核共用后须命中。
        idx = [{"tx_date": "2026-07-05", "direction": "OUT", "amount": "107.00"}]
        self.assertTrue(
            bank_paid_match(idx, amount="107.00", invoice_date="02/07/2026", direction="purchase")
        )


class LoadBankIndexTests(unittest.TestCase):
    def test_missing_user_id_returns_empty_without_query(self):
        self.assertEqual(load_bank_index(None, "2026-07-01", "2026-07-10"), [])

    def test_missing_date_window_returns_empty_without_query(self):
        self.assertEqual(load_bank_index("u1", None, None), [])

    def test_table_missing_swallowed_to_empty_list(self):
        with mock.patch("core.db.get_cursor_rls", side_effect=RuntimeError("relation missing")):
            self.assertEqual(load_bank_index("u1", "2026-07-01", "2026-07-10"), [])

    def test_query_result_passed_through(self):
        rows = [{"tx_date": "2026-07-05", "direction": "OUT", "amount": "107.00"}]

        class _Cur:
            def execute(self, *a, **kw):
                pass

            def fetchall(self):
                return rows

        class _Ctx:
            def __enter__(self):
                return _Cur()

            def __exit__(self, *a):
                return False

        with mock.patch("core.db.get_cursor_rls", return_value=_Ctx()):
            got = load_bank_index("u1", "2026-07-01", "2026-07-10")
        self.assertEqual(got, rows)


class LoadBankIndexForHistoriesTests(unittest.TestCase):
    def test_no_dates_returns_empty_without_query(self):
        with mock.patch("services.erp.express_push.bank_evidence.load_bank_index") as mocked:
            got = load_bank_index_for_histories([{"fields": {}}], "u1")
        self.assertEqual(got, [])
        mocked.assert_not_called()

    def test_window_spans_min_to_max_invoice_date(self):
        flats = [
            {"invoice_date": "2026-07-01", "fields": {}},
            {"fields": {"date": "2026-07-10"}},
        ]
        with mock.patch(
            "services.erp.express_push.bank_evidence.load_bank_index", return_value=[]
        ) as mocked:
            load_bank_index_for_histories(flats, "u1")
        mocked.assert_called_once_with("u1", "2026-06-24", "2026-07-17")

    def test_single_history_helper_delegates(self):
        with mock.patch(
            "services.erp.express_push.bank_evidence.load_bank_index_for_histories",
            return_value=[],
        ) as mocked:
            load_bank_index_for_history({"invoice_date": "2026-07-01"}, "u1")
        mocked.assert_called_once_with([{"invoice_date": "2026-07-01"}], "u1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
