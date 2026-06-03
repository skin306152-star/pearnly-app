# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · 超管成本/收入/监控 10 路由从 app.py 抽到 admin_cost_routes.py。

锁定(防搬迁回归):
  1. router 注册的 10 个路由 path+method 契约不变(防丢路由 / 改 URL / 改 method)
  2. app.py 通过 include_router 真挂上了(防漏挂)
  3. 全部路由复用 route_helpers._require_super_admin 单一来源(防超管闸丢失)
"""

import unittest

from routes import admin_cost_routes
from core import route_helpers
from routes.admin_cost_routes import router


class AdminCostRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """路由 path+method 契约 · 防搬迁丢路由 / 改 URL / 改 method"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    got.add((m, r.path))
        expected = {
            ("GET", "/api/admin/cost/overview"),
            ("GET", "/api/admin/cost/debug"),
            ("GET", "/api/admin/cost/by_user"),
            ("GET", "/api/admin/cost/daily_trend"),
            ("GET", "/api/admin/credits/overview"),
            ("GET", "/api/admin/credits/tenants"),
            ("GET", "/api/admin/credits/daily_trend"),
            ("GET", "/api/admin/monitoring/overview"),
            ("GET", "/api/admin/credits/export"),
            ("GET", "/api/admin/cost/export"),
        }
        self.assertEqual(got, expected)

    def test_app_includes_admin_cost_router(self):
        """防 include_router 漏挂 · app 必须能路由到成本/收入/监控"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/admin/cost/overview", paths)
        self.assertIn("/api/admin/credits/export", paths)
        self.assertIn("/api/admin/monitoring/overview", paths)

    def test_super_admin_guard_single_source(self):
        """全部路由复用 route_helpers._require_super_admin 单一来源(防超管闸丢失)"""
        self.assertIs(
            admin_cost_routes._require_super_admin,
            route_helpers._require_super_admin,
        )


if __name__ == "__main__":
    unittest.main()
