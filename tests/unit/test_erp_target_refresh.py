from __future__ import annotations

import unittest
from unittest import mock

from services.erp import selected_account_refresh, target_refresh


class _Cursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self.executed = []
        self.rowcount = 1

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None


class _Context:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, *_args):
        return False


class TargetRefreshTests(unittest.TestCase):
    def test_request_is_a_fast_database_enqueue(self):
        cursor = _Cursor(
            [
                {
                    "id": "endpoint-1",
                    "tenant_id": "tenant-1",
                    "owner_tenant_id": "tenant-1",
                    "binding_generation": 0,
                },
                None,
                {"id": "11111111-1111-4111-8111-111111111111", "status": "requested"},
            ]
        )
        with mock.patch.object(target_refresh.db, "get_cursor", return_value=_Context(cursor)):
            result = target_refresh.request_refresh(
                tenant_id="tenant-1",
                user_id="user-1",
                endpoint_id="endpoint-1",
                account_set_key="6:1",
                adapter="mrerp",
            )

        self.assertEqual(result["status"], "requested")
        self.assertEqual(result["account_set_key"], "6:1")
        self.assertTrue(
            any("INSERT INTO erp_target_refresh_requests" in sql for sql, _ in cursor.executed)
        )

    def test_request_expires_old_lease_before_allocating_a_new_request_id(self):
        cursor = _Cursor(
            [
                {
                    "id": "endpoint-1",
                    "tenant_id": "tenant-1",
                    "owner_tenant_id": "tenant-1",
                    "binding_generation": 0,
                },
                None,
                {"id": "22222222-2222-4222-8222-222222222222", "status": "requested"},
            ]
        )
        with mock.patch.object(target_refresh.db, "get_cursor", return_value=_Context(cursor)):
            result = target_refresh.request_refresh(
                tenant_id="tenant-1",
                user_id="user-1",
                endpoint_id="endpoint-1",
                account_set_key="@endpoint",
                adapter="express",
            )

        expiry_sql = next(
            sql
            for sql, _ in cursor.executed
            if "ERR_REFRESH_LEASE_EXPIRED" in sql and "tenant_id = %s" in sql
        )
        self.assertIn("lease_expires_at <= clock_timestamp()", expiry_sql)
        self.assertEqual(result["request_id"], "22222222-2222-4222-8222-222222222222")
        self.assertTrue(
            any("INSERT INTO erp_target_refresh_requests" in sql for sql, _ in cursor.executed)
        )

    def test_request_coalesces_a_current_in_flight_lease(self):
        request_id = "11111111-1111-4111-8111-111111111111"
        cursor = _Cursor(
            [
                {
                    "id": "endpoint-1",
                    "tenant_id": "tenant-1",
                    "owner_tenant_id": "tenant-1",
                    "binding_generation": 0,
                },
                {"id": request_id, "status": "leased", "lease_expires_at": object()},
                {"id": request_id, "status": "leased"},
            ]
        )
        with mock.patch.object(target_refresh.db, "get_cursor", return_value=_Context(cursor)):
            result = target_refresh.request_refresh(
                tenant_id="tenant-1",
                user_id="user-1",
                endpoint_id="endpoint-1",
                account_set_key="@endpoint",
                adapter="express",
            )

        self.assertEqual(result["request_id"], request_id)
        self.assertEqual(result["status"], "leased")
        self.assertFalse(
            any("INSERT INTO erp_target_refresh_requests" in sql for sql, _ in cursor.executed)
        )

    def test_express_live_lease_blocks_a_second_request_for_the_same_endpoint(self):
        cursor = _Cursor(
            [
                {"id": "endpoint-1"},
                {"id": "11111111-1111-4111-8111-111111111111"},
                {
                    "id": "22222222-2222-4222-8222-222222222222",
                    "status": "requested",
                    "account_set_key": "other-account",
                },
            ]
        )

        result = target_refresh.lease_express_refresh_with_cursor(cursor, "endpoint-1")

        self.assertIsNone(result)
        self.assertEqual(len(cursor.executed), 3)
        live_guard_sql = cursor.executed[2][0]
        self.assertIn("status = 'leased'", live_guard_sql)
        self.assertIn("lease_expires_at > clock_timestamp()", live_guard_sql)
        self.assertEqual(len(cursor.rows), 1)
        self.assertFalse(any("SET status = 'leased'" in sql for sql, _ in cursor.executed))

    def test_express_lease_marks_expired_attempt_failed_instead_of_reissuing_it(self):
        cursor = _Cursor(
            [
                {"id": "endpoint-1"},
                None,
                None,
            ]
        )

        result = target_refresh.lease_express_refresh_with_cursor(cursor, "endpoint-1")

        self.assertIsNone(result)
        fail_sql = next(
            sql
            for sql, _ in cursor.executed
            if "ERR_REFRESH_LEASE_EXPIRED" in sql and "adapter = 'express'" in sql
        )
        self.assertIn("status = 'failed'", fail_sql)
        self.assertIn("ERR_REFRESH_LEASE_EXPIRED", fail_sql)
        self.assertIn("lease_expires_at <= clock_timestamp()", fail_sql)

    def test_express_completion_requires_the_current_unexpired_lease_owner(self):
        cursor = _Cursor([])

        completed = target_refresh.complete_express_refresh_with_cursor(
            cursor,
            request_id="11111111-1111-4111-8111-111111111111",
            endpoint_id="endpoint-1",
            account_set_key=r"C:\EXPRESS\TEST",
            scope_kind="account_set",
            revision=3,
        )

        self.assertTrue(completed)
        sql, params = cursor.executed[-1]
        self.assertIn("status = 'leased'", sql)
        self.assertIn("lease_owner = %s", sql)
        self.assertIn("lease_expires_at > clock_timestamp()", sql)
        self.assertEqual(params[-1], "endpoint-1")

        cursor.rowcount = 0
        with self.assertRaisesRegex(ValueError, "erp.target_refresh_stale_completion"):
            target_refresh.complete_express_refresh_with_cursor(
                cursor,
                request_id="11111111-1111-4111-8111-111111111111",
                endpoint_id="endpoint-1",
                account_set_key=r"C:\EXPRESS\TEST",
                scope_kind="account_set",
                revision=4,
            )

    def test_mrerp_processor_finishes_with_published_revision(self):
        request = {
            "id": "11111111-1111-4111-8111-111111111111",
            "tenant_id": "tenant-1",
            "endpoint_id": "endpoint-1",
            "account_set_key": "6:1",
            "user_id": "user-1",
            "name": "MR.ERP",
            "config": {},
            "lease_owner": "worker-1",
        }
        with (
            mock.patch.object(target_refresh, "_claim_mrerp", return_value=request),
            mock.patch(
                "services.erp.mrerp_target_projection.refresh_mrerp_projection",
                return_value={
                    "ok": True,
                    "projection": {"revision": 7},
                    "error_code": None,
                },
            ) as refresh,
            mock.patch.object(target_refresh, "_finish_mrerp") as finish,
        ):
            processed = target_refresh.process_mrerp_request(request["id"])

        self.assertTrue(processed)
        refresh.assert_called_once()
        finish.assert_called_once_with(
            request["id"],
            "worker-1",
            success=True,
            error_code=None,
            revision=7,
        )

    def test_mrerp_endpoint_request_only_refreshes_account_catalog(self):
        request = {
            "id": "11111111-1111-4111-8111-111111111111",
            "tenant_id": "tenant-1",
            "endpoint_id": "endpoint-1",
            "account_set_key": target_refresh.ENDPOINT_SCOPE_KEY,
            "user_id": "user-1",
            "name": "MR.ERP",
            "config": {},
            "lease_owner": "worker-1",
        }
        with (
            mock.patch.object(target_refresh, "_claim_mrerp", return_value=request),
            mock.patch(
                "services.erp.mrerp_target_projection.refresh_mrerp_account_catalog",
                return_value={
                    "ok": True,
                    "catalog": {"revision": 5},
                    "error_code": None,
                },
            ) as refresh_catalog,
            mock.patch(
                "services.erp.mrerp_target_projection.refresh_mrerp_projection"
            ) as refresh_full,
            mock.patch.object(target_refresh, "_finish_mrerp") as finish,
        ):
            processed = target_refresh.process_mrerp_request(request["id"])

        self.assertTrue(processed)
        refresh_catalog.assert_called_once()
        refresh_full.assert_not_called()
        finish.assert_called_once_with(
            request["id"],
            "worker-1",
            success=True,
            error_code=None,
            revision=5,
        )

    def test_invalid_companion_completion_aborts_the_ingestion_transaction(self):
        cursor = _Cursor([])

        with self.assertRaisesRegex(ValueError, "erp.target_refresh_stale_completion"):
            target_refresh.complete_express_refresh_with_cursor(
                cursor,
                request_id="not-a-uuid",
                endpoint_id="endpoint-1",
                account_set_key=r"C:\EXPRESS\TEST",
                scope_kind="account_set",
                revision=3,
            )

        self.assertEqual(cursor.executed, [])


