# -*- coding: utf-8 -*-
"""登录支持邮箱 + 用户名大小写不敏感:find_user_by_username 按 lower(username) 命中,
用户名查无果且含 @ 时回退按 email 查。"""

import unittest
from unittest.mock import MagicMock, patch

from services.auth import user_lookup


def _cursor_cm(cur):
    cm = MagicMock()
    cm.__enter__.return_value = cur
    cm.__exit__.return_value = False
    return cm


class _FakeUsersCursor:
    """模拟 users 表匹配语义的假游标:按实际 SQL 分支执行 lower()/精确比较。

    刻意保留「非 lower() SQL → 精确匹配」分支:源码一旦回退成 WHERE username = %s,
    大小写不敏感用例立刻红,钉死这条语义不许倒退。
    """

    def __init__(self, rows):
        self.rows = rows
        self._hit = None

    def execute(self, sql, params):
        key = params[0]
        if "lower(username)" in sql:
            self._hit = next(
                (r for r in self.rows if (r.get("username") or "").lower() == key.lower()), None
            )
        elif "lower(email)" in sql:
            self._hit = next(
                (r for r in self.rows if (r.get("email") or "").lower() == key.lower()), None
            )
        else:
            self._hit = next((r for r in self.rows if r.get("username") == key), None)

    def fetchone(self):
        return self._hit


class CaseInsensitiveUsernameTests(unittest.TestCase):
    """大小写不敏感命中(权威在后端 lower() 匹配,不依赖任何前端小写化)。

    金标:prod 超管「Earn」存的是带大写用户名且无邮箱可回退——精确匹配下任何登录门
    前端加小写化都会把它锁外面。
    """

    def _lookup(self, rows, query):
        cur = _FakeUsersCursor(rows)
        with patch.object(user_lookup.db, "get_cursor", return_value=_cursor_cm(cur)):
            return user_lookup.find_user_by_username(query)

    def test_stored_lower_input_mixed_hits(self):
        row = self._lookup([{"id": "u1", "username": "earn"}], "Earn")
        self.assertIsNotNone(row)
        self.assertEqual(row["id"], "u1")

    def test_stored_mixed_input_lower_hits(self):
        # 超管本尊场景:库里存「Earn」,输入被前端小写成「earn」也必须命中。
        row = self._lookup([{"id": "u2", "username": "Earn"}], "earn")
        self.assertIsNotNone(row)
        self.assertEqual(row["id"], "u2")

    def test_stored_mixed_input_upper_hits(self):
        row = self._lookup([{"id": "u2", "username": "Earn"}], "EARN")
        self.assertIsNotNone(row)

    def test_different_name_still_misses(self):
        self.assertIsNone(self._lookup([{"id": "u2", "username": "Earn"}], "earn2"))


class EmailLoginFallbackTests(unittest.TestCase):
    def test_email_falls_back_to_email_column(self):
        cur = MagicMock()
        cur.fetchone.side_effect = [None, {"id": "x", "email": "a@b.com"}]
        with patch.object(user_lookup.db, "get_cursor", return_value=_cursor_cm(cur)):
            row = user_lookup.find_user_by_username("a@b.com")
        self.assertEqual(row["email"], "a@b.com")
        self.assertEqual(cur.execute.call_count, 2)  # username 查 + email 回退

    def test_plain_username_no_email_query(self):
        cur = MagicMock()
        cur.fetchone.return_value = {"id": "y", "username": "pizihao"}
        with patch.object(user_lookup.db, "get_cursor", return_value=_cursor_cm(cur)):
            row = user_lookup.find_user_by_username("pizihao")
        self.assertEqual(row["username"], "pizihao")
        self.assertEqual(cur.execute.call_count, 1)  # 不含 @ 不触发 email 回退

    def test_unknown_username_without_at_not_found(self):
        cur = MagicMock()
        cur.fetchone.return_value = None
        with patch.object(user_lookup.db, "get_cursor", return_value=_cursor_cm(cur)):
            row = user_lookup.find_user_by_username("nope")
        self.assertIsNone(row)
        self.assertEqual(cur.execute.call_count, 1)
