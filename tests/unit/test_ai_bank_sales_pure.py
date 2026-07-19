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

    def test_zero_bank_estimate_uses_neutral_state(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-bank-sales-render.js"))});
            process.stdout.write(JSON.stringify(b.crossCheckRows(
                {{applicable: true, reliable: true, sales_amount: '0'}},
                {{net_total: '100'}}, null
            )));
            """)
        self.assertTrue(out[0]["neutral"])
        self.assertFalse(out[0]["warn"])


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
class ReadinessChipTests(unittest.TestCase):
    def test_pending_rows_are_not_presented_as_usable(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-bank-sales-render.js"))});
            process.stdout.write(JSON.stringify(b.readinessChip(
                {{applicable: true, reliable: true, pending_count: 705}}
            )));
            """)
        self.assertEqual(
            out,
            {"cls": "w", "key": "bxs_state_pending_chip", "vars": {"n": 705}},
        )

    def test_zero_pending_rows_are_presented_as_usable(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-bank-sales-render.js"))});
            process.stdout.write(JSON.stringify(b.readinessChip(
                {{applicable: true, reliable: true, pending_count: 0}}
            )));
            """)
        self.assertEqual(
            out,
            {"cls": "g", "key": "bxs_state_reliable_chip", "vars": None},
        )


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


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class PendingGroupShapeTests(unittest.TestCase):
    def test_backend_groups_drive_large_and_small_buckets(self):
        out = _run_node(f"""
            const g = require({json.dumps(str(AI_DIR / "ai-bank-sales-groups.js"))});
            process.stdout.write(JSON.stringify(g.pendingGroups([
                {{fingerprint: 'a', verdict: 'pending', group: 'transfer_in', deposit: '9999.99'}},
                {{fingerprint: 'b', verdict: 'pending', group: 'transfer_in', deposit: '10000'}},
                {{fingerprint: 'c', verdict: 'sales', group: 'transfer_in', deposit: '500'}},
            ], [{{key: 'transfer_in', count: 2, sum: '19999.99'}}])));
            """)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["count"], 2)
        self.assertEqual(out[0]["sum"], "19999.99")
        self.assertEqual([row["fingerprint"] for row in out[0]["large"]], ["b"])
        self.assertEqual([row["fingerprint"] for row in out[0]["small"]], ["a"])

    def test_unknown_backend_group_falls_back_to_other(self):
        out = _run_node(f"""
            const g = require({json.dumps(str(AI_DIR / "ai-bank-sales-groups.js"))});
            process.stdout.write(JSON.stringify(g.pendingGroups([
                {{fingerprint: 'x', verdict: 'pending', group: 'unknown', deposit: '1'}}
            ], [])));
            """)
        self.assertEqual(out[0]["key"], "other_in")
        self.assertEqual(len(out[0]["small"]), 1)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class BankSalesApiTests(unittest.TestCase):
    def test_four_endpoints_keep_expected_paths_and_bodies(self):
        out = _run_node(f"""
            const m = require({json.dumps(str(AI_DIR / "ai-api-bank-sales.js"))});
            const calls = [];
            const api = m.create((...args) => {{ calls.push(args); return Promise.resolve({{}}); }});
            api.runBankSales('wo /1');
            api.bankSalesProgress('wo /1');
            api.decideBankSales('wo /1', {{fingerprint: 'a', verdict: 'sales'}});
            api.decideBankSalesBatch('wo /1', [{{fingerprint: 'b', verdict: 'non_sales'}}]);
            process.stdout.write(JSON.stringify(calls));
            """)
        prefix = "/api/workorder/orders/wo%20%2F1/bank-sales/"
        self.assertEqual(
            [call[:2] for call in out],
            [
                ["POST", prefix + "run"],
                ["GET", prefix + "progress"],
                ["POST", prefix + "decide"],
                ["POST", prefix + "decide-batch"],
            ],
        )
        self.assertEqual(out[3][2]["decisions"][0]["fingerprint"], "b")


if __name__ == "__main__":
    unittest.main()
