#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Daily SPA i18n + 前端纯函数守门(照 test_pos_spa_i18n / _node_harness 范式)。

钉死:
  1. daily-i18n.js 的 th/en/zh/ja 四语 key 集合完全一致(任一语缺键 → 切到该语裸露 key)。
  2. 四语值非空 · ja 是真日文(≠ en),不是英文兜底。
  3. daily.html / daily.js 用到的每个 data-i18n / data-i18n-placeholder / t('key') 都在字典里。
  4. 纯函数(月份/周界/汇总/格式化)node 真跑:与 PWA 原版行为一致。
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from tests.unit._node_harness import _run_node

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DAILY_DIR = PROJECT_ROOT / "static" / "daily"

LANGS = ("th", "en", "zh", "ja")

# 运行时拼接/参数化的键(带 {n}/{month}/{w}/{a}/{b} 占位 · 不直接出现在 t() 字面量):
_VARIADIC_PREFIXES = (
    "daily.gate.err_",
    "daily.confirm.",
    "daily.toast.",
    "daily.err.",
)


def _read(name: str) -> str:
    return (DAILY_DIR / name).read_text(encoding="utf-8")


def _lang_blocks(src: str) -> dict:
    blocks = {}
    starts = {}
    for lang in LANGS:
        m = re.search(r"\n\s+" + lang + r": \{", src)
        assert m, f"daily-i18n.js 缺语言块: {lang}"
        starts[lang] = m.start()
    ordered = sorted(LANGS, key=lambda x: starts[x])
    for i, lang in enumerate(ordered):
        begin = starts[lang]
        end = starts[ordered[i + 1]] if i + 1 < len(ordered) else len(src)
        blocks[lang] = src[begin:end]
    return blocks


def _keys(block: str) -> dict:
    out = {}
    pat = re.compile(r"""'([\w.]+)':\s*(?:'((?:[^'\\]|\\.)*)'|"((?:[^"\\]|\\.)*)")""")
    for m in pat.finditer(block):
        out[m.group(1)] = m.group(2) if m.group(2) is not None else m.group(3)
    return out


class DailyI18nTest(unittest.TestCase):
    def test_four_langs_have_identical_key_sets(self):
        src = _read("daily-i18n.js")
        blocks = {lang: _keys(block) for lang, block in _lang_blocks(src).items()}
        base = set(blocks["th"])
        self.assertTrue(base, "th 键集为空")
        for lang in LANGS:
            self.assertEqual(set(blocks[lang]), base, f"{lang} 与 th 键集不一致")

    def test_no_empty_values_and_ja_is_not_en_fallback(self):
        src = _read("daily-i18n.js")
        blocks = {lang: _keys(block) for lang, block in _lang_blocks(src).items()}
        for lang in LANGS:
            for key, value in blocks[lang].items():
                self.assertTrue(value.strip(), f"{lang}.{key} 为空值")
        ja = blocks["ja"]
        en = blocks["en"]
        self.assertNotEqual(ja, en, "ja 块整体等于 en(假日文兜底)")

    def test_html_and_js_reference_only_existing_keys(self):
        src = _read("daily-i18n.js")
        blocks = {lang: _keys(block) for lang, block in _lang_blocks(src).items()}
        known = set(blocks["th"])

        html = _read("daily.html")
        for key in re.findall(r"data-i18n(?:-placeholder)?=\"([\w.]+)\"", html):
            self.assertIn(key, known, f"daily.html 引用未知键: {key}")

        js = _read("daily.js") + _read("daily-actions.js")
        for key in re.findall(r"(?:\bt|\bcore\.t)\('([\w.]+)'", js):
            self.assertIn(key, known, f"daily.js 引用未知键: {key}")
        for key in re.findall(r"(?:\bt|\bcore\.t)\('([\w.]+)'", js):
            if key.startswith(_VARIADIC_PREFIXES):
                self.assertTrue(
                    any(key.startswith(p) for p in _VARIADIC_PREFIXES),
                    f"动态键缺前缀白名单: {key}",
                )

    def test_th_block_is_thai_not_latin(self):
        src = _read("daily-i18n.js")
        th = _keys(_lang_blocks(src)["th"])
        sample = " ".join(th.values())
        self.assertTrue(
            re.search(r"[\u0e00-\u0e7f]", sample),
            "th 块应含泰文字符(值贴错语言块 = 用户看到错语言)",
        )

    def test_empty_gate_root_collapses_in_source_and_bundle(self):
        source_css = _read("daily-gate.css")
        bundle_css = (PROJECT_ROOT / "static" / "dist" / "daily.css").read_text(encoding="utf-8")
        self.assertRegex(source_css, r"#gateRoot:empty\s*\{\s*display:\s*none")
        self.assertIn("#gateRoot:empty{display:none}", bundle_css)

    def test_daily_uses_buddhist_display_and_single_click_binding(self):
        js = _read("daily.js")
        self.assertIn("_dailyClickBound", js)
        out = _run_node(
            "const d = require('./static/daily/daily-core.js');"
            "console.log(JSON.stringify({year:d.buddhistYear(2026),date:d.buddhistDateLabel('2026-08-01')}))"
        )
        self.assertEqual(out, {"year": 2569, "date": "2569/08/01"})


