// ============================================================
// REFACTOR-WB-C1 (2026-05-30) · ERP 端点管理 从 erp-integration.js 抽出为独立 ES module
//
// 来源:erp-integration.js 端点管理函数群(loadErpEndpoints/loadErpTodayStats/
//   renderErpEndpointsList/openEndpointModal/closeEndpointModal/_sanitizeUrl/
//   readEndpointForm/testEndpointConnection/saveEndpoint/showEpSaveError/deleteEndpoint)
//   + 模块状态 _erpEndpoints/_epEditingId · verbatim 0 改逻辑。
// 推送日志组(loadErpLogs/showLogDetail/retryPushLog/批量)留 erp-integration.js。
// 端点组对日志组 0 引用(干净切面);日志组+initAutomationPage 经 window 桥接调本模块
//   (window.loadErpEndpoints/_erpEndpoints/loadErpTodayStats/openEndpointModal/.../_sanitizeUrl)。
// home.js 核心 + injectOcrPushButton 经 window._erpEndpoints 读缓存(每次 loadErpEndpoints 重写)。
// ============================================================
/* global escapeHtml, token, showConfirm, humanizeError, currentLang, routeTo, switchAutomationTab, _showSessionRevokedModal */

let _erpEndpoints = [];
window._erpEndpoints = _erpEndpoints;
let _epEditingId = null; // 当前编辑中的 endpoint id,null = 新增模式

async function loadErpEndpoints() {
    try {
        const resp = await fetch('/api/erp/endpoints', {
            headers: { Authorization: 'Bearer ' + token },
        });
        if (resp.status === 401) {
            localStorage.removeItem('mrpilot_token');
            const _bd = await resp.json().catch(() => ({}));
            const _dc =
                typeof _bd.detail === 'string' ? _bd.detail : (_bd.detail && _bd.detail.code) || '';
            if (_dc === 'auth.session_revoked') {
                _showSessionRevokedModal();
                return;
            }
            window.location.href = '/';
            return;
        }
        const data = await resp.json();
        _erpEndpoints = data.items || [];
        window._erpEndpoints = _erpEndpoints;
        renderErpEndpointsList();
    } catch (e) {
        console.error('load endpoints failed', e);
    }
}

// v118.34.34 (批 2 改动 7) · 外部模块 (erp-mrerp-connect.js) 调
// PATCH /api/erp/endpoints/:id 切 enabled 后,要让 home.js 的全局
// _erpEndpoints 同步 · 不然 OCR drawer 推送按钮还在用旧 list (会显示
// 已停用的 endpoint 在 picker 里).
window._refreshErpEndpointsCache = function () {
    return loadErpEndpoints();
};

// v0.17 · M5 · 今日 ERP 推送统计 · 显示在 ERP 对接 tab 头部
async function loadErpTodayStats() {
    const host = document.getElementById('erp-today-stats');
    if (!host) return;
    host.innerHTML = '';
    try {
        const resp = await fetch('/api/erp/stats/today', {
            headers: { Authorization: 'Bearer ' + token },
        });
        if (!resp.ok) return;
        const data = await resp.json();
        const total = data.total || 0;
        const success = data.success || 0;
        const failed = data.failed || 0;
        const autoCnt = data.auto_cnt || 0;
        if (total === 0) {
            host.innerHTML = `<span class="erp-today-empty">${escapeHtml(t('erp-today-none'))}</span>`;
            return;
        }
        const parts = [];
        parts.push(
            `<span class="erp-today-item"><strong>${total}</strong> ${escapeHtml(t('erp-today-total'))}</span>`
        );
        if (success > 0)
            parts.push(
                `<span class="erp-today-item ok"><strong>${success}</strong> ${escapeHtml(t('erp-today-success'))}</span>`
            );
        if (failed > 0)
            parts.push(
                `<span class="erp-today-item fail"><strong>${failed}</strong> ${escapeHtml(t('erp-today-failed'))}</span>`
            );
        if (autoCnt > 0)
            parts.push(
                `<span class="erp-today-item auto"><strong>${autoCnt}</strong> ${escapeHtml(t('erp-today-auto'))}</span>`
            );
        host.innerHTML = parts.join('');
    } catch (e) {
        console.warn('loadErpTodayStats failed', e);
    }
}

