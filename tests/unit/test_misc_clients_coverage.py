# -*- coding: utf-8 -*-
"""REFACTOR-D2 · services/clients/store.py 行为/契约覆盖

补行为测试(既有 test_clients_store_contract.py 只验 re-export ·
既有 test_buyer_to_client_resolver / resolve_or_create_buyer_client 已覆盖 resolver)。

本文件聚焦未被行为覆盖的部分:
- get_category_for_seller: 空 seller 不查 DB · tenant/user 两路 · 命中/未命中 / 异常
- learn_buyer_to_client: 空 buyer / 空 client_id 早返 · 截断 name[:200]/tax[:30] · 异常
- upsert_supplier_category: 空 seller/category 早返 · 截断 · tenant/user 两路 SQL
- list_used_categories / count_supplier_mappings: tenant 隔离 · 异常兜底
- list_clients / get_client / create_client / update_client / delete_client /
  assign_invoice_to_client: tenant 隔离 · rowcount 语义 · 越权防护 · 空名拒建。

全 tenant 隔离矩阵 · 测真实契约。
"""

import sys
import types
import unittest
from contextlib import contextmanager
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
from services.clients import store  # noqa: E402


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


@contextmanager
def _patch(cur):
    # B8 RLS:clients/ocr_history 已 enroll · DAL 走 get_cursor_rls · 同 patch 两游标(wave2 范式)。
    factory = lambda *a, **k: _CM(cur)  # noqa: E731
    with patch.object(db, "get_cursor", factory), patch.object(db, "get_cursor_rls", factory):
        yield


class GetCategoryForSellerTests(unittest.TestCase):
    def test_empty_seller_returns_none_no_db(self):
        cur = _FakeCursor()
        with _patch(cur):
            self.assertIsNone(store.get_category_for_seller("", "u1"))
            self.assertIsNone(store.get_category_for_seller("   ", "u1"))
            self.assertIsNone(store.get_category_for_seller(None, "u1"))
        self.assertEqual(len(cur.executed), 0)

    def test_tenant_scope_hit(self):
        cur = _FakeCursor(one_seq=[{"category": "Office Supplies"}])
        with _patch(cur):
            c = store.get_category_for_seller("Acme", "u1", tenant_id="t1")
        self.assertEqual(c, "Office Supplies")
        self.assertIn("tenant_id = %s", cur.executed[0][0])

    def test_user_scope_isolates_null_tenant(self):
        cur = _FakeCursor(one_seq=[None])
        with _patch(cur):
            store.get_category_for_seller("Acme", "u1")
        self.assertIn("tenant_id IS NULL", cur.executed[0][0])

    def test_exception_returns_none(self):
        with _patch(_ExplodingCursor()):
            self.assertIsNone(store.get_category_for_seller("Acme", "u1"))


class LearnBuyerToClientTests(unittest.TestCase):
    def test_empty_buyer_returns_false_no_db(self):
        cur = _FakeCursor()
        with _patch(cur):
            self.assertFalse(store.learn_buyer_to_client("", None, 5, "u1"))
            self.assertFalse(store.learn_buyer_to_client(None, None, 5, "u1"))
        self.assertEqual(len(cur.executed), 0)

    def test_zero_client_id_returns_false(self):
        cur = _FakeCursor()
        with _patch(cur):
            self.assertFalse(store.learn_buyer_to_client("Acme", None, 0, "u1"))
        self.assertEqual(len(cur.executed), 0)

    def test_truncates_name_and_tax(self):
        cur = _FakeCursor()
        with _patch(cur):
            store.learn_buyer_to_client("B" * 300, "9" * 50, 5, "u1")
        params = cur.executed[0][1]
        # (tenant_id, user_id, name, tax, client_id)
        self.assertEqual(len(params[2]), 200)
        self.assertEqual(len(params[3]), 30)
        self.assertEqual(params[4], 5)

    def test_blank_tax_becomes_none(self):
        cur = _FakeCursor()
        with _patch(cur):
            store.learn_buyer_to_client("Acme", "   ", 5, "u1")
        self.assertIsNone(cur.executed[0][1][3])

    def test_exception_returns_false(self):
        with _patch(_ExplodingCursor()):
            self.assertFalse(store.learn_buyer_to_client("Acme", None, 5, "u1"))


