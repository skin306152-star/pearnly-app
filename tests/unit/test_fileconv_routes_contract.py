# -*- coding: utf-8 -*-
"""K1b 路由契约 · 财务文件转换端点(routes/fileconv_routes.py)。

锁定:①路由按 path+method 注册且挂进 app;②pearnly_ai_m1 闸关 → 404(fail-closed,
不泄漏端点存在性);③未登录 → 401;④超 20MB → 413;⑤happy path 打桩 convert_pdf 回
JSON 摘要(doc_type/status/conserved/stats/issue_count + issues 截断);⑥?format=xlsx
回 xlsx 附件(Content-Disposition);⑦no_text_layer → 200 + status 诚实返回,不是 500。
"""

from __future__ import annotations

import io
import unittest
from unittest import mock

from fastapi import HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from core import route_helpers
from routes import fileconv_routes as fcr
from routes.fileconv_routes import router as fileconv_router
from services.fileconv.model import (
    ConvertResult,
    Issue,
    GL_LEDGER,
    STATUS_NO_TEXT_LAYER,
    STATUS_OK,
)

_USER = {"id": "u1", "tenant_id": "t-1"}


def _upload(name="in.pdf", data=b"%PDF-1.4 test"):
    return UploadFile(filename=name, file=io.BytesIO(data))


def _ok_result(issues=None):
    return ConvertResult(
        doc_type=GL_LEDGER,
        status=STATUS_OK,
        source_name="in.pdf",
        issues=issues or [],
        stats={"row_count": 3, "closing_balance": "608917.35"},
    )


class RouteContractTests(unittest.TestCase):
    def test_expected_routes_registered(self):
        rs = {
            (m, r.path)
            for r in fileconv_router.routes
            for m in (getattr(r, "methods", set()) or set())
            if m in ("GET", "POST", "PUT", "PATCH", "DELETE")
        }
        self.assertEqual(rs, {("POST", "/api/fileconv/convert")})

    def test_mounted_in_app(self):
        import app  # noqa: F401

        paths = {getattr(r, "path", None) for r in app.app.routes}
        self.assertIn("/api/fileconv/convert", paths)


class GatedRouteCase(unittest.IsolatedAsyncioTestCase):
    """M1 闸 + 权限桩(照 test_client_pool_routes_contract 先例,patch route_helpers
    模块级名——authorize_pearnly_ai 引用的是它们)。"""

    def _wire(self, m1=True):
        patches = (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=m1),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
        )
        for p in patches:
            self.enterContext(p)


class GateTests(GatedRouteCase):
    async def test_m1_gate_closed_hides_route_as_404(self):
        self._wire(m1=False)
        with self.assertRaises(HTTPException) as ctx:
            await fcr.convert_endpoint(mock.Mock(), file=_upload(), fmt=None)
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "fileconv.not_found")

    async def test_unauthenticated_is_401(self):
        self.enterContext(
            mock.patch.object(
                route_helpers,
                "get_current_user_from_request",
                side_effect=HTTPException(401, detail="auth.missing_token"),
            )
        )
        with self.assertRaises(HTTPException) as ctx:
            await fcr.convert_endpoint(mock.Mock(), file=_upload(), fmt=None)
        self.assertEqual(ctx.exception.status_code, 401)


class SizeLimitTests(GatedRouteCase):
    async def test_oversize_upload_is_413(self):
        self._wire()
        big = _upload(data=b"x" * (fcr._MAX_BYTES + 1))
        with self.assertRaises(HTTPException) as ctx:
            await fcr.convert_endpoint(mock.Mock(), file=big, fmt=None)
        self.assertEqual(ctx.exception.status_code, 413)
        self.assertEqual(ctx.exception.detail, "fileconv.file_too_large")

    async def test_empty_upload_is_400(self):
        self._wire()
        with self.assertRaises(HTTPException) as ctx:
            await fcr.convert_endpoint(mock.Mock(), file=_upload(data=b""), fmt=None)
        self.assertEqual(ctx.exception.status_code, 400)


