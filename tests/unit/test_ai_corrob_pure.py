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


if __name__ == "__main__":
    unittest.main()
