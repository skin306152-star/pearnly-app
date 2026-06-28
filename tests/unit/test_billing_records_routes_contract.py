# -*- coding: utf-8 -*-
"""路由契约测试 · billing_records_routes(账单记录预览 + 导出 · 2026-06-28)

锁定:① 两条路由(URL/method)不丢 ② 已聚合进 billing_routes.router
(app.py 单一 include 不变)③ period 范围计算正确(day/month/year/all)。
取数/导出业务行为由 test_billing_export_builder + 集成守。
"""

import datetime as _dt
import unittest

from routes import billing_records_routes as rr
from routes import billing_routes


def _paths(r):
    out = set()
    for route in r.routes:
        for m in getattr(route, "methods", None) or set():
            out.add((m, route.path))
    return out


RECORDS_PATHS = {
    ("GET", "/api/credits/records"),
    ("GET", "/api/credits/billing-export"),
}


class BillingRecordsRoutesContractTests(unittest.TestCase):
    def test_submodule_has_records_paths(self):
        self.assertTrue(RECORDS_PATHS <= _paths(rr.router))

    def test_aggregated_into_billing_router(self):
        got = _paths(billing_routes.router)
        self.assertTrue(
            RECORDS_PATHS <= got, f"记录路由未聚合进 billing_routes: {RECORDS_PATHS - got}"
        )

    def test_period_all_is_unbounded(self):
        self.assertEqual(rr._period_range("all", None), (None, None))
        self.assertEqual(rr._period_range("bogus", "2026-06-28"), (None, None))

    def test_period_day(self):
        s, e = rr._period_range("day", "2026-06-28")
        self.assertEqual((s, e), (_dt.date(2026, 6, 28), _dt.date(2026, 6, 29)))

    def test_period_month_spans_whole_month(self):
        s, e = rr._period_range("month", "2026-06-15")
        self.assertEqual((s, e), (_dt.date(2026, 6, 1), _dt.date(2026, 7, 1)))

    def test_period_month_december_rolls_year(self):
        s, e = rr._period_range("month", "2026-12-09")
        self.assertEqual((s, e), (_dt.date(2026, 12, 1), _dt.date(2027, 1, 1)))

    def test_period_year(self):
        s, e = rr._period_range("year", "2026-06-28")
        self.assertEqual((s, e), (_dt.date(2026, 1, 1), _dt.date(2027, 1, 1)))

    def test_range_sql_empty_when_no_bounds(self):
        params: list = []
        self.assertEqual(rr._range_sql("created_at", None, None, params), "")
        self.assertEqual(params, [])

    def test_range_sql_appends_params(self):
        params: list = []
        sql = rr._range_sql("ct.created_at", _dt.date(2026, 6, 1), _dt.date(2026, 7, 1), params)
        self.assertIn(">=", sql)
        self.assertIn("<", sql)
        self.assertEqual(params, [_dt.date(2026, 6, 1), _dt.date(2026, 7, 1)])


if __name__ == "__main__":
    unittest.main()
