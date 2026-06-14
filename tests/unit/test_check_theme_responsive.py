# -*- coding: utf-8 -*-
"""check_theme_responsive 检测器 + 棘轮裁决单测。

锁定两件最易错的事:① 半透明 rgba(阴影/遮罩)必须豁免,否则全站误报爆炸
② 走 var(--token) 的合规写法必须放行。
"""

import importlib.util
import unittest
from pathlib import Path

_MOD_PATH = Path(__file__).resolve().parent.parent.parent / "scripts" / "check_theme_responsive.py"
_spec = importlib.util.spec_from_file_location("check_theme_responsive", _MOD_PATH)
ctr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ctr)


class OffTokenColorTests(unittest.TestCase):
    def _scan(self, css):
        return ctr.scan_offtoken_colors(css, ts_mode=False)

    def test_three_digit_hex_caught(self):
        hits = self._scan("a { color: #fff; }")
        self.assertEqual(len(hits["暗夜:3位hex"]), 1)

    def test_six_digit_hex_not_caught_as_three(self):
        # 6 位 hex 由现有闸管,本闸不重复计数
        hits = self._scan("a { color: #2563EB; background: #ffffff; }")
        self.assertEqual(len(hits["暗夜:3位hex"]), 0)

    def test_white_keyword_caught(self):
        hits = self._scan("a { background: white; }")
        self.assertEqual(len(hits["暗夜:white/black关键字"]), 1)

    def test_white_space_property_not_caught(self):
        # white-space: nowrap 不是颜色
        hits = self._scan("a { white-space: nowrap; }")
        self.assertEqual(len(hits["暗夜:white/black关键字"]), 0)

    def test_opaque_rgb_caught(self):
        hits = self._scan("a { background: rgb(255,0,0); }")
        self.assertEqual(len(hits["暗夜:不透明rgb"]), 1)

    def test_rgba_alpha_one_caught(self):
        hits = self._scan("a { color: rgba(0,0,0,1); }")
        self.assertEqual(len(hits["暗夜:不透明rgb"]), 1)

    def test_translucent_rgba_exempt(self):
        # 阴影/遮罩半透明黑叠任意底色都成立 → 豁免,否则误报爆炸
        css = "a { box-shadow: 0 2px 8px rgba(0,0,0,0.12); background: rgba(255,255,255,.5); }"
        self.assertEqual(len(self._scan(css)["暗夜:不透明rgb"]), 0)

    def test_var_token_passes(self):
        css = "a { background: var(--bg); color: var(--ink); box-shadow: 0 1px 2px var(--shadow); }"
        hits = self._scan(css)
        self.assertEqual(sum(len(v) for v in hits.values()), 0)

    def test_ts_mode_ignores_non_css_lines(self):
        # .ts 里非 CSS 行(JS 字面量)的 #fff 不算
        js_line = 'const code = "#fff";'
        self.assertEqual(
            sum(len(v) for v in ctr.scan_offtoken_colors(js_line, ts_mode=True).values()), 0
        )
        css_line = "el.style.cssText = `color: #fff`;"
        self.assertEqual(len(ctr.scan_offtoken_colors(css_line, ts_mode=True)["暗夜:3位hex"]), 1)


class FixedWideTests(unittest.TestCase):
    def test_fixed_wide_caught(self):
        self.assertEqual(len(ctr.scan_fixed_wide("a { width: 600px; }")), 1)

    def test_max_width_exempt(self):
        self.assertEqual(len(ctr.scan_fixed_wide("a { max-width: 600px; }")), 0)

    def test_small_width_ok(self):
        self.assertEqual(len(ctr.scan_fixed_wide("a { width: 40px; }")), 0)


class ViewportTests(unittest.TestCase):
    def test_present(self):
        self.assertTrue(
            ctr.has_viewport('<meta name="viewport" content="width=device-width, initial-scale=1">')
        )

    def test_missing(self):
        self.assertFalse(ctr.has_viewport("<head><title>x</title></head>"))

    def test_partial_no_device_width(self):
        self.assertFalse(ctr.has_viewport('<meta name="viewport" content="initial-scale=1">'))


class RatchetTests(unittest.TestCase):
    def test_increase_blocks(self):
        ok, msgs = ctr.ratchet_verdict({"暗夜:3位hex": 5}, {"暗夜:3位hex": 4})
        self.assertFalse(ok)
        self.assertTrue(msgs)

    def test_equal_passes(self):
        ok, _ = ctr.ratchet_verdict({"暗夜:3位hex": 4}, {"暗夜:3位hex": 4})
        self.assertTrue(ok)

    def test_decrease_passes_with_hint(self):
        ok, msgs = ctr.ratchet_verdict({"暗夜:3位hex": 2}, {"暗夜:3位hex": 4})
        self.assertTrue(ok)
        self.assertTrue(any("下降" in m for m in msgs))

    def test_new_key_defaults_zero(self):
        ok, _ = ctr.ratchet_verdict({"新类别": 1}, {})
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
