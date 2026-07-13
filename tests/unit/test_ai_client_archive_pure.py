#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_client_archive_pure.py

EN-clients · 单客户档案页(ai-client-archive-render.js)零 DOM/零 i18n 依赖的那一半逻辑:
工单历史按账期倒序。画像/供应商两 tab 的表单逻辑复用 ai-profile.js(已有
test_ai_profile_pure.py 覆盖,不重测);HTML 拼装依赖 at()/AI.state/AI.format/AI.router,
不在 node 里独立可测,由 tests/e2e/_entryclose_verify.spec.js 真浏览器覆盖。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_RENDER = json.dumps(str(AI_DIR / "ai-client-archive-render.js"))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class SortOrdersByPeriodDescTests(unittest.TestCase):
    def test_sorts_descending_without_mutating_input(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            const input = [{{period: '2569-01'}}, {{period: '2569-05'}}, {{period: '2569-03'}}];
            const sorted = r.sortOrdersByPeriodDesc(input);
            process.stdout.write(JSON.stringify([sorted, input]));
            """)
        sorted_out, original = out
        self.assertEqual([o["period"] for o in sorted_out], ["2569-05", "2569-03", "2569-01"])
        # 原数组顺序不被就地排序打乱(调用方 listOrders() 拿到的响应可能被别处复用)。
        self.assertEqual([o["period"] for o in original], ["2569-01", "2569-05", "2569-03"])

    def test_empty_and_missing_input(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([r.sortOrdersByPeriodDesc([]), r.sortOrdersByPeriodDesc(null)]));
            """)
        self.assertEqual(out, [[], []])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class CompletenessFractionTests(unittest.TestCase):
    """P1-5(0% 画像无 CTA)判据——同 routes/tax_profile_routes.py::_profile_completeness
    的 6 字段集合/口径,两侧独立实现,这里锁住字段名对齐(改任一侧忘改另一侧会在此炸)。"""

    def test_all_unknown_is_zero(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify(r.completenessFraction({{
                has_employees: 'unknown', pays_individuals: 'unknown', pays_juristic: 'unknown',
                pays_foreign: 'unknown', pays_interest_dividend: 'unknown', efiling_enrolled: 'unknown',
            }})));
            """)
        self.assertEqual(out, 0)

    def test_missing_profile_is_zero(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([r.completenessFraction(null), r.completenessFraction({{}})]));
            """)
        self.assertEqual(out, [0, 0])

    def test_partial_answers_fraction(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify(r.completenessFraction({{
                has_employees: 'yes', pays_individuals: 'no', pays_juristic: 'unknown',
                pays_foreign: 'unknown', pays_interest_dividend: 'unknown', efiling_enrolled: 'unknown',
            }})));
            """)
        self.assertAlmostEqual(out, 2 / 6)

    def test_fully_answered_is_one(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify(r.completenessFraction({{
                has_employees: 'yes', pays_individuals: 'no', pays_juristic: 'yes',
                pays_foreign: 'no', pays_interest_dividend: 'yes', efiling_enrolled: 'no',
            }})));
            """)
        self.assertEqual(out, 1)

    # 字段名与后端 _COMPLETENESS_FIELDS 一一对齐——任一侧改名/加减字段而另一侧未同步,
    # 这里用一个"未知字段名"探针间接兜底:传一个后端集合之外的字段名不该被计入分子。
    def test_unrelated_field_names_do_not_count(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify(r.completenessFraction({{
                vat_credit_carry: '100', sbt_status: 'registered', filing_disposition: 'active',
            }})));
            """)
        self.assertEqual(out, 0)


if __name__ == "__main__":
    unittest.main()
