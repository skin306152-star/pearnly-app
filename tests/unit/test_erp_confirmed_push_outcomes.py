from __future__ import annotations

import unittest
from unittest import mock

from services.erp import confirmed_push


class ConfirmedPushOutcomeTests(unittest.IsolatedAsyncioTestCase):
    async def test_mrerp_http_exception_swallowed_by_adapter_is_manual_unknown(self):
        from services.erp.exceptions import MRERPTechnicalError
        from services.erp.mrerp_http import MrErpHttpAdapter

        endpoint = {
            "id": "endpoint-1",
            "user_id": "owner",
            "name": "MR.ERP",
            "adapter": "mrerp",
            "config": {"comidyear": "15", "seldb": "2"},
        }
        intent = {
            "endpoint": endpoint,
            "history": {"id": "history-1", "invoice_no": "INV-1", "pages": []},
            "history_id": "history-1",
            "log_id": "reserved-log",
        }
        adapter = MrErpHttpAdapter(
            login_url="https://example.invalid",
            username="user",
            password="pass",
            comidyear="15",
            seldb="2",
            serialize_sessions=False,
        )
        with (
            mock.patch.object(confirmed_push.db, "get_user_tenant_id", return_value="tenant"),
            mock.patch.object(confirmed_push.erp_push, "load_mrerp_mappings", return_value={}),
            mock.patch.object(
                confirmed_push.erp_push, "build_mrerp_adapter", return_value=(adapter, None)
            ),
            mock.patch(
                "services.erp.express_push.bank_evidence.attach_bank_index",
                side_effect=lambda mappings, *_args: mappings,
            ),
            mock.patch("services.erp.express_push.preflight._own_tax_id", return_value=None),
            mock.patch(
                "services.erp.mrerp_http.routing.route_and_upload",
                side_effect=MRERPTechnicalError(
                    "POST impartran/component/importpc.php network error: timeout"
                ),
            ),
            mock.patch.object(
                confirmed_push.confirmed_push_reservation,
                "mark_reserved_push_unknown",
                return_value=True,
            ) as mark_unknown,
            mock.patch.object(
                confirmed_push.confirmed_push_reservation, "finalize_reserved_push"
            ) as finalize,
            mock.patch.object(confirmed_push.db, "update_history_push_status"),
            mock.patch.object(confirmed_push.db, "schedule_log_retry") as retry,
        ):
            result = await confirmed_push._dispatch_reserved_push(intent, posting_kind=None)

        self.assertEqual(result["status"], "manual")
        self.assertEqual(result["error_msg"], "push_result_unknown")
        swallowed = mark_unknown.call_args.args[1]
        self.assertIn("ERR_TECHNICAL", swallowed["error_msg"])
        self.assertIn("importpc.php", swallowed["error_msg"])
        finalize.assert_not_called()
        retry.assert_not_called()

    async def test_express_failed_enqueue_and_retry_schedule_are_one_finalize(self):
        intent = {
            "endpoint": {"id": "endpoint-1", "name": "Express", "adapter": "express"},
            "history": {"id": "history-1"},
            "history_id": "history-1",
            "log_id": "reserved-log",
        }
        failed = {
            "success": False,
            "http_status": 0,
            "request_body": {"adapter": "express"},
            "response_body": None,
            "error_msg": "ERR_EXPRESS_DISABLED",
            "elapsed_ms": 2,
        }
        with (
            mock.patch.object(confirmed_push.erp_push, "push_to_endpoint", return_value=failed),
            mock.patch.object(confirmed_push.db, "get_erp_retry_delay_sec", return_value=60),
            mock.patch.object(
                confirmed_push.confirmed_push_reservation,
                "finalize_reserved_push",
                return_value="failed",
            ) as finalize,
            mock.patch.object(confirmed_push.db, "update_endpoint_stats"),
            mock.patch.object(confirmed_push.db, "update_history_push_status"),
            mock.patch.object(confirmed_push.db, "schedule_log_retry") as legacy_schedule,
        ):
            result = await confirmed_push._dispatch_reserved_push(intent, posting_kind=None)

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "retrying")
        self.assertEqual(finalize.call_args.kwargs["retry_delay_sec"], 60)
        legacy_schedule.assert_not_called()

    async def test_uncertain_finalize_uses_committed_log_readback(self):
        intent = {
            "endpoint": {"id": "endpoint-1", "name": "MR.ERP", "adapter": "mrerp"},
            "history": {"id": "history-1"},
            "history_id": "history-1",
            "log_id": "reserved-log",
        }
        pushed = {
            "success": True,
            "http_status": 200,
            "request_body": {"adapter": "mrerp"},
            "response_body": "ok",
            "error_msg": None,
            "elapsed_ms": 4,
        }
        with (
            mock.patch.object(confirmed_push.erp_push, "push_to_endpoint", return_value=pushed),
            mock.patch.object(
                confirmed_push.confirmed_push_reservation,
                "finalize_reserved_push",
                return_value=None,
            ),
            mock.patch.object(
                confirmed_push.confirmed_push_reservation,
                "read_reserved_push_result",
                return_value={
                    "status": "success",
                    "next_retry_at": None,
                    "lease_owner": None,
                },
            ) as readback,
            mock.patch.object(
                confirmed_push.confirmed_push_reservation, "mark_reserved_push_unknown"
            ) as mark_unknown,
            mock.patch.object(confirmed_push.db, "update_endpoint_stats"),
            mock.patch.object(confirmed_push.db, "update_history_push_status") as history_status,
            mock.patch.object(confirmed_push.db, "counts_as_endpoint_success", return_value=True),
            mock.patch("services.erp.line_push_notification.notify_success"),
        ):
            result = await confirmed_push._dispatch_reserved_push(intent, posting_kind=None)

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "success")
        readback.assert_called_once_with(intent)
        mark_unknown.assert_not_called()
        history_status.assert_called_once_with("history-1", "success")

    async def test_uncertain_finalize_preserves_a_committed_express_queue(self):
        intent = {
            "endpoint": {"id": "endpoint-1", "name": "Express", "adapter": "express"},
            "history": {"id": "history-1"},
            "history_id": "history-1",
            "log_id": "reserved-log",
        }
        queued = {
            "success": False,
            "http_status": 202,
            "request_body": {"adapter": "express"},
            "response_body": None,
            "error_msg": "EXPRESS_QUEUED",
            "elapsed_ms": 3,
        }
        with (
            mock.patch.object(confirmed_push.erp_push, "push_to_endpoint", return_value=queued),
            mock.patch.object(
                confirmed_push.confirmed_push_reservation,
                "finalize_reserved_push",
                return_value=None,
            ),
            mock.patch.object(
                confirmed_push.confirmed_push_reservation,
                "read_reserved_push_result",
                return_value={
                    "status": "pending",
                    "next_retry_at": None,
                    "lease_owner": None,
                },
            ),
            mock.patch.object(
                confirmed_push.confirmed_push_reservation, "mark_reserved_push_unknown"
            ) as mark_unknown,
            mock.patch.object(confirmed_push.db, "update_endpoint_stats"),
            mock.patch.object(confirmed_push.db, "update_history_push_status") as history_status,
        ):
            result = await confirmed_push._dispatch_reserved_push(intent, posting_kind=None)

        self.assertEqual(result["status"], "pending")
        mark_unknown.assert_not_called()
        history_status.assert_called_once_with("history-1", "pending")


if __name__ == "__main__":
    unittest.main()
