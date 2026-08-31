from __future__ import annotations

import asyncio
import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest import mock

from fastapi import HTTPException

from routes import erp_endpoints_routes, history_routes
from services.erp import team_access
from services.line_erp import cards


def _request():
    return SimpleNamespace(state=SimpleNamespace(), cookies={}, headers={})


def _member(**overrides):
    user = {
        "id": "00000000-0000-0000-0000-000000000002",
        "tenant_id": "00000000-0000-0000-0000-000000000001",
        "entry": "erp",
        "is_active": True,
        "is_super_admin": False,
    }
    user.update(overrides)
    return user


class TeamPermissionTests(unittest.TestCase):
    def test_normalizes_modules_in_product_order(self):
        self.assertEqual(
            team_access.normalize_modules(["sales", "PRODUCT", "unknown", "purchase"]),
            ("product", "purchase", "sales"),
        )

    def test_member_codes_exclude_configuration_permissions(self):
        codes = set(team_access.permission_codes(["product", "purchase", "sales"]))
        self.assertIn("stockcard.report.view", codes)
        self.assertIn("purchase.doc.create", codes)
        self.assertIn("sales.doc.create", codes)
        self.assertIn("erp.endpoint.view", codes)
        self.assertIn("intake.upload", codes)
        self.assertNotIn("purchase.settings.manage", codes)
        self.assertNotIn("purchase.supplier.manage", codes)
        self.assertNotIn("sales.product.manage", codes)
        self.assertNotIn("sales.settings.manage", codes)
        self.assertNotIn("erp.endpoint.manage", codes)

    def test_member_cannot_switch_from_assigned_endpoint(self):
        user = _member()
        access = {"is_owner": False, "is_active": True, "modules": ["purchase"]}
        assigned = {"id": "00000000-0000-0000-0000-000000000010"}
        with (
            mock.patch.object(team_access, "access_for_user", return_value=access),
            mock.patch.object(team_access, "assigned_push_endpoint", return_value=assigned),
        ):
            self.assertEqual(
                team_access.assigned_endpoint_for_request(user, None),
                assigned,
            )
            with self.assertRaises(HTTPException) as raised:
                team_access.assigned_endpoint_for_request(
                    user, "00000000-0000-0000-0000-000000000011"
                )
        self.assertEqual(raised.exception.status_code, 404)

    def test_profile_does_not_expand_a_non_team_role(self):
        @contextmanager
        def cursor_context():
            yield mock.MagicMock()

        row = {
            "role_key": "accountant",
            "membership_status": "active",
            "team_active": True,
            "modules": ["purchase"],
        }
        with (
            mock.patch.object(team_access.db, "get_cursor", side_effect=cursor_context),
            mock.patch.object(team_access, "_role_and_profile", return_value=row),
        ):
            self.assertIsNone(team_access.access_for_user("tenant", "member"))

    def test_member_gets_creator_scope_owner_keeps_tenant_scope(self):
        request = _request()
        user = _member()
        member_access = {
            "is_owner": False,
            "is_active": True,
            "modules": ["purchase"],
        }
        with mock.patch.object(team_access, "access_for_user", return_value=member_access):
            self.assertEqual(team_access.record_creator_scope(request, user), user["id"])
            self.assertIsNone(team_access.tenant_record_scope(request, user))

        owner_access = {"is_owner": True, "is_active": True, "modules": list(team_access.MODULES)}
        request = _request()
        with mock.patch.object(team_access, "access_for_user", return_value=owner_access):
            self.assertIsNone(team_access.record_creator_scope(request, user))
            self.assertEqual(team_access.tenant_record_scope(request, user), user["tenant_id"])

    def test_line_menu_only_renders_assigned_mode(self):
        rendered = str(cards.menu_card(("purchase",)))
        self.assertIn("mode%3Apurchase", rendered)
        self.assertNotIn("mode%3Asales", rendered)

    def test_member_endpoint_list_never_appends_other_shared_targets(self):
        user = _member(role="member")
        assigned = [{"id": "assigned", "adapter": "mrerp", "read_only": True}]
        with (
            mock.patch.object(
                erp_endpoints_routes, "get_current_user_from_request", return_value=user
            ),
            mock.patch.object(erp_endpoints_routes, "require_erp_portal"),
            mock.patch.object(erp_endpoints_routes, "_check_push_access"),
            mock.patch.object(
                erp_endpoints_routes.team_access,
                "assigned_endpoint_items",
                return_value=assigned,
            ),
            mock.patch.object(
                erp_endpoints_routes.shared_express_access,
                "list_shared_endpoint_items",
            ) as shared,
        ):
            result = asyncio.run(erp_endpoints_routes.erp_endpoints_list(_request()))
        self.assertEqual(result, {"items": assigned})
        shared.assert_not_called()


class HistoryOwnershipTests(unittest.TestCase):
    def _cursor_context(self, found):
        cursor = mock.MagicMock()
        cursor.fetchone.return_value = {"n": found}

        @contextmanager
        def context(**_kwargs):
            yield cursor

        return cursor, context

    def test_member_history_batch_must_be_entirely_owned(self):
        user = _member()
        cursor, context = self._cursor_context(1)
        with (
            mock.patch.object(team_access, "record_creator_scope", return_value=user["id"]),
            mock.patch.object(team_access.db, "get_cursor_rls", side_effect=context),
            self.assertRaises(HTTPException) as raised,
        ):
            team_access.assert_owned_histories(_request(), user, ["a", "b"])
        self.assertEqual(raised.exception.status_code, 404)
        self.assertIn("user_id = %s::uuid", cursor.execute.call_args.args[0])

    def test_history_list_uses_member_user_scope(self):
        user = _member()
        request = _request()
        expected = {"items": [], "total": 0, "status_counts": {}}
        with (
            mock.patch.object(history_routes, "get_current_user_from_request", return_value=user),
            mock.patch.object(history_routes, "_check_history_access", return_value=90),
            mock.patch.object(
                history_routes.db, "get_visible_client_ids_for_user", return_value=None
            ),
            mock.patch.object(history_routes.wc, "active_workspace_for_request", return_value=7),
            mock.patch.object(history_routes.team_access, "tenant_record_scope", return_value=None),
            mock.patch.object(history_routes, "list_ocr_history", return_value=expected) as listing,
        ):
            result = asyncio.run(history_routes.history_list(request))
        self.assertEqual(result, expected)
        self.assertIsNone(listing.call_args.kwargs["tenant_id"])
        self.assertEqual(listing.call_args.kwargs["user_id"], user["id"])


if __name__ == "__main__":
    unittest.main()
