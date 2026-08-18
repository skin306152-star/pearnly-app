# -*- coding: utf-8 -*-

import unittest
from unittest import mock

from services.erp.mrerp_dms_client_base import DMSClientError
from services.erp.mrerp_dms_company_banks import (
    company_bank_label,
    fetch_company_banks,
    normalize_company_bank_rows,
    validate_company_bank_payments,
)


class _Locator:
    def __init__(self, page, selector):
        self.page = page
        self.selector = selector

    def wait_for(self, **kwargs):
        self.page.waits += 1
        if self.page.waits <= self.page.fail_waits:
            raise TimeoutError("not ready")

    def evaluate_all(self, script):
        return self.page.rows


class _Page:
    def __init__(self, rows, fail_waits=0):
        self.rows = rows
        self.fail_waits = fail_waits
        self.waits = 0
        self.gotos = []
        self.reloads = 0
        self.timeouts = []

    def goto(self, url, **kwargs):
        self.gotos.append(url)

    def reload(self, **kwargs):
        self.reloads += 1

    def expect_response(self, predicate, **kwargs):
        return mock.MagicMock()

    def wait_for_timeout(self, timeout):
        self.timeouts.append(timeout)

    def locator(self, selector):
        return _Locator(self, selector)


class _Adapter:
    base_url = "https://example.test/dms/"

    def __init__(self, page):
        self._page = page


class CompanyBankTests(unittest.TestCase):
    def test_browser_fetch_reloads_once_then_reads_rows(self):
        page = _Page([{"id": "1", "details": ["SCB", "SCB"]}], fail_waits=1)
        self.assertEqual(fetch_company_banks(_Adapter(page)), [["1", "SCB", "SCB"]])
        self.assertEqual(page.gotos, ["https://example.test/dms/bank/view.php"])
        self.assertEqual(page.reloads, 1)
        self.assertEqual(page.timeouts, [100])

    def test_normalizes_page_rows_and_labels(self):
        rows = normalize_company_bank_rows(
            [
                {"id": "1", "details": ["SCB", "SCB"]},
                {"id": "2", "details": ["KBANK", "บัญชีรับจอง"]},
                {"id": "", "details": ["dirty"]},
            ]
        )
        self.assertEqual(rows, [["1", "SCB", "SCB"], ["2", "KBANK", "บัญชีรับจอง"]])
        self.assertEqual(company_bank_label(rows[0]), "SCB")
        self.assertEqual(company_bank_label(rows[1]), "KBANK · บัญชีรับจอง")

    def test_submit_revalidates_selected_bank(self):
        payments = [
            {
                "channel": "transfer",
                "amount": "1500.00",
                "extra": {"src": "customer", "dst_id": "1", "dst": "old"},
            }
        ]
        with mock.patch(
            "services.erp.mrerp_dms_company_banks.fetch_company_banks",
            return_value=[["1", "SCB", "SCB"]],
        ):
            out = validate_company_bank_payments(object(), payments)
        self.assertEqual(out[0]["extra"]["dst"], "SCB")
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
