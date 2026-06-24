# -*- coding: utf-8 -*-
"""core.rls 单一来源 RLS helper 守门测试(POS 项目 · simplify 收口)。

锁定:apply_tenant_rls 对每表发 ENABLE RLS + DROP POLICY IF EXISTS + CREATE POLICY,且谓词
含 app.current_tenant_id + bypass_rls(USING + WITH CHECK 两端)。这是 3 个 ensure_* 共用的
唯一定义,改这里=全部生效。
"""

import unittest

from core.rls import (
    apply_tenant_rls,
    apply_tenant_workspace_rls,
    apply_tenant_or_user_rls,
    ensure_rls_app_role,
)


class FakeCursor:
    def __init__(self):
        self.sqls = []

    def execute(self, sql, params=None):
        self.sqls.append(sql)


class ApplyTenantRlsTests(unittest.TestCase):
    def test_emits_enable_drop_create_per_table(self):
        cur = FakeCursor()
        apply_tenant_rls(cur, "warehouses", "inventory_stock")
        joined = "\n".join(cur.sqls)
        for t in ("warehouses", "inventory_stock"):
            self.assertIn(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY", joined)
            self.assertIn(f"DROP POLICY IF EXISTS tenant_isolation ON {t}", joined)
            self.assertIn(f"CREATE POLICY tenant_isolation ON {t}", joined)
        # 每表 3 条语句
        self.assertEqual(len(cur.sqls), 6)

    def test_policy_predicate_both_sides(self):
        cur = FakeCursor()
        apply_tenant_rls(cur, "tenant_modules")
        create = next(s for s in cur.sqls if "CREATE POLICY" in s)
        self.assertIn("USING (", create)
        self.assertIn("WITH CHECK (", create)
        self.assertIn("current_setting('app.current_tenant_id', true)", create)
        self.assertIn("current_setting('app.bypass_rls', true) = 'on'", create)


class PolicyTemplateTests(unittest.TestCase):
    def test_workspace_policy_has_tenant_and_workspace_predicate(self):
        cur = FakeCursor()
        apply_tenant_workspace_rls(cur, "pos_sales")
        create = next(s for s in cur.sqls if "CREATE POLICY" in s)
        self.assertIn("current_setting('app.current_tenant_id', true)", create)
        self.assertIn("workspace_client_id::text", create)
        self.assertIn("current_setting('app.current_workspace_id', true)", create)
        self.assertIn("WITH CHECK (", create)

    def test_tenant_or_user_policy_has_user_fallback(self):
        cur = FakeCursor()
        apply_tenant_or_user_rls(cur, "clients")
        create = next(s for s in cur.sqls if "CREATE POLICY" in s)
        self.assertIn("tenant_id IS NULL", create)
        self.assertIn("user_id::text = current_setting('app.current_user_id', true)", create)

    def test_force_flag_emits_force_rls(self):
        cur = FakeCursor()
        apply_tenant_rls(cur, "clients", force=True)
        joined = "\n".join(cur.sqls)
        self.assertIn("FORCE ROW LEVEL SECURITY", joined)

    def test_no_force_by_default(self):
        cur = FakeCursor()
        apply_tenant_rls(cur, "clients")
        self.assertNotIn("FORCE ROW LEVEL SECURITY", "\n".join(cur.sqls))


class EnsureRlsAppRoleTests(unittest.TestCase):
    def test_creates_min_privilege_role_and_grants(self):
        cur = FakeCursor()
        ensure_rls_app_role(cur, "pearnly_app")
        joined = "\n".join(cur.sqls)
        self.assertIn("NOSUPERUSER", joined)
        self.assertIn("NOBYPASSRLS", joined)
        self.assertIn("pg_roles", joined)  # 幂等:存在才不建
        self.assertIn("GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES", joined)


class RlsLocalRoleTests(unittest.TestCase):
    def test_role_identifier_validated(self):
        import os
        from core.db import _rls_local_role

        original = os.environ.get("RLS_ROLE")
        try:
            os.environ["RLS_ROLE"] = "pearnly_app"
            self.assertEqual(_rls_local_role(), "pearnly_app")
            os.environ["RLS_ROLE"] = "bad; DROP TABLE x"  # 非法标识符 → 拒(防注入)
            self.assertEqual(_rls_local_role(), "")
            os.environ["RLS_ROLE"] = ""
            self.assertEqual(_rls_local_role(), "")
        finally:
            if original is None:
                os.environ.pop("RLS_ROLE", None)
            else:
                os.environ["RLS_ROLE"] = original


if __name__ == "__main__":
    unittest.main()
