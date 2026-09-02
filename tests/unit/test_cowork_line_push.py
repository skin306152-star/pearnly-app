from __future__ import annotations

import unittest
from unittest import mock

from fastapi import HTTPException

from services.cowork_line import push, push_recovery, push_reservation

IDENTITY = {
    "tenant_id": "tenant-1",
    "user_id": "user-1",
    "membership_id": "member-1",
    "line_user_id": "line-1",
}
HISTORY = {
    "id": "history-1",
    "invoice_no": "INV-1",
    "seller_name": "Seller",
    "total_amount": 120,
}


class _Cursor:
    def __init__(self, row=None, rows=None, rowcount=1):
        self.row = row
        self.rows = list(rows or [])
        self.rowcount = rowcount
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class _CursorContext:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc, traceback):
        return False


class CoworkLinePushTest(unittest.IsolatedAsyncioTestCase):
    def test_retryable_mrerp_failure_is_presented_as_waiting(self):
        cursor = _Cursor(rowcount=1)
        intent = {
            "history_id": "history-1",
            "log_id": "log-1",
            "status": "retrying",
            "accepted": False,
        }
        result = {
            "success": False,
            "http_status": 503,
            "request_body": {"adapter": "mrerp"},
            "response_body": None,
            "error_msg": "upstream_timeout",
            "elapsed_ms": 1000,
        }
        with (
            mock.patch.object(
                push_reservation.db, "get_cursor_rls", return_value=_CursorContext(cursor)
            ),
            mock.patch.object(push_reservation, "lock_endpoint_binding"),
            mock.patch.object(push_reservation, "lock_legacy_endpoint", return_value=True),
            mock.patch.object(push_reservation.db, "classify_push_status", return_value="failed"),
            mock.patch.object(
                push_reservation.db, "counts_as_endpoint_success", return_value=False
            ),
            mock.patch.object(push_reservation.db, "is_user_data_error", return_value=False),
            mock.patch.object(push_reservation.db, "get_erp_retry_delay_sec", return_value=5),
            mock.patch.object(
                push_reservation.db, "schedule_log_retry", return_value=True
            ) as retry,
        ):
            finalized = push_reservation.finalize_legacy_intent(
                IDENTITY, {"id": "endpoint-1"}, intent, result
            )

        self.assertTrue(finalized)
        self.assertEqual(intent["status"], "retrying")
        self.assertTrue(intent["accepted"])
        retry.assert_called_once_with("log-1", 5)
        update = next(call for call in cursor.calls if "UPDATE erp_push_logs" in call[0])
        self.assertIn('"source": "cowork_line"', update[1][2])

    def test_reservation_revalidates_active_line_identity_and_both_permissions(self):
        cursor = _Cursor({"role": "member", "invited_by": "owner-1"})
        authz = mock.Mock(
            membership_id=IDENTITY["membership_id"],
            has=mock.Mock(side_effect=lambda code: code == "erp.push.operate"),
            allows_workspace=mock.Mock(return_value=True),
        )
        with mock.patch.object(push_reservation, "resolve", return_value=authz):
            with self.assertRaises(HTTPException):
                push_reservation._active_actor(cursor, IDENTITY, 17)

        identity_query, params = cursor.calls[0]
        self.assertIn("identity.revoked_at IS NULL", identity_query)
        self.assertIn("membership.status = 'active'", identity_query)
        self.assertIn("u.is_active = TRUE", identity_query)
        self.assertEqual(
            params,
            (
                IDENTITY["membership_id"],
                IDENTITY["tenant_id"],
                IDENTITY["user_id"],
                IDENTITY["line_user_id"],
            ),
        )
        authz.has.assert_any_call("erp.endpoint.view")

    async def test_managed_batch_reserves_log_and_confirmation_together(self):
        target = {
            "endpoint_id": "endpoint-express",
            "workspace_client_id": 17,
            "adapter": "express",
            "managed": True,
        }
        queued = [
            {
                "history_id": "history-1",
                "status": "pending",
                "log_id": "log-express",
                "accepted": True,
            }
        ]
        selection = {
            "posting_kind": "stock",
            "account_set": r"S:\\70EXP\\TEST2020",
            "account_config": {
                "account_set": r"S:\\70EXP\\TEST2020",
                "root_key": r"S:\\70EXP",
            },
        }
        with mock.patch.object(push, "reserve_managed_batch", return_value=queued) as reserve:
            result = await push.dispatch_confirmed(IDENTITY, ["history-1"], target, selection)

        self.assertTrue(result["push_ok"])
        self.assertEqual(result["committed"], 1)
        self.assertEqual(result["results"][0]["log_id"], "log-express")
        reserve.assert_called_once_with(
            IDENTITY,
            ["history-1"],
            target,
            posting_kind="stock",
            account_set_key=selection["account_set"],
            account_config=selection["account_config"],
        )

    async def test_legacy_reserves_intent_before_external_push_and_finalizes_same_log(self):
        target = {
            "endpoint_id": "endpoint-mrerp",
            "workspace_client_id": 17,
            "adapter": "mrerp",
        }
        endpoint = {"id": "endpoint-mrerp", "adapter": "mrerp", "enabled": True}
        intent = {
            "history": dict(HISTORY),
            "history_id": "history-1",
            "log_id": "reserved-log",
            "status": "retrying",
            "accepted": False,
            "dispatch": True,
        }
        order = []

        def reserve(*_args):
            order.append("reserve")
            return endpoint, [intent]

        def send(*_args, **_kwargs):
            order.append("push")
            return {
                "success": True,
                "http_status": 200,
                "request_body": {"invoice": "INV-1"},
                "response_body": "ok",
                "error_msg": None,
                "elapsed_ms": 12,
            }

        def finalize(_identity, _endpoint, current, _result):
            order.append("finalize")
            current.update(status="success", accepted=True, error_msg=None)
            return True

        with (
            mock.patch.object(push, "reserve_legacy_batch", side_effect=reserve),
            mock.patch.object(push.erp_push, "push_to_endpoint", side_effect=send),
            mock.patch.object(push, "finalize_legacy_intent", side_effect=finalize),
        ):
            result = await push.dispatch_confirmed(
                IDENTITY, ["history-1"], target, {"payment": "cash"}
            )

        self.assertEqual(order, ["reserve", "push", "finalize"])
        self.assertEqual(result["committed"], 1)
        self.assertTrue(result["push_ok"])
        self.assertEqual(result["results"][0]["log_id"], "reserved-log")

    async def test_legacy_external_exception_finalizes_reserved_log_as_failed(self):
        target = {
            "endpoint_id": "endpoint-mrerp",
            "workspace_client_id": 17,
            "adapter": "mrerp",
        }
        endpoint = {"id": "endpoint-mrerp", "adapter": "mrerp", "enabled": True}
        intent = {
            "history": dict(HISTORY),
            "history_id": "history-1",
            "log_id": "reserved-log",
            "status": "retrying",
            "accepted": False,
            "dispatch": True,
        }

        def finalize(_identity, _endpoint, current, result):
            self.assertEqual(result["error_msg"], "RuntimeError")
            current.update(status="failed", accepted=False, error_msg="RuntimeError")
            return True

        with (
            mock.patch.object(push, "reserve_legacy_batch", return_value=(endpoint, [intent])),
            mock.patch.object(push.erp_push, "push_to_endpoint", side_effect=RuntimeError),
            mock.patch.object(push, "finalize_legacy_intent", side_effect=finalize),
            mock.patch.object(push, "_failure_log") as new_log,
        ):
            result = await push.dispatch_confirmed(
                IDENTITY, ["history-1"], target, {"payment": "credit"}
            )

        self.assertEqual(result["committed"], 1)
        self.assertFalse(result["push_ok"])
        self.assertEqual(result["results"][0]["log_id"], "reserved-log")
        new_log.assert_not_called()

    async def test_finalize_failure_marks_same_legacy_log_unknown_without_repush(self):
        target = {
            "endpoint_id": "endpoint-mrerp",
            "workspace_client_id": 17,
            "adapter": "mrerp",
        }
        endpoint = {"id": "endpoint-mrerp", "adapter": "mrerp", "enabled": True}
        intent = {
            "history": {**HISTORY, "workspace_client_id": 17},
            "history_id": "history-1",
            "log_id": "reserved-log",
            "status": "retrying",
            "accepted": False,
            "dispatch": True,
        }
        with (
            mock.patch.object(push, "reserve_legacy_batch", return_value=(endpoint, [intent])),
            mock.patch.object(
                push.erp_push,
                "push_to_endpoint",
                return_value={"success": True, "http_status": 200, "error_msg": None},
            ) as send,
            mock.patch.object(push, "finalize_legacy_intent", return_value=False),
            mock.patch.object(push, "mark_legacy_intent_unknown", return_value=True) as mark,
        ):
            result = await push.dispatch_confirmed(
                IDENTITY, ["history-1"], target, {"payment": "credit"}
            )

        send.assert_called_once()
        mark.assert_called_once_with(IDENTITY, endpoint, intent)
        self.assertEqual(result["results"][0]["log_id"], "reserved-log")
        self.assertEqual(result["results"][0]["status"], "manual")
        self.assertFalse(result["push_ok"])

    async def test_concurrent_draft_changed_reuses_canonical_log_without_failure_log(self):
        target = {
            "endpoint_id": "endpoint-express",
            "workspace_client_id": 17,
            "adapter": "express",
            "managed": True,
        }
        canonical = [
            {
                "history_id": "history-1",
                "log_id": "pending-log",
                "status": "pending",
                "accepted": True,
                "error_msg": None,
            }
        ]
        with (
            mock.patch.object(
                push,
                "reserve_managed_batch",
                side_effect=HTTPException(409, detail="cowork_line_intake.draft_changed"),
            ),
            mock.patch.object(push, "confirmed_batch_result", return_value=canonical) as existing,
            mock.patch.object(push, "_failure_log") as failure,
        ):
            result = await push.dispatch_confirmed(
                IDENTITY, ["history-1"], target, {"posting_kind": "stock"}
            )

        existing.assert_called_once_with(IDENTITY, ["history-1"], target)
        failure.assert_not_called()
        self.assertEqual(result["committed"], 1)
        self.assertTrue(result["push_ok"])
        self.assertEqual(result["results"], canonical)

    async def test_draft_changed_without_canonical_log_does_not_invent_failure_log(self):
        target = {
            "endpoint_id": "endpoint-mrerp",
            "workspace_client_id": 17,
            "adapter": "mrerp",
        }
        with (
            mock.patch.object(
                push,
                "reserve_legacy_batch",
                side_effect=HTTPException(409, detail="cowork_line_intake.draft_changed"),
            ),
            mock.patch.object(push, "confirmed_batch_result", return_value=None),
            mock.patch.object(push, "_failure_log") as failure,
        ):
            result = await push.dispatch_confirmed(
                IDENTITY, ["history-1"], target, {"payment": "credit"}
            )

        failure.assert_not_called()
        self.assertEqual(result["committed"], 0)
        self.assertEqual(result["results"], [])
        self.assertEqual(result["error_code"], "cowork_line_intake.draft_changed")

    def test_expired_legacy_reservation_converges_to_manual_without_dispatch(self):
        cursor = _Cursor(rows=[{"history_id": "44444444-4444-4444-8444-444444444444"}])
        with mock.patch.object(
            push_recovery.db,
            "get_cursor_rls",
            return_value=_CursorContext(cursor),
        ):
            settled = push_recovery.reconcile_stale_legacy_reservations(IDENTITY)

        self.assertEqual(settled, 1)
        update_log = cursor.calls[0]
        self.assertIn("status = 'manual'", update_log[0])
        self.assertIn("lease_expires_at <= clock_timestamp()", update_log[0])
        self.assertIn("lease_owner = NULL", update_log[0])
        self.assertTrue(any("UPDATE ocr_history" in sql for sql, _ in cursor.calls))

    async def test_managed_reservation_failure_keeps_draft_and_records_manual_attempt(self):
        target = {
            "endpoint_id": "endpoint-express",
            "workspace_client_id": 17,
            "adapter": "express",
            "managed": True,
        }
        cursor = _Cursor({"id": "manual-log"})
        with (
            mock.patch.object(push, "reserve_managed_batch", side_effect=RuntimeError),
            mock.patch.object(push.db, "get_ocr_history_detail", return_value=HISTORY),
            mock.patch.object(push.db, "get_cursor_rls", return_value=_CursorContext(cursor)),
        ):
            result = await push.dispatch_confirmed(
                IDENTITY, ["history-1"], target, {"posting_kind": "service"}
            )

        self.assertEqual(result["committed"], 0)
        self.assertFalse(result["push_ok"])
        self.assertEqual(result["results"][0]["log_id"], "manual-log")

    def test_failure_without_push_log_is_not_reported_as_a_completed_attempt(self):
        target = {
            "endpoint_id": "endpoint-mrerp",
            "workspace_client_id": 17,
            "adapter": "mrerp",
        }
        with (
            mock.patch.object(push.db, "get_ocr_history_detail", return_value=HISTORY),
            mock.patch.object(push.db, "insert_push_log", return_value=None),
        ):
            with self.assertRaises(push.CoworkLinePushError):
                push._failure_log(IDENTITY, target, "history-1", "target_not_ready")

    async def test_legacy_express_with_workspace_uses_legacy_reservation(self):
        target = {
            "endpoint_id": "endpoint-express",
            "workspace_client_id": 17,
            "adapter": "express",
            "managed": False,
        }
        endpoint = {"id": "endpoint-express", "adapter": "express", "enabled": True}
        intent = {
            "history": dict(HISTORY),
            "history_id": "history-1",
            "log_id": "reserved-log",
            "status": "retrying",
            "accepted": False,
            "dispatch": False,
        }
        with (
            mock.patch.object(
                push, "reserve_legacy_batch", return_value=(endpoint, [intent])
            ) as legacy,
            mock.patch.object(push, "reserve_managed_batch") as managed,
        ):
            result = await push.dispatch_confirmed(
                IDENTITY, ["history-1"], target, {"posting_kind": "stock"}
            )

        legacy.assert_called_once_with(IDENTITY, ["history-1"], target, {"posting_kind": "stock"})
        managed.assert_not_called()
        self.assertEqual(result["committed"], 1)


if __name__ == "__main__":
    unittest.main()
