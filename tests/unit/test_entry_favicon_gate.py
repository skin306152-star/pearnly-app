# -*- coding: utf-8 -*-
"""入口壳品牌 favicon 契约 —— dms / erp 必须引用统一品牌图标。

防回归:任何入口壳换掉 favicon 路径或漏掉 apple-touch-icon 即红。
纯文件解析,不起服务、不碰库。
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

SHELLS = {
    "dms": _REPO / "static" / "dms" / "dms.html",
    "erp": _REPO / "static" / "erp" / "erp.html",
}

EXPECTED_ICO = "/static/brand/favicon.ico?v=1"
EXPECTED_PNG = "/static/brand/favicon-32.png?v=1"
EXPECTED_APPLE = "/static/brand/apple-touch-icon-180.png?v=1"


def _hrefs(html: str, rel: str) -> list[str]:
    pat = rf'<link[^>]*\brel="{re.escape(rel)}"[^>]*>'
    return re.findall(pat, html, re.IGNORECASE)


def _extract_href(tag: str) -> str:
    m = re.search(r'href=["\']([^"\']+)["\']', tag)
    return m.group(1) if m else ""


class EntryFaviconGateTests(unittest.TestCase):
    def test_all_shells_exist(self):
        for name, path in SHELLS.items():
            self.assertTrue(path.exists(), f"{name} shell missing: {path}")

    def test_favicon_ico_present(self):
        for name, path in SHELLS.items():
            html = path.read_text(encoding="utf-8")
            tags = _hrefs(html, "icon")
            hrefs = [_extract_href(t) for t in tags]
            self.assertIn(
                EXPECTED_ICO,
                hrefs,
                f"{name}: missing favicon.ico ({hrefs})",
            )

    def test_favicon_png_32_present(self):
        for name, path in SHELLS.items():
            html = path.read_text(encoding="utf-8")
            tags = _hrefs(html, "icon")
            hrefs = [_extract_href(t) for t in tags]
            self.assertIn(
                EXPECTED_PNG,
                hrefs,
                f"{name}: missing favicon-32.png ({hrefs})",
            )

    def test_apple_touch_icon_present(self):
        for name, path in SHELLS.items():
            html = path.read_text(encoding="utf-8")
            tags = _hrefs(html, "apple-touch-icon")
            hrefs = [_extract_href(t) for t in tags]
            self.assertIn(
                EXPECTED_APPLE,
                hrefs,
                f"{name}: missing apple-touch-icon ({hrefs})",
            )


if __name__ == "__main__":
    unittest.main()
