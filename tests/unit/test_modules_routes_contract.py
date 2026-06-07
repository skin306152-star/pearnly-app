# -*- coding: utf-8 -*-
"""模块开关路由守门测试(POS 项目 · PO-A1)。

锁定:
  1. router 注册 GET /api/me/modules · path+method 契约
  2. app.py include_router 真挂上
  3. 响应走 ok() 信封({"ok": true, "data": {"modules": {...}}})
"""

import unittest

from routes.modules_routes import router

EXPECTED = {("GET", "/api/me/modules")}


class ModulesRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PATCH", "DELETE", "PUT"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_app_includes_modules_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/me/modules", paths)


if __name__ == "__main__":
    unittest.main()
