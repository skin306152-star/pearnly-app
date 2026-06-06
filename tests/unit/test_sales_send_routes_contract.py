# -*- coding: utf-8 -*-
"""销项 PO-7 · 发送/分享路由契约守门。"""

import unittest

from routes.sales_send_routes import router

EXPECTED = {
    ("POST", "/api/sales/documents/{doc_id}/send"),
    ("GET", "/api/sales/documents/shared/{token}/pdf"),
}


class SalesSendRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PATCH", "PUT", "DELETE"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_app_includes_send_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/sales/documents/{doc_id}/send", paths)
        self.assertIn("/api/sales/documents/shared/{token}/pdf", paths)


if __name__ == "__main__":
    unittest.main()
