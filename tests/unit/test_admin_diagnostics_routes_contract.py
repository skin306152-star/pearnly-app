# -*- coding: utf-8 -*-
"""
REFACTOR-D1 守门测试 · admin_diagnostics_routes.py(超管诊断 + 部署 webhook router)。

补缺(本模块此前无专属路由契约测试 · 8 硬门槛 #4 补齐):
  1. router 注册的 6 条路由 path+method 契约不变(防丢路由 / 改 URL)
  2. 本 router 无前缀(路径全绝对 · 含 /internal/* 部署链)· 防误加前缀
  3. app.py 通过 include_router 真挂上了全部 6 条(防漏挂)
  4. /internal/deploy(POST · GitHub webhook 入口)必须在(铁律:改 webhook 要停下问 ·
     此测试锁定它存在 · 防搬迁误删 → 自动部署链断)
  5. _read_last_500 / _require_super_admin 单一来源 = route_helpers(防各自再拷贝漂移)
"""

import unittest

from admin_diagnostics_routes import router

EXPECTED = {
    ("GET", "/api/admin/diagnostics/runtime"),
    ("POST", "/internal/deploy"),
    ("GET", "/internal/deploy/manual"),
    ("GET", "/internal/deploy/log"),
    ("GET", "/internal/install-playwright"),
    ("POST", "/internal/install-playwright"),
}


class AdminDiagnosticsRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """6 条路由 path+method 契约 · 防搬迁丢路由 / 改 URL"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_router_has_no_prefix(self):
        """本组路径全绝对(含 /internal/* 部署链)· router 不应带前缀"""
        self.assertEqual(router.prefix, "")

    def test_app_includes_admin_diagnostics_router(self):
        """防 include_router 漏挂 · app 必须能路由到全部 6 条"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        for _m, p in EXPECTED:
            self.assertIn(p, paths, f"diagnostics route missing from app: {p}")

    def test_deploy_webhook_present(self):
        """/internal/deploy(POST · GitHub webhook 部署入口)必须存在 · 防误删断部署链"""
        webhook = {
            (m, r.path)
            for r in router.routes
            if hasattr(r, "path")
            for m in (getattr(r, "methods", set()) or set())
        }
        self.assertIn(("POST", "/internal/deploy"), webhook)

    def test_shared_helpers_single_source(self):
        """_read_last_500 / _require_super_admin 必须复用 route_helpers · 单一来源防漂移"""
        import route_helpers
        import admin_diagnostics_routes as mod

        self.assertIs(mod._read_last_500, route_helpers._read_last_500)
        self.assertIs(mod._require_super_admin, route_helpers._require_super_admin)


if __name__ == "__main__":
    unittest.main()
