"""Manual URI entry and OCR subject handoff regression cases."""

import unittest
from unittest.mock import patch

from fastapi import HTTPException

from services.line_erp import internal_flow as flow


class InternalEntryTests(unittest.IsolatedAsyncioTestCase):
    async def test_method_choice_reserves_uri_without_creating_empty_record(self):
        payload = {"mode": "purchase", "workspace_client_id": 7, "target_label": "Company"}
        with (
            patch.object(flow, "selection", return_value=({}, payload)),
            patch.object(flow.store, "set_session") as session,
            patch.object(flow, "notify") as notify,
            patch.object(flow.internal_records, "save_draft") as save,
        ):
            await flow.offer_methods({"tenant_id": "t"}, "line", "reply", payload)
        pending_id = session.call_args.args[3]["manual_history_id"]
        action = notify.call_args.args[2][0]["quickReply"]["items"][0]["action"]
        self.assertEqual(action["type"], "uri")
        self.assertIn(pending_id, action["uri"])
        save.assert_not_called()

    async def test_authenticated_entry_materializes_reserved_draft_without_preview(self):
        binding = {"tenant_id": "t", "user_id": "u"}
        payload = {"manual_history_id": "h", "workspace_client_id": 7, "direction": "sales"}
        with (
            patch.object(
                flow.store, "get_session", return_value={"state": "receiving", "payload": payload}
            ),
            patch.object(flow, "selection", return_value=({}, payload)),
            patch.object(flow.internal_records, "save_draft") as save,
            patch.object(flow.store, "set_session") as session,
            patch.object(flow, "notify") as notify,
        ):
            await flow.create_manual(binding, "line", "h")
        self.assertEqual(save.call_args.kwargs["history_id"], "h")
        self.assertEqual(session.call_args.args[3]["history_ids"], ["h"])
        notify.assert_not_called()

    async def test_stale_manual_link_cannot_replace_active_draft(self):
        with (
            patch.object(
                flow.store,
                "get_session",
                return_value={"state": "draft", "payload": {"history_ids": ["other"]}},
            ),
            patch.object(flow.internal_records, "save_draft") as save,
        ):
            with self.assertRaises(HTTPException):
                await flow.create_manual({"tenant_id": "t"}, "line", "old")
        save.assert_not_called()

    def test_recognized_subject_is_authorized_and_replaces_old_subject(self):
        binding = {"tenant_id": "t", "user_id": "u"}
        with (
            patch(
                "services.ocr_history.queries.get_ocr_history_detail",
                return_value={"workspace_client_id": 252},
            ),
            patch.object(
                flow, "selection", return_value=({}, {"workspace_client_id": 252})
            ) as select,
        ):
            result = flow.recognized_selection(
                binding, {"workspace_client_id": 900001, "mode": "purchase"}, ["h"]
            )
        self.assertEqual(result["workspace_client_id"], 252)
        self.assertEqual(select.call_args.args[1]["workspace_client_id"], 252)

    def test_mixed_subjects_never_silently_save_under_first_subject(self):
        with patch(
            "services.ocr_history.queries.get_ocr_history_detail",
            side_effect=[{"workspace_client_id": 1}, {"workspace_client_id": 2}],
        ):
            with self.assertRaises(HTTPException) as caught:
                flow.recognized_selection({"tenant_id": "t", "user_id": "u"}, {}, ["a", "b"])
        self.assertEqual(caught.exception.detail, "line_erp.multiple_workspaces")
