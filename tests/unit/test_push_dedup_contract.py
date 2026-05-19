#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_push_dedup_contract.py

守门测试 · 批 2 改动 2 (Zihao 2026-05-19 拍板 · v118.34.34) · 推送去重契约.

`db.has_recent_successful_push(history_id, endpoint_id, user_id)` 是
重复推送防护的核心 · 一旦它的 SQL 错(漏掉 user_id 校验 / 把 status filter
打错 / order 写反) · 会导致:
  - false negative: 重推同发票 → MR.ERP 报 ERR_DUPLICATE_INVOICE
  - false positive: 跨账号读到他人 success → 数据泄漏 + 错误跳过

这里用 mock cursor 验证 SQL shape 跟参数顺序 · 不连真 DB.

覆盖:
  1. 找到 success log 返完整 dict (id / response_body / created_at / invoice_no)
  2. 没找到返 None
  3. history_id 或 endpoint_id 缺失返 None (不查 DB)
  4. user_id 必须出现在 WHERE 子句 (防 cross-tenant 读)
  5. status = 'success' 必须出现在 SQL (其他状态 skipped_dup / failed 不算)
  6. 单 user_id ORDER BY created_at DESC + LIMIT 1
  7. DB 异常时 catch 并返 None (不抛 · 上层 push_to_endpoint 不能因此挂)
"""

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Stub psycopg2 (跟 test_user_data_error_classifier.py 一样的模式).
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
        def __init__(self, *a, **k): pass
        def getconn(self): raise RuntimeError("stub")
        def putconn(self, *a, **k): pass
        def closeall(self): pass
    fake_pg.pool.ThreadedConnectionPool = _StubPool
    fake_pg.pool.SimpleConnectionPool = _StubPool
    fake_pg.sql = types.ModuleType("psycopg2.sql")
    fake_pg.sql.SQL = lambda s: s
    fake_pg.sql.Identifier = lambda s: s
    sys.modules["psycopg2"] = fake_pg
    sys.modules["psycopg2.extras"] = fake_pg.extras
    sys.modules["psycopg2.pool"] = fake_pg.pool
    sys.modules["psycopg2.sql"] = fake_pg.sql


import db  # noqa: E402


class _MockCursor:
    """模拟一个 PG cursor · 记录 execute 调用 · 返我们 inject 的结果."""

    def __init__(self, result=None, raise_on_execute=False):
        self.result = result
        self.executed = []
        self.raise_on_execute = raise_on_execute

    def execute(self, sql, params=None):
        if self.raise_on_execute:
            raise RuntimeError("simulated DB failure")
        self.executed.append((sql, params))

    def fetchone(self):
        return self.result

    def fetchall(self):
        return [self.result] if self.result else []


class _MockCursorCM:
    """context manager 包装 _MockCursor · get_cursor() as cur: 用."""

    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc, tb):
        return False


class HasRecentSuccessfulPushPositiveTests(unittest.TestCase):
    """正向 · 命中 success log."""

    def test_returns_dict_when_success_log_found(self):
        cursor = _MockCursor(result={
            "id": "log-abc",
            "response_body": {"bill_no": "SI690519-957345"},
            "created_at": "2026-05-19T10:30:00",
            "invoice_no": "INV2026030001",
        })
        with patch.object(db, "get_cursor", lambda *a, **k: _MockCursorCM(cursor)):
            r = db.has_recent_successful_push(
                history_id="hist-1", endpoint_id="ep-1", user_id="user-1",
            )
        self.assertIsNotNone(r)
        self.assertEqual(r["id"], "log-abc")
        self.assertEqual(r["invoice_no"], "INV2026030001")

    def test_sql_contains_status_success_filter(self):
        cursor = _MockCursor(result=None)
        with patch.object(db, "get_cursor", lambda *a, **k: _MockCursorCM(cursor)):
            db.has_recent_successful_push("h", "e", "u")
        self.assertEqual(len(cursor.executed), 1)
        sql, _ = cursor.executed[0]
        self.assertIn("status = 'success'", sql,
                      "去重必须只看 success log · 其他状态(failed/skipped_dup) "
                      "不能算撞")

    def test_sql_filters_by_user_id(self):
        """user_id 必须出现在 WHERE · 否则跨账号读到他人 success log."""
        cursor = _MockCursor(result=None)
        with patch.object(db, "get_cursor", lambda *a, **k: _MockCursorCM(cursor)):
            db.has_recent_successful_push("h", "e", "user-X")
        sql, params = cursor.executed[0]
        self.assertIn("user_id = %s", sql)
        # user_id 应是 params 三元组里之一
        self.assertIn("user-X", [str(p) for p in params])

    def test_sql_filters_by_history_id_and_endpoint_id(self):
        cursor = _MockCursor(result=None)
        with patch.object(db, "get_cursor", lambda *a, **k: _MockCursorCM(cursor)):
            db.has_recent_successful_push("h-1", "e-2", "u-3")
        sql, params = cursor.executed[0]
        self.assertIn("history_id = %s", sql)
        self.assertIn("endpoint_id = %s", sql)
        self.assertEqual(set([str(p) for p in params]), {"h-1", "e-2", "u-3"})

    def test_sql_orders_by_created_at_desc_limit_1(self):
        cursor = _MockCursor(result=None)
        with patch.object(db, "get_cursor", lambda *a, **k: _MockCursorCM(cursor)):
            db.has_recent_successful_push("h", "e", "u")
        sql, _ = cursor.executed[0]
        # 必须 ORDER BY DESC · 拿最新一条 success(防长期累积里挑到旧的)
        self.assertIn("ORDER BY created_at DESC", sql)
        self.assertIn("LIMIT 1", sql)


class HasRecentSuccessfulPushNegativeTests(unittest.TestCase):
    """反向 · 不命中 / 边界."""

    def test_returns_none_when_no_success_log(self):
        cursor = _MockCursor(result=None)
        with patch.object(db, "get_cursor", lambda *a, **k: _MockCursorCM(cursor)):
            r = db.has_recent_successful_push("h", "e", "u")
        self.assertIsNone(r)

    def test_returns_none_when_history_id_missing(self):
        # 没 history_id · 直接返 None · 不查 DB
        cursor = _MockCursor(result={"id": "x"})
        with patch.object(db, "get_cursor", lambda *a, **k: _MockCursorCM(cursor)):
            r = db.has_recent_successful_push("", "e", "u")
        self.assertIsNone(r)
        self.assertEqual(len(cursor.executed), 0)

    def test_returns_none_when_endpoint_id_missing(self):
        cursor = _MockCursor(result={"id": "x"})
        with patch.object(db, "get_cursor", lambda *a, **k: _MockCursorCM(cursor)):
            r = db.has_recent_successful_push("h", None, "u")
        self.assertIsNone(r)
        self.assertEqual(len(cursor.executed), 0)

    def test_returns_none_on_db_exception_not_raises(self):
        """DB 挂了不能往上抛 · 否则 push 路由整个炸. 应吞掉返 None."""
        cursor = _MockCursor(result=None, raise_on_execute=True)
        with patch.object(db, "get_cursor", lambda *a, **k: _MockCursorCM(cursor)):
            r = db.has_recent_successful_push("h", "e", "u")
        self.assertIsNone(r)


if __name__ == "__main__":
    unittest.main()
