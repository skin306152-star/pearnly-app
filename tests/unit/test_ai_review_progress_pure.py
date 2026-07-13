#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_review_progress_pure.py

MC2-A3 裁决后进度轮询状态机纯函数守门:static/ai/ai-review-progress.js 的指数退避排期
(有限次数封顶)、基线快照、落定判据(基线内工单是否都重现于队列 = 重跑落回 review)。
同 test_ai_review_queue_pure.py 先例,真 node 直接 require 源文件断言输出,不进浏览器。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_MOD = json.dumps(str(AI_DIR / "ai-review-progress.js"))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class NextDelayTests(unittest.TestCase):
    def test_exponential_backoff_capped_and_finite(self):
        out = _run_node(f"""
            const p = require({_MOD});
            const seq = [];
            for (let i = 0; i <= p.MAX_ATTEMPTS; i++) seq.push(p.nextDelayMs(i));
            process.stdout.write(JSON.stringify(seq));
            """)
        # 1500,3000,6000,12000,12000(封顶),12000,然后 null(退避次数用尽)
        self.assertEqual(out, [1500, 3000, 6000, 12000, 12000, 12000, None])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class SettledTests(unittest.TestCase):
    _Q_BOTH = (
        "{clients:[{orders:[{work_order_id:'a', updated_at:'t1'},"
        "{work_order_id:'b', updated_at:'t1'}]}]}"
    )

    def test_baseline_captures_all_order_timestamps(self):
        out = _run_node(f"""
            const p = require({_MOD});
            process.stdout.write(JSON.stringify(p.baseline({self._Q_BOTH})));
            """)
        self.assertEqual(out, {"a": "t1", "b": "t1"})

    def test_not_settled_while_a_watched_order_absent_from_queue(self):
        # b 还在 running(队列读模型看不到 running)→ 未落定,继续退避
        out = _run_node(f"""
            const p = require({_MOD});
            const base = {{a: 't1', b: 't1'}};
            const now = {{clients:[{{orders:[{{work_order_id:'a', updated_at:'t2'}}]}}]}};
            process.stdout.write(JSON.stringify(p.settled(now, base)));
            """)
        self.assertFalse(out)

    def test_settled_when_all_watched_orders_reappear(self):
        out = _run_node(f"""
            const p = require({_MOD});
            const base = {{a: 't1', b: 't1'}};
            process.stdout.write(JSON.stringify(p.settled({self._Q_BOTH}, base)));
            """)
        self.assertTrue(out)

    def test_empty_baseline_is_trivially_settled(self):
        out = _run_node(f"""
            const p = require({_MOD});
            process.stdout.write(JSON.stringify(p.settled({{clients:[]}}, {{}})));
            """)
        self.assertTrue(out)


if __name__ == "__main__":
    unittest.main()
