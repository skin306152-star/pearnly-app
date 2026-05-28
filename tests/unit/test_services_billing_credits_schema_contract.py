# -*- coding: utf-8 -*-
"""契约测试 · services/billing/credits_schema(REFACTOR-B2)"""

import unittest
from contextlib import contextmanager
from unittest import mock


class _FakeCursor:
    def __init__(self, raise_on_exec=False):
        self._raise = raise_on_exec
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        if self._raise:
            raise RuntimeError("simulated DB error")

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _ctxmgr(cur):
    @contextmanager
    def _gc(commit=False):
        yield cur

    return _gc


class CreditsSchemaReExportTests(unittest.TestCase):
    def test_db_reexports(self):
        import db
        from services.billing import credits_schema

        for name in ("ensure_credits_tables", "ensure_tenant_credits"):
            self.assertTrue(hasattr(credits_schema, name))
            self.assertIs(getattr(db, name), getattr(credits_schema, name))


class EnsureCreditsTablesTests(unittest.TestCase):
    def test_runs_advisory_lock_then_create_then_alter_then_seeds(self):
        from services.billing import credits_schema

        cur = _FakeCursor()
        with mock.patch.object(credits_schema.db, "get_cursor", _ctxmgr(cur)):
            credits_schema.ensure_credits_tables()

        sqls = [e[0] for e in cur.executed]
        # 串行 DDL advisory lock
        self.assertTrue(any("pg_advisory_xact_lock" in s for s in sqls))
        # 5 张表全建
        self.assertTrue(any("CREATE TABLE IF NOT EXISTS user_company_roles" in s for s in sqls))
        self.assertTrue(any("CREATE TABLE IF NOT EXISTS tenant_credits" in s for s in sqls))
        self.assertTrue(any("CREATE TABLE IF NOT EXISTS credit_transactions" in s for s in sqls))
        self.assertTrue(any("CREATE TABLE IF NOT EXISTS monthly_page_usage" in s for s in sqls))
        self.assertTrue(any("CREATE TABLE IF NOT EXISTS topup_requests" in s for s in sqls))
        # ALTER 2 列
        self.assertTrue(any("is_billing_exempt" in s and "ALTER TABLE users" in s for s in sqls))
        self.assertTrue(any("active_tenant_id" in s and "ALTER TABLE users" in s for s in sqls))
        # seed 迁移 + 豁免名单
        self.assertTrue(any("INSERT INTO user_company_roles" in s for s in sqls))
        self.assertTrue(any("INSERT INTO tenant_credits" in s for s in sqls))
        self.assertTrue(any("UPDATE users SET is_billing_exempt = TRUE" in s for s in sqls))

    def test_db_error_raises(self):
        """ensure_credits_tables 失败应 re-raise(启动期 DDL 失败要让上层感知)"""
        from services.billing import credits_schema

        cur = _FakeCursor(raise_on_exec=True)
        with mock.patch.object(credits_schema.db, "get_cursor", _ctxmgr(cur)):
            with self.assertRaises(RuntimeError):
                credits_schema.ensure_credits_tables()


class EnsureTenantCreditsTests(unittest.TestCase):
    def test_empty_tenant_returns_no_db_call(self):
        from services.billing import credits_schema

        cur = _FakeCursor()
        with mock.patch.object(credits_schema.db, "get_cursor", _ctxmgr(cur)):
            credits_schema.ensure_tenant_credits(None)
            credits_schema.ensure_tenant_credits("")
        self.assertEqual(cur.executed, [])

    def test_inserts_zero_balance_on_conflict_do_nothing(self):
        from services.billing import credits_schema

        cur = _FakeCursor()
        with mock.patch.object(credits_schema.db, "get_cursor", _ctxmgr(cur)):
            credits_schema.ensure_tenant_credits("t1")
        sql, params = cur.executed[0]
        self.assertIn("INSERT INTO tenant_credits", sql)
        self.assertIn("ON CONFLICT (tenant_id) DO NOTHING", sql)
        self.assertEqual(params, ("t1",))

    def test_db_error_warning_no_raise(self):
        """ensure_tenant_credits 失败应 swallow(注册主流程不受影响)"""
        from services.billing import credits_schema

        cur = _FakeCursor(raise_on_exec=True)
        with mock.patch.object(credits_schema.db, "get_cursor", _ctxmgr(cur)):
            # 不抛
            credits_schema.ensure_tenant_credits("t1")


if __name__ == "__main__":
    unittest.main()
