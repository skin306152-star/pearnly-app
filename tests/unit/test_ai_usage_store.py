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

    def test_attribution_columns_added_idempotently(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            store.ensure_ai_usage_table()
        sql = cur.all_sql()
        for col, typ in (("entry_point", "TEXT"), ("doc_type", "TEXT"), ("pages", "INTEGER")):
            self.assertIn(f"ADD COLUMN IF NOT EXISTS {col} {typ}", sql)

    def test_entry_index_leads_with_created_at(self):
        """前导列必须是 created_at:面板先按时间窗过滤,入口打头时范围条件落不到索引上。"""
        cur = FakeCursor()
        with patch_cursor(cur):
            store.ensure_ai_usage_table()
        sql = cur.all_sql()
        self.assertIn(
            "CREATE INDEX IF NOT EXISTS idx_ai_usage_created_entry "
            "ON ai_usage(created_at DESC, entry_point)",
            sql,
        )
        # 建反的旧索引拆掉(幂等),不留着白占写入开销
        self.assertIn("DROP INDEX IF EXISTS idx_ai_usage_entry", sql)
        self.assertNotIn("ON ai_usage(entry_point, created_at DESC)", sql)

    def test_panel_query_filters_by_the_indexed_leading_column(self):
        """索引前导列与面板 SQL 的过滤列同源 —— 两边漂了,索引就又白建。"""
        self.assertIn("WHERE created_at >= NOW()", store._COST_BY_ENTRY_SQL)
        self.assertIn("GROUP BY entry_point, doc_type", store._COST_BY_ENTRY_SQL)


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
            task="text_understand",
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
        # 系统级台账必须 bypass RLS:RLS_ROLE 强制切角色后,无租户行(网关调用/job worker)
        # 过不了 WITH CHECK,2026-08-07 起整本台账静默断流 5 天的根子就在这。
        self.assertEqual(cur.cm_kwargs[0].get("bypass"), True)
        p = cur.last_params
        self.assertEqual(p[0], "tenant-1")
        self.assertEqual(p[1], "user-1")
        self.assertEqual(p[2], "text_understand")
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

    def test_attribution_written_when_supplied(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            self._call(entry_point="bank_recon", doc_type="bank_statement", pages=18)
        self.assertIn("entry_point, doc_type, pages", cur.last_sql)
        p = cur.last_params
        self.assertEqual(p[12:], ("bank_recon", "bank_statement", 18))

    def test_attribution_defaults_to_null(self):
        # 没归因的调用点照旧能落账(旧行为不变),报表侧归「未归因」
        cur = FakeCursor()
        with patch_cursor(cur):
            self._call()
        self.assertEqual(cur.last_params[12:], (None, None, None))

    def test_zero_pages_stored_as_null(self):
        # 0 页 = 页数未知,落 NULL;落 0 会污染 cost_per_page 的分母
        cur = FakeCursor()
        with patch_cursor(cur):
            self._call(entry_point="line", pages=0)
        self.assertIsNone(cur.last_params[14])


class AggregationTests(unittest.TestCase):
    def test_get_usage_by_task_maps_rows(self):
        cur = FakeCursor(
            fetchall=[
                {
                    "task": "text_understand",
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
                    "task": "text_understand",
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


def _entry_row(**overrides):
    row = {
        "entry_point": "bank_recon",
        "doc_type": "bank_statement",
        "calls": 4,
        "pages": 18,
        "cost_thb": "39.6",
        "cost_per_page": "2.2",
        "p50_latency_ms": 1800.0,
        "models": ["gemini-3.5-flash"],
    }
    row.update(overrides)
    return row


class CostByEntryPointTests(unittest.TestCase):
    def test_sql_aggregates_in_one_query(self):
        cur = FakeCursor(fetchall=[])
        with patch_cursor(cur):
            store.get_cost_by_entry_point(days=7)
        self.assertEqual(len(cur.calls), 1, "聚合必须一条查询完成(禁 N+1)")
        sql = cur.last_sql
        self.assertIn("GROUP BY entry_point, doc_type", sql)
        self.assertIn("NULLIF(SUM(pages), 0)", sql)  # 无页数 → NULL 不除零
        self.assertIn("PERCENTILE_CONT(0.5)", sql)
        self.assertIn("ARRAY_AGG(DISTINCT model)", sql)
        self.assertIn("make_interval(days => %s)", sql)
        self.assertEqual(cur.last_params, (7,))

    def test_maps_row_shape(self):
        cur = FakeCursor(fetchall=[_entry_row()])
        with patch_cursor(cur):
            out = store.get_cost_by_entry_point(days=7)
        self.assertEqual(
            out["rows"],
            [
                {
                    "entry_point": "bank_recon",
                    "doc_type": "bank_statement",
                    "calls": 4,
                    "pages": 18,
                    "cost_thb": 39.6,
                    "cost_per_page": 2.2,  # 老板要看见的那 2.2,不再被混合均值藏住
                    "p50_latency_ms": 1800,
                    "models": ["gemini-3.5-flash"],
                }
            ],
        )
        self.assertEqual(out["days"], 7)
        self.assertTrue(out["generated_at"])

    def test_null_entry_point_rows_go_to_unattributed(self):
        cur = FakeCursor(
            fetchall=[
                _entry_row(),
                _entry_row(entry_point=None, doc_type=None, calls=9, cost_thb="1.5"),
                _entry_row(entry_point=None, doc_type=None, calls=1, cost_thb="0.25"),
            ]
        )
        with patch_cursor(cur):
            out = store.get_cost_by_entry_point()
        self.assertEqual(len(out["rows"]), 1)
        self.assertEqual(out["unattributed"], {"calls": 10, "cost_thb": 1.75})

    def test_missing_pages_and_latency_stay_none(self):
        # 「不知道几页」不是「每页 0 铢」—— 报表不许把未知渲染成 0
        cur = FakeCursor(fetchall=[_entry_row(pages=0, cost_per_page=None, p50_latency_ms=None)])
        with patch_cursor(cur):
            out = store.get_cost_by_entry_point()
        self.assertIsNone(out["rows"][0]["cost_per_page"])
        self.assertIsNone(out["rows"][0]["p50_latency_ms"])
        self.assertEqual(out["rows"][0]["pages"], 0)

    def test_exception_returns_empty_envelope(self):
        with patch_cursor_raises():
            out = store.get_cost_by_entry_point()
        self.assertEqual(out["rows"], [])
        self.assertEqual(out["unattributed"], {"calls": 0, "cost_thb": 0.0})


if __name__ == "__main__":
    unittest.main()
