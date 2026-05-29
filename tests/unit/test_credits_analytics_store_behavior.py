# -*- coding: utf-8 -*-
"""
REFACTOR-WA 覆盖补强 · services/credits/store.py 行为单测(credits 收入流分析 · 只读聚合 · 不动钱)

补真实行为/边界/错误分支(原仅 contract 锁结构 · 行为覆盖 ~34%):
revenue_overview(3 查:KPI/池余额/透支数)+ tenants_summary + tenant_summary + daily_trend
的返回映射 + is_overdraft/is_low_balance 边界 + days 钳制 + 空 tenant 守卫 + 异常吞咽兜底。
全部只读聚合 · FakeCursor mock(隔离确定 · 不打真实 DB · 不触发任何扣费)。
"""

import unittest
from unittest import mock

import db  # noqa: F401  · 先 import db 完成,避免 dal_reexports partial-init 循环
from services.credits import store as cr


class FakeCursor:
    def __init__(self, fetchone=None, fetchall=None, fetchone_seq=None):
        self.calls = []
        self._fetchone = fetchone
        self._fetchall = fetchall if fetchall is not None else []
        self._seq = list(fetchone_seq) if fetchone_seq is not None else None

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        if self._seq is not None:
            return self._seq.pop(0) if self._seq else None
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

    return mock.patch.object(cr.db, "get_cursor", factory)


def patch_cursor_raises(exc=RuntimeError("boom")):
    def factory(*a, **k):
        raise exc

    return mock.patch.object(cr.db, "get_cursor", factory)


class RevenueOverviewTests(unittest.TestCase):
    def test_maps_three_queries(self):
        kpi = {
            "today_usage": "5",
            "today_topup": "100",
            "month_usage": "50",
            "month_topup": "200",
            "total_usage": "500",
            "total_topup": "2000",
            "today_pages": 3,
            "month_pages": 30,
            "today_ocr_count": 2,
            "month_ocr_count": 20,
        }
        cur = FakeCursor(fetchone_seq=[kpi, {"total": "1234.5"}, {"n": 4}])
        with patch_cursor(cur):
            out = cr.get_credits_revenue_overview()
        self.assertEqual(out["today"]["usage_thb"], 5.0)
        self.assertEqual(out["month"]["topup_thb"], 200.0)
        self.assertEqual(out["total"]["usage_thb"], 500.0)
        self.assertEqual(out["pool_balance_thb"], 1234.5)
        self.assertEqual(out["overdraft_tenants"], 4)

    def test_exception_returns_default(self):
        with patch_cursor_raises():
            out = cr.get_credits_revenue_overview()
        self.assertEqual(out["pool_balance_thb"], 0)
        self.assertEqual(out["overdraft_tenants"], 0)
        self.assertEqual(out["today"], {})


class TenantsSummaryTests(unittest.TestCase):
    def test_maps_rows_and_overdraft_flags(self):
        rows = [
            {
                "tenant_id": "t1",
                "tenant_name": "ACME",
                "balance_thb": "100",
                "pages_this_month": 5,
                "month_usage_thb": "10",
                "lifetime_topup_thb": "300",
                "last_usage_at": None,
                "tenant_created_at": None,
            },
            {
                "tenant_id": "t2",
                "tenant_name": None,
                "balance_thb": "0",
                "pages_this_month": 0,
                "month_usage_thb": "0",
                "lifetime_topup_thb": "0",
                "last_usage_at": None,
                "tenant_created_at": None,
            },
            {
                "tenant_id": "t3",
                "tenant_name": "X",
                "balance_thb": "25",
                "pages_this_month": 1,
                "month_usage_thb": "1",
                "lifetime_topup_thb": "50",
                "last_usage_at": None,
                "tenant_created_at": None,
            },
        ]
        cur = FakeCursor(fetchall=rows)
        with patch_cursor(cur):
            out = cr.get_tenants_credits_summary(limit=10)
        self.assertEqual(out[0]["balance_thb"], 100.0)
        self.assertFalse(out[0]["is_overdraft"])
        self.assertFalse(out[0]["is_low_balance"])
        self.assertEqual(out[1]["tenant_name"], "(无名)")  # None→默认名
        self.assertTrue(out[1]["is_overdraft"])  # bal 0 ≤ 0
        self.assertTrue(out[2]["is_low_balance"])  # 0<25<50
        # limit 是 SQL 的最后一个参数
        self.assertEqual(cur.last_params[-1], 10)

    def test_exception_empty(self):
        with patch_cursor_raises():
            self.assertEqual(cr.get_tenants_credits_summary(), [])


class TenantSummaryTests(unittest.TestCase):
    def test_empty_tenant_returns_empty_without_db(self):
        with patch_cursor_raises():
            self.assertEqual(cr.get_tenant_credit_summary(""), {})

    def test_maps_row(self):
        row = {
            "balance_thb": "40",
            "pages_this_month": 2,
            "month_usage_thb": "8",
            "lifetime_topup_thb": "100",
            "topup_count": 3,
            "last_topup_at": None,
        }
        cur = FakeCursor(fetchone=row)
        with patch_cursor(cur):
            out = cr.get_tenant_credit_summary("t1")
        self.assertEqual(out["balance_thb"], 40.0)
        self.assertEqual(out["topup_count"], 3)
        self.assertTrue(out["is_low_balance"])  # 0<40<50

    def test_no_row_returns_empty(self):
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            self.assertEqual(cr.get_tenant_credit_summary("t1"), {})

    def test_exception_empty(self):
        with patch_cursor_raises():
            self.assertEqual(cr.get_tenant_credit_summary("t1"), {})


class DailyTrendTests(unittest.TestCase):
    def test_maps_rows_and_clamps_days(self):
        cur = FakeCursor(
            fetchall=[
                {
                    "day": "2026-05-29",
                    "usage_thb": "5",
                    "topup_thb": "10",
                    "pages": 3,
                    "ocr_count": 2,
                }
            ]
        )
        with patch_cursor(cur):
            out = cr.get_credits_daily_trend(days=9999)  # 钳到 365
        self.assertEqual(out[0]["usage_thb"], 5.0)
        self.assertIn("INTERVAL '365 days'", cur.last_sql)  # max 365

    def test_days_floor_one(self):
        cur = FakeCursor(fetchall=[])
        with patch_cursor(cur):
            cr.get_credits_daily_trend(days=0)
        self.assertIn("INTERVAL '1 days'", cur.last_sql)  # min 1

    def test_exception_empty(self):
        with patch_cursor_raises():
            self.assertEqual(cr.get_credits_daily_trend(), [])


if __name__ == "__main__":
    unittest.main()
