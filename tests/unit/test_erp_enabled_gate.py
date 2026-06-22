#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Express FE-2 · 停用端点(enabled=False)推送闸回归守门。

连接卡的「启用/停用」开关沿用 endpoint.enabled。停用后两条路必须不通:
  1. 手动推送 POST /api/erp/push 命中 enabled=False → 400 erp.endpoint_disabled(不入队/不推)。
  2. 推送目标列表 /api/erp/connectors/status 数据源排除停用端点(识别后选不到它)。
自动推送走 list_erp_endpoints(auto_push_only=True) 的 `enabled = TRUE` 过滤,同源,不在此重测。
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")

import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from routes import erp_push_log_routes  # noqa: E402
from routes import erp_connectors_routes  # noqa: E402

_USER = {"id": "u-test", "plan": "pro"}


class EnabledGateTests(unittest.TestCase):
    def _client(self):
        return TestClient(app.app)

    def test_manual_push_to_disabled_endpoint_rejected(self):
        """停用端点手动推送 → 400 erp.endpoint_disabled(在去重/推送之前就拦)。"""
        with (
            patch.object(erp_push_log_routes, "get_current_user_from_request", return_value=_USER),
            patch.object(erp_push_log_routes, "_check_push_access", return_value=None),
            patch.object(erp_push_log_routes, "_tid", return_value=None),
            patch.object(
                erp_push_log_routes.db,
                "get_ocr_history_detail",
                return_value={"invoice_no": "INV-1", "seller_name": "S", "total_amount": "1"},
            ),
            patch.object(
                erp_push_log_routes.db,
                "get_erp_endpoint",
                return_value={"id": "ep-x", "adapter": "express", "enabled": False, "config": {}},
            ) as get_ep,
            patch.object(erp_push_log_routes.db, "has_recent_successful_push") as dedup,
        ):
            with self._client() as client:
                r = client.post("/api/erp/push", json={"history_id": "h-1", "endpoint_id": "ep-x"})
        self.assertEqual(r.status_code, 400, r.text)
        self.assertEqual(r.json().get("detail"), "erp.endpoint_disabled")
        get_ep.assert_called_once()
        dedup.assert_not_called()  # 拦在去重/推送之前

    def test_connectors_status_excludes_disabled(self):
        """推送目标列表只含启用端点 · 停用的不出现(识别后选不到)。"""
        endpoints = [
            {"id": "ep-on", "adapter": "express", "enabled": True, "config": {}, "name": "On"},
            {"id": "ep-off", "adapter": "webhook", "enabled": False, "config": {}, "name": "Off"},
        ]
        with (
            patch.object(
                erp_connectors_routes, "get_current_user_from_request", return_value=_USER
            ),
            patch.object(erp_connectors_routes.db, "list_erp_endpoints", return_value=endpoints),
        ):
            with self._client() as client:
                r = client.get("/api/erp/connectors/status")
        self.assertEqual(r.status_code, 200, r.text)
        ids = [c.get("endpoint_id") for c in r.json().get("connectors", [])]
        self.assertIn("ep-on", ids)
        self.assertNotIn("ep-off", ids)


if __name__ == "__main__":
    unittest.main()
