#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_scan_engine_pure.py

摄像头扫码引擎三件套的行为守门,真 node 子进程跑源文件:
  scan-loader.js      能力探针 + 懒加载 URL 带页面指纹
  scan-camera.js      错误分档(每档一个 i18n 键 + 该不该给重试按钮)+ 零售格式集
  scan-zxing-shim.js  用【真的 dist/zxing.js】解一张合成 EAN-13 位图

最后那条是这个文件的重点。合成位图 + 真产物 = 一条真解码闭环:它同时挡住三种失效 ——
  · 打包把库压坏了(minify 改类名 → 库内异常识别失灵);
  · shim 的 hints/格式表接错(POSSIBLE_FORMATS 写错就一个码都读不出);
  · 「这一帧没读出码」被当成硬错误往上抛(每秒好几帧,店员会被错误提示糊满屏)。
只 grep 文件里有没有 'TRY_HARDER' 是验不出这些的(闸报绿 ≠ 闸看过)。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import PROJECT_ROOT, _run_node

SCAN_DIR = PROJECT_ROOT / "static" / "scan"
LOADER = SCAN_DIR / "scan-loader.js"
CAMERA = SCAN_DIR / "scan-camera.js"
SHIM = SCAN_DIR / "scan-zxing-shim.js"
ZXING_DIST = PROJECT_ROOT / "static" / "dist" / "zxing.js"


def _jp(path) -> str:
    return json.dumps(str(path))


# scan-camera.js 加载期就要求 scan-loader.js 已在(它只可能被 ensureLoaded 拉进来),
# 这里给一个最小外壳桩;不给 document,因为被验的都是不碰 DOM 的纯判定。
_CAMERA_PRELUDE = f"""
    global.PearnlyScanCamera = {{
        loadScript: () => Promise.resolve(),
        unsupportedReason: () => null,
    }};
    const cam = require({_jp(CAMERA)});
    const out = (o) => process.stdout.write(JSON.stringify(o));
"""

