#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_financials_pure.py

G1b · 月度报表包区(ai-financials-render.js)零 DOM/零 i18n 依赖的那一半逻辑:配平
胶囊态判定(balanceState)+ 权益节展示行装配(equityDisplayRows,BS 视觉配平硬约束:
本期损益必须恒作为一行列出,不能只渲染空 equity 数组)。HTML 拼装那一半依赖
at()/AI.state/AI.format,不在 node 里独立可测,由 tests/e2e/_gbatch_financials_local.spec.js
真浏览器覆盖(同 ai-shadow-render.js 先例)。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class BalanceStateTests(unittest.TestCase):
    def test_balanced_true_maps_to_good_chip(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-financials-render.js"))});
            process.stdout.write(JSON.stringify(r.balanceState(true)));
            """)
        self.assertEqual(out, {"cls": "g", "key": "fin_balanced_chip"})

    def test_balanced_false_maps_to_warn_chip(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-financials-render.js"))});
            process.stdout.write(JSON.stringify(r.balanceState(false)));
            """)
        self.assertEqual(out, {"cls": "w", "key": "fin_unbalanced_chip"})

    def test_missing_balanced_does_not_pretend_balanced(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-financials-render.js"))});
            process.stdout.write(JSON.stringify(r.balanceState(undefined)));
            """)
        self.assertEqual(out, {"cls": "w", "key": "fin_unbalanced_chip"})


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class EquityDisplayRowsTests(unittest.TestCase):
    def test_empty_equity_still_yields_current_earnings_row(self):
        # 硬约束:单月无留存收益科目是正常态,但本期损益必须恒列出一行,不能视觉
        # 消失成"没有权益"(会误读成没配平)。
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-financials-render.js"))});
            const bs = {{equity: [], current_earnings: '440814.24'}};
            process.stdout.write(JSON.stringify(r.equityDisplayRows(bs)));
            """)
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0]["current_earnings"])
        self.assertEqual(out[0]["amount"], "440814.24")
        self.assertIsNone(out[0]["code"])

    def test_preset_equity_accounts_preserved_before_earnings_row(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-financials-render.js"))});
            const bs = {{
                equity: [{{code: '3010', name_zh: '实收资本', name_th: 'ทุน', amount: '100000.00'}}],
                current_earnings: '440814.24',
            }};
            process.stdout.write(JSON.stringify(r.equityDisplayRows(bs)));
            """)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["code"], "3010")
        self.assertFalse(out[0]["current_earnings"])
        self.assertTrue(out[1]["current_earnings"])
        self.assertEqual(out[1]["amount"], "440814.24")

    def test_missing_balance_sheet_does_not_crash(self):
        # bs=null → amount 落 undefined,JSON.stringify 省略该键(不是 raw null)——
        # 同 test_ai_shadow_pure.py 的 glReconState(null) 先例,仍不假装有一个真实金额。
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-financials-render.js"))});
            process.stdout.write(JSON.stringify(r.equityDisplayRows(null)));
            """)
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0]["current_earnings"])
        self.assertNotIn("amount", out[0])


if __name__ == "__main__":
    unittest.main()
