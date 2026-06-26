# -*- coding: utf-8 -*-
"""B8 RLS wave4 · email_ingest 三表真表隔离(REFACTOR-B8)。

accounts/logs 纯 user(user_id);seen_uids 仅 account_id → 经父表 accounts 的 user-via-parent。
直接调真 enroll_email_ingest_rls() 验 enroll 代码路径。worker/管线路径(list_enabled/
update_status/is/mark_seen)保持裸 owner,本测试不碰。

CI 默认 skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_email_ingest_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

UA = "11111111-1111-1111-1111-111111111111"
UB = "22222222-2222-2222-2222-222222222222"
FAKE = "33333333-3333-3333-3333-333333333333"
ACC_A = "aaaaaaaa-0000-0000-0000-000000000001"

_STUBS = (
    "CREATE TABLE email_ingest_accounts ("
    "  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID UNIQUE NOT NULL,"
    "  email_address TEXT, imap_host TEXT, imap_port INT DEFAULT 993, imap_use_ssl BOOLEAN DEFAULT true,"
    "  password_enc BYTEA, folder TEXT DEFAULT 'INBOX', filter_subject TEXT, filter_sender TEXT,"
    "  mark_as_read BOOLEAN DEFAULT true, enabled BOOLEAN DEFAULT true, interval_min INT DEFAULT 15,"
    "  last_check_at TIMESTAMPTZ, last_fetched_at TIMESTAMPTZ, last_error TEXT,"
    "  success_count INT DEFAULT 0, failure_count INT DEFAULT 0,"
    "  created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW())",
    "CREATE TABLE email_ingest_logs ("
    "  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), account_id UUID, user_id UUID, status TEXT,"
    "  emails_scanned INT DEFAULT 0, attachments_found INT DEFAULT 0, ocr_succeeded INT DEFAULT 0,"
    "  ocr_failed INT DEFAULT 0, elapsed_ms INT DEFAULT 0, error_message TEXT,"
    "  error_details JSONB, trigger TEXT, created_at TIMESTAMPTZ DEFAULT NOW())",
    "CREATE TABLE email_ingest_seen_uids ("
    "  account_id UUID, uid TEXT, history_id TEXT, subject TEXT, sender TEXT,"
    "  UNIQUE(account_id, uid))",
)
_TABLES = ("email_ingest_seen_uids", "email_ingest_logs", "email_ingest_accounts")


class EmailIngestRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.email_ingest import store

        cls.db, cls.rls, cls.store = db, rls, store
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute(f"DROP TABLE IF EXISTS {', '.join(_TABLES)} CASCADE")
            for ddl in _STUBS:
                cur.execute(ddl)
            cur.execute(f"GRANT SELECT,INSERT,UPDATE,DELETE ON {', '.join(_TABLES)} TO pearnly_app")
        # 真 enroll 代码路径(force=False)
        store.enroll_email_ingest_rls()
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            for t in _TABLES:
                cur.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                cur.execute(f"DROP TABLE IF EXISTS {', '.join(_TABLES)} CASCADE")

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(f"TRUNCATE {', '.join(_TABLES)}")

    def test_accounts_real_fn_and_isolation(self):
        self.assertTrue(self.store.upsert_email_account(UA, "a@x.com", "imap.x", 993, True, b"pw"))
        self.assertTrue(self.store.upsert_email_account(UB, "b@x.com", "imap.x", 993, True, b"pw"))
        self.assertEqual(self.store.get_email_account(UA)["email_address"], "a@x.com")
        with self.db.get_cursor_rls(user_id=UA) as cur:
            cur.execute("SELECT count(*) n FROM email_ingest_accounts")
            self.assertEqual(cur.fetchone()["n"], 1)
        with self.db.get_cursor_rls(user_id=FAKE) as cur:
            cur.execute("SELECT count(*) n FROM email_ingest_accounts")
            self.assertEqual(cur.fetchone()["n"], 0)

    def test_logs_real_fn_isolated(self):
        self.assertIsNotNone(
            self.store.insert_email_ingest_log(ACC_A, UA, {"status": "ok"}, "manual")
        )
        self.assertIsNotNone(
            self.store.insert_email_ingest_log(ACC_A, UB, {"status": "ok"}, "manual")
        )
        self.assertEqual(len(self.store.list_email_ingest_logs(UA)), 1)
        self.assertEqual(len(self.store.list_email_ingest_logs(FAKE)), 0)

    def test_seen_uids_via_parent_isolation(self):
        # seen_uids 仅 account_id → 经父账号 user 隔离。账号属 UA。
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "INSERT INTO email_ingest_accounts(id, user_id, email_address) VALUES (%s,%s,'a@x.com')",
                (ACC_A, UA),
            )
            cur.execute(
                "INSERT INTO email_ingest_seen_uids(account_id, uid) VALUES (%s,'u1')", (ACC_A,)
            )
        with self.db.get_cursor_rls(user_id=UA) as cur:
            cur.execute("SELECT count(*) n FROM email_ingest_seen_uids")
            self.assertEqual(cur.fetchone()["n"], 1)  # 父账号属 UA → 可见
        with self.db.get_cursor_rls(user_id=UB) as cur:
            cur.execute("SELECT count(*) n FROM email_ingest_seen_uids")
            self.assertEqual(cur.fetchone()["n"], 0)  # 父账号不属 UB → 不可见

    def test_with_check_blocks_other_user_account(self):
        import psycopg2

        with self.assertRaises(psycopg2.errors.Error):
            with self.db.get_cursor_rls(user_id=UA, commit=True) as cur:
                cur.execute(
                    "INSERT INTO email_ingest_accounts(user_id, email_address) VALUES (%s,'x@x.com')",
                    (UB,),
                )


if __name__ == "__main__":
    unittest.main()