class SelectedAccountRefreshTests(unittest.TestCase):
    identity = {"tenant_id": "tenant-1", "user_id": "user-1"}
    target = {
        "endpoint_id": "endpoint-1",
        "adapter": "mrerp",
        "supports_master_refresh": True,
    }

    def test_matching_succeeded_refresh_is_reused(self):
        with (
            mock.patch.object(
                selected_account_refresh,
                "erp_target_projection_enabled_for",
                return_value=True,
            ),
            mock.patch.object(
                selected_account_refresh.target_refresh,
                "refresh_status",
                return_value={"status": "succeeded", "account_set_key": "6:1"},
            ),
            mock.patch.object(
                selected_account_refresh.target_refresh, "request_refresh"
            ) as request,
            mock.patch.object(
                selected_account_refresh.target_refresh, "process_mrerp_request"
            ) as process,
        ):
            result = selected_account_refresh.ensure_for_editor(
                self.identity,
                self.target,
                "6:1",
                previous_request_id="refresh-1",
            )

        self.assertEqual(result["request_id"], "refresh-1")
        self.assertEqual(result["status"], "succeeded")
        request.assert_not_called()
        process.assert_not_called()

    def test_changed_mrerp_year_gets_new_refresh_and_waits_for_it(self):
        states = [
            {"status": "succeeded", "account_set_key": "15:1"},
            {"status": "requested", "account_set_key": "6:1"},
            {"status": "succeeded", "account_set_key": "6:1"},
        ]
        with (
            mock.patch.object(
                selected_account_refresh,
                "erp_target_projection_enabled_for",
                return_value=True,
            ),
            mock.patch.object(
                selected_account_refresh.target_refresh,
                "refresh_status",
                side_effect=states,
            ),
            mock.patch.object(
                selected_account_refresh.target_refresh,
                "request_refresh",
                return_value={"request_id": "refresh-2", "status": "requested"},
            ) as request,
            mock.patch.object(
                selected_account_refresh.target_refresh,
                "process_mrerp_request",
                return_value=True,
            ) as process,
        ):
            result = selected_account_refresh.ensure_for_editor(
                self.identity,
                self.target,
                "6:1",
                previous_request_id="refresh-1",
            )

        request.assert_called_once_with(
            tenant_id="tenant-1",
            user_id="user-1",
            endpoint_id="endpoint-1",
            account_set_key="6:1",
            adapter="mrerp",
            reason="line_editor_selection",
        )
        process.assert_called_once_with("refresh-2")
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(result["account_set_key"], "6:1")

    def test_express_editor_requests_exact_account_without_cloud_blocking(self):
        target = {**self.target, "adapter": "express"}
        account_key = r"c:\express\new"
        with (
            mock.patch.object(
                selected_account_refresh,
                "erp_target_projection_enabled_for",
                return_value=True,
            ),
            mock.patch.object(
                selected_account_refresh.target_refresh,
                "refresh_status",
                return_value={"status": "requested", "account_set_key": account_key},
            ),
            mock.patch.object(
                selected_account_refresh.target_refresh,
                "request_refresh",
                return_value={"request_id": "refresh-3", "status": "requested"},
            ),
            mock.patch.object(
                selected_account_refresh.target_refresh, "process_mrerp_request"
            ) as process,
        ):
            result = selected_account_refresh.ensure_for_editor(
                self.identity,
                target,
                r"C:\\Express\\NEW",
            )

        process.assert_not_called()
        self.assertEqual(result["status"], "requested")
        self.assertEqual(result["account_set_key"], account_key)


if __name__ == "__main__":
    unittest.main()
