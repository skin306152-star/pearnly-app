# -*- coding: utf-8 -*-
"""0010_sales_discount 守门测试(静态契约 · 不连库)。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class SalesDiscountMigrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path = os.path.join(ROOT, "alembic", "versions", "0010_sales_discount.py")
        with open(cls.path, "r", encoding="utf-8") as f:
            cls.src = f.read()

    def test_file_present_and_revision_chain(self):
        self.assertTrue(os.path.exists(self.path), "0010 migration missing")
        self.assertIn('revision = "0010_sales_discount"', self.src)
        self.assertIn('down_revision = "0009_sales_buyer_and_payment"', self.src)

    def test_adds_columns_idempotent(self):
        for col in ("discount_pct", "header_discount_amount", "header_discount_pct"):
            self.assertRegex(
                self.src, rf"ADD COLUMN IF NOT EXISTS {col}\b", f"must add {col} idempotently"
            )

    def test_money_is_numeric(self):
        # ADD COLUMN 语句跨两段字符串字面量,分开断言列名与类型(numeric(14,2) 唯一属它)。
        self.assertIn("header_discount_amount", self.src)
        self.assertIn("numeric(14,2)", self.src)
        self.assertNotRegex(self.src, r"header_discount_amount\s+(float|double|real)")

    def test_downgrade_drops_columns(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.src, re.DOTALL)
        self.assertIsNotNone(m)
        body = m.group(1)
        self.assertIn("DROP COLUMN IF EXISTS", body)
        self.assertIn("for col in _DOC_COLUMNS", body)
        self.assertIn("for col in _LINE_COLUMNS", body)
        # 列名落在模块级常量(downgrade 走 loop),断言常量覆盖三列。
        consts = self.src
        for col in ("discount_pct", "header_discount_amount", "header_discount_pct"):
            self.assertIn(f'"{col}"', consts, f"_*_COLUMNS must list {col}")


if __name__ == "__main__":
    unittest.main()
