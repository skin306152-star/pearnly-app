# -*- coding: utf-8 -*-
"""resolver 纯逻辑守门:JSONB 解析 / 存量映射 / deny-by-default / 作用域语义。"""

import unittest

from services.authz import registry
from services.authz import resolver
from services.authz.resolver import (
    Authz,
    legacy_role_key,
    perms_from_jsonb,
)


class PermsFromJsonbTests(unittest.TestCase):
    def test_all_true_expands_to_full_set(self):
        self.assertEqual(perms_from_jsonb({"all": True}), registry.ALL_CODES)

    def test_all_true_as_string_jsonb(self):
        self.assertEqual(perms_from_jsonb('{"all": true}'), registry.ALL_CODES)

    def test_list_filters_unknown_codes(self):
        perms = perms_from_jsonb(["sales.doc.view", "not.a.code"])
        self.assertEqual(perms, frozenset({"sales.doc.view"}))

    def test_garbage_yields_empty(self):
        for junk in (None, "", "{bad json", {"unknown": True}, 42):
            self.assertEqual(perms_from_jsonb(junk), frozenset(), repr(junk))


class LegacyRoleKeyTests(unittest.TestCase):
    def test_owner_role(self):
        self.assertEqual(legacy_role_key({"role": "owner", "invited_by": "x"}), "owner")

    def test_invited_by_null_is_owner(self):
        self.assertEqual(legacy_role_key({"role": None, "invited_by": None}), "owner")

    def test_invited_member_maps_to_accountant(self):
        self.assertEqual(legacy_role_key({"role": "member", "invited_by": "boss"}), "accountant")

    def test_cashier_stays_cashier(self):
        self.assertEqual(legacy_role_key({"role": "cashier", "invited_by": None}), "cashier")


class AuthzDenyByDefaultTests(unittest.TestCase):
    def test_unknown_code_denied_even_with_full_set(self):
        authz = Authz(role_key="owner", permissions=registry.ALL_CODES)
        self.assertFalse(authz.has("made.up.code"))

    def test_known_code_granted(self):
        authz = Authz(role_key="viewer", permissions=frozenset({"sales.doc.view"}))
        self.assertTrue(authz.has("sales.doc.view"))
        self.assertFalse(authz.has("sales.doc.approve"))

    def test_empty_permissions_deny_all(self):
        authz = Authz(role_key="none")
        for code in sorted(registry.ALL_CODES)[:5]:
            self.assertFalse(authz.has(code))


class WorkspaceScopeTests(unittest.TestCase):
    def test_scope_all_allows_any_workspace(self):
        authz = Authz(role_key="accountant", scope_mode="all")
        self.assertTrue(authz.allows_workspace(11))
        self.assertTrue(authz.allows_workspace(None))

    def test_assigned_allows_only_listed(self):
        authz = Authz(
            role_key="accountant", scope_mode="assigned", workspace_ids=frozenset({11, 12})
        )
        self.assertTrue(authz.allows_workspace(11))
        self.assertTrue(authz.allows_workspace("12"))
        self.assertFalse(authz.allows_workspace(33))

    def test_assigned_with_no_list_denies(self):
        authz = Authz(role_key="clerk", scope_mode="assigned", workspace_ids=frozenset())
        self.assertFalse(authz.allows_workspace(11))
        self.assertFalse(authz.allows_workspace(None))


class _Cursor:
    def __init__(self, rows=()):
        self.rows = list(rows)
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((" ".join(sql.split()), params))

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None


class _ResolveCursor:
    def __init__(self, membership, workspace_ids=()):
        self.membership = membership
        self.workspace_ids = list(workspace_ids)
        self.calls = []
        self.current = None

    def execute(self, sql, params=None):
        compact = " ".join(sql.split())
        self.calls.append((compact, params))
        self.current = "scopes" if "FROM member_scopes" in compact else "membership"

    def fetchone(self):
        return self.membership if self.current == "membership" else None

    def fetchall(self):
        if self.current == "scopes":
            return [{"workspace_client_id": workspace_id} for workspace_id in self.workspace_ids]
        return []


