#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_ui_consistency.ratchet_verdict 纯函数单测(REFACTOR-WC)
============================================================
验证 UI 一致性违规棘轮:回退(>基线)fail · 下降/持平 pass。
"""

import importlib.util
import unittest
from pathlib import Path

_MOD_PATH = Path(__file__).resolve().parent.parent.parent / "scripts" / "check_ui_consistency.py"
_spec = importlib.util.spec_from_file_location("check_ui_consistency", _MOD_PATH)
check_ui_consistency = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_ui_consistency)
ratchet_verdict = check_ui_consistency.ratchet_verdict


class TestRatchetVerdict(unittest.TestCase):
    def test_regression_above_baseline_fails(self):
        ok, msg = ratchet_verdict(1788, 1787)
        self.assertFalse(ok)
        self.assertIn("回退", msg)

    def test_equal_baseline_passes(self):
        ok, msg = ratchet_verdict(1787, 1787)
        self.assertTrue(ok)
        self.assertIn("持平", msg)

    def test_below_baseline_passes_with_ratchet_hint(self):
        ok, msg = ratchet_verdict(1500, 1787)
        self.assertTrue(ok)
        self.assertIn("1500", msg)  # 提示可把基线调到 1500

    def test_zero_violations_passes(self):
        ok, _ = ratchet_verdict(0, 1787)
        self.assertTrue(ok)

    def test_default_baseline_constant_is_int(self):
        # 基线常量存在且为非负整数(防被改成 None/字符串导致比较崩)
        self.assertIsInstance(check_ui_consistency.BASELINE_TOTAL, int)
        self.assertGreaterEqual(check_ui_consistency.BASELINE_TOTAL, 0)


if __name__ == "__main__":
    unittest.main()
