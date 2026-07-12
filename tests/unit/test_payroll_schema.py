# -*- coding: utf-8 -*-
"""工资进料 schema 双跑对齐闸(ensure_payroll_schema 与 alembic 0072 同一份 DDL)。

纯静态扫文本不连库(照 test_tax_profile_schema 配方):两处覆盖同组表 + 每表 RLS + 迁移带
downgrade,任一处漏建/漏隔离 → 红。
"""

import pathlib
import re
import unittest

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_MIGRATION = "alembic/versions/0072_client_payroll.py"
_ENSURE = "services/payroll/schema.py"

_EXPECTED_TABLES = {"client_payroll_templates", "client_payroll_rows"}
_CREATE_RE = re.compile(r"CREATE TABLE IF NOT EXISTS\s+(\w+)", re.I)


def _text(path: str) -> str:
    return (_ROOT / path).read_text(encoding="utf-8")


def _tables_in(path: str) -> set:
    return set(_CREATE_RE.findall(_text(path)))


class PayrollSchemaParityTests(unittest.TestCase):
    def test_ensure_covers_expected_tables(self):
        self.assertEqual(_tables_in(_ENSURE), _EXPECTED_TABLES)

    def test_migration_covers_expected_tables(self):
        self.assertEqual(_tables_in(_MIGRATION), _EXPECTED_TABLES)

    def test_both_tables_have_rls_in_ensure(self):
        text = _text(_ENSURE)
        for t in _EXPECTED_TABLES:
            self.assertIn(f'"{t}"', text, f"{t} 未列入 ensure RLS 清单")

    def test_both_tables_have_rls_in_migration(self):
        text = _text(_MIGRATION)
        for t in _EXPECTED_TABLES:
            self.assertIn(f't="{t}"', text, f"{t} 缺 RLS policy(_RLS.format)")

    def test_migration_down_revision_points_to_actual_head(self):
        self.assertIn('down_revision = "0071_pos_client_uuid_scope"', _text(_MIGRATION))

    def test_migration_has_matching_downgrade(self):
        text = _text(_MIGRATION)
        for t in _EXPECTED_TABLES:
            self.assertIn(f"DROP TABLE IF EXISTS {t}", text)

    def test_amounts_are_numeric_not_float(self):
        for path in (_ENSURE, _MIGRATION):
            self.assertIn("paid_amount         numeric(15,2)", _text(path))
            self.assertIn("wht_amount          numeric(15,2)", _text(path))

    def test_period_index_present_both_sides(self):
        needle = "ON client_payroll_rows (tenant_id, workspace_client_id, period)"
        self.assertIn(needle, _text(_ENSURE))
        self.assertIn(needle, _text(_MIGRATION))


if __name__ == "__main__":
    unittest.main()
