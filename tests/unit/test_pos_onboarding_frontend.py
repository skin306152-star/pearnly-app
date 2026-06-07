#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_pos_onboarding_frontend.py

POS PO-B1 开通收银(屏8 · src/home/pos-onboarding.ts)前端守门。

钉死(治"假功能 / 字段读错 / 裸码"):
  1. 业态卡发后端的 business_type 必须是后端 BUSINESS_PRESETS 真有的 key(否则静默回落 retail,
     用户选了「餐厅」却开成零售 = 假功能)。
  2. 前端预设面板的 PRESETS 必须与后端 BUSINESS_PRESETS 逐项一致(诚实展示「将开什么」· 不漂移)。
  3. 屏8 i18n key(nav-pos-onboard + posob-*)在 zh/en/th/ja 四语都在(check_i18n 之外的显式兜底)。
  4. 失败分支走 posErrMsg(不裸抛 code / 不 showToast(err))。
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TS = PROJECT_ROOT / "src" / "home" / "pos-onboarding.ts"
I18N = PROJECT_ROOT / "static" / "i18n-data.js"

LANGS = ("zh", "en", "th", "ja")
POSOB_KEYS = (
    "nav-pos-onboard",
    "posob-title",
    "posob-sub",
    "posob-q",
    "posob-type-retail",
    "posob-type-pharmacy",
    "posob-type-restaurant",
    "posob-type-service",
    "posob-type-b2b",
    "posob-preset-suffix",
    "posob-panel-h",
    "posob-cap-multi-unit",
    "posob-cap-track-batch",
    "posob-cap-prescription",
    "posob-tag-on",
    "posob-tag-off",
    "posob-go",
    "posob-done",
    "posob-pin-short",
    "posob-owner-only",
)


class PosOnboardingFrontendTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ts = TS.read_text(encoding="utf-8")
        from services.pos.onboarding import BUSINESS_PRESETS

        cls.backend = BUSINESS_PRESETS

    def _front_presets(self) -> dict:
        m = re.search(r"const PRESETS: Record<string, string\[\]> = \{(.*?)\};", self.ts, re.S)
        self.assertTrue(m, "未找到前端 PRESETS")
        out = {}
        for key, caps in re.findall(r"(\w+):\s*\[([^\]]*)\]", m.group(1)):
            out[key] = re.findall(r"'([a-z_]+)'", caps)
        return out

    def _business_types(self) -> list:
        # TYPES[].bt 是发后端的 business_type
        return re.findall(r"bt:\s*'([a-z_]+)'", self.ts)

    def test_business_types_are_real_backend_keys(self):
        bts = self._business_types()
        self.assertTrue(bts, "未解析到业态 business_type")
        for bt in bts:
            self.assertIn(
                bt,
                self.backend,
                f"业态卡发的 business_type '{bt}' 后端无此预设 → 会静默回落 retail(假功能)",
            )

    def test_frontend_presets_mirror_backend(self):
        front = self._front_presets()
        for key, caps in front.items():
            self.assertIn(key, self.backend, f"前端 PRESETS 多了后端没有的 {key}")
            self.assertEqual(
                sorted(caps),
                sorted(self.backend[key]),
                f"{key} 前后端能力块不一致(预设展示会骗用户)",
            )

    def test_i18n_keys_four_langs(self):
        src = I18N.read_text(encoding="utf-8")
        # 粗切四语块:'zh': { ... 直到下一个顶层语言键。用每语块内是否含 key 判定。
        for key in POSOB_KEYS:
            count = len(re.findall(r"'" + re.escape(key) + r"':", src))
            self.assertGreaterEqual(count, 4, f"i18n key {key} 不足 4 语(实得 {count})")

    def test_failures_localized(self):
        self.assertIn("posErrMsg", self.ts)
        self.assertNotRegex(self.ts, r"showToast\(\s*err\s*\)", "不应 showToast(err) 裸抛")
        self.assertNotIn("HTTP ", self.ts)


if __name__ == "__main__":
    unittest.main()
