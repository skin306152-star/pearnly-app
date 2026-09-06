/* Stocktake QR decoding shares the POS camera stream and shipped WASM loader. */
(function () {
    'use strict';
    window.PearnlyStocktakeCamera = function (options) {
        let shared = null,
            timer = null,
            stopped = false,
            settled = false;
        let candidate = '',
            hits = 0,
            lastSent = '',
            lastSeen = 0;
        const video = document.createElement('video');
        video.muted = true;
        video.autoplay = true;
        video.playsInline = true;
        options.container.appendChild(video);
        function deliver(value) {
            if (stopped || settled) return;
            if (options.onScan(String(value).trim()) === true) settled = true;
        }
        return {
            async start() {
                try {
                    const engine = await window.PearnlyScanCamera.ensureLoaded();
                    const Ctor = await engine.withTimeout(
                        window.PearnlyScanWasm.load(),
                        20000,
                        'decoder_unavailable'
                    );
                    if (stopped) return false;
                    const qr = new Ctor({ formats: ['qr_code'] });
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d', { willReadFrequently: true });
                    async function tick() {
                        if (stopped || settled) return;
                        try {
                            if (video.readyState >= 2 && video.videoWidth) {
                                const sw = video.videoWidth * 0.9,
                                    sh = video.videoHeight * 0.85;
                                canvas.width = Math.min(960, sw);
                                canvas.height = Math.round((sh * canvas.width) / sw);
                                ctx.drawImage(
                                    video,
                                    (video.videoWidth - sw) / 2,
                                    (video.videoHeight - sh) / 2,
                                    sw,
                                    sh,
                                    0,
                                    0,
                                    canvas.width,
                                    canvas.height
                                );
                                const codes = await qr.detect(canvas);
                                if (stopped || settled) return;
                                const code = codes[0]?.rawValue?.trim() || '';
                                if (code) {
                                    hits =
                                        candidate === code && Date.now() - lastSeen < 2000
                                            ? hits + 1
                                            : 1;
                                    candidate = code;
                                    lastSeen = Date.now();
                                    if (hits >= 2 && code !== lastSent) {
                                        lastSent = code;
                                        deliver(code);
                                    }
                                } else if (Date.now() - lastSeen > 1500) {
                                    candidate = '';
                                    hits = 0;
                                    lastSent = '';
                                }
                            }
                        } catch (err) {
                            if (!stopped) options.onError(err);
                            return;
                        }
                        if (!stopped && !settled) timer = setTimeout(tick, 180);
                    }
                    shared = engine.create({
                        video,
                        cropRatio: { width: 0.9, height: 0.85 },
                        onScan: deliver,
                        onError: options.onError,
                        onReady: () => {
                            void tick();
                        },
                    });
                    const started = await shared.start();
                    if (stopped) shared.destroy();
                    return started && !stopped;
                } catch (err) {
                    if (!stopped) options.onError(err);
                    return false;
                }
            },
            destroy() {
                stopped = true;
                clearTimeout(timer);
                shared?.destroy();
                video.remove();
            },
        };
    };
})();
