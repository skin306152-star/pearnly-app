#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_steward_actions.py

智能管家(B3 · 前端)动作层守门:ai-steward-actions.js 是钩子注入的工厂,node 用假钩子 +
假 api 直接跑真代码,断言状态迁移(不是断言"函数存在"):
  1. 决断成功 → busy 收回 + 以响应的 task_id 整载重拉(批准复跑/拒绝收口都以重拉为准)。
  2. 决断被拒 → 错误码翻成对应词条落 actionErr + 轻刷拿服务端现状(终态不重启轮询)。
  3. busy 期间连点不重复打端点(后端 token 单次单用是硬闸,前端别让人白点)。
  4. 取消成功 → 幂等端点回的任务直接落地 + 停轮询;取消失败 → 人话错误行。
  5. 会话换代(state() 不再是发起时那份)→ 晚到的响应整段丢弃,不写进新会话。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_ACTIONS = json.dumps(str(AI_DIR / "ai-steward-actions.js"))
_AUTHZ = json.dumps(str(AI_DIR / "ai-steward-authz-render.js"))

# 共享搭台:真 authz-render 供错误码翻词条,at() 回吐 key 让断言认得出用的哪条词。
_SETUP = f"""
    const actionsMod = require({_ACTIONS});
    global.AI = {{ stewardAuthzRender: require({_AUTHZ}) }};
    global.at = (k) => k;
    const flush = () => new Promise((r) => setImmediate(r));
    function harness(api) {{
        const calls = [];
        const S = {{
            taskId: 't1', authzBusy: false, cancelBusy: false, actionErr: null,
            cdTimer: null, poller: null, api: api,
        }};
        const box = {{ S: S }};
        const hooks = {{
            state: () => box.S,
            getEl: () => null,
            renderLeft: () => calls.push('renderLeft'),
            loadTask: (id) => calls.push('loadTask:' + id),
            startWatch: (id) => calls.push('startWatch:' + id),
            stopPoll: () => calls.push('stopPoll'),
            isTerminal: (st) =>
                ['done', 'failed', 'waiting_user', 'cancelled'].indexOf(st) >= 0,
        }};
        return {{ act: actionsMod.create(hooks), S: S, box: box, calls: calls }};
    }}
"""


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端动作层测试")
class StewardActionsTests(unittest.TestCase):
    def test_decide_success_reloads_task_from_response(self):
        out = _run_node(f"""
            {_SETUP}
            (async () => {{
                let hits = 0;
                const h = harness({{
                    decideStewardAuthz: () => {{ hits += 1; return Promise.resolve({{ task_id: 't9' }}); }},
                }});
                h.act.decide(true, 'tok-12345678');
                const busyDuring = h.S.authzBusy;
                await flush(); await flush();
                process.stdout.write(JSON.stringify({{
                    hits, busyDuring, busyAfter: h.S.authzBusy,
                    err: h.S.actionErr, calls: h.calls,
                }}));
            }})();
            """)
        self.assertEqual(out["hits"], 1)
        self.assertTrue(out["busyDuring"])
        self.assertFalse(out["busyAfter"])
        self.assertIsNone(out["err"])
        self.assertIn("loadTask:t9", out["calls"])

    def test_decide_used_token_maps_copy_and_soft_refreshes_without_restarting_poll(self):
        out = _run_node(f"""
            {_SETUP}
            (async () => {{
                const h = harness({{
                    decideStewardAuthz: () => Promise.reject({{ code: 'steward.authz_used' }}),
                    getStewardTask: (id) =>
                        Promise.resolve({{ task_id: id, status: 'waiting_user' }}),
                }});
                h.act.decide(true, 'tok-12345678');
                await flush(); await flush(); await flush();
                process.stdout.write(JSON.stringify({{
                    err: h.S.actionErr, task: h.S.task, calls: h.calls,
                }}));
            }})();
            """)
        self.assertEqual(out["err"], "stw_authz_err_used")
        # 轻刷把服务端现状拉了回来;waiting_user 是收口态,不许重启轮询。
        self.assertEqual(out["task"]["status"], "waiting_user")
        self.assertNotIn("startWatch:t1", out["calls"])
        self.assertNotIn("loadTask:t1", out["calls"])

    def test_decide_ignores_second_click_while_busy(self):
        out = _run_node(f"""
            {_SETUP}
            (async () => {{
                let hits = 0;
                const h = harness({{
                    decideStewardAuthz: () => {{
                        hits += 1;
                        return new Promise(() => {{}}); // 永不落地,压住 busy
                    }},
                }});
                h.act.decide(true, 'tok-12345678');
                h.act.decide(true, 'tok-12345678');
                h.act.decide(false, 'tok-12345678');
                await flush();
                process.stdout.write(JSON.stringify({{ hits }}));
            }})();
            """)
        self.assertEqual(out["hits"], 1)

    def test_cancel_lands_response_task_and_stops_poll_or_reports_failure(self):
        out = _run_node(f"""
            {_SETUP}
            (async () => {{
                const ok = harness({{
                    cancelStewardTask: (id) =>
                        Promise.resolve({{ task_id: id, status: 'cancelled' }}),
                }});
                ok.act.cancel();
                await flush(); await flush();
                const bad = harness({{
                    cancelStewardTask: () => Promise.reject({{ status: 500 }}),
                }});
                bad.act.cancel();
                await flush(); await flush();
                process.stdout.write(JSON.stringify({{
                    okStatus: ok.S.task.status, okCalls: ok.calls, okErr: ok.S.actionErr,
                    badErr: bad.S.actionErr, badBusy: bad.S.cancelBusy,
                }}));
            }})();
            """)
        self.assertEqual(out["okStatus"], "cancelled")
        self.assertIn("stopPoll", out["okCalls"])
        self.assertIsNone(out["okErr"])
        self.assertEqual(out["badErr"], "stw_cancel_failed")
        self.assertFalse(out["badBusy"])

    def test_late_response_after_session_swap_is_dropped(self):
        out = _run_node(f"""
            {_SETUP}
            (async () => {{
                let release;
                const h = harness({{
                    decideStewardAuthz: () =>
                        new Promise((resolve) => {{ release = resolve; }}),
                }});
                h.act.decide(true, 'tok-12345678');
                // 会话换代(开新会话):旧响应晚到必须整段丢弃。
                h.box.S = {{ taskId: null, authzBusy: false, actionErr: null, api: {{}} }};
                release({{ task_id: 't9' }});
                await flush(); await flush();
                process.stdout.write(JSON.stringify({{
                    calls: h.calls, newErr: h.box.S.actionErr,
                }}));
            }})();
            """)
        self.assertNotIn("loadTask:t9", out["calls"])
        self.assertIsNone(out["newErr"])


if __name__ == "__main__":
    unittest.main()
