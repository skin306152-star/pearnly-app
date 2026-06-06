# -*- coding: utf-8 -*-
"""0018_sales_send 守门测试(静态契约 · 不连库)。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class SalesSendMigrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path = os.path.join(ROOT, "alembic", "versions", "0018_sales_send.py")
        with open(cls.path, "r", encoding="utf-8") as f:
            cls.src = f.read()

    def test_file_present_and_revision_chain(self):
        self.assertTrue(os.path.exists(self.path), "0018 migration missing")
        self.assertIn('revision = "0018_sales_send"', self.src)
        self.assertIn('down_revision = "0017_sales_settings"', self.src)

    def test_adds_share_token_and_seller_email(self):
        self.assertRegex(self.src, r"sales_documents ADD COLUMN IF NOT EXISTS share_token\b")
        self.assertRegex(self.src, r"workspace_clients ADD COLUMN IF NOT EXISTS email\b")

    def test_creates_send_log_table(self):
        self.assertIn("CREATE TABLE IF NOT EXISTS sales_document_sends", self.src)
        for col in ("channel", "identity", "recipient", "status"):
            self.assertIn(col, self.src)

    def test_share_token_unique_index(self):
        self.assertIn("uq_sales_doc_share_token", self.src)

    def test_downgrade_reverses(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.src, re.DOTALL)
        self.assertIsNotNone(m)
        self.assertIn("DROP TABLE IF EXISTS sales_document_sends", m.group(1))
        self.assertIn("DROP COLUMN IF EXISTS share_token", m.group(1))


if __name__ == "__main__":
    unittest.main()
