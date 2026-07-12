# -*- coding: utf-8 -*-
"""科目桥 schema 双跑对齐闸(ensure_coa_erp_bridge_schema 与 alembic 0073 同一份 DDL)。

纯静态扫文本不连库(照 test_payroll_schema 配方):两处覆盖同组表 + 每表 RLS + 迁移接真 head
带 downgrade + 启动链尾挂载,任一处漏建/漏隔离/断链 → 红。
"""

import pathlib
import re
import unittest

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_MIGRATION = "alembic/versions/0073_coa_erp_bridge.py"
_ENSURE = "services/accounting/bridge_schema.py"

_EXPECTED_TABLES = {"coa_erp_bridge"}
_CREATE_RE = re.compile(r"CREATE TABLE IF NOT EXISTS\s+(\w+)", re.I)
_PK = "PRIMARY KEY (tenant_id, workspace_client_id, erp_type, coa_code)"


def _text(path: str) -> str:
    return (_ROOT / path).read_text(encoding="utf-8")


def _tables_in(path: str) -> set:
    return set(_CREATE_RE.findall(_text(path)))


class CoaErpBridgeSchemaParityTests(unittest.TestCase):
    def test_ensure_covers_expected_tables(self):
        self.assertEqual(_tables_in(_ENSURE), _EXPECTED_TABLES)

    def test_migration_covers_expected_tables(self):
        self.assertEqual(_tables_in(_MIGRATION), _EXPECTED_TABLES)

    def test_table_has_rls_in_ensure(self):
        self.assertIn('"coa_erp_bridge"', _text(_ENSURE))

    def test_table_has_rls_in_migration(self):
        self.assertIn('t="coa_erp_bridge"', _text(_MIGRATION))

    def test_migration_down_revision_points_to_actual_head(self):
        # 0072_client_payroll 是落笔时 alembic heads 的唯一输出;撞号/接错头在此翻红。
        self.assertIn('down_revision = "0072_client_payroll"', _text(_MIGRATION))

    def test_migration_has_matching_downgrade(self):
        self.assertIn("DROP TABLE IF EXISTS coa_erp_bridge", _text(_MIGRATION))

    def test_unique_quad_is_primary_key_both_sides(self):
        # UNIQUE(tenant, 账套, erp_type, coa_code) 由 PK 承载,两侧逐字一致。
        self.assertIn(_PK, _text(_ENSURE))
        self.assertIn(_PK, _text(_MIGRATION))


class BridgeEnsureStartupChainTests(unittest.TestCase):
    """启动自愈接线:… → ensure_tax_profile_schema → ensure_coa_erp_bridge_schema
    (链尾挂载照 H1a R1 修法,startup.py 不加行)。链断 → 红,防「表没人建」静默回归。"""

    def test_tax_profile_ensure_calls_bridge_ensure(self):
        text = _text("services/workspace/tax_profile_schema.py")
        self.assertIn(
            "from services.accounting.bridge_schema import ensure_coa_erp_bridge_schema", text
        )
        self.assertIn("ensure_coa_erp_bridge_schema()", text)


if __name__ == "__main__":
    unittest.main()
