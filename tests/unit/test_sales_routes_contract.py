# -*- coding: utf-8 -*-
"""销项 PO-4 · 单据路由契约守门测试。"""

import unittest

from routes.sales_routes import router
from services.sales.record_enrichment import enrich, push_summary

EXPECTED = {
    ("GET", "/api/sales/documents"),
    ("POST", "/api/sales/documents"),
    ("GET", "/api/sales/documents/{doc_id}"),
    ("GET", "/api/sales/documents/{doc_id}/pdf"),
    ("PATCH", "/api/sales/documents/{doc_id}"),
    ("DELETE", "/api/sales/documents/{doc_id}"),
    ("POST", "/api/sales/documents/{doc_id}/issue"),
    ("POST", "/api/sales/documents/{doc_id}/void"),
    ("POST", "/api/sales/documents/{doc_id}/credit-note"),
    ("POST", "/api/sales/documents/{doc_id}/debit-note"),
    ("POST", "/api/sales/documents/{doc_id}/submit"),
    ("POST", "/api/sales/documents/{doc_id}/approve"),
    ("POST", "/api/sales/documents/{doc_id}/reject"),
    ("POST", "/api/sales/documents/{doc_id}/convert"),
    ("GET", "/api/sales/documents/{doc_id}/promptpay-qr"),
}


class SalesRoutesContractTests(unittest.TestCase):
    def test_sales_record_push_state_is_derived_from_existing_log_states(self):
        self.assertEqual(push_summary([]), "not_pushed")
        self.assertEqual(push_summary(["success", "skipped_dup"]), "success")
        self.assertEqual(push_summary(["pending"]), "pending")
        self.assertEqual(push_summary(["success", "failed"]), "failed")

    def test_sales_record_lineage_and_push_state_use_existing_sources(self):
        class Cursor:
            def __init__(self):
                self.results = [
                    [{"id": "h1", "source": "line_erp", "posting_kind": "mixed"}],
                    [
                        {
                            "history_id": "h1",
                            "status": "success",
                            "endpoint_name": "Express ERP",
                        }
                    ],
                ]

            def execute(self, _sql, _params=None):
                pass

            def fetchall(self):
                return self.results.pop(0)

        rows = [{"ocr_history_id": "h1"}]
        enrich(Cursor(), rows, tenant_id="t1", user_id="u1")
        self.assertEqual(rows[0]["source"], "line_erp")
        self.assertEqual(rows[0]["posting_kind"], "mixed")
        self.assertEqual(rows[0]["push_status"], "success")
        self.assertEqual(rows[0]["push_endpoints"], [{"name": "Express ERP", "status": "success"}])

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
