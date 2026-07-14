#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_bank_sales_pure.py

SA-3b · 银行流水倒推销项确认清单(ai-bank-sales-render.js)零 DOM/零 i18n 依赖的
那一半逻辑:交叉佐证差异比(diffRatio/crossCheckRows)+「采用建议值」放行判据
(canApply)+ 逐行分组(groupRows)。HTML 拼装那一半依赖 at()/AI.state/AI.format,
不在 node 里独立可测,由 tests/e2e/_sa3b_bank_sales.spec.js 真浏览器覆盖
(同 ai-recon-render.js/ai-corrob.js 先例)。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class DiffRatioTests(unittest.TestCase):
    def test_identical_amounts_zero_ratio(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-bank-sales-render.js"))});
            process.stdout.write(JSON.stringify(b.diffRatio('858780.16', '858780.16')));
            """)
        self.assertEqual(out, 0)

    def test_ratio_relative_to_larger_side(self):
        # |102-100| / max(102,100) = 2/102 ≈ 0.0196(<2% 阈值,不该触发黄灯)。
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-bank-sales-render.js"))});
            process.stdout.write(JSON.stringify(b.diffRatio('102', '100')));
            """)
        self.assertAlmostEqual(out, 2 / 102, places=6)

    def test_unparseable_side_returns_null(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-bank-sales-render.js"))});
            process.stdout.write(JSON.stringify([b.diffRatio('abc', '100'), b.diffRatio(null, '1')]));
            """)
        self.assertEqual(out, [None, None])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class CrossCheckRowsTests(unittest.TestCase):
    def test_warns_past_two_percent_threshold(self):
        # 858,780.16 vs 700,000 差异远超 2% → warn=true(方案 §三.3 材料性线)。
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-bank-sales-render.js"))});
            process.stdout.write(JSON.stringify(b.crossCheckRows(
                {{applicable: true, reliable: true, sales_amount: '858780.16'}},
                {{net_total: '700000.00'}},
                {{net_total: '858780.16'}},
            )));
            """)
        kinds = {row["kind"]: row for row in out}
        self.assertTrue(kinds["invoice"]["warn"])
        self.assertFalse(kinds["edc"]["warn"])

    def test_unreliable_suggestion_yields_no_rows(self):
        # 降级态(reliable=false)没有 sales_amount 可比——不假装比较过。
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-bank-sales-render.js"))});
            process.stdout.write(JSON.stringify(b.crossCheckRows(
                {{applicable: true, reliable: false}}, {{net_total: '1'}}, {{net_total: '1'}}
            )));
            """)
        self.assertEqual(out, [])

    def test_missing_corroboration_omits_that_row(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-bank-sales-render.js"))});
            process.stdout.write(JSON.stringify(b.crossCheckRows(
                {{applicable: true, reliable: true, sales_amount: '100'}}, null, {{net_total: '100'}}
            )));
            """)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "edc")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class CanApplyTests(unittest.TestCase):
    def test_ready_when_reliable_and_no_pending(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-bank-sales-render.js"))});
            process.stdout.write(JSON.stringify(b.canApply(
                {{applicable: true, reliable: true, pending_count: 0}}
            )));
            """)
        self.assertTrue(out)

    def test_blocked_while_pending_rows_remain(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-bank-sales-render.js"))});
            process.stdout.write(JSON.stringify(b.canApply(
                {{applicable: true, reliable: true, pending_count: 3}}
            )));
            """)
        self.assertFalse(out)

    def test_blocked_when_degraded_or_not_applicable(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-bank-sales-render.js"))});
            process.stdout.write(JSON.stringify([
                b.canApply({{applicable: true, reliable: false, pending_count: 0}}),
                b.canApply({{applicable: false}}),
                b.canApply(null),
            ]));
            """)
        self.assertEqual(out, [False, False, False])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class GroupRowsTests(unittest.TestCase):
    def test_splits_by_verdict_into_three_buckets(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-bank-sales-render.js"))});
            process.stdout.write(JSON.stringify(b.groupRows([
                {{fingerprint: 'a', verdict: 'sales'}},
                {{fingerprint: 'b', verdict: 'non_sales'}},
                {{fingerprint: 'c', verdict: 'pending'}},
                {{fingerprint: 'd', verdict: 'sales'}},
            ])));
            """)
        self.assertEqual([r["fingerprint"] for r in out["sales"]], ["a", "d"])
        self.assertEqual([r["fingerprint"] for r in out["nonSales"]], ["b"])
        self.assertEqual([r["fingerprint"] for r in out["pending"]], ["c"])

    def test_empty_rows_yields_empty_buckets(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-bank-sales-render.js"))});
            process.stdout.write(JSON.stringify(b.groupRows(null)));
            """)
        self.assertEqual(out, {"sales": [], "pending": [], "nonSales": []})


if __name__ == "__main__":
    unittest.main()
