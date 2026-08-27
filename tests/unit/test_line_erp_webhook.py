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
            mock.patch.object(webhook, "run_recognition_core") as recognize,
        ):
            await webhook._handle_document(
                {"id": "m1", "type": "image"}, binding, "line-u1", "reply"
            )
        recognize.assert_not_called()

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
