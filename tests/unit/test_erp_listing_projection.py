from __future__ import annotations

import asyncio
import unittest
from unittest import mock

from routes import erp_listing_routes as routes
from services.erp import mrerp_projection_listing as listing


class ErpListingProjectionTests(unittest.TestCase):
    def setUp(self):
        self.user = {
            "id": "user-1",
            "tenant_id": "tenant-1",
            "entry": "erp",
            "role": "owner",
            "plan": "pro",
        }
        self.endpoint = {
            "id": "endpoint-1",
            "adapter": "mrerp",
            "enabled": True,
            "config": {},
        }

    @staticmethod
    def _projection(kind: str):
        attributes = (
            {"category_code": "CAT", "category_name": "New category"}
            if kind == "products"
            else {"type_name": "Retail", "prefix": "ACME"}
        )
        return {
            "ok": True,
            "error_code": None,
            "data": {
                "freshness": {"status": "fresh", "observed_at": "2026-09-02T08:00:00Z"},
                "snapshot": {
                    "revision": 7,
                    "master_revision": 4,
                    "masters": {
                        kind: [
                            {
                                "source_id": "NEW-01",
                                "label": "New ERP option",
                                "attributes": attributes,
                            }
                        ]
                    },
                },
            },
        }

    def _patches(self, result):
        return (
            mock.patch.object(routes, "get_current_user_from_request", return_value=self.user),
            mock.patch.object(routes, "require_erp_portal"),
            mock.patch.object(routes, "_check_push_access"),
            mock.patch.object(routes, "_projection_endpoint", return_value=self.endpoint),
            mock.patch.object(routes, "erp_target_projection_enabled_for", return_value=True),
            mock.patch.object(listing, "refresh_mrerp_projection", return_value=result),
            mock.patch.object(routes, "_fetch_listing_with_retry"),
        )

    def test_saved_customer_endpoint_uses_fresh_projection_not_ttl_cache(self):
        auth, portal, access, endpoint, flag, refresh, legacy = self._patches(
            self._projection("customers")
        )
        with auth, portal, access, endpoint, flag, refresh as refresh_mock, legacy as legacy_mock:
            result = asyncio.run(routes.erp_endpoint_customers("endpoint-1", mock.Mock()))
        self.assertTrue(result["ok"])
        self.assertFalse(result["cached"])
        self.assertEqual(result["customers"][0]["code"], "NEW-01")
        self.assertEqual(result["master_revision"], 4)
        refresh_mock.assert_called_once()
        legacy_mock.assert_not_called()

    def test_saved_product_endpoint_runs_projection_off_event_loop(self):
        def refresh(**_kwargs):
            with self.assertRaises(RuntimeError):
                asyncio.get_running_loop()
            return self._projection("products")

        auth, portal, access, endpoint, flag, _, legacy = self._patches(None)
        with (
            auth,
            portal,
            access,
            endpoint,
            flag,
            mock.patch.object(listing, "refresh_mrerp_projection", side_effect=refresh),
            legacy as legacy_mock,
        ):
            result = asyncio.run(routes.erp_endpoint_products("endpoint-1", mock.Mock()))
        self.assertEqual(result["products"][0]["category_code"], "CAT")
        legacy_mock.assert_not_called()

    def test_failed_refresh_returns_stale_rows_without_claiming_success(self):
        stale = self._projection("customers")
        stale["ok"] = False
        stale["error_code"] = "ERR_TECHNICAL"
        auth, portal, access, endpoint, flag, refresh, legacy = self._patches(stale)
        with auth, portal, access, endpoint, flag, refresh, legacy:
            result = asyncio.run(routes.erp_endpoint_customers("endpoint-1", mock.Mock()))
        self.assertFalse(result["ok"])
        self.assertTrue(result["stale"])
        self.assertEqual(result["error_code"], "ERR_TECHNICAL")
        self.assertEqual(len(result["customers"]), 1)


if __name__ == "__main__":
    unittest.main()
