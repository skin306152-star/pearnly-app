# -*- coding: utf-8 -*-
"""0069_pos_shift_seq 守门(静态契约 · 不连库)。POS 项目 · PC-3。

钉死连号迁移与 services/pos/cashier.ensure_core_schema 双跑同源:加 shift_seq、每 (tenant,ws)
唯一约束、回填按 opened_at 连号。防删靠连号断裂可见(全仓无 DELETE FROM pos_shifts),故不建物理删。
"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class PosShiftSeqMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(
            os.path.join(ROOT, "alembic", "versions", "0069_pos_shift_seq.py"), encoding="utf-8"
        ) as f:
            cls.mig = f.read()
        with open(os.path.join(ROOT, "services", "pos", "cashier.py"), encoding="utf-8") as f:
            cls.ensure = f.read()

    def test_revision_chain(self):
        self.assertIn('revision = "0069_pos_shift_seq"', self.mig)
        self.assertIn('down_revision = "0068_pos_cashier_caps"', self.mig)

    def test_adds_shift_seq_column_dual_run(self):
        self.assertIn("ADD COLUMN IF NOT EXISTS shift_seq integer", self.mig)
        self.assertIn("ADD COLUMN IF NOT EXISTS shift_seq integer", self.ensure)

    def test_unique_per_tenant_ws_dual_run(self):
        for src in (self.mig, self.ensure):
            self.assertIn("uq_pos_shift_seq", src)
            self.assertIn("(tenant_id, workspace_client_id, shift_seq)", src)

    def test_backfill_orders_by_opened_at(self):
        # 存量回填每 (tenant,ws) 独立连号,按 opened_at 升序(确定序,同秒也不并列)。
        self.assertIn("row_number() OVER", self.mig)
        self.assertIn("PARTITION BY tenant_id, workspace_client_id", self.mig)
        self.assertIn("ORDER BY opened_at", self.mig)
        self.assertIn("WHERE s.id = n.id AND s.shift_seq IS NULL", self.mig)

    def test_downgrade_reverts(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.mig, re.DOTALL)
        self.assertIsNotNone(m)
        self.assertIn("DROP INDEX IF EXISTS uq_pos_shift_seq", m.group(1))
        self.assertIn("DROP COLUMN IF EXISTS shift_seq", m.group(1))


if __name__ == "__main__":
    unittest.main()
