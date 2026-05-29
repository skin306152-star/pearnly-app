(function(){const e=document.getElementById("page-reconcile");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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


`,e.dataset.wbInjected="1";try{const a=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",n=window.I18N;n&&n[a]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const l=s.getAttribute("data-i18n");n[a][l]&&(s.textContent=n[a][l])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const l=s.getAttribute("data-i18n-placeholder");n[a][l]&&(s.placeholder=n[a][l])}))}catch{}}})();(function(){const e=document.getElementById("page-integrations");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
        <div class="page-head-clean">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M9 16L4 21M15 8l5-5"/>
                    <path d="M11 5L6 10a3 3 0 000 4l4 4a3 3 0 004 0l5-5a3 3 0 000-4l-4-4a3 3 0 00-4 0z"/>
                </svg>
            </div>
            <div class="page-head-text">
                <div class="page-head-title" data-i18n="integrations-title">集成</div>
                <div class="page-head-sub" data-i18n="integrations-sub">Google · LINE · 邮箱 · ERP · 文件夹 · 云盘 等第三方授权 · 让 Pearnly 自动同步数据</div>
            </div>
        </div>

        <!-- A4 · 顶部 tab 切换 -->
        <div class="int-top-tabs" role="tablist">
            <button class="int-top-tab active" type="button" data-int-top-tab="cards" data-i18n="int-tab-cards">集成卡片</button>
            <button class="int-top-tab" type="button" data-int-top-tab="logs" data-i18n="int-tab-logs">推送日志</button>
        </div>

        <!-- Tab 1: integration-row 卡片(现有内容不变) -->
        <div class="int-top-panel active" data-int-top-panel="cards">
        <div class="card">
            <!-- Google 一次授权双服务 · 蓝色信息条 -->
            <div class="integrations-info-bar">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="10" cy="10" r="8"/>
                    <line x1="10" y1="6" x2="10" y2="10"/>
                    <circle cx="10" cy="14" r="0.6" fill="currentColor"/>
                </svg>
                <span data-i18n="integrations-google-info">授权一次 Google 账号 · Drive 和 Sheets 均可使用 · 无需重复授权</span>
            </div>

            <!-- 第 1 组 · Google 服务 -->
            <div class="integrations-section-title" data-i18n="integrations-section-google">GOOGLE 服务</div>

            <div class="integration-row" data-int-target="automation" data-int-anchor="google-drive">
                <div class="int-icon ic-g">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 2L4 16h6l2-4h4l2 4h-6L12 2z"/>
                    </svg>
                </div>
                <div class="int-info">
                    <div class="int-name"><span data-i18n="int-name-drive">Google Drive</span></div>
                    <div class="int-desc" data-i18n="int-desc-drive">发票/PV 审核后自动存入 Drive · 按客户和月份归档</div>
                </div>
                <div class="int-actions">
                    <button class="int-btn-configure" data-route="automation" data-i18n="btn-configure">配置</button>
                </div>
            </div>

            <div class="integration-row" data-int-target="automation" data-int-anchor="google-sheets">
                <div class="int-icon ic-gs">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                        <path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>
                    </svg>
                </div>
                <div class="int-info">
                    <div class="int-name"><span data-i18n="int-name-sheets">Google Sheets</span></div>
                    <div class="int-desc" data-i18n="int-desc-sheets">识别结果实时同步到 Sheets · 老板/会计师在线查看</div>
                </div>
                <div class="int-actions">
                    <button class="int-btn-configure" data-route="automation" data-i18n="btn-configure">配置</button>
                </div>
            </div>

            <div class="sec-divider"></div>

            <!-- 第 2 组 · 收票渠道(含 Gmail · v118.32.5.5.37 调整) -->
            <div class="integrations-section-title" data-i18n="integrations-section-channels">收票渠道</div>

            <!-- Gmail 抓取移至收票渠道(邮件是收票渠道 · 非 Google 产品功能) -->
            <div class="integration-row" data-int-target="automation" data-int-anchor="gmail">
                <div class="int-icon ic-gm">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="5" width="18" height="14" rx="2"/>
                        <path d="M3 7l9 6 9-6"/>
                    </svg>
                </div>
                <div class="int-info">
                    <div class="int-name"><span data-i18n="int-name-gmail">Gmail 抓取</span></div>
                    <div class="int-desc" data-i18n="int-desc-gmail">客户发来邮件附件自动抓 · 不用手动转发</div>
                </div>
                <div class="int-actions">
                    <button class="int-btn-configure" data-route="automation" data-i18n="btn-configure">配置</button>
                </div>
            </div>

            <div class="integration-row" data-int-target="automation" data-int-anchor="line">
                <div class="int-icon ic-line">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 5.96 2 10.84c0 4.37 3.55 8.04 8.36 8.74.32.07.77.21.88.49.1.25.07.65.03.91l-.14.86c-.04.25-.2.99.87.54 1.07-.46 5.77-3.4 7.87-5.82C21.32 15.04 22 13.05 22 10.84 22 5.96 17.52 2 12 2z"/>
                    </svg>
                </div>
                <div class="int-info">
                    <div class="int-name"><span data-i18n="int-name-line">LINE Bot</span></div>
                    <div class="int-desc" data-i18n="int-desc-line">外勤拍照发 LINE · 自动入账 · 单聊群聊都支持</div>
                </div>
                <div class="int-actions">
                    <button class="int-btn-configure" data-route="automation" data-i18n="btn-configure">配置</button>
                </div>
            </div>

            <div class="integration-row" data-int-target="automation" data-int-anchor="folder">
                <div class="int-icon ic-folder">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 7a2 2 0 012-2h4l2 3h8a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V7z"/>
                    </svg>
                </div>
                <div class="int-info">
                    <div class="int-name"><span data-i18n="int-name-folder">文件夹监听</span></div>
                    <div class="int-desc" data-i18n="int-desc-folder">指定本地/共享文件夹 · 扔进去就自动识别</div>
                </div>
                <div class="int-actions">
                    <button class="int-btn-configure" data-route="automation" data-i18n="btn-configure">配置</button>
                </div>
            </div>

            <div class="sec-divider"></div>

            <!-- 第 3 组 · ERP 系统 -->
            <div class="integrations-section-title" data-i18n="integrations-section-erp">ERP 系统</div>

            <div class="integration-row" data-int-target="automation" data-int-anchor="erp">
                <div class="int-icon ic-erp">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                        <path d="M9 9h6v6H9z"/>
                        <path d="M9 3v6M15 3v6M9 15v6M15 15v6M3 9h6M3 15h6M15 9h6M15 15h6"/>
                    </svg>
                </div>
                <div class="int-info">
                    <div class="int-name"><span data-i18n="int-name-erp">ERP 对接</span></div>
                    <div class="int-desc" data-i18n="int-desc-erp">Xero · MR.ERP · Webhook 等 · 识别完自动推到 ERP</div>
                </div>
                <div class="int-actions">
                    <!-- Bug 4 (Zihao 2026-05-19 拍板 · v118.34.22) · 集成卡片右下「看推送日志」link 删 ·
                         入口收敛: 点「配置」进 ERP 抽屉 → 在抽屉里点「看推送日志 →」 ·
                         或直接点集成主页顶部的「推送日志」tab. -->
                    <button class="int-btn-configure" data-route="automation" data-i18n="btn-configure">配置</button>
                </div>
            </div>

            <div class="sec-divider"></div>

            <!-- v118.32.5.5.37 NAV-IA Phase 5 收尾 · 自动化 & 提醒 区块 -->
            <div class="integrations-section-title" data-i18n="int-section-automation">通知提醒</div>

            <div class="integration-row" data-int-target="drawer" data-int-anchor="alert">
                <div class="int-icon ic-alert">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
                        <path d="M10 21a2 2 0 0 0 4 0"/>
                    </svg>
                </div>
                <div class="int-info">
                    <div class="int-name"><span data-i18n="auto-alert-title">智能提醒</span></div>
                    <div class="int-desc" data-i18n="auto-alert-desc">异常 high 或大额发票发生时 · 自动推送到老板/会计的 LINE</div>
                </div>
                <div class="int-actions">
                    <button class="int-btn-configure" data-i18n="btn-configure">配置</button>
                </div>
            </div>
        </div>
        </div>
        <!-- /Tab 1 -->

        <!-- Tab 2: 推送日志(从 auto-panel="erp" subpanel="logs" 搬过来 · A4 · v118.34.19) -->
        <div class="int-top-panel" data-int-top-panel="logs">
            <div class="card">
                <!-- 今日推送统计 -->
                <div id="erp-today-stats" class="erp-today-stats"></div>
                <section class="erp-logs-section" id="erp-logs-section">
                    <div class="erp-logs-head">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="8" cy="8" r="6"/><path d="M8 5v3l2 1"/>
                        </svg>
                        <span data-i18n="erp-logs-title">推送日志</span>
                        <span class="erp-logs-today-stats" id="erp-logs-today-stats"></span>
                    </div>

                    <div class="erp-logs-toolbar">
                        <div class="erp-logs-filters" id="erp-logs-filters">
                            <button class="chip-filter active" data-filter-key="all" data-filter-val=""><span data-i18n="erp-logs-filter-all">全部</span></button>
                            <button class="chip-filter" data-filter-key="status" data-filter-val="success">✓ <span data-i18n="erp-logs-filter-ok">成功</span></button>
                            <button class="chip-filter" data-filter-key="status" data-filter-val="retrying">↻ <span data-i18n="erp-logs-filter-retrying">重试中</span></button>
                            <button class="chip-filter" data-filter-key="status" data-filter-val="failed">✗ <span data-i18n="erp-logs-filter-fail">失败</span></button>
                            <button class="chip-filter" data-filter-key="trigger" data-filter-val="auto"><span data-i18n="erp-logs-filter-auto">自动</span></button>
                            <button class="chip-filter" data-filter-key="trigger" data-filter-val="manual"><span data-i18n="erp-logs-filter-manual">手动</span></button>
                            <!-- 批 3 改动 6 (Zihao 2026-05-19 拍板 · v118.34.34) · ERP filter chip ·
                                 按 endpoint_adapter 过滤(mrerp/xero) · FlowAccount 还没上线灰显. -->
                            <span class="erp-logs-filter-sep" aria-hidden="true">|</span>
                            <button class="chip-filter" data-filter-key="adapter" data-filter-val="mrerp"><span data-i18n="erp-logs-filter-mrerp">MR.ERP</span></button>
                            <button class="chip-filter" data-filter-key="adapter" data-filter-val="xero"><span data-i18n="erp-logs-filter-xero">Xero</span></button>
                            <button class="chip-filter chip-filter-disabled" data-filter-key="adapter" data-filter-val="flowaccount" disabled title="即将上线"><span data-i18n="erp-logs-filter-flowaccount">FlowAccount</span> <span class="chip-soon" data-i18n="erp-logs-filter-soon">即将</span></button>
                        </div>
                        <button class="btn btn-ghost btn-tiny" id="btn-refresh-logs" title="刷新">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M11.5 7a4.5 4.5 0 11-1.3-3.2M12 2v3h-3"/></svg>
                        </button>
                    </div>

                    <div id="erp-logs-batch-bar" class="erp-logs-batch-bar" style="display:none;">
                        <span class="erp-logs-batch-count" id="erp-logs-batch-count" data-i18n="erp-batch-selected" data-i18n-vars='{"n":0}'>已选 0 条</span>
                        <button class="btn btn-primary btn-tiny" id="btn-erp-batch-retry">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M11.5 7a4.5 4.5 0 11-1.3-3.2M12 2v3h-3"/></svg>
                            <span data-i18n="erp-batch-retry-btn">批量重推</span>
                        </button>
                        <!-- Bug 6 (Zihao 2026-05-19 拍板 · v118.34.23) · 批量删除按钮 -->
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
        </div>
        <!-- /Tab 2 -->
`,e.dataset.wbInjected="1";try{const a=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",n=window.I18N;n&&n[a]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const l=s.getAttribute("data-i18n");n[a][l]&&(s.textContent=n[a][l])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const l=s.getAttribute("data-i18n-placeholder");n[a][l]&&(s.placeholder=n[a][l])}))}catch{}}})();(function(){const e=document.getElementById("page-settings");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
        <!-- v118.27.5.1 · page-head · 视觉对齐自动化页/识别中心 -->
        <div class="page-head-clean">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="3"/>
                    <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 11-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 110-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 114 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 110 4h-.09a1.65 1.65 0 00-1.51 1z"/>
                </svg>
            </div>
            <div class="page-head-text">
                <div class="page-head-title" data-i18n="set-page-title">设置</div>
                <div class="page-head-sub" data-i18n="set-page-sub">管理你的账户、公司和工作流</div>
            </div>
        </div>

        <!-- v118.27.5.2 · settings-layout wrapper · 跟自动化 .auto-layout 同结构 · 修响应式问题 -->
        <div class="settings-layout">
            <!-- v118.27.4 · 设置左侧 4 大类二级导航 · 参考 Notion / Linear · 替代原顶部水平 tabs -->
            <aside class="settings-side-nav" id="settings-tabs">
            <div class="settings-nav-group">
                <div class="settings-nav-group-title" data-i18n="set-group-account">账户</div>
                <button class="settings-tab settings-nav-item active" data-tab="profile" data-i18n="set-tab-profile">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="7" r="3.5"/><path d="M3.5 17a6.5 6.5 0 0113 0"/></svg>
                    <span>个人资料</span>
                </button>
                <button class="settings-tab settings-nav-item" data-tab="security" data-i18n="set-tab-security">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="9" width="12" height="8" rx="1.5"/><path d="M7 9V6.5a3 3 0 016 0V9"/></svg>
                    <span>账户安全</span>
                </button>
                <button class="settings-tab settings-nav-item" data-tab="notifications" data-i18n="set-tab-notifications">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 8a5 5 0 0110 0v4l1.5 2h-13l1.5-2V8z"/><path d="M8 17a2 2 0 004 0"/></svg>
                    <span>通知偏好</span>
                </button>
            </div>
            <div class="settings-nav-group">
                <div class="settings-nav-group-title" data-i18n="set-group-company">公司</div>
                <button class="settings-tab settings-nav-item" data-tab="company" data-i18n="set-tab-company">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17V7l7-3 7 3v10"/><path d="M3 17h14M8 12h4M8 17v-4"/></svg>
                    <span>公司信息</span>
                </button>
                <button class="settings-tab settings-nav-item" data-tab="team" data-i18n="set-tab-team">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="14" cy="6.5" r="3"/><circle cx="6" cy="6.5" r="3"/><path d="M2 17v-1.5a3 3 0 013-3h2a3 3 0 013 3V17M11 13a3 3 0 013-3h2a3 3 0 013 3v4"/></svg>
                    <span>团队管理</span>
                </button>
                <button class="settings-tab settings-nav-item" data-tab="plan" data-i18n="set-tab-plan">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="6" width="14" height="10" rx="1.5"/><path d="M3 9h14M7 13h2"/></svg>
                    <span>用量</span>
                </button>
            </div>
            <div class="settings-nav-group">
                <div class="settings-nav-group-title" data-i18n="set-group-workflow">工作流</div>
                <button class="settings-tab settings-nav-item" data-tab="archive" data-i18n="set-tab-archive">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="14" height="3" rx="0.5"/><rect x="4" y="8" width="12" height="9" rx="1"/><path d="M8 11h4"/></svg>
                    <span>归档规则</span>
                </button>
                <button class="settings-tab settings-nav-item" data-tab="learned" data-i18n="set-tab-learned">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="6.5"/><path d="M7 10l2 2 4-4"/></svg>
                    <span>学习规则</span>
                </button>
                <!-- v118.35.0.16 · API & 密钥 tab 永久下线 · credits 系统接管 -->
            </div>
            <div class="settings-nav-group">
                <div class="settings-nav-group-title" data-i18n="set-group-system">系统</div>
                <button class="settings-tab settings-nav-item" data-tab="general" data-i18n="set-tab-general">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="2.5"/><path d="M10 2v2M10 16v2M2 10h2M16 10h2M4.2 4.2l1.4 1.4M14.4 14.4l1.4 1.4M4.2 15.8l1.4-1.4M14.4 5.6l1.4-1.4"/></svg>
                    <span>通用设置</span>
                </button>
                <!-- v118.28.8 · 仅 owner 可见 · 由 JS 控制显隐 -->
                <button class="settings-tab settings-nav-item set-tab-owner-only" data-tab="access-log" data-i18n="set-tab-access-log" style="display:none;">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="14" height="14" rx="2"/><path d="M7 8h6M7 11h6M7 14h4"/></svg>
                    <span>Pearnly 访问日志</span>
                </button>
            </div>
            <div class="settings-nav-group">
                <div class="settings-nav-group-title" data-i18n="set-group-about">关于</div>
                <button class="settings-tab settings-nav-item" data-tab="about" data-i18n="set-tab-about">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="8"/><path d="M10 13V9.5M10 7v0.01"/></svg>
                    <span>联系我们</span>
                </button>
            </div>
        </aside>

        <div class="settings-content">
            <!-- Tab 1 · 个人资料 -->
            <div class="settings-pane active" data-pane="profile">
                <div class="card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="set-profile-title">个人资料</div>
                        <div class="section-sub" data-i18n="set-profile-sub">这些信息只用于个性化体验 · 不会公开</div>
                    </div>
                    <div class="profile-form">
                        <div class="form-row">
                            <label data-i18n="set-profile-username">用户名</label>
                            <input type="text" id="profile-username" class="form-input" disabled>
                            <div class="form-hint" data-i18n="set-profile-username-hint">用户名注册后不可修改</div>
                        </div>
                        <div class="form-row">
                            <label data-i18n="set-profile-email">邮箱</label>
                            <input type="email" id="profile-email" class="form-input" disabled>
                        </div>
                        <div class="form-row">
                            <label data-i18n="set-profile-fullname">姓名(选填)</label>
                            <input type="text" id="profile-fullname" class="form-input" maxlength="64">
                        </div>
                        <div class="form-row">
                            <label data-i18n="set-profile-phone">电话(选填)</label>
                            <input type="tel" id="profile-phone" class="form-input" maxlength="32">
                        </div>
                        <div class="form-row">
                            <label data-i18n="set-profile-country">国家</label>
                            <select id="profile-country" class="form-input">
                                <option value="TH" data-i18n="country-th">泰国</option>
                                <option value="CN" data-i18n="country-cn">中国</option>
                                <option value="JP" data-i18n="country-jp">日本</option>
                                <option value="US" data-i18n="country-us">美国</option>
                                <option value="EN" data-i18n="country-other">其他</option>
                            </select>
                        </div>
                        <div class="form-row">
                            <label data-i18n="set-profile-line">LINE ID(选填)</label>
                            <input type="text" id="profile-line" class="form-input" maxlength="64" placeholder="@username">
                        </div>
                        <div class="form-actions">
                            <button class="btn btn-primary" id="btn-save-profile" data-i18n="set-save">保存修改</button>
                            <span class="form-msg" id="profile-save-msg"></span>
                        </div>
                    </div>
                </div>

                <!-- v118.28.5.1 · profile pane 不再放语言 · 已迁到 系统 → 通用设置 -->
            </div>

            <!-- Tab 2 · 公司信息 -->
            <div class="settings-pane" data-pane="company">
                <div class="card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="set-company-title">公司信息</div>
                        <div class="section-sub" data-i18n="set-company-sub">显示在工作台顶部和导出文件上 · 让团队成员有归属感</div>
                    </div>
                    <div class="profile-form">
                        <div class="form-row">
                            <label data-i18n="set-company-name">公司名称(选填)</label>
                            <input type="text" id="company-name" class="form-input" maxlength="200" placeholder="例如:ABC 会计事务所">
                            <div class="form-hint" data-i18n="set-company-name-hint">没有公司可留空 · 顶部将显示您的邮箱前缀</div>
                        </div>
                        <div class="form-row">
                            <label data-i18n="set-company-volume">月发票量(选填)</label>
                            <select id="company-volume" class="form-input">
                                <option value="" data-i18n="set-company-volume-none">— 选择 —</option>
                                <option value="0-50" data-i18n="vol-0-50">0-50 张</option>
                                <option value="50-200" data-i18n="vol-50-200">50-200 张</option>
                                <option value="200-1000" data-i18n="vol-200-1000">200-1000 张</option>
                                <option value="1000+" data-i18n="vol-1000-plus">1000+ 张</option>
                            </select>
                        </div>
                        <div class="form-row">
                            <label data-i18n="set-company-role">您的身份(选填)</label>
                            <select id="company-role" class="form-input">
                                <option value="" data-i18n="set-company-role-none">— 选择 —</option>
                                <option value="firm_owner" data-i18n="role-firm-owner">事务所老板 / 合伙人</option>
                                <option value="bookkeeper" data-i18n="role-bookkeeper">事务所会计 / 簿记员</option>
                                <option value="biz_owner" data-i18n="role-biz-owner">公司老板</option>
                                <option value="biz_finance" data-i18n="role-biz-finance">公司财务</option>
                                <option value="freelance" data-i18n="role-freelance">自由会计 / 个人</option>
                                <option value="other" data-i18n="role-other">其他</option>
                            </select>
                        </div>
                        <div class="form-actions">
                            <button class="btn btn-primary" id="btn-save-company" data-i18n="set-save">保存修改</button>
                            <span class="form-msg" id="company-save-msg"></span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tab 3 · 账户安全(修改密码) -->
            <div class="settings-pane" data-pane="security">
                <!-- v109.4 · 修改密码 -->
                <div class="card" id="change-pw-card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="settings-change-pw-title">修改密码</div>
                        <div class="section-sub" data-i18n="set-security-sub">建议每 90 天更换一次密码</div>
                    </div>
                    <!-- 防 autofill 诱饵字段 · 浏览器会把密码塞到这两个隐藏 input · 而不是真正的输入框 -->
                    <input type="text" name="username" autocomplete="username" style="display:none" tabindex="-1" aria-hidden="true">
                    <input type="password" name="password" autocomplete="current-password" style="display:none" tabindex="-1" aria-hidden="true">
                    <form class="change-pw-form" autocomplete="off" onsubmit="return false;">
                        <div class="cpw-field">
                            <label data-i18n="settings-change-pw-old">当前密码</label>
                            <div class="cpw-input-wrap">
                                <input type="password" id="cpw-old" class="cpw-input"
                                       name="cpw-old-randomname"
                                       autocomplete="off"
                                       autocorrect="off"
                                       autocapitalize="off"
                                       spellcheck="false"
                                       data-lpignore="true"
                                       data-1p-ignore="true"
                                       data-form-type="other"
                                       readonly
                                       value="">
                                <button type="button" class="cpw-eye" data-target="cpw-old" aria-label="show password">
                                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M2 10s3-6 8-6 8 6 8 6-3 6-8 6-8-6-8-6z"/><circle cx="10" cy="10" r="2.5"/></svg>
                                </button>
                            </div>
                            <div class="cpw-forgot-row">
                                <button type="button" class="cpw-forgot-link" id="cpw-forgot-link" data-i18n="settings-change-pw-forgot">忘记当前密码?</button>
                            </div>
                        </div>
                        <div class="cpw-field">
                            <label data-i18n="settings-change-pw-new">新密码</label>
                            <div class="cpw-input-wrap">
                                <input type="password" id="cpw-new" class="cpw-input"
                                       name="cpw-new-randomname"
                                       autocomplete="new-password"
                                       autocorrect="off"
                                       autocapitalize="off"
                                       spellcheck="false"
                                       data-lpignore="true"
                                       data-1p-ignore="true"
                                       readonly
                                       value="">
                                <button type="button" class="cpw-eye" data-target="cpw-new" aria-label="show password">
                                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M2 10s3-6 8-6 8 6 8 6-3 6-8 6-8-6-8-6z"/><circle cx="10" cy="10" r="2.5"/></svg>
                                </button>
                            </div>
                            <div class="cpw-strength" id="cpw-strength"><div class="cpw-strength-bar" id="cpw-strength-bar"></div></div>
                            <div class="cpw-hint" data-i18n="settings-change-pw-hint">至少 8 位 · 包含字母和数字</div>
                        </div>
                        <div class="cpw-field">
                            <label data-i18n="settings-change-pw-confirm">确认新密码</label>
                            <div class="cpw-input-wrap">
                                <input type="password" id="cpw-confirm" class="cpw-input"
                                       name="cpw-confirm-randomname"
                                       autocomplete="new-password"
                                       autocorrect="off"
                                       autocapitalize="off"
                                       spellcheck="false"
                                       data-lpignore="true"
                                       data-1p-ignore="true"
                                       readonly
                                       value="">
                                <button type="button" class="cpw-eye" data-target="cpw-confirm" aria-label="show password">
                                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M2 10s3-6 8-6 8 6 8 6-3 6-8 6-8-6-8-6z"/><circle cx="10" cy="10" r="2.5"/></svg>
                                </button>
                            </div>
                        </div>
                        <div class="cpw-msg" id="cpw-msg"></div>
                        <button type="button" class="btn btn-primary" id="btn-change-pw" data-i18n="settings-change-pw-submit">提交修改</button>
                    </form>
                </div>
            </div>

            <!-- Tab 4 · 通知偏好 -->
            <div class="settings-pane" data-pane="notifications">
                <div class="card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="set-notif-title">通知偏好</div>
                        <div class="section-sub" data-i18n="set-notif-sub">控制智能提醒和检测的行为</div>
                    </div>
                    <div class="settings-prefs-inline">
                        <div class="pref-row">
                            <div class="pref-info">
                                <div class="pref-title" data-i18n="pref-dup-check-title">重复发票检测</div>
                                <div class="pref-desc" data-i18n="pref-dup-check-desc">上传后自动检查发票号或字段组合是否与历史重复 · 弹窗提示</div>
                            </div>
                            <label class="toggle-switch">
                                <input type="checkbox" id="pref-dup-check" checked>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tab 5 · 用量(CLEANUP-PLAN-03 · 2026-05-22 · 老"套餐 & 用量" 改) -->
            <div class="settings-pane" data-pane="plan">
                <div class="card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="set-plan-title">用量</div>
                    </div>
                    <div id="settings-info"></div>
                </div>
            </div>

            <!-- Tab 6 · 团队管理(老板可见 · 由 JS 控制 tab 显隐) -->
            <div class="settings-pane settings-panel" data-pane="team" data-settings-panel="team">
                <div class="card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="team-title">员工管理</div>
                        <div class="section-sub" data-i18n="team-sub">添加员工后 · 他能用自己的账号登录 · 只看到本公司数据</div>
                    </div>

                    <div class="admin-toolbar">
                        <button class="btn btn-primary" id="btn-add-employee">
                            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M10 4v12M4 10h12"/>
                            </svg>
                            <span data-i18n="team-add">添加员工</span>
                        </button>
                        <div class="admin-stats" id="team-count"></div>
                    </div>

                    <div class="admin-table-wrap">
                        <div id="team-loading" class="admin-loading" data-i18n="admin-loading">加载中...</div>
                        <div class="team-list" id="team-list" style="display:none;"></div>
                        <div id="team-empty" class="admin-empty" style="display:none;" data-i18n="team-empty">还没有员工 · 点「添加员工」开始</div>
                    </div>
                </div>
            </div>

            <!-- v118.19.1 · Tab · 归档规则(从识别中心右上角移过来 · 低频功能) -->
            <div class="settings-pane" data-pane="archive">
                <div class="card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="set-archive-title">归档规则</div>
                        <div class="section-sub" data-i18n="set-archive-sub">设置批量下载 ZIP 时的文件命名模板 · 例如 日期_供应商_金额.pdf</div>
                    </div>
                    <button type="button" class="btn btn-primary" id="btn-open-archive-rule-from-settings" style="margin-top: 12px;">
                        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px;vertical-align:-3px;margin-right:6px;">
                            <rect x="3" y="4" width="14" height="12" rx="2"/>
                            <path d="M3 8h14M7 12h6"/>
                        </svg>
                        <span data-i18n="set-archive-open-btn">打开命名规则编辑器</span>
                    </button>
                </div>
            </div>

            <!-- v118.35.0.16 · Tab 7 API & 密钥(BYO Gemini Key)整段永久下线 · credits 系统不再需要用户自带 key -->

            <!-- v118.21.2 · 学习规则(撤销「忽略此类」白名单) -->
            <div class="settings-pane" data-pane="learned">
                <div class="card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="set-learned-title">学习规则</div>
                        <div class="section-sub" data-i18n="set-learned-sub">异常栏点过「永远忽略此类」后 · 系统会记住「该供应商 + 该规则」组合 · 下次自动放行 · 这里可撤销</div>
                    </div>
                    <div class="learned-list" id="learned-list">
                        <div class="learned-empty" data-i18n="set-learned-loading">加载中…</div>
                    </div>
                </div>
            </div>

            <!-- Tab · 通用设置(系统分组) -->
            <div class="settings-pane" data-pane="general">
                <div class="card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="set-general-title">通用设置</div>
                        <div class="section-sub" data-i18n="set-general-sub">语言 · 时区 · 日期 · 数字格式 · 一次设完不再动</div>
                    </div>
                    <div class="profile-form">
                        <div class="form-row form-row-inline">
                            <label data-i18n="set-general-lang">界面语言</label>
                            <select id="general-lang" class="form-input">
                                <option value="th">ไทย (TH)</option>
                                <option value="en">English (EN)</option>
                                <option value="zh">中文 (ZH)</option>
                                <option value="ja">日本語 (JA)</option>
                            </select>
                            <div class="form-hint" data-i18n="set-general-lang-hint">立即生效 · 自动同步到所有设备</div>
                        </div>
                        <div class="form-row form-row-inline">
                            <label data-i18n="set-general-tz">时区</label>
                            <select id="general-tz" class="form-input">
                                <option value="Asia/Bangkok">Asia/Bangkok (UTC+7)</option>
                                <option value="Asia/Shanghai">Asia/Shanghai (UTC+8)</option>
                                <option value="Asia/Tokyo">Asia/Tokyo (UTC+9)</option>
                                <option value="Asia/Singapore">Asia/Singapore (UTC+8)</option>
                                <option value="Asia/Hong_Kong">Asia/Hong_Kong (UTC+8)</option>
                                <option value="Asia/Taipei">Asia/Taipei (UTC+8)</option>
                                <option value="Asia/Kuala_Lumpur">Asia/Kuala_Lumpur (UTC+8)</option>
                                <option value="Asia/Jakarta">Asia/Jakarta (UTC+7)</option>
                                <option value="Asia/Ho_Chi_Minh">Asia/Ho_Chi_Minh (UTC+7)</option>
                                <option value="Asia/Manila">Asia/Manila (UTC+8)</option>
                                <option value="UTC">UTC (UTC+0)</option>
                            </select>
                            <div class="form-hint" data-i18n="set-general-tz-hint">用于报表 / 邮件时间戳 / 周报推送时间</div>
                        </div>
                        <div class="form-row form-row-inline">
                            <label data-i18n="set-general-date">日期格式</label>
                            <select id="general-date" class="form-input">
                                <option value="YYYY-MM-DD">2026-05-09</option>
                                <option value="DD/MM/YYYY">09/05/2026</option>
                                <option value="MM/DD/YYYY">05/09/2026</option>
                                <option value="DD-MM-YYYY">09-05-2026</option>
                                <option value="YYYY/MM/DD">2026/05/09</option>
                            </select>
                            <div class="form-hint" data-i18n="set-general-date-hint">显示在历史 / 异常 / 对账 / 导出 CSV</div>
                        </div>
                        <div class="form-row form-row-inline">
                            <label data-i18n="set-general-number">数字格式</label>
                            <select id="general-number" class="form-input">
                                <option value="comma_dot">1,234,567.89</option>
                                <option value="dot_comma">1.234.567,89</option>
                                <option value="space_dot">1 234 567.89</option>
                                <option value="space_comma">1 234 567,89</option>
                            </select>
                            <div class="form-hint" data-i18n="set-general-number-hint">金额千分位 · 小数点</div>
                        </div>
                        <div class="form-actions">
                            <button class="btn btn-primary" id="btn-save-general" data-i18n="set-save">保存修改</button>
                            <span class="form-msg" id="general-save-msg"></span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- v118.28.8 · Pearnly 访问日志(owner 可见 · 客户审计 Pearnly 内部员工的访问) -->
            <div class="settings-pane" data-pane="access-log">
                <div class="card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="set-access-log-title">Pearnly 访问日志</div>
                        <div class="section-sub" data-i18n="set-access-log-sub">Pearnly 内部员工对您账号的所有操作记录(对齐 Xero / QuickBooks Audit log)</div>
                    </div>
                    <div class="access-log-toolbar">
                        <input type="text" class="form-input" id="access-log-search" data-i18n-placeholder="set-access-log-search-ph" style="max-width:320px;">
                        <button class="btn btn-ghost" type="button" id="access-log-csv-btn">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px;margin-right:4px;">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                <polyline points="7 10 12 15 17 10"/>
                                <line x1="12" y1="15" x2="12" y2="3"/>
                            </svg>
                            <span data-i18n="set-access-log-csv">导出 CSV</span>
                        </button>
                    </div>
                    <div class="access-log-table" id="access-log-table"></div>
                    <div class="access-log-pager" id="access-log-pager"></div>
                </div>
            </div>

            <!-- Tab 8 · 联系我们 -->
            <div class="settings-pane" data-pane="about">
                <div class="card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="settings-about">联系我们</div>
                    </div>
                    <div class="about-desc" data-i18n="about-desc">需要帮助、升级账号或反馈问题 · 欢迎联系我们</div>
                    <div class="contact-grid" id="settings-contact-grid"></div>
                </div>
            </div>
        </div>
        <!-- /settings-layout -->
`,e.dataset.wbInjected="1";try{const a=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",n=window.I18N;n&&n[a]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const l=s.getAttribute("data-i18n");n[a][l]&&(s.textContent=n[a][l])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const l=s.getAttribute("data-i18n-placeholder");n[a][l]&&(s.placeholder=n[a][l])}))}catch{}}})();(function(){const e=document.getElementById("page-automation");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
        <div class="page-head-clean">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M13 2L3 14h9l-1 8 10-12h-9z"/>
                </svg>
            </div>
            <div class="page-head-text">
                <div class="page-head-title" data-i18n="auto-title">自动化</div>
                <div class="page-head-sub" data-i18n="auto-sub">让 Pearnly 替你完成重复性工作</div>
            </div>
        </div>

        <!-- Free 用户占位 -->
        <div class="card" id="automation-free-block" style="display:none;">
            <div class="coming-soon">
                <svg class="cs-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M26 4L10 26h12l-2 18 16-22H24z"/>
                </svg>
                <div class="cs-title" data-i18n="cs-auto-title">全自动处理流水线</div>
                <div class="cs-desc" data-i18n="cs-no-access">该功能暂未开放 · 如有需要请联系我们</div>
            </div>
        </div>

        <!-- Plus/Pro 用户主界面 · 左侧子菜单 + 右侧内容区(v0.10) -->
        <div id="automation-main" style="display:none;">
            <div class="auto-layout">
                <!-- 左侧子菜单 -->
                <aside class="auto-sidebar">
                    <div class="auto-sidebar-inner">
                        <button class="auto-nav-item active" data-auto-tab="erp">
                            <span class="auto-nav-icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M4 7h16M4 12h16M4 17h10"/>
                                    <path d="M18 17l3 3m0 0l-3 3m3-3h-5"/>
                                </svg>
                            </span>
                            <span class="auto-nav-label" data-i18n="auto-erp-title">ERP 对接</span>
                            <span class="auto-nav-badge" id="auto-nav-erp-badge"></span>
                        </button>

                        <button class="auto-nav-item" data-auto-tab="bank">
                            <span class="auto-nav-icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M3 10l9-6 9 6"/>
                                    <path d="M5 10v9M12 10v9M19 10v9"/>
                                    <path d="M3 20h18"/>
                                </svg>
                            </span>
                            <span class="auto-nav-label" data-i18n="auto-bank-title">银行对账</span>
                            <span class="auto-nav-badge" id="auto-nav-bank-badge"></span>
                        </button>

                        <button class="auto-nav-item" data-auto-tab="email">
                            <span class="auto-nav-icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                    <rect x="3" y="5" width="18" height="14" rx="2"/>
                                    <path d="M3 7l9 6 9-6"/>
                                </svg>
                            </span>
                            <span class="auto-nav-label" data-i18n="auto-email-title">邮箱抓取</span>
                        </button>

                        <button class="auto-nav-item" data-auto-tab="folder">
                            <span class="auto-nav-icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M3 7a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z"/>
                                </svg>
                            </span>
                            <span class="auto-nav-label" data-i18n="auto-folder-title">文件夹监听</span>
                        </button>

                        <button class="auto-nav-item" data-auto-tab="linebot">
                            <span class="auto-nav-icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M12 3C6.5 3 2 6.6 2 11c0 2.5 1.5 4.8 3.9 6.3-.2.8-.7 2.5-.8 2.9 0 0-.1.2.1.3s.3 0 .3 0c.3 0 3.2-2.1 3.8-2.5.9.1 1.8.2 2.7.2 5.5 0 10-3.6 10-8S17.5 3 12 3z"/>
                                </svg>
                            </span>
                            <span class="auto-nav-label" data-i18n="auto-linebot-title">LINE Bot</span>
                            <span class="auto-nav-badge" id="auto-nav-linebot-badge"></span>
                        </button>

                        <button class="auto-nav-item" data-auto-tab="alert" data-auto-soon="1">
                            <span class="auto-nav-icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
                                    <path d="M10 21a2 2 0 0 0 4 0"/>
                                </svg>
                            </span>
                            <span class="auto-nav-label" data-i18n="auto-alert-title">智能提醒</span>
                        </button>
                    </div>
                </aside>

                <!-- 右侧内容区 -->
                <main class="auto-content">

                    <!-- Tab: ERP 对接 -->
                    <div class="auto-panel active" data-auto-panel="erp">
                        <div class="auto-panel-head">
                            <div>
                                <div class="auto-panel-title" data-i18n="auto-erp-title">ERP 对接</div>
                                <div class="auto-panel-desc" data-i18n="auto-erp-desc">把识别结果自动推送到你的 ERP / 会计系统</div>
                            </div>
                            <span id="erp-status-summary" class="auto-status-pill" data-i18n="auto-status-loading">加载中…</span>
                        </div>

                        <!-- v118.34.4 (Zihao 2026-05-19 拍板) · ERP 三级 tab 拆分:
                             连接 / 推送日志 / 字段映射。
                             之前:连接 + 推送日志 挤在同一 subpanel · filter chips
                             和日志 row 被压缩看不清。现在:推送日志独占 subpanel·
                             全宽全屏 · 没有侧栏挤压。
                             ⚠ data-erp-subpanel="connect" 的 panel 同时也是
                             "auto-erp-subtab-connect" data-i18n key 的归宿,旧
                             分类不动 · 仅拆出新的 "logs" tab。
                        -->
                        <!-- v118.34.19 (A4) · 「推送日志」subtab 已移到集成主页面顶部 tab · 这里仅留 连接 / 字段映射 -->
                        <div class="erp-subtabs" role="tablist">
                            <button class="erp-subtab active" type="button" data-erp-subtab="connect" data-i18n="auto-erp-subtab-connect-only">连接</button>
                            <button class="erp-subtab" type="button" data-erp-subtab="mappings" data-i18n="auto-erp-subtab-mappings">字段映射</button>
                        </div>

                        <!-- 子面板 1:连接(纯卡片 · 不含日志、不含 today-stats · v118.34.5) -->
                        <div class="erp-subpanel active" data-erp-subpanel="connect">
                            <!-- P1b · 全局「ERP 自动处理方式」(账户级 · 对所有 ERP 端点统一生效 ·
                                 不是单个端点的设置 · 故放在卡片上方而非某张卡片内)。 -->
                            <div class="erp-global-mode" style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:0 0 16px;padding:12px 14px;background:#fff;border:1px solid #e8e8e3;border-radius:8px;">
                                <span data-i18n="pref-erp-mode-title" style="font-weight:600;font-size:13px;">ERP 自动处理方式</span>
                                <select id="erp-global-push-mode" class="folder-interval-select">
                                    <option value="smart" data-i18n="pref-erp-mode-smart">智能分拣(推荐)</option>
                                    <option value="fixed" data-i18n="pref-erp-mode-fixed">固定当前账套</option>
                                    <option value="ocr_only" data-i18n="pref-erp-mode-ocr">只识别不推送</option>
                                </select>
                                <span data-i18n="pref-erp-mode-desc" style="font-size:12px;color:#6B7280;flex:1 1 200px;">上传识别后,系统如何把发票推送到 ERP</span>
                            </div>
                            <!-- v118.27.4 · ERP 系统连接卡片区(Xero · MR.ERP) -->
                            <div class="erp-connect-cards" id="erp-connect-cards">
                                <!-- IIFE 渲染 Xero 卡片 + MR.ERP 卡片 -->
                            </div>

                            <div id="erp-endpoints-list"></div>
                            <button class="btn btn-primary btn-add-endpoint" id="btn-add-endpoint">
                                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M8 3v10M3 8h10"/></svg>
                                <span data-i18n="auto-erp-add">新增端点</span>
                            </button>

                            <!-- v118.34.35 · 看推送日志按钮放到底部 · 将来加新 ERP 卡片时按钮自然在最下 -->
                            <div class="erp-connect-logs-link" style="text-align:left;margin:16px 0 0;">
                                <button type="button" class="int-btn-view-logs" data-int-action="view-logs" data-i18n="int-btn-view-logs">看推送日志 →</button>
                            </div>
                        </div>

                        <!-- v118.34.19 (A4) · subpanel="logs" 已删除 · 内容搬到
                             集成主页面顶部 tab 2(全宽全屏)· erp-logs-section /
                             erp-today-stats 等 DOM 节点搬过去后这里清空 ·
                             home.js 的 loadErpLogs() 等通过 id 仍然找得到 ·
                             不需要改. -->

                        <!-- 子面板 2:字段映射(老板可写 / 员工只读 · IIFE 渲染) -->
                        <div class="erp-subpanel" data-erp-subpanel="mappings">
                            <div class="erp-map-sub-desc" data-i18n="erp-map-sub">把 Pearnly 的客户 / 科目 / 税码 翻译成你 ERP 系统的代码 · 后续推送 ERP 时会自动用这里的映射</div>
                            <div class="erp-map-subtabs" id="erp-map-subtabs" role="tablist">
                                <button class="erp-map-subtab active" type="button" data-erp-subtab="clients" data-i18n="erp-map-subtab-clients">客户映射</button>
                                <button class="erp-map-subtab erp-map-subtab-advanced" type="button" data-erp-subtab="accounts" data-i18n="erp-map-subtab-accounts">科目映射</button>
                                <button class="erp-map-subtab erp-map-subtab-advanced" type="button" data-erp-subtab="taxes" data-i18n="erp-map-subtab-taxes">税码映射</button>
                                <button class="erp-map-subtab erp-map-subtab-advanced" type="button" data-erp-subtab="products" data-i18n="erp-map-subtab-products">商品映射</button>
                                <button class="erp-map-show-advanced-btn" type="button" id="erp-map-show-advanced-btn" aria-pressed="false">
                                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                                        <line class="erp-map-adv-plus-h" x1="5" y1="10" x2="15" y2="10"/>
                                        <line class="erp-map-adv-plus-v" x1="10" y1="5" x2="10" y2="15"/>
                                    </svg>
                                    <span class="erp-map-adv-btn-label" data-i18n="erp-map-show-advanced">显示高级映射</span>
                                </button>
                            </div>
                            <div class="erp-map-pane-wrap" id="erp-map-pane-wrap"></div>
                        </div>
                    </div>

                    <!-- Tab: 银行对账 (v0.18 · M10) -->
                    <div class="auto-panel" data-auto-panel="bank">
                        <div class="auto-panel-head">
                            <div>
                                <div class="auto-panel-title" data-i18n="auto-bank-title">银行对账</div>
                                <div class="auto-panel-desc" data-i18n="bank-panel-desc">上传银行对账单 PDF · 自动和 Pearnly 里的发票做智能匹配 · 3 小时的月末对账压缩到 15 分钟</div>
                            </div>
                            <span id="bank-status-summary" class="auto-status-pill" data-i18n="auto-status-loading">加载中…</span>
                        </div>

                        <!-- 上传区(v118.26.1 · 批量上传) -->
                        <div class="bank-upload-card">
                            <div class="bank-upload-row">
                                <div class="bank-upload-icon">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M12 3v12M6 9l6-6 6 6"/>
                                        <path d="M5 21h14"/>
                                    </svg>
                                </div>
                                <div class="bank-upload-text">
                                    <div class="bank-upload-title" data-i18n="bank-upload-title">上传银行对账单</div>
                                    <div class="bank-upload-sub" data-i18n="bank-upload-sub-batch">支持多选 · KBank · SCB · BBL · 其他银行也能解析大部分流水</div>
                                </div>
                                <label for="bank-file-input" class="btn btn-primary bank-upload-btn">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M8 3v10M3 8h10"/></svg>
                                    <span data-i18n="bank-btn-upload-batch">选择文件(可多选)</span>
                                </label>
                                <input type="file" id="bank-file-input" accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.xlsx,.xls,.xlsm,.csv,.tsv,.docx,.doc" multiple style="display:none">
                            </div>
                            <!-- 单文件遗留 progress / error · 仅在仅传 1 张时降级显示 · 多文件走下方队列 -->
                            <div id="bank-upload-progress" class="bank-upload-progress" style="display:none">
                                <div class="bank-upload-spinner"></div>
                                <span data-i18n="bank-upload-parsing">正在解析对账单…</span>
                            </div>
                            <div id="bank-upload-error" class="bank-upload-error" style="display:none"></div>
                            <!-- v118.26.1 · 批量上传队列(每文件 1 行 · 进度 + 状态 + 重试) -->
                            <div id="bank-upload-queue" class="bank-upload-queue" style="display:none">
                                <div class="bank-upload-queue-head">
                                    <span class="bank-upload-queue-title" data-i18n="bank-queue-title">上传队列</span>
                                    <span class="bank-upload-queue-summary" id="bank-upload-queue-summary"></span>
                                    <button class="btn btn-ghost btn-tiny" id="btn-bank-queue-clear-done" type="button">
                                        <span data-i18n="bank-queue-clear-done">清除已完成</span>
                                    </button>
                                </div>
                                <div id="bank-upload-queue-list" class="bank-upload-queue-list"></div>
                            </div>
                        </div>

                        <!-- 会话列表(最近上传的对账单)-->
                        <div class="bank-sessions-section">
                            <div class="bank-section-head">
                                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M2 4h12M2 8h12M2 12h8"/>
                                </svg>
                                <span data-i18n="bank-sessions-title">最近对账</span>
                                <!-- v118.26.1.1 · 筛选 chip -->
                                <div class="bank-sessions-filters">
                                    <button class="bank-sessions-chip active" data-sess-filter="all" data-i18n="bank-sess-filter-all">全部</button>
                                    <button class="bank-sessions-chip" data-sess-filter="parsed" data-i18n="bank-sess-filter-parsed">已解析</button>
                                    <button class="bank-sessions-chip" data-sess-filter="failed" data-i18n="bank-sess-filter-failed">失败</button>
                                </div>
                            </div>
                            <div id="bank-sessions-list" class="bank-sessions-list">
                                <div class="bank-empty" data-i18n="bank-sessions-loading">加载中…</div>
                            </div>
                        </div>

                        <!-- 会话详情(选中一个会话后出现)-->
                        <div id="bank-detail" class="bank-detail" style="display:none">
                            <div class="bank-detail-head">
                                <button class="btn btn-ghost btn-small" id="btn-bank-back">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10 12L6 8l4-4"/></svg>
                                    <span data-i18n="bank-btn-back">返回列表</span>
                                </button>
                                <div class="bank-detail-title" id="bank-detail-title"></div>
                                <!-- v118.26.2 · 客户徽章 · 显示 session 当前所属客户(老板可改 · 员工只读) -->
                                <button class="bank-client-badge" id="bank-client-badge" type="button" style="display:none">
                                    <span class="bank-client-badge-dot" id="bank-client-badge-dot"></span>
                                    <span class="bank-client-badge-name" id="bank-client-badge-name">-</span>
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" id="bank-client-badge-caret"><path d="M4 6l4 4 4-4"/></svg>
                                </button>
                                <button class="btn btn-ghost btn-small bank-btn-danger" id="btn-bank-delete" title="">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/></svg>
                                </button>
                            </div>

                            <!-- 会话元信息卡 -->
                            <div class="bank-detail-meta">
                                <div class="bank-meta-item">
                                    <div class="bank-meta-label" data-i18n="bank-meta-period">对账周期</div>
                                    <div class="bank-meta-value" id="bank-meta-period">-</div>
                                </div>
                                <div class="bank-meta-item">
                                    <div class="bank-meta-label" data-i18n="bank-meta-opening">期初余额</div>
                                    <div class="bank-meta-value tabular-nums" id="bank-meta-opening">-</div>
                                </div>
                                <div class="bank-meta-item">
                                    <div class="bank-meta-label" data-i18n="bank-meta-inflow">入账</div>
                                    <div class="bank-meta-value tabular-nums bank-in" id="bank-meta-inflow">-</div>
                                </div>
                                <div class="bank-meta-item">
                                    <div class="bank-meta-label" data-i18n="bank-meta-outflow">出账</div>
                                    <div class="bank-meta-value tabular-nums bank-out" id="bank-meta-outflow">-</div>
                                </div>
                                <div class="bank-meta-item">
                                    <div class="bank-meta-label" data-i18n="bank-meta-closing">期末余额</div>
                                    <div class="bank-meta-value tabular-nums" id="bank-meta-closing">-</div>
                                </div>
                            </div>

                            <!-- 匹配统计 + 触发按钮 -->
                            <div class="bank-match-bar">
                                <div class="bank-match-stats" id="bank-match-stats">
                                    <span class="bank-stat-chip" data-kind="total">
                                        <span id="bank-stat-total">0</span> <span data-i18n="bank-stat-total">流水</span>
                                    </span>
                                    <span class="bank-stat-chip bank-stat-matched" data-kind="matched">
                                        <span id="bank-stat-matched">0</span> <span data-i18n="bank-stat-matched">已匹配</span>
                                    </span>
                                    <span class="bank-stat-chip bank-stat-suggested" data-kind="suggested">
                                        <span id="bank-stat-suggested">0</span> <span data-i18n="bank-stat-suggested">疑似</span>
                                    </span>
                                    <span class="bank-stat-chip bank-stat-unmatched" data-kind="unmatched">
                                        <span id="bank-stat-unmatched">0</span> <span data-i18n="bank-stat-unmatched">未匹配</span>
                                    </span>
                                </div>
                                <button class="btn btn-primary btn-small" id="btn-bank-run-match">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8a6 6 0 0111-3.5M14 8a6 6 0 01-11 3.5M14 3v3h-3M2 13v-3h3"/></svg>
                                    <span data-i18n="bank-btn-run-match">开始匹配</span>
                                </button>
                            </div>

                            <!-- 流水筛选 -->
                            <div class="bank-filter-bar">
                                <button class="bank-filter-btn active" data-bank-filter="all" data-i18n="bank-filter-all">全部</button>
                                <button class="bank-filter-btn" data-bank-filter="matched" data-i18n="bank-filter-matched">已匹配</button>
                                <button class="bank-filter-btn" data-bank-filter="suggested" data-i18n="bank-filter-suggested">疑似</button>
                                <button class="bank-filter-btn" data-bank-filter="unmatched" data-i18n="bank-filter-unmatched">未匹配</button>
                            </div>

                            <!-- v118.26.2 · 右半屏对账面板 · 流水表 + 候选发票并排 -->
                            <div class="bank-detail-body" id="bank-detail-body">
                                <!-- 左:流水表 -->
                                <div class="bank-recon-left">
                                    <div class="bank-tx-table-wrap">
                                        <table class="bank-tx-table">
                                            <thead>
                                                <tr>
                                                    <th data-i18n="bank-col-date">日期</th>
                                                    <th data-i18n="bank-col-desc">摘要</th>
                                                    <th class="bank-col-amt" data-i18n="bank-col-amount">金额</th>
                                                    <th data-i18n="bank-col-match">匹配状态</th>
                                                </tr>
                                            </thead>
                                            <tbody id="bank-tx-tbody">
                                                <tr><td colspan="4" class="bank-empty" data-i18n="bank-tx-loading">加载流水…</td></tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                                <!-- 右:候选 pane(默认空态 · 选中流水后渲染) -->
                                <aside class="bank-recon-right" id="bank-recon-right">
                                    <div class="bank-cand-pane" id="bank-cand-pane">
                                        <div class="bank-cand-pane-head">
                                            <div>
                                                <div class="bank-cand-pane-title" id="bank-cand-pane-title" data-i18n="bank-cand-pane-empty-title">点左侧任意一笔流水查看候选发票</div>
                                                <div class="bank-cand-pane-sub" id="bank-cand-pane-sub" data-i18n="bank-cand-pane-empty-sub">系统按金额 / 日期 / 商户名打分推荐</div>
                                            </div>
                                            <button class="modal-close" id="btn-bank-cand-pane-close" aria-label="close" style="display:none">
                                                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 3l10 10M13 3L3 13"/></svg>
                                            </button>
                                        </div>
                                        <div class="bank-cand-pane-body" id="bank-cand-pane-body">
                                            <div class="bank-cand-pane-empty">
                                                <svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
                                                    <rect x="14" y="10" width="36" height="44" rx="3"/>
                                                    <path d="M22 22h20M22 30h20M22 38h12"/>
                                                </svg>
                                                <div data-i18n="bank-cand-pane-empty-hint">在左边选一笔流水 · 系统会列出最有可能的发票</div>
                                            </div>
                                        </div>
                                        <div class="bank-cand-pane-foot" id="bank-cand-pane-foot" style="display:none">
                                            <button class="btn btn-ghost btn-small" id="btn-bank-cand-ignore-pane">
                                                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8h10"/></svg>
                                                <span data-i18n="bank-cand-ignore">忽略此条流水</span>
                                            </button>
                                        </div>
                                    </div>
                                </aside>
                            </div>
                        </div>
                    </div>

                    <!-- Tab: 邮箱抓取 (v0.17 · M6 · v93 在 Vultr 复活) -->
                    <div class="auto-panel" data-auto-panel="email">
                        <!-- v93 · 已迁 Vultr · 启用完整 UI -->
                        <div id="email-full-ui">
                        <div class="auto-panel-head">
                            <div>
                                <div class="auto-panel-title" data-i18n="auto-email-title">邮箱抓取</div>
                                <div class="auto-panel-desc" data-i18n="email-panel-desc">绑定邮箱后 · Pearnly 自动扫收件箱 · PDF 发票附件自动识别入库</div>
                            </div>
                            <span id="email-status-summary" class="auto-status-pill" data-i18n="auto-status-loading">加载中…</span>
                        </div>

                        <!-- 未绑定 · 引导卡片 -->
                        <div id="email-empty" class="email-empty-card" style="display:none;">
                            <div class="email-empty-icon">
                                <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                    <rect x="6" y="12" width="36" height="28" rx="3"/>
                                    <path d="M6 15l18 12 18-12"/>
                                </svg>
                            </div>
                            <div class="email-empty-title" data-i18n="email-empty-title">还没绑定邮箱</div>
                            <div class="email-empty-desc" data-i18n="email-empty-desc">绑定后 · Pearnly 会自动扫未读邮件 · 自动识别 PDF 发票附件</div>
                            <button class="btn btn-primary" id="btn-email-bind">
                                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M8 3v10M3 8h10"/></svg>
                                <span data-i18n="email-bind-btn">绑定邮箱</span>
                            </button>
                        </div>

                        <!-- 已绑定 · 账号卡片 -->
                        <div id="email-account-card" class="email-account-card" style="display:none;">
                            <div class="email-account-head">
                                <div class="email-account-icon">
                                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                        <rect x="2.5" y="5" width="15" height="11" rx="1.5"/>
                                        <path d="M2.5 6.5l7.5 5 7.5-5"/>
                                    </svg>
                                </div>
                                <div class="email-account-info">
                                    <div class="email-account-addr" id="email-account-addr">-</div>
                                    <div class="email-account-meta">
                                        <span id="email-account-host">-</span>
                                        <span class="email-meta-sep">·</span>
                                        <span id="email-account-last" data-i18n="email-last-never">从未抓取</span>
                                    </div>
                                </div>
                                <label class="toggle-switch" title="" id="email-enabled-wrap">
                                    <input type="checkbox" id="email-enabled-toggle">
                                    <span class="toggle-slider"></span>
                                </label>
                            </div>

                            <!-- 上次错误(若有)-->
                            <div id="email-last-error" class="email-last-error" style="display:none;"></div>

                            <div class="email-account-actions">
                                <button class="btn btn-primary btn-small" id="btn-email-trigger">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8a5 5 0 119 3M12 13V9h-4"/></svg>
                                    <span data-i18n="email-btn-trigger">立即抓取</span>
                                </button>
                                <button class="btn btn-ghost btn-small" id="btn-email-edit">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M11 3l2 2-7 7H4v-2l7-7zM10 4l2 2"/></svg>
                                    <span data-i18n="email-btn-edit">修改配置</span>
                                </button>
                                <div style="flex:1"></div>
                                <button class="btn btn-ghost btn-small email-btn-danger" id="btn-email-unbind">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/></svg>
                                    <span data-i18n="email-btn-unbind">解绑邮箱</span>
                                </button>
                            </div>
                        </div>

                        <!-- 抓取日志折叠区 -->
                        <details class="erp-logs-section" id="email-logs-section" style="display:none;">
                            <summary class="erp-logs-head">
                                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                    <circle cx="8" cy="8" r="6"/><path d="M8 5v3l2 1"/>
                                </svg>
                                <span data-i18n="email-logs-title">抓取日志</span>
                                <span class="erp-logs-today-stats" id="email-logs-hint"></span>
                            </summary>
                            <div class="erp-logs-toolbar">
                                <div></div>
                                <button class="btn btn-ghost btn-tiny" id="btn-email-refresh-logs" title="">
                                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M11.5 7a4.5 4.5 0 11-1.3-3.2M12 2v3h-3"/></svg>
                                </button>
                            </div>
                            <div id="email-logs-list" class="erp-logs-list">
                                <div class="erp-logs-empty" data-i18n="erp-logs-loading">加载中…</div>
                            </div>
                        </details>
                        </div><!-- /#email-full-ui -->
                    </div>

                    <!-- Tab: 文件夹监听 (v95 · 浏览器 File System Access API · 0 费用网页端方案) -->
                    <div class="auto-panel" data-auto-panel="folder">
                        <div class="auto-panel-head">
                            <div>
                                <div class="auto-panel-title" data-i18n="auto-folder-title">文件夹监听</div>
                                <div class="auto-panel-desc" data-i18n="folder-panel-desc">选一个本地文件夹 · Pearnly 自动扫描里面的 PDF 发票</div>
                            </div>
                            <span id="folder-status-summary" class="auto-status-pill" data-i18n="folder-status-init">初始化中…</span>
                        </div>

                        <!-- 浏览器不支持(Firefox / Safari) -->
                        <div id="folder-unsupported" class="folder-card folder-unsupported" style="display:none;">
                            <div class="folder-unsupported-icon">
                                <svg width="64" height="64" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                    <circle cx="24" cy="24" r="20"/>
                                    <path d="M24 16v10M24 32h.01"/>
                                </svg>
                            </div>
                            <div class="folder-unsupported-title" data-i18n="folder-unsupported-title">你的浏览器不支持本功能</div>
                            <div class="folder-unsupported-desc" data-i18n="folder-unsupported-desc">文件夹监听需要 Chrome 或 Edge 浏览器(Firefox / Safari 暂不支持)</div>
                            <div class="folder-alt-section">
                                <div class="folder-alt-title" data-i18n="folder-alt-title">替代方案</div>
                                <button class="btn btn-ghost folder-alt-btn" data-tab-jump="email">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="12" height="10" rx="1.5"/><path d="m2 4 6 4 6-4"/></svg>
                                    <span data-i18n="folder-alt-email">改用邮件抓取(任何浏览器)</span>
                                </button>
                                <button class="btn btn-ghost folder-alt-btn" data-tab-jump="upload">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 12V3M5 6l3-3 3 3"/><path d="M3 13h10"/></svg>
                                    <span data-i18n="folder-alt-upload">改用拖拽上传</span>
                                </button>
                            </div>
                        </div>

                        <!-- 还没选文件夹(支持的浏览器 · 未配置态) -->
                        <div id="folder-empty" class="folder-card folder-empty" style="display:none;">
                            <div class="folder-empty-icon">
                                <svg width="64" height="64" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M6 14a4 4 0 0 1 4-4h10l4 6h14a4 4 0 0 1 4 4v16a4 4 0 0 1-4 4H10a4 4 0 0 1-4-4V14z"/>
                                </svg>
                            </div>
                            <div class="folder-empty-title" data-i18n="folder-empty-title">还没选监听文件夹</div>
                            <div class="folder-empty-desc" data-i18n="folder-empty-desc">选一个本地文件夹后 · Pearnly 会扫描里面的 PDF / 图片发票 · 自动识别入库</div>
                            <button class="btn btn-primary" id="btn-folder-pick">
                                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M8 3v10M3 8h10"/></svg>
                                <span data-i18n="folder-pick-btn">选择监听文件夹</span>
                            </button>
                            <div class="folder-info-bar">
                                <span class="folder-info-chip" tabindex="0">
                                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.5"/><path d="M8 5v3.5M8 11h.01"/></svg>
                                    <span data-i18n="folder-info-keep-open-short">需保持页面打开</span>
                                    <span class="folder-info-tooltip" data-i18n="folder-warn-keep-open">本功能需要保持本页面打开 · 浏览器关闭 / 电脑睡眠后停止扫描 · 重新打开会自动继续</span>
                                </span>
                                <button type="button" class="folder-info-chip folder-info-chip-link" data-tab-jump="email">
                                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="12" height="10" rx="1.5"/><path d="m2 4 6 4 6-4"/></svg>
                                    <span data-i18n="folder-info-email-short">需 7×24 用邮件抓取</span>
                                    <span class="folder-info-tooltip" data-i18n="folder-need-247-tip">需要 7×24 后台运行?推荐改用「邮件抓取」· 把发票转发到绑定邮箱即可 · 任何浏览器都不需要打开</span>
                                </button>
                            </div>
                        </div>

                        <!-- 已配置(主面板) -->
                        <div id="folder-active" class="folder-active" style="display:none;">
                            <!-- 配置卡片 -->
                            <div class="folder-card folder-config-card">
                                <div class="folder-config-head">
                                    <div class="folder-config-info">
                                        <div class="folder-config-icon">
                                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z"/></svg>
                                        </div>
                                        <div>
                                            <div class="folder-config-path" id="folder-config-path">-</div>
                                            <div class="folder-config-meta">
                                                <span id="folder-status-pulse" class="folder-status-pulse"></span>
                                                <span id="folder-status-text" data-i18n="folder-status-running">正在监听</span>
                                                <span> · </span>
                                                <span data-i18n="folder-scan-every">每</span>
                                                <select id="folder-interval-select" class="folder-interval-select">
                                                    <option value="30" data-i18n="folder-interval-30">30 秒</option>
                                                    <option value="60" data-i18n="folder-interval-60" selected>1 分钟</option>
                                                    <option value="300" data-i18n="folder-interval-300">5 分钟</option>
                                                </select>
                                                <span data-i18n="folder-scan-once">扫一次</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="folder-config-actions">
                                        <button class="btn btn-ghost btn-small" id="btn-folder-pause">
                                            <svg viewBox="0 0 16 16" fill="currentColor"><rect x="4" y="3" width="3" height="10"/><rect x="9" y="3" width="3" height="10"/></svg>
                                            <span data-i18n="folder-btn-pause">暂停</span>
                                        </button>
                                        <button class="btn btn-ghost btn-small" id="btn-folder-resume" style="display:none;">
                                            <svg viewBox="0 0 16 16" fill="currentColor"><path d="M4 3l9 5-9 5z"/></svg>
                                            <span data-i18n="folder-btn-resume">恢复</span>
                                        </button>
                                        <button class="btn btn-ghost btn-small" id="btn-folder-scan-now">
                                            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8a6 6 0 0 1 6-6 6.5 6.5 0 0 1 4.5 1.83L14 5"/><path d="M14 2v3h-3"/><path d="M14 8a6 6 0 0 1-6 6 6.5 6.5 0 0 1-4.5-1.83L2 11"/><path d="M2 14v-3h3"/></svg>
                                            <span data-i18n="folder-btn-scan-now">立即扫描</span>
                                        </button>
                                        <button class="btn btn-ghost btn-small folder-btn-danger" id="btn-folder-remove">
                                            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 5h10M6 5V3h4v2M5 5v8a1 1 0 0 0 1 1h4a1 1 0 0 0 1-1V5"/></svg>
                                            <span data-i18n="folder-btn-remove">移除</span>
                                        </button>
                                    </div>
                                </div>
                                <div class="folder-stats">
                                    <div class="folder-stat">
                                        <div class="folder-stat-label" data-i18n="folder-stat-last-scan">上次扫描</div>
                                        <div class="folder-stat-value" id="folder-stat-last">-</div>
                                    </div>
                                    <div class="folder-stat">
                                        <div class="folder-stat-label" data-i18n="folder-stat-processed">累计处理</div>
                                        <div class="folder-stat-value" id="folder-stat-processed">0</div>
                                    </div>
                                    <div class="folder-stat">
                                        <div class="folder-stat-label" data-i18n="folder-stat-failed">失败</div>
                                        <div class="folder-stat-value" id="folder-stat-failed">0</div>
                                    </div>
                                    <div class="folder-stat">
                                        <div class="folder-stat-label" data-i18n="folder-stat-queue">队列中</div>
                                        <div class="folder-stat-value" id="folder-stat-queue">0</div>
                                    </div>
                                </div>
                                <div class="folder-warn-row" id="folder-keep-open-warn">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.5"/><path d="M8 5v3.5M8 11h.01"/></svg>
                                    <span data-i18n="folder-warn-keep-open">本功能需要保持此页面打开 · 关闭后停止扫描</span>
                                </div>
                                <!-- v118.24 · 子文件夹递归提示 -->
                                <div class="folder-warn-row folder-info-soft">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M2 5a1.5 1.5 0 0 1 1.5-1.5h3l1.5 2h4.5A1.5 1.5 0 0 1 14 7v5a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 2 12V5z"/><path d="M5 8.5h6"/></svg>
                                    <span data-i18n="folder-recursive-info">已自动扫子文件夹</span>
                                </div>
                            </div>

                            <!-- 最近处理 -->
                            <div class="folder-card folder-recent-card">
                                <div class="folder-recent-head">
                                    <div class="folder-recent-title" data-i18n="folder-recent-title">最近处理</div>
                                    <button class="btn btn-tiny" id="btn-folder-clear-recent" data-i18n="folder-clear-recent">清空记录</button>
                                </div>
                                <div id="folder-recent-list" class="folder-recent-list">
                                    <div class="folder-recent-empty" data-i18n="folder-recent-empty">还没处理任何文件</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Tab: LINE Bot(v0.19 · T1) -->
                    <div class="auto-panel" data-auto-panel="linebot">
                        <div class="auto-panel-head">
                            <div>
                                <div class="auto-panel-title" data-i18n="auto-linebot-title">LINE Bot</div>
                                <div class="auto-panel-desc" data-i18n="auto-linebot-desc">把发票拍照发到 LINE · Pearnly 自动识别入账</div>
                            </div>
                            <span id="linebot-status-summary" class="auto-status-pill" data-i18n="auto-status-loading">加载中…</span>
                        </div>

                        <!-- 未绑定态 -->
                        <div id="linebot-unbound" style="display:none;">
                            <div class="card linebot-card">
                                <div class="linebot-steps">
                                    <div class="linebot-step">
                                        <div class="linebot-step-no">1</div>
                                        <div class="linebot-step-body">
                                            <div class="linebot-step-title" data-i18n="linebot-step1-title">加 Bot 为 LINE 好友</div>
                                            <div class="linebot-step-desc" data-i18n="linebot-step1-desc">扫下面 QR 码 · 或在 LINE 搜索 Bot ID</div>
                                            <div class="linebot-qr-wrap">
                                                <div id="linebot-qr" class="linebot-qr-box"></div>
                                                <div class="linebot-bot-id">
                                                    <span data-i18n="linebot-bot-id-label">Bot ID</span>:
                                                    <span id="linebot-bot-id" class="linebot-bot-id-val">—</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="linebot-step">
                                        <div class="linebot-step-no">2</div>
                                        <div class="linebot-step-body">
                                            <div class="linebot-step-title" data-i18n="linebot-step2-title">把这 6 位数字发给 Bot</div>
                                            <div class="linebot-step-desc" data-i18n="linebot-step2-desc">10 分钟内有效 · 发送后自动绑定</div>
                                            <div class="linebot-code-wrap">
                                                <div id="linebot-code" class="linebot-code">——————</div>
                                                <button id="linebot-code-refresh" class="btn btn-ghost btn-tiny">
                                                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M11.5 7a4.5 4.5 0 11-1.3-3.2M12 2v3h-3"/></svg>
                                                    <span data-i18n="linebot-code-refresh">换一个</span>
                                                </button>
                                            </div>
                                            <div id="linebot-code-expires" class="linebot-code-expires"></div>
                                        </div>
                                    </div>

                                    <div class="linebot-step">
                                        <div class="linebot-step-no">3</div>
                                        <div class="linebot-step-body">
                                            <div class="linebot-step-title" data-i18n="linebot-step3-title">等待绑定完成</div>
                                            <div class="linebot-step-desc" data-i18n="linebot-step3-desc">发送成功后 · 这里会自动变为「已绑定」</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- 已绑定态 -->
                        <div id="linebot-bound" style="display:none;">
                            <div class="card linebot-bound-card">
                                <div class="linebot-bound-head">
                                    <img id="linebot-avatar" class="linebot-avatar" src="" alt="" onerror="this.style.display='none'">
                                    <div class="linebot-bound-info">
                                        <div class="linebot-bound-name" id="linebot-bound-name">—</div>
                                        <div class="linebot-bound-sub">
                                            <span data-i18n="linebot-bound-since">已绑定</span>
                                            <span id="linebot-bound-since">—</span>
                                        </div>
                                    </div>
                                    <div class="linebot-bound-badge">
                                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8l4 4 8-8"/></svg>
                                        <span data-i18n="linebot-bound-tag">已绑定</span>
                                    </div>
                                </div>
                                <div class="linebot-bound-tips">
                                    <div class="linebot-tip-title" data-i18n="linebot-tip-title">你现在可以这样用 👇</div>
                                    <ul class="linebot-tip-list">
                                        <li data-i18n="linebot-tip-1">在 LINE 里把发票照片发给 Bot · 自动识别(功能即将上线)</li>
                                        <li data-i18n="linebot-tip-2">多张发票可一次性发出 · Bot 逐张处理</li>
                                        <li data-i18n="linebot-tip-3">识别完成后 · Bot 自动回复结果</li>
                                    </ul>
                                </div>
                                <div class="linebot-bound-actions">
                                    <button id="linebot-unbind" class="btn btn-ghost">
                                        <span data-i18n="linebot-unbind">解绑 LINE</span>
                                    </button>
                                </div>
                            </div>
                        </div>

                        <!-- 错误态 -->
                        <div id="linebot-error" class="linebot-error" style="display:none;"></div>
                    </div>

                    <!-- Tab: 智能提醒 v118.22.2 · 完整面板 -->
                    <div class="auto-panel" data-auto-panel="alert">
                        <div class="auto-panel-head">
                            <div>
                                <div class="auto-panel-title" data-i18n="auto-alert-title">智能提醒</div>
                                <div class="auto-panel-desc" data-i18n="auto-alert-desc">异常 high 或大额发票发生时 · 自动推送到老板/会计的 LINE</div>
                            </div>
                            <button class="btn btn-primary" id="notif-btn-new">
                                <span data-i18n="notif-btn-new">+ 新建规则</span>
                            </button>
                        </div>

                        <!-- 规则列表 -->
                        <div class="card notif-card">
                            <div class="auto-card-head">
                                <div class="auto-card-title" data-i18n="notif-rules-title">我的规则</div>
                                <span id="notif-rules-count" class="auto-status-pill none">0</span>
                            </div>
                            <div id="notif-rules-empty" class="empty-state" style="display:none;">
                                <div class="empty-icon">
                                    <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M12 16a12 12 0 0 1 24 0c0 14 6 18 6 18H6s6-4 6-18"/>
                                        <path d="M20 42a4 4 0 0 0 8 0"/>
                                    </svg>
                                </div>
                                <div class="empty-title" data-i18n="notif-empty-title">还没有任何提醒规则</div>
                                <div class="empty-desc" data-i18n="notif-empty-desc">点右上角「新建规则」· 选个模板就行 · 老板会立刻在 LINE 收到</div>
                            </div>
                            <div id="notif-rules-list" class="notif-rules-list"></div>
                        </div>

                        <!-- 最近发送 -->
                        <div class="card notif-card">
                            <div class="auto-card-head">
                                <div class="auto-card-title" data-i18n="notif-logs-title">最近推送</div>
                                <button class="btn btn-tiny btn-ghost" id="notif-btn-refresh-logs">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;">
                                        <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/>
                                    </svg>
                                    <span data-i18n="notif-btn-refresh">刷新</span>
                                </button>
                            </div>
                            <div id="notif-logs-list" class="notif-logs-list">
                                <div class="notif-logs-empty" data-i18n="notif-logs-empty">还没推送过任何消息</div>
                            </div>
                        </div>
                    </div>

                </main>
            </div>
        </div>
`,e.dataset.wbInjected="1";try{const a=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",n=window.I18N;n&&n[a]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const l=s.getAttribute("data-i18n");n[a][l]&&(s.textContent=n[a][l])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const l=s.getAttribute("data-i18n-placeholder");n[a][l]&&(s.placeholder=n[a][l])}))}catch{}}})();function $e(e,a){try{return typeof window.t=="function"?window.t(e):a}catch{return a}}function Pe(e){if(e==null||isNaN(e))return"—";try{return String(e).replace(/\B(?=(\d{3})+(?!\d))/g,",")}catch{return String(e)}}function Et(e){if(!e)return"";try{const a=new Date(e).getTime();if(!a)return"";const n=Math.floor((Date.now()-a)/1e3);return n<60?$e("time-just-now","刚刚"):n<3600?Math.floor(n/60)+$e("time-min-ago-suffix"," 分钟前"):n<86400?Math.floor(n/3600)+$e("time-hour-ago-suffix"," 小时前"):Math.floor(n/86400)+$e("time-day-ago-suffix"," 天前")}catch{return""}}async function et(){pt();const e=document.getElementById("dash-kpi-invoices"),a=document.getElementById("dash-kpi-pending"),n=document.getElementById("dash-kpi-exceptions"),s=document.getElementById("dash-kpi-plan"),l=document.getElementById("dash-kpi-plan-sub"),f=document.getElementById("dash-recent-list"),h=document.getElementById("dash-quick-exc-badge");try{const x={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},[o,p,w]=await Promise.all([fetch("/api/me/tenant-usage",{headers:x}).then(N=>N.ok?N.json():null).catch(()=>null),fetch("/api/history?limit=20",{headers:x}).then(N=>N.ok?N.json():null).catch(()=>null),fetch("/api/exceptions/stats?status=pending",{headers:x}).then(N=>N.ok?N.json():null).catch(()=>null)]),g=o&&o.ocr_this_month||0;let B=0;const S=p&&(p.items||p.history||p)||[],I=Array.isArray(S)?S:[];I.forEach(N=>{(N.status==="pending"||N.status==="reviewing")&&B++});const U=w&&(w.total||w.count||w.pending||0)||0;if(e&&(e.textContent=Pe(g)),a&&(a.textContent=Pe(B)),n&&(n.textContent=Pe(U)),h&&(U>0?(h.style.display="",h.textContent=U):h.style.display="none"),s&&o){const N=o.ocr_this_month||0,M=o.quota||0;s.textContent=Pe(N),l&&(l.textContent=M?N+" / "+Pe(M)+" 张":$e("dash-kpi-plan-sub","本月用量"))}if(f)if(I.length===0)f.innerHTML='<div class="dash-recent-empty">'+$e("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>";else{const N=I.slice(0,5).map(M=>{const L=(M.invoice_no||M.filename||M.id||"").toString(),z=(M.supplier_name||M.buyer_name||M.client_name||M.notes||"").toString(),V=Et(M.created_at||M.upload_time||M.date),W=P=>String(P).replace(/[&<>"']/g,u=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[u]);return'<div class="dash-recent-row"><span class="dash-recent-key" title="'+W(L)+'">'+W(L)+'</span><span class="dash-recent-mid" title="'+W(z)+'">'+W(z)+'</span><span class="dash-recent-time">'+W(V)+"</span></div>"}).join("");f.innerHTML=N}}catch{f&&(f.innerHTML='<div class="dash-recent-empty">'+$e("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>")}}window.loadDashboard=et;async function pt(){const e=document.getElementById("dash-kpi-balance-card"),a=document.getElementById("dash-kpi-usage-card"),n=document.getElementById("dash-kpi-balance"),s=document.getElementById("dash-kpi-balance-sub"),l=document.getElementById("dash-kpi-usage"),f=document.getElementById("dash-kpi-usage-sub");if(!(!e||!a))try{const h={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},x=await fetch("/api/me/credits",{headers:h,cache:"no-store"});if(!x.ok){e.style.display="none",l&&(l.textContent="—"),f&&(f.textContent="");return}const o=await x.json(),p=!!o.is_owner,w=!!o.is_billing_exempt;if(!p)e.style.display="none";else if(e.style.display="",w)n&&(n.textContent="∞",n.className="dash-kpi-val dash-green"),s&&(s.textContent=typeof window.t=="function"?window.t("dash-kpi-balance-exempt"):"Billing exempt");else{const B=typeof o.balance_thb=="number"?o.balance_thb:0;if(n&&(n.textContent="฿"+B.toFixed(2),n.className=B<50?"dash-kpi-val dash-red":"dash-kpi-val"),s){const S=typeof window.t=="function"?window.t("dash-kpi-balance-topup"):"Top up →",I=B<50?"#dc2626":"#6b7280",U=N=>typeof window.escapeHtml=="function"?window.escapeHtml(N):String(N).replace(/[&<>"']/g,M=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[M]);s.innerHTML='<a href="#" id="kpi-balance-topup-link" style="color:'+I+';text-decoration:underline;cursor:pointer;" onclick="event.preventDefault();window._openTopupModal&&window._openTopupModal();return false;">'+U(S)+"</a>"}}const g=typeof o.pages_this_month=="number"?o.pages_this_month:typeof o.my_invoice_count=="number"?o.my_invoice_count:0;if(a.style.display="",l&&(l.textContent=String(g)),f){const B=g>=200?"dash-kpi-usage-sub-high":"dash-kpi-usage-sub-low",S=typeof window.t=="function"?window.t(B,{used:g}):g+" pages";f.textContent=S}}catch(h){console.warn("[credits] loadCreditsCard failed:",h),e.style.display="none",l&&(l.textContent="—")}}window.loadCreditsCard=pt;document.addEventListener("DOMContentLoaded",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&setTimeout(et,500)});typeof window.subscribeI18n=="function"&&window.subscribeI18n("dashboard",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&et()});function he(e){return(typeof window.t=="function"?window.t(e):null)||e}function tt(){return localStorage.getItem("mrpilot_token")||""}function me(e){return document.getElementById(e)}var Ve=null,Re=null;function ut(){Re||(Re=setInterval(function(){if(!document.hidden){var e=tt();e&&(window._userInfo&&window._userInfo.is_billing_exempt||fetch("/api/me/credits",{headers:{Authorization:"Bearer "+e},cache:"no-store"}).then(function(a){return a.ok?a.json():null}).then(function(a){if(a){var n=a.balance_thb!=null?Number(a.balance_thb):0;Ve!==null&&n>Ve&&(window.showToast&&window.showToast(he("credits-updated"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard(),typeof window._refreshBalanceAlerts=="function"&&window._refreshBalanceAlerts()),Ve=n}}).catch(function(){}))}},3e4))}function Bt(){Re&&(clearInterval(Re),Re=null),Ve=null}window._startCreditsPoll=ut;window._stopCreditsPoll=Bt;ut();var nt=null,at=0;function It(){if(!me("topup-v2-ov")){var e=document.createElement("div");e.id="topup-v2-ov",e.className="topup-v2-ov",e.style.cssText="display:none;position:fixed;inset:0;background:rgba(15,23,42,.5);z-index:9500;align-items:center;justify-content:center;padding:16px",e.innerHTML=['<div class="topup-v2-box">','  <div class="topup-v2-head">','    <div class="topup-v2-title" id="tv2-title"></div>','    <button class="topup-v2-close" id="tv2-close" aria-label="close">','      <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="4" y1="4" x2="16" y2="16"/><line x1="16" y1="4" x2="4" y2="16"/></svg>',"    </button>","  </div>",'  <div class="topup-v2-steps">','    <div class="topup-v2-step" id="tv2-d1"><span class="topup-v2-dot">1</span><span class="topup-v2-slabel" id="tv2-sl1"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d2"><span class="topup-v2-dot">2</span><span class="topup-v2-slabel" id="tv2-sl2"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d3"><span class="topup-v2-dot">3</span><span class="topup-v2-slabel" id="tv2-sl3"></span></div>',"  </div>",'  <div class="topup-v2-body">','    <div id="tv2-s1">','      <label class="topup-v2-label" id="tv2-al"></label>','      <div class="topup-v2-qamts">','        <button class="topup-v2-qamt" data-val="100">฿100</button>','        <button class="topup-v2-qamt" data-val="500">฿500</button>','        <button class="topup-v2-qamt" data-val="1000">฿1,000</button>','        <button class="topup-v2-qamt" data-val="2000">฿2,000</button>',"      </div>",'      <input id="tv2-amt" type="number" min="10" step="1" class="topup-v2-input" placeholder="฿ ...">','      <div id="tv2-ae" class="topup-v2-err" style="display:none"></div>',"    </div>",'    <div id="tv2-s2" style="display:none">','      <p class="topup-v2-bank-label" id="tv2-bl"></p>','      <div class="topup-v2-bank-card">','        <div class="topup-v2-bank-name">ธนาคาร กรุงเทพ</div>','        <div class="topup-v2-bank-branch">สาขาโชคชัย 4 ลาดพร้าว</div>','        <div class="topup-v2-bank-acct">230-0-91368-4</div>','        <div class="topup-v2-bank-holder">บจ. มิสเตอร์ อี อาร์ พี</div>','        <button class="topup-v2-copy" id="tv2-copy"></button>',"      </div>",'      <div class="topup-v2-warn" id="tv2-bn"></div>',"    </div>",'    <div id="tv2-s3" style="display:none">','      <div class="topup-v2-drop" id="tv2-drop">','        <input type="file" id="tv2-file" accept="image/*,.pdf" style="display:none">','        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>','        <span class="topup-v2-drop-text" id="tv2-dt"></span>',"      </div>",'      <div id="tv2-se" class="topup-v2-err" style="display:none"></div>','      <label class="topup-v2-label" id="tv2-pl"></label>','      <input id="tv2-payer" type="text" maxlength="200" class="topup-v2-input">','      <label class="topup-v2-label" id="tv2-nl"></label>','      <input id="tv2-note" type="text" maxlength="500" class="topup-v2-input">','      <div id="tv2-ue" class="topup-v2-err" style="display:none"></div>',"    </div>","  </div>",'  <div class="topup-v2-foot">','    <button class="btn btn-ghost" id="tv2-back" style="display:none"></button>','    <button class="btn btn-primary" id="tv2-next"></button>',"  </div>","</div>"].join(""),document.body.appendChild(e),Lt()}}function ft(){var e=function(a,n){var s=me(a);s&&(s.textContent=n)};e("tv2-title",he("topup-title")),e("tv2-sl1",he("topup-step1")),e("tv2-sl2",he("topup-step2")),e("tv2-sl3",he("topup-step3")),e("tv2-al",he("topup-amount-label")),e("tv2-bl",he("topup-bank-label")),e("tv2-copy",he("topup-copy-account")),e("tv2-dt",he("topup-slip-drop")),e("tv2-pl",he("topup-payer-label")),e("tv2-nl",he("topup-note-label"))}function ze(e){[1,2,3].forEach(function(l){var f=me("tv2-s"+l);f&&(f.style.display=l===e?"":"none");var h=me("tv2-d"+l);h&&h.classList.toggle("active",l<=e)});var a=me("tv2-back"),n=me("tv2-next");if(e===1?a&&(a.style.display="",a.textContent=he("topup-btn-cancel")):a&&(a.style.display="",a.textContent=he("topup-btn-back")),n&&(n.textContent=he(e===3?"topup-btn-submit":"topup-btn-next")),e===2){var s=me("tv2-bn");s&&(s.innerHTML=he("topup-bank-note").replace("{amount}","<strong>฿"+Number(at).toLocaleString()+"</strong>"))}}function Ze(){for(var e=1;e<=3;e++){var a=me("tv2-s"+e);if(a&&a.style.display!=="none")return e}return 1}function Ue(e){var a=me(e);a&&(a.textContent="",a.style.display="none")}function qe(e,a){var n=me(e);n&&(n.textContent=a,n.style.display="")}function ct(e){var a=me("tv2-dt");a&&(a.textContent=e.name);var n=me("tv2-drop");n&&n.classList.add("has-file"),Ue("tv2-se")}function Lt(){var e=me("topup-v2-ov");me("tv2-close").addEventListener("click",De),e.addEventListener("click",function(f){f.target===e&&De()}),document.addEventListener("keydown",function(f){f.key==="Escape"&&e&&e.style.display!=="none"&&De()}),e.addEventListener("click",function(f){var h=f.target.closest(".topup-v2-qamt");if(h){e.querySelectorAll(".topup-v2-qamt").forEach(function(o){o.classList.remove("active")}),h.classList.add("active");var x=me("tv2-amt");x&&(x.value=h.dataset.val,Ue("tv2-ae"))}});var a=me("tv2-amt");a&&a.addEventListener("input",function(){e.querySelectorAll(".topup-v2-qamt").forEach(function(f){f.classList.remove("active")}),Ue("tv2-ae")});var n=me("tv2-copy");n&&n.addEventListener("click",function(){navigator.clipboard&&navigator.clipboard.writeText("2300913684").then(function(){var f=n.textContent;n.textContent=he("topup-copied"),setTimeout(function(){n.textContent=f},1500)})});var s=me("tv2-drop"),l=me("tv2-file");s&&(s.addEventListener("click",function(){l&&l.click()}),s.addEventListener("dragover",function(f){f.preventDefault(),s.classList.add("drag-over")}),s.addEventListener("dragleave",function(){s.classList.remove("drag-over")}),s.addEventListener("drop",function(f){f.preventDefault(),s.classList.remove("drag-over");var h=f.dataTransfer&&f.dataTransfer.files[0];h&&ct(h)})),l&&l.addEventListener("change",function(){l.files[0]&&ct(l.files[0])}),me("tv2-back").addEventListener("click",function(){var f=Ze();if(f<=1){De();return}ze(f-1)}),me("tv2-next").addEventListener("click",function(){var f=Ze();f===1?Ct():f===2?ze(3):St()})}async function Ct(){var e=me("tv2-amt"),a=e?parseFloat(e.value):0;if(!a||a<10){qe("tv2-ae",he("topup-amount-invalid"));return}if(a>5e5){qe("tv2-ae",he("topup-amount-too-large"));return}at=a;var n=me("tv2-next");n&&(n.disabled=!0,n.textContent="…");try{var s=await fetch("/api/credits/topup/request",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+tt()},body:JSON.stringify({amount_thb:a})});if(!s.ok){var l=await s.text(),f=he("topup-submit-fail");try{var h=JSON.parse(l),x=h.detail;if(Array.isArray(x)&&x.length){var o=x[0]&&x[0].type||"";o.indexOf("less_than")>=0?f=he("topup-amount-too-large"):(o.indexOf("greater_than")>=0||o.indexOf("parsing")>=0)&&(f=he("topup-amount-invalid"))}else typeof x=="string"&&(f=x)}catch{}throw new Error(f)}var p=await s.json();nt=p.request_id,ze(2)}catch(w){qe("tv2-ae",w.message||he("topup-submit-fail"))}finally{n&&(n.disabled=!1,n.textContent=he("topup-btn-next"))}}async function St(){var e=me("tv2-file");if(!e||!e.files||!e.files[0]){qe("tv2-se",he("topup-slip-required"));return}var a=me("tv2-next");a&&(a.disabled=!0,a.textContent="…");try{var n=new FormData;n.append("file",e.files[0]);var s=me("tv2-payer"),l=me("tv2-note");s&&s.value.trim()&&n.append("payer_name",s.value.trim()),l&&l.value.trim()&&n.append("note",l.value.trim());var f=await fetch("/api/credits/topup/upload-slip/"+nt,{method:"POST",headers:{Authorization:"Bearer "+tt()},body:n});if(!f.ok)throw new Error(await f.text());var h=await f.json();h.auto_approved?(window.showToast&&window.showToast(he("topup-auto-approved"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard()):window.showToast&&window.showToast(he("topup-pending"),"info"),De()}catch(x){qe("tv2-ue",he("topup-upload-fail")+" · "+x.message),a&&(a.disabled=!1,a.textContent=he("topup-btn-submit"))}}function De(){var e=me("topup-v2-ov");e&&(e.style.display="none"),typeof window.loadDashboard=="function"&&window.loadDashboard()}window._openTopupModal=function(){It(),nt=null,at=0,["tv2-amt","tv2-payer","tv2-note"].forEach(function(n){var s=me(n);s&&(s.value="")});var e=me("tv2-file");e&&(e.value="");var a=me("tv2-drop");a&&a.classList.remove("has-file","drag-over"),me("topup-v2-ov").querySelectorAll(".topup-v2-qamt").forEach(function(n){n.classList.remove("active")}),["tv2-ae","tv2-se","tv2-ue"].forEach(function(n){Ue(n)}),ft(),ze(1),me("topup-v2-ov").style.display="flex"};typeof window.subscribeI18n=="function"&&window.subscribeI18n("topup-v2",function(){var e=me("topup-v2-ov");e&&e.style.display!=="none"&&e.style.display!==""&&(ft(),ze(Ze()))});(function(){const e="v118.28.5",a="pearnly_tc_results_"+e,n=[{id:"A1",group:"A · 异常栏 page-head(BUG1)",desc:"手机宽度进异常栏 · 标题「异常栏」横排正常 · 不再每字一行"},{id:"A2",group:"A · 异常栏 page-head(BUG1)",desc:"副标题「所有被规则拦截的单据集中复核…」也横排正常 · 不竖排"},{id:"A3",group:"A · 异常栏 page-head(BUG1)",desc:"客户筛选下拉 + 刷新按钮换到新一行 · 不抢标题宽度"},{id:"B1",group:"B · 客户管理 page-head(BUG2)",desc:"手机宽度进客户管理 · 标题「客户管理」横排正常"},{id:"B2",group:"B · 客户管理 page-head(BUG2)",desc:"副标题「为每家客户单独归档发票…」横排正常 · 不竖排"},{id:"B3",group:"B · 客户管理 page-head(BUG2)",desc:"「+ 新建客户」按钮换到新一行 · 不挤标题"},{id:"C1",group:"C · 客户卡片(BUG3)",desc:"客户卡片「编辑 / 导出本月」按钮文字清晰 · 不被截断"},{id:"D1",group:"D · 历史表头(BUG4)",desc:"手机宽度进单据记录 · 表头「文件·发票号·供应商」/「金额」单行 · 不竖排"},{id:"D2",group:"D · 历史表头(BUG4)",desc:"行内 INV-TH-202605-1006 这种长发票号正常单行展示 · 不一字一行"},{id:"E1",group:"E · 对账切换器(BUG6)",desc:"手机宽度进对账中心 · 顶栏点「全部客户」chip · 下拉从右上角向下展开 · 右对齐 · 不贴左屏边"},{id:"E2",group:"E · 对账切换器(BUG6)",desc:"下拉宽度自适应屏幕 · 不超出屏幕右边"},{id:"F1",group:"F · 通用设置回归",desc:"设置 → 个人资料 · 没有「界面语言」4 按钮卡"},{id:"F2",group:"F · 通用设置回归",desc:"左侧 nav 顺序:账户 / 公司 / 工作流 / 系统 / 关于"},{id:"F3",group:"F · 通用设置回归",desc:"系统 → 通用设置 · 4 行下拉(语言/时区/日期/数字)· 改语言立即切语言 · 改其他保存后 F5 仍保留"},{id:"G1",group:"G · 移动端 settings(回归)",desc:"手机宽度设置 tabs 不重叠 · 按分组分行 · chip 风格"},{id:"H1",group:"H · 回归",desc:"OCR 上传识别 / 客户管理 / 异常栏 / 对账中心 / 测试中心 全部仍工作"},{id:"H2",group:"H · 回归",desc:"4 语切换没新增异常(测试中心异常日志「API 失败」过滤无新条目)"},{id:"I1",group:"I · 三档移动 viewport",desc:"iPhone SE 375 · 上述 BUG 1-6 都修了"},{id:"I2",group:"I · 三档移动 viewport",desc:"Galaxy S 360 · 上述 BUG 1-6 都修了"},{id:"I3",group:"I · 三档移动 viewport",desc:"iPhone 12 Pro 414 · 上述 BUG 1-6 都修了"}];let s={},l="all",f=!1,h=!1;function x(F,Q,ie){let le=typeof t=="function"?t(F):null;return(!le||le===F)&&(le=Q),ie&&Object.keys(ie).forEach(function(ue){le=String(le).replace("{"+ue+"}",String(ie[ue]))}),le}function o(){try{const F=localStorage.getItem(a);s=F?JSON.parse(F):{},(typeof s!="object"||!s)&&(s={})}catch{s={}}}function p(){try{localStorage.setItem(a,JSON.stringify(s))}catch{}}function w(F){const Q=new Date(F),ie=function(le){return le<10?"0"+le:""+le};return ie(Q.getHours())+":"+ie(Q.getMinutes())+":"+ie(Q.getSeconds())}function g(F){return String(F??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function B(F,Q){try{typeof showToast=="function"?showToast(F,Q||"info"):alert(F)}catch{}}function S(F){try{navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(F).then(function(){B(x("tc-toast-copied","已复制到剪贴板"),"success")}).catch(function(){I(F)}):I(F)}catch{I(F)}}function I(F){try{const Q=document.createElement("textarea");Q.value=F,Q.style.position="fixed",Q.style.opacity="0",document.body.appendChild(Q),Q.select();const ie=document.execCommand("copy");document.body.removeChild(Q),B(ie?x("tc-toast-copied","已复制"):x("tc-toast-copy-fail","复制失败"),ie?"success":"error")}catch{B(x("tc-toast-copy-fail","复制失败"),"error")}}function U(){const F=document.getElementById("tc-account-chip"),Q=document.getElementById("tc-progress-chip");if(F&&(F.textContent=_userInfo&&(_userInfo.email||_userInfo.username)||"—"),Q){const ie=n.length,le=n.filter(function(ue){return s[ue.id]}).length;Q.textContent=le+" / "+ie}}function N(){const F=document.getElementById("tc-checklist-body");if(!F)return;const Q={};n.forEach(function(le){Q[le.group]||(Q[le.group]=[]),Q[le.group].push(le)});const ie=[];Object.keys(Q).forEach(function(le){ie.push('<div class="tc-checklist-group">'),ie.push('<div class="tc-checklist-group-title">'+g(le)+"</div>"),Q[le].forEach(function(ue){const R=s[ue.id]||"",k=R?"is-"+R:"";ie.push('<div class="tc-check-item '+k+'" data-id="'+g(ue.id)+'"><div class="tc-check-id">'+g(ue.id)+'</div><div class="tc-check-desc">'+g(ue.desc)+'</div><div class="tc-check-actions">'+M(ue.id,"pass",R)+M(ue.id,"fail",R)+M(ue.id,"skip",R)+"</div></div>")}),ie.push("</div>")}),F.innerHTML=ie.join("")}function M(F,Q,ie){const le=ie===Q,ue={pass:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="4,11 8,15 16,5"/></svg>',fail:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="5" x2="15" y2="15"/><line x1="15" y1="5" x2="5" y2="15"/></svg>',skip:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="10" x2="15" y2="10"/></svg>'},R={pass:x("tc-status-pass","通过"),fail:x("tc-status-fail","失败"),skip:x("tc-status-skip","跳过")};return'<button type="button" class="tc-status-btn '+(le?"is-active "+Q:"")+'" data-id="'+g(F)+'" data-kind="'+Q+'" title="'+g(R[Q])+'">'+ue[Q]+"</button>"}function L(F){return l==="all"?!0:l==="js_error"?F.type==="js_error"||F.type==="promise_error":l==="api"?F.type==="api_error"||F.type==="api_fail":l==="api_slow"?F.type==="api_slow":l==="console"?F.type==="console_error"||F.type==="console_warn":!0}function z(){const F=document.getElementById("tc-logs-body"),Q=document.getElementById("tc-logs-count");if(!F)return;const ie=(window._pearnlyTcLogs||[]).slice().reverse(),le=ie.filter(L);if(Q&&(Q.textContent=String(ie.length)),le.length===0){F.innerHTML='<div class="tc-logs-empty">'+g(x("tc-logs-empty","暂无异常"))+"</div>";return}const ue=le.slice(0,100).map(function(R){const k=typeof R.detail=="object"?JSON.stringify(R.detail,null,2):String(R.detail||"");return'<div class="tc-log-item t-'+g(R.type)+'" data-ts="'+R.ts+'"><span class="tc-log-time">'+w(R.ts)+'</span><span class="tc-log-type">'+g(R.type)+'</span><div class="tc-log-summary">'+g(R.summary)+'<div class="tc-log-detail">'+g(k)+"</div></div></div>"}).join("");F.innerHTML=ue,document.querySelectorAll("#tc-logs-filter .tc-filter-chip").forEach(function(R){R.classList.toggle("active",R.getAttribute("data-filter")===l)})}function V(){h||(h=!0,setTimeout(function(){h=!1,currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&z(),W()},200))}window._tcOnNewLog=V;function W(){const F=document.getElementById("nav-test-badge");if(!F)return;const Q=(window._pearnlyTcLogs||[]).filter(function(ie){return ie.type==="js_error"||ie.type==="promise_error"||ie.type==="api_error"||ie.type==="api_fail"||ie.type==="console_error"}).length;Q>0?(F.style.display="",F.textContent=Q>99?"99+":String(Q)):F.style.display="none"}function P(){U(),N(),z(),W()}function u(){const F=[],Q=new Date,ie=_userInfo&&(_userInfo.email||_userInfo.username)||"—";F.push("# Pearnly "+e+" 测试结果"),F.push("- 账号:"+ie),F.push("- 时间:"+Q.toISOString().replace("T"," ").slice(0,19));const le=n.length,ue=n.filter(function(re){return s[re.id]==="pass"}).length,R=n.filter(function(re){return s[re.id]==="fail"}).length,k=n.filter(function(re){return s[re.id]==="skip"}).length,Y=le-ue-R-k;F.push("- 进度:"+(ue+R+k)+" / "+le+" · ✅ "+ue+" · ❌ "+R+" · ⏭ "+k+" · 未测 "+Y),F.push(""),F.push("| ID | 描述 | 状态 |"),F.push("|---|---|---|"),n.forEach(function(re){const de=s[re.id],pe=de==="pass"?"✅":de==="fail"?"❌":de==="skip"?"⏭":"⬜";F.push("| "+re.id+" | "+re.desc.replace(/\|/g,"\\|")+" | "+pe+" |")});const X=n.filter(function(re){return s[re.id]==="fail"});X.length>0&&(F.push(""),F.push("## ❌ 失败项"),X.forEach(function(re){F.push("- **"+re.id+"** · "+re.desc)}));const ee=(window._pearnlyTcLogs||[]).slice(-30).reverse();return ee.length>0&&(F.push(""),F.push("## 🔴 异常日志(最近 "+ee.length+" 条)"),ee.forEach(function(re){if(F.push("- `"+w(re.ts)+"` · **"+re.type+"** · "+re.summary),re.detail){let de;try{de=JSON.stringify(re.detail)}catch{de=String(re.detail)}de&&de!=="{}"&&F.push("  - "+de.slice(0,600))}})),F.join(`
`)}function c(F){const Q=(window._pearnlyTcLogs||[]).slice(-30).reverse();if(Q.length===0)return"(暂无异常日志)";const ie=["# Pearnly 异常日志(最近 "+Q.length+" 条)"],le=_userInfo&&(_userInfo.email||_userInfo.username)||"—";return ie.push("- 账号:"+le),ie.push("- 当前页:"+(currentRoute||"?")),ie.push("- UA:"+navigator.userAgent),ie.push(""),Q.forEach(function(ue){if(ie.push("## `"+w(ue.ts)+"` · "+ue.type),ie.push("- "+ue.summary),ue.detail){ie.push("```");try{ie.push(JSON.stringify(ue.detail,null,2).slice(0,2e3))}catch{ie.push(String(ue.detail).slice(0,2e3))}ie.push("```")}}),ie.join(`
`)}function y(){const F=Date.now();fetch("/api/health").then(function(Q){const ie=Date.now()-F;Q.ok?B(x("tc-toast-health-ok","后端健康 ✓ {ms}ms",{ms:ie}),"success"):B(x("tc-toast-health-fail","后端无响应")+" ("+Q.status+")","error")}).catch(function(){B(x("tc-toast-health-fail","后端无响应"),"error")})}function $(){try{localStorage.removeItem(a),localStorage.removeItem("pearnly_current_client_id"),s={},(window._pearnlyTcLogs||[]).length=0,l="all",window.setCurrentClientId}catch{}P(),B(x("tc-toast-cleared","session 状态已清空"),"success")}function T(){try{fetch("/api/clients",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}).then(function(F){return F.json()}).then(function(F){window._clientsCache=F.clients||[],typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher(),typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter(),B("客户缓存已刷新 · "+(F.clients||[]).length+" 个客户","success")}).catch(function(){B("刷新失败","error")})}catch{}}function _(){if(f||!document.getElementById("page-test-center"))return;f=!0;const Q=document.getElementById("tc-checklist-body");Q&&Q.addEventListener("click",function(de){const pe=de.target.closest(".tc-status-btn");if(!pe)return;const G=pe.getAttribute("data-id"),ae=pe.getAttribute("data-kind");!G||!ae||(s[G]===ae?delete s[G]:s[G]=ae,p(),N(),U())});const ie=document.getElementById("tc-btn-reset-checklist");ie&&ie.addEventListener("click",function(){s={},p(),N(),U()});const le=document.getElementById("tc-btn-copy-all");le&&le.addEventListener("click",function(){S(u())});const ue=document.getElementById("tc-btn-copy-logs");ue&&ue.addEventListener("click",function(){S(c())});const R=document.getElementById("tc-btn-clear-logs");R&&R.addEventListener("click",function(){(window._pearnlyTcLogs||[]).length=0,z(),W()});const k=document.getElementById("tc-logs-filter");k&&k.addEventListener("click",function(de){const pe=de.target.closest(".tc-filter-chip");pe&&(l=pe.getAttribute("data-filter")||"all",z())});const Y=document.getElementById("tc-logs-body");Y&&Y.addEventListener("click",function(de){const pe=de.target.closest(".tc-log-item");pe&&pe.classList.toggle("expanded")});const X=document.getElementById("tc-tool-health");X&&X.addEventListener("click",y);const ee=document.getElementById("tc-tool-clear-session");ee&&ee.addEventListener("click",$);const re=document.getElementById("tc-tool-reload-clients");re&&re.addEventListener("click",T)}function E(){}window._tcApplyVisibility=E;let D=0;const J=setInterval(function(){D++,_userInfo&&clearInterval(J),D>60&&clearInterval(J)},500);window.loadTestCenterPage=function(){o(),_(),P()},typeof window.subscribeI18n=="function"&&window.subscribeI18n("test-center",function(){W(),currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&P()})})();(function(){const e="pearnly_active_workspace_client_id",a="pearnly_work_mode";function n(L,z){if(typeof window.t=="function"){const V=window.t(L);if(V&&V!==L)return V}return z}function s(){const L=window._userInfo||{},z=String(L.role||"").toLowerCase(),V=String(L.tenant_role||"").toLowerCase();return L.is_super_admin===!0||L.is_owner===!0||z==="owner"||z==="admin"||V==="owner"||V==="admin"}function l(){return localStorage.getItem(a)==="client"?"client":"personal"}function f(){const L=localStorage.getItem(e);if(!L||L==="null"||L==="0"||L==="")return null;const z=parseInt(L,10);return isNaN(z)?null:z}function h(L){try{window.dispatchEvent(new CustomEvent("pearnly:workspace-changed",{detail:{id:L,mode:l()}}))}catch{}}function x(L){const z=f();L==null||L===0?localStorage.removeItem(e):(localStorage.setItem(e,String(L)),localStorage.setItem(a,"client")),String(z)!==String(L)&&h(L)}function o(){const L=f();localStorage.setItem(a,"personal"),localStorage.removeItem(e),L!=null&&h(null)}async function p(){try{const L=window.apiGet;if(typeof L!="function")return[];const z=await L("/api/workspace/clients");return z&&(z.clients||z.items)||[]}catch{return[]}}async function w(L){if(l()==="client"&&f()!=null)return typeof L=="function"&&L(),!0;const z=n("ws-need-client","这个功能需要先选择工作空间"),V=n("ws-btn-pick","选择工作空间"),W=n("ws-btn-cancel","取消");return typeof window.showConfirm=="function"?await window.showConfirm(z,{okText:V,cancelText:W})&&g(L):window.confirm(z+`

[`+V+" / "+W+"]")&&g(L),!1}async function g(L){const z=await p();if(typeof L=="function"&&l()!=="personal"&&z.length===1){x(Number(z[0].id)),L();return}if(typeof window.openWorkspaceChooserUI=="function"){window.openWorkspaceChooserUI({clients:z,canCreate:s(),active:f(),onPersonal:o,onPick:function(V){x(Number(V)),typeof L=="function"&&L()},emptyHint:z.length?null:s()?n("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):n("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。")});return}if(!z.length){const V=s()?n("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):n("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。");typeof window.showToast=="function"&&window.showToast(V,"info")}}function B(L){const z=L||document.getElementById("workspace-switcher-root");if(!z)return;const V=l(),W=f();let P,u;if(V==="client"&&W!=null){const $=(window._workspaceClientsCache||[]).find(T=>Number(T.id)===Number(W));P=I("building"),u=$?$.name:n("ws-current-label","当前工作空间")}else P=I("user"),u=n("ws-personal","个人事务");z.innerHTML='<button class="ws-ctrl-btn" id="ws-ctrl-btn" type="button">'+P+'<span class="ws-ctrl-label">'+S(u)+"</span></button>";const c=z.querySelector("#ws-ctrl-btn");c&&c.addEventListener("click",()=>g(null))}function S(L){return String(L??"").replace(/[&<>"']/g,function(z){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[z]})}function I(L){const z='<svg class="ws-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';return L==="building"?z+'<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>':z+'<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'}function U(L){L=L||{};const z=L.clients||[],V=L.active,W=document.getElementById("ws-modal");W&&W.remove();const P=document.createElement("div");P.id="ws-modal",P.className="ws-modal";const c='<button type="button" class="ws-modal-item'+(l()==="personal"||V==null?" active":"")+'" data-ws-personal="1"><span class="ws-modal-item-ic">'+I("user")+'</span><span class="ws-modal-item-text" style="display:flex;flex-direction:column;align-items:flex-start;min-width:0;"><span class="ws-modal-item-name">'+S(n("ws-personal","个人事务"))+'</span><span class="ws-modal-item-desc" style="font-size:11px;color:#6b7280;font-weight:400;margin-top:2px;line-height:1.35;white-space:normal;">'+S(n("ws-personal-desc","用于临时识别、测试或处理不归属任何公司的文件。"))+"</span></span></button>";let y="";if(z.length){const D=['<option value="">'+S(n("ws-select-ph","— 选择账套主体 —"))+"</option>"].concat(z.map(function(J){const F=V!=null&&Number(V)===Number(J.id);return'<option value="'+S(J.id)+'"'+(F?" selected":"")+">"+S(J.name||"#"+J.id)+"</option>"}));y='<div class="ws-modal-select-row"><label class="ws-modal-select-label">'+S(n("ws-select-label","账套主体"))+'</label><select class="ws-modal-select" data-ws-select="1">'+D.join("")+"</select></div>"}const $=!z.length&&L.emptyHint?'<div class="ws-modal-empty">'+S(L.emptyHint)+"</div>":"",T=L.canCreate?'<div class="ws-modal-create"><button type="button" class="ws-modal-create-toggle" data-ws-create-toggle="1">+ '+S(n("ws-create-client","新建工作空间"))+'</button><div class="ws-modal-create-form" data-ws-create-form style="display:none;"><input type="text" class="ws-modal-create-input" data-ws-create-name placeholder="'+S(n("ws-create-ph","公司名称,例如 BAKELAB"))+'"><button type="button" class="ws-modal-create-submit" data-ws-create-submit="1">'+S(n("ws-create-submit","创建"))+"</button></div></div>":"";P.innerHTML='<div class="ws-modal-box" role="dialog" aria-modal="true"><div class="ws-modal-head"><span class="ws-modal-title">'+S(n("ws-chooser-title","选择工作空间"))+'</span><button type="button" class="ws-modal-close" data-ws-close="1" aria-label="close">✕</button></div><div class="ws-modal-subtitle" style="font-size:12px;color:#6b7280;padding:2px 4px 12px;line-height:1.45;white-space:normal;">'+S(n("ws-chooser-subtitle","账套主体 = 你的公司(发票卖方/开票方)。选择正在为哪家公司做账。"))+'</div><div class="ws-modal-list">'+c+y+"</div>"+$+T+"</div>",document.body.appendChild(P);const _=P.querySelector("[data-ws-select]");_&&_.addEventListener("change",function(){const D=_.value;D&&(typeof L.onPick=="function"&&L.onPick(D),E(),B())});function E(){P.remove()}P.addEventListener("click",function(D){if(D.target===P||D.target.closest("[data-ws-close]")){E();return}if(D.target.closest("[data-ws-personal]")){typeof L.onPersonal=="function"&&L.onPersonal(),E(),B();return}const F=D.target.closest("[data-ws-pick]");if(F){const le=F.getAttribute("data-ws-pick");typeof L.onPick=="function"&&L.onPick(le),E(),B();return}if(D.target.closest("[data-ws-create-toggle]")){const le=P.querySelector("[data-ws-create-form]");if(le){le.style.display=le.style.display==="none"?"flex":"none";const ue=le.querySelector("[data-ws-create-name]");ue&&ue.focus()}return}if(D.target.closest("[data-ws-create-submit]")){N(P,L,E);return}})}async function N(L,z,V){const W=L.querySelector("[data-ws-create-name]"),P=W?(W.value||"").trim():"";if(!P){W&&W.focus();return}let u=null;try{if(typeof window.apiPost=="function"){const y=await window.apiPost("/api/workspace/clients",{name:P});u=y&&typeof y.json=="function"?await y.json().catch(()=>null):y}}catch{u=null}const c=u&&(u.id||u.client&&u.client.id);if(!c){typeof window.showToast=="function"&&window.showToast(n("ws-create-fail","新建工作空间失败 · 请重试"),"error");return}window._workspaceClientsCache=await p(),x(Number(c)),z.onPick,V(),B()}window.openWorkspaceChooserUI=U,window.addEventListener("pearnly:workspace-changed",function(){B()}),window.getWorkMode=l,window.getActiveWorkspaceClientId=f,window.setActiveWorkspaceClientId=x,window.enterPersonalMode=o,window.requireWorkspace=w,window.openWorkspaceChooser=g,window.renderWorkspaceControl=B,window.fetchWorkspaceClients=p;function M(){try{if(sessionStorage.getItem("pearnly_ws_login_prompted")==="1"||f()!=null||localStorage.getItem(a)==="personal")return;sessionStorage.setItem("pearnly_ws_login_prompted","1"),setTimeout(function(){g(null)},800)}catch{}}p().then(L=>{window._workspaceClientsCache=L,B(),M()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("workspace-switcher",B)})();(function(){const e=V=>document.querySelector('[data-num-target="'+V+'"]');function a(V){if(!V)return t("reconcile-last-activity-none");try{const W=new Date(V),P=new Date,u=P-W;if(u/6e4<5)return t("reconcile-last-activity-just-now");if(W.toDateString()===P.toDateString())return t("reconcile-last-activity-today");const y=Math.max(1,Math.floor(u/(24*3600*1e3)));return t("reconcile-last-activity-days-ago").replace("{n}",y)}catch{return t("reconcile-last-activity-none")}}function n(V,W,P){const u=e(V);u&&(u.textContent=P?"-":String(W),u.classList.toggle("is-empty",!!P))}function s(V){const W=document.getElementById("reconcile-error");W&&(W.style.display=V?"flex":"none")}function l(V){const W=document.getElementById("reconcile-empty");W&&(W.style.display=V?"flex":"none")}function f(V,W){const P=document.getElementById("reconcile-last-activity");P&&(P.textContent=V,P.classList.toggle("has-data",!!W))}function h(V){const W=!V||(V.total_sessions||0)===0;n("pending",V.pending||0,W),n("matched",V.matched||0,W),n("unmatched",V.unmatched||0,W),f(a(V.last_activity_at),!!V.last_activity_at),s(!1),l(W)}function x(V){const W=V.toUpperCase();return W==="KBANK"?"bank-chip-kbank":W==="SCB"?"bank-chip-scb":W==="BBL"?"bank-chip-bbl":W==="KTB"?"bank-chip-ktb":W==="TTB"?"bank-chip-ttb":"bank-chip-other"}function o(V,W){const P=u=>u?String(u).slice(0,10):"?";return!V&&!W?"":P(V)+" ~ "+P(W)}function p(V){return V==null?"":String(V).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function w(V){const W=document.getElementById("reconcile-recent"),P=document.getElementById("reconcile-recent-list");if(!W||!P)return;const u=(V||[]).slice(0,20);if(u.length===0){W.style.display="none";return}W.style.display="",l(!1),P.innerHTML=u.map(c=>{const y=c.parse_status==="parse_failed",$=c.bank_code||"OTHER",T=c.account_last4?" ···"+p(c.account_last4):"",_=o(c.period_start,c.period_end),E=p(c.source_filename||""),D=Number(c.tx_count||0),J=y?'<span class="recon-card-fail" data-i18n="reconcile-card-parse-failed">'+t("reconcile-card-parse-failed")+"</span>":'<span class="recon-card-tx">'+t("reconcile-card-tx").replace("{n}",D)+"</span>";return'<div class="recon-card" data-session-id="'+p(c.id)+'" data-session-name="'+E+'"><span class="bank-chip '+x($)+'">'+p($)+'</span><div class="recon-card-main"><div class="recon-card-title">'+E+T+'</div><div class="recon-card-sub">'+p(_)+'</div></div><div class="recon-card-right">'+J+'</div><button class="recon-card-trash" data-trash="'+p(c.id)+'" title="'+p(t("bank-session-delete-tip")||"删除")+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/></svg></button><svg class="recon-card-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg></div>'}).join(""),P.querySelectorAll(".recon-card").forEach(c=>{c.addEventListener("click",y=>{y.target.closest(".recon-card-trash")||(c.dataset.sessionId,g())})}),P.querySelectorAll(".recon-card-trash").forEach(c=>{c.addEventListener("click",y=>{y.stopPropagation();const $=c.dataset.trash,T=c.closest(".recon-card"),_=T&&T.dataset.sessionName||"";typeof window._deleteBankSession=="function"&&window._deleteBankSession($,_)})})}function g(V){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const W=document.querySelector('[data-recon-tab="bank"]');W&&W.click()},150)}function B(){s(!0),l(!1)}function S(){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const V=document.querySelector('[data-recon-tab="bank"]');V&&V.click()},150)}async function I(){n("pending",0,!0),n("matched",0,!0),n("unmatched",0,!0),f("",!1),s(!1),l(!1);const V=document.getElementById("reconcile-recent");V&&(V.style.display="none");const W={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")};try{const[P,u]=await Promise.all([fetch("/api/bank-recon/stats",{headers:W}),fetch("/api/bank-recon/sessions?limit=20",{headers:W})]);if(!P.ok)throw new Error("http "+P.status);const c=await P.json(),y=u.ok?await u.json():[];h(c||{}),w(y||[])}catch(P){console.warn("[reconcile] load failed",P),B()}}function U(V){if(!V||!V.length)return;const W="Bearer "+(localStorage.getItem("mrpilot_token")||"");let P=0;const u=V.length;Array.from(V).forEach(function(c){const y=new FormData;y.append("file",c,c.name);const $=new XMLHttpRequest;$.open("POST","/api/bank-recon/upload"),$.setRequestHeader("Authorization",W),$.onload=function(){P++;try{const T=JSON.parse($.responseText);$.status===200&&T.tx_count!==void 0?showToast((t("bank-upload-ok")||"解析成功 · 共 {n} 条流水").replace("{n}",T.tx_count),"success"):showToast(c.name+" "+(t("upload-failed")||"上传失败"),"error")}catch{showToast(c.name+" "+(t("upload-failed")||"上传失败"),"error")}P===u&&setTimeout(I,600)},$.onerror=function(){P++,showToast(c.name+" "+(t("upload-failed")||"上传失败"),"error"),P===u&&setTimeout(I,600)},$.send(y)}),showToast((t("bank-queue-status-uploading")||"上传中")+"…","info")}function N(){if(window.__reconcileBound)return;window.__reconcileBound=!0;const V=document.getElementById("reconcile-bank-file-input");V&&V.addEventListener("change",function(){U(this.files),this.value=""}),document.addEventListener("click",W=>{if(W.target.closest("#btn-reconcile-upload-top")||W.target.closest("#btn-reconcile-upload-empty")){S();return}if(W.target.closest("#btn-reconcile-retry")){I();return}if(W.target.closest("#btn-reconcile-dev-seed")){z();return}})}const M=["468b50c1-5593-4fd6-990d-515ce8085563"];function L(){const V=document.getElementById("btn-reconcile-dev-seed");if(!V)return;const W=typeof _userInfo<"u"?_userInfo:null,P=W&&W.id&&M.indexOf(String(W.id))>=0;V.style.display=P?"":"none"}async function z(){try{const V=await fetch("/api/bank-recon/_dev/seed",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!V.ok)throw new Error("seed:"+V.status);const W=await V.json(),P=(t("reconcile-dev-seed-ok")||"").replace("{n}",W.tx_count||0);showToast(P,"success"),typeof window.navigateTo=="function"?window.navigateTo("automation"):location.hash="#/automation",setTimeout(()=>{const u=document.querySelector('[data-auto-tab="bank"]');u&&u.click(),W.session_id&&typeof window._openBankSession=="function"&&window._openBankSession(W.session_id)},300)}catch(V){console.warn("[reconcile] dev seed failed",V),showToast(t("reconcile-dev-seed-fail")||"Seed failed","error")}}window.loadReconcilePage=async function(){N(),L(),typeof window._bankReconV2Init=="function"&&window._bankReconV2Init();try{await I()}catch{}},window._rerenderReconcile=function(){typeof currentRoute=="string"&&currentRoute==="reconcile"&&I().catch(()=>{})},typeof window.subscribeI18n=="function"&&window.subscribeI18n("reconcile",window._rerenderReconcile)})();(function(){let e={employeeId:null,employeeName:"",clients:[],selected:new Set,opened:!1};function a(){return document.getElementById("assign-clients-modal")}function n(){return document.getElementById("assign-clients-list")}function s(){return document.getElementById("assign-select-all")}function l(){return document.getElementById("assign-selected-count")}function f(){return document.getElementById("assign-modal-target")}function h(){const I=n();if(I){if(!e.clients.length){I.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-no-clients")||"暂无客户 · 请先到「客户管理」添加")+"</div>";return}I.innerHTML=e.clients.map(U=>{const N=String(U.id),M=e.selected.has(N)?"checked":"",L=escapeHtml(U.name||U.label||"#"+N),z=U.code?'<span class="assign-row-code">'+escapeHtml(U.code)+"</span>":"";return'<label class="assign-row"><input type="checkbox" data-cid="'+escapeHtml(N)+'" '+M+'><span class="assign-row-name">'+L+"</span>"+z+"</label>"}).join(""),x()}}function x(){const I=l();if(I){const N=t("assign-selected-count")||"已选 {n} / {total}";I.textContent=N.replace("{n}",e.selected.size).replace("{total}",e.clients.length)}const U=s();U&&(U.checked=e.clients.length>0&&e.selected.size===e.clients.length)}function o(){const I=f();I&&(I.textContent=e.employeeName?" · "+e.employeeName:"")}async function p(I,U){e.employeeId=I,e.employeeName=U||"",e.opened=!0,e.selected=new Set,e.clients=[],o();const N=n();N&&(N.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-loading")||"加载中...")+"</div>");const M=a();M&&(M.style.display="flex");try{const[L,z]=await Promise.all([apiGet("/api/clients?include_inactive=false"),apiGet("/api/team/employees/"+encodeURIComponent(I)+"/assignments")]);e.clients=L&&L.clients||[];const V=z&&z.client_ids||[];e.selected=new Set(V.map(String)),h()}catch(L){console.error("[assign-clients] load failed",L);const z=n();z&&(z.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-load-failed")||"加载失败 · 请重试")+"</div>")}}function w(){e.opened=!1;const I=a();I&&(I.style.display="none")}async function g(){if(!e.employeeId)return;const I=Array.from(e.selected).map(N=>parseInt(N,10)).filter(N=>!isNaN(N)),U=document.getElementById("assign-modal-save");U&&(U.disabled=!0);try{const N=await apiPost("/api/team/employees/"+encodeURIComponent(e.employeeId)+"/assignments",{client_ids:I});N&&N.ok!==!1?(showToast((t("assign-saved")||"已保存 {n} 个客户分配").replace("{n}",I.length),"success"),w(),typeof loadTeamList=="function"&&loadTeamList()):showToast(t("assign-save-failed")||"保存失败","error")}catch(N){console.error("[assign-clients] save failed",N),showToast(t("assign-save-failed")||"保存失败","error")}finally{U&&(U.disabled=!1)}}function B(){const I=a();if(!I||I.dataset.bound==="1")return;I.dataset.bound="1";const U=document.getElementById("assign-modal-close");U&&U.addEventListener("click",w);const N=document.getElementById("assign-modal-cancel");N&&N.addEventListener("click",w);const M=document.getElementById("assign-modal-save");M&&M.addEventListener("click",g),I.addEventListener("click",function(V){V.target===I&&w()});const L=s();L&&L.addEventListener("change",function(){L.checked?e.selected=new Set(e.clients.map(V=>String(V.id))):e.selected=new Set,h()});const z=n();z&&z.addEventListener("change",function(V){const W=V.target.closest('input[type="checkbox"][data-cid]');if(!W)return;const P=W.dataset.cid;W.checked?e.selected.add(P):e.selected.delete(P),x()})}function S(){e.opened&&(o(),h())}typeof window.subscribeI18n=="function"&&window.subscribeI18n("assign-clients-modal",S),window.openAssignClientsModal=function(I,U){B(),p(I,U)}})();(function(){const e={page:1,per_page:50,q:"",total:0,rows:[],loaded:!1};function a(w){if(!w)return"";try{return new Date(w).toLocaleString()}catch{return w}}function n(w){const g=document.getElementById("access-log-table");g&&(g.innerHTML='<div class="access-log-empty">'+escapeHtml(w)+"</div>");const B=document.getElementById("access-log-pager");B&&(B.innerHTML="")}function s(){const w=document.getElementById("access-log-table");if(!w)return;const g=e.rows||[];if(!g.length){n(t("set-access-log-empty"));return}const B=`
            <div class="access-log-row access-log-head">
                <div>${escapeHtml(t("set-access-log-col-time"))}</div>
                <div>${escapeHtml(t("set-access-log-col-actor"))}</div>
                <div>${escapeHtml(t("set-access-log-col-action"))}</div>
                <div>${escapeHtml(t("set-access-log-col-target"))}</div>
                <div>${escapeHtml(t("set-access-log-col-ip"))}</div>
            </div>`,S=g.map(function(I){return`
                <div class="access-log-row">
                    <div class="access-log-time" data-label="${escapeHtml(t("set-access-log-col-time"))}">${escapeHtml(a(I.created_at))}</div>
                    <div class="access-log-actor" data-label="${escapeHtml(t("set-access-log-col-actor"))}">${escapeHtml(I.actor_username||"-")}</div>
                    <div data-label="${escapeHtml(t("set-access-log-col-action"))}"><span class="access-log-action">${escapeHtml(I.action||"-")}</span></div>
                    <div class="access-log-target" data-label="${escapeHtml(t("set-access-log-col-target"))}">${escapeHtml(I.target_name||I.target_type||"-")}</div>
                    <div class="access-log-ip" data-label="${escapeHtml(t("set-access-log-col-ip"))}">${escapeHtml(I.ip||"-")}</div>
                </div>`}).join("");w.innerHTML=B+S}function l(){const w=document.getElementById("access-log-pager");if(!w)return;const g=e.total||0;if(!g){w.innerHTML="";return}const B=e.page||1,S=e.per_page,I=Math.max(1,Math.ceil(g/S)),U=(t("set-access-log-pager-total")||"Total {n}").replace("{n}",g),N=(t("set-access-log-pager-page")||"Page {p} / {t}").replace("{p}",B).replace("{t}",I);w.innerHTML=`
            <div class="access-log-pager-info">${escapeHtml(U)}</div>
            <div class="access-log-pager-ctrl">
                <button class="access-log-pager-btn" type="button" data-access-log-page="${B-1}" ${B<=1?"disabled":""}>← ${escapeHtml(t("set-access-log-pager-prev"))}</button>
                <span class="access-log-pager-page">${escapeHtml(N)}</span>
                <button class="access-log-pager-btn" type="button" data-access-log-page="${B+1}" ${B>=I?"disabled":""}>${escapeHtml(t("set-access-log-pager-next"))} →</button>
            </div>`}async function f(w){const g=localStorage.getItem("mrpilot_token");if(g){e.page=w||1,n(t("set-access-log-loading"));try{const B="/api/me/access_log?page="+e.page+"&per_page="+e.per_page+"&q="+encodeURIComponent(e.q||""),S=await fetch(B,{headers:{Authorization:"Bearer "+g}});if(S.status===403){n(t("set-access-log-empty"));return}if(!S.ok)throw new Error("http_"+S.status);const I=await S.json();e.rows=I.logs||[],e.total=I.total||0,e.loaded=!0,s(),l()}catch{n(t("set-access-log-fail"))}}}async function h(){const w=localStorage.getItem("mrpilot_token");if(w)try{const g="/api/me/access_log.csv?q="+encodeURIComponent(e.q||""),B=await fetch(g,{headers:{Authorization:"Bearer "+w}});if(!B.ok){showToast(t("set-access-log-csv-fail")||"Export failed","error");return}const S=await B.blob(),I=document.createElement("a"),U=URL.createObjectURL(S);I.href=U,I.download="pearnly_access_log.csv",document.body.appendChild(I),I.click(),setTimeout(function(){URL.revokeObjectURL(U),I.remove()},100),showToast(t("set-access-log-csv-ok")||"Exported","success")}catch{showToast(t("set-access-log-csv-fail")||"Export failed","error")}}function x(){const w=document.querySelectorAll(".set-tab-owner-only"),g=!!(_userInfo&&(_userInfo.role==="owner"||_userInfo.is_super_admin));w.forEach(function(B){B.style.display=g?"":"none"})}document.addEventListener("click",function(w){if(w.target.closest('.settings-tab[data-tab="access-log"]')){setTimeout(function(){(!e.loaded||e.page!==1)&&f(1)},50);return}if(w.target.closest("#access-log-csv-btn")){w.preventDefault(),h();return}const S=w.target.closest(".access-log-pager-btn[data-access-log-page]");if(S&&!S.disabled){const I=parseInt(S.dataset.accessLogPage,10);f(I)}}),document.addEventListener("input",function(w){w.target&&w.target.id==="access-log-search"&&(clearTimeout(window.__accessLogSearchTimer),window.__accessLogSearchTimer=setTimeout(function(){e.q=(w.target.value||"").trim(),f(1)},350))});let o=0;const p=setInterval(function(){o++,_userInfo&&(x(),clearInterval(p)),o>60&&clearInterval(p)},500);typeof window.subscribeI18n=="function"&&window.subscribeI18n("me-access-log",function(){x(),e.loaded&&(s(),l())})})();(function(){const e=P=>document.getElementById(P);async function a(P,u){return await fetch(P,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(u||{})})}async function n(P){return await fetch(P,{method:"DELETE",headers:{Authorization:"Bearer "+token}})}let s=null;async function l(){try{s=await apiGet("/api/line/binding")}catch{s={bound:!1}}return s}function f(P,u){if(!P)return;P.style.display="",P.className="notif-line-check "+(u?"bound":"unbound");const c=u?'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>';P.innerHTML=c+"<span>"+escapeHtml(t(u?"notif-line-bound":"notif-line-not-bound"))+"</span>"}function h(P){if(P==null)return"-";const u=Number(P);return isNaN(u)?String(P):"฿ "+u.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function x(P){if(!P)return"-";try{const u=new Date(P),c=(u.getMonth()+1).toString().padStart(2,"0"),y=u.getDate().toString().padStart(2,"0"),$=u.getHours().toString().padStart(2,"0"),T=u.getMinutes().toString().padStart(2,"0");return`${c}-${y} ${$}:${T}`}catch{return P}}function o(P){const u=e("notif-rules-list"),c=e("notif-rules-empty"),y=e("notif-rules-count");if(!(!u||!c)){if(y.textContent=String(P.length),y.className="auto-status-pill "+(P.length>0?"active":"none"),!P.length){c.style.display="",u.style.display="none",u.innerHTML="";return}c.style.display="none",u.style.display="",u.innerHTML=P.map($=>{const T=$.template_code==="large_invoice",_=T?"notif-rule-large-tag":"notif-rule-exception-tag",E=T?"large":"";let D=[];if(T){const F=$.params&&$.params.threshold?h($.params.threshold):"-";D.push(escapeHtml(t("notif-rule-threshold-prefix"))+" "+F)}$.enabled||D.push('<span style="color:#9ca3af;">'+escapeHtml(t("notif-rule-disabled"))+"</span>");const J=D.length?D.join(' <span class="dot"></span> '):"";return`
                <div class="notif-rule-row${$.enabled?"":" disabled"}" data-rule-id="${$.id}">
                    <span class="notif-rule-tmpl-badge ${E}">${escapeHtml(t(_))}</span>
                    <div class="notif-rule-main">
                        <div class="notif-rule-name">${escapeHtml($.name)}</div>
                        <div class="notif-rule-meta">${J}</div>
                    </div>
                    <div class="notif-rule-actions">
                        <button class="notif-rule-toggle ${$.enabled?"on":""}" data-action="toggle" aria-label="toggle"></button>
                        <button class="notif-rule-btn" data-action="test">${escapeHtml(t("notif-action-test"))}</button>
                        <button class="notif-rule-btn danger" data-action="delete">${escapeHtml(t("notif-action-delete"))}</button>
                    </div>
                </div>`}).join("")}}function p(P){const u=e("notif-logs-list");if(u){if(!P.length){u.innerHTML='<div class="notif-logs-empty">'+escapeHtml(t("notif-logs-empty"))+"</div>";return}u.innerHTML=P.map(c=>{const y=c.status==="sent",$=c.event_type==="exception_high"?"notif-event-exception-high":c.event_type==="large_invoice"?"notif-event-large-invoice":"notif-event-test-send",T=y?"":" · "+escapeHtml(c.error||"failed");return`
                <div class="notif-log-row">
                    <span class="notif-log-status ${y?"":"failed"}"></span>
                    <div class="notif-log-main">
                        <div class="notif-log-event">${escapeHtml(t($))}</div>
                        <div class="notif-log-meta">${escapeHtml(c.template_code||"-")}${T}</div>
                    </div>
                    <div class="notif-log-time">${x(c.sent_at)}</div>
                </div>`}).join("")}}async function w(){try{const P=await apiGet("/api/notifications/rules");g=P&&P.items||[],o(g)}catch(P){console.warn("load rules fail",P)}try{const P=await apiGet("/api/notifications/logs?limit=20");B=P&&P.items||[],p(B)}catch(P){console.warn("load logs fail",P)}}let g=null,B=null;function S(){g&&o(g),B&&p(B);const P=e("notif-new-modal");P&&P.style.display!=="none"&&s&&f(e("notif-line-check"),!!(s&&s.bound))}function I(){const P=e("notif-new-modal");P&&(P.style.display="",e("notif-new-name").value="",e("notif-new-threshold").value="",e("notif-new-threshold-row").style.display="none",document.querySelectorAll('input[name="notif-template"]').forEach(u=>u.checked=!1),l().then(u=>f(e("notif-line-check"),!!(u&&u.bound))))}function U(){const P=e("notif-new-modal");P&&(P.style.display="none")}function N(){const P=document.querySelector('input[name="notif-template"]:checked'),u=e("notif-new-threshold-row");if(!P){u.style.display="none";return}u.style.display=P.value==="large_invoice"?"":"none";const c=e("notif-new-name");c&&!c.value.trim()&&(c.value=P.value==="large_invoice"?t("notif-tmpl-large-name"):t("notif-tmpl-exception-name"))}async function M(){const P=document.querySelector('input[name="notif-template"]:checked');if(!P){showToast(t("notif-new-template"),"error");return}const u=(e("notif-new-name").value||"").trim();if(!u){showToast(t("notif-name-required"),"error");return}const c={name:u,template_code:P.value,params:{},enabled:!0};if(P.value==="large_invoice"){const y=parseFloat(e("notif-new-threshold").value||"0");if(!y||y<=0){showToast(t("notif-threshold-required"),"error");return}c.params.threshold=y}try{const y=await apiPost("/api/notifications/rules",c);if(y&&y.ok)showToast(t("notif-toast-created"),"success"),U(),w();else{const $=await(y&&y.json&&y.json().catch(()=>({})))||{};showToast($&&$.detail||"save failed","error")}}catch{showToast("save failed","error")}}async function L(P,u,c){if(P==="toggle"){const y=c.classList.contains("on"),$=await a("/api/notifications/rules/"+u,{enabled:!y});$&&$.ok?(showToast(t(y?"notif-toast-toggled-off":"notif-toast-toggled-on"),"success"),w()):showToast("toggle failed","error");return}if(P==="test"){const y=await l();if(!y||!y.bound){showToast(t("notif-line-error-bind-first"),"error");return}const $=await apiPost("/api/notifications/rules/"+u+"/test",{});if($&&$.ok)showToast(t("notif-toast-test-sent"),"success"),w();else{const T=await($&&$.json&&$.json().catch(()=>({})))||{},_=T&&T.detail||"";showToast(_||t("notif-toast-test-failed"),"error"),w()}return}if(P==="delete"){if(!await showConfirm(t("notif-confirm-delete"),{danger:!0}))return;const $=await n("/api/notifications/rules/"+u);$&&$.ok?(showToast(t("notif-toast-deleted"),"success"),w()):showToast("delete failed","error");return}}let z=!1;function V(){if(z)return;z=!0;const P=e("notif-btn-new");P&&P.addEventListener("click",I);const u=e("notif-btn-refresh-logs");u&&u.addEventListener("click",w);const c=e("notif-new-close");c&&c.addEventListener("click",U);const y=e("notif-new-cancel");y&&y.addEventListener("click",U);const $=e("notif-new-save");$&&$.addEventListener("click",M),document.querySelectorAll('input[name="notif-template"]').forEach(E=>{E.addEventListener("change",N)});const T=e("notif-rules-list");T&&T.addEventListener("click",E=>{const D=E.target.closest("button[data-action]");if(!D)return;const J=D.closest("[data-rule-id]");J&&L(D.getAttribute("data-action"),J.getAttribute("data-rule-id"),D)});const _=e("notif-new-modal");_&&_.addEventListener("click",E=>{E.target===_&&U()})}async function W(){V(),await w()}window._loadNotificationsPanel=W,window._rerenderNotifications=S})();(function(){function a(M,L){try{return window.t&&window.t(M)||L}catch{return L}}function n(){var M="";try{M=localStorage.getItem("mrpilot_token")||""}catch{}return M?{Authorization:"Bearer "+M}:{}}var s=[{tbody:"vex-task-tbody",api:"/api/recon/tasks/batch_delete",reload:function(){try{window.loadRecentTasks&&window.loadRecentTasks()}catch{}},kind:"vex"},{tbody:"glv-history-tbody",api:"/api/recon/gl-vat/tasks/batch_delete",reload:function(){try{window._loadGlvHistory&&window._loadGlvHistory()}catch{}},kind:"glv"},{tbody:"brv2-history-tbody",api:"/api/recon/bank-v2/tasks/batch_delete",reload:function(){try{window._brv2LoadHistory&&window._brv2LoadHistory()}catch{}},kind:"brv2"}];function l(){if(!document.getElementById("recon-batch-style")){var M=document.createElement("style");M.id="recon-batch-style",M.textContent=".recon-sel-cell{width:36px;text-align:center;padding-left:10px!important;padding-right:6px!important}.recon-sel-cb,.recon-master-cb{cursor:pointer;width:14px;height:14px;accent-color:#111;margin:0;vertical-align:middle}th.recon-time-col,td.recon-time-col{white-space:nowrap}tr.recon-thead-batch{display:none}thead.recon-batch-mode tr.recon-thead-default{display:none}thead.recon-batch-mode tr.recon-thead-batch{display:table-row}tr.recon-thead-batch th{background:#fafaf8;border-bottom:1px solid #e8e8e3;padding:8px 12px}tr.recon-thead-batch .recon-batch-inline{display:flex;align-items:center;gap:10px;font-size:12px;color:#111;font-weight:normal}tr.recon-thead-batch .recon-batch-count-inline{font-weight:600;color:#111;margin-right:4px}tr.recon-thead-batch .recon-batch-del-inline{background:#dc2626;color:#fff;border:none;border-radius:6px;padding:4px 10px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:4px}tr.recon-thead-batch .recon-batch-del-inline:hover{background:#b91c1c}tr.recon-thead-batch .recon-batch-clear-inline{background:transparent;border:none;color:#555;cursor:pointer;font-size:12px;font-family:inherit;text-decoration:underline;padding:4px 2px}tr.recon-thead-batch .recon-batch-clear-inline:hover{color:#111}.recon-batch-bar{display:none!important}",document.head.appendChild(M)}}function f(M){return M?M.dataset&&M.dataset.taskId?M.dataset.taskId:M.dataset&&M.dataset.taskid?M.dataset.taskid:"":""}function h(M){var L=document.getElementById(M.tbody);if(!L)return null;var z=L.closest("table");if(!z)return null;var V=z.querySelector("thead");if(!V)return null;if(V._reconReady)return V;var W=V.querySelector("tr");if(!W)return null;if(W.classList.add("recon-thead-default"),!W.querySelector(".recon-master-cb")){var P=document.createElement("th");P.className="recon-sel-cell";var u=document.createElement("input");u.type="checkbox",u.className="recon-master-cb",u.setAttribute("aria-label","select all"),u.addEventListener("change",function(){w(M,u.checked)}),P.appendChild(u),W.insertBefore(P,W.firstElementChild)}var c=W.children[1];c&&!c.classList.contains("recon-time-col")&&c.classList.add("recon-time-col");var y=W.children.length,$=document.createElement("tr");$.className="recon-thead-batch";var T=document.createElement("th");T.className="recon-sel-cell";var _=document.createElement("input");_.type="checkbox",_.className="recon-master-cb",_.checked=!0,_.setAttribute("aria-label","select all"),_.addEventListener("change",function(){w(M,_.checked)}),T.appendChild(_);var E=document.createElement("th");return E.setAttribute("colspan",String(y-1)),E.innerHTML='<div class="recon-batch-inline"><span class="recon-batch-count-inline" data-recon-count></span><button type="button" class="recon-batch-del-inline" data-recon-del><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg><span data-recon-del-label></span></button><button type="button" class="recon-batch-clear-inline" data-recon-clear></button></div>',$.appendChild(T),$.appendChild(E),V.appendChild($),E.querySelector("[data-recon-del]").addEventListener("click",function(){I(M)}),E.querySelector("[data-recon-clear]").addEventListener("click",function(){S(M)}),V._reconReady=!0,B(M),V}function x(M){var L=document.getElementById(M.tbody);if(L){var z=L.querySelectorAll("tr");z.forEach(function(V){var W=f(V);if(W&&!V.querySelector(".recon-sel-cb")){var P=V.querySelector("td");if(P){var u=document.createElement("td");u.className="recon-sel-cell";var c=document.createElement("input");c.type="checkbox",c.className="recon-sel-cb",c.dataset.taskId=W,c.dataset.kind=M.kind,c.addEventListener("click",function($){$.stopPropagation()}),c.addEventListener("change",function(){g(M)}),u.appendChild(c),V.insertBefore(u,P);var y=V.children[1];y&&!y.classList.contains("recon-time-col")&&y.classList.add("recon-time-col")}}}),g(M)}}function o(M){var L=document.getElementById(M.tbody);return L?Array.prototype.slice.call(L.querySelectorAll(".recon-sel-cb")):[]}function p(M){return o(M).filter(function(L){return L.checked}).map(function(L){return L.dataset.taskId})}function w(M,L){o(M).forEach(function(z){z.checked=!!L}),g(M)}function g(M){var L=p(M),z=o(M),V=document.getElementById(M.tbody);if(V){var W=V.closest("table"),P=W&&W.querySelector("thead");if(P){L.length>0?P.classList.add("recon-batch-mode"):P.classList.remove("recon-batch-mode"),P.querySelectorAll(".recon-master-cb").forEach(function(c){if(z.length===0){c.checked=!1,c.indeterminate=!1;return}L.length===z.length?(c.checked=!0,c.indeterminate=!1):L.length===0?(c.checked=!1,c.indeterminate=!1):(c.checked=!1,c.indeterminate=!0)});var u=P.querySelector("[data-recon-count]");u&&(u.textContent=a("recon-batch-selected-n","已选 {n} 条").replace("{n}",L.length))}}}function B(M){var L=document.getElementById(M.tbody);if(L){var z=L.closest("table"),V=z&&z.querySelector("thead");if(V){var W=V.querySelector("[data-recon-del-label]"),P=V.querySelector("[data-recon-clear]");W&&(W.textContent=a("recon-batch-delete","批量删除")),P&&(P.textContent=a("recon-batch-clear","取消")),g(M)}}}function S(M){o(M).forEach(function(L){L.checked=!1}),g(M)}async function I(M){var L=p(M);if(L.length){var z=a("recon-batch-delete-confirm","确定删除选中的 {n} 条对账任务?此操作不可恢复").replace("{n}",L.length),V=!1;try{typeof window.pearnlyConfirm=="function"?V=await window.pearnlyConfirm(z,a("recon-batch-delete-title","批量删除")):V=window.confirm(z)}catch{V=!1}if(V)try{var W=Object.assign({"Content-Type":"application/json"},n()),P=M.kind==="glv"?L.map(function($){return parseInt($,10)}):L,u=await fetch(M.api,{method:"POST",headers:W,body:JSON.stringify({ids:P})});if(!u.ok){typeof window.showToast=="function"&&window.showToast(a("recon-batch-delete-fail","批量删除失败"),"error");return}var c=await u.json(),y=c&&(c.deleted!=null?c.deleted:c.count)||L.length;typeof window.showToast=="function"&&window.showToast(a("recon-batch-delete-ok","已删除 {n} 条").replace("{n}",y),"success"),M.reload()}catch{typeof window.showToast=="function"&&window.showToast(a("recon-batch-delete-fail","批量删除失败"),"error")}}}function U(M){h(M),x(M);var L=document.getElementById(M.tbody);if(!(!L||L._reconBatchWatched)){L._reconBatchWatched=!0;var z=new MutationObserver(function(){x(M)});z.observe(L,{childList:!0,subtree:!1})}}function N(){l(),s.forEach(U),document.querySelectorAll(".recon-batch-bar").forEach(function(M){try{M.remove()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",N):N(),setTimeout(N,1500),setTimeout(N,4e3),document.addEventListener("keydown",function(M){M.key==="Escape"&&s.forEach(function(L){p(L).length>0&&S(L)})}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-batch-thead",function(){s.forEach(B)})})();(function(){let e={role:"",monthly_volume:"",country:"",line_id:""},a=1;const n=4,s="pilot_ob_dismiss",l="pilot_ob_done";window.maybeShowOnboarding=function(p){};function f(p){a=p;for(let B=1;B<=n;B++){const S=document.getElementById("ob-step-"+B);S&&(S.style.display=B===p?"block":"none")}document.querySelectorAll(".ob-dot").forEach(B=>{const S=parseInt(B.dataset.step,10);B.classList.toggle("active",S===p),B.classList.toggle("done",S<p)});const w=document.getElementById("ob-step-label");w&&(w.textContent=p+" / "+n);const g=document.getElementById("ob-next");if(g&&(g.textContent=p===n?t("ob-finish"):t("ob-next")),p===4){const B=document.getElementById("ob-line-input");B&&(B.value=e.line_id||"")}}function h(p){const w=document.querySelector(".onboarding-modal");if(!w)return;let g=w.querySelector(".ob-feedback");g||(g=document.createElement("div"),g.className="ob-feedback",w.appendChild(g)),g.textContent=p,g.classList.add("show"),setTimeout(()=>g.classList.remove("show"),1800)}document.addEventListener("click",p=>{const w=p.target.closest(".ob-option");if(!w)return;const g=w.parentElement;if(!g||!g.classList.contains("ob-options"))return;g.querySelectorAll(".ob-option").forEach(S=>S.classList.remove("selected")),w.classList.add("selected");const B=w.dataset.value;g.id==="ob-role-options"?e.role=B:g.id==="ob-volume-options"?e.monthly_volume=B:g.id==="ob-country-options"&&(e.country=B)}),document.addEventListener("click",p=>{p.target.id==="ob-skip"&&x()}),document.addEventListener("click",p=>{if(p.target.id==="ob-next"){if(a===4){const w=document.getElementById("ob-line-input");e.line_id=(w&&w.value||"").trim().replace(/^@+/,"")}x()}}),document.addEventListener("click",p=>{if(p.target.closest("#ob-close")){localStorage.setItem(s,String(Date.now()));const w=document.getElementById("onboarding-modal");w&&(w.style.display="none")}});function x(){a===1&&e.role?h(t("ob-fb-role")):a===2&&e.monthly_volume?h(t("ob-fb-volume")):a===3&&e.country?h(t("ob-fb-country")):a===4&&e.line_id&&h(t("ob-fb-line")),a<n?setTimeout(()=>f(a+1),e[Object.keys(e)[a-1]]?350:0):o()}async function o(){const p=document.getElementById("onboarding-modal");localStorage.setItem(l,"1"),localStorage.removeItem(s);const w={};if(e.role&&(w.role=e.role),e.monthly_volume&&(w.monthly_volume=e.monthly_volume),e.country&&(w.country=e.country),e.line_id&&(w.line_id=e.line_id),Object.keys(w).length===0){p&&(p.style.display="none");return}try{const g=await fetch("/api/me/profile",{method:"PUT",headers:{Authorization:"Bearer "+(window.token||localStorage.getItem("mrpilot_token")),"Content-Type":"application/json"},body:JSON.stringify(w)});g.ok?(h(t("ob-fb-done")),window._userInfo&&Object.assign(window._userInfo,w),setTimeout(()=>{p&&(p.style.display="none")},1200)):(localStorage.setItem("pilot_ob_pending",JSON.stringify(w)),console.warn("onboarding profile save failed",g.status),h(t("ob-fb-saved-local")),setTimeout(()=>{p&&(p.style.display="none")},1500))}catch(g){console.error("onboarding submit",g),localStorage.setItem("pilot_ob_pending",JSON.stringify(w)),p&&(p.style.display="none")}}})();(function(){let e=[],a="by_month_seller",n=-1,s=!1;const l={date:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="3.5" width="11" height="10" rx="1.5"/><path d="M2.5 6.5h11M5.5 2v3M10.5 2v3"/></svg>',seller:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13.5V4a1 1 0 011-1h5a1 1 0 011 1v9.5"/><path d="M10 7h2.5a.5.5 0 01.5.5v6"/><path d="M5 6h1M5 9h1M5 12h1M13.5 13.5h-12"/></svg>',category:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 2h6L13 5.5v7.5a1 1 0 01-1 1H3.5a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M9 2v4h4"/><path d="M5 9h6M5 11.5h4"/></svg>',amount:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M8 4.5v7M10 6.3a1.8 1.8 0 00-4 0c0 .9.7 1.3 2 1.6s2 .8 2 1.6a1.8 1.8 0 01-4 0"/></svg>',invoice:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3.5l1.5 10.5 1.5-1 1.5 1 1.5-1 1.5 1 1.5-1 1.5 1L13 3.5z"/><path d="M5.5 6.5h5M5.5 9h5M5.5 11.5h3"/></svg>',buyer:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="6" r="2.5"/><path d="M3 13.5c0-2.5 2.2-4.5 5-4.5s5 2 5 4.5"/></svg>',sep:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v10"/></svg>'},f={date:{label:"field-date",defaultCfg:{format:"YYYY-MM-DD"}},seller:{label:"field-seller",defaultCfg:{short:!0}},category:{label:"field-category",defaultCfg:{}},amount:{label:"field-amount",defaultCfg:{with_currency:!0}},invoice:{label:"field-invoice",defaultCfg:{}},buyer:{label:"field-buyer",defaultCfg:{}},sep:{label:"field-sep",defaultCfg:{val:"_"}}};function h(){return{zh:"运费",en:"Shipping",th:"ค่าขนส่ง",ja:"送料"}[currentLang]||"Shipping"}function x(){return"DHL Express (Thailand) Co., Ltd."}function o(){return{merged_fields:{invoice_date:"2026-04-15",seller_name:x(),category:h(),total_amount:1250,currency:"THB",invoice_no:"INV-2026030002",buyer_name:"Mr.ERP Co., Ltd."}}}window.loadAboutPanel=()=>p(),window.loadPrefsSettings=()=>w(),window.loadArchiveSettings=()=>B();function p(){const u=document.getElementById("settings-contact-grid");if(!u)return;const c=_contact?.phone||"086-889-2228",y=_contact?.line_id||"@Pearnly",$=_contact?.line_url||"https://line.me/R/ti/p/@059oupmg",T=_contact?.email||"hello@pearnly.com",_=_contact?.address||"Bangkok, Thailand";u.innerHTML=`
            <a class="contact-item" href="${escapeHtml($)}" target="_blank" rel="noopener">
                <div class="contact-icon line">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.365 9.863c.349 0 .63.285.631.631 0 .345-.282.63-.631.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.282.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63.346 0 .628.285.628.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-line"))}</div>
                    <div class="contact-value">${escapeHtml(y)}</div>
                </div>
            </a>
            <a class="contact-item" href="mailto:${escapeHtml(T)}">
                <div class="contact-icon email">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-email"))}</div>
                    <div class="contact-value">${escapeHtml(T)}</div>
                </div>
            </a>
            <a class="contact-item" href="tel:${escapeHtml(c.replace(/[^\d+]/g,""))}">
                <div class="contact-icon phone">
                    <svg viewBox="0 0 20 20" fill="currentColor"><path d="M2 3a1 1 0 011-1h2.5a1 1 0 01.97.757l1 4a1 1 0 01-.29.986l-1.75 1.75a11 11 0 005.07 5.07l1.75-1.75a1 1 0 01.986-.29l4 1a1 1 0 01.757.97V17a1 1 0 01-1 1h-1C8.82 18 2 11.18 2 3V3z"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-phone"))}</div>
                    <div class="contact-value">${escapeHtml(c)}</div>
                </div>
            </a>
            <div class="contact-item">
                <div class="contact-icon address">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s-7-7.5-7-13a7 7 0 1114 0c0 5.5-7 13-7 13z"/><circle cx="12" cy="9" r="2.5"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-address"))}</div>
                    <div class="contact-value">${escapeHtml(_)}</div>
                </div>
            </div>
        `}async function w(){try{const u=await fetch("/api/settings/dup-check",{headers:{Authorization:"Bearer "+token}});if(!u.ok)return;const c=await u.json(),y=document.getElementById("pref-dup-check");y&&(y.checked=!!c.enabled)}catch(u){console.warn("load prefs failed",u)}}const g=document.getElementById("pref-dup-check");g&&!g.dataset.bound&&(g.dataset.bound="1",g.addEventListener("change",async u=>{const c=u.target.checked;try{(await fetch("/api/settings/dup-check",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({enabled:c})})).ok?showToast(c?t("pref-dup-check-on-toast"):t("pref-dup-check-off-toast"),"success"):(u.target.checked=!c,showToast(t("pref-save-failed"),"error"))}catch{u.target.checked=!c,showToast(t("pref-save-failed"),"error")}}));async function B(){const u=!!(_userInfo&&_userInfo.can_customize_archive);s=!u;const c=document.getElementById("archive-upgrade-banner");c&&(c.style.display=u?"none":"");const y=document.getElementById("archive-plus-badge");y&&(y.style.display=u?"none":"");try{const $=await fetch("/api/archive/settings",{headers:{Authorization:"Bearer "+token}});if(!$.ok)throw new Error("load failed");const T=await $.json();e=Array.isArray(T.name_template)?T.name_template:[],a=T.folder_strategy||"by_month_seller"}catch($){console.error("load archive settings failed",$),showToast(t("archive-load-failed"),"error");return}S(),I(),U(),N()}function S(){const u=document.getElementById("archive-rule-canvas");if(u){if(e.length===0){u.innerHTML=`<div class="archive-empty">${escapeHtml(t("archive-rule-empty"))}</div>`;return}u.innerHTML=e.map((c,y)=>{const $=f[c.type]||{label:c.type},T=l[c.type]||"",_=c.type==="sep"?`"${escapeHtml(c.val||"_")}"`:escapeHtml(t($.label));return`
                <span class="archive-token ${c.type}"
                      data-token-idx="${y}"
                      draggable="${s?"false":"true"}">
                    <span class="token-icon">${T}</span>
                    <span class="token-label">${_}</span>
                </span>
            `}).join("")}}function I(){const u=document.getElementById("archive-field-palette");if(!u)return;const c=["date","seller","category","amount","invoice","buyer","sep"];u.innerHTML=c.map(y=>{const $=f[y],T=l[y]||"";return`
                <button class="archive-palette-btn ${y}" data-add-field="${y}" ${s?"disabled":""}>
                    <span class="token-icon">${T}</span>
                    <span>${escapeHtml(t($.label))}</span>
                </button>
            `}).join("")}function U(){document.querySelectorAll('input[name="folder-strategy"]').forEach(u=>{u.checked=u.value===a,u.disabled=s})}async function N(){const u=document.getElementById("archive-preview-name"),c=document.getElementById("archive-preview-hint");if(c&&(c.textContent=t("archive-preview-hint",{category:h()})),!!u){if(e.length===0){u.textContent="-";return}try{const $=await(await fetch("/api/archive/rename-preview",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({merged_fields:o().merged_fields,name_template:e})})).json();u.textContent=($.name||"-")+".pdf"}catch{u.textContent="("+t("archive-preview-error")+")"}}}window._rerenderArchiveAll=function(){const u=document.getElementById("archive-rule-modal");!u||u.style.display==="none"||(S(),I(),N())};let M=-1;document.addEventListener("dragstart",u=>{const c=u.target.closest(".archive-token");!c||s||(M=parseInt(c.dataset.tokenIdx,10),c.classList.add("dragging"),u.dataTransfer.effectAllowed="move")}),document.addEventListener("dragend",u=>{document.querySelectorAll(".archive-token").forEach(c=>c.classList.remove("dragging","drop-target")),M=-1}),document.addEventListener("dragover",u=>{const c=u.target.closest(".archive-token");c&&(u.preventDefault(),u.dataTransfer.dropEffect="move",document.querySelectorAll(".archive-token").forEach(y=>y.classList.remove("drop-target")),c.classList.add("drop-target"))}),document.addEventListener("drop",u=>{const c=u.target.closest(".archive-token");if(!c||M<0||s)return;u.preventDefault();const y=parseInt(c.dataset.tokenIdx,10);if(y===M)return;const $=e.splice(M,1)[0];e.splice(y,0,$),M=-1,S(),N()}),document.addEventListener("click",u=>{if(u.target.closest("#btn-open-archive-rule")||u.target.closest("#btn-open-archive-rule-from-settings")){const T=document.getElementById("archive-rule-modal");T&&(T.style.display="",B());return}if(u.target.closest("#archive-rule-modal-close")||u.target.id==="archive-rule-modal"){const T=document.getElementById("archive-rule-modal");T&&(T.style.display="none");return}const c=u.target.closest(".settings-nav-item");if(c){switchSettingsTab(c.dataset.settingsTab);return}if(s&&u.target.closest(".archive-token, [data-add-field], #btn-archive-save, #btn-archive-reset")){showToast(t("feature-contact-us"),"info");return}const y=u.target.closest("[data-add-field]");if(y){const T=y.dataset.addField,_=f[T],E={type:T,..._.defaultCfg};e.push(E),S(),N();return}const $=u.target.closest(".archive-token");if($&&!s){L(parseInt($.dataset.tokenIdx,10));return}if(u.target.closest("#btn-archive-save"))return W();if(u.target.closest("#btn-archive-reset"))return P();(u.target.closest("#archive-token-close")||u.target.id==="archive-token-modal")&&(document.getElementById("archive-token-modal").style.display="none"),u.target.closest("#btn-archive-token-ok")&&z(),u.target.closest("#btn-archive-token-delete")&&V()}),document.addEventListener("change",u=>{u.target.name==="folder-strategy"&&(a=u.target.value)});function L(u){n=u;const c=e[u];if(!c)return;const y=document.getElementById("archive-token-body");let $="";c.type==="date"?$=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-date-format"))}</label>
                    <select class="form-input" id="token-date-format">
                        <option value="YYYY-MM-DD" ${c.format==="YYYY-MM-DD"?"selected":""}>YYYY-MM-DD (2026-04-15)</option>
                        <option value="YYYYMMDD"   ${c.format==="YYYYMMDD"?"selected":""}>YYYYMMDD (20260415)</option>
                        <option value="YY.MM"      ${c.format==="YY.MM"?"selected":""}>YY.MM (26.04)</option>
                        <option value="YYYY年MM月" ${c.format==="YYYY年MM月"?"selected":""}>YYYY年MM月 (2026年04月)</option>
                    </select>
                </div>`:c.type==="seller"?$=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-seller-short" ${c.short?"checked":""}> ${escapeHtml(t("archive-seller-short"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-seller-short-hint"))}</div>
                </div>`:c.type==="amount"?$=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-amount-currency" ${c.with_currency?"checked":""}> ${escapeHtml(t("archive-amount-currency"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-amount-currency-hint"))}</div>
                </div>`:c.type==="sep"?$=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-sep-val"))}</label>
                    <div class="sep-options">
                        <button type="button" class="sep-chip ${c.val==="_"?"active":""}" data-sep="_">_ (下划线)</button>
                        <button type="button" class="sep-chip ${c.val==="-"?"active":""}" data-sep="-">- (短横)</button>
                        <button type="button" class="sep-chip ${c.val===" "?"active":""}" data-sep=" ">(空格)</button>
                        <input type="text" id="token-sep-custom" class="form-input sep-custom" maxlength="3" placeholder="${escapeHtml(t("archive-sep-custom"))}" value="${["_","-"," "].includes(c.val)?"":escapeHtml(c.val||"")}">
                    </div>
                </div>`:$=`<div class="form-hint">${escapeHtml(t("archive-token-no-option"))}</div>`,y.innerHTML=$,document.getElementById("archive-token-modal").style.display="",y.querySelectorAll(".sep-chip").forEach(T=>{T.addEventListener("click",()=>{y.querySelectorAll(".sep-chip").forEach(E=>E.classList.remove("active")),T.classList.add("active");const _=document.getElementById("token-sep-custom");_&&(_.value="")})})}function z(){const u=e[n];if(u){if(u.type==="date")u.format=document.getElementById("token-date-format").value;else if(u.type==="seller")u.short=document.getElementById("token-seller-short").checked;else if(u.type==="amount")u.with_currency=document.getElementById("token-amount-currency").checked;else if(u.type==="sep"){const c=document.querySelector("#archive-token-body .sep-chip.active"),y=document.getElementById("token-sep-custom").value;u.val=y||(c?c.dataset.sep:"_")}document.getElementById("archive-token-modal").style.display="none",S(),N()}}function V(){n<0||(e.splice(n,1),document.getElementById("archive-token-modal").style.display="none",S(),N())}async function W(){if(e.length===0){showToast(t("archive-rule-cannot-empty"),"error");return}try{if(!(await fetch("/api/archive/settings",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({name_template:e,folder_strategy:a})})).ok)throw new Error("save failed");showToast(t("archive-save-ok"),"success");const c=document.getElementById("archive-rule-modal");c&&(c.style.display="none")}catch{showToast(t("archive-save-fail"),"error")}}async function P(){await showConfirm(t("archive-reset-confirm"),{danger:!0})&&(e=[{type:"date",format:"YYYY-MM-DD"},{type:"sep",val:"_"},{type:"seller",short:!0},{type:"sep",val:"_"},{type:"category"},{type:"sep",val:"_"},{type:"amount",with_currency:!0}],a="by_month_seller",S(),U(),N())}})();(function(){const s="pearnly_big_batch_tip_shown";let l=null,f=null,h=0,x=0,o=!1;function p(L){const z=typeof t=="function"?t("big-batch-unload-warn"):"Batch OCR running · close anyway?";return L.preventDefault(),L.returnValue=z,z}function w(){o||(o=!0,window.addEventListener("beforeunload",p))}function g(){o&&(o=!1,window.removeEventListener("beforeunload",p))}function B(){if(document.getElementById("big-batch-progress"))return;const L=document.getElementById("file-list");if(!L||!L.parentNode)return;const z=document.createElement("div");z.id="big-batch-progress",z.className="big-batch-progress",z.innerHTML='<div class="bbp-row"><svg class="bbp-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.5"/><path d="M8 4.5v3.5l2.5 1.5"/></svg><span class="bbp-text" id="bbp-text"></span></div><div class="bbp-track"><div class="bbp-fill" id="bbp-fill" style="width:0%"></div></div>',L.parentNode.insertBefore(z,L);const V=document.getElementById("bbp-text");V&&(V.textContent=typeof t=="function"?t("big-batch-progress-init"):"Starting...")}function S(){const L=document.getElementById("big-batch-progress");L&&L.remove()}function I(){if(!f)return;let L=0;for(let $=0;$<f.length;$++){const T=f[$].status;(T==="success"||T==="error"||T==="cancelled")&&L++}const z=h,V=z>0?Math.min(100,Math.floor(100*L/z)):0,W=(Date.now()-x)/1e3;let P;if(L>=3&&W>1){const $=W/L;P=(z-L)*$}else P=(z-L)*6/6;const u=Math.max(1,Math.ceil(P/60)),c=document.getElementById("bbp-fill"),y=document.getElementById("bbp-text");c&&(c.style.width=V+"%"),y&&(L>=z?y.textContent=t("big-batch-progress-done").replace("{total}",z):y.textContent=t("big-batch-progress-running").replace("{done}",L).replace("{total}",z).replace("{min}",u))}function U(L){try{if(localStorage.getItem(s)==="1")return}catch{}const z=Math.max(1,Math.ceil(L*6/6/60)),V=t("big-batch-first-tip").replace("{n}",L).replace("{min}",z);typeof showToast=="function"&&showToast(V,"info",8e3);try{localStorage.setItem(s,"1")}catch{}}function N(L){!L||L.length<100||(f=L,h=L.length,x=Date.now(),B(),w(),U(h),l&&clearInterval(l),l=setInterval(I,250),I())}function M(){l&&(clearInterval(l),l=null),g(),f&&h>=100?(I(),setTimeout(S,1200)):S(),f=null,h=0}window._bigBatchStart=N,window._bigBatchStop=M,typeof window.subscribeI18n=="function"&&window.subscribeI18n("big-batch-progress",function(){f&&I()})})();(function(){let e=null,a=!1,n=!1;function s(c){return typeof escapeHtml=="function"?escapeHtml(c==null?"":String(c)):String(c??"")}function l(c,y){try{typeof showToast=="function"&&showToast(c,y||"info")}catch{}}function f(){const c=typeof _userInfo<"u"?_userInfo:null;return!!(c&&(c.role==="owner"||c.is_super_admin))}function h(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function x(c){if(!c)return!1;const y=String(c.status||"").toLowerCase();return y==="exception"||y==="exception_pending"||y==="rejected"}async function o(c){if(a&&!c)return e;const y=localStorage.getItem("mrpilot_token");if(!y)return null;try{const $=await fetch("/api/erp/xero/status",{headers:{Authorization:"Bearer "+y}});if(!$.ok)throw new Error("http_"+$.status);e=await $.json(),a=!0}catch{e={configured:!1,connected:!1,organisations:[]},a=!1}return e}function p(){const c=document.getElementById("erp-connect-cards");if(!c)return;const y=e;let $,T=!1;y?y.configured?y.connected?(T=!0,$='<span class="mrerp-card-pill mrerp-pill-ok">'+s(t("xero-card-connected"))+"</span>"):$='<span class="mrerp-card-pill mrerp-pill-neutral">'+s(t("xero-card-not-connected"))+"</span>":$='<span class="mrerp-card-pill mrerp-pill-neutral">'+s(t("xero-card-not-configured"))+"</span>":$='<span class="mrerp-card-pill mrerp-pill-neutral">'+s(t("xero-card-not-connected"))+"</span>";let _="";if(!y||!y.configured)_='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+s(t("xero-connect-btn"))+"</button>";else if(!y.connected)f()&&(_='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+s(t("xero-connect-btn"))+"</button>");else{const R=!!y.auto_push,k=R?t("card-btn-disable"):t("card-btn-enable");_='<button type="button" class="'+(R?"mrerp-card-toggle mrerp-card-toggle-disable":"mrerp-card-toggle mrerp-card-toggle-enable")+'" id="btn-xero-toggle-enabled" data-xero-enabled="'+(R?"1":"0")+'" title="'+s(R?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip"))+'">'+s(k)+'</button><button type="button" class="int-btn-configure" id="btn-xero-edit-toggle">'+s(t("card-btn-edit"))+"</button>"}const E=y&&y.connected?"xero-card-desc-connected":"xero-card-desc-default",D=y&&y.connected?t("xero-card-connected")||"Connected · default org will receive pushes":"Cloud accounting · push invoices to your default Xero org",J=(function(){const R=t(E);return R===E?D:R})();let F='<div class="integration-row erp-connect-xero'+(T?" connected":"")+'"><div class="int-icon ic-xero"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="9" cy="10" r="1.3" fill="currentColor"/><circle cx="15" cy="14" r="1.3" fill="currentColor"/><path d="M9 14l6-4"/></svg></div><div class="int-info"><div class="int-name"><span>'+s(t("xero-card-title")||"Xero")+"</span>"+$+'</div><div class="int-desc">'+s(J)+'</div></div><div class="int-actions">'+_+"</div></div>";if(y&&y.configured&&y.connected&&f()){const R=y.organisations||[];let k="";if(R.length>0){k+='<div class="erp-cc-meta">'+s((t("xero-org-count")||"").replace("{n}",String(R.length)))+"</div>",k+='<div class="erp-cc-org-label">'+s(t("xero-default-org"))+":</div>",k+='<div class="erp-cc-orgs">',R.forEach(function(ee){k+='<label class="erp-cc-org-row"><input type="radio" name="xero-default-org" value="'+s(ee.id)+'"'+(ee.is_default?" checked":"")+'><span class="erp-cc-org-name">'+s(ee.organisation_name||ee.organisation_id)+"</span></label>"}),k+="</div>";const Y=!!y.auto_push,X=Y?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip");k+='<div class="erp-cc-auto-push" title="'+s(X)+'"><label class="erp-cc-toggle"><input type="checkbox" id="xero-auto-push-toggle"'+(Y?" checked":"")+'><span class="erp-cc-toggle-slider"></span><span class="erp-cc-toggle-label">'+s(t("erp-auto-push-label"))+"</span></label></div>",k+='<div class="erp-cc-actions"><button class="btn btn-ghost btn-tiny" type="button" id="btn-xero-disconnect">'+s(t("xero-disconnect-btn"))+"</button></div>"}F+='<div class="erp-xero-details" id="erp-xero-details" style="display:none; margin:8px 0 16px; padding:12px 14px; border:1px solid var(--line); border-radius:8px; background:var(--bg);">'+k+"</div>"}const Q=c.querySelector(".erp-connect-xero"),ie=c.querySelector("#erp-xero-details");ie&&ie.remove(),Q?Q.outerHTML=F:c.insertAdjacentHTML("afterbegin",F);const le=document.getElementById("btn-xero-edit-toggle");le&&le.addEventListener("click",function(R){R.preventDefault();const k=document.getElementById("erp-xero-details");k&&(k.style.display=k.style.display==="none"?"":"none")});const ue=document.getElementById("btn-xero-toggle-enabled");ue&&ue.addEventListener("click",async function(R){if(R.preventDefault(),ue.disabled)return;const Y=!(ue.getAttribute("data-xero-enabled")==="1");if(!Y)try{if(!await window.pearnlyConfirm(t("card-toggle-disable-confirm")))return}catch{}ue.disabled=!0,await S(Y,null)})}async function w(){const c=localStorage.getItem("mrpilot_token");if(c)try{const y=await fetch("/api/erp/xero/auth/start",{method:"GET",headers:{Authorization:"Bearer "+c}});if(!y.ok){let T="unknown";try{T=(await y.json()).detail||"unknown"}catch{}const _=String(T).replace(/^xero\./,"").toLowerCase();l(t("xero-push-fail").replace("{err}",t("xero-err-"+_)||T),"error");return}const $=await y.json();$.redirect_url&&(window.location.href=$.redirect_url)}catch(y){l(t("xero-push-fail").replace("{err}",y.message||"network"),"error")}}async function g(){if(!await window.pearnlyConfirm(t("xero-disconnect-confirm")))return;const y=localStorage.getItem("mrpilot_token");try{const $=await fetch("/api/erp/xero/disconnect",{method:"POST",headers:{Authorization:"Bearer "+y}});if(!$.ok)throw new Error("http_"+$.status);await o(!0),p()}catch($){l(t("xero-push-fail").replace("{err}",$.message),"error")}}async function B(c){const y=localStorage.getItem("mrpilot_token");try{const $=await fetch("/api/erp/xero/select_org",{method:"POST",headers:{Authorization:"Bearer "+y,"Content-Type":"application/json"},body:JSON.stringify({token_id:c})});if(!$.ok)throw new Error("http_"+$.status);await o(!0),p()}catch($){l(t("xero-push-fail").replace("{err}",$.message),"error")}}async function S(c,y){const $=localStorage.getItem("mrpilot_token");y&&(y.disabled=!0);try{const T=await fetch("/api/erp/xero/auto-push",{method:"POST",headers:{Authorization:"Bearer "+$,"Content-Type":"application/json"},body:JSON.stringify({on:!!c})});if(!T.ok){let _="unknown";try{_=(await T.json()).detail||"unknown"}catch{}throw new Error(_)}l(c?t("erp-auto-push-toggled-on"):t("erp-auto-push-toggled-off"),"success"),a=!1,await o(!0),p()}catch(T){y&&(y.checked=!c),l(t("erp-auto-push-toggle-fail").replace("{err}",T.message||"network"),"error")}finally{y&&(y.disabled=!1)}}async function I(){const c=document.getElementById("drawer-history-save");if(!c||c.querySelector("#btn-xero-push")||c.querySelector("#pn-push-wrap")||(await o(!1),c.querySelector("#pn-push-wrap"))||c.querySelector("#btn-xero-push"))return;const y=h();if(!(y&&(y._historyId||y.history_id)))return;let T=!1,_="xero-push-tip";!e||!e.configured?(T=!0,_="xero-err-not_configured"):e.connected?x(y)&&(T=!0,_="xero-push-disabled-exc"):(T=!0,_="xero-push-disabled-no-conn");const E=document.createElement("button");E.type="button",E.id="btn-xero-push",E.className="btn btn-ghost"+(T?" disabled":""),E.disabled=T,E.title=t(_)||"",E.innerHTML='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5 8l2 2 4-4"/></svg><span style="margin-left:4px;">'+s(t("xero-push-btn"))+"</span>",E.addEventListener("click",U);const D=document.getElementById("btn-push-erp");D&&D.parentNode?D.parentNode.insertBefore(E,D.nextSibling):c.insertBefore(E,c.firstChild)}async function U(){const c=h(),y=c&&(c._historyId||c.history_id);if(!y)return;const $=document.getElementById("btn-xero-push");$&&($.disabled=!0,$.classList.add("loading"));const T=localStorage.getItem("mrpilot_token");try{const _=await fetch("/api/erp/xero/push/"+encodeURIComponent(y),{method:"POST",headers:{Authorization:"Bearer "+T}});if(!_.ok){let E="unknown";try{E=(await _.json()).detail||"unknown"}catch{}const D=String(E).replace(/^xero\./,"").toLowerCase(),J=t("xero-"+D),F=J&&J!=="xero-"+D?J:E;l(t("xero-push-fail").replace("{err}",F),"error");return}l(t("xero-push-ok"),"success")}catch(_){l(t("xero-push-fail").replace("{err}",_.message||"network"),"error")}finally{$&&($.disabled=!1,$.classList.remove("loading"))}}async function N(){await o(!0),p(),M()}async function M(){const c=document.getElementById("erp-global-push-mode");if(!c)return;const y=localStorage.getItem("mrpilot_token");if(y)try{const $=await fetch("/api/settings/erp-push-mode",{headers:{Authorization:"Bearer "+y}});if($.ok){const T=await $.json();T.mode&&(c.value=T.mode,c.dataset.prev=T.mode)}}catch{}}async function L(c){const y=c.value,$=localStorage.getItem("mrpilot_token");try{(await fetch("/api/settings/erp-push-mode",{method:"PUT",headers:{Authorization:"Bearer "+$,"Content-Type":"application/json"},body:JSON.stringify({mode:y})})).ok?(c.dataset.prev=y,l(t("pref-erp-mode-saved"),"success")):(c.value=c.dataset.prev||"smart",l(t("pref-save-failed"),"error"))}catch{c.value=c.dataset.prev||"smart",l(t("pref-save-failed"),"error")}}function z(){try{const c=String(window.location.hash||"");if(c.indexOf("xero=ok")>=0){const y=c.match(/n=(\d+)/),$=y?y[1]:"1";l((t("xero-toast-redirected-ok")||"").replace("{n}",$),"success"),history.replaceState(null,"",window.location.pathname+"#automation"),o(!0).then(p)}else c.indexOf("xero=err")>=0&&(l(t("xero-toast-redirected-err"),"error"),history.replaceState(null,"",window.location.pathname+"#automation"))}catch{}}function V(){if(n)return;n=!0,document.addEventListener("click",function(y){if(y.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(N,50);return}if(y.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(N,80);return}if(y.target.closest("#btn-xero-connect")){y.preventDefault(),w();return}if(y.target.closest("#btn-xero-disconnect")){y.preventDefault(),g();return}}),document.addEventListener("change",function(y){y.target&&y.target.matches('input[name="xero-default-org"]')&&B(y.target.value),y.target&&y.target.id==="xero-auto-push-toggle"&&S(y.target.checked,y.target),y.target&&y.target.id==="erp-global-push-mode"&&L(y.target)});const c=function(){return document.getElementById("drawer-body")};try{const y=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("btn-xero-push")&&I()}),$=c();if($)y.observe($,{childList:!0,subtree:!0});else{const T=new MutationObserver(function(){const _=c();_&&(y.observe(_,{childList:!0,subtree:!0}),T.disconnect())});T.observe(document.body,{childList:!0,subtree:!0})}}catch{}setTimeout(z,500)}function W(){e&&p();const c=document.getElementById("btn-xero-push");if(c){const y=c.querySelector("span");y&&(y.textContent=t("xero-push-btn"))}}V(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("xero-adapter",W);async function P(c){const y=Date.now();for(;Date.now()-y<c;){if(typeof _userInfo<"u"&&_userInfo&&_userInfo.id)return _userInfo;await new Promise($=>setTimeout($,80))}return null}async function u(){await P(5e3);const c=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),y=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');c&&y&&await N()}setTimeout(u,200)})();(function(){const e={};function a(){if(document.getElementById("report-modal"))return;const p=`
        <div class="report-modal-overlay" id="report-modal" style="display:none;">
            <div class="report-modal">
                <div class="report-modal-head">
                    <span class="report-modal-title" data-i18n="report-modal-title">导出报表</span>
                    <button class="report-modal-close-x" id="report-modal-close-x" aria-label="close">
                        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 6l8 8M14 6l-8 8"/></svg>
                    </button>
                </div>
                <div class="report-modal-body">
                    <div class="report-section">
                        <div class="report-section-title" data-i18n="report-section-template">选择模板</div>
                        <div class="report-tpl-list" id="report-tpl-list">
                            <!-- 动态填充 -->
                        </div>
                    </div>
                    <div class="report-section" id="report-period-section">
                        <div class="report-section-title" data-i18n="report-section-period">时间范围</div>
                        <div class="report-period-list">
                            <label class="report-period-item">
                                <input type="radio" name="report-period" value="all" checked>
                                <span data-i18n="report-range-all">全部</span>
                            </label>
                            <label class="report-period-item">
                                <input type="radio" name="report-period" value="this-month">
                                <span data-i18n="report-range-this-month">本月</span>
                            </label>
                            <label class="report-period-item">
                                <input type="radio" name="report-period" value="last-month">
                                <span data-i18n="report-range-last-month">上月</span>
                            </label>
                            <label class="report-period-item">
                                <input type="radio" name="report-period" value="this-quarter">
                                <span data-i18n="report-range-this-quarter">本季度</span>
                            </label>
                            <label class="report-period-item">
                                <input type="radio" name="report-period" value="this-year">
                                <span data-i18n="report-range-this-year">今年</span>
                            </label>
                        </div>
                    </div>
                </div>
                <div class="report-modal-foot">
                    <button class="btn btn-ghost" id="report-modal-cancel" data-i18n="report-modal-cancel">取消</button>
                    <button class="btn btn-primary" id="report-modal-download">
                        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10 3v10M6 9l4 4 4-4M4 15v2h12v-2"/></svg>
                        <span data-i18n="report-modal-download">下载 Excel</span>
                    </button>
                </div>
            </div>
        </div>`,w=document.createElement("div");w.innerHTML=p,document.body.appendChild(w.firstElementChild),document.getElementById("report-modal-close-x").addEventListener("click",n),document.getElementById("report-modal-cancel").addEventListener("click",n),document.getElementById("report-modal").addEventListener("click",g=>{g.target.id==="report-modal"&&n()})}function n(){const p=document.getElementById("report-modal");p&&(p.style.display="none"),s=null}let s=null;async function l(p,w){const g=p+":"+(w||"");if(e[g])return e[g];let B;try{const S=localStorage.getItem("mrpilot_token"),I=await fetch(`/api/reports/templates?lang=${encodeURIComponent(p)}`,{headers:{Authorization:"Bearer "+S}});if(!I.ok)throw new Error("templates fetch failed");B=(await I.json()).templates||[]}catch(S){console.error("fetchTemplates fail",S),B=[{code:"input_vat",name:t("tpl-input-vat"),desc:t("tpl-input-vat-desc"),recommended:!0},{code:"standard",name:t("tpl-standard"),desc:t("tpl-standard-desc"),recommended:!1},{code:"print",name:t("tpl-print"),desc:t("tpl-print-desc"),recommended:!1}]}if(B=B.filter(S=>S.code!=="erp"),w==="history-batch"){const S=B.findIndex(U=>U.code==="standard"),I=S>=0?S+1:B.length;B.splice(I,0,{code:"sales_detail_th",name:t("export-tpl-sales-detail"),desc:t("export-tpl-sales-detail-desc"),recommended:!1,is_new:!0})}return e[g]=B,B}function f(p){const w=document.getElementById("report-tpl-list"),g=p.map((S,I)=>`
            <label class="report-tpl-item${S.recommended?" is-recommended":""}">
                <input type="radio" name="report-tpl" value="${S.code}" ${S.recommended||I===0?"checked":""}>
                <div class="report-tpl-content">
                    <div class="report-tpl-name">
                        ${h(S.name)}
                        ${S.recommended?`<span class="report-tpl-badge">${h(t("report-recommended"))}</span>`:""}
                    </div>
                    <div class="report-tpl-desc">${h(S.desc||"")}</div>
                </div>
            </label>
        `).join(""),B=`
            <label class="report-tpl-item report-tpl-coming" title="${h(t("tpl-custom-coming"))}">
                <input type="radio" name="report-tpl" disabled>
                <div class="report-tpl-content">
                    <div class="report-tpl-name">
                        + ${h(t("tpl-custom-new"))}
                        <span class="report-tpl-badge report-tpl-badge-soon">${h(t("cs-coming-soon"))}</span>
                    </div>
                    <div class="report-tpl-desc">${h(t("tpl-custom-desc"))}</div>
                </div>
            </label>
        `;w.innerHTML=g+B}function h(p){return p==null?"":String(p).replace(/[&<>"']/g,w=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[w])}function x(p){const w=new Date,g=w.getFullYear(),B=w.getMonth()+1;if(p==="all")return"all";if(p==="this-month")return`${g}-${String(B).padStart(2,"0")}`;if(p==="last-month"){const S=new Date(g,B-2,1);return`${S.getFullYear()}-${String(S.getMonth()+1).padStart(2,"0")}`}return p==="this-year"?`${g}`:p==="this-quarter"?`${g}-Q${Math.floor((B-1)/3)+1}`:"all"}window.openReportModal=async function(p){p=p||{},a(),typeof applyLang=="function"?applyLang(currentLang):document.querySelectorAll("#report-modal [data-i18n]").forEach(U=>{const N=U.getAttribute("data-i18n");I18N[currentLang]&&I18N[currentLang][N]&&(U.textContent=I18N[currentLang][N])});const w=document.getElementById("report-period-section");w&&(w.style.display=p.mode==="client"?"":"none");const g=document.getElementById("report-tpl-list");g.innerHTML=`<div class="report-tpl-loading">${h(t("report-modal-loading"))}</div>`,document.getElementById("report-modal").style.display="";const B=await l(currentLang,p&&p.mode);f(B),s=p;const S=document.getElementById("report-modal-download"),I=S.cloneNode(!0);S.parentNode.replaceChild(I,S),I.addEventListener("click",()=>o(s))};async function o(p){if(!p)return;const w=document.querySelector('input[name="report-tpl"]:checked');if(!w){showToast(t("report-toast-no-selection"),"info");return}const g=w.value,B=document.querySelector('input[name="report-period"]:checked'),S=B?B.value:"all",I=x(S),U=document.getElementById("report-modal-download"),N=U.innerHTML;U.disabled=!0,U.innerHTML=`<span>${h(t("report-modal-loading"))}</span>`;try{const M=localStorage.getItem("mrpilot_token");let L,z;if(p.mode==="records")L=await fetch("/api/reports/export",{method:"POST",headers:{Authorization:"Bearer "+M,"Content-Type":"application/json"},body:JSON.stringify({template:g,lang:currentLang,records:p.records||[],meta:p.meta||{}})}),z=`mrpilot-${g}-${Date.now()}.xlsx`;else if(p.mode==="client"){const $=`/api/reports/clients/${p.clientId}/export?template=${encodeURIComponent(g)}&lang=${encodeURIComponent(currentLang)}&month=${encodeURIComponent(I)}`;L=await fetch($,{headers:{Authorization:"Bearer "+M}}),z=`${(p.clientName||"client").replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40)}-${g}.xlsx`}else if(p.mode==="history-batch")g==="sales_detail_th"?(L=await fetch("/api/ocr/export-by-history-ids",{method:"POST",headers:{Authorization:"Bearer "+M,"Content-Type":"application/json"},body:JSON.stringify({template:"sales_detail_th",lang:currentLang,history_ids:p.historyIds||[],client_id:p.clientId||null})}),z=`Pearnly_SalesDetail_${Date.now()}.xlsx`):(L=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+M,"Content-Type":"application/json"},body:JSON.stringify({template:g,lang:currentLang,history_ids:p.historyIds||[],client_id:p.clientId||null})}),z=`mrpilot-batch-${g}-${Date.now()}.xlsx`);else throw new Error("unknown mode: "+p.mode);if(!L.ok){let $="HTTP "+L.status;try{const T=await L.json();T&&T.detail&&($=T.detail)}catch(T){console.warn("[batch-export] resp.json err.detail parse failed:",T)}L.status===404?showToast(t("report-toast-empty"),"info"):showToast(t("report-toast-fail")+" · "+$,"error");return}const V=await L.blob();let W=z;const u=(L.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(u)try{W=decodeURIComponent(u[1])}catch{}const c=URL.createObjectURL(V),y=document.createElement("a");y.href=c,y.download=W,document.body.appendChild(y),y.click(),document.body.removeChild(y),URL.revokeObjectURL(c),showToast(t("report-toast-success"),"success"),n()}catch(M){console.error("doDownload fail",M),showToast(t("report-toast-fail")+" · "+(M.message||""),"error")}finally{U.disabled=!1,U.innerHTML=N}}document.addEventListener("DOMContentLoaded",()=>{const p=document.getElementById("btn-export");if(p){const g=p.cloneNode(!0);p.parentNode.replaceChild(g,p),g.addEventListener("click",()=>{if(typeof _results>"u"||!_results||_results.length===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"records",records:_results.map(B=>({filename:B.filename,merged_fields:B.merged_fields||{}}))})})}const w=document.getElementById("history-batch-export");w&&w.addEventListener("click",()=>{if(typeof _historySelected>"u"||_historySelected.size===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"history-batch",historyIds:Array.from(_historySelected)})})}),window.openClientExportModal=function(p,w){openReportModal({mode:"client",clientId:p,clientName:w||""})}})();(function(){const a=typeof window<"u"&&"showDirectoryPicker"in window,n=/\.(pdf|jpe?g|png|webp)$/i,s="mrpilot_folder_watcher",l=1;let f=null,h=null,x=null,o=60,p=!1,w=!1,g=0,B=0,S=0,I=[],U=null,N=!1;function M(){return f||(f=new Promise((i,v)=>{const b=indexedDB.open(s,l);b.onupgradeneeded=j=>{const H=j.target.result;H.objectStoreNames.contains("handles")||H.createObjectStore("handles"),H.objectStoreNames.contains("seen")||H.createObjectStore("seen"),H.objectStoreNames.contains("config")||H.createObjectStore("config")},b.onsuccess=j=>i(j.target.result),b.onerror=j=>v(j.target.error)}),f)}function L(i,v){return M().then(b=>new Promise((j,H)=>{const C=b.transaction(i,"readonly").objectStore(i).get(v);C.onsuccess=()=>j(C.result),C.onerror=()=>H(C.error)}))}function z(i,v,b){return M().then(j=>new Promise((H,r)=>{const C=j.transaction(i,"readwrite");C.objectStore(i).put(b,v),C.oncomplete=()=>H(),C.onerror=()=>r(C.error)}))}function V(i,v){return M().then(b=>new Promise((j,H)=>{const r=b.transaction(i,"readwrite");r.objectStore(i).delete(v),r.oncomplete=()=>j(),r.onerror=()=>H(r.error)}))}function W(i){return M().then(v=>new Promise((b,j)=>{const H=v.transaction(i,"readwrite");H.objectStore(i).clear(),H.oncomplete=()=>b(),H.onerror=()=>j(H.error)}))}async function P(i){if(!i)return!1;try{const v={mode:"read"};let b=await i.queryPermission(v);return b==="granted"?!0:(b=await i.requestPermission(v),b==="granted")}catch(v){return console.warn("[folder] permission check failed:",v),!1}}function u(i,v){const b=document.getElementById("folder-status-summary");b&&(b.setAttribute("data-i18n",i),b.textContent=t(i),b.className="auto-status-pill"+(v?" "+v:""))}function c(i){["folder-unsupported","folder-empty","folder-active"].forEach(v=>{const b=document.getElementById(v);b&&(b.style.display=v===i?"":"none")})}function y(i){if(!i)return"-";const v=i instanceof Date?i:new Date(i),b=String(v.getHours()).padStart(2,"0"),j=String(v.getMinutes()).padStart(2,"0"),H=String(v.getSeconds()).padStart(2,"0");return`${b}:${j}:${H}`}function $(){c("folder-active");const i=document.getElementById("folder-config-path");i&&h&&(i.textContent=h.name||"-");const v=document.getElementById("folder-interval-select");v&&(v.value=String(o)),document.getElementById("folder-stat-last").textContent=U?y(U):"-",document.getElementById("folder-stat-processed").textContent=String(g),document.getElementById("folder-stat-failed").textContent=String(B),document.getElementById("folder-stat-queue").textContent=String(S);const b=document.getElementById("btn-folder-pause"),j=document.getElementById("btn-folder-resume");b&&(b.style.display=p?"none":""),j&&(j.style.display=p?"":"none"),p?u("folder-status-paused","paused"):u("folder-status-running","running");const H=document.getElementById("folder-status-text");H&&(H.setAttribute("data-i18n",p?"folder-status-paused":"folder-status-running"),H.textContent=t(p?"folder-status-paused":"folder-status-running"));const r=document.getElementById("folder-status-pulse");r&&(r.className="folder-status-pulse"+(p?" paused":"")),T()}function T(){const i=document.getElementById("folder-recent-list");if(i){if(I.length===0){i.innerHTML=`<div class="folder-recent-empty">${escapeHtml(t("folder-recent-empty"))}</div>`;return}i.innerHTML=I.slice(0,20).map(v=>{let b;v.status==="ok"?b=`<span class="folder-recent-icon ok">${svgIcon("check",12)}</span>`:v.status==="dup"?b=`<span class="folder-recent-icon dup" title="${escapeHtml(t("folder-recent-dup"))}">${svgIcon("copy",12)}</span>`:v.status==="skip"?b=`<span class="folder-recent-icon skip" title="${escapeHtml(t("folder-recent-skip"))}">${svgIcon("minus",12)}</span>`:b=`<span class="folder-recent-icon fail">${svgIcon("alert",12)}</span>`;const j=v.status==="fail"&&v.error?v.error:v.status==="dup"&&v.reason||v.status==="skip"&&v.reason?v.reason:"",H=j?`<div class="folder-recent-err">${escapeHtml(j)}</div>`:"";return`
                <div class="folder-recent-item">
                    ${b}
                    <div class="folder-recent-body">
                        <div class="folder-recent-name">${escapeHtml(v.name)}</div>
                        ${H}
                    </div>
                    <div class="folder-recent-time">${y(v.time)}</div>
                </div>
            `}).join("")}}function _(i){I.unshift(i),I.length>50&&(I.length=50),z("config","recent_list",I).catch(()=>{})}async function E(i){const v=new FormData;v.append("file",i,i.name),v.append("source","folder");const b=await fetch("/api/ocr/recognize?source=folder",{method:"POST",headers:{Authorization:"Bearer "+token,"X-Source":"folder"},body:v});if(!b.ok){let j="http_"+b.status;try{const H=await b.json();j=H&&H.detail?typeof H.detail=="string"?H.detail:H.detail.code||JSON.stringify(H.detail):j}catch{}throw new Error(j)}return await b.json()}async function D(i){try{const b=(await i.getFile()).size;return await new Promise(H=>setTimeout(H,3e3)),(await i.getFile()).size===b&&b>0}catch{return!1}}async function J(i,v,b,j){if(j>10)return;let H;try{H=await i.queryPermission({mode:"read"})}catch{H="denied"}if(H==="granted")for await(const r of i.values()){const C=v?`${v}/${r.name}`:r.name;if(r.kind==="file"){if(!n.test(r.name))continue;let A;try{A=await r.getFile()}catch{continue}const O=`${C}::${A.size}::${A.lastModified}`;if(await L("seen",O))continue;b.push({entry:r,file:A,seenKey:O,relPath:C})}else if(r.kind==="directory")try{await J(r,C,b,j+1)}catch{}}}async function F(){if(!(w||p||!h)){w=!0;try{if(await h.queryPermission({mode:"read"})!=="granted"){console.warn("[folder] permission lost · stop"),ee(),showToast("warn",t("folder-permission-lost"));return}U=new Date;const v=[];await J(h,"",v,0),S=v.length,$();for(const b of v){if(p)break;if(!await D(b.entry)){S=Math.max(0,S-1),$();continue}try{let H;try{H=await b.entry.getFile()}catch{H=b.file}const r=await E(H);await z("seen",b.seenKey,{name:H.name,relPath:b.relPath,size:H.size,lastModified:H.lastModified,processed_at:Date.now()});const C=r.history_ids||(r.history_id?[r.history_id]:[]),A=r.duplicate_warnings||[],O=b.relPath||H.name;C.length>0?(g+=C.length,_({name:O,status:"ok",time:new Date,history_id:C[0],count:C.length}),await z("config","processed_count",g)):A.length>0?_({name:O,status:"dup",time:new Date,reason:t("folder-recent-dup-reason")}):_({name:O,status:"skip",time:new Date,reason:t("folder-recent-skip-reason")})}catch(H){B++,_({name:b.relPath||b.file.name,status:"fail",time:new Date,error:String(H.message||H)}),await z("config","failed_count",B)}S=Math.max(0,S-1),$()}}catch(i){console.warn("[folder] scan error:",i)}finally{w=!1,$()}}}function Q(){x&&clearInterval(x),x=setInterval(F,o*1e3)}function ie(){x&&(clearInterval(x),x=null)}function le(i){if(!h||p)return;const v=typeof t=="function"?t("folder-unload-warn"):"Folder watcher running · close anyway?";return i.preventDefault(),i.returnValue=v,v}function ue(){window._pearnlyFolderUnloadAttached||(window._pearnlyFolderUnloadAttached=!0,window.addEventListener("beforeunload",le))}function R(){window._pearnlyFolderUnloadAttached&&(window._pearnlyFolderUnloadAttached=!1,window.removeEventListener("beforeunload",le))}function k(){p=!1,Q(),ue(),$(),F()}function Y(){p=!0,ie(),R(),$()}function X(){p=!1,Q(),ue(),$(),F()}function ee(){p=!0,ie(),R()}async function re(){try{const i=await window.showDirectoryPicker({mode:"read",startIn:"documents"});if(!await P(i)){showToast("warn",t("folder-permission-denied"));return}h=i,await z("handles","main",i),g=0,B=0,S=0,I=[],await z("config","processed_count",0),await z("config","failed_count",0),await W("seen"),k()}catch(i){i&&i.name!=="AbortError"&&console.warn("[folder] pick failed:",i)}}async function de(){await showConfirm(t("folder-confirm-remove"),{danger:!0})&&(ee(),h=null,g=0,B=0,S=0,I=[],await V("handles","main"),await V("config","processed_count"),await V("config","failed_count"),await W("seen"),c("folder-empty"),u("folder-status-empty",""))}async function pe(){I=[];try{await V("config","recent_list")}catch{}T()}async function G(){if(N)return;if(N=!0,!a){c("folder-unsupported"),u("folder-status-unsupported",""),m();return}ae();let i=null;try{i=await L("handles","main")}catch{}if(!i){c("folder-empty"),u("folder-status-empty","");return}if(!await P(i)){c("folder-empty"),u("folder-status-empty",""),await V("handles","main"),showToast("warn",t("folder-permission-lost-restart"));return}h=i;try{g=await L("config","processed_count")||0}catch{}try{B=await L("config","failed_count")||0}catch{}try{const b=await L("config","recent_list");Array.isArray(b)&&(I=b.map(j=>({...j,time:j.time?new Date(j.time):new Date})))}catch{}k()}function ae(){const i=document.getElementById("btn-folder-pick"),v=document.getElementById("btn-folder-pause"),b=document.getElementById("btn-folder-resume"),j=document.getElementById("btn-folder-scan-now"),H=document.getElementById("btn-folder-remove"),r=document.getElementById("btn-folder-clear-recent"),C=document.getElementById("folder-interval-select");i&&i.addEventListener("click",re),v&&v.addEventListener("click",Y),b&&b.addEventListener("click",X),j&&j.addEventListener("click",()=>{F()}),H&&H.addEventListener("click",de),r&&r.addEventListener("click",pe),C&&C.addEventListener("change",A=>{o=parseInt(A.target.value,10)||60,p||Q()}),d()}function d(){document.querySelectorAll('[data-auto-panel="folder"] [data-tab-jump]').forEach(i=>{i.dataset.tabJumpBound||(i.dataset.tabJumpBound="1",i.addEventListener("click",v=>{const b=v.currentTarget.dataset.tabJump;if(b==="email")typeof switchAutomationTab=="function"&&switchAutomationTab("email");else if(b==="upload"){const j=document.querySelector('[data-page="recognize"]')||document.querySelector('[data-page="upload"]');j&&j.click()}}))})}function m(){d()}window._loadFolderWatcherPanel=G;function q(){try{if(navigator.userAgentData&&Array.isArray(navigator.userAgentData.brands))return navigator.userAgentData.brands.some(v=>/chromium|google chrome|microsoft edge/i.test(v.brand||""))}catch{}const i=navigator.userAgent||"";return!!(/Edg\//.test(i)||/Chrome\//.test(i)&&!/OPR\/|YaBrowser|Opera/.test(i))}function Z(){try{if(q()||localStorage.getItem("pearnly_chrome_banner_dismissed")==="1")return;const i=document.getElementById("chrome-only-banner");if(!i)return;const v=i.querySelector('[data-i18n="chrome-banner-msg"]'),b=i.querySelector('[data-i18n="chrome-banner-dismiss"]');v&&typeof t=="function"&&(v.textContent=t("chrome-banner-msg")),b&&typeof t=="function"&&(b.textContent=t("chrome-banner-dismiss")),i.style.display="";const j=document.getElementById("chrome-only-banner-close");j&&!j.dataset.bound&&(j.dataset.bound="1",j.addEventListener("click",()=>{i.style.display="none";try{localStorage.setItem("pearnly_chrome_banner_dismissed","1")}catch{}}))}catch{}}typeof document<"u"&&(document.readyState==="loading"?document.addEventListener("DOMContentLoaded",Z):setTimeout(Z,0)),window._refreshChromeBanner=Z})();(function(){let e=null,a=null,n="new",s=!1,l=!1;async function f(){const E=document.getElementById("email-empty"),D=document.getElementById("email-account-card");if(document.getElementById("email-logs-section"),!(!E||!D))try{const J=await fetch("/api/email-ingest/account",{headers:{Authorization:"Bearer "+token}});if(J.status===401){localStorage.removeItem("mrpilot_token");const Q=await J.json().catch(()=>({}));if((typeof Q.detail=="string"?Q.detail:Q.detail&&Q.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}if(!J.ok){x("none");return}const F=await J.json();e=F.account||null,a=F.presets||{},s=!0,h(),e&&y()}catch(J){console.error("[email-ingest] load failed",J),x("none")}}function h(){const E=document.getElementById("email-empty"),D=document.getElementById("email-account-card"),J=document.getElementById("email-logs-section");if(!e){E.style.display="",D.style.display="none",J&&(J.style.display="none"),x("none");return}E.style.display="none",D.style.display="",J&&(J.style.display="");const F=document.getElementById("email-account-addr"),Q=document.getElementById("email-account-host"),ie=document.getElementById("email-account-last"),le=document.getElementById("email-last-error"),ue=document.getElementById("email-enabled-toggle");if(F&&(F.textContent=e.email_address||"-"),Q&&(Q.textContent=`${e.imap_host||"-"}:${e.imap_port||993}`),ie){const R=e.last_fetched_at;if(!R)ie.textContent=t("email-last-never");else{const k=o(R),Y=!e.last_error;ie.textContent=Y?t("email-last-ok",{time:k}):t("email-last-fail",{time:k})}}le&&(e.last_error?(le.style.display="",le.textContent=p(e.last_error)):le.style.display="none"),ue&&(ue.checked=!!e.enabled),e.enabled?e.last_error?x("error"):x("on"):x("off")}function x(E){const D=document.getElementById("email-status-summary");if(!D)return;D.classList.remove("none","ready","active","coming");let J="auto-status-loading";E==="none"?(J="email-status-none",D.classList.add("none")):E==="on"?(J="email-status-on",D.classList.add("active")):E==="off"?(J="email-status-off",D.classList.add("coming")):E==="error"&&(J="email-status-error",D.classList.add("none")),D.setAttribute("data-i18n",J),D.textContent=t(J)}function o(E){if(!E)return"";const D=new Date(E);if(isNaN(D.getTime()))return"";const J=F=>String(F).padStart(2,"0");return`${J(D.getMonth()+1)}-${J(D.getDate())} ${J(D.getHours())}:${J(D.getMinutes())}`}function p(E){if(!E)return"";const D=String(E);return/auth|AUTHENTICATIONFAILED|invalid credentials/i.test(D)?t("email-test-auth-fail"):/timeout|timed out/i.test(D)?t("email.timeout"):(/ENOTFOUND|getaddrinfo/i.test(D),D)}function w(E){n=E;const D=document.getElementById("email-modal");if(!D)return;const J=document.getElementById("email-preset");J.innerHTML="";const F=a||{},Q=["gmail","outlook","yahoo","icloud","qq","163","custom"],ie={gmail:"Gmail",outlook:"Outlook / Office365",yahoo:"Yahoo Mail",icloud:"iCloud",qq:"QQ 邮箱",163:"网易 163"};Q.forEach(ae=>{if(!F[ae])return;const d=document.createElement("option");d.value=ae,d.textContent=ae==="custom"?t("email-preset-custom"):ie[ae]||ae,J.appendChild(d)});const le=document.getElementById("email-modal-title"),ue=document.getElementById("email-address"),R=document.getElementById("email-password"),k=document.getElementById("email-imap-host"),Y=document.getElementById("email-imap-port"),X=document.getElementById("email-imap-ssl"),ee=document.getElementById("email-folder"),re=document.getElementById("email-mark-read"),de=document.getElementById("email-bind-enabled"),pe=document.getElementById("email-test-result"),G=document.getElementById("email-adv-details");if(pe&&(pe.style.display="none",pe.textContent=""),E==="edit"&&e){le.setAttribute("data-i18n","email-modal-title-edit"),le.textContent=t("email-modal-title-edit"),ue.value=e.email_address||"",R.value="",R.setAttribute("data-i18n-placeholder","email-field-password-edit-ph"),R.placeholder=t("email-field-password-edit-ph"),k.value=e.imap_host||"",Y.value=e.imap_port||993,X.checked=e.imap_use_ssl!==!1,ee.value=e.folder||"INBOX",re.checked=e.mark_as_read!==!1,de.checked=e.enabled!==!1;const ae=document.getElementById("email-filter-sender"),d=document.getElementById("email-filter-subject");ae&&(ae.value=e.filter_sender||""),d&&(d.value=e.filter_subject||""),L(e.interval_min||15),J.value=U(e.imap_host)||"custom",G&&(G.open=!0)}else{le.setAttribute("data-i18n","email-modal-title-new"),le.textContent=t("email-modal-title-new"),ue.value="",R.value="",R.setAttribute("data-i18n-placeholder","email-field-password-ph"),R.placeholder=t("email-field-password-ph"),J.value="gmail",B("gmail"),ee.value="INBOX",re.checked=!0,de.checked=!0;const ae=document.getElementById("email-filter-sender"),d=document.getElementById("email-filter-subject");ae&&(ae.value=""),d&&(d.value=""),L(15),G&&(G.open=!1)}M(),D.style.display="flex",setTimeout(()=>ue.focus(),60)}function g(){const E=document.getElementById("email-modal");E&&(E.style.display="none")}function B(E){const D=(a||{})[E];if(!D||E==="custom")return;const J=document.getElementById("email-imap-host"),F=document.getElementById("email-imap-port"),Q=document.getElementById("email-imap-ssl");J&&(J.value=D.host||""),F&&(F.value=D.port||993),Q&&(Q.checked=D.ssl!==!1)}const S={"gmail.com":"gmail","googlemail.com":"gmail","outlook.com":"outlook","hotmail.com":"outlook","live.com":"outlook","office365.com":"outlook","msn.com":"outlook","yahoo.com":"yahoo","yahoo.co.jp":"yahoo","icloud.com":"icloud","me.com":"icloud","mac.com":"icloud","qq.com":"qq","foxmail.com":"qq","163.com":"163","126.com":"163","yeah.net":"163"};function I(E){if(!E||!E.includes("@"))return;const D=E.split("@")[1].toLowerCase().trim(),J=S[D];if(!J)return;const F=document.getElementById("email-preset");if(!F)return;const Q=F.value;Q&&Q!=="custom"&&Q!==""&&Q===J||(F.value=J,B(J))}function U(E){if(!E)return null;const D=a||{};for(const J in D)if(J!=="custom"&&D[J]&&D[J].host===E)return J;return null}function N(){const E=document.querySelector("#email-interval-options .email-interval-btn.active"),D=E?parseInt(E.dataset.interval,10):15;return{email_address:(document.getElementById("email-address").value||"").trim(),password:document.getElementById("email-password").value||"",imap_host:(document.getElementById("email-imap-host").value||"").trim(),imap_port:parseInt(document.getElementById("email-imap-port").value||"993",10)||993,imap_use_ssl:document.getElementById("email-imap-ssl").checked,folder:(document.getElementById("email-folder").value||"INBOX").trim()||"INBOX",mark_as_read:document.getElementById("email-mark-read").checked,enabled:document.getElementById("email-bind-enabled").checked,interval_min:[5,15,60].includes(D)?D:15,filter_sender:(document.getElementById("email-filter-sender").value||"").trim()||null,filter_subject:(document.getElementById("email-filter-subject").value||"").trim()||null}}function M(){const E=document.getElementById("email-interval-options");!E||E._bound||(E._bound=!0,E.addEventListener("click",D=>{const J=D.target.closest(".email-interval-btn");J&&(E.querySelectorAll(".email-interval-btn").forEach(F=>F.classList.remove("active")),J.classList.add("active"))}))}function L(E){const D=[5,15,60].includes(E)?E:15,J=document.getElementById("email-interval-options");J&&J.querySelectorAll(".email-interval-btn").forEach(F=>{F.classList.toggle("active",parseInt(F.dataset.interval,10)===D)})}function z(E,D){const J=document.getElementById("email-test-result");J&&(J.style.display="",J.textContent=D,J.className="form-test-result "+(E==="ok"?"ok":E==="running"?"running":"fail"))}async function V(){const E=N();if(!E.email_address){z("fail",t("email-addr-required"));return}if(!E.password){z("fail",t("email-password-required"));return}if(!E.imap_host){z("fail",t("email-host-required"));return}const D=document.getElementById("btn-email-modal-test");D&&(D.disabled=!0),z("running",t("email-test-running"));try{const J=await fetch("/api/email-ingest/test",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:E.email_address,password:E.password,imap_host:E.imap_host,imap_port:E.imap_port,imap_use_ssl:E.imap_use_ssl,folder:E.folder})}),F=await J.json().catch(()=>({}));if(J.ok&&F.success)z("ok",t("email-test-ok",{folder:E.folder,n:F.folder_count??"?"}));else{const Q=F.error_msg||"";Q==="auth_failed"||/auth/i.test(Q)?z("fail",t("email-test-auth-fail")):z("fail",t("email-test-fail",{msg:Q||J.status}))}}catch(J){z("fail",t("email-test-fail",{msg:String(J).slice(0,120)}))}finally{D&&(D.disabled=!1)}}async function W(){const E=N();if(!E.email_address){z("fail",t("email-addr-required"));return}if(n==="new"&&!E.password){z("fail",t("email-password-required"));return}if(!E.imap_host){z("fail",t("email-host-required"));return}const D=document.getElementById("btn-email-modal-save");D&&(D.disabled=!0);const J={...E};n==="edit"&&!J.password&&delete J.password;try{const F=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(J)}),Q=await F.json().catch(()=>({}));if(F.ok&&Q.ok)e=Q.account,showToast(t("email-save-ok"),"success"),g(),h(),y();else{const le="email."+(Q.detail||"").split(".").slice(-1)[0];z("fail",t(le)!==le?t(le):t("email-save-fail"))}}catch{z("fail",t("email-save-fail"))}finally{D&&(D.disabled=!1)}}async function P(){if(!(!e||!await showConfirm(t("email-unbind-confirm",{email:e.email_address}),{danger:!0,okText:t("email-btn-unbind")})))try{if((await fetch("/api/email-ingest/account",{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){e=null,showToast(t("email-unbind-ok"),"success"),h();const J=document.getElementById("email-logs-list");J&&(J.innerHTML="")}else showToast(t("email-unbind-fail"),"error")}catch{showToast(t("email-unbind-fail"),"error")}}async function u(){if(!e||l)return;if(!e.enabled){showToast(t("email.disabled"),"error");return}l=!0;const E=document.getElementById("btn-email-trigger"),D=E?E.innerHTML:"";E&&(E.disabled=!0,E.innerHTML=`<span>${escapeHtml(t("email-trigger-running"))}</span>`);try{const J=await fetch("/api/email-ingest/trigger",{method:"POST",headers:{Authorization:"Bearer "+token}}),F=await J.json().catch(()=>({}));if(J.ok){const Q=F.emails_scanned||0,ie=F.ocr_succeeded||0,le=F.ocr_failed||0;Q===0&&ie===0&&le===0?showToast(t("email-trigger-empty"),"success"):showToast(t("email-trigger-result",{scanned:Q,ok:ie,fail:le}),le>0?"warn":"success")}else{const ie="email."+(F.detail||"").split(".").slice(-1)[0];showToast(t(ie)!==ie?t(ie):t("email-trigger-fail"),"error")}await f()}catch{showToast(t("email-trigger-fail"),"error")}finally{l=!1,E&&(E.disabled=!1,E.innerHTML=D)}}async function c(){if(!e)return;const E=document.getElementById("email-enabled-toggle"),D=!!(E&&E.checked),J=e.enabled;try{const F=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:e.email_address,imap_host:e.imap_host,imap_port:e.imap_port,imap_use_ssl:e.imap_use_ssl,folder:e.folder||"INBOX",filter_subject:e.filter_subject||null,filter_sender:e.filter_sender||null,mark_as_read:e.mark_as_read!==!1,enabled:D})}),Q=await F.json().catch(()=>({}));F.ok&&Q.ok?(e=Q.account,h()):(E&&(E.checked=J),showToast(t("email-toggle-fail"),"error"))}catch{E&&(E.checked=J),showToast(t("email-toggle-fail"),"error")}}async function y(){const E=document.getElementById("email-logs-list");if(E){E.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`;try{const D=await fetch("/api/email-ingest/logs?limit=20",{headers:{Authorization:"Bearer "+token}});if(!D.ok){E.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const J=await D.json();if(!Array.isArray(J)||J.length===0){E.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("email-logs-empty"))}</div>`;return}E.innerHTML=J.map($).join("")}catch{E.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}function $(E){const D=o(E.created_at),J=E.status||"failed",F=J==="success"?"ok":J==="partial"?"partial":"fail",Q=J==="success"?"✓":J==="partial"?"◐":"✗",ie=E.trigger==="manual"?`<span class="log-tag manual">${escapeHtml(t("email-log-tag-manual"))}</span>`:`<span class="log-tag auto">${escapeHtml(t("email-log-tag-auto"))}</span>`,le=t("email-log-counts",{scanned:E.emails_scanned||0,att:E.attachments_found||0,ok:E.ocr_succeeded||0,fail:E.ocr_failed||0}),ue=(E.elapsed_ms||0)+"ms";return`
            <div class="email-log-row ${F}">
                <span class="log-time">${escapeHtml(D)}</span>
                <span class="log-status">${Q}</span>
                ${ie}
                <span class="log-counts">${escapeHtml(le)}</span>
                <span class="log-elapsed">${escapeHtml(ue)}</span>
            </div>
        `}function T(){const E=document.getElementById("btn-email-bind");E&&E.addEventListener("click",()=>w("new"));const D=document.getElementById("btn-email-edit");D&&D.addEventListener("click",()=>w("edit"));const J=document.getElementById("btn-email-unbind");J&&J.addEventListener("click",P);const F=document.getElementById("btn-email-trigger");F&&F.addEventListener("click",u);const Q=document.getElementById("email-enabled-toggle");Q&&Q.addEventListener("change",c);const ie=document.getElementById("email-modal-close");ie&&ie.addEventListener("click",g);const le=document.getElementById("btn-email-modal-cancel");le&&le.addEventListener("click",g);const ue=document.getElementById("btn-email-modal-test");ue&&ue.addEventListener("click",V);const R=document.getElementById("btn-email-modal-save");R&&R.addEventListener("click",W);const k=document.getElementById("email-preset");k&&k.addEventListener("change",ee=>B(ee.target.value));const Y=document.getElementById("email-address");Y&&!Y.dataset.autoBound&&(Y.dataset.autoBound="1",Y.addEventListener("blur",ee=>I((ee.target.value||"").trim())),Y.addEventListener("input",ee=>{const re=(ee.target.value||"").trim();re.includes("@")&&re.split("@")[1].includes(".")&&I(re)}));const X=document.getElementById("btn-email-refresh-logs");X&&X.addEventListener("click",()=>{X.classList.add("spinning"),setTimeout(()=>X.classList.remove("spinning"),600),y()})}T(),window._loadEmailIngestPanel=f,window._rerenderEmailIngest=function(){if(!s)return;h();const E=document.getElementById("email-logs-section");e&&E&&E.open&&y()};let _=null;window._startEmailLogAutoRefresh=function(){_||(_=setInterval(()=>{e&&s&&y()},3e4))},window._stopEmailLogAutoRefresh=function(){_&&(clearInterval(_),_=null)}})();(function(){let e=[],a=null,n=[],s="all",l=null,f=!1;async function h(){if(f){T();return}f=!0,x(),await o(),T()}function x(){const r=document.getElementById("bank-file-input");r&&!r._bound&&(r._bound=!0,r.addEventListener("change",I));const C=document.getElementById("btn-bank-queue-clear-done");C&&!C._bound&&(C._bound=!0,C.addEventListener("click",V));const A=document.getElementById("btn-bank-back");A&&!A._bound&&(A._bound=!0,A.addEventListener("click",()=>{a=null,n=[],ie()}));const O=document.getElementById("btn-bank-delete");O&&!O._bound&&(O._bound=!0,O.addEventListener("click",c));const K=document.getElementById("btn-bank-run-match");K&&!K._bound&&(K._bound=!0,K.addEventListener("click",u)),document.querySelectorAll(".bank-filter-btn").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",()=>{s=fe.dataset.bankFilter||"all",document.querySelectorAll(".bank-filter-btn").forEach(ve=>{ve.classList.toggle("active",ve===fe)}),re()}))}),document.querySelectorAll("[data-bank-cand-close]").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",m))});const te=document.getElementById("btn-bank-cand-pane-close");te&&!te._bound&&(te._bound=!0,te.addEventListener("click",m));const oe=document.getElementById("btn-bank-cand-ignore");oe&&!oe._bound&&(oe._bound=!0,oe.addEventListener("click",y));const se=document.getElementById("btn-bank-cand-ignore-pane");se&&!se._bound&&(se._bound=!0,se.addEventListener("click",y));const ne=document.getElementById("bank-client-badge");ne&&!ne._bound&&(ne._bound=!0,ne.addEventListener("click",R)),document.querySelectorAll("[data-bank-client-picker-close]").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",k))});const ce=document.getElementById("btn-bank-client-picker-save");ce&&!ce._bound&&(ce._bound=!0,ce.addEventListener("click",X)),document.querySelectorAll(".bank-sessions-chip").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",()=>{_=fe.dataset.sessFilter||"all",document.querySelectorAll(".bank-sessions-chip").forEach(ve=>{ve.classList.toggle("active",ve===fe)}),E()}))})}async function o(){try{const r=await fetch("/api/bank-recon/sessions?limit=30",{headers:{Authorization:"Bearer "+token}});if(!r.ok)throw new Error("sessions:"+r.status);e=await r.json(),E()}catch(r){console.warn("[bank-recon] loadSessions failed",r),e=[],E()}}async function p(r){try{const C="/api/bank-recon/sessions/"+encodeURIComponent(r)+(s!=="all"?"?filter="+s:""),A=await fetch(C,{headers:{Authorization:"Bearer "+token}});if(!A.ok)throw new Error("detail:"+A.status);const O=await A.json();a=O.session,n=O.transactions||[],Q()}catch(C){console.warn("[bank-recon] loadSessionDetail failed",C),showToast(t("bank-load-failed"),"error")}}let w=[],g=0;const B=3;function S(){return g+=1,"q"+g+"_"+Date.now()}async function I(r){const C=Array.from(r.target.files||[]);if(r.target.value="",C.length!==0){for(const A of C){const O={id:S(),file:A,name:A.name,size:A.size,status:"pending",progress:0,error_code:null,tx_count:0,session_id:null};A.name.toLowerCase().endsWith(".pdf")?A.size>20*1024*1024&&(O.status="failed",O.error_code="bank_recon.file_too_large"):(O.status="failed",O.error_code="bank_recon.only_pdf"),w.push(O)}U(),N(),W()}}function U(){const r=document.getElementById("bank-upload-queue");r&&(r.style.display=""),q(),Z()}function N(){const r=document.getElementById("bank-upload-queue-list"),C=document.getElementById("bank-upload-queue-summary");if(!r)return;if(w.length===0){r.innerHTML="",C&&(C.textContent="");const oe=document.getElementById("bank-upload-queue");oe&&(oe.style.display="none");return}let A=0,O=0,K=0,te=0;for(const oe of w)oe.status==="ok"?A++:oe.status==="failed"?O++:oe.status==="uploading"||oe.status==="parsing"?K++:te++;C&&(C.textContent=t("bank-queue-summary").replace("{ok}",A).replace("{run}",K).replace("{wait}",te).replace("{fail}",O)),r.innerHTML=w.map(M).join(""),r.querySelectorAll("[data-q-act]").forEach(oe=>{const se=oe.dataset.qAct,ne=oe.dataset.qId;oe.addEventListener("click",()=>{se==="retry"&&L(ne),se==="remove"&&z(ne)})})}function M(r){const C=(r.size/1024).toFixed(0)+" KB";let A="",O="";if(r.status==="pending")A='<span class="bq-stat bq-wait">'+t("bank-queue-status-wait")+"</span>",O='<button data-q-act="remove" data-q-id="'+H(r.id)+'" class="bq-act">×</button>';else if(r.status==="uploading")A='<span class="bq-stat bq-run">'+t("bank-queue-status-uploading")+'</span><div class="bq-bar"><div class="bq-bar-fill" style="width:'+(r.progress||0)+'%"></div></div>';else if(r.status==="parsing")A='<span class="bq-stat bq-run">'+t("bank-queue-status-parsing")+'</span><div class="bq-bar"><div class="bq-bar-fill bq-bar-indet"></div></div>';else if(r.status==="ok")A='<span class="bq-stat bq-ok">'+t("bank-queue-status-ok").replace("{n}",r.tx_count||0)+"</span>",O='<button data-q-act="remove" data-q-id="'+H(r.id)+'" class="bq-act">×</button>';else if(r.status==="failed"){const K=i(r.error_code||"unknown");A='<span class="bq-stat bq-fail" title="'+H(K)+'">'+H(K)+"</span>",O='<button data-q-act="retry" data-q-id="'+H(r.id)+'" class="bq-act bq-act-retry">'+t("bank-queue-retry")+'</button><button data-q-act="remove" data-q-id="'+H(r.id)+'" class="bq-act">×</button>'}return'<div class="bq-row" data-q-row="'+H(r.id)+'"><div class="bq-name" title="'+H(r.name)+'">'+H(r.name)+'</div><div class="bq-size">'+C+'</div><div class="bq-status">'+A+'</div><div class="bq-actions">'+O+"</div></div>"}function L(r){const C=w.find(A=>A.id===r);C&&(C.status="pending",C.error_code=null,C.progress=0,N(),W())}function z(r){const C=w.findIndex(O=>O.id===r);if(C<0)return;const A=w[C];A.status==="uploading"||A.status==="parsing"||(w.splice(C,1),N())}function V(){w=w.filter(r=>r.status!=="ok"),N()}async function W(){for(;;){if(w.filter(A=>A.status==="uploading"||A.status==="parsing").length>=B)return;const C=w.find(A=>A.status==="pending");if(!C){w.every(A=>A.status==="ok"||A.status==="failed")&&(await o(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage());return}P(C).then(()=>W())}}async function P(r){r.status="uploading",r.progress=0,N();try{const C=new FormData;C.append("file",r.file,r.name);const A=await new Promise((K,te)=>{const oe=new XMLHttpRequest;oe.open("POST","/api/bank-recon/upload"),oe.setRequestHeader("Authorization","Bearer "+token),oe.upload.onprogress=se=>{se.lengthComputable&&(r.progress=Math.min(99,Math.round(se.loaded/se.total*100)),N())},oe.upload.onload=()=>{r.status="parsing",N()},oe.onload=()=>{oe.status>=200&&oe.status<300?K({status:oe.status,text:oe.responseText}):K({status:oe.status,text:oe.responseText})},oe.onerror=()=>te(new Error("network")),oe.send(C)});let O={};try{O=JSON.parse(A.text||"{}")}catch{O={}}if(A.status>=400){r.status="failed",r.error_code=O&&O.detail||"unknown",N();return}if(O.parse_status==="parse_failed"){r.status="failed",r.error_code=O.error==="scanned_pdf_not_yet"?"bank_recon.scanned":"bank_recon.no_tx",N();return}r.status="ok",r.tx_count=O.tx_count||0,r.session_id=O.session_id||null,N()}catch(C){console.warn("[bank-recon] upload failed",C),r.status="failed",r.error_code="network",N()}}async function u(){if(!a)return;const r=document.getElementById("btn-bank-run-match"),C=r.innerHTML;r.disabled=!0,r.innerHTML="<span>"+t("bank-matching")+"</span>";try{const A=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(a.id)+"/match",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!A.ok)throw new Error("match:"+A.status);const O=await A.json();showToast(t("bank-match-done").replace("{matched}",O.matched).replace("{suggested}",O.suggested).replace("{unmatched}",O.unmatched),"success"),await p(a.id),await o()}catch(A){console.warn("[bank-recon] match failed",A),showToast(t("bank-match-failed"),"error")}finally{r.disabled=!1,r.innerHTML=C}}async function c(){if(!(!a||!await showConfirm(t("bank-delete-confirm"),{danger:!0})))try{const C=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(a.id),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!C.ok)throw new Error("delete:"+C.status);showToast(t("bank-deleted"),"success"),a=null,n=[],ie(),await o()}catch(C){console.warn("[bank-recon] delete failed",C),showToast(t("bank-delete-failed"),"error")}}async function y(){if(l)try{const r=await fetch("/api/bank-recon/tx/"+encodeURIComponent(l.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"ignored"})});if(!r.ok)throw new Error("ignore:"+r.status);m(),await p(a.id)}catch{showToast(t("bank-action-failed"),"error")}}async function $(r){if(l)try{const C=await fetch("/api/bank-recon/tx/"+encodeURIComponent(l.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"matched",history_id:r})});if(!C.ok)throw new Error("pick:"+C.status);showToast(t("bank-matched-ok"),"success"),m(),await p(a.id)}catch{showToast(t("bank-action-failed"),"error")}}function T(){const r=document.getElementById("bank-status-summary");if(!r)return;if(e.length===0){r.textContent=t("bank-pill-none");return}let A=0;for(const O of e)O.parse_status==="parsed"&&(O.unmatched_count||0)>0&&A++;r.textContent=A>0?t("bank-pill-pending").replace("{n}",A):t("bank-pill-ok")}let _="all";function E(){const r=document.getElementById("bank-sessions-list");if(!r)return;let C=e||[];if(_==="parsed"?C=C.filter(A=>A.parse_status==="parsed"):_==="failed"&&(C=C.filter(A=>A.parse_status==="parse_failed")),!e||e.length===0){r.innerHTML='<div class="bank-empty" data-i18n="bank-sessions-empty">'+t("bank-sessions-empty")+"</div>";return}if(C.length===0){r.innerHTML='<div class="bank-empty">'+t("bank-sess-filter-empty")+"</div>";return}r.innerHTML=C.map(A=>J(A)).join(""),r.querySelectorAll(".bank-session-row").forEach(A=>{A.addEventListener("click",O=>{O.target.closest(".bank-session-trash")||p(A.dataset.sessionId)})}),r.querySelectorAll(".bank-session-trash").forEach(A=>{A.addEventListener("click",O=>{O.stopPropagation();const K=A.dataset.sessionId,te=A.dataset.sessionName||"";D(K,te)})})}async function D(r,C){if(!r)return;const A=(t("bank-session-delete-confirm")||"确定删除这条对账记录吗?").replace("{name}",C||"");if(await showConfirm(A,{danger:!0}))try{const K=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(r),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!K.ok)throw new Error("delete:"+K.status);showToast(t("bank-deleted"),"success"),a&&a.id===r&&(a=null,n=[],ie()),await o(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()}catch(K){console.warn("[bank-recon] delete failed",K),showToast(t("bank-delete-failed"),"error")}}window._deleteBankSession=D;function J(r){const C=(r.bank_code||"OTHER").toUpperCase(),A=j(r.period_start,r.period_end),O=r.account_last4?"···"+r.account_last4:"",K=F(r),te=b(r.created_at);return`
            <div class="bank-session-row" data-session-id="${H(r.id)}">
                <div class="bank-session-bank bk-${H(C)}">${H(C)}</div>
                <div class="bank-session-info">
                    <div class="bank-session-title">${H(r.source_filename||A||"-")}</div>
                    <div class="bank-session-meta">${H(A)} · ${H(O)} · ${H(te)}</div>
                </div>
                <div class="bank-session-counts">${K}</div>
                <button class="bank-session-trash" data-session-id="${H(r.id)}" data-session-name="${H(r.source_filename||"")}" title="${H(t("bank-session-delete-tip")||"删除")}">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/>
                    </svg>
                </button>
                <div class="bank-session-arrow">
                    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg>
                </div>
            </div>
        `}function F(r){if(r.parse_status==="parse_failed")return`<span class="bank-session-count cnt-failed">${t("bank-count-parse-failed")}</span>`;if(r.parse_status!=="parsed")return`<span class="bank-session-count">${t("bank-count-parsing")}</span>`;const C=r.tx_count||0,A=r.matched_count||0,O=r.unmatched_count||0,K=[`<span class="bank-session-count">${C} ${t("bank-count-tx")}</span>`];return A>0&&K.push(`<span class="bank-session-count cnt-matched">${A} ${t("bank-count-matched")}</span>`),O>0&&K.push(`<span class="bank-session-count cnt-unmatched">${O} ${t("bank-count-unmatched")}</span>`),K.join("")}function Q(){document.getElementById("bank-detail").style.display="",document.querySelector(".bank-sessions-section").style.display="none",ee(),re(),le()}function ie(){document.getElementById("bank-detail").style.display="none",document.querySelector(".bank-sessions-section").style.display="";const r=document.getElementById("bank-detail-body");r&&r.classList.remove("has-pane"),l=null}function le(){const r=document.getElementById("bank-client-badge");if(!r||!a)return;const C=a.client_id,A=document.getElementById("bank-client-badge-dot"),O=document.getElementById("bank-client-badge-name"),K=document.getElementById("bank-client-badge-caret"),te=typeof _userInfo<"u"?_userInfo:null,oe=!(te&&te.role==="member");if(C!=null){const se=(window._clientsCache||[]).find(ne=>Number(ne.id)===Number(C));r.classList.remove("is-empty"),A&&(A.style.background=se&&se.color||"#111111"),O&&(O.textContent=se&&(se.short_name||se.name)||"#"+C)}else r.classList.add("is-empty"),A&&(A.style.background=""),O&&(O.textContent=t("bank-client-none"));oe?(r.classList.remove("is-readonly"),r.disabled=!1,K&&(K.style.display="")):(r.classList.add("is-readonly"),r.disabled=!0,K&&(K.style.display="none")),r.style.display=""}let ue=null;function R(){if(!a)return;const r=typeof _userInfo<"u"?_userInfo:null;if(!!(r&&r.role==="member"))return;ue=a.client_id!=null?Number(a.client_id):null,Y();const A=document.getElementById("bank-client-picker-modal");A&&(A.style.display="")}function k(){const r=document.getElementById("bank-client-picker-modal");r&&(r.style.display="none"),ue=null}function Y(){const r=document.getElementById("bank-client-picker-list");if(!r)return;const C=(window._clientsCache||[]).filter(O=>O&&(O.is_active===!0||O.is_active===void 0)),A=[];A.push('<div class="bank-client-picker-row is-none'+(ue==null?" is-selected":"")+'" data-cid=""><span class="bank-cp-dot"></span><span>'+H(t("bank-client-picker-none"))+"</span></div>"),C.forEach(O=>{const K=Number(O.id)===Number(ue)?" is-selected":"";A.push('<div class="bank-client-picker-row'+K+'" data-cid="'+H(O.id)+'"><span class="bank-cp-dot" style="background:'+H(O.color||"#111111")+'"></span><span>'+H(O.short_name||O.name||"#"+O.id)+"</span></div>")}),r.innerHTML=A.join(""),r.querySelectorAll(".bank-client-picker-row").forEach(O=>{O.addEventListener("click",()=>{const K=O.dataset.cid;ue=K?Number(K):null,Y()})})}async function X(){if(a)try{const r=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(a.id)+"/client",{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({client_id:ue})});if(!r.ok)throw new Error("client:"+r.status);a.client_id=ue,le(),showToast(t("bank-client-changed"),"success"),k();try{await o()}catch{}}catch(r){console.warn("[bank-recon] save client failed",r),showToast(t("bank-client-change-failed"),"error")}}function ee(){if(!a)return;const r=a;document.getElementById("bank-detail-title").textContent=(r.bank_code||"-")+(r.account_last4?" ···"+r.account_last4:"")+" · "+(r.source_filename||""),document.getElementById("bank-meta-period").textContent=j(r.period_start,r.period_end)||"-",document.getElementById("bank-meta-opening").textContent=v(r.opening_balance),document.getElementById("bank-meta-inflow").textContent="+"+v(r.total_inflow),document.getElementById("bank-meta-outflow").textContent="-"+v(r.total_outflow),document.getElementById("bank-meta-closing").textContent=v(r.closing_balance);const C=n||[],A=C.length;let O=0,K=0,te=0;for(const oe of C){const se=oe.match_status||"unmatched";se==="matched"?O++:se==="suggested"?K++:te++}document.getElementById("bank-stat-total").textContent=A,document.getElementById("bank-stat-matched").textContent=O,document.getElementById("bank-stat-suggested").textContent=K,document.getElementById("bank-stat-unmatched").textContent=te}function re(){const r=document.getElementById("bank-tx-tbody");if(!r)return;let C=n||[];if(s!=="all"&&(C=C.filter(A=>s==="matched"?A.match_status==="matched":s==="suggested"?A.match_status==="suggested":s==="unmatched"?A.match_status==="unmatched"||A.match_status==="ignored":!0)),C.length===0){r.innerHTML=`<tr><td colspan="4" class="bank-empty">${t("bank-tx-empty")}</td></tr>`;return}if(r.innerHTML=C.map(A=>de(A)).join(""),r.querySelectorAll("tr[data-tx-id]").forEach(A=>{A.addEventListener("click",()=>{const O=A.dataset.txId,K=n.find(te=>te.id===O);K&&(r.querySelectorAll("tr.is-selected").forEach(te=>te.classList.remove("is-selected")),A.classList.add("is-selected"),pe(K))})}),l){const A=r.querySelector('tr[data-tx-id="'+l.id+'"]');A&&A.classList.add("is-selected")}}function de(r){const C=r.direction==="OUT",A=C?"-":"+",O=C?"bank-out":"bank-in",K=r.match_status||"unmatched",te=t("bank-match-"+K)||K,oe=b(r.tx_date),se=r.channel?`<span class="bank-tx-channel">${H(r.channel)}</span>`:"";return`
            <tr data-tx-id="${H(r.id)}">
                <td class="bank-tx-date">${H(oe)}</td>
                <td class="bank-tx-desc">${se}${H(r.description||"-")}</td>
                <td class="bank-td-amount ${O}">${A}${v(r.amount)}</td>
                <td><span class="bank-tx-match mt-${K}">${H(te)}</span></td>
            </tr>
        `}async function pe(r){l=r;const C=document.getElementById("bank-detail-body");C&&C.classList.add("has-pane");const A=document.getElementById("bank-cand-pane-title"),O=document.getElementById("bank-cand-pane-sub"),K=document.getElementById("bank-cand-pane-foot");if(A&&(A.textContent=t("bank-cand-pane-current")),O){const oe=r.direction==="OUT"?"-":"+",se=r.direction==="OUT"?"bank-out":"bank-in";O.innerHTML=`${H(b(r.tx_date))}
                <span style="margin:0 6px;color:#D1D5DB">·</span>
                <span>${H(r.description||"-")}</span>
                <span style="margin:0 6px;color:#D1D5DB">·</span>
                <strong class="${se}">${oe}${v(r.amount)}</strong>`}K&&(K.style.display="");const te=document.getElementById("bank-cand-pane-body");if(te){te.innerHTML=`<div class="bank-empty">${t("bank-cand-loading")}</div>`;try{const oe=await fetch("/api/bank-recon/tx/"+encodeURIComponent(r.id)+"/candidates",{headers:{Authorization:"Bearer "+token}});if(!oe.ok)throw new Error("cands:"+oe.status);const se=await oe.json();d(r,se.candidates||[])}catch{te.innerHTML=`<div class="bank-empty">${t("bank-cand-load-failed")}</div>`}}}function G(r){const C=Number(r||0);let A="score-low";return C>=85?A="score-high":C>=60&&(A="score-mid"),'<span class="bank-cand-score '+A+'">'+C.toFixed(0)+" "+t("bank-cand-score-unit")+"</span>"}function ae(r,C,A){const O=C.history_id,K=C.invoice_no||"-",te=C.vendor||"-",oe=C.amount_total!==null&&C.amount_total!==void 0?v(C.amount_total):"-",se=C.invoice_date?b(C.invoice_date):"-",ne=C.filename||"",ce=!!A&&r.matched_history_id===O,fe="bank-cand-card"+(C.is_auto_picked?" is-auto":"")+(ce?" is-picked":"");let ve="";return ce?ve='<button class="btn btn-ghost btn-small" data-act="unmatch"><span>'+t("bank-cand-unmatch")+"</span></button>":ve='<button class="btn btn-primary btn-small" data-act="pick" data-hid="'+H(O)+'"><span>'+t(C.is_auto_picked?"bank-cand-confirm":"bank-cand-pick-this")+"</span></button>",'<div class="'+fe+'" data-hid="'+H(O)+'"><div class="bank-cand-card-head"><div class="bank-cand-card-vendor">'+H(te)+"</div>"+G(C.score)+'</div><div class="bank-cand-card-fields"><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-invoice-no")+"</span> "+H(K)+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-amount")+"</span> "+oe+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-date")+"</span> "+H(se)+"</span></div>"+(ne?'<div class="bank-cand-card-file" title="'+H(ne)+'">'+H(ne)+"</div>":"")+(C.reason?'<div class="bank-cand-card-reason">'+H(C.reason)+"</div>":"")+'<div class="bank-cand-card-actions">'+ve+"</div></div>"}function d(r,C){const A=document.getElementById("bank-cand-pane-body");if(!A)return;const O=C||[];let K="";if(r.match_status==="matched")K='<div class="bank-cand-hint hint-matched">'+t("bank-cand-hint-matched").replace("{n}",O.length)+"</div>";else if(r.match_status==="suggested")K='<div class="bank-cand-hint hint-suggested">'+t("bank-cand-hint-suggested").replace("{n}",O.length)+"</div>";else if(O.length>0)K='<div class="bank-cand-hint hint-low">'+t("bank-cand-hint-low").replace("{n}",O.length)+"</div>";else{A.innerHTML='<div class="bank-empty">'+t("bank-cand-no-match-detail")+"</div>";return}const te=r.match_status==="matched",oe=O.map(se=>ae(r,se,te)).join("");A.innerHTML=K+'<div class="bank-cand-list">'+oe+"</div>",A.querySelectorAll('[data-act="pick"]').forEach(se=>{se.addEventListener("click",()=>{$(se.dataset.hid)})}),A.querySelectorAll('[data-act="unmatch"]').forEach(se=>{se.addEventListener("click",async()=>{try{await fetch("/api/bank-recon/tx/"+encodeURIComponent(r.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"unmatched"})}),m(),await p(a.id)}catch{showToast(t("bank-action-failed"),"error")}})})}function m(){const r=document.getElementById("bank-detail-body");r&&r.classList.remove("has-pane");const C=document.getElementById("bank-cand-pane-title"),A=document.getElementById("bank-cand-pane-sub"),O=document.getElementById("bank-cand-pane-body"),K=document.getElementById("bank-cand-pane-foot");C&&(C.textContent=t("bank-cand-pane-empty-title")),A&&(A.textContent=t("bank-cand-pane-empty-sub")),K&&(K.style.display="none"),O&&(O.innerHTML='<div class="bank-cand-pane-empty"><svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="14" y="10" width="36" height="44" rx="3"/><path d="M22 22h20M22 30h20M22 38h12"/></svg><div>'+t("bank-cand-pane-empty-hint")+"</div></div>");const te=document.getElementById("bank-tx-tbody");te&&te.querySelectorAll("tr.is-selected").forEach(oe=>oe.classList.remove("is-selected")),l=null}function q(r){const C=document.getElementById("bank-upload-progress");C&&(C.style.display="none")}function Z(){const r=document.getElementById("bank-upload-error");r&&(r.style.display="none")}function i(r){return{"bank_recon.only_pdf":t("bank-err-only-pdf"),"bank_recon.empty_file":t("bank-err-empty"),"bank_recon.file_too_large":t("bank-err-too-large"),"bank_recon.save_failed":t("bank-err-server"),"bank_recon.scanned":t("bank-err-scanned"),"bank_recon.no_tx":t("bank-err-no-tx"),network:t("bank-err-network")}[r]||t("bank-err-unknown")+" ("+r+")"}function v(r){if(r==null)return"-";const C=Number(r);return isNaN(C)?"-":C.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function b(r){if(!r)return"-";const C=String(r);return C.length>=10?C.slice(0,10):C}function j(r,C){return!r&&!C?"":(b(r)||"?")+" ~ "+(b(C)||"?")}function H(r){return r==null?"":String(r).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}window._loadBankReconPanel=h,window._rerenderBankRecon=function(){if(currentRoute==="automation"){if(E(),a&&(ee(),re(),le(),!l)){const r=document.getElementById("bank-cand-pane-title"),C=document.getElementById("bank-cand-pane-sub");r&&(r.textContent=t("bank-cand-pane-empty-title")),C&&(C.textContent=t("bank-cand-pane-empty-sub"))}N()}},typeof window.subscribeI18n=="function"&&window.subscribeI18n("bank-recon",window._rerenderBankRecon),window._openBankSession=async function(r){r&&(f||await h(),await p(r))}})();(function(){const e=document.getElementById("page-clients");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
        <div class="page-head">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
                    <circle cx="9" cy="7" r="4"/>
                    <path d="M23 21v-2a4 4 0 00-3-3.87"/>
                    <path d="M16 3.13a4 4 0 010 7.75"/>
                </svg>
            </div>
            <div class="page-head-text">
                <h1 class="page-title" data-i18n="clients-title">客户管理</h1>
                <div class="page-subtitle" data-i18n="clients-sub">账套主体 + 买方客户 · 统一归档管理</div>
            </div>
        </div>

        <!-- 顶部横向 tab 条(对账中心同款)· 账套主体 / 买方客户 -->
        <div class="recon-tab-bar cust-tab-bar">
            <button class="recon-tab-btn active" data-cust-tab="seller" data-i18n="cust-tab-seller">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><rect x="2" y="5" width="12" height="9" rx="1"/><path d="M10 14V4a1 1 0 00-1-1H7a1 1 0 00-1 1v10"/></svg>
                账套主体
            </button>
            <button class="recon-tab-btn" data-cust-tab="buyer" data-i18n="cust-tab-buyer">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M11 14v-1.2a2.4 2.4 0 00-2.4-2.4H4.4A2.4 2.4 0 002 12.8V14"/><circle cx="6.2" cy="5.2" r="2.4"/><path d="M14 14v-1.2a2.4 2.4 0 00-1.8-2.3"/></svg>
                买方客户
            </button>
        </div>

        <!-- ── 账套主体面板(= 工作空间 · 与右上角切换器/登录弹窗共用同一份)── -->
        <div id="cust-pane-seller" class="cust-pane active">
            <div class="cust-toolbar">
                <div class="search-wrap cust-search-wrap">
                    <svg class="search-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="7" cy="7" r="5"/><path d="M11 11l3 3"/></svg>
                    <input type="text" id="seller-search" class="search-input" data-i18n-placeholder="seller-search-ph" placeholder="搜索账套主体…">
                    <button class="search-clear" id="seller-search-clear" style="display:none;">&times;</button>
                </div>
                <button class="btn btn-primary" id="btn-seller-new" style="display:none;">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v10M3 8h10"/></svg>
                    <span data-i18n="seller-new">新建账套主体</span>
                </button>
            </div>
            <div class="cust-hint" data-i18n="seller-hint">账套主体 = 你的公司(发票卖方 / 开票方)。这里与右上角切换器、登录弹窗共用同一份数据,任意处新建/修改都会同步。</div>
            <div class="cust-table-wrap">
                <div class="cust-table-head seller-grid">
                    <div data-i18n="seller-col-name">账套主体</div>
                    <div data-i18n="seller-col-tax">税号</div>
                    <div class="align-right" data-i18n="seller-col-count">发票数</div>
                    <div class="align-right" data-i18n="seller-col-actions">操作</div>
                </div>
                <div id="seller-tbody"><div class="cust-loading" data-i18n="clients-loading">加载中…</div></div>
            </div>
        </div>

        <!-- ── 买方客户面板(横条列表 · 搜索/多选/批删/翻页 · 识别记录同款)── -->
        <div id="cust-pane-buyer" class="cust-pane">
            <div class="cust-toolbar">
                <div class="search-wrap cust-search-wrap">
                    <svg class="search-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="7" cy="7" r="5"/><path d="M11 11l3 3"/></svg>
                    <input type="text" id="buyer-search" class="search-input" data-i18n-placeholder="buyer-search-ph" placeholder="搜索买方客户 / 税号…">
                    <button class="search-clear" id="buyer-search-clear" style="display:none;">&times;</button>
                </div>
                <button class="btn btn-primary" id="btn-buyer-new">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v10M3 8h10"/></svg>
                    <span data-i18n="buyer-new">新建买方客户</span>
                </button>
            </div>
            <div id="buyer-batch-bar" class="cust-batch-bar" style="display:none;">
                <span class="cust-batch-count" id="buyer-batch-count"></span>
                <div class="cust-batch-actions">
                    <button class="btn btn-ghost btn-sm" id="buyer-batch-cancel" data-i18n="cust-batch-cancel">取消</button>
                    <button class="btn btn-danger btn-sm" id="buyer-batch-delete" data-i18n="cust-batch-delete">批量删除</button>
                </div>
            </div>
            <div class="cust-table-wrap">
                <div class="cust-table-head buyer-grid">
                    <div class="cust-col-check"><input type="checkbox" id="buyer-check-all"></div>
                    <div data-i18n="buyer-col-name">客户名称</div>
                    <div class="align-right" data-i18n="buyer-col-count">发票数</div>
                    <div class="align-right" data-i18n="buyer-col-amount">金额合计</div>
                    <div class="align-right" data-i18n="buyer-col-actions">操作</div>
                </div>
                <div id="buyer-tbody"><div class="cust-loading" data-i18n="clients-loading">加载中…</div></div>
            </div>
            <div class="cust-foot">
                <span class="cust-pager-info" id="buyer-pager-info"></span>
                <div class="cust-pager-btns">
                    <button class="btn btn-ghost btn-sm" id="buyer-prev" data-i18n="cust-prev">上一页</button>
                    <button class="btn btn-ghost btn-sm" id="buyer-next" data-i18n="cust-next">下一页</button>
                </div>
            </div>
        </div>
`,e.dataset.wbInjected="1";try{const a=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",n=window.I18N;n&&n[a]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const l=s.getAttribute("data-i18n");n[a][l]&&(s.textContent=n[a][l])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const l=s.getAttribute("data-i18n-placeholder");n[a][l]&&(s.placeholder=n[a][l])}))}catch{}}})();(function(){let e=[],a=null,n="",s="seller";const l={page:0,pageSize:12,keyword:""},f=new Set;let h=[];const x={keyword:""};let o=null;function p(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}async function w(k,Y={}){const X=await fetch(k,{...Y,headers:{"Content-Type":"application/json",...p(),...Y.headers||{}}});if(!X.ok){const ee=await X.json().catch(()=>({}));throw new Error(ee.detail||"HTTP "+X.status)}return X.json()}async function g(){try{e=(await w("/api/clients")).clients||[],window._clientsCache=e}catch(k){console.error("loadClientsCache fail",k),e=[]}try{typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter()}catch{}try{typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher()}catch{}return e}function B(k){s=k==="buyer"?"buyer":"seller",document.querySelectorAll("[data-cust-tab]").forEach(ee=>ee.classList.toggle("active",ee.dataset.custTab===s));const Y=document.getElementById("cust-pane-seller"),X=document.getElementById("cust-pane-buyer");Y&&Y.classList.toggle("active",s==="seller"),X&&X.classList.toggle("active",s==="buyer")}function S(){const k=window._userInfo||{},Y=String(k.role||"").toLowerCase(),X=String(k.tenant_role||"").toLowerCase();return k.is_super_admin===!0||k.is_owner===!0||Y==="owner"||Y==="admin"||X==="owner"||X==="admin"}function I(){window._workspaceClientsCache=h,typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl()}async function U(){try{const k=await w("/api/workspace/clients");h=k&&(k.clients||k.items)||[],window._workspaceClientsCache=h}catch(k){console.error("loadSellerCache fail",k),h=[]}return h}function N(){const k=x.keyword.trim().toLowerCase();return k?h.filter(Y=>(Y.name||"").toLowerCase().includes(k)||(Y.tax_id||"").toLowerCase().includes(k)):h}function M(){const k=document.getElementById("seller-tbody");if(!k)return;const Y=S(),X=document.getElementById("btn-seller-new");X&&(X.style.display=Y?"":"none");const ee=N(),re=typeof window.getActiveWorkspaceClientId=="function"?window.getActiveWorkspaceClientId():null;if(!ee.length){k.innerHTML=`<div class="cust-empty">${escapeHtml(t(x.keyword?"cust-no-match":"seller-empty"))}</div>`;return}k.innerHTML=ee.map(de=>{const G=re!=null&&Number(re)===Number(de.id)?`<span class="cust-badge-current"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7.5l3.2 3.2L12 4"/></svg>${escapeHtml(t("seller-current"))}</span>`:`<button class="cust-row-btn primary" data-saction="activate" data-wid="${de.id}">${escapeHtml(t("seller-set-current"))}</button>`,ae=Y?`
                <button class="cust-row-btn" data-saction="edit" data-wid="${de.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
                <button class="cust-row-btn danger" data-saction="archive" data-wid="${de.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h10M4 4v7a1 1 0 001 1h4a1 1 0 001-1V4M5.5 4V2.8a1 1 0 011-1h1a1 1 0 011 1V4"/></svg><span>${escapeHtml(t("wsclient-archive"))}</span></button>`:"";return`<div class="cust-row seller-grid" data-wid="${de.id}">
                <div class="cust-cell-name"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" style="flex-shrink:0;opacity:.55"><rect x="2" y="5" width="12" height="9" rx="1"/><path d="M10 14V4a1 1 0 00-1-1H7a1 1 0 00-1 1v10"/></svg><span class="cust-name-text">${escapeHtml(de.name||"#"+de.id)}</span></div>
                <div class="cust-cell-tax">${escapeHtml(de.tax_id||"—")}</div>
                <div class="align-right">${de.invoice_count||0}</div>
                <div class="cust-row-actions">${G}${ae}</div>
            </div>`}).join("")}function L(k){o=k?k.id:null,document.getElementById("wsclient-modal-title").textContent=t(k?"wsclient-modal-edit":"wsclient-modal-new"),document.getElementById("wsclient-input-name").value=k&&k.name||"",document.getElementById("wsclient-input-tax").value=k&&k.tax_id||"",document.getElementById("wsclient-modal-archive").style.display=k?"":"none",document.getElementById("wsclient-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("wsclient-input-name").focus(),50)}function z(){document.getElementById("wsclient-modal-mask").style.display="none",o=null}async function V(){const k=document.getElementById("wsclient-input-name").value.trim(),Y=document.getElementById("wsclient-input-tax").value.trim();if(!k){showToast(t("client-msg-name-required"),"fail");return}try{o?(await w("/api/workspace/clients/"+o,{method:"PATCH",body:JSON.stringify({name:k,tax_id:Y})}),showToast(t("client-msg-updated"),"success")):(await w("/api/workspace/clients",{method:"POST",body:JSON.stringify({name:k,tax_id:Y||null})}),showToast(t("client-msg-created"),"success")),z(),await U(),M(),I()}catch(X){const ee=X&&X.message?X.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+ee,"fail")}}async function W(){if(!o)return;const k=h.find(X=>Number(X.id)===Number(o));if(await showConfirm(t("wsclient-archive-confirm").replace("{name}",k?k.name:""),{danger:!0}))try{const X=o;await w("/api/workspace/clients/"+X,{method:"DELETE"}),showToast(t("wsclient-archived"),"success"),typeof window.getActiveWorkspaceClientId=="function"&&Number(window.getActiveWorkspaceClientId())===Number(X)&&typeof window.enterPersonalMode=="function"&&window.enterPersonalMode(),z(),await U(),M(),I()}catch{showToast(t("client-msg-save-fail"),"fail")}}function P(){const k=l.keyword.trim().toLowerCase();return k?e.filter(Y=>(Y.name||"").toLowerCase().includes(k)||(Y.short_name||"").toLowerCase().includes(k)||(Y.tax_id||"").toLowerCase().includes(k)):e}function u(){const k=P(),Y=l.pageSize,X=Math.max(0,Math.ceil(k.length/Y)-1);l.page>X&&(l.page=X);const ee=l.page*Y;return{all:k,items:k.slice(ee,ee+Y),start:ee,ps:Y,total:k.length,maxPage:X}}function c(){const k=document.getElementById("buyer-tbody");if(!k)return;const{items:Y,start:X,ps:ee,total:re,maxPage:de}=u();re?k.innerHTML=Y.map(d=>{const m=f.has(d.id);return`<div class="cust-row buyer-grid${m?" selected":""}" data-cid="${d.id}">
                    <div class="cust-cell-check"><input type="checkbox" class="buyer-row-check" data-cid="${d.id}" ${m?"checked":""}></div>
                    <div style="min-width:0">
                        <div class="cust-cell-name"><span class="cust-color-dot" style="background:${escapeHtml(d.color||"#111")}"></span><span class="cust-name-text">${escapeHtml(d.name)}</span></div>
                        ${d.tax_id?`<div class="cust-cell-sub">${escapeHtml(d.tax_id)}</div>`:""}
                    </div>
                    <div class="align-right">${d.invoice_count||0}</div>
                    <div class="align-right cust-cell-amount">฿${(d.total_amount||0).toLocaleString(void 0,{maximumFractionDigits:0})}</div>
                    <div class="cust-row-actions">
                        <button class="cust-row-btn" data-action="edit" data-cid="${d.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
                        <button class="cust-row-btn" data-action="export" data-cid="${d.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 2v7M4 6l3 3 3-3M2 11h10"/></svg><span>${escapeHtml(t("client-card-export"))}</span></button>
                    </div>
                </div>`}).join(""):k.innerHTML=`<div class="cust-empty">${escapeHtml(t(l.keyword?"cust-no-match":"clients-empty"))}</div>`;const pe=document.getElementById("buyer-pager-info");pe&&(pe.textContent=re?`${X+1}–${Math.min(X+ee,re)} / ${re}`:"0");const G=document.getElementById("buyer-prev");G&&(G.disabled=l.page<=0);const ae=document.getElementById("buyer-next");ae&&(ae.disabled=l.page>=de),y()}function y(){const k=f.size,Y=document.getElementById("buyer-batch-bar");Y&&(Y.style.display=k?"flex":"none");const X=document.getElementById("buyer-batch-count");X&&(X.textContent=t("cust-selected-n").replace("{n}",k));const ee=document.getElementById("buyer-check-all");if(ee){const{items:re}=u(),de=re.map(G=>G.id),pe=de.filter(G=>f.has(G)).length;ee.checked=de.length>0&&pe===de.length,ee.indeterminate=pe>0&&pe<de.length}}function $(){f.clear(),c()}async function T(){const k=Array.from(f);if(!(!k.length||!await showConfirm(t("cust-batch-del-confirm").replace("{n}",k.length),{danger:!0})))try{await w("/api/clients/batch-delete",{method:"POST",body:JSON.stringify({ids:k})}),showToast(t("client-msg-deleted"),"success"),f.clear(),await g(),c(),ie(),R()}catch{showToast(t("client-msg-save-fail"),"fail")}}window.loadClientsPage=async function(){const k=document.getElementById("seller-tbody");k&&(k.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`);const Y=document.getElementById("buyer-tbody");Y&&(Y.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`),await Promise.all([U(),g()]),M(),c()},window.addEventListener("pearnly:workspace-changed",function(){typeof currentRoute<"u"&&currentRoute==="clients"&&M()});function _(k){a=k?k.id:null;const Y=!!k;document.getElementById("client-modal-title").textContent=t(Y?"client-modal-edit":"client-modal-new"),document.getElementById("client-input-name").value=k&&k.name||"",document.getElementById("client-input-short").value=k&&k.short_name||"",document.getElementById("client-input-tax").value=k&&k.tax_id||"",document.getElementById("client-input-address").value=k&&k.address||"",document.getElementById("client-input-contact").value=k&&k.contact_person||"",document.getElementById("client-input-phone").value=k&&k.contact_phone||"",document.getElementById("client-input-email").value=k&&k.contact_email||"",document.getElementById("client-input-notes").value=k&&k.notes||"";const X=k&&k.color||"#111111";document.querySelectorAll("#client-color-picker .color-swatch").forEach(ee=>{ee.classList.toggle("active",ee.dataset.color===X)}),document.getElementById("client-modal-delete").style.display=Y?"":"none",document.getElementById("client-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("client-input-name").focus(),50)}function E(){document.getElementById("client-modal-mask").style.display="none",a=null}function D(){const k=document.querySelector("#client-color-picker .color-swatch.active");return k?k.dataset.color:"#111111"}async function J(){const k=document.getElementById("client-input-name").value.trim();if(!k){showToast(t("client-msg-name-required"),"fail");return}const Y={name:k,short_name:document.getElementById("client-input-short").value.trim()||null,tax_id:document.getElementById("client-input-tax").value.trim()||null,address:document.getElementById("client-input-address").value.trim()||null,contact_person:document.getElementById("client-input-contact").value.trim()||null,contact_phone:document.getElementById("client-input-phone").value.trim()||null,contact_email:document.getElementById("client-input-email").value.trim()||null,notes:document.getElementById("client-input-notes").value.trim()||null,color:D()};try{a?(await w(`/api/clients/${a}`,{method:"PATCH",body:JSON.stringify(Y)}),showToast(t("client-msg-updated"),"success")):(await w("/api/clients",{method:"POST",body:JSON.stringify(Y)}),showToast(t("client-msg-created"),"success")),E(),await g(),currentRoute==="clients"&&c(),ie(),R()}catch(X){console.error("saveClient fail",X);const ee=X&&X.message?X.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+ee,"fail")}}async function F(){if(!a)return;const k=e.find(ee=>ee.id===a);if(!k)return;const Y=t("client-delete-confirm").replace("{name}",k.name);if(await showConfirm(Y,{danger:!0}))try{await w(`/api/clients/${a}`,{method:"DELETE"}),showToast(t("client-msg-deleted"),"success"),E(),await g(),currentRoute==="clients"&&c(),ie(),R()}catch(ee){console.error(ee),showToast(t("client-msg-save-fail"),"fail")}}async function Q(k){const Y=e.find(X=>X.id===k);if(typeof window.openClientExportModal=="function"){window.openClientExportModal(k,Y?Y.name:"");return}try{const X=localStorage.getItem("mrpilot_token"),ee=await fetch(`/api/clients/${k}/export?month=all`,{headers:{Authorization:"Bearer "+X}});if(!ee.ok){let ae="HTTP "+ee.status;try{const d=await ee.json();d&&d.detail&&(ae=d.detail)}catch{}throw new Error(ae)}const re=await ee.blob();if(re.size<200){showToast(t("client-export-month-empty"),"info");return}const de=Y&&Y.name?Y.name.replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40):"client",pe=URL.createObjectURL(re),G=document.createElement("a");G.href=pe,G.download=`${de}_export.csv`,G.click(),URL.revokeObjectURL(pe)}catch(X){console.error("exportClient fail",X),showToast(t("client-msg-save-fail")+" · "+(X.message||""),"fail")}}function ie(){const k=document.getElementById("drawer-client-select");if(!k)return;const Y=k.value;k.innerHTML=`<option value="">${escapeHtml(t("drawer-client-none"))}</option>`+e.map(X=>`<option value="${X.id}">${escapeHtml(X.name)}</option>`).join(""),k.value=Y||""}window.bindDrawerClient=function(k,Y){const X=document.getElementById("drawer-client-select");if(!X)return;if(ie(),X.value=Y?String(Y):"",!k){X.onchange=null;const re=document.getElementById("drawer-client-add");re&&(re.onclick=()=>_(null));return}X.onchange=async()=>{const re=X.value?parseInt(X.value,10):null;try{await w(`/api/history/${k}/assign_client`,{method:"POST",body:JSON.stringify({client_id:re})}),showToast(t("client-msg-updated"),"success");const de=_results[_drawerIdx];de&&(de.client_id=re),await g()}catch(de){console.error(de),showToast(t("client-msg-save-fail"),"fail"),X.value=Y?String(Y):""}};const ee=document.getElementById("drawer-client-add");ee&&(ee.onclick=()=>_(null))};let le={fetched:0,items:[],supplier_count:0};window.fillCategoryDatalist=async function(){try{const k=document.getElementById("drawer-cat-datalist"),Y=Date.now();if(Y-le.fetched<300*1e3){k&&(k.innerHTML=le.items.map(ee=>`<option value="${escapeHtml(ee)}">`).join("")),ue(le.supplier_count);return}const X=await w("/api/categories",{method:"GET"});le.fetched=Y,le.items=X&&X.categories||[],le.supplier_count=X&&X.supplier_count||0,k&&(k.innerHTML=le.items.map(ee=>`<option value="${escapeHtml(ee)}">`).join("")),ue(le.supplier_count)}catch(k){console.warn("fillCategoryDatalist failed",k)}};function ue(k){const Y=document.getElementById("drawer-cat-learned-tag");Y&&k>0&&(Y.textContent=(t("drawer-suggest-learned-with-count")||"已学 {n}").replace("{n}",k))}function R(){const k=document.getElementById("history-client-filter");if(!k)return;const Y=k.value;k.innerHTML=`<option value="">${escapeHtml(t("history-client-all"))}</option>`+e.map(X=>`<option value="${X.id}">${escapeHtml(X.name)}</option>`).join(""),k.value=Y||""}window.getHistoryClientFilter=function(){return n},document.addEventListener("DOMContentLoaded",()=>{const k=document.querySelector(".cust-tab-bar");k&&k.addEventListener("click",ne=>{const ce=ne.target.closest("[data-cust-tab]");ce&&B(ce.dataset.custTab)});const Y=document.getElementById("btn-buyer-new");Y&&Y.addEventListener("click",()=>_(null));const X=document.getElementById("buyer-tbody");X&&X.addEventListener("click",ne=>{const ce=ne.target.closest(".buyer-row-check");if(ce){const ge=parseInt(ce.dataset.cid,10);ce.checked?f.add(ge):f.delete(ge);const we=ce.closest(".cust-row");we&&we.classList.toggle("selected",ce.checked),y();return}const fe=ne.target.closest(".cust-row-btn");if(fe){ne.stopPropagation();const ge=parseInt(fe.dataset.cid,10);if(fe.dataset.action==="edit"){const we=e.find(ke=>ke.id===ge);we&&_(we)}else fe.dataset.action==="export"&&Q(ge);return}const ve=ne.target.closest(".cust-row");if(ve&&!ne.target.closest(".cust-cell-check")){const ge=e.find(we=>we.id===parseInt(ve.dataset.cid,10));ge&&_(ge)}});const ee=document.getElementById("buyer-check-all");ee&&ee.addEventListener("change",()=>{const{items:ne}=u();ne.forEach(ce=>{ee.checked?f.add(ce.id):f.delete(ce.id)}),c()});const re=document.getElementById("buyer-batch-cancel");re&&re.addEventListener("click",$);const de=document.getElementById("buyer-batch-delete");de&&de.addEventListener("click",T);const pe=document.getElementById("buyer-prev");pe&&pe.addEventListener("click",()=>{l.page>0&&(l.page--,c())});const G=document.getElementById("buyer-next");G&&G.addEventListener("click",()=>{l.page++,c()});const ae=document.getElementById("buyer-search");if(ae){let ne;ae.addEventListener("input",()=>{clearTimeout(ne),ne=setTimeout(()=>{l.keyword=ae.value,l.page=0;const ce=document.getElementById("buyer-search-clear");ce&&(ce.style.display=ae.value?"":"none"),c()},200)})}const d=document.getElementById("buyer-search-clear");d&&d.addEventListener("click",()=>{const ne=document.getElementById("buyer-search");ne&&(ne.value=""),l.keyword="",l.page=0,d.style.display="none",c()});const m=document.getElementById("btn-seller-new");m&&m.addEventListener("click",()=>L(null));const q=document.getElementById("seller-tbody");q&&q.addEventListener("click",ne=>{const ce=ne.target.closest("[data-saction]");if(!ce)return;ne.stopPropagation();const fe=parseInt(ce.dataset.wid,10),ve=ce.dataset.saction,ge=h.find(we=>Number(we.id)===fe);ve==="activate"?(typeof window.setActiveWorkspaceClientId=="function"&&window.setActiveWorkspaceClientId(fe),M(),typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl(),showToast(t("seller-activated").replace("{name}",ge?ge.name:""),"success")):ve==="edit"?ge&&L(ge):ve==="archive"&&(o=fe,W())});const Z=document.getElementById("seller-search");if(Z){let ne;Z.addEventListener("input",()=>{clearTimeout(ne),ne=setTimeout(()=>{x.keyword=Z.value;const ce=document.getElementById("seller-search-clear");ce&&(ce.style.display=Z.value?"":"none"),M()},200)})}const i=document.getElementById("seller-search-clear");i&&i.addEventListener("click",()=>{const ne=document.getElementById("seller-search");ne&&(ne.value=""),x.keyword="",i.style.display="none",M()});const v=document.getElementById("wsclient-modal-close");v&&v.addEventListener("click",z);const b=document.getElementById("wsclient-modal-cancel");b&&b.addEventListener("click",z);const j=document.getElementById("wsclient-modal-save");j&&j.addEventListener("click",V);const H=document.getElementById("wsclient-modal-archive");H&&H.addEventListener("click",W);const r=document.getElementById("wsclient-modal-mask");r&&r.addEventListener("click",ne=>{ne.target===r&&z()});const C=document.getElementById("client-modal-close");C&&C.addEventListener("click",E);const A=document.getElementById("client-modal-cancel");A&&A.addEventListener("click",E);const O=document.getElementById("client-modal-save");O&&O.addEventListener("click",J);const K=document.getElementById("client-modal-delete");K&&K.addEventListener("click",F);const te=document.getElementById("client-modal-mask");te&&te.addEventListener("click",ne=>{ne.target===te&&E()});const oe=document.getElementById("client-color-picker");oe&&oe.addEventListener("click",ne=>{const ce=ne.target.closest(".color-swatch");ce&&(oe.querySelectorAll(".color-swatch").forEach(fe=>fe.classList.remove("active")),ce.classList.add("active"))});const se=document.getElementById("history-client-filter");se&&se.addEventListener("change",()=>{n=se.value,typeof renderHistoryList=="function"&&renderHistoryList()})}),setTimeout(()=>g(),1e3)})();(function(){const e=document.getElementById("page-exceptions");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
        <div class="page-head">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M11 3.4L3.6 16.5a1.5 1.5 0 001.3 2.3h14.2a1.5 1.5 0 001.3-2.3L13 3.4a1.5 1.5 0 00-2 0z"/>
                    <line x1="12" y1="9" x2="12" y2="14"/>
                    <circle cx="12" cy="16.8" r="0.8" fill="currentColor"/>
                </svg>
            </div>
            <div class="page-head-text">
                <h1 class="page-title" data-i18n="exc-title">异常栏</h1>
                <div class="page-subtitle" data-i18n="exc-sub">所有被规则拦截的单据集中复核 · 系统会从你的判断中学习</div>
            </div>
            <div class="page-head-actions">
                <select class="history-range" id="exc-client-filter">
                    <option value="" data-i18n="history-client-all">全部客户</option>
                </select>
                <button class="btn btn-ghost" id="btn-exc-refresh" type="button">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 8a5 5 0 019-3l1.5 1.5M13 8a5 5 0 01-9 3L2.5 9.5M13 3v3h-3M3 13v-3h3"/>
                    </svg>
                    <span data-i18n="exc-refresh">刷新</span>
                </button>
            </div>
        </div>

        <!-- ERP 推送异常块(独立来源 · Zihao 2026-05-26)· 派生自 erp_push_logs ·
             0 条时隐藏 · 内容(标题/chip/卡片)全由 JS renderErpExceptions 填充 -->
        <div class="erp-exc-block" id="erp-exc-block" hidden></div>

        <!-- 顶部 4 KPI -->
        <div class="exc-kpi-row" id="exc-kpi-row">
            <div class="exc-kpi">
                <div class="exc-kpi-value" id="exc-kpi-pending">—</div>
                <div class="exc-kpi-label" data-i18n="exc-kpi-pending">待复核</div>
            </div>
            <div class="exc-kpi exc-kpi-danger">
                <div class="exc-kpi-value" id="exc-kpi-high">—</div>
                <div class="exc-kpi-label" data-i18n="exc-kpi-high">高危异常</div>
            </div>
            <div class="exc-kpi">
                <div class="exc-kpi-value" id="exc-kpi-resolved">—</div>
                <div class="exc-kpi-label" data-i18n="exc-kpi-resolved">已处理</div>
            </div>
            <div class="exc-kpi">
                <div class="exc-kpi-value" id="exc-kpi-learned">—</div>
                <div class="exc-kpi-label" data-i18n="exc-kpi-learned">已学习规则</div>
            </div>
        </div>

        <!-- v118.21.1 · 状态切换(待复核 / 已处理 / 已忽略) -->
        <div class="exc-status-tabs" id="exc-status-tabs">
            <button class="exc-status-tab active" data-status="pending" type="button">
                <span data-i18n="exc-status-pending">待复核</span>
                <span class="exc-status-tab-count" id="exc-status-tab-count-pending">0</span>
            </button>
            <button class="exc-status-tab" data-status="resolved" type="button">
                <span data-i18n="exc-status-resolved">已处理</span>
                <span class="exc-status-tab-count" id="exc-status-tab-count-resolved">0</span>
            </button>
            <button class="exc-status-tab" data-status="ignored" type="button">
                <span data-i18n="exc-status-ignored">已忽略</span>
                <span class="exc-status-tab-count" id="exc-status-tab-count-ignored">0</span>
            </button>
        </div>

        <!-- 筛选 chips -->
        <div class="exc-chips" id="exc-chips">
            <!-- chips 由 JS 渲染(因为要带计数 · 且要根据 stats by_rule 动态显示) -->
        </div>

        <!-- v118.20.5 · 批量栏(选中 ≥1 时浮现) -->
        <div class="exc-batch-bar" id="exc-batch-bar" style="display:none;">
            <div class="exc-batch-info">
                <button class="exc-batch-clear" id="exc-batch-clear" type="button" aria-label="clear">
                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 3l8 8M3 11l8-8"/>
                    </svg>
                </button>
                <span class="exc-batch-count" id="exc-batch-count">0</span>
            </div>
            <div class="exc-batch-actions">
                <button class="btn btn-ghost" id="exc-batch-ignore" type="button">
                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="7" cy="7" r="5.5"/>
                        <line x1="4" y1="4" x2="10" y2="10"/>
                    </svg>
                    <span data-i18n="exc-batch-ignore">全部忽略此类</span>
                </button>
                <button class="btn btn-primary" id="exc-batch-resolve" type="button">
                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M2.5 7l3 3 6-6"/>
                    </svg>
                    <span data-i18n="exc-batch-resolve">全部放行</span>
                </button>
            </div>
        </div>

        <!-- 列表 -->
        <div class="exc-list" id="exc-list">
            <div class="exc-loading" data-i18n="exc-loading">加载中…</div>
        </div>

        <!-- v118.20.5 · 列表底部:计数 + 加载更多 -->
        <div class="exc-list-foot" id="exc-list-foot" style="display:none;">
            <span class="exc-list-count" id="exc-list-count">—</span>
            <button class="btn btn-ghost" id="exc-loadmore" type="button" style="display:none;">
                <span data-i18n="exc-loadmore">加载更多</span>
            </button>
        </div>
`,e.dataset.wbInjected="1";try{const a=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",n=window.I18N;n&&n[a]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const l=s.getAttribute("data-i18n");n[a][l]&&(s.textContent=n[a][l])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const l=s.getAttribute("data-i18n-placeholder");n[a][l]&&(s.placeholder=n[a][l])}))}catch{}}})();(function(){let e={statsCache:null,listCache:[],currentRule:null,currentClient:"",currentStatus:"pending",loading:!1,selectedIds:new Set,offset:0,pageSize:50,total:0,loadFailed:!1,listScrollY:0};function a(d,m){let q=t(d)||d;if(m)for(const Z in m)q=q.replace(new RegExp("\\{"+Z+"\\}","g"),String(m[Z]));return q}async function n(){try{const d=e.currentClient||"",m="/api/exceptions/stats?status=pending"+(d?"&client_id="+encodeURIComponent(d):""),q=await fetch(m,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!q.ok)return;const Z=await q.json(),i=document.getElementById("nav-exc-badge");if(!i)return;const v=parseInt(Z.pending||0,10);v>0?(i.textContent=v>99?"99+":String(v),i.style.display=""):i.style.display="none"}catch{}}function s(d){return d==="high"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M7 1.5L1 12.5h12L7 1.5z"/>
                <line x1="7" y1="6" x2="7" y2="9"/>
                <circle cx="7" cy="10.6" r="0.5" fill="currentColor"/>
            </svg>`:d==="medium"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="7" cy="7" r="5.5"/>
                <line x1="7" y1="4" x2="7" y2="7.5"/>
                <circle cx="7" cy="9.5" r="0.5" fill="currentColor"/>
            </svg>`:`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="7" cy="7" r="5.5"/>
            <line x1="4.5" y1="7" x2="9.5" y2="7"/>
        </svg>`}function l(){return`<svg class="exc-empty-icon" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 19l5 5 13-13"/>
            <circle cx="20" cy="20" r="17"/>
        </svg>`}function f(d){if(d==null)return"—";const m=parseFloat(d);return isNaN(m)?"—":"฿ "+m.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function h(d){return d?d.slice(0,10):"—"}function x(d){document.getElementById("exc-kpi-pending").textContent=d.pending||0,document.getElementById("exc-kpi-high").textContent=d.high_severity||0,document.getElementById("exc-kpi-resolved").textContent=d.resolved||0,document.getElementById("exc-kpi-learned").textContent=d.learned_rules||0;const m=document.getElementById("exc-status-tab-count-pending"),q=document.getElementById("exc-status-tab-count-resolved"),Z=document.getElementById("exc-status-tab-count-ignored");m&&(m.textContent=d.pending||0),q&&(q.textContent=d.resolved||0),Z&&(Z.textContent=d.ignored||0),document.querySelectorAll("#exc-status-tabs .exc-status-tab").forEach(v=>{v.classList.toggle("active",v.dataset.status===(e.currentStatus||"pending"))})}function o(d){const m=document.getElementById("exc-chips");if(!m)return;const q=d.by_rule||{},Z=["confidence_low","duplicate","amount_missing","math_mismatch","tax_id_format_invalid"];let v=`<button class="exc-chip ${!e.currentRule?"active":""}" data-rule="">
            <span>${escapeHtml(t("exc-chip-all"))}</span>
            <span class="exc-chip-count">${d.pending||0}</span>
        </button>`;for(const b of Z){const j=q[b]||0;if(j===0&&e.currentRule!==b)continue;const H=e.currentRule===b;v+=`<button class="exc-chip ${H?"active":""}" data-rule="${escapeHtml(b)}">
                <span>${escapeHtml(t("exc-chip-"+b))}</span>
                <span class="exc-chip-count">${j}</span>
            </button>`}m.innerHTML=v,m.querySelectorAll(".exc-chip").forEach(b=>{b.addEventListener("click",()=>{const j=b.dataset.rule||null;e.currentRule=j,I()})})}function p(d){const m=document.getElementById("exc-list");if(!m)return;if(!d||d.length===0){m.innerHTML=`<div class="exc-empty">
                ${l()}
                <div class="exc-empty-title">${escapeHtml(t("exc-empty-title"))}</div>
                <div>${escapeHtml(t("exc-empty-desc"))}</div>
            </div>`,g();return}const q='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7l3 3 5-5"/></svg>',Z=(e.currentStatus||"pending")==="pending";m.innerHTML=d.map(i=>{const v=i.severity||"medium",b=t("exc-rule-"+i.rule_code)||i.rule_code,j=i.seller_name&&i.seller_name.trim()?i.seller_name:t("exc-no-seller"),H=i.filename||"—",r=h(i.invoice_date||i.created_at),C=i.status==="pending",A=e.selectedIds.has(i.id),O=Z&&C;return`
                <div class="exc-row sev-${escapeHtml(v)} ${A?"selected":""}" data-exc-id="${escapeHtml(String(i.id))}">
                    <div class="exc-row-check ${A?"checked":""}" data-check-id="${escapeHtml(String(i.id))}" ${O?"":'style="visibility:hidden;"'}>${q}</div>
                    <div class="exc-row-sev">${s(v)}</div>
                    <div class="exc-row-main">
                        <div class="exc-row-title">${escapeHtml(j)} · ${escapeHtml(H)}</div>
                        <div class="exc-row-meta">
                            ${i.invoice_no?`<span><b>${escapeHtml(i.invoice_no)}</b></span>`:""}
                            <span>${escapeHtml(r)}</span>
                        </div>
                    </div>
                    <div class="exc-row-rule r-${escapeHtml(v)}">${escapeHtml(b)}</div>
                    <div class="exc-row-amount">${escapeHtml(f(i.total_amount))}</div>
                </div>
            `}).join(""),m.querySelectorAll(".exc-row").forEach(i=>{i.addEventListener("click",v=>{if(v.target.closest(".exc-row-check"))return;const b=i.dataset.excId;b&&J(parseInt(b,10))})}),m.querySelectorAll(".exc-row-check").forEach(i=>{i.addEventListener("click",v=>{v.stopPropagation();const b=parseInt(i.dataset.checkId,10);b&&(e.selectedIds.has(b)?(e.selectedIds.delete(b),i.classList.remove("checked"),i.closest(".exc-row").classList.remove("selected")):(e.selectedIds.add(b),i.classList.add("checked"),i.closest(".exc-row").classList.add("selected")),w())})}),w(),g()}function w(){const d=document.getElementById("exc-batch-bar"),m=document.getElementById("exc-batch-count");if(!d||!m)return;const q=e.selectedIds.size;q===0?d.style.display="none":(d.style.display="",m.textContent=a("exc-batch-count",{n:q}))}function g(){const d=document.getElementById("exc-list-foot"),m=document.getElementById("exc-list-count"),q=document.getElementById("exc-loadmore");if(!d||!m||!q)return;const Z=e.listCache.length;if(Z===0){d.style.display="none";return}d.style.display="";let i=Z;const v=e.statsCache;v&&(e.currentRule?i=(v.by_rule||{})[e.currentRule]||Z:i=v.pending||Z),e.total=i,m.textContent=a("exc-list-count",{shown:Z,total:i});const b=Z<i&&Z<500;q.style.display=b?"":"none"}async function B(){try{if(navigator.onLine===!1)throw new Error("offline");const d=e.currentClient||"",m=e.currentStatus||"pending",q=new URLSearchParams;q.set("status",m),d&&q.set("client_id",d);const Z="/api/exceptions/stats?"+q.toString(),i=await fetch(Z,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!i.ok)throw new Error("http "+i.status);const v=await i.json();return e.statsCache=v,x(v),o(v),v}catch(d){return console.warn("loadExceptionsStats fail",d),null}}function S(d){const m=document.getElementById("exc-list");if(!m)return;const q=`<svg class="exc-error-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="18" cy="18" r="14"/>
            <line x1="18" y1="11" x2="18" y2="19"/>
            <circle cx="18" cy="23" r="0.8" fill="currentColor"/>
        </svg>`,Z=d?t("exc-offline"):t("exc-error-retry-title"),i=d?"":t("exc-error-retry-desc");m.innerHTML=`
            <div class="exc-error">
                ${q}
                <div class="exc-error-msg">${escapeHtml(Z)}${i?" · "+escapeHtml(i):""}</div>
                <button class="exc-retry-btn" id="exc-retry-btn" type="button">${escapeHtml(t("exc-retry-btn"))}</button>
            </div>`;const v=document.getElementById("exc-retry-btn");v&&v.addEventListener("click",()=>window.loadExceptionsPage&&window.loadExceptionsPage())}async function I(d){d=d||{};const m=!!d.append,q=document.getElementById("exc-list");!m&&q&&e.listCache.length===0&&(q.innerHTML=`<div class="exc-loading">${escapeHtml(t("exc-loading"))}</div>`);const Z=new URLSearchParams;Z.set("status",e.currentStatus||"pending"),e.currentRule&&Z.set("rule_code",e.currentRule),e.currentClient&&Z.set("client_id",e.currentClient);const i=m?e.listCache.length:0;Z.set("limit",String(e.pageSize)),Z.set("offset",String(i));try{if(navigator.onLine===!1)throw new Error("offline");const v=await fetch("/api/exceptions/list?"+Z.toString(),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!v.ok)throw new Error("http "+v.status);const j=(await v.json()).items||[];m?e.listCache=e.listCache.concat(j):(e.listCache=j,e.selectedIds.clear()),e.loadFailed=!1,p(e.listCache),e.statsCache&&o(e.statsCache)}catch(v){console.warn("loadExceptionsList fail",v),e.loadFailed=!0;const b=navigator.onLine===!1||String(v.message||"").includes("offline");m?showToast(t("exc-toast-load-fail"),"error"):(S(b),showToast(b?t("exc-offline"):t("exc-toast-load-fail"),"error"))}}async function U(){if(!e.loading&&!(e.listCache.length>=500)){e.loading=!0;try{await I({append:!0})}finally{e.loading=!1}}}function N(){const d=document.getElementById("exc-client-filter");if(!d)return;const m=window._clientsCache||[],q=e.currentClient||"",Z=typeof t=="function"?t("history-client-all"):"全部客户";d.innerHTML=`<option value="">${escapeHtml(Z)}</option>`+m.map(i=>`<option value="${i.id}">${escapeHtml(i.name)}</option>`).join(""),d.value=q}window.loadExceptionsPage=async function(){if(!e.loading){e.loading=!0;try{N(),y(),await B(),await I()}finally{e.loading=!1}}};let M={items:[],q:"",cat:"",selected:new Set,total:0,categories:{},pageSize:30,loading:!1,focusSearch:!1,searchCaret:0},L=null;function z(){return localStorage.getItem("mrpilot_token")||""}function V(d){const m=typeof currentLang=="string"&&currentLang||window._currentLang||"th",q=d.error_friendly&&d.error_friendly[m];if(q)return q;if(typeof humanizeError=="function"&&d.error_msg)try{return humanizeError(d.error_msg)}catch{}return t("erp-exc-reason-"+(d.category||"other"))}function W(){const d=document.getElementById("erp-exc-batch");if(!d)return;const m=M.selected.size;d.hidden=m===0;const q=d.querySelector(".erp-exc-batch-count");q&&(q.textContent=String(m))}function P(){const d=document.getElementById("erp-exc-block");if(!d)return;const m=M;if(!(m.total>0||!!m.q||!!m.cat)){d.hidden=!0,d.innerHTML="";return}d.hidden=!1;const Z=m.categories||{},i=Object.keys(Z).reduce((te,oe)=>te+Z[oe],0);let v=`<button class="erp-exc-chip ${m.cat===""?"active":""}" data-erpexc-cat=""><span>${escapeHtml(t("erp-exc-cat-all"))}</span><span class="erp-exc-chip-count">${i}</span></button>`;Object.keys(Z).forEach(te=>{v+=`<button class="erp-exc-chip ${m.cat===te?"active":""}" data-erpexc-cat="${escapeHtml(te)}"><span>${escapeHtml(t("erp-exc-cat-"+te))}</span><span class="erp-exc-chip-count">${Z[te]}</span></button>`});const b=m.items||[],j=b.length>0&&b.every(te=>m.selected.has(te.id)),H=b.map(te=>{const oe=te.state==="needs_action"?"needs":te.state==="retrying"?"retry":"fail",se=t("erp-exc-state-"+(te.state||"failed")),ne=V(te),ce=m.selected.has(te.id)?"checked":"";return`<div class="erp-exc-row" data-erpexc-id="${escapeHtml(te.id)}">
                <span class="ex-cb"><input type="checkbox" class="erp-exc-cb" data-erpexc-cb="${escapeHtml(te.id)}" ${ce}></span>
                <span class="ex-inv" title="${escapeHtml(te.invoice_no||"")}">${escapeHtml(te.invoice_no||"—")}</span>
                <span class="ex-seller" title="${escapeHtml(te.seller_name||"")}">${escapeHtml(te.seller_name||"—")}</span>
                <span class="ex-buyer" title="${escapeHtml(te.ocr_buyer_name||"")}">${escapeHtml(te.ocr_buyer_name||"—")}</span>
                <span class="ex-state"><span class="erp-exc-state ${oe}">${escapeHtml(se)}</span></span>
                <span class="ex-reason" title="${escapeHtml(ne)}">${escapeHtml(ne)}${te.error_code?` <span class="erp-exc-code">${escapeHtml(te.error_code)}</span>`:""}</span>
                <span class="ex-act"><button class="erp-exc-retry-btn" type="button" data-erpexc-retry="${escapeHtml(te.id)}">${escapeHtml(t("erp-exc-retry"))}</button></span>
            </div>`}).join(""),r=b.length===0?`<div class="erp-exc-empty">${escapeHtml(t("erp-exc-empty"))}</div>`:"",C=b.length<m.total?`<button class="erp-exc-more" type="button" id="erp-exc-more">${escapeHtml(t("erp-exc-load-more"))} (${b.length}/${m.total})</button>`:m.total>0?`<div class="erp-exc-count">${escapeHtml(t("erp-exc-shown",{n:b.length,total:m.total}))}</div>`:"";d.innerHTML=`
            <div class="erp-exc-head">
                <h2 class="erp-exc-title">${escapeHtml(t("erp-exc-title"))}</h2>
                <span class="erp-exc-sub">${escapeHtml(t("erp-exc-sub"))}</span>
                <input type="search" class="erp-exc-search" id="erp-exc-search" placeholder="${escapeHtml(t("erp-exc-search-ph"))}" value="${escapeHtml(m.q)}">
            </div>
            <div class="erp-exc-chips">${v}</div>
            <div class="erp-exc-batch" id="erp-exc-batch" ${m.selected.size?"":"hidden"}>
                <span class="erp-exc-batch-info"><span class="erp-exc-batch-count">${m.selected.size}</span> ${escapeHtml(t("erp-exc-batch-selected"))}</span>
                <button class="erp-exc-batch-btn" type="button" data-erpexc-batch="retry">${escapeHtml(t("erp-exc-batch-retry"))}</button>
                <button class="erp-exc-batch-btn danger" type="button" data-erpexc-batch="delete">${escapeHtml(t("erp-exc-batch-delete"))}</button>
                <button class="erp-exc-batch-btn ghost" type="button" data-erpexc-batch="clear">${escapeHtml(t("erp-exc-batch-clear"))}</button>
            </div>
            <div class="erp-exc-rows">
                <div class="erp-exc-row erp-exc-row-head">
                    <span class="ex-cb"><input type="checkbox" class="erp-exc-cb-all" id="erp-exc-cb-all" ${j?"checked":""}></span>
                    <span class="ex-inv">${escapeHtml(t("erp-exc-f-invoice"))}</span>
                    <span class="ex-seller">${escapeHtml(t("erp-exc-f-seller"))}</span>
                    <span class="ex-buyer">${escapeHtml(t("erp-exc-f-buyer"))}</span>
                    <span class="ex-state">${escapeHtml(t("erp-exc-f-state"))}</span>
                    <span class="ex-reason">${escapeHtml(t("erp-exc-f-reason"))}</span>
                    <span class="ex-act"></span>
                </div>
                ${H}${r}
            </div>
            <div class="erp-exc-foot">${C}</div>`;const A=document.getElementById("erp-exc-search");if(A){if(m.focusSearch){A.focus();try{A.setSelectionRange(m.searchCaret,m.searchCaret)}catch{}}A.addEventListener("input",()=>{m.q=A.value,m.focusSearch=!0,m.searchCaret=A.selectionStart||A.value.length,clearTimeout(L),L=setTimeout(()=>y(!1),350)}),A.addEventListener("blur",()=>{m.focusSearch=!1})}d.querySelectorAll(".erp-exc-chip").forEach(te=>{te.addEventListener("click",()=>{m.cat=te.dataset.erpexcCat||"",y(!1)})}),d.querySelectorAll("[data-erpexc-retry]").forEach(te=>{te.addEventListener("click",oe=>{oe.stopPropagation(),u(te.dataset.erpexcRetry,te)})}),d.querySelectorAll(".erp-exc-cb").forEach(te=>{te.addEventListener("change",()=>{const oe=te.dataset.erpexcCb;te.checked?m.selected.add(oe):m.selected.delete(oe);const se=document.getElementById("erp-exc-cb-all");se&&(se.checked=b.length>0&&b.every(ne=>m.selected.has(ne.id))),W()})});const O=document.getElementById("erp-exc-cb-all");O&&O.addEventListener("change",()=>{b.forEach(te=>{O.checked?m.selected.add(te.id):m.selected.delete(te.id)}),d.querySelectorAll(".erp-exc-cb").forEach(te=>{te.checked=O.checked}),W()}),d.querySelectorAll("[data-erpexc-batch]").forEach(te=>{te.addEventListener("click",()=>c(te.dataset.erpexcBatch))});const K=document.getElementById("erp-exc-more");K&&K.addEventListener("click",()=>y(!0)),d.querySelectorAll(".erp-exc-row:not(.erp-exc-row-head)").forEach(te=>{te.addEventListener("click",oe=>{oe.target.closest("input,button")||typeof window._erpExcOpenEdit=="function"&&window._erpExcOpenEdit(te.dataset.erpexcId)})})}async function u(d,m){if(d){m&&(m.disabled=!0,m.textContent=t("erp-exc-retrying"));try{const q=await fetch("/api/erp/logs/"+encodeURIComponent(d)+"/retry",{method:"POST",headers:{Authorization:"Bearer "+z()}}),Z=await q.json().catch(()=>({}));showToast(q.ok&&Z.ok?t("erp-exc-retry-ok"):t("erp-exc-retry-fail"),q.ok&&Z.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(M.selected.delete(d),y(!1),typeof n=="function")try{n()}catch{}}}async function c(d){const m=Array.from(M.selected);if(d==="clear"){M.selected.clear(),P();return}if(m.length!==0){if(d==="delete"){if(!await showConfirm(t("erp-exc-batch-delete-confirm",{n:m.length}),{danger:!0}))return;try{const Z=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+z(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:m.slice(0,200)})}),i=await Z.json().catch(()=>({}));showToast(Z.ok?t("erp-exc-batch-delete-ok",{n:i.deleted||0}):t("erp-exc-retry-fail"),Z.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}}else if(d==="retry")try{const q=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+z(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:m.slice(0,50)})}),Z=await q.json().catch(()=>({}));showToast(q.ok?t("erp-exc-batch-retry-ok",{ok:Z.succeeded||0,fail:(Z.failed||0)+(Z.skipped||0)}):t("erp-exc-retry-fail"),q.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(M.selected.clear(),y(!1),typeof n=="function")try{n()}catch{}}}async function y(d){const m=document.getElementById("erp-exc-block");if(!(!m||M.loading)){M.loading=!0;try{const q=new URLSearchParams;M.q&&q.set("q",M.q),M.cat&&q.set("category",M.cat),q.set("limit",String(M.pageSize)),q.set("offset",String(d?M.items.length:0));const Z=await fetch("/api/erp/exceptions?"+q.toString(),{headers:{Authorization:"Bearer "+z()}});if(!Z.ok){d||(m.hidden=!0);return}const i=await Z.json(),v=i.items||[];M.items=d?M.items.concat(v):v,M.total=i.total||0,M.categories=i.categories||{},P()}catch{d||(m.hidden=!0)}finally{M.loading=!1}}}let $={};function T(){const d=document.getElementById("erp-exc-modal");d&&d.remove()}window._erpExcOpenEdit=function(d){const m=(M.items||[]).find(r=>String(r.id)===String(d));if(!m)return;const q=!!m.history_client_id&&m.category==="customer_mismatch",Z=m.category==="product_mismatch"&&!!m.history_id&&!!m.endpoint_id,i=V(m),v=m.state==="needs_action"?"needs":m.state==="retrying"?"retry":"fail",b=(r,C)=>`<div class="erp-exc-m-row"><span class="erp-exc-m-k">${escapeHtml(r)}</span><span class="erp-exc-m-v">${escapeHtml(C||"—")}</span></div>`;let j="";if(q)j=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-pick"))}</div>
                    <input type="search" class="erp-exc-m-search" id="erp-exc-m-search" placeholder="${escapeHtml(t("erp-exc-edit-pick-ph"))}">
                    <div class="erp-exc-m-custlist" id="erp-exc-m-custlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-pick-loading"))}</div>
                    </div>
                </div>`;else if(Z)j=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-prod-intro"))}</div>
                    <div class="erp-exc-m-custlist" id="erp-exc-m-prodlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-prod-loading"))}</div>
                    </div>
                </div>`;else{const r="erp-exc-edit-hint-"+(m.category||"other");let C=t(r);(!C||C===r)&&(C=i),j=`<div class="erp-exc-m-hint">${escapeHtml(C)}</div>`}const H=document.createElement("div");if(H.id="erp-exc-modal",H.className="erp-exc-modal-overlay",H.innerHTML=`
            <div class="erp-exc-modal" role="dialog" aria-modal="true">
                <div class="erp-exc-m-head">
                    <h3>${escapeHtml(t("erp-exc-edit-title"))}</h3>
                    <button class="erp-exc-m-close" type="button" id="erp-exc-m-close" aria-label="close">×</button>
                </div>
                <div class="erp-exc-m-body">
                    <div class="erp-exc-m-reason"><span class="erp-exc-state ${v}">${escapeHtml(t("erp-exc-state-"+(m.state||"failed")))}</span> ${escapeHtml(i)}${m.error_code?` <span class="erp-exc-code">${escapeHtml(m.error_code)}</span>`:""}</div>
                    ${b(t("erp-exc-f-invoice"),m.invoice_no)}
                    ${b(t("erp-exc-f-seller"),m.seller_name)}
                    ${b(t("erp-exc-f-buyer"),m.ocr_buyer_name)}
                    ${b(t("erp-exc-edit-field-current"),m.client_name)}
                    ${j}
                </div>
                <div class="erp-exc-m-foot">
                    <button class="erp-exc-batch-btn ghost" type="button" id="erp-exc-m-cancel">${escapeHtml(t("erp-exc-edit-close"))}</button>
                    <button class="erp-exc-batch-btn" type="button" id="erp-exc-m-retry">${escapeHtml(t("erp-exc-edit-retry"))}</button>
                    ${q?`<button class="erp-exc-batch-btn" type="button" id="erp-exc-m-bind" disabled>${escapeHtml(t("erp-exc-edit-bind-retry"))}</button>`:""}
                    ${Z?`<button class="erp-exc-batch-btn" type="button" id="erp-exc-m-bind-prod" disabled>${escapeHtml(t("erp-exc-edit-bind-prod-retry"))}</button>`:""}
                </div>
            </div>`,document.body.appendChild(H),H.addEventListener("click",r=>{r.target===H&&T()}),document.getElementById("erp-exc-m-close").addEventListener("click",T),document.getElementById("erp-exc-m-cancel").addEventListener("click",T),document.getElementById("erp-exc-m-retry").addEventListener("click",()=>{T(),u(m.id,null)}),q){let r="";const C=document.getElementById("erp-exc-m-bind"),A=document.getElementById("erp-exc-m-custlist"),O=document.getElementById("erp-exc-m-search"),K=(oe,se)=>{const ne=(se||"").trim().toLowerCase(),ce=ne?oe.filter(fe=>(fe.code||"").toLowerCase().includes(ne)||(fe.name||"").toLowerCase().includes(ne)):oe;if(ce.length===0){A.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-empty"))}</div>`;return}A.innerHTML=ce.slice(0,100).map(fe=>`<div class="erp-exc-m-cust" data-cust-code="${escapeHtml(fe.code||"")}">
                        <span class="erp-exc-m-cust-name">${escapeHtml(fe.name||"")}</span>
                        <span class="erp-exc-m-cust-code">${escapeHtml(fe.code||"")}</span>
                    </div>`).join(""),A.querySelectorAll(".erp-exc-m-cust").forEach(fe=>{fe.addEventListener("click",()=>{r=fe.dataset.custCode||"",A.querySelectorAll(".erp-exc-m-cust").forEach(ve=>ve.classList.remove("sel")),fe.classList.add("sel"),C&&(C.disabled=!r)})})},te=async()=>{const oe=m.endpoint_id;if($[oe]){K($[oe],"");return}try{const se=await fetch("/api/erp/endpoints/"+encodeURIComponent(oe)+"/customers",{headers:{Authorization:"Bearer "+z()}}),ne=await se.json().catch(()=>({}));if(!se.ok||!ne.ok){A.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`;return}const ce=ne.customers||[];$[oe]=ce,K(ce,"")}catch{A.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`}};O&&O.addEventListener("input",()=>K($[m.endpoint_id]||[],O.value)),te(),C&&C.addEventListener("click",async()=>{if(r){C.disabled=!0,C.textContent=t("erp-exc-retrying");try{if(!(await fetch("/api/erp/mappings/clients",{method:"POST",headers:{Authorization:"Bearer "+z(),"Content-Type":"application/json"},body:JSON.stringify({client_id:m.history_client_id,erp_type:m.endpoint_adapter,erp_code:r})})).ok){showToast(t("erp-exc-retry-fail"),"error"),C.disabled=!1,C.textContent=t("erp-exc-edit-bind-retry");return}showToast(t("erp-exc-edit-bound-ok"),"success"),T(),await u(m.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),C.disabled=!1,C.textContent=t("erp-exc-edit-bind-retry")}}})}if(Z){const r=document.getElementById("erp-exc-m-bind-prod"),C=document.getElementById("erp-exc-m-prodlist"),A={};let O=[];const K=()=>'<option value="">'+escapeHtml(t("erp-exc-edit-prod-choose"))+"</option>"+O.slice(0,500).map(se=>`<option value="${escapeHtml(se.code||"")}" data-pname="${escapeHtml(se.name||"")}">`+escapeHtml((se.name||"")+" · "+(se.code||""))+"</option>").join(""),te=se=>{if(!se.length){C.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-noitems"))}</div>`;return}C.innerHTML=se.map(ne=>`<div class="erp-exc-m-cust" style="cursor:default">
                        <span class="erp-exc-m-cust-name" title="${escapeHtml(ne)}">${escapeHtml(ne)}</span>
                        <select class="erp-exc-m-prod-sel" data-item="${escapeHtml(ne)}" style="max-width:55%;flex:0 0 auto;padding:4px 6px;border:1px solid var(--border,#e5e7eb);border-radius:6px;font-size:12px">${K()}</select>
                    </div>`).join(""),C.querySelectorAll(".erp-exc-m-prod-sel").forEach(ne=>{ne.addEventListener("change",()=>{const ce=ne.dataset.item,fe=ne.options[ne.selectedIndex];ne.value?A[ce]={code:ne.value,name:fe&&fe.dataset.pname||""}:delete A[ce],r&&(r.disabled=Object.keys(A).length===0)})})};(async()=>{try{const ne=await(await fetch("/api/history/"+encodeURIComponent(m.history_id),{headers:{Authorization:"Bearer "+z()}})).json().catch(()=>({})),ce=ne&&ne.pages||[],fe=[],ve={};(Array.isArray(ce)?ce:[]).forEach(ke=>{const Le=ke&&ke.fields&&ke.fields.items||[];(Array.isArray(Le)?Le:[]).forEach(Be=>{const Ie=(Be&&(Be.name||Be.description)||"").trim();Ie&&!ve[Ie]&&(ve[Ie]=1,fe.push(Ie))})});const ge=await fetch("/api/erp/endpoints/"+encodeURIComponent(m.endpoint_id)+"/products",{headers:{Authorization:"Bearer "+z()}}),we=await ge.json().catch(()=>({}));if(!ge.ok||!we.ok){C.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`;return}O=we.products||[],te(fe)}catch{C.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`}})(),r&&r.addEventListener("click",async()=>{const se=Object.entries(A);if(se.length){r.disabled=!0,r.textContent=t("erp-exc-retrying");try{for(const[ne,ce]of se)if(!(await fetch("/api/erp/mappings/products",{method:"POST",headers:{Authorization:"Bearer "+z(),"Content-Type":"application/json"},body:JSON.stringify({erp_type:m.endpoint_adapter,item_name:ne,erp_code:ce.code,erp_name:ce.name})})).ok){showToast(t("erp-exc-retry-fail"),"error"),r.disabled=!1,r.textContent=t("erp-exc-edit-bind-prod-retry");return}showToast(t("erp-exc-edit-prod-bound-ok"),"success"),T(),await u(m.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),r.disabled=!1,r.textContent=t("erp-exc-edit-bind-prod-retry")}}})}},window._rerenderErpExceptions=P,window.refreshExcBadge=n,window._refreshExcClientFilter=N,window._excState=e,window._rerenderExceptions=function(){try{N()}catch{}e.statsCache&&(x(e.statsCache),o(e.statsCache)),e.listCache&&e.listCache.length&&p(e.listCache);try{M.items&&M.items.length&&P()}catch{}_.openExcId&&R()};let _={openExcId:null,excRow:null,history:null,loading:!1,pdfUrl:null,pdfStatus:"idle",editing:!1,editFields:null};function E(){if(_.pdfUrl){try{URL.revokeObjectURL(_.pdfUrl)}catch{}_.pdfUrl=null}_.pdfStatus="idle"}async function D(d,m){_.pdfStatus="loading",R();try{const q=await fetch("/api/history/"+encodeURIComponent(d)+"/pdf",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(_.openExcId!==m)return;if(q.status===404){_.pdfStatus="empty",R();return}if(!q.ok)throw new Error("http "+q.status);const Z=await q.blob();if(_.openExcId!==m)return;E(),_.pdfUrl=URL.createObjectURL(Z),_.pdfStatus="ready",R()}catch(q){if(_.openExcId!==m)return;console.warn("loadDrawerPdf fail",q),_.pdfStatus="error",R()}}function J(d){const m=(e.listCache||[]).find(q=>q.id===d);if(!m){showToast(t("exc-drawer-error"),"error");return}e.listScrollY=window.scrollY||document.documentElement.scrollTop||0,E(),_.editing=!1,_.editFields=null,_.openExcId=d,_.excRow=m,_.history=null,document.getElementById("exc-drawer-mask").classList.add("show"),document.getElementById("exc-drawer").classList.add("show"),R(),Q(m.history_id),D(m.history_id,d)}function F(){E(),_.editing=!1,_.editFields=null,_.openExcId=null,_.excRow=null,_.history=null,document.getElementById("exc-drawer-mask").classList.remove("show"),document.getElementById("exc-drawer").classList.remove("show");const d=e.listScrollY||0;d>0&&requestAnimationFrame(()=>window.scrollTo(0,d))}async function Q(d){try{const m=await fetch("/api/history/"+encodeURIComponent(d),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!m.ok)throw new Error("http "+m.status);_.history=await m.json()}catch(m){console.warn("loadHistoryDetail fail",m),_.history={_err:!0}}_.excRow&&R()}function ie(d){if(!d||!d.pages)return{};const m=d.pages,q=m.find(Z=>!Z.is_duplicate&&!Z.is_copy)||m[0];return q&&q.fields||{}}function le(d){if(d==null)return"—";const m=typeof d=="number"?d:parseFloat(String(d).replace(/,/g,""));return isNaN(m)?escapeHtml(String(d)):"฿ "+m.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function ue(d,m){if(m=m||{},d==="math_mismatch")return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-subtotal"))}</b><span>${escapeHtml(le(m.subtotal))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-vat"))}</b><span>${escapeHtml(le(m.vat))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(le(m.total_expected))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-actual"))}</b><span class="v-bad">${escapeHtml(le(m.total_actual))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-diff"))}</b><span class="v-bad">${escapeHtml(le(m.diff))}</span></div>
            `;if(d==="tax_id_format_invalid")return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-seller-tax"))}</b><span class="v-bad">${escapeHtml(m.tax_id_normalized||m.tax_id_raw||"—")}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-tax-len"))}</b><span class="v-bad">${escapeHtml(String(m.actual_length||"?"))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(t("exc-detail-tax-expected"))}</span></div>
            `;if(d==="duplicate"){const q=m.level==="exact"?t("exc-detail-dup-level-exact"):t("exc-detail-dup-level-likely");return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-dup-match"))}</b><span>${escapeHtml(m.match_filename||"—")}</span></div>
                ${m.match_invoice_no?`<div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-invoice-no"))}</b><span>${escapeHtml(m.match_invoice_no)}</span></div>`:""}
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span>${escapeHtml(q)}</span></div>
            `}return d==="confidence_low"?`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-conf-label"))}</b><span class="v-bad">${escapeHtml(m.confidence||"—")}</span></div>
            `:d==="amount_missing"?`<div class="exc-why-detail-row" style="justify-content:center;color:var(--danger);"><span>${escapeHtml(t("exc-detail-missing"))}</span></div>`:`<div class="exc-why-detail-row"><span style="font-size:11px;">${escapeHtml(JSON.stringify(m))}</span></div>`}function R(){const d=_.excRow;if(!d)return;const m=d.seller_name&&d.seller_name.trim()?d.seller_name:t("exc-no-seller"),q=d.filename||"—";document.getElementById("exc-drawer-title").textContent=q;const Z="exc-status-"+(d.status||"pending"),i=t(Z)||d.status,v="s-"+(d.status||"pending"),b=(d.invoice_date||d.created_at||"").slice(0,10);document.getElementById("exc-drawer-sub").innerHTML=`
            <span>${escapeHtml(m)}</span>
            ${d.invoice_no?`<span>· ${escapeHtml(d.invoice_no)}</span>`:""}
            ${b?`<span>· ${escapeHtml(b)}</span>`:""}
            <span class="exc-status-chip ${v}">${escapeHtml(i)}</span>
        `;const j=d.severity||"medium",H=t("exc-rule-"+d.rule_code)||d.rule_code,r=ue(d.rule_code,d.detail||{}),C=ie(_.history),A=_.history===null,O=_.history&&_.history._err,K=new Set;d.rule_code==="math_mismatch"?(K.add("subtotal"),K.add("vat"),K.add("total_amount")):d.rule_code==="tax_id_format_invalid"?K.add("seller_tax"):d.rule_code==="amount_missing"&&(K.add("total_amount"),K.add("invoice_number"));const te=!!_.editing,oe=_.editFields||{},se=(be,Se,Ce)=>{if(A)return`<div class="exc-field-row"><label>${escapeHtml(t(Se))}</label><span class="val empty">…</span></div>`;const xe=te?oe[be]!==void 0?oe[be]:C[be]!==void 0&&C[be]!==null?C[be]:"":C[be],je=K.has(be)?"flagged":"";if(te){const Ke=Ce?"number":"text",Xe=Ce?' step="0.01" inputmode="decimal"':"",Ee=xe==null?"":String(xe).replace(/"/g,"&quot;");return`<div class="exc-field-row ${je} editing">
                    <label>${escapeHtml(t(Se))}</label>
                    <input class="exc-field-input" type="${Ke}"${Xe} data-edit-key="${escapeHtml(be)}" value="${Ee}">
                </div>`}const Je=Ce?le(xe):xe||"",We=xe==null||xe===""?`<span class="val empty">${escapeHtml(t("exc-empty-val"))}</span>`:`<span class="val">${escapeHtml(Je)}</span>`;return`<div class="exc-field-row ${je}"><label>${escapeHtml(t(Se))}</label>${We}</div>`};let ne="";O?ne=`<div class="exc-drawer-error">${escapeHtml(t("exc-drawer-error"))}</div>`:ne=`
                <div class="exc-fields">
                    ${se("invoice_number","exc-fld-invoice-no",!1)}
                    ${se("date","exc-fld-date",!1)}
                    ${se("seller_name","exc-fld-seller",!1)}
                    ${se("seller_tax","exc-fld-seller-tax",!1)}
                    ${se("buyer_name","exc-fld-buyer",!1)}
                    ${se("buyer_tax","exc-fld-buyer-tax",!1)}
                    ${se("subtotal","exc-fld-subtotal",!0)}
                    ${se("vat","exc-fld-vat",!0)}
                    ${se("total_amount","exc-fld-total",!0)}
                </div>
            `;const ce=(()=>{if(_.pdfStatus==="loading"||_.pdfStatus==="idle")return`
                    <div class="exc-pdf-toolbar">
                        <span class="exc-pdf-toolbar-title">${escapeHtml(t("exc-pdf-loading"))}</span>
                    </div>
                    <div class="exc-pdf-empty">
                        <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M18 4v8a14 14 0 1014 14"/>
                        </svg>
                        <div class="exc-pdf-empty-msg">${escapeHtml(t("exc-pdf-loading"))}</div>
                    </div>
                `;if(_.pdfStatus==="empty")return`
                    <div class="exc-pdf-toolbar">
                        <span class="exc-pdf-toolbar-title">${escapeHtml(t("exc-pdf-empty-title"))}</span>
                    </div>
                    <div class="exc-pdf-empty">
                        <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M9 4h12l6 6v22H9z"/>
                            <path d="M21 4v6h6"/>
                            <line x1="14" y1="20" x2="22" y2="20"/>
                        </svg>
                        <div class="exc-pdf-empty-msg">${escapeHtml(t("exc-pdf-empty"))}</div>
                    </div>
                `;if(_.pdfStatus==="error")return`
                    <div class="exc-pdf-toolbar">
                        <span class="exc-pdf-toolbar-title">${escapeHtml(t("exc-pdf-error-title"))}</span>
                        <div class="exc-pdf-toolbar-actions">
                            <button class="exc-pdf-icon-btn" id="exc-pdf-retry" title="${escapeHtml(t("exc-pdf-retry"))}" type="button">
                                <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M2 7a5 5 0 019-3l1.5 1.5M12 7a5 5 0 01-9 3L1.5 8.5M12 2v3h-3M2 12V9h3"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                    <div class="exc-pdf-empty">
                        <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5">
                            <circle cx="18" cy="18" r="14"/>
                            <line x1="18" y1="11" x2="18" y2="20"/>
                            <circle cx="18" cy="24" r="0.8" fill="currentColor"/>
                        </svg>
                        <div class="exc-pdf-empty-msg">${escapeHtml(t("exc-pdf-error"))}</div>
                    </div>
                `;const be=_.pdfUrl;return`
                <div class="exc-pdf-toolbar">
                    <span class="exc-pdf-toolbar-title">${escapeHtml(q)}</span>
                    <div class="exc-pdf-toolbar-actions">
                        <a class="exc-pdf-icon-btn" id="exc-pdf-open-tab" href="${be}" target="_blank" rel="noopener" title="${escapeHtml(t("exc-pdf-open-tab"))}">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M8 2h4v4M12 2L7 7"/>
                                <path d="M11 8v3a1 1 0 01-1 1H3a1 1 0 01-1-1V4a1 1 0 011-1h3"/>
                            </svg>
                        </a>
                        <a class="exc-pdf-icon-btn" id="exc-pdf-download" href="${be}" download="${escapeHtml(q)}" title="${escapeHtml(t("exc-pdf-download"))}">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M7 2v8M3.5 6.5L7 10l3.5-3.5M2 12h10"/>
                            </svg>
                        </a>
                    </div>
                </div>
                <iframe class="exc-pdf-frame" src="${be}#toolbar=0&navpanes=0" title="PDF preview"></iframe>
            `})();document.getElementById("exc-drawer-body").innerHTML=`
            <div class="exc-pdf-pane">${ce}</div>
            <div class="exc-fields-pane">
                <div class="exc-section">
                    <div class="exc-section-title">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="7" cy="7" r="5.5"/><line x1="7" y1="4" x2="7" y2="7.5"/>
                            <circle cx="7" cy="9.6" r="0.5" fill="currentColor"/>
                        </svg>
                        <span>${escapeHtml(t("exc-sect-why"))}</span>
                    </div>
                    <div class="exc-why sev-${escapeHtml(j)}">
                        <div class="exc-why-rule">${escapeHtml(H)}</div>
                        <div class="exc-why-detail">${r}</div>
                    </div>
                </div>
                <div class="exc-section">
                    <div class="exc-section-title">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="2" y="2.5" width="10" height="9" rx="1"/>
                            <line x1="4" y1="5.5" x2="10" y2="5.5"/>
                            <line x1="4" y1="8.5" x2="10" y2="8.5"/>
                        </svg>
                        <span>${escapeHtml(t("exc-sect-fields"))}</span>
                        ${d.status==="pending"&&!A&&!O?te?`
                                <span class="exc-section-actions">
                                    <button class="exc-edit-btn ghost" id="exc-fld-cancel" type="button">${escapeHtml(t("exc-fld-cancel"))}</button>
                                    <button class="exc-edit-btn primary" id="exc-fld-save" type="button">${escapeHtml(t("exc-fld-save"))}</button>
                                </span>
                            `:`
                                <span class="exc-section-actions">
                                    <button class="exc-edit-btn ghost" id="exc-fld-edit" type="button">
                                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                            <path d="M2.5 11.5l1-3 6.5-6.5 2 2-6.5 6.5z"/>
                                            <path d="M9 2.5l2 2"/>
                                        </svg>
                                        <span>${escapeHtml(t("exc-fld-edit"))}</span>
                                    </button>
                                </span>
                            `:""}
                    </div>
                    ${ne}
                </div>
            </div>
        `;const fe=document.getElementById("exc-fld-edit");fe&&fe.addEventListener("click",()=>{_.editing=!0,_.editFields={...ie(_.history)},R()});const ve=document.getElementById("exc-fld-cancel");ve&&ve.addEventListener("click",()=>{_.editing=!1,_.editFields=null,R()});const ge=document.getElementById("exc-fld-save");ge&&ge.addEventListener("click",()=>k()),document.querySelectorAll(".exc-field-input").forEach(be=>{be.addEventListener("input",()=>{_.editFields||(_.editFields={}),_.editFields[be.dataset.editKey]=be.value})});const ke=document.getElementById("exc-pdf-retry");ke&&_.openExcId&&ke.addEventListener("click",()=>{_.excRow&&D(_.excRow.history_id,_.openExcId)});const Le=d.status==="pending",Be=!!(d.seller_name&&d.seller_name.trim()),Ie=document.getElementById("exc-btn-resolve"),Ae=document.getElementById("exc-btn-ignore");Ie.disabled=!Le,Ae.disabled=!Le||!Be,Ae.title=Be?t("exc-ignore-hint"):t("exc-ignore-no-seller")}async function k(){if(!_.openExcId||!_.history||!_.history.pages||_.loading)return;_.loading=!0;const d=showToast(t("exc-fld-saving"),"loading",0);try{const m=JSON.parse(JSON.stringify(_.history.pages||[]));let q=m.findIndex(H=>!H.is_duplicate&&!H.is_copy);q<0&&(q=0),m[q]||(m[q]={fields:{}});const Z=m[q].fields||{},i=_.editFields||{},v=new Set(["subtotal","vat","total_amount"]),b={...Z};for(const H in i){let r=i[H];if((r===""||r===void 0)&&(r=null),v.has(H)&&r!==null){const C=parseFloat(r);r=isNaN(C)?null:C}b[H]=r}m[q].fields=b;const j=await fetch("/api/history/"+encodeURIComponent(_.history.id),{method:"PUT",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({pages:m})});if(!j.ok)throw new Error("http "+j.status);d(),showToast(t("exc-fld-save-ok"),"success"),F(),await B(),await I(),n()}catch(m){d(),console.warn("save fields fail",m),showToast(t("exc-fld-save-fail"),"error")}finally{_.loading=!1}}async function Y(){if(!(!_.openExcId||_.loading)){_.loading=!0;try{const d=await fetch("/api/exceptions/"+_.openExcId+"/resolve",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!d.ok)throw new Error("http "+d.status);showToast(t("exc-toast-resolved"),"success"),F(),await B(),await I(),n()}catch(d){console.warn("resolve fail",d),showToast(t("exc-toast-action-fail"),"error")}finally{_.loading=!1}}}async function X(){if(!(!_.openExcId||_.loading)){_.loading=!0;try{const d=await fetch("/api/exceptions/"+_.openExcId+"/ignore",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!d.ok)throw new Error("http "+d.status);showToast(t("exc-toast-ignored"),"success"),F(),await B(),await I(),n()}catch(d){console.warn("ignore fail",d),showToast(t("exc-toast-action-fail"),"error")}finally{_.loading=!1}}}let ee=!1;async function re(){if(ee)return;const d=Array.from(e.selectedIds);if(d.length===0||!await showConfirm(a("exc-batch-confirm-resolve",{n:d.length})))return;ee=!0;const q=showToast(a("exc-batch-count",{n:d.length})+" …","loading",0);try{const Z=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:d,action:"resolve"})});if(!Z.ok)throw new Error("http "+Z.status);const i=await Z.json();q(),showToast(a("exc-toast-batch-resolved",{n:i.processed||0}),"success"),e.selectedIds.clear(),await B(),await I(),n()}catch(Z){q(),console.warn("batch resolve fail",Z),showToast(t("exc-toast-batch-fail"),"error")}finally{ee=!1}}async function de(){if(ee)return;const d=Array.from(e.selectedIds);if(d.length===0||!await showConfirm(a("exc-batch-confirm-ignore",{n:d.length}),{danger:!1}))return;ee=!0;const q=showToast(a("exc-batch-count",{n:d.length})+" …","loading",0);try{const Z=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:d,action:"ignore"})});if(!Z.ok)throw new Error("http "+Z.status);const i=await Z.json();q(),showToast(a("exc-toast-batch-ignored",{n:i.processed||0,wl:i.whitelist_added||0}),"success"),e.selectedIds.clear(),await B(),await I(),n()}catch(Z){q(),console.warn("batch ignore fail",Z),showToast(t("exc-toast-batch-fail"),"error")}finally{ee=!1}}function pe(){e.selectedIds.clear(),p(e.listCache)}document.addEventListener("click",d=>{d.target.closest("#exc-drawer-close")&&F(),d.target.closest("#exc-drawer-mask")&&F(),d.target.closest("#exc-btn-resolve")&&Y(),d.target.closest("#exc-btn-ignore")&&X(),d.target.closest("#exc-batch-resolve")&&re(),d.target.closest("#exc-batch-ignore")&&de(),d.target.closest("#exc-batch-clear")&&pe(),d.target.closest("#exc-loadmore")&&U()}),document.addEventListener("keydown",d=>{d.key==="Escape"&&_.openExcId&&F()}),document.addEventListener("click",d=>{d.target.closest("#btn-exc-refresh")&&(typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),n())}),document.addEventListener("change",d=>{if(!d.target.closest("#exc-client-filter"))return;const m=d.target;e.currentClient=m.value||"",e.currentRule=null,e.selectedIds.clear(),e.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),n()}),document.addEventListener("click",d=>{const m=d.target.closest("#exc-status-tabs .exc-status-tab");if(!m)return;const q=m.dataset.status||"pending";q!==e.currentStatus&&(e.currentStatus=q,e.currentRule=null,e.selectedIds.clear(),e.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage())}),window.addEventListener("online",()=>{e.loadFailed&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage&&window.loadExceptionsPage()}),setTimeout(n,1500),setInterval(n,6e4);function G(d){if(!d)return"—";try{const m=new Date(d),q=Z=>String(Z).padStart(2,"0");return`${m.getFullYear()}-${q(m.getMonth()+1)}-${q(m.getDate())} ${q(m.getHours())}:${q(m.getMinutes())}`}catch{return d.slice(0,16).replace("T"," ")}}async function ae(){const d=document.getElementById("learned-list");if(d){d.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-loading"))}</div>`;try{const m=await fetch("/api/exception-whitelist",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!m.ok)throw new Error("http "+m.status);const Z=(await m.json()).items||[];if(Z.length===0){d.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-empty"))}</div>`;return}const i=`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 4h8M5.5 4V2.5h3V4M4 4l0.6 8.5h4.8L10 4"/>
            </svg>`;d.innerHTML=Z.map(v=>{const b=t("exc-rule-"+v.rule_code)||v.rule_code;return`
                    <div class="learned-row" data-wl-id="${escapeHtml(String(v.id))}">
                        <div class="learned-seller" title="${escapeHtml(v.seller_name)}">${escapeHtml(v.seller_name)}</div>
                        <div class="learned-rule">${escapeHtml(b)}</div>
                        <div class="learned-date">${escapeHtml(G(v.created_at))}</div>
                        <button class="learned-del-btn" data-del-wl="${escapeHtml(String(v.id))}" title="${escapeHtml(t("set-learned-del"))}" type="button">${i}</button>
                    </div>
                `}).join("")}catch(m){console.warn("loadLearnedRules fail",m),d.innerHTML=`<div class="learned-empty">${escapeHtml(t("exc-toast-load-fail"))}</div>`}}}window.loadLearnedRules=ae,document.addEventListener("click",async d=>{const m=d.target.closest("[data-del-wl]");if(!m)return;const q=parseInt(m.dataset.delWl,10);if(!q)return;const Z=m.closest(".learned-row"),i=Z&&Z.querySelector(".learned-seller"),v=i?i.textContent.trim():"",b=t("set-learned-del-confirm").replace("{seller}",v);if(await showConfirm(b,{danger:!0}))try{const H=await fetch("/api/exception-whitelist/"+q,{method:"DELETE",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!H.ok)throw new Error("http "+H.status);showToast(t("set-learned-del-ok"),"success"),ae(),typeof window.loadExceptionsPage=="function"&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage()}catch(H){console.warn("delete whitelist fail",H),showToast(t("set-learned-del-fail"),"error")}})})();(function(){function e(g){try{if(location.search.indexOf("test_center=1")>=0||localStorage.getItem("pearnly_test_mode")==="1"||g&&g.id&&String(g.id)==="468b50c1-5593-4fd6-990d-515ce8085563")return!0}catch{}return!1}window.applyRoleVisibility=function(){var B=window._userInfo,S=!1,I=!0,U=!1,N=!1;B&&(S=typeof canManageTeam=="function"?canManageTeam(B):!!(B.role==="owner"||B.is_super_admin),I=typeof shouldHideMoney=="function"?shouldHideMoney(B):B.role==="member"&&!B.is_super_admin,U=typeof isSuperAdmin=="function"?isSuperAdmin(B):!!B.is_super_admin,N=e(B)),document.querySelectorAll("[data-show-if-team]").forEach(function(L){L.style.display=S?"":"none"}),document.querySelectorAll("[data-show-if-money]").forEach(function(L){L.style.display=I?"none":""}),document.querySelectorAll("[data-show-if-admin]").forEach(function(L){L.style.display=U?"":"none"}),document.querySelectorAll("[data-show-if-test]").forEach(function(L){L.style.display=N?"":"none"});var M=U||N;document.querySelectorAll("[data-show-if-special]").forEach(function(L){L.style.display=M?"":"none"})},window.renderAvatarMenu=function(B){if(B){var S=document.getElementById("avatar-btn"),I=document.getElementById("avatar-popup-name"),U=document.getElementById("avatar-popup-email");if(!(!S||!I||!U)){var N=(B.username||"").trim(),M=N.split("@")[0]||N||"—",L=(N.charAt(0)||"?").toUpperCase(),z=(B.avatar_url||"").trim();if(z){var V=z.replace(/"/g,"&quot;"),W=L.replace(/'/g,"\\'");S.innerHTML='<img src="'+V+'" alt="'+L+`" referrerpolicy="no-referrer" onerror="this.parentNode.textContent='`+W+`'">`}else S.textContent=L;I.textContent=M,U.textContent=N||"—",S.setAttribute("title",N||"")}}};function a(){var g=document.getElementById("avatar-wrap"),B=document.getElementById("avatar-btn"),S=document.getElementById("avatar-popup");if(!g||!B||!S)return;function I(){S.classList.remove("show"),B.setAttribute("aria-expanded","false")}function U(){S.classList.add("show"),B.setAttribute("aria-expanded","true")}B.addEventListener("click",function(N){N.stopPropagation(),S.classList.contains("show")?I():U()}),document.addEventListener("click",function(N){S.classList.contains("show")&&!g.contains(N.target)&&I()}),S.addEventListener("click",function(N){var M=N.target.closest(".avatar-popup-item");if(M){var L=M.dataset.action;switch(I(),L){case"settings":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings");break;case"team":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("team")},50);break;case"billing":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("plan")},50);break;case"shortcuts":if(typeof showToast=="function"){var z=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(z||"即将上线","info")}break;case"admin":window.location.href="/admin/cost";break;case"test-center":typeof routeTo=="function"&&routeTo("test-center");break;case"help":var V=document.getElementById("help-modal");V&&(V.style.display="flex");break;case"logout":try{localStorage.removeItem("mrpilot_token")}catch{}try{localStorage.removeItem("mrpilot_user")}catch{}window.location.href="/";break}}}),window._closeAvatarPopup=I}function n(){return[].slice.call(document.querySelectorAll(".cmdk-item")).filter(function(g){return g.style.display!=="none"})}function s(g){var B=n();B.forEach(function(S){S.classList.remove("focus")}),B[g]&&(B[g].classList.add("focus"),B[g].scrollIntoView({block:"nearest"}))}function l(g){var B=n();if(B.length){var S=B.findIndex(function(U){return U.classList.contains("focus")});S<0&&(S=0);var I=(S+g+B.length)%B.length;s(I)}}function f(g){g=(g||"").toLowerCase().trim();var B=0,S=window._userInfo,I=typeof isSuperAdmin=="function"?isSuperAdmin(S):!!(S&&S.is_super_admin),U=e(S);document.querySelectorAll(".cmdk-item").forEach(function(M){if(M.dataset.showIfAdmin==="1"&&!I){M.style.display="none";return}if(M.dataset.showIfTest==="1"&&!U){M.style.display="none";return}var L=(M.dataset.cmdkText||M.textContent||"").toLowerCase(),z=!g||L.indexOf(g)>=0;M.style.display=z?"":"none",M.classList.remove("focus"),z&&B++}),document.querySelectorAll("[data-cmdk-section]").forEach(function(M){for(var L=M.nextElementSibling,z=!1;L&&!L.hasAttribute("data-cmdk-section");){if(L.classList&&L.classList.contains("cmdk-item")&&L.style.display!=="none"){z=!0;break}L=L.nextElementSibling}M.style.display=z?"":"none"});var N=document.getElementById("cmdk-empty");N&&(N.style.display=B===0?"flex":"none"),s(0)}window.openCmdk=function(){var B=document.getElementById("cmdk-mask");B&&(typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup(),B.classList.add("show"),typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility(),setTimeout(function(){var S=document.getElementById("cmdk-input");S&&(S.value="",f(""),S.focus(),s(0))},50))},window.closeCmdk=function(){var B=document.getElementById("cmdk-mask");B&&B.classList.remove("show")};function h(g){if(g){if(g.classList.contains("cmdk-item-locked")){if(typeof showToast=="function"){var B=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(B||"即将上线","info")}return}var S=g.dataset.cmdkRoute,I=g.dataset.cmdkAction;if(window.closeCmdk(),S){typeof routeTo=="function"&&routeTo(S);return}if(I){if(I==="open-admin"){window.location.href="/admin/cost";return}if(I.indexOf("lang-")===0){var U=I.slice(5);typeof applyLang=="function"&&applyLang(U)}}}}function x(){var g=document.getElementById("cmdk-mask"),B=document.getElementById("cmdk-input"),S=document.getElementById("cmdk-body");if(!(!g||!B||!S)){g.addEventListener("click",function(N){N.target===g&&window.closeCmdk()});var I=document.getElementById("cmdk-esc-btn");I&&I.addEventListener("click",function(){window.closeCmdk()}),B.addEventListener("input",function(N){f(N.target.value)}),B.addEventListener("keydown",function(N){N.key==="ArrowDown"?(N.preventDefault(),l(1)):N.key==="ArrowUp"?(N.preventDefault(),l(-1)):N.key==="Enter"?(N.preventDefault(),h(g.querySelector(".cmdk-item.focus"))):N.key==="Escape"&&(N.preventDefault(),window.closeCmdk())}),S.addEventListener("click",function(N){var M=N.target.closest(".cmdk-item");M&&h(M)}),S.addEventListener("mousemove",function(N){var M=N.target.closest(".cmdk-item");!M||M.style.display==="none"||M.classList.contains("cmdk-item-locked")||(n().forEach(function(L){L.classList.remove("focus")}),M.classList.add("focus"))});var U=document.getElementById("topbar-search");U&&(U.addEventListener("click",function(){window.openCmdk()}),U.addEventListener("keydown",function(N){(N.key==="Enter"||N.key===" ")&&(N.preventDefault(),window.openCmdk())}))}}document.addEventListener("keydown",function(g){if((g.metaKey||g.ctrlKey)&&(g.key==="k"||g.key==="K")){g.preventDefault(),window.openCmdk();return}if(g.key==="Escape"){var B=document.getElementById("cmdk-mask");if(B&&B.classList.contains("show")){window.closeCmdk();return}var S=document.getElementById("avatar-popup");S&&S.classList.contains("show")&&typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup()}});try{var o=(navigator.userAgent||"").toLowerCase(),p=o.indexOf("mac")>=0||o.indexOf("iphone")>=0||o.indexOf("ipad")>=0;p||document.body.classList.add("is-windows")}catch{}function w(){a(),x(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("nav-ia-phase1-role",function(){try{typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",w):w()})();(function(){function a(I){return String(I??"").replace(/[&<>"']/g,function(U){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[U]})}function n(I){if(!I||isNaN(I))return"";var U=Number(I);return U<1024?U+" B":U<1024*1024?(U/1024).toFixed(1)+" KB":(U/1024/1024).toFixed(1)+" MB"}document.addEventListener("click",function(I){var U=I.target.closest&&I.target.closest(".recon-collapse-head");if(U&&!(I.target.closest("button")||I.target.closest("a"))){var N=U.closest(".recon-collapse");if(N){var M=N.getAttribute("data-collapsed")==="true";N.setAttribute("data-collapsed",M?"false":"true"),M&&(N.id==="vex-summary-collapse"&&w(),N.id==="vex-detail-collapse"&&g())}}}),document.addEventListener("keydown",function(I){if(!(I.key!=="Enter"&&I.key!==" ")){var U=I.target.closest&&I.target.closest(".recon-collapse-head");U&&(I.preventDefault(),U.click())}});var s={vat:"",gl:""};window._glvClearPreviewSearch=function(){s.vat="",s.gl=""};var l='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',f='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function h(){o("vat"),o("gl")}function x(I){try{if(typeof window._glvPreviewFiles=="function")return window._glvPreviewFiles(I)||[]}catch{}var U=document.getElementById(I==="vat"?"glv-vat-input":"glv-gl-input");return U&&U.files?Array.from(U.files):[]}function o(I){var U=document.getElementById(I==="vat"?"glv-pp-vat-col":"glv-pp-gl-col");if(U){var N=x(I),M=I==="vat"?"glv-up-vat-title":"glv-up-gl-title",L=I==="vat"?"① 销项税报告":"② 总账 GL",z=window.t&&window.t(M)||L,V=a(window.t&&window.t("vex-preview-search")||"搜索文件名..."),W=a(window.t&&window.t("vex-preview-clear-all")||"全清"),P=s[I]||"",u=N.length;U.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+a(z)+' <span class="vex-pp-col-count">'+u+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="glv-pp-search-'+I+'" type="text" placeholder="'+V+'" value="'+a(P)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="glv-pp-clearall-'+I+'" type="button">'+W+'</button></div><div class="vex-pp-file-list" id="glv-pp-'+I+'-list"></div><div class="vex-pp-pagination" id="glv-pp-'+I+'-pg"></div>';var c=document.getElementById("glv-pp-search-"+I);c&&c.addEventListener("input",function($){s[I]=$.target.value,p(I)});var y=document.getElementById("glv-pp-clearall-"+I);y&&y.addEventListener("click",function(){window._glvRemoveFile&&window._glvRemoveFile(I)}),p(I)}}function p(I){var U=document.getElementById("glv-pp-"+I+"-list"),N=document.getElementById("glv-pp-"+I+"-pg");if(U){var M=x(I),L=(s[I]||"").toLowerCase(),z=M.map(function(P,u){return{f:P,i:u}}),V=L?z.filter(function(P){return P.f.name.toLowerCase().indexOf(L)>=0}):z;if(U.innerHTML=V.map(function(P){var u=P.f;return'<div class="vex-pp-file-row">'+l+'<span class="vex-pp-fi-name" title="'+a(u.name)+'">'+a(u.name)+'</span><span class="vex-pp-fi-size">'+n(u.size)+'</span><button class="vex-pp-fi-del" type="button" data-kind="'+I+'" data-idx="'+P.i+'" aria-label="remove">'+f+"</button></div>"}).join(""),U.querySelectorAll(".vex-pp-fi-del").forEach(function(P){P.addEventListener("click",function(){var u=P.dataset.kind,c=parseInt(P.dataset.idx,10);window._glvRemoveFile&&window._glvRemoveFile(u,isNaN(c)?null:c)})}),N){var W=window.t&&window.t("vex-preview-count")||"显示前 {n} / 共 {m}";N.textContent=W.replace("{n}",V.length).replace("{m}",V.length)}}}function w(){var I=function(N,M){var L=document.getElementById(N);L&&(L.textContent=M==null?"—":String(M))},U=window._vexLastTask||{};I("vex-sum-total",U.total),I("vex-sum-matched",U.matched),I("vex-sum-diff",U.diff),I("vex-sum-incomplete",U.incomplete),I("vex-sum-cash",U.cash),document.getElementById("vex-summary-sub")}function g(){var I=window._vexLastTask&&window._vexLastTask.diff_rows||[],U=document.getElementById("vex-detail-tbody"),N=document.getElementById("vex-detail-table"),M=document.getElementById("vex-detail-empty");if(!(!U||!N||!M)){if(I.length===0){N.style.display="none",M.style.display="";return}M.style.display="none",N.style.display="";var L=I.map(function(V){return'<tr><td class="recon-detail-cell-mono">'+a(V.invoice_no||"")+"</td><td>"+a(V.field||"")+"</td><td>"+a(V.report_value||"")+"</td><td>"+a(V.invoice_value||"")+"</td><td>"+a(V.kind||"")+"</td></tr>"}).join("");U.innerHTML=L;var z=document.getElementById("vex-detail-sub");z&&(z.textContent=String(I.length))}}function B(){var I=document.getElementById("glv-toggle-preview");I&&!I._reconBound&&(I._reconBound=!0,I.addEventListener("click",function(){var U=document.getElementById("glv-preview-panel"),N=document.getElementById("glv-toggle-preview-label"),M=U&&U.style.display!=="none";U&&(U.style.display=M?"none":""),I.classList.toggle("open",!M),N&&(N.textContent=M?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),M||h()})),["glv-vat-input","glv-gl-input"].forEach(function(U){var N=document.getElementById(U);!N||N._reconWatched||(N._reconWatched=!0,N.addEventListener("change",function(){var M=document.getElementById("glv-preview-panel");M&&M.style.display!=="none"&&h()}))})}function S(){var I=document.getElementById("vex-summary-collapse"),U=document.getElementById("vex-detail-collapse");I&&(I.style.display=""),U&&(U.style.display=""),w(),g()}window._fillVexSummary=w,window._fillVexDetail=g,window._onVexResultShown=S,document.addEventListener("DOMContentLoaded",function(){B()}),setTimeout(B,1500),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-collapse",function(){var I=document.getElementById("glv-preview-panel");I&&I.style.display!=="none"&&h();var U=document.getElementById("glv-toggle-preview-label"),N=document.getElementById("glv-toggle-preview");U&&N&&(U.textContent=N.classList.contains("open")?window.t&&window.t("vex-toggle-preview-close")||"收起清单":window.t&&window.t("vex-toggle-preview-open")||"查看清单")}),window._reconCollapse={renderGlvPreview:h,fillVexSummary:w,fillVexDetail:g}})();(function(){function e(f){}function a(){const f=document.querySelectorAll("[data-recon-tab]");f.forEach(x=>{x.addEventListener("click",()=>{f.forEach(B=>B.classList.remove("active")),x.classList.add("active");const o=x.dataset.reconTab,p=document.getElementById("recon-pane-bank"),w=document.getElementById("recon-pane-sale-vat"),g=document.getElementById("recon-pane-gl-vat");p&&(p.style.display=o==="bank"?"":"none"),w&&(w.style.display=o==="sale-vat"?"":"none"),g&&(g.style.display=o==="gl-vat"?"":"none"),o==="gl-vat"&&window.GlVatRecon&&window.GlVatRecon.ensureInit(),o==="bank"&&typeof window._bankReconV2Init=="function"&&window._bankReconV2Init()})});const h=document.querySelector("[data-recon-tab].active");h&&(h.dataset.reconTab,void 0)}function n(){const f=document.getElementById("page-settings");if(!f)return null;let h=document.getElementById("settings-modal-overlay");if(h)return h;h=document.createElement("div"),h.id="settings-modal-overlay",h.className="settings-modal-overlay",h.style.display="none",f.parentElement.insertBefore(h,f),h.appendChild(f);const x=document.createElement("button");return x.id="settings-modal-close",x.className="settings-modal-close",x.setAttribute("aria-label","close"),x.innerHTML='<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 5l10 10M15 5L5 15"/></svg>',f.insertBefore(x,f.firstChild),x.addEventListener("click",l),h.addEventListener("click",o=>{o.target===h&&l()}),h}function s(){const f=n();if(!f)return;f.style.display="flex",document.body.classList.add("settings-modal-open");const h=document.getElementById("page-settings");h&&(h.style.display="block"),setTimeout(()=>{try{typeof renderSettings=="function"&&renderSettings()}catch(o){console.warn("renderSettings:",o)}let x=document.querySelector(".settings-tab.active")||document.querySelector('.settings-tab[data-tab="profile"]');x&&x.click()},50)}function l(){const f=document.getElementById("settings-modal-overlay");f&&(f.style.display="none"),document.body.classList.remove("settings-modal-open")}window.openSettingsModal=s,window.closeSettingsModal=l,document.addEventListener("keydown",f=>{if(f.key==="Escape"){const h=document.getElementById("settings-modal-overlay");h&&h.style.display==="flex"&&l()}}),window.addEventListener("hashchange",()=>{location.hash==="#/settings"&&s()}),window.addEventListener("DOMContentLoaded",()=>{location.hash==="#/settings"&&s()}),document.readyState==="loading"?document.addEventListener("DOMContentLoaded",a):a()})();(function(){const n=/\.(pdf|jpe?g|png|webp|tiff?|xlsx?|xlsm|csv|tsv|docx?)$/i,s=G=>document.getElementById(G);function l(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}function f(G){return String(G??"").replace(/[&<>"']/g,ae=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[ae])}function h(G){return G<1024?G+" B":G<1024*1024?(G/1024).toFixed(1)+" KB":(G/1024/1024).toFixed(1)+" MB"}let x=[],o=[],p=!1,w=[],g=50,B=50,S="",I="";async function U(){try{const G=await fetch("/api/vat_excel/tasks?page=1&page_size=1",{headers:l()});if(!G.ok)return;const d=(await G.json()).kpi||{};[["vex-kpi-month-val",d.this_month],["vex-kpi-running-val",d.running],["vex-kpi-done-val",d.done],["vex-kpi-failed-val",d.failed]].forEach(([m,q])=>{const Z=document.getElementById(m);Z&&(Z.textContent=q??0)})}catch{}}async function N(){try{const G=await fetch("/api/vat_excel/tasks?page=1&page_size=100",{headers:l()});if(!G.ok)return;const ae=await G.json();V(ae.rows||[])}catch{}}const M=10;var L=1;function z(){var G=((document.getElementById("vex-task-search")||{}).value||"").trim().toLowerCase();if(L=1,V(w),!!G){var ae=document.getElementById("vex-task-tbody");ae&&ae.querySelectorAll("tr").forEach(function(d){d.dataset.taskId&&(d.style.display=d.textContent.toLowerCase().indexOf(G)>=0?"":"none")})}}function V(G){w=G||w;const ae=document.getElementById("vex-task-tbody");if(!ae)return;if(!w.length){ae.innerHTML='<tr><td colspan="9" class="vex-task-empty">'+(t("sv-empty-title")||"还没有对账任务")+"</td></tr>",W(0);return}const d=Math.ceil(w.length/M);L>d&&(L=d);const m=(L-1)*M;P(w.slice(m,m+M)),W(w.length)}function W(G){const ae=document.getElementById("vex-task-pager"),d=document.getElementById("vex-task-pager-info"),m=document.getElementById("vex-task-prev"),q=document.getElementById("vex-task-next");if(!ae)return;if(G<=M){ae.style.display="none";return}ae.style.display="";const Z=Math.ceil(G/M);d&&(d.textContent=L+" / "+Z),m&&(m.disabled=L<=1),q&&(q.disabled=L>=Z)}function P(G){const ae=document.getElementById("vex-task-tbody");if(!ae)return;const d={pending:t("vex-status-pending")||"待处理",running:t("vex-status-running")||"处理中",done:t("vex-status-done")||"已完成",failed:t("vex-status-failed")||"失败"},m={pending:"badge-gray",running:"badge-blue",done:"badge-green",failed:"badge-red"},q='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',Z='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h10M6 4V3h4v1M5 4v8a1 1 0 001 1h4a1 1 0 001-1V4"/></svg>';ae.innerHTML=G.map(i=>{const v=i.created_at?new Date(i.created_at).toLocaleString([],{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}):"—",b=i.period||"—",j=i.matched_count!=null?i.matched_count+" ✓ · "+i.mismatched_count+" ⚠":"—",H=i.mismatch_amount!=null?"฿ "+Number(i.mismatch_amount).toLocaleString():"—",r=i.elapsed_seconds!=null?i.elapsed_seconds.toFixed(1)+" s":"—",C=i.status||"pending",A=i.client_name&&i.client_name!=="client"?i.client_name:t("vex-client-all")||"全部客户";return`<tr class="vex-task-row" data-task-id="${f(i.id)}" style="cursor:pointer">
                <td>${v}</td>
                <td>${f(A)}</td>
                <td>${f(b)}</td>
                <td>${(i.invoice_count||0)+" / "+(i.report_count||0)}</td>
                <td>${j}</td>
                <td>${H}</td>
                <td><span class="badge ${m[C]||"badge-gray"}">${d[C]||C}</span></td>
                <td>${r}</td>
                <td><div class="vex-task-actions">
                    <button class="vex-task-dl-btn" data-task-id="${f(i.id)}" title="${t("hist_export")||"导出"}">${q}</button>
                    <button class="vex-task-del-btn" data-task-id="${f(i.id)}" title="${t("vex-task-delete-confirm-title")||"删除"}">${Z}</button>
                </div></td>
            </tr>`}).join(""),ae.querySelectorAll(".vex-task-dl-btn").forEach(i=>{i.addEventListener("click",async v=>{v.stopPropagation();const b=i.dataset.taskId;try{const j=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(b)+"/download",{credentials:"include",headers:l()});if(j.status===410){showToast(t("vex-toast-expired")||"数据已过期 · 请重新对账","warn");return}if(!j.ok){showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error");return}const H=await j.blob(),C=(j.headers.get("Content-Disposition")||"").match(/filename\*?=(?:UTF-8''|")?([^";]+)/i),A=C?decodeURIComponent(C[1]):"vat_recon_"+b+".xlsx",O=URL.createObjectURL(H),K=document.createElement("a");K.href=O,K.download=A,K.click(),setTimeout(()=>URL.revokeObjectURL(O),1e3)}catch{showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error")}})}),ae.querySelectorAll(".vex-task-del-btn").forEach(i=>{i.addEventListener("click",v=>{v.stopPropagation(),c(i.dataset.taskId)})}),z()}function u(){var G=document.getElementById("vex-task-prev"),ae=document.getElementById("vex-task-next");G&&!G._vexBound&&(G._vexBound=!0,G.addEventListener("click",function(){L>1&&(L--,V())})),ae&&!ae._vexBound&&(ae._vexBound=!0,ae.addEventListener("click",function(){var d=Math.ceil(w.length/M);L<d&&(L++,V())}))}async function c(G){const ae=t("vex-task-delete-confirm-title")||"删除对账任务?",d=t("vex-task-delete-confirm-body")||"同时清掉对应的发票识别缓存 · 不可恢复";if(await showConfirm(d,{title:ae,danger:!0,okText:t("vex-task-delete-confirm-title")||"确认删除"}))try{const q=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(G),{method:"DELETE",credentials:"include",headers:l()});if(!q.ok)throw new Error(q.status);showToast(t("vex-task-delete-ok")||"已删除","success"),N(),U()}catch{showToast(t("vex-task-delete-fail")||"删除失败","error")}}function y(G){const ae=window._currentLang||"th",d={zh:`已忽略 ${G} 个不支持的文件 · 仅支持 PDF / 图片 / Excel / CSV / Word`,th:`ข้ามไฟล์ที่ไม่รองรับ ${G} ไฟล์ · รองรับเฉพาะ PDF / รูปภาพ / Excel / CSV / Word`,en:`Ignored ${G} unsupported file(s) · only PDF / image / Excel / CSV / Word are supported`,ja:`非対応ファイル ${G} 件をスキップ · 対応形式は PDF / 画像 / Excel / CSV / Word のみ`};showToast(d[ae]||d.th,"warn")}function $(G){const ae=new Set(x.map(m=>m.name+"|"+m.size));let d=0;for(const m of G){if(!n.test(m.name)){d++;continue}const q=m.name+"|"+m.size;if(!ae.has(q)&&(ae.add(q),x.push(m),x.length>=1e3))break}d>0&&y(d),x.length>1e3&&(x=x.slice(0,1e3),showToast(t("vex-toast-cap-inv"),"warn")),D()}function T(G){const ae=new Set(o.map(m=>m.name+"|"+m.size));let d=0;for(const m of G){if(!n.test(m.name)){d++;continue}const q=m.name+"|"+m.size;if(!ae.has(q)&&(ae.add(q),o.push(m),o.length>=30))break}d>0&&y(d),o.length>30&&(o=o.slice(0,30),showToast(t("vex-toast-cap-rep"),"warn")),D()}function _(G){x.splice(G,1),D()}function E(G){o.splice(G,1),D()}function D(){const G=s("vex-list-invoice"),ae=s("vex-list-report"),d=s("vex-count-invoice"),m=s("vex-count-report");d&&(d.textContent=x.length),m&&(m.textContent=o.length);const q=(v,b,j)=>`<div class="vex-fi">
            <svg class="vex-fi-ic" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2h6l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M10 2v4h4"/></svg>
            <span class="vex-fi-n" title="${f(v.name)}">${f(v.name)}</span>
            <span class="vex-fi-s">${h(v.size)}</span>
            <button class="vex-fi-x" type="button" data-vex-kind="${j}" data-vex-idx="${b}" aria-label="remove">×</button>
        </div>`;G&&(G.innerHTML=x.map((v,b)=>q(v,b,"inv")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),ae&&(ae.innerHTML=o.map((v,b)=>q(v,b,"rep")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),document.querySelectorAll(".vex-fi-x").forEach(v=>{v.addEventListener("click",b=>{const j=v.dataset.vexKind,H=parseInt(v.dataset.vexIdx,10);j==="inv"?_(H):E(H)})});const Z=x.length>0&&o.length>0;s("vex-build").disabled=!Z||p;const i=s("vex-action-info");i&&(!x.length||!o.length?(i.textContent=t("vex-need-both")||"需要至少 1 张发票 + 1 份 VAT 报告",i.className="vex-action-info muted"):(i.textContent=(t("vex-ready")||"已就绪 · {a} 张发票 · {b} 份报告").replace("{a}",x.length).replace("{b}",o.length),i.className="vex-action-info ok")),ie()}const J='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>',F='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',Q='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function ie(){const G=s("vex-preview-panel");if(!G||G.style.display==="none")return;le("inv"),le("rep");const ae=s("vex-pp-guide");ae&&(ae.style.display=x.length>100?"flex":"none")}function le(G){const ae=s(G==="inv"?"vex-pp-invoice-col":"vex-pp-report-col");if(!ae)return;const d=G==="inv"?x:o,m=G==="inv"?S:I,q=t(G==="inv"?"vex-preview-invoice":"vex-preview-report")||(G==="inv"?"销售发票":"VAT 报告"),Z=f(t("vex-preview-search")||"搜索文件名..."),i=f(t("vex-preview-clear-all")||"全清");ae.innerHTML=`
            <div class="vex-pp-col-title">
                <span class="vex-pp-col-name">${f(q)} <span class="vex-pp-col-count">${d.length}</span></span>
            </div>
            <div class="vex-pp-search-row">
                <input class="vex-pp-search" id="vex-pp-search-${G}" type="text"
                       placeholder="${Z}" value="${f(m)}" autocomplete="off">
                <button class="vex-pp-clear-btn" id="vex-pp-clearall-${G}" type="button">${i}</button>
            </div>
            <div class="vex-pp-file-list" id="vex-pp-${G}-list"></div>
            <div class="vex-pp-pagination" id="vex-pp-${G}-pg"></div>`;const v=s("vex-pp-search-"+G);v&&v.addEventListener("input",j=>{G==="inv"?(S=j.target.value,g=50):(I=j.target.value,B=50),ue(G)});const b=s("vex-pp-clearall-"+G);b&&b.addEventListener("click",()=>{G==="inv"?(x=[],S="",g=50):(o=[],I="",B=50),D()}),ue(G)}function ue(G){const ae=s("vex-pp-"+G+"-list"),d=s("vex-pp-"+G+"-pg");if(!ae)return;const m=G==="inv"?x:o,q=G==="inv"?S:I,Z=G==="inv"?g:B,i=G==="inv"?J:F,v=m.map((H,r)=>({f:H,i:r})),b=q?v.filter(({f:H})=>H.name.toLowerCase().includes(q.toLowerCase())):v,j=b.slice(0,Z);if(ae.innerHTML=j.map(({f:H,i:r})=>`
            <div class="vex-pp-file-row">
                ${i}
                <span class="vex-pp-fi-name" title="${f(H.name)}">${f(H.name)}</span>
                <span class="vex-pp-fi-size">${h(H.size)}</span>
                <button class="vex-pp-fi-del" type="button" data-kind="${G}" data-ridx="${r}" aria-label="remove">${Q}</button>
            </div>`).join("")+`<div id="vex-pp-sentinel-${G}" style="height:1px;flex-shrink:0"></div>`,ae.querySelectorAll(".vex-pp-fi-del").forEach(H=>{H.addEventListener("click",()=>{const r=parseInt(H.dataset.ridx,10);H.dataset.kind==="inv"?_(r):E(r)})}),d){const H=t("vex-preview-count")||"显示前 {n} / 共 {m}";d.textContent=H.replace("{n}",j.length).replace("{m}",b.length)}R(G,b.length)}function R(G,ae){if((G==="inv"?g:B)>=ae)return;const m=s("vex-pp-sentinel-"+G),q=s("vex-pp-"+G+"-list");if(!m||!q)return;const Z=new IntersectionObserver(i=>{i[0].isIntersecting&&(Z.disconnect(),G==="inv"?g+=50:B+=50,ue(G))},{root:q,threshold:.8});Z.observe(m)}function k(G,ae,d,m){const q=s(G),Z=s(ae);!q||!Z||(q.addEventListener("click",()=>Z.click()),q.addEventListener("keydown",i=>{(i.key==="Enter"||i.key===" ")&&(i.preventDefault(),Z.click())}),q.addEventListener("dragover",i=>{i.preventDefault(),q.classList.add("drag-over")}),q.addEventListener("dragleave",()=>q.classList.remove("drag-over")),q.addEventListener("drop",i=>{i.preventDefault(),q.classList.remove("drag-over");const b=Array.from(i.dataTransfer.files).filter(j=>n.test(j.name));if(!b.length){showToast(t("vex-toast-bad-ext"),"error");return}d(b)}),Z.addEventListener("change",()=>{const i=Array.from(Z.files);d(i),Z.value=""}))}async function Y(){if(p||!x.length||!o.length)return;p=!0,s("vex-build").disabled=!0,s("vex-progress").style.display="flex";var G=document.getElementById("vex-download");G&&(G.style.display="none"),["vex-summary-collapse","vex-detail-collapse"].forEach(function(q){var Z=document.getElementById(q);Z&&(Z.style.display="none")});const ae=Date.now();s("vex-progress-title").textContent=t("vex-progress-running")||"AI 抽取中",s("vex-progress-sub").textContent=(t("vex-progress-sub")||"{a} 张发票 + {b} 份报告 · 并行处理").replace("{a}",x.length).replace("{b}",o.length);const d=setInterval(()=>{const q=Math.floor((Date.now()-ae)/1e3);s("vex-progress-sub").textContent=(t("vex-progress-elapsed")||"已 {s} 秒 · {a} 张发票 + {b} 份报告").replace("{s}",q).replace("{a}",x.length).replace("{b}",o.length)},1e3);try{const q=new FormData;for(const ce of x)q.append("invoices",ce);for(const ce of o)q.append("reports",ce);const Z=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";q.append("lang",Z);const i=localStorage.getItem("mrpilot_token")||"",v=await fetch("/api/vat_excel/submit",{method:"POST",headers:l(),body:q});let b=null;try{b=await v.json()}catch{b=null}if(!v.ok||!b||!b.ok||!b.job_id)throw clearInterval(d),new Error(b&&b.detail||"HTTP "+v.status);const j=s("vex-progress-sub"),H=await window._reconPollJob(b.job_id,i,{onProgress:ce=>{j&&(j.textContent=window._reconProgressText(ce,Z))}});if(clearInterval(d),!H||H.status!=="done"||!H.result_id)throw new Error(t("vex-toast-fail")||"生成失败");const r=H.result_id;let C=0;const A=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(r)+"/download",{headers:l()});if(!A.ok)throw new Error("HTTP "+A.status);const K=(A.headers.get("Content-Disposition")||"").match(/filename="([^"]+)"/),te=K&&K[1]||"vat_recon_"+Date.now()+".xlsx",oe=await A.blob(),se=URL.createObjectURL(oe),ne=s("vex-download");ne.href=se,ne.download=te;try{const ce=document.createElement("a");ce.href=se,ce.download=te,document.body.appendChild(ce),ce.click(),setTimeout(()=>ce.remove(),100)}catch{}s("vex-progress").style.display="none";var m=document.getElementById("vex-download");m&&(m.style.display=""),r&&(C=await re(r)),window._onVexResultShown&&window._onVexResultShown(),C>0?showToast((t("vex-toast-some-fail")||"有 {n} 张发票 OCR 失败").replace("{n}",C),"warn"):showToast(t("vex-toast-done")||"Excel 已生成","success"),U(),setTimeout(N,800)}catch(q){clearInterval(d),s("vex-progress").style.display="none";const Z=(t("vex-toast-fail")||"生成失败")+": "+(q.message||q);showToast(Z,"error")}finally{p=!1,s("vex-build").disabled=!1}}function X(){x=[],o=[];var G=document.getElementById("vex-download");G&&(G.style.display="none"),D()}function ee(G){if(G==null)return"—";var ae=parseFloat(G);return isNaN(ae)?"—":ae.toLocaleString("th-TH",{minimumFractionDigits:2,maximumFractionDigits:2})}async function re(G){try{var ae=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(G),{headers:l()});if(!ae.ok)throw new Error(ae.status);var d=await ae.json(),m=d.raw_data_json;if(typeof m=="string")try{m=JSON.parse(m)}catch{m={}}m=m||{};var q=m.rows||[],Z=[];q.forEach(function(b){b.kind==="invoice_orphan"?Z.push({invoice_no:b.invoice_no||"",field:"仅发票有",report_value:"—",invoice_value:ee(b.amount_inv),kind:b.kind}):b.kind==="report_orphan"?Z.push({invoice_no:b.invoice_no||"",field:"仅报告有",report_value:ee(b.amount_rep),invoice_value:"—",kind:b.kind}):b.dims&&Object.keys(b.dims).length>0&&Object.keys(b.dims).forEach(function(j){var H=String(b.dims[j]||""),r=H.split(" ≠ ");Z.push({invoice_no:b.invoice_no||"",field:j,report_value:r[0]||H,invoice_value:r.length>1?r[1]:"—",kind:"diff"})})});var i=q.filter(function(b){return b.kind==="matched_cash"}).length,v=Math.max(0,parseInt(m.invoice_ocr_failed_count||0,10));return window._vexLastTask={total:m.n_total||0,matched:m.n_ok||0,diff:m.n_diff||0,incomplete:v,cash:i,diff_rows:Z,task_id:G},window._fillVexSummary&&window._fillVexSummary(),window._fillVexDetail&&window._fillVexDetail(),v}catch{return 0}}function de(){const G=document.getElementById("vex-pane");G&&G.querySelectorAll("[data-i18n]").forEach(ae=>{const d=t(ae.dataset.i18n);d&&(ae.textContent=d)}),D(),N()}function pe(){k("vex-drop-invoice","vex-input-invoice",$),k("vex-drop-report","vex-input-report",T);const G=s("vex-build"),ae=s("vex-reset");G&&G.addEventListener("click",Y),ae&&ae.addEventListener("click",X),document.querySelectorAll('[data-recon-tab="sale-vat"]').forEach(q=>{q.addEventListener("click",()=>{U(),N()})}),u();const d=document.getElementById("vex-task-search");d&&d.addEventListener("input",z);const m=document.getElementById("vex-toggle-preview");m&&m.addEventListener("click",()=>{const q=s("vex-preview-panel"),Z=s("vex-toggle-preview-label"),i=q&&q.style.display!=="none";q&&(q.style.display=i?"none":""),m&&m.classList.toggle("open",!i),Z&&(Z.textContent=i?t("vex-toggle-preview-open")||"查看清单":t("vex-toggle-preview-close")||"收起清单"),i||ie()}),D(),U()}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",pe):pe(),typeof window.subscribeI18n=="function"&&(window.subscribeI18n("vex-excel",de),window.subscribeI18n("vex-preview-panel",ie))})();(function(){const e=R=>document.getElementById(R),a=()=>localStorage.getItem("mrpilot_token")||"",n=()=>typeof window.currentLang=="string"&&window.currentLang?window.currentLang:localStorage.getItem("mrpilot_lang")||"th",s=()=>({Authorization:"Bearer "+a()}),l={inited:!1,glFile:[],vatFile:[],running:!1,currentTaskId:null,lastDetail:[],lastSummary:null},f={th:{not_found:"ไม่พบข้อมูล",running:"กำลังกระทบยอด…",error:"เกิดข้อผิดพลาด",need_files:"กรุณาเลือกไฟล์ทั้งสอง",done:"เสร็จสิ้น",hint_need_both:"อัปโหลด ① รายงานภาษีขาย + ② GL",hint_need_one_more:"อัปโหลดอีก 1 ไฟล์",hint_ready:"พร้อมแล้ว · กดเริ่มกระทบยอด",hist_load:"โหลด",hist_export:"ส่งออก",hist_delete:"ลบ",confirm_delete:"ยืนยันการลบงานนี้?",s_gl_total:"ยอดรวมตามบัญชีแยกประเภท",s_minus_gl_cr:"หัก : รายการเครดิตที่ไม่มีในรายงานภาษีขาย",s_plus_gl_dr:"บวก : รายการเดบิตที่ไม่มีในรายงานภาษีขาย",s_plus_vat_p:"บวก : รายการยอดขายที่ไม่มีในบัญชีแยกประเภท",s_minus_vat_n:"หัก : รายการลดหนี้ที่ไม่มีในบัญชีแยกประเภท",s_vat_total:"ยอดรวมตามรายงานภาษีขาย"},zh:{not_found:"未找到数据",running:"正在对账中...",error:"出错了",need_files:"请先选择两个文件",done:"完成",hint_need_both:"请上传① 销项税报告 + ② 总账 GL",hint_need_one_more:"还需上传 1 份文件",hint_ready:"已就绪 · 点击开始对账",hist_load:"加载",hist_export:"导出",hist_delete:"删除",confirm_delete:"确认删除此任务？",s_gl_total:"总账金额合计",s_minus_gl_cr:"减：销项税报告中未列的贷方记录",s_plus_gl_dr:"加：销项税报告中未列的借方记录",s_plus_vat_p:"加：总账中未列的销售记录",s_minus_vat_n:"减：总账中未列的贷项凭单(credit note)记录",s_vat_total:"销项税报告金额合计"},en:{not_found:"Not found",running:"Reconciling...",error:"Error",need_files:"Please select both files",done:"Done",hint_need_both:"Upload ① Output VAT report + ② GL file",hint_need_one_more:"1 more file required",hint_ready:"Ready · click Run to start",hist_load:"Load",hist_export:"Export",hist_delete:"Delete",confirm_delete:"Delete this task?",s_gl_total:"Total per General Ledger",s_minus_gl_cr:"Less: GL credits not in VAT Report",s_plus_gl_dr:"Add: GL debits not in VAT Report",s_plus_vat_p:"Add: Sales in VAT Report not in GL",s_minus_vat_n:"Less: Credit notes in VAT Report not in GL",s_vat_total:"Total per VAT Sales Report"},ja:{not_found:"データなし",running:"照合中…",error:"エラー",need_files:"両方のファイルを選択してください",done:"完了",hint_need_both:"① 売上税報告 + ② GL をアップロード",hint_need_one_more:"あと 1 ファイル必要",hint_ready:"準備完了 · 「開始」をクリック",hist_load:"読込",hist_export:"出力",hist_delete:"削除",confirm_delete:"このタスクを削除しますか?",s_gl_total:"総勘定元帳合計",s_minus_gl_cr:"減：売上税報告にないGL貸方記録",s_plus_gl_dr:"加：売上税報告にないGL借方記録",s_plus_vat_p:"加：GLにない売上記録",s_minus_vat_n:"減：GLにない赤伝記録",s_vat_total:"売上税報告合計"}},h=R=>(f[n()]||f.th)[R]||R;function x(R){const k=n(),X={gl_no_revenue_rows:{zh:"GL 中未找到收入科目行。请确认「收入科目前缀」是否正确(收入科目通常以 4 开头),改对后重试。",th:"ไม่พบรายการบัญชีรายได้ใน GL · ตรวจสอบ «คำนำหน้าบัญชีรายได้» (รายได้มักขึ้นต้นด้วย 4) แล้วลองใหม่",en:"No revenue-account rows found in the GL. Check the “revenue account prefix” (revenue usually starts with 4) and retry.",ja:"GL に収益科目の行が見つかりません。「収益科目プレフィックス」(通常 4 で始まる)を確認して再試行してください。"},gl_parse_failed:{zh:"GL 文件解析失败。请确认文件含日期/科目/借贷列,或换清晰的 Excel/CSV 重传。",th:"อ่านไฟล์ GL ไม่สำเร็จ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต-เครดิต หรืออัปโหลด Excel/CSV ที่ชัดเจน",en:"Failed to parse the GL file. Ensure it has date/account/debit-credit columns, or re-upload a clean Excel/CSV.",ja:"GL ファイルの解析に失敗しました。日付/科目/借方貸方列を確認するか、Excel/CSV を再アップロードしてください。"},vat_no_rows:{zh:"销项税报告里没有可对账的数据行。请确认上传了正确的销项税报告。",th:"ไม่พบแถวข้อมูลในรายงานภาษีขาย · ตรวจสอบว่าอัปโหลดรายงานที่ถูกต้อง",en:"No rows found in the sales-VAT report. Please check you uploaded the correct report.",ja:"売上VATレポートに行が見つかりません。正しいレポートをアップロードしたか確認してください。"},vat_parse_failed:{zh:"销项税报告解析失败。请换更清晰的版本,或转成 Excel/PDF 重传。",th:"อ่านรายงานภาษีขายไม่สำเร็จ · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น Excel/PDF",en:"Failed to parse the sales-VAT report. Try a clearer version, or convert to Excel/PDF.",ja:"売上VATレポートの解析に失敗しました。より鮮明な版か、Excel/PDF に変換してください。"}}[R];return X?X[k]||X.th||X.en:h("error")||"Error"}const o=R=>R==null||isNaN(R)?"":Number(R).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});function p(R,k,Y,X){const ee=e(R),re=e(k),de=e(Y);if(!ee||!re||!de)return;const pe=G=>{if(!G||!G.length)return;const ae=Array.isArray(l[X])?l[X].slice():[],d=new Set(ae.map(m=>m.name+"|"+m.size));for(const m of G){if(!m)continue;const q=m.name+"|"+m.size;d.has(q)||(ae.push(m),d.add(q))}l[X]=ae,w(de,ae),B(),S(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()};ee.addEventListener("click",()=>re.click()),ee.addEventListener("keydown",G=>{(G.key==="Enter"||G.key===" ")&&(G.preventDefault(),re.click())}),re.addEventListener("change",()=>{pe(Array.from(re.files||[])),re.value=""}),ee.addEventListener("dragover",G=>{G.preventDefault(),ee.classList.add("drag-over")}),ee.addEventListener("dragleave",()=>ee.classList.remove("drag-over")),ee.addEventListener("drop",G=>{G.preventDefault(),ee.classList.remove("drag-over");const ae=G.dataTransfer&&G.dataTransfer.files?Array.from(G.dataTransfer.files):[];pe(ae)})}function w(R,k){if(!R)return;if(!k||k.length===0){R.textContent="";return}const Y=k.reduce((X,ee)=>X+Math.round(ee.size/1024),0);if(k.length===1)R.textContent=k[0].name+"  ("+Y+" KB)";else{const X=window.t&&window.t("glv-files-count")||"{n} 个文件";R.textContent=X.replace("{n}",k.length)+"  ("+Y+" KB)"}}function g(R){const k=l[R];return Array.isArray(k)?k:k?[k]:[]}function B(){const R=e("btn-glv-run");if(!R)return;const k=g("glFile").length>0&&g("vatFile").length>0;R.disabled=!k||l.running}function S(){const R=e("glv-status");if(!R||l.running)return;const k=g("vatFile").length,Y=g("glFile").length;k===0&&Y===0?(R.className="vex-action-info muted",R.innerHTML="<span>"+h("hint_need_both")+"</span>"):k>0&&Y>0?(R.className="vex-action-info ok",R.innerHTML="<span>"+h("hint_ready")+"</span>"):(R.className="vex-action-info muted",R.innerHTML="<span>"+h("hint_need_one_more")+"</span>")}function I(R,k){const Y=R==="vat"?"vatFile":"glFile",X=R==="vat"?"glv-vat-input":"glv-gl-input",ee=R==="vat"?"glv-vat-name":"glv-gl-name",re=g(Y);k==null?l[Y]=[]:l[Y]=re.filter((pe,G)=>G!==k);const de=e(X);de&&(de.value=""),w(e(ee),g(Y)),B(),S(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}window._glvRemoveFile=I;function U(){l.glFile=[],l.vatFile=[],l.currentTaskId=null,l.lastDetail=[],l.lastSummary=null;const R=e("glv-vat-input");R&&(R.value="");const k=e("glv-gl-input");k&&(k.value="");const Y=e("glv-vat-name");Y&&(Y.textContent="");const X=e("glv-gl-name");X&&(X.textContent="");const ee=e("glv-result");ee&&(ee.style.display="none");const re=e("glv-kpi-strip");re&&(re.style.display="none"),B(),S(),window._glvClearPreviewSearch&&window._glvClearPreviewSearch(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}function N(R){const k=e("glv-tbody");if(!k)return;le(R.length),k.innerHTML="";const Y=h("not_found"),X=document.createDocumentFragment();R.forEach(ee=>{const re=document.createElement("tr"),de=(m,q)=>{const Z=document.createElement("td");return q&&(Z.className=q),Z.textContent=m,Z},pe=ee.gl_amount===null||ee.gl_amount===void 0,G=ee.diff;let ae="glv-num",d="glv-num";pe?(d+=" glv-cell-missing",ae+=" glv-cell-missing"):Math.abs(G||0)<.005?ae+=" glv-cell-ok":ae+=" glv-cell-diff",re.appendChild(de(ee.doc_no||"","glv-doc")),re.appendChild(de(ee.date||"","")),re.appendChild(de(ee.customer_name||"","")),re.appendChild(de(o(ee.vat_amount),"glv-num")),re.appendChild(de(pe?Y:o(ee.gl_amount),d)),re.appendChild(de(pe?Y:o(ee.diff),ae)),re.appendChild(de(ee.account_codes||"","glv-doc")),X.appendChild(re)}),k.appendChild(X)}function M(R){const k=e("glv-summary-table")&&e("glv-summary-table").querySelector("tbody");if(!k)return;k.innerHTML="",[{label:h("s_gl_total"),amount:R.gl_total,emph:!0,items:[],negate:!1},{label:h("s_minus_gl_cr"),amount:-(R.gl_only_credit||0),emph:!1,items:R.gl_only_credit_items||[],negate:!0},{label:h("s_plus_gl_dr"),amount:R.gl_only_debit||0,emph:!1,items:R.gl_only_debit_items||[],negate:!1},{label:h("s_plus_vat_p"),amount:R.vat_only_positive||0,emph:!1,items:R.vat_only_positive_items||[],negate:!1},{label:h("s_minus_vat_n"),amount:R.vat_only_negative||0,emph:!1,items:R.vat_only_negative_items||[],negate:!1},{label:h("s_vat_total"),amount:R.vat_total,emph:!0,items:[],negate:!1}].forEach(({label:X,amount:ee,emph:re,items:de,negate:pe})=>{const G=document.createElement("tr");G.className=re?"glv-summary-total":"glv-summary-sect";const ae=document.createElement("td"),d=document.createElement("td");ae.textContent=X,d.textContent=re?o(ee):"",G.appendChild(ae),G.appendChild(d),k.appendChild(G),(de||[]).forEach(m=>{const q=document.createElement("tr");q.className="glv-summary-item";const Z=document.createElement("td"),i=document.createElement("td"),v=[m.doc_no,m.date,m.name].filter(Boolean);Z.textContent="· "+v.join("  ·  ");const b=pe?-(m.amount||0):m.amount||0;i.textContent=o(b),q.appendChild(Z),q.appendChild(i),k.appendChild(q)})})}function L(R){e("glv-kpi-matched")&&(e("glv-kpi-matched").textContent=R&&R.matched!=null?R.matched:"—"),e("glv-kpi-diff")&&(e("glv-kpi-diff").textContent=R&&R.diff!=null?R.diff:"—"),e("glv-kpi-unmatched")&&(e("glv-kpi-unmatched").textContent=R&&R.unmatched!=null?R.unmatched:"—")}function z(R){if(!R)return"";try{const k=new Date(R);if(isNaN(k.getTime()))return R;const Y=X=>String(X).padStart(2,"0");return k.getFullYear()+"-"+Y(k.getMonth()+1)+"-"+Y(k.getDate())+" "+Y(k.getHours())+":"+Y(k.getMinutes())}catch{return R}}const V=10;var W=[],P=1;function u(){P=1,c();var R=((e("glv-hist-search")||{}).value||"").trim().toLowerCase();if(R){var k=e("glv-history-tbody");k&&k.querySelectorAll("tr").forEach(function(Y){Y.dataset.taskId&&(Y.style.display=Y.textContent.toLowerCase().indexOf(R)>=0?"":"none")})}}function c(){const R=e("glv-history-table-wrap"),k=e("glv-history-empty"),Y=e("glv-history-tbody"),X=e("glv-history-pager"),ee=e("glv-history-pager-info"),re=e("glv-history-prev"),de=e("glv-history-next");if(!Y)return;if(Y.innerHTML="",!W.length){R&&(R.style.display="none"),k&&(k.style.display=""),X&&(X.style.display="none");return}R&&(R.style.display=""),k&&(k.style.display="none");const pe=Math.ceil(W.length/V);P>pe&&(P=pe);const G=(P-1)*V,ae=W.slice(G,G+V);X&&(X.style.display=W.length>V?"":"none",ee&&(ee.textContent=P+" / "+pe),re&&(re.disabled=P<=1),de&&(de.disabled=P>=pe)),ae.forEach(m=>{const q=document.createElement("tr");q.dataset.taskId=m.id;const Z=document.createElement("td");Z.textContent=z(m.created_at);const i=document.createElement("td");i.className="glv-history-file",i.title=(m.vat_filename||"")+" + "+(m.gl_filename||""),i.textContent=(m.vat_filename||"?")+" + "+(m.gl_filename||"?");const v=document.createElement("td");v.className="glv-num",v.textContent=(m.vat_row_count||0)+" / "+(m.gl_row_count||0);const b=document.createElement("td");b.className="glv-num",b.textContent=m.matched_count||0;const j=document.createElement("td");j.className="glv-num",j.textContent=m.diff_count||0;const H=document.createElement("td");H.className="glv-num",H.textContent=m.unmatched_count||0;const r=document.createElement("td");r.className="glv-history-actions";const C=(te,oe,se,ne)=>{const ce=document.createElement("button");return ce.type="button",se&&(ce.className=se),ce.title=oe,ce.setAttribute("aria-label",oe),ce.innerHTML=te,ce.onclick=ne,ce},A='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 8a6 6 0 1 0 12 0A6 6 0 0 0 2 8z"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',O='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',K='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';r.appendChild(C(A,h("hist_load"),"",()=>T(m.id))),r.appendChild(C(O,h("hist_export"),"",()=>_(m.id))),r.appendChild(C(K,h("hist_delete"),"glv-del",()=>E(m.id))),[Z,i,v,b,j,H,r].forEach(te=>q.appendChild(te)),Y.appendChild(q)})}function y(){var R=e("glv-history-prev"),k=e("glv-history-next");R&&!R._glvBound&&(R._glvBound=!0,R.addEventListener("click",function(){P>1&&(P--,c())})),k&&!k._glvBound&&(k._glvBound=!0,k.addEventListener("click",function(){var Y=Math.ceil(W.length/V);P<Y&&(P++,c())}))}async function $(){try{const k=await(await fetch("/api/recon/gl-vat/tasks",{headers:s()})).json();W=k&&k.tasks||[],P=1,c(),y()}catch(R){console.error("[gl-vat] history load failed:",R)}}async function T(R){try{const Y=await(await fetch("/api/recon/gl-vat/"+R,{headers:s()})).json();if(!Y||!Y.ok)throw new Error("load_failed");l.currentTaskId=R,l.lastDetail=Y.detail||[],l.lastSummary=Y.summary||{},L(Y.stats||{}),N(l.lastDetail),M(l.lastSummary);const X=e("glv-result");X&&(X.style.display=""),Q(),window.scrollTo({top:X?X.offsetTop-80:0,behavior:"smooth"})}catch(k){console.error("[gl-vat] load task failed:",k),alert(h("error")+": "+(k.message||k))}}async function _(R){try{const k="/api/recon/gl-vat/"+R+"/export?lang="+encodeURIComponent(n()),Y=await fetch(k,{headers:s()});if(!Y.ok)throw new Error("HTTP "+Y.status);const X=await Y.blob(),ee=document.createElement("a");ee.href=URL.createObjectURL(X),ee.download="GL_VAT_recon_"+R+".xlsx",document.body.appendChild(ee),ee.click(),setTimeout(()=>{URL.revokeObjectURL(ee.href),ee.remove()},200)}catch(k){console.error("[gl-vat] exportTask failed:",k),typeof showToast=="function"&&showToast(h("error")+": "+(k.message||k),"error")}}async function E(R){let k;if(typeof window.showConfirm=="function"?k=await window.showConfirm(h("confirm_delete"),{danger:!0}):k=confirm(h("confirm_delete")),!!k)try{const Y=await fetch("/api/recon/gl-vat/"+R,{method:"DELETE",headers:s()});if(!Y.ok)throw new Error("HTTP "+Y.status);$()}catch(Y){console.error("[gl-vat] delete failed:",Y),typeof showToast=="function"&&showToast(h("error")+": "+(Y.message||Y),"error")}}async function D(){if(!l.glFile||!l.vatFile){typeof showToast=="function"&&showToast(h("need_files"),"warn");return}l.running=!0,B();const R=e("glv-status"),k=e("glv-progress"),Y=e("glv-progress-sub");R&&(R.className="vex-action-info muted",R.style.color="",R.innerHTML="<span>"+h("running")+"</span>"),k&&(k.style.display=""),Y&&(Y.textContent=(l.vatFile.name||"VAT")+" + "+(l.glFile.name||"GL"));const X=new FormData,ee=g("vatFile"),re=g("glFile");for(const pe of ee)X.append("vat_files",pe,pe.name);for(const pe of re)X.append("gl_files",pe,pe.name);const de=(e("glv-prefix")&&e("glv-prefix").value||"4").trim()||"4";X.append("revenue_prefix",de),X.append("lang",n());try{const pe=await fetch("/api/recon/gl-vat/submit",{method:"POST",headers:s(),body:X});let G=null;try{G=await pe.json()}catch{G=null}if(!pe.ok||!G||!G.ok||!G.job_id)throw new Error(G&&G.detail||G&&G.error||"HTTP "+pe.status);const ae=e("glv-progress-sub"),d=await window._reconPollJob(G.job_id,a(),{onProgress:i=>{ae&&(ae.textContent=window._reconProgressText(i,n()))}});if(!d||d.status!=="done"||!d.result_id)throw d&&d.status==="failed"&&d.error_code?new Error(x(d.error_code)):new Error(h("error")||"Error");const m=await fetch("/api/recon/gl-vat/"+encodeURIComponent(d.result_id),{headers:s()});let q=null;try{q=await m.json()}catch{q=null}if(!m.ok||!q||!q.ok)throw new Error(q&&q.detail||q&&q.error||"HTTP "+m.status);l.currentTaskId=q.task_id,l.lastDetail=q.detail||[],l.lastSummary=q.summary||{},L(q.stats||{}),N(l.lastDetail),M(l.lastSummary);const Z=e("glv-result");Z&&(Z.style.display=""),Q(),R&&(R.className="vex-action-info ok",R.style.color="",R.innerHTML="<span>"+h("done")+" · GL "+(q.gl_row_count||0)+" · VAT "+(q.vat_row_count||0)+"</span>"),$()}catch(pe){console.error("[gl-vat] run failed:",pe),R&&(R.className="vex-action-info",R.style.color="#ef4444",R.innerHTML="<span>"+h("error")+": "+(pe.message||pe)+"</span>")}finally{l.running=!1,k&&(k.style.display="none"),B()}}async function J(){if(l.currentTaskId)try{const R="/api/recon/gl-vat/"+l.currentTaskId+"/export?lang="+encodeURIComponent(n()),k=await fetch(R,{headers:s()});if(!k.ok)throw new Error("HTTP "+k.status);const Y=await k.blob(),X=document.createElement("a");X.href=URL.createObjectURL(Y),X.download="GL_VAT_recon_"+l.currentTaskId+".xlsx",document.body.appendChild(X),X.click(),setTimeout(()=>{URL.revokeObjectURL(X.href),X.remove()},200)}catch(R){console.error("[gl-vat] export failed:",R),typeof showToast=="function"&&showToast(h("error")+": "+(R.message||R),"error")}}function F(){l.running||S(),$(),l.lastDetail&&l.lastDetail.length&&N(l.lastDetail),l.lastSummary&&M(l.lastSummary)}function Q(){var R=e("glv-kpi-strip");R&&(R.style.display="");var k=e("glv-section-summary");k&&k.setAttribute("data-collapsed","false");var Y=e("glv-section-detail");Y&&Y.setAttribute("data-collapsed","false")}function ie(){document.querySelectorAll(".glv-section-head[data-toggle]").forEach(R=>{const k=R.getAttribute("data-toggle"),Y=document.getElementById(k);if(!Y)return;const X=ee=>{if(ee.target&&ee.target.closest("button")!==null&&!ee.target.classList.contains("glv-section-head"))return;const re=Y.getAttribute("data-collapsed")==="true";Y.setAttribute("data-collapsed",re?"false":"true")};R.addEventListener("click",X),R.addEventListener("keydown",ee=>{(ee.key==="Enter"||ee.key===" ")&&(ee.preventDefault(),X(ee))})})}function le(R){const k=e("glv-detail-count");k&&(k.textContent=R!=null?String(R):"")}function ue(){if(l.inited){$();return}l.inited=!0,p("glv-drop-gl","glv-gl-input","glv-gl-name","glFile"),p("glv-drop-vat","glv-vat-input","glv-vat-name","vatFile");const R=e("btn-glv-run");R&&R.addEventListener("click",D);const k=e("btn-glv-export");k&&k.addEventListener("click",J);const Y=e("btn-glv-reset");Y&&Y.addEventListener("click",U);const X=e("glv-hist-search");X&&X.addEventListener("input",u),ie(),L(null),S(),window._loadGlvHistory=$,$(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("gl-vat-recon",F)}window.GlVatRecon={ensureInit:ue},window._glvPreviewFiles=function(R){return g(R==="vat"?"vatFile":"glFile")}})();(function(){const e=["flowaccount","peak","xero","quickbooks","express"],a={flowaccount:"FlowAccount",peak:"PEAK",xero:"Xero",quickbooks:"QuickBooks",express:"Express"},n=["expense_office","expense_travel","expense_utility","asset_inventory","asset_fixed","liability_ap","revenue_sales","revenue_service","other"],s=["vat_7","vat_0","vat_exempt","wht_1","wht_3","wht_5","non_vat"],l="468b50c1-5593-4fd6-990d-515ce8085563";let f={sub:"clients",loaded:{clients:!1,accounts:!1,taxes:!1,products:!1},items:{clients:[],accounts:[],taxes:[],products:[]},clientList:[],clientLoaded:!1,addingNew:{clients:!1,accounts:!1,taxes:!1,products:!1},bound:!1};function h(){const T=typeof _userInfo<"u"?_userInfo:null;return!!(T&&(T.role==="owner"||T.is_super_admin))}function x(){const T=typeof _userInfo<"u"?_userInfo:null;return!!(T&&T.id===l)}function o(T){return typeof escapeHtml=="function"?escapeHtml(T==null?"":String(T)):String(T??"")}function p(T,_){try{typeof showToast=="function"&&showToast(T,_||"info")}catch{}}async function w(T,_){const E=localStorage.getItem("mrpilot_token");if(E&&!(f.loaded[T]&&!_))try{const D=await fetch("/api/erp/mappings/"+T,{headers:{Authorization:"Bearer "+E}});if(!D.ok)throw new Error("http_"+D.status);const J=await D.json();f.items[T]=J.items||[],f.loaded[T]=!0}catch{f.items[T]=[],f.loaded[T]=!1}}async function g(T){if(f.clientLoaded)return;const _=localStorage.getItem("mrpilot_token");if(_)try{const E=await fetch("/api/clients?include_inactive=false",{headers:{Authorization:"Bearer "+_}});if(!E.ok)throw new Error("http_"+E.status);const D=await E.json();f.clientList=(D.clients||D.items||[]).filter(J=>J.is_active!==!1),f.clientLoaded=!0}catch{f.clientList=[]}}function B(){const T=document.getElementById("erp-map-pane-wrap");if(!T)return;const _=!h();let E="";_&&(E+='<div class="erp-map-readonly-banner"><svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="8"/><path d="M10 6v4M10 13v0.01"/></svg>'+o(t("erp-map-readonly-tip"))+"</div>"),E+='<div class="erp-map-toolbar">',!_&&f.sub!=="products"&&(E+='<button class="btn btn-primary" type="button" id="erp-map-add-btn" data-i18n="erp-map-add-row">'+o(t("erp-map-add-row"))+"</button>"),E+="</div>",E+='<div class="erp-map-table" id="erp-map-table-host"></div>',T.innerHTML=E,S();const D=document.getElementById("erp-map-dev-bar");D&&(D.style.display=h()&&x()?"":"none")}function S(){const T=document.getElementById("erp-map-table-host");if(!T)return;const _=f.sub,E=f.items[_]||[],D=f.addingNew[_],J=!h();if(!E.length&&!D){T.innerHTML='<div class="erp-map-empty"><strong>'+o(t("erp-map-empty-"+_))+"</strong>"+o(t("erp-map-empty-"+_+"-sub"))+"</div>";return}let F="";F+=I(_),D&&!J&&(F+=z(_)),E.forEach(function(Q){F+=V(_,Q,J)}),T.innerHTML=F}function I(T){return T==="clients"?'<div class="erp-map-row erp-map-head row-clients"><div>'+o(t("erp-map-col-client"))+"</div><div>"+o(t("erp-map-col-erp"))+"</div><div>"+o(t("erp-map-col-erp-code"))+"</div><div>"+o(t("erp-map-col-notes"))+"</div><div>"+o(t("erp-map-col-actions"))+"</div></div>":T==="accounts"?'<div class="erp-map-row erp-map-head row-accounts"><div>'+o(t("erp-map-col-erp"))+"</div><div>"+o(t("erp-map-col-category"))+"</div><div>"+o(t("erp-map-col-erp-code"))+"</div><div>"+o(t("erp-map-col-erp-name"))+"</div><div>"+o(t("erp-map-col-notes"))+"</div><div>"+o(t("erp-map-col-actions"))+"</div></div>":T==="products"?'<div class="erp-map-row erp-map-head row-products"><div>'+o(t("erp-map-col-item-name"))+"</div><div>"+o(t("erp-map-col-erp-product-code"))+"</div><div>"+o(t("erp-map-col-erp-name"))+"</div><div>"+o(t("erp-map-col-notes"))+"</div><div>"+o(t("erp-map-col-actions"))+"</div></div>":'<div class="erp-map-row erp-map-head row-taxes"><div>'+o(t("erp-map-col-erp"))+"</div><div>"+o(t("erp-map-col-tax"))+"</div><div>"+o(t("erp-map-col-erp-tax-code"))+"</div><div>"+o(t("erp-map-col-notes"))+"</div><div>"+o(t("erp-map-col-actions"))+"</div></div>"}function U(T,_){let E='<select class="form-input" data-erp-field="'+_+'">';return E+='<option value="">'+o(t("erp-map-pick-erp"))+"</option>",e.forEach(function(D){const J=D===T?" selected":"";E+='<option value="'+D+'"'+J+">"+o(a[D])+"</option>"}),E+="</select>",E}function N(T){let _='<select class="form-input" data-erp-field="client_id">';return _+='<option value="">'+o(t("erp-map-pick-client"))+"</option>",(f.clientList||[]).forEach(function(E){const D=String(E.id)===String(T)?" selected":"";_+='<option value="'+E.id+'"'+D+">"+o(E.name||"#"+E.id)+"</option>"}),_+="</select>",_}function M(T){let _='<select class="form-input" data-erp-field="pearnly_category">';return _+='<option value="">'+o(t("erp-map-pick-cat"))+"</option>",n.forEach(function(E){const D=E===T?" selected":"";_+='<option value="'+E+'"'+D+">"+o(t("erp-map-cat-"+E))+"</option>"}),_+="</select>",_}function L(T){let _='<select class="form-input" data-erp-field="pearnly_tax_kind">';return _+='<option value="">'+o(t("erp-map-pick-tax"))+"</option>",s.forEach(function(E){const D=E===T?" selected":"";_+='<option value="'+E+'"'+D+">"+o(t("erp-map-tax-"+E))+"</option>"}),_+="</select>",_}function z(T){const _='<button class="btn btn-primary" type="button" data-erp-save="new" style="padding:6px 12px;height:32px;">'+o(t("erp-map-save"))+"</button>";return T==="clients"?'<div class="erp-map-row erp-map-row-add row-clients" data-erp-row="new"><div data-label="'+o(t("erp-map-col-client"))+'">'+N("")+'</div><div data-label="'+o(t("erp-map-col-erp"))+'">'+U("","erp_type")+'</div><div data-label="'+o(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+o(t("erp-map-ph-erp-code"))+'"></div><div data-label="'+o(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+o(t("erp-map-ph-notes"))+'"></div><div>'+_+"</div></div>":T==="accounts"?'<div class="erp-map-row erp-map-row-add row-accounts" data-erp-row="new"><div data-label="'+o(t("erp-map-col-erp"))+'">'+U("","erp_type")+'</div><div data-label="'+o(t("erp-map-col-category"))+'">'+M("")+'</div><div data-label="'+o(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+o(t("erp-map-ph-acc-code"))+'"></div><div data-label="'+o(t("erp-map-col-erp-name"))+'"><input type="text" class="form-input" data-erp-field="erp_name" placeholder="'+o(t("erp-map-ph-acc-name"))+'"></div><div data-label="'+o(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+o(t("erp-map-ph-notes"))+'"></div><div>'+_+"</div></div>":'<div class="erp-map-row erp-map-row-add row-taxes" data-erp-row="new"><div data-label="'+o(t("erp-map-col-erp"))+'">'+U("","erp_type")+'</div><div data-label="'+o(t("erp-map-col-tax"))+'">'+L("")+'</div><div data-label="'+o(t("erp-map-col-erp-tax-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+o(t("erp-map-ph-tax-code"))+'"></div><div data-label="'+o(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+o(t("erp-map-ph-notes"))+'"></div><div>'+_+"</div></div>"}function V(T,_,E){const D=E?"":'<button class="erp-map-del-btn" type="button" data-erp-del="'+o(_.id)+'" title="'+o(t("erp-map-delete"))+'"><svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h12M8 6V4h4v2M6 6l1 11h6l1-11"/></svg></button>',J='<span class="erp-map-erp-badge">'+o(a[_.erp_type]||_.erp_type)+"</span>";if(T==="clients")return'<div class="erp-map-row row-clients"><div data-label="'+o(t("erp-map-col-client"))+'" class="erp-map-cell-name">'+o(_.client_name||"#"+_.client_id)+'</div><div data-label="'+o(t("erp-map-col-erp"))+'">'+J+'</div><div data-label="'+o(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+o(_.erp_code||"")+'</div><div data-label="'+o(t("erp-map-col-notes"))+'">'+o(_.notes||"")+"</div><div>"+D+"</div></div>";if(T==="accounts"){const Q=t("erp-map-cat-"+(_.pearnly_category||"other"))||_.pearnly_category;return'<div class="erp-map-row row-accounts"><div data-label="'+o(t("erp-map-col-erp"))+'">'+J+'</div><div data-label="'+o(t("erp-map-col-category"))+'" class="erp-map-cell-name">'+o(Q)+'</div><div data-label="'+o(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+o(_.erp_code||"")+'</div><div data-label="'+o(t("erp-map-col-erp-name"))+'">'+o(_.erp_name||"")+'</div><div data-label="'+o(t("erp-map-col-notes"))+'">'+o(_.notes||"")+"</div><div>"+D+"</div></div>"}if(T==="products")return'<div class="erp-map-row row-products"><div data-label="'+o(t("erp-map-col-item-name"))+'" class="erp-map-cell-name">'+o(_.item_name||"")+'</div><div data-label="'+o(t("erp-map-col-erp-product-code"))+'" class="erp-map-code">'+o(_.erp_code||"")+'</div><div data-label="'+o(t("erp-map-col-erp-name"))+'">'+o(_.erp_name||"")+'</div><div data-label="'+o(t("erp-map-col-notes"))+'">'+o(_.notes||"")+"</div><div>"+D+"</div></div>";const F=t("erp-map-tax-"+(_.pearnly_tax_kind||""))||_.pearnly_tax_kind;return'<div class="erp-map-row row-taxes"><div data-label="'+o(t("erp-map-col-erp"))+'">'+J+'</div><div data-label="'+o(t("erp-map-col-tax"))+'" class="erp-map-cell-name"><span class="erp-map-tax-badge">'+o(F)+'</span></div><div data-label="'+o(t("erp-map-col-erp-tax-code"))+'" class="erp-map-code">'+o(_.erp_code||"")+'</div><div data-label="'+o(t("erp-map-col-notes"))+'">'+o(_.notes||"")+"</div><div>"+D+"</div></div>"}async function W(T){const _=f.sub,E={};T.querySelectorAll("[data-erp-field]").forEach(function(Q){E[Q.dataset.erpField]=(Q.value||"").trim()});const D=localStorage.getItem("mrpilot_token");if(!D)return;let J={},F="/api/erp/mappings/"+_;if(_==="clients"){if(!E.client_id||!E.erp_type||!E.erp_code){p(t("erp-map-save-fail"),"error");return}J={client_id:parseInt(E.client_id,10),erp_type:E.erp_type,erp_code:E.erp_code,notes:E.notes||""}}else if(_==="accounts"){if(!E.erp_type||!E.pearnly_category||!E.erp_code){p(t("erp-map-save-fail"),"error");return}J={erp_type:E.erp_type,pearnly_category:E.pearnly_category,erp_code:E.erp_code,erp_name:E.erp_name||"",notes:E.notes||""}}else{if(!E.erp_type||!E.pearnly_tax_kind||!E.erp_code){p(t("erp-map-save-fail"),"error");return}J={erp_type:E.erp_type,pearnly_tax_kind:E.pearnly_tax_kind,erp_code:E.erp_code,notes:E.notes||""}}try{const Q=await fetch(F,{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+D},body:JSON.stringify(J)});if(!Q.ok)throw new Error("http_"+Q.status);f.addingNew[_]=!1,await w(_,!0),S(),p(t("erp-map-saved-toast"),"success")}catch{p(t("erp-map-save-fail"),"error")}}async function P(T){if(!await window.pearnlyConfirm(t("erp-map-confirm-delete")))return;const E=f.sub,D=localStorage.getItem("mrpilot_token");try{const J=await fetch("/api/erp/mappings/"+E+"/"+encodeURIComponent(T),{method:"DELETE",headers:{Authorization:"Bearer "+D}});if(!J.ok)throw new Error("http_"+J.status);await w(E,!0),S(),p(t("erp-map-deleted-toast"),"success")}catch{p(t("erp-map-delete-fail"),"error")}}async function u(){await g(),await w(f.sub,!1),B()}function c(T){T!==f.sub&&(f.sub=T,f.addingNew[T]=!1,["clients","accounts","taxes","products"].forEach(function(_){_!==T&&(f.addingNew[_]=!1)}),document.querySelectorAll(".erp-map-subtab").forEach(function(_){_.classList.toggle("active",_.dataset.erpSubtab===T)}),w(T,!1).then(function(){B()}))}function y(){f.bound||(f.bound=!0,document.addEventListener("click",function(T){const _=T.target.closest(".erp-subtab[data-erp-subtab]");if(_){T.preventDefault();const Q=_.dataset.erpSubtab;document.querySelectorAll(".erp-subtab").forEach(function(ie){ie.classList.toggle("active",ie.dataset.erpSubtab===Q)}),document.querySelectorAll(".erp-subpanel").forEach(function(ie){ie.classList.toggle("active",ie.dataset.erpSubpanel===Q)}),Q==="mappings"&&setTimeout(u,50);return}const E=T.target.closest(".erp-map-subtab[data-erp-subtab]");if(E){T.preventDefault(),c(E.dataset.erpSubtab);return}if(T.target.closest("#erp-map-add-btn")){if(T.preventDefault(),!h())return;f.addingNew[f.sub]=!0,S();return}const J=T.target.closest('[data-erp-save="new"]');if(J){T.preventDefault();const Q=J.closest('[data-erp-row="new"]');Q&&W(Q);return}const F=T.target.closest("[data-erp-del]");if(F){T.preventDefault(),P(F.dataset.erpDel);return}}))}function $(){const T=document.getElementById("erp-map-pane-wrap");T&&T.children.length>0&&B(),document.querySelectorAll(".erp-map-subtab").forEach(function(_){const E="erp-map-subtab-"+_.dataset.erpSubtab,D=t(E);D&&D!==E&&(_.textContent=D)})}y(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-mappings",$)})();(function(){let e=null,a=0,n=!1;function s(u){return typeof escapeHtml=="function"?escapeHtml(u==null?"":String(u)):String(u??"")}function l(u,c){try{typeof showToast=="function"&&showToast(u,c||"info")}catch{}}async function f(u){const c=Date.now();if(e&&c-a<3e4)return e;const y=localStorage.getItem("mrpilot_token");if(!y)return[];try{const $=await fetch("/api/erp/connectors/status",{headers:{Authorization:"Bearer "+y}});if(!$.ok)return[];const T=await $.json();return e=T&&T.connectors||[],a=c,e}catch{return[]}}function h(){try{return localStorage.getItem("pn_push_default_connector")||""}catch{return""}}function x(u){try{localStorage.setItem("pn_push_default_connector",u||"")}catch{}}function o(u){if(!u||!u.length)return null;const c=h();if(c){const $=u.find(T=>T.id===c);if($)return $}const y=u.find($=>$.is_default);return y||u[0]}function p(u){if(!u)return!1;const c=String(u.status||"").toLowerCase();return c==="exception"||c==="exception_pending"||c==="rejected"}function w(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function g(u){const c=u&&(u.type||u.id);return c==="xero"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5.5 8l2 2 3-3.5"/></svg>':c==="webhook"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="11.5" r="1.8"/><circle cx="11" cy="4.5" r="1.8"/><path d="M6.4 10l3.2-4M5 9.6V5.5a3 3 0 016 0"/></svg>':'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/><rect x="11" y="3" width="3" height="10" rx="1"/></svg>'}async function B(u,c){if(!u||!c)return!1;const y=document.getElementById("btn-push-default");y&&(y.disabled=!0,y.classList.add("loading"));const $=localStorage.getItem("mrpilot_token");try{let T,_={method:"POST",headers:{Authorization:"Bearer "+$}};u.type==="xero"?T="/api/erp/xero/push/"+encodeURIComponent(c):(T="/api/erp/push",_.headers["Content-Type"]="application/json",_.body=JSON.stringify({history_id:c,endpoint_id:u.endpoint_id||void 0}));const E=await fetch(T,_);let D={};try{D=await E.json()}catch{}if(!E.ok){let J=D&&D.detail||"unknown";typeof J=="object"&&(J=J.code||JSON.stringify(J));let F=String(J||"unknown");if(u.type==="xero"){const Q=F.replace(/^xero\./,"").toLowerCase(),ie=t("xero-"+Q);ie&&ie!=="xero-"+Q&&(F=ie)}return l(t("unified-push-fail").replace("{name}",u.name).replace("{err}",F),"error"),!1}if(D&&D.ok===!1){let J=D.error_msg||D.error_code||"unknown";return J=String(J).slice(0,200),l(t("unified-push-fail").replace("{name}",u.name).replace("{err}",J),"error"),!1}return l(t("unified-push-ok").replace("{name}",u.name),"success"),!0}catch(T){return l(t("unified-push-fail").replace("{name}",u.name).replace("{err}",T.message||"network"),"error"),!1}finally{y&&(y.disabled=!1,y.classList.remove("loading"))}}async function S(u,c){for(const y of u)await B(y,c)}function I(u,c){const y=document.createElement("div");y.className="pn-push-dropdown",y.id="pn-push-dropdown";const $=(u||[]).map(_=>{const E=!!(c&&_.id===c.id),D=_.method==="download"?t("unified-push-tag-download"):E?t("unified-push-tag-default"):"";return'<div class="pn-pd-item" data-cid="'+s(_.id)+'"><span class="pn-pd-icon">'+g(_)+'</span><span class="pn-pd-name">'+s(_.name)+"</span>"+(D?'<span class="pn-pd-tag">'+s(D)+"</span>":"")+(E?'<span class="pn-pd-check">✓</span>':"")+"</div>"}).join(""),T=u&&u.length>1?'<div class="pn-pd-divider"></div><div class="pn-pd-item pn-pd-all" data-cid="__all__"><span class="pn-pd-icon"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h10M3 10h10M3 13.5h6"/></svg></span><span class="pn-pd-name">'+s(t("unified-push-all").replace("{n}",u.length))+"</span></div>":"";return y.innerHTML=$+T,y}function U(){const u=document.getElementById("pn-push-dropdown");u&&u.remove()}async function N(){if(document.getElementById("pn-push-dropdown")){U();return}const u=await f()||[],c=o(u),y=I(u,c),$=document.getElementById("pn-push-wrap");$&&$.appendChild(y)}async function M(){const u=await f()||[],c=o(u);if(!c)return;const y=w(),$=y&&(y._historyId||y.history_id);if($){if(p(y)){l(t("unified-push-disabled-exc"),"warn");return}await B(c,$)}}async function L(u){U();const c=await f()||[],y=w(),$=y&&(y._historyId||y.history_id);if(!$)return;if(p(y)){l(t("unified-push-disabled-exc"),"warn");return}if(u==="__all__"){await S(c,$);return}const T=c.find(_=>_.id===u);T&&(x(u),await B(T,$),V())}async function z(){const u=document.getElementById("drawer-history-save");if(!u||u.querySelector("#pn-push-wrap"))return;const c=document.createElement("div");c.id="pn-push-wrap",c.className="pn-push-wrap",c.dataset.loading="1",u.insertBefore(c,u.firstChild),["btn-push-erp","btn-xero-push"].forEach(D=>{u.querySelectorAll("#"+D).forEach(J=>{J.style.display="none"})});const y=await f()||[],$=o(y),T=y.length>0;if(!T)c.innerHTML='<button type="button" class="btn btn-ghost pn-push-empty" id="btn-push-default" disabled title="'+s(t("unified-push-empty-tip"))+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/></svg><span style="margin-left:4px;">'+s(t("unified-push-empty"))+"</span></button>";else{const D=y.length>1;c.innerHTML='<div class="pn-push-split"><button type="button" class="pn-push-main" id="btn-push-default" title="'+s(t("unified-push-tip"))+'">'+g($)+"<span>"+s(t("unified-push-to").replace("{name}",$?$.name:""))+"</span></button>"+(D?'<button type="button" class="pn-push-arrow" id="btn-push-arrow" title="'+s(t("unified-push-other"))+'"><svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5l3 3 3-3"/></svg></button>':"")+"</div>"}delete c.dataset.loading;const _=c.querySelector("#btn-push-default");_&&T&&_.addEventListener("click",M);const E=c.querySelector("#btn-push-arrow");E&&E.addEventListener("click",function(D){D.stopPropagation(),N()}),n||(n=!0,document.addEventListener("click",function(D){const J=D.target.closest(".pn-pd-item");if(J){const F=J.getAttribute("data-cid");L(F);return}D.target.closest("#btn-push-arrow")||U()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("unified-push",V))}function V(){const u=document.getElementById("pn-push-wrap");u&&(u.remove(),e=null,a=0,z())}function W(){const u=document.getElementById("drawer-history-save");if(!u||!u.querySelector("#pn-push-wrap"))return;["btn-push-erp","btn-xero-push"].forEach(y=>{u.querySelectorAll("#"+y).forEach($=>{$.style.display!=="none"&&($.style.display="none")})});const c=u.querySelectorAll("#pn-push-wrap");if(c.length>1)for(let y=1;y<c.length;y++)c[y].remove()}function P(){try{const u=function(){return document.getElementById("drawer-body")},c=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&z(),W()}),y=u();if(y)c.observe(y,{childList:!0,subtree:!0});else{const $=new MutationObserver(function(){const T=u();T&&(c.observe(T,{childList:!0,subtree:!0}),$.disconnect())});$.observe(document.body,{childList:!0,subtree:!0})}setTimeout(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&z(),W()},200)}catch{}}P()})();(function(){function e(){const n=document.getElementById("erp-map-show-advanced-btn");if(!n)return;const s=document.getElementById("erp-map-subtabs");if(!s)return;const l=s.classList.contains("show-advanced"),f=n.querySelector(".erp-map-adv-btn-label");if(f&&typeof t=="function"){const h=l?"erp-map-hide-advanced":"erp-map-show-advanced",x=t(h);x&&x!==h&&(f.textContent=x)}n.setAttribute("aria-pressed",l?"true":"false")}document.addEventListener("click",function(n){if(!n.target.closest("#erp-map-show-advanced-btn"))return;n.preventDefault();const l=document.getElementById("erp-map-subtabs");if(l&&(l.classList.toggle("show-advanced"),e(),!l.classList.contains("show-advanced")&&l.querySelector(".erp-map-subtab.active.erp-map-subtab-advanced"))){const h=l.querySelector('.erp-map-subtab[data-erp-subtab="clients"]');h&&h.click()}});function a(){e()}typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-map-advanced-toggle",a)})();(function(){const e="pearnly_erp_onboard_shown";let a=!1;function n(){try{return Array.isArray(window._erpEndpoints)&&window._erpEndpoints.length>0}catch{return!1}}function s(){if(document.getElementById("erp-onboard-mask"))return;const f=document.createElement("div");f.id="erp-onboard-mask",f.className="erp-onboard-mask",f.innerHTML='<div class="erp-onboard-modal" role="dialog" aria-modal="true"><div class="erp-onboard-icon"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="6" width="24" height="20" rx="3"/><path d="M9 13h14M9 18h10"/><path d="M22 22l3 3 5-5"/></svg></div><div class="erp-onboard-title" id="erp-onboard-title"></div><div class="erp-onboard-body" id="erp-onboard-body"></div><div class="erp-onboard-btns"><button type="button" class="btn btn-secondary" id="erp-onboard-later"></button><button type="button" class="btn btn-primary" id="erp-onboard-ok"></button></div></div>',document.body.appendChild(f);function h(){const o=document.getElementById("erp-onboard-title"),p=document.getElementById("erp-onboard-body"),w=document.getElementById("erp-onboard-ok"),g=document.getElementById("erp-onboard-later");o&&(o.textContent=t("erp-onboard-title")),p&&(p.textContent=t("erp-onboard-body")),w&&(w.textContent=t("erp-onboard-ok")),g&&(g.textContent=t("erp-onboard-later"))}h();function x(){f.style.display="none"}document.getElementById("erp-onboard-ok").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}x();try{const o=document.querySelector('#btn-add-endpoint, [data-action="erp-add-endpoint"]');o&&o.scrollIntoView({behavior:"smooth",block:"center"})}catch{}}),document.getElementById("erp-onboard-later").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}x()}),f.addEventListener("click",function(o){o.target===f&&x()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-onboard-modal",function(){f.style.display!=="none"&&h()})}function l(){if(!a){try{if(localStorage.getItem(e)==="1")return}catch{}n()||(a=!0,s(),requestAnimationFrame(function(){requestAnimationFrame(function(){if(n())return;const f=document.getElementById("erp-onboard-mask");f&&(f.style.display="flex")})}))}}document.addEventListener("click",function(f){const h=f.target.closest('.auto-nav-item[data-auto-tab="erp"]'),x=f.target.closest('.erp-subtab[data-erp-subtab="connect"]');(h||x)&&setTimeout(l,700)})})();(function(){const e={parse:{zh:"解析文件中",th:"กำลังอ่านไฟล์",en:"Parsing files",ja:"ファイル解析中"},report:{zh:"读取报告中",th:"กำลังอ่านรายงาน",en:"Reading report",ja:"レポート読込中"},reconcile:{zh:"对账中",th:"กำลังกระทบยอด",en:"Reconciling",ja:"照合中"},build:{zh:"生成中",th:"กำลังสร้างไฟล์",en:"Building",ja:"作成中"},persist:{zh:"保存中",th:"กำลังบันทึก",en:"Saving",ja:"保存中"},done:{zh:"完成",th:"เสร็จสิ้น",en:"Done",ja:"完了"}};window._reconProgressText=function(a,n){a=a||{},n=window._currentLang||n||localStorage.getItem("mrpilot_lang")||"th",e.parse[n]||(n="th");const s=a.stage||"parse",l=e[s]||e.parse,f=l[n]||l.th||l.en,h=a.stage_total,x=a.stage_done;if(s==="parse"&&Number.isFinite(h)&&h>0){const o={zh:"共 {d}/{t} 个文件",th:"{d}/{t} ไฟล์",en:"{d}/{t} files",ja:"{d}/{t} ファイル"}[n]||"{d}/{t} files";return f+" · "+o.replace("{d}",x||0).replace("{t}",h)}return f},window._reconPollJob=async function(a,n,s){s=s||{};const l=s.intervalMs||1500,f=s.maxMs||1200*1e3,h=Date.now();let x=0;for(;;){let o=null;try{const p=await fetch("/api/recon/jobs/"+encodeURIComponent(a),{headers:{Authorization:"Bearer "+n}});try{o=await p.json()}catch{o=null}(!p.ok||!o||!o.ok)&&(o=null)}catch{o=null}if(o){if(x=0,s.onProgress)try{s.onProgress(o.progress||{},o)}catch{}if(o.status==="done"||o.status==="failed"||o.status==="needs_review"||o.status==="needs_mapping")return o}else if(++x>=10)return{ok:!1,status:"failed",error_code:"poll_unreachable"};if(Date.now()-h>f)return{ok:!1,status:"timeout",error_code:"timeout"};await new Promise(p=>setTimeout(p,l))}}})();(function(){let e=!1,a=[],n=[],s=null,l="all",f=[],h={stmt:"",gl:""},x=[];const o=i=>document.getElementById(i);function p(i){if(i==null)return"—";const v=Number(i);return isNaN(v)?"—":v.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function w(i){return i?String(i).slice(0,10).split("-").reverse().join("/"):"—"}function g(i){return String(i||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function B(i,v){v=window._currentLang||v||"th";const b={stmt_headers_not_found:{zh:"认不出银行账单表头 · 请确认文件含日期/金额/余额列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตารางบัญชีธนาคารไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/จำนวนเงิน/ยอดคงเหลือ หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect bank statement headers · ensure the file has date/amount/balance columns, or re-upload as a clean Excel/CSV",ja:"銀行明細のヘッダーを認識できません · 日付/金額/残高列を確認するか、Excel/CSVに変換して再アップロードしてください"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含日期/科目/借方/贷方列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตาราง GL ไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต/เครดิต หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect GL headers · ensure the file has date/account/debit/credit columns, or re-upload as a clean Excel/CSV",ja:"GLのヘッダーを認識できません · 日付/科目/借方/貸方列を確認するか、Excel/CSVに変換して再アップロードしてください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水,或换更清晰的版本重传",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง หรือใช้เวอร์ชันที่ชัดเจนกว่า",en:"No transaction rows found · please upload the correct statement, or try a clearer version",ja:"取引データが見つかりません · 正しい明細をアップロードするか、より鮮明なファイルでお試しください"},no_rows:{zh:"解析后没有可对账的数据行 · 请确认文件内容完整,或换清晰版本重传",th:"ไม่มีแถวข้อมูลให้กระทบยอดหลังการอ่าน · ตรวจสอบความสมบูรณ์ของไฟล์ หรืออัปโหลดใหม่",en:"No reconcilable rows after parsing · check the file is complete, or re-upload a clearer version",ja:"解析後に照合可能な行がありません · ファイルの完全性を確認するか再アップロードしてください"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密 · 请换文件或转 PDF/Excel 重传",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส · ลองไฟล์อื่นหรือแปลงเป็น PDF/Excel",en:"File cannot be read · may be corrupted or encrypted · try another file or convert to PDF/Excel",ja:"ファイルを読み取れません · 破損または暗号化の可能性 · 別ファイルまたはPDF/Excelに変換してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロードしてください"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本,或转成 PDF / Excel / CSV 重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น PDF / Excel / CSV",en:"Could not read the file · try a clearer version, or convert to PDF / Excel / CSV",ja:"読み取りに失敗 · より鮮明なファイルか、PDF / Excel / CSV に変換して再試行してください"}},j={zh:"解析失败 · 请换更清晰的文件,或转成 Excel / CSV 后重新上传",th:"อ่านไฟล์ไม่สำเร็จ · ลองไฟล์ที่ชัดเจนกว่า หรือแปลงเป็น Excel / CSV แล้วอัปโหลดใหม่",en:"Parsing failed · try a clearer file, or convert to Excel / CSV and re-upload",ja:"解析に失敗しました · より鮮明なファイルか、Excel / CSV に変換して再アップロードしてください"},H=b[i]||j;return H[v]||H.th||H.en}function S(i){const v=i==="stmt"?a:n,b=o(`brv2-${i}-name`);if(b)if(v.length===0)b.textContent="";else{const H=window._currentLang||"zh",r={zh:"个文件",th:" ไฟล์",en:" file(s)",ja:" ファイル"};b.textContent=v.length+(r[H]||" 个文件")}const j=o("brv2-preview-panel");j&&j.style.display!=="none"&&N(i),I()}function I(){const i=o("brv2-toggle-preview"),v=o("brv2-preview-panel"),b=a.length+n.length>0;i&&(i.style.display=b?"":"none"),!b&&v&&(v.style.display="none",i&&i.classList.remove("open"))}function U(){N("stmt"),N("gl")}function N(i){const v=o(i==="stmt"?"brv2-pp-stmt-col":"brv2-pp-gl-col");if(!v)return;const b=i==="stmt"?a:n,j=window._currentLang||"zh",H={stmt:{zh:"① 银行账单",th:"① บัญชีธนาคาร",en:"① Bank Stmt",ja:"① 銀行明細"},gl:{zh:"② 总账 GL",th:"② GL รายงาน",en:"② GL Report",ja:"② GL帳簿"}},r=(H[i]||{})[j]||H[i].zh,C=g(window.t&&window.t("vex-preview-search")||"搜索文件名..."),A=g(window.t&&window.t("vex-preview-clear-all")||"全清"),O=h[i]||"";v.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+g(r)+' <span class="vex-pp-col-count">'+b.length+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="brv2-pp-search-'+i+'" type="text" placeholder="'+C+'" value="'+g(O)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="brv2-pp-clearall-'+i+'" type="button">'+A+'</button></div><div class="vex-pp-file-list" id="brv2-pp-'+i+'-list"></div><div class="vex-pp-pagination" id="brv2-pp-'+i+'-pg"></div>';const K=o("brv2-pp-search-"+i);K&&K.addEventListener("input",function(oe){h[i]=oe.target.value,M(i)});const te=o("brv2-pp-clearall-"+i);te&&te.addEventListener("click",function(){i==="stmt"?a.length=0:n.length=0,S(i),D()}),M(i)}function M(i){const v=o("brv2-pp-"+i+"-list"),b=o("brv2-pp-"+i+"-pg");if(!v)return;const j=i==="stmt"?a:n,H=(h[i]||"").toLowerCase(),r=H?j.filter(O=>O.name.toLowerCase().includes(H)):j.slice(),C='<svg class="vex-pp-fi-ico" viewBox="0 0 14 16" fill="none" stroke="currentColor" stroke-width="1.4" width="12" height="14"><path d="M3 1h6l3 3v11H3V1z"/><path d="M9 1v3h3"/></svg>',A='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" width="11" height="11"><path d="M2 4h10M5 4V2h4v2M5.5 7v4M8.5 7v4M3 4l1 8h6l1-8"/></svg>';if(v.innerHTML=r.map((O,K)=>'<div class="vex-pp-file-row">'+C+'<span class="vex-pp-fi-name" title="'+g(O.name)+'">'+g(O.name)+'</span><span class="vex-pp-fi-size">'+L(O.size)+'</span><button class="vex-pp-fi-del" type="button" data-zone="'+i+'" data-idx="'+j.indexOf(O)+'" aria-label="remove">'+A+"</button></div>").join(""),v.querySelectorAll(".vex-pp-fi-del").forEach(function(O){O.addEventListener("click",function(){const K=parseInt(O.dataset.idx,10);O.dataset.zone==="stmt"?a.splice(K,1):n.splice(K,1),S(O.dataset.zone),D()})}),b){const O=window.t&&window.t("vex-preview-count")||"显示 {n} / 共 {m}";b.textContent=O.replace("{n}",r.length).replace("{m}",j.length)}}function L(i){return i?i<1024?i+" B":i<1048576?(i/1024).toFixed(1)+" KB":(i/1048576).toFixed(1)+" MB":""}var z="pearnly.brv2.lastAnchorOcr";function V(i){try{var v=i&&i._anchor_ocr;if(!v||typeof v!="object")return;var b={stmt_opening:Number.isFinite(+v.stmt_opening)?+v.stmt_opening:null,gl_opening:Number.isFinite(+v.gl_opening)?+v.gl_opening:null,gl_closing:Number.isFinite(+v.gl_closing)?+v.gl_closing:null,stmt_closing:Number.isFinite(+v.stmt_closing)?+v.stmt_closing:null,ts:Date.now()};localStorage.setItem(z,JSON.stringify(b))}catch{}}function W(){try{var i=localStorage.getItem(z);if(!i)return null;var v=JSON.parse(i);return!v||typeof v!="object"?null:v}catch{return null}}function P(){var i=W();if(i){var v={"brv2-anchor-stmt-opening":i.stmt_opening,"brv2-anchor-gl-opening":i.gl_opening,"brv2-anchor-gl-closing":i.gl_closing,"brv2-anchor-stmt-closing":i.stmt_closing},b=0;Object.keys(v).forEach(function(A){var O=document.getElementById(A);if(O&&O.value===""){var K=v[A];if(Number.isFinite(K)){O.value=K.toFixed(2);var te=O.closest&&O.closest(".brv2-anchor-cell");te&&te.classList.add("is-prefilled"),b+=1}}});var j=document.getElementById("brv2-anchor-eq"),H=document.getElementById("brv2-anchor-eq-val");if(j&&H&&Number.isFinite(i.stmt_opening)&&Number.isFinite(i.gl_opening)){var r=i.stmt_opening-i.gl_opening;H.textContent=r.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),j.style.display=""}if(b>0){var C=document.getElementById("brv2-anchor-prefill-banner");C&&C.classList.add("show")}}}function u(){var i=document.getElementById("brv2-anchor-prefill-banner");if(i){var v=!1;["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"].forEach(function(b){var j=document.getElementById(b);if(j){var H=j.closest&&j.closest(".brv2-anchor-cell");H&&H.classList.contains("is-prefilled")&&(v=!0)}}),i.classList.toggle("show",v)}}var c=[["stmt_opening","brv2-anchor-stmt-opening"],["gl_opening","brv2-anchor-gl-opening"],["gl_closing","brv2-anchor-gl-closing"],["stmt_closing","brv2-anchor-stmt-closing"]];function y(i,v){return window.t&&window.t(i)||v}function $(i){return String(i??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function T(i){return Number.isFinite(+i)?(+i).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—"}function _(i){var v=document.getElementById("brv2-summary-collapse");if(!(!v||!v.parentNode)){var b=document.getElementById("brv2-anchor-audit"),j=i&&i._anchor_overrides;if(!j||typeof j!="object"||Object.keys(j).length===0){b&&b.parentNode&&b.parentNode.removeChild(b);return}b||(b=document.createElement("div"),b.id="brv2-anchor-audit",b.style.cssText="margin-top:14px;background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:14px 16px;",v.parentNode.insertBefore(b,v.nextSibling));var H=c.map(function(r){var C=j[r[0]];if(!C)return"";var A=+C.ocr||0,O=+C.user||0,K=O-A,te=K>0?"+":(K<0,""),oe=Math.abs(K)<.005?"#6b7280":K>0?"#16a34a":"#dc2626";return'<tr><td style="padding:6px 10px;color:#111827;font-size:13px">'+$(y(r[1],r[0]))+'</td><td style="padding:6px 10px;color:#6b7280;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+$(T(A))+'</td><td style="padding:6px 10px;background:#fef08a;color:#92400e;font-weight:600;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+$(T(O))+'</td><td style="padding:6px 10px;color:'+oe+';font-weight:500;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+$(te+T(K))+"</td></tr>"}).join("");b.innerHTML='<div style="font-weight:600;color:#92400e;font-size:13px;margin-bottom:10px">'+$(y("brv2-anchor-audit-title","⚠ This run contains manually entered anchors"))+'</div><table style="width:100%;border-collapse:collapse;font-family:inherit"><thead><tr><th style="padding:6px 10px;text-align:left;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+$(y("brv2-anchor-audit-col-field","Field"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+$(y("brv2-anchor-audit-col-ocr","OCR"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+$(y("brv2-anchor-audit-col-user","User"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+$(y("brv2-anchor-audit-col-diff","Diff"))+"</th></tr></thead><tbody>"+H+"</tbody></table>"}}function E(){const i=o("brv2-toggle-preview");i&&!i._reconBound&&(i._reconBound=!0,i.addEventListener("click",function(){const v=o("brv2-preview-panel"),b=o("brv2-toggle-preview-label"),j=v&&v.style.display!=="none";v&&(v.style.display=j?"none":""),i.classList.toggle("open",!j),b&&(b.textContent=j?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),j||U()}))}function D(){const i=o("brv2-run-btn"),v=o("brv2-status"),b=a.length>0,j=n.length>0;if(i&&(i.disabled=!(b&&j)),v){const H=window._currentLang||"zh";if(!b&&!j){const r={zh:"请上传银行账单和 GL 文件",th:"กรุณาอัปโหลดบัญชีธนาคารและ GL",en:"Upload bank statement and GL files",ja:"銀行明細と GL を両方アップロードしてください"};v.textContent=r[H]||r.zh}else if(b)if(j){const r={zh:"两份文件已就绪",th:"พร้อมสอบทาน",en:"Ready to reconcile",ja:"照合を開始できます"};v.textContent=r[H]||r.zh}else{const r={zh:"还缺 GL 文件",th:"ยังขาดไฟล์ GL",en:"Missing GL file",ja:"GL ファイルが未アップロード"};v.textContent=r[H]||r.zh}else{const r={zh:"还缺银行账单 PDF",th:"ยังขาดไฟล์บัญชีธนาคาร PDF",en:"Missing bank statement PDF",ja:"銀行明細 PDF が未アップロード"};v.textContent=r[H]||r.zh}}}function J(i,v,b){const j=o(i),H=o(v);!j||!H||(j.addEventListener("click",()=>H.click()),j.addEventListener("keydown",r=>{(r.key==="Enter"||r.key===" ")&&(r.preventDefault(),H.click())}),j.addEventListener("dragover",r=>{r.preventDefault(),j.classList.add("drag-over")}),j.addEventListener("dragleave",()=>j.classList.remove("drag-over")),j.addEventListener("drop",r=>{r.preventDefault(),j.classList.remove("drag-over");const C=Array.from(r.dataTransfer.files||[]);b==="stmt"?a.push(...C):n.push(...C),S(b),D()}),H.addEventListener("change",()=>{const r=Array.from(H.files||[]);b==="stmt"?a.push(...r):n.push(...r),H.value="",S(b),D()}))}function F(i){const v=o("brv2-progress"),b=o("brv2-run-btn"),j=o("brv2-error");v&&(v.style.display=i?"":"none"),b&&(b.disabled=i),j&&(j.style.display="none")}function Q(i){const v=o("brv2-error");v&&(v.textContent=i,v.style.display="",v.scrollIntoView({behavior:"smooth",block:"nearest"})),F(!1),D(),window.showToast&&window.showToast(i,"error")}async function ie(){if(a.length===0||n.length===0)return;const i=localStorage.getItem("mrpilot_token")||"",v=window._currentLang||"zh",b=(o("brv2-acct-select")||{}).value||"";ue(!1),F(!0);try{const j=new FormData;a.forEach(ne=>j.append("stmt_files",ne)),n.forEach(ne=>j.append("gl_files",ne)),j.append("gl_account",b),j.append("lang",v);const H=parseFloat((o("brv2-anchor-gl-closing")||{}).value),r=parseFloat((o("brv2-anchor-stmt-closing")||{}).value),C=parseFloat((o("brv2-anchor-stmt-opening")||{}).value),A=parseFloat((o("brv2-anchor-gl-opening")||{}).value);Number.isFinite(H)&&j.append("gl_closing_override",H),Number.isFinite(r)&&j.append("stmt_closing_override",r),Number.isFinite(C)&&j.append("stmt_opening_override",C),Number.isFinite(A)&&j.append("gl_opening_override",A);const O=await fetch("/api/recon/bank-v2/submit",{method:"POST",headers:{Authorization:"Bearer "+i},body:j});let K=null;try{K=await O.json()}catch{K=null}if(K&&K.needs_mapping){F(!1),window.ReconMapping?window.ReconMapping.show(K,{token:i,lang:v,onConfirmed:function(){ie()}}):Q(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(!O.ok||!K||!K.ok||!K.job_id){F(!1),K&&(K.detail||K.error)?Q(_humanizeBackendError(K.detail||K.error,"Error "+O.status)):Q(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const te=o("brv2-progress-sub"),oe=await window._reconPollJob(K.job_id,i,{onProgress:ne=>{te&&(te.textContent=window._reconProgressText(ne,v))}});if(oe&&oe.status==="needs_mapping"&&oe.mapping){F(!1),window.ReconMapping?window.ReconMapping.show(oe.mapping,{token:i,lang:v,onConfirmed:function(){ie()}}):Q(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(oe&&oe.status==="needs_review"&&oe.review){F(!1),window.ReconReview?window.ReconReview.show(oe.review,{token:i,lang:v,jobId:K.job_id,onConfirmed:async function(ne){F(!0);const ce=await window._reconPollJob(ne,i,{onProgress:fe=>{te&&(te.textContent=window._reconProgressText(fe,v))}});await se(ce)}}):Q(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(oe&&oe.status==="failed"){F(!1),Q(B(oe.error_code,v));return}await se(oe);async function se(ne){try{if(!ne||ne.status!=="done"||!ne.result_id){F(!1),Q(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const ce=await fetch("/api/recon/bank-v2/"+encodeURIComponent(ne.result_id),{headers:{Authorization:"Bearer "+i}});let fe=null;try{fe=await ce.json()}catch{fe=null}if(!ce.ok||fe===null||!fe.ok){F(!1),Q(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}(fe.gl_accounts||[]).length>1&&le(fe.gl_accounts),s=fe,f=fe.detail||[],l="all",document.querySelectorAll(".brv2-filter-btn").forEach(ge=>ge.classList.toggle("active",ge.dataset.filter==="all")),V(fe&&fe.summary),F(!1),X(fe),re();const ve=o("brv2-summary-collapse");ve&&ve.scrollIntoView({behavior:"smooth",block:"nearest"})}catch(ce){F(!1),Q(ce.message||"Network error")}}}catch(j){Q(j.message||"Network error")}}function le(i){const v=o("brv2-acct-select");if(!v)return;const b=window._currentLang||"zh",j={zh:"全部账户",th:"ทุกบัญชี",en:"All Accounts",ja:"すべての口座"}[b]||"全部账户";v.innerHTML=`<option value="">${j}</option>`+i.map(H=>`<option value="${g(H)}">${g(H)}</option>`).join(""),v.style.display=""}function ue(i){const v=o("brv2-summary-collapse"),b=o("brv2-detail-collapse"),j=o("brv2-export-btn"),H=o("brv2-new-btn"),r=o("brv2-parse-info-wrap");v&&(v.style.display=i?"":"none"),b&&(b.style.display=i?"":"none"),j&&(j.style.display=i?"":"none"),H&&(H.style.display=i?"":"none"),!i&&r&&(r.style.display="none");const C=o("brv2-warnings");!i&&C&&(C.style.display="none",C.innerHTML="")}function R(i){const v=o("brv2-parse-info-wrap"),b=o("brv2-parse-info-body");if(!v||!b)return;const j=i.parse_info;if(!j){v.style.display="none";return}const H=window._currentLang||"zh",r={title:{zh:"文件解析状态",th:"สถานะการอ่านไฟล์",en:"File Parse Status",ja:"ファイル解析状態"},type:{zh:"类型",th:"ประเภท",en:"Type",ja:"種別"},file:{zh:"文件名",th:"ชื่อไฟล์",en:"File",ja:"ファイル"},rows:{zh:"解析行数",th:"แถวที่พบ",en:"Rows Found",ja:"解析行数"},bank:{zh:"银行/科目",th:"ธนาคาร/บัญชี",en:"Bank/Account",ja:"銀行/科目"},status:{zh:"状态",th:"สถานะ",en:"Status",ja:"状態"},stmt:{zh:"账单",th:"บัญชีธนาคาร",en:"Stmt",ja:"明細"},gl:{zh:"总账GL",th:"GL",en:"GL",ja:"GL"},ok:{zh:"✓ 成功",th:"✓ สำเร็จ",en:"✓ OK",ja:"✓ 成功"},warn:{zh:"⚠ 0行",th:"⚠ 0 แถว",en:"⚠ 0 rows",ja:"⚠ 0行"},fail:{zh:"✗ 失败",th:"✗ ล้มเหลว",en:"✗ Failed",ja:"✗ 失敗"}},C=se=>(r[se]||{})[H]||(r[se]||{}).zh||se,A=[...(j.stmt_files||[]).map(se=>({...se,_type:"stmt",_extra:se.bank_code||""})),...(j.gl_files||[]).map(se=>({...se,_type:"gl",_extra:(se.accounts||[]).join(", ")}))],O={stmt_headers_not_found:{zh:"认不出表头列 · 请确认文件含日期/金额/余额列",th:"หาคอลัมน์หัวตารางไม่เจอ · ตรวจสอบไฟล์มีวันที่/จำนวนเงิน/ยอดคงเหลือ",en:"Cannot detect column headers · ensure file has date/amount/balance columns",ja:"列ヘッダーが認識できません · 日付/金額/残高列を確認してください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง",en:"No transaction rows found · please check the file",ja:"取引データが見つかりません · ファイルを確認してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロード"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส",en:"File cannot be read · may be corrupted or encrypted",ja:"ファイルを読み取れません · 破損または暗号化の可能性"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本或换 PDF 格式重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่าหรือเปลี่ยนเป็น PDF",en:"Could not read file · try a clearer version or upload as PDF",ja:"読み取り失敗 · より鮮明なファイルまたは PDF 形式で再試行"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含科目/借方/贷方列",th:"หาหัวคอลัมน์ GL ไม่เจอ · ตรวจสอบมีคอลัมน์บัญชี/เดบิต/เครดิต",en:"Cannot detect GL column headers · ensure account/debit/credit columns exist",ja:"GL 列ヘッダー認識不可 · 科目/借方/貸方列を確認してください"}},K=se=>{const ne=String(se||"");return/Cannot detect bank statement column headers/i.test(ne)?"stmt_headers_not_found":/Cannot detect GL column headers/i.test(ne)?"gl_headers_not_found":/No transaction rows found|no pages parsed/i.test(ne)?"stmt_no_rows":/unsupported format/i.test(ne)?"file_not_supported":/Cannot read Excel|file_unreadable/i.test(ne)?"file_unreadable":/Gemini.*invalid JSON|Gemini.*parsed but failed|validation errors|BankStatementDocument schema|layer2:|layer1:/i.test(ne)?"ocr_failed":null},te=se=>{const ne=se.error_code||K(se.error);if(ne&&O[ne]){const ce=window._currentLang||"zh";return O[ne][ce]||O[ne].zh}return String(se.error||"").slice(0,80)},oe=se=>!se.ok&&se.error?`<span style="color:#dc2626">${C("fail")} — ${g(te(se))}</span>`:se.rows?`<span style="color:#059669">${C("ok")} (${se.rows})</span>`:`<span style="color:#d97706">${C("warn")}</span>`;b.innerHTML=`
            <div style="font-size:12px;font-weight:600;margin-bottom:6px;color:var(--ink-2)">${C("title")}</div>
            <table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:4px">
                <thead>
                    <tr style="background:#f3f4f6;font-weight:600">
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${C("type")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb">${C("file")}</th>
                        <th style="padding:6px 8px;text-align:center;border:1px solid #e5e7eb;white-space:nowrap">${C("rows")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${C("bank")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${C("status")}</th>
                    </tr>
                </thead>
                <tbody>
                    ${A.map(se=>`<tr>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;white-space:nowrap">${se._type==="stmt"?C("stmt"):C("gl")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${g(se.file||"")}">${g(se.file||"")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;text-align:center">${se.rows||0}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;color:var(--ink-2)">${g(se._extra||"")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb">${oe(se)}</td>
                    </tr>`).join("")}
                </tbody>
            </table>`,v.style.display=""}async function k(i){const v=localStorage.getItem("mrpilot_token")||"",b=window._currentLang||"zh";try{const j=await fetch("/api/recon/bank-v2/"+i+"/export?lang="+b,{headers:{Authorization:"Bearer "+v}});if(!j.ok){const te=await j.json().catch(()=>({}));window.showToast&&window.showToast(te.detail||"Export failed","error");return}const H=await j.blob(),C=(j.headers.get("content-disposition")||"").match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/),A=C?C[1].replace(/['"]/g,""):"reconciliation.xlsx",O=URL.createObjectURL(H),K=document.createElement("a");K.href=O,K.download=A,document.body.appendChild(K),K.click(),document.body.removeChild(K),URL.revokeObjectURL(O)}catch(j){window.showToast&&window.showToast("Export error: "+j.message,"error")}}function Y(i,v){const b=o("brv2-summary-collapse");let j=o("brv2-warnings");const H=window._currentLang||"zh",r={zh:"⏭ 已跳过无法识别的文件:",th:"⏭ ข้ามไฟล์ที่อ่านไม่ได้:",en:"⏭ Skipped unreadable file:",ja:"⏭ 読み取れないファイルをスキップ:"}[H]||"⏭ ",C=[];if((v||[]).forEach(A=>C.push(r+" "+A)),(i||[]).forEach(A=>C.push(A)),!C.length){j&&(j.style.display="none");return}if(!j)if(j=document.createElement("div"),j.id="brv2-warnings",b&&b.parentNode)b.parentNode.insertBefore(j,b);else return;j.style.cssText="display:block;margin:10px 0;padding:10px 14px;background:#FEF3C7;border:1px solid #FCD34D;border-radius:8px;color:#92400E;font-size:13px;line-height:1.6",j.innerHTML=C.map(A=>"<div>"+g(A)+"</div>").join("")}function X(i){R(i),Y(i.warnings||[],i.skipped_files||[]),!i.ok&&i.error&&window.showToast&&window.showToast(i.error,"error");const v=i.stats||{},b=i.summary||{},j=v.matched||0,H=(v.gl_debit_only||0)+(v.gl_credit_only||0),r=(v.stmt_withdrawal_only||0)+(v.stmt_deposit_only||0),C=Number(b.formula_diff||0),A=Math.abs(C)<.05;o("brv2-kpi-matched")&&(o("brv2-kpi-matched").textContent=j),o("brv2-kpi-diff")&&(o("brv2-kpi-diff").textContent=p(C)),o("brv2-kpi-unmatched")&&(o("brv2-kpi-unmatched").textContent=H+r);const O=o("brv2-kpi-diff-icon");O&&(O.style.background=A?"#d1fae5":"#fee2e2",O.style.color=A?"#065f46":"#b91c1c");const K=o("brv2-formula-sub");if(K){const ce=window._currentLang||"zh";K.textContent=A?{zh:"✓ 平衡",th:"✓ สมดุล",en:"✓ Balanced",ja:"✓ 一致"}[ce]||"✓ 平衡":({zh:"差 ",th:"ต่าง ",en:"Diff ",ja:"差 "}[ce]||"差 ")+p(C)}const te=o("brv2-detail-sub");if(te){const ce=window._currentLang||"zh",fe={zh:"共 {n} 行",th:"ทั้งหมด {n} แถว",en:"{n} rows",ja:"計 {n} 行"}[ce]||"共 {n} 行";te.textContent=fe.replace("{n}",f.length)}function oe(ce,fe,ve){const ge=o(ce);ge&&(ge.textContent=(ve&&fe>0?"(":"")+p(ve?-fe:fe)+(ve&&fe>0?")":""))}oe("brf-gl-close",b.gl_closing||0),oe("brf-open-diff",b.opening_diff||0),oe("brf-gl-debit-only",b.gl_debit_only_amount||0,!0),oe("brf-gl-credit-only",b.gl_credit_only_amount||0),oe("brf-stmt-wd-only",b.stmt_withdrawal_only_amount||0,!0),oe("brf-stmt-dep-only",b.stmt_deposit_only_amount||0),oe("brf-calc-close",b.formula_stmt_closing||0),oe("brf-stmt-close",b.stmt_closing||0),o("brf-diff")&&(o("brf-diff").textContent=p(C));const se=o("brv2-fcell-diff");se&&se.classList.toggle("brv2-fcell-diff-ok",A);const ne=o("brv2-export-btn");ne&&(ne.onclick=()=>{s&&k(s.task_id)}),_(b),ue(!0),ee()}function ee(){const i=o("brv2-tbody");if(!i)return;const v=f.filter(r=>l==="all"?!0:l==="matched"?r.match_status==="matched":l==="gl_only"?r.match_status.startsWith("gl_"):l==="stmt_only"?r.match_status.startsWith("stmt_"):!0);if(v.length===0){const r={zh:"无记录",th:"ไม่มีรายการ",en:"No rows",ja:"行なし"}[window._currentLang||"zh"]||"无记录";i.innerHTML=`<tr><td colspan="10" style="text-align:center;padding:20px;color:var(--ink-3)">${r}</td></tr>`;return}const b=window._currentLang||"zh",j={zh:"OCR 余额验证未通过 · 上一行余额 ± 金额 ≠ 本行余额，请核对原 PDF",th:"การตรวจสอบยอดคงเหลือไม่ผ่าน · ยอดก่อนหน้า ± จำนวน ≠ ยอดบรรทัดนี้ โปรดตรวจสอบ PDF ต้นฉบับ",en:"Balance check FAILED · prev_balance ± amount ≠ this row balance — verify against the original PDF",ja:"残高検証エラー · 前残高 ± 金額 ≠ この行残高 — 元のPDFと照合してください"}[b],H={zh:"OCR 低置信度 · 数字模糊或难以辨认，请核对原 PDF",th:"OCR ความมั่นใจต่ำ · ตัวเลขเบลอหรืออ่านยาก โปรดตรวจสอบ PDF ต้นฉบับ",en:"OCR low confidence · digit was blurry or hard to read — verify against the original PDF",ja:"OCR信頼度低 · 数字がぼやけている — 元のPDFと照合してください"}[b];i.innerHTML=v.map(r=>{const C=r.match_status,A=r.match_layer;let O="",K="";C==="matched"?(A===1&&(O="matched",K='<span class="brv2-status-badge brv2-badge-matched">L1 ✓</span>'),A===2&&(O="matched-l2",K='<span class="brv2-status-badge brv2-badge-matched-l2">L2 ~</span>'),A===3&&(O="matched-l3",K='<span class="brv2-status-badge brv2-badge-matched-l3">L3 ?</span>')):C==="gl_debit_only"||C==="gl_credit_only"?(O="gl-only",K='<span class="brv2-status-badge brv2-badge-gl-only">GL</span>'):(O="stmt-only",K=`<span class="brv2-status-badge brv2-badge-stmt-only">${{zh:"账单",th:"บัญชี",en:"Stmt",ja:"明細"}[b]||"账单"}</span>`);let te="";return r.stmt_balance_ok===!1&&(te+=`<span class="brv2-ocr-warn brv2-ocr-warn-bal" title="${g(j)}">⚠</span>`,O+=" brv2-row-warn"),r.stmt_confidence==="low"&&(te+=`<span class="brv2-ocr-warn brv2-ocr-warn-conf" title="${g(H)}">◌</span>`,O.includes("brv2-row-warn")||(O+=" brv2-row-warn-soft")),`<tr class="${O.trim()}">
              <td>${K}${te}</td>
              <td>${g(w(r.stmt_date))}</td>
              <td title="${g(r.stmt_desc)}" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${g(r.stmt_desc)}</td>
              <td class="num">${r.stmt_withdrawal?p(r.stmt_withdrawal):""}</td>
              <td class="num">${r.stmt_deposit?p(r.stmt_deposit):""}</td>
              <td>${g(w(r.gl_date))}</td>
              <td title="${g(r.gl_doc_no)}" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${g(r.gl_doc_no)}</td>
              <td class="num">${r.gl_debit?p(r.gl_debit):""}</td>
              <td class="num">${r.gl_credit?p(r.gl_credit):""}</td>
              <td>${A?"L"+A:"—"}</td>
            </tr>`}).join("")}async function re(){const i=localStorage.getItem("mrpilot_token")||"";try{const b=await(await fetch("/api/recon/bank-v2/tasks",{headers:{Authorization:"Bearer "+i}})).json();d(b.tasks||[])}catch{const b=o("brv2-history-empty"),j=window._currentLang||"zh",H={zh:"加载失败",th:"โหลดประวัติไม่ได้",en:"Load failed",ja:"読み込み失敗"}[j]||"加载失败";b&&(b.textContent=H,b.style.display="");const r=o("brv2-history-table-wrap");r&&(r.style.display="none")}}const de=10;let pe=1;function G(){const i=o("brv2-history-pager"),v=o("brv2-history-pager-info"),b=o("brv2-history-prev"),j=o("brv2-history-next");if(!i)return;if(x.length<=de){i.style.display="none";return}i.style.display="";const H=Math.ceil(x.length/de);v&&(v.textContent=pe+" / "+H),b&&(b.disabled=pe<=1),j&&(j.disabled=pe>=H)}function ae(){const i=o("brv2-history-prev"),v=o("brv2-history-next");i&&!i._brv2Bound&&(i._brv2Bound=!0,i.addEventListener("click",()=>{pe>1&&(pe--,d(x))})),v&&!v._brv2Bound&&(v._brv2Bound=!0,v.addEventListener("click",()=>{const b=Math.ceil(x.length/de);pe<b&&(pe++,d(x))}))}function d(i){i!==void 0&&(x=i||[],pe=1);const v=x,b=o("brv2-history-empty"),j=o("brv2-history-table-wrap"),H=o("brv2-history-tbody");if(!H)return;const r=window._currentLang||"zh";if(!v.length){const ne={zh:"暂无对账记录",th:"ยังไม่มีประวัติ",en:"No records yet",ja:"記録なし"}[r]||"暂无对账记录";b&&(b.textContent=ne,b.style.display=""),j&&(j.style.display="none"),G();return}b&&(b.style.display="none"),j&&(j.style.display="");const C=Math.ceil(v.length/de);pe>C&&(pe=C);const A=(pe-1)*de,O=v.slice(A,A+de),K=localStorage.getItem("mrpilot_token")||"",te='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><circle cx="8" cy="8" r="6"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',oe='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',se='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';H.innerHTML="",O.forEach(ne=>{const ce=Number(ne.formula_diff||0),fe=Math.abs(ce)<.05,ve=(ne.stmt_files||"").split(";").map(Ee=>Ee.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),ge=(ne.gl_files||"").split(";").map(Ee=>Ee.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),we=ne.created_at?String(ne.created_at).slice(0,16).replace("T"," "):"",ke=document.createElement("tr");ke.dataset.taskId=ne.id;const Le=document.createElement("td");Le.textContent=we;const Be=document.createElement("td");Be.className="glv-history-file",Be.title=ve+" + "+ge,Be.textContent=ve+" + "+ge;const Ie=document.createElement("td");Ie.className="glv-num",Ie.textContent=(ne.stmt_row_count||0)+" / "+(ne.gl_row_count||0);const Ae=document.createElement("td");Ae.className="glv-num",Ae.textContent=ne.matched_count||0;const be=document.createElement("td");be.className="glv-num",be.textContent=ne.unmatched_gl||0;const Se=document.createElement("td");Se.className="glv-num",Se.textContent=ne.unmatched_stmt||0;const Ce=document.createElement("td");Ce.className="glv-num",Ce.style.color=fe?"#059669":"#dc2626",Ce.textContent=fe?"✓":p(ce);const xe=document.createElement("td");xe.className="glv-history-actions";const je=(Ee,rt,lt,xt)=>{const Te=document.createElement("button");return Te.type="button",Te.title=rt,Te.setAttribute("aria-label",rt),lt&&(Te.className=lt),Te.innerHTML=Ee,Te.onclick=_t=>{_t.stopPropagation(),xt()},Te},Je={zh:"删除这条记录?",th:"ลบรายการนี้?",en:"Delete this record?",ja:"この記録を削除しますか?"}[r]||"删除?",We={zh:"加载",th:"โหลด",en:"Load",ja:"読込"}[r]||"加载",Ke={zh:"导出",th:"ส่งออก",en:"Export",ja:"エクスポート"}[r]||"导出",Xe={zh:"删除",th:"ลบ",en:"Delete",ja:"削除"}[r]||"删除";xe.appendChild(je(te,We,"",()=>q(ne.id,K))),xe.appendChild(je(oe,Ke,"",()=>k(ne.id))),xe.appendChild(je(se,Xe,"glv-del",async()=>{await showConfirm(Je,{danger:!0})&&(await fetch("/api/recon/bank-v2/"+ne.id,{method:"DELETE",headers:{Authorization:"Bearer "+K}}),re())})),[Le,Be,Ie,Ae,be,Se,Ce,xe].forEach(Ee=>ke.appendChild(Ee)),ke.style.cursor="pointer",ke.addEventListener("click",async Ee=>{Ee.target.closest(".glv-del")||Ee.target.closest("button")||await q(ne.id,K)}),H.appendChild(ke)}),G(),m()}function m(){const i=((o("brv2-hist-search")||{}).value||"").trim().toLowerCase(),v=o("brv2-history-tbody");v&&v.querySelectorAll("tr").forEach(b=>{b.dataset.taskId&&(b.style.display=!i||b.textContent.toLowerCase().includes(i)?"":"none")})}async function q(i,v){try{const j=await(await fetch("/api/recon/bank-v2/"+i,{headers:{Authorization:"Bearer "+v}})).json();if(!j.ok)return;s={task_id:j.task_id,...j},f=j.detail||[],l="all",document.querySelectorAll(".brv2-filter-btn").forEach(H=>H.classList.toggle("active",H.dataset.filter==="all")),X(s)}catch{}}function Z(){if(e){re();return}e=!0,J("brv2-stmt-zone","brv2-stmt-input","stmt"),J("brv2-gl-zone","brv2-gl-input","gl");const i=["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"];function v(){const A=parseFloat((o("brv2-anchor-stmt-opening")||{}).value),O=parseFloat((o("brv2-anchor-gl-opening")||{}).value),K=o("brv2-anchor-eq"),te=o("brv2-anchor-eq-val");if(!(!K||!te))if(Number.isFinite(A)&&Number.isFinite(O)){const oe=A-O;te.textContent=oe.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),K.style.display=""}else K.style.display="none"}i.forEach(A=>{const O=o(A);O&&(O.addEventListener("input",v),O.addEventListener("input",()=>{const K=O.closest(".brv2-anchor-cell");K&&K.classList.remove("is-prefilled"),u()}))}),P();const b=o("brv2-run-btn");b&&b.addEventListener("click",ie);const j=o("brv2-reset-btn");j&&j.addEventListener("click",()=>{s=null,f=[],a=[],n=[],S("stmt"),S("gl"),D(),ue(!1);const A=o("brv2-acct-select");A&&(A.style.display="none"),i.forEach(te=>{const oe=o(te);if(oe){oe.value="";const se=oe.closest&&oe.closest(".brv2-anchor-cell");se&&se.classList.remove("is-prefilled")}});const O=o("brv2-anchor-eq");O&&(O.style.display="none");const K=o("brv2-anchor-prefill-banner");K&&K.classList.remove("show")});const H=o("brv2-new-btn");H&&H.addEventListener("click",()=>{s=null,f=[],a=[],n=[],S("stmt"),S("gl"),D(),ue(!1)});const r=o("brv2-filter-tabs");r&&r.addEventListener("click",A=>{A.stopPropagation();const O=A.target.closest(".brv2-filter-btn");O&&(l=O.dataset.filter,r.querySelectorAll(".brv2-filter-btn").forEach(K=>K.classList.toggle("active",K===O)),ee())}),E(),ae();const C=o("brv2-hist-search");C&&C.addEventListener("input",m),re(),D(),window._brv2LoadHistory=re,Array.isArray(window.__i18nSubs)||(window.__i18nSubs=[]),window.__i18nSubs=window.__i18nSubs.filter(A=>A.name!=="brv2"),window.__i18nSubs.push({name:"brv2",fn:function(){D(),S("stmt"),S("gl"),s&&X(s),d()}})}window._loadBankReconV2Panel=function(i){const v=i?document.getElementById(i):null;v&&v.id!=="recon-pane-bank"&&(v.innerHTML=`<div style="padding:16px;font-size:13px;color:var(--ink-3)">
                银行对账 v2 · 请前往对账中心使用</div>`),Z()},document.addEventListener("DOMContentLoaded",()=>{o("brv2-run-btn")&&Z()}),window._bankReconV2Init=Z})();(function(){const e=document.getElementById("general-lang");if(!e)return;e.addEventListener("change",n=>{const s=n.target.value;s&&applyLang(s)});const a=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";e.value=a})();(function(){const a="pearnly_general_tz",n="pearnly_general_date_format",s="pearnly_general_number_format",l={tz:"Asia/Bangkok",date:"YYYY-MM-DD",number:"comma_dot"};function f(){const p=document.getElementById("general-tz"),w=document.getElementById("general-date"),g=document.getElementById("general-number");if(!(!p||!w||!g))try{p.value=localStorage.getItem(a)||l.tz,w.value=localStorage.getItem(n)||l.date,g.value=localStorage.getItem(s)||l.number}catch{p.value=l.tz,w.value=l.date,g.value=l.number}}async function h(){const p=document.getElementById("btn-save-general"),w=document.getElementById("general-save-msg");if(!p)return;const g=p.innerHTML;p.disabled=!0,p.innerHTML="<span>"+(t("msg-saving")||"保存中...")+"</span>",w&&(w.textContent="",w.classList.remove("error"));try{const B=(document.getElementById("general-tz")||{}).value||l.tz,S=(document.getElementById("general-date")||{}).value||l.date,I=(document.getElementById("general-number")||{}).value||l.number;try{localStorage.setItem(a,B),localStorage.setItem(n,S),localStorage.setItem(s,I)}catch{}window._pearnlyGeneral={tz:B,date_format:S,number_format:I},w&&(w.textContent=t("msg-saved")||"已保存")}catch{w&&(w.textContent=t("msg-save-failed")||"保存失败",w.classList.add("error"))}finally{p.disabled=!1,p.innerHTML=g,setTimeout(function(){w&&(w.textContent="")},3e3)}}function x(){const p=document.getElementById("btn-save-general");if(!p){setTimeout(x,200);return}p._pearnlyGenBound||(p._pearnlyGenBound=!0,p.addEventListener("click",h),f())}function o(){f();const p=document.getElementById("general-lang");if(p){const w=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";p.value=w}}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",x):x(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("settings-general",o)})();(function(){const e="mrpilot_nav_collapsed",a={ocr:"sales",history:"sales",reconcile:"sales","sales-invoices":"sales",receivables:"sales",vouchers:"expense"};function n(){try{const h=localStorage.getItem(e);return h?JSON.parse(h):{}}catch{return{}}}function s(h){try{localStorage.setItem(e,JSON.stringify(h))}catch{}}function l(){const h=n();document.querySelectorAll(".nav-collapsible").forEach(function(x){const o=x.dataset.collapsible;h[o]?x.classList.add("collapsed"):x.classList.remove("collapsed")})}function f(h){const x=n();x[h]=!x[h],s(x),l()}(function(){const x=n();let o=!1;x.sales===void 0&&(x.sales=!1,o=!0),x.expense===void 0&&(x.expense=!0,o=!0),o&&s(x)})(),l(),document.querySelectorAll(".nav-group-toggle").forEach(function(h){h.addEventListener("click",function(){f(h.dataset.toggleGroup)})}),window.expandNavGroupForRoute=function(h){const x=a[h];if(!x)return;const o=n();o[x]&&(o[x]=!1,s(o),l())}})();(function(){function e(){const a=document.getElementById("help-modal"),n=document.getElementById("help-modal-close");a&&(n&&!n.dataset.bound&&(n.addEventListener("click",function(){a.style.display="none"}),n.dataset.bound="1"),a.dataset.maskBound||(a.addEventListener("click",function(s){s.target===a&&(a.style.display="none")}),a.dataset.maskBound="1"),window._helpModalEscBound||(document.addEventListener("keydown",function(s){s.key==="Escape"&&a.style.display==="flex"&&(a.style.display="none")}),window._helpModalEscBound=!0))}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",e):e()})();(function(){const e={line:"line",folder:"folder",gmail:"email",erp:"erp",alert:"alert"};document.addEventListener("click",function(a){const n=a.target.closest(".int-btn-configure");if(!n)return;const s=n.closest(".integration-row"),l=s?s.dataset.intAnchor:null;if(l&&e[l]){const f=s.querySelector(".int-name"),h=f?(f.textContent||f.innerText||"").trim():"配置";typeof window.openIntegrationDrawer=="function"&&window.openIntegrationDrawer(e[l],h)}})})();let _e=[];window._erpEndpoints=_e;let Oe=null,Me={key:"all",val:""},ye=new Set;async function He(e){const a=document.getElementById("erp-logs-list");if(a){e||(a.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`),it();try{const n=new URLSearchParams({limit:"30"});Me.key==="status"&&n.set("status",Me.val),Me.key==="trigger"&&n.set("trigger",Me.val),Me.key==="adapter"&&n.set("adapter",Me.val);const s=await fetch(`/api/erp/logs?${n}`,{headers:{Authorization:"Bearer "+token}});if(!s.ok){a.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const f=(await s.json()).items||[];if(window._erpLogPollTimer&&(clearTimeout(window._erpLogPollTimer),window._erpLogPollTimer=null),f.some(function(p){return p.status==="pending"})&&(window._erpLogPollTimer=setTimeout(function(){He(!0)},4e3)),f.length===0){a.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-empty"))}</div>`;return}const x='<div class="erp-log-row erp-log-row-header" data-log-header>'+(f.filter(function(p){var w=p.status==="failed"&&p.next_retry_at&&new Date(p.next_retry_at).getTime()>Date.now()-6e4;return!w}).map(function(p){return p.id}).length>0?`<input type="checkbox" class="erp-log-cb erp-log-cb-all" data-log-select-all title="${escapeHtml(t("erp-log-select-all-tip"))}">`:'<span class="erp-log-cb-spacer"></span>')+`<span class="log-time">${escapeHtml(t("erp-log-col-time"))}</span><span class="log-status">${escapeHtml(t("erp-log-col-status"))}</span><span class="log-tag-header">${escapeHtml(t("erp-log-col-trigger"))}</span><span class="log-invoice">${escapeHtml(t("erp-log-col-invoice"))}</span><span class="log-workspace">${escapeHtml(t("erp-log-col-workspace"))}</span><span class="log-client">${escapeHtml(t("erp-log-col-client"))}</span><span class="log-seller">${escapeHtml(t("erp-log-col-seller"))}</span><span class="log-erp">${escapeHtml(t("erp-log-col-erp"))}</span><span class="log-doc">${escapeHtml(t("erp-log-col-doc"))}</span><span class="log-http">${escapeHtml(t("erp-log-col-http"))}</span><span class="log-elapsed">${escapeHtml(t("erp-log-col-elapsed"))}</span><span class="log-actions"></span></div>`;a.innerHTML=x+f.map(p=>{const w=new Date(p.created_at),g=`${String(w.getMonth()+1).padStart(2,"0")}-${String(w.getDate()).padStart(2,"0")} ${String(w.getHours()).padStart(2,"0")}:${String(w.getMinutes()).padStart(2,"0")}`,B=p.status==="failed"&&p.next_retry_at&&new Date(p.next_retry_at).getTime()>Date.now()-6e4;let S,I,U;p.status==="pending"?(S="retrying",I="⟳",U=t("erp-status-pending")):p.status==="success"?(S="ok",I="✓",U=t("erp-status-success")):p.status==="skipped_dup"?(S="skipped",I="⏭",U=t("erp-status-skipped")):B?(S="retrying",I="↻",U=t("erp-status-retrying")):(S="fail",I="✗",U=t("erp-status-failed"));let N;p.trigger==="auto"?N=`<span class="log-tag auto">${escapeHtml(t("log-tag-auto"))}</span>`:p.trigger==="retry"?N=`<span class="log-tag retry">${escapeHtml(t("log-tag-retry"))}</span>`:N=`<span class="log-tag manual">${escapeHtml(t("log-tag-manual"))}</span>`;let M="";const L=p.retry_count||0,z=p.max_retries||3;if(B){const J=new Date(p.next_retry_at).getTime()-Date.now(),F=Math.max(0,Math.round(J/6e4)),Q=F<=0?t("erp-retry-next-soon"):t("erp-retry-next-min",{n:F});M=`${t("erp-retry-attempt",{n:L,max:z})} · ${Q}`}else p.status==="failed"&&L>=z&&!p.next_retry_at&&(M=t("erp-retry-exhausted",{n:L}));const V=p.status==="failed"&&!B?`<button class="log-retry-btn" data-log-retry="${escapeHtml(p.id)}" title="${escapeHtml(t("log-retry-title"))}">↻</button>`:"",W=!B,P=ye.has(p.id)?"checked":"",u=W?`<input type="checkbox" class="erp-log-cb" data-log-cb="${escapeHtml(p.id)}" ${P}>`:'<span class="erp-log-cb-spacer"></span>',c=(p.ocr_buyer_name||"").trim()||(p.client_name||"").trim(),y=c?`<span class="log-client" title="${escapeHtml(c)}">${escapeHtml(c.substring(0,18))}</span>`:`<span class="log-client log-client-empty" title="${escapeHtml(t("erp-log-client-unassigned-tip"))}">${escapeHtml(t("erp-log-client-unassigned"))}</span>`,$=p.workspace_name?`<span class="log-workspace">${escapeHtml((p.workspace_name||"").substring(0,16))}</span>`:`<span class="log-workspace log-workspace-unresolved" title="${escapeHtml(t("erp-log-ws-unresolved-tip"))}">${escapeHtml(t("erp-log-ws-unresolved"))}</span>`,T=p.endpoint_name?`<span class="log-erp">${escapeHtml((p.endpoint_name||"").substring(0,14))}</span>`:`<span class="log-erp log-erp-deleted">${escapeHtml(t("erp-log-endpoint-deleted"))}</span>`,_=(p.external_doc_no||"").trim(),E=(p.external_url||"").trim();let D;return E?D=`<span class="log-doc"><a href="${escapeHtml(E)}" target="_blank" rel="noopener" class="log-doc-open" title="${escapeHtml(_||"")}">${escapeHtml(t("erp-log-doc-open"))}</a></span>`:_?D=`<span class="log-doc log-doc-copy" data-copy-doc="${escapeHtml(_)}" title="${escapeHtml(t("erp-log-doc-copy-tip"))}">${escapeHtml(_.substring(0,18))}</span>`:p.status==="success"?D=`<span class="log-doc log-doc-missing" title="${escapeHtml(t("erp-log-doc-missing-tip"))}">${escapeHtml(t("erp-log-doc-missing"))}</span>`:D='<span class="log-doc log-doc-empty">-</span>',`
                <div class="erp-log-row ${S}" data-log-detail="${escapeHtml(p.id)}">
                    ${u}
                    <span class="log-time">${g}</span>
                    <span class="log-status" title="${escapeHtml(U+(M?" · "+M:""))}">${I}</span>
                    ${N}
                    <span class="log-invoice">${escapeHtml(p.invoice_no||"-")}</span>
                    ${$}
                    ${y}
                    <span class="log-seller">${escapeHtml((p.seller_name||"").substring(0,20))}</span>
                    ${T}
                    ${D}
                    <span class="log-http">HTTP ${p.http_status||"-"}</span>
                    <span class="log-elapsed">${p.elapsed_ms}ms</span>
                    <span class="log-actions">${V}</span>
                </div>
            `}).join("");const o=new Set(f.map(p=>p.id));for(const p of Array.from(ye))o.has(p)||ye.delete(p);Ne()}catch(n){console.error("load erp logs failed",n),a.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}function Ne(){const e=document.getElementById("erp-logs-batch-bar"),a=document.getElementById("erp-logs-batch-count"),n=document.querySelector("[data-log-select-all]");if(n){const f=document.querySelectorAll("[data-log-cb]").length,h=ye.size;h===0?(n.checked=!1,n.indeterminate=!1):h>=f?(n.checked=!0,n.indeterminate=!1):(n.checked=!1,n.indeterminate=!0)}if(!e||!a)return;const s=ye.size;if(s===0){e.style.display="none";return}e.style.display="",a.textContent=t("erp-batch-selected",{n:s})}async function vt(){console.info("[ErpBatch] retry triggered · selected=",ye.size);const e=Array.from(ye);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-confirm",{n:e.length})))try{const n=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!n.ok){showToast(t("erp-logs-error"),"error");return}const s=await n.json(),l=t("erp-batch-result",{ok:s.succeeded||0,fail:s.failed||0,skip:s.skipped||0}),f=s.failed&&s.failed>0?"warn":"success";showToast(l,f),ye.clear(),He()}catch(n){console.error("batch retry failed",n),showToast(t("erp-logs-error"),"error")}}async function Tt(){console.info("[ErpBatch] delete triggered · selected=",ye.size);const e=Array.from(ye);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-delete-confirm",{n:e.length}),{danger:!0}))try{const s=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!s.ok){showToast(t("erp-logs-error"),"error");return}const l=await s.json();e.forEach(function(f){var h=document.querySelector('[data-log-detail="'+f+'"]');h&&h.remove()});var n=document.getElementById("erp-logs-batch-bar");n&&(n.style.display="none"),showToast(t("erp-batch-delete-result",{n:l.deleted||0,skip:l.skipped||0}),l.deleted>0?"success":"warn"),ye.clear(),setTimeout(He,500)}catch(s){console.error("batch delete failed",s),showToast(t("erp-logs-error"),"error")}}(function(){function a(){var n=document.getElementById("btn-erp-batch-retry"),s=document.getElementById("btn-erp-batch-delete"),l=document.getElementById("btn-erp-batch-clear");n&&!n.dataset.boundDirect&&(n.addEventListener("click",function(f){f.preventDefault(),f.stopPropagation(),vt()}),n.dataset.boundDirect="1"),s&&!s.dataset.boundDirect&&(s.addEventListener("click",function(f){f.preventDefault(),f.stopPropagation(),Tt()}),s.dataset.boundDirect="1"),l&&!l.dataset.boundDirect&&(l.addEventListener("click",function(f){f.preventDefault(),f.stopPropagation(),ye.clear(),document.querySelectorAll(".erp-log-cb").forEach(function(h){h.checked=!1}),Ne()}),l.dataset.boundDirect="1")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",a):a(),setTimeout(a,2e3),setTimeout(a,5e3),window._bindErpBatchButtons=a})();async function ot(e){if(e=(e||"").trim(),!!e)try{await navigator.clipboard.writeText(e),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{try{const n=document.createElement("textarea");n.value=e,n.style.position="fixed",n.style.opacity="0",document.body.appendChild(n),n.select(),document.execCommand("copy"),n.remove(),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{showToast(t("erp-doc-copy-fail"),"error")}}}async function mt(e){const a=document.createElement("div");a.className="log-detail-modal",a.innerHTML=`
        <div class="log-detail-box">
            <div class="log-detail-loading">${escapeHtml(t("log-detail-loading"))}</div>
        </div>
    `,document.body.appendChild(a),a.addEventListener("click",async n=>{if(n.target===a||n.target.classList.contains("log-detail-close")){a.remove();return}const s=n.target.closest("[data-receipt-copy]");if(s){ot(s.dataset.receiptCopy);return}const l=n.target.closest("[data-receipt-action]");if(l){const f=l.dataset.receiptAction;f==="retry"?st(l.dataset.logId):f==="exceptions"?typeof routeTo=="function"&&routeTo("exceptions"):f==="mappings"&&typeof routeTo=="function"&&routeTo("integrations"),a.remove();return}});try{const n=await fetch(`/api/erp/logs/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!n.ok){a.remove();return}const s=await n.json(),l=_e.find(T=>T.id===s.endpoint_id),f=s.endpoint_name||(l?l.name:s.endpoint_id?t("erp-log-endpoint-deleted"):"-"),h=(s.endpoint_adapter||l&&l.adapter||"").toLowerCase(),x=new Date(s.created_at).toLocaleString(),o=s.trigger==="auto"?t("log-tag-auto"):s.trigger==="retry"?t("log-tag-retry"):t("log-tag-manual"),p=s.request_body?JSON.stringify(s.request_body,null,2):t("erp-receipt-no-tech"),w=s.response_body||t("erp-receipt-no-tech"),g=s.status==="success";let B=typeof w=="string"?w:JSON.stringify(w,null,2);if(g)try{const T=typeof s.response_body=="string"?JSON.parse(s.response_body):s.response_body||{},_=T.row_count||(Array.isArray(T.imported_rows)?T.imported_rows.length:0);_>0&&(B=t("log-push-rows").replace("{n}",String(_)))}catch{}const S=(s.external_doc_no||"").trim(),I=(s.external_url||"").trim(),U=(s.external_doc_hint||"").trim(),N=(s.ocr_buyer_name||"").trim()||s.client_name||"-",M=s.seller_name||"-";let L="-";const z=Number(s.total_amount);s.total_amount!=null&&s.total_amount!==""&&!isNaN(z)&&(L=z.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}));const V=g?t("erp-receipt-title-ok"):t("erp-receipt-title-fail"),W=g?"✓":"✗",P=[],u=(T,_)=>{P.push(`
                <div class="erp-receipt-row">
                    <span class="erp-receipt-key">${escapeHtml(T)}</span>
                    <span class="erp-receipt-val">${_}</span>
                </div>`)};if(u(t("erp-receipt-invoice-no"),`<strong>${escapeHtml(s.invoice_no||"-")}</strong>`),u(t("erp-receipt-erp-name"),escapeHtml(f)),g){let T;S?T=`<strong class="erp-receipt-docno">${escapeHtml(S)}</strong><button class="erp-receipt-copy-btn" type="button" data-receipt-copy="${escapeHtml(S)}" title="${escapeHtml(t("erp-doc-copy-tip"))}">${escapeHtml(t("erp-receipt-copy-btn"))}</button>`:T=`<span class="erp-receipt-docno-missing">${escapeHtml(t("erp-log-doc-missing"))}</span>`,u(t("erp-receipt-doc-no"),T)}u(t("erp-receipt-client"),escapeHtml(N)),u(t("erp-receipt-seller"),escapeHtml(M)),g&&u(t("erp-receipt-amount"),escapeHtml(L)),u(t("erp-receipt-time"),escapeHtml(x)),u(t("erp-receipt-elapsed"),escapeHtml((s.elapsed_ms!=null?s.elapsed_ms:"-")+"ms"));let c="";g&&I?c=`<a class="erp-receipt-primary-btn" href="${escapeHtml(I)}" target="_blank" rel="noopener">${escapeHtml(t("erp-receipt-open-erp"))}</a>`:g&&S&&(c=`<button class="erp-receipt-primary-btn" type="button" data-receipt-copy="${escapeHtml(S)}">${escapeHtml(t("erp-receipt-copy-docno"))}</button>`);let y="";if(g&&S&&U){const T="erp-receipt-hint-"+U,_=t(T);_&&_!==T&&(y=`<div class="erp-receipt-hint"><svg class="erp-receipt-hint-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span>${escapeHtml(_)}</span></div>`)}let $="";if(!g){const T=(s.error_msg||"").match(/ERR_[A-Z0-9_]+/),_=T?T[0]:"",E=typeof currentLang=="string"&&currentLang||window._currentLang||"th",J=s.error_friendly&&s.error_friendly[E]||(s.error_msg?humanizeError(s.error_msg):t("erp-receipt-no-error")),F=/ERR_NO_CUSTOMER_MAPPING|ERR_NO_CLIENT|ERR_NO_SEED_CUSTOMER|ERR_NO_SEED_PRODUCT/.test(s.error_msg||""),Q=!!(s.history_id&&s.endpoint_id),ie=[];ie.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="exceptions">${escapeHtml(t("erp-receipt-act-exceptions"))}</button>`),F&&ie.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="mappings">${escapeHtml(t("erp-receipt-act-mapping"))}</button>`),Q&&ie.push(`<button class="erp-receipt-action-btn primary" type="button" data-receipt-action="retry" data-log-id="${escapeHtml(s.id)}">${escapeHtml(t("erp-receipt-act-retry"))}</button>`),$=`
                <div class="erp-receipt-fail-reason-label">${escapeHtml(t("erp-receipt-fail-reason"))}</div>
                <div class="erp-receipt-fail-box">
                    ${_?`<div class="erp-receipt-errcode">${escapeHtml(_)}</div>`:""}
                    <div class="erp-receipt-friendly">${escapeHtml(J)}</div>
                </div>
                <div class="erp-receipt-actions-label">${escapeHtml(t("erp-receipt-suggest"))}</div>
                <div class="erp-receipt-actions">${ie.join("")}</div>`}a.querySelector(".log-detail-box").innerHTML=`
            <div class="log-detail-head">
                <div class="log-detail-title">
                    <span class="log-detail-status-icon ${g?"ok":"fail"}">${W}</span>
                    ${escapeHtml(V)}
                    <span class="log-tag ${s.trigger}">${escapeHtml(o)}</span>
                </div>
                <button class="log-detail-close" type="button">✕</button>
            </div>

            <div class="erp-receipt-body">
                ${P.join("")}
            </div>

            ${y}
            ${c?`<div class="erp-receipt-primary-wrap">${c}</div>`:""}
            ${$}

            <details class="log-detail-collapsible">
                <summary>${escapeHtml(t("erp-receipt-tech-toggle"))}</summary>
                <div class="log-detail-meta" style="margin-top:8px;">
                    <span>HTTP ${s.http_status||"-"}</span>
                    <span>${s.elapsed_ms}ms</span>
                    <span>${escapeHtml(t("log-detail-attempt",{n:s.attempt||1}))}</span>
                </div>
                <div class="log-detail-section" style="margin-top:12px;">
                    <div class="log-detail-label">${escapeHtml(t("log-detail-request-human"))}</div>
                    <pre>${escapeHtml(p)}</pre>
                </div>
                <div class="log-detail-section">
                    <div class="log-detail-label">${escapeHtml(t("log-detail-response-human"))}</div>
                    <pre>${escapeHtml(B)}</pre>
                </div>
            </details>
        `}catch(n){console.error(n),a.remove()}}async function st(e){try{const a=await fetch(`/api/erp/logs/${encodeURIComponent(e)}/retry`,{method:"POST",headers:{Authorization:"Bearer "+token}}),n=await a.json().catch(()=>({}));a.ok&&n.ok?showToast(t("log-retry-ok"),"success"):showToast(t("log-retry-fail")+" · HTTP "+(n.http_status||a.status),"error"),He(),Fe()}catch{showToast(t("log-retry-fail"),"error")}}async function Fe(){try{const e=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(e.status===401){localStorage.removeItem("mrpilot_token");const n=await e.json().catch(()=>({}));if((typeof n.detail=="string"?n.detail:n.detail&&n.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}_e=(await e.json()).items||[],window._erpEndpoints=_e,ht()}catch(e){console.error("load endpoints failed",e)}}window._refreshErpEndpointsCache=function(){return Fe()};async function it(){const e=document.getElementById("erp-today-stats");if(e){e.innerHTML="";try{const a=await fetch("/api/erp/stats/today",{headers:{Authorization:"Bearer "+token}});if(!a.ok)return;const n=await a.json(),s=n.total||0,l=n.success||0,f=n.failed||0,h=n.auto_cnt||0;if(s===0){e.innerHTML=`<span class="erp-today-empty">${escapeHtml(t("erp-today-none"))}</span>`;return}const x=[];x.push(`<span class="erp-today-item"><strong>${s}</strong> ${escapeHtml(t("erp-today-total"))}</span>`),l>0&&x.push(`<span class="erp-today-item ok"><strong>${l}</strong> ${escapeHtml(t("erp-today-success"))}</span>`),f>0&&x.push(`<span class="erp-today-item fail"><strong>${f}</strong> ${escapeHtml(t("erp-today-failed"))}</span>`),h>0&&x.push(`<span class="erp-today-item auto"><strong>${h}</strong> ${escapeHtml(t("erp-today-auto"))}</span>`),e.innerHTML=x.join("")}catch(a){console.warn("loadErpTodayStats failed",a)}}}function ht(){const e=document.getElementById("erp-endpoints-list"),a=document.getElementById("erp-status-summary"),n=document.getElementById("btn-add-endpoint");if(!e){console.warn("erp-endpoints-list 容器不存在");return}if(n&&_userInfo){const l=_userInfo.endpoints_limit;l!==-1&&_e.length>=l?(n.disabled=!0,n.title=t("ep-limit-reached",{limit:l}),n.classList.add("btn-disabled-plus")):(n.disabled=!1,n.title="",n.classList.remove("btn-disabled-plus"))}if(_e.length===0){e.innerHTML=`<div class="erp-empty">${escapeHtml(t("ep-list-empty"))}</div>`,a&&(a.textContent=t("auto-status-none"),a.className="auto-status-pill none");return}const s=_e.some(l=>l.auto_push&&l.enabled);if(a&&(a.textContent=t("auto-status-active",{n:_e.length,mode:s?t("auto-status-on"):t("auto-status-off")}),a.className="auto-status-pill "+(s?"active":"ready")),it(),e.innerHTML=_e.map(l=>{const f=l.config||{},h=escapeHtml(f.url||"");f._token_set;const x=l.enabled!==!1,o=[];l.is_default&&o.push(`<span class="ep-badge default">${escapeHtml(t("ep-default"))}</span>`),l.auto_push&&o.push(`<span class="ep-badge auto">${escapeHtml(t("ep-auto-push-on"))}</span>`),x||o.push(`<span class="ep-badge disabled">${escapeHtml(t("ep-disabled"))}</span>`);const p=[];return l.success_count>0&&p.push(`<span class="ep-stat ok">${escapeHtml(t("ep-success",{n:l.success_count}))}</span>`),l.failure_count>0&&p.push(`<span class="ep-stat fail">${escapeHtml(t("ep-failure",{n:l.failure_count}))}</span>`),`
            <div class="erp-endpoint" data-ep-id="${escapeHtml(l.id)}">
                <div class="ep-main">
                    <div class="ep-title-row">
                        <div class="ep-name">${escapeHtml(l.name)}</div>
                        <div class="ep-badges">${o.join("")}</div>
                    </div>
                    <div class="ep-url">${h||"-"}</div>
                    <div class="ep-stats">${p.join(" · ")}</div>
                </div>
                <div class="ep-actions">
                    <button class="btn btn-ghost btn-small" data-ep-edit="${escapeHtml(l.id)}">
                        <span>${escapeHtml(t("ep-edit"))}</span>
                    </button>
                    <button class="btn btn-ghost btn-small btn-danger" data-ep-del="${escapeHtml(l.id)}">
                        <span>${escapeHtml(t("ep-delete"))}</span>
                    </button>
                </div>
            </div>
        `}).join(""),_userInfo&&_userInfo.endpoints_limit!==-1){const l=_e.length,f=_userInfo.endpoints_limit,h=_userInfo.plan,x=document.createElement("div");x.className="erp-limit-hint",h==="free"?x.innerHTML=`${escapeHtml(t("ep-free-limit-hint",{used:l,limit:f}))} <a data-upgrade="plus">${escapeHtml(t("upgrade-to-plus"))}</a>`:x.textContent=t("ep-plus-limit-hint",{used:l,limit:f}),e.appendChild(x)}}function Qe(e){Oe=e||null;const a=document.getElementById("endpoint-modal"),n=document.getElementById("endpoint-modal-title");n.textContent=e?t("ep-modal-title-edit"):t("ep-modal-title-new");const s=document.getElementById("ep-name"),l=document.getElementById("ep-url"),f=document.getElementById("ep-token"),h=document.getElementById("ep-is-default"),x=document.getElementById("ep-auto-push"),o=document.getElementById("ep-test-result");o.style.display="none",o.textContent="";const p=document.getElementById("ep-save-error");if(p&&p.remove(),e){const g=_e.find(B=>B.id===e);if(!g)return;s.value=g.name||"",l.value=(g.config||{}).url||"",f.value=(g.config||{})._token_set&&g.config.token||"",f.placeholder=(g.config||{})._token_set?"（已保存 · 留空保持不变）":t("ep-token-ph"),h.checked=!!g.is_default,x.checked=!!g.auto_push}else s.value="",l.value="",f.value="",f.placeholder=t("ep-token-ph"),h.checked=_e.length===0,x.checked=!0;const w=x.closest(".form-switch-row");if(x.disabled=!1,w){w.classList.remove("disabled-plus"),w.title="",w.style.cursor="",w.onclick=null;const g=w.querySelector(".plus-badge");g&&g.remove()}a.style.display="",setTimeout(()=>s.focus(),50)}function Ge(){document.getElementById("endpoint-modal").style.display="none",Oe=null;const e=document.getElementById("ep-save-error");e&&e.remove()}function gt(e){if(!e)return"";let a=e.trim();const n=a.search(/\s/);return n>=0&&(a=a.slice(0,n)),a}function bt(){const e=document.getElementById("ep-name").value.trim(),a=gt(document.getElementById("ep-url").value),n=document.getElementById("ep-token").value,s=document.getElementById("ep-is-default").checked,l=document.getElementById("ep-auto-push").checked,f={url:a};return n&&(f.token=n),{name:e,url:a,tokenVal:n,isDefault:s,autoPush:l,config:f}}async function yt(){const{url:e,config:a}=bt(),n=document.getElementById("ep-test-result");if(!e){n.style.display="",n.className="form-test-result fail",n.textContent=t("ep-required");return}n.style.display="",n.className="form-test-result running",n.textContent=t("ep-test-running");try{const l=await(await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({adapter:"webhook",config:a})})).json();l.success?(n.className="form-test-result ok",n.textContent=t("ep-test-ok",{status:l.http_status,ms:l.elapsed_ms})):(n.className="form-test-result fail",n.textContent=t("ep-test-fail",{err:l.error_msg||"unknown"}))}catch(s){n.className="form-test-result fail",n.textContent=t("ep-test-fail",{err:s.message})}}async function wt(){const e=bt(),a=document.getElementById("ep-save-error");if(a&&(a.style.display="none"),!e.name||!e.url){dt(t("ep-required"));return}const n={name:e.name,adapter:"webhook",config:e.config,is_default:e.isDefault,auto_push:e.autoPush},s=document.getElementById("btn-ep-save"),l=s.innerHTML;s.disabled=!0,s.classList.add("loading");try{let f;if(Oe?f=await fetch(`/api/erp/endpoints/${encodeURIComponent(Oe)}`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(n)}):f=await fetch("/api/erp/endpoints",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(n)}),!f.ok){const x=(await f.json().catch(()=>({}))).detail||`HTTP ${f.status}`;throw new Error(typeof x=="string"?x:JSON.stringify(x))}Ge(),showToast(t("ep-save-ok")),Fe()}catch(f){dt(`${t("ep-save-fail")} · ${f.message||"unknown"}`)}finally{s.disabled=!1,s.classList.remove("loading"),s.innerHTML=l}}function dt(e){let a=document.getElementById("ep-save-error");if(!a){const n=document.querySelector("#endpoint-modal .modal-foot");if(!n)return;a=document.createElement("div"),a.id="ep-save-error",a.className="ep-inline-error",n.parentNode.insertBefore(a,n)}a.textContent=e,a.style.display=""}async function kt(e){const a=_e.find(s=>s.id===e);if(!(!a||!await showConfirm(t("ep-delete-confirm",{name:a.name}),{danger:!0})))try{if(!(await fetch(`/api/erp/endpoints/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showToast(t("ep-delete-ok")),Fe()}catch{showToast(t("ep-save-fail"),"fail")}}(function(){document.getElementById("btn-add-endpoint").addEventListener("click",()=>Qe(null)),document.getElementById("endpoint-modal-close").addEventListener("click",Ge),document.getElementById("btn-ep-cancel").addEventListener("click",Ge),document.getElementById("btn-ep-test").addEventListener("click",yt),document.getElementById("btn-ep-save").addEventListener("click",wt),document.getElementById("ep-url").addEventListener("blur",a=>{const n=gt(a.target.value);n!==a.target.value.trim()&&(a.target.value=n)}),document.addEventListener("click",a=>{const n=a.target.closest("[data-ep-edit]"),s=a.target.closest("[data-ep-del]");n&&Qe(n.dataset.epEdit),s&&kt(s.dataset.epDel);const l=a.target.closest("[data-log-retry]");if(l){a.stopPropagation(),st(l.dataset.logRetry);return}const f=a.target.closest("[data-log-cb]");if(f){a.stopPropagation();const w=f.dataset.logCb;f.checked?ye.add(w):ye.delete(w),Ne();return}const h=a.target.closest("[data-log-select-all]");if(h){a.stopPropagation();const w=h.checked;document.querySelectorAll("[data-log-cb]").forEach(function(B){B.checked=w;const S=B.dataset.logCb;w?ye.add(S):ye.delete(S)}),Ne();return}if(a.target.closest("#btn-erp-batch-retry")){a.stopPropagation(),vt();return}if(a.target.closest("#btn-erp-batch-clear")){a.stopPropagation(),ye.clear(),document.querySelectorAll(".erp-log-cb").forEach(w=>{w.checked=!1}),Ne();return}const x=a.target.closest("[data-log-detail]");if(x){if(a.target.closest("[data-log-cb]"))return;const w=a.target.closest("[data-copy-doc]");if(w){a.stopPropagation(),ot(w.dataset.copyDoc);return}if(a.target.closest(".log-doc-open"))return;mt(x.dataset.logDetail);return}const o=a.target.closest(".chip-filter");if(o){document.querySelectorAll("#erp-logs-filters .chip-filter").forEach(w=>w.classList.remove("active")),o.classList.add("active"),Me={key:o.dataset.filterKey,val:o.dataset.filterVal},He();return}if(a.target.closest("#btn-refresh-logs")){const w=a.target.closest("#btn-refresh-logs");w.classList.add("spinning"),setTimeout(()=>w.classList.remove("spinning"),600),He();return}const p=a.target.closest(".auto-nav-item");if(p&&p.dataset.autoTab){switchAutomationTab(p.dataset.autoTab);return}})})();window.loadErpLogs=He;window.loadErpEndpoints=Fe;window.loadErpTodayStats=it;window.renderErpEndpointsList=ht;window.showLogDetail=mt;window.retryPushLog=st;window.copyErpDocNo=ot;window.openEndpointModal=Qe;window.closeEndpointModal=Ge;window.saveEndpoint=wt;window.deleteEndpoint=kt;window.testEndpointConnection=yt;(function(){let e=null,a=!1;function n(){if(e)return e;const x=document.createElement("div");x.id="line-email-modal",x.style.cssText="position:fixed;inset:0;background:rgba(10,14,39,0.85);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;",x.innerHTML=`
            <div style="background:#fff;border-radius:16px;padding:28px 24px;max-width:420px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,0.3);">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#06C755" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="2" y="4" width="20" height="16" rx="2"/>
                        <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
                    </svg>
                    <h3 id="line-email-title-h" style="font-size:18px;font-weight:600;color:#0f172a;margin:0;"></h3>
                </div>
                <p id="line-email-sub-p" style="font-size:14px;color:#64748b;line-height:1.55;margin:0 0 18px;"></p>
                <input id="line-email-input" type="email" autocomplete="email" style="width:100%;padding:12px 14px;border:1px solid #e5e7eb;border-radius:10px;font-size:15px;outline:none;font-family:inherit;" />
                <div id="line-email-err" style="color:#dc2626;font-size:13px;margin-top:8px;min-height:18px;"></div>
                <button id="line-email-submit-btn" type="button" style="width:100%;margin-top:14px;padding:13px 16px;background:#111111;color:#fff;border:none;border-radius:10px;font-size:15px;font-weight:600;cursor:pointer;font-family:inherit;"></button>
            </div>
        `,document.body.appendChild(x),e=x;const o=x.querySelector("#line-email-input"),p=x.querySelector("#line-email-submit-btn"),w=x.querySelector("#line-email-err");async function g(){w.textContent="";const B=(o.value||"").trim().toLowerCase();if(!B||B.indexOf("@")<0||B.split("@")[1].indexOf(".")<0){w.textContent=t("line-email-err-invalid");return}p.disabled=!0,p.style.opacity="0.6";try{const S=await fetch("/api/me/line_complete_email",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},body:JSON.stringify({email:B})});if(!S.ok)throw new Error("http_"+S.status);const I=await S.json();I.token&&localStorage.setItem("mrpilot_token",I.token),typeof showToast=="function"&&showToast(I.merged?t("line-email-merged-toast"):t("line-email-saved-toast"),"success"),setTimeout(function(){window.location.reload()},600)}catch{w.textContent=t("line-email-err-failed"),p.disabled=!1,p.style.opacity="1"}}return p.addEventListener("click",g),o.addEventListener("keydown",function(B){B.key==="Enter"&&g()}),x}function s(){if(!e)return;const x=e.querySelector("#line-email-title-h"),o=e.querySelector("#line-email-sub-p"),p=e.querySelector("#line-email-input"),w=e.querySelector("#line-email-submit-btn");x&&(x.textContent=t("line-email-title")),o&&(o.textContent=t("line-email-sub")),p&&(p.placeholder=t("line-email-placeholder")),w&&(w.textContent=t("line-email-submit"))}function l(){n(),s(),e.style.display="flex",a=!0;const x=e.querySelector("#line-email-input");x&&setTimeout(function(){x.focus()},100)}async function f(){const x=localStorage.getItem("mrpilot_token");if(x)try{const o=await fetch("/api/me/needs_email",{headers:{Authorization:"Bearer "+x}});if(!o.ok)return;const p=await o.json();p&&p.needs_email&&l()}catch{}}function h(){setTimeout(f,800)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",h):h(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("line-email-modal",function(){a&&s()})})();(function(){function e(x){let o=0;return x.length>=8&&o++,x.length>=12&&o++,/[a-zA-Z]/.test(x)&&/\d/.test(x)&&o++,/[^a-zA-Z0-9]/.test(x)&&o++,Math.min(3,o)}function a(x,o){const p=document.getElementById("cpw-msg");p&&(p.textContent=x,p.className="cpw-msg "+(o||""))}function n(x){return typeof t=="function"?t(x):x}function s(){const x=["cpw-old","cpw-new","cpw-confirm"];x.forEach(B=>{const S=document.getElementById(B);S&&(S.value="",S.setAttribute("readonly","readonly"),S.addEventListener("focus",function(){this.removeAttribute("readonly")}))}),document.querySelectorAll('.settings-nav-item[data-settings-tab="account"]').forEach(B=>{B.addEventListener("click",()=>{setTimeout(()=>{x.forEach(I=>{const U=document.getElementById(I);U&&(U.value="",U.setAttribute("readonly","readonly"))});const S=document.getElementById("cpw-strength-bar");S&&(S.style.width="0%",S.className="cpw-strength-bar"),a("","")},100)})}),document.querySelectorAll(".cpw-eye").forEach(B=>{B.addEventListener("click",()=>{const S=B.dataset.target,I=document.getElementById(S);I&&(I.type=I.type==="password"?"text":"password")})});const o=document.getElementById("cpw-new"),p=document.getElementById("cpw-strength-bar");o&&p&&o.addEventListener("input",()=>{const B=e(o.value),S=["0%","33%","66%","100%"],I=["","weak","medium","strong"];p.style.width=S[B],p.className="cpw-strength-bar "+I[B]});const w=document.getElementById("cpw-forgot-link");w&&w.addEventListener("click",()=>l());const g=document.getElementById("btn-change-pw");g&&g.addEventListener("click",async()=>{const B=document.getElementById("cpw-old"),S=document.getElementById("cpw-new"),I=document.getElementById("cpw-confirm");if(!B||!S||!I)return;const U=B.value,N=S.value,M=I.value;if(!U||!N||!M){a(n("settings-change-pw-empty"),"error");return}if(N.length<8){a(n("settings-change-pw-too-short"),"error");return}if(!(/[a-zA-Z]/.test(N)&&/\d/.test(N))){a(n("settings-change-pw-too-weak"),"error");return}if(N!==M){a(n("settings-change-pw-mismatch"),"error");return}g.disabled=!0;const L=g.textContent;g.textContent=n("settings-change-pw-submitting"),a("","");try{const z=localStorage.getItem("mrpilot_token"),V=await fetch("/api/me/change_password",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+z},body:JSON.stringify({old_password:U,new_password:N})}),W=await V.json().catch(()=>({}));if(V.ok&&W.ok)a(n("settings-change-pw-success"),"success"),typeof showToast=="function"&&showToast(n("settings-change-pw-success"),"success"),B.value="",S.value="",I.value="",p&&(p.style.width="0%",p.className="cpw-strength-bar");else{const P=W.detail||"";let u=n("settings-change-pw-success");P==="wrong_old_password"?u=n("settings-change-pw-wrong-old"):P==="password_too_short"?u=n("settings-change-pw-too-short"):P==="password_too_weak"?u=n("settings-change-pw-too-weak"):u=P||"Error",a(u,"error")}}catch(z){console.error("change_password",z),a("Network error","error")}finally{g.disabled=!1,g.textContent=L}})}function l(){const x=window._userInfo||(typeof _userInfo<"u"?_userInfo:null),o=x&&x.username?x.username:"",p=f(o);let w=document.getElementById("cpw-forgot-overlay");w&&w.remove(),w=document.createElement("div"),w.id="cpw-forgot-overlay",w.className="cpw-forgot-overlay",w.innerHTML=`
            <div class="cpw-forgot-modal">
                <div class="cpw-forgot-head">
                    <div class="cpw-forgot-title">${h(n("cpw-forgot-title"))}</div>
                    <button class="cpw-forgot-close" id="cpw-forgot-close" aria-label="close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="cpw-forgot-body">
                    <p class="cpw-forgot-desc">${h(n("cpw-forgot-desc"))}</p>
                    <div class="cpw-forgot-email">${h(p)}</div>
                    <p class="cpw-forgot-tip">${h(n("cpw-forgot-tip"))}</p>
                    <div class="cpw-forgot-msg" id="cpw-forgot-msg"></div>
                </div>
                <div class="cpw-forgot-foot">
                    <button class="btn btn-ghost" id="cpw-forgot-cancel">${h(n("cpw-forgot-cancel"))}</button>
                    <button class="btn btn-primary" id="cpw-forgot-send">${h(n("cpw-forgot-send"))}</button>
                </div>
            </div>
        `,document.body.appendChild(w);const g=()=>w.remove();w.querySelector("#cpw-forgot-close").addEventListener("click",g),w.querySelector("#cpw-forgot-cancel").addEventListener("click",g),w.addEventListener("click",B=>{B.target===w&&g()}),w.querySelector("#cpw-forgot-send").addEventListener("click",async()=>{const B=w.querySelector("#cpw-forgot-send"),S=w.querySelector("#cpw-forgot-msg");B.disabled=!0;const I=B.textContent;B.textContent=n("cpw-forgot-sending");try{const U=await fetch("/api/auth/forgot_password",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:o})}),N=await U.json().catch(()=>({}));U.ok?(S.textContent=n("cpw-forgot-success"),S.className="cpw-forgot-msg success",B.style.display="none",w.querySelector("#cpw-forgot-cancel").textContent=n("cpw-forgot-close-btn")):(S.textContent=N.detail||n("cpw-forgot-fail"),S.className="cpw-forgot-msg error",B.disabled=!1,B.textContent=I)}catch{S.textContent=n("cpw-forgot-fail"),S.className="cpw-forgot-msg error",B.disabled=!1,B.textContent=I}})}function f(x){if(!x||!x.includes("@"))return x||"";const[o,p]=x.split("@");return o.length<=2?o+"****@"+p:o.slice(0,2)+"****@"+p}function h(x){return x==null?"":String(x).replace(/[&<>"']/g,o=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[o])}document.readyState==="complete"||document.readyState==="interactive"?s():document.addEventListener("DOMContentLoaded",s)})();(function(){let e=null,a=!1;async function n(){if(a)return;const l=localStorage.getItem("mrpilot_token");if(l){a=!0;try{const f=await fetch("/api/me",{headers:{Authorization:"Bearer "+l},cache:"no-store"});if(f.status===401){const h=await f.json().catch(()=>({})),x=h&&h.detail;let o="";if(typeof x=="string"?o=x:x&&typeof x=="object"&&(o=x.code||""),console.warn("[heartbeat] session revoked",o),localStorage.removeItem("mrpilot_token"),e&&(clearInterval(e),e=null),o==="auth.session_revoked")try{_showSessionRevokedModal()}catch{window.location.href="/"}else{const p=o==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";try{typeof showToast=="function"&&typeof t=="function"?showToast(t(p),"error"):alert("Session expired")}catch{}setTimeout(()=>{window.location.href="/"},1500)}}}catch{}finally{a=!1}}}function s(){e&&clearInterval(e),e=setInterval(n,15e3)}localStorage.getItem("mrpilot_token")&&s(),window.addEventListener("focus",n),document.addEventListener("visibilitychange",function(){document.hidden||n()}),window._sessionCheck=n})();async function Ye(){const e=document.getElementById("team-loading"),a=document.getElementById("team-list"),n=document.getElementById("team-empty"),s=document.getElementById("team-count");if(a){e&&(e.style.display=""),a.style.display="none",n&&(n.style.display="none");try{const l=await apiGet("/api/team/employees"),f=l&&l.employees||[];if(e&&(e.style.display="none"),s&&(s.textContent=(t("team-count")||"共 {n} 名员工").replace("{n}",f.length)),f.length===0){n&&(n.style.display="");return}a.style.display="",a.innerHTML=f.map(h=>{const x=h.last_login_at?new Date(h.last_login_at).toLocaleDateString():t("team-never-login")||"从未登录",o=h.is_active===!1?"team-status-off":"team-status-on",p=h.is_active===!1?t("team-status-disabled")||"已禁用":t("team-status-active")||"正常",w=h.email?`<span class="team-meta-sep">·</span><span>${escapeHtml(h.email)}</span>`:"";return`
            <div class="team-card" data-employee-id="${escapeHtml(h.id)}">
                <div class="team-card-main">
                    <div class="team-avatar">${escapeHtml((h.username||"?")[0].toUpperCase())}</div>
                    <div class="team-info">
                        <div class="team-name">${escapeHtml(h.username||"")}</div>
                        <div class="team-meta">
                            <span class="team-status-dot ${o}"></span>
                            <span>${escapeHtml(p)}</span>
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml(t("team-last-login")||"上次登录")}: ${escapeHtml(x)}</span>
                            ${w}
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml((t("team-assigned-clients")||"已分配 {n} 客户").replace("{n}",h.assigned_client_count||0))}</span>
                        </div>
                    </div>
                </div>
                <div class="team-card-actions">
                    <button class="btn btn-ghost btn-small" data-assign-clients="${escapeHtml(h.id)}" data-name="${escapeHtml(h.username||"")}">
                        ${escapeHtml(t("team-assign-clients")||"分配客户")}
                    </button>
                    <button class="btn btn-ghost btn-small" data-reset-pwd-employee="${escapeHtml(h.id)}" data-name="${escapeHtml(h.username||"")}" title="${escapeHtml(t("team-reset-pwd")||"重置密码")}">
                        ${escapeHtml(t("team-reset-pwd")||"重置密码")}
                    </button>
                    <button class="btn btn-ghost btn-small" data-toggle-employee="${escapeHtml(h.id)}" data-active="${h.is_active===!1?"false":"true"}">
                        ${escapeHtml(h.is_active===!1?t("team-enable")||"启用":t("team-disable")||"禁用")}
                    </button>
                    <button class="btn btn-ghost btn-small btn-danger-text" data-remove-employee="${escapeHtml(h.id)}" data-name="${escapeHtml(h.username||"")}">
                        ${escapeHtml(t("team-remove")||"移除")}
                    </button>
                </div>
            </div>`}).join("")}catch(l){console.error("loadTeamList failed:",l),e&&(e.textContent=t("team-load-failed")||"加载失败")}}}async function Mt(){document.querySelectorAll(".add-emp-overlay").forEach(s=>s.remove());const e=document.createElement("div");e.className="add-emp-overlay",e.innerHTML=`
        <div class="add-emp-modal">
            <div class="add-emp-head">
                <div class="add-emp-title">${escapeHtml(t("team-add")||"添加员工")}</div>
                <button class="add-emp-close" type="button" aria-label="close">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                </button>
            </div>
            <div class="add-emp-body">
                <div class="add-emp-field">
                    <label>${escapeHtml(t("team-modal-username")||"员工用户名")}</label>
                    <input type="text" class="add-emp-input" id="add-emp-username" placeholder="${escapeHtml(t("team-modal-username-ph")||"employee01")}" autocomplete="off">
                    <div class="add-emp-hint">${escapeHtml(t("team-modal-username-hint")||"3-50 位 · 字母 / 数字 / 下划线 / 点 / 横线 · 唯一")}</div>
                </div>
                <div class="add-emp-field">
                    <label>${escapeHtml(t("team-modal-email")||"邮箱(选填)")}</label>
                    <input type="email" class="add-emp-input" id="add-emp-email" placeholder="${escapeHtml(t("team-modal-email-ph")||"employee@example.com")}" autocomplete="off">
                    <div class="add-emp-hint">${escapeHtml(t("team-modal-email-hint")||"选填 · 用于忘记密码时邮件重置 · 留空则只能由老板重置")}</div>
                </div>
                <div class="add-emp-field">
                    <label>${escapeHtml(t("team-modal-password")||"初始密码")}</label>
                    <input type="text" class="add-emp-input" id="add-emp-password" placeholder="${escapeHtml(t("team-modal-password-ph")||"至少 8 位 · 字母 + 数字")}" autocomplete="off">
                    <div class="add-emp-hint">${escapeHtml(t("team-modal-password-hint")||"员工首次登录后会被强制修改密码")}</div>
                </div>
                <div class="add-emp-msg" id="add-emp-msg"></div>
            </div>
            <div class="add-emp-foot">
                <button class="btn btn-ghost" type="button" id="add-emp-cancel">${escapeHtml(t("btn-cancel")||"取消")}</button>
                <button class="btn btn-primary" type="button" id="add-emp-submit">${escapeHtml(t("team-add")||"添加员工")}</button>
            </div>
        </div>
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const s=document.getElementById("add-emp-username");s&&s.focus()},200);function a(){e.classList.remove("show"),setTimeout(()=>e.remove(),220)}e.querySelector(".add-emp-close").addEventListener("click",a),e.querySelector("#add-emp-cancel").addEventListener("click",a),e.addEventListener("click",s=>{s.target===e&&a()}),e.querySelector("#add-emp-submit").addEventListener("click",async()=>{const s=document.getElementById("add-emp-username"),l=document.getElementById("add-emp-email"),f=document.getElementById("add-emp-password"),h=document.getElementById("add-emp-msg"),x=document.getElementById("add-emp-submit"),o=(s.value||"").trim(),p=(l.value||"").trim(),w=f.value||"";if(h.textContent="",h.classList.remove("error"),!o||o.length<3){h.textContent=t("team-modal-err-username")||"用户名至少 3 位",h.classList.add("error");return}if(!/^[a-zA-Z0-9_.\-]+$/.test(o)){h.textContent=t("team-modal-err-username-fmt")||"只能用字母 / 数字 / 下划线 / 点 / 横线",h.classList.add("error");return}if(p&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(p)){h.textContent=t("msg-email-invalid")||"邮箱格式不对",h.classList.add("error");return}if(w.length<8){h.textContent=t("pwd-too-short")||"密码至少 8 位",h.classList.add("error");return}if(/^\d+$/.test(w)){h.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",h.classList.add("error");return}if(!(/[a-zA-Z]/.test(w)&&/\d/.test(w))){h.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",h.classList.add("error");return}x.disabled=!0,x.textContent=t("msg-saving")||"保存中...";try{const g={username:o,password:w};p&&(g.email=p);const B=await apiPost("/api/team/employees",g),S=B?await B.json().catch(()=>({})):{};if(B&&B.ok&&S&&S.ok){showToast(t("team-added")||"员工已添加","success"),a(),Ye();return}const I=S&&S.detail||"unknown",U={"team.username_exists":t("team-username-exists")||"用户名已被占用","team.email_exists":t("team-email-exists")||"邮箱已被占用","team.create_failed":t("team-create-failed")||"创建失败","team.only_owner_or_super":t("team-no-permission")||"无权限","team.no_tenant":t("team-no-tenant")||"请先升级账号","pwd.too_short":t("pwd-too-short")||"密码至少 8 位","pwd.too_weak_numeric":t("pwd-too-weak-numeric")||"不能是纯数字","pwd.too_weak_common":t("pwd-too-weak-common")||"这个密码太常见 · 请换一个","pwd.too_weak":t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};h.textContent=U[I]||(t("team-create-failed")||"创建失败")+" ("+I+")",h.classList.add("error")}catch{h.textContent=t("team-create-failed")||"创建失败",h.classList.add("error")}finally{x.disabled=!1,x.textContent=t("team-add")||"添加员工"}});function n(s){s.key==="Escape"&&(a(),document.removeEventListener("keydown",n))}document.addEventListener("keydown",n)}async function $t(e,a){try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}/active`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({is_active:!!a})})).ok){Ye();return}showToast(t("team-toggle-failed")||"操作失败","error")}catch{showToast(t("team-toggle-failed")||"操作失败","error")}}async function Ht(e,a){const s=(t("team-confirm-remove")||"确认移除员工「{name}」?他的所有识别记录会保留 · 但他将无法登录").replace("{name}",a).replace("{n}",a);if(await showConfirm(s,{danger:!0,okText:t("team-remove")}))try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){showToast(t("team-removed")||"已移除","success"),Ye();return}showToast(t("team-remove-failed")||"移除失败","error")}catch{showToast(t("team-remove-failed")||"移除失败","error")}}async function At(e,a){const s=(t("team-reset-pwd-confirm")||"给员工「{name}」发送改密链接?系统将通过员工的邮箱或 LINE 发送一个 15 分钟内有效的链接 · 员工自己点链接改密码 · 您看不到密码").replace("{name}",a).replace("{n}",a);if(await showConfirm(s,{okText:t("team-reset-link-send-btn")||"发送链接"}))try{const f=await fetch(`/api/team/employees/${encodeURIComponent(e)}/reset-password`,{method:"POST",headers:{Authorization:"Bearer "+token}}),h=await f.json().catch(()=>({}));if(f.status===400&&h.detail==="team.reset_no_channel"){showToast(t("team-reset-no-channel")||"员工尚未绑定邮箱或 LINE · 请先帮员工补充邮箱再重置","error");return}if(!f.ok){showToast(t("team-reset-pwd-fail")||"发送失败","error");return}if(h.channel==="line"||h.channel==="email"){const x=t("team-reset-link-sent")||"改密链接已通过 {ch} 发送给员工 · 链接 15 分钟内有效",o=h.channel==="line"?"LINE":t("team-reset-via-email")||"邮箱";showToast(x.replace("{ch}",o),"success");return}showToast(t("team-reset-pwd-fail")||"发送失败","error")}catch{showToast(t("team-reset-pwd-fail")||"发送失败","error")}}document.addEventListener("click",e=>{if(e.target.closest("#btn-add-employee")){e.preventDefault(),Mt();return}const a=e.target.closest("[data-toggle-employee]");if(a){e.preventDefault(),$t(a.dataset.toggleEmployee,a.dataset.active==="false");return}const n=e.target.closest("[data-remove-employee]");if(n){e.preventDefault(),Ht(n.dataset.removeEmployee,n.dataset.name||"");return}const s=e.target.closest("[data-reset-pwd-employee]");if(s){e.preventDefault(),At(s.dataset.resetPwdEmployee,s.dataset.name||"");return}const l=e.target.closest("[data-assign-clients]");if(l){e.preventDefault(),typeof window.openAssignClientsModal=="function"&&window.openAssignClientsModal(l.dataset.assignClients,l.dataset.name||"");return}});window.loadTeamList=Ye;function jt(e){document.querySelectorAll(".auto-nav-item").forEach(a=>{a.classList.toggle("active",a.dataset.autoTab===e)}),document.querySelectorAll(".auto-panel").forEach(a=>{a.classList.toggle("active",a.dataset.autoPanel===e)}),e==="email"&&typeof window._loadEmailIngestPanel=="function"?(window._loadEmailIngestPanel(),typeof window._startEmailLogAutoRefresh=="function"&&window._startEmailLogAutoRefresh()):typeof window._stopEmailLogAutoRefresh=="function"&&window._stopEmailLogAutoRefresh(),e==="bank"&&typeof window._loadBankReconPanel=="function"&&window._loadBankReconPanel(),e==="linebot"&&typeof window._loadLineBotPanel=="function"&&window._loadLineBotPanel(),e==="alert"&&typeof window._loadNotificationsPanel=="function"&&window._loadNotificationsPanel(),e==="folder"&&typeof window._loadFolderWatcherPanel=="function"&&window._loadFolderWatcherPanel()}window.switchAutomationTab=jt;typeof console<"u"&&typeof console.info=="function"&&console.info("[pearnly] vite bundle loaded · dashboard + billing + test-center + workspace-switcher + recon-center + assign-clients + access-log + notifications + recon-batch + welcome-wizard + archive-settings");
//# sourceMappingURL=main.js.map
