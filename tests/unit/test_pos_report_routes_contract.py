# -*- coding: utf-8 -*-
"""POS 销售报表路由守门测试(POS 项目 · PO-B6)。

锁定:GET /api/pos/admin/report 契约 · app.py include · 用 POS 信封 + require_owner 守门
(收银员不可调报表)+ 日期解析容错。"""

import unittest

import routes.pos_report_routes as mod
from routes.pos_report_routes import router

EXPECTED = {("GET", "/api/pos/admin/report")}


class PosReportRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PATCH", "DELETE", "PUT"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_app_includes_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/pos/admin/report", paths)

    def test_uses_owner_gate_and_envelope(self):
        self.assertTrue(hasattr(mod, "ok"))
        self.assertTrue(hasattr(mod, "require_owner"))
        self.assertTrue(hasattr(mod, "assert_module_enabled"))

    def test_parse_date_tolerant(self):
        self.assertEqual(mod._parse_date("2026-06-07").isoformat(), "2026-06-07")
        self.assertIsNone(mod._parse_date(None))
        self.assertIsNone(mod._parse_date(""))
        self.assertIsNone(mod._parse_date("garbage"))


if __name__ == "__main__":
    unittest.main()
