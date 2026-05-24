# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · ERP 连接器聚合 + Xero 8 路由从 app.py 抽到 erp_xero_routes.py。

锁定(防搬迁回归):
  1. router 注册的 8 个路由 path+method 契约不变(防丢路由 / 改 URL / 改 method)
  2. app.py 通过 include_router 真挂上了(防漏挂)
  3. owner/super 守门复用 route_helpers._require_owner_or_super 单一来源
  4. _tid / get_current_user_from_request 单一来源(防鉴权失踪)
  5. _ensure_fresh_xero_token 单一来源在 erp_xero_routes · app.py 自动推送复用的是同一个对象
"""

import unittest

import erp_xero_routes
import route_helpers
from erp_xero_routes import router


class ErpXeroRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """路由 path+method 契约 · 防搬迁丢路由 / 改 URL / 改 method"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    got.add((m, r.path))
        expected = {
            ("GET", "/api/erp/connectors/status"),
            ("GET", "/api/erp/xero/auth/start"),
            ("GET", "/api/erp/xero/auth/callback"),
            ("GET", "/api/erp/xero/status"),
            ("POST", "/api/erp/xero/auto-push"),
            ("POST", "/api/erp/xero/select_org"),
            ("POST", "/api/erp/xero/disconnect"),
            ("POST", "/api/erp/xero/push/{history_id}"),
        }
        self.assertEqual(got, expected)

    def test_app_includes_erp_xero_router(self):
        """防 include_router 漏挂 · app 必须能路由到连接器/Xero"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/erp/connectors/status", paths)
        self.assertIn("/api/erp/xero/auth/callback", paths)
        self.assertIn("/api/erp/xero/push/{history_id}", paths)

    def test_owner_guard_single_source(self):
        """owner/super 守门复用 route_helpers._require_owner_or_super 单一来源"""
        self.assertIs(
            erp_xero_routes._require_owner_or_super,
            route_helpers._require_owner_or_super,
        )

    def test_tid_and_auth_single_source(self):
        """_tid / get_current_user_from_request 单一来源(防鉴权失踪)"""
        import auth

        self.assertIs(erp_xero_routes._tid, route_helpers._tid)
        self.assertIs(
            erp_xero_routes.get_current_user_from_request,
            auth.get_current_user_from_request,
        )

    def test_ensure_fresh_token_single_source(self):
        """_ensure_fresh_xero_token 单一来源 · app.py 自动推送复用的就是本模块的同一对象"""
        import app

        self.assertIs(app._ensure_fresh_xero_token, erp_xero_routes._ensure_fresh_xero_token)


if __name__ == "__main__":
    unittest.main()
