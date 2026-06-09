// src/home/page-history.ts
// PO-UI 迁移(2026-06-09)· kit 作用域 .ui · 列表模板(标杆流式)。
//
// 全部 id 逐字保留(history-list.ts 按 id 取元素):
//   history-free-block · history-main · history-stats · history-search
//   history-search-clear · history-range · history-search-matches
//   history-batch-bar · history-batch-count · history-batch-export
//   history-batch-delete · history-batch-cancel · history-check-all
//   history-tbody · history-pager-info · history-prev · history-next · history-empty
(function () {
    'use strict';
    const sec = document.getElementById('page-history');
    if (!sec || sec.dataset.wbInjected === '1') return;
    sec.classList.add('ui');
    sec.innerHTML = `
        <div class="wrap">
            <div class="pagehead">
                <div>
                    <div class="h1" data-i18n="history-title">识别历史</div>
                    <div class="sub" data-i18n="history-sub">保留近 90 天 · 点击行查看详情</div>
                </div>
            </div>

            <div class="panel" id="history-free-block" style="display:none;">
                <div class="coming-soon">
                    <svg class="cs-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="24" cy="24" r="18"/><path d="M24 14v10l7 5"/>
                    </svg>
                    <div class="cs-title" data-i18n="cs-history-title">识别历史管理</div>
                    <div class="cs-desc" data-i18n="cs-no-access">该功能暂未开放 · 如有需要请联系我们</div>
                </div>
            </div>

            <div class="panel" id="history-main" style="display:none;">
                <div class="results-head">
                    <div class="results-head-left">
                        <div class="section-title" data-i18n="history-section-title">识别记录</div>
                        <div class="section-sub" data-i18n="history-section-sub">点击行查看详情</div>
                    </div>
                    <div class="results-head-stats" id="history-stats"></div>
                </div>

                <div class="history-filters">
                    <div class="search-wrap">
                        <svg class="search-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="7" cy="7" r="5"/><path d="M11 11l3 3"/>
                        </svg>
                        <input type="text" class="search-input" id="history-search" data-i18n-placeholder="history-search-placeholder">
                        <button type="button" class="search-clear" id="history-search-clear" style="display:none;" aria-label="clear">✕</button>
                    </div>
                    <select class="history-range" id="history-range">
                        <option value="7" data-i18n="history-range-7">最近 7 天</option>
                        <option value="30" data-i18n="history-range-30">最近 30 天</option>
                        <option value="90" selected data-i18n="history-range-90">最近 90 天</option>
                    </select>
                    <span class="search-matches" id="history-search-matches"></span>
                </div>

                <div class="history-table-wrap">
                    <div class="history-batch-bar" id="history-batch-bar" style="display:none;">
                        <span class="history-batch-count" id="history-batch-count">已选 0 条</span>
                        <div class="history-batch-actions">
                            <button class="btn-icon hist-batch-icon-btn" id="history-batch-export" title="批量导出">
                                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M10 3v10M6 9l4 4 4-4M4 15v2h12v-2"/></svg>
                            </button>
                            <button class="btn-icon hist-batch-icon-btn hist-batch-icon-danger" id="history-batch-delete" title="批量删除">
                                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h14M8 6V4a1 1 0 011-1h2a1 1 0 011 1v2m1 0v10a2 2 0 01-2 2H8a2 2 0 01-2-2V6m3 4v6m4-6v6"/></svg>
                            </button>
                            <button class="btn-icon hist-batch-icon-btn" id="history-batch-cancel" title="取消">
                                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 5l10 10M15 5L5 15"/></svg>
                            </button>
                        </div>
                    </div>
                    <div class="history-table-head">
                        <div class="history-col-check">
                            <input type="checkbox" id="history-check-all" aria-label="select all">
                        </div>
                        <div data-i18n="history-col-date">日期</div>
                        <div data-i18n="history-col-file">文件 · 发票号 · 供应商</div>
                        <div class="history-cell-amount align-right" data-i18n="history-col-amount">金额</div>
                        <div class="history-cell-conf align-center" data-i18n="history-col-conf">置信</div>
                        <div class="history-cell-menu"></div>
                    </div>
                    <div id="history-tbody"></div>
                </div>

                <div class="history-foot">
                    <div id="history-pager-info" class="history-pager-info"></div>
                    <div class="history-pager-btns">
                        <button id="history-prev" class="btn btn-ghost">‹</button>
                        <button id="history-next" class="btn btn-ghost">›</button>
                    </div>
                </div>
            </div>

            <div class="empty-state" id="history-empty" style="display:none;">
                <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="empty-icon">
                    <rect x="8" y="10" width="32" height="30" rx="2"/>
                    <path d="M16 20h16M16 28h12M16 36h8"/>
                </svg>
                <div class="empty-title" data-i18n="history-empty-title">还没有记录</div>
                <div class="empty-desc" data-i18n="history-empty-desc">识别的发票会自动出现在这里</div>
            </div>
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
    } catch (_) {
        // 初译失败不致命，切语言会补
    }
})();
