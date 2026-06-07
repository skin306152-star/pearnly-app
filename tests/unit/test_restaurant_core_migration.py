# -*- coding: utf-8 -*-
"""0027_restaurant_core 守门测试(静态契约 · 不连库)。餐厅 POS · PO-R1。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

_TABLES = ("pos_areas", "pos_tables", "pos_table_sessions", "pos_kot", "pos_session_lines")


class RestaurantCoreMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(
            os.path.join(ROOT, "alembic", "versions", "0027_restaurant_core.py"), encoding="utf-8"
        ) as f:
            cls.mig = f.read()
        with open(
            os.path.join(ROOT, "services", "pos", "restaurant", "schema.py"), encoding="utf-8"
        ) as f:
            cls.ensure = f.read()

    def test_revision_chain(self):
        self.assertIn('revision = "0027_restaurant_core"', self.mig)
        self.assertIn('down_revision = "0026_pos_perf_indexes"', self.mig)

    def test_creates_five_tables_in_both(self):
        for t in _TABLES:
            create = f"CREATE TABLE IF NOT EXISTS {t}"
            self.assertIn(create, self.mig, f"迁移缺 {t}")
            self.assertIn(create, self.ensure, f"双跑缺 {t}")

    def test_service_charge_added_in_both(self):
        col = "service_charge numeric(14,2)"
        self.assertIn("ALTER TABLE pos_sales ADD COLUMN IF NOT EXISTS", self.mig)
        self.assertIn(col, self.mig)
        self.assertIn(col, self.ensure)

    def test_money_and_qty_types(self):
        self.assertIn("unit_price numeric(14,2)", self.mig)
        self.assertIn("qty numeric(14,3)", self.mig)
        self.assertIn("unit_factor numeric(14,3)", self.mig)

    def test_one_open_session_per_table(self):
        self.assertIn("uq_table_open", self.mig)
        self.assertIn("WHERE status <> 'closed'", self.mig)

    def test_session_line_links(self):
        self.assertIn("kot_id uuid REFERENCES pos_kot(id)", self.mig)
        self.assertIn("settled_sale_id uuid REFERENCES pos_sales(id)", self.mig)
        self.assertIn("kitchen_status text NOT NULL DEFAULT 'pending'", self.mig)

    def test_rls_on_all_tables(self):
        self.assertIn("ENABLE ROW LEVEL SECURITY", self.mig)
        for t in _TABLES:
            self.assertRegex(self.mig, rf'_RLS_TABLES\s*=\s*\([^)]*"{t}"')

    def test_downgrade_drops_all(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.mig, re.DOTALL)
        for t in _TABLES:
            self.assertIn(f"DROP TABLE IF EXISTS {t}", m.group(1))
        self.assertIn("DROP COLUMN IF EXISTS service_charge", m.group(1))

    def test_bootstrap_double_run_registered(self):
        with open(os.path.join(ROOT, "services", "pos_schema.py"), encoding="utf-8") as f:
            boot = f.read()
        self.assertIn("ensure_restaurant_schema", boot)


if __name__ == "__main__":
    unittest.main()
