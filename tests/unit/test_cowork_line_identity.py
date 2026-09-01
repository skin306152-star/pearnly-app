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
    def test_issue_binding_code_hashes_six_digits_and_invalidates_older_code(self):
        cursor = FakeCursor([active_membership(), {"expires_at": "stored"}])
        with (
            patch.object(identity_store.db, "get_cursor", cursor_context(cursor)),
            patch.object(identity_store.secrets, "randbelow", return_value=234567),
        ):
            issued = identity_store.issue_binding_code(user_id="user-1", tenant_id="tenant-1")

        self.assertEqual(issued["code"], "334567")
        insert = next(
            call for call in cursor.calls if "INSERT INTO cowork_line_connect_tokens" in call[0]
        )
        stored_hash = insert[1][2]
        self.assertEqual(stored_hash, hashlib.sha256(issued["code"].encode()).hexdigest())
        self.assertNotIn(issued["code"], repr(cursor.calls))
        self.assertTrue(any("SET used_at = NOW()" in sql for sql, _ in cursor.calls))

    def test_issue_binding_code_rejects_inactive_membership(self):
        cursor = FakeCursor([None])
        with patch.object(identity_store.db, "get_cursor", cursor_context(cursor)):
            with self.assertRaisesRegex(
                identity_store.CoworkLineIdentityError, "membership_inactive"
            ):
                identity_store.issue_binding_code(user_id="user-1", tenant_id="tenant-1")

    def test_binding_code_binds_identity_before_marking_code_used(self):
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        cursor = FakeCursor(
            [
                {
                    "id": "token-1",
                    "membership_id": "membership-1",
                    "tenant_id": "tenant-1",
                    "user_id": "user-1",
                    "expires_at": expires_at,
                },
                None,
            ]
        )
        with patch.object(identity_store.db, "get_cursor", cursor_context(cursor)):
            context = identity_store.bind_identity_with_code(
                code="123456",
                line_user_id="U-line",
                display_name="Nok",
            )

        self.assertEqual(
            context,
            {
                "membership_id": "membership-1",
                "tenant_id": "tenant-1",
                "user_id": "user-1",
            },
        )
        statements = [sql for sql, _ in cursor.calls]
        bind_index = next(
            i for i, sql in enumerate(statements) if "INSERT INTO cowork_line_identities" in sql
        )
        used_index = next(i for i, sql in enumerate(statements) if "WHERE id = %s" in sql)
        self.assertLess(bind_index, used_index)
        select_sql = cursor.calls[0][0]
        self.assertIn("m.status = 'active'", select_sql)
        self.assertIn("u.is_active = TRUE", select_sql)

    def test_binding_code_conflict_does_not_mark_code_used(self):
        cursor = FakeCursor(
            [
                {
                    "id": "token-1",
                    "membership_id": "membership-1",
                    "tenant_id": "tenant-1",
                    "user_id": "user-1",
                    "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
                },
                {"membership_id": "membership-2", "revoked_at": None},
            ]
        )
        with patch.object(identity_store.db, "get_cursor", cursor_context(cursor)):
            with self.assertRaisesRegex(identity_store.CoworkLineIdentityError, "line_conflict"):
                identity_store.bind_identity_with_code(code="123456", line_user_id="U-other")
        self.assertFalse(any("WHERE id = %s" in sql for sql, _ in cursor.calls))

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
        checked_at = datetime(2026, 8, 31, 1, tzinfo=timezone.utc)
        cursor = FakeCursor(
            [
                active_membership(),
                {
                    "display_name": "Nok",
                    "connected_at": connected_at,
                    "friendship_ready": True,
                    "friendship_checked_at": checked_at,
                },
            ]
        )
        with patch.object(identity_store.db, "get_cursor", cursor_context(cursor)):
            status = identity_store.get_identity_status(user_id="user-1", tenant_id="tenant-1")
        self.assertEqual(
            status,
            {
                "connected": True,
                "display_name": "Nok",
                "connected_at": connected_at.isoformat(),
                "friendship_ready": True,
                "friendship_checked_at": checked_at.isoformat(),
            },
        )

    def test_unfollow_revokes_identity_and_invalidates_open_codes(self):
        cursor = FakeCursor(
            [
                {
                    "membership_id": "membership-1",
                    "tenant_id": "tenant-1",
                    "user_id": "user-1",
                }
            ]
        )
        with patch.object(identity_store.db, "get_cursor", cursor_context(cursor)):
            revoked = identity_store.revoke_identity_by_line_user("U-line")

        self.assertEqual(
            revoked,
            {
                "membership_id": "membership-1",
                "tenant_id": "tenant-1",
                "user_id": "user-1",
            },
        )
        statements = [sql for sql, _ in cursor.calls]
        self.assertIn("FOR UPDATE", statements[0])
        self.assertTrue(any("friendship_ready = FALSE" in sql for sql in statements))
        self.assertTrue(any("cowork_line_connect_tokens" in sql for sql in statements))

    def test_active_identity_reconciles_expired_mrerp_reservations(self):
        cursor = FakeCursor(
            [
                {
                    "membership_id": "membership-1",
                    "tenant_id": "tenant-1",
                    "user_id": "user-1",
                }
            ]
        )
        with (
            patch.object(identity_store.db, "get_cursor", cursor_context(cursor)),
            patch(
                "services.cowork_line.push_recovery.reconcile_stale_legacy_reservations"
            ) as reconcile,
        ):
            identity = identity_store.resolve_active_identity("U-line")

        self.assertEqual(identity["line_user_id"], "U-line")
        reconcile.assert_called_once_with(identity)

    def test_binding_code_route_returns_friend_target(self):
        request = object()
        user = {"id": "user-1", "tenant_id": "tenant-1"}
        issued = {"code": "123456", "expires_at": "2026-08-31T12:00:00+00:00"}
        with (
            patch.object(routes, "get_current_user_from_request", return_value=user),
            patch.object(routes, "issue_binding_code", return_value=issued),
            patch.object(routes, "_log_op"),
        ):
            result = asyncio.run(routes.cowork_line_binding_code(request))
        self.assertEqual(result["code"], "123456")
        self.assertEqual(result["bot_basic_id"], "@pearnly")


if __name__ == "__main__":
    unittest.main()
