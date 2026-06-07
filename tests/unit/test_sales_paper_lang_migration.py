# -*- coding: utf-8 -*-
"""0020_sales_doc_paper_lang 守门测试(静态契约 · 不连库)。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class PaperLangMigrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path = os.path.join(ROOT, "alembic", "versions", "0020_sales_doc_paper_lang.py")
        with open(cls.path, "r", encoding="utf-8") as f:
            cls.src = f.read()

    def test_file_present_and_revision_chain(self):
        self.assertTrue(os.path.exists(self.path), "0020 migration missing")
        self.assertIn('revision = "0020_sales_doc_paper_lang"', self.src)
        self.assertIn('down_revision = "0019_sales_doc_copies_layout"', self.src)

    def test_adds_columns_defaulted(self):
        # 两列都须 IF NOT EXISTS + 默认(向后兼容:旧单据 A4 + th_en = 原行为)。
        self.assertRegex(
            self.src, r"ADD COLUMN IF NOT EXISTS paper_size text NOT NULL DEFAULT 'A4'"
        )
        self.assertRegex(
            self.src, r"ADD COLUMN IF NOT EXISTS doc_language text NOT NULL DEFAULT 'th_en'"
        )

    def test_downgrade_drops_columns(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.src, re.DOTALL)
        self.assertIsNotNone(m)
        self.assertIn("DROP COLUMN IF EXISTS doc_language", m.group(1))
        self.assertIn("DROP COLUMN IF EXISTS paper_size", m.group(1))


if __name__ == "__main__":
    unittest.main()
