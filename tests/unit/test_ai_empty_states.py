#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_empty_states.py

/ai 空态出路守门(缺口 3/4 · 2026-07-27):
  1. AI.state 的出路件——sectionEmptyHtml 三态各自带得动出路、非法 phase 收敛到 empty、
     文案转义;blockHtml 的「点名去哪 + 直达按钮」(审核/交付包无工单时的出口)。
  2. 相位判定纯函数——reconRender.listPhase(四张单全空=没料可对,非全空=这单真没有)、
     clientWoRender.engineStalled(stuck 且后台报了 blocked_reasons 才算跑挂了)。
  3. ai-i18n-empty.js 分片 zh/th key 集合一致 + 渲染层引用的每个 emp_* key 都真实存在
     ——A 表引用 B 表的 id 必须配闸,否则空态文案静默落成 key 字面量还报绿。
"""

from __future__ import annotations

import json
import re
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_STATE = json.dumps(str(AI_DIR / "ai-state.js"))
_RECON = json.dumps(str(AI_DIR / "ai-recon-render.js"))
_WO = json.dumps(str(AI_DIR / "ai-client-wo-render.js"))
_I18N = json.dumps(str(AI_DIR / "ai-i18n-empty.js"))

# 渲染层拼 key 的两处前缀('emp_brx_' + kind + '_s'),静态正则抓不到完整 key,补闭集。
_BRX_KINDS = ("auto", "review", "missing", "unmatched")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class SectionEmptyHtmlTests(unittest.TestCase):
    def test_three_phases_are_distinguishable_in_markup(self):
        """三态必须在 DOM 上分得出来——真浏览器/E2E 靠 data-state 抓,类名靠 CSS 上色。"""
        out = _run_node(f"""
            const s = require({_STATE});
            process.stdout.write(JSON.stringify(
                s.SECTION_PHASES.map((p) => s.sectionEmptyHtml({{phase: p, title: 't', sub: 'u'}}))
            ));
            """)
        self.assertEqual(len(out), 3)
        for phase, html in zip(["idle", "empty", "error"], out):
            self.assertIn(f'data-state="{phase}"', html)
            self.assertIn(f"sec-empty-{phase}", html)

    def test_unknown_phase_falls_back_to_empty(self):
        """状态诚实:认不出的相位落最保守的「空」,不冒充「失败」也不冒充「还没开始」。"""
        out = _run_node(f"""
            const s = require({_STATE});
            process.stdout.write(JSON.stringify([
                s.sectionEmptyHtml({{phase: 'bogus', title: 't'}}),
                s.sectionEmptyHtml({{title: 't'}}),
            ]));
            """)
        for html in out:
            self.assertIn('data-state="empty"', html)

    def test_idle_carries_a_way_out_and_error_carries_retry(self):
        """空态不许只说「空」:idle 得给去补料的按钮,error 得给重试,且重试的 data-action
        可改写成调用方已有的委托名(工单页那颗断点重试)。"""
        out = _run_node(f"""
            const s = require({_STATE});
            process.stdout.write(JSON.stringify([
                s.sectionEmptyHtml({{
                    phase: 'idle', title: 't', sub: 'u',
                    actionLabel: '去收料', actionHref: '#/clients/9/intake',
                }}),
                s.sectionEmptyHtml({{
                    phase: 'error', title: 't', retryLabel: '重试', retryName: 'wo-retry-stuck',
                }}),
            ]));
            """)
        idle_html, error_html = out
        self.assertIn('href="#/clients/9/intake"', idle_html)
        self.assertIn("去收料", idle_html)
        self.assertIn('data-action="wo-retry-stuck"', error_html)
        self.assertNotIn('data-action="retry"', error_html)

    def test_copy_is_escaped(self):
        out = _run_node(f"""
            const s = require({_STATE});
            process.stdout.write(JSON.stringify(
                s.sectionEmptyHtml({{phase: 'empty', title: 'a<b', sub: '"x"'}})
            ));
            """)
        self.assertIn("a&lt;b", out)
        self.assertNotIn("<b", out.replace("&lt;b", ""))

    def test_block_empty_can_name_a_destination_and_link_to_it(self):
        """缺口 3:审核/交付包的无工单空态得点名去哪 + 给直达按钮,不能只留一句话。"""
        out = _run_node(f"""
            const s = require({_STATE});
            process.stdout.write(JSON.stringify(s.emptyHtml({{
                title: '这个客户还没有工单', sub: '去「工单」tab 开一张',
                actionLabel: '去「工单」tab 开单 →', actionHref: '#/clients/9/wo',
            }})));
            """)
        self.assertIn('data-state="empty"', out)
        self.assertIn('href="#/clients/9/wo"', out)
        self.assertIn("开单", out)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class EmptyPhaseDecisionTests(unittest.TestCase):
    def test_recon_list_phase_splits_no_material_from_real_zero(self):
        """四张单全空 = 对账跑了但手上没料(idle,该指路收料);任一张有行 = 本单的空是
        真结论(empty,该说清为什么空)。"""
        out = _run_node(f"""
            const r = require({_RECON});
            process.stdout.write(JSON.stringify([
                r.listPhase(null),
                r.listPhase({{}}),
                r.listPhase({{auto_matched: [], review: [], missing_invoice: [], unmatched_invoice: []}}),
                r.listPhase({{auto_matched: [1], review: []}}),
                r.listPhase({{unmatched_invoice: [1]}}),
            ]));
            """)
        self.assertEqual(out, ["idle", "idle", "idle", "empty", "empty"])

    def test_engine_stalled_requires_blocked_reasons_not_just_stuck(self):
        """缺料造成的 stuck 是「等人补料」不是「跑挂了」——只有后台报了 blocked_reasons
        才该把空态改口成失败并给重试,否则会把正常等待说成故障。"""
        out = _run_node(f"""
            const w = require({_WO});
            process.stdout.write(JSON.stringify([
                w.engineStalled({{status: 'stuck', blocked_reasons: ['ocr']}}),
                w.engineStalled({{status: 'stuck', blocked_reasons: []}}),
                w.engineStalled({{status: 'stuck'}}),
                w.engineStalled({{status: 'running', blocked_reasons: ['ocr']}}),
                w.engineStalled({{status: 'collecting'}}),
                w.engineStalled(null),
            ]));
            """)
        self.assertEqual(out, [True, False, False, False, False, False])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class EmptyI18nShardTests(unittest.TestCase):
    """分片只写 zh+th(en/ja 由 at() 回落 zh),主词典的四语一致性测试不装本分片,
    自己的闸自己带 —— 同 ai-i18n-states.js 先例。"""

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

    def test_every_referenced_emp_key_exists_in_dictionary(self):
        zh = set(self._shard_keys()["zh"])
        referenced = set()
        for name in (
            "ai-client.js",
            "ai-client-wo-render.js",
            "ai-recon-render.js",
            "ai-shadow-render.js",
            "ai-financials-render.js",
        ):
            text = (AI_DIR / name).read_text(encoding="utf-8")
            # 尾下划线的是拼 key 的前缀字面量('emp_brx_' + kind),不是完整 key。
            referenced |= {k for k in re.findall(r"\bemp_[a-z0-9_]+", text) if not k.endswith("_")}
        referenced |= {f"emp_brx_{kind}_s" for kind in _BRX_KINDS}
        missing = sorted(referenced - zh)
        self.assertEqual(missing, [], f"渲染层引用了词典里没有的 key:{missing}")

    def test_dictionary_has_no_unused_keys(self):
        """反向闸:词条只服务这几个渲染层,留了没人用的 key 就是文案漂移的温床。"""
        zh = set(self._shard_keys()["zh"])
        text = "".join(
            (AI_DIR / name).read_text(encoding="utf-8")
            for name in (
                "ai-client.js",
                "ai-client-wo-render.js",
                "ai-recon-render.js",
                "ai-shadow-render.js",
                "ai-financials-render.js",
            )
        )
        referenced = {k for k in re.findall(r"\bemp_[a-z0-9_]+", text) if not k.endswith("_")}
        referenced |= {f"emp_brx_{kind}_s" for kind in _BRX_KINDS}
        self.assertEqual(sorted(zh - referenced), [])


if __name__ == "__main__":
    unittest.main()
