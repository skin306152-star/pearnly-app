# -*- coding: utf-8 -*-
"""services.db_migrations.workspace_backfill 单测(套账隔离 PO-1)。

脱库可测的部分:默认套账创建的幂等逻辑 + 目标表清单与机械闸登记一致。
SQL 回填正确性 = prod 库 dry-run 验证(report()),见 runbook 05。
不用 pytest(见 memory no-pytest-tests-unittest-only)。
"""

import unittest

from services.db_migrations import workspace_backfill as wb
from tests.unit.test_workspace_sql_isolation import OPERATIONAL_TABLES


class _ProgFakeCursor:
    """按 SQL 子串编程返回的假游标(记录所有 execute)。"""

    def __init__(self, responder):
        self._responder = responder
        self.executed = []
        self._last = ("", None)

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        self._last = (sql, params)

    def fetchone(self):
        return self._responder(*self._last)

    def fetchall(self):
        return self._responder(*self._last)

    def inserts(self):
        return [c for c in self.executed if "INSERT INTO workspace_clients" in c[0]]


class EnsureDefaultWorkspacesTest(unittest.TestCase):
    def test_creates_only_for_tenant_without_workspace(self):
        tenants = [
            {"id": "t1", "name": "A 公司", "owner_user_id": "u1"},  # 无套账 → 建
            {"id": "t2", "name": "B 公司", "owner_user_id": "u2"},  # 已有套账 → 跳
        ]

        def responder(sql, params):
            if "FROM tenants" in sql:
                return tenants
            if "FROM workspace_clients WHERE tenant_id" in sql:
                return None if params[0] == "t1" else {"x": 1}
            return None

        cur = _ProgFakeCursor(responder)
        created = wb.ensure_default_workspaces(cur)
        self.assertEqual(created, 1)
        ins = cur.inserts()
        self.assertEqual(len(ins), 1)
        # 新套账归到 t1,user_id 用 owner
        self.assertEqual(ins[0][1], ("t1", "u1", "A 公司"))

    def test_falls_back_to_owner_lookup_when_owner_null(self):
        tenants = [{"id": "t1", "name": "X", "owner_user_id": None}]

        def responder(sql, params):
            if "FROM tenants" in sql:
                return tenants
            if "FROM workspace_clients WHERE tenant_id" in sql:
                return None
            if "FROM users WHERE tenant_id" in sql:
                return {"id": "owner-from-users"}
            return None

        cur = _ProgFakeCursor(responder)
        created = wb.ensure_default_workspaces(cur)
        self.assertEqual(created, 1)
        self.assertEqual(cur.inserts()[0][1], ("t1", "owner-from-users", "X"))

    def test_skips_tenant_with_no_usable_owner(self):
        tenants = [{"id": "t1", "name": "X", "owner_user_id": None}]

        def responder(sql, params):
            if "FROM tenants" in sql:
                return tenants
            if "FROM workspace_clients WHERE tenant_id" in sql:
                return None
            if "FROM users WHERE tenant_id" in sql:
                return None  # 连用户都没有 → 跳过,不建
            return None

        cur = _ProgFakeCursor(responder)
        self.assertEqual(wb.ensure_default_workspaces(cur), 0)
        self.assertEqual(cur.inserts(), [])


class RegistryConsistencyTest(unittest.TestCase):
    def test_target_tables_within_operational_set(self):
        for table in wb._ADD_AND_BACKFILL + wb._BACKFILL_ONLY:
            self.assertIn(table, OPERATIONAL_TABLES, f"{table} 不在运营表名单(01 数据模型)")


if __name__ == "__main__":
    unittest.main()
