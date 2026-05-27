# -*- coding: utf-8 -*-
"""REFACTOR-D2 · services/audit/store.py 行为/契约覆盖

补行为测试(既有 test_audit_store_contract.py 只验 re-export)。
操作日志:insert(UA 截断 / details 序列化 / 失败吞)· list(tenant 过滤 / 全局)·
list_paged(分页 clamp / 搜索 LIKE / action / 时间 / actor_is_super 过滤 / total)。
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

import db  # noqa: E402
from services.audit import store  # noqa: E402


class _FakeCursor:
    def __init__(self, one_seq=None, all_seq=None):
        self.one_seq = list(one_seq or [])
        self.all_seq = list(all_seq or [])
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self.one_seq.pop(0) if self.one_seq else None

    def fetchall(self):
        return self.all_seq.pop(0) if self.all_seq else []


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

    def fetchall(self):
        return []


def _patch(cur):
    return patch.object(db, "get_cursor", lambda *a, **k: _CM(cur))


class InsertOperationLogTests(unittest.TestCase):
    def test_returns_true_and_serializes_details(self):
        cur = _FakeCursor()
        with _patch(cur):
            ok = store.insert_operation_log("t1", "u1", "alice", False, "login", details={"k": "v"})
        self.assertTrue(ok)
        params = cur.executed[0][1]
        self.assertEqual(params[0], "t1")
        self.assertEqual(params[4], "login")
        # details 序列化为 JSON 字符串
        self.assertIn("k", params[8])

    def test_ua_truncated_to_300(self):
        cur = _FakeCursor()
        with _patch(cur):
            store.insert_operation_log(None, None, None, True, "act", ua="U" * 500)
        self.assertEqual(len(cur.executed[0][1][-1]), 300)

    def test_none_tenant_and_actor_become_none(self):
        cur = _FakeCursor()
        with _patch(cur):
            store.insert_operation_log(None, None, "sys", False, "boot")
        params = cur.executed[0][1]
        self.assertIsNone(params[0])  # tenant_id
        self.assertIsNone(params[1])  # actor_user_id

    def test_default_details_empty_object(self):
        cur = _FakeCursor()
        with _patch(cur):
            store.insert_operation_log("t1", "u1", "a", False, "x")
        self.assertEqual(cur.executed[0][1][8], "{}")

    def test_exception_returns_false(self):
        with _patch(_ExplodingCursor()):
            self.assertFalse(store.insert_operation_log("t1", "u1", "a", False, "x"))


class ListOperationLogsTests(unittest.TestCase):
    def test_tenant_filter(self):
        cur = _FakeCursor(all_seq=[[{"id": 1}]])
        with _patch(cur):
            rows = store.list_operation_logs(tenant_id="t1", limit=10)
        self.assertEqual(len(rows), 1)
        self.assertIn("WHERE tenant_id = %s", cur.executed[0][0])
        self.assertEqual(cur.executed[0][1], ("t1", 10))

    def test_global_no_where(self):
        cur = _FakeCursor(all_seq=[[]])
        with _patch(cur):
            store.list_operation_logs()
        self.assertNotIn("WHERE tenant_id", cur.executed[0][0])
        self.assertEqual(cur.executed[0][1], (200,))

    def test_exception_returns_empty(self):
        with _patch(_ExplodingCursor()):
            self.assertEqual(store.list_operation_logs(), [])


class ListOperationLogsPagedTests(unittest.TestCase):
    def test_basic_pagination_returns_total_and_rows(self):
        cur = _FakeCursor(one_seq=[{"c": 42}], all_seq=[[{"id": 1}, {"id": 2}]])
        with _patch(cur):
            res = store.list_operation_logs_paged(tenant_id="t1", page=2, per_page=25)
        self.assertEqual(res["total"], 42)
        self.assertEqual(res["page"], 2)
        self.assertEqual(res["per_page"], 25)
        self.assertEqual(len(res["rows"]), 2)
        # OFFSET = (2-1)*25 = 25
        self.assertIn(25, cur.executed[1][1])

    def test_per_page_clamped_to_500(self):
        cur = _FakeCursor(one_seq=[{"c": 0}], all_seq=[[]])
        with _patch(cur):
            res = store.list_operation_logs_paged(per_page=9999)
        self.assertEqual(res["per_page"], 500)

    def test_page_floor_one(self):
        cur = _FakeCursor(one_seq=[{"c": 0}], all_seq=[[]])
        with _patch(cur):
            res = store.list_operation_logs_paged(page=0)
        self.assertEqual(res["page"], 1)

    def test_search_q_builds_like(self):
        cur = _FakeCursor(one_seq=[{"c": 0}], all_seq=[[]])
        with _patch(cur):
            store.list_operation_logs_paged(q="Alice")
        count_sql, count_params = cur.executed[0]
        self.assertIn("LIKE %s", count_sql)
        self.assertIn("%alice%", count_params)

    def test_action_filter(self):
        cur = _FakeCursor(one_seq=[{"c": 0}], all_seq=[[]])
        with _patch(cur):
            store.list_operation_logs_paged(action="delete_user")
        self.assertIn("action = %s", cur.executed[0][0])
        self.assertIn("delete_user", cur.executed[0][1])

    def test_date_range_filters(self):
        cur = _FakeCursor(one_seq=[{"c": 0}], all_seq=[[]])
        with _patch(cur):
            store.list_operation_logs_paged(date_from="2026-01-01", date_to="2026-02-01")
        sql = cur.executed[0][0]
        self.assertIn("created_at >= %s", sql)
        self.assertIn("created_at <= %s", sql)

    def test_actor_is_super_true_filter(self):
        cur = _FakeCursor(one_seq=[{"c": 0}], all_seq=[[]])
        with _patch(cur):
            store.list_operation_logs_paged(actor_is_super=True)
        self.assertIn("COALESCE(actor_is_super, false) = true", cur.executed[0][0])

    def test_actor_is_super_false_filter(self):
        cur = _FakeCursor(one_seq=[{"c": 0}], all_seq=[[]])
        with _patch(cur):
            store.list_operation_logs_paged(actor_is_super=False)
        self.assertIn("COALESCE(actor_is_super, false) = false", cur.executed[0][0])

    def test_limit_all_skips_offset(self):
        cur = _FakeCursor(one_seq=[{"c": 5}], all_seq=[[{"id": 1}]])
        with _patch(cur):
            store.list_operation_logs_paged(limit_all=1000)
        # limit_all 路径用 LIMIT %s 无 OFFSET
        self.assertIn("LIMIT %s", cur.executed[1][0])
        self.assertNotIn("OFFSET", cur.executed[1][0])

    def test_total_from_tuple_row(self):
        # total_row 是 tuple(非 dict)时取 [0]
        cur = _FakeCursor(one_seq=[(17,)], all_seq=[[]])
        with _patch(cur):
            res = store.list_operation_logs_paged()
        self.assertEqual(res["total"], 17)

    def test_exception_returns_empty_shape(self):
        with _patch(_ExplodingCursor()):
            res = store.list_operation_logs_paged(page=3, per_page=10)
        self.assertEqual(res["rows"], [])
        self.assertEqual(res["total"], 0)
        self.assertEqual(res["page"], 3)


if __name__ == "__main__":
    unittest.main()
