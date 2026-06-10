# -*- coding: utf-8 -*-
"""员工操作 DAL 行为覆盖(批5 后宿主 = services/team/console_store.py)

补行为测试(既有 test_team_store_contract.py 只验单一来源):
list_employees / remove_employee / toggle_employee_active 的安全部分
(tenant + role=member 过滤 · 级联删 · 异常兜底)。
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

from core import db  # noqa: E402  (先 import db 触发 re-export · 解循环)
from services.team import console_store as store  # noqa: E402


class _FakeCursor:
    def __init__(self, one_seq=None, all_seq=None, rowcount=0):
        self.one_seq = list(one_seq or [])
        self.all_seq = list(all_seq or [])
        self.rowcount = rowcount
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


class ListEmployeesTests(unittest.TestCase):
    def test_filters_tenant_and_member_role(self):
        cur = _FakeCursor(all_seq=[[{"id": "e1", "username": "bob", "role": "member"}]])
        with _patch(cur):
            rows = store.list_employees("t1")
        self.assertEqual(len(rows), 1)
        sql = cur.executed[0][0]
        self.assertIn("tenant_id = %s", sql)
        self.assertIn("role = 'member'", sql)
        self.assertEqual(cur.executed[0][1], ("t1",))

    def test_empty_list(self):
        with _patch(_FakeCursor(all_seq=[[]])):
            self.assertEqual(store.list_employees("t1"), [])

    def test_exception_returns_empty(self):
        with _patch(_ExplodingCursor()):
            self.assertEqual(store.list_employees("t1"), [])


class RemoveEmployeeTests(unittest.TestCase):
    def test_not_found_returns_false_no_delete(self):
        # 员工不存在/不属本 tenant/非 member → SELECT 返 None → False · 不删
        cur = _FakeCursor(one_seq=[None])
        with _patch(cur):
            ok = store.remove_employee("t1", "e1")
        self.assertFalse(ok)
        self.assertEqual(len(cur.executed), 1)  # 只执行了 SELECT 校验

    def test_safety_check_scopes_tenant_and_member(self):
        cur = _FakeCursor(one_seq=[None])
        with _patch(cur):
            store.remove_employee("t1", "e1")
        sql = cur.executed[0][0]
        self.assertIn("tenant_id = %s", sql)
        self.assertIn("role = 'member'", sql)
        self.assertEqual(cur.executed[0][1], ("e1", "t1"))

    def test_found_cascades_then_deletes_user(self):
        # SELECT 命中 → 跑级联删 + 删 users · 返 True
        cur = _FakeCursor(one_seq=[{"id": "e1"}])
        with _patch(cur):
            ok = store.remove_employee("t1", "e1")
        self.assertTrue(ok)
        # 最后一条必须是删 users
        self.assertIn("DELETE FROM users WHERE id = %s", cur.executed[-1][0])
        # 级联里应包含 ocr_history 解除
        joined = " ".join(e[0] for e in cur.executed)
        self.assertIn("DELETE FROM ocr_history", joined)

    def test_cascade_table_missing_swallowed(self):
        # 级联中某表不存在(execute 抛)被内层 try/except 吞 · 仍删 users 返 True
        class _PartialCursor(_FakeCursor):
            def execute(self, sql, params=None):
                self.executed.append((sql, params))
                if "erp_push_logs" in sql:
                    raise RuntimeError("relation does not exist")

        cur = _PartialCursor(one_seq=[{"id": "e1"}])
        with _patch(cur):
            ok = store.remove_employee("t1", "e1")
        self.assertTrue(ok)
        self.assertIn("DELETE FROM users WHERE id = %s", cur.executed[-1][0])

    def test_exception_returns_false(self):
        with _patch(_ExplodingCursor()):
            self.assertFalse(store.remove_employee("t1", "e1"))


class ToggleEmployeeActiveTests(unittest.TestCase):
    def test_scopes_tenant_member_and_sets_active(self):
        cur = _FakeCursor(rowcount=1)
        with _patch(cur):
            ok = store.toggle_employee_active("t1", "e1", False)
        self.assertTrue(ok)
        sql = cur.executed[0][0]
        self.assertIn("tenant_id = %s", sql)
        self.assertIn("role = 'member'", sql)
        self.assertEqual(cur.executed[0][1], (False, "e1", "t1"))

    def test_rowcount_zero_returns_false(self):
        with _patch(_FakeCursor(rowcount=0)):
            self.assertFalse(store.toggle_employee_active("t1", "e1", True))

    def test_exception_returns_false(self):
        with _patch(_ExplodingCursor()):
            self.assertFalse(store.toggle_employee_active("t1", "e1", True))


if __name__ == "__main__":
    unittest.main()
