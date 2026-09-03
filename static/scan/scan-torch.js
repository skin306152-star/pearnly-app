/* Optional camera torch control. Unsupported browsers keep scanning without showing a dead button. */
(function (root) {
    'use strict';

    function available(track) {
        if (!track || typeof track.getCapabilities !== 'function') return false;
        try {
            return track.getCapabilities().torch === true;
        } catch {
            return false;
        }
    }

    function enabled(track) {
        if (!track || typeof track.getSettings !== 'function') return false;
        try {
            return track.getSettings().torch === true;
        } catch {
            return false;
        }
    }

    function set(track, value) {
        if (!available(track) || typeof track.applyConstraints !== 'function') {
            return Promise.resolve(false);
        }
        return Promise.resolve(track.applyConstraints({ advanced: [{ torch: !!value }] })).then(
            function () {
                return true;
            },
            function () {
                return false;
            }
        );
    }

    function control(track, name, value) {
        if (name === 'torchAvailable') return available(track);
        if (name === 'torchEnabled') return enabled(track);
        if (name === 'setTorch') return set(track, value);
        return false;
    }

    var api = { control: control };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) root.PearnlyScanTorch = api;
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
