#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ui_copy_signposts.py

指路与方位的机械闸(2026-07-27 文案验收揪出的两条硬伤)。

一、指路存在性:错误文案里「去 X 看」的 X 必须是产品里真有的那一项。
    反面教材是 bridge_offline 曾经写的「集成 · ERP 桥」—— 全仓没有这一栏,会计照着找
    只能找到自己;「集成 · 推送日志」同理,推送日志 2026-07-01 已搬成独立导航项。
    判据一律从【真实产物】取:主站侧栏取 app-shell-sidebar-html.ts 的 data-i18n,/ai 取
    ai.html 的 data-at,再到两份真词典里换成中泰文 —— 不在测试里手抄一份菜单名清单
    (手抄的那份会跟着菜单一起漂,还漂得毫无声响)。

二、方位词:管家页 900px 以下是单栏(执行状态在上、对话在下),「左侧 / 右侧」到手机
    上一律是错的。只管左右不管上下 —— 泰文 ด้านบน 常指「同一条消息里上面那几个数」,
    那是文内指代不是版面方位,一并禁会把对的句子也判红。

两个闸都自带反证(见 SelfCheckTests):判据取空、或改坏了检不出已知的错句,当场红。
"""

from __future__ import annotations

import re
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, PROJECT_ROOT, _run_node

_AI_HTML = AI_DIR / "ai.html"
_MAIN_SIDEBAR = PROJECT_ROOT / "src" / "home" / "app-shell-sidebar-html.ts"
_MAIN_I18N = PROJECT_ROOT / "static" / "i18n-data.js"

# /ai 词典分片(与 test_ui_copy_register 同一份清单:两个闸扫的是同一片文案面)。
_SHARDS = (
    "ai-i18n-zh.js",
    "ai-i18n-zh-2.js",
    "ai-i18n-th.js",
    "ai-i18n-th-2.js",
    "ai-i18n-steward.js",
    "ai-i18n-empty.js",
    "ai-i18n-fail.js",
    "ai-i18n-blocked.js",
    "ai-i18n-board.js",
    "ai-i18n-bank-sales.js",
    "ai-i18n-machine-actions.js",
)

_COPY_MODULES = (
    "copy",
    "copy_artifacts",
    "copy_brief",
    "copy_calc",
    "copy_close",
    "copy_erp_push",
    "copy_file",
    "copy_loop",
    "copy_period",
)

# 指路的取词:只认跟在指路动词后面(或后面直接跟「页」)的那一对方角括号,且里面不带
# {} 占位符 —— 「{keyword}」这类是用户打的字与数据回显,不是菜单名。
_SIGNPOST = {
    "zh": (
        re.compile(r"(?:去|到|见|在|至|看)\s*「([^」{}]+)」"),
        re.compile(r"「([^」{}]+)」\s*页"),
    ),
    "th": (re.compile(r"(?:ที่|ใน|หน้า)\s*「([^」{}]+)」"),),
}

_DIRECTION_WORDS = {
    "zh": ("左侧", "右侧", "左边", "右边"),
    "th": ("ทางซ้าย", "ทางขวา", "ด้านซ้าย", "ด้านขวา"),
}

_LANGS = ("zh", "th")


def _lang_texts_from_python() -> dict[str, list[tuple[str, str]]]:
    """管家文案层的模块级容器 → {lang: [(出处, 文案)]}。

    只收 {"zh": ..., "th": ...} 这一形状:管家所有对外串都装在这种双语表里,别的模块级
    常量(BAHT、行数上限)不是文案。
    """
    import importlib

    out: dict[str, list[tuple[str, str]]] = {lang: [] for lang in _LANGS}

    def walk(value, where: str) -> None:
        if isinstance(value, dict):
            if any(lang in value for lang in _LANGS):
                for lang in _LANGS:
                    text = value.get(lang)
                    if isinstance(text, str):
                        out[lang].append((where, text))
            for key, sub in value.items():
                walk(sub, f"{where}[{key!r}]")
        elif isinstance(value, (list, tuple)):
            for i, sub in enumerate(value):
                walk(sub, f"{where}[{i}]")

    for name in _COPY_MODULES:
        module = importlib.import_module(f"services.steward.{name}")
        for attr, value in vars(module).items():
            if not attr.startswith("__"):
                walk(value, f"{module.__name__}.{attr}")
    return out


def _lang_texts_from_dictionaries(dicts: dict) -> dict[str, list[tuple[str, str]]]:
    return {
        lang: [
            (f"{lang}.{key}", text) for key, text in dicts[lang].items() if isinstance(text, str)
        ]
        for lang in _LANGS
    }


def _node_dictionaries() -> dict:
    """一次 node 调用同时装 /ai 分片与主站 window.I18N —— 两边都是真跑产物,不是正则解析。"""
    requires = "".join(f"require({str(AI_DIR / name)!r});" for name in _SHARDS)
    return _run_node(f"""
        global.window = global;
        global.__AI_I18N_ZH__ = {{}};
        global.__AI_I18N_TH__ = {{}};
        global.__AI_I18N_EN__ = {{}};
        global.__AI_I18N_JA__ = {{}};
        {requires}
        require({str(_MAIN_I18N)!r});
        process.stdout.write(JSON.stringify({{
            zh: global.__AI_I18N_ZH__, th: global.__AI_I18N_TH__,
            main_zh: global.I18N.zh, main_th: global.I18N.th,
        }}));
        """)


def _real_destinations(dicts: dict) -> dict[str, set[str]]:
    """真实可去之处 = /ai 壳里挂出来的导航/标签页 + 主站侧栏的每一项(换成中泰文)。"""
    ai_keys = set(re.findall(r'data-at="((?:nav|tab)_[a-z0-9_]+)"', _AI_HTML.read_text("utf-8")))
    main_keys = set(
        re.findall(
            r'class="nav-label" data-i18n="([a-z0-9-]+)"',
            _MAIN_SIDEBAR.read_text("utf-8"),
        )
    )
    out: dict[str, set[str]] = {}
    for lang in _LANGS:
        labels = {dicts[lang].get(k) for k in ai_keys}
        labels |= {dicts[f"main_{lang}"].get(k) for k in main_keys}
        out[lang] = {str(x).strip() for x in labels if isinstance(x, str) and x.strip()}
    return out


def _signposts(lang: str, text: str) -> list[str]:
    return [hit for rule in _SIGNPOST[lang] for hit in rule.findall(text)]


def _bad_signposts(texts: dict, real: dict) -> list[str]:
    bad = []
    for lang in _LANGS:
        for where, text in texts[lang]:
            for dest in _signposts(lang, text):
                if dest.strip() not in real[lang]:
                    bad.append(f"{where}: 「{dest}」不是真实导航项 · 原文:{text}")
    return bad


def _bad_directions(texts: dict) -> list[str]:
    bad = []
    for lang in _LANGS:
        for where, text in texts[lang]:
            for word in _DIRECTION_WORDS[lang]:
                if word in text:
                    bad.append(f"{where}: 「{word}」· 单栏下方位是错的 · 原文:{text}")
    return bad


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过词典装载")
class SignpostTests(unittest.TestCase):
    """指路的那一项必须在真实导航里存在。"""

    @classmethod
    def setUpClass(cls):
        cls.dicts = _node_dictionaries()
        cls.real = _real_destinations(cls.dicts)
        cls.texts = {
            lang: _lang_texts_from_python()[lang] + _lang_texts_from_dictionaries(cls.dicts)[lang]
            for lang in _LANGS
        }

    def test_every_signpost_names_a_real_navigation_item(self):
        bad = _bad_signposts(self.texts, self.real)
        self.assertEqual(bad, [], "文案指向了产品里不存在的地方:\n" + "\n".join(bad))

    def test_the_gate_actually_looked_at_something(self):
        """判据取空 = 闸永远绿。真实菜单表与被扫的指路条数都必须非空。"""
        for lang in _LANGS:
            self.assertGreater(len(self.real[lang]), 10, f"{lang} 的真实菜单表没解析出来")
            found = [d for _, t in self.texts[lang] for d in _signposts(lang, t)]
            self.assertGreater(len(found), 0, f"{lang} 一条指路都没扫到 —— 取词规则失效了")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过词典装载")
class DirectionWordTests(unittest.TestCase):
    """左右方位词不许上屏:900px 以下管家是单栏,左右都不成立。"""

    @classmethod
    def setUpClass(cls):
        dicts = _node_dictionaries()
        cls.texts = {
            lang: _lang_texts_from_python()[lang] + _lang_texts_from_dictionaries(dicts)[lang]
            for lang in _LANGS
        }

    def test_no_left_right_words_in_user_facing_copy(self):
        bad = _bad_directions(self.texts)
        self.assertEqual(bad, [], "文案用了在手机上不成立的方位词:\n" + "\n".join(bad))


class SelfCheckTests(unittest.TestCase):
    """反证:两个闸都要能对已知的错句报红,否则「全绿」只说明它没在看。"""

    def test_a_menu_that_never_existed_is_reported(self):
        texts = {"zh": [("fake", "去「集成 · ERP 桥」确认小助手在线。")], "th": []}
        real = {"zh": {"集成", "推送日志"}, "th": set()}
        self.assertEqual(len(_bad_signposts(texts, real)), 1)

    def test_a_real_menu_passes(self):
        texts = {"zh": [("fake", "去「推送日志」看这张票的状态。")], "th": []}
        real = {"zh": {"集成", "推送日志"}, "th": set()}
        self.assertEqual(_bad_signposts(texts, real), [])

    def test_a_direction_word_is_reported(self):
        texts = {"zh": [("fake", "在右侧输入要办的事。")], "th": []}
        self.assertEqual(len(_bad_directions(texts)), 1)


if __name__ == "__main__":
    unittest.main()
