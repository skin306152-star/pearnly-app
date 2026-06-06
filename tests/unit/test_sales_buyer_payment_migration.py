# -*- coding: utf-8 -*-
"""0009_sales_buyer_and_payment 守门测试(静态契约 · 不连库)。

锁定:
  1. 文件存在 + revision 链(0009 → 0008_sales_seller_fields)
  2. upgrade() 幂等加齐买方块 + parties_snapshot + 收款列(均 ADD COLUMN IF NOT EXISTS)
  3. buyer_tax_id 是单列(一字段三义 · 不为每种买方类型建独立列)
  4. parties_snapshot 是 jsonb(双方冻结)
  5. 钱用 numeric(非 float)· payment_status 带默认
  6. downgrade() 可回滚(DROP COLUMN IF EXISTS 全列)
"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EXPECTED_COLUMNS = (
    "buyer_type",
    "buyer_name",
    "buyer_address",
    "buyer_tax_id",
    "buyer_branch_type",
    "buyer_branch_no",
    "parties_snapshot",
    "payment_status",
    "paid_amount",
    "payment_method",
    "payment_date",
)


class SalesBuyerPaymentMigrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path = os.path.join(ROOT, "alembic", "versions", "0009_sales_buyer_and_payment.py")
        with open(cls.path, "r", encoding="utf-8") as f:
            cls.src = f.read()

    def test_file_present_and_revision_chain(self):
        self.assertTrue(os.path.exists(self.path), "0009 migration missing")
        self.assertIn('revision = "0009_sales_buyer_and_payment"', self.src)
        self.assertIn(
            'down_revision = "0008_sales_seller_fields"',
            self.src,
            "down_revision must chain onto the current head 0008_sales_seller_fields",
        )

    def test_upgrade_adds_all_columns_idempotent(self):
        body = self._upgrade_body()
        for col in EXPECTED_COLUMNS:
            self.assertRegex(
                body,
                rf"ADD COLUMN IF NOT EXISTS {col}\b",
                f"upgrade() must add {col} with IF NOT EXISTS (idempotent)",
            )

    def test_buyer_tax_id_is_single_column(self):
        """一字段三义:不为公司/个人/外国分别建列。"""
        self.assertRegex(self.src, r"buyer_tax_id\s+text")
        for forbidden in ("buyer_national_id", "buyer_passport", "buyer_company_tax_id"):
            self.assertNotIn(forbidden, self.src, f"must not split buyer tax id into {forbidden}")

    def test_parties_snapshot_is_jsonb(self):
        self.assertRegex(
            self.src, r"parties_snapshot\s+jsonb", "double-party freeze must be jsonb (§A)"
        )

    def test_money_is_numeric_and_status_defaulted(self):
        self.assertRegex(self.src, r"paid_amount\s+numeric\(14,2\)", "money must be numeric")
        self.assertNotRegex(self.src, r"paid_amount\s+(float|double|real)")
        # The ADD COLUMN statement is split across two string literals, so assert the
        # column and its default separately rather than as one contiguous run.
        self.assertRegex(self.src, r"payment_status\s+text", "payment_status must be text")
        self.assertIn("NOT NULL DEFAULT 'unpaid'", self.src, "payment_status needs a default")

    def test_no_postgres_rls_policy_in_migration(self):
        self.assertNotIn("CREATE POLICY", self.src)
        self.assertNotIn("ROW LEVEL SECURITY", self.src)

    def test_downgrade_drops_all_columns(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.src, re.DOTALL)
        self.assertIsNotNone(m, "downgrade() not found")
        body = m.group(1)
        self.assertIn("DROP COLUMN IF EXISTS", body)
        self.assertIn("for col in _DOC_COLUMNS", body, "downgrade() must iterate _DOC_COLUMNS")
        m_const = re.search(r"_DOC_COLUMNS\s*=\s*\((.*?)\)", self.src, re.DOTALL)
        self.assertIsNotNone(m_const, "_DOC_COLUMNS constant not found")
        const = m_const.group(1)
        for col in EXPECTED_COLUMNS:
            self.assertIn(col, const, f"_DOC_COLUMNS must list {col}")

    def _upgrade_body(self):
        m = re.search(r"def upgrade\(\)[^:]*:(.*?)\ndef downgrade", self.src, re.DOTALL)
        self.assertIsNotNone(m, "upgrade() not found")
        return m.group(1)


if __name__ == "__main__":
    unittest.main()
