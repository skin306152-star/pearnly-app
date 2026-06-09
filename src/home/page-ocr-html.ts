// ============================================================
// page-ocr-html · 上传识别主页(#page-ocr · 登录后默认 active 页)
//
// PO-UI 迁移(2026-06-09)· 套列表变体模板 + kit 作用域 .ui。
// 高扇出:upload-files / ocr-recognize / ocr-results / export 等在【模块 eval 顶层】
// 绑 drop-zone / btn-start / file-input / search-input / results-tbody 等;
// 本模块须早于所有 OCR 消费模块 eval(main.js import 顺序保证)。
//
// 全部 id 逐字保留(ocr-recognize / upload-files / ocr-results 按 id 取元素):
//   drop-zone · file-input · file-list · btn-start · btn-stop · btn-clear
//   btn-export · btn-export-arrow · btn-custom-template · camera-input · gallery-input
//   btn-scan-doc · btn-upload-pic · upload-alt-row · upload-hint · info-bar
//   alert-info · alert-info-text · alert-warn · alert-warn-text · alert-error · alert-error-text
//   results-card · results-head-stats · results-tbody · results-table · search-input
//   search-clear · search-matches
// ============================================================
(function () {
    'use strict';
    const sec = document.getElementById('page-ocr');
    if (!sec || sec.dataset.wbInjected === '1') return;
    sec.classList.add('ui');
    sec.innerHTML = `
        <div class="wrap">
            <div class="pagehead">
                <div>
                    <div class="h1" data-i18n="ocr-title">上传识别</div>
                    <div class="sub" data-i18n="ocr-sub">把票据一拍 · 数据自动进 Excel 和 ERP</div>
                </div>
            </div>

            <div class="info-bar" id="info-bar"></div>

            <div class="panel box" style="margin-bottom:var(--s4)">
                <div class="ocr-card-head">
                    <div class="ocr-card-title" data-i18n="upload-title">上传 PDF 文件</div>
                    <div class="ocr-card-sub" id="upload-hint"></div>
                </div>

                <div class="drop-zone" id="drop-zone">
                    <svg class="icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M14 32V16a2 2 0 012-2h12l8 8v10a2 2 0 01-2 2H16a2 2 0 01-2-2z"/>
                        <path d="M28 14v8h8M24 28v-6M20 24l4-4 4 4"/>
                    </svg>
                    <div class="text" data-i18n="drop-text">点击或拖拽文件到此处</div>
                    <div class="hint" data-i18n="drop-hint">支持 PDF / 图片 / Excel / CSV / Word · 系统自动选择 OCR 或直接解析 · 数据不存服务器</div>
                </div>
                <input type="file" id="file-input" accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.bmp,.gif,.xlsx,.xls,.xlsm,.csv,.tsv,.docx,.doc,.txt" multiple>

                <div class="upload-alt-row" id="upload-alt-row" style="display:none;">
                    <button type="button" class="btn-scan-doc" id="btn-scan-doc">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M3 7h4l2-2h6l2 2h4a1 1 0 011 1v11a1 1 0 01-1 1H3a1 1 0 01-1-1V8a1 1 0 011-1z"/>
                            <circle cx="12" cy="13" r="4"/>
                        </svg>
                        <span data-i18n="btn-scan-doc">拍摄票据</span>
                    </button>
                    <button type="button" class="btn-scan-doc btn-upload-pic" id="btn-upload-pic">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="4" width="18" height="16" rx="2"/>
                            <circle cx="9" cy="10" r="1.6" fill="currentColor"/>
                            <path d="M3 17l5-5 4 4 3-3 6 6"/>
                        </svg>
                        <span data-i18n="btn-upload-pic">上传图片</span>
                    </button>
                </div>
                <input type="file" id="camera-input" accept="image/*" capture="environment" style="display:none;">
                <input type="file" id="gallery-input" accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.bmp,.gif,.xlsx,.xls,.xlsm,.csv,.tsv,.docx,.doc,.txt" multiple style="display:none;">

                <ul class="file-list" id="file-list"></ul>

                <div class="btn-row">
                    <button class="btn pri" id="btn-start" disabled>
                        <svg viewBox="0 0 20 20" fill="currentColor"><path d="M6 4l10 6-10 6z"/></svg>
                        <span data-i18n="btn-start">开始识别</span>
                    </button>
                    <button class="btn dng" id="btn-stop" style="display:none;">
                        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="5" width="10" height="10" rx="1.5"/></svg>
                        <span data-i18n="btn-stop">停止识别</span>
                    </button>
                    <button class="btn sec" id="btn-clear" disabled>
                        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 7h10M8 3h4M7 7l1 10h4l1-10"/></svg>
                        <span data-i18n="btn-clear">清空</span>
                    </button>
                    <div class="export-split-wrap" id="export-split-wrap">
                        <button class="btn sec export-main" id="btn-export" disabled>
                            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10 3v10M6 9l4 4 4-4M4 15v2h12v-2"/></svg>
                            <span data-i18n="btn-export">导出 Excel</span>
                        </button>
                        <button class="btn sec export-arrow" id="btn-export-arrow" disabled aria-label="选模板">
                            <svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5l3 3 3-3"/></svg>
                        </button>
                    </div>
                    <button class="btn sec btn-locked" id="btn-custom-template" style="display:none;">
                        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="14" height="12" rx="1"/><path d="M3 8h14M7 4v12"/></svg>
                        <span data-i18n="btn-custom-tpl">自定义模板</span>
                    </button>
                </div>

                <div class="alert alert-info" id="alert-info">
                    <svg viewBox="0 0 20 20" fill="currentColor"><path d="M10 2a8 8 0 100 16 8 8 0 000-16zm0 14a1 1 0 110-2 1 1 0 010 2zm1-4a1 1 0 01-2 0V6a1 1 0 012 0v6z"/></svg>
                    <span id="alert-info-text"></span>
                </div>
                <div class="alert alert-warn" id="alert-warn">
                    <svg viewBox="0 0 20 20" fill="currentColor"><path d="M10 2L1 18h18L10 2zm0 14a1 1 0 110-2 1 1 0 010 2zm1-4a1 1 0 01-2 0V8a1 1 0 012 0v4z"/></svg>
                    <span id="alert-warn-text"></span>
                </div>
                <div class="alert alert-error" id="alert-error">
                    <svg viewBox="0 0 20 20" fill="currentColor"><path d="M10 2a8 8 0 100 16 8 8 0 000-16zm4.24 11.17L13 14.41l-3-3-3 3-1.24-1.24 3-3-3-3L7 4.93l3 3 3-3 1.24 1.24-3 3 3 3z"/></svg>
                    <span id="alert-error-text"></span>
                </div>
            </div>

            <div class="panel results-card" id="results-card" style="padding:var(--s5) var(--s6);margin-bottom:var(--s4)">
                <div class="results-head">
                    <div class="results-head-left">
                        <div class="ocr-card-title" data-i18n="results-title">识别结果</div>
                        <div class="ocr-card-sub" data-i18n="results-sub">点击行查看详情</div>
                    </div>
                    <div class="results-head-stats" id="results-head-stats"></div>
                </div>

                <div class="results-saved-banner">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                        <circle cx="10" cy="10" r="8"/>
                        <polyline points="6.5,10.5 9,13 13.5,7.5"/>
                    </svg>
                    <span data-i18n="results-saved-banner">识别结果会自动保存到「单据记录」 · 关掉本页也不会丢</span>
                </div>

                <div class="search-row">
                    <div class="search-wrap">
                        <svg class="search-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="7" cy="7" r="5"/><path d="M11 11l3 3"/>
                        </svg>
                        <input type="text" class="search-input" id="search-input" data-i18n-placeholder="search-placeholder">
                        <button type="button" class="search-clear" id="search-clear" style="display:none;" aria-label="clear">✕</button>
                    </div>
                    <span class="search-matches" id="search-matches"></span>
                </div>

                <div class="table-wrap">
                    <table class="results-table" id="results-table">
                        <thead>
                            <tr>
                                <th data-sort="no" class="no-sort"><span data-i18n="col-no">序号</span></th>
                                <th data-sort="filename"><span data-i18n="col-filename">文件名</span> <span class="sort-indicator"></span></th>
                                <th data-sort="invoice_no"><span data-i18n="col-invoice">发票号</span> <span class="sort-indicator"></span></th>
                                <th data-sort="invoice_date"><span data-i18n="col-date">日期</span> <span class="sort-indicator"></span></th>
                                <th data-sort="total" class="amount-col"><span data-i18n="col-total">金额</span> <span class="sort-indicator"></span></th>
                                <th data-sort="confidence" id="col-conf-th"><span data-i18n="col-conf">置信度</span> <span class="sort-indicator"></span></th>
                            </tr>
                        </thead>
                        <tbody id="results-tbody"></tbody>
                    </table>
                </div>
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
