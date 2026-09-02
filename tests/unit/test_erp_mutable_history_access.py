# -*- coding: utf-8 -*-
"""Shared ERP history mutations are actor-scoped, workspace-scoped, and immutable after formalization."""

import unittest
from unittest import mock

from fastapi import HTTPException

from routes import history_assign_routes, history_routes
from services.intake_bridge import mutable_history_access as access

TENANT = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
ACTOR = "11111111-1111-1111-1111-111111111111"
HISTORY = "cccccccc-cccc-cccc-cccc-cccccccc0001"
OTHER_HISTORY = "cccccccc-cccc-cccc-cccc-cccccccc0002"
WORKSPACE = 101


class _Context:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *_args):
        return False


def _history_row(history_id=HISTORY, workspace=WORKSPACE, pages=None):
    return {
        "id": history_id,
        "workspace_client_id": workspace,
        "pages": pages if pages is not None else [{"fields": {"seller_tax": "0105537000881"}}],
    }


class MutableHistoryLockTests(unittest.TestCase):
    def test_lock_order_is_workspace_then_history_and_formal_ignores_current_workspace(self):
        cur = mock.Mock()
        cur.fetchall.side_effect = (
            [_history_row()],
            [{"id": WORKSPACE}],
            [_history_row()],
            [],
            [],
        )
        with mock.patch.object(access, "check_workspace_scope") as scope:
            rows = access._lock_mutable_histories(
                cur,
                mock.sentinel.request,
                {"id": ACTOR, "entry": "main"},
                TENANT,
                ACTOR,
                [HISTORY],
            )
        self.assertEqual(rows[HISTORY]["workspace_client_id"], WORKSPACE)
        sql = [call.args[0] for call in cur.execute.call_args_list]
        self.assertNotIn("FOR UPDATE", sql[0])
        self.assertIn("workspace_clients", sql[1])
        self.assertIn("is_active = TRUE", sql[1])
        self.assertIn("ORDER BY id FOR SHARE", sql[1])
        self.assertIn("ORDER BY id FOR UPDATE", sql[2])
        self.assertNotIn("workspace_client_id", sql[3])
        self.assertNotIn("workspace_client_id", sql[4])
        scope.assert_called_once_with(mock.sentinel.request, mock.ANY, WORKSPACE)

    def test_missing_other_actor_and_inactive_workspace_fail_before_history_lock(self):
        cases = (
            (([],), "history.not_found"),
            (([_history_row()], []), "authz.not_found"),
        )
        for results, detail in cases:
            with self.subTest(detail=detail):
                cur = mock.Mock()
                cur.fetchall.side_effect = results
                with self.assertRaises(HTTPException) as caught:
                    access._lock_mutable_histories(
                        cur,
                        mock.sentinel.request,
                        {"id": ACTOR, "entry": "erp"},
                        TENANT,
                        ACTOR,
                        [HISTORY],
                    )
                self.assertEqual(caught.exception.status_code, 404)
                self.assertEqual(caught.exception.detail, detail)
                sql = [call.args[0] for call in cur.execute.call_args_list]
                self.assertFalse(any("FOR UPDATE" in statement for statement in sql))

    def test_workspace_change_between_snapshot_and_lock_fails_closed(self):
        cur = mock.Mock()
        cur.fetchall.side_effect = (
            [_history_row(workspace=WORKSPACE)],
            [{"id": WORKSPACE}],
            [_history_row(workspace=WORKSPACE + 1)],
        )
        with (
            mock.patch.object(access, "check_workspace_scope"),
            self.assertRaises(HTTPException) as caught,
        ):
            access._lock_mutable_histories(
                cur,
                mock.sentinel.request,
                {"id": ACTOR, "entry": "cowork"},
                TENANT,
                ACTOR,
                [HISTORY],
            )
        self.assertEqual(caught.exception.status_code, 404)
        self.assertEqual(caught.exception.detail, "history.not_found")

    def test_formal_document_in_any_workspace_locks_the_source(self):
        cur = mock.Mock()
        cur.fetchall.side_effect = (
            [_history_row()],
            [{"id": WORKSPACE}],
            [_history_row()],
            [{"history_id": HISTORY}],
            [],
        )
        with (
            mock.patch.object(access, "check_workspace_scope"),
            self.assertRaises(HTTPException) as caught,
        ):
            access._lock_mutable_histories(
                cur,
                mock.sentinel.request,
                {"id": ACTOR, "entry": "main"},
                TENANT,
                ACTOR,
                [HISTORY],
            )
        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(caught.exception.detail["code"], "erp.formal_document_locked")
        self.assertEqual(caught.exception.detail["history_ids"], [HISTORY])
        formal_sql = cur.execute.call_args_list[3].args[0]
        self.assertNotIn("workspace_client_id", formal_sql)


