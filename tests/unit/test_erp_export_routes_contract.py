# -*- coding: utf-8 -*-
"""erp_export_routes 契约测试 · 下载 MR.ERP 批量导入 Excel 端点。

锁定:① 路由注册(子 router + erp_routes 聚合) ② 鉴权走 _check_push_access
③ history 不存在 → 404 ④ preflight 不合格 → 422(回错误码) ⑤ 合格 → 返回 xlsx 字节。
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


class ErpExportRoutesContractTests(unittest.IsolatedAsyncioTestCase):
    def test_route_registered_and_aggregated(self):
        path = ("GET", "/api/erp/mrerp-xlsx/{history_id}")
        self.assertIn(path, _paths(ex.router))
        self.assertIn(path, _paths(erp_routes.router))

    def test_uses_push_access_guard(self):
        # 与手动推送同一道准入闸(能推就能导)
        from routes import erp_routes_access

        self.assertIs(ex._check_push_access, erp_routes_access._check_push_access)

    async def test_history_not_found_404(self):
        with (
            patch.object(ex, "get_current_user_from_request", return_value={"id": "u1"}),
            patch.object(ex, "_check_push_access"),
            patch.object(ex, "_tid", return_value="t1"),
            patch.object(ex.db, "get_ocr_history_detail", return_value=None),
        ):
            with self.assertRaises(HTTPException) as cm:
                await ex.download_mrerp_xlsx("h1", object())
            self.assertEqual(cm.exception.status_code, 404)

    async def test_preflight_fail_returns_422_with_code(self):
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
                await ex.download_mrerp_xlsx("h1", object())
            self.assertEqual(cm.exception.status_code, 422)
            self.assertEqual(cm.exception.detail, "ERR_NO_CUSTOMER_MAPPING")

    async def test_success_returns_xlsx_bytes(self):
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
            resp = await ex.download_mrerp_xlsx("h1", object())
        self.assertEqual(resp.body, b"PK\x03\x04xlsx")
        self.assertIn("spreadsheetml", resp.media_type)
        self.assertIn("attachment", resp.headers["content-disposition"])


if __name__ == "__main__":
    unittest.main()
