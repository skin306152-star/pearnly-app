# -*- coding: utf-8 -*-
"""销项 §M7 · 开票设置路由契约守门测试。"""

import unittest

from routes.sales_settings_routes import router

EXPECTED = {
    ("GET", "/api/sales/settings"),
    ("PUT", "/api/sales/settings"),
}


class SalesSettingsRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PATCH", "PUT", "DELETE"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_app_includes_settings_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/sales/settings", paths)


if __name__ == "__main__":
    unittest.main()
