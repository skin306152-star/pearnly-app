from __future__ import annotations

import json
import unittest
from unittest import mock

from fastapi import HTTPException

from services.erp import confirmed_push_reservation as reservation
from services.erp import push_retry


class _CursorContext:
    def __init__(self, cursor, events=None):
        self.cursor = cursor
        self.events = events if events is not None else []

    def __enter__(self):
        self.events.append("transaction_enter")
        return self.cursor

    def __exit__(self, exc_type, exc, traceback):
        self.events.append("transaction_exit")
        return False


class ConfirmedPushReservationTests(unittest.TestCase):
    def test_proof_and_choice_are_frozen_before_reservation_commit(self):
        events = []
        cursor = mock.MagicMock(rowcount=1)
        endpoint = {
            "id": "endpoint-1",
            "user_id": "owner",
            "name": "MR.ERP",
            "adapter": "mrerp",
            "enabled": True,
            "binding_generation": 0,
            "config": {"comidyear": "6", "seldb": "1", "password_enc": "secret"},
        }
        cursor.fetchone.side_effect = [endpoint, None, None, None, {"id": "reserved-log"}]

        def execute(sql, _params=None):
            if "erp_endpoints ep" in sql and sql.startswith("SELECT"):
                events.append("endpoint_locked")
            elif "INSERT INTO erp_push_logs" in sql:
                events.append("intent_inserted")

        cursor.execute.side_effect = execute

        def validate(*_args, **kwargs):
            events.append("proof_validated")
            self.assertIs(kwargs["cur"], cursor)
            return {
                "ok": True,
                "proof_required": True,
                "request_id": "refresh-1",
                "revision": 9,
                "root_key": None,
            }

        def resolve(*_args, **kwargs):
            events.append("choice_resolved")
            self.assertIs(kwargs["cur"], cursor)
            return {"key": "15:2", "comidyear": "15", "seldb": "2"}

        with (
            mock.patch.object(
                reservation.db,
                "get_cursor",
                return_value=_CursorContext(cursor, events),
            ),
            mock.patch.object(
                reservation, "lock_endpoint_binding", side_effect=lambda *_: events.append("lock")
            ),
            mock.patch.object(
                reservation, "require_catalog_evidence", side_effect=validate
            ) as evidence,
            mock.patch.object(reservation, "resolve_account_choice", side_effect=resolve),
        ):
            intent = reservation.reserve_catalog_selected_push(
                user={"id": "member", "tenant_id": "tenant"},
                endpoint_id="endpoint-1",
                history={"id": "history-1", "workspace_client_id": 17},
                assigned=True,
                account_set_key="15:2",
                account_config=None,
                refresh_request_id="refresh-1",
                projection_revision=9,
                source="line_erp",
                workspace_client_id=17,
                posting_kind=None,
            )

        self.assertTrue(intent["dispatch"])
        self.assertEqual(intent["log_id"], "reserved-log")
        self.assertEqual(intent["endpoint"]["config"]["comidyear"], "15")
        self.assertEqual(intent["endpoint"]["config"]["seldb"], "2")
        self.assertEqual(
            events,
            [
                "transaction_enter",
                "lock",
                "endpoint_locked",
                "proof_validated",
                "choice_resolved",
                "intent_inserted",
                "transaction_exit",
            ],
        )
        evidence.assert_called_once()
        assigned_sql = next(
            call.args[0]
            for call in cursor.execute.call_args_list
            if "FROM erp_team_members" in call.args[0]
        )
        self.assertIn("membership.status = 'active'", assigned_sql)
        self.assertIn("FOR SHARE OF ep,etm,membership,actor,owner_user", assigned_sql)
        insert = next(
            call
            for call in cursor.execute.call_args_list
            if "INSERT INTO erp_push_logs" in call.args[0]
        )
        body = json.loads(insert.args[1][6])
        self.assertIn("'retrying'", insert.args[0])
        self.assertIn("lease_owner,lease_expires_at", insert.args[0])
        self.assertNotIn("next_retry_at", insert.args[0])
        self.assertEqual(body["account_set"], "15:2")
        self.assertEqual(body["target_intent"]["catalog_refresh_request_id"], "refresh-1")
        self.assertEqual(body["target_intent"]["catalog_projection_revision"], 9)
        self.assertNotIn("password_enc", body)

    def test_invalid_locked_proof_cannot_create_an_intent(self):
        cursor = mock.MagicMock(rowcount=1)
        cursor.fetchone.return_value = {
            "id": "endpoint-1",
            "user_id": "owner",
            "adapter": "mrerp",
            "enabled": True,
            "binding_generation": 0,
            "config": {"comidyear": "6", "seldb": "1"},
        }
        denied = HTTPException(
            409,
            detail={"code": "catalog_refresh_invalid", "reason": "refresh_superseded"},
        )
        with (
            mock.patch.object(reservation.db, "get_cursor", return_value=_CursorContext(cursor)),
            mock.patch.object(reservation, "lock_endpoint_binding"),
            mock.patch.object(
                reservation, "require_catalog_evidence", side_effect=denied
            ) as evidence,
            mock.patch.object(reservation, "resolve_account_choice") as resolve,
        ):
            with self.assertRaises(HTTPException) as caught:
                reservation.reserve_catalog_selected_push(
                    user={"id": "owner", "tenant_id": "tenant"},
                    endpoint_id="endpoint-1",
                    history={"id": "history-1"},
                    assigned=False,
                    account_set_key="15:2",
                    account_config=None,
                    refresh_request_id="refresh-old",
                    projection_revision=8,
                    source="main",
                    workspace_client_id=None,
                    posting_kind=None,
                )

        self.assertIs(caught.exception, denied)
        self.assertIs(evidence.call_args.kwargs["cur"], cursor)
        resolve.assert_not_called()
        self.assertFalse(
            any(
                "INSERT INTO erp_push_logs" in call.args[0]
                for call in cursor.execute.call_args_list
            )
        )

    def test_existing_active_reservation_is_reused_without_another_insert(self):
        cursor = mock.MagicMock(rowcount=1)
        endpoint = {
            "id": "endpoint-1",
            "user_id": "owner",
            "name": "Express",
            "adapter": "express",
            "enabled": True,
            "binding_generation": 0,
            "config": {"account_set": r"S:\\70EXP\\TEST2020"},
        }
        active = {
            "id": "active-log",
            "status": "retrying",
            "http_status": 102,
            "response_body": None,
            "error_msg": "ERP_CONFIRMED_PUSH_RESERVED",
        }
        cursor.fetchone.side_effect = [endpoint, None, active]
        with (
            mock.patch.object(reservation.db, "get_cursor", return_value=_CursorContext(cursor)),
            mock.patch.object(reservation, "lock_endpoint_binding"),
            mock.patch.object(
                reservation,
                "require_catalog_evidence",
                return_value={"ok": True, "proof_required": True},
            ),
            mock.patch.object(
                reservation,
                "resolve_account_choice",
                return_value={"account_set": r"S:\\70EXP\\TEST2020"},
            ),
        ):
            result = reservation.reserve_catalog_selected_push(
                user={"id": "owner", "tenant_id": "tenant"},
                endpoint_id="endpoint-1",
                history={"id": "history-1"},
                assigned=False,
                account_set_key=r"S:\\70EXP\\TEST2020",
                account_config=None,
                refresh_request_id="refresh-1",
                projection_revision=5,
                source="main",
                workspace_client_id=None,
                posting_kind="stock",
            )

        self.assertFalse(result["dispatch"])
        self.assertEqual(result["response"]["log_id"], "active-log")
        self.assertTrue(result["response"]["reused"])
        active_lookup = next(
            call
            for call in cursor.execute.call_args_list
            if "status IN ('pending','retrying')" in call.args[0]
        )
        self.assertIn("WHERE tenant_id = %s", active_lookup.args[0])
        self.assertEqual(active_lookup.args[1][0], "tenant")
        self.assertFalse(
            any(
                "INSERT INTO erp_push_logs" in call.args[0]
                for call in cursor.execute.call_args_list
            )
        )

    def test_scheduled_retry_is_reused_as_retrying_without_another_insert(self):
        cursor = mock.MagicMock(rowcount=1)
        endpoint = {
            "id": "endpoint-1",
            "user_id": "owner",
            "name": "Express",
            "adapter": "express",
            "enabled": True,
            "binding_generation": 0,
            "config": {"account_set": r"S:\\70EXP\\TEST2020"},
        }
        scheduled = {
            "id": "scheduled-log",
            "status": "failed",
            "http_status": 0,
            "response_body": None,
            "error_msg": "ERR_EXPRESS_DISABLED",
            "next_retry_at": "2026-09-02T12:00:00+07:00",
        }
        cursor.fetchone.side_effect = [endpoint, None, scheduled]
        with (
            mock.patch.object(reservation.db, "get_cursor", return_value=_CursorContext(cursor)),
            mock.patch.object(reservation, "lock_endpoint_binding"),
            mock.patch.object(
                reservation,
                "require_catalog_evidence",
                return_value={"ok": True, "proof_required": True},
            ),
            mock.patch.object(
                reservation,
                "resolve_account_choice",
                return_value={"account_set": r"S:\\70EXP\\TEST2020"},
            ),
        ):
            result = reservation.reserve_catalog_selected_push(
                user={"id": "owner", "tenant_id": "tenant"},
                endpoint_id="endpoint-1",
                history={"id": "history-1"},
                assigned=False,
                account_set_key=r"S:\\70EXP\\TEST2020",
                account_config=None,
                refresh_request_id="refresh-1",
                projection_revision=5,
                source="main",
                workspace_client_id=None,
                posting_kind="stock",
            )

        self.assertFalse(result["dispatch"])
        self.assertEqual(result["response"]["status"], "retrying")
        self.assertTrue(result["response"]["retry_scheduled"])
        self.assertTrue(result["response"]["reused"])
        active_query = next(
            call.args[0]
            for call in cursor.execute.call_args_list
            if "status IN ('pending','retrying')" in call.args[0]
        )
        self.assertIn("status = 'failed' AND next_retry_at IS NOT NULL", active_query)
        self.assertFalse(
            any(
                "INSERT INTO erp_push_logs" in call.args[0]
                for call in cursor.execute.call_args_list
            )
        )

    def test_finalize_keeps_reserved_target_and_clears_lease(self):
        cursor = mock.MagicMock(rowcount=1)
        intent = {
            "log_id": "reserved-log",
            "history_id": "history-1",
            "user_id": "owner",
            "tenant_id": "tenant",
            "workspace_client_id": 17,
            "account_set": "15:2",
            "source": "line_erp",
            "target_intent": {
                "account_set": "15:2",
                "catalog_refresh_request_id": "refresh-1",
                "catalog_projection_revision": 9,
            },
        }
        with (
            mock.patch.object(
                reservation.db,
                "get_cursor_rls",
                return_value=_CursorContext(cursor),
            ) as get_cursor,
            mock.patch.object(reservation.db, "classify_push_status", return_value="success"),
        ):
            status = reservation.finalize_reserved_push(
                intent,
                {
                    "success": True,
                    "http_status": 200,
                    "request_body": {"account_set": "6:1", "invoice_no": "INV-1"},
                    "response_body": {"ok": True},
                    "error_msg": None,
                    "elapsed_ms": 12,
                },
            )

        self.assertEqual(status, "success")
        get_cursor.assert_called_once_with(
            tenant_id="tenant",
            user_id="owner",
            workspace_client_id=17,
            commit=True,
        )
        update = cursor.execute.call_args
        self.assertIn("lease_owner = NULL", update.args[0])
        self.assertIn("AND status = 'retrying' AND lease_owner = %s", update.args[0])
        body = json.loads(update.args[1][2])
        self.assertEqual(body["account_set"], "15:2")
        self.assertEqual(body["target_intent"], intent["target_intent"])
        self.assertEqual(update.args[1][3], '{"ok": true}')
        self.assertIsNone(update.args[1][6])
        self.assertIsNone(update.args[1][7])

    def test_retry_schedule_is_written_in_same_cas_as_failed_result(self):
        cursor = mock.MagicMock(rowcount=1)
        intent = {
            "log_id": "reserved-log",
            "history_id": "history-1",
            "user_id": "owner",
            "tenant_id": "tenant",
            "workspace_client_id": None,
            "account_set": r"S:\\70EXP\\TEST2020",
            "source": "main",
            "target_intent": {"account_set": r"S:\\70EXP\\TEST2020"},
        }
        with (
            mock.patch.object(
                reservation.db,
                "get_cursor_rls",
                return_value=_CursorContext(cursor),
            ),
            mock.patch.object(reservation.db, "classify_push_status", return_value="failed"),
        ):
            status = reservation.finalize_reserved_push(
                intent,
                {
                    "success": False,
                    "http_status": 0,
                    "request_body": {"adapter": "express"},
                    "response_body": None,
                    "error_msg": "ERR_EXPRESS_DISABLED",
                    "elapsed_ms": 3,
                },
                retry_delay_sec=60,
            )

        self.assertEqual(status, "failed")
        sql, params = cursor.execute.call_args.args
        self.assertIn("next_retry_at = CASE", sql)
        self.assertIn("clock_timestamp()", sql)
        self.assertEqual(params[6:8], (60, 60))
        self.assertIn("AND status = 'retrying' AND lease_owner = %s", sql)

    def test_unknown_result_cas_clears_retry_and_keeps_adapter_diagnostic(self):
        cursor = mock.MagicMock(rowcount=1)
        intent = {
            "log_id": "reserved-log",
            "history_id": "history-1",
            "user_id": "owner",
            "tenant_id": "tenant",
            "workspace_client_id": None,
            "account_set": "15:2",
            "source": "line_erp",
            "target_intent": {"account_set": "15:2"},
        }
        adapter_result = {
            "success": False,
            "http_status": 0,
            "request_body": {"adapter": "mrerp"},
            "response_body": "technical: timed out",
            "error_msg": "ERR_TECHNICAL: importpc timed out",
        }
        with mock.patch.object(
            reservation.db,
            "get_cursor_rls",
            return_value=_CursorContext(cursor),
        ):
            self.assertTrue(reservation.mark_reserved_push_unknown(intent, adapter_result))

        sql, params = cursor.execute.call_args.args
        self.assertIn("status = 'manual'", sql)
        self.assertIn("next_retry_at = NULL", sql)
        self.assertIn("AND status = 'retrying' AND lease_owner = %s", sql)
        self.assertEqual(params[3], "ERP_CONFIRMED_PUSH_RESULT_UNKNOWN")
        diagnostic = json.loads(params[2])
        self.assertEqual(diagnostic["adapter_error"], adapter_result["error_msg"])

    def test_uncertain_finalize_can_read_back_the_committed_terminal_result(self):
        cursor = mock.MagicMock()
        cursor.fetchone.return_value = {
            "status": "success",
            "http_status": 200,
            "error_msg": None,
            "next_retry_at": None,
            "lease_owner": None,
        }
        intent = {
            "log_id": "reserved-log",
            "history_id": "history-1",
            "user_id": "owner",
            "tenant_id": "tenant",
            "workspace_client_id": 17,
            "endpoint": {"id": "endpoint-1"},
        }
        with mock.patch.object(
            reservation.db,
            "get_cursor_rls",
            return_value=_CursorContext(cursor),
        ):
            result = reservation.read_reserved_push_result(intent)

        self.assertEqual(result["status"], "success")
        sql, params = cursor.execute.call_args.args
        self.assertIn("WHERE id = %s AND tenant_id = %s", sql)
        self.assertEqual(
            params,
            ("reserved-log", "tenant", "endpoint-1", "history-1"),
        )

    def test_generic_retry_worker_cannot_claim_a_fresh_reservation(self):
        cursor = mock.MagicMock()
        cursor.fetchall.return_value = []
        with mock.patch.object(push_retry.db, "get_cursor", return_value=_CursorContext(cursor)):
            self.assertEqual(push_retry.list_logs_due_for_retry(), [])

        query = cursor.execute.call_args.args[0]
        self.assertIn("l.status = 'failed'", query)
        self.assertIn("l.next_retry_at IS NOT NULL", query)
        self.assertIn("l.next_retry_at <= NOW()", query)


if __name__ == "__main__":
    unittest.main()
