#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_desk_render_pure.py

Pearnly AI(FD-0d)总台纯函数守门:ai-desk-render.js 的 deriveCard(六种系统卡判定)/
needCoverage(需料对照 ✓✗)/confirmReady(确认开工可点前置校验)。同 test_ai_board_pure.py
的 node subprocess require 手法——真 node 跑源文件,不进浏览器。

deriveCard 是本批最关键的纯函数:一份合同(public_view + FD-0d 补的 brain_suggestion)
+ 本次会话即时结果(liveExtra)→ 该出哪张卡,四种系统卡(盘点/合同/进度/拒绝)+ 降级卡 +
两个收尾态(dismissed/empty)逐一覆盖,含"刷新后靠 brain_suggestion 重建合同卡"这条
关键路径(施工总册 §2.2「消息流不建聊天表,靠服务端重建」的验收点)。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

DESK = str(AI_DIR / "ai-desk-render.js")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class DeriveCardTests(unittest.TestCase):
    def _derive(self, contract_json, live_extra_json="undefined"):
        return _run_node(f"""
            const d = require({json.dumps(DESK)});
            process.stdout.write(JSON.stringify(
                d.deriveCard({contract_json}, {live_extra_json})
            ));
            """)

    def test_confirmed_status_is_progress_card(self):
        out = self._derive('{"id":"c1","status":"confirmed"}')
        self.assertEqual(out["kind"], "progress")

    def test_executing_status_is_progress_card(self):
        out = self._derive('{"id":"c1","status":"executing"}')
        self.assertEqual(out["kind"], "progress")

    def test_delivered_status_is_progress_card(self):
        out = self._derive('{"id":"c1","status":"delivered"}')
        self.assertEqual(out["kind"], "progress")

    def test_archive_status_is_progress_card(self):
        out = self._derive('{"id":"c1","status":"archive"}')
        self.assertEqual(out["kind"], "progress")

    def test_rejected_status_is_dismissed_card(self):
        out = self._derive('{"id":"c1","status":"rejected"}')
        self.assertEqual(out["kind"], "dismissed")

    def test_live_degraded_takes_priority_over_persisted_suggestion(self):
        # 会话内刚拿到的降级信号必须优先于旧的持久化建议——降级是当次会话的临时状态,
        # 不该被上一轮成功的建议掩盖(否则用户会看到过期的合同卡,以为大脑仍在正常工作)。
        out = self._derive(
            '{"id":"c1","status":"draft","brain_suggestion":{"intent":"monthly_vat"}}',
            '{"degraded":true,"reason":"brain_timeout"}',
        )
        self.assertEqual(out["kind"], "degraded")
        self.assertEqual(out["reason"], "brain_timeout")

    def test_unsupported_intent_is_rejected_card(self):
        out = self._derive(
            '{"id":"c1","status":"draft"}',
            '{"suggestion":{"intent":"unsupported","client_id":null,"period":null}}',
        )
        self.assertEqual(out["kind"], "rejected")

    def test_unknown_intent_outside_closed_set_is_rejected_card(self):
        # 大脑理论上不该编造闭集外意图(interpret.py 已机器闸),但前端渲染层也不该
        # 假装认识——防御性地同归拒绝卡,不是静默展示一张没有 meta 的坏合同卡。
        out = self._derive(
            '{"id":"c1","status":"draft"}',
            '{"suggestion":{"intent":"pnd50","client_id":null,"period":null}}',
        )
        self.assertEqual(out["kind"], "rejected")

    def test_enabled_intent_suggestion_is_contract_card(self):
        out = self._derive(
            '{"id":"c1","status":"draft"}',
            '{"suggestion":{"intent":"monthly_vat","client_suggestion":7,"period":"2569-05"}}',
        )
        self.assertEqual(out["kind"], "contract")
        self.assertEqual(out["suggestion"]["intent"], "monthly_vat")

    def test_refresh_rebuilds_contract_card_from_persisted_brain_suggestion(self):
        # 刷新场景的核心断言:没有 liveExtra(会话已丢),纯靠 public_view 里持久化的
        # brain_suggestion 字段重建合同卡——这是 FD-0d 对 contract_store.public_view()
        # 的补丁(施工总册 §2.2「刷新不丢」)存在的理由。
        out = self._derive(
            '{"id":"c1","status":"draft","brain_suggestion":{"intent":"monthly_vat","client_suggestion":7,"period":"2569-05"}}'
        )
        self.assertEqual(out["kind"], "contract")
        self.assertEqual(out["suggestion"]["client_suggestion"], 7)

    def test_files_only_no_suggestion_is_inventory_card(self):
        out = self._derive(
            '{"id":"c1","status":"draft"}',
            '{"inventory":{"groups":[{"group":"image","count":3,"names":[]}],"total":3,"recognized":3,"unrecognized":0}}',
        )
        self.assertEqual(out["kind"], "inventory")
        self.assertEqual(out["inventory"]["total"], 3)

    def test_no_files_no_suggestion_is_empty_card(self):
        out = self._derive('{"id":"c1","status":"draft"}')
        self.assertEqual(out["kind"], "empty")

    def test_missing_status_defaults_to_empty_not_crash(self):
        out = self._derive("{}")
        self.assertEqual(out["kind"], "empty")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class NeedCoverageTests(unittest.TestCase):
    def test_satisfied_need_marked_true(self):
        out = _run_node(f"""
            const d = require({json.dumps(DESK)});
            process.stdout.write(JSON.stringify(d.needCoverage(
                ['fd_need_sales_summary'],
                [{{group:'spreadsheet', count: 2}}]
            )));
            """)
        self.assertEqual(out, [{"need": "fd_need_sales_summary", "satisfied": True}])

    def test_missing_need_marked_false(self):
        out = _run_node(f"""
            const d = require({json.dumps(DESK)});
            process.stdout.write(JSON.stringify(d.needCoverage(
                ['fd_need_bank_statement'],
                [{{group:'spreadsheet', count: 2}}]
            )));
            """)
        self.assertEqual(out, [{"need": "fd_need_bank_statement", "satisfied": False}])

    def test_zero_count_group_does_not_count_as_present(self):
        out = _run_node(f"""
            const d = require({json.dumps(DESK)});
            process.stdout.write(JSON.stringify(d.needCoverage(
                ['fd_need_sales_summary'],
                [{{group:'spreadsheet', count: 0}}]
            )));
            """)
        self.assertEqual(out, [{"need": "fd_need_sales_summary", "satisfied": False}])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ConfirmReadyTests(unittest.TestCase):
    def test_all_three_fields_and_enabled_intent_ready(self):
        out = _run_node(f"""
            const d = require({json.dumps(DESK)});
            process.stdout.write(JSON.stringify(d.confirmReady(
                {{clientId:'7', period:'2569-05', intent:'monthly_vat'}}
            )));
            """)
        self.assertTrue(out)

    def test_missing_client_not_ready(self):
        out = _run_node(f"""
            const d = require({json.dumps(DESK)});
            process.stdout.write(JSON.stringify(d.confirmReady(
                {{period:'2569-05', intent:'monthly_vat'}}
            )));
            """)
        self.assertFalse(out)

    def test_not_yet_enabled_intent_not_ready(self):
        # 账套红线的另一半:即便三值都填了,意图若不在开放闭集也不能点确认——
        # confirm() 服务端会 422 intent_not_enabled,前端不该让人白等一次网络往返。
        out = _run_node(f"""
            const d = require({json.dumps(DESK)});
            process.stdout.write(JSON.stringify(d.confirmReady(
                {{clientId:'7', period:'2569-05', intent:'bank_match'}}
            )));
            """)
        self.assertFalse(out)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class SuggestionPeriodBETests(unittest.TestCase):
    """interpret 建议期间(公历)→ 佛历下拉值换算:纪年接缝,换算不进选项集按无建议返 null。"""

    def _conv(self, period, periods):
        return _run_node(f"""
            const d = require({json.dumps(DESK)});
            process.stdout.write(JSON.stringify(d.suggestionPeriodBE(
                {json.dumps(period)}, {json.dumps(periods)}
            )));
            """)

    def test_gregorian_converts_to_be(self):
        self.assertEqual(self._conv("2026-06", ["2569-07", "2569-06"]), "2569-06")

    def test_already_be_passes_through(self):
        self.assertEqual(self._conv("2569-06", ["2569-07", "2569-06"]), "2569-06")

    def test_not_in_options_returns_null(self):
        self.assertIsNone(self._conv("2020-01", ["2569-07", "2569-06"]))

    def test_malformed_returns_null(self):
        self.assertIsNone(self._conv("06/2569", ["2569-06"]))
        self.assertIsNone(self._conv(None, ["2569-06"]))


if __name__ == "__main__":
    unittest.main()
