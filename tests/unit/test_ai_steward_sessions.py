# -*- coding: utf-8 -*-
"""会话侧栏动作层 + 侧栏纯函数(ai-steward-sessions.js / ai-steward-sessions-render.js)。

动作层用假钩子 + 假 api 跑真代码断状态迁移(同 test_ai_steward_actions 先例):
①列表刷新失败但已有旧列表时不翻错脸;②改名没改/清空 = 撤销不打请求、失败保编辑态;
③删除当前会话落到最近的另一个、一个不剩开新对话;④余额拿不到 = 整行不显示不编数。
纯函数:标题省略、活动草稿项补位。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_SESSIONS = json.dumps(str(AI_DIR / "ai-steward-sessions.js"))
_RENDER = json.dumps(str(AI_DIR / "ai-steward-sessions-render.js"))

_SETUP = f"""
    const mod = require({_SESSIONS});
    const flush = () => new Promise((r) => setImmediate(r));
    function harness(api, seed) {{
        const calls = [];
        const S = Object.assign({{
            sessions: [], sessionsLoading: false, sessionsErr: false,
            renamingId: null, deletingId: null, sessBusy: false,
            budget: null, sessionId: 's1', api: api,
        }}, seed || {{}});
        const inputs = {{}};
        const hooks = {{
            state: () => S,
            getEl: (id) => inputs[id] || null,
            renderSide: () => calls.push('renderSide'),
            switchSession: (sid) => calls.push('switch:' + sid),
            newSession: () => calls.push('new'),
        }};
        return {{ act: mod.create(hooks), S: S, calls: calls, inputs: inputs }};
    }}
"""


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端动作层测试")
class SessionsActionsTests(unittest.TestCase):
    def test_reload_failure_keeps_existing_list_quietly(self):
        out = _run_node(f"""
            {_SETUP}
            (async () => {{
                const h = harness({{ listStewardSessions: () => Promise.reject(new Error('x')) }},
                    {{ sessions: [{{ session_id: 's1', title: '旧的' }}] }});
                h.act.load();
                await flush(); await flush();
                process.stdout.write(JSON.stringify({{
                    err: h.S.sessionsErr, kept: h.S.sessions.length,
                }}));
            }})();
            """)
        self.assertFalse(out["err"])
        self.assertEqual(out["kept"], 1)

    def test_rename_unchanged_or_blank_cancels_without_request(self):
        out = _run_node(f"""
            {_SETUP}
            (async () => {{
                let hits = 0;
                const h = harness({{ renameStewardSession: () => {{ hits += 1; return Promise.resolve({{}}); }} }},
                    {{ sessions: [{{ session_id: 's1', title: '对账' }}], renamingId: 's1' }});
                h.inputs.stwSessRename = {{ value: '  对账  ' }};
                h.act.onKeydown({{ target: {{ id: 'stwSessRename' }}, key: 'Enter',
                                   preventDefault: () => {{}} }});
                await flush();
                process.stdout.write(JSON.stringify({{ hits, renaming: h.S.renamingId }}));
            }})();
            """)
        self.assertEqual(out["hits"], 0)
        self.assertIsNone(out["renaming"])

    def test_rename_failure_keeps_editing_state(self):
        out = _run_node(f"""
            {_SETUP}
            (async () => {{
                const h = harness({{ renameStewardSession: () => Promise.reject(new Error('x')) }},
                    {{ sessions: [{{ session_id: 's1', title: '对账' }}], renamingId: 's1' }});
                h.inputs.stwSessRename = {{ value: '新名字' }};
                h.act.onKeydown({{ target: {{ id: 'stwSessRename' }}, key: 'Enter',
                                   preventDefault: () => {{}} }});
                await flush(); await flush();
                process.stdout.write(JSON.stringify({{
                    renaming: h.S.renamingId, busy: h.S.sessBusy,
                }}));
            }})();
            """)
        # 失败保持编辑态:填的字还在,不逼人重打一遍。
        self.assertEqual(out["renaming"], "s1")
        self.assertFalse(out["busy"])

    def test_delete_active_session_lands_on_next_or_new(self):
        out = _run_node(f"""
            {_SETUP}
            (async () => {{
                const api = {{ deleteStewardSession: () => Promise.resolve({{ ok: true }}) }};
                const a = harness(api, {{ sessions: [
                    {{ session_id: 's1', title: '甲' }}, {{ session_id: 's2', title: '乙' }},
                ] }});
                a.act.onClick('stw-sess-del-yes', {{ getAttribute: () => 's1' }});
                await flush(); await flush();
                const b = harness(api, {{ sessions: [{{ session_id: 's1', title: '甲' }}] }});
                b.act.onClick('stw-sess-del-yes', {{ getAttribute: () => 's1' }});
                await flush(); await flush();
                process.stdout.write(JSON.stringify({{ a: a.calls, b: b.calls }}));
            }})();
            """)
        self.assertIn("switch:s2", out["a"])
        self.assertIn("new", out["b"])

    def test_budget_unavailable_clears_the_line(self):
        out = _run_node(f"""
            {_SETUP}
            (async () => {{
                const h = harness({{ getStewardBudget: () => Promise.resolve({{ available: false }}) }},
                    {{ budget: {{ session: {{ spent_thb: '1' }} }} }});
                h.act.refreshBudget();
                await flush(); await flush();
                process.stdout.write(JSON.stringify({{ budget: h.S.budget }}));
            }})();
            """)
        self.assertIsNone(out["budget"])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class SessionsRenderPureTests(unittest.TestCase):
    def test_display_title_trims_and_ellipsizes(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.displayTitle('  6 月  对账  '),
                r.displayTitle(''),
                r.displayTitle('长'.repeat(60)).length,
            ]));
            """)
        self.assertEqual(out[0], "6 月 对账")
        self.assertEqual(out[1], "")
        self.assertLessEqual(out[2], 40)

    def test_active_session_not_in_list_gets_a_draft_entry(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            const listed = [{{ session_id: 's1', title: '甲' }}];
            process.stdout.write(JSON.stringify([
                r.listEntries(listed, 's-new'),
                r.listEntries(listed, 's1'),
            ]));
            """)
        self.assertTrue(out[0][0]["draft"])
        self.assertEqual(out[0][0]["session_id"], "s-new")
        self.assertEqual(len(out[1]), 1)


if __name__ == "__main__":
    unittest.main()
