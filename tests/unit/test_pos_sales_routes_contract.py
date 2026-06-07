# -*- coding: utf-8 -*-
"""POS 收银前台路由守门测试(POS 项目 · PO-B2)。

锁定:14 条路由 path+method 契约 · app.py include · 路由用 POS 信封 + 模块守门。"""

import unittest

import routes.pos_sales_routes as mod
from routes.pos_sales_routes import router

EXPECTED = {
    ("GET", "/api/pos/bootstrap"),
    ("GET", "/api/pos/products"),
    ("GET", "/api/pos/products/by-barcode"),
    ("POST", "/api/pos/shifts/open"),
    ("POST", "/api/pos/shifts/{shift_id}/close"),
    ("POST", "/api/pos/sales"),
    ("POST", "/api/pos/sales/sync"),
    ("GET", "/api/pos/sales/by-receipt"),
    ("GET", "/api/pos/sales/{sale_id}"),
    ("POST", "/api/pos/sales/{sale_id}/refund"),
    ("POST", "/api/pos/sales/{sale_id}/void"),
    ("POST", "/api/pos/sales/{sale_id}/full-tax-invoice"),
    ("GET", "/api/pos/sales/{sale_id}/promptpay-qr"),
    ("GET", "/api/pos/sales/{sale_id}/receipt-pdf"),
}


class PosSalesRoutesContractTests(unittest.TestCase):
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
        for _m, p in EXPECTED:
            self.assertIn(p, paths, f"pos-sales route missing from app: {p}")

    def test_uses_pos_envelope_and_module_gate(self):
        self.assertTrue(hasattr(mod, "ok"))
        self.assertTrue(hasattr(mod, "assert_module_enabled"))
        self.assertTrue(hasattr(mod, "PosError"))
        self.assertTrue(hasattr(mod, "pos_auth"))


if __name__ == "__main__":
    unittest.main()