# ── 合成 EAN-13 位图 ────────────────────────────────────────────────────
# 桩 canvas 只要满足 ZXing 的 HTMLCanvasElementLuminanceSource 实际用到的形状:
# {width, height, getContext('2d').getImageData()} → {data: RGBA}。不需要 jsdom / node-canvas。
_EAN_HARNESS = r"""
    const L = ['0001101','0011001','0010011','0111101','0100011',
               '0110001','0101111','0111011','0110111','0001011'];
    const G = ['0100111','0110011','0011011','0100001','0011101',
               '0111001','0000101','0010001','0001001','0010111'];
    const R = L.map((s) => s.replace(/[01]/g, (c) => (c === '0' ? '1' : '0')));
    const PARITY = ['LLLLLL','LLGLGG','LLGGLG','LLGGGL','LGLLGG',
                    'LGGLLG','LGGGLL','LGLGLG','LGLGGL','LGGLGL'];

    function ean13Modules(code) {
        const d = code.split('').map(Number);
        const parity = PARITY[d[0]];
        let bits = '101';
        for (let i = 0; i < 6; i++) bits += parity[i] === 'L' ? L[d[i + 1]] : G[d[i + 1]];
        bits += '01010';
        for (let i = 7; i < 13; i++) bits += R[d[i]];
        return bits + '101';
    }

    // quiet = 左右静区模块数(EAN-13 规范要求,没有静区解码器认不出边界)
    function bitmap(bits, scale, height, quiet) {
        const width = (bits.length + quiet * 2) * scale;
        const data = new Uint8ClampedArray(width * height * 4);
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const mod = Math.floor(x / scale) - quiet;
                const v = mod >= 0 && mod < bits.length && bits[mod] === '1' ? 0 : 255;
                const i = (y * width + x) * 4;
                data[i] = v; data[i + 1] = v; data[i + 2] = v; data[i + 3] = 255;
            }
        }
        return { width, height, getContext: () => ({ getImageData: () => ({ data }) }) };
    }
"""


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class LoaderProbeTests(unittest.TestCase):
    """能力探针必须在首屏可答,且三档分得开 —— Odoo 在非 HTTPS 下让按钮静默消失,
    店员只觉得「功能没了」;这里每档都有自己的错误码可以说出人话。"""

    def _probe(self, secure: str, nav: str) -> dict:
        # node 自带的 navigator 是只读 getter,直接赋值悄悄不生效(会把用例做成假绿),
        # 必须 defineProperty 覆盖。
        return _run_node(f"""
            {secure}
            Object.defineProperty(globalThis, 'navigator', {{
                value: {nav}, configurable: true, writable: true,
            }});
            const shell = require({_jp(LOADER)});
            process.stdout.write(JSON.stringify({{
                reason: shell.unsupportedReason(),
                supported: shell.isSupported(),
            }}));
            """)

    _CAM = "{ mediaDevices: { getUserMedia: () => {} } }"

    def test_insecure_context_is_its_own_reason(self):
        got = self._probe("global.isSecureContext = false;", self._CAM)
        self.assertEqual(got, {"reason": "insecure_context", "supported": False})

    def test_missing_getusermedia_reports_no_camera_api(self):
        got = self._probe("global.isSecureContext = true;", "{}")
        self.assertEqual(got, {"reason": "no_camera_api", "supported": False})

    def test_secure_context_with_camera_api_is_supported(self):
        got = self._probe("global.isSecureContext = true;", self._CAM)
        self.assertEqual(got, {"reason": None, "supported": True})

    def test_undefined_secure_context_is_not_treated_as_insecure(self):
        # 读不到 ≠ 不安全。把 undefined 当 false 会在能扫的机器上把功能关掉。
        got = self._probe("", self._CAM)
        self.assertEqual(got["reason"], None)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class LoaderFingerprintTests(unittest.TestCase):
    """懒加载的 URL 必须带页面指纹:URL 不变 = CDN 一直发旧的,文件是新的也没人看得到
    (2026-07-26 教程 JSON 真事故)。"""

    def _load(self, scripts: str) -> dict:
        return _run_node(f"""
            const injected = [];
            global.document = {{
                querySelectorAll: () => {scripts},
                createElement: () => {{
                    const el = {{ remove: () => {{}} }};
                    injected.push(el);
                    // 注入后立刻当成功回调,免得 promise 悬着
                    setTimeout(() => el.onload && el.onload(), 0);
                    return el;
                }},
                head: {{ appendChild: () => {{}} }},
            }};
            const shell = require({_jp(LOADER)});
            shell.loadScript('/static/dist/zxing.js').then(() => {{
                process.stdout.write(JSON.stringify({{
                    version: shell.assetVersion(),
                    src: injected[0].src,
                    injected: injected.length,
                }}));
            }});
            """)

    def test_lazy_url_carries_page_bundle_fingerprint(self):
        got = self._load("[{ src: 'https://x/static/dist/pos.js?v=11911201' }]")
        self.assertEqual(got["version"], "11911201")
        self.assertEqual(got["src"], "/static/dist/zxing.js?v=11911201")

    def test_no_fingerprint_on_page_leaves_url_clean(self):
        # 抠不到就别挂空的 ?v= 污染 URL(单测页、直开静态文件)。
        got = self._load("[]")
        self.assertEqual(got["version"], "")
        self.assertEqual(got["src"], "/static/dist/zxing.js")

    def test_same_url_injected_once(self):
        got = _run_node(f"""
            const injected = [];
            global.document = {{
                querySelectorAll: () => [],
                createElement: () => {{
                    const el = {{ remove: () => {{}} }};
                    injected.push(el);
                    setTimeout(() => el.onload && el.onload(), 0);
                    return el;
                }},
                head: {{ appendChild: () => {{}} }},
            }};
            const shell = require({_jp(LOADER)});
            Promise.all([
                shell.loadScript('/static/dist/zxing.js'),
                shell.loadScript('/static/dist/zxing.js'),
            ]).then(() => process.stdout.write(JSON.stringify({{ injected: injected.length }})));
            """)
        self.assertEqual(got["injected"], 1, "同一个懒加载产物被注入了两次")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class CameraErrorTaxonomyTests(unittest.TestCase):
    def test_every_error_code_has_its_own_i18n_key(self):
        got = _run_node(_CAMERA_PRELUDE + """
            out({ keys: cam.ERROR_KEYS });
            """)
        keys = got["keys"]
        expected = {
            "insecure_context",
            "no_camera_api",
            "permission_denied",
            "no_camera",
            "camera_busy",
            "timeout",
            "decoder_unavailable",
            "unknown",
        }
        self.assertEqual(set(keys), expected)
        self.assertEqual(len(set(keys.values())), len(expected), "有两档共用同一个 i18n 键")
        for code, key in keys.items():
            self.assertTrue(key.startswith("bscan."), f"{code} 的键不在 bscan.* 命名空间")

    def test_retryable_only_where_retrying_can_help(self):
        got = _run_node(_CAMERA_PRELUDE + """
            const r = {};
            Object.keys(cam.ERROR_KEYS).forEach((c) => { r[c] = cam.scanError(c).retryable; });
            out(r);
            """)
        self.assertTrue(got["timeout"])
        self.assertTrue(got["camera_busy"])
        self.assertTrue(got["decoder_unavailable"])
        # 没有摄像头 / 非 HTTPS / 权限要去系统设置改 —— 给重试按钮是耍人
        self.assertFalse(got["no_camera"])
        self.assertFalse(got["insecure_context"])
        self.assertFalse(got["permission_denied"])

    def test_unknown_code_falls_back_without_losing_the_cause(self):
        got = _run_node(_CAMERA_PRELUDE + """
            out({
                bogus: cam.scanError('made_up_code'),
                withCause: cam.scanError('camera_busy', { name: 'NotReadableError' }),
                noCause: cam.scanError('timeout'),
            });
            """)
        self.assertEqual(got["bogus"]["code"], "unknown")
        self.assertEqual(got["bogus"]["messageKey"], "bscan.err.unknown")
        self.assertEqual(got["withCause"]["detail"], "NotReadableError")
        self.assertEqual(got["noCause"]["detail"], "")

    def test_getusermedia_exceptions_map_to_the_right_bucket(self):
        # 每个 DOMException 名字落到哪一档决定店员看到哪句话:开权限 / 关掉别的应用 /
        # 改手输。映射错了话术就答非所问。NotSupportedError 这条是真 Chromium 拒权限时
        # 实测发出来的名字(第一版漏了,落进 unknown)。
        got = _run_node(_CAMERA_PRELUDE + """
            const names = ['NotAllowedError','PermissionDeniedError','SecurityError',
                           'NotFoundError','DevicesNotFoundError','OverconstrainedError',
                           'NotSupportedError','NotReadableError','TrackStartError',
                           'AbortError','SomeBrandNewError'];
            const m = {};
            names.forEach((n) => { m[n] = cam.mediaErrorCode({ name: n }); });
            m['(nothing)'] = cam.mediaErrorCode(null);
            out(m);
            """)
        self.assertEqual(got["NotAllowedError"], "permission_denied")
        self.assertEqual(got["PermissionDeniedError"], "permission_denied")
        self.assertEqual(got["SecurityError"], "permission_denied")
        self.assertEqual(got["NotFoundError"], "no_camera")
        self.assertEqual(got["DevicesNotFoundError"], "no_camera")
        self.assertEqual(got["OverconstrainedError"], "no_camera")
        self.assertEqual(got["NotSupportedError"], "no_camera_api")
        self.assertEqual(got["NotReadableError"], "camera_busy")
        self.assertEqual(got["TrackStartError"], "camera_busy")
        self.assertEqual(got["AbortError"], "camera_busy")
        self.assertEqual(got["SomeBrandNewError"], "unknown")
        self.assertEqual(got["(nothing)"], "unknown")

    def test_domexception_legacy_code_does_not_impersonate_our_error(self):
        # 真机上照出来的坑:DOMException 带数字型 legacy code(NotFoundError=8、
        # SecurityError=18、AbortError=20),只看「有没有 .code」就会把它当成我们自己的
        # 错误对象直接放行,分档全被绕过 → 「没有摄像头」显示成最没用的通用报错。
        # NotAllowedError 的 legacy code 恰是 0,所以只测权限那一档时一切看起来正常。
        got = _run_node(_CAMERA_PRELUDE + """
            out({
                notFound: cam.isScanError({ name: 'NotFoundError', code: 8 }),
                security: cam.isScanError({ name: 'SecurityError', code: 18 }),
                abort: cam.isScanError({ name: 'AbortError', code: 20 }),
                notAllowed: cam.isScanError({ name: 'NotAllowedError', code: 0 }),
                ours: cam.isScanError(cam.scanError('timeout')),
                nothing: cam.isScanError(null),
                bogusString: cam.isScanError({ code: 'not_a_scan_code' }),
            });
            """)
        for name in ("notFound", "security", "abort", "notAllowed", "nothing", "bogusString"):
            self.assertFalse(got[name], f"{name} 被误认成我们自己的 scanError")
        self.assertTrue(got["ours"])

    def test_retail_formats_exclude_qr(self):
        got = _run_node(_CAMERA_PRELUDE + "out({ formats: cam.FORMATS });")
        self.assertEqual(
            got["formats"],
            ["ean_13", "ean_8", "upc_a", "upc_e", "code_128", "code_39", "itf"],
        )
        for junk in ("qr_code", "data_matrix", "aztec", "pdf417"):
            self.assertNotIn(junk, got["formats"], f"{junk} 白耗每帧 CPU · 商品条码里没有它")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
