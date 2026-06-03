# -*- coding: utf-8 -*-
"""契约测试 · services/auth/password(REFACTOR-B2)

E2E 闸:spec 13 password-change 已覆盖真实改密 + 老 token 401 闭环。本契约测试覆盖
假游标 mock 下的边界 · 异常吞 · 哈希格式调用。
"""

import unittest
from contextlib import contextmanager
from unittest import mock


class _FakeCursor:
    def __init__(self, row=None, rowcount=1, raise_on_exec=False):
        self._row = row
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


def _ctxmgr(cursor):
    @contextmanager
    def _gc(commit=False):
        yield cursor

    return _gc


class PasswordReExportTests(unittest.TestCase):
    def test_module_and_reexport_same_object(self):
        from core import db
        from services.auth import password

        for name in ("verify_user_password", "reset_user_password"):
            self.assertTrue(hasattr(password, name), f"{name} missing in module")
            self.assertIs(
                getattr(db, name),
                getattr(password, name),
                f"db.{name} re-export should be same object (防漂移)",
            )


class VerifyPasswordTests(unittest.TestCase):
    def test_no_row_returns_false(self):
        from services.auth import password

        cur = _FakeCursor(row=None)
        with mock.patch.object(password.db, "get_cursor", _ctxmgr(cur)):
            self.assertFalse(password.verify_user_password("u1", "x"))
        self.assertIn("SELECT password_hash", cur.executed[0][0])
        self.assertEqual(cur.executed[0][1], ("u1",))

    def test_db_exception_returns_false(self):
        from services.auth import password

        cur = _FakeCursor(raise_on_exec=True)
        with mock.patch.object(password.db, "get_cursor", _ctxmgr(cur)):
            self.assertFalse(password.verify_user_password("u1", "x"))

    def test_match_returns_true(self):
        from services.auth import password

        import bcrypt

        h = bcrypt.hashpw(b"correctpass", bcrypt.gensalt()).decode("utf-8")
        cur = _FakeCursor(row={"password_hash": h})
        with mock.patch.object(password.db, "get_cursor", _ctxmgr(cur)):
            self.assertTrue(password.verify_user_password("u1", "correctpass"))
            self.assertFalse(password.verify_user_password("u1", "wrongpass"))


class ResetPasswordTests(unittest.TestCase):
    def test_writes_hash_and_password_changed_at(self):
        from services.auth import password

        cur = _FakeCursor(rowcount=1)
        with mock.patch.object(password.db, "get_cursor", _ctxmgr(cur)):
            self.assertTrue(password.reset_user_password("u1", "newpassw0rd"))
        sql, params = cur.executed[0]
        self.assertIn("UPDATE users SET password_hash", sql)
        self.assertIn("password_changed_at = NOW()", sql)
        # 写入的应该是 bcrypt 哈希(以 $2 开头),不是明文
        self.assertTrue(params[0].startswith("$2"), f"应是 bcrypt 哈希 (got {params[0][:8]}...)")
        self.assertEqual(params[1], "u1")

    def test_no_rows_affected_returns_false(self):
        from services.auth import password

        cur = _FakeCursor(rowcount=0)
        with mock.patch.object(password.db, "get_cursor", _ctxmgr(cur)):
            self.assertFalse(password.reset_user_password("ghost", "x12345678"))

    def test_db_exception_returns_false(self):
        from services.auth import password

        cur = _FakeCursor(raise_on_exec=True)
        with mock.patch.object(password.db, "get_cursor", _ctxmgr(cur)):
            self.assertFalse(password.reset_user_password("u1", "x12345678"))


if __name__ == "__main__":
    unittest.main()
