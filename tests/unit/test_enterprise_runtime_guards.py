import unittest
from unittest.mock import patch

from services.ocr.enterprise_local.result import check_document, reconstruct
from services.ocr.enterprise_quota import wait_for_slot
from services.ocr.layer1_base import Layer1QuotaError


class EnterpriseGuardsTest(unittest.TestCase):
    def test_gl_uncheckable_chain_cannot_pass_zero_violations(self):
        doc = {
            "closing_balance": "10",
            "entries": [{"page": "1", "transaction_date": "2026-01-01", "balance": "10"}],
        }
        self.assertIn("balance_chain_incomplete_or_broken", check_document(doc, "gl", 1))

    def test_balanced_subset_cannot_hide_missing_page(self):
        doc = {
            "opening_balance": "0",
            "closing_balance": "10",
            "entries": [
                {
                    "page": "1",
                    "transaction_date": "2026-01-01",
                    "balance": "10",
                    "amount": "10",
                    "direction": "deposit",
                    "deposit": "10",
                }
            ],
        }
        self.assertEqual([], check_document(doc, "bank", 1))
        self.assertIn("transaction_page_coverage_unverified", check_document(doc, "bank", 2))

    def test_page_count_fails_before_parsing(self):
        with self.assertRaisesRegex(ValueError, "page count"):
            reconstruct([{"document": {"text": "", "pages": []}}], "bank", expected_pages=1)

    @patch("services.ocr.enterprise_quota.try_reserve", return_value=True)
    def test_quota_shared_by_processor_type(self, reserve):
        with patch.dict("os.environ", {"ENTERPRISE_OCR_REQUESTS_PER_MINUTE": "9"}):
            wait_for_slot("projects/p/locations/r/processors/one")
            wait_for_slot("projects/p/locations/r/processors/two")
        self.assertEqual(reserve.call_args_list[0], reserve.call_args_list[1])
        self.assertEqual("ocr:documentai:p:r:OCR_PROCESSOR", reserve.call_args.args[0])

    @patch("services.ocr.enterprise_quota.try_reserve", return_value=False)
    def test_quota_timeout_is_not_unlimited_fallback(self, reserve):
        with self.assertRaises(Layer1QuotaError):
            wait_for_slot("projects/p/locations/r/processors/one", timeout_s=0)

    @patch("services.ocr.enterprise_quota.try_reserve", side_effect=RuntimeError("db"))
    def test_database_failure_is_closed(self, reserve):
        with self.assertRaisesRegex(RuntimeError, "db"):
            wait_for_slot("projects/p/locations/r/processors/one")


if __name__ == "__main__":
    unittest.main()
