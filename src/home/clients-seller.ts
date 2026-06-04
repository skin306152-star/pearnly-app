// ============================================================
// REFACTOR-WB (2026-06-02) · 客户管理 · 账套主体:tab/列表/弹窗/归档 · 从 clients.js 抽出 · verbatim 0 改逻辑。
// ============================================================
/* global escapeHtml, showConfirm */
import { S, _sellerState } from './clients-store.js';
import { apiClient } from './clients-helpers.js';

// ==========================================================
// P3 · 客户管理页 · tab 切换
// ==========================================================
function switchCustTab(tab: string) {
    S.custTab = tab === 'buyer' ? 'buyer' : 'seller';
    document
        .querySelectorAll('[data-cust-tab]')
        .forEach((b) =>
            b.classList.toggle('active', (b as HTMLElement).dataset.custTab === S.custTab)
        );
    const ps = document.getElementById('cust-pane-seller');
    const pb = document.getElementById('cust-pane-buyer');
    if (ps) ps.classList.toggle('active', S.custTab === 'seller');
    if (pb) pb.classList.toggle('active', S.custTab === 'buyer');
}

function _isWsOwner() {
    const u = window._userInfo || {};
    const r = String(u.role || '').toLowerCase();
    const tr = String(u.tenant_role || '').toLowerCase();
    return (
        u.is_super_admin === true ||
        u.is_owner === true ||
        r === 'owner' ||
        r === 'admin' ||
        tr === 'owner' ||
        tr === 'admin'
    );
}

function _syncWorkspaceSwitcher() {
    // 账套主体改动后 → 让右上角切换器即时反映(共用同一份缓存)
    window._workspaceClientsCache = S.sellerClients;
    if (typeof window.renderWorkspaceControl === 'function') window.renderWorkspaceControl();
}

// ==========================================================
// P3 · 账套主体 tab(= 工作空间 · 与右上角切换器双向同步)
// ==========================================================
async function loadSellerCache() {
    try {
        const data = await apiClient('/api/workspace/clients');
        S.sellerClients = (data && (data.clients || data.items)) || [];
        window._workspaceClientsCache = S.sellerClients;
    } catch (e) {
        console.error('loadSellerCache fail', e);
        S.sellerClients = [];
    }
    return S.sellerClients;
}

function _sellerFiltered() {
    const kw = _sellerState.keyword.trim().toLowerCase();
    if (!kw) return S.sellerClients;
    return S.sellerClients.filter(
        (c: any) =>
            (c.name || '').toLowerCase().includes(kw) || (c.tax_id || '').toLowerCase().includes(kw)
    );
}

function renderSellerList() {
    const tb = document.getElementById('seller-tbody');
    if (!tb) return;
    const owner = _isWsOwner();
    const newBtn = document.getElementById('btn-seller-new');
    if (newBtn) newBtn.style.display = owner ? '' : 'none';
    const items = _sellerFiltered();
    const activeId =
        typeof window.getActiveWorkspaceClientId === 'function'
            ? window.getActiveWorkspaceClientId()
            : null;
    if (!items.length) {
        tb.innerHTML = `<div class="cust-empty">${escapeHtml(t(_sellerState.keyword ? 'cust-no-match' : 'seller-empty'))}</div>`;
        return;
    }
    tb.innerHTML = items
        .map((c: any) => {
            const isActive = activeId != null && Number(activeId) === Number(c.id);
            const current = isActive
                ? `<span class="cust-badge-current"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7.5l3.2 3.2L12 4"/></svg>${escapeHtml(t('seller-current'))}</span>`
                : `<button class="cust-row-btn primary" data-saction="activate" data-wid="${c.id}">${escapeHtml(t('seller-set-current'))}</button>`;
            const ownerBtns = owner
                ? `
            <button class="cust-row-btn" data-saction="edit" data-wid="${c.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t('client-card-edit'))}</span></button>
            <button class="cust-row-btn danger" data-saction="archive" data-wid="${c.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h10M4 4v7a1 1 0 001 1h4a1 1 0 001-1V4M5.5 4V2.8a1 1 0 011-1h1a1 1 0 011 1V4"/></svg><span>${escapeHtml(t('wsclient-archive'))}</span></button>`
                : '';
            return `<div class="cust-row seller-grid" data-wid="${c.id}">
            <div class="cust-cell-name"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" style="flex-shrink:0;opacity:.55"><rect x="2" y="5" width="12" height="9" rx="1"/><path d="M10 14V4a1 1 0 00-1-1H7a1 1 0 00-1 1v10"/></svg><span class="cust-name-text">${escapeHtml(c.name || '#' + c.id)}</span></div>
            <div class="cust-cell-tax">${escapeHtml(c.tax_id || '—')}</div>
            <div class="align-right">${c.invoice_count || 0}</div>
            <div class="cust-row-actions">${current}${ownerBtns}</div>
        </div>`;
        })
        .join('');
}

