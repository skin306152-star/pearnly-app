# -*- coding: utf-8 -*-
"""POS 收银员鉴权路由守门测试(POS 项目 · PO-B1 · 批2:require_perm 统一执行点)。

锁定:路由 path+method 契约 · app.py include · POS 信封 + 管理端点逐条带码
(pos.admin.manage / 开通=settings.modules.manage · 收银员 token 不可调)· POS token
自含声明且不污染普通用户鉴权(_pos_token_subject)。"""

import inspect
import os
import unittest
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-of-sufficient-length")

import routes.pos_auth_routes as mod  # noqa: E402
from core import auth as core_auth, pos_api  # noqa: E402
from routes.pos_auth_routes import router  # noqa: E402

EXPECTED = {
    ("GET", "/api/pos/cashiers"),
    ("POST", "/api/pos/auth/pin"),
    ("PUT", "/api/pos/admin/onboarding"),
    # 收银员后台管理(owner · 加人/改名换色/重设PIN/启停/删除未开班者)
    ("GET", "/api/pos/admin/cashiers"),
    ("POST", "/api/pos/admin/cashiers"),
    ("PUT", "/api/pos/admin/cashiers/{cashier_id}"),
    ("DELETE", "/api/pos/admin/cashiers/{cashier_id}"),
    # 收银台设备绑定(店铺码)· 收银员任意设备 PIN 登录
    ("POST", "/api/pos/bind"),
    ("GET", "/api/pos/admin/store-code"),
    ("POST", "/api/pos/admin/store-code/reset"),
}


class PosAuthRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PATCH", "DELETE", "PUT"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_app_includes_pos_auth_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        for _m, p in EXPECTED:
            self.assertIn(p, paths, f"pos-auth route missing from app: {p}")

    def test_uses_pos_envelope_and_perm_gate(self):
        self.assertTrue(hasattr(mod, "ok"))
        self.assertTrue(hasattr(mod, "PosError"))
        self.assertTrue(hasattr(mod, "require_perm_pos_tid"))

    def test_admin_handlers_pin_perm_codes(self):
        # 管理 7 端点逐条带码:6 条 pos.admin.manage + 开通 settings.modules.manage
        for fn in (
            mod.api_get_store_code,
            mod.api_reset_store_code,
            mod.api_admin_list_cashiers,
            mod.api_admin_create_cashier,
            mod.api_admin_update_cashier,
            mod.api_admin_delete_cashier,
        ):
            self.assertIn(
                'require_perm_pos_tid(request, "pos.admin.manage")',
                inspect.getsource(fn),
                fn.__name__,
            )
        self.assertIn(
            'require_perm_pos_tid(request, "settings.modules.manage")',
            inspect.getsource(mod.api_onboarding),
        )

    def test_public_endpoints_not_perm_gated(self):
        # 公开端点(bind/cashiers/auth/pin)自含校验(店铺码/店铺令牌/PIN),不走 require_perm
        for fn in (mod.api_bind_device, mod.api_list_cashiers, mod.api_pin_login):
            self.assertNotIn("require_perm", inspect.getsource(fn), fn.__name__)


class _Req:
    def __init__(self, token=None):
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}


class _StoreCursor:
    pass


