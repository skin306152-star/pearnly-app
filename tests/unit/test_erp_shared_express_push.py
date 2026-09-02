from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from starlette.requests import Request

from routes import erp_push_log_routes as routes
from services.erp import shared_express_push as service


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
        req = routes.ErpPushRequest(
            history_id="history-1",
            endpoint_id="endpoint-1",
            account_set_key=r"S:\\68EXP\\BRANCH",
            target_refresh_request_id="11111111-1111-4111-8111-111111111111",
            target_projection_revision=7,
        )
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
        self.assertEqual(reserve.call_args.kwargs["account_set_key"], r"S:\\68EXP\\BRANCH")
        self.assertEqual(
            reserve.call_args.kwargs["target_refresh_request_id"],
            "11111111-1111-4111-8111-111111111111",
        )
        self.assertEqual(reserve.call_args.kwargs["target_projection_revision"], 7)
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


class SharedExpressCatalogEvidenceTests(unittest.TestCase):
    def test_managed_reservation_holds_endpoint_row_against_new_refresh(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = {
            "id": "33333333-3333-4333-8333-333333333333",
            "adapter": "express",
            "enabled": True,
            "shared_scope": True,
            "binding_generation": 2,
            "bound_account_set": "main",
            "bound_profile_key": "profile",
            "live_account_set": "main",
            "live_profile_key": "profile",
            "revoked_at": None,
        }
        with patch.object(service, "_profile_is_fresh", return_value=True):
            service._endpoint_after_lock(
                cursor,
                endpoint_id="33333333-3333-4333-8333-333333333333",
                tenant_id="tenant",
                workspace_client_id=101,
            )

        self.assertIn("FOR SHARE", cursor.execute.call_args.args[0])

    def test_web_catalog_evidence_is_checked_in_the_reservation_transaction(self):
        cursor = MagicMock()
        cursor_context = MagicMock()
        cursor_context.__enter__.return_value = cursor
        endpoint = {
            "id": "33333333-3333-4333-8333-333333333333",
            "adapter": "express",
            "enabled": True,
            "shared_scope": True,
            "binding_generation": 2,
            "bound_account_set": "main",
            "config": {},
        }
        denied = HTTPException(
            409,
            detail={"code": "catalog_refresh_invalid", "reason": "refresh_superseded"},
        )
        authz = SimpleNamespace(
            membership_id="membership",
            has=lambda _permission: True,
            allows_workspace=lambda _workspace: True,
        )
        with (
            patch.object(service.db, "get_cursor_rls", return_value=cursor_context),
            patch.object(service, "erp_shared_express_endpoint_enabled_for", return_value=True),
            patch.object(service, "_legacy_selected", return_value=False),
            patch.object(service, "enable_shared_express_select", return_value=True),
            patch.object(
                service,
                "_managed_endpoint_id",
                return_value="33333333-3333-4333-8333-333333333333",
            ),
            patch.object(service, "lock_endpoint_binding"),
            patch.object(service, "resolve", return_value=authz),
            patch.object(service, "_lock_actor_and_workspace"),
            patch.object(service, "_endpoint_after_lock", return_value=endpoint),
            patch.object(service, "require_catalog_evidence", side_effect=denied) as evidence,
            patch.object(service, "resolve_account_choice") as account_choice,
        ):
            with self.assertRaises(HTTPException) as caught:
                service.reserve_managed_manual_push(
                    user={
                        "id": "11111111-1111-4111-8111-111111111111",
                        "tenant_id": "tenant",
                        "entry": "cowork",
                    },
                    history_id="44444444-4444-4444-8444-444444444444",
                    endpoint_id="33333333-3333-4333-8333-333333333333",
                    requested_workspace_id=101,
                    posting_kind="service",
                    account_set_key="other",
                    target_refresh_request_id="55555555-5555-4555-8555-555555555555",
                    target_projection_revision=8,
                    catalog_evidence_required=True,
                )

        self.assertIs(caught.exception, denied)
        self.assertIs(evidence.call_args.kwargs["cur"], cursor)
        self.assertEqual(
            evidence.call_args.kwargs["request_id"], "55555555-5555-4555-8555-555555555555"
        )
        self.assertEqual(evidence.call_args.kwargs["revision"], 8)
        account_choice.assert_not_called()


if __name__ == "__main__":
    unittest.main()
