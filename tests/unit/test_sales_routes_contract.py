# -*- coding: utf-8 -*-
"""销项 PO-4 · 单据路由契约守门测试。"""

import unittest

from routes.sales_routes import router

EXPECTED = {
    ("GET", "/api/sales/documents"),
    ("POST", "/api/sales/documents"),
    ("GET", "/api/sales/documents/{doc_id}"),
    ("PATCH", "/api/sales/documents/{doc_id}"),
    ("POST", "/api/sales/documents/{doc_id}/issue"),
    ("POST", "/api/sales/documents/{doc_id}/void"),
}


class SalesRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PATCH", "DELETE"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_app_includes_sales_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        for _m, p in EXPECTED:
            self.assertIn(p, paths, f"sales-document route missing from app: {p}")


if __name__ == "__main__":
    unittest.main()
