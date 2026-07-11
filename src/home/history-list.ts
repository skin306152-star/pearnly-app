// ============================================================
// REFACTOR-C1-home-batch4 (2026-05-31) · 发票记录页【列表侧】从 home.js 抽出为独立 ES module
//
// 来源:home.js verbatim 0 改逻辑 · updateHistoryBatchBar / clearHistorySelection /
//   loadHistoryPage / renderHistoryList。
// 共享态 _historyState / _historySelected 仍在 home.js 顶层 const(本 module 与 history-drawer.js
//   都 bare 读写其属性 · 同 realm 全局环境自动桥 · 属性 mutation 不触发 no-global-assign)。
// 桥回:window.loadHistoryPage/renderHistoryList/updateHistoryBatchBar/clearHistorySelection
//   (home.js routeTo/applyLang + history-drawer.js 的 IIFE/saveHistoryEdits/openHistoryMenu 调)。
// 自举:直接刷新落在 history 路由时(routeTo 在本 module 加载前已跑 · window.loadHistoryPage 未就绪
//   被 795 守卫跳过)· 本 module 加载后按 currentRoute 自触发一次(同 clients.js 范式)。
// ============================================================
/* global escapeHtml, svgIcon, token, _historyState, _historySelected, _showSessionRevokedModal */

type HistoryRow = {
    id: string;
    confidence?: string;
    created_at: string;
    filename?: string;
    page_count?: number;
    invoice_no?: string;
    seller_name?: string;
    category_tag?: string;
    source_total?: number;
    source_index?: number;
    total_amount?: number | null;
    invoice_date?: string;
    edited?: boolean;
    edit_count?: number;
    smart_assigned_flag?: boolean;
    source?: string;
    buyer_name?: string | null;
    vat_amount?: string | null;
    status?: string; // 后端派生:confirmed | pending | failed
};

function updateHistoryBatchBar() {
    const bar = document.getElementById('history-batch-bar');
    const countEl = document.getElementById('history-batch-count');
    const checkAll = document.getElementById('history-check-all');
    if (!bar || !countEl) return;

    const n = _historySelected.size;
    if (n > 0) {
        bar.style.display = '';
        countEl.textContent = t('history-batch-count', { n });
    } else {
        bar.style.display = 'none';
    }

    // "全选" checkbox 三态:全选/部分/全不选
    if (checkAll) {
        const items = (_historyState.items || []) as HistoryRow[];
        if (items.length === 0) {
            (checkAll as HTMLInputElement).checked = false;
            (checkAll as HTMLInputElement).indeterminate = false;
        } else {
            const selectedInPage = items.filter((r: HistoryRow) =>
                _historySelected.has(r.id)
            ).length;
            (checkAll as HTMLInputElement).checked = selectedInPage === items.length;
            (checkAll as HTMLInputElement).indeterminate =
                selectedInPage > 0 && selectedInPage < items.length;
        }
    }
}

function clearHistorySelection() {
    _historySelected.clear();
    updateHistoryBatchBar();
}

// 汇总卡:填充各状态计数(后端全量分布)+ 高亮当前选中卡
function renderHistorySummary() {
    const c = _historyState.statusCounts || { all: 0, confirmed: 0, pending: 0, failed: 0 };
    const set = (id: string, n: number) => {
        const el = document.getElementById(id);
        if (el) el.textContent = String(n);
    };
    set('hist-count-all', c.all);
    set('hist-count-confirmed', c.confirmed);
    set('hist-count-pending', c.pending);
    set('hist-count-failed', c.failed);
    const active = _historyState.statusFilter || 'all';
    document.querySelectorAll('#history-summary .hist-card').forEach((card) => {
        card.classList.toggle('active', (card as HTMLElement).dataset.statusFilter === active);
    });
}

