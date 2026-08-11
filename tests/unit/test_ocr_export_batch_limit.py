# -*- coding: utf-8 -*-
"""export-by-history-ids 守门:数量上限 + 一次取数。

原实现在 `for hid in req.history_ids` 里逐条查详情(N 张票 = N 次查询 + N 次取游标),
且没有数量上限 —— 前端全选几千张就能把库拖垮。这里锁两条:超上限拒在查库之前、
批量只查一次;外加查不到的 id 照旧跳过(与逐条版返 None 等价)。
"""

import unittest
from unittest.mock import patch

from fastapi import HTTPException

from routes import ocr_export_routes as ox


def _req(ids):
    return ox.ExportByHistoryIdsRequest(history_ids=ids)


def _details(ids):
    return {str(i): {"id": str(i), "filename": f"{i}.pdf", "pages": []} for i in ids}


class ExportByHistoryIdsBatchTests(unittest.IsolatedAsyncioTestCase):
    async def test_over_limit_rejected_before_touching_db(self):
        ids = [f"h{i}" for i in range(ox.MAX_BATCH_SIZE + 1)]
        with (
            patch.object(ox, "get_current_user_from_request", return_value={"id": "u1"}),
            patch.object(
                ox.db,
                "get_ocr_history_details_bulk",
                side_effect=AssertionError("超上限必须拒在查库之前"),
            ),
        ):
            with self.assertRaises(HTTPException) as cm:
                await ox.ocr_export_by_history_ids(_req(ids), object())
        self.assertEqual(cm.exception.status_code, 400)
        self.assertEqual(cm.exception.detail, "export.batch_too_many")

    async def test_at_limit_reads_in_one_query(self):
        ids = [f"h{i}" for i in range(ox.MAX_BATCH_SIZE)]
        with (
            patch.object(ox, "get_current_user_from_request", return_value={"id": "u1"}),
            patch.object(ox.db, "get_ocr_history_details_bulk", return_value=_details(ids)) as spy,
            patch.object(ox, "_enrich_records_by_history_id", return_value=("", [])),
            patch(
                "services.excel.excel_template_th.build_sales_detail_xlsx",
                return_value=b"PK\x03\x04",
            ) as build,
        ):
            resp = await ox.ocr_export_by_history_ids(_req(ids), object())
        self.assertEqual(spy.call_count, 1)  # N+1 的守门:100 张也只查一次
        self.assertEqual(len(build.call_args[0][0]), ox.MAX_BATCH_SIZE)
        self.assertEqual(resp.body, b"PK\x03\x04")

    async def test_missing_ids_skipped_all_missing_is_404(self):
        with (
            patch.object(ox, "get_current_user_from_request", return_value={"id": "u1"}),
            patch.object(ox.db, "get_ocr_history_details_bulk", return_value=_details(["h1"])),
            patch.object(ox, "_enrich_records_by_history_id", return_value=("", [])),
            patch(
                "services.excel.excel_template_th.build_sales_detail_xlsx",
                return_value=b"PK\x03\x04",
            ) as build,
        ):
            await ox.ocr_export_by_history_ids(_req(["h1", "gone", "junk"]), object())
        self.assertEqual(len(build.call_args[0][0]), 1)

        with (
            patch.object(ox, "get_current_user_from_request", return_value={"id": "u1"}),
            patch.object(ox.db, "get_ocr_history_details_bulk", return_value={}),
        ):
            with self.assertRaises(HTTPException) as cm:
                await ox.ocr_export_by_history_ids(_req(["gone"]), object())
        self.assertEqual(cm.exception.status_code, 404)

    async def test_bulk_call_carries_tenant_scope(self):
        """tenant_id 照旧传下去 —— 老板看员工单据的既有能力不能因为改批量丢掉。"""
        with (
            patch.object(
                ox,
                "get_current_user_from_request",
                return_value={"id": "u1", "tenant_id": "t1"},
            ),
            patch.object(ox.db, "get_ocr_history_details_bulk", return_value={}) as spy,
        ):
            with self.assertRaises(HTTPException):
                await ox.ocr_export_by_history_ids(_req(["h1"]), object())
        self.assertEqual(spy.call_args[0][0], "u1")
        self.assertEqual(spy.call_args[0][2], "t1")


if __name__ == "__main__":
    unittest.main()
