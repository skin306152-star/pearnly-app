# -*- coding: utf-8 -*-
"""客户税务画像 schema 双跑对齐闸(税务画像-方案-B1 §5 · B2-a)。

prod 无自动迁移,services/workspace/tax_profile_schema.ensure_tax_profile_schema 与
alembic 0064 是同一份 DDL 的两处副本(启动 ensure / 正式迁移)。本测试机械保证两处
覆盖同一组表 + 每表 RLS + defs seed 九行,任一处漏建/漏隔离/漏 seed → 红。纯静态
扫文本,不连库(照 tests/unit/test_purchase_schema.py 同款配方)。
"""

import pathlib
import re
import unittest

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_MIGRATION = "alembic/versions/0064_client_tax_profile.py"
_ENSURE = "services/workspace/tax_profile_schema.py"

_EXPECTED_TABLES = {
    "client_tax_profiles",
    "client_name_aliases",
    "tax_obligation_defs",
    "client_period_obligations",
}

# tax_obligation_defs 是全租户共享法定常量表,无 tenant_id 列,不进 RLS 清单。
_RLS_TABLES = {
    "client_tax_profiles",
    "client_name_aliases",
    "client_period_obligations",
}

# 方案 §3.2 九行:obligation_code -> (due_paper_day, due_efiling_day)。
_EXPECTED_DEFS_DUE = {
    "pnd1": (7, 15),
    "pnd2": (7, 15),
    "pnd3": (7, 15),
    "pnd53": (7, 15),
    "pnd54": (7, 15),
    "pp36": (7, 15),
    "pp30": (15, 23),
    "sso": (15, None),
    "sbt": (15, None),
}

_CREATE_RE = re.compile(r"CREATE TABLE IF NOT EXISTS\s+(\w+)", re.I)
_SEED_ROW_RE = re.compile(
    r"'(\w+)',\s*'\{.*?\}'::jsonb,\s*'(\w+)',\s*(\d+),\s*(\d+|NULL),\s*(\d+)",
    re.S,
)


def _text(path: str) -> str:
    return (_ROOT / path).read_text(encoding="utf-8")


def _tables_in(path: str) -> set:
    return set(_CREATE_RE.findall(_text(path)))


def _seed_due_days(text: str) -> dict:
    out = {}
    for code, _trigger, paper, efiling, _extra in _SEED_ROW_RE.findall(text):
        out[code] = (int(paper), None if efiling == "NULL" else int(efiling))
    return out


class TaxProfileSchemaParityTests(unittest.TestCase):
    def test_ensure_covers_all_expected_tables(self):
        self.assertEqual(_tables_in(_ENSURE), _EXPECTED_TABLES)

    def test_migration_covers_all_expected_tables(self):
        self.assertEqual(_tables_in(_MIGRATION), _EXPECTED_TABLES)

    def test_every_business_table_has_rls_in_ensure(self):
        text = _text(_ENSURE)
        for t in _RLS_TABLES:
            self.assertIn(f'"{t}"', text, f"{t} 未列入 ensure 的 RLS 清单")

    def test_every_business_table_has_rls_in_migration(self):
        text = _text(_MIGRATION)
        for t in _RLS_TABLES:
            self.assertIn(f't="{t}"', text, f"{t} 缺 RLS policy 应用(_RLS.format)")

    def test_tax_obligation_defs_has_no_rls(self):
        # 全租户共享法定常量表,不启 RLS(方案 §5.4 结论)。
        for path in (_ENSURE, _MIGRATION):
            self.assertNotIn('"tax_obligation_defs"', _text(path))
            self.assertNotIn('t="tax_obligation_defs"', _text(path))

    def test_migration_down_revision_points_to_actual_head(self):
        # 冻结「接在真正的 head 后」这条要求:0063 是 alembic heads 实际输出的分支头
        # 之一(方案草案曾写猜测名,施工须核对真实 heads 后落定)。
        text = _text(_MIGRATION)
        self.assertIn('down_revision = "0063_pos_entitlements"', text)

    def test_migration_has_matching_downgrade(self):
        text = _text(_MIGRATION)
        for t in _EXPECTED_TABLES:
            self.assertIn(f"DROP TABLE IF EXISTS {t}", text)

    def test_alias_unique_index_present_both_sides_no_redundant_index(self):
        # 污染闸①(uq_client_alias_norm)必须两处一致;主窗拍板修正:草案里
        # 冗余的 ix_client_alias_lookup(与 uq 同列同 WHERE)已删,两处都不应再有。
        needle = "ON client_name_aliases (tenant_id, alias_norm) WHERE is_active"
        for path in (_ENSURE, _MIGRATION):
            text = _text(path)
            self.assertIn(needle, text)
            self.assertNotIn("ix_client_alias_lookup", text)

    def test_period_obligation_unique_scope_index_present_both_sides(self):
        # 幂等物化铁律:唯一约束覆盖 tenant+账套+期间+义务码,ensure 和迁移必须同款。
        needle = (
            "ON client_period_obligations (tenant_id, workspace_client_id, period, obligation_code)"
        )
        self.assertIn(needle, _text(_ENSURE))
        self.assertIn(needle, _text(_MIGRATION))

    def test_seed_defs_nine_rows_and_due_days_match_plan(self):
        for path in (_ENSURE, _MIGRATION):
            due = _seed_due_days(_text(path))
            self.assertEqual(
                due, _EXPECTED_DEFS_DUE, f"{path} 的 defs seed 九行截止日与方案 §3.2 不符"
            )

    def test_seed_upsert_is_idempotent_on_conflict(self):
        # 幂等重入(真库跑两遍不报错)靠 ON CONFLICT DO NOTHING;两处 DDL 都须带。
        for path in (_ENSURE, _MIGRATION):
            self.assertIn("ON CONFLICT (obligation_code) DO NOTHING", _text(path))

    def test_vat_credit_carry_is_numeric_not_float(self):
        # 金标敏感字段(§2.2 ⑧):铁律钱用 decimal 不用 float。
        for path in (_ENSURE, _MIGRATION):
            self.assertIn("vat_credit_carry        numeric(14,2)", _text(path))

    def test_period_obligations_fk_references_work_orders(self):
        # 不堵批次 C/D:物化行挂工单,列不重复存工单已有字段。
        for path in (_ENSURE, _MIGRATION):
            self.assertIn(
                "work_order_id       uuid   REFERENCES work_orders (id) ON DELETE SET NULL",
                _text(path),
            )


if __name__ == "__main__":
    unittest.main()
