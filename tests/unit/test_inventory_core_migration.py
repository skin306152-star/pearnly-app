# -*- coding: utf-8 -*-
"""0023_inventory_core 守门测试(静态契约 · 不连库)。POS 项目 · PO-A3。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class InventoryCoreMigrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path = os.path.join(ROOT, "alembic", "versions", "0023_inventory_core.py")
        with open(cls.path, "r", encoding="utf-8") as f:
            cls.src = f.read()

    def test_revision_chain(self):
        self.assertIn('revision = "0023_inventory_core"', self.src)
        self.assertIn('down_revision = "0022_product_units_and_flags"', self.src)

    def test_creates_four_tables(self):
        for t in (
            "CREATE TABLE IF NOT EXISTS warehouses",
            "CREATE TABLE IF NOT EXISTS inventory_batches",
            "CREATE TABLE IF NOT EXISTS inventory_stock",
            "CREATE TABLE IF NOT EXISTS inventory_transactions",
        ):
            self.assertIn(t, self.src)

    def test_money_and_qty_types(self):
        # 数量 numeric(14,3) · 钱 numeric(14,2)
        self.assertIn("qty_on_hand numeric(14,3)", self.src)
        self.assertIn("qty_delta numeric(14,3)", self.src)
        self.assertIn("unit_cost numeric(14,2)", self.src)

    def test_immutable_ledger_idempotency_key(self):
        self.assertIn("client_uuid uuid UNIQUE", self.src)

    def test_stock_partial_unique_indexes_for_null_batch(self):
        self.assertIn("uq_stock_batched", self.src)
        self.assertIn("WHERE batch_id IS NOT NULL", self.src)
        self.assertIn("uq_stock_nobatch", self.src)
        self.assertIn("WHERE batch_id IS NULL", self.src)

    def test_fk_types_aligned(self):
        # workspace_client_id/warehouse_id = bigint;product_id/batch_id = uuid
        self.assertIn("workspace_client_id bigint", self.src)
        self.assertIn("warehouse_id bigint", self.src)
        self.assertIn("product_id uuid", self.src)

    def test_rls_on_all_tables(self):
        # 4 张表的 RLS 在 _RLS_TABLES 循环里统一开(f-string 模板)
        self.assertIn("ALTER TABLE {table} ENABLE ROW LEVEL SECURITY", self.src)
        self.assertIn("CREATE POLICY tenant_isolation ON {table}", self.src)
        self.assertRegex(self.src, r"_RLS_TABLES\s*=\s*\([^)]*\"warehouses\"")

    def test_downgrade_drops_all(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.src, re.DOTALL)
        self.assertIsNotNone(m)
        for t in (
            "inventory_transactions",
            "inventory_stock",
            "inventory_batches",
            "warehouses",
        ):
            self.assertIn(f"DROP TABLE IF EXISTS {t}", m.group(1))


if __name__ == "__main__":
    unittest.main()
