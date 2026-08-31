from __future__ import annotations

import asyncio
import hashlib
import unittest
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from routes import cowork_line_binding_routes as routes
from services.cowork_line import identity_store


class FakeCursor:
    def __init__(self, rows, *, rowcount=0):
        self.rows = list(rows)
        self.rowcount = rowcount
        self.calls = []

    def execute(self, statement, params=None):
        self.calls.append((statement, params))

    def fetchone(self):
        return self.rows.pop(0)


def cursor_context(cursor):
    @contextmanager
    def _cursor(*, commit=False):
        yield cursor

    return _cursor


def active_membership():
    return {"id": "membership-1", "user_id": "user-1", "tenant_id": "tenant-1"}


class CoworkLineIdentityTests(unittest.TestCase):
    def test_issue_connect_token_hashes_raw_token_and_uses_dict_rows(self):
        cursor = FakeCursor([active_membership(), None])
        with patch.object(identity_store.db, "get_cursor", cursor_context(cursor)):
            issued = identity_store.issue_connect_token(user_id="user-1", tenant_id="tenant-1")

        self.assertTrue(issued["token"].startswith("clc_"))
        insert = next(
            call for call in cursor.calls if "INSERT INTO cowork_line_connect_tokens" in call[0]
        )
        stored_hash = insert[1][2]
        self.assertEqual(stored_hash, hashlib.sha256(issued["token"].encode()).hexdigest())
        self.assertNotIn(issued["token"], repr(cursor.calls))

    def test_issue_connect_token_rejects_inactive_membership(self):
        cursor = FakeCursor([None])
        with patch.object(identity_store.db, "get_cursor", cursor_context(cursor)):
            with self.assertRaisesRegex(
                identity_store.CoworkLineIdentityError, "membership_inactive"
            ):
                identity_store.issue_connect_token(user_id="user-1", tenant_id="tenant-1")

    def test_consume_connect_token_is_one_time_and_returns_membership_context(self):
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        cursor = FakeCursor(
            [
                {
                    "id": "token-1",
                    "membership_id": "membership-1",
                    "tenant_id": "tenant-1",
                    "user_id": "user-1",
                    "expires_at": expires_at,
                }
            ]
        )
        with patch.object(identity_store.db, "get_cursor", cursor_context(cursor)):
            context = identity_store.consume_connect_token("clc_valid")

        self.assertEqual(
            context,
            {
                "membership_id": "membership-1",
                "tenant_id": "tenant-1",
                "user_id": "user-1",
            },
        )
        self.assertTrue(any("SET used_at = NOW()" in sql for sql, _ in cursor.calls))
        select_sql = cursor.calls[0][0]
        self.assertIn("m.status = 'active'", select_sql)
        self.assertIn("u.is_active = TRUE", select_sql)

    def test_consume_expired_token_marks_it_used_and_reports_expired(self):
        cursor = FakeCursor(
            [
                {
                    "id": "token-1",
                    "membership_id": "membership-1",
                    "tenant_id": "tenant-1",
                    "user_id": "user-1",
                    "expires_at": datetime.now(timezone.utc) - timedelta(seconds=1),
                }
            ]
        )
        with patch.object(identity_store.db, "get_cursor", cursor_context(cursor)):
            with self.assertRaisesRegex(identity_store.CoworkLineIdentityError, "token_expired"):
                identity_store.consume_connect_token("clc_expired")
        self.assertTrue(any("SET used_at = NOW()" in sql for sql, _ in cursor.calls))

    def test_bind_identity_raises_line_conflict_for_another_membership(self):
        cursor = FakeCursor(
            [active_membership(), {"membership_id": "membership-2", "revoked_at": None}]
        )
        with patch.object(identity_store.db, "get_cursor", cursor_context(cursor)):
            with self.assertRaisesRegex(identity_store.CoworkLineIdentityError, "line_conflict"):
                identity_store.bind_identity(
                    membership_id="membership-1",
                    tenant_id="tenant-1",
                    user_id="user-1",
                    line_user_id="U-line",
                )

    def test_bind_identity_allows_reuse_after_previous_member_disconnected(self):
        cursor = FakeCursor(
            [
                active_membership(),
                {
                    "membership_id": "membership-2",
                    "revoked_at": datetime.now(timezone.utc),
                },
            ]
        )
        with patch.object(identity_store.db, "get_cursor", cursor_context(cursor)):
            result = identity_store.bind_identity(
                membership_id="membership-1",
                tenant_id="tenant-1",
                user_id="user-1",
                line_user_id="U-line",
            )
        self.assertTrue(result["success"])
        self.assertTrue(any("DELETE FROM cowork_line_identities" in sql for sql, _ in cursor.calls))

    def test_get_identity_status_uses_member_identity_shape(self):
        connected_at = datetime(2026, 8, 31, tzinfo=timezone.utc)
        cursor = FakeCursor(
            [active_membership(), {"display_name": "Nok", "connected_at": connected_at}]
        )
        with patch.object(identity_store.db, "get_cursor", cursor_context(cursor)):
            status = identity_store.get_identity_status(user_id="user-1", tenant_id="tenant-1")
        self.assertEqual(
            status,
            {
                "connected": True,
                "display_name": "Nok",
                "connected_at": connected_at.isoformat(),
            },
        )

    def test_connect_start_returns_oauth_bridge_url(self):
        request = object()
        user = {"id": "user-1", "tenant_id": "tenant-1"}
        issued = {"token": "clc_a+b/c", "expires_at": "2026-08-31T12:00:00+00:00"}
        with (
            patch.object(routes, "get_current_user_from_request", return_value=user),
            patch.object(routes, "issue_connect_token", return_value=issued),
            patch.object(routes, "_log_op"),
        ):
            result = asyncio.run(routes.cowork_line_connect_start(request))
        self.assertEqual(
            result,
            {"url": "/api/auth/line/start?entry=cowork&connect_token=clc_a%2Bb%2Fc"},
        )


if __name__ == "__main__":
    unittest.main()
