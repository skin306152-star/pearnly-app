# -*- coding: utf-8 -*-
"""POS 收银员鉴权路由守门测试(POS 项目 · PO-B1)。

锁定:3 条路由 path+method 契约 · app.py include · 路由用 POS 信封 + onboarding 走 require_owner
(收银员 token 不可开通)· POS token 自含声明且不污染普通用户鉴权(_pos_token_subject)。"""

import os
import unittest

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

    def test_uses_pos_envelope_and_owner_gate(self):
        self.assertTrue(hasattr(mod, "ok"))
        self.assertTrue(hasattr(mod, "PosError"))
        self.assertTrue(hasattr(mod, "require_owner"))


class _Req:
    def __init__(self, token=None):
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}


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

    def test_require_owner_rejects_cashier_token(self):
        token, _ = core_auth.create_pos_token(
            tenant_id="t-1", workspace_client_id=9, cashier_id="c1", display_name="Nok"
        )
        with self.assertRaises(pos_api.PosError) as ctx:
            pos_api.require_owner(_Req(token))
        self.assertEqual(ctx.exception.code, "pos.forbidden")
        self.assertEqual(ctx.exception.http_status, 403)


if __name__ == "__main__":
    unittest.main()
