#!/usr/bin/env python3
"""Tonight's scanner upgrade: local WASM, camera quality and false-read revocation."""

from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path

from tests.unit._node_harness import PROJECT_ROOT, _run_node

SCAN = PROJECT_ROOT / "static" / "scan"
VENDOR = PROJECT_ROOT / "static" / "vendor" / "barcode-detector"
DIST = PROJECT_ROOT / "static" / "dist"


@unittest.skipUnless(shutil.which("node"), "node is required")
class RejectedCandidateTests(unittest.TestCase):
    def test_rejected_false_read_must_confirm_again(self):
        track = json.dumps(str(SCAN / "scan-track.js"))
        got = _run_node(f"""
            const {{ createTracker }} = require({track});
            const tr = createTracker({{
                clearAfterMs: 1600, clearAfterMisses: 12,
                dupNoticeMs: 800, dupNoticeMisses: 2,
                confirmHits: 3, confirmWindowMs: 3000,
            }});
            const code = '881341040333';
            const before = [tr.sample([code], 0), tr.sample([code], 30), tr.sample([code], 60)];
            tr.reject(code);
            const whileHeld = tr.sample([code], 90);
            let at = 300;
            for (let i = 0; i < 12; i++, at += 240) tr.sample([], at);
            const after = [tr.sample([code], at), tr.sample([code], at + 30), tr.sample([code], at + 60)];
            process.stdout.write(JSON.stringify({{
                acceptedBefore: before.flatMap((e) => e.accepted),
                acceptedWhileHeld: whileHeld.accepted,
                acceptedAfter: after.flatMap((e) => e.accepted),
            }}));
            """)
        self.assertEqual(got["acceptedBefore"], ["881341040333"])
        self.assertEqual(got["acceptedWhileHeld"], [])
        self.assertEqual(got["acceptedAfter"], ["881341040333"])

    def test_two_stable_wrong_fragments_are_not_enough(self):
        track = json.dumps(str(SCAN / "scan-track.js"))
        got = _run_node(f"""
            const {{ createTracker }} = require({track});
            const tr = createTracker({{
                clearAfterMs: 1600, clearAfterMisses: 12,
                dupNoticeMs: 800, dupNoticeMisses: 2,
                confirmHits: 3, confirmWindowMs: 3000,
            }});
            const bad = ['82130503', '88134826', '881341040333'];
            const accepted = [];
            for (const code of bad) {{
                accepted.push(...tr.sample([code], 0).accepted);
                accepted.push(...tr.sample([code], 30).accepted);
            }}
            process.stdout.write(JSON.stringify(accepted));
            """)
        self.assertEqual(got, [])


class ScannerAssetTests(unittest.TestCase):
    def test_open_source_wasm_assets_are_vendored(self):
        for name in (
            "ponyfill.js",
            "zxing_reader.wasm",
            "barcode-detector-LICENSE",
            "zxing-wasm-LICENSE",
            "README.md",
            "version",
        ):
            self.assertGreater((VENDOR / name).stat().st_size, 0, name)

    def test_runtime_products_exist(self):
        self.assertGreater((DIST / "barcode-detector.js").stat().st_size, 20_000)
        self.assertGreater((DIST / "zxing_reader.wasm").stat().st_size, 500_000)

    def test_camera_requests_hd_and_continuous_focus(self):
        source = (SCAN / "scan-camera.js").read_text(encoding="utf-8")
        controls = (SCAN / "scan-track-controls.js").read_text(encoding="utf-8")
        self.assertIn("idealWidth", source)
        self.assertIn("idealHeight", source)
        self.assertIn("focusMode", controls)
        self.assertIn("applyConstraints", controls)

    def test_wasm_is_same_origin_and_versioned(self):
        shim = (SCAN / "scan-wasm-shim.js").read_text(encoding="utf-8")
        self.assertIn("'/static/dist/barcode-detector.js'", shim)
        self.assertIn("'/static/dist/zxing_reader.wasm'", shim)
        self.assertIn("shell.assetUrl", shim)
        self.assertNotIn("jsdelivr", shim)

    def test_unknown_catalog_codes_revoke_decoder_trust(self):
        pos = (PROJECT_ROOT / "static/pos/pos-scan.js").read_text(encoding="utf-8")
        inventory = (PROJECT_ROOT / "src/home/inventory-scan.ts").read_text(encoding="utf-8")
        self.assertIn("cam.reject(code)", pos)
        self.assertIn("rejectCameraCode(code)", inventory)

    def test_duplicate_notice_states_what_happened(self):
        i18n = (PROJECT_ROOT / "static/i18n-data.js").read_text(encoding="utf-8")
        self.assertIn("条码仍在取景框内，数量未增加", i18n)
        self.assertNotIn("刚才这一下当成同一件了", i18n)


