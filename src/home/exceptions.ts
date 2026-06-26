// ============================================================
// REFACTOR-C1 (2026-05-27) · 异常栏 列表页 exceptions 从 home.js 抽出为 ES module
// REFACTOR-WB (2026-06-02) · store 中心化 + 拆 6 子模块(store/helpers/list/drawer/drawer-render/learned)。
// ============================================================
/* global escapeHtml, showConfirm, currentLang, humanizeError */
import { _excState, _drawer } from './exceptions-store.js';
import {
    refreshExcBadge,
    renderKpis,
    renderChips,
    renderList,
    loadExceptionsStats,
    loadExceptionsList,
    loadMore,
    _refreshExcClientFilter,
    clearBatchSelection,
    actionBatchResolve,
    actionBatchIgnore,
} from './exceptions-list.js';
import { closeExcDrawer, actionResolve, actionIgnore } from './exceptions-drawer.js';
import { renderDrawer } from './exceptions-drawer-render.js';
import { loadLearnedRules } from './exceptions-learned.js';

window.loadExceptionsPage = async function () {
    if (_excState.loading) return;
    _excState.loading = true;
    try {
        _refreshExcClientFilter();
        // ERP 推送异常块已搬至集成页「推送异常」tab(由 _activateIntTopTab 触发加载)
        await loadExceptionsStats();
        await loadExceptionsList();
    } finally {
        _excState.loading = false;
    }
};

// 暴露红点刷新 · 启动时 + 周期调用
window.refreshExcBadge = refreshExcBadge;
// v118.21.0 · 客户列表加载完毕后给异常栏刷下拉
window._refreshExcClientFilter = _refreshExcClientFilter;
// v118.28.0 · 暴露状态给顶栏客户切换器联动
window._excState = _excState as unknown as Record<string, unknown>;

// 切语言时用缓存重渲(不发请求 · 即时无闪烁)
window._rerenderExceptions = function () {
    // v118.21.0.1 · 客户下拉的「全部客户」选项也是 t() 渲染 · 切语言要刷
    try {
        _refreshExcClientFilter();
    } catch (_) {
        /* silent · 通知下游刷新 */
    }
    if (_excState.statsCache) {
        renderKpis(_excState.statsCache);
        renderChips(_excState.statsCache);
    }
    if (_excState.listCache && _excState.listCache.length) {
        renderList(_excState.listCache);
    }
    // 抽屉打开时也跟着重渲
    if (_drawer.openExcId) renderDrawer();
};

// 抽屉事件接线(deferred · 等 DOM 就绪)
document.addEventListener('click', (e) => {
    if ((e.target as HTMLElement).closest('#exc-drawer-close')) closeExcDrawer();
    if ((e.target as HTMLElement).closest('#exc-drawer-mask')) closeExcDrawer();
    if ((e.target as HTMLElement).closest('#exc-btn-resolve')) actionResolve();
    if ((e.target as HTMLElement).closest('#exc-btn-ignore')) actionIgnore();
    // v118.20.5 · 批量栏 + 加载更多
    if ((e.target as HTMLElement).closest('#exc-batch-resolve')) actionBatchResolve();
    if ((e.target as HTMLElement).closest('#exc-batch-ignore')) actionBatchIgnore();
    if ((e.target as HTMLElement).closest('#exc-batch-clear')) clearBatchSelection();
    if ((e.target as HTMLElement).closest('#exc-loadmore')) loadMore();
});
// ESC 关抽屉
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && _drawer.openExcId) closeExcDrawer();
});

// 「刷新」按钮(页内)
document.addEventListener('click', (e) => {
    const btn = (e.target as HTMLElement).closest('#btn-exc-refresh');
    if (!btn) return;
    if (typeof window.loadExceptionsPage === 'function') window.loadExceptionsPage();
    refreshExcBadge();
});

// v118.21.0 · 客户筛选切换 · 重置 chip / 选中 · 重拉数据
document.addEventListener('change', (e) => {
    if (!(e.target as HTMLElement).closest('#exc-client-filter')) return;
    const sel = e.target as HTMLSelectElement;
    _excState.currentClient = sel.value || '';
    _excState.currentRule = null; // 切客户后还原全部规则 chip
    _excState.selectedIds.clear(); // 清空多选(列表会变)
    _excState.listCache = [];
    if (typeof window.loadExceptionsPage === 'function') window.loadExceptionsPage();
    refreshExcBadge();
});

// v118.21.1 · status tab 切换(待复核 / 已处理 / 已忽略)
document.addEventListener('click', (e) => {
    const tab = (e.target as HTMLElement).closest(
        '#exc-status-tabs .exc-status-tab'
    ) as HTMLElement;
    if (!tab) return;
    const newStatus = tab.dataset.status || 'pending';
    if (newStatus === _excState.currentStatus) return;
    _excState.currentStatus = newStatus;
    _excState.currentRule = null; // 切状态后还原全部规则 chip
    _excState.selectedIds.clear(); // 清多选
    _excState.listCache = [];
    if (typeof window.loadExceptionsPage === 'function') window.loadExceptionsPage();
});

// v118.20.5 · 网络恢复时 · 若上次加载失败 · 自动重试
window.addEventListener('online', () => {
    if (
        _excState.loadFailed &&
        document.getElementById('page-exceptions')?.classList.contains('show')
    ) {
        window.loadExceptionsPage && window.loadExceptionsPage();
    }
});

// 启动后立即拉一次徽章数 · 每 60 秒刷一次
setTimeout(refreshExcBadge, 1500);
setInterval(refreshExcBadge, 60000);

window.loadLearnedRules = loadLearnedRules;

// 删除按钮事件(委托)
document.addEventListener('click', async (e) => {
    const btn = (e.target as HTMLElement).closest('[data-del-wl]') as HTMLElement;
    if (!btn) return;
    const wlId = parseInt(btn.dataset.delWl!, 10);
    if (!wlId) return;
    const row = btn.closest('.learned-row');
    const sellerEl = row && row.querySelector('.learned-seller');
    const sellerName = sellerEl ? sellerEl.textContent!.trim() : '';
    const msg = t('set-learned-del-confirm').replace('{seller}', sellerName);
    const ok = await showConfirm(msg, { danger: true });
    if (!ok) return;
    try {
        const resp = await fetch('/api/exception-whitelist/' + wlId, {
            method: 'DELETE',
            headers: {
                Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
            },
        });
        if (!resp.ok) throw new Error('http ' + resp.status);
        showToast(t('set-learned-del-ok'), 'success');
        loadLearnedRules();
        // 异常栏徽章可能不变(只删白名单 · 不复活拦截)· 但学习规则数变 · 刷一次 stats
        if (
            typeof window.loadExceptionsPage === 'function' &&
            document.getElementById('page-exceptions')?.classList.contains('show')
        ) {
            window.loadExceptionsPage();
        }
    } catch (err) {
        console.warn('delete whitelist fail', err);
        showToast(t('set-learned-del-fail'), 'error');
    }
});
