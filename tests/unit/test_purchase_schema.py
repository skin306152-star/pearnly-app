# -*- coding: utf-8 -*-
"""采购 schema 双跑对齐闸(docs/purchasing/01 · S1)。

prod 无自动迁移,services/purchase/schema.ensure_purchase_schema 与 alembic 0031-0033 是同一
份 DDL 的两处副本(启动 ensure / 正式迁移)。本测试机械保证两处覆盖同一组表 + 每表 RLS,
任一处漏建/漏隔离 → 红。纯静态扫文本,不连库。
"""

import pathlib
import re
import unittest

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_MIGRATIONS = (
    "alembic/versions/0031_suppliers.py",
    "alembic/versions/0032_purchase_docs.py",
    "alembic/versions/0033_purchase_config.py",
    "alembic/versions/0061_supplier_posting_profiles.py",
)
_ENSURE = "services/purchase/schema.py"

# 现役表(ensure 建·与迁移净结果一致)。
_EXPECTED_TABLES = {
    "suppliers",
    "purchase_docs",
    "purchase_lines",
    "expense_categories",
    "purchase_settings",
    "purchase_attachments",
    "supplier_posting_profiles",  # F4(L2)· 0061
}

# 历史表:0033 建、0040 下线(待归类模块删)。迁移史里有,ensure 不再建。
_DROPPED_TABLES = {"intake_items"}

_CREATE_RE = re.compile(r"CREATE TABLE IF NOT EXISTS\s+(\w+)", re.I)


def _tables_in(path: str) -> set:
    text = (_ROOT / path).read_text(encoding="utf-8")
    return set(_CREATE_RE.findall(text))


class PurchaseSchemaParityTests(unittest.TestCase):
    def test_ensure_covers_all_expected_tables(self):
        self.assertEqual(_tables_in(_ENSURE), _EXPECTED_TABLES)

    def test_migrations_cover_all_expected_tables(self):
        migrated = set()
        for m in _MIGRATIONS:
            migrated |= _tables_in(m)
        self.assertEqual(migrated, _EXPECTED_TABLES | _DROPPED_TABLES)

    def test_every_table_has_rls_in_ensure(self):
        text = (_ROOT / _ENSURE).read_text(encoding="utf-8")
        # ensure 走 apply_tenant_rls(cur, *_RLS_TABLES);校验 7 表全列入 _RLS_TABLES。
        for t in _EXPECTED_TABLES:
            self.assertIn(f'"{t}"', text, f"{t} 未列入 ensure 的 RLS 清单")

    def test_every_table_has_rls_in_migrations(self):
        for m in _MIGRATIONS:
            text = (_ROOT / m).read_text(encoding="utf-8")
            for t in _tables_in(m):
                self.assertIn(f't="{t}"', text, f"{m}:{t} 缺 RLS policy 应用(_RLS.format)")

    def test_payment_method_column_dual_run(self):
        # purchase_docs.payment_method 须 ensure(CREATE/ALTER 自愈)+ alembic 0042 双跑(铁律 #5)。
        ensure = (_ROOT / _ENSURE).read_text(encoding="utf-8")
        self.assertIn("payment_method text", ensure)
        mig = (_ROOT / "alembic/versions/0042_purchase_payment_method.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("payment_method", mig)


if __name__ == "__main__":
    unittest.main()
