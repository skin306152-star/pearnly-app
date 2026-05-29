# -*- coding: utf-8 -*-
"""
REFACTOR-WA 覆盖补强 · services/cost/store.py 行为单测(成本记账 DAL · 纯只读聚合 · 不涉扣费)

补真实行为/边界/错误分支(原仅 contract 锁结构 · 行为覆盖 ~23%):
ensure_table / log_ocr_cost / get_cost_overview / get_cost_by_user / daily_trend / daily_by_engine
的 SQL 形状 + 参数(str 归一 / cost 四舍五入 / days int 防注入)+ 返回映射 + 异常吞咽兜底。
全部 FakeCursor mock(隔离确定 · 不打真实 DB · 不触发任何扣费)。
"""

import unittest
from unittest import mock

import db  # noqa: F401  · 先 import db 完成,避免 dal_reexports partial-init 循环
from services.cost import store as cost


class FakeCursor:
    def __init__(self, fetchone=None, fetchall=None):
        self.calls = []
        self._fetchone = fetchone
        self._fetchall = fetchall if fetchall is not None else []

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

    def all_sql(self):
        return " ".join(c[0] for c in self.calls)


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

    return mock.patch.object(cost.db, "get_cursor", factory)


def patch_cursor_raises(exc=RuntimeError("boom")):
    def factory(*a, **k):
        raise exc

    return mock.patch.object(cost.db, "get_cursor", factory)


class EnsureTableTests(unittest.TestCase):
    def test_creates_table_with_commit(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            cost.ensure_ocr_cost_log_table()
        self.assertIn("CREATE TABLE IF NOT EXISTS ocr_cost_log", cur.all_sql())
        self.assertEqual(cur.cm_kwargs[0].get("commit"), True)

    def test_exception_swallowed(self):
        with patch_cursor_raises():
            cost.ensure_ocr_cost_log_table()  # 不抛


class LogOcrCostTests(unittest.TestCase):
    def test_success_normalizes_params_and_rounds_cost(self):
        cur = FakeCursor(fetchone={"id": 99})
        with patch_cursor(cur):
            ok = cost.log_ocr_cost("user1234", "tenant1", 12345, "gemini", 3, 100, 50, 1.23456, 800)
        self.assertTrue(ok)
        self.assertIn("INSERT INTO ocr_cost_log", cur.last_sql)
        self.assertEqual(cur.cm_kwargs[0].get("commit"), True)
        p = cur.last_params
        self.assertEqual(p[0], "user1234")
        self.assertEqual(p[2], "12345")  # history_id int→str
        self.assertEqual(p[7], 1.2346)  # cost rounded to 4dp

    def test_none_tenant_and_history_become_none(self):
        cur = FakeCursor(fetchone={"id": 1})
        with patch_cursor(cur):
            cost.log_ocr_cost("u" * 8, None, None, "gemini", 1, 0, 0, 0.0, 0)
        p = cur.last_params
        self.assertIsNone(p[1])  # tenant None
        self.assertIsNone(p[2])  # history None

    def test_exception_returns_false(self):
        with patch_cursor_raises():
            self.assertFalse(cost.log_ocr_cost("user1234", "t", "h", "gemini", 1, 0, 0, 0.0, 0))


class OverviewTests(unittest.TestCase):
    def test_maps_kpi_and_engines(self):
        kpi = {
            "today_cost": "1.5",
            "today_pages": 2,
            "today_invoices": 1,
            "month_cost": "10",
            "month_pages": 20,
            "month_invoices": 5,
            "total_cost": "100",
            "total_pages": 200,
            "total_invoices": 50,
        }
        engines = [{"engine": "gemini", "cnt": 5, "cost": "10"}]
        cur = FakeCursor(fetchone=kpi, fetchall=engines)
        with patch_cursor(cur):
            out = cost.get_cost_overview()
        self.assertEqual(out["today"]["cost_thb"], 1.5)
        self.assertEqual(out["month"]["pages"], 20)
        self.assertEqual(out["total"]["invoices"], 50)
        self.assertEqual(out["engines"], [{"engine": "gemini", "count": 5, "cost_thb": 10.0}])

    def test_exception_returns_default(self):
        with patch_cursor_raises():
            out = cost.get_cost_overview()
        self.assertEqual(out, {"today": {}, "month": {}, "total": {}, "engines": []})


class ByUserTests(unittest.TestCase):
    def test_returns_rows_and_passes_limit(self):
        cur = FakeCursor(fetchall=[{"user_id": "u1", "month_cost": 9}])
        with patch_cursor(cur):
            out = cost.get_cost_by_user(limit=25)
        self.assertEqual(len(out), 1)
        self.assertIn("LEFT JOIN users", cur.last_sql)
        self.assertEqual(cur.last_params, (25,))

    def test_exception_empty(self):
        with patch_cursor_raises():
            self.assertEqual(cost.get_cost_by_user(), [])


class DailyTrendTests(unittest.TestCase):
    def test_maps_rows_and_int_coerces_days(self):
        cur = FakeCursor(fetchall=[{"day": "2026-05-29", "cost": "2.5", "pages": 4, "invoices": 2}])
        with patch_cursor(cur):
            out = cost.get_cost_daily_trend(days=7)
        self.assertEqual(out[0]["day"], "2026-05-29")
        self.assertEqual(out[0]["cost_thb"], 2.5)
        self.assertIn("INTERVAL '7 days'", cur.last_sql)  # int 插值防注入

    def test_exception_empty(self):
        with patch_cursor_raises():
            self.assertEqual(cost.get_cost_daily_trend(), [])


class DailyByEngineTests(unittest.TestCase):
    def test_maps_rows_with_engine(self):
        cur = FakeCursor(
            fetchall=[
                {"day": "2026-05-29", "engine": "gemini", "cost": "3", "pages": 6, "invoices": 3}
            ]
        )
        with patch_cursor(cur):
            out = cost.get_cost_daily_by_engine(days=14)
        self.assertEqual(out[0]["engine"], "gemini")
        self.assertEqual(out[0]["cost_thb"], 3.0)
        self.assertIn("INTERVAL '14 days'", cur.last_sql)

    def test_exception_empty(self):
        with patch_cursor_raises():
            self.assertEqual(cost.get_cost_daily_by_engine(), [])


if __name__ == "__main__":
    unittest.main()
