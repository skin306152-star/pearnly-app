from __future__ import annotations

import unittest
from unittest import mock

from fastapi import HTTPException

from services.erp import confirmed_push


class ConfirmedPushTests(unittest.IsolatedAsyncioTestCase):
    async def test_line_non_default_push_rechecks_proof_before_direct_outbound(self):
        user = {"id": "owner", "tenant_id": "tenant", "entry": "erp"}
        endpoint = {
            "id": "endpoint-1",
            "name": "MR.ERP",
            "adapter": "mrerp",
            "enabled": True,
            "config": {"comidyear": "6", "seldb": "1"},
        }
        denied = HTTPException(
            409,
            detail={"code": "catalog_refresh_invalid", "reason": "refresh_superseded"},
        )
        with (
            mock.patch.object(
                confirmed_push.team_access, "assigned_endpoint_for_request", return_value=None
            ),
            mock.patch.object(
                confirmed_push.shared_express_push,
                "reserve_managed_manual_push",
                return_value=None,
            ),
            mock.patch.object(
                confirmed_push.db, "get_ocr_history_detail", return_value={"id": "history"}
            ),
            mock.patch.object(
                confirmed_push.convert_svc, "history_is_converted", return_value=True
            ),
            mock.patch.object(confirmed_push.db, "get_erp_endpoint", return_value=endpoint),
            mock.patch(
                "services.erp.selected_account.require_catalog_evidence",
                side_effect=denied,
            ) as evidence,
            mock.patch.object(confirmed_push.erp_push, "push_to_endpoint") as outbound,
        ):
            with self.assertRaises(HTTPException) as caught:
                await confirmed_push.dispatch_confirmed_history(
                    user=user,
                    history_id="history",
                    endpoint_id="endpoint-1",
                    account_set_key="15:2",
                    target_refresh_request_id="11111111-1111-4111-8111-111111111111",
                    target_projection_revision=8,
                    catalog_evidence_required=True,
                )

        self.assertIs(caught.exception, denied)
        self.assertEqual(evidence.call_args.kwargs["account_set_key"], "15:2")
        self.assertEqual(
            evidence.call_args.kwargs["request_id"],
            "11111111-1111-4111-8111-111111111111",
        )
        self.assertEqual(evidence.call_args.kwargs["revision"], 8)
        outbound.assert_not_called()

    async def test_non_default_push_reserves_before_outbound_and_finalizes_same_log(self):
        user = {"id": "owner", "tenant_id": "tenant", "entry": "erp"}
        history = {"id": "history", "invoice_no": "INV-1", "total_amount": 100}
        endpoint = {
            "id": "endpoint-1",
            "name": "MR.ERP",
            "adapter": "mrerp",
            "enabled": True,
            "config": {"comidyear": "6", "seldb": "1"},
        }
        frozen = {**endpoint, "config": {"comidyear": "15", "seldb": "2"}}
        reservation = {
            "dispatch": True,
            "endpoint": frozen,
            "history": history,
            "history_id": "history",
            "log_id": "reserved-log",
            "user_id": "owner",
            "tenant_id": "tenant",
            "account_set": "15:2",
            "source": "line_erp",
            "target_intent": {"account_set": "15:2"},
        }
        pushed = {
            "success": True,
            "http_status": 200,
            "request_body": {"account_set": "15:2"},
            "response_body": "ok",
            "error_msg": None,
            "elapsed_ms": 5,
        }
        order = []

        def reserve(**_kwargs):
            order.append("reserve_committed")
            return reservation

        def outbound(selected, *_args, **_kwargs):
            order.append("outbound")
            self.assertEqual(selected["config"], {"comidyear": "15", "seldb": "2"})
            return pushed

        def finalize(current, result, *, retry_delay_sec=None):
            order.append("finalize")
            self.assertIs(current, reservation)
            self.assertIs(result, pushed)
            self.assertIsNone(retry_delay_sec)
            return "success"

        with (
            mock.patch.object(
                confirmed_push.team_access, "assigned_endpoint_for_request", return_value=None
            ),
            mock.patch.object(
                confirmed_push.shared_express_push,
                "reserve_managed_manual_push",
                return_value=None,
            ),
            mock.patch.object(confirmed_push.db, "get_ocr_history_detail", return_value=history),
            mock.patch.object(
                confirmed_push.convert_svc, "history_is_converted", return_value=True
            ),
            mock.patch.object(confirmed_push.db, "get_erp_endpoint", return_value=endpoint),
            mock.patch(
                "services.erp.selected_account.require_catalog_evidence",
                return_value={"ok": True, "proof_required": True},
            ),
            mock.patch.object(
                confirmed_push.confirmed_push_reservation,
                "reserve_catalog_selected_push",
                side_effect=reserve,
            ) as reserve_call,
            mock.patch.object(
                confirmed_push.erp_push, "push_to_endpoint", side_effect=outbound
            ) as outbound_call,
            mock.patch.object(
                confirmed_push.confirmed_push_reservation,
                "finalize_reserved_push",
                side_effect=finalize,
            ),
            mock.patch.object(confirmed_push.db, "update_endpoint_stats"),
            mock.patch.object(confirmed_push.db, "update_history_push_status"),
            mock.patch.object(confirmed_push.db, "counts_as_endpoint_success", return_value=True),
            mock.patch(
                "services.erp.line_push_notification.notify_success",
                return_value=None,
            ),
            mock.patch.object(confirmed_push.db, "insert_push_log") as insert_log,
        ):
            result = await confirmed_push.dispatch_confirmed_history(
                user=user,
                history_id="history",
                endpoint_id="endpoint-1",
                workspace_client_id=17,
                account_set_key="15:2",
                target_refresh_request_id="11111111-1111-4111-8111-111111111111",
                target_projection_revision=9,
                catalog_evidence_required=True,
            )

        self.assertEqual(order, ["reserve_committed", "outbound", "finalize"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["log_id"], "reserved-log")
        self.assertEqual(
            reserve_call.call_args.kwargs["refresh_request_id"],
            ("11111111-1111-4111-8111-111111111111"),
        )
        outbound_call.assert_called_once()
        insert_log.assert_not_called()

    async def test_reserved_outbound_exception_is_manual_and_never_auto_retried(self):
        reservation = {
            "dispatch": True,
            "endpoint": {"id": "endpoint-1", "name": "MR.ERP", "adapter": "mrerp"},
            "history": {"id": "history"},
            "history_id": "history",
            "log_id": "reserved-log",
        }
        with (
            mock.patch.object(
                confirmed_push.erp_push, "push_to_endpoint", side_effect=TimeoutError
            ),
            mock.patch.object(
                confirmed_push.confirmed_push_reservation,
                "mark_reserved_push_unknown",
                return_value=True,
            ) as mark_unknown,
            mock.patch.object(
                confirmed_push.confirmed_push_reservation, "finalize_reserved_push"
            ) as finalize,
            mock.patch.object(confirmed_push.db, "update_history_push_status") as history_status,
            mock.patch.object(confirmed_push.db, "schedule_log_retry") as retry,
        ):
            result = await confirmed_push._dispatch_reserved_push(reservation, posting_kind=None)

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "manual")
        self.assertEqual(result["error_msg"], "push_result_unknown")
        mark_unknown.assert_called_once_with(reservation)
        history_status.assert_called_once_with("history", "manual")
        finalize.assert_not_called()
        retry.assert_not_called()

    async def test_web_non_default_push_cannot_bypass_catalog_evidence(self):
        user = {"id": "owner", "tenant_id": "tenant", "entry": "main"}
        endpoint = {
            "id": "endpoint-1",
            "name": "MR.ERP",
            "adapter": "mrerp",
            "enabled": True,
            "config": {"comidyear": "6", "seldb": "1"},
        }
        denied = HTTPException(
            409,
            detail={"code": "catalog_refresh_invalid", "reason": "refresh_superseded"},
        )
        request = mock.Mock()
        with (
            mock.patch.object(
                confirmed_push.team_access, "assigned_endpoint_for_request", return_value=None
            ),
            mock.patch.object(
                confirmed_push.team_access, "record_creator_scope", return_value=None
            ),
            mock.patch.object(
                confirmed_push.shared_express_push,
                "maybe_reserve_manual_push",
                new=mock.AsyncMock(return_value=None),
            ) as managed,
            mock.patch.object(
                confirmed_push.db, "get_ocr_history_detail", return_value={"id": "history"}
            ),
            mock.patch.object(confirmed_push.db, "get_erp_endpoint", return_value=endpoint),
            mock.patch(
                "services.erp.selected_account.require_catalog_evidence",
                side_effect=denied,
            ) as evidence,
            mock.patch.object(confirmed_push.erp_push, "push_to_endpoint") as outbound,
        ):
            with self.assertRaises(HTTPException) as caught:
                await confirmed_push.dispatch_confirmed_history(
                    user=user,
                    request=request,
                    history_id="history",
                    endpoint_id="endpoint-1",
                    account_set_key="15:2",
                    target_refresh_request_id="11111111-1111-4111-8111-111111111111",
                    target_projection_revision=7,
                )

        self.assertIs(caught.exception, denied)
        self.assertEqual(
            managed.call_args.kwargs["target_refresh_request_id"],
            "11111111-1111-4111-8111-111111111111",
        )
        self.assertEqual(managed.call_args.kwargs["target_projection_revision"], 7)
        self.assertEqual(evidence.call_args.kwargs["account_set_key"], "15:2")
        outbound.assert_not_called()

    async def test_retryable_first_failure_is_presented_as_waiting(self):
        user = {"id": "owner", "tenant_id": "tenant", "entry": "erp"}
        endpoint = {
            "id": "endpoint-1",
            "name": "MR.ERP",
            "adapter": "mrerp",
            "enabled": True,
            "config": {"comidyear": "6", "seldb": "1"},
        }
        history = {
            "id": "history",
            "invoice_no": "INV-1",
            "seller_name": "Seller",
            "total_amount": 100,
        }
        failure = {
            "success": False,
            "http_status": 503,
            "request_body": {"adapter": "mrerp"},
            "response_body": None,
            "error_msg": "upstream_timeout",
            "elapsed_ms": 1000,
        }
        with (
            mock.patch.object(
                confirmed_push.team_access, "assigned_endpoint_for_request", return_value=None
            ),
            mock.patch.object(
                confirmed_push.shared_express_push,
                "reserve_managed_manual_push",
                return_value=None,
            ),
            mock.patch.object(confirmed_push.db, "get_ocr_history_detail", return_value=history),
            mock.patch.object(
                confirmed_push.convert_svc, "history_is_converted", return_value=True
            ),
            mock.patch.object(confirmed_push.db, "get_erp_endpoint", return_value=endpoint),
            mock.patch.object(confirmed_push.db, "has_recent_successful_push", return_value=None),
            mock.patch.object(confirmed_push.erp_push, "push_to_endpoint", return_value=failure),
            mock.patch.object(confirmed_push.db, "classify_push_status", return_value="failed"),
            mock.patch.object(confirmed_push.db, "insert_push_log", return_value="log-1") as log,
            mock.patch.object(confirmed_push.db, "update_endpoint_stats"),
            mock.patch.object(confirmed_push.db, "update_history_push_status"),
            mock.patch.object(confirmed_push.db, "is_user_data_error", return_value=False),
            mock.patch.object(confirmed_push.db, "get_erp_retry_delay_sec", return_value=5),
            mock.patch.object(confirmed_push.db, "schedule_log_retry", return_value=True) as retry,
        ):
            result = await confirmed_push.dispatch_confirmed_history(
                user=user,
                history_id="history",
                endpoint_id="endpoint-1",
                workspace_client_id=7,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "retrying")
        self.assertEqual(log.call_args.kwargs["request_body"]["source"], "line_erp")
        retry.assert_called_once_with("log-1", 5)

    async def test_member_push_uses_only_owner_assigned_endpoint(self):
        user = {
            "id": "member",
            "tenant_id": "tenant",
            "entry": "erp",
            "role": "member",
        }
        endpoint = {
            "id": "assigned",
            "name": "Owner MR.ERP",
            "adapter": "mrerp",
            "enabled": True,
        }
        history = {
            "id": "history",
            "invoice_no": "INV-1",
            "seller_name": "Seller",
            "total_amount": 100,
        }
        push_result = {
            "success": True,
            "http_status": 200,
            "request_body": {"adapter": "mrerp"},
            "response_body": "ok",
            "error_msg": None,
            "elapsed_ms": 4,
        }
        with (
            mock.patch.object(
                confirmed_push.team_access,
                "assigned_endpoint_for_request",
                return_value=endpoint,
            ),
            mock.patch.object(
                confirmed_push.shared_express_push,
                "reserve_managed_manual_push",
                return_value=None,
            ),
            mock.patch.object(
                confirmed_push.db, "get_ocr_history_detail", return_value=history
            ) as history_lookup,
            mock.patch.object(
                confirmed_push.convert_svc, "history_is_converted", return_value=True
            ),
            mock.patch.object(confirmed_push.db, "has_recent_successful_push", return_value=None),
            mock.patch.object(
                confirmed_push.erp_push, "push_to_endpoint", return_value=push_result
            ) as outbound,
            mock.patch.object(confirmed_push.db, "classify_push_status", return_value="success"),
            mock.patch.object(
                confirmed_push.team_access,
                "insert_assigned_push_log",
                return_value="log-1",
            ) as insert_log,
            mock.patch.object(confirmed_push.db, "insert_push_log") as owner_log,
            mock.patch.object(confirmed_push.db, "update_endpoint_stats"),
            mock.patch.object(confirmed_push.db, "update_history_push_status"),
        ):
            result = await confirmed_push.dispatch_confirmed_history(
                user=user,
                history_id="history",
                workspace_client_id=7,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["log_id"], "log-1")
        history_lookup.assert_called_once_with("member", "history")
        outbound.assert_called_once_with(endpoint, history, posting_kind=None)
        insert_log.assert_called_once()
        owner_log.assert_not_called()

    async def test_managed_express_result_returns_without_direct_outbound_push(self):
        user = {
            "id": "member",
            "tenant_id": "tenant",
            "entry": "erp",
            "role": "member",
        }
        endpoint = {"id": "shared-express", "adapter": "express", "enabled": True}
        queued = {"ok": True, "status": "pending", "queued": True, "log_id": "log-2"}
        with (
            mock.patch.object(
                confirmed_push.team_access,
                "assigned_endpoint_for_request",
                return_value=endpoint,
            ),
            mock.patch.object(
                confirmed_push.db, "get_ocr_history_detail", return_value={"id": "history"}
            ),
            mock.patch.object(
                confirmed_push.shared_express_push,
                "reserve_managed_manual_push",
                return_value=queued,
            ) as reserve,
            mock.patch.object(confirmed_push.erp_push, "push_to_endpoint") as outbound,
        ):
            result = await confirmed_push.dispatch_confirmed_history(
                user=user,
                history_id="history",
                workspace_client_id=7,
                account_set_key="other",
                target_refresh_request_id="11111111-1111-4111-8111-111111111111",
                target_projection_revision=8,
                catalog_evidence_required=True,
            )

        self.assertEqual(result, queued)
        self.assertEqual(reserve.call_args.kwargs["endpoint_id"], "shared-express")
        self.assertEqual(reserve.call_args.kwargs["requested_workspace_id"], 7)
        self.assertEqual(reserve.call_args.kwargs["account_set_key"], "other")
        self.assertEqual(
            reserve.call_args.kwargs["target_refresh_request_id"],
            "11111111-1111-4111-8111-111111111111",
        )
        self.assertEqual(reserve.call_args.kwargs["target_projection_revision"], 8)
        self.assertTrue(reserve.call_args.kwargs["catalog_evidence_required"])
        outbound.assert_not_called()


if __name__ == "__main__":
    unittest.main()
