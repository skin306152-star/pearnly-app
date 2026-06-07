# -*- coding: utf-8 -*-
"""库存路由守门测试(POS 项目 · PO-A3)。

锁定:6 条路由 path+method 契约 · app.py include · 路由用 POS 信封(import ok/PosError)+
模块开关守门(assert_module_enabled)。
"""

import unittest

import routes.inventory_routes as mod
from routes.inventory_routes import router

EXPECTED = {
    ("GET", "/api/inventory/warehouses"),
    ("GET", "/api/inventory/stock"),
    ("GET", "/api/inventory/near-expiry"),
    ("POST", "/api/inventory/in"),
    ("POST", "/api/inventory/count"),
    ("POST", "/api/inventory/adjust"),
}


class InventoryRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PATCH", "DELETE", "PUT"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_app_includes_inventory_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        for _m, p in EXPECTED:
            self.assertIn(p, paths, f"inventory route missing from app: {p}")

    def test_uses_pos_envelope_and_module_gate(self):
        # 信封 + 模块守门从 core.pos_api 引入(POS/库存统一信封)
        self.assertTrue(hasattr(mod, "ok"))
        self.assertTrue(hasattr(mod, "assert_module_enabled"))
        self.assertTrue(hasattr(mod, "PosError"))


if __name__ == "__main__":
    unittest.main()
