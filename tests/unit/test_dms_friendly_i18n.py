#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_dms_friendly_i18n.py

DMS 错误友好文案 i18n 守门(R5 复测 FAIL 修复 · Codex 2026-06-01 R2)。

背景:DMS 错误在 Pearnly 主 UI 渲染时按 currentLang ∈ {zh,en,th,ja} 取文案。
_DMS_FRIENDLY 历史只有 zh/en/th/zh_TW(无 ja)→ 日文界面回退英文(R5 FAIL)。

钉死:
  1. 每条 DMS 友好文案都覆盖主 UI 4 语 zh/en/th/ja(zh_TW 保留不强求)。
  2. ja 非空,且不等于 en(必须是真日文,不是英文兜底)。
  3. _dms_friendly() 对未知码兜底到 ERR_UNEXPECTED,且兜底也带 ja。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.erp import erp_push  # noqa: E402

APP_UI_LANGS = ("zh", "en", "th", "ja")


class TestDmsFriendlyI18n(unittest.TestCase):
    def test_every_entry_covers_app_ui_langs(self):
        for code, d in erp_push._DMS_FRIENDLY.items():
            for lang in APP_UI_LANGS:
                self.assertIn(lang, d, f"{code} missing lang {lang}")
                self.assertTrue(str(d[lang]).strip(), f"{code}.{lang} empty")

    def test_ja_is_real_japanese_not_english_fallback(self):
        for code, d in erp_push._DMS_FRIENDLY.items():
            self.assertNotEqual(d["ja"], d["en"], f"{code} ja still equals en (English fallback)")

    def test_dms_auth_resolves_japanese(self):
        d = erp_push._dms_friendly("ERR_DMS_AUTH")
        self.assertIn("ja", d)
        self.assertTrue(d["ja"].strip())
        self.assertNotEqual(d["ja"], d["en"])

    def test_unknown_code_falls_back_to_unexpected_with_ja(self):
        d = erp_push._dms_friendly("ERR_SOMETHING_NOT_DEFINED")
        self.assertEqual(d, erp_push._DMS_FRIENDLY["ERR_UNEXPECTED"])
        self.assertIn("ja", d)
        self.assertTrue(d["ja"].strip())


if __name__ == "__main__":
    unittest.main()
