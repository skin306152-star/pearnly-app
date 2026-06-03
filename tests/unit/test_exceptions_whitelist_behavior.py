# -*- coding: utf-8 -*-
"""
REFACTOR-WA 覆盖补强 · services/exceptions/exceptions_whitelist.py 行为单测(异常白名单 DAL · 非高敏)

补真实行为/边界/错误分支(原仅 contract 锁结构 · 行为覆盖 ~17%):
is_exception_whitelisted / add / list / delete / count 的 SQL 形状 + 参数 + 返回 +
tenant vs user 隔离两路径 + 空守卫(seller/rule 空)+ 异常吞咽兜底。
全部 FakeCursor mock(隔离确定 · 不打真实 DB)。
"""

import unittest
from unittest import mock

from core import db  # noqa: F401  · 先 import db 完成,避免 dal_reexports partial-init 循环
from services.exceptions import exceptions_whitelist as wl


class FakeCursor:
    def __init__(self, fetchone=None, fetchall=None, rowcount=0):
        self.calls = []
        self._fetchone = fetchone
        self._fetchall = fetchall if fetchall is not None else []
        self.rowcount = rowcount

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._fetchone

    def fetchall(self):
        return self._fetchall

    @property
    def last_sql(self):
        return self.calls[-1][0] if self.calls else ""

    @property
    def last_params(self):
        return self.calls[-1][1] if self.calls else None


class _CM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


def patch_cursor(cur):
    cur.cm_kwargs = []

    def factory(*a, **k):
        cur.cm_kwargs.append(k)
        return _CM(cur)

    return mock.patch.object(wl.db, "get_cursor", factory)


def patch_cursor_raises(exc=RuntimeError("boom")):
    def factory(*a, **k):
        raise exc

    return mock.patch.object(wl.db, "get_cursor", factory)


class IsWhitelistedTests(unittest.TestCase):
    def test_blank_seller_or_rule_false_without_db(self):
        with patch_cursor_raises():
            self.assertFalse(wl.is_exception_whitelisted("u1", "t1", "  ", "R"))
            self.assertFalse(wl.is_exception_whitelisted("u1", "t1", "ACME", ""))

    def test_tenant_path_hit(self):
        cur = FakeCursor(fetchone={"?column?": 1})
        with patch_cursor(cur):
            self.assertTrue(wl.is_exception_whitelisted("u1", "t1", " ACME ", "R"))
        self.assertIn("tenant_id = %s", cur.last_sql)
        self.assertIn("LOWER(seller_name) = LOWER(%s)", cur.last_sql)
        self.assertEqual(cur.last_params, ("t1", "ACME", "R"))  # seller trimmed

    def test_user_path_miss(self):
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            self.assertFalse(wl.is_exception_whitelisted("u1", None, "ACME", "R"))
        self.assertIn("user_id = %s", cur.last_sql)
        self.assertIn("tenant_id IS NULL", cur.last_sql)

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(wl.is_exception_whitelisted("u1", "t1", "ACME", "R"))


class AddTests(unittest.TestCase):
    def test_blank_false_without_db(self):
        with patch_cursor_raises():
            self.assertFalse(wl.add_exception_whitelist("u1", "t1", "", "R"))

    def test_success_inserts_with_conflict_and_commit(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            self.assertTrue(wl.add_exception_whitelist("u1", "t1", " ACME ", "R"))
        self.assertIn("INSERT INTO exception_whitelist", cur.last_sql)
        self.assertIn("ON CONFLICT DO NOTHING", cur.last_sql)
        self.assertEqual(cur.cm_kwargs[0].get("commit"), True)
        self.assertEqual(cur.last_params, ("u1", "t1", "ACME", "R"))

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(wl.add_exception_whitelist("u1", "t1", "ACME", "R"))


class ListTests(unittest.TestCase):
    def test_tenant_path_and_mapping(self):
        cur = FakeCursor(
            fetchall=[{"id": 5, "seller_name": "ACME", "rule_code": "R", "created_at": None}]
        )
        with patch_cursor(cur):
            out = wl.list_exception_whitelist("u1", tenant_id="t1")
        self.assertEqual(
            out, [{"id": 5, "seller_name": "ACME", "rule_code": "R", "created_at": None}]
        )
        self.assertIn("tenant_id = %s", cur.last_sql)
        self.assertIn("ORDER BY created_at DESC", cur.last_sql)

    def test_user_path(self):
        cur = FakeCursor(fetchall=[])
        with patch_cursor(cur):
            wl.list_exception_whitelist("u1", tenant_id=None)
        self.assertIn("user_id = %s", cur.last_sql)
        self.assertIn("tenant_id IS NULL", cur.last_sql)

    def test_exception_empty(self):
        with patch_cursor_raises():
            self.assertEqual(wl.list_exception_whitelist("u1", "t1"), [])


class DeleteTests(unittest.TestCase):
    def test_tenant_path_rowcount(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            self.assertTrue(wl.delete_exception_whitelist("u1", 5, tenant_id="t1"))
        self.assertIn("DELETE FROM exception_whitelist", cur.last_sql)
        self.assertIn("tenant_id = %s", cur.last_sql)
        self.assertEqual(cur.cm_kwargs[0].get("commit"), True)

    def test_user_path_rowcount_zero(self):
        cur = FakeCursor(rowcount=0)
        with patch_cursor(cur):
            self.assertFalse(wl.delete_exception_whitelist("u1", 5, tenant_id=None))
        self.assertIn("user_id = %s", cur.last_sql)

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(wl.delete_exception_whitelist("u1", 5, "t1"))


class CountTests(unittest.TestCase):
    def test_tenant_path_returns_n(self):
        cur = FakeCursor(fetchone={"n": 7})
        with patch_cursor(cur):
            self.assertEqual(wl.count_whitelist_rules("u1", tenant_id="t1"), 7)
        self.assertIn("COUNT(*)", cur.last_sql)
        self.assertIn("tenant_id = %s", cur.last_sql)

    def test_user_path_no_row_zero(self):
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            self.assertEqual(wl.count_whitelist_rules("u1", tenant_id=None), 0)
        self.assertIn("tenant_id IS NULL", cur.last_sql)

    def test_exception_zero(self):
        with patch_cursor_raises():
            self.assertEqual(wl.count_whitelist_rules("u1", "t1"), 0)


if __name__ == "__main__":
    unittest.main()
