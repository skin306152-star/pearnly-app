# -*- coding: utf-8 -*-
"""schema DDL + 泰标科目预置一致性闸(docs/accounting/01)。

DDL 是字符串常量 → 不连库即可断言关键约束(双隔离列/DECIMAL/partial 唯一索引排除 void/
建议模式默认值)。预置科目与角色映射互相咬合(每个角色必指向存在的预置编号)。"""

import unittest

from services.accounting import coa_preset, schema


class SchemaDdlTests(unittest.TestCase):
    def _ddl(self, table: str) -> str:
        for t in schema._TABLES:
            if f"CREATE TABLE IF NOT EXISTS {table}" in t:
                return t
        raise AssertionError(f"missing table ddl: {table}")

    def test_six_tables_present(self):
        for t in (
            "chart_of_accounts",
            "account_mappings",
            "journal_vouchers",
            "journal_lines",
            "accounting_settings",
            "review_learned",
        ):
            self._ddl(t)

    def test_workspace_isolation_columns(self):
        # journal_lines 经 voucher 归属(行表无 ws 列),其余 5 表双隔离 NOT NULL
        for t in (
            "chart_of_accounts",
            "account_mappings",
            "journal_vouchers",
            "accounting_settings",
            "review_learned",
        ):
            ddl = self._ddl(t)
            self.assertIn("tenant_id uuid NOT NULL", ddl, t)
            self.assertIn("workspace_client_id bigint NOT NULL", ddl, t)

    def test_money_is_decimal_not_float(self):
        for t in ("journal_vouchers", "journal_lines"):
            ddl = self._ddl(t)
            self.assertIn("numeric(14,2)", ddl)
            self.assertNotIn("float", ddl.lower())
            self.assertNotIn("real", ddl.lower().split("created")[0])

    def test_dedupe_index_is_partial_excluding_void(self):
        idx = next(i for i in schema._INDEXES if "uq_jv_source" in i)
        self.assertIn("WHERE source_id IS NOT NULL AND status != 'void'", idx)

    def test_settings_default_is_suggest_mode(self):
        ddl = self._ddl("accounting_settings")
        self.assertIn("auto_post boolean NOT NULL DEFAULT FALSE", ddl)

    def test_safety_belt_columns_present(self):
        ddl = self._ddl("journal_vouchers")
        self.assertIn("method text NOT NULL DEFAULT 'suggested'", ddl)
        self.assertIn("source_tier text", ddl)

    def test_rls_covers_all_tables(self):
        # 做账 6 表 + 银行对账 3 表 + 失败重试队列
        self.assertEqual(len(schema._RLS_TABLES), 10)
        for t in ("acct_bank_accounts", "acct_bank_lines", "acct_voucher_templates"):
            self.assertIn(t, schema._RLS_TABLES)
        self.assertIn("accounting_posting_failures", schema._RLS_TABLES)


class CoaPresetTests(unittest.TestCase):
    def test_codes_unique_and_types_valid(self):
        codes = [c for c, _zh, _th, _t in coa_preset.PRESET_ACCOUNTS]
        self.assertEqual(len(codes), len(set(codes)))
        for _c, _zh, _th, acct_type in coa_preset.PRESET_ACCOUNTS:
            self.assertIn(acct_type, coa_preset.ACCT_TYPES)

    def test_every_role_maps_to_existing_preset_code(self):
        codes = {c for c, _zh, _th, _t in coa_preset.PRESET_ACCOUNTS}
        for role, code in coa_preset.ROLE_DEFAULTS.items():
            self.assertIn(code, codes, f"role {role} 指向不存在的科目 {code}")

    def test_engine_core_roles_all_mapped(self):
        # rules.py 模板用到的核心角色必须在默认映射里(缺=凭证落待审壳,违封板)
        for role in (
            "cash",
            "bank",
            "ar",
            "ap",
            "input_vat",
            "output_vat",
            "vat_payable",
            "vat_receivable",
            "wht_payable",
            "wht_prepaid",
            "inventory",
            "cogs",
            "sales_revenue",
            "expense_default",
        ):
            self.assertIn(role, coa_preset.ROLE_DEFAULTS, f"核心角色 {role} 没默认映射")

    def test_thai_names_present(self):
        for _c, _zh, name_th, _t in coa_preset.PRESET_ACCOUNTS:
            self.assertTrue(name_th)


if __name__ == "__main__":
    unittest.main()
