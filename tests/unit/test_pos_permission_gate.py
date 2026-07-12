# -*- coding: utf-8 -*-
"""POS 越权守门测试(docs/pos/10 §5.1 · 批2:require_perm_pos 统一执行点)。

收银员 token 只认收银码集(卖货/班次);管理动作(开通收银、库存进货/盘点/调整、销售报表)
按矩阵码集判定。锁 require_perm_pos 判定 + 库存写/报表/开通路由逐条带码接线(防回归降级)。"""

import contextlib
import inspect
import os
import unittest
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-of-sufficient-length")

from core.pos_api import PosError
from core import pos_api
from services.authz import deps
from services.authz.registry import ALL_CODES
from services.authz.resolver import Authz


class _Req:
    def __init__(self):
        self.headers = {}


@contextlib.contextmanager
def _gate(user, *codes, module_disabled=False):
    authz = Authz(role_key="test", permissions=frozenset(codes))
    with contextlib.ExitStack() as st:
        st.enter_context(mock.patch("core.pos_api.pos_auth", return_value=user))
        st.enter_context(mock.patch.object(deps, "_pos_token_payload", return_value=None))
        st.enter_context(mock.patch.object(deps, "_module_disabled", return_value=module_disabled))
        st.enter_context(mock.patch.object(deps, "_cached_authz", return_value=authz))
        yield


class RequirePermPosTests(unittest.TestCase):
    def test_cashier_blocked_on_admin_code_403(self):
        cashier = {"tenant_id": "t", "id": "c", "role": "cashier", "is_super_admin": False}
        with mock.patch("core.pos_api.pos_auth", return_value=cashier):
            with self.assertRaises(PosError) as ctx:
                deps.require_perm_pos_tid(_Req(), "pos.admin.manage")
        self.assertEqual(ctx.exception.code, "pos.forbidden")
        self.assertEqual(ctx.exception.http_status, 403)


class PosWorkspaceGateTests(unittest.TestCase):
    def test_subject_requires_sale_permission(self):
        request = _Req()
        user = {"tenant_id": "t", "id": "u"}
        with mock.patch("services.authz.deps.require_perm_pos", return_value=user) as require_perm:
            self.assertEqual(pos_api.subject(request), (user, "t"))
        require_perm.assert_called_once_with(request, "pos.sale.operate")

    def test_pos_write_forwards_explicit_permission(self):
        request = _Req()
        user = {"tenant_id": "t", "id": "u", "workspace_client_id": 7}
        cursor = mock.MagicMock()
        cursor_context = mock.MagicMock()
        cursor_context.__enter__.return_value = cursor
        with (
            mock.patch.object(pos_api, "subject", return_value=(user, "t")) as subject,
            mock.patch.object(pos_api.db, "get_cursor_rls", return_value=cursor_context),
            mock.patch.object(pos_api, "assert_module_enabled"),
            mock.patch.object(pos_api, "require_workspace_access"),
        ):
            pos_api.pos_write(
                request,
                ws_override=None,
                write_fn=lambda *_args: {},
                permission="pos.shift.operate",
            )
        subject.assert_called_once_with(request, "pos.shift.operate")

    def test_workspace_gate_checks_assignment_after_tenant_ownership(self):
        request = _Req()
        cur = object()
        with (
            mock.patch.object(pos_api, "require_workspace") as require_workspace,
            mock.patch("services.authz.deps.check_request_scope") as check_scope,
        ):
            pos_api.require_workspace_access(cur, request, "t", 7)
        require_workspace.assert_called_once_with(cur, "t", 7)
        check_scope.assert_called_once_with(request, 7, pos=True)

    def test_unassigned_workspace_uses_pos_not_found(self):
        request = _Req()
        authz = Authz(
            role_key="member",
            permissions=frozenset({"pos.sale.operate"}),
            scope_mode="assigned",
            workspace_ids=frozenset({8}),
        )
        with (
            mock.patch.object(pos_api, "require_workspace"),
            mock.patch.object(deps, "_cached_authz", return_value=authz),
            mock.patch.object(deps, "_pos_token_payload", return_value=None),
            mock.patch("core.auth.get_current_user_from_request", return_value={"id": "u"}),
        ):
            with self.assertRaises(PosError) as ctx:
                pos_api.require_workspace_access(object(), request, "t", 7)
        self.assertEqual((ctx.exception.code, ctx.exception.http_status), ("pos.not_found", 404))

    def test_cashier_workspace_override_mismatch_is_forbidden(self):
        with self.assertRaises(PosError) as ctx:
            pos_api.resolve_ws({"workspace_client_id": 7}, 8)
        self.assertEqual((ctx.exception.code, ctx.exception.http_status), ("pos.forbidden", 403))


