# -*- coding: utf-8 -*-
"""POS 收银前台路由守门测试(POS 项目 · PO-B2)。

锁定:路由 path+method 契约 · app.py include · 路由用 POS 信封 + 模块守门。"""

import unittest
from unittest.mock import patch

from starlette.requests import Request

import routes.pos_sales_routes as mod
import services.pos.payment_settings as pay_settings
from routes.pos_sales_routes import router


def _request():
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/pos/payment-methods",
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


EXPECTED = {
    ("GET", "/api/pos/bootstrap"),
    ("GET", "/api/pos/products"),
    ("GET", "/api/pos/products/image/{name}"),
    ("GET", "/api/pos/products/by-barcode"),
    ("POST", "/api/pos/sales"),
    ("POST", "/api/pos/sales/sync"),
    ("GET", "/api/pos/sales/by-receipt"),
    ("GET", "/api/pos/sales/today"),
    ("GET", "/api/pos/sales/{sale_id}"),
    ("POST", "/api/pos/sales/{sale_id}/refund"),
    ("POST", "/api/pos/sales/{sale_id}/void"),
    ("POST", "/api/pos/sales/{sale_id}/full-tax-invoice"),
    ("GET", "/api/pos/sales/{sale_id}/promptpay-qr"),
    ("GET", "/api/pos/sales/{sale_id}/receipt-pdf"),
    ("GET", "/api/pos/promptpay-qr"),
    ("GET", "/api/pos/payment-methods"),
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
        self.assertTrue(hasattr(mod.pos_api, "subject"))


class PaymentMethodsRouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_cashier_readable_returns_settings(self):
        # 收银员 token(带 workspace_client_id · 无 admin 权限)即可读 → 走 _read 不是 owner admin 口。
        with (
            patch.object(
                mod.pos_api,
                "subject",
                return_value=({"tenant_id": "t-1", "workspace_client_id": 7}, "t-1"),
            ),
            patch.object(mod.db, "get_cursor_rls", return_value=_CursorCtx()),
            patch.object(mod, "assert_module_enabled"),
            patch.object(mod, "require_workspace_access"),
            patch.object(
                pay_settings,
                "get_settings",
                return_value={
                    "promptpay_enabled": True,
                    "card_enabled": True,
                    "bank_transfer_enabled": True,
                    "bank_name": "开泰银行",
                    "bank_account_no": "1234567890",
                    "bank_account_name": "Pearnly",
                    "promptpay_id": "0812345678",
                },
            ) as gs,
        ):
            body = await mod.api_payment_methods(_request(), workspace_client_id=7)

        self.assertTrue(body["ok"])
        self.assertTrue(body["data"]["bank_transfer_enabled"])
        self.assertEqual(body["data"]["bank_name"], "开泰银行")
        _, kwargs = gs.call_args
        self.assertEqual(kwargs["workspace_client_id"], 7)


if __name__ == "__main__":
    unittest.main()
