// ============================================================
// REFACTOR-WB (2026-06-02) · 客户管理 · 买方客户:列表/分页/批量/弹窗/导出 · 从 clients.js 抽出 · verbatim 0 改逻辑。
// ============================================================
/* global escapeHtml, showConfirm */
import { S, _buyerState, _buyerSelected } from './clients-store.js';
import { apiClient, getActiveColor } from './clients-helpers.js';

type Client = {
    id: string;
    name?: string;
    short_name?: string;
    tax_id?: string;
    color?: string;
    invoice_count?: number;
    total_amount?: number;
    address?: string;
    contact_person?: string;
    contact_phone?: string;
    contact_email?: string;
    notes?: string;
};

// ---------- 加载客户列表 ----------
async function loadClientsCache() {
    try {
        const data = await apiClient('/api/clients');
        S.clients = data.clients || [];
        window._clientsCache = S.clients as { [key: string]: unknown; id?: unknown }[];
    } catch (e) {
        console.error('loadClientsCache fail', e);
        S.clients = [];
    }
    // v118.21.0 · 通知异常栏客户下拉刷新
    try {
        if (typeof window._refreshExcClientFilter === 'function') window._refreshExcClientFilter();
    } catch (_) {
        /* silent · 通知下游刷新 */
    }
    // v118.28.0 · 通知顶栏客户切换器刷新
    try {
        if (typeof window._refreshClientSwitcher === 'function') window._refreshClientSwitcher();
    } catch (_) {
        /* silent · 通知下游刷新 */
    }
    return S.clients;
}

// ---------- 客户管理页 · 渲染卡片 ----------
function renderClientsGrid() {
    const wrap = document.getElementById('clients-grid');
    if (!wrap) return;
    if (!S.clients.length) {
        wrap.innerHTML = `
            <div class="client-card-empty">
                <svg class="client-card-empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
                    <circle cx="9" cy="7" r="4"/>
                    <path d="M23 21v-2a4 4 0 00-3-3.87"/>
                    <path d="M16 3.13a4 4 0 010 7.75"/>
                </svg>
                <p><strong>${escapeHtml(t('clients-empty'))}</strong></p>
                <p>${escapeHtml(t('clients-empty-hint'))}</p>
            </div>`;
        return;
    }
    wrap.innerHTML = (S.clients as Client[])
        .map(
            (c) => `
        <div class="client-card" data-cid="${c.id}" style="--client-color:${escapeHtml(c.color)}">
            <div class="client-card-head">
                <div>
                    <div class="client-card-name">${escapeHtml(c.name)}</div>
                    ${c.tax_id ? `<div class="client-card-tax">${escapeHtml(c.tax_id)}</div>` : ''}
                </div>
            </div>
            <div class="client-card-stats">
                <div>
                    <div class="client-card-stat-label">${escapeHtml(t('client-card-invoices'))}</div>
                    <div class="client-card-stat-value">${c.invoice_count || 0}</div>
                </div>
                <div>
                    <div class="client-card-stat-label">${escapeHtml(t('client-card-amount'))}</div>
                    <div class="client-card-stat-value">฿${(c.total_amount || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
                </div>
            </div>
            <div class="client-card-actions">
                <button class="client-card-btn" data-action="edit" data-cid="${c.id}">
                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M9 2l3 3-7 7H2v-3z"/>
                    </svg>
                    ${escapeHtml(t('client-card-edit'))}
                </button>
                <button class="client-card-btn" data-action="export" data-cid="${c.id}">
                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M7 2v7M4 6l3 3 3-3M2 11h10"/>
                    </svg>
                    ${escapeHtml(t('client-card-export'))}
                </button>
            </div>
        </div>
    `
        )
        .join('');
}

