# -*- coding: utf-8 -*-
"""契约测试 · services/auth/user_lookup(REFACTOR-B2)

验证:
1. 7 个函数都在新模块存在
2. db.py 尾 re-export 是同一对象(防漂移)
3. 假游标 mock 验真行为(SELECT/UPDATE)
"""

import unittest
from unittest import mock


class UserLookupReExportTests(unittest.TestCase):
    """函数存在 + re-export 同一对象 · 防接线漂移"""

    NAMES = [
        "find_user_by_username",
        "find_user_by_id",
        "find_user_by_google_sub",
        "link_google_sub_to_user",
        "update_user_avatar",
        "find_user_by_line_uid",
        "link_line_uid_to_user",
    ]

    def test_functions_exist_in_service_module(self):
        from services.auth import user_lookup

        for name in self.NAMES:
            self.assertTrue(
                hasattr(user_lookup, name), f"{name} should be defined in services.auth.user_lookup"
            )
            self.assertTrue(callable(getattr(user_lookup, name)), f"{name} should be callable")

    def test_db_reexports_same_object(self):
        import db
        from services.auth import user_lookup

        for name in self.NAMES:
            self.assertIs(
                getattr(db, name),
                getattr(user_lookup, name),
                f"db.{name} should be re-exported from services.auth.user_lookup (防漂移)",
            )


class _FakeCursor:
    def __init__(self, row=None, raise_on_exec=False):
        self._row = row
        self._raise = raise_on_exec
        self.executed = []  # [(sql, params), ...]

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        if self._raise:
            raise RuntimeError("simulated DB error")

    def fetchone(self):
        return self._row

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _ctxmgr(cursor):
    """把 _FakeCursor 包成 contextmanager(get_cursor 用法是 `with` 块)"""
    from contextlib import contextmanager

    @contextmanager
    def _gc(commit=False):
        yield cursor

    return _gc


class UserLookupBehaviorTests(unittest.TestCase):
    """假游标 mock 验真行为 · 别看 source code 看实际 SQL"""

    def test_find_user_by_username_returns_dict(self):
        from services.auth import user_lookup

        cur = _FakeCursor(row={"id": "u1", "username": "alice", "email": "a@x.com"})
        with mock.patch.object(user_lookup.db, "get_cursor", _ctxmgr(cur)):
            u = user_lookup.find_user_by_username("alice")
        self.assertEqual(u["id"], "u1")
        self.assertEqual(u["username"], "alice")
        self.assertEqual(cur.executed[0][1], ("alice",))
        self.assertIn("FROM users WHERE username", cur.executed[0][0])

    def test_find_user_by_id_returns_none_when_no_row(self):
        from services.auth import user_lookup

        cur = _FakeCursor(row=None)
        with mock.patch.object(user_lookup.db, "get_cursor", _ctxmgr(cur)):
            u = user_lookup.find_user_by_id("nonexistent")
        self.assertIsNone(u)

    def test_find_user_by_id_swallows_exception_returns_none(self):
        from services.auth import user_lookup

        cur = _FakeCursor(raise_on_exec=True)
        with mock.patch.object(user_lookup.db, "get_cursor", _ctxmgr(cur)):
            u = user_lookup.find_user_by_id("x")
        self.assertIsNone(u)

    def test_find_user_by_google_sub_empty_returns_none_no_db_call(self):
        from services.auth import user_lookup

        cur = _FakeCursor()
        with mock.patch.object(user_lookup.db, "get_cursor", _ctxmgr(cur)):
            self.assertIsNone(user_lookup.find_user_by_google_sub(""))
            self.assertIsNone(user_lookup.find_user_by_google_sub(None))
        self.assertEqual(cur.executed, [])  # 不应碰 DB

    def test_link_google_sub_validates_args(self):
        from services.auth import user_lookup

        cur = _FakeCursor()
        with mock.patch.object(user_lookup.db, "get_cursor", _ctxmgr(cur)):
            self.assertFalse(user_lookup.link_google_sub_to_user("", "g123"))
            self.assertFalse(user_lookup.link_google_sub_to_user("u1", ""))
        self.assertEqual(cur.executed, [])

    def test_link_google_sub_happy_path(self):
        from services.auth import user_lookup

        cur = _FakeCursor()
        with mock.patch.object(user_lookup.db, "get_cursor", _ctxmgr(cur)):
            self.assertTrue(user_lookup.link_google_sub_to_user("u1", "g123"))
        self.assertEqual(len(cur.executed), 1)
        self.assertEqual(cur.executed[0][1], ("g123", "u1"))
        self.assertIn("UPDATE users SET google_sub", cur.executed[0][0])

    def test_update_user_avatar_validates_then_writes(self):
        from services.auth import user_lookup

        cur = _FakeCursor()
        with mock.patch.object(user_lookup.db, "get_cursor", _ctxmgr(cur)):
            self.assertFalse(user_lookup.update_user_avatar("", "http://x/y.jpg"))
            self.assertFalse(user_lookup.update_user_avatar("u1", ""))
            self.assertTrue(user_lookup.update_user_avatar("u1", "http://x/y.jpg"))
        self.assertEqual(len(cur.executed), 1)
        self.assertEqual(cur.executed[0][1], ("http://x/y.jpg", "u1"))

    def test_find_user_by_line_uid_returns_dict(self):
        from services.auth import user_lookup

        cur = _FakeCursor(row={"id": "u2", "line_uid": "L12345"})
        with mock.patch.object(user_lookup.db, "get_cursor", _ctxmgr(cur)):
            u = user_lookup.find_user_by_line_uid("L12345")
        self.assertEqual(u["id"], "u2")
        self.assertIn("WHERE line_uid", cur.executed[0][0])

    def test_link_line_uid_happy_path(self):
        from services.auth import user_lookup

        cur = _FakeCursor()
        with mock.patch.object(user_lookup.db, "get_cursor", _ctxmgr(cur)):
            self.assertTrue(user_lookup.link_line_uid_to_user("u1", "L9"))
        self.assertEqual(cur.executed[0][1], ("L9", "u1"))
        self.assertIn("UPDATE users SET line_uid", cur.executed[0][0])


if __name__ == "__main__":
    unittest.main()
