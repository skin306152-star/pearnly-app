# -*- coding: utf-8 -*-
"""0012_sales_price_includes_vat 守门测试(静态契约 · 不连库)。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class SalesPriceIncludesVatMigrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path = os.path.join(ROOT, "alembic", "versions", "0012_sales_price_includes_vat.py")
        with open(cls.path, "r", encoding="utf-8") as f:
            cls.src = f.read()

    def test_file_present_and_revision_chain(self):
        self.assertTrue(os.path.exists(self.path), "0012 migration missing")
        self.assertIn('revision = "0012_sales_price_includes_vat"', self.src)
        self.assertIn('down_revision = "0011_sales_terms"', self.src)

    def test_adds_column_idempotent(self):
        self.assertRegex(self.src, r"ADD COLUMN IF NOT EXISTS price_includes_vat\b")

    def test_is_boolean_defaulted(self):
        self.assertIn("boolean NOT NULL DEFAULT false", self.src)

    def test_downgrade_drops_column(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.src, re.DOTALL)
        self.assertIsNotNone(m)
        self.assertIn("DROP COLUMN IF EXISTS", m.group(1))
        self.assertIn('"price_includes_vat"', self.src)


if __name__ == "__main__":
    unittest.main()
