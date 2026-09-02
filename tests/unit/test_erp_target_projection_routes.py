from __future__ import annotations

import asyncio
import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes import erp_target_projection_routes as routes


class TargetProjectionRouteTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(routes.router)
        self.client = TestClient(app)
        self.user = {
            "id": "11111111-1111-1111-1111-111111111111",
            "tenant_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "entry": "erp",
            "role": "owner",
        }

    def _patches(self, *, enabled=True, state=None):
        if state is None:
            state = {"snapshot": None, "freshness": {"status": "offline"}}
        return (
            mock.patch.object(routes, "require_perm", return_value=self.user),
            mock.patch.object(routes, "erp_target_projection_enabled_for", return_value=enabled),
            mock.patch.object(routes, "_endpoint_visible", return_value=True),
            mock.patch.object(routes, "load_state", return_value=state),
        )

    def test_disabled_flag_hides_the_route_contract(self):
        auth, flag, visible, load = self._patches(enabled=False)
        with auth, flag, visible, load as load_mock:
            response = self.client.get(
                "/api/erp/endpoints/33333333-3333-4333-8333-333333333333/target-projection"
            )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "erp.target_projection_unavailable")
        load_mock.assert_not_called()

    def test_enabled_route_returns_projection_and_requested_entities(self):
        state = {"snapshot": {"revision": 3}, "freshness": {"status": "fresh"}}
        auth, flag, visible, load = self._patches(state=state)
        with auth, flag, visible, load as load_mock:
            response = self.client.get(
                "/api/erp/endpoints/33333333-3333-4333-8333-333333333333/target-projection",
                params={"account_set_key": "2026", "entity_types": "products,accounts"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True, "data": state})
        self.assertEqual(load_mock.call_args.kwargs["entity_types"], ("products", "accounts"))
        self.assertEqual(load_mock.call_args.kwargs["account_set_key"], "2026")

    def test_sync_auth_and_store_run_off_the_async_loop(self):
        def require_off_loop(*_args, **_kwargs):
            with self.assertRaises(RuntimeError):
                asyncio.get_running_loop()
            return self.user

        def load_off_loop(**_kwargs):
            with self.assertRaises(RuntimeError):
                asyncio.get_running_loop()
            return {"snapshot": None, "freshness": {"status": "offline"}}

        with (
            mock.patch.object(routes, "require_perm", side_effect=require_off_loop),
            mock.patch.object(routes, "erp_target_projection_enabled_for", return_value=True),
            mock.patch.object(routes, "_endpoint_visible", return_value=True),
            mock.patch.object(routes, "load_state", side_effect=load_off_loop),
        ):
            response = self.client.get(
                "/api/erp/endpoints/33333333-3333-4333-8333-333333333333/target-projection"
            )
        self.assertEqual(response.status_code, 200)

    def test_refresh_enqueues_collector_off_the_async_loop(self):
        endpoint = {"id": "33333333-3333-4333-8333-333333333333", "adapter": "mrerp"}

        def refresh_off_loop(**kwargs):
            with self.assertRaises(RuntimeError):
                asyncio.get_running_loop()
            self.assertEqual(kwargs["account_set_key"], "15:2")
            return {"request_id": "refresh-1", "status": "requested"}

        with (
            mock.patch.object(routes, "require_perm", return_value=self.user),
            mock.patch.object(routes, "erp_target_projection_enabled_for", return_value=True),
            mock.patch.object(routes, "_resolve_endpoint", return_value=endpoint),
            mock.patch.object(
                routes.target_refresh, "request_refresh", side_effect=refresh_off_loop
            ),
            mock.patch.object(routes.target_refresh, "process_mrerp_request", return_value=True),
        ):
            response = self.client.post(
                "/api/erp/endpoints/33333333-3333-4333-8333-333333333333/target-projection/refresh",
                params={"account_set_key": "15:2"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertEqual(response.json()["refresh"]["request_id"], "refresh-1")

    def test_refresh_supports_express_without_running_collector_in_request(self):
        endpoint = {
            "id": "33333333-3333-4333-8333-333333333333",
            "adapter": "express",
            "agent_version": "1.1.72",
        }
        with (
            mock.patch.object(routes, "require_perm", return_value=self.user),
            mock.patch.object(routes, "erp_target_projection_enabled_for", return_value=True),
            mock.patch.object(routes, "_resolve_endpoint", return_value=endpoint),
            mock.patch.object(
                routes.target_refresh,
                "request_refresh",
                return_value={"request_id": "refresh-2", "status": "requested"},
            ),
            mock.patch.object(routes.target_refresh, "process_mrerp_request") as process,
        ):
            response = self.client.post(
                "/api/erp/endpoints/33333333-3333-4333-8333-333333333333/target-projection/refresh"
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["refresh"]["request_id"], "refresh-2")
        process.assert_not_called()

    def test_refresh_requires_express_companion_protocol(self):
        endpoint = {
            "id": "33333333-3333-4333-8333-333333333333",
            "adapter": "express",
            "agent_version": "1.1.71",
        }
        with (
            mock.patch.object(routes, "require_perm", return_value=self.user),
            mock.patch.object(routes, "erp_target_projection_enabled_for", return_value=True),
            mock.patch.object(routes, "_resolve_endpoint", return_value=endpoint),
            mock.patch.object(routes.target_refresh, "request_refresh") as request_refresh,
        ):
            response = self.client.post(
                "/api/erp/endpoints/33333333-3333-4333-8333-333333333333/target-projection/refresh"
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["detail"], "erp.companion_update_required")
        request_refresh.assert_not_called()

    def test_refresh_status_is_tenant_and_endpoint_scoped(self):
        with (
            mock.patch.object(routes, "require_perm", return_value=self.user),
            mock.patch.object(routes, "erp_target_projection_enabled_for", return_value=True),
            mock.patch.object(routes, "_endpoint_visible", return_value=True),
            mock.patch.object(
                routes.target_refresh,
                "refresh_status",
                return_value={"status": "succeeded", "result_revision": 9},
            ) as status,
        ):
            response = self.client.get(
                "/api/erp/endpoints/33333333-3333-4333-8333-333333333333/"
                "target-projection/refresh/44444444-4444-4444-8444-444444444444"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["refresh"]["result_revision"], 9)
        status.assert_called_once_with(
            "44444444-4444-4444-8444-444444444444",
            tenant_id=self.user["tenant_id"],
            endpoint_id="33333333-3333-4333-8333-333333333333",
        )


if __name__ == "__main__":
    unittest.main()
