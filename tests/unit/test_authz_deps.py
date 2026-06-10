# -*- coding: utf-8 -*-
"""require_perm 判定核守门:短路顺序 / POS 令牌码集 / 模块联动 / scope 404 语义。

mock 掉查库面(_module_disabled/_cached_authz),只验 deps 自身的判定逻辑。
"""

import unittest
from unittest import mock

from fastapi import HTTPException

from services.authz import deps
from services.authz.resolver import Authz


def _user(**kw):
    base = {"id": "u1", "tenant_id": "t1", "role": "member", "is_super_admin": False}
    base.update(kw)
    return base


def _no_pos_token(request):
    return None


class CheckOrderTests(unittest.TestCase):
    def test_unknown_code_denied_even_for_super_admin(self):
        allowed, reason = deps._check(None, _user(is_super_admin=True), "made.up.code")
        self.assertFalse(allowed)
        self.assertEqual(reason, "unknown_code")

    def test_super_admin_short_circuits(self):
        with mock.patch.object(deps, "_pos_token_payload", _no_pos_token):
            allowed, _ = deps._check(None, _user(is_super_admin=True), "billing.manage")
        self.assertTrue(allowed)

    def test_cashier_role_limited_to_cashier_codes(self):
        with mock.patch.object(deps, "_pos_token_payload", _no_pos_token):
            allowed, _ = deps._check(None, _user(role="cashier"), "pos.sale.operate")
            self.assertTrue(allowed)
            allowed, reason = deps._check(None, _user(role="cashier"), "sales.doc.view")
        self.assertFalse(allowed)
        self.assertEqual(reason, "pos_token_out_of_scope")

    def test_no_tenant_denied(self):
        with mock.patch.object(deps, "_pos_token_payload", _no_pos_token):
            allowed, reason = deps._check(None, _user(tenant_id=None), "sales.doc.view")
        self.assertFalse(allowed)
        self.assertEqual(reason, "no_tenant")

    def test_module_disabled_blocks_before_role(self):
        owner_authz = Authz(role_key="owner", permissions=frozenset({"pos.admin.manage"}))
        with (
            mock.patch.object(deps, "_pos_token_payload", _no_pos_token),
            mock.patch.object(deps, "_module_disabled", return_value=True),
            mock.patch.object(deps, "_cached_authz", return_value=owner_authz),
        ):
            allowed, reason = deps._check(None, _user(role="owner"), "pos.admin.manage")
        self.assertFalse(allowed)
        self.assertEqual(reason, "module_disabled")

    def test_role_permission_decides(self):
        viewer = Authz(role_key="viewer", permissions=frozenset({"sales.doc.view"}))
        with (
            mock.patch.object(deps, "_pos_token_payload", _no_pos_token),
            mock.patch.object(deps, "_module_disabled", return_value=False),
            mock.patch.object(deps, "_cached_authz", return_value=viewer),
        ):
            allowed, _ = deps._check(None, _user(), "sales.doc.view")
            self.assertTrue(allowed)
            allowed, reason = deps._check(None, _user(), "sales.doc.approve")
        self.assertFalse(allowed)
        self.assertEqual(reason, "forbidden")


class WorkspaceScopeTests(unittest.TestCase):
    def test_assigned_member_unlisted_workspace_404(self):
        assigned = Authz(
            role_key="accountant", scope_mode="assigned", workspace_ids=frozenset({11})
        )
        with mock.patch.object(deps, "_cached_authz", return_value=assigned):
            deps.check_workspace_scope(None, _user(), 11)
            with self.assertRaises(HTTPException) as ctx:
                deps.check_workspace_scope(None, _user(), 33)
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "authz.not_found")

    def test_scope_all_member_passes(self):
        allmode = Authz(role_key="accountant", scope_mode="all")
        with mock.patch.object(deps, "_cached_authz", return_value=allmode):
            deps.check_workspace_scope(None, _user(), 999)

    def test_super_admin_skips_scope(self):
        deps.check_workspace_scope(None, _user(is_super_admin=True), 999)
