# -*- coding: utf-8 -*-
"""0063_pos_entitlements 守门测试(静态契约 · 不连库)。PS-3。

钉死:迁移与 services/pos/entitlements.ensure_pos_entitlement_schema 双跑同源;一租户一行唯一;
授权码全局唯一;RLS;credit_transactions.type 放宽收下 pos_buyout(与 credits_schema 权威约束同步);
可升可降。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


class PosEntitlementMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mig = _read("alembic", "versions", "0063_pos_entitlements.py")
        cls.ensure = _read("services", "pos", "entitlements.py")
        cls.credits = _read("services", "billing", "credits_schema.py")

    def test_revision_chain(self):
        self.assertIn('revision = "0063_pos_entitlements"', self.mig)
        self.assertIn('down_revision = "0062_pos_sale_line_cost"', self.mig)

    def test_table_created_both_places(self):
        needle = "CREATE TABLE IF NOT EXISTS pos_entitlements"
        self.assertIn(needle, self.mig)
        self.assertIn(needle, self.ensure)

    def test_one_row_per_tenant_unique(self):
        for src in (self.mig, self.ensure):
            self.assertIn("UNIQUE (tenant_id)", src)

    def test_grant_code_globally_unique(self):
        for src in (self.mig, self.ensure):
            self.assertIn("uq_pos_entitlement_code", src)
            self.assertIn("ON pos_entitlements (grant_code)", src)

    def test_money_is_numeric_not_float(self):
        for src in (self.mig, self.ensure):
            self.assertIn("amount_paid_thb numeric(12,2)", src)

    def test_status_state_machine_check(self):
        for src in (self.mig, self.ensure):
            self.assertIn("CHECK (status IN ('active','revoked','transferred'))", src)

    def test_rls_enabled(self):
        self.assertIn("ENABLE ROW LEVEL SECURITY", self.mig)
        self.assertIn('apply_tenant_rls(cur, "pos_entitlements")', self.ensure)

    def test_ct_check_widened_to_pos_buyout_both_sources(self):
        # 迁移放开 + credits_schema 权威约束都必须含 pos_buyout(两处不同步会被启动 DROP+ADD 覆盖回退)。
        self.assertIn("pos_buyout", self.mig)
        self.assertIn(
            "CHECK (type IN ('topup','usage','adjustment','subscription','pos_buyout'))",
            self.credits,
        )

    def test_downgrade_drops_table(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.mig, re.DOTALL)
        self.assertIsNotNone(m)
        self.assertIn("DROP TABLE IF EXISTS pos_entitlements", m.group(1))


if __name__ == "__main__":
    unittest.main()
