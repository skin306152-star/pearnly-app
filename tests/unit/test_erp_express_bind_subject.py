#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""守门测试 · Express 主体绑定卡(方向判不出的票绑账套主体 → 重推)。

绑定后写 history.workspace_client_id → 重推(更新原行,不新建)。校验主体归属、非 express 拒。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from core import db  # noqa: E402,F401
from services.erp import erp_push as _erp  # noqa: E402


@unittest.skipUnless(
    __import__("importlib").util.find_spec("fastapi") is not None,
    "fastapi not installed",
)
class ExpressBindSubjectRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os

        os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")
        import app  # noqa: F401
        from routes import erp_express_account_routes as erp_routes

        cls.app_module = app
        cls.erp_routes = erp_routes

    def _client(self):
        from fastapi.testclient import TestClient

        return TestClient(self.app_module.app)

    _UNSET = object()

    def _run(self, body, *, adapter="express", wc=_UNSET, bind_ok=True):
        app = self.app_module
        erp_routes = self.erp_routes
        log_row = {"id": "log-1", "status": "manual", "history_id": "h-1", "endpoint_id": "ep-1"}
        endpoint = {"id": "ep-1", "adapter": adapter, "config": {"account_set": "DATAT"}}
        if wc is self._UNSET:
            wc = {"id": 7, "name": "มานะชัย", "tax_id": "0994000333444"}
        push_result = {
            "success": False,
            "error_msg": "EXPRESS_QUEUED",
            "http_status": 202,
            "elapsed_ms": 5,
            "request_body": {"adapter": "express"},
        }
        bind_mock = MagicMock(return_value=bind_ok)
        push_mock = MagicMock(return_value=push_result)
        with (
            patch.object(erp_routes, "get_current_user_from_request", return_value={"id": "u"}),
            patch.object(erp_routes, "_check_push_access", return_value=None),
            patch.object(erp_routes, "_tid", return_value="t-1"),
            patch.object(app.db, "get_push_log_detail", return_value=log_row),
            patch.object(app.db, "get_erp_endpoint", return_value=endpoint),
            patch.object(app.db, "get_workspace_client", return_value=wc),
            patch.object(app.db, "update_history_workspace_client_id", bind_mock),
            patch.object(app.db, "get_ocr_history_detail", return_value={"id": "h-1"}),
            patch.object(app.db, "classify_push_status", return_value="pending"),
            patch.object(app.db, "counts_as_endpoint_success", return_value=True),
            patch.object(app.db, "increment_retry_count", MagicMock(return_value=2)),
            patch.object(app.db, "update_log_status_after_retry", MagicMock()),
            patch.object(app.db, "update_endpoint_stats", MagicMock()),
            patch.object(app.db, "update_history_push_status", MagicMock()),
            patch.object(_erp, "push_to_endpoint", push_mock),
        ):
            with self._client() as client:
                r = client.post("/api/erp/logs/log-1/express-bind-subject", json=body)
        return r, bind_mock, push_mock

    def test_bind_then_repush(self):
        r, bind_mock, push_mock = self._run({"workspace_client_id": 7})
        self.assertEqual(r.status_code, 200, r.text)
        b = r.json()
        self.assertTrue(b["ok"])
        self.assertTrue(b["bound"])
        self.assertEqual(b["status"], "pending")
        bind_mock.assert_called_once()
        self.assertEqual(bind_mock.call_args.args[:2], ("h-1", 7))
        push_mock.assert_called_once()

    def test_workspace_client_not_owned_rejected(self):
        r, bind_mock, push_mock = self._run({"workspace_client_id": 7}, wc=None)
        self.assertEqual(r.status_code, 404, r.text)
        bind_mock.assert_not_called()
        push_mock.assert_not_called()

    def test_non_express_rejected(self):
        r, bind_mock, _ = self._run({"workspace_client_id": 7}, adapter="mrerp")
        self.assertEqual(r.status_code, 400, r.text)
        bind_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
