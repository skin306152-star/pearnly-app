# -*- coding: utf-8 -*-
"""0022_product_units_and_flags 守门测试(静态契约 · 不连库)。POS 项目 · PO-A2。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class ProductUnitsMigrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path = os.path.join(ROOT, "alembic", "versions", "0022_product_units_and_flags.py")
        with open(cls.path, "r", encoding="utf-8") as f:
            cls.src = f.read()

    def test_revision_chain(self):
        self.assertIn('revision = "0022_product_units_and_flags"', self.src)
        self.assertIn('down_revision = "0021_tenant_modules"', self.src)

    def test_adds_six_product_columns_defaulted(self):
        for col, typ in (
            ("base_unit", "text NOT NULL DEFAULT 'ชิ้น'"),
            ("track_batch", "boolean NOT NULL DEFAULT FALSE"),
            ("track_expiry", "boolean NOT NULL DEFAULT FALSE"),
            ("is_weighed", "boolean NOT NULL DEFAULT FALSE"),
            ("min_stock", "numeric(14,3)"),
            ("default_cost", "numeric(14,2)"),
        ):
            self.assertIn(f"ADD COLUMN IF NOT EXISTS {col} {typ}", self.src)

    def test_creates_product_units_table(self):
        self.assertIn("CREATE TABLE IF NOT EXISTS product_units", self.src)
        self.assertIn("factor_to_base numeric(14,3) NOT NULL", self.src)
        self.assertIn("price numeric(14,2)", self.src)
        self.assertIn("REFERENCES products(id) ON DELETE CASCADE", self.src)
        self.assertRegex(self.src, r"UNIQUE\s*\(tenant_id,\s*product_id,\s*unit_name\)")

    def test_enables_rls_with_policy(self):
        self.assertIn("ENABLE ROW LEVEL SECURITY", self.src)
        self.assertIn("CREATE POLICY tenant_isolation ON product_units", self.src)
        self.assertIn("WITH CHECK (", self.src)

    def test_downgrade_drops_table_and_columns(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.src, re.DOTALL)
        self.assertIsNotNone(m)
        self.assertIn("DROP TABLE IF EXISTS product_units", m.group(1))
        # 6 列在 _DROP_COLS 元组里循环 DROP COLUMN IF EXISTS {col}
        self.assertIn("DROP COLUMN IF EXISTS {col}", m.group(1))
        self.assertRegex(self.src, r"_DROP_COLS\s*=\s*\([^)]*\"base_unit\"")


if __name__ == "__main__":
    unittest.main()
