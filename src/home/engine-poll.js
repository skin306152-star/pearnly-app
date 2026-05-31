// REFACTOR-C1-home-batch9g1 · 从 home.js verbatim 抽出(0 逻辑改)
// OCR 引擎就绪轮询(ocr-recognize 经 window 调)

let _engineCheckTimer = null;

function startEnginePolling() {
    stopEnginePolling();
    _engineCheckTimer = setInterval(async () => {
        try {
            const h = await fetch('/api/health').then((r) => r.json());
            if (h.ocr_ready) stopEnginePolling();
        } catch {}
    }, 10000);
}
function stopEnginePolling() {
    if (_engineCheckTimer) {
        clearInterval(_engineCheckTimer);
        _engineCheckTimer = null;
    }
}

window.startEnginePolling = startEnginePolling;
window.stopEnginePolling = stopEnginePolling;