// 账套主体编辑弹窗
function openWsClientModal(ws: any) {
    S.editingWsClientId = ws ? ws.id : null;
    document.getElementById('wsclient-modal-title')!.textContent = t(
        ws ? 'wsclient-modal-edit' : 'wsclient-modal-new'
    );
    (document.getElementById('wsclient-input-name') as HTMLInputElement).value =
        (ws && ws.name) || '';
    (document.getElementById('wsclient-input-tax') as HTMLInputElement).value =
        (ws && ws.tax_id) || '';
    document.getElementById('wsclient-modal-archive')!.style.display = ws ? '' : 'none';
    document.getElementById('wsclient-modal-mask')!.style.display = 'flex';
    setTimeout(() => document.getElementById('wsclient-input-name')!.focus(), 50);
}

function closeWsClientModal() {
    document.getElementById('wsclient-modal-mask')!.style.display = 'none';
    S.editingWsClientId = null;
}

async function saveWsClient() {
    const name = (document.getElementById('wsclient-input-name') as HTMLInputElement).value.trim();
    const tax = (document.getElementById('wsclient-input-tax') as HTMLInputElement).value.trim();
    if (!name) {
        showToast(t('client-msg-name-required'), 'fail');
        return;
    }
    try {
        if (S.editingWsClientId) {
            await apiClient('/api/workspace/clients/' + S.editingWsClientId, {
                method: 'PATCH',
                body: JSON.stringify({ name, tax_id: tax }),
            });
            showToast(t('client-msg-updated'), 'success');
        } else {
            await apiClient('/api/workspace/clients', {
                method: 'POST',
                body: JSON.stringify({ name, tax_id: tax || null }),
            });
            showToast(t('client-msg-created'), 'success');
        }
        closeWsClientModal();
        await loadSellerCache();
        renderSellerList();
        _syncWorkspaceSwitcher();
    } catch (e) {
        const m = e && (e as Error).message ? (e as Error).message : t('client-msg-save-fail');
        showToast(t('client-msg-save-fail') + ' · ' + m, 'fail');
    }
}

async function archiveWsClient() {
    if (!S.editingWsClientId) return;
    const ws = S.sellerClients.find((x: any) => Number(x.id) === Number(S.editingWsClientId));
    const ok = await showConfirm(
        t('wsclient-archive-confirm').replace('{name}', ws ? (ws as any).name : ''),
        { danger: true }
    );
    if (!ok) return;
    try {
        const archivedId = S.editingWsClientId;
        await apiClient('/api/workspace/clients/' + archivedId, { method: 'DELETE' });
        showToast(t('wsclient-archived'), 'success');
        // 归档的若正是当前账套 → 退回个人事务,避免悬空
        if (
            typeof window.getActiveWorkspaceClientId === 'function' &&
            Number(window.getActiveWorkspaceClientId()) === Number(archivedId) &&
            typeof window.enterPersonalMode === 'function'
        ) {
            window.enterPersonalMode();
        }
        closeWsClientModal();
        await loadSellerCache();
        renderSellerList();
        _syncWorkspaceSwitcher();
    } catch (e) {
        showToast(t('client-msg-save-fail'), 'fail');
    }
}

export {
    switchCustTab,
    loadSellerCache,
    renderSellerList,
    openWsClientModal,
    closeWsClientModal,
    saveWsClient,
    archiveWsClient,
};
