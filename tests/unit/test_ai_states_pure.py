#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_states_pure.py

状态词典 #/states(B1 · 状态语言底座)守门:
  1. ai-states-render.js 纯函数——八色族/15 类/按钮七态闭集、越界值收敛(百分比钳位、
     非法色族落空白族)、HTML 转义(状态文案可能带用户数据)。
  2. ai-states.js 的演示步进 nextDemoPct 越界回卷。
  3. ai-i18n-states.js 分片 zh/th key 集合一致(主词典的四语一致性测试不装本分片,
     这里自己锁)+ 样例页/壳引用的每个 sts_* key 都真实存在于 zh 词典——A 表引用
     B 表的 id 必须配闸,防「深链 35 条全落空却报绿」的老坑重演。
  4. ai-router.js 的 #/states 往返解析(新路由不破既有路由)。
"""

from __future__ import annotations

import json
import re
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_RENDER = json.dumps(str(AI_DIR / "ai-states-render.js"))
_STATES = json.dumps(str(AI_DIR / "ai-states.js"))
_ROUTER = json.dumps(str(AI_DIR / "ai-router.js"))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class StatesRenderPureTests(unittest.TestCase):
    def test_families_and_categories_are_the_approved_closed_sets(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([r.FAMILIES, r.CATEGORIES, r.BTN_STATES]));
            """)
        self.assertEqual(out[0], ["ok", "wait", "run", "ai", "warn", "err", "off", "empty"])
        # 15 类顺序 = Zihao 拍板原话顺序,少一节/错序都算走样。
        self.assertEqual(
            out[1],
            [
                "data",
                "task",
                "ai",
                "flow",
                "system",
                "progress",
                "risk",
                "review",
                "file",
                "notify",
                "perm",
                "button",
                "explain",
                "color",
                "anim",
            ],
        )
        self.assertEqual(
            out[2], ["default", "hover", "active", "disabled", "loading", "success", "error"]
        )

    def test_badge_escapes_label_and_unknown_family_falls_to_empty(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.badgeHtml('ok', '<b>x</b>'),
                r.badgeHtml('nope', 'y'),
                r.badgeHtml('warn', 'z', {{ bounce: true }}),
            ]));
            """)
        self.assertIn("st-badge st-ok", out[0])
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", out[0])
        self.assertNotIn("<b>x</b>", out[0])
        # 非法色族不冒充任何具体状态,落空白族。
        self.assertIn("st-empty", out[1])
        self.assertIn("st-badge-bounce", out[2])

    def test_bar_and_ring_clamp_percent_into_0_100(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.barHtml('run', 64), r.barHtml('run', 250), r.barHtml('run', -3),
                r.barHtml('run', 'oops'), r.ringHtml('run', 40.6),
                r.barHtml('run', 10, {{ demo: true }}),
            ]));
            """)
        self.assertIn("--p:64", out[0])
        self.assertIn("--p:100", out[1])
        self.assertIn("--p:0", out[2])
        self.assertIn("--p:0", out[3])
        self.assertIn("--p:41", out[4])
        self.assertIn("<b>41%</b>", out[4])
        self.assertIn('data-demo="pct"', out[5])
        self.assertNotIn("data-demo", out[0])

    def test_steps_render_on_segments_and_clamp_current(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.stepsHtml('run', 3, 8), r.stepsHtml('run', 99, 4), r.stepsHtml('run', -1, 4),
            ]));
            """)
        self.assertEqual(out[0].count('<i class="on">'), 3)
        self.assertEqual(out[0].count("<i>"), 8 - 3)
        self.assertEqual(out[1].count('<i class="on">'), 4)
        self.assertEqual(out[2].count('<i class="on">'), 0)

    def test_button_seven_states_shapes(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            const states = r.BTN_STATES.map((s) => r.btnHtml(s, 'go'));
            states.push(r.btnHtml('bogus', 'go'));
            process.stdout.write(JSON.stringify(states));
            """)
        default, hover, active, disabled, loading, success, error, bogus = out
        self.assertNotIn("is-", default)
        self.assertIn("is-hover", hover)
        self.assertIn("is-active", active)
        self.assertIn(" disabled", disabled)
        # loading:三点内嵌 + disabled 双保险。
        self.assertIn("is-loading", loading)
        self.assertIn("st-dots", loading)
        self.assertIn(" disabled", loading)
        self.assertIn("is-success", success)
        self.assertIn("is-error", error)
        self.assertNotIn("is-", bogus)

    def test_explain_card_open_state_and_sources(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            const opts = {{
                badgeLabel: 'AI', verdict: 'v<1>', toggleLabel: 't',
                sources: [{{ k: 'face', v: 'val&1' }}],
            }};
            process.stdout.write(JSON.stringify([
                r.explainCardHtml(opts),
                r.explainCardHtml(Object.assign({{ open: true }}, opts)),
            ]));
            """)
        self.assertIn('class="st-explain"', out[0])
        self.assertIn('class="st-explain on"', out[1])
        self.assertIn("v&lt;1&gt;", out[0])
        self.assertIn("val&amp;1", out[0])
        self.assertIn('data-action="sts-explain-toggle"', out[0])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class StatesDemoTickTests(unittest.TestCase):
    def test_next_demo_pct_advances_and_wraps(self):
        out = _run_node(f"""
            const s = require({_STATES});
            process.stdout.write(JSON.stringify([
                s.nextDemoPct(0), s.nextDemoPct(64), s.nextDemoPct(99),
                s.nextDemoPct(100), s.nextDemoPct(-5), s.nextDemoPct('x'),
            ]));
            """)
        self.assertEqual(out, [9, 73, 0, 0, 9, 9])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class StatesI18nShardTests(unittest.TestCase):
    """zh/th key 一致 + 被引用 key 必须真实存在(词典分片不在主四语一致性测试的装载清单里,
    自己的闸自己带)。"""

    def _shard_keys(self):
        out = _run_node(f"""
            global.window = global;
            global.__AI_I18N_ZH__ = {{}};
            global.__AI_I18N_TH__ = {{}};
            global.__AI_I18N_EN__ = {{}};
            global.__AI_I18N_JA__ = {{}};
            require({json.dumps(str(AI_DIR / "ai-i18n-states.js"))});
            process.stdout.write(JSON.stringify({{
                zh: Object.keys(global.__AI_I18N_ZH__).sort(),
                th: Object.keys(global.__AI_I18N_TH__).sort(),
            }}));
            """)
        return out

    def test_zh_and_th_key_sets_identical(self):
        keys = self._shard_keys()
        self.assertTrue(keys["zh"], "分片 zh 词条为空")
        self.assertEqual(keys["zh"], keys["th"], "th 词典 key 集合与 zh 不一致")

    def test_every_referenced_sts_key_exists_in_dictionary(self):
        zh = set(self._shard_keys()["zh"])
        referenced = set()
        for name in ("ai-states-render.js", "ai-states.js", "ai.html", "ai.js"):
            text = (AI_DIR / name).read_text(encoding="utf-8")
            # 尾下划线的是动态拼 key 的前缀字面量('sts_st_' + state),不是完整 key。
            referenced |= {k for k in re.findall(r"\bsts_[a-z0-9_]+", text) if not k.endswith("_")}
        # 动态拼 key 的两处(sts_st_ + 按钮态 / sts_fam_ + 色族)静态正则抓不全,补上闭集。
        referenced |= {
            f"sts_st_{s}"
            for s in ("default", "hover", "active", "disabled", "loading", "success", "error")
        }
        referenced |= {
            f"sts_fam_{f}" for f in ("ok", "wait", "run", "ai", "warn", "err", "off", "empty")
        }
        missing = sorted(k for k in referenced if k not in zh)
        self.assertEqual(missing, [], f"页面引用了词典里不存在的 key: {missing}")
        unused = sorted(k for k in zh if k not in referenced)
        self.assertEqual(unused, [], f"词典里有没人引用的死 key: {unused}")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class StatesRouteTests(unittest.TestCase):
    def test_states_route_round_trips_and_leaves_others_alone(self):
        out = _run_node(f"""
            const r = require({_ROUTER});
            process.stdout.write(JSON.stringify([
                r.parseHash('#/states'),
                r.parseHash(r.buildStatesHash()),
                r.parseHash('#/settings'),
                r.parseHash('#/statesx'),
            ]));
            """)
        self.assertEqual(out[0], {"name": "states"})
        self.assertEqual(out[1], {"name": "states"})
        self.assertEqual(out[2], {"name": "settings", "focus": None})
        # 未知路径仍落工作台默认,不被新路由前缀劫走。
        self.assertEqual(out[3], {"name": "dashboard", "sub": "matrix"})


if __name__ == "__main__":
    unittest.main()
