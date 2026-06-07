# -*- coding: utf-8 -*-
"""0025_pos_sales 守门测试(静态契约 · 不连库)。POS 项目 · PO-B2。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class PosSalesMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(
            os.path.join(ROOT, "alembic", "versions", "0025_pos_sales.py"), encoding="utf-8"
        ) as f:
            cls.mig = f.read()
        with open(os.path.join(ROOT, "services", "pos", "sales_store.py"), encoding="utf-8") as f:
            cls.ensure = f.read()

    def test_revision_chain(self):
        self.assertIn('revision = "0025_pos_sales"', self.mig)
        self.assertIn('down_revision = "0024_pos_core"', self.mig)

    def test_creates_three_tables_in_both(self):
        for t in (
            "CREATE TABLE IF NOT EXISTS pos_sales",
            "CREATE TABLE IF NOT EXISTS pos_sale_lines",
            "CREATE TABLE IF NOT EXISTS pos_payments",
        ):
            self.assertIn(t, self.mig)
            self.assertIn(t, self.ensure)

    def test_idempotency_key_unique(self):
        self.assertIn("client_uuid uuid UNIQUE", self.mig)

    def test_money_and_qty_types(self):
        self.assertIn("grand_total numeric(14,2)", self.mig)
        self.assertIn("qty_base numeric(14,3)", self.mig)
        self.assertIn("unit_factor numeric(14,3)", self.mig)

    def test_refund_links_back_to_line(self):
        self.assertIn("refund_of_line_id uuid", self.mig)
        self.assertIn("refund_of_sale_id uuid", self.mig)

    def test_rls_on_all_tables(self):
        self.assertIn("ALTER TABLE {table} ENABLE ROW LEVEL SECURITY", self.mig)
        self.assertRegex(self.mig, r"_RLS_TABLES\s*=\s*\([^)]*\"pos_sales\"")

    def test_downgrade_drops_all(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.mig, re.DOTALL)
        for t in ("pos_payments", "pos_sale_lines", "pos_sales"):
            self.assertIn(f"DROP TABLE IF EXISTS {t}", m.group(1))


if __name__ == "__main__":
    unittest.main()
