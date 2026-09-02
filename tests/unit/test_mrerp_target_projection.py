from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest import mock

from services.erp import mrerp_target_projection as projection


class MRErpTargetProjectionTests(unittest.TestCase):
    def setUp(self):
        self.endpoint = {
            "id": "33333333-3333-4333-8333-333333333333",
            "adapter": "mrerp",
            "config": {
                "username_enc": "encrypted-user",
                "password_enc": "encrypted-password",
                "comidyear": "6",
                "seldb": "1",
            },
        }
        self.observed_at = datetime(2026, 9, 2, 8, 0, tzinfo=timezone.utc)
        self.account_result = {
            "ok": True,
            "companies": [
                {"label": "Current", "comidyear": "6", "seldb": "1"},
                {"label": "New account", "comidyear": "15", "seldb": "2"},
            ],
        }
        self.product_result = {
            "ok": True,
            "products": [
                {
                    "code": "P-01",
                    "name": "New product",
                    "category_code": "CAT",
                    "category_name": "Category",
                }
            ],
        }
        self.customer_result = {
            "ok": True,
            "customers": [
                {"code": "C-01", "name": "New customer", "type_name": "Retail", "prefix": ""}
            ],
        }

    def _patches(self):
        return (
            mock.patch.object(projection, "_claim_endpoint_tenant"),
            mock.patch.object(projection, "test_mrerp_endpoint", return_value=self.account_result),
            mock.patch.object(projection, "list_mrerp_products", return_value=self.product_result),
            mock.patch.object(
                projection, "list_mrerp_customers", return_value=self.customer_result
            ),
            mock.patch.object(
                projection,
                "publish_projection",
                side_effect=[
                    {"published": True, "revision": 2},
                    {"published": True, "revision": 4},
                ],
            ),
            mock.patch.object(projection, "load_state", return_value={"snapshot": {"revision": 4}}),
        )

    def test_refresh_publishes_catalog_then_atomic_selected_account_snapshot(self):
        claim, accounts, products, customers, publish, load = self._patches()
        with (
            claim as claim_mock,
            accounts,
            products as product_mock,
            customers as customer_mock,
            publish as publish_mock,
            load,
        ):
            result = projection.refresh_mrerp_projection(
                tenant_id="tenant-a",
                user_id="user-a",
                endpoint=self.endpoint,
                account_set_key="15:2",
                observed_at=self.observed_at,
            )

        self.assertTrue(result["ok"])
        claim_mock.assert_called_once_with(tenant_id="tenant-a", endpoint_id=self.endpoint["id"])
        self.assertEqual(product_mock.call_args.args[0]["comidyear"], "15")
        self.assertEqual(customer_mock.call_args.args[0]["seldb"], "2")
        self.assertEqual(publish_mock.call_count, 2)
        catalog = publish_mock.call_args_list[0].kwargs["observation"]
        selected = publish_mock.call_args_list[1].kwargs["observation"]
        self.assertNotIn("account_set_key", catalog)
        self.assertEqual(selected["account_set_key"], "15:2")
        self.assertEqual(selected["masters"]["products"][0]["source_id"], "P-01")
        self.assertEqual(selected["masters"]["customers"][0]["label"], "New customer")
        fields = {field["key"]: field for field in selected["form_schema"]["fields"]}
        self.assertEqual(fields["product_id"]["options_source"], "products")
        self.assertEqual(fields["supplier_id"]["type"], "unsupported")

    def test_master_rows_keep_first_value_for_duplicate_erp_code(self):
        rows = [
            {"code": "P-01", "name": "First", "category_code": "A"},
            {"code": "P-01", "name": "Duplicate", "category_code": "B"},
            {"code": "P-02", "name": "Second", "category_code": "A"},
        ]

        projected = projection._master_rows(rows, kind="products")

        self.assertEqual([row["source_id"] for row in projected], ["P-01", "P-02"])
        self.assertEqual(projected[0]["label"], "First")
        self.assertEqual(projected[0]["attributes"]["category_code"], "A")

    def test_account_catalog_refresh_never_fetches_heavy_master_lists(self):
        claim, accounts, products, customers, publish, load = self._patches()
        with (
            claim,
            accounts,
            products as product_mock,
            customers as customer_mock,
            publish as publish_mock,
            load,
        ):
            result = projection.refresh_mrerp_account_catalog(
                tenant_id="tenant-a",
                user_id="user-a",
                endpoint=self.endpoint,
                observed_at=self.observed_at,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(len(result["account_sets"]), 2)
        product_mock.assert_not_called()
        customer_mock.assert_not_called()
        publish_mock.assert_called_once()

    def test_transient_product_failure_retries_once_then_keeps_stale_snapshot(self):
        stale = {"snapshot": {"revision": 3}, "freshness": {"status": "offline"}}
        with (
            mock.patch.object(projection, "_claim_endpoint_tenant"),
            mock.patch.object(projection, "test_mrerp_endpoint", return_value=self.account_result),
            mock.patch.object(
                projection,
                "list_mrerp_products",
                side_effect=[
                    {"ok": False, "error_code": "ERR_TECHNICAL"},
                    {"ok": False, "error_code": "ERR_TECHNICAL"},
                ],
            ) as products,
            mock.patch.object(projection, "list_mrerp_customers") as customers,
            mock.patch.object(
                projection, "publish_projection", return_value={"published": True, "revision": 2}
            ) as publish,
            mock.patch.object(projection, "record_refresh_state") as record,
            mock.patch.object(projection, "load_state", return_value=stale),
            mock.patch.object(projection.time, "sleep") as sleep,
        ):
            result = projection.refresh_mrerp_projection(
                tenant_id="tenant-a",
                user_id="user-a",
                endpoint=self.endpoint,
                observed_at=self.observed_at,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["data"], stale)
        self.assertEqual(products.call_count, 2)
        customers.assert_not_called()
        self.assertEqual(publish.call_count, 1)
        sleep.assert_called_once_with(2.0)
        self.assertEqual(record.call_args.kwargs["status"], "offline")
        self.assertEqual(record.call_args.kwargs["account_set_key"], "6:1")

    def test_unknown_account_set_updates_catalog_but_does_not_fetch_masters(self):
        with (
            mock.patch.object(projection, "_claim_endpoint_tenant"),
            mock.patch.object(projection, "test_mrerp_endpoint", return_value=self.account_result),
            mock.patch.object(projection, "list_mrerp_products") as products,
            mock.patch.object(projection, "list_mrerp_customers") as customers,
            mock.patch.object(
                projection, "publish_projection", return_value={"published": True, "revision": 2}
            ) as publish,
            mock.patch.object(projection, "record_refresh_state") as record,
            mock.patch.object(projection, "load_state", return_value=None),
        ):
            result = projection.refresh_mrerp_projection(
                tenant_id="tenant-a",
                user_id="user-a",
                endpoint=self.endpoint,
                account_set_key="404:1",
                observed_at=self.observed_at,
            )

        self.assertEqual(result["error_code"], "ERR_ACCOUNT_SET_UNAVAILABLE")
        self.assertEqual(publish.call_count, 1)
        products.assert_not_called()
        customers.assert_not_called()
        self.assertEqual(record.call_args.kwargs["account_set_key"], "404:1")

    def test_non_mrerp_endpoint_is_rejected_before_external_calls(self):
        endpoint = {**self.endpoint, "adapter": "express"}
        with mock.patch.object(projection, "test_mrerp_endpoint") as accounts:
            with self.assertRaises(projection.MRErpProjectionError) as raised:
                projection.refresh_mrerp_projection(
                    tenant_id="tenant-a", user_id="user-a", endpoint=endpoint
                )
        self.assertEqual(raised.exception.code, "erp.target_projection_adapter_mismatch")
        accounts.assert_not_called()


if __name__ == "__main__":
    unittest.main()
