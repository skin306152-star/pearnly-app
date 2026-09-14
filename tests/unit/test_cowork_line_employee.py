"""Employee capabilities cannot reuse owner buttons or accept completed work."""

import unittest
from unittest.mock import patch

from tests.unit import test_cowork_line_work as owner_tests
from services.cowork_line import work_flow as flow


class EmployeeFlowTests(unittest.TestCase):
    command = owner_tests.OwnerFlowTests.command
    conversation = owner_tests.OwnerFlowTests.conversation
    text = owner_tests.OwnerFlowTests.text

    def setUp(self):
        owner_tests.OwnerFlowTests.setUp(self)
        self.actor = patch.object(flow.remote, "actor", return_value={"work_role": "employee"})
        self.actor.start()
        self.addCleanup(self.actor.stop)
        self.data["cards"] = [
            {
                "_id": "c",
                "title": "ตรวจนับ",
                "boardId": "b",
                "listId": "pending",
                "assignees": ["u"],
                "modifiedAt": "first",
            }
        ]

    def test_employee_menu_and_no_owner_mutations(self):
        self.command("home")
        self.command("task", id="c")
        with patch.object(flow.remote, "mutate") as mutate:
            for command in (
                "accept",
                "return",
                "new",
                "create_board",
                "setup",
                "edit",
                "team",
                "add_member",
            ):
                self.command(command)
            self.command("set_status", s="done")
            mutate.assert_not_called()
        result = self.command("task", id="c")
        commands = [x["action"].get("data", "") for x in result["quickReply"]["items"]]
        self.assertTrue(any("s=review" in x for x in commands))
        self.assertFalse(any("c=accept" in x or "c=edit" in x for x in commands))

    def test_employee_confirmed_progress_and_closed_task(self):
        self.command("home")
        self.command("task", id="c")

        def move(*args):
            self.data["cards"][0]["listId"] = args[3]["listId"]

        with patch.object(flow.remote, "mutate", side_effect=move) as mutate:
            self.command("set_status", s="review")
            mutate.assert_not_called()
            self.command("apply")
            mutate.assert_called_once()
        self.data["cards"][0]["listId"] = "done"
        with patch.object(flow.remote, "mutate") as mutate:
            self.command("set_status", s="doing")
            self.command("comment")
            mutate.assert_not_called()