class SummaryTests(GatedRouteCase):
    async def test_happy_path_returns_summary_shape(self):
        self._wire()
        self.enterContext(mock.patch.object(fcr, "convert_pdf", return_value=_ok_result()))
        out = await fcr.convert_endpoint(mock.Mock(), file=_upload(), fmt=None)
        self.assertEqual(out["doc_type"], GL_LEDGER)
        self.assertEqual(out["status"], STATUS_OK)
        self.assertTrue(out["conserved"])
        self.assertEqual(out["issue_count"], 0)
        self.assertEqual(out["issues"], [])
        self.assertEqual(out["stats"]["closing_balance"], "608917.35")

    async def test_issues_are_named_and_truncated(self):
        self._wire()
        issues = [
            Issue(
                kind="gl_balance_chain",
                line_no=i,
                account="1113-01",
                message="ยอดไม่ตรง",
                expected="100.00",
                actual="99.00",
            )
            for i in range(fcr._ISSUES_PREVIEW + 5)
        ]
        self.enterContext(
            mock.patch.object(fcr, "convert_pdf", return_value=_ok_result(issues=issues))
        )
        out = await fcr.convert_endpoint(mock.Mock(), file=_upload(), fmt=None)
        self.assertFalse(out["conserved"])
        self.assertEqual(out["issue_count"], fcr._ISSUES_PREVIEW + 5)
        self.assertEqual(len(out["issues"]), fcr._ISSUES_PREVIEW)
        first = out["issues"][0]
        self.assertEqual(first["line_no"], 0)
        self.assertEqual(first["expected"], "100.00")
        self.assertEqual(first["actual"], "99.00")

    async def test_no_text_layer_is_200_with_honest_status(self):
        self._wire()
        rejected = ConvertResult(
            doc_type="",
            status=STATUS_NO_TEXT_LAYER,
            source_name="scan.pdf",
            stats={"reason": "无文字层(疑扫描件)· OCR 归 K1c"},
        )
        self.enterContext(mock.patch.object(fcr, "convert_pdf", return_value=rejected))
        out = await fcr.convert_endpoint(mock.Mock(), file=_upload(name="scan.pdf"), fmt=None)
        self.assertEqual(out["status"], STATUS_NO_TEXT_LAYER)
        self.assertEqual(out["issue_count"], 0)


class XlsxTests(GatedRouteCase):
    async def test_format_xlsx_returns_attachment(self):
        self._wire()
        self.enterContext(mock.patch.object(fcr, "convert_pdf", return_value=_ok_result()))
        self.enterContext(mock.patch.object(fcr, "build_xlsx", return_value=b"xlsx-bytes"))
        out = await fcr.convert_endpoint(mock.Mock(), file=_upload(name="GL TTB.pdf"), fmt="xlsx")
        self.assertIsInstance(out, StreamingResponse)
        self.assertEqual(
            out.media_type,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        disp = out.headers["Content-Disposition"]
        self.assertIn("attachment", disp)
        self.assertIn("filename*=UTF-8''GL%20TTB.xlsx", disp)

    async def test_thai_filename_survives_header_encoding(self):
        # HTTP 头只认 latin-1——泰文原名必须走 RFC 5987 filename*,裸塞会在响应编码时崩。
        self._wire()
        self.enterContext(mock.patch.object(fcr, "convert_pdf", return_value=_ok_result()))
        self.enterContext(mock.patch.object(fcr, "build_xlsx", return_value=b"x"))
        out = await fcr.convert_endpoint(
            mock.Mock(), file=_upload(name="สมุดแยกประเภท.pdf"), fmt="xlsx"
        )
        disp = out.headers["Content-Disposition"]
        disp.encode("latin-1")  # 编不过 = 生产 500,直接让测试红
        self.assertIn("filename*=UTF-8''", disp)


class XlsxFilenameTests(unittest.TestCase):
    def test_windows_reserved_chars_replaced(self):
        self.assertEqual(fcr._xlsx_filename('a<b>:"c.pdf'), "a_b___c.xlsx")

    def test_empty_name_falls_back(self):
        self.assertEqual(fcr._xlsx_filename(""), "convert.xlsx")
        self.assertEqual(fcr._xlsx_filename(".pdf"), "convert.xlsx")


if __name__ == "__main__":
    unittest.main()
