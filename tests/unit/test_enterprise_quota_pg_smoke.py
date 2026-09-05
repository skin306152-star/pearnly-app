"""Real concurrent reservations in an explicitly disposable local PostgreSQL."""

import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from unittest.mock import patch
from urllib.parse import urlsplit
from uuid import uuid4

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from services.ocr.enterprise_quota import try_reserve
from tests.unit._pg_smoke import require_disposable_db


class EnterpriseQuotaPostgresTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dsn = os.environ.get("PEARNLY_OCR_TEST_DSN", "")
        if not cls.dsn:
            raise unittest.SkipTest("explicit disposable OCR test DSN required")
        parsed = urlsplit(cls.dsn)
        if (
            parsed.hostname not in ("127.0.0.1", "localhost")
            or parsed.path != "/pearnly_ci_ocr_quota"
        ):
            raise RuntimeError("refusing non-disposable OCR quota database")
        cls.schema = "ocr_quota_test_" + uuid4().hex
        with psycopg2.connect(cls.dsn) as conn, conn.cursor() as cur:
            cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(cls.schema)))
        with cls.cursor(commit=True) as cur:
            cur.execute(
                "CREATE TABLE cloud_task_locks(name TEXT PRIMARY KEY, owner UUID NOT NULL, lease_until TIMESTAMPTZ NOT NULL)"
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
        finally:
            conn.close()

    @classmethod
    def tearDownClass(cls):
        with cls.cursor(commit=True) as cur:
            require_disposable_db(cur, cls.schema, "ocr_quota_test_")
            cur.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(cls.schema)))

    def test_concurrent_instances_share_one_slot(self):
        key = "ocr:documentai:test:sg:OCR_PROCESSOR"
        with patch("core.db.get_cursor", self.cursor):
            with ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(lambda _: try_reserve(key, 60), range(8)))
            self.assertEqual(1, sum(results))
            self.assertFalse(try_reserve(key, 60))
            self.assertTrue(try_reserve("ocr:documentai:other:sg:OCR_PROCESSOR", 60))
            with self.cursor(commit=True) as cur:
                cur.execute(
                    "UPDATE cloud_task_locks SET lease_until=clock_timestamp()-interval '1 second' WHERE name=%s",
                    (key,),
                )
            self.assertTrue(try_reserve(key, 60))


if __name__ == "__main__":
    unittest.main()
