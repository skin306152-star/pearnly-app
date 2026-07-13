# -*- coding: utf-8 -*-
"""LINE 收料暂存编排(services/line_binding/line_intake_staging)· LN-1 契约。

闸关/未绑定/登录用户/多主体歧义/故障全部 False 回落原路(webhook 现状零变化);
闸开且命中绑定才下载落盘 + 插池 + 四语回执。重投幂等不双记不双回执;下载失败
诚实不回「已收到」。
"""

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.line_binding import line_intake_staging as m


def _dm_event(mid="mid-1", uid="U-1"):
    return {
        "replyToken": "rt-1",
        "source": {"type": "user", "userId": uid},
        "message": {"type": "image", "id": mid, "quoteToken": "qt-1"},
    }


def _group_event(mid="mid-2", gid="G-1", uid="U-9"):
    return {
        "replyToken": "rt-2",
        "source": {"type": "group", "groupId": gid, "userId": uid},
        "message": {"type": "image", "id": mid},
    }


_CONTACT = {"tenant_id": "t-1", "workspace_client_id": 84, "preferred_lang": "th"}
_GROUP = {"line_group_id": "G-1", "tenant_id": "t-1", "workspace_client_id": 84}


class TryStageMediaTests(unittest.IsolatedAsyncioTestCase):
    async def test_gate_closed_returns_false_without_download(self):
        with (
            patch("core.db.get_user_by_line_user_id", return_value=None),
            patch(
                "services.line_binding.line_client_contact.list_contacts_by_line_user",
                return_value=[_CONTACT],
            ),
            patch(
                "core.feature_flags.pearnly_ai_line_intake_enabled_for", return_value=False
            ) as gate,
            patch("services.line_binding.line_client.download_message_content") as dl,
            patch("services.line_binding.line_intake_store.insert_staging") as ins,
        ):
            self.assertFalse(await m.try_stage_media(_dm_event()))
        gate.assert_called_once_with("t-1")
        dl.assert_not_called()
        ins.assert_not_called()

    async def test_bound_pearnly_user_dm_falls_back_to_ocr_path(self):
        """登录用户发图 = 自己账本的 OCR 料,收料分支绝不截胡(现状不变)。"""
        with (
            patch("core.db.get_user_by_line_user_id", return_value={"id": "u-1"}),
            patch(
                "services.line_binding.line_client_contact.list_contacts_by_line_user"
            ) as contacts,
        ):
            self.assertFalse(await m.try_stage_media(_dm_event()))
        contacts.assert_not_called()

    async def test_unbound_group_returns_false(self):
        with patch("services.line_binding.line_client_group.get_group", return_value=None):
            self.assertFalse(await m.try_stage_media(_group_event()))

    async def test_multi_client_contact_ambiguity_returns_false(self):
        with (
            patch("core.db.get_user_by_line_user_id", return_value=None),
            patch(
                "services.line_binding.line_client_contact.list_contacts_by_line_user",
                return_value=[_CONTACT, {**_CONTACT, "workspace_client_id": 91}],
            ),
        ):
            self.assertFalse(await m.try_stage_media(_dm_event()))

    async def test_dm_happy_path_saves_hashes_inserts_and_replies(self):
        content = b"receipt-bytes"
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(m, "_BASE", tmp),
            patch("core.db.get_user_by_line_user_id", return_value=None),
            patch(
                "services.line_binding.line_client_contact.list_contacts_by_line_user",
                return_value=[_CONTACT],
            ),
            patch("core.feature_flags.pearnly_ai_line_intake_enabled_for", return_value=True),
            patch(
                "services.line_binding.line_client.download_message_content",
                return_value=content,
            ),
            patch(
                "services.line_binding.line_intake_store.latest_open_period",
                return_value="2026-06",
            ),
            patch(
                "services.line_binding.line_intake_store.insert_staging", return_value=True
            ) as ins,
            patch(
                "services.line_binding.line_intake_store.client_display_name",
                return_value="Sister Makeup",
            ),
            patch("services.line_binding.line_reply.reply_text_context") as reply,
        ):
            self.assertTrue(await m.try_stage_media(_dm_event()))
            kwargs = ins.call_args.kwargs
            self.assertEqual(ins.call_args.args, ("t-1", 84))
            self.assertEqual(kwargs["line_message_id"], "mid-1")
            self.assertEqual(kwargs["sha256"], hashlib.sha256(content).hexdigest())
            self.assertEqual(kwargs["source"], "dm")
            self.assertEqual(kwargs["sender_line_user_id"], "U-1")
            self.assertEqual(kwargs["suggested_period"], "2026-06")
            saved = Path(kwargs["file_path"])
            self.assertTrue(saved.is_file())
            self.assertEqual(saved.read_bytes(), content)
        reply.assert_called_once()
        self.assertIn("Sister Makeup", reply.call_args.args[1])
        self.assertEqual(reply.call_args.kwargs["tenant_id"], "t-1")

    async def test_group_happy_path_stages_as_group_source(self):
        with (
            patch("services.line_binding.line_client_group.get_group", return_value=_GROUP),
            patch("core.feature_flags.pearnly_ai_line_intake_enabled_for", return_value=True),
            patch("services.line_binding.line_client.download_message_content", return_value=b"x"),
            patch.object(m, "_save_to_disk", return_value="/tmp/f.jpg"),
            patch("services.line_binding.line_intake_store.latest_open_period", return_value=None),
            patch(
                "services.line_binding.line_intake_store.insert_staging", return_value=True
            ) as ins,
            patch(
                "services.line_binding.line_intake_store.client_display_name", return_value="冰厂"
            ),
            patch("services.line_binding.line_reply.reply_text_context") as reply,
        ):
            self.assertTrue(await m.try_stage_media(_group_event(), lang_hint="zh"))
        self.assertEqual(ins.call_args.kwargs["source"], "group")
        self.assertIsNone(ins.call_args.kwargs["suggested_period"])
        self.assertIn("冰厂", reply.call_args.args[1])

    async def test_duplicate_message_id_no_double_record_no_double_reply(self):
        with (
            patch("services.line_binding.line_client_group.get_group", return_value=_GROUP),
            patch("core.feature_flags.pearnly_ai_line_intake_enabled_for", return_value=True),
            patch("services.line_binding.line_client.download_message_content", return_value=b"x"),
            patch.object(m, "_save_to_disk", return_value="/tmp/dup.jpg"),
            patch("services.line_binding.line_intake_store.latest_open_period", return_value=None),
            patch("services.line_binding.line_intake_store.insert_staging", return_value=False),
            patch.object(m, "_discard_file") as discard,
            patch("services.line_binding.line_reply.reply_text_context") as reply,
        ):
            self.assertTrue(await m.try_stage_media(_group_event()))
        discard.assert_called_once_with("/tmp/dup.jpg")
        reply.assert_not_called()

    async def test_download_failure_is_honest_no_receipt(self):
        """下载失败 → 不回「已收到」(等客户重发),但仍归本分支管(True 不回落原路)。"""
        with (
            patch("core.db.get_user_by_line_user_id", return_value=None),
            patch(
                "services.line_binding.line_client_contact.list_contacts_by_line_user",
                return_value=[_CONTACT],
            ),
            patch("core.feature_flags.pearnly_ai_line_intake_enabled_for", return_value=True),
            patch("services.line_binding.line_client.download_message_content", return_value=None),
            patch("services.line_binding.line_intake_store.insert_staging") as ins,
            patch("services.line_binding.line_reply.reply_text_context") as reply,
        ):
            self.assertTrue(await m.try_stage_media(_dm_event()))
        ins.assert_not_called()
        reply.assert_not_called()

    async def test_any_exception_fails_open(self):
        with patch("core.db.get_user_by_line_user_id", side_effect=RuntimeError("db down")):
            self.assertFalse(await m.try_stage_media(_dm_event()))


class ReceiptCopyTests(unittest.TestCase):
    def test_four_languages_carry_client_name(self):
        for lang in ("th", "en", "zh", "ja"):
            self.assertIn("Sister Makeup", m.receipt_text(lang, "Sister Makeup"))

    def test_unknown_lang_falls_back_to_thai(self):
        self.assertEqual(m.receipt_text("fr", "X"), m.receipt_text("th", "X"))


if __name__ == "__main__":
    unittest.main()
