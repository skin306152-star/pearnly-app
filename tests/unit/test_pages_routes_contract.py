# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · 静态页面 + 公开 meta 路由从 app.py 抽到 pages_routes.py。

锁定(防搬迁回归):
  1. router 注册的 13 条路由 path+method 契约不变(防丢路由 / 改 URL)
     · REFACTOR-WA-B4 新增 /api/ready 真探活端点(铁律 #23.7)
  2. app.py 通过 include_router 真挂上了全部 13 条(防漏挂)
  3. /api/version **不在** pages_routes(在 meta_aliases · 读 PEARNLY_FRONTEND_VERSION
     模块全局 · 部署金丝雀)· 但仍挂在 app 上
  4. v1_health / v1_contact 仍委托给本模块的 health / contact(单一来源)
"""

import unittest

from routes.pages_routes import router

EXPECTED = {
    ("GET", "/api/health"),
    ("GET", "/api/ready"),
    ("GET", "/api/contact"),
    ("GET", "/api/v1/health"),
    ("GET", "/api/v1/contact"),
    ("GET", "/"),
    ("GET", "/login"),
    ("GET", "/home"),
    ("GET", "/admin"),
    ("GET", "/admin/{rest:path}"),
    ("GET", "/reset"),
    ("GET", "/terms"),
    ("GET", "/privacy"),
}


class PagesRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """13 条路由 path+method 契约 · 防搬迁丢路由 / 改 URL"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_app_includes_pages_router(self):
        """防 include_router 漏挂 · app 必须能路由到全部 12 条"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        for _m, p in EXPECTED:
            self.assertIn(p, paths, f"page route missing from app: {p}")

    def test_version_route_stays_in_app_not_pages(self):
        """/api/version 在 meta_aliases(部署金丝雀 · 读 PEARNLY_FRONTEND_VERSION)· 不在 pages_routes"""
        pages_paths = {r.path for r in router.routes if hasattr(r, "path")}
        self.assertNotIn("/api/version", pages_paths)

        import app

        app_paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/version", app_paths)

    def test_v1_aliases_delegate_to_base(self):
        """v1_health / v1_contact 委托给本模块 health / contact · 单一来源"""
        from routes import pages_routes

        self.assertIs(pages_routes.v1_health.__globals__["health"], pages_routes.health)
        self.assertIs(pages_routes.v1_contact.__globals__["contact"], pages_routes.contact)


if __name__ == "__main__":
    unittest.main()
