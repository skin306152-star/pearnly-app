import unittest
from unittest import mock

from services.line_erp import webhook


def _express_selection(mode="purchase"):
    return {
        "mode": mode,
        "direction": mode,
        "endpoint_id": "ep-1",
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
    async def test_menu_refreshes_all_erp_targets_before_rendering(self):
        status = {"ready": True, "any_ready": True, "targets": [], "text": "ready"}
        with mock.patch.object(
            webhook, "_target_status", new=mock.AsyncMock(return_value=status)
        ) as inspect:
            card = await webhook._menu_card(
                {"tenant_id": "t1", "user_id": "u1"}, ("purchase", "sales")
            )

        inspect.assert_awaited_once_with({"tenant_id": "t1", "user_id": "u1"}, refresh=True)
        self.assertEqual(card["type"], "flex")

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

    async def test_document_backfills_preview_before_opening_draft(self):
        binding = {"tenant_id": "t1", "user_id": "u1", "workspace_client_id": 7}
        selection = _express_selection()
        with (
            mock.patch.object(
                webhook.store,
                "get_session",
                return_value={"state": "receiving", "payload": selection},
            ),
            mock.patch.object(webhook.store, "set_session") as set_session,
            mock.patch.object(webhook.line_client, "download_message_content", return_value=b"pdf"),
            mock.patch.object(webhook.line_client, "reply_messages"),
            mock.patch.object(
                webhook.db,
                "find_user_by_id",
                return_value={"id": "u1", "tenant_id": "t1", "plan": "free"},
            ),
            mock.patch.object(webhook, "erp_line_enabled_for", return_value=True),
            mock.patch.object(webhook, "_allowed_modes", return_value=("purchase",)),
            mock.patch.object(
                webhook.target_selection,
                "normalize",
                return_value=(_ready(selection), selection),
            ),
            mock.patch.object(
                webhook,
                "run_recognition_core",
                return_value={
                    "history_ids": ["h1"],
                    "raw_pages": [{"page_number": 1, "fields": {}}],
                },
            ),
            mock.patch.object(
                webhook.intake,
                "generate_and_save_pdf",
                return_value={"saved": False, "updated": 0},
            ) as backfill,
        ):
            await webhook._handle_document(
                {"id": "m1", "type": "file", "fileName": "invoice.pdf"},
                binding,
                "line-u1",
                "reply",
            )
        backfill.assert_called_once()
        payload = set_session.call_args.args[3]
        self.assertEqual(set_session.call_args.args[:3], ("t1", "line-u1", "draft"))
        self.assertEqual(payload["history_ids"], ["h1"])
        self.assertTrue(payload["nonce"])

    async def test_inactive_bound_user_never_reaches_ocr(self):
        binding = {"tenant_id": "t1", "user_id": "u1", "workspace_client_id": 7}
        selection = _express_selection("sales")
        with (
            mock.patch.object(
                webhook.store,
                "get_session",
                return_value={"state": "receiving", "payload": selection},
            ),
            mock.patch.object(
                webhook.target_selection,
                "normalize",
                side_effect=webhook.target_selection.SelectionError("erp_user_inactive"),
            ),
            mock.patch.object(webhook, "erp_line_enabled_for", return_value=True),
            mock.patch.object(webhook, "_allowed_modes", return_value=("sales",)),
            mock.patch.object(webhook, "run_recognition_core") as recognize,
            mock.patch.object(webhook.store, "clear_session") as clear_session,
        ):
            await webhook._handle_document(
                {"id": "m1", "type": "image"}, binding, "line-u1", "reply"
            )
        recognize.assert_not_called()
        clear_session.assert_called_once_with("t1", "line-u1")

    async def test_incomplete_confirm_keeps_session_and_rolls_back_batch(self):
        binding = {"tenant_id": "t1", "user_id": "u1"}
        cursor = _Cursor()
        selection = _express_selection()
        with (
            mock.patch.object(
                webhook.store,
                "get_session",
                return_value={
                    "state": "draft",
                    "payload": {**selection, "history_ids": ["h1", "h2"]},
                },
            ),
            mock.patch.object(webhook.store, "clear_session") as clear_session,
            mock.patch.object(
                webhook.db,
                "find_user_by_id",
                return_value={"id": "u1", "tenant_id": "t1", "is_active": True},
            ),
            mock.patch.object(webhook, "erp_line_enabled_for", return_value=True),
            mock.patch.object(webhook.team_access, "mode_allowed", return_value=True),
            mock.patch.object(
                webhook.target_selection,
                "normalize",
                return_value=(_ready(selection), selection),
            ),
            mock.patch.object(
                webhook,
                "draft_records",
                return_value=[
                    {
                        "pages": [
                            {
                                "fields": {
                                    "direction": "purchase",
                                    "date": "2026-08-28",
                                    "seller_name": "Supplier A",
                                    "total_amount": "100",
                                    "items": [{"name": "A", "qty": "1", "posting_kind": "stock"}],
                                }
                            }
                        ]
                    },
                    {
                        "pages": [
                            {
                                "fields": {
                                    "direction": "purchase",
                                    "date": "2026-08-28",
                                    "seller_name": "Supplier B",
                                    "total_amount": "200",
                                    "items": [{"name": "B", "qty": "1", "posting_kind": "service"}],
                                }
                            }
                        ]
                    },
                ],
            ),
            mock.patch.object(
                webhook.draft_actions.line_document_subject,
                "matches",
                return_value=(True, None),
            ),
            mock.patch.object(
                webhook.convert_svc,
                "convert_histories",
                return_value={"converted": [{"history_id": "h1"}], "skipped": []},
            ),
            mock.patch.object(webhook.db, "get_cursor_rls", return_value=_Context(cursor)),
        ):
            result = await webhook.act_draft(binding, "line-u1", None, "h1", "confirm")
        self.assertEqual(result["detail"], "line_erp.confirm_incomplete")
        clear_session.assert_not_called()
        self.assertFalse(
            any("UPDATE ocr_history SET staged = FALSE" in sql for sql, _ in cursor.sql)
        )

    async def test_complete_confirm_pushes_each_history_through_assigned_erp(self):
        binding = {
            "tenant_id": "t1",
            "user_id": "u1",
            "workspace_client_id": 7,
        }
        cursor = _Cursor(count=2)
        selection = _express_selection()
        records = [
            {
                "pages": [
                    {
                        "fields": {
                            "direction": "purchase",
                            "date": "2026-09-01",
                            "seller_name": "Supplier " + name,
                            "total_amount": "100",
                            "items": [{"name": name, "qty": "1", "posting_kind": "stock"}],
                        }
                    }
                ]
            }
            for name in ("A", "B")
        ]
        pushed = mock.AsyncMock(
            return_value={
                "ok": True,
                "push_ok": True,
                "push_results": [
                    {"history_id": "h1", "ok": True, "status": "success", "log_id": "l1"},
                    {"history_id": "h2", "ok": True, "status": "pending", "log_id": "l2"},
                ],
            }
        )
        with (
            mock.patch.object(
                webhook.store,
                "get_session",
                return_value={
                    "state": "draft",
                    "payload": {**selection, "history_ids": ["h1", "h2"]},
                },
            ),
            mock.patch.object(webhook.store, "clear_session") as clear_session,
            mock.patch.object(
                webhook.db,
                "find_user_by_id",
                return_value={"id": "u1", "tenant_id": "t1", "is_active": True},
            ),
            mock.patch.object(webhook, "erp_line_enabled_for", return_value=True),
            mock.patch.object(webhook.team_access, "mode_allowed", return_value=True),
            mock.patch.object(
                webhook.target_selection,
                "normalize",
                return_value=(_ready(selection), selection),
            ),
            mock.patch.object(webhook, "draft_records", return_value=records),
            mock.patch.object(
                webhook.draft_actions.line_document_subject,
                "matches",
                return_value=(True, None),
            ),
            mock.patch.object(
                webhook.convert_svc,
                "convert_histories",
                return_value={
                    "converted": [{"history_id": "h1"}, {"history_id": "h2"}],
                    "skipped": [],
                },
            ),
            mock.patch.object(webhook.db, "get_cursor_rls", return_value=_Context(cursor)),
            mock.patch.object(webhook.line_push, "dispatch_confirmed", pushed),
        ):
            result = await webhook.act_draft(binding, "line-u1", None, "h1", "confirm")

        self.assertTrue(result["ok"])
        self.assertTrue(result["push_ok"])
        self.assertEqual([row["status"] for row in result["push_results"]], ["success", "pending"])
        pushed.assert_awaited_once_with(
            user={"id": "u1", "tenant_id": "t1", "is_active": True, "entry": "erp"},
            history_ids=["h1", "h2"],
            endpoint_id="ep-1",
            workspace_client_id=7,
            posting_kind="stock",
            account_config=None,
        )
        clear_session.assert_called_once_with("t1", "line-u1")


if __name__ == "__main__":
    unittest.main()
