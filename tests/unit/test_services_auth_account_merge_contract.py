# -*- coding: utf-8 -*-
"""契约测试 · services/auth/account_merge(REFACTOR-B2)"""

import unittest
from contextlib import contextmanager
from unittest import mock


class _FakeCursor:
    def __init__(self, raise_on_exec=False, raise_on_nth=None):
        self._raise = raise_on_exec
        self._raise_on_nth = raise_on_nth
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        if self._raise:
            raise RuntimeError("simulated DB error")
        if self._raise_on_nth is not None and len(self.executed) == self._raise_on_nth:
            raise RuntimeError(f"simulated DB error at exec #{self._raise_on_nth}")

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _ctxmgr(cursor):
    @contextmanager
    def _gc(commit=False):
        yield cursor

    return _gc


class AccountMergeReExportTests(unittest.TestCase):
    def test_reexport_same_object(self):
        import db
        from services.auth import account_merge

        for name in (
            "is_line_placeholder_username",
            "update_user_email_and_username",
            "merge_line_account_into_existing",
        ):
            self.assertTrue(hasattr(account_merge, name))
            self.assertIs(
                getattr(db, name),
                getattr(account_merge, name),
                f"db.{name} re-export 应与 account_merge.{name} 同对象",
            )


class IsLinePlaceholderTests(unittest.TestCase):
    def test_true_for_line_placeholder(self):
        from services.auth.account_merge import is_line_placeholder_username

        self.assertTrue(is_line_placeholder_username("line_U12345@line.local"))
        self.assertTrue(is_line_placeholder_username("line_abc@line.local"))

    def test_false_for_real_email(self):
        from services.auth.account_merge import is_line_placeholder_username

        self.assertFalse(is_line_placeholder_username("user@gmail.com"))
        self.assertFalse(is_line_placeholder_username("line_x@example.com"))
        self.assertFalse(is_line_placeholder_username("foo@line.local"))
        self.assertFalse(is_line_placeholder_username(""))
        self.assertFalse(is_line_placeholder_username(None))


class UpdateEmailUsernameTests(unittest.TestCase):
    def test_validates_args(self):
        from services.auth import account_merge

        cur = _FakeCursor()
        with mock.patch.object(account_merge.db, "get_cursor", _ctxmgr(cur)):
            self.assertFalse(account_merge.update_user_email_and_username("", "x@y.com"))
            self.assertFalse(account_merge.update_user_email_and_username("u1", ""))
        self.assertEqual(cur.executed, [])

    def test_happy_path_writes_three_columns(self):
        from services.auth import account_merge

        cur = _FakeCursor()
        with mock.patch.object(account_merge.db, "get_cursor", _ctxmgr(cur)):
            self.assertTrue(account_merge.update_user_email_and_username("u1", "  Foo@Bar.COM  "))
        sql, params = cur.executed[0]
        self.assertIn("UPDATE users SET username", sql)
        self.assertIn("email = %s", sql)
        self.assertIn("email_normalized", sql)
        # username + email clean = 小写 + 去 strip
        self.assertEqual(params[0], "foo@bar.com")
        self.assertEqual(params[1], "foo@bar.com")
        # email_normalized 来自 auth_signup.normalize_email(或 fallback lambda)· 都是小写 strip
        self.assertEqual(params[2], "foo@bar.com")
        self.assertEqual(params[3], "u1")

    def test_db_exception_returns_false(self):
        from services.auth import account_merge

        cur = _FakeCursor(raise_on_exec=True)
        with mock.patch.object(account_merge.db, "get_cursor", _ctxmgr(cur)):
            self.assertFalse(account_merge.update_user_email_and_username("u1", "a@b.com"))


class MergeLineAccountTests(unittest.TestCase):
    def test_validates_args(self):
        from services.auth import account_merge

        cur = _FakeCursor()
        with mock.patch.object(account_merge.db, "get_cursor", _ctxmgr(cur)):
            self.assertFalse(account_merge.merge_line_account_into_existing("", "t", "L1"))
            self.assertFalse(account_merge.merge_line_account_into_existing("temp", "", "L1"))
            self.assertFalse(account_merge.merge_line_account_into_existing("temp", "t", ""))
        self.assertEqual(cur.executed, [])

    def test_happy_path_five_writes(self):
        from services.auth import account_merge

        cur = _FakeCursor()
        with mock.patch.object(account_merge.db, "get_cursor", _ctxmgr(cur)):
            self.assertTrue(
                account_merge.merge_line_account_into_existing("temp1", "target1", "L9")
            )
        # 5 步真写(临时摘 line_uid · 老账号绑 · 删临时 client · 删订阅日志 · 删临时 user)
        self.assertEqual(len(cur.executed), 5)
        # 1: UPDATE users SET line_uid = NULL ... temp
        self.assertIn("line_uid = NULL", cur.executed[0][0])
        self.assertEqual(cur.executed[0][1], ("temp1",))
        # 2: UPDATE users SET line_uid = L9 ... target
        self.assertIn("UPDATE users SET line_uid", cur.executed[1][0])
        self.assertEqual(cur.executed[1][1], ("L9", "target1"))
        # 3: DELETE FROM clients ... temp
        self.assertIn("DELETE FROM clients", cur.executed[2][0])
        # 4: DELETE FROM subscription_log ... temp
        self.assertIn("DELETE FROM subscription_log", cur.executed[3][0])
        # 5: DELETE FROM users ... temp
        self.assertIn("DELETE FROM users", cur.executed[4][0])

    def test_subscription_log_table_missing_is_swallowed(self):
        """步骤 4 失败应被 swallow · 步骤 5 继续(整体仍返 True)"""
        from services.auth import account_merge

        cur = _FakeCursor(raise_on_nth=4)
        with mock.patch.object(account_merge.db, "get_cursor", _ctxmgr(cur)):
            # 第 4 个 execute 抛错 · 但函数内部 try/except 兜底 · 步骤 5 仍跑
            # 不过当前实现:步骤 4 抛后 try 块外是 step 5,逻辑上 try 包裹的是 step 4
            # 自身,因此第 5 步会继续。整个 transaction 应仍提交 → 返 True
            ok = account_merge.merge_line_account_into_existing("temp1", "target1", "L9")
        # 由于 raise_on_nth=4 抛后 fake cursor 不接受后续 execute? 看实现:
        # try/except pass swallow 第 4 步 raise · 继续 step 5。
        # 但 _FakeCursor 抛后不影响后续 execute · 所以 step 5 会被记录
        self.assertEqual(len(cur.executed), 5)
        # 该 path 实现里 try/except 在 cur 上 · 函数应仍返 True 因为后续 step 5 成功
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
