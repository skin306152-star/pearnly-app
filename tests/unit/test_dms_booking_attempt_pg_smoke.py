"""PostgreSQL proves attempt ownership and stale-draft guards under real concurrency."""

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
from services.line_dms import schema, session_store, store
from tests.unit._pg_smoke import require_disposable_db


class BookingAttemptPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dsn = os.environ.get("PEARNLY_DMS_ATTEMPT_TEST_DSN", "")
        if not cls.dsn:
            raise unittest.SkipTest("explicit disposable booking attempt DSN required")
        parsed = urlsplit(cls.dsn)
        if (
            parsed.hostname not in {"localhost", "127.0.0.1"}
            or parsed.path != "/pearnly_ci_dms_attempts"
        ):
            raise RuntimeError("refusing non-disposable booking attempt database")
        cls.test_schema = "dms_attempt_test_" + uuid4().hex
        with psycopg2.connect(cls.dsn) as conn, conn.cursor() as cur:
            cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(cls.test_schema)))
        with cls.cursor(commit=True) as cur:
            cur.execute(schema._SESSIONS)

    @classmethod
    @contextmanager
    def cursor(cls, *args, commit=False, **kwargs):
        conn = psycopg2.connect(cls.dsn)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    sql.SQL("SET LOCAL search_path TO {}").format(sql.Identifier(cls.test_schema))
                )
                yield cur
                if commit:
                    conn.commit()
        finally:
            conn.close()

    @classmethod
    def tearDownClass(cls):
        with cls.cursor(commit=True) as cur:
            require_disposable_db(cur, cls.test_schema, "dms_attempt_test_")
            cur.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(cls.test_schema)))

    def setUp(self):
        self.enterContext(patch.object(db, "get_cursor_rls", self.cursor))
        self.tenant = str(uuid4())
        self.line = "attempt-" + uuid4().hex
        self.payload = {"nonce": "N", "qa": {"customer": {"id": "C"}}}
        store.set_session(self.tenant, self.line, "booking_review", self.payload)

    def _claim(self):
        claimed = store.consume_nonce(self.tenant, self.line, "booking_review", "N")
        self.assertIsNotNone(claimed)
        self.assertEqual(claimed["nonce"], "N")
        return claimed

    def test_claim_and_attempt_preserve_draft_without_rearming_confirmation(self):
        self._claim()
        self.assertTrue(
            session_store.record_booking_attempt(self.tenant, self.line, "N", "PD1", "owner")
        )
        saved = store.get_session(self.tenant, self.line)["payload"]
        self.assertEqual(saved["qa"], self.payload["qa"])
        self.assertIsNone(saved["nonce"])
        self.assertEqual(saved["_booking_claim"], "N")
        self.assertEqual(saved["booking_attempt"]["booking_no"], "PD1")
        self.assertIsNone(store.consume_nonce(self.tenant, self.line, "booking_review", "N"))

    def test_unconsumed_or_wrong_nonce_cannot_mark(self):
        self.assertFalse(
            session_store.record_booking_attempt(self.tenant, self.line, "N", "PD1", "owner")
        )
        self._claim()
        self.assertFalse(
            session_store.record_booking_attempt(self.tenant, self.line, "other", "PD1", "owner")
        )

    def test_new_draft_and_cancel_are_never_overwritten_by_late_marker(self):
        self._claim()
        store.set_session(
            self.tenant, self.line, "booking_review", {"nonce": "NEW", "qa": {"fresh": True}}
        )
        self.assertFalse(
            session_store.record_booking_attempt(self.tenant, self.line, "N", "PD1", "owner")
        )
        self.assertEqual(store.get_session(self.tenant, self.line)["payload"]["nonce"], "NEW")
        store.clear_session(self.tenant, self.line)
        self.assertFalse(
            session_store.record_booking_attempt(self.tenant, self.line, "N", "PD1", "owner")
        )
        self.assertIsNone(store.get_session(self.tenant, self.line))

    def test_only_record_owner_can_advance_an_explicitly_rejected_duplicate(self):
        self._claim()
        self.assertTrue(
            session_store.record_booking_attempt(self.tenant, self.line, "N", "PD1", "owner")
        )
        self.assertFalse(
            session_store.record_booking_attempt(self.tenant, self.line, "N", "PD2", "other", "PD1")
        )
        self.assertFalse(
            session_store.record_booking_attempt(
                self.tenant, self.line, "N", "PD2", "owner", "wrong"
            )
        )
        self.assertTrue(
            session_store.record_booking_attempt(self.tenant, self.line, "N", "PD2", "owner", "PD1")
        )

    def test_twenty_competing_executions_mark_once(self):
        self._claim()
        barrier = threading.Barrier(20)

        def attempt(index):
            barrier.wait(timeout=10)
            return session_store.record_booking_attempt(
                self.tenant, self.line, "N", "PD1", str(index)
            )

        with ThreadPoolExecutor(max_workers=20) as pool:
            outcomes = list(pool.map(attempt, range(20)))
        self.assertEqual(outcomes.count(True), 1)

    def test_old_success_cannot_clear_new_draft(self):
        self._claim()
        self.assertTrue(
            session_store.record_booking_attempt(self.tenant, self.line, "N", "PD1", "owner")
        )
        store.set_session(self.tenant, self.line, "booking_review", {"nonce": "NEW"})
        self.assertFalse(session_store.clear_booking_attempt(self.tenant, self.line, "N"))
        self.assertEqual(store.get_session(self.tenant, self.line)["payload"]["nonce"], "NEW")

    def test_completed_attempt_clears_only_its_claimed_draft(self):
        self._claim()
        self.assertTrue(
            session_store.record_booking_attempt(self.tenant, self.line, "N", "PD1", "owner")
        )
        self.assertTrue(session_store.clear_booking_attempt(self.tenant, self.line, "N"))
        self.assertIsNone(store.get_session(self.tenant, self.line))

    def test_prewrite_retry_rotates_only_its_claim_and_removes_old_claim(self):
        self._claim()
        self.assertTrue(
            session_store.replace_claimed_booking_payload(
                self.tenant,
                self.line,
                "N",
                "booking_review",
                {**self.payload, "nonce": "NEW", "_booking_claim": "N"},
                30,
            )
        )
        saved = store.get_session(self.tenant, self.line)["payload"]
        self.assertEqual(saved["nonce"], "NEW")
        self.assertNotIn("_booking_claim", saved)
        self.assertFalse(
            session_store.record_booking_attempt(self.tenant, self.line, "N", "PD1", "late")
        )

    def test_attempt_blocks_rearm_backtracking_and_discard(self):
        self._claim()
        self.assertTrue(
            session_store.record_booking_attempt(self.tenant, self.line, "N", "PD1", "owner")
        )
        for state in ("booking_review", "booking_qa", None):
            with self.subTest(state=state):
                self.assertFalse(
                    session_store.replace_claimed_booking_payload(
                        self.tenant, self.line, "N", state, {"nonce": "NEW"}
                    )
                )
        self.assertEqual(
            store.get_session(self.tenant, self.line)["payload"]["booking_attempt"]["booking_no"],
            "PD1",
        )

    def test_new_or_cancelled_draft_survives_old_prewrite_failure(self):
        self._claim()
        store.set_session(self.tenant, self.line, "booking_review", {"nonce": "NEW"})
        for state in ("booking_review", "booking_qa", None):
            self.assertFalse(
                session_store.replace_claimed_booking_payload(
                    self.tenant, self.line, "N", state, {"nonce": "OLD_RETRY"}
                )
            )
        self.assertEqual(store.get_session(self.tenant, self.line)["payload"]["nonce"], "NEW")
        store.clear_session(self.tenant, self.line)
        self.assertFalse(
            session_store.replace_claimed_booking_payload(
                self.tenant, self.line, "N", "booking_review", {"nonce": "OLD_RETRY"}
            )
        )
        self.assertIsNone(store.get_session(self.tenant, self.line))

    def test_competing_prewrite_results_transition_the_claim_only_once(self):
        self._claim()
        barrier = threading.Barrier(12)

        def rearm(index):
            barrier.wait(timeout=10)
            return session_store.replace_claimed_booking_payload(
                self.tenant, self.line, "N", "booking_review", {"nonce": str(index)}
            )

        with ThreadPoolExecutor(max_workers=12) as pool:
            outcomes = list(pool.map(rearm, range(12)))
        self.assertEqual(outcomes.count(True), 1)

    def test_missing_advisor_can_discard_only_current_unsubmitted_claim(self):
        self._claim()
        self.assertTrue(
            session_store.replace_claimed_booking_payload(self.tenant, self.line, "N", None, {})
        )
        self.assertIsNone(store.get_session(self.tenant, self.line))


if __name__ == "__main__":
    unittest.main()
