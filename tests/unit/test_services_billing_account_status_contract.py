# -*- coding: utf-8 -*-
"""契约测试 · services/billing/account_status(REFACTOR-B2)"""

import unittest
from contextlib import contextmanager
from unittest import mock


class _FakeCursor:
    def __init__(self, row=None, raise_on_exec=False):
        self._row = row
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


def _clear_exempt_cache():
    from services.billing import account_status

    account_status._EXEMPT_CACHE.clear()


class AccountStatusReExportTests(unittest.TestCase):
    def test_db_reexports(self):
        import db
        from services.billing import account_status

        # 注意 _bkk_year_month 是私有 helper · 但 charge_ocr bare 调 · 必须 re-export
        for name in ("is_user_billing_exempt", "get_billing_status_combined", "_bkk_year_month"):
            self.assertTrue(hasattr(account_status, name))
            self.assertIs(getattr(db, name), getattr(account_status, name))


class BkkYearMonthTests(unittest.TestCase):
    def test_format_is_yyyy_mm(self):
        from services.billing.account_status import _bkk_year_month

        v = _bkk_year_month()
        # YYYY-MM
        self.assertRegex(v, r"^\d{4}-\d{2}$")


class IsUserBillingExemptTests(unittest.TestCase):
    def setUp(self):
        _clear_exempt_cache()

    def test_empty_user_returns_false(self):
        from services.billing import account_status

        self.assertFalse(account_status.is_user_billing_exempt(None))
        self.assertFalse(account_status.is_user_billing_exempt(""))

    def test_exempt_row_returns_true_and_caches(self):
        from services.billing import account_status

        cur = _FakeCursor(row={"x": True})
        with mock.patch.object(account_status.db, "get_cursor", _ctxmgr(cur)):
            self.assertTrue(account_status.is_user_billing_exempt("u1"))
            # 第二次调相同 key · 走 cache · 不再 execute
            self.assertTrue(account_status.is_user_billing_exempt("u1"))
        self.assertEqual(len(cur.executed), 1, "第二次应命中 cache · 不再查 DB")

    def test_non_exempt_row_returns_false(self):
        from services.billing import account_status

        cur = _FakeCursor(row={"x": False})
        with mock.patch.object(account_status.db, "get_cursor", _ctxmgr(cur)):
            self.assertFalse(account_status.is_user_billing_exempt("u2"))

    def test_no_row_returns_false(self):
        from services.billing import account_status

        cur = _FakeCursor(row=None)
        with mock.patch.object(account_status.db, "get_cursor", _ctxmgr(cur)):
            self.assertFalse(account_status.is_user_billing_exempt("u3"))

    def test_db_error_returns_false_no_cache_poison(self):
        from services.billing import account_status

        cur = _FakeCursor(raise_on_exec=True)
        with mock.patch.object(account_status.db, "get_cursor", _ctxmgr(cur)):
            self.assertFalse(account_status.is_user_billing_exempt("u4"))


class GetBillingStatusCombinedTests(unittest.TestCase):
    def setUp(self):
        _clear_exempt_cache()

    def test_exempt_user_returns_allowed_no_db_call(self):
        """白名单走 cache · 跳过 DB 查询"""
        from services.billing import account_status

        # 预填 cache: u_exempt 是 exempt
        account_status._EXEMPT_CACHE["u_exempt"] = (True, _time_far_future())
        cur = _FakeCursor()
        with mock.patch.object(account_status.db, "get_cursor", _ctxmgr(cur)):
            s = account_status.get_billing_status_combined("u_exempt", "tenant1")
        self.assertEqual(s["allowed"], True)
        self.assertEqual(s["is_exempt"], True)
        self.assertEqual(s["balance_thb"], 0.0)
        self.assertIsNone(s["error_code"])
        self.assertEqual(cur.executed, [])

    def test_no_tenant_returns_blocked(self):
        from services.billing import account_status

        cur = _FakeCursor(row={"x": False})  # is_user_billing_exempt: False
        with mock.patch.object(account_status.db, "get_cursor", _ctxmgr(cur)):
            s = account_status.get_billing_status_combined("u1", None)
        self.assertFalse(s["allowed"])
        self.assertEqual(s["error_code"], "no_tenant")

    def test_zero_balance_returns_insufficient(self):
        from services.billing import account_status

        # 复合 mock:第一次查 is_exempt 返 False · 第二次查 balance 返 (0, 0)
        # 用同一个 fake cursor · 第 2 个 execute 后 fetchone 返第 2 个 row
        # 简化:用两个 fakes 链式分别响应

        # 简化路径:cache is_exempt=False 预填 · 跳过第一次查
        account_status._EXEMPT_CACHE["u1"] = (False, _time_far_future())
        cur = _FakeCursor(row={"balance_thb": 0, "pages_used": 5})
        with mock.patch.object(account_status.db, "get_cursor", _ctxmgr(cur)):
            s = account_status.get_billing_status_combined("u1", "t1")
        self.assertFalse(s["allowed"])
        self.assertEqual(s["error_code"], "insufficient_balance")
        self.assertEqual(s["balance_thb"], 0.0)
        self.assertEqual(s["pages_used_this_month"], 5)

    def test_positive_balance_returns_allowed(self):
        from services.billing import account_status

        account_status._EXEMPT_CACHE["u1"] = (False, _time_far_future())
        cur = _FakeCursor(row={"balance_thb": 150.5, "pages_used": 12})
        with mock.patch.object(account_status.db, "get_cursor", _ctxmgr(cur)):
            s = account_status.get_billing_status_combined("u1", "t1")
        self.assertTrue(s["allowed"])
        self.assertFalse(s["is_exempt"])
        self.assertAlmostEqual(s["balance_thb"], 150.5)
        self.assertEqual(s["pages_used_this_month"], 12)
        self.assertIsNone(s["error_code"])

    def test_db_error_degrades_to_allowed_with_error_code(self):
        from services.billing import account_status

        account_status._EXEMPT_CACHE["u1"] = (False, _time_far_future())
        cur = _FakeCursor(raise_on_exec=True)
        with mock.patch.object(account_status.db, "get_cursor", _ctxmgr(cur)):
            s = account_status.get_billing_status_combined("u1", "t1")
        # 失败时不阻塞 OCR(降级允许)· 但 error_code 标 lookup_error
        self.assertTrue(s["allowed"])
        self.assertEqual(s["error_code"], "lookup_error")


def _time_far_future():
    import time as _t

    return _t.time() + 600


if __name__ == "__main__":
    unittest.main()