function renderErpEndpointsList() {
    const list = document.getElementById('erp-endpoints-list');
    const summary = document.getElementById('erp-status-summary');
    const addBtn = document.getElementById('btn-add-endpoint');

    if (!list) {
        console.warn('erp-endpoints-list 容器不存在');
        return;
    }

    // v0.8 · 按 endpoints_limit 灰化新增按钮
    if (addBtn && _userInfo) {
        const limit = _userInfo.endpoints_limit;
        if (limit !== -1 && _erpEndpoints.length >= limit) {
            addBtn.disabled = true;
            addBtn.title = t('ep-limit-reached', { limit });
            addBtn.classList.add('btn-disabled-plus');
        } else {
            addBtn.disabled = false;
            addBtn.title = '';
            addBtn.classList.remove('btn-disabled-plus');
        }
    }

    if (_erpEndpoints.length === 0) {
        list.innerHTML = `<div class="erp-empty">${escapeHtml(t('ep-list-empty'))}</div>`;
        if (summary) {
            summary.textContent = t('auto-status-none');
            summary.className = 'auto-status-pill none';
        }
        return;
    }

    const autoOn = _erpEndpoints.some((e) => e.auto_push && e.enabled);
    if (summary) {
        summary.textContent = t('auto-status-active', {
            n: _erpEndpoints.length,
            mode: autoOn ? t('auto-status-on') : t('auto-status-off'),
        });
        summary.className = 'auto-status-pill ' + (autoOn ? 'active' : 'ready');
    }
    // v0.17 · M5 · 异步加载今日统计 · 追加到 summary 区域下方
    loadErpTodayStats();

    list.innerHTML = _erpEndpoints
        .map((ep) => {
            const cfg = ep.config || {};
            const url = escapeHtml(cfg.url || '');
            const hasToken = !!cfg._token_set;
            const enabled = ep.enabled !== false;

            const badges = [];
            if (ep.is_default)
                badges.push(`<span class="ep-badge default">${escapeHtml(t('ep-default'))}</span>`);
            if (ep.auto_push)
                badges.push(
                    `<span class="ep-badge auto">${escapeHtml(t('ep-auto-push-on'))}</span>`
                );
            if (!enabled)
                badges.push(
                    `<span class="ep-badge disabled">${escapeHtml(t('ep-disabled'))}</span>`
                );

            const stats = [];
            if (ep.success_count > 0)
                stats.push(
                    `<span class="ep-stat ok">${escapeHtml(t('ep-success', { n: ep.success_count }))}</span>`
                );
            if (ep.failure_count > 0)
                stats.push(
                    `<span class="ep-stat fail">${escapeHtml(t('ep-failure', { n: ep.failure_count }))}</span>`
                );

            return `
            <div class="erp-endpoint" data-ep-id="${escapeHtml(ep.id)}">
                <div class="ep-main">
                    <div class="ep-title-row">
                        <div class="ep-name">${escapeHtml(ep.name)}</div>
                        <div class="ep-badges">${badges.join('')}</div>
                    </div>
                    <div class="ep-url">${url || '-'}</div>
                    <div class="ep-stats">${stats.join(' · ')}</div>
                </div>
                <div class="ep-actions">
                    <button class="btn btn-ghost btn-small" data-ep-edit="${escapeHtml(ep.id)}">
                        <span>${escapeHtml(t('ep-edit'))}</span>
                    </button>
                    <button class="btn btn-ghost btn-small btn-danger" data-ep-del="${escapeHtml(ep.id)}">
                        <span>${escapeHtml(t('ep-delete'))}</span>
                    </button>
                </div>
            </div>
        `;
        })
        .join('');

    // v0.8.1 · 列表下方显示上限提示(根据 plan)
    if (_userInfo && _userInfo.endpoints_limit !== -1) {
        const usedN = _erpEndpoints.length;
        const limit = _userInfo.endpoints_limit;
        const plan = _userInfo.plan;
        const hint = document.createElement('div');
        hint.className = 'erp-limit-hint';
        if (plan === 'free') {
            hint.innerHTML = `${escapeHtml(t('ep-free-limit-hint', { used: usedN, limit }))} <a data-upgrade="plus">${escapeHtml(t('upgrade-to-plus'))}</a>`;
        } else {
            hint.textContent = t('ep-plus-limit-hint', { used: usedN, limit });
        }
        list.appendChild(hint);
    }
}

