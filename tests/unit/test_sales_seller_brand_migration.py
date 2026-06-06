# -*- coding: utf-8 -*-
"""0016_sales_seller_brand 守门测试(静态契约 · 不连库)。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class SalesSellerBrandMigrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path = os.path.join(ROOT, "alembic", "versions", "0016_sales_seller_brand.py")
        with open(cls.path, "r", encoding="utf-8") as f:
            cls.src = f.read()

    def test_file_present_and_revision_chain(self):
        self.assertTrue(os.path.exists(self.path), "0016 migration missing")
        self.assertIn('revision = "0016_sales_seller_brand"', self.src)
        self.assertIn('down_revision = "0015_sales_promptpay_wht"', self.src)

    def test_adds_brand_columns_idempotent(self):
        for col in (
            "template_id",
            "brand_color",
            "logo_url",
            "seal_url",
            "signature_url",
            "footer_text",
        ):
            self.assertIn(col, self.src)
        self.assertIn("ADD COLUMN IF NOT EXISTS", self.src)

    def test_targets_workspace_clients(self):
        self.assertIn("ALTER TABLE workspace_clients", self.src)

    def test_downgrade_drops_columns(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.src, re.DOTALL)
        self.assertIsNotNone(m)
        self.assertIn("DROP COLUMN IF EXISTS", m.group(1))


if __name__ == "__main__":
    unittest.main()