// ==========================================================
// P3 · 买方客户 tab(横条列表 · 搜索/多选/批删/翻页)
// ==========================================================
function _buyerFiltered() {
    const kw = _buyerState.keyword.trim().toLowerCase();
    if (!kw) return S.clients as Client[];
    return (S.clients as Client[]).filter(
        (c) =>
            (c.name || '').toLowerCase().includes(kw) ||
            (c.short_name || '').toLowerCase().includes(kw) ||
            (c.tax_id || '').toLowerCase().includes(kw)
    );
}

function _buyerPageItems() {
    const all = _buyerFiltered();
    const ps = _buyerState.pageSize;
    const maxPage = Math.max(0, Math.ceil(all.length / ps) - 1);
    if (_buyerState.page > maxPage) _buyerState.page = maxPage;
    const start = _buyerState.page * ps;
    return { all, items: all.slice(start, start + ps), start, ps, total: all.length, maxPage };
}

function renderBuyerList() {
    const tb = document.getElementById('buyer-tbody');
    if (!tb) return;
    const { items, start, ps, total, maxPage } = _buyerPageItems();
    if (!total) {
        tb.innerHTML = `<div class="cust-empty">${escapeHtml(t(_buyerState.keyword ? 'cust-no-match' : 'clients-empty'))}</div>`;
    } else {
        tb.innerHTML = items
            .map((c) => {
                const sel = _buyerSelected.has(c.id);
                return `<div class="cust-row buyer-grid${sel ? ' selected' : ''}" data-cid="${c.id}">
                <div class="cust-cell-check"><input type="checkbox" class="buyer-row-check" data-cid="${c.id}" ${sel ? 'checked' : ''}></div>
                <div style="min-width:0">
                    <div class="cust-cell-name"><span class="cust-color-dot" style="background:${escapeHtml(c.color || '#111')}"></span><span class="cust-name-text">${escapeHtml(c.name)}</span></div>
                    ${c.tax_id ? `<div class="cust-cell-sub">${escapeHtml(c.tax_id)}</div>` : ''}
                </div>
                <div class="align-right">${c.invoice_count || 0}</div>
                <div class="align-right cust-cell-amount">฿${(c.total_amount || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
                <div class="cust-row-actions">
                    <button class="cust-row-btn" data-action="edit" data-cid="${c.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t('client-card-edit'))}</span></button>
                    <button class="cust-row-btn" data-action="export" data-cid="${c.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 2v7M4 6l3 3 3-3M2 11h10"/></svg><span>${escapeHtml(t('client-card-export'))}</span></button>
                </div>
            </div>`;
            })
            .join('');
    }
    const info = document.getElementById('buyer-pager-info');
    if (info)
        info.textContent = total ? `${start + 1}–${Math.min(start + ps, total)} / ${total}` : '0';
    const prev = document.getElementById('buyer-prev') as HTMLButtonElement | null;
    if (prev) prev.disabled = _buyerState.page <= 0;
    const next = document.getElementById('buyer-next') as HTMLButtonElement | null;
    if (next) next.disabled = _buyerState.page >= maxPage;
    _updateBuyerBatchBar();
}

function _updateBuyerBatchBar() {
    const n = _buyerSelected.size;
    const bar = document.getElementById('buyer-batch-bar');
    if (bar) bar.style.display = n ? 'flex' : 'none';
    const cnt = document.getElementById('buyer-batch-count');
    if (cnt) cnt.textContent = t('cust-selected-n').replace('{n}', n as unknown as string);
    const all = document.getElementById('buyer-check-all') as HTMLInputElement | null;
    if (all) {
        const { items } = _buyerPageItems();
        const pageIds = items.map((c) => c.id);
        const onPage = pageIds.filter((id) => _buyerSelected.has(id)).length;
        all.checked = pageIds.length > 0 && onPage === pageIds.length;
        all.indeterminate = onPage > 0 && onPage < pageIds.length;
    }
}

function clearBuyerSelection() {
    _buyerSelected.clear();
    renderBuyerList();
}

