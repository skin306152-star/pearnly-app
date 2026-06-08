# -*- coding: utf-8 -*-
"""product_units workspace_client_id 迁移一致性守门(POS-RO-001 · 静态契约 · 不连库)。

修复点:0022/ensure 历来漏建 workspace_client_id,而 DAL 全列读写 → 新库一碰多单位即 500。
本测试锁:① 新迁移 0030 补列+回填+NOT NULL ② ensure_schema 同源(建表带列 + 幂等补列回填)
③ DAL 全程按 ws 过滤。任一处回退即红(防"迁移与运行时再次漂移")。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


class ProductUnitsWorkspaceMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mig = _read("alembic", "versions", "0030_product_units_workspace_client_id.py")
        cls.units = _read("services", "products", "units.py")

    def test_revision_chain(self):
        self.assertIn('revision = "0030_product_units_workspace_client_id"', self.mig)
        self.assertIn('down_revision = "0029_pos_payment_settings"', self.mig)

    def test_migration_adds_backfills_and_locks_column(self):
        self.assertIn("ADD COLUMN IF NOT EXISTS workspace_client_id", self.mig)
        # 回填取自归属商品(products.workspace_client_id),再收 NOT NULL。
        self.assertRegex(self.mig, r"UPDATE product_units[\s\S]*FROM products")
        self.assertIn("SET NOT NULL", self.mig)

    def test_downgrade_drops_column(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.mig, re.DOTALL)
        self.assertIsNotNone(m)
        self.assertIn("DROP COLUMN IF EXISTS workspace_client_id", m.group(1))

    def test_ensure_schema_consistent_with_migration(self):
        # 全新库建表即带列(NOT NULL)+ 老库幂等补列 + 回填(双跑与迁移同源)。
        self.assertIn("workspace_client_id bigint NOT NULL", self.units)
        self.assertIn("ADD COLUMN IF NOT EXISTS workspace_client_id", self.units)
        self.assertRegex(self.units, r"UPDATE product_units[\s\S]*FROM products")

    def test_dal_filters_by_workspace(self):
        # list/get/create/update/delete 全部按 workspace_client_id 过滤(≥5 处)。
        self.assertGreaterEqual(self.units.count("workspace_client_id = %s"), 5)


if __name__ == "__main__":
    unittest.main()
