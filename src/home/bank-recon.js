/* eslint-disable no-useless-assignment -- verbatim home.js · 防御式初始化 · 非 bug */
// ============================================================
// REFACTOR-C1 (2026-05-27) · 银行对账模块(M10)bank-recon 从 home.js 抽出为 ES module
//
// 来源:home.js L6764-7819 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================
/* global token, showConfirm */
// ============================================================
// v0.18 · M10 · 银行对账模块
// ============================================================
(function () {
    // 状态
    let _sessions = [];
    let _currentSession = null;
    let _currentTxs = [];
    let _currentFilter = 'all';
    let _currentTxForDrawer = null;
    let _loaded = false;

    async function load() {
        if (_loaded) {
            refreshSummary();
            return;
        }
        _loaded = true;
        bindEvents();
        await refreshSessions();
        refreshSummary();
    }

    function bindEvents() {
        // 上传(v118.26.1 · 批量)
        const input = document.getElementById('bank-file-input');
        if (input && !input._bound) {
            input._bound = true;
            input.addEventListener('change', handleFilePick);
        }
        // 清除已完成队列
        const btnClear = document.getElementById('btn-bank-queue-clear-done');
        if (btnClear && !btnClear._bound) {
            btnClear._bound = true;
            btnClear.addEventListener('click', _clearDone);
        }
        // 返回列表
        const btnBack = document.getElementById('btn-bank-back');
        if (btnBack && !btnBack._bound) {
            btnBack._bound = true;
            btnBack.addEventListener('click', () => {
                _currentSession = null;
                _currentTxs = [];
                showListMode();
            });
        }
        // 删除会话
        const btnDel = document.getElementById('btn-bank-delete');
        if (btnDel && !btnDel._bound) {
            btnDel._bound = true;
            btnDel.addEventListener('click', handleDeleteSession);
        }
        // 触发匹配
        const btnMatch = document.getElementById('btn-bank-run-match');
        if (btnMatch && !btnMatch._bound) {
            btnMatch._bound = true;
            btnMatch.addEventListener('click', handleRunMatch);
        }
        // 过滤按钮组(委托到容器)
        document.querySelectorAll('.bank-filter-btn').forEach((b) => {
            if (b._bound) return;
            b._bound = true;
            b.addEventListener('click', () => {
                _currentFilter = b.dataset.bankFilter || 'all';
                document.querySelectorAll('.bank-filter-btn').forEach((x) => {
                    x.classList.toggle('active', x === b);
                });
                renderTxTable();
            });
        });
        // 抽屉关闭(旧 fixed drawer · 保留兼容)
        document.querySelectorAll('[data-bank-cand-close]').forEach((e) => {
            if (e._bound) return;
            e._bound = true;
            e.addEventListener('click', closeCandDrawer);
        });
        // v118.26.2 · 新右半屏 pane 的 close 按钮(移动端 drawer 模式才显示)
        const btnPaneClose = document.getElementById('btn-bank-cand-pane-close');
        if (btnPaneClose && !btnPaneClose._bound) {
            btnPaneClose._bound = true;
            btnPaneClose.addEventListener('click', closeCandDrawer);
        }
        // 抽屉的忽略按钮(旧 + 新 pane)
        const btnIgn = document.getElementById('btn-bank-cand-ignore');
        if (btnIgn && !btnIgn._bound) {
            btnIgn._bound = true;
            btnIgn.addEventListener('click', handleIgnoreTx);
        }
        const btnIgnPane = document.getElementById('btn-bank-cand-ignore-pane');
        if (btnIgnPane && !btnIgnPane._bound) {
            btnIgnPane._bound = true;
            btnIgnPane.addEventListener('click', handleIgnoreTx);
        }
        // v118.26.2 · 客户徽章点击 · 老板可改 / 员工只读
        const badge = document.getElementById('bank-client-badge');
        if (badge && !badge._bound) {
            badge._bound = true;
            badge.addEventListener('click', _openClientPicker);
        }
        // v118.26.2 · 客户绑定 modal · close 按钮
        document.querySelectorAll('[data-bank-client-picker-close]').forEach((e) => {
            if (e._bound) return;
            e._bound = true;
            e.addEventListener('click', _closeClientPicker);
        });
        // v118.26.2 · 客户绑定 modal · 保存按钮
        const btnSave = document.getElementById('btn-bank-client-picker-save');
        if (btnSave && !btnSave._bound) {
            btnSave._bound = true;
            btnSave.addEventListener('click', _saveClientPicker);
        }
        // v118.26.1.1 · session list 顶部筛选 chip
        document.querySelectorAll('.bank-sessions-chip').forEach((b) => {
            if (b._bound) return;
            b._bound = true;
            b.addEventListener('click', () => {
                _sessionFilter = b.dataset.sessFilter || 'all';
                document.querySelectorAll('.bank-sessions-chip').forEach((x) => {
                    x.classList.toggle('active', x === b);
                });
                renderSessionList();
            });
        });
    }

    // ---------- API 调用 ----------
    async function refreshSessions() {
        try {
            const resp = await fetch('/api/bank-recon/sessions?limit=30', {
                headers: { Authorization: 'Bearer ' + token },
            });
            if (!resp.ok) throw new Error('sessions:' + resp.status);
            _sessions = await resp.json();
            renderSessionList();
        } catch (e) {
            console.warn('[bank-recon] loadSessions failed', e);
            _sessions = [];
            renderSessionList();
        }
    }

    async function loadSessionDetail(sessionId) {
        try {
            const url =
                '/api/bank-recon/sessions/' +
                encodeURIComponent(sessionId) +
                (_currentFilter !== 'all' ? '?filter=' + _currentFilter : '');
            const resp = await fetch(url, { headers: { Authorization: 'Bearer ' + token } });
            if (!resp.ok) throw new Error('detail:' + resp.status);
            const data = await resp.json();
            _currentSession = data.session;
            _currentTxs = data.transactions || [];
            showDetailMode();
        } catch (e) {
            console.warn('[bank-recon] loadSessionDetail failed', e);
            showToast(t('bank-load-failed'), 'error');
        }
    }

    // v118.26.1 · 批量上传:队列 + 并发 3 + 单文件重试
    // ----------------------------------------------------------
    // _queue:
    //   [{ id, file, status: 'pending'|'uploading'|'parsing'|'ok'|'failed', progress(0-100),
    //      error_code, tx_count, session_id }]
    let _queue = [];
    let _qSeq = 0;
    const QUEUE_CONCURRENCY = 3;

    function _qid() {
        _qSeq += 1;
        return 'q' + _qSeq + '_' + Date.now();
    }

    async function handleFilePick(e) {
        const files = Array.from(e.target.files || []);
        e.target.value = '';
        if (files.length === 0) return;

        // 校验 + 入队
        for (const f of files) {
            const item = {
                id: _qid(),
                file: f,
                name: f.name,
                size: f.size,
                status: 'pending',
                progress: 0,
                error_code: null,
                tx_count: 0,
                session_id: null,
            };
            if (!f.name.toLowerCase().endsWith('.pdf')) {
                item.status = 'failed';
                item.error_code = 'bank_recon.only_pdf';
            } else if (f.size > 20 * 1024 * 1024) {
                item.status = 'failed';
                item.error_code = 'bank_recon.file_too_large';
            }
            _queue.push(item);
        }
        showQueue();
        renderQueue();
        // 启动调度
        _drainQueue();
    }

    function showQueue() {
        const q = document.getElementById('bank-upload-queue');
        if (q) q.style.display = '';
        // 单文件遗留区隐藏(走队列 UI 即可)
        showBankProgress(false);
        hideBankError();
    }

    function renderQueue() {
        const list = document.getElementById('bank-upload-queue-list');
        const summary = document.getElementById('bank-upload-queue-summary');
        if (!list) return;

        if (_queue.length === 0) {
            list.innerHTML = '';
            if (summary) summary.textContent = '';
            const q = document.getElementById('bank-upload-queue');
            if (q) q.style.display = 'none';
            return;
        }

        // summary 文案
        let nDone = 0,
            nFail = 0,
            nRun = 0,
            nWait = 0;
        for (const it of _queue) {
            if (it.status === 'ok') nDone++;
            else if (it.status === 'failed') nFail++;
            else if (it.status === 'uploading' || it.status === 'parsing') nRun++;
            else nWait++;
        }
        if (summary) {
            summary.textContent = t('bank-queue-summary')
                .replace('{ok}', nDone)
                .replace('{run}', nRun)
                .replace('{wait}', nWait)
                .replace('{fail}', nFail);
        }

        list.innerHTML = _queue.map(_rowHtml).join('');
        // 绑定重试 / 移除按钮
        list.querySelectorAll('[data-q-act]').forEach((btn) => {
            const act = btn.dataset.qAct;
            const id = btn.dataset.qId;
            btn.addEventListener('click', () => {
                if (act === 'retry') _retryItem(id);
                if (act === 'remove') _removeItem(id);
            });
        });
    }

    function _rowHtml(it) {
        const sizeKb = (it.size / 1024).toFixed(0) + ' KB';
        let statusHtml = '';
        let actHtml = '';
        if (it.status === 'pending') {
            statusHtml = '<span class="bq-stat bq-wait">' + t('bank-queue-status-wait') + '</span>';
            actHtml =
                '<button data-q-act="remove" data-q-id="' +
                esc(it.id) +
                '" class="bq-act">×</button>';
        } else if (it.status === 'uploading') {
            statusHtml =
                '<span class="bq-stat bq-run">' +
                t('bank-queue-status-uploading') +
                '</span>' +
                '<div class="bq-bar"><div class="bq-bar-fill" style="width:' +
                (it.progress || 0) +
                '%"></div></div>';
        } else if (it.status === 'parsing') {
            statusHtml =
                '<span class="bq-stat bq-run">' +
                t('bank-queue-status-parsing') +
                '</span>' +
                '<div class="bq-bar"><div class="bq-bar-fill bq-bar-indet"></div></div>';
        } else if (it.status === 'ok') {
            statusHtml =
                '<span class="bq-stat bq-ok">' +
                t('bank-queue-status-ok').replace('{n}', it.tx_count || 0) +
                '</span>';
            actHtml =
                '<button data-q-act="remove" data-q-id="' +
                esc(it.id) +
                '" class="bq-act">×</button>';
        } else if (it.status === 'failed') {
            const msg = formatUploadError(it.error_code || 'unknown');
            statusHtml =
                '<span class="bq-stat bq-fail" title="' + esc(msg) + '">' + esc(msg) + '</span>';
            actHtml =
                '<button data-q-act="retry" data-q-id="' +
                esc(it.id) +
                '" class="bq-act bq-act-retry">' +
                t('bank-queue-retry') +
                '</button>' +
                '<button data-q-act="remove" data-q-id="' +
                esc(it.id) +
                '" class="bq-act">×</button>';
        }
        return (
            '<div class="bq-row" data-q-row="' +
            esc(it.id) +
            '">' +
            '<div class="bq-name" title="' +
            esc(it.name) +
            '">' +
            esc(it.name) +
            '</div>' +
            '<div class="bq-size">' +
            sizeKb +
            '</div>' +
            '<div class="bq-status">' +
            statusHtml +
            '</div>' +
            '<div class="bq-actions">' +
            actHtml +
            '</div>' +
            '</div>'
        );
    }

    function _retryItem(id) {
        const it = _queue.find((x) => x.id === id);
        if (!it) return;
        it.status = 'pending';
        it.error_code = null;
        it.progress = 0;
        renderQueue();
        _drainQueue();
    }

    function _removeItem(id) {
        const idx = _queue.findIndex((x) => x.id === id);
        if (idx < 0) return;
        const it = _queue[idx];
        // 跑着的不能直接移除(防中断)· 只能完成态/排队态
        if (it.status === 'uploading' || it.status === 'parsing') return;
        _queue.splice(idx, 1);
        renderQueue();
    }

    function _clearDone() {
        _queue = _queue.filter((x) => x.status !== 'ok');
        renderQueue();
    }

    async function _drainQueue() {
        while (true) {
            const running = _queue.filter(
                (x) => x.status === 'uploading' || x.status === 'parsing'
            ).length;
            if (running >= QUEUE_CONCURRENCY) return;
            const next = _queue.find((x) => x.status === 'pending');
            if (!next) {
                // 全部跑完一轮 · 刷一次 sessions 列表
                if (_queue.every((x) => x.status === 'ok' || x.status === 'failed')) {
                    await refreshSessions();
                    if (typeof window.loadReconcilePage === 'function') {
                        window.loadReconcilePage();
                    }
                }
                return;
            }
            // 启动一个上传(不 await · 让循环继续抓下一个)
            _runOne(next).then(() => _drainQueue());
            // 立刻继续看能不能再开下一个并发
        }
    }

    async function _runOne(it) {
        it.status = 'uploading';
        it.progress = 0;
        renderQueue();

        try {
            // 用 XHR 拿上传进度;后端处理是同步的(解析阻塞返回) · 上传完后切 'parsing' 等响应
            const fd = new FormData();
            fd.append('file', it.file, it.name);
            const respText = await new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();
                xhr.open('POST', '/api/bank-recon/upload');
                xhr.setRequestHeader('Authorization', 'Bearer ' + token);
                xhr.upload.onprogress = (ev) => {
                    if (ev.lengthComputable) {
                        it.progress = Math.min(99, Math.round((ev.loaded / ev.total) * 100));
                        renderQueue();
                    }
                };
                xhr.upload.onload = () => {
                    it.status = 'parsing';
                    renderQueue();
                };
                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300)
                        resolve({ status: xhr.status, text: xhr.responseText });
                    else resolve({ status: xhr.status, text: xhr.responseText }); // 不 reject · 业务错误也走解析
                };
                xhr.onerror = () => reject(new Error('network'));
                xhr.send(fd);
            });

            let body = {};
            try {
                body = JSON.parse(respText.text || '{}');
            } catch (_) {
                body = {};
            }

            if (respText.status >= 400) {
                it.status = 'failed';
                it.error_code = (body && body.detail) || 'unknown';
                renderQueue();
                return;
            }
            if (body.parse_status === 'parse_failed') {
                it.status = 'failed';
                it.error_code =
                    body.error === 'scanned_pdf_not_yet'
                        ? 'bank_recon.scanned'
                        : 'bank_recon.no_tx';
                renderQueue();
                return;
            }
            it.status = 'ok';
            it.tx_count = body.tx_count || 0;
            it.session_id = body.session_id || null;
            renderQueue();
        } catch (e) {
            console.warn('[bank-recon] upload failed', e);
            it.status = 'failed';
            it.error_code = 'network';
            renderQueue();
        }
    }

    async function handleRunMatch() {
        if (!_currentSession) return;
        const btn = document.getElementById('btn-bank-run-match');
        const origHTML = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span>' + t('bank-matching') + '</span>';
        try {
            const resp = await fetch(
                '/api/bank-recon/sessions/' + encodeURIComponent(_currentSession.id) + '/match',
                {
                    method: 'POST',
                    headers: { Authorization: 'Bearer ' + token },
                }
            );
            if (!resp.ok) throw new Error('match:' + resp.status);
            const stats = await resp.json();
            showToast(
                t('bank-match-done')
                    .replace('{matched}', stats.matched)
                    .replace('{suggested}', stats.suggested)
                    .replace('{unmatched}', stats.unmatched),
                'success'
            );
            // 刷详情
            await loadSessionDetail(_currentSession.id);
            await refreshSessions();
        } catch (e) {
            console.warn('[bank-recon] match failed', e);
            showToast(t('bank-match-failed'), 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = origHTML;
        }
    }

    async function handleDeleteSession() {
        if (!_currentSession) return;
        const ok = await showConfirm(t('bank-delete-confirm'), { danger: true });
        if (!ok) return;
        try {
            const resp = await fetch(
                '/api/bank-recon/sessions/' + encodeURIComponent(_currentSession.id),
                {
                    method: 'DELETE',
                    headers: { Authorization: 'Bearer ' + token },
                }
            );
            if (!resp.ok) throw new Error('delete:' + resp.status);
            showToast(t('bank-deleted'), 'success');
            _currentSession = null;
            _currentTxs = [];
            showListMode();
            await refreshSessions();
        } catch (e) {
            console.warn('[bank-recon] delete failed', e);
            showToast(t('bank-delete-failed'), 'error');
        }
    }

    async function handleIgnoreTx() {
        if (!_currentTxForDrawer) return;
        try {
            const resp = await fetch(
                '/api/bank-recon/tx/' + encodeURIComponent(_currentTxForDrawer.id) + '/override',
                {
                    method: 'POST',
                    headers: {
                        Authorization: 'Bearer ' + token,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ status: 'ignored' }),
                }
            );
            if (!resp.ok) throw new Error('ignore:' + resp.status);
            closeCandDrawer();
            await loadSessionDetail(_currentSession.id);
        } catch (e) {
            showToast(t('bank-action-failed'), 'error');
        }
    }

    async function handlePickCandidate(historyId) {
        if (!_currentTxForDrawer) return;
        try {
            const resp = await fetch(
                '/api/bank-recon/tx/' + encodeURIComponent(_currentTxForDrawer.id) + '/override',
                {
                    method: 'POST',
                    headers: {
                        Authorization: 'Bearer ' + token,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ status: 'matched', history_id: historyId }),
                }
            );
            if (!resp.ok) throw new Error('pick:' + resp.status);
            showToast(t('bank-matched-ok'), 'success');
            closeCandDrawer();
            await loadSessionDetail(_currentSession.id);
        } catch (e) {
            showToast(t('bank-action-failed'), 'error');
        }
    }

    // ---------- 渲染 ----------
    function refreshSummary() {
        const pill = document.getElementById('bank-status-summary');
        if (!pill) return;
        const total = _sessions.length;
        if (total === 0) {
            pill.textContent = t('bank-pill-none');
            return;
        }
        // 统计未完全匹配的
        let pending = 0;
        for (const s of _sessions) {
            if (s.parse_status === 'parsed' && (s.unmatched_count || 0) > 0) pending++;
        }
        pill.textContent =
            pending > 0 ? t('bank-pill-pending').replace('{n}', pending) : t('bank-pill-ok');
    }

    // v118.26.1.1 · 列表筛选状态 · 'all' / 'parsed' / 'failed'
    let _sessionFilter = 'all';

    function renderSessionList() {
        const list = document.getElementById('bank-sessions-list');
        if (!list) return;
        // 筛选
        let visible = _sessions || [];
        if (_sessionFilter === 'parsed') {
            visible = visible.filter((s) => s.parse_status === 'parsed');
        } else if (_sessionFilter === 'failed') {
            visible = visible.filter((s) => s.parse_status === 'parse_failed');
        }
        if (!_sessions || _sessions.length === 0) {
            list.innerHTML =
                '<div class="bank-empty" data-i18n="bank-sessions-empty">' +
                t('bank-sessions-empty') +
                '</div>';
            return;
        }
        if (visible.length === 0) {
            list.innerHTML = '<div class="bank-empty">' + t('bank-sess-filter-empty') + '</div>';
            return;
        }
        list.innerHTML = visible.map((s) => renderSessionRow(s)).join('');
        // 行点击 → 进会话详情 · 但点垃圾桶不能触发
        list.querySelectorAll('.bank-session-row').forEach((row) => {
            row.addEventListener('click', (e) => {
                if (e.target.closest('.bank-session-trash')) return; // 点的是垃圾桶 · 跳过
                loadSessionDetail(row.dataset.sessionId);
            });
        });
        // 垃圾桶绑定
        list.querySelectorAll('.bank-session-trash').forEach((btn) => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const sid = btn.dataset.sessionId;
                const fname = btn.dataset.sessionName || '';
                handleDeleteSessionFromList(sid, fname);
            });
        });
    }

    // v118.26.1.1 · 共用删除函数 · 自动化 tab 列表 + 对账中心列表都用
    async function handleDeleteSessionFromList(sessionId, fname) {
        if (!sessionId) return;
        const msg = (t('bank-session-delete-confirm') || '确定删除这条对账记录吗?').replace(
            '{name}',
            fname || ''
        );
        const ok = await showConfirm(msg, { danger: true });
        if (!ok) return;
        try {
            const resp = await fetch('/api/bank-recon/sessions/' + encodeURIComponent(sessionId), {
                method: 'DELETE',
                headers: { Authorization: 'Bearer ' + token },
            });
            if (!resp.ok) throw new Error('delete:' + resp.status);
            showToast(t('bank-deleted'), 'success');
            // 如果当前正打开这个会话 · 退回列表
            if (_currentSession && _currentSession.id === sessionId) {
                _currentSession = null;
                _currentTxs = [];
                showListMode();
            }
            await refreshSessions();
            // 对账中心首页也刷
            if (typeof window.loadReconcilePage === 'function') {
                window.loadReconcilePage();
            }
        } catch (e) {
            console.warn('[bank-recon] delete failed', e);
            showToast(t('bank-delete-failed'), 'error');
        }
    }
    // 暴露给对账中心首页用
    window._deleteBankSession = handleDeleteSessionFromList;

    function renderSessionRow(s) {
        const bank = (s.bank_code || 'OTHER').toUpperCase();
        const period = formatPeriod(s.period_start, s.period_end);
        const acct = s.account_last4 ? '···' + s.account_last4 : '';
        const counts = renderSessionCounts(s);
        const dateStr = formatDate(s.created_at);
        return `
            <div class="bank-session-row" data-session-id="${esc(s.id)}">
                <div class="bank-session-bank bk-${esc(bank)}">${esc(bank)}</div>
                <div class="bank-session-info">
                    <div class="bank-session-title">${esc(s.source_filename || period || '-')}</div>
                    <div class="bank-session-meta">${esc(period)} · ${esc(acct)} · ${esc(dateStr)}</div>
                </div>
                <div class="bank-session-counts">${counts}</div>
                <button class="bank-session-trash" data-session-id="${esc(s.id)}" data-session-name="${esc(s.source_filename || '')}" title="${esc(t('bank-session-delete-tip') || '删除')}">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/>
                    </svg>
                </button>
                <div class="bank-session-arrow">
                    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg>
                </div>
            </div>
        `;
    }

    function renderSessionCounts(s) {
        if (s.parse_status === 'parse_failed') {
            return `<span class="bank-session-count cnt-failed">${t('bank-count-parse-failed')}</span>`;
        }
        if (s.parse_status !== 'parsed') {
            return `<span class="bank-session-count">${t('bank-count-parsing')}</span>`;
        }
        const total = s.tx_count || 0;
        const matched = s.matched_count || 0;
        const unmatched = s.unmatched_count || 0;
        const parts = [`<span class="bank-session-count">${total} ${t('bank-count-tx')}</span>`];
        if (matched > 0)
            parts.push(
                `<span class="bank-session-count cnt-matched">${matched} ${t('bank-count-matched')}</span>`
            );
        if (unmatched > 0)
            parts.push(
                `<span class="bank-session-count cnt-unmatched">${unmatched} ${t('bank-count-unmatched')}</span>`
            );
        return parts.join('');
    }

    function showDetailMode() {
        document.getElementById('bank-detail').style.display = '';
        document.querySelector('.bank-sessions-section').style.display = 'none';
        renderDetailMeta();
        renderTxTable();
        // v118.26.2 · 渲染客户徽章
        _renderClientBadge();
    }

    function showListMode() {
        document.getElementById('bank-detail').style.display = 'none';
        document.querySelector('.bank-sessions-section').style.display = '';
        // v118.26.2 · 退出 detail 顺手关 pane(切回列表不残留)
        const detailBody = document.getElementById('bank-detail-body');
        if (detailBody) detailBody.classList.remove('has-pane');
        _currentTxForDrawer = null;
    }

    // v118.26.2 · 客户徽章渲染 · 老板可点改 / 员工只读
    function _renderClientBadge() {
        const badge = document.getElementById('bank-client-badge');
        if (!badge || !_currentSession) return;
        const cid = _currentSession.client_id;
        const dot = document.getElementById('bank-client-badge-dot');
        const name = document.getElementById('bank-client-badge-name');
        const caret = document.getElementById('bank-client-badge-caret');
        // v118.26.2.1 · _userInfo 是文件顶层 let · 不在 window 上 · 直接读
        const u = typeof _userInfo !== 'undefined' ? _userInfo : null;
        const isOwnerLike = !(u && u.role === 'member');

        if (cid != null) {
            const c = (window._clientsCache || []).find((x) => Number(x.id) === Number(cid));
            badge.classList.remove('is-empty');
            if (dot) dot.style.background = (c && c.color) || '#111111';
            if (name) name.textContent = (c && (c.short_name || c.name)) || '#' + cid;
        } else {
            badge.classList.add('is-empty');
            if (dot) dot.style.background = '';
            if (name) name.textContent = t('bank-client-none');
        }

        // 员工只读 · 老板可点
        if (isOwnerLike) {
            badge.classList.remove('is-readonly');
            badge.disabled = false;
            if (caret) caret.style.display = '';
        } else {
            badge.classList.add('is-readonly');
            badge.disabled = true;
            if (caret) caret.style.display = 'none';
        }
        badge.style.display = '';
    }

    // v118.26.2 · 客户绑定 modal · 打开
    let _pickerSelected = null; // 当前 modal 内选中的 client_id(null = 不绑定)
    function _openClientPicker() {
        if (!_currentSession) return;
        const u = typeof _userInfo !== 'undefined' ? _userInfo : null;
        const isOwnerLike = !(u && u.role === 'member');
        if (!isOwnerLike) return; // 员工没权限 · 直接 noop
        _pickerSelected =
            _currentSession.client_id != null ? Number(_currentSession.client_id) : null;
        _renderClientPickerList();
        const m = document.getElementById('bank-client-picker-modal');
        if (m) m.style.display = '';
    }

    function _closeClientPicker() {
        const m = document.getElementById('bank-client-picker-modal');
        if (m) m.style.display = 'none';
        _pickerSelected = null;
    }

    function _renderClientPickerList() {
        const list = document.getElementById('bank-client-picker-list');
        if (!list) return;
        const clients = (window._clientsCache || []).filter(
            (c) => c && (c.is_active === true || c.is_active === undefined)
        );
        const rows = [];
        // 「不绑定」一行
        rows.push(
            '<div class="bank-client-picker-row is-none' +
                (_pickerSelected == null ? ' is-selected' : '') +
                '" data-cid="">' +
                '<span class="bank-cp-dot"></span>' +
                '<span>' +
                esc(t('bank-client-picker-none')) +
                '</span>' +
                '</div>'
        );
        clients.forEach((c) => {
            const sel = Number(c.id) === Number(_pickerSelected) ? ' is-selected' : '';
            rows.push(
                '<div class="bank-client-picker-row' +
                    sel +
                    '" data-cid="' +
                    esc(c.id) +
                    '">' +
                    '<span class="bank-cp-dot" style="background:' +
                    esc(c.color || '#111111') +
                    '"></span>' +
                    '<span>' +
                    esc(c.short_name || c.name || '#' + c.id) +
                    '</span>' +
                    '</div>'
            );
        });
        list.innerHTML = rows.join('');
        list.querySelectorAll('.bank-client-picker-row').forEach((row) => {
            row.addEventListener('click', () => {
                const cid = row.dataset.cid;
                _pickerSelected = cid ? Number(cid) : null;
                _renderClientPickerList();
            });
        });
    }

    async function _saveClientPicker() {
        if (!_currentSession) return;
        try {
            const resp = await fetch(
                '/api/bank-recon/sessions/' + encodeURIComponent(_currentSession.id) + '/client',
                {
                    method: 'PATCH',
                    headers: {
                        Authorization: 'Bearer ' + token,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ client_id: _pickerSelected }),
                }
            );
            if (!resp.ok) throw new Error('client:' + resp.status);
            _currentSession.client_id = _pickerSelected;
            _renderClientBadge();
            showToast(t('bank-client-changed'), 'success');
            _closeClientPicker();
            // 顺手刷新会话列表(让列表也带新 client_id)
            try {
                await refreshSessions();
            } catch (_) {
                /* silent · 顺手刷新会话列表 */
            }
        } catch (e) {
            console.warn('[bank-recon] save client failed', e);
            showToast(t('bank-client-change-failed'), 'error');
        }
    }

    function renderDetailMeta() {
        if (!_currentSession) return;
        const s = _currentSession;
        document.getElementById('bank-detail-title').textContent =
            (s.bank_code || '-') +
            (s.account_last4 ? ' ···' + s.account_last4 : '') +
            ' · ' +
            (s.source_filename || '');
        document.getElementById('bank-meta-period').textContent =
            formatPeriod(s.period_start, s.period_end) || '-';
        document.getElementById('bank-meta-opening').textContent = fmtAmt(s.opening_balance);
        document.getElementById('bank-meta-inflow').textContent = '+' + fmtAmt(s.total_inflow);
        document.getElementById('bank-meta-outflow').textContent = '-' + fmtAmt(s.total_outflow);
        document.getElementById('bank-meta-closing').textContent = fmtAmt(s.closing_balance);

        // v118.26.1 · 4 个 chip 全部从 _currentTxs 实时数 · 不读 session 字段
        // (修上次发现的 bug:save_bank_recon_parse 没回写 unmatched_count · 顶部 chip 永远 0)
        const txs = _currentTxs || [];
        const total = txs.length;
        let nMatched = 0,
            nSuggested = 0,
            nUnmatched = 0;
        for (const x of txs) {
            const ms = x.match_status || 'unmatched';
            if (ms === 'matched') nMatched++;
            else if (ms === 'suggested') nSuggested++;
            else nUnmatched++; // unmatched + ignored 都计入未匹配
        }
        document.getElementById('bank-stat-total').textContent = total;
        document.getElementById('bank-stat-matched').textContent = nMatched;
        document.getElementById('bank-stat-suggested').textContent = nSuggested;
        document.getElementById('bank-stat-unmatched').textContent = nUnmatched;
    }

    function renderTxTable() {
        const tbody = document.getElementById('bank-tx-tbody');
        if (!tbody) return;
        let txs = _currentTxs || [];
        if (_currentFilter !== 'all') {
            txs = txs.filter((x) => {
                if (_currentFilter === 'matched') return x.match_status === 'matched';
                if (_currentFilter === 'suggested') return x.match_status === 'suggested';
                if (_currentFilter === 'unmatched')
                    return x.match_status === 'unmatched' || x.match_status === 'ignored';
                return true;
            });
        }
        if (txs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="bank-empty">${t('bank-tx-empty')}</td></tr>`;
            return;
        }
        tbody.innerHTML = txs.map((tx) => renderTxRow(tx)).join('');
        tbody.querySelectorAll('tr[data-tx-id]').forEach((row) => {
            row.addEventListener('click', () => {
                const id = row.dataset.txId;
                const tx = _currentTxs.find((x) => x.id === id);
                if (!tx) return;
                // v118.26.2 · 高亮选中行 · 切到新行清旧
                tbody
                    .querySelectorAll('tr.is-selected')
                    .forEach((r) => r.classList.remove('is-selected'));
                row.classList.add('is-selected');
                openCandDrawer(tx);
            });
        });
        // v118.26.2 · 重渲后保持上次选中(切 filter 不丢)
        if (_currentTxForDrawer) {
            const sel = tbody.querySelector('tr[data-tx-id="' + _currentTxForDrawer.id + '"]');
            if (sel) sel.classList.add('is-selected');
        }
    }

    function renderTxRow(tx) {
        const isOut = tx.direction === 'OUT';
        const sign = isOut ? '-' : '+';
        const cls = isOut ? 'bank-out' : 'bank-in';
        const status = tx.match_status || 'unmatched';
        const statusLabel = t('bank-match-' + status) || status;
        const date = formatDate(tx.tx_date);
        const channel = tx.channel ? `<span class="bank-tx-channel">${esc(tx.channel)}</span>` : '';
        return `
            <tr data-tx-id="${esc(tx.id)}">
                <td class="bank-tx-date">${esc(date)}</td>
                <td class="bank-tx-desc">${channel}${esc(tx.description || '-')}</td>
                <td class="bank-td-amount ${cls}">${sign}${fmtAmt(tx.amount)}</td>
                <td><span class="bank-tx-match mt-${status}">${esc(statusLabel)}</span></td>
            </tr>
        `;
    }

    // ---------- v118.26.2 · 右半屏候选 pane(取代旧 fixed drawer)----------
    async function openCandDrawer(tx) {
        _currentTxForDrawer = tx;
        // 切到 grid 双栏(桌面) · 移动端样式自动改成底部 drawer
        const detailBody = document.getElementById('bank-detail-body');
        if (detailBody) detailBody.classList.add('has-pane');

        const titleEl = document.getElementById('bank-cand-pane-title');
        const subEl = document.getElementById('bank-cand-pane-sub');
        const foot = document.getElementById('bank-cand-pane-foot');
        if (titleEl) titleEl.textContent = t('bank-cand-pane-current');
        if (subEl) {
            const sign = tx.direction === 'OUT' ? '-' : '+';
            const cls = tx.direction === 'OUT' ? 'bank-out' : 'bank-in';
            subEl.innerHTML = `${esc(formatDate(tx.tx_date))}
                <span style="margin:0 6px;color:#D1D5DB">·</span>
                <span>${esc(tx.description || '-')}</span>
                <span style="margin:0 6px;color:#D1D5DB">·</span>
                <strong class="${cls}">${sign}${fmtAmt(tx.amount)}</strong>`;
        }
        if (foot) foot.style.display = '';

        const body = document.getElementById('bank-cand-pane-body');
        if (!body) return;
        body.innerHTML = `<div class="bank-empty">${t('bank-cand-loading')}</div>`;

        // 拉 top 5 候选 + 发票字段
        try {
            const resp = await fetch(
                '/api/bank-recon/tx/' + encodeURIComponent(tx.id) + '/candidates',
                {
                    headers: { Authorization: 'Bearer ' + token },
                }
            );
            if (!resp.ok) throw new Error('cands:' + resp.status);
            const data = await resp.json();
            renderCandBody(tx, data.candidates || []);
        } catch (e) {
            body.innerHTML = `<div class="bank-empty">${t('bank-cand-load-failed')}</div>`;
        }
    }

    function _scoreBadge(score) {
        const n = Number(score || 0);
        let cls = 'score-low';
        if (n >= 85) cls = 'score-high';
        else if (n >= 60) cls = 'score-mid';
        return (
            '<span class="bank-cand-score ' +
            cls +
            '">' +
            n.toFixed(0) +
            ' ' +
            t('bank-cand-score-unit') +
            '</span>'
        );
    }

    function _candCard(tx, c, isCurrentMatched) {
        const hid = c.history_id;
        const inv = c.invoice_no || '-';
        const vendor = c.vendor || '-';
        const amt =
            c.amount_total !== null && c.amount_total !== undefined ? fmtAmt(c.amount_total) : '-';
        const idate = c.invoice_date ? formatDate(c.invoice_date) : '-';
        const fname = c.filename || '';

        const isPicked = !!isCurrentMatched && tx.matched_history_id === hid;
        const cardCls =
            'bank-cand-card' +
            (c.is_auto_picked ? ' is-auto' : '') +
            (isPicked ? ' is-picked' : '');

        let actHtml = '';
        if (isPicked) {
            actHtml =
                '<button class="btn btn-ghost btn-small" data-act="unmatch">' +
                '<span>' +
                t('bank-cand-unmatch') +
                '</span>' +
                '</button>';
        } else {
            actHtml =
                '<button class="btn btn-primary btn-small" data-act="pick" data-hid="' +
                esc(hid) +
                '">' +
                '<span>' +
                t(c.is_auto_picked ? 'bank-cand-confirm' : 'bank-cand-pick-this') +
                '</span>' +
                '</button>';
        }

        return (
            '<div class="' +
            cardCls +
            '" data-hid="' +
            esc(hid) +
            '">' +
            '<div class="bank-cand-card-head">' +
            '<div class="bank-cand-card-vendor">' +
            esc(vendor) +
            '</div>' +
            _scoreBadge(c.score) +
            '</div>' +
            '<div class="bank-cand-card-fields">' +
            '<span class="bank-cand-field"><span class="bank-cand-flabel">' +
            t('bank-cand-fld-invoice-no') +
            '</span> ' +
            esc(inv) +
            '</span>' +
            '<span class="bank-cand-field"><span class="bank-cand-flabel">' +
            t('bank-cand-fld-amount') +
            '</span> ' +
            amt +
            '</span>' +
            '<span class="bank-cand-field"><span class="bank-cand-flabel">' +
            t('bank-cand-fld-date') +
            '</span> ' +
            esc(idate) +
            '</span>' +
            '</div>' +
            (fname
                ? '<div class="bank-cand-card-file" title="' +
                  esc(fname) +
                  '">' +
                  esc(fname) +
                  '</div>'
                : '') +
            (c.reason ? '<div class="bank-cand-card-reason">' + esc(c.reason) + '</div>' : '') +
            '<div class="bank-cand-card-actions">' +
            actHtml +
            '</div>' +
            '</div>'
        );
    }

    function renderCandBody(tx, candidates) {
        // v118.26.2 · 渲染目标改成新 inline pane body
        const body = document.getElementById('bank-cand-pane-body');
        if (!body) return;
        const list = candidates || [];

        // 头部小提示:auto-picked / suggested / unmatched 三种状态
        let headHint = '';
        if (tx.match_status === 'matched') {
            headHint =
                '<div class="bank-cand-hint hint-matched">' +
                t('bank-cand-hint-matched').replace('{n}', list.length) +
                '</div>';
        } else if (tx.match_status === 'suggested') {
            headHint =
                '<div class="bank-cand-hint hint-suggested">' +
                t('bank-cand-hint-suggested').replace('{n}', list.length) +
                '</div>';
        } else if (list.length > 0) {
            headHint =
                '<div class="bank-cand-hint hint-low">' +
                t('bank-cand-hint-low').replace('{n}', list.length) +
                '</div>';
        } else {
            // 0 候选 · 空态卡片
            body.innerHTML = '<div class="bank-empty">' + t('bank-cand-no-match-detail') + '</div>';
            return;
        }

        const isMatched = tx.match_status === 'matched';
        const cards = list.map((c) => _candCard(tx, c, isMatched)).join('');
        body.innerHTML = headHint + '<div class="bank-cand-list">' + cards + '</div>';

        // 绑事件
        body.querySelectorAll('[data-act="pick"]').forEach((btn) => {
            btn.addEventListener('click', () => {
                handlePickCandidate(btn.dataset.hid);
            });
        });
        body.querySelectorAll('[data-act="unmatch"]').forEach((btn) => {
            btn.addEventListener('click', async () => {
                try {
                    await fetch('/api/bank-recon/tx/' + encodeURIComponent(tx.id) + '/override', {
                        method: 'POST',
                        headers: {
                            Authorization: 'Bearer ' + token,
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ status: 'unmatched' }),
                    });
                    closeCandDrawer();
                    await loadSessionDetail(_currentSession.id);
                } catch (e) {
                    showToast(t('bank-action-failed'), 'error');
                }
            });
        });
    }

    function closeCandDrawer() {
        // v118.26.2 · 关闭 = 从 grid 双栏退出 + 清空 pane + 取消行高亮
        const detailBody = document.getElementById('bank-detail-body');
        if (detailBody) detailBody.classList.remove('has-pane');
        const titleEl = document.getElementById('bank-cand-pane-title');
        const subEl = document.getElementById('bank-cand-pane-sub');
        const body = document.getElementById('bank-cand-pane-body');
        const foot = document.getElementById('bank-cand-pane-foot');
        if (titleEl) titleEl.textContent = t('bank-cand-pane-empty-title');
        if (subEl) subEl.textContent = t('bank-cand-pane-empty-sub');
        if (foot) foot.style.display = 'none';
        if (body) {
            body.innerHTML =
                '<div class="bank-cand-pane-empty">' +
                '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">' +
                '<rect x="14" y="10" width="36" height="44" rx="3"/>' +
                '<path d="M22 22h20M22 30h20M22 38h12"/></svg>' +
                '<div>' +
                t('bank-cand-pane-empty-hint') +
                '</div></div>';
        }
        const tbody = document.getElementById('bank-tx-tbody');
        if (tbody) {
            tbody
                .querySelectorAll('tr.is-selected')
                .forEach((r) => r.classList.remove('is-selected'));
        }
        _currentTxForDrawer = null;
    }

    // ---------- 工具 ----------
    function showBankProgress(show) {
        const el = document.getElementById('bank-upload-progress');
        if (el) el.style.display = show ? '' : 'none';
    }
    function showBankError(msg) {
        const el = document.getElementById('bank-upload-error');
        if (el) {
            el.textContent = msg;
            el.style.display = '';
        }
    }
    function hideBankError() {
        const el = document.getElementById('bank-upload-error');
        if (el) el.style.display = 'none';
    }
    function formatUploadError(detail) {
        const map = {
            'bank_recon.only_pdf': t('bank-err-only-pdf'),
            'bank_recon.empty_file': t('bank-err-empty'),
            'bank_recon.file_too_large': t('bank-err-too-large'),
            'bank_recon.save_failed': t('bank-err-server'),
            // v118.26.1 · 批量上传扩展错误码
            'bank_recon.scanned': t('bank-err-scanned'),
            'bank_recon.no_tx': t('bank-err-no-tx'),
            network: t('bank-err-network'),
        };
        return map[detail] || t('bank-err-unknown') + ' (' + detail + ')';
    }
    function fmtAmt(v) {
        if (v === null || v === undefined) return '-';
        const n = Number(v);
        if (isNaN(n)) return '-';
        return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    function formatDate(s) {
        if (!s) return '-';
        const str = String(s);
        return str.length >= 10 ? str.slice(0, 10) : str;
    }
    function formatPeriod(a, b) {
        if (!a && !b) return '';
        return (formatDate(a) || '?') + ' ~ ' + (formatDate(b) || '?');
    }
    function esc(s) {
        if (s === null || s === undefined) return '';
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    // 暴露
    window._loadBankReconPanel = load;
    window._rerenderBankRecon = function () {
        // v118.26.1.2 · 改成只渲染当前路由 · 防止其他页面无谓 DOM 操作
        if (currentRoute !== 'automation') return;
        renderSessionList();
        if (_currentSession) {
            renderDetailMeta();
            renderTxTable();
            // v118.26.2 · 客户徽章文案随 t() 切换
            _renderClientBadge();
            // 候选 pane 空态文案随 t() 切换(只在没选流水时刷)
            if (!_currentTxForDrawer) {
                const titleEl = document.getElementById('bank-cand-pane-title');
                const subEl = document.getElementById('bank-cand-pane-sub');
                if (titleEl) titleEl.textContent = t('bank-cand-pane-empty-title');
                if (subEl) subEl.textContent = t('bank-cand-pane-empty-sub');
            }
        }
        renderQueue();
    };
    // v118.26.1.2 · 注册到 i18n 订阅总线 · 切语言自动重渲(不再依赖 applyLang 散调用)
    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('bank-recon', window._rerenderBankRecon);
    }

    // v118.26.1 · 对账中心点最近会话卡 → 跳过来打开会话
    window._openBankSession = async function (sessionId) {
        if (!sessionId) return;
        // 确保面板已 load · 否则 refreshSessions 没跑 · 顺序点击会跳空
        if (!_loaded) {
            await load();
        }
        await loadSessionDetail(sessionId);
    };
})();
