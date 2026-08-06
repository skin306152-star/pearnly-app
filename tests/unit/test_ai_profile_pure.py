#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_profile_pure.py

税务画像卡(智能判断版·画像卡设计稿 v1)纯字段模型单测——ai-profile-render.js 走
pos-totals.js/ai-intake-render.js 先例的 UMD 双导出,这里用真 node 直接 require 源文件
断言输出——不进浏览器,只测无 DOM 依赖的那一半逻辑(deriveFieldStatus/deriveSourceBadge/
validateFieldInput/isApplicable)。ai-format.js 的 priorPeriodCheckStatus(N-3 修复)也在
本文件守,不再往已近 500 行的 test_ai_pure_modules.py 里堆(单文件<500 铁律)。别名纯校验
(validateAliasRaw)在同一文件守,拆自 ai-profile-panels-render.js。node 缺失时跳过
(本地/CI 均装了 node)。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, BAHT, _run_node

# ai-profile-render.js 的 validateFieldInput(money 分支)借道 root.AI.format.parseAmount
# (同 ai-intake-render.js 的 parseAmount 先例),node 独立进程里没人挂 AI.format,先 require
# ai-format.js 把它挂上 globalThis,后续 require 的 ai-profile-render.js 才能真正解析。
_REQUIRE_AI_FORMAT = f'require({json.dumps(str(AI_DIR / "ai-format.js"))});\n'


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class PriorPeriodCheckTests(unittest.TestCase):
    """N-3 修复:prior_period_check 对象 → i18n key + 插值,不再字面显示 [object Object]。"""

    def test_no_prior_period_status(self):
        out = _run_node(f"""
            const f = require({json.dumps(str(AI_DIR / "ai-format.js"))});
            process.stdout.write(JSON.stringify(f.priorPeriodCheckStatus({{status: 'no_prior_period'}})));
            """)
        self.assertEqual(out, {"key": "ppc_no_prior", "vars": None})

    def test_compared_status_carries_period_and_formatted_delta(self):
        out = _run_node(f"""
            const f = require({json.dumps(str(AI_DIR / "ai-format.js"))});
            process.stdout.write(JSON.stringify(f.priorPeriodCheckStatus({{
                status: 'compared', prior_period: '2569-04', prior_tax_due: '100.00', delta: '-25.5',
            }})));
            """)
        self.assertEqual(out["key"], "ppc_compared")
        self.assertEqual(out["vars"]["period"], "2569-04")
        self.assertEqual(out["vars"]["delta"], f"-{BAHT}25.50")

    def test_missing_or_null_check_defaults_to_no_prior(self):
        out = _run_node(f"""
            const f = require({json.dumps(str(AI_DIR / "ai-format.js"))});
            process.stdout.write(JSON.stringify([
                f.priorPeriodCheckStatus(null), f.priorPeriodCheckStatus({{}}),
            ]));
            """)
        self.assertEqual(out, [{"key": "ppc_no_prior", "vars": None}] * 2)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class FieldMetaTests(unittest.TestCase):
    """FIELD_META 是画像卡唯一事实源(HTML 拼装 + saveField 都读它)——14 键
    (画像卡设计稿 v1 顶注核实过,不是 13),覆盖方案 §2.2 关键字段。"""

    def test_field_meta_has_exactly_14_keys(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-profile-render.js"))});
            process.stdout.write(JSON.stringify(r.FIELD_META.map(f => f.key)));
            """)
        self.assertEqual(len(out), 14)
        for key in (
            "sbt_status",
            "sbt_business_type",
            "has_employees",
            "pays_individuals",
            "pays_juristic",
            "pays_foreign",
            "pays_interest_dividend",
            "has_multi_branch",
            "branch_count",
            "filing_disposition",
            "efiling_enrolled",
            "tax_agent_authorized",
            "tax_agent_ref",
            "vat_credit_carry",
        ):
            self.assertIn(key, out)

    def test_only_wht_backed_fields_are_inferable(self):
        """诚实边界:has_employees/pays_foreign/pays_interest_dividend 没有数据源,
        只有 pays_individuals/pays_juristic 走 wht_signals 推断链路。"""
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-profile-render.js"))});
            process.stdout.write(JSON.stringify(r.INFERABLE_FIELDS));
            """)
        self.assertEqual(set(out), {"pays_individuals", "pays_juristic"})

    def test_visibility_fields_subset_of_field_meta(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-profile-render.js"))});
            const keys = r.FIELD_META.map(f => f.key);
            process.stdout.write(JSON.stringify(
                r.VISIBILITY_FIELDS.every(v => keys.indexOf(v) >= 0)
            ));
            """)
        self.assertTrue(out)

    def test_field_by_key_returns_null_for_unknown_key(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-profile-render.js"))});
            process.stdout.write(JSON.stringify([
                r.fieldByKey('sbt_status') !== null, r.fieldByKey('nope') === null,
            ]));
            """)
        self.assertEqual(out, [True, True])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class IsApplicableTests(unittest.TestCase):
    """渐进展露(showIf):sbt_business_type/branch_count/tax_agent_ref 只在父开关打开时展示。"""

    def test_conditional_fields_hidden_by_default(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-profile-render.js"))});
            const v = {{ sbt_status: 'none', has_multi_branch: false, tax_agent_authorized: false }};
            process.stdout.write(JSON.stringify([
                r.isApplicable(r.fieldByKey('sbt_business_type'), v),
                r.isApplicable(r.fieldByKey('branch_count'), v),
                r.isApplicable(r.fieldByKey('tax_agent_ref'), v),
            ]));
            """)
        self.assertEqual(out, [False, False, False])

    def test_conditional_fields_shown_when_parent_open(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-profile-render.js"))});
            const v = {{ sbt_status: 'registered', has_multi_branch: true, tax_agent_authorized: true }};
            process.stdout.write(JSON.stringify([
                r.isApplicable(r.fieldByKey('sbt_business_type'), v),
                r.isApplicable(r.fieldByKey('branch_count'), v),
                r.isApplicable(r.fieldByKey('tax_agent_ref'), v),
            ]));
            """)
        self.assertEqual(out, [True, True, True])

    def test_unconditional_field_always_applicable(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-profile-render.js"))});
            process.stdout.write(JSON.stringify(r.isApplicable(r.fieldByKey('has_employees'), {{}})));
            """)
        self.assertTrue(out)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class DeriveFieldStatusTests(unittest.TestCase):
    """字段展示态派生(镜像后端 field_meta 契约):confirmed/pending/conflict/unknown/blocked。"""

    def _status(self, meta_json: str, value_json: str, field_meta_json: str) -> str:
        return _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-profile-render.js"))});
            process.stdout.write(JSON.stringify(
                r.deriveFieldStatus({meta_json}, {value_json}, {field_meta_json})
            ));
            """)

    def test_sbt_none_with_no_meta_is_blocked(self):
        """SBT 沉默默认(DDL 落 'none')但从未有人确认过 → 前端专属特例,视觉当未确认处理。"""
        out = self._status("{kind:'enum',key:'sbt_status'}", "'none'", "null")
        self.assertEqual(out, "blocked")

    def test_sbt_registered_with_no_meta_is_confirmed(self):
        """一旦真实取值偏离沉默默认(比如 legacy PUT 过),即使没有 field_meta 戳也算已确认。"""
        out = self._status("{kind:'enum',key:'sbt_status'}", "'registered'", "null")
        self.assertEqual(out, "confirmed")

    def test_enum_unknown_with_no_meta_is_unknown(self):
        out = self._status("{kind:'enum',key:'has_employees'}", "'unknown'", "null")
        self.assertEqual(out, "unknown")

    def test_enum_real_value_with_no_meta_is_confirmed(self):
        """存量数据(改造前已经填过、没有 field_meta 戳的字段)按已确认展示,不无端制造待办。"""
        out = self._status("{kind:'enum',key:'has_employees'}", "'yes'", "null")
        self.assertEqual(out, "confirmed")

    def test_bool_field_always_confirmed_no_unknown_sentinel(self):
        out = self._status("{kind:'bool',key:'has_multi_branch'}", "false", "null")
        self.assertEqual(out, "confirmed")

    def test_proposal_without_confirmation_is_pending(self):
        out = self._status(
            "{kind:'enum',key:'pays_individuals'}",
            "'unknown'",
            "{proposal:{value:'yes'},confirmed_at:null}",
        )
        self.assertEqual(out, "pending")

    def test_proposal_with_prior_confirmation_is_conflict(self):
        out = self._status(
            "{kind:'enum',key:'pays_individuals'}",
            "'no'",
            "{proposal:{value:'yes'},confirmed_at:'2026-08-01T00:00:00Z'}",
        )
        self.assertEqual(out, "conflict")

    def test_confirmed_no_proposal_is_confirmed(self):
        out = self._status(
            "{kind:'enum',key:'pays_individuals'}",
            "'yes'",
            "{proposal:null,confirmed_at:'2026-08-01T00:00:00Z'}",
        )
        self.assertEqual(out, "confirmed")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class DeriveSourceBadgeTests(unittest.TestCase):
    def test_meta_source_wins_when_present(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-profile-render.js"))});
            process.stdout.write(JSON.stringify(r.deriveSourceBadge('confirmed', {{source: 'inferred'}})));
            """)
        self.assertEqual(out, "inferred")

    def test_unknown_status_without_meta_is_unknown_source(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-profile-render.js"))});
            process.stdout.write(JSON.stringify(r.deriveSourceBadge('unknown', null)));
            """)
        self.assertEqual(out, "unknown")

    def test_confirmed_status_without_meta_falls_back_to_manual(self):
        """存量数据没有出处戳——按手填口径展示,不假装官方(诚实边界)。"""
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-profile-render.js"))});
            process.stdout.write(JSON.stringify(r.deriveSourceBadge('confirmed', null)));
            """)
        self.assertEqual(out, "manual")

    def test_pending_status_badges_as_inferred_not_manual(self):
        """待确认的候选本身就是票据推断出的——徽章要照实说,不能因未确认就退回手填
        (03-conflict-before.png 真截图揪出的问题:pending 行曾误标"手填")。"""
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-profile-render.js"))});
            process.stdout.write(JSON.stringify(r.deriveSourceBadge('pending', {{proposal:{{value:'yes'}}}})));
            """)
        self.assertEqual(out, "inferred")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ValidateFieldInputTests(unittest.TestCase):
    def _validate(self, field_json: str, raw_json: str):
        return _run_node(f"""
            {_REQUIRE_AI_FORMAT}
            const r = require({json.dumps(str(AI_DIR / "ai-profile-render.js"))});
            process.stdout.write(JSON.stringify(r.validateFieldInput({field_json}, {raw_json})));
            """)

    def test_branch_count_rejects_zero_and_blank(self):
        for raw in ("'0'", "''", "null"):
            out = self._validate("{kind:'int'}", raw)
            self.assertFalse(out["ok"], f"raw={raw}")
            self.assertEqual(out["errKey"], "err_profile_branch_count_invalid")

    def test_branch_count_accepts_positive_int(self):
        out = self._validate("{kind:'int'}", "'5'")
        self.assertTrue(out["ok"])
        self.assertEqual(out["value"], 5)

    def test_vat_credit_blank_defaults_to_zero(self):
        out = self._validate("{kind:'money'}", "''")
        self.assertTrue(out["ok"])
        self.assertEqual(out["value"], "0.00")

    def test_vat_credit_invalid_rejected(self):
        out = self._validate("{kind:'money'}", "'not-a-number'")
        self.assertFalse(out["ok"])
        self.assertEqual(out["errKey"], "err_profile_vat_credit_invalid")

    def test_vat_credit_normalizes_thousands_separator(self):
        out = self._validate("{kind:'money'}", "'1,234.5'")
        self.assertTrue(out["ok"])
        self.assertEqual(out["value"], "1234.5")

    def test_bool_field_coerced_to_real_boolean(self):
        out = self._validate("{kind:'bool'}", "true")
        self.assertTrue(out["ok"])
        self.assertIs(out["value"], True)

    def test_enum_field_passthrough(self):
        out = self._validate("{kind:'enum'}", "'yes'")
        self.assertTrue(out["ok"])
        self.assertEqual(out["value"], "yes")

    def test_text_field_blank_allowed(self):
        out = self._validate("{kind:'text'}", "null")
        self.assertTrue(out["ok"])
        self.assertEqual(out["value"], "")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ValidateAliasRawTests(unittest.TestCase):
    """前端只挡"非空"(真正的长度/泛词/唯一性闸在后端 client_alias_store 五道污染闸)。"""

    def test_empty_rejected(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-profile-panels-render.js"))});
            process.stdout.write(JSON.stringify([
                r.validateAliasRaw(''), r.validateAliasRaw('   '), r.validateAliasRaw(null),
            ]));
            """)
        for item in out:
            self.assertFalse(item["ok"])
            self.assertEqual(item["errKey"], "err_alias_required")

    def test_valid_trims_whitespace(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-profile-panels-render.js"))});
            process.stdout.write(JSON.stringify(r.validateAliasRaw('  Sister Makeup  ')));
            """)
        self.assertTrue(out["ok"])
        self.assertEqual(out["value"], "Sister Makeup")

    def test_alias_kinds_and_match_modes_exposed(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-profile-panels-render.js"))});
            process.stdout.write(JSON.stringify([r.ALIAS_KINDS, r.MATCH_MODES]));
            """)
        self.assertIn("trade_en", out[0])
        self.assertIn("misc", out[0])
        self.assertEqual(out[1], ["exact", "substring"])


if __name__ == "__main__":
    unittest.main()
