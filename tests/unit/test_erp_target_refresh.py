from __future__ import annotations

import unittest
from unittest import mock

from services.erp import mrerp_refresh_worker, selected_account_refresh, target_refresh


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
        self.exit_args = None

    def __enter__(self):
        return self.cursor

    def __exit__(self, *args):
        self.exit_args = args
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
        self.assertIn("requested_at > started_at", expiry_sql)
        self.assertIn("THEN 'requested'", expiry_sql)
        self.assertEqual(result["request_id"], "22222222-2222-4222-8222-222222222222")
        self.assertTrue(
            any("INSERT INTO erp_target_refresh_requests" in sql for sql, _ in cursor.executed)
        )

    def test_request_replaces_a_current_lease_with_a_new_scan(self):
        old_request_id = "11111111-1111-4111-8111-111111111111"
        new_request_id = "22222222-2222-4222-8222-222222222222"
        cursor = _Cursor(
            [
                {
                    "id": "endpoint-1",
                    "tenant_id": "tenant-1",
                    "owner_tenant_id": "tenant-1",
                    "binding_generation": 0,
                },
                {"id": old_request_id, "status": "leased", "lease_expires_at": object()},
                {"id": new_request_id, "status": "requested"},
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

        self.assertEqual(result["request_id"], new_request_id)
        self.assertEqual(result["status"], "requested")
        supersede_sql = next(sql for sql, _ in cursor.executed if "ERR_REFRESH_SUPERSEDED" in sql)
        self.assertIn("status = 'failed'", supersede_sql)
        self.assertTrue(
            any("INSERT INTO erp_target_refresh_requests" in sql for sql, _ in cursor.executed)
        )

    def test_request_coalesces_before_collection_has_started(self):
        request_id = "11111111-1111-4111-8111-111111111111"
        cursor = _Cursor(
            [
                {
                    "id": "endpoint-1",
                    "tenant_id": "tenant-1",
                    "owner_tenant_id": "tenant-1",
                    "binding_generation": 0,
                },
                {"id": request_id, "status": "requested", "lease_expires_at": None},
                {"id": request_id, "status": "requested"},
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
        self.assertEqual(result["status"], "requested")
        self.assertIn("requested_at = clock_timestamp()", cursor.executed[-1][0])
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

    def test_express_lease_preserves_a_click_recorded_during_an_expired_attempt(self):
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
        self.assertIn("requested_at > started_at", fail_sql)
        self.assertIn("THEN 'requested'", fail_sql)
        self.assertIn("ELSE 'failed'", fail_sql)
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
        self.assertIn("requested_at > started_at", sql)
        self.assertIn("THEN 'requested'", sql)
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

    def test_express_empty_scan_completion_is_terminal_failed(self):
        cursor = _Cursor([])

        completed = target_refresh.complete_express_refresh_with_cursor(
            cursor,
            request_id="11111111-1111-4111-8111-111111111111",
            endpoint_id="endpoint-1",
            account_set_key=target_refresh.ENDPOINT_SCOPE_KEY,
            scope_kind="endpoint",
            error_code="ERR_ACCOUNT_SET_EMPTY",
        )

        self.assertTrue(completed)
        sql, params = cursor.executed[-1]
        self.assertIn("ELSE %s END", sql)
        self.assertEqual(params[0], "failed")
        self.assertEqual(params[1], "ERR_ACCOUNT_SET_EMPTY")
        self.assertIsNone(params[2])

    def test_mrerp_claim_preserves_a_click_recorded_during_an_expired_attempt(self):
        cursor = _Cursor([None])
        request_id = "11111111-1111-4111-8111-111111111111"
        with mock.patch.object(target_refresh.db, "get_cursor", return_value=_Context(cursor)):
            claimed = target_refresh._claim_mrerp(request_id)

        self.assertIsNone(claimed)
        expiry_sql = cursor.executed[0][0]
        claim_sql = cursor.executed[1][0]
        self.assertIn("ERR_REFRESH_LEASE_EXPIRED", expiry_sql)
        self.assertIn("lease_expires_at <= clock_timestamp()", expiry_sql)
        self.assertIn("requested_at > started_at", expiry_sql)
        self.assertIn("THEN 'requested'", expiry_sql)
        self.assertIn("r.status = 'requested'", claim_sql)
        self.assertNotIn("r.status = 'leased'", claim_sql)

    def test_mrerp_processor_commits_the_collected_result(self):
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
        result = {"ok": True, "observed_at": object(), "observations": [{"adapter": "mrerp"}]}
        with (
            mock.patch.object(target_refresh, "_claim_mrerp", return_value=request),
            mock.patch.object(mrerp_refresh_worker, "collect", return_value=result) as collect,
            mock.patch.object(mrerp_refresh_worker, "commit", return_value=True) as commit,
        ):
            processed = target_refresh.process_mrerp_request(request["id"])

        self.assertTrue(processed)
        collect.assert_called_once_with(
            request,
            endpoint_scope_key=target_refresh.ENDPOINT_SCOPE_KEY,
        )
        commit.assert_called_once_with(request, result)

    def test_mrerp_processor_rescans_after_config_changes_during_collection(self):
        request = {
            **self._leased_mrerp_request(),
            "user_id": "user-1",
            "config": {},
        }
        first_result = {"ok": True, "observations": [{"scan": 1}]}
        second_result = {"ok": True, "observations": [{"scan": 2}]}
        with (
            mock.patch.object(target_refresh, "_claim_mrerp", side_effect=[request, request]),
            mock.patch.object(
                mrerp_refresh_worker,
                "collect",
                side_effect=[first_result, second_result],
            ) as collect,
            mock.patch.object(
                mrerp_refresh_worker,
                "commit",
                side_effect=[False, True],
            ) as commit,
        ):
            processed = target_refresh.process_mrerp_request(request["id"])

        self.assertTrue(processed)
        self.assertEqual(collect.call_count, 2)
        self.assertEqual(commit.call_count, 2)

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
        account_result = {
            "ok": True,
            "companies": [{"comidyear": "6", "seldb": "1", "label": "TEST2019"}],
        }
        with mock.patch.object(
            mrerp_refresh_worker.projection, "_run_live", return_value=account_result
        ) as run_live:
            result = mrerp_refresh_worker.collect(
                request,
                endpoint_scope_key=target_refresh.ENDPOINT_SCOPE_KEY,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(len(result["observations"]), 1)
        self.assertNotIn("account_set_key", result["observations"][0])
        run_live.assert_called_once_with(
            mrerp_refresh_worker.projection.test_mrerp_endpoint,
            {},
        )

    def test_mrerp_account_collection_does_not_publish_before_fence(self):
        request = {
            "account_set_key": "6:1",
            "config": {},
        }
        results = [
            {
                "ok": True,
                "companies": [{"comidyear": "6", "seldb": "1", "label": "TEST2019"}],
            },
            {"ok": True, "products": [{"code": "P1", "name": "Product"}]},
            {"ok": True, "customers": [{"code": "C1", "name": "Customer"}]},
        ]
        with (
            mock.patch.object(
                mrerp_refresh_worker.projection, "_run_live", side_effect=results
            ) as run_live,
            mock.patch.object(mrerp_refresh_worker.projection, "publish_projection") as publish,
        ):
            result = mrerp_refresh_worker.collect(
                request,
                endpoint_scope_key=target_refresh.ENDPOINT_SCOPE_KEY,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(len(result["observations"]), 1)
        self.assertEqual(result["observations"][0]["account_set_key"], "6:1")
        self.assertEqual(run_live.call_count, 3)
        publish.assert_not_called()

    @staticmethod
    def _leased_mrerp_request():
        return {
            "id": "11111111-1111-4111-8111-111111111111",
            "tenant_id": "22222222-2222-4222-8222-222222222222",
            "endpoint_id": "33333333-3333-4333-8333-333333333333",
            "account_set_key": "6:1",
            "lease_owner": "worker-1",
        }

    def test_mrerp_commit_fences_before_publishing_in_the_same_transaction(self):
        request = self._leased_mrerp_request()
        cursor = _Cursor(
            [
                {
                    "id": request["id"],
                    "requested_at": 1,
                    "started_at": 2,
                }
            ]
        )
        context = _Context(cursor)
        result = {"ok": True, "observed_at": object(), "observations": [{"raw": True}]}
        with (
            mock.patch.object(mrerp_refresh_worker.db, "get_cursor", return_value=context),
            mock.patch.object(
                mrerp_refresh_worker.projection,
                "claim_endpoint_tenant_with_cursor",
                return_value={"config": {}},
            ) as claim_endpoint,
            mock.patch.object(
                mrerp_refresh_worker, "normalize_projection", return_value="normalized"
            ),
            mock.patch.object(
                mrerp_refresh_worker, "publish_with_cursor", return_value={"revision": 7}
            ) as publish,
        ):
            mrerp_refresh_worker.commit(request, result)

        claim_endpoint.assert_called_once_with(
            cursor,
            tenant_id=request["tenant_id"],
            endpoint_id=request["endpoint_id"],
        )
        fence_sql = cursor.executed[0][0]
        finish_sql = cursor.executed[-1][0]
        self.assertIn("r.status = 'leased'", fence_sql)
        self.assertIn("r.lease_owner = %s", fence_sql)
        self.assertIn("r.lease_expires_at > clock_timestamp()", fence_sql)
        self.assertIn("NOT EXISTS", fence_sql)
        self.assertIn("lease_expires_at > clock_timestamp()", finish_sql)
        publish.assert_called_once_with(
            cursor,
            tenant_id=request["tenant_id"],
            endpoint_id=request["endpoint_id"],
            projection="normalized",
        )
        self.assertEqual(cursor.executed[-1][1][2], 7)
        self.assertIsNone(context.exit_args[0])

    def test_stale_mrerp_worker_cannot_publish(self):
        request = self._leased_mrerp_request()
        cursor = _Cursor([None])
        context = _Context(cursor)
        result = {"ok": True, "observed_at": object(), "observations": [{"raw": True}]}
        with (
            mock.patch.object(mrerp_refresh_worker.db, "get_cursor", return_value=context),
            mock.patch.object(
                mrerp_refresh_worker.projection,
                "claim_endpoint_tenant_with_cursor",
                return_value={"config": {}},
            ),
            mock.patch.object(mrerp_refresh_worker, "publish_with_cursor") as publish,
        ):
            with self.assertRaisesRegex(ValueError, "erp.target_refresh_stale_completion"):
                mrerp_refresh_worker.commit(request, result)

        publish.assert_not_called()
        self.assertIs(context.exit_args[0], ValueError)

    def test_mrerp_commit_requeues_when_clicked_during_collection(self):
        request = {**self._leased_mrerp_request(), "config": {"seldb": "1"}}
        cursor = _Cursor(
            [
                {
                    "id": request["id"],
                    "requested_at": 3,
                    "started_at": 2,
                }
            ]
        )
        result = {"ok": True, "observed_at": object(), "observations": [{"raw": True}]}
        with (
            mock.patch.object(mrerp_refresh_worker.db, "get_cursor", return_value=_Context(cursor)),
            mock.patch.object(
                mrerp_refresh_worker.projection,
                "claim_endpoint_tenant_with_cursor",
                return_value={"config": {"seldb": "1"}},
            ),
            mock.patch.object(mrerp_refresh_worker, "publish_with_cursor") as publish,
        ):
            completed = mrerp_refresh_worker.commit(request, result)

        self.assertFalse(completed)
        publish.assert_not_called()
        requeue_sql = cursor.executed[-1][0]
        self.assertIn("SET status = 'requested'", requeue_sql)
        self.assertIn("started_at = NULL", requeue_sql)

    def test_mrerp_commit_requeues_when_endpoint_config_changed(self):
        request = {**self._leased_mrerp_request(), "config": {"seldb": "1"}}
        cursor = _Cursor(
            [
                {
                    "id": request["id"],
                    "requested_at": 1,
                    "started_at": 2,
                }
            ]
        )
        result = {"ok": True, "observed_at": object(), "observations": [{"raw": True}]}
        with (
            mock.patch.object(mrerp_refresh_worker.db, "get_cursor", return_value=_Context(cursor)),
            mock.patch.object(
                mrerp_refresh_worker.projection,
                "claim_endpoint_tenant_with_cursor",
                return_value={"config": {"seldb": "2"}},
            ),
            mock.patch.object(mrerp_refresh_worker, "publish_with_cursor") as publish,
        ):
            completed = mrerp_refresh_worker.commit(request, result)

        self.assertFalse(completed)
        publish.assert_not_called()
        self.assertIn("SET status = 'requested'", cursor.executed[-1][0])

    def test_mrerp_commit_rolls_back_if_lease_expires_during_publication(self):
        request = self._leased_mrerp_request()
        cursor = _Cursor(
            [
                {
                    "id": request["id"],
                    "requested_at": 1,
                    "started_at": 2,
                }
            ]
        )
        context = _Context(cursor)
        result = {"ok": True, "observed_at": object(), "observations": [{"raw": True}]}

        def publish_then_expire(*_args, **_kwargs):
            cursor.rowcount = 0
            return {"revision": 8}

        with (
            mock.patch.object(mrerp_refresh_worker.db, "get_cursor", return_value=context),
            mock.patch.object(
                mrerp_refresh_worker.projection,
                "claim_endpoint_tenant_with_cursor",
                return_value={"config": {}},
            ),
            mock.patch.object(
                mrerp_refresh_worker, "normalize_projection", return_value="normalized"
            ),
            mock.patch.object(
                mrerp_refresh_worker, "publish_with_cursor", side_effect=publish_then_expire
            ),
        ):
            with self.assertRaisesRegex(ValueError, "erp.target_refresh_stale_completion"):
                mrerp_refresh_worker.commit(request, result)

        self.assertIs(context.exit_args[0], ValueError)

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
