#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""i18n 词典解析器的反证 + 「同一语言块键重复」这道新闸。

为什么单独有这一份:check_i18n 报的数字一直是**对不上真词典**的。它按行读、一行只认第一个键,
而字典里有 12 行是一行写好几条 —— 2026-07-31 实测每种语言各漏数 14 个键(5019 → 5033),
其中 `user-menu-logout` / `set-group-*` / `help-modal-tip` 这些从来没进过那道完整性闸的射程。
少数了还报「0 missing」,是这道闸最坏的失效方式:它不是没拦住,是它压根没看见。

而重复键是另一条它结构上看不见的缝:同一个键写两遍,四语一起数都对得上,missing/extra 全 0,
界面上生效的是文件里靠后那一条 —— 改文案的人对着靠前那条改,改完没反应,查不出为什么。
(真实存量:cs-dashboard-desc 两条值完全不同,靠前那条是死文案。)

下面每条用例都喂**会出事的输入**:一行多键、值里带不成对的花括号、值里带转义引号、注释里带冒号。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from check_i18n import (  # noqa: E402
    _i18n_source_file,
    duplicate_keys,
    iter_i18n_entries,
    parse_i18n_blocks,
)


def dict_js(*per_lang: str) -> str:
    """真词典的形状:window.I18N = { zh: {…}, en: {…}, th: {…}, ja: {…} }。"""
    body = "\n".join(
        f"    {lang}: {{\n{rows}\n    }}," for lang, rows in zip(("zh", "en", "th", "ja"), per_lang)
    )
    return "window.I18N = {\n" + body + "\n};\n"


def same_for_all(rows: str) -> str:
    return dict_js(rows, rows, rows, rows)


class OneLineManyKeys(unittest.TestCase):
    """本闸存在的理由 —— 旧解析器在这种行上只认第一个键。"""

    ROW = "        'a': '甲', 'b': '乙', 'c': '丙',"

    def test_every_key_on_a_shared_line_is_seen(self):
        self.assertEqual(parse_i18n_blocks(same_for_all(self.ROW))["zh"], {"a", "b", "c"})

    def test_a_key_missing_only_on_a_shared_line_still_gets_caught(self):
        """漏译刚好落在一行多键的那一行上 —— 旧解析器两边都只看得见 'a',于是报 0 missing。"""
        blocks = parse_i18n_blocks(
            dict_js(self.ROW, self.ROW, "        'a': 'ก', 'b': 'ข',", self.ROW)
        )
        self.assertEqual(blocks["zh"] - blocks["th"], {"c"})


class ValuesThatLookLikeSyntax(unittest.TestCase):
    """值里本来就带花括号(989 行有 {n} 占位符)和引号 —— 按字符数括号迟早算歪。"""

    def test_unbalanced_brace_in_a_value_does_not_end_the_block(self):
        rows = "        'tip': '用 { 开头',\n        'after': '后面这条不能丢',"
        self.assertEqual(parse_i18n_blocks(same_for_all(rows))["zh"], {"tip", "after"})

    def test_escaped_quote_in_a_value_does_not_swallow_the_next_key(self):
        rows = "        'q': 'it\\'s fine',\n        'next': '下一条',"
        self.assertEqual(parse_i18n_blocks(same_for_all(rows))["zh"], {"q", "next"})

    def test_a_colon_inside_a_comment_is_not_a_key(self):
        rows = "        // 备注:'ghost': 这行是注释\n        'real': '真的',"
        self.assertEqual(parse_i18n_blocks(same_for_all(rows))["zh"], {"real"})

    def test_a_nested_object_value_does_not_leak_its_inner_keys(self):
        rows = "        'outer': { 'inner': 1 },\n        'plain': '平的',"
        self.assertEqual(parse_i18n_blocks(same_for_all(rows))["zh"], {"outer", "plain"})


class DuplicateKeysAreCaught(unittest.TestCase):
    """新闸:同一语言块里写两遍。"""

    def test_a_repeated_key_is_reported_with_both_line_numbers(self):
        rows = "        'k': '先写的',\n        'other': '别的',\n        'k': '后写的才生效',"
        dupes = duplicate_keys(same_for_all(rows))
        self.assertEqual(sorted(dupes), ["en", "ja", "th", "zh"])
        self.assertEqual(dupes["zh"], ["k(行 3, 5)"])

    def test_two_copies_on_the_same_line_are_caught_too(self):
        self.assertEqual(
            duplicate_keys(same_for_all("        'k': '甲', 'k': '乙',"))["zh"], ["k(行 3, 3)"]
        )

    def test_the_same_key_across_languages_is_not_a_duplicate(self):
        """误报反证:词典本来就是四语各一份同名键 —— 这道闸只在语言块【内部】看重复。"""
        self.assertEqual(duplicate_keys(same_for_all("        'k': '甲',")), {})

    def test_the_old_completeness_gate_calls_a_duplicated_dictionary_clean(self):
        """对照组:重复键在完整性闸眼里 missing/extra 全是 0 —— 这正是它藏了这么久的原因。"""
        from check_i18n import diff_keysets

        rows = "        'k': '先写的',\n        'k': '后写的',"
        diffs = diff_keysets(parse_i18n_blocks(same_for_all(rows)))
        self.assertEqual({lang: d for lang, d in diffs.items() if d["missing"] or d["extra"]}, {})


class TheRealDictionary(unittest.TestCase):
    """闸自检:解析器扫不到东西时上面每条都会「通过」,绿得毫无意义。"""

    @classmethod
    def setUpClass(cls):
        cls.text = _i18n_source_file().read_text(encoding="utf-8")

    def test_four_blocks_with_thousands_of_keys(self):
        blocks = parse_i18n_blocks(self.text)
        self.assertEqual(set(blocks), {"zh", "en", "th", "ja"})
        self.assertGreater(len(blocks["zh"]), 4000, "只解出这么点键 —— 解析器没在读真词典")

    def test_keys_that_only_the_token_scanner_can_see_are_present(self):
        """挑几个真实存在、且【只写在一行多键那种行上】的键:按行读的解析器看不见它们。"""
        zh = parse_i18n_blocks(self.text)["zh"]
        for key in ("user-menu-logout", "set-group-about", "help-modal-tip", "contact-line-label"):
            self.assertIn(key, zh)

    def test_line_numbers_point_at_the_real_line(self):
        lines = self.text.splitlines()
        for lang, key, line in iter_i18n_entries(self.text):
            self.assertIn(f"'{key}'", lines[line - 1], f"{lang}.{key} 的行号指错了行")
            break

    def test_no_duplicate_keys_in_the_shipped_dictionary(self):
        dupes = duplicate_keys(self.text)
        self.assertEqual(
            dupes,
            {},
            "同一语言块里有键写了两遍 —— 生效的是靠后那条,靠前那条是死文案。"
            "删掉靠前那条(删靠后的会改变界面上真正显示的字)。",
        )


if __name__ == "__main__":
    unittest.main()
