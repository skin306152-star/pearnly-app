# -*- coding: utf-8 -*-
"""0019_sales_doc_copies_layout 守门测试(静态契约 · 不连库)。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class CopiesLayoutMigrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path = os.path.join(ROOT, "alembic", "versions", "0019_sales_doc_copies_layout.py")
        with open(cls.path, "r", encoding="utf-8") as f:
            cls.src = f.read()

    def test_file_present_and_revision_chain(self):
        self.assertTrue(os.path.exists(self.path), "0019 migration missing")
        self.assertIn('revision = "0019_sales_doc_copies_layout"', self.src)
        self.assertIn('down_revision = "0018_sales_send"', self.src)

    def test_adds_copies_layout_column_defaulted(self):
        # 必须 IF NOT EXISTS + 有默认(向后兼容,旧单据回落 separate)。
        self.assertRegex(
            self.src,
            r"ADD COLUMN IF NOT EXISTS copies_layout text NOT NULL DEFAULT 'separate'",
        )

    def test_downgrade_drops_column(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.src, re.DOTALL)
        self.assertIsNotNone(m)
        self.assertIn("DROP COLUMN IF EXISTS copies_layout", m.group(1))


if __name__ == "__main__":
    unittest.main()
