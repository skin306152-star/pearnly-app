/* Pearnly scanner feedback: unlock audio on the scan-button gesture, then beep on decode. */
(function (root) {
    'use strict';

    var context = null;
    var successBuffer = null;
    var BEEP_LEAD_IN = 0.008;
    var BEEP_DURATION = 0.078;
    var BEEP_TOTAL = 0.1;
    var BEEP_FREQUENCY = 2450;

    function audioCtor() {
        return root && (root.AudioContext || root.webkitAudioContext);
    }

    function buildSuccessBuffer() {
        if (!context || typeof context.createBuffer !== 'function') return null;
        var rate = context.sampleRate || 48000;
        var buffer = context.createBuffer(1, Math.round(rate * BEEP_TOTAL), rate);
        var samples = buffer.getChannelData(0);
        var attack = 0.0015;
        var release = Math.min(0.022, BEEP_DURATION * 0.4);
        for (var i = 0; i < samples.length; i++) {
            var t = i / rate - BEEP_LEAD_IN;
            if (t < 0 || t > BEEP_DURATION) continue;
            var envelope;
            if (t < attack) envelope = t / attack;
            else if (t > BEEP_DURATION - release) envelope = (BEEP_DURATION - t) / release;
            else envelope = Math.exp((-2.4 * (t - attack)) / BEEP_DURATION);
            var phase = 2 * Math.PI * BEEP_FREQUENCY * t;
            samples[i] = (Math.sin(phase) + Math.sin(phase * 2) * 0.32) * envelope * 0.5;
        }
        return buffer;
    }

    function arm() {
        var Ctor = audioCtor();
        if (!Ctor) return false;
        try {
            if (!context || context.state === 'closed') context = new Ctor();
            if (!successBuffer) successBuffer = buildSuccessBuffer();
            if (context.state === 'suspended' && context.resume) {
                var resumed = context.resume();
                if (resumed && resumed.catch) resumed.catch(function () {});
            }
            return true;
        } catch {
            return false;
        }
    }

    function beep() {
        if (!context || context.state === 'closed') return false;
        function play() {
            try {
                if (!successBuffer) successBuffer = buildSuccessBuffer();
                if (!successBuffer) return false;
                var source = context.createBufferSource();
                source.buffer = successBuffer;
                source.connect(context.destination);
                source.start(context.currentTime);
                source.stop(context.currentTime + successBuffer.duration);
                return true;
            } catch {
                return false;
            }
        }
        if (context.state === 'suspended' && context.resume) {
            return context.resume().then(play, function () {
                return false;
            });
        }
        return play();
    }

    function success() {
        var nav = root && root.navigator;
        if (nav && typeof nav.vibrate === 'function') nav.vibrate(60);
        return beep();
    }

    var api = { arm: arm, success: success };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.PearnlyScanFeedback = api;
        root.PearnlyScanCamera = root.PearnlyScanCamera || {};
        root.PearnlyScanCamera.armFeedback = arm;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