// 打开新增对话框
function openEndpointModal(editingId) {
    _epEditingId = editingId || null;
    const modal = document.getElementById('endpoint-modal');
    const titleEl = document.getElementById('endpoint-modal-title');
    titleEl.textContent = editingId ? t('ep-modal-title-edit') : t('ep-modal-title-new');

    const nameEl = document.getElementById('ep-name');
    const urlEl = document.getElementById('ep-url');
    const tokenEl = document.getElementById('ep-token');
    const isDefEl = document.getElementById('ep-is-default');
    const autoPushEl = document.getElementById('ep-auto-push');
    const resultEl = document.getElementById('ep-test-result');

    resultEl.style.display = 'none';
    resultEl.textContent = '';

    // 清掉上次遗留的错误提示
    const errBox = document.getElementById('ep-save-error');
    if (errBox) errBox.remove();

    if (editingId) {
        const ep = _erpEndpoints.find((e) => e.id === editingId);
        if (!ep) return;
        nameEl.value = ep.name || '';
        urlEl.value = (ep.config || {}).url || '';
        tokenEl.value = (ep.config || {})._token_set ? ep.config.token || '' : '';
        tokenEl.placeholder = (ep.config || {})._token_set
            ? '（已保存 · 留空保持不变）'
            : t('ep-token-ph');
        isDefEl.checked = !!ep.is_default;
        autoPushEl.checked = !!ep.auto_push;
    } else {
        nameEl.value = '';
        urlEl.value = '';
        tokenEl.value = '';
        tokenEl.placeholder = t('ep-token-ph');
        isDefEl.checked = _erpEndpoints.length === 0; // 第一个默认选中
        // v118.27.8.1.15 · 新建 endpoint 默认开启自动推送(0 操作上 ERP)· 老 endpoint 不变(走 14132 读 ep.auto_push)
        autoPushEl.checked = true;
    }

    // v0.15 · 扁平权限 · 所有人都能自动推送
    const autoPushRow = autoPushEl.closest('.form-switch-row');
    autoPushEl.disabled = false;
    if (autoPushRow) {
        autoPushRow.classList.remove('disabled-plus');
        autoPushRow.title = '';
        autoPushRow.style.cursor = '';
        autoPushRow.onclick = null;
        const b = autoPushRow.querySelector('.plus-badge');
        if (b) b.remove();
    }

    modal.style.display = '';
    setTimeout(() => nameEl.focus(), 50);
}

function closeEndpointModal() {
    document.getElementById('endpoint-modal').style.display = 'none';
    _epEditingId = null;
    // 关闭时清错误提示,避免下次打开残留
    const errBox = document.getElementById('ep-save-error');
    if (errBox) errBox.remove();
}

function _sanitizeUrl(raw) {
    // v0.9.1 · 清理常见"复制糟粕"(Copy to clipboard / 空格后跟可疑词)
    if (!raw) return '';
    let u = raw.trim();
    // 只保留到第一个空格前(URL 不能含空格)
    const spIdx = u.search(/\s/);
    if (spIdx >= 0) u = u.slice(0, spIdx);
    return u;
}

function readEndpointForm() {
    const name = document.getElementById('ep-name').value.trim();
    const url = _sanitizeUrl(document.getElementById('ep-url').value);
    const tokenVal = document.getElementById('ep-token').value;
    const isDefault = document.getElementById('ep-is-default').checked;
    const autoPush = document.getElementById('ep-auto-push').checked;

    const config = { url };
    // token:编辑模式下如果留空,发 "***" 占位(后端会保留旧值);否则发新值
    if (_epEditingId) {
        if (tokenVal) config.token = tokenVal;
    } else {
        if (tokenVal) config.token = tokenVal;
    }

    return { name, url, tokenVal, isDefault, autoPush, config };
}

