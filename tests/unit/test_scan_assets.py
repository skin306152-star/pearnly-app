#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_scan_assets.py

扫码地基的资产与接线契约(静态断言,不跑浏览器)。行为归 test_scan_wedge_pure.py 与
test_scan_engine_pure.py;这里只守「东西真的在该在的地方」——上一次栽在这上头的教训是
「验收脚本全绿但产品里根本没那个东西」。

钉死四组:
  1. vendor:zxing 源 + LICENSE + version + README 齐,Apache-2.0 原文随仓库分发。
  2. 产物:dist/zxing.js 与 dist/scan.js 存在、非空、许可头在。
  3. 分层:常驻两件(loader/wedge)真在 dist/pos.js 与 dist/pre.js 里;摄像头两件与 ZXing
     真【不在】首屏 bundle 里(不然「懒加载」只是注释里的说法)。
  4. 源码硬约束:单文件 <500 行、iOS 的 playsinline+muted、关闭时停掉每条 track、0 console.log。
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCAN_DIR = PROJECT_ROOT / "static" / "scan"
VENDOR_DIR = PROJECT_ROOT / "static" / "vendor" / "zxing"
DIST = PROJECT_ROOT / "static" / "dist"
BUILD_SCRIPT = PROJECT_ROOT / "scripts" / "build-home-js.mjs"

RESIDENT = ("scan-loader.js", "scan-wedge.js")  # 必须首屏就在(枪可能一开页面就被扫)
LAZY = ("scan-camera.js", "scan-errors.js", "scan-track.js", "scan-zxing-shim.js")  # 点了扫码才拉
SCAN_SOURCES = RESIDENT + LAZY
FIRST_PAINT_BUNDLES = ("pos.js", "pre.js")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


class VendorProvenanceTests(unittest.TestCase):
    def test_library_license_and_version_all_present(self):
        for name in ("zxing-library.js", "LICENSE", "version", "README.md"):
            f = VENDOR_DIR / name
            self.assertTrue(f.is_file(), f"static/vendor/zxing/{name} 缺失")
            self.assertGreater(f.stat().st_size, 0, f"{name} 是空文件")

    def test_license_is_apache_2_full_text(self):
        text = _read(VENDOR_DIR / "LICENSE")
        self.assertIn("Apache License", text)
        self.assertIn("Version 2.0, January 2004", text)
        self.assertIn("TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION", text)

    def test_readme_states_source_version_and_why_vendored(self):
        readme = _read(VENDOR_DIR / "README.md")
        version = _read(VENDOR_DIR / "version").strip()
        self.assertIn("github.com/zxing-js/library", readme)
        self.assertIn(version, readme, "README 里的版本号跟 version 文件不一致")
        self.assertIn("Apache-2.0", readme)
        # 为什么不走 npm/CDN:CSP 只允许 self + 收银台要能离线。理由丢了,下个窗口就会想「改成 CDN 吧」。
        self.assertIn("CSP", readme)
        self.assertIn("离线", readme)


