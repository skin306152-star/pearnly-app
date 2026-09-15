"""Real PostgreSQL proof that one shared DMS scope has one refresh owner."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import threading
import unittest
from unittest.mock import patch
from uuid import uuid4

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from services.erp import dms_master_shared as shared
from services.erp import dms_masters_cache as cache
from tests.unit._pg_smoke import LOCAL_DSN, connect_or_skip, require_disposable_db


class SharedMasterLeasePostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        probe = connect_or_skip()
        probe.close()
        cls.schema = "dms_master_shared_test_" + uuid4().hex
        with psycopg2.connect(LOCAL_DSN) as conn, conn.cursor() as cur:
            cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(cls.schema)))
        with patch("core.db.get_cursor", cls.cursor):
            shared.migrate_lock_table()
            cache.ensure_table()

    @classmethod
    @contextmanager
    def cursor(cls, commit=False):
        conn = psycopg2.connect(LOCAL_DSN)
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
            require_disposable_db(cur, cls.schema, "dms_master_shared_test_")
            cur.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(cls.schema)))

    def setUp(self):
        with self.cursor(commit=True) as cur:
            cur.execute("TRUNCATE dms_master_refresh_locks")
            cur.execute("TRUNCATE dms_masters_cache")

    def test_concurrent_scope_has_exactly_one_refresh_owner(self):
        barrier = threading.Barrier(8)

        def acquire():
            barrier.wait(timeout=5)
            with patch("core.db.get_cursor", self.cursor):
                return shared._acquire("tenant-system-admin", lease_seconds=30)

        with ThreadPoolExecutor(max_workers=8) as pool:
            owners = list(pool.map(lambda _index: acquire(), range(8)))
        winners = [owner for owner in owners if owner]
        self.assertEqual(len(winners), 1)

        with patch("core.db.get_cursor", self.cursor):
            shared._release("tenant-system-admin", winners[0])
        with self.cursor() as cur:
            cur.execute("SELECT count(*) AS count FROM dms_master_refresh_locks")
            self.assertEqual(cur.fetchone()["count"], 0)

    def test_paint_merge_cannot_replace_newer_full_master_bundle(self):
        old_blob = {
            "cars": [["old-car"]],
            "paints_by_car": {"c1": [["old-paint"]]},
            "paints_refreshed_at": {"c1": 1},
        }
        fresh_blob = {"cars": [["fresh-car"]], "company_banks": [["bank-1"]]}
        stale_paint_writer = {
            **old_blob,
            "paints_by_car": {"c1": [["fresh-paint"]]},
            "paints_refreshed_at": {"c1": 2},
        }
        with patch("core.db.get_cursor", self.cursor):
            cache._write("shared-scope", fresh_blob)
            cache._write("shared-scope", stale_paint_writer, touch_refreshed_at=False)
            stored = cache._read("shared-scope")["masters"]
        self.assertEqual(stored["cars"], [["fresh-car"]])
        self.assertEqual(stored["company_banks"], [["bank-1"]])
        self.assertEqual(stored["paints_by_car"]["c1"], [["fresh-paint"]])

    def test_full_master_refresh_cannot_erase_concurrent_paint_result(self):
        full_snapshot_read_before_paint = {"cars": [["c1"], ["c2"]], "company_banks": []}
        paint_writer = {
            "paints_by_car": {"c1": [["p1", "", "Red"]]},
            "paints_refreshed_at": {"c1": 123},
        }
        with patch("core.db.get_cursor", self.cursor):
            cache._write("shared-scope", {"cars": [["c1"]]})
            cache._write("shared-scope", paint_writer, touch_refreshed_at=False)
            cache._write_full_preserving_paints("shared-scope", full_snapshot_read_before_paint)
            stored = cache._read("shared-scope")["masters"]
        self.assertEqual(stored["cars"], [["c1"], ["c2"]])
        self.assertEqual(stored["paints_by_car"]["c1"], [["p1", "", "Red"]])
        self.assertEqual(stored["paints_refreshed_at"]["c1"], 123)


if __name__ == "__main__":
    unittest.main()
