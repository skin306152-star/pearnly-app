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
    def _gc(*a, **k):
        yield cur

    return _gc


def _clear_exempt_cache():
    from services.billing import account_status

    account_status._EXEMPT_CACHE.clear()


class AccountStatusReExportTests(unittest.TestCase):
    def test_db_reexports(self):
        from core import db
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

    def _run(self, cur, sub, user="u1", tenant="t1"):
        """跑一次查询 · 订阅侧显式给桩。

        get_active_subscription 必须自己 mock:它内部也用 db.get_cursor_rls,不 mock 就吃到
        这里的 fake cursor、拿 row 里不存在的键抛 KeyError 被它自己的 except 吞掉 → 恒返
        None。订阅分支会看着有测试其实一次没走到(2026-08-11 查出的假覆盖)。
        """
        from services.billing import account_status

        account_status._EXEMPT_CACHE[user] = (False, _time_far_future())
        with mock.patch.object(account_status.db, "get_cursor_rls", _ctxmgr(cur)):
            with mock.patch.object(account_status.db, "get_active_subscription", sub):
                return account_status.get_billing_status_combined(user, tenant)

    def test_zero_balance_returns_insufficient(self):
        cur = _FakeCursor(row={"balance_thb": 0, "pages_used": 5})
        s = self._run(cur, lambda t: None)
        self.assertFalse(s["allowed"])
        self.assertEqual(s["error_code"], "insufficient_balance")
        self.assertEqual(s["balance_thb"], 0.0)
        self.assertEqual(s["pages_used_this_month"], 5)
        self.assertIsNone(s["subscription"])

    def test_positive_balance_returns_allowed(self):
        cur = _FakeCursor(row={"balance_thb": 150.5, "pages_used": 12})
        s = self._run(cur, lambda t: None)
        self.assertTrue(s["allowed"])
        self.assertFalse(s["is_exempt"])
        self.assertAlmostEqual(s["balance_thb"], 150.5)
        self.assertEqual(s["pages_used_this_month"], 12)
        self.assertIsNone(s["error_code"])

    def test_subscription_remaining_allows_on_zero_balance(self):
        """套餐内还有额度 → 余额 0 也放行(额度免费 · 不看余额)。"""
        cur = _FakeCursor(row={"balance_thb": 0, "pages_used": 3, "sub_pages_used": 7})
        s = self._run(cur, lambda t: _sub(remaining=40))
        self.assertTrue(s["allowed"])
        self.assertIsNone(s["error_code"])
        self.assertEqual(s["subscription"]["remaining"], 40)
        # 两计数器互斥 · 读侧相加(按量 3 + 订阅本周期 7)
        self.assertEqual(s["pages_used_this_month"], 10)

    def test_subscription_exhausted_zero_balance_blocks(self):
        cur = _FakeCursor(row={"balance_thb": 0, "pages_used": 0, "sub_pages_used": 50})
        s = self._run(cur, lambda t: _sub(remaining=0))
        self.assertFalse(s["allowed"])
        self.assertEqual(s["error_code"], "insufficient_balance")
        self.assertEqual(s["subscription"]["remaining"], 0)

    def test_subscription_exhausted_with_balance_allows_overage(self):
        """额度耗尽 · 有余额 → 放行扣超额。"""
        cur = _FakeCursor(row={"balance_thb": 88.0, "pages_used": 0, "sub_pages_used": 50})
        s = self._run(cur, lambda t: _sub(remaining=0))
        self.assertTrue(s["allowed"])
        self.assertIsNone(s["error_code"])

    def test_subscription_lookup_error_falls_back_to_balance_gate(self):
        """订阅查询炸了按「无套餐」走余额闸 · 不许扩大成放行。"""

        def _boom(_tenant):
            raise RuntimeError("subscription table unreachable")

        cur = _FakeCursor(row={"balance_thb": 0, "pages_used": 1})
        s = self._run(cur, _boom)
        self.assertFalse(s["allowed"])
        self.assertEqual(s["error_code"], "insufficient_balance")

    def test_db_error_blocks_fail_closed(self):
        """钱闸 fail-closed:查不出计费状态一律不放行(DB 抖动放行 = 全站免费,不可逆)。"""
        cur = _FakeCursor(raise_on_exec=True)
        s = self._run(cur, lambda t: None)
        self.assertFalse(s["allowed"])
        self.assertFalse(s["is_exempt"])
        # 「查询失败」不许报成「用户没钱」· 两个码对应两条出路(503 重试 vs 402 充值)
        self.assertEqual(s["error_code"], "lookup_error")
        self.assertNotEqual(s["error_code"], "insufficient_balance")


def _time_far_future():
    import time as _t

    return _t.time() + 600


def _sub(*, remaining: int) -> dict:
    """get_active_subscription 的对外形状(services/billing/subscription._row_to_sub)。"""
    return {
        "plan_code": "starter",
        "status": "active",
        "quota": 50,
        "remaining": remaining,
        "pages_used_this_cycle": 50 - remaining,
    }


if __name__ == "__main__":
    unittest.main()
