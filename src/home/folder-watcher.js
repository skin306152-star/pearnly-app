// ============================================================
// REFACTOR-C1 (2026-05-27) · 文件夹监听 folder-watcher 从 home.js 抽出为 ES module
//
// 来源:home.js L7420-7968 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================
/* global escapeHtml, svgIcon, token, showConfirm, switchAutomationTab */
// ============================================================
// v95 · 文件夹监听 · 浏览器 File System Access API · 0 费用网页端方案
// 仅 Chrome / Edge 支持
// ============================================================
(function folderWatcher() {
    const SUPPORTED = typeof window !== 'undefined' && 'showDirectoryPicker' in window;
    const VALID_EXTS = /\.(pdf|jpe?g|png|webp)$/i;
    const DB_NAME = 'mrpilot_folder_watcher';
    const DB_VERSION = 1;

    let _dbPromise = null;
    let _dirHandle = null;
    let _intervalId = null;
    let _intervalSec = 60;
    let _paused = false;
    let _scanning = false; // 防重入
    let _processedCount = 0;
    let _failedCount = 0;
    let _queueCount = 0;
    let _recent = []; // [{name, status, time, error?, history_id?}]
    let _lastScanAt = null;
    let _loaded = false;

    // ---------- IndexedDB ----------
    function openDB() {
        if (_dbPromise) return _dbPromise;
        _dbPromise = new Promise((resolve, reject) => {
            const req = indexedDB.open(DB_NAME, DB_VERSION);
            req.onupgradeneeded = (e) => {
                const db = e.target.result;
                if (!db.objectStoreNames.contains('handles')) db.createObjectStore('handles');
                if (!db.objectStoreNames.contains('seen')) db.createObjectStore('seen');
                if (!db.objectStoreNames.contains('config')) db.createObjectStore('config');
            };
            req.onsuccess = (e) => resolve(e.target.result);
            req.onerror = (e) => reject(e.target.error);
        });
        return _dbPromise;
    }

    function idbGet(store, key) {
        return openDB().then(
            (db) =>
                new Promise((resolve, reject) => {
                    const tx = db.transaction(store, 'readonly');
                    const req = tx.objectStore(store).get(key);
                    req.onsuccess = () => resolve(req.result);
                    req.onerror = () => reject(req.error);
                })
        );
    }
    function idbPut(store, key, value) {
        return openDB().then(
            (db) =>
                new Promise((resolve, reject) => {
                    const tx = db.transaction(store, 'readwrite');
                    tx.objectStore(store).put(value, key);
                    tx.oncomplete = () => resolve();
                    tx.onerror = () => reject(tx.error);
                })
        );
    }
    function idbDel(store, key) {
        return openDB().then(
            (db) =>
                new Promise((resolve, reject) => {
                    const tx = db.transaction(store, 'readwrite');
                    tx.objectStore(store).delete(key);
                    tx.oncomplete = () => resolve();
                    tx.onerror = () => reject(tx.error);
                })
        );
    }
    function idbClear(store) {
        return openDB().then(
            (db) =>
                new Promise((resolve, reject) => {
                    const tx = db.transaction(store, 'readwrite');
                    tx.objectStore(store).clear();
                    tx.oncomplete = () => resolve();
                    tx.onerror = () => reject(tx.error);
                })
        );
    }

    // ---------- 权限 ----------
    async function ensurePermission(handle) {
        if (!handle) return false;
        try {
            const opts = { mode: 'read' };
            let perm = await handle.queryPermission(opts);
            if (perm === 'granted') return true;
            perm = await handle.requestPermission(opts);
            return perm === 'granted';
        } catch (e) {
            console.warn('[folder] permission check failed:', e);
            return false;
        }
    }

    // ---------- UI ----------
    function setStatus(textKey, cls) {
        const el = document.getElementById('folder-status-summary');
        if (!el) return;
        el.setAttribute('data-i18n', textKey);
        el.textContent = t(textKey);
        el.className = 'auto-status-pill' + (cls ? ' ' + cls : '');
    }

    function showOnly(panelId) {
        ['folder-unsupported', 'folder-empty', 'folder-active'].forEach((id) => {
            const el = document.getElementById(id);
            if (el) el.style.display = id === panelId ? '' : 'none';
        });
    }

    function fmtTime(d) {
        if (!d) return '-';
        const dt = d instanceof Date ? d : new Date(d);
        const hh = String(dt.getHours()).padStart(2, '0');
        const mm = String(dt.getMinutes()).padStart(2, '0');
        const ss = String(dt.getSeconds()).padStart(2, '0');
        return `${hh}:${mm}:${ss}`;
    }

    function renderActive() {
        showOnly('folder-active');
        const pathEl = document.getElementById('folder-config-path');
        if (pathEl && _dirHandle) pathEl.textContent = _dirHandle.name || '-';
        const intervalSel = document.getElementById('folder-interval-select');
        if (intervalSel) intervalSel.value = String(_intervalSec);

        document.getElementById('folder-stat-last').textContent = _lastScanAt
            ? fmtTime(_lastScanAt)
            : '-';
        document.getElementById('folder-stat-processed').textContent = String(_processedCount);
        document.getElementById('folder-stat-failed').textContent = String(_failedCount);
        document.getElementById('folder-stat-queue').textContent = String(_queueCount);

        const pauseBtn = document.getElementById('btn-folder-pause');
        const resumeBtn = document.getElementById('btn-folder-resume');
        if (pauseBtn) pauseBtn.style.display = _paused ? 'none' : '';
        if (resumeBtn) resumeBtn.style.display = _paused ? '' : 'none';

        // status pill
        if (_paused) setStatus('folder-status-paused', 'paused');
        else setStatus('folder-status-running', 'running');

        // status text in config card
        const statusTextEl = document.getElementById('folder-status-text');
        if (statusTextEl) {
            statusTextEl.setAttribute(
                'data-i18n',
                _paused ? 'folder-status-paused' : 'folder-status-running'
            );
            statusTextEl.textContent = t(
                _paused ? 'folder-status-paused' : 'folder-status-running'
            );
        }
        const pulseEl = document.getElementById('folder-status-pulse');
        if (pulseEl) pulseEl.className = 'folder-status-pulse' + (_paused ? ' paused' : '');

        renderRecent();
    }

    function renderRecent() {
        const listEl = document.getElementById('folder-recent-list');
        if (!listEl) return;
        if (_recent.length === 0) {
            listEl.innerHTML = `<div class="folder-recent-empty">${escapeHtml(t('folder-recent-empty'))}</div>`;
            return;
        }
        listEl.innerHTML = _recent
            .slice(0, 20)
            .map((r) => {
                // v101 · Bug 1 · 支持 dup / skip 两种新状态
                let icon;
                if (r.status === 'ok') {
                    icon = `<span class="folder-recent-icon ok">${svgIcon('check', 12)}</span>`;
                } else if (r.status === 'dup') {
                    icon = `<span class="folder-recent-icon dup" title="${escapeHtml(t('folder-recent-dup'))}">${svgIcon('copy', 12)}</span>`;
                } else if (r.status === 'skip') {
                    icon = `<span class="folder-recent-icon skip" title="${escapeHtml(t('folder-recent-skip'))}">${svgIcon('minus', 12)}</span>`;
                } else {
                    icon = `<span class="folder-recent-icon fail">${svgIcon('alert', 12)}</span>`;
                }
                const subTxt =
                    r.status === 'fail' && r.error
                        ? r.error
                        : r.status === 'dup' && r.reason
                          ? r.reason
                          : r.status === 'skip' && r.reason
                            ? r.reason
                            : '';
                const subHtml = subTxt
                    ? `<div class="folder-recent-err">${escapeHtml(subTxt)}</div>`
                    : '';
                return `
                <div class="folder-recent-item">
                    ${icon}
                    <div class="folder-recent-body">
                        <div class="folder-recent-name">${escapeHtml(r.name)}</div>
                        ${subHtml}
                    </div>
                    <div class="folder-recent-time">${fmtTime(r.time)}</div>
                </div>
            `;
            })
            .join('');
    }

    function pushRecent(item) {
        _recent.unshift(item);
        if (_recent.length > 50) _recent.length = 50;
        // v101 · Bug 3 修复 · 持久化到 IndexedDB · 切页/刷新不丢
        idbPut('config', 'recent_list', _recent).catch(() => {});
    }

    // ---------- 上传单个文件 ----------
    async function uploadOne(file) {
        const fd = new FormData();
        fd.append('file', file, file.name);
        fd.append('source', 'folder');
        // v101 · Bug 2 对冲 · 后端可能只从 query/header 读 source
        const resp = await fetch('/api/ocr/recognize?source=folder', {
            method: 'POST',
            headers: {
                Authorization: 'Bearer ' + token,
                'X-Source': 'folder',
            },
            body: fd,
        });
        if (!resp.ok) {
            let errCode = 'http_' + resp.status;
            try {
                const j = await resp.json();
                errCode =
                    j && j.detail
                        ? typeof j.detail === 'string'
                            ? j.detail
                            : j.detail.code || JSON.stringify(j.detail)
                        : errCode;
            } catch {}
            throw new Error(errCode);
        }
        return await resp.json();
    }

    // ---------- 等文件写完(检测 size 不变 3s)----------
    async function isFileStable(handle) {
        try {
            const f1 = await handle.getFile();
            const s1 = f1.size;
            await new Promise((r) => setTimeout(r, 3000));
            const f2 = await handle.getFile();
            return f2.size === s1 && s1 > 0;
        } catch {
            return false;
        }
    }

    // v118.24 · 递归遍历目录 · 子文件夹也扫
    async function walkDir(handle, prefix, candidates, depth) {
        if (depth > 10) return; // 防深度爆栈
        let perm;
        try {
            perm = await handle.queryPermission({ mode: 'read' });
        } catch {
            perm = 'denied';
        }
        if (perm !== 'granted') return;
        for await (const entry of handle.values()) {
            const relPath = prefix ? `${prefix}/${entry.name}` : entry.name;
            if (entry.kind === 'file') {
                if (!VALID_EXTS.test(entry.name)) continue;
                let f;
                try {
                    f = await entry.getFile();
                } catch {
                    continue;
                }
                // seenKey 含相对路径 · 避免不同子文件夹同名文件互相误判
                const seenKey = `${relPath}::${f.size}::${f.lastModified}`;
                const seen = await idbGet('seen', seenKey);
                if (seen) continue;
                candidates.push({ entry, file: f, seenKey, relPath });
            } else if (entry.kind === 'directory') {
                try {
                    await walkDir(entry, relPath, candidates, depth + 1);
                } catch (e) {
                    /* 单个子目录失败不影响整体 */
                }
            }
        }
    }

    // ---------- 扫描循环 ----------
    async function scanOnce() {
        if (_scanning || _paused || !_dirHandle) return;
        _scanning = true;
        try {
            // 检查权限是否还在
            const perm = await _dirHandle.queryPermission({ mode: 'read' });
            if (perm !== 'granted') {
                console.warn('[folder] permission lost · stop');
                stop();
                showToast('warn', t('folder-permission-lost'));
                return;
            }

            _lastScanAt = new Date();
            const candidates = [];
            // v118.24 · 递归扫描子文件夹
            await walkDir(_dirHandle, '', candidates, 0);
            _queueCount = candidates.length;
            renderActive();

            for (const c of candidates) {
                if (_paused) break;
                // 等文件写完
                const stable = await isFileStable(c.entry);
                if (!stable) {
                    // 下次扫描再处理
                    _queueCount = Math.max(0, _queueCount - 1);
                    renderActive();
                    continue;
                }
                try {
                    let freshFile;
                    try {
                        freshFile = await c.entry.getFile();
                    } catch {
                        freshFile = c.file;
                    }
                    const result = await uploadOne(freshFile);
                    await idbPut('seen', c.seenKey, {
                        name: freshFile.name,
                        relPath: c.relPath,
                        size: freshFile.size,
                        lastModified: freshFile.lastModified,
                        processed_at: Date.now(),
                    });
                    // v101 · Bug 1 修复 · 按真实新增数计数
                    const newIds =
                        result.history_ids || (result.history_id ? [result.history_id] : []);
                    const dupWarnings = result.duplicate_warnings || [];
                    // v118.24 · 显示用相对路径 · 让用户看到子文件夹来源
                    const displayName = c.relPath || freshFile.name;
                    if (newIds.length > 0) {
                        _processedCount += newIds.length;
                        pushRecent({
                            name: displayName,
                            status: 'ok',
                            time: new Date(),
                            history_id: newIds[0],
                            count: newIds.length,
                        });
                        await idbPut('config', 'processed_count', _processedCount);
                    } else if (dupWarnings.length > 0) {
                        pushRecent({
                            name: displayName,
                            status: 'dup',
                            time: new Date(),
                            reason: t('folder-recent-dup-reason'),
                        });
                    } else {
                        pushRecent({
                            name: displayName,
                            status: 'skip',
                            time: new Date(),
                            reason: t('folder-recent-skip-reason'),
                        });
                    }
                } catch (err) {
                    _failedCount++;
                    pushRecent({
                        name: c.relPath || c.file.name,
                        status: 'fail',
                        time: new Date(),
                        error: String(err.message || err),
                    });
                    // 不写 seen · 下次重试
                    await idbPut('config', 'failed_count', _failedCount);
                }
                _queueCount = Math.max(0, _queueCount - 1);
                renderActive();
            }
        } catch (e) {
            console.warn('[folder] scan error:', e);
        } finally {
            _scanning = false;
            renderActive();
        }
    }

    function startTimer() {
        if (_intervalId) clearInterval(_intervalId);
        _intervalId = setInterval(scanOnce, _intervalSec * 1000);
    }
    function stopTimer() {
        if (_intervalId) {
            clearInterval(_intervalId);
            _intervalId = null;
        }
    }

    // v118.24 · 浏览器关闭警告 · 监听运行时阻止意外关闭
    function _unloadHandler(e) {
        if (!_dirHandle || _paused) return;
        const msg =
            typeof t === 'function'
                ? t('folder-unload-warn')
                : 'Folder watcher running · close anyway?';
        e.preventDefault();
        e.returnValue = msg; // 现代浏览器忽略自定义文案 · 仍触发原生确认框
        return msg;
    }
    function attachUnloadGuard() {
        if (window._pearnlyFolderUnloadAttached) return;
        window._pearnlyFolderUnloadAttached = true;
        window.addEventListener('beforeunload', _unloadHandler);
    }
    function detachUnloadGuard() {
        if (!window._pearnlyFolderUnloadAttached) return;
        window._pearnlyFolderUnloadAttached = false;
        window.removeEventListener('beforeunload', _unloadHandler);
    }

    function start() {
        _paused = false;
        startTimer();
        attachUnloadGuard();
        renderActive();
        // 立刻扫一次
        scanOnce();
    }
    function pause() {
        _paused = true;
        stopTimer();
        detachUnloadGuard();
        renderActive();
    }
    function resume() {
        _paused = false;
        startTimer();
        attachUnloadGuard();
        renderActive();
        scanOnce();
    }
    function stop() {
        _paused = true;
        stopTimer();
        detachUnloadGuard();
    }

    async function pickFolder() {
        try {
            const handle = await window.showDirectoryPicker({ mode: 'read', startIn: 'documents' });
            const ok = await ensurePermission(handle);
            if (!ok) {
                showToast('warn', t('folder-permission-denied'));
                return;
            }
            _dirHandle = handle;
            await idbPut('handles', 'main', handle);
            _processedCount = 0;
            _failedCount = 0;
            _queueCount = 0;
            _recent = [];
            await idbPut('config', 'processed_count', 0);
            await idbPut('config', 'failed_count', 0);
            await idbClear('seen');
            start();
        } catch (e) {
            // 用户取消选择 · 静默
            if (e && e.name !== 'AbortError') console.warn('[folder] pick failed:', e);
        }
    }

    async function removeFolder() {
        const ok = await showConfirm(t('folder-confirm-remove'), { danger: true });
        if (!ok) return;
        stop();
        _dirHandle = null;
        _processedCount = 0;
        _failedCount = 0;
        _queueCount = 0;
        _recent = [];
        await idbDel('handles', 'main');
        await idbDel('config', 'processed_count');
        await idbDel('config', 'failed_count');
        await idbClear('seen');
        showOnly('folder-empty');
        setStatus('folder-status-empty', '');
    }

    async function clearRecent() {
        _recent = [];
        // v101 · Bug 3 · 清空时也清掉持久化
        try {
            await idbDel('config', 'recent_list');
        } catch {}
        renderRecent();
    }

    // ---------- 加载 ----------
    async function load() {
        if (_loaded) return;
        _loaded = true;

        if (!SUPPORTED) {
            showOnly('folder-unsupported');
            setStatus('folder-status-unsupported', '');
            wireUnsupported();
            return;
        }

        wire();

        // 尝试恢复
        let savedHandle = null;
        try {
            savedHandle = await idbGet('handles', 'main');
        } catch {}
        if (!savedHandle) {
            showOnly('folder-empty');
            setStatus('folder-status-empty', '');
            return;
        }
        const ok = await ensurePermission(savedHandle);
        if (!ok) {
            // 权限丢了 · 但 handle 还在 · 给用户一个「重新授权」按钮
            // 简化:直接提示重选
            showOnly('folder-empty');
            setStatus('folder-status-empty', '');
            await idbDel('handles', 'main');
            showToast('warn', t('folder-permission-lost-restart'));
            return;
        }
        _dirHandle = savedHandle;
        try {
            _processedCount = (await idbGet('config', 'processed_count')) || 0;
        } catch {}
        try {
            _failedCount = (await idbGet('config', 'failed_count')) || 0;
        } catch {}
        // v101 · Bug 3 修复 · 恢复最近处理列表 · 切页/刷新不丢
        try {
            const saved = await idbGet('config', 'recent_list');
            if (Array.isArray(saved)) {
                // 反序列化:time 字段可能是字符串 · 转回 Date
                _recent = saved.map((r) => ({
                    ...r,
                    time: r.time ? new Date(r.time) : new Date(),
                }));
            }
        } catch {}
        start();
    }

    function wire() {
        const pickBtn = document.getElementById('btn-folder-pick');
        const pauseBtn = document.getElementById('btn-folder-pause');
        const resumeBtn = document.getElementById('btn-folder-resume');
        const scanBtn = document.getElementById('btn-folder-scan-now');
        const removeBtn = document.getElementById('btn-folder-remove');
        const clearBtn = document.getElementById('btn-folder-clear-recent');
        const intervalSel = document.getElementById('folder-interval-select');

        if (pickBtn) pickBtn.addEventListener('click', pickFolder);
        if (pauseBtn) pauseBtn.addEventListener('click', pause);
        if (resumeBtn) resumeBtn.addEventListener('click', resume);
        if (scanBtn)
            scanBtn.addEventListener('click', () => {
                scanOnce();
            });
        if (removeBtn) removeBtn.addEventListener('click', removeFolder);
        if (clearBtn) clearBtn.addEventListener('click', clearRecent);
        if (intervalSel)
            intervalSel.addEventListener('change', (e) => {
                _intervalSec = parseInt(e.target.value, 10) || 60;
                if (!_paused) startTimer();
            });
        // v98 · folder-empty 卡片 + folder-unsupported 卡片里所有 [data-tab-jump]
        wireTabJump();
    }

    function wireTabJump() {
        document.querySelectorAll('[data-auto-panel="folder"] [data-tab-jump]').forEach((btn) => {
            if (btn.dataset.tabJumpBound) return;
            btn.dataset.tabJumpBound = '1';
            btn.addEventListener('click', (e) => {
                const target = e.currentTarget.dataset.tabJump;
                if (target === 'email') {
                    if (typeof switchAutomationTab === 'function') switchAutomationTab('email');
                } else if (target === 'upload') {
                    const navUpload =
                        document.querySelector('[data-page="recognize"]') ||
                        document.querySelector('[data-page="upload"]');
                    if (navUpload) navUpload.click();
                }
            });
        });
    }

    function wireUnsupported() {
        // v98 · 老接口保留 · 内部走 wireTabJump 全局绑
        wireTabJump();
    }

    window._loadFolderWatcherPanel = load;

    // v118.24 · Chromium 浏览器检测 + 顶部 banner(非 Chromium 系一次性提示)
    function _isChromium() {
        try {
            if (navigator.userAgentData && Array.isArray(navigator.userAgentData.brands)) {
                return navigator.userAgentData.brands.some((b) =>
                    /chromium|google chrome|microsoft edge/i.test(b.brand || '')
                );
            }
        } catch {}
        const ua = navigator.userAgent || '';
        if (/Edg\//.test(ua)) return true; // Edge (Chromium)
        if (/Chrome\//.test(ua) && !/OPR\/|YaBrowser|Opera/.test(ua)) return true; // Chrome
        return false;
    }
    function _showChromeBanner() {
        try {
            if (_isChromium()) return;
            if (localStorage.getItem('pearnly_chrome_banner_dismissed') === '1') return;
            const el = document.getElementById('chrome-only-banner');
            if (!el) return;
            const msgEl = el.querySelector('[data-i18n="chrome-banner-msg"]');
            const btnEl = el.querySelector('[data-i18n="chrome-banner-dismiss"]');
            if (msgEl && typeof t === 'function') msgEl.textContent = t('chrome-banner-msg');
            if (btnEl && typeof t === 'function') btnEl.textContent = t('chrome-banner-dismiss');
            el.style.display = '';
            const closeBtn = document.getElementById('chrome-only-banner-close');
            if (closeBtn && !closeBtn.dataset.bound) {
                closeBtn.dataset.bound = '1';
                closeBtn.addEventListener('click', () => {
                    el.style.display = 'none';
                    try {
                        localStorage.setItem('pearnly_chrome_banner_dismissed', '1');
                    } catch {}
                });
            }
        } catch (e) {
            /* 静默 */
        }
    }
    // 主页面加载后 + 切语言后都触发(让文案跟随当前语言)
    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', _showChromeBanner);
        } else {
            setTimeout(_showChromeBanner, 0);
        }
    }
    window._refreshChromeBanner = _showChromeBanner;
})();
