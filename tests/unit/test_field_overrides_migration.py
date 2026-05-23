# -*- coding: utf-8 -*-
"""
P1.1 BUG-FIX-P1.1 v118.35.0.41 · 守门测试 · Alembic 002 + ensure_field_overrides_columns

锁定 5 个契约:
  1. Alembic 002 migration 文件存在 + revision 链正确(002 → down_revision=001_baseline)
  2. upgrade() 含 4 表 ADD COLUMN field_overrides JSONB
  3. downgrade() 含 4 表 DROP COLUMN field_overrides
  4. ensure_field_overrides_columns() 函数定义存在 + 4 表都在 TARGET_TABLES
  5. app.py 启动钩子已注册 ensure_field_overrides_columns(防 deploy 时漏跑)
"""
import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class FieldOverridesMigrationContractTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.migration_path = os.path.join(
            ROOT, "alembic", "versions", "002_field_overrides_4_modules.py"
        )
        cls.service_path = os.path.join(
            ROOT, "services", "db_migrations", "field_overrides.py"
        )
        with open(cls.migration_path, "r", encoding="utf-8") as f:
            cls.migration_src = f.read()
        with open(cls.service_path, "r", encoding="utf-8") as f:
            cls.service_src = f.read()
        with open(os.path.join(ROOT, "app.py"), "r", encoding="utf-8") as f:
            cls.app_src = f.read()

    # 4 模块表 · 必须全覆盖
    EXPECTED_TABLES = ("ocr_history", "reconciliation_row", "gl_vat_tasks", "bank_recon_v2_tasks")

    def test_alembic_002_file_present_and_revision_chain_correct(self):
        """P1.1 契约 1 · 002 文件存在 + revision = 002 + down_revision = 001_baseline"""
        self.assertTrue(os.path.exists(self.migration_path),
            "Alembic 002 migration file missing")
        m_rev = re.search(r'revision:\s*str\s*=\s*"([^"]+)"', self.migration_src)
        self.assertIsNotNone(m_rev, "revision = ... not declared")
        self.assertEqual(m_rev.group(1), "002_field_overrides_4_modules")
        # down_revision 必须指向 baseline(链不能断)
        self.assertIn('down_revision: Union[str, Sequence[str], None] = "001_baseline"',
            self.migration_src,
            "down_revision must point to 001_baseline (Alembic version chain)")

    def test_upgrade_adds_4_columns(self):
        """P1.1 契约 2 · upgrade() 含 4 表的 ADD COLUMN field_overrides JSONB
        允许 2 种格式:直接 SQL 或 _TABLES = [...] loop · 都要 4 表全到 + ADD COLUMN IF NOT EXISTS
        """
        # 找 _TABLES list(loop 形式) OR upgrade body 含表名(直接形式)
        # 先看 _TABLES 列表
        m_tables = re.search(r'_TABLES\s*=\s*\[([^\]]+)\]', self.migration_src)
        if m_tables:
            tables_in_list = m_tables.group(1)
            for table in self.EXPECTED_TABLES:
                self.assertIn(table, tables_in_list,
                    f"_TABLES list must include {table}")
        else:
            # 没 _TABLES 则要求 upgrade body 直接含 4 表
            m = re.search(r'def upgrade\(\)[^:]*:\s*(.*?)(?=\ndef downgrade)', self.migration_src, re.DOTALL)
            self.assertIsNotNone(m, "upgrade() function not found")
            for table in self.EXPECTED_TABLES:
                self.assertIn(table, m.group(1),
                    f"upgrade() must add field_overrides to {table}")
        # ADD COLUMN IF NOT EXISTS · 保 idempotent(在文件任何位置都行)
        self.assertIn("ADD COLUMN IF NOT EXISTS field_overrides JSONB", self.migration_src,
            "Alembic 002 must use ADD COLUMN IF NOT EXISTS field_overrides JSONB (idempotent)")

    def test_downgrade_drops_4_columns(self):
        """P1.1 契约 3 · downgrade() 含 DROP COLUMN(支持 alembic downgrade -1 回滚)
        允许 loop 形式 · 表名来自 _TABLES 共享列表
        """
        m = re.search(r'def downgrade\(\)[^:]*:\s*(.*)', self.migration_src, re.DOTALL)
        self.assertIsNotNone(m, "downgrade() function not found")
        downgrade_body = m.group(1)
        # downgrade 走 _TABLES loop · 至少要 reference _TABLES 或 4 表全列
        loop_form = "for table in _TABLES" in downgrade_body or "_TABLES" in downgrade_body
        direct_form = all(table in downgrade_body for table in self.EXPECTED_TABLES)
        self.assertTrue(loop_form or direct_form,
            "downgrade() must reference _TABLES loop OR list all 4 tables directly")
        self.assertIn("DROP COLUMN IF EXISTS field_overrides", downgrade_body,
            "downgrade() must use DROP COLUMN IF EXISTS (idempotent)")

    def test_ensure_function_defined_with_all_4_tables(self):
        """P1.1 契约 4 · ensure_field_overrides_columns() 定义 + 4 表全在 TARGET_TABLES"""
        self.assertIn("def ensure_field_overrides_columns", self.service_src,
            "ensure_field_overrides_columns function missing in services/db_migrations/field_overrides.py")
        # TARGET_TABLES 必须含 4 个
        for table in self.EXPECTED_TABLES:
            self.assertIn(f'"{table}"', self.service_src,
                f"TARGET_TABLES must include {table}")
        # ALTER TABLE + ADD COLUMN IF NOT EXISTS field_overrides JSONB
        self.assertIn("ADD COLUMN IF NOT EXISTS field_overrides JSONB", self.service_src,
            "ensure function must use ADD COLUMN IF NOT EXISTS field_overrides JSONB")
        # 防误删铁律 #21 注释(便携)
        self.assertIn("铁律 #21", self.service_src,
            "service module must reference 铁律 #21 (not in db.py · independent module)")

    def test_app_py_startup_hook_calls_ensure(self):
        """P1.1 契约 5 · app.py 启动钩子已 import + 调 ensure_field_overrides_columns
        防 prod deploy 后漏跑 ensure · 老 task 表没 field_overrides 列 · 后续 P1.2+ 写时挂
        """
        self.assertIn(
            "from services.db_migrations.field_overrides import ensure_field_overrides_columns",
            self.app_src,
            "app.py startup must import ensure_field_overrides_columns")
        # 找 import 之后必须有调用
        idx = self.app_src.find("from services.db_migrations.field_overrides import ensure_field_overrides_columns")
        self.assertGreater(idx, 0)
        nearby = self.app_src[idx:idx + 200]
        self.assertIn("ensure_field_overrides_columns()", nearby,
            "app.py must call ensure_field_overrides_columns() after import in startup")


if __name__ == "__main__":
    unittest.main()