async function loadHistoryPage() {
    if (!_userInfo) {
        setTimeout(() => loadHistoryPage(), 300);
        return;
    }
    const freeBlock = document.getElementById('history-free-block');
    const main = document.getElementById('history-main');
    const empty = document.getElementById('history-empty');
    if (!freeBlock || !main || !empty) {
        console.warn('[History] container missing');
        return;
    }

    if (!_userInfo.can_view_history) {
        freeBlock.style.display = '';
        main.style.display = 'none';
        empty.style.display = 'none';
        return;
    }
    freeBlock.style.display = 'none';

    _historyState.loading = true;
    try {
        const offset = _historyState.page * _historyState.pageSize;
        const params = new URLSearchParams({
            limit: _historyState.pageSize,
            offset: offset,
        } as unknown as Record<string, string>);
        if (_historyState.keyword) params.set('keyword', _historyState.keyword);
        // 汇总卡 / 状态下拉 + 来源下拉(默认 all 不传 · 后端白名单收敛)
        if (_historyState.statusFilter && _historyState.statusFilter !== 'all')
            params.set('status', String(_historyState.statusFilter));
        if (_historyState.sourceFilter && _historyState.sourceFilter !== 'all')
            params.set('source', String(_historyState.sourceFilter));
        // v118.28.0 · 顶栏客户切换器过滤(唯一来源 · 14b.3 后删除了重复 UI)
        const cid =
            typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId() : null;
        if (cid) params.set('client_id', String(cid));
        // 跟随账套主体:带 X-Workspace-Client-Id 头(后端 active_workspace_for_request 已按它过滤)。
        // 原裸 fetch 不带此头 → 不跟随账套;切账套→core-boot 重载本页→带新 ws 重新拉数。
        const resp = await fetch(`/api/history?${params}`, {
            headers: Object.assign(
                { Authorization: 'Bearer ' + token },
                typeof window._wsHeader === 'function' ? window._wsHeader() : {}
            ),
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
            window.location.href = window.loginUrl!();
            return;
        }
        const data = await resp.json();
        _historyState.items = data.items || [];
        _historyState.total = data.total || 0;
        _historyState.statusCounts = data.status_counts || {
            all: 0,
            confirmed: 0,
            pending: 0,
            failed: 0,
        };
        // 拉到新一页后 · 只保留当前页里仍然存在的那些选中项
        const currentIds = new Set(
            (_historyState.items as HistoryRow[]).map((r: HistoryRow) => r.id)
        );
        for (const id of Array.from(_historySelected)) {
            if (!currentIds.has(id as string)) _historySelected.delete(id);
        }
        renderHistoryList();
    } catch (e) {
        console.error('load history failed', e);
    } finally {
        _historyState.loading = false;
    }
}

function renderHistoryList() {
    const main = document.getElementById('history-main');
    const empty = document.getElementById('history-empty');
    const items = _historyState.items as HistoryRow[];

    // v0.11 · 更新匹配计数
    const matchesEl = document.getElementById('history-search-matches');
    if (matchesEl) {
        matchesEl.textContent = _historyState.keyword
            ? t('search-matches', { n: _historyState.total })
            : '';
    }

    if (items.length === 0 && _historyState.total === 0 && !_historyState.keyword) {
        main!.style.display = 'none';
        empty!.style.display = '';
        return;
    }
    main!.style.display = '';
    empty!.style.display = 'none';

    // 头部统计
    let highCount = 0;
    items.forEach((r: HistoryRow) => {
        if (r.confidence === 'high') highCount++;
    });
    const avgConfPct = items.length > 0 ? Math.round((highCount / items.length) * 100) : 0;

    document.getElementById('history-stats')!.innerHTML = `
        <div class="rh-stat">
            <span class="rh-stat-label">${escapeHtml(t('history-total', { n: _historyState.total }))}</span>
        </div>
        <div class="rh-stat rh-stat-quality">
            <span class="rh-stat-dot"></span>
            <span class="rh-stat-label">${escapeHtml(t('history-avg-conf', { p: avgConfPct }))}</span>
        </div>
    `;
    renderHistorySummary();

    // 列表
    const tbody = document.getElementById('history-tbody');
    if (items.length === 0) {
        tbody!.innerHTML = `<div class="history-row-empty">${escapeHtml(t('history-empty-title'))}</div>`;
    } else {
        tbody!.innerHTML = items
            .map((r: HistoryRow) => {
                const dt = new Date(r.created_at);
                const mm = String(dt.getMonth() + 1).padStart(2, '0');
                const dd = String(dt.getDate()).padStart(2, '0');
                const hh = String(dt.getHours()).padStart(2, '0');
                const mi = String(dt.getMinutes()).padStart(2, '0');
                const dateStr = `${mm}-${dd} ${hh}:${mi}`;

                const origName = escapeHtml(r.filename || '');
                const shortOrig = origName.length > 46 ? origName.substring(0, 46) + '…' : origName;
                // v89 · 主标题:发票号优先(会计最关心的业务标识)· 否则原文件名截断
                const mainName = r.invoice_no ? escapeHtml(r.invoice_no) : shortOrig;
                // 销项口径 · 副标题=文件名 + 页数(卖方=自己 · 不显)
                const subParts = [];
                if (r.invoice_no && r.filename) subParts.push(shortOrig);
                if (r.page_count)
                    subParts.push(escapeHtml(t('history-pages-n', { n: r.page_count })));
                const subtitle = subParts.join(' · ') || '-';

                // 科目标签(有就显 · 我们没有可靠的"单据类型"字段 · 不臆造)
                const categoryBadge = r.category_tag
                    ? `<span class="history-badge category">${escapeHtml(r.category_tag)}</span>`
                    : '';
                // v0.11 · 多发票拆分角标
                const multiBadge =
                    r.source_total && r.source_total > 1
                        ? `<span class="history-badge multi">${escapeHtml(t('invoice-part-of', { i: r.source_index || 1, n: r.source_total }))}</span>`
                        : '';
                const smartBadge = r.smart_assigned_flag
                    ? `<span class="history-badge smart-assigned" title="${escapeHtml(t('history-smart-assigned'))}">${svgIcon('sparkle', 11)}</span>`
                    : '';

                // 来源短标签(草稿口径:上传 / LINE / 邮件)· folder/api 退回邮件样式
                const src = r.source || 'manual';
                const srcMeta: Record<string, [string, string]> = {
                    manual: ['upload', 'history-src-upload'],
                    upload: ['upload', 'history-src-upload'],
                    line: ['line', 'history-src-line'],
                    email: ['email', 'history-src-email'],
                    folder: ['email', 'history-source-folder'],
                    api: ['email', 'history-source-api'],
                };
                const sm = srcMeta[src] || srcMeta.manual;
                const sourceTag = `<span class="hist-src-tag src-${sm[0]}">${escapeHtml(t(sm[1]))}</span>`;

                // 买方(卖方=自己不显)
                const buyerCell = r.buyer_name
                    ? escapeHtml(r.buyer_name)
                    : `<span class="hist-buyer-empty">—</span>`;

                // 金额 + 税额副行
                const amount =
                    r.total_amount !== null && r.total_amount !== undefined
                        ? Number(r.total_amount).toLocaleString(undefined, {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                          })
                        : `<span class="history-cell-amount-empty">—</span>`;
                const st = r.status || 'pending';
                const vatNum = r.vat_amount != null ? parseFloat(String(r.vat_amount)) : NaN;
                let amountSub: string;
                if (!Number.isNaN(vatNum) && vatNum > 0) {
                    amountSub = t('history-amt-vat', {
                        v: vatNum.toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                        }),
                    });
                } else if (st === 'failed') {
                    amountSub = t('history-amt-reprocess');
                } else if (st === 'pending') {
                    amountSub = t('history-amt-pending');
                } else {
                    amountSub = t('history-amt-novat');
                }

                // 状态药丸(后端派生 · 与汇总卡同口径)
                const stLabelKey =
                    st === 'confirmed'
                        ? 'history-st-confirmed'
                        : st === 'failed'
                          ? 'history-st-failed'
                          : 'history-st-pending';
                const statusPill = `<span class="hist-status-pill ${st}">${escapeHtml(t(stLabelKey))}</span>`;

                return `
                <div class="history-row history-row-v2" data-hid="${escapeHtml(r.id)}">
                    <div class="history-cell-check">
                        <input type="checkbox" class="history-row-check" data-hid="${escapeHtml(r.id)}" ${_historySelected.has(r.id) ? 'checked' : ''} aria-label="select">
                    </div>
                    <div class="history-cell-date">${dateStr}</div>
                    <div class="history-cell-file">
                        <div class="history-cell-filename">${mainName} ${categoryBadge} ${sourceTag} ${multiBadge} ${smartBadge}</div>
                        <div class="history-cell-subtitle">${subtitle}</div>
                    </div>
                    <div class="history-cell-buyer">${buyerCell}</div>
                    <div class="history-cell-amount">
                        <strong>${amount}</strong>
                        <span class="hist-amount-sub">${escapeHtml(amountSub)}</span>
                    </div>
                    <div class="history-cell-status">${statusPill}</div>
                    <div class="history-cell-menu">
                        <button class="history-menu-btn" data-hmenu="${escapeHtml(r.id)}" type="button" aria-label="menu">
                            <svg viewBox="0 0 16 16" fill="currentColor"><circle cx="3" cy="8" r="1.5"/><circle cx="8" cy="8" r="1.5"/><circle cx="13" cy="8" r="1.5"/></svg>
                        </button>
                    </div>
                </div>
            `;
            })
            .join('');
    }

    // v0.16 · 渲染后同步选择状态(含批量工具栏、"全选"checkbox 的三态)
    updateHistoryBatchBar();

    // 分页信息
    const from = items.length > 0 ? _historyState.page * _historyState.pageSize + 1 : 0;
    const to = _historyState.page * _historyState.pageSize + items.length;
    document.getElementById('history-pager-info')!.textContent = t('history-pager', {
        from,
        to,
        total: _historyState.total,
    });

    // 分页按钮
    (document.getElementById('history-prev') as HTMLButtonElement).disabled =
        _historyState.page === 0;
    (document.getElementById('history-next') as HTMLButtonElement).disabled =
        (_historyState.page + 1) * _historyState.pageSize >= _historyState.total;
}

