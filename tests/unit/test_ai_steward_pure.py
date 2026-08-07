#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_steward_pure.py

智能管家(B2-M1 · 前端)守门:
  1. ai-steward-render.js 纯函数——左窗五个 step state / 四个 task status 到 B1 色族的
     映射闭集、契约外的值一律落空白族(状态诚实,不冒充某个具体状态)、轮询终态判据、
     深链白名单(javascript:/外站/协议相对一律丢弃)、步数统计与 agent 数兜底。
  2. ai-steward-chat-render.js 纯函数——角色→气泡类、本地送出态收敛、可送出判据
     (空串/上一句还在路上都不许再送)。
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
_ATTACH_RENDER = json.dumps(str(AI_DIR / "ai-steward-attach-render.js"))
_I18N = json.dumps(str(AI_DIR / "ai-i18n-steward.js"))
_I18N_CHAT = json.dumps(str(AI_DIR / "ai-i18n-steward-chat.js"))


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
            [
                ["running", "run"],
                ["done", "ok"],
                ["failed", "err"],
                ["waiting_user", "wait"],
                ["cancelled", "off"],
            ],
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

    def test_only_terminal_and_waiting_user_stop_polling(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.isTerminalStatus('done'), r.isTerminalStatus('failed'),
                r.isTerminalStatus('waiting_user'), r.isTerminalStatus('cancelled'),
                r.isTerminalStatus('running'),
                r.isTerminalStatus(undefined), r.isTerminalStatus('bogus'),
            ]));
            """)
        # 未知值当"还在跑"继续轮询——停轮询会让真在跑的任务永远停在半路。
        self.assertEqual(out, [True, True, True, True, False, False, False])

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

    def test_agent_count_floor(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.agentCount({{agent_count: 3}}), r.agentCount({{agent_count: 0}}),
                r.agentCount({{}}), r.agentCount(null),
            ]));
            """)
        # 缺失/非法一律兜到 1:不显示"0 个 Agent"这种自证没在干活的假状态。
        self.assertEqual(out, [3, 1, 1, 1])

    def test_loop_question_normalises_options_and_drops_empty_ones(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.loopQuestion({{ loop: {{ question: {{ field: 'period',
                    text: ' 哪一期? ', options: [' 上个月 ', '', '本月', '上个月', null] }} }} }}),
                r.loopQuestion({{ loop: {{ question: {{ text: '  ', options: ['x'] }} }} }}),
                r.loopQuestion({{ loop: {{ calls: 2 }} }}),
                r.loopQuestion({{}}),
                r.loopQuestion(null),
            ]));
            """)
        # 去空、去重、去首尾空格,顺序照后端给的来(候选是它按数据算的,前端不重排)。
        self.assertEqual(
            out[0], {"field": "period", "text": "哪一期?", "options": ["上个月", "本月"]}
        )
        # 问题为空 = 没有追问:整块不渲染,不摆一排点了没意义的按钮。
        self.assertEqual(out[1:], [None, None, None, None])

    def test_the_failure_sentence_is_printed_once_per_screen(self):
        """后端把同一句失败原因写进红条 / 失败步 detail / 回复气泡三处(一字不差)。

        气泡里已经有了 → 左窗红条让位;气泡里没有(深链直接开左窗、消息还没回来)→ 红条
        照印,不能让失败的任务只剩一个「失败」徽章、说不出为什么。
        """
        out = _run_node(f"""
            const r = require({_RENDER});
            const reason = '小助手离线,69EXP 没有写入。小助手上线后再说一次。';
            const task = {{ task_id: 't1', error_reason: reason }};
            const bubble = {{ role: 'steward', task_id: 't1', text: reason }};
            process.stdout.write(JSON.stringify([
                r.reasonIsEchoed(task, [bubble]),
                r.reasonIsEchoed(task, [{{ role: 'steward', task_id: 't1', text: ' ' + reason + ' ' }}]),
                r.reasonIsEchoed(task, []),
                r.reasonIsEchoed(task, [{{ role: 'user', task_id: 't1', text: reason }}]),
                r.reasonIsEchoed(task, [{{ role: 'steward', task_id: 't2', text: reason }}]),
                r.reasonIsEchoed(task, [{{ role: 'steward', task_id: 't1', text: '推好了' }}]),
                r.reasonIsEchoed({{ task_id: 't1' }}, [bubble]),
            ]));
            """)
        # 用户自己打的字、别条任务的气泡、内容不同的回复都不算「已经印过」。
        self.assertEqual(out, [True, True, False, False, False, False, False])

    def test_loop_question_caps_the_number_of_options(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            const many = Array.from({{ length: 20 }}, (_, i) => 'o' + i);
            const q = r.loopQuestion({{ loop: {{ question: {{ text: '选一个', options: many }} }} }});
            process.stdout.write(JSON.stringify([r.MAX_OPTIONS, q.options.length]));
            """)
        self.assertEqual(out[1], out[0])

    def test_options_are_clickable_only_while_the_task_still_waits(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.optionsEnabled({{ status: 'waiting_user' }}, false),
                r.optionsEnabled({{ status: 'waiting_user' }}, true),
                r.optionsEnabled({{ status: 'running' }}, false),
                r.optionsEnabled({{ status: 'done' }}, false),
                r.optionsEnabled({{ status: 'cancelled' }}, false),
            ]));
            """)
        # 终态后后端那一轮不认;busy 是本地送出在途,连点会送出两句。
        self.assertEqual(out, [True, False, False, False, False])

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
        # 两个分片一起装:旧词条(zh/th)在 ai-i18n-steward.js,S1 会话流新词条(四语)
        # 在 ai-i18n-steward-chat.js —— 引用检查看的是合并后的 zh 集合。
        return _run_node(f"""
            global.window = global;
            global.__AI_I18N_ZH__ = {{}};
            global.__AI_I18N_TH__ = {{}};
            global.__AI_I18N_EN__ = {{}};
            global.__AI_I18N_JA__ = {{}};
            require({_I18N});
            require({_I18N_CHAT});
            process.stdout.write(JSON.stringify({{
                zh: Object.keys(global.__AI_I18N_ZH__).sort(),
                th: Object.keys(global.__AI_I18N_TH__).sort(),
            }}));
            """)

    def test_zh_and_th_key_sets_identical(self):
        keys = self._shard_keys()
        self.assertTrue(keys["zh"], "分片 zh 词条为空")
        self.assertEqual(keys["zh"], keys["th"], "th 词典 key 集合与 zh 不一致")

    def test_chat_shard_ships_all_four_languages(self):
        """S1 新词条按拍板一步到位四语:chat 分片单独装,四份 key 集合必须逐一相同。"""
        keys = _run_node(f"""
            global.window = global;
            global.__AI_I18N_ZH__ = {{}};
            global.__AI_I18N_TH__ = {{}};
            global.__AI_I18N_EN__ = {{}};
            global.__AI_I18N_JA__ = {{}};
            require({_I18N_CHAT});
            process.stdout.write(JSON.stringify({{
                zh: Object.keys(global.__AI_I18N_ZH__).sort(),
                th: Object.keys(global.__AI_I18N_TH__).sort(),
                en: Object.keys(global.__AI_I18N_EN__).sort(),
                ja: Object.keys(global.__AI_I18N_JA__).sort(),
            }}));
            """)
        self.assertTrue(keys["zh"], "chat 分片 zh 词条为空")
        self.assertEqual(keys["zh"], keys["th"], "th 与 zh key 集合不一致")
        self.assertEqual(keys["zh"], keys["en"], "en 与 zh key 集合不一致")
        self.assertEqual(keys["zh"], keys["ja"], "ja 与 zh key 集合不一致")

    def test_every_referenced_key_exists_in_dictionary(self):
        zh = set(self._shard_keys()["zh"])
        sources = (
            "ai-steward-render.js",
            "ai-steward-chat-render.js",
            "ai-steward-flow-render.js",
            "ai-steward-sessions-render.js",
            "ai-steward-sessions.js",
            "ai-steward-md.js",
            "ai-steward-stream.js",
            "ai-steward-view.js",
            "ai-steward-tasks.js",
            "ai-steward-gate.js",
            "ai-steward-authz-render.js",
            "ai-steward-actions.js",
            "ai-steward-attach-render.js",
            "ai-steward-attach.js",
            "ai-steward.js",
            "ai.html",
        )
        referenced = {"nav_steward"}
        for name in sources:
            text = (AI_DIR / name).read_text(encoding="utf-8")
            # 尾下划线的是动态拼 key 的前缀字面量('stw_step_' + state),不是完整 key。
            referenced |= {k for k in re.findall(r"\bstw_[a-z0-9_]+", text) if not k.endswith("_")}
        # 动态拼 key 的三处(stw_step_ + 步骤态 / stw_status_ + 任务态 / stw_authz_ + 卡态)
        # 静态正则抓不全,补闭集。
        referenced |= {
            f"stw_step_{s}"
            for s in ("done", "running", "queued", "waiting_auth", "failed", "unknown")
        }
        referenced |= {
            f"stw_status_{s}"
            for s in ("running", "done", "failed", "waiting_user", "cancelled", "unknown")
        }
        referenced |= {
            f"stw_authz_{s}" for s in ("pending", "approved", "rejected", "expired", "unknown")
        }
        # 万能口两处动态拼 key(料的闭集 kindKey / 选文件当下的拒收码 limitErrKey):
        # 【跑真函数取 key】,不手抄一份后缀清单 —— 首版就是手抄的,limitErrKey 实际吐的是
        # stw_att_err_attachment_too_large,清单里写的是 stw_att_err_too_large,闸全绿而
        # 产品里每条被拒的料都印一串原始 key。被验的标识符必须来自真实产物。
        referenced |= set(_run_node(f"""
            const a = require({_ATTACH_RENDER});
            process.stdout.write(JSON.stringify(
                a.KINDS.map(a.kindKey).concat(a.REJECT_CODES.map(a.limitErrKey))));
            """))
        missing = sorted(referenced - zh)
        self.assertEqual(missing, [], f"引用了词典里不存在的 key: {missing}")


def _unwired(emitted, dispatched) -> list:
    """画出来了却没人接的 data-action。闸与反证共用这一份判据。"""
    return sorted(set(emitted) - set(dispatched))


class StewardActionWiringTests(unittest.TestCase):
    """render 层吐的每个 data-action 都得在某个 onClick 链里有一支 —— 名字对不上就是一颗
    点了没反应的按钮,静态上完全看不出来(A 文件引用 B 文件的 id 必须配闸,老坑)。

    收编了此前只扫 ai-steward-render.js 的那道弱闸:它拿 `'名字' in 拼起来的源码` 当判据,
    动作名在注释里被提一句就算「有人接」。两道闸并存时弱的那道会先绿,掩掉强的那道。"""

    _EMITTERS = ("ai-steward-render.js", "ai-steward-authz-render.js", "ai-steward-chat-render.js",
                 "ai-steward-flow-render.js", "ai-steward-sessions-render.js", "ai-steward-md.js",
                 "ai-steward-attach-render.js")  # fmt: skip
    # 三处 onClick:主壳 / 附件盘自己认的六个 / 侧栏动作层。
    _DISPATCHERS = ("ai-steward.js", "ai-steward-attach.js", "ai-steward-sessions.js")  # fmt: skip

    def _scan(self, names, pattern):
        found = set()
        for name in names:
            found |= set(re.findall(pattern, (AI_DIR / name).read_text(encoding="utf-8")))
        return found

    def _sets(self):
        emitted = self._scan(self._EMITTERS, r'data-action="(stw-[a-z0-9-]+)"')
        dispatched = self._scan(self._DISPATCHERS, r"=== '(stw-[a-z0-9-]+)'")
        self.assertTrue(emitted, "一个 data-action 都没扫到 —— 正则或文件清单漂了")
        return emitted, dispatched

    def test_every_emitted_action_has_a_handler(self):
        emitted, dispatched = self._sets()
        self.assertEqual(_unwired(emitted, dispatched), [])

    def test_gate_flags_an_action_nobody_handles(self):
        """反证:塞一个没人接的动作名,闸必须点名它。"""
        emitted, dispatched = self._sets()
        self.assertEqual(_unwired(emitted | {"stw-ghost"}, dispatched), ["stw-ghost"])


class CopyMatchesCapabilityTests(unittest.TestCase):
    """页面自述必须与注册表真实能力一致(状态诚实):B3 曾把文案提前改成「要改数的会先出
    授权卡」,而闭集里一个写工具都没有 —— 用户照文案提改数请求只会吃 out_of_scope。
    此闸双向:全只读 ⇒ 不许承诺授权卡;第一个写工具挂上 ⇒ 不许再自称只读(逼文案随能力换)。"""

    # 承诺过「会改数的先批准」的那几处注脚。哪几处会随排版增删(composer 注脚已在
    # 2026-07-27 去重时撤掉 —— 同一条规则整页只说一遍),故按「存在就查」收,不写死清单;
    # 页头那条是唯一必须在的,它没了等于页面不再自述能力。
    _NOTE_KEYS = ("stw_note", "stw_composer_note", "stw_composer_note_files")

    def _notes(self):
        text = (AI_DIR / "ai-i18n-steward.js").read_text(encoding="utf-8")
        out = {}
        for key in self._NOTE_KEYS:
            values = re.findall(rf"{key}: '([^']*)'", text)
            if not values:
                continue
            self.assertEqual(len(values), 2, f"{key} 应 zh/th 各一条")
            out[key] = values
        self.assertIn("stw_note", out, "页头自述没了 —— 页面不再说明会改数的要先批准")
        return out

    def test_notes_promise_exactly_what_the_registry_can_do(self):
        from services.steward import registry

        has_write = any(not t.readonly for t in registry.TOOLS_BY_NAME.values())
        for key, (zh, th) in self._notes().items():
            if has_write:
                self.assertNotIn("只查不改数", zh, f"{key}: 有写工具了还自称只读")
                self.assertNotIn("อ่านอย่างเดียว", th, f"{key}: 有写工具了还自称只读(th)")
            else:
                self.assertNotIn("授权卡", zh, f"{key}: 没有写工具却承诺授权卡")
                self.assertNotIn("การ์ดขออนุมัติ", th, f"{key}: 没有写工具却承诺授权卡(th)")
