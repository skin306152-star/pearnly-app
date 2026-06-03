# -*- coding: utf-8 -*-
"""REFACTOR-D2 · services/notification/store.py 行为/契约覆盖

补行为测试(既有 test_notification_store_contract.py 只验 re-export)。
重点:tenant 隔离(tenant_id 给/不给走不同 WHERE)· 返回结构 · 异常吞 ·
update 的部分字段拼 SQL · delete 先 SET NULL logs.rule_id。
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
from services.notification import store  # noqa: E402


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


class ListNotificationRulesTests(unittest.TestCase):
    def test_tenant_scope_uses_tenant_where(self):
        cur = _FakeCursor(all_seq=[[{"id": 1}]])
        with _patch(cur):
            rows = store.list_notification_rules("u1", tenant_id="t1")
        self.assertEqual(len(rows), 1)
        self.assertIn("WHERE tenant_id = %s", cur.executed[0][0])
        self.assertEqual(cur.executed[0][1], ("t1",))

    def test_user_scope_isolates_null_tenant(self):
        cur = _FakeCursor(all_seq=[[]])
        with _patch(cur):
            store.list_notification_rules("u1")
        self.assertIn("tenant_id IS NULL", cur.executed[0][0])
        self.assertEqual(cur.executed[0][1], ("u1",))

    def test_exception_returns_empty(self):
        with _patch(_ExplodingCursor()):
            self.assertEqual(store.list_notification_rules("u1"), [])


class GetNotificationRuleTests(unittest.TestCase):
    def test_tenant_scope(self):
        cur = _FakeCursor(one_seq=[{"id": 5, "tenant_id": "t1"}])
        with _patch(cur):
            r = store.get_notification_rule(5, "u1", tenant_id="t1")
        self.assertEqual(r["id"], 5)
        self.assertEqual(cur.executed[0][1], (5, "t1"))

    def test_user_scope_rejects_other(self):
        with _patch(_FakeCursor(one_seq=[None])):
            self.assertIsNone(store.get_notification_rule(5, "u1"))

    def test_exception_returns_none(self):
        with _patch(_ExplodingCursor()):
            self.assertIsNone(store.get_notification_rule(5, "u1"))


class CreateNotificationRuleTests(unittest.TestCase):
    def test_returns_int_id_and_strips_name(self):
        cur = _FakeCursor(one_seq=[{"id": 99}])
        with _patch(cur):
            rid = store.create_notification_rule("u1", None, "  My Rule  ", "tpl", {"k": 1})
        self.assertEqual(rid, 99)
        self.assertEqual(cur.executed[0][1][2], "My Rule")  # stripped name

    def test_default_params_empty_json(self):
        cur = _FakeCursor(one_seq=[{"id": 1}])
        with _patch(cur):
            store.create_notification_rule("u1", None, "r", "tpl")
        # params 序列化 · 第 5 个参数
        self.assertEqual(cur.executed[0][1][4], "{}")

    def test_exception_returns_none(self):
        with _patch(_ExplodingCursor()):
            self.assertIsNone(store.create_notification_rule("u1", None, "r", "tpl"))


class UpdateNotificationRuleTests(unittest.TestCase):
    def test_no_fields_returns_true_without_db(self):
        cur = _FakeCursor()
        with _patch(cur):
            ok = store.update_notification_rule(1, "u1", None)
        self.assertTrue(ok)
        self.assertEqual(len(cur.executed), 0)  # 没字段 → 不查 DB

    def test_partial_update_builds_set_clause(self):
        cur = _FakeCursor(rowcount=1)
        with _patch(cur):
            ok = store.update_notification_rule(1, "u1", None, name="New", enabled=False)
        self.assertTrue(ok)
        sql = cur.executed[0][0]
        self.assertIn("name = %s", sql)
        self.assertIn("enabled = %s", sql)
        self.assertIn("updated_at = NOW()", sql)

    def test_tenant_scope_where(self):
        cur = _FakeCursor(rowcount=1)
        with _patch(cur):
            store.update_notification_rule(1, "u1", "t1", enabled=True)
        self.assertIn("tenant_id = %s", cur.executed[0][0])

    def test_rowcount_zero_returns_false(self):
        with _patch(_FakeCursor(rowcount=0)):
            self.assertFalse(store.update_notification_rule(1, "u1", None, name="x"))

    def test_exception_returns_false(self):
        with _patch(_ExplodingCursor()):
            self.assertFalse(store.update_notification_rule(1, "u1", None, name="x"))


class DeleteNotificationRuleTests(unittest.TestCase):
    def test_nulls_logs_then_deletes_rule(self):
        cur = _FakeCursor(rowcount=1)
        with _patch(cur):
            ok = store.delete_notification_rule(7, "u1", None)
        self.assertTrue(ok)
        # 第 1 条:SET rule_id NULL on logs ; 第 2 条:DELETE rule
        self.assertIn("UPDATE notification_logs SET rule_id = NULL", cur.executed[0][0])
        self.assertIn("DELETE FROM notification_rules", cur.executed[1][0])

    def test_tenant_scope(self):
        cur = _FakeCursor(rowcount=1)
        with _patch(cur):
            store.delete_notification_rule(7, "u1", "t1")
        self.assertIn("tenant_id = %s", cur.executed[1][0])

    def test_exception_returns_false(self):
        with _patch(_ExplodingCursor()):
            self.assertFalse(store.delete_notification_rule(7, "u1", None))


class LogNotificationTests(unittest.TestCase):
    def test_returns_id_and_coerces_rule_id(self):
        cur = _FakeCursor(one_seq=[{"id": 12}])
        with _patch(cur):
            rid = store.log_notification("u1", None, 3, "tpl", "evt", "ref", "L123", "sent")
        self.assertEqual(rid, 12)
        self.assertEqual(cur.executed[0][1][2], 3)

    def test_none_rule_id_stays_none(self):
        cur = _FakeCursor(one_seq=[{"id": 13}])
        with _patch(cur):
            store.log_notification("u1", None, None, "tpl", None, None, None, "failed")
        self.assertIsNone(cur.executed[0][1][2])

    def test_exception_returns_none(self):
        with _patch(_ExplodingCursor()):
            self.assertIsNone(
                store.log_notification("u1", None, None, "tpl", None, None, None, "x")
            )


class ListNotificationLogsTests(unittest.TestCase):
    def test_tenant_scope_with_limit(self):
        cur = _FakeCursor(all_seq=[[{"id": 1}]])
        with _patch(cur):
            store.list_notification_logs("u1", tenant_id="t1", limit=10)
        self.assertEqual(cur.executed[0][1], ("t1", 10))

    def test_user_scope_null_tenant(self):
        cur = _FakeCursor(all_seq=[[]])
        with _patch(cur):
            store.list_notification_logs("u1")
        self.assertIn("tenant_id IS NULL", cur.executed[0][0])

    def test_exception_returns_empty(self):
        with _patch(_ExplodingCursor()):
            self.assertEqual(store.list_notification_logs("u1"), [])


class ListActiveByTemplateTests(unittest.TestCase):
    def test_filters_enabled_template(self):
        cur = _FakeCursor(all_seq=[[{"id": 1, "enabled": True}]])
        with _patch(cur):
            rows = store.list_active_notification_rules_by_template("tpl_x")
        self.assertEqual(len(rows), 1)
        self.assertIn("enabled = true", cur.executed[0][0])
        self.assertEqual(cur.executed[0][1], ("tpl_x",))

    def test_exception_returns_empty(self):
        with _patch(_ExplodingCursor()):
            self.assertEqual(store.list_active_notification_rules_by_template("tpl_x"), [])


if __name__ == "__main__":
    unittest.main()
