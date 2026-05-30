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


`,e.dataset.wbInjected="1";try{const a=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",n=window.I18N;n&&n[a]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const i=s.getAttribute("data-i18n");n[a][i]&&(s.textContent=n[a][i])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const i=s.getAttribute("data-i18n-placeholder");n[a][i]&&(s.placeholder=n[a][i])}))}catch{}}})();(function(){const e=document.getElementById("page-integrations");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const a=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",n=window.I18N;n&&n[a]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const i=s.getAttribute("data-i18n");n[a][i]&&(s.textContent=n[a][i])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const i=s.getAttribute("data-i18n-placeholder");n[a][i]&&(s.placeholder=n[a][i])}))}catch{}}})();(function(){const e=document.getElementById("page-settings");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const a=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",n=window.I18N;n&&n[a]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const i=s.getAttribute("data-i18n");n[a][i]&&(s.textContent=n[a][i])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const i=s.getAttribute("data-i18n-placeholder");n[a][i]&&(s.placeholder=n[a][i])}))}catch{}}})();(function(){const e=document.getElementById("page-automation");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const a=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",n=window.I18N;n&&n[a]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const i=s.getAttribute("data-i18n");n[a][i]&&(s.textContent=n[a][i])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const i=s.getAttribute("data-i18n-placeholder");n[a][i]&&(s.placeholder=n[a][i])}))}catch{}}})();(function(){const e={"page-integration":`
        <div class="coming-soon">
            <svg class="cs-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 14V8M30 14V8M14 40h20"/>
                <rect x="12" y="14" width="24" height="26" rx="2"/>
            </svg>
            <div class="cs-title" data-i18n="cs-int-title">ERP 无缝对接</div>
            <div class="cs-desc" data-i18n="cs-int-desc">把识别结果自动推送到你的 Mr.ERP,告别手动复制粘贴</div>
            <div class="cs-coming" data-i18n="cs-coming-soon">即将上线</div>
        </div>
`,"page-templates":`
        <div class="coming-soon">
            <svg class="cs-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <rect x="8" y="10" width="32" height="28" rx="2"/>
                <path d="M8 20h32M18 10v28"/>
            </svg>
            <div class="cs-title" data-i18n="cs-tpl-title">自定义 Excel 模板</div>
            <div class="cs-desc" data-i18n="cs-tpl-desc">根据不同客户的 ERP 定制导出列结构</div>
            <div class="cs-coming" data-i18n="cs-coming-soon">即将上线</div>
        </div>
`,"page-api-keys":`
        <div class="coming-soon">
            <svg class="cs-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M10 26l14-14M10 26l-3 12 12-3M24 12l10 10M34 22l7-7a2 2 0 000-3l-3-3a2 2 0 00-3 0l-7 7"/>
            </svg>
            <div class="cs-title" data-i18n="cs-api-title">自动化对接</div>
            <div class="cs-desc" data-i18n="cs-api-desc">未来可通过此功能对接 UiPath、n8n 等自动化工具 · 让识别流程融入您的工作流</div>
            <div class="cs-coming" data-i18n="cs-coming-soon">即将上线</div>
        </div>
`,"page-vouchers":`
        <div class="auto-coming-hero">
            <div class="coming-big-icon">
                <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M10 6h18l12 12v22a2 2 0 01-2 2H10a2 2 0 01-2-2V8a2 2 0 012-2z"/>
                    <path d="M28 6v12h12"/>
                    <path d="M15 28l5 5 10-10"/>
                </svg>
            </div>
            <div class="coming-big-title" data-i18n="cs-vouchers-title">凭证中心</div>
            <div class="coming-big-desc" data-i18n="cs-vouchers-desc">识别后自动生成会计凭证 · 借贷科目 AI 推荐 · 审核后一键推 ERP</div>
            <ul class="coming-features">
                <li data-i18n="cs-vouchers-f1">凭证自动生成 · AI 推荐借贷科目和金额分录</li>
                <li data-i18n="cs-vouchers-f2">批量审核 + 单笔修改 · 审计追溯完整 · 所有改动留痕</li>
                <li data-i18n="cs-vouchers-f3">支持中式凭证(借 / 贷)与泰式凭证(ใบสำคัญ)双格式</li>
            </ul>
            <div class="coming-eta" data-i18n="cs-vouchers-eta">预计 v104 上线</div>
        </div>
`,"page-sales-invoices":`
        <div class="auto-coming-hero">
            <div class="coming-big-icon">
                <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 6h18l6 6v30H12z"/>
                    <path d="M30 6v6h6"/>
                    <line x1="18" y1="20" x2="32" y2="20"/>
                    <line x1="18" y1="26" x2="32" y2="26"/>
                    <line x1="18" y1="32" x2="26" y2="32"/>
                </svg>
            </div>
            <div class="coming-big-title" data-i18n="cs-sales-invoices-title">销售发票</div>
            <div class="coming-big-desc" data-i18n="cs-sales-invoices-desc">给客户开发票一键生成 · 进项识别 + 销项开票一站搞定 · ภ.พ.30 报税进销一并汇总</div>
            <ul class="coming-features">
                <li data-i18n="cs-sales-invoices-f1">选客户(已存档)+ 商品行项目 + 自动算 7% VAT · 1 分钟开一张</li>
                <li data-i18n="cs-sales-invoices-f2">生成正规 ใบกำกับภาษี / ใบเสร็จ PDF · 一键发邮件 / LINE 给客户</li>
                <li data-i18n="cs-sales-invoices-f3">销项数据自动汇入 ภ.พ.30 · 不再手抄进销税额对账</li>
            </ul>
            <div class="coming-eta" data-i18n="cs-sales-invoices-eta">预计 v110.1 上线</div>
        </div>
`,"page-receivables":`
        <div class="auto-coming-hero">
            <div class="coming-big-icon">
                <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M24 6v36"/>
                    <path d="M34 14h-13a6 6 0 000 12h5a6 6 0 010 12h-13"/>
                </svg>
            </div>
            <div class="coming-big-title" data-i18n="cs-receivables-title">应收追踪</div>
            <div class="coming-big-desc" data-i18n="cs-receivables-desc">应收未收款一目了然 · 账龄自动分组 · 到期自动提醒客户付款 · DSO 指标实时更新</div>
            <ul class="coming-features">
                <li data-i18n="cs-receivables-f1">账龄分析(30 / 60 / 90 / 90+ 天)· 逾期自动红标</li>
                <li data-i18n="cs-receivables-f2">LINE / 邮件自动催收 · 多模板预设 · 一键群发不失礼</li>
                <li data-i18n="cs-receivables-f3">银行流水回款自动核销 · 不用手动对账 · 收款秒到账</li>
            </ul>
            <div class="coming-eta" data-i18n="cs-receivables-eta">预计 v107 上线</div>
        </div>
`,"page-cloud":`
        <div class="auto-coming-hero">
            <div class="coming-big-icon">
                <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M36 22h-2a12 12 0 10-20 10h22a6 6 0 000-12z"/>
                    <path d="M24 20v10M20 26l4 4 4-4"/>
                </svg>
            </div>
            <div class="coming-big-title" data-i18n="cs-cloud-title">云盘同步</div>
            <div class="coming-big-desc" data-i18n="cs-cloud-desc">Google Drive / OneDrive 指定文件夹监听 · 跨设备远程入账 · 不依赖本地浏览器</div>
            <ul class="coming-features">
                <li data-i18n="cs-cloud-f1">手机拍照 → Drive app 上传 → Pearnly 自动识别推 ERP</li>
                <li data-i18n="cs-cloud-f2">服务器侧轮询 · 浏览器关了照样跑 · 真 24/7 不间断</li>
                <li data-i18n="cs-cloud-f3">多设备协作 · 出纳外勤扫描 + 会计坐班复核分工</li>
            </ul>
            <div class="coming-eta" data-i18n="cs-cloud-eta">预计 v108 上线</div>
        </div>
`},a=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",n=window.I18N;Object.keys(e).forEach(s=>{const i=document.getElementById(s);!i||i.dataset.wbInjected==="1"||(i.innerHTML=e[s],i.dataset.wbInjected="1",n&&n[a]&&i.querySelectorAll("[data-i18n]").forEach(g=>{const b=g.getAttribute("data-i18n");n[a][b]&&(g.textContent=n[a][b])}))})})();function Be(e,a){try{return typeof window.t=="function"?window.t(e):a}catch{return a}}function Te(e){if(e==null||isNaN(e))return"—";try{return String(e).replace(/\B(?=(\d{3})+(?!\d))/g,",")}catch{return String(e)}}function Et(e){if(!e)return"";try{const a=new Date(e).getTime();if(!a)return"";const n=Math.floor((Date.now()-a)/1e3);return n<60?Be("time-just-now","刚刚"):n<3600?Math.floor(n/60)+Be("time-min-ago-suffix"," 分钟前"):n<86400?Math.floor(n/3600)+Be("time-hour-ago-suffix"," 小时前"):Math.floor(n/86400)+Be("time-day-ago-suffix"," 天前")}catch{return""}}async function Ke(){rt();const e=document.getElementById("dash-kpi-invoices"),a=document.getElementById("dash-kpi-pending"),n=document.getElementById("dash-kpi-exceptions"),s=document.getElementById("dash-kpi-plan"),i=document.getElementById("dash-kpi-plan-sub"),g=document.getElementById("dash-recent-list"),b=document.getElementById("dash-quick-exc-badge");try{const _={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},[o,v,w]=await Promise.all([fetch("/api/me/tenant-usage",{headers:_}).then(R=>R.ok?R.json():null).catch(()=>null),fetch("/api/history?limit=20",{headers:_}).then(R=>R.ok?R.json():null).catch(()=>null),fetch("/api/exceptions/stats?status=pending",{headers:_}).then(R=>R.ok?R.json():null).catch(()=>null)]),u=o&&o.ocr_this_month||0;let d=0;const E=v&&(v.items||v.history||v)||[],k=Array.isArray(E)?E:[];k.forEach(R=>{(R.status==="pending"||R.status==="reviewing")&&d++});const q=w&&(w.total||w.count||w.pending||0)||0;if(e&&(e.textContent=Te(u)),a&&(a.textContent=Te(d)),n&&(n.textContent=Te(q)),b&&(q>0?(b.style.display="",b.textContent=q):b.style.display="none"),s&&o){const R=o.ocr_this_month||0,y=o.quota||0;s.textContent=Te(R),i&&(i.textContent=y?R+" / "+Te(y)+" 张":Be("dash-kpi-plan-sub","本月用量"))}if(g)if(k.length===0)g.innerHTML='<div class="dash-recent-empty">'+Be("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>";else{const R=k.slice(0,5).map(y=>{const B=(y.invoice_no||y.filename||y.id||"").toString(),O=(y.supplier_name||y.buyer_name||y.client_name||y.notes||"").toString(),D=Et(y.created_at||y.upload_time||y.date),F=A=>String(A).replace(/[&<>"']/g,f=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[f]);return'<div class="dash-recent-row"><span class="dash-recent-key" title="'+F(B)+'">'+F(B)+'</span><span class="dash-recent-mid" title="'+F(O)+'">'+F(O)+'</span><span class="dash-recent-time">'+F(D)+"</span></div>"}).join("");g.innerHTML=R}}catch{g&&(g.innerHTML='<div class="dash-recent-empty">'+Be("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>")}}window.loadDashboard=Ke;async function rt(){const e=document.getElementById("dash-kpi-balance-card"),a=document.getElementById("dash-kpi-usage-card"),n=document.getElementById("dash-kpi-balance"),s=document.getElementById("dash-kpi-balance-sub"),i=document.getElementById("dash-kpi-usage"),g=document.getElementById("dash-kpi-usage-sub");if(!(!e||!a))try{const b={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},_=await fetch("/api/me/credits",{headers:b,cache:"no-store"});if(!_.ok){e.style.display="none",i&&(i.textContent="—"),g&&(g.textContent="");return}const o=await _.json(),v=!!o.is_owner,w=!!o.is_billing_exempt;if(!v)e.style.display="none";else if(e.style.display="",w)n&&(n.textContent="∞",n.className="dash-kpi-val dash-green"),s&&(s.textContent=typeof window.t=="function"?window.t("dash-kpi-balance-exempt"):"Billing exempt");else{const d=typeof o.balance_thb=="number"?o.balance_thb:0;if(n&&(n.textContent="฿"+d.toFixed(2),n.className=d<50?"dash-kpi-val dash-red":"dash-kpi-val"),s){const E=typeof window.t=="function"?window.t("dash-kpi-balance-topup"):"Top up →",k=d<50?"#dc2626":"#6b7280",q=R=>typeof window.escapeHtml=="function"?window.escapeHtml(R):String(R).replace(/[&<>"']/g,y=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[y]);s.innerHTML='<a href="#" id="kpi-balance-topup-link" style="color:'+k+';text-decoration:underline;cursor:pointer;" onclick="event.preventDefault();window._openTopupModal&&window._openTopupModal();return false;">'+q(E)+"</a>"}}const u=typeof o.pages_this_month=="number"?o.pages_this_month:typeof o.my_invoice_count=="number"?o.my_invoice_count:0;if(a.style.display="",i&&(i.textContent=String(u)),g){const d=u>=200?"dash-kpi-usage-sub-high":"dash-kpi-usage-sub-low",E=typeof window.t=="function"?window.t(d,{used:u}):u+" pages";g.textContent=E}}catch(b){console.warn("[credits] loadCreditsCard failed:",b),e.style.display="none",i&&(i.textContent="—")}}window.loadCreditsCard=rt;document.addEventListener("DOMContentLoaded",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&setTimeout(Ke,500)});typeof window.subscribeI18n=="function"&&window.subscribeI18n("dashboard",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&Ke()});function ge(e){return(typeof window.t=="function"?window.t(e):null)||e}function Xe(){return localStorage.getItem("mrpilot_token")||""}function me(e){return document.getElementById(e)}var Ne=null,$e=null;function lt(){$e||($e=setInterval(function(){if(!document.hidden){var e=Xe();e&&(window._userInfo&&window._userInfo.is_billing_exempt||fetch("/api/me/credits",{headers:{Authorization:"Bearer "+e},cache:"no-store"}).then(function(a){return a.ok?a.json():null}).then(function(a){if(a){var n=a.balance_thb!=null?Number(a.balance_thb):0;Ne!==null&&n>Ne&&(window.showToast&&window.showToast(ge("credits-updated"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard(),typeof window._refreshBalanceAlerts=="function"&&window._refreshBalanceAlerts()),Ne=n}}).catch(function(){}))}},3e4))}function Bt(){$e&&(clearInterval($e),$e=null),Ne=null}window._startCreditsPoll=lt;window._stopCreditsPoll=Bt;lt();var Ze=null,Qe=0;function It(){if(!me("topup-v2-ov")){var e=document.createElement("div");e.id="topup-v2-ov",e.className="topup-v2-ov",e.style.cssText="display:none;position:fixed;inset:0;background:rgba(15,23,42,.5);z-index:9500;align-items:center;justify-content:center;padding:16px",e.innerHTML=['<div class="topup-v2-box">','  <div class="topup-v2-head">','    <div class="topup-v2-title" id="tv2-title"></div>','    <button class="topup-v2-close" id="tv2-close" aria-label="close">','      <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="4" y1="4" x2="16" y2="16"/><line x1="16" y1="4" x2="4" y2="16"/></svg>',"    </button>","  </div>",'  <div class="topup-v2-steps">','    <div class="topup-v2-step" id="tv2-d1"><span class="topup-v2-dot">1</span><span class="topup-v2-slabel" id="tv2-sl1"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d2"><span class="topup-v2-dot">2</span><span class="topup-v2-slabel" id="tv2-sl2"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d3"><span class="topup-v2-dot">3</span><span class="topup-v2-slabel" id="tv2-sl3"></span></div>',"  </div>",'  <div class="topup-v2-body">','    <div id="tv2-s1">','      <label class="topup-v2-label" id="tv2-al"></label>','      <div class="topup-v2-qamts">','        <button class="topup-v2-qamt" data-val="100">฿100</button>','        <button class="topup-v2-qamt" data-val="500">฿500</button>','        <button class="topup-v2-qamt" data-val="1000">฿1,000</button>','        <button class="topup-v2-qamt" data-val="2000">฿2,000</button>',"      </div>",'      <input id="tv2-amt" type="number" min="10" step="1" class="topup-v2-input" placeholder="฿ ...">','      <div id="tv2-ae" class="topup-v2-err" style="display:none"></div>',"    </div>",'    <div id="tv2-s2" style="display:none">','      <p class="topup-v2-bank-label" id="tv2-bl"></p>','      <div class="topup-v2-bank-card">','        <div class="topup-v2-bank-name">ธนาคาร กรุงเทพ</div>','        <div class="topup-v2-bank-branch">สาขาโชคชัย 4 ลาดพร้าว</div>','        <div class="topup-v2-bank-acct">230-0-91368-4</div>','        <div class="topup-v2-bank-holder">บจ. มิสเตอร์ อี อาร์ พี</div>','        <button class="topup-v2-copy" id="tv2-copy"></button>',"      </div>",'      <div class="topup-v2-warn" id="tv2-bn"></div>',"    </div>",'    <div id="tv2-s3" style="display:none">','      <div class="topup-v2-drop" id="tv2-drop">','        <input type="file" id="tv2-file" accept="image/*,.pdf" style="display:none">','        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>','        <span class="topup-v2-drop-text" id="tv2-dt"></span>',"      </div>",'      <div id="tv2-se" class="topup-v2-err" style="display:none"></div>','      <label class="topup-v2-label" id="tv2-pl"></label>','      <input id="tv2-payer" type="text" maxlength="200" class="topup-v2-input">','      <label class="topup-v2-label" id="tv2-nl"></label>','      <input id="tv2-note" type="text" maxlength="500" class="topup-v2-input">','      <div id="tv2-ue" class="topup-v2-err" style="display:none"></div>',"    </div>","  </div>",'  <div class="topup-v2-foot">','    <button class="btn btn-ghost" id="tv2-back" style="display:none"></button>','    <button class="btn btn-primary" id="tv2-next"></button>',"  </div>","</div>"].join(""),document.body.appendChild(e),Lt()}}function ct(){var e=function(a,n){var s=me(a);s&&(s.textContent=n)};e("tv2-title",ge("topup-title")),e("tv2-sl1",ge("topup-step1")),e("tv2-sl2",ge("topup-step2")),e("tv2-sl3",ge("topup-step3")),e("tv2-al",ge("topup-amount-label")),e("tv2-bl",ge("topup-bank-label")),e("tv2-copy",ge("topup-copy-account")),e("tv2-dt",ge("topup-slip-drop")),e("tv2-pl",ge("topup-payer-label")),e("tv2-nl",ge("topup-note-label"))}function je(e){[1,2,3].forEach(function(i){var g=me("tv2-s"+i);g&&(g.style.display=i===e?"":"none");var b=me("tv2-d"+i);b&&b.classList.toggle("active",i<=e)});var a=me("tv2-back"),n=me("tv2-next");if(e===1?a&&(a.style.display="",a.textContent=ge("topup-btn-cancel")):a&&(a.style.display="",a.textContent=ge("topup-btn-back")),n&&(n.textContent=ge(e===3?"topup-btn-submit":"topup-btn-next")),e===2){var s=me("tv2-bn");s&&(s.innerHTML=ge("topup-bank-note").replace("{amount}","<strong>฿"+Number(Qe).toLocaleString()+"</strong>"))}}function Je(){for(var e=1;e<=3;e++){var a=me("tv2-s"+e);if(a&&a.style.display!=="none")return e}return 1}function ze(e){var a=me(e);a&&(a.textContent="",a.style.display="none")}function He(e,a){var n=me(e);n&&(n.textContent=a,n.style.display="")}function st(e){var a=me("tv2-dt");a&&(a.textContent=e.name);var n=me("tv2-drop");n&&n.classList.add("has-file"),ze("tv2-se")}function Lt(){var e=me("topup-v2-ov");me("tv2-close").addEventListener("click",Me),e.addEventListener("click",function(g){g.target===e&&Me()}),document.addEventListener("keydown",function(g){g.key==="Escape"&&e&&e.style.display!=="none"&&Me()}),e.addEventListener("click",function(g){var b=g.target.closest(".topup-v2-qamt");if(b){e.querySelectorAll(".topup-v2-qamt").forEach(function(o){o.classList.remove("active")}),b.classList.add("active");var _=me("tv2-amt");_&&(_.value=b.dataset.val,ze("tv2-ae"))}});var a=me("tv2-amt");a&&a.addEventListener("input",function(){e.querySelectorAll(".topup-v2-qamt").forEach(function(g){g.classList.remove("active")}),ze("tv2-ae")});var n=me("tv2-copy");n&&n.addEventListener("click",function(){navigator.clipboard&&navigator.clipboard.writeText("2300913684").then(function(){var g=n.textContent;n.textContent=ge("topup-copied"),setTimeout(function(){n.textContent=g},1500)})});var s=me("tv2-drop"),i=me("tv2-file");s&&(s.addEventListener("click",function(){i&&i.click()}),s.addEventListener("dragover",function(g){g.preventDefault(),s.classList.add("drag-over")}),s.addEventListener("dragleave",function(){s.classList.remove("drag-over")}),s.addEventListener("drop",function(g){g.preventDefault(),s.classList.remove("drag-over");var b=g.dataTransfer&&g.dataTransfer.files[0];b&&st(b)})),i&&i.addEventListener("change",function(){i.files[0]&&st(i.files[0])}),me("tv2-back").addEventListener("click",function(){var g=Je();if(g<=1){Me();return}je(g-1)}),me("tv2-next").addEventListener("click",function(){var g=Je();g===1?Ct():g===2?je(3):St()})}async function Ct(){var e=me("tv2-amt"),a=e?parseFloat(e.value):0;if(!a||a<10){He("tv2-ae",ge("topup-amount-invalid"));return}if(a>5e5){He("tv2-ae",ge("topup-amount-too-large"));return}Qe=a;var n=me("tv2-next");n&&(n.disabled=!0,n.textContent="…");try{var s=await fetch("/api/credits/topup/request",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+Xe()},body:JSON.stringify({amount_thb:a})});if(!s.ok){var i=await s.text(),g=ge("topup-submit-fail");try{var b=JSON.parse(i),_=b.detail;if(Array.isArray(_)&&_.length){var o=_[0]&&_[0].type||"";o.indexOf("less_than")>=0?g=ge("topup-amount-too-large"):(o.indexOf("greater_than")>=0||o.indexOf("parsing")>=0)&&(g=ge("topup-amount-invalid"))}else typeof _=="string"&&(g=_)}catch{}throw new Error(g)}var v=await s.json();Ze=v.request_id,je(2)}catch(w){He("tv2-ae",w.message||ge("topup-submit-fail"))}finally{n&&(n.disabled=!1,n.textContent=ge("topup-btn-next"))}}async function St(){var e=me("tv2-file");if(!e||!e.files||!e.files[0]){He("tv2-se",ge("topup-slip-required"));return}var a=me("tv2-next");a&&(a.disabled=!0,a.textContent="…");try{var n=new FormData;n.append("file",e.files[0]);var s=me("tv2-payer"),i=me("tv2-note");s&&s.value.trim()&&n.append("payer_name",s.value.trim()),i&&i.value.trim()&&n.append("note",i.value.trim());var g=await fetch("/api/credits/topup/upload-slip/"+Ze,{method:"POST",headers:{Authorization:"Bearer "+Xe()},body:n});if(!g.ok)throw new Error(await g.text());var b=await g.json();b.auto_approved?(window.showToast&&window.showToast(ge("topup-auto-approved"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard()):window.showToast&&window.showToast(ge("topup-pending"),"info"),Me()}catch(_){He("tv2-ue",ge("topup-upload-fail")+" · "+_.message),a&&(a.disabled=!1,a.textContent=ge("topup-btn-submit"))}}function Me(){var e=me("topup-v2-ov");e&&(e.style.display="none"),typeof window.loadDashboard=="function"&&window.loadDashboard()}window._openTopupModal=function(){It(),Ze=null,Qe=0,["tv2-amt","tv2-payer","tv2-note"].forEach(function(n){var s=me(n);s&&(s.value="")});var e=me("tv2-file");e&&(e.value="");var a=me("tv2-drop");a&&a.classList.remove("has-file","drag-over"),me("topup-v2-ov").querySelectorAll(".topup-v2-qamt").forEach(function(n){n.classList.remove("active")}),["tv2-ae","tv2-se","tv2-ue"].forEach(function(n){ze(n)}),ct(),je(1),me("topup-v2-ov").style.display="flex"};typeof window.subscribeI18n=="function"&&window.subscribeI18n("topup-v2",function(){var e=me("topup-v2-ov");e&&e.style.display!=="none"&&e.style.display!==""&&(ct(),je(Je()))});(function(){const e="v118.28.5",a="pearnly_tc_results_"+e,n=[{id:"A1",group:"A · 异常栏 page-head(BUG1)",desc:"手机宽度进异常栏 · 标题「异常栏」横排正常 · 不再每字一行"},{id:"A2",group:"A · 异常栏 page-head(BUG1)",desc:"副标题「所有被规则拦截的单据集中复核…」也横排正常 · 不竖排"},{id:"A3",group:"A · 异常栏 page-head(BUG1)",desc:"客户筛选下拉 + 刷新按钮换到新一行 · 不抢标题宽度"},{id:"B1",group:"B · 客户管理 page-head(BUG2)",desc:"手机宽度进客户管理 · 标题「客户管理」横排正常"},{id:"B2",group:"B · 客户管理 page-head(BUG2)",desc:"副标题「为每家客户单独归档发票…」横排正常 · 不竖排"},{id:"B3",group:"B · 客户管理 page-head(BUG2)",desc:"「+ 新建客户」按钮换到新一行 · 不挤标题"},{id:"C1",group:"C · 客户卡片(BUG3)",desc:"客户卡片「编辑 / 导出本月」按钮文字清晰 · 不被截断"},{id:"D1",group:"D · 历史表头(BUG4)",desc:"手机宽度进单据记录 · 表头「文件·发票号·供应商」/「金额」单行 · 不竖排"},{id:"D2",group:"D · 历史表头(BUG4)",desc:"行内 INV-TH-202605-1006 这种长发票号正常单行展示 · 不一字一行"},{id:"E1",group:"E · 对账切换器(BUG6)",desc:"手机宽度进对账中心 · 顶栏点「全部客户」chip · 下拉从右上角向下展开 · 右对齐 · 不贴左屏边"},{id:"E2",group:"E · 对账切换器(BUG6)",desc:"下拉宽度自适应屏幕 · 不超出屏幕右边"},{id:"F1",group:"F · 通用设置回归",desc:"设置 → 个人资料 · 没有「界面语言」4 按钮卡"},{id:"F2",group:"F · 通用设置回归",desc:"左侧 nav 顺序:账户 / 公司 / 工作流 / 系统 / 关于"},{id:"F3",group:"F · 通用设置回归",desc:"系统 → 通用设置 · 4 行下拉(语言/时区/日期/数字)· 改语言立即切语言 · 改其他保存后 F5 仍保留"},{id:"G1",group:"G · 移动端 settings(回归)",desc:"手机宽度设置 tabs 不重叠 · 按分组分行 · chip 风格"},{id:"H1",group:"H · 回归",desc:"OCR 上传识别 / 客户管理 / 异常栏 / 对账中心 / 测试中心 全部仍工作"},{id:"H2",group:"H · 回归",desc:"4 语切换没新增异常(测试中心异常日志「API 失败」过滤无新条目)"},{id:"I1",group:"I · 三档移动 viewport",desc:"iPhone SE 375 · 上述 BUG 1-6 都修了"},{id:"I2",group:"I · 三档移动 viewport",desc:"Galaxy S 360 · 上述 BUG 1-6 都修了"},{id:"I3",group:"I · 三档移动 viewport",desc:"iPhone 12 Pro 414 · 上述 BUG 1-6 都修了"}];let s={},i="all",g=!1,b=!1;function _(G,K,te){let re=typeof t=="function"?t(G):null;return(!re||re===G)&&(re=K),te&&Object.keys(te).forEach(function(S){re=String(re).replace("{"+S+"}",String(te[S]))}),re}function o(){try{const G=localStorage.getItem(a);s=G?JSON.parse(G):{},(typeof s!="object"||!s)&&(s={})}catch{s={}}}function v(){try{localStorage.setItem(a,JSON.stringify(s))}catch{}}function w(G){const K=new Date(G),te=function(re){return re<10?"0"+re:""+re};return te(K.getHours())+":"+te(K.getMinutes())+":"+te(K.getSeconds())}function u(G){return String(G??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function d(G,K){try{typeof showToast=="function"?showToast(G,K||"info"):alert(G)}catch{}}function E(G){try{navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(G).then(function(){d(_("tc-toast-copied","已复制到剪贴板"),"success")}).catch(function(){k(G)}):k(G)}catch{k(G)}}function k(G){try{const K=document.createElement("textarea");K.value=G,K.style.position="fixed",K.style.opacity="0",document.body.appendChild(K),K.select();const te=document.execCommand("copy");document.body.removeChild(K),d(te?_("tc-toast-copied","已复制"):_("tc-toast-copy-fail","复制失败"),te?"success":"error")}catch{d(_("tc-toast-copy-fail","复制失败"),"error")}}function q(){const G=document.getElementById("tc-account-chip"),K=document.getElementById("tc-progress-chip");if(G&&(G.textContent=_userInfo&&(_userInfo.email||_userInfo.username)||"—"),K){const te=n.length,re=n.filter(function(S){return s[S.id]}).length;K.textContent=re+" / "+te}}function R(){const G=document.getElementById("tc-checklist-body");if(!G)return;const K={};n.forEach(function(re){K[re.group]||(K[re.group]=[]),K[re.group].push(re)});const te=[];Object.keys(K).forEach(function(re){te.push('<div class="tc-checklist-group">'),te.push('<div class="tc-checklist-group-title">'+u(re)+"</div>"),K[re].forEach(function(S){const h=s[S.id]||"",c=h?"is-"+h:"";te.push('<div class="tc-check-item '+c+'" data-id="'+u(S.id)+'"><div class="tc-check-id">'+u(S.id)+'</div><div class="tc-check-desc">'+u(S.desc)+'</div><div class="tc-check-actions">'+y(S.id,"pass",h)+y(S.id,"fail",h)+y(S.id,"skip",h)+"</div></div>")}),te.push("</div>")}),G.innerHTML=te.join("")}function y(G,K,te){const re=te===K,S={pass:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="4,11 8,15 16,5"/></svg>',fail:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="5" x2="15" y2="15"/><line x1="15" y1="5" x2="5" y2="15"/></svg>',skip:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="10" x2="15" y2="10"/></svg>'},h={pass:_("tc-status-pass","通过"),fail:_("tc-status-fail","失败"),skip:_("tc-status-skip","跳过")};return'<button type="button" class="tc-status-btn '+(re?"is-active "+K:"")+'" data-id="'+u(G)+'" data-kind="'+K+'" title="'+u(h[K])+'">'+S[K]+"</button>"}function B(G){return i==="all"?!0:i==="js_error"?G.type==="js_error"||G.type==="promise_error":i==="api"?G.type==="api_error"||G.type==="api_fail":i==="api_slow"?G.type==="api_slow":i==="console"?G.type==="console_error"||G.type==="console_warn":!0}function O(){const G=document.getElementById("tc-logs-body"),K=document.getElementById("tc-logs-count");if(!G)return;const te=(window._pearnlyTcLogs||[]).slice().reverse(),re=te.filter(B);if(K&&(K.textContent=String(te.length)),re.length===0){G.innerHTML='<div class="tc-logs-empty">'+u(_("tc-logs-empty","暂无异常"))+"</div>";return}const S=re.slice(0,100).map(function(h){const c=typeof h.detail=="object"?JSON.stringify(h.detail,null,2):String(h.detail||"");return'<div class="tc-log-item t-'+u(h.type)+'" data-ts="'+h.ts+'"><span class="tc-log-time">'+w(h.ts)+'</span><span class="tc-log-type">'+u(h.type)+'</span><div class="tc-log-summary">'+u(h.summary)+'<div class="tc-log-detail">'+u(c)+"</div></div></div>"}).join("");G.innerHTML=S,document.querySelectorAll("#tc-logs-filter .tc-filter-chip").forEach(function(h){h.classList.toggle("active",h.getAttribute("data-filter")===i)})}function D(){b||(b=!0,setTimeout(function(){b=!1,currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&O(),F()},200))}window._tcOnNewLog=D;function F(){const G=document.getElementById("nav-test-badge");if(!G)return;const K=(window._pearnlyTcLogs||[]).filter(function(te){return te.type==="js_error"||te.type==="promise_error"||te.type==="api_error"||te.type==="api_fail"||te.type==="console_error"}).length;K>0?(G.style.display="",G.textContent=K>99?"99+":String(K)):G.style.display="none"}function A(){q(),R(),O(),F()}function f(){const G=[],K=new Date,te=_userInfo&&(_userInfo.email||_userInfo.username)||"—";G.push("# Pearnly "+e+" 测试结果"),G.push("- 账号:"+te),G.push("- 时间:"+K.toISOString().replace("T"," ").slice(0,19));const re=n.length,S=n.filter(function(Z){return s[Z.id]==="pass"}).length,h=n.filter(function(Z){return s[Z.id]==="fail"}).length,c=n.filter(function(Z){return s[Z.id]==="skip"}).length,$=re-S-h-c;G.push("- 进度:"+(S+h+c)+" / "+re+" · ✅ "+S+" · ❌ "+h+" · ⏭ "+c+" · 未测 "+$),G.push(""),G.push("| ID | 描述 | 状态 |"),G.push("|---|---|---|"),n.forEach(function(Z){const le=s[Z.id],ie=le==="pass"?"✅":le==="fail"?"❌":le==="skip"?"⏭":"⬜";G.push("| "+Z.id+" | "+Z.desc.replace(/\|/g,"\\|")+" | "+ie+" |")});const P=n.filter(function(Z){return s[Z.id]==="fail"});P.length>0&&(G.push(""),G.push("## ❌ 失败项"),P.forEach(function(Z){G.push("- **"+Z.id+"** · "+Z.desc)}));const Y=(window._pearnlyTcLogs||[]).slice(-30).reverse();return Y.length>0&&(G.push(""),G.push("## 🔴 异常日志(最近 "+Y.length+" 条)"),Y.forEach(function(Z){if(G.push("- `"+w(Z.ts)+"` · **"+Z.type+"** · "+Z.summary),Z.detail){let le;try{le=JSON.stringify(Z.detail)}catch{le=String(Z.detail)}le&&le!=="{}"&&G.push("  - "+le.slice(0,600))}})),G.join(`
`)}function l(G){const K=(window._pearnlyTcLogs||[]).slice(-30).reverse();if(K.length===0)return"(暂无异常日志)";const te=["# Pearnly 异常日志(最近 "+K.length+" 条)"],re=_userInfo&&(_userInfo.email||_userInfo.username)||"—";return te.push("- 账号:"+re),te.push("- 当前页:"+(currentRoute||"?")),te.push("- UA:"+navigator.userAgent),te.push(""),K.forEach(function(S){if(te.push("## `"+w(S.ts)+"` · "+S.type),te.push("- "+S.summary),S.detail){te.push("```");try{te.push(JSON.stringify(S.detail,null,2).slice(0,2e3))}catch{te.push(String(S.detail).slice(0,2e3))}te.push("```")}}),te.join(`
`)}function p(){const G=Date.now();fetch("/api/health").then(function(K){const te=Date.now()-G;K.ok?d(_("tc-toast-health-ok","后端健康 ✓ {ms}ms",{ms:te}),"success"):d(_("tc-toast-health-fail","后端无响应")+" ("+K.status+")","error")}).catch(function(){d(_("tc-toast-health-fail","后端无响应"),"error")})}function I(){try{localStorage.removeItem(a),localStorage.removeItem("pearnly_current_client_id"),s={},(window._pearnlyTcLogs||[]).length=0,i="all",window.setCurrentClientId}catch{}A(),d(_("tc-toast-cleared","session 状态已清空"),"success")}function L(){try{fetch("/api/clients",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}).then(function(G){return G.json()}).then(function(G){window._clientsCache=G.clients||[],typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher(),typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter(),d("客户缓存已刷新 · "+(G.clients||[]).length+" 个客户","success")}).catch(function(){d("刷新失败","error")})}catch{}}function H(){if(g||!document.getElementById("page-test-center"))return;g=!0;const K=document.getElementById("tc-checklist-body");K&&K.addEventListener("click",function(le){const ie=le.target.closest(".tc-status-btn");if(!ie)return;const V=ie.getAttribute("data-id"),Q=ie.getAttribute("data-kind");!V||!Q||(s[V]===Q?delete s[V]:s[V]=Q,v(),R(),q())});const te=document.getElementById("tc-btn-reset-checklist");te&&te.addEventListener("click",function(){s={},v(),R(),q()});const re=document.getElementById("tc-btn-copy-all");re&&re.addEventListener("click",function(){E(f())});const S=document.getElementById("tc-btn-copy-logs");S&&S.addEventListener("click",function(){E(l())});const h=document.getElementById("tc-btn-clear-logs");h&&h.addEventListener("click",function(){(window._pearnlyTcLogs||[]).length=0,O(),F()});const c=document.getElementById("tc-logs-filter");c&&c.addEventListener("click",function(le){const ie=le.target.closest(".tc-filter-chip");ie&&(i=ie.getAttribute("data-filter")||"all",O())});const $=document.getElementById("tc-logs-body");$&&$.addEventListener("click",function(le){const ie=le.target.closest(".tc-log-item");ie&&ie.classList.toggle("expanded")});const P=document.getElementById("tc-tool-health");P&&P.addEventListener("click",p);const Y=document.getElementById("tc-tool-clear-session");Y&&Y.addEventListener("click",I);const Z=document.getElementById("tc-tool-reload-clients");Z&&Z.addEventListener("click",L)}function x(){}window._tcApplyVisibility=x;let M=0;const W=setInterval(function(){M++,_userInfo&&clearInterval(W),M>60&&clearInterval(W)},500);window.loadTestCenterPage=function(){o(),H(),A()},typeof window.subscribeI18n=="function"&&window.subscribeI18n("test-center",function(){F(),currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&A()})})();(function(){const e="pearnly_active_workspace_client_id",a="pearnly_work_mode";function n(B,O){if(typeof window.t=="function"){const D=window.t(B);if(D&&D!==B)return D}return O}function s(){const B=window._userInfo||{},O=String(B.role||"").toLowerCase(),D=String(B.tenant_role||"").toLowerCase();return B.is_super_admin===!0||B.is_owner===!0||O==="owner"||O==="admin"||D==="owner"||D==="admin"}function i(){return localStorage.getItem(a)==="client"?"client":"personal"}function g(){const B=localStorage.getItem(e);if(!B||B==="null"||B==="0"||B==="")return null;const O=parseInt(B,10);return isNaN(O)?null:O}function b(B){try{window.dispatchEvent(new CustomEvent("pearnly:workspace-changed",{detail:{id:B,mode:i()}}))}catch{}}function _(B){const O=g();B==null||B===0?localStorage.removeItem(e):(localStorage.setItem(e,String(B)),localStorage.setItem(a,"client")),String(O)!==String(B)&&b(B)}function o(){const B=g();localStorage.setItem(a,"personal"),localStorage.removeItem(e),B!=null&&b(null)}async function v(){try{const B=window.apiGet;if(typeof B!="function")return[];const O=await B("/api/workspace/clients");return O&&(O.clients||O.items)||[]}catch{return[]}}async function w(B){if(i()==="client"&&g()!=null)return typeof B=="function"&&B(),!0;const O=n("ws-need-client","这个功能需要先选择工作空间"),D=n("ws-btn-pick","选择工作空间"),F=n("ws-btn-cancel","取消");return typeof window.showConfirm=="function"?await window.showConfirm(O,{okText:D,cancelText:F})&&u(B):window.confirm(O+`

[`+D+" / "+F+"]")&&u(B),!1}async function u(B){const O=await v();if(typeof B=="function"&&i()!=="personal"&&O.length===1){_(Number(O[0].id)),B();return}if(typeof window.openWorkspaceChooserUI=="function"){window.openWorkspaceChooserUI({clients:O,canCreate:s(),active:g(),onPersonal:o,onPick:function(D){_(Number(D)),typeof B=="function"&&B()},emptyHint:O.length?null:s()?n("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):n("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。")});return}if(!O.length){const D=s()?n("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):n("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。");typeof window.showToast=="function"&&window.showToast(D,"info")}}function d(B){const O=B||document.getElementById("workspace-switcher-root");if(!O)return;const D=i(),F=g();let A,f;if(D==="client"&&F!=null){const I=(window._workspaceClientsCache||[]).find(L=>Number(L.id)===Number(F));A=k("building"),f=I?I.name:n("ws-current-label","当前工作空间")}else A=k("user"),f=n("ws-personal","个人事务");O.innerHTML='<button class="ws-ctrl-btn" id="ws-ctrl-btn" type="button">'+A+'<span class="ws-ctrl-label">'+E(f)+"</span></button>";const l=O.querySelector("#ws-ctrl-btn");l&&l.addEventListener("click",()=>u(null))}function E(B){return String(B??"").replace(/[&<>"']/g,function(O){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[O]})}function k(B){const O='<svg class="ws-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';return B==="building"?O+'<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>':O+'<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'}function q(B){B=B||{};const O=B.clients||[],D=B.active,F=document.getElementById("ws-modal");F&&F.remove();const A=document.createElement("div");A.id="ws-modal",A.className="ws-modal";const l='<button type="button" class="ws-modal-item'+(i()==="personal"||D==null?" active":"")+'" data-ws-personal="1"><span class="ws-modal-item-ic">'+k("user")+'</span><span class="ws-modal-item-text" style="display:flex;flex-direction:column;align-items:flex-start;min-width:0;"><span class="ws-modal-item-name">'+E(n("ws-personal","个人事务"))+'</span><span class="ws-modal-item-desc" style="font-size:11px;color:#6b7280;font-weight:400;margin-top:2px;line-height:1.35;white-space:normal;">'+E(n("ws-personal-desc","用于临时识别、测试或处理不归属任何公司的文件。"))+"</span></span></button>";let p="";if(O.length){const M=['<option value="">'+E(n("ws-select-ph","— 选择账套主体 —"))+"</option>"].concat(O.map(function(W){const G=D!=null&&Number(D)===Number(W.id);return'<option value="'+E(W.id)+'"'+(G?" selected":"")+">"+E(W.name||"#"+W.id)+"</option>"}));p='<div class="ws-modal-select-row"><label class="ws-modal-select-label">'+E(n("ws-select-label","账套主体"))+'</label><select class="ws-modal-select" data-ws-select="1">'+M.join("")+"</select></div>"}const I=!O.length&&B.emptyHint?'<div class="ws-modal-empty">'+E(B.emptyHint)+"</div>":"",L=B.canCreate?'<div class="ws-modal-create"><button type="button" class="ws-modal-create-toggle" data-ws-create-toggle="1">+ '+E(n("ws-create-client","新建工作空间"))+'</button><div class="ws-modal-create-form" data-ws-create-form style="display:none;"><input type="text" class="ws-modal-create-input" data-ws-create-name placeholder="'+E(n("ws-create-ph","公司名称,例如 BAKELAB"))+'"><button type="button" class="ws-modal-create-submit" data-ws-create-submit="1">'+E(n("ws-create-submit","创建"))+"</button></div></div>":"";A.innerHTML='<div class="ws-modal-box" role="dialog" aria-modal="true"><div class="ws-modal-head"><span class="ws-modal-title">'+E(n("ws-chooser-title","选择工作空间"))+'</span><button type="button" class="ws-modal-close" data-ws-close="1" aria-label="close">✕</button></div><div class="ws-modal-subtitle" style="font-size:12px;color:#6b7280;padding:2px 4px 12px;line-height:1.45;white-space:normal;">'+E(n("ws-chooser-subtitle","账套主体 = 你的公司(发票卖方/开票方)。选择正在为哪家公司做账。"))+'</div><div class="ws-modal-list">'+l+p+"</div>"+I+L+"</div>",document.body.appendChild(A);const H=A.querySelector("[data-ws-select]");H&&H.addEventListener("change",function(){const M=H.value;M&&(typeof B.onPick=="function"&&B.onPick(M),x(),d())});function x(){A.remove()}A.addEventListener("click",function(M){if(M.target===A||M.target.closest("[data-ws-close]")){x();return}if(M.target.closest("[data-ws-personal]")){typeof B.onPersonal=="function"&&B.onPersonal(),x(),d();return}const G=M.target.closest("[data-ws-pick]");if(G){const re=G.getAttribute("data-ws-pick");typeof B.onPick=="function"&&B.onPick(re),x(),d();return}if(M.target.closest("[data-ws-create-toggle]")){const re=A.querySelector("[data-ws-create-form]");if(re){re.style.display=re.style.display==="none"?"flex":"none";const S=re.querySelector("[data-ws-create-name]");S&&S.focus()}return}if(M.target.closest("[data-ws-create-submit]")){R(A,B,x);return}})}async function R(B,O,D){const F=B.querySelector("[data-ws-create-name]"),A=F?(F.value||"").trim():"";if(!A){F&&F.focus();return}let f=null;try{if(typeof window.apiPost=="function"){const p=await window.apiPost("/api/workspace/clients",{name:A});f=p&&typeof p.json=="function"?await p.json().catch(()=>null):p}}catch{f=null}const l=f&&(f.id||f.client&&f.client.id);if(!l){typeof window.showToast=="function"&&window.showToast(n("ws-create-fail","新建工作空间失败 · 请重试"),"error");return}window._workspaceClientsCache=await v(),_(Number(l)),O.onPick,D(),d()}window.openWorkspaceChooserUI=q,window.addEventListener("pearnly:workspace-changed",function(){d()}),window.getWorkMode=i,window.getActiveWorkspaceClientId=g,window.setActiveWorkspaceClientId=_,window.enterPersonalMode=o,window.requireWorkspace=w,window.openWorkspaceChooser=u,window.renderWorkspaceControl=d,window.fetchWorkspaceClients=v;function y(){try{if(sessionStorage.getItem("pearnly_ws_login_prompted")==="1"||g()!=null||localStorage.getItem(a)==="personal")return;sessionStorage.setItem("pearnly_ws_login_prompted","1"),setTimeout(function(){u(null)},800)}catch{}}v().then(B=>{window._workspaceClientsCache=B,d(),y()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("workspace-switcher",d)})();(function(){const e=D=>document.querySelector('[data-num-target="'+D+'"]');function a(D){if(!D)return t("reconcile-last-activity-none");try{const F=new Date(D),A=new Date,f=A-F;if(f/6e4<5)return t("reconcile-last-activity-just-now");if(F.toDateString()===A.toDateString())return t("reconcile-last-activity-today");const p=Math.max(1,Math.floor(f/(24*3600*1e3)));return t("reconcile-last-activity-days-ago").replace("{n}",p)}catch{return t("reconcile-last-activity-none")}}function n(D,F,A){const f=e(D);f&&(f.textContent=A?"-":String(F),f.classList.toggle("is-empty",!!A))}function s(D){const F=document.getElementById("reconcile-error");F&&(F.style.display=D?"flex":"none")}function i(D){const F=document.getElementById("reconcile-empty");F&&(F.style.display=D?"flex":"none")}function g(D,F){const A=document.getElementById("reconcile-last-activity");A&&(A.textContent=D,A.classList.toggle("has-data",!!F))}function b(D){const F=!D||(D.total_sessions||0)===0;n("pending",D.pending||0,F),n("matched",D.matched||0,F),n("unmatched",D.unmatched||0,F),g(a(D.last_activity_at),!!D.last_activity_at),s(!1),i(F)}function _(D){const F=D.toUpperCase();return F==="KBANK"?"bank-chip-kbank":F==="SCB"?"bank-chip-scb":F==="BBL"?"bank-chip-bbl":F==="KTB"?"bank-chip-ktb":F==="TTB"?"bank-chip-ttb":"bank-chip-other"}function o(D,F){const A=f=>f?String(f).slice(0,10):"?";return!D&&!F?"":A(D)+" ~ "+A(F)}function v(D){return D==null?"":String(D).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function w(D){const F=document.getElementById("reconcile-recent"),A=document.getElementById("reconcile-recent-list");if(!F||!A)return;const f=(D||[]).slice(0,20);if(f.length===0){F.style.display="none";return}F.style.display="",i(!1),A.innerHTML=f.map(l=>{const p=l.parse_status==="parse_failed",I=l.bank_code||"OTHER",L=l.account_last4?" ···"+v(l.account_last4):"",H=o(l.period_start,l.period_end),x=v(l.source_filename||""),M=Number(l.tx_count||0),W=p?'<span class="recon-card-fail" data-i18n="reconcile-card-parse-failed">'+t("reconcile-card-parse-failed")+"</span>":'<span class="recon-card-tx">'+t("reconcile-card-tx").replace("{n}",M)+"</span>";return'<div class="recon-card" data-session-id="'+v(l.id)+'" data-session-name="'+x+'"><span class="bank-chip '+_(I)+'">'+v(I)+'</span><div class="recon-card-main"><div class="recon-card-title">'+x+L+'</div><div class="recon-card-sub">'+v(H)+'</div></div><div class="recon-card-right">'+W+'</div><button class="recon-card-trash" data-trash="'+v(l.id)+'" title="'+v(t("bank-session-delete-tip")||"删除")+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/></svg></button><svg class="recon-card-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg></div>'}).join(""),A.querySelectorAll(".recon-card").forEach(l=>{l.addEventListener("click",p=>{p.target.closest(".recon-card-trash")||(l.dataset.sessionId,u())})}),A.querySelectorAll(".recon-card-trash").forEach(l=>{l.addEventListener("click",p=>{p.stopPropagation();const I=l.dataset.trash,L=l.closest(".recon-card"),H=L&&L.dataset.sessionName||"";typeof window._deleteBankSession=="function"&&window._deleteBankSession(I,H)})})}function u(D){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const F=document.querySelector('[data-recon-tab="bank"]');F&&F.click()},150)}function d(){s(!0),i(!1)}function E(){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const D=document.querySelector('[data-recon-tab="bank"]');D&&D.click()},150)}async function k(){n("pending",0,!0),n("matched",0,!0),n("unmatched",0,!0),g("",!1),s(!1),i(!1);const D=document.getElementById("reconcile-recent");D&&(D.style.display="none");const F={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")};try{const[A,f]=await Promise.all([fetch("/api/bank-recon/stats",{headers:F}),fetch("/api/bank-recon/sessions?limit=20",{headers:F})]);if(!A.ok)throw new Error("http "+A.status);const l=await A.json(),p=f.ok?await f.json():[];b(l||{}),w(p||[])}catch(A){console.warn("[reconcile] load failed",A),d()}}function q(D){if(!D||!D.length)return;const F="Bearer "+(localStorage.getItem("mrpilot_token")||"");let A=0;const f=D.length;Array.from(D).forEach(function(l){const p=new FormData;p.append("file",l,l.name);const I=new XMLHttpRequest;I.open("POST","/api/bank-recon/upload"),I.setRequestHeader("Authorization",F),I.onload=function(){A++;try{const L=JSON.parse(I.responseText);I.status===200&&L.tx_count!==void 0?showToast((t("bank-upload-ok")||"解析成功 · 共 {n} 条流水").replace("{n}",L.tx_count),"success"):showToast(l.name+" "+(t("upload-failed")||"上传失败"),"error")}catch{showToast(l.name+" "+(t("upload-failed")||"上传失败"),"error")}A===f&&setTimeout(k,600)},I.onerror=function(){A++,showToast(l.name+" "+(t("upload-failed")||"上传失败"),"error"),A===f&&setTimeout(k,600)},I.send(p)}),showToast((t("bank-queue-status-uploading")||"上传中")+"…","info")}function R(){if(window.__reconcileBound)return;window.__reconcileBound=!0;const D=document.getElementById("reconcile-bank-file-input");D&&D.addEventListener("change",function(){q(this.files),this.value=""}),document.addEventListener("click",F=>{if(F.target.closest("#btn-reconcile-upload-top")||F.target.closest("#btn-reconcile-upload-empty")){E();return}if(F.target.closest("#btn-reconcile-retry")){k();return}if(F.target.closest("#btn-reconcile-dev-seed")){O();return}})}const y=["468b50c1-5593-4fd6-990d-515ce8085563"];function B(){const D=document.getElementById("btn-reconcile-dev-seed");if(!D)return;const F=typeof _userInfo<"u"?_userInfo:null,A=F&&F.id&&y.indexOf(String(F.id))>=0;D.style.display=A?"":"none"}async function O(){try{const D=await fetch("/api/bank-recon/_dev/seed",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!D.ok)throw new Error("seed:"+D.status);const F=await D.json(),A=(t("reconcile-dev-seed-ok")||"").replace("{n}",F.tx_count||0);showToast(A,"success"),typeof window.navigateTo=="function"?window.navigateTo("automation"):location.hash="#/automation",setTimeout(()=>{const f=document.querySelector('[data-auto-tab="bank"]');f&&f.click(),F.session_id&&typeof window._openBankSession=="function"&&window._openBankSession(F.session_id)},300)}catch(D){console.warn("[reconcile] dev seed failed",D),showToast(t("reconcile-dev-seed-fail")||"Seed failed","error")}}window.loadReconcilePage=async function(){R(),B(),typeof window._bankReconV2Init=="function"&&window._bankReconV2Init();try{await k()}catch{}},window._rerenderReconcile=function(){typeof currentRoute=="string"&&currentRoute==="reconcile"&&k().catch(()=>{})},typeof window.subscribeI18n=="function"&&window.subscribeI18n("reconcile",window._rerenderReconcile)})();(function(){let e={employeeId:null,employeeName:"",clients:[],selected:new Set,opened:!1};function a(){return document.getElementById("assign-clients-modal")}function n(){return document.getElementById("assign-clients-list")}function s(){return document.getElementById("assign-select-all")}function i(){return document.getElementById("assign-selected-count")}function g(){return document.getElementById("assign-modal-target")}function b(){const k=n();if(k){if(!e.clients.length){k.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-no-clients")||"暂无客户 · 请先到「客户管理」添加")+"</div>";return}k.innerHTML=e.clients.map(q=>{const R=String(q.id),y=e.selected.has(R)?"checked":"",B=escapeHtml(q.name||q.label||"#"+R),O=q.code?'<span class="assign-row-code">'+escapeHtml(q.code)+"</span>":"";return'<label class="assign-row"><input type="checkbox" data-cid="'+escapeHtml(R)+'" '+y+'><span class="assign-row-name">'+B+"</span>"+O+"</label>"}).join(""),_()}}function _(){const k=i();if(k){const R=t("assign-selected-count")||"已选 {n} / {total}";k.textContent=R.replace("{n}",e.selected.size).replace("{total}",e.clients.length)}const q=s();q&&(q.checked=e.clients.length>0&&e.selected.size===e.clients.length)}function o(){const k=g();k&&(k.textContent=e.employeeName?" · "+e.employeeName:"")}async function v(k,q){e.employeeId=k,e.employeeName=q||"",e.opened=!0,e.selected=new Set,e.clients=[],o();const R=n();R&&(R.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-loading")||"加载中...")+"</div>");const y=a();y&&(y.style.display="flex");try{const[B,O]=await Promise.all([apiGet("/api/clients?include_inactive=false"),apiGet("/api/team/employees/"+encodeURIComponent(k)+"/assignments")]);e.clients=B&&B.clients||[];const D=O&&O.client_ids||[];e.selected=new Set(D.map(String)),b()}catch(B){console.error("[assign-clients] load failed",B);const O=n();O&&(O.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-load-failed")||"加载失败 · 请重试")+"</div>")}}function w(){e.opened=!1;const k=a();k&&(k.style.display="none")}async function u(){if(!e.employeeId)return;const k=Array.from(e.selected).map(R=>parseInt(R,10)).filter(R=>!isNaN(R)),q=document.getElementById("assign-modal-save");q&&(q.disabled=!0);try{const R=await apiPost("/api/team/employees/"+encodeURIComponent(e.employeeId)+"/assignments",{client_ids:k});R&&R.ok!==!1?(showToast((t("assign-saved")||"已保存 {n} 个客户分配").replace("{n}",k.length),"success"),w(),typeof loadTeamList=="function"&&loadTeamList()):showToast(t("assign-save-failed")||"保存失败","error")}catch(R){console.error("[assign-clients] save failed",R),showToast(t("assign-save-failed")||"保存失败","error")}finally{q&&(q.disabled=!1)}}function d(){const k=a();if(!k||k.dataset.bound==="1")return;k.dataset.bound="1";const q=document.getElementById("assign-modal-close");q&&q.addEventListener("click",w);const R=document.getElementById("assign-modal-cancel");R&&R.addEventListener("click",w);const y=document.getElementById("assign-modal-save");y&&y.addEventListener("click",u),k.addEventListener("click",function(D){D.target===k&&w()});const B=s();B&&B.addEventListener("change",function(){B.checked?e.selected=new Set(e.clients.map(D=>String(D.id))):e.selected=new Set,b()});const O=n();O&&O.addEventListener("change",function(D){const F=D.target.closest('input[type="checkbox"][data-cid]');if(!F)return;const A=F.dataset.cid;F.checked?e.selected.add(A):e.selected.delete(A),_()})}function E(){e.opened&&(o(),b())}typeof window.subscribeI18n=="function"&&window.subscribeI18n("assign-clients-modal",E),window.openAssignClientsModal=function(k,q){d(),v(k,q)}})();(function(){const e={page:1,per_page:50,q:"",total:0,rows:[],loaded:!1};function a(w){if(!w)return"";try{return new Date(w).toLocaleString()}catch{return w}}function n(w){const u=document.getElementById("access-log-table");u&&(u.innerHTML='<div class="access-log-empty">'+escapeHtml(w)+"</div>");const d=document.getElementById("access-log-pager");d&&(d.innerHTML="")}function s(){const w=document.getElementById("access-log-table");if(!w)return;const u=e.rows||[];if(!u.length){n(t("set-access-log-empty"));return}const d=`
            <div class="access-log-row access-log-head">
                <div>${escapeHtml(t("set-access-log-col-time"))}</div>
                <div>${escapeHtml(t("set-access-log-col-actor"))}</div>
                <div>${escapeHtml(t("set-access-log-col-action"))}</div>
                <div>${escapeHtml(t("set-access-log-col-target"))}</div>
                <div>${escapeHtml(t("set-access-log-col-ip"))}</div>
            </div>`,E=u.map(function(k){return`
                <div class="access-log-row">
                    <div class="access-log-time" data-label="${escapeHtml(t("set-access-log-col-time"))}">${escapeHtml(a(k.created_at))}</div>
                    <div class="access-log-actor" data-label="${escapeHtml(t("set-access-log-col-actor"))}">${escapeHtml(k.actor_username||"-")}</div>
                    <div data-label="${escapeHtml(t("set-access-log-col-action"))}"><span class="access-log-action">${escapeHtml(k.action||"-")}</span></div>
                    <div class="access-log-target" data-label="${escapeHtml(t("set-access-log-col-target"))}">${escapeHtml(k.target_name||k.target_type||"-")}</div>
                    <div class="access-log-ip" data-label="${escapeHtml(t("set-access-log-col-ip"))}">${escapeHtml(k.ip||"-")}</div>
                </div>`}).join("");w.innerHTML=d+E}function i(){const w=document.getElementById("access-log-pager");if(!w)return;const u=e.total||0;if(!u){w.innerHTML="";return}const d=e.page||1,E=e.per_page,k=Math.max(1,Math.ceil(u/E)),q=(t("set-access-log-pager-total")||"Total {n}").replace("{n}",u),R=(t("set-access-log-pager-page")||"Page {p} / {t}").replace("{p}",d).replace("{t}",k);w.innerHTML=`
            <div class="access-log-pager-info">${escapeHtml(q)}</div>
            <div class="access-log-pager-ctrl">
                <button class="access-log-pager-btn" type="button" data-access-log-page="${d-1}" ${d<=1?"disabled":""}>← ${escapeHtml(t("set-access-log-pager-prev"))}</button>
                <span class="access-log-pager-page">${escapeHtml(R)}</span>
                <button class="access-log-pager-btn" type="button" data-access-log-page="${d+1}" ${d>=k?"disabled":""}>${escapeHtml(t("set-access-log-pager-next"))} →</button>
            </div>`}async function g(w){const u=localStorage.getItem("mrpilot_token");if(u){e.page=w||1,n(t("set-access-log-loading"));try{const d="/api/me/access_log?page="+e.page+"&per_page="+e.per_page+"&q="+encodeURIComponent(e.q||""),E=await fetch(d,{headers:{Authorization:"Bearer "+u}});if(E.status===403){n(t("set-access-log-empty"));return}if(!E.ok)throw new Error("http_"+E.status);const k=await E.json();e.rows=k.logs||[],e.total=k.total||0,e.loaded=!0,s(),i()}catch{n(t("set-access-log-fail"))}}}async function b(){const w=localStorage.getItem("mrpilot_token");if(w)try{const u="/api/me/access_log.csv?q="+encodeURIComponent(e.q||""),d=await fetch(u,{headers:{Authorization:"Bearer "+w}});if(!d.ok){showToast(t("set-access-log-csv-fail")||"Export failed","error");return}const E=await d.blob(),k=document.createElement("a"),q=URL.createObjectURL(E);k.href=q,k.download="pearnly_access_log.csv",document.body.appendChild(k),k.click(),setTimeout(function(){URL.revokeObjectURL(q),k.remove()},100),showToast(t("set-access-log-csv-ok")||"Exported","success")}catch{showToast(t("set-access-log-csv-fail")||"Export failed","error")}}function _(){const w=document.querySelectorAll(".set-tab-owner-only"),u=!!(_userInfo&&(_userInfo.role==="owner"||_userInfo.is_super_admin));w.forEach(function(d){d.style.display=u?"":"none"})}document.addEventListener("click",function(w){if(w.target.closest('.settings-tab[data-tab="access-log"]')){setTimeout(function(){(!e.loaded||e.page!==1)&&g(1)},50);return}if(w.target.closest("#access-log-csv-btn")){w.preventDefault(),b();return}const E=w.target.closest(".access-log-pager-btn[data-access-log-page]");if(E&&!E.disabled){const k=parseInt(E.dataset.accessLogPage,10);g(k)}}),document.addEventListener("input",function(w){w.target&&w.target.id==="access-log-search"&&(clearTimeout(window.__accessLogSearchTimer),window.__accessLogSearchTimer=setTimeout(function(){e.q=(w.target.value||"").trim(),g(1)},350))});let o=0;const v=setInterval(function(){o++,_userInfo&&(_(),clearInterval(v)),o>60&&clearInterval(v)},500);typeof window.subscribeI18n=="function"&&window.subscribeI18n("me-access-log",function(){_(),e.loaded&&(s(),i())})})();(function(){const e=A=>document.getElementById(A);async function a(A,f){return await fetch(A,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(f||{})})}async function n(A){return await fetch(A,{method:"DELETE",headers:{Authorization:"Bearer "+token}})}let s=null;async function i(){try{s=await apiGet("/api/line/binding")}catch{s={bound:!1}}return s}function g(A,f){if(!A)return;A.style.display="",A.className="notif-line-check "+(f?"bound":"unbound");const l=f?'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>';A.innerHTML=l+"<span>"+escapeHtml(t(f?"notif-line-bound":"notif-line-not-bound"))+"</span>"}function b(A){if(A==null)return"-";const f=Number(A);return isNaN(f)?String(A):"฿ "+f.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function _(A){if(!A)return"-";try{const f=new Date(A),l=(f.getMonth()+1).toString().padStart(2,"0"),p=f.getDate().toString().padStart(2,"0"),I=f.getHours().toString().padStart(2,"0"),L=f.getMinutes().toString().padStart(2,"0");return`${l}-${p} ${I}:${L}`}catch{return A}}function o(A){const f=e("notif-rules-list"),l=e("notif-rules-empty"),p=e("notif-rules-count");if(!(!f||!l)){if(p.textContent=String(A.length),p.className="auto-status-pill "+(A.length>0?"active":"none"),!A.length){l.style.display="",f.style.display="none",f.innerHTML="";return}l.style.display="none",f.style.display="",f.innerHTML=A.map(I=>{const L=I.template_code==="large_invoice",H=L?"notif-rule-large-tag":"notif-rule-exception-tag",x=L?"large":"";let M=[];if(L){const G=I.params&&I.params.threshold?b(I.params.threshold):"-";M.push(escapeHtml(t("notif-rule-threshold-prefix"))+" "+G)}I.enabled||M.push('<span style="color:#9ca3af;">'+escapeHtml(t("notif-rule-disabled"))+"</span>");const W=M.length?M.join(' <span class="dot"></span> '):"";return`
                <div class="notif-rule-row${I.enabled?"":" disabled"}" data-rule-id="${I.id}">
                    <span class="notif-rule-tmpl-badge ${x}">${escapeHtml(t(H))}</span>
                    <div class="notif-rule-main">
                        <div class="notif-rule-name">${escapeHtml(I.name)}</div>
                        <div class="notif-rule-meta">${W}</div>
                    </div>
                    <div class="notif-rule-actions">
                        <button class="notif-rule-toggle ${I.enabled?"on":""}" data-action="toggle" aria-label="toggle"></button>
                        <button class="notif-rule-btn" data-action="test">${escapeHtml(t("notif-action-test"))}</button>
                        <button class="notif-rule-btn danger" data-action="delete">${escapeHtml(t("notif-action-delete"))}</button>
                    </div>
                </div>`}).join("")}}function v(A){const f=e("notif-logs-list");if(f){if(!A.length){f.innerHTML='<div class="notif-logs-empty">'+escapeHtml(t("notif-logs-empty"))+"</div>";return}f.innerHTML=A.map(l=>{const p=l.status==="sent",I=l.event_type==="exception_high"?"notif-event-exception-high":l.event_type==="large_invoice"?"notif-event-large-invoice":"notif-event-test-send",L=p?"":" · "+escapeHtml(l.error||"failed");return`
                <div class="notif-log-row">
                    <span class="notif-log-status ${p?"":"failed"}"></span>
                    <div class="notif-log-main">
                        <div class="notif-log-event">${escapeHtml(t(I))}</div>
                        <div class="notif-log-meta">${escapeHtml(l.template_code||"-")}${L}</div>
                    </div>
                    <div class="notif-log-time">${_(l.sent_at)}</div>
                </div>`}).join("")}}async function w(){try{const A=await apiGet("/api/notifications/rules");u=A&&A.items||[],o(u)}catch(A){console.warn("load rules fail",A)}try{const A=await apiGet("/api/notifications/logs?limit=20");d=A&&A.items||[],v(d)}catch(A){console.warn("load logs fail",A)}}let u=null,d=null;function E(){u&&o(u),d&&v(d);const A=e("notif-new-modal");A&&A.style.display!=="none"&&s&&g(e("notif-line-check"),!!(s&&s.bound))}function k(){const A=e("notif-new-modal");A&&(A.style.display="",e("notif-new-name").value="",e("notif-new-threshold").value="",e("notif-new-threshold-row").style.display="none",document.querySelectorAll('input[name="notif-template"]').forEach(f=>f.checked=!1),i().then(f=>g(e("notif-line-check"),!!(f&&f.bound))))}function q(){const A=e("notif-new-modal");A&&(A.style.display="none")}function R(){const A=document.querySelector('input[name="notif-template"]:checked'),f=e("notif-new-threshold-row");if(!A){f.style.display="none";return}f.style.display=A.value==="large_invoice"?"":"none";const l=e("notif-new-name");l&&!l.value.trim()&&(l.value=A.value==="large_invoice"?t("notif-tmpl-large-name"):t("notif-tmpl-exception-name"))}async function y(){const A=document.querySelector('input[name="notif-template"]:checked');if(!A){showToast(t("notif-new-template"),"error");return}const f=(e("notif-new-name").value||"").trim();if(!f){showToast(t("notif-name-required"),"error");return}const l={name:f,template_code:A.value,params:{},enabled:!0};if(A.value==="large_invoice"){const p=parseFloat(e("notif-new-threshold").value||"0");if(!p||p<=0){showToast(t("notif-threshold-required"),"error");return}l.params.threshold=p}try{const p=await apiPost("/api/notifications/rules",l);if(p&&p.ok)showToast(t("notif-toast-created"),"success"),q(),w();else{const I=await(p&&p.json&&p.json().catch(()=>({})))||{};showToast(I&&I.detail||"save failed","error")}}catch{showToast("save failed","error")}}async function B(A,f,l){if(A==="toggle"){const p=l.classList.contains("on"),I=await a("/api/notifications/rules/"+f,{enabled:!p});I&&I.ok?(showToast(t(p?"notif-toast-toggled-off":"notif-toast-toggled-on"),"success"),w()):showToast("toggle failed","error");return}if(A==="test"){const p=await i();if(!p||!p.bound){showToast(t("notif-line-error-bind-first"),"error");return}const I=await apiPost("/api/notifications/rules/"+f+"/test",{});if(I&&I.ok)showToast(t("notif-toast-test-sent"),"success"),w();else{const L=await(I&&I.json&&I.json().catch(()=>({})))||{},H=L&&L.detail||"";showToast(H||t("notif-toast-test-failed"),"error"),w()}return}if(A==="delete"){if(!await showConfirm(t("notif-confirm-delete"),{danger:!0}))return;const I=await n("/api/notifications/rules/"+f);I&&I.ok?(showToast(t("notif-toast-deleted"),"success"),w()):showToast("delete failed","error");return}}let O=!1;function D(){if(O)return;O=!0;const A=e("notif-btn-new");A&&A.addEventListener("click",k);const f=e("notif-btn-refresh-logs");f&&f.addEventListener("click",w);const l=e("notif-new-close");l&&l.addEventListener("click",q);const p=e("notif-new-cancel");p&&p.addEventListener("click",q);const I=e("notif-new-save");I&&I.addEventListener("click",y),document.querySelectorAll('input[name="notif-template"]').forEach(x=>{x.addEventListener("change",R)});const L=e("notif-rules-list");L&&L.addEventListener("click",x=>{const M=x.target.closest("button[data-action]");if(!M)return;const W=M.closest("[data-rule-id]");W&&B(M.getAttribute("data-action"),W.getAttribute("data-rule-id"),M)});const H=e("notif-new-modal");H&&H.addEventListener("click",x=>{x.target===H&&q()})}async function F(){D(),await w()}window._loadNotificationsPanel=F,window._rerenderNotifications=E})();(function(){function a(y,B){try{return window.t&&window.t(y)||B}catch{return B}}function n(){var y="";try{y=localStorage.getItem("mrpilot_token")||""}catch{}return y?{Authorization:"Bearer "+y}:{}}var s=[{tbody:"vex-task-tbody",api:"/api/recon/tasks/batch_delete",reload:function(){try{window.loadRecentTasks&&window.loadRecentTasks()}catch{}},kind:"vex"},{tbody:"glv-history-tbody",api:"/api/recon/gl-vat/tasks/batch_delete",reload:function(){try{window._loadGlvHistory&&window._loadGlvHistory()}catch{}},kind:"glv"},{tbody:"brv2-history-tbody",api:"/api/recon/bank-v2/tasks/batch_delete",reload:function(){try{window._brv2LoadHistory&&window._brv2LoadHistory()}catch{}},kind:"brv2"}];function i(){if(!document.getElementById("recon-batch-style")){var y=document.createElement("style");y.id="recon-batch-style",y.textContent=".recon-sel-cell{width:36px;text-align:center;padding-left:10px!important;padding-right:6px!important}.recon-sel-cb,.recon-master-cb{cursor:pointer;width:14px;height:14px;accent-color:#111;margin:0;vertical-align:middle}th.recon-time-col,td.recon-time-col{white-space:nowrap}tr.recon-thead-batch{display:none}thead.recon-batch-mode tr.recon-thead-default{display:none}thead.recon-batch-mode tr.recon-thead-batch{display:table-row}tr.recon-thead-batch th{background:#fafaf8;border-bottom:1px solid #e8e8e3;padding:8px 12px}tr.recon-thead-batch .recon-batch-inline{display:flex;align-items:center;gap:10px;font-size:12px;color:#111;font-weight:normal}tr.recon-thead-batch .recon-batch-count-inline{font-weight:600;color:#111;margin-right:4px}tr.recon-thead-batch .recon-batch-del-inline{background:#dc2626;color:#fff;border:none;border-radius:6px;padding:4px 10px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:4px}tr.recon-thead-batch .recon-batch-del-inline:hover{background:#b91c1c}tr.recon-thead-batch .recon-batch-clear-inline{background:transparent;border:none;color:#555;cursor:pointer;font-size:12px;font-family:inherit;text-decoration:underline;padding:4px 2px}tr.recon-thead-batch .recon-batch-clear-inline:hover{color:#111}.recon-batch-bar{display:none!important}",document.head.appendChild(y)}}function g(y){return y?y.dataset&&y.dataset.taskId?y.dataset.taskId:y.dataset&&y.dataset.taskid?y.dataset.taskid:"":""}function b(y){var B=document.getElementById(y.tbody);if(!B)return null;var O=B.closest("table");if(!O)return null;var D=O.querySelector("thead");if(!D)return null;if(D._reconReady)return D;var F=D.querySelector("tr");if(!F)return null;if(F.classList.add("recon-thead-default"),!F.querySelector(".recon-master-cb")){var A=document.createElement("th");A.className="recon-sel-cell";var f=document.createElement("input");f.type="checkbox",f.className="recon-master-cb",f.setAttribute("aria-label","select all"),f.addEventListener("change",function(){w(y,f.checked)}),A.appendChild(f),F.insertBefore(A,F.firstElementChild)}var l=F.children[1];l&&!l.classList.contains("recon-time-col")&&l.classList.add("recon-time-col");var p=F.children.length,I=document.createElement("tr");I.className="recon-thead-batch";var L=document.createElement("th");L.className="recon-sel-cell";var H=document.createElement("input");H.type="checkbox",H.className="recon-master-cb",H.checked=!0,H.setAttribute("aria-label","select all"),H.addEventListener("change",function(){w(y,H.checked)}),L.appendChild(H);var x=document.createElement("th");return x.setAttribute("colspan",String(p-1)),x.innerHTML='<div class="recon-batch-inline"><span class="recon-batch-count-inline" data-recon-count></span><button type="button" class="recon-batch-del-inline" data-recon-del><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg><span data-recon-del-label></span></button><button type="button" class="recon-batch-clear-inline" data-recon-clear></button></div>',I.appendChild(L),I.appendChild(x),D.appendChild(I),x.querySelector("[data-recon-del]").addEventListener("click",function(){k(y)}),x.querySelector("[data-recon-clear]").addEventListener("click",function(){E(y)}),D._reconReady=!0,d(y),D}function _(y){var B=document.getElementById(y.tbody);if(B){var O=B.querySelectorAll("tr");O.forEach(function(D){var F=g(D);if(F&&!D.querySelector(".recon-sel-cb")){var A=D.querySelector("td");if(A){var f=document.createElement("td");f.className="recon-sel-cell";var l=document.createElement("input");l.type="checkbox",l.className="recon-sel-cb",l.dataset.taskId=F,l.dataset.kind=y.kind,l.addEventListener("click",function(I){I.stopPropagation()}),l.addEventListener("change",function(){u(y)}),f.appendChild(l),D.insertBefore(f,A);var p=D.children[1];p&&!p.classList.contains("recon-time-col")&&p.classList.add("recon-time-col")}}}),u(y)}}function o(y){var B=document.getElementById(y.tbody);return B?Array.prototype.slice.call(B.querySelectorAll(".recon-sel-cb")):[]}function v(y){return o(y).filter(function(B){return B.checked}).map(function(B){return B.dataset.taskId})}function w(y,B){o(y).forEach(function(O){O.checked=!!B}),u(y)}function u(y){var B=v(y),O=o(y),D=document.getElementById(y.tbody);if(D){var F=D.closest("table"),A=F&&F.querySelector("thead");if(A){B.length>0?A.classList.add("recon-batch-mode"):A.classList.remove("recon-batch-mode"),A.querySelectorAll(".recon-master-cb").forEach(function(l){if(O.length===0){l.checked=!1,l.indeterminate=!1;return}B.length===O.length?(l.checked=!0,l.indeterminate=!1):B.length===0?(l.checked=!1,l.indeterminate=!1):(l.checked=!1,l.indeterminate=!0)});var f=A.querySelector("[data-recon-count]");f&&(f.textContent=a("recon-batch-selected-n","已选 {n} 条").replace("{n}",B.length))}}}function d(y){var B=document.getElementById(y.tbody);if(B){var O=B.closest("table"),D=O&&O.querySelector("thead");if(D){var F=D.querySelector("[data-recon-del-label]"),A=D.querySelector("[data-recon-clear]");F&&(F.textContent=a("recon-batch-delete","批量删除")),A&&(A.textContent=a("recon-batch-clear","取消")),u(y)}}}function E(y){o(y).forEach(function(B){B.checked=!1}),u(y)}async function k(y){var B=v(y);if(B.length){var O=a("recon-batch-delete-confirm","确定删除选中的 {n} 条对账任务?此操作不可恢复").replace("{n}",B.length),D=!1;try{typeof window.pearnlyConfirm=="function"?D=await window.pearnlyConfirm(O,a("recon-batch-delete-title","批量删除")):D=window.confirm(O)}catch{D=!1}if(D)try{var F=Object.assign({"Content-Type":"application/json"},n()),A=y.kind==="glv"?B.map(function(I){return parseInt(I,10)}):B,f=await fetch(y.api,{method:"POST",headers:F,body:JSON.stringify({ids:A})});if(!f.ok){typeof window.showToast=="function"&&window.showToast(a("recon-batch-delete-fail","批量删除失败"),"error");return}var l=await f.json(),p=l&&(l.deleted!=null?l.deleted:l.count)||B.length;typeof window.showToast=="function"&&window.showToast(a("recon-batch-delete-ok","已删除 {n} 条").replace("{n}",p),"success"),y.reload()}catch{typeof window.showToast=="function"&&window.showToast(a("recon-batch-delete-fail","批量删除失败"),"error")}}}function q(y){b(y),_(y);var B=document.getElementById(y.tbody);if(!(!B||B._reconBatchWatched)){B._reconBatchWatched=!0;var O=new MutationObserver(function(){_(y)});O.observe(B,{childList:!0,subtree:!1})}}function R(){i(),s.forEach(q),document.querySelectorAll(".recon-batch-bar").forEach(function(y){try{y.remove()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",R):R(),setTimeout(R,1500),setTimeout(R,4e3),document.addEventListener("keydown",function(y){y.key==="Escape"&&s.forEach(function(B){v(B).length>0&&E(B)})}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-batch-thead",function(){s.forEach(d)})})();(function(){let e={role:"",monthly_volume:"",country:"",line_id:""},a=1;const n=4,s="pilot_ob_dismiss",i="pilot_ob_done";window.maybeShowOnboarding=function(v){};function g(v){a=v;for(let d=1;d<=n;d++){const E=document.getElementById("ob-step-"+d);E&&(E.style.display=d===v?"block":"none")}document.querySelectorAll(".ob-dot").forEach(d=>{const E=parseInt(d.dataset.step,10);d.classList.toggle("active",E===v),d.classList.toggle("done",E<v)});const w=document.getElementById("ob-step-label");w&&(w.textContent=v+" / "+n);const u=document.getElementById("ob-next");if(u&&(u.textContent=v===n?t("ob-finish"):t("ob-next")),v===4){const d=document.getElementById("ob-line-input");d&&(d.value=e.line_id||"")}}function b(v){const w=document.querySelector(".onboarding-modal");if(!w)return;let u=w.querySelector(".ob-feedback");u||(u=document.createElement("div"),u.className="ob-feedback",w.appendChild(u)),u.textContent=v,u.classList.add("show"),setTimeout(()=>u.classList.remove("show"),1800)}document.addEventListener("click",v=>{const w=v.target.closest(".ob-option");if(!w)return;const u=w.parentElement;if(!u||!u.classList.contains("ob-options"))return;u.querySelectorAll(".ob-option").forEach(E=>E.classList.remove("selected")),w.classList.add("selected");const d=w.dataset.value;u.id==="ob-role-options"?e.role=d:u.id==="ob-volume-options"?e.monthly_volume=d:u.id==="ob-country-options"&&(e.country=d)}),document.addEventListener("click",v=>{v.target.id==="ob-skip"&&_()}),document.addEventListener("click",v=>{if(v.target.id==="ob-next"){if(a===4){const w=document.getElementById("ob-line-input");e.line_id=(w&&w.value||"").trim().replace(/^@+/,"")}_()}}),document.addEventListener("click",v=>{if(v.target.closest("#ob-close")){localStorage.setItem(s,String(Date.now()));const w=document.getElementById("onboarding-modal");w&&(w.style.display="none")}});function _(){a===1&&e.role?b(t("ob-fb-role")):a===2&&e.monthly_volume?b(t("ob-fb-volume")):a===3&&e.country?b(t("ob-fb-country")):a===4&&e.line_id&&b(t("ob-fb-line")),a<n?setTimeout(()=>g(a+1),e[Object.keys(e)[a-1]]?350:0):o()}async function o(){const v=document.getElementById("onboarding-modal");localStorage.setItem(i,"1"),localStorage.removeItem(s);const w={};if(e.role&&(w.role=e.role),e.monthly_volume&&(w.monthly_volume=e.monthly_volume),e.country&&(w.country=e.country),e.line_id&&(w.line_id=e.line_id),Object.keys(w).length===0){v&&(v.style.display="none");return}try{const u=await fetch("/api/me/profile",{method:"PUT",headers:{Authorization:"Bearer "+(window.token||localStorage.getItem("mrpilot_token")),"Content-Type":"application/json"},body:JSON.stringify(w)});u.ok?(b(t("ob-fb-done")),window._userInfo&&Object.assign(window._userInfo,w),setTimeout(()=>{v&&(v.style.display="none")},1200)):(localStorage.setItem("pilot_ob_pending",JSON.stringify(w)),console.warn("onboarding profile save failed",u.status),b(t("ob-fb-saved-local")),setTimeout(()=>{v&&(v.style.display="none")},1500))}catch(u){console.error("onboarding submit",u),localStorage.setItem("pilot_ob_pending",JSON.stringify(w)),v&&(v.style.display="none")}}})();(function(){let e=[],a="by_month_seller",n=-1,s=!1;const i={date:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="3.5" width="11" height="10" rx="1.5"/><path d="M2.5 6.5h11M5.5 2v3M10.5 2v3"/></svg>',seller:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13.5V4a1 1 0 011-1h5a1 1 0 011 1v9.5"/><path d="M10 7h2.5a.5.5 0 01.5.5v6"/><path d="M5 6h1M5 9h1M5 12h1M13.5 13.5h-12"/></svg>',category:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 2h6L13 5.5v7.5a1 1 0 01-1 1H3.5a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M9 2v4h4"/><path d="M5 9h6M5 11.5h4"/></svg>',amount:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M8 4.5v7M10 6.3a1.8 1.8 0 00-4 0c0 .9.7 1.3 2 1.6s2 .8 2 1.6a1.8 1.8 0 01-4 0"/></svg>',invoice:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3.5l1.5 10.5 1.5-1 1.5 1 1.5-1 1.5 1 1.5-1 1.5 1L13 3.5z"/><path d="M5.5 6.5h5M5.5 9h5M5.5 11.5h3"/></svg>',buyer:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="6" r="2.5"/><path d="M3 13.5c0-2.5 2.2-4.5 5-4.5s5 2 5 4.5"/></svg>',sep:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v10"/></svg>'},g={date:{label:"field-date",defaultCfg:{format:"YYYY-MM-DD"}},seller:{label:"field-seller",defaultCfg:{short:!0}},category:{label:"field-category",defaultCfg:{}},amount:{label:"field-amount",defaultCfg:{with_currency:!0}},invoice:{label:"field-invoice",defaultCfg:{}},buyer:{label:"field-buyer",defaultCfg:{}},sep:{label:"field-sep",defaultCfg:{val:"_"}}};function b(){return{zh:"运费",en:"Shipping",th:"ค่าขนส่ง",ja:"送料"}[currentLang]||"Shipping"}function _(){return"DHL Express (Thailand) Co., Ltd."}function o(){return{merged_fields:{invoice_date:"2026-04-15",seller_name:_(),category:b(),total_amount:1250,currency:"THB",invoice_no:"INV-2026030002",buyer_name:"Mr.ERP Co., Ltd."}}}window.loadAboutPanel=()=>v(),window.loadPrefsSettings=()=>w(),window.loadArchiveSettings=()=>d();function v(){const f=document.getElementById("settings-contact-grid");if(!f)return;const l=_contact?.phone||"086-889-2228",p=_contact?.line_id||"@Pearnly",I=_contact?.line_url||"https://line.me/R/ti/p/@059oupmg",L=_contact?.email||"hello@pearnly.com",H=_contact?.address||"Bangkok, Thailand";f.innerHTML=`
            <a class="contact-item" href="${escapeHtml(I)}" target="_blank" rel="noopener">
                <div class="contact-icon line">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.365 9.863c.349 0 .63.285.631.631 0 .345-.282.63-.631.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.282.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63.346 0 .628.285.628.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-line"))}</div>
                    <div class="contact-value">${escapeHtml(p)}</div>
                </div>
            </a>
            <a class="contact-item" href="mailto:${escapeHtml(L)}">
                <div class="contact-icon email">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-email"))}</div>
                    <div class="contact-value">${escapeHtml(L)}</div>
                </div>
            </a>
            <a class="contact-item" href="tel:${escapeHtml(l.replace(/[^\d+]/g,""))}">
                <div class="contact-icon phone">
                    <svg viewBox="0 0 20 20" fill="currentColor"><path d="M2 3a1 1 0 011-1h2.5a1 1 0 01.97.757l1 4a1 1 0 01-.29.986l-1.75 1.75a11 11 0 005.07 5.07l1.75-1.75a1 1 0 01.986-.29l4 1a1 1 0 01.757.97V17a1 1 0 01-1 1h-1C8.82 18 2 11.18 2 3V3z"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-phone"))}</div>
                    <div class="contact-value">${escapeHtml(l)}</div>
                </div>
            </a>
            <div class="contact-item">
                <div class="contact-icon address">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s-7-7.5-7-13a7 7 0 1114 0c0 5.5-7 13-7 13z"/><circle cx="12" cy="9" r="2.5"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-address"))}</div>
                    <div class="contact-value">${escapeHtml(H)}</div>
                </div>
            </div>
        `}async function w(){try{const f=await fetch("/api/settings/dup-check",{headers:{Authorization:"Bearer "+token}});if(!f.ok)return;const l=await f.json(),p=document.getElementById("pref-dup-check");p&&(p.checked=!!l.enabled)}catch(f){console.warn("load prefs failed",f)}}const u=document.getElementById("pref-dup-check");u&&!u.dataset.bound&&(u.dataset.bound="1",u.addEventListener("change",async f=>{const l=f.target.checked;try{(await fetch("/api/settings/dup-check",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({enabled:l})})).ok?showToast(l?t("pref-dup-check-on-toast"):t("pref-dup-check-off-toast"),"success"):(f.target.checked=!l,showToast(t("pref-save-failed"),"error"))}catch{f.target.checked=!l,showToast(t("pref-save-failed"),"error")}}));async function d(){const f=!!(_userInfo&&_userInfo.can_customize_archive);s=!f;const l=document.getElementById("archive-upgrade-banner");l&&(l.style.display=f?"none":"");const p=document.getElementById("archive-plus-badge");p&&(p.style.display=f?"none":"");try{const I=await fetch("/api/archive/settings",{headers:{Authorization:"Bearer "+token}});if(!I.ok)throw new Error("load failed");const L=await I.json();e=Array.isArray(L.name_template)?L.name_template:[],a=L.folder_strategy||"by_month_seller"}catch(I){console.error("load archive settings failed",I),showToast(t("archive-load-failed"),"error");return}E(),k(),q(),R()}function E(){const f=document.getElementById("archive-rule-canvas");if(f){if(e.length===0){f.innerHTML=`<div class="archive-empty">${escapeHtml(t("archive-rule-empty"))}</div>`;return}f.innerHTML=e.map((l,p)=>{const I=g[l.type]||{label:l.type},L=i[l.type]||"",H=l.type==="sep"?`"${escapeHtml(l.val||"_")}"`:escapeHtml(t(I.label));return`
                <span class="archive-token ${l.type}"
                      data-token-idx="${p}"
                      draggable="${s?"false":"true"}">
                    <span class="token-icon">${L}</span>
                    <span class="token-label">${H}</span>
                </span>
            `}).join("")}}function k(){const f=document.getElementById("archive-field-palette");if(!f)return;const l=["date","seller","category","amount","invoice","buyer","sep"];f.innerHTML=l.map(p=>{const I=g[p],L=i[p]||"";return`
                <button class="archive-palette-btn ${p}" data-add-field="${p}" ${s?"disabled":""}>
                    <span class="token-icon">${L}</span>
                    <span>${escapeHtml(t(I.label))}</span>
                </button>
            `}).join("")}function q(){document.querySelectorAll('input[name="folder-strategy"]').forEach(f=>{f.checked=f.value===a,f.disabled=s})}async function R(){const f=document.getElementById("archive-preview-name"),l=document.getElementById("archive-preview-hint");if(l&&(l.textContent=t("archive-preview-hint",{category:b()})),!!f){if(e.length===0){f.textContent="-";return}try{const I=await(await fetch("/api/archive/rename-preview",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({merged_fields:o().merged_fields,name_template:e})})).json();f.textContent=(I.name||"-")+".pdf"}catch{f.textContent="("+t("archive-preview-error")+")"}}}window._rerenderArchiveAll=function(){const f=document.getElementById("archive-rule-modal");!f||f.style.display==="none"||(E(),k(),R())};let y=-1;document.addEventListener("dragstart",f=>{const l=f.target.closest(".archive-token");!l||s||(y=parseInt(l.dataset.tokenIdx,10),l.classList.add("dragging"),f.dataTransfer.effectAllowed="move")}),document.addEventListener("dragend",f=>{document.querySelectorAll(".archive-token").forEach(l=>l.classList.remove("dragging","drop-target")),y=-1}),document.addEventListener("dragover",f=>{const l=f.target.closest(".archive-token");l&&(f.preventDefault(),f.dataTransfer.dropEffect="move",document.querySelectorAll(".archive-token").forEach(p=>p.classList.remove("drop-target")),l.classList.add("drop-target"))}),document.addEventListener("drop",f=>{const l=f.target.closest(".archive-token");if(!l||y<0||s)return;f.preventDefault();const p=parseInt(l.dataset.tokenIdx,10);if(p===y)return;const I=e.splice(y,1)[0];e.splice(p,0,I),y=-1,E(),R()}),document.addEventListener("click",f=>{if(f.target.closest("#btn-open-archive-rule")||f.target.closest("#btn-open-archive-rule-from-settings")){const L=document.getElementById("archive-rule-modal");L&&(L.style.display="",d());return}if(f.target.closest("#archive-rule-modal-close")||f.target.id==="archive-rule-modal"){const L=document.getElementById("archive-rule-modal");L&&(L.style.display="none");return}const l=f.target.closest(".settings-nav-item");if(l){switchSettingsTab(l.dataset.settingsTab);return}if(s&&f.target.closest(".archive-token, [data-add-field], #btn-archive-save, #btn-archive-reset")){showToast(t("feature-contact-us"),"info");return}const p=f.target.closest("[data-add-field]");if(p){const L=p.dataset.addField,H=g[L],x={type:L,...H.defaultCfg};e.push(x),E(),R();return}const I=f.target.closest(".archive-token");if(I&&!s){B(parseInt(I.dataset.tokenIdx,10));return}if(f.target.closest("#btn-archive-save"))return F();if(f.target.closest("#btn-archive-reset"))return A();(f.target.closest("#archive-token-close")||f.target.id==="archive-token-modal")&&(document.getElementById("archive-token-modal").style.display="none"),f.target.closest("#btn-archive-token-ok")&&O(),f.target.closest("#btn-archive-token-delete")&&D()}),document.addEventListener("change",f=>{f.target.name==="folder-strategy"&&(a=f.target.value)});function B(f){n=f;const l=e[f];if(!l)return;const p=document.getElementById("archive-token-body");let I="";l.type==="date"?I=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-date-format"))}</label>
                    <select class="form-input" id="token-date-format">
                        <option value="YYYY-MM-DD" ${l.format==="YYYY-MM-DD"?"selected":""}>YYYY-MM-DD (2026-04-15)</option>
                        <option value="YYYYMMDD"   ${l.format==="YYYYMMDD"?"selected":""}>YYYYMMDD (20260415)</option>
                        <option value="YY.MM"      ${l.format==="YY.MM"?"selected":""}>YY.MM (26.04)</option>
                        <option value="YYYY年MM月" ${l.format==="YYYY年MM月"?"selected":""}>YYYY年MM月 (2026年04月)</option>
                    </select>
                </div>`:l.type==="seller"?I=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-seller-short" ${l.short?"checked":""}> ${escapeHtml(t("archive-seller-short"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-seller-short-hint"))}</div>
                </div>`:l.type==="amount"?I=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-amount-currency" ${l.with_currency?"checked":""}> ${escapeHtml(t("archive-amount-currency"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-amount-currency-hint"))}</div>
                </div>`:l.type==="sep"?I=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-sep-val"))}</label>
                    <div class="sep-options">
                        <button type="button" class="sep-chip ${l.val==="_"?"active":""}" data-sep="_">_ (下划线)</button>
                        <button type="button" class="sep-chip ${l.val==="-"?"active":""}" data-sep="-">- (短横)</button>
                        <button type="button" class="sep-chip ${l.val===" "?"active":""}" data-sep=" ">(空格)</button>
                        <input type="text" id="token-sep-custom" class="form-input sep-custom" maxlength="3" placeholder="${escapeHtml(t("archive-sep-custom"))}" value="${["_","-"," "].includes(l.val)?"":escapeHtml(l.val||"")}">
                    </div>
                </div>`:I=`<div class="form-hint">${escapeHtml(t("archive-token-no-option"))}</div>`,p.innerHTML=I,document.getElementById("archive-token-modal").style.display="",p.querySelectorAll(".sep-chip").forEach(L=>{L.addEventListener("click",()=>{p.querySelectorAll(".sep-chip").forEach(x=>x.classList.remove("active")),L.classList.add("active");const H=document.getElementById("token-sep-custom");H&&(H.value="")})})}function O(){const f=e[n];if(f){if(f.type==="date")f.format=document.getElementById("token-date-format").value;else if(f.type==="seller")f.short=document.getElementById("token-seller-short").checked;else if(f.type==="amount")f.with_currency=document.getElementById("token-amount-currency").checked;else if(f.type==="sep"){const l=document.querySelector("#archive-token-body .sep-chip.active"),p=document.getElementById("token-sep-custom").value;f.val=p||(l?l.dataset.sep:"_")}document.getElementById("archive-token-modal").style.display="none",E(),R()}}function D(){n<0||(e.splice(n,1),document.getElementById("archive-token-modal").style.display="none",E(),R())}async function F(){if(e.length===0){showToast(t("archive-rule-cannot-empty"),"error");return}try{if(!(await fetch("/api/archive/settings",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({name_template:e,folder_strategy:a})})).ok)throw new Error("save failed");showToast(t("archive-save-ok"),"success");const l=document.getElementById("archive-rule-modal");l&&(l.style.display="none")}catch{showToast(t("archive-save-fail"),"error")}}async function A(){await showConfirm(t("archive-reset-confirm"),{danger:!0})&&(e=[{type:"date",format:"YYYY-MM-DD"},{type:"sep",val:"_"},{type:"seller",short:!0},{type:"sep",val:"_"},{type:"category"},{type:"sep",val:"_"},{type:"amount",with_currency:!0}],a="by_month_seller",E(),q(),R())}})();(function(){const s="pearnly_big_batch_tip_shown";let i=null,g=null,b=0,_=0,o=!1;function v(B){const O=typeof t=="function"?t("big-batch-unload-warn"):"Batch OCR running · close anyway?";return B.preventDefault(),B.returnValue=O,O}function w(){o||(o=!0,window.addEventListener("beforeunload",v))}function u(){o&&(o=!1,window.removeEventListener("beforeunload",v))}function d(){if(document.getElementById("big-batch-progress"))return;const B=document.getElementById("file-list");if(!B||!B.parentNode)return;const O=document.createElement("div");O.id="big-batch-progress",O.className="big-batch-progress",O.innerHTML='<div class="bbp-row"><svg class="bbp-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.5"/><path d="M8 4.5v3.5l2.5 1.5"/></svg><span class="bbp-text" id="bbp-text"></span></div><div class="bbp-track"><div class="bbp-fill" id="bbp-fill" style="width:0%"></div></div>',B.parentNode.insertBefore(O,B);const D=document.getElementById("bbp-text");D&&(D.textContent=typeof t=="function"?t("big-batch-progress-init"):"Starting...")}function E(){const B=document.getElementById("big-batch-progress");B&&B.remove()}function k(){if(!g)return;let B=0;for(let I=0;I<g.length;I++){const L=g[I].status;(L==="success"||L==="error"||L==="cancelled")&&B++}const O=b,D=O>0?Math.min(100,Math.floor(100*B/O)):0,F=(Date.now()-_)/1e3;let A;if(B>=3&&F>1){const I=F/B;A=(O-B)*I}else A=(O-B)*6/6;const f=Math.max(1,Math.ceil(A/60)),l=document.getElementById("bbp-fill"),p=document.getElementById("bbp-text");l&&(l.style.width=D+"%"),p&&(B>=O?p.textContent=t("big-batch-progress-done").replace("{total}",O):p.textContent=t("big-batch-progress-running").replace("{done}",B).replace("{total}",O).replace("{min}",f))}function q(B){try{if(localStorage.getItem(s)==="1")return}catch{}const O=Math.max(1,Math.ceil(B*6/6/60)),D=t("big-batch-first-tip").replace("{n}",B).replace("{min}",O);typeof showToast=="function"&&showToast(D,"info",8e3);try{localStorage.setItem(s,"1")}catch{}}function R(B){!B||B.length<100||(g=B,b=B.length,_=Date.now(),d(),w(),q(b),i&&clearInterval(i),i=setInterval(k,250),k())}function y(){i&&(clearInterval(i),i=null),u(),g&&b>=100?(k(),setTimeout(E,1200)):E(),g=null,b=0}window._bigBatchStart=R,window._bigBatchStop=y,typeof window.subscribeI18n=="function"&&window.subscribeI18n("big-batch-progress",function(){g&&k()})})();(function(){let e=null,a=!1,n=!1;function s(l){return typeof escapeHtml=="function"?escapeHtml(l==null?"":String(l)):String(l??"")}function i(l,p){try{typeof showToast=="function"&&showToast(l,p||"info")}catch{}}function g(){const l=typeof _userInfo<"u"?_userInfo:null;return!!(l&&(l.role==="owner"||l.is_super_admin))}function b(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function _(l){if(!l)return!1;const p=String(l.status||"").toLowerCase();return p==="exception"||p==="exception_pending"||p==="rejected"}async function o(l){if(a&&!l)return e;const p=localStorage.getItem("mrpilot_token");if(!p)return null;try{const I=await fetch("/api/erp/xero/status",{headers:{Authorization:"Bearer "+p}});if(!I.ok)throw new Error("http_"+I.status);e=await I.json(),a=!0}catch{e={configured:!1,connected:!1,organisations:[]},a=!1}return e}function v(){const l=document.getElementById("erp-connect-cards");if(!l)return;const p=e;let I,L=!1;p?p.configured?p.connected?(L=!0,I='<span class="mrerp-card-pill mrerp-pill-ok">'+s(t("xero-card-connected"))+"</span>"):I='<span class="mrerp-card-pill mrerp-pill-neutral">'+s(t("xero-card-not-connected"))+"</span>":I='<span class="mrerp-card-pill mrerp-pill-neutral">'+s(t("xero-card-not-configured"))+"</span>":I='<span class="mrerp-card-pill mrerp-pill-neutral">'+s(t("xero-card-not-connected"))+"</span>";let H="";if(!p||!p.configured)H='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+s(t("xero-connect-btn"))+"</button>";else if(!p.connected)g()&&(H='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+s(t("xero-connect-btn"))+"</button>");else{const h=!!p.auto_push,c=h?t("card-btn-disable"):t("card-btn-enable");H='<button type="button" class="'+(h?"mrerp-card-toggle mrerp-card-toggle-disable":"mrerp-card-toggle mrerp-card-toggle-enable")+'" id="btn-xero-toggle-enabled" data-xero-enabled="'+(h?"1":"0")+'" title="'+s(h?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip"))+'">'+s(c)+'</button><button type="button" class="int-btn-configure" id="btn-xero-edit-toggle">'+s(t("card-btn-edit"))+"</button>"}const x=p&&p.connected?"xero-card-desc-connected":"xero-card-desc-default",M=p&&p.connected?t("xero-card-connected")||"Connected · default org will receive pushes":"Cloud accounting · push invoices to your default Xero org",W=(function(){const h=t(x);return h===x?M:h})();let G='<div class="integration-row erp-connect-xero'+(L?" connected":"")+'"><div class="int-icon ic-xero"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="9" cy="10" r="1.3" fill="currentColor"/><circle cx="15" cy="14" r="1.3" fill="currentColor"/><path d="M9 14l6-4"/></svg></div><div class="int-info"><div class="int-name"><span>'+s(t("xero-card-title")||"Xero")+"</span>"+I+'</div><div class="int-desc">'+s(W)+'</div></div><div class="int-actions">'+H+"</div></div>";if(p&&p.configured&&p.connected&&g()){const h=p.organisations||[];let c="";if(h.length>0){c+='<div class="erp-cc-meta">'+s((t("xero-org-count")||"").replace("{n}",String(h.length)))+"</div>",c+='<div class="erp-cc-org-label">'+s(t("xero-default-org"))+":</div>",c+='<div class="erp-cc-orgs">',h.forEach(function(Y){c+='<label class="erp-cc-org-row"><input type="radio" name="xero-default-org" value="'+s(Y.id)+'"'+(Y.is_default?" checked":"")+'><span class="erp-cc-org-name">'+s(Y.organisation_name||Y.organisation_id)+"</span></label>"}),c+="</div>";const $=!!p.auto_push,P=$?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip");c+='<div class="erp-cc-auto-push" title="'+s(P)+'"><label class="erp-cc-toggle"><input type="checkbox" id="xero-auto-push-toggle"'+($?" checked":"")+'><span class="erp-cc-toggle-slider"></span><span class="erp-cc-toggle-label">'+s(t("erp-auto-push-label"))+"</span></label></div>",c+='<div class="erp-cc-actions"><button class="btn btn-ghost btn-tiny" type="button" id="btn-xero-disconnect">'+s(t("xero-disconnect-btn"))+"</button></div>"}G+='<div class="erp-xero-details" id="erp-xero-details" style="display:none; margin:8px 0 16px; padding:12px 14px; border:1px solid var(--line); border-radius:8px; background:var(--bg);">'+c+"</div>"}const K=l.querySelector(".erp-connect-xero"),te=l.querySelector("#erp-xero-details");te&&te.remove(),K?K.outerHTML=G:l.insertAdjacentHTML("afterbegin",G);const re=document.getElementById("btn-xero-edit-toggle");re&&re.addEventListener("click",function(h){h.preventDefault();const c=document.getElementById("erp-xero-details");c&&(c.style.display=c.style.display==="none"?"":"none")});const S=document.getElementById("btn-xero-toggle-enabled");S&&S.addEventListener("click",async function(h){if(h.preventDefault(),S.disabled)return;const $=!(S.getAttribute("data-xero-enabled")==="1");if(!$)try{if(!await window.pearnlyConfirm(t("card-toggle-disable-confirm")))return}catch{}S.disabled=!0,await E($,null)})}async function w(){const l=localStorage.getItem("mrpilot_token");if(l)try{const p=await fetch("/api/erp/xero/auth/start",{method:"GET",headers:{Authorization:"Bearer "+l}});if(!p.ok){let L="unknown";try{L=(await p.json()).detail||"unknown"}catch{}const H=String(L).replace(/^xero\./,"").toLowerCase();i(t("xero-push-fail").replace("{err}",t("xero-err-"+H)||L),"error");return}const I=await p.json();I.redirect_url&&(window.location.href=I.redirect_url)}catch(p){i(t("xero-push-fail").replace("{err}",p.message||"network"),"error")}}async function u(){if(!await window.pearnlyConfirm(t("xero-disconnect-confirm")))return;const p=localStorage.getItem("mrpilot_token");try{const I=await fetch("/api/erp/xero/disconnect",{method:"POST",headers:{Authorization:"Bearer "+p}});if(!I.ok)throw new Error("http_"+I.status);await o(!0),v()}catch(I){i(t("xero-push-fail").replace("{err}",I.message),"error")}}async function d(l){const p=localStorage.getItem("mrpilot_token");try{const I=await fetch("/api/erp/xero/select_org",{method:"POST",headers:{Authorization:"Bearer "+p,"Content-Type":"application/json"},body:JSON.stringify({token_id:l})});if(!I.ok)throw new Error("http_"+I.status);await o(!0),v()}catch(I){i(t("xero-push-fail").replace("{err}",I.message),"error")}}async function E(l,p){const I=localStorage.getItem("mrpilot_token");p&&(p.disabled=!0);try{const L=await fetch("/api/erp/xero/auto-push",{method:"POST",headers:{Authorization:"Bearer "+I,"Content-Type":"application/json"},body:JSON.stringify({on:!!l})});if(!L.ok){let H="unknown";try{H=(await L.json()).detail||"unknown"}catch{}throw new Error(H)}i(l?t("erp-auto-push-toggled-on"):t("erp-auto-push-toggled-off"),"success"),a=!1,await o(!0),v()}catch(L){p&&(p.checked=!l),i(t("erp-auto-push-toggle-fail").replace("{err}",L.message||"network"),"error")}finally{p&&(p.disabled=!1)}}async function k(){const l=document.getElementById("drawer-history-save");if(!l||l.querySelector("#btn-xero-push")||l.querySelector("#pn-push-wrap")||(await o(!1),l.querySelector("#pn-push-wrap"))||l.querySelector("#btn-xero-push"))return;const p=b();if(!(p&&(p._historyId||p.history_id)))return;let L=!1,H="xero-push-tip";!e||!e.configured?(L=!0,H="xero-err-not_configured"):e.connected?_(p)&&(L=!0,H="xero-push-disabled-exc"):(L=!0,H="xero-push-disabled-no-conn");const x=document.createElement("button");x.type="button",x.id="btn-xero-push",x.className="btn btn-ghost"+(L?" disabled":""),x.disabled=L,x.title=t(H)||"",x.innerHTML='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5 8l2 2 4-4"/></svg><span style="margin-left:4px;">'+s(t("xero-push-btn"))+"</span>",x.addEventListener("click",q);const M=document.getElementById("btn-push-erp");M&&M.parentNode?M.parentNode.insertBefore(x,M.nextSibling):l.insertBefore(x,l.firstChild)}async function q(){const l=b(),p=l&&(l._historyId||l.history_id);if(!p)return;const I=document.getElementById("btn-xero-push");I&&(I.disabled=!0,I.classList.add("loading"));const L=localStorage.getItem("mrpilot_token");try{const H=await fetch("/api/erp/xero/push/"+encodeURIComponent(p),{method:"POST",headers:{Authorization:"Bearer "+L}});if(!H.ok){let x="unknown";try{x=(await H.json()).detail||"unknown"}catch{}const M=String(x).replace(/^xero\./,"").toLowerCase(),W=t("xero-"+M),G=W&&W!=="xero-"+M?W:x;i(t("xero-push-fail").replace("{err}",G),"error");return}i(t("xero-push-ok"),"success")}catch(H){i(t("xero-push-fail").replace("{err}",H.message||"network"),"error")}finally{I&&(I.disabled=!1,I.classList.remove("loading"))}}async function R(){await o(!0),v(),y()}async function y(){const l=document.getElementById("erp-global-push-mode");if(!l)return;const p=localStorage.getItem("mrpilot_token");if(p)try{const I=await fetch("/api/settings/erp-push-mode",{headers:{Authorization:"Bearer "+p}});if(I.ok){const L=await I.json();L.mode&&(l.value=L.mode,l.dataset.prev=L.mode)}}catch{}}async function B(l){const p=l.value,I=localStorage.getItem("mrpilot_token");try{(await fetch("/api/settings/erp-push-mode",{method:"PUT",headers:{Authorization:"Bearer "+I,"Content-Type":"application/json"},body:JSON.stringify({mode:p})})).ok?(l.dataset.prev=p,i(t("pref-erp-mode-saved"),"success")):(l.value=l.dataset.prev||"smart",i(t("pref-save-failed"),"error"))}catch{l.value=l.dataset.prev||"smart",i(t("pref-save-failed"),"error")}}function O(){try{const l=String(window.location.hash||"");if(l.indexOf("xero=ok")>=0){const p=l.match(/n=(\d+)/),I=p?p[1]:"1";i((t("xero-toast-redirected-ok")||"").replace("{n}",I),"success"),history.replaceState(null,"",window.location.pathname+"#automation"),o(!0).then(v)}else l.indexOf("xero=err")>=0&&(i(t("xero-toast-redirected-err"),"error"),history.replaceState(null,"",window.location.pathname+"#automation"))}catch{}}function D(){if(n)return;n=!0,document.addEventListener("click",function(p){if(p.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(R,50);return}if(p.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(R,80);return}if(p.target.closest("#btn-xero-connect")){p.preventDefault(),w();return}if(p.target.closest("#btn-xero-disconnect")){p.preventDefault(),u();return}}),document.addEventListener("change",function(p){p.target&&p.target.matches('input[name="xero-default-org"]')&&d(p.target.value),p.target&&p.target.id==="xero-auto-push-toggle"&&E(p.target.checked,p.target),p.target&&p.target.id==="erp-global-push-mode"&&B(p.target)});const l=function(){return document.getElementById("drawer-body")};try{const p=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("btn-xero-push")&&k()}),I=l();if(I)p.observe(I,{childList:!0,subtree:!0});else{const L=new MutationObserver(function(){const H=l();H&&(p.observe(H,{childList:!0,subtree:!0}),L.disconnect())});L.observe(document.body,{childList:!0,subtree:!0})}}catch{}setTimeout(O,500)}function F(){e&&v();const l=document.getElementById("btn-xero-push");if(l){const p=l.querySelector("span");p&&(p.textContent=t("xero-push-btn"))}}D(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("xero-adapter",F);async function A(l){const p=Date.now();for(;Date.now()-p<l;){if(typeof _userInfo<"u"&&_userInfo&&_userInfo.id)return _userInfo;await new Promise(I=>setTimeout(I,80))}return null}async function f(){await A(5e3);const l=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),p=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');l&&p&&await R()}setTimeout(f,200)})();(function(){const e={};function a(){if(document.getElementById("report-modal"))return;const v=`
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
        </div>`,w=document.createElement("div");w.innerHTML=v,document.body.appendChild(w.firstElementChild),document.getElementById("report-modal-close-x").addEventListener("click",n),document.getElementById("report-modal-cancel").addEventListener("click",n),document.getElementById("report-modal").addEventListener("click",u=>{u.target.id==="report-modal"&&n()})}function n(){const v=document.getElementById("report-modal");v&&(v.style.display="none"),s=null}let s=null;async function i(v,w){const u=v+":"+(w||"");if(e[u])return e[u];let d;try{const E=localStorage.getItem("mrpilot_token"),k=await fetch(`/api/reports/templates?lang=${encodeURIComponent(v)}`,{headers:{Authorization:"Bearer "+E}});if(!k.ok)throw new Error("templates fetch failed");d=(await k.json()).templates||[]}catch(E){console.error("fetchTemplates fail",E),d=[{code:"input_vat",name:t("tpl-input-vat"),desc:t("tpl-input-vat-desc"),recommended:!0},{code:"standard",name:t("tpl-standard"),desc:t("tpl-standard-desc"),recommended:!1},{code:"print",name:t("tpl-print"),desc:t("tpl-print-desc"),recommended:!1}]}if(d=d.filter(E=>E.code!=="erp"),w==="history-batch"){const E=d.findIndex(q=>q.code==="standard"),k=E>=0?E+1:d.length;d.splice(k,0,{code:"sales_detail_th",name:t("export-tpl-sales-detail"),desc:t("export-tpl-sales-detail-desc"),recommended:!1,is_new:!0})}return e[u]=d,d}function g(v){const w=document.getElementById("report-tpl-list"),u=v.map((E,k)=>`
            <label class="report-tpl-item${E.recommended?" is-recommended":""}">
                <input type="radio" name="report-tpl" value="${E.code}" ${E.recommended||k===0?"checked":""}>
                <div class="report-tpl-content">
                    <div class="report-tpl-name">
                        ${b(E.name)}
                        ${E.recommended?`<span class="report-tpl-badge">${b(t("report-recommended"))}</span>`:""}
                    </div>
                    <div class="report-tpl-desc">${b(E.desc||"")}</div>
                </div>
            </label>
        `).join(""),d=`
            <label class="report-tpl-item report-tpl-coming" title="${b(t("tpl-custom-coming"))}">
                <input type="radio" name="report-tpl" disabled>
                <div class="report-tpl-content">
                    <div class="report-tpl-name">
                        + ${b(t("tpl-custom-new"))}
                        <span class="report-tpl-badge report-tpl-badge-soon">${b(t("cs-coming-soon"))}</span>
                    </div>
                    <div class="report-tpl-desc">${b(t("tpl-custom-desc"))}</div>
                </div>
            </label>
        `;w.innerHTML=u+d}function b(v){return v==null?"":String(v).replace(/[&<>"']/g,w=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[w])}function _(v){const w=new Date,u=w.getFullYear(),d=w.getMonth()+1;if(v==="all")return"all";if(v==="this-month")return`${u}-${String(d).padStart(2,"0")}`;if(v==="last-month"){const E=new Date(u,d-2,1);return`${E.getFullYear()}-${String(E.getMonth()+1).padStart(2,"0")}`}return v==="this-year"?`${u}`:v==="this-quarter"?`${u}-Q${Math.floor((d-1)/3)+1}`:"all"}window.openReportModal=async function(v){v=v||{},a(),typeof applyLang=="function"?applyLang(currentLang):document.querySelectorAll("#report-modal [data-i18n]").forEach(q=>{const R=q.getAttribute("data-i18n");I18N[currentLang]&&I18N[currentLang][R]&&(q.textContent=I18N[currentLang][R])});const w=document.getElementById("report-period-section");w&&(w.style.display=v.mode==="client"?"":"none");const u=document.getElementById("report-tpl-list");u.innerHTML=`<div class="report-tpl-loading">${b(t("report-modal-loading"))}</div>`,document.getElementById("report-modal").style.display="";const d=await i(currentLang,v&&v.mode);g(d),s=v;const E=document.getElementById("report-modal-download"),k=E.cloneNode(!0);E.parentNode.replaceChild(k,E),k.addEventListener("click",()=>o(s))};async function o(v){if(!v)return;const w=document.querySelector('input[name="report-tpl"]:checked');if(!w){showToast(t("report-toast-no-selection"),"info");return}const u=w.value,d=document.querySelector('input[name="report-period"]:checked'),E=d?d.value:"all",k=_(E),q=document.getElementById("report-modal-download"),R=q.innerHTML;q.disabled=!0,q.innerHTML=`<span>${b(t("report-modal-loading"))}</span>`;try{const y=localStorage.getItem("mrpilot_token");let B,O;if(v.mode==="records")B=await fetch("/api/reports/export",{method:"POST",headers:{Authorization:"Bearer "+y,"Content-Type":"application/json"},body:JSON.stringify({template:u,lang:currentLang,records:v.records||[],meta:v.meta||{}})}),O=`mrpilot-${u}-${Date.now()}.xlsx`;else if(v.mode==="client"){const I=`/api/reports/clients/${v.clientId}/export?template=${encodeURIComponent(u)}&lang=${encodeURIComponent(currentLang)}&month=${encodeURIComponent(k)}`;B=await fetch(I,{headers:{Authorization:"Bearer "+y}}),O=`${(v.clientName||"client").replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40)}-${u}.xlsx`}else if(v.mode==="history-batch")u==="sales_detail_th"?(B=await fetch("/api/ocr/export-by-history-ids",{method:"POST",headers:{Authorization:"Bearer "+y,"Content-Type":"application/json"},body:JSON.stringify({template:"sales_detail_th",lang:currentLang,history_ids:v.historyIds||[],client_id:v.clientId||null})}),O=`Pearnly_SalesDetail_${Date.now()}.xlsx`):(B=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+y,"Content-Type":"application/json"},body:JSON.stringify({template:u,lang:currentLang,history_ids:v.historyIds||[],client_id:v.clientId||null})}),O=`mrpilot-batch-${u}-${Date.now()}.xlsx`);else throw new Error("unknown mode: "+v.mode);if(!B.ok){let I="HTTP "+B.status;try{const L=await B.json();L&&L.detail&&(I=L.detail)}catch(L){console.warn("[batch-export] resp.json err.detail parse failed:",L)}B.status===404?showToast(t("report-toast-empty"),"info"):showToast(t("report-toast-fail")+" · "+I,"error");return}const D=await B.blob();let F=O;const f=(B.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(f)try{F=decodeURIComponent(f[1])}catch{}const l=URL.createObjectURL(D),p=document.createElement("a");p.href=l,p.download=F,document.body.appendChild(p),p.click(),document.body.removeChild(p),URL.revokeObjectURL(l),showToast(t("report-toast-success"),"success"),n()}catch(y){console.error("doDownload fail",y),showToast(t("report-toast-fail")+" · "+(y.message||""),"error")}finally{q.disabled=!1,q.innerHTML=R}}document.addEventListener("DOMContentLoaded",()=>{const v=document.getElementById("btn-export");if(v){const u=v.cloneNode(!0);v.parentNode.replaceChild(u,v),u.addEventListener("click",()=>{if(typeof _results>"u"||!_results||_results.length===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"records",records:_results.map(d=>({filename:d.filename,merged_fields:d.merged_fields||{}}))})})}const w=document.getElementById("history-batch-export");w&&w.addEventListener("click",()=>{if(typeof _historySelected>"u"||_historySelected.size===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"history-batch",historyIds:Array.from(_historySelected)})})}),window.openClientExportModal=function(v,w){openReportModal({mode:"client",clientId:v,clientName:w||""})}})();(function(){const a=typeof window<"u"&&"showDirectoryPicker"in window,n=/\.(pdf|jpe?g|png|webp)$/i,s="mrpilot_folder_watcher",i=1;let g=null,b=null,_=null,o=60,v=!1,w=!1,u=0,d=0,E=0,k=[],q=null,R=!1;function y(){return g||(g=new Promise((m,C)=>{const T=indexedDB.open(s,i);T.onupgradeneeded=U=>{const N=U.target.result;N.objectStoreNames.contains("handles")||N.createObjectStore("handles"),N.objectStoreNames.contains("seen")||N.createObjectStore("seen"),N.objectStoreNames.contains("config")||N.createObjectStore("config")},T.onsuccess=U=>m(U.target.result),T.onerror=U=>C(U.target.error)}),g)}function B(m,C){return y().then(T=>new Promise((U,N)=>{const j=T.transaction(m,"readonly").objectStore(m).get(C);j.onsuccess=()=>U(j.result),j.onerror=()=>N(j.error)}))}function O(m,C,T){return y().then(U=>new Promise((N,r)=>{const j=U.transaction(m,"readwrite");j.objectStore(m).put(T,C),j.oncomplete=()=>N(),j.onerror=()=>r(j.error)}))}function D(m,C){return y().then(T=>new Promise((U,N)=>{const r=T.transaction(m,"readwrite");r.objectStore(m).delete(C),r.oncomplete=()=>U(),r.onerror=()=>N(r.error)}))}function F(m){return y().then(C=>new Promise((T,U)=>{const N=C.transaction(m,"readwrite");N.objectStore(m).clear(),N.oncomplete=()=>T(),N.onerror=()=>U(N.error)}))}async function A(m){if(!m)return!1;try{const C={mode:"read"};let T=await m.queryPermission(C);return T==="granted"?!0:(T=await m.requestPermission(C),T==="granted")}catch(C){return console.warn("[folder] permission check failed:",C),!1}}function f(m,C){const T=document.getElementById("folder-status-summary");T&&(T.setAttribute("data-i18n",m),T.textContent=t(m),T.className="auto-status-pill"+(C?" "+C:""))}function l(m){["folder-unsupported","folder-empty","folder-active"].forEach(C=>{const T=document.getElementById(C);T&&(T.style.display=C===m?"":"none")})}function p(m){if(!m)return"-";const C=m instanceof Date?m:new Date(m),T=String(C.getHours()).padStart(2,"0"),U=String(C.getMinutes()).padStart(2,"0"),N=String(C.getSeconds()).padStart(2,"0");return`${T}:${U}:${N}`}function I(){l("folder-active");const m=document.getElementById("folder-config-path");m&&b&&(m.textContent=b.name||"-");const C=document.getElementById("folder-interval-select");C&&(C.value=String(o)),document.getElementById("folder-stat-last").textContent=q?p(q):"-",document.getElementById("folder-stat-processed").textContent=String(u),document.getElementById("folder-stat-failed").textContent=String(d),document.getElementById("folder-stat-queue").textContent=String(E);const T=document.getElementById("btn-folder-pause"),U=document.getElementById("btn-folder-resume");T&&(T.style.display=v?"none":""),U&&(U.style.display=v?"":"none"),v?f("folder-status-paused","paused"):f("folder-status-running","running");const N=document.getElementById("folder-status-text");N&&(N.setAttribute("data-i18n",v?"folder-status-paused":"folder-status-running"),N.textContent=t(v?"folder-status-paused":"folder-status-running"));const r=document.getElementById("folder-status-pulse");r&&(r.className="folder-status-pulse"+(v?" paused":"")),L()}function L(){const m=document.getElementById("folder-recent-list");if(m){if(k.length===0){m.innerHTML=`<div class="folder-recent-empty">${escapeHtml(t("folder-recent-empty"))}</div>`;return}m.innerHTML=k.slice(0,20).map(C=>{let T;C.status==="ok"?T=`<span class="folder-recent-icon ok">${svgIcon("check",12)}</span>`:C.status==="dup"?T=`<span class="folder-recent-icon dup" title="${escapeHtml(t("folder-recent-dup"))}">${svgIcon("copy",12)}</span>`:C.status==="skip"?T=`<span class="folder-recent-icon skip" title="${escapeHtml(t("folder-recent-skip"))}">${svgIcon("minus",12)}</span>`:T=`<span class="folder-recent-icon fail">${svgIcon("alert",12)}</span>`;const U=C.status==="fail"&&C.error?C.error:C.status==="dup"&&C.reason||C.status==="skip"&&C.reason?C.reason:"",N=U?`<div class="folder-recent-err">${escapeHtml(U)}</div>`:"";return`
                <div class="folder-recent-item">
                    ${T}
                    <div class="folder-recent-body">
                        <div class="folder-recent-name">${escapeHtml(C.name)}</div>
                        ${N}
                    </div>
                    <div class="folder-recent-time">${p(C.time)}</div>
                </div>
            `}).join("")}}function H(m){k.unshift(m),k.length>50&&(k.length=50),O("config","recent_list",k).catch(()=>{})}async function x(m){const C=new FormData;C.append("file",m,m.name),C.append("source","folder");const T=await fetch("/api/ocr/recognize?source=folder",{method:"POST",headers:{Authorization:"Bearer "+token,"X-Source":"folder"},body:C});if(!T.ok){let U="http_"+T.status;try{const N=await T.json();U=N&&N.detail?typeof N.detail=="string"?N.detail:N.detail.code||JSON.stringify(N.detail):U}catch{}throw new Error(U)}return await T.json()}async function M(m){try{const T=(await m.getFile()).size;return await new Promise(N=>setTimeout(N,3e3)),(await m.getFile()).size===T&&T>0}catch{return!1}}async function W(m,C,T,U){if(U>10)return;let N;try{N=await m.queryPermission({mode:"read"})}catch{N="denied"}if(N==="granted")for await(const r of m.values()){const j=C?`${C}/${r.name}`:r.name;if(r.kind==="file"){if(!n.test(r.name))continue;let z;try{z=await r.getFile()}catch{continue}const J=`${j}::${z.size}::${z.lastModified}`;if(await B("seen",J))continue;T.push({entry:r,file:z,seenKey:J,relPath:j})}else if(r.kind==="directory")try{await W(r,j,T,U+1)}catch{}}}async function G(){if(!(w||v||!b)){w=!0;try{if(await b.queryPermission({mode:"read"})!=="granted"){console.warn("[folder] permission lost · stop"),Y(),showToast("warn",t("folder-permission-lost"));return}q=new Date;const C=[];await W(b,"",C,0),E=C.length,I();for(const T of C){if(v)break;if(!await M(T.entry)){E=Math.max(0,E-1),I();continue}try{let N;try{N=await T.entry.getFile()}catch{N=T.file}const r=await x(N);await O("seen",T.seenKey,{name:N.name,relPath:T.relPath,size:N.size,lastModified:N.lastModified,processed_at:Date.now()});const j=r.history_ids||(r.history_id?[r.history_id]:[]),z=r.duplicate_warnings||[],J=T.relPath||N.name;j.length>0?(u+=j.length,H({name:J,status:"ok",time:new Date,history_id:j[0],count:j.length}),await O("config","processed_count",u)):z.length>0?H({name:J,status:"dup",time:new Date,reason:t("folder-recent-dup-reason")}):H({name:J,status:"skip",time:new Date,reason:t("folder-recent-skip-reason")})}catch(N){d++,H({name:T.relPath||T.file.name,status:"fail",time:new Date,error:String(N.message||N)}),await O("config","failed_count",d)}E=Math.max(0,E-1),I()}}catch(m){console.warn("[folder] scan error:",m)}finally{w=!1,I()}}}function K(){_&&clearInterval(_),_=setInterval(G,o*1e3)}function te(){_&&(clearInterval(_),_=null)}function re(m){if(!b||v)return;const C=typeof t=="function"?t("folder-unload-warn"):"Folder watcher running · close anyway?";return m.preventDefault(),m.returnValue=C,C}function S(){window._pearnlyFolderUnloadAttached||(window._pearnlyFolderUnloadAttached=!0,window.addEventListener("beforeunload",re))}function h(){window._pearnlyFolderUnloadAttached&&(window._pearnlyFolderUnloadAttached=!1,window.removeEventListener("beforeunload",re))}function c(){v=!1,K(),S(),I(),G()}function $(){v=!0,te(),h(),I()}function P(){v=!1,K(),S(),I(),G()}function Y(){v=!0,te(),h()}async function Z(){try{const m=await window.showDirectoryPicker({mode:"read",startIn:"documents"});if(!await A(m)){showToast("warn",t("folder-permission-denied"));return}b=m,await O("handles","main",m),u=0,d=0,E=0,k=[],await O("config","processed_count",0),await O("config","failed_count",0),await F("seen"),c()}catch(m){m&&m.name!=="AbortError"&&console.warn("[folder] pick failed:",m)}}async function le(){await showConfirm(t("folder-confirm-remove"),{danger:!0})&&(Y(),b=null,u=0,d=0,E=0,k=[],await D("handles","main"),await D("config","processed_count"),await D("config","failed_count"),await F("seen"),l("folder-empty"),f("folder-status-empty",""))}async function ie(){k=[];try{await D("config","recent_list")}catch{}L()}async function V(){if(R)return;if(R=!0,!a){l("folder-unsupported"),f("folder-status-unsupported",""),ne();return}Q();let m=null;try{m=await B("handles","main")}catch{}if(!m){l("folder-empty"),f("folder-status-empty","");return}if(!await A(m)){l("folder-empty"),f("folder-status-empty",""),await D("handles","main"),showToast("warn",t("folder-permission-lost-restart"));return}b=m;try{u=await B("config","processed_count")||0}catch{}try{d=await B("config","failed_count")||0}catch{}try{const T=await B("config","recent_list");Array.isArray(T)&&(k=T.map(U=>({...U,time:U.time?new Date(U.time):new Date})))}catch{}c()}function Q(){const m=document.getElementById("btn-folder-pick"),C=document.getElementById("btn-folder-pause"),T=document.getElementById("btn-folder-resume"),U=document.getElementById("btn-folder-scan-now"),N=document.getElementById("btn-folder-remove"),r=document.getElementById("btn-folder-clear-recent"),j=document.getElementById("folder-interval-select");m&&m.addEventListener("click",Z),C&&C.addEventListener("click",$),T&&T.addEventListener("click",P),U&&U.addEventListener("click",()=>{G()}),N&&N.addEventListener("click",le),r&&r.addEventListener("click",ie),j&&j.addEventListener("change",z=>{o=parseInt(z.target.value,10)||60,v||K()}),ee()}function ee(){document.querySelectorAll('[data-auto-panel="folder"] [data-tab-jump]').forEach(m=>{m.dataset.tabJumpBound||(m.dataset.tabJumpBound="1",m.addEventListener("click",C=>{const T=C.currentTarget.dataset.tabJump;if(T==="email")typeof switchAutomationTab=="function"&&switchAutomationTab("email");else if(T==="upload"){const U=document.querySelector('[data-page="recognize"]')||document.querySelector('[data-page="upload"]');U&&U.click()}}))})}function ne(){ee()}window._loadFolderWatcherPanel=V;function oe(){try{if(navigator.userAgentData&&Array.isArray(navigator.userAgentData.brands))return navigator.userAgentData.brands.some(C=>/chromium|google chrome|microsoft edge/i.test(C.brand||""))}catch{}const m=navigator.userAgent||"";return!!(/Edg\//.test(m)||/Chrome\//.test(m)&&!/OPR\/|YaBrowser|Opera/.test(m))}function ue(){try{if(oe()||localStorage.getItem("pearnly_chrome_banner_dismissed")==="1")return;const m=document.getElementById("chrome-only-banner");if(!m)return;const C=m.querySelector('[data-i18n="chrome-banner-msg"]'),T=m.querySelector('[data-i18n="chrome-banner-dismiss"]');C&&typeof t=="function"&&(C.textContent=t("chrome-banner-msg")),T&&typeof t=="function"&&(T.textContent=t("chrome-banner-dismiss")),m.style.display="";const U=document.getElementById("chrome-only-banner-close");U&&!U.dataset.bound&&(U.dataset.bound="1",U.addEventListener("click",()=>{m.style.display="none";try{localStorage.setItem("pearnly_chrome_banner_dismissed","1")}catch{}}))}catch{}}typeof document<"u"&&(document.readyState==="loading"?document.addEventListener("DOMContentLoaded",ue):setTimeout(ue,0)),window._refreshChromeBanner=ue})();(function(){let e=null,a=null,n="new",s=!1,i=!1;async function g(){const x=document.getElementById("email-empty"),M=document.getElementById("email-account-card");if(document.getElementById("email-logs-section"),!(!x||!M))try{const W=await fetch("/api/email-ingest/account",{headers:{Authorization:"Bearer "+token}});if(W.status===401){localStorage.removeItem("mrpilot_token");const K=await W.json().catch(()=>({}));if((typeof K.detail=="string"?K.detail:K.detail&&K.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}if(!W.ok){_("none");return}const G=await W.json();e=G.account||null,a=G.presets||{},s=!0,b(),e&&p()}catch(W){console.error("[email-ingest] load failed",W),_("none")}}function b(){const x=document.getElementById("email-empty"),M=document.getElementById("email-account-card"),W=document.getElementById("email-logs-section");if(!e){x.style.display="",M.style.display="none",W&&(W.style.display="none"),_("none");return}x.style.display="none",M.style.display="",W&&(W.style.display="");const G=document.getElementById("email-account-addr"),K=document.getElementById("email-account-host"),te=document.getElementById("email-account-last"),re=document.getElementById("email-last-error"),S=document.getElementById("email-enabled-toggle");if(G&&(G.textContent=e.email_address||"-"),K&&(K.textContent=`${e.imap_host||"-"}:${e.imap_port||993}`),te){const h=e.last_fetched_at;if(!h)te.textContent=t("email-last-never");else{const c=o(h),$=!e.last_error;te.textContent=$?t("email-last-ok",{time:c}):t("email-last-fail",{time:c})}}re&&(e.last_error?(re.style.display="",re.textContent=v(e.last_error)):re.style.display="none"),S&&(S.checked=!!e.enabled),e.enabled?e.last_error?_("error"):_("on"):_("off")}function _(x){const M=document.getElementById("email-status-summary");if(!M)return;M.classList.remove("none","ready","active","coming");let W="auto-status-loading";x==="none"?(W="email-status-none",M.classList.add("none")):x==="on"?(W="email-status-on",M.classList.add("active")):x==="off"?(W="email-status-off",M.classList.add("coming")):x==="error"&&(W="email-status-error",M.classList.add("none")),M.setAttribute("data-i18n",W),M.textContent=t(W)}function o(x){if(!x)return"";const M=new Date(x);if(isNaN(M.getTime()))return"";const W=G=>String(G).padStart(2,"0");return`${W(M.getMonth()+1)}-${W(M.getDate())} ${W(M.getHours())}:${W(M.getMinutes())}`}function v(x){if(!x)return"";const M=String(x);return/auth|AUTHENTICATIONFAILED|invalid credentials/i.test(M)?t("email-test-auth-fail"):/timeout|timed out/i.test(M)?t("email.timeout"):(/ENOTFOUND|getaddrinfo/i.test(M),M)}function w(x){n=x;const M=document.getElementById("email-modal");if(!M)return;const W=document.getElementById("email-preset");W.innerHTML="";const G=a||{},K=["gmail","outlook","yahoo","icloud","qq","163","custom"],te={gmail:"Gmail",outlook:"Outlook / Office365",yahoo:"Yahoo Mail",icloud:"iCloud",qq:"QQ 邮箱",163:"网易 163"};K.forEach(Q=>{if(!G[Q])return;const ee=document.createElement("option");ee.value=Q,ee.textContent=Q==="custom"?t("email-preset-custom"):te[Q]||Q,W.appendChild(ee)});const re=document.getElementById("email-modal-title"),S=document.getElementById("email-address"),h=document.getElementById("email-password"),c=document.getElementById("email-imap-host"),$=document.getElementById("email-imap-port"),P=document.getElementById("email-imap-ssl"),Y=document.getElementById("email-folder"),Z=document.getElementById("email-mark-read"),le=document.getElementById("email-bind-enabled"),ie=document.getElementById("email-test-result"),V=document.getElementById("email-adv-details");if(ie&&(ie.style.display="none",ie.textContent=""),x==="edit"&&e){re.setAttribute("data-i18n","email-modal-title-edit"),re.textContent=t("email-modal-title-edit"),S.value=e.email_address||"",h.value="",h.setAttribute("data-i18n-placeholder","email-field-password-edit-ph"),h.placeholder=t("email-field-password-edit-ph"),c.value=e.imap_host||"",$.value=e.imap_port||993,P.checked=e.imap_use_ssl!==!1,Y.value=e.folder||"INBOX",Z.checked=e.mark_as_read!==!1,le.checked=e.enabled!==!1;const Q=document.getElementById("email-filter-sender"),ee=document.getElementById("email-filter-subject");Q&&(Q.value=e.filter_sender||""),ee&&(ee.value=e.filter_subject||""),B(e.interval_min||15),W.value=q(e.imap_host)||"custom",V&&(V.open=!0)}else{re.setAttribute("data-i18n","email-modal-title-new"),re.textContent=t("email-modal-title-new"),S.value="",h.value="",h.setAttribute("data-i18n-placeholder","email-field-password-ph"),h.placeholder=t("email-field-password-ph"),W.value="gmail",d("gmail"),Y.value="INBOX",Z.checked=!0,le.checked=!0;const Q=document.getElementById("email-filter-sender"),ee=document.getElementById("email-filter-subject");Q&&(Q.value=""),ee&&(ee.value=""),B(15),V&&(V.open=!1)}y(),M.style.display="flex",setTimeout(()=>S.focus(),60)}function u(){const x=document.getElementById("email-modal");x&&(x.style.display="none")}function d(x){const M=(a||{})[x];if(!M||x==="custom")return;const W=document.getElementById("email-imap-host"),G=document.getElementById("email-imap-port"),K=document.getElementById("email-imap-ssl");W&&(W.value=M.host||""),G&&(G.value=M.port||993),K&&(K.checked=M.ssl!==!1)}const E={"gmail.com":"gmail","googlemail.com":"gmail","outlook.com":"outlook","hotmail.com":"outlook","live.com":"outlook","office365.com":"outlook","msn.com":"outlook","yahoo.com":"yahoo","yahoo.co.jp":"yahoo","icloud.com":"icloud","me.com":"icloud","mac.com":"icloud","qq.com":"qq","foxmail.com":"qq","163.com":"163","126.com":"163","yeah.net":"163"};function k(x){if(!x||!x.includes("@"))return;const M=x.split("@")[1].toLowerCase().trim(),W=E[M];if(!W)return;const G=document.getElementById("email-preset");if(!G)return;const K=G.value;K&&K!=="custom"&&K!==""&&K===W||(G.value=W,d(W))}function q(x){if(!x)return null;const M=a||{};for(const W in M)if(W!=="custom"&&M[W]&&M[W].host===x)return W;return null}function R(){const x=document.querySelector("#email-interval-options .email-interval-btn.active"),M=x?parseInt(x.dataset.interval,10):15;return{email_address:(document.getElementById("email-address").value||"").trim(),password:document.getElementById("email-password").value||"",imap_host:(document.getElementById("email-imap-host").value||"").trim(),imap_port:parseInt(document.getElementById("email-imap-port").value||"993",10)||993,imap_use_ssl:document.getElementById("email-imap-ssl").checked,folder:(document.getElementById("email-folder").value||"INBOX").trim()||"INBOX",mark_as_read:document.getElementById("email-mark-read").checked,enabled:document.getElementById("email-bind-enabled").checked,interval_min:[5,15,60].includes(M)?M:15,filter_sender:(document.getElementById("email-filter-sender").value||"").trim()||null,filter_subject:(document.getElementById("email-filter-subject").value||"").trim()||null}}function y(){const x=document.getElementById("email-interval-options");!x||x._bound||(x._bound=!0,x.addEventListener("click",M=>{const W=M.target.closest(".email-interval-btn");W&&(x.querySelectorAll(".email-interval-btn").forEach(G=>G.classList.remove("active")),W.classList.add("active"))}))}function B(x){const M=[5,15,60].includes(x)?x:15,W=document.getElementById("email-interval-options");W&&W.querySelectorAll(".email-interval-btn").forEach(G=>{G.classList.toggle("active",parseInt(G.dataset.interval,10)===M)})}function O(x,M){const W=document.getElementById("email-test-result");W&&(W.style.display="",W.textContent=M,W.className="form-test-result "+(x==="ok"?"ok":x==="running"?"running":"fail"))}async function D(){const x=R();if(!x.email_address){O("fail",t("email-addr-required"));return}if(!x.password){O("fail",t("email-password-required"));return}if(!x.imap_host){O("fail",t("email-host-required"));return}const M=document.getElementById("btn-email-modal-test");M&&(M.disabled=!0),O("running",t("email-test-running"));try{const W=await fetch("/api/email-ingest/test",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:x.email_address,password:x.password,imap_host:x.imap_host,imap_port:x.imap_port,imap_use_ssl:x.imap_use_ssl,folder:x.folder})}),G=await W.json().catch(()=>({}));if(W.ok&&G.success)O("ok",t("email-test-ok",{folder:x.folder,n:G.folder_count??"?"}));else{const K=G.error_msg||"";K==="auth_failed"||/auth/i.test(K)?O("fail",t("email-test-auth-fail")):O("fail",t("email-test-fail",{msg:K||W.status}))}}catch(W){O("fail",t("email-test-fail",{msg:String(W).slice(0,120)}))}finally{M&&(M.disabled=!1)}}async function F(){const x=R();if(!x.email_address){O("fail",t("email-addr-required"));return}if(n==="new"&&!x.password){O("fail",t("email-password-required"));return}if(!x.imap_host){O("fail",t("email-host-required"));return}const M=document.getElementById("btn-email-modal-save");M&&(M.disabled=!0);const W={...x};n==="edit"&&!W.password&&delete W.password;try{const G=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(W)}),K=await G.json().catch(()=>({}));if(G.ok&&K.ok)e=K.account,showToast(t("email-save-ok"),"success"),u(),b(),p();else{const re="email."+(K.detail||"").split(".").slice(-1)[0];O("fail",t(re)!==re?t(re):t("email-save-fail"))}}catch{O("fail",t("email-save-fail"))}finally{M&&(M.disabled=!1)}}async function A(){if(!(!e||!await showConfirm(t("email-unbind-confirm",{email:e.email_address}),{danger:!0,okText:t("email-btn-unbind")})))try{if((await fetch("/api/email-ingest/account",{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){e=null,showToast(t("email-unbind-ok"),"success"),b();const W=document.getElementById("email-logs-list");W&&(W.innerHTML="")}else showToast(t("email-unbind-fail"),"error")}catch{showToast(t("email-unbind-fail"),"error")}}async function f(){if(!e||i)return;if(!e.enabled){showToast(t("email.disabled"),"error");return}i=!0;const x=document.getElementById("btn-email-trigger"),M=x?x.innerHTML:"";x&&(x.disabled=!0,x.innerHTML=`<span>${escapeHtml(t("email-trigger-running"))}</span>`);try{const W=await fetch("/api/email-ingest/trigger",{method:"POST",headers:{Authorization:"Bearer "+token}}),G=await W.json().catch(()=>({}));if(W.ok){const K=G.emails_scanned||0,te=G.ocr_succeeded||0,re=G.ocr_failed||0;K===0&&te===0&&re===0?showToast(t("email-trigger-empty"),"success"):showToast(t("email-trigger-result",{scanned:K,ok:te,fail:re}),re>0?"warn":"success")}else{const te="email."+(G.detail||"").split(".").slice(-1)[0];showToast(t(te)!==te?t(te):t("email-trigger-fail"),"error")}await g()}catch{showToast(t("email-trigger-fail"),"error")}finally{i=!1,x&&(x.disabled=!1,x.innerHTML=M)}}async function l(){if(!e)return;const x=document.getElementById("email-enabled-toggle"),M=!!(x&&x.checked),W=e.enabled;try{const G=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:e.email_address,imap_host:e.imap_host,imap_port:e.imap_port,imap_use_ssl:e.imap_use_ssl,folder:e.folder||"INBOX",filter_subject:e.filter_subject||null,filter_sender:e.filter_sender||null,mark_as_read:e.mark_as_read!==!1,enabled:M})}),K=await G.json().catch(()=>({}));G.ok&&K.ok?(e=K.account,b()):(x&&(x.checked=W),showToast(t("email-toggle-fail"),"error"))}catch{x&&(x.checked=W),showToast(t("email-toggle-fail"),"error")}}async function p(){const x=document.getElementById("email-logs-list");if(x){x.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`;try{const M=await fetch("/api/email-ingest/logs?limit=20",{headers:{Authorization:"Bearer "+token}});if(!M.ok){x.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const W=await M.json();if(!Array.isArray(W)||W.length===0){x.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("email-logs-empty"))}</div>`;return}x.innerHTML=W.map(I).join("")}catch{x.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}function I(x){const M=o(x.created_at),W=x.status||"failed",G=W==="success"?"ok":W==="partial"?"partial":"fail",K=W==="success"?"✓":W==="partial"?"◐":"✗",te=x.trigger==="manual"?`<span class="log-tag manual">${escapeHtml(t("email-log-tag-manual"))}</span>`:`<span class="log-tag auto">${escapeHtml(t("email-log-tag-auto"))}</span>`,re=t("email-log-counts",{scanned:x.emails_scanned||0,att:x.attachments_found||0,ok:x.ocr_succeeded||0,fail:x.ocr_failed||0}),S=(x.elapsed_ms||0)+"ms";return`
            <div class="email-log-row ${G}">
                <span class="log-time">${escapeHtml(M)}</span>
                <span class="log-status">${K}</span>
                ${te}
                <span class="log-counts">${escapeHtml(re)}</span>
                <span class="log-elapsed">${escapeHtml(S)}</span>
            </div>
        `}function L(){const x=document.getElementById("btn-email-bind");x&&x.addEventListener("click",()=>w("new"));const M=document.getElementById("btn-email-edit");M&&M.addEventListener("click",()=>w("edit"));const W=document.getElementById("btn-email-unbind");W&&W.addEventListener("click",A);const G=document.getElementById("btn-email-trigger");G&&G.addEventListener("click",f);const K=document.getElementById("email-enabled-toggle");K&&K.addEventListener("change",l);const te=document.getElementById("email-modal-close");te&&te.addEventListener("click",u);const re=document.getElementById("btn-email-modal-cancel");re&&re.addEventListener("click",u);const S=document.getElementById("btn-email-modal-test");S&&S.addEventListener("click",D);const h=document.getElementById("btn-email-modal-save");h&&h.addEventListener("click",F);const c=document.getElementById("email-preset");c&&c.addEventListener("change",Y=>d(Y.target.value));const $=document.getElementById("email-address");$&&!$.dataset.autoBound&&($.dataset.autoBound="1",$.addEventListener("blur",Y=>k((Y.target.value||"").trim())),$.addEventListener("input",Y=>{const Z=(Y.target.value||"").trim();Z.includes("@")&&Z.split("@")[1].includes(".")&&k(Z)}));const P=document.getElementById("btn-email-refresh-logs");P&&P.addEventListener("click",()=>{P.classList.add("spinning"),setTimeout(()=>P.classList.remove("spinning"),600),p()})}L(),window._loadEmailIngestPanel=g,window._rerenderEmailIngest=function(){if(!s)return;b();const x=document.getElementById("email-logs-section");e&&x&&x.open&&p()};let H=null;window._startEmailLogAutoRefresh=function(){H||(H=setInterval(()=>{e&&s&&p()},3e4))},window._stopEmailLogAutoRefresh=function(){H&&(clearInterval(H),H=null)}})();(function(){let e=[],a=null,n=[],s="all",i=null,g=!1;async function b(){if(g){L();return}g=!0,_(),await o(),L()}function _(){const r=document.getElementById("bank-file-input");r&&!r._bound&&(r._bound=!0,r.addEventListener("change",k));const j=document.getElementById("btn-bank-queue-clear-done");j&&!j._bound&&(j._bound=!0,j.addEventListener("click",D));const z=document.getElementById("btn-bank-back");z&&!z._bound&&(z._bound=!0,z.addEventListener("click",()=>{a=null,n=[],te()}));const J=document.getElementById("btn-bank-delete");J&&!J._bound&&(J._bound=!0,J.addEventListener("click",l));const X=document.getElementById("btn-bank-run-match");X&&!X._bound&&(X._bound=!0,X.addEventListener("click",f)),document.querySelectorAll(".bank-filter-btn").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",()=>{s=fe.dataset.bankFilter||"all",document.querySelectorAll(".bank-filter-btn").forEach(ve=>{ve.classList.toggle("active",ve===fe)}),Z()}))}),document.querySelectorAll("[data-bank-cand-close]").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",ne))});const de=document.getElementById("btn-bank-cand-pane-close");de&&!de._bound&&(de._bound=!0,de.addEventListener("click",ne));const se=document.getElementById("btn-bank-cand-ignore");se&&!se._bound&&(se._bound=!0,se.addEventListener("click",p));const ce=document.getElementById("btn-bank-cand-ignore-pane");ce&&!ce._bound&&(ce._bound=!0,ce.addEventListener("click",p));const ae=document.getElementById("bank-client-badge");ae&&!ae._bound&&(ae._bound=!0,ae.addEventListener("click",h)),document.querySelectorAll("[data-bank-client-picker-close]").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",c))});const pe=document.getElementById("btn-bank-client-picker-save");pe&&!pe._bound&&(pe._bound=!0,pe.addEventListener("click",P)),document.querySelectorAll(".bank-sessions-chip").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",()=>{H=fe.dataset.sessFilter||"all",document.querySelectorAll(".bank-sessions-chip").forEach(ve=>{ve.classList.toggle("active",ve===fe)}),x()}))})}async function o(){try{const r=await fetch("/api/bank-recon/sessions?limit=30",{headers:{Authorization:"Bearer "+token}});if(!r.ok)throw new Error("sessions:"+r.status);e=await r.json(),x()}catch(r){console.warn("[bank-recon] loadSessions failed",r),e=[],x()}}async function v(r){try{const j="/api/bank-recon/sessions/"+encodeURIComponent(r)+(s!=="all"?"?filter="+s:""),z=await fetch(j,{headers:{Authorization:"Bearer "+token}});if(!z.ok)throw new Error("detail:"+z.status);const J=await z.json();a=J.session,n=J.transactions||[],K()}catch(j){console.warn("[bank-recon] loadSessionDetail failed",j),showToast(t("bank-load-failed"),"error")}}let w=[],u=0;const d=3;function E(){return u+=1,"q"+u+"_"+Date.now()}async function k(r){const j=Array.from(r.target.files||[]);if(r.target.value="",j.length!==0){for(const z of j){const J={id:E(),file:z,name:z.name,size:z.size,status:"pending",progress:0,error_code:null,tx_count:0,session_id:null};z.name.toLowerCase().endsWith(".pdf")?z.size>20*1024*1024&&(J.status="failed",J.error_code="bank_recon.file_too_large"):(J.status="failed",J.error_code="bank_recon.only_pdf"),w.push(J)}q(),R(),F()}}function q(){const r=document.getElementById("bank-upload-queue");r&&(r.style.display=""),oe(),ue()}function R(){const r=document.getElementById("bank-upload-queue-list"),j=document.getElementById("bank-upload-queue-summary");if(!r)return;if(w.length===0){r.innerHTML="",j&&(j.textContent="");const se=document.getElementById("bank-upload-queue");se&&(se.style.display="none");return}let z=0,J=0,X=0,de=0;for(const se of w)se.status==="ok"?z++:se.status==="failed"?J++:se.status==="uploading"||se.status==="parsing"?X++:de++;j&&(j.textContent=t("bank-queue-summary").replace("{ok}",z).replace("{run}",X).replace("{wait}",de).replace("{fail}",J)),r.innerHTML=w.map(y).join(""),r.querySelectorAll("[data-q-act]").forEach(se=>{const ce=se.dataset.qAct,ae=se.dataset.qId;se.addEventListener("click",()=>{ce==="retry"&&B(ae),ce==="remove"&&O(ae)})})}function y(r){const j=(r.size/1024).toFixed(0)+" KB";let z="",J="";if(r.status==="pending")z='<span class="bq-stat bq-wait">'+t("bank-queue-status-wait")+"</span>",J='<button data-q-act="remove" data-q-id="'+N(r.id)+'" class="bq-act">×</button>';else if(r.status==="uploading")z='<span class="bq-stat bq-run">'+t("bank-queue-status-uploading")+'</span><div class="bq-bar"><div class="bq-bar-fill" style="width:'+(r.progress||0)+'%"></div></div>';else if(r.status==="parsing")z='<span class="bq-stat bq-run">'+t("bank-queue-status-parsing")+'</span><div class="bq-bar"><div class="bq-bar-fill bq-bar-indet"></div></div>';else if(r.status==="ok")z='<span class="bq-stat bq-ok">'+t("bank-queue-status-ok").replace("{n}",r.tx_count||0)+"</span>",J='<button data-q-act="remove" data-q-id="'+N(r.id)+'" class="bq-act">×</button>';else if(r.status==="failed"){const X=m(r.error_code||"unknown");z='<span class="bq-stat bq-fail" title="'+N(X)+'">'+N(X)+"</span>",J='<button data-q-act="retry" data-q-id="'+N(r.id)+'" class="bq-act bq-act-retry">'+t("bank-queue-retry")+'</button><button data-q-act="remove" data-q-id="'+N(r.id)+'" class="bq-act">×</button>'}return'<div class="bq-row" data-q-row="'+N(r.id)+'"><div class="bq-name" title="'+N(r.name)+'">'+N(r.name)+'</div><div class="bq-size">'+j+'</div><div class="bq-status">'+z+'</div><div class="bq-actions">'+J+"</div></div>"}function B(r){const j=w.find(z=>z.id===r);j&&(j.status="pending",j.error_code=null,j.progress=0,R(),F())}function O(r){const j=w.findIndex(J=>J.id===r);if(j<0)return;const z=w[j];z.status==="uploading"||z.status==="parsing"||(w.splice(j,1),R())}function D(){w=w.filter(r=>r.status!=="ok"),R()}async function F(){for(;;){if(w.filter(z=>z.status==="uploading"||z.status==="parsing").length>=d)return;const j=w.find(z=>z.status==="pending");if(!j){w.every(z=>z.status==="ok"||z.status==="failed")&&(await o(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage());return}A(j).then(()=>F())}}async function A(r){r.status="uploading",r.progress=0,R();try{const j=new FormData;j.append("file",r.file,r.name);const z=await new Promise((X,de)=>{const se=new XMLHttpRequest;se.open("POST","/api/bank-recon/upload"),se.setRequestHeader("Authorization","Bearer "+token),se.upload.onprogress=ce=>{ce.lengthComputable&&(r.progress=Math.min(99,Math.round(ce.loaded/ce.total*100)),R())},se.upload.onload=()=>{r.status="parsing",R()},se.onload=()=>{se.status>=200&&se.status<300?X({status:se.status,text:se.responseText}):X({status:se.status,text:se.responseText})},se.onerror=()=>de(new Error("network")),se.send(j)});let J={};try{J=JSON.parse(z.text||"{}")}catch{J={}}if(z.status>=400){r.status="failed",r.error_code=J&&J.detail||"unknown",R();return}if(J.parse_status==="parse_failed"){r.status="failed",r.error_code=J.error==="scanned_pdf_not_yet"?"bank_recon.scanned":"bank_recon.no_tx",R();return}r.status="ok",r.tx_count=J.tx_count||0,r.session_id=J.session_id||null,R()}catch(j){console.warn("[bank-recon] upload failed",j),r.status="failed",r.error_code="network",R()}}async function f(){if(!a)return;const r=document.getElementById("btn-bank-run-match"),j=r.innerHTML;r.disabled=!0,r.innerHTML="<span>"+t("bank-matching")+"</span>";try{const z=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(a.id)+"/match",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!z.ok)throw new Error("match:"+z.status);const J=await z.json();showToast(t("bank-match-done").replace("{matched}",J.matched).replace("{suggested}",J.suggested).replace("{unmatched}",J.unmatched),"success"),await v(a.id),await o()}catch(z){console.warn("[bank-recon] match failed",z),showToast(t("bank-match-failed"),"error")}finally{r.disabled=!1,r.innerHTML=j}}async function l(){if(!(!a||!await showConfirm(t("bank-delete-confirm"),{danger:!0})))try{const j=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(a.id),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!j.ok)throw new Error("delete:"+j.status);showToast(t("bank-deleted"),"success"),a=null,n=[],te(),await o()}catch(j){console.warn("[bank-recon] delete failed",j),showToast(t("bank-delete-failed"),"error")}}async function p(){if(i)try{const r=await fetch("/api/bank-recon/tx/"+encodeURIComponent(i.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"ignored"})});if(!r.ok)throw new Error("ignore:"+r.status);ne(),await v(a.id)}catch{showToast(t("bank-action-failed"),"error")}}async function I(r){if(i)try{const j=await fetch("/api/bank-recon/tx/"+encodeURIComponent(i.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"matched",history_id:r})});if(!j.ok)throw new Error("pick:"+j.status);showToast(t("bank-matched-ok"),"success"),ne(),await v(a.id)}catch{showToast(t("bank-action-failed"),"error")}}function L(){const r=document.getElementById("bank-status-summary");if(!r)return;if(e.length===0){r.textContent=t("bank-pill-none");return}let z=0;for(const J of e)J.parse_status==="parsed"&&(J.unmatched_count||0)>0&&z++;r.textContent=z>0?t("bank-pill-pending").replace("{n}",z):t("bank-pill-ok")}let H="all";function x(){const r=document.getElementById("bank-sessions-list");if(!r)return;let j=e||[];if(H==="parsed"?j=j.filter(z=>z.parse_status==="parsed"):H==="failed"&&(j=j.filter(z=>z.parse_status==="parse_failed")),!e||e.length===0){r.innerHTML='<div class="bank-empty" data-i18n="bank-sessions-empty">'+t("bank-sessions-empty")+"</div>";return}if(j.length===0){r.innerHTML='<div class="bank-empty">'+t("bank-sess-filter-empty")+"</div>";return}r.innerHTML=j.map(z=>W(z)).join(""),r.querySelectorAll(".bank-session-row").forEach(z=>{z.addEventListener("click",J=>{J.target.closest(".bank-session-trash")||v(z.dataset.sessionId)})}),r.querySelectorAll(".bank-session-trash").forEach(z=>{z.addEventListener("click",J=>{J.stopPropagation();const X=z.dataset.sessionId,de=z.dataset.sessionName||"";M(X,de)})})}async function M(r,j){if(!r)return;const z=(t("bank-session-delete-confirm")||"确定删除这条对账记录吗?").replace("{name}",j||"");if(await showConfirm(z,{danger:!0}))try{const X=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(r),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!X.ok)throw new Error("delete:"+X.status);showToast(t("bank-deleted"),"success"),a&&a.id===r&&(a=null,n=[],te()),await o(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()}catch(X){console.warn("[bank-recon] delete failed",X),showToast(t("bank-delete-failed"),"error")}}window._deleteBankSession=M;function W(r){const j=(r.bank_code||"OTHER").toUpperCase(),z=U(r.period_start,r.period_end),J=r.account_last4?"···"+r.account_last4:"",X=G(r),de=T(r.created_at);return`
            <div class="bank-session-row" data-session-id="${N(r.id)}">
                <div class="bank-session-bank bk-${N(j)}">${N(j)}</div>
                <div class="bank-session-info">
                    <div class="bank-session-title">${N(r.source_filename||z||"-")}</div>
                    <div class="bank-session-meta">${N(z)} · ${N(J)} · ${N(de)}</div>
                </div>
                <div class="bank-session-counts">${X}</div>
                <button class="bank-session-trash" data-session-id="${N(r.id)}" data-session-name="${N(r.source_filename||"")}" title="${N(t("bank-session-delete-tip")||"删除")}">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/>
                    </svg>
                </button>
                <div class="bank-session-arrow">
                    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg>
                </div>
            </div>
        `}function G(r){if(r.parse_status==="parse_failed")return`<span class="bank-session-count cnt-failed">${t("bank-count-parse-failed")}</span>`;if(r.parse_status!=="parsed")return`<span class="bank-session-count">${t("bank-count-parsing")}</span>`;const j=r.tx_count||0,z=r.matched_count||0,J=r.unmatched_count||0,X=[`<span class="bank-session-count">${j} ${t("bank-count-tx")}</span>`];return z>0&&X.push(`<span class="bank-session-count cnt-matched">${z} ${t("bank-count-matched")}</span>`),J>0&&X.push(`<span class="bank-session-count cnt-unmatched">${J} ${t("bank-count-unmatched")}</span>`),X.join("")}function K(){document.getElementById("bank-detail").style.display="",document.querySelector(".bank-sessions-section").style.display="none",Y(),Z(),re()}function te(){document.getElementById("bank-detail").style.display="none",document.querySelector(".bank-sessions-section").style.display="";const r=document.getElementById("bank-detail-body");r&&r.classList.remove("has-pane"),i=null}function re(){const r=document.getElementById("bank-client-badge");if(!r||!a)return;const j=a.client_id,z=document.getElementById("bank-client-badge-dot"),J=document.getElementById("bank-client-badge-name"),X=document.getElementById("bank-client-badge-caret"),de=typeof _userInfo<"u"?_userInfo:null,se=!(de&&de.role==="member");if(j!=null){const ce=(window._clientsCache||[]).find(ae=>Number(ae.id)===Number(j));r.classList.remove("is-empty"),z&&(z.style.background=ce&&ce.color||"#111111"),J&&(J.textContent=ce&&(ce.short_name||ce.name)||"#"+j)}else r.classList.add("is-empty"),z&&(z.style.background=""),J&&(J.textContent=t("bank-client-none"));se?(r.classList.remove("is-readonly"),r.disabled=!1,X&&(X.style.display="")):(r.classList.add("is-readonly"),r.disabled=!0,X&&(X.style.display="none")),r.style.display=""}let S=null;function h(){if(!a)return;const r=typeof _userInfo<"u"?_userInfo:null;if(!!(r&&r.role==="member"))return;S=a.client_id!=null?Number(a.client_id):null,$();const z=document.getElementById("bank-client-picker-modal");z&&(z.style.display="")}function c(){const r=document.getElementById("bank-client-picker-modal");r&&(r.style.display="none"),S=null}function $(){const r=document.getElementById("bank-client-picker-list");if(!r)return;const j=(window._clientsCache||[]).filter(J=>J&&(J.is_active===!0||J.is_active===void 0)),z=[];z.push('<div class="bank-client-picker-row is-none'+(S==null?" is-selected":"")+'" data-cid=""><span class="bank-cp-dot"></span><span>'+N(t("bank-client-picker-none"))+"</span></div>"),j.forEach(J=>{const X=Number(J.id)===Number(S)?" is-selected":"";z.push('<div class="bank-client-picker-row'+X+'" data-cid="'+N(J.id)+'"><span class="bank-cp-dot" style="background:'+N(J.color||"#111111")+'"></span><span>'+N(J.short_name||J.name||"#"+J.id)+"</span></div>")}),r.innerHTML=z.join(""),r.querySelectorAll(".bank-client-picker-row").forEach(J=>{J.addEventListener("click",()=>{const X=J.dataset.cid;S=X?Number(X):null,$()})})}async function P(){if(a)try{const r=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(a.id)+"/client",{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({client_id:S})});if(!r.ok)throw new Error("client:"+r.status);a.client_id=S,re(),showToast(t("bank-client-changed"),"success"),c();try{await o()}catch{}}catch(r){console.warn("[bank-recon] save client failed",r),showToast(t("bank-client-change-failed"),"error")}}function Y(){if(!a)return;const r=a;document.getElementById("bank-detail-title").textContent=(r.bank_code||"-")+(r.account_last4?" ···"+r.account_last4:"")+" · "+(r.source_filename||""),document.getElementById("bank-meta-period").textContent=U(r.period_start,r.period_end)||"-",document.getElementById("bank-meta-opening").textContent=C(r.opening_balance),document.getElementById("bank-meta-inflow").textContent="+"+C(r.total_inflow),document.getElementById("bank-meta-outflow").textContent="-"+C(r.total_outflow),document.getElementById("bank-meta-closing").textContent=C(r.closing_balance);const j=n||[],z=j.length;let J=0,X=0,de=0;for(const se of j){const ce=se.match_status||"unmatched";ce==="matched"?J++:ce==="suggested"?X++:de++}document.getElementById("bank-stat-total").textContent=z,document.getElementById("bank-stat-matched").textContent=J,document.getElementById("bank-stat-suggested").textContent=X,document.getElementById("bank-stat-unmatched").textContent=de}function Z(){const r=document.getElementById("bank-tx-tbody");if(!r)return;let j=n||[];if(s!=="all"&&(j=j.filter(z=>s==="matched"?z.match_status==="matched":s==="suggested"?z.match_status==="suggested":s==="unmatched"?z.match_status==="unmatched"||z.match_status==="ignored":!0)),j.length===0){r.innerHTML=`<tr><td colspan="4" class="bank-empty">${t("bank-tx-empty")}</td></tr>`;return}if(r.innerHTML=j.map(z=>le(z)).join(""),r.querySelectorAll("tr[data-tx-id]").forEach(z=>{z.addEventListener("click",()=>{const J=z.dataset.txId,X=n.find(de=>de.id===J);X&&(r.querySelectorAll("tr.is-selected").forEach(de=>de.classList.remove("is-selected")),z.classList.add("is-selected"),ie(X))})}),i){const z=r.querySelector('tr[data-tx-id="'+i.id+'"]');z&&z.classList.add("is-selected")}}function le(r){const j=r.direction==="OUT",z=j?"-":"+",J=j?"bank-out":"bank-in",X=r.match_status||"unmatched",de=t("bank-match-"+X)||X,se=T(r.tx_date),ce=r.channel?`<span class="bank-tx-channel">${N(r.channel)}</span>`:"";return`
            <tr data-tx-id="${N(r.id)}">
                <td class="bank-tx-date">${N(se)}</td>
                <td class="bank-tx-desc">${ce}${N(r.description||"-")}</td>
                <td class="bank-td-amount ${J}">${z}${C(r.amount)}</td>
                <td><span class="bank-tx-match mt-${X}">${N(de)}</span></td>
            </tr>
        `}async function ie(r){i=r;const j=document.getElementById("bank-detail-body");j&&j.classList.add("has-pane");const z=document.getElementById("bank-cand-pane-title"),J=document.getElementById("bank-cand-pane-sub"),X=document.getElementById("bank-cand-pane-foot");if(z&&(z.textContent=t("bank-cand-pane-current")),J){const se=r.direction==="OUT"?"-":"+",ce=r.direction==="OUT"?"bank-out":"bank-in";J.innerHTML=`${N(T(r.tx_date))}
                <span style="margin:0 6px;color:#D1D5DB">·</span>
                <span>${N(r.description||"-")}</span>
                <span style="margin:0 6px;color:#D1D5DB">·</span>
                <strong class="${ce}">${se}${C(r.amount)}</strong>`}X&&(X.style.display="");const de=document.getElementById("bank-cand-pane-body");if(de){de.innerHTML=`<div class="bank-empty">${t("bank-cand-loading")}</div>`;try{const se=await fetch("/api/bank-recon/tx/"+encodeURIComponent(r.id)+"/candidates",{headers:{Authorization:"Bearer "+token}});if(!se.ok)throw new Error("cands:"+se.status);const ce=await se.json();ee(r,ce.candidates||[])}catch{de.innerHTML=`<div class="bank-empty">${t("bank-cand-load-failed")}</div>`}}}function V(r){const j=Number(r||0);let z="score-low";return j>=85?z="score-high":j>=60&&(z="score-mid"),'<span class="bank-cand-score '+z+'">'+j.toFixed(0)+" "+t("bank-cand-score-unit")+"</span>"}function Q(r,j,z){const J=j.history_id,X=j.invoice_no||"-",de=j.vendor||"-",se=j.amount_total!==null&&j.amount_total!==void 0?C(j.amount_total):"-",ce=j.invoice_date?T(j.invoice_date):"-",ae=j.filename||"",pe=!!z&&r.matched_history_id===J,fe="bank-cand-card"+(j.is_auto_picked?" is-auto":"")+(pe?" is-picked":"");let ve="";return pe?ve='<button class="btn btn-ghost btn-small" data-act="unmatch"><span>'+t("bank-cand-unmatch")+"</span></button>":ve='<button class="btn btn-primary btn-small" data-act="pick" data-hid="'+N(J)+'"><span>'+t(j.is_auto_picked?"bank-cand-confirm":"bank-cand-pick-this")+"</span></button>",'<div class="'+fe+'" data-hid="'+N(J)+'"><div class="bank-cand-card-head"><div class="bank-cand-card-vendor">'+N(de)+"</div>"+V(j.score)+'</div><div class="bank-cand-card-fields"><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-invoice-no")+"</span> "+N(X)+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-amount")+"</span> "+se+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-date")+"</span> "+N(ce)+"</span></div>"+(ae?'<div class="bank-cand-card-file" title="'+N(ae)+'">'+N(ae)+"</div>":"")+(j.reason?'<div class="bank-cand-card-reason">'+N(j.reason)+"</div>":"")+'<div class="bank-cand-card-actions">'+ve+"</div></div>"}function ee(r,j){const z=document.getElementById("bank-cand-pane-body");if(!z)return;const J=j||[];let X="";if(r.match_status==="matched")X='<div class="bank-cand-hint hint-matched">'+t("bank-cand-hint-matched").replace("{n}",J.length)+"</div>";else if(r.match_status==="suggested")X='<div class="bank-cand-hint hint-suggested">'+t("bank-cand-hint-suggested").replace("{n}",J.length)+"</div>";else if(J.length>0)X='<div class="bank-cand-hint hint-low">'+t("bank-cand-hint-low").replace("{n}",J.length)+"</div>";else{z.innerHTML='<div class="bank-empty">'+t("bank-cand-no-match-detail")+"</div>";return}const de=r.match_status==="matched",se=J.map(ce=>Q(r,ce,de)).join("");z.innerHTML=X+'<div class="bank-cand-list">'+se+"</div>",z.querySelectorAll('[data-act="pick"]').forEach(ce=>{ce.addEventListener("click",()=>{I(ce.dataset.hid)})}),z.querySelectorAll('[data-act="unmatch"]').forEach(ce=>{ce.addEventListener("click",async()=>{try{await fetch("/api/bank-recon/tx/"+encodeURIComponent(r.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"unmatched"})}),ne(),await v(a.id)}catch{showToast(t("bank-action-failed"),"error")}})})}function ne(){const r=document.getElementById("bank-detail-body");r&&r.classList.remove("has-pane");const j=document.getElementById("bank-cand-pane-title"),z=document.getElementById("bank-cand-pane-sub"),J=document.getElementById("bank-cand-pane-body"),X=document.getElementById("bank-cand-pane-foot");j&&(j.textContent=t("bank-cand-pane-empty-title")),z&&(z.textContent=t("bank-cand-pane-empty-sub")),X&&(X.style.display="none"),J&&(J.innerHTML='<div class="bank-cand-pane-empty"><svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="14" y="10" width="36" height="44" rx="3"/><path d="M22 22h20M22 30h20M22 38h12"/></svg><div>'+t("bank-cand-pane-empty-hint")+"</div></div>");const de=document.getElementById("bank-tx-tbody");de&&de.querySelectorAll("tr.is-selected").forEach(se=>se.classList.remove("is-selected")),i=null}function oe(r){const j=document.getElementById("bank-upload-progress");j&&(j.style.display="none")}function ue(){const r=document.getElementById("bank-upload-error");r&&(r.style.display="none")}function m(r){return{"bank_recon.only_pdf":t("bank-err-only-pdf"),"bank_recon.empty_file":t("bank-err-empty"),"bank_recon.file_too_large":t("bank-err-too-large"),"bank_recon.save_failed":t("bank-err-server"),"bank_recon.scanned":t("bank-err-scanned"),"bank_recon.no_tx":t("bank-err-no-tx"),network:t("bank-err-network")}[r]||t("bank-err-unknown")+" ("+r+")"}function C(r){if(r==null)return"-";const j=Number(r);return isNaN(j)?"-":j.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function T(r){if(!r)return"-";const j=String(r);return j.length>=10?j.slice(0,10):j}function U(r,j){return!r&&!j?"":(T(r)||"?")+" ~ "+(T(j)||"?")}function N(r){return r==null?"":String(r).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}window._loadBankReconPanel=b,window._rerenderBankRecon=function(){if(currentRoute==="automation"){if(x(),a&&(Y(),Z(),re(),!i)){const r=document.getElementById("bank-cand-pane-title"),j=document.getElementById("bank-cand-pane-sub");r&&(r.textContent=t("bank-cand-pane-empty-title")),j&&(j.textContent=t("bank-cand-pane-empty-sub"))}R()}},typeof window.subscribeI18n=="function"&&window.subscribeI18n("bank-recon",window._rerenderBankRecon),window._openBankSession=async function(r){r&&(g||await b(),await v(r))}})();(function(){const e=document.getElementById("page-clients");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const a=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",n=window.I18N;n&&n[a]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const i=s.getAttribute("data-i18n");n[a][i]&&(s.textContent=n[a][i])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const i=s.getAttribute("data-i18n-placeholder");n[a][i]&&(s.placeholder=n[a][i])}))}catch{}}})();(function(){let e=[],a=null,n="",s="seller";const i={page:0,pageSize:12,keyword:""},g=new Set;let b=[];const _={keyword:""};let o=null;function v(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}async function w(c,$={}){const P=await fetch(c,{...$,headers:{"Content-Type":"application/json",...v(),...$.headers||{}}});if(!P.ok){const Y=await P.json().catch(()=>({}));throw new Error(Y.detail||"HTTP "+P.status)}return P.json()}async function u(){try{e=(await w("/api/clients")).clients||[],window._clientsCache=e}catch(c){console.error("loadClientsCache fail",c),e=[]}try{typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter()}catch{}try{typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher()}catch{}return e}function d(c){s=c==="buyer"?"buyer":"seller",document.querySelectorAll("[data-cust-tab]").forEach(Y=>Y.classList.toggle("active",Y.dataset.custTab===s));const $=document.getElementById("cust-pane-seller"),P=document.getElementById("cust-pane-buyer");$&&$.classList.toggle("active",s==="seller"),P&&P.classList.toggle("active",s==="buyer")}function E(){const c=window._userInfo||{},$=String(c.role||"").toLowerCase(),P=String(c.tenant_role||"").toLowerCase();return c.is_super_admin===!0||c.is_owner===!0||$==="owner"||$==="admin"||P==="owner"||P==="admin"}function k(){window._workspaceClientsCache=b,typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl()}async function q(){try{const c=await w("/api/workspace/clients");b=c&&(c.clients||c.items)||[],window._workspaceClientsCache=b}catch(c){console.error("loadSellerCache fail",c),b=[]}return b}function R(){const c=_.keyword.trim().toLowerCase();return c?b.filter($=>($.name||"").toLowerCase().includes(c)||($.tax_id||"").toLowerCase().includes(c)):b}function y(){const c=document.getElementById("seller-tbody");if(!c)return;const $=E(),P=document.getElementById("btn-seller-new");P&&(P.style.display=$?"":"none");const Y=R(),Z=typeof window.getActiveWorkspaceClientId=="function"?window.getActiveWorkspaceClientId():null;if(!Y.length){c.innerHTML=`<div class="cust-empty">${escapeHtml(t(_.keyword?"cust-no-match":"seller-empty"))}</div>`;return}c.innerHTML=Y.map(le=>{const V=Z!=null&&Number(Z)===Number(le.id)?`<span class="cust-badge-current"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7.5l3.2 3.2L12 4"/></svg>${escapeHtml(t("seller-current"))}</span>`:`<button class="cust-row-btn primary" data-saction="activate" data-wid="${le.id}">${escapeHtml(t("seller-set-current"))}</button>`,Q=$?`
                <button class="cust-row-btn" data-saction="edit" data-wid="${le.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
                <button class="cust-row-btn danger" data-saction="archive" data-wid="${le.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h10M4 4v7a1 1 0 001 1h4a1 1 0 001-1V4M5.5 4V2.8a1 1 0 011-1h1a1 1 0 011 1V4"/></svg><span>${escapeHtml(t("wsclient-archive"))}</span></button>`:"";return`<div class="cust-row seller-grid" data-wid="${le.id}">
                <div class="cust-cell-name"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" style="flex-shrink:0;opacity:.55"><rect x="2" y="5" width="12" height="9" rx="1"/><path d="M10 14V4a1 1 0 00-1-1H7a1 1 0 00-1 1v10"/></svg><span class="cust-name-text">${escapeHtml(le.name||"#"+le.id)}</span></div>
                <div class="cust-cell-tax">${escapeHtml(le.tax_id||"—")}</div>
                <div class="align-right">${le.invoice_count||0}</div>
                <div class="cust-row-actions">${V}${Q}</div>
            </div>`}).join("")}function B(c){o=c?c.id:null,document.getElementById("wsclient-modal-title").textContent=t(c?"wsclient-modal-edit":"wsclient-modal-new"),document.getElementById("wsclient-input-name").value=c&&c.name||"",document.getElementById("wsclient-input-tax").value=c&&c.tax_id||"",document.getElementById("wsclient-modal-archive").style.display=c?"":"none",document.getElementById("wsclient-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("wsclient-input-name").focus(),50)}function O(){document.getElementById("wsclient-modal-mask").style.display="none",o=null}async function D(){const c=document.getElementById("wsclient-input-name").value.trim(),$=document.getElementById("wsclient-input-tax").value.trim();if(!c){showToast(t("client-msg-name-required"),"fail");return}try{o?(await w("/api/workspace/clients/"+o,{method:"PATCH",body:JSON.stringify({name:c,tax_id:$})}),showToast(t("client-msg-updated"),"success")):(await w("/api/workspace/clients",{method:"POST",body:JSON.stringify({name:c,tax_id:$||null})}),showToast(t("client-msg-created"),"success")),O(),await q(),y(),k()}catch(P){const Y=P&&P.message?P.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+Y,"fail")}}async function F(){if(!o)return;const c=b.find(P=>Number(P.id)===Number(o));if(await showConfirm(t("wsclient-archive-confirm").replace("{name}",c?c.name:""),{danger:!0}))try{const P=o;await w("/api/workspace/clients/"+P,{method:"DELETE"}),showToast(t("wsclient-archived"),"success"),typeof window.getActiveWorkspaceClientId=="function"&&Number(window.getActiveWorkspaceClientId())===Number(P)&&typeof window.enterPersonalMode=="function"&&window.enterPersonalMode(),O(),await q(),y(),k()}catch{showToast(t("client-msg-save-fail"),"fail")}}function A(){const c=i.keyword.trim().toLowerCase();return c?e.filter($=>($.name||"").toLowerCase().includes(c)||($.short_name||"").toLowerCase().includes(c)||($.tax_id||"").toLowerCase().includes(c)):e}function f(){const c=A(),$=i.pageSize,P=Math.max(0,Math.ceil(c.length/$)-1);i.page>P&&(i.page=P);const Y=i.page*$;return{all:c,items:c.slice(Y,Y+$),start:Y,ps:$,total:c.length,maxPage:P}}function l(){const c=document.getElementById("buyer-tbody");if(!c)return;const{items:$,start:P,ps:Y,total:Z,maxPage:le}=f();Z?c.innerHTML=$.map(ee=>{const ne=g.has(ee.id);return`<div class="cust-row buyer-grid${ne?" selected":""}" data-cid="${ee.id}">
                    <div class="cust-cell-check"><input type="checkbox" class="buyer-row-check" data-cid="${ee.id}" ${ne?"checked":""}></div>
                    <div style="min-width:0">
                        <div class="cust-cell-name"><span class="cust-color-dot" style="background:${escapeHtml(ee.color||"#111")}"></span><span class="cust-name-text">${escapeHtml(ee.name)}</span></div>
                        ${ee.tax_id?`<div class="cust-cell-sub">${escapeHtml(ee.tax_id)}</div>`:""}
                    </div>
                    <div class="align-right">${ee.invoice_count||0}</div>
                    <div class="align-right cust-cell-amount">฿${(ee.total_amount||0).toLocaleString(void 0,{maximumFractionDigits:0})}</div>
                    <div class="cust-row-actions">
                        <button class="cust-row-btn" data-action="edit" data-cid="${ee.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
                        <button class="cust-row-btn" data-action="export" data-cid="${ee.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 2v7M4 6l3 3 3-3M2 11h10"/></svg><span>${escapeHtml(t("client-card-export"))}</span></button>
                    </div>
                </div>`}).join(""):c.innerHTML=`<div class="cust-empty">${escapeHtml(t(i.keyword?"cust-no-match":"clients-empty"))}</div>`;const ie=document.getElementById("buyer-pager-info");ie&&(ie.textContent=Z?`${P+1}–${Math.min(P+Y,Z)} / ${Z}`:"0");const V=document.getElementById("buyer-prev");V&&(V.disabled=i.page<=0);const Q=document.getElementById("buyer-next");Q&&(Q.disabled=i.page>=le),p()}function p(){const c=g.size,$=document.getElementById("buyer-batch-bar");$&&($.style.display=c?"flex":"none");const P=document.getElementById("buyer-batch-count");P&&(P.textContent=t("cust-selected-n").replace("{n}",c));const Y=document.getElementById("buyer-check-all");if(Y){const{items:Z}=f(),le=Z.map(V=>V.id),ie=le.filter(V=>g.has(V)).length;Y.checked=le.length>0&&ie===le.length,Y.indeterminate=ie>0&&ie<le.length}}function I(){g.clear(),l()}async function L(){const c=Array.from(g);if(!(!c.length||!await showConfirm(t("cust-batch-del-confirm").replace("{n}",c.length),{danger:!0})))try{await w("/api/clients/batch-delete",{method:"POST",body:JSON.stringify({ids:c})}),showToast(t("client-msg-deleted"),"success"),g.clear(),await u(),l(),te(),h()}catch{showToast(t("client-msg-save-fail"),"fail")}}window.loadClientsPage=async function(){const c=document.getElementById("seller-tbody");c&&(c.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`);const $=document.getElementById("buyer-tbody");$&&($.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`),await Promise.all([q(),u()]),y(),l()},window.addEventListener("pearnly:workspace-changed",function(){typeof currentRoute<"u"&&currentRoute==="clients"&&y()});function H(c){a=c?c.id:null;const $=!!c;document.getElementById("client-modal-title").textContent=t($?"client-modal-edit":"client-modal-new"),document.getElementById("client-input-name").value=c&&c.name||"",document.getElementById("client-input-short").value=c&&c.short_name||"",document.getElementById("client-input-tax").value=c&&c.tax_id||"",document.getElementById("client-input-address").value=c&&c.address||"",document.getElementById("client-input-contact").value=c&&c.contact_person||"",document.getElementById("client-input-phone").value=c&&c.contact_phone||"",document.getElementById("client-input-email").value=c&&c.contact_email||"",document.getElementById("client-input-notes").value=c&&c.notes||"";const P=c&&c.color||"#111111";document.querySelectorAll("#client-color-picker .color-swatch").forEach(Y=>{Y.classList.toggle("active",Y.dataset.color===P)}),document.getElementById("client-modal-delete").style.display=$?"":"none",document.getElementById("client-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("client-input-name").focus(),50)}function x(){document.getElementById("client-modal-mask").style.display="none",a=null}function M(){const c=document.querySelector("#client-color-picker .color-swatch.active");return c?c.dataset.color:"#111111"}async function W(){const c=document.getElementById("client-input-name").value.trim();if(!c){showToast(t("client-msg-name-required"),"fail");return}const $={name:c,short_name:document.getElementById("client-input-short").value.trim()||null,tax_id:document.getElementById("client-input-tax").value.trim()||null,address:document.getElementById("client-input-address").value.trim()||null,contact_person:document.getElementById("client-input-contact").value.trim()||null,contact_phone:document.getElementById("client-input-phone").value.trim()||null,contact_email:document.getElementById("client-input-email").value.trim()||null,notes:document.getElementById("client-input-notes").value.trim()||null,color:M()};try{a?(await w(`/api/clients/${a}`,{method:"PATCH",body:JSON.stringify($)}),showToast(t("client-msg-updated"),"success")):(await w("/api/clients",{method:"POST",body:JSON.stringify($)}),showToast(t("client-msg-created"),"success")),x(),await u(),currentRoute==="clients"&&l(),te(),h()}catch(P){console.error("saveClient fail",P);const Y=P&&P.message?P.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+Y,"fail")}}async function G(){if(!a)return;const c=e.find(Y=>Y.id===a);if(!c)return;const $=t("client-delete-confirm").replace("{name}",c.name);if(await showConfirm($,{danger:!0}))try{await w(`/api/clients/${a}`,{method:"DELETE"}),showToast(t("client-msg-deleted"),"success"),x(),await u(),currentRoute==="clients"&&l(),te(),h()}catch(Y){console.error(Y),showToast(t("client-msg-save-fail"),"fail")}}async function K(c){const $=e.find(P=>P.id===c);if(typeof window.openClientExportModal=="function"){window.openClientExportModal(c,$?$.name:"");return}try{const P=localStorage.getItem("mrpilot_token"),Y=await fetch(`/api/clients/${c}/export?month=all`,{headers:{Authorization:"Bearer "+P}});if(!Y.ok){let Q="HTTP "+Y.status;try{const ee=await Y.json();ee&&ee.detail&&(Q=ee.detail)}catch{}throw new Error(Q)}const Z=await Y.blob();if(Z.size<200){showToast(t("client-export-month-empty"),"info");return}const le=$&&$.name?$.name.replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40):"client",ie=URL.createObjectURL(Z),V=document.createElement("a");V.href=ie,V.download=`${le}_export.csv`,V.click(),URL.revokeObjectURL(ie)}catch(P){console.error("exportClient fail",P),showToast(t("client-msg-save-fail")+" · "+(P.message||""),"fail")}}function te(){const c=document.getElementById("drawer-client-select");if(!c)return;const $=c.value;c.innerHTML=`<option value="">${escapeHtml(t("drawer-client-none"))}</option>`+e.map(P=>`<option value="${P.id}">${escapeHtml(P.name)}</option>`).join(""),c.value=$||""}window.bindDrawerClient=function(c,$){const P=document.getElementById("drawer-client-select");if(!P)return;if(te(),P.value=$?String($):"",!c){P.onchange=null;const Z=document.getElementById("drawer-client-add");Z&&(Z.onclick=()=>H(null));return}P.onchange=async()=>{const Z=P.value?parseInt(P.value,10):null;try{await w(`/api/history/${c}/assign_client`,{method:"POST",body:JSON.stringify({client_id:Z})}),showToast(t("client-msg-updated"),"success");const le=_results[_drawerIdx];le&&(le.client_id=Z),await u()}catch(le){console.error(le),showToast(t("client-msg-save-fail"),"fail"),P.value=$?String($):""}};const Y=document.getElementById("drawer-client-add");Y&&(Y.onclick=()=>H(null))};let re={fetched:0,items:[],supplier_count:0};window.fillCategoryDatalist=async function(){try{const c=document.getElementById("drawer-cat-datalist"),$=Date.now();if($-re.fetched<300*1e3){c&&(c.innerHTML=re.items.map(Y=>`<option value="${escapeHtml(Y)}">`).join("")),S(re.supplier_count);return}const P=await w("/api/categories",{method:"GET"});re.fetched=$,re.items=P&&P.categories||[],re.supplier_count=P&&P.supplier_count||0,c&&(c.innerHTML=re.items.map(Y=>`<option value="${escapeHtml(Y)}">`).join("")),S(re.supplier_count)}catch(c){console.warn("fillCategoryDatalist failed",c)}};function S(c){const $=document.getElementById("drawer-cat-learned-tag");$&&c>0&&($.textContent=(t("drawer-suggest-learned-with-count")||"已学 {n}").replace("{n}",c))}function h(){const c=document.getElementById("history-client-filter");if(!c)return;const $=c.value;c.innerHTML=`<option value="">${escapeHtml(t("history-client-all"))}</option>`+e.map(P=>`<option value="${P.id}">${escapeHtml(P.name)}</option>`).join(""),c.value=$||""}window.getHistoryClientFilter=function(){return n},document.addEventListener("DOMContentLoaded",()=>{const c=document.querySelector(".cust-tab-bar");c&&c.addEventListener("click",ae=>{const pe=ae.target.closest("[data-cust-tab]");pe&&d(pe.dataset.custTab)});const $=document.getElementById("btn-buyer-new");$&&$.addEventListener("click",()=>H(null));const P=document.getElementById("buyer-tbody");P&&P.addEventListener("click",ae=>{const pe=ae.target.closest(".buyer-row-check");if(pe){const he=parseInt(pe.dataset.cid,10);pe.checked?g.add(he):g.delete(he);const ye=pe.closest(".cust-row");ye&&ye.classList.toggle("selected",pe.checked),p();return}const fe=ae.target.closest(".cust-row-btn");if(fe){ae.stopPropagation();const he=parseInt(fe.dataset.cid,10);if(fe.dataset.action==="edit"){const ye=e.find(xe=>xe.id===he);ye&&H(ye)}else fe.dataset.action==="export"&&K(he);return}const ve=ae.target.closest(".cust-row");if(ve&&!ae.target.closest(".cust-cell-check")){const he=e.find(ye=>ye.id===parseInt(ve.dataset.cid,10));he&&H(he)}});const Y=document.getElementById("buyer-check-all");Y&&Y.addEventListener("change",()=>{const{items:ae}=f();ae.forEach(pe=>{Y.checked?g.add(pe.id):g.delete(pe.id)}),l()});const Z=document.getElementById("buyer-batch-cancel");Z&&Z.addEventListener("click",I);const le=document.getElementById("buyer-batch-delete");le&&le.addEventListener("click",L);const ie=document.getElementById("buyer-prev");ie&&ie.addEventListener("click",()=>{i.page>0&&(i.page--,l())});const V=document.getElementById("buyer-next");V&&V.addEventListener("click",()=>{i.page++,l()});const Q=document.getElementById("buyer-search");if(Q){let ae;Q.addEventListener("input",()=>{clearTimeout(ae),ae=setTimeout(()=>{i.keyword=Q.value,i.page=0;const pe=document.getElementById("buyer-search-clear");pe&&(pe.style.display=Q.value?"":"none"),l()},200)})}const ee=document.getElementById("buyer-search-clear");ee&&ee.addEventListener("click",()=>{const ae=document.getElementById("buyer-search");ae&&(ae.value=""),i.keyword="",i.page=0,ee.style.display="none",l()});const ne=document.getElementById("btn-seller-new");ne&&ne.addEventListener("click",()=>B(null));const oe=document.getElementById("seller-tbody");oe&&oe.addEventListener("click",ae=>{const pe=ae.target.closest("[data-saction]");if(!pe)return;ae.stopPropagation();const fe=parseInt(pe.dataset.wid,10),ve=pe.dataset.saction,he=b.find(ye=>Number(ye.id)===fe);ve==="activate"?(typeof window.setActiveWorkspaceClientId=="function"&&window.setActiveWorkspaceClientId(fe),y(),typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl(),showToast(t("seller-activated").replace("{name}",he?he.name:""),"success")):ve==="edit"?he&&B(he):ve==="archive"&&(o=fe,F())});const ue=document.getElementById("seller-search");if(ue){let ae;ue.addEventListener("input",()=>{clearTimeout(ae),ae=setTimeout(()=>{_.keyword=ue.value;const pe=document.getElementById("seller-search-clear");pe&&(pe.style.display=ue.value?"":"none"),y()},200)})}const m=document.getElementById("seller-search-clear");m&&m.addEventListener("click",()=>{const ae=document.getElementById("seller-search");ae&&(ae.value=""),_.keyword="",m.style.display="none",y()});const C=document.getElementById("wsclient-modal-close");C&&C.addEventListener("click",O);const T=document.getElementById("wsclient-modal-cancel");T&&T.addEventListener("click",O);const U=document.getElementById("wsclient-modal-save");U&&U.addEventListener("click",D);const N=document.getElementById("wsclient-modal-archive");N&&N.addEventListener("click",F);const r=document.getElementById("wsclient-modal-mask");r&&r.addEventListener("click",ae=>{ae.target===r&&O()});const j=document.getElementById("client-modal-close");j&&j.addEventListener("click",x);const z=document.getElementById("client-modal-cancel");z&&z.addEventListener("click",x);const J=document.getElementById("client-modal-save");J&&J.addEventListener("click",W);const X=document.getElementById("client-modal-delete");X&&X.addEventListener("click",G);const de=document.getElementById("client-modal-mask");de&&de.addEventListener("click",ae=>{ae.target===de&&x()});const se=document.getElementById("client-color-picker");se&&se.addEventListener("click",ae=>{const pe=ae.target.closest(".color-swatch");pe&&(se.querySelectorAll(".color-swatch").forEach(fe=>fe.classList.remove("active")),pe.classList.add("active"))});const ce=document.getElementById("history-client-filter");ce&&ce.addEventListener("change",()=>{n=ce.value,typeof renderHistoryList=="function"&&renderHistoryList()})}),setTimeout(()=>u(),1e3)})();(function(){const e=document.getElementById("page-exceptions");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const a=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",n=window.I18N;n&&n[a]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const i=s.getAttribute("data-i18n");n[a][i]&&(s.textContent=n[a][i])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const i=s.getAttribute("data-i18n-placeholder");n[a][i]&&(s.placeholder=n[a][i])}))}catch{}}})();(function(){let e={statsCache:null,listCache:[],currentRule:null,currentClient:"",currentStatus:"pending",loading:!1,selectedIds:new Set,offset:0,pageSize:50,total:0,loadFailed:!1,listScrollY:0};function a(S,h){let c=t(S)||S;if(h)for(const $ in h)c=c.replace(new RegExp("\\{"+$+"\\}","g"),String(h[$]));return c}async function n(){try{const S=e.currentClient||"",h="/api/exceptions/stats?status=pending"+(S?"&client_id="+encodeURIComponent(S):""),c=await fetch(h,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!c.ok)return;const $=await c.json(),P=document.getElementById("nav-exc-badge");if(!P)return;const Y=parseInt($.pending||0,10);Y>0?(P.textContent=Y>99?"99+":String(Y),P.style.display=""):P.style.display="none"}catch{}}function s(S){return S==="high"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M7 1.5L1 12.5h12L7 1.5z"/>
                <line x1="7" y1="6" x2="7" y2="9"/>
                <circle cx="7" cy="10.6" r="0.5" fill="currentColor"/>
            </svg>`:S==="medium"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="7" cy="7" r="5.5"/>
                <line x1="7" y1="4" x2="7" y2="7.5"/>
                <circle cx="7" cy="9.5" r="0.5" fill="currentColor"/>
            </svg>`:`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="7" cy="7" r="5.5"/>
            <line x1="4.5" y1="7" x2="9.5" y2="7"/>
        </svg>`}function i(){return`<svg class="exc-empty-icon" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 19l5 5 13-13"/>
            <circle cx="20" cy="20" r="17"/>
        </svg>`}function g(S){if(S==null)return"—";const h=parseFloat(S);return isNaN(h)?"—":"฿ "+h.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function b(S){return S?S.slice(0,10):"—"}function _(S){document.getElementById("exc-kpi-pending").textContent=S.pending||0,document.getElementById("exc-kpi-high").textContent=S.high_severity||0,document.getElementById("exc-kpi-resolved").textContent=S.resolved||0,document.getElementById("exc-kpi-learned").textContent=S.learned_rules||0;const h=document.getElementById("exc-status-tab-count-pending"),c=document.getElementById("exc-status-tab-count-resolved"),$=document.getElementById("exc-status-tab-count-ignored");h&&(h.textContent=S.pending||0),c&&(c.textContent=S.resolved||0),$&&($.textContent=S.ignored||0),document.querySelectorAll("#exc-status-tabs .exc-status-tab").forEach(Y=>{Y.classList.toggle("active",Y.dataset.status===(e.currentStatus||"pending"))})}function o(S){const h=document.getElementById("exc-chips");if(!h)return;const c=S.by_rule||{},$=["confidence_low","duplicate","amount_missing","math_mismatch","tax_id_format_invalid"];let Y=`<button class="exc-chip ${!e.currentRule?"active":""}" data-rule="">
            <span>${escapeHtml(t("exc-chip-all"))}</span>
            <span class="exc-chip-count">${S.pending||0}</span>
        </button>`;for(const Z of $){const le=c[Z]||0;if(le===0&&e.currentRule!==Z)continue;const ie=e.currentRule===Z;Y+=`<button class="exc-chip ${ie?"active":""}" data-rule="${escapeHtml(Z)}">
                <span>${escapeHtml(t("exc-chip-"+Z))}</span>
                <span class="exc-chip-count">${le}</span>
            </button>`}h.innerHTML=Y,h.querySelectorAll(".exc-chip").forEach(Z=>{Z.addEventListener("click",()=>{const le=Z.dataset.rule||null;e.currentRule=le,k()})})}function v(S){const h=document.getElementById("exc-list");if(!h)return;if(!S||S.length===0){h.innerHTML=`<div class="exc-empty">
                ${i()}
                <div class="exc-empty-title">${escapeHtml(t("exc-empty-title"))}</div>
                <div>${escapeHtml(t("exc-empty-desc"))}</div>
            </div>`,u();return}const c='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7l3 3 5-5"/></svg>',$=(e.currentStatus||"pending")==="pending";h.innerHTML=S.map(P=>{const Y=P.severity||"medium",Z=t("exc-rule-"+P.rule_code)||P.rule_code,le=P.seller_name&&P.seller_name.trim()?P.seller_name:t("exc-no-seller"),ie=P.filename||"—",V=b(P.invoice_date||P.created_at),Q=P.status==="pending",ee=e.selectedIds.has(P.id),ne=$&&Q;return`
                <div class="exc-row sev-${escapeHtml(Y)} ${ee?"selected":""}" data-exc-id="${escapeHtml(String(P.id))}">
                    <div class="exc-row-check ${ee?"checked":""}" data-check-id="${escapeHtml(String(P.id))}" ${ne?"":'style="visibility:hidden;"'}>${c}</div>
                    <div class="exc-row-sev">${s(Y)}</div>
                    <div class="exc-row-main">
                        <div class="exc-row-title">${escapeHtml(le)} · ${escapeHtml(ie)}</div>
                        <div class="exc-row-meta">
                            ${P.invoice_no?`<span><b>${escapeHtml(P.invoice_no)}</b></span>`:""}
                            <span>${escapeHtml(V)}</span>
                        </div>
                    </div>
                    <div class="exc-row-rule r-${escapeHtml(Y)}">${escapeHtml(Z)}</div>
                    <div class="exc-row-amount">${escapeHtml(g(P.total_amount))}</div>
                </div>
            `}).join(""),h.querySelectorAll(".exc-row").forEach(P=>{P.addEventListener("click",Y=>{if(Y.target.closest(".exc-row-check"))return;const Z=P.dataset.excId;Z&&D(parseInt(Z,10))})}),h.querySelectorAll(".exc-row-check").forEach(P=>{P.addEventListener("click",Y=>{Y.stopPropagation();const Z=parseInt(P.dataset.checkId,10);Z&&(e.selectedIds.has(Z)?(e.selectedIds.delete(Z),P.classList.remove("checked"),P.closest(".exc-row").classList.remove("selected")):(e.selectedIds.add(Z),P.classList.add("checked"),P.closest(".exc-row").classList.add("selected")),w())})}),w(),u()}function w(){const S=document.getElementById("exc-batch-bar"),h=document.getElementById("exc-batch-count");if(!S||!h)return;const c=e.selectedIds.size;c===0?S.style.display="none":(S.style.display="",h.textContent=a("exc-batch-count",{n:c}))}function u(){const S=document.getElementById("exc-list-foot"),h=document.getElementById("exc-list-count"),c=document.getElementById("exc-loadmore");if(!S||!h||!c)return;const $=e.listCache.length;if($===0){S.style.display="none";return}S.style.display="";let P=$;const Y=e.statsCache;Y&&(e.currentRule?P=(Y.by_rule||{})[e.currentRule]||$:P=Y.pending||$),e.total=P,h.textContent=a("exc-list-count",{shown:$,total:P});const Z=$<P&&$<500;c.style.display=Z?"":"none"}async function d(){try{if(navigator.onLine===!1)throw new Error("offline");const S=e.currentClient||"",h=e.currentStatus||"pending",c=new URLSearchParams;c.set("status",h),S&&c.set("client_id",S);const $="/api/exceptions/stats?"+c.toString(),P=await fetch($,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!P.ok)throw new Error("http "+P.status);const Y=await P.json();return e.statsCache=Y,_(Y),o(Y),Y}catch(S){return console.warn("loadExceptionsStats fail",S),null}}function E(S){const h=document.getElementById("exc-list");if(!h)return;const c=`<svg class="exc-error-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="18" cy="18" r="14"/>
            <line x1="18" y1="11" x2="18" y2="19"/>
            <circle cx="18" cy="23" r="0.8" fill="currentColor"/>
        </svg>`,$=S?t("exc-offline"):t("exc-error-retry-title"),P=S?"":t("exc-error-retry-desc");h.innerHTML=`
            <div class="exc-error">
                ${c}
                <div class="exc-error-msg">${escapeHtml($)}${P?" · "+escapeHtml(P):""}</div>
                <button class="exc-retry-btn" id="exc-retry-btn" type="button">${escapeHtml(t("exc-retry-btn"))}</button>
            </div>`;const Y=document.getElementById("exc-retry-btn");Y&&Y.addEventListener("click",()=>window.loadExceptionsPage&&window.loadExceptionsPage())}async function k(S){S=S||{};const h=!!S.append,c=document.getElementById("exc-list");!h&&c&&e.listCache.length===0&&(c.innerHTML=`<div class="exc-loading">${escapeHtml(t("exc-loading"))}</div>`);const $=new URLSearchParams;$.set("status",e.currentStatus||"pending"),e.currentRule&&$.set("rule_code",e.currentRule),e.currentClient&&$.set("client_id",e.currentClient);const P=h?e.listCache.length:0;$.set("limit",String(e.pageSize)),$.set("offset",String(P));try{if(navigator.onLine===!1)throw new Error("offline");const Y=await fetch("/api/exceptions/list?"+$.toString(),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!Y.ok)throw new Error("http "+Y.status);const le=(await Y.json()).items||[];h?e.listCache=e.listCache.concat(le):(e.listCache=le,e.selectedIds.clear()),e.loadFailed=!1,v(e.listCache),e.statsCache&&o(e.statsCache)}catch(Y){console.warn("loadExceptionsList fail",Y),e.loadFailed=!0;const Z=navigator.onLine===!1||String(Y.message||"").includes("offline");h?showToast(t("exc-toast-load-fail"),"error"):(E(Z),showToast(Z?t("exc-offline"):t("exc-toast-load-fail"),"error"))}}async function q(){if(!e.loading&&!(e.listCache.length>=500)){e.loading=!0;try{await k({append:!0})}finally{e.loading=!1}}}function R(){const S=document.getElementById("exc-client-filter");if(!S)return;const h=window._clientsCache||[],c=e.currentClient||"",$=typeof t=="function"?t("history-client-all"):"全部客户";S.innerHTML=`<option value="">${escapeHtml($)}</option>`+h.map(P=>`<option value="${P.id}">${escapeHtml(P.name)}</option>`).join(""),S.value=c}window.loadExceptionsPage=async function(){if(!e.loading){e.loading=!0;try{R(),typeof window.loadErpExceptions=="function"&&window.loadErpExceptions(),await d(),await k()}finally{e.loading=!1}}},window.refreshExcBadge=n,window._refreshExcClientFilter=R,window._excState=e,window._rerenderExceptions=function(){try{R()}catch{}e.statsCache&&(_(e.statsCache),o(e.statsCache)),e.listCache&&e.listCache.length&&v(e.listCache);try{window._erpExcState&&window._erpExcState.items&&window._erpExcState.items.length&&typeof window._rerenderErpExceptions=="function"&&window._rerenderErpExceptions()}catch{}y.openExcId&&I()};let y={openExcId:null,excRow:null,history:null,loading:!1,pdfUrl:null,pdfStatus:"idle",editing:!1,editFields:null};function B(){if(y.pdfUrl){try{URL.revokeObjectURL(y.pdfUrl)}catch{}y.pdfUrl=null}y.pdfStatus="idle"}async function O(S,h){y.pdfStatus="loading",I();try{const c=await fetch("/api/history/"+encodeURIComponent(S)+"/pdf",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(y.openExcId!==h)return;if(c.status===404){y.pdfStatus="empty",I();return}if(!c.ok)throw new Error("http "+c.status);const $=await c.blob();if(y.openExcId!==h)return;B(),y.pdfUrl=URL.createObjectURL($),y.pdfStatus="ready",I()}catch(c){if(y.openExcId!==h)return;console.warn("loadDrawerPdf fail",c),y.pdfStatus="error",I()}}function D(S){const h=(e.listCache||[]).find(c=>c.id===S);if(!h){showToast(t("exc-drawer-error"),"error");return}e.listScrollY=window.scrollY||document.documentElement.scrollTop||0,B(),y.editing=!1,y.editFields=null,y.openExcId=S,y.excRow=h,y.history=null,document.getElementById("exc-drawer-mask").classList.add("show"),document.getElementById("exc-drawer").classList.add("show"),I(),A(h.history_id),O(h.history_id,S)}function F(){B(),y.editing=!1,y.editFields=null,y.openExcId=null,y.excRow=null,y.history=null,document.getElementById("exc-drawer-mask").classList.remove("show"),document.getElementById("exc-drawer").classList.remove("show");const S=e.listScrollY||0;S>0&&requestAnimationFrame(()=>window.scrollTo(0,S))}async function A(S){try{const h=await fetch("/api/history/"+encodeURIComponent(S),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!h.ok)throw new Error("http "+h.status);y.history=await h.json()}catch(h){console.warn("loadHistoryDetail fail",h),y.history={_err:!0}}y.excRow&&I()}function f(S){if(!S||!S.pages)return{};const h=S.pages,c=h.find($=>!$.is_duplicate&&!$.is_copy)||h[0];return c&&c.fields||{}}function l(S){if(S==null)return"—";const h=typeof S=="number"?S:parseFloat(String(S).replace(/,/g,""));return isNaN(h)?escapeHtml(String(S)):"฿ "+h.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function p(S,h){if(h=h||{},S==="math_mismatch")return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-subtotal"))}</b><span>${escapeHtml(l(h.subtotal))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-vat"))}</b><span>${escapeHtml(l(h.vat))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(l(h.total_expected))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-actual"))}</b><span class="v-bad">${escapeHtml(l(h.total_actual))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-diff"))}</b><span class="v-bad">${escapeHtml(l(h.diff))}</span></div>
            `;if(S==="tax_id_format_invalid")return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-seller-tax"))}</b><span class="v-bad">${escapeHtml(h.tax_id_normalized||h.tax_id_raw||"—")}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-tax-len"))}</b><span class="v-bad">${escapeHtml(String(h.actual_length||"?"))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(t("exc-detail-tax-expected"))}</span></div>
            `;if(S==="duplicate"){const c=h.level==="exact"?t("exc-detail-dup-level-exact"):t("exc-detail-dup-level-likely");return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-dup-match"))}</b><span>${escapeHtml(h.match_filename||"—")}</span></div>
                ${h.match_invoice_no?`<div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-invoice-no"))}</b><span>${escapeHtml(h.match_invoice_no)}</span></div>`:""}
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span>${escapeHtml(c)}</span></div>
            `}return S==="confidence_low"?`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-conf-label"))}</b><span class="v-bad">${escapeHtml(h.confidence||"—")}</span></div>
            `:S==="amount_missing"?`<div class="exc-why-detail-row" style="justify-content:center;color:var(--danger);"><span>${escapeHtml(t("exc-detail-missing"))}</span></div>`:`<div class="exc-why-detail-row"><span style="font-size:11px;">${escapeHtml(JSON.stringify(h))}</span></div>`}function I(){const S=y.excRow;if(!S)return;const h=S.seller_name&&S.seller_name.trim()?S.seller_name:t("exc-no-seller"),c=S.filename||"—";document.getElementById("exc-drawer-title").textContent=c;const $="exc-status-"+(S.status||"pending"),P=t($)||S.status,Y="s-"+(S.status||"pending"),Z=(S.invoice_date||S.created_at||"").slice(0,10);document.getElementById("exc-drawer-sub").innerHTML=`
            <span>${escapeHtml(h)}</span>
            ${S.invoice_no?`<span>· ${escapeHtml(S.invoice_no)}</span>`:""}
            ${Z?`<span>· ${escapeHtml(Z)}</span>`:""}
            <span class="exc-status-chip ${Y}">${escapeHtml(P)}</span>
        `;const le=S.severity||"medium",ie=t("exc-rule-"+S.rule_code)||S.rule_code,V=p(S.rule_code,S.detail||{}),Q=f(y.history),ee=y.history===null,ne=y.history&&y.history._err,oe=new Set;S.rule_code==="math_mismatch"?(oe.add("subtotal"),oe.add("vat"),oe.add("total_amount")):S.rule_code==="tax_id_format_invalid"?oe.add("seller_tax"):S.rule_code==="amount_missing"&&(oe.add("total_amount"),oe.add("invoice_number"));const ue=!!y.editing,m=y.editFields||{},C=(ae,pe,fe)=>{if(ee)return`<div class="exc-field-row"><label>${escapeHtml(t(pe))}</label><span class="val empty">…</span></div>`;const ve=ue?m[ae]!==void 0?m[ae]:Q[ae]!==void 0&&Q[ae]!==null?Q[ae]:"":Q[ae],he=oe.has(ae)?"flagged":"";if(ue){const Re=fe?"number":"text",Le=fe?' step="0.01" inputmode="decimal"':"",Ce=ve==null?"":String(ve).replace(/"/g,"&quot;");return`<div class="exc-field-row ${he} editing">
                    <label>${escapeHtml(t(pe))}</label>
                    <input class="exc-field-input" type="${Re}"${Le} data-edit-key="${escapeHtml(ae)}" value="${Ce}">
                </div>`}const ye=fe?l(ve):ve||"",xe=ve==null||ve===""?`<span class="val empty">${escapeHtml(t("exc-empty-val"))}</span>`:`<span class="val">${escapeHtml(ye)}</span>`;return`<div class="exc-field-row ${he}"><label>${escapeHtml(t(pe))}</label>${xe}</div>`};let T="";ne?T=`<div class="exc-drawer-error">${escapeHtml(t("exc-drawer-error"))}</div>`:T=`
                <div class="exc-fields">
                    ${C("invoice_number","exc-fld-invoice-no",!1)}
                    ${C("date","exc-fld-date",!1)}
                    ${C("seller_name","exc-fld-seller",!1)}
                    ${C("seller_tax","exc-fld-seller-tax",!1)}
                    ${C("buyer_name","exc-fld-buyer",!1)}
                    ${C("buyer_tax","exc-fld-buyer-tax",!1)}
                    ${C("subtotal","exc-fld-subtotal",!0)}
                    ${C("vat","exc-fld-vat",!0)}
                    ${C("total_amount","exc-fld-total",!0)}
                </div>
            `;const U=(()=>{if(y.pdfStatus==="loading"||y.pdfStatus==="idle")return`
                    <div class="exc-pdf-toolbar">
                        <span class="exc-pdf-toolbar-title">${escapeHtml(t("exc-pdf-loading"))}</span>
                    </div>
                    <div class="exc-pdf-empty">
                        <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M18 4v8a14 14 0 1014 14"/>
                        </svg>
                        <div class="exc-pdf-empty-msg">${escapeHtml(t("exc-pdf-loading"))}</div>
                    </div>
                `;if(y.pdfStatus==="empty")return`
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
                `;if(y.pdfStatus==="error")return`
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
                `;const ae=y.pdfUrl;return`
                <div class="exc-pdf-toolbar">
                    <span class="exc-pdf-toolbar-title">${escapeHtml(c)}</span>
                    <div class="exc-pdf-toolbar-actions">
                        <a class="exc-pdf-icon-btn" id="exc-pdf-open-tab" href="${ae}" target="_blank" rel="noopener" title="${escapeHtml(t("exc-pdf-open-tab"))}">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M8 2h4v4M12 2L7 7"/>
                                <path d="M11 8v3a1 1 0 01-1 1H3a1 1 0 01-1-1V4a1 1 0 011-1h3"/>
                            </svg>
                        </a>
                        <a class="exc-pdf-icon-btn" id="exc-pdf-download" href="${ae}" download="${escapeHtml(c)}" title="${escapeHtml(t("exc-pdf-download"))}">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M7 2v8M3.5 6.5L7 10l3.5-3.5M2 12h10"/>
                            </svg>
                        </a>
                    </div>
                </div>
                <iframe class="exc-pdf-frame" src="${ae}#toolbar=0&navpanes=0" title="PDF preview"></iframe>
            `})();document.getElementById("exc-drawer-body").innerHTML=`
            <div class="exc-pdf-pane">${U}</div>
            <div class="exc-fields-pane">
                <div class="exc-section">
                    <div class="exc-section-title">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="7" cy="7" r="5.5"/><line x1="7" y1="4" x2="7" y2="7.5"/>
                            <circle cx="7" cy="9.6" r="0.5" fill="currentColor"/>
                        </svg>
                        <span>${escapeHtml(t("exc-sect-why"))}</span>
                    </div>
                    <div class="exc-why sev-${escapeHtml(le)}">
                        <div class="exc-why-rule">${escapeHtml(ie)}</div>
                        <div class="exc-why-detail">${V}</div>
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
                        ${S.status==="pending"&&!ee&&!ne?ue?`
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
                    ${T}
                </div>
            </div>
        `;const N=document.getElementById("exc-fld-edit");N&&N.addEventListener("click",()=>{y.editing=!0,y.editFields={...f(y.history)},I()});const r=document.getElementById("exc-fld-cancel");r&&r.addEventListener("click",()=>{y.editing=!1,y.editFields=null,I()});const j=document.getElementById("exc-fld-save");j&&j.addEventListener("click",()=>L()),document.querySelectorAll(".exc-field-input").forEach(ae=>{ae.addEventListener("input",()=>{y.editFields||(y.editFields={}),y.editFields[ae.dataset.editKey]=ae.value})});const J=document.getElementById("exc-pdf-retry");J&&y.openExcId&&J.addEventListener("click",()=>{y.excRow&&O(y.excRow.history_id,y.openExcId)});const X=S.status==="pending",de=!!(S.seller_name&&S.seller_name.trim()),se=document.getElementById("exc-btn-resolve"),ce=document.getElementById("exc-btn-ignore");se.disabled=!X,ce.disabled=!X||!de,ce.title=de?t("exc-ignore-hint"):t("exc-ignore-no-seller")}async function L(){if(!y.openExcId||!y.history||!y.history.pages||y.loading)return;y.loading=!0;const S=showToast(t("exc-fld-saving"),"loading",0);try{const h=JSON.parse(JSON.stringify(y.history.pages||[]));let c=h.findIndex(ie=>!ie.is_duplicate&&!ie.is_copy);c<0&&(c=0),h[c]||(h[c]={fields:{}});const $=h[c].fields||{},P=y.editFields||{},Y=new Set(["subtotal","vat","total_amount"]),Z={...$};for(const ie in P){let V=P[ie];if((V===""||V===void 0)&&(V=null),Y.has(ie)&&V!==null){const Q=parseFloat(V);V=isNaN(Q)?null:Q}Z[ie]=V}h[c].fields=Z;const le=await fetch("/api/history/"+encodeURIComponent(y.history.id),{method:"PUT",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({pages:h})});if(!le.ok)throw new Error("http "+le.status);S(),showToast(t("exc-fld-save-ok"),"success"),F(),await d(),await k(),n()}catch(h){S(),console.warn("save fields fail",h),showToast(t("exc-fld-save-fail"),"error")}finally{y.loading=!1}}async function H(){if(!(!y.openExcId||y.loading)){y.loading=!0;try{const S=await fetch("/api/exceptions/"+y.openExcId+"/resolve",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!S.ok)throw new Error("http "+S.status);showToast(t("exc-toast-resolved"),"success"),F(),await d(),await k(),n()}catch(S){console.warn("resolve fail",S),showToast(t("exc-toast-action-fail"),"error")}finally{y.loading=!1}}}async function x(){if(!(!y.openExcId||y.loading)){y.loading=!0;try{const S=await fetch("/api/exceptions/"+y.openExcId+"/ignore",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!S.ok)throw new Error("http "+S.status);showToast(t("exc-toast-ignored"),"success"),F(),await d(),await k(),n()}catch(S){console.warn("ignore fail",S),showToast(t("exc-toast-action-fail"),"error")}finally{y.loading=!1}}}let M=!1;async function W(){if(M)return;const S=Array.from(e.selectedIds);if(S.length===0||!await showConfirm(a("exc-batch-confirm-resolve",{n:S.length})))return;M=!0;const c=showToast(a("exc-batch-count",{n:S.length})+" …","loading",0);try{const $=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:S,action:"resolve"})});if(!$.ok)throw new Error("http "+$.status);const P=await $.json();c(),showToast(a("exc-toast-batch-resolved",{n:P.processed||0}),"success"),e.selectedIds.clear(),await d(),await k(),n()}catch($){c(),console.warn("batch resolve fail",$),showToast(t("exc-toast-batch-fail"),"error")}finally{M=!1}}async function G(){if(M)return;const S=Array.from(e.selectedIds);if(S.length===0||!await showConfirm(a("exc-batch-confirm-ignore",{n:S.length}),{danger:!1}))return;M=!0;const c=showToast(a("exc-batch-count",{n:S.length})+" …","loading",0);try{const $=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:S,action:"ignore"})});if(!$.ok)throw new Error("http "+$.status);const P=await $.json();c(),showToast(a("exc-toast-batch-ignored",{n:P.processed||0,wl:P.whitelist_added||0}),"success"),e.selectedIds.clear(),await d(),await k(),n()}catch($){c(),console.warn("batch ignore fail",$),showToast(t("exc-toast-batch-fail"),"error")}finally{M=!1}}function K(){e.selectedIds.clear(),v(e.listCache)}document.addEventListener("click",S=>{S.target.closest("#exc-drawer-close")&&F(),S.target.closest("#exc-drawer-mask")&&F(),S.target.closest("#exc-btn-resolve")&&H(),S.target.closest("#exc-btn-ignore")&&x(),S.target.closest("#exc-batch-resolve")&&W(),S.target.closest("#exc-batch-ignore")&&G(),S.target.closest("#exc-batch-clear")&&K(),S.target.closest("#exc-loadmore")&&q()}),document.addEventListener("keydown",S=>{S.key==="Escape"&&y.openExcId&&F()}),document.addEventListener("click",S=>{S.target.closest("#btn-exc-refresh")&&(typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),n())}),document.addEventListener("change",S=>{if(!S.target.closest("#exc-client-filter"))return;const h=S.target;e.currentClient=h.value||"",e.currentRule=null,e.selectedIds.clear(),e.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),n()}),document.addEventListener("click",S=>{const h=S.target.closest("#exc-status-tabs .exc-status-tab");if(!h)return;const c=h.dataset.status||"pending";c!==e.currentStatus&&(e.currentStatus=c,e.currentRule=null,e.selectedIds.clear(),e.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage())}),window.addEventListener("online",()=>{e.loadFailed&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage&&window.loadExceptionsPage()}),setTimeout(n,1500),setInterval(n,6e4);function te(S){if(!S)return"—";try{const h=new Date(S),c=$=>String($).padStart(2,"0");return`${h.getFullYear()}-${c(h.getMonth()+1)}-${c(h.getDate())} ${c(h.getHours())}:${c(h.getMinutes())}`}catch{return S.slice(0,16).replace("T"," ")}}async function re(){const S=document.getElementById("learned-list");if(S){S.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-loading"))}</div>`;try{const h=await fetch("/api/exception-whitelist",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!h.ok)throw new Error("http "+h.status);const $=(await h.json()).items||[];if($.length===0){S.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-empty"))}</div>`;return}const P=`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 4h8M5.5 4V2.5h3V4M4 4l0.6 8.5h4.8L10 4"/>
            </svg>`;S.innerHTML=$.map(Y=>{const Z=t("exc-rule-"+Y.rule_code)||Y.rule_code;return`
                    <div class="learned-row" data-wl-id="${escapeHtml(String(Y.id))}">
                        <div class="learned-seller" title="${escapeHtml(Y.seller_name)}">${escapeHtml(Y.seller_name)}</div>
                        <div class="learned-rule">${escapeHtml(Z)}</div>
                        <div class="learned-date">${escapeHtml(te(Y.created_at))}</div>
                        <button class="learned-del-btn" data-del-wl="${escapeHtml(String(Y.id))}" title="${escapeHtml(t("set-learned-del"))}" type="button">${P}</button>
                    </div>
                `}).join("")}catch(h){console.warn("loadLearnedRules fail",h),S.innerHTML=`<div class="learned-empty">${escapeHtml(t("exc-toast-load-fail"))}</div>`}}}window.loadLearnedRules=re,document.addEventListener("click",async S=>{const h=S.target.closest("[data-del-wl]");if(!h)return;const c=parseInt(h.dataset.delWl,10);if(!c)return;const $=h.closest(".learned-row"),P=$&&$.querySelector(".learned-seller"),Y=P?P.textContent.trim():"",Z=t("set-learned-del-confirm").replace("{seller}",Y);if(await showConfirm(Z,{danger:!0}))try{const ie=await fetch("/api/exception-whitelist/"+c,{method:"DELETE",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!ie.ok)throw new Error("http "+ie.status);showToast(t("set-learned-del-ok"),"success"),re(),typeof window.loadExceptionsPage=="function"&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage()}catch(ie){console.warn("delete whitelist fail",ie),showToast(t("set-learned-del-fail"),"error")}})})();(function(){let e={items:[],q:"",cat:"",selected:new Set,total:0,categories:{},pageSize:30,loading:!1,focusSearch:!1,searchCaret:0},a=null;function n(){return localStorage.getItem("mrpilot_token")||""}function s(u){const d=typeof currentLang=="string"&&currentLang||window._currentLang||"th",E=u.error_friendly&&u.error_friendly[d];if(E)return E;if(typeof humanizeError=="function"&&u.error_msg)try{return humanizeError(u.error_msg)}catch{}return t("erp-exc-reason-"+(u.category||"other"))}function i(){const u=document.getElementById("erp-exc-batch");if(!u)return;const d=e.selected.size;u.hidden=d===0;const E=u.querySelector(".erp-exc-batch-count");E&&(E.textContent=String(d))}function g(){const u=document.getElementById("erp-exc-block");if(!u)return;const d=e;if(!(d.total>0||!!d.q||!!d.cat)){u.hidden=!0,u.innerHTML="";return}u.hidden=!1;const k=d.categories||{},q=Object.keys(k).reduce((p,I)=>p+k[I],0);let R=`<button class="erp-exc-chip ${d.cat===""?"active":""}" data-erpexc-cat=""><span>${escapeHtml(t("erp-exc-cat-all"))}</span><span class="erp-exc-chip-count">${q}</span></button>`;Object.keys(k).forEach(p=>{R+=`<button class="erp-exc-chip ${d.cat===p?"active":""}" data-erpexc-cat="${escapeHtml(p)}"><span>${escapeHtml(t("erp-exc-cat-"+p))}</span><span class="erp-exc-chip-count">${k[p]}</span></button>`});const y=d.items||[],B=y.length>0&&y.every(p=>d.selected.has(p.id)),O=y.map(p=>{const I=p.state==="needs_action"?"needs":p.state==="retrying"?"retry":"fail",L=t("erp-exc-state-"+(p.state||"failed")),H=s(p),x=d.selected.has(p.id)?"checked":"";return`<div class="erp-exc-row" data-erpexc-id="${escapeHtml(p.id)}">
                <span class="ex-cb"><input type="checkbox" class="erp-exc-cb" data-erpexc-cb="${escapeHtml(p.id)}" ${x}></span>
                <span class="ex-inv" title="${escapeHtml(p.invoice_no||"")}">${escapeHtml(p.invoice_no||"—")}</span>
                <span class="ex-seller" title="${escapeHtml(p.seller_name||"")}">${escapeHtml(p.seller_name||"—")}</span>
                <span class="ex-buyer" title="${escapeHtml(p.ocr_buyer_name||"")}">${escapeHtml(p.ocr_buyer_name||"—")}</span>
                <span class="ex-state"><span class="erp-exc-state ${I}">${escapeHtml(L)}</span></span>
                <span class="ex-reason" title="${escapeHtml(H)}">${escapeHtml(H)}${p.error_code?` <span class="erp-exc-code">${escapeHtml(p.error_code)}</span>`:""}</span>
                <span class="ex-act"><button class="erp-exc-retry-btn" type="button" data-erpexc-retry="${escapeHtml(p.id)}">${escapeHtml(t("erp-exc-retry"))}</button></span>
            </div>`}).join(""),D=y.length===0?`<div class="erp-exc-empty">${escapeHtml(t("erp-exc-empty"))}</div>`:"",F=y.length<d.total?`<button class="erp-exc-more" type="button" id="erp-exc-more">${escapeHtml(t("erp-exc-load-more"))} (${y.length}/${d.total})</button>`:d.total>0?`<div class="erp-exc-count">${escapeHtml(t("erp-exc-shown",{n:y.length,total:d.total}))}</div>`:"";u.innerHTML=`
            <div class="erp-exc-head">
                <h2 class="erp-exc-title">${escapeHtml(t("erp-exc-title"))}</h2>
                <span class="erp-exc-sub">${escapeHtml(t("erp-exc-sub"))}</span>
                <input type="search" class="erp-exc-search" id="erp-exc-search" placeholder="${escapeHtml(t("erp-exc-search-ph"))}" value="${escapeHtml(d.q)}">
            </div>
            <div class="erp-exc-chips">${R}</div>
            <div class="erp-exc-batch" id="erp-exc-batch" ${d.selected.size?"":"hidden"}>
                <span class="erp-exc-batch-info"><span class="erp-exc-batch-count">${d.selected.size}</span> ${escapeHtml(t("erp-exc-batch-selected"))}</span>
                <button class="erp-exc-batch-btn" type="button" data-erpexc-batch="retry">${escapeHtml(t("erp-exc-batch-retry"))}</button>
                <button class="erp-exc-batch-btn danger" type="button" data-erpexc-batch="delete">${escapeHtml(t("erp-exc-batch-delete"))}</button>
                <button class="erp-exc-batch-btn ghost" type="button" data-erpexc-batch="clear">${escapeHtml(t("erp-exc-batch-clear"))}</button>
            </div>
            <div class="erp-exc-rows">
                <div class="erp-exc-row erp-exc-row-head">
                    <span class="ex-cb"><input type="checkbox" class="erp-exc-cb-all" id="erp-exc-cb-all" ${B?"checked":""}></span>
                    <span class="ex-inv">${escapeHtml(t("erp-exc-f-invoice"))}</span>
                    <span class="ex-seller">${escapeHtml(t("erp-exc-f-seller"))}</span>
                    <span class="ex-buyer">${escapeHtml(t("erp-exc-f-buyer"))}</span>
                    <span class="ex-state">${escapeHtml(t("erp-exc-f-state"))}</span>
                    <span class="ex-reason">${escapeHtml(t("erp-exc-f-reason"))}</span>
                    <span class="ex-act"></span>
                </div>
                ${O}${D}
            </div>
            <div class="erp-exc-foot">${F}</div>`;const A=document.getElementById("erp-exc-search");if(A){if(d.focusSearch){A.focus();try{A.setSelectionRange(d.searchCaret,d.searchCaret)}catch{}}A.addEventListener("input",()=>{d.q=A.value,d.focusSearch=!0,d.searchCaret=A.selectionStart||A.value.length,clearTimeout(a),a=setTimeout(()=>o(!1),350)}),A.addEventListener("blur",()=>{d.focusSearch=!1})}u.querySelectorAll(".erp-exc-chip").forEach(p=>{p.addEventListener("click",()=>{d.cat=p.dataset.erpexcCat||"",o(!1)})}),u.querySelectorAll("[data-erpexc-retry]").forEach(p=>{p.addEventListener("click",I=>{I.stopPropagation(),b(p.dataset.erpexcRetry,p)})}),u.querySelectorAll(".erp-exc-cb").forEach(p=>{p.addEventListener("change",()=>{const I=p.dataset.erpexcCb;p.checked?d.selected.add(I):d.selected.delete(I);const L=document.getElementById("erp-exc-cb-all");L&&(L.checked=y.length>0&&y.every(H=>d.selected.has(H.id))),i()})});const f=document.getElementById("erp-exc-cb-all");f&&f.addEventListener("change",()=>{y.forEach(p=>{f.checked?d.selected.add(p.id):d.selected.delete(p.id)}),u.querySelectorAll(".erp-exc-cb").forEach(p=>{p.checked=f.checked}),i()}),u.querySelectorAll("[data-erpexc-batch]").forEach(p=>{p.addEventListener("click",()=>_(p.dataset.erpexcBatch))});const l=document.getElementById("erp-exc-more");l&&l.addEventListener("click",()=>o(!0)),u.querySelectorAll(".erp-exc-row:not(.erp-exc-row-head)").forEach(p=>{p.addEventListener("click",I=>{I.target.closest("input,button")||typeof window._erpExcOpenEdit=="function"&&window._erpExcOpenEdit(p.dataset.erpexcId)})})}async function b(u,d){if(u){d&&(d.disabled=!0,d.textContent=t("erp-exc-retrying"));try{const E=await fetch("/api/erp/logs/"+encodeURIComponent(u)+"/retry",{method:"POST",headers:{Authorization:"Bearer "+n()}}),k=await E.json().catch(()=>({}));showToast(E.ok&&k.ok?t("erp-exc-retry-ok"):t("erp-exc-retry-fail"),E.ok&&k.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.delete(u),o(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function _(u){const d=Array.from(e.selected);if(u==="clear"){e.selected.clear(),g();return}if(d.length!==0){if(u==="delete"){if(!await showConfirm(t("erp-exc-batch-delete-confirm",{n:d.length}),{danger:!0}))return;try{const k=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+n(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:d.slice(0,200)})}),q=await k.json().catch(()=>({}));showToast(k.ok?t("erp-exc-batch-delete-ok",{n:q.deleted||0}):t("erp-exc-retry-fail"),k.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}}else if(u==="retry")try{const E=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+n(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:d.slice(0,50)})}),k=await E.json().catch(()=>({}));showToast(E.ok?t("erp-exc-batch-retry-ok",{ok:k.succeeded||0,fail:(k.failed||0)+(k.skipped||0)}):t("erp-exc-retry-fail"),E.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.clear(),o(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function o(u){const d=document.getElementById("erp-exc-block");if(!(!d||e.loading)){e.loading=!0;try{const E=new URLSearchParams;e.q&&E.set("q",e.q),e.cat&&E.set("category",e.cat),E.set("limit",String(e.pageSize)),E.set("offset",String(u?e.items.length:0));const k=await fetch("/api/erp/exceptions?"+E.toString(),{headers:{Authorization:"Bearer "+n()}});if(!k.ok){u||(d.hidden=!0);return}const q=await k.json(),R=q.items||[];e.items=u?e.items.concat(R):R,e.total=q.total||0,e.categories=q.categories||{},g()}catch{u||(d.hidden=!0)}finally{e.loading=!1}}}let v={};function w(){const u=document.getElementById("erp-exc-modal");u&&u.remove()}window._erpExcOpenEdit=function(u){const d=(e.items||[]).find(D=>String(D.id)===String(u));if(!d)return;const E=!!d.history_client_id&&d.category==="customer_mismatch",k=d.category==="product_mismatch"&&!!d.history_id&&!!d.endpoint_id,q=s(d),R=d.state==="needs_action"?"needs":d.state==="retrying"?"retry":"fail",y=(D,F)=>`<div class="erp-exc-m-row"><span class="erp-exc-m-k">${escapeHtml(D)}</span><span class="erp-exc-m-v">${escapeHtml(F||"—")}</span></div>`;let B="";if(E)B=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-pick"))}</div>
                    <input type="search" class="erp-exc-m-search" id="erp-exc-m-search" placeholder="${escapeHtml(t("erp-exc-edit-pick-ph"))}">
                    <div class="erp-exc-m-custlist" id="erp-exc-m-custlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-pick-loading"))}</div>
                    </div>
                </div>`;else if(k)B=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-prod-intro"))}</div>
                    <div class="erp-exc-m-custlist" id="erp-exc-m-prodlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-prod-loading"))}</div>
                    </div>
                </div>`;else{const D="erp-exc-edit-hint-"+(d.category||"other");let F=t(D);(!F||F===D)&&(F=q),B=`<div class="erp-exc-m-hint">${escapeHtml(F)}</div>`}const O=document.createElement("div");if(O.id="erp-exc-modal",O.className="erp-exc-modal-overlay",O.innerHTML=`
            <div class="erp-exc-modal" role="dialog" aria-modal="true">
                <div class="erp-exc-m-head">
                    <h3>${escapeHtml(t("erp-exc-edit-title"))}</h3>
                    <button class="erp-exc-m-close" type="button" id="erp-exc-m-close" aria-label="close">×</button>
                </div>
                <div class="erp-exc-m-body">
                    <div class="erp-exc-m-reason"><span class="erp-exc-state ${R}">${escapeHtml(t("erp-exc-state-"+(d.state||"failed")))}</span> ${escapeHtml(q)}${d.error_code?` <span class="erp-exc-code">${escapeHtml(d.error_code)}</span>`:""}</div>
                    ${y(t("erp-exc-f-invoice"),d.invoice_no)}
                    ${y(t("erp-exc-f-seller"),d.seller_name)}
                    ${y(t("erp-exc-f-buyer"),d.ocr_buyer_name)}
                    ${y(t("erp-exc-edit-field-current"),d.client_name)}
                    ${B}
                </div>
                <div class="erp-exc-m-foot">
                    <button class="erp-exc-batch-btn ghost" type="button" id="erp-exc-m-cancel">${escapeHtml(t("erp-exc-edit-close"))}</button>
                    <button class="erp-exc-batch-btn" type="button" id="erp-exc-m-retry">${escapeHtml(t("erp-exc-edit-retry"))}</button>
                    ${E?`<button class="erp-exc-batch-btn" type="button" id="erp-exc-m-bind" disabled>${escapeHtml(t("erp-exc-edit-bind-retry"))}</button>`:""}
                    ${k?`<button class="erp-exc-batch-btn" type="button" id="erp-exc-m-bind-prod" disabled>${escapeHtml(t("erp-exc-edit-bind-prod-retry"))}</button>`:""}
                </div>
            </div>`,document.body.appendChild(O),O.addEventListener("click",D=>{D.target===O&&w()}),document.getElementById("erp-exc-m-close").addEventListener("click",w),document.getElementById("erp-exc-m-cancel").addEventListener("click",w),document.getElementById("erp-exc-m-retry").addEventListener("click",()=>{w(),b(d.id,null)}),E){let D="";const F=document.getElementById("erp-exc-m-bind"),A=document.getElementById("erp-exc-m-custlist"),f=document.getElementById("erp-exc-m-search"),l=(I,L)=>{const H=(L||"").trim().toLowerCase(),x=H?I.filter(M=>(M.code||"").toLowerCase().includes(H)||(M.name||"").toLowerCase().includes(H)):I;if(x.length===0){A.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-empty"))}</div>`;return}A.innerHTML=x.slice(0,100).map(M=>`<div class="erp-exc-m-cust" data-cust-code="${escapeHtml(M.code||"")}">
                        <span class="erp-exc-m-cust-name">${escapeHtml(M.name||"")}</span>
                        <span class="erp-exc-m-cust-code">${escapeHtml(M.code||"")}</span>
                    </div>`).join(""),A.querySelectorAll(".erp-exc-m-cust").forEach(M=>{M.addEventListener("click",()=>{D=M.dataset.custCode||"",A.querySelectorAll(".erp-exc-m-cust").forEach(W=>W.classList.remove("sel")),M.classList.add("sel"),F&&(F.disabled=!D)})})},p=async()=>{const I=d.endpoint_id;if(v[I]){l(v[I],"");return}try{const L=await fetch("/api/erp/endpoints/"+encodeURIComponent(I)+"/customers",{headers:{Authorization:"Bearer "+n()}}),H=await L.json().catch(()=>({}));if(!L.ok||!H.ok){A.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`;return}const x=H.customers||[];v[I]=x,l(x,"")}catch{A.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`}};f&&f.addEventListener("input",()=>l(v[d.endpoint_id]||[],f.value)),p(),F&&F.addEventListener("click",async()=>{if(D){F.disabled=!0,F.textContent=t("erp-exc-retrying");try{if(!(await fetch("/api/erp/mappings/clients",{method:"POST",headers:{Authorization:"Bearer "+n(),"Content-Type":"application/json"},body:JSON.stringify({client_id:d.history_client_id,erp_type:d.endpoint_adapter,erp_code:D})})).ok){showToast(t("erp-exc-retry-fail"),"error"),F.disabled=!1,F.textContent=t("erp-exc-edit-bind-retry");return}showToast(t("erp-exc-edit-bound-ok"),"success"),w(),await b(d.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),F.disabled=!1,F.textContent=t("erp-exc-edit-bind-retry")}}})}if(k){const D=document.getElementById("erp-exc-m-bind-prod"),F=document.getElementById("erp-exc-m-prodlist"),A={};let f=[];const l=()=>'<option value="">'+escapeHtml(t("erp-exc-edit-prod-choose"))+"</option>"+f.slice(0,500).map(L=>`<option value="${escapeHtml(L.code||"")}" data-pname="${escapeHtml(L.name||"")}">`+escapeHtml((L.name||"")+" · "+(L.code||""))+"</option>").join(""),p=L=>{if(!L.length){F.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-noitems"))}</div>`;return}F.innerHTML=L.map(H=>`<div class="erp-exc-m-cust" style="cursor:default">
                        <span class="erp-exc-m-cust-name" title="${escapeHtml(H)}">${escapeHtml(H)}</span>
                        <select class="erp-exc-m-prod-sel" data-item="${escapeHtml(H)}" style="max-width:55%;flex:0 0 auto;padding:4px 6px;border:1px solid var(--border,#e5e7eb);border-radius:6px;font-size:12px">${l()}</select>
                    </div>`).join(""),F.querySelectorAll(".erp-exc-m-prod-sel").forEach(H=>{H.addEventListener("change",()=>{const x=H.dataset.item,M=H.options[H.selectedIndex];H.value?A[x]={code:H.value,name:M&&M.dataset.pname||""}:delete A[x],D&&(D.disabled=Object.keys(A).length===0)})})};(async()=>{try{const H=await(await fetch("/api/history/"+encodeURIComponent(d.history_id),{headers:{Authorization:"Bearer "+n()}})).json().catch(()=>({})),x=H&&H.pages||[],M=[],W={};(Array.isArray(x)?x:[]).forEach(te=>{const re=te&&te.fields&&te.fields.items||[];(Array.isArray(re)?re:[]).forEach(S=>{const h=(S&&(S.name||S.description)||"").trim();h&&!W[h]&&(W[h]=1,M.push(h))})});const G=await fetch("/api/erp/endpoints/"+encodeURIComponent(d.endpoint_id)+"/products",{headers:{Authorization:"Bearer "+n()}}),K=await G.json().catch(()=>({}));if(!G.ok||!K.ok){F.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`;return}f=K.products||[],p(M)}catch{F.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`}})(),D&&D.addEventListener("click",async()=>{const L=Object.entries(A);if(L.length){D.disabled=!0,D.textContent=t("erp-exc-retrying");try{for(const[H,x]of L)if(!(await fetch("/api/erp/mappings/products",{method:"POST",headers:{Authorization:"Bearer "+n(),"Content-Type":"application/json"},body:JSON.stringify({erp_type:d.endpoint_adapter,item_name:H,erp_code:x.code,erp_name:x.name})})).ok){showToast(t("erp-exc-retry-fail"),"error"),D.disabled=!1,D.textContent=t("erp-exc-edit-bind-prod-retry");return}showToast(t("erp-exc-edit-prod-bound-ok"),"success"),w(),await b(d.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),D.disabled=!1,D.textContent=t("erp-exc-edit-bind-prod-retry")}}})}},window._rerenderErpExceptions=g,window.loadErpExceptions=o,window._erpExcState=e})();(function(){function e(u){try{if(location.search.indexOf("test_center=1")>=0||localStorage.getItem("pearnly_test_mode")==="1"||u&&u.id&&String(u.id)==="468b50c1-5593-4fd6-990d-515ce8085563")return!0}catch{}return!1}window.applyRoleVisibility=function(){var d=window._userInfo,E=!1,k=!0,q=!1,R=!1;d&&(E=typeof canManageTeam=="function"?canManageTeam(d):!!(d.role==="owner"||d.is_super_admin),k=typeof shouldHideMoney=="function"?shouldHideMoney(d):d.role==="member"&&!d.is_super_admin,q=typeof isSuperAdmin=="function"?isSuperAdmin(d):!!d.is_super_admin,R=e(d)),document.querySelectorAll("[data-show-if-team]").forEach(function(B){B.style.display=E?"":"none"}),document.querySelectorAll("[data-show-if-money]").forEach(function(B){B.style.display=k?"none":""}),document.querySelectorAll("[data-show-if-admin]").forEach(function(B){B.style.display=q?"":"none"}),document.querySelectorAll("[data-show-if-test]").forEach(function(B){B.style.display=R?"":"none"});var y=q||R;document.querySelectorAll("[data-show-if-special]").forEach(function(B){B.style.display=y?"":"none"})},window.renderAvatarMenu=function(d){if(d){var E=document.getElementById("avatar-btn"),k=document.getElementById("avatar-popup-name"),q=document.getElementById("avatar-popup-email");if(!(!E||!k||!q)){var R=(d.username||"").trim(),y=R.split("@")[0]||R||"—",B=(R.charAt(0)||"?").toUpperCase(),O=(d.avatar_url||"").trim();if(O){var D=O.replace(/"/g,"&quot;"),F=B.replace(/'/g,"\\'");E.innerHTML='<img src="'+D+'" alt="'+B+`" referrerpolicy="no-referrer" onerror="this.parentNode.textContent='`+F+`'">`}else E.textContent=B;k.textContent=y,q.textContent=R||"—",E.setAttribute("title",R||"")}}};function a(){var u=document.getElementById("avatar-wrap"),d=document.getElementById("avatar-btn"),E=document.getElementById("avatar-popup");if(!u||!d||!E)return;function k(){E.classList.remove("show"),d.setAttribute("aria-expanded","false")}function q(){E.classList.add("show"),d.setAttribute("aria-expanded","true")}d.addEventListener("click",function(R){R.stopPropagation(),E.classList.contains("show")?k():q()}),document.addEventListener("click",function(R){E.classList.contains("show")&&!u.contains(R.target)&&k()}),E.addEventListener("click",function(R){var y=R.target.closest(".avatar-popup-item");if(y){var B=y.dataset.action;switch(k(),B){case"settings":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings");break;case"team":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("team")},50);break;case"billing":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("plan")},50);break;case"shortcuts":if(typeof showToast=="function"){var O=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(O||"即将上线","info")}break;case"admin":window.location.href="/admin/cost";break;case"test-center":typeof routeTo=="function"&&routeTo("test-center");break;case"help":var D=document.getElementById("help-modal");D&&(D.style.display="flex");break;case"logout":try{localStorage.removeItem("mrpilot_token")}catch{}try{localStorage.removeItem("mrpilot_user")}catch{}window.location.href="/";break}}}),window._closeAvatarPopup=k}function n(){return[].slice.call(document.querySelectorAll(".cmdk-item")).filter(function(u){return u.style.display!=="none"})}function s(u){var d=n();d.forEach(function(E){E.classList.remove("focus")}),d[u]&&(d[u].classList.add("focus"),d[u].scrollIntoView({block:"nearest"}))}function i(u){var d=n();if(d.length){var E=d.findIndex(function(q){return q.classList.contains("focus")});E<0&&(E=0);var k=(E+u+d.length)%d.length;s(k)}}function g(u){u=(u||"").toLowerCase().trim();var d=0,E=window._userInfo,k=typeof isSuperAdmin=="function"?isSuperAdmin(E):!!(E&&E.is_super_admin),q=e(E);document.querySelectorAll(".cmdk-item").forEach(function(y){if(y.dataset.showIfAdmin==="1"&&!k){y.style.display="none";return}if(y.dataset.showIfTest==="1"&&!q){y.style.display="none";return}var B=(y.dataset.cmdkText||y.textContent||"").toLowerCase(),O=!u||B.indexOf(u)>=0;y.style.display=O?"":"none",y.classList.remove("focus"),O&&d++}),document.querySelectorAll("[data-cmdk-section]").forEach(function(y){for(var B=y.nextElementSibling,O=!1;B&&!B.hasAttribute("data-cmdk-section");){if(B.classList&&B.classList.contains("cmdk-item")&&B.style.display!=="none"){O=!0;break}B=B.nextElementSibling}y.style.display=O?"":"none"});var R=document.getElementById("cmdk-empty");R&&(R.style.display=d===0?"flex":"none"),s(0)}window.openCmdk=function(){var d=document.getElementById("cmdk-mask");d&&(typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup(),d.classList.add("show"),typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility(),setTimeout(function(){var E=document.getElementById("cmdk-input");E&&(E.value="",g(""),E.focus(),s(0))},50))},window.closeCmdk=function(){var d=document.getElementById("cmdk-mask");d&&d.classList.remove("show")};function b(u){if(u){if(u.classList.contains("cmdk-item-locked")){if(typeof showToast=="function"){var d=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(d||"即将上线","info")}return}var E=u.dataset.cmdkRoute,k=u.dataset.cmdkAction;if(window.closeCmdk(),E){typeof routeTo=="function"&&routeTo(E);return}if(k){if(k==="open-admin"){window.location.href="/admin/cost";return}if(k.indexOf("lang-")===0){var q=k.slice(5);typeof applyLang=="function"&&applyLang(q)}}}}function _(){var u=document.getElementById("cmdk-mask"),d=document.getElementById("cmdk-input"),E=document.getElementById("cmdk-body");if(!(!u||!d||!E)){u.addEventListener("click",function(R){R.target===u&&window.closeCmdk()});var k=document.getElementById("cmdk-esc-btn");k&&k.addEventListener("click",function(){window.closeCmdk()}),d.addEventListener("input",function(R){g(R.target.value)}),d.addEventListener("keydown",function(R){R.key==="ArrowDown"?(R.preventDefault(),i(1)):R.key==="ArrowUp"?(R.preventDefault(),i(-1)):R.key==="Enter"?(R.preventDefault(),b(u.querySelector(".cmdk-item.focus"))):R.key==="Escape"&&(R.preventDefault(),window.closeCmdk())}),E.addEventListener("click",function(R){var y=R.target.closest(".cmdk-item");y&&b(y)}),E.addEventListener("mousemove",function(R){var y=R.target.closest(".cmdk-item");!y||y.style.display==="none"||y.classList.contains("cmdk-item-locked")||(n().forEach(function(B){B.classList.remove("focus")}),y.classList.add("focus"))});var q=document.getElementById("topbar-search");q&&(q.addEventListener("click",function(){window.openCmdk()}),q.addEventListener("keydown",function(R){(R.key==="Enter"||R.key===" ")&&(R.preventDefault(),window.openCmdk())}))}}document.addEventListener("keydown",function(u){if((u.metaKey||u.ctrlKey)&&(u.key==="k"||u.key==="K")){u.preventDefault(),window.openCmdk();return}if(u.key==="Escape"){var d=document.getElementById("cmdk-mask");if(d&&d.classList.contains("show")){window.closeCmdk();return}var E=document.getElementById("avatar-popup");E&&E.classList.contains("show")&&typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup()}});try{var o=(navigator.userAgent||"").toLowerCase(),v=o.indexOf("mac")>=0||o.indexOf("iphone")>=0||o.indexOf("ipad")>=0;v||document.body.classList.add("is-windows")}catch{}function w(){a(),_(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("nav-ia-phase1-role",function(){try{typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",w):w()})();(function(){function a(k){return String(k??"").replace(/[&<>"']/g,function(q){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[q]})}function n(k){if(!k||isNaN(k))return"";var q=Number(k);return q<1024?q+" B":q<1024*1024?(q/1024).toFixed(1)+" KB":(q/1024/1024).toFixed(1)+" MB"}document.addEventListener("click",function(k){var q=k.target.closest&&k.target.closest(".recon-collapse-head");if(q&&!(k.target.closest("button")||k.target.closest("a"))){var R=q.closest(".recon-collapse");if(R){var y=R.getAttribute("data-collapsed")==="true";R.setAttribute("data-collapsed",y?"false":"true"),y&&(R.id==="vex-summary-collapse"&&w(),R.id==="vex-detail-collapse"&&u())}}}),document.addEventListener("keydown",function(k){if(!(k.key!=="Enter"&&k.key!==" ")){var q=k.target.closest&&k.target.closest(".recon-collapse-head");q&&(k.preventDefault(),q.click())}});var s={vat:"",gl:""};window._glvClearPreviewSearch=function(){s.vat="",s.gl=""};var i='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',g='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function b(){o("vat"),o("gl")}function _(k){try{if(typeof window._glvPreviewFiles=="function")return window._glvPreviewFiles(k)||[]}catch{}var q=document.getElementById(k==="vat"?"glv-vat-input":"glv-gl-input");return q&&q.files?Array.from(q.files):[]}function o(k){var q=document.getElementById(k==="vat"?"glv-pp-vat-col":"glv-pp-gl-col");if(q){var R=_(k),y=k==="vat"?"glv-up-vat-title":"glv-up-gl-title",B=k==="vat"?"① 销项税报告":"② 总账 GL",O=window.t&&window.t(y)||B,D=a(window.t&&window.t("vex-preview-search")||"搜索文件名..."),F=a(window.t&&window.t("vex-preview-clear-all")||"全清"),A=s[k]||"",f=R.length;q.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+a(O)+' <span class="vex-pp-col-count">'+f+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="glv-pp-search-'+k+'" type="text" placeholder="'+D+'" value="'+a(A)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="glv-pp-clearall-'+k+'" type="button">'+F+'</button></div><div class="vex-pp-file-list" id="glv-pp-'+k+'-list"></div><div class="vex-pp-pagination" id="glv-pp-'+k+'-pg"></div>';var l=document.getElementById("glv-pp-search-"+k);l&&l.addEventListener("input",function(I){s[k]=I.target.value,v(k)});var p=document.getElementById("glv-pp-clearall-"+k);p&&p.addEventListener("click",function(){window._glvRemoveFile&&window._glvRemoveFile(k)}),v(k)}}function v(k){var q=document.getElementById("glv-pp-"+k+"-list"),R=document.getElementById("glv-pp-"+k+"-pg");if(q){var y=_(k),B=(s[k]||"").toLowerCase(),O=y.map(function(A,f){return{f:A,i:f}}),D=B?O.filter(function(A){return A.f.name.toLowerCase().indexOf(B)>=0}):O;if(q.innerHTML=D.map(function(A){var f=A.f;return'<div class="vex-pp-file-row">'+i+'<span class="vex-pp-fi-name" title="'+a(f.name)+'">'+a(f.name)+'</span><span class="vex-pp-fi-size">'+n(f.size)+'</span><button class="vex-pp-fi-del" type="button" data-kind="'+k+'" data-idx="'+A.i+'" aria-label="remove">'+g+"</button></div>"}).join(""),q.querySelectorAll(".vex-pp-fi-del").forEach(function(A){A.addEventListener("click",function(){var f=A.dataset.kind,l=parseInt(A.dataset.idx,10);window._glvRemoveFile&&window._glvRemoveFile(f,isNaN(l)?null:l)})}),R){var F=window.t&&window.t("vex-preview-count")||"显示前 {n} / 共 {m}";R.textContent=F.replace("{n}",D.length).replace("{m}",D.length)}}}function w(){var k=function(R,y){var B=document.getElementById(R);B&&(B.textContent=y==null?"—":String(y))},q=window._vexLastTask||{};k("vex-sum-total",q.total),k("vex-sum-matched",q.matched),k("vex-sum-diff",q.diff),k("vex-sum-incomplete",q.incomplete),k("vex-sum-cash",q.cash),document.getElementById("vex-summary-sub")}function u(){var k=window._vexLastTask&&window._vexLastTask.diff_rows||[],q=document.getElementById("vex-detail-tbody"),R=document.getElementById("vex-detail-table"),y=document.getElementById("vex-detail-empty");if(!(!q||!R||!y)){if(k.length===0){R.style.display="none",y.style.display="";return}y.style.display="none",R.style.display="";var B=k.map(function(D){return'<tr><td class="recon-detail-cell-mono">'+a(D.invoice_no||"")+"</td><td>"+a(D.field||"")+"</td><td>"+a(D.report_value||"")+"</td><td>"+a(D.invoice_value||"")+"</td><td>"+a(D.kind||"")+"</td></tr>"}).join("");q.innerHTML=B;var O=document.getElementById("vex-detail-sub");O&&(O.textContent=String(k.length))}}function d(){var k=document.getElementById("glv-toggle-preview");k&&!k._reconBound&&(k._reconBound=!0,k.addEventListener("click",function(){var q=document.getElementById("glv-preview-panel"),R=document.getElementById("glv-toggle-preview-label"),y=q&&q.style.display!=="none";q&&(q.style.display=y?"none":""),k.classList.toggle("open",!y),R&&(R.textContent=y?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),y||b()})),["glv-vat-input","glv-gl-input"].forEach(function(q){var R=document.getElementById(q);!R||R._reconWatched||(R._reconWatched=!0,R.addEventListener("change",function(){var y=document.getElementById("glv-preview-panel");y&&y.style.display!=="none"&&b()}))})}function E(){var k=document.getElementById("vex-summary-collapse"),q=document.getElementById("vex-detail-collapse");k&&(k.style.display=""),q&&(q.style.display=""),w(),u()}window._fillVexSummary=w,window._fillVexDetail=u,window._onVexResultShown=E,document.addEventListener("DOMContentLoaded",function(){d()}),setTimeout(d,1500),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-collapse",function(){var k=document.getElementById("glv-preview-panel");k&&k.style.display!=="none"&&b();var q=document.getElementById("glv-toggle-preview-label"),R=document.getElementById("glv-toggle-preview");q&&R&&(q.textContent=R.classList.contains("open")?window.t&&window.t("vex-toggle-preview-close")||"收起清单":window.t&&window.t("vex-toggle-preview-open")||"查看清单")}),window._reconCollapse={renderGlvPreview:b,fillVexSummary:w,fillVexDetail:u}})();(function(){function e(g){}function a(){const g=document.querySelectorAll("[data-recon-tab]");g.forEach(_=>{_.addEventListener("click",()=>{g.forEach(d=>d.classList.remove("active")),_.classList.add("active");const o=_.dataset.reconTab,v=document.getElementById("recon-pane-bank"),w=document.getElementById("recon-pane-sale-vat"),u=document.getElementById("recon-pane-gl-vat");v&&(v.style.display=o==="bank"?"":"none"),w&&(w.style.display=o==="sale-vat"?"":"none"),u&&(u.style.display=o==="gl-vat"?"":"none"),o==="gl-vat"&&window.GlVatRecon&&window.GlVatRecon.ensureInit(),o==="bank"&&typeof window._bankReconV2Init=="function"&&window._bankReconV2Init()})});const b=document.querySelector("[data-recon-tab].active");b&&(b.dataset.reconTab,void 0)}function n(){const g=document.getElementById("page-settings");if(!g)return null;let b=document.getElementById("settings-modal-overlay");if(b)return b;b=document.createElement("div"),b.id="settings-modal-overlay",b.className="settings-modal-overlay",b.style.display="none",g.parentElement.insertBefore(b,g),b.appendChild(g);const _=document.createElement("button");return _.id="settings-modal-close",_.className="settings-modal-close",_.setAttribute("aria-label","close"),_.innerHTML='<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 5l10 10M15 5L5 15"/></svg>',g.insertBefore(_,g.firstChild),_.addEventListener("click",i),b.addEventListener("click",o=>{o.target===b&&i()}),b}function s(){const g=n();if(!g)return;g.style.display="flex",document.body.classList.add("settings-modal-open");const b=document.getElementById("page-settings");b&&(b.style.display="block"),setTimeout(()=>{try{typeof renderSettings=="function"&&renderSettings()}catch(o){console.warn("renderSettings:",o)}let _=document.querySelector(".settings-tab.active")||document.querySelector('.settings-tab[data-tab="profile"]');_&&_.click()},50)}function i(){const g=document.getElementById("settings-modal-overlay");g&&(g.style.display="none"),document.body.classList.remove("settings-modal-open")}window.openSettingsModal=s,window.closeSettingsModal=i,document.addEventListener("keydown",g=>{if(g.key==="Escape"){const b=document.getElementById("settings-modal-overlay");b&&b.style.display==="flex"&&i()}}),window.addEventListener("hashchange",()=>{location.hash==="#/settings"&&s()}),window.addEventListener("DOMContentLoaded",()=>{location.hash==="#/settings"&&s()}),document.readyState==="loading"?document.addEventListener("DOMContentLoaded",a):a()})();(function(){const n=/\.(pdf|jpe?g|png|webp|tiff?|xlsx?|xlsm|csv|tsv|docx?)$/i,s=V=>document.getElementById(V);function i(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}function g(V){return String(V??"").replace(/[&<>"']/g,Q=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[Q])}function b(V){return V<1024?V+" B":V<1024*1024?(V/1024).toFixed(1)+" KB":(V/1024/1024).toFixed(1)+" MB"}let _=[],o=[],v=!1,w=[],u=50,d=50,E="",k="";async function q(){try{const V=await fetch("/api/vat_excel/tasks?page=1&page_size=1",{headers:i()});if(!V.ok)return;const ee=(await V.json()).kpi||{};[["vex-kpi-month-val",ee.this_month],["vex-kpi-running-val",ee.running],["vex-kpi-done-val",ee.done],["vex-kpi-failed-val",ee.failed]].forEach(([ne,oe])=>{const ue=document.getElementById(ne);ue&&(ue.textContent=oe??0)})}catch{}}async function R(){try{const V=await fetch("/api/vat_excel/tasks?page=1&page_size=100",{headers:i()});if(!V.ok)return;const Q=await V.json();D(Q.rows||[])}catch{}}const y=10;var B=1;function O(){var V=((document.getElementById("vex-task-search")||{}).value||"").trim().toLowerCase();if(B=1,D(w),!!V){var Q=document.getElementById("vex-task-tbody");Q&&Q.querySelectorAll("tr").forEach(function(ee){ee.dataset.taskId&&(ee.style.display=ee.textContent.toLowerCase().indexOf(V)>=0?"":"none")})}}function D(V){w=V||w;const Q=document.getElementById("vex-task-tbody");if(!Q)return;if(!w.length){Q.innerHTML='<tr><td colspan="9" class="vex-task-empty">'+(t("sv-empty-title")||"还没有对账任务")+"</td></tr>",F(0);return}const ee=Math.ceil(w.length/y);B>ee&&(B=ee);const ne=(B-1)*y;A(w.slice(ne,ne+y)),F(w.length)}function F(V){const Q=document.getElementById("vex-task-pager"),ee=document.getElementById("vex-task-pager-info"),ne=document.getElementById("vex-task-prev"),oe=document.getElementById("vex-task-next");if(!Q)return;if(V<=y){Q.style.display="none";return}Q.style.display="";const ue=Math.ceil(V/y);ee&&(ee.textContent=B+" / "+ue),ne&&(ne.disabled=B<=1),oe&&(oe.disabled=B>=ue)}function A(V){const Q=document.getElementById("vex-task-tbody");if(!Q)return;const ee={pending:t("vex-status-pending")||"待处理",running:t("vex-status-running")||"处理中",done:t("vex-status-done")||"已完成",failed:t("vex-status-failed")||"失败"},ne={pending:"badge-gray",running:"badge-blue",done:"badge-green",failed:"badge-red"},oe='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',ue='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h10M6 4V3h4v1M5 4v8a1 1 0 001 1h4a1 1 0 001-1V4"/></svg>';Q.innerHTML=V.map(m=>{const C=m.created_at?new Date(m.created_at).toLocaleString([],{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}):"—",T=m.period||"—",U=m.matched_count!=null?m.matched_count+" ✓ · "+m.mismatched_count+" ⚠":"—",N=m.mismatch_amount!=null?"฿ "+Number(m.mismatch_amount).toLocaleString():"—",r=m.elapsed_seconds!=null?m.elapsed_seconds.toFixed(1)+" s":"—",j=m.status||"pending",z=m.client_name&&m.client_name!=="client"?m.client_name:t("vex-client-all")||"全部客户";return`<tr class="vex-task-row" data-task-id="${g(m.id)}" style="cursor:pointer">
                <td>${C}</td>
                <td>${g(z)}</td>
                <td>${g(T)}</td>
                <td>${(m.invoice_count||0)+" / "+(m.report_count||0)}</td>
                <td>${U}</td>
                <td>${N}</td>
                <td><span class="badge ${ne[j]||"badge-gray"}">${ee[j]||j}</span></td>
                <td>${r}</td>
                <td><div class="vex-task-actions">
                    <button class="vex-task-dl-btn" data-task-id="${g(m.id)}" title="${t("hist_export")||"导出"}">${oe}</button>
                    <button class="vex-task-del-btn" data-task-id="${g(m.id)}" title="${t("vex-task-delete-confirm-title")||"删除"}">${ue}</button>
                </div></td>
            </tr>`}).join(""),Q.querySelectorAll(".vex-task-dl-btn").forEach(m=>{m.addEventListener("click",async C=>{C.stopPropagation();const T=m.dataset.taskId;try{const U=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(T)+"/download",{credentials:"include",headers:i()});if(U.status===410){showToast(t("vex-toast-expired")||"数据已过期 · 请重新对账","warn");return}if(!U.ok){showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error");return}const N=await U.blob(),j=(U.headers.get("Content-Disposition")||"").match(/filename\*?=(?:UTF-8''|")?([^";]+)/i),z=j?decodeURIComponent(j[1]):"vat_recon_"+T+".xlsx",J=URL.createObjectURL(N),X=document.createElement("a");X.href=J,X.download=z,X.click(),setTimeout(()=>URL.revokeObjectURL(J),1e3)}catch{showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error")}})}),Q.querySelectorAll(".vex-task-del-btn").forEach(m=>{m.addEventListener("click",C=>{C.stopPropagation(),l(m.dataset.taskId)})}),O()}function f(){var V=document.getElementById("vex-task-prev"),Q=document.getElementById("vex-task-next");V&&!V._vexBound&&(V._vexBound=!0,V.addEventListener("click",function(){B>1&&(B--,D())})),Q&&!Q._vexBound&&(Q._vexBound=!0,Q.addEventListener("click",function(){var ee=Math.ceil(w.length/y);B<ee&&(B++,D())}))}async function l(V){const Q=t("vex-task-delete-confirm-title")||"删除对账任务?",ee=t("vex-task-delete-confirm-body")||"同时清掉对应的发票识别缓存 · 不可恢复";if(await showConfirm(ee,{title:Q,danger:!0,okText:t("vex-task-delete-confirm-title")||"确认删除"}))try{const oe=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(V),{method:"DELETE",credentials:"include",headers:i()});if(!oe.ok)throw new Error(oe.status);showToast(t("vex-task-delete-ok")||"已删除","success"),R(),q()}catch{showToast(t("vex-task-delete-fail")||"删除失败","error")}}function p(V){const Q=window._currentLang||"th",ee={zh:`已忽略 ${V} 个不支持的文件 · 仅支持 PDF / 图片 / Excel / CSV / Word`,th:`ข้ามไฟล์ที่ไม่รองรับ ${V} ไฟล์ · รองรับเฉพาะ PDF / รูปภาพ / Excel / CSV / Word`,en:`Ignored ${V} unsupported file(s) · only PDF / image / Excel / CSV / Word are supported`,ja:`非対応ファイル ${V} 件をスキップ · 対応形式は PDF / 画像 / Excel / CSV / Word のみ`};showToast(ee[Q]||ee.th,"warn")}function I(V){const Q=new Set(_.map(ne=>ne.name+"|"+ne.size));let ee=0;for(const ne of V){if(!n.test(ne.name)){ee++;continue}const oe=ne.name+"|"+ne.size;if(!Q.has(oe)&&(Q.add(oe),_.push(ne),_.length>=1e3))break}ee>0&&p(ee),_.length>1e3&&(_=_.slice(0,1e3),showToast(t("vex-toast-cap-inv"),"warn")),M()}function L(V){const Q=new Set(o.map(ne=>ne.name+"|"+ne.size));let ee=0;for(const ne of V){if(!n.test(ne.name)){ee++;continue}const oe=ne.name+"|"+ne.size;if(!Q.has(oe)&&(Q.add(oe),o.push(ne),o.length>=30))break}ee>0&&p(ee),o.length>30&&(o=o.slice(0,30),showToast(t("vex-toast-cap-rep"),"warn")),M()}function H(V){_.splice(V,1),M()}function x(V){o.splice(V,1),M()}function M(){const V=s("vex-list-invoice"),Q=s("vex-list-report"),ee=s("vex-count-invoice"),ne=s("vex-count-report");ee&&(ee.textContent=_.length),ne&&(ne.textContent=o.length);const oe=(C,T,U)=>`<div class="vex-fi">
            <svg class="vex-fi-ic" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2h6l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M10 2v4h4"/></svg>
            <span class="vex-fi-n" title="${g(C.name)}">${g(C.name)}</span>
            <span class="vex-fi-s">${b(C.size)}</span>
            <button class="vex-fi-x" type="button" data-vex-kind="${U}" data-vex-idx="${T}" aria-label="remove">×</button>
        </div>`;V&&(V.innerHTML=_.map((C,T)=>oe(C,T,"inv")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),Q&&(Q.innerHTML=o.map((C,T)=>oe(C,T,"rep")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),document.querySelectorAll(".vex-fi-x").forEach(C=>{C.addEventListener("click",T=>{const U=C.dataset.vexKind,N=parseInt(C.dataset.vexIdx,10);U==="inv"?H(N):x(N)})});const ue=_.length>0&&o.length>0;s("vex-build").disabled=!ue||v;const m=s("vex-action-info");m&&(!_.length||!o.length?(m.textContent=t("vex-need-both")||"需要至少 1 张发票 + 1 份 VAT 报告",m.className="vex-action-info muted"):(m.textContent=(t("vex-ready")||"已就绪 · {a} 张发票 · {b} 份报告").replace("{a}",_.length).replace("{b}",o.length),m.className="vex-action-info ok")),te()}const W='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>',G='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',K='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function te(){const V=s("vex-preview-panel");if(!V||V.style.display==="none")return;re("inv"),re("rep");const Q=s("vex-pp-guide");Q&&(Q.style.display=_.length>100?"flex":"none")}function re(V){const Q=s(V==="inv"?"vex-pp-invoice-col":"vex-pp-report-col");if(!Q)return;const ee=V==="inv"?_:o,ne=V==="inv"?E:k,oe=t(V==="inv"?"vex-preview-invoice":"vex-preview-report")||(V==="inv"?"销售发票":"VAT 报告"),ue=g(t("vex-preview-search")||"搜索文件名..."),m=g(t("vex-preview-clear-all")||"全清");Q.innerHTML=`
            <div class="vex-pp-col-title">
                <span class="vex-pp-col-name">${g(oe)} <span class="vex-pp-col-count">${ee.length}</span></span>
            </div>
            <div class="vex-pp-search-row">
                <input class="vex-pp-search" id="vex-pp-search-${V}" type="text"
                       placeholder="${ue}" value="${g(ne)}" autocomplete="off">
                <button class="vex-pp-clear-btn" id="vex-pp-clearall-${V}" type="button">${m}</button>
            </div>
            <div class="vex-pp-file-list" id="vex-pp-${V}-list"></div>
            <div class="vex-pp-pagination" id="vex-pp-${V}-pg"></div>`;const C=s("vex-pp-search-"+V);C&&C.addEventListener("input",U=>{V==="inv"?(E=U.target.value,u=50):(k=U.target.value,d=50),S(V)});const T=s("vex-pp-clearall-"+V);T&&T.addEventListener("click",()=>{V==="inv"?(_=[],E="",u=50):(o=[],k="",d=50),M()}),S(V)}function S(V){const Q=s("vex-pp-"+V+"-list"),ee=s("vex-pp-"+V+"-pg");if(!Q)return;const ne=V==="inv"?_:o,oe=V==="inv"?E:k,ue=V==="inv"?u:d,m=V==="inv"?W:G,C=ne.map((N,r)=>({f:N,i:r})),T=oe?C.filter(({f:N})=>N.name.toLowerCase().includes(oe.toLowerCase())):C,U=T.slice(0,ue);if(Q.innerHTML=U.map(({f:N,i:r})=>`
            <div class="vex-pp-file-row">
                ${m}
                <span class="vex-pp-fi-name" title="${g(N.name)}">${g(N.name)}</span>
                <span class="vex-pp-fi-size">${b(N.size)}</span>
                <button class="vex-pp-fi-del" type="button" data-kind="${V}" data-ridx="${r}" aria-label="remove">${K}</button>
            </div>`).join("")+`<div id="vex-pp-sentinel-${V}" style="height:1px;flex-shrink:0"></div>`,Q.querySelectorAll(".vex-pp-fi-del").forEach(N=>{N.addEventListener("click",()=>{const r=parseInt(N.dataset.ridx,10);N.dataset.kind==="inv"?H(r):x(r)})}),ee){const N=t("vex-preview-count")||"显示前 {n} / 共 {m}";ee.textContent=N.replace("{n}",U.length).replace("{m}",T.length)}h(V,T.length)}function h(V,Q){if((V==="inv"?u:d)>=Q)return;const ne=s("vex-pp-sentinel-"+V),oe=s("vex-pp-"+V+"-list");if(!ne||!oe)return;const ue=new IntersectionObserver(m=>{m[0].isIntersecting&&(ue.disconnect(),V==="inv"?u+=50:d+=50,S(V))},{root:oe,threshold:.8});ue.observe(ne)}function c(V,Q,ee,ne){const oe=s(V),ue=s(Q);!oe||!ue||(oe.addEventListener("click",()=>ue.click()),oe.addEventListener("keydown",m=>{(m.key==="Enter"||m.key===" ")&&(m.preventDefault(),ue.click())}),oe.addEventListener("dragover",m=>{m.preventDefault(),oe.classList.add("drag-over")}),oe.addEventListener("dragleave",()=>oe.classList.remove("drag-over")),oe.addEventListener("drop",m=>{m.preventDefault(),oe.classList.remove("drag-over");const T=Array.from(m.dataTransfer.files).filter(U=>n.test(U.name));if(!T.length){showToast(t("vex-toast-bad-ext"),"error");return}ee(T)}),ue.addEventListener("change",()=>{const m=Array.from(ue.files);ee(m),ue.value=""}))}async function $(){if(v||!_.length||!o.length)return;v=!0,s("vex-build").disabled=!0,s("vex-progress").style.display="flex";var V=document.getElementById("vex-download");V&&(V.style.display="none"),["vex-summary-collapse","vex-detail-collapse"].forEach(function(oe){var ue=document.getElementById(oe);ue&&(ue.style.display="none")});const Q=Date.now();s("vex-progress-title").textContent=t("vex-progress-running")||"AI 抽取中",s("vex-progress-sub").textContent=(t("vex-progress-sub")||"{a} 张发票 + {b} 份报告 · 并行处理").replace("{a}",_.length).replace("{b}",o.length);const ee=setInterval(()=>{const oe=Math.floor((Date.now()-Q)/1e3);s("vex-progress-sub").textContent=(t("vex-progress-elapsed")||"已 {s} 秒 · {a} 张发票 + {b} 份报告").replace("{s}",oe).replace("{a}",_.length).replace("{b}",o.length)},1e3);try{const oe=new FormData;for(const pe of _)oe.append("invoices",pe);for(const pe of o)oe.append("reports",pe);const ue=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";oe.append("lang",ue);const m=localStorage.getItem("mrpilot_token")||"",C=await fetch("/api/vat_excel/submit",{method:"POST",headers:i(),body:oe});let T=null;try{T=await C.json()}catch{T=null}if(!C.ok||!T||!T.ok||!T.job_id)throw clearInterval(ee),new Error(T&&T.detail||"HTTP "+C.status);const U=s("vex-progress-sub"),N=await window._reconPollJob(T.job_id,m,{onProgress:pe=>{U&&(U.textContent=window._reconProgressText(pe,ue))}});if(clearInterval(ee),!N||N.status!=="done"||!N.result_id)throw new Error(t("vex-toast-fail")||"生成失败");const r=N.result_id;let j=0;const z=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(r)+"/download",{headers:i()});if(!z.ok)throw new Error("HTTP "+z.status);const X=(z.headers.get("Content-Disposition")||"").match(/filename="([^"]+)"/),de=X&&X[1]||"vat_recon_"+Date.now()+".xlsx",se=await z.blob(),ce=URL.createObjectURL(se),ae=s("vex-download");ae.href=ce,ae.download=de;try{const pe=document.createElement("a");pe.href=ce,pe.download=de,document.body.appendChild(pe),pe.click(),setTimeout(()=>pe.remove(),100)}catch{}s("vex-progress").style.display="none";var ne=document.getElementById("vex-download");ne&&(ne.style.display=""),r&&(j=await Z(r)),window._onVexResultShown&&window._onVexResultShown(),j>0?showToast((t("vex-toast-some-fail")||"有 {n} 张发票 OCR 失败").replace("{n}",j),"warn"):showToast(t("vex-toast-done")||"Excel 已生成","success"),q(),setTimeout(R,800)}catch(oe){clearInterval(ee),s("vex-progress").style.display="none";const ue=(t("vex-toast-fail")||"生成失败")+": "+(oe.message||oe);showToast(ue,"error")}finally{v=!1,s("vex-build").disabled=!1}}function P(){_=[],o=[];var V=document.getElementById("vex-download");V&&(V.style.display="none"),M()}function Y(V){if(V==null)return"—";var Q=parseFloat(V);return isNaN(Q)?"—":Q.toLocaleString("th-TH",{minimumFractionDigits:2,maximumFractionDigits:2})}async function Z(V){try{var Q=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(V),{headers:i()});if(!Q.ok)throw new Error(Q.status);var ee=await Q.json(),ne=ee.raw_data_json;if(typeof ne=="string")try{ne=JSON.parse(ne)}catch{ne={}}ne=ne||{};var oe=ne.rows||[],ue=[];oe.forEach(function(T){T.kind==="invoice_orphan"?ue.push({invoice_no:T.invoice_no||"",field:"仅发票有",report_value:"—",invoice_value:Y(T.amount_inv),kind:T.kind}):T.kind==="report_orphan"?ue.push({invoice_no:T.invoice_no||"",field:"仅报告有",report_value:Y(T.amount_rep),invoice_value:"—",kind:T.kind}):T.dims&&Object.keys(T.dims).length>0&&Object.keys(T.dims).forEach(function(U){var N=String(T.dims[U]||""),r=N.split(" ≠ ");ue.push({invoice_no:T.invoice_no||"",field:U,report_value:r[0]||N,invoice_value:r.length>1?r[1]:"—",kind:"diff"})})});var m=oe.filter(function(T){return T.kind==="matched_cash"}).length,C=Math.max(0,parseInt(ne.invoice_ocr_failed_count||0,10));return window._vexLastTask={total:ne.n_total||0,matched:ne.n_ok||0,diff:ne.n_diff||0,incomplete:C,cash:m,diff_rows:ue,task_id:V},window._fillVexSummary&&window._fillVexSummary(),window._fillVexDetail&&window._fillVexDetail(),C}catch{return 0}}function le(){const V=document.getElementById("vex-pane");V&&V.querySelectorAll("[data-i18n]").forEach(Q=>{const ee=t(Q.dataset.i18n);ee&&(Q.textContent=ee)}),M(),R()}function ie(){c("vex-drop-invoice","vex-input-invoice",I),c("vex-drop-report","vex-input-report",L);const V=s("vex-build"),Q=s("vex-reset");V&&V.addEventListener("click",$),Q&&Q.addEventListener("click",P),document.querySelectorAll('[data-recon-tab="sale-vat"]').forEach(oe=>{oe.addEventListener("click",()=>{q(),R()})}),f();const ee=document.getElementById("vex-task-search");ee&&ee.addEventListener("input",O);const ne=document.getElementById("vex-toggle-preview");ne&&ne.addEventListener("click",()=>{const oe=s("vex-preview-panel"),ue=s("vex-toggle-preview-label"),m=oe&&oe.style.display!=="none";oe&&(oe.style.display=m?"none":""),ne&&ne.classList.toggle("open",!m),ue&&(ue.textContent=m?t("vex-toggle-preview-open")||"查看清单":t("vex-toggle-preview-close")||"收起清单"),m||te()}),M(),q()}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",ie):ie(),typeof window.subscribeI18n=="function"&&(window.subscribeI18n("vex-excel",le),window.subscribeI18n("vex-preview-panel",te))})();(function(){const e=h=>document.getElementById(h),a=()=>localStorage.getItem("mrpilot_token")||"",n=()=>typeof window.currentLang=="string"&&window.currentLang?window.currentLang:localStorage.getItem("mrpilot_lang")||"th",s=()=>({Authorization:"Bearer "+a()}),i={inited:!1,glFile:[],vatFile:[],running:!1,currentTaskId:null,lastDetail:[],lastSummary:null},g={th:{not_found:"ไม่พบข้อมูล",running:"กำลังกระทบยอด…",error:"เกิดข้อผิดพลาด",need_files:"กรุณาเลือกไฟล์ทั้งสอง",done:"เสร็จสิ้น",hint_need_both:"อัปโหลด ① รายงานภาษีขาย + ② GL",hint_need_one_more:"อัปโหลดอีก 1 ไฟล์",hint_ready:"พร้อมแล้ว · กดเริ่มกระทบยอด",hist_load:"โหลด",hist_export:"ส่งออก",hist_delete:"ลบ",confirm_delete:"ยืนยันการลบงานนี้?",s_gl_total:"ยอดรวมตามบัญชีแยกประเภท",s_minus_gl_cr:"หัก : รายการเครดิตที่ไม่มีในรายงานภาษีขาย",s_plus_gl_dr:"บวก : รายการเดบิตที่ไม่มีในรายงานภาษีขาย",s_plus_vat_p:"บวก : รายการยอดขายที่ไม่มีในบัญชีแยกประเภท",s_minus_vat_n:"หัก : รายการลดหนี้ที่ไม่มีในบัญชีแยกประเภท",s_vat_total:"ยอดรวมตามรายงานภาษีขาย"},zh:{not_found:"未找到数据",running:"正在对账中...",error:"出错了",need_files:"请先选择两个文件",done:"完成",hint_need_both:"请上传① 销项税报告 + ② 总账 GL",hint_need_one_more:"还需上传 1 份文件",hint_ready:"已就绪 · 点击开始对账",hist_load:"加载",hist_export:"导出",hist_delete:"删除",confirm_delete:"确认删除此任务？",s_gl_total:"总账金额合计",s_minus_gl_cr:"减：销项税报告中未列的贷方记录",s_plus_gl_dr:"加：销项税报告中未列的借方记录",s_plus_vat_p:"加：总账中未列的销售记录",s_minus_vat_n:"减：总账中未列的贷项凭单(credit note)记录",s_vat_total:"销项税报告金额合计"},en:{not_found:"Not found",running:"Reconciling...",error:"Error",need_files:"Please select both files",done:"Done",hint_need_both:"Upload ① Output VAT report + ② GL file",hint_need_one_more:"1 more file required",hint_ready:"Ready · click Run to start",hist_load:"Load",hist_export:"Export",hist_delete:"Delete",confirm_delete:"Delete this task?",s_gl_total:"Total per General Ledger",s_minus_gl_cr:"Less: GL credits not in VAT Report",s_plus_gl_dr:"Add: GL debits not in VAT Report",s_plus_vat_p:"Add: Sales in VAT Report not in GL",s_minus_vat_n:"Less: Credit notes in VAT Report not in GL",s_vat_total:"Total per VAT Sales Report"},ja:{not_found:"データなし",running:"照合中…",error:"エラー",need_files:"両方のファイルを選択してください",done:"完了",hint_need_both:"① 売上税報告 + ② GL をアップロード",hint_need_one_more:"あと 1 ファイル必要",hint_ready:"準備完了 · 「開始」をクリック",hist_load:"読込",hist_export:"出力",hist_delete:"削除",confirm_delete:"このタスクを削除しますか?",s_gl_total:"総勘定元帳合計",s_minus_gl_cr:"減：売上税報告にないGL貸方記録",s_plus_gl_dr:"加：売上税報告にないGL借方記録",s_plus_vat_p:"加：GLにない売上記録",s_minus_vat_n:"減：GLにない赤伝記録",s_vat_total:"売上税報告合計"}},b=h=>(g[n()]||g.th)[h]||h;function _(h){const c=n(),P={gl_no_revenue_rows:{zh:"GL 中未找到收入科目行。请确认「收入科目前缀」是否正确(收入科目通常以 4 开头),改对后重试。",th:"ไม่พบรายการบัญชีรายได้ใน GL · ตรวจสอบ «คำนำหน้าบัญชีรายได้» (รายได้มักขึ้นต้นด้วย 4) แล้วลองใหม่",en:"No revenue-account rows found in the GL. Check the “revenue account prefix” (revenue usually starts with 4) and retry.",ja:"GL に収益科目の行が見つかりません。「収益科目プレフィックス」(通常 4 で始まる)を確認して再試行してください。"},gl_parse_failed:{zh:"GL 文件解析失败。请确认文件含日期/科目/借贷列,或换清晰的 Excel/CSV 重传。",th:"อ่านไฟล์ GL ไม่สำเร็จ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต-เครดิต หรืออัปโหลด Excel/CSV ที่ชัดเจน",en:"Failed to parse the GL file. Ensure it has date/account/debit-credit columns, or re-upload a clean Excel/CSV.",ja:"GL ファイルの解析に失敗しました。日付/科目/借方貸方列を確認するか、Excel/CSV を再アップロードしてください。"},vat_no_rows:{zh:"销项税报告里没有可对账的数据行。请确认上传了正确的销项税报告。",th:"ไม่พบแถวข้อมูลในรายงานภาษีขาย · ตรวจสอบว่าอัปโหลดรายงานที่ถูกต้อง",en:"No rows found in the sales-VAT report. Please check you uploaded the correct report.",ja:"売上VATレポートに行が見つかりません。正しいレポートをアップロードしたか確認してください。"},vat_parse_failed:{zh:"销项税报告解析失败。请换更清晰的版本,或转成 Excel/PDF 重传。",th:"อ่านรายงานภาษีขายไม่สำเร็จ · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น Excel/PDF",en:"Failed to parse the sales-VAT report. Try a clearer version, or convert to Excel/PDF.",ja:"売上VATレポートの解析に失敗しました。より鮮明な版か、Excel/PDF に変換してください。"}}[h];return P?P[c]||P.th||P.en:b("error")||"Error"}const o=h=>h==null||isNaN(h)?"":Number(h).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});function v(h,c,$,P){const Y=e(h),Z=e(c),le=e($);if(!Y||!Z||!le)return;const ie=V=>{if(!V||!V.length)return;const Q=Array.isArray(i[P])?i[P].slice():[],ee=new Set(Q.map(ne=>ne.name+"|"+ne.size));for(const ne of V){if(!ne)continue;const oe=ne.name+"|"+ne.size;ee.has(oe)||(Q.push(ne),ee.add(oe))}i[P]=Q,w(le,Q),d(),E(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()};Y.addEventListener("click",()=>Z.click()),Y.addEventListener("keydown",V=>{(V.key==="Enter"||V.key===" ")&&(V.preventDefault(),Z.click())}),Z.addEventListener("change",()=>{ie(Array.from(Z.files||[])),Z.value=""}),Y.addEventListener("dragover",V=>{V.preventDefault(),Y.classList.add("drag-over")}),Y.addEventListener("dragleave",()=>Y.classList.remove("drag-over")),Y.addEventListener("drop",V=>{V.preventDefault(),Y.classList.remove("drag-over");const Q=V.dataTransfer&&V.dataTransfer.files?Array.from(V.dataTransfer.files):[];ie(Q)})}function w(h,c){if(!h)return;if(!c||c.length===0){h.textContent="";return}const $=c.reduce((P,Y)=>P+Math.round(Y.size/1024),0);if(c.length===1)h.textContent=c[0].name+"  ("+$+" KB)";else{const P=window.t&&window.t("glv-files-count")||"{n} 个文件";h.textContent=P.replace("{n}",c.length)+"  ("+$+" KB)"}}function u(h){const c=i[h];return Array.isArray(c)?c:c?[c]:[]}function d(){const h=e("btn-glv-run");if(!h)return;const c=u("glFile").length>0&&u("vatFile").length>0;h.disabled=!c||i.running}function E(){const h=e("glv-status");if(!h||i.running)return;const c=u("vatFile").length,$=u("glFile").length;c===0&&$===0?(h.className="vex-action-info muted",h.innerHTML="<span>"+b("hint_need_both")+"</span>"):c>0&&$>0?(h.className="vex-action-info ok",h.innerHTML="<span>"+b("hint_ready")+"</span>"):(h.className="vex-action-info muted",h.innerHTML="<span>"+b("hint_need_one_more")+"</span>")}function k(h,c){const $=h==="vat"?"vatFile":"glFile",P=h==="vat"?"glv-vat-input":"glv-gl-input",Y=h==="vat"?"glv-vat-name":"glv-gl-name",Z=u($);c==null?i[$]=[]:i[$]=Z.filter((ie,V)=>V!==c);const le=e(P);le&&(le.value=""),w(e(Y),u($)),d(),E(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}window._glvRemoveFile=k;function q(){i.glFile=[],i.vatFile=[],i.currentTaskId=null,i.lastDetail=[],i.lastSummary=null;const h=e("glv-vat-input");h&&(h.value="");const c=e("glv-gl-input");c&&(c.value="");const $=e("glv-vat-name");$&&($.textContent="");const P=e("glv-gl-name");P&&(P.textContent="");const Y=e("glv-result");Y&&(Y.style.display="none");const Z=e("glv-kpi-strip");Z&&(Z.style.display="none"),d(),E(),window._glvClearPreviewSearch&&window._glvClearPreviewSearch(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}function R(h){const c=e("glv-tbody");if(!c)return;re(h.length),c.innerHTML="";const $=b("not_found"),P=document.createDocumentFragment();h.forEach(Y=>{const Z=document.createElement("tr"),le=(ne,oe)=>{const ue=document.createElement("td");return oe&&(ue.className=oe),ue.textContent=ne,ue},ie=Y.gl_amount===null||Y.gl_amount===void 0,V=Y.diff;let Q="glv-num",ee="glv-num";ie?(ee+=" glv-cell-missing",Q+=" glv-cell-missing"):Math.abs(V||0)<.005?Q+=" glv-cell-ok":Q+=" glv-cell-diff",Z.appendChild(le(Y.doc_no||"","glv-doc")),Z.appendChild(le(Y.date||"","")),Z.appendChild(le(Y.customer_name||"","")),Z.appendChild(le(o(Y.vat_amount),"glv-num")),Z.appendChild(le(ie?$:o(Y.gl_amount),ee)),Z.appendChild(le(ie?$:o(Y.diff),Q)),Z.appendChild(le(Y.account_codes||"","glv-doc")),P.appendChild(Z)}),c.appendChild(P)}function y(h){const c=e("glv-summary-table")&&e("glv-summary-table").querySelector("tbody");if(!c)return;c.innerHTML="",[{label:b("s_gl_total"),amount:h.gl_total,emph:!0,items:[],negate:!1},{label:b("s_minus_gl_cr"),amount:-(h.gl_only_credit||0),emph:!1,items:h.gl_only_credit_items||[],negate:!0},{label:b("s_plus_gl_dr"),amount:h.gl_only_debit||0,emph:!1,items:h.gl_only_debit_items||[],negate:!1},{label:b("s_plus_vat_p"),amount:h.vat_only_positive||0,emph:!1,items:h.vat_only_positive_items||[],negate:!1},{label:b("s_minus_vat_n"),amount:h.vat_only_negative||0,emph:!1,items:h.vat_only_negative_items||[],negate:!1},{label:b("s_vat_total"),amount:h.vat_total,emph:!0,items:[],negate:!1}].forEach(({label:P,amount:Y,emph:Z,items:le,negate:ie})=>{const V=document.createElement("tr");V.className=Z?"glv-summary-total":"glv-summary-sect";const Q=document.createElement("td"),ee=document.createElement("td");Q.textContent=P,ee.textContent=Z?o(Y):"",V.appendChild(Q),V.appendChild(ee),c.appendChild(V),(le||[]).forEach(ne=>{const oe=document.createElement("tr");oe.className="glv-summary-item";const ue=document.createElement("td"),m=document.createElement("td"),C=[ne.doc_no,ne.date,ne.name].filter(Boolean);ue.textContent="· "+C.join("  ·  ");const T=ie?-(ne.amount||0):ne.amount||0;m.textContent=o(T),oe.appendChild(ue),oe.appendChild(m),c.appendChild(oe)})})}function B(h){e("glv-kpi-matched")&&(e("glv-kpi-matched").textContent=h&&h.matched!=null?h.matched:"—"),e("glv-kpi-diff")&&(e("glv-kpi-diff").textContent=h&&h.diff!=null?h.diff:"—"),e("glv-kpi-unmatched")&&(e("glv-kpi-unmatched").textContent=h&&h.unmatched!=null?h.unmatched:"—")}function O(h){if(!h)return"";try{const c=new Date(h);if(isNaN(c.getTime()))return h;const $=P=>String(P).padStart(2,"0");return c.getFullYear()+"-"+$(c.getMonth()+1)+"-"+$(c.getDate())+" "+$(c.getHours())+":"+$(c.getMinutes())}catch{return h}}const D=10;var F=[],A=1;function f(){A=1,l();var h=((e("glv-hist-search")||{}).value||"").trim().toLowerCase();if(h){var c=e("glv-history-tbody");c&&c.querySelectorAll("tr").forEach(function($){$.dataset.taskId&&($.style.display=$.textContent.toLowerCase().indexOf(h)>=0?"":"none")})}}function l(){const h=e("glv-history-table-wrap"),c=e("glv-history-empty"),$=e("glv-history-tbody"),P=e("glv-history-pager"),Y=e("glv-history-pager-info"),Z=e("glv-history-prev"),le=e("glv-history-next");if(!$)return;if($.innerHTML="",!F.length){h&&(h.style.display="none"),c&&(c.style.display=""),P&&(P.style.display="none");return}h&&(h.style.display=""),c&&(c.style.display="none");const ie=Math.ceil(F.length/D);A>ie&&(A=ie);const V=(A-1)*D,Q=F.slice(V,V+D);P&&(P.style.display=F.length>D?"":"none",Y&&(Y.textContent=A+" / "+ie),Z&&(Z.disabled=A<=1),le&&(le.disabled=A>=ie)),Q.forEach(ne=>{const oe=document.createElement("tr");oe.dataset.taskId=ne.id;const ue=document.createElement("td");ue.textContent=O(ne.created_at);const m=document.createElement("td");m.className="glv-history-file",m.title=(ne.vat_filename||"")+" + "+(ne.gl_filename||""),m.textContent=(ne.vat_filename||"?")+" + "+(ne.gl_filename||"?");const C=document.createElement("td");C.className="glv-num",C.textContent=(ne.vat_row_count||0)+" / "+(ne.gl_row_count||0);const T=document.createElement("td");T.className="glv-num",T.textContent=ne.matched_count||0;const U=document.createElement("td");U.className="glv-num",U.textContent=ne.diff_count||0;const N=document.createElement("td");N.className="glv-num",N.textContent=ne.unmatched_count||0;const r=document.createElement("td");r.className="glv-history-actions";const j=(de,se,ce,ae)=>{const pe=document.createElement("button");return pe.type="button",ce&&(pe.className=ce),pe.title=se,pe.setAttribute("aria-label",se),pe.innerHTML=de,pe.onclick=ae,pe},z='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 8a6 6 0 1 0 12 0A6 6 0 0 0 2 8z"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',J='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',X='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';r.appendChild(j(z,b("hist_load"),"",()=>L(ne.id))),r.appendChild(j(J,b("hist_export"),"",()=>H(ne.id))),r.appendChild(j(X,b("hist_delete"),"glv-del",()=>x(ne.id))),[ue,m,C,T,U,N,r].forEach(de=>oe.appendChild(de)),$.appendChild(oe)})}function p(){var h=e("glv-history-prev"),c=e("glv-history-next");h&&!h._glvBound&&(h._glvBound=!0,h.addEventListener("click",function(){A>1&&(A--,l())})),c&&!c._glvBound&&(c._glvBound=!0,c.addEventListener("click",function(){var $=Math.ceil(F.length/D);A<$&&(A++,l())}))}async function I(){try{const c=await(await fetch("/api/recon/gl-vat/tasks",{headers:s()})).json();F=c&&c.tasks||[],A=1,l(),p()}catch(h){console.error("[gl-vat] history load failed:",h)}}async function L(h){try{const $=await(await fetch("/api/recon/gl-vat/"+h,{headers:s()})).json();if(!$||!$.ok)throw new Error("load_failed");i.currentTaskId=h,i.lastDetail=$.detail||[],i.lastSummary=$.summary||{},B($.stats||{}),R(i.lastDetail),y(i.lastSummary);const P=e("glv-result");P&&(P.style.display=""),K(),window.scrollTo({top:P?P.offsetTop-80:0,behavior:"smooth"})}catch(c){console.error("[gl-vat] load task failed:",c),alert(b("error")+": "+(c.message||c))}}async function H(h){try{const c="/api/recon/gl-vat/"+h+"/export?lang="+encodeURIComponent(n()),$=await fetch(c,{headers:s()});if(!$.ok)throw new Error("HTTP "+$.status);const P=await $.blob(),Y=document.createElement("a");Y.href=URL.createObjectURL(P),Y.download="GL_VAT_recon_"+h+".xlsx",document.body.appendChild(Y),Y.click(),setTimeout(()=>{URL.revokeObjectURL(Y.href),Y.remove()},200)}catch(c){console.error("[gl-vat] exportTask failed:",c),typeof showToast=="function"&&showToast(b("error")+": "+(c.message||c),"error")}}async function x(h){let c;if(typeof window.showConfirm=="function"?c=await window.showConfirm(b("confirm_delete"),{danger:!0}):c=confirm(b("confirm_delete")),!!c)try{const $=await fetch("/api/recon/gl-vat/"+h,{method:"DELETE",headers:s()});if(!$.ok)throw new Error("HTTP "+$.status);I()}catch($){console.error("[gl-vat] delete failed:",$),typeof showToast=="function"&&showToast(b("error")+": "+($.message||$),"error")}}async function M(){if(!i.glFile||!i.vatFile){typeof showToast=="function"&&showToast(b("need_files"),"warn");return}i.running=!0,d();const h=e("glv-status"),c=e("glv-progress"),$=e("glv-progress-sub");h&&(h.className="vex-action-info muted",h.style.color="",h.innerHTML="<span>"+b("running")+"</span>"),c&&(c.style.display=""),$&&($.textContent=(i.vatFile.name||"VAT")+" + "+(i.glFile.name||"GL"));const P=new FormData,Y=u("vatFile"),Z=u("glFile");for(const ie of Y)P.append("vat_files",ie,ie.name);for(const ie of Z)P.append("gl_files",ie,ie.name);const le=(e("glv-prefix")&&e("glv-prefix").value||"4").trim()||"4";P.append("revenue_prefix",le),P.append("lang",n());try{const ie=await fetch("/api/recon/gl-vat/submit",{method:"POST",headers:s(),body:P});let V=null;try{V=await ie.json()}catch{V=null}if(!ie.ok||!V||!V.ok||!V.job_id)throw new Error(V&&V.detail||V&&V.error||"HTTP "+ie.status);const Q=e("glv-progress-sub"),ee=await window._reconPollJob(V.job_id,a(),{onProgress:m=>{Q&&(Q.textContent=window._reconProgressText(m,n()))}});if(!ee||ee.status!=="done"||!ee.result_id)throw ee&&ee.status==="failed"&&ee.error_code?new Error(_(ee.error_code)):new Error(b("error")||"Error");const ne=await fetch("/api/recon/gl-vat/"+encodeURIComponent(ee.result_id),{headers:s()});let oe=null;try{oe=await ne.json()}catch{oe=null}if(!ne.ok||!oe||!oe.ok)throw new Error(oe&&oe.detail||oe&&oe.error||"HTTP "+ne.status);i.currentTaskId=oe.task_id,i.lastDetail=oe.detail||[],i.lastSummary=oe.summary||{},B(oe.stats||{}),R(i.lastDetail),y(i.lastSummary);const ue=e("glv-result");ue&&(ue.style.display=""),K(),h&&(h.className="vex-action-info ok",h.style.color="",h.innerHTML="<span>"+b("done")+" · GL "+(oe.gl_row_count||0)+" · VAT "+(oe.vat_row_count||0)+"</span>"),I()}catch(ie){console.error("[gl-vat] run failed:",ie),h&&(h.className="vex-action-info",h.style.color="#ef4444",h.innerHTML="<span>"+b("error")+": "+(ie.message||ie)+"</span>")}finally{i.running=!1,c&&(c.style.display="none"),d()}}async function W(){if(i.currentTaskId)try{const h="/api/recon/gl-vat/"+i.currentTaskId+"/export?lang="+encodeURIComponent(n()),c=await fetch(h,{headers:s()});if(!c.ok)throw new Error("HTTP "+c.status);const $=await c.blob(),P=document.createElement("a");P.href=URL.createObjectURL($),P.download="GL_VAT_recon_"+i.currentTaskId+".xlsx",document.body.appendChild(P),P.click(),setTimeout(()=>{URL.revokeObjectURL(P.href),P.remove()},200)}catch(h){console.error("[gl-vat] export failed:",h),typeof showToast=="function"&&showToast(b("error")+": "+(h.message||h),"error")}}function G(){i.running||E(),I(),i.lastDetail&&i.lastDetail.length&&R(i.lastDetail),i.lastSummary&&y(i.lastSummary)}function K(){var h=e("glv-kpi-strip");h&&(h.style.display="");var c=e("glv-section-summary");c&&c.setAttribute("data-collapsed","false");var $=e("glv-section-detail");$&&$.setAttribute("data-collapsed","false")}function te(){document.querySelectorAll(".glv-section-head[data-toggle]").forEach(h=>{const c=h.getAttribute("data-toggle"),$=document.getElementById(c);if(!$)return;const P=Y=>{if(Y.target&&Y.target.closest("button")!==null&&!Y.target.classList.contains("glv-section-head"))return;const Z=$.getAttribute("data-collapsed")==="true";$.setAttribute("data-collapsed",Z?"false":"true")};h.addEventListener("click",P),h.addEventListener("keydown",Y=>{(Y.key==="Enter"||Y.key===" ")&&(Y.preventDefault(),P(Y))})})}function re(h){const c=e("glv-detail-count");c&&(c.textContent=h!=null?String(h):"")}function S(){if(i.inited){I();return}i.inited=!0,v("glv-drop-gl","glv-gl-input","glv-gl-name","glFile"),v("glv-drop-vat","glv-vat-input","glv-vat-name","vatFile");const h=e("btn-glv-run");h&&h.addEventListener("click",M);const c=e("btn-glv-export");c&&c.addEventListener("click",W);const $=e("btn-glv-reset");$&&$.addEventListener("click",q);const P=e("glv-hist-search");P&&P.addEventListener("input",f),te(),B(null),E(),window._loadGlvHistory=I,I(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("gl-vat-recon",G)}window.GlVatRecon={ensureInit:S},window._glvPreviewFiles=function(h){return u(h==="vat"?"vatFile":"glFile")}})();(function(){const e=["flowaccount","peak","xero","quickbooks","express"],a={flowaccount:"FlowAccount",peak:"PEAK",xero:"Xero",quickbooks:"QuickBooks",express:"Express"},n=["expense_office","expense_travel","expense_utility","asset_inventory","asset_fixed","liability_ap","revenue_sales","revenue_service","other"],s=["vat_7","vat_0","vat_exempt","wht_1","wht_3","wht_5","non_vat"],i="468b50c1-5593-4fd6-990d-515ce8085563";let g={sub:"clients",loaded:{clients:!1,accounts:!1,taxes:!1,products:!1},items:{clients:[],accounts:[],taxes:[],products:[]},clientList:[],clientLoaded:!1,addingNew:{clients:!1,accounts:!1,taxes:!1,products:!1},bound:!1};function b(){const L=typeof _userInfo<"u"?_userInfo:null;return!!(L&&(L.role==="owner"||L.is_super_admin))}function _(){const L=typeof _userInfo<"u"?_userInfo:null;return!!(L&&L.id===i)}function o(L){return typeof escapeHtml=="function"?escapeHtml(L==null?"":String(L)):String(L??"")}function v(L,H){try{typeof showToast=="function"&&showToast(L,H||"info")}catch{}}async function w(L,H){const x=localStorage.getItem("mrpilot_token");if(x&&!(g.loaded[L]&&!H))try{const M=await fetch("/api/erp/mappings/"+L,{headers:{Authorization:"Bearer "+x}});if(!M.ok)throw new Error("http_"+M.status);const W=await M.json();g.items[L]=W.items||[],g.loaded[L]=!0}catch{g.items[L]=[],g.loaded[L]=!1}}async function u(L){if(g.clientLoaded)return;const H=localStorage.getItem("mrpilot_token");if(H)try{const x=await fetch("/api/clients?include_inactive=false",{headers:{Authorization:"Bearer "+H}});if(!x.ok)throw new Error("http_"+x.status);const M=await x.json();g.clientList=(M.clients||M.items||[]).filter(W=>W.is_active!==!1),g.clientLoaded=!0}catch{g.clientList=[]}}function d(){const L=document.getElementById("erp-map-pane-wrap");if(!L)return;const H=!b();let x="";H&&(x+='<div class="erp-map-readonly-banner"><svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="8"/><path d="M10 6v4M10 13v0.01"/></svg>'+o(t("erp-map-readonly-tip"))+"</div>"),x+='<div class="erp-map-toolbar">',!H&&g.sub!=="products"&&(x+='<button class="btn btn-primary" type="button" id="erp-map-add-btn" data-i18n="erp-map-add-row">'+o(t("erp-map-add-row"))+"</button>"),x+="</div>",x+='<div class="erp-map-table" id="erp-map-table-host"></div>',L.innerHTML=x,E();const M=document.getElementById("erp-map-dev-bar");M&&(M.style.display=b()&&_()?"":"none")}function E(){const L=document.getElementById("erp-map-table-host");if(!L)return;const H=g.sub,x=g.items[H]||[],M=g.addingNew[H],W=!b();if(!x.length&&!M){L.innerHTML='<div class="erp-map-empty"><strong>'+o(t("erp-map-empty-"+H))+"</strong>"+o(t("erp-map-empty-"+H+"-sub"))+"</div>";return}let G="";G+=k(H),M&&!W&&(G+=O(H)),x.forEach(function(K){G+=D(H,K,W)}),L.innerHTML=G}function k(L){return L==="clients"?'<div class="erp-map-row erp-map-head row-clients"><div>'+o(t("erp-map-col-client"))+"</div><div>"+o(t("erp-map-col-erp"))+"</div><div>"+o(t("erp-map-col-erp-code"))+"</div><div>"+o(t("erp-map-col-notes"))+"</div><div>"+o(t("erp-map-col-actions"))+"</div></div>":L==="accounts"?'<div class="erp-map-row erp-map-head row-accounts"><div>'+o(t("erp-map-col-erp"))+"</div><div>"+o(t("erp-map-col-category"))+"</div><div>"+o(t("erp-map-col-erp-code"))+"</div><div>"+o(t("erp-map-col-erp-name"))+"</div><div>"+o(t("erp-map-col-notes"))+"</div><div>"+o(t("erp-map-col-actions"))+"</div></div>":L==="products"?'<div class="erp-map-row erp-map-head row-products"><div>'+o(t("erp-map-col-item-name"))+"</div><div>"+o(t("erp-map-col-erp-product-code"))+"</div><div>"+o(t("erp-map-col-erp-name"))+"</div><div>"+o(t("erp-map-col-notes"))+"</div><div>"+o(t("erp-map-col-actions"))+"</div></div>":'<div class="erp-map-row erp-map-head row-taxes"><div>'+o(t("erp-map-col-erp"))+"</div><div>"+o(t("erp-map-col-tax"))+"</div><div>"+o(t("erp-map-col-erp-tax-code"))+"</div><div>"+o(t("erp-map-col-notes"))+"</div><div>"+o(t("erp-map-col-actions"))+"</div></div>"}function q(L,H){let x='<select class="form-input" data-erp-field="'+H+'">';return x+='<option value="">'+o(t("erp-map-pick-erp"))+"</option>",e.forEach(function(M){const W=M===L?" selected":"";x+='<option value="'+M+'"'+W+">"+o(a[M])+"</option>"}),x+="</select>",x}function R(L){let H='<select class="form-input" data-erp-field="client_id">';return H+='<option value="">'+o(t("erp-map-pick-client"))+"</option>",(g.clientList||[]).forEach(function(x){const M=String(x.id)===String(L)?" selected":"";H+='<option value="'+x.id+'"'+M+">"+o(x.name||"#"+x.id)+"</option>"}),H+="</select>",H}function y(L){let H='<select class="form-input" data-erp-field="pearnly_category">';return H+='<option value="">'+o(t("erp-map-pick-cat"))+"</option>",n.forEach(function(x){const M=x===L?" selected":"";H+='<option value="'+x+'"'+M+">"+o(t("erp-map-cat-"+x))+"</option>"}),H+="</select>",H}function B(L){let H='<select class="form-input" data-erp-field="pearnly_tax_kind">';return H+='<option value="">'+o(t("erp-map-pick-tax"))+"</option>",s.forEach(function(x){const M=x===L?" selected":"";H+='<option value="'+x+'"'+M+">"+o(t("erp-map-tax-"+x))+"</option>"}),H+="</select>",H}function O(L){const H='<button class="btn btn-primary" type="button" data-erp-save="new" style="padding:6px 12px;height:32px;">'+o(t("erp-map-save"))+"</button>";return L==="clients"?'<div class="erp-map-row erp-map-row-add row-clients" data-erp-row="new"><div data-label="'+o(t("erp-map-col-client"))+'">'+R("")+'</div><div data-label="'+o(t("erp-map-col-erp"))+'">'+q("","erp_type")+'</div><div data-label="'+o(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+o(t("erp-map-ph-erp-code"))+'"></div><div data-label="'+o(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+o(t("erp-map-ph-notes"))+'"></div><div>'+H+"</div></div>":L==="accounts"?'<div class="erp-map-row erp-map-row-add row-accounts" data-erp-row="new"><div data-label="'+o(t("erp-map-col-erp"))+'">'+q("","erp_type")+'</div><div data-label="'+o(t("erp-map-col-category"))+'">'+y("")+'</div><div data-label="'+o(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+o(t("erp-map-ph-acc-code"))+'"></div><div data-label="'+o(t("erp-map-col-erp-name"))+'"><input type="text" class="form-input" data-erp-field="erp_name" placeholder="'+o(t("erp-map-ph-acc-name"))+'"></div><div data-label="'+o(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+o(t("erp-map-ph-notes"))+'"></div><div>'+H+"</div></div>":'<div class="erp-map-row erp-map-row-add row-taxes" data-erp-row="new"><div data-label="'+o(t("erp-map-col-erp"))+'">'+q("","erp_type")+'</div><div data-label="'+o(t("erp-map-col-tax"))+'">'+B("")+'</div><div data-label="'+o(t("erp-map-col-erp-tax-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+o(t("erp-map-ph-tax-code"))+'"></div><div data-label="'+o(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+o(t("erp-map-ph-notes"))+'"></div><div>'+H+"</div></div>"}function D(L,H,x){const M=x?"":'<button class="erp-map-del-btn" type="button" data-erp-del="'+o(H.id)+'" title="'+o(t("erp-map-delete"))+'"><svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h12M8 6V4h4v2M6 6l1 11h6l1-11"/></svg></button>',W='<span class="erp-map-erp-badge">'+o(a[H.erp_type]||H.erp_type)+"</span>";if(L==="clients")return'<div class="erp-map-row row-clients"><div data-label="'+o(t("erp-map-col-client"))+'" class="erp-map-cell-name">'+o(H.client_name||"#"+H.client_id)+'</div><div data-label="'+o(t("erp-map-col-erp"))+'">'+W+'</div><div data-label="'+o(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+o(H.erp_code||"")+'</div><div data-label="'+o(t("erp-map-col-notes"))+'">'+o(H.notes||"")+"</div><div>"+M+"</div></div>";if(L==="accounts"){const K=t("erp-map-cat-"+(H.pearnly_category||"other"))||H.pearnly_category;return'<div class="erp-map-row row-accounts"><div data-label="'+o(t("erp-map-col-erp"))+'">'+W+'</div><div data-label="'+o(t("erp-map-col-category"))+'" class="erp-map-cell-name">'+o(K)+'</div><div data-label="'+o(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+o(H.erp_code||"")+'</div><div data-label="'+o(t("erp-map-col-erp-name"))+'">'+o(H.erp_name||"")+'</div><div data-label="'+o(t("erp-map-col-notes"))+'">'+o(H.notes||"")+"</div><div>"+M+"</div></div>"}if(L==="products")return'<div class="erp-map-row row-products"><div data-label="'+o(t("erp-map-col-item-name"))+'" class="erp-map-cell-name">'+o(H.item_name||"")+'</div><div data-label="'+o(t("erp-map-col-erp-product-code"))+'" class="erp-map-code">'+o(H.erp_code||"")+'</div><div data-label="'+o(t("erp-map-col-erp-name"))+'">'+o(H.erp_name||"")+'</div><div data-label="'+o(t("erp-map-col-notes"))+'">'+o(H.notes||"")+"</div><div>"+M+"</div></div>";const G=t("erp-map-tax-"+(H.pearnly_tax_kind||""))||H.pearnly_tax_kind;return'<div class="erp-map-row row-taxes"><div data-label="'+o(t("erp-map-col-erp"))+'">'+W+'</div><div data-label="'+o(t("erp-map-col-tax"))+'" class="erp-map-cell-name"><span class="erp-map-tax-badge">'+o(G)+'</span></div><div data-label="'+o(t("erp-map-col-erp-tax-code"))+'" class="erp-map-code">'+o(H.erp_code||"")+'</div><div data-label="'+o(t("erp-map-col-notes"))+'">'+o(H.notes||"")+"</div><div>"+M+"</div></div>"}async function F(L){const H=g.sub,x={};L.querySelectorAll("[data-erp-field]").forEach(function(K){x[K.dataset.erpField]=(K.value||"").trim()});const M=localStorage.getItem("mrpilot_token");if(!M)return;let W={},G="/api/erp/mappings/"+H;if(H==="clients"){if(!x.client_id||!x.erp_type||!x.erp_code){v(t("erp-map-save-fail"),"error");return}W={client_id:parseInt(x.client_id,10),erp_type:x.erp_type,erp_code:x.erp_code,notes:x.notes||""}}else if(H==="accounts"){if(!x.erp_type||!x.pearnly_category||!x.erp_code){v(t("erp-map-save-fail"),"error");return}W={erp_type:x.erp_type,pearnly_category:x.pearnly_category,erp_code:x.erp_code,erp_name:x.erp_name||"",notes:x.notes||""}}else{if(!x.erp_type||!x.pearnly_tax_kind||!x.erp_code){v(t("erp-map-save-fail"),"error");return}W={erp_type:x.erp_type,pearnly_tax_kind:x.pearnly_tax_kind,erp_code:x.erp_code,notes:x.notes||""}}try{const K=await fetch(G,{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+M},body:JSON.stringify(W)});if(!K.ok)throw new Error("http_"+K.status);g.addingNew[H]=!1,await w(H,!0),E(),v(t("erp-map-saved-toast"),"success")}catch{v(t("erp-map-save-fail"),"error")}}async function A(L){if(!await window.pearnlyConfirm(t("erp-map-confirm-delete")))return;const x=g.sub,M=localStorage.getItem("mrpilot_token");try{const W=await fetch("/api/erp/mappings/"+x+"/"+encodeURIComponent(L),{method:"DELETE",headers:{Authorization:"Bearer "+M}});if(!W.ok)throw new Error("http_"+W.status);await w(x,!0),E(),v(t("erp-map-deleted-toast"),"success")}catch{v(t("erp-map-delete-fail"),"error")}}async function f(){await u(),await w(g.sub,!1),d()}function l(L){L!==g.sub&&(g.sub=L,g.addingNew[L]=!1,["clients","accounts","taxes","products"].forEach(function(H){H!==L&&(g.addingNew[H]=!1)}),document.querySelectorAll(".erp-map-subtab").forEach(function(H){H.classList.toggle("active",H.dataset.erpSubtab===L)}),w(L,!1).then(function(){d()}))}function p(){g.bound||(g.bound=!0,document.addEventListener("click",function(L){const H=L.target.closest(".erp-subtab[data-erp-subtab]");if(H){L.preventDefault();const K=H.dataset.erpSubtab;document.querySelectorAll(".erp-subtab").forEach(function(te){te.classList.toggle("active",te.dataset.erpSubtab===K)}),document.querySelectorAll(".erp-subpanel").forEach(function(te){te.classList.toggle("active",te.dataset.erpSubpanel===K)}),K==="mappings"&&setTimeout(f,50);return}const x=L.target.closest(".erp-map-subtab[data-erp-subtab]");if(x){L.preventDefault(),l(x.dataset.erpSubtab);return}if(L.target.closest("#erp-map-add-btn")){if(L.preventDefault(),!b())return;g.addingNew[g.sub]=!0,E();return}const W=L.target.closest('[data-erp-save="new"]');if(W){L.preventDefault();const K=W.closest('[data-erp-row="new"]');K&&F(K);return}const G=L.target.closest("[data-erp-del]");if(G){L.preventDefault(),A(G.dataset.erpDel);return}}))}function I(){const L=document.getElementById("erp-map-pane-wrap");L&&L.children.length>0&&d(),document.querySelectorAll(".erp-map-subtab").forEach(function(H){const x="erp-map-subtab-"+H.dataset.erpSubtab,M=t(x);M&&M!==x&&(H.textContent=M)})}p(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-mappings",I)})();(function(){let e=null,a=0,n=!1;function s(f){return typeof escapeHtml=="function"?escapeHtml(f==null?"":String(f)):String(f??"")}function i(f,l){try{typeof showToast=="function"&&showToast(f,l||"info")}catch{}}async function g(f){const l=Date.now();if(e&&l-a<3e4)return e;const p=localStorage.getItem("mrpilot_token");if(!p)return[];try{const I=await fetch("/api/erp/connectors/status",{headers:{Authorization:"Bearer "+p}});if(!I.ok)return[];const L=await I.json();return e=L&&L.connectors||[],a=l,e}catch{return[]}}function b(){try{return localStorage.getItem("pn_push_default_connector")||""}catch{return""}}function _(f){try{localStorage.setItem("pn_push_default_connector",f||"")}catch{}}function o(f){if(!f||!f.length)return null;const l=b();if(l){const I=f.find(L=>L.id===l);if(I)return I}const p=f.find(I=>I.is_default);return p||f[0]}function v(f){if(!f)return!1;const l=String(f.status||"").toLowerCase();return l==="exception"||l==="exception_pending"||l==="rejected"}function w(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function u(f){const l=f&&(f.type||f.id);return l==="xero"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5.5 8l2 2 3-3.5"/></svg>':l==="webhook"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="11.5" r="1.8"/><circle cx="11" cy="4.5" r="1.8"/><path d="M6.4 10l3.2-4M5 9.6V5.5a3 3 0 016 0"/></svg>':'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/><rect x="11" y="3" width="3" height="10" rx="1"/></svg>'}async function d(f,l){if(!f||!l)return!1;const p=document.getElementById("btn-push-default");p&&(p.disabled=!0,p.classList.add("loading"));const I=localStorage.getItem("mrpilot_token");try{let L,H={method:"POST",headers:{Authorization:"Bearer "+I}};f.type==="xero"?L="/api/erp/xero/push/"+encodeURIComponent(l):(L="/api/erp/push",H.headers["Content-Type"]="application/json",H.body=JSON.stringify({history_id:l,endpoint_id:f.endpoint_id||void 0}));const x=await fetch(L,H);let M={};try{M=await x.json()}catch{}if(!x.ok){let W=M&&M.detail||"unknown";typeof W=="object"&&(W=W.code||JSON.stringify(W));let G=String(W||"unknown");if(f.type==="xero"){const K=G.replace(/^xero\./,"").toLowerCase(),te=t("xero-"+K);te&&te!=="xero-"+K&&(G=te)}return i(t("unified-push-fail").replace("{name}",f.name).replace("{err}",G),"error"),!1}if(M&&M.ok===!1){let W=M.error_msg||M.error_code||"unknown";return W=String(W).slice(0,200),i(t("unified-push-fail").replace("{name}",f.name).replace("{err}",W),"error"),!1}return i(t("unified-push-ok").replace("{name}",f.name),"success"),!0}catch(L){return i(t("unified-push-fail").replace("{name}",f.name).replace("{err}",L.message||"network"),"error"),!1}finally{p&&(p.disabled=!1,p.classList.remove("loading"))}}async function E(f,l){for(const p of f)await d(p,l)}function k(f,l){const p=document.createElement("div");p.className="pn-push-dropdown",p.id="pn-push-dropdown";const I=(f||[]).map(H=>{const x=!!(l&&H.id===l.id),M=H.method==="download"?t("unified-push-tag-download"):x?t("unified-push-tag-default"):"";return'<div class="pn-pd-item" data-cid="'+s(H.id)+'"><span class="pn-pd-icon">'+u(H)+'</span><span class="pn-pd-name">'+s(H.name)+"</span>"+(M?'<span class="pn-pd-tag">'+s(M)+"</span>":"")+(x?'<span class="pn-pd-check">✓</span>':"")+"</div>"}).join(""),L=f&&f.length>1?'<div class="pn-pd-divider"></div><div class="pn-pd-item pn-pd-all" data-cid="__all__"><span class="pn-pd-icon"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h10M3 10h10M3 13.5h6"/></svg></span><span class="pn-pd-name">'+s(t("unified-push-all").replace("{n}",f.length))+"</span></div>":"";return p.innerHTML=I+L,p}function q(){const f=document.getElementById("pn-push-dropdown");f&&f.remove()}async function R(){if(document.getElementById("pn-push-dropdown")){q();return}const f=await g()||[],l=o(f),p=k(f,l),I=document.getElementById("pn-push-wrap");I&&I.appendChild(p)}async function y(){const f=await g()||[],l=o(f);if(!l)return;const p=w(),I=p&&(p._historyId||p.history_id);if(I){if(v(p)){i(t("unified-push-disabled-exc"),"warn");return}await d(l,I)}}async function B(f){q();const l=await g()||[],p=w(),I=p&&(p._historyId||p.history_id);if(!I)return;if(v(p)){i(t("unified-push-disabled-exc"),"warn");return}if(f==="__all__"){await E(l,I);return}const L=l.find(H=>H.id===f);L&&(_(f),await d(L,I),D())}async function O(){const f=document.getElementById("drawer-history-save");if(!f||f.querySelector("#pn-push-wrap"))return;const l=document.createElement("div");l.id="pn-push-wrap",l.className="pn-push-wrap",l.dataset.loading="1",f.insertBefore(l,f.firstChild),["btn-push-erp","btn-xero-push"].forEach(M=>{f.querySelectorAll("#"+M).forEach(W=>{W.style.display="none"})});const p=await g()||[],I=o(p),L=p.length>0;if(!L)l.innerHTML='<button type="button" class="btn btn-ghost pn-push-empty" id="btn-push-default" disabled title="'+s(t("unified-push-empty-tip"))+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/></svg><span style="margin-left:4px;">'+s(t("unified-push-empty"))+"</span></button>";else{const M=p.length>1;l.innerHTML='<div class="pn-push-split"><button type="button" class="pn-push-main" id="btn-push-default" title="'+s(t("unified-push-tip"))+'">'+u(I)+"<span>"+s(t("unified-push-to").replace("{name}",I?I.name:""))+"</span></button>"+(M?'<button type="button" class="pn-push-arrow" id="btn-push-arrow" title="'+s(t("unified-push-other"))+'"><svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5l3 3 3-3"/></svg></button>':"")+"</div>"}delete l.dataset.loading;const H=l.querySelector("#btn-push-default");H&&L&&H.addEventListener("click",y);const x=l.querySelector("#btn-push-arrow");x&&x.addEventListener("click",function(M){M.stopPropagation(),R()}),n||(n=!0,document.addEventListener("click",function(M){const W=M.target.closest(".pn-pd-item");if(W){const G=W.getAttribute("data-cid");B(G);return}M.target.closest("#btn-push-arrow")||q()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("unified-push",D))}function D(){const f=document.getElementById("pn-push-wrap");f&&(f.remove(),e=null,a=0,O())}function F(){const f=document.getElementById("drawer-history-save");if(!f||!f.querySelector("#pn-push-wrap"))return;["btn-push-erp","btn-xero-push"].forEach(p=>{f.querySelectorAll("#"+p).forEach(I=>{I.style.display!=="none"&&(I.style.display="none")})});const l=f.querySelectorAll("#pn-push-wrap");if(l.length>1)for(let p=1;p<l.length;p++)l[p].remove()}function A(){try{const f=function(){return document.getElementById("drawer-body")},l=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&O(),F()}),p=f();if(p)l.observe(p,{childList:!0,subtree:!0});else{const I=new MutationObserver(function(){const L=f();L&&(l.observe(L,{childList:!0,subtree:!0}),I.disconnect())});I.observe(document.body,{childList:!0,subtree:!0})}setTimeout(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&O(),F()},200)}catch{}}A()})();(function(){function e(){const n=document.getElementById("erp-map-show-advanced-btn");if(!n)return;const s=document.getElementById("erp-map-subtabs");if(!s)return;const i=s.classList.contains("show-advanced"),g=n.querySelector(".erp-map-adv-btn-label");if(g&&typeof t=="function"){const b=i?"erp-map-hide-advanced":"erp-map-show-advanced",_=t(b);_&&_!==b&&(g.textContent=_)}n.setAttribute("aria-pressed",i?"true":"false")}document.addEventListener("click",function(n){if(!n.target.closest("#erp-map-show-advanced-btn"))return;n.preventDefault();const i=document.getElementById("erp-map-subtabs");if(i&&(i.classList.toggle("show-advanced"),e(),!i.classList.contains("show-advanced")&&i.querySelector(".erp-map-subtab.active.erp-map-subtab-advanced"))){const b=i.querySelector('.erp-map-subtab[data-erp-subtab="clients"]');b&&b.click()}});function a(){e()}typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-map-advanced-toggle",a)})();(function(){const e="pearnly_erp_onboard_shown";let a=!1;function n(){try{return Array.isArray(window._erpEndpoints)&&window._erpEndpoints.length>0}catch{return!1}}function s(){if(document.getElementById("erp-onboard-mask"))return;const g=document.createElement("div");g.id="erp-onboard-mask",g.className="erp-onboard-mask",g.innerHTML='<div class="erp-onboard-modal" role="dialog" aria-modal="true"><div class="erp-onboard-icon"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="6" width="24" height="20" rx="3"/><path d="M9 13h14M9 18h10"/><path d="M22 22l3 3 5-5"/></svg></div><div class="erp-onboard-title" id="erp-onboard-title"></div><div class="erp-onboard-body" id="erp-onboard-body"></div><div class="erp-onboard-btns"><button type="button" class="btn btn-secondary" id="erp-onboard-later"></button><button type="button" class="btn btn-primary" id="erp-onboard-ok"></button></div></div>',document.body.appendChild(g);function b(){const o=document.getElementById("erp-onboard-title"),v=document.getElementById("erp-onboard-body"),w=document.getElementById("erp-onboard-ok"),u=document.getElementById("erp-onboard-later");o&&(o.textContent=t("erp-onboard-title")),v&&(v.textContent=t("erp-onboard-body")),w&&(w.textContent=t("erp-onboard-ok")),u&&(u.textContent=t("erp-onboard-later"))}b();function _(){g.style.display="none"}document.getElementById("erp-onboard-ok").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}_();try{const o=document.querySelector('#btn-add-endpoint, [data-action="erp-add-endpoint"]');o&&o.scrollIntoView({behavior:"smooth",block:"center"})}catch{}}),document.getElementById("erp-onboard-later").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}_()}),g.addEventListener("click",function(o){o.target===g&&_()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-onboard-modal",function(){g.style.display!=="none"&&b()})}function i(){if(!a){try{if(localStorage.getItem(e)==="1")return}catch{}n()||(a=!0,s(),requestAnimationFrame(function(){requestAnimationFrame(function(){if(n())return;const g=document.getElementById("erp-onboard-mask");g&&(g.style.display="flex")})}))}}document.addEventListener("click",function(g){const b=g.target.closest('.auto-nav-item[data-auto-tab="erp"]'),_=g.target.closest('.erp-subtab[data-erp-subtab="connect"]');(b||_)&&setTimeout(i,700)})})();(function(){const e={parse:{zh:"解析文件中",th:"กำลังอ่านไฟล์",en:"Parsing files",ja:"ファイル解析中"},report:{zh:"读取报告中",th:"กำลังอ่านรายงาน",en:"Reading report",ja:"レポート読込中"},reconcile:{zh:"对账中",th:"กำลังกระทบยอด",en:"Reconciling",ja:"照合中"},build:{zh:"生成中",th:"กำลังสร้างไฟล์",en:"Building",ja:"作成中"},persist:{zh:"保存中",th:"กำลังบันทึก",en:"Saving",ja:"保存中"},done:{zh:"完成",th:"เสร็จสิ้น",en:"Done",ja:"完了"}};window._reconProgressText=function(a,n){a=a||{},n=window._currentLang||n||localStorage.getItem("mrpilot_lang")||"th",e.parse[n]||(n="th");const s=a.stage||"parse",i=e[s]||e.parse,g=i[n]||i.th||i.en,b=a.stage_total,_=a.stage_done;if(s==="parse"&&Number.isFinite(b)&&b>0){const o={zh:"共 {d}/{t} 个文件",th:"{d}/{t} ไฟล์",en:"{d}/{t} files",ja:"{d}/{t} ファイル"}[n]||"{d}/{t} files";return g+" · "+o.replace("{d}",_||0).replace("{t}",b)}return g},window._reconPollJob=async function(a,n,s){s=s||{};const i=s.intervalMs||1500,g=s.maxMs||1200*1e3,b=Date.now();let _=0;for(;;){let o=null;try{const v=await fetch("/api/recon/jobs/"+encodeURIComponent(a),{headers:{Authorization:"Bearer "+n}});try{o=await v.json()}catch{o=null}(!v.ok||!o||!o.ok)&&(o=null)}catch{o=null}if(o){if(_=0,s.onProgress)try{s.onProgress(o.progress||{},o)}catch{}if(o.status==="done"||o.status==="failed"||o.status==="needs_review"||o.status==="needs_mapping")return o}else if(++_>=10)return{ok:!1,status:"failed",error_code:"poll_unreachable"};if(Date.now()-b>g)return{ok:!1,status:"timeout",error_code:"timeout"};await new Promise(v=>setTimeout(v,i))}}})();(function(){let e=!1,a=[],n=[],s=null,i="all",g=[],b={stmt:"",gl:""},_=[];const o=m=>document.getElementById(m);function v(m){if(m==null)return"—";const C=Number(m);return isNaN(C)?"—":C.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function w(m){return m?String(m).slice(0,10).split("-").reverse().join("/"):"—"}function u(m){return String(m||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function d(m,C){C=window._currentLang||C||"th";const T={stmt_headers_not_found:{zh:"认不出银行账单表头 · 请确认文件含日期/金额/余额列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตารางบัญชีธนาคารไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/จำนวนเงิน/ยอดคงเหลือ หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect bank statement headers · ensure the file has date/amount/balance columns, or re-upload as a clean Excel/CSV",ja:"銀行明細のヘッダーを認識できません · 日付/金額/残高列を確認するか、Excel/CSVに変換して再アップロードしてください"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含日期/科目/借方/贷方列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตาราง GL ไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต/เครดิต หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect GL headers · ensure the file has date/account/debit/credit columns, or re-upload as a clean Excel/CSV",ja:"GLのヘッダーを認識できません · 日付/科目/借方/貸方列を確認するか、Excel/CSVに変換して再アップロードしてください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水,或换更清晰的版本重传",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง หรือใช้เวอร์ชันที่ชัดเจนกว่า",en:"No transaction rows found · please upload the correct statement, or try a clearer version",ja:"取引データが見つかりません · 正しい明細をアップロードするか、より鮮明なファイルでお試しください"},no_rows:{zh:"解析后没有可对账的数据行 · 请确认文件内容完整,或换清晰版本重传",th:"ไม่มีแถวข้อมูลให้กระทบยอดหลังการอ่าน · ตรวจสอบความสมบูรณ์ของไฟล์ หรืออัปโหลดใหม่",en:"No reconcilable rows after parsing · check the file is complete, or re-upload a clearer version",ja:"解析後に照合可能な行がありません · ファイルの完全性を確認するか再アップロードしてください"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密 · 请换文件或转 PDF/Excel 重传",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส · ลองไฟล์อื่นหรือแปลงเป็น PDF/Excel",en:"File cannot be read · may be corrupted or encrypted · try another file or convert to PDF/Excel",ja:"ファイルを読み取れません · 破損または暗号化の可能性 · 別ファイルまたはPDF/Excelに変換してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロードしてください"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本,或转成 PDF / Excel / CSV 重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น PDF / Excel / CSV",en:"Could not read the file · try a clearer version, or convert to PDF / Excel / CSV",ja:"読み取りに失敗 · より鮮明なファイルか、PDF / Excel / CSV に変換して再試行してください"}},U={zh:"解析失败 · 请换更清晰的文件,或转成 Excel / CSV 后重新上传",th:"อ่านไฟล์ไม่สำเร็จ · ลองไฟล์ที่ชัดเจนกว่า หรือแปลงเป็น Excel / CSV แล้วอัปโหลดใหม่",en:"Parsing failed · try a clearer file, or convert to Excel / CSV and re-upload",ja:"解析に失敗しました · より鮮明なファイルか、Excel / CSV に変換して再アップロードしてください"},N=T[m]||U;return N[C]||N.th||N.en}function E(m){const C=m==="stmt"?a:n,T=o(`brv2-${m}-name`);if(T)if(C.length===0)T.textContent="";else{const N=window._currentLang||"zh",r={zh:"个文件",th:" ไฟล์",en:" file(s)",ja:" ファイル"};T.textContent=C.length+(r[N]||" 个文件")}const U=o("brv2-preview-panel");U&&U.style.display!=="none"&&R(m),k()}function k(){const m=o("brv2-toggle-preview"),C=o("brv2-preview-panel"),T=a.length+n.length>0;m&&(m.style.display=T?"":"none"),!T&&C&&(C.style.display="none",m&&m.classList.remove("open"))}function q(){R("stmt"),R("gl")}function R(m){const C=o(m==="stmt"?"brv2-pp-stmt-col":"brv2-pp-gl-col");if(!C)return;const T=m==="stmt"?a:n,U=window._currentLang||"zh",N={stmt:{zh:"① 银行账单",th:"① บัญชีธนาคาร",en:"① Bank Stmt",ja:"① 銀行明細"},gl:{zh:"② 总账 GL",th:"② GL รายงาน",en:"② GL Report",ja:"② GL帳簿"}},r=(N[m]||{})[U]||N[m].zh,j=u(window.t&&window.t("vex-preview-search")||"搜索文件名..."),z=u(window.t&&window.t("vex-preview-clear-all")||"全清"),J=b[m]||"";C.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+u(r)+' <span class="vex-pp-col-count">'+T.length+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="brv2-pp-search-'+m+'" type="text" placeholder="'+j+'" value="'+u(J)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="brv2-pp-clearall-'+m+'" type="button">'+z+'</button></div><div class="vex-pp-file-list" id="brv2-pp-'+m+'-list"></div><div class="vex-pp-pagination" id="brv2-pp-'+m+'-pg"></div>';const X=o("brv2-pp-search-"+m);X&&X.addEventListener("input",function(se){b[m]=se.target.value,y(m)});const de=o("brv2-pp-clearall-"+m);de&&de.addEventListener("click",function(){m==="stmt"?a.length=0:n.length=0,E(m),M()}),y(m)}function y(m){const C=o("brv2-pp-"+m+"-list"),T=o("brv2-pp-"+m+"-pg");if(!C)return;const U=m==="stmt"?a:n,N=(b[m]||"").toLowerCase(),r=N?U.filter(J=>J.name.toLowerCase().includes(N)):U.slice(),j='<svg class="vex-pp-fi-ico" viewBox="0 0 14 16" fill="none" stroke="currentColor" stroke-width="1.4" width="12" height="14"><path d="M3 1h6l3 3v11H3V1z"/><path d="M9 1v3h3"/></svg>',z='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" width="11" height="11"><path d="M2 4h10M5 4V2h4v2M5.5 7v4M8.5 7v4M3 4l1 8h6l1-8"/></svg>';if(C.innerHTML=r.map((J,X)=>'<div class="vex-pp-file-row">'+j+'<span class="vex-pp-fi-name" title="'+u(J.name)+'">'+u(J.name)+'</span><span class="vex-pp-fi-size">'+B(J.size)+'</span><button class="vex-pp-fi-del" type="button" data-zone="'+m+'" data-idx="'+U.indexOf(J)+'" aria-label="remove">'+z+"</button></div>").join(""),C.querySelectorAll(".vex-pp-fi-del").forEach(function(J){J.addEventListener("click",function(){const X=parseInt(J.dataset.idx,10);J.dataset.zone==="stmt"?a.splice(X,1):n.splice(X,1),E(J.dataset.zone),M()})}),T){const J=window.t&&window.t("vex-preview-count")||"显示 {n} / 共 {m}";T.textContent=J.replace("{n}",r.length).replace("{m}",U.length)}}function B(m){return m?m<1024?m+" B":m<1048576?(m/1024).toFixed(1)+" KB":(m/1048576).toFixed(1)+" MB":""}var O="pearnly.brv2.lastAnchorOcr";function D(m){try{var C=m&&m._anchor_ocr;if(!C||typeof C!="object")return;var T={stmt_opening:Number.isFinite(+C.stmt_opening)?+C.stmt_opening:null,gl_opening:Number.isFinite(+C.gl_opening)?+C.gl_opening:null,gl_closing:Number.isFinite(+C.gl_closing)?+C.gl_closing:null,stmt_closing:Number.isFinite(+C.stmt_closing)?+C.stmt_closing:null,ts:Date.now()};localStorage.setItem(O,JSON.stringify(T))}catch{}}function F(){try{var m=localStorage.getItem(O);if(!m)return null;var C=JSON.parse(m);return!C||typeof C!="object"?null:C}catch{return null}}function A(){var m=F();if(m){var C={"brv2-anchor-stmt-opening":m.stmt_opening,"brv2-anchor-gl-opening":m.gl_opening,"brv2-anchor-gl-closing":m.gl_closing,"brv2-anchor-stmt-closing":m.stmt_closing},T=0;Object.keys(C).forEach(function(z){var J=document.getElementById(z);if(J&&J.value===""){var X=C[z];if(Number.isFinite(X)){J.value=X.toFixed(2);var de=J.closest&&J.closest(".brv2-anchor-cell");de&&de.classList.add("is-prefilled"),T+=1}}});var U=document.getElementById("brv2-anchor-eq"),N=document.getElementById("brv2-anchor-eq-val");if(U&&N&&Number.isFinite(m.stmt_opening)&&Number.isFinite(m.gl_opening)){var r=m.stmt_opening-m.gl_opening;N.textContent=r.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),U.style.display=""}if(T>0){var j=document.getElementById("brv2-anchor-prefill-banner");j&&j.classList.add("show")}}}function f(){var m=document.getElementById("brv2-anchor-prefill-banner");if(m){var C=!1;["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"].forEach(function(T){var U=document.getElementById(T);if(U){var N=U.closest&&U.closest(".brv2-anchor-cell");N&&N.classList.contains("is-prefilled")&&(C=!0)}}),m.classList.toggle("show",C)}}var l=[["stmt_opening","brv2-anchor-stmt-opening"],["gl_opening","brv2-anchor-gl-opening"],["gl_closing","brv2-anchor-gl-closing"],["stmt_closing","brv2-anchor-stmt-closing"]];function p(m,C){return window.t&&window.t(m)||C}function I(m){return String(m??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function L(m){return Number.isFinite(+m)?(+m).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—"}function H(m){var C=document.getElementById("brv2-summary-collapse");if(!(!C||!C.parentNode)){var T=document.getElementById("brv2-anchor-audit"),U=m&&m._anchor_overrides;if(!U||typeof U!="object"||Object.keys(U).length===0){T&&T.parentNode&&T.parentNode.removeChild(T);return}T||(T=document.createElement("div"),T.id="brv2-anchor-audit",T.style.cssText="margin-top:14px;background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:14px 16px;",C.parentNode.insertBefore(T,C.nextSibling));var N=l.map(function(r){var j=U[r[0]];if(!j)return"";var z=+j.ocr||0,J=+j.user||0,X=J-z,de=X>0?"+":(X<0,""),se=Math.abs(X)<.005?"#6b7280":X>0?"#16a34a":"#dc2626";return'<tr><td style="padding:6px 10px;color:#111827;font-size:13px">'+I(p(r[1],r[0]))+'</td><td style="padding:6px 10px;color:#6b7280;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+I(L(z))+'</td><td style="padding:6px 10px;background:#fef08a;color:#92400e;font-weight:600;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+I(L(J))+'</td><td style="padding:6px 10px;color:'+se+';font-weight:500;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+I(de+L(X))+"</td></tr>"}).join("");T.innerHTML='<div style="font-weight:600;color:#92400e;font-size:13px;margin-bottom:10px">'+I(p("brv2-anchor-audit-title","⚠ This run contains manually entered anchors"))+'</div><table style="width:100%;border-collapse:collapse;font-family:inherit"><thead><tr><th style="padding:6px 10px;text-align:left;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+I(p("brv2-anchor-audit-col-field","Field"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+I(p("brv2-anchor-audit-col-ocr","OCR"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+I(p("brv2-anchor-audit-col-user","User"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+I(p("brv2-anchor-audit-col-diff","Diff"))+"</th></tr></thead><tbody>"+N+"</tbody></table>"}}function x(){const m=o("brv2-toggle-preview");m&&!m._reconBound&&(m._reconBound=!0,m.addEventListener("click",function(){const C=o("brv2-preview-panel"),T=o("brv2-toggle-preview-label"),U=C&&C.style.display!=="none";C&&(C.style.display=U?"none":""),m.classList.toggle("open",!U),T&&(T.textContent=U?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),U||q()}))}function M(){const m=o("brv2-run-btn"),C=o("brv2-status"),T=a.length>0,U=n.length>0;if(m&&(m.disabled=!(T&&U)),C){const N=window._currentLang||"zh";if(!T&&!U){const r={zh:"请上传银行账单和 GL 文件",th:"กรุณาอัปโหลดบัญชีธนาคารและ GL",en:"Upload bank statement and GL files",ja:"銀行明細と GL を両方アップロードしてください"};C.textContent=r[N]||r.zh}else if(T)if(U){const r={zh:"两份文件已就绪",th:"พร้อมสอบทาน",en:"Ready to reconcile",ja:"照合を開始できます"};C.textContent=r[N]||r.zh}else{const r={zh:"还缺 GL 文件",th:"ยังขาดไฟล์ GL",en:"Missing GL file",ja:"GL ファイルが未アップロード"};C.textContent=r[N]||r.zh}else{const r={zh:"还缺银行账单 PDF",th:"ยังขาดไฟล์บัญชีธนาคาร PDF",en:"Missing bank statement PDF",ja:"銀行明細 PDF が未アップロード"};C.textContent=r[N]||r.zh}}}function W(m,C,T){const U=o(m),N=o(C);!U||!N||(U.addEventListener("click",()=>N.click()),U.addEventListener("keydown",r=>{(r.key==="Enter"||r.key===" ")&&(r.preventDefault(),N.click())}),U.addEventListener("dragover",r=>{r.preventDefault(),U.classList.add("drag-over")}),U.addEventListener("dragleave",()=>U.classList.remove("drag-over")),U.addEventListener("drop",r=>{r.preventDefault(),U.classList.remove("drag-over");const j=Array.from(r.dataTransfer.files||[]);T==="stmt"?a.push(...j):n.push(...j),E(T),M()}),N.addEventListener("change",()=>{const r=Array.from(N.files||[]);T==="stmt"?a.push(...r):n.push(...r),N.value="",E(T),M()}))}function G(m){const C=o("brv2-progress"),T=o("brv2-run-btn"),U=o("brv2-error");C&&(C.style.display=m?"":"none"),T&&(T.disabled=m),U&&(U.style.display="none")}function K(m){const C=o("brv2-error");C&&(C.textContent=m,C.style.display="",C.scrollIntoView({behavior:"smooth",block:"nearest"})),G(!1),M(),window.showToast&&window.showToast(m,"error")}async function te(){if(a.length===0||n.length===0)return;const m=localStorage.getItem("mrpilot_token")||"",C=window._currentLang||"zh",T=(o("brv2-acct-select")||{}).value||"";S(!1),G(!0);try{const U=new FormData;a.forEach(ae=>U.append("stmt_files",ae)),n.forEach(ae=>U.append("gl_files",ae)),U.append("gl_account",T),U.append("lang",C);const N=parseFloat((o("brv2-anchor-gl-closing")||{}).value),r=parseFloat((o("brv2-anchor-stmt-closing")||{}).value),j=parseFloat((o("brv2-anchor-stmt-opening")||{}).value),z=parseFloat((o("brv2-anchor-gl-opening")||{}).value);Number.isFinite(N)&&U.append("gl_closing_override",N),Number.isFinite(r)&&U.append("stmt_closing_override",r),Number.isFinite(j)&&U.append("stmt_opening_override",j),Number.isFinite(z)&&U.append("gl_opening_override",z);const J=await fetch("/api/recon/bank-v2/submit",{method:"POST",headers:{Authorization:"Bearer "+m},body:U});let X=null;try{X=await J.json()}catch{X=null}if(X&&X.needs_mapping){G(!1),window.ReconMapping?window.ReconMapping.show(X,{token:m,lang:C,onConfirmed:function(){te()}}):K(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(!J.ok||!X||!X.ok||!X.job_id){G(!1),X&&(X.detail||X.error)?K(_humanizeBackendError(X.detail||X.error,"Error "+J.status)):K(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const de=o("brv2-progress-sub"),se=await window._reconPollJob(X.job_id,m,{onProgress:ae=>{de&&(de.textContent=window._reconProgressText(ae,C))}});if(se&&se.status==="needs_mapping"&&se.mapping){G(!1),window.ReconMapping?window.ReconMapping.show(se.mapping,{token:m,lang:C,onConfirmed:function(){te()}}):K(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(se&&se.status==="needs_review"&&se.review){G(!1),window.ReconReview?window.ReconReview.show(se.review,{token:m,lang:C,jobId:X.job_id,onConfirmed:async function(ae){G(!0);const pe=await window._reconPollJob(ae,m,{onProgress:fe=>{de&&(de.textContent=window._reconProgressText(fe,C))}});await ce(pe)}}):K(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(se&&se.status==="failed"){G(!1),K(d(se.error_code,C));return}await ce(se);async function ce(ae){try{if(!ae||ae.status!=="done"||!ae.result_id){G(!1),K(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const pe=await fetch("/api/recon/bank-v2/"+encodeURIComponent(ae.result_id),{headers:{Authorization:"Bearer "+m}});let fe=null;try{fe=await pe.json()}catch{fe=null}if(!pe.ok||fe===null||!fe.ok){G(!1),K(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}(fe.gl_accounts||[]).length>1&&re(fe.gl_accounts),s=fe,g=fe.detail||[],i="all",document.querySelectorAll(".brv2-filter-btn").forEach(he=>he.classList.toggle("active",he.dataset.filter==="all")),D(fe&&fe.summary),G(!1),P(fe),Z();const ve=o("brv2-summary-collapse");ve&&ve.scrollIntoView({behavior:"smooth",block:"nearest"})}catch(pe){G(!1),K(pe.message||"Network error")}}}catch(U){K(U.message||"Network error")}}function re(m){const C=o("brv2-acct-select");if(!C)return;const T=window._currentLang||"zh",U={zh:"全部账户",th:"ทุกบัญชี",en:"All Accounts",ja:"すべての口座"}[T]||"全部账户";C.innerHTML=`<option value="">${U}</option>`+m.map(N=>`<option value="${u(N)}">${u(N)}</option>`).join(""),C.style.display=""}function S(m){const C=o("brv2-summary-collapse"),T=o("brv2-detail-collapse"),U=o("brv2-export-btn"),N=o("brv2-new-btn"),r=o("brv2-parse-info-wrap");C&&(C.style.display=m?"":"none"),T&&(T.style.display=m?"":"none"),U&&(U.style.display=m?"":"none"),N&&(N.style.display=m?"":"none"),!m&&r&&(r.style.display="none");const j=o("brv2-warnings");!m&&j&&(j.style.display="none",j.innerHTML="")}function h(m){const C=o("brv2-parse-info-wrap"),T=o("brv2-parse-info-body");if(!C||!T)return;const U=m.parse_info;if(!U){C.style.display="none";return}const N=window._currentLang||"zh",r={title:{zh:"文件解析状态",th:"สถานะการอ่านไฟล์",en:"File Parse Status",ja:"ファイル解析状態"},type:{zh:"类型",th:"ประเภท",en:"Type",ja:"種別"},file:{zh:"文件名",th:"ชื่อไฟล์",en:"File",ja:"ファイル"},rows:{zh:"解析行数",th:"แถวที่พบ",en:"Rows Found",ja:"解析行数"},bank:{zh:"银行/科目",th:"ธนาคาร/บัญชี",en:"Bank/Account",ja:"銀行/科目"},status:{zh:"状态",th:"สถานะ",en:"Status",ja:"状態"},stmt:{zh:"账单",th:"บัญชีธนาคาร",en:"Stmt",ja:"明細"},gl:{zh:"总账GL",th:"GL",en:"GL",ja:"GL"},ok:{zh:"✓ 成功",th:"✓ สำเร็จ",en:"✓ OK",ja:"✓ 成功"},warn:{zh:"⚠ 0行",th:"⚠ 0 แถว",en:"⚠ 0 rows",ja:"⚠ 0行"},fail:{zh:"✗ 失败",th:"✗ ล้มเหลว",en:"✗ Failed",ja:"✗ 失敗"}},j=ce=>(r[ce]||{})[N]||(r[ce]||{}).zh||ce,z=[...(U.stmt_files||[]).map(ce=>({...ce,_type:"stmt",_extra:ce.bank_code||""})),...(U.gl_files||[]).map(ce=>({...ce,_type:"gl",_extra:(ce.accounts||[]).join(", ")}))],J={stmt_headers_not_found:{zh:"认不出表头列 · 请确认文件含日期/金额/余额列",th:"หาคอลัมน์หัวตารางไม่เจอ · ตรวจสอบไฟล์มีวันที่/จำนวนเงิน/ยอดคงเหลือ",en:"Cannot detect column headers · ensure file has date/amount/balance columns",ja:"列ヘッダーが認識できません · 日付/金額/残高列を確認してください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง",en:"No transaction rows found · please check the file",ja:"取引データが見つかりません · ファイルを確認してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロード"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส",en:"File cannot be read · may be corrupted or encrypted",ja:"ファイルを読み取れません · 破損または暗号化の可能性"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本或换 PDF 格式重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่าหรือเปลี่ยนเป็น PDF",en:"Could not read file · try a clearer version or upload as PDF",ja:"読み取り失敗 · より鮮明なファイルまたは PDF 形式で再試行"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含科目/借方/贷方列",th:"หาหัวคอลัมน์ GL ไม่เจอ · ตรวจสอบมีคอลัมน์บัญชี/เดบิต/เครดิต",en:"Cannot detect GL column headers · ensure account/debit/credit columns exist",ja:"GL 列ヘッダー認識不可 · 科目/借方/貸方列を確認してください"}},X=ce=>{const ae=String(ce||"");return/Cannot detect bank statement column headers/i.test(ae)?"stmt_headers_not_found":/Cannot detect GL column headers/i.test(ae)?"gl_headers_not_found":/No transaction rows found|no pages parsed/i.test(ae)?"stmt_no_rows":/unsupported format/i.test(ae)?"file_not_supported":/Cannot read Excel|file_unreadable/i.test(ae)?"file_unreadable":/Gemini.*invalid JSON|Gemini.*parsed but failed|validation errors|BankStatementDocument schema|layer2:|layer1:/i.test(ae)?"ocr_failed":null},de=ce=>{const ae=ce.error_code||X(ce.error);if(ae&&J[ae]){const pe=window._currentLang||"zh";return J[ae][pe]||J[ae].zh}return String(ce.error||"").slice(0,80)},se=ce=>!ce.ok&&ce.error?`<span style="color:#dc2626">${j("fail")} — ${u(de(ce))}</span>`:ce.rows?`<span style="color:#059669">${j("ok")} (${ce.rows})</span>`:`<span style="color:#d97706">${j("warn")}</span>`;T.innerHTML=`
            <div style="font-size:12px;font-weight:600;margin-bottom:6px;color:var(--ink-2)">${j("title")}</div>
            <table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:4px">
                <thead>
                    <tr style="background:#f3f4f6;font-weight:600">
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${j("type")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb">${j("file")}</th>
                        <th style="padding:6px 8px;text-align:center;border:1px solid #e5e7eb;white-space:nowrap">${j("rows")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${j("bank")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${j("status")}</th>
                    </tr>
                </thead>
                <tbody>
                    ${z.map(ce=>`<tr>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;white-space:nowrap">${ce._type==="stmt"?j("stmt"):j("gl")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${u(ce.file||"")}">${u(ce.file||"")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;text-align:center">${ce.rows||0}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;color:var(--ink-2)">${u(ce._extra||"")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb">${se(ce)}</td>
                    </tr>`).join("")}
                </tbody>
            </table>`,C.style.display=""}async function c(m){const C=localStorage.getItem("mrpilot_token")||"",T=window._currentLang||"zh";try{const U=await fetch("/api/recon/bank-v2/"+m+"/export?lang="+T,{headers:{Authorization:"Bearer "+C}});if(!U.ok){const de=await U.json().catch(()=>({}));window.showToast&&window.showToast(de.detail||"Export failed","error");return}const N=await U.blob(),j=(U.headers.get("content-disposition")||"").match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/),z=j?j[1].replace(/['"]/g,""):"reconciliation.xlsx",J=URL.createObjectURL(N),X=document.createElement("a");X.href=J,X.download=z,document.body.appendChild(X),X.click(),document.body.removeChild(X),URL.revokeObjectURL(J)}catch(U){window.showToast&&window.showToast("Export error: "+U.message,"error")}}function $(m,C){const T=o("brv2-summary-collapse");let U=o("brv2-warnings");const N=window._currentLang||"zh",r={zh:"⏭ 已跳过无法识别的文件:",th:"⏭ ข้ามไฟล์ที่อ่านไม่ได้:",en:"⏭ Skipped unreadable file:",ja:"⏭ 読み取れないファイルをスキップ:"}[N]||"⏭ ",j=[];if((C||[]).forEach(z=>j.push(r+" "+z)),(m||[]).forEach(z=>j.push(z)),!j.length){U&&(U.style.display="none");return}if(!U)if(U=document.createElement("div"),U.id="brv2-warnings",T&&T.parentNode)T.parentNode.insertBefore(U,T);else return;U.style.cssText="display:block;margin:10px 0;padding:10px 14px;background:#FEF3C7;border:1px solid #FCD34D;border-radius:8px;color:#92400E;font-size:13px;line-height:1.6",U.innerHTML=j.map(z=>"<div>"+u(z)+"</div>").join("")}function P(m){h(m),$(m.warnings||[],m.skipped_files||[]),!m.ok&&m.error&&window.showToast&&window.showToast(m.error,"error");const C=m.stats||{},T=m.summary||{},U=C.matched||0,N=(C.gl_debit_only||0)+(C.gl_credit_only||0),r=(C.stmt_withdrawal_only||0)+(C.stmt_deposit_only||0),j=Number(T.formula_diff||0),z=Math.abs(j)<.05;o("brv2-kpi-matched")&&(o("brv2-kpi-matched").textContent=U),o("brv2-kpi-diff")&&(o("brv2-kpi-diff").textContent=v(j)),o("brv2-kpi-unmatched")&&(o("brv2-kpi-unmatched").textContent=N+r);const J=o("brv2-kpi-diff-icon");J&&(J.style.background=z?"#d1fae5":"#fee2e2",J.style.color=z?"#065f46":"#b91c1c");const X=o("brv2-formula-sub");if(X){const pe=window._currentLang||"zh";X.textContent=z?{zh:"✓ 平衡",th:"✓ สมดุล",en:"✓ Balanced",ja:"✓ 一致"}[pe]||"✓ 平衡":({zh:"差 ",th:"ต่าง ",en:"Diff ",ja:"差 "}[pe]||"差 ")+v(j)}const de=o("brv2-detail-sub");if(de){const pe=window._currentLang||"zh",fe={zh:"共 {n} 行",th:"ทั้งหมด {n} แถว",en:"{n} rows",ja:"計 {n} 行"}[pe]||"共 {n} 行";de.textContent=fe.replace("{n}",g.length)}function se(pe,fe,ve){const he=o(pe);he&&(he.textContent=(ve&&fe>0?"(":"")+v(ve?-fe:fe)+(ve&&fe>0?")":""))}se("brf-gl-close",T.gl_closing||0),se("brf-open-diff",T.opening_diff||0),se("brf-gl-debit-only",T.gl_debit_only_amount||0,!0),se("brf-gl-credit-only",T.gl_credit_only_amount||0),se("brf-stmt-wd-only",T.stmt_withdrawal_only_amount||0,!0),se("brf-stmt-dep-only",T.stmt_deposit_only_amount||0),se("brf-calc-close",T.formula_stmt_closing||0),se("brf-stmt-close",T.stmt_closing||0),o("brf-diff")&&(o("brf-diff").textContent=v(j));const ce=o("brv2-fcell-diff");ce&&ce.classList.toggle("brv2-fcell-diff-ok",z);const ae=o("brv2-export-btn");ae&&(ae.onclick=()=>{s&&c(s.task_id)}),H(T),S(!0),Y()}function Y(){const m=o("brv2-tbody");if(!m)return;const C=g.filter(r=>i==="all"?!0:i==="matched"?r.match_status==="matched":i==="gl_only"?r.match_status.startsWith("gl_"):i==="stmt_only"?r.match_status.startsWith("stmt_"):!0);if(C.length===0){const r={zh:"无记录",th:"ไม่มีรายการ",en:"No rows",ja:"行なし"}[window._currentLang||"zh"]||"无记录";m.innerHTML=`<tr><td colspan="10" style="text-align:center;padding:20px;color:var(--ink-3)">${r}</td></tr>`;return}const T=window._currentLang||"zh",U={zh:"OCR 余额验证未通过 · 上一行余额 ± 金额 ≠ 本行余额，请核对原 PDF",th:"การตรวจสอบยอดคงเหลือไม่ผ่าน · ยอดก่อนหน้า ± จำนวน ≠ ยอดบรรทัดนี้ โปรดตรวจสอบ PDF ต้นฉบับ",en:"Balance check FAILED · prev_balance ± amount ≠ this row balance — verify against the original PDF",ja:"残高検証エラー · 前残高 ± 金額 ≠ この行残高 — 元のPDFと照合してください"}[T],N={zh:"OCR 低置信度 · 数字模糊或难以辨认，请核对原 PDF",th:"OCR ความมั่นใจต่ำ · ตัวเลขเบลอหรืออ่านยาก โปรดตรวจสอบ PDF ต้นฉบับ",en:"OCR low confidence · digit was blurry or hard to read — verify against the original PDF",ja:"OCR信頼度低 · 数字がぼやけている — 元のPDFと照合してください"}[T];m.innerHTML=C.map(r=>{const j=r.match_status,z=r.match_layer;let J="",X="";j==="matched"?(z===1&&(J="matched",X='<span class="brv2-status-badge brv2-badge-matched">L1 ✓</span>'),z===2&&(J="matched-l2",X='<span class="brv2-status-badge brv2-badge-matched-l2">L2 ~</span>'),z===3&&(J="matched-l3",X='<span class="brv2-status-badge brv2-badge-matched-l3">L3 ?</span>')):j==="gl_debit_only"||j==="gl_credit_only"?(J="gl-only",X='<span class="brv2-status-badge brv2-badge-gl-only">GL</span>'):(J="stmt-only",X=`<span class="brv2-status-badge brv2-badge-stmt-only">${{zh:"账单",th:"บัญชี",en:"Stmt",ja:"明細"}[T]||"账单"}</span>`);let de="";return r.stmt_balance_ok===!1&&(de+=`<span class="brv2-ocr-warn brv2-ocr-warn-bal" title="${u(U)}">⚠</span>`,J+=" brv2-row-warn"),r.stmt_confidence==="low"&&(de+=`<span class="brv2-ocr-warn brv2-ocr-warn-conf" title="${u(N)}">◌</span>`,J.includes("brv2-row-warn")||(J+=" brv2-row-warn-soft")),`<tr class="${J.trim()}">
              <td>${X}${de}</td>
              <td>${u(w(r.stmt_date))}</td>
              <td title="${u(r.stmt_desc)}" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${u(r.stmt_desc)}</td>
              <td class="num">${r.stmt_withdrawal?v(r.stmt_withdrawal):""}</td>
              <td class="num">${r.stmt_deposit?v(r.stmt_deposit):""}</td>
              <td>${u(w(r.gl_date))}</td>
              <td title="${u(r.gl_doc_no)}" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${u(r.gl_doc_no)}</td>
              <td class="num">${r.gl_debit?v(r.gl_debit):""}</td>
              <td class="num">${r.gl_credit?v(r.gl_credit):""}</td>
              <td>${z?"L"+z:"—"}</td>
            </tr>`}).join("")}async function Z(){const m=localStorage.getItem("mrpilot_token")||"";try{const T=await(await fetch("/api/recon/bank-v2/tasks",{headers:{Authorization:"Bearer "+m}})).json();ee(T.tasks||[])}catch{const T=o("brv2-history-empty"),U=window._currentLang||"zh",N={zh:"加载失败",th:"โหลดประวัติไม่ได้",en:"Load failed",ja:"読み込み失敗"}[U]||"加载失败";T&&(T.textContent=N,T.style.display="");const r=o("brv2-history-table-wrap");r&&(r.style.display="none")}}const le=10;let ie=1;function V(){const m=o("brv2-history-pager"),C=o("brv2-history-pager-info"),T=o("brv2-history-prev"),U=o("brv2-history-next");if(!m)return;if(_.length<=le){m.style.display="none";return}m.style.display="";const N=Math.ceil(_.length/le);C&&(C.textContent=ie+" / "+N),T&&(T.disabled=ie<=1),U&&(U.disabled=ie>=N)}function Q(){const m=o("brv2-history-prev"),C=o("brv2-history-next");m&&!m._brv2Bound&&(m._brv2Bound=!0,m.addEventListener("click",()=>{ie>1&&(ie--,ee(_))})),C&&!C._brv2Bound&&(C._brv2Bound=!0,C.addEventListener("click",()=>{const T=Math.ceil(_.length/le);ie<T&&(ie++,ee(_))}))}function ee(m){m!==void 0&&(_=m||[],ie=1);const C=_,T=o("brv2-history-empty"),U=o("brv2-history-table-wrap"),N=o("brv2-history-tbody");if(!N)return;const r=window._currentLang||"zh";if(!C.length){const ae={zh:"暂无对账记录",th:"ยังไม่มีประวัติ",en:"No records yet",ja:"記録なし"}[r]||"暂无对账记录";T&&(T.textContent=ae,T.style.display=""),U&&(U.style.display="none"),V();return}T&&(T.style.display="none"),U&&(U.style.display="");const j=Math.ceil(C.length/le);ie>j&&(ie=j);const z=(ie-1)*le,J=C.slice(z,z+le),X=localStorage.getItem("mrpilot_token")||"",de='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><circle cx="8" cy="8" r="6"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',se='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',ce='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';N.innerHTML="",J.forEach(ae=>{const pe=Number(ae.formula_diff||0),fe=Math.abs(pe)<.05,ve=(ae.stmt_files||"").split(";").map(ke=>ke.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),he=(ae.gl_files||"").split(";").map(ke=>ke.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),ye=ae.created_at?String(ae.created_at).slice(0,16).replace("T"," "):"",xe=document.createElement("tr");xe.dataset.taskId=ae.id;const Re=document.createElement("td");Re.textContent=ye;const Le=document.createElement("td");Le.className="glv-history-file",Le.title=ve+" + "+he,Le.textContent=ve+" + "+he;const Ce=document.createElement("td");Ce.className="glv-num",Ce.textContent=(ae.stmt_row_count||0)+" / "+(ae.gl_row_count||0);const Ve=document.createElement("td");Ve.className="glv-num",Ve.textContent=ae.matched_count||0;const Ue=document.createElement("td");Ue.className="glv-num",Ue.textContent=ae.unmatched_gl||0;const Ge=document.createElement("td");Ge.className="glv-num",Ge.textContent=ae.unmatched_stmt||0;const qe=document.createElement("td");qe.className="glv-num",qe.style.color=fe?"#059669":"#dc2626",qe.textContent=fe?"✓":v(pe);const Se=document.createElement("td");Se.className="glv-history-actions";const Ye=(ke,at,ot,xt)=>{const _e=document.createElement("button");return _e.type="button",_e.title=at,_e.setAttribute("aria-label",at),ot&&(_e.className=ot),_e.innerHTML=ke,_e.onclick=_t=>{_t.stopPropagation(),xt()},_e},bt={zh:"删除这条记录?",th:"ลบรายการนี้?",en:"Delete this record?",ja:"この記録を削除しますか?"}[r]||"删除?",yt={zh:"加载",th:"โหลด",en:"Load",ja:"読込"}[r]||"加载",wt={zh:"导出",th:"ส่งออก",en:"Export",ja:"エクスポート"}[r]||"导出",kt={zh:"删除",th:"ลบ",en:"Delete",ja:"削除"}[r]||"删除";Se.appendChild(Ye(de,yt,"",()=>oe(ae.id,X))),Se.appendChild(Ye(se,wt,"",()=>c(ae.id))),Se.appendChild(Ye(ce,kt,"glv-del",async()=>{await showConfirm(bt,{danger:!0})&&(await fetch("/api/recon/bank-v2/"+ae.id,{method:"DELETE",headers:{Authorization:"Bearer "+X}}),Z())})),[Re,Le,Ce,Ve,Ue,Ge,qe,Se].forEach(ke=>xe.appendChild(ke)),xe.style.cursor="pointer",xe.addEventListener("click",async ke=>{ke.target.closest(".glv-del")||ke.target.closest("button")||await oe(ae.id,X)}),N.appendChild(xe)}),V(),ne()}function ne(){const m=((o("brv2-hist-search")||{}).value||"").trim().toLowerCase(),C=o("brv2-history-tbody");C&&C.querySelectorAll("tr").forEach(T=>{T.dataset.taskId&&(T.style.display=!m||T.textContent.toLowerCase().includes(m)?"":"none")})}async function oe(m,C){try{const U=await(await fetch("/api/recon/bank-v2/"+m,{headers:{Authorization:"Bearer "+C}})).json();if(!U.ok)return;s={task_id:U.task_id,...U},g=U.detail||[],i="all",document.querySelectorAll(".brv2-filter-btn").forEach(N=>N.classList.toggle("active",N.dataset.filter==="all")),P(s)}catch{}}function ue(){if(e){Z();return}e=!0,W("brv2-stmt-zone","brv2-stmt-input","stmt"),W("brv2-gl-zone","brv2-gl-input","gl");const m=["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"];function C(){const z=parseFloat((o("brv2-anchor-stmt-opening")||{}).value),J=parseFloat((o("brv2-anchor-gl-opening")||{}).value),X=o("brv2-anchor-eq"),de=o("brv2-anchor-eq-val");if(!(!X||!de))if(Number.isFinite(z)&&Number.isFinite(J)){const se=z-J;de.textContent=se.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),X.style.display=""}else X.style.display="none"}m.forEach(z=>{const J=o(z);J&&(J.addEventListener("input",C),J.addEventListener("input",()=>{const X=J.closest(".brv2-anchor-cell");X&&X.classList.remove("is-prefilled"),f()}))}),A();const T=o("brv2-run-btn");T&&T.addEventListener("click",te);const U=o("brv2-reset-btn");U&&U.addEventListener("click",()=>{s=null,g=[],a=[],n=[],E("stmt"),E("gl"),M(),S(!1);const z=o("brv2-acct-select");z&&(z.style.display="none"),m.forEach(de=>{const se=o(de);if(se){se.value="";const ce=se.closest&&se.closest(".brv2-anchor-cell");ce&&ce.classList.remove("is-prefilled")}});const J=o("brv2-anchor-eq");J&&(J.style.display="none");const X=o("brv2-anchor-prefill-banner");X&&X.classList.remove("show")});const N=o("brv2-new-btn");N&&N.addEventListener("click",()=>{s=null,g=[],a=[],n=[],E("stmt"),E("gl"),M(),S(!1)});const r=o("brv2-filter-tabs");r&&r.addEventListener("click",z=>{z.stopPropagation();const J=z.target.closest(".brv2-filter-btn");J&&(i=J.dataset.filter,r.querySelectorAll(".brv2-filter-btn").forEach(X=>X.classList.toggle("active",X===J)),Y())}),x(),Q();const j=o("brv2-hist-search");j&&j.addEventListener("input",ne),Z(),M(),window._brv2LoadHistory=Z,Array.isArray(window.__i18nSubs)||(window.__i18nSubs=[]),window.__i18nSubs=window.__i18nSubs.filter(z=>z.name!=="brv2"),window.__i18nSubs.push({name:"brv2",fn:function(){M(),E("stmt"),E("gl"),s&&P(s),ee()}})}window._loadBankReconV2Panel=function(m){const C=m?document.getElementById(m):null;C&&C.id!=="recon-pane-bank"&&(C.innerHTML=`<div style="padding:16px;font-size:13px;color:var(--ink-3)">
                银行对账 v2 · 请前往对账中心使用</div>`),ue()},document.addEventListener("DOMContentLoaded",()=>{o("brv2-run-btn")&&ue()}),window._bankReconV2Init=ue})();(function(){const e=document.getElementById("general-lang");if(!e)return;e.addEventListener("change",n=>{const s=n.target.value;s&&applyLang(s)});const a=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";e.value=a})();(function(){const a="pearnly_general_tz",n="pearnly_general_date_format",s="pearnly_general_number_format",i={tz:"Asia/Bangkok",date:"YYYY-MM-DD",number:"comma_dot"};function g(){const v=document.getElementById("general-tz"),w=document.getElementById("general-date"),u=document.getElementById("general-number");if(!(!v||!w||!u))try{v.value=localStorage.getItem(a)||i.tz,w.value=localStorage.getItem(n)||i.date,u.value=localStorage.getItem(s)||i.number}catch{v.value=i.tz,w.value=i.date,u.value=i.number}}async function b(){const v=document.getElementById("btn-save-general"),w=document.getElementById("general-save-msg");if(!v)return;const u=v.innerHTML;v.disabled=!0,v.innerHTML="<span>"+(t("msg-saving")||"保存中...")+"</span>",w&&(w.textContent="",w.classList.remove("error"));try{const d=(document.getElementById("general-tz")||{}).value||i.tz,E=(document.getElementById("general-date")||{}).value||i.date,k=(document.getElementById("general-number")||{}).value||i.number;try{localStorage.setItem(a,d),localStorage.setItem(n,E),localStorage.setItem(s,k)}catch{}window._pearnlyGeneral={tz:d,date_format:E,number_format:k},w&&(w.textContent=t("msg-saved")||"已保存")}catch{w&&(w.textContent=t("msg-save-failed")||"保存失败",w.classList.add("error"))}finally{v.disabled=!1,v.innerHTML=u,setTimeout(function(){w&&(w.textContent="")},3e3)}}function _(){const v=document.getElementById("btn-save-general");if(!v){setTimeout(_,200);return}v._pearnlyGenBound||(v._pearnlyGenBound=!0,v.addEventListener("click",b),g())}function o(){g();const v=document.getElementById("general-lang");if(v){const w=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";v.value=w}}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",_):_(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("settings-general",o)})();(function(){const e="mrpilot_nav_collapsed",a={ocr:"sales",history:"sales",reconcile:"sales","sales-invoices":"sales",receivables:"sales",vouchers:"expense"};function n(){try{const b=localStorage.getItem(e);return b?JSON.parse(b):{}}catch{return{}}}function s(b){try{localStorage.setItem(e,JSON.stringify(b))}catch{}}function i(){const b=n();document.querySelectorAll(".nav-collapsible").forEach(function(_){const o=_.dataset.collapsible;b[o]?_.classList.add("collapsed"):_.classList.remove("collapsed")})}function g(b){const _=n();_[b]=!_[b],s(_),i()}(function(){const _=n();let o=!1;_.sales===void 0&&(_.sales=!1,o=!0),_.expense===void 0&&(_.expense=!0,o=!0),o&&s(_)})(),i(),document.querySelectorAll(".nav-group-toggle").forEach(function(b){b.addEventListener("click",function(){g(b.dataset.toggleGroup)})}),window.expandNavGroupForRoute=function(b){const _=a[b];if(!_)return;const o=n();o[_]&&(o[_]=!1,s(o),i())}})();(function(){function e(){const a=document.getElementById("help-modal"),n=document.getElementById("help-modal-close");a&&(n&&!n.dataset.bound&&(n.addEventListener("click",function(){a.style.display="none"}),n.dataset.bound="1"),a.dataset.maskBound||(a.addEventListener("click",function(s){s.target===a&&(a.style.display="none")}),a.dataset.maskBound="1"),window._helpModalEscBound||(document.addEventListener("keydown",function(s){s.key==="Escape"&&a.style.display==="flex"&&(a.style.display="none")}),window._helpModalEscBound=!0))}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",e):e()})();(function(){const e={line:"line",folder:"folder",gmail:"email",erp:"erp",alert:"alert"};document.addEventListener("click",function(a){const n=a.target.closest(".int-btn-configure");if(!n)return;const s=n.closest(".integration-row"),i=s?s.dataset.intAnchor:null;if(i&&e[i]){const g=s.querySelector(".int-name"),b=g?(g.textContent||g.innerText||"").trim():"配置";typeof window.openIntegrationDrawer=="function"&&window.openIntegrationDrawer(e[i],b)}})})();let we=[];window._erpEndpoints=we;let Pe=null,Ee={key:"all",val:""},be=new Set;async function Ie(e){const a=document.getElementById("erp-logs-list");if(a){e||(a.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`),nt();try{const n=new URLSearchParams({limit:"30"});Ee.key==="status"&&n.set("status",Ee.val),Ee.key==="trigger"&&n.set("trigger",Ee.val),Ee.key==="adapter"&&n.set("adapter",Ee.val);const s=await fetch(`/api/erp/logs?${n}`,{headers:{Authorization:"Bearer "+token}});if(!s.ok){a.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const g=(await s.json()).items||[];if(window._erpLogPollTimer&&(clearTimeout(window._erpLogPollTimer),window._erpLogPollTimer=null),g.some(function(v){return v.status==="pending"})&&(window._erpLogPollTimer=setTimeout(function(){Ie(!0)},4e3)),g.length===0){a.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-empty"))}</div>`;return}const _='<div class="erp-log-row erp-log-row-header" data-log-header>'+(g.filter(function(v){var w=v.status==="failed"&&v.next_retry_at&&new Date(v.next_retry_at).getTime()>Date.now()-6e4;return!w}).map(function(v){return v.id}).length>0?`<input type="checkbox" class="erp-log-cb erp-log-cb-all" data-log-select-all title="${escapeHtml(t("erp-log-select-all-tip"))}">`:'<span class="erp-log-cb-spacer"></span>')+`<span class="log-time">${escapeHtml(t("erp-log-col-time"))}</span><span class="log-status">${escapeHtml(t("erp-log-col-status"))}</span><span class="log-tag-header">${escapeHtml(t("erp-log-col-trigger"))}</span><span class="log-invoice">${escapeHtml(t("erp-log-col-invoice"))}</span><span class="log-workspace">${escapeHtml(t("erp-log-col-workspace"))}</span><span class="log-client">${escapeHtml(t("erp-log-col-client"))}</span><span class="log-seller">${escapeHtml(t("erp-log-col-seller"))}</span><span class="log-erp">${escapeHtml(t("erp-log-col-erp"))}</span><span class="log-doc">${escapeHtml(t("erp-log-col-doc"))}</span><span class="log-http">${escapeHtml(t("erp-log-col-http"))}</span><span class="log-elapsed">${escapeHtml(t("erp-log-col-elapsed"))}</span><span class="log-actions"></span></div>`;a.innerHTML=_+g.map(v=>{const w=new Date(v.created_at),u=`${String(w.getMonth()+1).padStart(2,"0")}-${String(w.getDate()).padStart(2,"0")} ${String(w.getHours()).padStart(2,"0")}:${String(w.getMinutes()).padStart(2,"0")}`,d=v.status==="failed"&&v.next_retry_at&&new Date(v.next_retry_at).getTime()>Date.now()-6e4;let E,k,q;v.status==="pending"?(E="retrying",k="⟳",q=t("erp-status-pending")):v.status==="success"?(E="ok",k="✓",q=t("erp-status-success")):v.status==="skipped_dup"?(E="skipped",k="⏭",q=t("erp-status-skipped")):d?(E="retrying",k="↻",q=t("erp-status-retrying")):(E="fail",k="✗",q=t("erp-status-failed"));let R;v.trigger==="auto"?R=`<span class="log-tag auto">${escapeHtml(t("log-tag-auto"))}</span>`:v.trigger==="retry"?R=`<span class="log-tag retry">${escapeHtml(t("log-tag-retry"))}</span>`:R=`<span class="log-tag manual">${escapeHtml(t("log-tag-manual"))}</span>`;let y="";const B=v.retry_count||0,O=v.max_retries||3;if(d){const W=new Date(v.next_retry_at).getTime()-Date.now(),G=Math.max(0,Math.round(W/6e4)),K=G<=0?t("erp-retry-next-soon"):t("erp-retry-next-min",{n:G});y=`${t("erp-retry-attempt",{n:B,max:O})} · ${K}`}else v.status==="failed"&&B>=O&&!v.next_retry_at&&(y=t("erp-retry-exhausted",{n:B}));const D=v.status==="failed"&&!d?`<button class="log-retry-btn" data-log-retry="${escapeHtml(v.id)}" title="${escapeHtml(t("log-retry-title"))}">↻</button>`:"",F=!d,A=be.has(v.id)?"checked":"",f=F?`<input type="checkbox" class="erp-log-cb" data-log-cb="${escapeHtml(v.id)}" ${A}>`:'<span class="erp-log-cb-spacer"></span>',l=(v.ocr_buyer_name||"").trim()||(v.client_name||"").trim(),p=l?`<span class="log-client" title="${escapeHtml(l)}">${escapeHtml(l.substring(0,18))}</span>`:`<span class="log-client log-client-empty" title="${escapeHtml(t("erp-log-client-unassigned-tip"))}">${escapeHtml(t("erp-log-client-unassigned"))}</span>`,I=v.workspace_name?`<span class="log-workspace">${escapeHtml((v.workspace_name||"").substring(0,16))}</span>`:`<span class="log-workspace log-workspace-unresolved" title="${escapeHtml(t("erp-log-ws-unresolved-tip"))}">${escapeHtml(t("erp-log-ws-unresolved"))}</span>`,L=v.endpoint_name?`<span class="log-erp">${escapeHtml((v.endpoint_name||"").substring(0,14))}</span>`:`<span class="log-erp log-erp-deleted">${escapeHtml(t("erp-log-endpoint-deleted"))}</span>`,H=(v.external_doc_no||"").trim(),x=(v.external_url||"").trim();let M;return x?M=`<span class="log-doc"><a href="${escapeHtml(x)}" target="_blank" rel="noopener" class="log-doc-open" title="${escapeHtml(H||"")}">${escapeHtml(t("erp-log-doc-open"))}</a></span>`:H?M=`<span class="log-doc log-doc-copy" data-copy-doc="${escapeHtml(H)}" title="${escapeHtml(t("erp-log-doc-copy-tip"))}">${escapeHtml(H.substring(0,18))}</span>`:v.status==="success"?M=`<span class="log-doc log-doc-missing" title="${escapeHtml(t("erp-log-doc-missing-tip"))}">${escapeHtml(t("erp-log-doc-missing"))}</span>`:M='<span class="log-doc log-doc-empty">-</span>',`
                <div class="erp-log-row ${E}" data-log-detail="${escapeHtml(v.id)}">
                    ${f}
                    <span class="log-time">${u}</span>
                    <span class="log-status" title="${escapeHtml(q+(y?" · "+y:""))}">${k}</span>
                    ${R}
                    <span class="log-invoice">${escapeHtml(v.invoice_no||"-")}</span>
                    ${I}
                    ${p}
                    <span class="log-seller">${escapeHtml((v.seller_name||"").substring(0,20))}</span>
                    ${L}
                    ${M}
                    <span class="log-http">HTTP ${v.http_status||"-"}</span>
                    <span class="log-elapsed">${v.elapsed_ms}ms</span>
                    <span class="log-actions">${D}</span>
                </div>
            `}).join("");const o=new Set(g.map(v=>v.id));for(const v of Array.from(be))o.has(v)||be.delete(v);Ae()}catch(n){console.error("load erp logs failed",n),a.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}function Ae(){const e=document.getElementById("erp-logs-batch-bar"),a=document.getElementById("erp-logs-batch-count"),n=document.querySelector("[data-log-select-all]");if(n){const g=document.querySelectorAll("[data-log-cb]").length,b=be.size;b===0?(n.checked=!1,n.indeterminate=!1):b>=g?(n.checked=!0,n.indeterminate=!1):(n.checked=!1,n.indeterminate=!0)}if(!e||!a)return;const s=be.size;if(s===0){e.style.display="none";return}e.style.display="",a.textContent=t("erp-batch-selected",{n:s})}async function dt(){console.info("[ErpBatch] retry triggered · selected=",be.size);const e=Array.from(be);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-confirm",{n:e.length})))try{const n=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!n.ok){showToast(t("erp-logs-error"),"error");return}const s=await n.json(),i=t("erp-batch-result",{ok:s.succeeded||0,fail:s.failed||0,skip:s.skipped||0}),g=s.failed&&s.failed>0?"warn":"success";showToast(i,g),be.clear(),Ie()}catch(n){console.error("batch retry failed",n),showToast(t("erp-logs-error"),"error")}}async function Tt(){console.info("[ErpBatch] delete triggered · selected=",be.size);const e=Array.from(be);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-delete-confirm",{n:e.length}),{danger:!0}))try{const s=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!s.ok){showToast(t("erp-logs-error"),"error");return}const i=await s.json();e.forEach(function(g){var b=document.querySelector('[data-log-detail="'+g+'"]');b&&b.remove()});var n=document.getElementById("erp-logs-batch-bar");n&&(n.style.display="none"),showToast(t("erp-batch-delete-result",{n:i.deleted||0,skip:i.skipped||0}),i.deleted>0?"success":"warn"),be.clear(),setTimeout(Ie,500)}catch(s){console.error("batch delete failed",s),showToast(t("erp-logs-error"),"error")}}(function(){function a(){var n=document.getElementById("btn-erp-batch-retry"),s=document.getElementById("btn-erp-batch-delete"),i=document.getElementById("btn-erp-batch-clear");n&&!n.dataset.boundDirect&&(n.addEventListener("click",function(g){g.preventDefault(),g.stopPropagation(),dt()}),n.dataset.boundDirect="1"),s&&!s.dataset.boundDirect&&(s.addEventListener("click",function(g){g.preventDefault(),g.stopPropagation(),Tt()}),s.dataset.boundDirect="1"),i&&!i.dataset.boundDirect&&(i.addEventListener("click",function(g){g.preventDefault(),g.stopPropagation(),be.clear(),document.querySelectorAll(".erp-log-cb").forEach(function(b){b.checked=!1}),Ae()}),i.dataset.boundDirect="1")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",a):a(),setTimeout(a,2e3),setTimeout(a,5e3),window._bindErpBatchButtons=a})();async function et(e){if(e=(e||"").trim(),!!e)try{await navigator.clipboard.writeText(e),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{try{const n=document.createElement("textarea");n.value=e,n.style.position="fixed",n.style.opacity="0",document.body.appendChild(n),n.select(),document.execCommand("copy"),n.remove(),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{showToast(t("erp-doc-copy-fail"),"error")}}}async function pt(e){const a=document.createElement("div");a.className="log-detail-modal",a.innerHTML=`
        <div class="log-detail-box">
            <div class="log-detail-loading">${escapeHtml(t("log-detail-loading"))}</div>
        </div>
    `,document.body.appendChild(a),a.addEventListener("click",async n=>{if(n.target===a||n.target.classList.contains("log-detail-close")){a.remove();return}const s=n.target.closest("[data-receipt-copy]");if(s){et(s.dataset.receiptCopy);return}const i=n.target.closest("[data-receipt-action]");if(i){const g=i.dataset.receiptAction;g==="retry"?tt(i.dataset.logId):g==="exceptions"?typeof routeTo=="function"&&routeTo("exceptions"):g==="mappings"&&typeof routeTo=="function"&&routeTo("integrations"),a.remove();return}});try{const n=await fetch(`/api/erp/logs/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!n.ok){a.remove();return}const s=await n.json(),i=we.find(L=>L.id===s.endpoint_id),g=s.endpoint_name||(i?i.name:s.endpoint_id?t("erp-log-endpoint-deleted"):"-"),b=(s.endpoint_adapter||i&&i.adapter||"").toLowerCase(),_=new Date(s.created_at).toLocaleString(),o=s.trigger==="auto"?t("log-tag-auto"):s.trigger==="retry"?t("log-tag-retry"):t("log-tag-manual"),v=s.request_body?JSON.stringify(s.request_body,null,2):t("erp-receipt-no-tech"),w=s.response_body||t("erp-receipt-no-tech"),u=s.status==="success";let d=typeof w=="string"?w:JSON.stringify(w,null,2);if(u)try{const L=typeof s.response_body=="string"?JSON.parse(s.response_body):s.response_body||{},H=L.row_count||(Array.isArray(L.imported_rows)?L.imported_rows.length:0);H>0&&(d=t("log-push-rows").replace("{n}",String(H)))}catch{}const E=(s.external_doc_no||"").trim(),k=(s.external_url||"").trim(),q=(s.external_doc_hint||"").trim(),R=(s.ocr_buyer_name||"").trim()||s.client_name||"-",y=s.seller_name||"-";let B="-";const O=Number(s.total_amount);s.total_amount!=null&&s.total_amount!==""&&!isNaN(O)&&(B=O.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}));const D=u?t("erp-receipt-title-ok"):t("erp-receipt-title-fail"),F=u?"✓":"✗",A=[],f=(L,H)=>{A.push(`
                <div class="erp-receipt-row">
                    <span class="erp-receipt-key">${escapeHtml(L)}</span>
                    <span class="erp-receipt-val">${H}</span>
                </div>`)};if(f(t("erp-receipt-invoice-no"),`<strong>${escapeHtml(s.invoice_no||"-")}</strong>`),f(t("erp-receipt-erp-name"),escapeHtml(g)),u){let L;E?L=`<strong class="erp-receipt-docno">${escapeHtml(E)}</strong><button class="erp-receipt-copy-btn" type="button" data-receipt-copy="${escapeHtml(E)}" title="${escapeHtml(t("erp-doc-copy-tip"))}">${escapeHtml(t("erp-receipt-copy-btn"))}</button>`:L=`<span class="erp-receipt-docno-missing">${escapeHtml(t("erp-log-doc-missing"))}</span>`,f(t("erp-receipt-doc-no"),L)}f(t("erp-receipt-client"),escapeHtml(R)),f(t("erp-receipt-seller"),escapeHtml(y)),u&&f(t("erp-receipt-amount"),escapeHtml(B)),f(t("erp-receipt-time"),escapeHtml(_)),f(t("erp-receipt-elapsed"),escapeHtml((s.elapsed_ms!=null?s.elapsed_ms:"-")+"ms"));let l="";u&&k?l=`<a class="erp-receipt-primary-btn" href="${escapeHtml(k)}" target="_blank" rel="noopener">${escapeHtml(t("erp-receipt-open-erp"))}</a>`:u&&E&&(l=`<button class="erp-receipt-primary-btn" type="button" data-receipt-copy="${escapeHtml(E)}">${escapeHtml(t("erp-receipt-copy-docno"))}</button>`);let p="";if(u&&E&&q){const L="erp-receipt-hint-"+q,H=t(L);H&&H!==L&&(p=`<div class="erp-receipt-hint"><svg class="erp-receipt-hint-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span>${escapeHtml(H)}</span></div>`)}let I="";if(!u){const L=(s.error_msg||"").match(/ERR_[A-Z0-9_]+/),H=L?L[0]:"",x=typeof currentLang=="string"&&currentLang||window._currentLang||"th",W=s.error_friendly&&s.error_friendly[x]||(s.error_msg?humanizeError(s.error_msg):t("erp-receipt-no-error")),G=/ERR_NO_CUSTOMER_MAPPING|ERR_NO_CLIENT|ERR_NO_SEED_CUSTOMER|ERR_NO_SEED_PRODUCT/.test(s.error_msg||""),K=!!(s.history_id&&s.endpoint_id),te=[];te.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="exceptions">${escapeHtml(t("erp-receipt-act-exceptions"))}</button>`),G&&te.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="mappings">${escapeHtml(t("erp-receipt-act-mapping"))}</button>`),K&&te.push(`<button class="erp-receipt-action-btn primary" type="button" data-receipt-action="retry" data-log-id="${escapeHtml(s.id)}">${escapeHtml(t("erp-receipt-act-retry"))}</button>`),I=`
                <div class="erp-receipt-fail-reason-label">${escapeHtml(t("erp-receipt-fail-reason"))}</div>
                <div class="erp-receipt-fail-box">
                    ${H?`<div class="erp-receipt-errcode">${escapeHtml(H)}</div>`:""}
                    <div class="erp-receipt-friendly">${escapeHtml(W)}</div>
                </div>
                <div class="erp-receipt-actions-label">${escapeHtml(t("erp-receipt-suggest"))}</div>
                <div class="erp-receipt-actions">${te.join("")}</div>`}a.querySelector(".log-detail-box").innerHTML=`
            <div class="log-detail-head">
                <div class="log-detail-title">
                    <span class="log-detail-status-icon ${u?"ok":"fail"}">${F}</span>
                    ${escapeHtml(D)}
                    <span class="log-tag ${s.trigger}">${escapeHtml(o)}</span>
                </div>
                <button class="log-detail-close" type="button">✕</button>
            </div>

            <div class="erp-receipt-body">
                ${A.join("")}
            </div>

            ${p}
            ${l?`<div class="erp-receipt-primary-wrap">${l}</div>`:""}
            ${I}

            <details class="log-detail-collapsible">
                <summary>${escapeHtml(t("erp-receipt-tech-toggle"))}</summary>
                <div class="log-detail-meta" style="margin-top:8px;">
                    <span>HTTP ${s.http_status||"-"}</span>
                    <span>${s.elapsed_ms}ms</span>
                    <span>${escapeHtml(t("log-detail-attempt",{n:s.attempt||1}))}</span>
                </div>
                <div class="log-detail-section" style="margin-top:12px;">
                    <div class="log-detail-label">${escapeHtml(t("log-detail-request-human"))}</div>
                    <pre>${escapeHtml(v)}</pre>
                </div>
                <div class="log-detail-section">
                    <div class="log-detail-label">${escapeHtml(t("log-detail-response-human"))}</div>
                    <pre>${escapeHtml(d)}</pre>
                </div>
            </details>
        `}catch(n){console.error(n),a.remove()}}async function tt(e){try{const a=await fetch(`/api/erp/logs/${encodeURIComponent(e)}/retry`,{method:"POST",headers:{Authorization:"Bearer "+token}}),n=await a.json().catch(()=>({}));a.ok&&n.ok?showToast(t("log-retry-ok"),"success"):showToast(t("log-retry-fail")+" · HTTP "+(n.http_status||a.status),"error"),Ie(),De()}catch{showToast(t("log-retry-fail"),"error")}}async function De(){try{const e=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(e.status===401){localStorage.removeItem("mrpilot_token");const n=await e.json().catch(()=>({}));if((typeof n.detail=="string"?n.detail:n.detail&&n.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}we=(await e.json()).items||[],window._erpEndpoints=we,ut()}catch(e){console.error("load endpoints failed",e)}}window._refreshErpEndpointsCache=function(){return De()};async function nt(){const e=document.getElementById("erp-today-stats");if(e){e.innerHTML="";try{const a=await fetch("/api/erp/stats/today",{headers:{Authorization:"Bearer "+token}});if(!a.ok)return;const n=await a.json(),s=n.total||0,i=n.success||0,g=n.failed||0,b=n.auto_cnt||0;if(s===0){e.innerHTML=`<span class="erp-today-empty">${escapeHtml(t("erp-today-none"))}</span>`;return}const _=[];_.push(`<span class="erp-today-item"><strong>${s}</strong> ${escapeHtml(t("erp-today-total"))}</span>`),i>0&&_.push(`<span class="erp-today-item ok"><strong>${i}</strong> ${escapeHtml(t("erp-today-success"))}</span>`),g>0&&_.push(`<span class="erp-today-item fail"><strong>${g}</strong> ${escapeHtml(t("erp-today-failed"))}</span>`),b>0&&_.push(`<span class="erp-today-item auto"><strong>${b}</strong> ${escapeHtml(t("erp-today-auto"))}</span>`),e.innerHTML=_.join("")}catch(a){console.warn("loadErpTodayStats failed",a)}}}function ut(){const e=document.getElementById("erp-endpoints-list"),a=document.getElementById("erp-status-summary"),n=document.getElementById("btn-add-endpoint");if(!e){console.warn("erp-endpoints-list 容器不存在");return}if(n&&_userInfo){const i=_userInfo.endpoints_limit;i!==-1&&we.length>=i?(n.disabled=!0,n.title=t("ep-limit-reached",{limit:i}),n.classList.add("btn-disabled-plus")):(n.disabled=!1,n.title="",n.classList.remove("btn-disabled-plus"))}if(we.length===0){e.innerHTML=`<div class="erp-empty">${escapeHtml(t("ep-list-empty"))}</div>`,a&&(a.textContent=t("auto-status-none"),a.className="auto-status-pill none");return}const s=we.some(i=>i.auto_push&&i.enabled);if(a&&(a.textContent=t("auto-status-active",{n:we.length,mode:s?t("auto-status-on"):t("auto-status-off")}),a.className="auto-status-pill "+(s?"active":"ready")),nt(),e.innerHTML=we.map(i=>{const g=i.config||{},b=escapeHtml(g.url||"");g._token_set;const _=i.enabled!==!1,o=[];i.is_default&&o.push(`<span class="ep-badge default">${escapeHtml(t("ep-default"))}</span>`),i.auto_push&&o.push(`<span class="ep-badge auto">${escapeHtml(t("ep-auto-push-on"))}</span>`),_||o.push(`<span class="ep-badge disabled">${escapeHtml(t("ep-disabled"))}</span>`);const v=[];return i.success_count>0&&v.push(`<span class="ep-stat ok">${escapeHtml(t("ep-success",{n:i.success_count}))}</span>`),i.failure_count>0&&v.push(`<span class="ep-stat fail">${escapeHtml(t("ep-failure",{n:i.failure_count}))}</span>`),`
            <div class="erp-endpoint" data-ep-id="${escapeHtml(i.id)}">
                <div class="ep-main">
                    <div class="ep-title-row">
                        <div class="ep-name">${escapeHtml(i.name)}</div>
                        <div class="ep-badges">${o.join("")}</div>
                    </div>
                    <div class="ep-url">${b||"-"}</div>
                    <div class="ep-stats">${v.join(" · ")}</div>
                </div>
                <div class="ep-actions">
                    <button class="btn btn-ghost btn-small" data-ep-edit="${escapeHtml(i.id)}">
                        <span>${escapeHtml(t("ep-edit"))}</span>
                    </button>
                    <button class="btn btn-ghost btn-small btn-danger" data-ep-del="${escapeHtml(i.id)}">
                        <span>${escapeHtml(t("ep-delete"))}</span>
                    </button>
                </div>
            </div>
        `}).join(""),_userInfo&&_userInfo.endpoints_limit!==-1){const i=we.length,g=_userInfo.endpoints_limit,b=_userInfo.plan,_=document.createElement("div");_.className="erp-limit-hint",b==="free"?_.innerHTML=`${escapeHtml(t("ep-free-limit-hint",{used:i,limit:g}))} <a data-upgrade="plus">${escapeHtml(t("upgrade-to-plus"))}</a>`:_.textContent=t("ep-plus-limit-hint",{used:i,limit:g}),e.appendChild(_)}}function We(e){Pe=e||null;const a=document.getElementById("endpoint-modal"),n=document.getElementById("endpoint-modal-title");n.textContent=e?t("ep-modal-title-edit"):t("ep-modal-title-new");const s=document.getElementById("ep-name"),i=document.getElementById("ep-url"),g=document.getElementById("ep-token"),b=document.getElementById("ep-is-default"),_=document.getElementById("ep-auto-push"),o=document.getElementById("ep-test-result");o.style.display="none",o.textContent="";const v=document.getElementById("ep-save-error");if(v&&v.remove(),e){const u=we.find(d=>d.id===e);if(!u)return;s.value=u.name||"",i.value=(u.config||{}).url||"",g.value=(u.config||{})._token_set&&u.config.token||"",g.placeholder=(u.config||{})._token_set?"（已保存 · 留空保持不变）":t("ep-token-ph"),b.checked=!!u.is_default,_.checked=!!u.auto_push}else s.value="",i.value="",g.value="",g.placeholder=t("ep-token-ph"),b.checked=we.length===0,_.checked=!0;const w=_.closest(".form-switch-row");if(_.disabled=!1,w){w.classList.remove("disabled-plus"),w.title="",w.style.cursor="",w.onclick=null;const u=w.querySelector(".plus-badge");u&&u.remove()}a.style.display="",setTimeout(()=>s.focus(),50)}function Oe(){document.getElementById("endpoint-modal").style.display="none",Pe=null;const e=document.getElementById("ep-save-error");e&&e.remove()}function ft(e){if(!e)return"";let a=e.trim();const n=a.search(/\s/);return n>=0&&(a=a.slice(0,n)),a}function vt(){const e=document.getElementById("ep-name").value.trim(),a=ft(document.getElementById("ep-url").value),n=document.getElementById("ep-token").value,s=document.getElementById("ep-is-default").checked,i=document.getElementById("ep-auto-push").checked,g={url:a};return n&&(g.token=n),{name:e,url:a,tokenVal:n,isDefault:s,autoPush:i,config:g}}async function mt(){const{url:e,config:a}=vt(),n=document.getElementById("ep-test-result");if(!e){n.style.display="",n.className="form-test-result fail",n.textContent=t("ep-required");return}n.style.display="",n.className="form-test-result running",n.textContent=t("ep-test-running");try{const i=await(await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({adapter:"webhook",config:a})})).json();i.success?(n.className="form-test-result ok",n.textContent=t("ep-test-ok",{status:i.http_status,ms:i.elapsed_ms})):(n.className="form-test-result fail",n.textContent=t("ep-test-fail",{err:i.error_msg||"unknown"}))}catch(s){n.className="form-test-result fail",n.textContent=t("ep-test-fail",{err:s.message})}}async function gt(){const e=vt(),a=document.getElementById("ep-save-error");if(a&&(a.style.display="none"),!e.name||!e.url){it(t("ep-required"));return}const n={name:e.name,adapter:"webhook",config:e.config,is_default:e.isDefault,auto_push:e.autoPush},s=document.getElementById("btn-ep-save"),i=s.innerHTML;s.disabled=!0,s.classList.add("loading");try{let g;if(Pe?g=await fetch(`/api/erp/endpoints/${encodeURIComponent(Pe)}`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(n)}):g=await fetch("/api/erp/endpoints",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(n)}),!g.ok){const _=(await g.json().catch(()=>({}))).detail||`HTTP ${g.status}`;throw new Error(typeof _=="string"?_:JSON.stringify(_))}Oe(),showToast(t("ep-save-ok")),De()}catch(g){it(`${t("ep-save-fail")} · ${g.message||"unknown"}`)}finally{s.disabled=!1,s.classList.remove("loading"),s.innerHTML=i}}function it(e){let a=document.getElementById("ep-save-error");if(!a){const n=document.querySelector("#endpoint-modal .modal-foot");if(!n)return;a=document.createElement("div"),a.id="ep-save-error",a.className="ep-inline-error",n.parentNode.insertBefore(a,n)}a.textContent=e,a.style.display=""}async function ht(e){const a=we.find(s=>s.id===e);if(!(!a||!await showConfirm(t("ep-delete-confirm",{name:a.name}),{danger:!0})))try{if(!(await fetch(`/api/erp/endpoints/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showToast(t("ep-delete-ok")),De()}catch{showToast(t("ep-save-fail"),"fail")}}(function(){document.getElementById("btn-add-endpoint").addEventListener("click",()=>We(null)),document.getElementById("endpoint-modal-close").addEventListener("click",Oe),document.getElementById("btn-ep-cancel").addEventListener("click",Oe),document.getElementById("btn-ep-test").addEventListener("click",mt),document.getElementById("btn-ep-save").addEventListener("click",gt),document.getElementById("ep-url").addEventListener("blur",a=>{const n=ft(a.target.value);n!==a.target.value.trim()&&(a.target.value=n)}),document.addEventListener("click",a=>{const n=a.target.closest("[data-ep-edit]"),s=a.target.closest("[data-ep-del]");n&&We(n.dataset.epEdit),s&&ht(s.dataset.epDel);const i=a.target.closest("[data-log-retry]");if(i){a.stopPropagation(),tt(i.dataset.logRetry);return}const g=a.target.closest("[data-log-cb]");if(g){a.stopPropagation();const w=g.dataset.logCb;g.checked?be.add(w):be.delete(w),Ae();return}const b=a.target.closest("[data-log-select-all]");if(b){a.stopPropagation();const w=b.checked;document.querySelectorAll("[data-log-cb]").forEach(function(d){d.checked=w;const E=d.dataset.logCb;w?be.add(E):be.delete(E)}),Ae();return}if(a.target.closest("#btn-erp-batch-retry")){a.stopPropagation(),dt();return}if(a.target.closest("#btn-erp-batch-clear")){a.stopPropagation(),be.clear(),document.querySelectorAll(".erp-log-cb").forEach(w=>{w.checked=!1}),Ae();return}const _=a.target.closest("[data-log-detail]");if(_){if(a.target.closest("[data-log-cb]"))return;const w=a.target.closest("[data-copy-doc]");if(w){a.stopPropagation(),et(w.dataset.copyDoc);return}if(a.target.closest(".log-doc-open"))return;pt(_.dataset.logDetail);return}const o=a.target.closest(".chip-filter");if(o){document.querySelectorAll("#erp-logs-filters .chip-filter").forEach(w=>w.classList.remove("active")),o.classList.add("active"),Ee={key:o.dataset.filterKey,val:o.dataset.filterVal},Ie();return}if(a.target.closest("#btn-refresh-logs")){const w=a.target.closest("#btn-refresh-logs");w.classList.add("spinning"),setTimeout(()=>w.classList.remove("spinning"),600),Ie();return}const v=a.target.closest(".auto-nav-item");if(v&&v.dataset.autoTab){switchAutomationTab(v.dataset.autoTab);return}})})();window.loadErpLogs=Ie;window.loadErpEndpoints=De;window.loadErpTodayStats=nt;window.renderErpEndpointsList=ut;window.showLogDetail=pt;window.retryPushLog=tt;window.copyErpDocNo=et;window.openEndpointModal=We;window.closeEndpointModal=Oe;window.saveEndpoint=gt;window.deleteEndpoint=ht;window.testEndpointConnection=mt;(function(){let e=null,a=!1;function n(){if(e)return e;const _=document.createElement("div");_.id="line-email-modal",_.style.cssText="position:fixed;inset:0;background:rgba(10,14,39,0.85);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;",_.innerHTML=`
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
        `,document.body.appendChild(_),e=_;const o=_.querySelector("#line-email-input"),v=_.querySelector("#line-email-submit-btn"),w=_.querySelector("#line-email-err");async function u(){w.textContent="";const d=(o.value||"").trim().toLowerCase();if(!d||d.indexOf("@")<0||d.split("@")[1].indexOf(".")<0){w.textContent=t("line-email-err-invalid");return}v.disabled=!0,v.style.opacity="0.6";try{const E=await fetch("/api/me/line_complete_email",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},body:JSON.stringify({email:d})});if(!E.ok)throw new Error("http_"+E.status);const k=await E.json();k.token&&localStorage.setItem("mrpilot_token",k.token),typeof showToast=="function"&&showToast(k.merged?t("line-email-merged-toast"):t("line-email-saved-toast"),"success"),setTimeout(function(){window.location.reload()},600)}catch{w.textContent=t("line-email-err-failed"),v.disabled=!1,v.style.opacity="1"}}return v.addEventListener("click",u),o.addEventListener("keydown",function(d){d.key==="Enter"&&u()}),_}function s(){if(!e)return;const _=e.querySelector("#line-email-title-h"),o=e.querySelector("#line-email-sub-p"),v=e.querySelector("#line-email-input"),w=e.querySelector("#line-email-submit-btn");_&&(_.textContent=t("line-email-title")),o&&(o.textContent=t("line-email-sub")),v&&(v.placeholder=t("line-email-placeholder")),w&&(w.textContent=t("line-email-submit"))}function i(){n(),s(),e.style.display="flex",a=!0;const _=e.querySelector("#line-email-input");_&&setTimeout(function(){_.focus()},100)}async function g(){const _=localStorage.getItem("mrpilot_token");if(_)try{const o=await fetch("/api/me/needs_email",{headers:{Authorization:"Bearer "+_}});if(!o.ok)return;const v=await o.json();v&&v.needs_email&&i()}catch{}}function b(){setTimeout(g,800)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",b):b(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("line-email-modal",function(){a&&s()})})();(function(){function e(_){let o=0;return _.length>=8&&o++,_.length>=12&&o++,/[a-zA-Z]/.test(_)&&/\d/.test(_)&&o++,/[^a-zA-Z0-9]/.test(_)&&o++,Math.min(3,o)}function a(_,o){const v=document.getElementById("cpw-msg");v&&(v.textContent=_,v.className="cpw-msg "+(o||""))}function n(_){return typeof t=="function"?t(_):_}function s(){const _=["cpw-old","cpw-new","cpw-confirm"];_.forEach(d=>{const E=document.getElementById(d);E&&(E.value="",E.setAttribute("readonly","readonly"),E.addEventListener("focus",function(){this.removeAttribute("readonly")}))}),document.querySelectorAll('.settings-nav-item[data-settings-tab="account"]').forEach(d=>{d.addEventListener("click",()=>{setTimeout(()=>{_.forEach(k=>{const q=document.getElementById(k);q&&(q.value="",q.setAttribute("readonly","readonly"))});const E=document.getElementById("cpw-strength-bar");E&&(E.style.width="0%",E.className="cpw-strength-bar"),a("","")},100)})}),document.querySelectorAll(".cpw-eye").forEach(d=>{d.addEventListener("click",()=>{const E=d.dataset.target,k=document.getElementById(E);k&&(k.type=k.type==="password"?"text":"password")})});const o=document.getElementById("cpw-new"),v=document.getElementById("cpw-strength-bar");o&&v&&o.addEventListener("input",()=>{const d=e(o.value),E=["0%","33%","66%","100%"],k=["","weak","medium","strong"];v.style.width=E[d],v.className="cpw-strength-bar "+k[d]});const w=document.getElementById("cpw-forgot-link");w&&w.addEventListener("click",()=>i());const u=document.getElementById("btn-change-pw");u&&u.addEventListener("click",async()=>{const d=document.getElementById("cpw-old"),E=document.getElementById("cpw-new"),k=document.getElementById("cpw-confirm");if(!d||!E||!k)return;const q=d.value,R=E.value,y=k.value;if(!q||!R||!y){a(n("settings-change-pw-empty"),"error");return}if(R.length<8){a(n("settings-change-pw-too-short"),"error");return}if(!(/[a-zA-Z]/.test(R)&&/\d/.test(R))){a(n("settings-change-pw-too-weak"),"error");return}if(R!==y){a(n("settings-change-pw-mismatch"),"error");return}u.disabled=!0;const B=u.textContent;u.textContent=n("settings-change-pw-submitting"),a("","");try{const O=localStorage.getItem("mrpilot_token"),D=await fetch("/api/me/change_password",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+O},body:JSON.stringify({old_password:q,new_password:R})}),F=await D.json().catch(()=>({}));if(D.ok&&F.ok)a(n("settings-change-pw-success"),"success"),typeof showToast=="function"&&showToast(n("settings-change-pw-success"),"success"),d.value="",E.value="",k.value="",v&&(v.style.width="0%",v.className="cpw-strength-bar");else{const A=F.detail||"";let f=n("settings-change-pw-success");A==="wrong_old_password"?f=n("settings-change-pw-wrong-old"):A==="password_too_short"?f=n("settings-change-pw-too-short"):A==="password_too_weak"?f=n("settings-change-pw-too-weak"):f=A||"Error",a(f,"error")}}catch(O){console.error("change_password",O),a("Network error","error")}finally{u.disabled=!1,u.textContent=B}})}function i(){const _=window._userInfo||(typeof _userInfo<"u"?_userInfo:null),o=_&&_.username?_.username:"",v=g(o);let w=document.getElementById("cpw-forgot-overlay");w&&w.remove(),w=document.createElement("div"),w.id="cpw-forgot-overlay",w.className="cpw-forgot-overlay",w.innerHTML=`
            <div class="cpw-forgot-modal">
                <div class="cpw-forgot-head">
                    <div class="cpw-forgot-title">${b(n("cpw-forgot-title"))}</div>
                    <button class="cpw-forgot-close" id="cpw-forgot-close" aria-label="close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="cpw-forgot-body">
                    <p class="cpw-forgot-desc">${b(n("cpw-forgot-desc"))}</p>
                    <div class="cpw-forgot-email">${b(v)}</div>
                    <p class="cpw-forgot-tip">${b(n("cpw-forgot-tip"))}</p>
                    <div class="cpw-forgot-msg" id="cpw-forgot-msg"></div>
                </div>
                <div class="cpw-forgot-foot">
                    <button class="btn btn-ghost" id="cpw-forgot-cancel">${b(n("cpw-forgot-cancel"))}</button>
                    <button class="btn btn-primary" id="cpw-forgot-send">${b(n("cpw-forgot-send"))}</button>
                </div>
            </div>
        `,document.body.appendChild(w);const u=()=>w.remove();w.querySelector("#cpw-forgot-close").addEventListener("click",u),w.querySelector("#cpw-forgot-cancel").addEventListener("click",u),w.addEventListener("click",d=>{d.target===w&&u()}),w.querySelector("#cpw-forgot-send").addEventListener("click",async()=>{const d=w.querySelector("#cpw-forgot-send"),E=w.querySelector("#cpw-forgot-msg");d.disabled=!0;const k=d.textContent;d.textContent=n("cpw-forgot-sending");try{const q=await fetch("/api/auth/forgot_password",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:o})}),R=await q.json().catch(()=>({}));q.ok?(E.textContent=n("cpw-forgot-success"),E.className="cpw-forgot-msg success",d.style.display="none",w.querySelector("#cpw-forgot-cancel").textContent=n("cpw-forgot-close-btn")):(E.textContent=R.detail||n("cpw-forgot-fail"),E.className="cpw-forgot-msg error",d.disabled=!1,d.textContent=k)}catch{E.textContent=n("cpw-forgot-fail"),E.className="cpw-forgot-msg error",d.disabled=!1,d.textContent=k}})}function g(_){if(!_||!_.includes("@"))return _||"";const[o,v]=_.split("@");return o.length<=2?o+"****@"+v:o.slice(0,2)+"****@"+v}function b(_){return _==null?"":String(_).replace(/[&<>"']/g,o=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[o])}document.readyState==="complete"||document.readyState==="interactive"?s():document.addEventListener("DOMContentLoaded",s)})();(function(){let e=null,a=!1;async function n(){if(a)return;const i=localStorage.getItem("mrpilot_token");if(i){a=!0;try{const g=await fetch("/api/me",{headers:{Authorization:"Bearer "+i},cache:"no-store"});if(g.status===401){const b=await g.json().catch(()=>({})),_=b&&b.detail;let o="";if(typeof _=="string"?o=_:_&&typeof _=="object"&&(o=_.code||""),console.warn("[heartbeat] session revoked",o),localStorage.removeItem("mrpilot_token"),e&&(clearInterval(e),e=null),o==="auth.session_revoked")try{_showSessionRevokedModal()}catch{window.location.href="/"}else{const v=o==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";try{typeof showToast=="function"&&typeof t=="function"?showToast(t(v),"error"):alert("Session expired")}catch{}setTimeout(()=>{window.location.href="/"},1500)}}}catch{}finally{a=!1}}}function s(){e&&clearInterval(e),e=setInterval(n,15e3)}localStorage.getItem("mrpilot_token")&&s(),window.addEventListener("focus",n),document.addEventListener("visibilitychange",function(){document.hidden||n()}),window._sessionCheck=n})();async function Fe(){const e=document.getElementById("team-loading"),a=document.getElementById("team-list"),n=document.getElementById("team-empty"),s=document.getElementById("team-count");if(a){e&&(e.style.display=""),a.style.display="none",n&&(n.style.display="none");try{const i=await apiGet("/api/team/employees"),g=i&&i.employees||[];if(e&&(e.style.display="none"),s&&(s.textContent=(t("team-count")||"共 {n} 名员工").replace("{n}",g.length)),g.length===0){n&&(n.style.display="");return}a.style.display="",a.innerHTML=g.map(b=>{const _=b.last_login_at?new Date(b.last_login_at).toLocaleDateString():t("team-never-login")||"从未登录",o=b.is_active===!1?"team-status-off":"team-status-on",v=b.is_active===!1?t("team-status-disabled")||"已禁用":t("team-status-active")||"正常",w=b.email?`<span class="team-meta-sep">·</span><span>${escapeHtml(b.email)}</span>`:"";return`
            <div class="team-card" data-employee-id="${escapeHtml(b.id)}">
                <div class="team-card-main">
                    <div class="team-avatar">${escapeHtml((b.username||"?")[0].toUpperCase())}</div>
                    <div class="team-info">
                        <div class="team-name">${escapeHtml(b.username||"")}</div>
                        <div class="team-meta">
                            <span class="team-status-dot ${o}"></span>
                            <span>${escapeHtml(v)}</span>
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml(t("team-last-login")||"上次登录")}: ${escapeHtml(_)}</span>
                            ${w}
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml((t("team-assigned-clients")||"已分配 {n} 客户").replace("{n}",b.assigned_client_count||0))}</span>
                        </div>
                    </div>
                </div>
                <div class="team-card-actions">
                    <button class="btn btn-ghost btn-small" data-assign-clients="${escapeHtml(b.id)}" data-name="${escapeHtml(b.username||"")}">
                        ${escapeHtml(t("team-assign-clients")||"分配客户")}
                    </button>
                    <button class="btn btn-ghost btn-small" data-reset-pwd-employee="${escapeHtml(b.id)}" data-name="${escapeHtml(b.username||"")}" title="${escapeHtml(t("team-reset-pwd")||"重置密码")}">
                        ${escapeHtml(t("team-reset-pwd")||"重置密码")}
                    </button>
                    <button class="btn btn-ghost btn-small" data-toggle-employee="${escapeHtml(b.id)}" data-active="${b.is_active===!1?"false":"true"}">
                        ${escapeHtml(b.is_active===!1?t("team-enable")||"启用":t("team-disable")||"禁用")}
                    </button>
                    <button class="btn btn-ghost btn-small btn-danger-text" data-remove-employee="${escapeHtml(b.id)}" data-name="${escapeHtml(b.username||"")}">
                        ${escapeHtml(t("team-remove")||"移除")}
                    </button>
                </div>
            </div>`}).join("")}catch(i){console.error("loadTeamList failed:",i),e&&(e.textContent=t("team-load-failed")||"加载失败")}}}async function Mt(){document.querySelectorAll(".add-emp-overlay").forEach(s=>s.remove());const e=document.createElement("div");e.className="add-emp-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const s=document.getElementById("add-emp-username");s&&s.focus()},200);function a(){e.classList.remove("show"),setTimeout(()=>e.remove(),220)}e.querySelector(".add-emp-close").addEventListener("click",a),e.querySelector("#add-emp-cancel").addEventListener("click",a),e.addEventListener("click",s=>{s.target===e&&a()}),e.querySelector("#add-emp-submit").addEventListener("click",async()=>{const s=document.getElementById("add-emp-username"),i=document.getElementById("add-emp-email"),g=document.getElementById("add-emp-password"),b=document.getElementById("add-emp-msg"),_=document.getElementById("add-emp-submit"),o=(s.value||"").trim(),v=(i.value||"").trim(),w=g.value||"";if(b.textContent="",b.classList.remove("error"),!o||o.length<3){b.textContent=t("team-modal-err-username")||"用户名至少 3 位",b.classList.add("error");return}if(!/^[a-zA-Z0-9_.\-]+$/.test(o)){b.textContent=t("team-modal-err-username-fmt")||"只能用字母 / 数字 / 下划线 / 点 / 横线",b.classList.add("error");return}if(v&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)){b.textContent=t("msg-email-invalid")||"邮箱格式不对",b.classList.add("error");return}if(w.length<8){b.textContent=t("pwd-too-short")||"密码至少 8 位",b.classList.add("error");return}if(/^\d+$/.test(w)){b.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",b.classList.add("error");return}if(!(/[a-zA-Z]/.test(w)&&/\d/.test(w))){b.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",b.classList.add("error");return}_.disabled=!0,_.textContent=t("msg-saving")||"保存中...";try{const u={username:o,password:w};v&&(u.email=v);const d=await apiPost("/api/team/employees",u),E=d?await d.json().catch(()=>({})):{};if(d&&d.ok&&E&&E.ok){showToast(t("team-added")||"员工已添加","success"),a(),Fe();return}const k=E&&E.detail||"unknown",q={"team.username_exists":t("team-username-exists")||"用户名已被占用","team.email_exists":t("team-email-exists")||"邮箱已被占用","team.create_failed":t("team-create-failed")||"创建失败","team.only_owner_or_super":t("team-no-permission")||"无权限","team.no_tenant":t("team-no-tenant")||"请先升级账号","pwd.too_short":t("pwd-too-short")||"密码至少 8 位","pwd.too_weak_numeric":t("pwd-too-weak-numeric")||"不能是纯数字","pwd.too_weak_common":t("pwd-too-weak-common")||"这个密码太常见 · 请换一个","pwd.too_weak":t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};b.textContent=q[k]||(t("team-create-failed")||"创建失败")+" ("+k+")",b.classList.add("error")}catch{b.textContent=t("team-create-failed")||"创建失败",b.classList.add("error")}finally{_.disabled=!1,_.textContent=t("team-add")||"添加员工"}});function n(s){s.key==="Escape"&&(a(),document.removeEventListener("keydown",n))}document.addEventListener("keydown",n)}async function $t(e,a){try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}/active`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({is_active:!!a})})).ok){Fe();return}showToast(t("team-toggle-failed")||"操作失败","error")}catch{showToast(t("team-toggle-failed")||"操作失败","error")}}async function Ht(e,a){const s=(t("team-confirm-remove")||"确认移除员工「{name}」?他的所有识别记录会保留 · 但他将无法登录").replace("{name}",a).replace("{n}",a);if(await showConfirm(s,{danger:!0,okText:t("team-remove")}))try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){showToast(t("team-removed")||"已移除","success"),Fe();return}showToast(t("team-remove-failed")||"移除失败","error")}catch{showToast(t("team-remove-failed")||"移除失败","error")}}async function At(e,a){const s=(t("team-reset-pwd-confirm")||"给员工「{name}」发送改密链接?系统将通过员工的邮箱或 LINE 发送一个 15 分钟内有效的链接 · 员工自己点链接改密码 · 您看不到密码").replace("{name}",a).replace("{n}",a);if(await showConfirm(s,{okText:t("team-reset-link-send-btn")||"发送链接"}))try{const g=await fetch(`/api/team/employees/${encodeURIComponent(e)}/reset-password`,{method:"POST",headers:{Authorization:"Bearer "+token}}),b=await g.json().catch(()=>({}));if(g.status===400&&b.detail==="team.reset_no_channel"){showToast(t("team-reset-no-channel")||"员工尚未绑定邮箱或 LINE · 请先帮员工补充邮箱再重置","error");return}if(!g.ok){showToast(t("team-reset-pwd-fail")||"发送失败","error");return}if(b.channel==="line"||b.channel==="email"){const _=t("team-reset-link-sent")||"改密链接已通过 {ch} 发送给员工 · 链接 15 分钟内有效",o=b.channel==="line"?"LINE":t("team-reset-via-email")||"邮箱";showToast(_.replace("{ch}",o),"success");return}showToast(t("team-reset-pwd-fail")||"发送失败","error")}catch{showToast(t("team-reset-pwd-fail")||"发送失败","error")}}document.addEventListener("click",e=>{if(e.target.closest("#btn-add-employee")){e.preventDefault(),Mt();return}const a=e.target.closest("[data-toggle-employee]");if(a){e.preventDefault(),$t(a.dataset.toggleEmployee,a.dataset.active==="false");return}const n=e.target.closest("[data-remove-employee]");if(n){e.preventDefault(),Ht(n.dataset.removeEmployee,n.dataset.name||"");return}const s=e.target.closest("[data-reset-pwd-employee]");if(s){e.preventDefault(),At(s.dataset.resetPwdEmployee,s.dataset.name||"");return}const i=e.target.closest("[data-assign-clients]");if(i){e.preventDefault(),typeof window.openAssignClientsModal=="function"&&window.openAssignClientsModal(i.dataset.assignClients,i.dataset.name||"");return}});window.loadTeamList=Fe;function jt(e){document.querySelectorAll(".auto-nav-item").forEach(a=>{a.classList.toggle("active",a.dataset.autoTab===e)}),document.querySelectorAll(".auto-panel").forEach(a=>{a.classList.toggle("active",a.dataset.autoPanel===e)}),e==="email"&&typeof window._loadEmailIngestPanel=="function"?(window._loadEmailIngestPanel(),typeof window._startEmailLogAutoRefresh=="function"&&window._startEmailLogAutoRefresh()):typeof window._stopEmailLogAutoRefresh=="function"&&window._stopEmailLogAutoRefresh(),e==="bank"&&typeof window._loadBankReconPanel=="function"&&window._loadBankReconPanel(),e==="linebot"&&typeof window._loadLineBotPanel=="function"&&window._loadLineBotPanel(),e==="alert"&&typeof window._loadNotificationsPanel=="function"&&window._loadNotificationsPanel(),e==="folder"&&typeof window._loadFolderWatcherPanel=="function"&&window._loadFolderWatcherPanel()}window.switchAutomationTab=jt;typeof console<"u"&&typeof console.info=="function"&&console.info("[pearnly] vite bundle loaded · dashboard + billing + test-center + workspace-switcher + recon-center + assign-clients + access-log + notifications + recon-batch + welcome-wizard + archive-settings");
//# sourceMappingURL=main.js.map