async function testEndpointConnection() {
    const { name, url, config } = readEndpointForm();
    const resultEl = document.getElementById('ep-test-result');
    if (!url) {
        resultEl.style.display = '';
        resultEl.className = 'form-test-result fail';
        resultEl.textContent = t('ep-required');
        return;
    }
    resultEl.style.display = '';
    resultEl.className = 'form-test-result running';
    resultEl.textContent = t('ep-test-running');

    try {
        const resp = await fetch('/api/erp/test-connection', {
            method: 'POST',
            headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
            body: JSON.stringify({ adapter: 'webhook', config }),
        });
        const data = await resp.json();
        if (data.success) {
            resultEl.className = 'form-test-result ok';
            resultEl.textContent = t('ep-test-ok', {
                status: data.http_status,
                ms: data.elapsed_ms,
            });
        } else {
            resultEl.className = 'form-test-result fail';
            resultEl.textContent = t('ep-test-fail', { err: data.error_msg || 'unknown' });
        }
    } catch (e) {
        resultEl.className = 'form-test-result fail';
        resultEl.textContent = t('ep-test-fail', { err: e.message });
    }
}

async function saveEndpoint() {
    const form = readEndpointForm();
    const errBox = document.getElementById('ep-save-error');
    if (errBox) errBox.style.display = 'none';

    if (!form.name || !form.url) {
        showEpSaveError(t('ep-required'));
        return;
    }
    const payload = {
        name: form.name,
        adapter: 'webhook',
        config: form.config,
        is_default: form.isDefault,
        auto_push: form.autoPush,
    };

    const btn = document.getElementById('btn-ep-save');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.classList.add('loading');

    try {
        let resp;
        if (_epEditingId) {
            resp = await fetch(`/api/erp/endpoints/${encodeURIComponent(_epEditingId)}`, {
                method: 'PATCH',
                headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
        } else {
            resp = await fetch('/api/erp/endpoints', {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
        }
        if (!resp.ok) {
            const errData = await resp.json().catch(() => ({}));
            const detail = errData.detail || `HTTP ${resp.status}`;
            throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
        }
        // 成功 · 静默关窗 + 小 toast
        closeEndpointModal();
        showToast(t('ep-save-ok'));
        loadErpEndpoints();
    } catch (e) {
        showEpSaveError(`${t('ep-save-fail')} · ${e.message || 'unknown'}`);
    } finally {
        btn.disabled = false;
        btn.classList.remove('loading');
        btn.innerHTML = originalText;
    }
}

function showEpSaveError(msg) {
    let box = document.getElementById('ep-save-error');
    if (!box) {
        const foot = document.querySelector('#endpoint-modal .modal-foot');
        if (!foot) return;
        box = document.createElement('div');
        box.id = 'ep-save-error';
        box.className = 'ep-inline-error';
        foot.parentNode.insertBefore(box, foot);
    }
    box.textContent = msg;
    box.style.display = '';
}

async function deleteEndpoint(endpointId) {
    const ep = _erpEndpoints.find((e) => e.id === endpointId);
    if (!ep) return;
    const ok = await showConfirm(t('ep-delete-confirm', { name: ep.name }), { danger: true });
    if (!ok) return;
    try {
        const resp = await fetch(`/api/erp/endpoints/${encodeURIComponent(endpointId)}`, {
            method: 'DELETE',
            headers: { Authorization: 'Bearer ' + token },
        });
        if (!resp.ok) throw new Error();
        showToast(t('ep-delete-ok'));
        loadErpEndpoints();
    } catch {
        showToast(t('ep-save-fail'), 'fail');
    }
}

// ── 模块外调用入口(home.js routeTo / initAutomationPage / 其它模块经 window 调)──
window.loadErpEndpoints = loadErpEndpoints;
window.loadErpTodayStats = loadErpTodayStats;
window.renderErpEndpointsList = renderErpEndpointsList;
window.openEndpointModal = openEndpointModal;
window.closeEndpointModal = closeEndpointModal;
window.saveEndpoint = saveEndpoint;
window.deleteEndpoint = deleteEndpoint;
window.testEndpointConnection = testEndpointConnection;
window._sanitizeUrl = _sanitizeUrl;
