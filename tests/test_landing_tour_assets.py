"""着陆页产品导览(landing-tour)资产守门:三件套齐全、进打包清单、四语键对齐。

导览 = 登录页后接 5 屏卖点横向滑动(2026-07-06 上线)。这里不跑浏览器,只锁三条
机械事实:文件在、bundler 清单没漏(漏了 = prod 静默缺功能)、四语文案键集合一致
(缺键 = 某语言整块空白)。视觉验收走真浏览器 E2E,不在单测层。
"""

import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANDING = ROOT / "static" / "landing"
TOUR_FILES = [
    "landing-tour.css",
    "landing-tour-phone.css",
    "landing-tour-cards.css",
    "landing-tour-i18n.js",
    "landing-tour-scenes.js",
    "landing-tour.js",
]


class LandingTourAssetTest(unittest.TestCase):
    def test_files_exist(self):
        for name in TOUR_FILES:
            self.assertTrue((LANDING / name).is_file(), f"missing static/landing/{name}")

    def test_css_in_bundle_manifest_ordered(self):
        manifest = (ROOT / "scripts" / "build-home-css.mjs").read_text(encoding="utf-8")
        positions = [
            manifest.find(f"landing/{n}")
            for n in ["landing-tour.css", "landing-tour-phone.css", "landing-tour-cards.css"]
        ]
        self.assertTrue(all(p >= 0 for p in positions), "tour css missing from landing bundle")
        self.assertEqual(
            positions, sorted(positions), "tour css order must be base -> phone -> cards"
        )

    def test_source_files_under_500_lines(self):
        for name in TOUR_FILES:
            lines = (LANDING / name).read_text(encoding="utf-8").count("\n")
            self.assertLessEqual(lines, 500, f"static/landing/{name} = {lines} 行,超 500 铁律")

    def test_js_in_bundle_manifest_ordered(self):
        manifest = (ROOT / "scripts" / "build-home-js.mjs").read_text(encoding="utf-8")
        positions = [
            manifest.find(f"landing/{n}")
            for n in ["landing-tour-i18n.js", "landing-tour-scenes.js", "landing-tour.js"]
        ]
        self.assertTrue(all(p >= 0 for p in positions), "tour js missing from landing bundle")
        self.assertEqual(
            positions, sorted(positions), "tour js bundle order must be i18n -> scenes -> main"
        )

    def test_i18n_four_langs_same_keys(self):
        # node 里真执行字典文件再吐 JSON,比正则数键可靠
        script = (
            "global.window={};"
            "require(process.argv[1]);"
            "const d=global.window.PearnlyTourI18N;"
            "console.log(JSON.stringify(Object.fromEntries("
            "Object.entries(d).map(([k,v])=>[k,[Object.keys(v).sort(),Object.keys(v.chat).sort()]]))))"
        )
        out = subprocess.run(
            ["node", "-e", script, str(LANDING / "landing-tour-i18n.js")],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        keysets = json.loads(out.stdout)
        self.assertEqual(sorted(keysets), ["en", "ja", "th", "zh"])
        for lang in ("zh", "en", "ja"):
            self.assertEqual(keysets["th"], keysets[lang], f"i18n keys diverge: th vs {lang}")

    def test_login_shell_cache_busted_past_v13(self):
        shell = (ROOT / "login.html").read_text(encoding="utf-8")
        versions = [int(v) for v in re.findall(r"/static/dist/landing\.(?:css|js)\?v=(\d+)", shell)]
        self.assertEqual(len(versions), 2)
        self.assertTrue(all(v >= 14 for v in versions), f"?v not bumped for tour ship: {versions}")


if __name__ == "__main__":
    unittest.main()
