# -*- coding: utf-8 -*-
"""
REFACTOR-WA 覆盖补强 · services/user_settings/store.py 行为单测(用户设置/偏好 DAL · 非高敏)

补真实行为/边界/错误分支(原仅 contract 锁结构 · 行为覆盖 ~45%):
dup_check 开关 / gemini_key(set/get/遮罩)/ preferred_lang(枚举校验)
的默认值 + 非法值拒写 + 遮罩逻辑(短/长 key)+ 异常吞咽兜底。
全部 FakeCursor mock(隔离确定 · 不打真实 DB)。
"""

import unittest
from unittest import mock

from core import db  # noqa: F401  · 先 import db 完成,避免 dal_reexports partial-init 循环
from services.user_settings import store as us


class FakeCursor:
    def __init__(self, fetchone=None, rowcount=0):
        self.calls = []
        self._fetchone = fetchone
        self.rowcount = rowcount

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._fetchone

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

    return mock.patch.object(us.db, "get_cursor", factory)


def patch_cursor_raises(exc=RuntimeError("boom")):
    def factory(*a, **k):
        raise exc

    return mock.patch.object(us.db, "get_cursor", factory)


class DupCheckTests(unittest.TestCase):
    def test_no_row_defaults_true(self):
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertTrue(us.get_user_dup_check_enabled("u1"))

    def test_null_value_defaults_true(self):
        with patch_cursor(FakeCursor(fetchone={"dup_check_enabled": None})):
            self.assertTrue(us.get_user_dup_check_enabled("u1"))

    def test_false_value(self):
        with patch_cursor(FakeCursor(fetchone={"dup_check_enabled": False})):
            self.assertFalse(us.get_user_dup_check_enabled("u1"))

    def test_exception_defaults_true(self):
        with patch_cursor_raises():
            self.assertTrue(us.get_user_dup_check_enabled("u1"))

    def test_set_success_commit_and_bool_coerce(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            self.assertTrue(us.set_user_dup_check_enabled("u1", 1))
        self.assertIn("UPDATE users SET dup_check_enabled", cur.last_sql)
        self.assertEqual(cur.last_params[0], True)  # 1 → bool True
        self.assertEqual(cur.cm_kwargs[0].get("commit"), True)

    def test_set_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(us.set_user_dup_check_enabled("u1", True))


class GeminiKeyTests(unittest.TestCase):
    def test_set_blank_stores_none(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            self.assertTrue(us.set_user_gemini_key("u1", "   "))
        self.assertIsNone(cur.last_params[0])  # blank → None (清空切回系统 key)
        self.assertEqual(cur.cm_kwargs[0].get("commit"), True)

    def test_set_value_stored(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            us.set_user_gemini_key("u1", "  AIzaKEY  ")
        self.assertEqual(cur.last_params[0], "AIzaKEY")  # trimmed

    def test_set_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(us.set_user_gemini_key("u1", "k"))

    def test_get_returns_key(self):
        with patch_cursor(FakeCursor(fetchone={"gemini_api_key": "AIzaKEY"})):
            self.assertEqual(us.get_user_gemini_key("u1"), "AIzaKEY")

    def test_get_no_row_none(self):
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertIsNone(us.get_user_gemini_key("u1"))

    def test_get_exception_none(self):
        with patch_cursor_raises():
            self.assertIsNone(us.get_user_gemini_key("u1"))

    def test_masked_no_key(self):
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertEqual(us.get_user_gemini_key_masked("u1"), {"has_key": False, "preview": ""})

    def test_masked_short_key_all_stars(self):
        with patch_cursor(FakeCursor(fetchone={"gemini_api_key": "AIza1234"})):  # 8 chars
            out = us.get_user_gemini_key_masked("u1")
        self.assertTrue(out["has_key"])
        self.assertEqual(out["preview"], "*" * 8)

    def test_masked_long_key_prefix_suffix(self):
        with patch_cursor(FakeCursor(fetchone={"gemini_api_key": "AIzaSyAbcd1234XY9Z2"})):
            out = us.get_user_gemini_key_masked("u1")
        self.assertEqual(out["preview"], "AIza...Y9Z2")  # k[:4]...k[-4:]


class PreferredLangTests(unittest.TestCase):
    def test_invalid_lang_rejected_without_db(self):
        with patch_cursor_raises():
            self.assertFalse(us.update_user_preferred_lang("u1", "fr"))

    def test_valid_lang_rowcount(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            self.assertTrue(us.update_user_preferred_lang("u1", "th"))
        self.assertIn("UPDATE users SET preferred_lang", cur.last_sql)
        self.assertEqual(cur.last_params, ("th", "u1"))
        self.assertEqual(cur.cm_kwargs[0].get("commit"), True)

    def test_valid_lang_rowcount_zero_false(self):
        cur = FakeCursor(rowcount=0)
        with patch_cursor(cur):
            self.assertFalse(us.update_user_preferred_lang("u1", "ja"))

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(us.update_user_preferred_lang("u1", "en"))


if __name__ == "__main__":
    unittest.main()