class BuildProductTests(unittest.TestCase):
    def test_lazy_products_exist_and_non_empty(self):
        for name in ("zxing.js", "scan.js"):
            f = DIST / name
            self.assertTrue(
                f.is_file(), f"static/dist/{name} 未构建 · 跑 node scripts/build-home-js.mjs"
            )
            self.assertGreater(f.stat().st_size, 1000, f"static/dist/{name} 太小,像是没打进东西")

    def test_zxing_product_keeps_license_header(self):
        # Apache-2.0 要求分发时保留版权与许可声明;minify 默认会把注释全删掉。
        head = _read(DIST / "zxing.js")[:400]
        self.assertIn("Apache-2.0", head)
        self.assertIn("zxing-js/library", head)
        self.assertIn(_read(VENDOR_DIR / "version").strip(), head)

    def test_zxing_product_has_no_dangling_sourcemap_ref(self):
        # 上游源码尾巴上指向 index.js.map,那个文件没随仓库分发 → 浏览器每次都白发一个 404。
        self.assertNotIn("sourceMappingURL", _read(DIST / "zxing.js"))

    def test_zxing_product_is_really_the_library(self):
        code = _read(DIST / "zxing.js")
        for symbol in (
            "MultiFormatReader",
            "HTMLCanvasElementLuminanceSource",
            "NotFoundException",
        ):
            self.assertIn(symbol, code, f"dist/zxing.js 里找不到 {symbol}")

    def test_scan_product_carries_camera_engine_not_the_library(self):
        code = _read(DIST / "scan.js")
        self.assertIn("PearnlyScanCamera", code)
        self.assertIn("PearnlyScanZXing", code)
        # ZXing 本体必须留在自己那个产物里 —— 混进来 scan.js 就从 7KB 变成 350KB,
        # 「原生 BarcodeDetector 能用时一个字节都不拉 ZXing」的承诺随之作废。
        self.assertNotIn("HTMLCanvasElementLuminanceSource = ", code)
        self.assertLess(len(code), 60_000, "dist/scan.js 体积异常 · 像是把 ZXing 一起打进来了")


class BundleWiringTests(unittest.TestCase):
    def test_every_scan_source_is_in_the_build_manifest(self):
        manifest = _read(BUILD_SCRIPT)
        for name in SCAN_SOURCES:
            self.assertIn(f"scan/{name}", manifest, f"scan/{name} 不在 build-home-js.mjs 清单")

    def test_resident_layer_shipped_in_both_first_paint_bundles(self):
        # 这条是「假绿第三种」的直接反证:注释说进了 bundle,不如去产物里查一眼。
        for bundle in FIRST_PAINT_BUNDLES:
            code = _read(DIST / bundle)
            self.assertIn("PearnlyScanWedge", code, f"dist/{bundle} 里没有条码枪楔子")
            self.assertIn("ensureLoaded", code, f"dist/{bundle} 里没有摄像头懒加载入口")

    def test_camera_layer_not_in_first_paint_bundles(self):
        for bundle in FIRST_PAINT_BUNDLES:
            code = _read(DIST / bundle)
            self.assertNotIn("PearnlyScanZXing", code, f"dist/{bundle} 把摄像头解码层打进了首屏")
            self.assertNotIn("HTMLCanvasElementLuminanceSource", code)

    def test_lazy_layer_declared_only_in_the_lazy_product(self):
        # 分层写在构建清单上要能被查:懒加载那两件只许出现在 dist/scan.js 那条 files 里。
        manifest = _read(BUILD_SCRIPT)
        block = manifest[manifest.index("out: 'static/dist/scan.js'") :]
        block = block[: block.index("],")]
        for name in LAZY:
            self.assertIn(f"scan/{name}", block, f"scan/{name} 不在 dist/scan.js 的 files 里")
        for name in RESIDENT:
            self.assertNotIn(f"scan/{name}", block, f"常驻件 scan/{name} 被塞进懒加载产物了")

    def test_wedge_precedes_cashier_logic_in_pos_bundle(self):
        # 楔子要在收银台逻辑之前挂上,否则页面刚开那一下扫的码没人接。断在【产物】上而不是
        # 清单数组上:清单可以用展开/常量写,产物里的先后才是真正的执行时序。
        code = _read(DIST / "pos.js")
        cashier_marker = "posui.scan.title"  # 只出现在 pos-cashier.js(openScanPad 的标题)
        self.assertIn(cashier_marker, code, "pos-cashier.js 的锚点没了 · 判据失效比断言失败更危险")
        self.assertLess(
            code.index("PearnlyScanWedge"),
            code.index(cashier_marker),
            "dist/pos.js 里楔子排在收银台逻辑之后了",
        )

    def test_lazy_products_guarded_by_cachebust_gate(self):
        # 懒加载产物不写在 HTML 里,漏进 CACHE_BUST_DIRS 就永远报绿(已犯三次)。
        gate = _read(PROJECT_ROOT / "scripts" / "check_cachebust.py")
        for name in ("static/dist/scan.js", "static/dist/zxing.js"):
            self.assertIn(name, gate, f"{name} 没进 check_cachebust 的清单")


