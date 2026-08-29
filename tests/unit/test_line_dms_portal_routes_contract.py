# -*- coding: utf-8 -*-

import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from core.pos_api import PosError
from routes import line_dms_portal_routes as portal_routes

EXPECTED = {
    ("POST", "/api/line/dms-portal/ticket"),
    ("GET", "/home/dms-booking/portal"),
}


class LineDmsPortalRouteContractTests(unittest.TestCase):
    def test_router_contract(self):
        got = {
            (method, route.path)
            for route in portal_routes.router.routes
            for method in (getattr(route, "methods", set()) or set())
            if method in {"GET", "POST"}
        }
        self.assertEqual(got, EXPECTED)

    def test_app_registers_routes(self):
        import app

        paths = {route.path for route in app.app.routes if hasattr(route, "path")}
        for _method, path in EXPECTED:
            self.assertIn(path, paths)

    def test_public_relay_is_explicitly_whitelisted(self):
        from scripts.check_authz_coverage import PUBLIC_ROUTES

        self.assertIn(("GET", "/home/dms-booking/portal"), PUBLIC_ROUTES)


class LineDmsPortalRouteTests(unittest.TestCase):
    @patch.object(portal_routes.login_tickets, "issue_login_ticket")
    @patch.object(portal_routes, "_authorize", new_callable=AsyncMock)
    def test_issue_ticket_is_bound_to_authenticated_identity(self, authorize, issue):
        authorize.return_value = {"id": "user-1", "tenant_id": "tenant-2"}
        issue.return_value = {"ticket": "opaque+/", "expires_at": "soon"}
        result = asyncio.run(portal_routes.issue_mrerp_login_ticket(object()))
        issue.assert_called_once_with("tenant-2", "user-1")
        self.assertEqual(
            result["data"]["url"],
            "/home/dms-booking/portal?ticket=opaque%2B%2F",
        )
        self.assertTrue(result["data"]["url"].startswith("/home/dms-booking/"))

    @patch.object(portal_routes, "_authorize", new_callable=AsyncMock)
    def test_issue_rejects_missing_identity(self, authorize):
        authorize.return_value = {"id": "user-1", "tenant_id": ""}
        with self.assertRaises(PosError) as caught:
            asyncio.run(portal_routes.issue_mrerp_login_ticket(object()))
        self.assertEqual(caught.exception.http_status, 403)

    @patch.object(portal_routes.login_tickets, "consume_login_ticket", return_value=None)
    def test_invalid_or_reused_ticket_is_gone(self, _consume):
        response = asyncio.run(portal_routes.consume_mrerp_login_ticket("bad"))
        self.assertEqual(response.status_code, 410)
        self.assertIn("no-store", response.headers["cache-control"])

    @patch.object(portal_routes.mrerp_portal, "load_credentials")
    @patch.object(portal_routes.db, "find_user_by_id")
    @patch.object(portal_routes.login_tickets, "consume_login_ticket")
    def test_success_returns_uncached_relay(self, consume, find_user, load_credentials):
        consume.return_value = {"tenant_id": "tenant-2", "user_id": "user-1"}
        find_user.return_value = {
            "id": "user-1",
            "tenant_id": "tenant-2",
            "is_active": True,
        }
        load_credentials.return_value = ("staff", "secret")
        response = asyncio.run(portal_routes.consume_mrerp_login_ticket("opaque"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response.headers["cache-control"])
        self.assertEqual(response.headers["referrer-policy"], "no-referrer")
        self.assertIn(b'name="txtpasswords"', response.body)

    @patch.object(
        portal_routes.mrerp_portal,
        "load_credentials",
        side_effect=portal_routes.mrerp_portal.PortalCredentialsMissing,
    )
    @patch.object(portal_routes.db, "find_user_by_id")
    @patch.object(portal_routes.login_tickets, "consume_login_ticket")
    def test_missing_credentials_is_conflict(self, consume, find_user, _load):
        consume.return_value = {"tenant_id": "tenant-2", "user_id": "user-1"}
        find_user.return_value = {"tenant_id": "tenant-2", "is_active": True}
        response = asyncio.run(portal_routes.consume_mrerp_login_ticket("opaque"))
        self.assertEqual(response.status_code, 409)
        self.assertNotIn(b"staff", response.body)

    @patch.object(portal_routes.db, "find_user_by_id")
    @patch.object(portal_routes.login_tickets, "consume_login_ticket")
    def test_ticket_identity_cannot_cross_tenants(self, consume, find_user):
        consume.return_value = {"tenant_id": "tenant-2", "user_id": "user-1"}
        find_user.return_value = {"tenant_id": "tenant-other", "is_active": True}
        response = asyncio.run(portal_routes.consume_mrerp_login_ticket("opaque"))
        self.assertEqual(response.status_code, 410)


if __name__ == "__main__":
    unittest.main()
