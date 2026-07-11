#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_recon_pure.py

E2 · 银行对账区(ai-recon-render.js)零 DOM/零 i18n 依赖的那一半逻辑:差异判定
(hasGap/diffState)+ 缺票行推 LINE 待问的 payload 打包(buildMissingStagePayload)。
HTML 拼装那一半依赖 at()/AI.state/AI.format/AI.viewer,不在 node 里独立可测,由
tests/e2e/_e2_bank_recon_local.spec.js 真浏览器覆盖(同 ai-pkg-render.js 先例)。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class HasGapTests(unittest.TestCase):
    def test_no_gap_when_both_lists_empty(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-recon-render.js"))});
            process.stdout.write(JSON.stringify(r.hasGap({{
                auto_matched: [{{}}], review: [{{}}], missing_invoice: [], unmatched_invoice: [],
            }})));
            """)
        self.assertFalse(out)

    def test_gap_when_missing_invoice_present(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-recon-render.js"))});
            process.stdout.write(JSON.stringify(r.hasGap({{
                missing_invoice: [{{amount: '30.00'}}], unmatched_invoice: [],
            }})));
            """)
        self.assertTrue(out)

    def test_gap_when_unmatched_invoice_present(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-recon-render.js"))});
            process.stdout.write(JSON.stringify(r.hasGap({{
                missing_invoice: [], unmatched_invoice: [{{candidate_id: 'it-1'}}],
            }})));
            """)
        self.assertTrue(out)

    def test_gap_false_on_null_recon(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-recon-render.js"))});
            process.stdout.write(JSON.stringify(r.hasGap(null)));
            """)
        self.assertFalse(out)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class DiffStateTests(unittest.TestCase):
    def test_ok_when_no_gap_ignores_stale_net_string(self):
        # 没有差异时净差一律归零显示,不管 diff.net 里格式化后残留什么字符串
        # (Decimal 输入精度副作用,不是真差异——见 workorder_recon_adapter._fmt)。
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-recon-render.js"))});
            process.stdout.write(JSON.stringify(r.diffState({{
                missing_invoice: [], unmatched_invoice: [], diff: {{net: '0.00'}},
            }})));
            """)
        self.assertEqual(out, {"ok": True, "net": "0"})

    def test_not_ok_surfaces_diff_net_when_gap_present(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-recon-render.js"))});
            process.stdout.write(JSON.stringify(r.diffState({{
                missing_invoice: [{{amount: '30.00'}}], unmatched_invoice: [],
                diff: {{net: '10.00'}},
            }})));
            """)
        self.assertEqual(out, {"ok": False, "net": "10.00"})


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class BuildMissingStagePayloadTests(unittest.TestCase):
    def test_builds_freeform_payload_anchored_on_bank_item(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-recon-render.js"))});
            process.stdout.write(JSON.stringify(
                r.buildMissingStagePayload('bank-1', 'note text')
            ));
            """)
        self.assertEqual(
            out,
            {
                "item_id": "bank-1",
                "question_type": "freeform",
                "payload": {"supplier": "", "invno": "", "amount": "", "note": "note text"},
            },
        )

    def test_no_bank_item_id_returns_null(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-recon-render.js"))});
            process.stdout.write(JSON.stringify(r.buildMissingStagePayload(null, 'x')));
            """)
        self.assertIsNone(out)


if __name__ == "__main__":
    unittest.main()
