#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_review_inbox_render_pure.py

UI 记债 #2(2026-07-14)守门:static/ai/ai-review-inbox-render.js 的
orderUndecidedTotal——「还有异常票据待裁决」提示条改读未决数(不再照 order.status
判断),按 flagged_groups 的 undecided_count 现算总数,缺字段(旧响应)回落 count。
同 test_ai_review_progress_pure.py 先例,真 node 直接 require 源文件断言输出。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_MOD = json.dumps(str(AI_DIR / "ai-review-inbox-render.js"))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class OrderUndecidedTotalTests(unittest.TestCase):
    def test_sums_undecided_count_across_groups(self):
        out = _run_node(f"""
            const r = require({_MOD});
            const order = {{flagged_groups: [
                {{undecided_count: 2, count: 4}}, {{undecided_count: 0, count: 1}},
            ]}};
            process.stdout.write(JSON.stringify(r.orderUndecidedTotal(order)));
            """)
        self.assertEqual(out, 2)

    def test_falls_back_to_count_when_field_missing(self):
        # 旧响应没带 undecided_count(后端投影未接线的场景)→ 回落总数,行为同旧版。
        out = _run_node(f"""
            const r = require({_MOD});
            const order = {{flagged_groups: [{{count: 3}}, {{count: 5}}]}};
            process.stdout.write(JSON.stringify(r.orderUndecidedTotal(order)));
            """)
        self.assertEqual(out, 8)

    def test_all_decided_yields_zero(self):
        # 全裁完:每组 undecided_count 归零 → 提示条该消失的口径。
        out = _run_node(f"""
            const r = require({_MOD});
            const order = {{flagged_groups: [
                {{undecided_count: 0, count: 4, decided_count: 4}},
                {{undecided_count: 0, count: 2, decided_count: 2}},
            ]}};
            process.stdout.write(JSON.stringify(r.orderUndecidedTotal(order)));
            """)
        self.assertEqual(out, 0)

    def test_no_flagged_groups_is_zero(self):
        out = _run_node(f"""
            const r = require({_MOD});
            process.stdout.write(JSON.stringify(r.orderUndecidedTotal({{flagged_groups: []}})));
            """)
        self.assertEqual(out, 0)


if __name__ == "__main__":
    unittest.main()
