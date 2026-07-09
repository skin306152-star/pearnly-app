# -*- coding: utf-8 -*-
"""services/cost/ai_usage_store.py 行为单测 · AI 网关调用成本落库(ai_usage)。

覆盖:ensure 建表含 RLS 调用 · log_ai_usage 写入 SQL 形状/参数归一 · 吞异常不抛 ·
两个聚合读函数的 SQL 形状。全部 FakeCursor mock,不摸真实 DB。
"""

import unittest

from core import db  # noqa: F401 · 先 import 完成,避免 partial-init 循环
from services.cost import ai_usage_store as store
from tests.unit._cursor_patch import patch_both


class FakeCursor:
    def __init__(self, fetchall=None):
        self.calls = []
        self._fetchall = fetchall if fetchall is not None else []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

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

    return patch_both(factory=factory)


def patch_cursor_raises(exc=RuntimeError("boom")):
    def factory(*a, **k):
        raise exc

    return patch_both(factory=factory)


class EnsureAiUsageTableTests(unittest.TestCase):
    def test_creates_table_and_applies_tenant_rls(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            store.ensure_ai_usage_table()
        sql = cur.all_sql()
        self.assertIn("CREATE TABLE IF NOT EXISTS ai_usage", sql)
        self.assertIn("ENABLE ROW LEVEL SECURITY", sql)
        self.assertIn("CREATE POLICY tenant_isolation ON ai_usage", sql)
        self.assertEqual(cur.cm_kwargs[0].get("commit"), True)


class LogAiUsageTests(unittest.TestCase):
    def setUp(self):
        # 跳过懒加载 ensure,单独测 insert 形状(ensure 已有独立测试覆盖)
        store._ensured = True

    def tearDown(self):
        store._ensured = False

    def _call(self, **overrides):
        kw = dict(
            tenant_id="tenant-1",
            user_id="user-1",
            task="line_text_understand",
            provider="fake",
            model="m",
            status="ok",
            error_kind=None,
            latency_ms=120,
            input_tokens=5,
            output_tokens=3,
            cost_thb=0.1234567,
            trace_id="tr-1",
        )
        kw.update(overrides)
        store.log_ai_usage(**kw)

    def test_inserts_expected_shape_and_rounds_cost(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            self._call()
        self.assertIn("INSERT INTO ai_usage", cur.last_sql)
        self.assertEqual(cur.cm_kwargs[0].get("commit"), True)
        p = cur.last_params
        self.assertEqual(p[0], "tenant-1")
        self.assertEqual(p[1], "user-1")
        self.assertEqual(p[2], "line_text_understand")
        self.assertEqual(p[10], 0.123457)  # cost 四舍五入到 6 位

    def test_none_tenant_and_user_pass_through_as_none(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            self._call(tenant_id=None, user_id=None)
        p = cur.last_params
        self.assertIsNone(p[0])
        self.assertIsNone(p[1])

    def test_exception_swallowed_not_raised(self):
        with patch_cursor_raises():
            self._call()  # 不抛即通过


class AggregationTests(unittest.TestCase):
    def test_get_usage_by_task_maps_rows(self):
        cur = FakeCursor(
            fetchall=[
                {
                    "task": "line_text_understand",
                    "calls": 3,
                    "cost_thb": "1.5",
                    "input_tokens": 100,
                    "output_tokens": 40,
                }
            ]
        )
        with patch_cursor(cur):
            out = store.get_usage_by_task(days=7)
        self.assertEqual(
            out,
            [
                {
                    "task": "line_text_understand",
                    "calls": 3,
                    "cost_thb": 1.5,
                    "input_tokens": 100,
                    "output_tokens": 40,
                }
            ],
        )
        self.assertIn("GROUP BY task", cur.last_sql)
        self.assertEqual(cur.last_params, (7,))

    def test_get_usage_by_task_exception_returns_empty(self):
        with patch_cursor_raises():
            self.assertEqual(store.get_usage_by_task(), [])

    def test_get_usage_daily_trend_maps_rows(self):
        cur = FakeCursor(fetchall=[{"day": "2026-07-08", "cost_thb": "2.0", "calls": 4}])
        with patch_cursor(cur):
            out = store.get_usage_daily_trend(days=30)
        self.assertEqual(out, [{"day": "2026-07-08", "cost_thb": 2.0, "calls": 4}])
        self.assertIn("GROUP BY day", cur.last_sql)

    def test_get_usage_daily_trend_exception_returns_empty(self):
        with patch_cursor_raises():
            self.assertEqual(store.get_usage_daily_trend(), [])


if __name__ == "__main__":
    unittest.main()
