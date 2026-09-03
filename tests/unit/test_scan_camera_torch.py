import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ScanCameraTorchTest(unittest.TestCase):
    def test_handle_exposes_real_track_torch_capability_and_toggle(self):
        script = r"""
const cameraPath = process.argv[1];
const errorsPath = process.argv[2];
const trackPath = process.argv[3];
const torchPath = process.argv[4];
let torch = false;
const applied = [];
const mediaTrack = {
  readyState: 'live',
  muted: false,
  stop() { this.readyState = 'ended'; },
  addEventListener() {},
  removeEventListener() {},
  getCapabilities: () => ({torch: true}),
  getSettings: () => ({torch}),
  applyConstraints: (constraints) => {
    torch = constraints.advanced[0].torch;
    applied.push(torch);
    return Promise.resolve();
  },
};
const stream = {
  getTracks: () => [mediaTrack],
  getVideoTracks: () => [mediaTrack],
};
global.document = {
  createElement: (tag) => tag === 'canvas'
    ? {width: 0, height: 0, getContext: () => ({drawImage() {}})}
    : {
        setAttribute() {}, className: '', readyState: 2, videoWidth: 640, videoHeight: 480,
        srcObject: null, play: () => Promise.resolve(), parentNode: null,
      },
};
Object.defineProperty(globalThis, 'navigator', {
  configurable: true,
  value: {mediaDevices: {getUserMedia: () => Promise.resolve(stream)}},
});
global.PearnlyScanCamera = {loadScript: () => Promise.resolve(), unsupportedReason: () => null};
require(errorsPath);
require(trackPath);
require(torchPath);
global.BarcodeDetector = function () {};
global.BarcodeDetector.getSupportedFormats = () => Promise.resolve(['ean_13']);
global.BarcodeDetector.prototype.detect = () => Promise.resolve([]);
const api = require(cameraPath);
const handle = api.create({onError: (err) => { throw err; }});
(async () => {
  await handle.start();
  const available = handle.cameraControl('torchAvailable');
  const before = handle.cameraControl('torchEnabled');
  const onResult = await handle.cameraControl('setTorch', true);
  const afterOn = handle.cameraControl('torchEnabled');
  const offResult = await handle.cameraControl('setTorch', false);
  const afterOff = handle.cameraControl('torchEnabled');
  handle.destroy();
  console.log(JSON.stringify({available, before, onResult, afterOn, offResult, afterOff, applied}));
})().catch((error) => { console.error(error); process.exit(1); });
"""
        result = subprocess.run(
            [
                "node",
                "-e",
                script,
                str(ROOT / "static" / "scan" / "scan-camera.js"),
                str(ROOT / "static" / "scan" / "scan-errors.js"),
                str(ROOT / "static" / "scan" / "scan-track.js"),
                str(ROOT / "static" / "scan" / "scan-torch.js"),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
            timeout=10,
        )
        got = json.loads(result.stdout)
        self.assertTrue(got["available"])
        self.assertFalse(got["before"])
        self.assertTrue(got["onResult"])
        self.assertTrue(got["afterOn"])
        self.assertTrue(got["offResult"])
        self.assertFalse(got["afterOff"])
        self.assertEqual(got["applied"], [True, False])


if __name__ == "__main__":
    unittest.main()
