#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_review_verdict_pure.py

MC1-b2 审核收件箱纯函数守门:static/ai/ai-review-verdict.js 的置信度 class/i18n key
映射、判据人话回退(narrative_key 缺失 → flag_reason 原文)、批量建议裁决模板
（narrative_key 命名空间随 services/workorder/verdict.py 手工对齐)、组级批量放行判定
(groupCanBulk——低置信度混入即禁止整组批量)。同 test_ai_review_queue_pure.py 先例,
真 node 直接 require 源文件断言输出,不进浏览器。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ConfidenceMappingTests(unittest.TestCase):
    def test_chip_class_and_label_key(self):
        out = _run_node(f"""
            const v = require({json.dumps(str(AI_DIR / "ai-review-verdict.js"))});
            process.stdout.write(JSON.stringify([
                v.confidenceChipClass('high'),
                v.confidenceChipClass('mid'),
                v.confidenceChipClass('low'),
                v.confidenceChipClass('bogus'),
                v.confidenceLabelKey('high'),
                v.confidenceLabelKey('mid'),
                v.confidenceLabelKey('low'),
            ]));
            """)
        self.assertEqual(
            out,
            ["g", "w", "b", "b", "riq_conf_high", "riq_conf_mid", "riq_conf_low"],
        )


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class NarrativeOfTests(unittest.TestCase):
    def test_known_key_carries_params(self):
        out = _run_node(f"""
            const v = require({json.dumps(str(AI_DIR / "ai-review-verdict.js"))});
            const hint = {{narrative_key: 'verdict_amount_math_fail', params: {{net: '100.00'}}}};
            process.stdout.write(JSON.stringify(v.narrativeOf(hint, 'amount_math_fail')));
            """)
        self.assertEqual(out, {"key": "verdict_amount_math_fail", "vars": {"net": "100.00"}})

    def test_unknown_key_falls_back_to_raw_flag_reason(self):
        out = _run_node(f"""
            const v = require({json.dumps(str(AI_DIR / "ai-review-verdict.js"))});
            process.stdout.write(JSON.stringify(v.narrativeOf({{narrative_key: null}}, 'some_new_reason:x')));
            """)
        self.assertEqual(out, {"key": None, "fallbackText": "some_new_reason:x"})

    def test_missing_hint_falls_back_too(self):
        out = _run_node(f"""
            const v = require({json.dumps(str(AI_DIR / "ai-review-verdict.js"))});
            process.stdout.write(JSON.stringify(v.narrativeOf(null, 'ocr_error:page2')));
            """)
        self.assertEqual(out, {"key": None, "fallbackText": "ocr_error:page2"})


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class BulkDecisionTemplateTests(unittest.TestCase):
    """MC2-A3:建议裁决改读后端 verdict_hint.suggested_decision(政策副本 _BULK_TEMPLATES 已删),
    前端只透传,不再自持 flag_reason→模板表。"""

    def test_reads_suggested_decision_from_backend_hint(self):
        out = _run_node(f"""
            const v = require({json.dumps(str(AI_DIR / "ai-review-verdict.js"))});
            process.stdout.write(JSON.stringify([
                v.bulkDecisionTemplate({{verdict_hint: {{suggested_decision: {{decision: 'assign_kind', kind: 'sales_doc'}}}}}}),
                v.bulkDecisionTemplate({{verdict_hint: {{suggested_decision: {{decision: 'exclude'}}}}}}),
            ]));
            """)
        self.assertEqual(
            out,
            [{"decision": "assign_kind", "kind": "sales_doc"}, {"decision": "exclude"}],
        )

    def test_no_suggested_decision_yields_null(self):
        out = _run_node(f"""
            const v = require({json.dumps(str(AI_DIR / "ai-review-verdict.js"))});
            process.stdout.write(JSON.stringify([
                v.bulkDecisionTemplate({{verdict_hint: {{suggested_decision: null}}}}),
                v.bulkDecisionTemplate({{verdict_hint: {{}}}}),
                v.bulkDecisionTemplate({{}}),
                v.bulkDecisionTemplate(null),
            ]));
            """)
        self.assertEqual(out, [None, None, None, None])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class GroupCanBulkTests(unittest.TestCase):
    _SD = "suggested_decision: {decision: 'assign_kind', kind: 'sales_doc'}"

    def test_uniform_high_confidence_allows_bulk(self):
        out = _run_node(f"""
            const v = require({json.dumps(str(AI_DIR / "ai-review-verdict.js"))});
            const items = [
                {{verdict_hint: {{confidence: 'high', {self._SD}}}}},
                {{verdict_hint: {{confidence: 'mid', {self._SD}}}}},
            ];
            process.stdout.write(JSON.stringify(v.groupCanBulk(items)));
            """)
        self.assertTrue(out)

    def test_one_low_confidence_item_blocks_whole_group(self):
        out = _run_node(f"""
            const v = require({json.dumps(str(AI_DIR / "ai-review-verdict.js"))});
            const items = [
                {{verdict_hint: {{confidence: 'high', {self._SD}}}}},
                {{verdict_hint: {{confidence: 'low', {self._SD}}}}},
            ];
            process.stdout.write(JSON.stringify(v.groupCanBulk(items)));
            """)
        self.assertFalse(out)

    def test_no_suggested_decision_blocks_bulk_even_at_high_confidence(self):
        out = _run_node(f"""
            const v = require({json.dumps(str(AI_DIR / "ai-review-verdict.js"))});
            const items = [{{verdict_hint: {{confidence: 'high'}}}}];
            process.stdout.write(JSON.stringify(v.groupCanBulk(items)));
            """)
        self.assertFalse(out)

    def test_empty_group_cannot_bulk(self):
        out = _run_node(f"""
            const v = require({json.dumps(str(AI_DIR / "ai-review-verdict.js"))});
            process.stdout.write(JSON.stringify(v.groupCanBulk([])));
            """)
        self.assertFalse(out)


if __name__ == "__main__":
    unittest.main()
