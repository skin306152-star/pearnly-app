# -*- coding: utf-8 -*-
"""销项模块 PO-1 · Alembic 0006_sales_core 守门测试(静态契约 · 不连库)。

锁定:
  1. 文件存在 + revision 链(0006_sales_core → 0005_invoice_risk_checks)
  2. upgrade() 幂等建齐 6 张表(均 CREATE TABLE IF NOT EXISTS)
  3. client_id 是 BIGINT(匹配 clients.id BIGSERIAL · 非 draft 的 UUID)
  4. 每张业务表带 tenant_id(app 层 RLS 隔离前提)
  5. 迁移内不写 Postgres RLS policy(仓库靠 get_cursor_rls + DAL · 非迁移建 policy)
  6. downgrade() 可回滚(DROP TABLE IF EXISTS 全表)
"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EXPECTED_TABLES = (
    "products",
    "document_number_sequences",
    "sales_documents",
    "sales_document_lines",
    "etax_submissions",
    "etax_channel_settings",
)


class SalesCoreMigrationContractTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path = os.path.join(ROOT, "alembic", "versions", "0006_sales_core.py")
        with open(cls.path, "r", encoding="utf-8") as f:
            cls.src = f.read()

    def test_file_present_and_revision_chain(self):
        self.assertTrue(os.path.exists(self.path), "0006_sales_core migration missing")
        self.assertIn('revision = "0006_sales_core"', self.src)
        self.assertIn(
            'down_revision = "0005_invoice_risk_checks"',
            self.src,
            "down_revision must chain onto the current head 0005_invoice_risk_checks",
        )

    def test_upgrade_creates_all_tables_idempotent(self):
        m = re.search(r"def upgrade\(\)[^:]*:(.*?)\ndef downgrade", self.src, re.DOTALL)
        self.assertIsNotNone(m, "upgrade() not found")
        body = m.group(1)
        for table in EXPECTED_TABLES:
            self.assertIn(
                f"CREATE TABLE IF NOT EXISTS {table}",
                body,
                f"upgrade() must create {table} with IF NOT EXISTS (idempotent)",
            )

    def test_client_id_is_bigint_not_uuid(self):
        """clients.id 是 BIGSERIAL → client_id 必须 bigint,否则 FK 建不上。"""
        self.assertRegex(
            self.src,
            r"client_id\s+bigint",
            "client_id must be bigint to match clients.id (BIGSERIAL)",
        )
        self.assertNotRegex(
            self.src, r"client_id\s+uuid", "client_id must not stay UUID (the draft placeholder)"
        )

    def test_business_tables_carry_tenant_id(self):
        for table in ("products", "sales_documents", "sales_document_lines", "etax_submissions"):
            block = self._table_block(table)
            self.assertRegex(
                block, r"tenant_id\s+uuid", f"{table} must carry tenant_id uuid for isolation"
            )

    def test_no_postgres_rls_policy_in_migration(self):
        """仓库隔离靠 get_cursor_rls + DAL · 迁移不建 policy(与知识库迁移一致)。"""
        self.assertNotIn("CREATE POLICY", self.src)
        self.assertNotIn("ROW LEVEL SECURITY", self.src)

    def test_downgrade_drops_all_tables(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.src, re.DOTALL)
        self.assertIsNotNone(m, "downgrade() not found")
        body = m.group(1)
        self.assertIn("DROP TABLE IF EXISTS", body)
        # downgrade 走 _TABLES loop(表名在模块级常量)· 验 loop 引用 + 常量列全表
        self.assertIn("for table in _TABLES", body, "downgrade() must iterate _TABLES")
        m_const = re.search(r"_TABLES\s*=\s*\((.*?)\)", self.src, re.DOTALL)
        self.assertIsNotNone(m_const, "_TABLES constant not found")
        const = m_const.group(1)
        for table in EXPECTED_TABLES:
            self.assertIn(table, const, f"_TABLES must list {table}")

    def _table_block(self, table):
        m = re.search(
            rf"CREATE TABLE IF NOT EXISTS {table} \((.*?)\n        \)", self.src, re.DOTALL
        )
        self.assertIsNotNone(m, f"{table} block not found")
        return m.group(1)


if __name__ == "__main__":
    unittest.main()