class StoreTokenBoundaryTests(unittest.TestCase):
    def test_cashier_access_requires_store_token(self):
        with self.assertRaises(pos_api.PosError) as ctx:
            mod._workspace_from_store_token(_StoreCursor(), _Req(), None)
        self.assertEqual(ctx.exception.code, "pos.store_unbound")
        self.assertEqual(ctx.exception.http_status, 401)

    def test_workspace_id_without_any_identity_is_rejected(self):
        with self.assertRaises(pos_api.PosError) as ctx:
            mod._workspace_from_store_token(_StoreCursor(), _Req(), 9)
        self.assertEqual(ctx.exception.http_status, 401)

    def test_request_workspace_must_match_store_token(self):
        token = core_auth.create_pos_store_token(tenant_id="t-1", workspace_client_id=9, version=3)
        with mock.patch.object(mod.store_binding, "current_version", return_value=3):
            with self.assertRaises(pos_api.PosError) as ctx:
                mod._workspace_from_store_token(_StoreCursor(), _Req(token), 10)
        self.assertEqual(ctx.exception.code, "pos.forbidden")
        self.assertEqual(ctx.exception.http_status, 403)

    def test_store_token_workspace_is_authoritative(self):
        token = core_auth.create_pos_store_token(tenant_id="t-1", workspace_client_id=9, version=3)
        with mock.patch.object(mod.store_binding, "current_version", return_value=3):
            self.assertEqual(
                mod._workspace_from_store_token(_StoreCursor(), _Req(token), 9),
                ("t-1", 9),
            )

    def test_revoked_store_token_wins_over_workspace_mismatch(self):
        token = core_auth.create_pos_store_token(tenant_id="t-1", workspace_client_id=9, version=3)
        with mock.patch.object(mod.store_binding, "current_version", return_value=4):
            with self.assertRaises(pos_api.PosError) as ctx:
                mod._workspace_from_store_token(_StoreCursor(), _Req(token), 10)
        self.assertEqual(ctx.exception.code, "pos.store_unbound")
        self.assertEqual(ctx.exception.http_status, 401)

    def test_authorized_platform_member_can_use_selected_workspace(self):
        user = {"id": "u-1", "tenant_id": "t-1", "role": "owner"}
        with (
            mock.patch.object(mod, "require_perm_pos", return_value=user),
            mock.patch.object(mod, "require_workspace") as require_workspace,
            mock.patch.object(mod, "check_workspace_scope") as check_scope,
        ):
            result = mod._workspace_from_store_token(_StoreCursor(), _Req("user-jwt"), 9)
        self.assertEqual(result, ("t-1", 9))
        require_workspace.assert_called_once_with(mock.ANY, "t-1", 9)
        check_scope.assert_called_once_with(mock.ANY, user, 9, pos=True)

    def test_platform_member_without_pos_permission_is_rejected(self):
        denied = pos_api.PosError("pos.forbidden", 403)
        with mock.patch.object(mod, "require_perm_pos", side_effect=denied):
            with self.assertRaises(pos_api.PosError) as ctx:
                mod._workspace_from_store_token(_StoreCursor(), _Req("user-jwt"), 9)
        self.assertEqual(ctx.exception.code, "pos.forbidden")

    def test_assigned_workspace_scope_is_enforced(self):
        user = {"id": "u-1", "tenant_id": "t-1", "role": "member"}
        denied = pos_api.PosError("pos.not_found", 404)
        with (
            mock.patch.object(mod, "require_perm_pos", return_value=user),
            mock.patch.object(mod, "require_workspace"),
            mock.patch.object(mod, "check_workspace_scope", side_effect=denied),
        ):
            with self.assertRaises(pos_api.PosError) as ctx:
                mod._workspace_from_store_token(_StoreCursor(), _Req("user-jwt"), 9)
        self.assertEqual(ctx.exception.code, "pos.not_found")


class PosTokenSubjectTests(unittest.TestCase):
    def test_pos_token_yields_synthetic_subject(self):
        token, _ttl = core_auth.create_pos_token(
            tenant_id="t-1", workspace_client_id=9, cashier_id="c1", display_name="Nok"
        )
        subj = pos_api._pos_token_subject(_Req(token))
        self.assertEqual(subj["tenant_id"], "t-1")
        self.assertEqual(subj["workspace_client_id"], 9)
        self.assertEqual(subj["cashier_id"], "c1")
        self.assertEqual(subj["role"], "cashier")
        self.assertFalse(subj["is_super_admin"])

    def test_non_pos_token_returns_none(self):
        # 普通用户 token 不带 typ='pos' → 不被 POS 分流接管
        user_token = core_auth.create_access_token(
            user_id="u1", username="boss", plan="free", tenant_id="t", role="owner"
        )
        self.assertIsNone(pos_api._pos_token_subject(_Req(user_token)))

    def test_no_auth_header_returns_none(self):
        self.assertIsNone(pos_api._pos_token_subject(_Req()))

    def test_perm_gate_rejects_cashier_token_for_admin_code(self):
        from services.authz.deps import require_perm_pos

        token, _ = core_auth.create_pos_token(
            tenant_id="t-1", workspace_client_id=9, cashier_id="c1", display_name="Nok"
        )
        with self.assertRaises(pos_api.PosError) as ctx:
            require_perm_pos(_Req(token), "pos.admin.manage")
        self.assertEqual(ctx.exception.code, "pos.forbidden")
        self.assertEqual(ctx.exception.http_status, 403)

    def test_perm_gate_allows_cashier_token_for_cashier_code(self):
        from services.authz.deps import require_perm_pos

        token, _ = core_auth.create_pos_token(
            tenant_id="t-1", workspace_client_id=9, cashier_id="c1", display_name="Nok"
        )
        subj = require_perm_pos(_Req(token), "pos.sale.operate")
        self.assertEqual(subj["role"], "cashier")
        self.assertEqual(subj["tenant_id"], "t-1")


if __name__ == "__main__":
    unittest.main()
