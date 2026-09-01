# -*- coding: utf-8 -*-

import unittest
from unittest import mock

from services.erp.mrerp_dms_client_base import DMSClientError
from services.erp.mrerp_dms_company_banks import (
    company_bank_label,
    company_bank_payment_extra,
    fetch_company_banks,
    normalize_company_bank_rows,
    validate_company_bank_payments,
)


class _Client:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def _bshsd_all(self, elemname, **kwargs):
        self.calls.append((elemname, kwargs))
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class _Adapter:
    def __init__(self, results):
        self.client = _Client(results)

    def _client(self):
        return self.client


class CompanyBankTests(unittest.TestCase):
    def test_typeahead_fetch_retries_once_then_reads_complete_rows(self):
        adapter = _Adapter([None, [[1, "SCB", "SCB", "ระยอง", "1234567890123"]]])
        self.assertEqual(
            fetch_company_banks(adapter),
            [["1", "SCB", "SCB", "ระยอง", "1234567890123"]],
        )
        self.assertEqual(
            adapter.client.calls,
            [
                ("txtbanknametfmon", {"page_size": 200}),
                ("txtbanknametfmon", {"page_size": 200}),
            ],
        )

    def test_normalizes_page_rows_and_labels(self):
        rows = normalize_company_bank_rows(
            [
                {"id": "1", "details": ["SCB", "SCB"]},
                {"id": "2", "details": ["KBANK", "บัญชีรับจอง"]},
                {"id": "", "details": ["dirty"]},
            ]
        )
        self.assertEqual(
            rows,
            [["1", "SCB", "SCB", "", ""], ["2", "KBANK", "บัญชีรับจอง", "", ""]],
        )
        self.assertEqual(company_bank_label(rows[0]), "SCB")
        self.assertEqual(company_bank_label(rows[1]), "KBANK · บัญชีรับจอง")

    def test_label_and_payment_extra_include_account_and_branch(self):
        row = ["2", "BBL", "BBL", "ระยอง", "Bbl 987654321"]
        self.assertEqual(company_bank_label(row), "BBL · Bbl 987654321 · ระยอง")
        self.assertEqual(
            company_bank_payment_extra(row),
            {
                "dst_id": "2",
                "dst": "BBL · Bbl 987654321 · ระยอง",
                "dst_bank_id": "2",
                "dst_bank_name": "BBL",
                "dst_branch_name": "ระยอง",
                "dst_account_no": "Bbl 987654321",
            },
        )

    def test_submit_revalidates_selected_bank(self):
        payments = [
            {
                "channel": "transfer",
                "amount": "1500.00",
                "extra": {
                    "src_bank_name": "KBank",
                    "src_account_no": "123",
                    "dst_id": "1",
                    "dst": "old",
                },
            }
        ]
        with mock.patch(
            "services.erp.mrerp_dms_company_banks.fetch_company_banks",
            return_value=[["1", "SCB", "SCB", "ระยอง", "1234567890123"]],
        ):
            out = validate_company_bank_payments(object(), payments)
        self.assertEqual(out[0]["extra"]["dst"], "SCB · 1234567890123 · ระยอง")
        self.assertEqual(out[0]["extra"]["dst_account_no"], "1234567890123")
        self.assertEqual(out[0]["extra"]["dst_bank_id"], "1")
        self.assertEqual(payments[0]["extra"]["dst"], "old")

    def test_submit_rejects_removed_or_legacy_free_text_bank(self):
        payment = {"channel": "transfer", "amount": "1.00", "extra": {"dst": "SCB"}}
        with mock.patch(
            "services.erp.mrerp_dms_company_banks.fetch_company_banks", return_value=[]
        ):
            with self.assertRaises(DMSClientError) as ctx:
                validate_company_bank_payments(object(), [payment])
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNMATCHED")


if __name__ == "__main__":
    unittest.main()
