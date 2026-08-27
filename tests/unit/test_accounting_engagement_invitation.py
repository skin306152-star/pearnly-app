"""Earn ERP 邀请与事务所关系原子编排契约。"""

from __future__ import annotations

import contextlib
import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core import route_helpers
from routes import admin_erp_routes
from services.accounting_engagement import invitations
from services.accounting_engagement.errors import PRIMARY_EXISTS, EngagementError


class Cursor:
    def __init__(self, one=None):
        self.one = one or {"ok": 1}
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self.one


@contextlib.contextmanager
def cursor_cm(cur):
    yield cur


def identity(username="merchant@example.test"):
    return {
        "lookup_key": username,
        "username": username,
        "email": username if "@" in username else None,
        "email_norm": username if "@" in username else None,
    }


def engagement():
    return {
        "id": "eng-1",
        "firm_tenant_id": "firm-1",
        "merchant_tenant_id": "merchant-1",
        "status": "pending_merchant",
    }


class InvitationServiceTests(unittest.TestCase):
    def test_existing_account_is_reused_without_password_reset(self):
        cur = Cursor()
        resolver = mock.Mock(return_value="must-not-run")
        with (
            mock.patch.object(
                invitations,
                "find_login_user",
                return_value={"id": "user-1", "tenant_id": "merchant-1", "username": "boss"},
            ),
            mock.patch.object(invitations, "create_owner_login_user") as create_user,
            mock.patch.object(invitations, "_ensure_tenant_for_new_user") as create_tenant,
            mock.patch.object(invitations.lifecycle, "invite", return_value=engagement()),
            mock.patch.object(invitations, "grant_entrance") as grant,
        ):
            result = invitations.invite_merchant(
                cur,
                identity=identity("boss"),
                firm_tenant_id="firm-1",
                admin_user_id="admin-1",
                password="ignored",
                password_resolver=resolver,
            )

        self.assertFalse(result["created_account"])
        self.assertNotIn("initial_password", result)
        resolver.assert_not_called()
        create_user.assert_not_called()
        create_tenant.assert_not_called()
        grant.assert_called_once_with(cur, "merchant-1", "erp", "admin-1")
        self.assertTrue(any("platform_setting_allowlist" in sql for sql, _ in cur.calls))

    def test_new_account_tenant_engagement_and_access_share_one_cursor(self):
        cur = Cursor()
        with (
            mock.patch.object(invitations, "find_login_user", return_value=None),
            mock.patch.object(invitations, "hash_password", return_value="hash") as hasher,
            mock.patch.object(
                invitations, "create_owner_login_user", return_value="user-new"
            ) as create_user,
            mock.patch.object(
                invitations, "_ensure_tenant_for_new_user", return_value="merchant-1"
            ) as create_tenant,
            mock.patch.object(invitations.lifecycle, "invite", return_value=engagement()) as invite,
            mock.patch.object(invitations, "grant_entrance") as grant,
        ):
            result = invitations.invite_merchant(
                cur,
                identity=identity(),
                firm_tenant_id="firm-1",
                admin_user_id="admin-1",
                password="Temp1234",
            )

        self.assertTrue(result["created_account"])
        self.assertEqual(result["initial_password"], "Temp1234")
        hasher.assert_called_once_with("Temp1234")
        self.assertEqual(create_user.call_args.args[0], cur)
        self.assertEqual(create_tenant.call_args.args[0], cur)
        self.assertEqual(create_tenant.call_args.kwargs["entry"], "erp")
        self.assertEqual(invite.call_args.args[0], cur)
        self.assertEqual(grant.call_args.args[0], cur)

    def test_relationship_conflict_stops_access_grant(self):
        cur = Cursor()
        with (
            mock.patch.object(
                invitations,
                "find_login_user",
                return_value={"id": "user-1", "tenant_id": "merchant-1", "username": "boss"},
            ),
            mock.patch.object(
                invitations.lifecycle,
                "invite",
                side_effect=EngagementError(PRIMARY_EXISTS),
            ),
            mock.patch.object(invitations, "grant_entrance") as grant,
        ):
            with self.assertRaises(EngagementError) as error:
                invitations.invite_merchant(
                    cur,
                    identity=identity("boss"),
                    firm_tenant_id="firm-2",
                    admin_user_id="admin-1",
                )
        self.assertEqual(error.exception.code, PRIMARY_EXISTS)
        grant.assert_not_called()
        self.assertFalse(any("platform_setting_allowlist" in sql for sql, _ in cur.calls))


class InvitationRouteTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(admin_erp_routes.router)
        self.client = TestClient(app)
        self.super_admin = mock.patch.object(
            route_helpers,
            "get_current_user_from_request",
            return_value={"id": "admin-1", "is_super_admin": True},
        )
        self.super_admin.start()
        self.addCleanup(self.super_admin.stop)

    def test_relationship_path_is_default_closed_before_database_write(self):
        with (
            mock.patch.object(admin_erp_routes.engagement_flags, "enabled_for", return_value=False),
            mock.patch.object(admin_erp_routes.db, "get_cursor_rls") as get_cursor,
        ):
            response = self.client.post(
                "/api/admin/erp/invite",
                json={"username_or_email": "boss", "firm_tenant_id": "firm-1"},
            )
        self.assertEqual(response.status_code, 404)
        get_cursor.assert_not_called()

    def test_enabled_relationship_invite_returns_metadata_only(self):
        cur = Cursor()
        result = {
            "created_account": True,
            "initial_password": "Temp1234",
            "merchant_tenant_id": "merchant-1",
            "username": "merchant@example.test",
            "engagement": engagement(),
        }
        with (
            mock.patch.object(admin_erp_routes.engagement_flags, "enabled_for", return_value=True),
            mock.patch.object(
                admin_erp_routes.db, "get_cursor_rls", return_value=cursor_cm(cur)
            ) as get_cursor,
            mock.patch.object(
                admin_erp_routes.engagement_invitations,
                "invite_merchant",
                return_value=result,
            ),
            mock.patch.object(admin_erp_routes, "_log_op"),
        ):
            response = self.client.post(
                "/api/admin/erp/invite",
                json={
                    "username_or_email": "merchant@example.test",
                    "firm_tenant_id": "firm-1",
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["engagement"]["status"], "pending_merchant")
        self.assertNotIn("snapshot_json", str(body))
        get_cursor.assert_called_once_with(bypass=True, commit=True)

    def test_active_firm_list_contains_only_selection_metadata(self):
        cur = Cursor()
        rows = [
            {
                "tenant_id": "firm-1",
                "firm_code": "PF000001",
                "display_name": "Acme Accounting",
                "tax_id": "0100000000001",
                "tenant_name": "Acme",
                "status": "active",
            }
        ]
        with (
            mock.patch.object(
                admin_erp_routes.db, "get_cursor_rls", return_value=cursor_cm(cur)
            ) as get_cursor,
            mock.patch.object(
                admin_erp_routes.firm_store,
                "list_active_profiles_for_admin",
                return_value=rows,
            ),
        ):
            response = self.client.get("/api/admin/erp/firms")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.json()["firms"][0]),
            {"tenant_id", "firm_code", "display_name", "tax_id"},
        )
        get_cursor.assert_called_once_with(bypass=True)


if __name__ == "__main__":
    unittest.main()
