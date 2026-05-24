# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · 银行对账 11 路由从 app.py 抽到 bank_recon_routes.py。

锁定(防搬迁回归):
  1. router 注册的 11 个路由 path+method 契约不变(防丢路由 / 改 URL / 改 method)
  2. app.py 通过 include_router 真挂上了(防漏挂)
  3. dev seed/clear 的白名单常量 _TEST_USER_IDS 单一来源在 bank_recon_routes(防权限闸丢失)
  4. 路由依赖 auth.get_current_user_from_request(单一来源 · 防鉴权失踪)
"""

import unittest

import bank_recon_routes
from bank_recon_routes import _TEST_USER_IDS, router


class BankReconRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """路由 path+method 契约 · 防搬迁丢路由 / 改 URL / 改 method"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    got.add((m, r.path))
        expected = {
            ("POST", "/api/bank-recon/upload"),
            ("GET", "/api/bank-recon/sessions"),
            ("GET", "/api/bank-recon/stats"),
            ("GET", "/api/bank-recon/sessions/{session_id}"),
            ("DELETE", "/api/bank-recon/sessions/{session_id}"),
            ("POST", "/api/bank-recon/sessions/{session_id}/match"),
            ("POST", "/api/bank-recon/tx/{tx_id}/override"),
            ("GET", "/api/bank-recon/tx/{tx_id}/candidates"),
            ("PATCH", "/api/bank-recon/sessions/{session_id}/client"),
            ("POST", "/api/bank-recon/_dev/seed"),
            ("POST", "/api/bank-recon/_dev/clear"),
        }
        self.assertEqual(got, expected)

    def test_app_includes_bank_recon_router(self):
        """防 include_router 漏挂 · app 必须能路由到 bank-recon"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/bank-recon/upload", paths)
        self.assertIn("/api/bank-recon/sessions", paths)
        self.assertIn("/api/bank-recon/_dev/seed", paths)

    def test_dev_whitelist_constant_present(self):
        """dev seed/clear 白名单单一来源 · skin uid 仍在闸内(防权限闸丢失)"""
        self.assertIn("468b50c1-5593-4fd6-990d-515ce8085563", _TEST_USER_IDS)

    def test_routes_use_auth_dependency(self):
        """路由模块用 auth.get_current_user_from_request 单一来源(防鉴权失踪)"""
        import auth

        self.assertIs(
            bank_recon_routes.get_current_user_from_request,
            auth.get_current_user_from_request,
        )


if __name__ == "__main__":
    unittest.main()
