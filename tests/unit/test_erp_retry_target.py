from __future__ import annotations

import unittest

from services.erp.retry_target import endpoint_for_retry, request_after_retry


class ErpRetryTargetTests(unittest.TestCase):
    def test_mrerp_retry_reuses_logged_year_and_account(self):
        endpoint = {
            "adapter": "mrerp",
            "config": {"comidyear": "6", "seldb": "1", "username_enc": "kept"},
        }
        projected = endpoint_for_retry(
            endpoint,
            {"source": "line_erp", "account_set": "7:2"},
        )

        self.assertEqual(projected["config"]["comidyear"], "7")
        self.assertEqual(projected["config"]["seldb"], "2")
        self.assertEqual(projected["config"]["username_enc"], "kept")
        self.assertEqual(endpoint["config"]["comidyear"], "6")

    def test_invalid_logged_choice_does_not_mutate_endpoint(self):
        endpoint = {"adapter": "mrerp", "config": {"comidyear": "6", "seldb": "1"}}
        self.assertIs(endpoint_for_retry(endpoint, {"account_set": "broken"}), endpoint)

    def test_retry_result_preserves_line_origin(self):
        merged = request_after_retry(
            {"source": "cowork_line", "account_set": "7:2"},
            {"adapter": "mrerp", "account_set": "7:2"},
        )
        self.assertEqual(merged["source"], "cowork_line")


if __name__ == "__main__":
    unittest.main()
