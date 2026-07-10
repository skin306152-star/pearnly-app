#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_review_queue_pure.py

Pearnly AI(M1-W3)人审队列纯函数守门:static/ai/ai-review-queue.js 的过滤/分级/
VAT 校验/裁决 payload 构造/文件名——同 test_ai_pure_modules.py 先例,真 node 直接
require 源文件断言输出,不进浏览器。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

# ai-review-queue.js 的 parseVat 转发给 AI.format.parseAmount(照 ai-viewer.js 的
# esc()→AI.state.esc 先例)——node 单测独立进程里没人挂 AI.format,这里先 require
# ai-format.js 把它挂上 globalThis,后续 require 的 ai-review-queue.js 才能真正解析。
_REQUIRE_AI_FORMAT = f'require({json.dumps(str(AI_DIR / "ai-format.js"))});\n'


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class FilterPurchaseQueueTests(unittest.TestCase):
    def test_keeps_only_purchase_invoice_kind_in_given_order(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            const flagged = [
                {{item_id: 'a', kind: 'purchase_invoice'}},
                {{item_id: 'b', kind: 'sales_direction_unhandled'}},
                {{item_id: 'c', kind: 'purchase_invoice'}},
                {{item_id: 'd', kind: 'bank_statement'}},
            ];
            process.stdout.write(JSON.stringify(q.filterPurchaseQueue(flagged).map(x => x.item_id)));
            """)
        self.assertEqual(out, ["a", "c"])

    def test_non_array_input_returns_empty(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify([q.filterPurchaseQueue(null), q.filterPurchaseQueue(undefined)]));
            """)
        self.assertEqual(out, [[], []])

    def test_direction_tickets_of_both_prefixes_are_collected_into_queue(self):
        # G1/G1R2 黑洞根治:两类方向票(kind=unknown)都进队列——direction_ambiguous(锚点不明)
        # 与 sales_direction_unhandled(疑似本方销项)。后者过去被漏收 → 无裁决照样出包。
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            const flagged = [
                {{item_id: 'a', kind: 'purchase_invoice', flag_reason: 'amount_math_fail'}},
                {{item_id: 'd', kind: 'unknown', flag_reason: 'direction_ambiguous'}},
                {{item_id: 'x', kind: 'unknown', flag_reason: 'sales_direction_unhandled'}},
                {{item_id: 'b', kind: 'bank_statement'}},
            ];
            process.stdout.write(JSON.stringify(q.filterPurchaseQueue(flagged).map(x => x.item_id)));
            """)
        self.assertEqual(out, ["a", "d", "x"])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class IsDirectionTicketTests(unittest.TestCase):
    def test_both_direction_prefixes_are_direction_others_are_not(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify([
                q.isDirectionTicket({{flag_reason: 'direction_ambiguous'}}),
                q.isDirectionTicket({{flag_reason: 'direction_ambiguous:deposit'}}),
                q.isDirectionTicket({{flag_reason: 'sales_direction_unhandled'}}),
                q.isDirectionTicket({{flag_reason: 'amount_math_fail'}}),
                q.isDirectionTicket({{flag_reason: ''}}),
                q.isDirectionTicket(null),
            ]));
            """)
        self.assertEqual(out, [True, True, True, False, False, False])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class FlagSeverityTests(unittest.TestCase):
    def test_math_fail_and_ocr_error_are_crit(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify([
                q.flagSeverity('amount_math_fail'),
                q.flagSeverity('ocr_error:ValueError'),
                q.flagSeverity('anything_unknown'),
                q.flagSeverity(''),
            ]));
            """)
        self.assertEqual(out, ["crit", "crit", "crit", "crit"])

    def test_low_confidence_and_validation_warning_are_warn(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify([
                q.flagSeverity('ocr_low_confidence:needs_review'),
                q.flagSeverity('ocr_validation_warning'),
            ]));
            """)
        self.assertEqual(out, ["warn", "warn"])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class FlagReasonKeyTests(unittest.TestCase):
    def test_maps_known_reasons_including_colon_suffixed_ones(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify([
                q.flagReasonKey('amount_math_fail'),
                q.flagReasonKey('ocr_validation_warning'),
                q.flagReasonKey('ocr_low_confidence:needs_review'),
                q.flagReasonKey('ocr_error:ValueError'),
            ]));
            """)
        self.assertEqual(
            out,
            ["rv_flag_math_fail", "rv_flag_validation", "rv_flag_low_conf", "rv_flag_ocr_error"],
        )

    def test_unknown_or_empty_reason_falls_back_to_null(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify([
                q.flagReasonKey('some_future_reason'),
                q.flagReasonKey(''),
                q.flagReasonKey(null),
            ]));
            """)
        self.assertEqual(out, [None, None, None])

    def test_direction_ambiguous_maps_to_direction_key(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify([
                q.flagReasonKey('direction_ambiguous'),
                q.flagReasonKey('direction_ambiguous:deposit'),
            ]));
            """)
        self.assertEqual(out, ["rv_flag_direction", "rv_flag_direction"])

    def test_sales_direction_unhandled_maps_to_own_key(self):
        # 收编第二类方向票:自家==卖方=疑似本方销项,人话与 direction_ambiguous 区分呈现。
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify(q.flagReasonKey('sales_direction_unhandled')));
            """)
        self.assertEqual(out, "rv_flag_sales_direction")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ParseVatTests(unittest.TestCase):
    def test_accepts_plain_and_thousands_separated_decimals(self):
        out = _run_node(f"""
            {_REQUIRE_AI_FORMAT}
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify([
                q.parseVat('4069.05'), q.parseVat('4,069.05'), q.parseVat('  4069  '), q.parseVat('0'),
            ]));
            """)
        self.assertEqual(out, ["4069.05", "4069.05", "4069", "0"])

    def test_rejects_empty_non_numeric_and_too_many_decimals(self):
        out = _run_node(f"""
            {_REQUIRE_AI_FORMAT}
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify([
                q.parseVat(''), q.parseVat('   '), q.parseVat('abc'), q.parseVat('4069.055'), q.parseVat(null),
            ]));
            """)
        self.assertEqual(out, [None, None, None, None, None])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class BuildDecisionPayloadTests(unittest.TestCase):
    def test_accept_and_exclude_need_no_values(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify([
                q.buildDecisionPayload('it1', 'accept'),
                q.buildDecisionPayload('it1', 'exclude'),
            ]));
            """)
        self.assertEqual(
            out,
            [
                {"item_id": "it1", "decision": "face_value"},
                {"item_id": "it1", "decision": "exclude"},
            ],
        )

    def test_recalc_carries_parsed_vat(self):
        out = _run_node(f"""
            {_REQUIRE_AI_FORMAT}
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify(q.buildDecisionPayload('it1', 'recalc', '4,069.05')));
            """)
        self.assertEqual(
            out, {"item_id": "it1", "decision": "recalc", "values": {"vat": "4069.05"}}
        )

    def test_recalc_without_valid_vat_returns_null_not_a_request(self):
        out = _run_node(f"""
            {_REQUIRE_AI_FORMAT}
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify([
                q.buildDecisionPayload('it1', 'recalc', ''),
                q.buildDecisionPayload('it1', 'recalc', 'abc'),
                q.buildDecisionPayload('it1', 'unknown-action'),
            ]));
            """)
        self.assertEqual(out, [None, None, None])

    def test_direction_actions_build_assign_kind_payloads(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify([
                q.buildDecisionPayload('it1', 'assign_purchase'),
                q.buildDecisionPayload('it1', 'assign_sales'),
                q.buildDecisionPayload('it1', 'assign_nontax'),
            ]));
            """)
        self.assertEqual(
            out,
            [
                {"item_id": "it1", "decision": "assign_kind", "kind": "purchase_invoice"},
                {"item_id": "it1", "decision": "assign_kind", "kind": "sales_doc"},
                {"item_id": "it1", "decision": "assign_kind", "kind": "non_tax"},
            ],
        )


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class DecisionChipKeyTests(unittest.TestCase):
    def test_maps_known_decisions_and_falls_back_to_null(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify([
                q.decisionChipKey({{decision: 'face_value'}}),
                q.decisionChipKey({{decision: 'recalc'}}),
                q.decisionChipKey({{decision: 'exclude'}}),
                q.decisionChipKey({{decision: 'nonsense'}}),
                q.decisionChipKey(null),
            ]));
            """)
        self.assertEqual(
            out,
            ["rv_chip_accepted", "rv_chip_recalc", "rv_chip_excluded", None, None],
        )

    def test_assign_kind_decisions_map_by_direction(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify([
                q.decisionChipKey({{decision: 'assign_kind', kind: 'purchase_invoice'}}),
                q.decisionChipKey({{decision: 'assign_kind', kind: 'sales_doc'}}),
                q.decisionChipKey({{decision: 'assign_kind', kind: 'non_tax'}}),
                q.decisionChipKey({{decision: 'assign_kind', kind: 'bogus'}}),
            ]));
            """)
        self.assertEqual(
            out,
            ["rv_chip_dir_purchase", "rv_chip_dir_sales", "rv_chip_dir_nontax", None],
        )


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class FileNameTests(unittest.TestCase):
    def test_extracts_basename_from_windows_and_posix_paths(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify([
                q.fileName('C:\\\\Users\\\\skin3\\\\Desktop\\\\5\\u6708\\\\IMG_2647.JPG'),
                q.fileName('/srv/storage/wo/IMG_2648.JPG'),
                q.fileName(''),
                q.fileName(null),
            ]));
            """)
        self.assertEqual(out, ["IMG_2647.JPG", "IMG_2648.JPG", "", ""])


if __name__ == "__main__":
    unittest.main()
