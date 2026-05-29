#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_erp_retry_update_and_skipped_dup.py

P2「状态单一真相」守门(第三十二会话 · Zihao 2026-05-27 拍板):
  - P2-A:手动重试**更新原行**(不再 INSERT 新行)→ 消除 A3 重复日志行。
  - P2-D:MR.ERP 返「发票号已存在/已推过」= skipped_dup 中性态(不算失败)→ B8。

为什么守:重试 INSERT 新行会让日志出现「旧失败行 + 新成功行」两条(A3),
还和异常队列口径打架(A4);发票号已存在被当失败会红叉吓用户(B8)。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
import erp_push as _erp  # noqa: E402

import db  # noqa: E402,F401  · 先 import db 再 import push_store(避免 partial-init 循环)
from services.erp.push_store import (  # noqa: E402
    is_already_pushed_error,
    classify_push_status,
)


class AlreadyPushedClassifierTests(unittest.TestCase):
    def test_thai_already_exists_patterns(self):
        self.assertTrue(is_already_pushed_error("เลขที่ดังกล่าวมีอยู่ในระบบแล้ว"))
        self.assertTrue(is_already_pushed_error("...เลขที่เอกสารซ้ำ..."))

    def test_err_duplicate_code(self):
        self.assertTrue(is_already_pushed_error("ERR_DUPLICATE_INVOICE"))
        self.assertTrue(is_already_pushed_error("push failed: ERR_DUPLICATE_INVOICE x"))

    def test_negatives(self):
        self.assertFalse(is_already_pushed_error(None))
        self.assertFalse(is_already_pushed_error(""))
        self.assertFalse(is_already_pushed_error("ERR_CUSTOMER_NAME_MISMATCH"))
        self.assertFalse(is_already_pushed_error("ไม่พบข้อมูลรหัสลูกค้า"))

    def test_classify_push_status(self):
        self.assertEqual(classify_push_status(True, None), "success")
        self.assertEqual(
            classify_push_status(True, "ERR_DUPLICATE_INVOICE"), "success"
        )  # success 优先
        self.assertEqual(
            classify_push_status(False, "เลขที่ดังกล่าวมีอยู่ในระบบแล้ว"), "skipped_dup"
        )
        self.assertEqual(classify_push_status(False, "ERR_DUPLICATE_INVOICE"), "skipped_dup")
        self.assertEqual(classify_push_status(False, "ERR_CUSTOMER_NAME_MISMATCH"), "failed")
        self.assertEqual(classify_push_status(False, None), "failed")


@unittest.skipUnless(
    __import__("importlib").util.find_spec("fastapi") is not None,
    "fastapi not installed — route-level test covered server-side.",
)
class RetryUpdatesOriginalRowTests(unittest.TestCase):
    """重试路由必须 UPDATE 原行 · 不许再 INSERT 新行。"""

    @classmethod
    def setUpClass(cls):
        import os

        os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")
        import app  # noqa: F401

        # R18(2026-05-29):retry 路由从 erp_routes 拆到 erp_push_log_routes ·
        # patch 目标随 handler 落点走(get_current_user/_check_push_access/_tid 都在该模块)。
        import erp_push_log_routes as erp_routes  # noqa: F401

        cls.app_module = app
        cls.erp_routes = erp_routes

    def _client(self):
        from fastapi.testclient import TestClient

        return TestClient(self.app_module.app)

    def _run_retry(self, push_result):
        app = self.app_module
        erp_routes = self.erp_routes
        log_row = {
            "id": "log-orig-1",
            "status": "failed",
            "history_id": "h-1",
            "endpoint_id": "ep-1",
            "attempt": 1,
            "next_retry_at": None,
        }
        insert_mock = MagicMock(return_value="SHOULD-NOT-BE-CALLED")
        update_mock = MagicMock()
        with (
            patch.object(
                erp_routes,
                "get_current_user_from_request",
                return_value={"id": "u", "plan": "pro"},
            ),
            patch.object(erp_routes, "_check_push_access", return_value=None),
            patch.object(erp_routes, "_tid", return_value="t-1"),
            patch.object(app.db, "get_push_log_detail", return_value=log_row),
            patch.object(
                app.db, "get_ocr_history_detail", return_value={"id": "h-1", "invoice_no": "INV-1"}
            ),
            patch.object(
                app.db, "get_erp_endpoint", return_value={"id": "ep-1", "adapter": "mrerp"}
            ),
            patch.object(app.db, "insert_push_log", insert_mock),
            patch.object(app.db, "increment_retry_count", MagicMock(return_value=2)),
            patch.object(app.db, "update_log_status_after_retry", update_mock),
            patch.object(app.db, "update_endpoint_stats", MagicMock()),
            patch.object(app.db, "update_history_push_status", MagicMock()),
            patch.object(_erp, "push_to_endpoint", MagicMock(return_value=push_result)),
        ):
            with self._client() as client:
                r = client.post("/api/erp/logs/log-orig-1/retry")
        return r, insert_mock, update_mock

    def test_retry_updates_does_not_insert(self):
        r, insert_mock, update_mock = self._run_retry(
            {"success": True, "http_status": 200, "elapsed_ms": 10}
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body.get("ok"))
        self.assertEqual(body.get("log_id"), "log-orig-1")  # 原行 id · 不是新行
        self.assertEqual(body.get("status"), "success")
        insert_mock.assert_not_called()  # ← A3 守门:绝不 INSERT 新行
        update_mock.assert_called_once()
        # 必须更新的是原行
        self.assertEqual(update_mock.call_args.kwargs.get("log_id"), "log-orig-1")

    def test_retry_already_exists_is_skipped_dup(self):
        r, insert_mock, update_mock = self._run_retry(
            {
                "success": False,
                "error_msg": "เลขที่ดังกล่าวมีอยู่ในระบบแล้ว",
                "http_status": 200,
                "elapsed_ms": 10,
            }
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body.get("status"), "skipped_dup")
        self.assertTrue(body.get("ok"))  # 已推送过 = 非失败
        insert_mock.assert_not_called()
        # update 用 final_status=skipped_dup
        self.assertEqual(update_mock.call_args.kwargs.get("final_status"), "skipped_dup")


if __name__ == "__main__":
    unittest.main()
