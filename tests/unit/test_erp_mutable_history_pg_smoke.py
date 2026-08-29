# -*- coding: utf-8 -*-
"""Real PostgreSQL proof for shared history workspace/history lock ordering."""

import concurrent.futures
import threading
import time
import unittest
import uuid
from unittest import mock

from fastapi import HTTPException

from services.intake_bridge import mutable_history_access as access
from tests.unit._pg_smoke import connect, connect_or_skip


class ErpMutableHistoryPgSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        probe = connect_or_skip()
        probe.close()
        from psycopg2.extras import RealDictCursor

        cls.cursor_factory = RealDictCursor
        cls.schema = "erp_mutable_history_pg_smoke"
        cls.tenant_id = str(uuid.uuid4())
        cls.actor_id = str(uuid.uuid4())
        cls.history_id = str(uuid.uuid4())
        cls.workspace_id = uuid.uuid4().int % 2_000_000_000 + 1
        with (
            cls._connect(autocommit=True) as conn,
            conn.cursor(cursor_factory=cls.cursor_factory) as cur,
        ):
            cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{cls.schema}"')
            cur.execute(f'SET search_path TO "{cls.schema}"')
            cur.execute(
                "CREATE TABLE IF NOT EXISTS workspace_clients ("
                "id bigint PRIMARY KEY, tenant_id uuid NOT NULL, is_active boolean NOT NULL)"
            )
            cur.execute(
                "CREATE TABLE IF NOT EXISTS ocr_history ("
                "id uuid PRIMARY KEY, tenant_id uuid NOT NULL, user_id uuid NOT NULL, "
                "workspace_client_id bigint NOT NULL, pages jsonb NOT NULL)"
            )
            cur.execute(
                "CREATE TABLE IF NOT EXISTS purchase_docs ("
                "id uuid PRIMARY KEY, tenant_id uuid NOT NULL, ocr_history_id uuid NOT NULL)"
            )
            cur.execute(
                "CREATE TABLE IF NOT EXISTS sales_documents ("
                "id uuid PRIMARY KEY, tenant_id uuid NOT NULL, ocr_history_id uuid NOT NULL)"
            )

    @classmethod
    def tearDownClass(cls):
        with (
            cls._connect(autocommit=True) as conn,
            conn.cursor(cursor_factory=cls.cursor_factory) as cur,
        ):
            cur.execute(f'SET search_path TO "{cls.schema}"')
            cur.execute("DELETE FROM purchase_docs WHERE tenant_id=%s", (cls.tenant_id,))
            cur.execute("DELETE FROM sales_documents WHERE tenant_id=%s", (cls.tenant_id,))
            cur.execute("DELETE FROM ocr_history WHERE tenant_id=%s", (cls.tenant_id,))
            cur.execute("DELETE FROM workspace_clients WHERE tenant_id=%s", (cls.tenant_id,))

    @classmethod
    def _connect(cls, autocommit=False):
        conn = connect()
        conn.autocommit = autocommit
        return conn

    def setUp(self):
        with (
            self._connect(autocommit=True) as conn,
            conn.cursor(cursor_factory=self.cursor_factory) as cur,
        ):
            cur.execute(f'SET search_path TO "{self.schema}"')
            cur.execute("DELETE FROM purchase_docs WHERE tenant_id=%s", (self.tenant_id,))
            cur.execute("DELETE FROM sales_documents WHERE tenant_id=%s", (self.tenant_id,))
            cur.execute("DELETE FROM ocr_history WHERE tenant_id=%s", (self.tenant_id,))
            cur.execute("DELETE FROM workspace_clients WHERE tenant_id=%s", (self.tenant_id,))
            cur.execute(
                "INSERT INTO workspace_clients VALUES (%s,%s,TRUE)",
                (self.workspace_id, self.tenant_id),
            )
            cur.execute(
                "INSERT INTO ocr_history VALUES (%s,%s,%s,%s,%s::jsonb)",
                (
                    self.history_id,
                    self.tenant_id,
                    self.actor_id,
                    self.workspace_id,
                    '{"version": 1}',
                ),
            )

    def _prepare(self, cur):
        cur.execute(f'SET search_path TO "{self.schema}"')
        cur.execute("SET LOCAL lock_timeout = '3s'")
        cur.execute("SET LOCAL statement_timeout = '5s'")

    def test_formalization_wins_and_waiting_edit_rechecks_formal(self):
        formal_locked = threading.Event()
        edit_attempted = threading.Event()
        release_formal = threading.Event()

        def formalize():
            with self._connect() as conn, conn.cursor(cursor_factory=self.cursor_factory) as cur:
                self._prepare(cur)
                cur.execute(
                    "SELECT id FROM workspace_clients WHERE id=%s AND tenant_id=%s "
                    "AND is_active=TRUE FOR SHARE",
                    (self.workspace_id, self.tenant_id),
                )
                cur.execute(
                    "SELECT id FROM ocr_history WHERE id=%s AND tenant_id=%s "
                    "AND user_id=%s FOR UPDATE",
                    (self.history_id, self.tenant_id, self.actor_id),
                )
                cur.execute(
                    "INSERT INTO purchase_docs VALUES (%s,%s,%s)",
                    (str(uuid.uuid4()), self.tenant_id, self.history_id),
                )
                formal_locked.set()
                if not release_formal.wait(timeout=3):
                    raise AssertionError("timed out waiting to release formal transaction")
                return "formalized"

        def edit():
            self.assertTrue(formal_locked.wait(timeout=2))
            with self._connect() as conn, conn.cursor(cursor_factory=self.cursor_factory) as cur:
                self._prepare(cur)
                edit_attempted.set()
                try:
                    with mock.patch.object(access, "check_workspace_scope"):
                        access._lock_mutable_histories(
                            cur,
                            mock.sentinel.request,
                            {"id": self.actor_id, "entry": "main"},
                            self.tenant_id,
                            self.actor_id,
                            [self.history_id],
                        )
                except HTTPException as exc:
                    return exc.detail["code"]
                cur.execute(
                    "UPDATE ocr_history SET pages=%s::jsonb WHERE id=%s",
                    ('{"version": 2}', self.history_id),
                )
                return "edited"

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            formal = pool.submit(formalize)
            mutation = pool.submit(edit)
            self.assertTrue(edit_attempted.wait(timeout=2))
            try:
                time.sleep(0.1)
                self.assertFalse(mutation.done())
            finally:
                release_formal.set()
            self.assertEqual(formal.result(timeout=5), "formalized")
            self.assertEqual(mutation.result(timeout=5), "erp.formal_document_locked")
        with self._connect() as conn, conn.cursor(cursor_factory=self.cursor_factory) as cur:
            self._prepare(cur)
            cur.execute("SELECT pages FROM ocr_history WHERE id=%s", (self.history_id,))
            self.assertEqual(cur.fetchone()["pages"], {"version": 1})

    def test_workspace_archive_waits_for_inflight_mutation(self):
        mutation_locked = threading.Event()
        archive_attempted = threading.Event()
        release_mutation = threading.Event()

        def edit():
            with self._connect() as conn, conn.cursor(cursor_factory=self.cursor_factory) as cur:
                self._prepare(cur)
                with mock.patch.object(access, "check_workspace_scope"):
                    access._lock_mutable_histories(
                        cur,
                        mock.sentinel.request,
                        {"id": self.actor_id, "entry": "cowork"},
                        self.tenant_id,
                        self.actor_id,
                        [self.history_id],
                    )
                mutation_locked.set()
                cur.execute(
                    "UPDATE ocr_history SET pages=%s::jsonb WHERE id=%s",
                    ('{"version": 2}', self.history_id),
                )
                if not release_mutation.wait(timeout=3):
                    raise AssertionError("timed out waiting to release mutation transaction")
                return "edited"

        def archive():
            self.assertTrue(mutation_locked.wait(timeout=2))
            with self._connect() as conn, conn.cursor(cursor_factory=self.cursor_factory) as cur:
                self._prepare(cur)
                archive_attempted.set()
                cur.execute(
                    "UPDATE workspace_clients SET is_active=FALSE WHERE id=%s",
                    (self.workspace_id,),
                )
                return "archived"

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            mutation = pool.submit(edit)
            archived = pool.submit(archive)
            self.assertTrue(archive_attempted.wait(timeout=2))
            try:
                time.sleep(0.1)
                self.assertFalse(archived.done())
            finally:
                release_mutation.set()
            self.assertEqual(mutation.result(timeout=5), "edited")
            self.assertEqual(archived.result(timeout=5), "archived")
        with self._connect() as conn, conn.cursor(cursor_factory=self.cursor_factory) as cur:
            self._prepare(cur)
            cur.execute(
                "SELECT w.is_active, h.pages FROM workspace_clients w "
                "JOIN ocr_history h ON h.workspace_client_id=w.id WHERE w.id=%s",
                (self.workspace_id,),
            )
            row = cur.fetchone()
            self.assertFalse(row["is_active"])
            self.assertEqual(row["pages"], {"version": 2})


if __name__ == "__main__":
    unittest.main()
