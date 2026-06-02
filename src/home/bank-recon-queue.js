// ============================================================
// REFACTOR-WB (2026-06-02) · 银行对账 M10 · 批量上传队列(并发3+重试) · 从 bank-recon.js 抽出
// verbatim 0 改逻辑。
// ============================================================
/* global token, showConfirm */
import { S } from './bank-recon-store.js';
import { showBankProgress, hideBankError, formatUploadError, esc } from './bank-recon-helpers.js';
import { refreshSessions } from './bank-recon-sessions.js';

const QUEUE_CONCURRENCY = 3;

function _qid() {
    S.qSeq += 1;
    return 'q' + S.qSeq + '_' + Date.now();
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
        S.queue.push(item);
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

    if (S.queue.length === 0) {
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
    for (const it of S.queue) {
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

    list.innerHTML = S.queue.map(_rowHtml).join('');
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
            '<button data-q-act="remove" data-q-id="' + esc(it.id) + '" class="bq-act">×</button>';
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
            '<button data-q-act="remove" data-q-id="' + esc(it.id) + '" class="bq-act">×</button>';
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
    const it = S.queue.find((x) => x.id === id);
    if (!it) return;
    it.status = 'pending';
    it.error_code = null;
    it.progress = 0;
    renderQueue();
    _drainQueue();
}

function _removeItem(id) {
    const idx = S.queue.findIndex((x) => x.id === id);
    if (idx < 0) return;
    const it = S.queue[idx];
    // 跑着的不能直接移除(防中断)· 只能完成态/排队态
    if (it.status === 'uploading' || it.status === 'parsing') return;
    S.queue.splice(idx, 1);
    renderQueue();
}

function _clearDone() {
    S.queue = S.queue.filter((x) => x.status !== 'ok');
    renderQueue();
}

async function _drainQueue() {
    while (true) {
        const running = S.queue.filter(
            (x) => x.status === 'uploading' || x.status === 'parsing'
        ).length;
        if (running >= QUEUE_CONCURRENCY) return;
        const next = S.queue.find((x) => x.status === 'pending');
        if (!next) {
            // 全部跑完一轮 · 刷一次 sessions 列表
            if (S.queue.every((x) => x.status === 'ok' || x.status === 'failed')) {
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
                body.error === 'scanned_pdf_not_yet' ? 'bank_recon.scanned' : 'bank_recon.no_tx';
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

export { handleFilePick, renderQueue, _clearDone };
