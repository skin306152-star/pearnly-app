# -*- coding: utf-8 -*-
"""0011_sales_terms 守门测试(静态契约 · 不连库)。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class SalesTermsMigrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path = os.path.join(ROOT, "alembic", "versions", "0011_sales_terms.py")
        with open(cls.path, "r", encoding="utf-8") as f:
            cls.src = f.read()

    def test_revision_chain(self):
        self.assertIn('revision = "0011_sales_terms"', self.src)
        self.assertIn('down_revision = "0010_sales_discount"', self.src)

    def test_adds_columns_idempotent(self):
        for col in ("due_date", "payment_terms"):
            self.assertRegex(self.src, rf"ADD COLUMN IF NOT EXISTS {col}\b")

    def test_downgrade_drops_columns(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.src, re.DOTALL)
        self.assertIsNotNone(m)
        self.assertIn("DROP COLUMN IF EXISTS", m.group(1))
        for col in ("due_date", "payment_terms"):
            self.assertIn(f'"{col}"', self.src)


if __name__ == "__main__":
    unittest.main()
