# -*- coding: utf-8 -*-
"""0017_sales_settings 守门测试(静态契约 · 不连库)。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class SalesSettingsMigrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path = os.path.join(ROOT, "alembic", "versions", "0017_sales_settings.py")
        with open(cls.path, "r", encoding="utf-8") as f:
            cls.src = f.read()

    def test_file_present_and_revision_chain(self):
        self.assertTrue(os.path.exists(self.path), "0017 migration missing")
        self.assertIn('revision = "0017_sales_settings"', self.src)
        self.assertIn('down_revision = "0016_sales_seller_brand"', self.src)

    def test_creates_sales_settings_table(self):
        self.assertIn("CREATE TABLE IF NOT EXISTS sales_settings", self.src)
        for col in ("approval_mode", "number_prefix", "number_reset", "number_start"):
            self.assertIn(col, self.src)

    def test_tenant_id_is_primary_key(self):
        self.assertRegex(self.src, r"tenant_id\s+uuid\s+PRIMARY KEY")

    def test_adds_client_buyer_fields(self):
        self.assertRegex(self.src, r"clients ADD COLUMN IF NOT EXISTS \{col\} text")
        for col in ("party_type", "branch", "promptpay_id"):
            self.assertIn(f'"{col}"', self.src)

    def test_downgrade_drops_table_and_columns(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.src, re.DOTALL)
        self.assertIsNotNone(m)
        self.assertIn("DROP TABLE IF EXISTS sales_settings", m.group(1))
        self.assertIn("DROP COLUMN IF EXISTS", m.group(1))


if __name__ == "__main__":
    unittest.main()
