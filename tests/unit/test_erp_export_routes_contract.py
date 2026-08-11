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


def _bulk(found=None):
    """db.get_ocr_history_details_bulk 桩 · 签名与真函数一致,只回 found 里有的 id。
    found=None → 每个请求的 id 都当查得到。"""

    def _fn(user_id, history_ids, tenant_id=None, workspace_client_id=None):
        if found is None:
            return {str(h): {"id": str(h)} for h in history_ids}
        return {str(h): found[str(h)] for h in history_ids if str(h) in found}

    return _fn


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
            patch.object(
                ex.db, "get_ocr_history_details_bulk", side_effect=_bulk({"h1": {"id": "h1"}})
            ),
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
            patch.object(ex.db, "get_ocr_history_details_bulk", side_effect=_bulk()),
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


class BatchSizeLimitTests(unittest.IsolatedAsyncioTestCase):
    """上限 + 单次取数 · 超上限要在碰库之前就拒掉。"""

    async def test_over_limit_rejected_before_touching_db(self):
        bulk = _bulk()
        with (
            patch.object(ex, "get_current_user_from_request", return_value={"id": "u1"}),
            patch.object(ex, "_check_push_access"),
            patch.object(ex, "_tid", return_value="t1"),
            patch.object(ex.db, "get_ocr_history_details_bulk", side_effect=bulk) as spy,
            patch.object(ex, "load_mrerp_mappings", return_value={}),
        ):
            ids = [f"h{i}" for i in range(ex.MAX_BATCH_SIZE + 1)]
            with self.assertRaises(HTTPException) as cm:
                await ex.download_mrerp_xlsx_batch(_req(ids), object())
        self.assertEqual(cm.exception.status_code, 400)
        self.assertEqual(cm.exception.detail, "erp.batch_too_many")
        self.assertEqual(spy.call_count, 0)  # 拒在查库之前 · 别先把几千张读出来再说

    async def test_at_limit_passes_and_reads_in_one_query(self):
        with (
            patch.object(ex, "get_current_user_from_request", return_value={"id": "u1"}),
            patch.object(ex, "_check_push_access"),
            patch.object(ex, "_tid", return_value="t1"),
            patch.object(ex.db, "get_ocr_history_details_bulk", side_effect=_bulk()) as spy,
            patch.object(ex, "flatten_history_for_mrerp", return_value={"client_id": 1}),
            patch.object(ex, "load_mrerp_mappings", return_value={}),
            patch.object(
                ex.mrerp_xlsx_generator,
                "validate_history_for_sales_credit",
                return_value=(True, None, []),
            ),
            patch.object(ex.mrerp_xlsx_generator, "generate_xlsx", return_value=b"PK\x03\x04xlsx"),
        ):
            ids = [f"h{i}" for i in range(ex.MAX_BATCH_SIZE)]
            resp = await ex.download_mrerp_xlsx_batch(_req(ids), object())
        self.assertEqual(resp.body, b"PK\x03\x04xlsx")
        self.assertEqual(spy.call_count, 1)  # N+1 的守门:100 张也只查一次

    async def test_missing_ids_are_skipped_not_fatal(self):
        """查不到的 id 跳过、其余照常出表 —— 与逐条版 detail 返回 None 同语义。"""
        with (
            patch.object(ex, "get_current_user_from_request", return_value={"id": "u1"}),
            patch.object(ex, "_check_push_access"),
            patch.object(ex, "_tid", return_value="t1"),
            patch.object(
                ex.db,
                "get_ocr_history_details_bulk",
                side_effect=_bulk({"h1": {"id": "h1"}}),
            ),
            patch.object(ex, "flatten_history_for_mrerp", return_value={"client_id": 1}),
            patch.object(ex, "load_mrerp_mappings", return_value={}),
            patch.object(
                ex.mrerp_xlsx_generator,
                "validate_history_for_sales_credit",
                return_value=(True, None, []),
            ),
            patch.object(ex.mrerp_xlsx_generator, "generate_xlsx") as gen,
        ):
            gen.return_value = b"PK\x03\x04xlsx"
            await ex.download_mrerp_xlsx_batch(_req(["h1", "not-a-uuid", "h9"]), object())
        self.assertEqual(len(gen.call_args[0][0]), 1)  # 只有 h1 进文件


if __name__ == "__main__":
    unittest.main()
