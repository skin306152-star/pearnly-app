"""Owner chat transitions and independence from ERP intake."""

from contextlib import contextmanager
from copy import deepcopy
import unittest
from unittest.mock import patch

from services.cowork_line import work_flow as flow, work_cards as cards


class OwnerFlowTests(unittest.TestCase):
    def setUp(self):
        self.state = {"board": "b", "mappings": {"b": {key: key for key in cards.STATES}}}
        self.identity = {
            "user_id": "u",
            "tenant_id": "t",
            "membership_id": "m",
            "line_user_id": "l",
        }
        self.data = {
            "userId": "u",
            "board": {"_id": "b", "title": "Board"},
            "lists": [{"_id": key, "title": key} for key in cards.STATES],
            "cards": [],
            "people": [{"_id": "u", "name": "Owner"}],
            "lanes": [{"_id": "lane"}],
            "comments": [],
            "attachments": [],
        }
        self.stack = []
        p = patch.object(flow.work_store, "board_mapping", return_value={})
        p.start()
        self.addCleanup(p.stop)
        for target, replacement in [("conversation", self.conversation)]:
            p = patch.object(flow.work_store, target, replacement)
            p.start()
            self.addCleanup(p.stop)
        p = patch.object(flow.remote, "actor", return_value={"work_role": "owner"})
        p.start()
        self.addCleanup(p.stop)
        self.snapshot = patch.object(
            flow.remote, "snapshot", side_effect=lambda *a: deepcopy(self.data)
        )
        self.snapshot.start()
        self.addCleanup(self.snapshot.stop)

    @contextmanager
    def conversation(self, _identity):
        yield self.state

    def command(self, command, **params):
        from urllib.parse import urlencode

        event = {
            "type": "postback",
            "postback": {
                "data": urlencode(
                    {"a": "work", "c": command, "n": self.state.get("nonce", ""), **params}
                )
            },
        }
        return flow.process(event, self.identity, "zh")

    def text(self, text):
        return flow.process(
            {"type": "message", "message": {"type": "text", "text": text}}, self.identity, "zh"
        )

    def test_create_edit_keyboard_and_confirm_only_write(self):
        with patch.object(flow.actions, "save") as save:
            self.command("home")
            self.command("new")
            self.text("明天核对库存")
            self.assertEqual(self.state["draft"]["title"], "明天核对库存")
            self.command("assignee")
            self.command("person", id="u")
            self.command("field", f="description")
            result = self.text("提交差异明细")
            self.assertEqual(self.state["draft"]["description"], "提交差异明细")
            save.assert_not_called()
            buttons = result["quickReply"]["items"]
            self.assertTrue(any(b["action"].get("inputOption") == "openKeyboard" for b in buttons))
            self.assertTrue(any(b["action"]["type"] == "datetimepicker" for b in buttons))

    def test_menu_suspends_work_without_erasing_draft(self):
        self.command("home")
        self.command("new")
        self.text("Keep draft")
        before = deepcopy(self.state["draft"])
        self.assertIsNone(self.text("Menu"))
        self.assertFalse(self.state["active"])
        self.assertEqual(self.state["draft"], before)
        self.assertIsNone(self.text("ERP input"))
        self.command("home")
        self.command("resume")
        self.assertEqual(self.state["draft"], before)

    def test_editor_languages_keep_preview_and_primary_actions_thai(self):
        self.command("home")
        self.command("new")
        self.text("ตรวจสอบสต็อก")
        for lang in ("th", "zh", "en", "ja"):
            result = self.command("edit_lang", l=lang)
            body = result["contents"]["body"]["contents"]
            self.assertTrue(any("ผู้รับผิดชอบ" in row["text"] for row in body))
            self.assertEqual(
                [b["action"]["label"] for b in result["contents"]["footer"]["contents"]],
                ["ยืนยัน", "แก้ไข", "ยกเลิก", "กลับ"],
            )
            self.assertEqual(
                result["quickReply"]["items"][0]["action"]["label"], cards.t(lang, "title")
            )
            prompt = self.command("field", f="description")
            self.assertEqual(prompt["text"].split("\n")[0], cards.t("th", "description"))
            self.text("ตรวจนับสินค้า")

    def test_plain_steps_and_empty_board_back_escape(self):
        self.state.pop("board")
        self.data["boards"] = []
        result = self.command("boards")
        self.assertEqual(result["type"], "text")
        result = self.command("home")
        self.assertNotIn(cards.t("th", "boards") + "\n", result["text"])
        self.assertIn("สร้างบอร์ด", result["text"])
        self.assertEqual(self.command("create_board")["type"], "text")
        confirm = self.text("New board")
        self.assertEqual(confirm["type"], "flex")
        footer = confirm["contents"]["footer"]
        self.assertEqual(footer["layout"], "vertical")
        self.assertEqual(footer["contents"][0]["style"], "primary")
        self.assertEqual(footer["contents"][1]["style"], "secondary")

    def test_saved_task_returns_plain_status_after_write(self):
        self.data["cards"] = [
            {"_id": "c", "title": "Task", "listId": "pending", "assignees": ["u"]}
        ]
        self.command("home")
        self.state["draft"] = {"title": "Task", "assignees": ["u"]}
        with (
            patch.object(flow.actions, "save", return_value="c"),
            patch.object(flow.actions, "notify", return_value=True),
        ):
            result = self.command("save")
        self.assertEqual(result["type"], "text")
        self.assertIn(cards.t("th", "saved"), result["text"])
        self.assertNotIn("draft", self.state)

    def test_old_button_cannot_change_task(self):
        self.command("home")
        old = self.state["nonce"]
        self.command("new")
        result = flow.process(
            {"type": "postback", "postback": {"data": "a=work&c=save&n=" + old}},
            self.identity,
            "zh",
        )
        self.assertEqual(result["text"], cards.t("th", "expired"))

    def test_accept_only_awaiting_review_and_requires_confirmation(self):
        self.data["cards"] = [
            {
                "_id": "c",
                "title": "Task",
                "boardId": "b",
                "listId": "review",
                "modifiedAt": "one",
                "assignees": ["u"],
            }
        ]
        self.command("home")
        self.command("task", id="c")
        with patch.object(flow.remote, "mutate") as mutate:
            self.command("accept")
            mutate.assert_not_called()
            self.data["cards"][0]["modifiedAt"] = "two"
            self.command("apply")
            mutate.assert_not_called()

    def test_blank_editor_omits_invalid_empty_line_fill_text(self):
        for lang in ("th", "en", "zh", "ja"):
            blank = cards.edit_button(lang, "description", "nonce", "")["action"]
            self.assertEqual(blank["inputOption"], "openKeyboard")
            self.assertNotIn("fillInText", blank)
            filled = cards.edit_button(lang, "description", "nonce", "existing")["action"]
            self.assertEqual(filled["fillInText"], "existing")

    def test_language_rows_and_native_limits(self):
        for key, translations in cards.COPY.items():
            self.assertEqual(len(translations), 4, key)
            self.assertTrue(all(translations), key)
        for lang in ("th", "en", "zh", "ja"):
            self.state["nonce"] = "n" * 16
            result = flow.views.home(lang, self.state, self.data)
            for item in result.get("quickReply", {}).get("items", []):
                self.assertLessEqual(len(item["action"]["label"]), 20)
                self.assertLessEqual(len(item["action"].get("data", "")), 300)


if __name__ == "__main__":
    unittest.main()
