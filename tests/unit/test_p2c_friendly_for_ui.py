#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_p2c_friendly_for_ui.py

守门测试 · P2-C (B7 · Zihao 2026-05-27) · `mrerp_business_friendly.friendly_for_ui`.

P2-C「不裸透泰文」:后端给推送日志/异常响应附 `error_friendly` 4 语 dict,前端优先
用本语言显示,而不是把 raw 泰文/ERR 码直接甩给中日英用户。

friendly_for_ui 契约:
  1. 命中 catalog(ERR_* 或泰文子串)→ 返回主 UI 4 语 {zh,th,en,ja},每个非空
  2. 语言键正好是主 UI 集 zh/th/en/ja(不是 catalog 的 zh_TW)
  3. ja 无目录条目 → 退英文(== en)
  4. 未命中 / None / 空 → 返回 None(让前端回退 humanizeError · 不硬塞 raw)
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.erp import mrerp_business_friendly as mbf  # noqa: E402


class FriendlyForUiTests(unittest.TestCase):
    def test_err_code_match_returns_four_app_langs(self):
        """ERR_NO_CLIENT 在 catalog → 返回 zh/th/en/ja 四语 · 每个非空 · 非原码回显."""
        r = mbf.friendly_for_ui("ERR_NO_CLIENT")
        self.assertIsNotNone(r)
        self.assertEqual(set(r.keys()), {"zh", "th", "en", "ja"})
        for k, v in r.items():
            self.assertTrue(v, f"{k} 友好文案不应为空")
        # 翻译过(不是把 ERR 码原样回显)
        self.assertNotEqual(r["zh"], "ERR_NO_CLIENT")
        self.assertNotEqual(r["th"], "ERR_NO_CLIENT")

    def test_ja_falls_back_to_en(self):
        """catalog 无日语 → ja 退英文(== en)."""
        r = mbf.friendly_for_ui("ERR_NO_CLIENT")
        self.assertEqual(r["ja"], r["en"])

    def test_keys_are_app_ui_set_not_zh_tw(self):
        """主 UI 语言集是 ja 不是 zh_TW(对齐 home.js currentLang)."""
        r = mbf.friendly_for_ui("ERR_NO_CLIENT")
        self.assertIn("ja", r)
        self.assertNotIn("zh_TW", r)

    def test_thai_substring_match(self):
        """泰文子串命中(取 catalog 里真实存在的一条)→ 翻成本语言,不回显泰文原文."""
        # 用 catalog 内确实有的一条泰文 reason 触发子串匹配
        sample = None
        for pattern, _tr in mbf._THAI_REASON_CATALOG:
            sample = pattern
            break
        self.assertIsNotNone(sample, "catalog 应至少有一条泰文 reason")
        r = mbf.friendly_for_ui(sample)
        self.assertIsNotNone(r)
        self.assertEqual(set(r.keys()), {"zh", "th", "en", "ja"})
        # 中文/英文应是翻译后的(与原始泰文 reason 不同)
        self.assertNotEqual(r["en"], sample)

    def test_unknown_returns_none(self):
        """未命中 catalog 的错误(如网络错误)→ None · 前端回退 humanizeError."""
        self.assertIsNone(mbf.friendly_for_ui("ECONNREFUSED some random tail"))
        self.assertIsNone(mbf.friendly_for_ui("totally-unknown-xyz-123"))

    def test_empty_or_none_returns_none(self):
        self.assertIsNone(mbf.friendly_for_ui(None))
        self.assertIsNone(mbf.friendly_for_ui(""))


if __name__ == "__main__":
    unittest.main()
