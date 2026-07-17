#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_poll_pure.py

Pearnly AI(J-B)共享轮询器守门:ai-poll.js 的 create()——终态即停 / 超时兜底 /
页面隐藏时暂停。真 node 子进程跑源文件(用真 setTimeout,不 mock 计时器),
断言脚本自带异步等待,stdout 只在轮询链路收尾后才写,同 _node_harness 的
同步 subprocess 读取手法天然兼容(node 进程有 pending 定时器就不会提前退出)。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class RunPollTests(unittest.TestCase):
    def test_ticks_until_terminal_then_stops(self):
        out = _run_node(f"""
            const poll = require({json.dumps(str(AI_DIR / "ai-poll.js"))});
            let n = 0;
            const seen = [];
            const h = poll.create({{
                intervalMs: 5,
                fetch: () => Promise.resolve(++n),
                onTick: (v) => seen.push(v),
                isTerminal: (v) => v >= 3,
                onTerminal: (v) => {{
                    process.stdout.write(JSON.stringify({{ seen, terminalValue: v }}));
                }},
            }});
            h.start();
            """)
        self.assertEqual(out, {"seen": [1, 2, 3], "terminalValue": 3})

    def test_max_tries_exceeded_calls_timeout_not_terminal(self):
        out = _run_node(f"""
            const poll = require({json.dumps(str(AI_DIR / "ai-poll.js"))});
            let ticks = 0;
            let terminalCalled = false;
            const h = poll.create({{
                intervalMs: 5,
                maxTries: 2,
                fetch: () => Promise.resolve({{}}),
                onTick: () => {{ ticks += 1; }},
                isTerminal: () => false,
                onTerminal: () => {{ terminalCalled = true; }},
                onTimeout: () => {{
                    process.stdout.write(JSON.stringify({{ ticks, terminalCalled }}));
                }},
            }});
            h.start();
            """)
        self.assertEqual(out, {"ticks": 2, "terminalCalled": False})

    def test_fetch_rejection_does_not_stop_polling(self):
        out = _run_node(f"""
            const poll = require({json.dumps(str(AI_DIR / "ai-poll.js"))});
            let attempt = 0;
            let errCount = 0;
            const h = poll.create({{
                intervalMs: 5,
                fetch: () => {{
                    attempt += 1;
                    return attempt === 1 ? Promise.reject(new Error('boom')) : Promise.resolve('ok');
                }},
                isTerminal: (v) => v === 'ok',
                onError: () => {{ errCount += 1; }},
                onTerminal: () => {{
                    process.stdout.write(JSON.stringify({{ attempt, errCount }}));
                }},
            }});
            h.start();
            """)
        self.assertEqual(out, {"attempt": 2, "errCount": 1})

    def test_stop_prevents_further_ticks(self):
        out = _run_node(f"""
            const poll = require({json.dumps(str(AI_DIR / "ai-poll.js"))});
            let ticks = 0;
            const h = poll.create({{
                intervalMs: 5,
                fetch: () => Promise.resolve({{}}),
                onTick: () => {{ ticks += 1; }},
                isTerminal: () => false,
            }});
            h.start();
            setTimeout(() => {{
                h.stop();
                const afterStop = ticks;
                setTimeout(() => {{
                    process.stdout.write(JSON.stringify({{ afterStop, unchanged: ticks === afterStop }}));
                }}, 30);
            }}, 8);
            """)
        self.assertTrue(out["unchanged"])
        self.assertGreaterEqual(out["afterStop"], 1)

    def test_paused_while_hidden_resumes_when_visible(self):
        out = _run_node(f"""
            const handlers = [];
            global.document = {{
                hidden: false,
                addEventListener: (t, f) => handlers.push(f),
                removeEventListener: (t, f) => {{
                    const i = handlers.indexOf(f);
                    if (i >= 0) handlers.splice(i, 1);
                }},
                fire: () => handlers.forEach((f) => f()),
            }};
            const poll = require({json.dumps(str(AI_DIR / "ai-poll.js"))});
            let ticks = 0;
            const h = poll.create({{
                intervalMs: 15,
                fetch: () => Promise.resolve({{}}),
                onTick: () => {{ ticks += 1; }},
                isTerminal: () => false,
            }});
            h.start();
            global.document.hidden = true;
            global.document.fire(); // 立即隐藏:排定的第一次 tick 被清掉
            setTimeout(() => {{
                const pausedCount = ticks; // 隐藏期间(> intervalMs)应仍为 0
                global.document.hidden = false;
                global.document.fire(); // 恢复可见:续排
                setTimeout(() => {{
                    h.stop();
                    process.stdout.write(JSON.stringify({{ pausedCount, resumedCount: ticks }}));
                }}, 30);
            }}, 25);
            """)
        self.assertEqual(out["pausedCount"], 0)
        self.assertGreaterEqual(out["resumedCount"], 1)


if __name__ == "__main__":
    unittest.main()
