# -*- coding: utf-8 -*-
"""0014_sales_pdf_archive 守门测试(静态契约 · 不连库)。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class SalesPdfArchiveMigrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path = os.path.join(ROOT, "alembic", "versions", "0014_sales_pdf_archive.py")
        with open(cls.path, "r", encoding="utf-8") as f:
            cls.src = f.read()

    def test_file_present_and_revision_chain(self):
        self.assertTrue(os.path.exists(self.path), "0014 migration missing")
        self.assertIn('revision = "0014_sales_pdf_archive"', self.src)
        self.assertIn('down_revision = "0013_sales_approval"', self.src)

    def test_adds_columns_idempotent(self):
        for col in ("pdf_sha256", "pdf_url"):
            self.assertRegex(self.src, rf"ADD COLUMN IF NOT EXISTS {col}\b")

    def test_downgrade_drops_columns(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.src, re.DOTALL)
        self.assertIsNotNone(m)
        self.assertIn("DROP COLUMN IF EXISTS", m.group(1))
        for col in ("pdf_sha256", "pdf_url"):
            self.assertIn(f'"{col}"', self.src)


if __name__ == "__main__":
    unittest.main()
