#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_review_progress_pure.py

MC2-A3 裁决后进度轮询状态机纯函数守门:static/ai/ai-review-progress.js 的指数退避排期
(有限次数封顶)、基线快照、落定判据。S3(2026-07-17)语义翻新:读模型连 running 一起
下发,「消失=在跑」作废——落定 = 基线工单全部以非 running 状态重现于队列;基线外的
running 不绑架轮询(simplify 收口)。同 test_ai_review_queue_pure.py 先例,真 node 断言。
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
            process.stdout.write(JSON.stringify([p.MAX_ATTEMPTS, seq]));
            """)
        max_attempts, seq = out
        # S3:封顶提到 40 次 ≈8 分钟(防挂机标签页无限轮询;超时后手动「刷新」钮兜底)
        self.assertEqual(max_attempts, 40)
        self.assertEqual(seq[:4], [1500, 3000, 6000, 12000])
        self.assertEqual(seq[4:-1], [12000] * 36)  # 12s 封顶一路到次数用尽
        self.assertIsNone(seq[-1])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class SettledTests(unittest.TestCase):
    _Q_BOTH = (
        "{clients:[{orders:[{work_order_id:'a', status:'review', updated_at:'t1'},"
        "{work_order_id:'b', status:'stuck', updated_at:'t1'}]}]}"
    )

    def test_baseline_captures_all_order_timestamps(self):
        out = _run_node(f"""
            const p = require({_MOD});
            process.stdout.write(JSON.stringify(p.baseline({self._Q_BOTH})));
            """)
        self.assertEqual(out, {"a": "t1", "b": "t1"})

    def test_not_settled_while_a_watched_order_absent_from_queue(self):
        # b 缺席(极端时序:状态翻转间隙)→ 未落定,继续退避
        out = _run_node(f"""
            const p = require({_MOD});
            const base = {{a: 't1', b: 't1'}};
            const now = {{clients:[{{orders:[{{work_order_id:'a', status:'review'}}]}}]}};
            process.stdout.write(JSON.stringify(p.settled(now, base)));
            """)
        self.assertFalse(out)

    def test_not_settled_while_a_baseline_order_still_running(self):
        # S3+simplify 收口:落定只看**基线内**是否仍有 running——基线工单 running 在场
        # 未落定;租户里与本次无关的基线外长跑单(stranger)不绑架轮询,空基线直接落定。
        out = _run_node(f"""
            const p = require({_MOD});
            const watched = {{clients:[{{orders:[
                {{work_order_id:'a', status:'review'}},
                {{work_order_id:'b', status:'running'}},
            ]}}]}};
            const stranger = {{clients:[{{orders:[{{work_order_id:'c', status:'running'}}]}}]}};
            process.stdout.write(JSON.stringify([
                p.settled(watched, {{a: 't1', b: 't1'}}),
                p.settled(stranger, {{}}),
            ]));
            """)
        self.assertEqual(out, [False, True])

    def test_settled_when_all_watched_orders_reappear_not_running(self):
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
