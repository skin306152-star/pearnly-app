# -*- coding: utf-8 -*-
"""守门:_seed_roles 只刷 tenant_id IS NULL 的预设行,不碰 ERP 团队角色。

ERP 团队以 tenant roles 表达最小权限组合。启动种子只能更新系统预设行,不能覆盖这些
租户级 ERP 角色。

内存假游标拦 SQL(同 test_authz_schema_migration 套路 · 不触真库)。
"""

import unittest

import services.db_migrations.authz_schema as mig
from services.authz import registry


class _Cur:
    def __init__(self):
        self.sql = []
        self.params = []
        self.rowcount = 0

    def execute(self, sql, params=None):
        self.sql.append(" ".join(sql.split()))
        self.params.append(params)

    def fetchall(self):
        return []

    def fetchone(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _run_seed():
    cur = _Cur()
    mig._seed_roles(cur)
    return cur


class SeedTouchesOnlySystemRowsTests(unittest.TestCase):
    """种子的每一条写语句都必须把作用域钉在 tenant_id IS NULL 上。"""

    def test_only_six_system_keys_upserted(self):
        cur = _run_seed()
        upserts = [p for p in cur.params if p and isinstance(p, tuple) and len(p) == 3]
        seeded_keys = {p[0] for p in upserts}
        self.assertEqual(seeded_keys, set(registry.ROLE_KEYS))
        self.assertEqual(len(upserts), len(registry.ROLE_KEYS), "种子不得为 ERP 团队角色多发语句")

    def test_every_insert_pins_tenant_id_null(self):
        """INSERT 的 VALUES 把 tenant_id 硬写 NULL,租户级 ERP 角色不会是冲突目标。"""
        for stmt in (s for s in _run_seed().sql if "INSERT INTO roles" in s):
            self.assertIn("is_system, tenant_id", stmt)
            self.assertIn("TRUE, NULL", stmt, "系统角色必须 tenant_id=NULL 入库")

    def test_no_blanket_mutation_of_roles(self):
        """种子里不得出现会扫到租户角色的 DELETE / 无 tenant_id 限定的 UPDATE。"""
        for stmt in _run_seed().sql:
            self.assertNotIn("DELETE FROM roles", stmt, f"种子不许删 roles: {stmt}")
            if stmt.startswith("UPDATE roles"):
                self.fail(f"种子不许直接 UPDATE roles(只能走 ON CONFLICT 限定系统行): {stmt}")

    def test_conflict_target_is_system_name(self):
        """冲突解析走 name 列;ERP 角色使用租户命名空间,不会撞系统 name。"""
        joined = " || ".join(_run_seed().sql)
        self.assertIn("ON CONFLICT (name) DO UPDATE", joined)


class SeedProvisionsErpTeamRoleSchemaTests(unittest.TestCase):
    """ERP 团队角色所需的列/索引由种子幂等建好。"""

    def test_display_name_column_added(self):
        joined = " || ".join(_run_seed().sql)
        self.assertIn("ADD COLUMN IF NOT EXISTS display_name TEXT", joined)

    def test_erp_team_role_active_and_version_columns(self):
        joined = " || ".join(_run_seed().sql)
        self.assertIn("ADD COLUMN IF NOT EXISTS is_active BOOLEAN", joined)
        self.assertIn("ADD COLUMN IF NOT EXISTS version INTEGER", joined)

    def test_per_tenant_key_unique_index(self):
        """(tenant_id, key) 唯一,同租户同 ERP 权限组合只命中一行。"""
        joined = " || ".join(_run_seed().sql)
        self.assertIn("uq_roles_tenant_key", joined)
        self.assertIn("WHERE tenant_id IS NOT NULL", joined)


if __name__ == "__main__":
    unittest.main()
