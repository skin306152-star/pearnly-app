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
console.log(JSON.stringify({
  firstResult,
  second,
  secondCaptionChildren: secondCaption.children.length,
  overlapCount,
  afterFirstCard,
  afterFirstRing: body.children.length,
  timerDelays: timers.map((timer) => timer.delay),
}));
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

    def test_all_three_success_paths_call_the_shared_visual(self):
        pos = (ROOT / "static" / "pos" / "pos-scan.js").read_text()
        inventory = (ROOT / "src" / "home" / "inventory-scan.ts").read_text()
        products = (ROOT / "src" / "home" / "sales-products-scan.ts").read_text()
        self.assertIn("visual.show({", pos)
        self.assertIn("showScanSuccessVisual({ label: name", inventory)
        self.assertIn("showCodeAccepted(code)", products)
        self.assertIn("checkState === 'free' || checkState === 'self'", products)

    def test_builds_ship_the_shared_source_and_style_to_both_apps(self):
        js_build = (ROOT / "scripts" / "build-home-js.mjs").read_text()
        css_build = (ROOT / "scripts" / "build-home-css.mjs").read_text()
        self.assertIn("'scan/scan-success-visual.js'", js_build)
        self.assertEqual(css_build.count("'scan/scan-success-visual.css'"), 2)


if __name__ == "__main__":
    unittest.main()
