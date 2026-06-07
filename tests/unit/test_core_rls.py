# -*- coding: utf-8 -*-
"""core.rls 单一来源 RLS helper 守门测试(POS 项目 · simplify 收口)。

锁定:apply_tenant_rls 对每表发 ENABLE RLS + DROP POLICY IF EXISTS + CREATE POLICY,且谓词
含 app.current_tenant_id + bypass_rls(USING + WITH CHECK 两端)。这是 3 个 ensure_* 共用的
唯一定义,改这里=全部生效。
"""

import unittest

from core.rls import apply_tenant_rls


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


if __name__ == "__main__":
    unittest.main()