@unittest.skipUnless(ZXING_DIST.is_file(), "static/dist/zxing.js 未构建 · 先跑 build-home-js.mjs")
class ZXingShimDecodeTests(unittest.TestCase):
    """真产物 + 合成位图的解码闭环。"""

    def _decode(self, body: str) -> dict:
        return _run_node(f"""
            const ZXing = require({_jp(ZXING_DIST)});
            const shim = require({_jp(SHIM)});
            const out = (o) => process.stdout.write(JSON.stringify(o));
            {_EAN_HARNESS}
            {body}
            """)

    def test_decodes_synthetic_thai_ean13(self):
        # 885 = 泰国 GS1 前缀,客户店里的货就是这个开头。
        got = self._decode("""
            const det = new (shim.build(ZXing))({ formats: ['ean_13'] });
            det.detect(bitmap(ean13Modules('8850999320014'), 3, 40, 12)).then(
                (codes) => out({
                    n: codes.length,
                    raw: codes[0] && codes[0].rawValue,
                    format: codes[0] && codes[0].format,
                    hasBox: !!(codes[0] && codes[0].boundingBox),
                }),
                (e) => out({ rejected: String(e && (e.message || e.name)) })
            );
            """)
        self.assertEqual(got.get("n"), 1, f"合成 EAN-13 没解出来: {got}")
        self.assertEqual(got["raw"], "8850999320014")
        self.assertEqual(got["format"], "ean_13", "格式名反查表接错")
        self.assertTrue(got["hasBox"])

    def test_blank_frame_resolves_empty_not_rejects(self):
        # 每秒好几帧都是「这帧没码」。若它走 reject,上层就把常态当硬错误弹给店员。
        got = self._decode("""
            const det = new (shim.build(ZXing))({ formats: ['ean_13'] });
            det.detect(bitmap('0'.repeat(95), 3, 40, 12)).then(
                (codes) => out({ codes }),
                (e) => out({ rejected: String(e && (e.getKind ? e.getKind() : e.name)) })
            );
            """)
        self.assertEqual(got, {"codes": []})

    def test_minified_bundle_keeps_exception_identity(self):
        # 这条直指压缩改类名的坑:Odoo 比的是 err.name(它 serve 未压缩源码),
        # 照抄到压过的产物上就会把「没扫到」当硬错误。
        got = self._decode("""
            const e = new ZXing.NotFoundException();
            out({
                kind: typeof e.getKind === 'function' ? e.getKind() : null,
                isInstance: e instanceof ZXing.NotFoundException,
                hasChecksum: typeof ZXing.ChecksumException === 'function',
            });
            """)
        self.assertEqual(got["kind"], "NotFoundException")
        self.assertTrue(got["isInstance"])
        self.assertTrue(got["hasChecksum"])

    def test_fixture_generator_agrees_with_the_test_encoder(self):
        # scripts/_scan_ean_y4m.py(真浏览器验收用的假摄像头素材)与本文件里的 JS 编码器
        # 是两份独立实现的同一张 EAN-13 编码表。哪份抄错了,真浏览器那条就会在「素材本身
        # 不是合法条码」上白跑一整轮而查不出原因 —— 两份对一次,便宜。
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "_scan_ean_y4m", PROJECT_ROOT / "scripts" / "_scan_ean_y4m.py"
        )
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
        codes = ["8850999320014", "4901234567894", "0123456789012"]
        got = self._decode(
            "out({ bits: %s.map(ean13Modules) });" % json.dumps(codes),
        )
        self.assertEqual(got["bits"], [gen.ean13_bits(c) for c in codes])

    def test_shim_format_list_matches_camera_retail_list(self):
        # 两处各写一份格式名,漂了就是「原生能扫 ZXing 扫不到」这种只在 iOS 上复现的鬼故事。
        got = self._decode("out({ shim: shim.FORMAT_NAMES });")
        cam = _run_node(_CAMERA_PRELUDE + "out({ formats: cam.FORMATS });")
        self.assertEqual(got["shim"], cam["formats"])


if __name__ == "__main__":
    unittest.main()
