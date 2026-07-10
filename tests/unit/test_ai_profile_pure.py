#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_profile_pure.py

税务画像/别名/义务清单前端(B2-e)纯函数模块的等价/边界守门:ai-profile-render.js /
ai-profile-panels-render.js 走 pos-totals.js/ai-intake-render.js 先例的 UMD 双导出,
这里用真 node 直接 require 源文件断言输出——不进浏览器,只测无 DOM 依赖的那一半逻辑。
ai-format.js 的 priorPeriodCheckStatus(N-3 修复)也在本文件守,不再往已近 500 行的
test_ai_pure_modules.py 里堆(单文件<500 铁律)。node 缺失时跳过(本地/CI 均装了 node)。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

# ai-profile-render.js 的 buildProfilePayload 借道 root.AI.format.parseAmount(同
# ai-intake-render.js 的 parseAmount 先例),node 独立进程里没人挂 AI.format,先 require
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
        self.assertEqual(out["vars"]["delta"], "-฿25.50")

    def test_missing_or_null_check_defaults_to_no_prior(self):
        out = _run_node(f"""
            const f = require({json.dumps(str(AI_DIR / "ai-format.js"))});
            process.stdout.write(JSON.stringify([
                f.priorPeriodCheckStatus(null), f.priorPeriodCheckStatus({{}}),
            ]));
            """)
        self.assertEqual(out, [{"key": "ppc_no_prior", "vars": None}] * 2)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class FieldDefsTests(unittest.TestCase):
    """FIELD_DEFS 是画像表单唯一事实源(HTML 拼装 + readProfileForm 都读它)——
    覆盖方案 §2.2 的关键字段,顺序/存在性回归就能第一时间抓到。"""

    def test_field_defs_cover_key_profile_fields(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-profile-render.js"))});
            process.stdout.write(JSON.stringify(r.FIELD_DEFS.map(f => f.key)));
            """)
        for key in (
            "sbt_status",
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

    def test_visibility_fields_subset_of_field_defs(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-profile-render.js"))});
            const keys = r.FIELD_DEFS.map(f => f.key);
            process.stdout.write(JSON.stringify(
                r.VISIBILITY_FIELDS.every(v => v === 'sbt_status' || keys.indexOf(v) >= 0)
            ));
            """)
        self.assertTrue(out)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class BuildProfilePayloadTests(unittest.TestCase):
    def _build(self, raw: dict):
        return _run_node(f"""
            {_REQUIRE_AI_FORMAT}
            const r = require({json.dumps(str(AI_DIR / "ai-profile-render.js"))});
            process.stdout.write(JSON.stringify(r.buildProfilePayload({json.dumps(raw)})));
            """)

    def test_minimal_valid_defaults_branch_one_and_credit_zero(self):
        out = self._build(
            {
                "sbt_status": "none",
                "has_employees": "unknown",
                "pays_individuals": "unknown",
                "pays_juristic": "unknown",
                "pays_foreign": "unknown",
                "pays_interest_dividend": "unknown",
                "has_multi_branch": False,
                "filing_disposition": "active",
                "efiling_enrolled": "unknown",
                "tax_agent_authorized": False,
            }
        )
        self.assertTrue(out["ok"])
        self.assertEqual(out["payload"]["branch_count"], 1)
        self.assertEqual(out["payload"]["vat_credit_carry"], "0.00")
        self.assertEqual(out["payload"]["tax_agent_ref"], "")

    def test_multi_branch_without_count_rejected(self):
        out = self._build({"has_multi_branch": True, "branch_count": ""})
        self.assertFalse(out["ok"])
        self.assertEqual(out["errKey"], "err_profile_branch_count_invalid")

    def test_multi_branch_with_valid_count_accepted(self):
        out = self._build({"has_multi_branch": True, "branch_count": "5"})
        self.assertTrue(out["ok"])
        self.assertEqual(out["payload"]["branch_count"], 5)

    def test_invalid_vat_credit_rejected(self):
        out = self._build({"vat_credit_carry": "not-a-number"})
        self.assertFalse(out["ok"])
        self.assertEqual(out["errKey"], "err_profile_vat_credit_invalid")

    def test_valid_vat_credit_normalized(self):
        out = self._build({"vat_credit_carry": "1,234.5"})
        self.assertTrue(out["ok"])
        self.assertEqual(out["payload"]["vat_credit_carry"], "1234.5")

    def test_tax_agent_ref_cleared_when_not_authorized(self):
        out = self._build({"tax_agent_authorized": False, "tax_agent_ref": "REF-123"})
        self.assertTrue(out["ok"])
        self.assertEqual(out["payload"]["tax_agent_ref"], "")

    def test_tax_agent_ref_kept_when_authorized(self):
        out = self._build({"tax_agent_authorized": True, "tax_agent_ref": "REF-123"})
        self.assertTrue(out["ok"])
        self.assertEqual(out["payload"]["tax_agent_ref"], "REF-123")


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
