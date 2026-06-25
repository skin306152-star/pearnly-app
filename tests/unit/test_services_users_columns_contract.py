# -*- coding: utf-8 -*-
"""契约测试 · services/users/columns + services/auth/email_codes_schema(REFACTOR-B2)"""

import unittest
from contextlib import contextmanager
from unittest import mock


class _FakeCursor:
    def __init__(self, raise_on_exec=False):
        self._raise = raise_on_exec
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        if self._raise:
            raise RuntimeError("simulated DB error")

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _ctxmgr(cur):
    @contextmanager
    def _gc(commit=False):
        yield cur

    return _gc


class UsersColumnsReExportTests(unittest.TestCase):
    def test_users_columns_reexport(self):
        from core import db
        from services.users import columns

        for name in (
            "ensure_google_sub_column",
            "ensure_password_changed_at_column",
            "ensure_line_uid_column",
        ):
            self.assertTrue(hasattr(columns, name))
            self.assertIs(getattr(db, name), getattr(columns, name))

    def test_email_codes_schema_reexport(self):
        from core import db
        from services.auth import email_codes_schema

        self.assertTrue(hasattr(email_codes_schema, "ensure_email_codes_table"))
        self.assertIs(db.ensure_email_codes_table, email_codes_schema.ensure_email_codes_table)


class EnsureGoogleSubColumnTests(unittest.TestCase):
    def test_adds_user_identity_columns_and_index(self):
        from services.users import columns

        cur = _FakeCursor()
        with mock.patch.object(columns.db, "get_cursor", _ctxmgr(cur)):
            self.assertTrue(columns.ensure_google_sub_column())

        sqls = [e[0] for e in cur.executed]
        self.assertTrue(any("google_sub TEXT" in s for s in sqls))
        self.assertTrue(any("idx_users_google_sub" in s for s in sqls))
        self.assertTrue(any("avatar_url TEXT" in s for s in sqls))

    def test_db_error_returns_false(self):
        from services.users import columns

        cur = _FakeCursor(raise_on_exec=True)
        with mock.patch.object(columns.db, "get_cursor", _ctxmgr(cur)):
            self.assertFalse(columns.ensure_google_sub_column())


class EnsurePasswordChangedAtColumnTests(unittest.TestCase):
    def test_adds_password_changed_at_with_default_now(self):
        from services.users import columns

        cur = _FakeCursor()
        with mock.patch.object(columns.db, "get_cursor", _ctxmgr(cur)):
            self.assertTrue(columns.ensure_password_changed_at_column())
        sql, _ = cur.executed[0]
        self.assertIn("password_changed_at TIMESTAMPTZ DEFAULT NOW()", sql)


class EnsureLineUidColumnTests(unittest.TestCase):
    def test_adds_line_uid_with_partial_index(self):
        from services.users import columns

        cur = _FakeCursor()
        with mock.patch.object(columns.db, "get_cursor", _ctxmgr(cur)):
            self.assertTrue(columns.ensure_line_uid_column())
        sqls = [e[0] for e in cur.executed]
        self.assertTrue(any("line_uid TEXT" in s for s in sqls))
        self.assertTrue(any("WHERE line_uid IS NOT NULL" in s for s in sqls))


class EnsureEmailCodesTableTests(unittest.TestCase):
    def test_creates_table_and_two_indices(self):
        from services.auth import email_codes_schema

        cur = _FakeCursor()
        with mock.patch.object(email_codes_schema.db, "get_cursor", _ctxmgr(cur)):
            self.assertTrue(email_codes_schema.ensure_email_codes_table())
        sqls = [e[0] for e in cur.executed]
        self.assertTrue(any("CREATE TABLE IF NOT EXISTS email_codes" in s for s in sqls))
        self.assertTrue(any("idx_email_codes_email" in s for s in sqls))
        self.assertTrue(any("idx_email_codes_expires" in s for s in sqls))

    def test_db_error_returns_false(self):
        from services.auth import email_codes_schema

        cur = _FakeCursor(raise_on_exec=True)
        with mock.patch.object(email_codes_schema.db, "get_cursor", _ctxmgr(cur)):
            self.assertFalse(email_codes_schema.ensure_email_codes_table())


if __name__ == "__main__":
    unittest.main()
