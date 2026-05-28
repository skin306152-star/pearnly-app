# -*- coding: utf-8 -*-
"""契约测试 · services/usage/store(REFACTOR-B2)"""

import unittest
from contextlib import contextmanager
from unittest import mock


class _FakeCursor:
    def __init__(self, fetch_row=None, rowcount=0, raise_on_exec=False):
        self._row = fetch_row
        self.rowcount = rowcount
        self._raise = raise_on_exec
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        if self._raise:
            raise RuntimeError("simulated DB error")

    def fetchone(self):
        return self._row

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _ctxmgr(cur):
    @contextmanager
    def _gc(commit=False):
        yield cur

    return _gc


class UsageStoreReExportTests(unittest.TestCase):
    def test_db_reexports_same_object(self):
        import db
        from services.usage import store

        for name in (
            "update_last_login",
            "increment_user_monthly_usage",
            "cleanup_expired_history",
        ):
            self.assertTrue(hasattr(store, name))
            self.assertIs(getattr(db, name), getattr(store, name))


class UpdateLastLoginTests(unittest.TestCase):
    def test_writes_last_login_at_now(self):
        from services.usage import store

        cur = _FakeCursor()
        with mock.patch.object(store.db, "get_cursor", _ctxmgr(cur)):
            store.update_last_login("u1")
        self.assertIn("UPDATE users SET last_login_at = NOW()", cur.executed[0][0])
        self.assertEqual(cur.executed[0][1], ("u1",))

    def test_db_error_silent(self):
        from services.usage import store

        cur = _FakeCursor(raise_on_exec=True)
        with mock.patch.object(store.db, "get_cursor", _ctxmgr(cur)):
            # 函数返 None · 不抛
            self.assertIsNone(store.update_last_login("u1"))


class IncrementUsageTests(unittest.TestCase):
    def test_returns_used_this_month_from_row(self):
        from services.usage import store

        cur = _FakeCursor(fetch_row={"used_this_month": 7})
        with mock.patch.object(store.db, "get_cursor", _ctxmgr(cur)):
            n = store.increment_user_monthly_usage("u1", 3)
        self.assertEqual(n, 7)
        sql, params = cur.executed[0]
        self.assertIn("CASE", sql)
        self.assertIn("last_usage_month < DATE_TRUNC", sql)
        self.assertIn("RETURNING used_this_month", sql)
        self.assertEqual(params, (3, 3, "u1"))

    def test_no_row_returns_zero(self):
        from services.usage import store

        cur = _FakeCursor(fetch_row=None)
        with mock.patch.object(store.db, "get_cursor", _ctxmgr(cur)):
            self.assertEqual(store.increment_user_monthly_usage("u1"), 0)

    def test_db_error_returns_zero(self):
        from services.usage import store

        cur = _FakeCursor(raise_on_exec=True)
        with mock.patch.object(store.db, "get_cursor", _ctxmgr(cur)):
            self.assertEqual(store.increment_user_monthly_usage("u1"), 0)


class CleanupExpiredHistoryTests(unittest.TestCase):
    def test_three_deletes_one_per_tier(self):
        from services.usage import store

        cur = _FakeCursor(rowcount=2)  # 每条 DELETE 删 2 行
        with mock.patch.object(store.db, "get_cursor", _ctxmgr(cur)):
            total = store.cleanup_expired_history(free_days=5, plus_days=30, pro_days=120)
        self.assertEqual(len(cur.executed), 3, "应跑 3 条 DELETE(free/plus/pro 三档)")
        self.assertIn("plan = 'free'", cur.executed[0][0])
        self.assertIn("plan = 'plus'", cur.executed[1][0])
        self.assertIn("plan = 'pro'", cur.executed[2][0])
        self.assertEqual(cur.executed[0][1], ("5",))
        self.assertEqual(cur.executed[1][1], ("30",))
        self.assertEqual(cur.executed[2][1], ("120",))
        self.assertEqual(total, 6)  # 2*3 = 6 行

    def test_db_error_returns_zero(self):
        from services.usage import store

        cur = _FakeCursor(raise_on_exec=True)
        with mock.patch.object(store.db, "get_cursor", _ctxmgr(cur)):
            self.assertEqual(store.cleanup_expired_history(), 0)


if __name__ == "__main__":
    unittest.main()
