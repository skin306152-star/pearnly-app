#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_pos_spa_i18n.py

POS PO-B3 收银前台(/pos 独立 SPA · static/pos/)i18n + 失败文案守门。

钉死(对齐 09 §A.3「失败只露人话」+ 06「每个 code 必在 4 语」+ 视觉照搬单语铁律):
  1. pos-i18n.js 的 th/en/zh/ja 四语 key 集合完全一致(任一语缺键 → 切到该语裸露 key)。
  2. docs/pos/06 全部 pos.* 错误码在四语都在且非空(缺翻译 → 前端裸码 / 回退英文)。
  3. pos.* 的 ja 是真日文(≠ en),不是英文兜底。
  4. pos.html 用到的每个 data-i18n / data-i18n-placeholder key 都在字典里(防死 key)。
  5. /pos 各 JS 失败分支统一走 posErrMsg(不裸抛 code、不 showToast(err)、无 'HTTP '+status 拼接)。
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
POS_DIR = PROJECT_ROOT / "static" / "pos"

LANGS = ("th", "en", "zh", "ja")

# docs/pos/06-error-codes.md 全集(信封 error.code)
POS_ERROR_CODES = (
    "pos.pin_invalid",
    "pos.cashier_inactive",
    "pos.product_not_found",
    "pos.out_of_stock",
    "pos.shift_already_open",
    "pos.shift_closed",
    "pos.line_invalid",
    "pos.payment_invalid",
    "pos.void_not_allowed",
    "pos.tax_id_invalid",
    "pos.already_upgraded",
    "pos.over_refund",
    "pos.module_disabled",
    "pos.forbidden",
    "pos.too_many_requests",
    "pos.offline_saved",
    "pos.sync_partial",
    "pos.server_busy",
    "pos.unexpected",
)


def _read(name: str) -> str:
    return (POS_DIR / name).read_text(encoding="utf-8")


def _lang_blocks(src: str) -> dict:
    """切出 window.POS_I18N 里每个语言对象的源码片段(按 `        th: {` 锚点定位)。"""
    blocks = {}
    starts = {}
    for lang in LANGS:
        m = re.search(r"\n        " + lang + r": \{", src)
        assert m, f"pos-i18n.js 缺语言块: {lang}"
        starts[lang] = m.start()
    ordered = sorted(LANGS, key=lambda x: starts[x])
    for i, lang in enumerate(ordered):
        begin = starts[lang]
        end = starts[ordered[i + 1]] if i + 1 < len(ordered) else len(src)
        blocks[lang] = src[begin:end]
    return blocks


def _keys(block: str) -> dict:
    """语言块里所有 'key': value 对(值兼容单/双引号 · 含撇号的英文值用了双引号)。"""
    out = {}
    pat = re.compile(r"""'([\w.]+)':\s*(?:'((?:[^'\\]|\\.)*)'|"((?:[^"\\]|\\.)*)")""")
    for m in pat.finditer(block):
        out[m.group(1)] = m.group(2) if m.group(2) is not None else m.group(3)
    return out


class PosSpaI18nTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = _read("pos-i18n.js")
        cls.blocks = _lang_blocks(cls.src)
        cls.dicts = {lang: _keys(cls.blocks[lang]) for lang in LANGS}

    def test_four_langs_same_keys(self):
        ref = set(self.dicts["zh"].keys())
        self.assertGreater(len(ref), 60, "zh key 数异常少,解析可能出错")
        for lang in LANGS:
            self.assertEqual(
                set(self.dicts[lang].keys()),
                ref,
                f"{lang} 与 zh key 集合不一致(缺/多): "
                f"missing={ref - set(self.dicts[lang])} extra={set(self.dicts[lang]) - ref}",
            )

    def test_all_error_codes_present_nonempty(self):
        for code in POS_ERROR_CODES:
            for lang in LANGS:
                self.assertIn(code, self.dicts[lang], f"{lang} 缺错误码 {code}")
                self.assertTrue(self.dicts[lang][code].strip(), f"{lang} 的 {code} 为空")

    def test_japanese_error_codes_not_english_fallback(self):
        for code in POS_ERROR_CODES:
            self.assertNotEqual(
                self.dicts["ja"][code],
                self.dicts["en"][code],
                f"{code} 的 ja 抄了英文(应为真日文)",
            )

    def test_html_keys_all_defined(self):
        html = _read("pos.html")
        used = set(re.findall(r'data-i18n(?:-placeholder)?="([\w.]+)"', html))
        self.assertGreater(len(used), 20, "pos.html data-i18n 抓取异常")
        zh = self.dicts["zh"]
        for key in used:
            self.assertIn(key, zh, f"pos.html 用到未定义的 i18n key: {key}")

    def test_failures_go_through_pos_err_msg(self):
        # 各 JS 失败分支必须走 posErrMsg / posErrText,禁裸抛 code / showToast(err) / 'HTTP '+status
        for name in ("pos.js", "pos-cashier.js", "pos-ops.js"):
            src = _read(name)
            self.assertNotIn("HTTP ", src, f"{name} 不应向用户拼 'HTTP '+status")
            self.assertNotRegex(
                src,
                r"showToast\(\s*err\s*\)",
                f"{name} 不应 showToast(err) 裸抛异常",
            )
        # 至少一处错误码本地化入口存在(治裸码)
        self.assertIn("posErrMsg", _read("pos-cashier.js"))
        self.assertIn("posErrMsg", _read("pos-ops.js"))


if __name__ == "__main__":
    unittest.main()
