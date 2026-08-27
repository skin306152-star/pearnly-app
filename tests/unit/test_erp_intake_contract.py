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
            self._authorize({"id": "u1", "tenant_id": "t1", "entry": "erp"}, invited=False)
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "erp.not_found")

    def test_invited_erp_entry_in_same_tenant_is_allowed(self):
        user = {"id": "u1", "tenant_id": "t1", "entry": "erp"}
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

    def test_erp_staged_upload_bypasses_legacy_cache_autopush_path(self):
        user = {
            "id": "u1",
            "tenant_id": "t1",
            "entry": "erp",
            "plan": "free",
        }
        with (
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
    async def test_successful_conversion_finishes_resolved_staged_histories(self):
        cur = _Cur()
        result = {
            "converted": [{"history_id": "h1"}],
            "skipped": [{"history_id": "h2", "reason": "already_converted"}],
        }
        user = {"id": "u1", "tenant_id": "t1", "entry": "erp"}
        with (
            mock.patch.object(history_routes, "get_current_user_from_request", return_value=user),
            mock.patch.object(history_routes, "_check_history_access"),
            mock.patch.object(history_routes, "_tid", return_value="t1"),
            mock.patch.object(history_routes.db, "get_cursor_rls", return_value=_Ctx(cur)),
            mock.patch.object(history_routes.wc, "assert_workspace_in_tenant"),
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
        updates = [(sql, params) for sql, params in cur.sql if "SET staged = FALSE" in sql]
        self.assertEqual(len(updates), 1)
        self.assertEqual(set(updates[0][1][0]), {"h1", "h2"})


if __name__ == "__main__":
    unittest.main()
