# -*- coding: utf-8 -*-
"""0024_pos_core 守门测试(静态契约 · 不连库)。POS 项目 · PO-B1。

钉死迁移与 services/pos/cashier.ensure_core_schema 同源(双跑)的关键约束:表/类型/单 open 班次
约束/RLS/外键对齐。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class PosCoreMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(
            os.path.join(ROOT, "alembic", "versions", "0024_pos_core.py"), encoding="utf-8"
        ) as f:
            cls.mig = f.read()
        with open(os.path.join(ROOT, "services", "pos", "cashier.py"), encoding="utf-8") as f:
            cls.ensure = f.read()

    def test_revision_chain(self):
        self.assertIn('revision = "0024_pos_core"', self.mig)
        self.assertIn('down_revision = "0023_inventory_core"', self.mig)

    def test_creates_three_tables(self):
        for t in (
            "CREATE TABLE IF NOT EXISTS pos_terminals",
            "CREATE TABLE IF NOT EXISTS pos_cashiers",
            "CREATE TABLE IF NOT EXISTS pos_shifts",
        ):
            self.assertIn(t, self.mig)
            self.assertIn(t, self.ensure)

    def test_pin_hash_not_plaintext_column(self):
        self.assertIn("pin_hash text NOT NULL", self.mig)

    def test_single_open_shift_partial_unique(self):
        # 一个终端同时只能一个 open 班次(pos.shift_already_open 的 DB 兜底)
        self.assertIn("uq_pos_shift_open", self.mig)
        self.assertIn("WHERE status = 'open'", self.mig)
        self.assertIn("uq_pos_shift_open", self.ensure)

    def test_money_types(self):
        self.assertIn("opening_float numeric(14,2)", self.mig)
        self.assertIn("cash_diff numeric(14,2)", self.mig)

    def test_fk_types_aligned(self):
        # cashier_id/user_id = uuid;terminal_id/workspace_client_id = bigint
        self.assertIn("cashier_id uuid", self.mig)
        self.assertIn("terminal_id bigint", self.mig)
        self.assertIn("workspace_client_id bigint", self.mig)

    def test_rls_on_all_tables(self):
        self.assertIn("ALTER TABLE {table} ENABLE ROW LEVEL SECURITY", self.mig)
        self.assertRegex(self.mig, r"_RLS_TABLES\s*=\s*\([^)]*\"pos_terminals\"")

    def test_downgrade_drops_all(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.mig, re.DOTALL)
        self.assertIsNotNone(m)
        for t in ("pos_shifts", "pos_cashiers", "pos_terminals"):
            self.assertIn(f"DROP TABLE IF EXISTS {t}", m.group(1))


if __name__ == "__main__":
    unittest.main()
