# -*- coding: utf-8 -*-
"""
REFACTOR-D1 守门测试 · report_routes.py(v109 报告 / 模板导出 router)。

补缺(本模块此前 0 测试覆盖 · 8 硬门槛 #4「每拆一个模块必带守门测试」补齐):
  1. router 注册的 4 条路由 path+method 契约不变(防丢路由 / 改 URL)
  2. router 前缀 = /api/reports(防搬迁误改前缀)
  3. app.py 通过 include_router 真挂上了全部 4 条(防漏挂)
"""

import unittest
from unittest.mock import patch

from fastapi import HTTPException

from routes import report_routes as rr
from routes.report_routes import router

EXPECTED = {
    ("GET", "/api/reports/templates"),
    ("POST", "/api/reports/export"),
    ("GET", "/api/reports/clients/{client_id}/export"),
    ("POST", "/api/reports/history/batch_export"),
}


class ReportRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """4 条路由 path+method 契约 · 防搬迁丢路由 / 改 URL"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_router_prefix(self):
        """前缀 /api/reports 固定 · 防误改导致前端全 404"""
        self.assertEqual(router.prefix, "/api/reports")

    def test_app_includes_report_router(self):
        """防 include_router 漏挂 · app 必须能路由到全部 4 条"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        for _m, p in EXPECTED:
            self.assertIn(p, paths, f"report route missing from app: {p}")


def _req(ids, template="standard"):
    return rr.HistoryBatchExportRequest(history_ids=ids, template=template, lang="zh")


class BatchExportSizeAndFetchTests(unittest.TestCase):
    """批量导出:数量上限 + 一次取数(原先逐条查 = N+1)。"""

    def test_over_limit_rejected_before_touching_db(self):
        ids = [f"h{i}" for i in range(rr.MAX_BATCH_SIZE + 1)]
        with (
            patch("core.auth.get_current_user_from_request", return_value={"id": "u1"}),
            patch(
                "core.db.get_ocr_history_details_bulk",
                side_effect=AssertionError("超上限必须拒在查库之前"),
            ),
        ):
            with self.assertRaises(HTTPException) as cm:
                rr.batch_export_history(_req(ids), object())
        self.assertEqual(cm.exception.status_code, 400)
        self.assertEqual(cm.exception.detail, "reports.batch_too_many")

    def test_at_limit_reads_in_one_query_and_keeps_order(self):
        ids = [f"h{i}" for i in range(rr.MAX_BATCH_SIZE)]
        details = {i: {"id": i, "pages": []} for i in ids}
        with (
            patch("core.auth.get_current_user_from_request", return_value={"id": "u1"}),
            patch("core.db.get_ocr_history_details_bulk", return_value=details) as spy,
            patch.object(rr, "build_report", return_value=b"xlsx") as build,
        ):
            resp = rr.batch_export_history(_req(ids), object())
        self.assertEqual(spy.call_count, 1)  # N+1 的守门:100 条也只查一次
        rows = build.call_args[0][1]
        self.assertEqual([r["id"] for r in rows], ids)  # 顺序照传入的来
        self.assertEqual(resp.status_code, 200)

    def test_missing_ids_skipped_and_all_missing_is_404(self):
        with (
            patch("core.auth.get_current_user_from_request", return_value={"id": "u1"}),
            patch(
                "core.db.get_ocr_history_details_bulk",
                return_value={"h1": {"id": "h1", "pages": []}},
            ),
            patch.object(rr, "build_report", return_value=b"xlsx") as build,
        ):
            rr.batch_export_history(_req(["h1", "gone", "junk"]), object())
            self.assertEqual(len(build.call_args[0][1]), 1)

        with (
            patch("core.auth.get_current_user_from_request", return_value={"id": "u1"}),
            patch("core.db.get_ocr_history_details_bulk", return_value={}),
        ):
            with self.assertRaises(HTTPException) as cm:
                rr.batch_export_history(_req(["gone"]), object())
        self.assertEqual(cm.exception.status_code, 404)

    def test_bulk_call_stays_user_scoped(self):
        """不传 tenant_id:与逐条版同口径,老板不会因为改批量就看到员工的单据。"""
        with (
            patch("core.auth.get_current_user_from_request", return_value={"id": "u1"}),
            patch("core.db.get_ocr_history_details_bulk", return_value={}) as spy,
        ):
            with self.assertRaises(HTTPException):
                rr.batch_export_history(_req(["h1"]), object())
        self.assertEqual(spy.call_args[0][0], "u1")
        self.assertNotIn("tenant_id", spy.call_args[1])


if __name__ == "__main__":
    unittest.main()
