"""Real SQL authorization and independent conversation persistence."""

from contextlib import contextmanager
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException
from psycopg2.extras import RealDictCursor

from services.cowork_line import work_store
from services.work_bridge import line_owner
from tests.unit._pg_smoke import connect_or_skip, require_disposable_db


class WorkOwnerPgTests(unittest.TestCase):
    def setUp(self):
        self.conn = connect_or_skip()
        self.schema = "smoke_line_work_" + uuid4().hex[:10]
        self.ids = {key: str(uuid4()) for key in ("tenant_id", "membership_id", "user_id", "role")}
        self.identity = {**self.ids, "line_user_id": "local-owner"}
        with self.conn.cursor() as cur:
            cur.execute(f'CREATE SCHEMA "{self.schema}"')
            cur.execute(f'SET search_path TO "{self.schema}", public')
            cur.execute("CREATE TABLE tenants(id uuid PRIMARY KEY, status text)")
            cur.execute(
                "CREATE TABLE users(id uuid PRIMARY KEY, username text, full_name text, email text, is_active boolean, expires_at timestamptz)"
            )
            cur.execute("CREATE TABLE roles(id uuid PRIMARY KEY, key text)")
            cur.execute(
                "CREATE TABLE memberships(id uuid PRIMARY KEY, user_id uuid, tenant_id uuid, role_id uuid, status text)"
            )
            cur.execute(
                "CREATE TABLE cowork_line_identities(membership_id uuid, user_id uuid, tenant_id uuid, line_user_id text, revoked_at timestamptz)"
            )
            cur.execute("INSERT INTO tenants VALUES (%s, 'active')", (self.ids["tenant_id"],))
            cur.execute(
                "INSERT INTO users VALUES (%s, 'owner', 'Owner', NULL, true, NULL)",
                (self.ids["user_id"],),
            )
            cur.execute("INSERT INTO roles VALUES (%s, 'owner')", (self.ids["role"],))
            cur.execute(
                "INSERT INTO memberships VALUES (%s,%s,%s,%s,'active')",
                tuple(self.ids[x] for x in ("membership_id", "user_id", "tenant_id", "role")),
            )
            cur.execute(
                "INSERT INTO cowork_line_identities VALUES (%s,%s,%s,'local-owner',NULL)",
                tuple(self.ids[x] for x in ("membership_id", "user_id", "tenant_id")),
            )
        self.conn.commit()
        for name in ("get_cursor", "get_cursor_rls"):
            p = patch("core.db." + name, self.cursor)
            p.start()
            self.addCleanup(p.stop)
        work_store.migrate_schema()
        work_store.migrate_schema()

    @contextmanager
    def cursor(self, *args, commit=False, **kwargs):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                if args:
                    cur.execute("SELECT set_config('app.tenant_id', %s, true)", (args[0],))
                yield cur
                if commit:
                    self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

    def tearDown(self):
        self.conn.rollback()
        with self.conn.cursor() as cur:
            require_disposable_db(cur, self.schema, "smoke_line_work_")
            cur.execute(f'DROP SCHEMA "{self.schema}" CASCADE')
        self.conn.commit()
        self.conn.close()

    def test_live_owner_binding_and_revocation(self):
        self.assertEqual(line_owner.owner(self.identity)["user_id"], self.ids["user_id"])
        with self.cursor(commit=True) as cur:
            cur.execute("UPDATE cowork_line_identities SET revoked_at=now()")
        with self.assertRaises(HTTPException):
            line_owner.owner(self.identity)

    def test_employee_and_other_tenant_denied(self):
        with self.assertRaises(HTTPException):
            line_owner.owner({**self.identity, "tenant_id": str(uuid4())})
        with self.cursor(commit=True) as cur:
            cur.execute("UPDATE roles SET key='accountant'")
        with self.assertRaises(HTTPException):
            line_owner.owner(self.identity)

    def test_expired_assignee_does_not_receive_task_content(self):
        from services.cowork_line import work_actions

        user_id, membership = str(uuid4()), str(uuid4())
        with self.cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO users VALUES (%s,'expired','Employee',NULL,true,now()-interval '1 day')",
                (user_id,),
            )
            cur.execute(
                "INSERT INTO memberships VALUES (%s,%s,%s,%s,'active')",
                (membership, user_id, self.ids["tenant_id"], self.ids["role"]),
            )
            cur.execute(
                "INSERT INTO cowork_line_identities VALUES (%s,%s,%s,'expired-line',NULL)",
                (membership, user_id, self.ids["tenant_id"]),
            )
        data = {
            "userId": "owner-native",
            "board": {"title": "Board"},
            "people": [{"_id": "employee-native", "user_id": user_id}],
        }
        item = {
            "_id": "card",
            "boardId": "board",
            "title": "Task",
            "assignees": ["employee-native"],
        }
        with patch.object(work_actions.line, "push_messages") as push:
            self.assertFalse(work_actions.notify(self.identity, item, data, "th"))
            push.assert_not_called()

    def test_draft_persists_and_transaction_rolls_back(self):
        with work_store.conversation(self.identity) as state:
            state["draft"] = {"title": "盘点"}
        with work_store.conversation(self.identity) as state:
            self.assertEqual(state["draft"]["title"], "盘点")

        with self.assertRaises(RuntimeError):
            with work_store.conversation(self.identity) as state:
                state["draft"]["title"] = "discard me"
                raise RuntimeError("rollback")
        with work_store.conversation(self.identity) as state:
            self.assertEqual(state["draft"]["title"], "盘点")

    def test_owner_notice_retries_with_stable_receipt_and_stops_after_success(self):
        from services.cowork_line import work_notifications as notices

        with work_store.conversation(self.identity) as state:
            state.update(lang="th", mappings={"board": {"review": "review"}})
        data = {
            "board": {"title": "งาน"},
            "cards": [{"_id": "task", "title": "ตรวจนับ", "listId": "review"}],
        }
        with (
            patch.object(notices.remote, "snapshot", return_value=data),
            patch.object(notices, "push") as push,
        ):
            notices.deliver("board", "task", "old-event", "doing")
            push.assert_not_called()
            push.side_effect = HTTPException(503, "retry")
            with self.assertRaises(HTTPException):
                notices.deliver("board", "task", "event", "review")
            first = push.call_args.args
            push.side_effect = None
            notices.deliver("board", "task", "event", "review")
            self.assertEqual(push.call_args.args, first)
            notices.deliver("board", "task", "event", "review")
            self.assertEqual(push.call_count, 2)


if __name__ == "__main__":
    unittest.main()
