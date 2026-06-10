# -*- coding: utf-8 -*-
"""库存报表路由守门测试(POS 项目 · C1 · 批2:require_perm 统一执行点)。

锁定:GET /api/inventory/report 契约 · app.py include · POS 信封 + inv.report.view 带码守门
(收银员 token 不可调)+ 日期解析容错。"""

import inspect
import unittest
from datetime import date

import routes.inventory_report_routes as mod
from routes.inventory_report_routes import router


class InventoryReportRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_route(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PATCH", "DELETE", "PUT"):
                    got.add((m, r.path))
        self.assertEqual(got, {("GET", "/api/inventory/report")})

    def test_app_includes_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/inventory/report", paths)

    def test_uses_perm_gate_and_envelope(self):
        self.assertTrue(hasattr(mod, "ok"))
        self.assertTrue(hasattr(mod, "require_perm_pos_tid"))
        self.assertTrue(hasattr(mod, "assert_module_enabled"))
        self.assertIn(
            'require_perm_pos_tid(request, "inv.report.view")',
            inspect.getsource(mod.api_inventory_report),
        )

    def test_parse_date_tolerant(self):
        d = date(2026, 1, 1)
        self.assertEqual(mod._parse_date("2026-06-07", d).isoformat(), "2026-06-07")
        self.assertEqual(mod._parse_date(None, d), d)
        self.assertEqual(mod._parse_date("garbage", d), d)


if __name__ == "__main__":
    unittest.main()
