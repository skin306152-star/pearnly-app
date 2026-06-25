#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_buyer_to_client_resolver.py

守门测试 · 批 1 改动 1 (Zihao 2026-05-19 拍板 · v118.34.33) ·
`db.try_resolve_buyer_to_client(buyer_name, buyer_tax, user_id, tenant_id)`
按 buyer_name + buyer_tax 在 clients 表里查 Pearnly 客户 · 自动归属用.

阈值 (Zihao 拍板):
  ≥0.95 → 自动绑 + 学习
  0.80-0.95 → 抽屉标"建议归属"
  <0.80 → 标"待归属"

匹配优先级 / confidence:
  L1 buyer_to_client_memory 学习记忆       → 1.0
  L2 clients.tax_id 完全匹配 (≥10 位)       → 0.98
  L3 clients.name 完全匹配 (case-insens)   → 0.95
  L3.5 clients.short_name 完全匹配          → 0.90
  L4 clients.name substring 双向            → 0.80-0.90
  L5 clients.short_name substring           → 0.78-0.86

这条函数是 auto-resolve 的核心 · 阈值错或 confidence 算错会导致:
  - 误绑: 把发票绑到错的客户(财务结账出问题)
  - 漏绑: 该自动的没自动(用户继续手动 assign)

覆盖:
  1. 空 buyer_name 返 None (不查 DB)
  2. memory hit → confidence 1.0 (Layer 1 优先)
  3. tax_id 完全匹配 → 0.98 (Layer 2)
  4. name 完全匹配 → 0.95 (Layer 3)
  5. short_name 完全匹配 → 0.90 (Layer 3.5)
  6. name substring → 0.80-0.90 之间 (Layer 4)
  7. 没匹配返 None
  8. DB 异常返 None (不抛)
