# -*- coding: utf-8 -*-
"""POS 交易明细日志路由契约(老板后台 · 按账套隔离 · view 级权限同报表)。"""

import inspect
import unittest
from unittest.mock import patch

from starlette.requests import Request


def _request(path="/api/pos/admin/sales-log"):
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "query_string": b"",
            "headers": [],
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )


class _CursorCtx:
    def __enter__(self):
        return object()

    def __exit__(self, exc_type, exc, tb):
        return False


class RoutesContractTests(unittest.TestCase):
    def test_router_registers_get_endpoints(self):
        from routes.pos_sales_log_routes import router

        paths = {r.path for r in router.routes}
        self.assertIn("/api/pos/admin/sales-log", paths)
        self.assertIn("/api/pos/admin/sales-log/export.csv", paths)

    def test_app_includes_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/pos/admin/sales-log", paths)
        self.assertIn("/api/pos/admin/sales-log/export.csv", paths)

    def test_view_level_permission_not_admin_manage(self):
        from routes import pos_sales_log_routes

        src = inspect.getsource(pos_sales_log_routes)
        self.assertIn('require_perm_pos_tid(request, "pos.report.view")', src)
        self.assertIn('assert_module_enabled(cur, tid, "pos")', src)
        self.assertIn("require_workspace", src)

    def test_csv_export_uses_safe_writer(self):
        from routes import pos_sales_log_routes

        src = inspect.getsource(pos_sales_log_routes)
        self.assertIn("SafeCsvWriter", src)

    def test_registered_in_agent_registry_as_app_exclusive(self):
        import json
        from pathlib import Path

        registry = json.loads(
            (Path(__file__).resolve().parents[2] / "docs/agent/agent_registry.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(registry.get("pos_sales_log_routes"), "C")


class ListRouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_list_passes_filters_through(self):
        from routes import pos_sales_log_routes as psr

        with (
            patch.object(
                psr,
                "require_perm_pos_tid",
                return_value=("t-1", "u-1"),
            ),
            patch.object(psr.db, "get_cursor_rls", return_value=_CursorCtx()),
            patch.object(psr, "assert_module_enabled"),
            patch.object(psr, "require_workspace"),
            patch.object(
                psr.svc,
                "list_sales",
                return_value={"items": [], "total": 0},
            ) as list_mock,
        ):
            body = await psr.api_sales_log(
                _request(),
                workspace_client_id=7,
                date_from="2026-07-01",
                date_to="2026-07-08",
                cashier_id="c9",
                lang="zh",
                limit=50,
                offset=10,
            )

        self.assertTrue(body["ok"])
        _, kwargs = list_mock.call_args
        self.assertEqual(kwargs["cashier_id"], "c9")
        self.assertEqual(kwargs["lang"], "zh")
        self.assertEqual(kwargs["limit"], 50)
        self.assertEqual(kwargs["offset"], 10)


class ExportRouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_export_returns_csv_with_attachment_header(self):
        from routes import pos_sales_log_routes as psr

        with (
            patch.object(
                psr,
                "require_perm_pos_tid",
                return_value=("t-1", "u-1"),
            ),
            patch.object(psr.db, "get_cursor_rls", return_value=_CursorCtx()),
            patch.object(psr, "assert_module_enabled"),
            patch.object(psr, "require_workspace"),
            patch.object(
                psr.svc,
                "export_rows",
                return_value=[
                    {
                        "receipt_no": "RCP-001",
                        "sold_at": "2026-07-08T09:16:11",
                        "cashier_name": "Earn",
                        "items": "บลัชออน x1",
                        "qty_total": "1",
                        "subtotal": "271.03",
                        "discount_total": "0",
                        "vat_amount": "18.97",
                        "grand_total": "290.00",
                        "method": "银行转账",
                        "paid_total": "300.00",
                        "change_amount": "10.00",
                        "shift_opened_at": "2026-07-08T08:00:00",
                        "shift_closed_at": "",
                    }
                ],
            ),
        ):
            resp = await psr.api_sales_log_export(
                _request("/api/pos/admin/sales-log/export.csv"),
                workspace_client_id=7,
                lang="zh",
            )

        self.assertIn("attachment", resp.headers["content-disposition"])
        body = resp.body.decode("utf-8-sig")
        self.assertIn("RCP-001", body)
        self.assertIn("Earn", body)
        self.assertIn("银行转账", body)


if __name__ == "__main__":
    unittest.main()
