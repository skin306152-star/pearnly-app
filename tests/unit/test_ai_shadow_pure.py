#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_shadow_pure.py

F3 · 影子底稿区(ai-shadow-render.js)零 DOM/零 i18n 依赖的那一半逻辑:建议分录按
凭证分组(groupEntriesBySource)+ 试算平衡/GL 对平的胶囊态判定(trialBalanceState/
glReconState)。HTML 拼装那一半依赖 at()/AI.state/AI.format,不在 node 里独立可测,
由 tests/e2e/_f3_shadow_local.spec.js 真浏览器覆盖(同 ai-recon-render.js 先例)。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class GroupEntriesBySourceTests(unittest.TestCase):
    def test_groups_entries_by_matching_source_label(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-shadow-render.js"))});
            const entries = [
                {{source: 'purchase#1', rule_key: 'R1', dr_cr: 'debit', account_code: '5290',
                  account_name: 'expense', amount: '100.00', memo: 'a'}},
                {{source: 'purchase#1', rule_key: 'R1', dr_cr: 'credit', account_code: '2010',
                  account_name: 'ap', amount: '100.00', memo: 'b'}},
            ];
            const sources = [{{label: 'purchase#1', rule_key: 'R1', human_note: 'note'}}];
            process.stdout.write(JSON.stringify(r.groupEntriesBySource(entries, sources)));
            """)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["label"], "purchase#1")
        self.assertEqual(out[0]["human_note"], "note")
        self.assertEqual(len(out[0]["rows"]), 2)

    def test_entry_without_matching_source_still_forms_a_group(self):
        # sources[] 与 entries[] 理论上一一对应,但缺对应项时兜底建组,不丢分录
        # (human_note 诚实置 null,不臆造说明)。
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-shadow-render.js"))});
            const entries = [
                {{source: 'orphan', rule_key: 'R9', dr_cr: 'debit', account_code: '1140',
                  account_name: 'vat', amount: '5.00', memo: 'x'}},
            ];
            process.stdout.write(JSON.stringify(r.groupEntriesBySource(entries, [])));
            """)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["label"], "orphan")
        self.assertIsNone(out[0]["human_note"])

    def test_empty_entries_and_sources_yield_empty_list(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-shadow-render.js"))});
            process.stdout.write(JSON.stringify(r.groupEntriesBySource([], [])));
            """)
        self.assertEqual(out, [])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class TrialBalanceStateTests(unittest.TestCase):
    def test_balanced_true_maps_to_good_chip(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-shadow-render.js"))});
            process.stdout.write(JSON.stringify(r.trialBalanceState({{balanced: true}})));
            """)
        self.assertEqual(out, {"cls": "g", "key": "shadow_balanced_chip"})

    def test_balanced_false_maps_to_warn_chip(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-shadow-render.js"))});
            process.stdout.write(JSON.stringify(r.trialBalanceState({{balanced: false, diff: '15.00'}})));
            """)
        self.assertEqual(out, {"cls": "w", "key": "shadow_unbalanced_chip"})

    def test_missing_trial_balance_does_not_pretend_balanced(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-shadow-render.js"))});
            process.stdout.write(JSON.stringify(r.trialBalanceState(null)));
            """)
        self.assertEqual(out, {"cls": "w", "key": "shadow_unbalanced_chip"})


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class GlReconStateTests(unittest.TestCase):
    def test_reconciled_status_maps_to_good_chip(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-shadow-render.js"))});
            process.stdout.write(JSON.stringify(r.glReconState({{status: 'reconciled'}})));
            """)
        self.assertEqual(out, {"cls": "g", "key": "shadow_gl_reconciled"})

    def test_mismatch_status_maps_to_warn_chip(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-shadow-render.js"))});
            process.stdout.write(JSON.stringify(r.glReconState({{status: 'mismatch'}})));
            """)
        self.assertEqual(out, {"cls": "w", "key": "shadow_gl_mismatch"})

    def test_no_gl_source_status_maps_to_neutral_honest_chip(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-shadow-render.js"))});
            process.stdout.write(JSON.stringify(r.glReconState({{status: 'no_gl_source'}})));
            """)
        self.assertEqual(out, {"cls": "n", "key": "shadow_gl_no_source_chip"})

    def test_unknown_status_falls_back_neutral_without_inventing_text(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-shadow-render.js"))});
            process.stdout.write(JSON.stringify(r.glReconState({{status: 'reconcile_gl_skipped'}})));
            """)
        self.assertEqual(out, {"cls": "n", "key": None, "raw": "reconcile_gl_skipped"})

    def test_missing_reconcile_gl_falls_back_neutral(self):
        # status 是 undefined(非 null)时 JSON.stringify 直接省略该键,不是 raw:null。
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-shadow-render.js"))});
            process.stdout.write(JSON.stringify(r.glReconState(null)));
            """)
        self.assertEqual(out, {"cls": "n", "key": None})


if __name__ == "__main__":
    unittest.main()