class UpsertSupplierCategoryTests(unittest.TestCase):
    def test_empty_inputs_return_false_no_db(self):
        cur = _FakeCursor()
        with _patch(cur):
            self.assertFalse(store.upsert_supplier_category("", "cat", "u1"))
            self.assertFalse(store.upsert_supplier_category("seller", "", "u1"))
            self.assertFalse(store.upsert_supplier_category(None, None, "u1"))
        self.assertEqual(len(cur.executed), 0)

    def test_truncation(self):
        cur = _FakeCursor()
        with _patch(cur):
            store.upsert_supplier_category("S" * 300, "C" * 100, "u1")
        params = cur.executed[0][1]
        # user-scope: (user_id, seller, category)
        self.assertEqual(len(params[1]), 200)
        self.assertEqual(len(params[2]), 80)

    def test_tenant_scope_sql(self):
        cur = _FakeCursor()
        with _patch(cur):
            store.upsert_supplier_category("Acme", "Office", "u1", tenant_id="t1")
        self.assertIn("INSERT INTO supplier_categories (tenant_id", cur.executed[0][0])
        self.assertEqual(cur.executed[0][1][0], "t1")

    def test_exception_returns_false(self):
        with _patch(_ExplodingCursor()):
            self.assertFalse(store.upsert_supplier_category("Acme", "Office", "u1"))


class ListUsedCategoriesTests(unittest.TestCase):
    def test_tenant_scope_returns_category_list(self):
        cur = _FakeCursor(all_seq=[[{"category": "A", "total": 5}, {"category": "B", "total": 2}]])
        with _patch(cur):
            cats = store.list_used_categories("u1", tenant_id="t1")
        self.assertEqual(cats, ["A", "B"])
        self.assertIn("tenant_id = %s", cur.executed[0][0])

    def test_user_scope_null_tenant(self):
        cur = _FakeCursor(all_seq=[[]])
        with _patch(cur):
            store.list_used_categories("u1")
        self.assertIn("tenant_id IS NULL", cur.executed[0][0])

    def test_exception_returns_empty(self):
        with _patch(_ExplodingCursor()):
            self.assertEqual(store.list_used_categories("u1"), [])


class CountSupplierMappingsTests(unittest.TestCase):
    def test_tenant_scope_count(self):
        cur = _FakeCursor(one_seq=[{"n": 7}])
        with _patch(cur):
            self.assertEqual(store.count_supplier_mappings("u1", tenant_id="t1"), 7)

    def test_user_scope_none_row_zero(self):
        with _patch(_FakeCursor(one_seq=[None])):
            self.assertEqual(store.count_supplier_mappings("u1"), 0)

    def test_exception_returns_zero(self):
        with _patch(_ExplodingCursor()):
            self.assertEqual(store.count_supplier_mappings("u1"), 0)


class ListClientsTests(unittest.TestCase):
    def test_tenant_scope_where(self):
        cur = _FakeCursor(all_seq=[[{"id": 1, "name": "X"}]])
        with _patch(cur):
            rows = store.list_clients("u1", tenant_id="t1")
        self.assertEqual(len(rows), 1)
        self.assertIn("user_id IN (SELECT id FROM users WHERE tenant_id = %s)", cur.executed[0][0])

    def test_active_only_default(self):
        cur = _FakeCursor(all_seq=[[]])
        with _patch(cur):
            store.list_clients("u1")
        self.assertIn("is_active = TRUE", cur.executed[0][0])

    def test_include_inactive_drops_filter(self):
        cur = _FakeCursor(all_seq=[[]])
        with _patch(cur):
            store.list_clients("u1", include_inactive=True)
        self.assertNotIn("is_active = TRUE", cur.executed[0][0])

    def test_exception_returns_empty(self):
        with _patch(_ExplodingCursor()):
            self.assertEqual(store.list_clients("u1"), [])


