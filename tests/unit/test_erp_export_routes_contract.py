# -*- coding: utf-8 -*-
"""erp_export_routes 契约测试 · 批量下载 MR.ERP 导入 Excel 端点。

锁定:① 路由注册(子 router + erp_routes 聚合) ② 鉴权走 _check_push_access
③ 全部 preflight 不合格 → 422(回首个错误码) ④ 有合格 → 返回 xlsx 字节。
"""

import unittest
from unittest.mock import patch

from fastapi import HTTPException

from routes import erp_export_routes as ex
from routes import erp_routes


def _paths(r):
    out = set()
    for route in r.routes:
        for m in getattr(route, "methods", None) or set():
            out.add((m, route.path))
    return out


def _req(ids):
    return ex.MrerpXlsxBatchRequest(history_ids=ids)


class ErpExportRoutesContractTests(unittest.IsolatedAsyncioTestCase):
    def test_route_registered_and_aggregated(self):
        path = ("POST", "/api/erp/mrerp-xlsx-batch")
        self.assertIn(path, _paths(ex.router))
        self.assertIn(path, _paths(erp_routes.router))

    def test_uses_push_access_guard(self):
        from routes import erp_routes_access

        self.assertIs(ex._check_push_access, erp_routes_access._check_push_access)

    async def test_all_preflight_fail_returns_422(self):
        with (
            patch.object(ex, "get_current_user_from_request", return_value={"id": "u1"}),
            patch.object(ex, "_check_push_access"),
            patch.object(ex, "_tid", return_value="t1"),
            patch.object(ex.db, "get_ocr_history_detail", return_value={"id": "h1"}),
            patch.object(ex, "flatten_history_for_mrerp", return_value={}),
            patch.object(ex, "load_mrerp_mappings", return_value={}),
            patch.object(
                ex.mrerp_xlsx_generator,
                "validate_history_for_sales_credit",
                return_value=(False, "ERR_NO_CUSTOMER_MAPPING", []),
            ),
        ):
            with self.assertRaises(HTTPException) as cm:
                await ex.download_mrerp_xlsx_batch(_req(["h1"]), object())
            self.assertEqual(cm.exception.status_code, 422)
            self.assertEqual(cm.exception.detail, "ERR_NO_CUSTOMER_MAPPING")

    async def test_valid_returns_xlsx_bytes(self):
        with (
            patch.object(ex, "get_current_user_from_request", return_value={"id": "u1"}),
            patch.object(ex, "_check_push_access"),
            patch.object(ex, "_tid", return_value="t1"),
            patch.object(ex.db, "get_ocr_history_detail", return_value={"id": "h1"}),
            patch.object(ex, "flatten_history_for_mrerp", return_value={"client_id": 1}),
            patch.object(ex, "load_mrerp_mappings", return_value={}),
            patch.object(
                ex.mrerp_xlsx_generator,
                "validate_history_for_sales_credit",
                return_value=(True, None, []),
            ),
            patch.object(ex.mrerp_xlsx_generator, "generate_xlsx", return_value=b"PK\x03\x04xlsx"),
        ):
            resp = await ex.download_mrerp_xlsx_batch(_req(["h1", "h2"]), object())
        self.assertEqual(resp.body, b"PK\x03\x04xlsx")
        self.assertIn("spreadsheetml", resp.media_type)
        self.assertIn("attachment", resp.headers["content-disposition"])


if __name__ == "__main__":
    unittest.main()
