# -*- coding: utf-8 -*-
"""销项 PO-5 · Alembic 0007 引用列迁移守门(静态契约)。"""

import os
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class SalesRefMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(
            os.path.join(ROOT, "alembic", "versions", "0007_sales_doc_reference.py"),
            encoding="utf-8",
        ) as f:
            cls.src = f.read()

    def test_revision_chain(self):
        self.assertIn('revision = "0007_sales_doc_reference"', self.src)
        self.assertIn('down_revision = "0006_sales_core"', self.src)

    def test_adds_reference_columns_idempotent(self):
        self.assertIn("ADD COLUMN IF NOT EXISTS references_document_id uuid", self.src)
        self.assertIn("ADD COLUMN IF NOT EXISTS reference_reason text", self.src)

    def test_downgrade_drops_columns(self):
        self.assertIn("DROP COLUMN IF EXISTS", self.src)


if __name__ == "__main__":
    unittest.main()
