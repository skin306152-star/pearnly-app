from __future__ import annotations

import asyncio
import inspect
import unittest
from types import SimpleNamespace
from unittest import mock

import jwt
from fastapi import HTTPException

from routes import cowork_line_intake_routes as routes
from services.cowork_line import intake

IDENTITY = {
    "tenant_id": "tenant-1",
    "user_id": "user-1",
    "membership_id": "member-1",
    "line_user_id": "line-1",
}
MRERP_ACCOUNT = {
    "selected_account_key": "6:1",
    "account_choices": [
        {
            "key": "6:1",
            "label": "TEST2019",
            "comidyear": "6",
            "seldb": "1",
            "writable": True,
        }
    ],
}
PAYLOAD = {
    "history_ids": ["history-1"],
    "nonce": "nonce-1",
    "adapter": "mrerp",
    "endpoint_id": "endpoint-1",
    "workspace_client_id": None,
    "account_set": "6:1",
    "direction": "purchase",
    "payment": "cash",
}


class IntakeServiceTest(unittest.TestCase):
    def test_opening_a_new_draft_forces_latest_erp_projection(self):
        targets = SimpleNamespace(list_targets=mock.Mock(return_value=[]))
        with (
            mock.patch.object(intake, "require_draft", return_value=({}, dict(PAYLOAD))),
            mock.patch.object(intake, "_assert_owned_staged"),
            mock.patch.object(intake, "_records", return_value=[]),
            mock.patch.object(intake, "_targets_service", return_value=targets),
        ):
            intake.get_draft(IDENTITY, "history-1")
        targets.list_targets.assert_called_once_with(IDENTITY, refresh=True)

    def test_save_revalidates_target_and_auto_creates_workspace(self):
        initial = {
            "endpoint_id": "endpoint-1",
            "workspace_client_id": None,
            "adapter": "mrerp",
            "label": "MR.ERP",
            "mode_options": ["cash", "credit"],
            **MRERP_ACCOUNT,
        }
        ready = {**initial, "workspace_client_id": 17}
        targets = SimpleNamespace(
            require_target=mock.Mock(return_value=initial),
            resolve_history_workspace=mock.Mock(return_value=ready),
            list_targets=mock.Mock(return_value=[ready]),
            preflight_document=mock.Mock(return_value={"ok": True, "missing": []}),
        )
        records = [{"id": "history-1", "pages": [{"fields": {"total_amount": "120"}}]}]
        selection = {
            "endpoint_id": "endpoint-1",
            "workspace_client_id": None,
            "direction": "purchase",
            "payment": "cash",
            "account_set": "6:1",
        }
        posting_result = SimpleNamespace(ok=True)

        with (
            mock.patch.object(intake, "require_draft", return_value=({}, dict(PAYLOAD))),
            mock.patch.object(intake, "_assert_owned_staged"),
            mock.patch.object(intake, "_targets_service", return_value=targets),
            mock.patch.object(intake, "update_ocr_history_pages", return_value=True) as update,
            mock.patch.object(intake, "_update_scope") as update_scope,
            mock.patch.object(intake, "_records", return_value=records),
            mock.patch.object(
                intake.selected_account_refresh,
                "ensure_for_editor",
                return_value={
                    "request_id": "refresh-6-1",
                    "status": "succeeded",
                    "account_set_key": "6:1",
                },
            ) as refresh,
            mock.patch.object(intake.session_store, "set_session") as set_session,
            mock.patch(
                "services.ocr_history.posting_manual.update_history_posting_manual",
                return_value=posting_result,
            ),
        ):
            result = intake.save_draft(IDENTITY, "history-1", records, selection)

        saved_pages = update.call_args.args[2]
        self.assertEqual(saved_pages[0]["fields"]["direction"], "purchase")
        targets.require_target.assert_called_once_with(
            IDENTITY, "endpoint-1", workspace_client_id=None
        )
        targets.resolve_history_workspace.assert_called_once_with(
            IDENTITY,
            initial,
            ["history-1"],
            "purchase",
            provisional_history_assignment=True,
        )
        self.assertEqual(update_scope.call_args.args[2]["workspace_client_id"], 17)
        saved_payload = set_session.call_args.kwargs["payload"]
        self.assertEqual(saved_payload["workspace_client_id"], 17)
        self.assertEqual(saved_payload["posting_mode"], "cash")
        self.assertEqual(saved_payload["master_refresh_request_id"], "refresh-6-1")
        refresh.assert_called_once_with(
            IDENTITY,
            mock.ANY,
            "6:1",
            previous_request_id=None,
        )
        self.assertEqual(result["selection"]["payment"], "cash")

    def test_line_posting_mode_is_projected_into_editor_selection(self):
        payload = {**PAYLOAD, "payment": None, "posting_mode": "credit"}
        self.assertEqual(intake._selection(payload)["payment"], "credit")

    def test_target_errors_are_scoped_and_do_not_leak_configuration(self):
        class TargetError(Exception):
            code = "target_not_ready"

        TargetError.__name__ = "CoworkLineErpTargetError"
        targets = SimpleNamespace(require_target=mock.Mock(side_effect=TargetError()))
        with mock.patch.object(intake, "_targets_service", return_value=targets):
            with self.assertRaises(intake.CoworkLineIntakeError) as caught:
                intake._validated_selection(IDENTITY, PAYLOAD)
        self.assertEqual(caught.exception.code, "target_not_ready")
        self.assertEqual(caught.exception.status_code, 409)

    def test_cowork_intake_never_converts_to_formal_documents(self):
        source = inspect.getsource(intake)
        self.assertNotIn("intake_bridge", source)
        self.assertNotIn("purchase_docs", source)
        self.assertNotIn("sales_documents", source)


