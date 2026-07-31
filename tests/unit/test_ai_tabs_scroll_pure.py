#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_tabs_scroll_pure.py

static/ai/ai-tabs-scroll.js 的边界算术守门(同 test_ai_review_queue_pure.py 先例,真 node
require 源文件断言输出)。DOM 那一半(滚 scrollLeft / 挂 tabs-more-* / 渐隐边)在真浏览器
里验:tests/e2e/_ai_mobile_reach_local.spec.js。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_MODULE = json.dumps(str(AI_DIR / "ai-tabs-scroll.js"))


def _rect(left, right):
    return {"left": left, "right": right}


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class EdgeShiftTests(unittest.TestCase):
    def _shift(self, bar, btn, peek=None):
        arg = "" if peek is None else f", {peek}"
        return _run_node(f"""
            const t = require({_MODULE});
            process.stdout.write(JSON.stringify(
                t.edgeShift({json.dumps(bar)}, {json.dumps(btn)}{arg})
            ));
            """)

    def test_fully_visible_tab_does_not_move(self):
        self.assertEqual(self._shift(_rect(79, 375), _rect(120, 200)), 0)

    def test_tab_clipped_on_the_right_scrolls_right_with_peek(self):
        # 2026-07-30 泰语实测的那一处:容器 79..375,当前项 315..404 被右边切掉 29px。
        self.assertEqual(self._shift(_rect(79, 375), _rect(315, 404), 26), 55)

    def test_tab_clipped_on_the_left_scrolls_back_with_peek(self):
        self.assertEqual(self._shift(_rect(79, 375), _rect(40, 100), 26), -65)

    def test_default_peek_is_used_when_omitted(self):
        self.assertEqual(self._shift(_rect(0, 100), _rect(90, 130)), 30 + _peek())

    def test_touching_the_edge_exactly_is_not_clipped(self):
        self.assertEqual(self._shift(_rect(79, 375), _rect(79, 375)), 0)


def _peek() -> int:
    return _run_node(f"""
        const t = require({_MODULE});
        process.stdout.write(JSON.stringify(t.PEEK));
        """)


if __name__ == "__main__":
    unittest.main()
