# -*- coding: utf-8 -*-
"""0021_tenant_modules 守门测试(静态契约 · 不连库)。POS 项目 · PO-A1。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TenantModulesMigrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path = os.path.join(ROOT, "alembic", "versions", "0021_tenant_modules.py")
        with open(cls.path, "r", encoding="utf-8") as f:
            cls.src = f.read()

    def test_file_present_and_revision_chain(self):
        self.assertTrue(os.path.exists(self.path), "0021 migration missing")
        self.assertIn('revision = "0021_tenant_modules"', self.src)
        self.assertIn('down_revision = "0020_sales_doc_paper_lang"', self.src)

    def test_creates_table_idempotent_with_unique(self):
        self.assertIn("CREATE TABLE IF NOT EXISTS tenant_modules", self.src)
        self.assertIn("tenant_id uuid NOT NULL", self.src)
        self.assertIn("module_key text NOT NULL", self.src)
        self.assertIn("config jsonb NOT NULL DEFAULT '{}'::jsonb", self.src)
        self.assertRegex(self.src, r"UNIQUE\s*\(tenant_id,\s*module_key\)")

    def test_enables_rls_with_tenant_policy(self):
        self.assertIn("ENABLE ROW LEVEL SECURITY", self.src)
        self.assertIn("CREATE POLICY tenant_isolation ON tenant_modules", self.src)
        # policy 同时含 USING + WITH CHECK(读写两端都隔离)
        self.assertIn("USING (", self.src)
        self.assertIn("WITH CHECK (", self.src)
        self.assertIn("current_setting('app.current_tenant_id', true)", self.src)

    def test_downgrade_drops_policy_and_table(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.src, re.DOTALL)
        self.assertIsNotNone(m)
        self.assertIn("DROP POLICY IF EXISTS tenant_isolation ON tenant_modules", m.group(1))
        self.assertIn("DROP TABLE IF EXISTS tenant_modules", m.group(1))


if __name__ == "__main__":
    unittest.main()
