# -*- coding: utf-8 -*-
"""REFACTOR-D2 · services/archive/store.py 行为/契约覆盖

补行为测试(既有 test_archive_store_contract.py 只验 re-export)。
重点:folder_strategy 非法值兜底成 by_month_seller · get_archive_template 只取 list ·
返回结构 / None / 异常吞。
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
from services.archive import store  # noqa: E402


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
    return patch.object(db, "get_cursor_rls", lambda *a, **k: _CM(cur))


class GetArchiveSettingsTests(unittest.TestCase):
    def test_returns_dict(self):
        cur = _FakeCursor(
            one_seq=[
                {"user_id": "u1", "name_template": [{"f": "date"}], "folder_strategy": "by_month"}
            ]
        )
        with _patch(cur):
            r = store.get_archive_settings("u1")
        self.assertEqual(r["folder_strategy"], "by_month")
        self.assertEqual(cur.executed[0][1], ("u1",))

    def test_returns_none_when_unset(self):
        with _patch(_FakeCursor(one_seq=[None])):
            self.assertIsNone(store.get_archive_settings("u1"))

    def test_exception_returns_none(self):
        with _patch(_ExplodingCursor()):
            self.assertIsNone(store.get_archive_settings("u1"))


class GetArchiveTemplateTests(unittest.TestCase):
    def test_returns_template_list(self):
        cur = _FakeCursor(
            one_seq=[{"name_template": [{"f": "date"}, {"f": "seller"}], "folder_strategy": "none"}]
        )
        with _patch(cur):
            tpl = store.get_archive_template("u1")
        self.assertEqual(len(tpl), 2)

    def test_no_settings_returns_none(self):
        with _patch(_FakeCursor(one_seq=[None])):
            self.assertIsNone(store.get_archive_template("u1"))

    def test_empty_template_returns_none(self):
        cur = _FakeCursor(one_seq=[{"name_template": [], "folder_strategy": "none"}])
        with _patch(cur):
            self.assertIsNone(store.get_archive_template("u1"))

    def test_non_list_template_returns_none(self):
        cur = _FakeCursor(one_seq=[{"name_template": {"bad": 1}, "folder_strategy": "none"}])
        with _patch(cur):
            self.assertIsNone(store.get_archive_template("u1"))


class UpsertArchiveSettingsTests(unittest.TestCase):
    def test_valid_strategy_kept(self):
        cur = _FakeCursor()
        with _patch(cur):
            ok = store.upsert_archive_settings("u1", [{"f": "date"}], "by_seller")
        self.assertTrue(ok)
        self.assertEqual(cur.executed[0][1][2], "by_seller")

    def test_invalid_strategy_falls_back(self):
        cur = _FakeCursor()
        with _patch(cur):
            store.upsert_archive_settings("u1", [], "garbage_value")
        self.assertEqual(cur.executed[0][1][2], "by_month_seller")

    def test_all_valid_strategies_pass_through(self):
        for strat in ("none", "by_month", "by_seller", "by_month_seller"):
            cur = _FakeCursor()
            with _patch(cur):
                store.upsert_archive_settings("u1", [], strat)
            self.assertEqual(cur.executed[0][1][2], strat)

    def test_none_template_serialized_as_empty_list(self):
        cur = _FakeCursor()
        with _patch(cur):
            store.upsert_archive_settings("u1", None, "none")
        self.assertEqual(cur.executed[0][1][1], "[]")

    def test_exception_returns_false(self):
        with _patch(_ExplodingCursor()):
            self.assertFalse(store.upsert_archive_settings("u1", [], "none"))


if __name__ == "__main__":
    unittest.main()
