/* Apply optional camera controls without making unsupported devices fail to scan. */
(function (root) {
    'use strict';

    function zoomValue(range, preferred) {
        if (!range || !Number.isFinite(preferred)) return null;
        var value = Math.min(range.max, Math.max(range.min, preferred));
        if (Number.isFinite(range.step) && range.step > 0) {
            value = range.min + Math.round((value - range.min) / range.step) * range.step;
        }
        return Number(value.toFixed(3));
    }

    function configure(track, opts) {
        if (!track || !track.getCapabilities || !track.applyConstraints)
            return Promise.resolve(false);
        var caps;
        try {
            caps = track.getCapabilities();
        } catch {
            return Promise.resolve(false);
        }
        var settings = {};
        if (caps.focusMode && caps.focusMode.indexOf('continuous') >= 0) {
            settings.focusMode = 'continuous';
        }
        var zoom = zoomValue(caps.zoom, Number(opts && opts.preferredZoom));
        if (zoom !== null) settings.zoom = zoom;
        if (!Object.keys(settings).length) return Promise.resolve(false);
        return Promise.resolve(track.applyConstraints({ advanced: [settings] })).then(
            function () {
                return true;
            },
            function () {
                return false;
            }
        );
    }

    var api = { configure: configure };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) root.PearnlyScanTrackControls = api;
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
