# -*- coding: utf-8 -*-
"""REFACTOR-D2 · services/rd/store.py 行为/契约覆盖

补行为测试(既有 test_rd_store_contract.py 只验 re-export)。
RD 日限计数:get 返今日次数(无记录=0)· increment 返累加后值 · 异常兜底。
注意:这是 Free 套餐计数(限额逻辑非计费扣款 · 安全数据层 · 不触计费铁律)。
"""

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

if "psycopg2" not in sys.modules:
    _pg = types.ModuleType("psycopg2")
    _pg.connect = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("stub"))
    _pg.Error = Exception
    _pg.OperationalError = Exception
    _pg.extras = types.ModuleType("psycopg2.extras")
    _pg.extras.RealDictCursor = object
    _pg.extras.DictCursor = object
    _pg.extras.execute_values = lambda *a, **k: None
    _pg.extras.Json = lambda x: x
    _pg.pool = types.ModuleType("psycopg2.pool")

    class _StubPool:
        def __init__(self, *a, **k):
            pass

        def getconn(self):
            raise RuntimeError("stub")

        def putconn(self, *a, **k):
            pass

        def closeall(self):
            pass

    _pg.pool.ThreadedConnectionPool = _StubPool
    _pg.pool.SimpleConnectionPool = _StubPool
    _pg.sql = types.ModuleType("psycopg2.sql")
    _pg.sql.SQL = lambda s: s
    _pg.sql.Identifier = lambda s: s
    sys.modules["psycopg2"] = _pg
    sys.modules["psycopg2.extras"] = _pg.extras
    sys.modules["psycopg2.pool"] = _pg.pool
    sys.modules["psycopg2.sql"] = _pg.sql

from core import db  # noqa: E402
from services.rd import store  # noqa: E402


class _FakeCursor:
    def __init__(self, one_seq=None):
        self.one_seq = list(one_seq or [])
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self.one_seq.pop(0) if self.one_seq else None


class _CM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


class _ExplodingCursor:
    def execute(self, *a, **k):
        raise RuntimeError("DB outage")

    def fetchone(self):
        return None


def _patch(cur):
    return patch.object(db, "get_cursor", lambda *a, **k: _CM(cur))


class GetRdDailyUsageTests(unittest.TestCase):
    def test_returns_count_int(self):
        cur = _FakeCursor(one_seq=[{"count": 4}])
        with _patch(cur):
            n = store.get_rd_daily_usage("u1")
        self.assertEqual(n, 4)
        self.assertIn("CURRENT_DATE", cur.executed[0][0])
        self.assertEqual(cur.executed[0][1], ("u1",))

    def test_no_row_returns_zero(self):
        with _patch(_FakeCursor(one_seq=[None])):
            self.assertEqual(store.get_rd_daily_usage("u1"), 0)

    def test_string_count_coerced(self):
        with _patch(_FakeCursor(one_seq=[{"count": "9"}])):
            self.assertEqual(store.get_rd_daily_usage("u1"), 9)

    def test_exception_returns_zero(self):
        with _patch(_ExplodingCursor()):
            self.assertEqual(store.get_rd_daily_usage("u1"), 0)


class IncrementRdDailyUsageTests(unittest.TestCase):
    def test_returns_new_count(self):
        cur = _FakeCursor(one_seq=[{"count": 5}])
        with _patch(cur):
            n = store.increment_rd_daily_usage("u1")
        self.assertEqual(n, 5)
        self.assertEqual(cur.executed[0][1], ("u1", 1))

    def test_custom_increment_n(self):
        cur = _FakeCursor(one_seq=[{"count": 12}])
        with _patch(cur):
            store.increment_rd_daily_usage("u1", n=3)
        self.assertEqual(cur.executed[0][1], ("u1", 3))

    def test_no_row_returns_n_fallback(self):
        # RETURNING 没拿到行 → 返回传入的 n(乐观兜底)
        cur = _FakeCursor(one_seq=[None])
        with _patch(cur):
            n = store.increment_rd_daily_usage("u1", n=7)
        self.assertEqual(n, 7)

    def test_exception_returns_zero(self):
        with _patch(_ExplodingCursor()):
            self.assertEqual(store.increment_rd_daily_usage("u1"), 0)


if __name__ == "__main__":
    unittest.main()
