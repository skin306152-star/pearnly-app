# -*- coding: utf-8 -*-
"""0013_sales_approval 守门测试(静态契约 · 不连库)。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class SalesApprovalMigrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path = os.path.join(ROOT, "alembic", "versions", "0013_sales_approval.py")
        with open(cls.path, "r", encoding="utf-8") as f:
            cls.src = f.read()

    def test_file_present_and_revision_chain(self):
        self.assertTrue(os.path.exists(self.path), "0013 migration missing")
        self.assertIn('revision = "0013_sales_approval"', self.src)
        self.assertIn('down_revision = "0012_sales_price_includes_vat"', self.src)

    def test_adds_columns_idempotent(self):
        for col in ("approved_by", "approved_at", "rejected_reason"):
            self.assertRegex(self.src, rf"ADD COLUMN IF NOT EXISTS {col}\b")

    def test_approved_at_is_timestamptz(self):
        self.assertRegex(self.src, r"approved_at timestamptz")

    def test_downgrade_drops_columns(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.src, re.DOTALL)
        self.assertIsNotNone(m)
        self.assertIn("DROP COLUMN IF EXISTS", m.group(1))
        for col in ("approved_by", "approved_at", "rejected_reason"):
            self.assertIn(f'"{col}"', self.src)


if __name__ == "__main__":
    unittest.main()
