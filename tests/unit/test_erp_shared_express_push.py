from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from starlette.requests import Request

from routes import erp_push_log_routes as routes


def _request(workspace: str = "101") -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/erp/push",
            "headers": [(b"x-workspace-client-id", workspace.encode())],
        }
    )


class SharedExpressPushRouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_managed_manual_push_returns_queued_without_outbound_push(self):
        user = {"id": "actor", "tenant_id": "tenant", "entry": "cowork"}
        queued = {
            "ok": True,
            "queued": True,
            "status": "pending",
            "log_id": "log-1",
            "endpoint_id": "endpoint-1",
            "http_status": 202,
        }
        request = _request()
        req = routes.ErpPushRequest(history_id="history-1", endpoint_id="endpoint-1")
        with (
            patch.object(routes, "get_current_user_from_request", return_value=user),
            patch.object(routes, "require_erp_portal"),
            patch.object(routes, "_check_push_access"),
            patch(
                "services.erp.shared_express_push.maybe_reserve_manual_push",
                new=AsyncMock(return_value=queued),
            ) as reserve,
            patch.object(routes._erp, "push_to_endpoint") as outbound,
        ):
            result = await routes.erp_push(req, request)

        self.assertEqual(result, queued)
        reserve.assert_awaited_once()
        outbound.assert_not_called()

    async def test_gen0_fallback_keeps_existing_route_result(self):
        user = {"id": "actor", "tenant_id": "tenant", "entry": "main"}
        endpoint = {"id": "endpoint-0", "name": "Legacy", "adapter": "webhook", "enabled": True}
        history = {"id": "history-1", "invoice_no": "INV-1"}
        request = _request()
        req = routes.ErpPushRequest(history_id="history-1", endpoint_id="endpoint-0")
        push_result = {
            "success": True,
            "http_status": 200,
            "response_body": "ok",
            "error_msg": None,
            "elapsed_ms": 3,
            "request_body": {"legacy": True},
        }
        with (
            patch.object(routes, "get_current_user_from_request", return_value=user),
            patch.object(routes, "require_erp_portal"),
            patch.object(routes, "_check_push_access"),
            patch(
                "services.erp.shared_express_push.maybe_reserve_manual_push",
                new=AsyncMock(return_value=None),
            ),
            patch.object(routes.db, "get_ocr_history_detail", return_value=history),
            patch.object(routes.db, "get_erp_endpoint", return_value=endpoint),
            patch.object(routes.db, "has_recent_successful_push", return_value=None),
            patch.object(routes._erp, "push_to_endpoint", return_value=push_result),
            patch.object(routes.db, "classify_push_status", return_value="success"),
            patch.object(routes.db, "insert_push_log", return_value="legacy-log"),
            patch.object(routes.db, "update_endpoint_stats"),
            patch.object(routes.db, "update_history_push_status"),
        ):
            result = await routes.erp_push(req, request)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["log_id"], "legacy-log")
        self.assertTrue(result["ok"])


if __name__ == "__main__":
    unittest.main()
