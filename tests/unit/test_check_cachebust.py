# -*- coding: utf-8 -*-
"""缓存破机械闸判定核测试(scripts/check_cachebust.py)。

锁纯判定函数 find_violations / extract_vparam:产物变则源 HTML 指纹必 bump,否则违规。
不碰 git(main() 的 git 接线由 CI 真跑覆盖),只验判定逻辑本身。"""

import importlib.util
import unittest
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "check_cachebust",
    Path(__file__).resolve().parent.parent.parent / "scripts" / "check_cachebust.py",
)
cachebust = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cachebust)

BUNDLE = "static/dist/main.js"
HTML = "home.html"


def _html(v: str) -> str:
    return f'<script type="module" src="/static/dist/main.js?v={v}"></script>'


class ExtractVparamTests(unittest.TestCase):
    def test_extracts_numeric_fingerprint(self):
        self.assertEqual(cachebust.extract_vparam(_html("11856008"), "dist/main.js"), "11856008")

    def test_extracts_alnum_fingerprint(self):
        self.assertEqual(cachebust.extract_vparam(_html("a1b2c3"), "dist/main.js"), "a1b2c3")

    def test_missing_ref_returns_none(self):
        self.assertIsNone(
            cachebust.extract_vparam("<script src='/other.js'></script>", "dist/main.js")
        )


class FindViolationsTests(unittest.TestCase):
    def test_bundle_unchanged_no_check(self):
        # 产物没进本次 diff → 不检查,哪怕指纹一样也放行。
        fails = cachebust.find_violations(
            changed={HTML}, base_html={HTML: _html("1")}, head_html={HTML: _html("1")}
        )
        self.assertEqual(fails, [])

    def test_bundle_changed_but_vparam_not_bumped_fails(self):
        fails = cachebust.find_violations(
            changed={BUNDLE, HTML},
            base_html={HTML: _html("1")},
            head_html={HTML: _html("1")},
        )
        self.assertEqual(len(fails), 1)
        self.assertIn("没 bump", fails[0])

    def test_bundle_changed_and_vparam_bumped_passes(self):
        fails = cachebust.find_violations(
            changed={BUNDLE, HTML},
            base_html={HTML: _html("1")},
            head_html={HTML: _html("2")},
        )
        self.assertEqual(fails, [])

    def test_bundle_changed_html_untouched_fails(self):
        # 只改产物、没碰 home.html → 两端指纹必然相同 → 违规。
        fails = cachebust.find_violations(
            changed={BUNDLE},
            base_html={HTML: _html("1")},
            head_html={HTML: _html("1")},
        )
        self.assertEqual(len(fails), 1)


if __name__ == "__main__":
    unittest.main()
