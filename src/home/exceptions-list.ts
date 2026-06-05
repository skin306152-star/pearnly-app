// ============================================================
// REFACTOR-WB (2026-06-02) · 异常栏 · 列表/KPI/chips/分页/红点/批量动作 · 从 exceptions.js 抽出 · verbatim 0 改逻辑。
// ============================================================
/* global escapeHtml, showConfirm, currentLang, humanizeError */
import { _excState, _flags } from './exceptions-store.js';
import {
    _tn,
    _sevSvg,
    _emptySvg,
    _fmtMoney,
    _shortDate,
    excRuleLabel,
    EXC_RULE_GROUPS,
} from './exceptions-helpers.js';
import { openExcDrawer } from './exceptions-drawer.js';

// 红点徽章 · 全局可用 · 路由切换 + 周期刷新都调它
async function refreshExcBadge() {
    try {
        // v118.21.0 · 徽章数跟随 currentClient · 防切走客户后徽章数和列表不一致
        // v118.21.1 · 徽章固定数 pending(不论用户当前在看哪个状态 tab)
        const cid = _excState.currentClient || '';
        const url =
            '/api/exceptions/stats?status=pending' +
            (cid ? '&client_id=' + encodeURIComponent(cid) : '');
        const resp = await fetch(url, {
            headers: {
                Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
            },
        });
        if (!resp.ok) return;
        const stats = await resp.json();
        const badge = document.getElementById('nav-exc-badge');
        if (!badge) return;
        const n = parseInt(stats.pending || 0, 10);
        if (n > 0) {
            badge.textContent = n > 99 ? '99+' : String(n);
            badge.style.display = '';
        } else {
            badge.style.display = 'none';
        }
    } catch (e) {
        /* 静默 · 不打断主流程 */
    }
}

function renderKpis(stats?: any) {
    document.getElementById('exc-kpi-pending')!.textContent = stats.pending || 0;
    document.getElementById('exc-kpi-high')!.textContent = stats.high_severity || 0;
    document.getElementById('exc-kpi-resolved')!.textContent = stats.resolved || 0;
    document.getElementById('exc-kpi-learned')!.textContent = stats.learned_rules || 0;
    // v118.21.1 · status tab 计数同步
    const cp = document.getElementById('exc-status-tab-count-pending');
    const cr = document.getElementById('exc-status-tab-count-resolved');
    const ci = document.getElementById('exc-status-tab-count-ignored');
    if (cp) cp.textContent = stats.pending || 0;
    if (cr) cr.textContent = stats.resolved || 0;
    if (ci) ci.textContent = stats.ignored || 0;
    // active 态
    const tabs = document.querySelectorAll('#exc-status-tabs .exc-status-tab');
    tabs.forEach((t) => {
        t.classList.toggle(
            'active',
            (t as HTMLElement).dataset.status === (_excState.currentStatus || 'pending')
        );
    });
}

// 按规则组求和(currentRule 可能是逗号分隔的一组 rule_code)
function _sumByRule(byRule: Record<string, number>, ruleParam: string) {
    return ruleParam.split(',').reduce((s, c) => s + (byRule[c] || 0), 0);
}

function renderChips(stats?: any) {
    const wrap = document.getElementById('exc-chips');
    if (!wrap) return;
    const byRule = stats.by_rule || {};

    const allActive = !_excState.currentRule;
    let html = `<button class="exc-chip ${allActive ? 'active' : ''}" data-rule="">
        <span>${escapeHtml(t('exc-chip-all'))}</span>
        <span class="exc-chip-count">${stats.pending || 0}</span>
    </button>`;
    for (const grp of EXC_RULE_GROUPS) {
        const ruleParam = grp.codes.join(',');
        const n = _sumByRule(byRule, ruleParam);
        const active = _excState.currentRule === ruleParam;
        if (n === 0 && !active) continue; // 0 数 + 非当前激活 → 隐藏 chip 减杂讯
        html += `<button class="exc-chip ${active ? 'active' : ''}" data-rule="${escapeHtml(ruleParam)}">
            <span>${escapeHtml(t(grp.labelKey))}</span>
            <span class="exc-chip-count">${n}</span>
        </button>`;
    }
    wrap.innerHTML = html;
    wrap.querySelectorAll('.exc-chip').forEach((btn) => {
        btn.addEventListener('click', () => {
            const rc = (btn as HTMLElement).dataset.rule || null;
            _excState.currentRule = rc;
            loadExceptionsList();
        });
    });
}

