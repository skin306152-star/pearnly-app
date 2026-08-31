#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard that disabled ERP endpoints cannot be pushed manually."""

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

_USER = {"id": "u-test", "plan": "pro"}


class EnabledGateTests(unittest.TestCase):
    def _client(self):
        return TestClient(app.app)

    def test_manual_push_to_disabled_endpoint_rejected(self):
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
                response = client.post(
                    "/api/erp/push",
                    json={"history_id": "h-1", "endpoint_id": "ep-x"},
                )

        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json().get("detail"), "erp.endpoint_disabled")
        get_ep.assert_called_once()
        dedup.assert_not_called()

    def test_erp_entry_cannot_push_unconfirmed_history(self):
        user = {
            "id": "u-test",
            "tenant_id": "t1",
            "entry": "erp",
            "plan": "pro",
            "role": "owner",
            "is_active": True,
        }
        with (
            patch.object(erp_push_log_routes, "get_current_user_from_request", return_value=user),
            patch.object(erp_push_log_routes, "_check_push_access", return_value=None),
            patch.object(erp_push_log_routes, "_tid", return_value="t1"),
            patch.object(
                erp_push_log_routes.db,
                "get_ocr_history_detail",
                return_value={"invoice_no": "INV-1", "total_amount": "1"},
            ),
            patch.object(
                erp_push_log_routes.convert_svc,
                "history_is_converted",
                return_value=False,
            ),
            patch.object(erp_push_log_routes.db, "get_erp_endpoint") as get_endpoint,
            patch.object(erp_push_log_routes._erp, "push_to_endpoint") as push,
        ):
            response = self._client().post(
                "/api/erp/push", json={"history_id": "h-1", "endpoint_id": "ep-x"}
            )
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(response.json().get("detail"), "erp.history_not_converted")
        get_endpoint.assert_not_called()
        push.assert_not_called()


if __name__ == "__main__":
    unittest.main()
