#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_board_pure.py

Pearnly AI(M1-W2)五列看板纯函数守门:ai-board.js 的 mapOrderToColumn /
summarizeCard / currentPeriodBE。同 test_ai_pure_modules.py 的 node subprocess
require 手法——真 node 跑源文件,不进浏览器。fieldLabel 已随查表型格式化函数搬去
ai-format.js,对应测试在 test_ai_pure_modules.py。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class MapOrderToColumnTests(unittest.TestCase):
    def test_no_order_goes_materials(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify([b.mapOrderToColumn(null), b.mapOrderToColumn(undefined)]));
            """)
        self.assertEqual(out, [{"column": "materials"}, {"column": "materials"}])

    def test_collecting_and_running(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify([
                b.mapOrderToColumn({{status: 'collecting'}}),
                b.mapOrderToColumn({{status: 'running'}}),
            ]));
            """)
        self.assertEqual(out, [{"column": "materials"}, {"column": "working"}])

    def test_stuck_with_needs_goes_materials(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(
                b.mapOrderToColumn({{status: 'stuck'}}, {{needs: ['sales_summary'], blocked_reasons: []}})
            ));
            """)
        self.assertEqual(out, {"column": "materials"})

    def test_stuck_with_blocked_reasons_but_no_flagged_queue_goes_materials(self):
        # J-12 根治:blocked_reasons 非空不再单独决定"等你审"——没有 flagged 队列条目
        # (卡住但没有真的待裁决票)该落「等资料/卡住」语义列(materials),不是"等你审"
        # (此前会把这种单塞进等你审列,点进去审核队列却空的,状态词骗人)。
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(
                b.mapOrderToColumn({{status: 'stuck'}}, {{needs: [], blocked_reasons: ['reconcile.input_vat_mismatch'], flagged: []}})
            ));
            """)
        self.assertEqual(out, {"column": "materials"})

    def test_stuck_with_pending_purchase_flagged_goes_review(self):
        # 真有待裁决进项票(flagged 命中 W3 队列口径)才归「等你审」。
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(
                b.mapOrderToColumn(
                    {{status: 'stuck'}},
                    {{needs: [], blocked_reasons: [], flagged: [{{item_id: 'it-1', kind: 'purchase_invoice'}}]}}
                )
            ));
            """)
        self.assertEqual(out, {"column": "review"})

    def test_stuck_with_flagged_all_already_decided_goes_materials(self):
        # flagged 条目存在但已全部裁决(非进项票/非方向不明票)不算真队列——同上归 materials。
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(
                b.mapOrderToColumn(
                    {{status: 'stuck'}},
                    {{needs: [], blocked_reasons: [], flagged: [{{item_id: 'it-1', kind: 'sales_summary'}}]}}
                )
            ));
            """)
        self.assertEqual(out, {"column": "materials"})

    def test_stuck_without_detail_degrades_to_materials(self):
        # 没有逐条 detail(看板首屏用 list 端点批量拉,不是本单元测试关心的性能优化,只
        # 关心诚实降级)——没数据不等于"有事要审",不再乐观地塞进等你审列。
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(b.mapOrderToColumn({{status: 'stuck'}})));
            """)
        self.assertEqual(out, {"column": "materials"})

    def test_review_status_goes_sign_column(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(b.mapOrderToColumn({{status: 'review'}})));
            """)
        self.assertEqual(out, {"column": "sign"})

    def test_archive_status_goes_archived_column(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(b.mapOrderToColumn({{status: 'archive'}})));
            """)
        self.assertEqual(out, {"column": "archived"})

    def test_unknown_status_falls_back_and_flags(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(b.mapOrderToColumn({{status: 'some_future_status'}})));
            """)
        self.assertEqual(out, {"column": "materials", "unknown": True})


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class SummarizeCardTests(unittest.TestCase):
    def test_no_order(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(b.summarizeCard(null)));
            """)
        self.assertEqual(out, {"key": "card_no_order"})

    def test_blocked_reasons_take_priority_over_needs(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(b.summarizeCard(
                {{status: 'stuck', period: '2569-05'}},
                {{needs: ['bank_statement'], blocked_reasons: ['reconcile.input_vat_mismatch']}}
            )));
            """)
        self.assertEqual(out, {"key": "card_blocked_n", "vars": {"n": 1}})

    def test_needs_list_joins_real_field_names(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(b.summarizeCard(
                {{status: 'stuck', period: '2569-05'}},
                {{needs: ['sales_summary', 'bank_statement'], blocked_reasons: []}}
            )));
            """)
        self.assertEqual(
            out, {"key": "card_needs_list", "vars": {"list": "sales_summary、bank_statement"}}
        )

    def test_running_reports_current_step(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(b.summarizeCard(
                {{status: 'running', current_step: 'classify', period: '2569-05'}}
            )));
            """)
        self.assertEqual(out, {"key": "card_running_step", "vars": {"step": "classify"}})

    def test_review_with_tax_due_uses_formatted_money(self):
        out = _run_node(f"""
            global.window = global;
            global.localStorage = {{ getItem: () => null, setItem: () => {{}} }};
            require({json.dumps(str(AI_DIR / "ai-format.js"))});
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(b.summarizeCard(
                {{status: 'review', period: '2568-01'}},
                {{numbers: {{tax_due: '29263.28'}}}}
            )));
            """)
        self.assertEqual(out, {"key": "card_tax_due", "vars": {"amount": "฿29,263.28"}})

    def test_review_without_tax_due_falls_back_to_period(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(b.summarizeCard(
                {{status: 'review', period: '2568-01'}},
                {{numbers: {{}}}}
            )));
            """)
        self.assertEqual(out, {"key": "card_period_only", "vars": {"p": "2568-01"}})

    def test_insufficient_data_degrades_to_period_only(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(b.summarizeCard({{status: 'collecting', period: '2569-05'}})));
            """)
        self.assertEqual(out, {"key": "card_period_only", "vars": {"p": "2569-05"}})


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class CurrentPeriodBETests(unittest.TestCase):
    def test_converts_gregorian_to_buddhist_era(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify([
                b.currentPeriodBE(new Date(2026, 6, 9)),
                b.currentPeriodBE(new Date(2026, 0, 1)),
                b.currentPeriodBE(new Date(2025, 11, 31)),
            ]));
            """)
        self.assertEqual(out, ["2569-07", "2569-01", "2568-12"])

    def test_no_arg_uses_now_and_returns_valid_shape(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(b.currentPeriodBE()));
            """)
        self.assertRegex(out, r"^\d{4}-\d{2}$")

    def test_invalid_date_falls_back_to_now(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(b.currentPeriodBE(new Date('not-a-date'))));
            """)
        self.assertRegex(out, r"^\d{4}-\d{2}$")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class PeriodOptionsTests(unittest.TestCase):
    """开单账期可选(A3):当月在前 · 默认 14 个选项(当月 + 往前 13 个月) · 跨年借位正确。"""

    def test_default_count_spans_current_plus_13_months_back(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(b.periodOptions(undefined, new Date(2026, 6, 9))));
            """)
        self.assertEqual(len(out), 14)
        self.assertEqual(out[0], "2569-07")  # 当月排第一(选择器默认选中项)
        self.assertEqual(out[-1], "2568-06")  # 往前数到第 13 个月

    def test_crosses_buddhist_year_boundary(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(b.periodOptions(3, new Date(2026, 1, 15))));
            """)
        self.assertEqual(out, ["2569-02", "2569-01", "2568-12"])

    def test_custom_count_honored(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(b.periodOptions(3, new Date(2026, 6, 9)).length));
            """)
        self.assertEqual(out, 3)

    def test_no_date_uses_now_and_returns_current_month_first(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify([b.periodOptions()[0], b.currentPeriodBE()]));
            """)
        self.assertEqual(out[0], out[1])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class NeedsOpenControlTests(unittest.TestCase):
    """开单控件显隐判据(R2F-R3 拍板:常显)。此前判「当期没有工单」(A3 修复版)仍挡住
    "当期已有单、想再开/核对别的历史账期"这个真实场景——卡片上无处可点,只能绕去客户
    档案页。选中已有期由后端 open_work_order 幂等打开既有单,不会重复建单,故拿掉一切
    判断,任何卡片状态都恒显开单控件。"""

    def test_no_order_shows_control(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(b.needsOpenControl({{order: null}}, '2569-05')));
            """)
        self.assertTrue(out)

    def test_current_period_order_still_shows_control(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(b.needsOpenControl(
                {{order: {{period: '2569-05'}}}}, '2569-05'
            )));
            """)
        self.assertTrue(out)

    def test_historical_order_only_still_shows_control(self):
        out = _run_node(f"""
            const b = require({json.dumps(str(AI_DIR / "ai-board.js"))});
            process.stdout.write(JSON.stringify(b.needsOpenControl(
                {{order: {{period: '2568-06'}}}}, '2569-05'
            )));
            """)
        self.assertTrue(out)


if __name__ == "__main__":
    unittest.main()
