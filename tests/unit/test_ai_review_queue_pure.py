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

    def test_sales_doc_kind_is_direction_ticket_for_confirm(self):
        # MC1-c.1:自动判本方销项票(kind=sales_doc)也走 P/S/X 卡(留人工过目/按 S 一键确认)。
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify([
                q.isDirectionTicket({{kind: 'sales_doc', flag_reason: 'sales_doc_review'}}),
                q.filterPurchaseQueue([
                    {{item_id: 'sd', kind: 'sales_doc', flag_reason: 'sales_doc_review'}},
                    {{item_id: 'p', kind: 'purchase_invoice', flag_reason: 'amount_math_fail'}},
                ]).map(x => x.item_id),
            ]));
            """)
        self.assertEqual(out, [True, ["sd", "p"]])


# severity 政策副本(flagSeverity/_WARN_REASONS)MC2-A3 已删,单一事实源移到后端
# services/workorder/verdict.py(见 test_workorder_verdict.SeverityPolicyTests);前端只渲染
# 后端下发的 verdict_hint.severity,不再有可脱管单测的前端 severity 纯函数。


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


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class RecalcFullValuesTests(unittest.TestCase):
    # J-C · J-A 建议值三字段改数(net/vat/grand_total),vatRaw 省略走 fullValues 路径。
    def test_full_values_carries_all_three_fields(self):
        out = _run_node(f"""
            {_REQUIRE_AI_FORMAT}
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify(q.buildDecisionPayload('it1', 'recalc', null, {{
                net: '58129.35', vat: '4069.05', grand: '62198.40',
            }})));
            """)
        self.assertEqual(
            out,
            {
                "item_id": "it1",
                "decision": "recalc",
                "values": {"vat": "4069.05", "net": "58129.35", "grand_total": "62198.40"},
            },
        )

    def test_full_values_missing_vat_returns_null(self):
        out = _run_node(f"""
            {_REQUIRE_AI_FORMAT}
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify(
                q.buildDecisionPayload('it1', 'recalc', null, {{net: '100', vat: '', grand: '107'}})
            ));
            """)
        self.assertIsNone(out)

    def test_full_values_optional_net_grand_omitted_when_blank(self):
        # net/grand 留空 → 不带这两个键,后端按票面等式自行兜底,不假装被改过。
        out = _run_node(f"""
            {_REQUIRE_AI_FORMAT}
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify(
                q.buildDecisionPayload('it1', 'recalc', null, {{net: '', vat: '4069.05', grand: ''}})
            ));
            """)
        self.assertEqual(
            out, {"item_id": "it1", "decision": "recalc", "values": {"vat": "4069.05"}}
        )


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class IsDecidedTests(unittest.TestCase):
    def test_local_decision_or_entry_decision_either_counts(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify([
                q.isDecided({{item_id: 'a'}}, null),
                q.isDecided({{item_id: 'a', decision: {{decision: 'face_value'}}}}, null),
                q.isDecided({{item_id: 'a'}}, {{decision: {{decision: 'recalc'}}}}),
            ]));
            """)
        self.assertEqual(out, [False, True, True])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class SplitByDecisionTests(unittest.TestCase):
    def test_splits_undecided_and_decided_by_entry_decision(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            const queue = [
                {{item_id: 'a'}},
                {{item_id: 'b', decision: {{decision: 'face_value'}}}},
                {{item_id: 'c'}},
            ];
            const split = q.splitByDecision(queue);
            process.stdout.write(JSON.stringify([
                split.undecided.map(x => x.item_id), split.decided.map(x => x.item_id),
            ]));
            """)
        self.assertEqual(out, [["a", "c"], ["b"]])

    def test_local_by_item_also_counts_as_decided(self):
        # 收件箱折叠共用同一份判断:session-local 乐观态也要挪进 decided。
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            const queue = [{{item_id: 'a'}}, {{item_id: 'b'}}];
            const local = {{a: {{decision: {{decision: 'exclude'}}}}}};
            const split = q.splitByDecision(queue, local);
            process.stdout.write(JSON.stringify([
                split.undecided.map(x => x.item_id), split.decided.map(x => x.item_id),
            ]));
            """)
        self.assertEqual(out, [["b"], ["a"]])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class UndecidedCountTests(unittest.TestCase):
    def test_counts_only_entries_without_any_decision(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            const queue = [{{item_id: 'a'}}, {{item_id: 'b'}}, {{item_id: 'c'}}];
            const local = {{b: {{decision: {{decision: 'face_value'}}}}}};
            process.stdout.write(JSON.stringify(q.undecidedCount(queue, local)));
            """)
        self.assertEqual(out, 2)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class SuggestionForItemTests(unittest.TestCase):
    def test_matches_by_type_and_item_id(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            const alerts = [
                {{type: 'taxid_typo_suspected', item_id: 'x'}},
                {{type: 'amount_read_suggested', item_id: 'it1', suggestion: {{vat: '4069.05'}}}},
            ];
            process.stdout.write(JSON.stringify(q.suggestionForItem(alerts, 'it1')));
            """)
        self.assertEqual(
            out,
            {"type": "amount_read_suggested", "item_id": "it1", "suggestion": {"vat": "4069.05"}},
        )

    def test_no_match_returns_null(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify(q.suggestionForItem([], 'it1')));
            """)
        self.assertIsNone(out)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class EditStartValuesTests(unittest.TestCase):
    def test_no_suggestion_falls_back_to_single_field_state(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            const entry = {{item_id: 'it1', ocr_read: {{vat: '100.00'}}}};
            process.stdout.write(JSON.stringify(q.editStartValues([], entry, null)));
            """)
        self.assertEqual(out, {"suggestion": None, "editValue": "100.00", "suggestValues": None})

    def test_suggestion_prefills_three_fields(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            const entry = {{item_id: 'it1', ocr_read: {{vat: '4060.05'}}}};
            const alerts = [{{
                type: 'amount_read_suggested', item_id: 'it1',
                suggestion: {{net: '58129.35', vat: '4069.05', grand: '62198.40'}},
            }}];
            const v = q.editStartValues(alerts, entry, null);
            process.stdout.write(JSON.stringify([v.suggestion !== null, v.editValue, v.suggestValues]));
            """)
        self.assertEqual(
            out,
            [True, None, {"net": "58129.35", "vat": "4069.05", "grand": "62198.40"}],
        )

    def test_prior_recalc_values_win_over_suggestion(self):
        # 改判场景:人工已改过的值优先于建议值(不覆盖已裁决的选择)。
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            const entry = {{item_id: 'it1', ocr_read: {{vat: '4060.05'}}}};
            const alerts = [{{
                type: 'amount_read_suggested', item_id: 'it1',
                suggestion: {{net: '58129.35', vat: '4069.05', grand: '62198.40'}},
            }}];
            const prior = {{decision: 'recalc', values: {{net: '58200.00', vat: '4074.00', grand_total: '62274.00'}}}};
            const v = q.editStartValues(alerts, entry, prior);
            process.stdout.write(JSON.stringify(v.suggestValues));
            """)
        self.assertEqual(out, {"net": "58200.00", "vat": "4074.00", "grand": "62274.00"})


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ActionOfDecisionTests(unittest.TestCase):
    def test_maps_known_decisions_and_no_fallback_outside_map(self):
        # 映射外无兜底(简化角):bulkDecisionTemplate 只产 face_value/exclude/recalc,
        # 未知词显式落空暴露,不静默套 'assign' 错标签。
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify([
                q.actionOfDecision({{decision: 'face_value'}}),
                q.actionOfDecision({{decision: 'exclude'}}),
                q.actionOfDecision({{decision: 'recalc'}}),
                q.actionOfDecision({{decision: 'assign_kind', kind: 'purchase_invoice'}}),
                q.actionOfDecision(null),
            ]));
            """)
        self.assertEqual(out, ["accept", "exclude", "recalc", None, None])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class DecidedValueTests(unittest.TestCase):
    def test_no_effective_decision_falls_back_uncorrected(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify(q.decidedValue(null, 'vat', '100.00')));
            """)
        self.assertEqual(out, {"value": "100.00", "corrected": False})

    def test_recalc_value_differing_from_fallback_is_corrected(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            const decision = {{decision: 'recalc', values: {{vat: '4069.05'}}}};
            process.stdout.write(JSON.stringify(q.decidedValue(decision, 'vat', '4060.05')));
            """)
        self.assertEqual(out, {"value": "4069.05", "corrected": True})

    def test_recalc_missing_key_falls_back_uncorrected(self):
        # 老单字段裁决只填了 vat——net/grand_total 键不存在,诚实回落原读数,不假装改过。
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            const decision = {{decision: 'recalc', values: {{vat: '4069.05'}}}};
            process.stdout.write(JSON.stringify(q.decidedValue(decision, 'net', '58048.40')));
            """)
        self.assertEqual(out, {"value": "58048.40", "corrected": False})

    def test_recalc_value_equal_to_fallback_is_not_corrected(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            const decision = {{decision: 'recalc', values: {{vat: '100.00'}}}};
            process.stdout.write(JSON.stringify(q.decidedValue(decision, 'vat', '100.00')));
            """)
        self.assertEqual(out, {"value": "100.00", "corrected": False})


if __name__ == "__main__":
    unittest.main()