function renderList(items?: any) {
    const wrap = document.getElementById('exc-list');
    if (!wrap) return;
    if (!items || items.length === 0) {
        wrap.innerHTML = `<div class="exc-empty">
            ${_emptySvg()}
            <div class="exc-empty-title">${escapeHtml(t('exc-empty-title'))}</div>
            <div>${escapeHtml(t('exc-empty-desc'))}</div>
        </div>`;
        renderListFoot(); // 空列表也更新底部计数(0/0)
        return;
    }
    const checkSvg = `<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7l3 3 5-5"/></svg>`;
    const showCheckbox = (_excState.currentStatus || 'pending') === 'pending';
    wrap.innerHTML = items
        .map((it: any) => {
            const sev = it.severity || 'medium';
            const ruleLabel = excRuleLabel(it);
            const seller =
                it.seller_name && it.seller_name.trim() ? it.seller_name : t('exc-no-seller');
            const filename = it.filename || '—';
            const date = _shortDate(it.invoice_date || it.created_at);
            const isPending = it.status === 'pending';
            const checked = _excState.selectedIds.has(it.id);
            const checkCellVisible = showCheckbox && isPending;
            return `
            <div class="exc-row sev-${escapeHtml(sev)} ${checked ? 'selected' : ''}" data-exc-id="${escapeHtml(String(it.id))}">
                <div class="exc-row-check ${checked ? 'checked' : ''}" data-check-id="${escapeHtml(String(it.id))}" ${checkCellVisible ? '' : 'style="visibility:hidden;"'}>${checkSvg}</div>
                <div class="exc-row-sev">${_sevSvg(sev)}</div>
                <div class="exc-row-main">
                    <div class="exc-row-title">${escapeHtml(seller)} · ${escapeHtml(filename)}</div>
                    <div class="exc-row-meta">
                        ${it.invoice_no ? `<span><b>${escapeHtml(it.invoice_no)}</b></span>` : ''}
                        <span>${escapeHtml(date)}</span>
                    </div>
                </div>
                <div class="exc-row-rule r-${escapeHtml(sev)}">${escapeHtml(ruleLabel)}</div>
                <div class="exc-row-amount">${escapeHtml(_fmtMoney(it.total_amount))}</div>
            </div>
        `;
        })
        .join('');
    // 行点击 → 抽屉(checkbox 区域阻断)
    wrap.querySelectorAll('.exc-row').forEach((row) => {
        row.addEventListener('click', (e) => {
            if ((e.target as HTMLElement).closest('.exc-row-check')) return; // checkbox 自己处理
            const id = (row as HTMLElement).dataset.excId;
            if (id) openExcDrawer(parseInt(id, 10));
        });
    });
    // checkbox 切换
    wrap.querySelectorAll('.exc-row-check').forEach((box) => {
        box.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = parseInt((box as HTMLElement).dataset.checkId!, 10);
            if (!id) return;
            if (_excState.selectedIds.has(id)) {
                _excState.selectedIds.delete(id);
                box.classList.remove('checked');
                box.closest('.exc-row')!.classList.remove('selected');
            } else {
                _excState.selectedIds.add(id);
                box.classList.add('checked');
                box.closest('.exc-row')!.classList.add('selected');
            }
            renderBatchBar();
        });
    });
    renderBatchBar();
    renderListFoot();
}

// v118.20.5 · 批量栏渲染
function renderBatchBar() {
    const bar = document.getElementById('exc-batch-bar');
    const cnt = document.getElementById('exc-batch-count');
    if (!bar || !cnt) return;
    const n = _excState.selectedIds.size;
    if (n === 0) {
        bar.style.display = 'none';
    } else {
        bar.style.display = '';
        cnt.textContent = _tn('exc-batch-count', { n });
    }
}