class GetClientTests(unittest.TestCase):
    def test_tenant_scope(self):
        cur = _FakeCursor(one_seq=[{"id": 9, "name": "Y"}])
        with _patch(cur):
            r = store.get_client("u1", 9, tenant_id="t1")
        self.assertEqual(r["id"], 9)
        self.assertIn("tenant_id = %s", cur.executed[0][0])

    def test_user_scope_not_found(self):
        with _patch(_FakeCursor(one_seq=[None])):
            self.assertIsNone(store.get_client("u1", 9))

    def test_exception_returns_none(self):
        with _patch(_ExplodingCursor()):
            self.assertIsNone(store.get_client("u1", 9))


class CreateClientTests(unittest.TestCase):
    def test_empty_name_returns_none_no_db(self):
        cur = _FakeCursor()
        with _patch(cur):
            self.assertIsNone(store.create_client("u1", None, ""))
            self.assertIsNone(store.create_client("u1", None, "   "))
        self.assertEqual(len(cur.executed), 0)

    def test_returns_new_id_and_truncates_name(self):
        cur = _FakeCursor(one_seq=[{"id": 55}])
        with _patch(cur):
            cid = store.create_client("u1", None, "N" * 300, tax_id="0105543123456")
        self.assertEqual(cid, 55)
        # name 截断到 200
        self.assertEqual(len(cur.executed[0][1][2]), 200)

    def test_blank_optional_fields_become_none(self):
        cur = _FakeCursor(one_seq=[{"id": 1}])
        with _patch(cur):
            store.create_client("u1", None, "Acme", short_name="   ", tax_id="")
        params = cur.executed[0][1]
        self.assertIsNone(params[3])  # short_name
        self.assertIsNone(params[4])  # tax_id

    def test_default_color(self):
        cur = _FakeCursor(one_seq=[{"id": 1}])
        with _patch(cur):
            store.create_client("u1", None, "Acme")
        # color 是第 11 个参数(index 10);其后是买方目录字段 party_type/branch/promptpay_id。
        self.assertEqual(cur.executed[0][1][10], "#3b82f6")

    def test_buyer_directory_fields_persist(self):
        cur = _FakeCursor(one_seq=[{"id": 1}])
        with _patch(cur):
            store.create_client(
                "u1", None, "Acme", party_type="company", branch="HQ", promptpay_id="0812345678"
            )
        params = cur.executed[0][1]
        self.assertIn("company", params)
        self.assertIn("HQ", params)
        self.assertIn("0812345678", params)

    def test_exception_returns_none(self):
        with _patch(_ExplodingCursor()):
            self.assertIsNone(store.create_client("u1", None, "Acme"))


class UpdateClientTests(unittest.TestCase):
    def test_no_fields_returns_false(self):
        cur = _FakeCursor()
        with _patch(cur):
            self.assertFalse(store.update_client("u1", 5))
        self.assertEqual(len(cur.executed), 0)

    def test_disallowed_field_ignored_returns_false(self):
        cur = _FakeCursor()
        with _patch(cur):
            self.assertFalse(store.update_client("u1", 5, id=999, bogus="x"))
        self.assertEqual(len(cur.executed), 0)

    def test_partial_update_builds_set_and_truncates(self):
        cur = _FakeCursor(rowcount=1)
        with _patch(cur):
            ok = store.update_client("u1", 5, name="N" * 300, color="blue")
        self.assertTrue(ok)
        sql = cur.executed[0][0]
        self.assertIn("name = %s", sql)
        self.assertIn("updated_at = NOW()", sql)
        # 第一个 param 是被截断的 name
        self.assertEqual(len(cur.executed[0][1][0]), 200)

    def test_tenant_scope_where(self):
        cur = _FakeCursor(rowcount=1)
        with _patch(cur):
            store.update_client("u1", 5, tenant_id="t1", name="X")
        self.assertIn("user_id IN (SELECT id FROM users WHERE tenant_id = %s)", cur.executed[0][0])

    def test_rowcount_zero_false(self):
        with _patch(_FakeCursor(rowcount=0)):
            self.assertFalse(store.update_client("u1", 5, name="X"))

    def test_exception_returns_false(self):
        with _patch(_ExplodingCursor()):
            self.assertFalse(store.update_client("u1", 5, name="X"))