class SourceContractTests(unittest.TestCase):
    def test_all_files_under_line_ceiling(self):
        for name in SCAN_SOURCES:
            lines = _read(SCAN_DIR / name).count("\n") + 1
            self.assertLess(lines, 500, f"static/scan/{name} {lines} 行 · 铁律单文件 <500")

    def test_no_console_log_left_behind(self):
        for name in SCAN_SOURCES:
            self.assertNotRegex(
                _read(SCAN_DIR / name),
                r"\bconsole\.log\s*\(",
                f"static/scan/{name} 有 console.log 残留",
            )

    def test_video_element_gets_playsinline_and_muted(self):
        # 少任何一个,iOS Safari 就把预览抢成全屏播放器,弹窗被顶掉 —— iOS 上必踩。
        src = _read(SCAN_DIR / "scan-camera.js")
        self.assertRegex(src, r"setAttribute\('playsinline'")
        self.assertRegex(src, r"setAttribute\('muted'")
        self.assertRegex(src, r"video\.muted\s*=\s*true")

    def test_stop_releases_every_track(self):
        # 漏一条 track = 相机灯一直亮、别的应用再也打不开相机。
        self.assertRegex(
            _read(SCAN_DIR / "scan-camera.js"),
            r"getTracks\(\)\.forEach\(function \(t\) \{\s*t\.stop\(\);",
        )

    def test_engine_watches_the_track_it_decodes_on_both_paths(self):
        # 相机被系统收走之后 <video> 停在最后一帧(readyState 仍是 4、videoWidth 仍是 640),
        # videoReady() 于是恒真 —— 不盯轨道就会一直解同一张死图,屏上照旧说「对准条码」。
        # 两条路缺一不可,所以两条都钉:事件那条管「立刻」,轮询那条管「stop() 不发事件」
        # (页面外部收走轨道走的正是它,只订事件对整类全盲)。行为归 test_scan_camera_runtime。
        engine = _read(SCAN_DIR / "scan-camera.js")
        self.assertIn("shell.watchTracks(", engine, "引擎没挂轨道生死看门人")
        self.assertRegex(engine, r"if \(lost\(token\)\) return;", "tick 里没有每拍轮询那一侧")
        watch = _read(SCAN_DIR / "scan-errors.js")
        self.assertIn("addEventListener('ended'", watch, "事件那一侧没订")
        self.assertIn("readyState !== 'ended'", watch, "轮询那一侧没判 readyState")
        self.assertIn("visibilityState", watch, "后台期间仍在给冻结画面计时 · 回来会误判相机坏")

    def test_start_has_a_timeout_not_a_busy_wait(self):
        # Odoo 那个 FIXME 的位置:它 `while (!ready) await delay(10)` 死等。三把尺子各管一段:
        # 权限弹窗(人的时间)/ 相机出帧 / 解码器下载 —— 共用一把就会答非所问。
        src = _read(SCAN_DIR / "scan-camera.js")
        for knob in ("grantTimeoutMs", "startTimeoutMs", "decoderTimeoutMs"):
            self.assertIn(knob, src, f"缺 {knob} · 这一段会变成死等")
        self.assertIn("withTimeout", src)

    def test_play_is_inside_the_start_timeout(self):
        # play() 在「拿到 stream 却永远不出帧」时不会 settle(captureStream(0) 可复现),
        # 只给等帧那段加超时等于还是死等 —— 必须整段包在 withTimeout 里。
        src = _read(SCAN_DIR / "scan-camera.js")
        self.assertRegex(src, r"function cameraReady\([\s\S]{0,400}?video\.play\(\)")
        self.assertRegex(src, r"withTimeout\(cameraReady\(token\), cfg\.startTimeoutMs")

    def test_zxing_lazy_url_points_at_dist(self):
        # webhook 不可靠拾取新增的 static/ 根文件,dist/ 已实证可靠 —— 运行时拉的必须在 dist。
        src = _read(SCAN_DIR / "scan-camera.js")
        self.assertIn("'/static/dist/zxing.js'", src)
        self.assertNotIn("/static/vendor/", src, "运行时不能直接拉 vendor 源(未压缩且部署不保证)")

    def test_try_harder_hint_enabled(self):
        # 不开 TRY_HARDER 就读不了横躺 90° 的条码(zxing-js/library#291)。
        self.assertIn("TRY_HARDER", _read(SCAN_DIR / "scan-zxing-shim.js"))

    def test_sources_are_lf_only(self):
        # bundle 是把各文件 minify 后用 `;\n` 拼起来的;混进 CRLF 只会制造纯行尾的假 diff。
        for name in SCAN_SOURCES:
            raw = (SCAN_DIR / name).read_bytes()
            self.assertNotIn(b"\r\n", raw, f"static/scan/{name} 有 CRLF 行尾")

    def test_error_keys_and_ui_keys_share_one_namespace(self):
        # 引擎不翻译,只回 i18n 键;两个 SPA 各自的字典里放同名键。键名散了就会有一档漏翻译。
        keys = set(re.findall(r"'(bscan\.[\w.]+)'", _read(SCAN_DIR / "scan-errors.js")))
        self.assertGreaterEqual(len(keys), 8, f"bscan.* 键抓取异常: {keys}")

    def test_error_module_loads_before_the_engine(self):
        # 引擎在【加载期】就把 scanError/withTimeout 抓进闭包 —— 顺序反了不是少一个函数,
        # 是整个 dist/scan.js 加载即抛。清单和产物两处都验:清单可以用变量拼,产物里的
        # 先后才是真正的执行时序(同 test_wedge_precedes_cashier_logic_in_pos_bundle)。
        manifest = _read(BUILD_SCRIPT)
        block = manifest[manifest.index("out: 'static/dist/scan.js'") :]
        block = block[: block.index("],")]
        self.assertLess(
            block.index("scan/scan-errors.js"),
            block.index("scan/scan-camera.js"),
            "构建清单里 scan-errors.js 排在引擎之后了",
        )
        code = _read(DIST / "scan.js")
        anchor = "NotReadableError"  # 只出现在 scan-errors.js 的 MEDIA_ERRORS 表
        self.assertIn(anchor, code, "scan-errors.js 的锚点没了 · 判据失效比断言失败更危险")
        self.assertLess(
            code.index(anchor),
            code.index("cropRatio"),  # 只出现在 scan-camera.js
            "dist/scan.js 里错误分档排在引擎之后了",
        )

    def test_engine_refuses_to_start_without_the_error_module(self):
        # 硬 guard 不是装饰:少了错误分档就无声跑起来,第一次报错时 scanError 是 undefined,
        # 店员看到的是白屏而不是「相机被别的应用占着」。
        src = _read(SCAN_DIR / "scan-camera.js")
        self.assertRegex(src, r"typeof shell\.scanError !== 'function'")
        self.assertIn("scan-errors.js", src, "抛的话里没说缺的是哪个文件")

    def test_engine_does_not_call_a_translator_itself(self):
        # 翻译函数由调用方传进来(POS 是 POS.t,主站是全局 t)。引擎里写死任何一个都会让
        # 另一个 SPA 拿到裸键。
        src = _read(SCAN_DIR / "scan-camera.js")
        self.assertNotRegex(src, r"\bPOS\.t\(")
        self.assertNotRegex(src, r"\bwindow\.t\(")
        self.assertIn("typeof o.t === 'function'", src)


if __name__ == "__main__":
    unittest.main()