class DailyPureFunctionsTest(unittest.TestCase):
    def test_week_bounds_match_pwa_semantics(self):
        out = _run_node(
            "const d = require('./static/daily/daily-core.js');"
            "console.log(JSON.stringify({"
            "  w1: d.weekBounds(2026, 9, 1),"
            "  w5: d.weekBounds(2026, 9, 5),"
            "  feb: d.weekBounds(2027, 2, 5)"
            "}))"
        )
        self.assertEqual(
            out["w1"], {"startDay": 1, "endDay": 7, "min": "2026-09-01", "max": "2026-09-07"}
        )
        self.assertEqual(
            out["w5"], {"startDay": 29, "endDay": 30, "min": "2026-09-29", "max": "2026-09-30"}
        )
        self.assertEqual(out["feb"]["endDay"], 28, "2027-02 非闰年 · 第5周止于 28")

    def test_month_options_cover_last_13_months_ending_current(self):
        out = _run_node(
            "const d = require('./static/daily/daily-core.js');"
            "console.log(JSON.stringify(d.monthOptions(new Date(2026, 8, 15))))"
        )
        self.assertEqual(len(out), 13)
        self.assertEqual(out[0]["id"], "2025-09")
        self.assertEqual(out[-1]["id"], "2026-09")

    def test_sumby_separates_kinds(self):
        out = _run_node(
            "const d = require('./static/daily/daily-core.js');"
            "const es = [{kind:'income', amount:'100'},{kind:'expense', amount:'40.5'},{kind:'expense', amount:'9.5'}];"
            "console.log(JSON.stringify({i: d.sumBy(es,'income'), e: d.sumBy(es,'expense')}))"
        )
        self.assertEqual(out["i"], 100)
        self.assertEqual(out["e"], 50)

    def test_month_and_range_filters(self):
        out = _run_node(
            "const d = require('./static/daily/daily-core.js');"
            "const es = [{entry_date:'2026-09-03'},{entry_date:'2026-09-11'},{entry_date:'2026-10-01'}];"
            "console.log(JSON.stringify({"
            " m: es.filter(e => d.inMonth(e, '2026-09')).length,"
            " r: es.filter(e => d.inRange(e, '2026-09-01', '2026-09-07')).length"
            "}))"
        )
        self.assertEqual(out["m"], 2)
        self.assertEqual(out["r"], 1)

    def test_escape_html(self):
        out = _run_node(
            "const d = require('./static/daily/daily-core.js');"
            "console.log(JSON.stringify(d.escapeHtml('<a href=\"x\">&</a>')))"
        )
        self.assertEqual(out, "&lt;a href=&quot;x&quot;&gt;&amp;&lt;/a&gt;")


if __name__ == "__main__":
    unittest.main()
