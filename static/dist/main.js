const Ct=`
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

`,St=`        <!-- ── 销项税对账面板(v118.32.0 · 屏 A) ── -->
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


`;(function(){const e=document.getElementById("page-reconcile");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=Ct+St,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");a[n][o]&&(s.textContent=a[n][o])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const o=s.getAttribute("data-i18n-placeholder");a[n][o]&&(s.placeholder=a[n][o])}))}catch{}}})();(function(){const e=document.getElementById("page-integrations");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");a[n][o]&&(s.textContent=a[n][o])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const o=s.getAttribute("data-i18n-placeholder");a[n][o]&&(s.placeholder=a[n][o])}))}catch{}}})();(function(){const e=document.getElementById("page-settings");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");a[n][o]&&(s.textContent=a[n][o])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const o=s.getAttribute("data-i18n-placeholder");a[n][o]&&(s.placeholder=a[n][o])}))}catch{}}})();const Tt=`
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
                                <button class="btn btn-sm btn-secondary bank-filter-btn active" data-bank-filter="all" data-i18n="bank-filter-all">全部</button>
                                <button class="btn btn-sm btn-secondary bank-filter-btn" data-bank-filter="matched" data-i18n="bank-filter-matched">已匹配</button>
                                <button class="btn btn-sm btn-secondary bank-filter-btn" data-bank-filter="suggested" data-i18n="bank-filter-suggested">疑似</button>
                                <button class="btn btn-sm btn-secondary bank-filter-btn" data-bank-filter="unmatched" data-i18n="bank-filter-unmatched">未匹配</button>
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

`,Mt=`                    <!-- Tab: 邮箱抓取 (v0.17 · M6 · v93 在 Vultr 复活) -->
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
`;(function(){const e=document.getElementById("page-automation");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=Tt+Mt,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");a[n][o]&&(s.textContent=a[n][o])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const o=s.getAttribute("data-i18n-placeholder");a[n][o]&&(s.placeholder=a[n][o])}))}catch{}}})();(function(){const e={"page-integration":`
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
`},n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;Object.keys(e).forEach(s=>{const o=document.getElementById(s);!o||o.dataset.wbInjected==="1"||(o.innerHTML=e[s],o.dataset.wbInjected="1",a&&a[n]&&o.querySelectorAll("[data-i18n]").forEach(m=>{const r=m.getAttribute("data-i18n");a[n][r]&&(m.textContent=a[n][r])}))})})();(function(){const e=document.getElementById("page-dashboard");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
        <div class="page-head-clean">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 12l9-9 9 9"/><path d="M5 10v10h14V10"/>
                </svg>
            </div>
            <div class="page-head-text">
                <div class="page-head-title" data-i18n="dash-title">首页</div>
                <div class="page-head-sub" id="dash-subtitle" data-i18n="dash-sub">今日工作概况</div>
            </div>
        </div>
        <div class="dash-kpi-grid">
            <div class="dash-kpi">
                <div class="dash-kpi-label"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 2h7l3 3v9H3z"/><path d="M10 2v3h3"/></svg><span data-i18n="dash-kpi-month-invoices">本月发票</span></div>
                <div class="dash-kpi-val" id="dash-kpi-invoices">—</div>
                <div class="dash-kpi-sub" data-i18n="dash-kpi-month-invoices-sub">张已识别</div>
            </div>
            <div class="dash-kpi">
                <div class="dash-kpi-label"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="8" cy="8" r="6"/><path d="M8 4v4l2.5 2.5"/></svg><span data-i18n="dash-kpi-pending">待处理</span></div>
                <div class="dash-kpi-val dash-amber" id="dash-kpi-pending">—</div>
                <div class="dash-kpi-sub" data-i18n="dash-kpi-pending-sub">条待审核</div>
            </div>
            <div class="dash-kpi">
                <div class="dash-kpi-label"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M8 1l7 13H1z"/><path d="M8 6v4"/><circle cx="8" cy="12" r="0.6" fill="currentColor"/></svg><span data-i18n="dash-kpi-exceptions">异常</span></div>
                <div class="dash-kpi-val dash-red" id="dash-kpi-exceptions">—</div>
                <div class="dash-kpi-sub" data-i18n="dash-kpi-exceptions-sub">需立即处理</div>
            </div>
            <div class="dash-kpi">
                <div class="dash-kpi-label"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="2" y="3" width="12" height="10" rx="1.5"/><path d="M2 7h12"/></svg><span data-i18n="dash-kpi-plan">配额</span></div>
                <div class="dash-kpi-val" id="dash-kpi-plan">—</div>
                <div class="dash-kpi-sub" id="dash-kpi-plan-sub" data-i18n="dash-kpi-plan-sub">本月用量</div>
            </div>
        </div>
        <!-- v118.35.0.9 · credits 第二排 KPI · 账户余额 + 本月用量(分级显示) -->
        <div class="dash-kpi-grid dash-kpi-grid-credits" id="dash-kpi-credits" style="grid-template-columns: repeat(2, 1fr);">
            <div class="dash-kpi" id="dash-kpi-balance-card" style="display:none;">
                <div class="dash-kpi-label"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="2" y="4" width="12" height="9" rx="1.5"/><circle cx="11" cy="8.5" r="1.5"/></svg><span data-i18n="dash-kpi-balance">账户余额</span></div>
                <div class="dash-kpi-val" id="dash-kpi-balance">—</div>
                <div class="dash-kpi-sub" id="dash-kpi-balance-sub">&nbsp;</div>
            </div>
            <div class="dash-kpi" id="dash-kpi-usage-card">
                <div class="dash-kpi-label"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M2 13l4-5 3 3 5-7"/><circle cx="14" cy="4" r="1.2"/></svg><span data-i18n="dash-kpi-usage">本月用量</span></div>
                <div class="dash-kpi-val" id="dash-kpi-usage">—</div>
                <div class="dash-kpi-sub" id="dash-kpi-usage-sub">&nbsp;</div>
            </div>
        </div>
        <div class="dash-grid2">
            <div class="card">
                <div class="section-head">
                    <div class="section-title" data-i18n="dash-quick-title">快速操作</div>
                    <div class="section-sub" data-i18n="dash-quick-sub">3 步进入主流程</div>
                </div>
                <div class="dash-quick-list">
                    <button class="btn dash-quick-btn" onclick="window.routeTo && window.routeTo('ocr')">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M8 2v9"/><path d="M5 6l3-3 3 3"/><path d="M2 13h12"/></svg>
                        <span data-i18n="dash-quick-upload">上传发票</span>
                    </button>
                    <button class="btn dash-quick-btn" onclick="window.routeTo && window.routeTo('clients')">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="2" y="3" width="12" height="11" rx="1"/><path d="M5 6h6M5 9h6M5 12h3"/></svg>
                        <span data-i18n="dash-quick-clients">查看客户</span>
                    </button>
                    <button class="btn dash-quick-btn" onclick="window.routeTo && window.routeTo('reconcile')">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 4h10M3 8h10M3 12h7"/></svg>
                        <span data-i18n="dash-quick-reconcile">开始对账</span>
                    </button>
                    <button class="btn dash-quick-btn dash-quick-btn-warn" onclick="window.routeTo && window.routeTo('exceptions')">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M8 1l7 13H1z"/><path d="M8 6v4"/></svg>
                        <span data-i18n="dash-quick-exceptions">处理异常</span>
                        <span class="dash-quick-badge" id="dash-quick-exc-badge" style="display:none">0</span>
                    </button>
                </div>
            </div>
            <div class="card">
                <div class="section-head">
                    <div class="section-title" data-i18n="dash-recent-title">最近动态</div>
                    <div class="section-sub" data-i18n="dash-recent-sub">最近 5 条识别</div>
                </div>
                <div id="dash-recent-list" class="dash-recent-list">
                    <div class="dash-recent-empty" data-i18n="dash-recent-empty">还没有识别记录 · 去上传第一张吧</div>
                </div>
            </div>
        </div>
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");a[n][o]&&(s.textContent=a[n][o])})}catch{}}})();function ze(){const e=document.getElementById("results-card");if(_results.length===0){e.classList.remove("show");return}e.classList.add("show");let n=0;_results.forEach(r=>{const k=parseFloat(r.merged_fields.total_amount);isNaN(k)||(n+=k)}),_selectedFiles&&_selectedFiles.length||_results.length;const a=_results.length,s=n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2});document.getElementById("results-head-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-value">${a}</span>
            <span class="rh-stat-label">${t("stats-invoices")}</span>
        </div>
        <div class="rh-stat">
            <span class="rh-stat-label">${t("stats-total")}</span>
            <span class="rh-stat-value">฿ ${s}</span>
        </div>
    `;let o=_results.map((r,k)=>({...r,_idx:k}));if(_searchKeyword){const r=_searchKeyword.toLowerCase();o=o.filter(k=>(k.filename||"").toLowerCase().includes(r)||(k.merged_fields.invoice_number||"").toLowerCase().includes(r))}_sortKey&&o.sort((r,k)=>{let i,f;return _sortKey==="filename"?(i=r.filename,f=k.filename):_sortKey==="invoice_no"?(i=r.merged_fields.invoice_number,f=k.merged_fields.invoice_number):_sortKey==="invoice_date"?(i=r.merged_fields.date,f=k.merged_fields.date):_sortKey==="total"?(i=parseFloat(r.merged_fields.total_amount)||0,f=parseFloat(k.merged_fields.total_amount)||0):_sortKey==="confidence"?(i=r.confidence,f=k.confidence):(i="",f=""),i<f?_sortDir==="asc"?-1:1:i>f?_sortDir==="asc"?1:-1:0});const m=document.getElementById("results-tbody");m.innerHTML=o.map((r,k)=>{const i=r.merged_fields,f=`<span class="empty-cell">${t("empty-val")}</span>`,u="conf-tip-"+(r.confidence||"low"),c="conf-"+(r.confidence||"low"),v=t(u),E=t(c);return`
            <tr data-idx="${r._idx}">
                <td class="num">${k+1}</td>
                <td class="fname" title="${escapeHtml(r.filename)}">${escapeHtml(r.filename)}</td>
                <td class="inv">${i.invoice_number?escapeHtml(i.invoice_number):f}</td>
                <td class="date">${i.date?escapeHtml(i.date):f}</td>
                <td class="amount">${i.total_amount?Number(i.total_amount).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}):f}</td>
                <td><span class="conf-badge ${r.confidence}" data-tip="${escapeHtml(v)}">${E}</span></td>
            </tr>
        `}).join(""),document.querySelectorAll("#results-table th").forEach(r=>{r.classList.remove("sort-asc","sort-desc"),r.dataset.sort===_sortKey&&r.classList.add("sort-"+_sortDir)}),m.querySelectorAll("tr").forEach(r=>{r.addEventListener("click",()=>{const k=parseInt(r.dataset.idx,10);rt(k)})})}document.querySelectorAll("#results-table th").forEach(e=>{e.classList.contains("no-sort")||e.addEventListener("click",()=>{const n=e.dataset.sort;_sortKey===n?_sortDir=_sortDir==="asc"?"desc":"asc":(_sortKey=n,_sortDir="asc"),ze()})});let tt=null;document.getElementById("search-input").addEventListener("input",e=>{const n=e.target.value;document.getElementById("search-clear").style.display=n?"":"none",clearTimeout(tt),tt=setTimeout(()=>{_searchKeyword=n.trim(),ze(),it()},200)});document.getElementById("search-clear").addEventListener("click",()=>{const e=document.getElementById("search-input");e.value="",_searchKeyword="",document.getElementById("search-clear").style.display="none",ze(),it(),e.focus()});function it(){const e=document.getElementById("search-matches");if(!e)return;if(!_searchKeyword){e.textContent="";return}const n=_searchKeyword.toLowerCase();let a=0;for(const s of _results)[s.filename,s.merged_fields?.invoice_number,s.merged_fields?.seller_name,s.merged_fields?.buyer_name].filter(Boolean).join(" ").toLowerCase().includes(n)&&a++;e.textContent=t("search-matches",{n:a})}function rt(e){_drawerIdx=e;const n=_results[e];if(!n)return;document.getElementById("drawer-title").textContent=n.filename;const a=n.engine==="cache"||n.from_cache,s=a?t("badge-cached-hint"):`${(n.elapsed_ms/1e3).toFixed(1)}s`;document.getElementById("drawer-sub").innerHTML=`
        <span>${n.page_count} ${t("pages-unit")} · ${escapeHtml(s)}</span>
        ${a?`<span class="engine-badge cached">${escapeHtml(t("badge-cached"))}</span>`:""}
        <span class="drawer-edit-count" id="drawer-edit-count-sub"></span>
    `,updateDrawerEditCount();const o=_userInfo&&_userInfo.can_edit_fields,m=_userInfo&&_userInfo.can_verify_tax,r=n.merged_fields,k=document.getElementById("drawer-body"),i=o?"":`
        <div class="drawer-readonly-banner">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="9" width="12" height="9" rx="1"/><path d="M7 9V6a3 3 0 016 0v3"/></svg>
            <span>${t("readonly-banner")}</span>
        </div>
    `,f=m?"":`<span class="tax-badge unverified" data-tip="${escapeHtml(t("tax-tip-unverified"))}">${t("tax-unverified")}</span>`;if(k.innerHTML=`
        ${i}

        <!-- v118.19 · 决策区(C 位) · 会计每张发票真正要做的两个决策 -->
        <div class="drawer-decision-zone">
            <div class="drawer-decision-title">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="3.5" cy="3" r="1.4"/>
                    <circle cx="3.5" cy="13" r="1.4"/>
                    <circle cx="12.5" cy="8" r="1.4"/>
                    <path d="M3.5 4.4v7.2"/>
                    <path d="M3.5 8h7.6"/>
                </svg>
                <span>${escapeHtml(t("drawer-decision-title"))}</span>
            </div>
            <div class="drawer-decision-grid">
                <!-- 归属客户(左) -->
                <div class="drawer-client-card" data-field-wrap="client_id">
                    <div class="drawer-client-head">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M11 14v-1.2a2.4 2.4 0 00-2.4-2.4H4a2.4 2.4 0 00-2.4 2.4V14"/>
                            <circle cx="6.4" cy="5.2" r="2.4"/>
                        </svg>
                        <span>${escapeHtml(t("drawer-client-label"))}</span>
                    </div>
                    <div class="drawer-client-body">
                        <select class="drawer-client-select" id="drawer-client-select" ${o?"":"disabled"}>
                            <option value="">${escapeHtml(t("drawer-client-none"))}</option>
                        </select>
                        <button class="drawer-client-add" id="drawer-client-add" type="button" title="${escapeHtml(t("client-new"))}">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M7 2v10M2 7h10"/></svg>
                        </button>
                    </div>
                </div>

                <!-- 记账科目(右) · 学过的发亮 -->
                <div class="drawer-suggest-card" data-field-wrap="category_tag">
                    <div class="drawer-suggest-head">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M2 4a1 1 0 011-1h4l2 2h5a1 1 0 011 1v6a1 1 0 01-1 1H3a1 1 0 01-1-1V4z"/>
                        </svg>
                        <span>${escapeHtml(t("drawer-suggest-category"))}</span>
                        ${r.category||n.category_tag?`<span class="drawer-suggest-learned" id="drawer-cat-learned-tag" title="${escapeHtml(t("drawer-suggest-learned-tip"))}">${escapeHtml(t("drawer-suggest-learned"))}</span>`:`<span class="drawer-suggest-empty">${escapeHtml(t("drawer-suggest-empty"))}</span>`}
                    </div>
                    <div class="drawer-suggest-body">
                        <input type="text" class="drawer-suggest-input" id="drawer-cat-input" data-field="category_tag"
                               list="drawer-cat-datalist"
                               placeholder="${escapeHtml(t("drawer-suggest-placeholder"))}"
                               value="${escapeHtml((n.edits&&n.edits.category_tag!==void 0?n.edits.category_tag:r.category||n.category_tag)||"")}"
                               ${o?"":"readonly"}>
                        <datalist id="drawer-cat-datalist"></datalist>
                    </div>
                </div>
            </div>
            <div class="drawer-decision-hint">${escapeHtml(t("drawer-suggest-hint"))}</div>
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 2h8l3 3v13H5z"/><path d="M13 2v3h3"/><path d="M8 10h6M8 13h6"/></svg>
                ${t("drawer-sec-basic")}
            </div>
            ${ye("invoice_number","drawer-lbl-invoice",r.invoice_number,"input",o)}
            ${ye("date","drawer-lbl-date",r.date,"input",o)}
            ${r.date_raw&&r.date_raw!==r.date?`<div class="date-raw-hint" title="${escapeHtml(t("drawer-date-raw-tip"))}">${escapeHtml(t("drawer-date-raw-label"))}: ${escapeHtml(r.date_raw)}</div>`:""}
            ${ye("subtotal","drawer-lbl-subtotal",r.subtotal,"input",o)}
            ${ye("vat","drawer-lbl-vat",r.vat,"input",o)}
            ${ye("total_amount","drawer-lbl-total",r.total_amount,"input",o)}
            ${r.wht_amount||r.wht_rate?`
                ${ye("wht_amount","drawer-lbl-wht-amount",r.wht_amount,"input",o,$t(r.wht_rate))}
            `:""}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 18V8h14v10M3 8l2-4h10l2 4M7 12h2M11 12h2"/></svg>
                ${t("drawer-sec-seller")}
            </div>
            ${ye("seller_name","drawer-lbl-name",r.seller_name,"input",o)}
            ${ye("seller_tax","drawer-lbl-tax",r.seller_tax,"input",o,f,nt("seller"))}
            ${ye("seller_addr","drawer-lbl-addr",r.seller_addr,"textarea",o)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="10" cy="6" r="3"/><path d="M3 18c0-3.9 3.1-7 7-7s7 3.1 7 7"/></svg>
                ${t("drawer-sec-buyer")}
            </div>
            ${ye("buyer_name","drawer-lbl-name",r.buyer_name,"input",o)}
            ${ye("buyer_tax","drawer-lbl-tax",r.buyer_tax,"input",o,f,nt("buyer"))}
            ${ye("buyer_addr","drawer-lbl-addr",r.buyer_addr,"textarea",o)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 7l7-4 7 4v7l-7 4-7-4z"/><path d="M3 7l7 4 7-4M10 11v8"/></svg>
                ${t("drawer-sec-items")}
            </div>
            ${r.items&&r.items.length>0?Ht(r.items):`<div class="drawer-items-empty">${t("drawer-items-empty")}</div>`}
        </div>

        <div class="drawer-section">
            ${ye("notes","drawer-lbl-notes",r.notes,"textarea",o)}
        </div>

        <details class="raw-text">
            <summary>${t("raw-text")}</summary>
            <pre>${escapeHtml(n.pages.map(u=>`--- Page ${u.page||u.page_number||"?"} ---
${u.raw_text||u.text||""}`).join(`

`))}</pre>
        </details>
    `,o?k.querySelectorAll("[data-field]").forEach(u=>{u.addEventListener("input",onFieldEdit)}):k.querySelectorAll("[data-field]").forEach(u=>{u.setAttribute("readonly","readonly")}),document.getElementById("drawer-mask").classList.add("show"),document.getElementById("drawer").classList.add("show"),injectOcrPushButton(),typeof window.bindDrawerClient=="function"){const u=n._historyId||n.history_id||null;window.bindDrawerClient(u,n.client_id||null)}typeof window.fillCategoryDatalist=="function"&&window.fillCategoryDatalist(),setTimeout(()=>{const u=document.getElementById("drawer-cat-input");u&&!u.value&&!u.readOnly&&u.focus()},80)}function $t(e){return e?`<span class="wht-badge">${escapeHtml(e)}%</span>`:""}function ye(e,n,a,s,o,m,r){const k=_results[_drawerIdx],i=k&&k.edits[e]!==void 0?k.edits[e]:a,f=k&&k.edits[e]!==void 0&&k.edits[e]!==a,u=escapeHtml(i??""),c=o?"":"readonly",v=s==="textarea"?`<textarea data-field="${e}" rows="2">${u}</textarea>`:`<input type="text" data-field="${e}" value="${u}">`;return`
        <div class="drawer-field ${f?"edited":""} ${c}" data-field-wrap="${e}">
            <label class="drawer-field-label">
                <span class="drawer-field-edited-dot"></span>
                ${t(n)}
                ${m||""}
                ${r?`<span class="drawer-field-actions">${r}</span>`:""}
            </label>
            ${v}
        </div>
    `}function nt(e){return _userInfo&&_userInfo.can_verify_tax?`
        <button class="rd-btn rd-btn-verify" data-rd-action="verify" data-rd-side="${e}" type="button">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 8l3 3 7-7"/></svg>
            ${t("rd-btn-verify")}
        </button>
        <button class="rd-btn rd-btn-sync" data-rd-action="sync" data-rd-side="${e}" type="button">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 8a5 5 0 019-3l1.5 1.5M13 8a5 5 0 01-9 3L2.5 9.5M13 3v3h-3M3 13v-3h3"/></svg>
            ${t("rd-btn-sync")}
        </button>
        <span class="rd-status" data-rd-status="${e}"></span>
    `:`<button class="rd-btn-locked" data-upgrade="plus" type="button" title="${escapeHtml(t("rd-tip-upgrade"))}">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="7" width="10" height="7" rx="1"/><path d="M5 7V5a3 3 0 016 0v2"/></svg>
        </button>`}function Ht(e){return`
        <div class="drawer-items-header">
            <div>${t("drawer-item-name")}</div>
            <div>${t("drawer-item-qty")}</div>
            <div>${t("drawer-item-price")}</div>
            <div>${t("drawer-item-sub")}</div>
        </div>
        ${e.map(n=>`
            <div class="drawer-item-row">
                <div>${escapeHtml(n.name||"")}</div>
                <div>${escapeHtml(n.qty||n.quantity||"")}</div>
                <div>${escapeHtml(n.price||n.unit_price||"")}</div>
                <div>${escapeHtml(n.subtotal||n.total||"")}</div>
            </div>
        `).join("")}
    `}function At(){document.getElementById("drawer-mask").classList.remove("show"),document.getElementById("drawer").classList.remove("show");const e=document.getElementById("drawer-history-save");e&&e.remove();const n=document.getElementById("drawer-ocr-push");n&&n.remove();const a=document.getElementById("drawer-ocr-push-btn");a&&a.remove(),_drawerIdx=-1}window.renderResults=ze;window.openDrawer=rt;window.closeDrawer=At;function jt(){const e=_results[_drawerIdx];if(!e||e._historyMode||!_userInfo||!_userInfo.can_push_erp||!e._historyId&&!e.history_id)return;const n=e._historyId||e.history_id,a=document.querySelector(".drawer-header");if(!a||document.getElementById("drawer-ocr-push-btn"))return;const s=(window._erpEndpoints||_erpEndpoints||[]).filter(function(k){return k&&k.enabled!==!1});if(s.length===0)return;const o=document.createElement("button");o.id="drawer-ocr-push-btn",o.className="drawer-push-btn";let m;if(s.length===1){const k=s[0].name||s[0].adapter||"ERP";m=t("btn-push-to-name",{name:k}),o.title=m}else m=t("btn-push-erp")+" ▾",o.title=t("btn-push-erp-pick-tip");o.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 8h9M8 5l3 3-3 3"/>
            <rect x="11" y="3" width="3" height="10" rx="1"/>
        </svg>
        <span>${escapeHtml(m)}</span>
    `,o.addEventListener("click",function(k){k.preventDefault(),k.stopPropagation(),s.length===1?lt(n,s[0].id):Pt(o,n,s)});const r=a.querySelector(".drawer-diagnose");r?a.insertBefore(o,r):a.appendChild(o)}function Pt(e,n,a){document.querySelectorAll(".drawer-push-picker").forEach(i=>i.remove());const s=e.getBoundingClientRect(),o=document.createElement("div");o.className="drawer-push-picker history-popover",o.style.position="fixed",o.style.top=s.bottom+6+"px",o.style.left=Math.max(8,s.right-240)+"px",o.style.minWidth="220px",o.style.zIndex="12000";const m=a.map(function(i){const f=escapeHtml(i.name||i.adapter||"ERP"),u=escapeHtml((i.adapter||"").toLowerCase()),v=i.is_default?'<span style="font-size:10px;color:#0a7a2c;background:#d6f5e0;padding:1px 6px;border-radius:999px;margin-left:6px;">'+escapeHtml(t("ep-default"))+"</span>":"";return'<button type="button" data-ep-id="'+escapeHtml(i.id)+'" style="display:flex;align-items:center;justify-content:space-between;width:100%;text-align:left;"><span><span style="color:#5d5d57;font-size:11px;margin-right:6px;">'+u+"</span>"+f+v+"</span></button>"}).join("");o.innerHTML=m,document.body.appendChild(o);const r=()=>{o.remove(),document.removeEventListener("click",k,!0)},k=i=>{!o.contains(i.target)&&i.target!==e&&!e.contains(i.target)&&r()};setTimeout(()=>document.addEventListener("click",k,!0),0),o.addEventListener("click",i=>{const f=i.target.closest("[data-ep-id]");if(!f)return;const u=f.getAttribute("data-ep-id");r(),lt(n,u)})}async function lt(e,n){const a=document.getElementById("drawer-ocr-push-btn");a&&(a.disabled=!0);try{const s={history_id:e};n&&(s.endpoint_id=n);const o=await fetch("/api/erp/push",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(s)}),m=await o.json();if(!o.ok){const r=m&&m.detail?m.detail:"err.unknown";r==="erp.no_default_endpoint"?showToast(t("erp-push-no-endpoint"),"warn"):r==="erp.endpoint_disabled"?(showToast(t("erp-push-disabled-tip")||t("card-disabled-tip")||"Endpoint disabled","warn"),typeof window._refreshErpEndpointsCache=="function"&&window._refreshErpEndpointsCache()):showToast(t("erp-push-fail",{err:r}),"fail");return}m.ok?showToast(t("erp-push-ok",{name:m.endpoint_name||""})):showToast(t("erp-push-fail",{err:m.error_msg||"unknown"}),"fail")}catch(s){showToast(t("erp-push-fail",{err:s.message}),"fail")}finally{a&&(a.disabled=!1)}}window.injectOcrPushButton=jt;function Ie(e,n){try{return typeof window.t=="function"?window.t(e):n}catch{return n}}function Te(e){if(e==null||isNaN(e))return"—";try{return String(e).replace(/\B(?=(\d{3})+(?!\d))/g,",")}catch{return String(e)}}function Dt(e){if(!e)return"";try{const n=new Date(e).getTime();if(!n)return"";const a=Math.floor((Date.now()-n)/1e3);return a<60?Ie("time-just-now","刚刚"):a<3600?Math.floor(a/60)+Ie("time-min-ago-suffix"," 分钟前"):a<86400?Math.floor(a/3600)+Ie("time-hour-ago-suffix"," 小时前"):Math.floor(a/86400)+Ie("time-day-ago-suffix"," 天前")}catch{return""}}async function Ke(){ct();const e=document.getElementById("dash-kpi-invoices"),n=document.getElementById("dash-kpi-pending"),a=document.getElementById("dash-kpi-exceptions"),s=document.getElementById("dash-kpi-plan"),o=document.getElementById("dash-kpi-plan-sub"),m=document.getElementById("dash-recent-list"),r=document.getElementById("dash-quick-exc-badge");try{const k={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},[i,f,u]=await Promise.all([fetch("/api/me/tenant-usage",{headers:k}).then(D=>D.ok?D.json():null).catch(()=>null),fetch("/api/history?limit=20",{headers:k}).then(D=>D.ok?D.json():null).catch(()=>null),fetch("/api/exceptions/stats?status=pending",{headers:k}).then(D=>D.ok?D.json():null).catch(()=>null)]),c=i&&i.ocr_this_month||0;let v=0;const E=f&&(f.items||f.history||f)||[],x=Array.isArray(E)?E:[];x.forEach(D=>{(D.status==="pending"||D.status==="reviewing")&&v++});const R=u&&(u.total||u.count||u.pending||0)||0;if(e&&(e.textContent=Te(c)),n&&(n.textContent=Te(v)),a&&(a.textContent=Te(R)),r&&(R>0?(r.style.display="",r.textContent=R):r.style.display="none"),s&&i){const D=i.ocr_this_month||0,w=i.quota||0;s.textContent=Te(D),o&&(o.textContent=w?D+" / "+Te(w)+" 张":Ie("dash-kpi-plan-sub","本月用量"))}if(m)if(x.length===0)m.innerHTML='<div class="dash-recent-empty">'+Ie("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>";else{const D=x.slice(0,5).map(w=>{const B=(w.invoice_no||w.filename||w.id||"").toString(),z=(w.supplier_name||w.buyer_name||w.client_name||w.notes||"").toString(),q=Dt(w.created_at||w.upload_time||w.date),F=A=>String(A).replace(/[&<>"']/g,g=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[g]);return'<div class="dash-recent-row"><span class="dash-recent-key" title="'+F(B)+'">'+F(B)+'</span><span class="dash-recent-mid" title="'+F(z)+'">'+F(z)+'</span><span class="dash-recent-time">'+F(q)+"</span></div>"}).join("");m.innerHTML=D}}catch{m&&(m.innerHTML='<div class="dash-recent-empty">'+Ie("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>")}}window.loadDashboard=Ke;async function ct(){const e=document.getElementById("dash-kpi-balance-card"),n=document.getElementById("dash-kpi-usage-card"),a=document.getElementById("dash-kpi-balance"),s=document.getElementById("dash-kpi-balance-sub"),o=document.getElementById("dash-kpi-usage"),m=document.getElementById("dash-kpi-usage-sub");if(!(!e||!n))try{const r={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},k=await fetch("/api/me/credits",{headers:r,cache:"no-store"});if(!k.ok){e.style.display="none",o&&(o.textContent="—"),m&&(m.textContent="");return}const i=await k.json(),f=!!i.is_owner,u=!!i.is_billing_exempt;if(!f)e.style.display="none";else if(e.style.display="",u)a&&(a.textContent="∞",a.className="dash-kpi-val dash-green"),s&&(s.textContent=typeof window.t=="function"?window.t("dash-kpi-balance-exempt"):"Billing exempt");else{const v=typeof i.balance_thb=="number"?i.balance_thb:0;if(a&&(a.textContent="฿"+v.toFixed(2),a.className=v<50?"dash-kpi-val dash-red":"dash-kpi-val"),s){const E=typeof window.t=="function"?window.t("dash-kpi-balance-topup"):"Top up →",x=v<50?"#dc2626":"#6b7280",R=D=>typeof window.escapeHtml=="function"?window.escapeHtml(D):String(D).replace(/[&<>"']/g,w=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[w]);s.innerHTML='<a href="#" id="kpi-balance-topup-link" style="color:'+x+';text-decoration:underline;cursor:pointer;" onclick="event.preventDefault();window._openTopupModal&&window._openTopupModal();return false;">'+R(E)+"</a>"}}const c=typeof i.pages_this_month=="number"?i.pages_this_month:typeof i.my_invoice_count=="number"?i.my_invoice_count:0;if(n.style.display="",o&&(o.textContent=String(c)),m){const v=c>=200?"dash-kpi-usage-sub-high":"dash-kpi-usage-sub-low",E=typeof window.t=="function"?window.t(v,{used:c}):c+" pages";m.textContent=E}}catch(r){console.warn("[credits] loadCreditsCard failed:",r),e.style.display="none",o&&(o.textContent="—")}}window.loadCreditsCard=ct;document.addEventListener("DOMContentLoaded",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&setTimeout(Ke,500)});typeof window.subscribeI18n=="function"&&window.subscribeI18n("dashboard",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&Ke()});function he(e){return(typeof window.t=="function"?window.t(e):null)||e}function We(){return localStorage.getItem("mrpilot_token")||""}function me(e){return document.getElementById(e)}var Re=null,$e=null;function dt(){$e||($e=setInterval(function(){if(!document.hidden){var e=We();e&&(window._userInfo&&window._userInfo.is_billing_exempt||fetch("/api/me/credits",{headers:{Authorization:"Bearer "+e},cache:"no-store"}).then(function(n){return n.ok?n.json():null}).then(function(n){if(n){var a=n.balance_thb!=null?Number(n.balance_thb):0;Re!==null&&a>Re&&(window.showToast&&window.showToast(he("credits-updated"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard(),typeof window._refreshBalanceAlerts=="function"&&window._refreshBalanceAlerts()),Re=a}}).catch(function(){}))}},3e4))}function qt(){$e&&(clearInterval($e),$e=null),Re=null}window._startCreditsPoll=dt;window._stopCreditsPoll=qt;dt();var Xe=null,Ze=0;function Rt(){if(!me("topup-v2-ov")){var e=document.createElement("div");e.id="topup-v2-ov",e.className="topup-v2-ov",e.style.cssText="display:none;position:fixed;inset:0;background:rgba(15,23,42,.5);z-index:9500;align-items:center;justify-content:center;padding:16px",e.innerHTML=['<div class="topup-v2-box">','  <div class="topup-v2-head">','    <div class="topup-v2-title" id="tv2-title"></div>','    <button class="topup-v2-close" id="tv2-close" aria-label="close">','      <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="4" y1="4" x2="16" y2="16"/><line x1="16" y1="4" x2="4" y2="16"/></svg>',"    </button>","  </div>",'  <div class="topup-v2-steps">','    <div class="topup-v2-step" id="tv2-d1"><span class="topup-v2-dot">1</span><span class="topup-v2-slabel" id="tv2-sl1"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d2"><span class="topup-v2-dot">2</span><span class="topup-v2-slabel" id="tv2-sl2"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d3"><span class="topup-v2-dot">3</span><span class="topup-v2-slabel" id="tv2-sl3"></span></div>',"  </div>",'  <div class="topup-v2-body">','    <div id="tv2-s1">','      <label class="topup-v2-label" id="tv2-al"></label>','      <div class="topup-v2-qamts">','        <button class="topup-v2-qamt" data-val="100">฿100</button>','        <button class="topup-v2-qamt" data-val="500">฿500</button>','        <button class="topup-v2-qamt" data-val="1000">฿1,000</button>','        <button class="topup-v2-qamt" data-val="2000">฿2,000</button>',"      </div>",'      <input id="tv2-amt" type="number" min="10" step="1" class="topup-v2-input" placeholder="฿ ...">','      <div id="tv2-ae" class="topup-v2-err" style="display:none"></div>',"    </div>",'    <div id="tv2-s2" style="display:none">','      <p class="topup-v2-bank-label" id="tv2-bl"></p>','      <div class="topup-v2-bank-card">','        <div class="topup-v2-bank-name">ธนาคาร กรุงเทพ</div>','        <div class="topup-v2-bank-branch">สาขาโชคชัย 4 ลาดพร้าว</div>','        <div class="topup-v2-bank-acct">230-0-91368-4</div>','        <div class="topup-v2-bank-holder">บจ. มิสเตอร์ อี อาร์ พี</div>','        <button class="topup-v2-copy" id="tv2-copy"></button>',"      </div>",'      <div class="topup-v2-warn" id="tv2-bn"></div>',"    </div>",'    <div id="tv2-s3" style="display:none">','      <div class="topup-v2-drop" id="tv2-drop">','        <input type="file" id="tv2-file" accept="image/*,.pdf" style="display:none">','        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>','        <span class="topup-v2-drop-text" id="tv2-dt"></span>',"      </div>",'      <div id="tv2-se" class="topup-v2-err" style="display:none"></div>','      <label class="topup-v2-label" id="tv2-pl"></label>','      <input id="tv2-payer" type="text" maxlength="200" class="topup-v2-input">','      <label class="topup-v2-label" id="tv2-nl"></label>','      <input id="tv2-note" type="text" maxlength="500" class="topup-v2-input">','      <div id="tv2-ue" class="topup-v2-err" style="display:none"></div>',"    </div>","  </div>",'  <div class="topup-v2-foot">','    <button class="btn btn-ghost" id="tv2-back" style="display:none"></button>','    <button class="btn btn-primary" id="tv2-next"></button>',"  </div>","</div>"].join(""),document.body.appendChild(e),Nt()}}function pt(){var e=function(n,a){var s=me(n);s&&(s.textContent=a)};e("tv2-title",he("topup-title")),e("tv2-sl1",he("topup-step1")),e("tv2-sl2",he("topup-step2")),e("tv2-sl3",he("topup-step3")),e("tv2-al",he("topup-amount-label")),e("tv2-bl",he("topup-bank-label")),e("tv2-copy",he("topup-copy-account")),e("tv2-dt",he("topup-slip-drop")),e("tv2-pl",he("topup-payer-label")),e("tv2-nl",he("topup-note-label"))}function Ae(e){[1,2,3].forEach(function(o){var m=me("tv2-s"+o);m&&(m.style.display=o===e?"":"none");var r=me("tv2-d"+o);r&&r.classList.toggle("active",o<=e)});var n=me("tv2-back"),a=me("tv2-next");if(e===1?n&&(n.style.display="",n.textContent=he("topup-btn-cancel")):n&&(n.style.display="",n.textContent=he("topup-btn-back")),a&&(a.textContent=he(e===3?"topup-btn-submit":"topup-btn-next")),e===2){var s=me("tv2-bn");s&&(s.innerHTML=he("topup-bank-note").replace("{amount}","<strong>฿"+Number(Ze).toLocaleString()+"</strong>"))}}function Je(){for(var e=1;e<=3;e++){var n=me("tv2-s"+e);if(n&&n.style.display!=="none")return e}return 1}function Ne(e){var n=me(e);n&&(n.textContent="",n.style.display="none")}function He(e,n){var a=me(e);a&&(a.textContent=n,a.style.display="")}function at(e){var n=me("tv2-dt");n&&(n.textContent=e.name);var a=me("tv2-drop");a&&a.classList.add("has-file"),Ne("tv2-se")}function Nt(){var e=me("topup-v2-ov");me("tv2-close").addEventListener("click",Me),e.addEventListener("click",function(m){m.target===e&&Me()}),document.addEventListener("keydown",function(m){m.key==="Escape"&&e&&e.style.display!=="none"&&Me()}),e.addEventListener("click",function(m){var r=m.target.closest(".topup-v2-qamt");if(r){e.querySelectorAll(".topup-v2-qamt").forEach(function(i){i.classList.remove("active")}),r.classList.add("active");var k=me("tv2-amt");k&&(k.value=r.dataset.val,Ne("tv2-ae"))}});var n=me("tv2-amt");n&&n.addEventListener("input",function(){e.querySelectorAll(".topup-v2-qamt").forEach(function(m){m.classList.remove("active")}),Ne("tv2-ae")});var a=me("tv2-copy");a&&a.addEventListener("click",function(){navigator.clipboard&&navigator.clipboard.writeText("2300913684").then(function(){var m=a.textContent;a.textContent=he("topup-copied"),setTimeout(function(){a.textContent=m},1500)})});var s=me("tv2-drop"),o=me("tv2-file");s&&(s.addEventListener("click",function(){o&&o.click()}),s.addEventListener("dragover",function(m){m.preventDefault(),s.classList.add("drag-over")}),s.addEventListener("dragleave",function(){s.classList.remove("drag-over")}),s.addEventListener("drop",function(m){m.preventDefault(),s.classList.remove("drag-over");var r=m.dataTransfer&&m.dataTransfer.files[0];r&&at(r)})),o&&o.addEventListener("change",function(){o.files[0]&&at(o.files[0])}),me("tv2-back").addEventListener("click",function(){var m=Je();if(m<=1){Me();return}Ae(m-1)}),me("tv2-next").addEventListener("click",function(){var m=Je();m===1?zt():m===2?Ae(3):Ot()})}async function zt(){var e=me("tv2-amt"),n=e?parseFloat(e.value):0;if(!n||n<10){He("tv2-ae",he("topup-amount-invalid"));return}if(n>5e5){He("tv2-ae",he("topup-amount-too-large"));return}Ze=n;var a=me("tv2-next");a&&(a.disabled=!0,a.textContent="…");try{var s=await fetch("/api/credits/topup/request",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+We()},body:JSON.stringify({amount_thb:n})});if(!s.ok){var o=await s.text(),m=he("topup-submit-fail");try{var r=JSON.parse(o),k=r.detail;if(Array.isArray(k)&&k.length){var i=k[0]&&k[0].type||"";i.indexOf("less_than")>=0?m=he("topup-amount-too-large"):(i.indexOf("greater_than")>=0||i.indexOf("parsing")>=0)&&(m=he("topup-amount-invalid"))}else typeof k=="string"&&(m=k)}catch{}throw new Error(m)}var f=await s.json();Xe=f.request_id,Ae(2)}catch(u){He("tv2-ae",u.message||he("topup-submit-fail"))}finally{a&&(a.disabled=!1,a.textContent=he("topup-btn-next"))}}async function Ot(){var e=me("tv2-file");if(!e||!e.files||!e.files[0]){He("tv2-se",he("topup-slip-required"));return}var n=me("tv2-next");n&&(n.disabled=!0,n.textContent="…");try{var a=new FormData;a.append("file",e.files[0]);var s=me("tv2-payer"),o=me("tv2-note");s&&s.value.trim()&&a.append("payer_name",s.value.trim()),o&&o.value.trim()&&a.append("note",o.value.trim());var m=await fetch("/api/credits/topup/upload-slip/"+Xe,{method:"POST",headers:{Authorization:"Bearer "+We()},body:a});if(!m.ok)throw new Error(await m.text());var r=await m.json();r.auto_approved?(window.showToast&&window.showToast(he("topup-auto-approved"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard()):window.showToast&&window.showToast(he("topup-pending"),"info"),Me()}catch(k){He("tv2-ue",he("topup-upload-fail")+" · "+k.message),n&&(n.disabled=!1,n.textContent=he("topup-btn-submit"))}}function Me(){var e=me("topup-v2-ov");e&&(e.style.display="none"),typeof window.loadDashboard=="function"&&window.loadDashboard()}window._openTopupModal=function(){Rt(),Xe=null,Ze=0,["tv2-amt","tv2-payer","tv2-note"].forEach(function(a){var s=me(a);s&&(s.value="")});var e=me("tv2-file");e&&(e.value="");var n=me("tv2-drop");n&&n.classList.remove("has-file","drag-over"),me("topup-v2-ov").querySelectorAll(".topup-v2-qamt").forEach(function(a){a.classList.remove("active")}),["tv2-ae","tv2-se","tv2-ue"].forEach(function(a){Ne(a)}),pt(),Ae(1),me("topup-v2-ov").style.display="flex"};typeof window.subscribeI18n=="function"&&window.subscribeI18n("topup-v2",function(){var e=me("topup-v2-ov");e&&e.style.display!=="none"&&e.style.display!==""&&(pt(),Ae(Je()))});(function(){const e="v118.28.5",n="pearnly_tc_results_"+e,a=[{id:"A1",group:"A · 异常栏 page-head(BUG1)",desc:"手机宽度进异常栏 · 标题「异常栏」横排正常 · 不再每字一行"},{id:"A2",group:"A · 异常栏 page-head(BUG1)",desc:"副标题「所有被规则拦截的单据集中复核…」也横排正常 · 不竖排"},{id:"A3",group:"A · 异常栏 page-head(BUG1)",desc:"客户筛选下拉 + 刷新按钮换到新一行 · 不抢标题宽度"},{id:"B1",group:"B · 客户管理 page-head(BUG2)",desc:"手机宽度进客户管理 · 标题「客户管理」横排正常"},{id:"B2",group:"B · 客户管理 page-head(BUG2)",desc:"副标题「为每家客户单独归档发票…」横排正常 · 不竖排"},{id:"B3",group:"B · 客户管理 page-head(BUG2)",desc:"「+ 新建客户」按钮换到新一行 · 不挤标题"},{id:"C1",group:"C · 客户卡片(BUG3)",desc:"客户卡片「编辑 / 导出本月」按钮文字清晰 · 不被截断"},{id:"D1",group:"D · 历史表头(BUG4)",desc:"手机宽度进单据记录 · 表头「文件·发票号·供应商」/「金额」单行 · 不竖排"},{id:"D2",group:"D · 历史表头(BUG4)",desc:"行内 INV-TH-202605-1006 这种长发票号正常单行展示 · 不一字一行"},{id:"E1",group:"E · 对账切换器(BUG6)",desc:"手机宽度进对账中心 · 顶栏点「全部客户」chip · 下拉从右上角向下展开 · 右对齐 · 不贴左屏边"},{id:"E2",group:"E · 对账切换器(BUG6)",desc:"下拉宽度自适应屏幕 · 不超出屏幕右边"},{id:"F1",group:"F · 通用设置回归",desc:"设置 → 个人资料 · 没有「界面语言」4 按钮卡"},{id:"F2",group:"F · 通用设置回归",desc:"左侧 nav 顺序:账户 / 公司 / 工作流 / 系统 / 关于"},{id:"F3",group:"F · 通用设置回归",desc:"系统 → 通用设置 · 4 行下拉(语言/时区/日期/数字)· 改语言立即切语言 · 改其他保存后 F5 仍保留"},{id:"G1",group:"G · 移动端 settings(回归)",desc:"手机宽度设置 tabs 不重叠 · 按分组分行 · chip 风格"},{id:"H1",group:"H · 回归",desc:"OCR 上传识别 / 客户管理 / 异常栏 / 对账中心 / 测试中心 全部仍工作"},{id:"H2",group:"H · 回归",desc:"4 语切换没新增异常(测试中心异常日志「API 失败」过滤无新条目)"},{id:"I1",group:"I · 三档移动 viewport",desc:"iPhone SE 375 · 上述 BUG 1-6 都修了"},{id:"I2",group:"I · 三档移动 viewport",desc:"Galaxy S 360 · 上述 BUG 1-6 都修了"},{id:"I3",group:"I · 三档移动 viewport",desc:"iPhone 12 Pro 414 · 上述 BUG 1-6 都修了"}];let s={},o="all",m=!1,r=!1;function k(G,W,te){let re=typeof t=="function"?t(G):null;return(!re||re===G)&&(re=W),te&&Object.keys(te).forEach(function(S){re=String(re).replace("{"+S+"}",String(te[S]))}),re}function i(){try{const G=localStorage.getItem(n);s=G?JSON.parse(G):{},(typeof s!="object"||!s)&&(s={})}catch{s={}}}function f(){try{localStorage.setItem(n,JSON.stringify(s))}catch{}}function u(G){const W=new Date(G),te=function(re){return re<10?"0"+re:""+re};return te(W.getHours())+":"+te(W.getMinutes())+":"+te(W.getSeconds())}function c(G){return String(G??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function v(G,W){try{typeof showToast=="function"?showToast(G,W||"info"):alert(G)}catch{}}function E(G){try{navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(G).then(function(){v(k("tc-toast-copied","已复制到剪贴板"),"success")}).catch(function(){x(G)}):x(G)}catch{x(G)}}function x(G){try{const W=document.createElement("textarea");W.value=G,W.style.position="fixed",W.style.opacity="0",document.body.appendChild(W),W.select();const te=document.execCommand("copy");document.body.removeChild(W),v(te?k("tc-toast-copied","已复制"):k("tc-toast-copy-fail","复制失败"),te?"success":"error")}catch{v(k("tc-toast-copy-fail","复制失败"),"error")}}function R(){const G=document.getElementById("tc-account-chip"),W=document.getElementById("tc-progress-chip");if(G&&(G.textContent=_userInfo&&(_userInfo.email||_userInfo.username)||"—"),W){const te=a.length,re=a.filter(function(S){return s[S.id]}).length;W.textContent=re+" / "+te}}function D(){const G=document.getElementById("tc-checklist-body");if(!G)return;const W={};a.forEach(function(re){W[re.group]||(W[re.group]=[]),W[re.group].push(re)});const te=[];Object.keys(W).forEach(function(re){te.push('<div class="tc-checklist-group">'),te.push('<div class="tc-checklist-group-title">'+c(re)+"</div>"),W[re].forEach(function(S){const y=s[S.id]||"",p=y?"is-"+y:"";te.push('<div class="tc-check-item '+p+'" data-id="'+c(S.id)+'"><div class="tc-check-id">'+c(S.id)+'</div><div class="tc-check-desc">'+c(S.desc)+'</div><div class="tc-check-actions">'+w(S.id,"pass",y)+w(S.id,"fail",y)+w(S.id,"skip",y)+"</div></div>")}),te.push("</div>")}),G.innerHTML=te.join("")}function w(G,W,te){const re=te===W,S={pass:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="4,11 8,15 16,5"/></svg>',fail:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="5" x2="15" y2="15"/><line x1="15" y1="5" x2="5" y2="15"/></svg>',skip:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="10" x2="15" y2="10"/></svg>'},y={pass:k("tc-status-pass","通过"),fail:k("tc-status-fail","失败"),skip:k("tc-status-skip","跳过")};return'<button type="button" class="tc-status-btn '+(re?"is-active "+W:"")+'" data-id="'+c(G)+'" data-kind="'+W+'" title="'+c(y[W])+'">'+S[W]+"</button>"}function B(G){return o==="all"?!0:o==="js_error"?G.type==="js_error"||G.type==="promise_error":o==="api"?G.type==="api_error"||G.type==="api_fail":o==="api_slow"?G.type==="api_slow":o==="console"?G.type==="console_error"||G.type==="console_warn":!0}function z(){const G=document.getElementById("tc-logs-body"),W=document.getElementById("tc-logs-count");if(!G)return;const te=(window._pearnlyTcLogs||[]).slice().reverse(),re=te.filter(B);if(W&&(W.textContent=String(te.length)),re.length===0){G.innerHTML='<div class="tc-logs-empty">'+c(k("tc-logs-empty","暂无异常"))+"</div>";return}const S=re.slice(0,100).map(function(y){const p=typeof y.detail=="object"?JSON.stringify(y.detail,null,2):String(y.detail||"");return'<div class="tc-log-item t-'+c(y.type)+'" data-ts="'+y.ts+'"><span class="tc-log-time">'+u(y.ts)+'</span><span class="tc-log-type">'+c(y.type)+'</span><div class="tc-log-summary">'+c(y.summary)+'<div class="tc-log-detail">'+c(p)+"</div></div></div>"}).join("");G.innerHTML=S,document.querySelectorAll("#tc-logs-filter .tc-filter-chip").forEach(function(y){y.classList.toggle("active",y.getAttribute("data-filter")===o)})}function q(){r||(r=!0,setTimeout(function(){r=!1,currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&z(),F()},200))}window._tcOnNewLog=q;function F(){const G=document.getElementById("nav-test-badge");if(!G)return;const W=(window._pearnlyTcLogs||[]).filter(function(te){return te.type==="js_error"||te.type==="promise_error"||te.type==="api_error"||te.type==="api_fail"||te.type==="console_error"}).length;W>0?(G.style.display="",G.textContent=W>99?"99+":String(W)):G.style.display="none"}function A(){R(),D(),z(),F()}function g(){const G=[],W=new Date,te=_userInfo&&(_userInfo.email||_userInfo.username)||"—";G.push("# Pearnly "+e+" 测试结果"),G.push("- 账号:"+te),G.push("- 时间:"+W.toISOString().replace("T"," ").slice(0,19));const re=a.length,S=a.filter(function(Z){return s[Z.id]==="pass"}).length,y=a.filter(function(Z){return s[Z.id]==="fail"}).length,p=a.filter(function(Z){return s[Z.id]==="skip"}).length,$=re-S-y-p;G.push("- 进度:"+(S+y+p)+" / "+re+" · ✅ "+S+" · ❌ "+y+" · ⏭ "+p+" · 未测 "+$),G.push(""),G.push("| ID | 描述 | 状态 |"),G.push("|---|---|---|"),a.forEach(function(Z){const le=s[Z.id],ie=le==="pass"?"✅":le==="fail"?"❌":le==="skip"?"⏭":"⬜";G.push("| "+Z.id+" | "+Z.desc.replace(/\|/g,"\\|")+" | "+ie+" |")});const P=a.filter(function(Z){return s[Z.id]==="fail"});P.length>0&&(G.push(""),G.push("## ❌ 失败项"),P.forEach(function(Z){G.push("- **"+Z.id+"** · "+Z.desc)}));const Y=(window._pearnlyTcLogs||[]).slice(-30).reverse();return Y.length>0&&(G.push(""),G.push("## 🔴 异常日志(最近 "+Y.length+" 条)"),Y.forEach(function(Z){if(G.push("- `"+u(Z.ts)+"` · **"+Z.type+"** · "+Z.summary),Z.detail){let le;try{le=JSON.stringify(Z.detail)}catch{le=String(Z.detail)}le&&le!=="{}"&&G.push("  - "+le.slice(0,600))}})),G.join(`
`)}function d(G){const W=(window._pearnlyTcLogs||[]).slice(-30).reverse();if(W.length===0)return"(暂无异常日志)";const te=["# Pearnly 异常日志(最近 "+W.length+" 条)"],re=_userInfo&&(_userInfo.email||_userInfo.username)||"—";return te.push("- 账号:"+re),te.push("- 当前页:"+(currentRoute||"?")),te.push("- UA:"+navigator.userAgent),te.push(""),W.forEach(function(S){if(te.push("## `"+u(S.ts)+"` · "+S.type),te.push("- "+S.summary),S.detail){te.push("```");try{te.push(JSON.stringify(S.detail,null,2).slice(0,2e3))}catch{te.push(String(S.detail).slice(0,2e3))}te.push("```")}}),te.join(`
`)}function h(){const G=Date.now();fetch("/api/health").then(function(W){const te=Date.now()-G;W.ok?v(k("tc-toast-health-ok","后端健康 ✓ {ms}ms",{ms:te}),"success"):v(k("tc-toast-health-fail","后端无响应")+" ("+W.status+")","error")}).catch(function(){v(k("tc-toast-health-fail","后端无响应"),"error")})}function I(){try{localStorage.removeItem(n),localStorage.removeItem("pearnly_current_client_id"),s={},(window._pearnlyTcLogs||[]).length=0,o="all",window.setCurrentClientId}catch{}A(),v(k("tc-toast-cleared","session 状态已清空"),"success")}function L(){try{fetch("/api/clients",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}).then(function(G){return G.json()}).then(function(G){window._clientsCache=G.clients||[],typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher(),typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter(),v("客户缓存已刷新 · "+(G.clients||[]).length+" 个客户","success")}).catch(function(){v("刷新失败","error")})}catch{}}function H(){if(m||!document.getElementById("page-test-center"))return;m=!0;const W=document.getElementById("tc-checklist-body");W&&W.addEventListener("click",function(le){const ie=le.target.closest(".tc-status-btn");if(!ie)return;const V=ie.getAttribute("data-id"),Q=ie.getAttribute("data-kind");!V||!Q||(s[V]===Q?delete s[V]:s[V]=Q,f(),D(),R())});const te=document.getElementById("tc-btn-reset-checklist");te&&te.addEventListener("click",function(){s={},f(),D(),R()});const re=document.getElementById("tc-btn-copy-all");re&&re.addEventListener("click",function(){E(g())});const S=document.getElementById("tc-btn-copy-logs");S&&S.addEventListener("click",function(){E(d())});const y=document.getElementById("tc-btn-clear-logs");y&&y.addEventListener("click",function(){(window._pearnlyTcLogs||[]).length=0,z(),F()});const p=document.getElementById("tc-logs-filter");p&&p.addEventListener("click",function(le){const ie=le.target.closest(".tc-filter-chip");ie&&(o=ie.getAttribute("data-filter")||"all",z())});const $=document.getElementById("tc-logs-body");$&&$.addEventListener("click",function(le){const ie=le.target.closest(".tc-log-item");ie&&ie.classList.toggle("expanded")});const P=document.getElementById("tc-tool-health");P&&P.addEventListener("click",h);const Y=document.getElementById("tc-tool-clear-session");Y&&Y.addEventListener("click",I);const Z=document.getElementById("tc-tool-reload-clients");Z&&Z.addEventListener("click",L)}function _(){}window._tcApplyVisibility=_;let M=0;const K=setInterval(function(){M++,_userInfo&&clearInterval(K),M>60&&clearInterval(K)},500);window.loadTestCenterPage=function(){i(),H(),A()},typeof window.subscribeI18n=="function"&&window.subscribeI18n("test-center",function(){F(),currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&A()})})();(function(){const e="pearnly_active_workspace_client_id",n="pearnly_work_mode";function a(B,z){if(typeof window.t=="function"){const q=window.t(B);if(q&&q!==B)return q}return z}function s(){const B=window._userInfo||{},z=String(B.role||"").toLowerCase(),q=String(B.tenant_role||"").toLowerCase();return B.is_super_admin===!0||B.is_owner===!0||z==="owner"||z==="admin"||q==="owner"||q==="admin"}function o(){return localStorage.getItem(n)==="client"?"client":"personal"}function m(){const B=localStorage.getItem(e);if(!B||B==="null"||B==="0"||B==="")return null;const z=parseInt(B,10);return isNaN(z)?null:z}function r(B){try{window.dispatchEvent(new CustomEvent("pearnly:workspace-changed",{detail:{id:B,mode:o()}}))}catch{}}function k(B){const z=m();B==null||B===0?localStorage.removeItem(e):(localStorage.setItem(e,String(B)),localStorage.setItem(n,"client")),String(z)!==String(B)&&r(B)}function i(){const B=m();localStorage.setItem(n,"personal"),localStorage.removeItem(e),B!=null&&r(null)}async function f(){try{const B=window.apiGet;if(typeof B!="function")return[];const z=await B("/api/workspace/clients");return z&&(z.clients||z.items)||[]}catch{return[]}}async function u(B){if(o()==="client"&&m()!=null)return typeof B=="function"&&B(),!0;const z=a("ws-need-client","这个功能需要先选择工作空间"),q=a("ws-btn-pick","选择工作空间"),F=a("ws-btn-cancel","取消");return typeof window.showConfirm=="function"?await window.showConfirm(z,{okText:q,cancelText:F})&&c(B):window.confirm(z+`

[`+q+" / "+F+"]")&&c(B),!1}async function c(B){const z=await f();if(typeof B=="function"&&o()!=="personal"&&z.length===1){k(Number(z[0].id)),B();return}if(typeof window.openWorkspaceChooserUI=="function"){window.openWorkspaceChooserUI({clients:z,canCreate:s(),active:m(),onPersonal:i,onPick:function(q){k(Number(q)),typeof B=="function"&&B()},emptyHint:z.length?null:s()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。")});return}if(!z.length){const q=s()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。");typeof window.showToast=="function"&&window.showToast(q,"info")}}function v(B){const z=B||document.getElementById("workspace-switcher-root");if(!z)return;const q=o(),F=m();let A,g;if(q==="client"&&F!=null){const I=(window._workspaceClientsCache||[]).find(L=>Number(L.id)===Number(F));A=x("building"),g=I?I.name:a("ws-current-label","当前工作空间")}else A=x("user"),g=a("ws-personal","个人事务");z.innerHTML='<button class="ws-ctrl-btn" id="ws-ctrl-btn" type="button">'+A+'<span class="ws-ctrl-label">'+E(g)+"</span></button>";const d=z.querySelector("#ws-ctrl-btn");d&&d.addEventListener("click",()=>c(null))}function E(B){return String(B??"").replace(/[&<>"']/g,function(z){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[z]})}function x(B){const z='<svg class="ws-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';return B==="building"?z+'<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>':z+'<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'}function R(B){B=B||{};const z=B.clients||[],q=B.active,F=document.getElementById("ws-modal");F&&F.remove();const A=document.createElement("div");A.id="ws-modal",A.className="ws-modal";const d='<button type="button" class="ws-modal-item'+(o()==="personal"||q==null?" active":"")+'" data-ws-personal="1"><span class="ws-modal-item-ic">'+x("user")+'</span><span class="ws-modal-item-text" style="display:flex;flex-direction:column;align-items:flex-start;min-width:0;"><span class="ws-modal-item-name">'+E(a("ws-personal","个人事务"))+'</span><span class="ws-modal-item-desc" style="font-size:11px;color:#6b7280;font-weight:400;margin-top:2px;line-height:1.35;white-space:normal;">'+E(a("ws-personal-desc","用于临时识别、测试或处理不归属任何公司的文件。"))+"</span></span></button>";let h="";if(z.length){const M=['<option value="">'+E(a("ws-select-ph","— 选择账套主体 —"))+"</option>"].concat(z.map(function(K){const G=q!=null&&Number(q)===Number(K.id);return'<option value="'+E(K.id)+'"'+(G?" selected":"")+">"+E(K.name||"#"+K.id)+"</option>"}));h='<div class="ws-modal-select-row"><label class="ws-modal-select-label">'+E(a("ws-select-label","账套主体"))+'</label><select class="ws-modal-select" data-ws-select="1">'+M.join("")+"</select></div>"}const I=!z.length&&B.emptyHint?'<div class="ws-modal-empty">'+E(B.emptyHint)+"</div>":"",L=B.canCreate?'<div class="ws-modal-create"><button type="button" class="ws-modal-create-toggle" data-ws-create-toggle="1">+ '+E(a("ws-create-client","新建工作空间"))+'</button><div class="ws-modal-create-form" data-ws-create-form style="display:none;"><input type="text" class="ws-modal-create-input" data-ws-create-name placeholder="'+E(a("ws-create-ph","公司名称,例如 BAKELAB"))+'"><button type="button" class="ws-modal-create-submit" data-ws-create-submit="1">'+E(a("ws-create-submit","创建"))+"</button></div></div>":"";A.innerHTML='<div class="ws-modal-box" role="dialog" aria-modal="true"><div class="ws-modal-head"><span class="ws-modal-title">'+E(a("ws-chooser-title","选择工作空间"))+'</span><button type="button" class="ws-modal-close" data-ws-close="1" aria-label="close">✕</button></div><div class="ws-modal-subtitle" style="font-size:12px;color:#6b7280;padding:2px 4px 12px;line-height:1.45;white-space:normal;">'+E(a("ws-chooser-subtitle","账套主体 = 你的公司(发票卖方/开票方)。选择正在为哪家公司做账。"))+'</div><div class="ws-modal-list">'+d+h+"</div>"+I+L+"</div>",document.body.appendChild(A);const H=A.querySelector("[data-ws-select]");H&&H.addEventListener("change",function(){const M=H.value;M&&(typeof B.onPick=="function"&&B.onPick(M),_(),v())});function _(){A.remove()}A.addEventListener("click",function(M){if(M.target===A||M.target.closest("[data-ws-close]")){_();return}if(M.target.closest("[data-ws-personal]")){typeof B.onPersonal=="function"&&B.onPersonal(),_(),v();return}const G=M.target.closest("[data-ws-pick]");if(G){const re=G.getAttribute("data-ws-pick");typeof B.onPick=="function"&&B.onPick(re),_(),v();return}if(M.target.closest("[data-ws-create-toggle]")){const re=A.querySelector("[data-ws-create-form]");if(re){re.style.display=re.style.display==="none"?"flex":"none";const S=re.querySelector("[data-ws-create-name]");S&&S.focus()}return}if(M.target.closest("[data-ws-create-submit]")){D(A,B,_);return}})}async function D(B,z,q){const F=B.querySelector("[data-ws-create-name]"),A=F?(F.value||"").trim():"";if(!A){F&&F.focus();return}let g=null;try{if(typeof window.apiPost=="function"){const h=await window.apiPost("/api/workspace/clients",{name:A});g=h&&typeof h.json=="function"?await h.json().catch(()=>null):h}}catch{g=null}const d=g&&(g.id||g.client&&g.client.id);if(!d){typeof window.showToast=="function"&&window.showToast(a("ws-create-fail","新建工作空间失败 · 请重试"),"error");return}window._workspaceClientsCache=await f(),k(Number(d)),z.onPick,q(),v()}window.openWorkspaceChooserUI=R,window.addEventListener("pearnly:workspace-changed",function(){v()}),window.getWorkMode=o,window.getActiveWorkspaceClientId=m,window.setActiveWorkspaceClientId=k,window.enterPersonalMode=i,window.requireWorkspace=u,window.openWorkspaceChooser=c,window.renderWorkspaceControl=v,window.fetchWorkspaceClients=f;function w(){try{if(sessionStorage.getItem("pearnly_ws_login_prompted")==="1"||m()!=null||localStorage.getItem(n)==="personal")return;sessionStorage.setItem("pearnly_ws_login_prompted","1"),setTimeout(function(){c(null)},800)}catch{}}f().then(B=>{window._workspaceClientsCache=B,v(),w()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("workspace-switcher",v)})();(function(){const e=q=>document.querySelector('[data-num-target="'+q+'"]');function n(q){if(!q)return t("reconcile-last-activity-none");try{const F=new Date(q),A=new Date,g=A-F;if(g/6e4<5)return t("reconcile-last-activity-just-now");if(F.toDateString()===A.toDateString())return t("reconcile-last-activity-today");const h=Math.max(1,Math.floor(g/(24*3600*1e3)));return t("reconcile-last-activity-days-ago").replace("{n}",h)}catch{return t("reconcile-last-activity-none")}}function a(q,F,A){const g=e(q);g&&(g.textContent=A?"-":String(F),g.classList.toggle("is-empty",!!A))}function s(q){const F=document.getElementById("reconcile-error");F&&(F.style.display=q?"flex":"none")}function o(q){const F=document.getElementById("reconcile-empty");F&&(F.style.display=q?"flex":"none")}function m(q,F){const A=document.getElementById("reconcile-last-activity");A&&(A.textContent=q,A.classList.toggle("has-data",!!F))}function r(q){const F=!q||(q.total_sessions||0)===0;a("pending",q.pending||0,F),a("matched",q.matched||0,F),a("unmatched",q.unmatched||0,F),m(n(q.last_activity_at),!!q.last_activity_at),s(!1),o(F)}function k(q){const F=q.toUpperCase();return F==="KBANK"?"bank-chip-kbank":F==="SCB"?"bank-chip-scb":F==="BBL"?"bank-chip-bbl":F==="KTB"?"bank-chip-ktb":F==="TTB"?"bank-chip-ttb":"bank-chip-other"}function i(q,F){const A=g=>g?String(g).slice(0,10):"?";return!q&&!F?"":A(q)+" ~ "+A(F)}function f(q){return q==null?"":String(q).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function u(q){const F=document.getElementById("reconcile-recent"),A=document.getElementById("reconcile-recent-list");if(!F||!A)return;const g=(q||[]).slice(0,20);if(g.length===0){F.style.display="none";return}F.style.display="",o(!1),A.innerHTML=g.map(d=>{const h=d.parse_status==="parse_failed",I=d.bank_code||"OTHER",L=d.account_last4?" ···"+f(d.account_last4):"",H=i(d.period_start,d.period_end),_=f(d.source_filename||""),M=Number(d.tx_count||0),K=h?'<span class="recon-card-fail" data-i18n="reconcile-card-parse-failed">'+t("reconcile-card-parse-failed")+"</span>":'<span class="recon-card-tx">'+t("reconcile-card-tx").replace("{n}",M)+"</span>";return'<div class="recon-card" data-session-id="'+f(d.id)+'" data-session-name="'+_+'"><span class="bank-chip '+k(I)+'">'+f(I)+'</span><div class="recon-card-main"><div class="recon-card-title">'+_+L+'</div><div class="recon-card-sub">'+f(H)+'</div></div><div class="recon-card-right">'+K+'</div><button class="recon-card-trash" data-trash="'+f(d.id)+'" title="'+f(t("bank-session-delete-tip")||"删除")+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/></svg></button><svg class="recon-card-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg></div>'}).join(""),A.querySelectorAll(".recon-card").forEach(d=>{d.addEventListener("click",h=>{h.target.closest(".recon-card-trash")||(d.dataset.sessionId,c())})}),A.querySelectorAll(".recon-card-trash").forEach(d=>{d.addEventListener("click",h=>{h.stopPropagation();const I=d.dataset.trash,L=d.closest(".recon-card"),H=L&&L.dataset.sessionName||"";typeof window._deleteBankSession=="function"&&window._deleteBankSession(I,H)})})}function c(q){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const F=document.querySelector('[data-recon-tab="bank"]');F&&F.click()},150)}function v(){s(!0),o(!1)}function E(){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const q=document.querySelector('[data-recon-tab="bank"]');q&&q.click()},150)}async function x(){a("pending",0,!0),a("matched",0,!0),a("unmatched",0,!0),m("",!1),s(!1),o(!1);const q=document.getElementById("reconcile-recent");q&&(q.style.display="none");const F={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")};try{const[A,g]=await Promise.all([fetch("/api/bank-recon/stats",{headers:F}),fetch("/api/bank-recon/sessions?limit=20",{headers:F})]);if(!A.ok)throw new Error("http "+A.status);const d=await A.json(),h=g.ok?await g.json():[];r(d||{}),u(h||[])}catch(A){console.warn("[reconcile] load failed",A),v()}}function R(q){if(!q||!q.length)return;const F="Bearer "+(localStorage.getItem("mrpilot_token")||"");let A=0;const g=q.length;Array.from(q).forEach(function(d){const h=new FormData;h.append("file",d,d.name);const I=new XMLHttpRequest;I.open("POST","/api/bank-recon/upload"),I.setRequestHeader("Authorization",F),I.onload=function(){A++;try{const L=JSON.parse(I.responseText);I.status===200&&L.tx_count!==void 0?showToast((t("bank-upload-ok")||"解析成功 · 共 {n} 条流水").replace("{n}",L.tx_count),"success"):showToast(d.name+" "+(t("upload-failed")||"上传失败"),"error")}catch{showToast(d.name+" "+(t("upload-failed")||"上传失败"),"error")}A===g&&setTimeout(x,600)},I.onerror=function(){A++,showToast(d.name+" "+(t("upload-failed")||"上传失败"),"error"),A===g&&setTimeout(x,600)},I.send(h)}),showToast((t("bank-queue-status-uploading")||"上传中")+"…","info")}function D(){if(window.__reconcileBound)return;window.__reconcileBound=!0;const q=document.getElementById("reconcile-bank-file-input");q&&q.addEventListener("change",function(){R(this.files),this.value=""}),document.addEventListener("click",F=>{if(F.target.closest("#btn-reconcile-upload-top")||F.target.closest("#btn-reconcile-upload-empty")){E();return}if(F.target.closest("#btn-reconcile-retry")){x();return}if(F.target.closest("#btn-reconcile-dev-seed")){z();return}})}const w=["468b50c1-5593-4fd6-990d-515ce8085563"];function B(){const q=document.getElementById("btn-reconcile-dev-seed");if(!q)return;const F=typeof _userInfo<"u"?_userInfo:null,A=F&&F.id&&w.indexOf(String(F.id))>=0;q.style.display=A?"":"none"}async function z(){try{const q=await fetch("/api/bank-recon/_dev/seed",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!q.ok)throw new Error("seed:"+q.status);const F=await q.json(),A=(t("reconcile-dev-seed-ok")||"").replace("{n}",F.tx_count||0);showToast(A,"success"),typeof window.navigateTo=="function"?window.navigateTo("automation"):location.hash="#/automation",setTimeout(()=>{const g=document.querySelector('[data-auto-tab="bank"]');g&&g.click(),F.session_id&&typeof window._openBankSession=="function"&&window._openBankSession(F.session_id)},300)}catch(q){console.warn("[reconcile] dev seed failed",q),showToast(t("reconcile-dev-seed-fail")||"Seed failed","error")}}window.loadReconcilePage=async function(){D(),B(),typeof window._bankReconV2Init=="function"&&window._bankReconV2Init();try{await x()}catch{}},window._rerenderReconcile=function(){typeof currentRoute=="string"&&currentRoute==="reconcile"&&x().catch(()=>{})},typeof window.subscribeI18n=="function"&&window.subscribeI18n("reconcile",window._rerenderReconcile)})();(function(){const e=document.getElementById("assign-clients-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
    <div class="modal" style="max-width:480px">
        <div class="modal-head">
            <div class="modal-title">
                <span data-i18n="assign-modal-title">分配客户</span>
                <span class="modal-title-sub" id="assign-modal-target"></span>
            </div>
            <button type="button" class="modal-close" id="assign-modal-close" aria-label="Close">
                <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 6l8 8M14 6l-8 8" stroke-linecap="round"/></svg>
            </button>
        </div>
        <div class="modal-body">
            <div class="assign-modal-toolbar">
                <label class="assign-toolbar-checkbox">
                    <input type="checkbox" id="assign-select-all">
                    <span data-i18n="assign-select-all">全选</span>
                </label>
                <span class="assign-toolbar-count" id="assign-selected-count"></span>
            </div>
            <div class="assign-clients-list" id="assign-clients-list">
                <div class="assign-empty" data-i18n="assign-loading">加载中...</div>
            </div>
        </div>
        <div class="modal-foot">
            <button type="button" class="btn btn-ghost" id="assign-modal-cancel" data-i18n="assign-cancel">取消</button>
            <button type="button" class="btn btn-primary" id="assign-modal-save" data-i18n="assign-save">保存</button>
        </div>
    </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");a[n][o]&&(s.textContent=a[n][o])})}catch{}}})();(function(){let e={employeeId:null,employeeName:"",clients:[],selected:new Set,opened:!1};function n(){return document.getElementById("assign-clients-modal")}function a(){return document.getElementById("assign-clients-list")}function s(){return document.getElementById("assign-select-all")}function o(){return document.getElementById("assign-selected-count")}function m(){return document.getElementById("assign-modal-target")}function r(){const x=a();if(x){if(!e.clients.length){x.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-no-clients")||"暂无客户 · 请先到「客户管理」添加")+"</div>";return}x.innerHTML=e.clients.map(R=>{const D=String(R.id),w=e.selected.has(D)?"checked":"",B=escapeHtml(R.name||R.label||"#"+D),z=R.code?'<span class="assign-row-code">'+escapeHtml(R.code)+"</span>":"";return'<label class="assign-row"><input type="checkbox" data-cid="'+escapeHtml(D)+'" '+w+'><span class="assign-row-name">'+B+"</span>"+z+"</label>"}).join(""),k()}}function k(){const x=o();if(x){const D=t("assign-selected-count")||"已选 {n} / {total}";x.textContent=D.replace("{n}",e.selected.size).replace("{total}",e.clients.length)}const R=s();R&&(R.checked=e.clients.length>0&&e.selected.size===e.clients.length)}function i(){const x=m();x&&(x.textContent=e.employeeName?" · "+e.employeeName:"")}async function f(x,R){e.employeeId=x,e.employeeName=R||"",e.opened=!0,e.selected=new Set,e.clients=[],i();const D=a();D&&(D.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-loading")||"加载中...")+"</div>");const w=n();w&&(w.style.display="flex");try{const[B,z]=await Promise.all([apiGet("/api/clients?include_inactive=false"),apiGet("/api/team/employees/"+encodeURIComponent(x)+"/assignments")]);e.clients=B&&B.clients||[];const q=z&&z.client_ids||[];e.selected=new Set(q.map(String)),r()}catch(B){console.error("[assign-clients] load failed",B);const z=a();z&&(z.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-load-failed")||"加载失败 · 请重试")+"</div>")}}function u(){e.opened=!1;const x=n();x&&(x.style.display="none")}async function c(){if(!e.employeeId)return;const x=Array.from(e.selected).map(D=>parseInt(D,10)).filter(D=>!isNaN(D)),R=document.getElementById("assign-modal-save");R&&(R.disabled=!0);try{const D=await apiPost("/api/team/employees/"+encodeURIComponent(e.employeeId)+"/assignments",{client_ids:x});D&&D.ok!==!1?(showToast((t("assign-saved")||"已保存 {n} 个客户分配").replace("{n}",x.length),"success"),u(),typeof loadTeamList=="function"&&loadTeamList()):showToast(t("assign-save-failed")||"保存失败","error")}catch(D){console.error("[assign-clients] save failed",D),showToast(t("assign-save-failed")||"保存失败","error")}finally{R&&(R.disabled=!1)}}function v(){const x=n();if(!x||x.dataset.bound==="1")return;x.dataset.bound="1";const R=document.getElementById("assign-modal-close");R&&R.addEventListener("click",u);const D=document.getElementById("assign-modal-cancel");D&&D.addEventListener("click",u);const w=document.getElementById("assign-modal-save");w&&w.addEventListener("click",c),x.addEventListener("click",function(q){q.target===x&&u()});const B=s();B&&B.addEventListener("change",function(){B.checked?e.selected=new Set(e.clients.map(q=>String(q.id))):e.selected=new Set,r()});const z=a();z&&z.addEventListener("change",function(q){const F=q.target.closest('input[type="checkbox"][data-cid]');if(!F)return;const A=F.dataset.cid;F.checked?e.selected.add(A):e.selected.delete(A),k()})}function E(){e.opened&&(i(),r())}typeof window.subscribeI18n=="function"&&window.subscribeI18n("assign-clients-modal",E),window.openAssignClientsModal=function(x,R){v(),f(x,R)}})();(function(){const e={page:1,per_page:50,q:"",total:0,rows:[],loaded:!1};function n(u){if(!u)return"";try{return new Date(u).toLocaleString()}catch{return u}}function a(u){const c=document.getElementById("access-log-table");c&&(c.innerHTML='<div class="access-log-empty">'+escapeHtml(u)+"</div>");const v=document.getElementById("access-log-pager");v&&(v.innerHTML="")}function s(){const u=document.getElementById("access-log-table");if(!u)return;const c=e.rows||[];if(!c.length){a(t("set-access-log-empty"));return}const v=`
            <div class="access-log-row access-log-head">
                <div>${escapeHtml(t("set-access-log-col-time"))}</div>
                <div>${escapeHtml(t("set-access-log-col-actor"))}</div>
                <div>${escapeHtml(t("set-access-log-col-action"))}</div>
                <div>${escapeHtml(t("set-access-log-col-target"))}</div>
                <div>${escapeHtml(t("set-access-log-col-ip"))}</div>
            </div>`,E=c.map(function(x){return`
                <div class="access-log-row">
                    <div class="access-log-time" data-label="${escapeHtml(t("set-access-log-col-time"))}">${escapeHtml(n(x.created_at))}</div>
                    <div class="access-log-actor" data-label="${escapeHtml(t("set-access-log-col-actor"))}">${escapeHtml(x.actor_username||"-")}</div>
                    <div data-label="${escapeHtml(t("set-access-log-col-action"))}"><span class="access-log-action">${escapeHtml(x.action||"-")}</span></div>
                    <div class="access-log-target" data-label="${escapeHtml(t("set-access-log-col-target"))}">${escapeHtml(x.target_name||x.target_type||"-")}</div>
                    <div class="access-log-ip" data-label="${escapeHtml(t("set-access-log-col-ip"))}">${escapeHtml(x.ip||"-")}</div>
                </div>`}).join("");u.innerHTML=v+E}function o(){const u=document.getElementById("access-log-pager");if(!u)return;const c=e.total||0;if(!c){u.innerHTML="";return}const v=e.page||1,E=e.per_page,x=Math.max(1,Math.ceil(c/E)),R=(t("set-access-log-pager-total")||"Total {n}").replace("{n}",c),D=(t("set-access-log-pager-page")||"Page {p} / {t}").replace("{p}",v).replace("{t}",x);u.innerHTML=`
            <div class="access-log-pager-info">${escapeHtml(R)}</div>
            <div class="access-log-pager-ctrl">
                <button class="access-log-pager-btn" type="button" data-access-log-page="${v-1}" ${v<=1?"disabled":""}>← ${escapeHtml(t("set-access-log-pager-prev"))}</button>
                <span class="access-log-pager-page">${escapeHtml(D)}</span>
                <button class="access-log-pager-btn" type="button" data-access-log-page="${v+1}" ${v>=x?"disabled":""}>${escapeHtml(t("set-access-log-pager-next"))} →</button>
            </div>`}async function m(u){const c=localStorage.getItem("mrpilot_token");if(c){e.page=u||1,a(t("set-access-log-loading"));try{const v="/api/me/access_log?page="+e.page+"&per_page="+e.per_page+"&q="+encodeURIComponent(e.q||""),E=await fetch(v,{headers:{Authorization:"Bearer "+c}});if(E.status===403){a(t("set-access-log-empty"));return}if(!E.ok)throw new Error("http_"+E.status);const x=await E.json();e.rows=x.logs||[],e.total=x.total||0,e.loaded=!0,s(),o()}catch{a(t("set-access-log-fail"))}}}async function r(){const u=localStorage.getItem("mrpilot_token");if(u)try{const c="/api/me/access_log.csv?q="+encodeURIComponent(e.q||""),v=await fetch(c,{headers:{Authorization:"Bearer "+u}});if(!v.ok){showToast(t("set-access-log-csv-fail")||"Export failed","error");return}const E=await v.blob(),x=document.createElement("a"),R=URL.createObjectURL(E);x.href=R,x.download="pearnly_access_log.csv",document.body.appendChild(x),x.click(),setTimeout(function(){URL.revokeObjectURL(R),x.remove()},100),showToast(t("set-access-log-csv-ok")||"Exported","success")}catch{showToast(t("set-access-log-csv-fail")||"Export failed","error")}}function k(){const u=document.querySelectorAll(".set-tab-owner-only"),c=!!(_userInfo&&(_userInfo.role==="owner"||_userInfo.is_super_admin));u.forEach(function(v){v.style.display=c?"":"none"})}document.addEventListener("click",function(u){if(u.target.closest('.settings-tab[data-tab="access-log"]')){setTimeout(function(){(!e.loaded||e.page!==1)&&m(1)},50);return}if(u.target.closest("#access-log-csv-btn")){u.preventDefault(),r();return}const E=u.target.closest(".access-log-pager-btn[data-access-log-page]");if(E&&!E.disabled){const x=parseInt(E.dataset.accessLogPage,10);m(x)}}),document.addEventListener("input",function(u){u.target&&u.target.id==="access-log-search"&&(clearTimeout(window.__accessLogSearchTimer),window.__accessLogSearchTimer=setTimeout(function(){e.q=(u.target.value||"").trim(),m(1)},350))});let i=0;const f=setInterval(function(){i++,_userInfo&&(k(),clearInterval(f)),i>60&&clearInterval(f)},500);typeof window.subscribeI18n=="function"&&window.subscribeI18n("me-access-log",function(){k(),e.loaded&&(s(),o())})})();(function(){const e=document.getElementById("notif-new-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
        <div class="modal" style="max-width:520px;">
            <div class="modal-head">
                <div class="modal-title" data-i18n="notif-new-title">新建提醒规则</div>
                <button class="modal-close" id="notif-new-close" type="button" aria-label="close">×</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label class="form-label" data-i18n="notif-new-template">触发场景</label>
                    <div class="notif-template-options">
                        <label class="notif-template-opt" data-tmpl="exception_high">
                            <input type="radio" name="notif-template" value="exception_high">
                            <div class="notif-template-card">
                                <div class="notif-template-name" data-i18n="notif-tmpl-exception-name">异常栏拦下高危单</div>
                                <div class="notif-template-desc" data-i18n="notif-tmpl-exception-desc">数学不自洽 / 重复发票 / 缺总额 等高严重度异常 · 自动推送</div>
                            </div>
                        </label>
                        <label class="notif-template-opt" data-tmpl="large_invoice">
                            <input type="radio" name="notif-template" value="large_invoice">
                            <div class="notif-template-card">
                                <div class="notif-template-name" data-i18n="notif-tmpl-large-name">单张发票超阈值</div>
                                <div class="notif-template-desc" data-i18n="notif-tmpl-large-desc">总金额 ≥ 你设的金额 · 立刻推 LINE</div>
                            </div>
                        </label>
                    </div>
                </div>

                <div class="form-group">
                    <label class="form-label" for="notif-new-name" data-i18n="notif-new-name-label">规则名称</label>
                    <input type="text" id="notif-new-name" class="form-input" maxlength="100" data-i18n-placeholder="notif-new-name-ph" placeholder="例:大额发票推老板">
                </div>

                <div class="form-group" id="notif-new-threshold-row" style="display:none;">
                    <label class="form-label" for="notif-new-threshold" data-i18n="notif-new-threshold-label">金额阈值(฿)</label>
                    <input type="number" id="notif-new-threshold" class="form-input" min="1" step="1" data-i18n-placeholder="notif-new-threshold-ph" placeholder="500000">
                    <div class="form-hint" data-i18n="notif-new-threshold-hint">总额 ≥ 此值 · 才推送</div>
                </div>

                <div id="notif-line-check" class="notif-line-check" style="display:none;"></div>
            </div>
            <div class="modal-foot">
                <button class="btn btn-ghost" id="notif-new-cancel" type="button" data-i18n="btn-cancel">取消</button>
                <button class="btn btn-primary" id="notif-new-save" type="button" data-i18n="notif-new-save">保存规则</button>
            </div>
        </div>
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");a[n][o]&&(s.textContent=a[n][o])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const o=s.getAttribute("data-i18n-placeholder");a[n][o]&&(s.placeholder=a[n][o])}))}catch{}}})();(function(){const e=A=>document.getElementById(A);async function n(A,g){return await fetch(A,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(g||{})})}async function a(A){return await fetch(A,{method:"DELETE",headers:{Authorization:"Bearer "+token}})}let s=null;async function o(){try{s=await apiGet("/api/line/binding")}catch{s={bound:!1}}return s}function m(A,g){if(!A)return;A.style.display="",A.className="notif-line-check "+(g?"bound":"unbound");const d=g?'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>';A.innerHTML=d+"<span>"+escapeHtml(t(g?"notif-line-bound":"notif-line-not-bound"))+"</span>"}function r(A){if(A==null)return"-";const g=Number(A);return isNaN(g)?String(A):"฿ "+g.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function k(A){if(!A)return"-";try{const g=new Date(A),d=(g.getMonth()+1).toString().padStart(2,"0"),h=g.getDate().toString().padStart(2,"0"),I=g.getHours().toString().padStart(2,"0"),L=g.getMinutes().toString().padStart(2,"0");return`${d}-${h} ${I}:${L}`}catch{return A}}function i(A){const g=e("notif-rules-list"),d=e("notif-rules-empty"),h=e("notif-rules-count");if(!(!g||!d)){if(h.textContent=String(A.length),h.className="auto-status-pill "+(A.length>0?"active":"none"),!A.length){d.style.display="",g.style.display="none",g.innerHTML="";return}d.style.display="none",g.style.display="",g.innerHTML=A.map(I=>{const L=I.template_code==="large_invoice",H=L?"notif-rule-large-tag":"notif-rule-exception-tag",_=L?"large":"";let M=[];if(L){const G=I.params&&I.params.threshold?r(I.params.threshold):"-";M.push(escapeHtml(t("notif-rule-threshold-prefix"))+" "+G)}I.enabled||M.push('<span style="color:#9ca3af;">'+escapeHtml(t("notif-rule-disabled"))+"</span>");const K=M.length?M.join(' <span class="dot"></span> '):"";return`
                <div class="notif-rule-row${I.enabled?"":" disabled"}" data-rule-id="${I.id}">
                    <span class="notif-rule-tmpl-badge ${_}">${escapeHtml(t(H))}</span>
                    <div class="notif-rule-main">
                        <div class="notif-rule-name">${escapeHtml(I.name)}</div>
                        <div class="notif-rule-meta">${K}</div>
                    </div>
                    <div class="notif-rule-actions">
                        <button class="notif-rule-toggle ${I.enabled?"on":""}" data-action="toggle" aria-label="toggle"></button>
                        <button class="notif-rule-btn" data-action="test">${escapeHtml(t("notif-action-test"))}</button>
                        <button class="notif-rule-btn danger" data-action="delete">${escapeHtml(t("notif-action-delete"))}</button>
                    </div>
                </div>`}).join("")}}function f(A){const g=e("notif-logs-list");if(g){if(!A.length){g.innerHTML='<div class="notif-logs-empty">'+escapeHtml(t("notif-logs-empty"))+"</div>";return}g.innerHTML=A.map(d=>{const h=d.status==="sent",I=d.event_type==="exception_high"?"notif-event-exception-high":d.event_type==="large_invoice"?"notif-event-large-invoice":"notif-event-test-send",L=h?"":" · "+escapeHtml(d.error||"failed");return`
                <div class="notif-log-row">
                    <span class="notif-log-status ${h?"":"failed"}"></span>
                    <div class="notif-log-main">
                        <div class="notif-log-event">${escapeHtml(t(I))}</div>
                        <div class="notif-log-meta">${escapeHtml(d.template_code||"-")}${L}</div>
                    </div>
                    <div class="notif-log-time">${k(d.sent_at)}</div>
                </div>`}).join("")}}async function u(){try{const A=await apiGet("/api/notifications/rules");c=A&&A.items||[],i(c)}catch(A){console.warn("load rules fail",A)}try{const A=await apiGet("/api/notifications/logs?limit=20");v=A&&A.items||[],f(v)}catch(A){console.warn("load logs fail",A)}}let c=null,v=null;function E(){c&&i(c),v&&f(v);const A=e("notif-new-modal");A&&A.style.display!=="none"&&s&&m(e("notif-line-check"),!!(s&&s.bound))}function x(){const A=e("notif-new-modal");A&&(A.style.display="",e("notif-new-name").value="",e("notif-new-threshold").value="",e("notif-new-threshold-row").style.display="none",document.querySelectorAll('input[name="notif-template"]').forEach(g=>g.checked=!1),o().then(g=>m(e("notif-line-check"),!!(g&&g.bound))))}function R(){const A=e("notif-new-modal");A&&(A.style.display="none")}function D(){const A=document.querySelector('input[name="notif-template"]:checked'),g=e("notif-new-threshold-row");if(!A){g.style.display="none";return}g.style.display=A.value==="large_invoice"?"":"none";const d=e("notif-new-name");d&&!d.value.trim()&&(d.value=A.value==="large_invoice"?t("notif-tmpl-large-name"):t("notif-tmpl-exception-name"))}async function w(){const A=document.querySelector('input[name="notif-template"]:checked');if(!A){showToast(t("notif-new-template"),"error");return}const g=(e("notif-new-name").value||"").trim();if(!g){showToast(t("notif-name-required"),"error");return}const d={name:g,template_code:A.value,params:{},enabled:!0};if(A.value==="large_invoice"){const h=parseFloat(e("notif-new-threshold").value||"0");if(!h||h<=0){showToast(t("notif-threshold-required"),"error");return}d.params.threshold=h}try{const h=await apiPost("/api/notifications/rules",d);if(h&&h.ok)showToast(t("notif-toast-created"),"success"),R(),u();else{const I=await(h&&h.json&&h.json().catch(()=>({})))||{};showToast(I&&I.detail||"save failed","error")}}catch{showToast("save failed","error")}}async function B(A,g,d){if(A==="toggle"){const h=d.classList.contains("on"),I=await n("/api/notifications/rules/"+g,{enabled:!h});I&&I.ok?(showToast(t(h?"notif-toast-toggled-off":"notif-toast-toggled-on"),"success"),u()):showToast("toggle failed","error");return}if(A==="test"){const h=await o();if(!h||!h.bound){showToast(t("notif-line-error-bind-first"),"error");return}const I=await apiPost("/api/notifications/rules/"+g+"/test",{});if(I&&I.ok)showToast(t("notif-toast-test-sent"),"success"),u();else{const L=await(I&&I.json&&I.json().catch(()=>({})))||{},H=L&&L.detail||"";showToast(H||t("notif-toast-test-failed"),"error"),u()}return}if(A==="delete"){if(!await showConfirm(t("notif-confirm-delete"),{danger:!0}))return;const I=await a("/api/notifications/rules/"+g);I&&I.ok?(showToast(t("notif-toast-deleted"),"success"),u()):showToast("delete failed","error");return}}let z=!1;function q(){if(z)return;z=!0;const A=e("notif-btn-new");A&&A.addEventListener("click",x);const g=e("notif-btn-refresh-logs");g&&g.addEventListener("click",u);const d=e("notif-new-close");d&&d.addEventListener("click",R);const h=e("notif-new-cancel");h&&h.addEventListener("click",R);const I=e("notif-new-save");I&&I.addEventListener("click",w),document.querySelectorAll('input[name="notif-template"]').forEach(_=>{_.addEventListener("change",D)});const L=e("notif-rules-list");L&&L.addEventListener("click",_=>{const M=_.target.closest("button[data-action]");if(!M)return;const K=M.closest("[data-rule-id]");K&&B(M.getAttribute("data-action"),K.getAttribute("data-rule-id"),M)});const H=e("notif-new-modal");H&&H.addEventListener("click",_=>{_.target===H&&R()})}async function F(){q(),await u()}window._loadNotificationsPanel=F,window._rerenderNotifications=E})();(function(){function n(w,B){try{return window.t&&window.t(w)||B}catch{return B}}function a(){var w="";try{w=localStorage.getItem("mrpilot_token")||""}catch{}return w?{Authorization:"Bearer "+w}:{}}var s=[{tbody:"vex-task-tbody",api:"/api/recon/tasks/batch_delete",reload:function(){try{window.loadRecentTasks&&window.loadRecentTasks()}catch{}},kind:"vex"},{tbody:"glv-history-tbody",api:"/api/recon/gl-vat/tasks/batch_delete",reload:function(){try{window._loadGlvHistory&&window._loadGlvHistory()}catch{}},kind:"glv"},{tbody:"brv2-history-tbody",api:"/api/recon/bank-v2/tasks/batch_delete",reload:function(){try{window._brv2LoadHistory&&window._brv2LoadHistory()}catch{}},kind:"brv2"}];function o(){if(!document.getElementById("recon-batch-style")){var w=document.createElement("style");w.id="recon-batch-style",w.textContent=".recon-sel-cell{width:36px;text-align:center;padding-left:10px!important;padding-right:6px!important}.recon-sel-cb,.recon-master-cb{cursor:pointer;width:14px;height:14px;accent-color:#111;margin:0;vertical-align:middle}th.recon-time-col,td.recon-time-col{white-space:nowrap}tr.recon-thead-batch{display:none}thead.recon-batch-mode tr.recon-thead-default{display:none}thead.recon-batch-mode tr.recon-thead-batch{display:table-row}tr.recon-thead-batch th{background:#fafaf8;border-bottom:1px solid #e8e8e3;padding:8px 12px}tr.recon-thead-batch .recon-batch-inline{display:flex;align-items:center;gap:10px;font-size:12px;color:#111;font-weight:normal}tr.recon-thead-batch .recon-batch-count-inline{font-weight:600;color:#111;margin-right:4px}tr.recon-thead-batch .recon-batch-del-inline{background:#dc2626;color:#fff;border:none;border-radius:6px;padding:4px 10px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:4px}tr.recon-thead-batch .recon-batch-del-inline:hover{background:#b91c1c}tr.recon-thead-batch .recon-batch-clear-inline{background:transparent;border:none;color:#555;cursor:pointer;font-size:12px;font-family:inherit;text-decoration:underline;padding:4px 2px}tr.recon-thead-batch .recon-batch-clear-inline:hover{color:#111}.recon-batch-bar{display:none!important}",document.head.appendChild(w)}}function m(w){return w?w.dataset&&w.dataset.taskId?w.dataset.taskId:w.dataset&&w.dataset.taskid?w.dataset.taskid:"":""}function r(w){var B=document.getElementById(w.tbody);if(!B)return null;var z=B.closest("table");if(!z)return null;var q=z.querySelector("thead");if(!q)return null;if(q._reconReady)return q;var F=q.querySelector("tr");if(!F)return null;if(F.classList.add("recon-thead-default"),!F.querySelector(".recon-master-cb")){var A=document.createElement("th");A.className="recon-sel-cell";var g=document.createElement("input");g.type="checkbox",g.className="recon-master-cb",g.setAttribute("aria-label","select all"),g.addEventListener("change",function(){u(w,g.checked)}),A.appendChild(g),F.insertBefore(A,F.firstElementChild)}var d=F.children[1];d&&!d.classList.contains("recon-time-col")&&d.classList.add("recon-time-col");var h=F.children.length,I=document.createElement("tr");I.className="recon-thead-batch";var L=document.createElement("th");L.className="recon-sel-cell";var H=document.createElement("input");H.type="checkbox",H.className="recon-master-cb",H.checked=!0,H.setAttribute("aria-label","select all"),H.addEventListener("change",function(){u(w,H.checked)}),L.appendChild(H);var _=document.createElement("th");return _.setAttribute("colspan",String(h-1)),_.innerHTML='<div class="recon-batch-inline"><span class="recon-batch-count-inline" data-recon-count></span><button type="button" class="recon-batch-del-inline" data-recon-del><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg><span data-recon-del-label></span></button><button type="button" class="recon-batch-clear-inline" data-recon-clear></button></div>',I.appendChild(L),I.appendChild(_),q.appendChild(I),_.querySelector("[data-recon-del]").addEventListener("click",function(){x(w)}),_.querySelector("[data-recon-clear]").addEventListener("click",function(){E(w)}),q._reconReady=!0,v(w),q}function k(w){var B=document.getElementById(w.tbody);if(B){var z=B.querySelectorAll("tr");z.forEach(function(q){var F=m(q);if(F&&!q.querySelector(".recon-sel-cb")){var A=q.querySelector("td");if(A){var g=document.createElement("td");g.className="recon-sel-cell";var d=document.createElement("input");d.type="checkbox",d.className="recon-sel-cb",d.dataset.taskId=F,d.dataset.kind=w.kind,d.addEventListener("click",function(I){I.stopPropagation()}),d.addEventListener("change",function(){c(w)}),g.appendChild(d),q.insertBefore(g,A);var h=q.children[1];h&&!h.classList.contains("recon-time-col")&&h.classList.add("recon-time-col")}}}),c(w)}}function i(w){var B=document.getElementById(w.tbody);return B?Array.prototype.slice.call(B.querySelectorAll(".recon-sel-cb")):[]}function f(w){return i(w).filter(function(B){return B.checked}).map(function(B){return B.dataset.taskId})}function u(w,B){i(w).forEach(function(z){z.checked=!!B}),c(w)}function c(w){var B=f(w),z=i(w),q=document.getElementById(w.tbody);if(q){var F=q.closest("table"),A=F&&F.querySelector("thead");if(A){B.length>0?A.classList.add("recon-batch-mode"):A.classList.remove("recon-batch-mode"),A.querySelectorAll(".recon-master-cb").forEach(function(d){if(z.length===0){d.checked=!1,d.indeterminate=!1;return}B.length===z.length?(d.checked=!0,d.indeterminate=!1):B.length===0?(d.checked=!1,d.indeterminate=!1):(d.checked=!1,d.indeterminate=!0)});var g=A.querySelector("[data-recon-count]");g&&(g.textContent=n("recon-batch-selected-n","已选 {n} 条").replace("{n}",B.length))}}}function v(w){var B=document.getElementById(w.tbody);if(B){var z=B.closest("table"),q=z&&z.querySelector("thead");if(q){var F=q.querySelector("[data-recon-del-label]"),A=q.querySelector("[data-recon-clear]");F&&(F.textContent=n("recon-batch-delete","批量删除")),A&&(A.textContent=n("recon-batch-clear","取消")),c(w)}}}function E(w){i(w).forEach(function(B){B.checked=!1}),c(w)}async function x(w){var B=f(w);if(B.length){var z=n("recon-batch-delete-confirm","确定删除选中的 {n} 条对账任务?此操作不可恢复").replace("{n}",B.length),q=!1;try{typeof window.pearnlyConfirm=="function"?q=await window.pearnlyConfirm(z,n("recon-batch-delete-title","批量删除")):q=window.confirm(z)}catch{q=!1}if(q)try{var F=Object.assign({"Content-Type":"application/json"},a()),A=w.kind==="glv"?B.map(function(I){return parseInt(I,10)}):B,g=await fetch(w.api,{method:"POST",headers:F,body:JSON.stringify({ids:A})});if(!g.ok){typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error");return}var d=await g.json(),h=d&&(d.deleted!=null?d.deleted:d.count)||B.length;typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-ok","已删除 {n} 条").replace("{n}",h),"success"),w.reload()}catch{typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error")}}}function R(w){r(w),k(w);var B=document.getElementById(w.tbody);if(!(!B||B._reconBatchWatched)){B._reconBatchWatched=!0;var z=new MutationObserver(function(){k(w)});z.observe(B,{childList:!0,subtree:!1})}}function D(){o(),s.forEach(R),document.querySelectorAll(".recon-batch-bar").forEach(function(w){try{w.remove()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",D):D(),setTimeout(D,1500),setTimeout(D,4e3),document.addEventListener("keydown",function(w){w.key==="Escape"&&s.forEach(function(B){f(B).length>0&&E(B)})}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-batch-thead",function(){s.forEach(v)})})();(function(){let e={role:"",monthly_volume:"",country:"",line_id:""},n=1;const a=4,s="pilot_ob_dismiss",o="pilot_ob_done";window.maybeShowOnboarding=function(f){};function m(f){n=f;for(let v=1;v<=a;v++){const E=document.getElementById("ob-step-"+v);E&&(E.style.display=v===f?"block":"none")}document.querySelectorAll(".ob-dot").forEach(v=>{const E=parseInt(v.dataset.step,10);v.classList.toggle("active",E===f),v.classList.toggle("done",E<f)});const u=document.getElementById("ob-step-label");u&&(u.textContent=f+" / "+a);const c=document.getElementById("ob-next");if(c&&(c.textContent=f===a?t("ob-finish"):t("ob-next")),f===4){const v=document.getElementById("ob-line-input");v&&(v.value=e.line_id||"")}}function r(f){const u=document.querySelector(".onboarding-modal");if(!u)return;let c=u.querySelector(".ob-feedback");c||(c=document.createElement("div"),c.className="ob-feedback",u.appendChild(c)),c.textContent=f,c.classList.add("show"),setTimeout(()=>c.classList.remove("show"),1800)}document.addEventListener("click",f=>{const u=f.target.closest(".ob-option");if(!u)return;const c=u.parentElement;if(!c||!c.classList.contains("ob-options"))return;c.querySelectorAll(".ob-option").forEach(E=>E.classList.remove("selected")),u.classList.add("selected");const v=u.dataset.value;c.id==="ob-role-options"?e.role=v:c.id==="ob-volume-options"?e.monthly_volume=v:c.id==="ob-country-options"&&(e.country=v)}),document.addEventListener("click",f=>{f.target.id==="ob-skip"&&k()}),document.addEventListener("click",f=>{if(f.target.id==="ob-next"){if(n===4){const u=document.getElementById("ob-line-input");e.line_id=(u&&u.value||"").trim().replace(/^@+/,"")}k()}}),document.addEventListener("click",f=>{if(f.target.closest("#ob-close")){localStorage.setItem(s,String(Date.now()));const u=document.getElementById("onboarding-modal");u&&(u.style.display="none")}});function k(){n===1&&e.role?r(t("ob-fb-role")):n===2&&e.monthly_volume?r(t("ob-fb-volume")):n===3&&e.country?r(t("ob-fb-country")):n===4&&e.line_id&&r(t("ob-fb-line")),n<a?setTimeout(()=>m(n+1),e[Object.keys(e)[n-1]]?350:0):i()}async function i(){const f=document.getElementById("onboarding-modal");localStorage.setItem(o,"1"),localStorage.removeItem(s);const u={};if(e.role&&(u.role=e.role),e.monthly_volume&&(u.monthly_volume=e.monthly_volume),e.country&&(u.country=e.country),e.line_id&&(u.line_id=e.line_id),Object.keys(u).length===0){f&&(f.style.display="none");return}try{const c=await fetch("/api/me/profile",{method:"PUT",headers:{Authorization:"Bearer "+(window.token||localStorage.getItem("mrpilot_token")),"Content-Type":"application/json"},body:JSON.stringify(u)});c.ok?(r(t("ob-fb-done")),window._userInfo&&Object.assign(window._userInfo,u),setTimeout(()=>{f&&(f.style.display="none")},1200)):(localStorage.setItem("pilot_ob_pending",JSON.stringify(u)),console.warn("onboarding profile save failed",c.status),r(t("ob-fb-saved-local")),setTimeout(()=>{f&&(f.style.display="none")},1500))}catch(c){console.error("onboarding submit",c),localStorage.setItem("pilot_ob_pending",JSON.stringify(u)),f&&(f.style.display="none")}}})();(function(){const e=document.getElementById("archive-rule-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
        <div class="modal modal-lg">
            <div class="modal-head">
                <div class="modal-title" data-i18n="settings-archive">归档命名</div>
                <button class="modal-close" id="archive-rule-modal-close" aria-label="close">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                </button>
            </div>
            <div class="modal-body">
                <div id="archive-editor-card">
                    <div class="archive-editor-desc" data-i18n="archive-editor-desc">自定义识别后文件的命名规则和归档文件夹结构</div>
                    <!-- 当前规则 -->
                    <div class="archive-section">
                        <div class="archive-section-label" data-i18n="archive-current-rule">当前规则(点字段编辑 · 拖拽排序)</div>
                        <div class="archive-rule-canvas" id="archive-rule-canvas"></div>
                    </div>
                    <!-- 可添加的字段 -->
                    <div class="archive-section">
                        <div class="archive-section-label" data-i18n="archive-add-field">添加字段(点击加入规则)</div>
                        <div class="archive-field-palette" id="archive-field-palette"></div>
                    </div>
                    <!-- 实时预览 -->
                    <div class="archive-section">
                        <div class="archive-section-label" data-i18n="archive-preview">实时预览</div>
                        <div class="archive-preview-box">
                            <code id="archive-preview-name">-</code>
                            <div class="archive-preview-hint" id="archive-preview-hint"></div>
                        </div>
                    </div>
                    <!-- 文件夹策略 -->
                    <div class="archive-section">
                        <div class="archive-section-label" data-i18n="archive-folder-strategy">文件夹策略(批量下载 ZIP 时生效)</div>
                        <div class="archive-folder-options" id="archive-folder-options">
                            <label class="radio-opt"><input type="radio" name="folder-strategy" value="none"><span data-i18n="folder-strategy-none">不分文件夹</span></label>
                            <label class="radio-opt"><input type="radio" name="folder-strategy" value="by_month"><span data-i18n="folder-strategy-month">按月份(2026-04/)</span></label>
                            <label class="radio-opt"><input type="radio" name="folder-strategy" value="by_seller"><span data-i18n="folder-strategy-seller">按供应商(DHL/)</span></label>
                            <label class="radio-opt"><input type="radio" name="folder-strategy" value="by_month_seller"><span data-i18n="folder-strategy-both">按月份+供应商(2026-04/DHL/)</span></label>
                        </div>
                    </div>
                </div>
            </div>
            <div class="modal-foot">
                <button class="btn btn-ghost" id="btn-archive-reset" data-i18n="archive-reset">恢复默认</button>
                <button class="btn btn-primary" id="btn-archive-save" data-i18n="archive-save">保存</button>
            </div>
        </div>
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");a[n][o]&&(s.textContent=a[n][o])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const o=s.getAttribute("data-i18n-placeholder");a[n][o]&&(s.placeholder=a[n][o])}))}catch{}}})();(function(){const e=document.getElementById("archive-token-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
        <div class="modal" style="max-width:420px;">
            <div class="modal-head">
                <div class="modal-title" data-i18n="archive-token-title">编辑字段</div>
                <button class="modal-close" id="archive-token-close">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                </button>
            </div>
            <div class="modal-body" id="archive-token-body"></div>
            <div class="modal-foot">
                <button class="btn btn-danger btn-ghost" id="btn-archive-token-delete" data-i18n="archive-token-delete">删除此字段</button>
                <button class="btn btn-primary" id="btn-archive-token-ok" data-i18n="archive-token-ok">确定</button>
            </div>
        </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");a[n][o]&&(s.textContent=a[n][o])})}catch{}}})();(function(){let e=[],n="by_month_seller",a=-1,s=!1;const o={date:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="3.5" width="11" height="10" rx="1.5"/><path d="M2.5 6.5h11M5.5 2v3M10.5 2v3"/></svg>',seller:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13.5V4a1 1 0 011-1h5a1 1 0 011 1v9.5"/><path d="M10 7h2.5a.5.5 0 01.5.5v6"/><path d="M5 6h1M5 9h1M5 12h1M13.5 13.5h-12"/></svg>',category:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 2h6L13 5.5v7.5a1 1 0 01-1 1H3.5a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M9 2v4h4"/><path d="M5 9h6M5 11.5h4"/></svg>',amount:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M8 4.5v7M10 6.3a1.8 1.8 0 00-4 0c0 .9.7 1.3 2 1.6s2 .8 2 1.6a1.8 1.8 0 01-4 0"/></svg>',invoice:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3.5l1.5 10.5 1.5-1 1.5 1 1.5-1 1.5 1 1.5-1 1.5 1L13 3.5z"/><path d="M5.5 6.5h5M5.5 9h5M5.5 11.5h3"/></svg>',buyer:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="6" r="2.5"/><path d="M3 13.5c0-2.5 2.2-4.5 5-4.5s5 2 5 4.5"/></svg>',sep:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v10"/></svg>'},m={date:{label:"field-date",defaultCfg:{format:"YYYY-MM-DD"}},seller:{label:"field-seller",defaultCfg:{short:!0}},category:{label:"field-category",defaultCfg:{}},amount:{label:"field-amount",defaultCfg:{with_currency:!0}},invoice:{label:"field-invoice",defaultCfg:{}},buyer:{label:"field-buyer",defaultCfg:{}},sep:{label:"field-sep",defaultCfg:{val:"_"}}};function r(){return{zh:"运费",en:"Shipping",th:"ค่าขนส่ง",ja:"送料"}[currentLang]||"Shipping"}function k(){return"DHL Express (Thailand) Co., Ltd."}function i(){return{merged_fields:{invoice_date:"2026-04-15",seller_name:k(),category:r(),total_amount:1250,currency:"THB",invoice_no:"INV-2026030002",buyer_name:"Mr.ERP Co., Ltd."}}}window.loadAboutPanel=()=>f(),window.loadPrefsSettings=()=>u(),window.loadArchiveSettings=()=>v();function f(){const g=document.getElementById("settings-contact-grid");if(!g)return;const d=_contact?.phone||"086-889-2228",h=_contact?.line_id||"@Pearnly",I=_contact?.line_url||"https://line.me/R/ti/p/@059oupmg",L=_contact?.email||"hello@pearnly.com",H=_contact?.address||"Bangkok, Thailand";g.innerHTML=`
            <a class="contact-item" href="${escapeHtml(I)}" target="_blank" rel="noopener">
                <div class="contact-icon line">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.365 9.863c.349 0 .63.285.631.631 0 .345-.282.63-.631.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.282.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63.346 0 .628.285.628.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-line"))}</div>
                    <div class="contact-value">${escapeHtml(h)}</div>
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
            <a class="contact-item" href="tel:${escapeHtml(d.replace(/[^\d+]/g,""))}">
                <div class="contact-icon phone">
                    <svg viewBox="0 0 20 20" fill="currentColor"><path d="M2 3a1 1 0 011-1h2.5a1 1 0 01.97.757l1 4a1 1 0 01-.29.986l-1.75 1.75a11 11 0 005.07 5.07l1.75-1.75a1 1 0 01.986-.29l4 1a1 1 0 01.757.97V17a1 1 0 01-1 1h-1C8.82 18 2 11.18 2 3V3z"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-phone"))}</div>
                    <div class="contact-value">${escapeHtml(d)}</div>
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
        `}async function u(){try{const g=await fetch("/api/settings/dup-check",{headers:{Authorization:"Bearer "+token}});if(!g.ok)return;const d=await g.json(),h=document.getElementById("pref-dup-check");h&&(h.checked=!!d.enabled)}catch(g){console.warn("load prefs failed",g)}}const c=document.getElementById("pref-dup-check");c&&!c.dataset.bound&&(c.dataset.bound="1",c.addEventListener("change",async g=>{const d=g.target.checked;try{(await fetch("/api/settings/dup-check",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({enabled:d})})).ok?showToast(d?t("pref-dup-check-on-toast"):t("pref-dup-check-off-toast"),"success"):(g.target.checked=!d,showToast(t("pref-save-failed"),"error"))}catch{g.target.checked=!d,showToast(t("pref-save-failed"),"error")}}));async function v(){const g=!!(_userInfo&&_userInfo.can_customize_archive);s=!g;const d=document.getElementById("archive-upgrade-banner");d&&(d.style.display=g?"none":"");const h=document.getElementById("archive-plus-badge");h&&(h.style.display=g?"none":"");try{const I=await fetch("/api/archive/settings",{headers:{Authorization:"Bearer "+token}});if(!I.ok)throw new Error("load failed");const L=await I.json();e=Array.isArray(L.name_template)?L.name_template:[],n=L.folder_strategy||"by_month_seller"}catch(I){console.error("load archive settings failed",I),showToast(t("archive-load-failed"),"error");return}E(),x(),R(),D()}function E(){const g=document.getElementById("archive-rule-canvas");if(g){if(e.length===0){g.innerHTML=`<div class="archive-empty">${escapeHtml(t("archive-rule-empty"))}</div>`;return}g.innerHTML=e.map((d,h)=>{const I=m[d.type]||{label:d.type},L=o[d.type]||"",H=d.type==="sep"?`"${escapeHtml(d.val||"_")}"`:escapeHtml(t(I.label));return`
                <span class="archive-token ${d.type}"
                      data-token-idx="${h}"
                      draggable="${s?"false":"true"}">
                    <span class="token-icon">${L}</span>
                    <span class="token-label">${H}</span>
                </span>
            `}).join("")}}function x(){const g=document.getElementById("archive-field-palette");if(!g)return;const d=["date","seller","category","amount","invoice","buyer","sep"];g.innerHTML=d.map(h=>{const I=m[h],L=o[h]||"";return`
                <button class="archive-palette-btn ${h}" data-add-field="${h}" ${s?"disabled":""}>
                    <span class="token-icon">${L}</span>
                    <span>${escapeHtml(t(I.label))}</span>
                </button>
            `}).join("")}function R(){document.querySelectorAll('input[name="folder-strategy"]').forEach(g=>{g.checked=g.value===n,g.disabled=s})}async function D(){const g=document.getElementById("archive-preview-name"),d=document.getElementById("archive-preview-hint");if(d&&(d.textContent=t("archive-preview-hint",{category:r()})),!!g){if(e.length===0){g.textContent="-";return}try{const I=await(await fetch("/api/archive/rename-preview",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({merged_fields:i().merged_fields,name_template:e})})).json();g.textContent=(I.name||"-")+".pdf"}catch{g.textContent="("+t("archive-preview-error")+")"}}}window._rerenderArchiveAll=function(){const g=document.getElementById("archive-rule-modal");!g||g.style.display==="none"||(E(),x(),D())};let w=-1;document.addEventListener("dragstart",g=>{const d=g.target.closest(".archive-token");!d||s||(w=parseInt(d.dataset.tokenIdx,10),d.classList.add("dragging"),g.dataTransfer.effectAllowed="move")}),document.addEventListener("dragend",g=>{document.querySelectorAll(".archive-token").forEach(d=>d.classList.remove("dragging","drop-target")),w=-1}),document.addEventListener("dragover",g=>{const d=g.target.closest(".archive-token");d&&(g.preventDefault(),g.dataTransfer.dropEffect="move",document.querySelectorAll(".archive-token").forEach(h=>h.classList.remove("drop-target")),d.classList.add("drop-target"))}),document.addEventListener("drop",g=>{const d=g.target.closest(".archive-token");if(!d||w<0||s)return;g.preventDefault();const h=parseInt(d.dataset.tokenIdx,10);if(h===w)return;const I=e.splice(w,1)[0];e.splice(h,0,I),w=-1,E(),D()}),document.addEventListener("click",g=>{if(g.target.closest("#btn-open-archive-rule")||g.target.closest("#btn-open-archive-rule-from-settings")){const L=document.getElementById("archive-rule-modal");L&&(L.style.display="",v());return}if(g.target.closest("#archive-rule-modal-close")||g.target.id==="archive-rule-modal"){const L=document.getElementById("archive-rule-modal");L&&(L.style.display="none");return}const d=g.target.closest(".settings-nav-item");if(d){switchSettingsTab(d.dataset.settingsTab);return}if(s&&g.target.closest(".archive-token, [data-add-field], #btn-archive-save, #btn-archive-reset")){showToast(t("feature-contact-us"),"info");return}const h=g.target.closest("[data-add-field]");if(h){const L=h.dataset.addField,H=m[L],_={type:L,...H.defaultCfg};e.push(_),E(),D();return}const I=g.target.closest(".archive-token");if(I&&!s){B(parseInt(I.dataset.tokenIdx,10));return}if(g.target.closest("#btn-archive-save"))return F();if(g.target.closest("#btn-archive-reset"))return A();(g.target.closest("#archive-token-close")||g.target.id==="archive-token-modal")&&(document.getElementById("archive-token-modal").style.display="none"),g.target.closest("#btn-archive-token-ok")&&z(),g.target.closest("#btn-archive-token-delete")&&q()}),document.addEventListener("change",g=>{g.target.name==="folder-strategy"&&(n=g.target.value)});function B(g){a=g;const d=e[g];if(!d)return;const h=document.getElementById("archive-token-body");let I="";d.type==="date"?I=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-date-format"))}</label>
                    <select class="form-input" id="token-date-format">
                        <option value="YYYY-MM-DD" ${d.format==="YYYY-MM-DD"?"selected":""}>YYYY-MM-DD (2026-04-15)</option>
                        <option value="YYYYMMDD"   ${d.format==="YYYYMMDD"?"selected":""}>YYYYMMDD (20260415)</option>
                        <option value="YY.MM"      ${d.format==="YY.MM"?"selected":""}>YY.MM (26.04)</option>
                        <option value="YYYY年MM月" ${d.format==="YYYY年MM月"?"selected":""}>YYYY年MM月 (2026年04月)</option>
                    </select>
                </div>`:d.type==="seller"?I=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-seller-short" ${d.short?"checked":""}> ${escapeHtml(t("archive-seller-short"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-seller-short-hint"))}</div>
                </div>`:d.type==="amount"?I=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-amount-currency" ${d.with_currency?"checked":""}> ${escapeHtml(t("archive-amount-currency"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-amount-currency-hint"))}</div>
                </div>`:d.type==="sep"?I=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-sep-val"))}</label>
                    <div class="sep-options">
                        <button type="button" class="sep-chip ${d.val==="_"?"active":""}" data-sep="_">_ (下划线)</button>
                        <button type="button" class="sep-chip ${d.val==="-"?"active":""}" data-sep="-">- (短横)</button>
                        <button type="button" class="sep-chip ${d.val===" "?"active":""}" data-sep=" ">(空格)</button>
                        <input type="text" id="token-sep-custom" class="form-input sep-custom" maxlength="3" placeholder="${escapeHtml(t("archive-sep-custom"))}" value="${["_","-"," "].includes(d.val)?"":escapeHtml(d.val||"")}">
                    </div>
                </div>`:I=`<div class="form-hint">${escapeHtml(t("archive-token-no-option"))}</div>`,h.innerHTML=I,document.getElementById("archive-token-modal").style.display="",h.querySelectorAll(".sep-chip").forEach(L=>{L.addEventListener("click",()=>{h.querySelectorAll(".sep-chip").forEach(_=>_.classList.remove("active")),L.classList.add("active");const H=document.getElementById("token-sep-custom");H&&(H.value="")})})}function z(){const g=e[a];if(g){if(g.type==="date")g.format=document.getElementById("token-date-format").value;else if(g.type==="seller")g.short=document.getElementById("token-seller-short").checked;else if(g.type==="amount")g.with_currency=document.getElementById("token-amount-currency").checked;else if(g.type==="sep"){const d=document.querySelector("#archive-token-body .sep-chip.active"),h=document.getElementById("token-sep-custom").value;g.val=h||(d?d.dataset.sep:"_")}document.getElementById("archive-token-modal").style.display="none",E(),D()}}function q(){a<0||(e.splice(a,1),document.getElementById("archive-token-modal").style.display="none",E(),D())}async function F(){if(e.length===0){showToast(t("archive-rule-cannot-empty"),"error");return}try{if(!(await fetch("/api/archive/settings",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({name_template:e,folder_strategy:n})})).ok)throw new Error("save failed");showToast(t("archive-save-ok"),"success");const d=document.getElementById("archive-rule-modal");d&&(d.style.display="none")}catch{showToast(t("archive-save-fail"),"error")}}async function A(){await showConfirm(t("archive-reset-confirm"),{danger:!0})&&(e=[{type:"date",format:"YYYY-MM-DD"},{type:"sep",val:"_"},{type:"seller",short:!0},{type:"sep",val:"_"},{type:"category"},{type:"sep",val:"_"},{type:"amount",with_currency:!0}],n="by_month_seller",E(),R(),D())}})();(function(){const s="pearnly_big_batch_tip_shown";let o=null,m=null,r=0,k=0,i=!1;function f(B){const z=typeof t=="function"?t("big-batch-unload-warn"):"Batch OCR running · close anyway?";return B.preventDefault(),B.returnValue=z,z}function u(){i||(i=!0,window.addEventListener("beforeunload",f))}function c(){i&&(i=!1,window.removeEventListener("beforeunload",f))}function v(){if(document.getElementById("big-batch-progress"))return;const B=document.getElementById("file-list");if(!B||!B.parentNode)return;const z=document.createElement("div");z.id="big-batch-progress",z.className="big-batch-progress",z.innerHTML='<div class="bbp-row"><svg class="bbp-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.5"/><path d="M8 4.5v3.5l2.5 1.5"/></svg><span class="bbp-text" id="bbp-text"></span></div><div class="bbp-track"><div class="bbp-fill" id="bbp-fill" style="width:0%"></div></div>',B.parentNode.insertBefore(z,B);const q=document.getElementById("bbp-text");q&&(q.textContent=typeof t=="function"?t("big-batch-progress-init"):"Starting...")}function E(){const B=document.getElementById("big-batch-progress");B&&B.remove()}function x(){if(!m)return;let B=0;for(let I=0;I<m.length;I++){const L=m[I].status;(L==="success"||L==="error"||L==="cancelled")&&B++}const z=r,q=z>0?Math.min(100,Math.floor(100*B/z)):0,F=(Date.now()-k)/1e3;let A;if(B>=3&&F>1){const I=F/B;A=(z-B)*I}else A=(z-B)*6/6;const g=Math.max(1,Math.ceil(A/60)),d=document.getElementById("bbp-fill"),h=document.getElementById("bbp-text");d&&(d.style.width=q+"%"),h&&(B>=z?h.textContent=t("big-batch-progress-done").replace("{total}",z):h.textContent=t("big-batch-progress-running").replace("{done}",B).replace("{total}",z).replace("{min}",g))}function R(B){try{if(localStorage.getItem(s)==="1")return}catch{}const z=Math.max(1,Math.ceil(B*6/6/60)),q=t("big-batch-first-tip").replace("{n}",B).replace("{min}",z);typeof showToast=="function"&&showToast(q,"info",8e3);try{localStorage.setItem(s,"1")}catch{}}function D(B){!B||B.length<100||(m=B,r=B.length,k=Date.now(),v(),u(),R(r),o&&clearInterval(o),o=setInterval(x,250),x())}function w(){o&&(clearInterval(o),o=null),c(),m&&r>=100?(x(),setTimeout(E,1200)):E(),m=null,r=0}window._bigBatchStart=D,window._bigBatchStop=w,typeof window.subscribeI18n=="function"&&window.subscribeI18n("big-batch-progress",function(){m&&x()})})();(function(){let e=null,n=!1,a=!1;function s(d){return typeof escapeHtml=="function"?escapeHtml(d==null?"":String(d)):String(d??"")}function o(d,h){try{typeof showToast=="function"&&showToast(d,h||"info")}catch{}}function m(){const d=typeof _userInfo<"u"?_userInfo:null;return!!(d&&(d.role==="owner"||d.is_super_admin))}function r(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function k(d){if(!d)return!1;const h=String(d.status||"").toLowerCase();return h==="exception"||h==="exception_pending"||h==="rejected"}async function i(d){if(n&&!d)return e;const h=localStorage.getItem("mrpilot_token");if(!h)return null;try{const I=await fetch("/api/erp/xero/status",{headers:{Authorization:"Bearer "+h}});if(!I.ok)throw new Error("http_"+I.status);e=await I.json(),n=!0}catch{e={configured:!1,connected:!1,organisations:[]},n=!1}return e}function f(){const d=document.getElementById("erp-connect-cards");if(!d)return;const h=e;let I,L=!1;h?h.configured?h.connected?(L=!0,I='<span class="mrerp-card-pill mrerp-pill-ok">'+s(t("xero-card-connected"))+"</span>"):I='<span class="mrerp-card-pill mrerp-pill-neutral">'+s(t("xero-card-not-connected"))+"</span>":I='<span class="mrerp-card-pill mrerp-pill-neutral">'+s(t("xero-card-not-configured"))+"</span>":I='<span class="mrerp-card-pill mrerp-pill-neutral">'+s(t("xero-card-not-connected"))+"</span>";let H="";if(!h||!h.configured)H='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+s(t("xero-connect-btn"))+"</button>";else if(!h.connected)m()&&(H='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+s(t("xero-connect-btn"))+"</button>");else{const y=!!h.auto_push,p=y?t("card-btn-disable"):t("card-btn-enable");H='<button type="button" class="'+(y?"mrerp-card-toggle mrerp-card-toggle-disable":"mrerp-card-toggle mrerp-card-toggle-enable")+'" id="btn-xero-toggle-enabled" data-xero-enabled="'+(y?"1":"0")+'" title="'+s(y?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip"))+'">'+s(p)+'</button><button type="button" class="int-btn-configure" id="btn-xero-edit-toggle">'+s(t("card-btn-edit"))+"</button>"}const _=h&&h.connected?"xero-card-desc-connected":"xero-card-desc-default",M=h&&h.connected?t("xero-card-connected")||"Connected · default org will receive pushes":"Cloud accounting · push invoices to your default Xero org",K=(function(){const y=t(_);return y===_?M:y})();let G='<div class="integration-row erp-connect-xero'+(L?" connected":"")+'"><div class="int-icon ic-xero"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="9" cy="10" r="1.3" fill="currentColor"/><circle cx="15" cy="14" r="1.3" fill="currentColor"/><path d="M9 14l6-4"/></svg></div><div class="int-info"><div class="int-name"><span>'+s(t("xero-card-title")||"Xero")+"</span>"+I+'</div><div class="int-desc">'+s(K)+'</div></div><div class="int-actions">'+H+"</div></div>";if(h&&h.configured&&h.connected&&m()){const y=h.organisations||[];let p="";if(y.length>0){p+='<div class="erp-cc-meta">'+s((t("xero-org-count")||"").replace("{n}",String(y.length)))+"</div>",p+='<div class="erp-cc-org-label">'+s(t("xero-default-org"))+":</div>",p+='<div class="erp-cc-orgs">',y.forEach(function(Y){p+='<label class="erp-cc-org-row"><input type="radio" name="xero-default-org" value="'+s(Y.id)+'"'+(Y.is_default?" checked":"")+'><span class="erp-cc-org-name">'+s(Y.organisation_name||Y.organisation_id)+"</span></label>"}),p+="</div>";const $=!!h.auto_push,P=$?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip");p+='<div class="erp-cc-auto-push" title="'+s(P)+'"><label class="erp-cc-toggle"><input type="checkbox" id="xero-auto-push-toggle"'+($?" checked":"")+'><span class="erp-cc-toggle-slider"></span><span class="erp-cc-toggle-label">'+s(t("erp-auto-push-label"))+"</span></label></div>",p+='<div class="erp-cc-actions"><button class="btn btn-ghost btn-tiny" type="button" id="btn-xero-disconnect">'+s(t("xero-disconnect-btn"))+"</button></div>"}G+='<div class="erp-xero-details" id="erp-xero-details" style="display:none; margin:8px 0 16px; padding:12px 14px; border:1px solid var(--line); border-radius:8px; background:var(--bg);">'+p+"</div>"}const W=d.querySelector(".erp-connect-xero"),te=d.querySelector("#erp-xero-details");te&&te.remove(),W?W.outerHTML=G:d.insertAdjacentHTML("afterbegin",G);const re=document.getElementById("btn-xero-edit-toggle");re&&re.addEventListener("click",function(y){y.preventDefault();const p=document.getElementById("erp-xero-details");p&&(p.style.display=p.style.display==="none"?"":"none")});const S=document.getElementById("btn-xero-toggle-enabled");S&&S.addEventListener("click",async function(y){if(y.preventDefault(),S.disabled)return;const $=!(S.getAttribute("data-xero-enabled")==="1");if(!$)try{if(!await window.pearnlyConfirm(t("card-toggle-disable-confirm")))return}catch{}S.disabled=!0,await E($,null)})}async function u(){const d=localStorage.getItem("mrpilot_token");if(d)try{const h=await fetch("/api/erp/xero/auth/start",{method:"GET",headers:{Authorization:"Bearer "+d}});if(!h.ok){let L="unknown";try{L=(await h.json()).detail||"unknown"}catch{}const H=String(L).replace(/^xero\./,"").toLowerCase();o(t("xero-push-fail").replace("{err}",t("xero-err-"+H)||L),"error");return}const I=await h.json();I.redirect_url&&(window.location.href=I.redirect_url)}catch(h){o(t("xero-push-fail").replace("{err}",h.message||"network"),"error")}}async function c(){if(!await window.pearnlyConfirm(t("xero-disconnect-confirm")))return;const h=localStorage.getItem("mrpilot_token");try{const I=await fetch("/api/erp/xero/disconnect",{method:"POST",headers:{Authorization:"Bearer "+h}});if(!I.ok)throw new Error("http_"+I.status);await i(!0),f()}catch(I){o(t("xero-push-fail").replace("{err}",I.message),"error")}}async function v(d){const h=localStorage.getItem("mrpilot_token");try{const I=await fetch("/api/erp/xero/select_org",{method:"POST",headers:{Authorization:"Bearer "+h,"Content-Type":"application/json"},body:JSON.stringify({token_id:d})});if(!I.ok)throw new Error("http_"+I.status);await i(!0),f()}catch(I){o(t("xero-push-fail").replace("{err}",I.message),"error")}}async function E(d,h){const I=localStorage.getItem("mrpilot_token");h&&(h.disabled=!0);try{const L=await fetch("/api/erp/xero/auto-push",{method:"POST",headers:{Authorization:"Bearer "+I,"Content-Type":"application/json"},body:JSON.stringify({on:!!d})});if(!L.ok){let H="unknown";try{H=(await L.json()).detail||"unknown"}catch{}throw new Error(H)}o(d?t("erp-auto-push-toggled-on"):t("erp-auto-push-toggled-off"),"success"),n=!1,await i(!0),f()}catch(L){h&&(h.checked=!d),o(t("erp-auto-push-toggle-fail").replace("{err}",L.message||"network"),"error")}finally{h&&(h.disabled=!1)}}async function x(){const d=document.getElementById("drawer-history-save");if(!d||d.querySelector("#btn-xero-push")||d.querySelector("#pn-push-wrap")||(await i(!1),d.querySelector("#pn-push-wrap"))||d.querySelector("#btn-xero-push"))return;const h=r();if(!(h&&(h._historyId||h.history_id)))return;let L=!1,H="xero-push-tip";!e||!e.configured?(L=!0,H="xero-err-not_configured"):e.connected?k(h)&&(L=!0,H="xero-push-disabled-exc"):(L=!0,H="xero-push-disabled-no-conn");const _=document.createElement("button");_.type="button",_.id="btn-xero-push",_.className="btn btn-ghost"+(L?" disabled":""),_.disabled=L,_.title=t(H)||"",_.innerHTML='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5 8l2 2 4-4"/></svg><span style="margin-left:4px;">'+s(t("xero-push-btn"))+"</span>",_.addEventListener("click",R);const M=document.getElementById("btn-push-erp");M&&M.parentNode?M.parentNode.insertBefore(_,M.nextSibling):d.insertBefore(_,d.firstChild)}async function R(){const d=r(),h=d&&(d._historyId||d.history_id);if(!h)return;const I=document.getElementById("btn-xero-push");I&&(I.disabled=!0,I.classList.add("loading"));const L=localStorage.getItem("mrpilot_token");try{const H=await fetch("/api/erp/xero/push/"+encodeURIComponent(h),{method:"POST",headers:{Authorization:"Bearer "+L}});if(!H.ok){let _="unknown";try{_=(await H.json()).detail||"unknown"}catch{}const M=String(_).replace(/^xero\./,"").toLowerCase(),K=t("xero-"+M),G=K&&K!=="xero-"+M?K:_;o(t("xero-push-fail").replace("{err}",G),"error");return}o(t("xero-push-ok"),"success")}catch(H){o(t("xero-push-fail").replace("{err}",H.message||"network"),"error")}finally{I&&(I.disabled=!1,I.classList.remove("loading"))}}async function D(){await i(!0),f(),w()}async function w(){const d=document.getElementById("erp-global-push-mode");if(!d)return;const h=localStorage.getItem("mrpilot_token");if(h)try{const I=await fetch("/api/settings/erp-push-mode",{headers:{Authorization:"Bearer "+h}});if(I.ok){const L=await I.json();L.mode&&(d.value=L.mode,d.dataset.prev=L.mode)}}catch{}}async function B(d){const h=d.value,I=localStorage.getItem("mrpilot_token");try{(await fetch("/api/settings/erp-push-mode",{method:"PUT",headers:{Authorization:"Bearer "+I,"Content-Type":"application/json"},body:JSON.stringify({mode:h})})).ok?(d.dataset.prev=h,o(t("pref-erp-mode-saved"),"success")):(d.value=d.dataset.prev||"smart",o(t("pref-save-failed"),"error"))}catch{d.value=d.dataset.prev||"smart",o(t("pref-save-failed"),"error")}}function z(){try{const d=String(window.location.hash||"");if(d.indexOf("xero=ok")>=0){const h=d.match(/n=(\d+)/),I=h?h[1]:"1";o((t("xero-toast-redirected-ok")||"").replace("{n}",I),"success"),history.replaceState(null,"",window.location.pathname+"#automation"),i(!0).then(f)}else d.indexOf("xero=err")>=0&&(o(t("xero-toast-redirected-err"),"error"),history.replaceState(null,"",window.location.pathname+"#automation"))}catch{}}function q(){if(a)return;a=!0,document.addEventListener("click",function(h){if(h.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(D,50);return}if(h.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(D,80);return}if(h.target.closest("#btn-xero-connect")){h.preventDefault(),u();return}if(h.target.closest("#btn-xero-disconnect")){h.preventDefault(),c();return}}),document.addEventListener("change",function(h){h.target&&h.target.matches('input[name="xero-default-org"]')&&v(h.target.value),h.target&&h.target.id==="xero-auto-push-toggle"&&E(h.target.checked,h.target),h.target&&h.target.id==="erp-global-push-mode"&&B(h.target)});const d=function(){return document.getElementById("drawer-body")};try{const h=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("btn-xero-push")&&x()}),I=d();if(I)h.observe(I,{childList:!0,subtree:!0});else{const L=new MutationObserver(function(){const H=d();H&&(h.observe(H,{childList:!0,subtree:!0}),L.disconnect())});L.observe(document.body,{childList:!0,subtree:!0})}}catch{}setTimeout(z,500)}function F(){e&&f();const d=document.getElementById("btn-xero-push");if(d){const h=d.querySelector("span");h&&(h.textContent=t("xero-push-btn"))}}q(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("xero-adapter",F);async function A(d){const h=Date.now();for(;Date.now()-h<d;){if(typeof _userInfo<"u"&&_userInfo&&_userInfo.id)return _userInfo;await new Promise(I=>setTimeout(I,80))}return null}async function g(){await A(5e3);const d=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),h=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');d&&h&&await D()}setTimeout(g,200)})();(function(){const e={};function n(){if(document.getElementById("report-modal"))return;const f=`
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
        </div>`,u=document.createElement("div");u.innerHTML=f,document.body.appendChild(u.firstElementChild),document.getElementById("report-modal-close-x").addEventListener("click",a),document.getElementById("report-modal-cancel").addEventListener("click",a),document.getElementById("report-modal").addEventListener("click",c=>{c.target.id==="report-modal"&&a()})}function a(){const f=document.getElementById("report-modal");f&&(f.style.display="none"),s=null}let s=null;async function o(f,u){const c=f+":"+(u||"");if(e[c])return e[c];let v;try{const E=localStorage.getItem("mrpilot_token"),x=await fetch(`/api/reports/templates?lang=${encodeURIComponent(f)}`,{headers:{Authorization:"Bearer "+E}});if(!x.ok)throw new Error("templates fetch failed");v=(await x.json()).templates||[]}catch(E){console.error("fetchTemplates fail",E),v=[{code:"input_vat",name:t("tpl-input-vat"),desc:t("tpl-input-vat-desc"),recommended:!0},{code:"standard",name:t("tpl-standard"),desc:t("tpl-standard-desc"),recommended:!1},{code:"print",name:t("tpl-print"),desc:t("tpl-print-desc"),recommended:!1}]}if(v=v.filter(E=>E.code!=="erp"),u==="history-batch"){const E=v.findIndex(R=>R.code==="standard"),x=E>=0?E+1:v.length;v.splice(x,0,{code:"sales_detail_th",name:t("export-tpl-sales-detail"),desc:t("export-tpl-sales-detail-desc"),recommended:!1,is_new:!0})}return e[c]=v,v}function m(f){const u=document.getElementById("report-tpl-list"),c=f.map((E,x)=>`
            <label class="report-tpl-item${E.recommended?" is-recommended":""}">
                <input type="radio" name="report-tpl" value="${E.code}" ${E.recommended||x===0?"checked":""}>
                <div class="report-tpl-content">
                    <div class="report-tpl-name">
                        ${r(E.name)}
                        ${E.recommended?`<span class="report-tpl-badge">${r(t("report-recommended"))}</span>`:""}
                    </div>
                    <div class="report-tpl-desc">${r(E.desc||"")}</div>
                </div>
            </label>
        `).join(""),v=`
            <label class="report-tpl-item report-tpl-coming" title="${r(t("tpl-custom-coming"))}">
                <input type="radio" name="report-tpl" disabled>
                <div class="report-tpl-content">
                    <div class="report-tpl-name">
                        + ${r(t("tpl-custom-new"))}
                        <span class="report-tpl-badge report-tpl-badge-soon">${r(t("cs-coming-soon"))}</span>
                    </div>
                    <div class="report-tpl-desc">${r(t("tpl-custom-desc"))}</div>
                </div>
            </label>
        `;u.innerHTML=c+v}function r(f){return f==null?"":String(f).replace(/[&<>"']/g,u=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[u])}function k(f){const u=new Date,c=u.getFullYear(),v=u.getMonth()+1;if(f==="all")return"all";if(f==="this-month")return`${c}-${String(v).padStart(2,"0")}`;if(f==="last-month"){const E=new Date(c,v-2,1);return`${E.getFullYear()}-${String(E.getMonth()+1).padStart(2,"0")}`}return f==="this-year"?`${c}`:f==="this-quarter"?`${c}-Q${Math.floor((v-1)/3)+1}`:"all"}window.openReportModal=async function(f){f=f||{},n(),typeof applyLang=="function"?applyLang(currentLang):document.querySelectorAll("#report-modal [data-i18n]").forEach(R=>{const D=R.getAttribute("data-i18n");I18N[currentLang]&&I18N[currentLang][D]&&(R.textContent=I18N[currentLang][D])});const u=document.getElementById("report-period-section");u&&(u.style.display=f.mode==="client"?"":"none");const c=document.getElementById("report-tpl-list");c.innerHTML=`<div class="report-tpl-loading">${r(t("report-modal-loading"))}</div>`,document.getElementById("report-modal").style.display="";const v=await o(currentLang,f&&f.mode);m(v),s=f;const E=document.getElementById("report-modal-download"),x=E.cloneNode(!0);E.parentNode.replaceChild(x,E),x.addEventListener("click",()=>i(s))};async function i(f){if(!f)return;const u=document.querySelector('input[name="report-tpl"]:checked');if(!u){showToast(t("report-toast-no-selection"),"info");return}const c=u.value,v=document.querySelector('input[name="report-period"]:checked'),E=v?v.value:"all",x=k(E),R=document.getElementById("report-modal-download"),D=R.innerHTML;R.disabled=!0,R.innerHTML=`<span>${r(t("report-modal-loading"))}</span>`;try{const w=localStorage.getItem("mrpilot_token");let B,z;if(f.mode==="records")B=await fetch("/api/reports/export",{method:"POST",headers:{Authorization:"Bearer "+w,"Content-Type":"application/json"},body:JSON.stringify({template:c,lang:currentLang,records:f.records||[],meta:f.meta||{}})}),z=`mrpilot-${c}-${Date.now()}.xlsx`;else if(f.mode==="client"){const I=`/api/reports/clients/${f.clientId}/export?template=${encodeURIComponent(c)}&lang=${encodeURIComponent(currentLang)}&month=${encodeURIComponent(x)}`;B=await fetch(I,{headers:{Authorization:"Bearer "+w}}),z=`${(f.clientName||"client").replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40)}-${c}.xlsx`}else if(f.mode==="history-batch")c==="sales_detail_th"?(B=await fetch("/api/ocr/export-by-history-ids",{method:"POST",headers:{Authorization:"Bearer "+w,"Content-Type":"application/json"},body:JSON.stringify({template:"sales_detail_th",lang:currentLang,history_ids:f.historyIds||[],client_id:f.clientId||null})}),z=`Pearnly_SalesDetail_${Date.now()}.xlsx`):(B=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+w,"Content-Type":"application/json"},body:JSON.stringify({template:c,lang:currentLang,history_ids:f.historyIds||[],client_id:f.clientId||null})}),z=`mrpilot-batch-${c}-${Date.now()}.xlsx`);else throw new Error("unknown mode: "+f.mode);if(!B.ok){let I="HTTP "+B.status;try{const L=await B.json();L&&L.detail&&(I=L.detail)}catch(L){console.warn("[batch-export] resp.json err.detail parse failed:",L)}B.status===404?showToast(t("report-toast-empty"),"info"):showToast(t("report-toast-fail")+" · "+I,"error");return}const q=await B.blob();let F=z;const g=(B.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(g)try{F=decodeURIComponent(g[1])}catch{}const d=URL.createObjectURL(q),h=document.createElement("a");h.href=d,h.download=F,document.body.appendChild(h),h.click(),document.body.removeChild(h),URL.revokeObjectURL(d),showToast(t("report-toast-success"),"success"),a()}catch(w){console.error("doDownload fail",w),showToast(t("report-toast-fail")+" · "+(w.message||""),"error")}finally{R.disabled=!1,R.innerHTML=D}}document.addEventListener("DOMContentLoaded",()=>{const f=document.getElementById("btn-export");if(f){const c=f.cloneNode(!0);f.parentNode.replaceChild(c,f),c.addEventListener("click",()=>{if(typeof _results>"u"||!_results||_results.length===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"records",records:_results.map(v=>({filename:v.filename,merged_fields:v.merged_fields||{}}))})})}const u=document.getElementById("history-batch-export");u&&u.addEventListener("click",()=>{if(typeof _historySelected>"u"||_historySelected.size===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"history-batch",historyIds:Array.from(_historySelected)})})}),window.openClientExportModal=function(f,u){openReportModal({mode:"client",clientId:f,clientName:u||""})}})();(function(){const n=typeof window<"u"&&"showDirectoryPicker"in window,a=/\.(pdf|jpe?g|png|webp)$/i,s="mrpilot_folder_watcher",o=1;let m=null,r=null,k=null,i=60,f=!1,u=!1,c=0,v=0,E=0,x=[],R=null,D=!1;function w(){return m||(m=new Promise((b,C)=>{const T=indexedDB.open(s,o);T.onupgradeneeded=U=>{const N=U.target.result;N.objectStoreNames.contains("handles")||N.createObjectStore("handles"),N.objectStoreNames.contains("seen")||N.createObjectStore("seen"),N.objectStoreNames.contains("config")||N.createObjectStore("config")},T.onsuccess=U=>b(U.target.result),T.onerror=U=>C(U.target.error)}),m)}function B(b,C){return w().then(T=>new Promise((U,N)=>{const j=T.transaction(b,"readonly").objectStore(b).get(C);j.onsuccess=()=>U(j.result),j.onerror=()=>N(j.error)}))}function z(b,C,T){return w().then(U=>new Promise((N,l)=>{const j=U.transaction(b,"readwrite");j.objectStore(b).put(T,C),j.oncomplete=()=>N(),j.onerror=()=>l(j.error)}))}function q(b,C){return w().then(T=>new Promise((U,N)=>{const l=T.transaction(b,"readwrite");l.objectStore(b).delete(C),l.oncomplete=()=>U(),l.onerror=()=>N(l.error)}))}function F(b){return w().then(C=>new Promise((T,U)=>{const N=C.transaction(b,"readwrite");N.objectStore(b).clear(),N.oncomplete=()=>T(),N.onerror=()=>U(N.error)}))}async function A(b){if(!b)return!1;try{const C={mode:"read"};let T=await b.queryPermission(C);return T==="granted"?!0:(T=await b.requestPermission(C),T==="granted")}catch(C){return console.warn("[folder] permission check failed:",C),!1}}function g(b,C){const T=document.getElementById("folder-status-summary");T&&(T.setAttribute("data-i18n",b),T.textContent=t(b),T.className="auto-status-pill"+(C?" "+C:""))}function d(b){["folder-unsupported","folder-empty","folder-active"].forEach(C=>{const T=document.getElementById(C);T&&(T.style.display=C===b?"":"none")})}function h(b){if(!b)return"-";const C=b instanceof Date?b:new Date(b),T=String(C.getHours()).padStart(2,"0"),U=String(C.getMinutes()).padStart(2,"0"),N=String(C.getSeconds()).padStart(2,"0");return`${T}:${U}:${N}`}function I(){d("folder-active");const b=document.getElementById("folder-config-path");b&&r&&(b.textContent=r.name||"-");const C=document.getElementById("folder-interval-select");C&&(C.value=String(i)),document.getElementById("folder-stat-last").textContent=R?h(R):"-",document.getElementById("folder-stat-processed").textContent=String(c),document.getElementById("folder-stat-failed").textContent=String(v),document.getElementById("folder-stat-queue").textContent=String(E);const T=document.getElementById("btn-folder-pause"),U=document.getElementById("btn-folder-resume");T&&(T.style.display=f?"none":""),U&&(U.style.display=f?"":"none"),f?g("folder-status-paused","paused"):g("folder-status-running","running");const N=document.getElementById("folder-status-text");N&&(N.setAttribute("data-i18n",f?"folder-status-paused":"folder-status-running"),N.textContent=t(f?"folder-status-paused":"folder-status-running"));const l=document.getElementById("folder-status-pulse");l&&(l.className="folder-status-pulse"+(f?" paused":"")),L()}function L(){const b=document.getElementById("folder-recent-list");if(b){if(x.length===0){b.innerHTML=`<div class="folder-recent-empty">${escapeHtml(t("folder-recent-empty"))}</div>`;return}b.innerHTML=x.slice(0,20).map(C=>{let T;C.status==="ok"?T=`<span class="folder-recent-icon ok">${svgIcon("check",12)}</span>`:C.status==="dup"?T=`<span class="folder-recent-icon dup" title="${escapeHtml(t("folder-recent-dup"))}">${svgIcon("copy",12)}</span>`:C.status==="skip"?T=`<span class="folder-recent-icon skip" title="${escapeHtml(t("folder-recent-skip"))}">${svgIcon("minus",12)}</span>`:T=`<span class="folder-recent-icon fail">${svgIcon("alert",12)}</span>`;const U=C.status==="fail"&&C.error?C.error:C.status==="dup"&&C.reason||C.status==="skip"&&C.reason?C.reason:"",N=U?`<div class="folder-recent-err">${escapeHtml(U)}</div>`:"";return`
                <div class="folder-recent-item">
                    ${T}
                    <div class="folder-recent-body">
                        <div class="folder-recent-name">${escapeHtml(C.name)}</div>
                        ${N}
                    </div>
                    <div class="folder-recent-time">${h(C.time)}</div>
                </div>
            `}).join("")}}function H(b){x.unshift(b),x.length>50&&(x.length=50),z("config","recent_list",x).catch(()=>{})}async function _(b){const C=new FormData;C.append("file",b,b.name),C.append("source","folder");const T=await fetch("/api/ocr/recognize?source=folder",{method:"POST",headers:{Authorization:"Bearer "+token,"X-Source":"folder"},body:C});if(!T.ok){let U="http_"+T.status;try{const N=await T.json();U=N&&N.detail?typeof N.detail=="string"?N.detail:N.detail.code||JSON.stringify(N.detail):U}catch{}throw new Error(U)}return await T.json()}async function M(b){try{const T=(await b.getFile()).size;return await new Promise(N=>setTimeout(N,3e3)),(await b.getFile()).size===T&&T>0}catch{return!1}}async function K(b,C,T,U){if(U>10)return;let N;try{N=await b.queryPermission({mode:"read"})}catch{N="denied"}if(N==="granted")for await(const l of b.values()){const j=C?`${C}/${l.name}`:l.name;if(l.kind==="file"){if(!a.test(l.name))continue;let O;try{O=await l.getFile()}catch{continue}const J=`${j}::${O.size}::${O.lastModified}`;if(await B("seen",J))continue;T.push({entry:l,file:O,seenKey:J,relPath:j})}else if(l.kind==="directory")try{await K(l,j,T,U+1)}catch{}}}async function G(){if(!(u||f||!r)){u=!0;try{if(await r.queryPermission({mode:"read"})!=="granted"){console.warn("[folder] permission lost · stop"),Y(),showToast("warn",t("folder-permission-lost"));return}R=new Date;const C=[];await K(r,"",C,0),E=C.length,I();for(const T of C){if(f)break;if(!await M(T.entry)){E=Math.max(0,E-1),I();continue}try{let N;try{N=await T.entry.getFile()}catch{N=T.file}const l=await _(N);await z("seen",T.seenKey,{name:N.name,relPath:T.relPath,size:N.size,lastModified:N.lastModified,processed_at:Date.now()});const j=l.history_ids||(l.history_id?[l.history_id]:[]),O=l.duplicate_warnings||[],J=T.relPath||N.name;j.length>0?(c+=j.length,H({name:J,status:"ok",time:new Date,history_id:j[0],count:j.length}),await z("config","processed_count",c)):O.length>0?H({name:J,status:"dup",time:new Date,reason:t("folder-recent-dup-reason")}):H({name:J,status:"skip",time:new Date,reason:t("folder-recent-skip-reason")})}catch(N){v++,H({name:T.relPath||T.file.name,status:"fail",time:new Date,error:String(N.message||N)}),await z("config","failed_count",v)}E=Math.max(0,E-1),I()}}catch(b){console.warn("[folder] scan error:",b)}finally{u=!1,I()}}}function W(){k&&clearInterval(k),k=setInterval(G,i*1e3)}function te(){k&&(clearInterval(k),k=null)}function re(b){if(!r||f)return;const C=typeof t=="function"?t("folder-unload-warn"):"Folder watcher running · close anyway?";return b.preventDefault(),b.returnValue=C,C}function S(){window._pearnlyFolderUnloadAttached||(window._pearnlyFolderUnloadAttached=!0,window.addEventListener("beforeunload",re))}function y(){window._pearnlyFolderUnloadAttached&&(window._pearnlyFolderUnloadAttached=!1,window.removeEventListener("beforeunload",re))}function p(){f=!1,W(),S(),I(),G()}function $(){f=!0,te(),y(),I()}function P(){f=!1,W(),S(),I(),G()}function Y(){f=!0,te(),y()}async function Z(){try{const b=await window.showDirectoryPicker({mode:"read",startIn:"documents"});if(!await A(b)){showToast("warn",t("folder-permission-denied"));return}r=b,await z("handles","main",b),c=0,v=0,E=0,x=[],await z("config","processed_count",0),await z("config","failed_count",0),await F("seen"),p()}catch(b){b&&b.name!=="AbortError"&&console.warn("[folder] pick failed:",b)}}async function le(){await showConfirm(t("folder-confirm-remove"),{danger:!0})&&(Y(),r=null,c=0,v=0,E=0,x=[],await q("handles","main"),await q("config","processed_count"),await q("config","failed_count"),await F("seen"),d("folder-empty"),g("folder-status-empty",""))}async function ie(){x=[];try{await q("config","recent_list")}catch{}L()}async function V(){if(D)return;if(D=!0,!n){d("folder-unsupported"),g("folder-status-unsupported",""),ne();return}Q();let b=null;try{b=await B("handles","main")}catch{}if(!b){d("folder-empty"),g("folder-status-empty","");return}if(!await A(b)){d("folder-empty"),g("folder-status-empty",""),await q("handles","main"),showToast("warn",t("folder-permission-lost-restart"));return}r=b;try{c=await B("config","processed_count")||0}catch{}try{v=await B("config","failed_count")||0}catch{}try{const T=await B("config","recent_list");Array.isArray(T)&&(x=T.map(U=>({...U,time:U.time?new Date(U.time):new Date})))}catch{}p()}function Q(){const b=document.getElementById("btn-folder-pick"),C=document.getElementById("btn-folder-pause"),T=document.getElementById("btn-folder-resume"),U=document.getElementById("btn-folder-scan-now"),N=document.getElementById("btn-folder-remove"),l=document.getElementById("btn-folder-clear-recent"),j=document.getElementById("folder-interval-select");b&&b.addEventListener("click",Z),C&&C.addEventListener("click",$),T&&T.addEventListener("click",P),U&&U.addEventListener("click",()=>{G()}),N&&N.addEventListener("click",le),l&&l.addEventListener("click",ie),j&&j.addEventListener("change",O=>{i=parseInt(O.target.value,10)||60,f||W()}),ee()}function ee(){document.querySelectorAll('[data-auto-panel="folder"] [data-tab-jump]').forEach(b=>{b.dataset.tabJumpBound||(b.dataset.tabJumpBound="1",b.addEventListener("click",C=>{const T=C.currentTarget.dataset.tabJump;if(T==="email")typeof switchAutomationTab=="function"&&switchAutomationTab("email");else if(T==="upload"){const U=document.querySelector('[data-page="recognize"]')||document.querySelector('[data-page="upload"]');U&&U.click()}}))})}function ne(){ee()}window._loadFolderWatcherPanel=V;function se(){try{if(navigator.userAgentData&&Array.isArray(navigator.userAgentData.brands))return navigator.userAgentData.brands.some(C=>/chromium|google chrome|microsoft edge/i.test(C.brand||""))}catch{}const b=navigator.userAgent||"";return!!(/Edg\//.test(b)||/Chrome\//.test(b)&&!/OPR\/|YaBrowser|Opera/.test(b))}function ue(){try{if(se()||localStorage.getItem("pearnly_chrome_banner_dismissed")==="1")return;const b=document.getElementById("chrome-only-banner");if(!b)return;const C=b.querySelector('[data-i18n="chrome-banner-msg"]'),T=b.querySelector('[data-i18n="chrome-banner-dismiss"]');C&&typeof t=="function"&&(C.textContent=t("chrome-banner-msg")),T&&typeof t=="function"&&(T.textContent=t("chrome-banner-dismiss")),b.style.display="";const U=document.getElementById("chrome-only-banner-close");U&&!U.dataset.bound&&(U.dataset.bound="1",U.addEventListener("click",()=>{b.style.display="none";try{localStorage.setItem("pearnly_chrome_banner_dismissed","1")}catch{}}))}catch{}}typeof document<"u"&&(document.readyState==="loading"?document.addEventListener("DOMContentLoaded",ue):setTimeout(ue,0)),window._refreshChromeBanner=ue})();(function(){let e=null,n=null,a="new",s=!1,o=!1;async function m(){const _=document.getElementById("email-empty"),M=document.getElementById("email-account-card");if(document.getElementById("email-logs-section"),!(!_||!M))try{const K=await fetch("/api/email-ingest/account",{headers:{Authorization:"Bearer "+token}});if(K.status===401){localStorage.removeItem("mrpilot_token");const W=await K.json().catch(()=>({}));if((typeof W.detail=="string"?W.detail:W.detail&&W.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}if(!K.ok){k("none");return}const G=await K.json();e=G.account||null,n=G.presets||{},s=!0,r(),e&&h()}catch(K){console.error("[email-ingest] load failed",K),k("none")}}function r(){const _=document.getElementById("email-empty"),M=document.getElementById("email-account-card"),K=document.getElementById("email-logs-section");if(!e){_.style.display="",M.style.display="none",K&&(K.style.display="none"),k("none");return}_.style.display="none",M.style.display="",K&&(K.style.display="");const G=document.getElementById("email-account-addr"),W=document.getElementById("email-account-host"),te=document.getElementById("email-account-last"),re=document.getElementById("email-last-error"),S=document.getElementById("email-enabled-toggle");if(G&&(G.textContent=e.email_address||"-"),W&&(W.textContent=`${e.imap_host||"-"}:${e.imap_port||993}`),te){const y=e.last_fetched_at;if(!y)te.textContent=t("email-last-never");else{const p=i(y),$=!e.last_error;te.textContent=$?t("email-last-ok",{time:p}):t("email-last-fail",{time:p})}}re&&(e.last_error?(re.style.display="",re.textContent=f(e.last_error)):re.style.display="none"),S&&(S.checked=!!e.enabled),e.enabled?e.last_error?k("error"):k("on"):k("off")}function k(_){const M=document.getElementById("email-status-summary");if(!M)return;M.classList.remove("none","ready","active","coming");let K="auto-status-loading";_==="none"?(K="email-status-none",M.classList.add("none")):_==="on"?(K="email-status-on",M.classList.add("active")):_==="off"?(K="email-status-off",M.classList.add("coming")):_==="error"&&(K="email-status-error",M.classList.add("none")),M.setAttribute("data-i18n",K),M.textContent=t(K)}function i(_){if(!_)return"";const M=new Date(_);if(isNaN(M.getTime()))return"";const K=G=>String(G).padStart(2,"0");return`${K(M.getMonth()+1)}-${K(M.getDate())} ${K(M.getHours())}:${K(M.getMinutes())}`}function f(_){if(!_)return"";const M=String(_);return/auth|AUTHENTICATIONFAILED|invalid credentials/i.test(M)?t("email-test-auth-fail"):/timeout|timed out/i.test(M)?t("email.timeout"):(/ENOTFOUND|getaddrinfo/i.test(M),M)}function u(_){a=_;const M=document.getElementById("email-modal");if(!M)return;const K=document.getElementById("email-preset");K.innerHTML="";const G=n||{},W=["gmail","outlook","yahoo","icloud","qq","163","custom"],te={gmail:"Gmail",outlook:"Outlook / Office365",yahoo:"Yahoo Mail",icloud:"iCloud",qq:"QQ 邮箱",163:"网易 163"};W.forEach(Q=>{if(!G[Q])return;const ee=document.createElement("option");ee.value=Q,ee.textContent=Q==="custom"?t("email-preset-custom"):te[Q]||Q,K.appendChild(ee)});const re=document.getElementById("email-modal-title"),S=document.getElementById("email-address"),y=document.getElementById("email-password"),p=document.getElementById("email-imap-host"),$=document.getElementById("email-imap-port"),P=document.getElementById("email-imap-ssl"),Y=document.getElementById("email-folder"),Z=document.getElementById("email-mark-read"),le=document.getElementById("email-bind-enabled"),ie=document.getElementById("email-test-result"),V=document.getElementById("email-adv-details");if(ie&&(ie.style.display="none",ie.textContent=""),_==="edit"&&e){re.setAttribute("data-i18n","email-modal-title-edit"),re.textContent=t("email-modal-title-edit"),S.value=e.email_address||"",y.value="",y.setAttribute("data-i18n-placeholder","email-field-password-edit-ph"),y.placeholder=t("email-field-password-edit-ph"),p.value=e.imap_host||"",$.value=e.imap_port||993,P.checked=e.imap_use_ssl!==!1,Y.value=e.folder||"INBOX",Z.checked=e.mark_as_read!==!1,le.checked=e.enabled!==!1;const Q=document.getElementById("email-filter-sender"),ee=document.getElementById("email-filter-subject");Q&&(Q.value=e.filter_sender||""),ee&&(ee.value=e.filter_subject||""),B(e.interval_min||15),K.value=R(e.imap_host)||"custom",V&&(V.open=!0)}else{re.setAttribute("data-i18n","email-modal-title-new"),re.textContent=t("email-modal-title-new"),S.value="",y.value="",y.setAttribute("data-i18n-placeholder","email-field-password-ph"),y.placeholder=t("email-field-password-ph"),K.value="gmail",v("gmail"),Y.value="INBOX",Z.checked=!0,le.checked=!0;const Q=document.getElementById("email-filter-sender"),ee=document.getElementById("email-filter-subject");Q&&(Q.value=""),ee&&(ee.value=""),B(15),V&&(V.open=!1)}w(),M.style.display="flex",setTimeout(()=>S.focus(),60)}function c(){const _=document.getElementById("email-modal");_&&(_.style.display="none")}function v(_){const M=(n||{})[_];if(!M||_==="custom")return;const K=document.getElementById("email-imap-host"),G=document.getElementById("email-imap-port"),W=document.getElementById("email-imap-ssl");K&&(K.value=M.host||""),G&&(G.value=M.port||993),W&&(W.checked=M.ssl!==!1)}const E={"gmail.com":"gmail","googlemail.com":"gmail","outlook.com":"outlook","hotmail.com":"outlook","live.com":"outlook","office365.com":"outlook","msn.com":"outlook","yahoo.com":"yahoo","yahoo.co.jp":"yahoo","icloud.com":"icloud","me.com":"icloud","mac.com":"icloud","qq.com":"qq","foxmail.com":"qq","163.com":"163","126.com":"163","yeah.net":"163"};function x(_){if(!_||!_.includes("@"))return;const M=_.split("@")[1].toLowerCase().trim(),K=E[M];if(!K)return;const G=document.getElementById("email-preset");if(!G)return;const W=G.value;W&&W!=="custom"&&W!==""&&W===K||(G.value=K,v(K))}function R(_){if(!_)return null;const M=n||{};for(const K in M)if(K!=="custom"&&M[K]&&M[K].host===_)return K;return null}function D(){const _=document.querySelector("#email-interval-options .email-interval-btn.active"),M=_?parseInt(_.dataset.interval,10):15;return{email_address:(document.getElementById("email-address").value||"").trim(),password:document.getElementById("email-password").value||"",imap_host:(document.getElementById("email-imap-host").value||"").trim(),imap_port:parseInt(document.getElementById("email-imap-port").value||"993",10)||993,imap_use_ssl:document.getElementById("email-imap-ssl").checked,folder:(document.getElementById("email-folder").value||"INBOX").trim()||"INBOX",mark_as_read:document.getElementById("email-mark-read").checked,enabled:document.getElementById("email-bind-enabled").checked,interval_min:[5,15,60].includes(M)?M:15,filter_sender:(document.getElementById("email-filter-sender").value||"").trim()||null,filter_subject:(document.getElementById("email-filter-subject").value||"").trim()||null}}function w(){const _=document.getElementById("email-interval-options");!_||_._bound||(_._bound=!0,_.addEventListener("click",M=>{const K=M.target.closest(".email-interval-btn");K&&(_.querySelectorAll(".email-interval-btn").forEach(G=>G.classList.remove("active")),K.classList.add("active"))}))}function B(_){const M=[5,15,60].includes(_)?_:15,K=document.getElementById("email-interval-options");K&&K.querySelectorAll(".email-interval-btn").forEach(G=>{G.classList.toggle("active",parseInt(G.dataset.interval,10)===M)})}function z(_,M){const K=document.getElementById("email-test-result");K&&(K.style.display="",K.textContent=M,K.className="form-test-result "+(_==="ok"?"ok":_==="running"?"running":"fail"))}async function q(){const _=D();if(!_.email_address){z("fail",t("email-addr-required"));return}if(!_.password){z("fail",t("email-password-required"));return}if(!_.imap_host){z("fail",t("email-host-required"));return}const M=document.getElementById("btn-email-modal-test");M&&(M.disabled=!0),z("running",t("email-test-running"));try{const K=await fetch("/api/email-ingest/test",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:_.email_address,password:_.password,imap_host:_.imap_host,imap_port:_.imap_port,imap_use_ssl:_.imap_use_ssl,folder:_.folder})}),G=await K.json().catch(()=>({}));if(K.ok&&G.success)z("ok",t("email-test-ok",{folder:_.folder,n:G.folder_count??"?"}));else{const W=G.error_msg||"";W==="auth_failed"||/auth/i.test(W)?z("fail",t("email-test-auth-fail")):z("fail",t("email-test-fail",{msg:W||K.status}))}}catch(K){z("fail",t("email-test-fail",{msg:String(K).slice(0,120)}))}finally{M&&(M.disabled=!1)}}async function F(){const _=D();if(!_.email_address){z("fail",t("email-addr-required"));return}if(a==="new"&&!_.password){z("fail",t("email-password-required"));return}if(!_.imap_host){z("fail",t("email-host-required"));return}const M=document.getElementById("btn-email-modal-save");M&&(M.disabled=!0);const K={..._};a==="edit"&&!K.password&&delete K.password;try{const G=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(K)}),W=await G.json().catch(()=>({}));if(G.ok&&W.ok)e=W.account,showToast(t("email-save-ok"),"success"),c(),r(),h();else{const re="email."+(W.detail||"").split(".").slice(-1)[0];z("fail",t(re)!==re?t(re):t("email-save-fail"))}}catch{z("fail",t("email-save-fail"))}finally{M&&(M.disabled=!1)}}async function A(){if(!(!e||!await showConfirm(t("email-unbind-confirm",{email:e.email_address}),{danger:!0,okText:t("email-btn-unbind")})))try{if((await fetch("/api/email-ingest/account",{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){e=null,showToast(t("email-unbind-ok"),"success"),r();const K=document.getElementById("email-logs-list");K&&(K.innerHTML="")}else showToast(t("email-unbind-fail"),"error")}catch{showToast(t("email-unbind-fail"),"error")}}async function g(){if(!e||o)return;if(!e.enabled){showToast(t("email.disabled"),"error");return}o=!0;const _=document.getElementById("btn-email-trigger"),M=_?_.innerHTML:"";_&&(_.disabled=!0,_.innerHTML=`<span>${escapeHtml(t("email-trigger-running"))}</span>`);try{const K=await fetch("/api/email-ingest/trigger",{method:"POST",headers:{Authorization:"Bearer "+token}}),G=await K.json().catch(()=>({}));if(K.ok){const W=G.emails_scanned||0,te=G.ocr_succeeded||0,re=G.ocr_failed||0;W===0&&te===0&&re===0?showToast(t("email-trigger-empty"),"success"):showToast(t("email-trigger-result",{scanned:W,ok:te,fail:re}),re>0?"warn":"success")}else{const te="email."+(G.detail||"").split(".").slice(-1)[0];showToast(t(te)!==te?t(te):t("email-trigger-fail"),"error")}await m()}catch{showToast(t("email-trigger-fail"),"error")}finally{o=!1,_&&(_.disabled=!1,_.innerHTML=M)}}async function d(){if(!e)return;const _=document.getElementById("email-enabled-toggle"),M=!!(_&&_.checked),K=e.enabled;try{const G=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:e.email_address,imap_host:e.imap_host,imap_port:e.imap_port,imap_use_ssl:e.imap_use_ssl,folder:e.folder||"INBOX",filter_subject:e.filter_subject||null,filter_sender:e.filter_sender||null,mark_as_read:e.mark_as_read!==!1,enabled:M})}),W=await G.json().catch(()=>({}));G.ok&&W.ok?(e=W.account,r()):(_&&(_.checked=K),showToast(t("email-toggle-fail"),"error"))}catch{_&&(_.checked=K),showToast(t("email-toggle-fail"),"error")}}async function h(){const _=document.getElementById("email-logs-list");if(_){_.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`;try{const M=await fetch("/api/email-ingest/logs?limit=20",{headers:{Authorization:"Bearer "+token}});if(!M.ok){_.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const K=await M.json();if(!Array.isArray(K)||K.length===0){_.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("email-logs-empty"))}</div>`;return}_.innerHTML=K.map(I).join("")}catch{_.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}function I(_){const M=i(_.created_at),K=_.status||"failed",G=K==="success"?"ok":K==="partial"?"partial":"fail",W=K==="success"?"✓":K==="partial"?"◐":"✗",te=_.trigger==="manual"?`<span class="log-tag manual">${escapeHtml(t("email-log-tag-manual"))}</span>`:`<span class="log-tag auto">${escapeHtml(t("email-log-tag-auto"))}</span>`,re=t("email-log-counts",{scanned:_.emails_scanned||0,att:_.attachments_found||0,ok:_.ocr_succeeded||0,fail:_.ocr_failed||0}),S=(_.elapsed_ms||0)+"ms";return`
            <div class="email-log-row ${G}">
                <span class="log-time">${escapeHtml(M)}</span>
                <span class="log-status">${W}</span>
                ${te}
                <span class="log-counts">${escapeHtml(re)}</span>
                <span class="log-elapsed">${escapeHtml(S)}</span>
            </div>
        `}function L(){const _=document.getElementById("btn-email-bind");_&&_.addEventListener("click",()=>u("new"));const M=document.getElementById("btn-email-edit");M&&M.addEventListener("click",()=>u("edit"));const K=document.getElementById("btn-email-unbind");K&&K.addEventListener("click",A);const G=document.getElementById("btn-email-trigger");G&&G.addEventListener("click",g);const W=document.getElementById("email-enabled-toggle");W&&W.addEventListener("change",d);const te=document.getElementById("email-modal-close");te&&te.addEventListener("click",c);const re=document.getElementById("btn-email-modal-cancel");re&&re.addEventListener("click",c);const S=document.getElementById("btn-email-modal-test");S&&S.addEventListener("click",q);const y=document.getElementById("btn-email-modal-save");y&&y.addEventListener("click",F);const p=document.getElementById("email-preset");p&&p.addEventListener("change",Y=>v(Y.target.value));const $=document.getElementById("email-address");$&&!$.dataset.autoBound&&($.dataset.autoBound="1",$.addEventListener("blur",Y=>x((Y.target.value||"").trim())),$.addEventListener("input",Y=>{const Z=(Y.target.value||"").trim();Z.includes("@")&&Z.split("@")[1].includes(".")&&x(Z)}));const P=document.getElementById("btn-email-refresh-logs");P&&P.addEventListener("click",()=>{P.classList.add("spinning"),setTimeout(()=>P.classList.remove("spinning"),600),h()})}L(),window._loadEmailIngestPanel=m,window._rerenderEmailIngest=function(){if(!s)return;r();const _=document.getElementById("email-logs-section");e&&_&&_.open&&h()};let H=null;window._startEmailLogAutoRefresh=function(){H||(H=setInterval(()=>{e&&s&&h()},3e4))},window._stopEmailLogAutoRefresh=function(){H&&(clearInterval(H),H=null)}})();(function(){let e=[],n=null,a=[],s="all",o=null,m=!1;async function r(){if(m){L();return}m=!0,k(),await i(),L()}function k(){const l=document.getElementById("bank-file-input");l&&!l._bound&&(l._bound=!0,l.addEventListener("change",x));const j=document.getElementById("btn-bank-queue-clear-done");j&&!j._bound&&(j._bound=!0,j.addEventListener("click",q));const O=document.getElementById("btn-bank-back");O&&!O._bound&&(O._bound=!0,O.addEventListener("click",()=>{n=null,a=[],te()}));const J=document.getElementById("btn-bank-delete");J&&!J._bound&&(J._bound=!0,J.addEventListener("click",d));const X=document.getElementById("btn-bank-run-match");X&&!X._bound&&(X._bound=!0,X.addEventListener("click",g)),document.querySelectorAll(".bank-filter-btn").forEach(ve=>{ve._bound||(ve._bound=!0,ve.addEventListener("click",()=>{s=ve.dataset.bankFilter||"all",document.querySelectorAll(".bank-filter-btn").forEach(fe=>{fe.classList.toggle("active",fe===ve)}),Z()}))}),document.querySelectorAll("[data-bank-cand-close]").forEach(ve=>{ve._bound||(ve._bound=!0,ve.addEventListener("click",ne))});const de=document.getElementById("btn-bank-cand-pane-close");de&&!de._bound&&(de._bound=!0,de.addEventListener("click",ne));const oe=document.getElementById("btn-bank-cand-ignore");oe&&!oe._bound&&(oe._bound=!0,oe.addEventListener("click",h));const ce=document.getElementById("btn-bank-cand-ignore-pane");ce&&!ce._bound&&(ce._bound=!0,ce.addEventListener("click",h));const ae=document.getElementById("bank-client-badge");ae&&!ae._bound&&(ae._bound=!0,ae.addEventListener("click",y)),document.querySelectorAll("[data-bank-client-picker-close]").forEach(ve=>{ve._bound||(ve._bound=!0,ve.addEventListener("click",p))});const pe=document.getElementById("btn-bank-client-picker-save");pe&&!pe._bound&&(pe._bound=!0,pe.addEventListener("click",P)),document.querySelectorAll(".bank-sessions-chip").forEach(ve=>{ve._bound||(ve._bound=!0,ve.addEventListener("click",()=>{H=ve.dataset.sessFilter||"all",document.querySelectorAll(".bank-sessions-chip").forEach(fe=>{fe.classList.toggle("active",fe===ve)}),_()}))})}async function i(){try{const l=await fetch("/api/bank-recon/sessions?limit=30",{headers:{Authorization:"Bearer "+token}});if(!l.ok)throw new Error("sessions:"+l.status);e=await l.json(),_()}catch(l){console.warn("[bank-recon] loadSessions failed",l),e=[],_()}}async function f(l){try{const j="/api/bank-recon/sessions/"+encodeURIComponent(l)+(s!=="all"?"?filter="+s:""),O=await fetch(j,{headers:{Authorization:"Bearer "+token}});if(!O.ok)throw new Error("detail:"+O.status);const J=await O.json();n=J.session,a=J.transactions||[],W()}catch(j){console.warn("[bank-recon] loadSessionDetail failed",j),showToast(t("bank-load-failed"),"error")}}let u=[],c=0;const v=3;function E(){return c+=1,"q"+c+"_"+Date.now()}async function x(l){const j=Array.from(l.target.files||[]);if(l.target.value="",j.length!==0){for(const O of j){const J={id:E(),file:O,name:O.name,size:O.size,status:"pending",progress:0,error_code:null,tx_count:0,session_id:null};O.name.toLowerCase().endsWith(".pdf")?O.size>20*1024*1024&&(J.status="failed",J.error_code="bank_recon.file_too_large"):(J.status="failed",J.error_code="bank_recon.only_pdf"),u.push(J)}R(),D(),F()}}function R(){const l=document.getElementById("bank-upload-queue");l&&(l.style.display=""),se(),ue()}function D(){const l=document.getElementById("bank-upload-queue-list"),j=document.getElementById("bank-upload-queue-summary");if(!l)return;if(u.length===0){l.innerHTML="",j&&(j.textContent="");const oe=document.getElementById("bank-upload-queue");oe&&(oe.style.display="none");return}let O=0,J=0,X=0,de=0;for(const oe of u)oe.status==="ok"?O++:oe.status==="failed"?J++:oe.status==="uploading"||oe.status==="parsing"?X++:de++;j&&(j.textContent=t("bank-queue-summary").replace("{ok}",O).replace("{run}",X).replace("{wait}",de).replace("{fail}",J)),l.innerHTML=u.map(w).join(""),l.querySelectorAll("[data-q-act]").forEach(oe=>{const ce=oe.dataset.qAct,ae=oe.dataset.qId;oe.addEventListener("click",()=>{ce==="retry"&&B(ae),ce==="remove"&&z(ae)})})}function w(l){const j=(l.size/1024).toFixed(0)+" KB";let O="",J="";if(l.status==="pending")O='<span class="bq-stat bq-wait">'+t("bank-queue-status-wait")+"</span>",J='<button data-q-act="remove" data-q-id="'+N(l.id)+'" class="bq-act">×</button>';else if(l.status==="uploading")O='<span class="bq-stat bq-run">'+t("bank-queue-status-uploading")+'</span><div class="bq-bar"><div class="bq-bar-fill" style="width:'+(l.progress||0)+'%"></div></div>';else if(l.status==="parsing")O='<span class="bq-stat bq-run">'+t("bank-queue-status-parsing")+'</span><div class="bq-bar"><div class="bq-bar-fill bq-bar-indet"></div></div>';else if(l.status==="ok")O='<span class="bq-stat bq-ok">'+t("bank-queue-status-ok").replace("{n}",l.tx_count||0)+"</span>",J='<button data-q-act="remove" data-q-id="'+N(l.id)+'" class="bq-act">×</button>';else if(l.status==="failed"){const X=b(l.error_code||"unknown");O='<span class="bq-stat bq-fail" title="'+N(X)+'">'+N(X)+"</span>",J='<button data-q-act="retry" data-q-id="'+N(l.id)+'" class="bq-act bq-act-retry">'+t("bank-queue-retry")+'</button><button data-q-act="remove" data-q-id="'+N(l.id)+'" class="bq-act">×</button>'}return'<div class="bq-row" data-q-row="'+N(l.id)+'"><div class="bq-name" title="'+N(l.name)+'">'+N(l.name)+'</div><div class="bq-size">'+j+'</div><div class="bq-status">'+O+'</div><div class="bq-actions">'+J+"</div></div>"}function B(l){const j=u.find(O=>O.id===l);j&&(j.status="pending",j.error_code=null,j.progress=0,D(),F())}function z(l){const j=u.findIndex(J=>J.id===l);if(j<0)return;const O=u[j];O.status==="uploading"||O.status==="parsing"||(u.splice(j,1),D())}function q(){u=u.filter(l=>l.status!=="ok"),D()}async function F(){for(;;){if(u.filter(O=>O.status==="uploading"||O.status==="parsing").length>=v)return;const j=u.find(O=>O.status==="pending");if(!j){u.every(O=>O.status==="ok"||O.status==="failed")&&(await i(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage());return}A(j).then(()=>F())}}async function A(l){l.status="uploading",l.progress=0,D();try{const j=new FormData;j.append("file",l.file,l.name);const O=await new Promise((X,de)=>{const oe=new XMLHttpRequest;oe.open("POST","/api/bank-recon/upload"),oe.setRequestHeader("Authorization","Bearer "+token),oe.upload.onprogress=ce=>{ce.lengthComputable&&(l.progress=Math.min(99,Math.round(ce.loaded/ce.total*100)),D())},oe.upload.onload=()=>{l.status="parsing",D()},oe.onload=()=>{oe.status>=200&&oe.status<300?X({status:oe.status,text:oe.responseText}):X({status:oe.status,text:oe.responseText})},oe.onerror=()=>de(new Error("network")),oe.send(j)});let J={};try{J=JSON.parse(O.text||"{}")}catch{J={}}if(O.status>=400){l.status="failed",l.error_code=J&&J.detail||"unknown",D();return}if(J.parse_status==="parse_failed"){l.status="failed",l.error_code=J.error==="scanned_pdf_not_yet"?"bank_recon.scanned":"bank_recon.no_tx",D();return}l.status="ok",l.tx_count=J.tx_count||0,l.session_id=J.session_id||null,D()}catch(j){console.warn("[bank-recon] upload failed",j),l.status="failed",l.error_code="network",D()}}async function g(){if(!n)return;const l=document.getElementById("btn-bank-run-match"),j=l.innerHTML;l.disabled=!0,l.innerHTML="<span>"+t("bank-matching")+"</span>";try{const O=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id)+"/match",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!O.ok)throw new Error("match:"+O.status);const J=await O.json();showToast(t("bank-match-done").replace("{matched}",J.matched).replace("{suggested}",J.suggested).replace("{unmatched}",J.unmatched),"success"),await f(n.id),await i()}catch(O){console.warn("[bank-recon] match failed",O),showToast(t("bank-match-failed"),"error")}finally{l.disabled=!1,l.innerHTML=j}}async function d(){if(!(!n||!await showConfirm(t("bank-delete-confirm"),{danger:!0})))try{const j=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!j.ok)throw new Error("delete:"+j.status);showToast(t("bank-deleted"),"success"),n=null,a=[],te(),await i()}catch(j){console.warn("[bank-recon] delete failed",j),showToast(t("bank-delete-failed"),"error")}}async function h(){if(o)try{const l=await fetch("/api/bank-recon/tx/"+encodeURIComponent(o.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"ignored"})});if(!l.ok)throw new Error("ignore:"+l.status);ne(),await f(n.id)}catch{showToast(t("bank-action-failed"),"error")}}async function I(l){if(o)try{const j=await fetch("/api/bank-recon/tx/"+encodeURIComponent(o.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"matched",history_id:l})});if(!j.ok)throw new Error("pick:"+j.status);showToast(t("bank-matched-ok"),"success"),ne(),await f(n.id)}catch{showToast(t("bank-action-failed"),"error")}}function L(){const l=document.getElementById("bank-status-summary");if(!l)return;if(e.length===0){l.textContent=t("bank-pill-none");return}let O=0;for(const J of e)J.parse_status==="parsed"&&(J.unmatched_count||0)>0&&O++;l.textContent=O>0?t("bank-pill-pending").replace("{n}",O):t("bank-pill-ok")}let H="all";function _(){const l=document.getElementById("bank-sessions-list");if(!l)return;let j=e||[];if(H==="parsed"?j=j.filter(O=>O.parse_status==="parsed"):H==="failed"&&(j=j.filter(O=>O.parse_status==="parse_failed")),!e||e.length===0){l.innerHTML='<div class="bank-empty" data-i18n="bank-sessions-empty">'+t("bank-sessions-empty")+"</div>";return}if(j.length===0){l.innerHTML='<div class="bank-empty">'+t("bank-sess-filter-empty")+"</div>";return}l.innerHTML=j.map(O=>K(O)).join(""),l.querySelectorAll(".bank-session-row").forEach(O=>{O.addEventListener("click",J=>{J.target.closest(".bank-session-trash")||f(O.dataset.sessionId)})}),l.querySelectorAll(".bank-session-trash").forEach(O=>{O.addEventListener("click",J=>{J.stopPropagation();const X=O.dataset.sessionId,de=O.dataset.sessionName||"";M(X,de)})})}async function M(l,j){if(!l)return;const O=(t("bank-session-delete-confirm")||"确定删除这条对账记录吗?").replace("{name}",j||"");if(await showConfirm(O,{danger:!0}))try{const X=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(l),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!X.ok)throw new Error("delete:"+X.status);showToast(t("bank-deleted"),"success"),n&&n.id===l&&(n=null,a=[],te()),await i(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()}catch(X){console.warn("[bank-recon] delete failed",X),showToast(t("bank-delete-failed"),"error")}}window._deleteBankSession=M;function K(l){const j=(l.bank_code||"OTHER").toUpperCase(),O=U(l.period_start,l.period_end),J=l.account_last4?"···"+l.account_last4:"",X=G(l),de=T(l.created_at);return`
            <div class="bank-session-row" data-session-id="${N(l.id)}">
                <div class="bank-session-bank bk-${N(j)}">${N(j)}</div>
                <div class="bank-session-info">
                    <div class="bank-session-title">${N(l.source_filename||O||"-")}</div>
                    <div class="bank-session-meta">${N(O)} · ${N(J)} · ${N(de)}</div>
                </div>
                <div class="bank-session-counts">${X}</div>
                <button class="bank-session-trash" data-session-id="${N(l.id)}" data-session-name="${N(l.source_filename||"")}" title="${N(t("bank-session-delete-tip")||"删除")}">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/>
                    </svg>
                </button>
                <div class="bank-session-arrow">
                    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg>
                </div>
            </div>
        `}function G(l){if(l.parse_status==="parse_failed")return`<span class="bank-session-count cnt-failed">${t("bank-count-parse-failed")}</span>`;if(l.parse_status!=="parsed")return`<span class="bank-session-count">${t("bank-count-parsing")}</span>`;const j=l.tx_count||0,O=l.matched_count||0,J=l.unmatched_count||0,X=[`<span class="bank-session-count">${j} ${t("bank-count-tx")}</span>`];return O>0&&X.push(`<span class="bank-session-count cnt-matched">${O} ${t("bank-count-matched")}</span>`),J>0&&X.push(`<span class="bank-session-count cnt-unmatched">${J} ${t("bank-count-unmatched")}</span>`),X.join("")}function W(){document.getElementById("bank-detail").style.display="",document.querySelector(".bank-sessions-section").style.display="none",Y(),Z(),re()}function te(){document.getElementById("bank-detail").style.display="none",document.querySelector(".bank-sessions-section").style.display="";const l=document.getElementById("bank-detail-body");l&&l.classList.remove("has-pane"),o=null}function re(){const l=document.getElementById("bank-client-badge");if(!l||!n)return;const j=n.client_id,O=document.getElementById("bank-client-badge-dot"),J=document.getElementById("bank-client-badge-name"),X=document.getElementById("bank-client-badge-caret"),de=typeof _userInfo<"u"?_userInfo:null,oe=!(de&&de.role==="member");if(j!=null){const ce=(window._clientsCache||[]).find(ae=>Number(ae.id)===Number(j));l.classList.remove("is-empty"),O&&(O.style.background=ce&&ce.color||"#111111"),J&&(J.textContent=ce&&(ce.short_name||ce.name)||"#"+j)}else l.classList.add("is-empty"),O&&(O.style.background=""),J&&(J.textContent=t("bank-client-none"));oe?(l.classList.remove("is-readonly"),l.disabled=!1,X&&(X.style.display="")):(l.classList.add("is-readonly"),l.disabled=!0,X&&(X.style.display="none")),l.style.display=""}let S=null;function y(){if(!n)return;const l=typeof _userInfo<"u"?_userInfo:null;if(!!(l&&l.role==="member"))return;S=n.client_id!=null?Number(n.client_id):null,$();const O=document.getElementById("bank-client-picker-modal");O&&(O.style.display="")}function p(){const l=document.getElementById("bank-client-picker-modal");l&&(l.style.display="none"),S=null}function $(){const l=document.getElementById("bank-client-picker-list");if(!l)return;const j=(window._clientsCache||[]).filter(J=>J&&(J.is_active===!0||J.is_active===void 0)),O=[];O.push('<div class="bank-client-picker-row is-none'+(S==null?" is-selected":"")+'" data-cid=""><span class="bank-cp-dot"></span><span>'+N(t("bank-client-picker-none"))+"</span></div>"),j.forEach(J=>{const X=Number(J.id)===Number(S)?" is-selected":"";O.push('<div class="bank-client-picker-row'+X+'" data-cid="'+N(J.id)+'"><span class="bank-cp-dot" style="background:'+N(J.color||"#111111")+'"></span><span>'+N(J.short_name||J.name||"#"+J.id)+"</span></div>")}),l.innerHTML=O.join(""),l.querySelectorAll(".bank-client-picker-row").forEach(J=>{J.addEventListener("click",()=>{const X=J.dataset.cid;S=X?Number(X):null,$()})})}async function P(){if(n)try{const l=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id)+"/client",{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({client_id:S})});if(!l.ok)throw new Error("client:"+l.status);n.client_id=S,re(),showToast(t("bank-client-changed"),"success"),p();try{await i()}catch{}}catch(l){console.warn("[bank-recon] save client failed",l),showToast(t("bank-client-change-failed"),"error")}}function Y(){if(!n)return;const l=n;document.getElementById("bank-detail-title").textContent=(l.bank_code||"-")+(l.account_last4?" ···"+l.account_last4:"")+" · "+(l.source_filename||""),document.getElementById("bank-meta-period").textContent=U(l.period_start,l.period_end)||"-",document.getElementById("bank-meta-opening").textContent=C(l.opening_balance),document.getElementById("bank-meta-inflow").textContent="+"+C(l.total_inflow),document.getElementById("bank-meta-outflow").textContent="-"+C(l.total_outflow),document.getElementById("bank-meta-closing").textContent=C(l.closing_balance);const j=a||[],O=j.length;let J=0,X=0,de=0;for(const oe of j){const ce=oe.match_status||"unmatched";ce==="matched"?J++:ce==="suggested"?X++:de++}document.getElementById("bank-stat-total").textContent=O,document.getElementById("bank-stat-matched").textContent=J,document.getElementById("bank-stat-suggested").textContent=X,document.getElementById("bank-stat-unmatched").textContent=de}function Z(){const l=document.getElementById("bank-tx-tbody");if(!l)return;let j=a||[];if(s!=="all"&&(j=j.filter(O=>s==="matched"?O.match_status==="matched":s==="suggested"?O.match_status==="suggested":s==="unmatched"?O.match_status==="unmatched"||O.match_status==="ignored":!0)),j.length===0){l.innerHTML=`<tr><td colspan="4" class="bank-empty">${t("bank-tx-empty")}</td></tr>`;return}if(l.innerHTML=j.map(O=>le(O)).join(""),l.querySelectorAll("tr[data-tx-id]").forEach(O=>{O.addEventListener("click",()=>{const J=O.dataset.txId,X=a.find(de=>de.id===J);X&&(l.querySelectorAll("tr.is-selected").forEach(de=>de.classList.remove("is-selected")),O.classList.add("is-selected"),ie(X))})}),o){const O=l.querySelector('tr[data-tx-id="'+o.id+'"]');O&&O.classList.add("is-selected")}}function le(l){const j=l.direction==="OUT",O=j?"-":"+",J=j?"bank-out":"bank-in",X=l.match_status||"unmatched",de=t("bank-match-"+X)||X,oe=T(l.tx_date),ce=l.channel?`<span class="bank-tx-channel">${N(l.channel)}</span>`:"";return`
            <tr data-tx-id="${N(l.id)}">
                <td class="bank-tx-date">${N(oe)}</td>
                <td class="bank-tx-desc">${ce}${N(l.description||"-")}</td>
                <td class="bank-td-amount ${J}">${O}${C(l.amount)}</td>
                <td><span class="bank-tx-match mt-${X}">${N(de)}</span></td>
            </tr>
        `}async function ie(l){o=l;const j=document.getElementById("bank-detail-body");j&&j.classList.add("has-pane");const O=document.getElementById("bank-cand-pane-title"),J=document.getElementById("bank-cand-pane-sub"),X=document.getElementById("bank-cand-pane-foot");if(O&&(O.textContent=t("bank-cand-pane-current")),J){const oe=l.direction==="OUT"?"-":"+",ce=l.direction==="OUT"?"bank-out":"bank-in";J.innerHTML=`${N(T(l.tx_date))}
                <span style="margin:0 6px;color:#D1D5DB">·</span>
                <span>${N(l.description||"-")}</span>
                <span style="margin:0 6px;color:#D1D5DB">·</span>
                <strong class="${ce}">${oe}${C(l.amount)}</strong>`}X&&(X.style.display="");const de=document.getElementById("bank-cand-pane-body");if(de){de.innerHTML=`<div class="bank-empty">${t("bank-cand-loading")}</div>`;try{const oe=await fetch("/api/bank-recon/tx/"+encodeURIComponent(l.id)+"/candidates",{headers:{Authorization:"Bearer "+token}});if(!oe.ok)throw new Error("cands:"+oe.status);const ce=await oe.json();ee(l,ce.candidates||[])}catch{de.innerHTML=`<div class="bank-empty">${t("bank-cand-load-failed")}</div>`}}}function V(l){const j=Number(l||0);let O="score-low";return j>=85?O="score-high":j>=60&&(O="score-mid"),'<span class="bank-cand-score '+O+'">'+j.toFixed(0)+" "+t("bank-cand-score-unit")+"</span>"}function Q(l,j,O){const J=j.history_id,X=j.invoice_no||"-",de=j.vendor||"-",oe=j.amount_total!==null&&j.amount_total!==void 0?C(j.amount_total):"-",ce=j.invoice_date?T(j.invoice_date):"-",ae=j.filename||"",pe=!!O&&l.matched_history_id===J,ve="bank-cand-card"+(j.is_auto_picked?" is-auto":"")+(pe?" is-picked":"");let fe="";return pe?fe='<button class="btn btn-ghost btn-small" data-act="unmatch"><span>'+t("bank-cand-unmatch")+"</span></button>":fe='<button class="btn btn-primary btn-small" data-act="pick" data-hid="'+N(J)+'"><span>'+t(j.is_auto_picked?"bank-cand-confirm":"bank-cand-pick-this")+"</span></button>",'<div class="'+ve+'" data-hid="'+N(J)+'"><div class="bank-cand-card-head"><div class="bank-cand-card-vendor">'+N(de)+"</div>"+V(j.score)+'</div><div class="bank-cand-card-fields"><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-invoice-no")+"</span> "+N(X)+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-amount")+"</span> "+oe+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-date")+"</span> "+N(ce)+"</span></div>"+(ae?'<div class="bank-cand-card-file" title="'+N(ae)+'">'+N(ae)+"</div>":"")+(j.reason?'<div class="bank-cand-card-reason">'+N(j.reason)+"</div>":"")+'<div class="bank-cand-card-actions">'+fe+"</div></div>"}function ee(l,j){const O=document.getElementById("bank-cand-pane-body");if(!O)return;const J=j||[];let X="";if(l.match_status==="matched")X='<div class="bank-cand-hint hint-matched">'+t("bank-cand-hint-matched").replace("{n}",J.length)+"</div>";else if(l.match_status==="suggested")X='<div class="bank-cand-hint hint-suggested">'+t("bank-cand-hint-suggested").replace("{n}",J.length)+"</div>";else if(J.length>0)X='<div class="bank-cand-hint hint-low">'+t("bank-cand-hint-low").replace("{n}",J.length)+"</div>";else{O.innerHTML='<div class="bank-empty">'+t("bank-cand-no-match-detail")+"</div>";return}const de=l.match_status==="matched",oe=J.map(ce=>Q(l,ce,de)).join("");O.innerHTML=X+'<div class="bank-cand-list">'+oe+"</div>",O.querySelectorAll('[data-act="pick"]').forEach(ce=>{ce.addEventListener("click",()=>{I(ce.dataset.hid)})}),O.querySelectorAll('[data-act="unmatch"]').forEach(ce=>{ce.addEventListener("click",async()=>{try{await fetch("/api/bank-recon/tx/"+encodeURIComponent(l.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"unmatched"})}),ne(),await f(n.id)}catch{showToast(t("bank-action-failed"),"error")}})})}function ne(){const l=document.getElementById("bank-detail-body");l&&l.classList.remove("has-pane");const j=document.getElementById("bank-cand-pane-title"),O=document.getElementById("bank-cand-pane-sub"),J=document.getElementById("bank-cand-pane-body"),X=document.getElementById("bank-cand-pane-foot");j&&(j.textContent=t("bank-cand-pane-empty-title")),O&&(O.textContent=t("bank-cand-pane-empty-sub")),X&&(X.style.display="none"),J&&(J.innerHTML='<div class="bank-cand-pane-empty"><svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="14" y="10" width="36" height="44" rx="3"/><path d="M22 22h20M22 30h20M22 38h12"/></svg><div>'+t("bank-cand-pane-empty-hint")+"</div></div>");const de=document.getElementById("bank-tx-tbody");de&&de.querySelectorAll("tr.is-selected").forEach(oe=>oe.classList.remove("is-selected")),o=null}function se(l){const j=document.getElementById("bank-upload-progress");j&&(j.style.display="none")}function ue(){const l=document.getElementById("bank-upload-error");l&&(l.style.display="none")}function b(l){return{"bank_recon.only_pdf":t("bank-err-only-pdf"),"bank_recon.empty_file":t("bank-err-empty"),"bank_recon.file_too_large":t("bank-err-too-large"),"bank_recon.save_failed":t("bank-err-server"),"bank_recon.scanned":t("bank-err-scanned"),"bank_recon.no_tx":t("bank-err-no-tx"),network:t("bank-err-network")}[l]||t("bank-err-unknown")+" ("+l+")"}function C(l){if(l==null)return"-";const j=Number(l);return isNaN(j)?"-":j.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function T(l){if(!l)return"-";const j=String(l);return j.length>=10?j.slice(0,10):j}function U(l,j){return!l&&!j?"":(T(l)||"?")+" ~ "+(T(j)||"?")}function N(l){return l==null?"":String(l).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}window._loadBankReconPanel=r,window._rerenderBankRecon=function(){if(currentRoute==="automation"){if(_(),n&&(Y(),Z(),re(),!o)){const l=document.getElementById("bank-cand-pane-title"),j=document.getElementById("bank-cand-pane-sub");l&&(l.textContent=t("bank-cand-pane-empty-title")),j&&(j.textContent=t("bank-cand-pane-empty-sub"))}D()}},typeof window.subscribeI18n=="function"&&window.subscribeI18n("bank-recon",window._rerenderBankRecon),window._openBankSession=async function(l){l&&(m||await r(),await f(l))}})();(function(){const e=document.getElementById("page-clients");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");a[n][o]&&(s.textContent=a[n][o])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const o=s.getAttribute("data-i18n-placeholder");a[n][o]&&(s.placeholder=a[n][o])}))}catch{}}})();(function(){let e=[],n=null,a="",s="seller";const o={page:0,pageSize:12,keyword:""},m=new Set;let r=[];const k={keyword:""};let i=null;function f(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}async function u(p,$={}){const P=await fetch(p,{...$,headers:{"Content-Type":"application/json",...f(),...$.headers||{}}});if(!P.ok){const Y=await P.json().catch(()=>({}));throw new Error(Y.detail||"HTTP "+P.status)}return P.json()}async function c(){try{e=(await u("/api/clients")).clients||[],window._clientsCache=e}catch(p){console.error("loadClientsCache fail",p),e=[]}try{typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter()}catch{}try{typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher()}catch{}return e}function v(p){s=p==="buyer"?"buyer":"seller",document.querySelectorAll("[data-cust-tab]").forEach(Y=>Y.classList.toggle("active",Y.dataset.custTab===s));const $=document.getElementById("cust-pane-seller"),P=document.getElementById("cust-pane-buyer");$&&$.classList.toggle("active",s==="seller"),P&&P.classList.toggle("active",s==="buyer")}function E(){const p=window._userInfo||{},$=String(p.role||"").toLowerCase(),P=String(p.tenant_role||"").toLowerCase();return p.is_super_admin===!0||p.is_owner===!0||$==="owner"||$==="admin"||P==="owner"||P==="admin"}function x(){window._workspaceClientsCache=r,typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl()}async function R(){try{const p=await u("/api/workspace/clients");r=p&&(p.clients||p.items)||[],window._workspaceClientsCache=r}catch(p){console.error("loadSellerCache fail",p),r=[]}return r}function D(){const p=k.keyword.trim().toLowerCase();return p?r.filter($=>($.name||"").toLowerCase().includes(p)||($.tax_id||"").toLowerCase().includes(p)):r}function w(){const p=document.getElementById("seller-tbody");if(!p)return;const $=E(),P=document.getElementById("btn-seller-new");P&&(P.style.display=$?"":"none");const Y=D(),Z=typeof window.getActiveWorkspaceClientId=="function"?window.getActiveWorkspaceClientId():null;if(!Y.length){p.innerHTML=`<div class="cust-empty">${escapeHtml(t(k.keyword?"cust-no-match":"seller-empty"))}</div>`;return}p.innerHTML=Y.map(le=>{const V=Z!=null&&Number(Z)===Number(le.id)?`<span class="cust-badge-current"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7.5l3.2 3.2L12 4"/></svg>${escapeHtml(t("seller-current"))}</span>`:`<button class="cust-row-btn primary" data-saction="activate" data-wid="${le.id}">${escapeHtml(t("seller-set-current"))}</button>`,Q=$?`
                <button class="cust-row-btn" data-saction="edit" data-wid="${le.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
                <button class="cust-row-btn danger" data-saction="archive" data-wid="${le.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h10M4 4v7a1 1 0 001 1h4a1 1 0 001-1V4M5.5 4V2.8a1 1 0 011-1h1a1 1 0 011 1V4"/></svg><span>${escapeHtml(t("wsclient-archive"))}</span></button>`:"";return`<div class="cust-row seller-grid" data-wid="${le.id}">
                <div class="cust-cell-name"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" style="flex-shrink:0;opacity:.55"><rect x="2" y="5" width="12" height="9" rx="1"/><path d="M10 14V4a1 1 0 00-1-1H7a1 1 0 00-1 1v10"/></svg><span class="cust-name-text">${escapeHtml(le.name||"#"+le.id)}</span></div>
                <div class="cust-cell-tax">${escapeHtml(le.tax_id||"—")}</div>
                <div class="align-right">${le.invoice_count||0}</div>
                <div class="cust-row-actions">${V}${Q}</div>
            </div>`}).join("")}function B(p){i=p?p.id:null,document.getElementById("wsclient-modal-title").textContent=t(p?"wsclient-modal-edit":"wsclient-modal-new"),document.getElementById("wsclient-input-name").value=p&&p.name||"",document.getElementById("wsclient-input-tax").value=p&&p.tax_id||"",document.getElementById("wsclient-modal-archive").style.display=p?"":"none",document.getElementById("wsclient-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("wsclient-input-name").focus(),50)}function z(){document.getElementById("wsclient-modal-mask").style.display="none",i=null}async function q(){const p=document.getElementById("wsclient-input-name").value.trim(),$=document.getElementById("wsclient-input-tax").value.trim();if(!p){showToast(t("client-msg-name-required"),"fail");return}try{i?(await u("/api/workspace/clients/"+i,{method:"PATCH",body:JSON.stringify({name:p,tax_id:$})}),showToast(t("client-msg-updated"),"success")):(await u("/api/workspace/clients",{method:"POST",body:JSON.stringify({name:p,tax_id:$||null})}),showToast(t("client-msg-created"),"success")),z(),await R(),w(),x()}catch(P){const Y=P&&P.message?P.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+Y,"fail")}}async function F(){if(!i)return;const p=r.find(P=>Number(P.id)===Number(i));if(await showConfirm(t("wsclient-archive-confirm").replace("{name}",p?p.name:""),{danger:!0}))try{const P=i;await u("/api/workspace/clients/"+P,{method:"DELETE"}),showToast(t("wsclient-archived"),"success"),typeof window.getActiveWorkspaceClientId=="function"&&Number(window.getActiveWorkspaceClientId())===Number(P)&&typeof window.enterPersonalMode=="function"&&window.enterPersonalMode(),z(),await R(),w(),x()}catch{showToast(t("client-msg-save-fail"),"fail")}}function A(){const p=o.keyword.trim().toLowerCase();return p?e.filter($=>($.name||"").toLowerCase().includes(p)||($.short_name||"").toLowerCase().includes(p)||($.tax_id||"").toLowerCase().includes(p)):e}function g(){const p=A(),$=o.pageSize,P=Math.max(0,Math.ceil(p.length/$)-1);o.page>P&&(o.page=P);const Y=o.page*$;return{all:p,items:p.slice(Y,Y+$),start:Y,ps:$,total:p.length,maxPage:P}}function d(){const p=document.getElementById("buyer-tbody");if(!p)return;const{items:$,start:P,ps:Y,total:Z,maxPage:le}=g();Z?p.innerHTML=$.map(ee=>{const ne=m.has(ee.id);return`<div class="cust-row buyer-grid${ne?" selected":""}" data-cid="${ee.id}">
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
                </div>`}).join(""):p.innerHTML=`<div class="cust-empty">${escapeHtml(t(o.keyword?"cust-no-match":"clients-empty"))}</div>`;const ie=document.getElementById("buyer-pager-info");ie&&(ie.textContent=Z?`${P+1}–${Math.min(P+Y,Z)} / ${Z}`:"0");const V=document.getElementById("buyer-prev");V&&(V.disabled=o.page<=0);const Q=document.getElementById("buyer-next");Q&&(Q.disabled=o.page>=le),h()}function h(){const p=m.size,$=document.getElementById("buyer-batch-bar");$&&($.style.display=p?"flex":"none");const P=document.getElementById("buyer-batch-count");P&&(P.textContent=t("cust-selected-n").replace("{n}",p));const Y=document.getElementById("buyer-check-all");if(Y){const{items:Z}=g(),le=Z.map(V=>V.id),ie=le.filter(V=>m.has(V)).length;Y.checked=le.length>0&&ie===le.length,Y.indeterminate=ie>0&&ie<le.length}}function I(){m.clear(),d()}async function L(){const p=Array.from(m);if(!(!p.length||!await showConfirm(t("cust-batch-del-confirm").replace("{n}",p.length),{danger:!0})))try{await u("/api/clients/batch-delete",{method:"POST",body:JSON.stringify({ids:p})}),showToast(t("client-msg-deleted"),"success"),m.clear(),await c(),d(),te(),y()}catch{showToast(t("client-msg-save-fail"),"fail")}}window.loadClientsPage=async function(){const p=document.getElementById("seller-tbody");p&&(p.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`);const $=document.getElementById("buyer-tbody");$&&($.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`),await Promise.all([R(),c()]),w(),d()},window.addEventListener("pearnly:workspace-changed",function(){typeof currentRoute<"u"&&currentRoute==="clients"&&w()});function H(p){n=p?p.id:null;const $=!!p;document.getElementById("client-modal-title").textContent=t($?"client-modal-edit":"client-modal-new"),document.getElementById("client-input-name").value=p&&p.name||"",document.getElementById("client-input-short").value=p&&p.short_name||"",document.getElementById("client-input-tax").value=p&&p.tax_id||"",document.getElementById("client-input-address").value=p&&p.address||"",document.getElementById("client-input-contact").value=p&&p.contact_person||"",document.getElementById("client-input-phone").value=p&&p.contact_phone||"",document.getElementById("client-input-email").value=p&&p.contact_email||"",document.getElementById("client-input-notes").value=p&&p.notes||"";const P=p&&p.color||"#111111";document.querySelectorAll("#client-color-picker .color-swatch").forEach(Y=>{Y.classList.toggle("active",Y.dataset.color===P)}),document.getElementById("client-modal-delete").style.display=$?"":"none",document.getElementById("client-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("client-input-name").focus(),50)}function _(){document.getElementById("client-modal-mask").style.display="none",n=null}function M(){const p=document.querySelector("#client-color-picker .color-swatch.active");return p?p.dataset.color:"#111111"}async function K(){const p=document.getElementById("client-input-name").value.trim();if(!p){showToast(t("client-msg-name-required"),"fail");return}const $={name:p,short_name:document.getElementById("client-input-short").value.trim()||null,tax_id:document.getElementById("client-input-tax").value.trim()||null,address:document.getElementById("client-input-address").value.trim()||null,contact_person:document.getElementById("client-input-contact").value.trim()||null,contact_phone:document.getElementById("client-input-phone").value.trim()||null,contact_email:document.getElementById("client-input-email").value.trim()||null,notes:document.getElementById("client-input-notes").value.trim()||null,color:M()};try{n?(await u(`/api/clients/${n}`,{method:"PATCH",body:JSON.stringify($)}),showToast(t("client-msg-updated"),"success")):(await u("/api/clients",{method:"POST",body:JSON.stringify($)}),showToast(t("client-msg-created"),"success")),_(),await c(),currentRoute==="clients"&&d(),te(),y()}catch(P){console.error("saveClient fail",P);const Y=P&&P.message?P.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+Y,"fail")}}async function G(){if(!n)return;const p=e.find(Y=>Y.id===n);if(!p)return;const $=t("client-delete-confirm").replace("{name}",p.name);if(await showConfirm($,{danger:!0}))try{await u(`/api/clients/${n}`,{method:"DELETE"}),showToast(t("client-msg-deleted"),"success"),_(),await c(),currentRoute==="clients"&&d(),te(),y()}catch(Y){console.error(Y),showToast(t("client-msg-save-fail"),"fail")}}async function W(p){const $=e.find(P=>P.id===p);if(typeof window.openClientExportModal=="function"){window.openClientExportModal(p,$?$.name:"");return}try{const P=localStorage.getItem("mrpilot_token"),Y=await fetch(`/api/clients/${p}/export?month=all`,{headers:{Authorization:"Bearer "+P}});if(!Y.ok){let Q="HTTP "+Y.status;try{const ee=await Y.json();ee&&ee.detail&&(Q=ee.detail)}catch{}throw new Error(Q)}const Z=await Y.blob();if(Z.size<200){showToast(t("client-export-month-empty"),"info");return}const le=$&&$.name?$.name.replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40):"client",ie=URL.createObjectURL(Z),V=document.createElement("a");V.href=ie,V.download=`${le}_export.csv`,V.click(),URL.revokeObjectURL(ie)}catch(P){console.error("exportClient fail",P),showToast(t("client-msg-save-fail")+" · "+(P.message||""),"fail")}}function te(){const p=document.getElementById("drawer-client-select");if(!p)return;const $=p.value;p.innerHTML=`<option value="">${escapeHtml(t("drawer-client-none"))}</option>`+e.map(P=>`<option value="${P.id}">${escapeHtml(P.name)}</option>`).join(""),p.value=$||""}window.bindDrawerClient=function(p,$){const P=document.getElementById("drawer-client-select");if(!P)return;if(te(),P.value=$?String($):"",!p){P.onchange=null;const Z=document.getElementById("drawer-client-add");Z&&(Z.onclick=()=>H(null));return}P.onchange=async()=>{const Z=P.value?parseInt(P.value,10):null;try{await u(`/api/history/${p}/assign_client`,{method:"POST",body:JSON.stringify({client_id:Z})}),showToast(t("client-msg-updated"),"success");const le=_results[_drawerIdx];le&&(le.client_id=Z),await c()}catch(le){console.error(le),showToast(t("client-msg-save-fail"),"fail"),P.value=$?String($):""}};const Y=document.getElementById("drawer-client-add");Y&&(Y.onclick=()=>H(null))};let re={fetched:0,items:[],supplier_count:0};window.fillCategoryDatalist=async function(){try{const p=document.getElementById("drawer-cat-datalist"),$=Date.now();if($-re.fetched<300*1e3){p&&(p.innerHTML=re.items.map(Y=>`<option value="${escapeHtml(Y)}">`).join("")),S(re.supplier_count);return}const P=await u("/api/categories",{method:"GET"});re.fetched=$,re.items=P&&P.categories||[],re.supplier_count=P&&P.supplier_count||0,p&&(p.innerHTML=re.items.map(Y=>`<option value="${escapeHtml(Y)}">`).join("")),S(re.supplier_count)}catch(p){console.warn("fillCategoryDatalist failed",p)}};function S(p){const $=document.getElementById("drawer-cat-learned-tag");$&&p>0&&($.textContent=(t("drawer-suggest-learned-with-count")||"已学 {n}").replace("{n}",p))}function y(){const p=document.getElementById("history-client-filter");if(!p)return;const $=p.value;p.innerHTML=`<option value="">${escapeHtml(t("history-client-all"))}</option>`+e.map(P=>`<option value="${P.id}">${escapeHtml(P.name)}</option>`).join(""),p.value=$||""}window.getHistoryClientFilter=function(){return a},document.addEventListener("DOMContentLoaded",()=>{const p=document.querySelector(".cust-tab-bar");p&&p.addEventListener("click",ae=>{const pe=ae.target.closest("[data-cust-tab]");pe&&v(pe.dataset.custTab)});const $=document.getElementById("btn-buyer-new");$&&$.addEventListener("click",()=>H(null));const P=document.getElementById("buyer-tbody");P&&P.addEventListener("click",ae=>{const pe=ae.target.closest(".buyer-row-check");if(pe){const ge=parseInt(pe.dataset.cid,10);pe.checked?m.add(ge):m.delete(ge);const be=pe.closest(".cust-row");be&&be.classList.toggle("selected",pe.checked),h();return}const ve=ae.target.closest(".cust-row-btn");if(ve){ae.stopPropagation();const ge=parseInt(ve.dataset.cid,10);if(ve.dataset.action==="edit"){const be=e.find(xe=>xe.id===ge);be&&H(be)}else ve.dataset.action==="export"&&W(ge);return}const fe=ae.target.closest(".cust-row");if(fe&&!ae.target.closest(".cust-cell-check")){const ge=e.find(be=>be.id===parseInt(fe.dataset.cid,10));ge&&H(ge)}});const Y=document.getElementById("buyer-check-all");Y&&Y.addEventListener("change",()=>{const{items:ae}=g();ae.forEach(pe=>{Y.checked?m.add(pe.id):m.delete(pe.id)}),d()});const Z=document.getElementById("buyer-batch-cancel");Z&&Z.addEventListener("click",I);const le=document.getElementById("buyer-batch-delete");le&&le.addEventListener("click",L);const ie=document.getElementById("buyer-prev");ie&&ie.addEventListener("click",()=>{o.page>0&&(o.page--,d())});const V=document.getElementById("buyer-next");V&&V.addEventListener("click",()=>{o.page++,d()});const Q=document.getElementById("buyer-search");if(Q){let ae;Q.addEventListener("input",()=>{clearTimeout(ae),ae=setTimeout(()=>{o.keyword=Q.value,o.page=0;const pe=document.getElementById("buyer-search-clear");pe&&(pe.style.display=Q.value?"":"none"),d()},200)})}const ee=document.getElementById("buyer-search-clear");ee&&ee.addEventListener("click",()=>{const ae=document.getElementById("buyer-search");ae&&(ae.value=""),o.keyword="",o.page=0,ee.style.display="none",d()});const ne=document.getElementById("btn-seller-new");ne&&ne.addEventListener("click",()=>B(null));const se=document.getElementById("seller-tbody");se&&se.addEventListener("click",ae=>{const pe=ae.target.closest("[data-saction]");if(!pe)return;ae.stopPropagation();const ve=parseInt(pe.dataset.wid,10),fe=pe.dataset.saction,ge=r.find(be=>Number(be.id)===ve);fe==="activate"?(typeof window.setActiveWorkspaceClientId=="function"&&window.setActiveWorkspaceClientId(ve),w(),typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl(),showToast(t("seller-activated").replace("{name}",ge?ge.name:""),"success")):fe==="edit"?ge&&B(ge):fe==="archive"&&(i=ve,F())});const ue=document.getElementById("seller-search");if(ue){let ae;ue.addEventListener("input",()=>{clearTimeout(ae),ae=setTimeout(()=>{k.keyword=ue.value;const pe=document.getElementById("seller-search-clear");pe&&(pe.style.display=ue.value?"":"none"),w()},200)})}const b=document.getElementById("seller-search-clear");b&&b.addEventListener("click",()=>{const ae=document.getElementById("seller-search");ae&&(ae.value=""),k.keyword="",b.style.display="none",w()});const C=document.getElementById("wsclient-modal-close");C&&C.addEventListener("click",z);const T=document.getElementById("wsclient-modal-cancel");T&&T.addEventListener("click",z);const U=document.getElementById("wsclient-modal-save");U&&U.addEventListener("click",q);const N=document.getElementById("wsclient-modal-archive");N&&N.addEventListener("click",F);const l=document.getElementById("wsclient-modal-mask");l&&l.addEventListener("click",ae=>{ae.target===l&&z()});const j=document.getElementById("client-modal-close");j&&j.addEventListener("click",_);const O=document.getElementById("client-modal-cancel");O&&O.addEventListener("click",_);const J=document.getElementById("client-modal-save");J&&J.addEventListener("click",K);const X=document.getElementById("client-modal-delete");X&&X.addEventListener("click",G);const de=document.getElementById("client-modal-mask");de&&de.addEventListener("click",ae=>{ae.target===de&&_()});const oe=document.getElementById("client-color-picker");oe&&oe.addEventListener("click",ae=>{const pe=ae.target.closest(".color-swatch");pe&&(oe.querySelectorAll(".color-swatch").forEach(ve=>ve.classList.remove("active")),pe.classList.add("active"))});const ce=document.getElementById("history-client-filter");ce&&ce.addEventListener("change",()=>{a=ce.value,typeof renderHistoryList=="function"&&renderHistoryList()})}),setTimeout(()=>c(),1e3)})();(function(){const e=document.getElementById("page-exceptions");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");a[n][o]&&(s.textContent=a[n][o])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const o=s.getAttribute("data-i18n-placeholder");a[n][o]&&(s.placeholder=a[n][o])}))}catch{}}})();(function(){let e={statsCache:null,listCache:[],currentRule:null,currentClient:"",currentStatus:"pending",loading:!1,selectedIds:new Set,offset:0,pageSize:50,total:0,loadFailed:!1,listScrollY:0};function n(S,y){let p=t(S)||S;if(y)for(const $ in y)p=p.replace(new RegExp("\\{"+$+"\\}","g"),String(y[$]));return p}async function a(){try{const S=e.currentClient||"",y="/api/exceptions/stats?status=pending"+(S?"&client_id="+encodeURIComponent(S):""),p=await fetch(y,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!p.ok)return;const $=await p.json(),P=document.getElementById("nav-exc-badge");if(!P)return;const Y=parseInt($.pending||0,10);Y>0?(P.textContent=Y>99?"99+":String(Y),P.style.display=""):P.style.display="none"}catch{}}function s(S){return S==="high"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
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
        </svg>`}function o(){return`<svg class="exc-empty-icon" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 19l5 5 13-13"/>
            <circle cx="20" cy="20" r="17"/>
        </svg>`}function m(S){if(S==null)return"—";const y=parseFloat(S);return isNaN(y)?"—":"฿ "+y.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function r(S){return S?S.slice(0,10):"—"}function k(S){document.getElementById("exc-kpi-pending").textContent=S.pending||0,document.getElementById("exc-kpi-high").textContent=S.high_severity||0,document.getElementById("exc-kpi-resolved").textContent=S.resolved||0,document.getElementById("exc-kpi-learned").textContent=S.learned_rules||0;const y=document.getElementById("exc-status-tab-count-pending"),p=document.getElementById("exc-status-tab-count-resolved"),$=document.getElementById("exc-status-tab-count-ignored");y&&(y.textContent=S.pending||0),p&&(p.textContent=S.resolved||0),$&&($.textContent=S.ignored||0),document.querySelectorAll("#exc-status-tabs .exc-status-tab").forEach(Y=>{Y.classList.toggle("active",Y.dataset.status===(e.currentStatus||"pending"))})}function i(S){const y=document.getElementById("exc-chips");if(!y)return;const p=S.by_rule||{},$=["confidence_low","duplicate","amount_missing","math_mismatch","tax_id_format_invalid"];let Y=`<button class="exc-chip ${!e.currentRule?"active":""}" data-rule="">
            <span>${escapeHtml(t("exc-chip-all"))}</span>
            <span class="exc-chip-count">${S.pending||0}</span>
        </button>`;for(const Z of $){const le=p[Z]||0;if(le===0&&e.currentRule!==Z)continue;const ie=e.currentRule===Z;Y+=`<button class="exc-chip ${ie?"active":""}" data-rule="${escapeHtml(Z)}">
                <span>${escapeHtml(t("exc-chip-"+Z))}</span>
                <span class="exc-chip-count">${le}</span>
            </button>`}y.innerHTML=Y,y.querySelectorAll(".exc-chip").forEach(Z=>{Z.addEventListener("click",()=>{const le=Z.dataset.rule||null;e.currentRule=le,x()})})}function f(S){const y=document.getElementById("exc-list");if(!y)return;if(!S||S.length===0){y.innerHTML=`<div class="exc-empty">
                ${o()}
                <div class="exc-empty-title">${escapeHtml(t("exc-empty-title"))}</div>
                <div>${escapeHtml(t("exc-empty-desc"))}</div>
            </div>`,c();return}const p='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7l3 3 5-5"/></svg>',$=(e.currentStatus||"pending")==="pending";y.innerHTML=S.map(P=>{const Y=P.severity||"medium",Z=t("exc-rule-"+P.rule_code)||P.rule_code,le=P.seller_name&&P.seller_name.trim()?P.seller_name:t("exc-no-seller"),ie=P.filename||"—",V=r(P.invoice_date||P.created_at),Q=P.status==="pending",ee=e.selectedIds.has(P.id),ne=$&&Q;return`
                <div class="exc-row sev-${escapeHtml(Y)} ${ee?"selected":""}" data-exc-id="${escapeHtml(String(P.id))}">
                    <div class="exc-row-check ${ee?"checked":""}" data-check-id="${escapeHtml(String(P.id))}" ${ne?"":'style="visibility:hidden;"'}>${p}</div>
                    <div class="exc-row-sev">${s(Y)}</div>
                    <div class="exc-row-main">
                        <div class="exc-row-title">${escapeHtml(le)} · ${escapeHtml(ie)}</div>
                        <div class="exc-row-meta">
                            ${P.invoice_no?`<span><b>${escapeHtml(P.invoice_no)}</b></span>`:""}
                            <span>${escapeHtml(V)}</span>
                        </div>
                    </div>
                    <div class="exc-row-rule r-${escapeHtml(Y)}">${escapeHtml(Z)}</div>
                    <div class="exc-row-amount">${escapeHtml(m(P.total_amount))}</div>
                </div>
            `}).join(""),y.querySelectorAll(".exc-row").forEach(P=>{P.addEventListener("click",Y=>{if(Y.target.closest(".exc-row-check"))return;const Z=P.dataset.excId;Z&&q(parseInt(Z,10))})}),y.querySelectorAll(".exc-row-check").forEach(P=>{P.addEventListener("click",Y=>{Y.stopPropagation();const Z=parseInt(P.dataset.checkId,10);Z&&(e.selectedIds.has(Z)?(e.selectedIds.delete(Z),P.classList.remove("checked"),P.closest(".exc-row").classList.remove("selected")):(e.selectedIds.add(Z),P.classList.add("checked"),P.closest(".exc-row").classList.add("selected")),u())})}),u(),c()}function u(){const S=document.getElementById("exc-batch-bar"),y=document.getElementById("exc-batch-count");if(!S||!y)return;const p=e.selectedIds.size;p===0?S.style.display="none":(S.style.display="",y.textContent=n("exc-batch-count",{n:p}))}function c(){const S=document.getElementById("exc-list-foot"),y=document.getElementById("exc-list-count"),p=document.getElementById("exc-loadmore");if(!S||!y||!p)return;const $=e.listCache.length;if($===0){S.style.display="none";return}S.style.display="";let P=$;const Y=e.statsCache;Y&&(e.currentRule?P=(Y.by_rule||{})[e.currentRule]||$:P=Y.pending||$),e.total=P,y.textContent=n("exc-list-count",{shown:$,total:P});const Z=$<P&&$<500;p.style.display=Z?"":"none"}async function v(){try{if(navigator.onLine===!1)throw new Error("offline");const S=e.currentClient||"",y=e.currentStatus||"pending",p=new URLSearchParams;p.set("status",y),S&&p.set("client_id",S);const $="/api/exceptions/stats?"+p.toString(),P=await fetch($,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!P.ok)throw new Error("http "+P.status);const Y=await P.json();return e.statsCache=Y,k(Y),i(Y),Y}catch(S){return console.warn("loadExceptionsStats fail",S),null}}function E(S){const y=document.getElementById("exc-list");if(!y)return;const p=`<svg class="exc-error-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="18" cy="18" r="14"/>
            <line x1="18" y1="11" x2="18" y2="19"/>
            <circle cx="18" cy="23" r="0.8" fill="currentColor"/>
        </svg>`,$=S?t("exc-offline"):t("exc-error-retry-title"),P=S?"":t("exc-error-retry-desc");y.innerHTML=`
            <div class="exc-error">
                ${p}
                <div class="exc-error-msg">${escapeHtml($)}${P?" · "+escapeHtml(P):""}</div>
                <button class="btn btn-sm btn-secondary" id="exc-retry-btn" type="button">${escapeHtml(t("exc-retry-btn"))}</button>
            </div>`;const Y=document.getElementById("exc-retry-btn");Y&&Y.addEventListener("click",()=>window.loadExceptionsPage&&window.loadExceptionsPage())}async function x(S){S=S||{};const y=!!S.append,p=document.getElementById("exc-list");!y&&p&&e.listCache.length===0&&(p.innerHTML=`<div class="exc-loading">${escapeHtml(t("exc-loading"))}</div>`);const $=new URLSearchParams;$.set("status",e.currentStatus||"pending"),e.currentRule&&$.set("rule_code",e.currentRule),e.currentClient&&$.set("client_id",e.currentClient);const P=y?e.listCache.length:0;$.set("limit",String(e.pageSize)),$.set("offset",String(P));try{if(navigator.onLine===!1)throw new Error("offline");const Y=await fetch("/api/exceptions/list?"+$.toString(),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!Y.ok)throw new Error("http "+Y.status);const le=(await Y.json()).items||[];y?e.listCache=e.listCache.concat(le):(e.listCache=le,e.selectedIds.clear()),e.loadFailed=!1,f(e.listCache),e.statsCache&&i(e.statsCache)}catch(Y){console.warn("loadExceptionsList fail",Y),e.loadFailed=!0;const Z=navigator.onLine===!1||String(Y.message||"").includes("offline");y?showToast(t("exc-toast-load-fail"),"error"):(E(Z),showToast(Z?t("exc-offline"):t("exc-toast-load-fail"),"error"))}}async function R(){if(!e.loading&&!(e.listCache.length>=500)){e.loading=!0;try{await x({append:!0})}finally{e.loading=!1}}}function D(){const S=document.getElementById("exc-client-filter");if(!S)return;const y=window._clientsCache||[],p=e.currentClient||"",$=typeof t=="function"?t("history-client-all"):"全部客户";S.innerHTML=`<option value="">${escapeHtml($)}</option>`+y.map(P=>`<option value="${P.id}">${escapeHtml(P.name)}</option>`).join(""),S.value=p}window.loadExceptionsPage=async function(){if(!e.loading){e.loading=!0;try{D(),typeof window.loadErpExceptions=="function"&&window.loadErpExceptions(),await v(),await x()}finally{e.loading=!1}}},window.refreshExcBadge=a,window._refreshExcClientFilter=D,window._excState=e,window._rerenderExceptions=function(){try{D()}catch{}e.statsCache&&(k(e.statsCache),i(e.statsCache)),e.listCache&&e.listCache.length&&f(e.listCache);try{window._erpExcState&&window._erpExcState.items&&window._erpExcState.items.length&&typeof window._rerenderErpExceptions=="function"&&window._rerenderErpExceptions()}catch{}w.openExcId&&I()};let w={openExcId:null,excRow:null,history:null,loading:!1,pdfUrl:null,pdfStatus:"idle",editing:!1,editFields:null};function B(){if(w.pdfUrl){try{URL.revokeObjectURL(w.pdfUrl)}catch{}w.pdfUrl=null}w.pdfStatus="idle"}async function z(S,y){w.pdfStatus="loading",I();try{const p=await fetch("/api/history/"+encodeURIComponent(S)+"/pdf",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(w.openExcId!==y)return;if(p.status===404){w.pdfStatus="empty",I();return}if(!p.ok)throw new Error("http "+p.status);const $=await p.blob();if(w.openExcId!==y)return;B(),w.pdfUrl=URL.createObjectURL($),w.pdfStatus="ready",I()}catch(p){if(w.openExcId!==y)return;console.warn("loadDrawerPdf fail",p),w.pdfStatus="error",I()}}function q(S){const y=(e.listCache||[]).find(p=>p.id===S);if(!y){showToast(t("exc-drawer-error"),"error");return}e.listScrollY=window.scrollY||document.documentElement.scrollTop||0,B(),w.editing=!1,w.editFields=null,w.openExcId=S,w.excRow=y,w.history=null,document.getElementById("exc-drawer-mask").classList.add("show"),document.getElementById("exc-drawer").classList.add("show"),I(),A(y.history_id),z(y.history_id,S)}function F(){B(),w.editing=!1,w.editFields=null,w.openExcId=null,w.excRow=null,w.history=null,document.getElementById("exc-drawer-mask").classList.remove("show"),document.getElementById("exc-drawer").classList.remove("show");const S=e.listScrollY||0;S>0&&requestAnimationFrame(()=>window.scrollTo(0,S))}async function A(S){try{const y=await fetch("/api/history/"+encodeURIComponent(S),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!y.ok)throw new Error("http "+y.status);w.history=await y.json()}catch(y){console.warn("loadHistoryDetail fail",y),w.history={_err:!0}}w.excRow&&I()}function g(S){if(!S||!S.pages)return{};const y=S.pages,p=y.find($=>!$.is_duplicate&&!$.is_copy)||y[0];return p&&p.fields||{}}function d(S){if(S==null)return"—";const y=typeof S=="number"?S:parseFloat(String(S).replace(/,/g,""));return isNaN(y)?escapeHtml(String(S)):"฿ "+y.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function h(S,y){if(y=y||{},S==="math_mismatch")return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-subtotal"))}</b><span>${escapeHtml(d(y.subtotal))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-vat"))}</b><span>${escapeHtml(d(y.vat))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(d(y.total_expected))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-actual"))}</b><span class="v-bad">${escapeHtml(d(y.total_actual))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-diff"))}</b><span class="v-bad">${escapeHtml(d(y.diff))}</span></div>
            `;if(S==="tax_id_format_invalid")return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-seller-tax"))}</b><span class="v-bad">${escapeHtml(y.tax_id_normalized||y.tax_id_raw||"—")}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-tax-len"))}</b><span class="v-bad">${escapeHtml(String(y.actual_length||"?"))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(t("exc-detail-tax-expected"))}</span></div>
            `;if(S==="duplicate"){const p=y.level==="exact"?t("exc-detail-dup-level-exact"):t("exc-detail-dup-level-likely");return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-dup-match"))}</b><span>${escapeHtml(y.match_filename||"—")}</span></div>
                ${y.match_invoice_no?`<div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-invoice-no"))}</b><span>${escapeHtml(y.match_invoice_no)}</span></div>`:""}
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span>${escapeHtml(p)}</span></div>
            `}return S==="confidence_low"?`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-conf-label"))}</b><span class="v-bad">${escapeHtml(y.confidence||"—")}</span></div>
            `:S==="amount_missing"?`<div class="exc-why-detail-row" style="justify-content:center;color:var(--danger);"><span>${escapeHtml(t("exc-detail-missing"))}</span></div>`:`<div class="exc-why-detail-row"><span style="font-size:11px;">${escapeHtml(JSON.stringify(y))}</span></div>`}function I(){const S=w.excRow;if(!S)return;const y=S.seller_name&&S.seller_name.trim()?S.seller_name:t("exc-no-seller"),p=S.filename||"—";document.getElementById("exc-drawer-title").textContent=p;const $="exc-status-"+(S.status||"pending"),P=t($)||S.status,Y="s-"+(S.status||"pending"),Z=(S.invoice_date||S.created_at||"").slice(0,10);document.getElementById("exc-drawer-sub").innerHTML=`
            <span>${escapeHtml(y)}</span>
            ${S.invoice_no?`<span>· ${escapeHtml(S.invoice_no)}</span>`:""}
            ${Z?`<span>· ${escapeHtml(Z)}</span>`:""}
            <span class="exc-status-chip ${Y}">${escapeHtml(P)}</span>
        `;const le=S.severity||"medium",ie=t("exc-rule-"+S.rule_code)||S.rule_code,V=h(S.rule_code,S.detail||{}),Q=g(w.history),ee=w.history===null,ne=w.history&&w.history._err,se=new Set;S.rule_code==="math_mismatch"?(se.add("subtotal"),se.add("vat"),se.add("total_amount")):S.rule_code==="tax_id_format_invalid"?se.add("seller_tax"):S.rule_code==="amount_missing"&&(se.add("total_amount"),se.add("invoice_number"));const ue=!!w.editing,b=w.editFields||{},C=(ae,pe,ve)=>{if(ee)return`<div class="exc-field-row"><label>${escapeHtml(t(pe))}</label><span class="val empty">…</span></div>`;const fe=ue?b[ae]!==void 0?b[ae]:Q[ae]!==void 0&&Q[ae]!==null?Q[ae]:"":Q[ae],ge=se.has(ae)?"flagged":"";if(ue){const De=ve?"number":"text",Le=ve?' step="0.01" inputmode="decimal"':"",Ce=fe==null?"":String(fe).replace(/"/g,"&quot;");return`<div class="exc-field-row ${ge} editing">
                    <label>${escapeHtml(t(pe))}</label>
                    <input class="exc-field-input" type="${De}"${Le} data-edit-key="${escapeHtml(ae)}" value="${Ce}">
                </div>`}const be=ve?d(fe):fe||"",xe=fe==null||fe===""?`<span class="val empty">${escapeHtml(t("exc-empty-val"))}</span>`:`<span class="val">${escapeHtml(be)}</span>`;return`<div class="exc-field-row ${ge}"><label>${escapeHtml(t(pe))}</label>${xe}</div>`};let T="";ne?T=`<div class="exc-drawer-error">${escapeHtml(t("exc-drawer-error"))}</div>`:T=`
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
            `;const U=(()=>{if(w.pdfStatus==="loading"||w.pdfStatus==="idle")return`
                    <div class="exc-pdf-toolbar">
                        <span class="exc-pdf-toolbar-title">${escapeHtml(t("exc-pdf-loading"))}</span>
                    </div>
                    <div class="exc-pdf-empty">
                        <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M18 4v8a14 14 0 1014 14"/>
                        </svg>
                        <div class="exc-pdf-empty-msg">${escapeHtml(t("exc-pdf-loading"))}</div>
                    </div>
                `;if(w.pdfStatus==="empty")return`
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
                `;if(w.pdfStatus==="error")return`
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
                `;const ae=w.pdfUrl;return`
                <div class="exc-pdf-toolbar">
                    <span class="exc-pdf-toolbar-title">${escapeHtml(p)}</span>
                    <div class="exc-pdf-toolbar-actions">
                        <a class="exc-pdf-icon-btn" id="exc-pdf-open-tab" href="${ae}" target="_blank" rel="noopener" title="${escapeHtml(t("exc-pdf-open-tab"))}">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M8 2h4v4M12 2L7 7"/>
                                <path d="M11 8v3a1 1 0 01-1 1H3a1 1 0 01-1-1V4a1 1 0 011-1h3"/>
                            </svg>
                        </a>
                        <a class="exc-pdf-icon-btn" id="exc-pdf-download" href="${ae}" download="${escapeHtml(p)}" title="${escapeHtml(t("exc-pdf-download"))}">
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
        `;const N=document.getElementById("exc-fld-edit");N&&N.addEventListener("click",()=>{w.editing=!0,w.editFields={...g(w.history)},I()});const l=document.getElementById("exc-fld-cancel");l&&l.addEventListener("click",()=>{w.editing=!1,w.editFields=null,I()});const j=document.getElementById("exc-fld-save");j&&j.addEventListener("click",()=>L()),document.querySelectorAll(".exc-field-input").forEach(ae=>{ae.addEventListener("input",()=>{w.editFields||(w.editFields={}),w.editFields[ae.dataset.editKey]=ae.value})});const J=document.getElementById("exc-pdf-retry");J&&w.openExcId&&J.addEventListener("click",()=>{w.excRow&&z(w.excRow.history_id,w.openExcId)});const X=S.status==="pending",de=!!(S.seller_name&&S.seller_name.trim()),oe=document.getElementById("exc-btn-resolve"),ce=document.getElementById("exc-btn-ignore");oe.disabled=!X,ce.disabled=!X||!de,ce.title=de?t("exc-ignore-hint"):t("exc-ignore-no-seller")}async function L(){if(!w.openExcId||!w.history||!w.history.pages||w.loading)return;w.loading=!0;const S=showToast(t("exc-fld-saving"),"loading",0);try{const y=JSON.parse(JSON.stringify(w.history.pages||[]));let p=y.findIndex(ie=>!ie.is_duplicate&&!ie.is_copy);p<0&&(p=0),y[p]||(y[p]={fields:{}});const $=y[p].fields||{},P=w.editFields||{},Y=new Set(["subtotal","vat","total_amount"]),Z={...$};for(const ie in P){let V=P[ie];if((V===""||V===void 0)&&(V=null),Y.has(ie)&&V!==null){const Q=parseFloat(V);V=isNaN(Q)?null:Q}Z[ie]=V}y[p].fields=Z;const le=await fetch("/api/history/"+encodeURIComponent(w.history.id),{method:"PUT",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({pages:y})});if(!le.ok)throw new Error("http "+le.status);S(),showToast(t("exc-fld-save-ok"),"success"),F(),await v(),await x(),a()}catch(y){S(),console.warn("save fields fail",y),showToast(t("exc-fld-save-fail"),"error")}finally{w.loading=!1}}async function H(){if(!(!w.openExcId||w.loading)){w.loading=!0;try{const S=await fetch("/api/exceptions/"+w.openExcId+"/resolve",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!S.ok)throw new Error("http "+S.status);showToast(t("exc-toast-resolved"),"success"),F(),await v(),await x(),a()}catch(S){console.warn("resolve fail",S),showToast(t("exc-toast-action-fail"),"error")}finally{w.loading=!1}}}async function _(){if(!(!w.openExcId||w.loading)){w.loading=!0;try{const S=await fetch("/api/exceptions/"+w.openExcId+"/ignore",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!S.ok)throw new Error("http "+S.status);showToast(t("exc-toast-ignored"),"success"),F(),await v(),await x(),a()}catch(S){console.warn("ignore fail",S),showToast(t("exc-toast-action-fail"),"error")}finally{w.loading=!1}}}let M=!1;async function K(){if(M)return;const S=Array.from(e.selectedIds);if(S.length===0||!await showConfirm(n("exc-batch-confirm-resolve",{n:S.length})))return;M=!0;const p=showToast(n("exc-batch-count",{n:S.length})+" …","loading",0);try{const $=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:S,action:"resolve"})});if(!$.ok)throw new Error("http "+$.status);const P=await $.json();p(),showToast(n("exc-toast-batch-resolved",{n:P.processed||0}),"success"),e.selectedIds.clear(),await v(),await x(),a()}catch($){p(),console.warn("batch resolve fail",$),showToast(t("exc-toast-batch-fail"),"error")}finally{M=!1}}async function G(){if(M)return;const S=Array.from(e.selectedIds);if(S.length===0||!await showConfirm(n("exc-batch-confirm-ignore",{n:S.length}),{danger:!1}))return;M=!0;const p=showToast(n("exc-batch-count",{n:S.length})+" …","loading",0);try{const $=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:S,action:"ignore"})});if(!$.ok)throw new Error("http "+$.status);const P=await $.json();p(),showToast(n("exc-toast-batch-ignored",{n:P.processed||0,wl:P.whitelist_added||0}),"success"),e.selectedIds.clear(),await v(),await x(),a()}catch($){p(),console.warn("batch ignore fail",$),showToast(t("exc-toast-batch-fail"),"error")}finally{M=!1}}function W(){e.selectedIds.clear(),f(e.listCache)}document.addEventListener("click",S=>{S.target.closest("#exc-drawer-close")&&F(),S.target.closest("#exc-drawer-mask")&&F(),S.target.closest("#exc-btn-resolve")&&H(),S.target.closest("#exc-btn-ignore")&&_(),S.target.closest("#exc-batch-resolve")&&K(),S.target.closest("#exc-batch-ignore")&&G(),S.target.closest("#exc-batch-clear")&&W(),S.target.closest("#exc-loadmore")&&R()}),document.addEventListener("keydown",S=>{S.key==="Escape"&&w.openExcId&&F()}),document.addEventListener("click",S=>{S.target.closest("#btn-exc-refresh")&&(typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),a())}),document.addEventListener("change",S=>{if(!S.target.closest("#exc-client-filter"))return;const y=S.target;e.currentClient=y.value||"",e.currentRule=null,e.selectedIds.clear(),e.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),a()}),document.addEventListener("click",S=>{const y=S.target.closest("#exc-status-tabs .exc-status-tab");if(!y)return;const p=y.dataset.status||"pending";p!==e.currentStatus&&(e.currentStatus=p,e.currentRule=null,e.selectedIds.clear(),e.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage())}),window.addEventListener("online",()=>{e.loadFailed&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage&&window.loadExceptionsPage()}),setTimeout(a,1500),setInterval(a,6e4);function te(S){if(!S)return"—";try{const y=new Date(S),p=$=>String($).padStart(2,"0");return`${y.getFullYear()}-${p(y.getMonth()+1)}-${p(y.getDate())} ${p(y.getHours())}:${p(y.getMinutes())}`}catch{return S.slice(0,16).replace("T"," ")}}async function re(){const S=document.getElementById("learned-list");if(S){S.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-loading"))}</div>`;try{const y=await fetch("/api/exception-whitelist",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!y.ok)throw new Error("http "+y.status);const $=(await y.json()).items||[];if($.length===0){S.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-empty"))}</div>`;return}const P=`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 4h8M5.5 4V2.5h3V4M4 4l0.6 8.5h4.8L10 4"/>
            </svg>`;S.innerHTML=$.map(Y=>{const Z=t("exc-rule-"+Y.rule_code)||Y.rule_code;return`
                    <div class="learned-row" data-wl-id="${escapeHtml(String(Y.id))}">
                        <div class="learned-seller" title="${escapeHtml(Y.seller_name)}">${escapeHtml(Y.seller_name)}</div>
                        <div class="learned-rule">${escapeHtml(Z)}</div>
                        <div class="learned-date">${escapeHtml(te(Y.created_at))}</div>
                        <button class="learned-del-btn" data-del-wl="${escapeHtml(String(Y.id))}" title="${escapeHtml(t("set-learned-del"))}" type="button">${P}</button>
                    </div>
                `}).join("")}catch(y){console.warn("loadLearnedRules fail",y),S.innerHTML=`<div class="learned-empty">${escapeHtml(t("exc-toast-load-fail"))}</div>`}}}window.loadLearnedRules=re,document.addEventListener("click",async S=>{const y=S.target.closest("[data-del-wl]");if(!y)return;const p=parseInt(y.dataset.delWl,10);if(!p)return;const $=y.closest(".learned-row"),P=$&&$.querySelector(".learned-seller"),Y=P?P.textContent.trim():"",Z=t("set-learned-del-confirm").replace("{seller}",Y);if(await showConfirm(Z,{danger:!0}))try{const ie=await fetch("/api/exception-whitelist/"+p,{method:"DELETE",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!ie.ok)throw new Error("http "+ie.status);showToast(t("set-learned-del-ok"),"success"),re(),typeof window.loadExceptionsPage=="function"&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage()}catch(ie){console.warn("delete whitelist fail",ie),showToast(t("set-learned-del-fail"),"error")}})})();(function(){let e={items:[],q:"",cat:"",selected:new Set,total:0,categories:{},pageSize:30,loading:!1,focusSearch:!1,searchCaret:0},n=null;function a(){return localStorage.getItem("mrpilot_token")||""}function s(c){const v=typeof currentLang=="string"&&currentLang||window._currentLang||"th",E=c.error_friendly&&c.error_friendly[v];if(E)return E;if(typeof humanizeError=="function"&&c.error_msg)try{return humanizeError(c.error_msg)}catch{}return t("erp-exc-reason-"+(c.category||"other"))}function o(){const c=document.getElementById("erp-exc-batch");if(!c)return;const v=e.selected.size;c.hidden=v===0;const E=c.querySelector(".erp-exc-batch-count");E&&(E.textContent=String(v))}function m(){const c=document.getElementById("erp-exc-block");if(!c)return;const v=e;if(!(v.total>0||!!v.q||!!v.cat)){c.hidden=!0,c.innerHTML="";return}c.hidden=!1;const x=v.categories||{},R=Object.keys(x).reduce((h,I)=>h+x[I],0);let D=`<button class="erp-exc-chip ${v.cat===""?"active":""}" data-erpexc-cat=""><span>${escapeHtml(t("erp-exc-cat-all"))}</span><span class="erp-exc-chip-count">${R}</span></button>`;Object.keys(x).forEach(h=>{D+=`<button class="erp-exc-chip ${v.cat===h?"active":""}" data-erpexc-cat="${escapeHtml(h)}"><span>${escapeHtml(t("erp-exc-cat-"+h))}</span><span class="erp-exc-chip-count">${x[h]}</span></button>`});const w=v.items||[],B=w.length>0&&w.every(h=>v.selected.has(h.id)),z=w.map(h=>{const I=h.state==="needs_action"?"needs":h.state==="retrying"?"retry":"fail",L=t("erp-exc-state-"+(h.state||"failed")),H=s(h),_=v.selected.has(h.id)?"checked":"";return`<div class="erp-exc-row" data-erpexc-id="${escapeHtml(h.id)}">
                <span class="ex-cb"><input type="checkbox" class="erp-exc-cb" data-erpexc-cb="${escapeHtml(h.id)}" ${_}></span>
                <span class="ex-inv" title="${escapeHtml(h.invoice_no||"")}">${escapeHtml(h.invoice_no||"—")}</span>
                <span class="ex-seller" title="${escapeHtml(h.seller_name||"")}">${escapeHtml(h.seller_name||"—")}</span>
                <span class="ex-buyer" title="${escapeHtml(h.ocr_buyer_name||"")}">${escapeHtml(h.ocr_buyer_name||"—")}</span>
                <span class="ex-state"><span class="erp-exc-state ${I}">${escapeHtml(L)}</span></span>
                <span class="ex-reason" title="${escapeHtml(H)}">${escapeHtml(H)}${h.error_code?` <span class="erp-exc-code">${escapeHtml(h.error_code)}</span>`:""}</span>
                <span class="ex-act"><button class="btn btn-sm btn-secondary" type="button" data-erpexc-retry="${escapeHtml(h.id)}">${escapeHtml(t("erp-exc-retry"))}</button></span>
            </div>`}).join(""),q=w.length===0?`<div class="erp-exc-empty">${escapeHtml(t("erp-exc-empty"))}</div>`:"",F=w.length<v.total?`<button class="erp-exc-more" type="button" id="erp-exc-more">${escapeHtml(t("erp-exc-load-more"))} (${w.length}/${v.total})</button>`:v.total>0?`<div class="erp-exc-count">${escapeHtml(t("erp-exc-shown",{n:w.length,total:v.total}))}</div>`:"";c.innerHTML=`
            <div class="erp-exc-head">
                <h2 class="erp-exc-title">${escapeHtml(t("erp-exc-title"))}</h2>
                <span class="erp-exc-sub">${escapeHtml(t("erp-exc-sub"))}</span>
                <input type="search" class="erp-exc-search" id="erp-exc-search" placeholder="${escapeHtml(t("erp-exc-search-ph"))}" value="${escapeHtml(v.q)}">
            </div>
            <div class="erp-exc-chips">${D}</div>
            <div class="erp-exc-batch" id="erp-exc-batch" ${v.selected.size?"":"hidden"}>
                <span class="erp-exc-batch-info"><span class="erp-exc-batch-count">${v.selected.size}</span> ${escapeHtml(t("erp-exc-batch-selected"))}</span>
                <button class="btn btn-sm btn-primary" type="button" data-erpexc-batch="retry">${escapeHtml(t("erp-exc-batch-retry"))}</button>
                <button class="btn btn-sm btn-danger" type="button" data-erpexc-batch="delete">${escapeHtml(t("erp-exc-batch-delete"))}</button>
                <button class="btn btn-sm btn-ghost" type="button" data-erpexc-batch="clear">${escapeHtml(t("erp-exc-batch-clear"))}</button>
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
                ${z}${q}
            </div>
            <div class="erp-exc-foot">${F}</div>`;const A=document.getElementById("erp-exc-search");if(A){if(v.focusSearch){A.focus();try{A.setSelectionRange(v.searchCaret,v.searchCaret)}catch{}}A.addEventListener("input",()=>{v.q=A.value,v.focusSearch=!0,v.searchCaret=A.selectionStart||A.value.length,clearTimeout(n),n=setTimeout(()=>i(!1),350)}),A.addEventListener("blur",()=>{v.focusSearch=!1})}c.querySelectorAll(".erp-exc-chip").forEach(h=>{h.addEventListener("click",()=>{v.cat=h.dataset.erpexcCat||"",i(!1)})}),c.querySelectorAll("[data-erpexc-retry]").forEach(h=>{h.addEventListener("click",I=>{I.stopPropagation(),r(h.dataset.erpexcRetry,h)})}),c.querySelectorAll(".erp-exc-cb").forEach(h=>{h.addEventListener("change",()=>{const I=h.dataset.erpexcCb;h.checked?v.selected.add(I):v.selected.delete(I);const L=document.getElementById("erp-exc-cb-all");L&&(L.checked=w.length>0&&w.every(H=>v.selected.has(H.id))),o()})});const g=document.getElementById("erp-exc-cb-all");g&&g.addEventListener("change",()=>{w.forEach(h=>{g.checked?v.selected.add(h.id):v.selected.delete(h.id)}),c.querySelectorAll(".erp-exc-cb").forEach(h=>{h.checked=g.checked}),o()}),c.querySelectorAll("[data-erpexc-batch]").forEach(h=>{h.addEventListener("click",()=>k(h.dataset.erpexcBatch))});const d=document.getElementById("erp-exc-more");d&&d.addEventListener("click",()=>i(!0)),c.querySelectorAll(".erp-exc-row:not(.erp-exc-row-head)").forEach(h=>{h.addEventListener("click",I=>{I.target.closest("input,button")||typeof window._erpExcOpenEdit=="function"&&window._erpExcOpenEdit(h.dataset.erpexcId)})})}async function r(c,v){if(c){v&&(v.disabled=!0,v.textContent=t("erp-exc-retrying"));try{const E=await fetch("/api/erp/logs/"+encodeURIComponent(c)+"/retry",{method:"POST",headers:{Authorization:"Bearer "+a()}}),x=await E.json().catch(()=>({}));showToast(E.ok&&x.ok?t("erp-exc-retry-ok"):t("erp-exc-retry-fail"),E.ok&&x.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.delete(c),i(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function k(c){const v=Array.from(e.selected);if(c==="clear"){e.selected.clear(),m();return}if(v.length!==0){if(c==="delete"){if(!await showConfirm(t("erp-exc-batch-delete-confirm",{n:v.length}),{danger:!0}))return;try{const x=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:v.slice(0,200)})}),R=await x.json().catch(()=>({}));showToast(x.ok?t("erp-exc-batch-delete-ok",{n:R.deleted||0}):t("erp-exc-retry-fail"),x.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}}else if(c==="retry")try{const E=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:v.slice(0,50)})}),x=await E.json().catch(()=>({}));showToast(E.ok?t("erp-exc-batch-retry-ok",{ok:x.succeeded||0,fail:(x.failed||0)+(x.skipped||0)}):t("erp-exc-retry-fail"),E.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.clear(),i(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function i(c){const v=document.getElementById("erp-exc-block");if(!(!v||e.loading)){e.loading=!0;try{const E=new URLSearchParams;e.q&&E.set("q",e.q),e.cat&&E.set("category",e.cat),E.set("limit",String(e.pageSize)),E.set("offset",String(c?e.items.length:0));const x=await fetch("/api/erp/exceptions?"+E.toString(),{headers:{Authorization:"Bearer "+a()}});if(!x.ok){c||(v.hidden=!0);return}const R=await x.json(),D=R.items||[];e.items=c?e.items.concat(D):D,e.total=R.total||0,e.categories=R.categories||{},m()}catch{c||(v.hidden=!0)}finally{e.loading=!1}}}let f={};function u(){const c=document.getElementById("erp-exc-modal");c&&c.remove()}window._erpExcOpenEdit=function(c){const v=(e.items||[]).find(q=>String(q.id)===String(c));if(!v)return;const E=!!v.history_client_id&&v.category==="customer_mismatch",x=v.category==="product_mismatch"&&!!v.history_id&&!!v.endpoint_id,R=s(v),D=v.state==="needs_action"?"needs":v.state==="retrying"?"retry":"fail",w=(q,F)=>`<div class="erp-exc-m-row"><span class="erp-exc-m-k">${escapeHtml(q)}</span><span class="erp-exc-m-v">${escapeHtml(F||"—")}</span></div>`;let B="";if(E)B=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-pick"))}</div>
                    <input type="search" class="erp-exc-m-search" id="erp-exc-m-search" placeholder="${escapeHtml(t("erp-exc-edit-pick-ph"))}">
                    <div class="erp-exc-m-custlist" id="erp-exc-m-custlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-pick-loading"))}</div>
                    </div>
                </div>`;else if(x)B=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-prod-intro"))}</div>
                    <div class="erp-exc-m-custlist" id="erp-exc-m-prodlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-prod-loading"))}</div>
                    </div>
                </div>`;else{const q="erp-exc-edit-hint-"+(v.category||"other");let F=t(q);(!F||F===q)&&(F=R),B=`<div class="erp-exc-m-hint">${escapeHtml(F)}</div>`}const z=document.createElement("div");if(z.id="erp-exc-modal",z.className="erp-exc-modal-overlay",z.innerHTML=`
            <div class="erp-exc-modal" role="dialog" aria-modal="true">
                <div class="erp-exc-m-head">
                    <h3>${escapeHtml(t("erp-exc-edit-title"))}</h3>
                    <button class="erp-exc-m-close" type="button" id="erp-exc-m-close" aria-label="close">×</button>
                </div>
                <div class="erp-exc-m-body">
                    <div class="erp-exc-m-reason"><span class="erp-exc-state ${D}">${escapeHtml(t("erp-exc-state-"+(v.state||"failed")))}</span> ${escapeHtml(R)}${v.error_code?` <span class="erp-exc-code">${escapeHtml(v.error_code)}</span>`:""}</div>
                    ${w(t("erp-exc-f-invoice"),v.invoice_no)}
                    ${w(t("erp-exc-f-seller"),v.seller_name)}
                    ${w(t("erp-exc-f-buyer"),v.ocr_buyer_name)}
                    ${w(t("erp-exc-edit-field-current"),v.client_name)}
                    ${B}
                </div>
                <div class="erp-exc-m-foot">
                    <button class="btn btn-sm btn-ghost" type="button" id="erp-exc-m-cancel">${escapeHtml(t("erp-exc-edit-close"))}</button>
                    <button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-retry">${escapeHtml(t("erp-exc-edit-retry"))}</button>
                    ${E?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind" disabled>${escapeHtml(t("erp-exc-edit-bind-retry"))}</button>`:""}
                    ${x?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind-prod" disabled>${escapeHtml(t("erp-exc-edit-bind-prod-retry"))}</button>`:""}
                </div>
            </div>`,document.body.appendChild(z),z.addEventListener("click",q=>{q.target===z&&u()}),document.getElementById("erp-exc-m-close").addEventListener("click",u),document.getElementById("erp-exc-m-cancel").addEventListener("click",u),document.getElementById("erp-exc-m-retry").addEventListener("click",()=>{u(),r(v.id,null)}),E){let q="";const F=document.getElementById("erp-exc-m-bind"),A=document.getElementById("erp-exc-m-custlist"),g=document.getElementById("erp-exc-m-search"),d=(I,L)=>{const H=(L||"").trim().toLowerCase(),_=H?I.filter(M=>(M.code||"").toLowerCase().includes(H)||(M.name||"").toLowerCase().includes(H)):I;if(_.length===0){A.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-empty"))}</div>`;return}A.innerHTML=_.slice(0,100).map(M=>`<div class="erp-exc-m-cust" data-cust-code="${escapeHtml(M.code||"")}">
                        <span class="erp-exc-m-cust-name">${escapeHtml(M.name||"")}</span>
                        <span class="erp-exc-m-cust-code">${escapeHtml(M.code||"")}</span>
                    </div>`).join(""),A.querySelectorAll(".erp-exc-m-cust").forEach(M=>{M.addEventListener("click",()=>{q=M.dataset.custCode||"",A.querySelectorAll(".erp-exc-m-cust").forEach(K=>K.classList.remove("sel")),M.classList.add("sel"),F&&(F.disabled=!q)})})},h=async()=>{const I=v.endpoint_id;if(f[I]){d(f[I],"");return}try{const L=await fetch("/api/erp/endpoints/"+encodeURIComponent(I)+"/customers",{headers:{Authorization:"Bearer "+a()}}),H=await L.json().catch(()=>({}));if(!L.ok||!H.ok){A.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`;return}const _=H.customers||[];f[I]=_,d(_,"")}catch{A.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`}};g&&g.addEventListener("input",()=>d(f[v.endpoint_id]||[],g.value)),h(),F&&F.addEventListener("click",async()=>{if(q){F.disabled=!0,F.textContent=t("erp-exc-retrying");try{if(!(await fetch("/api/erp/mappings/clients",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({client_id:v.history_client_id,erp_type:v.endpoint_adapter,erp_code:q})})).ok){showToast(t("erp-exc-retry-fail"),"error"),F.disabled=!1,F.textContent=t("erp-exc-edit-bind-retry");return}showToast(t("erp-exc-edit-bound-ok"),"success"),u(),await r(v.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),F.disabled=!1,F.textContent=t("erp-exc-edit-bind-retry")}}})}if(x){const q=document.getElementById("erp-exc-m-bind-prod"),F=document.getElementById("erp-exc-m-prodlist"),A={};let g=[];const d=()=>'<option value="">'+escapeHtml(t("erp-exc-edit-prod-choose"))+"</option>"+g.slice(0,500).map(L=>`<option value="${escapeHtml(L.code||"")}" data-pname="${escapeHtml(L.name||"")}">`+escapeHtml((L.name||"")+" · "+(L.code||""))+"</option>").join(""),h=L=>{if(!L.length){F.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-noitems"))}</div>`;return}F.innerHTML=L.map(H=>`<div class="erp-exc-m-cust" style="cursor:default">
                        <span class="erp-exc-m-cust-name" title="${escapeHtml(H)}">${escapeHtml(H)}</span>
                        <select class="erp-exc-m-prod-sel" data-item="${escapeHtml(H)}" style="max-width:55%;flex:0 0 auto;padding:4px 6px;border:1px solid var(--border,#e5e7eb);border-radius:6px;font-size:12px">${d()}</select>
                    </div>`).join(""),F.querySelectorAll(".erp-exc-m-prod-sel").forEach(H=>{H.addEventListener("change",()=>{const _=H.dataset.item,M=H.options[H.selectedIndex];H.value?A[_]={code:H.value,name:M&&M.dataset.pname||""}:delete A[_],q&&(q.disabled=Object.keys(A).length===0)})})};(async()=>{try{const H=await(await fetch("/api/history/"+encodeURIComponent(v.history_id),{headers:{Authorization:"Bearer "+a()}})).json().catch(()=>({})),_=H&&H.pages||[],M=[],K={};(Array.isArray(_)?_:[]).forEach(te=>{const re=te&&te.fields&&te.fields.items||[];(Array.isArray(re)?re:[]).forEach(S=>{const y=(S&&(S.name||S.description)||"").trim();y&&!K[y]&&(K[y]=1,M.push(y))})});const G=await fetch("/api/erp/endpoints/"+encodeURIComponent(v.endpoint_id)+"/products",{headers:{Authorization:"Bearer "+a()}}),W=await G.json().catch(()=>({}));if(!G.ok||!W.ok){F.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`;return}g=W.products||[],h(M)}catch{F.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`}})(),q&&q.addEventListener("click",async()=>{const L=Object.entries(A);if(L.length){q.disabled=!0,q.textContent=t("erp-exc-retrying");try{for(const[H,_]of L)if(!(await fetch("/api/erp/mappings/products",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({erp_type:v.endpoint_adapter,item_name:H,erp_code:_.code,erp_name:_.name})})).ok){showToast(t("erp-exc-retry-fail"),"error"),q.disabled=!1,q.textContent=t("erp-exc-edit-bind-prod-retry");return}showToast(t("erp-exc-edit-prod-bound-ok"),"success"),u(),await r(v.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),q.disabled=!1,q.textContent=t("erp-exc-edit-bind-prod-retry")}}})}},window._rerenderErpExceptions=m,window.loadErpExceptions=i,window._erpExcState=e})();(function(){function e(c){try{if(location.search.indexOf("test_center=1")>=0||localStorage.getItem("pearnly_test_mode")==="1"||c&&c.id&&String(c.id)==="468b50c1-5593-4fd6-990d-515ce8085563")return!0}catch{}return!1}window.applyRoleVisibility=function(){var v=window._userInfo,E=!1,x=!0,R=!1,D=!1;v&&(E=typeof canManageTeam=="function"?canManageTeam(v):!!(v.role==="owner"||v.is_super_admin),x=typeof shouldHideMoney=="function"?shouldHideMoney(v):v.role==="member"&&!v.is_super_admin,R=typeof isSuperAdmin=="function"?isSuperAdmin(v):!!v.is_super_admin,D=e(v)),document.querySelectorAll("[data-show-if-team]").forEach(function(B){B.style.display=E?"":"none"}),document.querySelectorAll("[data-show-if-money]").forEach(function(B){B.style.display=x?"none":""}),document.querySelectorAll("[data-show-if-admin]").forEach(function(B){B.style.display=R?"":"none"}),document.querySelectorAll("[data-show-if-test]").forEach(function(B){B.style.display=D?"":"none"});var w=R||D;document.querySelectorAll("[data-show-if-special]").forEach(function(B){B.style.display=w?"":"none"})},window.renderAvatarMenu=function(v){if(v){var E=document.getElementById("avatar-btn"),x=document.getElementById("avatar-popup-name"),R=document.getElementById("avatar-popup-email");if(!(!E||!x||!R)){var D=(v.username||"").trim(),w=D.split("@")[0]||D||"—",B=(D.charAt(0)||"?").toUpperCase(),z=(v.avatar_url||"").trim();if(z){var q=z.replace(/"/g,"&quot;"),F=B.replace(/'/g,"\\'");E.innerHTML='<img src="'+q+'" alt="'+B+`" referrerpolicy="no-referrer" onerror="this.parentNode.textContent='`+F+`'">`}else E.textContent=B;x.textContent=w,R.textContent=D||"—",E.setAttribute("title",D||"")}}};function n(){var c=document.getElementById("avatar-wrap"),v=document.getElementById("avatar-btn"),E=document.getElementById("avatar-popup");if(!c||!v||!E)return;function x(){E.classList.remove("show"),v.setAttribute("aria-expanded","false")}function R(){E.classList.add("show"),v.setAttribute("aria-expanded","true")}v.addEventListener("click",function(D){D.stopPropagation(),E.classList.contains("show")?x():R()}),document.addEventListener("click",function(D){E.classList.contains("show")&&!c.contains(D.target)&&x()}),E.addEventListener("click",function(D){var w=D.target.closest(".avatar-popup-item");if(w){var B=w.dataset.action;switch(x(),B){case"settings":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings");break;case"team":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("team")},50);break;case"billing":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("plan")},50);break;case"shortcuts":if(typeof showToast=="function"){var z=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(z||"即将上线","info")}break;case"admin":window.location.href="/admin/cost";break;case"test-center":typeof routeTo=="function"&&routeTo("test-center");break;case"help":var q=document.getElementById("help-modal");q&&(q.style.display="flex");break;case"logout":try{localStorage.removeItem("mrpilot_token")}catch{}try{localStorage.removeItem("mrpilot_user")}catch{}window.location.href="/";break}}}),window._closeAvatarPopup=x}function a(){return[].slice.call(document.querySelectorAll(".cmdk-item")).filter(function(c){return c.style.display!=="none"})}function s(c){var v=a();v.forEach(function(E){E.classList.remove("focus")}),v[c]&&(v[c].classList.add("focus"),v[c].scrollIntoView({block:"nearest"}))}function o(c){var v=a();if(v.length){var E=v.findIndex(function(R){return R.classList.contains("focus")});E<0&&(E=0);var x=(E+c+v.length)%v.length;s(x)}}function m(c){c=(c||"").toLowerCase().trim();var v=0,E=window._userInfo,x=typeof isSuperAdmin=="function"?isSuperAdmin(E):!!(E&&E.is_super_admin),R=e(E);document.querySelectorAll(".cmdk-item").forEach(function(w){if(w.dataset.showIfAdmin==="1"&&!x){w.style.display="none";return}if(w.dataset.showIfTest==="1"&&!R){w.style.display="none";return}var B=(w.dataset.cmdkText||w.textContent||"").toLowerCase(),z=!c||B.indexOf(c)>=0;w.style.display=z?"":"none",w.classList.remove("focus"),z&&v++}),document.querySelectorAll("[data-cmdk-section]").forEach(function(w){for(var B=w.nextElementSibling,z=!1;B&&!B.hasAttribute("data-cmdk-section");){if(B.classList&&B.classList.contains("cmdk-item")&&B.style.display!=="none"){z=!0;break}B=B.nextElementSibling}w.style.display=z?"":"none"});var D=document.getElementById("cmdk-empty");D&&(D.style.display=v===0?"flex":"none"),s(0)}window.openCmdk=function(){var v=document.getElementById("cmdk-mask");v&&(typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup(),v.classList.add("show"),typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility(),setTimeout(function(){var E=document.getElementById("cmdk-input");E&&(E.value="",m(""),E.focus(),s(0))},50))},window.closeCmdk=function(){var v=document.getElementById("cmdk-mask");v&&v.classList.remove("show")};function r(c){if(c){if(c.classList.contains("cmdk-item-locked")){if(typeof showToast=="function"){var v=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(v||"即将上线","info")}return}var E=c.dataset.cmdkRoute,x=c.dataset.cmdkAction;if(window.closeCmdk(),E){typeof routeTo=="function"&&routeTo(E);return}if(x){if(x==="open-admin"){window.location.href="/admin/cost";return}if(x.indexOf("lang-")===0){var R=x.slice(5);typeof applyLang=="function"&&applyLang(R)}}}}function k(){var c=document.getElementById("cmdk-mask"),v=document.getElementById("cmdk-input"),E=document.getElementById("cmdk-body");if(!(!c||!v||!E)){c.addEventListener("click",function(D){D.target===c&&window.closeCmdk()});var x=document.getElementById("cmdk-esc-btn");x&&x.addEventListener("click",function(){window.closeCmdk()}),v.addEventListener("input",function(D){m(D.target.value)}),v.addEventListener("keydown",function(D){D.key==="ArrowDown"?(D.preventDefault(),o(1)):D.key==="ArrowUp"?(D.preventDefault(),o(-1)):D.key==="Enter"?(D.preventDefault(),r(c.querySelector(".cmdk-item.focus"))):D.key==="Escape"&&(D.preventDefault(),window.closeCmdk())}),E.addEventListener("click",function(D){var w=D.target.closest(".cmdk-item");w&&r(w)}),E.addEventListener("mousemove",function(D){var w=D.target.closest(".cmdk-item");!w||w.style.display==="none"||w.classList.contains("cmdk-item-locked")||(a().forEach(function(B){B.classList.remove("focus")}),w.classList.add("focus"))});var R=document.getElementById("topbar-search");R&&(R.addEventListener("click",function(){window.openCmdk()}),R.addEventListener("keydown",function(D){(D.key==="Enter"||D.key===" ")&&(D.preventDefault(),window.openCmdk())}))}}document.addEventListener("keydown",function(c){if((c.metaKey||c.ctrlKey)&&(c.key==="k"||c.key==="K")){c.preventDefault(),window.openCmdk();return}if(c.key==="Escape"){var v=document.getElementById("cmdk-mask");if(v&&v.classList.contains("show")){window.closeCmdk();return}var E=document.getElementById("avatar-popup");E&&E.classList.contains("show")&&typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup()}});try{var i=(navigator.userAgent||"").toLowerCase(),f=i.indexOf("mac")>=0||i.indexOf("iphone")>=0||i.indexOf("ipad")>=0;f||document.body.classList.add("is-windows")}catch{}function u(){n(),k(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("nav-ia-phase1-role",function(){try{typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",u):u()})();(function(){function n(x){return String(x??"").replace(/[&<>"']/g,function(R){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[R]})}function a(x){if(!x||isNaN(x))return"";var R=Number(x);return R<1024?R+" B":R<1024*1024?(R/1024).toFixed(1)+" KB":(R/1024/1024).toFixed(1)+" MB"}document.addEventListener("click",function(x){var R=x.target.closest&&x.target.closest(".recon-collapse-head");if(R&&!(x.target.closest("button")||x.target.closest("a"))){var D=R.closest(".recon-collapse");if(D){var w=D.getAttribute("data-collapsed")==="true";D.setAttribute("data-collapsed",w?"false":"true"),w&&(D.id==="vex-summary-collapse"&&u(),D.id==="vex-detail-collapse"&&c())}}}),document.addEventListener("keydown",function(x){if(!(x.key!=="Enter"&&x.key!==" ")){var R=x.target.closest&&x.target.closest(".recon-collapse-head");R&&(x.preventDefault(),R.click())}});var s={vat:"",gl:""};window._glvClearPreviewSearch=function(){s.vat="",s.gl=""};var o='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',m='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function r(){i("vat"),i("gl")}function k(x){try{if(typeof window._glvPreviewFiles=="function")return window._glvPreviewFiles(x)||[]}catch{}var R=document.getElementById(x==="vat"?"glv-vat-input":"glv-gl-input");return R&&R.files?Array.from(R.files):[]}function i(x){var R=document.getElementById(x==="vat"?"glv-pp-vat-col":"glv-pp-gl-col");if(R){var D=k(x),w=x==="vat"?"glv-up-vat-title":"glv-up-gl-title",B=x==="vat"?"① 销项税报告":"② 总账 GL",z=window.t&&window.t(w)||B,q=n(window.t&&window.t("vex-preview-search")||"搜索文件名..."),F=n(window.t&&window.t("vex-preview-clear-all")||"全清"),A=s[x]||"",g=D.length;R.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+n(z)+' <span class="vex-pp-col-count">'+g+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="glv-pp-search-'+x+'" type="text" placeholder="'+q+'" value="'+n(A)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="glv-pp-clearall-'+x+'" type="button">'+F+'</button></div><div class="vex-pp-file-list" id="glv-pp-'+x+'-list"></div><div class="vex-pp-pagination" id="glv-pp-'+x+'-pg"></div>';var d=document.getElementById("glv-pp-search-"+x);d&&d.addEventListener("input",function(I){s[x]=I.target.value,f(x)});var h=document.getElementById("glv-pp-clearall-"+x);h&&h.addEventListener("click",function(){window._glvRemoveFile&&window._glvRemoveFile(x)}),f(x)}}function f(x){var R=document.getElementById("glv-pp-"+x+"-list"),D=document.getElementById("glv-pp-"+x+"-pg");if(R){var w=k(x),B=(s[x]||"").toLowerCase(),z=w.map(function(A,g){return{f:A,i:g}}),q=B?z.filter(function(A){return A.f.name.toLowerCase().indexOf(B)>=0}):z;if(R.innerHTML=q.map(function(A){var g=A.f;return'<div class="vex-pp-file-row">'+o+'<span class="vex-pp-fi-name" title="'+n(g.name)+'">'+n(g.name)+'</span><span class="vex-pp-fi-size">'+a(g.size)+'</span><button class="vex-pp-fi-del" type="button" data-kind="'+x+'" data-idx="'+A.i+'" aria-label="remove">'+m+"</button></div>"}).join(""),R.querySelectorAll(".vex-pp-fi-del").forEach(function(A){A.addEventListener("click",function(){var g=A.dataset.kind,d=parseInt(A.dataset.idx,10);window._glvRemoveFile&&window._glvRemoveFile(g,isNaN(d)?null:d)})}),D){var F=window.t&&window.t("vex-preview-count")||"显示前 {n} / 共 {m}";D.textContent=F.replace("{n}",q.length).replace("{m}",q.length)}}}function u(){var x=function(D,w){var B=document.getElementById(D);B&&(B.textContent=w==null?"—":String(w))},R=window._vexLastTask||{};x("vex-sum-total",R.total),x("vex-sum-matched",R.matched),x("vex-sum-diff",R.diff),x("vex-sum-incomplete",R.incomplete),x("vex-sum-cash",R.cash),document.getElementById("vex-summary-sub")}function c(){var x=window._vexLastTask&&window._vexLastTask.diff_rows||[],R=document.getElementById("vex-detail-tbody"),D=document.getElementById("vex-detail-table"),w=document.getElementById("vex-detail-empty");if(!(!R||!D||!w)){if(x.length===0){D.style.display="none",w.style.display="";return}w.style.display="none",D.style.display="";var B=x.map(function(q){return'<tr><td class="recon-detail-cell-mono">'+n(q.invoice_no||"")+"</td><td>"+n(q.field||"")+"</td><td>"+n(q.report_value||"")+"</td><td>"+n(q.invoice_value||"")+"</td><td>"+n(q.kind||"")+"</td></tr>"}).join("");R.innerHTML=B;var z=document.getElementById("vex-detail-sub");z&&(z.textContent=String(x.length))}}function v(){var x=document.getElementById("glv-toggle-preview");x&&!x._reconBound&&(x._reconBound=!0,x.addEventListener("click",function(){var R=document.getElementById("glv-preview-panel"),D=document.getElementById("glv-toggle-preview-label"),w=R&&R.style.display!=="none";R&&(R.style.display=w?"none":""),x.classList.toggle("open",!w),D&&(D.textContent=w?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),w||r()})),["glv-vat-input","glv-gl-input"].forEach(function(R){var D=document.getElementById(R);!D||D._reconWatched||(D._reconWatched=!0,D.addEventListener("change",function(){var w=document.getElementById("glv-preview-panel");w&&w.style.display!=="none"&&r()}))})}function E(){var x=document.getElementById("vex-summary-collapse"),R=document.getElementById("vex-detail-collapse");x&&(x.style.display=""),R&&(R.style.display=""),u(),c()}window._fillVexSummary=u,window._fillVexDetail=c,window._onVexResultShown=E,document.addEventListener("DOMContentLoaded",function(){v()}),setTimeout(v,1500),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-collapse",function(){var x=document.getElementById("glv-preview-panel");x&&x.style.display!=="none"&&r();var R=document.getElementById("glv-toggle-preview-label"),D=document.getElementById("glv-toggle-preview");R&&D&&(R.textContent=D.classList.contains("open")?window.t&&window.t("vex-toggle-preview-close")||"收起清单":window.t&&window.t("vex-toggle-preview-open")||"查看清单")}),window._reconCollapse={renderGlvPreview:r,fillVexSummary:u,fillVexDetail:c}})();(function(){function e(m){}function n(){const m=document.querySelectorAll("[data-recon-tab]");m.forEach(k=>{k.addEventListener("click",()=>{m.forEach(v=>v.classList.remove("active")),k.classList.add("active");const i=k.dataset.reconTab,f=document.getElementById("recon-pane-bank"),u=document.getElementById("recon-pane-sale-vat"),c=document.getElementById("recon-pane-gl-vat");f&&(f.style.display=i==="bank"?"":"none"),u&&(u.style.display=i==="sale-vat"?"":"none"),c&&(c.style.display=i==="gl-vat"?"":"none"),i==="gl-vat"&&window.GlVatRecon&&window.GlVatRecon.ensureInit(),i==="bank"&&typeof window._bankReconV2Init=="function"&&window._bankReconV2Init()})});const r=document.querySelector("[data-recon-tab].active");r&&(r.dataset.reconTab,void 0)}function a(){const m=document.getElementById("page-settings");if(!m)return null;let r=document.getElementById("settings-modal-overlay");if(r)return r;r=document.createElement("div"),r.id="settings-modal-overlay",r.className="settings-modal-overlay",r.style.display="none",m.parentElement.insertBefore(r,m),r.appendChild(m);const k=document.createElement("button");return k.id="settings-modal-close",k.className="settings-modal-close",k.setAttribute("aria-label","close"),k.innerHTML='<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 5l10 10M15 5L5 15"/></svg>',m.insertBefore(k,m.firstChild),k.addEventListener("click",o),r.addEventListener("click",i=>{i.target===r&&o()}),r}function s(){const m=a();if(!m)return;m.style.display="flex",document.body.classList.add("settings-modal-open");const r=document.getElementById("page-settings");r&&(r.style.display="block"),setTimeout(()=>{try{typeof renderSettings=="function"&&renderSettings()}catch(i){console.warn("renderSettings:",i)}let k=document.querySelector(".settings-tab.active")||document.querySelector('.settings-tab[data-tab="profile"]');k&&k.click()},50)}function o(){const m=document.getElementById("settings-modal-overlay");m&&(m.style.display="none"),document.body.classList.remove("settings-modal-open")}window.openSettingsModal=s,window.closeSettingsModal=o,document.addEventListener("keydown",m=>{if(m.key==="Escape"){const r=document.getElementById("settings-modal-overlay");r&&r.style.display==="flex"&&o()}}),window.addEventListener("hashchange",()=>{location.hash==="#/settings"&&s()}),window.addEventListener("DOMContentLoaded",()=>{location.hash==="#/settings"&&s()}),document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){const a=/\.(pdf|jpe?g|png|webp|tiff?|xlsx?|xlsm|csv|tsv|docx?)$/i,s=V=>document.getElementById(V);function o(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}function m(V){return String(V??"").replace(/[&<>"']/g,Q=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[Q])}function r(V){return V<1024?V+" B":V<1024*1024?(V/1024).toFixed(1)+" KB":(V/1024/1024).toFixed(1)+" MB"}let k=[],i=[],f=!1,u=[],c=50,v=50,E="",x="";async function R(){try{const V=await fetch("/api/vat_excel/tasks?page=1&page_size=1",{headers:o()});if(!V.ok)return;const ee=(await V.json()).kpi||{};[["vex-kpi-month-val",ee.this_month],["vex-kpi-running-val",ee.running],["vex-kpi-done-val",ee.done],["vex-kpi-failed-val",ee.failed]].forEach(([ne,se])=>{const ue=document.getElementById(ne);ue&&(ue.textContent=se??0)})}catch{}}async function D(){try{const V=await fetch("/api/vat_excel/tasks?page=1&page_size=100",{headers:o()});if(!V.ok)return;const Q=await V.json();q(Q.rows||[])}catch{}}const w=10;var B=1;function z(){var V=((document.getElementById("vex-task-search")||{}).value||"").trim().toLowerCase();if(B=1,q(u),!!V){var Q=document.getElementById("vex-task-tbody");Q&&Q.querySelectorAll("tr").forEach(function(ee){ee.dataset.taskId&&(ee.style.display=ee.textContent.toLowerCase().indexOf(V)>=0?"":"none")})}}function q(V){u=V||u;const Q=document.getElementById("vex-task-tbody");if(!Q)return;if(!u.length){Q.innerHTML='<tr><td colspan="9" class="vex-task-empty">'+(t("sv-empty-title")||"还没有对账任务")+"</td></tr>",F(0);return}const ee=Math.ceil(u.length/w);B>ee&&(B=ee);const ne=(B-1)*w;A(u.slice(ne,ne+w)),F(u.length)}function F(V){const Q=document.getElementById("vex-task-pager"),ee=document.getElementById("vex-task-pager-info"),ne=document.getElementById("vex-task-prev"),se=document.getElementById("vex-task-next");if(!Q)return;if(V<=w){Q.style.display="none";return}Q.style.display="";const ue=Math.ceil(V/w);ee&&(ee.textContent=B+" / "+ue),ne&&(ne.disabled=B<=1),se&&(se.disabled=B>=ue)}function A(V){const Q=document.getElementById("vex-task-tbody");if(!Q)return;const ee={pending:t("vex-status-pending")||"待处理",running:t("vex-status-running")||"处理中",done:t("vex-status-done")||"已完成",failed:t("vex-status-failed")||"失败"},ne={pending:"badge-gray",running:"badge-blue",done:"badge-green",failed:"badge-red"},se='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',ue='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h10M6 4V3h4v1M5 4v8a1 1 0 001 1h4a1 1 0 001-1V4"/></svg>';Q.innerHTML=V.map(b=>{const C=b.created_at?new Date(b.created_at).toLocaleString([],{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}):"—",T=b.period||"—",U=b.matched_count!=null?b.matched_count+" ✓ · "+b.mismatched_count+" ⚠":"—",N=b.mismatch_amount!=null?"฿ "+Number(b.mismatch_amount).toLocaleString():"—",l=b.elapsed_seconds!=null?b.elapsed_seconds.toFixed(1)+" s":"—",j=b.status||"pending",O=b.client_name&&b.client_name!=="client"?b.client_name:t("vex-client-all")||"全部客户";return`<tr class="vex-task-row" data-task-id="${m(b.id)}" style="cursor:pointer">
                <td>${C}</td>
                <td>${m(O)}</td>
                <td>${m(T)}</td>
                <td>${(b.invoice_count||0)+" / "+(b.report_count||0)}</td>
                <td>${U}</td>
                <td>${N}</td>
                <td><span class="badge ${ne[j]||"badge-gray"}">${ee[j]||j}</span></td>
                <td>${l}</td>
                <td><div class="vex-task-actions">
                    <button class="vex-task-dl-btn" data-task-id="${m(b.id)}" title="${t("hist_export")||"导出"}">${se}</button>
                    <button class="vex-task-del-btn" data-task-id="${m(b.id)}" title="${t("vex-task-delete-confirm-title")||"删除"}">${ue}</button>
                </div></td>
            </tr>`}).join(""),Q.querySelectorAll(".vex-task-dl-btn").forEach(b=>{b.addEventListener("click",async C=>{C.stopPropagation();const T=b.dataset.taskId;try{const U=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(T)+"/download",{credentials:"include",headers:o()});if(U.status===410){showToast(t("vex-toast-expired")||"数据已过期 · 请重新对账","warn");return}if(!U.ok){showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error");return}const N=await U.blob(),j=(U.headers.get("Content-Disposition")||"").match(/filename\*?=(?:UTF-8''|")?([^";]+)/i),O=j?decodeURIComponent(j[1]):"vat_recon_"+T+".xlsx",J=URL.createObjectURL(N),X=document.createElement("a");X.href=J,X.download=O,X.click(),setTimeout(()=>URL.revokeObjectURL(J),1e3)}catch{showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error")}})}),Q.querySelectorAll(".vex-task-del-btn").forEach(b=>{b.addEventListener("click",C=>{C.stopPropagation(),d(b.dataset.taskId)})}),z()}function g(){var V=document.getElementById("vex-task-prev"),Q=document.getElementById("vex-task-next");V&&!V._vexBound&&(V._vexBound=!0,V.addEventListener("click",function(){B>1&&(B--,q())})),Q&&!Q._vexBound&&(Q._vexBound=!0,Q.addEventListener("click",function(){var ee=Math.ceil(u.length/w);B<ee&&(B++,q())}))}async function d(V){const Q=t("vex-task-delete-confirm-title")||"删除对账任务?",ee=t("vex-task-delete-confirm-body")||"同时清掉对应的发票识别缓存 · 不可恢复";if(await showConfirm(ee,{title:Q,danger:!0,okText:t("vex-task-delete-confirm-title")||"确认删除"}))try{const se=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(V),{method:"DELETE",credentials:"include",headers:o()});if(!se.ok)throw new Error(se.status);showToast(t("vex-task-delete-ok")||"已删除","success"),D(),R()}catch{showToast(t("vex-task-delete-fail")||"删除失败","error")}}function h(V){const Q=window._currentLang||"th",ee={zh:`已忽略 ${V} 个不支持的文件 · 仅支持 PDF / 图片 / Excel / CSV / Word`,th:`ข้ามไฟล์ที่ไม่รองรับ ${V} ไฟล์ · รองรับเฉพาะ PDF / รูปภาพ / Excel / CSV / Word`,en:`Ignored ${V} unsupported file(s) · only PDF / image / Excel / CSV / Word are supported`,ja:`非対応ファイル ${V} 件をスキップ · 対応形式は PDF / 画像 / Excel / CSV / Word のみ`};showToast(ee[Q]||ee.th,"warn")}function I(V){const Q=new Set(k.map(ne=>ne.name+"|"+ne.size));let ee=0;for(const ne of V){if(!a.test(ne.name)){ee++;continue}const se=ne.name+"|"+ne.size;if(!Q.has(se)&&(Q.add(se),k.push(ne),k.length>=1e3))break}ee>0&&h(ee),k.length>1e3&&(k=k.slice(0,1e3),showToast(t("vex-toast-cap-inv"),"warn")),M()}function L(V){const Q=new Set(i.map(ne=>ne.name+"|"+ne.size));let ee=0;for(const ne of V){if(!a.test(ne.name)){ee++;continue}const se=ne.name+"|"+ne.size;if(!Q.has(se)&&(Q.add(se),i.push(ne),i.length>=30))break}ee>0&&h(ee),i.length>30&&(i=i.slice(0,30),showToast(t("vex-toast-cap-rep"),"warn")),M()}function H(V){k.splice(V,1),M()}function _(V){i.splice(V,1),M()}function M(){const V=s("vex-list-invoice"),Q=s("vex-list-report"),ee=s("vex-count-invoice"),ne=s("vex-count-report");ee&&(ee.textContent=k.length),ne&&(ne.textContent=i.length);const se=(C,T,U)=>`<div class="vex-fi">
            <svg class="vex-fi-ic" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2h6l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M10 2v4h4"/></svg>
            <span class="vex-fi-n" title="${m(C.name)}">${m(C.name)}</span>
            <span class="vex-fi-s">${r(C.size)}</span>
            <button class="vex-fi-x" type="button" data-vex-kind="${U}" data-vex-idx="${T}" aria-label="remove">×</button>
        </div>`;V&&(V.innerHTML=k.map((C,T)=>se(C,T,"inv")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),Q&&(Q.innerHTML=i.map((C,T)=>se(C,T,"rep")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),document.querySelectorAll(".vex-fi-x").forEach(C=>{C.addEventListener("click",T=>{const U=C.dataset.vexKind,N=parseInt(C.dataset.vexIdx,10);U==="inv"?H(N):_(N)})});const ue=k.length>0&&i.length>0;s("vex-build").disabled=!ue||f;const b=s("vex-action-info");b&&(!k.length||!i.length?(b.textContent=t("vex-need-both")||"需要至少 1 张发票 + 1 份 VAT 报告",b.className="vex-action-info muted"):(b.textContent=(t("vex-ready")||"已就绪 · {a} 张发票 · {b} 份报告").replace("{a}",k.length).replace("{b}",i.length),b.className="vex-action-info ok")),te()}const K='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>',G='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',W='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function te(){const V=s("vex-preview-panel");if(!V||V.style.display==="none")return;re("inv"),re("rep");const Q=s("vex-pp-guide");Q&&(Q.style.display=k.length>100?"flex":"none")}function re(V){const Q=s(V==="inv"?"vex-pp-invoice-col":"vex-pp-report-col");if(!Q)return;const ee=V==="inv"?k:i,ne=V==="inv"?E:x,se=t(V==="inv"?"vex-preview-invoice":"vex-preview-report")||(V==="inv"?"销售发票":"VAT 报告"),ue=m(t("vex-preview-search")||"搜索文件名..."),b=m(t("vex-preview-clear-all")||"全清");Q.innerHTML=`
            <div class="vex-pp-col-title">
                <span class="vex-pp-col-name">${m(se)} <span class="vex-pp-col-count">${ee.length}</span></span>
            </div>
            <div class="vex-pp-search-row">
                <input class="vex-pp-search" id="vex-pp-search-${V}" type="text"
                       placeholder="${ue}" value="${m(ne)}" autocomplete="off">
                <button class="vex-pp-clear-btn" id="vex-pp-clearall-${V}" type="button">${b}</button>
            </div>
            <div class="vex-pp-file-list" id="vex-pp-${V}-list"></div>
            <div class="vex-pp-pagination" id="vex-pp-${V}-pg"></div>`;const C=s("vex-pp-search-"+V);C&&C.addEventListener("input",U=>{V==="inv"?(E=U.target.value,c=50):(x=U.target.value,v=50),S(V)});const T=s("vex-pp-clearall-"+V);T&&T.addEventListener("click",()=>{V==="inv"?(k=[],E="",c=50):(i=[],x="",v=50),M()}),S(V)}function S(V){const Q=s("vex-pp-"+V+"-list"),ee=s("vex-pp-"+V+"-pg");if(!Q)return;const ne=V==="inv"?k:i,se=V==="inv"?E:x,ue=V==="inv"?c:v,b=V==="inv"?K:G,C=ne.map((N,l)=>({f:N,i:l})),T=se?C.filter(({f:N})=>N.name.toLowerCase().includes(se.toLowerCase())):C,U=T.slice(0,ue);if(Q.innerHTML=U.map(({f:N,i:l})=>`
            <div class="vex-pp-file-row">
                ${b}
                <span class="vex-pp-fi-name" title="${m(N.name)}">${m(N.name)}</span>
                <span class="vex-pp-fi-size">${r(N.size)}</span>
                <button class="vex-pp-fi-del" type="button" data-kind="${V}" data-ridx="${l}" aria-label="remove">${W}</button>
            </div>`).join("")+`<div id="vex-pp-sentinel-${V}" style="height:1px;flex-shrink:0"></div>`,Q.querySelectorAll(".vex-pp-fi-del").forEach(N=>{N.addEventListener("click",()=>{const l=parseInt(N.dataset.ridx,10);N.dataset.kind==="inv"?H(l):_(l)})}),ee){const N=t("vex-preview-count")||"显示前 {n} / 共 {m}";ee.textContent=N.replace("{n}",U.length).replace("{m}",T.length)}y(V,T.length)}function y(V,Q){if((V==="inv"?c:v)>=Q)return;const ne=s("vex-pp-sentinel-"+V),se=s("vex-pp-"+V+"-list");if(!ne||!se)return;const ue=new IntersectionObserver(b=>{b[0].isIntersecting&&(ue.disconnect(),V==="inv"?c+=50:v+=50,S(V))},{root:se,threshold:.8});ue.observe(ne)}function p(V,Q,ee,ne){const se=s(V),ue=s(Q);!se||!ue||(se.addEventListener("click",()=>ue.click()),se.addEventListener("keydown",b=>{(b.key==="Enter"||b.key===" ")&&(b.preventDefault(),ue.click())}),se.addEventListener("dragover",b=>{b.preventDefault(),se.classList.add("drag-over")}),se.addEventListener("dragleave",()=>se.classList.remove("drag-over")),se.addEventListener("drop",b=>{b.preventDefault(),se.classList.remove("drag-over");const T=Array.from(b.dataTransfer.files).filter(U=>a.test(U.name));if(!T.length){showToast(t("vex-toast-bad-ext"),"error");return}ee(T)}),ue.addEventListener("change",()=>{const b=Array.from(ue.files);ee(b),ue.value=""}))}async function $(){if(f||!k.length||!i.length)return;f=!0,s("vex-build").disabled=!0,s("vex-progress").style.display="flex";var V=document.getElementById("vex-download");V&&(V.style.display="none"),["vex-summary-collapse","vex-detail-collapse"].forEach(function(se){var ue=document.getElementById(se);ue&&(ue.style.display="none")});const Q=Date.now();s("vex-progress-title").textContent=t("vex-progress-running")||"AI 抽取中",s("vex-progress-sub").textContent=(t("vex-progress-sub")||"{a} 张发票 + {b} 份报告 · 并行处理").replace("{a}",k.length).replace("{b}",i.length);const ee=setInterval(()=>{const se=Math.floor((Date.now()-Q)/1e3);s("vex-progress-sub").textContent=(t("vex-progress-elapsed")||"已 {s} 秒 · {a} 张发票 + {b} 份报告").replace("{s}",se).replace("{a}",k.length).replace("{b}",i.length)},1e3);try{const se=new FormData;for(const pe of k)se.append("invoices",pe);for(const pe of i)se.append("reports",pe);const ue=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";se.append("lang",ue);const b=localStorage.getItem("mrpilot_token")||"",C=await fetch("/api/vat_excel/submit",{method:"POST",headers:o(),body:se});let T=null;try{T=await C.json()}catch{T=null}if(!C.ok||!T||!T.ok||!T.job_id)throw clearInterval(ee),new Error(T&&T.detail||"HTTP "+C.status);const U=s("vex-progress-sub"),N=await window._reconPollJob(T.job_id,b,{onProgress:pe=>{U&&(U.textContent=window._reconProgressText(pe,ue))}});if(clearInterval(ee),!N||N.status!=="done"||!N.result_id)throw new Error(t("vex-toast-fail")||"生成失败");const l=N.result_id;let j=0;const O=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(l)+"/download",{headers:o()});if(!O.ok)throw new Error("HTTP "+O.status);const X=(O.headers.get("Content-Disposition")||"").match(/filename="([^"]+)"/),de=X&&X[1]||"vat_recon_"+Date.now()+".xlsx",oe=await O.blob(),ce=URL.createObjectURL(oe),ae=s("vex-download");ae.href=ce,ae.download=de;try{const pe=document.createElement("a");pe.href=ce,pe.download=de,document.body.appendChild(pe),pe.click(),setTimeout(()=>pe.remove(),100)}catch{}s("vex-progress").style.display="none";var ne=document.getElementById("vex-download");ne&&(ne.style.display=""),l&&(j=await Z(l)),window._onVexResultShown&&window._onVexResultShown(),j>0?showToast((t("vex-toast-some-fail")||"有 {n} 张发票 OCR 失败").replace("{n}",j),"warn"):showToast(t("vex-toast-done")||"Excel 已生成","success"),R(),setTimeout(D,800)}catch(se){clearInterval(ee),s("vex-progress").style.display="none";const ue=(t("vex-toast-fail")||"生成失败")+": "+(se.message||se);showToast(ue,"error")}finally{f=!1,s("vex-build").disabled=!1}}function P(){k=[],i=[];var V=document.getElementById("vex-download");V&&(V.style.display="none"),M()}function Y(V){if(V==null)return"—";var Q=parseFloat(V);return isNaN(Q)?"—":Q.toLocaleString("th-TH",{minimumFractionDigits:2,maximumFractionDigits:2})}async function Z(V){try{var Q=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(V),{headers:o()});if(!Q.ok)throw new Error(Q.status);var ee=await Q.json(),ne=ee.raw_data_json;if(typeof ne=="string")try{ne=JSON.parse(ne)}catch{ne={}}ne=ne||{};var se=ne.rows||[],ue=[];se.forEach(function(T){T.kind==="invoice_orphan"?ue.push({invoice_no:T.invoice_no||"",field:"仅发票有",report_value:"—",invoice_value:Y(T.amount_inv),kind:T.kind}):T.kind==="report_orphan"?ue.push({invoice_no:T.invoice_no||"",field:"仅报告有",report_value:Y(T.amount_rep),invoice_value:"—",kind:T.kind}):T.dims&&Object.keys(T.dims).length>0&&Object.keys(T.dims).forEach(function(U){var N=String(T.dims[U]||""),l=N.split(" ≠ ");ue.push({invoice_no:T.invoice_no||"",field:U,report_value:l[0]||N,invoice_value:l.length>1?l[1]:"—",kind:"diff"})})});var b=se.filter(function(T){return T.kind==="matched_cash"}).length,C=Math.max(0,parseInt(ne.invoice_ocr_failed_count||0,10));return window._vexLastTask={total:ne.n_total||0,matched:ne.n_ok||0,diff:ne.n_diff||0,incomplete:C,cash:b,diff_rows:ue,task_id:V},window._fillVexSummary&&window._fillVexSummary(),window._fillVexDetail&&window._fillVexDetail(),C}catch{return 0}}function le(){const V=document.getElementById("vex-pane");V&&V.querySelectorAll("[data-i18n]").forEach(Q=>{const ee=t(Q.dataset.i18n);ee&&(Q.textContent=ee)}),M(),D()}function ie(){p("vex-drop-invoice","vex-input-invoice",I),p("vex-drop-report","vex-input-report",L);const V=s("vex-build"),Q=s("vex-reset");V&&V.addEventListener("click",$),Q&&Q.addEventListener("click",P),document.querySelectorAll('[data-recon-tab="sale-vat"]').forEach(se=>{se.addEventListener("click",()=>{R(),D()})}),g();const ee=document.getElementById("vex-task-search");ee&&ee.addEventListener("input",z);const ne=document.getElementById("vex-toggle-preview");ne&&ne.addEventListener("click",()=>{const se=s("vex-preview-panel"),ue=s("vex-toggle-preview-label"),b=se&&se.style.display!=="none";se&&(se.style.display=b?"none":""),ne&&ne.classList.toggle("open",!b),ue&&(ue.textContent=b?t("vex-toggle-preview-open")||"查看清单":t("vex-toggle-preview-close")||"收起清单"),b||te()}),M(),R()}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",ie):ie(),typeof window.subscribeI18n=="function"&&(window.subscribeI18n("vex-excel",le),window.subscribeI18n("vex-preview-panel",te))})();(function(){const e=y=>document.getElementById(y),n=()=>localStorage.getItem("mrpilot_token")||"",a=()=>typeof window.currentLang=="string"&&window.currentLang?window.currentLang:localStorage.getItem("mrpilot_lang")||"th",s=()=>({Authorization:"Bearer "+n()}),o={inited:!1,glFile:[],vatFile:[],running:!1,currentTaskId:null,lastDetail:[],lastSummary:null},m={th:{not_found:"ไม่พบข้อมูล",running:"กำลังกระทบยอด…",error:"เกิดข้อผิดพลาด",need_files:"กรุณาเลือกไฟล์ทั้งสอง",done:"เสร็จสิ้น",hint_need_both:"อัปโหลด ① รายงานภาษีขาย + ② GL",hint_need_one_more:"อัปโหลดอีก 1 ไฟล์",hint_ready:"พร้อมแล้ว · กดเริ่มกระทบยอด",hist_load:"โหลด",hist_export:"ส่งออก",hist_delete:"ลบ",confirm_delete:"ยืนยันการลบงานนี้?",s_gl_total:"ยอดรวมตามบัญชีแยกประเภท",s_minus_gl_cr:"หัก : รายการเครดิตที่ไม่มีในรายงานภาษีขาย",s_plus_gl_dr:"บวก : รายการเดบิตที่ไม่มีในรายงานภาษีขาย",s_plus_vat_p:"บวก : รายการยอดขายที่ไม่มีในบัญชีแยกประเภท",s_minus_vat_n:"หัก : รายการลดหนี้ที่ไม่มีในบัญชีแยกประเภท",s_vat_total:"ยอดรวมตามรายงานภาษีขาย"},zh:{not_found:"未找到数据",running:"正在对账中...",error:"出错了",need_files:"请先选择两个文件",done:"完成",hint_need_both:"请上传① 销项税报告 + ② 总账 GL",hint_need_one_more:"还需上传 1 份文件",hint_ready:"已就绪 · 点击开始对账",hist_load:"加载",hist_export:"导出",hist_delete:"删除",confirm_delete:"确认删除此任务？",s_gl_total:"总账金额合计",s_minus_gl_cr:"减：销项税报告中未列的贷方记录",s_plus_gl_dr:"加：销项税报告中未列的借方记录",s_plus_vat_p:"加：总账中未列的销售记录",s_minus_vat_n:"减：总账中未列的贷项凭单(credit note)记录",s_vat_total:"销项税报告金额合计"},en:{not_found:"Not found",running:"Reconciling...",error:"Error",need_files:"Please select both files",done:"Done",hint_need_both:"Upload ① Output VAT report + ② GL file",hint_need_one_more:"1 more file required",hint_ready:"Ready · click Run to start",hist_load:"Load",hist_export:"Export",hist_delete:"Delete",confirm_delete:"Delete this task?",s_gl_total:"Total per General Ledger",s_minus_gl_cr:"Less: GL credits not in VAT Report",s_plus_gl_dr:"Add: GL debits not in VAT Report",s_plus_vat_p:"Add: Sales in VAT Report not in GL",s_minus_vat_n:"Less: Credit notes in VAT Report not in GL",s_vat_total:"Total per VAT Sales Report"},ja:{not_found:"データなし",running:"照合中…",error:"エラー",need_files:"両方のファイルを選択してください",done:"完了",hint_need_both:"① 売上税報告 + ② GL をアップロード",hint_need_one_more:"あと 1 ファイル必要",hint_ready:"準備完了 · 「開始」をクリック",hist_load:"読込",hist_export:"出力",hist_delete:"削除",confirm_delete:"このタスクを削除しますか?",s_gl_total:"総勘定元帳合計",s_minus_gl_cr:"減：売上税報告にないGL貸方記録",s_plus_gl_dr:"加：売上税報告にないGL借方記録",s_plus_vat_p:"加：GLにない売上記録",s_minus_vat_n:"減：GLにない赤伝記録",s_vat_total:"売上税報告合計"}},r=y=>(m[a()]||m.th)[y]||y;function k(y){const p=a(),P={gl_no_revenue_rows:{zh:"GL 中未找到收入科目行。请确认「收入科目前缀」是否正确(收入科目通常以 4 开头),改对后重试。",th:"ไม่พบรายการบัญชีรายได้ใน GL · ตรวจสอบ «คำนำหน้าบัญชีรายได้» (รายได้มักขึ้นต้นด้วย 4) แล้วลองใหม่",en:"No revenue-account rows found in the GL. Check the “revenue account prefix” (revenue usually starts with 4) and retry.",ja:"GL に収益科目の行が見つかりません。「収益科目プレフィックス」(通常 4 で始まる)を確認して再試行してください。"},gl_parse_failed:{zh:"GL 文件解析失败。请确认文件含日期/科目/借贷列,或换清晰的 Excel/CSV 重传。",th:"อ่านไฟล์ GL ไม่สำเร็จ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต-เครดิต หรืออัปโหลด Excel/CSV ที่ชัดเจน",en:"Failed to parse the GL file. Ensure it has date/account/debit-credit columns, or re-upload a clean Excel/CSV.",ja:"GL ファイルの解析に失敗しました。日付/科目/借方貸方列を確認するか、Excel/CSV を再アップロードしてください。"},vat_no_rows:{zh:"销项税报告里没有可对账的数据行。请确认上传了正确的销项税报告。",th:"ไม่พบแถวข้อมูลในรายงานภาษีขาย · ตรวจสอบว่าอัปโหลดรายงานที่ถูกต้อง",en:"No rows found in the sales-VAT report. Please check you uploaded the correct report.",ja:"売上VATレポートに行が見つかりません。正しいレポートをアップロードしたか確認してください。"},vat_parse_failed:{zh:"销项税报告解析失败。请换更清晰的版本,或转成 Excel/PDF 重传。",th:"อ่านรายงานภาษีขายไม่สำเร็จ · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น Excel/PDF",en:"Failed to parse the sales-VAT report. Try a clearer version, or convert to Excel/PDF.",ja:"売上VATレポートの解析に失敗しました。より鮮明な版か、Excel/PDF に変換してください。"}}[y];return P?P[p]||P.th||P.en:r("error")||"Error"}const i=y=>y==null||isNaN(y)?"":Number(y).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});function f(y,p,$,P){const Y=e(y),Z=e(p),le=e($);if(!Y||!Z||!le)return;const ie=V=>{if(!V||!V.length)return;const Q=Array.isArray(o[P])?o[P].slice():[],ee=new Set(Q.map(ne=>ne.name+"|"+ne.size));for(const ne of V){if(!ne)continue;const se=ne.name+"|"+ne.size;ee.has(se)||(Q.push(ne),ee.add(se))}o[P]=Q,u(le,Q),v(),E(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()};Y.addEventListener("click",()=>Z.click()),Y.addEventListener("keydown",V=>{(V.key==="Enter"||V.key===" ")&&(V.preventDefault(),Z.click())}),Z.addEventListener("change",()=>{ie(Array.from(Z.files||[])),Z.value=""}),Y.addEventListener("dragover",V=>{V.preventDefault(),Y.classList.add("drag-over")}),Y.addEventListener("dragleave",()=>Y.classList.remove("drag-over")),Y.addEventListener("drop",V=>{V.preventDefault(),Y.classList.remove("drag-over");const Q=V.dataTransfer&&V.dataTransfer.files?Array.from(V.dataTransfer.files):[];ie(Q)})}function u(y,p){if(!y)return;if(!p||p.length===0){y.textContent="";return}const $=p.reduce((P,Y)=>P+Math.round(Y.size/1024),0);if(p.length===1)y.textContent=p[0].name+"  ("+$+" KB)";else{const P=window.t&&window.t("glv-files-count")||"{n} 个文件";y.textContent=P.replace("{n}",p.length)+"  ("+$+" KB)"}}function c(y){const p=o[y];return Array.isArray(p)?p:p?[p]:[]}function v(){const y=e("btn-glv-run");if(!y)return;const p=c("glFile").length>0&&c("vatFile").length>0;y.disabled=!p||o.running}function E(){const y=e("glv-status");if(!y||o.running)return;const p=c("vatFile").length,$=c("glFile").length;p===0&&$===0?(y.className="vex-action-info muted",y.innerHTML="<span>"+r("hint_need_both")+"</span>"):p>0&&$>0?(y.className="vex-action-info ok",y.innerHTML="<span>"+r("hint_ready")+"</span>"):(y.className="vex-action-info muted",y.innerHTML="<span>"+r("hint_need_one_more")+"</span>")}function x(y,p){const $=y==="vat"?"vatFile":"glFile",P=y==="vat"?"glv-vat-input":"glv-gl-input",Y=y==="vat"?"glv-vat-name":"glv-gl-name",Z=c($);p==null?o[$]=[]:o[$]=Z.filter((ie,V)=>V!==p);const le=e(P);le&&(le.value=""),u(e(Y),c($)),v(),E(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}window._glvRemoveFile=x;function R(){o.glFile=[],o.vatFile=[],o.currentTaskId=null,o.lastDetail=[],o.lastSummary=null;const y=e("glv-vat-input");y&&(y.value="");const p=e("glv-gl-input");p&&(p.value="");const $=e("glv-vat-name");$&&($.textContent="");const P=e("glv-gl-name");P&&(P.textContent="");const Y=e("glv-result");Y&&(Y.style.display="none");const Z=e("glv-kpi-strip");Z&&(Z.style.display="none"),v(),E(),window._glvClearPreviewSearch&&window._glvClearPreviewSearch(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}function D(y){const p=e("glv-tbody");if(!p)return;re(y.length),p.innerHTML="";const $=r("not_found"),P=document.createDocumentFragment();y.forEach(Y=>{const Z=document.createElement("tr"),le=(ne,se)=>{const ue=document.createElement("td");return se&&(ue.className=se),ue.textContent=ne,ue},ie=Y.gl_amount===null||Y.gl_amount===void 0,V=Y.diff;let Q="glv-num",ee="glv-num";ie?(ee+=" glv-cell-missing",Q+=" glv-cell-missing"):Math.abs(V||0)<.005?Q+=" glv-cell-ok":Q+=" glv-cell-diff",Z.appendChild(le(Y.doc_no||"","glv-doc")),Z.appendChild(le(Y.date||"","")),Z.appendChild(le(Y.customer_name||"","")),Z.appendChild(le(i(Y.vat_amount),"glv-num")),Z.appendChild(le(ie?$:i(Y.gl_amount),ee)),Z.appendChild(le(ie?$:i(Y.diff),Q)),Z.appendChild(le(Y.account_codes||"","glv-doc")),P.appendChild(Z)}),p.appendChild(P)}function w(y){const p=e("glv-summary-table")&&e("glv-summary-table").querySelector("tbody");if(!p)return;p.innerHTML="",[{label:r("s_gl_total"),amount:y.gl_total,emph:!0,items:[],negate:!1},{label:r("s_minus_gl_cr"),amount:-(y.gl_only_credit||0),emph:!1,items:y.gl_only_credit_items||[],negate:!0},{label:r("s_plus_gl_dr"),amount:y.gl_only_debit||0,emph:!1,items:y.gl_only_debit_items||[],negate:!1},{label:r("s_plus_vat_p"),amount:y.vat_only_positive||0,emph:!1,items:y.vat_only_positive_items||[],negate:!1},{label:r("s_minus_vat_n"),amount:y.vat_only_negative||0,emph:!1,items:y.vat_only_negative_items||[],negate:!1},{label:r("s_vat_total"),amount:y.vat_total,emph:!0,items:[],negate:!1}].forEach(({label:P,amount:Y,emph:Z,items:le,negate:ie})=>{const V=document.createElement("tr");V.className=Z?"glv-summary-total":"glv-summary-sect";const Q=document.createElement("td"),ee=document.createElement("td");Q.textContent=P,ee.textContent=Z?i(Y):"",V.appendChild(Q),V.appendChild(ee),p.appendChild(V),(le||[]).forEach(ne=>{const se=document.createElement("tr");se.className="glv-summary-item";const ue=document.createElement("td"),b=document.createElement("td"),C=[ne.doc_no,ne.date,ne.name].filter(Boolean);ue.textContent="· "+C.join("  ·  ");const T=ie?-(ne.amount||0):ne.amount||0;b.textContent=i(T),se.appendChild(ue),se.appendChild(b),p.appendChild(se)})})}function B(y){e("glv-kpi-matched")&&(e("glv-kpi-matched").textContent=y&&y.matched!=null?y.matched:"—"),e("glv-kpi-diff")&&(e("glv-kpi-diff").textContent=y&&y.diff!=null?y.diff:"—"),e("glv-kpi-unmatched")&&(e("glv-kpi-unmatched").textContent=y&&y.unmatched!=null?y.unmatched:"—")}function z(y){if(!y)return"";try{const p=new Date(y);if(isNaN(p.getTime()))return y;const $=P=>String(P).padStart(2,"0");return p.getFullYear()+"-"+$(p.getMonth()+1)+"-"+$(p.getDate())+" "+$(p.getHours())+":"+$(p.getMinutes())}catch{return y}}const q=10;var F=[],A=1;function g(){A=1,d();var y=((e("glv-hist-search")||{}).value||"").trim().toLowerCase();if(y){var p=e("glv-history-tbody");p&&p.querySelectorAll("tr").forEach(function($){$.dataset.taskId&&($.style.display=$.textContent.toLowerCase().indexOf(y)>=0?"":"none")})}}function d(){const y=e("glv-history-table-wrap"),p=e("glv-history-empty"),$=e("glv-history-tbody"),P=e("glv-history-pager"),Y=e("glv-history-pager-info"),Z=e("glv-history-prev"),le=e("glv-history-next");if(!$)return;if($.innerHTML="",!F.length){y&&(y.style.display="none"),p&&(p.style.display=""),P&&(P.style.display="none");return}y&&(y.style.display=""),p&&(p.style.display="none");const ie=Math.ceil(F.length/q);A>ie&&(A=ie);const V=(A-1)*q,Q=F.slice(V,V+q);P&&(P.style.display=F.length>q?"":"none",Y&&(Y.textContent=A+" / "+ie),Z&&(Z.disabled=A<=1),le&&(le.disabled=A>=ie)),Q.forEach(ne=>{const se=document.createElement("tr");se.dataset.taskId=ne.id;const ue=document.createElement("td");ue.textContent=z(ne.created_at);const b=document.createElement("td");b.className="glv-history-file",b.title=(ne.vat_filename||"")+" + "+(ne.gl_filename||""),b.textContent=(ne.vat_filename||"?")+" + "+(ne.gl_filename||"?");const C=document.createElement("td");C.className="glv-num",C.textContent=(ne.vat_row_count||0)+" / "+(ne.gl_row_count||0);const T=document.createElement("td");T.className="glv-num",T.textContent=ne.matched_count||0;const U=document.createElement("td");U.className="glv-num",U.textContent=ne.diff_count||0;const N=document.createElement("td");N.className="glv-num",N.textContent=ne.unmatched_count||0;const l=document.createElement("td");l.className="glv-history-actions";const j=(de,oe,ce,ae)=>{const pe=document.createElement("button");return pe.type="button",ce&&(pe.className=ce),pe.title=oe,pe.setAttribute("aria-label",oe),pe.innerHTML=de,pe.onclick=ae,pe},O='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 8a6 6 0 1 0 12 0A6 6 0 0 0 2 8z"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',J='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',X='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';l.appendChild(j(O,r("hist_load"),"",()=>L(ne.id))),l.appendChild(j(J,r("hist_export"),"",()=>H(ne.id))),l.appendChild(j(X,r("hist_delete"),"glv-del",()=>_(ne.id))),[ue,b,C,T,U,N,l].forEach(de=>se.appendChild(de)),$.appendChild(se)})}function h(){var y=e("glv-history-prev"),p=e("glv-history-next");y&&!y._glvBound&&(y._glvBound=!0,y.addEventListener("click",function(){A>1&&(A--,d())})),p&&!p._glvBound&&(p._glvBound=!0,p.addEventListener("click",function(){var $=Math.ceil(F.length/q);A<$&&(A++,d())}))}async function I(){try{const p=await(await fetch("/api/recon/gl-vat/tasks",{headers:s()})).json();F=p&&p.tasks||[],A=1,d(),h()}catch(y){console.error("[gl-vat] history load failed:",y)}}async function L(y){try{const $=await(await fetch("/api/recon/gl-vat/"+y,{headers:s()})).json();if(!$||!$.ok)throw new Error("load_failed");o.currentTaskId=y,o.lastDetail=$.detail||[],o.lastSummary=$.summary||{},B($.stats||{}),D(o.lastDetail),w(o.lastSummary);const P=e("glv-result");P&&(P.style.display=""),W(),window.scrollTo({top:P?P.offsetTop-80:0,behavior:"smooth"})}catch(p){console.error("[gl-vat] load task failed:",p),alert(r("error")+": "+(p.message||p))}}async function H(y){try{const p="/api/recon/gl-vat/"+y+"/export?lang="+encodeURIComponent(a()),$=await fetch(p,{headers:s()});if(!$.ok)throw new Error("HTTP "+$.status);const P=await $.blob(),Y=document.createElement("a");Y.href=URL.createObjectURL(P),Y.download="GL_VAT_recon_"+y+".xlsx",document.body.appendChild(Y),Y.click(),setTimeout(()=>{URL.revokeObjectURL(Y.href),Y.remove()},200)}catch(p){console.error("[gl-vat] exportTask failed:",p),typeof showToast=="function"&&showToast(r("error")+": "+(p.message||p),"error")}}async function _(y){let p;if(typeof window.showConfirm=="function"?p=await window.showConfirm(r("confirm_delete"),{danger:!0}):p=confirm(r("confirm_delete")),!!p)try{const $=await fetch("/api/recon/gl-vat/"+y,{method:"DELETE",headers:s()});if(!$.ok)throw new Error("HTTP "+$.status);I()}catch($){console.error("[gl-vat] delete failed:",$),typeof showToast=="function"&&showToast(r("error")+": "+($.message||$),"error")}}async function M(){if(!o.glFile||!o.vatFile){typeof showToast=="function"&&showToast(r("need_files"),"warn");return}o.running=!0,v();const y=e("glv-status"),p=e("glv-progress"),$=e("glv-progress-sub");y&&(y.className="vex-action-info muted",y.style.color="",y.innerHTML="<span>"+r("running")+"</span>"),p&&(p.style.display=""),$&&($.textContent=(o.vatFile.name||"VAT")+" + "+(o.glFile.name||"GL"));const P=new FormData,Y=c("vatFile"),Z=c("glFile");for(const ie of Y)P.append("vat_files",ie,ie.name);for(const ie of Z)P.append("gl_files",ie,ie.name);const le=(e("glv-prefix")&&e("glv-prefix").value||"4").trim()||"4";P.append("revenue_prefix",le),P.append("lang",a());try{const ie=await fetch("/api/recon/gl-vat/submit",{method:"POST",headers:s(),body:P});let V=null;try{V=await ie.json()}catch{V=null}if(!ie.ok||!V||!V.ok||!V.job_id)throw new Error(V&&V.detail||V&&V.error||"HTTP "+ie.status);const Q=e("glv-progress-sub"),ee=await window._reconPollJob(V.job_id,n(),{onProgress:b=>{Q&&(Q.textContent=window._reconProgressText(b,a()))}});if(!ee||ee.status!=="done"||!ee.result_id)throw ee&&ee.status==="failed"&&ee.error_code?new Error(k(ee.error_code)):new Error(r("error")||"Error");const ne=await fetch("/api/recon/gl-vat/"+encodeURIComponent(ee.result_id),{headers:s()});let se=null;try{se=await ne.json()}catch{se=null}if(!ne.ok||!se||!se.ok)throw new Error(se&&se.detail||se&&se.error||"HTTP "+ne.status);o.currentTaskId=se.task_id,o.lastDetail=se.detail||[],o.lastSummary=se.summary||{},B(se.stats||{}),D(o.lastDetail),w(o.lastSummary);const ue=e("glv-result");ue&&(ue.style.display=""),W(),y&&(y.className="vex-action-info ok",y.style.color="",y.innerHTML="<span>"+r("done")+" · GL "+(se.gl_row_count||0)+" · VAT "+(se.vat_row_count||0)+"</span>"),I()}catch(ie){console.error("[gl-vat] run failed:",ie),y&&(y.className="vex-action-info",y.style.color="#ef4444",y.innerHTML="<span>"+r("error")+": "+(ie.message||ie)+"</span>")}finally{o.running=!1,p&&(p.style.display="none"),v()}}async function K(){if(o.currentTaskId)try{const y="/api/recon/gl-vat/"+o.currentTaskId+"/export?lang="+encodeURIComponent(a()),p=await fetch(y,{headers:s()});if(!p.ok)throw new Error("HTTP "+p.status);const $=await p.blob(),P=document.createElement("a");P.href=URL.createObjectURL($),P.download="GL_VAT_recon_"+o.currentTaskId+".xlsx",document.body.appendChild(P),P.click(),setTimeout(()=>{URL.revokeObjectURL(P.href),P.remove()},200)}catch(y){console.error("[gl-vat] export failed:",y),typeof showToast=="function"&&showToast(r("error")+": "+(y.message||y),"error")}}function G(){o.running||E(),I(),o.lastDetail&&o.lastDetail.length&&D(o.lastDetail),o.lastSummary&&w(o.lastSummary)}function W(){var y=e("glv-kpi-strip");y&&(y.style.display="");var p=e("glv-section-summary");p&&p.setAttribute("data-collapsed","false");var $=e("glv-section-detail");$&&$.setAttribute("data-collapsed","false")}function te(){document.querySelectorAll(".glv-section-head[data-toggle]").forEach(y=>{const p=y.getAttribute("data-toggle"),$=document.getElementById(p);if(!$)return;const P=Y=>{if(Y.target&&Y.target.closest("button")!==null&&!Y.target.classList.contains("glv-section-head"))return;const Z=$.getAttribute("data-collapsed")==="true";$.setAttribute("data-collapsed",Z?"false":"true")};y.addEventListener("click",P),y.addEventListener("keydown",Y=>{(Y.key==="Enter"||Y.key===" ")&&(Y.preventDefault(),P(Y))})})}function re(y){const p=e("glv-detail-count");p&&(p.textContent=y!=null?String(y):"")}function S(){if(o.inited){I();return}o.inited=!0,f("glv-drop-gl","glv-gl-input","glv-gl-name","glFile"),f("glv-drop-vat","glv-vat-input","glv-vat-name","vatFile");const y=e("btn-glv-run");y&&y.addEventListener("click",M);const p=e("btn-glv-export");p&&p.addEventListener("click",K);const $=e("btn-glv-reset");$&&$.addEventListener("click",R);const P=e("glv-hist-search");P&&P.addEventListener("input",g),te(),B(null),E(),window._loadGlvHistory=I,I(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("gl-vat-recon",G)}window.GlVatRecon={ensureInit:S},window._glvPreviewFiles=function(y){return c(y==="vat"?"vatFile":"glFile")}})();(function(){const e=["flowaccount","peak","xero","quickbooks","express"],n={flowaccount:"FlowAccount",peak:"PEAK",xero:"Xero",quickbooks:"QuickBooks",express:"Express"},a=["expense_office","expense_travel","expense_utility","asset_inventory","asset_fixed","liability_ap","revenue_sales","revenue_service","other"],s=["vat_7","vat_0","vat_exempt","wht_1","wht_3","wht_5","non_vat"],o="468b50c1-5593-4fd6-990d-515ce8085563";let m={sub:"clients",loaded:{clients:!1,accounts:!1,taxes:!1,products:!1},items:{clients:[],accounts:[],taxes:[],products:[]},clientList:[],clientLoaded:!1,addingNew:{clients:!1,accounts:!1,taxes:!1,products:!1},bound:!1};function r(){const L=typeof _userInfo<"u"?_userInfo:null;return!!(L&&(L.role==="owner"||L.is_super_admin))}function k(){const L=typeof _userInfo<"u"?_userInfo:null;return!!(L&&L.id===o)}function i(L){return typeof escapeHtml=="function"?escapeHtml(L==null?"":String(L)):String(L??"")}function f(L,H){try{typeof showToast=="function"&&showToast(L,H||"info")}catch{}}async function u(L,H){const _=localStorage.getItem("mrpilot_token");if(_&&!(m.loaded[L]&&!H))try{const M=await fetch("/api/erp/mappings/"+L,{headers:{Authorization:"Bearer "+_}});if(!M.ok)throw new Error("http_"+M.status);const K=await M.json();m.items[L]=K.items||[],m.loaded[L]=!0}catch{m.items[L]=[],m.loaded[L]=!1}}async function c(L){if(m.clientLoaded)return;const H=localStorage.getItem("mrpilot_token");if(H)try{const _=await fetch("/api/clients?include_inactive=false",{headers:{Authorization:"Bearer "+H}});if(!_.ok)throw new Error("http_"+_.status);const M=await _.json();m.clientList=(M.clients||M.items||[]).filter(K=>K.is_active!==!1),m.clientLoaded=!0}catch{m.clientList=[]}}function v(){const L=document.getElementById("erp-map-pane-wrap");if(!L)return;const H=!r();let _="";H&&(_+='<div class="erp-map-readonly-banner"><svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="8"/><path d="M10 6v4M10 13v0.01"/></svg>'+i(t("erp-map-readonly-tip"))+"</div>"),_+='<div class="erp-map-toolbar">',!H&&m.sub!=="products"&&(_+='<button class="btn btn-primary" type="button" id="erp-map-add-btn" data-i18n="erp-map-add-row">'+i(t("erp-map-add-row"))+"</button>"),_+="</div>",_+='<div class="erp-map-table" id="erp-map-table-host"></div>',L.innerHTML=_,E();const M=document.getElementById("erp-map-dev-bar");M&&(M.style.display=r()&&k()?"":"none")}function E(){const L=document.getElementById("erp-map-table-host");if(!L)return;const H=m.sub,_=m.items[H]||[],M=m.addingNew[H],K=!r();if(!_.length&&!M){L.innerHTML='<div class="erp-map-empty"><strong>'+i(t("erp-map-empty-"+H))+"</strong>"+i(t("erp-map-empty-"+H+"-sub"))+"</div>";return}let G="";G+=x(H),M&&!K&&(G+=z(H)),_.forEach(function(W){G+=q(H,W,K)}),L.innerHTML=G}function x(L){return L==="clients"?'<div class="erp-map-row erp-map-head row-clients"><div>'+i(t("erp-map-col-client"))+"</div><div>"+i(t("erp-map-col-erp"))+"</div><div>"+i(t("erp-map-col-erp-code"))+"</div><div>"+i(t("erp-map-col-notes"))+"</div><div>"+i(t("erp-map-col-actions"))+"</div></div>":L==="accounts"?'<div class="erp-map-row erp-map-head row-accounts"><div>'+i(t("erp-map-col-erp"))+"</div><div>"+i(t("erp-map-col-category"))+"</div><div>"+i(t("erp-map-col-erp-code"))+"</div><div>"+i(t("erp-map-col-erp-name"))+"</div><div>"+i(t("erp-map-col-notes"))+"</div><div>"+i(t("erp-map-col-actions"))+"</div></div>":L==="products"?'<div class="erp-map-row erp-map-head row-products"><div>'+i(t("erp-map-col-item-name"))+"</div><div>"+i(t("erp-map-col-erp-product-code"))+"</div><div>"+i(t("erp-map-col-erp-name"))+"</div><div>"+i(t("erp-map-col-notes"))+"</div><div>"+i(t("erp-map-col-actions"))+"</div></div>":'<div class="erp-map-row erp-map-head row-taxes"><div>'+i(t("erp-map-col-erp"))+"</div><div>"+i(t("erp-map-col-tax"))+"</div><div>"+i(t("erp-map-col-erp-tax-code"))+"</div><div>"+i(t("erp-map-col-notes"))+"</div><div>"+i(t("erp-map-col-actions"))+"</div></div>"}function R(L,H){let _='<select class="form-input" data-erp-field="'+H+'">';return _+='<option value="">'+i(t("erp-map-pick-erp"))+"</option>",e.forEach(function(M){const K=M===L?" selected":"";_+='<option value="'+M+'"'+K+">"+i(n[M])+"</option>"}),_+="</select>",_}function D(L){let H='<select class="form-input" data-erp-field="client_id">';return H+='<option value="">'+i(t("erp-map-pick-client"))+"</option>",(m.clientList||[]).forEach(function(_){const M=String(_.id)===String(L)?" selected":"";H+='<option value="'+_.id+'"'+M+">"+i(_.name||"#"+_.id)+"</option>"}),H+="</select>",H}function w(L){let H='<select class="form-input" data-erp-field="pearnly_category">';return H+='<option value="">'+i(t("erp-map-pick-cat"))+"</option>",a.forEach(function(_){const M=_===L?" selected":"";H+='<option value="'+_+'"'+M+">"+i(t("erp-map-cat-"+_))+"</option>"}),H+="</select>",H}function B(L){let H='<select class="form-input" data-erp-field="pearnly_tax_kind">';return H+='<option value="">'+i(t("erp-map-pick-tax"))+"</option>",s.forEach(function(_){const M=_===L?" selected":"";H+='<option value="'+_+'"'+M+">"+i(t("erp-map-tax-"+_))+"</option>"}),H+="</select>",H}function z(L){const H='<button class="btn btn-primary" type="button" data-erp-save="new" style="padding:6px 12px;height:32px;">'+i(t("erp-map-save"))+"</button>";return L==="clients"?'<div class="erp-map-row erp-map-row-add row-clients" data-erp-row="new"><div data-label="'+i(t("erp-map-col-client"))+'">'+D("")+'</div><div data-label="'+i(t("erp-map-col-erp"))+'">'+R("","erp_type")+'</div><div data-label="'+i(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+i(t("erp-map-ph-erp-code"))+'"></div><div data-label="'+i(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+i(t("erp-map-ph-notes"))+'"></div><div>'+H+"</div></div>":L==="accounts"?'<div class="erp-map-row erp-map-row-add row-accounts" data-erp-row="new"><div data-label="'+i(t("erp-map-col-erp"))+'">'+R("","erp_type")+'</div><div data-label="'+i(t("erp-map-col-category"))+'">'+w("")+'</div><div data-label="'+i(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+i(t("erp-map-ph-acc-code"))+'"></div><div data-label="'+i(t("erp-map-col-erp-name"))+'"><input type="text" class="form-input" data-erp-field="erp_name" placeholder="'+i(t("erp-map-ph-acc-name"))+'"></div><div data-label="'+i(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+i(t("erp-map-ph-notes"))+'"></div><div>'+H+"</div></div>":'<div class="erp-map-row erp-map-row-add row-taxes" data-erp-row="new"><div data-label="'+i(t("erp-map-col-erp"))+'">'+R("","erp_type")+'</div><div data-label="'+i(t("erp-map-col-tax"))+'">'+B("")+'</div><div data-label="'+i(t("erp-map-col-erp-tax-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+i(t("erp-map-ph-tax-code"))+'"></div><div data-label="'+i(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+i(t("erp-map-ph-notes"))+'"></div><div>'+H+"</div></div>"}function q(L,H,_){const M=_?"":'<button class="erp-map-del-btn" type="button" data-erp-del="'+i(H.id)+'" title="'+i(t("erp-map-delete"))+'"><svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h12M8 6V4h4v2M6 6l1 11h6l1-11"/></svg></button>',K='<span class="erp-map-erp-badge">'+i(n[H.erp_type]||H.erp_type)+"</span>";if(L==="clients")return'<div class="erp-map-row row-clients"><div data-label="'+i(t("erp-map-col-client"))+'" class="erp-map-cell-name">'+i(H.client_name||"#"+H.client_id)+'</div><div data-label="'+i(t("erp-map-col-erp"))+'">'+K+'</div><div data-label="'+i(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+i(H.erp_code||"")+'</div><div data-label="'+i(t("erp-map-col-notes"))+'">'+i(H.notes||"")+"</div><div>"+M+"</div></div>";if(L==="accounts"){const W=t("erp-map-cat-"+(H.pearnly_category||"other"))||H.pearnly_category;return'<div class="erp-map-row row-accounts"><div data-label="'+i(t("erp-map-col-erp"))+'">'+K+'</div><div data-label="'+i(t("erp-map-col-category"))+'" class="erp-map-cell-name">'+i(W)+'</div><div data-label="'+i(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+i(H.erp_code||"")+'</div><div data-label="'+i(t("erp-map-col-erp-name"))+'">'+i(H.erp_name||"")+'</div><div data-label="'+i(t("erp-map-col-notes"))+'">'+i(H.notes||"")+"</div><div>"+M+"</div></div>"}if(L==="products")return'<div class="erp-map-row row-products"><div data-label="'+i(t("erp-map-col-item-name"))+'" class="erp-map-cell-name">'+i(H.item_name||"")+'</div><div data-label="'+i(t("erp-map-col-erp-product-code"))+'" class="erp-map-code">'+i(H.erp_code||"")+'</div><div data-label="'+i(t("erp-map-col-erp-name"))+'">'+i(H.erp_name||"")+'</div><div data-label="'+i(t("erp-map-col-notes"))+'">'+i(H.notes||"")+"</div><div>"+M+"</div></div>";const G=t("erp-map-tax-"+(H.pearnly_tax_kind||""))||H.pearnly_tax_kind;return'<div class="erp-map-row row-taxes"><div data-label="'+i(t("erp-map-col-erp"))+'">'+K+'</div><div data-label="'+i(t("erp-map-col-tax"))+'" class="erp-map-cell-name"><span class="erp-map-tax-badge">'+i(G)+'</span></div><div data-label="'+i(t("erp-map-col-erp-tax-code"))+'" class="erp-map-code">'+i(H.erp_code||"")+'</div><div data-label="'+i(t("erp-map-col-notes"))+'">'+i(H.notes||"")+"</div><div>"+M+"</div></div>"}async function F(L){const H=m.sub,_={};L.querySelectorAll("[data-erp-field]").forEach(function(W){_[W.dataset.erpField]=(W.value||"").trim()});const M=localStorage.getItem("mrpilot_token");if(!M)return;let K={},G="/api/erp/mappings/"+H;if(H==="clients"){if(!_.client_id||!_.erp_type||!_.erp_code){f(t("erp-map-save-fail"),"error");return}K={client_id:parseInt(_.client_id,10),erp_type:_.erp_type,erp_code:_.erp_code,notes:_.notes||""}}else if(H==="accounts"){if(!_.erp_type||!_.pearnly_category||!_.erp_code){f(t("erp-map-save-fail"),"error");return}K={erp_type:_.erp_type,pearnly_category:_.pearnly_category,erp_code:_.erp_code,erp_name:_.erp_name||"",notes:_.notes||""}}else{if(!_.erp_type||!_.pearnly_tax_kind||!_.erp_code){f(t("erp-map-save-fail"),"error");return}K={erp_type:_.erp_type,pearnly_tax_kind:_.pearnly_tax_kind,erp_code:_.erp_code,notes:_.notes||""}}try{const W=await fetch(G,{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+M},body:JSON.stringify(K)});if(!W.ok)throw new Error("http_"+W.status);m.addingNew[H]=!1,await u(H,!0),E(),f(t("erp-map-saved-toast"),"success")}catch{f(t("erp-map-save-fail"),"error")}}async function A(L){if(!await window.pearnlyConfirm(t("erp-map-confirm-delete")))return;const _=m.sub,M=localStorage.getItem("mrpilot_token");try{const K=await fetch("/api/erp/mappings/"+_+"/"+encodeURIComponent(L),{method:"DELETE",headers:{Authorization:"Bearer "+M}});if(!K.ok)throw new Error("http_"+K.status);await u(_,!0),E(),f(t("erp-map-deleted-toast"),"success")}catch{f(t("erp-map-delete-fail"),"error")}}async function g(){await c(),await u(m.sub,!1),v()}function d(L){L!==m.sub&&(m.sub=L,m.addingNew[L]=!1,["clients","accounts","taxes","products"].forEach(function(H){H!==L&&(m.addingNew[H]=!1)}),document.querySelectorAll(".erp-map-subtab").forEach(function(H){H.classList.toggle("active",H.dataset.erpSubtab===L)}),u(L,!1).then(function(){v()}))}function h(){m.bound||(m.bound=!0,document.addEventListener("click",function(L){const H=L.target.closest(".erp-subtab[data-erp-subtab]");if(H){L.preventDefault();const W=H.dataset.erpSubtab;document.querySelectorAll(".erp-subtab").forEach(function(te){te.classList.toggle("active",te.dataset.erpSubtab===W)}),document.querySelectorAll(".erp-subpanel").forEach(function(te){te.classList.toggle("active",te.dataset.erpSubpanel===W)}),W==="mappings"&&setTimeout(g,50);return}const _=L.target.closest(".erp-map-subtab[data-erp-subtab]");if(_){L.preventDefault(),d(_.dataset.erpSubtab);return}if(L.target.closest("#erp-map-add-btn")){if(L.preventDefault(),!r())return;m.addingNew[m.sub]=!0,E();return}const K=L.target.closest('[data-erp-save="new"]');if(K){L.preventDefault();const W=K.closest('[data-erp-row="new"]');W&&F(W);return}const G=L.target.closest("[data-erp-del]");if(G){L.preventDefault(),A(G.dataset.erpDel);return}}))}function I(){const L=document.getElementById("erp-map-pane-wrap");L&&L.children.length>0&&v(),document.querySelectorAll(".erp-map-subtab").forEach(function(H){const _="erp-map-subtab-"+H.dataset.erpSubtab,M=t(_);M&&M!==_&&(H.textContent=M)})}h(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-mappings",I)})();(function(){let e=null,n=0,a=!1;function s(g){return typeof escapeHtml=="function"?escapeHtml(g==null?"":String(g)):String(g??"")}function o(g,d){try{typeof showToast=="function"&&showToast(g,d||"info")}catch{}}async function m(g){const d=Date.now();if(e&&d-n<3e4)return e;const h=localStorage.getItem("mrpilot_token");if(!h)return[];try{const I=await fetch("/api/erp/connectors/status",{headers:{Authorization:"Bearer "+h}});if(!I.ok)return[];const L=await I.json();return e=L&&L.connectors||[],n=d,e}catch{return[]}}function r(){try{return localStorage.getItem("pn_push_default_connector")||""}catch{return""}}function k(g){try{localStorage.setItem("pn_push_default_connector",g||"")}catch{}}function i(g){if(!g||!g.length)return null;const d=r();if(d){const I=g.find(L=>L.id===d);if(I)return I}const h=g.find(I=>I.is_default);return h||g[0]}function f(g){if(!g)return!1;const d=String(g.status||"").toLowerCase();return d==="exception"||d==="exception_pending"||d==="rejected"}function u(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function c(g){const d=g&&(g.type||g.id);return d==="xero"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5.5 8l2 2 3-3.5"/></svg>':d==="webhook"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="11.5" r="1.8"/><circle cx="11" cy="4.5" r="1.8"/><path d="M6.4 10l3.2-4M5 9.6V5.5a3 3 0 016 0"/></svg>':'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/><rect x="11" y="3" width="3" height="10" rx="1"/></svg>'}async function v(g,d){if(!g||!d)return!1;const h=document.getElementById("btn-push-default");h&&(h.disabled=!0,h.classList.add("loading"));const I=localStorage.getItem("mrpilot_token");try{let L,H={method:"POST",headers:{Authorization:"Bearer "+I}};g.type==="xero"?L="/api/erp/xero/push/"+encodeURIComponent(d):(L="/api/erp/push",H.headers["Content-Type"]="application/json",H.body=JSON.stringify({history_id:d,endpoint_id:g.endpoint_id||void 0}));const _=await fetch(L,H);let M={};try{M=await _.json()}catch{}if(!_.ok){let K=M&&M.detail||"unknown";typeof K=="object"&&(K=K.code||JSON.stringify(K));let G=String(K||"unknown");if(g.type==="xero"){const W=G.replace(/^xero\./,"").toLowerCase(),te=t("xero-"+W);te&&te!=="xero-"+W&&(G=te)}return o(t("unified-push-fail").replace("{name}",g.name).replace("{err}",G),"error"),!1}if(M&&M.ok===!1){let K=M.error_msg||M.error_code||"unknown";return K=String(K).slice(0,200),o(t("unified-push-fail").replace("{name}",g.name).replace("{err}",K),"error"),!1}return o(t("unified-push-ok").replace("{name}",g.name),"success"),!0}catch(L){return o(t("unified-push-fail").replace("{name}",g.name).replace("{err}",L.message||"network"),"error"),!1}finally{h&&(h.disabled=!1,h.classList.remove("loading"))}}async function E(g,d){for(const h of g)await v(h,d)}function x(g,d){const h=document.createElement("div");h.className="pn-push-dropdown",h.id="pn-push-dropdown";const I=(g||[]).map(H=>{const _=!!(d&&H.id===d.id),M=H.method==="download"?t("unified-push-tag-download"):_?t("unified-push-tag-default"):"";return'<div class="pn-pd-item" data-cid="'+s(H.id)+'"><span class="pn-pd-icon">'+c(H)+'</span><span class="pn-pd-name">'+s(H.name)+"</span>"+(M?'<span class="pn-pd-tag">'+s(M)+"</span>":"")+(_?'<span class="pn-pd-check">✓</span>':"")+"</div>"}).join(""),L=g&&g.length>1?'<div class="pn-pd-divider"></div><div class="pn-pd-item pn-pd-all" data-cid="__all__"><span class="pn-pd-icon"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h10M3 10h10M3 13.5h6"/></svg></span><span class="pn-pd-name">'+s(t("unified-push-all").replace("{n}",g.length))+"</span></div>":"";return h.innerHTML=I+L,h}function R(){const g=document.getElementById("pn-push-dropdown");g&&g.remove()}async function D(){if(document.getElementById("pn-push-dropdown")){R();return}const g=await m()||[],d=i(g),h=x(g,d),I=document.getElementById("pn-push-wrap");I&&I.appendChild(h)}async function w(){const g=await m()||[],d=i(g);if(!d)return;const h=u(),I=h&&(h._historyId||h.history_id);if(I){if(f(h)){o(t("unified-push-disabled-exc"),"warn");return}await v(d,I)}}async function B(g){R();const d=await m()||[],h=u(),I=h&&(h._historyId||h.history_id);if(!I)return;if(f(h)){o(t("unified-push-disabled-exc"),"warn");return}if(g==="__all__"){await E(d,I);return}const L=d.find(H=>H.id===g);L&&(k(g),await v(L,I),q())}async function z(){const g=document.getElementById("drawer-history-save");if(!g||g.querySelector("#pn-push-wrap"))return;const d=document.createElement("div");d.id="pn-push-wrap",d.className="pn-push-wrap",d.dataset.loading="1",g.insertBefore(d,g.firstChild),["btn-push-erp","btn-xero-push"].forEach(M=>{g.querySelectorAll("#"+M).forEach(K=>{K.style.display="none"})});const h=await m()||[],I=i(h),L=h.length>0;if(!L)d.innerHTML='<button type="button" class="btn btn-ghost pn-push-empty" id="btn-push-default" disabled title="'+s(t("unified-push-empty-tip"))+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/></svg><span style="margin-left:4px;">'+s(t("unified-push-empty"))+"</span></button>";else{const M=h.length>1;d.innerHTML='<div class="pn-push-split"><button type="button" class="pn-push-main" id="btn-push-default" title="'+s(t("unified-push-tip"))+'">'+c(I)+"<span>"+s(t("unified-push-to").replace("{name}",I?I.name:""))+"</span></button>"+(M?'<button type="button" class="pn-push-arrow" id="btn-push-arrow" title="'+s(t("unified-push-other"))+'"><svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5l3 3 3-3"/></svg></button>':"")+"</div>"}delete d.dataset.loading;const H=d.querySelector("#btn-push-default");H&&L&&H.addEventListener("click",w);const _=d.querySelector("#btn-push-arrow");_&&_.addEventListener("click",function(M){M.stopPropagation(),D()}),a||(a=!0,document.addEventListener("click",function(M){const K=M.target.closest(".pn-pd-item");if(K){const G=K.getAttribute("data-cid");B(G);return}M.target.closest("#btn-push-arrow")||R()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("unified-push",q))}function q(){const g=document.getElementById("pn-push-wrap");g&&(g.remove(),e=null,n=0,z())}function F(){const g=document.getElementById("drawer-history-save");if(!g||!g.querySelector("#pn-push-wrap"))return;["btn-push-erp","btn-xero-push"].forEach(h=>{g.querySelectorAll("#"+h).forEach(I=>{I.style.display!=="none"&&(I.style.display="none")})});const d=g.querySelectorAll("#pn-push-wrap");if(d.length>1)for(let h=1;h<d.length;h++)d[h].remove()}function A(){try{const g=function(){return document.getElementById("drawer-body")},d=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&z(),F()}),h=g();if(h)d.observe(h,{childList:!0,subtree:!0});else{const I=new MutationObserver(function(){const L=g();L&&(d.observe(L,{childList:!0,subtree:!0}),I.disconnect())});I.observe(document.body,{childList:!0,subtree:!0})}setTimeout(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&z(),F()},200)}catch{}}A()})();(function(){function e(){const a=document.getElementById("erp-map-show-advanced-btn");if(!a)return;const s=document.getElementById("erp-map-subtabs");if(!s)return;const o=s.classList.contains("show-advanced"),m=a.querySelector(".erp-map-adv-btn-label");if(m&&typeof t=="function"){const r=o?"erp-map-hide-advanced":"erp-map-show-advanced",k=t(r);k&&k!==r&&(m.textContent=k)}a.setAttribute("aria-pressed",o?"true":"false")}document.addEventListener("click",function(a){if(!a.target.closest("#erp-map-show-advanced-btn"))return;a.preventDefault();const o=document.getElementById("erp-map-subtabs");if(o&&(o.classList.toggle("show-advanced"),e(),!o.classList.contains("show-advanced")&&o.querySelector(".erp-map-subtab.active.erp-map-subtab-advanced"))){const r=o.querySelector('.erp-map-subtab[data-erp-subtab="clients"]');r&&r.click()}});function n(){e()}typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-map-advanced-toggle",n)})();(function(){const e="pearnly_erp_onboard_shown";let n=!1;function a(){try{return Array.isArray(window._erpEndpoints)&&window._erpEndpoints.length>0}catch{return!1}}function s(){if(document.getElementById("erp-onboard-mask"))return;const m=document.createElement("div");m.id="erp-onboard-mask",m.className="erp-onboard-mask",m.innerHTML='<div class="erp-onboard-modal" role="dialog" aria-modal="true"><div class="erp-onboard-icon"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="6" width="24" height="20" rx="3"/><path d="M9 13h14M9 18h10"/><path d="M22 22l3 3 5-5"/></svg></div><div class="erp-onboard-title" id="erp-onboard-title"></div><div class="erp-onboard-body" id="erp-onboard-body"></div><div class="erp-onboard-btns"><button type="button" class="btn btn-secondary" id="erp-onboard-later"></button><button type="button" class="btn btn-primary" id="erp-onboard-ok"></button></div></div>',document.body.appendChild(m);function r(){const i=document.getElementById("erp-onboard-title"),f=document.getElementById("erp-onboard-body"),u=document.getElementById("erp-onboard-ok"),c=document.getElementById("erp-onboard-later");i&&(i.textContent=t("erp-onboard-title")),f&&(f.textContent=t("erp-onboard-body")),u&&(u.textContent=t("erp-onboard-ok")),c&&(c.textContent=t("erp-onboard-later"))}r();function k(){m.style.display="none"}document.getElementById("erp-onboard-ok").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}k();try{const i=document.querySelector('#btn-add-endpoint, [data-action="erp-add-endpoint"]');i&&i.scrollIntoView({behavior:"smooth",block:"center"})}catch{}}),document.getElementById("erp-onboard-later").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}k()}),m.addEventListener("click",function(i){i.target===m&&k()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-onboard-modal",function(){m.style.display!=="none"&&r()})}function o(){if(!n){try{if(localStorage.getItem(e)==="1")return}catch{}a()||(n=!0,s(),requestAnimationFrame(function(){requestAnimationFrame(function(){if(a())return;const m=document.getElementById("erp-onboard-mask");m&&(m.style.display="flex")})}))}}document.addEventListener("click",function(m){const r=m.target.closest('.auto-nav-item[data-auto-tab="erp"]'),k=m.target.closest('.erp-subtab[data-erp-subtab="connect"]');(r||k)&&setTimeout(o,700)})})();(function(){const e={parse:{zh:"解析文件中",th:"กำลังอ่านไฟล์",en:"Parsing files",ja:"ファイル解析中"},report:{zh:"读取报告中",th:"กำลังอ่านรายงาน",en:"Reading report",ja:"レポート読込中"},reconcile:{zh:"对账中",th:"กำลังกระทบยอด",en:"Reconciling",ja:"照合中"},build:{zh:"生成中",th:"กำลังสร้างไฟล์",en:"Building",ja:"作成中"},persist:{zh:"保存中",th:"กำลังบันทึก",en:"Saving",ja:"保存中"},done:{zh:"完成",th:"เสร็จสิ้น",en:"Done",ja:"完了"}};window._reconProgressText=function(n,a){n=n||{},a=window._currentLang||a||localStorage.getItem("mrpilot_lang")||"th",e.parse[a]||(a="th");const s=n.stage||"parse",o=e[s]||e.parse,m=o[a]||o.th||o.en,r=n.stage_total,k=n.stage_done;if(s==="parse"&&Number.isFinite(r)&&r>0){const i={zh:"共 {d}/{t} 个文件",th:"{d}/{t} ไฟล์",en:"{d}/{t} files",ja:"{d}/{t} ファイル"}[a]||"{d}/{t} files";return m+" · "+i.replace("{d}",k||0).replace("{t}",r)}return m},window._reconPollJob=async function(n,a,s){s=s||{};const o=s.intervalMs||1500,m=s.maxMs||1200*1e3,r=Date.now();let k=0;for(;;){let i=null;try{const f=await fetch("/api/recon/jobs/"+encodeURIComponent(n),{headers:{Authorization:"Bearer "+a}});try{i=await f.json()}catch{i=null}(!f.ok||!i||!i.ok)&&(i=null)}catch{i=null}if(i){if(k=0,s.onProgress)try{s.onProgress(i.progress||{},i)}catch{}if(i.status==="done"||i.status==="failed"||i.status==="needs_review"||i.status==="needs_mapping")return i}else if(++k>=10)return{ok:!1,status:"failed",error_code:"poll_unreachable"};if(Date.now()-r>m)return{ok:!1,status:"timeout",error_code:"timeout"};await new Promise(f=>setTimeout(f,o))}}})();(function(){let e=!1,n=[],a=[],s=null,o="all",m=[],r={stmt:"",gl:""},k=[];const i=b=>document.getElementById(b);function f(b){if(b==null)return"—";const C=Number(b);return isNaN(C)?"—":C.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function u(b){return b?String(b).slice(0,10).split("-").reverse().join("/"):"—"}function c(b){return String(b||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function v(b,C){C=window._currentLang||C||"th";const T={stmt_headers_not_found:{zh:"认不出银行账单表头 · 请确认文件含日期/金额/余额列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตารางบัญชีธนาคารไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/จำนวนเงิน/ยอดคงเหลือ หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect bank statement headers · ensure the file has date/amount/balance columns, or re-upload as a clean Excel/CSV",ja:"銀行明細のヘッダーを認識できません · 日付/金額/残高列を確認するか、Excel/CSVに変換して再アップロードしてください"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含日期/科目/借方/贷方列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตาราง GL ไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต/เครดิต หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect GL headers · ensure the file has date/account/debit/credit columns, or re-upload as a clean Excel/CSV",ja:"GLのヘッダーを認識できません · 日付/科目/借方/貸方列を確認するか、Excel/CSVに変換して再アップロードしてください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水,或换更清晰的版本重传",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง หรือใช้เวอร์ชันที่ชัดเจนกว่า",en:"No transaction rows found · please upload the correct statement, or try a clearer version",ja:"取引データが見つかりません · 正しい明細をアップロードするか、より鮮明なファイルでお試しください"},no_rows:{zh:"解析后没有可对账的数据行 · 请确认文件内容完整,或换清晰版本重传",th:"ไม่มีแถวข้อมูลให้กระทบยอดหลังการอ่าน · ตรวจสอบความสมบูรณ์ของไฟล์ หรืออัปโหลดใหม่",en:"No reconcilable rows after parsing · check the file is complete, or re-upload a clearer version",ja:"解析後に照合可能な行がありません · ファイルの完全性を確認するか再アップロードしてください"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密 · 请换文件或转 PDF/Excel 重传",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส · ลองไฟล์อื่นหรือแปลงเป็น PDF/Excel",en:"File cannot be read · may be corrupted or encrypted · try another file or convert to PDF/Excel",ja:"ファイルを読み取れません · 破損または暗号化の可能性 · 別ファイルまたはPDF/Excelに変換してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロードしてください"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本,或转成 PDF / Excel / CSV 重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น PDF / Excel / CSV",en:"Could not read the file · try a clearer version, or convert to PDF / Excel / CSV",ja:"読み取りに失敗 · より鮮明なファイルか、PDF / Excel / CSV に変換して再試行してください"}},U={zh:"解析失败 · 请换更清晰的文件,或转成 Excel / CSV 后重新上传",th:"อ่านไฟล์ไม่สำเร็จ · ลองไฟล์ที่ชัดเจนกว่า หรือแปลงเป็น Excel / CSV แล้วอัปโหลดใหม่",en:"Parsing failed · try a clearer file, or convert to Excel / CSV and re-upload",ja:"解析に失敗しました · より鮮明なファイルか、Excel / CSV に変換して再アップロードしてください"},N=T[b]||U;return N[C]||N.th||N.en}function E(b){const C=b==="stmt"?n:a,T=i(`brv2-${b}-name`);if(T)if(C.length===0)T.textContent="";else{const N=window._currentLang||"zh",l={zh:"个文件",th:" ไฟล์",en:" file(s)",ja:" ファイル"};T.textContent=C.length+(l[N]||" 个文件")}const U=i("brv2-preview-panel");U&&U.style.display!=="none"&&D(b),x()}function x(){const b=i("brv2-toggle-preview"),C=i("brv2-preview-panel"),T=n.length+a.length>0;b&&(b.style.display=T?"":"none"),!T&&C&&(C.style.display="none",b&&b.classList.remove("open"))}function R(){D("stmt"),D("gl")}function D(b){const C=i(b==="stmt"?"brv2-pp-stmt-col":"brv2-pp-gl-col");if(!C)return;const T=b==="stmt"?n:a,U=window._currentLang||"zh",N={stmt:{zh:"① 银行账单",th:"① บัญชีธนาคาร",en:"① Bank Stmt",ja:"① 銀行明細"},gl:{zh:"② 总账 GL",th:"② GL รายงาน",en:"② GL Report",ja:"② GL帳簿"}},l=(N[b]||{})[U]||N[b].zh,j=c(window.t&&window.t("vex-preview-search")||"搜索文件名..."),O=c(window.t&&window.t("vex-preview-clear-all")||"全清"),J=r[b]||"";C.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+c(l)+' <span class="vex-pp-col-count">'+T.length+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="brv2-pp-search-'+b+'" type="text" placeholder="'+j+'" value="'+c(J)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="brv2-pp-clearall-'+b+'" type="button">'+O+'</button></div><div class="vex-pp-file-list" id="brv2-pp-'+b+'-list"></div><div class="vex-pp-pagination" id="brv2-pp-'+b+'-pg"></div>';const X=i("brv2-pp-search-"+b);X&&X.addEventListener("input",function(oe){r[b]=oe.target.value,w(b)});const de=i("brv2-pp-clearall-"+b);de&&de.addEventListener("click",function(){b==="stmt"?n.length=0:a.length=0,E(b),M()}),w(b)}function w(b){const C=i("brv2-pp-"+b+"-list"),T=i("brv2-pp-"+b+"-pg");if(!C)return;const U=b==="stmt"?n:a,N=(r[b]||"").toLowerCase(),l=N?U.filter(J=>J.name.toLowerCase().includes(N)):U.slice(),j='<svg class="vex-pp-fi-ico" viewBox="0 0 14 16" fill="none" stroke="currentColor" stroke-width="1.4" width="12" height="14"><path d="M3 1h6l3 3v11H3V1z"/><path d="M9 1v3h3"/></svg>',O='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" width="11" height="11"><path d="M2 4h10M5 4V2h4v2M5.5 7v4M8.5 7v4M3 4l1 8h6l1-8"/></svg>';if(C.innerHTML=l.map((J,X)=>'<div class="vex-pp-file-row">'+j+'<span class="vex-pp-fi-name" title="'+c(J.name)+'">'+c(J.name)+'</span><span class="vex-pp-fi-size">'+B(J.size)+'</span><button class="vex-pp-fi-del" type="button" data-zone="'+b+'" data-idx="'+U.indexOf(J)+'" aria-label="remove">'+O+"</button></div>").join(""),C.querySelectorAll(".vex-pp-fi-del").forEach(function(J){J.addEventListener("click",function(){const X=parseInt(J.dataset.idx,10);J.dataset.zone==="stmt"?n.splice(X,1):a.splice(X,1),E(J.dataset.zone),M()})}),T){const J=window.t&&window.t("vex-preview-count")||"显示 {n} / 共 {m}";T.textContent=J.replace("{n}",l.length).replace("{m}",U.length)}}function B(b){return b?b<1024?b+" B":b<1048576?(b/1024).toFixed(1)+" KB":(b/1048576).toFixed(1)+" MB":""}var z="pearnly.brv2.lastAnchorOcr";function q(b){try{var C=b&&b._anchor_ocr;if(!C||typeof C!="object")return;var T={stmt_opening:Number.isFinite(+C.stmt_opening)?+C.stmt_opening:null,gl_opening:Number.isFinite(+C.gl_opening)?+C.gl_opening:null,gl_closing:Number.isFinite(+C.gl_closing)?+C.gl_closing:null,stmt_closing:Number.isFinite(+C.stmt_closing)?+C.stmt_closing:null,ts:Date.now()};localStorage.setItem(z,JSON.stringify(T))}catch{}}function F(){try{var b=localStorage.getItem(z);if(!b)return null;var C=JSON.parse(b);return!C||typeof C!="object"?null:C}catch{return null}}function A(){var b=F();if(b){var C={"brv2-anchor-stmt-opening":b.stmt_opening,"brv2-anchor-gl-opening":b.gl_opening,"brv2-anchor-gl-closing":b.gl_closing,"brv2-anchor-stmt-closing":b.stmt_closing},T=0;Object.keys(C).forEach(function(O){var J=document.getElementById(O);if(J&&J.value===""){var X=C[O];if(Number.isFinite(X)){J.value=X.toFixed(2);var de=J.closest&&J.closest(".brv2-anchor-cell");de&&de.classList.add("is-prefilled"),T+=1}}});var U=document.getElementById("brv2-anchor-eq"),N=document.getElementById("brv2-anchor-eq-val");if(U&&N&&Number.isFinite(b.stmt_opening)&&Number.isFinite(b.gl_opening)){var l=b.stmt_opening-b.gl_opening;N.textContent=l.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),U.style.display=""}if(T>0){var j=document.getElementById("brv2-anchor-prefill-banner");j&&j.classList.add("show")}}}function g(){var b=document.getElementById("brv2-anchor-prefill-banner");if(b){var C=!1;["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"].forEach(function(T){var U=document.getElementById(T);if(U){var N=U.closest&&U.closest(".brv2-anchor-cell");N&&N.classList.contains("is-prefilled")&&(C=!0)}}),b.classList.toggle("show",C)}}var d=[["stmt_opening","brv2-anchor-stmt-opening"],["gl_opening","brv2-anchor-gl-opening"],["gl_closing","brv2-anchor-gl-closing"],["stmt_closing","brv2-anchor-stmt-closing"]];function h(b,C){return window.t&&window.t(b)||C}function I(b){return String(b??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function L(b){return Number.isFinite(+b)?(+b).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—"}function H(b){var C=document.getElementById("brv2-summary-collapse");if(!(!C||!C.parentNode)){var T=document.getElementById("brv2-anchor-audit"),U=b&&b._anchor_overrides;if(!U||typeof U!="object"||Object.keys(U).length===0){T&&T.parentNode&&T.parentNode.removeChild(T);return}T||(T=document.createElement("div"),T.id="brv2-anchor-audit",T.style.cssText="margin-top:14px;background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:14px 16px;",C.parentNode.insertBefore(T,C.nextSibling));var N=d.map(function(l){var j=U[l[0]];if(!j)return"";var O=+j.ocr||0,J=+j.user||0,X=J-O,de=X>0?"+":(X<0,""),oe=Math.abs(X)<.005?"#6b7280":X>0?"#16a34a":"#dc2626";return'<tr><td style="padding:6px 10px;color:#111827;font-size:13px">'+I(h(l[1],l[0]))+'</td><td style="padding:6px 10px;color:#6b7280;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+I(L(O))+'</td><td style="padding:6px 10px;background:#fef08a;color:#92400e;font-weight:600;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+I(L(J))+'</td><td style="padding:6px 10px;color:'+oe+';font-weight:500;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+I(de+L(X))+"</td></tr>"}).join("");T.innerHTML='<div style="font-weight:600;color:#92400e;font-size:13px;margin-bottom:10px">'+I(h("brv2-anchor-audit-title","⚠ This run contains manually entered anchors"))+'</div><table style="width:100%;border-collapse:collapse;font-family:inherit"><thead><tr><th style="padding:6px 10px;text-align:left;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+I(h("brv2-anchor-audit-col-field","Field"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+I(h("brv2-anchor-audit-col-ocr","OCR"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+I(h("brv2-anchor-audit-col-user","User"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+I(h("brv2-anchor-audit-col-diff","Diff"))+"</th></tr></thead><tbody>"+N+"</tbody></table>"}}function _(){const b=i("brv2-toggle-preview");b&&!b._reconBound&&(b._reconBound=!0,b.addEventListener("click",function(){const C=i("brv2-preview-panel"),T=i("brv2-toggle-preview-label"),U=C&&C.style.display!=="none";C&&(C.style.display=U?"none":""),b.classList.toggle("open",!U),T&&(T.textContent=U?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),U||R()}))}function M(){const b=i("brv2-run-btn"),C=i("brv2-status"),T=n.length>0,U=a.length>0;if(b&&(b.disabled=!(T&&U)),C){const N=window._currentLang||"zh";if(!T&&!U){const l={zh:"请上传银行账单和 GL 文件",th:"กรุณาอัปโหลดบัญชีธนาคารและ GL",en:"Upload bank statement and GL files",ja:"銀行明細と GL を両方アップロードしてください"};C.textContent=l[N]||l.zh}else if(T)if(U){const l={zh:"两份文件已就绪",th:"พร้อมสอบทาน",en:"Ready to reconcile",ja:"照合を開始できます"};C.textContent=l[N]||l.zh}else{const l={zh:"还缺 GL 文件",th:"ยังขาดไฟล์ GL",en:"Missing GL file",ja:"GL ファイルが未アップロード"};C.textContent=l[N]||l.zh}else{const l={zh:"还缺银行账单 PDF",th:"ยังขาดไฟล์บัญชีธนาคาร PDF",en:"Missing bank statement PDF",ja:"銀行明細 PDF が未アップロード"};C.textContent=l[N]||l.zh}}}function K(b,C,T){const U=i(b),N=i(C);!U||!N||(U.addEventListener("click",()=>N.click()),U.addEventListener("keydown",l=>{(l.key==="Enter"||l.key===" ")&&(l.preventDefault(),N.click())}),U.addEventListener("dragover",l=>{l.preventDefault(),U.classList.add("drag-over")}),U.addEventListener("dragleave",()=>U.classList.remove("drag-over")),U.addEventListener("drop",l=>{l.preventDefault(),U.classList.remove("drag-over");const j=Array.from(l.dataTransfer.files||[]);T==="stmt"?n.push(...j):a.push(...j),E(T),M()}),N.addEventListener("change",()=>{const l=Array.from(N.files||[]);T==="stmt"?n.push(...l):a.push(...l),N.value="",E(T),M()}))}function G(b){const C=i("brv2-progress"),T=i("brv2-run-btn"),U=i("brv2-error");C&&(C.style.display=b?"":"none"),T&&(T.disabled=b),U&&(U.style.display="none")}function W(b){const C=i("brv2-error");C&&(C.textContent=b,C.style.display="",C.scrollIntoView({behavior:"smooth",block:"nearest"})),G(!1),M(),window.showToast&&window.showToast(b,"error")}async function te(){if(n.length===0||a.length===0)return;const b=localStorage.getItem("mrpilot_token")||"",C=window._currentLang||"zh",T=(i("brv2-acct-select")||{}).value||"";S(!1),G(!0);try{const U=new FormData;n.forEach(ae=>U.append("stmt_files",ae)),a.forEach(ae=>U.append("gl_files",ae)),U.append("gl_account",T),U.append("lang",C);const N=parseFloat((i("brv2-anchor-gl-closing")||{}).value),l=parseFloat((i("brv2-anchor-stmt-closing")||{}).value),j=parseFloat((i("brv2-anchor-stmt-opening")||{}).value),O=parseFloat((i("brv2-anchor-gl-opening")||{}).value);Number.isFinite(N)&&U.append("gl_closing_override",N),Number.isFinite(l)&&U.append("stmt_closing_override",l),Number.isFinite(j)&&U.append("stmt_opening_override",j),Number.isFinite(O)&&U.append("gl_opening_override",O);const J=await fetch("/api/recon/bank-v2/submit",{method:"POST",headers:{Authorization:"Bearer "+b},body:U});let X=null;try{X=await J.json()}catch{X=null}if(X&&X.needs_mapping){G(!1),window.ReconMapping?window.ReconMapping.show(X,{token:b,lang:C,onConfirmed:function(){te()}}):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(!J.ok||!X||!X.ok||!X.job_id){G(!1),X&&(X.detail||X.error)?W(_humanizeBackendError(X.detail||X.error,"Error "+J.status)):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const de=i("brv2-progress-sub"),oe=await window._reconPollJob(X.job_id,b,{onProgress:ae=>{de&&(de.textContent=window._reconProgressText(ae,C))}});if(oe&&oe.status==="needs_mapping"&&oe.mapping){G(!1),window.ReconMapping?window.ReconMapping.show(oe.mapping,{token:b,lang:C,onConfirmed:function(){te()}}):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(oe&&oe.status==="needs_review"&&oe.review){G(!1),window.ReconReview?window.ReconReview.show(oe.review,{token:b,lang:C,jobId:X.job_id,onConfirmed:async function(ae){G(!0);const pe=await window._reconPollJob(ae,b,{onProgress:ve=>{de&&(de.textContent=window._reconProgressText(ve,C))}});await ce(pe)}}):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(oe&&oe.status==="failed"){G(!1),W(v(oe.error_code,C));return}await ce(oe);async function ce(ae){try{if(!ae||ae.status!=="done"||!ae.result_id){G(!1),W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const pe=await fetch("/api/recon/bank-v2/"+encodeURIComponent(ae.result_id),{headers:{Authorization:"Bearer "+b}});let ve=null;try{ve=await pe.json()}catch{ve=null}if(!pe.ok||ve===null||!ve.ok){G(!1),W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}(ve.gl_accounts||[]).length>1&&re(ve.gl_accounts),s=ve,m=ve.detail||[],o="all",document.querySelectorAll(".brv2-filter-btn").forEach(ge=>ge.classList.toggle("active",ge.dataset.filter==="all")),q(ve&&ve.summary),G(!1),P(ve),Z();const fe=i("brv2-summary-collapse");fe&&fe.scrollIntoView({behavior:"smooth",block:"nearest"})}catch(pe){G(!1),W(pe.message||"Network error")}}}catch(U){W(U.message||"Network error")}}function re(b){const C=i("brv2-acct-select");if(!C)return;const T=window._currentLang||"zh",U={zh:"全部账户",th:"ทุกบัญชี",en:"All Accounts",ja:"すべての口座"}[T]||"全部账户";C.innerHTML=`<option value="">${U}</option>`+b.map(N=>`<option value="${c(N)}">${c(N)}</option>`).join(""),C.style.display=""}function S(b){const C=i("brv2-summary-collapse"),T=i("brv2-detail-collapse"),U=i("brv2-export-btn"),N=i("brv2-new-btn"),l=i("brv2-parse-info-wrap");C&&(C.style.display=b?"":"none"),T&&(T.style.display=b?"":"none"),U&&(U.style.display=b?"":"none"),N&&(N.style.display=b?"":"none"),!b&&l&&(l.style.display="none");const j=i("brv2-warnings");!b&&j&&(j.style.display="none",j.innerHTML="")}function y(b){const C=i("brv2-parse-info-wrap"),T=i("brv2-parse-info-body");if(!C||!T)return;const U=b.parse_info;if(!U){C.style.display="none";return}const N=window._currentLang||"zh",l={title:{zh:"文件解析状态",th:"สถานะการอ่านไฟล์",en:"File Parse Status",ja:"ファイル解析状態"},type:{zh:"类型",th:"ประเภท",en:"Type",ja:"種別"},file:{zh:"文件名",th:"ชื่อไฟล์",en:"File",ja:"ファイル"},rows:{zh:"解析行数",th:"แถวที่พบ",en:"Rows Found",ja:"解析行数"},bank:{zh:"银行/科目",th:"ธนาคาร/บัญชี",en:"Bank/Account",ja:"銀行/科目"},status:{zh:"状态",th:"สถานะ",en:"Status",ja:"状態"},stmt:{zh:"账单",th:"บัญชีธนาคาร",en:"Stmt",ja:"明細"},gl:{zh:"总账GL",th:"GL",en:"GL",ja:"GL"},ok:{zh:"✓ 成功",th:"✓ สำเร็จ",en:"✓ OK",ja:"✓ 成功"},warn:{zh:"⚠ 0行",th:"⚠ 0 แถว",en:"⚠ 0 rows",ja:"⚠ 0行"},fail:{zh:"✗ 失败",th:"✗ ล้มเหลว",en:"✗ Failed",ja:"✗ 失敗"}},j=ce=>(l[ce]||{})[N]||(l[ce]||{}).zh||ce,O=[...(U.stmt_files||[]).map(ce=>({...ce,_type:"stmt",_extra:ce.bank_code||""})),...(U.gl_files||[]).map(ce=>({...ce,_type:"gl",_extra:(ce.accounts||[]).join(", ")}))],J={stmt_headers_not_found:{zh:"认不出表头列 · 请确认文件含日期/金额/余额列",th:"หาคอลัมน์หัวตารางไม่เจอ · ตรวจสอบไฟล์มีวันที่/จำนวนเงิน/ยอดคงเหลือ",en:"Cannot detect column headers · ensure file has date/amount/balance columns",ja:"列ヘッダーが認識できません · 日付/金額/残高列を確認してください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง",en:"No transaction rows found · please check the file",ja:"取引データが見つかりません · ファイルを確認してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロード"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส",en:"File cannot be read · may be corrupted or encrypted",ja:"ファイルを読み取れません · 破損または暗号化の可能性"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本或换 PDF 格式重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่าหรือเปลี่ยนเป็น PDF",en:"Could not read file · try a clearer version or upload as PDF",ja:"読み取り失敗 · より鮮明なファイルまたは PDF 形式で再試行"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含科目/借方/贷方列",th:"หาหัวคอลัมน์ GL ไม่เจอ · ตรวจสอบมีคอลัมน์บัญชี/เดบิต/เครดิต",en:"Cannot detect GL column headers · ensure account/debit/credit columns exist",ja:"GL 列ヘッダー認識不可 · 科目/借方/貸方列を確認してください"}},X=ce=>{const ae=String(ce||"");return/Cannot detect bank statement column headers/i.test(ae)?"stmt_headers_not_found":/Cannot detect GL column headers/i.test(ae)?"gl_headers_not_found":/No transaction rows found|no pages parsed/i.test(ae)?"stmt_no_rows":/unsupported format/i.test(ae)?"file_not_supported":/Cannot read Excel|file_unreadable/i.test(ae)?"file_unreadable":/Gemini.*invalid JSON|Gemini.*parsed but failed|validation errors|BankStatementDocument schema|layer2:|layer1:/i.test(ae)?"ocr_failed":null},de=ce=>{const ae=ce.error_code||X(ce.error);if(ae&&J[ae]){const pe=window._currentLang||"zh";return J[ae][pe]||J[ae].zh}return String(ce.error||"").slice(0,80)},oe=ce=>!ce.ok&&ce.error?`<span style="color:#dc2626">${j("fail")} — ${c(de(ce))}</span>`:ce.rows?`<span style="color:#059669">${j("ok")} (${ce.rows})</span>`:`<span style="color:#d97706">${j("warn")}</span>`;T.innerHTML=`
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
                    ${O.map(ce=>`<tr>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;white-space:nowrap">${ce._type==="stmt"?j("stmt"):j("gl")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${c(ce.file||"")}">${c(ce.file||"")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;text-align:center">${ce.rows||0}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;color:var(--ink-2)">${c(ce._extra||"")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb">${oe(ce)}</td>
                    </tr>`).join("")}
                </tbody>
            </table>`,C.style.display=""}async function p(b){const C=localStorage.getItem("mrpilot_token")||"",T=window._currentLang||"zh";try{const U=await fetch("/api/recon/bank-v2/"+b+"/export?lang="+T,{headers:{Authorization:"Bearer "+C}});if(!U.ok){const de=await U.json().catch(()=>({}));window.showToast&&window.showToast(de.detail||"Export failed","error");return}const N=await U.blob(),j=(U.headers.get("content-disposition")||"").match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/),O=j?j[1].replace(/['"]/g,""):"reconciliation.xlsx",J=URL.createObjectURL(N),X=document.createElement("a");X.href=J,X.download=O,document.body.appendChild(X),X.click(),document.body.removeChild(X),URL.revokeObjectURL(J)}catch(U){window.showToast&&window.showToast("Export error: "+U.message,"error")}}function $(b,C){const T=i("brv2-summary-collapse");let U=i("brv2-warnings");const N=window._currentLang||"zh",l={zh:"⏭ 已跳过无法识别的文件:",th:"⏭ ข้ามไฟล์ที่อ่านไม่ได้:",en:"⏭ Skipped unreadable file:",ja:"⏭ 読み取れないファイルをスキップ:"}[N]||"⏭ ",j=[];if((C||[]).forEach(O=>j.push(l+" "+O)),(b||[]).forEach(O=>j.push(O)),!j.length){U&&(U.style.display="none");return}if(!U)if(U=document.createElement("div"),U.id="brv2-warnings",T&&T.parentNode)T.parentNode.insertBefore(U,T);else return;U.style.cssText="display:block;margin:10px 0;padding:10px 14px;background:#FEF3C7;border:1px solid #FCD34D;border-radius:8px;color:#92400E;font-size:13px;line-height:1.6",U.innerHTML=j.map(O=>"<div>"+c(O)+"</div>").join("")}function P(b){y(b),$(b.warnings||[],b.skipped_files||[]),!b.ok&&b.error&&window.showToast&&window.showToast(b.error,"error");const C=b.stats||{},T=b.summary||{},U=C.matched||0,N=(C.gl_debit_only||0)+(C.gl_credit_only||0),l=(C.stmt_withdrawal_only||0)+(C.stmt_deposit_only||0),j=Number(T.formula_diff||0),O=Math.abs(j)<.05;i("brv2-kpi-matched")&&(i("brv2-kpi-matched").textContent=U),i("brv2-kpi-diff")&&(i("brv2-kpi-diff").textContent=f(j)),i("brv2-kpi-unmatched")&&(i("brv2-kpi-unmatched").textContent=N+l);const J=i("brv2-kpi-diff-icon");J&&(J.style.background=O?"#d1fae5":"#fee2e2",J.style.color=O?"#065f46":"#b91c1c");const X=i("brv2-formula-sub");if(X){const pe=window._currentLang||"zh";X.textContent=O?{zh:"✓ 平衡",th:"✓ สมดุล",en:"✓ Balanced",ja:"✓ 一致"}[pe]||"✓ 平衡":({zh:"差 ",th:"ต่าง ",en:"Diff ",ja:"差 "}[pe]||"差 ")+f(j)}const de=i("brv2-detail-sub");if(de){const pe=window._currentLang||"zh",ve={zh:"共 {n} 行",th:"ทั้งหมด {n} แถว",en:"{n} rows",ja:"計 {n} 行"}[pe]||"共 {n} 行";de.textContent=ve.replace("{n}",m.length)}function oe(pe,ve,fe){const ge=i(pe);ge&&(ge.textContent=(fe&&ve>0?"(":"")+f(fe?-ve:ve)+(fe&&ve>0?")":""))}oe("brf-gl-close",T.gl_closing||0),oe("brf-open-diff",T.opening_diff||0),oe("brf-gl-debit-only",T.gl_debit_only_amount||0,!0),oe("brf-gl-credit-only",T.gl_credit_only_amount||0),oe("brf-stmt-wd-only",T.stmt_withdrawal_only_amount||0,!0),oe("brf-stmt-dep-only",T.stmt_deposit_only_amount||0),oe("brf-calc-close",T.formula_stmt_closing||0),oe("brf-stmt-close",T.stmt_closing||0),i("brf-diff")&&(i("brf-diff").textContent=f(j));const ce=i("brv2-fcell-diff");ce&&ce.classList.toggle("brv2-fcell-diff-ok",O);const ae=i("brv2-export-btn");ae&&(ae.onclick=()=>{s&&p(s.task_id)}),H(T),S(!0),Y()}function Y(){const b=i("brv2-tbody");if(!b)return;const C=m.filter(l=>o==="all"?!0:o==="matched"?l.match_status==="matched":o==="gl_only"?l.match_status.startsWith("gl_"):o==="stmt_only"?l.match_status.startsWith("stmt_"):!0);if(C.length===0){const l={zh:"无记录",th:"ไม่มีรายการ",en:"No rows",ja:"行なし"}[window._currentLang||"zh"]||"无记录";b.innerHTML=`<tr><td colspan="10" style="text-align:center;padding:20px;color:var(--ink-3)">${l}</td></tr>`;return}const T=window._currentLang||"zh",U={zh:"OCR 余额验证未通过 · 上一行余额 ± 金额 ≠ 本行余额，请核对原 PDF",th:"การตรวจสอบยอดคงเหลือไม่ผ่าน · ยอดก่อนหน้า ± จำนวน ≠ ยอดบรรทัดนี้ โปรดตรวจสอบ PDF ต้นฉบับ",en:"Balance check FAILED · prev_balance ± amount ≠ this row balance — verify against the original PDF",ja:"残高検証エラー · 前残高 ± 金額 ≠ この行残高 — 元のPDFと照合してください"}[T],N={zh:"OCR 低置信度 · 数字模糊或难以辨认，请核对原 PDF",th:"OCR ความมั่นใจต่ำ · ตัวเลขเบลอหรืออ่านยาก โปรดตรวจสอบ PDF ต้นฉบับ",en:"OCR low confidence · digit was blurry or hard to read — verify against the original PDF",ja:"OCR信頼度低 · 数字がぼやけている — 元のPDFと照合してください"}[T];b.innerHTML=C.map(l=>{const j=l.match_status,O=l.match_layer;let J="",X="";j==="matched"?(O===1&&(J="matched",X='<span class="brv2-status-badge brv2-badge-matched">L1 ✓</span>'),O===2&&(J="matched-l2",X='<span class="brv2-status-badge brv2-badge-matched-l2">L2 ~</span>'),O===3&&(J="matched-l3",X='<span class="brv2-status-badge brv2-badge-matched-l3">L3 ?</span>')):j==="gl_debit_only"||j==="gl_credit_only"?(J="gl-only",X='<span class="brv2-status-badge brv2-badge-gl-only">GL</span>'):(J="stmt-only",X=`<span class="brv2-status-badge brv2-badge-stmt-only">${{zh:"账单",th:"บัญชี",en:"Stmt",ja:"明細"}[T]||"账单"}</span>`);let de="";return l.stmt_balance_ok===!1&&(de+=`<span class="brv2-ocr-warn brv2-ocr-warn-bal" title="${c(U)}">⚠</span>`,J+=" brv2-row-warn"),l.stmt_confidence==="low"&&(de+=`<span class="brv2-ocr-warn brv2-ocr-warn-conf" title="${c(N)}">◌</span>`,J.includes("brv2-row-warn")||(J+=" brv2-row-warn-soft")),`<tr class="${J.trim()}">
              <td>${X}${de}</td>
              <td>${c(u(l.stmt_date))}</td>
              <td title="${c(l.stmt_desc)}" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${c(l.stmt_desc)}</td>
              <td class="num">${l.stmt_withdrawal?f(l.stmt_withdrawal):""}</td>
              <td class="num">${l.stmt_deposit?f(l.stmt_deposit):""}</td>
              <td>${c(u(l.gl_date))}</td>
              <td title="${c(l.gl_doc_no)}" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${c(l.gl_doc_no)}</td>
              <td class="num">${l.gl_debit?f(l.gl_debit):""}</td>
              <td class="num">${l.gl_credit?f(l.gl_credit):""}</td>
              <td>${O?"L"+O:"—"}</td>
            </tr>`}).join("")}async function Z(){const b=localStorage.getItem("mrpilot_token")||"";try{const T=await(await fetch("/api/recon/bank-v2/tasks",{headers:{Authorization:"Bearer "+b}})).json();ee(T.tasks||[])}catch{const T=i("brv2-history-empty"),U=window._currentLang||"zh",N={zh:"加载失败",th:"โหลดประวัติไม่ได้",en:"Load failed",ja:"読み込み失敗"}[U]||"加载失败";T&&(T.textContent=N,T.style.display="");const l=i("brv2-history-table-wrap");l&&(l.style.display="none")}}const le=10;let ie=1;function V(){const b=i("brv2-history-pager"),C=i("brv2-history-pager-info"),T=i("brv2-history-prev"),U=i("brv2-history-next");if(!b)return;if(k.length<=le){b.style.display="none";return}b.style.display="";const N=Math.ceil(k.length/le);C&&(C.textContent=ie+" / "+N),T&&(T.disabled=ie<=1),U&&(U.disabled=ie>=N)}function Q(){const b=i("brv2-history-prev"),C=i("brv2-history-next");b&&!b._brv2Bound&&(b._brv2Bound=!0,b.addEventListener("click",()=>{ie>1&&(ie--,ee(k))})),C&&!C._brv2Bound&&(C._brv2Bound=!0,C.addEventListener("click",()=>{const T=Math.ceil(k.length/le);ie<T&&(ie++,ee(k))}))}function ee(b){b!==void 0&&(k=b||[],ie=1);const C=k,T=i("brv2-history-empty"),U=i("brv2-history-table-wrap"),N=i("brv2-history-tbody");if(!N)return;const l=window._currentLang||"zh";if(!C.length){const ae={zh:"暂无对账记录",th:"ยังไม่มีประวัติ",en:"No records yet",ja:"記録なし"}[l]||"暂无对账记录";T&&(T.textContent=ae,T.style.display=""),U&&(U.style.display="none"),V();return}T&&(T.style.display="none"),U&&(U.style.display="");const j=Math.ceil(C.length/le);ie>j&&(ie=j);const O=(ie-1)*le,J=C.slice(O,O+le),X=localStorage.getItem("mrpilot_token")||"",de='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><circle cx="8" cy="8" r="6"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',oe='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',ce='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';N.innerHTML="",J.forEach(ae=>{const pe=Number(ae.formula_diff||0),ve=Math.abs(pe)<.05,fe=(ae.stmt_files||"").split(";").map(ke=>ke.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),ge=(ae.gl_files||"").split(";").map(ke=>ke.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),be=ae.created_at?String(ae.created_at).slice(0,16).replace("T"," "):"",xe=document.createElement("tr");xe.dataset.taskId=ae.id;const De=document.createElement("td");De.textContent=be;const Le=document.createElement("td");Le.className="glv-history-file",Le.title=fe+" + "+ge,Le.textContent=fe+" + "+ge;const Ce=document.createElement("td");Ce.className="glv-num",Ce.textContent=(ae.stmt_row_count||0)+" / "+(ae.gl_row_count||0);const Ve=document.createElement("td");Ve.className="glv-num",Ve.textContent=ae.matched_count||0;const Ue=document.createElement("td");Ue.className="glv-num",Ue.textContent=ae.unmatched_gl||0;const Ge=document.createElement("td");Ge.className="glv-num",Ge.textContent=ae.unmatched_stmt||0;const qe=document.createElement("td");qe.className="glv-num",qe.style.color=ve?"#059669":"#dc2626",qe.textContent=ve?"✓":f(pe);const Se=document.createElement("td");Se.className="glv-history-actions";const Ye=(ke,Qe,et,It)=>{const Ee=document.createElement("button");return Ee.type="button",Ee.title=Qe,Ee.setAttribute("aria-label",Qe),et&&(Ee.className=et),Ee.innerHTML=ke,Ee.onclick=Lt=>{Lt.stopPropagation(),It()},Ee},xt={zh:"删除这条记录?",th:"ลบรายการนี้?",en:"Delete this record?",ja:"この記録を削除しますか?"}[l]||"删除?",_t={zh:"加载",th:"โหลด",en:"Load",ja:"読込"}[l]||"加载",Et={zh:"导出",th:"ส่งออก",en:"Export",ja:"エクスポート"}[l]||"导出",Bt={zh:"删除",th:"ลบ",en:"Delete",ja:"削除"}[l]||"删除";Se.appendChild(Ye(de,_t,"",()=>se(ae.id,X))),Se.appendChild(Ye(oe,Et,"",()=>p(ae.id))),Se.appendChild(Ye(ce,Bt,"glv-del",async()=>{await showConfirm(xt,{danger:!0})&&(await fetch("/api/recon/bank-v2/"+ae.id,{method:"DELETE",headers:{Authorization:"Bearer "+X}}),Z())})),[De,Le,Ce,Ve,Ue,Ge,qe,Se].forEach(ke=>xe.appendChild(ke)),xe.style.cursor="pointer",xe.addEventListener("click",async ke=>{ke.target.closest(".glv-del")||ke.target.closest("button")||await se(ae.id,X)}),N.appendChild(xe)}),V(),ne()}function ne(){const b=((i("brv2-hist-search")||{}).value||"").trim().toLowerCase(),C=i("brv2-history-tbody");C&&C.querySelectorAll("tr").forEach(T=>{T.dataset.taskId&&(T.style.display=!b||T.textContent.toLowerCase().includes(b)?"":"none")})}async function se(b,C){try{const U=await(await fetch("/api/recon/bank-v2/"+b,{headers:{Authorization:"Bearer "+C}})).json();if(!U.ok)return;s={task_id:U.task_id,...U},m=U.detail||[],o="all",document.querySelectorAll(".brv2-filter-btn").forEach(N=>N.classList.toggle("active",N.dataset.filter==="all")),P(s)}catch{}}function ue(){if(e){Z();return}e=!0,K("brv2-stmt-zone","brv2-stmt-input","stmt"),K("brv2-gl-zone","brv2-gl-input","gl");const b=["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"];function C(){const O=parseFloat((i("brv2-anchor-stmt-opening")||{}).value),J=parseFloat((i("brv2-anchor-gl-opening")||{}).value),X=i("brv2-anchor-eq"),de=i("brv2-anchor-eq-val");if(!(!X||!de))if(Number.isFinite(O)&&Number.isFinite(J)){const oe=O-J;de.textContent=oe.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),X.style.display=""}else X.style.display="none"}b.forEach(O=>{const J=i(O);J&&(J.addEventListener("input",C),J.addEventListener("input",()=>{const X=J.closest(".brv2-anchor-cell");X&&X.classList.remove("is-prefilled"),g()}))}),A();const T=i("brv2-run-btn");T&&T.addEventListener("click",te);const U=i("brv2-reset-btn");U&&U.addEventListener("click",()=>{s=null,m=[],n=[],a=[],E("stmt"),E("gl"),M(),S(!1);const O=i("brv2-acct-select");O&&(O.style.display="none"),b.forEach(de=>{const oe=i(de);if(oe){oe.value="";const ce=oe.closest&&oe.closest(".brv2-anchor-cell");ce&&ce.classList.remove("is-prefilled")}});const J=i("brv2-anchor-eq");J&&(J.style.display="none");const X=i("brv2-anchor-prefill-banner");X&&X.classList.remove("show")});const N=i("brv2-new-btn");N&&N.addEventListener("click",()=>{s=null,m=[],n=[],a=[],E("stmt"),E("gl"),M(),S(!1)});const l=i("brv2-filter-tabs");l&&l.addEventListener("click",O=>{O.stopPropagation();const J=O.target.closest(".brv2-filter-btn");J&&(o=J.dataset.filter,l.querySelectorAll(".brv2-filter-btn").forEach(X=>X.classList.toggle("active",X===J)),Y())}),_(),Q();const j=i("brv2-hist-search");j&&j.addEventListener("input",ne),Z(),M(),window._brv2LoadHistory=Z,Array.isArray(window.__i18nSubs)||(window.__i18nSubs=[]),window.__i18nSubs=window.__i18nSubs.filter(O=>O.name!=="brv2"),window.__i18nSubs.push({name:"brv2",fn:function(){M(),E("stmt"),E("gl"),s&&P(s),ee()}})}window._loadBankReconV2Panel=function(b){const C=b?document.getElementById(b):null;C&&C.id!=="recon-pane-bank"&&(C.innerHTML=`<div style="padding:16px;font-size:13px;color:var(--ink-3)">
                银行对账 v2 · 请前往对账中心使用</div>`),ue()},document.addEventListener("DOMContentLoaded",()=>{i("brv2-run-btn")&&ue()}),window._bankReconV2Init=ue})();(function(){const e=document.getElementById("general-lang");if(!e)return;e.addEventListener("change",a=>{const s=a.target.value;s&&applyLang(s)});const n=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";e.value=n})();(function(){const n="pearnly_general_tz",a="pearnly_general_date_format",s="pearnly_general_number_format",o={tz:"Asia/Bangkok",date:"YYYY-MM-DD",number:"comma_dot"};function m(){const f=document.getElementById("general-tz"),u=document.getElementById("general-date"),c=document.getElementById("general-number");if(!(!f||!u||!c))try{f.value=localStorage.getItem(n)||o.tz,u.value=localStorage.getItem(a)||o.date,c.value=localStorage.getItem(s)||o.number}catch{f.value=o.tz,u.value=o.date,c.value=o.number}}async function r(){const f=document.getElementById("btn-save-general"),u=document.getElementById("general-save-msg");if(!f)return;const c=f.innerHTML;f.disabled=!0,f.innerHTML="<span>"+(t("msg-saving")||"保存中...")+"</span>",u&&(u.textContent="",u.classList.remove("error"));try{const v=(document.getElementById("general-tz")||{}).value||o.tz,E=(document.getElementById("general-date")||{}).value||o.date,x=(document.getElementById("general-number")||{}).value||o.number;try{localStorage.setItem(n,v),localStorage.setItem(a,E),localStorage.setItem(s,x)}catch{}window._pearnlyGeneral={tz:v,date_format:E,number_format:x},u&&(u.textContent=t("msg-saved")||"已保存")}catch{u&&(u.textContent=t("msg-save-failed")||"保存失败",u.classList.add("error"))}finally{f.disabled=!1,f.innerHTML=c,setTimeout(function(){u&&(u.textContent="")},3e3)}}function k(){const f=document.getElementById("btn-save-general");if(!f){setTimeout(k,200);return}f._pearnlyGenBound||(f._pearnlyGenBound=!0,f.addEventListener("click",r),m())}function i(){m();const f=document.getElementById("general-lang");if(f){const u=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";f.value=u}}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",k):k(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("settings-general",i)})();(function(){const e="mrpilot_nav_collapsed",n={ocr:"sales",history:"sales",reconcile:"sales","sales-invoices":"sales",receivables:"sales",vouchers:"expense"};function a(){try{const r=localStorage.getItem(e);return r?JSON.parse(r):{}}catch{return{}}}function s(r){try{localStorage.setItem(e,JSON.stringify(r))}catch{}}function o(){const r=a();document.querySelectorAll(".nav-collapsible").forEach(function(k){const i=k.dataset.collapsible;r[i]?k.classList.add("collapsed"):k.classList.remove("collapsed")})}function m(r){const k=a();k[r]=!k[r],s(k),o()}(function(){const k=a();let i=!1;k.sales===void 0&&(k.sales=!1,i=!0),k.expense===void 0&&(k.expense=!0,i=!0),i&&s(k)})(),o(),document.querySelectorAll(".nav-group-toggle").forEach(function(r){r.addEventListener("click",function(){m(r.dataset.toggleGroup)})}),window.expandNavGroupForRoute=function(r){const k=n[r];if(!k)return;const i=a();i[k]&&(i[k]=!1,s(i),o())}})();const Ft=`
    <div class="modal" style="max-width:440px">
        <div class="modal-head">
            <div class="modal-title" data-i18n="help-modal-title">帮助反馈</div>
            <button type="button" class="modal-close" id="help-modal-close" aria-label="Close">
                <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 6l8 8M14 6l-8 8" stroke-linecap="round"/></svg>
            </button>
        </div>
        <div class="modal-body">
            <p class="help-modal-tip" data-i18n="help-modal-tip">遇到问题或有产品建议?以下方式联系我们 · 通常 24 小时内回复</p>
            <div class="help-contact-list">
                <a class="help-contact-card" href="mailto:hello@pearnly.com">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="5" width="18" height="14" rx="2"/>
                        <path d="M3 7l9 6 9-6"/>
                    </svg>
                    <div>
                        <div class="help-contact-label" data-i18n="contact-email-label">邮箱</div>
                        <div class="help-contact-value">hello@pearnly.com</div>
                    </div>
                </a>
                <a class="help-contact-card" href="tel:+66868892228">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                    </svg>
                    <div>
                        <div class="help-contact-label" data-i18n="contact-phone-label">电话</div>
                        <div class="help-contact-value">+66 86-889-2228</div>
                    </div>
                </a>
                <a class="help-contact-card" href="https://line.me/R/ti/p/@059oupmg" target="_blank" rel="noopener">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8z"/>
                    </svg>
                    <div>
                        <div class="help-contact-label" data-i18n="contact-line-label">LINE 客服</div>
                        <div class="help-contact-value">@059oupmg</div>
                    </div>
                </a>
            </div>
        </div>
    </div>`;function st(){const e=document.getElementById("help-modal");if(!e||e.children.length)return;e.innerHTML=Ft;const n=window._currentLang||"th",a=window.I18N&&window.I18N[n]||{};e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");a[o]&&(s.textContent=a[o])})}document.readyState,st();(function(){function e(){const n=document.getElementById("help-modal"),a=document.getElementById("help-modal-close");n&&(a&&!a.dataset.bound&&(a.addEventListener("click",function(){n.style.display="none"}),a.dataset.bound="1"),n.dataset.maskBound||(n.addEventListener("click",function(s){s.target===n&&(n.style.display="none")}),n.dataset.maskBound="1"),window._helpModalEscBound||(document.addEventListener("keydown",function(s){s.key==="Escape"&&n.style.display==="flex"&&(n.style.display="none")}),window._helpModalEscBound=!0))}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",e):e()})();(function(){const e={line:"line",folder:"folder",gmail:"email",erp:"erp",alert:"alert"};document.addEventListener("click",function(n){const a=n.target.closest(".int-btn-configure");if(!a)return;const s=a.closest(".integration-row"),o=s?s.dataset.intAnchor:null;if(o&&e[o]){const m=s.querySelector(".int-name"),r=m?(m.textContent||m.innerText||"").trim():"配置";typeof window.openIntegrationDrawer=="function"&&window.openIntegrationDrawer(e[o],r)}})})();let we=[];window._erpEndpoints=we;let je=null;async function Oe(){try{const e=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(e.status===401){localStorage.removeItem("mrpilot_token");const a=await e.json().catch(()=>({}));if((typeof a.detail=="string"?a.detail:a.detail&&a.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}we=(await e.json()).items||[],window._erpEndpoints=we,vt()}catch(e){console.error("load endpoints failed",e)}}window._refreshErpEndpointsCache=function(){return Oe()};async function ut(){const e=document.getElementById("erp-today-stats");if(e){e.innerHTML="";try{const n=await fetch("/api/erp/stats/today",{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),s=a.total||0,o=a.success||0,m=a.failed||0,r=a.auto_cnt||0;if(s===0){e.innerHTML=`<span class="erp-today-empty">${escapeHtml(t("erp-today-none"))}</span>`;return}const k=[];k.push(`<span class="erp-today-item"><strong>${s}</strong> ${escapeHtml(t("erp-today-total"))}</span>`),o>0&&k.push(`<span class="erp-today-item ok"><strong>${o}</strong> ${escapeHtml(t("erp-today-success"))}</span>`),m>0&&k.push(`<span class="erp-today-item fail"><strong>${m}</strong> ${escapeHtml(t("erp-today-failed"))}</span>`),r>0&&k.push(`<span class="erp-today-item auto"><strong>${r}</strong> ${escapeHtml(t("erp-today-auto"))}</span>`),e.innerHTML=k.join("")}catch(n){console.warn("loadErpTodayStats failed",n)}}}function vt(){const e=document.getElementById("erp-endpoints-list"),n=document.getElementById("erp-status-summary"),a=document.getElementById("btn-add-endpoint");if(!e){console.warn("erp-endpoints-list 容器不存在");return}if(a&&_userInfo){const o=_userInfo.endpoints_limit;o!==-1&&we.length>=o?(a.disabled=!0,a.title=t("ep-limit-reached",{limit:o}),a.classList.add("btn-disabled-plus")):(a.disabled=!1,a.title="",a.classList.remove("btn-disabled-plus"))}if(we.length===0){e.innerHTML=`<div class="erp-empty">${escapeHtml(t("ep-list-empty"))}</div>`,n&&(n.textContent=t("auto-status-none"),n.className="auto-status-pill none");return}const s=we.some(o=>o.auto_push&&o.enabled);if(n&&(n.textContent=t("auto-status-active",{n:we.length,mode:s?t("auto-status-on"):t("auto-status-off")}),n.className="auto-status-pill "+(s?"active":"ready")),ut(),e.innerHTML=we.map(o=>{const m=o.config||{},r=escapeHtml(m.url||"");m._token_set;const k=o.enabled!==!1,i=[];o.is_default&&i.push(`<span class="ep-badge default">${escapeHtml(t("ep-default"))}</span>`),o.auto_push&&i.push(`<span class="ep-badge auto">${escapeHtml(t("ep-auto-push-on"))}</span>`),k||i.push(`<span class="ep-badge disabled">${escapeHtml(t("ep-disabled"))}</span>`);const f=[];return o.success_count>0&&f.push(`<span class="ep-stat ok">${escapeHtml(t("ep-success",{n:o.success_count}))}</span>`),o.failure_count>0&&f.push(`<span class="ep-stat fail">${escapeHtml(t("ep-failure",{n:o.failure_count}))}</span>`),`
            <div class="erp-endpoint" data-ep-id="${escapeHtml(o.id)}">
                <div class="ep-main">
                    <div class="ep-title-row">
                        <div class="ep-name">${escapeHtml(o.name)}</div>
                        <div class="ep-badges">${i.join("")}</div>
                    </div>
                    <div class="ep-url">${r||"-"}</div>
                    <div class="ep-stats">${f.join(" · ")}</div>
                </div>
                <div class="ep-actions">
                    <button class="btn btn-ghost btn-small" data-ep-edit="${escapeHtml(o.id)}">
                        <span>${escapeHtml(t("ep-edit"))}</span>
                    </button>
                    <button class="btn btn-ghost btn-small btn-danger" data-ep-del="${escapeHtml(o.id)}">
                        <span>${escapeHtml(t("ep-delete"))}</span>
                    </button>
                </div>
            </div>
        `}).join(""),_userInfo&&_userInfo.endpoints_limit!==-1){const o=we.length,m=_userInfo.endpoints_limit,r=_userInfo.plan,k=document.createElement("div");k.className="erp-limit-hint",r==="free"?k.innerHTML=`${escapeHtml(t("ep-free-limit-hint",{used:o,limit:m}))} <a data-upgrade="plus">${escapeHtml(t("upgrade-to-plus"))}</a>`:k.textContent=t("ep-plus-limit-hint",{used:o,limit:m}),e.appendChild(k)}}function Vt(e){je=e||null;const n=document.getElementById("endpoint-modal"),a=document.getElementById("endpoint-modal-title");a.textContent=e?t("ep-modal-title-edit"):t("ep-modal-title-new");const s=document.getElementById("ep-name"),o=document.getElementById("ep-url"),m=document.getElementById("ep-token"),r=document.getElementById("ep-is-default"),k=document.getElementById("ep-auto-push"),i=document.getElementById("ep-test-result");i.style.display="none",i.textContent="";const f=document.getElementById("ep-save-error");if(f&&f.remove(),e){const c=we.find(v=>v.id===e);if(!c)return;s.value=c.name||"",o.value=(c.config||{}).url||"",m.value=(c.config||{})._token_set&&c.config.token||"",m.placeholder=(c.config||{})._token_set?"（已保存 · 留空保持不变）":t("ep-token-ph"),r.checked=!!c.is_default,k.checked=!!c.auto_push}else s.value="",o.value="",m.value="",m.placeholder=t("ep-token-ph"),r.checked=we.length===0,k.checked=!0;const u=k.closest(".form-switch-row");if(k.disabled=!1,u){u.classList.remove("disabled-plus"),u.title="",u.style.cursor="",u.onclick=null;const c=u.querySelector(".plus-badge");c&&c.remove()}n.style.display="",setTimeout(()=>s.focus(),50)}function ft(){document.getElementById("endpoint-modal").style.display="none",je=null;const e=document.getElementById("ep-save-error");e&&e.remove()}function mt(e){if(!e)return"";let n=e.trim();const a=n.search(/\s/);return a>=0&&(n=n.slice(0,a)),n}function ht(){const e=document.getElementById("ep-name").value.trim(),n=mt(document.getElementById("ep-url").value),a=document.getElementById("ep-token").value,s=document.getElementById("ep-is-default").checked,o=document.getElementById("ep-auto-push").checked,m={url:n};return a&&(m.token=a),{name:e,url:n,tokenVal:a,isDefault:s,autoPush:o,config:m}}async function Ut(){const{url:e,config:n}=ht(),a=document.getElementById("ep-test-result");if(!e){a.style.display="",a.className="form-test-result fail",a.textContent=t("ep-required");return}a.style.display="",a.className="form-test-result running",a.textContent=t("ep-test-running");try{const o=await(await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({adapter:"webhook",config:n})})).json();o.success?(a.className="form-test-result ok",a.textContent=t("ep-test-ok",{status:o.http_status,ms:o.elapsed_ms})):(a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:o.error_msg||"unknown"}))}catch(s){a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:s.message})}}async function Gt(){const e=ht(),n=document.getElementById("ep-save-error");if(n&&(n.style.display="none"),!e.name||!e.url){ot(t("ep-required"));return}const a={name:e.name,adapter:"webhook",config:e.config,is_default:e.isDefault,auto_push:e.autoPush},s=document.getElementById("btn-ep-save"),o=s.innerHTML;s.disabled=!0,s.classList.add("loading");try{let m;if(je?m=await fetch(`/api/erp/endpoints/${encodeURIComponent(je)}`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}):m=await fetch("/api/erp/endpoints",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}),!m.ok){const k=(await m.json().catch(()=>({}))).detail||`HTTP ${m.status}`;throw new Error(typeof k=="string"?k:JSON.stringify(k))}ft(),showToast(t("ep-save-ok")),Oe()}catch(m){ot(`${t("ep-save-fail")} · ${m.message||"unknown"}`)}finally{s.disabled=!1,s.classList.remove("loading"),s.innerHTML=o}}function ot(e){let n=document.getElementById("ep-save-error");if(!n){const a=document.querySelector("#endpoint-modal .modal-foot");if(!a)return;n=document.createElement("div"),n.id="ep-save-error",n.className="ep-inline-error",a.parentNode.insertBefore(n,a)}n.textContent=e,n.style.display=""}async function Yt(e){const n=we.find(s=>s.id===e);if(!(!n||!await showConfirm(t("ep-delete-confirm",{name:n.name}),{danger:!0})))try{if(!(await fetch(`/api/erp/endpoints/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showToast(t("ep-delete-ok")),Oe()}catch{showToast(t("ep-save-fail"),"fail")}}window.loadErpEndpoints=Oe;window.loadErpTodayStats=ut;window.renderErpEndpointsList=vt;window.openEndpointModal=Vt;window.closeEndpointModal=ft;window.saveEndpoint=Gt;window.deleteEndpoint=Yt;window.testEndpointConnection=Ut;window._sanitizeUrl=mt;async function gt(e){if(e=(e||"").trim(),!!e)try{await navigator.clipboard.writeText(e),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{try{const a=document.createElement("textarea");a.value=e,a.style.position="fixed",a.style.opacity="0",document.body.appendChild(a),a.select(),document.execCommand("copy"),a.remove(),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{showToast(t("erp-doc-copy-fail"),"error")}}}async function Jt(e){const n=document.createElement("div");n.className="log-detail-modal",n.innerHTML=`
        <div class="log-detail-box">
            <div class="log-detail-loading">${escapeHtml(t("log-detail-loading"))}</div>
        </div>
    `,document.body.appendChild(n),n.addEventListener("click",async a=>{if(a.target===n||a.target.classList.contains("log-detail-close")){n.remove();return}const s=a.target.closest("[data-receipt-copy]");if(s){gt(s.dataset.receiptCopy);return}const o=a.target.closest("[data-receipt-action]");if(o){const m=o.dataset.receiptAction;m==="retry"?window.retryPushLog(o.dataset.logId):m==="exceptions"?typeof routeTo=="function"&&routeTo("exceptions"):m==="mappings"&&typeof routeTo=="function"&&routeTo("integrations"),n.remove();return}});try{const a=await fetch(`/api/erp/logs/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!a.ok){n.remove();return}const s=await a.json(),o=window._erpEndpoints.find(L=>L.id===s.endpoint_id),m=s.endpoint_name||(o?o.name:s.endpoint_id?t("erp-log-endpoint-deleted"):"-"),r=(s.endpoint_adapter||o&&o.adapter||"").toLowerCase(),k=new Date(s.created_at).toLocaleString(),i=s.trigger==="auto"?t("log-tag-auto"):s.trigger==="retry"?t("log-tag-retry"):t("log-tag-manual"),f=s.request_body?JSON.stringify(s.request_body,null,2):t("erp-receipt-no-tech"),u=s.response_body||t("erp-receipt-no-tech"),c=s.status==="success";let v=typeof u=="string"?u:JSON.stringify(u,null,2);if(c)try{const L=typeof s.response_body=="string"?JSON.parse(s.response_body):s.response_body||{},H=L.row_count||(Array.isArray(L.imported_rows)?L.imported_rows.length:0);H>0&&(v=t("log-push-rows").replace("{n}",String(H)))}catch{}const E=(s.external_doc_no||"").trim(),x=(s.external_url||"").trim(),R=(s.external_doc_hint||"").trim(),D=(s.ocr_buyer_name||"").trim()||s.client_name||"-",w=s.seller_name||"-";let B="-";const z=Number(s.total_amount);s.total_amount!=null&&s.total_amount!==""&&!isNaN(z)&&(B=z.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}));const q=c?t("erp-receipt-title-ok"):t("erp-receipt-title-fail"),F=c?"✓":"✗",A=[],g=(L,H)=>{A.push(`
                <div class="erp-receipt-row">
                    <span class="erp-receipt-key">${escapeHtml(L)}</span>
                    <span class="erp-receipt-val">${H}</span>
                </div>`)};if(g(t("erp-receipt-invoice-no"),`<strong>${escapeHtml(s.invoice_no||"-")}</strong>`),g(t("erp-receipt-erp-name"),escapeHtml(m)),c){let L;E?L=`<strong class="erp-receipt-docno">${escapeHtml(E)}</strong><button class="erp-receipt-copy-btn" type="button" data-receipt-copy="${escapeHtml(E)}" title="${escapeHtml(t("erp-doc-copy-tip"))}">${escapeHtml(t("erp-receipt-copy-btn"))}</button>`:L=`<span class="erp-receipt-docno-missing">${escapeHtml(t("erp-log-doc-missing"))}</span>`,g(t("erp-receipt-doc-no"),L)}g(t("erp-receipt-client"),escapeHtml(D)),g(t("erp-receipt-seller"),escapeHtml(w)),c&&g(t("erp-receipt-amount"),escapeHtml(B)),g(t("erp-receipt-time"),escapeHtml(k)),g(t("erp-receipt-elapsed"),escapeHtml((s.elapsed_ms!=null?s.elapsed_ms:"-")+"ms"));let d="";c&&x?d=`<a class="erp-receipt-primary-btn" href="${escapeHtml(x)}" target="_blank" rel="noopener">${escapeHtml(t("erp-receipt-open-erp"))}</a>`:c&&E&&(d=`<button class="erp-receipt-primary-btn" type="button" data-receipt-copy="${escapeHtml(E)}">${escapeHtml(t("erp-receipt-copy-docno"))}</button>`);let h="";if(c&&E&&R){const L="erp-receipt-hint-"+R,H=t(L);H&&H!==L&&(h=`<div class="erp-receipt-hint"><svg class="erp-receipt-hint-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span>${escapeHtml(H)}</span></div>`)}let I="";if(!c){const L=(s.error_msg||"").match(/ERR_[A-Z0-9_]+/),H=L?L[0]:"",_=typeof currentLang=="string"&&currentLang||window._currentLang||"th",K=s.error_friendly&&s.error_friendly[_]||(s.error_msg?humanizeError(s.error_msg):t("erp-receipt-no-error")),G=/ERR_NO_CUSTOMER_MAPPING|ERR_NO_CLIENT|ERR_NO_SEED_CUSTOMER|ERR_NO_SEED_PRODUCT/.test(s.error_msg||""),W=!!(s.history_id&&s.endpoint_id),te=[];te.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="exceptions">${escapeHtml(t("erp-receipt-act-exceptions"))}</button>`),G&&te.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="mappings">${escapeHtml(t("erp-receipt-act-mapping"))}</button>`),W&&te.push(`<button class="erp-receipt-action-btn primary" type="button" data-receipt-action="retry" data-log-id="${escapeHtml(s.id)}">${escapeHtml(t("erp-receipt-act-retry"))}</button>`),I=`
                <div class="erp-receipt-fail-reason-label">${escapeHtml(t("erp-receipt-fail-reason"))}</div>
                <div class="erp-receipt-fail-box">
                    ${H?`<div class="erp-receipt-errcode">${escapeHtml(H)}</div>`:""}
                    <div class="erp-receipt-friendly">${escapeHtml(K)}</div>
                </div>
                <div class="erp-receipt-actions-label">${escapeHtml(t("erp-receipt-suggest"))}</div>
                <div class="erp-receipt-actions">${te.join("")}</div>`}n.querySelector(".log-detail-box").innerHTML=`
            <div class="log-detail-head">
                <div class="log-detail-title">
                    <span class="log-detail-status-icon ${c?"ok":"fail"}">${F}</span>
                    ${escapeHtml(q)}
                    <span class="log-tag ${s.trigger}">${escapeHtml(i)}</span>
                </div>
                <button class="log-detail-close" type="button">✕</button>
            </div>

            <div class="erp-receipt-body">
                ${A.join("")}
            </div>

            ${h}
            ${d?`<div class="erp-receipt-primary-wrap">${d}</div>`:""}
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
                    <pre>${escapeHtml(f)}</pre>
                </div>
                <div class="log-detail-section">
                    <div class="log-detail-label">${escapeHtml(t("log-detail-response-human"))}</div>
                    <pre>${escapeHtml(v)}</pre>
                </div>
            </details>
        `}catch(a){console.error(a),n.remove()}}window.copyErpDocNo=gt;window.showLogDetail=Jt;let Be={key:"all",val:""},_e=new Set;window._erpSelected=_e;async function Pe(e){const n=document.getElementById("erp-logs-list");if(n){e||(n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`),window.loadErpTodayStats();try{const a=new URLSearchParams({limit:"30"});Be.key==="status"&&a.set("status",Be.val),Be.key==="trigger"&&a.set("trigger",Be.val),Be.key==="adapter"&&a.set("adapter",Be.val);const s=await fetch(`/api/erp/logs?${a}`,{headers:{Authorization:"Bearer "+token}});if(!s.ok){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const m=(await s.json()).items||[];if(window._erpLogPollTimer&&(clearTimeout(window._erpLogPollTimer),window._erpLogPollTimer=null),m.some(function(f){return f.status==="pending"})&&(window._erpLogPollTimer=setTimeout(function(){Pe(!0)},4e3)),m.length===0){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-empty"))}</div>`;return}const k='<div class="erp-log-row erp-log-row-header" data-log-header>'+(m.filter(function(f){var u=f.status==="failed"&&f.next_retry_at&&new Date(f.next_retry_at).getTime()>Date.now()-6e4;return!u}).map(function(f){return f.id}).length>0?`<input type="checkbox" class="erp-log-cb erp-log-cb-all" data-log-select-all title="${escapeHtml(t("erp-log-select-all-tip"))}">`:'<span class="erp-log-cb-spacer"></span>')+`<span class="log-time">${escapeHtml(t("erp-log-col-time"))}</span><span class="log-status">${escapeHtml(t("erp-log-col-status"))}</span><span class="log-tag-header">${escapeHtml(t("erp-log-col-trigger"))}</span><span class="log-invoice">${escapeHtml(t("erp-log-col-invoice"))}</span><span class="log-workspace">${escapeHtml(t("erp-log-col-workspace"))}</span><span class="log-client">${escapeHtml(t("erp-log-col-client"))}</span><span class="log-seller">${escapeHtml(t("erp-log-col-seller"))}</span><span class="log-erp">${escapeHtml(t("erp-log-col-erp"))}</span><span class="log-doc">${escapeHtml(t("erp-log-col-doc"))}</span><span class="log-http">${escapeHtml(t("erp-log-col-http"))}</span><span class="log-elapsed">${escapeHtml(t("erp-log-col-elapsed"))}</span><span class="log-actions"></span></div>`;n.innerHTML=k+m.map(f=>{const u=new Date(f.created_at),c=`${String(u.getMonth()+1).padStart(2,"0")}-${String(u.getDate()).padStart(2,"0")} ${String(u.getHours()).padStart(2,"0")}:${String(u.getMinutes()).padStart(2,"0")}`,v=f.status==="failed"&&f.next_retry_at&&new Date(f.next_retry_at).getTime()>Date.now()-6e4;let E,x,R;f.status==="pending"?(E="retrying",x="⟳",R=t("erp-status-pending")):f.status==="success"?(E="ok",x="✓",R=t("erp-status-success")):f.status==="skipped_dup"?(E="skipped",x="⏭",R=t("erp-status-skipped")):v?(E="retrying",x="↻",R=t("erp-status-retrying")):(E="fail",x="✗",R=t("erp-status-failed"));let D;f.trigger==="auto"?D=`<span class="log-tag auto">${escapeHtml(t("log-tag-auto"))}</span>`:f.trigger==="retry"?D=`<span class="log-tag retry">${escapeHtml(t("log-tag-retry"))}</span>`:D=`<span class="log-tag manual">${escapeHtml(t("log-tag-manual"))}</span>`;let w="";const B=f.retry_count||0,z=f.max_retries||3;if(v){const K=new Date(f.next_retry_at).getTime()-Date.now(),G=Math.max(0,Math.round(K/6e4)),W=G<=0?t("erp-retry-next-soon"):t("erp-retry-next-min",{n:G});w=`${t("erp-retry-attempt",{n:B,max:z})} · ${W}`}else f.status==="failed"&&B>=z&&!f.next_retry_at&&(w=t("erp-retry-exhausted",{n:B}));const q=f.status==="failed"&&!v?`<button class="log-retry-btn btn btn-icon" data-log-retry="${escapeHtml(f.id)}" title="${escapeHtml(t("log-retry-title"))}">↻</button>`:"",F=!v,A=_e.has(f.id)?"checked":"",g=F?`<input type="checkbox" class="erp-log-cb" data-log-cb="${escapeHtml(f.id)}" ${A}>`:'<span class="erp-log-cb-spacer"></span>',d=(f.ocr_buyer_name||"").trim()||(f.client_name||"").trim(),h=d?`<span class="log-client" title="${escapeHtml(d)}">${escapeHtml(d.substring(0,18))}</span>`:`<span class="log-client log-client-empty" title="${escapeHtml(t("erp-log-client-unassigned-tip"))}">${escapeHtml(t("erp-log-client-unassigned"))}</span>`,I=f.workspace_name?`<span class="log-workspace">${escapeHtml((f.workspace_name||"").substring(0,16))}</span>`:`<span class="log-workspace log-workspace-unresolved" title="${escapeHtml(t("erp-log-ws-unresolved-tip"))}">${escapeHtml(t("erp-log-ws-unresolved"))}</span>`,L=f.endpoint_name?`<span class="log-erp">${escapeHtml((f.endpoint_name||"").substring(0,14))}</span>`:`<span class="log-erp log-erp-deleted">${escapeHtml(t("erp-log-endpoint-deleted"))}</span>`,H=(f.external_doc_no||"").trim(),_=(f.external_url||"").trim();let M;return _?M=`<span class="log-doc"><a href="${escapeHtml(_)}" target="_blank" rel="noopener" class="log-doc-open" title="${escapeHtml(H||"")}">${escapeHtml(t("erp-log-doc-open"))}</a></span>`:H?M=`<span class="log-doc log-doc-copy" data-copy-doc="${escapeHtml(H)}" title="${escapeHtml(t("erp-log-doc-copy-tip"))}">${escapeHtml(H.substring(0,18))}</span>`:f.status==="success"?M=`<span class="log-doc log-doc-missing" title="${escapeHtml(t("erp-log-doc-missing-tip"))}">${escapeHtml(t("erp-log-doc-missing"))}</span>`:M='<span class="log-doc log-doc-empty">-</span>',`
                <div class="erp-log-row ${E}" data-log-detail="${escapeHtml(f.id)}">
                    ${g}
                    <span class="log-time">${c}</span>
                    <span class="log-status" title="${escapeHtml(R+(w?" · "+w:""))}">${x}</span>
                    ${D}
                    <span class="log-invoice">${escapeHtml(f.invoice_no||"-")}</span>
                    ${I}
                    ${h}
                    <span class="log-seller">${escapeHtml((f.seller_name||"").substring(0,20))}</span>
                    ${L}
                    ${M}
                    <span class="log-http">HTTP ${f.http_status||"-"}</span>
                    <span class="log-elapsed">${f.elapsed_ms}ms</span>
                    <span class="log-actions">${q}</span>
                </div>
            `}).join("");const i=new Set(m.map(f=>f.id));for(const f of Array.from(_e))i.has(f)||_e.delete(f);window._refreshErpBatchBar()}catch(a){console.error("load erp logs failed",a),n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}async function bt(e){try{const n=await fetch(`/api/erp/logs/${encodeURIComponent(e)}/retry`,{method:"POST",headers:{Authorization:"Bearer "+token}}),a=await n.json().catch(()=>({}));n.ok&&a.ok?showToast(t("log-retry-ok"),"success"):showToast(t("log-retry-fail")+" · HTTP "+(a.http_status||n.status),"error"),Pe(),window.loadErpEndpoints()}catch{showToast(t("log-retry-fail"),"error")}}(function(){document.getElementById("btn-add-endpoint").addEventListener("click",()=>window.openEndpointModal(null)),document.getElementById("endpoint-modal-close").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-cancel").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-test").addEventListener("click",window.testEndpointConnection),document.getElementById("btn-ep-save").addEventListener("click",window.saveEndpoint),document.getElementById("ep-url").addEventListener("blur",n=>{const a=window._sanitizeUrl(n.target.value);a!==n.target.value.trim()&&(n.target.value=a)}),document.addEventListener("click",n=>{const a=n.target.closest("[data-ep-edit]"),s=n.target.closest("[data-ep-del]");a&&window.openEndpointModal(a.dataset.epEdit),s&&window.deleteEndpoint(s.dataset.epDel);const o=n.target.closest("[data-log-retry]");if(o){n.stopPropagation(),bt(o.dataset.logRetry);return}const m=n.target.closest("[data-log-cb]");if(m){n.stopPropagation();const u=m.dataset.logCb;m.checked?_e.add(u):_e.delete(u),window._refreshErpBatchBar();return}const r=n.target.closest("[data-log-select-all]");if(r){n.stopPropagation();const u=r.checked;document.querySelectorAll("[data-log-cb]").forEach(function(v){v.checked=u;const E=v.dataset.logCb;u?_e.add(E):_e.delete(E)}),window._refreshErpBatchBar();return}if(n.target.closest("#btn-erp-batch-retry")){n.stopPropagation(),window._runErpBatchRetry();return}if(n.target.closest("#btn-erp-batch-clear")){n.stopPropagation(),_e.clear(),document.querySelectorAll(".erp-log-cb").forEach(u=>{u.checked=!1}),window._refreshErpBatchBar();return}const k=n.target.closest("[data-log-detail]");if(k){if(n.target.closest("[data-log-cb]"))return;const u=n.target.closest("[data-copy-doc]");if(u){n.stopPropagation(),window.copyErpDocNo(u.dataset.copyDoc);return}if(n.target.closest(".log-doc-open"))return;window.showLogDetail(k.dataset.logDetail);return}const i=n.target.closest(".chip-filter");if(i){document.querySelectorAll("#erp-logs-filters .chip-filter").forEach(u=>u.classList.remove("active")),i.classList.add("active"),Be={key:i.dataset.filterKey,val:i.dataset.filterVal},Pe();return}if(n.target.closest("#btn-refresh-logs")){const u=n.target.closest("#btn-refresh-logs");u.classList.add("spinning"),setTimeout(()=>u.classList.remove("spinning"),600),Pe();return}const f=n.target.closest(".auto-nav-item");if(f&&f.dataset.autoTab){switchAutomationTab(f.dataset.autoTab);return}})})();window.loadErpLogs=Pe;window.retryPushLog=bt;function yt(){const e=document.getElementById("erp-logs-batch-bar"),n=document.getElementById("erp-logs-batch-count"),a=document.querySelector("[data-log-select-all]");if(a){const m=document.querySelectorAll("[data-log-cb]").length,r=window._erpSelected.size;r===0?(a.checked=!1,a.indeterminate=!1):r>=m?(a.checked=!0,a.indeterminate=!1):(a.checked=!1,a.indeterminate=!0)}if(!e||!n)return;const s=window._erpSelected.size;if(s===0){e.style.display="none";return}e.style.display="",n.textContent=t("erp-batch-selected",{n:s})}async function wt(){console.info("[ErpBatch] retry triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-confirm",{n:e.length})))try{const a=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!a.ok){showToast(t("erp-logs-error"),"error");return}const s=await a.json(),o=t("erp-batch-result",{ok:s.succeeded||0,fail:s.failed||0,skip:s.skipped||0}),m=s.failed&&s.failed>0?"warn":"success";showToast(o,m),window._erpSelected.clear(),window.loadErpLogs()}catch(a){console.error("batch retry failed",a),showToast(t("erp-logs-error"),"error")}}async function kt(){console.info("[ErpBatch] delete triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-delete-confirm",{n:e.length}),{danger:!0}))try{const s=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!s.ok){showToast(t("erp-logs-error"),"error");return}const o=await s.json();e.forEach(function(m){var r=document.querySelector('[data-log-detail="'+m+'"]');r&&r.remove()});var a=document.getElementById("erp-logs-batch-bar");a&&(a.style.display="none"),showToast(t("erp-batch-delete-result",{n:o.deleted||0,skip:o.skipped||0}),o.deleted>0?"success":"warn"),window._erpSelected.clear(),setTimeout(window.loadErpLogs,500)}catch(s){console.error("batch delete failed",s),showToast(t("erp-logs-error"),"error")}}(function(){function n(){var a=document.getElementById("btn-erp-batch-retry"),s=document.getElementById("btn-erp-batch-delete"),o=document.getElementById("btn-erp-batch-clear");a&&!a.dataset.boundDirect&&(a.addEventListener("click",function(m){m.preventDefault(),m.stopPropagation(),wt()}),a.dataset.boundDirect="1"),s&&!s.dataset.boundDirect&&(s.addEventListener("click",function(m){m.preventDefault(),m.stopPropagation(),kt()}),s.dataset.boundDirect="1"),o&&!o.dataset.boundDirect&&(o.addEventListener("click",function(m){m.preventDefault(),m.stopPropagation(),window._erpSelected.clear(),document.querySelectorAll(".erp-log-cb").forEach(function(r){r.checked=!1}),yt()}),o.dataset.boundDirect="1")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n(),setTimeout(n,2e3),setTimeout(n,5e3),window._bindErpBatchButtons=n})();window._refreshErpBatchBar=yt;window._runErpBatchRetry=wt;window._runErpBatchDelete=kt;(function(){let e=null,n=!1;function a(){if(e)return e;const k=document.createElement("div");k.id="line-email-modal",k.style.cssText="position:fixed;inset:0;background:rgba(10,14,39,0.85);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;",k.innerHTML=`
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
        `,document.body.appendChild(k),e=k;const i=k.querySelector("#line-email-input"),f=k.querySelector("#line-email-submit-btn"),u=k.querySelector("#line-email-err");async function c(){u.textContent="";const v=(i.value||"").trim().toLowerCase();if(!v||v.indexOf("@")<0||v.split("@")[1].indexOf(".")<0){u.textContent=t("line-email-err-invalid");return}f.disabled=!0,f.style.opacity="0.6";try{const E=await fetch("/api/me/line_complete_email",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},body:JSON.stringify({email:v})});if(!E.ok)throw new Error("http_"+E.status);const x=await E.json();x.token&&localStorage.setItem("mrpilot_token",x.token),typeof showToast=="function"&&showToast(x.merged?t("line-email-merged-toast"):t("line-email-saved-toast"),"success"),setTimeout(function(){window.location.reload()},600)}catch{u.textContent=t("line-email-err-failed"),f.disabled=!1,f.style.opacity="1"}}return f.addEventListener("click",c),i.addEventListener("keydown",function(v){v.key==="Enter"&&c()}),k}function s(){if(!e)return;const k=e.querySelector("#line-email-title-h"),i=e.querySelector("#line-email-sub-p"),f=e.querySelector("#line-email-input"),u=e.querySelector("#line-email-submit-btn");k&&(k.textContent=t("line-email-title")),i&&(i.textContent=t("line-email-sub")),f&&(f.placeholder=t("line-email-placeholder")),u&&(u.textContent=t("line-email-submit"))}function o(){a(),s(),e.style.display="flex",n=!0;const k=e.querySelector("#line-email-input");k&&setTimeout(function(){k.focus()},100)}async function m(){const k=localStorage.getItem("mrpilot_token");if(k)try{const i=await fetch("/api/me/needs_email",{headers:{Authorization:"Bearer "+k}});if(!i.ok)return;const f=await i.json();f&&f.needs_email&&o()}catch{}}function r(){setTimeout(m,800)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",r):r(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("line-email-modal",function(){n&&s()})})();(function(){function e(u){let c=0;return u.length>=8&&c++,u.length>=12&&c++,/[a-zA-Z]/.test(u)&&/\d/.test(u)&&c++,/[^a-zA-Z0-9]/.test(u)&&c++,Math.min(3,c)}function n(u,c){const v=document.getElementById("cpw-msg");v&&(v.textContent=u,v.className="cpw-msg "+(c||""))}function a(u){return typeof t=="function"?t(u):u}let s=!1;function o(){["cpw-old","cpw-new","cpw-confirm"].forEach(c=>{const v=document.getElementById(c);v&&(v.value="",v.setAttribute("readonly","readonly"))});const u=document.getElementById("cpw-strength-bar");u&&(u.style.width="0%",u.className="cpw-strength-bar"),n("","")}async function m(){const u=document.getElementById("btn-change-pw"),c=document.getElementById("cpw-old"),v=document.getElementById("cpw-new"),E=document.getElementById("cpw-confirm"),x=document.getElementById("cpw-strength-bar");if(!u||!c||!v||!E)return;const R=c.value,D=v.value,w=E.value;if(!R||!D||!w){n(a("settings-change-pw-empty"),"error");return}if(D.length<8){n(a("settings-change-pw-too-short"),"error");return}if(!(/[a-zA-Z]/.test(D)&&/\d/.test(D))){n(a("settings-change-pw-too-weak"),"error");return}if(D!==w){n(a("settings-change-pw-mismatch"),"error");return}u.disabled=!0;const B=u.textContent;u.textContent=a("settings-change-pw-submitting"),n("","");try{const z=localStorage.getItem("mrpilot_token"),q=await fetch("/api/me/change_password",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+z},body:JSON.stringify({old_password:R,new_password:D})}),F=await q.json().catch(()=>({}));if(q.ok&&F.ok)n(a("settings-change-pw-success"),"success"),typeof showToast=="function"&&showToast(a("settings-change-pw-success"),"success"),c.value="",v.value="",E.value="",x&&(x.style.width="0%",x.className="cpw-strength-bar");else{const A=F.detail||"";let g=a("settings-change-pw-success");A==="wrong_old_password"?g=a("settings-change-pw-wrong-old"):A==="password_too_short"?g=a("settings-change-pw-too-short"):A==="password_too_weak"?g=a("settings-change-pw-too-weak"):g=A||"Error",n(g,"error")}}catch(z){console.error("change_password",z),n("Network error","error")}finally{u.disabled=!1,u.textContent=B}}function r(){s||(s=!0,document.addEventListener("click",u=>{if(!u.target||!u.target.closest)return;const c=u.target.closest(".cpw-eye");if(c){const v=document.getElementById(c.dataset.target);v&&(v.type=v.type==="password"?"text":"password");return}if(u.target.closest("#cpw-forgot-link")){u.preventDefault(),k();return}if(u.target.closest("#btn-change-pw")){m();return}u.target.closest('.settings-nav-item[data-settings-tab="account"], .settings-nav-item[data-tab="account"], .settings-nav-item[data-tab="security"]')&&setTimeout(o,100)}),document.addEventListener("input",u=>{if(u.target&&u.target.id==="cpw-new"){const c=document.getElementById("cpw-strength-bar");if(!c)return;const v=e(u.target.value),E=["0%","33%","66%","100%"],x=["","weak","medium","strong"];c.style.width=E[v],c.className="cpw-strength-bar "+x[v]}}),document.addEventListener("focusin",u=>{u.target&&["cpw-old","cpw-new","cpw-confirm"].includes(u.target.id)&&u.target.removeAttribute("readonly")}),document.getElementById("cpw-old")&&o())}function k(){const u=window._userInfo||(typeof _userInfo<"u"?_userInfo:null),c=u&&u.username?u.username:"",v=i(c);let E=document.getElementById("cpw-forgot-overlay");E&&E.remove(),E=document.createElement("div"),E.id="cpw-forgot-overlay",E.className="cpw-forgot-overlay",E.innerHTML=`
            <div class="cpw-forgot-modal">
                <div class="cpw-forgot-head">
                    <div class="cpw-forgot-title">${f(a("cpw-forgot-title"))}</div>
                    <button class="cpw-forgot-close" id="cpw-forgot-close" aria-label="close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="cpw-forgot-body">
                    <p class="cpw-forgot-desc">${f(a("cpw-forgot-desc"))}</p>
                    <div class="cpw-forgot-email">${f(v)}</div>
                    <p class="cpw-forgot-tip">${f(a("cpw-forgot-tip"))}</p>
                    <div class="cpw-forgot-msg" id="cpw-forgot-msg"></div>
                </div>
                <div class="cpw-forgot-foot">
                    <button class="btn btn-ghost" id="cpw-forgot-cancel">${f(a("cpw-forgot-cancel"))}</button>
                    <button class="btn btn-primary" id="cpw-forgot-send">${f(a("cpw-forgot-send"))}</button>
                </div>
            </div>
        `,document.body.appendChild(E);const x=()=>E.remove();E.querySelector("#cpw-forgot-close").addEventListener("click",x),E.querySelector("#cpw-forgot-cancel").addEventListener("click",x),E.addEventListener("click",R=>{R.target===E&&x()}),E.querySelector("#cpw-forgot-send").addEventListener("click",async()=>{const R=E.querySelector("#cpw-forgot-send"),D=E.querySelector("#cpw-forgot-msg");R.disabled=!0;const w=R.textContent;R.textContent=a("cpw-forgot-sending");try{const B=await fetch("/api/auth/forgot_password",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:c})}),z=await B.json().catch(()=>({}));B.ok?(D.textContent=a("cpw-forgot-success"),D.className="cpw-forgot-msg success",R.style.display="none",E.querySelector("#cpw-forgot-cancel").textContent=a("cpw-forgot-close-btn")):(D.textContent=z.detail||a("cpw-forgot-fail"),D.className="cpw-forgot-msg error",R.disabled=!1,R.textContent=w)}catch{D.textContent=a("cpw-forgot-fail"),D.className="cpw-forgot-msg error",R.disabled=!1,R.textContent=w}})}function i(u){if(!u||!u.includes("@"))return u||"";const[c,v]=u.split("@");return c.length<=2?c+"****@"+v:c.slice(0,2)+"****@"+v}function f(u){return u==null?"":String(u).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c])}document.readyState==="complete"||document.readyState==="interactive"?r():document.addEventListener("DOMContentLoaded",r)})();(function(){let e=null,n=!1;async function a(){if(n)return;const o=localStorage.getItem("mrpilot_token");if(o){n=!0;try{const m=await fetch("/api/me",{headers:{Authorization:"Bearer "+o},cache:"no-store"});if(m.status===401){const r=await m.json().catch(()=>({})),k=r&&r.detail;let i="";if(typeof k=="string"?i=k:k&&typeof k=="object"&&(i=k.code||""),console.warn("[heartbeat] session revoked",i),localStorage.removeItem("mrpilot_token"),e&&(clearInterval(e),e=null),i==="auth.session_revoked")try{_showSessionRevokedModal()}catch{window.location.href="/"}else{const f=i==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";try{typeof showToast=="function"&&typeof t=="function"?showToast(t(f),"error"):alert("Session expired")}catch{}setTimeout(()=>{window.location.href="/"},1500)}}}catch{}finally{n=!1}}}function s(){e&&clearInterval(e),e=setInterval(a,15e3)}localStorage.getItem("mrpilot_token")&&s(),window.addEventListener("focus",a),document.addEventListener("visibilitychange",function(){document.hidden||a()}),window._sessionCheck=a})();async function Fe(){const e=document.getElementById("team-loading"),n=document.getElementById("team-list"),a=document.getElementById("team-empty"),s=document.getElementById("team-count");if(n){e&&(e.style.display=""),n.style.display="none",a&&(a.style.display="none");try{const o=await apiGet("/api/team/employees"),m=o&&o.employees||[];if(e&&(e.style.display="none"),s&&(s.textContent=(t("team-count")||"共 {n} 名员工").replace("{n}",m.length)),m.length===0){a&&(a.style.display="");return}n.style.display="",n.innerHTML=m.map(r=>{const k=r.last_login_at?new Date(r.last_login_at).toLocaleDateString():t("team-never-login")||"从未登录",i=r.is_active===!1?"team-status-off":"team-status-on",f=r.is_active===!1?t("team-status-disabled")||"已禁用":t("team-status-active")||"正常",u=r.email?`<span class="team-meta-sep">·</span><span>${escapeHtml(r.email)}</span>`:"";return`
            <div class="team-card" data-employee-id="${escapeHtml(r.id)}">
                <div class="team-card-main">
                    <div class="team-avatar">${escapeHtml((r.username||"?")[0].toUpperCase())}</div>
                    <div class="team-info">
                        <div class="team-name">${escapeHtml(r.username||"")}</div>
                        <div class="team-meta">
                            <span class="team-status-dot ${i}"></span>
                            <span>${escapeHtml(f)}</span>
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml(t("team-last-login")||"上次登录")}: ${escapeHtml(k)}</span>
                            ${u}
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml((t("team-assigned-clients")||"已分配 {n} 客户").replace("{n}",r.assigned_client_count||0))}</span>
                        </div>
                    </div>
                </div>
                <div class="team-card-actions">
                    <button class="btn btn-ghost btn-small" data-assign-clients="${escapeHtml(r.id)}" data-name="${escapeHtml(r.username||"")}">
                        ${escapeHtml(t("team-assign-clients")||"分配客户")}
                    </button>
                    <button class="btn btn-ghost btn-small" data-reset-pwd-employee="${escapeHtml(r.id)}" data-name="${escapeHtml(r.username||"")}" title="${escapeHtml(t("team-reset-pwd")||"重置密码")}">
                        ${escapeHtml(t("team-reset-pwd")||"重置密码")}
                    </button>
                    <button class="btn btn-ghost btn-small" data-toggle-employee="${escapeHtml(r.id)}" data-active="${r.is_active===!1?"false":"true"}">
                        ${escapeHtml(r.is_active===!1?t("team-enable")||"启用":t("team-disable")||"禁用")}
                    </button>
                    <button class="btn btn-ghost btn-small btn-danger-text" data-remove-employee="${escapeHtml(r.id)}" data-name="${escapeHtml(r.username||"")}">
                        ${escapeHtml(t("team-remove")||"移除")}
                    </button>
                </div>
            </div>`}).join("")}catch(o){console.error("loadTeamList failed:",o),e&&(e.textContent=t("team-load-failed")||"加载失败")}}}async function Kt(){document.querySelectorAll(".add-emp-overlay").forEach(s=>s.remove());const e=document.createElement("div");e.className="add-emp-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const s=document.getElementById("add-emp-username");s&&s.focus()},200);function n(){e.classList.remove("show"),setTimeout(()=>e.remove(),220)}e.querySelector(".add-emp-close").addEventListener("click",n),e.querySelector("#add-emp-cancel").addEventListener("click",n),e.addEventListener("click",s=>{s.target===e&&n()}),e.querySelector("#add-emp-submit").addEventListener("click",async()=>{const s=document.getElementById("add-emp-username"),o=document.getElementById("add-emp-email"),m=document.getElementById("add-emp-password"),r=document.getElementById("add-emp-msg"),k=document.getElementById("add-emp-submit"),i=(s.value||"").trim(),f=(o.value||"").trim(),u=m.value||"";if(r.textContent="",r.classList.remove("error"),!i||i.length<3){r.textContent=t("team-modal-err-username")||"用户名至少 3 位",r.classList.add("error");return}if(!/^[a-zA-Z0-9_.\-]+$/.test(i)){r.textContent=t("team-modal-err-username-fmt")||"只能用字母 / 数字 / 下划线 / 点 / 横线",r.classList.add("error");return}if(f&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f)){r.textContent=t("msg-email-invalid")||"邮箱格式不对",r.classList.add("error");return}if(u.length<8){r.textContent=t("pwd-too-short")||"密码至少 8 位",r.classList.add("error");return}if(/^\d+$/.test(u)){r.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",r.classList.add("error");return}if(!(/[a-zA-Z]/.test(u)&&/\d/.test(u))){r.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",r.classList.add("error");return}k.disabled=!0,k.textContent=t("msg-saving")||"保存中...";try{const c={username:i,password:u};f&&(c.email=f);const v=await apiPost("/api/team/employees",c),E=v?await v.json().catch(()=>({})):{};if(v&&v.ok&&E&&E.ok){showToast(t("team-added")||"员工已添加","success"),n(),Fe();return}const x=E&&E.detail||"unknown",R={"team.username_exists":t("team-username-exists")||"用户名已被占用","team.email_exists":t("team-email-exists")||"邮箱已被占用","team.create_failed":t("team-create-failed")||"创建失败","team.only_owner_or_super":t("team-no-permission")||"无权限","team.no_tenant":t("team-no-tenant")||"请先升级账号","pwd.too_short":t("pwd-too-short")||"密码至少 8 位","pwd.too_weak_numeric":t("pwd-too-weak-numeric")||"不能是纯数字","pwd.too_weak_common":t("pwd-too-weak-common")||"这个密码太常见 · 请换一个","pwd.too_weak":t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};r.textContent=R[x]||(t("team-create-failed")||"创建失败")+" ("+x+")",r.classList.add("error")}catch{r.textContent=t("team-create-failed")||"创建失败",r.classList.add("error")}finally{k.disabled=!1,k.textContent=t("team-add")||"添加员工"}});function a(s){s.key==="Escape"&&(n(),document.removeEventListener("keydown",a))}document.addEventListener("keydown",a)}async function Wt(e,n){try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}/active`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({is_active:!!n})})).ok){Fe();return}showToast(t("team-toggle-failed")||"操作失败","error")}catch{showToast(t("team-toggle-failed")||"操作失败","error")}}async function Xt(e,n){const s=(t("team-confirm-remove")||"确认移除员工「{name}」?他的所有识别记录会保留 · 但他将无法登录").replace("{name}",n).replace("{n}",n);if(await showConfirm(s,{danger:!0,okText:t("team-remove")}))try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){showToast(t("team-removed")||"已移除","success"),Fe();return}showToast(t("team-remove-failed")||"移除失败","error")}catch{showToast(t("team-remove-failed")||"移除失败","error")}}async function Zt(e,n){const s=(t("team-reset-pwd-confirm")||"给员工「{name}」发送改密链接?系统将通过员工的邮箱或 LINE 发送一个 15 分钟内有效的链接 · 员工自己点链接改密码 · 您看不到密码").replace("{name}",n).replace("{n}",n);if(await showConfirm(s,{okText:t("team-reset-link-send-btn")||"发送链接"}))try{const m=await fetch(`/api/team/employees/${encodeURIComponent(e)}/reset-password`,{method:"POST",headers:{Authorization:"Bearer "+token}}),r=await m.json().catch(()=>({}));if(m.status===400&&r.detail==="team.reset_no_channel"){showToast(t("team-reset-no-channel")||"员工尚未绑定邮箱或 LINE · 请先帮员工补充邮箱再重置","error");return}if(!m.ok){showToast(t("team-reset-pwd-fail")||"发送失败","error");return}if(r.channel==="line"||r.channel==="email"){const k=t("team-reset-link-sent")||"改密链接已通过 {ch} 发送给员工 · 链接 15 分钟内有效",i=r.channel==="line"?"LINE":t("team-reset-via-email")||"邮箱";showToast(k.replace("{ch}",i),"success");return}showToast(t("team-reset-pwd-fail")||"发送失败","error")}catch{showToast(t("team-reset-pwd-fail")||"发送失败","error")}}document.addEventListener("click",e=>{if(e.target.closest("#btn-add-employee")){e.preventDefault(),Kt();return}const n=e.target.closest("[data-toggle-employee]");if(n){e.preventDefault(),Wt(n.dataset.toggleEmployee,n.dataset.active==="false");return}const a=e.target.closest("[data-remove-employee]");if(a){e.preventDefault(),Xt(a.dataset.removeEmployee,a.dataset.name||"");return}const s=e.target.closest("[data-reset-pwd-employee]");if(s){e.preventDefault(),Zt(s.dataset.resetPwdEmployee,s.dataset.name||"");return}const o=e.target.closest("[data-assign-clients]");if(o){e.preventDefault(),typeof window.openAssignClientsModal=="function"&&window.openAssignClientsModal(o.dataset.assignClients,o.dataset.name||"");return}});window.loadTeamList=Fe;function Qt(e){document.querySelectorAll(".auto-nav-item").forEach(n=>{n.classList.toggle("active",n.dataset.autoTab===e)}),document.querySelectorAll(".auto-panel").forEach(n=>{n.classList.toggle("active",n.dataset.autoPanel===e)}),e==="email"&&typeof window._loadEmailIngestPanel=="function"?(window._loadEmailIngestPanel(),typeof window._startEmailLogAutoRefresh=="function"&&window._startEmailLogAutoRefresh()):typeof window._stopEmailLogAutoRefresh=="function"&&window._stopEmailLogAutoRefresh(),e==="bank"&&typeof window._loadBankReconPanel=="function"&&window._loadBankReconPanel(),e==="linebot"&&typeof window._loadLineBotPanel=="function"&&window._loadLineBotPanel(),e==="alert"&&typeof window._loadNotificationsPanel=="function"&&window._loadNotificationsPanel(),e==="folder"&&typeof window._loadFolderWatcherPanel=="function"&&window._loadFolderWatcherPanel()}window.switchAutomationTab=Qt;typeof console<"u"&&typeof console.info=="function"&&console.info("[pearnly] vite bundle loaded · dashboard + billing + test-center + workspace-switcher + recon-center + assign-clients + access-log + notifications + recon-batch + welcome-wizard + archive-settings");
//# sourceMappingURL=main.js.map
