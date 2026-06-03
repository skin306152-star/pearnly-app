#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_push_logs_fold.py

守门测试 · P2-B (Zihao 2026-05-27 · ERP 收尾) · `db.list_push_logs` 折叠口径的 SQL 契约.

P2-B 把推送日志列表折叠到每对 (history×endpoint) 最新一条,清「混合手动+自动推」
遗留重复行,与 list_push_exceptions 同口径(单一状态源·铁律 #12)。

本地无 DB,折叠的真实效果在生产真账号实测(STATE 记 468b50c1: 15→5 / 1182f2ae: 25→25
NULL-safe)。本测试守的是 **SQL 形状契约**——折叠子句、NULL-safe 分区、过滤作用于折叠后
当前态、user_id 永在 CTE——防后续改动把折叠/隔离/NULL 保护改丢:
  1. COUNT + 主查询都带折叠 CTE (WITH ranked AS + ROW_NUMBER() OVER)
  2. 分区 NULL-safe:两 id 都有才拼 key,否则 'solo:'||id 独立(孤儿/Xero 不被误合并)
  3. 窗口按 created_at DESC 取最新(id 作 tie-break)
  4. 过滤作用于折叠后当前态 (_rn = 1)
  5. status_filter 在折叠之后生效(_rn=1 与 status 条件共存)
  6. user_id 永在 CTE WHERE(防 cross-tenant)
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


class _MockCursor:
    """记录 execute · fetchone 返 {n: 0} · fetchall 返 [] (空结果)."""

    def __init__(self):
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, list(params) if params else []))

    def fetchone(self):
        return {"n": 0}

    def fetchall(self):
        return []


class _MockCursorCM:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc, tb):
        return False


class PushLogsFoldShapeTests(unittest.TestCase):
    """折叠口径 SQL 形状契约."""

    def _run(self, **kwargs):
        cur = _MockCursor()
        with patch.object(db, "get_cursor", lambda *a, **k: _MockCursorCM(cur)):
            r = db.list_push_logs("user-X", **kwargs)
        return cur, r

    def test_fold_cte_present_in_both_queries(self):
        """COUNT + 主查询都必须带折叠 CTE(否则只折一半 = 仍出重复行)."""
        cur, _ = self._run()
        self.assertGreaterEqual(len(cur.executed), 2)
        for sql, _ in cur.executed:
            self.assertIn("WITH ranked AS", sql, f"缺折叠 CTE: {sql[:120]}")
            self.assertIn("ROW_NUMBER() OVER", sql, f"缺 ROW_NUMBER 折叠: {sql[:120]}")

    def test_null_safe_partition(self):
        """NULL-safe:两 id 都有才拼 history|endpoint key,否则 'solo:'||id 各自独立."""
        cur, _ = self._run()
        for sql, _ in cur.executed:
            self.assertIn("l.history_id IS NOT NULL AND l.endpoint_id IS NOT NULL", sql)
            self.assertIn("'solo:'", sql, "缺孤儿行的独立分区兜底(防 Xero/孤儿被误合并)")

    def test_window_takes_latest_first(self):
        """折叠按 created_at DESC 取最新一条(id 作 tie-break 保确定性)."""
        cur, _ = self._run()
        for sql, _ in cur.executed:
            self.assertIn("ORDER BY l.created_at DESC, l.id DESC", sql)

    def test_filter_on_folded_current_state(self):
        """过滤作用于折叠后的当前态:_rn = 1 必须出现在两条 SQL."""
        cur, _ = self._run()
        for sql, _ in cur.executed:
            self.assertIn("l._rn = 1", sql, "过滤未作用于折叠后行(缺 _rn = 1)")

    def test_status_filter_applies_after_fold(self):
        """status_filter 在折叠之后生效:_rn=1 与 l.status 条件共存于折叠后当前态."""
        for sf, frag in (
            ("success", "l.status = 'success'"),
            ("failed", "l.status = 'failed' AND l.next_retry_at IS NULL"),
            ("retrying", "l.status = 'failed' AND l.next_retry_at IS NOT NULL"),
        ):
            cur, _ = self._run(status_filter=sf)
            for sql, _ in cur.executed:
                self.assertIn("l._rn = 1", sql)
                self.assertIn(frag, sql, f"status_filter={sf} 缺条件 {frag}")

    def test_user_id_always_in_cte_where(self):
        """user_id 永在 CTE WHERE 且为首个 param(防 cross-tenant · 折叠在租户内)."""
        for kwargs in ({}, {"adapter_filter": "mrerp"}, {"status_filter": "success"}):
            cur, _ = self._run(**kwargs)
            for sql, params in cur.executed:
                self.assertIn("l.user_id = %s", sql)
                self.assertTrue(params and params[0] == "user-X", f"user_id 应为首参: {params}")

    def test_empty_result_shape(self):
        """mock 空结果 → 返回 {items: [], total: 0}(结构不破)."""
        _, r = self._run()
        self.assertEqual(r, {"items": [], "total": 0})


if __name__ == "__main__":
    unittest.main()