class MutableHistoryWriteTests(unittest.TestCase):
    def test_non_erp_context_never_opens_a_formal_mutation_transaction(self):
        for entry in ("main", "cowork", "pos", "ai", "dms", "daily", None, "unknown"):
            with self.subTest(entry=entry):
                user = {"id": ACTOR, "tenant_id": TENANT, "entry": entry}
                with mock.patch.object(access.db, "get_cursor_rls") as cursor:
                    result = access.update_history_pages(
                        mock.sentinel.request, user, TENANT, HISTORY, [{"fields": {}}]
                    )
                self.assertIsNone(result)
                cursor.assert_not_called()

    def test_pages_update_is_actor_and_workspace_bound_in_one_transaction(self):
        cur = mock.Mock(rowcount=1)
        pages = [{"fields": {"invoice_number": "INV-1", "total_amount": "100"}}]
        with (
            mock.patch.object(access, "_shared_actor", return_value=ACTOR),
            mock.patch.object(access.db, "get_cursor_rls", return_value=_Context(cur)) as cursor,
            mock.patch.object(
                access,
                "_lock_mutable_history",
                return_value=(HISTORY, WORKSPACE, _history_row(pages=pages)),
            ),
            mock.patch.object(
                access.history_mutations,
                "_extract_summary_fields",
                return_value={
                    "invoice_no": "INV-1",
                    "invoice_date": None,
                    "seller_name": None,
                    "total_amount": 100,
                },
            ),
            mock.patch.object(access, "_archive_values", return_value=(None, None)),
            mock.patch.object(access, "_record_edit_feedback") as feedback,
        ):
            result = access.update_history_pages(
                mock.sentinel.request,
                {"id": ACTOR, "entry": "main"},
                TENANT,
                HISTORY,
                pages,
            )
        self.assertTrue(result)
        cursor.assert_called_once_with(tenant_id=TENANT, user_id=ACTOR, commit=True)
        sql, params = cur.execute.call_args.args
        self.assertIn("tenant_id = %s::uuid AND user_id = %s::uuid", sql)
        self.assertIn("workspace_client_id = %s", sql)
        self.assertEqual(params[-4:], (HISTORY, TENANT, ACTOR, WORKSPACE))
        feedback.assert_called_once_with(ACTOR, TENANT, HISTORY, pages)

    def test_assign_workspace_locks_source_and_target_in_sorted_workspace_phase(self):
        cur = mock.Mock(rowcount=1)
        with (
            mock.patch.object(access, "_shared_actor", return_value=ACTOR),
            mock.patch.object(access.db, "get_cursor_rls", return_value=_Context(cur)),
            mock.patch.object(
                access,
                "_lock_mutable_history",
                return_value=(HISTORY, WORKSPACE, _history_row()),
            ) as lock,
        ):
            result = access.assign_workspace(
                mock.sentinel.request,
                {"id": ACTOR, "entry": "cowork"},
                TENANT,
                HISTORY,
                WORKSPACE + 1,
            )
        self.assertTrue(result)
        self.assertEqual(lock.call_args.kwargs["additional_workspace_ids"], (WORKSPACE + 1,))
        sql, params = cur.execute.call_args.args
        self.assertIn("user_id = %s::uuid", sql)
        self.assertEqual(params, (WORKSPACE + 1, HISTORY, TENANT, ACTOR, WORKSPACE))

    def test_assign_client_locks_history_before_client(self):
        cur = mock.Mock(rowcount=1)
        cur.fetchone.return_value = {"id": 7}
        order = []

        def lock(*_args, **_kwargs):
            order.append("history")
            return HISTORY, WORKSPACE, _history_row()

        def execute(sql, _params):
            if "FROM clients" in sql:
                order.append("client")
            elif sql.startswith("UPDATE ocr_history"):
                order.append("update")

        cur.execute.side_effect = execute
        with (
            mock.patch.object(access, "_shared_actor", return_value=ACTOR),
            mock.patch.object(access.db, "get_cursor_rls", return_value=_Context(cur)),
            mock.patch.object(access, "_lock_mutable_history", side_effect=lock),
        ):
            result = access.assign_client(
                mock.sentinel.request,
                {"id": ACTOR, "entry": "main"},
                TENANT,
                HISTORY,
                7,
            )
        self.assertTrue(result)
        self.assertEqual(order, ["history", "client", "update"])

    def test_batch_delete_returns_paths_only_after_atomic_preflight(self):
        cur = mock.Mock()
        cur.fetchall.return_value = [
            {"pdf_storage_path": "one.pdf"},
            {"pdf_storage_path": None},
        ]
        with (
            mock.patch.object(access, "_shared_actor", return_value=ACTOR),
            mock.patch.object(access.db, "get_cursor_rls", return_value=_Context(cur)),
            mock.patch.object(access, "_lock_mutable_histories") as lock,
        ):
            result = access.delete_histories(
                mock.sentinel.request,
                {"id": ACTOR, "entry": "erp"},
                TENANT,
                [HISTORY, OTHER_HISTORY],
            )
        self.assertEqual(result, (2, ["one.pdf"]))
        lock.assert_called_once()
        sql, params = cur.execute.call_args.args
        self.assertTrue(sql.startswith("DELETE FROM ocr_history"))
        self.assertIn("tenant_id = %s::uuid", sql)
        self.assertIn("user_id = %s::uuid", sql)
        self.assertEqual(params, ([HISTORY, OTHER_HISTORY], TENANT, ACTOR))


class MutableHistoryRouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_put_and_v1_alias_never_fall_back_after_shared_denial(self):
        user = {"id": ACTOR, "tenant_id": TENANT, "entry": "main"}
        for handler in (history_routes.history_update, history_routes.v1_history_update):
            with self.subTest(handler=handler.__name__):
                with (
                    mock.patch.object(
                        history_routes, "get_current_user_from_request", return_value=user
                    ),
                    mock.patch.object(history_routes, "_check_history_access"),
                    mock.patch.object(history_routes, "_tid", return_value=TENANT),
                    mock.patch.object(
                        history_routes.mutable_history_access,
                        "update_history_pages",
                        side_effect=HTTPException(
                            409, detail={"code": "erp.formal_document_locked"}
                        ),
                    ),
                    mock.patch.object(history_routes, "update_ocr_history_pages") as legacy,
                ):
                    with self.assertRaises(HTTPException) as caught:
                        await handler(
                            HISTORY,
                            history_routes.HistoryUpdateRequest(pages=[{"fields": {}}]),
                            mock.MagicMock(),
                        )
                self.assertEqual(caught.exception.status_code, 409)
                legacy.assert_not_called()

    async def test_posting_and_delete_denials_have_zero_legacy_side_effects(self):
        user = {"id": ACTOR, "tenant_id": TENANT, "entry": "erp"}
        cases = (
            (
                history_routes.history_update_posting,
                history_routes.HistoryPostingRequest(payment="cash"),
                "update_history_posting",
                "update_history_posting_manual",
            ),
            (
                history_routes.history_delete,
                None,
                "delete_histories",
                "delete_ocr_history_with_pdf_paths",
            ),
        )
        for handler, payload, shared_name, legacy_name in cases:
            with self.subTest(handler=handler.__name__):
                with (
                    mock.patch.object(
                        history_routes, "get_current_user_from_request", return_value=user
                    ),
                    mock.patch.object(history_routes, "_check_history_access"),
                    mock.patch.object(history_routes, "_tid", return_value=TENANT),
                    mock.patch.object(
                        history_routes.mutable_history_access,
                        shared_name,
                        side_effect=HTTPException(404, detail="history.not_found"),
                    ),
                    mock.patch.object(history_routes, legacy_name) as legacy,
                ):
                    with self.assertRaises(HTTPException) as caught:
                        if payload is None:
                            await handler(HISTORY, mock.MagicMock())
                        else:
                            await handler(HISTORY, payload, mock.MagicMock())
                self.assertEqual(caught.exception.status_code, 404)
                legacy.assert_not_called()

    async def test_batch_delete_and_assign_denials_never_call_tenant_wide_stores(self):
        user = {"id": ACTOR, "tenant_id": TENANT, "entry": "cowork"}
        with (
            mock.patch.object(history_routes, "get_current_user_from_request", return_value=user),
            mock.patch.object(history_routes, "_check_history_access"),
            mock.patch.object(history_routes, "_tid", return_value=TENANT),
            mock.patch.object(
                history_routes.mutable_history_access,
                "delete_histories",
                side_effect=HTTPException(404, detail="history.not_found"),
            ),
            mock.patch.object(history_routes, "delete_ocr_history_with_pdf_paths") as legacy_delete,
        ):
            with self.assertRaises(HTTPException):
                await history_routes.history_batch_delete(
                    history_routes.HistoryBatchDeleteRequest(ids=[HISTORY, OTHER_HISTORY]),
                    mock.MagicMock(),
                )
        legacy_delete.assert_not_called()

        with (
            mock.patch.object(
                history_assign_routes, "get_current_user_from_request", return_value=user
            ),
            mock.patch.object(history_assign_routes, "_check_history_access"),
            mock.patch.object(history_assign_routes, "_tid", return_value=TENANT),
            mock.patch.object(
                history_assign_routes.mutable_history_access,
                "assign_workspace",
                side_effect=HTTPException(409, detail="erp.formal_document_locked"),
            ),
            mock.patch.object(
                history_assign_routes.db, "update_history_workspace_client_id"
            ) as legacy_assign,
        ):
            with self.assertRaises(HTTPException):
                await history_assign_routes.api_assign_workspace(
                    HISTORY,
                    history_assign_routes.AssignWorkspaceRequest(workspace_client_id=WORKSPACE + 1),
                    mock.MagicMock(),
                )
        legacy_assign.assert_not_called()

        with (
            mock.patch.object(
                history_assign_routes, "get_current_user_from_request", return_value=user
            ),
            mock.patch.object(history_assign_routes, "_tid", return_value=TENANT),
            mock.patch.object(
                history_assign_routes.db, "get_visible_client_ids_for_user", return_value=None
            ),
            mock.patch.object(
                history_assign_routes.mutable_history_access,
                "assign_client",
                side_effect=HTTPException(404, detail="history.not_found"),
            ),
            mock.patch.object(
                history_assign_routes.db, "assign_invoice_to_client"
            ) as legacy_client,
        ):
            with self.assertRaises(HTTPException):
                await history_assign_routes.api_assign_client(
                    HISTORY,
                    history_assign_routes.AssignClientRequest(client_id=None),
                    mock.MagicMock(),
                )
        legacy_client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