@unittest.skipUnless(shutil.which("node"), "node is required")
class WasmDecodeTests(unittest.TestCase):
    def test_real_wasm_decodes_the_demo_barcode(self):
        js = json.dumps(str(DIST / "barcode-detector.js"))
        wasm = json.dumps(str(DIST / "zxing_reader.wasm"))
        got = _run_node(
            f"""
            const fs = require('fs');
            (0, eval)(fs.readFileSync({js}, 'utf8'));
            global.DOMRectReadOnly = class {{
                constructor(x, y, width, height) {{ Object.assign(this, {{ x, y, width, height }}); }}
            }};
            global.ImageData = class {{
                constructor(data, width, height) {{ Object.assign(this, {{ data, width, height }}); }}
            }};
            const wasm = fs.readFileSync({wasm});
            global.fetch = async () => new Response(wasm, {{
                headers: {{ 'Content-Type': 'application/wasm' }},
            }});
            const L = ['0001101','0011001','0010011','0111101','0100011',
                       '0110001','0101111','0111011','0110111','0001011'];
            const G = ['0100111','0110011','0011011','0100001','0011101',
                       '0111001','0000101','0010001','0001001','0010111'];
            const R = L.map((s) => s.replace(/[01]/g, (c) => c === '0' ? '1' : '0'));
            const parity = ['LLLLLL','LLGLGG','LLGGLG','LLGGGL','LGLLGG',
                            'LGGLLG','LGGGLL','LGLGLG','LGLGGL','LGGLGL'];
            function image(code) {{
                const digits = code.split('').map(Number);
                let bits = '101';
                for (let i = 0; i < 6; i++)
                    bits += (parity[digits[0]][i] === 'L' ? L : G)[digits[i + 1]];
                bits += '01010';
                for (let i = 7; i < 13; i++) bits += R[digits[i]];
                bits += '101';
                const scale = 3, quiet = 12, height = 80;
                const width = (bits.length + quiet * 2) * scale;
                const data = new Uint8ClampedArray(width * height * 4);
                for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {{
                    const m = Math.floor(x / scale) - quiet;
                    const v = m >= 0 && m < bits.length && bits[m] === '1' ? 0 : 255;
                    const p = (y * width + x) * 4;
                    data[p] = data[p + 1] = data[p + 2] = v; data[p + 3] = 255;
                }}
                return new ImageData(data, width, height);
            }}
            (async () => {{
                await BarcodeDetectionAPI.prepareZXingModule({{
                    overrides: {{ locateFile: () => '/static/dist/zxing_reader.wasm' }},
                }});
                const detector = new BarcodeDetectionAPI.BarcodeDetector({{ formats: ['ean_13'] }});
                const codes = await detector.detect(image('4891338050333'));
                process.stdout.write(JSON.stringify(codes.map((c) => [c.rawValue, c.format])));
            }})().catch((e) => {{ process.stderr.write(String(e.stack || e)); process.exit(1); }});
            """,
            timeout=30,
        )
        self.assertEqual(got, [["4891338050333", "ean_13"]])


if __name__ == "__main__":
    unittest.main()
