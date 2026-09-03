import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VISUAL_JS = ROOT / "static" / "scan" / "scan-success-visual.js"
VISUAL_CSS = ROOT / "static" / "scan" / "scan-success-visual.css"


class ScanSuccessVisualTest(unittest.TestCase):
    def _run_harness(self):
        script = r"""
class FakeNode {
  constructor(tag) {
    this.tagName = tag;
    this.children = [];
    this.parentNode = null;
    this.attributes = {};
    this.listeners = {};
    this.className = '';
    this._classes = new Set();
    this.style = {
      values: {},
      setProperty: (key, value) => { this.style.values[key] = value; },
    };
    this.classList = {
      add: (name) => this._classes.add(name),
      remove: (name) => this._classes.delete(name),
      contains: (name) => this._classes.has(name),
    };
  }
  appendChild(child) { child.parentNode = this; this.children.push(child); return child; }
  removeChild(child) { this.children = this.children.filter((item) => item !== child); child.parentNode = null; }
  setAttribute(key, value) { this.attributes[key] = value; }
  addEventListener(type, cb) { this.listeners[type] = cb; }
  fire(type) { if (this.listeners[type]) this.listeners[type](); }
  getBoundingClientRect() { return this.rect || {left: 0, top: 0, width: 0, height: 0}; }
}
const body = new FakeNode('body');
const target = new FakeNode('target');
target.rect = {left: 10, top: 700, width: 40, height: 40};
const saved = new Map();
global.localStorage = {
  getItem: (key) => saved.has(key) ? saved.get(key) : null,
  setItem: (key, value) => saved.set(key, value),
};
global.document = {
  body,
  documentElement: {clientWidth: 390, clientHeight: 844},
  createElement: (tag) => new FakeNode(tag),
  querySelector: (selector) => selector === '#target' ? target : null,
};
global.innerWidth = 390;
global.innerHeight = 844;
const timers = [];
global.setTimeout = (cb, delay) => { timers.push({cb, delay}); return timers.length; };
const api = require(process.argv[1]);
let loadedUrl = '';
const first = api.show({
  label: 'Water',
  imageUrl: '/image/water.jpg',
  target: '#target',
  loadImage: (img, url) => { loadedUrl = url; img.fire('load'); },
});
const firstCard = body.children[0];
const firstRing = body.children[1];
const firstCaption = firstCard.children[1];
const firstResult = {
  first,
  childCount: body.children.length,
  loadedUrl,
  hasImage: firstCard.classList.contains('has-image'),
  amount: firstCaption.children[1].textContent,
  dx: firstCard.style.values['--scan-fly-x'],
  dy: firstCard.style.values['--scan-fly-y'],
  ringLeft: firstRing.style.left,
};
const second = api.show({label: 'New code', target, increment: false});
const secondCard = body.children[2];
const secondCaption = secondCard.children[1];
const overlapCount = body.children.length;
firstCard.fire('animationend');
const afterFirstCard = body.children.length;
firstRing.fire('animationend');
const controlHost = new FakeNode('controls');
const controlAnchor = new FakeNode('frame');
let torchOn = false;
const torchCalls = [];
const camera = {
  cameraControl: (name, next) => {
    if (name === 'torchAvailable') return true;
    if (name === 'torchEnabled') return torchOn;
    if (name === 'setTorch') { torchCalls.push(next); torchOn = next; return Promise.resolve(true); }
    return false;
  },
};
const control = api.mountControls({
  container: controlHost,
  anchor: controlAnchor,
  camera,
  t: (key) => ({
    'scan-controls.animation': '扫码动画',
    'scan-controls.torch-on': '打开手电筒',
    'scan-controls.torch-off': '关闭手电筒',
  })[key] || key,
});
const toolbar = controlAnchor.children[0];
const torch = toolbar.children[0];
const checkbox = toolbar.children[1].children[0];
checkbox.checked = false;
checkbox.fire('change');
const disabledVisual = api.show({label: 'Disabled', target});
torch.fire('click');
Promise.resolve().then(() => Promise.resolve()).then(() => {
  console.log(JSON.stringify({
    firstResult,
    second,
    secondCaptionChildren: secondCaption.children.length,
    overlapCount,
    afterFirstCard,
    afterFirstRing: body.children.length,
    timerDelays: timers.map((timer) => timer.delay),
    controls: {
      checkboxLabel: toolbar.children[1].children[1].textContent,
      disabledVisual,
      motionStored: saved.get('pearnly_scan_motion'),
      torchHidden: torch.hidden,
      torchCalls,
      torchPressed: torch.attributes['aria-pressed'],
      torchTitle: torch.title,
      hostChildren: controlHost.children.length,
      anchorChildren: controlAnchor.children.length,
    },
  }));
});
"""
        out = subprocess.run(
            ["node", "-e", script, str(VISUAL_JS)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(out.stdout)

    def test_visuals_overlap_without_queueing_or_blocking(self):
        result = self._run_harness()
        first = result["firstResult"]
        self.assertTrue(first["first"])
        self.assertTrue(result["second"])
        self.assertEqual(result["overlapCount"], 4)
        self.assertEqual(first["amount"], "+1")
        self.assertEqual(result["secondCaptionChildren"], 1)
        self.assertEqual(result["afterFirstCard"], 3)
        self.assertEqual(result["afterFirstRing"], 2)
        self.assertEqual(result["timerDelays"], [1100, 1100])

    def test_image_loader_and_target_geometry_are_reused(self):
        first = self._run_harness()["firstResult"]
        self.assertEqual(first["loadedUrl"], "/image/water.jpg")
        self.assertTrue(first["hasImage"])
        self.assertEqual(first["dx"], "-147px")
        self.assertEqual(first["ringLeft"], "30px")
        self.assertTrue(first["dy"].endswith("px"))

    def test_css_is_non_blocking_and_respects_reduced_motion(self):
        css = VISUAL_CSS.read_text()
        self.assertIn("pointer-events: none", css)
        self.assertIn("prefers-reduced-motion: reduce", css)
        self.assertIn("scan-success-fly 680ms", css)
        self.assertIn("will-change: transform, opacity", css)
        self.assertIn(".scan-view-torch[hidden]", css)
        self.assertIn(".scan-view-motion input", css)

    def test_shared_controls_persist_animation_and_toggle_supported_torch(self):
        controls = self._run_harness()["controls"]
        self.assertEqual(controls["checkboxLabel"], "扫码动画")
        self.assertFalse(controls["disabledVisual"])
        self.assertEqual(controls["motionStored"], "0")
        self.assertFalse(controls["torchHidden"])
        self.assertEqual(controls["torchCalls"], [True])
        self.assertEqual(controls["torchPressed"], "true")
        self.assertEqual(controls["torchTitle"], "关闭手电筒")
        self.assertEqual(controls["hostChildren"], 0)
        self.assertEqual(controls["anchorChildren"], 1)

    def test_all_three_success_paths_call_the_shared_visual(self):
        pos = (ROOT / "static" / "pos" / "pos-scan.js").read_text()
        inventory = (ROOT / "src" / "home" / "inventory-scan.ts").read_text()
        products = (ROOT / "src" / "home" / "sales-products-scan.ts").read_text()
        self.assertIn("visual.show({", pos)
        self.assertIn("showScanSuccessVisual({ label: name", inventory)
        self.assertIn("showCodeAccepted(code)", products)
        self.assertIn("checkState === 'free' || checkState === 'self'", products)
        self.assertIn("visual.mountControls({", pos)
        inventory_camera = (ROOT / "src" / "home" / "inventory-scan-camera.ts").read_text()
        self.assertIn("mountScanCameraControls(stage, handle, frame)", inventory_camera)
        self.assertIn("anchor: $('bscan-frame')", pos)
        product_camera = (ROOT / "src" / "home" / "sales-products-scan-cam.ts").read_text()
        self.assertIn("mountScanCameraControls(view, h, frame)", product_camera)

    def test_builds_ship_the_shared_source_and_style_to_both_apps(self):
        js_build = (ROOT / "scripts" / "build-home-js.mjs").read_text()
        css_build = (ROOT / "scripts" / "build-home-css.mjs").read_text()
        self.assertIn("'scan/scan-success-visual.js'", js_build)
        self.assertEqual(css_build.count("'scan/scan-success-visual.css'"), 2)


if __name__ == "__main__":
    unittest.main()