"""

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

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


class _LayeredCursor:
    """模拟 cursor · 按 execute 顺序返不同结果 (跟 5 层 SQL 一一对应).

    使用方法:
      cur = _LayeredCursor([
          {"client_id": 7, "client_name": "X Co"},  # memory hit
      ])
      # 第 1 次 execute → fetchone() 返第 1 个元素
      # 后面的 execute 都不 reach (函数 short-circuit)
    """

    def __init__(self, sequence):
        self.sequence = list(sequence)
        self.index = 0
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        if self.index < len(self.sequence):
            r = self.sequence[self.index]
            self.index += 1
            # 如果是 list (说明这是 fetchall 用的) · fetchone 返 None
            if isinstance(r, list):
                return None
            return r
        return None

    def fetchall(self):
        if self.index < len(self.sequence):
            r = self.sequence[self.index]
            self.index += 1
            if isinstance(r, list):
                return r
            return [r] if r else []
        return []


class _CursorCM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, exc_type, exc, tb):
        return False


class EmptyInputTests(unittest.TestCase):
    """空 buyer_name 直接返 None · 不查 DB."""

    def test_empty_string_returns_none(self):
        cur = _LayeredCursor([])
        with patch.object(db, "get_cursor", lambda *a, **k: _CursorCM(cur)), patch.object(db, "get_cursor_rls", lambda *a, **k: _CursorCM(cur)):
            r = db.try_resolve_buyer_to_client("", None, "user-1")
        self.assertIsNone(r)
        self.assertEqual(len(cur.executed), 0)

    def test_whitespace_only_returns_none(self):
        cur = _LayeredCursor([])
        with patch.object(db, "get_cursor", lambda *a, **k: _CursorCM(cur)), patch.object(db, "get_cursor_rls", lambda *a, **k: _CursorCM(cur)):
            r = db.try_resolve_buyer_to_client("   ", None, "user-1")
        self.assertIsNone(r)
        self.assertEqual(len(cur.executed), 0)

    def test_none_returns_none(self):
        cur = _LayeredCursor([])
        with patch.object(db, "get_cursor", lambda *a, **k: _CursorCM(cur)), patch.object(db, "get_cursor_rls", lambda *a, **k: _CursorCM(cur)):
            r = db.try_resolve_buyer_to_client(None, None, "user-1")
        self.assertIsNone(r)
        self.assertEqual(len(cur.executed), 0)


class LayerHitTests(unittest.TestCase):
    """各层命中时的 confidence 必须 = Zihao 拍板的阈值."""

    def test_layer_1_memory_hit_confidence_1_0(self):
        # 第 1 个 query (memory) 命中 → short-circuit · confidence 1.0
        cur = _LayeredCursor(
            [
                {"client_id": 7, "client_name": "บริษัท X จำกัด"},
            ]
        )
        with patch.object(db, "get_cursor", lambda *a, **k: _CursorCM(cur)), patch.object(db, "get_cursor_rls", lambda *a, **k: _CursorCM(cur)):
            r = db.try_resolve_buyer_to_client(
                "บริษัท X จำกัด",
                None,
                "user-1",
            )
        self.assertIsNotNone(r)
        self.assertEqual(r["client_id"], 7)
        self.assertEqual(r["confidence"], 1.0)
        self.assertEqual(r["match_source"], "memory")

    def test_layer_2_tax_id_hit_confidence_0_98(self):
        # memory miss(None) → tax_id hit
        cur = _LayeredCursor(
            [
                None,  # L1 memory miss
                {"id": 42, "name": "Acme Co Ltd"},  # L2 tax_id hit
            ]
        )
        with patch.object(db, "get_cursor", lambda *a, **k: _CursorCM(cur)), patch.object(db, "get_cursor_rls", lambda *a, **k: _CursorCM(cur)):
            r = db.try_resolve_buyer_to_client(
                "Different Name Here",
                "0105543123456",  # 13-digit tax → tax_clean ≥10 触发 L2
                "user-1",
            )
        self.assertIsNotNone(r)
        self.assertEqual(r["client_id"], 42)
        self.assertEqual(r["confidence"], 0.98)
        self.assertEqual(r["match_source"], "tax_id_exact")

    def test_layer_3_name_exact_hit_confidence_0_95(self):
        # L1 miss + 无 tax_id (skip L2) + L3 name exact 命中
        cur = _LayeredCursor(
            [
                None,  # L1 memory miss
                # L2 跳过 (没 tax)
                [{"id": 88, "name": "Acme Co", "short_name": None}],  # L3-5 fetchall
            ]
        )
        with patch.object(db, "get_cursor", lambda *a, **k: _CursorCM(cur)), patch.object(db, "get_cursor_rls", lambda *a, **k: _CursorCM(cur)):
            r = db.try_resolve_buyer_to_client(
                "ACME CO",  # case-insensitive 完全匹配
                None,
                "user-1",
            )
        self.assertIsNotNone(r)
        self.assertEqual(r["client_id"], 88)
        self.assertEqual(r["confidence"], 0.95)
        self.assertEqual(r["match_source"], "name_exact")

    def test_layer_3_5_short_name_exact_confidence_0_90(self):
        # L3 name exact 不命中 · L3.5 short_name exact 命中
        cur = _LayeredCursor(
            [
                None,
                [{"id": 99, "name": "Long Full Company Name Ltd", "short_name": "LFC"}],
            ]
        )
        with patch.object(db, "get_cursor", lambda *a, **k: _CursorCM(cur)), patch.object(db, "get_cursor_rls", lambda *a, **k: _CursorCM(cur)):
            r = db.try_resolve_buyer_to_client("LFC", None, "user-1")
        self.assertIsNotNone(r)
        self.assertEqual(r["client_id"], 99)
        self.assertEqual(r["confidence"], 0.90)
        self.assertEqual(r["match_source"], "short_name_exact")

    def test_layer_4_name_substring_in_range_0_80_to_0_90(self):
        # name substring 命中 · confidence 落在 0.80-0.90
        cur = _LayeredCursor(
            [
                None,
                [{"id": 11, "name": "Acme", "short_name": None}],
            ]
        )
        with patch.object(db, "get_cursor", lambda *a, **k: _CursorCM(cur)), patch.object(db, "get_cursor_rls", lambda *a, **k: _CursorCM(cur)):
            # "Acme Corporation Ltd" 含 "Acme" · 反向 substring
            r = db.try_resolve_buyer_to_client(
                "Acme Corporation Ltd",
                None,
                "user-1",
            )
        self.assertIsNotNone(r)
        self.assertEqual(r["client_id"], 11)
        # ratio = min(4, 20) / max(4, 20) = 0.20 · conf = 0.80 + 0.02 = 0.82
        self.assertGreaterEqual(r["confidence"], 0.80)
        self.assertLessEqual(r["confidence"], 0.90)
        self.assertEqual(r["match_source"], "name_substring")


class NoMatchTests(unittest.TestCase):
    """没匹配返 None."""

    def test_no_match_anywhere(self):
        cur = _LayeredCursor(
            [
                None,  # L1 memory miss
                # L2 tax 跳过
                [{"id": 1, "name": "Apple Inc", "short_name": None}],  # L3-5 rows
            ]
        )
        with patch.object(db, "get_cursor", lambda *a, **k: _CursorCM(cur)), patch.object(db, "get_cursor_rls", lambda *a, **k: _CursorCM(cur)):
            r = db.try_resolve_buyer_to_client(
                "Banana Co",  # 跟 Apple Inc 完全无关
                None,
                "user-1",
            )
        self.assertIsNone(r)

    def test_no_clients_at_all(self):
        cur = _LayeredCursor(
            [
                None,  # L1 miss
                [],  # L3-5 rows 空
            ]
        )
        with patch.object(db, "get_cursor", lambda *a, **k: _CursorCM(cur)), patch.object(db, "get_cursor_rls", lambda *a, **k: _CursorCM(cur)):
            r = db.try_resolve_buyer_to_client(
                "Whatever Co",
                None,
                "user-empty",
            )
        self.assertIsNone(r)


class DbExceptionTests(unittest.TestCase):
    """DB 异常不能往上抛 · 否则 OCR 完整 pipeline 炸."""

    def test_db_exception_returns_none(self):
        class _ExplodingCursor:
            def execute(self, *a, **k):
                raise RuntimeError("simulated DB outage")

            def fetchone(self):
                return None

            def fetchall(self):
                return []

        with patch.object(db, "get_cursor", lambda *a, **k: _CursorCM(_ExplodingCursor())), patch.object(db, "get_cursor_rls", lambda *a, **k: _CursorCM(_ExplodingCursor())):
            r = db.try_resolve_buyer_to_client("Any Co", None, "user-1")
        self.assertIsNone(r)


if __name__ == "__main__":
    unittest.main()
