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
from services.line_dms import binding_guard, login_tickets, store
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
            cur.execute(store._BINDINGS)
            cur.execute(store._SESSIONS)
            cur.execute(login_tickets._DDL)
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
