/* Pearnly · ZXing-C++ WASM fallback for browsers without native BarcodeDetector. */
(function (root) {
    'use strict';

    var shell = root && root.PearnlyScanCamera;
    var SCRIPT = '/static/dist/barcode-detector.js';
    var WASM = '/static/dist/zxing_reader.wasm';
    var pending = null;

    function load() {
        if (pending) return pending;
        pending = shell
            .loadScript(SCRIPT)
            .then(function () {
                var api = root.BarcodeDetectionAPI;
                if (!api || !api.BarcodeDetector || !api.prepareZXingModule) {
                    throw new Error('barcode-detector API missing');
                }
                return api
                    .prepareZXingModule({
                        overrides: {
                            locateFile: function (name) {
                                return name.slice(-5) === '.wasm' ? shell.assetUrl(WASM) : name;
                            },
                        },
                    })
                    .then(function () {
                        return api.BarcodeDetector;
                    });
            })
            .catch(function (err) {
                pending = null;
                throw err;
            });
        return pending;
    }

    var api = { load: load, SCRIPT: SCRIPT, WASM: WASM };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) root.PearnlyScanWasm = api;
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
