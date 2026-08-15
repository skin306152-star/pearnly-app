# -*- coding: utf-8 -*-
"""契约测试 · services/daily(schema + store)。

不碰真库:store 用 _FakeCursor 断言 SQL 参数化 + 租户隔离条件;
schema 断言 re-export 与幂等 DDL 内容(照 test_services_usage_store_contract 范式)。
"""

import unittest
from contextlib import contextmanager
from decimal import Decimal
from unittest import mock


class _FakeCursor:
    def __init__(self, fetch_row=None, rowcount=0):
        self._row = fetch_row
        self.rowcount = rowcount
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self._row

    def fetchall(self):
        return [self._row] if self._row is not None else []


def _ctxmgr(cur):
    @contextmanager
    def _gc(*a, **k):
        yield cur

    return _gc


class DailySchemaTests(unittest.TestCase):
    def test_db_reexports_same_object(self):
        from core import db
        from services.daily import schema

        self.assertIs(db.ensure_daily_tables, schema.ensure_daily_tables)
        self.assertIs(db.ensure_daily_rls, schema.ensure_daily_rls)

    def test_ensure_daily_tables_runs_ddl_and_index(self):
        from services.daily import schema

        cur = _FakeCursor()
        with mock.patch.object(schema.db, "get_cursor", _ctxmgr(cur)):
            schema.ensure_daily_tables()
        self.assertEqual(len(cur.executed), 2)
        create, index = cur.executed
        self.assertIn("CREATE TABLE IF NOT EXISTS daily_entries", create[0])
        self.assertIn("tenant_id uuid NOT NULL", create[0])
        self.assertIn("amount numeric(12, 2) NOT NULL CHECK (amount > 0)", create[0])
        self.assertIn("kind text NOT NULL CHECK (kind IN ('income', 'expense'))", create[0])
        self.assertIn("idx_daily_entries_tenant_date", index[0])

    def test_ensure_daily_rls_applies_tenant_policy(self):
        from services.daily import schema

        with (
            mock.patch("core.rls.existing_tables", return_value=["daily_entries"]),
            mock.patch("core.rls.apply_tenant_rls") as apply,
        ):
            cur = object()
            with mock.patch.object(schema.db, "get_cursor", _ctxmgr(cur)):
                schema.ensure_daily_rls()
        apply.assert_called_once_with(cur, "daily_entries")

    def test_ensure_daily_rls_skips_missing_table(self):
        from services.daily import schema

        with (
            mock.patch("core.rls.existing_tables", return_value=[]),
            mock.patch("core.rls.apply_tenant_rls") as apply,
        ):
            with mock.patch.object(schema.db, "get_cursor", _ctxmgr(object())):
                schema.ensure_daily_rls()
        apply.assert_called_once_with(mock.ANY)  # 表未建 → 零参数传入


class DailyStoreTests(unittest.TestCase):
    def test_list_entries_scoped_by_tenant_and_month(self):
        from services.daily import store

        cur = _FakeCursor(fetch_row={"id": "e1"})
        store.list_entries(cur, "t1", "2026-09")
        sql, params = cur.executed[0]
        self.assertIn("WHERE tenant_id = %s::uuid AND to_char(entry_date, 'YYYY-MM') = %s", sql)
        self.assertIn("ORDER BY entry_date DESC", sql)
        self.assertEqual(params, ("t1", "2026-09"))

    def test_insert_entry_returns_row(self):
        from services.daily import store

        cur = _FakeCursor(fetch_row={"id": "e1", "amount": Decimal("12.50")})
        row = store.insert_entry(cur, "t1", "2026-09-05", "expense", "ค่าอาหาร", Decimal("12.50"))
        sql, params = cur.executed[0]
        self.assertIn("INSERT INTO daily_entries", sql)
        self.assertIn("RETURNING id::text", sql)
        self.assertEqual(params, ("t1", "2026-09-05", "expense", "ค่าอาหาร", Decimal("12.50")))
        self.assertEqual(row["id"], "e1")

    def test_insert_entry_no_row_returns_none(self):
        from services.daily import store

        cur = _FakeCursor(fetch_row=None)
        self.assertIsNone(store.insert_entry(cur, "t1", "2026-09-05", "income", "x", Decimal("1")))

    def test_delete_entry_requires_tenant_and_id(self):
        from services.daily import store

        cur = _FakeCursor(rowcount=1)
        self.assertTrue(store.delete_entry(cur, "t1", "e1"))
        sql, params = cur.executed[0]
        self.assertIn("WHERE tenant_id = %s::uuid AND id = %s::uuid", sql)
        self.assertEqual(params, ("t1", "e1"))

    def test_delete_entry_zero_rows_returns_false(self):
        from services.daily import store

        cur = _FakeCursor(rowcount=0)
        self.assertFalse(store.delete_entry(cur, "t1", "e1"))


if __name__ == "__main__":
    unittest.main()
