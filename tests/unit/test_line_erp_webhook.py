import unittest
from unittest import mock

from services.line_erp import webhook


def _express_selection(mode="purchase"):
    return {
        "mode": mode,
        "direction": mode,
        "endpoint_id": "ep-1",
        "connection_workspace_client_id": 7,
        "workspace_client_id": 7,
        "adapter": "express",
        "target_label": "Express · Main",
        "posting_kind": "stock",
        "payment": None,
        "posting_mode": "stock",
    }


def _ready(selection):
    return {
        "ready": True,
        "endpoint_id": selection["endpoint_id"],
        "workspace_client_id": selection["workspace_client_id"],
        "user": {"id": "u1", "tenant_id": "t1", "plan": "free"},
        "target": {
            "endpoint_id": selection["endpoint_id"],
            "workspace_client_id": selection["workspace_client_id"],
            "adapter": selection["adapter"],
        },
    }


class _Cursor:
    def __init__(self, count=1):
        self.count = count
        self.sql = []

    def execute(self, sql, params=None):
        self.sql.append((sql, params))

    def fetchone(self):
        return {"n": self.count}


class _Context:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, *_args):
        return False


class ErpLineWebhookTests(unittest.IsolatedAsyncioTestCase):
    def test_missing_document_workspace_profile_is_a_saved_non_push_result(self):
        result = {
            "status": "manual",
            "push_results": [
                {
                    "status": "manual",
                    "error_msg": "erp.workspace_endpoint_required",
                }
            ],
        }
        self.assertTrue(webhook.draft_actions._saved_without_profile(result))
        self.assertFalse(
            webhook.draft_actions._saved_without_profile(
                {"status": "manual", "push_results": [{"status": "manual"}]}
            )
        )

    async def test_menu_does_not_probe_targets_before_rendering(self):
        with mock.patch("services.line_erp.target_preflight.inspect_targets") as inspect:
            card = await webhook._menu_card(
                {"tenant_id": "t1", "user_id": "u1"}, ("purchase", "sales")
            )

        inspect.assert_not_called()
        self.assertEqual(card["type"], "flex")

    async def test_rich_menu_postback_respects_assigned_modes(self):
        binding = {"tenant_id": "t1", "user_id": "u1"}
        event = {"postback": {"data": "a=mode%3Asales"}}
        with (
            mock.patch.object(webhook, "_allowed_modes", return_value=("purchase",)),
            mock.patch.object(webhook.internal_flow, "begin_mode") as begin_mode,
            mock.patch.object(webhook.line_client, "reply_text") as reply_text,
        ):
            await webhook._handle_postback(event, binding, "line-u1", "reply")
        begin_mode.assert_not_called()
        reply_text.assert_called_once()
        self.assertIn("ไม่มีสิทธิ์", reply_text.call_args.args[1])

    async def test_rich_menu_postback_starts_an_assigned_mode(self):
        binding = {"tenant_id": "t1", "user_id": "u1"}
        event = {"postback": {"data": "a=mode%3Apurchase"}}
        with (
            mock.patch.object(webhook, "_allowed_modes", return_value=("purchase",)),
            mock.patch.object(webhook.internal_flow, "begin_mode") as begin_mode,
        ):
            await webhook._handle_postback(event, binding, "line-u1", "reply")
        begin_mode.assert_awaited_once_with(binding, "line-u1", "reply", "purchase")

    async def test_old_external_postbacks_do_not_open_a_picker(self):
        from services.line_erp import target_flow

        with mock.patch.object(target_flow, "show_account_picker") as show:
            await webhook._handle_postback(
                {"postback": {"data": "a=erp-type&erp=express"}},
                {"tenant_id": "t1", "user_id": "u1"},
                "line-u1",
                "reply",
            )
        show.assert_not_called()

    async def test_internal_manual_postback_uses_shared_flow(self):
        binding = {"tenant_id": "t1", "user_id": "u1"}
        with mock.patch.object(webhook.internal_flow, "manual") as manual:
            await webhook._handle_postback(
                {"postback": {"data": "a=internal-manual"}}, binding, "line-u1", "reply"
            )
        manual.assert_awaited_once_with(binding, "line-u1", "reply")

    async def test_media_event_queues_ocr_instead_of_waiting_for_reply(self):
        binding = {"tenant_id": "t1", "user_id": "u1"}
        with (
            mock.patch.object(webhook.store, "get_binding", return_value=binding),
            mock.patch.object(webhook, "erp_line_enabled_for", return_value=True),
            mock.patch.object(webhook, "_allowed_modes", return_value=("purchase", "sales")),
            mock.patch.object(webhook, "_queue_document") as queue,
        ):
            await webhook.handle_event(
                {
                    "type": "message",
                    "source": {"userId": "line-u1"},
                    "replyToken": "reply",
                    "message": {"type": "image", "id": "m1"},
                }
            )
        queue.assert_called_once_with({"type": "image", "id": "m1"}, binding, "line-u1", "reply")

    async def test_queue_atomically_claims_one_billable_ocr_run(self):
        binding = {"tenant_id": "t1", "user_id": "u1"}

        def close_task(coro):
            coro.close()

        with (
            mock.patch.object(
                webhook.store, "claim_processing", return_value={"mode": "purchase"}
            ) as claim,
            mock.patch.object(webhook, "_spawn", side_effect=close_task) as spawn,
        ):
            await webhook._queue_document(
                {"type": "image", "id": "m1"}, binding, "line-u1", "reply"
            )
        claim.assert_called_once_with("t1", "line-u1", "m1")
        spawn.assert_called_once()

    async def test_queue_rejects_duplicate_while_ocr_is_processing(self):
        binding = {"tenant_id": "t1", "user_id": "u1"}
        with (
            mock.patch.object(webhook.store, "claim_processing", return_value=None),
            mock.patch.object(
                webhook.store,
                "get_session",
                return_value={"state": "ocr_processing", "payload": {"mode": "purchase"}},
            ),
            mock.patch.object(webhook, "_notify") as notify,
            mock.patch.object(webhook, "_spawn") as spawn,
        ):
            await webhook._queue_document(
                {"type": "image", "id": "m2"}, binding, "line-u1", "reply"
            )
        spawn.assert_not_called()
        notify.assert_called_once()
        self.assertIn("กำลังอ่านเอกสาร", notify.call_args.args[2])

    async def test_processing_session_does_not_switch_document_mode(self):
        binding = {"tenant_id": "t1", "user_id": "u1"}
        with (
            mock.patch.object(
                webhook.store,
                "get_session",
                return_value={"state": "ocr_processing", "payload": {"mode": "purchase"}},
            ),
            mock.patch.object(webhook.store, "set_session") as set_session,
            mock.patch.object(webhook.line_client, "reply_text") as reply_text,
        ):
            await webhook._handle_text({"text": "2"}, binding, "line-u1", "reply")
        set_session.assert_not_called()
        reply_text.assert_called_once()
        self.assertIn("กำลังอ่านเอกสาร", reply_text.call_args.args[1])

    async def test_document_saves_preview_and_keeps_internal_workspace(self):
        selection = {
            "mode": "purchase",
            "direction": "purchase",
            "workspace_client_id": 7,
            "target_label": "Local Company",
        }
        binding = {"tenant_id": "t1", "user_id": "u1"}
        with (
            mock.patch.object(
                webhook.store,
                "get_session",
                return_value={"state": "receiving", "payload": selection},
            ),
            mock.patch.object(webhook.store, "set_session") as session,
            mock.patch.object(
                webhook.internal_flow,
                "selection",
                return_value=({"id": "u1", "tenant_id": "t1"}, selection),
            ),
            mock.patch.object(webhook.line_client, "download_message_content", return_value=b"pdf"),
            mock.patch.object(webhook.line_client, "reply_messages"),
            mock.patch.object(webhook.line_client, "start_loading"),
            mock.patch.object(webhook, "erp_line_enabled_for", return_value=True),
            mock.patch.object(webhook, "_allowed_modes", return_value=("purchase",)),
            mock.patch.object(
                webhook,
                "run_recognition_core",
                return_value={"history_ids": ["h1"], "raw_pages": []},
            ) as recognize,
            mock.patch.object(webhook.intake, "generate_and_save_pdf") as pdf,
            mock.patch.object(
                webhook.internal_flow, "recognized_selection", return_value=selection
            ),
        ):
            await webhook._handle_document(
                {"id": "m1", "fileName": "invoice.pdf"}, binding, "line-u1", "reply"
            )
        pdf.assert_called_once()
        self.assertEqual(recognize.call_args.kwargs["source"], "line_erp")
        self.assertEqual(recognize.call_args.kwargs["ws_client_id"], 7)
        self.assertTrue(recognize.call_args.kwargs["staged"])
        payload = session.call_args.args[3]
        self.assertEqual(payload["workspace_client_id"], 7)
        self.assertEqual(payload["history_ids"], ["h1"])
        self.assertTrue(payload["nonce"])
        self.assertNotIn("endpoint_id", payload)

    async def test_missing_internal_workspace_stops_before_download(self):
        from fastapi import HTTPException

        with (
            mock.patch.object(
                webhook.store,
                "get_session",
                return_value={"state": "receiving", "payload": {"mode": "purchase"}},
            ),
            mock.patch.object(
                webhook.internal_flow,
                "selection",
                side_effect=HTTPException(404, "workspace.not_found"),
            ),
            mock.patch.object(webhook, "_allowed_modes", return_value=("purchase",)),
            mock.patch.object(webhook, "_restore_receiving") as restore,
            mock.patch.object(webhook, "_notify"),
            mock.patch.object(webhook.line_client, "download_message_content") as download,
        ):
            await webhook._handle_document(
                {"id": "m1"}, {"tenant_id": "t1", "user_id": "u1"}, "line-u1", "reply"
            )
        download.assert_not_called()
        restore.assert_called_once()

    async def test_inactive_bound_user_never_reaches_ocr(self):
        selection = {"mode": "sales", "workspace_client_id": 7}
        with (
            mock.patch.object(
                webhook.store,
                "get_session",
                return_value={"state": "receiving", "payload": selection},
            ),
            mock.patch.object(
                webhook.internal_flow,
                "selection",
                return_value=({"id": "u1", "tenant_id": "t1", "is_active": False}, selection),
            ),
            mock.patch.object(webhook.line_client, "download_message_content", return_value=b"pdf"),
            mock.patch.object(webhook, "_allowed_modes", return_value=("sales",)),
            mock.patch.object(webhook, "_notify"),
            mock.patch.object(webhook, "run_recognition_core") as recognize,
            mock.patch.object(webhook.store, "clear_session") as clear,
        ):
            await webhook._handle_document(
                {"id": "m1"}, {"tenant_id": "t1", "user_id": "u1"}, "line-u1", "reply"
            )
        recognize.assert_not_called()
        clear.assert_called_once_with("t1", "line-u1")

    async def test_pending_draft_menu_and_mode_restore_actions_without_clearing(self):
        binding = {"tenant_id": "t1", "user_id": "u1"}
        session = {"state": "draft", "payload": {"mode": "purchase", "history_ids": ["h1"]}}
        with (
            mock.patch.object(webhook.store, "get_session", return_value=session),
            mock.patch.object(
                webhook.internal_flow, "remind_draft", new_callable=mock.AsyncMock
            ) as remind,
            mock.patch.object(webhook.store, "clear_session") as clear,
        ):
            await webhook._handle_text({"text": "เมนู"}, binding, "line-u1", "reply")
            await webhook.internal_flow.begin_mode(binding, "line-u1", "reply", "sales")
            await webhook.internal_flow.manual(binding, "line-u1", "reply")
        self.assertEqual(remind.await_count, 3)
        clear.assert_not_called()

    async def test_failed_confirm_keeps_session(self):
        await self._assert_confirm({"ok": False, "status": 409, "detail": "erp.confirm_failed"})

    async def test_finished_card_replies_without_confirming_again(self):
        with (
            mock.patch.object(webhook.store, "get_session", return_value=None),
            mock.patch.object(webhook.line_client, "reply_text") as reply,
            mock.patch.object(webhook, "_confirm") as confirm,
        ):
            result = await webhook.act_draft(
                {"tenant_id": "t1", "user_id": "u1"}, "line-u1", "reply", "h1", "confirm"
            )
        self.assertFalse(result["ok"])
        reply.assert_called_once()
        confirm.assert_not_called()

    async def test_complete_confirm_saves_without_push(self):
        await self._assert_confirm(
            {"ok": True, "status": "saved", "converted": [{"history_id": "h1"}]}
        )

    async def _assert_confirm(self, saved):
        with (
            mock.patch.object(
                webhook.store,
                "get_session",
                return_value={
                    "state": "draft",
                    "payload": {"mode": "purchase", "history_ids": ["h1"]},
                },
            ),
            mock.patch.object(webhook.store, "clear_session") as clear,
            mock.patch.object(
                webhook.db,
                "find_user_by_id",
                return_value={"id": "u1", "tenant_id": "t1", "is_active": True},
            ),
            mock.patch.object(webhook, "erp_line_enabled_for", return_value=True),
            mock.patch.object(webhook.team_access, "mode_allowed", return_value=True),
            mock.patch.object(webhook, "_confirm", return_value=saved),
            mock.patch.object(
                webhook.draft_actions.draft_view,
                "records",
                return_value=[{"id": "h1", "pages": [{"fields": {"total_amount": "120"}}]}],
            ),
            mock.patch.object(webhook.line_client, "push_messages") as receipt,
            mock.patch.object(webhook.line_push, "dispatch_confirmed") as push,
        ):
            result = await webhook.act_draft(
                {"tenant_id": "t1", "user_id": "u1"}, "line-u1", None, "h1", "confirm"
            )
        self.assertEqual(result["ok"], saved["ok"])
        push.assert_not_called()
        if saved["ok"]:
            self.assertEqual(result["status"], "saved")
            clear.assert_called_once()
            receipt.assert_called_once()
            self.assertIn("120", str(receipt.call_args))
        else:
            clear.assert_not_called()


if __name__ == "__main__":
    unittest.main()
