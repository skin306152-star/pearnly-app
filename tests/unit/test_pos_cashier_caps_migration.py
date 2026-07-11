# -*- coding: utf-8 -*-
"""0068_pos_cashier_caps 守门测试(静态契约 · 不连库)。PC-1a。

钉死:迁移把 caps jsonb 加到 pos_cashiers,且 services/pos/cashier.ensure_core_schema 跑同一
幂等 ADD COLUMN(双跑同源 · prod 无自动迁移)。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class CashierCapsMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(
            os.path.join(ROOT, "alembic", "versions", "0068_pos_cashier_caps.py"), encoding="utf-8"
        ) as f:
            cls.mig = f.read()
        with open(os.path.join(ROOT, "services", "pos", "cashier.py"), encoding="utf-8") as f:
            cls.ensure = f.read()

    def test_revision_chain(self):
        self.assertIn('revision = "0068_pos_cashier_caps"', self.mig)
        self.assertIn('down_revision = "0067_workorder_freeze_evidence"', self.mig)

    def test_adds_caps_jsonb_idempotent(self):
        self.assertIn("ADD COLUMN IF NOT EXISTS caps jsonb NOT NULL DEFAULT '{}'::jsonb", self.mig)

    def test_dual_run_in_ensure_core_schema(self):
        # 与迁移同源的幂等 DDL 必须在 ensure_core_schema 里(prod 靠双跑落列)
        self.assertIn("ADD COLUMN IF NOT EXISTS caps jsonb NOT NULL DEFAULT '{}'::jsonb", self.ensure)

    def test_downgrade_drops_caps(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.mig, re.DOTALL)
        self.assertIsNotNone(m)
        self.assertIn("DROP COLUMN IF EXISTS caps", m.group(1))


if __name__ == "__main__":
    unittest.main()
