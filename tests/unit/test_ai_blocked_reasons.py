#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_blocked_reasons.py

后台卡点(order_detail.blocked_reasons)上屏守门。修的是三件叠在一起的事:

  1. 原因码原样 join 上屏 —— 泰国会计看到的是 "insufficient_balance" 这串生标识符;
  2. 余额不足唯一的按钮是「重试」,而没充值的重试 100% 立刻再 stuck(classify 开跑前
     wallet.exhausted() 就返)—— 一个死循环冒充出路;
  3. ocr_cost_cap_exceeded 与 insufficient_balance 走同一段渲染同一个按钮,「两个原因码
     UI 上分得开、出路不同」在这一屏上不成立。

装真词典跑真 node(同 test_ai_fail_render.py 手法):断言用户真看到的那句话,不是 key。
后端产出的原因码集合与词典对齐也在这里锁(加了码没加词条 = 上屏生码)。
"""

from __future__ import annotations

import json
import re
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, PROJECT_ROOT, _run_node

_LANGS = ("zh", "th", "en", "ja")
_BLOCKED_SHARD = AI_DIR / "ai-i18n-blocked.js"
_CLASSIFY = PROJECT_ROOT / "services" / "workorder" / "steps" / "classify.py"


def _require(name: str) -> str:
    return f"require({json.dumps(str(AI_DIR / name))});\n"


# 真词典 + 真 at():文案断言认中文/泰文本身,不认 key(key 对了文案还能是生码)。
_DICTS = "".join(
    _require(f"ai-i18n-{lang}.js") + _require(f"ai-i18n-{lang}-2.js") for lang in _LANGS
) + _require("ai-i18n-blocked.js")

_PRELUDE = f"""
    global.window = global;
    global.localStorage = {{ getItem: () => null, setItem: () => {{}} }};
    {_DICTS}
    {_require("ai-i18n-fail.js")}
    {_require("ai-i18n.js")}
    {_require("ai-state.js")}
    {_require("ai-format.js")}
    {_require("ai-router.js")}
    {_require("ai-review-queue.js")}
    {_require("ai-fail-render.js")}
    {_require("ai-client-wo-render.js")}
    {_require("ai-viewer.js")}
    {_require("ai-pkg-render.js")}
    """


def _wo_html(detail: dict, lang: str = "zh") -> str:
    return f"""
        {_PRELUDE}
        global.atSetLang({json.dumps(lang)});
        process.stdout.write(JSON.stringify(
            global.AI.clientWoRender.woSummaryHtml({json.dumps(detail)}, 7)
        ));
        """


def _stuck(*reasons) -> dict:
    return {
        "status": "stuck",
        "blocked_reasons": list(reasons),
        "flagged": [],
        "needs": [],
        "numbers": {},
        "period": "2569-05",
    }


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class BlockedReasonLabelTests(unittest.TestCase):
    def _labels(self, reasons):
        return _run_node(f"""
            {_PRELUDE}
            process.stdout.write(JSON.stringify(
                {json.dumps(reasons)}.map(global.AI.format.blockedReasonLabel)
            ));
            """)

    def test_known_codes_become_human_text(self):
        zh = self._labels(["insufficient_balance", "ocr_cost_cap_exceeded"])
        self.assertTrue(all("_" not in s for s in zh), zh)
        self.assertIn("余额", zh[0])
        self.assertIn("预算", zh[1])
        self.assertNotEqual(zh[0], zh[1])  # 两个原因码不是同一句话

    def test_parametric_code_keeps_its_number(self):
        self.assertIn("3", self._labels(["ocr_quota_deferred:3"])[0])

    def test_unknown_code_falls_back_to_the_raw_string(self):
        # 状态诚实:没有词条就如实显示原码,不臆造一句解释。
        self.assertEqual(self._labels(["something_new:7"]), ["something_new:7"])

    def test_topup_detection_only_fires_on_the_balance_code(self):
        out = _run_node(f"""
            {_PRELUDE}
            const f = global.AI.format;
            process.stdout.write(JSON.stringify([
                f.blockedNeedsTopup(['insufficient_balance']),
                f.blockedNeedsTopup(['ocr_quota_deferred:2', 'insufficient_balance']),
                f.blockedNeedsTopup(['ocr_cost_cap_exceeded']),
                f.blockedNeedsTopup([]),
            ]));
            """)
        self.assertEqual(out, [True, True, False, False])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class WorkOrderCardTests(unittest.TestCase):
    """工单卡:跑一半没钱那一屏。E2E 落盘证据里它长这样 ——
    「后台在这里停住:insufficient_balance…」+ 唯一一个「重试」+ topupLinks: 0。"""

    def _html(self, detail, lang="zh"):
        return _run_node(_wo_html(detail, lang))

    def test_balance_stuck_shows_human_text_not_the_raw_code(self):
        html = self._html(_stuck("insufficient_balance"))
        self.assertNotIn("insufficient_balance", html)
        self.assertIn("余额", html)

    def test_balance_stuck_offers_the_topup_deep_link(self):
        html = self._html(_stuck("insufficient_balance"))
        self.assertIn('href="#/settings?focus=billing"', html)
        self.assertIn("去充值", html)

    def test_cost_cap_stuck_has_no_topup_link(self):
        # 内部成本封顶不是用户的钱包问题:出充值按钮等于把我们的预算问题记到用户账上。
        html = self._html(_stuck("ocr_cost_cap_exceeded"))
        self.assertNotIn("#/settings?focus=billing", html)
        self.assertIn('data-action="wo-retry-stuck"', html)

    def test_the_two_money_codes_do_not_render_the_same_card(self):
        self.assertNotEqual(
            self._html(_stuck("insufficient_balance")),
            self._html(_stuck("ocr_cost_cap_exceeded")),
        )

    def test_both_reasons_render_when_backend_reports_both(self):
        html = self._html(_stuck("ocr_quota_deferred:1", "insufficient_balance"))
        self.assertIn("配额", html)
        self.assertIn("余额", html)
        self.assertIn('href="#/settings?focus=billing"', html)

    def test_thai_card_has_no_latin_identifier(self):
        # E2E 证据 s5_th-mobile 里泰文那句是 "ระบบหยุดที่นี่: insufficient_balance ..."。
        html = self._html(_stuck("insufficient_balance"), lang="th")
        self.assertNotIn("insufficient_balance", html)
        self.assertIn("เครดิต OCR", html)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class PackageCardTests(unittest.TestCase):
    """交付包卡走的是另一段渲染,同一份码表 —— 两处分头写迟早漂(pkg 侧此前也是原样 join)。"""

    def _html(self, detail):
        return _run_node(f"""
            {_PRELUDE}
            process.stdout.write(JSON.stringify(
                global.AI.pkgRender.blockedHtml({json.dumps(detail)})
            ));
            """)

    def test_raw_code_never_reaches_the_package_card(self):
        html = self._html({"blocked_reasons": ["insufficient_balance"], "needs": []})
        self.assertNotIn("insufficient_balance", html)
        self.assertIn('href="#/settings?focus=billing"', html)

    def test_missing_materials_still_win_over_topup(self):
        # 缺料能自己补齐,那才是最短出路;余额按钮排它后面(出路只出一个,不摆两个让人挑)。
        html = self._html(
            {"blocked_reasons": ["insufficient_balance"], "needs": ["bank_statement"]}
        )
        self.assertIn('data-action="pkg-go-intake"', html)
        self.assertNotIn("pkg-topup", html)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class DictionaryTests(unittest.TestCase):
    def test_four_languages_have_identical_key_sets(self):
        out = _run_node(f"""
            global.window = global;
            {"".join(f"global.__AI_I18N_{lang.upper()}__ = {{}};" for lang in _LANGS)}
            {_require("ai-i18n-blocked.js")}
            process.stdout.write(JSON.stringify(Object.fromEntries(
                {json.dumps(list(_LANGS))}.map((l) =>
                    [l, Object.keys(global['__AI_I18N_' + l.toUpperCase() + '__']).sort()])
            )));
            """)
        for lang in _LANGS[1:]:
            self.assertEqual(out[lang], out["zh"], f"{lang} 词条 key 集合与 zh 不一致")

    def test_every_backend_stuck_code_has_an_entry(self):
        """classify.py 落进 blocked_reasons 的码必须都在词典里 —— 加了码没加词条 = 上屏生码。"""
        src = _CLASSIFY.read_text(encoding="utf-8")
        codes = set(re.findall(r'blocked\.append\(f?"([a-z_]+)', src))
        codes.add("insufficient_balance")  # ocr_balance.STUCK_REASON,常量引用抓不到字面量
        shard = _BLOCKED_SHARD.read_text(encoding="utf-8")
        for code in codes:
            self.assertIn(f"blocked_{code}", shard, f"原因码 {code} 没有四语词条")

    def test_upload_402_maps_to_a_real_sentence(self):
        # 入料端点的 402 走 mapApiErrorKey('insufficient_balance');没词条就回落 err_generic
        # 「出错了」—— 总台此前根本没有余额闸,补上闸而不补文案等于换个地方给死胡同。
        out = _run_node(f"""
            {_PRELUDE}
            {_require("ai-api.js")}
            const key = global.AI.api.mapApiErrorKey('insufficient_balance');
            process.stdout.write(JSON.stringify([key, global.at(key)]));
            """)
        self.assertEqual(out[0], "err_insufficient_balance")
        self.assertIn("充值", out[1])

    def test_shard_is_loaded_by_the_page(self):
        self.assertIn("ai-i18n-blocked.js", (AI_DIR / "ai.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
