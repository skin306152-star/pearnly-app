#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_push_logs_workspace_filter.py

套账隔离守门:推送日志列表 + 今日统计按当前套账过滤(PO-4 同源 · 列在 ocr_history h 上)。

真机实锤(2026-08):切到 Sister Makeup 套账,推送日志仍列出另一套账(冰块公司)的
Express 推送——全链路没带套账维度。本测试锁 SQL 契约,防后续改动把过滤改丢:

  1. 带 workspace_client_id → COUNT 与主查询都含
     `h.workspace_client_id = %s OR h.workspace_client_id IS NULL` 且参数在正确位置;
  2. 不带(None)→ SQL 不含该子句(与现状逐字节一致 · 老调用方零改动);
  3. COUNT 查询在带过滤时补 LEFT JOIN ocr_history h(过滤列不在 l 上);
  4. 孤儿行(history_id NULL)经 LEFT JOIN 得 NULL → IS NULL 回落仍显示(老数据不一夜消失);
  5. get_push_stats_today 同口径(补 JOIN + 过滤子句 · None 不带)。

只验 SQL 拼接 + 参数,不触真库(mock get_cursor_rls)。
"""

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Stub psycopg2 (与其它 push 守门测试同款 · 本地无 DB).
if "psycopg2" not in sys.modules:
    fake_pg = types.ModuleType("psycopg2")
    fake_pg.connect = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("stub"))
    fake_pg.Error = Exception
    fake_pg.OperationalError = Exception
    fake_pg.extras = types.ModuleType("psycopg2.extras")
    fake_pg.extras.RealDictCursor = object
    fake_pg.extras.DictCursor = object
    fake_pg.extras.execute_values = lambda *a, **k: None
    fake_pg.extras.Json = lambda x: x
    fake_pg.pool = types.ModuleType("psycopg2.pool")

    class _StubPool:
        def __init__(self, *a, **k):
            pass

        def getconn(self):
            raise RuntimeError("stub")

        def putconn(self, *a, **k):
            pass

        def closeall(self):
            pass

    fake_pg.pool.ThreadedConnectionPool = _StubPool
    fake_pg.pool.SimpleConnectionPool = _StubPool
    fake_pg.sql = types.ModuleType("psycopg2.sql")
    fake_pg.sql.SQL = lambda s: s
    fake_pg.sql.Identifier = lambda s: s
    sys.modules["psycopg2"] = fake_pg
    sys.modules["psycopg2.extras"] = fake_pg.extras
    sys.modules["psycopg2.pool"] = fake_pg.pool
    sys.modules["psycopg2.sql"] = fake_pg.sql


from core import db  # noqa: E402

_WS_CLAUSE = "(h.workspace_client_id = %s OR h.workspace_client_id IS NULL)"
_WS_JOIN = "LEFT JOIN ocr_history h ON h.id = l.history_id"


class _MockCursor:
    """记录 execute · fetchone 可配(列表查询返 {n: 0} · 统计返合计 dict)."""

    def __init__(self, fetchone=None):
        self.executed = []
        self._fetchone = fetchone if fetchone is not None else {"n": 0}

    def execute(self, sql, params=None):
        self.executed.append((sql, list(params) if params else []))

    def fetchone(self):
        return self._fetchone

    def fetchall(self):
        return []


class _MockCursorCM:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc, tb):
        return False


class PushLogsWorkspaceFilterTests(unittest.TestCase):
    """list_push_logs · 套账过滤 SQL 契约."""

    def _run_list(self, **kwargs):
        cur = _MockCursor()
        with (
            patch.object(db, "get_cursor", lambda *a, **k: _MockCursorCM(cur)),
            patch.object(db, "get_cursor_rls", lambda *a, **k: _MockCursorCM(cur)),
        ):
            r = db.list_push_logs("user-X", **kwargs)
        return cur, r

    def test_with_workspace_adds_filter_to_count_and_main(self):
        cur, _ = self._run_list(workspace_client_id=7)
        self.assertGreaterEqual(len(cur.executed), 2)  # COUNT + main
        for sql, params in cur.executed:
            self.assertIn(
                _WS_CLAUSE,
                sql,
                f"套账过滤必须同时进 COUNT 和主查询(total 才诚实): {sql[:200]}",
            )
            self.assertIn(
                _WS_JOIN,
                sql,
                f"过滤列在 ocr_history h 上,必须 JOIN h: {sql[:200]}",
            )
            self.assertIn(7, [p for p in params if isinstance(p, int)])

    def test_workspace_param_follows_other_filters(self):
        # adapter_filter 先拼、套账后拼 → params 顺序 user → adapter → ws
        cur, _ = self._run_list(adapter_filter="mrerp", workspace_client_id=7)
        for sql, params in cur.executed:
            self.assertIn("LOWER(e.adapter) = LOWER(%s)", sql)
            str_params = [str(p) for p in params]
            self.assertIn("mrerp", str_params)
            self.assertIn(7, [p for p in params])
            self.assertGreater(
                [p for p in params].index(7),
                str_params.index("mrerp"),
                "workspace 参数应在 adapter 参数之后(占位符顺序一致)",
            )

    def test_without_workspace_no_filter(self):
        cur, _ = self._run_list()
        # 主查询恒有 h JOIN(取 workspace_name)· 但 COUNT 在 None 时不额外 JOIN h、
        # 两查都不拼套账 WHERE 子句(与现状逐字节一致)。
        count_sql, _ = cur.executed[0]
        self.assertNotIn(_WS_CLAUSE, count_sql, "None 时不该加套账过滤(与现状逐字节一致)")
        self.assertNotIn(_WS_JOIN, count_sql, "None 时 COUNT 不该额外 JOIN ocr_history")
        for sql, _ in cur.executed:
            self.assertNotIn("(h.workspace_client_id = %s", sql, "None 时不该拼套账 WHERE 子句")

    def test_orphan_rows_stay_visible_by_null_fallback(self):
        # 孤儿行 history_id NULL → LEFT JOIN 得 h NULL → `NULL IS NULL` 命中回落语义。
        cur, _ = self._run_list(workspace_client_id=7)
        for sql, _ in cur.executed:
            self.assertIn("IS NULL", sql, "未归属/孤儿行必须靠 IS NULL 回落保持可见")

    def test_user_id_still_first_param(self):
        cur, _ = self._run_list(workspace_client_id=7)
        for sql, params in cur.executed:
            self.assertIn("user_id = %s", sql)
            self.assertTrue(params and params[0] == "user-X", f"user_id 应为首参: {params}")


class PushStatsTodayWorkspaceFilterTests(unittest.TestCase):
    """get_push_stats_today · 今日统计同口径."""

    def _run_stats(self, **kwargs):
        cur = _MockCursor(fetchone={"total": 5, "success": 3, "failed": 2, "auto_cnt": 1})
        with patch.object(db, "get_cursor_rls", lambda *a, **k: _MockCursorCM(cur)):
            out = db.get_push_stats_today("user-X", **kwargs)
        return cur, out

    def test_with_workspace_adds_join_and_filter(self):
        cur, out = self._run_stats(workspace_client_id=7)
        self.assertEqual(out["total"], 5)
        sql, params = cur.executed[0]
        self.assertIn(_WS_JOIN, sql, "统计不走 h JOIN 则套账过滤无从谈起")
        self.assertIn(_WS_CLAUSE, sql)
        self.assertIn(7, [p for p in params if isinstance(p, int)])

    def test_without_workspace_no_filter(self):
        cur, out = self._run_stats()
        self.assertEqual(out["total"], 5)
        sql, params = cur.executed[0]
        self.assertNotIn("workspace_client_id", sql)
        self.assertNotIn(_WS_JOIN, sql)
        self.assertEqual(params, ["user-X"], "None 时只穿 user_id(参数不漂移)")


if __name__ == "__main__":
    unittest.main()
