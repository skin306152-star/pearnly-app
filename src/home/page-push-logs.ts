// ============================================================
// 推送日志 · 独立页(2026-07-01 · 从集成页 Tab2 抽出为左侧栏独立导航项)
//
// home.html <section id="page-push-logs"> 空壳 · 本模块运行期注入 erp-logs-section 骨架 innerHTML。
// 日志渲染/筛选/批量/失败卡由 erp-integration.ts + erp-log-card.ts 按元素 id 绑定(#erp-logs-* 不变) →
// 位置从集成页搬到这里,ID 一致,wiring 零改。window.loadPushLogs = loadErpLogs + loadErpTodayStats(route loader)。
// ============================================================
(function () {
    'use strict';
    const sec = document.getElementById('page-push-logs');
    if (!sec || sec.dataset.wbInjected === '1') return;
    sec.innerHTML = `
        <div class="page-head-clean">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>
                </svg>
            </div>
            <div class="page-head-text">
                <div class="page-head-title" data-i18n="nav-push-logs">推送日志</div>
                <div class="page-head-sub" data-i18n="push-logs-sub">识别后推送到 ERP 的结果 · 成功 / 失败 / 重试 · 失败可就地修复重推</div>
            </div>
        </div>

        <div class="card">
            <section class="erp-logs-section" id="erp-logs-section">
                <div class="erp-logs-head">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="8" cy="8" r="6"/><path d="M8 5v3l2 1"/>
                    </svg>
                    <span data-i18n="erp-logs-title">推送日志</span>
                    <div id="erp-today-stats" class="erp-today-stats"></div>
                </div>

                <div class="erp-logs-toolbar">
                    <div class="erp-logs-filters" id="erp-logs-filters">
                        <button class="chip-filter active" data-filter-key="all" data-filter-val=""><span data-i18n="erp-logs-filter-all">全部</span></button>
                        <button class="chip-filter" data-filter-key="status" data-filter-val="success">✓ <span data-i18n="erp-logs-filter-ok">成功</span></button>
                        <button class="chip-filter" data-filter-key="status" data-filter-val="retrying">↻ <span data-i18n="erp-logs-filter-retrying">重试中</span></button>
                        <button class="chip-filter" data-filter-key="status" data-filter-val="failed">✗ <span data-i18n="erp-logs-filter-fail">失败</span></button>
                        <button class="chip-filter" data-filter-key="trigger" data-filter-val="auto"><span data-i18n="erp-logs-filter-auto">自动</span></button>
                        <button class="chip-filter" data-filter-key="trigger" data-filter-val="manual"><span data-i18n="erp-logs-filter-manual">手动</span></button>
                        <span class="erp-logs-filter-sep" aria-hidden="true">|</span>
                        <select id="erp-logs-business-select" class="erp-logs-erp-select" aria-label="business">
                            <option value="" data-i18n="erp-logs-biz-all">全部业务</option>
                            <option value="invoice" data-i18n="erp-logs-biz-invoice">发票 / 单据</option>
                            <option value="id_card" data-i18n="erp-logs-biz-idcard">身份证订车</option>
                        </select>
                        <select id="erp-logs-erp-select" class="erp-logs-erp-select" aria-label="ERP">
                            <option value="" data-i18n="erp-logs-erp-all">全部 ERP</option>
                        </select>
                    </div>
                    <div class="erp-logs-toolbar-right">
                        <div class="erp-logs-search">
                            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="7" cy="7" r="5"/><path d="M11 11l3 3"/></svg>
                            <input type="search" id="erp-logs-search" data-i18n-placeholder="erp-logs-search-ph" placeholder="搜索单据号 / 客户 / 任务">
                        </div>
                        <button class="btn btn-ghost btn-tiny" id="btn-refresh-logs" title="刷新">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M11.5 7a4.5 4.5 0 11-1.3-3.2M12 2v3h-3"/></svg>
                        </button>
                    </div>
                </div>

                <div id="erp-logs-batch-bar" class="erp-logs-batch-bar" style="display:none;">
                    <span class="erp-logs-batch-count" id="erp-logs-batch-count" data-i18n="erp-batch-selected" data-i18n-vars='{"n":0}'>已选 0 条</span>
                    <button class="btn btn-primary btn-tiny" id="btn-erp-batch-retry">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M11.5 7a4.5 4.5 0 11-1.3-3.2M12 2v3h-3"/></svg>
                        <span data-i18n="erp-batch-retry-btn">批量重推</span>
                    </button>
                    <button class="btn btn-ghost btn-tiny btn-danger-ghost" id="btn-erp-batch-delete">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h8M5 4V2.5h4V4M6 7v4M8 7v4M4 4l.5 8h5l.5-8"/></svg>
                        <span data-i18n="erp-batch-delete-btn">批量删除</span>
                    </button>
                    <button class="btn btn-ghost btn-tiny" id="btn-erp-batch-clear">
                        <span data-i18n="erp-batch-clear">取消选择</span>
                    </button>
                </div>

                <div id="erp-logs-list" class="erp-logs-list">
                    <div class="erp-logs-empty" data-i18n="erp-logs-loading">加载中…</div>
                </div>
            </section>
        </div>
`;
    sec.dataset.wbInjected = '1';
    try {
        const lang = window._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
        const I = window.I18N;
        if (I && I[lang]) {
            sec.querySelectorAll('[data-i18n]').forEach((el) => {
                const k = el.getAttribute('data-i18n') as string;
                if (I[lang][k]) el.textContent = I[lang][k];
            });
            sec.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
                const k = el.getAttribute('data-i18n-placeholder') as string;
                if (I[lang][k]) (el as HTMLInputElement).placeholder = I[lang][k];
            });
        }
    } catch (e) {
        /* silent · 初译失败不致命 · 切语言会补 */
    }

    // route loader:进「推送日志」路由即拉日志 + 今日统计(erp-integration.ts 提供全局函数)。
    (window as unknown as { loadPushLogs: () => void }).loadPushLogs = function () {
        const w = window as unknown as {
            loadErpLogs?: () => void;
            loadErpTodayStats?: () => void;
        };
        if (typeof w.loadErpLogs === 'function') w.loadErpLogs();
        if (typeof w.loadErpTodayStats === 'function') w.loadErpTodayStats();
    };
})();
