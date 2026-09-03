#!/usr/bin/env python3
"""Scanner ergonomics: close-focus assistance and one-shot success feedback."""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import PROJECT_ROOT, _run_node

SCAN = PROJECT_ROOT / "static" / "scan"
FEEDBACK = SCAN / "scan-feedback.js"
CONTROLS = SCAN / "scan-track-controls.js"


def _js_path(path) -> str:
    return json.dumps(str(path))


@unittest.skipUnless(shutil.which("node"), "node is required")
class ScanFeedbackTests(unittest.TestCase):
    def test_success_uses_short_beep_and_supported_haptic(self):
        got = _run_node(f"""
            const calls = [];
            class Param {{
                setValueAtTime(value) {{ calls.push(['set', value]); }}
                exponentialRampToValueAtTime(value) {{ calls.push(['ramp', value]); }}
            }}
            class AudioContext {{
                constructor() {{ this.state = 'running'; this.currentTime = 1; this.destination = {{}}; }}
                createOscillator() {{
                    return {{
                        type: '', frequency: new Param(),
                        connect: () => calls.push(['osc-connect']),
                        start: () => calls.push(['start']), stop: () => calls.push(['stop']),
                    }};
                }}
                createGain() {{
                    return {{ gain: new Param(), connect: () => calls.push(['gain-connect']) }};
                }}
            }}
            global.AudioContext = AudioContext;
            Object.defineProperty(globalThis, 'navigator', {{
                value: {{ vibrate: (pattern) => calls.push(['vibrate', pattern]) }},
                configurable: true,
            }});
            const feedback = require({_js_path(FEEDBACK)});
            const armed = feedback.arm();
            Promise.resolve(feedback.success()).then(() => {{
                process.stdout.write(JSON.stringify({{ armed, calls }}));
            }});
            """)
        self.assertTrue(got["armed"])
        self.assertIn(["vibrate", 60], got["calls"])
        self.assertIn(["start"], got["calls"])
        self.assertIn(["stop"], got["calls"])

    def test_feedback_is_armed_in_all_three_camera_entrypoints(self):
        product = (PROJECT_ROOT / "src/home/sales-products-scan-cam.ts").read_text()
        inventory = (PROJECT_ROOT / "src/home/inventory-scan-camera.ts").read_text()
        pos = (PROJECT_ROOT / "static/pos/pos-scan.js").read_text()
        for source in (product, inventory, pos):
            self.assertIn("armFeedback", source)


@unittest.skipUnless(shutil.which("node"), "node is required")
class CameraControlTests(unittest.TestCase):
    def test_supported_camera_gets_continuous_focus_and_gentle_zoom(self):
        got = _run_node(f"""
            let applied = null;
            const controls = require({_js_path(CONTROLS)});
            const track = {{
                getCapabilities: () => ({{
                    focusMode: ['manual', 'continuous'],
                    zoom: {{ min: 1, max: 4, step: 0.1 }},
                }}),
                applyConstraints: (value) => {{ applied = value; return Promise.resolve(); }},
            }};
            controls.configure(track, {{ preferredZoom: 1.4 }}).then(() => {{
                process.stdout.write(JSON.stringify(applied));
            }});
            """)
        self.assertEqual(got["advanced"][0]["focusMode"], "continuous")
        self.assertEqual(got["advanced"][0]["zoom"], 1.4)

    def test_unsupported_zoom_falls_back_to_focus_only(self):
        got = _run_node(f"""
            let applied = null;
            const controls = require({_js_path(CONTROLS)});
            const track = {{
                getCapabilities: () => ({{ focusMode: ['continuous'] }}),
                applyConstraints: (value) => {{ applied = value; return Promise.resolve(); }},
            }};
            controls.configure(track, {{ preferredZoom: 1.4 }}).then(() => {{
                process.stdout.write(JSON.stringify(applied));
            }});
            """)
        self.assertEqual(got, {"advanced": [{"focusMode": "continuous"}]})

    def test_product_scan_requests_zoom_without_changing_other_flows(self):
        product = (PROJECT_ROOT / "src/home/sales-products-scan-cam.ts").read_text()
        inventory = (PROJECT_ROOT / "src/home/inventory-scan-camera.ts").read_text()
        pos = (PROJECT_ROOT / "static/pos/pos-scan.js").read_text()
        self.assertIn("PRODUCT_VISUAL_ZOOM = 1.125", product)
        self.assertIn("PRODUCT_CROP = { width: 0.8, height: 0.44 }", product)
        self.assertIn("cropRatio: PRODUCT_CROP", product)
        self.assertIn("preferredZoom: 1.2", product)
        self.assertNotIn("preferredZoom", inventory)
        self.assertNotIn("preferredZoom", pos)


class BundleContractTests(unittest.TestCase):
    def test_feedback_is_resident_and_track_controls_are_lazy(self):
        build = (PROJECT_ROOT / "scripts/build-home-js.mjs").read_text()
        self.assertIn("scan/scan-feedback.js", build)
        self.assertIn("scan/scan-track-controls.js", build)

    def test_camera_dispatches_feedback_once_per_accepted_code(self):
        camera = (SCAN / "scan-camera.js").read_text()
        accepted = camera[camera.index("for (var j = 0;") : camera.index("for (var k = 0;")]
        self.assertEqual(accepted.count("feedback.success()"), 1)
        self.assertNotIn("navigator.vibrate", camera)


if __name__ == "__main__":
    unittest.main()