async function buyerBatchDelete() {
    const ids = Array.from(_buyerSelected);
    if (!ids.length) return;
    const ok = await showConfirm(
        t('cust-batch-del-confirm').replace('{n}', ids.length as unknown as string),
        {
            danger: true,
        }
    );
    if (!ok) return;
    try {
        await apiClient('/api/clients/batch-delete', {
            method: 'POST',
            body: JSON.stringify({ ids }),
        });
        showToast(t('client-msg-deleted'), 'success');
        _buyerSelected.clear();
        await loadClientsCache();
        renderBuyerList();
        refreshDrawerClientSelect();
        refreshHistoryClientFilter();
    } catch (e) {
        showToast(t('client-msg-save-fail'), 'fail');
    }
}

// ---------- 弹窗 ----------
function openClientModal(client: Client | null) {
    S.editingClientId = client ? client.id : null;
    const isEdit = !!client;
    document.getElementById('client-modal-title')!.textContent = t(
        isEdit ? 'client-modal-edit' : 'client-modal-new'
    );
    (document.getElementById('client-input-name') as HTMLInputElement).value =
        (client && client.name) || '';
    (document.getElementById('client-input-short') as HTMLInputElement).value =
        (client && client.short_name) || '';
    (document.getElementById('client-input-tax') as HTMLInputElement).value =
        (client && client.tax_id) || '';
    (document.getElementById('client-input-address') as HTMLInputElement).value =
        (client && client.address) || '';
    (document.getElementById('client-input-contact') as HTMLInputElement).value =
        (client && client.contact_person) || '';
    (document.getElementById('client-input-phone') as HTMLInputElement).value =
        (client && client.contact_phone) || '';
    (document.getElementById('client-input-email') as HTMLInputElement).value =
        (client && client.contact_email) || '';
    (document.getElementById('client-input-notes') as HTMLInputElement).value =
        (client && client.notes) || '';
    // 颜色
    const targetColor = (client && client.color) || '#111111';
    document.querySelectorAll('#client-color-picker .color-swatch').forEach((s) => {
        s.classList.toggle('active', (s as HTMLElement).dataset.color === targetColor);
    });
    // 删除按钮(仅编辑时显示)
    document.getElementById('client-modal-delete')!.style.display = isEdit ? '' : 'none';
    document.getElementById('client-modal-mask')!.style.display = 'flex';
    setTimeout(() => document.getElementById('client-input-name')!.focus(), 50);
}

function closeClientModal() {
    document.getElementById('client-modal-mask')!.style.display = 'none';
    S.editingClientId = null;
}

async function saveClient() {
    const name = (document.getElementById('client-input-name') as HTMLInputElement).value.trim();
    if (!name) {
        showToast(t('client-msg-name-required'), 'fail');
        return;
    }
    const payload = {
        name,
        short_name:
            (document.getElementById('client-input-short') as HTMLInputElement).value.trim() ||
            null,
        tax_id:
            (document.getElementById('client-input-tax') as HTMLInputElement).value.trim() || null,
        address:
            (document.getElementById('client-input-address') as HTMLInputElement).value.trim() ||
            null,
        contact_person:
            (document.getElementById('client-input-contact') as HTMLInputElement).value.trim() ||
            null,
        contact_phone:
            (document.getElementById('client-input-phone') as HTMLInputElement).value.trim() ||
            null,
        contact_email:
            (document.getElementById('client-input-email') as HTMLInputElement).value.trim() ||
            null,
        notes:
            (document.getElementById('client-input-notes') as HTMLInputElement).value.trim() ||
            null,
        color: getActiveColor(),
    };
    try {
        if (S.editingClientId) {
            await apiClient(`/api/clients/${S.editingClientId}`, {
                method: 'PATCH',
                body: JSON.stringify(payload),
            });
            showToast(t('client-msg-updated'), 'success');
        } else {
            await apiClient('/api/clients', { method: 'POST', body: JSON.stringify(payload) });
            showToast(t('client-msg-created'), 'success');
        }
        closeClientModal();
        await loadClientsCache();
        if (currentRoute === 'clients') renderBuyerList();
        // 抽屉里的下拉也刷新
        refreshDrawerClientSelect();
        // 历史页筛选下拉刷新
        refreshHistoryClientFilter();
    } catch (e) {
        console.error('saveClient fail', e);
        // v107.1 · 显示后端 detail · 而不是模糊的"保存失败"
        const errMsg = e && (e as Error).message ? (e as Error).message : t('client-msg-save-fail');
        showToast(t('client-msg-save-fail') + ' · ' + errMsg, 'fail');
    }
}