class DeleteClientTests(unittest.TestCase):
    def test_cascade_unlink_then_delete(self):
        cur = _FakeCursor(rowcount=1)
        with _patch(cur):
            ok = store.delete_client("u1", 5)
        self.assertTrue(ok)
        # 第 1 条解绑 ocr_history · 第 2 条删 client
        self.assertIn("UPDATE ocr_history SET client_id = NULL", cur.executed[0][0])
        self.assertIn("DELETE FROM clients", cur.executed[1][0])

    def test_no_cascade_skips_unlink(self):
        cur = _FakeCursor(rowcount=1)
        with _patch(cur):
            store.delete_client("u1", 5, cascade_unlink=False)
        self.assertIn("DELETE FROM clients", cur.executed[0][0])
        self.assertEqual(len(cur.executed), 1)

    def test_tenant_scope(self):
        cur = _FakeCursor(rowcount=1)
        with _patch(cur):
            store.delete_client("u1", 5, tenant_id="t1")
        self.assertIn("tenant_id = %s", cur.executed[-1][0])

    def test_exception_returns_false(self):
        with _patch(_ExplodingCursor()):
            self.assertFalse(store.delete_client("u1", 5))


class AssignInvoiceToClientTests(unittest.TestCase):
    def test_unauthorized_client_returns_false(self):
        # 验证客户归属查询返 None → 越权 · 直接 False · 不更新发票
        cur = _FakeCursor(one_seq=[None])
        with _patch(cur):
            ok = store.assign_invoice_to_client("u1", "hist-1", 5)
        self.assertFalse(ok)
        # 只执行了 SELECT 校验 · 没 UPDATE
        self.assertEqual(len(cur.executed), 1)

    def test_valid_client_updates_invoice(self):
        cur = _FakeCursor(one_seq=[{"id": 5}], rowcount=1)
        with _patch(cur):
            ok = store.assign_invoice_to_client("u1", "hist-1", 5)
        self.assertTrue(ok)
        self.assertIn("UPDATE ocr_history SET client_id", cur.executed[1][0])

    def test_none_client_id_skips_ownership_check(self):
        # client_id=None 表示移除归属 · 不做客户校验 · 直接更新
        cur = _FakeCursor(rowcount=1)
        with _patch(cur):
            ok = store.assign_invoice_to_client("u1", "hist-1", None)
        self.assertTrue(ok)
        self.assertIn("UPDATE ocr_history SET client_id", cur.executed[0][0])

    def test_tenant_scope_ownership_check(self):
        cur = _FakeCursor(one_seq=[{"id": 5}], rowcount=1)
        with _patch(cur):
            store.assign_invoice_to_client("u1", "hist-1", 5, tenant_id="t1")
        self.assertIn("tenant_id = %s", cur.executed[0][0])

    def test_exception_returns_false(self):
        with _patch(_ExplodingCursor()):
            self.assertFalse(store.assign_invoice_to_client("u1", "hist-1", None))


class UpdateHistoryClientIdTests(unittest.TestCase):
    def test_tenant_scope(self):
        cur = _FakeCursor(rowcount=1)
        with _patch(cur):
            ok = store.update_history_client_id("hist-1", 5, "u1", tenant_id="t1")
        self.assertTrue(ok)
        self.assertIn("user_id IN (SELECT id FROM users WHERE tenant_id = %s)", cur.executed[0][0])

    def test_user_scope(self):
        cur = _FakeCursor(rowcount=1)
        with _patch(cur):
            store.update_history_client_id("hist-1", 5, "u1")
        self.assertIn("user_id = %s", cur.executed[0][0])

    def test_rowcount_zero_false(self):
        with _patch(_FakeCursor(rowcount=0)):
            self.assertFalse(store.update_history_client_id("hist-1", 5, "u1"))

    def test_exception_returns_false(self):
        with _patch(_ExplodingCursor()):
            self.assertFalse(store.update_history_client_id("hist-1", 5, "u1"))


if __name__ == "__main__":
    unittest.main()
