"""Opt-in local LINE -> PostgreSQL -> pinned WeKan acceptance, no LINE sends.

Requires LINE_OWNER_TEST_URL on loopback and PEARNLY_PG_SMOKE_URL. The WeKan
database must be a disposable task-owned instance; tests create native boards.
"""

import asyncio
import json
import os
from urllib.parse import urlencode, urlsplit
import unittest
from unittest.mock import patch

from services.cowork_line import work_flow, work_store, work_cards
from services.work_bridge import line_owner
from tests.unit.test_cowork_line_work_pg_smoke import WorkOwnerPgTests


class NativeOwnerAcceptance(unittest.TestCase):
    def setUp(self):
        url = os.environ.get("LINE_OWNER_TEST_URL", "")
        if not url:
            self.skipTest("LINE_OWNER_TEST_URL not set")
        if urlsplit(url).hostname not in {"127.0.0.1", "localhost"}:
            raise RuntimeError("Native acceptance requires a local disposable WeKan")
        self.pg = WorkOwnerPgTests()
        self.pg.setUp()
        self.addCleanup(self.pg.doCleanups)
        self.addCleanup(self.pg.tearDown)
        self.identity = self.pg.identity
        p = patch.dict(
            os.environ,
            {
                "WORK_BRIDGE_URL": url,
                "PEARNLY_ENV": "development",
                "WORK_BRIDGE_SECRET": os.environ["LINE_OWNER_TEST_SECRET"],
            },
        )
        p.start()
        self.addCleanup(p.stop)
        self.events = []

    def state(self):
        with work_store.conversation(self.identity) as state:
            return json.loads(json.dumps(state))

    def command(self, command, **params):
        event = {
            "type": "postback",
            "postback": {
                "data": urlencode(
                    {"a": "work", "c": command, "n": self.state().get("nonce", ""), **params}
                )
            },
        }
        response = work_flow.process(event, self.identity, "zh")
        self.events.append({"event": event, "response": response})
        serialized = json.dumps(response, ensure_ascii=False)
        for language in ("zh", "th", "en", "ja"):
            self.assertNotIn(work_cards.t(language, "failed"), serialized, (command, response))
            self.assertNotIn(work_cards.t(language, "forbidden"), serialized, (command, response))
        return response

    def text(self, value):
        response = work_flow.process(
            {"type": "message", "message": {"type": "text", "text": value}}, self.identity, "zh"
        )
        self.events.append({"text": value, "response": response})
        return response

    def test_native_owner_full_cycle_and_idempotency(self):
        self.command("home")
        self.command("create_board")
        self.text("老板 LINE 验收 " + self.identity["user_id"][:8])
        operation = self.state()["board_draft"]["operation"]
        self.command("confirm_board")
        state = self.state()
        data = line_owner.snapshot(self.identity, state["board"])
        self.assertEqual(len(data["lists"]), 6)
        duplicate = line_owner.mutate(
            self.identity,
            "POST",
            "/api/boards",
            {"title": data["board"]["title"], "permission": "private"},
            operation,
        )
        self.assertEqual(duplicate["_id"], state["board"])
        self.command("new")
        self.text("核对库存差异")
        self.command("assignee")
        self.command("person", id=data["userId"])
        self.command("field", f="description")
        self.text("提交盘点差异明细")
        self.command("attachment")
        work_flow.process(
            {
                "type": "message",
                "message": {
                    "type": "file",
                    "id": "local-attachment",
                    "fileName": "stock-count.csv",
                    "fileSize": 34,
                },
            },
            self.identity,
            "th",
        )
        with patch.object(
            work_flow.actions.line, "download_message_content", return_value=b"sku,count\nDEMO,19\n"
        ):
            self.command("save")
        state = self.state()
        data = line_owner.snapshot(self.identity, state["board"])
        self.assertEqual(len(data["cards"]), 1)
        self.assertEqual(data["cards"][0]["description"], "提交盘点差异明细")
        self.assertEqual(data["cards"][0]["assignees"], [data["userId"]])
        self.assertEqual(len(data["attachments"]), 1)
        self.assertEqual(data["attachments"][0]["name"], "stock-count.csv")
        self.command("files")
        self.command("detail", id=data["cards"][0]["_id"])
        self.command("edit")
        self.command("field", f="title")
        self.text("核对库存差异（已调整）")
        self.command("save")
        self.command("comment")
        self.text("请说明当前进展")
        self.command("apply")
        self.command("status")
        self.command("set_status", s="review")
        self.command("apply")
        self.command("accept")
        self.command("apply")
        fresh = line_owner.snapshot(self.identity, state["board"])
        self.assertEqual(fresh["cards"][0]["listId"], state["mappings"][state["board"]]["done"])
        self.assertEqual(fresh["cards"][0]["title"], "核对库存差异（已调整）")
        self.assertTrue(any(c["text"] == "请说明当前进展" for c in fresh["comments"]))
        for index in range(7):
            self.command("comment")
            self.text(f"บันทึกเพิ่มเติม {index}")
            self.command("apply")
        first = self.command("history")
        self.assertTrue(any(x["action"]["label"] == "ถัดไป" for x in first["quickReply"]["items"]))
        second = self.command("history", p=1)
        self.assertFalse(
            any(
                x["action"]["label"] == "ถัดไป"
                for x in second.get("quickReply", {}).get("items", [])
            )
        )
        output = os.environ.get("LINE_OWNER_ACCEPTANCE_OUTPUT")
        if output:
            from pathlib import Path

            Path(output).write_text(json.dumps(self.events, ensure_ascii=False, indent=2))

    def test_employee_native_scope_and_review_cycle(self):
        from uuid import uuid4
        from fastapi import HTTPException
        from services.cowork_line import work_actions

        owner = self.identity
        employee = {
            **owner,
            "user_id": str(uuid4()),
            "membership_id": str(uuid4()),
            "line_user_id": "employee-" + uuid4().hex,
        }
        role = str(uuid4())
        with self.pg.cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO users VALUES (%s,'employee','พนักงาน',NULL,true,NULL)",
                (employee["user_id"],),
            )
            cur.execute("INSERT INTO roles VALUES (%s,'accountant')", (role,))
            cur.execute(
                "INSERT INTO memberships VALUES (%s,%s,%s,%s,'active')",
                (employee["membership_id"], employee["user_id"], employee["tenant_id"], role),
            )
            cur.execute(
                "INSERT INTO cowork_line_identities VALUES (%s,%s,%s,%s,NULL)",
                (
                    employee["membership_id"],
                    employee["user_id"],
                    employee["tenant_id"],
                    employee["line_user_id"],
                ),
            )
        self.command("home")
        self.command("create_board")
        self.text("ทดสอบวงจรพนักงาน")
        self.command("confirm_board")
        board = self.state()["board"]
        self.command("team")
        self.command("member", id=employee["user_id"])
        self.command("add_member")
        data = line_owner.snapshot(owner, board)
        native_employee = next(
            x["_id"] for x in data["people"] if x["user_id"] == employee["user_id"]
        )
        with patch.object(work_actions.line, "push_messages", return_value=True):
            for person in (data["userId"], native_employee):
                self.command("new")
                self.text("ตรวจนับ " + person)
                self.command("assignee")
                self.command("person", id=person)
                self.command("save")
            assigned = self.state()["task"]
            self.identity = employee
            self.command("open", b=board, id=assigned)
            snapshot = line_owner.snapshot(employee, board)
            self.assertEqual([x["_id"] for x in snapshot["cards"]], [assigned])
            private = next(
                x for x in line_owner.snapshot(owner, board)["cards"] if x["_id"] != assigned
            )
            for method, path, body in (
                ("PUT", work_actions.path(private), {"listId": private["listId"]}),
                ("POST", "/api/boards", {"title": "unauthorized"}),
                ("PUT", work_actions.path(snapshot["cards"][0]), {"title": "unauthorized"}),
            ):
                with self.assertRaises(HTTPException):
                    line_owner.mutate(employee, method, path, body, "denied-" + uuid4().hex)
            self.command("comment")
            self.text("ตรวจนับแล้วครับ")
            self.command("apply")
            self.command("set_status", s="review")
            self.command("apply")
            self.identity = owner
            self.command("open", b=board, id=assigned)
            self.command("return")
            self.text("กรุณาแนบหลักฐานเพิ่มครับ")
            self.command("apply")
            self.identity = employee
            self.command("open", b=board, id=assigned)
            self.command("set_status", s="review")
            self.command("apply")
            self.identity = owner
            self.command("open", b=board, id=assigned)
            self.command("accept")
            self.command("apply")
            final = line_owner.snapshot(employee, board)["cards"][0]
            self.assertEqual(final["listId"], work_store.board_mapping(employee, board)["done"])
            with self.assertRaises(HTTPException):
                line_owner.mutate(
                    employee,
                    "PUT",
                    work_actions.path(final),
                    {"listId": work_store.board_mapping(employee, board)["doing"]},
                    "closed-" + uuid4().hex,
                )

    def test_async_handler_runs_outside_event_loop(self):
        async def check():
            marker = []

            async def heartbeat():
                await asyncio.sleep(0.001)
                marker.append("responsive")

            event = {
                "type": "postback",
                "replyToken": "local-not-sent",
                "postback": {"data": "a=work&c=home"},
            }
            with patch.object(work_flow.line, "reply_messages", return_value=True) as reply:
                result, _ = await asyncio.gather(
                    work_flow.handle(event, self.identity, "zh"), heartbeat()
                )
                self.assertTrue(result)
                reply.assert_called_once()
            self.assertEqual(marker, ["responsive"])

        asyncio.run(check())