async function deleteClient() {
    if (!S.editingClientId) return;
    const c = (S.clients as Client[]).find((x) => x.id === S.editingClientId);
    if (!c) return;
    const msg = t('client-delete-confirm').replace('{name}', c.name as string);
    const ok = await showConfirm(msg, { danger: true });
    if (!ok) return;
    try {
        await apiClient(`/api/clients/${S.editingClientId}`, { method: 'DELETE' });
        showToast(t('client-msg-deleted'), 'success');
        closeClientModal();
        await loadClientsCache();
        if (currentRoute === 'clients') renderBuyerList();
        refreshDrawerClientSelect();
        refreshHistoryClientFilter();
    } catch (e) {
        console.error(e);
        showToast(t('client-msg-save-fail'), 'fail');
    }
}

// 导出某客户(v109.1 · 改用统一弹窗)
async function exportClient(clientId: string) {
    const c = (S.clients as Client[]).find((x) => x.id === clientId);
    if (typeof window.openClientExportModal === 'function') {
        window.openClientExportModal(clientId, c ? c.name : '');
        return;
    }
    // fallback · 老路径(理论不到这里)
    try {
        const tok = localStorage.getItem('mrpilot_token');
        const r = await fetch(`/api/clients/${clientId}/export?month=all`, {
            headers: { Authorization: 'Bearer ' + tok },
        });
        if (!r.ok) {
            let detail = 'HTTP ' + r.status;
            try {
                const err = await r.json();
                if (err && err.detail) detail = err.detail;
            } catch (_e) {}
            throw new Error(detail);
        }
        const blob = await r.blob();
        if (blob.size < 200) {
            showToast(t('client-export-month-empty'), 'info');
            return;
        }
        const cname =
            c && c.name
                ? c.name.replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g, '_').slice(0, 40)
                : 'client';
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${cname}_export.csv`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (e) {
        console.error('exportClient fail', e);
        showToast(t('client-msg-save-fail') + ' · ' + ((e as Error).message || ''), 'fail');
    }
}

// ---------- 抽屉里下拉 ----------
function refreshDrawerClientSelect() {
    const sel = document.getElementById('drawer-client-select') as HTMLSelectElement | null;
    if (!sel) return;
    const cur = sel.value;
    sel.innerHTML =
        `<option value="">${escapeHtml(t('drawer-client-none'))}</option>` +
        (S.clients as Client[])
            .map((c) => `<option value="${c.id}">${escapeHtml(c.name)}</option>`)
            .join('');
    sel.value = cur || '';
}

// ---------- 历史页筛选 ----------
function refreshHistoryClientFilter() {
    const sel = document.getElementById('history-client-filter') as HTMLSelectElement | null;
    if (!sel) return;
    const cur = sel.value;
    sel.innerHTML =
        `<option value="">${escapeHtml(t('history-client-all'))}</option>` +
        (S.clients as Client[])
            .map((c) => `<option value="${c.id}">${escapeHtml(c.name)}</option>`)
            .join('');
    sel.value = cur || '';
}

export {
    loadClientsCache,
    renderClientsGrid,
    renderBuyerList,
    _buyerPageItems,
    _updateBuyerBatchBar,
    clearBuyerSelection,
    buyerBatchDelete,
    openClientModal,
    closeClientModal,
    saveClient,
    deleteClient,
    exportClient,
    refreshDrawerClientSelect,
    refreshHistoryClientFilter,
};