// 汇总卡 / 状态下拉 / 来源下拉 / 上传按钮绑定(列表态归口在本 module)·
// 由 history-drawer 的 initHistoryPage 经 window.initHistoryFilters 调一次。
function initHistoryFilters() {
    // 状态筛选:汇总卡 + 状态下拉互相同步(单一真值 _historyState.statusFilter)
    const applyStatusFilter = (val: string) => {
        _historyState.statusFilter = val;
        _historyState.page = 0;
        const sel = document.getElementById('history-status-select') as HTMLSelectElement | null;
        if (sel && sel.value !== val) sel.value = val;
        clearHistorySelection();
        loadHistoryPage();
    };
    document.querySelectorAll('#history-summary .hist-card').forEach((card) => {
        card.addEventListener('click', () =>
            applyStatusFilter((card as HTMLElement).dataset.statusFilter || 'all')
        );
    });
    document
        .getElementById('history-status-select')
        ?.addEventListener('change', (e) =>
            applyStatusFilter((e.target as HTMLSelectElement).value)
        );
    // 来源筛选(上传 / LINE / 邮件)
    document.getElementById('history-source-select')?.addEventListener('change', (e) => {
        _historyState.sourceFilter = (e.target as HTMLSelectElement).value;
        _historyState.page = 0;
        clearHistorySelection();
        loadHistoryPage();
    });
    // 上传新票据 → 回录入工作台
    document.getElementById('history-act-upload')?.addEventListener('click', () => {
        if (typeof window.routeTo === 'function') window.routeTo('dms-intake');
    });
}

// 桥回 home.js + history-drawer.js
window.loadHistoryPage = loadHistoryPage;
window.renderHistoryList = renderHistoryList;
window.updateHistoryBatchBar = updateHistoryBatchBar;
window.clearHistorySelection = clearHistorySelection;
window.initHistoryFilters = initHistoryFilters;

// 自举:直接刷新落在 history 路由(routeTo 早于本 module 跑)→ 本 module 就绪后补加载一次
if (typeof currentRoute !== 'undefined' && currentRoute === 'history') loadHistoryPage();

// 切账套重载已统一收口到 core-boot 全局 pearnly:workspace-changed → reloadCurrentRoute。
