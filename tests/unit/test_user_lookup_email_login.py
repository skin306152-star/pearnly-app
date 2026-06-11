# -*- coding: utf-8 -*-
"""登录支持邮箱:find_user_by_username 在用户名查无果且含 @ 时回退按 email 查。"""

import unittest
from unittest.mock import MagicMock, patch

from services.auth import user_lookup


def _cursor_cm(cur):
    cm = MagicMock()
    cm.__enter__.return_value = cur
    cm.__exit__.return_value = False
    return cm


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