class RequirePermPosMatrixTests(unittest.TestCase):
    def test_cashier_allowed_on_cashier_code(self):
        cashier = {"tenant_id": "t", "id": "c", "role": "cashier", "is_super_admin": False}
        with mock.patch("core.pos_api.pos_auth", return_value=cashier):
            user = deps.require_perm_pos(_Req(), "pos.sale.operate")
        self.assertEqual(user["id"], "c")

    def test_owner_codes_allowed(self):
        owner = {"tenant_id": "t", "id": "u", "role": "owner"}
        with _gate(owner, *ALL_CODES):
            tid, uid = deps.require_perm_pos_tid(_Req(), "pos.admin.manage")
        self.assertEqual((tid, uid), ("t", "u"))

    def test_member_without_code_403(self):
        member = {"tenant_id": "t", "id": "m", "role": "member"}
        with _gate(member, "pos.report.view"):
            with self.assertRaises(PosError) as ctx:
                deps.require_perm_pos(_Req(), "pos.admin.manage")
        self.assertEqual(ctx.exception.code, "pos.forbidden")
        self.assertEqual(ctx.exception.http_status, 403)

    def test_super_admin_allowed_even_if_cashier_role(self):
        sa = {"tenant_id": "t", "id": "s", "role": "cashier", "is_super_admin": True}
        with mock.patch("core.pos_api.pos_auth", return_value=sa):
            tid, _uid = deps.require_perm_pos_tid(_Req(), "pos.admin.manage")
        self.assertEqual(tid, "t")

    def test_no_tenant_forbidden(self):
        with _gate({"id": "x", "role": "owner"}, *ALL_CODES):
            with self.assertRaises(PosError) as ctx:
                deps.require_perm_pos_tid(_Req(), "pos.admin.manage")
        self.assertEqual(ctx.exception.http_status, 403)

    def test_module_disabled_403(self):
        member = {"tenant_id": "t", "id": "m"}
        with _gate(member, *ALL_CODES, module_disabled=True):
            with self.assertRaises(PosError) as ctx:
                deps.require_perm_pos(_Req(), "inv.create")
        self.assertEqual(ctx.exception.code, "pos.module_disabled")
        self.assertEqual(ctx.exception.http_status, 403)


class WiringTests(unittest.TestCase):
    """库存写端/报表/开通逐条带码接线(收银员 token 调=403;防回归降级)。"""

    def test_inventory_read_write_codes(self):
        import routes.inventory_routes as inv

        self.assertIn('require_perm_pos_tid(request, "inv.view")', inspect.getsource(inv._read))
        self.assertIn("require_perm_pos_tid(request, code)", inspect.getsource(inv._write))
        self.assertIn('"inv.create"', inspect.getsource(inv.api_receive))
        self.assertIn('"inv.approve"', inspect.getsource(inv.api_count))
        self.assertIn('"inv.approve"', inspect.getsource(inv.api_adjust))

    def test_report_route_code(self):
        import routes.pos_report_routes as rep

        self.assertIn(
            'require_perm_pos_tid(request, "pos.report.view")', inspect.getsource(rep.api_report)
        )

    def test_onboarding_code(self):
        import routes.pos_auth_routes as auth

        self.assertIn(
            'require_perm_pos_tid(request, "settings.modules.manage")',
            inspect.getsource(auth.api_onboarding),
        )

    def test_sales_routes_use_shared_permission_and_workspace_gate(self):
        import routes.pos_sales_routes as sales

        self.assertIn("pos_api.subject(request)", inspect.getsource(sales._subject))
        self.assertIn("require_workspace_access", inspect.getsource(sales._read))

    def test_shift_routes_use_shift_permission(self):
        import routes.pos_shift_routes as shift

        self.assertIn('permission="pos.shift.operate"', inspect.getsource(shift.api_open_shift))
        self.assertIn(
            'subject(request, "pos.shift.operate")', inspect.getsource(shift.api_current_shift)
        )
        self.assertIn('permission="pos.shift.operate"', inspect.getsource(shift.api_close_shift))


if __name__ == "__main__":
    unittest.main()
