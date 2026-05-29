// ============================================================
// REFACTOR-WB-C3 (2026-05-29) · page-reconcile 静态骨架从 home.html 抽出 · 运行期模板注入(R6 机制)
//
// home.html <section id="page-reconcile"> 现为空壳 · 本模块注入骨架 innerHTML。
// 对账中心被 6 个模块渲染/绑定(recon-center / recon-subtab-settings / gl-vat-recon / bank-recon-v2 /
// recon-collapse / excel-formula-recon · 多含 DOMContentLoaded 绑定)→ 本 import 置于 main.js 最前(所有 home
// 模块之前)· eval 即注入 · 保证早于任何模块 eval-time getElementById 与 DOMContentLoaded · 元素恒在场。
// home.js parse 期 0 处绑定对账元素(已核 · 全走 window.loadReconcilePage 路由期 + 模块 DOMContentLoaded)。
// i18n:注入后子树补译(镜像 applyLang)· 切语言由 applyLang 全文扫描覆盖。verbatim 搬迁骨架 · 0 改结构。
// ============================================================
(function () {
    'use strict';
    const sec = document.getElementById('page-reconcile');
    if (!sec || sec.dataset.wbInjected === '1') return;
    sec.innerHTML = `
        <!-- 顶部 page head -->
        <div class="page-head-clean">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 10l9-6 9 6v11H3V10z"/>
                    <path d="M9 21V12h6v9"/>
                </svg>
            </div>
            <div class="page-head-text">
                <div class="page-head-title" id="recon-main-title" data-i18n="rc-page-title">对账中心</div>
                <div class="page-head-sub" id="recon-main-sub" data-i18n="rc-page-sub">核对账目 · 找出差异 · 关账更快</div>
            </div>
        </div>

        <!-- 顶部横向 tab 条 -->
        <div class="recon-tab-bar">
            <button class="recon-tab-btn active" data-recon-tab="bank" data-i18n="recon-tab-bank">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 6h12M3 6V4a5 5 0 0110 0v2M2 6v7a1 1 0 001 1h10a1 1 0 001-1V6"/><path d="M6 10h4"/></svg>
                银行对账
            </button>
            <button class="recon-tab-btn" data-recon-tab="sale-vat" data-i18n="recon-tab-sale-vat">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M9 1.5H4a1 1 0 00-1 1v11a1 1 0 001 1h8a1 1 0 001-1V5.5L9 1.5z"/><path d="M9 1.5v4h4M5.5 9l1.5 1.5 3-3"/></svg>
                销项税报告核查
            </button>
            <button class="recon-tab-btn" data-recon-tab="gl-vat" data-i18n="recon-tab-gl-vat">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><rect x="1.5" y="1.5" width="13" height="13" rx="1.5"/><path d="M1.5 5.5h13M1.5 9.5h13M5.5 5.5v9M10.5 5.5v9"/></svg>
                收入对账
            </button>
        </div>
        <!-- pane 区(全宽) -->

        <!-- ── 银行对账面板 v2（vex-drop 同款视觉 · v118.33.6.1 UI 重构对齐 GL-VAT） ── -->
        <div id="recon-pane-bank" class="recon-pane active">

            <!-- KPI 3 卡 -->
            <div class="vex-kpi-strip" id="brv2-kpi-strip">
                <div class="vex-kpi-card">
                    <div class="vex-kpi-icon-wrap vex-kpi-icon-ok">✓</div>
                    <div>
                        <div class="vex-kpi-val" id="brv2-kpi-matched">—</div>
                        <div class="vex-kpi-lbl" data-i18n="brv2-stat-matched">完全匹配</div>
                    </div>
                </div>
                <div class="vex-kpi-card">
                    <div class="vex-kpi-icon-wrap" id="brv2-kpi-diff-icon" style="background:#f3f4f6;color:#6b7280">△</div>
                    <div>
                        <div class="vex-kpi-val" id="brv2-kpi-diff">—</div>
                        <div class="vex-kpi-lbl" data-i18n="brv2-stat-diff">差额</div>
                    </div>
                </div>
                <div class="vex-kpi-card">
                    <div class="vex-kpi-icon-wrap vex-kpi-icon-err">!</div>
                    <div>
                        <div class="vex-kpi-val" id="brv2-kpi-unmatched">—</div>
                        <div class="vex-kpi-lbl" data-i18n="brv2-stat-unmatched">未匹配</div>
                    </div>
                </div>
            </div>

            <!-- 主操作区（沿用 vex-main-action 视觉） -->
            <div class="vex-main-action">
                <div class="vex-main-action-tag" data-i18n="vex-main-action-tag">主操作</div>

                <!-- 左右双拖拽区 -->
                <div class="vex-drops">
                    <div class="vex-drop vex-drop-invoice" id="brv2-stmt-zone" role="button" tabindex="0">
                        <div class="vex-drop-icon-wrap">
                            <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M8 4h12l6 6v16a2 2 0 01-2 2H8a2 2 0 01-2-2V6a2 2 0 012-2z"/>
                                <path d="M20 4v6h6M10 14h12M10 20h8"/>
                            </svg>
                        </div>
                        <div class="vex-drop-title" data-i18n="brv2-stmt-title">① 银行账单 PDF</div>
                        <div class="vex-drop-sub" data-i18n="brv2-stmt-hint">PDF / 图片 / Excel / CSV / Word · 多文件 · 自动识别</div>
                        <div class="vex-drop-filename" id="brv2-stmt-name"></div>
                        <input type="file" id="brv2-stmt-input" accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.xlsx,.xls,.xlsm,.csv,.tsv,.docx,.doc" multiple style="display:none">
                    </div>

                    <div class="vex-drop-divider" aria-hidden="true"><span>+</span></div>

                    <div class="vex-drop vex-drop-report" id="brv2-gl-zone" role="button" tabindex="0">
                        <div class="vex-drop-icon-wrap">
                            <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="4" y="6" width="24" height="20" rx="2"/>
                                <line x1="4" y1="13" x2="28" y2="13"/>
                                <line x1="12" y1="6" x2="12" y2="26"/>
                                <line x1="20" y1="6" x2="20" y2="26"/>
                            </svg>
                        </div>
                        <div class="vex-drop-title" data-i18n="brv2-gl-title">② 总账 GL</div>
                        <div class="vex-drop-sub" data-i18n="brv2-gl-hint">PDF / 图片 / Excel / CSV / Word · 多文件 · 自动识别</div>
                        <div class="vex-drop-filename" id="brv2-gl-name"></div>
                        <input type="file" id="brv2-gl-input" accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.xlsx,.xls,.xlsm,.csv,.tsv,.docx,.doc" multiple style="display:none">
                    </div>
                </div>

                <!-- BUG-B v118.35.0.36 (2026-05-22) · OCR 抽 GL/STATEMENT 3 个 anchor 余额不准时
                     用户手动录入兜底 · 防 OCR 错位连锁整张报告废 · Zihao 拍板破例整顿期允许 -->
                <div class="brv2-anchor-row" id="brv2-anchor-row">
                    <div class="brv2-anchor-head">
                        <span class="brv2-anchor-icon" aria-hidden="true">
                            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="14" height="14">
                                <path d="M8 1.5L14.5 4v4c0 4-3 6.5-6.5 6.5S1.5 12 1.5 8V4L8 1.5z"/>
                                <path d="M6 8l1.5 1.5L10.5 6.5"/>
                            </svg>
                        </span>
                        <span class="brv2-anchor-title" data-i18n="brv2-anchor-title">OCR 抽不准?手动录入 3 个余额(可选 · 留空走 OCR)</span>
                    </div>
                    <div class="brv2-anchor-prefill-banner" id="brv2-anchor-prefill-banner" data-i18n="brv2-anchor-prefill-banner">⚠ 下面带橙色背景的数字是上次 OCR 识别的(浏览器本地缓存)· 不对请点击修改</div>
                    <div class="brv2-anchor-grid">
                        <div class="brv2-anchor-cell">
                            <label for="brv2-anchor-gl-closing" data-i18n="brv2-anchor-gl-closing">GL 期末余额</label>
                            <input type="number" id="brv2-anchor-gl-closing" step="any" inputmode="decimal" placeholder="0.00" autocomplete="off">
                        </div>
                        <div class="brv2-anchor-cell">
                            <label for="brv2-anchor-stmt-closing" data-i18n="brv2-anchor-stmt-closing">Statement 期末余额</label>
                            <input type="number" id="brv2-anchor-stmt-closing" step="any" inputmode="decimal" placeholder="0.00" autocomplete="off">
                        </div>
                        <div class="brv2-anchor-cell">
                            <label for="brv2-anchor-stmt-opening" data-i18n="brv2-anchor-stmt-opening">期初 Statement 余额</label>
                            <input type="number" id="brv2-anchor-stmt-opening" step="any" inputmode="decimal" placeholder="0.00" autocomplete="off">
                        </div>
                        <div class="brv2-anchor-cell">
                            <label for="brv2-anchor-gl-opening" data-i18n="brv2-anchor-gl-opening">GL 期初余额</label>
                            <input type="number" id="brv2-anchor-gl-opening" step="any" inputmode="decimal" placeholder="0.00" autocomplete="off">
                        </div>
                    </div>
                    <div class="brv2-anchor-eq" id="brv2-anchor-eq" style="display:none">
                        <span class="brv2-anchor-eq-lbl" data-i18n="brv2-anchor-eq-lbl">期初差额(Statement 期初 − GL 期初):</span>
                        <span class="brv2-anchor-eq-val" id="brv2-anchor-eq-val">—</span>
                    </div>
                </div>

                <!-- 操作栏 -->
                <div class="vex-action-bar">
                    <button class="btn btn-ghost" id="brv2-reset-btn" type="button" data-i18n="vex-btn-reset">清空</button>
                    <div class="vex-action-info muted" id="brv2-status">
                        <span data-i18n="brv2-hint-need-both">请上传银行账单和 GL 文件</span>
                    </div>
                    <button class="vex-toggle-preview-btn" id="brv2-toggle-preview" type="button" style="display:none">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
                        <span id="brv2-toggle-preview-label" data-i18n="vex-toggle-preview-open">查看清单</span>
                    </button>
                    <select class="brv2-acct-select" id="brv2-acct-select" style="display:none">
                        <option value="" data-i18n="brv2-acct-all">全部账户</option>
                    </select>
                    <button class="btn btn-primary" id="brv2-run-btn" type="button" disabled>
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M3 8l4 4 6-8"/>
                        </svg>
                        <span data-i18n="brv2-run-btn">开始对账</span>
                    </button>
                </div>

                <!-- 查看清单面板（同款 vex-preview-panel 视觉） -->
                <div class="vex-preview-panel" id="brv2-preview-panel" style="display:none">
                    <div class="vex-pp-grid">
                        <div id="brv2-pp-stmt-col"></div>
                        <div id="brv2-pp-gl-col"></div>
                    </div>
                </div>

                <!-- 进度区 -->
                <div class="vex-progress" id="brv2-progress" style="display:none">
                    <div class="spinner"></div>
                    <div>
                        <div class="vex-progress-title" data-i18n="brv2-processing">对账中…</div>
                        <div class="vex-progress-sub" id="brv2-progress-sub"></div>
                    </div>
                </div>

                <!-- 错误提示 -->
                <div class="brv2-error" id="brv2-error" style="display:none"></div>

                <!-- 文件解析诊断表 (失败/部分解析时显示) -->
                <div id="brv2-parse-info-wrap" style="display:none;margin-top:12px">
                    <div id="brv2-parse-info-body"></div>
                </div>

                <!-- 结果 · 对账公式折叠区 -->
                <div class="recon-collapse" id="brv2-summary-collapse" data-collapsed="false" style="display:none;margin-top:14px">
                    <div class="recon-collapse-head" data-toggle="brv2-summary-collapse" tabindex="0" role="button">
                        <svg class="recon-collapse-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="5 7 8 10 11 7"/>
                        </svg>
                        <span class="recon-collapse-title" data-i18n="brv2-formula-title">对账公式</span>
                        <span class="recon-collapse-sub" id="brv2-formula-sub"></span>
                        <div class="glv-section-spacer"></div>
                        <button class="btn btn-ghost btn-small" id="brv2-export-btn" type="button" style="display:none">
                            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" width="13" height="13">
                                <path d="M3 11v2h10v-2M8 2v8M5 7l3 4 3-4"/>
                            </svg>
                            <span data-i18n="brv2-export-excel">导出 Excel</span>
                        </button>
                        <button class="btn btn-ghost btn-small" id="brv2-new-btn" type="button" style="display:none">
                            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" width="13" height="13">
                                <path d="M8 3v10M3 8h10"/>
                            </svg>
                            <span data-i18n="brv2-new-btn">新建</span>
                        </button>
                    </div>
                    <div class="recon-collapse-body">
                        <div class="brv2-formula-grid" id="brv2-formula-grid">
                            <div class="brv2-fcell">
                                <div class="brv2-fcell-lbl" data-i18n="brv2-gl-close">GL 期末余额</div>
                                <div class="brv2-fcell-val" id="brf-gl-close">—</div>
                            </div>
                            <div class="brv2-fsep">+</div>
                            <div class="brv2-fcell">
                                <div class="brv2-fcell-lbl" data-i18n="brv2-open-diff">期初差额</div>
                                <div class="brv2-fcell-val" id="brf-open-diff">—</div>
                            </div>
                            <div class="brv2-fsep">−</div>
                            <div class="brv2-fcell">
                                <div class="brv2-fcell-lbl" data-i18n="brv2-gl-debit-only-short">GL 仅借方</div>
                                <div class="brv2-fcell-val" id="brf-gl-debit-only">—</div>
                            </div>
                            <div class="brv2-fsep">+</div>
                            <div class="brv2-fcell">
                                <div class="brv2-fcell-lbl" data-i18n="brv2-gl-credit-only-short">GL 仅贷方</div>
                                <div class="brv2-fcell-val" id="brf-gl-credit-only">—</div>
                            </div>
                            <div class="brv2-fsep">−</div>
                            <div class="brv2-fcell">
                                <div class="brv2-fcell-lbl" data-i18n="brv2-stmt-wd-only-short">账单仅提款</div>
                                <div class="brv2-fcell-val" id="brf-stmt-wd-only">—</div>
                            </div>
                            <div class="brv2-fsep">+</div>
                            <div class="brv2-fcell">
                                <div class="brv2-fcell-lbl" data-i18n="brv2-stmt-dep-only-short">账单仅存款</div>
                                <div class="brv2-fcell-val" id="brf-stmt-dep-only">—</div>
                            </div>
                            <div class="brv2-fsep">=</div>
                            <div class="brv2-fcell brv2-fcell-result">
                                <div class="brv2-fcell-lbl" data-i18n="brv2-calc-close">计算期末</div>
                                <div class="brv2-fcell-val brv2-fcell-bold" id="brf-calc-close">—</div>
                            </div>
                            <div class="brv2-fsep">vs</div>
                            <div class="brv2-fcell">
                                <div class="brv2-fcell-lbl" data-i18n="brv2-stmt-close">账单期末</div>
                                <div class="brv2-fcell-val" id="brf-stmt-close">—</div>
                            </div>
                            <div class="brv2-fsep">→</div>
                            <div class="brv2-fcell brv2-fcell-diff" id="brv2-fcell-diff">
                                <div class="brv2-fcell-lbl" data-i18n="brv2-diff-label">差额 (应为 0)</div>
                                <div class="brv2-fcell-val brv2-fcell-bold" id="brf-diff">—</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 结果 · 明细折叠区 -->
                <div class="recon-collapse" id="brv2-detail-collapse" data-collapsed="false" style="display:none;margin-top:10px">
                    <div class="recon-collapse-head" data-toggle="brv2-detail-collapse" tabindex="0" role="button">
                        <svg class="recon-collapse-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="5 7 8 10 11 7"/>
                        </svg>
                        <span class="recon-collapse-title" data-i18n="brv2-detail-title">明細</span>
                        <span class="recon-collapse-sub" id="brv2-detail-sub"></span>
                        <div class="glv-section-spacer"></div>
                        <!-- 过滤 tabs（放在折叠头部右侧） -->
                        <div class="brv2-filter-tabs" id="brv2-filter-tabs">
                            <button class="brv2-filter-btn active" data-filter="all" data-i18n="brv2-filter-all">全部</button>
                            <button class="brv2-filter-btn" data-filter="matched" data-i18n="brv2-filter-matched">已匹配</button>
                            <button class="brv2-filter-btn" data-filter="gl_only" data-i18n="brv2-filter-gl-only">GL 未配</button>
                            <button class="brv2-filter-btn" data-filter="stmt_only" data-i18n="brv2-filter-stmt-only">账单未配</button>
                        </div>
                    </div>
                    <div class="recon-collapse-body">
                        <div class="brv2-table-wrap">
                            <table class="brv2-table" id="brv2-detail-table">
                                <thead>
                                    <tr>
                                        <th data-i18n="brv2-th-status">状态</th>
                                        <th data-i18n="brv2-th-stmt-date">账单日期</th>
                                        <th data-i18n="brv2-th-stmt-desc">账单摘要</th>
                                        <th class="num" data-i18n="brv2-th-wd">提款</th>
                                        <th class="num" data-i18n="brv2-th-dep">存款</th>
                                        <th data-i18n="brv2-th-gl-date">GL 日期</th>
                                        <th data-i18n="brv2-th-gl-doc">GL 凭证</th>
                                        <th class="num" data-i18n="brv2-th-gl-debit">借方</th>
                                        <th class="num" data-i18n="brv2-th-gl-credit">贷方</th>
                                        <th data-i18n="brv2-th-layer">层级</th>
                                    </tr>
                                </thead>
                                <tbody id="brv2-tbody"></tbody>
                            </table>
                        </div>
                    </div>
                </div>

            </div><!-- /vex-main-action -->

            <!-- 历史记录（同款 glv-history 视觉） -->
            <div class="glv-history" id="brv2-history">
                <div class="glv-result-head">
                    <div class="glv-result-title" data-i18n="brv2-history-title">近期对账记录</div>
                    <input type="text" class="hist-search-input" id="brv2-hist-search"
                           data-i18n-placeholder="brv2-hist-search-ph" placeholder="搜索..." autocomplete="off">
                </div>
                <div class="glv-history-empty" id="brv2-history-empty" data-i18n="brv2-history-empty">
                    暂无对账记录
                </div>
                <div class="glv-history-table-wrap" id="brv2-history-table-wrap" style="display:none">
                    <table class="glv-history-table" id="brv2-history-table">
                        <thead>
                            <tr>
                                <th data-i18n="brv2-hist-time">时间</th>
                                <th data-i18n="brv2-hist-files">文件</th>
                                <th class="glv-num" data-i18n="brv2-hist-rows">账单/GL行数</th>
                                <th class="glv-num" data-i18n="brv2-hist-matched">已匹配</th>
                                <th class="glv-num" data-i18n="brv2-hist-gl-only">GL仅有</th>
                                <th class="glv-num" data-i18n="brv2-hist-stmt-only">账单仅有</th>
                                <th class="glv-num" data-i18n="brv2-hist-diff">差额</th>
                                <th data-i18n="brv2-hist-actions">操作</th>
                            </tr>
                        </thead>
                        <tbody id="brv2-history-tbody"></tbody>
                    </table>
                    <div class="hist-pager" id="brv2-history-pager" style="display:none">
                        <button class="hist-pager-btn" id="brv2-history-prev" type="button" disabled>&#8592;</button>
                        <span class="hist-pager-info" id="brv2-history-pager-info"></span>
                        <button class="hist-pager-btn" id="brv2-history-next" type="button">&#8594;</button>
                    </div>
                </div>
            </div>

        </div><!-- /recon-pane-bank -->

        <!-- ── 销项税对账面板(v118.32.0 · 屏 A) ── -->
        <div id="recon-pane-sale-vat" class="recon-pane" style="display:none">


            <!-- v4.10.7 · KPI 3 卡统一视觉 -->
            <div class="vex-kpi-strip" id="vex-kpi-strip">
                <div class="vex-kpi-card">
                    <div class="vex-kpi-icon-wrap vex-kpi-icon-warn">⏱</div>
                    <div>
                        <div class="vex-kpi-val" id="vex-kpi-running-val">—</div>
                        <div class="vex-kpi-lbl" data-i18n="vex-kpi-running">进行中</div>
                    </div>
                </div>
                <div class="vex-kpi-card">
                    <div class="vex-kpi-icon-wrap vex-kpi-icon-ok">✓</div>
                    <div>
                        <div class="vex-kpi-val" id="vex-kpi-done-val">—</div>
                        <div class="vex-kpi-lbl" data-i18n="vex-kpi-done">已完成</div>
                    </div>
                </div>
                <div class="vex-kpi-card">
                    <div class="vex-kpi-icon-wrap vex-kpi-icon-err">!</div>
                    <div>
                        <div class="vex-kpi-val" id="vex-kpi-failed-val">—</div>
                        <div class="vex-kpi-lbl" data-i18n="vex-kpi-failed">失败</div>
                    </div>
                </div>
            </div>

            <!-- v4.10.6 · 主操作区(上移到列表上方) -->
            <div class="vex-main-action">
                <div class="vex-main-action-tag" data-i18n="vex-main-action-tag">主操作</div>

            <!-- v118.32.4.10.1 · Excel 对账上传区(全网开放) -->
            <div id="vex-pane">
                <!-- 左右双拖拽区(防呆 · 中间间距) -->
                <div class="vex-drops">
                    <div class="vex-drop vex-drop-invoice" id="vex-drop-invoice" role="button" tabindex="0">
                        <div class="vex-drop-icon-wrap">
                            <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M8 4h12l6 6v16a2 2 0 01-2 2H8a2 2 0 01-2-2V6a2 2 0 012-2z"/>
                                <path d="M20 4v6h6M10 16h12M10 21h8"/>
                            </svg>
                        </div>
                        <div class="vex-drop-title" data-i18n="vex-drop-invoice-title">销售发票</div>
                        <div class="vex-drop-sub" data-i18n="vex-drop-invoice-sub">PDF / 图片 / Excel / CSV / Word · 多文件 · 自动识别</div>
                        <input type="file" id="vex-input-invoice" multiple accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.xlsx,.xls,.xlsm,.csv,.tsv,.docx,.doc" style="display:none">
                    </div>
                    <div class="vex-drop-divider" aria-hidden="true">
                        <span>+</span>
                    </div>
                    <div class="vex-drop vex-drop-report" id="vex-drop-report" role="button" tabindex="0">
                        <div class="vex-drop-icon-wrap">
                            <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="5" y="6" width="22" height="20" rx="2"/>
                                <line x1="5" y1="12" x2="27" y2="12"/>
                                <line x1="10" y1="6" x2="10" y2="12"/>
                                <line x1="22" y1="6" x2="22" y2="12"/>
                                <line x1="9" y1="17" x2="16" y2="17"/>
                                <line x1="9" y1="21" x2="14" y2="21"/>
                            </svg>
                        </div>
                        <div class="vex-drop-title" data-i18n="vex-drop-report-title">VAT 报告</div>
                        <div class="vex-drop-sub" data-i18n="vex-drop-report-sub">PDF / 图片 / Excel / CSV / Word · 多文件 · 自动识别</div>
                        <input type="file" id="vex-input-report" multiple accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.xlsx,.xls,.xlsm,.csv,.tsv,.docx,.doc" style="display:none">
                    </div>
                </div>

                <!-- 操作栏 -->
                <div class="vex-action-bar">
                    <button class="btn btn-ghost" id="vex-reset" type="button" data-i18n="vex-btn-reset">清空</button>
                    <div class="vex-action-info" id="vex-action-info"></div>
                    <button class="vex-toggle-preview-btn" id="vex-toggle-preview" type="button">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
                        <span id="vex-toggle-preview-label" data-i18n="vex-toggle-preview-open">查看清单</span>
                    </button>
                    <button class="btn btn-primary" id="vex-build" type="button" disabled>
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M8 2v9M4 7l4 4 4-4M3 14h10"/>
                        </svg>
                        <span data-i18n="vex-btn-build">开始对账</span>
                    </button>
                </div>

                <!-- v4.10.11 · 上传清单预览面板 -->
                <div class="vex-preview-panel" id="vex-preview-panel" style="display:none">
                    <div class="vex-pp-grid">
                        <div id="vex-pp-invoice-col"></div>
                        <div id="vex-pp-report-col"></div>
                    </div>
                    <div class="vex-pp-guide" id="vex-pp-guide" style="display:none">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                        <span data-i18n="vex-preview-guide-search">文件多(800+ 张)时用搜索框过滤 · 滚动到底自动加载</span>
                    </div>
                </div>

                <!-- 进度区(跑中显示) -->
                <div class="vex-progress" id="vex-progress" style="display:none">
                    <div class="spinner"></div>
                    <div>
                        <div class="vex-progress-title" id="vex-progress-title" data-i18n="vex-progress-running">对账中…</div>
                        <div class="vex-progress-sub" id="vex-progress-sub"></div>
                    </div>
                </div>

                <!-- v118.32.5.5.19 · 对账汇总 折叠区(对齐 GL 风格 · 跑完后显示)-->
                <div class="recon-collapse" id="vex-summary-collapse" data-collapsed="true" style="display:none;margin-top:14px">
                    <div class="recon-collapse-head" data-toggle="vex-summary-collapse" tabindex="0" role="button">
                        <svg class="recon-collapse-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="5 7 8 10 11 7"/>
                        </svg>
                        <span class="recon-collapse-title" data-i18n="vex-summary-title">对账汇总</span>
                        <span class="recon-collapse-sub" id="vex-summary-sub"></span>
                        <div class="glv-section-spacer"></div>
                        <a class="btn btn-ghost btn-small glv-section-action" id="vex-download" href="#" download style="display:none">
                            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M8 2v9M4 7l4 4 4-4M3 14h10"/>
                            </svg>
                            <span data-i18n="glv-btn-export">导出 Excel</span>
                        </a>
                    </div>
                    <div class="recon-collapse-body">
                        <div class="recon-summary-grid" id="vex-summary-grid">
                            <div class="recon-sum-card"><div class="recon-sum-val" id="vex-sum-total">—</div><div class="recon-sum-lbl" data-i18n="vex-sum-total">总笔数</div></div>
                            <div class="recon-sum-card"><div class="recon-sum-val recon-sum-ok" id="vex-sum-matched">—</div><div class="recon-sum-lbl" data-i18n="vex-sum-matched">完全一致</div></div>
                            <div class="recon-sum-card"><div class="recon-sum-val recon-sum-warn" id="vex-sum-diff">—</div><div class="recon-sum-lbl" data-i18n="vex-sum-diff">数据差异</div></div>
                            <div class="recon-sum-card"><div class="recon-sum-val recon-sum-err" id="vex-sum-incomplete">—</div><div class="recon-sum-lbl" data-i18n="vex-sum-incomplete">OCR 漏识别</div></div>
                            <div class="recon-sum-card"><div class="recon-sum-val" id="vex-sum-cash">—</div><div class="recon-sum-lbl" data-i18n="vex-sum-cash">散客无发票</div></div>
                        </div>
                    </div>
                </div>

                <!-- v118.32.5.5.19 · 差异明细 折叠区(列出最新任务的字段差异行)-->
                <div class="recon-collapse" id="vex-detail-collapse" data-collapsed="true" style="display:none;margin-top:10px">
                    <div class="recon-collapse-head" data-toggle="vex-detail-collapse" tabindex="0" role="button">
                        <svg class="recon-collapse-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="5 7 8 10 11 7"/>
                        </svg>
                        <span class="recon-collapse-title" data-i18n="vex-detail-title">差异明细</span>
                        <span class="recon-collapse-sub" id="vex-detail-sub"></span>
                    </div>
                    <div class="recon-collapse-body">
                        <div class="recon-detail-empty" id="vex-detail-empty" data-i18n="vex-detail-empty">本次对账未发现差异</div>
                        <table class="recon-detail-table" id="vex-detail-table" style="display:none">
                            <thead>
                                <tr>
                                    <th data-i18n="vex-detail-h-inv">发票号</th>
                                    <th data-i18n="vex-detail-h-field">差异字段</th>
                                    <th data-i18n="vex-detail-h-rep">报告侧</th>
                                    <th data-i18n="vex-detail-h-inv-side">发票侧</th>
                                    <th data-i18n="vex-detail-h-kind">类型</th>
                                </tr>
                            </thead>
                            <tbody id="vex-detail-tbody"></tbody>
                        </table>
                    </div>
                </div>

                <!-- vex-download 已移至 vex-summary-collapse 头部 -->
            </div><!-- /vex-pane -->
            </div><!-- /vex-main-action -->

            <!-- v4.10.6 · 历史任务列表(移到主操作下方) -->
            <div class="vex-task-section" id="vex-task-section">
                <div class="vex-task-header-wrap">
                    <div class="vex-task-header" data-i18n="sv-recent-tasks">近期对账任务</div>
                    <input type="text" class="hist-search-input" id="vex-task-search" data-i18n-placeholder="hist-search-ph" placeholder="搜索..." autocomplete="off">
                </div>
                <div class="vex-task-table-wrap">
                    <table class="vex-task-table">
                        <thead>
                            <tr>
                                <th data-i18n="vex-col-time">创建时间</th>
                                <th data-i18n="vex-col-client">客户</th>
                                <th data-i18n="vex-col-period">期间</th>
                                <th data-i18n="vex-col-count">笔数</th>
                                <th data-i18n="vex-col-kpi">核对结果</th>
                                <th data-i18n="vex-col-diff">异常金额</th>
                                <th data-i18n="vex-col-status">状态</th>
                                <th data-i18n="vex-col-elapsed">用时</th>
                                <th data-i18n="vex-col-actions">操作</th>
                            </tr>
                        </thead>
                        <tbody id="vex-task-tbody"></tbody>
                    </table>
                    <div class="hist-pager" id="vex-task-pager" style="display:none">
                        <button class="hist-pager-btn" id="vex-task-prev" type="button" disabled>&#8592;</button>
                        <span class="hist-pager-info" id="vex-task-pager-info"></span>
                        <button class="hist-pager-btn" id="vex-task-next" type="button">&#8594;</button>
                    </div>
                </div>
            </div>

            <!-- ── 新建对账抽屉/模态(屏 A 核心) ── -->

        </div><!-- /recon-pane-sale-vat -->

        <!-- ══════════════════════════════════════════════════════════════
             v118.32.5 · GL vs 销项税报告 收入对账面板
             复用 vex-drops / vex-drop / vex-action-bar 现有视觉
             ══════════════════════════════════════════════════════════════ -->
        <div id="recon-pane-gl-vat" class="recon-pane" style="display:none">


            <!-- KPI 3 卡（沿用 vex-kpi-strip 视觉 · 默认可见，跑完更新数字） -->
            <div class="vex-kpi-strip" id="glv-kpi-strip">
                <div class="vex-kpi-card">
                    <div class="vex-kpi-icon-wrap vex-kpi-icon-ok">✓</div>
                    <div>
                        <div class="vex-kpi-val" id="glv-kpi-matched">—</div>
                        <div class="vex-kpi-lbl" data-i18n="glv-kpi-matched">完全匹配</div>
                    </div>
                </div>
                <div class="vex-kpi-card">
                    <div class="vex-kpi-icon-wrap vex-kpi-icon-warn">⚠</div>
                    <div>
                        <div class="vex-kpi-val" id="glv-kpi-diff">—</div>
                        <div class="vex-kpi-lbl" data-i18n="glv-kpi-diff">有差异</div>
                    </div>
                </div>
                <div class="vex-kpi-card">
                    <div class="vex-kpi-icon-wrap vex-kpi-icon-err">!</div>
                    <div>
                        <div class="vex-kpi-val" id="glv-kpi-unmatched">—</div>
                        <div class="vex-kpi-lbl" data-i18n="glv-kpi-unmatched">GL 未找到</div>
                    </div>
                </div>
            </div>

            <!-- 主操作区(沿用 vex-main-action 视觉) -->
            <div class="vex-main-action">
                <div class="vex-main-action-tag" data-i18n="vex-main-action-tag">主操作</div>

                <!-- 左右双拖拽区 -->
                <div class="vex-drops">
                    <div class="vex-drop vex-drop-invoice" id="glv-drop-vat" role="button" tabindex="0">
                        <div class="vex-drop-icon-wrap">
                            <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="5" y="6" width="22" height="20" rx="2"/>
                                <line x1="5" y1="12" x2="27" y2="12"/>
                                <line x1="10" y1="6" x2="10" y2="12"/>
                                <line x1="22" y1="6" x2="22" y2="12"/>
                                <line x1="9" y1="17" x2="16" y2="17"/>
                                <line x1="9" y1="21" x2="14" y2="21"/>
                            </svg>
                        </div>
                        <div class="vex-drop-title" data-i18n="glv-up-vat-title">① 销项税报告</div>
                        <div class="vex-drop-sub"   data-i18n="glv-up-vat-sub">PDF / 图片 / Excel / CSV / Word · 多文件 · 自动识别</div>
                        <div class="vex-drop-filename" id="glv-vat-name"></div>
                        <input type="file" id="glv-vat-input" accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.bmp,.gif,.xlsx,.xls,.xlsm,.csv,.tsv,.docx,.doc,.txt" multiple style="display:none">
                    </div>

                    <div class="vex-drop-divider" aria-hidden="true"><span>+</span></div>

                    <div class="vex-drop vex-drop-report" id="glv-drop-gl" role="button" tabindex="0">
                        <div class="vex-drop-icon-wrap">
                            <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M6 6h20v6H6z"/>
                                <path d="M6 14h10v12H6z"/>
                                <path d="M18 14h8v6h-8z"/>
                                <path d="M18 22h8v4h-8z"/>
                            </svg>
                        </div>
                        <div class="vex-drop-title" data-i18n="glv-up-gl-title">② 总账 GL</div>
                        <div class="vex-drop-sub"   data-i18n="glv-up-gl-sub">PDF / 图片 / Excel / CSV / Word · 多文件 · 自动识别</div>
                        <div class="vex-drop-filename" id="glv-gl-name"></div>
                        <input type="file" id="glv-gl-input" accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.bmp,.gif,.xlsx,.xls,.xlsm,.csv,.tsv,.docx,.doc,.txt" multiple style="display:none">
                    </div>
                </div>

                <!-- 操作栏 · v5.5.23 加 toggle 查看清单按钮 · 复刻销售税核查同款 -->
                <div class="vex-action-bar">
                    <button class="btn btn-ghost" id="btn-glv-reset" type="button" data-i18n="vex-btn-reset">清空</button>
                    <div class="vex-action-info muted" id="glv-status">
                        <span data-i18n="glv-hint-need-both">请先上传两份文件</span>
                    </div>
                    <button class="vex-toggle-preview-btn" id="glv-toggle-preview" type="button">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
                        <span id="glv-toggle-preview-label" data-i18n="vex-toggle-preview-open">查看清单</span>
                    </button>
                    <label class="glv-acct-prefix-wrap">
                        <span class="glv-acct-prefix-lbl" data-i18n="glv-acct-prefix">收入科目前缀</span>
                        <input type="text" id="glv-prefix" value="4" maxlength="3" class="glv-acct-prefix-input">
                    </label>
                    <button class="btn btn-primary" id="btn-glv-run" type="button" disabled>
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M3 8l4 4 6-8"/>
                        </svg>
                        <span data-i18n="glv-btn-run">开始对账</span>
                    </button>
                </div>

                <!-- v5.5.23 · 查看清单面板(同款 .vex-preview-panel 视觉) -->
                <div class="vex-preview-panel" id="glv-preview-panel" style="display:none">
                    <div class="vex-pp-grid">
                        <div id="glv-pp-vat-col"></div>
                        <div id="glv-pp-gl-col"></div>
                    </div>
                </div>

                <!-- 跑中进度 -->
                <div class="vex-progress" id="glv-progress" style="display:none">
                    <div class="spinner"></div>
                    <div>
                        <div class="vex-progress-title" data-i18n="glv-running">对账中…</div>
                        <div class="vex-progress-sub" id="glv-progress-sub"></div>
                    </div>
                </div>

                <!-- 结果区(默认隐藏) -->
                <div id="glv-result" style="display:none;margin-top:14px;">
                    <!-- 对账汇总 · 可折叠分区（默认收起） -->
                    <div class="glv-section" id="glv-section-summary" data-collapsed="true">
                        <div class="glv-section-head" data-toggle="glv-section-summary" tabindex="0" role="button">
                            <svg class="glv-section-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="5 7 8 10 11 7"/>
                            </svg>
                            <span class="glv-section-title" data-i18n="glv-summary-title">对账汇总</span>
                            <div class="glv-section-spacer"></div>
                            <button class="btn btn-ghost btn-small glv-section-action" id="btn-glv-export" type="button">
                                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M8 2v9M4 7l4 4 4-4M3 14h10"/>
                                </svg>
                                <span data-i18n="glv-btn-export">导出 Excel</span>
                            </button>
                        </div>
                        <div class="glv-section-body">
                            <table class="glv-summary-table" id="glv-summary-table">
                                <tbody></tbody>
                            </table>
                        </div>
                    </div>

                    <!-- 差异明细 · 可折叠分区（默认收起） -->
                    <div class="glv-section" id="glv-section-detail" data-collapsed="true" style="margin-top:10px;">
                        <div class="glv-section-head" data-toggle="glv-section-detail" tabindex="0" role="button">
                            <svg class="glv-section-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="5 7 8 10 11 7"/>
                            </svg>
                            <span class="glv-section-title" data-i18n="glv-detail-title">差异明细</span>
                            <span class="glv-section-count" id="glv-detail-count"></span>
                        </div>
                        <div class="glv-section-body">
                            <div class="glv-table-wrap">
                                <table class="glv-table" id="glv-table">
                                    <thead>
                                        <tr>
                                            <th data-i18n="glv-h-doc">单据号</th>
                                            <th data-i18n="glv-h-date">日期</th>
                                            <th data-i18n="glv-h-customer">客户</th>
                                            <th class="glv-num" data-i18n="glv-h-vat">VAT 金额</th>
                                            <th class="glv-num" data-i18n="glv-h-gl">GL 金额</th>
                                            <th class="glv-num" data-i18n="glv-h-diff">差异</th>
                                            <th data-i18n="glv-h-acct">收入科目</th>
                                        </tr>
                                    </thead>
                                    <tbody id="glv-tbody"></tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div><!-- /glv-result -->
            </div><!-- /vex-main-action -->

            <!-- 近期对账任务（沿用销项税对账的视觉） -->
            <div class="glv-history" id="glv-history">
                <div class="glv-result-head">
                    <div class="glv-result-title" data-i18n="glv-history-title">近期对账任务</div>
                    <input type="text" class="hist-search-input" id="glv-hist-search" data-i18n-placeholder="hist-search-ph" placeholder="搜索..." autocomplete="off">
                </div>
                <div class="glv-history-empty" id="glv-history-empty" data-i18n="glv-history-empty">
                    暂无对账记录
                </div>
                <div class="glv-history-table-wrap" id="glv-history-table-wrap" style="display:none;">
                <table class="glv-history-table" id="glv-history-table">
                    <thead>
                        <tr>
                            <th data-i18n="glv-hist-time">时间</th>
                            <th data-i18n="glv-hist-files">文件</th>
                            <th class="glv-num" data-i18n="glv-hist-rows">行数 (VAT/GL)</th>
                            <th class="glv-num" data-i18n="glv-hist-matched">匹配</th>
                            <th class="glv-num" data-i18n="glv-hist-diff">差异</th>
                            <th class="glv-num" data-i18n="glv-hist-missing">缺失</th>
                            <th data-i18n="glv-hist-actions">操作</th>
                        </tr>
                    </thead>
                    <tbody id="glv-history-tbody"></tbody>
                </table>
                <div class="hist-pager" id="glv-history-pager" style="display:none">
                    <button class="hist-pager-btn" id="glv-history-prev" type="button" disabled>&#8592;</button>
                    <span class="hist-pager-info" id="glv-history-pager-info"></span>
                    <button class="hist-pager-btn" id="glv-history-next" type="button">&#8594;</button>
                </div>
                </div>
            </div>

        </div><!-- /recon-pane-gl-vat -->


`;
    sec.dataset.wbInjected = '1';
    try {
        const lang = window._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
        const I = window.I18N;
        if (I && I[lang]) {
            sec.querySelectorAll('[data-i18n]').forEach((el) => {
                const k = el.getAttribute('data-i18n');
                if (I[lang][k]) el.textContent = I[lang][k];
            });
            sec.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
                const k = el.getAttribute('data-i18n-placeholder');
                if (I[lang][k]) el.placeholder = I[lang][k];
            });
        }
    } catch (e) {
        /* silent · 初译失败不致命 · 切语言会补 */
    }
})();