class IntakeConfirmTest(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def _ready_records():
        return [
            {
                "id": "history-1",
                "pages": [
                    {
                        "fields": {
                            "seller_name": "Supplier",
                            "date": "2026-09-01",
                            "total_amount": "120",
                            "items": [{"name": "Service", "qty": "1"}],
                        }
                    }
                ],
            }
        ]

    async def test_confirm_clears_session_after_atomic_log_and_recognition_commit(self):
        target = {
            "endpoint_id": "endpoint-1",
            "workspace_client_id": 17,
            "adapter": "mrerp",
            "label": "MR.ERP",
            "mode_options": ["cash", "credit"],
            **MRERP_ACCOUNT,
        }
        payload = {**PAYLOAD, "workspace_client_id": 17}

        async def dispatch(*args):
            return {
                "status": "pending",
                "push_ok": True,
                "committed": 1,
                "results": [{"history_id": "history-1", "log_id": "log-1"}],
            }

        targets = SimpleNamespace(require_target=mock.Mock(return_value=target))
        targets.preflight_document = mock.Mock(return_value={"ok": True, "missing": []})
        with (
            mock.patch.object(intake, "require_draft", return_value=({}, payload)),
            mock.patch.object(intake, "_assert_owned_staged") as staged_precheck,
            mock.patch.object(intake, "_targets_service", return_value=targets),
            mock.patch.object(intake, "_records", return_value=self._ready_records()),
            mock.patch.object(intake, "_dispatch_confirmed", side_effect=dispatch),
            mock.patch.object(intake.session_store, "clear_session") as clear,
        ):
            result = await intake.confirm_and_push(IDENTITY, payload)

        self.assertTrue(result["saved"])
        self.assertTrue(result["push_ok"])
        self.assertEqual(result["committed"], 1)
        staged_precheck.assert_not_called()
        clear.assert_called_once()

    async def test_confirm_keeps_retryable_session_when_no_history_was_committed(self):
        target = {
            "endpoint_id": "endpoint-1",
            "workspace_client_id": 17,
            "adapter": "mrerp",
            "label": "MR.ERP",
            "mode_options": ["cash", "credit"],
            **MRERP_ACCOUNT,
        }
        payload = {**PAYLOAD, "workspace_client_id": 17}
        targets = SimpleNamespace(
            require_target=mock.Mock(return_value=target),
            preflight_document=mock.Mock(return_value={"ok": True, "missing": []}),
        )
        with (
            mock.patch.object(intake, "require_draft", return_value=({}, payload)),
            mock.patch.object(intake, "_assert_owned_staged"),
            mock.patch.object(intake, "_targets_service", return_value=targets),
            mock.patch.object(intake, "_records", return_value=self._ready_records()),
            mock.patch.object(
                intake,
                "_dispatch_confirmed",
                return_value={"status": "failed", "push_ok": False, "committed": 0},
            ),
            mock.patch.object(intake.session_store, "clear_session") as clear,
        ):
            result = await intake.confirm_and_push(IDENTITY, payload)

        self.assertFalse(result["saved"])
        self.assertFalse(result["push_ok"])
        clear.assert_not_called()

    async def test_confirm_rejects_payload_with_different_history_scope(self):
        with mock.patch.object(intake, "require_draft", return_value=({}, dict(PAYLOAD))):
            with self.assertRaises(intake.CoworkLineIntakeError) as caught:
                await intake.confirm_and_push(IDENTITY, {**PAYLOAD, "history_ids": ["other"]})
        self.assertEqual(caught.exception.code, "records_incomplete")

    async def test_confirm_blocks_batch_when_any_document_has_unresolved_fields(self):
        target = {
            "endpoint_id": "endpoint-1",
            "workspace_client_id": 17,
            "adapter": "mrerp",
            "label": "MR.ERP",
            "mode_options": ["cash", "credit"],
            **MRERP_ACCOUNT,
        }
        payload = {**PAYLOAD, "workspace_client_id": 17}
        targets = SimpleNamespace(require_target=mock.Mock(return_value=target))
        with (
            mock.patch.object(intake, "require_draft", return_value=({}, payload)),
            mock.patch.object(intake, "_targets_service", return_value=targets),
            mock.patch.object(
                intake,
                "_records",
                return_value=[{"id": "history-1", "pages": [{"fields": {"items": []}}]}],
            ),
            mock.patch.object(intake, "_dispatch_confirmed") as dispatch,
        ):
            with self.assertRaises(intake.CoworkLineIntakeError) as caught:
                await intake.confirm_and_push(IDENTITY, payload)

        self.assertEqual(caught.exception.code, "document_not_ready")
        self.assertEqual(caught.exception.status_code, 422)
        dispatch.assert_not_called()


class IntakeRouteTest(unittest.TestCase):
    def test_liff_auth_uses_active_identity_and_session_nonce(self):
        session = {"state": "draft", "payload": dict(PAYLOAD)}
        with (
            mock.patch(
                "routes.cowork_line_intake_routes.verify_id_token", return_value={"sub": "line-1"}
            ),
            mock.patch.object(
                routes.identity_store, "resolve_active_identity", return_value=IDENTITY
            ),
            mock.patch.object(routes.session_store, "get_session", return_value=session),
            mock.patch.object(routes, "_secret", return_value="test-secret-for-cowork-line-intake"),
        ):
            response = asyncio.run(
                routes.cowork_intake_liff_auth(
                    routes.LiffAuthIn(id_token="line-token", draft_id="history-1")
                )
            )
        claims = jwt.decode(
            response["data"]["token"],
            "test-secret-for-cowork-line-intake",
            algorithms=[routes.JWT_ALGORITHM],
            audience="cowork_line_intake",
        )
        self.assertEqual(claims["scope"], "cowork_line_intake")
        self.assertEqual(claims["session_nonce"], "nonce-1")
        self.assertEqual(claims["draft_id"], "history-1")

    def test_auth_rejects_non_review_session(self):
        with mock.patch.object(
            routes.session_store,
            "get_session",
            return_value={"state": "receiving", "payload": dict(PAYLOAD)},
        ):
            with self.assertRaises(HTTPException) as caught:
                routes._session_for(IDENTITY, "history-1")
        self.assertEqual(caught.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
