# -*- coding: utf-8 -*-
"""0015_sales_promptpay_wht 守门测试(静态契约 · 不连库)。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class SalesPromptPayWhtMigrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path = os.path.join(ROOT, "alembic", "versions", "0015_sales_promptpay_wht.py")
        with open(cls.path, "r", encoding="utf-8") as f:
            cls.src = f.read()

    def test_file_present_and_revision_chain(self):
        self.assertTrue(os.path.exists(self.path), "0015 migration missing")
        self.assertIn('revision = "0015_sales_promptpay_wht"', self.src)
        self.assertIn('down_revision = "0014_sales_pdf_archive"', self.src)

    def test_adds_promptpay_id_on_seller(self):
        self.assertRegex(self.src, r"workspace_clients ADD COLUMN IF NOT EXISTS promptpay_id\b")

    def test_adds_wht_rate_on_document(self):
        self.assertRegex(self.src, r"sales_documents ADD COLUMN IF NOT EXISTS wht_rate\b")

    def test_downgrade_drops_columns(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.src, re.DOTALL)
        self.assertIsNotNone(m)
        self.assertIn("DROP COLUMN IF EXISTS promptpay_id", m.group(1))
        self.assertIn("DROP COLUMN IF EXISTS wht_rate", m.group(1))


if __name__ == "__main__":
    unittest.main()