class ErpTeamRoleRuntimeStatusTests(unittest.TestCase):
    def _row(self, *, active):
        return {
            "id": "membership-1",
            "scope_mode": "assigned",
            "role_key": "custom:erp-team-p",
            "permissions": ["purchase.doc.create"],
            "role_tenant_id": "tenant-a",
            "role_is_active": active,
        }

    def test_active_erp_team_role_resolves_permissions_and_locked_scope(self):
        cur = _ResolveCursor(self._row(active=True), workspace_ids=[11])
        authz = resolver._resolve_with_cursor(
            cur,
            {"id": "user-1", "role": "member", "invited_by": "owner-1"},
            "tenant-a",
            lock=True,
        )
        self.assertTrue(authz.has("purchase.doc.create"))
        self.assertEqual(authz.workspace_ids, frozenset({11}))
        self.assertIn("FOR SHARE OF m, r", cur.calls[0][0])
        self.assertIn("FOR SHARE", cur.calls[1][0])

    def test_inactive_erp_team_role_loses_permissions_without_legacy_fallback(self):
        cur = _ResolveCursor(self._row(active=False), workspace_ids=[11])
        authz = resolver._resolve_with_cursor(
            cur,
            {"id": "user-1", "role": "member", "invited_by": "owner-1"},
            "tenant-a",
        )
        self.assertEqual(authz.role_key, "custom:erp-team-p")
        self.assertEqual(authz.permissions, frozenset())
        self.assertEqual(authz.scope_mode, "assigned")
        self.assertEqual(authz.workspace_ids, frozenset({11}))
        self.assertFalse(authz.has("acct.entry.approve"))

    def test_cross_tenant_erp_team_role_is_also_fail_closed(self):
        row = self._row(active=True)
        row["role_tenant_id"] = "tenant-b"
        authz = resolver._resolve_with_cursor(
            _ResolveCursor(row),
            {"id": "user-1", "role": "member", "invited_by": "owner-1"},
            "tenant-a",
        )
        self.assertEqual(authz.role_key, "custom:erp-team-p")
        self.assertEqual(authz.permissions, frozenset())

    def test_retired_general_custom_role_is_fail_closed(self):
        row = self._row(active=True)
        row["role_key"] = "custom:buyer"
        authz = resolver._resolve_with_cursor(
            _ResolveCursor(row),
            {"id": "user-1", "role": "member", "invited_by": "owner-1"},
            "tenant-a",
        )
        self.assertEqual(authz.permissions, frozenset())


class AssignableRoleResolutionTests(unittest.TestCase):
    def test_erp_team_role_requires_explicit_opt_in(self):
        cur = _Cursor([{"id": "should-not-be-read"}])
        role_id = resolver._assignable_role_id(cur, "tenant-a", "custom:erp-team-p")
        self.assertIsNone(role_id)
        self.assertEqual(cur.calls, [])

    def test_erp_team_role_query_binds_tenant_and_active(self):
        cur = _Cursor([{"id": "role-1"}])
        role_id = resolver._assignable_role_id(
            cur, "tenant-a", "custom:erp-team-p", allow_erp_team_role=True
        )
        self.assertEqual(role_id, "role-1")
        sql, params = cur.calls[0]
        self.assertIn("tenant_id = %s", sql)
        self.assertIn("COALESCE(is_active, TRUE)", sql)
        self.assertIn("FOR SHARE", sql)
        self.assertEqual(params, ("custom:erp-team-p", "tenant-a"))

    def test_general_custom_role_is_rejected(self):
        cur = _Cursor([{"id": "should-not-be-read"}])
        role_id = resolver._assignable_role_id(
            cur, "tenant-a", "custom:buyer", allow_erp_team_role=True
        )
        self.assertIsNone(role_id)
        self.assertEqual(cur.calls, [])

    def test_unassignable_system_role_does_not_query(self):
        cur = _Cursor([{"id": "cashier-role"}])
        self.assertIsNone(resolver._assignable_role_id(cur, "tenant-a", "cashier"))
        self.assertEqual(cur.calls, [])


class CreateMembershipTests(unittest.TestCase):
    def test_erp_team_role_cannot_enter_without_explicit_opt_in(self):
        cur = _Cursor()
        ok = resolver.create_membership(
            cur,
            user_id="user-1",
            tenant_id="tenant-a",
            role_key="custom:erp-team-p",
        )
        self.assertFalse(ok)
        self.assertEqual(cur.calls, [])

    def test_owner_requires_registration_callers_explicit_allowance(self):
        cur = _Cursor([{"id": "owner-role"}])
        ok = resolver.create_membership(
            cur,
            user_id="user-1",
            tenant_id="tenant-a",
            role_key="owner",
            allow_owner=False,
        )
        self.assertFalse(ok)
        self.assertEqual(cur.calls, [])

    def test_conflicting_membership_is_not_reported_as_success(self):
        cur = _Cursor([{"id": "role-viewer"}, None])
        ok = resolver.create_membership(
            cur,
            user_id="user-1",
            tenant_id="tenant-a",
            role_key="viewer",
        )
        self.assertFalse(ok)
        self.assertFalse(any(sql.startswith("UPDATE users") for sql, _ in cur.calls))

    def test_active_erp_team_membership_succeeds_when_enabled_by_caller(self):
        cur = _Cursor([{"id": "role-custom"}, {"?column?": 1}])
        ok = resolver.create_membership(
            cur,
            user_id="user-1",
            tenant_id="tenant-a",
            role_key="custom:erp-team-p",
            granted_by="owner-1",
            scope_mode="assigned",
            allow_erp_team_role=True,
        )
        self.assertTrue(ok)
        self.assertTrue(any(sql.startswith("INSERT INTO memberships") for sql, _ in cur.calls))
        self.assertTrue(any(sql.startswith("UPDATE users") for sql, _ in cur.calls))
