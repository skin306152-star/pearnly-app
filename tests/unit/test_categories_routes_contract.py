# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · /api/categories 单路由从 app.py 抽到 categories_routes.py。

锁定(防搬迁回归):
  1. router 注册的路由 path+method 契约不变(防丢路由 / 改 URL)
  2. app.py 通过 include_router 真挂上了(防漏挂)
  3. api_list_used_categories 复用 route_helpers._tid(单一来源 · 防各自一份副本漂移)
"""

import unittest

import route_helpers
from categories_routes import api_list_used_categories, router


class CategoriesRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """路由 path+method 契约 · 防搬迁丢路由 / 改 URL"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m == "GET":
                    got.add((m, r.path))
        self.assertEqual(got, {("GET", "/api/categories")})

    def test_app_includes_categories_router(self):
        """防 include_router 漏挂 · app 必须能路由到 categories"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/categories", paths)

    def test_uses_tid_from_route_helpers(self):
        """api_list_used_categories 依赖 route_helpers._tid · 单一来源"""
        self.assertIs(api_list_used_categories.__globals__["_tid"], route_helpers._tid)


if __name__ == "__main__":
    unittest.main()
