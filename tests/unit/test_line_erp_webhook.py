import unittest
from unittest import mock

from services.line_erp import webhook


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
        with (
            mock.patch.object(
                webhook.store,
                "get_session",
                return_value={"state": "receiving", "payload": {"mode": "purchase"}},
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
        with (
            mock.patch.object(
                webhook.store,
                "get_session",
                return_value={"state": "receiving", "payload": {"mode": "sales"}},
            ),
            mock.patch.object(webhook.line_client, "download_message_content", return_value=b"x"),
            mock.patch.object(
                webhook.db,
                "find_user_by_id",
                return_value={"id": "u1", "tenant_id": "t1", "is_active": False},
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
        with (
            mock.patch.object(
                webhook.store,
                "get_session",
                return_value={
                    "state": "draft",
                    "payload": {"history_ids": ["h1", "h2"]},
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
                webhook,
                "draft_records",
                return_value=[
                    {
                        "pages": [
                            {
                                "fields": {
                                    "direction": "purchase",
                                    "date": "2026-08-28",
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
                                    "items": [{"name": "B", "qty": "1", "posting_kind": "service"}],
                                }
                            }
                        ]
                    },
                ],
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


if __name__ == "__main__":
    unittest.main()
