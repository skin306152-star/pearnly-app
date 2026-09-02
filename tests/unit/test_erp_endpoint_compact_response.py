from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace
from unittest import mock

from routes import erp_endpoints_routes
from services.erp.endpoint_config import strip_endpoint_for_response


def _express_endpoint() -> dict:
    return {
        "id": "express-1",
        "adapter": "express",
        "config": {
            "agent_token_hash": "secret-hash",
            "token": "secret-token-value",
            "account_set": r"S:\\2569\\69EXP\\TEST",
            "account_dir": r"S:\\2569\\69EXP\\TEST",
            "express_root": r"S:\\2569\\69EXP",
            "account_set_label": "TEST",
            "account_company": "Pearnly Co., Ltd.",
            "reported_account_sets": [{"path": f"account-{index}"} for index in range(50)],
            "reported_accounts": [{"code": str(index)} for index in range(50)],
            "reported_products": [{"code": str(index)} for index in range(50)],
            "reported_customers": [{"code": str(index)} for index in range(50)],
            "reported_stock_acc_groups": [{"code": str(index)} for index in range(50)],
            "reported_catalog": {"products": [{"code": "P1"}]},
            "reported_future_directory": [{"id": str(index)} for index in range(50)],
            "reported_protocol_version": 2,
        },
    }


class EndpointResponseShapeTests(unittest.TestCase):
    def test_compact_removes_catalogs_and_preserves_express_default(self):
        endpoint = _express_endpoint()

        result = strip_endpoint_for_response(endpoint, compact=True)

        config = result["config"]
        self.assertTrue(
            {
                "account_set",
                "account_dir",
                "express_root",
                "account_set_label",
                "account_company",
            }
            <= set(config)
        )
        self.assertFalse(
            set(config)
            & {
                "reported_account_sets",
                "reported_accounts",
                "reported_products",
                "reported_customers",
                "reported_stock_acc_groups",
                "reported_catalog",
                "reported_future_directory",
            }
        )
        self.assertEqual(config["reported_protocol_version"], 2)
        self.assertNotIn("agent_token_hash", config)
        self.assertNotEqual(config["token"], "secret-token-value")
        self.assertIn("reported_account_sets", endpoint["config"])

    def test_compact_preserves_mrerp_default(self):
        endpoint = {
            "id": "mrerp-1",
            "adapter": "mrerp",
            "config": {
                "comidyear": "15",
                "seldb": "2",
                "account_set_label": "TEST2020",
                "reported_products": [{"code": "P1"}],
            },
        }

        config = strip_endpoint_for_response(endpoint, compact=True)["config"]

        self.assertEqual(config["comidyear"], "15")
        self.assertEqual(config["seldb"], "2")
        self.assertEqual(config["account_set_label"], "TEST2020")
        self.assertNotIn("reported_products", config)

    def test_default_response_keeps_catalogs_for_compatibility(self):
        endpoint = _express_endpoint()

        config = strip_endpoint_for_response(endpoint)["config"]

        for key in (
            "reported_account_sets",
            "reported_accounts",
            "reported_products",
            "reported_customers",
            "reported_stock_acc_groups",
            "reported_catalog",
            "reported_future_directory",
        ):
            self.assertIn(key, config)


class EndpointListCompactQueryTests(unittest.TestCase):
    def _list(self, *, compact: bool):
        user = {"id": "owner-1", "entry": "cowork", "role": "owner"}
        with (
            mock.patch.object(
                erp_endpoints_routes, "get_current_user_from_request", return_value=user
            ),
            mock.patch.object(erp_endpoints_routes, "require_erp_portal"),
            mock.patch.object(erp_endpoints_routes, "_check_push_access"),
            mock.patch.object(
                erp_endpoints_routes.shared_express_access,
                "is_shared_endpoint_read",
                return_value=False,
            ),
            mock.patch.object(
                erp_endpoints_routes.db,
                "list_erp_endpoints",
                return_value=[_express_endpoint()],
            ),
        ):
            return asyncio.run(
                erp_endpoints_routes.erp_endpoints_list(
                    SimpleNamespace(headers={}), compact=compact
                )
            )

    def test_compact_query_omits_catalogs(self):
        with mock.patch("services.erp.target_projection_store.load_state") as load_state:
            config = self._list(compact=True)["items"][0]["config"]
        self.assertNotIn("reported_account_sets", config)
        self.assertEqual(config["account_set_label"], "TEST")
        load_state.assert_not_called()

    def test_default_query_is_compatible(self):
        config = self._list(compact=False)["items"][0]["config"]
        self.assertIn("reported_account_sets", config)


if __name__ == "__main__":
    unittest.main()
