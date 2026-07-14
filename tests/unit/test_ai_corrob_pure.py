#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_corrob_pure.py

MC1-c.1 · 销项佐证卡(ai-corrob.js)零 DOM/零 i18n 的那一半:covered_state → chip 分类。
HTML 拼装依赖 at()/AI.state/AI.format,不在 node 里独立可测,由本地全栈真浏览器 E2E 覆盖
(同 ai-recon-render.js 先例)。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class CoveredChipKeyTests(unittest.TestCase):
    def _key(self, crb):
        return _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-corrob.js"))});
            process.stdout.write(JSON.stringify(r.coveredChipKey({json.dumps(crb)})));
            """)

    def test_amber_passthrough(self):
        self.assertEqual(self._key({"covered_state": "amber"}), "amber")

    def test_green_passthrough(self):
        self.assertEqual(self._key({"covered_state": "green"}), "green")

    def test_needs_passthrough(self):
        self.assertEqual(self._key({"covered_state": "needs"}), "needs")

    def test_unknown_state_falls_back_to_needs(self):
        self.assertEqual(self._key({"covered_state": "weird"}), "needs")

    def test_null_falls_back_to_needs(self):
        self.assertEqual(self._key(None), "needs")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class SrcVariantTests(unittest.TestCase):
    """source → 文案族选择(SA-2b:EDC 聚合卡与 c.1 逐票卡同一套渲染、不同措辞)。"""

    def _variant(self, crb):
        return _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-corrob.js"))});
            process.stdout.write(JSON.stringify(r.srcVariant({json.dumps(crb)})));
            """)

    def test_edc_source_selected(self):
        self.assertEqual(self._variant({"source": "edc_aggregate"}), "edc_aggregate")

    def test_invoice_source_selected(self):
        self.assertEqual(self._variant({"source": "invoice_aggregate"}), "invoice_aggregate")

    def test_unknown_or_missing_source_falls_back_to_invoice(self):
        self.assertEqual(self._variant({"source": "weird"}), "invoice_aggregate")
        self.assertEqual(self._variant(None), "invoice_aggregate")


if __name__ == "__main__":
    unittest.main()
