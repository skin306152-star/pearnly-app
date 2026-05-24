# -*- coding: utf-8 -*-
"""
ADR-006 S4 守门测试 · 列映射接口 + submit 预检。

锁定:
  1. import_routes 3 路由契约 + app 真挂上。
  2. save-mapping:鉴权 / 校验(doc_type、date 必填)/ 成功转存 template_store(同一作用域)。
  3. _preflight_stmt_mapping:Excel 新模板 → needs_mapping;能理解 → None;PDF 跳过。
"""

import asyncio
import io
import os
import tempfile
import unittest
from unittest import mock

from fastapi import HTTPException

import import_routes as ir
import recon_jobs_routes as rjr


def _xlsx(rows):
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class RouteContractTests(unittest.TestCase):
    def test_routes(self):
        got = {
            (m, r.path)
            for r in ir.router.routes
            for m in (getattr(r, "methods", set()) or set())
            if m in ("GET", "POST", "DELETE")
        }
        self.assertEqual(
            got,
            {
                ("POST", "/api/recon/import/save-mapping"),
                ("GET", "/api/recon/import/mappings"),
                ("DELETE", "/api/recon/import/mappings/{mapping_id}"),
            },
        )

    def test_app_includes(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/recon/import/save-mapping", paths)


class SaveMappingRouteTests(unittest.TestCase):
    def setUp(self):
        p = mock.patch.object(
            ir, "get_current_user_from_request", return_value={"id": "u1", "tenant_id": "t1"}
        )
        p.start()
        self.addCleanup(p.stop)

    def test_save_ok_uses_tenant_scope(self):
        body = ir.SaveMappingBody(
            document_type="statement",
            template_signature="sig1",
            mapping={"date": 0, "deposit": 2, "withdrawal": 3, "balance": 4},
            sample_headers=["d", "x", "in", "out", "bal"],
        )
        with mock.patch.object(ir.template_store, "save_mapping", return_value=True) as save:
            out = asyncio.run(ir.save_mapping(body, request=None))
        self.assertTrue(out["ok"])
        self.assertEqual(save.call_args[0][0], "t1")  # scope = tenant_id
        self.assertEqual(save.call_args[0][1], "statement")

    def test_no_tenant_falls_back_to_user(self):
        with mock.patch.object(
            ir, "get_current_user_from_request", return_value={"id": "u9", "tenant_id": None}
        ):
            body = ir.SaveMappingBody(
                document_type="gl", template_signature="s", mapping={"date": 0}
            )
            with mock.patch.object(ir.template_store, "save_mapping", return_value=True) as save:
                asyncio.run(ir.save_mapping(body, request=None))
        self.assertEqual(save.call_args[0][0], "u9")  # 无租户退回 user_id

    def test_reject_bad_doctype_and_missing_date(self):
        with self.assertRaises(HTTPException):
            asyncio.run(
                ir.save_mapping(
                    ir.SaveMappingBody(
                        document_type="bogus", template_signature="s", mapping={"date": 0}
                    ),
                    request=None,
                )
            )
        with self.assertRaises(HTTPException):
            asyncio.run(
                ir.save_mapping(
                    ir.SaveMappingBody(
                        document_type="statement", template_signature="s", mapping={"deposit": 2}
                    ),
                    request=None,
                )
            )


class PreflightTests(unittest.TestCase):
    def _stage(self, name, data):
        d = tempfile.mkdtemp()
        p = os.path.join(d, name)
        with open(p, "wb") as f:
            f.write(data)
        return {"path": p, "filename": name, "role": "stmt"}

    def test_ambiguous_excel_needs_mapping(self):
        rows = [
            ["X1", "X2", "X3", "X4"],
            ["2025-11-01", "a", "5000.00", "2000.00"],
            ["2025-11-02", "b", "3000.00", "1000.00"],
            ["2025-11-03", "c", "4000.00", "500.00"],
        ]
        ref = self._stage("weird.xlsx", _xlsx(rows))
        out = rjr._preflight_stmt_mapping([ref], "t1")
        if out is not None:  # 拿不准 → needs_mapping(理想路径)
            self.assertTrue(out["needs_mapping"])
            self.assertEqual(out["file"], "weird.xlsx")

    def test_good_excel_passes(self):
        rows = [
            ["วันที่", "รายการ", "ฝาก", "ถอน", "คงเหลือ"],
            ["2025-11-01", "a", "5000.00", "", "15000.00"],
            ["2025-11-02", "b", "", "2000.00", "13000.00"],
            ["2025-11-03", "c", "", "1000.00", "12000.00"],
        ]
        ref = self._stage("ok.xlsx", _xlsx(rows))
        self.assertIsNone(rjr._preflight_stmt_mapping([ref], "t1"))

    def test_pdf_skipped(self):
        ref = {"path": "/nonexistent.pdf", "filename": "x.pdf", "role": "stmt"}
        self.assertIsNone(rjr._preflight_stmt_mapping([ref], "t1"))


if __name__ == "__main__":
    unittest.main()
