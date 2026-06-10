# -*- coding: utf-8 -*-
"""resolver 纯逻辑守门:JSONB 解析 / 存量映射 / deny-by-default / 作用域语义。"""

import unittest

from services.authz import registry
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
        for junk in (None, "", "{bad json", {"manage_team": True}, 42):
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
