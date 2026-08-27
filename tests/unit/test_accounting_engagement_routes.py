"""ERP/Cowork 双确认 API 的入口、RLS 与状态契约。"""

from __future__ import annotations

import contextlib
import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes import accounting_engagement_routes as routes


@contextlib.contextmanager
def cursor_cm(cur):
    yield cur


def row(status="pending_merchant"):
    return {
        "id": "eng-1",
        "firm_tenant_id": "firm-1",
        "firm_workspace_client_id": 8 if status == "active" else None,
        "merchant_tenant_id": "merchant-1",
        "merchant_workspace_client_id": 7 if status != "pending_merchant" else None,
        "status": status,
        "merchant_accepted_at": None,
        "firm_accepted_at": None,
        "active_from": None,
        "ended_at": None,
        "created_at": None,
        "updated_at": None,
        "snapshot_json": {"must": "not leak"},
    }


class AccountingEngagementRouteTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(routes.router)
        self.client = TestClient(app)

    def test_route_surface_is_split_by_product(self):
        got = {
            (method, route.path)
            for route in routes.router.routes
            for method in route.methods
            if method in {"GET", "POST"}
        }
        self.assertEqual(
            got,
            {
                ("GET", "/api/erp/accounting-engagements"),
                ("POST", "/api/erp/accounting-engagements/{engagement_id}/accept"),
                ("GET", "/api/cowork/accounting-engagements"),
                ("POST", "/api/cowork/accounting-engagements/{engagement_id}/accept"),
            },
        )

    def test_wrong_product_session_is_rejected_before_flag_or_database(self):
        with (
            mock.patch.object(
                routes,
                "require_perm",
                return_value={"id": "u1", "tenant_id": "merchant-1", "entry": "cowork"},
            ),
            mock.patch.object(routes.flags, "enabled_for") as enabled,
            mock.patch.object(routes.db, "get_cursor_rls") as get_cursor,
        ):
            response = self.client.get("/api/erp/accounting-engagements")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "ERR_ENGAGEMENT_FORBIDDEN")
        enabled.assert_not_called()
        get_cursor.assert_not_called()

    def test_default_closed_flag_hides_participant_routes(self):
        with (
            mock.patch.object(
                routes,
                "require_perm",
                return_value={"id": "u1", "tenant_id": "merchant-1", "entry": "erp"},
            ),
            mock.patch.object(routes.flags, "enabled_for", return_value=False),
            mock.patch.object(routes.db, "get_cursor_rls") as get_cursor,
        ):
            response = self.client.get("/api/erp/accounting-engagements")
        self.assertEqual(response.status_code, 404)
        get_cursor.assert_not_called()

    def test_merchant_list_uses_merchant_rls_and_returns_metadata_only(self):
        cur = object()
        with (
            mock.patch.object(
                routes,
                "require_perm",
                return_value={"id": "u1", "tenant_id": "merchant-1", "entry": "erp"},
            ),
            mock.patch.object(routes.flags, "enabled_for", return_value=True),
            mock.patch.object(
                routes.db, "get_cursor_rls", return_value=cursor_cm(cur)
            ) as get_cursor,
            mock.patch.object(routes.store, "list_for_tenant", return_value=[row()]) as listing,
        ):
            response = self.client.get("/api/erp/accounting-engagements")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("snapshot_json", str(response.json()))
        get_cursor.assert_called_once_with(tenant_id="merchant-1", user_id="u1")
        listing.assert_called_once_with(cur, tenant_id="merchant-1")

    def test_merchant_accept_moves_to_pending_firm_in_one_rls_transaction(self):
        cur = object()
        accepted = row("pending_firm")
        with (
            mock.patch.object(
                routes,
                "require_perm",
                return_value={"id": "u1", "tenant_id": "merchant-1", "entry": "erp"},
            ),
            mock.patch.object(routes.flags, "enabled_for", return_value=True),
            mock.patch.object(
                routes.db, "get_cursor_rls", return_value=cursor_cm(cur)
            ) as get_cursor,
            mock.patch.object(routes.lifecycle, "accept_merchant", return_value=accepted) as accept,
            mock.patch.object(routes, "_log_op"),
        ):
            response = self.client.post(
                "/api/erp/accounting-engagements/eng-1/accept",
                json={"workspace_client_id": 7},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["engagement"]["status"], "pending_firm")
        get_cursor.assert_called_once_with(tenant_id="merchant-1", user_id="u1", commit=True)
        accept.assert_called_once_with(
            cur,
            engagement_id="eng-1",
            merchant_tenant_id="merchant-1",
            workspace_client_id=7,
        )

    def test_cowork_accept_uses_firm_identity_and_activates(self):
        cur = object()
        active = row("active")
        with (
            mock.patch.object(
                routes,
                "require_perm",
                return_value={"id": "u2", "tenant_id": "firm-1", "entry": "cowork"},
            ),
            mock.patch.object(routes.flags, "enabled_for", return_value=True),
            mock.patch.object(routes.db, "get_cursor_rls", return_value=cursor_cm(cur)),
            mock.patch.object(routes.lifecycle, "accept_firm", return_value=active) as accept,
            mock.patch.object(routes, "_log_op"),
        ):
            response = self.client.post(
                "/api/cowork/accounting-engagements/eng-1/accept",
                json={"workspace_client_id": 8},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["engagement"]["status"], "active")
        accept.assert_called_once_with(
            cur,
            engagement_id="eng-1",
            firm_tenant_id="firm-1",
            workspace_client_id=8,
        )


if __name__ == "__main__":
    unittest.main()
