// ============================================================
// REFACTOR-C1 (2026-05-27) · 客户(Client)实体前端逻辑 clients 从 home.js 抽出为 ES module
//
// 来源:home.js L9691-10443 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================
/* global escapeHtml, showConfirm, _results, _drawerIdx, renderHistoryList */
// 注:t / showToast 已在 eslint.config.mjs 声明为全局 · 此处不再重复(避免 no-redeclare)。

// ============================================================
// v107 · 客户(Client)实体 · 全部前端逻辑
// ============================================================
(function () {
    let _clients = []; // 全局买方客户缓存
    let _editingClientId = null; // 买方弹窗当前编辑的客户 ID(null=新建)
    let _historyClientFilter = ''; // 历史页客户筛选

    // P3 · 客户管理页(账套主体 / 买方客户 双 tab)状态
    let _custTab = 'seller'; // 当前 tab:'seller' | 'buyer'
    const _buyerState = { page: 0, pageSize: 12, keyword: '' };
    const _buyerSelected = new Set(); // 跨页保留的勾选 id
    let _sellerClients = []; // 账套主体缓存
    const _sellerState = { keyword: '' };
    let _editingWsClientId = null; // 账套主体弹窗编辑 id(null=新建)

    // ---------- 工具 ----------
    function authH() {
        return { Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || '') };
    }
    async function apiClient(path, opts = {}) {
        const r = await fetch(path, {
            ...opts,
            headers: { 'Content-Type': 'application/json', ...authH(), ...(opts.headers || {}) },
        });
        if (!r.ok) {
            const err = await r.json().catch(() => ({}));
            throw new Error(err.detail || 'HTTP ' + r.status);
        }
        return r.json();
    }

    // ---------- 加载客户列表 ----------
    async function loadClientsCache() {
        try {
            const data = await apiClient('/api/clients');
            _clients = data.clients || [];
            window._clientsCache = _clients;
        } catch (e) {
            console.error('loadClientsCache fail', e);
            _clients = [];
        }
        // v118.21.0 · 通知异常栏客户下拉刷新
        try {
            if (typeof window._refreshExcClientFilter === 'function')
                window._refreshExcClientFilter();
        } catch (_) {
            /* silent · 通知下游刷新 */
        }
        // v118.28.0 · 通知顶栏客户切换器刷新
        try {
            if (typeof window._refreshClientSwitcher === 'function')
                window._refreshClientSwitcher();
        } catch (_) {
            /* silent · 通知下游刷新 */
        }
        return _clients;
    }

    // ---------- 客户管理页 · 渲染卡片 ----------
    function renderClientsGrid() {
        const wrap = document.getElementById('clients-grid');
        if (!wrap) return;
        if (!_clients.length) {
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
        wrap.innerHTML = _clients
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
    // P3 · 客户管理页 · tab 切换
    // ==========================================================
    function switchCustTab(tab) {
        _custTab = tab === 'buyer' ? 'buyer' : 'seller';
        document
            .querySelectorAll('[data-cust-tab]')
            .forEach((b) => b.classList.toggle('active', b.dataset.custTab === _custTab));
        const ps = document.getElementById('cust-pane-seller');
        const pb = document.getElementById('cust-pane-buyer');
        if (ps) ps.classList.toggle('active', _custTab === 'seller');
        if (pb) pb.classList.toggle('active', _custTab === 'buyer');
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
        window._workspaceClientsCache = _sellerClients;
        if (typeof window.renderWorkspaceControl === 'function') window.renderWorkspaceControl();
    }

    // ==========================================================
    // P3 · 账套主体 tab(= 工作空间 · 与右上角切换器双向同步)
    // ==========================================================
    async function loadSellerCache() {
        try {
            const data = await apiClient('/api/workspace/clients');
            _sellerClients = (data && (data.clients || data.items)) || [];
            window._workspaceClientsCache = _sellerClients;
        } catch (e) {
            console.error('loadSellerCache fail', e);
            _sellerClients = [];
        }
        return _sellerClients;
    }

    function _sellerFiltered() {
        const kw = _sellerState.keyword.trim().toLowerCase();
        if (!kw) return _sellerClients;
        return _sellerClients.filter(
            (c) =>
                (c.name || '').toLowerCase().includes(kw) ||
                (c.tax_id || '').toLowerCase().includes(kw)
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
            .map((c) => {
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
    function openWsClientModal(ws) {
        _editingWsClientId = ws ? ws.id : null;
        document.getElementById('wsclient-modal-title').textContent = t(
            ws ? 'wsclient-modal-edit' : 'wsclient-modal-new'
        );
        document.getElementById('wsclient-input-name').value = (ws && ws.name) || '';
        document.getElementById('wsclient-input-tax').value = (ws && ws.tax_id) || '';
        document.getElementById('wsclient-modal-archive').style.display = ws ? '' : 'none';
        document.getElementById('wsclient-modal-mask').style.display = 'flex';
        setTimeout(() => document.getElementById('wsclient-input-name').focus(), 50);
    }
    function closeWsClientModal() {
        document.getElementById('wsclient-modal-mask').style.display = 'none';
        _editingWsClientId = null;
    }
    async function saveWsClient() {
        const name = document.getElementById('wsclient-input-name').value.trim();
        const tax = document.getElementById('wsclient-input-tax').value.trim();
        if (!name) {
            showToast(t('client-msg-name-required'), 'fail');
            return;
        }
        try {
            if (_editingWsClientId) {
                await apiClient('/api/workspace/clients/' + _editingWsClientId, {
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
            const m = e && e.message ? e.message : t('client-msg-save-fail');
            showToast(t('client-msg-save-fail') + ' · ' + m, 'fail');
        }
    }
    async function archiveWsClient() {
        if (!_editingWsClientId) return;
        const ws = _sellerClients.find((x) => Number(x.id) === Number(_editingWsClientId));
        const ok = await showConfirm(
            t('wsclient-archive-confirm').replace('{name}', ws ? ws.name : ''),
            { danger: true }
        );
        if (!ok) return;
        try {
            const archivedId = _editingWsClientId;
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

    // ==========================================================
    // P3 · 买方客户 tab(横条列表 · 搜索/多选/批删/翻页)
    // ==========================================================
    function _buyerFiltered() {
        const kw = _buyerState.keyword.trim().toLowerCase();
        if (!kw) return _clients;
        return _clients.filter(
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
            info.textContent = total
                ? `${start + 1}–${Math.min(start + ps, total)} / ${total}`
                : '0';
        const prev = document.getElementById('buyer-prev');
        if (prev) prev.disabled = _buyerState.page <= 0;
        const next = document.getElementById('buyer-next');
        if (next) next.disabled = _buyerState.page >= maxPage;
        _updateBuyerBatchBar();
    }

    function _updateBuyerBatchBar() {
        const n = _buyerSelected.size;
        const bar = document.getElementById('buyer-batch-bar');
        if (bar) bar.style.display = n ? 'flex' : 'none';
        const cnt = document.getElementById('buyer-batch-count');
        if (cnt) cnt.textContent = t('cust-selected-n').replace('{n}', n);
        const all = document.getElementById('buyer-check-all');
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
        const ok = await showConfirm(t('cust-batch-del-confirm').replace('{n}', ids.length), {
            danger: true,
        });
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

    window.loadClientsPage = async function () {
        const st = document.getElementById('seller-tbody');
        if (st)
            st.innerHTML = `<div class="cust-loading">${escapeHtml(t('clients-loading'))}</div>`;
        const bt = document.getElementById('buyer-tbody');
        if (bt)
            bt.innerHTML = `<div class="cust-loading">${escapeHtml(t('clients-loading'))}</div>`;
        await Promise.all([loadSellerCache(), loadClientsCache()]);
        renderSellerList();
        renderBuyerList();
    };

    // 账套主体在别处(右上角弹窗)切换 → 客户管理页账套 tab 即时更新当前标记
    window.addEventListener('pearnly:workspace-changed', function () {
        if (typeof currentRoute !== 'undefined' && currentRoute === 'clients') renderSellerList();
    });

    // ---------- 弹窗 ----------
    function openClientModal(client) {
        _editingClientId = client ? client.id : null;
        const isEdit = !!client;
        document.getElementById('client-modal-title').textContent = t(
            isEdit ? 'client-modal-edit' : 'client-modal-new'
        );
        document.getElementById('client-input-name').value = (client && client.name) || '';
        document.getElementById('client-input-short').value = (client && client.short_name) || '';
        document.getElementById('client-input-tax').value = (client && client.tax_id) || '';
        document.getElementById('client-input-address').value = (client && client.address) || '';
        document.getElementById('client-input-contact').value =
            (client && client.contact_person) || '';
        document.getElementById('client-input-phone').value =
            (client && client.contact_phone) || '';
        document.getElementById('client-input-email').value =
            (client && client.contact_email) || '';
        document.getElementById('client-input-notes').value = (client && client.notes) || '';
        // 颜色
        const targetColor = (client && client.color) || '#111111';
        document.querySelectorAll('#client-color-picker .color-swatch').forEach((s) => {
            s.classList.toggle('active', s.dataset.color === targetColor);
        });
        // 删除按钮(仅编辑时显示)
        document.getElementById('client-modal-delete').style.display = isEdit ? '' : 'none';
        document.getElementById('client-modal-mask').style.display = 'flex';
        setTimeout(() => document.getElementById('client-input-name').focus(), 50);
    }
    function closeClientModal() {
        document.getElementById('client-modal-mask').style.display = 'none';
        _editingClientId = null;
    }
    function getActiveColor() {
        const sel = document.querySelector('#client-color-picker .color-swatch.active');
        return sel ? sel.dataset.color : '#111111';
    }

    async function saveClient() {
        const name = document.getElementById('client-input-name').value.trim();
        if (!name) {
            showToast(t('client-msg-name-required'), 'fail');
            return;
        }
        const payload = {
            name,
            short_name: document.getElementById('client-input-short').value.trim() || null,
            tax_id: document.getElementById('client-input-tax').value.trim() || null,
            address: document.getElementById('client-input-address').value.trim() || null,
            contact_person: document.getElementById('client-input-contact').value.trim() || null,
            contact_phone: document.getElementById('client-input-phone').value.trim() || null,
            contact_email: document.getElementById('client-input-email').value.trim() || null,
            notes: document.getElementById('client-input-notes').value.trim() || null,
            color: getActiveColor(),
        };
        try {
            if (_editingClientId) {
                await apiClient(`/api/clients/${_editingClientId}`, {
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
            const errMsg = e && e.message ? e.message : t('client-msg-save-fail');
            showToast(t('client-msg-save-fail') + ' · ' + errMsg, 'fail');
        }
    }

    async function deleteClient() {
        if (!_editingClientId) return;
        const c = _clients.find((x) => x.id === _editingClientId);
        if (!c) return;
        const msg = t('client-delete-confirm').replace('{name}', c.name);
        const ok = await showConfirm(msg, { danger: true });
        if (!ok) return;
        try {
            await apiClient(`/api/clients/${_editingClientId}`, { method: 'DELETE' });
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
    async function exportClient(clientId) {
        const c = _clients.find((x) => x.id === clientId);
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
            showToast(t('client-msg-save-fail') + ' · ' + (e.message || ''), 'fail');
        }
    }

    // ---------- 抽屉里下拉 ----------
    function refreshDrawerClientSelect() {
        const sel = document.getElementById('drawer-client-select');
        if (!sel) return;
        const cur = sel.value;
        sel.innerHTML =
            `<option value="">${escapeHtml(t('drawer-client-none'))}</option>` +
            _clients.map((c) => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join('');
        sel.value = cur || '';
    }

    // 抽屉打开后绑定客户下拉(从 history detail 拿 client_id 填充)
    // v118.16 · history_id 为 null 时只填充选项 · 不绑 onchange(识别中心 cache 命中时没 history_id)
    window.bindDrawerClient = function (history_id, current_client_id) {
        const sel = document.getElementById('drawer-client-select');
        if (!sel) return;
        refreshDrawerClientSelect();
        sel.value = current_client_id ? String(current_client_id) : '';
        if (!history_id) {
            // 没 history_id · 只填充选项 · 不绑 onchange · 用户选了也没用(史无 PK)
            sel.onchange = null;
            const addBtn = document.getElementById('drawer-client-add');
            if (addBtn) addBtn.onclick = () => openClientModal(null);
            return;
        }
        sel.onchange = async () => {
            const newCid = sel.value ? parseInt(sel.value, 10) : null;
            try {
                await apiClient(`/api/history/${history_id}/assign_client`, {
                    method: 'POST',
                    body: JSON.stringify({ client_id: newCid }),
                });
                showToast(t('client-msg-updated'), 'success');
                // P0-1: 保存后立即更新快照, 无需关闭抽屉即可推送
                const snap = _results[_drawerIdx];
                if (snap) snap.client_id = newCid;
                await loadClientsCache(); // 刷新统计
            } catch (e) {
                console.error(e);
                showToast(t('client-msg-save-fail'), 'fail');
                // 回滚
                sel.value = current_client_id ? String(current_client_id) : '';
            }
        };
        // 「+」快捷新建
        const addBtn = document.getElementById('drawer-client-add');
        if (addBtn) addBtn.onclick = () => openClientModal(null);
    };

    // v118.18 · 推荐分类 datalist 自动补全 · 缓存 5 分钟
    let _catCache = { fetched: 0, items: [], supplier_count: 0 };
    window.fillCategoryDatalist = async function () {
        try {
            const dl = document.getElementById('drawer-cat-datalist');
            // 如果缓存没过期 · 直接用
            const now = Date.now();
            if (now - _catCache.fetched < 5 * 60 * 1000) {
                if (dl) {
                    dl.innerHTML = _catCache.items
                        .map((c) => `<option value="${escapeHtml(c)}">`)
                        .join('');
                }
                _updateLearnedBadge(_catCache.supplier_count);
                return;
            }
            // 拉一次
            const r = await apiClient('/api/categories', { method: 'GET' });
            _catCache.fetched = now;
            _catCache.items = (r && r.categories) || [];
            _catCache.supplier_count = (r && r.supplier_count) || 0;
            if (dl) {
                dl.innerHTML = _catCache.items
                    .map((c) => `<option value="${escapeHtml(c)}">`)
                    .join('');
            }
            _updateLearnedBadge(_catCache.supplier_count);
        } catch (e) {
            console.warn('fillCategoryDatalist failed', e);
        }
    };
    function _updateLearnedBadge(n) {
        const tag = document.getElementById('drawer-cat-learned-tag');
        if (!tag) return;
        // 如果有学过的供应商映射 · badge 显示「已学 N」 · 否则保持「自动建议」默认
        if (n > 0) {
            tag.textContent = (t('drawer-suggest-learned-with-count') || '已学 {n}').replace(
                '{n}',
                n
            );
        }
    }

    // ---------- 历史页筛选 ----------
    function refreshHistoryClientFilter() {
        const sel = document.getElementById('history-client-filter');
        if (!sel) return;
        const cur = sel.value;
        sel.innerHTML =
            `<option value="">${escapeHtml(t('history-client-all'))}</option>` +
            _clients.map((c) => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join('');
        sel.value = cur || '';
    }

    window.getHistoryClientFilter = function () {
        return _historyClientFilter;
    };

    // ---------- 全局事件 ----------
    document.addEventListener('DOMContentLoaded', () => {
        // ===== 客户管理页 · tab 切换 =====
        const tabBar = document.querySelector('.cust-tab-bar');
        if (tabBar) {
            tabBar.addEventListener('click', (e) => {
                const b = e.target.closest('[data-cust-tab]');
                if (b) switchCustTab(b.dataset.custTab);
            });
        }

        // ===== 买方客户 tab =====
        const buyerNew = document.getElementById('btn-buyer-new');
        if (buyerNew) buyerNew.addEventListener('click', () => openClientModal(null));

        const buyerTbody = document.getElementById('buyer-tbody');
        if (buyerTbody) {
            buyerTbody.addEventListener('click', (e) => {
                const cb = e.target.closest('.buyer-row-check');
                if (cb) {
                    const cid = parseInt(cb.dataset.cid, 10);
                    if (cb.checked) _buyerSelected.add(cid);
                    else _buyerSelected.delete(cid);
                    const row = cb.closest('.cust-row');
                    if (row) row.classList.toggle('selected', cb.checked);
                    _updateBuyerBatchBar();
                    return;
                }
                const btn = e.target.closest('.cust-row-btn');
                if (btn) {
                    e.stopPropagation();
                    const cid = parseInt(btn.dataset.cid, 10);
                    if (btn.dataset.action === 'edit') {
                        const c = _clients.find((x) => x.id === cid);
                        if (c) openClientModal(c);
                    } else if (btn.dataset.action === 'export') {
                        exportClient(cid);
                    }
                    return;
                }
                const row = e.target.closest('.cust-row');
                if (row && !e.target.closest('.cust-cell-check')) {
                    const c = _clients.find((x) => x.id === parseInt(row.dataset.cid, 10));
                    if (c) openClientModal(c);
                }
            });
        }
        const buyerCheckAll = document.getElementById('buyer-check-all');
        if (buyerCheckAll) {
            buyerCheckAll.addEventListener('change', () => {
                const { items } = _buyerPageItems();
                items.forEach((c) => {
                    if (buyerCheckAll.checked) _buyerSelected.add(c.id);
                    else _buyerSelected.delete(c.id);
                });
                renderBuyerList();
            });
        }
        const buyerBatchCancel = document.getElementById('buyer-batch-cancel');
        if (buyerBatchCancel) buyerBatchCancel.addEventListener('click', clearBuyerSelection);
        const buyerBatchDel = document.getElementById('buyer-batch-delete');
        if (buyerBatchDel) buyerBatchDel.addEventListener('click', buyerBatchDelete);
        const buyerPrev = document.getElementById('buyer-prev');
        if (buyerPrev)
            buyerPrev.addEventListener('click', () => {
                if (_buyerState.page > 0) {
                    _buyerState.page--;
                    renderBuyerList();
                }
            });
        const buyerNext = document.getElementById('buyer-next');
        if (buyerNext)
            buyerNext.addEventListener('click', () => {
                _buyerState.page++;
                renderBuyerList();
            });
        const buyerSearch = document.getElementById('buyer-search');
        if (buyerSearch) {
            let dq;
            buyerSearch.addEventListener('input', () => {
                clearTimeout(dq);
                dq = setTimeout(() => {
                    _buyerState.keyword = buyerSearch.value;
                    _buyerState.page = 0;
                    const cl = document.getElementById('buyer-search-clear');
                    if (cl) cl.style.display = buyerSearch.value ? '' : 'none';
                    renderBuyerList();
                }, 200);
            });
        }
        const buyerSearchClear = document.getElementById('buyer-search-clear');
        if (buyerSearchClear)
            buyerSearchClear.addEventListener('click', () => {
                const s = document.getElementById('buyer-search');
                if (s) s.value = '';
                _buyerState.keyword = '';
                _buyerState.page = 0;
                buyerSearchClear.style.display = 'none';
                renderBuyerList();
            });

        // ===== 账套主体 tab =====
        const sellerNew = document.getElementById('btn-seller-new');
        if (sellerNew) sellerNew.addEventListener('click', () => openWsClientModal(null));
        const sellerTbody = document.getElementById('seller-tbody');
        if (sellerTbody) {
            sellerTbody.addEventListener('click', (e) => {
                const btn = e.target.closest('[data-saction]');
                if (!btn) return;
                e.stopPropagation();
                const wid = parseInt(btn.dataset.wid, 10);
                const act = btn.dataset.saction;
                const ws = _sellerClients.find((x) => Number(x.id) === wid);
                if (act === 'activate') {
                    if (typeof window.setActiveWorkspaceClientId === 'function')
                        window.setActiveWorkspaceClientId(wid);
                    renderSellerList();
                    if (typeof window.renderWorkspaceControl === 'function')
                        window.renderWorkspaceControl();
                    showToast(
                        t('seller-activated').replace('{name}', ws ? ws.name : ''),
                        'success'
                    );
                } else if (act === 'edit') {
                    if (ws) openWsClientModal(ws);
                } else if (act === 'archive') {
                    _editingWsClientId = wid;
                    archiveWsClient();
                }
            });
        }
        const sellerSearch = document.getElementById('seller-search');
        if (sellerSearch) {
            let dq2;
            sellerSearch.addEventListener('input', () => {
                clearTimeout(dq2);
                dq2 = setTimeout(() => {
                    _sellerState.keyword = sellerSearch.value;
                    const cl = document.getElementById('seller-search-clear');
                    if (cl) cl.style.display = sellerSearch.value ? '' : 'none';
                    renderSellerList();
                }, 200);
            });
        }
        const sellerSearchClear = document.getElementById('seller-search-clear');
        if (sellerSearchClear)
            sellerSearchClear.addEventListener('click', () => {
                const s = document.getElementById('seller-search');
                if (s) s.value = '';
                _sellerState.keyword = '';
                sellerSearchClear.style.display = 'none';
                renderSellerList();
            });

        // 账套主体编辑弹窗
        const wsClose = document.getElementById('wsclient-modal-close');
        if (wsClose) wsClose.addEventListener('click', closeWsClientModal);
        const wsCancel = document.getElementById('wsclient-modal-cancel');
        if (wsCancel) wsCancel.addEventListener('click', closeWsClientModal);
        const wsSave = document.getElementById('wsclient-modal-save');
        if (wsSave) wsSave.addEventListener('click', saveWsClient);
        const wsArchive = document.getElementById('wsclient-modal-archive');
        if (wsArchive) wsArchive.addEventListener('click', archiveWsClient);
        const wsMask = document.getElementById('wsclient-modal-mask');
        if (wsMask)
            wsMask.addEventListener('click', (e) => {
                if (e.target === wsMask) closeWsClientModal();
            });

        // ===== 买方客户编辑弹窗(复用) =====
        const closeBtn = document.getElementById('client-modal-close');
        if (closeBtn) closeBtn.addEventListener('click', closeClientModal);
        const cancelBtn = document.getElementById('client-modal-cancel');
        if (cancelBtn) cancelBtn.addEventListener('click', closeClientModal);
        const saveBtn = document.getElementById('client-modal-save');
        if (saveBtn) saveBtn.addEventListener('click', saveClient);
        const delBtn = document.getElementById('client-modal-delete');
        if (delBtn) delBtn.addEventListener('click', deleteClient);
        const mask = document.getElementById('client-modal-mask');
        if (mask)
            mask.addEventListener('click', (e) => {
                if (e.target === mask) closeClientModal();
            });

        // 颜色选择
        const picker = document.getElementById('client-color-picker');
        if (picker) {
            picker.addEventListener('click', (e) => {
                const sw = e.target.closest('.color-swatch');
                if (!sw) return;
                picker
                    .querySelectorAll('.color-swatch')
                    .forEach((s) => s.classList.remove('active'));
                sw.classList.add('active');
            });
        }

        // 历史页客户筛选
        const histFilter = document.getElementById('history-client-filter');
        if (histFilter) {
            histFilter.addEventListener('change', () => {
                _historyClientFilter = histFilter.value;
                if (typeof renderHistoryList === 'function') renderHistoryList();
            });
        }
    });

    // 初始预加载客户(应用启动后台加载)
    setTimeout(() => loadClientsCache(), 1000);
})();
