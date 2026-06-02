// ============================================================
// REFACTOR-C1 (2026-05-27) · 客户(Client)实体前端逻辑 clients 从 home.js 抽出为 ES module
// REFACTOR-WB (2026-06-02) · store 中心化 + 拆 4 子模块(store/helpers/buyer/seller)。
// ============================================================
/* global escapeHtml, _results, _drawerIdx, renderHistoryList */
import { S, _buyerState, _buyerSelected, _sellerState } from './clients-store.js';
import { apiClient, _updateLearnedBadge } from './clients-helpers.js';
import {
    loadClientsCache,
    renderBuyerList,
    openClientModal,
    closeClientModal,
    exportClient,
    _buyerPageItems,
    clearBuyerSelection,
    buyerBatchDelete,
    _updateBuyerBatchBar,
    saveClient,
    deleteClient,
    refreshDrawerClientSelect,
} from './clients-buyer.js';
import {
    switchCustTab,
    loadSellerCache,
    renderSellerList,
    openWsClientModal,
    closeWsClientModal,
    saveWsClient,
    archiveWsClient,
} from './clients-seller.js';

window.loadClientsPage = async function () {
    const st = document.getElementById('seller-tbody');
    if (st) st.innerHTML = `<div class="cust-loading">${escapeHtml(t('clients-loading'))}</div>`;
    const bt = document.getElementById('buyer-tbody');
    if (bt) bt.innerHTML = `<div class="cust-loading">${escapeHtml(t('clients-loading'))}</div>`;
    await Promise.all([loadSellerCache(), loadClientsCache()]);
    renderSellerList();
    renderBuyerList();
};

// 账套主体在别处(右上角弹窗)切换 → 客户管理页账套 tab 即时更新当前标记
window.addEventListener('pearnly:workspace-changed', function () {
    if (typeof currentRoute !== 'undefined' && currentRoute === 'clients') renderSellerList();
});

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

window.fillCategoryDatalist = async function () {
    try {
        const dl = document.getElementById('drawer-cat-datalist');
        // 如果缓存没过期 · 直接用
        const now = Date.now();
        if (now - S.catCache.fetched < 5 * 60 * 1000) {
            if (dl) {
                dl.innerHTML = S.catCache.items
                    .map((c) => `<option value="${escapeHtml(c)}">`)
                    .join('');
            }
            _updateLearnedBadge(S.catCache.supplier_count);
            return;
        }
        // 拉一次
        const r = await apiClient('/api/categories', { method: 'GET' });
        S.catCache.fetched = now;
        S.catCache.items = (r && r.categories) || [];
        S.catCache.supplier_count = (r && r.supplier_count) || 0;
        if (dl) {
            dl.innerHTML = S.catCache.items
                .map((c) => `<option value="${escapeHtml(c)}">`)
                .join('');
        }
        _updateLearnedBadge(S.catCache.supplier_count);
    } catch (e) {
        console.warn('fillCategoryDatalist failed', e);
    }
};

window.getHistoryClientFilter = function () {
    return S.historyClientFilter;
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
                    const c = S.clients.find((x) => x.id === cid);
                    if (c) openClientModal(c);
                } else if (btn.dataset.action === 'export') {
                    exportClient(cid);
                }
                return;
            }
            const row = e.target.closest('.cust-row');
            if (row && !e.target.closest('.cust-cell-check')) {
                const c = S.clients.find((x) => x.id === parseInt(row.dataset.cid, 10));
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
            const ws = S.sellerClients.find((x) => Number(x.id) === wid);
            if (act === 'activate') {
                if (typeof window.setActiveWorkspaceClientId === 'function')
                    window.setActiveWorkspaceClientId(wid);
                renderSellerList();
                if (typeof window.renderWorkspaceControl === 'function')
                    window.renderWorkspaceControl();
                showToast(t('seller-activated').replace('{name}', ws ? ws.name : ''), 'success');
            } else if (act === 'edit') {
                if (ws) openWsClientModal(ws);
            } else if (act === 'archive') {
                S.editingWsClientId = wid;
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
            picker.querySelectorAll('.color-swatch').forEach((s) => s.classList.remove('active'));
            sw.classList.add('active');
        });
    }

    // 历史页客户筛选
    const histFilter = document.getElementById('history-client-filter');
    if (histFilter) {
        histFilter.addEventListener('change', () => {
            S.historyClientFilter = histFilter.value;
            if (typeof renderHistoryList === 'function') renderHistoryList();
        });
    }
});

// 初始预加载客户(应用启动后台加载)
setTimeout(() => loadClientsCache(), 1000);
