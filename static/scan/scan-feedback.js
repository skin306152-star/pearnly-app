/* Pearnly scanner feedback: unlock audio on the scan-button gesture, then beep on decode. */
(function (root) {
    'use strict';

    var context = null;

    function audioCtor() {
        return root && (root.AudioContext || root.webkitAudioContext);
    }

    function arm() {
        var Ctor = audioCtor();
        if (!Ctor) return false;
        try {
            if (!context || context.state === 'closed') context = new Ctor();
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
                var start = context.currentTime;
                var oscillator = context.createOscillator();
                var gain = context.createGain();
                oscillator.type = 'sine';
                oscillator.frequency.setValueAtTime(960, start);
                gain.gain.setValueAtTime(0.0001, start);
                gain.gain.exponentialRampToValueAtTime(0.1, start + 0.004);
                gain.gain.exponentialRampToValueAtTime(0.0001, start + 0.075);
                oscillator.connect(gain);
                gain.connect(context.destination);
                oscillator.start(start);
                oscillator.stop(start + 0.08);
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
