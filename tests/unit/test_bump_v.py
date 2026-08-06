# -*- coding: utf-8 -*-
"""bump_v 破缓存工具守门(scripts/bump_v.py)。

tmp 文件夹造 CRLF 样本:三处一致(pos.html pos.js ?v == 两个 SW const V)、CRLF 原样保留、
--set 指哪打哪、--dry-run 不落盘。不碰仓库真文件(bump 对象是路径参数化后的 root)。
"""

import tempfile
import unittest
from pathlib import Path

from scripts.bump_v import TARGETS, _SW_FILES, bump


def _crlf(text: str) -> bytes:
    return text.replace("\n", "\r\n").encode("utf-8")


def _make_root() -> Path:
    root = Path(tempfile.mkdtemp())
    home = _crlf(
        '<link rel="stylesheet" href="/static/dist/home.css?v=7">\n'
        '<script src="/static/dist/pre.js?v=4" defer></script>\n'
        '<script type="module" src="/static/dist/main.js?v=9"></script>\n'
        '<script src="/static/dist/post.js?v=5" defer></script>\n'
        '<script src="/static/i18n-data.js?v=9"></script>\n'
    )
    (root / "home.html").write_bytes(home)
    pos_html = _crlf(
        '<link rel="stylesheet" href="/static/dist/pos.css?v=3">\n'
        '<script src="/static/dist/pos.js?v=5"></script>\n'
    )
    (root / "static" / "pos").mkdir(parents=True)
    (root / "static" / "pos" / "pos.html").write_bytes(pos_html)
    for sw in _SW_FILES:
        p = root / sw
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(_crlf("const V = '5';\nconst CACHE = 'pearnly-v' + V;\n"))
    ai = _crlf(
        '<link rel="stylesheet" href="/static/dist/ai.css?v=79">\n'
        '<script src="/static/dist/ai.js?v=79"></script>\n'
    )
    (root / "static" / "ai").mkdir(parents=True)
    (root / "static" / "ai" / "ai.html").write_bytes(ai)
    return root


class BumpHomeTests(unittest.TestCase):
    def test_asset_limited_bump_only_touches_named_asset(self):
        root = _make_root()
        bump(root, target="home", assets={"main.js"})
        html = (root / "home.html").read_text(encoding="utf-8")
        self.assertIn("/static/dist/main.js?v=10", html)
        self.assertIn("/static/i18n-data.js?v=9", html)  # 没点名的不动
        self.assertIn("/static/dist/home.css?v=7", html)

    def test_no_asset_bumps_all(self):
        root = _make_root()
        bump(root, target="home")
        html = (root / "home.html").read_text(encoding="utf-8")
        self.assertIn("/static/dist/main.js?v=10", html)
        self.assertIn("/static/i18n-data.js?v=10", html)
        self.assertIn("/static/dist/home.css?v=8", html)

    def test_set_pins_exact_value(self):
        root = _make_root()
        bump(root, target="home", assets={"main.js"}, set_v=12060099)
        self.assertIn(
            "/static/dist/main.js?v=12060099", (root / "home.html").read_text(encoding="utf-8")
        )

    def test_dry_run_writes_nothing(self):
        root = _make_root()
        before = (root / "home.html").read_bytes()
        changed = bump(root, target="home", assets={"main.js"}, dry_run=True)
        self.assertEqual(changed, 0)
        self.assertEqual((root / "home.html").read_bytes(), before)


class BumpPosTests(unittest.TestCase):
    def test_pos_js_three_way_consistent(self):
        root = _make_root()
        bump(root, target="pos", assets={"pos.js"})
        pos_html = (root / "static" / "pos" / "pos.html").read_text(encoding="utf-8")
        # 三处现值 max 是 5 → +1 = 6,pos.js 与两个 SW 全对齐
        self.assertIn("/static/dist/pos.js?v=6", pos_html)
        for sw in _SW_FILES:
            self.assertIn("const V = '6';", (root / sw).read_text(encoding="utf-8"))
        # pos.css 不是 pos.js,不被连带
        self.assertIn("/static/dist/pos.css?v=3", pos_html)

    def test_pos_css_does_not_touch_sw(self):
        root = _make_root()
        bump(root, target="pos", assets={"pos.css"})
        pos_html = (root / "static" / "pos" / "pos.html").read_text(encoding="utf-8")
        self.assertIn("/static/dist/pos.css?v=4", pos_html)
        for sw in _SW_FILES:
            self.assertIn("const V = '5';", (root / sw).read_text(encoding="utf-8"))

    def test_crlf_preserved_after_bump(self):
        root = _make_root()
        bump(root, target="pos")
        for rel in ("static/pos/pos.html", *_SW_FILES):
            b = (root / rel).read_bytes()
            self.assertEqual(b.count(b"\r\n"), b.count(b"\n"), f"{rel} 混入 LF")
            self.assertIn(b"\r\n", b, f"{rel} 丢 CRLF")


class BumpAiTests(unittest.TestCase):
    def test_ai_bumps_js_and_css(self):
        root = _make_root()
        bump(root, target="ai")
        ai = (root / "static" / "ai" / "ai.html").read_text(encoding="utf-8")
        self.assertIn("/static/dist/ai.js?v=80", ai)
        self.assertIn("/static/dist/ai.css?v=80", ai)


class BadInputTests(unittest.TestCase):
    def test_unknown_asset_raises(self):
        root = _make_root()
        with self.assertRaises(SystemExit):
            bump(root, target="home", assets={"bogus.js"})

    def test_unknown_target_raises(self):
        root = _make_root()
        with self.assertRaises(KeyError):
            bump(root, target="bogus")

    def test_asset_name_must_exist_in_target(self):
        # ai target 不认 home 的资产名
        root = _make_root()
        with self.assertRaises(SystemExit):
            bump(root, target="ai", assets={"main.js"})

    def test_targets_table_covers_pos_sw_contract(self):
        # 三处一致契约钉在常量上:pos target 的 SW 列表不许悄悄改名
        self.assertIn("static/pos/pos-sw.js", _SW_FILES)
        self.assertIn("static/pos/cashier-sw.js", _SW_FILES)
        self.assertIn("pos.js", TARGETS["pos"]["assets"])


if __name__ == "__main__":
    unittest.main()
