"""Real PostgreSQL rebind, stale state and concurrent confirmation regressions."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import os
import threading
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit
from uuid import uuid4

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from core import db
from services.erp import push_store
from services.line_dms import account_channel, binding_guard, login_tickets, schema, store
from tests.unit._pg_smoke import require_disposable_db


class DmsBindingPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dsn = os.environ.get("PEARNLY_DMS_BINDING_TEST_DSN", "")
        if not cls.dsn:
            raise unittest.SkipTest("explicit disposable DMS binding DSN required")
        parsed = urlsplit(cls.dsn)
        if (
            parsed.hostname not in {"localhost", "127.0.0.1"}
            or parsed.path != "/pearnly_ci_dms_binding"
        ):
            raise RuntimeError("refusing non-disposable DMS binding database")
        cls.schema = "dms_binding_test_" + uuid4().hex
        with psycopg2.connect(cls.dsn) as conn, conn.cursor() as cur:
            cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(cls.schema)))
        with cls.cursor(commit=True) as cur:
            cur.execute(schema._BINDINGS)
            cur.execute(schema._BINDING_CODES)
            cur.execute(schema._SESSIONS)
            cur.execute(schema._ACCOUNT_CHANNELS)
            for statement in schema._MIGRATIONS:
                cur.execute(statement)
            cur.execute(schema._SESSIONS_PK)
            cur.execute(login_tickets._DDL)
            for statement in login_tickets._MIGRATIONS:
                cur.execute(statement)
            for statement in login_tickets._INDEXES:
                cur.execute(statement)
            cur.execute(
                "CREATE TABLE erp_endpoints(id uuid PRIMARY KEY, user_id uuid, "
                "config jsonb, binding_generation integer DEFAULT 0)"
            )

    @classmethod
    @contextmanager
    def cursor(cls, *args, commit=False, **kwargs):
        conn = psycopg2.connect(cls.dsn)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    sql.SQL("SET LOCAL search_path TO {}").format(sql.Identifier(cls.schema))
                )
                yield cur
                if commit:
                    conn.commit()
        finally:
            conn.close()

    @classmethod
    def tearDownClass(cls):
        with cls.cursor(commit=True) as cur:
            require_disposable_db(cur, cls.schema, "dms_binding_test_")
            cur.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(cls.schema)))

    def setUp(self):
        self.enterContext(patch.object(db, "get_cursor", self.cursor))
        self.enterContext(patch.object(db, "get_cursor_rls", self.cursor))
        self.enterContext(patch("services.line_dms.menu_sync.request_sync"))
        self.tenant, self.a, self.b = [str(uuid4()) for _ in range(3)]
        self.line = "line-" + uuid4().hex
        self.assertTrue(store.create_or_update_binding(self.tenant, self.a, self.line))
        self.binding = store.get_binding_by_line_user(self.line)

    def test_rebind_clears_draft_tickets_and_rotates_epoch(self):
        store.set_session(self.tenant, self.line, "reviewing", {"nonce": "old", "draft": "A"})
        ticket = login_tickets.issue_login_ticket(self.tenant, self.a)
        self.assertTrue(store.unbind_by_line_user(self.line))
        self.assertTrue(store.create_or_update_binding(self.tenant, self.b, self.line))
        self.assertNotEqual(store.get_binding_by_line_user(self.line)["id"], self.binding["id"])
        self.assertIsNone(store.get_session(self.tenant, self.line))
        self.assertIsNone(login_tickets.consume_login_ticket(ticket["ticket"]))

    def test_same_user_rebind_also_invalidates_old_epoch(self):
        self.assertTrue(store.create_or_update_binding(self.tenant, self.a, self.line))
        self.assertNotEqual(store.get_binding_by_line_user(self.line)["id"], self.binding["id"])

    def test_late_old_task_cannot_replace_or_delete_new_draft(self):
        store.unbind_by_line_user(self.line)
        store.create_or_update_binding(self.tenant, self.b, self.line)
        store.set_session(self.tenant, self.line, "reviewing", {"nonce": "new", "draft": "B"})
        with binding_guard.scope(self.binding):
            store.set_session(self.tenant, self.line, "reviewing", {"draft": "A"})
            store.clear_session(self.tenant, self.line)
            self.assertIsNone(store.get_session(self.tenant, self.line))
            self.assertIsNone(store.consume_nonce(self.tenant, self.line, "reviewing", "new"))
        self.assertEqual(store.get_session(self.tenant, self.line)["payload"]["draft"], "B")

    def test_old_credentials_update_is_blocked_inside_write_transaction(self):
        endpoint = str(uuid4())
        with self.cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO erp_endpoints(id,user_id,config) VALUES (%s,%s,%s::jsonb)",
                (endpoint, self.a, '{"password_enc":"original"}'),
            )
        store.unbind_by_line_user(self.line)
        store.create_or_update_binding(self.tenant, self.b, self.line)
        with binding_guard.scope(self.binding):
            self.assertFalse(
                push_store.update_erp_endpoint(self.a, endpoint, config={"password_enc": "wrong"})
            )
        with self.cursor() as cur:
            cur.execute("SELECT config FROM erp_endpoints WHERE id=%s", (endpoint,))
            self.assertEqual(cur.fetchone()["config"]["password_enc"], "original")

    def test_twenty_concurrent_confirmations_claim_once(self):
        store.set_session(self.tenant, self.line, "reviewing", {"nonce": "once", "draft": "A"})
        barrier = threading.Barrier(20)

        def claim(_):
            barrier.wait(timeout=10)
            with binding_guard.scope(self.binding):
                return store.consume_nonce(self.tenant, self.line, "reviewing", "once")

        with ThreadPoolExecutor(max_workers=20) as pool:
            results = list(pool.map(claim, range(20)))
        winners = [r for r in results if r is not None]
        self.assertEqual(winners, [{"nonce": "once", "draft": "A"}])

    def test_concurrent_rebind_and_old_state_write_cannot_leave_old_draft(self):
        barrier = threading.Barrier(2)

        def rebind():
            barrier.wait(timeout=10)
            store.unbind_by_line_user(self.line)
            store.create_or_update_binding(self.tenant, self.b, self.line)

        def late_write():
            barrier.wait(timeout=10)
            with binding_guard.scope(self.binding):
                store.set_session(self.tenant, self.line, "reviewing", {"nonce": "stale"})

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(rebind), pool.submit(late_write)]
            for future in futures:
                future.result(timeout=15)
        self.assertIsNone(store.get_session(self.tenant, self.line))

    def test_unbind_by_user_invalidates_all_pending_artifacts(self):
        store.set_session(self.tenant, self.line, "reviewing", {"nonce": "old"})
        ticket = login_tickets.issue_login_ticket(self.tenant, self.a)
        self.assertTrue(store.unbind_by_user(self.a))
        self.assertIsNone(store.get_binding_by_line_user(self.line))
        self.assertIsNone(store.get_session(self.tenant, self.line))
        self.assertIsNone(login_tickets.consume_login_ticket(ticket["ticket"]))

    def test_same_line_id_cannot_take_two_users_on_one_oa(self):
        account_channel.set_channel(self.tenant, "dms_a")
        self.assertTrue(
            store.create_or_update_binding(self.tenant, self.a, self.line, channel_key="dms_a")
        )
        self.assertIsNotNone(store.get_binding_by_line_user(self.line, "dms_a"))
        self.assertFalse(
            store.create_or_update_binding(self.tenant, self.b, self.line, channel_key="dms_a")
        )

    def test_schema_constraints_are_channel_scoped(self):
        """Unique (channel_key, line_user_id) + session PK includes channel_key."""
        with self.cursor() as cur:
            cur.execute(
                "SELECT indexdef FROM pg_indexes WHERE schemaname = current_schema() "
                "AND indexname = 'ux_line_dms_bindings_channel_line'"
            )
            indexdef = cur.fetchone()["indexdef"]
            self.assertIn("UNIQUE", indexdef)
            self.assertIn("channel_key", indexdef)
            self.assertIn("line_user_id", indexdef)
            cur.execute(
                "SELECT pg_get_constraintdef(oid) AS definition FROM pg_constraint "
                "WHERE conrelid = 'dms_line_sessions'::regclass AND contype = 'p'"
            )
            definition = cur.fetchone()["definition"]
            self.assertIn("channel_key", definition)
            self.assertIn("line_user_id", definition)

    def test_sessions_are_keyed_by_channel(self):
        store.set_session(self.tenant, self.line, "state_dms", {"v": 1})
        store.set_session(self.tenant, self.line, "state_a", {"v": 2}, channel_key="dms_a")
        self.assertEqual(store.get_session(self.tenant, self.line)["state"], "state_dms")
        self.assertEqual(
            store.get_session(self.tenant, self.line, channel_key="dms_a")["state"], "state_a"
        )

    def test_channel_change_is_atomic_and_kills_old_codes_and_bindings(self):
        account_channel.set_channel(self.tenant, "dms_a")
        issued = store.generate_bind_code(self.tenant, self.a, "dms_a")
        self.assertEqual(issued["channel_key"], "dms_a")
        self.assertTrue(
            store.create_or_update_binding(self.tenant, self.a, self.line, channel_key="dms_a")
        )
        result = account_channel.set_channel(self.tenant, "dms_b")
        self.assertTrue(result["changed"])
        self.assertEqual(result["unbound"], 1)
        self.assertIsNone(store.get_binding_by_line_user(self.line, "dms_a"))
        self.assertIsNone(store.consume_bind_code(issued["code"], "dms_a"))
        # The stale code can no longer restore the old OA even if it is still submitted.
        self.assertFalse(
            store.create_or_update_binding(self.tenant, self.a, self.line, channel_key="dms_a")
        )

    def test_bind_code_issuance_refuses_stale_channel_under_the_account_lock(self):
        account_channel.set_channel(self.tenant, "dms_b")
        self.assertIsNone(store.generate_bind_code(self.tenant, self.a, "dms_a"))
        self.assertIsNotNone(store.generate_bind_code(self.tenant, self.a, "dms_b"))

    def test_login_ticket_carries_binding_channel_and_epoch(self):
        account_channel.set_channel(self.tenant, "dms_a")
        self.assertTrue(
            store.create_or_update_binding(self.tenant, self.a, self.line, channel_key="dms_a")
        )
        binding = store.get_binding_by_line_user(self.line, "dms_a")
        with binding_guard.scope(binding):
            ticket = login_tickets.issue_login_ticket(self.tenant, self.a)
        identity = login_tickets.consume_login_ticket(ticket["ticket"])
        self.assertEqual(identity["channel_key"], "dms_a")
        self.assertEqual(identity["binding_id"], binding["id"])
