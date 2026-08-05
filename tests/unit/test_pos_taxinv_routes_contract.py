# -*- coding: utf-8 -*-
"""POS 补开全式税票路由守门(G2)。

锁定:路由 path+method 契约 · app include · POS 信封/模块守门 · 税号带出四态
(查到 found:true 归一字段 / 查不到 found:false 不走 4xx)· PDF 端点作用域
(未升级小票 404,不开放任意 doc_id)。"""

import unittest
from unittest.mock import patch

from starlette.requests import Request

import routes.pos_taxinv_routes as mod
from core.pos_api import PosError
from routes.pos_taxinv_routes import router

EXPECTED = {
    ("GET", "/api/pos/tax-lookup"),
    ("GET", "/api/pos/sales/{sale_id}/full-invoice-pdf"),
}


def _request():
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/pos/tax-lookup",
            "query_string": b"",
            "headers": [],
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )


class _CursorCtx:
    def __init__(self, cur=None):
        self._cur = cur if cur is not None else object()

    def __enter__(self):
        return self._cur

    def __exit__(self, exc_type, exc, tb):
        return False


def _pos_envelope_patches(cur=None):
    return (
        patch.object(
            mod.pos_api,
            "subject",
            return_value=({"tenant_id": "t-1", "workspace_client_id": 7}, "t-1"),
        ),
        patch.object(mod.pos_api, "resolve_ws", return_value=7),
        patch.object(mod.db, "get_cursor_rls", return_value=_CursorCtx(cur)),
        patch.object(mod, "assert_module_enabled"),
        patch.object(mod, "require_workspace_access"),
    )


class RoutesContractTests(unittest.TestCase):
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
            self.assertIn(p, paths, f"pos-taxinv route missing from app: {p}")

    def test_uses_pos_envelope_and_module_gate(self):
        self.assertTrue(hasattr(mod, "ok"))
        self.assertTrue(hasattr(mod, "assert_module_enabled"))
        self.assertTrue(hasattr(mod, "PosError"))
        self.assertTrue(hasattr(mod.pos_api, "subject"))


class TaxLookupTests(unittest.IsolatedAsyncioTestCase):
    async def test_found_returns_normalized_fields(self):
        rd = {
            "ok": True,
            "cached": False,
            "data": {
                "tax_id": "0107544000108",
                "name": "บริษัท ปตท. จำกัด (มหาชน)",
                "address": "555 ถ.วิภาวดีรังสิต กรุงเทพฯ",
                "branch_no": "00000",
                "branch_label": "สำนักงานใหญ่",
                "post_code": "10900",
                "province": "กรุงเทพมหานคร",
            },
        }
        with patch("services.rd.rd_api.lookup_vat", return_value=rd) as lv:
            p = _pos_envelope_patches()
            with p[0], p[1], p[2], p[3], p[4]:
                body = await mod.api_pos_tax_lookup(
                    _request(), tax_id="0107544000108", branch=0, workspace_client_id=7
                )
        self.assertTrue(body["ok"])
        self.assertTrue(body["data"]["found"])
        self.assertEqual(body["data"]["name"], "บริษัท ปตท. จำกัด (มหาชน)")
        self.assertTrue(body["data"]["vat_registered"])
        lv.assert_called_once_with("0107544000108", 0)

    async def test_not_found_is_honest_not_4xx(self):
        with patch("services.rd.rd_api.lookup_vat", return_value={"ok": False, "error": "timeout"}):
            p = _pos_envelope_patches()
            with p[0], p[1], p[2], p[3], p[4]:
                body = await mod.api_pos_tax_lookup(
                    _request(), tax_id="0105551234567", branch=0, workspace_client_id=7
                )
        self.assertTrue(body["ok"])  # 信封 ok:查询执行了
        self.assertFalse(body["data"]["found"])  # 结果诚实:没查到,端上转手填
        self.assertEqual(body["data"]["error"], "timeout")


class FullInvoicePdfTests(unittest.IsolatedAsyncioTestCase):
    async def test_not_upgraded_sale_404(self):
        with patch(
            "services.pos.sales_store.get_sale",
            return_value={"id": "s-1", "full_invoice_id": None},
        ):
            p = _pos_envelope_patches()
            with p[0], p[1], p[2], p[3], p[4]:
                with self.assertRaises(PosError) as ctx:
                    await mod.api_full_invoice_pdf(
                        "s-1", _request(), workspace_client_id=7, copy="original"
                    )
        self.assertEqual(ctx.exception.http_status, 404)

    async def test_upgraded_sale_returns_pdf_scoped_to_full_invoice_id(self):
        doc = {"id": "d-9", "doc_type": "tax_invoice"}
        with (
            patch(
                "services.pos.sales_store.get_sale",
                return_value={"id": "s-1", "full_invoice_id": "d-9"},
            ),
            patch("services.sales.document.get_document", return_value=doc) as gd,
            patch("services.sales.render.build_pdf", return_value=b"%PDF-fake") as bp,
        ):
            p = _pos_envelope_patches()
            with p[0], p[1], p[2], p[3], p[4]:
                resp = await mod.api_full_invoice_pdf(
                    "s-1", _request(), workspace_client_id=7, copy="bogus"
                )
        self.assertEqual(resp.media_type, "application/pdf")
        self.assertEqual(resp.body, b"%PDF-fake")
        # 作用域:doc_id 只能来自 sale.full_invoice_id,不吃请求参数
        self.assertEqual(gd.call_args.kwargs["doc_id"], "d-9")
        # 非法 copy 回落 original,不透传
        self.assertEqual(bp.call_args.kwargs["copy_kind"], "original")


if __name__ == "__main__":
    unittest.main()
