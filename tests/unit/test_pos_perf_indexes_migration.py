# -*- coding: utf-8 -*-
"""0026_pos_perf_indexes 守门测试(静态契约 · 不连库)。POS 项目 · C2。

锁定:新索引 ix_stock_ws_product 同时进 alembic 0026(迁移链)与 services/inventory/store.py
ensure_schema(prod 走 bootstrap_pos_schema 双跑 · 见 [[pos-pob4-b5-b6-shipped]])。两处缺一 →
要么迁移链断、要么 prod 不生效。"""

import os
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class PerfIndexMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(
            os.path.join(ROOT, "alembic", "versions", "0026_pos_perf_indexes.py"),
            encoding="utf-8",
        ) as f:
            cls.mig = f.read()
        with open(os.path.join(ROOT, "services", "inventory", "store.py"), encoding="utf-8") as f:
            cls.store = f.read()

    def test_revision_chain(self):
        self.assertIn('revision = "0026_pos_perf_indexes"', self.mig)
        self.assertIn('down_revision = "0025_pos_sales"', self.mig)

    def test_migration_creates_index(self):
        self.assertIn("ix_stock_ws_product", self.mig)
        self.assertIn("inventory_stock (tenant_id, workspace_client_id, product_id)", self.mig)
        self.assertIn("DROP INDEX IF EXISTS ix_stock_ws_product", self.mig)

    def test_ensure_schema_double_run_has_index(self):
        # prod 不跑 alembic upgrade(head 停 0020),实际生效靠 ensure_schema 双跑
        self.assertIn("ix_stock_ws_product", self.store)
        self.assertIn("CREATE INDEX IF NOT EXISTS ix_stock_ws_product", self.store)


if __name__ == "__main__":
    unittest.main()
