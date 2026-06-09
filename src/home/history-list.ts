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
        // v118.28.0 · 顶栏客户切换器过滤(唯一来源 · 14b.3 后删除了重复 UI)
        const cid =
            typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId() : null;
        if (cid) params.set('client_id', String(cid));
        const resp = await fetch(`/api/history?${params}`, {
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
        _historyState.items = data.items || [];
        _historyState.total = data.total || 0;
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
                const shortOrig = origName.length > 50 ? origName.substring(0, 50) + '…' : origName;
                // v89 · 主标题:发票号优先(会计最关心的业务标识)· 否则原文件名截断
                //       归档名(archive_name)不在列表显示 · 只用于 ZIP 导出文件名
                const mainName = r.invoice_no ? escapeHtml(r.invoice_no) : shortOrig;
                const subtitleParts = [];
                if (r.seller_name) subtitleParts.push(escapeHtml(r.seller_name));
                // 如果主标题是发票号 · 副标题补上原文件名(截短版)· 方便用户仍能按文件名找
                if (r.invoice_no && r.filename) subtitleParts.push(shortOrig);
                const subtitle = subtitleParts.join(' · ') || '-';

                const categoryBadge = r.category_tag
                    ? `<span class="history-badge category">${escapeHtml(r.category_tag)}</span>`
                    : '';

                // v0.11 · 多发票拆分角标(同一个 PDF 拆成 N 张时显示 "2/3")
                const multiBadge =
                    r.source_total && r.source_total > 1
                        ? `<span class="history-badge multi">${escapeHtml(t('invoice-part-of', { i: r.source_index || 1, n: r.source_total }))}</span>`
                        : '';

                const amount =
                    r.total_amount !== null && r.total_amount !== undefined
                        ? Number(r.total_amount).toLocaleString(undefined, {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                          })
                        : `<span class="history-cell-amount-empty">—</span>`;

                // v102 · 统一未识别指示 · 扫描关键字段缺失
                const missingFields = [];
                if (r.total_amount === null || r.total_amount === undefined)
                    missingFields.push(t('field-amount'));
                if (!r.invoice_no) missingFields.push(t('field-invoice-no'));
                if (!r.invoice_date) missingFields.push(t('field-invoice-date'));
                if (!r.seller_name) missingFields.push(t('field-seller-name'));
                // @ts-expect-error TS6133 verbatim 未使用占位 · 0 改逻辑保留
                const reviewBadge =
                    missingFields.length > 0
                        ? `<span class="history-needs-review" data-review="${escapeHtml(r.id)}" title="${escapeHtml(t('history-needs-review-tip') + ' · ' + missingFields.join(' · '))}" role="button" aria-label="${escapeHtml(t('history-needs-review-tip'))}">${svgIcon('alert', 14)}</span>`
                        : '';

                // @ts-expect-error TS6133 verbatim 未使用占位 · 0 改逻辑保留
                const editedBadge = r.edited
                    ? `<span class="history-badge edited">${escapeHtml(t('history-edited', { n: r.edit_count || 1 }))}</span>`
                    : '';

                const smartBadge = r.smart_assigned_flag
                    ? `<span class="history-badge smart-assigned" title="${escapeHtml(t('history-smart-assigned'))}">${svgIcon('sparkle', 11)}</span>`
                    : '';

                const confClass =
                    r.confidence === 'high' ? 'high' : r.confidence === 'medium' ? 'mid' : 'low';
                const confLabel =
                    r.confidence === 'high'
                        ? t('conf-high')
                        : r.confidence === 'medium'
                          ? t('conf-medium')
                          : t('conf-low');
                const confBadge = `<span class="history-badge conf-${confClass}">${escapeHtml(confLabel)}</span>`;

                // v95 · 来源标签 · 邮件抓取 / 文件夹监听 / API 显示 SVG · 默认 manual 不显示
                let sourceBadge = '';
                const src = r.source || 'manual';
                if (src === 'email') {
                    sourceBadge = `<span class="history-badge source source-email" title="${escapeHtml(t('history-source-email'))}">${svgIcon('mail', 11)}<span>${escapeHtml(t('history-source-email'))}</span></span>`;
                } else if (src === 'folder') {
                    sourceBadge = `<span class="history-badge source source-folder" title="${escapeHtml(t('history-source-folder'))}">${svgIcon('folder', 11)}<span>${escapeHtml(t('history-source-folder'))}</span></span>`;
                } else if (src === 'api') {
                    sourceBadge = `<span class="history-badge source source-api" title="${escapeHtml(t('history-source-api'))}">${svgIcon('api', 11)}<span>${escapeHtml(t('history-source-api'))}</span></span>`;
                }

                return `
                <div class="history-row" data-hid="${escapeHtml(r.id)}">
                    <div class="history-cell-check">
                        <input type="checkbox" class="history-row-check" data-hid="${escapeHtml(r.id)}" ${_historySelected.has(r.id) ? 'checked' : ''} aria-label="select">
                    </div>
                    <div class="history-cell-date">${dateStr}</div>
                    <div class="history-cell-file">
                        <div class="history-cell-filename">${mainName} ${categoryBadge} ${multiBadge} ${sourceBadge} ${smartBadge}</div>
                        <div class="history-cell-subtitle">${subtitle}</div>
                    </div>
                    <div class="history-cell-amount">${amount}</div>
                    <div class="history-cell-conf">${confBadge}</div>
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

// 桥回 home.js + history-drawer.js
window.loadHistoryPage = loadHistoryPage;
window.renderHistoryList = renderHistoryList;
window.updateHistoryBatchBar = updateHistoryBatchBar;
window.clearHistorySelection = clearHistorySelection;

// 自举:直接刷新落在 history 路由(routeTo 早于本 module 跑)→ 本 module 就绪后补加载一次
if (typeof currentRoute !== 'undefined' && currentRoute === 'history') loadHistoryPage();

// 切账套重载已统一收口到 core-boot 全局 pearnly:workspace-changed → reloadCurrentRoute。
