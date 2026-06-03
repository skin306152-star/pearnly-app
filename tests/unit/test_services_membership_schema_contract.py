# -*- coding: utf-8 -*-
"""契约测试 · services/membership/schema(REFACTOR-B2)"""

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


class MembershipSchemaReExportTests(unittest.TestCase):
    def test_db_reexports(self):
        from core import db
        from services.membership import schema

        self.assertTrue(hasattr(schema, "ensure_membership_tables"))
        self.assertIs(db.ensure_membership_tables, schema.ensure_membership_tables)


class EnsureMembershipTablesTests(unittest.TestCase):
    def test_builds_three_tables_and_seeds_roles(self):
        from services.membership import schema

        cur = _FakeCursor()
        with mock.patch.object(schema.db, "get_cursor", _ctxmgr(cur)):
            schema.ensure_membership_tables()

        sqls = [e[0] for e in cur.executed]
        self.assertTrue(any("CREATE TABLE IF NOT EXISTS roles" in s for s in sqls))
        self.assertTrue(any("CREATE TABLE IF NOT EXISTS memberships" in s for s in sqls))
        self.assertTrue(any("CREATE TABLE IF NOT EXISTS client_assignments" in s for s in sqls))
        self.assertTrue(
            any("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS tenant_type_v2" in s for s in sqls)
        )
        # 3 系统角色 seed
        self.assertTrue(any("INSERT INTO roles" in s and "'owner'" in s for s in sqls))

    def test_db_error_swallowed_not_raised(self):
        """ensure_membership_tables 失败仅 log error · 不抛(启动期不阻塞主流程)"""
        from services.membership import schema

        cur = _FakeCursor(raise_on_exec=True)
        with mock.patch.object(schema.db, "get_cursor", _ctxmgr(cur)):
            # 不抛
            schema.ensure_membership_tables()


if __name__ == "__main__":
    unittest.main()
