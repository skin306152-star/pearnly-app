import unittest
from types import SimpleNamespace
from unittest import mock

from fastapi import HTTPException

from core import db  # noqa: F401
from routes import erp_intake_routes as routes
from routes import history_routes
from services.erp.express_push.posting_kind import item_posting_kinds
from services.ocr_history import staged
from services.ocr.recognize import core as recognize_core


class _Cur:
    def __init__(self):
        self.rowcount = 2
        self.sql = []

    def execute(self, sql, params=None):
        self.sql.append((sql, params))

    def fetchall(self):
        return []


class _Ctx:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *args):
        return False


class ErpIntakeContractTests(unittest.TestCase):
    def _authorize(self, user, invited=True):
        with (
            mock.patch.object(routes, "get_current_user_from_request", return_value=user),
            mock.patch.object(routes, "erp_portal_enabled_for", return_value=invited),
        ):
            return routes._authorize(mock.MagicMock())

    def test_main_and_cowork_sessions_are_rejected(self):
        for entry in ("main", "cowork"):
            with self.assertRaises(HTTPException) as ctx:
                self._authorize({"id": "u1", "tenant_id": "t1", "entry": entry})
            self.assertEqual(ctx.exception.status_code, 403)
            self.assertEqual(ctx.exception.detail, "authz.entrance_scope")

    def test_erp_entry_without_invite_is_rejected(self):
        with self.assertRaises(HTTPException) as ctx:
            self._authorize(
                {"id": "u1", "tenant_id": "t1", "entry": "erp", "role": "owner"},
                invited=False,
            )
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "erp.not_found")

    def test_invited_erp_entry_in_same_tenant_is_allowed(self):
        user = {"id": "u1", "tenant_id": "t1", "entry": "erp", "role": "owner"}
        self.assertIs(self._authorize(user), user)

    def test_line_declarations_support_mixed_and_reject_missing(self):
        self.assertEqual(
            item_posting_kinds(
                [{"name": "A", "posting_kind": "stock"}, {"name": "B", "posting_kind": "service"}]
            ),
            ["stock", "service"],
        )
        self.assertEqual(
            item_posting_kinds([{"name": "A", "posting_kind": "stock"}, {"name": "B"}]), []
        )

    def test_discard_sql_is_staged_and_not_converted_scoped(self):
        cur = _Cur()
        with mock.patch.object(staged.db, "get_cursor_rls", return_value=_Ctx(cur)):
            deleted, paths = staged.discard_staged_ocr_history_with_pdf_paths(
                "u1", ["h1"], tenant_id="t1"
            )
        self.assertEqual((deleted, paths), (2, []))
        self.assertEqual(len(cur.sql), 2)
        for sql, params in cur.sql:
            self.assertIn("staged = TRUE", sql)
            self.assertIn("user_id = %s::uuid", sql)
            self.assertIn("NOT EXISTS", sql)
            self.assertEqual(params, (["h1"], "u1"))

    def test_every_staged_upload_bypasses_legacy_cache_path(self):
        for entry in ("erp", "cowork"):
            user = {
                "id": "u1",
                "tenant_id": "t1",
                "entry": entry,
                "plan": "free",
            }
            with (
                self.subTest(entry=entry),
                mock.patch.object(recognize_core, "_ocr_get_cached") as get_cached,
                mock.patch.object(
                    recognize_core.db,
                    "get_billing_status_combined",
                    side_effect=RuntimeError("stop after cache decision"),
                ),
            ):
                with self.assertRaises(HTTPException) as ctx:
                    recognize_core.run_recognition_core(
                        user,
                        b"image",
                        SimpleNamespace(filename="invoice.jpg"),
                        ws_client_id=1,
                        staged=True,
                        direction="purchase",
                    )
                self.assertEqual(ctx.exception.status_code, 503)
                get_cached.assert_not_called()


