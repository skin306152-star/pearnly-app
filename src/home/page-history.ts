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
                <div class="hist-pagehead-actions">
                    <button class="btn btn-primary" id="history-act-upload" type="button">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 11V3M5 6l3-3 3 3M3 13h10"/></svg>
                        <span data-i18n="history-act-upload">上传新票据</span>
                    </button>
                </div>
            </div>

            <!-- 范围条:这页只展示销项发票/收据识别结果 -->
            <div class="hist-scope">
                <div class="hist-scope-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h9l3 3v15H6z"/><path d="M15 3v4h4"/><path d="M9 11h6M9 15h6"/></svg>
                </div>
                <div class="hist-scope-copy">
                    <b data-i18n="history-scope-title">这里只展示发票、收据和票据表格记录</b>
                    <span data-i18n="history-scope-desc">身份证订车记录请在「录入工作台」或「集成 → 推送记录」中查看。</span>
                </div>
                <span class="hist-scope-tag" data-i18n="history-scope-tag">仅票据</span>
            </div>

            <!-- 汇总卡:点击按状态筛选(计数由 history-list 填充)-->
            <div class="hist-summary" id="history-summary">
                <button class="hist-card active" type="button" data-status-filter="all">
                    <span class="hist-card-label" data-i18n="history-card-all">全部记录</span>
                    <span class="hist-card-num" id="hist-count-all">—</span>
                    <span class="hist-card-sub" data-i18n="history-card-all-sub">近 90 天</span>
                </button>
                <button class="hist-card confirmed" type="button" data-status-filter="confirmed">
                    <span class="hist-card-label" data-i18n="history-card-confirmed">已确认</span>
                    <span class="hist-card-num" id="hist-count-confirmed">—</span>
                    <span class="hist-card-sub" data-i18n="history-card-confirmed-sub">可直接使用</span>
                </button>
                <button class="hist-card pending" type="button" data-status-filter="pending">
                    <span class="hist-card-label" data-i18n="history-card-pending">待复核</span>
                    <span class="hist-card-num" id="hist-count-pending">—</span>
                    <span class="hist-card-sub" data-i18n="history-card-pending-sub">存在需要确认的字段</span>
                </button>
                <button class="hist-card failed" type="button" data-status-filter="failed">
                    <span class="hist-card-label" data-i18n="history-card-failed">处理失败</span>
                    <span class="hist-card-num" id="hist-count-failed">—</span>
                    <span class="hist-card-sub" data-i18n="history-card-failed-sub">文件需要重新处理</span>
                </button>
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
                    <select class="history-range" id="history-status-select">
                        <option value="all" data-i18n="history-status-all">全部状态</option>
                        <option value="confirmed" data-i18n="history-st-confirmed">已确认</option>
                        <option value="pending" data-i18n="history-st-pending">待复核</option>
                        <option value="failed" data-i18n="history-st-failed">处理失败</option>
                    </select>
                    <select class="history-range" id="history-source-select">
                        <option value="all" data-i18n="history-source-all">全部来源</option>
                        <option value="upload" data-i18n="history-src-upload">网页上传</option>
                        <option value="line" data-i18n="history-src-line">LINE</option>
                        <option value="email" data-i18n="history-src-email">邮件</option>
                    </select>
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
                    <div class="history-table-head history-table-head-v2">
                        <div class="history-col-check">
                            <input type="checkbox" id="history-check-all" aria-label="select all">
                        </div>
                        <div data-i18n="history-col-date">日期</div>
                        <div data-i18n="history-col-doc">票据 / 文件</div>
                        <div data-i18n="history-col-buyer">买方</div>
                        <div class="history-cell-amount align-right" data-i18n="history-col-amount">金额</div>
                        <div class="history-cell-status align-right" data-i18n="history-col-status">状态</div>
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
