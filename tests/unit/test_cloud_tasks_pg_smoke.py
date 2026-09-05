"""Real PostgreSQL delivery/lock tests, restricted to an explicitly disposable local DB."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import os
import threading
import unittest
from unittest.mock import AsyncMock, patch
from urllib.parse import urlsplit
from uuid import UUID, uuid4

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql

from services.cloud_tasks import registry, routes, store, workorders
from services.erp import session_lock
from tests.unit._pg_smoke import require_disposable_db


class CloudTasksPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dsn = os.environ.get("PEARNLY_CLOUD_TASKS_TEST_DSN", "")
        if not cls.dsn:
            raise unittest.SkipTest("explicit disposable Cloud Tasks DSN required")
        parsed = urlsplit(cls.dsn)
        if parsed.hostname not in {"127.0.0.1", "localhost"} or not parsed.path.startswith(
            "/pearnly_ci_cloud_tasks"
        ):
            raise RuntimeError("refusing non-disposable Cloud Tasks test database")
        cls.schema = "cloud_tasks_test_" + uuid4().hex
        cls.created_roles = []
        with psycopg2.connect(cls.dsn) as conn, conn.cursor() as cur:
            cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(cls.schema)))
            for role in ("anon", "authenticated"):
                cur.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (role,))
                if not cur.fetchone():
                    cur.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(role)))
                    cls.created_roles.append(role)
                cur.execute(
                    sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                        sql.Identifier(cls.schema), sql.Identifier(role)
                    )
                )
                # Reproduce Supabase explicit default grants, not just PUBLIC ACLs.
                cur.execute(
                    sql.SQL(
                        "ALTER DEFAULT PRIVILEGES IN SCHEMA {} " "GRANT ALL ON TABLES TO {}"
                    ).format(sql.Identifier(cls.schema), sql.Identifier(role))
                )
        with patch.object(store, "get_cursor", cls.cursor):
            store.ensure_table()
        with cls.cursor(commit=True) as cur:
            cur.execute("CREATE TABLE observed_effects(id SERIAL PRIMARY KEY)")
            cur.execute(
                "CREATE TABLE work_orders(tenant_id TEXT, id TEXT, "
                "run_lease_owner TEXT, run_lease_expires_at TIMESTAMPTZ, "
                "updated_at TIMESTAMPTZ DEFAULT now())"
            )

    @classmethod
    @contextmanager
    def cursor(cls, commit=False):
        conn = psycopg2.connect(cls.dsn)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    sql.SQL("SET LOCAL search_path TO {}").format(sql.Identifier(cls.schema))
                )
                yield cur
                if commit:
                    conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @classmethod
    def tearDownClass(cls):
        with cls.cursor(commit=True) as cur:
            require_disposable_db(cur, cls.schema, "cloud_tasks_test_")
            cur.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(cls.schema)))
            for role in cls.created_roles:
                cur.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))

    def setUp(self):
        self.patch_cursor = patch.object(store, "get_cursor", self.cursor)
        self.patch_cursor.start()
        self.addCleanup(self.patch_cursor.stop)
        with self.cursor(commit=True) as cur:
            require_disposable_db(cur, self.schema, "cloud_tasks_test_")
            cur.execute(
                "TRUNCATE cloud_task_deliveries, cloud_task_locks, observed_effects, work_orders"
            )

    def test_default_client_grants_are_revoked_and_rls_blocks_rows(self):
        task_id = store.insert("dms.image", {"args": ["private"], "kwargs": {}})
        for role in ("anon", "authenticated"):
            with self.subTest(role=role), self.cursor(commit=True) as cur:
                for table in ("cloud_task_deliveries", "cloud_task_locks"):
                    cur.execute(
                        "SELECT has_table_privilege(%s, %s, %s) AS allowed",
                        (role, self.schema + "." + table, "SELECT"),
                    )
                    self.assertFalse(cur.fetchone()["allowed"])
                cur.execute(
                    sql.SQL("GRANT SELECT ON cloud_task_deliveries TO {}").format(
                        sql.Identifier(role)
                    )
                )
                cur.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                cur.execute("SELECT id FROM cloud_task_deliveries WHERE id=%s::uuid", (task_id,))
                self.assertEqual(cur.fetchall(), [])
                cur.execute("RESET ROLE")
                cur.execute(
                    sql.SQL("REVOKE SELECT ON cloud_task_deliveries FROM {}").format(
                        sql.Identifier(role)
                    )
                )

    def test_concurrent_delivery_claims_have_one_execution_owner(self):
        task_id = store.insert("dms.image", {"args": [], "kwargs": {}})
        barrier = threading.Barrier(8)

        def claim():
            barrier.wait(timeout=5)
            return store.claim(task_id)

        with ThreadPoolExecutor(max_workers=8) as pool:
            rows = list(pool.map(lambda _: claim(), range(8)))
        self.assertEqual(sum("handler" in row for row in rows), 1)
        self.assertTrue(all(row["status"] == "running" for row in rows))

    def test_stale_execution_is_uncertain_not_requeued_and_late_finish_cannot_override(self):
        task_id = store.insert("dms.image", {"args": [], "kwargs": {}})
        store.claim(task_id)
        with self.cursor(commit=True) as cur:
            cur.execute("UPDATE cloud_task_deliveries SET lease_until=now()-interval '1 minute'")
        self.assertEqual(store.recoverable(), [])
        store.finish(task_id, "succeeded")
        self.assertEqual(store.claim(task_id), {"status": "uncertain"})

    def test_partial_external_effect_error_is_visible_and_duplicate_delivery_does_not_replay(self):
        task_id = store.insert("dms.image", {"args": [], "kwargs": {}})

        async def partial_effect(*_):
            with self.cursor(commit=True) as cur:
                cur.execute("INSERT INTO observed_effects DEFAULT VALUES")
            raise RuntimeError("simulated response lost after external commit")

        with patch.object(registry, "execute", side_effect=partial_effect) as execute:
            first = asyncio.run(routes.run_delivery(routes.Delivery(task_id=UUID(task_id))))
            second = asyncio.run(routes.run_delivery(routes.Delivery(task_id=UUID(task_id))))
        self.assertEqual(first, {"status": "failed"})
        self.assertEqual(second, {"status": "failed"})
        self.assertEqual(execute.call_count, 1)
        with self.cursor(commit=True) as cur:
            cur.execute("SELECT count(*) AS count FROM observed_effects")
            self.assertEqual(cur.fetchone()["count"], 1)
            cur.execute(
                "SELECT error_code FROM cloud_task_deliveries WHERE id=%s::uuid", (task_id,)
            )
            self.assertEqual(cur.fetchone()["error_code"], "RuntimeError")

    def test_delivery_json_roundtrip_and_completed_payload_retention(self):
        user_id = uuid4()
        task_id = store.insert(
            "dms.image", {"args": [user_id, None, 3, True], "kwargs": {"lang": "th"}}
        )
        self.assertEqual(store.claim(task_id)["payload"]["args"], [str(user_id), None, 3, True])
        store.finish(task_id, "succeeded")
        with self.cursor(commit=True) as cur:
            cur.execute("UPDATE cloud_task_deliveries SET updated_at=now()-interval '8 days'")
        store.recoverable()
        with self.cursor(commit=True) as cur:
            cur.execute("SELECT payload, status FROM cloud_task_deliveries")
            self.assertEqual(dict(cur.fetchone()), {"payload": {}, "status": "succeeded"})

    def test_maintenance_owner_cas_does_not_release_successor(self):
        first = store.acquire_maintenance()
        self.assertIsNotNone(first)
        self.assertIsNone(store.acquire_maintenance())
        with self.cursor(commit=True) as cur:
            cur.execute("UPDATE cloud_task_locks SET lease_until=now()-interval '1 minute'")
        second = store.acquire_maintenance()
        self.assertIsNotNone(second)
        store.release_maintenance(first)
        self.assertIsNone(store.acquire_maintenance())
        store.release_maintenance(second)
        self.assertIsNotNone(store.acquire_maintenance())

    def test_queued_workorder_rejects_superseded_lease_before_business_execution(self):
        with self.cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO work_orders VALUES ('tenant', 'order', 'new-owner', "
                "now()+interval '5 minutes', now())"
            )
        with (
            patch("services.cloud_tasks.workorders.db.get_cursor", self.cursor),
            patch.object(workorders.runner, "advance") as advance,
        ):
            self.assertEqual(
                workorders.advance("tenant", "order", "old-owner"), {"skipped": "lease_superseded"}
            )
        advance.assert_not_called()

    def test_real_mrerp_lock_timeout_fails_closed_and_release_allows_successor(self):
        class Pool:
            def getconn(inner):
                return psycopg2.connect(self.dsn)

            def putconn(inner, conn):
                conn.close()

        with (
            patch.dict(os.environ, PEARNLY_RUNTIME_ROLE="worker"),
            patch("core.db.get_pool", return_value=Pool()),
        ):
            with session_lock.mrerp_session_lock("test-only-account", timeout_sec=0) as got:
                self.assertTrue(got)
                with self.assertRaises(session_lock.MrerpSessionLockUnavailable):
                    with session_lock.mrerp_session_lock("test-only-account", timeout_sec=0):
                        self.fail("second browser session must never start")
            with session_lock.mrerp_session_lock("test-only-account", timeout_sec=0) as got:
                self.assertTrue(got)


if __name__ == "__main__":
    unittest.main()
