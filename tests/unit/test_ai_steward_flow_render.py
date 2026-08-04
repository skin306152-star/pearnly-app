# -*- coding: utf-8 -*-
"""对话流拼装的纯函数(static/ai/ai-steward-flow-render.js)。

锁:①轮分组 —— 连续 steward 消息聚一轮、taskIds 按首现去重(过程条一条任务只画一次);
②折叠默认值 —— done/cancelled 折起、failed/running/waiting 展开;③摘要选型 ——
running 优先用正在跑那一步的 label,不编;各终态给对应词条 key。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_FLOW = json.dumps(str(AI_DIR / "ai-steward-flow-render.js"))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class GroupTurnsTests(unittest.TestCase):
    def _group(self, messages):
        return _run_node(f"""
            const f = require({_FLOW});
            process.stdout.write(JSON.stringify(f.groupTurns({json.dumps(messages)})));
            """)

    def test_consecutive_steward_messages_merge_into_one_turn(self):
        turns = self._group([
            {"role": "user", "text": "两张票入账"},
            {"role": "steward", "text": "已受理", "task_id": "t1"},
            {"role": "steward", "text": "已完成", "task_id": "t1"},
            {"role": "user", "text": "第二张是什么"},
            {"role": "steward", "text": "是 Makro", "task_id": "t2"},
        ])  # fmt: skip
        self.assertEqual([t["kind"] for t in turns], ["user", "steward", "user", "steward"])
        self.assertEqual(len(turns[1]["msgs"]), 2)
        # 同一条任务两条消息只登记一次 —— 过程条只画一条。
        self.assertEqual(turns[1]["taskIds"], ["t1"])
        self.assertEqual(turns[3]["taskIds"], ["t2"])

    def test_leading_steward_message_forms_its_own_turn(self):
        turns = self._group([{"role": "steward", "text": "欢迎回来"}])
        self.assertEqual(turns[0]["kind"], "steward")
        self.assertEqual(turns[0]["taskIds"], [])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ProcDefaultsTests(unittest.TestCase):
    def test_collapse_defaults_follow_status(self):
        out = _run_node(f"""
            const f = require({_FLOW});
            process.stdout.write(JSON.stringify(
                ['done', 'cancelled', 'failed', 'running', 'waiting_user'].map(f.defaultCollapsed)));
            """)
        # 跑完/人停的折起;failed 展开(哪一步断的是排障第一问);live 的展开。
        self.assertEqual(out, [True, True, False, False, False])

    def test_summary_prefers_running_step_label(self):
        out = _run_node(f"""
            const f = require({_FLOW});
            const task = {{ status: 'running', steps: [
                {{ label: '读取票据', state: 'done' }},
                {{ label: 'OCR 识别', state: 'running' }},
            ] }};
            process.stdout.write(JSON.stringify([
                f.summarySpec(task),
                f.summarySpec({{ status: 'running', steps: [] }}),
                f.summarySpec({{ status: 'done', steps: [{{ state: 'done' }}] }}),
                f.summarySpec({{ status: 'failed', steps: [] }}),
                f.summarySpec({{ status: 'cancelled', steps: [{{ state: 'done' }}] }}),
                f.summarySpec({{ status: 'waiting_user', steps: [] }}),
            ]));
            """)
        self.assertEqual(out[0], {"key": None, "text": "OCR 识别"})
        self.assertEqual(out[1]["key"], "stw_proc_running_sum")
        self.assertEqual(out[2], {"key": "stw_proc_done_sum", "vars": {"n": 1}})
        self.assertEqual(out[3]["key"], "stw_proc_failed_sum")
        self.assertEqual(out[4], {"key": "stw_proc_cancelled_sum", "vars": {"n": 1}})
        self.assertEqual(out[5]["key"], "stw_proc_waiting_sum")


if __name__ == "__main__":
    unittest.main()