// v118.20.5 · 列表底部计数 + 加载更多按钮显示控制
function renderListFoot() {
    const foot = document.getElementById('exc-list-foot');
    const cnt = document.getElementById('exc-list-count');
    const more = document.getElementById('exc-loadmore');
    if (!foot || !cnt || !more) return;
    const shown = _excState.listCache.length;
    if (shown === 0) {
        foot.style.display = 'none';
        return;
    }
    foot.style.display = '';
    // 当前筛选下的 pending 总数(从 stats 取 · 跟 chip 数同步)
    let total = shown;
    const stats = _excState.statsCache as any;
    if (stats) {
        if (_excState.currentRule) {
            total = _sumByRule(stats.by_rule || {}, _excState.currentRule) || shown;
        } else {
            total = stats.pending || shown;
        }
    }
    _excState.total = total;
    cnt.textContent = _tn('exc-list-count', { shown, total });
    // 加载更多按钮:还有未加载的 + 没到 500 上限
    const canLoadMore = shown < total && shown < 500;
    more.style.display = canLoadMore ? '' : 'none';
}

async function loadExceptionsStats() {
    try {
        if (navigator.onLine === false) throw new Error('offline');
        const cid = _excState.currentClient || '';
        const st = _excState.currentStatus || 'pending';
        const params = new URLSearchParams();
        params.set('status', st);
        if (cid) params.set('client_id', cid);
        const url = '/api/exceptions/stats?' + params.toString();
        const resp = await fetch(url, {
            headers: {
                Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
            },
        });
        if (!resp.ok) throw new Error('http ' + resp.status);
        const stats = await resp.json();
        _excState.statsCache = stats;
        renderKpis(stats);
        renderChips(stats);
        return stats;
    } catch (e) {
        console.warn('loadExceptionsStats fail', e);
        // 不显式 toast(列表加载会触发 toast · 避免双弹)· 但 KPI 显「—」
        return null;
    }
}

function _renderListError(isOffline?: any) {
    const wrap = document.getElementById('exc-list');
    if (!wrap) return;
    const errSvg = `<svg class="exc-error-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="18" cy="18" r="14"/>
        <line x1="18" y1="11" x2="18" y2="19"/>
        <circle cx="18" cy="23" r="0.8" fill="currentColor"/>
    </svg>`;
    const title = isOffline ? t('exc-offline') : t('exc-error-retry-title');
    const desc = isOffline ? '' : t('exc-error-retry-desc');
    wrap.innerHTML = `
        <div class="exc-error">
            ${errSvg}
            <div class="exc-error-msg">${escapeHtml(title)}${desc ? ' · ' + escapeHtml(desc) : ''}</div>
            <button class="btn btn-sm btn-secondary" id="exc-retry-btn" type="button">${escapeHtml(t('exc-retry-btn'))}</button>
        </div>`;
    const btn = document.getElementById('exc-retry-btn');
    if (btn)
        btn.addEventListener(
            'click',
            () => window.loadExceptionsPage && window.loadExceptionsPage()
        );
}

async function loadExceptionsList(opts?: any) {
    opts = opts || {};
    const append = !!opts.append;
    const wrap = document.getElementById('exc-list');
    if (!append && wrap && _excState.listCache.length === 0) {
        wrap.innerHTML = `<div class="exc-loading">${escapeHtml(t('exc-loading'))}</div>`;
    }
    const params = new URLSearchParams();
    params.set('status', _excState.currentStatus || 'pending');
    if (_excState.currentRule) params.set('rule_code', _excState.currentRule);
    if (_excState.currentClient) params.set('client_id', _excState.currentClient);
    const offset = append ? _excState.listCache.length : 0;
    params.set('limit', String(_excState.pageSize));
    params.set('offset', String(offset));
    try {
        if (navigator.onLine === false) throw new Error('offline');
        const resp = await fetch('/api/exceptions/list?' + params.toString(), {
            headers: {
                Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
            },
        });
        if (!resp.ok) throw new Error('http ' + resp.status);
        const data = await resp.json();
        const newItems = data.items || [];
        if (append) {
            _excState.listCache = _excState.listCache.concat(newItems);
        } else {
            _excState.listCache = newItems;
            // 切换 chip / 全量重载 · 清空选中(避免选中已不在列表的项)
            _excState.selectedIds.clear();
        }
        _excState.loadFailed = false;
        renderList(_excState.listCache);
        // 重渲 chips · 让 active 状态跟随
        if (_excState.statsCache) renderChips(_excState.statsCache);
    } catch (e) {
        console.warn('loadExceptionsList fail', e);
        _excState.loadFailed = true;
        const isOffline =
            navigator.onLine === false || String((e as any).message || '').includes('offline');
        // append 失败:仅 toast · 不替换列表(用户已加载的不丢)
        if (append) {
            showToast(t('exc-toast-load-fail'), 'error');
        } else {
            _renderListError(isOffline);
            showToast(isOffline ? t('exc-offline') : t('exc-toast-load-fail'), 'error');
        }
    }
}

