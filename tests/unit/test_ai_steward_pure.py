#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_steward_pure.py

智能管家(B2-M1 · 前端)守门:
  1. ai-steward-render.js 纯函数——左窗五个 step state / 四个 task status 到 B1 色族的
     映射闭集、契约外的值一律落空白族(状态诚实,不冒充某个具体状态)、轮询终态判据、
     深链白名单(javascript:/外站/协议相对一律丢弃)、步数统计与 agent 数兜底。
  2. ai-steward-chat-render.js 纯函数——角色→气泡类、本地送出态收敛、可送出判据
     (空串/上一句还在路上都不许再送)、快捷问法 chips 闭集。
  3. ai-i18n-steward.js 分片 zh/th key 集合一致 + 页面/渲染层引用的每个 stw_*(含
     nav_steward)都真实存在于 zh 词典——A 表引用 B 表的 id 必须配闸(防「深链 35 条
     全落空却报绿」的老坑)。
  4. ai-router.js 的 #/steward 往返解析(新路由不破既有路由)。
"""

from __future__ import annotations

import json
import re
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_RENDER = json.dumps(str(AI_DIR / "ai-steward-render.js"))
_CHAT = json.dumps(str(AI_DIR / "ai-steward-chat-render.js"))
_ROUTER = json.dumps(str(AI_DIR / "ai-router.js"))
_I18N = json.dumps(str(AI_DIR / "ai-i18n-steward.js"))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class TaskRenderPureTests(unittest.TestCase):
    def test_state_families_match_the_agreed_mapping(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify({{
                steps: r.STEP_STATES.map((s) => [s, r.stepFamily(s)]),
                tasks: r.TASK_STATUSES.map((s) => [s, r.taskFamily(s)]),
                unknownStep: r.stepFamily('nope'),
                unknownTask: r.taskFamily('nope'),
            }}));
            """)
        # 契约:done→成功绿 / running→执行蓝 / queued→中性灰 / waiting_auth→警告橙 / failed→错误红
        self.assertEqual(
            out["steps"],
            [
                ["done", "ok"],
                ["running", "run"],
                ["queued", "off"],
                ["waiting_auth", "warn"],
                ["failed", "err"],
            ],
        )
        self.assertEqual(
            out["tasks"],
            [["running", "run"], ["done", "ok"], ["failed", "err"], ["waiting_user", "wait"]],
        )
        # 契约外的值不冒充任何具体状态。
        self.assertEqual(out["unknownStep"], "empty")
        self.assertEqual(out["unknownTask"], "empty")

    def test_state_label_keys_fall_back_to_unknown(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.stepStateKey('waiting_auth'), r.stepStateKey('bogus'),
                r.taskStatusKey('waiting_user'), r.taskStatusKey('bogus'),
            ]));
            """)
        self.assertEqual(
            out,
            [
                "stw_step_waiting_auth",
                "stw_step_unknown",
                "stw_status_waiting_user",
                "stw_status_unknown",
            ],
        )

    def test_only_done_failed_waiting_user_stop_polling(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.isTerminalStatus('done'), r.isTerminalStatus('failed'),
                r.isTerminalStatus('waiting_user'), r.isTerminalStatus('running'),
                r.isTerminalStatus(undefined), r.isTerminalStatus('bogus'),
            ]));
            """)
        # 未知值当"还在跑"继续轮询——停轮询会让真在跑的任务永远停在半路。
        self.assertEqual(out, [True, True, True, False, False, False])

    def test_deeplink_whitelist_drops_dangerous_and_offsite_hrefs(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.safeHref('#/client/c1/wo?period=2569-06'),
                r.safeHref('/api/ai/steward/tasks/t1/export.xlsx'),
                r.safeHref('javascript:alert(1)'),
                r.safeHref('https://evil.example/x'),
                r.safeHref('//evil.example/x'),
                r.safeHref(''),
                r.safeHref(null),
            ]));
            """)
        self.assertEqual(
            out,
            [
                "#/client/c1/wo?period=2569-06",
                "/api/ai/steward/tasks/t1/export.xlsx",
                None,
                None,
                None,
                None,
                None,
            ],
        )

    def test_safe_links_filters_and_backfills_label(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify(r.safeLinks([
                {{ label: '看工单', href: '#/client/c1/wo' }},
                {{ href: '#/' }},
                {{ label: '外站', href: 'https://x.example' }},
                null,
            ])));
            """)
        self.assertEqual(
            out,
            [{"label": "看工单", "href": "#/client/c1/wo"}, {"label": "#/", "href": "#/"}],
        )

    def test_step_counts_and_agent_count_floor(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.stepCounts([{{state:'done'}},{{state:'running'}},{{state:'done'}}]),
                r.stepCounts([]), r.stepCounts(undefined),
                r.agentCount({{agent_count: 3}}), r.agentCount({{agent_count: 0}}),
                r.agentCount({{}}), r.agentCount(null),
            ]));
            """)
        self.assertEqual(out[0], {"done": 2, "total": 3})
        self.assertEqual(out[1], {"done": 0, "total": 0})
        self.assertEqual(out[2], {"done": 0, "total": 0})
        # 缺失/非法一律兜到 1:不显示"0 个 Agent"这种自证没在干活的假状态。
        self.assertEqual(out[3:], [3, 1, 1, 1])

    def test_started_label_is_empty_when_unparseable(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.startedLabel('2026-07-26T09:05:00'),
                r.startedLabel('not-a-date'), r.startedLabel(null),
            ]));
            """)
        self.assertEqual(out[0], "09:05")
        self.assertEqual(out[1:], ["", ""])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ChatRenderPureTests(unittest.TestCase):
    def test_role_class_only_user_is_me(self):
        out = _run_node(f"""
            const c = require({_CHAT});
            process.stdout.write(JSON.stringify([
                c.roleClass('user'), c.roleClass('steward'), c.roleClass('bogus'),
            ]));
            """)
        self.assertEqual(out, ["me", "agent", "agent"])

    def test_send_state_collapses_unknown_to_sent(self):
        out = _run_node(f"""
            const c = require({_CHAT});
            process.stdout.write(JSON.stringify([
                c.SEND_STATES, c.sendState('sending'), c.sendState('failed'),
                c.sendState('bogus'), c.sendState(undefined),
            ]));
            """)
        self.assertEqual(out[0], ["sent", "sending", "failed"])
        self.assertEqual(out[1:], ["sending", "failed", "sent", "sent"])

    def test_can_send_rejects_blank_and_in_flight(self):
        out = _run_node(f"""
            const c = require({_CHAT});
            process.stdout.write(JSON.stringify([
                c.canSend('本期谁缺料', false), c.canSend('   ', false),
                c.canSend('', false), c.canSend(null, false),
                c.canSend('本期谁缺料', true),
            ]));
            """)
        self.assertEqual(out, [True, False, False, False, False])

    def test_quick_keys_are_the_four_agreed_chips(self):
        out = _run_node(f"""
            const c = require({_CHAT});
            process.stdout.write(JSON.stringify(c.QUICK_KEYS));
            """)
        self.assertEqual(
            out,
            [
                "stw_quick_missing",
                "stw_quick_review",
                "stw_quick_pushfail",
                "stw_quick_progress",
            ],
        )


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class StewardRouteTests(unittest.TestCase):
    def test_steward_hash_round_trips_and_leaves_others_intact(self):
        out = _run_node(f"""
            const r = require({_ROUTER});
            process.stdout.write(JSON.stringify([
                r.parseHash('#' + r.buildStewardHash().slice(1)),
                r.buildStewardHash(),
                r.parseHash('#/desk'),
                r.parseHash('#/'),
                r.parseHash('#/client/c1/wo?period=2569-06'),
            ]));
            """)
        self.assertEqual(out[0], {"name": "steward"})
        self.assertEqual(out[1], "#/steward")
        self.assertEqual(out[2], {"name": "desk"})
        self.assertEqual(out[3], {"name": "dashboard", "sub": "matrix"})
        self.assertEqual(out[4]["name"], "client")
        self.assertEqual(out[4]["period"], "2569-06")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class StewardI18nShardTests(unittest.TestCase):
    """zh/th key 一致 + 被引用 key 必须真实存在(词典分片不在主四语一致性测试的装载清单
    里,自己的闸自己带 · 同 ai-i18n-states.js 先例)。"""

    def _shard_keys(self):
        return _run_node(f"""
            global.window = global;
            global.__AI_I18N_ZH__ = {{}};
            global.__AI_I18N_TH__ = {{}};
            require({_I18N});
            process.stdout.write(JSON.stringify({{
                zh: Object.keys(global.__AI_I18N_ZH__).sort(),
                th: Object.keys(global.__AI_I18N_TH__).sort(),
            }}));
            """)

    def test_zh_and_th_key_sets_identical(self):
        keys = self._shard_keys()
        self.assertTrue(keys["zh"], "分片 zh 词条为空")
        self.assertEqual(keys["zh"], keys["th"], "th 词典 key 集合与 zh 不一致")

    def test_every_referenced_key_exists_in_dictionary(self):
        zh = set(self._shard_keys()["zh"])
        sources = (
            "ai-steward-render.js",
            "ai-steward-chat-render.js",
            "ai-steward.js",
            "ai-steward-bar.js",
            "ai.html",
        )
        referenced = {"nav_steward"}
        for name in sources:
            text = (AI_DIR / name).read_text(encoding="utf-8")
            # 尾下划线的是动态拼 key 的前缀字面量('stw_step_' + state),不是完整 key。
            referenced |= {k for k in re.findall(r"\bstw_[a-z0-9_]+", text) if not k.endswith("_")}
        # 动态拼 key 的两处(stw_step_ + 步骤态 / stw_status_ + 任务态)静态正则抓不全,补闭集。
        referenced |= {
            f"stw_step_{s}"
            for s in ("done", "running", "queued", "waiting_auth", "failed", "unknown")
        }
        referenced |= {
            f"stw_status_{s}" for s in ("running", "done", "failed", "waiting_user", "unknown")
        }
        missing = sorted(referenced - zh)
        self.assertEqual(missing, [], f"引用了词典里不存在的 key: {missing}")

    def test_quick_chip_keys_are_all_translated(self):
        """chips 闭集来自 ai-steward-chat-render.js,四条都必须在 zh/th 里有真文案。"""
        keys = self._shard_keys()
        quick = _run_node(f"""
            const c = require({_CHAT});
            process.stdout.write(JSON.stringify(c.QUICK_KEYS));
            """)
        for k in quick:
            self.assertIn(k, keys["zh"])
            self.assertIn(k, keys["th"])