class ErpWebConfirmTests(unittest.IsolatedAsyncioTestCase):
    async def test_erp_commit_rejects_history_without_formal_document(self):
        cur = _Cur()
        user = {"id": "u1", "tenant_id": "t1", "entry": "erp", "role": "owner"}
        with (
            mock.patch.object(history_routes, "get_current_user_from_request", return_value=user),
            mock.patch.object(history_routes, "_check_history_access"),
            mock.patch.object(history_routes, "_tid", return_value="t1"),
            mock.patch.object(
                history_routes.erp_confirmation_access,
                "commit_shared_confirmation",
                return_value=None,
            ),
            mock.patch.object(history_routes.db, "get_cursor_rls", return_value=_Ctx(cur)),
            mock.patch.object(
                history_routes.convert_svc,
                "unconverted_owned_history_ids",
                return_value=["h1"],
            ),
            mock.patch.object(history_routes, "commit_staged_ocr_history") as commit,
        ):
            with self.assertRaises(HTTPException) as ctx:
                await history_routes.ocr_commit(
                    history_routes.OcrCommitRequest(ids=["h1"]), mock.MagicMock()
                )
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail["code"], "erp.formal_document_required")
        commit.assert_not_called()

    async def test_erp_commit_allows_converted_history(self):
        cur = _Cur()
        user = {"id": "u1", "tenant_id": "t1", "entry": "erp", "role": "owner"}
        with (
            mock.patch.object(history_routes, "get_current_user_from_request", return_value=user),
            mock.patch.object(history_routes, "_check_history_access"),
            mock.patch.object(history_routes, "_tid", return_value="t1"),
            mock.patch.object(
                history_routes.erp_confirmation_access,
                "commit_shared_confirmation",
                return_value=None,
            ),
            mock.patch.object(history_routes.db, "get_cursor_rls", return_value=_Ctx(cur)),
            mock.patch.object(
                history_routes.convert_svc,
                "unconverted_owned_history_ids",
                return_value=[],
            ),
            mock.patch.object(history_routes, "commit_staged_ocr_history", return_value=1),
        ):
            result = await history_routes.ocr_commit(
                history_routes.OcrCommitRequest(ids=["h1"]), mock.MagicMock()
            )
        self.assertEqual(result, {"ok": True, "committed": 1})

    async def test_non_erp_commit_keeps_existing_behavior(self):
        user = {"id": "u1", "tenant_id": "t1", "entry": "pos"}
        with (
            mock.patch.object(history_routes, "get_current_user_from_request", return_value=user),
            mock.patch.object(history_routes, "_check_history_access"),
            mock.patch.object(history_routes, "_tid", return_value="t1"),
            mock.patch.object(
                history_routes.erp_confirmation_access,
                "commit_shared_confirmation",
                return_value=None,
            ) as shared_commit,
            mock.patch.object(history_routes.db, "get_cursor_rls") as get_cursor,
            mock.patch.object(history_routes, "commit_staged_ocr_history", return_value=1),
        ):
            result = await history_routes.ocr_commit(
                history_routes.OcrCommitRequest(ids=["h1"]), mock.MagicMock()
            )
        self.assertEqual(result, {"ok": True, "committed": 1})
        shared_commit.assert_called_once()
        get_cursor.assert_not_called()

    async def test_shared_commit_returns_atomic_result_without_legacy_mutation(self):
        user = {"id": "u1", "tenant_id": "t1", "entry": "cowork"}
        with (
            mock.patch.object(history_routes, "get_current_user_from_request", return_value=user),
            mock.patch.object(history_routes, "_check_history_access"),
            mock.patch.object(history_routes, "_tid", return_value="t1"),
            mock.patch.object(
                history_routes.erp_confirmation_access,
                "commit_shared_confirmation",
                return_value=2,
            ) as shared_commit,
            mock.patch.object(history_routes.db, "get_cursor_rls") as legacy_cursor,
            mock.patch.object(history_routes, "commit_staged_ocr_history") as legacy_commit,
        ):
            result = await history_routes.ocr_commit(
                history_routes.OcrCommitRequest(ids=["h1", "h2"]), mock.MagicMock()
            )
        self.assertEqual(result, {"ok": True, "committed": 2})
        shared_commit.assert_called_once_with(mock.ANY, user, "t1", ["h1", "h2"])
        legacy_cursor.assert_not_called()
        legacy_commit.assert_not_called()

    async def test_shared_commit_denials_have_zero_legacy_side_effects(self):
        cases = (
            HTTPException(403, detail="authz.forbidden"),
            HTTPException(404, detail="history.not_found"),
            HTTPException(
                409,
                detail={"code": "erp.formal_document_required", "history_ids": ["h1"]},
            ),
        )
        user = {"id": "u1", "tenant_id": "t1", "entry": "erp", "role": "owner"}
        for failure in cases:
            with self.subTest(status=failure.status_code):
                with (
                    mock.patch.object(
                        history_routes, "get_current_user_from_request", return_value=user
                    ),
                    mock.patch.object(history_routes, "_check_history_access"),
                    mock.patch.object(history_routes, "_tid", return_value="t1"),
                    mock.patch.object(
                        history_routes.erp_confirmation_access,
                        "commit_shared_confirmation",
                        side_effect=failure,
                    ),
                    mock.patch.object(history_routes.db, "get_cursor_rls") as legacy_cursor,
                    mock.patch.object(history_routes, "commit_staged_ocr_history") as legacy_commit,
                ):
                    with self.assertRaises(HTTPException) as caught:
                        await history_routes.ocr_commit(
                            history_routes.OcrCommitRequest(ids=["h1"]), mock.MagicMock()
                        )
                self.assertEqual(caught.exception.status_code, failure.status_code)
                legacy_cursor.assert_not_called()
                legacy_commit.assert_not_called()

    async def test_successful_conversion_finishes_resolved_staged_histories(self):
        cur = _Cur()
        result = {
            "converted": [{"history_id": "h1"}],
            "skipped": [{"history_id": "h2", "reason": "already_converted"}],
        }
        user = {"id": "u1", "tenant_id": "t1", "entry": "erp", "role": "owner"}
        preflight = history_routes.erp_confirmation_access.ConfirmationPreflight(
            ("purchase", "sales"),
            (),
            (("h1", "purchase"), ("h2", "sales")),
        )
        with (
            mock.patch.object(history_routes, "get_current_user_from_request", return_value=user),
            mock.patch.object(history_routes, "_check_history_access"),
            mock.patch.object(history_routes, "_tid", return_value="t1"),
            mock.patch.object(
                history_routes.db, "get_cursor_rls", return_value=_Ctx(cur)
            ) as get_cursor,
            mock.patch.object(
                history_routes.erp_confirmation_access,
                "guard_confirmation",
                return_value=preflight,
            ) as guard,
            mock.patch.object(
                history_routes.erp_confirmation_access, "finish_resolved_histories"
            ) as finish,
            mock.patch.object(
                history_routes.convert_svc, "validate_erp_histories", return_value={}
            ),
            mock.patch.object(history_routes.convert_svc, "convert_histories", return_value=result),
        ):
            response = await history_routes.ocr_convert_documents(
                history_routes.OcrConvertRequest(history_ids=["h1", "h2"], workspace_client_id=1),
                mock.MagicMock(),
            )
        self.assertEqual(response, result)
        finish.assert_called_once_with(cur, preflight, "t1", "u1", 1, {"h1", "h2"})
        guard.assert_called_once_with(cur, mock.ANY, user, "t1", 1, ["h1", "h2"])
        get_cursor.assert_called_once_with(
            tenant_id="t1", workspace_client_id=1, user_id="u1", commit=True
        )

    async def test_confirmation_guard_failure_keeps_batch_zero_write(self):
        cur = _Cur()
        user = {"id": "u1", "tenant_id": "t1", "entry": "cowork"}
        with (
            mock.patch.object(history_routes, "get_current_user_from_request", return_value=user),
            mock.patch.object(history_routes, "_check_history_access"),
            mock.patch.object(history_routes, "_tid", return_value="t1"),
            mock.patch.object(history_routes.db, "get_cursor_rls", return_value=_Ctx(cur)),
            mock.patch.object(
                history_routes.erp_confirmation_access,
                "guard_confirmation",
                side_effect=HTTPException(404, detail="authz.not_found"),
            ),
            mock.patch.object(history_routes.convert_svc, "convert_histories") as convert,
        ):
            with self.assertRaises(HTTPException) as caught:
                await history_routes.ocr_convert_documents(
                    history_routes.OcrConvertRequest(history_ids=["h1"], workspace_client_id=7),
                    mock.MagicMock(),
                )
        self.assertEqual(caught.exception.status_code, 404)
        self.assertEqual(caught.exception.detail, "authz.not_found")
        convert.assert_not_called()


if __name__ == "__main__":
    unittest.main()