// v118.20.5 · 分页 · 加载更多
async function loadMore() {
    if (_excState.loading) return;
    if (_excState.listCache.length >= 500) return;
    _excState.loading = true;
    try {
        await loadExceptionsList({ append: true });
    } finally {
        _excState.loading = false;
    }
}

// 主入口 · routeTo 调它
// v118.21.0 · 把客户缓存灌到下拉里 · 进页 / 客户列表更新后调
function _refreshExcClientFilter() {
    const sel = document.getElementById('exc-client-filter');
    if (!sel) return;
    const list = window._clientsCache || [];
    const cur = _excState.currentClient || '';
    const allLabel = typeof t === 'function' ? t('history-client-all') : '全部客户';
    sel.innerHTML =
        `<option value="">${escapeHtml(allLabel)}</option>` +
        list.map((c) => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join('');
    (sel as HTMLSelectElement).value = cur;
}

async function actionBatchResolve() {
    if (_flags.batchLoading) return;
    const ids = Array.from(_excState.selectedIds);
    if (ids.length === 0) return;
    const ok = await showConfirm(_tn('exc-batch-confirm-resolve', { n: ids.length }));
    if (!ok) return;
    _flags.batchLoading = true;
    const dismiss = showToast(_tn('exc-batch-count', { n: ids.length }) + ' …', 'loading', 0);
    try {
        const resp = await fetch('/api/exceptions/batch', {
            method: 'POST',
            headers: {
                Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ids, action: 'resolve' }),
        });
        if (!resp.ok) throw new Error('http ' + resp.status);
        const data = await resp.json();
        dismiss();
        showToast(_tn('exc-toast-batch-resolved', { n: data.processed || 0 }), 'success');
        _excState.selectedIds.clear();
        await loadExceptionsStats();
        await loadExceptionsList();
        refreshExcBadge();
    } catch (e) {
        dismiss();
        console.warn('batch resolve fail', e);
        showToast(t('exc-toast-batch-fail'), 'error');
    } finally {
        _flags.batchLoading = false;
    }
}

async function actionBatchIgnore() {
    if (_flags.batchLoading) return;
    const ids = Array.from(_excState.selectedIds);
    if (ids.length === 0) return;
    const ok = await showConfirm(_tn('exc-batch-confirm-ignore', { n: ids.length }), {
        danger: false,
    });
    if (!ok) return;
    _flags.batchLoading = true;
    const dismiss = showToast(_tn('exc-batch-count', { n: ids.length }) + ' …', 'loading', 0);
    try {
        const resp = await fetch('/api/exceptions/batch', {
            method: 'POST',
            headers: {
                Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ids, action: 'ignore' }),
        });
        if (!resp.ok) throw new Error('http ' + resp.status);
        const data = await resp.json();
        dismiss();
        showToast(
            _tn('exc-toast-batch-ignored', {
                n: data.processed || 0,
                wl: data.whitelist_added || 0,
            }),
            'success'
        );
        _excState.selectedIds.clear();
        await loadExceptionsStats();
        await loadExceptionsList();
        refreshExcBadge();
    } catch (e) {
        dismiss();
        console.warn('batch ignore fail', e);
        showToast(t('exc-toast-batch-fail'), 'error');
    } finally {
        _flags.batchLoading = false;
    }
}

function clearBatchSelection() {
    _excState.selectedIds.clear();
    // 重渲列表(摘掉 selected 态)· 不发请求
    renderList(_excState.listCache);
}

export {
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
};
