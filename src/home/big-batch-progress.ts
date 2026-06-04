// ============================================================
// REFACTOR-C1 (2026-05-27) · 大批量上传进度条 big-batch-progress 从 home.js 抽出为 ES module
//
// 来源:home.js L18339-18484 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================
// ============================================================
// v118.27.8.1.15 · 大批量上传 (>100 张) 进度条 + 关页警告 + 首次一次性提示
//   - 跟现有 btn-start handler 解耦 · 通过 window._bigBatchStart / _bigBatchStop 提供 hook
//   - 用 setInterval 200ms 看 pendingFiles 完成数 · 不动 worker 主循环
//   - beforeunload 跟文件夹监听共存 · 各自 attach / detach
// ============================================================
(function () {
    'use strict';

    const BIG_THRESHOLD = 100; // >= 100 张才认为是大批量
    const TICK_MS = 250;
    const PER_FILE_SEC = 6; // 预估每张 6 秒(并行 6 路 · 单张实际 ~3-4s)
    const TIP_STORAGE_KEY = 'pearnly_big_batch_tip_shown';

    let _intervalId: ReturnType<typeof setInterval> | null = null;
    let _pendingRef: { status: string }[] | null = null;
    let _totalAtStart = 0;
    let _startTs = 0;
    let _unloadAttached = false;

    function _unloadHandler(e: BeforeUnloadEvent) {
        const msg =
            typeof t === 'function'
                ? t('big-batch-unload-warn')
                : 'Batch OCR running · close anyway?';
        e.preventDefault();
        e.returnValue = msg;
        return msg;
    }
    function _attachUnload() {
        if (_unloadAttached) return;
        _unloadAttached = true;
        window.addEventListener('beforeunload', _unloadHandler);
    }
    function _detachUnload() {
        if (!_unloadAttached) return;
        _unloadAttached = false;
        window.removeEventListener('beforeunload', _unloadHandler);
    }

    function _injectBar() {
        if (document.getElementById('big-batch-progress')) return;
        const fileList = document.getElementById('file-list');
        if (!fileList || !fileList.parentNode) return;
        const bar = document.createElement('div');
        bar.id = 'big-batch-progress';
        bar.className = 'big-batch-progress';
        bar.innerHTML =
            '<div class="bbp-row">' +
            '<svg class="bbp-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
            '<circle cx="8" cy="8" r="6.5"/>' +
            '<path d="M8 4.5v3.5l2.5 1.5"/>' +
            '</svg>' +
            '<span class="bbp-text" id="bbp-text"></span>' +
            '</div>' +
            '<div class="bbp-track"><div class="bbp-fill" id="bbp-fill" style="width:0%"></div></div>';
        // 插到 #file-list 上方
        fileList.parentNode.insertBefore(bar, fileList);
        const txt = document.getElementById('bbp-text');
        if (txt)
            txt.textContent =
                typeof t === 'function' ? t('big-batch-progress-init') : 'Starting...';
    }
    function _removeBar() {
        const el = document.getElementById('big-batch-progress');
        if (el) el.remove();
    }

    function _tick() {
        if (!_pendingRef) return;
        let done = 0;
        for (let i = 0; i < _pendingRef.length; i++) {
            const s = _pendingRef[i].status;
            if (s === 'success' || s === 'error' || s === 'cancelled') done++;
        }
        const total = _totalAtStart;
        const pct = total > 0 ? Math.min(100, Math.floor((100 * done) / total)) : 0;
        const elapsedSec = (Date.now() - _startTs) / 1000;
        // ETA · 用实测速率 · 至少跑过 3 张才算 · 否则用 PER_FILE_SEC 兜底
        let remainSec;
        if (done >= 3 && elapsedSec > 1) {
            const realRate = elapsedSec / done;
            remainSec = (total - done) * realRate;
        } else {
            remainSec = ((total - done) * PER_FILE_SEC) / 6; // 6 路并行
        }
        const remainMin = Math.max(1, Math.ceil(remainSec / 60));
        const fill = document.getElementById('bbp-fill');
        const txt = document.getElementById('bbp-text');
        if (fill) fill.style.width = pct + '%';
        if (txt) {
            if (done >= total) {
                txt.textContent = t('big-batch-progress-done').replace(
                    '{total}',
                    total as unknown as string
                );
            } else {
                txt.textContent = t('big-batch-progress-running')
                    .replace('{done}', done as unknown as string)
                    .replace('{total}', total as unknown as string)
                    .replace('{min}', remainMin as unknown as string);
            }
        }
    }

    function _maybeShowFirstTip(total: number) {
        try {
            if (localStorage.getItem(TIP_STORAGE_KEY) === '1') return;
        } catch (_) {
            /* silent · localStorage 私模 / 兜底默认 */
        }
        const estMin = Math.max(1, Math.ceil((total * PER_FILE_SEC) / 6 / 60));
        const msg = t('big-batch-first-tip')
            .replace('{n}', total as unknown as string)
            .replace('{min}', estMin as unknown as string);
        if (typeof showToast === 'function') showToast(msg, 'info', 8000);
        try {
            localStorage.setItem(TIP_STORAGE_KEY, '1');
        } catch (_) {
            /* silent · localStorage 私模/配额 */
        }
    }

    function _start(pendingFiles: { status: string }[]) {
        if (!pendingFiles || pendingFiles.length < BIG_THRESHOLD) return;
        _pendingRef = pendingFiles;
        _totalAtStart = pendingFiles.length;
        _startTs = Date.now();
        _injectBar();
        _attachUnload();
        _maybeShowFirstTip(_totalAtStart);
        if (_intervalId) clearInterval(_intervalId);
        _intervalId = setInterval(_tick, TICK_MS);
        _tick(); // 立刻刷一次
    }
    function _stop() {
        if (_intervalId) {
            clearInterval(_intervalId);
            _intervalId = null;
        }
        _detachUnload();
        // 让 done 状态显示 1 秒后再隐藏 · 给用户看一眼
        if (_pendingRef && _totalAtStart >= BIG_THRESHOLD) {
            _tick();
            setTimeout(_removeBar, 1200);
        } else {
            _removeBar();
        }
        _pendingRef = null;
        _totalAtStart = 0;
    }

    window._bigBatchStart = _start as (files?: unknown) => void;
    window._bigBatchStop = _stop;

    // i18n 切语言 · 重渲进度文本
    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('big-batch-progress', function () {
            if (_pendingRef) _tick();
        });
    }
})();
