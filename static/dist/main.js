const Pt=`
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

`,Dt=`        <!-- ── 销项税对账面板(v118.32.0 · 屏 A) ── -->
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


`;(function(){const e=document.getElementById("page-reconcile");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=Pt+Dt,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=document.getElementById("page-integrations");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=document.getElementById("page-settings");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const Rt=`
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

`,qt=`                    <!-- Tab: 邮箱抓取 (v0.17 · M6 · v93 在 Vultr 复活) -->
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
`;(function(){const e=document.getElementById("page-automation");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=Rt+qt,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e={"page-integration":`
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
`},n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;Object.keys(e).forEach(o=>{const s=document.getElementById(o);!s||s.dataset.wbInjected==="1"||(s.innerHTML=e[o],s.dataset.wbInjected="1",a&&a[n]&&s.querySelectorAll("[data-i18n]").forEach(p=>{const l=p.getAttribute("data-i18n");a[n][l]&&(p.textContent=a[n][l])}))})})();(function(){const e=document.getElementById("page-dashboard");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();function Oe(){const e=document.getElementById("results-card");if(_results.length===0){e.classList.remove("show");return}e.classList.add("show");let n=0;_results.forEach(l=>{const y=parseFloat(l.merged_fields.total_amount);isNaN(y)||(n+=y)}),_selectedFiles&&_selectedFiles.length||_results.length;const a=_results.length,o=n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2});document.getElementById("results-head-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-value">${a}</span>
            <span class="rh-stat-label">${t("stats-invoices")}</span>
        </div>
        <div class="rh-stat">
            <span class="rh-stat-label">${t("stats-total")}</span>
            <span class="rh-stat-value">฿ ${o}</span>
        </div>
    `;let s=_results.map((l,y)=>({...l,_idx:y}));if(_searchKeyword){const l=_searchKeyword.toLowerCase();s=s.filter(y=>(y.filename||"").toLowerCase().includes(l)||(y.merged_fields.invoice_number||"").toLowerCase().includes(l))}_sortKey&&s.sort((l,y)=>{let i,r;return _sortKey==="filename"?(i=l.filename,r=y.filename):_sortKey==="invoice_no"?(i=l.merged_fields.invoice_number,r=y.merged_fields.invoice_number):_sortKey==="invoice_date"?(i=l.merged_fields.date,r=y.merged_fields.date):_sortKey==="total"?(i=parseFloat(l.merged_fields.total_amount)||0,r=parseFloat(y.merged_fields.total_amount)||0):_sortKey==="confidence"?(i=l.confidence,r=y.confidence):(i="",r=""),i<r?_sortDir==="asc"?-1:1:i>r?_sortDir==="asc"?1:-1:0});const p=document.getElementById("results-tbody");p.innerHTML=s.map((l,y)=>{const i=l.merged_fields,r=`<span class="empty-cell">${t("empty-val")}</span>`,d="conf-tip-"+(l.confidence||"low"),c="conf-"+(l.confidence||"low"),v=t(d),x=t(c);return`
            <tr data-idx="${l._idx}">
                <td class="num">${y+1}</td>
                <td class="fname" title="${escapeHtml(l.filename)}">${escapeHtml(l.filename)}</td>
                <td class="inv">${i.invoice_number?escapeHtml(i.invoice_number):r}</td>
                <td class="date">${i.date?escapeHtml(i.date):r}</td>
                <td class="amount">${i.total_amount?Number(i.total_amount).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}):r}</td>
                <td><span class="conf-badge ${l.confidence}" data-tip="${escapeHtml(v)}">${x}</span></td>
            </tr>
        `}).join(""),document.querySelectorAll("#results-table th").forEach(l=>{l.classList.remove("sort-asc","sort-desc"),l.dataset.sort===_sortKey&&l.classList.add("sort-"+_sortDir)}),p.querySelectorAll("tr").forEach(l=>{l.addEventListener("click",()=>{const y=parseInt(l.dataset.idx,10);ut(y)})})}document.querySelectorAll("#results-table th").forEach(e=>{e.classList.contains("no-sort")||e.addEventListener("click",()=>{const n=e.dataset.sort;_sortKey===n?_sortDir=_sortDir==="asc"?"desc":"asc":(_sortKey=n,_sortDir="asc"),Oe()})});let it=null;document.getElementById("search-input").addEventListener("input",e=>{const n=e.target.value;document.getElementById("search-clear").style.display=n?"":"none",clearTimeout(it),it=setTimeout(()=>{_searchKeyword=n.trim(),Oe(),pt()},200)});document.getElementById("search-clear").addEventListener("click",()=>{const e=document.getElementById("search-input");e.value="",_searchKeyword="",document.getElementById("search-clear").style.display="none",Oe(),pt(),e.focus()});function pt(){const e=document.getElementById("search-matches");if(!e)return;if(!_searchKeyword){e.textContent="";return}const n=_searchKeyword.toLowerCase();let a=0;for(const o of _results)[o.filename,o.merged_fields?.invoice_number,o.merged_fields?.seller_name,o.merged_fields?.buyer_name].filter(Boolean).join(" ").toLowerCase().includes(n)&&a++;e.textContent=t("search-matches",{n:a})}function ut(e){_drawerIdx=e;const n=_results[e];if(!n)return;document.getElementById("drawer-title").textContent=n.filename;const a=n.engine==="cache"||n.from_cache,o=a?t("badge-cached-hint"):`${(n.elapsed_ms/1e3).toFixed(1)}s`;document.getElementById("drawer-sub").innerHTML=`
        <span>${n.page_count} ${t("pages-unit")} · ${escapeHtml(o)}</span>
        ${a?`<span class="engine-badge cached">${escapeHtml(t("badge-cached"))}</span>`:""}
        <span class="drawer-edit-count" id="drawer-edit-count-sub"></span>
    `,updateDrawerEditCount();const s=_userInfo&&_userInfo.can_edit_fields,p=_userInfo&&_userInfo.can_verify_tax,l=n.merged_fields,y=document.getElementById("drawer-body"),i=s?"":`
        <div class="drawer-readonly-banner">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="9" width="12" height="9" rx="1"/><path d="M7 9V6a3 3 0 016 0v3"/></svg>
            <span>${t("readonly-banner")}</span>
        </div>
    `,r=p?"":`<span class="tax-badge unverified" data-tip="${escapeHtml(t("tax-tip-unverified"))}">${t("tax-unverified")}</span>`;if(y.innerHTML=`
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
                        <select class="drawer-client-select" id="drawer-client-select" ${s?"":"disabled"}>
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
                        ${l.category||n.category_tag?`<span class="drawer-suggest-learned" id="drawer-cat-learned-tag" title="${escapeHtml(t("drawer-suggest-learned-tip"))}">${escapeHtml(t("drawer-suggest-learned"))}</span>`:`<span class="drawer-suggest-empty">${escapeHtml(t("drawer-suggest-empty"))}</span>`}
                    </div>
                    <div class="drawer-suggest-body">
                        <input type="text" class="drawer-suggest-input" id="drawer-cat-input" data-field="category_tag"
                               list="drawer-cat-datalist"
                               placeholder="${escapeHtml(t("drawer-suggest-placeholder"))}"
                               value="${escapeHtml((n.edits&&n.edits.category_tag!==void 0?n.edits.category_tag:l.category||n.category_tag)||"")}"
                               ${s?"":"readonly"}>
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
            ${ye("invoice_number","drawer-lbl-invoice",l.invoice_number,"input",s)}
            ${ye("date","drawer-lbl-date",l.date,"input",s)}
            ${l.date_raw&&l.date_raw!==l.date?`<div class="date-raw-hint" title="${escapeHtml(t("drawer-date-raw-tip"))}">${escapeHtml(t("drawer-date-raw-label"))}: ${escapeHtml(l.date_raw)}</div>`:""}
            ${ye("subtotal","drawer-lbl-subtotal",l.subtotal,"input",s)}
            ${ye("vat","drawer-lbl-vat",l.vat,"input",s)}
            ${ye("total_amount","drawer-lbl-total",l.total_amount,"input",s)}
            ${l.wht_amount||l.wht_rate?`
                ${ye("wht_amount","drawer-lbl-wht-amount",l.wht_amount,"input",s,Nt(l.wht_rate))}
            `:""}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 18V8h14v10M3 8l2-4h10l2 4M7 12h2M11 12h2"/></svg>
                ${t("drawer-sec-seller")}
            </div>
            ${ye("seller_name","drawer-lbl-name",l.seller_name,"input",s)}
            ${ye("seller_tax","drawer-lbl-tax",l.seller_tax,"input",s,r,rt("seller"))}
            ${ye("seller_addr","drawer-lbl-addr",l.seller_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="10" cy="6" r="3"/><path d="M3 18c0-3.9 3.1-7 7-7s7 3.1 7 7"/></svg>
                ${t("drawer-sec-buyer")}
            </div>
            ${ye("buyer_name","drawer-lbl-name",l.buyer_name,"input",s)}
            ${ye("buyer_tax","drawer-lbl-tax",l.buyer_tax,"input",s,r,rt("buyer"))}
            ${ye("buyer_addr","drawer-lbl-addr",l.buyer_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 7l7-4 7 4v7l-7 4-7-4z"/><path d="M3 7l7 4 7-4M10 11v8"/></svg>
                ${t("drawer-sec-items")}
            </div>
            ${l.items&&l.items.length>0?zt(l.items):`<div class="drawer-items-empty">${t("drawer-items-empty")}</div>`}
        </div>

        <div class="drawer-section">
            ${ye("notes","drawer-lbl-notes",l.notes,"textarea",s)}
        </div>

        <details class="raw-text">
            <summary>${t("raw-text")}</summary>
            <pre>${escapeHtml(n.pages.map(d=>`--- Page ${d.page||d.page_number||"?"} ---
${d.raw_text||d.text||""}`).join(`

`))}</pre>
        </details>
    `,s?y.querySelectorAll("[data-field]").forEach(d=>{d.addEventListener("input",onFieldEdit)}):y.querySelectorAll("[data-field]").forEach(d=>{d.setAttribute("readonly","readonly")}),document.getElementById("drawer-mask").classList.add("show"),document.getElementById("drawer").classList.add("show"),injectOcrPushButton(),typeof window.bindDrawerClient=="function"){const d=n._historyId||n.history_id||null;window.bindDrawerClient(d,n.client_id||null)}typeof window.fillCategoryDatalist=="function"&&window.fillCategoryDatalist(),setTimeout(()=>{const d=document.getElementById("drawer-cat-input");d&&!d.value&&!d.readOnly&&d.focus()},80)}function Nt(e){return e?`<span class="wht-badge">${escapeHtml(e)}%</span>`:""}function ye(e,n,a,o,s,p,l){const y=_results[_drawerIdx],i=y&&y.edits[e]!==void 0?y.edits[e]:a,r=y&&y.edits[e]!==void 0&&y.edits[e]!==a,d=escapeHtml(i??""),c=s?"":"readonly",v=o==="textarea"?`<textarea data-field="${e}" rows="2">${d}</textarea>`:`<input type="text" data-field="${e}" value="${d}">`;return`
        <div class="drawer-field ${r?"edited":""} ${c}" data-field-wrap="${e}">
            <label class="drawer-field-label">
                <span class="drawer-field-edited-dot"></span>
                ${t(n)}
                ${p||""}
                ${l?`<span class="drawer-field-actions">${l}</span>`:""}
            </label>
            ${v}
        </div>
    `}function rt(e){return _userInfo&&_userInfo.can_verify_tax?`
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
        </button>`}function zt(e){return`
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
    `}function Ot(){document.getElementById("drawer-mask").classList.remove("show"),document.getElementById("drawer").classList.remove("show");const e=document.getElementById("drawer-history-save");e&&e.remove();const n=document.getElementById("drawer-ocr-push");n&&n.remove();const a=document.getElementById("drawer-ocr-push-btn");a&&a.remove(),_drawerIdx=-1}window.renderResults=Oe;window.openDrawer=ut;window.closeDrawer=Ot;function Ft(){const e=_results[_drawerIdx];if(!e||e._historyMode||!_userInfo||!_userInfo.can_push_erp||!e._historyId&&!e.history_id)return;const n=e._historyId||e.history_id,a=document.querySelector(".drawer-header");if(!a||document.getElementById("drawer-ocr-push-btn"))return;const o=(window._erpEndpoints||_erpEndpoints||[]).filter(function(y){return y&&y.enabled!==!1});if(o.length===0)return;const s=document.createElement("button");s.id="drawer-ocr-push-btn",s.className="drawer-push-btn";let p;if(o.length===1){const y=o[0].name||o[0].adapter||"ERP";p=t("btn-push-to-name",{name:y}),s.title=p}else p=t("btn-push-erp")+" ▾",s.title=t("btn-push-erp-pick-tip");s.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 8h9M8 5l3 3-3 3"/>
            <rect x="11" y="3" width="3" height="10" rx="1"/>
        </svg>
        <span>${escapeHtml(p)}</span>
    `,s.addEventListener("click",function(y){y.preventDefault(),y.stopPropagation(),o.length===1?vt(n,o[0].id):Vt(s,n,o)});const l=a.querySelector(".drawer-diagnose");l?a.insertBefore(s,l):a.appendChild(s)}function Vt(e,n,a){document.querySelectorAll(".drawer-push-picker").forEach(i=>i.remove());const o=e.getBoundingClientRect(),s=document.createElement("div");s.className="drawer-push-picker history-popover",s.style.position="fixed",s.style.top=o.bottom+6+"px",s.style.left=Math.max(8,o.right-240)+"px",s.style.minWidth="220px",s.style.zIndex="12000";const p=a.map(function(i){const r=escapeHtml(i.name||i.adapter||"ERP"),d=escapeHtml((i.adapter||"").toLowerCase()),v=i.is_default?'<span style="font-size:10px;color:#0a7a2c;background:#d6f5e0;padding:1px 6px;border-radius:999px;margin-left:6px;">'+escapeHtml(t("ep-default"))+"</span>":"";return'<button type="button" data-ep-id="'+escapeHtml(i.id)+'" style="display:flex;align-items:center;justify-content:space-between;width:100%;text-align:left;"><span><span style="color:#5d5d57;font-size:11px;margin-right:6px;">'+d+"</span>"+r+v+"</span></button>"}).join("");s.innerHTML=p,document.body.appendChild(s);const l=()=>{s.remove(),document.removeEventListener("click",y,!0)},y=i=>{!s.contains(i.target)&&i.target!==e&&!e.contains(i.target)&&l()};setTimeout(()=>document.addEventListener("click",y,!0),0),s.addEventListener("click",i=>{const r=i.target.closest("[data-ep-id]");if(!r)return;const d=r.getAttribute("data-ep-id");l(),vt(n,d)})}async function vt(e,n){const a=document.getElementById("drawer-ocr-push-btn");a&&(a.disabled=!0);try{const o={history_id:e};n&&(o.endpoint_id=n);const s=await fetch("/api/erp/push",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(o)}),p=await s.json();if(!s.ok){const l=p&&p.detail?p.detail:"err.unknown";l==="erp.no_default_endpoint"?showToast(t("erp-push-no-endpoint"),"warn"):l==="erp.endpoint_disabled"?(showToast(t("erp-push-disabled-tip")||t("card-disabled-tip")||"Endpoint disabled","warn"),typeof window._refreshErpEndpointsCache=="function"&&window._refreshErpEndpointsCache()):showToast(t("erp-push-fail",{err:l}),"fail");return}p.ok?showToast(t("erp-push-ok",{name:p.endpoint_name||""})):showToast(t("erp-push-fail",{err:p.error_msg||"unknown"}),"fail")}catch(o){showToast(t("erp-push-fail",{err:o.message}),"fail")}finally{a&&(a.disabled=!1)}}window.injectOcrPushButton=Ft;const Ut=[{id:"input_vat",nameKey:"tpl-input-vat",descKey:"tpl-input-vat-desc",badge:"recommended"},{id:"standard",nameKey:"tpl-standard",descKey:"tpl-standard-desc"},{id:"sales_detail_th",nameKey:"export-tpl-sales-detail",descKey:"export-tpl-sales-detail-desc",badge:"new"},{id:"print",nameKey:"tpl-print",descKey:"tpl-print-desc"}];function ft(){try{const e=localStorage.getItem("pn_export_tpl")||"input_vat";return e==="erp"?"input_vat":e}catch{return"input_vat"}}function Gt(e){try{localStorage.setItem("pn_export_tpl",e||"input_vat")}catch{}}async function mt(e){if(_results.length===0)return;e=e||"input_vat";const n=document.getElementById("btn-export");n&&(n.disabled=!0,n.classList.add("loading"));try{let a,o=`pearnly-export-${Date.now()}.xlsx`;if(e==="sales_detail_th"){const r=[];for(const d of _results){const c=d.invoices&&d.invoices.length>0?d.invoices:null;if(c&&c.length>1)for(let v=0;v<c.length;v++){const x=c[v]||{};r.push({filename:d.filename+" #"+(v+1)+"/"+c.length,engine:d.engine,merged_fields:x.fields||{}})}else r.push({filename:d.filename,engine:d.engine,merged_fields:d.merged_fields})}a=await apiPost("/api/ocr/export",{records:r,lang:currentLang,template:"sales_detail_th"})}else{const r=[];for(const c of _results)c.history_ids&&Array.isArray(c.history_ids)?r.push(...c.history_ids):c.history_id&&r.push(c.history_id);if(r.length===0){showToast(t("toast-export-error"),"error");return}const d=localStorage.getItem("mrpilot_token");a=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+d,"Content-Type":"application/json"},body:JSON.stringify({template:e,lang:currentLang,history_ids:r,client_id:null})}),o=`pearnly-${e}-${Date.now()}.xlsx`}if(!a)return;if(!a.ok){let r="HTTP "+a.status;try{const c=await a.json();c&&c.detail&&(r=typeof c.detail=="string"?c.detail:JSON.stringify(c.detail))}catch(c){console.warn("[export] resp.json err.detail parse failed:",c)}const d=typeof r=="string"&&r.indexOf(".")>0?"err."+r:null;showToast(d?t(d):t("toast-export-error")+" · "+r,"error");return}const s=await a.blob();let p=o;const l=a.headers.get("X-Filename");if(l)p=l;else{const d=(a.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(d)try{p=decodeURIComponent(d[1])}catch{}}const y=URL.createObjectURL(s),i=document.createElement("a");i.href=y,i.download=p,document.body.appendChild(i),i.click(),document.body.removeChild(i),URL.revokeObjectURL(y),showToast(t("toast-export-success"),"success")}catch(a){console.error(a),showToast(t("toast-export-error"),"error")}finally{n&&(n.disabled=!1,n.classList.remove("loading"))}}document.getElementById("btn-export").addEventListener("click",()=>{mt(ft())});function Jt(){const e=document.getElementById("export-split-wrap");if(!e)return;let n=document.getElementById("export-dropdown");if(n){n.remove();return}n=document.createElement("div"),n.id="export-dropdown",n.className="export-dropdown";const a=ft(),o=Ut.map(p=>{const l=p.badge==="recommended"?`<span class="export-dd-badge badge-rec">${escapeHtml(t("report-recommended"))}</span>`:p.badge==="new"?`<span class="export-dd-badge badge-new">${escapeHtml(t("tpl-badge-new"))}</span>`:"";return`
            <div class="export-dd-item ${p.id===a?"active":""}" data-tpl="${p.id}">
                <div class="export-dd-row">
                    <span class="export-dd-name">${escapeHtml(t(p.nameKey))}</span>
                    ${l}
                    ${p.id===a?'<span class="export-dd-check">✓</span>':""}
                </div>
                <div class="export-dd-desc">${escapeHtml(t(p.descKey))}</div>
            </div>
        `}).join(""),s=`
        <div class="export-dd-divider"></div>
        <div class="export-dd-item export-dd-custom" data-tpl="__custom" title="${escapeHtml(t("tpl-custom-coming"))}">
            <div class="export-dd-row">
                <span class="export-dd-name">+ ${escapeHtml(t("tpl-custom-new"))}</span>
                <span class="export-dd-badge badge-soon">${escapeHtml(t("cs-coming-soon"))}</span>
            </div>
        </div>
    `;n.innerHTML=o+s,e.appendChild(n)}function Ke(){const e=document.getElementById("export-dropdown");e&&e.remove()}const We=document.getElementById("btn-export-arrow");We&&We.addEventListener("click",e=>{e.stopPropagation(),!We.disabled&&Jt()});document.addEventListener("click",e=>{const n=e.target.closest(".export-dd-item");if(n){const a=n.getAttribute("data-tpl");if(a==="__custom"){Ke(),showToast(t("cs-coming-soon"),"info");return}Gt(a),Ke(),mt(a);return}e.target.closest("#btn-export-arrow")||Ke()});function Yt(){const e=document.getElementById("btn-export-arrow"),n=document.getElementById("btn-export");e&&n&&(e.disabled=n.disabled)}setInterval(Yt,300);function Ze(){const e=document.getElementById("history-batch-bar"),n=document.getElementById("history-batch-count"),a=document.getElementById("history-check-all");if(!e||!n)return;const o=_historySelected.size;if(o>0?(e.style.display="",n.textContent=t("history-batch-count",{n:o})):e.style.display="none",a){const s=_historyState.items||[];if(s.length===0)a.checked=!1,a.indeterminate=!1;else{const p=s.filter(l=>_historySelected.has(l.id)).length;a.checked=p===s.length,a.indeterminate=p>0&&p<s.length}}}function Kt(){_historySelected.clear(),Ze()}async function Qe(){if(!_userInfo){setTimeout(()=>Qe(),300);return}const e=document.getElementById("history-free-block"),n=document.getElementById("history-main"),a=document.getElementById("history-empty");if(!e||!n||!a){console.warn("[History] container missing");return}if(!_userInfo.can_view_history){e.style.display="",n.style.display="none",a.style.display="none";return}e.style.display="none",_historyState.loading=!0;try{const o=_historyState.page*_historyState.pageSize,s=new URLSearchParams({limit:_historyState.pageSize,offset:o});_historyState.keyword&&s.set("keyword",_historyState.keyword);const p=typeof window.getCurrentClientId=="function"?window.getCurrentClientId():null;p&&s.set("client_id",String(p));const l=await fetch(`/api/history?${s}`,{headers:{Authorization:"Bearer "+token}});if(l.status===401){localStorage.removeItem("mrpilot_token");const r=await l.json().catch(()=>({}));if((typeof r.detail=="string"?r.detail:r.detail&&r.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}const y=await l.json();_historyState.items=y.items||[],_historyState.total=y.total||0;const i=new Set(_historyState.items.map(r=>r.id));for(const r of Array.from(_historySelected))i.has(r)||_historySelected.delete(r);ht()}catch(o){console.error("load history failed",o)}finally{_historyState.loading=!1}}function ht(){const e=document.getElementById("history-main"),n=document.getElementById("history-empty"),a=_historyState.items,o=document.getElementById("history-search-matches");if(o&&(o.textContent=_historyState.keyword?t("search-matches",{n:_historyState.total}):""),a.length===0&&_historyState.total===0&&!_historyState.keyword){e.style.display="none",n.style.display="";return}e.style.display="",n.style.display="none";let s=0;a.forEach(r=>{r.confidence==="high"&&s++});const p=a.length>0?Math.round(s/a.length*100):0;document.getElementById("history-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-label">${escapeHtml(t("history-total",{n:_historyState.total}))}</span>
        </div>
        <div class="rh-stat rh-stat-quality">
            <span class="rh-stat-dot"></span>
            <span class="rh-stat-label">${escapeHtml(t("history-avg-conf",{p}))}</span>
        </div>
    `;const l=document.getElementById("history-tbody");a.length===0?l.innerHTML=`<div class="history-row-empty">${escapeHtml(t("history-empty-title"))}</div>`:l.innerHTML=a.map(r=>{const d=new Date(r.created_at),c=String(d.getMonth()+1).padStart(2,"0"),v=String(d.getDate()).padStart(2,"0"),x=String(d.getHours()).padStart(2,"0"),_=String(d.getMinutes()).padStart(2,"0"),q=`${c}-${v} ${x}:${_}`,j=escapeHtml(r.filename||""),k=j.length>50?j.substring(0,50)+"…":j,B=r.invoice_no?escapeHtml(r.invoice_no):k,N=[];r.seller_name&&N.push(escapeHtml(r.seller_name)),r.invoice_no&&r.filename&&N.push(k);const R=N.join(" · ")||"-",F=r.category_tag?`<span class="history-badge category">${escapeHtml(r.category_tag)}</span>`:"",A=r.source_total&&r.source_total>1?`<span class="history-badge multi">${escapeHtml(t("invoice-part-of",{i:r.source_index||1,n:r.source_total}))}</span>`:"",g=r.total_amount!==null&&r.total_amount!==void 0?Number(r.total_amount).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):'<span class="history-cell-amount-empty">—</span>',f=[];(r.total_amount===null||r.total_amount===void 0)&&f.push(t("field-amount")),r.invoice_no||f.push(t("field-invoice-no")),r.invoice_date||f.push(t("field-invoice-date")),r.seller_name||f.push(t("field-seller-name")),f.length>0&&`${escapeHtml(r.id)}${escapeHtml(t("history-needs-review-tip")+" · "+f.join(" · "))}${escapeHtml(t("history-needs-review-tip"))}${svgIcon("alert",14)}`,r.edited&&`${escapeHtml(t("history-edited",{n:r.edit_count||1}))}`;const h=r.smart_assigned_flag?`<span class="history-badge smart-assigned" title="${escapeHtml(t("history-smart-assigned"))}">${svgIcon("sparkle",11)}</span>`:"",I=r.confidence==="high"?"high":r.confidence==="medium"?"mid":"low",L=r.confidence==="high"?t("conf-high"):r.confidence==="medium"?t("conf-medium"):t("conf-low"),$=`<span class="history-badge conf-${I}">${escapeHtml(L)}</span>`;let E="";const M=r.source||"manual";return M==="email"?E=`<span class="history-badge source source-email" title="${escapeHtml(t("history-source-email"))}">${svgIcon("mail",11)}<span>${escapeHtml(t("history-source-email"))}</span></span>`:M==="folder"?E=`<span class="history-badge source source-folder" title="${escapeHtml(t("history-source-folder"))}">${svgIcon("folder",11)}<span>${escapeHtml(t("history-source-folder"))}</span></span>`:M==="api"&&(E=`<span class="history-badge source source-api" title="${escapeHtml(t("history-source-api"))}">${svgIcon("api",11)}<span>${escapeHtml(t("history-source-api"))}</span></span>`),`
                <div class="history-row" data-hid="${escapeHtml(r.id)}">
                    <div class="history-cell-check">
                        <input type="checkbox" class="history-row-check" data-hid="${escapeHtml(r.id)}" ${_historySelected.has(r.id)?"checked":""} aria-label="select">
                    </div>
                    <div class="history-cell-date">${q}</div>
                    <div class="history-cell-file">
                        <div class="history-cell-filename">${B} ${F} ${A} ${E} ${h}</div>
                        <div class="history-cell-subtitle">${R}</div>
                    </div>
                    <div class="history-cell-amount">${g}</div>
                    <div class="history-cell-conf">${$}</div>
                    <div class="history-cell-menu">
                        <button class="history-menu-btn" data-hmenu="${escapeHtml(r.id)}" type="button" aria-label="menu">
                            <svg viewBox="0 0 16 16" fill="currentColor"><circle cx="3" cy="8" r="1.5"/><circle cx="8" cy="8" r="1.5"/><circle cx="13" cy="8" r="1.5"/></svg>
                        </button>
                    </div>
                </div>
            `}).join(""),Ze();const y=a.length>0?_historyState.page*_historyState.pageSize+1:0,i=_historyState.page*_historyState.pageSize+a.length;document.getElementById("history-pager-info").textContent=t("history-pager",{from:y,to:i,total:_historyState.total}),document.getElementById("history-prev").disabled=_historyState.page===0,document.getElementById("history-next").disabled=(_historyState.page+1)*_historyState.pageSize>=_historyState.total}window.loadHistoryPage=Qe;window.renderHistoryList=ht;window.updateHistoryBatchBar=Ze;window.clearHistorySelection=Kt;typeof currentRoute<"u"&&currentRoute==="history"&&Qe();async function Ne(e){try{const n=await fetch(`/api/history/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=mergeFields(a.pages||[]),s={filename:a.filename,pages:a.pages,page_count:a.page_count,elapsed_ms:a.elapsed_ms,engine:"history",merged_fields:o,edits:{},confidence:a.confidence,archive_name:a.archive_name||null,category_tag:a.category_tag||null,_historyId:a.id,_historyMode:!0,client_id:a.client_id||null};_results.push(s),_drawerIdx=_results.length-1,openDrawer(_drawerIdx),Xt(),typeof window.bindDrawerClient=="function"&&window.bindDrawerClient(a.id,a.client_id||null),Zt(a.id)}catch(n){console.error("open history detail failed",n)}}async function Wt(e){await Ne(e),requestAnimationFrame(()=>{const n=document.querySelector('[data-field="total_amount"]');if(n){try{n.focus()}catch{}try{n.select()}catch{}try{n.scrollIntoView({block:"center",behavior:"smooth"})}catch{}}})}function Xt(){const e=document.getElementById("drawer-body");if(!e||document.getElementById("drawer-history-save"))return;const n=document.createElement("div");n.id="drawer-history-save",n.className="drawer-history-save-bar",n.innerHTML=`
        <button class="btn btn-ghost" id="btn-push-erp" title="${escapeHtml(t("btn-push-erp"))}" style="display:none;">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M2 8h9M8 5l3 3-3 3"/>
                <rect x="11" y="3" width="3" height="10" rx="1"/>
            </svg>
            <span>${escapeHtml(t("btn-push-erp"))}</span>
        </button>
        <span id="drawer-erp-pushed-badge" style="display:none;align-items:center;gap:4px;font-size:12px;font-weight:600;color:#059669;background:#D1FAE5;padding:3px 8px;border-radius:20px;white-space:nowrap;">
            <svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:10px;height:10px;flex-shrink:0;"><path d="M2 6l3 3 5-5"/></svg>
            ${escapeHtml(t("erp-pushed-badge"))}
        </span>
        <div style="flex:1"></div>
        <button class="btn btn-primary" id="btn-save-history">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8l3 3 7-7"/></svg>
            <span>${escapeHtml(t("history-save"))}</span>
        </button>
    `,e.appendChild(n),document.getElementById("btn-save-history").addEventListener("click",en),document.getElementById("btn-push-erp").addEventListener("click",Qt)}async function Zt(e){}async function Qt(){showToast(t("erp-push-coming-soon")||"ERP 推送即将开放，敬请期待","info")}async function en(){const e=_results[_drawerIdx];if(!e||!e._historyId)return;const n=JSON.parse(JSON.stringify(e.pages||[]));if(n.length>0){const o=n.findIndex(y=>!y.is_duplicate&&!y.is_copy),s=o>=0?o:0,p=n[s].fields||(n[s].fields={}),l={...e.edits};l.category_tag!==void 0&&(l.category=l.category_tag,delete l.category_tag),Object.assign(p,l)}const a=document.getElementById("btn-save-history");a&&(a.disabled=!0);try{if(!(await fetch(`/api/history/${encodeURIComponent(e._historyId)}`,{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({pages:n})})).ok)throw new Error("save failed");showAlert("info",t("history-save-ok")),setTimeout(hideAlerts,1500),closeDrawer(),e._historyMode&&_results.pop(),loadHistoryPage()}catch{showAlert("error",t("history-save-fail")),a&&(a.disabled=!1)}}function tn(e,n){document.querySelectorAll(".history-popover").forEach(r=>r.remove());const a=n.getBoundingClientRect(),o=(_historyState.items||[]).find(r=>r.id===e),s=o&&o.invoice_no?String(o.invoice_no):"",p=o&&o.has_pdf===!0,l=document.createElement("div");l.className="history-popover",l.innerHTML=`
        <button data-act="copy-invno" ${s?"":"disabled"}>${escapeHtml(t("history-menu-copy-invno"))}</button>
        <button data-act="download-pdf" ${p?"":"disabled"}>${escapeHtml(t("history-menu-download-pdf"))}</button>
        <button data-act="delete" class="danger">${escapeHtml(t("history-menu-delete"))}</button>
    `,l.style.top=a.bottom+4+"px",l.style.left=a.right-160+"px",document.body.appendChild(l);const y=()=>{l.remove(),document.removeEventListener("click",i,!0)},i=r=>{!l.contains(r.target)&&r.target!==n&&y()};setTimeout(()=>document.addEventListener("click",i,!0),0),l.addEventListener("click",async r=>{const d=r.target.closest("[data-act]");if(!d||d.disabled)return;const c=d.dataset.act;if(y(),c==="copy-invno"){if(!s)return;try{await navigator.clipboard.writeText(s),showToast(t("history-copy-invno-ok",{no:s}),"success")}catch{try{const x=document.createElement("textarea");x.value=s,x.style.position="fixed",x.style.opacity="0",document.body.appendChild(x),x.select(),document.execCommand("copy"),document.body.removeChild(x),showToast(t("history-copy-invno-ok",{no:s}),"success")}catch{showToast(t("history-copy-invno-fail"),"error")}}}else if(c==="download-pdf"){const v=showToast(t("history-download-pdf-loading"),"loading",0);try{const x=await fetch(`/api/history/${encodeURIComponent(e)}/pdf`,{headers:{Authorization:"Bearer "+token}});if(!x.ok)throw new Error("download failed");const _=await x.blob(),q=URL.createObjectURL(_),j=document.createElement("a");j.href=q,j.download=o&&o.filename?o.filename.endsWith(".pdf")?o.filename:o.filename+".pdf":"invoice.pdf",document.body.appendChild(j),j.click(),document.body.removeChild(j),setTimeout(()=>URL.revokeObjectURL(q),5e3),v(),showToast(t("history-download-pdf-ok"),"success")}catch{v(),showToast(t("history-download-pdf-fail"),"error")}}else if(c==="delete"){if(!await showConfirm(t("history-confirm-delete"),{danger:!0}))return;try{if(!(await fetch(`/api/history/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showAlert("info",t("history-delete-ok")),setTimeout(hideAlerts,1500),loadHistoryPage()}catch{showAlert("error",t("history-delete-fail"))}}})}(function(){document.addEventListener("click",l=>{const y=l.target.closest(".history-row"),i=l.target.closest("[data-hmenu]");if(i){l.stopPropagation(),tn(i.dataset.hmenu,i);return}const r=l.target.closest("[data-review]");if(r){l.stopPropagation(),Ne(r.dataset.review);return}const d=l.target.closest("[data-fill-amount]");if(d){l.stopPropagation(),Wt(d.dataset.fillAmount);return}l.target.closest(".history-row-check")||l.target.closest(".history-cell-check")||y&&!l.target.closest("[data-hmenu]")&&Ne(y.dataset.hid)});const n=document.getElementById("history-tbody");n&&n.addEventListener("change",l=>{const y=l.target.closest(".history-row-check");if(!y)return;const i=y.dataset.hid;y.checked?_historySelected.add(i):_historySelected.delete(i),updateHistoryBatchBar()});const a=document.getElementById("history-check-all");a&&a.addEventListener("change",l=>{const y=l.target.checked;for(const i of _historyState.items)y?_historySelected.add(i.id):_historySelected.delete(i.id);document.querySelectorAll(".history-row-check").forEach(i=>{i.checked=y}),updateHistoryBatchBar()});const o=document.getElementById("history-batch-cancel");o&&o.addEventListener("click",()=>{clearHistorySelection(),document.querySelectorAll(".history-row-check").forEach(l=>{l.checked=!1})});const s=document.getElementById("history-batch-delete");s&&s.addEventListener("click",async()=>{const l=_historySelected.size;if(l===0||!await showConfirm(t("history-batch-confirm",{n:l}),{danger:!0}))return;const i=Array.from(_historySelected);try{const r=await fetch("/api/history/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({ids:i})});if(!r.ok)throw new Error("batch delete failed");const d=await r.json();showToast(t("history-batch-done",{n:d.deleted||0}),"success"),clearHistorySelection(),loadHistoryPage()}catch(r){console.error("batch delete",r),showToast(t("history-batch-fail"),"error")}});let p=null;document.getElementById("history-search").addEventListener("input",l=>{const y=l.target.value;document.getElementById("history-search-clear").style.display=y?"":"none",clearTimeout(p),p=setTimeout(()=>{_historyState.keyword=y.trim(),_historyState.page=0,clearHistorySelection(),loadHistoryPage()},300)}),document.getElementById("history-search-clear").addEventListener("click",()=>{const l=document.getElementById("history-search");l.value="",_historyState.keyword="",_historyState.page=0,clearHistorySelection(),document.getElementById("history-search-clear").style.display="none",loadHistoryPage(),l.focus()}),document.getElementById("history-range").addEventListener("change",l=>{_historyState.range=parseInt(l.target.value,10),_historyState.page=0,clearHistorySelection(),loadHistoryPage()}),document.getElementById("history-prev").addEventListener("click",()=>{_historyState.page>0&&(_historyState.page--,clearHistorySelection(),loadHistoryPage())}),document.getElementById("history-next").addEventListener("click",()=>{(_historyState.page+1)*_historyState.pageSize<_historyState.total&&(_historyState.page++,clearHistorySelection(),loadHistoryPage())})})();window.openHistoryDrawer=Ne;function Ie(e,n){try{return typeof window.t=="function"?window.t(e):n}catch{return n}}function Te(e){if(e==null||isNaN(e))return"—";try{return String(e).replace(/\B(?=(\d{3})+(?!\d))/g,",")}catch{return String(e)}}function nn(e){if(!e)return"";try{const n=new Date(e).getTime();if(!n)return"";const a=Math.floor((Date.now()-n)/1e3);return a<60?Ie("time-just-now","刚刚"):a<3600?Math.floor(a/60)+Ie("time-min-ago-suffix"," 分钟前"):a<86400?Math.floor(a/3600)+Ie("time-hour-ago-suffix"," 小时前"):Math.floor(a/86400)+Ie("time-day-ago-suffix"," 天前")}catch{return""}}async function et(){gt();const e=document.getElementById("dash-kpi-invoices"),n=document.getElementById("dash-kpi-pending"),a=document.getElementById("dash-kpi-exceptions"),o=document.getElementById("dash-kpi-plan"),s=document.getElementById("dash-kpi-plan-sub"),p=document.getElementById("dash-recent-list"),l=document.getElementById("dash-quick-exc-badge");try{const y={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},[i,r,d]=await Promise.all([fetch("/api/me/tenant-usage",{headers:y}).then(j=>j.ok?j.json():null).catch(()=>null),fetch("/api/history?limit=20",{headers:y}).then(j=>j.ok?j.json():null).catch(()=>null),fetch("/api/exceptions/stats?status=pending",{headers:y}).then(j=>j.ok?j.json():null).catch(()=>null)]),c=i&&i.ocr_this_month||0;let v=0;const x=r&&(r.items||r.history||r)||[],_=Array.isArray(x)?x:[];_.forEach(j=>{(j.status==="pending"||j.status==="reviewing")&&v++});const q=d&&(d.total||d.count||d.pending||0)||0;if(e&&(e.textContent=Te(c)),n&&(n.textContent=Te(v)),a&&(a.textContent=Te(q)),l&&(q>0?(l.style.display="",l.textContent=q):l.style.display="none"),o&&i){const j=i.ocr_this_month||0,k=i.quota||0;o.textContent=Te(j),s&&(s.textContent=k?j+" / "+Te(k)+" 张":Ie("dash-kpi-plan-sub","本月用量"))}if(p)if(_.length===0)p.innerHTML='<div class="dash-recent-empty">'+Ie("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>";else{const j=_.slice(0,5).map(k=>{const B=(k.invoice_no||k.filename||k.id||"").toString(),N=(k.supplier_name||k.buyer_name||k.client_name||k.notes||"").toString(),R=nn(k.created_at||k.upload_time||k.date),F=A=>String(A).replace(/[&<>"']/g,g=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[g]);return'<div class="dash-recent-row"><span class="dash-recent-key" title="'+F(B)+'">'+F(B)+'</span><span class="dash-recent-mid" title="'+F(N)+'">'+F(N)+'</span><span class="dash-recent-time">'+F(R)+"</span></div>"}).join("");p.innerHTML=j}}catch{p&&(p.innerHTML='<div class="dash-recent-empty">'+Ie("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>")}}window.loadDashboard=et;async function gt(){const e=document.getElementById("dash-kpi-balance-card"),n=document.getElementById("dash-kpi-usage-card"),a=document.getElementById("dash-kpi-balance"),o=document.getElementById("dash-kpi-balance-sub"),s=document.getElementById("dash-kpi-usage"),p=document.getElementById("dash-kpi-usage-sub");if(!(!e||!n))try{const l={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},y=await fetch("/api/me/credits",{headers:l,cache:"no-store"});if(!y.ok){e.style.display="none",s&&(s.textContent="—"),p&&(p.textContent="");return}const i=await y.json(),r=!!i.is_owner,d=!!i.is_billing_exempt;if(!r)e.style.display="none";else if(e.style.display="",d)a&&(a.textContent="∞",a.className="dash-kpi-val dash-green"),o&&(o.textContent=typeof window.t=="function"?window.t("dash-kpi-balance-exempt"):"Billing exempt");else{const v=typeof i.balance_thb=="number"?i.balance_thb:0;if(a&&(a.textContent="฿"+v.toFixed(2),a.className=v<50?"dash-kpi-val dash-red":"dash-kpi-val"),o){const x=typeof window.t=="function"?window.t("dash-kpi-balance-topup"):"Top up →",_=v<50?"#dc2626":"#6b7280",q=j=>typeof window.escapeHtml=="function"?window.escapeHtml(j):String(j).replace(/[&<>"']/g,k=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[k]);o.innerHTML='<a href="#" id="kpi-balance-topup-link" style="color:'+_+';text-decoration:underline;cursor:pointer;" onclick="event.preventDefault();window._openTopupModal&&window._openTopupModal();return false;">'+q(x)+"</a>"}}const c=typeof i.pages_this_month=="number"?i.pages_this_month:typeof i.my_invoice_count=="number"?i.my_invoice_count:0;if(n.style.display="",s&&(s.textContent=String(c)),p){const v=c>=200?"dash-kpi-usage-sub-high":"dash-kpi-usage-sub-low",x=typeof window.t=="function"?window.t(v,{used:c}):c+" pages";p.textContent=x}}catch(l){console.warn("[credits] loadCreditsCard failed:",l),e.style.display="none",s&&(s.textContent="—")}}window.loadCreditsCard=gt;document.addEventListener("DOMContentLoaded",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&setTimeout(et,500)});typeof window.subscribeI18n=="function"&&window.subscribeI18n("dashboard",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&et()});function he(e){return(typeof window.t=="function"?window.t(e):null)||e}function tt(){return localStorage.getItem("mrpilot_token")||""}function me(e){return document.getElementById(e)}var qe=null,$e=null;function bt(){$e||($e=setInterval(function(){if(!document.hidden){var e=tt();e&&(window._userInfo&&window._userInfo.is_billing_exempt||fetch("/api/me/credits",{headers:{Authorization:"Bearer "+e},cache:"no-store"}).then(function(n){return n.ok?n.json():null}).then(function(n){if(n){var a=n.balance_thb!=null?Number(n.balance_thb):0;qe!==null&&a>qe&&(window.showToast&&window.showToast(he("credits-updated"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard(),typeof window._refreshBalanceAlerts=="function"&&window._refreshBalanceAlerts()),qe=a}}).catch(function(){}))}},3e4))}function an(){$e&&(clearInterval($e),$e=null),qe=null}window._startCreditsPoll=bt;window._stopCreditsPoll=an;bt();var nt=null,at=0;function on(){if(!me("topup-v2-ov")){var e=document.createElement("div");e.id="topup-v2-ov",e.className="topup-v2-ov",e.style.cssText="display:none;position:fixed;inset:0;background:rgba(15,23,42,.5);z-index:9500;align-items:center;justify-content:center;padding:16px",e.innerHTML=['<div class="topup-v2-box">','  <div class="topup-v2-head">','    <div class="topup-v2-title" id="tv2-title"></div>','    <button class="topup-v2-close" id="tv2-close" aria-label="close">','      <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="4" y1="4" x2="16" y2="16"/><line x1="16" y1="4" x2="4" y2="16"/></svg>',"    </button>","  </div>",'  <div class="topup-v2-steps">','    <div class="topup-v2-step" id="tv2-d1"><span class="topup-v2-dot">1</span><span class="topup-v2-slabel" id="tv2-sl1"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d2"><span class="topup-v2-dot">2</span><span class="topup-v2-slabel" id="tv2-sl2"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d3"><span class="topup-v2-dot">3</span><span class="topup-v2-slabel" id="tv2-sl3"></span></div>',"  </div>",'  <div class="topup-v2-body">','    <div id="tv2-s1">','      <label class="topup-v2-label" id="tv2-al"></label>','      <div class="topup-v2-qamts">','        <button class="topup-v2-qamt" data-val="100">฿100</button>','        <button class="topup-v2-qamt" data-val="500">฿500</button>','        <button class="topup-v2-qamt" data-val="1000">฿1,000</button>','        <button class="topup-v2-qamt" data-val="2000">฿2,000</button>',"      </div>",'      <input id="tv2-amt" type="number" min="10" step="1" class="topup-v2-input" placeholder="฿ ...">','      <div id="tv2-ae" class="topup-v2-err" style="display:none"></div>',"    </div>",'    <div id="tv2-s2" style="display:none">','      <p class="topup-v2-bank-label" id="tv2-bl"></p>','      <div class="topup-v2-bank-card">','        <div class="topup-v2-bank-name">ธนาคาร กรุงเทพ</div>','        <div class="topup-v2-bank-branch">สาขาโชคชัย 4 ลาดพร้าว</div>','        <div class="topup-v2-bank-acct">230-0-91368-4</div>','        <div class="topup-v2-bank-holder">บจ. มิสเตอร์ อี อาร์ พี</div>','        <button class="topup-v2-copy" id="tv2-copy"></button>',"      </div>",'      <div class="topup-v2-warn" id="tv2-bn"></div>',"    </div>",'    <div id="tv2-s3" style="display:none">','      <div class="topup-v2-drop" id="tv2-drop">','        <input type="file" id="tv2-file" accept="image/*,.pdf" style="display:none">','        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>','        <span class="topup-v2-drop-text" id="tv2-dt"></span>',"      </div>",'      <div id="tv2-se" class="topup-v2-err" style="display:none"></div>','      <label class="topup-v2-label" id="tv2-pl"></label>','      <input id="tv2-payer" type="text" maxlength="200" class="topup-v2-input">','      <label class="topup-v2-label" id="tv2-nl"></label>','      <input id="tv2-note" type="text" maxlength="500" class="topup-v2-input">','      <div id="tv2-ue" class="topup-v2-err" style="display:none"></div>',"    </div>","  </div>",'  <div class="topup-v2-foot">','    <button class="btn btn-ghost" id="tv2-back" style="display:none"></button>','    <button class="btn btn-primary" id="tv2-next"></button>',"  </div>","</div>"].join(""),document.body.appendChild(e),sn()}}function yt(){var e=function(n,a){var o=me(n);o&&(o.textContent=a)};e("tv2-title",he("topup-title")),e("tv2-sl1",he("topup-step1")),e("tv2-sl2",he("topup-step2")),e("tv2-sl3",he("topup-step3")),e("tv2-al",he("topup-amount-label")),e("tv2-bl",he("topup-bank-label")),e("tv2-copy",he("topup-copy-account")),e("tv2-dt",he("topup-slip-drop")),e("tv2-pl",he("topup-payer-label")),e("tv2-nl",he("topup-note-label"))}function Ae(e){[1,2,3].forEach(function(s){var p=me("tv2-s"+s);p&&(p.style.display=s===e?"":"none");var l=me("tv2-d"+s);l&&l.classList.toggle("active",s<=e)});var n=me("tv2-back"),a=me("tv2-next");if(e===1?n&&(n.style.display="",n.textContent=he("topup-btn-cancel")):n&&(n.style.display="",n.textContent=he("topup-btn-back")),a&&(a.textContent=he(e===3?"topup-btn-submit":"topup-btn-next")),e===2){var o=me("tv2-bn");o&&(o.innerHTML=he("topup-bank-note").replace("{amount}","<strong>฿"+Number(at).toLocaleString()+"</strong>"))}}function Xe(){for(var e=1;e<=3;e++){var n=me("tv2-s"+e);if(n&&n.style.display!=="none")return e}return 1}function ze(e){var n=me(e);n&&(n.textContent="",n.style.display="none")}function He(e,n){var a=me(e);a&&(a.textContent=n,a.style.display="")}function lt(e){var n=me("tv2-dt");n&&(n.textContent=e.name);var a=me("tv2-drop");a&&a.classList.add("has-file"),ze("tv2-se")}function sn(){var e=me("topup-v2-ov");me("tv2-close").addEventListener("click",Me),e.addEventListener("click",function(p){p.target===e&&Me()}),document.addEventListener("keydown",function(p){p.key==="Escape"&&e&&e.style.display!=="none"&&Me()}),e.addEventListener("click",function(p){var l=p.target.closest(".topup-v2-qamt");if(l){e.querySelectorAll(".topup-v2-qamt").forEach(function(i){i.classList.remove("active")}),l.classList.add("active");var y=me("tv2-amt");y&&(y.value=l.dataset.val,ze("tv2-ae"))}});var n=me("tv2-amt");n&&n.addEventListener("input",function(){e.querySelectorAll(".topup-v2-qamt").forEach(function(p){p.classList.remove("active")}),ze("tv2-ae")});var a=me("tv2-copy");a&&a.addEventListener("click",function(){navigator.clipboard&&navigator.clipboard.writeText("2300913684").then(function(){var p=a.textContent;a.textContent=he("topup-copied"),setTimeout(function(){a.textContent=p},1500)})});var o=me("tv2-drop"),s=me("tv2-file");o&&(o.addEventListener("click",function(){s&&s.click()}),o.addEventListener("dragover",function(p){p.preventDefault(),o.classList.add("drag-over")}),o.addEventListener("dragleave",function(){o.classList.remove("drag-over")}),o.addEventListener("drop",function(p){p.preventDefault(),o.classList.remove("drag-over");var l=p.dataTransfer&&p.dataTransfer.files[0];l&&lt(l)})),s&&s.addEventListener("change",function(){s.files[0]&&lt(s.files[0])}),me("tv2-back").addEventListener("click",function(){var p=Xe();if(p<=1){Me();return}Ae(p-1)}),me("tv2-next").addEventListener("click",function(){var p=Xe();p===1?rn():p===2?Ae(3):ln()})}async function rn(){var e=me("tv2-amt"),n=e?parseFloat(e.value):0;if(!n||n<10){He("tv2-ae",he("topup-amount-invalid"));return}if(n>5e5){He("tv2-ae",he("topup-amount-too-large"));return}at=n;var a=me("tv2-next");a&&(a.disabled=!0,a.textContent="…");try{var o=await fetch("/api/credits/topup/request",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+tt()},body:JSON.stringify({amount_thb:n})});if(!o.ok){var s=await o.text(),p=he("topup-submit-fail");try{var l=JSON.parse(s),y=l.detail;if(Array.isArray(y)&&y.length){var i=y[0]&&y[0].type||"";i.indexOf("less_than")>=0?p=he("topup-amount-too-large"):(i.indexOf("greater_than")>=0||i.indexOf("parsing")>=0)&&(p=he("topup-amount-invalid"))}else typeof y=="string"&&(p=y)}catch{}throw new Error(p)}var r=await o.json();nt=r.request_id,Ae(2)}catch(d){He("tv2-ae",d.message||he("topup-submit-fail"))}finally{a&&(a.disabled=!1,a.textContent=he("topup-btn-next"))}}async function ln(){var e=me("tv2-file");if(!e||!e.files||!e.files[0]){He("tv2-se",he("topup-slip-required"));return}var n=me("tv2-next");n&&(n.disabled=!0,n.textContent="…");try{var a=new FormData;a.append("file",e.files[0]);var o=me("tv2-payer"),s=me("tv2-note");o&&o.value.trim()&&a.append("payer_name",o.value.trim()),s&&s.value.trim()&&a.append("note",s.value.trim());var p=await fetch("/api/credits/topup/upload-slip/"+nt,{method:"POST",headers:{Authorization:"Bearer "+tt()},body:a});if(!p.ok)throw new Error(await p.text());var l=await p.json();l.auto_approved?(window.showToast&&window.showToast(he("topup-auto-approved"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard()):window.showToast&&window.showToast(he("topup-pending"),"info"),Me()}catch(y){He("tv2-ue",he("topup-upload-fail")+" · "+y.message),n&&(n.disabled=!1,n.textContent=he("topup-btn-submit"))}}function Me(){var e=me("topup-v2-ov");e&&(e.style.display="none"),typeof window.loadDashboard=="function"&&window.loadDashboard()}window._openTopupModal=function(){on(),nt=null,at=0,["tv2-amt","tv2-payer","tv2-note"].forEach(function(a){var o=me(a);o&&(o.value="")});var e=me("tv2-file");e&&(e.value="");var n=me("tv2-drop");n&&n.classList.remove("has-file","drag-over"),me("topup-v2-ov").querySelectorAll(".topup-v2-qamt").forEach(function(a){a.classList.remove("active")}),["tv2-ae","tv2-se","tv2-ue"].forEach(function(a){ze(a)}),yt(),Ae(1),me("topup-v2-ov").style.display="flex"};typeof window.subscribeI18n=="function"&&window.subscribeI18n("topup-v2",function(){var e=me("topup-v2-ov");e&&e.style.display!=="none"&&e.style.display!==""&&(yt(),Ae(Xe()))});(function(){const e="v118.28.5",n="pearnly_tc_results_"+e,a=[{id:"A1",group:"A · 异常栏 page-head(BUG1)",desc:"手机宽度进异常栏 · 标题「异常栏」横排正常 · 不再每字一行"},{id:"A2",group:"A · 异常栏 page-head(BUG1)",desc:"副标题「所有被规则拦截的单据集中复核…」也横排正常 · 不竖排"},{id:"A3",group:"A · 异常栏 page-head(BUG1)",desc:"客户筛选下拉 + 刷新按钮换到新一行 · 不抢标题宽度"},{id:"B1",group:"B · 客户管理 page-head(BUG2)",desc:"手机宽度进客户管理 · 标题「客户管理」横排正常"},{id:"B2",group:"B · 客户管理 page-head(BUG2)",desc:"副标题「为每家客户单独归档发票…」横排正常 · 不竖排"},{id:"B3",group:"B · 客户管理 page-head(BUG2)",desc:"「+ 新建客户」按钮换到新一行 · 不挤标题"},{id:"C1",group:"C · 客户卡片(BUG3)",desc:"客户卡片「编辑 / 导出本月」按钮文字清晰 · 不被截断"},{id:"D1",group:"D · 历史表头(BUG4)",desc:"手机宽度进单据记录 · 表头「文件·发票号·供应商」/「金额」单行 · 不竖排"},{id:"D2",group:"D · 历史表头(BUG4)",desc:"行内 INV-TH-202605-1006 这种长发票号正常单行展示 · 不一字一行"},{id:"E1",group:"E · 对账切换器(BUG6)",desc:"手机宽度进对账中心 · 顶栏点「全部客户」chip · 下拉从右上角向下展开 · 右对齐 · 不贴左屏边"},{id:"E2",group:"E · 对账切换器(BUG6)",desc:"下拉宽度自适应屏幕 · 不超出屏幕右边"},{id:"F1",group:"F · 通用设置回归",desc:"设置 → 个人资料 · 没有「界面语言」4 按钮卡"},{id:"F2",group:"F · 通用设置回归",desc:"左侧 nav 顺序:账户 / 公司 / 工作流 / 系统 / 关于"},{id:"F3",group:"F · 通用设置回归",desc:"系统 → 通用设置 · 4 行下拉(语言/时区/日期/数字)· 改语言立即切语言 · 改其他保存后 F5 仍保留"},{id:"G1",group:"G · 移动端 settings(回归)",desc:"手机宽度设置 tabs 不重叠 · 按分组分行 · chip 风格"},{id:"H1",group:"H · 回归",desc:"OCR 上传识别 / 客户管理 / 异常栏 / 对账中心 / 测试中心 全部仍工作"},{id:"H2",group:"H · 回归",desc:"4 语切换没新增异常(测试中心异常日志「API 失败」过滤无新条目)"},{id:"I1",group:"I · 三档移动 viewport",desc:"iPhone SE 375 · 上述 BUG 1-6 都修了"},{id:"I2",group:"I · 三档移动 viewport",desc:"Galaxy S 360 · 上述 BUG 1-6 都修了"},{id:"I3",group:"I · 三档移动 viewport",desc:"iPhone 12 Pro 414 · 上述 BUG 1-6 都修了"}];let o={},s="all",p=!1,l=!1;function y(G,W,te){let re=typeof t=="function"?t(G):null;return(!re||re===G)&&(re=W),te&&Object.keys(te).forEach(function(S){re=String(re).replace("{"+S+"}",String(te[S]))}),re}function i(){try{const G=localStorage.getItem(n);o=G?JSON.parse(G):{},(typeof o!="object"||!o)&&(o={})}catch{o={}}}function r(){try{localStorage.setItem(n,JSON.stringify(o))}catch{}}function d(G){const W=new Date(G),te=function(re){return re<10?"0"+re:""+re};return te(W.getHours())+":"+te(W.getMinutes())+":"+te(W.getSeconds())}function c(G){return String(G??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function v(G,W){try{typeof showToast=="function"?showToast(G,W||"info"):alert(G)}catch{}}function x(G){try{navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(G).then(function(){v(y("tc-toast-copied","已复制到剪贴板"),"success")}).catch(function(){_(G)}):_(G)}catch{_(G)}}function _(G){try{const W=document.createElement("textarea");W.value=G,W.style.position="fixed",W.style.opacity="0",document.body.appendChild(W),W.select();const te=document.execCommand("copy");document.body.removeChild(W),v(te?y("tc-toast-copied","已复制"):y("tc-toast-copy-fail","复制失败"),te?"success":"error")}catch{v(y("tc-toast-copy-fail","复制失败"),"error")}}function q(){const G=document.getElementById("tc-account-chip"),W=document.getElementById("tc-progress-chip");if(G&&(G.textContent=_userInfo&&(_userInfo.email||_userInfo.username)||"—"),W){const te=a.length,re=a.filter(function(S){return o[S.id]}).length;W.textContent=re+" / "+te}}function j(){const G=document.getElementById("tc-checklist-body");if(!G)return;const W={};a.forEach(function(re){W[re.group]||(W[re.group]=[]),W[re.group].push(re)});const te=[];Object.keys(W).forEach(function(re){te.push('<div class="tc-checklist-group">'),te.push('<div class="tc-checklist-group-title">'+c(re)+"</div>"),W[re].forEach(function(S){const w=o[S.id]||"",m=w?"is-"+w:"";te.push('<div class="tc-check-item '+m+'" data-id="'+c(S.id)+'"><div class="tc-check-id">'+c(S.id)+'</div><div class="tc-check-desc">'+c(S.desc)+'</div><div class="tc-check-actions">'+k(S.id,"pass",w)+k(S.id,"fail",w)+k(S.id,"skip",w)+"</div></div>")}),te.push("</div>")}),G.innerHTML=te.join("")}function k(G,W,te){const re=te===W,S={pass:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="4,11 8,15 16,5"/></svg>',fail:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="5" x2="15" y2="15"/><line x1="15" y1="5" x2="5" y2="15"/></svg>',skip:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="10" x2="15" y2="10"/></svg>'},w={pass:y("tc-status-pass","通过"),fail:y("tc-status-fail","失败"),skip:y("tc-status-skip","跳过")};return'<button type="button" class="tc-status-btn '+(re?"is-active "+W:"")+'" data-id="'+c(G)+'" data-kind="'+W+'" title="'+c(w[W])+'">'+S[W]+"</button>"}function B(G){return s==="all"?!0:s==="js_error"?G.type==="js_error"||G.type==="promise_error":s==="api"?G.type==="api_error"||G.type==="api_fail":s==="api_slow"?G.type==="api_slow":s==="console"?G.type==="console_error"||G.type==="console_warn":!0}function N(){const G=document.getElementById("tc-logs-body"),W=document.getElementById("tc-logs-count");if(!G)return;const te=(window._pearnlyTcLogs||[]).slice().reverse(),re=te.filter(B);if(W&&(W.textContent=String(te.length)),re.length===0){G.innerHTML='<div class="tc-logs-empty">'+c(y("tc-logs-empty","暂无异常"))+"</div>";return}const S=re.slice(0,100).map(function(w){const m=typeof w.detail=="object"?JSON.stringify(w.detail,null,2):String(w.detail||"");return'<div class="tc-log-item t-'+c(w.type)+'" data-ts="'+w.ts+'"><span class="tc-log-time">'+d(w.ts)+'</span><span class="tc-log-type">'+c(w.type)+'</span><div class="tc-log-summary">'+c(w.summary)+'<div class="tc-log-detail">'+c(m)+"</div></div></div>"}).join("");G.innerHTML=S,document.querySelectorAll("#tc-logs-filter .tc-filter-chip").forEach(function(w){w.classList.toggle("active",w.getAttribute("data-filter")===s)})}function R(){l||(l=!0,setTimeout(function(){l=!1,currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&N(),F()},200))}window._tcOnNewLog=R;function F(){const G=document.getElementById("nav-test-badge");if(!G)return;const W=(window._pearnlyTcLogs||[]).filter(function(te){return te.type==="js_error"||te.type==="promise_error"||te.type==="api_error"||te.type==="api_fail"||te.type==="console_error"}).length;W>0?(G.style.display="",G.textContent=W>99?"99+":String(W)):G.style.display="none"}function A(){q(),j(),N(),F()}function g(){const G=[],W=new Date,te=_userInfo&&(_userInfo.email||_userInfo.username)||"—";G.push("# Pearnly "+e+" 测试结果"),G.push("- 账号:"+te),G.push("- 时间:"+W.toISOString().replace("T"," ").slice(0,19));const re=a.length,S=a.filter(function(Z){return o[Z.id]==="pass"}).length,w=a.filter(function(Z){return o[Z.id]==="fail"}).length,m=a.filter(function(Z){return o[Z.id]==="skip"}).length,H=re-S-w-m;G.push("- 进度:"+(S+w+m)+" / "+re+" · ✅ "+S+" · ❌ "+w+" · ⏭ "+m+" · 未测 "+H),G.push(""),G.push("| ID | 描述 | 状态 |"),G.push("|---|---|---|"),a.forEach(function(Z){const le=o[Z.id],ie=le==="pass"?"✅":le==="fail"?"❌":le==="skip"?"⏭":"⬜";G.push("| "+Z.id+" | "+Z.desc.replace(/\|/g,"\\|")+" | "+ie+" |")});const D=a.filter(function(Z){return o[Z.id]==="fail"});D.length>0&&(G.push(""),G.push("## ❌ 失败项"),D.forEach(function(Z){G.push("- **"+Z.id+"** · "+Z.desc)}));const J=(window._pearnlyTcLogs||[]).slice(-30).reverse();return J.length>0&&(G.push(""),G.push("## 🔴 异常日志(最近 "+J.length+" 条)"),J.forEach(function(Z){if(G.push("- `"+d(Z.ts)+"` · **"+Z.type+"** · "+Z.summary),Z.detail){let le;try{le=JSON.stringify(Z.detail)}catch{le=String(Z.detail)}le&&le!=="{}"&&G.push("  - "+le.slice(0,600))}})),G.join(`
`)}function f(G){const W=(window._pearnlyTcLogs||[]).slice(-30).reverse();if(W.length===0)return"(暂无异常日志)";const te=["# Pearnly 异常日志(最近 "+W.length+" 条)"],re=_userInfo&&(_userInfo.email||_userInfo.username)||"—";return te.push("- 账号:"+re),te.push("- 当前页:"+(currentRoute||"?")),te.push("- UA:"+navigator.userAgent),te.push(""),W.forEach(function(S){if(te.push("## `"+d(S.ts)+"` · "+S.type),te.push("- "+S.summary),S.detail){te.push("```");try{te.push(JSON.stringify(S.detail,null,2).slice(0,2e3))}catch{te.push(String(S.detail).slice(0,2e3))}te.push("```")}}),te.join(`
`)}function h(){const G=Date.now();fetch("/api/health").then(function(W){const te=Date.now()-G;W.ok?v(y("tc-toast-health-ok","后端健康 ✓ {ms}ms",{ms:te}),"success"):v(y("tc-toast-health-fail","后端无响应")+" ("+W.status+")","error")}).catch(function(){v(y("tc-toast-health-fail","后端无响应"),"error")})}function I(){try{localStorage.removeItem(n),localStorage.removeItem("pearnly_current_client_id"),o={},(window._pearnlyTcLogs||[]).length=0,s="all",window.setCurrentClientId}catch{}A(),v(y("tc-toast-cleared","session 状态已清空"),"success")}function L(){try{fetch("/api/clients",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}).then(function(G){return G.json()}).then(function(G){window._clientsCache=G.clients||[],typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher(),typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter(),v("客户缓存已刷新 · "+(G.clients||[]).length+" 个客户","success")}).catch(function(){v("刷新失败","error")})}catch{}}function $(){if(p||!document.getElementById("page-test-center"))return;p=!0;const W=document.getElementById("tc-checklist-body");W&&W.addEventListener("click",function(le){const ie=le.target.closest(".tc-status-btn");if(!ie)return;const V=ie.getAttribute("data-id"),Q=ie.getAttribute("data-kind");!V||!Q||(o[V]===Q?delete o[V]:o[V]=Q,r(),j(),q())});const te=document.getElementById("tc-btn-reset-checklist");te&&te.addEventListener("click",function(){o={},r(),j(),q()});const re=document.getElementById("tc-btn-copy-all");re&&re.addEventListener("click",function(){x(g())});const S=document.getElementById("tc-btn-copy-logs");S&&S.addEventListener("click",function(){x(f())});const w=document.getElementById("tc-btn-clear-logs");w&&w.addEventListener("click",function(){(window._pearnlyTcLogs||[]).length=0,N(),F()});const m=document.getElementById("tc-logs-filter");m&&m.addEventListener("click",function(le){const ie=le.target.closest(".tc-filter-chip");ie&&(s=ie.getAttribute("data-filter")||"all",N())});const H=document.getElementById("tc-logs-body");H&&H.addEventListener("click",function(le){const ie=le.target.closest(".tc-log-item");ie&&ie.classList.toggle("expanded")});const D=document.getElementById("tc-tool-health");D&&D.addEventListener("click",h);const J=document.getElementById("tc-tool-clear-session");J&&J.addEventListener("click",I);const Z=document.getElementById("tc-tool-reload-clients");Z&&Z.addEventListener("click",L)}function E(){}window._tcApplyVisibility=E;let M=0;const K=setInterval(function(){M++,_userInfo&&clearInterval(K),M>60&&clearInterval(K)},500);window.loadTestCenterPage=function(){i(),$(),A()},typeof window.subscribeI18n=="function"&&window.subscribeI18n("test-center",function(){F(),currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&A()})})();(function(){const e="pearnly_active_workspace_client_id",n="pearnly_work_mode";function a(B,N){if(typeof window.t=="function"){const R=window.t(B);if(R&&R!==B)return R}return N}function o(){const B=window._userInfo||{},N=String(B.role||"").toLowerCase(),R=String(B.tenant_role||"").toLowerCase();return B.is_super_admin===!0||B.is_owner===!0||N==="owner"||N==="admin"||R==="owner"||R==="admin"}function s(){return localStorage.getItem(n)==="client"?"client":"personal"}function p(){const B=localStorage.getItem(e);if(!B||B==="null"||B==="0"||B==="")return null;const N=parseInt(B,10);return isNaN(N)?null:N}function l(B){try{window.dispatchEvent(new CustomEvent("pearnly:workspace-changed",{detail:{id:B,mode:s()}}))}catch{}}function y(B){const N=p();B==null||B===0?localStorage.removeItem(e):(localStorage.setItem(e,String(B)),localStorage.setItem(n,"client")),String(N)!==String(B)&&l(B)}function i(){const B=p();localStorage.setItem(n,"personal"),localStorage.removeItem(e),B!=null&&l(null)}async function r(){try{const B=window.apiGet;if(typeof B!="function")return[];const N=await B("/api/workspace/clients");return N&&(N.clients||N.items)||[]}catch{return[]}}async function d(B){if(s()==="client"&&p()!=null)return typeof B=="function"&&B(),!0;const N=a("ws-need-client","这个功能需要先选择工作空间"),R=a("ws-btn-pick","选择工作空间"),F=a("ws-btn-cancel","取消");return typeof window.showConfirm=="function"?await window.showConfirm(N,{okText:R,cancelText:F})&&c(B):window.confirm(N+`

[`+R+" / "+F+"]")&&c(B),!1}async function c(B){const N=await r();if(typeof B=="function"&&s()!=="personal"&&N.length===1){y(Number(N[0].id)),B();return}if(typeof window.openWorkspaceChooserUI=="function"){window.openWorkspaceChooserUI({clients:N,canCreate:o(),active:p(),onPersonal:i,onPick:function(R){y(Number(R)),typeof B=="function"&&B()},emptyHint:N.length?null:o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。")});return}if(!N.length){const R=o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。");typeof window.showToast=="function"&&window.showToast(R,"info")}}function v(B){const N=B||document.getElementById("workspace-switcher-root");if(!N)return;const R=s(),F=p();let A,g;if(R==="client"&&F!=null){const I=(window._workspaceClientsCache||[]).find(L=>Number(L.id)===Number(F));A=_("building"),g=I?I.name:a("ws-current-label","当前工作空间")}else A=_("user"),g=a("ws-personal","个人事务");N.innerHTML='<button class="ws-ctrl-btn" id="ws-ctrl-btn" type="button">'+A+'<span class="ws-ctrl-label">'+x(g)+"</span></button>";const f=N.querySelector("#ws-ctrl-btn");f&&f.addEventListener("click",()=>c(null))}function x(B){return String(B??"").replace(/[&<>"']/g,function(N){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[N]})}function _(B){const N='<svg class="ws-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';return B==="building"?N+'<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>':N+'<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'}function q(B){B=B||{};const N=B.clients||[],R=B.active,F=document.getElementById("ws-modal");F&&F.remove();const A=document.createElement("div");A.id="ws-modal",A.className="ws-modal";const f='<button type="button" class="ws-modal-item'+(s()==="personal"||R==null?" active":"")+'" data-ws-personal="1"><span class="ws-modal-item-ic">'+_("user")+'</span><span class="ws-modal-item-text" style="display:flex;flex-direction:column;align-items:flex-start;min-width:0;"><span class="ws-modal-item-name">'+x(a("ws-personal","个人事务"))+'</span><span class="ws-modal-item-desc" style="font-size:11px;color:#6b7280;font-weight:400;margin-top:2px;line-height:1.35;white-space:normal;">'+x(a("ws-personal-desc","用于临时识别、测试或处理不归属任何公司的文件。"))+"</span></span></button>";let h="";if(N.length){const M=['<option value="">'+x(a("ws-select-ph","— 选择账套主体 —"))+"</option>"].concat(N.map(function(K){const G=R!=null&&Number(R)===Number(K.id);return'<option value="'+x(K.id)+'"'+(G?" selected":"")+">"+x(K.name||"#"+K.id)+"</option>"}));h='<div class="ws-modal-select-row"><label class="ws-modal-select-label">'+x(a("ws-select-label","账套主体"))+'</label><select class="ws-modal-select" data-ws-select="1">'+M.join("")+"</select></div>"}const I=!N.length&&B.emptyHint?'<div class="ws-modal-empty">'+x(B.emptyHint)+"</div>":"",L=B.canCreate?'<div class="ws-modal-create"><button type="button" class="ws-modal-create-toggle" data-ws-create-toggle="1">+ '+x(a("ws-create-client","新建工作空间"))+'</button><div class="ws-modal-create-form" data-ws-create-form style="display:none;"><input type="text" class="ws-modal-create-input" data-ws-create-name placeholder="'+x(a("ws-create-ph","公司名称,例如 BAKELAB"))+'"><button type="button" class="ws-modal-create-submit" data-ws-create-submit="1">'+x(a("ws-create-submit","创建"))+"</button></div></div>":"";A.innerHTML='<div class="ws-modal-box" role="dialog" aria-modal="true"><div class="ws-modal-head"><span class="ws-modal-title">'+x(a("ws-chooser-title","选择工作空间"))+'</span><button type="button" class="ws-modal-close" data-ws-close="1" aria-label="close">✕</button></div><div class="ws-modal-subtitle" style="font-size:12px;color:#6b7280;padding:2px 4px 12px;line-height:1.45;white-space:normal;">'+x(a("ws-chooser-subtitle","账套主体 = 你的公司(发票卖方/开票方)。选择正在为哪家公司做账。"))+'</div><div class="ws-modal-list">'+f+h+"</div>"+I+L+"</div>",document.body.appendChild(A);const $=A.querySelector("[data-ws-select]");$&&$.addEventListener("change",function(){const M=$.value;M&&(typeof B.onPick=="function"&&B.onPick(M),E(),v())});function E(){A.remove()}A.addEventListener("click",function(M){if(M.target===A||M.target.closest("[data-ws-close]")){E();return}if(M.target.closest("[data-ws-personal]")){typeof B.onPersonal=="function"&&B.onPersonal(),E(),v();return}const G=M.target.closest("[data-ws-pick]");if(G){const re=G.getAttribute("data-ws-pick");typeof B.onPick=="function"&&B.onPick(re),E(),v();return}if(M.target.closest("[data-ws-create-toggle]")){const re=A.querySelector("[data-ws-create-form]");if(re){re.style.display=re.style.display==="none"?"flex":"none";const S=re.querySelector("[data-ws-create-name]");S&&S.focus()}return}if(M.target.closest("[data-ws-create-submit]")){j(A,B,E);return}})}async function j(B,N,R){const F=B.querySelector("[data-ws-create-name]"),A=F?(F.value||"").trim():"";if(!A){F&&F.focus();return}let g=null;try{if(typeof window.apiPost=="function"){const h=await window.apiPost("/api/workspace/clients",{name:A});g=h&&typeof h.json=="function"?await h.json().catch(()=>null):h}}catch{g=null}const f=g&&(g.id||g.client&&g.client.id);if(!f){typeof window.showToast=="function"&&window.showToast(a("ws-create-fail","新建工作空间失败 · 请重试"),"error");return}window._workspaceClientsCache=await r(),y(Number(f)),N.onPick,R(),v()}window.openWorkspaceChooserUI=q,window.addEventListener("pearnly:workspace-changed",function(){v()}),window.getWorkMode=s,window.getActiveWorkspaceClientId=p,window.setActiveWorkspaceClientId=y,window.enterPersonalMode=i,window.requireWorkspace=d,window.openWorkspaceChooser=c,window.renderWorkspaceControl=v,window.fetchWorkspaceClients=r;function k(){try{if(sessionStorage.getItem("pearnly_ws_login_prompted")==="1"||p()!=null||localStorage.getItem(n)==="personal")return;sessionStorage.setItem("pearnly_ws_login_prompted","1"),setTimeout(function(){c(null)},800)}catch{}}r().then(B=>{window._workspaceClientsCache=B,v(),k()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("workspace-switcher",v)})();(function(){const e=R=>document.querySelector('[data-num-target="'+R+'"]');function n(R){if(!R)return t("reconcile-last-activity-none");try{const F=new Date(R),A=new Date,g=A-F;if(g/6e4<5)return t("reconcile-last-activity-just-now");if(F.toDateString()===A.toDateString())return t("reconcile-last-activity-today");const h=Math.max(1,Math.floor(g/(24*3600*1e3)));return t("reconcile-last-activity-days-ago").replace("{n}",h)}catch{return t("reconcile-last-activity-none")}}function a(R,F,A){const g=e(R);g&&(g.textContent=A?"-":String(F),g.classList.toggle("is-empty",!!A))}function o(R){const F=document.getElementById("reconcile-error");F&&(F.style.display=R?"flex":"none")}function s(R){const F=document.getElementById("reconcile-empty");F&&(F.style.display=R?"flex":"none")}function p(R,F){const A=document.getElementById("reconcile-last-activity");A&&(A.textContent=R,A.classList.toggle("has-data",!!F))}function l(R){const F=!R||(R.total_sessions||0)===0;a("pending",R.pending||0,F),a("matched",R.matched||0,F),a("unmatched",R.unmatched||0,F),p(n(R.last_activity_at),!!R.last_activity_at),o(!1),s(F)}function y(R){const F=R.toUpperCase();return F==="KBANK"?"bank-chip-kbank":F==="SCB"?"bank-chip-scb":F==="BBL"?"bank-chip-bbl":F==="KTB"?"bank-chip-ktb":F==="TTB"?"bank-chip-ttb":"bank-chip-other"}function i(R,F){const A=g=>g?String(g).slice(0,10):"?";return!R&&!F?"":A(R)+" ~ "+A(F)}function r(R){return R==null?"":String(R).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function d(R){const F=document.getElementById("reconcile-recent"),A=document.getElementById("reconcile-recent-list");if(!F||!A)return;const g=(R||[]).slice(0,20);if(g.length===0){F.style.display="none";return}F.style.display="",s(!1),A.innerHTML=g.map(f=>{const h=f.parse_status==="parse_failed",I=f.bank_code||"OTHER",L=f.account_last4?" ···"+r(f.account_last4):"",$=i(f.period_start,f.period_end),E=r(f.source_filename||""),M=Number(f.tx_count||0),K=h?'<span class="recon-card-fail" data-i18n="reconcile-card-parse-failed">'+t("reconcile-card-parse-failed")+"</span>":'<span class="recon-card-tx">'+t("reconcile-card-tx").replace("{n}",M)+"</span>";return'<div class="recon-card" data-session-id="'+r(f.id)+'" data-session-name="'+E+'"><span class="bank-chip '+y(I)+'">'+r(I)+'</span><div class="recon-card-main"><div class="recon-card-title">'+E+L+'</div><div class="recon-card-sub">'+r($)+'</div></div><div class="recon-card-right">'+K+'</div><button class="recon-card-trash" data-trash="'+r(f.id)+'" title="'+r(t("bank-session-delete-tip")||"删除")+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/></svg></button><svg class="recon-card-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg></div>'}).join(""),A.querySelectorAll(".recon-card").forEach(f=>{f.addEventListener("click",h=>{h.target.closest(".recon-card-trash")||(f.dataset.sessionId,c())})}),A.querySelectorAll(".recon-card-trash").forEach(f=>{f.addEventListener("click",h=>{h.stopPropagation();const I=f.dataset.trash,L=f.closest(".recon-card"),$=L&&L.dataset.sessionName||"";typeof window._deleteBankSession=="function"&&window._deleteBankSession(I,$)})})}function c(R){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const F=document.querySelector('[data-recon-tab="bank"]');F&&F.click()},150)}function v(){o(!0),s(!1)}function x(){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const R=document.querySelector('[data-recon-tab="bank"]');R&&R.click()},150)}async function _(){a("pending",0,!0),a("matched",0,!0),a("unmatched",0,!0),p("",!1),o(!1),s(!1);const R=document.getElementById("reconcile-recent");R&&(R.style.display="none");const F={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")};try{const[A,g]=await Promise.all([fetch("/api/bank-recon/stats",{headers:F}),fetch("/api/bank-recon/sessions?limit=20",{headers:F})]);if(!A.ok)throw new Error("http "+A.status);const f=await A.json(),h=g.ok?await g.json():[];l(f||{}),d(h||[])}catch(A){console.warn("[reconcile] load failed",A),v()}}function q(R){if(!R||!R.length)return;const F="Bearer "+(localStorage.getItem("mrpilot_token")||"");let A=0;const g=R.length;Array.from(R).forEach(function(f){const h=new FormData;h.append("file",f,f.name);const I=new XMLHttpRequest;I.open("POST","/api/bank-recon/upload"),I.setRequestHeader("Authorization",F),I.onload=function(){A++;try{const L=JSON.parse(I.responseText);I.status===200&&L.tx_count!==void 0?showToast((t("bank-upload-ok")||"解析成功 · 共 {n} 条流水").replace("{n}",L.tx_count),"success"):showToast(f.name+" "+(t("upload-failed")||"上传失败"),"error")}catch{showToast(f.name+" "+(t("upload-failed")||"上传失败"),"error")}A===g&&setTimeout(_,600)},I.onerror=function(){A++,showToast(f.name+" "+(t("upload-failed")||"上传失败"),"error"),A===g&&setTimeout(_,600)},I.send(h)}),showToast((t("bank-queue-status-uploading")||"上传中")+"…","info")}function j(){if(window.__reconcileBound)return;window.__reconcileBound=!0;const R=document.getElementById("reconcile-bank-file-input");R&&R.addEventListener("change",function(){q(this.files),this.value=""}),document.addEventListener("click",F=>{if(F.target.closest("#btn-reconcile-upload-top")||F.target.closest("#btn-reconcile-upload-empty")){x();return}if(F.target.closest("#btn-reconcile-retry")){_();return}if(F.target.closest("#btn-reconcile-dev-seed")){N();return}})}const k=["468b50c1-5593-4fd6-990d-515ce8085563"];function B(){const R=document.getElementById("btn-reconcile-dev-seed");if(!R)return;const F=typeof _userInfo<"u"?_userInfo:null,A=F&&F.id&&k.indexOf(String(F.id))>=0;R.style.display=A?"":"none"}async function N(){try{const R=await fetch("/api/bank-recon/_dev/seed",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!R.ok)throw new Error("seed:"+R.status);const F=await R.json(),A=(t("reconcile-dev-seed-ok")||"").replace("{n}",F.tx_count||0);showToast(A,"success"),typeof window.navigateTo=="function"?window.navigateTo("automation"):location.hash="#/automation",setTimeout(()=>{const g=document.querySelector('[data-auto-tab="bank"]');g&&g.click(),F.session_id&&typeof window._openBankSession=="function"&&window._openBankSession(F.session_id)},300)}catch(R){console.warn("[reconcile] dev seed failed",R),showToast(t("reconcile-dev-seed-fail")||"Seed failed","error")}}window.loadReconcilePage=async function(){j(),B(),typeof window._bankReconV2Init=="function"&&window._bankReconV2Init();try{await _()}catch{}},window._rerenderReconcile=function(){typeof currentRoute=="string"&&currentRoute==="reconcile"&&_().catch(()=>{})},typeof window.subscribeI18n=="function"&&window.subscribeI18n("reconcile",window._rerenderReconcile)})();(function(){const e=document.getElementById("assign-clients-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
    </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e={employeeId:null,employeeName:"",clients:[],selected:new Set,opened:!1};function n(){return document.getElementById("assign-clients-modal")}function a(){return document.getElementById("assign-clients-list")}function o(){return document.getElementById("assign-select-all")}function s(){return document.getElementById("assign-selected-count")}function p(){return document.getElementById("assign-modal-target")}function l(){const _=a();if(_){if(!e.clients.length){_.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-no-clients")||"暂无客户 · 请先到「客户管理」添加")+"</div>";return}_.innerHTML=e.clients.map(q=>{const j=String(q.id),k=e.selected.has(j)?"checked":"",B=escapeHtml(q.name||q.label||"#"+j),N=q.code?'<span class="assign-row-code">'+escapeHtml(q.code)+"</span>":"";return'<label class="assign-row"><input type="checkbox" data-cid="'+escapeHtml(j)+'" '+k+'><span class="assign-row-name">'+B+"</span>"+N+"</label>"}).join(""),y()}}function y(){const _=s();if(_){const j=t("assign-selected-count")||"已选 {n} / {total}";_.textContent=j.replace("{n}",e.selected.size).replace("{total}",e.clients.length)}const q=o();q&&(q.checked=e.clients.length>0&&e.selected.size===e.clients.length)}function i(){const _=p();_&&(_.textContent=e.employeeName?" · "+e.employeeName:"")}async function r(_,q){e.employeeId=_,e.employeeName=q||"",e.opened=!0,e.selected=new Set,e.clients=[],i();const j=a();j&&(j.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-loading")||"加载中...")+"</div>");const k=n();k&&(k.style.display="flex");try{const[B,N]=await Promise.all([apiGet("/api/clients?include_inactive=false"),apiGet("/api/team/employees/"+encodeURIComponent(_)+"/assignments")]);e.clients=B&&B.clients||[];const R=N&&N.client_ids||[];e.selected=new Set(R.map(String)),l()}catch(B){console.error("[assign-clients] load failed",B);const N=a();N&&(N.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-load-failed")||"加载失败 · 请重试")+"</div>")}}function d(){e.opened=!1;const _=n();_&&(_.style.display="none")}async function c(){if(!e.employeeId)return;const _=Array.from(e.selected).map(j=>parseInt(j,10)).filter(j=>!isNaN(j)),q=document.getElementById("assign-modal-save");q&&(q.disabled=!0);try{const j=await apiPost("/api/team/employees/"+encodeURIComponent(e.employeeId)+"/assignments",{client_ids:_});j&&j.ok!==!1?(showToast((t("assign-saved")||"已保存 {n} 个客户分配").replace("{n}",_.length),"success"),d(),typeof loadTeamList=="function"&&loadTeamList()):showToast(t("assign-save-failed")||"保存失败","error")}catch(j){console.error("[assign-clients] save failed",j),showToast(t("assign-save-failed")||"保存失败","error")}finally{q&&(q.disabled=!1)}}function v(){const _=n();if(!_||_.dataset.bound==="1")return;_.dataset.bound="1";const q=document.getElementById("assign-modal-close");q&&q.addEventListener("click",d);const j=document.getElementById("assign-modal-cancel");j&&j.addEventListener("click",d);const k=document.getElementById("assign-modal-save");k&&k.addEventListener("click",c),_.addEventListener("click",function(R){R.target===_&&d()});const B=o();B&&B.addEventListener("change",function(){B.checked?e.selected=new Set(e.clients.map(R=>String(R.id))):e.selected=new Set,l()});const N=a();N&&N.addEventListener("change",function(R){const F=R.target.closest('input[type="checkbox"][data-cid]');if(!F)return;const A=F.dataset.cid;F.checked?e.selected.add(A):e.selected.delete(A),y()})}function x(){e.opened&&(i(),l())}typeof window.subscribeI18n=="function"&&window.subscribeI18n("assign-clients-modal",x),window.openAssignClientsModal=function(_,q){v(),r(_,q)}})();(function(){const e={page:1,per_page:50,q:"",total:0,rows:[],loaded:!1};function n(d){if(!d)return"";try{return new Date(d).toLocaleString()}catch{return d}}function a(d){const c=document.getElementById("access-log-table");c&&(c.innerHTML='<div class="access-log-empty">'+escapeHtml(d)+"</div>");const v=document.getElementById("access-log-pager");v&&(v.innerHTML="")}function o(){const d=document.getElementById("access-log-table");if(!d)return;const c=e.rows||[];if(!c.length){a(t("set-access-log-empty"));return}const v=`
            <div class="access-log-row access-log-head">
                <div>${escapeHtml(t("set-access-log-col-time"))}</div>
                <div>${escapeHtml(t("set-access-log-col-actor"))}</div>
                <div>${escapeHtml(t("set-access-log-col-action"))}</div>
                <div>${escapeHtml(t("set-access-log-col-target"))}</div>
                <div>${escapeHtml(t("set-access-log-col-ip"))}</div>
            </div>`,x=c.map(function(_){return`
                <div class="access-log-row">
                    <div class="access-log-time" data-label="${escapeHtml(t("set-access-log-col-time"))}">${escapeHtml(n(_.created_at))}</div>
                    <div class="access-log-actor" data-label="${escapeHtml(t("set-access-log-col-actor"))}">${escapeHtml(_.actor_username||"-")}</div>
                    <div data-label="${escapeHtml(t("set-access-log-col-action"))}"><span class="access-log-action">${escapeHtml(_.action||"-")}</span></div>
                    <div class="access-log-target" data-label="${escapeHtml(t("set-access-log-col-target"))}">${escapeHtml(_.target_name||_.target_type||"-")}</div>
                    <div class="access-log-ip" data-label="${escapeHtml(t("set-access-log-col-ip"))}">${escapeHtml(_.ip||"-")}</div>
                </div>`}).join("");d.innerHTML=v+x}function s(){const d=document.getElementById("access-log-pager");if(!d)return;const c=e.total||0;if(!c){d.innerHTML="";return}const v=e.page||1,x=e.per_page,_=Math.max(1,Math.ceil(c/x)),q=(t("set-access-log-pager-total")||"Total {n}").replace("{n}",c),j=(t("set-access-log-pager-page")||"Page {p} / {t}").replace("{p}",v).replace("{t}",_);d.innerHTML=`
            <div class="access-log-pager-info">${escapeHtml(q)}</div>
            <div class="access-log-pager-ctrl">
                <button class="access-log-pager-btn" type="button" data-access-log-page="${v-1}" ${v<=1?"disabled":""}>← ${escapeHtml(t("set-access-log-pager-prev"))}</button>
                <span class="access-log-pager-page">${escapeHtml(j)}</span>
                <button class="access-log-pager-btn" type="button" data-access-log-page="${v+1}" ${v>=_?"disabled":""}>${escapeHtml(t("set-access-log-pager-next"))} →</button>
            </div>`}async function p(d){const c=localStorage.getItem("mrpilot_token");if(c){e.page=d||1,a(t("set-access-log-loading"));try{const v="/api/me/access_log?page="+e.page+"&per_page="+e.per_page+"&q="+encodeURIComponent(e.q||""),x=await fetch(v,{headers:{Authorization:"Bearer "+c}});if(x.status===403){a(t("set-access-log-empty"));return}if(!x.ok)throw new Error("http_"+x.status);const _=await x.json();e.rows=_.logs||[],e.total=_.total||0,e.loaded=!0,o(),s()}catch{a(t("set-access-log-fail"))}}}async function l(){const d=localStorage.getItem("mrpilot_token");if(d)try{const c="/api/me/access_log.csv?q="+encodeURIComponent(e.q||""),v=await fetch(c,{headers:{Authorization:"Bearer "+d}});if(!v.ok){showToast(t("set-access-log-csv-fail")||"Export failed","error");return}const x=await v.blob(),_=document.createElement("a"),q=URL.createObjectURL(x);_.href=q,_.download="pearnly_access_log.csv",document.body.appendChild(_),_.click(),setTimeout(function(){URL.revokeObjectURL(q),_.remove()},100),showToast(t("set-access-log-csv-ok")||"Exported","success")}catch{showToast(t("set-access-log-csv-fail")||"Export failed","error")}}function y(){const d=document.querySelectorAll(".set-tab-owner-only"),c=!!(_userInfo&&(_userInfo.role==="owner"||_userInfo.is_super_admin));d.forEach(function(v){v.style.display=c?"":"none"})}document.addEventListener("click",function(d){if(d.target.closest('.settings-tab[data-tab="access-log"]')){setTimeout(function(){(!e.loaded||e.page!==1)&&p(1)},50);return}if(d.target.closest("#access-log-csv-btn")){d.preventDefault(),l();return}const x=d.target.closest(".access-log-pager-btn[data-access-log-page]");if(x&&!x.disabled){const _=parseInt(x.dataset.accessLogPage,10);p(_)}}),document.addEventListener("input",function(d){d.target&&d.target.id==="access-log-search"&&(clearTimeout(window.__accessLogSearchTimer),window.__accessLogSearchTimer=setTimeout(function(){e.q=(d.target.value||"").trim(),p(1)},350))});let i=0;const r=setInterval(function(){i++,_userInfo&&(y(),clearInterval(r)),i>60&&clearInterval(r)},500);typeof window.subscribeI18n=="function"&&window.subscribeI18n("me-access-log",function(){y(),e.loaded&&(o(),s())})})();(function(){const e=document.getElementById("notif-new-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=A=>document.getElementById(A);async function n(A,g){return await fetch(A,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(g||{})})}async function a(A){return await fetch(A,{method:"DELETE",headers:{Authorization:"Bearer "+token}})}let o=null;async function s(){try{o=await apiGet("/api/line/binding")}catch{o={bound:!1}}return o}function p(A,g){if(!A)return;A.style.display="",A.className="notif-line-check "+(g?"bound":"unbound");const f=g?'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>';A.innerHTML=f+"<span>"+escapeHtml(t(g?"notif-line-bound":"notif-line-not-bound"))+"</span>"}function l(A){if(A==null)return"-";const g=Number(A);return isNaN(g)?String(A):"฿ "+g.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function y(A){if(!A)return"-";try{const g=new Date(A),f=(g.getMonth()+1).toString().padStart(2,"0"),h=g.getDate().toString().padStart(2,"0"),I=g.getHours().toString().padStart(2,"0"),L=g.getMinutes().toString().padStart(2,"0");return`${f}-${h} ${I}:${L}`}catch{return A}}function i(A){const g=e("notif-rules-list"),f=e("notif-rules-empty"),h=e("notif-rules-count");if(!(!g||!f)){if(h.textContent=String(A.length),h.className="auto-status-pill "+(A.length>0?"active":"none"),!A.length){f.style.display="",g.style.display="none",g.innerHTML="";return}f.style.display="none",g.style.display="",g.innerHTML=A.map(I=>{const L=I.template_code==="large_invoice",$=L?"notif-rule-large-tag":"notif-rule-exception-tag",E=L?"large":"";let M=[];if(L){const G=I.params&&I.params.threshold?l(I.params.threshold):"-";M.push(escapeHtml(t("notif-rule-threshold-prefix"))+" "+G)}I.enabled||M.push('<span style="color:#9ca3af;">'+escapeHtml(t("notif-rule-disabled"))+"</span>");const K=M.length?M.join(' <span class="dot"></span> '):"";return`
                <div class="notif-rule-row${I.enabled?"":" disabled"}" data-rule-id="${I.id}">
                    <span class="notif-rule-tmpl-badge ${E}">${escapeHtml(t($))}</span>
                    <div class="notif-rule-main">
                        <div class="notif-rule-name">${escapeHtml(I.name)}</div>
                        <div class="notif-rule-meta">${K}</div>
                    </div>
                    <div class="notif-rule-actions">
                        <button class="notif-rule-toggle ${I.enabled?"on":""}" data-action="toggle" aria-label="toggle"></button>
                        <button class="notif-rule-btn" data-action="test">${escapeHtml(t("notif-action-test"))}</button>
                        <button class="notif-rule-btn danger" data-action="delete">${escapeHtml(t("notif-action-delete"))}</button>
                    </div>
                </div>`}).join("")}}function r(A){const g=e("notif-logs-list");if(g){if(!A.length){g.innerHTML='<div class="notif-logs-empty">'+escapeHtml(t("notif-logs-empty"))+"</div>";return}g.innerHTML=A.map(f=>{const h=f.status==="sent",I=f.event_type==="exception_high"?"notif-event-exception-high":f.event_type==="large_invoice"?"notif-event-large-invoice":"notif-event-test-send",L=h?"":" · "+escapeHtml(f.error||"failed");return`
                <div class="notif-log-row">
                    <span class="notif-log-status ${h?"":"failed"}"></span>
                    <div class="notif-log-main">
                        <div class="notif-log-event">${escapeHtml(t(I))}</div>
                        <div class="notif-log-meta">${escapeHtml(f.template_code||"-")}${L}</div>
                    </div>
                    <div class="notif-log-time">${y(f.sent_at)}</div>
                </div>`}).join("")}}async function d(){try{const A=await apiGet("/api/notifications/rules");c=A&&A.items||[],i(c)}catch(A){console.warn("load rules fail",A)}try{const A=await apiGet("/api/notifications/logs?limit=20");v=A&&A.items||[],r(v)}catch(A){console.warn("load logs fail",A)}}let c=null,v=null;function x(){c&&i(c),v&&r(v);const A=e("notif-new-modal");A&&A.style.display!=="none"&&o&&p(e("notif-line-check"),!!(o&&o.bound))}function _(){const A=e("notif-new-modal");A&&(A.style.display="",e("notif-new-name").value="",e("notif-new-threshold").value="",e("notif-new-threshold-row").style.display="none",document.querySelectorAll('input[name="notif-template"]').forEach(g=>g.checked=!1),s().then(g=>p(e("notif-line-check"),!!(g&&g.bound))))}function q(){const A=e("notif-new-modal");A&&(A.style.display="none")}function j(){const A=document.querySelector('input[name="notif-template"]:checked'),g=e("notif-new-threshold-row");if(!A){g.style.display="none";return}g.style.display=A.value==="large_invoice"?"":"none";const f=e("notif-new-name");f&&!f.value.trim()&&(f.value=A.value==="large_invoice"?t("notif-tmpl-large-name"):t("notif-tmpl-exception-name"))}async function k(){const A=document.querySelector('input[name="notif-template"]:checked');if(!A){showToast(t("notif-new-template"),"error");return}const g=(e("notif-new-name").value||"").trim();if(!g){showToast(t("notif-name-required"),"error");return}const f={name:g,template_code:A.value,params:{},enabled:!0};if(A.value==="large_invoice"){const h=parseFloat(e("notif-new-threshold").value||"0");if(!h||h<=0){showToast(t("notif-threshold-required"),"error");return}f.params.threshold=h}try{const h=await apiPost("/api/notifications/rules",f);if(h&&h.ok)showToast(t("notif-toast-created"),"success"),q(),d();else{const I=await(h&&h.json&&h.json().catch(()=>({})))||{};showToast(I&&I.detail||"save failed","error")}}catch{showToast("save failed","error")}}async function B(A,g,f){if(A==="toggle"){const h=f.classList.contains("on"),I=await n("/api/notifications/rules/"+g,{enabled:!h});I&&I.ok?(showToast(t(h?"notif-toast-toggled-off":"notif-toast-toggled-on"),"success"),d()):showToast("toggle failed","error");return}if(A==="test"){const h=await s();if(!h||!h.bound){showToast(t("notif-line-error-bind-first"),"error");return}const I=await apiPost("/api/notifications/rules/"+g+"/test",{});if(I&&I.ok)showToast(t("notif-toast-test-sent"),"success"),d();else{const L=await(I&&I.json&&I.json().catch(()=>({})))||{},$=L&&L.detail||"";showToast($||t("notif-toast-test-failed"),"error"),d()}return}if(A==="delete"){if(!await showConfirm(t("notif-confirm-delete"),{danger:!0}))return;const I=await a("/api/notifications/rules/"+g);I&&I.ok?(showToast(t("notif-toast-deleted"),"success"),d()):showToast("delete failed","error");return}}let N=!1;function R(){if(N)return;N=!0;const A=e("notif-btn-new");A&&A.addEventListener("click",_);const g=e("notif-btn-refresh-logs");g&&g.addEventListener("click",d);const f=e("notif-new-close");f&&f.addEventListener("click",q);const h=e("notif-new-cancel");h&&h.addEventListener("click",q);const I=e("notif-new-save");I&&I.addEventListener("click",k),document.querySelectorAll('input[name="notif-template"]').forEach(E=>{E.addEventListener("change",j)});const L=e("notif-rules-list");L&&L.addEventListener("click",E=>{const M=E.target.closest("button[data-action]");if(!M)return;const K=M.closest("[data-rule-id]");K&&B(M.getAttribute("data-action"),K.getAttribute("data-rule-id"),M)});const $=e("notif-new-modal");$&&$.addEventListener("click",E=>{E.target===$&&q()})}async function F(){R(),await d()}window._loadNotificationsPanel=F,window._rerenderNotifications=x})();(function(){function n(k,B){try{return window.t&&window.t(k)||B}catch{return B}}function a(){var k="";try{k=localStorage.getItem("mrpilot_token")||""}catch{}return k?{Authorization:"Bearer "+k}:{}}var o=[{tbody:"vex-task-tbody",api:"/api/recon/tasks/batch_delete",reload:function(){try{window.loadRecentTasks&&window.loadRecentTasks()}catch{}},kind:"vex"},{tbody:"glv-history-tbody",api:"/api/recon/gl-vat/tasks/batch_delete",reload:function(){try{window._loadGlvHistory&&window._loadGlvHistory()}catch{}},kind:"glv"},{tbody:"brv2-history-tbody",api:"/api/recon/bank-v2/tasks/batch_delete",reload:function(){try{window._brv2LoadHistory&&window._brv2LoadHistory()}catch{}},kind:"brv2"}];function s(){if(!document.getElementById("recon-batch-style")){var k=document.createElement("style");k.id="recon-batch-style",k.textContent=".recon-sel-cell{width:36px;text-align:center;padding-left:10px!important;padding-right:6px!important}.recon-sel-cb,.recon-master-cb{cursor:pointer;width:14px;height:14px;accent-color:#111;margin:0;vertical-align:middle}th.recon-time-col,td.recon-time-col{white-space:nowrap}tr.recon-thead-batch{display:none}thead.recon-batch-mode tr.recon-thead-default{display:none}thead.recon-batch-mode tr.recon-thead-batch{display:table-row}tr.recon-thead-batch th{background:#fafaf8;border-bottom:1px solid #e8e8e3;padding:8px 12px}tr.recon-thead-batch .recon-batch-inline{display:flex;align-items:center;gap:10px;font-size:12px;color:#111;font-weight:normal}tr.recon-thead-batch .recon-batch-count-inline{font-weight:600;color:#111;margin-right:4px}tr.recon-thead-batch .recon-batch-del-inline{background:#dc2626;color:#fff;border:none;border-radius:6px;padding:4px 10px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:4px}tr.recon-thead-batch .recon-batch-del-inline:hover{background:#b91c1c}tr.recon-thead-batch .recon-batch-clear-inline{background:transparent;border:none;color:#555;cursor:pointer;font-size:12px;font-family:inherit;text-decoration:underline;padding:4px 2px}tr.recon-thead-batch .recon-batch-clear-inline:hover{color:#111}.recon-batch-bar{display:none!important}",document.head.appendChild(k)}}function p(k){return k?k.dataset&&k.dataset.taskId?k.dataset.taskId:k.dataset&&k.dataset.taskid?k.dataset.taskid:"":""}function l(k){var B=document.getElementById(k.tbody);if(!B)return null;var N=B.closest("table");if(!N)return null;var R=N.querySelector("thead");if(!R)return null;if(R._reconReady)return R;var F=R.querySelector("tr");if(!F)return null;if(F.classList.add("recon-thead-default"),!F.querySelector(".recon-master-cb")){var A=document.createElement("th");A.className="recon-sel-cell";var g=document.createElement("input");g.type="checkbox",g.className="recon-master-cb",g.setAttribute("aria-label","select all"),g.addEventListener("change",function(){d(k,g.checked)}),A.appendChild(g),F.insertBefore(A,F.firstElementChild)}var f=F.children[1];f&&!f.classList.contains("recon-time-col")&&f.classList.add("recon-time-col");var h=F.children.length,I=document.createElement("tr");I.className="recon-thead-batch";var L=document.createElement("th");L.className="recon-sel-cell";var $=document.createElement("input");$.type="checkbox",$.className="recon-master-cb",$.checked=!0,$.setAttribute("aria-label","select all"),$.addEventListener("change",function(){d(k,$.checked)}),L.appendChild($);var E=document.createElement("th");return E.setAttribute("colspan",String(h-1)),E.innerHTML='<div class="recon-batch-inline"><span class="recon-batch-count-inline" data-recon-count></span><button type="button" class="recon-batch-del-inline" data-recon-del><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg><span data-recon-del-label></span></button><button type="button" class="recon-batch-clear-inline" data-recon-clear></button></div>',I.appendChild(L),I.appendChild(E),R.appendChild(I),E.querySelector("[data-recon-del]").addEventListener("click",function(){_(k)}),E.querySelector("[data-recon-clear]").addEventListener("click",function(){x(k)}),R._reconReady=!0,v(k),R}function y(k){var B=document.getElementById(k.tbody);if(B){var N=B.querySelectorAll("tr");N.forEach(function(R){var F=p(R);if(F&&!R.querySelector(".recon-sel-cb")){var A=R.querySelector("td");if(A){var g=document.createElement("td");g.className="recon-sel-cell";var f=document.createElement("input");f.type="checkbox",f.className="recon-sel-cb",f.dataset.taskId=F,f.dataset.kind=k.kind,f.addEventListener("click",function(I){I.stopPropagation()}),f.addEventListener("change",function(){c(k)}),g.appendChild(f),R.insertBefore(g,A);var h=R.children[1];h&&!h.classList.contains("recon-time-col")&&h.classList.add("recon-time-col")}}}),c(k)}}function i(k){var B=document.getElementById(k.tbody);return B?Array.prototype.slice.call(B.querySelectorAll(".recon-sel-cb")):[]}function r(k){return i(k).filter(function(B){return B.checked}).map(function(B){return B.dataset.taskId})}function d(k,B){i(k).forEach(function(N){N.checked=!!B}),c(k)}function c(k){var B=r(k),N=i(k),R=document.getElementById(k.tbody);if(R){var F=R.closest("table"),A=F&&F.querySelector("thead");if(A){B.length>0?A.classList.add("recon-batch-mode"):A.classList.remove("recon-batch-mode"),A.querySelectorAll(".recon-master-cb").forEach(function(f){if(N.length===0){f.checked=!1,f.indeterminate=!1;return}B.length===N.length?(f.checked=!0,f.indeterminate=!1):B.length===0?(f.checked=!1,f.indeterminate=!1):(f.checked=!1,f.indeterminate=!0)});var g=A.querySelector("[data-recon-count]");g&&(g.textContent=n("recon-batch-selected-n","已选 {n} 条").replace("{n}",B.length))}}}function v(k){var B=document.getElementById(k.tbody);if(B){var N=B.closest("table"),R=N&&N.querySelector("thead");if(R){var F=R.querySelector("[data-recon-del-label]"),A=R.querySelector("[data-recon-clear]");F&&(F.textContent=n("recon-batch-delete","批量删除")),A&&(A.textContent=n("recon-batch-clear","取消")),c(k)}}}function x(k){i(k).forEach(function(B){B.checked=!1}),c(k)}async function _(k){var B=r(k);if(B.length){var N=n("recon-batch-delete-confirm","确定删除选中的 {n} 条对账任务?此操作不可恢复").replace("{n}",B.length),R=!1;try{typeof window.pearnlyConfirm=="function"?R=await window.pearnlyConfirm(N,n("recon-batch-delete-title","批量删除")):R=window.confirm(N)}catch{R=!1}if(R)try{var F=Object.assign({"Content-Type":"application/json"},a()),A=k.kind==="glv"?B.map(function(I){return parseInt(I,10)}):B,g=await fetch(k.api,{method:"POST",headers:F,body:JSON.stringify({ids:A})});if(!g.ok){typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error");return}var f=await g.json(),h=f&&(f.deleted!=null?f.deleted:f.count)||B.length;typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-ok","已删除 {n} 条").replace("{n}",h),"success"),k.reload()}catch{typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error")}}}function q(k){l(k),y(k);var B=document.getElementById(k.tbody);if(!(!B||B._reconBatchWatched)){B._reconBatchWatched=!0;var N=new MutationObserver(function(){y(k)});N.observe(B,{childList:!0,subtree:!1})}}function j(){s(),o.forEach(q),document.querySelectorAll(".recon-batch-bar").forEach(function(k){try{k.remove()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",j):j(),setTimeout(j,1500),setTimeout(j,4e3),document.addEventListener("keydown",function(k){k.key==="Escape"&&o.forEach(function(B){r(B).length>0&&x(B)})}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-batch-thead",function(){o.forEach(v)})})();(function(){let e={role:"",monthly_volume:"",country:"",line_id:""},n=1;const a=4,o="pilot_ob_dismiss",s="pilot_ob_done";window.maybeShowOnboarding=function(r){};function p(r){n=r;for(let v=1;v<=a;v++){const x=document.getElementById("ob-step-"+v);x&&(x.style.display=v===r?"block":"none")}document.querySelectorAll(".ob-dot").forEach(v=>{const x=parseInt(v.dataset.step,10);v.classList.toggle("active",x===r),v.classList.toggle("done",x<r)});const d=document.getElementById("ob-step-label");d&&(d.textContent=r+" / "+a);const c=document.getElementById("ob-next");if(c&&(c.textContent=r===a?t("ob-finish"):t("ob-next")),r===4){const v=document.getElementById("ob-line-input");v&&(v.value=e.line_id||"")}}function l(r){const d=document.querySelector(".onboarding-modal");if(!d)return;let c=d.querySelector(".ob-feedback");c||(c=document.createElement("div"),c.className="ob-feedback",d.appendChild(c)),c.textContent=r,c.classList.add("show"),setTimeout(()=>c.classList.remove("show"),1800)}document.addEventListener("click",r=>{const d=r.target.closest(".ob-option");if(!d)return;const c=d.parentElement;if(!c||!c.classList.contains("ob-options"))return;c.querySelectorAll(".ob-option").forEach(x=>x.classList.remove("selected")),d.classList.add("selected");const v=d.dataset.value;c.id==="ob-role-options"?e.role=v:c.id==="ob-volume-options"?e.monthly_volume=v:c.id==="ob-country-options"&&(e.country=v)}),document.addEventListener("click",r=>{r.target.id==="ob-skip"&&y()}),document.addEventListener("click",r=>{if(r.target.id==="ob-next"){if(n===4){const d=document.getElementById("ob-line-input");e.line_id=(d&&d.value||"").trim().replace(/^@+/,"")}y()}}),document.addEventListener("click",r=>{if(r.target.closest("#ob-close")){localStorage.setItem(o,String(Date.now()));const d=document.getElementById("onboarding-modal");d&&(d.style.display="none")}});function y(){n===1&&e.role?l(t("ob-fb-role")):n===2&&e.monthly_volume?l(t("ob-fb-volume")):n===3&&e.country?l(t("ob-fb-country")):n===4&&e.line_id&&l(t("ob-fb-line")),n<a?setTimeout(()=>p(n+1),e[Object.keys(e)[n-1]]?350:0):i()}async function i(){const r=document.getElementById("onboarding-modal");localStorage.setItem(s,"1"),localStorage.removeItem(o);const d={};if(e.role&&(d.role=e.role),e.monthly_volume&&(d.monthly_volume=e.monthly_volume),e.country&&(d.country=e.country),e.line_id&&(d.line_id=e.line_id),Object.keys(d).length===0){r&&(r.style.display="none");return}try{const c=await fetch("/api/me/profile",{method:"PUT",headers:{Authorization:"Bearer "+(window.token||localStorage.getItem("mrpilot_token")),"Content-Type":"application/json"},body:JSON.stringify(d)});c.ok?(l(t("ob-fb-done")),window._userInfo&&Object.assign(window._userInfo,d),setTimeout(()=>{r&&(r.style.display="none")},1200)):(localStorage.setItem("pilot_ob_pending",JSON.stringify(d)),console.warn("onboarding profile save failed",c.status),l(t("ob-fb-saved-local")),setTimeout(()=>{r&&(r.style.display="none")},1500))}catch(c){console.error("onboarding submit",c),localStorage.setItem("pilot_ob_pending",JSON.stringify(d)),r&&(r.style.display="none")}}})();(function(){const e=document.getElementById("archive-rule-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=document.getElementById("archive-token-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
        </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e=[],n="by_month_seller",a=-1,o=!1;const s={date:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="3.5" width="11" height="10" rx="1.5"/><path d="M2.5 6.5h11M5.5 2v3M10.5 2v3"/></svg>',seller:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13.5V4a1 1 0 011-1h5a1 1 0 011 1v9.5"/><path d="M10 7h2.5a.5.5 0 01.5.5v6"/><path d="M5 6h1M5 9h1M5 12h1M13.5 13.5h-12"/></svg>',category:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 2h6L13 5.5v7.5a1 1 0 01-1 1H3.5a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M9 2v4h4"/><path d="M5 9h6M5 11.5h4"/></svg>',amount:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M8 4.5v7M10 6.3a1.8 1.8 0 00-4 0c0 .9.7 1.3 2 1.6s2 .8 2 1.6a1.8 1.8 0 01-4 0"/></svg>',invoice:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3.5l1.5 10.5 1.5-1 1.5 1 1.5-1 1.5 1 1.5-1 1.5 1L13 3.5z"/><path d="M5.5 6.5h5M5.5 9h5M5.5 11.5h3"/></svg>',buyer:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="6" r="2.5"/><path d="M3 13.5c0-2.5 2.2-4.5 5-4.5s5 2 5 4.5"/></svg>',sep:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v10"/></svg>'},p={date:{label:"field-date",defaultCfg:{format:"YYYY-MM-DD"}},seller:{label:"field-seller",defaultCfg:{short:!0}},category:{label:"field-category",defaultCfg:{}},amount:{label:"field-amount",defaultCfg:{with_currency:!0}},invoice:{label:"field-invoice",defaultCfg:{}},buyer:{label:"field-buyer",defaultCfg:{}},sep:{label:"field-sep",defaultCfg:{val:"_"}}};function l(){return{zh:"运费",en:"Shipping",th:"ค่าขนส่ง",ja:"送料"}[currentLang]||"Shipping"}function y(){return"DHL Express (Thailand) Co., Ltd."}function i(){return{merged_fields:{invoice_date:"2026-04-15",seller_name:y(),category:l(),total_amount:1250,currency:"THB",invoice_no:"INV-2026030002",buyer_name:"Mr.ERP Co., Ltd."}}}window.loadAboutPanel=()=>r(),window.loadPrefsSettings=()=>d(),window.loadArchiveSettings=()=>v();function r(){const g=document.getElementById("settings-contact-grid");if(!g)return;const f=_contact?.phone||"086-889-2228",h=_contact?.line_id||"@Pearnly",I=_contact?.line_url||"https://line.me/R/ti/p/@059oupmg",L=_contact?.email||"hello@pearnly.com",$=_contact?.address||"Bangkok, Thailand";g.innerHTML=`
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
            <a class="contact-item" href="tel:${escapeHtml(f.replace(/[^\d+]/g,""))}">
                <div class="contact-icon phone">
                    <svg viewBox="0 0 20 20" fill="currentColor"><path d="M2 3a1 1 0 011-1h2.5a1 1 0 01.97.757l1 4a1 1 0 01-.29.986l-1.75 1.75a11 11 0 005.07 5.07l1.75-1.75a1 1 0 01.986-.29l4 1a1 1 0 01.757.97V17a1 1 0 01-1 1h-1C8.82 18 2 11.18 2 3V3z"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-phone"))}</div>
                    <div class="contact-value">${escapeHtml(f)}</div>
                </div>
            </a>
            <div class="contact-item">
                <div class="contact-icon address">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s-7-7.5-7-13a7 7 0 1114 0c0 5.5-7 13-7 13z"/><circle cx="12" cy="9" r="2.5"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-address"))}</div>
                    <div class="contact-value">${escapeHtml($)}</div>
                </div>
            </div>
        `}async function d(){try{const g=await fetch("/api/settings/dup-check",{headers:{Authorization:"Bearer "+token}});if(!g.ok)return;const f=await g.json(),h=document.getElementById("pref-dup-check");h&&(h.checked=!!f.enabled)}catch(g){console.warn("load prefs failed",g)}}const c=document.getElementById("pref-dup-check");c&&!c.dataset.bound&&(c.dataset.bound="1",c.addEventListener("change",async g=>{const f=g.target.checked;try{(await fetch("/api/settings/dup-check",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({enabled:f})})).ok?showToast(f?t("pref-dup-check-on-toast"):t("pref-dup-check-off-toast"),"success"):(g.target.checked=!f,showToast(t("pref-save-failed"),"error"))}catch{g.target.checked=!f,showToast(t("pref-save-failed"),"error")}}));async function v(){const g=!!(_userInfo&&_userInfo.can_customize_archive);o=!g;const f=document.getElementById("archive-upgrade-banner");f&&(f.style.display=g?"none":"");const h=document.getElementById("archive-plus-badge");h&&(h.style.display=g?"none":"");try{const I=await fetch("/api/archive/settings",{headers:{Authorization:"Bearer "+token}});if(!I.ok)throw new Error("load failed");const L=await I.json();e=Array.isArray(L.name_template)?L.name_template:[],n=L.folder_strategy||"by_month_seller"}catch(I){console.error("load archive settings failed",I),showToast(t("archive-load-failed"),"error");return}x(),_(),q(),j()}function x(){const g=document.getElementById("archive-rule-canvas");if(g){if(e.length===0){g.innerHTML=`<div class="archive-empty">${escapeHtml(t("archive-rule-empty"))}</div>`;return}g.innerHTML=e.map((f,h)=>{const I=p[f.type]||{label:f.type},L=s[f.type]||"",$=f.type==="sep"?`"${escapeHtml(f.val||"_")}"`:escapeHtml(t(I.label));return`
                <span class="archive-token ${f.type}"
                      data-token-idx="${h}"
                      draggable="${o?"false":"true"}">
                    <span class="token-icon">${L}</span>
                    <span class="token-label">${$}</span>
                </span>
            `}).join("")}}function _(){const g=document.getElementById("archive-field-palette");if(!g)return;const f=["date","seller","category","amount","invoice","buyer","sep"];g.innerHTML=f.map(h=>{const I=p[h],L=s[h]||"";return`
                <button class="archive-palette-btn ${h}" data-add-field="${h}" ${o?"disabled":""}>
                    <span class="token-icon">${L}</span>
                    <span>${escapeHtml(t(I.label))}</span>
                </button>
            `}).join("")}function q(){document.querySelectorAll('input[name="folder-strategy"]').forEach(g=>{g.checked=g.value===n,g.disabled=o})}async function j(){const g=document.getElementById("archive-preview-name"),f=document.getElementById("archive-preview-hint");if(f&&(f.textContent=t("archive-preview-hint",{category:l()})),!!g){if(e.length===0){g.textContent="-";return}try{const I=await(await fetch("/api/archive/rename-preview",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({merged_fields:i().merged_fields,name_template:e})})).json();g.textContent=(I.name||"-")+".pdf"}catch{g.textContent="("+t("archive-preview-error")+")"}}}window._rerenderArchiveAll=function(){const g=document.getElementById("archive-rule-modal");!g||g.style.display==="none"||(x(),_(),j())};let k=-1;document.addEventListener("dragstart",g=>{const f=g.target.closest(".archive-token");!f||o||(k=parseInt(f.dataset.tokenIdx,10),f.classList.add("dragging"),g.dataTransfer.effectAllowed="move")}),document.addEventListener("dragend",g=>{document.querySelectorAll(".archive-token").forEach(f=>f.classList.remove("dragging","drop-target")),k=-1}),document.addEventListener("dragover",g=>{const f=g.target.closest(".archive-token");f&&(g.preventDefault(),g.dataTransfer.dropEffect="move",document.querySelectorAll(".archive-token").forEach(h=>h.classList.remove("drop-target")),f.classList.add("drop-target"))}),document.addEventListener("drop",g=>{const f=g.target.closest(".archive-token");if(!f||k<0||o)return;g.preventDefault();const h=parseInt(f.dataset.tokenIdx,10);if(h===k)return;const I=e.splice(k,1)[0];e.splice(h,0,I),k=-1,x(),j()}),document.addEventListener("click",g=>{if(g.target.closest("#btn-open-archive-rule")||g.target.closest("#btn-open-archive-rule-from-settings")){const L=document.getElementById("archive-rule-modal");L&&(L.style.display="",v());return}if(g.target.closest("#archive-rule-modal-close")||g.target.id==="archive-rule-modal"){const L=document.getElementById("archive-rule-modal");L&&(L.style.display="none");return}const f=g.target.closest(".settings-nav-item");if(f){switchSettingsTab(f.dataset.settingsTab);return}if(o&&g.target.closest(".archive-token, [data-add-field], #btn-archive-save, #btn-archive-reset")){showToast(t("feature-contact-us"),"info");return}const h=g.target.closest("[data-add-field]");if(h){const L=h.dataset.addField,$=p[L],E={type:L,...$.defaultCfg};e.push(E),x(),j();return}const I=g.target.closest(".archive-token");if(I&&!o){B(parseInt(I.dataset.tokenIdx,10));return}if(g.target.closest("#btn-archive-save"))return F();if(g.target.closest("#btn-archive-reset"))return A();(g.target.closest("#archive-token-close")||g.target.id==="archive-token-modal")&&(document.getElementById("archive-token-modal").style.display="none"),g.target.closest("#btn-archive-token-ok")&&N(),g.target.closest("#btn-archive-token-delete")&&R()}),document.addEventListener("change",g=>{g.target.name==="folder-strategy"&&(n=g.target.value)});function B(g){a=g;const f=e[g];if(!f)return;const h=document.getElementById("archive-token-body");let I="";f.type==="date"?I=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-date-format"))}</label>
                    <select class="form-input" id="token-date-format">
                        <option value="YYYY-MM-DD" ${f.format==="YYYY-MM-DD"?"selected":""}>YYYY-MM-DD (2026-04-15)</option>
                        <option value="YYYYMMDD"   ${f.format==="YYYYMMDD"?"selected":""}>YYYYMMDD (20260415)</option>
                        <option value="YY.MM"      ${f.format==="YY.MM"?"selected":""}>YY.MM (26.04)</option>
                        <option value="YYYY年MM月" ${f.format==="YYYY年MM月"?"selected":""}>YYYY年MM月 (2026年04月)</option>
                    </select>
                </div>`:f.type==="seller"?I=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-seller-short" ${f.short?"checked":""}> ${escapeHtml(t("archive-seller-short"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-seller-short-hint"))}</div>
                </div>`:f.type==="amount"?I=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-amount-currency" ${f.with_currency?"checked":""}> ${escapeHtml(t("archive-amount-currency"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-amount-currency-hint"))}</div>
                </div>`:f.type==="sep"?I=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-sep-val"))}</label>
                    <div class="sep-options">
                        <button type="button" class="sep-chip ${f.val==="_"?"active":""}" data-sep="_">_ (下划线)</button>
                        <button type="button" class="sep-chip ${f.val==="-"?"active":""}" data-sep="-">- (短横)</button>
                        <button type="button" class="sep-chip ${f.val===" "?"active":""}" data-sep=" ">(空格)</button>
                        <input type="text" id="token-sep-custom" class="form-input sep-custom" maxlength="3" placeholder="${escapeHtml(t("archive-sep-custom"))}" value="${["_","-"," "].includes(f.val)?"":escapeHtml(f.val||"")}">
                    </div>
                </div>`:I=`<div class="form-hint">${escapeHtml(t("archive-token-no-option"))}</div>`,h.innerHTML=I,document.getElementById("archive-token-modal").style.display="",h.querySelectorAll(".sep-chip").forEach(L=>{L.addEventListener("click",()=>{h.querySelectorAll(".sep-chip").forEach(E=>E.classList.remove("active")),L.classList.add("active");const $=document.getElementById("token-sep-custom");$&&($.value="")})})}function N(){const g=e[a];if(g){if(g.type==="date")g.format=document.getElementById("token-date-format").value;else if(g.type==="seller")g.short=document.getElementById("token-seller-short").checked;else if(g.type==="amount")g.with_currency=document.getElementById("token-amount-currency").checked;else if(g.type==="sep"){const f=document.querySelector("#archive-token-body .sep-chip.active"),h=document.getElementById("token-sep-custom").value;g.val=h||(f?f.dataset.sep:"_")}document.getElementById("archive-token-modal").style.display="none",x(),j()}}function R(){a<0||(e.splice(a,1),document.getElementById("archive-token-modal").style.display="none",x(),j())}async function F(){if(e.length===0){showToast(t("archive-rule-cannot-empty"),"error");return}try{if(!(await fetch("/api/archive/settings",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({name_template:e,folder_strategy:n})})).ok)throw new Error("save failed");showToast(t("archive-save-ok"),"success");const f=document.getElementById("archive-rule-modal");f&&(f.style.display="none")}catch{showToast(t("archive-save-fail"),"error")}}async function A(){await showConfirm(t("archive-reset-confirm"),{danger:!0})&&(e=[{type:"date",format:"YYYY-MM-DD"},{type:"sep",val:"_"},{type:"seller",short:!0},{type:"sep",val:"_"},{type:"category"},{type:"sep",val:"_"},{type:"amount",with_currency:!0}],n="by_month_seller",x(),q(),j())}})();(function(){const o="pearnly_big_batch_tip_shown";let s=null,p=null,l=0,y=0,i=!1;function r(B){const N=typeof t=="function"?t("big-batch-unload-warn"):"Batch OCR running · close anyway?";return B.preventDefault(),B.returnValue=N,N}function d(){i||(i=!0,window.addEventListener("beforeunload",r))}function c(){i&&(i=!1,window.removeEventListener("beforeunload",r))}function v(){if(document.getElementById("big-batch-progress"))return;const B=document.getElementById("file-list");if(!B||!B.parentNode)return;const N=document.createElement("div");N.id="big-batch-progress",N.className="big-batch-progress",N.innerHTML='<div class="bbp-row"><svg class="bbp-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.5"/><path d="M8 4.5v3.5l2.5 1.5"/></svg><span class="bbp-text" id="bbp-text"></span></div><div class="bbp-track"><div class="bbp-fill" id="bbp-fill" style="width:0%"></div></div>',B.parentNode.insertBefore(N,B);const R=document.getElementById("bbp-text");R&&(R.textContent=typeof t=="function"?t("big-batch-progress-init"):"Starting...")}function x(){const B=document.getElementById("big-batch-progress");B&&B.remove()}function _(){if(!p)return;let B=0;for(let I=0;I<p.length;I++){const L=p[I].status;(L==="success"||L==="error"||L==="cancelled")&&B++}const N=l,R=N>0?Math.min(100,Math.floor(100*B/N)):0,F=(Date.now()-y)/1e3;let A;if(B>=3&&F>1){const I=F/B;A=(N-B)*I}else A=(N-B)*6/6;const g=Math.max(1,Math.ceil(A/60)),f=document.getElementById("bbp-fill"),h=document.getElementById("bbp-text");f&&(f.style.width=R+"%"),h&&(B>=N?h.textContent=t("big-batch-progress-done").replace("{total}",N):h.textContent=t("big-batch-progress-running").replace("{done}",B).replace("{total}",N).replace("{min}",g))}function q(B){try{if(localStorage.getItem(o)==="1")return}catch{}const N=Math.max(1,Math.ceil(B*6/6/60)),R=t("big-batch-first-tip").replace("{n}",B).replace("{min}",N);typeof showToast=="function"&&showToast(R,"info",8e3);try{localStorage.setItem(o,"1")}catch{}}function j(B){!B||B.length<100||(p=B,l=B.length,y=Date.now(),v(),d(),q(l),s&&clearInterval(s),s=setInterval(_,250),_())}function k(){s&&(clearInterval(s),s=null),c(),p&&l>=100?(_(),setTimeout(x,1200)):x(),p=null,l=0}window._bigBatchStart=j,window._bigBatchStop=k,typeof window.subscribeI18n=="function"&&window.subscribeI18n("big-batch-progress",function(){p&&_()})})();(function(){let e=null,n=!1,a=!1;function o(f){return typeof escapeHtml=="function"?escapeHtml(f==null?"":String(f)):String(f??"")}function s(f,h){try{typeof showToast=="function"&&showToast(f,h||"info")}catch{}}function p(){const f=typeof _userInfo<"u"?_userInfo:null;return!!(f&&(f.role==="owner"||f.is_super_admin))}function l(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function y(f){if(!f)return!1;const h=String(f.status||"").toLowerCase();return h==="exception"||h==="exception_pending"||h==="rejected"}async function i(f){if(n&&!f)return e;const h=localStorage.getItem("mrpilot_token");if(!h)return null;try{const I=await fetch("/api/erp/xero/status",{headers:{Authorization:"Bearer "+h}});if(!I.ok)throw new Error("http_"+I.status);e=await I.json(),n=!0}catch{e={configured:!1,connected:!1,organisations:[]},n=!1}return e}function r(){const f=document.getElementById("erp-connect-cards");if(!f)return;const h=e;let I,L=!1;h?h.configured?h.connected?(L=!0,I='<span class="mrerp-card-pill mrerp-pill-ok">'+o(t("xero-card-connected"))+"</span>"):I='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-connected"))+"</span>":I='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-configured"))+"</span>":I='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-connected"))+"</span>";let $="";if(!h||!h.configured)$='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+o(t("xero-connect-btn"))+"</button>";else if(!h.connected)p()&&($='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+o(t("xero-connect-btn"))+"</button>");else{const w=!!h.auto_push,m=w?t("card-btn-disable"):t("card-btn-enable");$='<button type="button" class="'+(w?"mrerp-card-toggle mrerp-card-toggle-disable":"mrerp-card-toggle mrerp-card-toggle-enable")+'" id="btn-xero-toggle-enabled" data-xero-enabled="'+(w?"1":"0")+'" title="'+o(w?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip"))+'">'+o(m)+'</button><button type="button" class="int-btn-configure" id="btn-xero-edit-toggle">'+o(t("card-btn-edit"))+"</button>"}const E=h&&h.connected?"xero-card-desc-connected":"xero-card-desc-default",M=h&&h.connected?t("xero-card-connected")||"Connected · default org will receive pushes":"Cloud accounting · push invoices to your default Xero org",K=(function(){const w=t(E);return w===E?M:w})();let G='<div class="integration-row erp-connect-xero'+(L?" connected":"")+'"><div class="int-icon ic-xero"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="9" cy="10" r="1.3" fill="currentColor"/><circle cx="15" cy="14" r="1.3" fill="currentColor"/><path d="M9 14l6-4"/></svg></div><div class="int-info"><div class="int-name"><span>'+o(t("xero-card-title")||"Xero")+"</span>"+I+'</div><div class="int-desc">'+o(K)+'</div></div><div class="int-actions">'+$+"</div></div>";if(h&&h.configured&&h.connected&&p()){const w=h.organisations||[];let m="";if(w.length>0){m+='<div class="erp-cc-meta">'+o((t("xero-org-count")||"").replace("{n}",String(w.length)))+"</div>",m+='<div class="erp-cc-org-label">'+o(t("xero-default-org"))+":</div>",m+='<div class="erp-cc-orgs">',w.forEach(function(J){m+='<label class="erp-cc-org-row"><input type="radio" name="xero-default-org" value="'+o(J.id)+'"'+(J.is_default?" checked":"")+'><span class="erp-cc-org-name">'+o(J.organisation_name||J.organisation_id)+"</span></label>"}),m+="</div>";const H=!!h.auto_push,D=H?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip");m+='<div class="erp-cc-auto-push" title="'+o(D)+'"><label class="erp-cc-toggle"><input type="checkbox" id="xero-auto-push-toggle"'+(H?" checked":"")+'><span class="erp-cc-toggle-slider"></span><span class="erp-cc-toggle-label">'+o(t("erp-auto-push-label"))+"</span></label></div>",m+='<div class="erp-cc-actions"><button class="btn btn-ghost btn-tiny" type="button" id="btn-xero-disconnect">'+o(t("xero-disconnect-btn"))+"</button></div>"}G+='<div class="erp-xero-details" id="erp-xero-details" style="display:none; margin:8px 0 16px; padding:12px 14px; border:1px solid var(--line); border-radius:8px; background:var(--bg);">'+m+"</div>"}const W=f.querySelector(".erp-connect-xero"),te=f.querySelector("#erp-xero-details");te&&te.remove(),W?W.outerHTML=G:f.insertAdjacentHTML("afterbegin",G);const re=document.getElementById("btn-xero-edit-toggle");re&&re.addEventListener("click",function(w){w.preventDefault();const m=document.getElementById("erp-xero-details");m&&(m.style.display=m.style.display==="none"?"":"none")});const S=document.getElementById("btn-xero-toggle-enabled");S&&S.addEventListener("click",async function(w){if(w.preventDefault(),S.disabled)return;const H=!(S.getAttribute("data-xero-enabled")==="1");if(!H)try{if(!await window.pearnlyConfirm(t("card-toggle-disable-confirm")))return}catch{}S.disabled=!0,await x(H,null)})}async function d(){const f=localStorage.getItem("mrpilot_token");if(f)try{const h=await fetch("/api/erp/xero/auth/start",{method:"GET",headers:{Authorization:"Bearer "+f}});if(!h.ok){let L="unknown";try{L=(await h.json()).detail||"unknown"}catch{}const $=String(L).replace(/^xero\./,"").toLowerCase();s(t("xero-push-fail").replace("{err}",t("xero-err-"+$)||L),"error");return}const I=await h.json();I.redirect_url&&(window.location.href=I.redirect_url)}catch(h){s(t("xero-push-fail").replace("{err}",h.message||"network"),"error")}}async function c(){if(!await window.pearnlyConfirm(t("xero-disconnect-confirm")))return;const h=localStorage.getItem("mrpilot_token");try{const I=await fetch("/api/erp/xero/disconnect",{method:"POST",headers:{Authorization:"Bearer "+h}});if(!I.ok)throw new Error("http_"+I.status);await i(!0),r()}catch(I){s(t("xero-push-fail").replace("{err}",I.message),"error")}}async function v(f){const h=localStorage.getItem("mrpilot_token");try{const I=await fetch("/api/erp/xero/select_org",{method:"POST",headers:{Authorization:"Bearer "+h,"Content-Type":"application/json"},body:JSON.stringify({token_id:f})});if(!I.ok)throw new Error("http_"+I.status);await i(!0),r()}catch(I){s(t("xero-push-fail").replace("{err}",I.message),"error")}}async function x(f,h){const I=localStorage.getItem("mrpilot_token");h&&(h.disabled=!0);try{const L=await fetch("/api/erp/xero/auto-push",{method:"POST",headers:{Authorization:"Bearer "+I,"Content-Type":"application/json"},body:JSON.stringify({on:!!f})});if(!L.ok){let $="unknown";try{$=(await L.json()).detail||"unknown"}catch{}throw new Error($)}s(f?t("erp-auto-push-toggled-on"):t("erp-auto-push-toggled-off"),"success"),n=!1,await i(!0),r()}catch(L){h&&(h.checked=!f),s(t("erp-auto-push-toggle-fail").replace("{err}",L.message||"network"),"error")}finally{h&&(h.disabled=!1)}}async function _(){const f=document.getElementById("drawer-history-save");if(!f||f.querySelector("#btn-xero-push")||f.querySelector("#pn-push-wrap")||(await i(!1),f.querySelector("#pn-push-wrap"))||f.querySelector("#btn-xero-push"))return;const h=l();if(!(h&&(h._historyId||h.history_id)))return;let L=!1,$="xero-push-tip";!e||!e.configured?(L=!0,$="xero-err-not_configured"):e.connected?y(h)&&(L=!0,$="xero-push-disabled-exc"):(L=!0,$="xero-push-disabled-no-conn");const E=document.createElement("button");E.type="button",E.id="btn-xero-push",E.className="btn btn-ghost"+(L?" disabled":""),E.disabled=L,E.title=t($)||"",E.innerHTML='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5 8l2 2 4-4"/></svg><span style="margin-left:4px;">'+o(t("xero-push-btn"))+"</span>",E.addEventListener("click",q);const M=document.getElementById("btn-push-erp");M&&M.parentNode?M.parentNode.insertBefore(E,M.nextSibling):f.insertBefore(E,f.firstChild)}async function q(){const f=l(),h=f&&(f._historyId||f.history_id);if(!h)return;const I=document.getElementById("btn-xero-push");I&&(I.disabled=!0,I.classList.add("loading"));const L=localStorage.getItem("mrpilot_token");try{const $=await fetch("/api/erp/xero/push/"+encodeURIComponent(h),{method:"POST",headers:{Authorization:"Bearer "+L}});if(!$.ok){let E="unknown";try{E=(await $.json()).detail||"unknown"}catch{}const M=String(E).replace(/^xero\./,"").toLowerCase(),K=t("xero-"+M),G=K&&K!=="xero-"+M?K:E;s(t("xero-push-fail").replace("{err}",G),"error");return}s(t("xero-push-ok"),"success")}catch($){s(t("xero-push-fail").replace("{err}",$.message||"network"),"error")}finally{I&&(I.disabled=!1,I.classList.remove("loading"))}}async function j(){await i(!0),r(),k()}async function k(){const f=document.getElementById("erp-global-push-mode");if(!f)return;const h=localStorage.getItem("mrpilot_token");if(h)try{const I=await fetch("/api/settings/erp-push-mode",{headers:{Authorization:"Bearer "+h}});if(I.ok){const L=await I.json();L.mode&&(f.value=L.mode,f.dataset.prev=L.mode)}}catch{}}async function B(f){const h=f.value,I=localStorage.getItem("mrpilot_token");try{(await fetch("/api/settings/erp-push-mode",{method:"PUT",headers:{Authorization:"Bearer "+I,"Content-Type":"application/json"},body:JSON.stringify({mode:h})})).ok?(f.dataset.prev=h,s(t("pref-erp-mode-saved"),"success")):(f.value=f.dataset.prev||"smart",s(t("pref-save-failed"),"error"))}catch{f.value=f.dataset.prev||"smart",s(t("pref-save-failed"),"error")}}function N(){try{const f=String(window.location.hash||"");if(f.indexOf("xero=ok")>=0){const h=f.match(/n=(\d+)/),I=h?h[1]:"1";s((t("xero-toast-redirected-ok")||"").replace("{n}",I),"success"),history.replaceState(null,"",window.location.pathname+"#automation"),i(!0).then(r)}else f.indexOf("xero=err")>=0&&(s(t("xero-toast-redirected-err"),"error"),history.replaceState(null,"",window.location.pathname+"#automation"))}catch{}}function R(){if(a)return;a=!0,document.addEventListener("click",function(h){if(h.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(j,50);return}if(h.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(j,80);return}if(h.target.closest("#btn-xero-connect")){h.preventDefault(),d();return}if(h.target.closest("#btn-xero-disconnect")){h.preventDefault(),c();return}}),document.addEventListener("change",function(h){h.target&&h.target.matches('input[name="xero-default-org"]')&&v(h.target.value),h.target&&h.target.id==="xero-auto-push-toggle"&&x(h.target.checked,h.target),h.target&&h.target.id==="erp-global-push-mode"&&B(h.target)});const f=function(){return document.getElementById("drawer-body")};try{const h=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("btn-xero-push")&&_()}),I=f();if(I)h.observe(I,{childList:!0,subtree:!0});else{const L=new MutationObserver(function(){const $=f();$&&(h.observe($,{childList:!0,subtree:!0}),L.disconnect())});L.observe(document.body,{childList:!0,subtree:!0})}}catch{}setTimeout(N,500)}function F(){e&&r();const f=document.getElementById("btn-xero-push");if(f){const h=f.querySelector("span");h&&(h.textContent=t("xero-push-btn"))}}R(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("xero-adapter",F);async function A(f){const h=Date.now();for(;Date.now()-h<f;){if(typeof _userInfo<"u"&&_userInfo&&_userInfo.id)return _userInfo;await new Promise(I=>setTimeout(I,80))}return null}async function g(){await A(5e3);const f=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),h=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');f&&h&&await j()}setTimeout(g,200)})();(function(){const e={};function n(){if(document.getElementById("report-modal"))return;const r=`
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
        </div>`,d=document.createElement("div");d.innerHTML=r,document.body.appendChild(d.firstElementChild),document.getElementById("report-modal-close-x").addEventListener("click",a),document.getElementById("report-modal-cancel").addEventListener("click",a),document.getElementById("report-modal").addEventListener("click",c=>{c.target.id==="report-modal"&&a()})}function a(){const r=document.getElementById("report-modal");r&&(r.style.display="none"),o=null}let o=null;async function s(r,d){const c=r+":"+(d||"");if(e[c])return e[c];let v;try{const x=localStorage.getItem("mrpilot_token"),_=await fetch(`/api/reports/templates?lang=${encodeURIComponent(r)}`,{headers:{Authorization:"Bearer "+x}});if(!_.ok)throw new Error("templates fetch failed");v=(await _.json()).templates||[]}catch(x){console.error("fetchTemplates fail",x),v=[{code:"input_vat",name:t("tpl-input-vat"),desc:t("tpl-input-vat-desc"),recommended:!0},{code:"standard",name:t("tpl-standard"),desc:t("tpl-standard-desc"),recommended:!1},{code:"print",name:t("tpl-print"),desc:t("tpl-print-desc"),recommended:!1}]}if(v=v.filter(x=>x.code!=="erp"),d==="history-batch"){const x=v.findIndex(q=>q.code==="standard"),_=x>=0?x+1:v.length;v.splice(_,0,{code:"sales_detail_th",name:t("export-tpl-sales-detail"),desc:t("export-tpl-sales-detail-desc"),recommended:!1,is_new:!0})}return e[c]=v,v}function p(r){const d=document.getElementById("report-tpl-list"),c=r.map((x,_)=>`
            <label class="report-tpl-item${x.recommended?" is-recommended":""}">
                <input type="radio" name="report-tpl" value="${x.code}" ${x.recommended||_===0?"checked":""}>
                <div class="report-tpl-content">
                    <div class="report-tpl-name">
                        ${l(x.name)}
                        ${x.recommended?`<span class="report-tpl-badge">${l(t("report-recommended"))}</span>`:""}
                    </div>
                    <div class="report-tpl-desc">${l(x.desc||"")}</div>
                </div>
            </label>
        `).join(""),v=`
            <label class="report-tpl-item report-tpl-coming" title="${l(t("tpl-custom-coming"))}">
                <input type="radio" name="report-tpl" disabled>
                <div class="report-tpl-content">
                    <div class="report-tpl-name">
                        + ${l(t("tpl-custom-new"))}
                        <span class="report-tpl-badge report-tpl-badge-soon">${l(t("cs-coming-soon"))}</span>
                    </div>
                    <div class="report-tpl-desc">${l(t("tpl-custom-desc"))}</div>
                </div>
            </label>
        `;d.innerHTML=c+v}function l(r){return r==null?"":String(r).replace(/[&<>"']/g,d=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[d])}function y(r){const d=new Date,c=d.getFullYear(),v=d.getMonth()+1;if(r==="all")return"all";if(r==="this-month")return`${c}-${String(v).padStart(2,"0")}`;if(r==="last-month"){const x=new Date(c,v-2,1);return`${x.getFullYear()}-${String(x.getMonth()+1).padStart(2,"0")}`}return r==="this-year"?`${c}`:r==="this-quarter"?`${c}-Q${Math.floor((v-1)/3)+1}`:"all"}window.openReportModal=async function(r){r=r||{},n(),typeof applyLang=="function"?applyLang(currentLang):document.querySelectorAll("#report-modal [data-i18n]").forEach(q=>{const j=q.getAttribute("data-i18n");I18N[currentLang]&&I18N[currentLang][j]&&(q.textContent=I18N[currentLang][j])});const d=document.getElementById("report-period-section");d&&(d.style.display=r.mode==="client"?"":"none");const c=document.getElementById("report-tpl-list");c.innerHTML=`<div class="report-tpl-loading">${l(t("report-modal-loading"))}</div>`,document.getElementById("report-modal").style.display="";const v=await s(currentLang,r&&r.mode);p(v),o=r;const x=document.getElementById("report-modal-download"),_=x.cloneNode(!0);x.parentNode.replaceChild(_,x),_.addEventListener("click",()=>i(o))};async function i(r){if(!r)return;const d=document.querySelector('input[name="report-tpl"]:checked');if(!d){showToast(t("report-toast-no-selection"),"info");return}const c=d.value,v=document.querySelector('input[name="report-period"]:checked'),x=v?v.value:"all",_=y(x),q=document.getElementById("report-modal-download"),j=q.innerHTML;q.disabled=!0,q.innerHTML=`<span>${l(t("report-modal-loading"))}</span>`;try{const k=localStorage.getItem("mrpilot_token");let B,N;if(r.mode==="records")B=await fetch("/api/reports/export",{method:"POST",headers:{Authorization:"Bearer "+k,"Content-Type":"application/json"},body:JSON.stringify({template:c,lang:currentLang,records:r.records||[],meta:r.meta||{}})}),N=`mrpilot-${c}-${Date.now()}.xlsx`;else if(r.mode==="client"){const I=`/api/reports/clients/${r.clientId}/export?template=${encodeURIComponent(c)}&lang=${encodeURIComponent(currentLang)}&month=${encodeURIComponent(_)}`;B=await fetch(I,{headers:{Authorization:"Bearer "+k}}),N=`${(r.clientName||"client").replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40)}-${c}.xlsx`}else if(r.mode==="history-batch")c==="sales_detail_th"?(B=await fetch("/api/ocr/export-by-history-ids",{method:"POST",headers:{Authorization:"Bearer "+k,"Content-Type":"application/json"},body:JSON.stringify({template:"sales_detail_th",lang:currentLang,history_ids:r.historyIds||[],client_id:r.clientId||null})}),N=`Pearnly_SalesDetail_${Date.now()}.xlsx`):(B=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+k,"Content-Type":"application/json"},body:JSON.stringify({template:c,lang:currentLang,history_ids:r.historyIds||[],client_id:r.clientId||null})}),N=`mrpilot-batch-${c}-${Date.now()}.xlsx`);else throw new Error("unknown mode: "+r.mode);if(!B.ok){let I="HTTP "+B.status;try{const L=await B.json();L&&L.detail&&(I=L.detail)}catch(L){console.warn("[batch-export] resp.json err.detail parse failed:",L)}B.status===404?showToast(t("report-toast-empty"),"info"):showToast(t("report-toast-fail")+" · "+I,"error");return}const R=await B.blob();let F=N;const g=(B.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(g)try{F=decodeURIComponent(g[1])}catch{}const f=URL.createObjectURL(R),h=document.createElement("a");h.href=f,h.download=F,document.body.appendChild(h),h.click(),document.body.removeChild(h),URL.revokeObjectURL(f),showToast(t("report-toast-success"),"success"),a()}catch(k){console.error("doDownload fail",k),showToast(t("report-toast-fail")+" · "+(k.message||""),"error")}finally{q.disabled=!1,q.innerHTML=j}}document.addEventListener("DOMContentLoaded",()=>{const r=document.getElementById("btn-export");if(r){const c=r.cloneNode(!0);r.parentNode.replaceChild(c,r),c.addEventListener("click",()=>{if(typeof _results>"u"||!_results||_results.length===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"records",records:_results.map(v=>({filename:v.filename,merged_fields:v.merged_fields||{}}))})})}const d=document.getElementById("history-batch-export");d&&d.addEventListener("click",()=>{if(typeof _historySelected>"u"||_historySelected.size===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"history-batch",historyIds:Array.from(_historySelected)})})}),window.openClientExportModal=function(r,d){openReportModal({mode:"client",clientId:r,clientName:d||""})}})();(function(){const n=typeof window<"u"&&"showDirectoryPicker"in window,a=/\.(pdf|jpe?g|png|webp)$/i,o="mrpilot_folder_watcher",s=1;let p=null,l=null,y=null,i=60,r=!1,d=!1,c=0,v=0,x=0,_=[],q=null,j=!1;function k(){return p||(p=new Promise((b,C)=>{const T=indexedDB.open(o,s);T.onupgradeneeded=U=>{const z=U.target.result;z.objectStoreNames.contains("handles")||z.createObjectStore("handles"),z.objectStoreNames.contains("seen")||z.createObjectStore("seen"),z.objectStoreNames.contains("config")||z.createObjectStore("config")},T.onsuccess=U=>b(U.target.result),T.onerror=U=>C(U.target.error)}),p)}function B(b,C){return k().then(T=>new Promise((U,z)=>{const P=T.transaction(b,"readonly").objectStore(b).get(C);P.onsuccess=()=>U(P.result),P.onerror=()=>z(P.error)}))}function N(b,C,T){return k().then(U=>new Promise((z,u)=>{const P=U.transaction(b,"readwrite");P.objectStore(b).put(T,C),P.oncomplete=()=>z(),P.onerror=()=>u(P.error)}))}function R(b,C){return k().then(T=>new Promise((U,z)=>{const u=T.transaction(b,"readwrite");u.objectStore(b).delete(C),u.oncomplete=()=>U(),u.onerror=()=>z(u.error)}))}function F(b){return k().then(C=>new Promise((T,U)=>{const z=C.transaction(b,"readwrite");z.objectStore(b).clear(),z.oncomplete=()=>T(),z.onerror=()=>U(z.error)}))}async function A(b){if(!b)return!1;try{const C={mode:"read"};let T=await b.queryPermission(C);return T==="granted"?!0:(T=await b.requestPermission(C),T==="granted")}catch(C){return console.warn("[folder] permission check failed:",C),!1}}function g(b,C){const T=document.getElementById("folder-status-summary");T&&(T.setAttribute("data-i18n",b),T.textContent=t(b),T.className="auto-status-pill"+(C?" "+C:""))}function f(b){["folder-unsupported","folder-empty","folder-active"].forEach(C=>{const T=document.getElementById(C);T&&(T.style.display=C===b?"":"none")})}function h(b){if(!b)return"-";const C=b instanceof Date?b:new Date(b),T=String(C.getHours()).padStart(2,"0"),U=String(C.getMinutes()).padStart(2,"0"),z=String(C.getSeconds()).padStart(2,"0");return`${T}:${U}:${z}`}function I(){f("folder-active");const b=document.getElementById("folder-config-path");b&&l&&(b.textContent=l.name||"-");const C=document.getElementById("folder-interval-select");C&&(C.value=String(i)),document.getElementById("folder-stat-last").textContent=q?h(q):"-",document.getElementById("folder-stat-processed").textContent=String(c),document.getElementById("folder-stat-failed").textContent=String(v),document.getElementById("folder-stat-queue").textContent=String(x);const T=document.getElementById("btn-folder-pause"),U=document.getElementById("btn-folder-resume");T&&(T.style.display=r?"none":""),U&&(U.style.display=r?"":"none"),r?g("folder-status-paused","paused"):g("folder-status-running","running");const z=document.getElementById("folder-status-text");z&&(z.setAttribute("data-i18n",r?"folder-status-paused":"folder-status-running"),z.textContent=t(r?"folder-status-paused":"folder-status-running"));const u=document.getElementById("folder-status-pulse");u&&(u.className="folder-status-pulse"+(r?" paused":"")),L()}function L(){const b=document.getElementById("folder-recent-list");if(b){if(_.length===0){b.innerHTML=`<div class="folder-recent-empty">${escapeHtml(t("folder-recent-empty"))}</div>`;return}b.innerHTML=_.slice(0,20).map(C=>{let T;C.status==="ok"?T=`<span class="folder-recent-icon ok">${svgIcon("check",12)}</span>`:C.status==="dup"?T=`<span class="folder-recent-icon dup" title="${escapeHtml(t("folder-recent-dup"))}">${svgIcon("copy",12)}</span>`:C.status==="skip"?T=`<span class="folder-recent-icon skip" title="${escapeHtml(t("folder-recent-skip"))}">${svgIcon("minus",12)}</span>`:T=`<span class="folder-recent-icon fail">${svgIcon("alert",12)}</span>`;const U=C.status==="fail"&&C.error?C.error:C.status==="dup"&&C.reason||C.status==="skip"&&C.reason?C.reason:"",z=U?`<div class="folder-recent-err">${escapeHtml(U)}</div>`:"";return`
                <div class="folder-recent-item">
                    ${T}
                    <div class="folder-recent-body">
                        <div class="folder-recent-name">${escapeHtml(C.name)}</div>
                        ${z}
                    </div>
                    <div class="folder-recent-time">${h(C.time)}</div>
                </div>
            `}).join("")}}function $(b){_.unshift(b),_.length>50&&(_.length=50),N("config","recent_list",_).catch(()=>{})}async function E(b){const C=new FormData;C.append("file",b,b.name),C.append("source","folder");const T=await fetch("/api/ocr/recognize?source=folder",{method:"POST",headers:{Authorization:"Bearer "+token,"X-Source":"folder"},body:C});if(!T.ok){let U="http_"+T.status;try{const z=await T.json();U=z&&z.detail?typeof z.detail=="string"?z.detail:z.detail.code||JSON.stringify(z.detail):U}catch{}throw new Error(U)}return await T.json()}async function M(b){try{const T=(await b.getFile()).size;return await new Promise(z=>setTimeout(z,3e3)),(await b.getFile()).size===T&&T>0}catch{return!1}}async function K(b,C,T,U){if(U>10)return;let z;try{z=await b.queryPermission({mode:"read"})}catch{z="denied"}if(z==="granted")for await(const u of b.values()){const P=C?`${C}/${u.name}`:u.name;if(u.kind==="file"){if(!a.test(u.name))continue;let O;try{O=await u.getFile()}catch{continue}const Y=`${P}::${O.size}::${O.lastModified}`;if(await B("seen",Y))continue;T.push({entry:u,file:O,seenKey:Y,relPath:P})}else if(u.kind==="directory")try{await K(u,P,T,U+1)}catch{}}}async function G(){if(!(d||r||!l)){d=!0;try{if(await l.queryPermission({mode:"read"})!=="granted"){console.warn("[folder] permission lost · stop"),J(),showToast("warn",t("folder-permission-lost"));return}q=new Date;const C=[];await K(l,"",C,0),x=C.length,I();for(const T of C){if(r)break;if(!await M(T.entry)){x=Math.max(0,x-1),I();continue}try{let z;try{z=await T.entry.getFile()}catch{z=T.file}const u=await E(z);await N("seen",T.seenKey,{name:z.name,relPath:T.relPath,size:z.size,lastModified:z.lastModified,processed_at:Date.now()});const P=u.history_ids||(u.history_id?[u.history_id]:[]),O=u.duplicate_warnings||[],Y=T.relPath||z.name;P.length>0?(c+=P.length,$({name:Y,status:"ok",time:new Date,history_id:P[0],count:P.length}),await N("config","processed_count",c)):O.length>0?$({name:Y,status:"dup",time:new Date,reason:t("folder-recent-dup-reason")}):$({name:Y,status:"skip",time:new Date,reason:t("folder-recent-skip-reason")})}catch(z){v++,$({name:T.relPath||T.file.name,status:"fail",time:new Date,error:String(z.message||z)}),await N("config","failed_count",v)}x=Math.max(0,x-1),I()}}catch(b){console.warn("[folder] scan error:",b)}finally{d=!1,I()}}}function W(){y&&clearInterval(y),y=setInterval(G,i*1e3)}function te(){y&&(clearInterval(y),y=null)}function re(b){if(!l||r)return;const C=typeof t=="function"?t("folder-unload-warn"):"Folder watcher running · close anyway?";return b.preventDefault(),b.returnValue=C,C}function S(){window._pearnlyFolderUnloadAttached||(window._pearnlyFolderUnloadAttached=!0,window.addEventListener("beforeunload",re))}function w(){window._pearnlyFolderUnloadAttached&&(window._pearnlyFolderUnloadAttached=!1,window.removeEventListener("beforeunload",re))}function m(){r=!1,W(),S(),I(),G()}function H(){r=!0,te(),w(),I()}function D(){r=!1,W(),S(),I(),G()}function J(){r=!0,te(),w()}async function Z(){try{const b=await window.showDirectoryPicker({mode:"read",startIn:"documents"});if(!await A(b)){showToast("warn",t("folder-permission-denied"));return}l=b,await N("handles","main",b),c=0,v=0,x=0,_=[],await N("config","processed_count",0),await N("config","failed_count",0),await F("seen"),m()}catch(b){b&&b.name!=="AbortError"&&console.warn("[folder] pick failed:",b)}}async function le(){await showConfirm(t("folder-confirm-remove"),{danger:!0})&&(J(),l=null,c=0,v=0,x=0,_=[],await R("handles","main"),await R("config","processed_count"),await R("config","failed_count"),await F("seen"),f("folder-empty"),g("folder-status-empty",""))}async function ie(){_=[];try{await R("config","recent_list")}catch{}L()}async function V(){if(j)return;if(j=!0,!n){f("folder-unsupported"),g("folder-status-unsupported",""),ne();return}Q();let b=null;try{b=await B("handles","main")}catch{}if(!b){f("folder-empty"),g("folder-status-empty","");return}if(!await A(b)){f("folder-empty"),g("folder-status-empty",""),await R("handles","main"),showToast("warn",t("folder-permission-lost-restart"));return}l=b;try{c=await B("config","processed_count")||0}catch{}try{v=await B("config","failed_count")||0}catch{}try{const T=await B("config","recent_list");Array.isArray(T)&&(_=T.map(U=>({...U,time:U.time?new Date(U.time):new Date})))}catch{}m()}function Q(){const b=document.getElementById("btn-folder-pick"),C=document.getElementById("btn-folder-pause"),T=document.getElementById("btn-folder-resume"),U=document.getElementById("btn-folder-scan-now"),z=document.getElementById("btn-folder-remove"),u=document.getElementById("btn-folder-clear-recent"),P=document.getElementById("folder-interval-select");b&&b.addEventListener("click",Z),C&&C.addEventListener("click",H),T&&T.addEventListener("click",D),U&&U.addEventListener("click",()=>{G()}),z&&z.addEventListener("click",le),u&&u.addEventListener("click",ie),P&&P.addEventListener("change",O=>{i=parseInt(O.target.value,10)||60,r||W()}),ee()}function ee(){document.querySelectorAll('[data-auto-panel="folder"] [data-tab-jump]').forEach(b=>{b.dataset.tabJumpBound||(b.dataset.tabJumpBound="1",b.addEventListener("click",C=>{const T=C.currentTarget.dataset.tabJump;if(T==="email")typeof switchAutomationTab=="function"&&switchAutomationTab("email");else if(T==="upload"){const U=document.querySelector('[data-page="recognize"]')||document.querySelector('[data-page="upload"]');U&&U.click()}}))})}function ne(){ee()}window._loadFolderWatcherPanel=V;function oe(){try{if(navigator.userAgentData&&Array.isArray(navigator.userAgentData.brands))return navigator.userAgentData.brands.some(C=>/chromium|google chrome|microsoft edge/i.test(C.brand||""))}catch{}const b=navigator.userAgent||"";return!!(/Edg\//.test(b)||/Chrome\//.test(b)&&!/OPR\/|YaBrowser|Opera/.test(b))}function ue(){try{if(oe()||localStorage.getItem("pearnly_chrome_banner_dismissed")==="1")return;const b=document.getElementById("chrome-only-banner");if(!b)return;const C=b.querySelector('[data-i18n="chrome-banner-msg"]'),T=b.querySelector('[data-i18n="chrome-banner-dismiss"]');C&&typeof t=="function"&&(C.textContent=t("chrome-banner-msg")),T&&typeof t=="function"&&(T.textContent=t("chrome-banner-dismiss")),b.style.display="";const U=document.getElementById("chrome-only-banner-close");U&&!U.dataset.bound&&(U.dataset.bound="1",U.addEventListener("click",()=>{b.style.display="none";try{localStorage.setItem("pearnly_chrome_banner_dismissed","1")}catch{}}))}catch{}}typeof document<"u"&&(document.readyState==="loading"?document.addEventListener("DOMContentLoaded",ue):setTimeout(ue,0)),window._refreshChromeBanner=ue})();(function(){let e=null,n=null,a="new",o=!1,s=!1;async function p(){const E=document.getElementById("email-empty"),M=document.getElementById("email-account-card");if(document.getElementById("email-logs-section"),!(!E||!M))try{const K=await fetch("/api/email-ingest/account",{headers:{Authorization:"Bearer "+token}});if(K.status===401){localStorage.removeItem("mrpilot_token");const W=await K.json().catch(()=>({}));if((typeof W.detail=="string"?W.detail:W.detail&&W.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}if(!K.ok){y("none");return}const G=await K.json();e=G.account||null,n=G.presets||{},o=!0,l(),e&&h()}catch(K){console.error("[email-ingest] load failed",K),y("none")}}function l(){const E=document.getElementById("email-empty"),M=document.getElementById("email-account-card"),K=document.getElementById("email-logs-section");if(!e){E.style.display="",M.style.display="none",K&&(K.style.display="none"),y("none");return}E.style.display="none",M.style.display="",K&&(K.style.display="");const G=document.getElementById("email-account-addr"),W=document.getElementById("email-account-host"),te=document.getElementById("email-account-last"),re=document.getElementById("email-last-error"),S=document.getElementById("email-enabled-toggle");if(G&&(G.textContent=e.email_address||"-"),W&&(W.textContent=`${e.imap_host||"-"}:${e.imap_port||993}`),te){const w=e.last_fetched_at;if(!w)te.textContent=t("email-last-never");else{const m=i(w),H=!e.last_error;te.textContent=H?t("email-last-ok",{time:m}):t("email-last-fail",{time:m})}}re&&(e.last_error?(re.style.display="",re.textContent=r(e.last_error)):re.style.display="none"),S&&(S.checked=!!e.enabled),e.enabled?e.last_error?y("error"):y("on"):y("off")}function y(E){const M=document.getElementById("email-status-summary");if(!M)return;M.classList.remove("none","ready","active","coming");let K="auto-status-loading";E==="none"?(K="email-status-none",M.classList.add("none")):E==="on"?(K="email-status-on",M.classList.add("active")):E==="off"?(K="email-status-off",M.classList.add("coming")):E==="error"&&(K="email-status-error",M.classList.add("none")),M.setAttribute("data-i18n",K),M.textContent=t(K)}function i(E){if(!E)return"";const M=new Date(E);if(isNaN(M.getTime()))return"";const K=G=>String(G).padStart(2,"0");return`${K(M.getMonth()+1)}-${K(M.getDate())} ${K(M.getHours())}:${K(M.getMinutes())}`}function r(E){if(!E)return"";const M=String(E);return/auth|AUTHENTICATIONFAILED|invalid credentials/i.test(M)?t("email-test-auth-fail"):/timeout|timed out/i.test(M)?t("email.timeout"):(/ENOTFOUND|getaddrinfo/i.test(M),M)}function d(E){a=E;const M=document.getElementById("email-modal");if(!M)return;const K=document.getElementById("email-preset");K.innerHTML="";const G=n||{},W=["gmail","outlook","yahoo","icloud","qq","163","custom"],te={gmail:"Gmail",outlook:"Outlook / Office365",yahoo:"Yahoo Mail",icloud:"iCloud",qq:"QQ 邮箱",163:"网易 163"};W.forEach(Q=>{if(!G[Q])return;const ee=document.createElement("option");ee.value=Q,ee.textContent=Q==="custom"?t("email-preset-custom"):te[Q]||Q,K.appendChild(ee)});const re=document.getElementById("email-modal-title"),S=document.getElementById("email-address"),w=document.getElementById("email-password"),m=document.getElementById("email-imap-host"),H=document.getElementById("email-imap-port"),D=document.getElementById("email-imap-ssl"),J=document.getElementById("email-folder"),Z=document.getElementById("email-mark-read"),le=document.getElementById("email-bind-enabled"),ie=document.getElementById("email-test-result"),V=document.getElementById("email-adv-details");if(ie&&(ie.style.display="none",ie.textContent=""),E==="edit"&&e){re.setAttribute("data-i18n","email-modal-title-edit"),re.textContent=t("email-modal-title-edit"),S.value=e.email_address||"",w.value="",w.setAttribute("data-i18n-placeholder","email-field-password-edit-ph"),w.placeholder=t("email-field-password-edit-ph"),m.value=e.imap_host||"",H.value=e.imap_port||993,D.checked=e.imap_use_ssl!==!1,J.value=e.folder||"INBOX",Z.checked=e.mark_as_read!==!1,le.checked=e.enabled!==!1;const Q=document.getElementById("email-filter-sender"),ee=document.getElementById("email-filter-subject");Q&&(Q.value=e.filter_sender||""),ee&&(ee.value=e.filter_subject||""),B(e.interval_min||15),K.value=q(e.imap_host)||"custom",V&&(V.open=!0)}else{re.setAttribute("data-i18n","email-modal-title-new"),re.textContent=t("email-modal-title-new"),S.value="",w.value="",w.setAttribute("data-i18n-placeholder","email-field-password-ph"),w.placeholder=t("email-field-password-ph"),K.value="gmail",v("gmail"),J.value="INBOX",Z.checked=!0,le.checked=!0;const Q=document.getElementById("email-filter-sender"),ee=document.getElementById("email-filter-subject");Q&&(Q.value=""),ee&&(ee.value=""),B(15),V&&(V.open=!1)}k(),M.style.display="flex",setTimeout(()=>S.focus(),60)}function c(){const E=document.getElementById("email-modal");E&&(E.style.display="none")}function v(E){const M=(n||{})[E];if(!M||E==="custom")return;const K=document.getElementById("email-imap-host"),G=document.getElementById("email-imap-port"),W=document.getElementById("email-imap-ssl");K&&(K.value=M.host||""),G&&(G.value=M.port||993),W&&(W.checked=M.ssl!==!1)}const x={"gmail.com":"gmail","googlemail.com":"gmail","outlook.com":"outlook","hotmail.com":"outlook","live.com":"outlook","office365.com":"outlook","msn.com":"outlook","yahoo.com":"yahoo","yahoo.co.jp":"yahoo","icloud.com":"icloud","me.com":"icloud","mac.com":"icloud","qq.com":"qq","foxmail.com":"qq","163.com":"163","126.com":"163","yeah.net":"163"};function _(E){if(!E||!E.includes("@"))return;const M=E.split("@")[1].toLowerCase().trim(),K=x[M];if(!K)return;const G=document.getElementById("email-preset");if(!G)return;const W=G.value;W&&W!=="custom"&&W!==""&&W===K||(G.value=K,v(K))}function q(E){if(!E)return null;const M=n||{};for(const K in M)if(K!=="custom"&&M[K]&&M[K].host===E)return K;return null}function j(){const E=document.querySelector("#email-interval-options .email-interval-btn.active"),M=E?parseInt(E.dataset.interval,10):15;return{email_address:(document.getElementById("email-address").value||"").trim(),password:document.getElementById("email-password").value||"",imap_host:(document.getElementById("email-imap-host").value||"").trim(),imap_port:parseInt(document.getElementById("email-imap-port").value||"993",10)||993,imap_use_ssl:document.getElementById("email-imap-ssl").checked,folder:(document.getElementById("email-folder").value||"INBOX").trim()||"INBOX",mark_as_read:document.getElementById("email-mark-read").checked,enabled:document.getElementById("email-bind-enabled").checked,interval_min:[5,15,60].includes(M)?M:15,filter_sender:(document.getElementById("email-filter-sender").value||"").trim()||null,filter_subject:(document.getElementById("email-filter-subject").value||"").trim()||null}}function k(){const E=document.getElementById("email-interval-options");!E||E._bound||(E._bound=!0,E.addEventListener("click",M=>{const K=M.target.closest(".email-interval-btn");K&&(E.querySelectorAll(".email-interval-btn").forEach(G=>G.classList.remove("active")),K.classList.add("active"))}))}function B(E){const M=[5,15,60].includes(E)?E:15,K=document.getElementById("email-interval-options");K&&K.querySelectorAll(".email-interval-btn").forEach(G=>{G.classList.toggle("active",parseInt(G.dataset.interval,10)===M)})}function N(E,M){const K=document.getElementById("email-test-result");K&&(K.style.display="",K.textContent=M,K.className="form-test-result "+(E==="ok"?"ok":E==="running"?"running":"fail"))}async function R(){const E=j();if(!E.email_address){N("fail",t("email-addr-required"));return}if(!E.password){N("fail",t("email-password-required"));return}if(!E.imap_host){N("fail",t("email-host-required"));return}const M=document.getElementById("btn-email-modal-test");M&&(M.disabled=!0),N("running",t("email-test-running"));try{const K=await fetch("/api/email-ingest/test",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:E.email_address,password:E.password,imap_host:E.imap_host,imap_port:E.imap_port,imap_use_ssl:E.imap_use_ssl,folder:E.folder})}),G=await K.json().catch(()=>({}));if(K.ok&&G.success)N("ok",t("email-test-ok",{folder:E.folder,n:G.folder_count??"?"}));else{const W=G.error_msg||"";W==="auth_failed"||/auth/i.test(W)?N("fail",t("email-test-auth-fail")):N("fail",t("email-test-fail",{msg:W||K.status}))}}catch(K){N("fail",t("email-test-fail",{msg:String(K).slice(0,120)}))}finally{M&&(M.disabled=!1)}}async function F(){const E=j();if(!E.email_address){N("fail",t("email-addr-required"));return}if(a==="new"&&!E.password){N("fail",t("email-password-required"));return}if(!E.imap_host){N("fail",t("email-host-required"));return}const M=document.getElementById("btn-email-modal-save");M&&(M.disabled=!0);const K={...E};a==="edit"&&!K.password&&delete K.password;try{const G=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(K)}),W=await G.json().catch(()=>({}));if(G.ok&&W.ok)e=W.account,showToast(t("email-save-ok"),"success"),c(),l(),h();else{const re="email."+(W.detail||"").split(".").slice(-1)[0];N("fail",t(re)!==re?t(re):t("email-save-fail"))}}catch{N("fail",t("email-save-fail"))}finally{M&&(M.disabled=!1)}}async function A(){if(!(!e||!await showConfirm(t("email-unbind-confirm",{email:e.email_address}),{danger:!0,okText:t("email-btn-unbind")})))try{if((await fetch("/api/email-ingest/account",{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){e=null,showToast(t("email-unbind-ok"),"success"),l();const K=document.getElementById("email-logs-list");K&&(K.innerHTML="")}else showToast(t("email-unbind-fail"),"error")}catch{showToast(t("email-unbind-fail"),"error")}}async function g(){if(!e||s)return;if(!e.enabled){showToast(t("email.disabled"),"error");return}s=!0;const E=document.getElementById("btn-email-trigger"),M=E?E.innerHTML:"";E&&(E.disabled=!0,E.innerHTML=`<span>${escapeHtml(t("email-trigger-running"))}</span>`);try{const K=await fetch("/api/email-ingest/trigger",{method:"POST",headers:{Authorization:"Bearer "+token}}),G=await K.json().catch(()=>({}));if(K.ok){const W=G.emails_scanned||0,te=G.ocr_succeeded||0,re=G.ocr_failed||0;W===0&&te===0&&re===0?showToast(t("email-trigger-empty"),"success"):showToast(t("email-trigger-result",{scanned:W,ok:te,fail:re}),re>0?"warn":"success")}else{const te="email."+(G.detail||"").split(".").slice(-1)[0];showToast(t(te)!==te?t(te):t("email-trigger-fail"),"error")}await p()}catch{showToast(t("email-trigger-fail"),"error")}finally{s=!1,E&&(E.disabled=!1,E.innerHTML=M)}}async function f(){if(!e)return;const E=document.getElementById("email-enabled-toggle"),M=!!(E&&E.checked),K=e.enabled;try{const G=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:e.email_address,imap_host:e.imap_host,imap_port:e.imap_port,imap_use_ssl:e.imap_use_ssl,folder:e.folder||"INBOX",filter_subject:e.filter_subject||null,filter_sender:e.filter_sender||null,mark_as_read:e.mark_as_read!==!1,enabled:M})}),W=await G.json().catch(()=>({}));G.ok&&W.ok?(e=W.account,l()):(E&&(E.checked=K),showToast(t("email-toggle-fail"),"error"))}catch{E&&(E.checked=K),showToast(t("email-toggle-fail"),"error")}}async function h(){const E=document.getElementById("email-logs-list");if(E){E.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`;try{const M=await fetch("/api/email-ingest/logs?limit=20",{headers:{Authorization:"Bearer "+token}});if(!M.ok){E.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const K=await M.json();if(!Array.isArray(K)||K.length===0){E.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("email-logs-empty"))}</div>`;return}E.innerHTML=K.map(I).join("")}catch{E.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}function I(E){const M=i(E.created_at),K=E.status||"failed",G=K==="success"?"ok":K==="partial"?"partial":"fail",W=K==="success"?"✓":K==="partial"?"◐":"✗",te=E.trigger==="manual"?`<span class="log-tag manual">${escapeHtml(t("email-log-tag-manual"))}</span>`:`<span class="log-tag auto">${escapeHtml(t("email-log-tag-auto"))}</span>`,re=t("email-log-counts",{scanned:E.emails_scanned||0,att:E.attachments_found||0,ok:E.ocr_succeeded||0,fail:E.ocr_failed||0}),S=(E.elapsed_ms||0)+"ms";return`
            <div class="email-log-row ${G}">
                <span class="log-time">${escapeHtml(M)}</span>
                <span class="log-status">${W}</span>
                ${te}
                <span class="log-counts">${escapeHtml(re)}</span>
                <span class="log-elapsed">${escapeHtml(S)}</span>
            </div>
        `}function L(){const E=document.getElementById("btn-email-bind");E&&E.addEventListener("click",()=>d("new"));const M=document.getElementById("btn-email-edit");M&&M.addEventListener("click",()=>d("edit"));const K=document.getElementById("btn-email-unbind");K&&K.addEventListener("click",A);const G=document.getElementById("btn-email-trigger");G&&G.addEventListener("click",g);const W=document.getElementById("email-enabled-toggle");W&&W.addEventListener("change",f);const te=document.getElementById("email-modal-close");te&&te.addEventListener("click",c);const re=document.getElementById("btn-email-modal-cancel");re&&re.addEventListener("click",c);const S=document.getElementById("btn-email-modal-test");S&&S.addEventListener("click",R);const w=document.getElementById("btn-email-modal-save");w&&w.addEventListener("click",F);const m=document.getElementById("email-preset");m&&m.addEventListener("change",J=>v(J.target.value));const H=document.getElementById("email-address");H&&!H.dataset.autoBound&&(H.dataset.autoBound="1",H.addEventListener("blur",J=>_((J.target.value||"").trim())),H.addEventListener("input",J=>{const Z=(J.target.value||"").trim();Z.includes("@")&&Z.split("@")[1].includes(".")&&_(Z)}));const D=document.getElementById("btn-email-refresh-logs");D&&D.addEventListener("click",()=>{D.classList.add("spinning"),setTimeout(()=>D.classList.remove("spinning"),600),h()})}L(),window._loadEmailIngestPanel=p,window._rerenderEmailIngest=function(){if(!o)return;l();const E=document.getElementById("email-logs-section");e&&E&&E.open&&h()};let $=null;window._startEmailLogAutoRefresh=function(){$||($=setInterval(()=>{e&&o&&h()},3e4))},window._stopEmailLogAutoRefresh=function(){$&&(clearInterval($),$=null)}})();(function(){let e=[],n=null,a=[],o="all",s=null,p=!1;async function l(){if(p){L();return}p=!0,y(),await i(),L()}function y(){const u=document.getElementById("bank-file-input");u&&!u._bound&&(u._bound=!0,u.addEventListener("change",_));const P=document.getElementById("btn-bank-queue-clear-done");P&&!P._bound&&(P._bound=!0,P.addEventListener("click",R));const O=document.getElementById("btn-bank-back");O&&!O._bound&&(O._bound=!0,O.addEventListener("click",()=>{n=null,a=[],te()}));const Y=document.getElementById("btn-bank-delete");Y&&!Y._bound&&(Y._bound=!0,Y.addEventListener("click",f));const X=document.getElementById("btn-bank-run-match");X&&!X._bound&&(X._bound=!0,X.addEventListener("click",g)),document.querySelectorAll(".bank-filter-btn").forEach(ve=>{ve._bound||(ve._bound=!0,ve.addEventListener("click",()=>{o=ve.dataset.bankFilter||"all",document.querySelectorAll(".bank-filter-btn").forEach(fe=>{fe.classList.toggle("active",fe===ve)}),Z()}))}),document.querySelectorAll("[data-bank-cand-close]").forEach(ve=>{ve._bound||(ve._bound=!0,ve.addEventListener("click",ne))});const de=document.getElementById("btn-bank-cand-pane-close");de&&!de._bound&&(de._bound=!0,de.addEventListener("click",ne));const se=document.getElementById("btn-bank-cand-ignore");se&&!se._bound&&(se._bound=!0,se.addEventListener("click",h));const ce=document.getElementById("btn-bank-cand-ignore-pane");ce&&!ce._bound&&(ce._bound=!0,ce.addEventListener("click",h));const ae=document.getElementById("bank-client-badge");ae&&!ae._bound&&(ae._bound=!0,ae.addEventListener("click",w)),document.querySelectorAll("[data-bank-client-picker-close]").forEach(ve=>{ve._bound||(ve._bound=!0,ve.addEventListener("click",m))});const pe=document.getElementById("btn-bank-client-picker-save");pe&&!pe._bound&&(pe._bound=!0,pe.addEventListener("click",D)),document.querySelectorAll(".bank-sessions-chip").forEach(ve=>{ve._bound||(ve._bound=!0,ve.addEventListener("click",()=>{$=ve.dataset.sessFilter||"all",document.querySelectorAll(".bank-sessions-chip").forEach(fe=>{fe.classList.toggle("active",fe===ve)}),E()}))})}async function i(){try{const u=await fetch("/api/bank-recon/sessions?limit=30",{headers:{Authorization:"Bearer "+token}});if(!u.ok)throw new Error("sessions:"+u.status);e=await u.json(),E()}catch(u){console.warn("[bank-recon] loadSessions failed",u),e=[],E()}}async function r(u){try{const P="/api/bank-recon/sessions/"+encodeURIComponent(u)+(o!=="all"?"?filter="+o:""),O=await fetch(P,{headers:{Authorization:"Bearer "+token}});if(!O.ok)throw new Error("detail:"+O.status);const Y=await O.json();n=Y.session,a=Y.transactions||[],W()}catch(P){console.warn("[bank-recon] loadSessionDetail failed",P),showToast(t("bank-load-failed"),"error")}}let d=[],c=0;const v=3;function x(){return c+=1,"q"+c+"_"+Date.now()}async function _(u){const P=Array.from(u.target.files||[]);if(u.target.value="",P.length!==0){for(const O of P){const Y={id:x(),file:O,name:O.name,size:O.size,status:"pending",progress:0,error_code:null,tx_count:0,session_id:null};O.name.toLowerCase().endsWith(".pdf")?O.size>20*1024*1024&&(Y.status="failed",Y.error_code="bank_recon.file_too_large"):(Y.status="failed",Y.error_code="bank_recon.only_pdf"),d.push(Y)}q(),j(),F()}}function q(){const u=document.getElementById("bank-upload-queue");u&&(u.style.display=""),oe(),ue()}function j(){const u=document.getElementById("bank-upload-queue-list"),P=document.getElementById("bank-upload-queue-summary");if(!u)return;if(d.length===0){u.innerHTML="",P&&(P.textContent="");const se=document.getElementById("bank-upload-queue");se&&(se.style.display="none");return}let O=0,Y=0,X=0,de=0;for(const se of d)se.status==="ok"?O++:se.status==="failed"?Y++:se.status==="uploading"||se.status==="parsing"?X++:de++;P&&(P.textContent=t("bank-queue-summary").replace("{ok}",O).replace("{run}",X).replace("{wait}",de).replace("{fail}",Y)),u.innerHTML=d.map(k).join(""),u.querySelectorAll("[data-q-act]").forEach(se=>{const ce=se.dataset.qAct,ae=se.dataset.qId;se.addEventListener("click",()=>{ce==="retry"&&B(ae),ce==="remove"&&N(ae)})})}function k(u){const P=(u.size/1024).toFixed(0)+" KB";let O="",Y="";if(u.status==="pending")O='<span class="bq-stat bq-wait">'+t("bank-queue-status-wait")+"</span>",Y='<button data-q-act="remove" data-q-id="'+z(u.id)+'" class="bq-act">×</button>';else if(u.status==="uploading")O='<span class="bq-stat bq-run">'+t("bank-queue-status-uploading")+'</span><div class="bq-bar"><div class="bq-bar-fill" style="width:'+(u.progress||0)+'%"></div></div>';else if(u.status==="parsing")O='<span class="bq-stat bq-run">'+t("bank-queue-status-parsing")+'</span><div class="bq-bar"><div class="bq-bar-fill bq-bar-indet"></div></div>';else if(u.status==="ok")O='<span class="bq-stat bq-ok">'+t("bank-queue-status-ok").replace("{n}",u.tx_count||0)+"</span>",Y='<button data-q-act="remove" data-q-id="'+z(u.id)+'" class="bq-act">×</button>';else if(u.status==="failed"){const X=b(u.error_code||"unknown");O='<span class="bq-stat bq-fail" title="'+z(X)+'">'+z(X)+"</span>",Y='<button data-q-act="retry" data-q-id="'+z(u.id)+'" class="bq-act bq-act-retry">'+t("bank-queue-retry")+'</button><button data-q-act="remove" data-q-id="'+z(u.id)+'" class="bq-act">×</button>'}return'<div class="bq-row" data-q-row="'+z(u.id)+'"><div class="bq-name" title="'+z(u.name)+'">'+z(u.name)+'</div><div class="bq-size">'+P+'</div><div class="bq-status">'+O+'</div><div class="bq-actions">'+Y+"</div></div>"}function B(u){const P=d.find(O=>O.id===u);P&&(P.status="pending",P.error_code=null,P.progress=0,j(),F())}function N(u){const P=d.findIndex(Y=>Y.id===u);if(P<0)return;const O=d[P];O.status==="uploading"||O.status==="parsing"||(d.splice(P,1),j())}function R(){d=d.filter(u=>u.status!=="ok"),j()}async function F(){for(;;){if(d.filter(O=>O.status==="uploading"||O.status==="parsing").length>=v)return;const P=d.find(O=>O.status==="pending");if(!P){d.every(O=>O.status==="ok"||O.status==="failed")&&(await i(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage());return}A(P).then(()=>F())}}async function A(u){u.status="uploading",u.progress=0,j();try{const P=new FormData;P.append("file",u.file,u.name);const O=await new Promise((X,de)=>{const se=new XMLHttpRequest;se.open("POST","/api/bank-recon/upload"),se.setRequestHeader("Authorization","Bearer "+token),se.upload.onprogress=ce=>{ce.lengthComputable&&(u.progress=Math.min(99,Math.round(ce.loaded/ce.total*100)),j())},se.upload.onload=()=>{u.status="parsing",j()},se.onload=()=>{se.status>=200&&se.status<300?X({status:se.status,text:se.responseText}):X({status:se.status,text:se.responseText})},se.onerror=()=>de(new Error("network")),se.send(P)});let Y={};try{Y=JSON.parse(O.text||"{}")}catch{Y={}}if(O.status>=400){u.status="failed",u.error_code=Y&&Y.detail||"unknown",j();return}if(Y.parse_status==="parse_failed"){u.status="failed",u.error_code=Y.error==="scanned_pdf_not_yet"?"bank_recon.scanned":"bank_recon.no_tx",j();return}u.status="ok",u.tx_count=Y.tx_count||0,u.session_id=Y.session_id||null,j()}catch(P){console.warn("[bank-recon] upload failed",P),u.status="failed",u.error_code="network",j()}}async function g(){if(!n)return;const u=document.getElementById("btn-bank-run-match"),P=u.innerHTML;u.disabled=!0,u.innerHTML="<span>"+t("bank-matching")+"</span>";try{const O=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id)+"/match",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!O.ok)throw new Error("match:"+O.status);const Y=await O.json();showToast(t("bank-match-done").replace("{matched}",Y.matched).replace("{suggested}",Y.suggested).replace("{unmatched}",Y.unmatched),"success"),await r(n.id),await i()}catch(O){console.warn("[bank-recon] match failed",O),showToast(t("bank-match-failed"),"error")}finally{u.disabled=!1,u.innerHTML=P}}async function f(){if(!(!n||!await showConfirm(t("bank-delete-confirm"),{danger:!0})))try{const P=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!P.ok)throw new Error("delete:"+P.status);showToast(t("bank-deleted"),"success"),n=null,a=[],te(),await i()}catch(P){console.warn("[bank-recon] delete failed",P),showToast(t("bank-delete-failed"),"error")}}async function h(){if(s)try{const u=await fetch("/api/bank-recon/tx/"+encodeURIComponent(s.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"ignored"})});if(!u.ok)throw new Error("ignore:"+u.status);ne(),await r(n.id)}catch{showToast(t("bank-action-failed"),"error")}}async function I(u){if(s)try{const P=await fetch("/api/bank-recon/tx/"+encodeURIComponent(s.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"matched",history_id:u})});if(!P.ok)throw new Error("pick:"+P.status);showToast(t("bank-matched-ok"),"success"),ne(),await r(n.id)}catch{showToast(t("bank-action-failed"),"error")}}function L(){const u=document.getElementById("bank-status-summary");if(!u)return;if(e.length===0){u.textContent=t("bank-pill-none");return}let O=0;for(const Y of e)Y.parse_status==="parsed"&&(Y.unmatched_count||0)>0&&O++;u.textContent=O>0?t("bank-pill-pending").replace("{n}",O):t("bank-pill-ok")}let $="all";function E(){const u=document.getElementById("bank-sessions-list");if(!u)return;let P=e||[];if($==="parsed"?P=P.filter(O=>O.parse_status==="parsed"):$==="failed"&&(P=P.filter(O=>O.parse_status==="parse_failed")),!e||e.length===0){u.innerHTML='<div class="bank-empty" data-i18n="bank-sessions-empty">'+t("bank-sessions-empty")+"</div>";return}if(P.length===0){u.innerHTML='<div class="bank-empty">'+t("bank-sess-filter-empty")+"</div>";return}u.innerHTML=P.map(O=>K(O)).join(""),u.querySelectorAll(".bank-session-row").forEach(O=>{O.addEventListener("click",Y=>{Y.target.closest(".bank-session-trash")||r(O.dataset.sessionId)})}),u.querySelectorAll(".bank-session-trash").forEach(O=>{O.addEventListener("click",Y=>{Y.stopPropagation();const X=O.dataset.sessionId,de=O.dataset.sessionName||"";M(X,de)})})}async function M(u,P){if(!u)return;const O=(t("bank-session-delete-confirm")||"确定删除这条对账记录吗?").replace("{name}",P||"");if(await showConfirm(O,{danger:!0}))try{const X=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(u),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!X.ok)throw new Error("delete:"+X.status);showToast(t("bank-deleted"),"success"),n&&n.id===u&&(n=null,a=[],te()),await i(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()}catch(X){console.warn("[bank-recon] delete failed",X),showToast(t("bank-delete-failed"),"error")}}window._deleteBankSession=M;function K(u){const P=(u.bank_code||"OTHER").toUpperCase(),O=U(u.period_start,u.period_end),Y=u.account_last4?"···"+u.account_last4:"",X=G(u),de=T(u.created_at);return`
            <div class="bank-session-row" data-session-id="${z(u.id)}">
                <div class="bank-session-bank bk-${z(P)}">${z(P)}</div>
                <div class="bank-session-info">
                    <div class="bank-session-title">${z(u.source_filename||O||"-")}</div>
                    <div class="bank-session-meta">${z(O)} · ${z(Y)} · ${z(de)}</div>
                </div>
                <div class="bank-session-counts">${X}</div>
                <button class="bank-session-trash" data-session-id="${z(u.id)}" data-session-name="${z(u.source_filename||"")}" title="${z(t("bank-session-delete-tip")||"删除")}">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/>
                    </svg>
                </button>
                <div class="bank-session-arrow">
                    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg>
                </div>
            </div>
        `}function G(u){if(u.parse_status==="parse_failed")return`<span class="bank-session-count cnt-failed">${t("bank-count-parse-failed")}</span>`;if(u.parse_status!=="parsed")return`<span class="bank-session-count">${t("bank-count-parsing")}</span>`;const P=u.tx_count||0,O=u.matched_count||0,Y=u.unmatched_count||0,X=[`<span class="bank-session-count">${P} ${t("bank-count-tx")}</span>`];return O>0&&X.push(`<span class="bank-session-count cnt-matched">${O} ${t("bank-count-matched")}</span>`),Y>0&&X.push(`<span class="bank-session-count cnt-unmatched">${Y} ${t("bank-count-unmatched")}</span>`),X.join("")}function W(){document.getElementById("bank-detail").style.display="",document.querySelector(".bank-sessions-section").style.display="none",J(),Z(),re()}function te(){document.getElementById("bank-detail").style.display="none",document.querySelector(".bank-sessions-section").style.display="";const u=document.getElementById("bank-detail-body");u&&u.classList.remove("has-pane"),s=null}function re(){const u=document.getElementById("bank-client-badge");if(!u||!n)return;const P=n.client_id,O=document.getElementById("bank-client-badge-dot"),Y=document.getElementById("bank-client-badge-name"),X=document.getElementById("bank-client-badge-caret"),de=typeof _userInfo<"u"?_userInfo:null,se=!(de&&de.role==="member");if(P!=null){const ce=(window._clientsCache||[]).find(ae=>Number(ae.id)===Number(P));u.classList.remove("is-empty"),O&&(O.style.background=ce&&ce.color||"#111111"),Y&&(Y.textContent=ce&&(ce.short_name||ce.name)||"#"+P)}else u.classList.add("is-empty"),O&&(O.style.background=""),Y&&(Y.textContent=t("bank-client-none"));se?(u.classList.remove("is-readonly"),u.disabled=!1,X&&(X.style.display="")):(u.classList.add("is-readonly"),u.disabled=!0,X&&(X.style.display="none")),u.style.display=""}let S=null;function w(){if(!n)return;const u=typeof _userInfo<"u"?_userInfo:null;if(!!(u&&u.role==="member"))return;S=n.client_id!=null?Number(n.client_id):null,H();const O=document.getElementById("bank-client-picker-modal");O&&(O.style.display="")}function m(){const u=document.getElementById("bank-client-picker-modal");u&&(u.style.display="none"),S=null}function H(){const u=document.getElementById("bank-client-picker-list");if(!u)return;const P=(window._clientsCache||[]).filter(Y=>Y&&(Y.is_active===!0||Y.is_active===void 0)),O=[];O.push('<div class="bank-client-picker-row is-none'+(S==null?" is-selected":"")+'" data-cid=""><span class="bank-cp-dot"></span><span>'+z(t("bank-client-picker-none"))+"</span></div>"),P.forEach(Y=>{const X=Number(Y.id)===Number(S)?" is-selected":"";O.push('<div class="bank-client-picker-row'+X+'" data-cid="'+z(Y.id)+'"><span class="bank-cp-dot" style="background:'+z(Y.color||"#111111")+'"></span><span>'+z(Y.short_name||Y.name||"#"+Y.id)+"</span></div>")}),u.innerHTML=O.join(""),u.querySelectorAll(".bank-client-picker-row").forEach(Y=>{Y.addEventListener("click",()=>{const X=Y.dataset.cid;S=X?Number(X):null,H()})})}async function D(){if(n)try{const u=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id)+"/client",{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({client_id:S})});if(!u.ok)throw new Error("client:"+u.status);n.client_id=S,re(),showToast(t("bank-client-changed"),"success"),m();try{await i()}catch{}}catch(u){console.warn("[bank-recon] save client failed",u),showToast(t("bank-client-change-failed"),"error")}}function J(){if(!n)return;const u=n;document.getElementById("bank-detail-title").textContent=(u.bank_code||"-")+(u.account_last4?" ···"+u.account_last4:"")+" · "+(u.source_filename||""),document.getElementById("bank-meta-period").textContent=U(u.period_start,u.period_end)||"-",document.getElementById("bank-meta-opening").textContent=C(u.opening_balance),document.getElementById("bank-meta-inflow").textContent="+"+C(u.total_inflow),document.getElementById("bank-meta-outflow").textContent="-"+C(u.total_outflow),document.getElementById("bank-meta-closing").textContent=C(u.closing_balance);const P=a||[],O=P.length;let Y=0,X=0,de=0;for(const se of P){const ce=se.match_status||"unmatched";ce==="matched"?Y++:ce==="suggested"?X++:de++}document.getElementById("bank-stat-total").textContent=O,document.getElementById("bank-stat-matched").textContent=Y,document.getElementById("bank-stat-suggested").textContent=X,document.getElementById("bank-stat-unmatched").textContent=de}function Z(){const u=document.getElementById("bank-tx-tbody");if(!u)return;let P=a||[];if(o!=="all"&&(P=P.filter(O=>o==="matched"?O.match_status==="matched":o==="suggested"?O.match_status==="suggested":o==="unmatched"?O.match_status==="unmatched"||O.match_status==="ignored":!0)),P.length===0){u.innerHTML=`<tr><td colspan="4" class="bank-empty">${t("bank-tx-empty")}</td></tr>`;return}if(u.innerHTML=P.map(O=>le(O)).join(""),u.querySelectorAll("tr[data-tx-id]").forEach(O=>{O.addEventListener("click",()=>{const Y=O.dataset.txId,X=a.find(de=>de.id===Y);X&&(u.querySelectorAll("tr.is-selected").forEach(de=>de.classList.remove("is-selected")),O.classList.add("is-selected"),ie(X))})}),s){const O=u.querySelector('tr[data-tx-id="'+s.id+'"]');O&&O.classList.add("is-selected")}}function le(u){const P=u.direction==="OUT",O=P?"-":"+",Y=P?"bank-out":"bank-in",X=u.match_status||"unmatched",de=t("bank-match-"+X)||X,se=T(u.tx_date),ce=u.channel?`<span class="bank-tx-channel">${z(u.channel)}</span>`:"";return`
            <tr data-tx-id="${z(u.id)}">
                <td class="bank-tx-date">${z(se)}</td>
                <td class="bank-tx-desc">${ce}${z(u.description||"-")}</td>
                <td class="bank-td-amount ${Y}">${O}${C(u.amount)}</td>
                <td><span class="bank-tx-match mt-${X}">${z(de)}</span></td>
            </tr>
        `}async function ie(u){s=u;const P=document.getElementById("bank-detail-body");P&&P.classList.add("has-pane");const O=document.getElementById("bank-cand-pane-title"),Y=document.getElementById("bank-cand-pane-sub"),X=document.getElementById("bank-cand-pane-foot");if(O&&(O.textContent=t("bank-cand-pane-current")),Y){const se=u.direction==="OUT"?"-":"+",ce=u.direction==="OUT"?"bank-out":"bank-in";Y.innerHTML=`${z(T(u.tx_date))}
                <span style="margin:0 6px;color:#D1D5DB">·</span>
                <span>${z(u.description||"-")}</span>
                <span style="margin:0 6px;color:#D1D5DB">·</span>
                <strong class="${ce}">${se}${C(u.amount)}</strong>`}X&&(X.style.display="");const de=document.getElementById("bank-cand-pane-body");if(de){de.innerHTML=`<div class="bank-empty">${t("bank-cand-loading")}</div>`;try{const se=await fetch("/api/bank-recon/tx/"+encodeURIComponent(u.id)+"/candidates",{headers:{Authorization:"Bearer "+token}});if(!se.ok)throw new Error("cands:"+se.status);const ce=await se.json();ee(u,ce.candidates||[])}catch{de.innerHTML=`<div class="bank-empty">${t("bank-cand-load-failed")}</div>`}}}function V(u){const P=Number(u||0);let O="score-low";return P>=85?O="score-high":P>=60&&(O="score-mid"),'<span class="bank-cand-score '+O+'">'+P.toFixed(0)+" "+t("bank-cand-score-unit")+"</span>"}function Q(u,P,O){const Y=P.history_id,X=P.invoice_no||"-",de=P.vendor||"-",se=P.amount_total!==null&&P.amount_total!==void 0?C(P.amount_total):"-",ce=P.invoice_date?T(P.invoice_date):"-",ae=P.filename||"",pe=!!O&&u.matched_history_id===Y,ve="bank-cand-card"+(P.is_auto_picked?" is-auto":"")+(pe?" is-picked":"");let fe="";return pe?fe='<button class="btn btn-ghost btn-small" data-act="unmatch"><span>'+t("bank-cand-unmatch")+"</span></button>":fe='<button class="btn btn-primary btn-small" data-act="pick" data-hid="'+z(Y)+'"><span>'+t(P.is_auto_picked?"bank-cand-confirm":"bank-cand-pick-this")+"</span></button>",'<div class="'+ve+'" data-hid="'+z(Y)+'"><div class="bank-cand-card-head"><div class="bank-cand-card-vendor">'+z(de)+"</div>"+V(P.score)+'</div><div class="bank-cand-card-fields"><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-invoice-no")+"</span> "+z(X)+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-amount")+"</span> "+se+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-date")+"</span> "+z(ce)+"</span></div>"+(ae?'<div class="bank-cand-card-file" title="'+z(ae)+'">'+z(ae)+"</div>":"")+(P.reason?'<div class="bank-cand-card-reason">'+z(P.reason)+"</div>":"")+'<div class="bank-cand-card-actions">'+fe+"</div></div>"}function ee(u,P){const O=document.getElementById("bank-cand-pane-body");if(!O)return;const Y=P||[];let X="";if(u.match_status==="matched")X='<div class="bank-cand-hint hint-matched">'+t("bank-cand-hint-matched").replace("{n}",Y.length)+"</div>";else if(u.match_status==="suggested")X='<div class="bank-cand-hint hint-suggested">'+t("bank-cand-hint-suggested").replace("{n}",Y.length)+"</div>";else if(Y.length>0)X='<div class="bank-cand-hint hint-low">'+t("bank-cand-hint-low").replace("{n}",Y.length)+"</div>";else{O.innerHTML='<div class="bank-empty">'+t("bank-cand-no-match-detail")+"</div>";return}const de=u.match_status==="matched",se=Y.map(ce=>Q(u,ce,de)).join("");O.innerHTML=X+'<div class="bank-cand-list">'+se+"</div>",O.querySelectorAll('[data-act="pick"]').forEach(ce=>{ce.addEventListener("click",()=>{I(ce.dataset.hid)})}),O.querySelectorAll('[data-act="unmatch"]').forEach(ce=>{ce.addEventListener("click",async()=>{try{await fetch("/api/bank-recon/tx/"+encodeURIComponent(u.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"unmatched"})}),ne(),await r(n.id)}catch{showToast(t("bank-action-failed"),"error")}})})}function ne(){const u=document.getElementById("bank-detail-body");u&&u.classList.remove("has-pane");const P=document.getElementById("bank-cand-pane-title"),O=document.getElementById("bank-cand-pane-sub"),Y=document.getElementById("bank-cand-pane-body"),X=document.getElementById("bank-cand-pane-foot");P&&(P.textContent=t("bank-cand-pane-empty-title")),O&&(O.textContent=t("bank-cand-pane-empty-sub")),X&&(X.style.display="none"),Y&&(Y.innerHTML='<div class="bank-cand-pane-empty"><svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="14" y="10" width="36" height="44" rx="3"/><path d="M22 22h20M22 30h20M22 38h12"/></svg><div>'+t("bank-cand-pane-empty-hint")+"</div></div>");const de=document.getElementById("bank-tx-tbody");de&&de.querySelectorAll("tr.is-selected").forEach(se=>se.classList.remove("is-selected")),s=null}function oe(u){const P=document.getElementById("bank-upload-progress");P&&(P.style.display="none")}function ue(){const u=document.getElementById("bank-upload-error");u&&(u.style.display="none")}function b(u){return{"bank_recon.only_pdf":t("bank-err-only-pdf"),"bank_recon.empty_file":t("bank-err-empty"),"bank_recon.file_too_large":t("bank-err-too-large"),"bank_recon.save_failed":t("bank-err-server"),"bank_recon.scanned":t("bank-err-scanned"),"bank_recon.no_tx":t("bank-err-no-tx"),network:t("bank-err-network")}[u]||t("bank-err-unknown")+" ("+u+")"}function C(u){if(u==null)return"-";const P=Number(u);return isNaN(P)?"-":P.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function T(u){if(!u)return"-";const P=String(u);return P.length>=10?P.slice(0,10):P}function U(u,P){return!u&&!P?"":(T(u)||"?")+" ~ "+(T(P)||"?")}function z(u){return u==null?"":String(u).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}window._loadBankReconPanel=l,window._rerenderBankRecon=function(){if(currentRoute==="automation"){if(E(),n&&(J(),Z(),re(),!s)){const u=document.getElementById("bank-cand-pane-title"),P=document.getElementById("bank-cand-pane-sub");u&&(u.textContent=t("bank-cand-pane-empty-title")),P&&(P.textContent=t("bank-cand-pane-empty-sub"))}j()}},typeof window.subscribeI18n=="function"&&window.subscribeI18n("bank-recon",window._rerenderBankRecon),window._openBankSession=async function(u){u&&(p||await l(),await r(u))}})();(function(){const e=document.getElementById("page-clients");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){let e=[],n=null,a="",o="seller";const s={page:0,pageSize:12,keyword:""},p=new Set;let l=[];const y={keyword:""};let i=null;function r(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}async function d(m,H={}){const D=await fetch(m,{...H,headers:{"Content-Type":"application/json",...r(),...H.headers||{}}});if(!D.ok){const J=await D.json().catch(()=>({}));throw new Error(J.detail||"HTTP "+D.status)}return D.json()}async function c(){try{e=(await d("/api/clients")).clients||[],window._clientsCache=e}catch(m){console.error("loadClientsCache fail",m),e=[]}try{typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter()}catch{}try{typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher()}catch{}return e}function v(m){o=m==="buyer"?"buyer":"seller",document.querySelectorAll("[data-cust-tab]").forEach(J=>J.classList.toggle("active",J.dataset.custTab===o));const H=document.getElementById("cust-pane-seller"),D=document.getElementById("cust-pane-buyer");H&&H.classList.toggle("active",o==="seller"),D&&D.classList.toggle("active",o==="buyer")}function x(){const m=window._userInfo||{},H=String(m.role||"").toLowerCase(),D=String(m.tenant_role||"").toLowerCase();return m.is_super_admin===!0||m.is_owner===!0||H==="owner"||H==="admin"||D==="owner"||D==="admin"}function _(){window._workspaceClientsCache=l,typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl()}async function q(){try{const m=await d("/api/workspace/clients");l=m&&(m.clients||m.items)||[],window._workspaceClientsCache=l}catch(m){console.error("loadSellerCache fail",m),l=[]}return l}function j(){const m=y.keyword.trim().toLowerCase();return m?l.filter(H=>(H.name||"").toLowerCase().includes(m)||(H.tax_id||"").toLowerCase().includes(m)):l}function k(){const m=document.getElementById("seller-tbody");if(!m)return;const H=x(),D=document.getElementById("btn-seller-new");D&&(D.style.display=H?"":"none");const J=j(),Z=typeof window.getActiveWorkspaceClientId=="function"?window.getActiveWorkspaceClientId():null;if(!J.length){m.innerHTML=`<div class="cust-empty">${escapeHtml(t(y.keyword?"cust-no-match":"seller-empty"))}</div>`;return}m.innerHTML=J.map(le=>{const V=Z!=null&&Number(Z)===Number(le.id)?`<span class="cust-badge-current"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7.5l3.2 3.2L12 4"/></svg>${escapeHtml(t("seller-current"))}</span>`:`<button class="cust-row-btn primary" data-saction="activate" data-wid="${le.id}">${escapeHtml(t("seller-set-current"))}</button>`,Q=H?`
                <button class="cust-row-btn" data-saction="edit" data-wid="${le.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
                <button class="cust-row-btn danger" data-saction="archive" data-wid="${le.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h10M4 4v7a1 1 0 001 1h4a1 1 0 001-1V4M5.5 4V2.8a1 1 0 011-1h1a1 1 0 011 1V4"/></svg><span>${escapeHtml(t("wsclient-archive"))}</span></button>`:"";return`<div class="cust-row seller-grid" data-wid="${le.id}">
                <div class="cust-cell-name"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" style="flex-shrink:0;opacity:.55"><rect x="2" y="5" width="12" height="9" rx="1"/><path d="M10 14V4a1 1 0 00-1-1H7a1 1 0 00-1 1v10"/></svg><span class="cust-name-text">${escapeHtml(le.name||"#"+le.id)}</span></div>
                <div class="cust-cell-tax">${escapeHtml(le.tax_id||"—")}</div>
                <div class="align-right">${le.invoice_count||0}</div>
                <div class="cust-row-actions">${V}${Q}</div>
            </div>`}).join("")}function B(m){i=m?m.id:null,document.getElementById("wsclient-modal-title").textContent=t(m?"wsclient-modal-edit":"wsclient-modal-new"),document.getElementById("wsclient-input-name").value=m&&m.name||"",document.getElementById("wsclient-input-tax").value=m&&m.tax_id||"",document.getElementById("wsclient-modal-archive").style.display=m?"":"none",document.getElementById("wsclient-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("wsclient-input-name").focus(),50)}function N(){document.getElementById("wsclient-modal-mask").style.display="none",i=null}async function R(){const m=document.getElementById("wsclient-input-name").value.trim(),H=document.getElementById("wsclient-input-tax").value.trim();if(!m){showToast(t("client-msg-name-required"),"fail");return}try{i?(await d("/api/workspace/clients/"+i,{method:"PATCH",body:JSON.stringify({name:m,tax_id:H})}),showToast(t("client-msg-updated"),"success")):(await d("/api/workspace/clients",{method:"POST",body:JSON.stringify({name:m,tax_id:H||null})}),showToast(t("client-msg-created"),"success")),N(),await q(),k(),_()}catch(D){const J=D&&D.message?D.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+J,"fail")}}async function F(){if(!i)return;const m=l.find(D=>Number(D.id)===Number(i));if(await showConfirm(t("wsclient-archive-confirm").replace("{name}",m?m.name:""),{danger:!0}))try{const D=i;await d("/api/workspace/clients/"+D,{method:"DELETE"}),showToast(t("wsclient-archived"),"success"),typeof window.getActiveWorkspaceClientId=="function"&&Number(window.getActiveWorkspaceClientId())===Number(D)&&typeof window.enterPersonalMode=="function"&&window.enterPersonalMode(),N(),await q(),k(),_()}catch{showToast(t("client-msg-save-fail"),"fail")}}function A(){const m=s.keyword.trim().toLowerCase();return m?e.filter(H=>(H.name||"").toLowerCase().includes(m)||(H.short_name||"").toLowerCase().includes(m)||(H.tax_id||"").toLowerCase().includes(m)):e}function g(){const m=A(),H=s.pageSize,D=Math.max(0,Math.ceil(m.length/H)-1);s.page>D&&(s.page=D);const J=s.page*H;return{all:m,items:m.slice(J,J+H),start:J,ps:H,total:m.length,maxPage:D}}function f(){const m=document.getElementById("buyer-tbody");if(!m)return;const{items:H,start:D,ps:J,total:Z,maxPage:le}=g();Z?m.innerHTML=H.map(ee=>{const ne=p.has(ee.id);return`<div class="cust-row buyer-grid${ne?" selected":""}" data-cid="${ee.id}">
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
                </div>`}).join(""):m.innerHTML=`<div class="cust-empty">${escapeHtml(t(s.keyword?"cust-no-match":"clients-empty"))}</div>`;const ie=document.getElementById("buyer-pager-info");ie&&(ie.textContent=Z?`${D+1}–${Math.min(D+J,Z)} / ${Z}`:"0");const V=document.getElementById("buyer-prev");V&&(V.disabled=s.page<=0);const Q=document.getElementById("buyer-next");Q&&(Q.disabled=s.page>=le),h()}function h(){const m=p.size,H=document.getElementById("buyer-batch-bar");H&&(H.style.display=m?"flex":"none");const D=document.getElementById("buyer-batch-count");D&&(D.textContent=t("cust-selected-n").replace("{n}",m));const J=document.getElementById("buyer-check-all");if(J){const{items:Z}=g(),le=Z.map(V=>V.id),ie=le.filter(V=>p.has(V)).length;J.checked=le.length>0&&ie===le.length,J.indeterminate=ie>0&&ie<le.length}}function I(){p.clear(),f()}async function L(){const m=Array.from(p);if(!(!m.length||!await showConfirm(t("cust-batch-del-confirm").replace("{n}",m.length),{danger:!0})))try{await d("/api/clients/batch-delete",{method:"POST",body:JSON.stringify({ids:m})}),showToast(t("client-msg-deleted"),"success"),p.clear(),await c(),f(),te(),w()}catch{showToast(t("client-msg-save-fail"),"fail")}}window.loadClientsPage=async function(){const m=document.getElementById("seller-tbody");m&&(m.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`);const H=document.getElementById("buyer-tbody");H&&(H.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`),await Promise.all([q(),c()]),k(),f()},window.addEventListener("pearnly:workspace-changed",function(){typeof currentRoute<"u"&&currentRoute==="clients"&&k()});function $(m){n=m?m.id:null;const H=!!m;document.getElementById("client-modal-title").textContent=t(H?"client-modal-edit":"client-modal-new"),document.getElementById("client-input-name").value=m&&m.name||"",document.getElementById("client-input-short").value=m&&m.short_name||"",document.getElementById("client-input-tax").value=m&&m.tax_id||"",document.getElementById("client-input-address").value=m&&m.address||"",document.getElementById("client-input-contact").value=m&&m.contact_person||"",document.getElementById("client-input-phone").value=m&&m.contact_phone||"",document.getElementById("client-input-email").value=m&&m.contact_email||"",document.getElementById("client-input-notes").value=m&&m.notes||"";const D=m&&m.color||"#111111";document.querySelectorAll("#client-color-picker .color-swatch").forEach(J=>{J.classList.toggle("active",J.dataset.color===D)}),document.getElementById("client-modal-delete").style.display=H?"":"none",document.getElementById("client-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("client-input-name").focus(),50)}function E(){document.getElementById("client-modal-mask").style.display="none",n=null}function M(){const m=document.querySelector("#client-color-picker .color-swatch.active");return m?m.dataset.color:"#111111"}async function K(){const m=document.getElementById("client-input-name").value.trim();if(!m){showToast(t("client-msg-name-required"),"fail");return}const H={name:m,short_name:document.getElementById("client-input-short").value.trim()||null,tax_id:document.getElementById("client-input-tax").value.trim()||null,address:document.getElementById("client-input-address").value.trim()||null,contact_person:document.getElementById("client-input-contact").value.trim()||null,contact_phone:document.getElementById("client-input-phone").value.trim()||null,contact_email:document.getElementById("client-input-email").value.trim()||null,notes:document.getElementById("client-input-notes").value.trim()||null,color:M()};try{n?(await d(`/api/clients/${n}`,{method:"PATCH",body:JSON.stringify(H)}),showToast(t("client-msg-updated"),"success")):(await d("/api/clients",{method:"POST",body:JSON.stringify(H)}),showToast(t("client-msg-created"),"success")),E(),await c(),currentRoute==="clients"&&f(),te(),w()}catch(D){console.error("saveClient fail",D);const J=D&&D.message?D.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+J,"fail")}}async function G(){if(!n)return;const m=e.find(J=>J.id===n);if(!m)return;const H=t("client-delete-confirm").replace("{name}",m.name);if(await showConfirm(H,{danger:!0}))try{await d(`/api/clients/${n}`,{method:"DELETE"}),showToast(t("client-msg-deleted"),"success"),E(),await c(),currentRoute==="clients"&&f(),te(),w()}catch(J){console.error(J),showToast(t("client-msg-save-fail"),"fail")}}async function W(m){const H=e.find(D=>D.id===m);if(typeof window.openClientExportModal=="function"){window.openClientExportModal(m,H?H.name:"");return}try{const D=localStorage.getItem("mrpilot_token"),J=await fetch(`/api/clients/${m}/export?month=all`,{headers:{Authorization:"Bearer "+D}});if(!J.ok){let Q="HTTP "+J.status;try{const ee=await J.json();ee&&ee.detail&&(Q=ee.detail)}catch{}throw new Error(Q)}const Z=await J.blob();if(Z.size<200){showToast(t("client-export-month-empty"),"info");return}const le=H&&H.name?H.name.replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40):"client",ie=URL.createObjectURL(Z),V=document.createElement("a");V.href=ie,V.download=`${le}_export.csv`,V.click(),URL.revokeObjectURL(ie)}catch(D){console.error("exportClient fail",D),showToast(t("client-msg-save-fail")+" · "+(D.message||""),"fail")}}function te(){const m=document.getElementById("drawer-client-select");if(!m)return;const H=m.value;m.innerHTML=`<option value="">${escapeHtml(t("drawer-client-none"))}</option>`+e.map(D=>`<option value="${D.id}">${escapeHtml(D.name)}</option>`).join(""),m.value=H||""}window.bindDrawerClient=function(m,H){const D=document.getElementById("drawer-client-select");if(!D)return;if(te(),D.value=H?String(H):"",!m){D.onchange=null;const Z=document.getElementById("drawer-client-add");Z&&(Z.onclick=()=>$(null));return}D.onchange=async()=>{const Z=D.value?parseInt(D.value,10):null;try{await d(`/api/history/${m}/assign_client`,{method:"POST",body:JSON.stringify({client_id:Z})}),showToast(t("client-msg-updated"),"success");const le=_results[_drawerIdx];le&&(le.client_id=Z),await c()}catch(le){console.error(le),showToast(t("client-msg-save-fail"),"fail"),D.value=H?String(H):""}};const J=document.getElementById("drawer-client-add");J&&(J.onclick=()=>$(null))};let re={fetched:0,items:[],supplier_count:0};window.fillCategoryDatalist=async function(){try{const m=document.getElementById("drawer-cat-datalist"),H=Date.now();if(H-re.fetched<300*1e3){m&&(m.innerHTML=re.items.map(J=>`<option value="${escapeHtml(J)}">`).join("")),S(re.supplier_count);return}const D=await d("/api/categories",{method:"GET"});re.fetched=H,re.items=D&&D.categories||[],re.supplier_count=D&&D.supplier_count||0,m&&(m.innerHTML=re.items.map(J=>`<option value="${escapeHtml(J)}">`).join("")),S(re.supplier_count)}catch(m){console.warn("fillCategoryDatalist failed",m)}};function S(m){const H=document.getElementById("drawer-cat-learned-tag");H&&m>0&&(H.textContent=(t("drawer-suggest-learned-with-count")||"已学 {n}").replace("{n}",m))}function w(){const m=document.getElementById("history-client-filter");if(!m)return;const H=m.value;m.innerHTML=`<option value="">${escapeHtml(t("history-client-all"))}</option>`+e.map(D=>`<option value="${D.id}">${escapeHtml(D.name)}</option>`).join(""),m.value=H||""}window.getHistoryClientFilter=function(){return a},document.addEventListener("DOMContentLoaded",()=>{const m=document.querySelector(".cust-tab-bar");m&&m.addEventListener("click",ae=>{const pe=ae.target.closest("[data-cust-tab]");pe&&v(pe.dataset.custTab)});const H=document.getElementById("btn-buyer-new");H&&H.addEventListener("click",()=>$(null));const D=document.getElementById("buyer-tbody");D&&D.addEventListener("click",ae=>{const pe=ae.target.closest(".buyer-row-check");if(pe){const ge=parseInt(pe.dataset.cid,10);pe.checked?p.add(ge):p.delete(ge);const be=pe.closest(".cust-row");be&&be.classList.toggle("selected",pe.checked),h();return}const ve=ae.target.closest(".cust-row-btn");if(ve){ae.stopPropagation();const ge=parseInt(ve.dataset.cid,10);if(ve.dataset.action==="edit"){const be=e.find(xe=>xe.id===ge);be&&$(be)}else ve.dataset.action==="export"&&W(ge);return}const fe=ae.target.closest(".cust-row");if(fe&&!ae.target.closest(".cust-cell-check")){const ge=e.find(be=>be.id===parseInt(fe.dataset.cid,10));ge&&$(ge)}});const J=document.getElementById("buyer-check-all");J&&J.addEventListener("change",()=>{const{items:ae}=g();ae.forEach(pe=>{J.checked?p.add(pe.id):p.delete(pe.id)}),f()});const Z=document.getElementById("buyer-batch-cancel");Z&&Z.addEventListener("click",I);const le=document.getElementById("buyer-batch-delete");le&&le.addEventListener("click",L);const ie=document.getElementById("buyer-prev");ie&&ie.addEventListener("click",()=>{s.page>0&&(s.page--,f())});const V=document.getElementById("buyer-next");V&&V.addEventListener("click",()=>{s.page++,f()});const Q=document.getElementById("buyer-search");if(Q){let ae;Q.addEventListener("input",()=>{clearTimeout(ae),ae=setTimeout(()=>{s.keyword=Q.value,s.page=0;const pe=document.getElementById("buyer-search-clear");pe&&(pe.style.display=Q.value?"":"none"),f()},200)})}const ee=document.getElementById("buyer-search-clear");ee&&ee.addEventListener("click",()=>{const ae=document.getElementById("buyer-search");ae&&(ae.value=""),s.keyword="",s.page=0,ee.style.display="none",f()});const ne=document.getElementById("btn-seller-new");ne&&ne.addEventListener("click",()=>B(null));const oe=document.getElementById("seller-tbody");oe&&oe.addEventListener("click",ae=>{const pe=ae.target.closest("[data-saction]");if(!pe)return;ae.stopPropagation();const ve=parseInt(pe.dataset.wid,10),fe=pe.dataset.saction,ge=l.find(be=>Number(be.id)===ve);fe==="activate"?(typeof window.setActiveWorkspaceClientId=="function"&&window.setActiveWorkspaceClientId(ve),k(),typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl(),showToast(t("seller-activated").replace("{name}",ge?ge.name:""),"success")):fe==="edit"?ge&&B(ge):fe==="archive"&&(i=ve,F())});const ue=document.getElementById("seller-search");if(ue){let ae;ue.addEventListener("input",()=>{clearTimeout(ae),ae=setTimeout(()=>{y.keyword=ue.value;const pe=document.getElementById("seller-search-clear");pe&&(pe.style.display=ue.value?"":"none"),k()},200)})}const b=document.getElementById("seller-search-clear");b&&b.addEventListener("click",()=>{const ae=document.getElementById("seller-search");ae&&(ae.value=""),y.keyword="",b.style.display="none",k()});const C=document.getElementById("wsclient-modal-close");C&&C.addEventListener("click",N);const T=document.getElementById("wsclient-modal-cancel");T&&T.addEventListener("click",N);const U=document.getElementById("wsclient-modal-save");U&&U.addEventListener("click",R);const z=document.getElementById("wsclient-modal-archive");z&&z.addEventListener("click",F);const u=document.getElementById("wsclient-modal-mask");u&&u.addEventListener("click",ae=>{ae.target===u&&N()});const P=document.getElementById("client-modal-close");P&&P.addEventListener("click",E);const O=document.getElementById("client-modal-cancel");O&&O.addEventListener("click",E);const Y=document.getElementById("client-modal-save");Y&&Y.addEventListener("click",K);const X=document.getElementById("client-modal-delete");X&&X.addEventListener("click",G);const de=document.getElementById("client-modal-mask");de&&de.addEventListener("click",ae=>{ae.target===de&&E()});const se=document.getElementById("client-color-picker");se&&se.addEventListener("click",ae=>{const pe=ae.target.closest(".color-swatch");pe&&(se.querySelectorAll(".color-swatch").forEach(ve=>ve.classList.remove("active")),pe.classList.add("active"))});const ce=document.getElementById("history-client-filter");ce&&ce.addEventListener("change",()=>{a=ce.value,typeof renderHistoryList=="function"&&renderHistoryList()})}),setTimeout(()=>c(),1e3)})();(function(){const e=document.getElementById("page-exceptions");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){let e={statsCache:null,listCache:[],currentRule:null,currentClient:"",currentStatus:"pending",loading:!1,selectedIds:new Set,offset:0,pageSize:50,total:0,loadFailed:!1,listScrollY:0};function n(S,w){let m=t(S)||S;if(w)for(const H in w)m=m.replace(new RegExp("\\{"+H+"\\}","g"),String(w[H]));return m}async function a(){try{const S=e.currentClient||"",w="/api/exceptions/stats?status=pending"+(S?"&client_id="+encodeURIComponent(S):""),m=await fetch(w,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!m.ok)return;const H=await m.json(),D=document.getElementById("nav-exc-badge");if(!D)return;const J=parseInt(H.pending||0,10);J>0?(D.textContent=J>99?"99+":String(J),D.style.display=""):D.style.display="none"}catch{}}function o(S){return S==="high"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
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
        </svg>`}function s(){return`<svg class="exc-empty-icon" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 19l5 5 13-13"/>
            <circle cx="20" cy="20" r="17"/>
        </svg>`}function p(S){if(S==null)return"—";const w=parseFloat(S);return isNaN(w)?"—":"฿ "+w.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function l(S){return S?S.slice(0,10):"—"}function y(S){document.getElementById("exc-kpi-pending").textContent=S.pending||0,document.getElementById("exc-kpi-high").textContent=S.high_severity||0,document.getElementById("exc-kpi-resolved").textContent=S.resolved||0,document.getElementById("exc-kpi-learned").textContent=S.learned_rules||0;const w=document.getElementById("exc-status-tab-count-pending"),m=document.getElementById("exc-status-tab-count-resolved"),H=document.getElementById("exc-status-tab-count-ignored");w&&(w.textContent=S.pending||0),m&&(m.textContent=S.resolved||0),H&&(H.textContent=S.ignored||0),document.querySelectorAll("#exc-status-tabs .exc-status-tab").forEach(J=>{J.classList.toggle("active",J.dataset.status===(e.currentStatus||"pending"))})}function i(S){const w=document.getElementById("exc-chips");if(!w)return;const m=S.by_rule||{},H=["confidence_low","duplicate","amount_missing","math_mismatch","tax_id_format_invalid"];let J=`<button class="exc-chip ${!e.currentRule?"active":""}" data-rule="">
            <span>${escapeHtml(t("exc-chip-all"))}</span>
            <span class="exc-chip-count">${S.pending||0}</span>
        </button>`;for(const Z of H){const le=m[Z]||0;if(le===0&&e.currentRule!==Z)continue;const ie=e.currentRule===Z;J+=`<button class="exc-chip ${ie?"active":""}" data-rule="${escapeHtml(Z)}">
                <span>${escapeHtml(t("exc-chip-"+Z))}</span>
                <span class="exc-chip-count">${le}</span>
            </button>`}w.innerHTML=J,w.querySelectorAll(".exc-chip").forEach(Z=>{Z.addEventListener("click",()=>{const le=Z.dataset.rule||null;e.currentRule=le,_()})})}function r(S){const w=document.getElementById("exc-list");if(!w)return;if(!S||S.length===0){w.innerHTML=`<div class="exc-empty">
                ${s()}
                <div class="exc-empty-title">${escapeHtml(t("exc-empty-title"))}</div>
                <div>${escapeHtml(t("exc-empty-desc"))}</div>
            </div>`,c();return}const m='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7l3 3 5-5"/></svg>',H=(e.currentStatus||"pending")==="pending";w.innerHTML=S.map(D=>{const J=D.severity||"medium",Z=t("exc-rule-"+D.rule_code)||D.rule_code,le=D.seller_name&&D.seller_name.trim()?D.seller_name:t("exc-no-seller"),ie=D.filename||"—",V=l(D.invoice_date||D.created_at),Q=D.status==="pending",ee=e.selectedIds.has(D.id),ne=H&&Q;return`
                <div class="exc-row sev-${escapeHtml(J)} ${ee?"selected":""}" data-exc-id="${escapeHtml(String(D.id))}">
                    <div class="exc-row-check ${ee?"checked":""}" data-check-id="${escapeHtml(String(D.id))}" ${ne?"":'style="visibility:hidden;"'}>${m}</div>
                    <div class="exc-row-sev">${o(J)}</div>
                    <div class="exc-row-main">
                        <div class="exc-row-title">${escapeHtml(le)} · ${escapeHtml(ie)}</div>
                        <div class="exc-row-meta">
                            ${D.invoice_no?`<span><b>${escapeHtml(D.invoice_no)}</b></span>`:""}
                            <span>${escapeHtml(V)}</span>
                        </div>
                    </div>
                    <div class="exc-row-rule r-${escapeHtml(J)}">${escapeHtml(Z)}</div>
                    <div class="exc-row-amount">${escapeHtml(p(D.total_amount))}</div>
                </div>
            `}).join(""),w.querySelectorAll(".exc-row").forEach(D=>{D.addEventListener("click",J=>{if(J.target.closest(".exc-row-check"))return;const Z=D.dataset.excId;Z&&R(parseInt(Z,10))})}),w.querySelectorAll(".exc-row-check").forEach(D=>{D.addEventListener("click",J=>{J.stopPropagation();const Z=parseInt(D.dataset.checkId,10);Z&&(e.selectedIds.has(Z)?(e.selectedIds.delete(Z),D.classList.remove("checked"),D.closest(".exc-row").classList.remove("selected")):(e.selectedIds.add(Z),D.classList.add("checked"),D.closest(".exc-row").classList.add("selected")),d())})}),d(),c()}function d(){const S=document.getElementById("exc-batch-bar"),w=document.getElementById("exc-batch-count");if(!S||!w)return;const m=e.selectedIds.size;m===0?S.style.display="none":(S.style.display="",w.textContent=n("exc-batch-count",{n:m}))}function c(){const S=document.getElementById("exc-list-foot"),w=document.getElementById("exc-list-count"),m=document.getElementById("exc-loadmore");if(!S||!w||!m)return;const H=e.listCache.length;if(H===0){S.style.display="none";return}S.style.display="";let D=H;const J=e.statsCache;J&&(e.currentRule?D=(J.by_rule||{})[e.currentRule]||H:D=J.pending||H),e.total=D,w.textContent=n("exc-list-count",{shown:H,total:D});const Z=H<D&&H<500;m.style.display=Z?"":"none"}async function v(){try{if(navigator.onLine===!1)throw new Error("offline");const S=e.currentClient||"",w=e.currentStatus||"pending",m=new URLSearchParams;m.set("status",w),S&&m.set("client_id",S);const H="/api/exceptions/stats?"+m.toString(),D=await fetch(H,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!D.ok)throw new Error("http "+D.status);const J=await D.json();return e.statsCache=J,y(J),i(J),J}catch(S){return console.warn("loadExceptionsStats fail",S),null}}function x(S){const w=document.getElementById("exc-list");if(!w)return;const m=`<svg class="exc-error-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="18" cy="18" r="14"/>
            <line x1="18" y1="11" x2="18" y2="19"/>
            <circle cx="18" cy="23" r="0.8" fill="currentColor"/>
        </svg>`,H=S?t("exc-offline"):t("exc-error-retry-title"),D=S?"":t("exc-error-retry-desc");w.innerHTML=`
            <div class="exc-error">
                ${m}
                <div class="exc-error-msg">${escapeHtml(H)}${D?" · "+escapeHtml(D):""}</div>
                <button class="btn btn-sm btn-secondary" id="exc-retry-btn" type="button">${escapeHtml(t("exc-retry-btn"))}</button>
            </div>`;const J=document.getElementById("exc-retry-btn");J&&J.addEventListener("click",()=>window.loadExceptionsPage&&window.loadExceptionsPage())}async function _(S){S=S||{};const w=!!S.append,m=document.getElementById("exc-list");!w&&m&&e.listCache.length===0&&(m.innerHTML=`<div class="exc-loading">${escapeHtml(t("exc-loading"))}</div>`);const H=new URLSearchParams;H.set("status",e.currentStatus||"pending"),e.currentRule&&H.set("rule_code",e.currentRule),e.currentClient&&H.set("client_id",e.currentClient);const D=w?e.listCache.length:0;H.set("limit",String(e.pageSize)),H.set("offset",String(D));try{if(navigator.onLine===!1)throw new Error("offline");const J=await fetch("/api/exceptions/list?"+H.toString(),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!J.ok)throw new Error("http "+J.status);const le=(await J.json()).items||[];w?e.listCache=e.listCache.concat(le):(e.listCache=le,e.selectedIds.clear()),e.loadFailed=!1,r(e.listCache),e.statsCache&&i(e.statsCache)}catch(J){console.warn("loadExceptionsList fail",J),e.loadFailed=!0;const Z=navigator.onLine===!1||String(J.message||"").includes("offline");w?showToast(t("exc-toast-load-fail"),"error"):(x(Z),showToast(Z?t("exc-offline"):t("exc-toast-load-fail"),"error"))}}async function q(){if(!e.loading&&!(e.listCache.length>=500)){e.loading=!0;try{await _({append:!0})}finally{e.loading=!1}}}function j(){const S=document.getElementById("exc-client-filter");if(!S)return;const w=window._clientsCache||[],m=e.currentClient||"",H=typeof t=="function"?t("history-client-all"):"全部客户";S.innerHTML=`<option value="">${escapeHtml(H)}</option>`+w.map(D=>`<option value="${D.id}">${escapeHtml(D.name)}</option>`).join(""),S.value=m}window.loadExceptionsPage=async function(){if(!e.loading){e.loading=!0;try{j(),typeof window.loadErpExceptions=="function"&&window.loadErpExceptions(),await v(),await _()}finally{e.loading=!1}}},window.refreshExcBadge=a,window._refreshExcClientFilter=j,window._excState=e,window._rerenderExceptions=function(){try{j()}catch{}e.statsCache&&(y(e.statsCache),i(e.statsCache)),e.listCache&&e.listCache.length&&r(e.listCache);try{window._erpExcState&&window._erpExcState.items&&window._erpExcState.items.length&&typeof window._rerenderErpExceptions=="function"&&window._rerenderErpExceptions()}catch{}k.openExcId&&I()};let k={openExcId:null,excRow:null,history:null,loading:!1,pdfUrl:null,pdfStatus:"idle",editing:!1,editFields:null};function B(){if(k.pdfUrl){try{URL.revokeObjectURL(k.pdfUrl)}catch{}k.pdfUrl=null}k.pdfStatus="idle"}async function N(S,w){k.pdfStatus="loading",I();try{const m=await fetch("/api/history/"+encodeURIComponent(S)+"/pdf",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(k.openExcId!==w)return;if(m.status===404){k.pdfStatus="empty",I();return}if(!m.ok)throw new Error("http "+m.status);const H=await m.blob();if(k.openExcId!==w)return;B(),k.pdfUrl=URL.createObjectURL(H),k.pdfStatus="ready",I()}catch(m){if(k.openExcId!==w)return;console.warn("loadDrawerPdf fail",m),k.pdfStatus="error",I()}}function R(S){const w=(e.listCache||[]).find(m=>m.id===S);if(!w){showToast(t("exc-drawer-error"),"error");return}e.listScrollY=window.scrollY||document.documentElement.scrollTop||0,B(),k.editing=!1,k.editFields=null,k.openExcId=S,k.excRow=w,k.history=null,document.getElementById("exc-drawer-mask").classList.add("show"),document.getElementById("exc-drawer").classList.add("show"),I(),A(w.history_id),N(w.history_id,S)}function F(){B(),k.editing=!1,k.editFields=null,k.openExcId=null,k.excRow=null,k.history=null,document.getElementById("exc-drawer-mask").classList.remove("show"),document.getElementById("exc-drawer").classList.remove("show");const S=e.listScrollY||0;S>0&&requestAnimationFrame(()=>window.scrollTo(0,S))}async function A(S){try{const w=await fetch("/api/history/"+encodeURIComponent(S),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!w.ok)throw new Error("http "+w.status);k.history=await w.json()}catch(w){console.warn("loadHistoryDetail fail",w),k.history={_err:!0}}k.excRow&&I()}function g(S){if(!S||!S.pages)return{};const w=S.pages,m=w.find(H=>!H.is_duplicate&&!H.is_copy)||w[0];return m&&m.fields||{}}function f(S){if(S==null)return"—";const w=typeof S=="number"?S:parseFloat(String(S).replace(/,/g,""));return isNaN(w)?escapeHtml(String(S)):"฿ "+w.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function h(S,w){if(w=w||{},S==="math_mismatch")return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-subtotal"))}</b><span>${escapeHtml(f(w.subtotal))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-vat"))}</b><span>${escapeHtml(f(w.vat))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(f(w.total_expected))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-actual"))}</b><span class="v-bad">${escapeHtml(f(w.total_actual))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-diff"))}</b><span class="v-bad">${escapeHtml(f(w.diff))}</span></div>
            `;if(S==="tax_id_format_invalid")return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-seller-tax"))}</b><span class="v-bad">${escapeHtml(w.tax_id_normalized||w.tax_id_raw||"—")}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-tax-len"))}</b><span class="v-bad">${escapeHtml(String(w.actual_length||"?"))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(t("exc-detail-tax-expected"))}</span></div>
            `;if(S==="duplicate"){const m=w.level==="exact"?t("exc-detail-dup-level-exact"):t("exc-detail-dup-level-likely");return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-dup-match"))}</b><span>${escapeHtml(w.match_filename||"—")}</span></div>
                ${w.match_invoice_no?`<div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-invoice-no"))}</b><span>${escapeHtml(w.match_invoice_no)}</span></div>`:""}
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span>${escapeHtml(m)}</span></div>
            `}return S==="confidence_low"?`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-conf-label"))}</b><span class="v-bad">${escapeHtml(w.confidence||"—")}</span></div>
            `:S==="amount_missing"?`<div class="exc-why-detail-row" style="justify-content:center;color:var(--danger);"><span>${escapeHtml(t("exc-detail-missing"))}</span></div>`:`<div class="exc-why-detail-row"><span style="font-size:11px;">${escapeHtml(JSON.stringify(w))}</span></div>`}function I(){const S=k.excRow;if(!S)return;const w=S.seller_name&&S.seller_name.trim()?S.seller_name:t("exc-no-seller"),m=S.filename||"—";document.getElementById("exc-drawer-title").textContent=m;const H="exc-status-"+(S.status||"pending"),D=t(H)||S.status,J="s-"+(S.status||"pending"),Z=(S.invoice_date||S.created_at||"").slice(0,10);document.getElementById("exc-drawer-sub").innerHTML=`
            <span>${escapeHtml(w)}</span>
            ${S.invoice_no?`<span>· ${escapeHtml(S.invoice_no)}</span>`:""}
            ${Z?`<span>· ${escapeHtml(Z)}</span>`:""}
            <span class="exc-status-chip ${J}">${escapeHtml(D)}</span>
        `;const le=S.severity||"medium",ie=t("exc-rule-"+S.rule_code)||S.rule_code,V=h(S.rule_code,S.detail||{}),Q=g(k.history),ee=k.history===null,ne=k.history&&k.history._err,oe=new Set;S.rule_code==="math_mismatch"?(oe.add("subtotal"),oe.add("vat"),oe.add("total_amount")):S.rule_code==="tax_id_format_invalid"?oe.add("seller_tax"):S.rule_code==="amount_missing"&&(oe.add("total_amount"),oe.add("invoice_number"));const ue=!!k.editing,b=k.editFields||{},C=(ae,pe,ve)=>{if(ee)return`<div class="exc-field-row"><label>${escapeHtml(t(pe))}</label><span class="val empty">…</span></div>`;const fe=ue?b[ae]!==void 0?b[ae]:Q[ae]!==void 0&&Q[ae]!==null?Q[ae]:"":Q[ae],ge=oe.has(ae)?"flagged":"";if(ue){const De=ve?"number":"text",Le=ve?' step="0.01" inputmode="decimal"':"",Ce=fe==null?"":String(fe).replace(/"/g,"&quot;");return`<div class="exc-field-row ${ge} editing">
                    <label>${escapeHtml(t(pe))}</label>
                    <input class="exc-field-input" type="${De}"${Le} data-edit-key="${escapeHtml(ae)}" value="${Ce}">
                </div>`}const be=ve?f(fe):fe||"",xe=fe==null||fe===""?`<span class="val empty">${escapeHtml(t("exc-empty-val"))}</span>`:`<span class="val">${escapeHtml(be)}</span>`;return`<div class="exc-field-row ${ge}"><label>${escapeHtml(t(pe))}</label>${xe}</div>`};let T="";ne?T=`<div class="exc-drawer-error">${escapeHtml(t("exc-drawer-error"))}</div>`:T=`
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
            `;const U=(()=>{if(k.pdfStatus==="loading"||k.pdfStatus==="idle")return`
                    <div class="exc-pdf-toolbar">
                        <span class="exc-pdf-toolbar-title">${escapeHtml(t("exc-pdf-loading"))}</span>
                    </div>
                    <div class="exc-pdf-empty">
                        <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M18 4v8a14 14 0 1014 14"/>
                        </svg>
                        <div class="exc-pdf-empty-msg">${escapeHtml(t("exc-pdf-loading"))}</div>
                    </div>
                `;if(k.pdfStatus==="empty")return`
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
                `;if(k.pdfStatus==="error")return`
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
                `;const ae=k.pdfUrl;return`
                <div class="exc-pdf-toolbar">
                    <span class="exc-pdf-toolbar-title">${escapeHtml(m)}</span>
                    <div class="exc-pdf-toolbar-actions">
                        <a class="exc-pdf-icon-btn" id="exc-pdf-open-tab" href="${ae}" target="_blank" rel="noopener" title="${escapeHtml(t("exc-pdf-open-tab"))}">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M8 2h4v4M12 2L7 7"/>
                                <path d="M11 8v3a1 1 0 01-1 1H3a1 1 0 01-1-1V4a1 1 0 011-1h3"/>
                            </svg>
                        </a>
                        <a class="exc-pdf-icon-btn" id="exc-pdf-download" href="${ae}" download="${escapeHtml(m)}" title="${escapeHtml(t("exc-pdf-download"))}">
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
        `;const z=document.getElementById("exc-fld-edit");z&&z.addEventListener("click",()=>{k.editing=!0,k.editFields={...g(k.history)},I()});const u=document.getElementById("exc-fld-cancel");u&&u.addEventListener("click",()=>{k.editing=!1,k.editFields=null,I()});const P=document.getElementById("exc-fld-save");P&&P.addEventListener("click",()=>L()),document.querySelectorAll(".exc-field-input").forEach(ae=>{ae.addEventListener("input",()=>{k.editFields||(k.editFields={}),k.editFields[ae.dataset.editKey]=ae.value})});const Y=document.getElementById("exc-pdf-retry");Y&&k.openExcId&&Y.addEventListener("click",()=>{k.excRow&&N(k.excRow.history_id,k.openExcId)});const X=S.status==="pending",de=!!(S.seller_name&&S.seller_name.trim()),se=document.getElementById("exc-btn-resolve"),ce=document.getElementById("exc-btn-ignore");se.disabled=!X,ce.disabled=!X||!de,ce.title=de?t("exc-ignore-hint"):t("exc-ignore-no-seller")}async function L(){if(!k.openExcId||!k.history||!k.history.pages||k.loading)return;k.loading=!0;const S=showToast(t("exc-fld-saving"),"loading",0);try{const w=JSON.parse(JSON.stringify(k.history.pages||[]));let m=w.findIndex(ie=>!ie.is_duplicate&&!ie.is_copy);m<0&&(m=0),w[m]||(w[m]={fields:{}});const H=w[m].fields||{},D=k.editFields||{},J=new Set(["subtotal","vat","total_amount"]),Z={...H};for(const ie in D){let V=D[ie];if((V===""||V===void 0)&&(V=null),J.has(ie)&&V!==null){const Q=parseFloat(V);V=isNaN(Q)?null:Q}Z[ie]=V}w[m].fields=Z;const le=await fetch("/api/history/"+encodeURIComponent(k.history.id),{method:"PUT",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({pages:w})});if(!le.ok)throw new Error("http "+le.status);S(),showToast(t("exc-fld-save-ok"),"success"),F(),await v(),await _(),a()}catch(w){S(),console.warn("save fields fail",w),showToast(t("exc-fld-save-fail"),"error")}finally{k.loading=!1}}async function $(){if(!(!k.openExcId||k.loading)){k.loading=!0;try{const S=await fetch("/api/exceptions/"+k.openExcId+"/resolve",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!S.ok)throw new Error("http "+S.status);showToast(t("exc-toast-resolved"),"success"),F(),await v(),await _(),a()}catch(S){console.warn("resolve fail",S),showToast(t("exc-toast-action-fail"),"error")}finally{k.loading=!1}}}async function E(){if(!(!k.openExcId||k.loading)){k.loading=!0;try{const S=await fetch("/api/exceptions/"+k.openExcId+"/ignore",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!S.ok)throw new Error("http "+S.status);showToast(t("exc-toast-ignored"),"success"),F(),await v(),await _(),a()}catch(S){console.warn("ignore fail",S),showToast(t("exc-toast-action-fail"),"error")}finally{k.loading=!1}}}let M=!1;async function K(){if(M)return;const S=Array.from(e.selectedIds);if(S.length===0||!await showConfirm(n("exc-batch-confirm-resolve",{n:S.length})))return;M=!0;const m=showToast(n("exc-batch-count",{n:S.length})+" …","loading",0);try{const H=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:S,action:"resolve"})});if(!H.ok)throw new Error("http "+H.status);const D=await H.json();m(),showToast(n("exc-toast-batch-resolved",{n:D.processed||0}),"success"),e.selectedIds.clear(),await v(),await _(),a()}catch(H){m(),console.warn("batch resolve fail",H),showToast(t("exc-toast-batch-fail"),"error")}finally{M=!1}}async function G(){if(M)return;const S=Array.from(e.selectedIds);if(S.length===0||!await showConfirm(n("exc-batch-confirm-ignore",{n:S.length}),{danger:!1}))return;M=!0;const m=showToast(n("exc-batch-count",{n:S.length})+" …","loading",0);try{const H=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:S,action:"ignore"})});if(!H.ok)throw new Error("http "+H.status);const D=await H.json();m(),showToast(n("exc-toast-batch-ignored",{n:D.processed||0,wl:D.whitelist_added||0}),"success"),e.selectedIds.clear(),await v(),await _(),a()}catch(H){m(),console.warn("batch ignore fail",H),showToast(t("exc-toast-batch-fail"),"error")}finally{M=!1}}function W(){e.selectedIds.clear(),r(e.listCache)}document.addEventListener("click",S=>{S.target.closest("#exc-drawer-close")&&F(),S.target.closest("#exc-drawer-mask")&&F(),S.target.closest("#exc-btn-resolve")&&$(),S.target.closest("#exc-btn-ignore")&&E(),S.target.closest("#exc-batch-resolve")&&K(),S.target.closest("#exc-batch-ignore")&&G(),S.target.closest("#exc-batch-clear")&&W(),S.target.closest("#exc-loadmore")&&q()}),document.addEventListener("keydown",S=>{S.key==="Escape"&&k.openExcId&&F()}),document.addEventListener("click",S=>{S.target.closest("#btn-exc-refresh")&&(typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),a())}),document.addEventListener("change",S=>{if(!S.target.closest("#exc-client-filter"))return;const w=S.target;e.currentClient=w.value||"",e.currentRule=null,e.selectedIds.clear(),e.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),a()}),document.addEventListener("click",S=>{const w=S.target.closest("#exc-status-tabs .exc-status-tab");if(!w)return;const m=w.dataset.status||"pending";m!==e.currentStatus&&(e.currentStatus=m,e.currentRule=null,e.selectedIds.clear(),e.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage())}),window.addEventListener("online",()=>{e.loadFailed&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage&&window.loadExceptionsPage()}),setTimeout(a,1500),setInterval(a,6e4);function te(S){if(!S)return"—";try{const w=new Date(S),m=H=>String(H).padStart(2,"0");return`${w.getFullYear()}-${m(w.getMonth()+1)}-${m(w.getDate())} ${m(w.getHours())}:${m(w.getMinutes())}`}catch{return S.slice(0,16).replace("T"," ")}}async function re(){const S=document.getElementById("learned-list");if(S){S.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-loading"))}</div>`;try{const w=await fetch("/api/exception-whitelist",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!w.ok)throw new Error("http "+w.status);const H=(await w.json()).items||[];if(H.length===0){S.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-empty"))}</div>`;return}const D=`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 4h8M5.5 4V2.5h3V4M4 4l0.6 8.5h4.8L10 4"/>
            </svg>`;S.innerHTML=H.map(J=>{const Z=t("exc-rule-"+J.rule_code)||J.rule_code;return`
                    <div class="learned-row" data-wl-id="${escapeHtml(String(J.id))}">
                        <div class="learned-seller" title="${escapeHtml(J.seller_name)}">${escapeHtml(J.seller_name)}</div>
                        <div class="learned-rule">${escapeHtml(Z)}</div>
                        <div class="learned-date">${escapeHtml(te(J.created_at))}</div>
                        <button class="learned-del-btn" data-del-wl="${escapeHtml(String(J.id))}" title="${escapeHtml(t("set-learned-del"))}" type="button">${D}</button>
                    </div>
                `}).join("")}catch(w){console.warn("loadLearnedRules fail",w),S.innerHTML=`<div class="learned-empty">${escapeHtml(t("exc-toast-load-fail"))}</div>`}}}window.loadLearnedRules=re,document.addEventListener("click",async S=>{const w=S.target.closest("[data-del-wl]");if(!w)return;const m=parseInt(w.dataset.delWl,10);if(!m)return;const H=w.closest(".learned-row"),D=H&&H.querySelector(".learned-seller"),J=D?D.textContent.trim():"",Z=t("set-learned-del-confirm").replace("{seller}",J);if(await showConfirm(Z,{danger:!0}))try{const ie=await fetch("/api/exception-whitelist/"+m,{method:"DELETE",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!ie.ok)throw new Error("http "+ie.status);showToast(t("set-learned-del-ok"),"success"),re(),typeof window.loadExceptionsPage=="function"&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage()}catch(ie){console.warn("delete whitelist fail",ie),showToast(t("set-learned-del-fail"),"error")}})})();(function(){let e={items:[],q:"",cat:"",selected:new Set,total:0,categories:{},pageSize:30,loading:!1,focusSearch:!1,searchCaret:0},n=null;function a(){return localStorage.getItem("mrpilot_token")||""}function o(c){const v=typeof currentLang=="string"&&currentLang||window._currentLang||"th",x=c.error_friendly&&c.error_friendly[v];if(x)return x;if(typeof humanizeError=="function"&&c.error_msg)try{return humanizeError(c.error_msg)}catch{}return t("erp-exc-reason-"+(c.category||"other"))}function s(){const c=document.getElementById("erp-exc-batch");if(!c)return;const v=e.selected.size;c.hidden=v===0;const x=c.querySelector(".erp-exc-batch-count");x&&(x.textContent=String(v))}function p(){const c=document.getElementById("erp-exc-block");if(!c)return;const v=e;if(!(v.total>0||!!v.q||!!v.cat)){c.hidden=!0,c.innerHTML="";return}c.hidden=!1;const _=v.categories||{},q=Object.keys(_).reduce((h,I)=>h+_[I],0);let j=`<button class="erp-exc-chip ${v.cat===""?"active":""}" data-erpexc-cat=""><span>${escapeHtml(t("erp-exc-cat-all"))}</span><span class="erp-exc-chip-count">${q}</span></button>`;Object.keys(_).forEach(h=>{j+=`<button class="erp-exc-chip ${v.cat===h?"active":""}" data-erpexc-cat="${escapeHtml(h)}"><span>${escapeHtml(t("erp-exc-cat-"+h))}</span><span class="erp-exc-chip-count">${_[h]}</span></button>`});const k=v.items||[],B=k.length>0&&k.every(h=>v.selected.has(h.id)),N=k.map(h=>{const I=h.state==="needs_action"?"needs":h.state==="retrying"?"retry":"fail",L=t("erp-exc-state-"+(h.state||"failed")),$=o(h),E=v.selected.has(h.id)?"checked":"";return`<div class="erp-exc-row" data-erpexc-id="${escapeHtml(h.id)}">
                <span class="ex-cb"><input type="checkbox" class="erp-exc-cb" data-erpexc-cb="${escapeHtml(h.id)}" ${E}></span>
                <span class="ex-inv" title="${escapeHtml(h.invoice_no||"")}">${escapeHtml(h.invoice_no||"—")}</span>
                <span class="ex-seller" title="${escapeHtml(h.seller_name||"")}">${escapeHtml(h.seller_name||"—")}</span>
                <span class="ex-buyer" title="${escapeHtml(h.ocr_buyer_name||"")}">${escapeHtml(h.ocr_buyer_name||"—")}</span>
                <span class="ex-state"><span class="erp-exc-state ${I}">${escapeHtml(L)}</span></span>
                <span class="ex-reason" title="${escapeHtml($)}">${escapeHtml($)}${h.error_code?` <span class="erp-exc-code">${escapeHtml(h.error_code)}</span>`:""}</span>
                <span class="ex-act"><button class="btn btn-sm btn-secondary" type="button" data-erpexc-retry="${escapeHtml(h.id)}">${escapeHtml(t("erp-exc-retry"))}</button></span>
            </div>`}).join(""),R=k.length===0?`<div class="erp-exc-empty">${escapeHtml(t("erp-exc-empty"))}</div>`:"",F=k.length<v.total?`<button class="erp-exc-more" type="button" id="erp-exc-more">${escapeHtml(t("erp-exc-load-more"))} (${k.length}/${v.total})</button>`:v.total>0?`<div class="erp-exc-count">${escapeHtml(t("erp-exc-shown",{n:k.length,total:v.total}))}</div>`:"";c.innerHTML=`
            <div class="erp-exc-head">
                <h2 class="erp-exc-title">${escapeHtml(t("erp-exc-title"))}</h2>
                <span class="erp-exc-sub">${escapeHtml(t("erp-exc-sub"))}</span>
                <input type="search" class="erp-exc-search" id="erp-exc-search" placeholder="${escapeHtml(t("erp-exc-search-ph"))}" value="${escapeHtml(v.q)}">
            </div>
            <div class="erp-exc-chips">${j}</div>
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
                ${N}${R}
            </div>
            <div class="erp-exc-foot">${F}</div>`;const A=document.getElementById("erp-exc-search");if(A){if(v.focusSearch){A.focus();try{A.setSelectionRange(v.searchCaret,v.searchCaret)}catch{}}A.addEventListener("input",()=>{v.q=A.value,v.focusSearch=!0,v.searchCaret=A.selectionStart||A.value.length,clearTimeout(n),n=setTimeout(()=>i(!1),350)}),A.addEventListener("blur",()=>{v.focusSearch=!1})}c.querySelectorAll(".erp-exc-chip").forEach(h=>{h.addEventListener("click",()=>{v.cat=h.dataset.erpexcCat||"",i(!1)})}),c.querySelectorAll("[data-erpexc-retry]").forEach(h=>{h.addEventListener("click",I=>{I.stopPropagation(),l(h.dataset.erpexcRetry,h)})}),c.querySelectorAll(".erp-exc-cb").forEach(h=>{h.addEventListener("change",()=>{const I=h.dataset.erpexcCb;h.checked?v.selected.add(I):v.selected.delete(I);const L=document.getElementById("erp-exc-cb-all");L&&(L.checked=k.length>0&&k.every($=>v.selected.has($.id))),s()})});const g=document.getElementById("erp-exc-cb-all");g&&g.addEventListener("change",()=>{k.forEach(h=>{g.checked?v.selected.add(h.id):v.selected.delete(h.id)}),c.querySelectorAll(".erp-exc-cb").forEach(h=>{h.checked=g.checked}),s()}),c.querySelectorAll("[data-erpexc-batch]").forEach(h=>{h.addEventListener("click",()=>y(h.dataset.erpexcBatch))});const f=document.getElementById("erp-exc-more");f&&f.addEventListener("click",()=>i(!0)),c.querySelectorAll(".erp-exc-row:not(.erp-exc-row-head)").forEach(h=>{h.addEventListener("click",I=>{I.target.closest("input,button")||typeof window._erpExcOpenEdit=="function"&&window._erpExcOpenEdit(h.dataset.erpexcId)})})}async function l(c,v){if(c){v&&(v.disabled=!0,v.textContent=t("erp-exc-retrying"));try{const x=await fetch("/api/erp/logs/"+encodeURIComponent(c)+"/retry",{method:"POST",headers:{Authorization:"Bearer "+a()}}),_=await x.json().catch(()=>({}));showToast(x.ok&&_.ok?t("erp-exc-retry-ok"):t("erp-exc-retry-fail"),x.ok&&_.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.delete(c),i(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function y(c){const v=Array.from(e.selected);if(c==="clear"){e.selected.clear(),p();return}if(v.length!==0){if(c==="delete"){if(!await showConfirm(t("erp-exc-batch-delete-confirm",{n:v.length}),{danger:!0}))return;try{const _=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:v.slice(0,200)})}),q=await _.json().catch(()=>({}));showToast(_.ok?t("erp-exc-batch-delete-ok",{n:q.deleted||0}):t("erp-exc-retry-fail"),_.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}}else if(c==="retry")try{const x=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:v.slice(0,50)})}),_=await x.json().catch(()=>({}));showToast(x.ok?t("erp-exc-batch-retry-ok",{ok:_.succeeded||0,fail:(_.failed||0)+(_.skipped||0)}):t("erp-exc-retry-fail"),x.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.clear(),i(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function i(c){const v=document.getElementById("erp-exc-block");if(!(!v||e.loading)){e.loading=!0;try{const x=new URLSearchParams;e.q&&x.set("q",e.q),e.cat&&x.set("category",e.cat),x.set("limit",String(e.pageSize)),x.set("offset",String(c?e.items.length:0));const _=await fetch("/api/erp/exceptions?"+x.toString(),{headers:{Authorization:"Bearer "+a()}});if(!_.ok){c||(v.hidden=!0);return}const q=await _.json(),j=q.items||[];e.items=c?e.items.concat(j):j,e.total=q.total||0,e.categories=q.categories||{},p()}catch{c||(v.hidden=!0)}finally{e.loading=!1}}}let r={};function d(){const c=document.getElementById("erp-exc-modal");c&&c.remove()}window._erpExcOpenEdit=function(c){const v=(e.items||[]).find(R=>String(R.id)===String(c));if(!v)return;const x=!!v.history_client_id&&v.category==="customer_mismatch",_=v.category==="product_mismatch"&&!!v.history_id&&!!v.endpoint_id,q=o(v),j=v.state==="needs_action"?"needs":v.state==="retrying"?"retry":"fail",k=(R,F)=>`<div class="erp-exc-m-row"><span class="erp-exc-m-k">${escapeHtml(R)}</span><span class="erp-exc-m-v">${escapeHtml(F||"—")}</span></div>`;let B="";if(x)B=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-pick"))}</div>
                    <input type="search" class="erp-exc-m-search" id="erp-exc-m-search" placeholder="${escapeHtml(t("erp-exc-edit-pick-ph"))}">
                    <div class="erp-exc-m-custlist" id="erp-exc-m-custlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-pick-loading"))}</div>
                    </div>
                </div>`;else if(_)B=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-prod-intro"))}</div>
                    <div class="erp-exc-m-custlist" id="erp-exc-m-prodlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-prod-loading"))}</div>
                    </div>
                </div>`;else{const R="erp-exc-edit-hint-"+(v.category||"other");let F=t(R);(!F||F===R)&&(F=q),B=`<div class="erp-exc-m-hint">${escapeHtml(F)}</div>`}const N=document.createElement("div");if(N.id="erp-exc-modal",N.className="erp-exc-modal-overlay",N.innerHTML=`
            <div class="erp-exc-modal" role="dialog" aria-modal="true">
                <div class="erp-exc-m-head">
                    <h3>${escapeHtml(t("erp-exc-edit-title"))}</h3>
                    <button class="erp-exc-m-close" type="button" id="erp-exc-m-close" aria-label="close">×</button>
                </div>
                <div class="erp-exc-m-body">
                    <div class="erp-exc-m-reason"><span class="erp-exc-state ${j}">${escapeHtml(t("erp-exc-state-"+(v.state||"failed")))}</span> ${escapeHtml(q)}${v.error_code?` <span class="erp-exc-code">${escapeHtml(v.error_code)}</span>`:""}</div>
                    ${k(t("erp-exc-f-invoice"),v.invoice_no)}
                    ${k(t("erp-exc-f-seller"),v.seller_name)}
                    ${k(t("erp-exc-f-buyer"),v.ocr_buyer_name)}
                    ${k(t("erp-exc-edit-field-current"),v.client_name)}
                    ${B}
                </div>
                <div class="erp-exc-m-foot">
                    <button class="btn btn-sm btn-ghost" type="button" id="erp-exc-m-cancel">${escapeHtml(t("erp-exc-edit-close"))}</button>
                    <button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-retry">${escapeHtml(t("erp-exc-edit-retry"))}</button>
                    ${x?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind" disabled>${escapeHtml(t("erp-exc-edit-bind-retry"))}</button>`:""}
                    ${_?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind-prod" disabled>${escapeHtml(t("erp-exc-edit-bind-prod-retry"))}</button>`:""}
                </div>
            </div>`,document.body.appendChild(N),N.addEventListener("click",R=>{R.target===N&&d()}),document.getElementById("erp-exc-m-close").addEventListener("click",d),document.getElementById("erp-exc-m-cancel").addEventListener("click",d),document.getElementById("erp-exc-m-retry").addEventListener("click",()=>{d(),l(v.id,null)}),x){let R="";const F=document.getElementById("erp-exc-m-bind"),A=document.getElementById("erp-exc-m-custlist"),g=document.getElementById("erp-exc-m-search"),f=(I,L)=>{const $=(L||"").trim().toLowerCase(),E=$?I.filter(M=>(M.code||"").toLowerCase().includes($)||(M.name||"").toLowerCase().includes($)):I;if(E.length===0){A.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-empty"))}</div>`;return}A.innerHTML=E.slice(0,100).map(M=>`<div class="erp-exc-m-cust" data-cust-code="${escapeHtml(M.code||"")}">
                        <span class="erp-exc-m-cust-name">${escapeHtml(M.name||"")}</span>
                        <span class="erp-exc-m-cust-code">${escapeHtml(M.code||"")}</span>
                    </div>`).join(""),A.querySelectorAll(".erp-exc-m-cust").forEach(M=>{M.addEventListener("click",()=>{R=M.dataset.custCode||"",A.querySelectorAll(".erp-exc-m-cust").forEach(K=>K.classList.remove("sel")),M.classList.add("sel"),F&&(F.disabled=!R)})})},h=async()=>{const I=v.endpoint_id;if(r[I]){f(r[I],"");return}try{const L=await fetch("/api/erp/endpoints/"+encodeURIComponent(I)+"/customers",{headers:{Authorization:"Bearer "+a()}}),$=await L.json().catch(()=>({}));if(!L.ok||!$.ok){A.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`;return}const E=$.customers||[];r[I]=E,f(E,"")}catch{A.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`}};g&&g.addEventListener("input",()=>f(r[v.endpoint_id]||[],g.value)),h(),F&&F.addEventListener("click",async()=>{if(R){F.disabled=!0,F.textContent=t("erp-exc-retrying");try{if(!(await fetch("/api/erp/mappings/clients",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({client_id:v.history_client_id,erp_type:v.endpoint_adapter,erp_code:R})})).ok){showToast(t("erp-exc-retry-fail"),"error"),F.disabled=!1,F.textContent=t("erp-exc-edit-bind-retry");return}showToast(t("erp-exc-edit-bound-ok"),"success"),d(),await l(v.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),F.disabled=!1,F.textContent=t("erp-exc-edit-bind-retry")}}})}if(_){const R=document.getElementById("erp-exc-m-bind-prod"),F=document.getElementById("erp-exc-m-prodlist"),A={};let g=[];const f=()=>'<option value="">'+escapeHtml(t("erp-exc-edit-prod-choose"))+"</option>"+g.slice(0,500).map(L=>`<option value="${escapeHtml(L.code||"")}" data-pname="${escapeHtml(L.name||"")}">`+escapeHtml((L.name||"")+" · "+(L.code||""))+"</option>").join(""),h=L=>{if(!L.length){F.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-noitems"))}</div>`;return}F.innerHTML=L.map($=>`<div class="erp-exc-m-cust" style="cursor:default">
                        <span class="erp-exc-m-cust-name" title="${escapeHtml($)}">${escapeHtml($)}</span>
                        <select class="erp-exc-m-prod-sel" data-item="${escapeHtml($)}" style="max-width:55%;flex:0 0 auto;padding:4px 6px;border:1px solid var(--border,#e5e7eb);border-radius:6px;font-size:12px">${f()}</select>
                    </div>`).join(""),F.querySelectorAll(".erp-exc-m-prod-sel").forEach($=>{$.addEventListener("change",()=>{const E=$.dataset.item,M=$.options[$.selectedIndex];$.value?A[E]={code:$.value,name:M&&M.dataset.pname||""}:delete A[E],R&&(R.disabled=Object.keys(A).length===0)})})};(async()=>{try{const $=await(await fetch("/api/history/"+encodeURIComponent(v.history_id),{headers:{Authorization:"Bearer "+a()}})).json().catch(()=>({})),E=$&&$.pages||[],M=[],K={};(Array.isArray(E)?E:[]).forEach(te=>{const re=te&&te.fields&&te.fields.items||[];(Array.isArray(re)?re:[]).forEach(S=>{const w=(S&&(S.name||S.description)||"").trim();w&&!K[w]&&(K[w]=1,M.push(w))})});const G=await fetch("/api/erp/endpoints/"+encodeURIComponent(v.endpoint_id)+"/products",{headers:{Authorization:"Bearer "+a()}}),W=await G.json().catch(()=>({}));if(!G.ok||!W.ok){F.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`;return}g=W.products||[],h(M)}catch{F.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`}})(),R&&R.addEventListener("click",async()=>{const L=Object.entries(A);if(L.length){R.disabled=!0,R.textContent=t("erp-exc-retrying");try{for(const[$,E]of L)if(!(await fetch("/api/erp/mappings/products",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({erp_type:v.endpoint_adapter,item_name:$,erp_code:E.code,erp_name:E.name})})).ok){showToast(t("erp-exc-retry-fail"),"error"),R.disabled=!1,R.textContent=t("erp-exc-edit-bind-prod-retry");return}showToast(t("erp-exc-edit-prod-bound-ok"),"success"),d(),await l(v.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),R.disabled=!1,R.textContent=t("erp-exc-edit-bind-prod-retry")}}})}},window._rerenderErpExceptions=p,window.loadErpExceptions=i,window._erpExcState=e})();(function(){function e(c){try{if(location.search.indexOf("test_center=1")>=0||localStorage.getItem("pearnly_test_mode")==="1"||c&&c.id&&String(c.id)==="468b50c1-5593-4fd6-990d-515ce8085563")return!0}catch{}return!1}window.applyRoleVisibility=function(){var v=window._userInfo,x=!1,_=!0,q=!1,j=!1;v&&(x=typeof canManageTeam=="function"?canManageTeam(v):!!(v.role==="owner"||v.is_super_admin),_=typeof shouldHideMoney=="function"?shouldHideMoney(v):v.role==="member"&&!v.is_super_admin,q=typeof isSuperAdmin=="function"?isSuperAdmin(v):!!v.is_super_admin,j=e(v)),document.querySelectorAll("[data-show-if-team]").forEach(function(B){B.style.display=x?"":"none"}),document.querySelectorAll("[data-show-if-money]").forEach(function(B){B.style.display=_?"none":""}),document.querySelectorAll("[data-show-if-admin]").forEach(function(B){B.style.display=q?"":"none"}),document.querySelectorAll("[data-show-if-test]").forEach(function(B){B.style.display=j?"":"none"});var k=q||j;document.querySelectorAll("[data-show-if-special]").forEach(function(B){B.style.display=k?"":"none"})},window.renderAvatarMenu=function(v){if(v){var x=document.getElementById("avatar-btn"),_=document.getElementById("avatar-popup-name"),q=document.getElementById("avatar-popup-email");if(!(!x||!_||!q)){var j=(v.username||"").trim(),k=j.split("@")[0]||j||"—",B=(j.charAt(0)||"?").toUpperCase(),N=(v.avatar_url||"").trim();if(N){var R=N.replace(/"/g,"&quot;"),F=B.replace(/'/g,"\\'");x.innerHTML='<img src="'+R+'" alt="'+B+`" referrerpolicy="no-referrer" onerror="this.parentNode.textContent='`+F+`'">`}else x.textContent=B;_.textContent=k,q.textContent=j||"—",x.setAttribute("title",j||"")}}};function n(){var c=document.getElementById("avatar-wrap"),v=document.getElementById("avatar-btn"),x=document.getElementById("avatar-popup");if(!c||!v||!x)return;function _(){x.classList.remove("show"),v.setAttribute("aria-expanded","false")}function q(){x.classList.add("show"),v.setAttribute("aria-expanded","true")}v.addEventListener("click",function(j){j.stopPropagation(),x.classList.contains("show")?_():q()}),document.addEventListener("click",function(j){x.classList.contains("show")&&!c.contains(j.target)&&_()}),x.addEventListener("click",function(j){var k=j.target.closest(".avatar-popup-item");if(k){var B=k.dataset.action;switch(_(),B){case"settings":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings");break;case"team":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("team")},50);break;case"billing":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("plan")},50);break;case"shortcuts":if(typeof showToast=="function"){var N=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(N||"即将上线","info")}break;case"admin":window.location.href="/admin/cost";break;case"test-center":typeof routeTo=="function"&&routeTo("test-center");break;case"help":var R=document.getElementById("help-modal");R&&(R.style.display="flex");break;case"logout":try{localStorage.removeItem("mrpilot_token")}catch{}try{localStorage.removeItem("mrpilot_user")}catch{}window.location.href="/";break}}}),window._closeAvatarPopup=_}function a(){return[].slice.call(document.querySelectorAll(".cmdk-item")).filter(function(c){return c.style.display!=="none"})}function o(c){var v=a();v.forEach(function(x){x.classList.remove("focus")}),v[c]&&(v[c].classList.add("focus"),v[c].scrollIntoView({block:"nearest"}))}function s(c){var v=a();if(v.length){var x=v.findIndex(function(q){return q.classList.contains("focus")});x<0&&(x=0);var _=(x+c+v.length)%v.length;o(_)}}function p(c){c=(c||"").toLowerCase().trim();var v=0,x=window._userInfo,_=typeof isSuperAdmin=="function"?isSuperAdmin(x):!!(x&&x.is_super_admin),q=e(x);document.querySelectorAll(".cmdk-item").forEach(function(k){if(k.dataset.showIfAdmin==="1"&&!_){k.style.display="none";return}if(k.dataset.showIfTest==="1"&&!q){k.style.display="none";return}var B=(k.dataset.cmdkText||k.textContent||"").toLowerCase(),N=!c||B.indexOf(c)>=0;k.style.display=N?"":"none",k.classList.remove("focus"),N&&v++}),document.querySelectorAll("[data-cmdk-section]").forEach(function(k){for(var B=k.nextElementSibling,N=!1;B&&!B.hasAttribute("data-cmdk-section");){if(B.classList&&B.classList.contains("cmdk-item")&&B.style.display!=="none"){N=!0;break}B=B.nextElementSibling}k.style.display=N?"":"none"});var j=document.getElementById("cmdk-empty");j&&(j.style.display=v===0?"flex":"none"),o(0)}window.openCmdk=function(){var v=document.getElementById("cmdk-mask");v&&(typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup(),v.classList.add("show"),typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility(),setTimeout(function(){var x=document.getElementById("cmdk-input");x&&(x.value="",p(""),x.focus(),o(0))},50))},window.closeCmdk=function(){var v=document.getElementById("cmdk-mask");v&&v.classList.remove("show")};function l(c){if(c){if(c.classList.contains("cmdk-item-locked")){if(typeof showToast=="function"){var v=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(v||"即将上线","info")}return}var x=c.dataset.cmdkRoute,_=c.dataset.cmdkAction;if(window.closeCmdk(),x){typeof routeTo=="function"&&routeTo(x);return}if(_){if(_==="open-admin"){window.location.href="/admin/cost";return}if(_.indexOf("lang-")===0){var q=_.slice(5);typeof applyLang=="function"&&applyLang(q)}}}}function y(){var c=document.getElementById("cmdk-mask"),v=document.getElementById("cmdk-input"),x=document.getElementById("cmdk-body");if(!(!c||!v||!x)){c.addEventListener("click",function(j){j.target===c&&window.closeCmdk()});var _=document.getElementById("cmdk-esc-btn");_&&_.addEventListener("click",function(){window.closeCmdk()}),v.addEventListener("input",function(j){p(j.target.value)}),v.addEventListener("keydown",function(j){j.key==="ArrowDown"?(j.preventDefault(),s(1)):j.key==="ArrowUp"?(j.preventDefault(),s(-1)):j.key==="Enter"?(j.preventDefault(),l(c.querySelector(".cmdk-item.focus"))):j.key==="Escape"&&(j.preventDefault(),window.closeCmdk())}),x.addEventListener("click",function(j){var k=j.target.closest(".cmdk-item");k&&l(k)}),x.addEventListener("mousemove",function(j){var k=j.target.closest(".cmdk-item");!k||k.style.display==="none"||k.classList.contains("cmdk-item-locked")||(a().forEach(function(B){B.classList.remove("focus")}),k.classList.add("focus"))});var q=document.getElementById("topbar-search");q&&(q.addEventListener("click",function(){window.openCmdk()}),q.addEventListener("keydown",function(j){(j.key==="Enter"||j.key===" ")&&(j.preventDefault(),window.openCmdk())}))}}document.addEventListener("keydown",function(c){if((c.metaKey||c.ctrlKey)&&(c.key==="k"||c.key==="K")){c.preventDefault(),window.openCmdk();return}if(c.key==="Escape"){var v=document.getElementById("cmdk-mask");if(v&&v.classList.contains("show")){window.closeCmdk();return}var x=document.getElementById("avatar-popup");x&&x.classList.contains("show")&&typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup()}});try{var i=(navigator.userAgent||"").toLowerCase(),r=i.indexOf("mac")>=0||i.indexOf("iphone")>=0||i.indexOf("ipad")>=0;r||document.body.classList.add("is-windows")}catch{}function d(){n(),y(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("nav-ia-phase1-role",function(){try{typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",d):d()})();(function(){function n(_){return String(_??"").replace(/[&<>"']/g,function(q){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[q]})}function a(_){if(!_||isNaN(_))return"";var q=Number(_);return q<1024?q+" B":q<1024*1024?(q/1024).toFixed(1)+" KB":(q/1024/1024).toFixed(1)+" MB"}document.addEventListener("click",function(_){var q=_.target.closest&&_.target.closest(".recon-collapse-head");if(q&&!(_.target.closest("button")||_.target.closest("a"))){var j=q.closest(".recon-collapse");if(j){var k=j.getAttribute("data-collapsed")==="true";j.setAttribute("data-collapsed",k?"false":"true"),k&&(j.id==="vex-summary-collapse"&&d(),j.id==="vex-detail-collapse"&&c())}}}),document.addEventListener("keydown",function(_){if(!(_.key!=="Enter"&&_.key!==" ")){var q=_.target.closest&&_.target.closest(".recon-collapse-head");q&&(_.preventDefault(),q.click())}});var o={vat:"",gl:""};window._glvClearPreviewSearch=function(){o.vat="",o.gl=""};var s='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',p='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function l(){i("vat"),i("gl")}function y(_){try{if(typeof window._glvPreviewFiles=="function")return window._glvPreviewFiles(_)||[]}catch{}var q=document.getElementById(_==="vat"?"glv-vat-input":"glv-gl-input");return q&&q.files?Array.from(q.files):[]}function i(_){var q=document.getElementById(_==="vat"?"glv-pp-vat-col":"glv-pp-gl-col");if(q){var j=y(_),k=_==="vat"?"glv-up-vat-title":"glv-up-gl-title",B=_==="vat"?"① 销项税报告":"② 总账 GL",N=window.t&&window.t(k)||B,R=n(window.t&&window.t("vex-preview-search")||"搜索文件名..."),F=n(window.t&&window.t("vex-preview-clear-all")||"全清"),A=o[_]||"",g=j.length;q.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+n(N)+' <span class="vex-pp-col-count">'+g+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="glv-pp-search-'+_+'" type="text" placeholder="'+R+'" value="'+n(A)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="glv-pp-clearall-'+_+'" type="button">'+F+'</button></div><div class="vex-pp-file-list" id="glv-pp-'+_+'-list"></div><div class="vex-pp-pagination" id="glv-pp-'+_+'-pg"></div>';var f=document.getElementById("glv-pp-search-"+_);f&&f.addEventListener("input",function(I){o[_]=I.target.value,r(_)});var h=document.getElementById("glv-pp-clearall-"+_);h&&h.addEventListener("click",function(){window._glvRemoveFile&&window._glvRemoveFile(_)}),r(_)}}function r(_){var q=document.getElementById("glv-pp-"+_+"-list"),j=document.getElementById("glv-pp-"+_+"-pg");if(q){var k=y(_),B=(o[_]||"").toLowerCase(),N=k.map(function(A,g){return{f:A,i:g}}),R=B?N.filter(function(A){return A.f.name.toLowerCase().indexOf(B)>=0}):N;if(q.innerHTML=R.map(function(A){var g=A.f;return'<div class="vex-pp-file-row">'+s+'<span class="vex-pp-fi-name" title="'+n(g.name)+'">'+n(g.name)+'</span><span class="vex-pp-fi-size">'+a(g.size)+'</span><button class="vex-pp-fi-del" type="button" data-kind="'+_+'" data-idx="'+A.i+'" aria-label="remove">'+p+"</button></div>"}).join(""),q.querySelectorAll(".vex-pp-fi-del").forEach(function(A){A.addEventListener("click",function(){var g=A.dataset.kind,f=parseInt(A.dataset.idx,10);window._glvRemoveFile&&window._glvRemoveFile(g,isNaN(f)?null:f)})}),j){var F=window.t&&window.t("vex-preview-count")||"显示前 {n} / 共 {m}";j.textContent=F.replace("{n}",R.length).replace("{m}",R.length)}}}function d(){var _=function(j,k){var B=document.getElementById(j);B&&(B.textContent=k==null?"—":String(k))},q=window._vexLastTask||{};_("vex-sum-total",q.total),_("vex-sum-matched",q.matched),_("vex-sum-diff",q.diff),_("vex-sum-incomplete",q.incomplete),_("vex-sum-cash",q.cash),document.getElementById("vex-summary-sub")}function c(){var _=window._vexLastTask&&window._vexLastTask.diff_rows||[],q=document.getElementById("vex-detail-tbody"),j=document.getElementById("vex-detail-table"),k=document.getElementById("vex-detail-empty");if(!(!q||!j||!k)){if(_.length===0){j.style.display="none",k.style.display="";return}k.style.display="none",j.style.display="";var B=_.map(function(R){return'<tr><td class="recon-detail-cell-mono">'+n(R.invoice_no||"")+"</td><td>"+n(R.field||"")+"</td><td>"+n(R.report_value||"")+"</td><td>"+n(R.invoice_value||"")+"</td><td>"+n(R.kind||"")+"</td></tr>"}).join("");q.innerHTML=B;var N=document.getElementById("vex-detail-sub");N&&(N.textContent=String(_.length))}}function v(){var _=document.getElementById("glv-toggle-preview");_&&!_._reconBound&&(_._reconBound=!0,_.addEventListener("click",function(){var q=document.getElementById("glv-preview-panel"),j=document.getElementById("glv-toggle-preview-label"),k=q&&q.style.display!=="none";q&&(q.style.display=k?"none":""),_.classList.toggle("open",!k),j&&(j.textContent=k?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),k||l()})),["glv-vat-input","glv-gl-input"].forEach(function(q){var j=document.getElementById(q);!j||j._reconWatched||(j._reconWatched=!0,j.addEventListener("change",function(){var k=document.getElementById("glv-preview-panel");k&&k.style.display!=="none"&&l()}))})}function x(){var _=document.getElementById("vex-summary-collapse"),q=document.getElementById("vex-detail-collapse");_&&(_.style.display=""),q&&(q.style.display=""),d(),c()}window._fillVexSummary=d,window._fillVexDetail=c,window._onVexResultShown=x,document.addEventListener("DOMContentLoaded",function(){v()}),setTimeout(v,1500),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-collapse",function(){var _=document.getElementById("glv-preview-panel");_&&_.style.display!=="none"&&l();var q=document.getElementById("glv-toggle-preview-label"),j=document.getElementById("glv-toggle-preview");q&&j&&(q.textContent=j.classList.contains("open")?window.t&&window.t("vex-toggle-preview-close")||"收起清单":window.t&&window.t("vex-toggle-preview-open")||"查看清单")}),window._reconCollapse={renderGlvPreview:l,fillVexSummary:d,fillVexDetail:c}})();(function(){function e(p){}function n(){const p=document.querySelectorAll("[data-recon-tab]");p.forEach(y=>{y.addEventListener("click",()=>{p.forEach(v=>v.classList.remove("active")),y.classList.add("active");const i=y.dataset.reconTab,r=document.getElementById("recon-pane-bank"),d=document.getElementById("recon-pane-sale-vat"),c=document.getElementById("recon-pane-gl-vat");r&&(r.style.display=i==="bank"?"":"none"),d&&(d.style.display=i==="sale-vat"?"":"none"),c&&(c.style.display=i==="gl-vat"?"":"none"),i==="gl-vat"&&window.GlVatRecon&&window.GlVatRecon.ensureInit(),i==="bank"&&typeof window._bankReconV2Init=="function"&&window._bankReconV2Init()})});const l=document.querySelector("[data-recon-tab].active");l&&(l.dataset.reconTab,void 0)}function a(){const p=document.getElementById("page-settings");if(!p)return null;let l=document.getElementById("settings-modal-overlay");if(l)return l;l=document.createElement("div"),l.id="settings-modal-overlay",l.className="settings-modal-overlay",l.style.display="none",p.parentElement.insertBefore(l,p),l.appendChild(p);const y=document.createElement("button");return y.id="settings-modal-close",y.className="settings-modal-close",y.setAttribute("aria-label","close"),y.innerHTML='<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 5l10 10M15 5L5 15"/></svg>',p.insertBefore(y,p.firstChild),y.addEventListener("click",s),l.addEventListener("click",i=>{i.target===l&&s()}),l}function o(){const p=a();if(!p)return;p.style.display="flex",document.body.classList.add("settings-modal-open");const l=document.getElementById("page-settings");l&&(l.style.display="block"),setTimeout(()=>{try{typeof renderSettings=="function"&&renderSettings()}catch(i){console.warn("renderSettings:",i)}let y=document.querySelector(".settings-tab.active")||document.querySelector('.settings-tab[data-tab="profile"]');y&&y.click()},50)}function s(){const p=document.getElementById("settings-modal-overlay");p&&(p.style.display="none"),document.body.classList.remove("settings-modal-open")}window.openSettingsModal=o,window.closeSettingsModal=s,document.addEventListener("keydown",p=>{if(p.key==="Escape"){const l=document.getElementById("settings-modal-overlay");l&&l.style.display==="flex"&&s()}}),window.addEventListener("hashchange",()=>{location.hash==="#/settings"&&o()}),window.addEventListener("DOMContentLoaded",()=>{location.hash==="#/settings"&&o()}),document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){const a=/\.(pdf|jpe?g|png|webp|tiff?|xlsx?|xlsm|csv|tsv|docx?)$/i,o=V=>document.getElementById(V);function s(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}function p(V){return String(V??"").replace(/[&<>"']/g,Q=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[Q])}function l(V){return V<1024?V+" B":V<1024*1024?(V/1024).toFixed(1)+" KB":(V/1024/1024).toFixed(1)+" MB"}let y=[],i=[],r=!1,d=[],c=50,v=50,x="",_="";async function q(){try{const V=await fetch("/api/vat_excel/tasks?page=1&page_size=1",{headers:s()});if(!V.ok)return;const ee=(await V.json()).kpi||{};[["vex-kpi-month-val",ee.this_month],["vex-kpi-running-val",ee.running],["vex-kpi-done-val",ee.done],["vex-kpi-failed-val",ee.failed]].forEach(([ne,oe])=>{const ue=document.getElementById(ne);ue&&(ue.textContent=oe??0)})}catch{}}async function j(){try{const V=await fetch("/api/vat_excel/tasks?page=1&page_size=100",{headers:s()});if(!V.ok)return;const Q=await V.json();R(Q.rows||[])}catch{}}const k=10;var B=1;function N(){var V=((document.getElementById("vex-task-search")||{}).value||"").trim().toLowerCase();if(B=1,R(d),!!V){var Q=document.getElementById("vex-task-tbody");Q&&Q.querySelectorAll("tr").forEach(function(ee){ee.dataset.taskId&&(ee.style.display=ee.textContent.toLowerCase().indexOf(V)>=0?"":"none")})}}function R(V){d=V||d;const Q=document.getElementById("vex-task-tbody");if(!Q)return;if(!d.length){Q.innerHTML='<tr><td colspan="9" class="vex-task-empty">'+(t("sv-empty-title")||"还没有对账任务")+"</td></tr>",F(0);return}const ee=Math.ceil(d.length/k);B>ee&&(B=ee);const ne=(B-1)*k;A(d.slice(ne,ne+k)),F(d.length)}function F(V){const Q=document.getElementById("vex-task-pager"),ee=document.getElementById("vex-task-pager-info"),ne=document.getElementById("vex-task-prev"),oe=document.getElementById("vex-task-next");if(!Q)return;if(V<=k){Q.style.display="none";return}Q.style.display="";const ue=Math.ceil(V/k);ee&&(ee.textContent=B+" / "+ue),ne&&(ne.disabled=B<=1),oe&&(oe.disabled=B>=ue)}function A(V){const Q=document.getElementById("vex-task-tbody");if(!Q)return;const ee={pending:t("vex-status-pending")||"待处理",running:t("vex-status-running")||"处理中",done:t("vex-status-done")||"已完成",failed:t("vex-status-failed")||"失败"},ne={pending:"badge-gray",running:"badge-blue",done:"badge-green",failed:"badge-red"},oe='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',ue='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h10M6 4V3h4v1M5 4v8a1 1 0 001 1h4a1 1 0 001-1V4"/></svg>';Q.innerHTML=V.map(b=>{const C=b.created_at?new Date(b.created_at).toLocaleString([],{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}):"—",T=b.period||"—",U=b.matched_count!=null?b.matched_count+" ✓ · "+b.mismatched_count+" ⚠":"—",z=b.mismatch_amount!=null?"฿ "+Number(b.mismatch_amount).toLocaleString():"—",u=b.elapsed_seconds!=null?b.elapsed_seconds.toFixed(1)+" s":"—",P=b.status||"pending",O=b.client_name&&b.client_name!=="client"?b.client_name:t("vex-client-all")||"全部客户";return`<tr class="vex-task-row" data-task-id="${p(b.id)}" style="cursor:pointer">
                <td>${C}</td>
                <td>${p(O)}</td>
                <td>${p(T)}</td>
                <td>${(b.invoice_count||0)+" / "+(b.report_count||0)}</td>
                <td>${U}</td>
                <td>${z}</td>
                <td><span class="badge ${ne[P]||"badge-gray"}">${ee[P]||P}</span></td>
                <td>${u}</td>
                <td><div class="vex-task-actions">
                    <button class="vex-task-dl-btn" data-task-id="${p(b.id)}" title="${t("hist_export")||"导出"}">${oe}</button>
                    <button class="vex-task-del-btn" data-task-id="${p(b.id)}" title="${t("vex-task-delete-confirm-title")||"删除"}">${ue}</button>
                </div></td>
            </tr>`}).join(""),Q.querySelectorAll(".vex-task-dl-btn").forEach(b=>{b.addEventListener("click",async C=>{C.stopPropagation();const T=b.dataset.taskId;try{const U=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(T)+"/download",{credentials:"include",headers:s()});if(U.status===410){showToast(t("vex-toast-expired")||"数据已过期 · 请重新对账","warn");return}if(!U.ok){showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error");return}const z=await U.blob(),P=(U.headers.get("Content-Disposition")||"").match(/filename\*?=(?:UTF-8''|")?([^";]+)/i),O=P?decodeURIComponent(P[1]):"vat_recon_"+T+".xlsx",Y=URL.createObjectURL(z),X=document.createElement("a");X.href=Y,X.download=O,X.click(),setTimeout(()=>URL.revokeObjectURL(Y),1e3)}catch{showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error")}})}),Q.querySelectorAll(".vex-task-del-btn").forEach(b=>{b.addEventListener("click",C=>{C.stopPropagation(),f(b.dataset.taskId)})}),N()}function g(){var V=document.getElementById("vex-task-prev"),Q=document.getElementById("vex-task-next");V&&!V._vexBound&&(V._vexBound=!0,V.addEventListener("click",function(){B>1&&(B--,R())})),Q&&!Q._vexBound&&(Q._vexBound=!0,Q.addEventListener("click",function(){var ee=Math.ceil(d.length/k);B<ee&&(B++,R())}))}async function f(V){const Q=t("vex-task-delete-confirm-title")||"删除对账任务?",ee=t("vex-task-delete-confirm-body")||"同时清掉对应的发票识别缓存 · 不可恢复";if(await showConfirm(ee,{title:Q,danger:!0,okText:t("vex-task-delete-confirm-title")||"确认删除"}))try{const oe=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(V),{method:"DELETE",credentials:"include",headers:s()});if(!oe.ok)throw new Error(oe.status);showToast(t("vex-task-delete-ok")||"已删除","success"),j(),q()}catch{showToast(t("vex-task-delete-fail")||"删除失败","error")}}function h(V){const Q=window._currentLang||"th",ee={zh:`已忽略 ${V} 个不支持的文件 · 仅支持 PDF / 图片 / Excel / CSV / Word`,th:`ข้ามไฟล์ที่ไม่รองรับ ${V} ไฟล์ · รองรับเฉพาะ PDF / รูปภาพ / Excel / CSV / Word`,en:`Ignored ${V} unsupported file(s) · only PDF / image / Excel / CSV / Word are supported`,ja:`非対応ファイル ${V} 件をスキップ · 対応形式は PDF / 画像 / Excel / CSV / Word のみ`};showToast(ee[Q]||ee.th,"warn")}function I(V){const Q=new Set(y.map(ne=>ne.name+"|"+ne.size));let ee=0;for(const ne of V){if(!a.test(ne.name)){ee++;continue}const oe=ne.name+"|"+ne.size;if(!Q.has(oe)&&(Q.add(oe),y.push(ne),y.length>=1e3))break}ee>0&&h(ee),y.length>1e3&&(y=y.slice(0,1e3),showToast(t("vex-toast-cap-inv"),"warn")),M()}function L(V){const Q=new Set(i.map(ne=>ne.name+"|"+ne.size));let ee=0;for(const ne of V){if(!a.test(ne.name)){ee++;continue}const oe=ne.name+"|"+ne.size;if(!Q.has(oe)&&(Q.add(oe),i.push(ne),i.length>=30))break}ee>0&&h(ee),i.length>30&&(i=i.slice(0,30),showToast(t("vex-toast-cap-rep"),"warn")),M()}function $(V){y.splice(V,1),M()}function E(V){i.splice(V,1),M()}function M(){const V=o("vex-list-invoice"),Q=o("vex-list-report"),ee=o("vex-count-invoice"),ne=o("vex-count-report");ee&&(ee.textContent=y.length),ne&&(ne.textContent=i.length);const oe=(C,T,U)=>`<div class="vex-fi">
            <svg class="vex-fi-ic" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2h6l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M10 2v4h4"/></svg>
            <span class="vex-fi-n" title="${p(C.name)}">${p(C.name)}</span>
            <span class="vex-fi-s">${l(C.size)}</span>
            <button class="vex-fi-x" type="button" data-vex-kind="${U}" data-vex-idx="${T}" aria-label="remove">×</button>
        </div>`;V&&(V.innerHTML=y.map((C,T)=>oe(C,T,"inv")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),Q&&(Q.innerHTML=i.map((C,T)=>oe(C,T,"rep")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),document.querySelectorAll(".vex-fi-x").forEach(C=>{C.addEventListener("click",T=>{const U=C.dataset.vexKind,z=parseInt(C.dataset.vexIdx,10);U==="inv"?$(z):E(z)})});const ue=y.length>0&&i.length>0;o("vex-build").disabled=!ue||r;const b=o("vex-action-info");b&&(!y.length||!i.length?(b.textContent=t("vex-need-both")||"需要至少 1 张发票 + 1 份 VAT 报告",b.className="vex-action-info muted"):(b.textContent=(t("vex-ready")||"已就绪 · {a} 张发票 · {b} 份报告").replace("{a}",y.length).replace("{b}",i.length),b.className="vex-action-info ok")),te()}const K='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>',G='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',W='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function te(){const V=o("vex-preview-panel");if(!V||V.style.display==="none")return;re("inv"),re("rep");const Q=o("vex-pp-guide");Q&&(Q.style.display=y.length>100?"flex":"none")}function re(V){const Q=o(V==="inv"?"vex-pp-invoice-col":"vex-pp-report-col");if(!Q)return;const ee=V==="inv"?y:i,ne=V==="inv"?x:_,oe=t(V==="inv"?"vex-preview-invoice":"vex-preview-report")||(V==="inv"?"销售发票":"VAT 报告"),ue=p(t("vex-preview-search")||"搜索文件名..."),b=p(t("vex-preview-clear-all")||"全清");Q.innerHTML=`
            <div class="vex-pp-col-title">
                <span class="vex-pp-col-name">${p(oe)} <span class="vex-pp-col-count">${ee.length}</span></span>
            </div>
            <div class="vex-pp-search-row">
                <input class="vex-pp-search" id="vex-pp-search-${V}" type="text"
                       placeholder="${ue}" value="${p(ne)}" autocomplete="off">
                <button class="vex-pp-clear-btn" id="vex-pp-clearall-${V}" type="button">${b}</button>
            </div>
            <div class="vex-pp-file-list" id="vex-pp-${V}-list"></div>
            <div class="vex-pp-pagination" id="vex-pp-${V}-pg"></div>`;const C=o("vex-pp-search-"+V);C&&C.addEventListener("input",U=>{V==="inv"?(x=U.target.value,c=50):(_=U.target.value,v=50),S(V)});const T=o("vex-pp-clearall-"+V);T&&T.addEventListener("click",()=>{V==="inv"?(y=[],x="",c=50):(i=[],_="",v=50),M()}),S(V)}function S(V){const Q=o("vex-pp-"+V+"-list"),ee=o("vex-pp-"+V+"-pg");if(!Q)return;const ne=V==="inv"?y:i,oe=V==="inv"?x:_,ue=V==="inv"?c:v,b=V==="inv"?K:G,C=ne.map((z,u)=>({f:z,i:u})),T=oe?C.filter(({f:z})=>z.name.toLowerCase().includes(oe.toLowerCase())):C,U=T.slice(0,ue);if(Q.innerHTML=U.map(({f:z,i:u})=>`
            <div class="vex-pp-file-row">
                ${b}
                <span class="vex-pp-fi-name" title="${p(z.name)}">${p(z.name)}</span>
                <span class="vex-pp-fi-size">${l(z.size)}</span>
                <button class="vex-pp-fi-del" type="button" data-kind="${V}" data-ridx="${u}" aria-label="remove">${W}</button>
            </div>`).join("")+`<div id="vex-pp-sentinel-${V}" style="height:1px;flex-shrink:0"></div>`,Q.querySelectorAll(".vex-pp-fi-del").forEach(z=>{z.addEventListener("click",()=>{const u=parseInt(z.dataset.ridx,10);z.dataset.kind==="inv"?$(u):E(u)})}),ee){const z=t("vex-preview-count")||"显示前 {n} / 共 {m}";ee.textContent=z.replace("{n}",U.length).replace("{m}",T.length)}w(V,T.length)}function w(V,Q){if((V==="inv"?c:v)>=Q)return;const ne=o("vex-pp-sentinel-"+V),oe=o("vex-pp-"+V+"-list");if(!ne||!oe)return;const ue=new IntersectionObserver(b=>{b[0].isIntersecting&&(ue.disconnect(),V==="inv"?c+=50:v+=50,S(V))},{root:oe,threshold:.8});ue.observe(ne)}function m(V,Q,ee,ne){const oe=o(V),ue=o(Q);!oe||!ue||(oe.addEventListener("click",()=>ue.click()),oe.addEventListener("keydown",b=>{(b.key==="Enter"||b.key===" ")&&(b.preventDefault(),ue.click())}),oe.addEventListener("dragover",b=>{b.preventDefault(),oe.classList.add("drag-over")}),oe.addEventListener("dragleave",()=>oe.classList.remove("drag-over")),oe.addEventListener("drop",b=>{b.preventDefault(),oe.classList.remove("drag-over");const T=Array.from(b.dataTransfer.files).filter(U=>a.test(U.name));if(!T.length){showToast(t("vex-toast-bad-ext"),"error");return}ee(T)}),ue.addEventListener("change",()=>{const b=Array.from(ue.files);ee(b),ue.value=""}))}async function H(){if(r||!y.length||!i.length)return;r=!0,o("vex-build").disabled=!0,o("vex-progress").style.display="flex";var V=document.getElementById("vex-download");V&&(V.style.display="none"),["vex-summary-collapse","vex-detail-collapse"].forEach(function(oe){var ue=document.getElementById(oe);ue&&(ue.style.display="none")});const Q=Date.now();o("vex-progress-title").textContent=t("vex-progress-running")||"AI 抽取中",o("vex-progress-sub").textContent=(t("vex-progress-sub")||"{a} 张发票 + {b} 份报告 · 并行处理").replace("{a}",y.length).replace("{b}",i.length);const ee=setInterval(()=>{const oe=Math.floor((Date.now()-Q)/1e3);o("vex-progress-sub").textContent=(t("vex-progress-elapsed")||"已 {s} 秒 · {a} 张发票 + {b} 份报告").replace("{s}",oe).replace("{a}",y.length).replace("{b}",i.length)},1e3);try{const oe=new FormData;for(const pe of y)oe.append("invoices",pe);for(const pe of i)oe.append("reports",pe);const ue=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";oe.append("lang",ue);const b=localStorage.getItem("mrpilot_token")||"",C=await fetch("/api/vat_excel/submit",{method:"POST",headers:s(),body:oe});let T=null;try{T=await C.json()}catch{T=null}if(!C.ok||!T||!T.ok||!T.job_id)throw clearInterval(ee),new Error(T&&T.detail||"HTTP "+C.status);const U=o("vex-progress-sub"),z=await window._reconPollJob(T.job_id,b,{onProgress:pe=>{U&&(U.textContent=window._reconProgressText(pe,ue))}});if(clearInterval(ee),!z||z.status!=="done"||!z.result_id)throw new Error(t("vex-toast-fail")||"生成失败");const u=z.result_id;let P=0;const O=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(u)+"/download",{headers:s()});if(!O.ok)throw new Error("HTTP "+O.status);const X=(O.headers.get("Content-Disposition")||"").match(/filename="([^"]+)"/),de=X&&X[1]||"vat_recon_"+Date.now()+".xlsx",se=await O.blob(),ce=URL.createObjectURL(se),ae=o("vex-download");ae.href=ce,ae.download=de;try{const pe=document.createElement("a");pe.href=ce,pe.download=de,document.body.appendChild(pe),pe.click(),setTimeout(()=>pe.remove(),100)}catch{}o("vex-progress").style.display="none";var ne=document.getElementById("vex-download");ne&&(ne.style.display=""),u&&(P=await Z(u)),window._onVexResultShown&&window._onVexResultShown(),P>0?showToast((t("vex-toast-some-fail")||"有 {n} 张发票 OCR 失败").replace("{n}",P),"warn"):showToast(t("vex-toast-done")||"Excel 已生成","success"),q(),setTimeout(j,800)}catch(oe){clearInterval(ee),o("vex-progress").style.display="none";const ue=(t("vex-toast-fail")||"生成失败")+": "+(oe.message||oe);showToast(ue,"error")}finally{r=!1,o("vex-build").disabled=!1}}function D(){y=[],i=[];var V=document.getElementById("vex-download");V&&(V.style.display="none"),M()}function J(V){if(V==null)return"—";var Q=parseFloat(V);return isNaN(Q)?"—":Q.toLocaleString("th-TH",{minimumFractionDigits:2,maximumFractionDigits:2})}async function Z(V){try{var Q=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(V),{headers:s()});if(!Q.ok)throw new Error(Q.status);var ee=await Q.json(),ne=ee.raw_data_json;if(typeof ne=="string")try{ne=JSON.parse(ne)}catch{ne={}}ne=ne||{};var oe=ne.rows||[],ue=[];oe.forEach(function(T){T.kind==="invoice_orphan"?ue.push({invoice_no:T.invoice_no||"",field:"仅发票有",report_value:"—",invoice_value:J(T.amount_inv),kind:T.kind}):T.kind==="report_orphan"?ue.push({invoice_no:T.invoice_no||"",field:"仅报告有",report_value:J(T.amount_rep),invoice_value:"—",kind:T.kind}):T.dims&&Object.keys(T.dims).length>0&&Object.keys(T.dims).forEach(function(U){var z=String(T.dims[U]||""),u=z.split(" ≠ ");ue.push({invoice_no:T.invoice_no||"",field:U,report_value:u[0]||z,invoice_value:u.length>1?u[1]:"—",kind:"diff"})})});var b=oe.filter(function(T){return T.kind==="matched_cash"}).length,C=Math.max(0,parseInt(ne.invoice_ocr_failed_count||0,10));return window._vexLastTask={total:ne.n_total||0,matched:ne.n_ok||0,diff:ne.n_diff||0,incomplete:C,cash:b,diff_rows:ue,task_id:V},window._fillVexSummary&&window._fillVexSummary(),window._fillVexDetail&&window._fillVexDetail(),C}catch{return 0}}function le(){const V=document.getElementById("vex-pane");V&&V.querySelectorAll("[data-i18n]").forEach(Q=>{const ee=t(Q.dataset.i18n);ee&&(Q.textContent=ee)}),M(),j()}function ie(){m("vex-drop-invoice","vex-input-invoice",I),m("vex-drop-report","vex-input-report",L);const V=o("vex-build"),Q=o("vex-reset");V&&V.addEventListener("click",H),Q&&Q.addEventListener("click",D),document.querySelectorAll('[data-recon-tab="sale-vat"]').forEach(oe=>{oe.addEventListener("click",()=>{q(),j()})}),g();const ee=document.getElementById("vex-task-search");ee&&ee.addEventListener("input",N);const ne=document.getElementById("vex-toggle-preview");ne&&ne.addEventListener("click",()=>{const oe=o("vex-preview-panel"),ue=o("vex-toggle-preview-label"),b=oe&&oe.style.display!=="none";oe&&(oe.style.display=b?"none":""),ne&&ne.classList.toggle("open",!b),ue&&(ue.textContent=b?t("vex-toggle-preview-open")||"查看清单":t("vex-toggle-preview-close")||"收起清单"),b||te()}),M(),q()}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",ie):ie(),typeof window.subscribeI18n=="function"&&(window.subscribeI18n("vex-excel",le),window.subscribeI18n("vex-preview-panel",te))})();(function(){const e=w=>document.getElementById(w),n=()=>localStorage.getItem("mrpilot_token")||"",a=()=>typeof window.currentLang=="string"&&window.currentLang?window.currentLang:localStorage.getItem("mrpilot_lang")||"th",o=()=>({Authorization:"Bearer "+n()}),s={inited:!1,glFile:[],vatFile:[],running:!1,currentTaskId:null,lastDetail:[],lastSummary:null},p={th:{not_found:"ไม่พบข้อมูล",running:"กำลังกระทบยอด…",error:"เกิดข้อผิดพลาด",need_files:"กรุณาเลือกไฟล์ทั้งสอง",done:"เสร็จสิ้น",hint_need_both:"อัปโหลด ① รายงานภาษีขาย + ② GL",hint_need_one_more:"อัปโหลดอีก 1 ไฟล์",hint_ready:"พร้อมแล้ว · กดเริ่มกระทบยอด",hist_load:"โหลด",hist_export:"ส่งออก",hist_delete:"ลบ",confirm_delete:"ยืนยันการลบงานนี้?",s_gl_total:"ยอดรวมตามบัญชีแยกประเภท",s_minus_gl_cr:"หัก : รายการเครดิตที่ไม่มีในรายงานภาษีขาย",s_plus_gl_dr:"บวก : รายการเดบิตที่ไม่มีในรายงานภาษีขาย",s_plus_vat_p:"บวก : รายการยอดขายที่ไม่มีในบัญชีแยกประเภท",s_minus_vat_n:"หัก : รายการลดหนี้ที่ไม่มีในบัญชีแยกประเภท",s_vat_total:"ยอดรวมตามรายงานภาษีขาย"},zh:{not_found:"未找到数据",running:"正在对账中...",error:"出错了",need_files:"请先选择两个文件",done:"完成",hint_need_both:"请上传① 销项税报告 + ② 总账 GL",hint_need_one_more:"还需上传 1 份文件",hint_ready:"已就绪 · 点击开始对账",hist_load:"加载",hist_export:"导出",hist_delete:"删除",confirm_delete:"确认删除此任务？",s_gl_total:"总账金额合计",s_minus_gl_cr:"减：销项税报告中未列的贷方记录",s_plus_gl_dr:"加：销项税报告中未列的借方记录",s_plus_vat_p:"加：总账中未列的销售记录",s_minus_vat_n:"减：总账中未列的贷项凭单(credit note)记录",s_vat_total:"销项税报告金额合计"},en:{not_found:"Not found",running:"Reconciling...",error:"Error",need_files:"Please select both files",done:"Done",hint_need_both:"Upload ① Output VAT report + ② GL file",hint_need_one_more:"1 more file required",hint_ready:"Ready · click Run to start",hist_load:"Load",hist_export:"Export",hist_delete:"Delete",confirm_delete:"Delete this task?",s_gl_total:"Total per General Ledger",s_minus_gl_cr:"Less: GL credits not in VAT Report",s_plus_gl_dr:"Add: GL debits not in VAT Report",s_plus_vat_p:"Add: Sales in VAT Report not in GL",s_minus_vat_n:"Less: Credit notes in VAT Report not in GL",s_vat_total:"Total per VAT Sales Report"},ja:{not_found:"データなし",running:"照合中…",error:"エラー",need_files:"両方のファイルを選択してください",done:"完了",hint_need_both:"① 売上税報告 + ② GL をアップロード",hint_need_one_more:"あと 1 ファイル必要",hint_ready:"準備完了 · 「開始」をクリック",hist_load:"読込",hist_export:"出力",hist_delete:"削除",confirm_delete:"このタスクを削除しますか?",s_gl_total:"総勘定元帳合計",s_minus_gl_cr:"減：売上税報告にないGL貸方記録",s_plus_gl_dr:"加：売上税報告にないGL借方記録",s_plus_vat_p:"加：GLにない売上記録",s_minus_vat_n:"減：GLにない赤伝記録",s_vat_total:"売上税報告合計"}},l=w=>(p[a()]||p.th)[w]||w;function y(w){const m=a(),D={gl_no_revenue_rows:{zh:"GL 中未找到收入科目行。请确认「收入科目前缀」是否正确(收入科目通常以 4 开头),改对后重试。",th:"ไม่พบรายการบัญชีรายได้ใน GL · ตรวจสอบ «คำนำหน้าบัญชีรายได้» (รายได้มักขึ้นต้นด้วย 4) แล้วลองใหม่",en:"No revenue-account rows found in the GL. Check the “revenue account prefix” (revenue usually starts with 4) and retry.",ja:"GL に収益科目の行が見つかりません。「収益科目プレフィックス」(通常 4 で始まる)を確認して再試行してください。"},gl_parse_failed:{zh:"GL 文件解析失败。请确认文件含日期/科目/借贷列,或换清晰的 Excel/CSV 重传。",th:"อ่านไฟล์ GL ไม่สำเร็จ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต-เครดิต หรืออัปโหลด Excel/CSV ที่ชัดเจน",en:"Failed to parse the GL file. Ensure it has date/account/debit-credit columns, or re-upload a clean Excel/CSV.",ja:"GL ファイルの解析に失敗しました。日付/科目/借方貸方列を確認するか、Excel/CSV を再アップロードしてください。"},vat_no_rows:{zh:"销项税报告里没有可对账的数据行。请确认上传了正确的销项税报告。",th:"ไม่พบแถวข้อมูลในรายงานภาษีขาย · ตรวจสอบว่าอัปโหลดรายงานที่ถูกต้อง",en:"No rows found in the sales-VAT report. Please check you uploaded the correct report.",ja:"売上VATレポートに行が見つかりません。正しいレポートをアップロードしたか確認してください。"},vat_parse_failed:{zh:"销项税报告解析失败。请换更清晰的版本,或转成 Excel/PDF 重传。",th:"อ่านรายงานภาษีขายไม่สำเร็จ · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น Excel/PDF",en:"Failed to parse the sales-VAT report. Try a clearer version, or convert to Excel/PDF.",ja:"売上VATレポートの解析に失敗しました。より鮮明な版か、Excel/PDF に変換してください。"}}[w];return D?D[m]||D.th||D.en:l("error")||"Error"}const i=w=>w==null||isNaN(w)?"":Number(w).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});function r(w,m,H,D){const J=e(w),Z=e(m),le=e(H);if(!J||!Z||!le)return;const ie=V=>{if(!V||!V.length)return;const Q=Array.isArray(s[D])?s[D].slice():[],ee=new Set(Q.map(ne=>ne.name+"|"+ne.size));for(const ne of V){if(!ne)continue;const oe=ne.name+"|"+ne.size;ee.has(oe)||(Q.push(ne),ee.add(oe))}s[D]=Q,d(le,Q),v(),x(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()};J.addEventListener("click",()=>Z.click()),J.addEventListener("keydown",V=>{(V.key==="Enter"||V.key===" ")&&(V.preventDefault(),Z.click())}),Z.addEventListener("change",()=>{ie(Array.from(Z.files||[])),Z.value=""}),J.addEventListener("dragover",V=>{V.preventDefault(),J.classList.add("drag-over")}),J.addEventListener("dragleave",()=>J.classList.remove("drag-over")),J.addEventListener("drop",V=>{V.preventDefault(),J.classList.remove("drag-over");const Q=V.dataTransfer&&V.dataTransfer.files?Array.from(V.dataTransfer.files):[];ie(Q)})}function d(w,m){if(!w)return;if(!m||m.length===0){w.textContent="";return}const H=m.reduce((D,J)=>D+Math.round(J.size/1024),0);if(m.length===1)w.textContent=m[0].name+"  ("+H+" KB)";else{const D=window.t&&window.t("glv-files-count")||"{n} 个文件";w.textContent=D.replace("{n}",m.length)+"  ("+H+" KB)"}}function c(w){const m=s[w];return Array.isArray(m)?m:m?[m]:[]}function v(){const w=e("btn-glv-run");if(!w)return;const m=c("glFile").length>0&&c("vatFile").length>0;w.disabled=!m||s.running}function x(){const w=e("glv-status");if(!w||s.running)return;const m=c("vatFile").length,H=c("glFile").length;m===0&&H===0?(w.className="vex-action-info muted",w.innerHTML="<span>"+l("hint_need_both")+"</span>"):m>0&&H>0?(w.className="vex-action-info ok",w.innerHTML="<span>"+l("hint_ready")+"</span>"):(w.className="vex-action-info muted",w.innerHTML="<span>"+l("hint_need_one_more")+"</span>")}function _(w,m){const H=w==="vat"?"vatFile":"glFile",D=w==="vat"?"glv-vat-input":"glv-gl-input",J=w==="vat"?"glv-vat-name":"glv-gl-name",Z=c(H);m==null?s[H]=[]:s[H]=Z.filter((ie,V)=>V!==m);const le=e(D);le&&(le.value=""),d(e(J),c(H)),v(),x(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}window._glvRemoveFile=_;function q(){s.glFile=[],s.vatFile=[],s.currentTaskId=null,s.lastDetail=[],s.lastSummary=null;const w=e("glv-vat-input");w&&(w.value="");const m=e("glv-gl-input");m&&(m.value="");const H=e("glv-vat-name");H&&(H.textContent="");const D=e("glv-gl-name");D&&(D.textContent="");const J=e("glv-result");J&&(J.style.display="none");const Z=e("glv-kpi-strip");Z&&(Z.style.display="none"),v(),x(),window._glvClearPreviewSearch&&window._glvClearPreviewSearch(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}function j(w){const m=e("glv-tbody");if(!m)return;re(w.length),m.innerHTML="";const H=l("not_found"),D=document.createDocumentFragment();w.forEach(J=>{const Z=document.createElement("tr"),le=(ne,oe)=>{const ue=document.createElement("td");return oe&&(ue.className=oe),ue.textContent=ne,ue},ie=J.gl_amount===null||J.gl_amount===void 0,V=J.diff;let Q="glv-num",ee="glv-num";ie?(ee+=" glv-cell-missing",Q+=" glv-cell-missing"):Math.abs(V||0)<.005?Q+=" glv-cell-ok":Q+=" glv-cell-diff",Z.appendChild(le(J.doc_no||"","glv-doc")),Z.appendChild(le(J.date||"","")),Z.appendChild(le(J.customer_name||"","")),Z.appendChild(le(i(J.vat_amount),"glv-num")),Z.appendChild(le(ie?H:i(J.gl_amount),ee)),Z.appendChild(le(ie?H:i(J.diff),Q)),Z.appendChild(le(J.account_codes||"","glv-doc")),D.appendChild(Z)}),m.appendChild(D)}function k(w){const m=e("glv-summary-table")&&e("glv-summary-table").querySelector("tbody");if(!m)return;m.innerHTML="",[{label:l("s_gl_total"),amount:w.gl_total,emph:!0,items:[],negate:!1},{label:l("s_minus_gl_cr"),amount:-(w.gl_only_credit||0),emph:!1,items:w.gl_only_credit_items||[],negate:!0},{label:l("s_plus_gl_dr"),amount:w.gl_only_debit||0,emph:!1,items:w.gl_only_debit_items||[],negate:!1},{label:l("s_plus_vat_p"),amount:w.vat_only_positive||0,emph:!1,items:w.vat_only_positive_items||[],negate:!1},{label:l("s_minus_vat_n"),amount:w.vat_only_negative||0,emph:!1,items:w.vat_only_negative_items||[],negate:!1},{label:l("s_vat_total"),amount:w.vat_total,emph:!0,items:[],negate:!1}].forEach(({label:D,amount:J,emph:Z,items:le,negate:ie})=>{const V=document.createElement("tr");V.className=Z?"glv-summary-total":"glv-summary-sect";const Q=document.createElement("td"),ee=document.createElement("td");Q.textContent=D,ee.textContent=Z?i(J):"",V.appendChild(Q),V.appendChild(ee),m.appendChild(V),(le||[]).forEach(ne=>{const oe=document.createElement("tr");oe.className="glv-summary-item";const ue=document.createElement("td"),b=document.createElement("td"),C=[ne.doc_no,ne.date,ne.name].filter(Boolean);ue.textContent="· "+C.join("  ·  ");const T=ie?-(ne.amount||0):ne.amount||0;b.textContent=i(T),oe.appendChild(ue),oe.appendChild(b),m.appendChild(oe)})})}function B(w){e("glv-kpi-matched")&&(e("glv-kpi-matched").textContent=w&&w.matched!=null?w.matched:"—"),e("glv-kpi-diff")&&(e("glv-kpi-diff").textContent=w&&w.diff!=null?w.diff:"—"),e("glv-kpi-unmatched")&&(e("glv-kpi-unmatched").textContent=w&&w.unmatched!=null?w.unmatched:"—")}function N(w){if(!w)return"";try{const m=new Date(w);if(isNaN(m.getTime()))return w;const H=D=>String(D).padStart(2,"0");return m.getFullYear()+"-"+H(m.getMonth()+1)+"-"+H(m.getDate())+" "+H(m.getHours())+":"+H(m.getMinutes())}catch{return w}}const R=10;var F=[],A=1;function g(){A=1,f();var w=((e("glv-hist-search")||{}).value||"").trim().toLowerCase();if(w){var m=e("glv-history-tbody");m&&m.querySelectorAll("tr").forEach(function(H){H.dataset.taskId&&(H.style.display=H.textContent.toLowerCase().indexOf(w)>=0?"":"none")})}}function f(){const w=e("glv-history-table-wrap"),m=e("glv-history-empty"),H=e("glv-history-tbody"),D=e("glv-history-pager"),J=e("glv-history-pager-info"),Z=e("glv-history-prev"),le=e("glv-history-next");if(!H)return;if(H.innerHTML="",!F.length){w&&(w.style.display="none"),m&&(m.style.display=""),D&&(D.style.display="none");return}w&&(w.style.display=""),m&&(m.style.display="none");const ie=Math.ceil(F.length/R);A>ie&&(A=ie);const V=(A-1)*R,Q=F.slice(V,V+R);D&&(D.style.display=F.length>R?"":"none",J&&(J.textContent=A+" / "+ie),Z&&(Z.disabled=A<=1),le&&(le.disabled=A>=ie)),Q.forEach(ne=>{const oe=document.createElement("tr");oe.dataset.taskId=ne.id;const ue=document.createElement("td");ue.textContent=N(ne.created_at);const b=document.createElement("td");b.className="glv-history-file",b.title=(ne.vat_filename||"")+" + "+(ne.gl_filename||""),b.textContent=(ne.vat_filename||"?")+" + "+(ne.gl_filename||"?");const C=document.createElement("td");C.className="glv-num",C.textContent=(ne.vat_row_count||0)+" / "+(ne.gl_row_count||0);const T=document.createElement("td");T.className="glv-num",T.textContent=ne.matched_count||0;const U=document.createElement("td");U.className="glv-num",U.textContent=ne.diff_count||0;const z=document.createElement("td");z.className="glv-num",z.textContent=ne.unmatched_count||0;const u=document.createElement("td");u.className="glv-history-actions";const P=(de,se,ce,ae)=>{const pe=document.createElement("button");return pe.type="button",ce&&(pe.className=ce),pe.title=se,pe.setAttribute("aria-label",se),pe.innerHTML=de,pe.onclick=ae,pe},O='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 8a6 6 0 1 0 12 0A6 6 0 0 0 2 8z"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',Y='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',X='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';u.appendChild(P(O,l("hist_load"),"",()=>L(ne.id))),u.appendChild(P(Y,l("hist_export"),"",()=>$(ne.id))),u.appendChild(P(X,l("hist_delete"),"glv-del",()=>E(ne.id))),[ue,b,C,T,U,z,u].forEach(de=>oe.appendChild(de)),H.appendChild(oe)})}function h(){var w=e("glv-history-prev"),m=e("glv-history-next");w&&!w._glvBound&&(w._glvBound=!0,w.addEventListener("click",function(){A>1&&(A--,f())})),m&&!m._glvBound&&(m._glvBound=!0,m.addEventListener("click",function(){var H=Math.ceil(F.length/R);A<H&&(A++,f())}))}async function I(){try{const m=await(await fetch("/api/recon/gl-vat/tasks",{headers:o()})).json();F=m&&m.tasks||[],A=1,f(),h()}catch(w){console.error("[gl-vat] history load failed:",w)}}async function L(w){try{const H=await(await fetch("/api/recon/gl-vat/"+w,{headers:o()})).json();if(!H||!H.ok)throw new Error("load_failed");s.currentTaskId=w,s.lastDetail=H.detail||[],s.lastSummary=H.summary||{},B(H.stats||{}),j(s.lastDetail),k(s.lastSummary);const D=e("glv-result");D&&(D.style.display=""),W(),window.scrollTo({top:D?D.offsetTop-80:0,behavior:"smooth"})}catch(m){console.error("[gl-vat] load task failed:",m),alert(l("error")+": "+(m.message||m))}}async function $(w){try{const m="/api/recon/gl-vat/"+w+"/export?lang="+encodeURIComponent(a()),H=await fetch(m,{headers:o()});if(!H.ok)throw new Error("HTTP "+H.status);const D=await H.blob(),J=document.createElement("a");J.href=URL.createObjectURL(D),J.download="GL_VAT_recon_"+w+".xlsx",document.body.appendChild(J),J.click(),setTimeout(()=>{URL.revokeObjectURL(J.href),J.remove()},200)}catch(m){console.error("[gl-vat] exportTask failed:",m),typeof showToast=="function"&&showToast(l("error")+": "+(m.message||m),"error")}}async function E(w){let m;if(typeof window.showConfirm=="function"?m=await window.showConfirm(l("confirm_delete"),{danger:!0}):m=confirm(l("confirm_delete")),!!m)try{const H=await fetch("/api/recon/gl-vat/"+w,{method:"DELETE",headers:o()});if(!H.ok)throw new Error("HTTP "+H.status);I()}catch(H){console.error("[gl-vat] delete failed:",H),typeof showToast=="function"&&showToast(l("error")+": "+(H.message||H),"error")}}async function M(){if(!s.glFile||!s.vatFile){typeof showToast=="function"&&showToast(l("need_files"),"warn");return}s.running=!0,v();const w=e("glv-status"),m=e("glv-progress"),H=e("glv-progress-sub");w&&(w.className="vex-action-info muted",w.style.color="",w.innerHTML="<span>"+l("running")+"</span>"),m&&(m.style.display=""),H&&(H.textContent=(s.vatFile.name||"VAT")+" + "+(s.glFile.name||"GL"));const D=new FormData,J=c("vatFile"),Z=c("glFile");for(const ie of J)D.append("vat_files",ie,ie.name);for(const ie of Z)D.append("gl_files",ie,ie.name);const le=(e("glv-prefix")&&e("glv-prefix").value||"4").trim()||"4";D.append("revenue_prefix",le),D.append("lang",a());try{const ie=await fetch("/api/recon/gl-vat/submit",{method:"POST",headers:o(),body:D});let V=null;try{V=await ie.json()}catch{V=null}if(!ie.ok||!V||!V.ok||!V.job_id)throw new Error(V&&V.detail||V&&V.error||"HTTP "+ie.status);const Q=e("glv-progress-sub"),ee=await window._reconPollJob(V.job_id,n(),{onProgress:b=>{Q&&(Q.textContent=window._reconProgressText(b,a()))}});if(!ee||ee.status!=="done"||!ee.result_id)throw ee&&ee.status==="failed"&&ee.error_code?new Error(y(ee.error_code)):new Error(l("error")||"Error");const ne=await fetch("/api/recon/gl-vat/"+encodeURIComponent(ee.result_id),{headers:o()});let oe=null;try{oe=await ne.json()}catch{oe=null}if(!ne.ok||!oe||!oe.ok)throw new Error(oe&&oe.detail||oe&&oe.error||"HTTP "+ne.status);s.currentTaskId=oe.task_id,s.lastDetail=oe.detail||[],s.lastSummary=oe.summary||{},B(oe.stats||{}),j(s.lastDetail),k(s.lastSummary);const ue=e("glv-result");ue&&(ue.style.display=""),W(),w&&(w.className="vex-action-info ok",w.style.color="",w.innerHTML="<span>"+l("done")+" · GL "+(oe.gl_row_count||0)+" · VAT "+(oe.vat_row_count||0)+"</span>"),I()}catch(ie){console.error("[gl-vat] run failed:",ie),w&&(w.className="vex-action-info",w.style.color="#ef4444",w.innerHTML="<span>"+l("error")+": "+(ie.message||ie)+"</span>")}finally{s.running=!1,m&&(m.style.display="none"),v()}}async function K(){if(s.currentTaskId)try{const w="/api/recon/gl-vat/"+s.currentTaskId+"/export?lang="+encodeURIComponent(a()),m=await fetch(w,{headers:o()});if(!m.ok)throw new Error("HTTP "+m.status);const H=await m.blob(),D=document.createElement("a");D.href=URL.createObjectURL(H),D.download="GL_VAT_recon_"+s.currentTaskId+".xlsx",document.body.appendChild(D),D.click(),setTimeout(()=>{URL.revokeObjectURL(D.href),D.remove()},200)}catch(w){console.error("[gl-vat] export failed:",w),typeof showToast=="function"&&showToast(l("error")+": "+(w.message||w),"error")}}function G(){s.running||x(),I(),s.lastDetail&&s.lastDetail.length&&j(s.lastDetail),s.lastSummary&&k(s.lastSummary)}function W(){var w=e("glv-kpi-strip");w&&(w.style.display="");var m=e("glv-section-summary");m&&m.setAttribute("data-collapsed","false");var H=e("glv-section-detail");H&&H.setAttribute("data-collapsed","false")}function te(){document.querySelectorAll(".glv-section-head[data-toggle]").forEach(w=>{const m=w.getAttribute("data-toggle"),H=document.getElementById(m);if(!H)return;const D=J=>{if(J.target&&J.target.closest("button")!==null&&!J.target.classList.contains("glv-section-head"))return;const Z=H.getAttribute("data-collapsed")==="true";H.setAttribute("data-collapsed",Z?"false":"true")};w.addEventListener("click",D),w.addEventListener("keydown",J=>{(J.key==="Enter"||J.key===" ")&&(J.preventDefault(),D(J))})})}function re(w){const m=e("glv-detail-count");m&&(m.textContent=w!=null?String(w):"")}function S(){if(s.inited){I();return}s.inited=!0,r("glv-drop-gl","glv-gl-input","glv-gl-name","glFile"),r("glv-drop-vat","glv-vat-input","glv-vat-name","vatFile");const w=e("btn-glv-run");w&&w.addEventListener("click",M);const m=e("btn-glv-export");m&&m.addEventListener("click",K);const H=e("btn-glv-reset");H&&H.addEventListener("click",q);const D=e("glv-hist-search");D&&D.addEventListener("input",g),te(),B(null),x(),window._loadGlvHistory=I,I(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("gl-vat-recon",G)}window.GlVatRecon={ensureInit:S},window._glvPreviewFiles=function(w){return c(w==="vat"?"vatFile":"glFile")}})();(function(){const e=["flowaccount","peak","xero","quickbooks","express"],n={flowaccount:"FlowAccount",peak:"PEAK",xero:"Xero",quickbooks:"QuickBooks",express:"Express"},a=["expense_office","expense_travel","expense_utility","asset_inventory","asset_fixed","liability_ap","revenue_sales","revenue_service","other"],o=["vat_7","vat_0","vat_exempt","wht_1","wht_3","wht_5","non_vat"],s="468b50c1-5593-4fd6-990d-515ce8085563";let p={sub:"clients",loaded:{clients:!1,accounts:!1,taxes:!1,products:!1},items:{clients:[],accounts:[],taxes:[],products:[]},clientList:[],clientLoaded:!1,addingNew:{clients:!1,accounts:!1,taxes:!1,products:!1},bound:!1};function l(){const L=typeof _userInfo<"u"?_userInfo:null;return!!(L&&(L.role==="owner"||L.is_super_admin))}function y(){const L=typeof _userInfo<"u"?_userInfo:null;return!!(L&&L.id===s)}function i(L){return typeof escapeHtml=="function"?escapeHtml(L==null?"":String(L)):String(L??"")}function r(L,$){try{typeof showToast=="function"&&showToast(L,$||"info")}catch{}}async function d(L,$){const E=localStorage.getItem("mrpilot_token");if(E&&!(p.loaded[L]&&!$))try{const M=await fetch("/api/erp/mappings/"+L,{headers:{Authorization:"Bearer "+E}});if(!M.ok)throw new Error("http_"+M.status);const K=await M.json();p.items[L]=K.items||[],p.loaded[L]=!0}catch{p.items[L]=[],p.loaded[L]=!1}}async function c(L){if(p.clientLoaded)return;const $=localStorage.getItem("mrpilot_token");if($)try{const E=await fetch("/api/clients?include_inactive=false",{headers:{Authorization:"Bearer "+$}});if(!E.ok)throw new Error("http_"+E.status);const M=await E.json();p.clientList=(M.clients||M.items||[]).filter(K=>K.is_active!==!1),p.clientLoaded=!0}catch{p.clientList=[]}}function v(){const L=document.getElementById("erp-map-pane-wrap");if(!L)return;const $=!l();let E="";$&&(E+='<div class="erp-map-readonly-banner"><svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="8"/><path d="M10 6v4M10 13v0.01"/></svg>'+i(t("erp-map-readonly-tip"))+"</div>"),E+='<div class="erp-map-toolbar">',!$&&p.sub!=="products"&&(E+='<button class="btn btn-primary" type="button" id="erp-map-add-btn" data-i18n="erp-map-add-row">'+i(t("erp-map-add-row"))+"</button>"),E+="</div>",E+='<div class="erp-map-table" id="erp-map-table-host"></div>',L.innerHTML=E,x();const M=document.getElementById("erp-map-dev-bar");M&&(M.style.display=l()&&y()?"":"none")}function x(){const L=document.getElementById("erp-map-table-host");if(!L)return;const $=p.sub,E=p.items[$]||[],M=p.addingNew[$],K=!l();if(!E.length&&!M){L.innerHTML='<div class="erp-map-empty"><strong>'+i(t("erp-map-empty-"+$))+"</strong>"+i(t("erp-map-empty-"+$+"-sub"))+"</div>";return}let G="";G+=_($),M&&!K&&(G+=N($)),E.forEach(function(W){G+=R($,W,K)}),L.innerHTML=G}function _(L){return L==="clients"?'<div class="erp-map-row erp-map-head row-clients"><div>'+i(t("erp-map-col-client"))+"</div><div>"+i(t("erp-map-col-erp"))+"</div><div>"+i(t("erp-map-col-erp-code"))+"</div><div>"+i(t("erp-map-col-notes"))+"</div><div>"+i(t("erp-map-col-actions"))+"</div></div>":L==="accounts"?'<div class="erp-map-row erp-map-head row-accounts"><div>'+i(t("erp-map-col-erp"))+"</div><div>"+i(t("erp-map-col-category"))+"</div><div>"+i(t("erp-map-col-erp-code"))+"</div><div>"+i(t("erp-map-col-erp-name"))+"</div><div>"+i(t("erp-map-col-notes"))+"</div><div>"+i(t("erp-map-col-actions"))+"</div></div>":L==="products"?'<div class="erp-map-row erp-map-head row-products"><div>'+i(t("erp-map-col-item-name"))+"</div><div>"+i(t("erp-map-col-erp-product-code"))+"</div><div>"+i(t("erp-map-col-erp-name"))+"</div><div>"+i(t("erp-map-col-notes"))+"</div><div>"+i(t("erp-map-col-actions"))+"</div></div>":'<div class="erp-map-row erp-map-head row-taxes"><div>'+i(t("erp-map-col-erp"))+"</div><div>"+i(t("erp-map-col-tax"))+"</div><div>"+i(t("erp-map-col-erp-tax-code"))+"</div><div>"+i(t("erp-map-col-notes"))+"</div><div>"+i(t("erp-map-col-actions"))+"</div></div>"}function q(L,$){let E='<select class="form-input" data-erp-field="'+$+'">';return E+='<option value="">'+i(t("erp-map-pick-erp"))+"</option>",e.forEach(function(M){const K=M===L?" selected":"";E+='<option value="'+M+'"'+K+">"+i(n[M])+"</option>"}),E+="</select>",E}function j(L){let $='<select class="form-input" data-erp-field="client_id">';return $+='<option value="">'+i(t("erp-map-pick-client"))+"</option>",(p.clientList||[]).forEach(function(E){const M=String(E.id)===String(L)?" selected":"";$+='<option value="'+E.id+'"'+M+">"+i(E.name||"#"+E.id)+"</option>"}),$+="</select>",$}function k(L){let $='<select class="form-input" data-erp-field="pearnly_category">';return $+='<option value="">'+i(t("erp-map-pick-cat"))+"</option>",a.forEach(function(E){const M=E===L?" selected":"";$+='<option value="'+E+'"'+M+">"+i(t("erp-map-cat-"+E))+"</option>"}),$+="</select>",$}function B(L){let $='<select class="form-input" data-erp-field="pearnly_tax_kind">';return $+='<option value="">'+i(t("erp-map-pick-tax"))+"</option>",o.forEach(function(E){const M=E===L?" selected":"";$+='<option value="'+E+'"'+M+">"+i(t("erp-map-tax-"+E))+"</option>"}),$+="</select>",$}function N(L){const $='<button class="btn btn-primary" type="button" data-erp-save="new" style="padding:6px 12px;height:32px;">'+i(t("erp-map-save"))+"</button>";return L==="clients"?'<div class="erp-map-row erp-map-row-add row-clients" data-erp-row="new"><div data-label="'+i(t("erp-map-col-client"))+'">'+j("")+'</div><div data-label="'+i(t("erp-map-col-erp"))+'">'+q("","erp_type")+'</div><div data-label="'+i(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+i(t("erp-map-ph-erp-code"))+'"></div><div data-label="'+i(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+i(t("erp-map-ph-notes"))+'"></div><div>'+$+"</div></div>":L==="accounts"?'<div class="erp-map-row erp-map-row-add row-accounts" data-erp-row="new"><div data-label="'+i(t("erp-map-col-erp"))+'">'+q("","erp_type")+'</div><div data-label="'+i(t("erp-map-col-category"))+'">'+k("")+'</div><div data-label="'+i(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+i(t("erp-map-ph-acc-code"))+'"></div><div data-label="'+i(t("erp-map-col-erp-name"))+'"><input type="text" class="form-input" data-erp-field="erp_name" placeholder="'+i(t("erp-map-ph-acc-name"))+'"></div><div data-label="'+i(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+i(t("erp-map-ph-notes"))+'"></div><div>'+$+"</div></div>":'<div class="erp-map-row erp-map-row-add row-taxes" data-erp-row="new"><div data-label="'+i(t("erp-map-col-erp"))+'">'+q("","erp_type")+'</div><div data-label="'+i(t("erp-map-col-tax"))+'">'+B("")+'</div><div data-label="'+i(t("erp-map-col-erp-tax-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+i(t("erp-map-ph-tax-code"))+'"></div><div data-label="'+i(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+i(t("erp-map-ph-notes"))+'"></div><div>'+$+"</div></div>"}function R(L,$,E){const M=E?"":'<button class="erp-map-del-btn" type="button" data-erp-del="'+i($.id)+'" title="'+i(t("erp-map-delete"))+'"><svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h12M8 6V4h4v2M6 6l1 11h6l1-11"/></svg></button>',K='<span class="erp-map-erp-badge">'+i(n[$.erp_type]||$.erp_type)+"</span>";if(L==="clients")return'<div class="erp-map-row row-clients"><div data-label="'+i(t("erp-map-col-client"))+'" class="erp-map-cell-name">'+i($.client_name||"#"+$.client_id)+'</div><div data-label="'+i(t("erp-map-col-erp"))+'">'+K+'</div><div data-label="'+i(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+i($.erp_code||"")+'</div><div data-label="'+i(t("erp-map-col-notes"))+'">'+i($.notes||"")+"</div><div>"+M+"</div></div>";if(L==="accounts"){const W=t("erp-map-cat-"+($.pearnly_category||"other"))||$.pearnly_category;return'<div class="erp-map-row row-accounts"><div data-label="'+i(t("erp-map-col-erp"))+'">'+K+'</div><div data-label="'+i(t("erp-map-col-category"))+'" class="erp-map-cell-name">'+i(W)+'</div><div data-label="'+i(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+i($.erp_code||"")+'</div><div data-label="'+i(t("erp-map-col-erp-name"))+'">'+i($.erp_name||"")+'</div><div data-label="'+i(t("erp-map-col-notes"))+'">'+i($.notes||"")+"</div><div>"+M+"</div></div>"}if(L==="products")return'<div class="erp-map-row row-products"><div data-label="'+i(t("erp-map-col-item-name"))+'" class="erp-map-cell-name">'+i($.item_name||"")+'</div><div data-label="'+i(t("erp-map-col-erp-product-code"))+'" class="erp-map-code">'+i($.erp_code||"")+'</div><div data-label="'+i(t("erp-map-col-erp-name"))+'">'+i($.erp_name||"")+'</div><div data-label="'+i(t("erp-map-col-notes"))+'">'+i($.notes||"")+"</div><div>"+M+"</div></div>";const G=t("erp-map-tax-"+($.pearnly_tax_kind||""))||$.pearnly_tax_kind;return'<div class="erp-map-row row-taxes"><div data-label="'+i(t("erp-map-col-erp"))+'">'+K+'</div><div data-label="'+i(t("erp-map-col-tax"))+'" class="erp-map-cell-name"><span class="erp-map-tax-badge">'+i(G)+'</span></div><div data-label="'+i(t("erp-map-col-erp-tax-code"))+'" class="erp-map-code">'+i($.erp_code||"")+'</div><div data-label="'+i(t("erp-map-col-notes"))+'">'+i($.notes||"")+"</div><div>"+M+"</div></div>"}async function F(L){const $=p.sub,E={};L.querySelectorAll("[data-erp-field]").forEach(function(W){E[W.dataset.erpField]=(W.value||"").trim()});const M=localStorage.getItem("mrpilot_token");if(!M)return;let K={},G="/api/erp/mappings/"+$;if($==="clients"){if(!E.client_id||!E.erp_type||!E.erp_code){r(t("erp-map-save-fail"),"error");return}K={client_id:parseInt(E.client_id,10),erp_type:E.erp_type,erp_code:E.erp_code,notes:E.notes||""}}else if($==="accounts"){if(!E.erp_type||!E.pearnly_category||!E.erp_code){r(t("erp-map-save-fail"),"error");return}K={erp_type:E.erp_type,pearnly_category:E.pearnly_category,erp_code:E.erp_code,erp_name:E.erp_name||"",notes:E.notes||""}}else{if(!E.erp_type||!E.pearnly_tax_kind||!E.erp_code){r(t("erp-map-save-fail"),"error");return}K={erp_type:E.erp_type,pearnly_tax_kind:E.pearnly_tax_kind,erp_code:E.erp_code,notes:E.notes||""}}try{const W=await fetch(G,{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+M},body:JSON.stringify(K)});if(!W.ok)throw new Error("http_"+W.status);p.addingNew[$]=!1,await d($,!0),x(),r(t("erp-map-saved-toast"),"success")}catch{r(t("erp-map-save-fail"),"error")}}async function A(L){if(!await window.pearnlyConfirm(t("erp-map-confirm-delete")))return;const E=p.sub,M=localStorage.getItem("mrpilot_token");try{const K=await fetch("/api/erp/mappings/"+E+"/"+encodeURIComponent(L),{method:"DELETE",headers:{Authorization:"Bearer "+M}});if(!K.ok)throw new Error("http_"+K.status);await d(E,!0),x(),r(t("erp-map-deleted-toast"),"success")}catch{r(t("erp-map-delete-fail"),"error")}}async function g(){await c(),await d(p.sub,!1),v()}function f(L){L!==p.sub&&(p.sub=L,p.addingNew[L]=!1,["clients","accounts","taxes","products"].forEach(function($){$!==L&&(p.addingNew[$]=!1)}),document.querySelectorAll(".erp-map-subtab").forEach(function($){$.classList.toggle("active",$.dataset.erpSubtab===L)}),d(L,!1).then(function(){v()}))}function h(){p.bound||(p.bound=!0,document.addEventListener("click",function(L){const $=L.target.closest(".erp-subtab[data-erp-subtab]");if($){L.preventDefault();const W=$.dataset.erpSubtab;document.querySelectorAll(".erp-subtab").forEach(function(te){te.classList.toggle("active",te.dataset.erpSubtab===W)}),document.querySelectorAll(".erp-subpanel").forEach(function(te){te.classList.toggle("active",te.dataset.erpSubpanel===W)}),W==="mappings"&&setTimeout(g,50);return}const E=L.target.closest(".erp-map-subtab[data-erp-subtab]");if(E){L.preventDefault(),f(E.dataset.erpSubtab);return}if(L.target.closest("#erp-map-add-btn")){if(L.preventDefault(),!l())return;p.addingNew[p.sub]=!0,x();return}const K=L.target.closest('[data-erp-save="new"]');if(K){L.preventDefault();const W=K.closest('[data-erp-row="new"]');W&&F(W);return}const G=L.target.closest("[data-erp-del]");if(G){L.preventDefault(),A(G.dataset.erpDel);return}}))}function I(){const L=document.getElementById("erp-map-pane-wrap");L&&L.children.length>0&&v(),document.querySelectorAll(".erp-map-subtab").forEach(function($){const E="erp-map-subtab-"+$.dataset.erpSubtab,M=t(E);M&&M!==E&&($.textContent=M)})}h(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-mappings",I)})();(function(){let e=null,n=0,a=!1;function o(g){return typeof escapeHtml=="function"?escapeHtml(g==null?"":String(g)):String(g??"")}function s(g,f){try{typeof showToast=="function"&&showToast(g,f||"info")}catch{}}async function p(g){const f=Date.now();if(e&&f-n<3e4)return e;const h=localStorage.getItem("mrpilot_token");if(!h)return[];try{const I=await fetch("/api/erp/connectors/status",{headers:{Authorization:"Bearer "+h}});if(!I.ok)return[];const L=await I.json();return e=L&&L.connectors||[],n=f,e}catch{return[]}}function l(){try{return localStorage.getItem("pn_push_default_connector")||""}catch{return""}}function y(g){try{localStorage.setItem("pn_push_default_connector",g||"")}catch{}}function i(g){if(!g||!g.length)return null;const f=l();if(f){const I=g.find(L=>L.id===f);if(I)return I}const h=g.find(I=>I.is_default);return h||g[0]}function r(g){if(!g)return!1;const f=String(g.status||"").toLowerCase();return f==="exception"||f==="exception_pending"||f==="rejected"}function d(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function c(g){const f=g&&(g.type||g.id);return f==="xero"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5.5 8l2 2 3-3.5"/></svg>':f==="webhook"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="11.5" r="1.8"/><circle cx="11" cy="4.5" r="1.8"/><path d="M6.4 10l3.2-4M5 9.6V5.5a3 3 0 016 0"/></svg>':'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/><rect x="11" y="3" width="3" height="10" rx="1"/></svg>'}async function v(g,f){if(!g||!f)return!1;const h=document.getElementById("btn-push-default");h&&(h.disabled=!0,h.classList.add("loading"));const I=localStorage.getItem("mrpilot_token");try{let L,$={method:"POST",headers:{Authorization:"Bearer "+I}};g.type==="xero"?L="/api/erp/xero/push/"+encodeURIComponent(f):(L="/api/erp/push",$.headers["Content-Type"]="application/json",$.body=JSON.stringify({history_id:f,endpoint_id:g.endpoint_id||void 0}));const E=await fetch(L,$);let M={};try{M=await E.json()}catch{}if(!E.ok){let K=M&&M.detail||"unknown";typeof K=="object"&&(K=K.code||JSON.stringify(K));let G=String(K||"unknown");if(g.type==="xero"){const W=G.replace(/^xero\./,"").toLowerCase(),te=t("xero-"+W);te&&te!=="xero-"+W&&(G=te)}return s(t("unified-push-fail").replace("{name}",g.name).replace("{err}",G),"error"),!1}if(M&&M.ok===!1){let K=M.error_msg||M.error_code||"unknown";return K=String(K).slice(0,200),s(t("unified-push-fail").replace("{name}",g.name).replace("{err}",K),"error"),!1}return s(t("unified-push-ok").replace("{name}",g.name),"success"),!0}catch(L){return s(t("unified-push-fail").replace("{name}",g.name).replace("{err}",L.message||"network"),"error"),!1}finally{h&&(h.disabled=!1,h.classList.remove("loading"))}}async function x(g,f){for(const h of g)await v(h,f)}function _(g,f){const h=document.createElement("div");h.className="pn-push-dropdown",h.id="pn-push-dropdown";const I=(g||[]).map($=>{const E=!!(f&&$.id===f.id),M=$.method==="download"?t("unified-push-tag-download"):E?t("unified-push-tag-default"):"";return'<div class="pn-pd-item" data-cid="'+o($.id)+'"><span class="pn-pd-icon">'+c($)+'</span><span class="pn-pd-name">'+o($.name)+"</span>"+(M?'<span class="pn-pd-tag">'+o(M)+"</span>":"")+(E?'<span class="pn-pd-check">✓</span>':"")+"</div>"}).join(""),L=g&&g.length>1?'<div class="pn-pd-divider"></div><div class="pn-pd-item pn-pd-all" data-cid="__all__"><span class="pn-pd-icon"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h10M3 10h10M3 13.5h6"/></svg></span><span class="pn-pd-name">'+o(t("unified-push-all").replace("{n}",g.length))+"</span></div>":"";return h.innerHTML=I+L,h}function q(){const g=document.getElementById("pn-push-dropdown");g&&g.remove()}async function j(){if(document.getElementById("pn-push-dropdown")){q();return}const g=await p()||[],f=i(g),h=_(g,f),I=document.getElementById("pn-push-wrap");I&&I.appendChild(h)}async function k(){const g=await p()||[],f=i(g);if(!f)return;const h=d(),I=h&&(h._historyId||h.history_id);if(I){if(r(h)){s(t("unified-push-disabled-exc"),"warn");return}await v(f,I)}}async function B(g){q();const f=await p()||[],h=d(),I=h&&(h._historyId||h.history_id);if(!I)return;if(r(h)){s(t("unified-push-disabled-exc"),"warn");return}if(g==="__all__"){await x(f,I);return}const L=f.find($=>$.id===g);L&&(y(g),await v(L,I),R())}async function N(){const g=document.getElementById("drawer-history-save");if(!g||g.querySelector("#pn-push-wrap"))return;const f=document.createElement("div");f.id="pn-push-wrap",f.className="pn-push-wrap",f.dataset.loading="1",g.insertBefore(f,g.firstChild),["btn-push-erp","btn-xero-push"].forEach(M=>{g.querySelectorAll("#"+M).forEach(K=>{K.style.display="none"})});const h=await p()||[],I=i(h),L=h.length>0;if(!L)f.innerHTML='<button type="button" class="btn btn-ghost pn-push-empty" id="btn-push-default" disabled title="'+o(t("unified-push-empty-tip"))+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/></svg><span style="margin-left:4px;">'+o(t("unified-push-empty"))+"</span></button>";else{const M=h.length>1;f.innerHTML='<div class="pn-push-split"><button type="button" class="pn-push-main" id="btn-push-default" title="'+o(t("unified-push-tip"))+'">'+c(I)+"<span>"+o(t("unified-push-to").replace("{name}",I?I.name:""))+"</span></button>"+(M?'<button type="button" class="pn-push-arrow" id="btn-push-arrow" title="'+o(t("unified-push-other"))+'"><svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5l3 3 3-3"/></svg></button>':"")+"</div>"}delete f.dataset.loading;const $=f.querySelector("#btn-push-default");$&&L&&$.addEventListener("click",k);const E=f.querySelector("#btn-push-arrow");E&&E.addEventListener("click",function(M){M.stopPropagation(),j()}),a||(a=!0,document.addEventListener("click",function(M){const K=M.target.closest(".pn-pd-item");if(K){const G=K.getAttribute("data-cid");B(G);return}M.target.closest("#btn-push-arrow")||q()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("unified-push",R))}function R(){const g=document.getElementById("pn-push-wrap");g&&(g.remove(),e=null,n=0,N())}function F(){const g=document.getElementById("drawer-history-save");if(!g||!g.querySelector("#pn-push-wrap"))return;["btn-push-erp","btn-xero-push"].forEach(h=>{g.querySelectorAll("#"+h).forEach(I=>{I.style.display!=="none"&&(I.style.display="none")})});const f=g.querySelectorAll("#pn-push-wrap");if(f.length>1)for(let h=1;h<f.length;h++)f[h].remove()}function A(){try{const g=function(){return document.getElementById("drawer-body")},f=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&N(),F()}),h=g();if(h)f.observe(h,{childList:!0,subtree:!0});else{const I=new MutationObserver(function(){const L=g();L&&(f.observe(L,{childList:!0,subtree:!0}),I.disconnect())});I.observe(document.body,{childList:!0,subtree:!0})}setTimeout(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&N(),F()},200)}catch{}}A()})();(function(){function e(){const a=document.getElementById("erp-map-show-advanced-btn");if(!a)return;const o=document.getElementById("erp-map-subtabs");if(!o)return;const s=o.classList.contains("show-advanced"),p=a.querySelector(".erp-map-adv-btn-label");if(p&&typeof t=="function"){const l=s?"erp-map-hide-advanced":"erp-map-show-advanced",y=t(l);y&&y!==l&&(p.textContent=y)}a.setAttribute("aria-pressed",s?"true":"false")}document.addEventListener("click",function(a){if(!a.target.closest("#erp-map-show-advanced-btn"))return;a.preventDefault();const s=document.getElementById("erp-map-subtabs");if(s&&(s.classList.toggle("show-advanced"),e(),!s.classList.contains("show-advanced")&&s.querySelector(".erp-map-subtab.active.erp-map-subtab-advanced"))){const l=s.querySelector('.erp-map-subtab[data-erp-subtab="clients"]');l&&l.click()}});function n(){e()}typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-map-advanced-toggle",n)})();(function(){const e="pearnly_erp_onboard_shown";let n=!1;function a(){try{return Array.isArray(window._erpEndpoints)&&window._erpEndpoints.length>0}catch{return!1}}function o(){if(document.getElementById("erp-onboard-mask"))return;const p=document.createElement("div");p.id="erp-onboard-mask",p.className="erp-onboard-mask",p.innerHTML='<div class="erp-onboard-modal" role="dialog" aria-modal="true"><div class="erp-onboard-icon"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="6" width="24" height="20" rx="3"/><path d="M9 13h14M9 18h10"/><path d="M22 22l3 3 5-5"/></svg></div><div class="erp-onboard-title" id="erp-onboard-title"></div><div class="erp-onboard-body" id="erp-onboard-body"></div><div class="erp-onboard-btns"><button type="button" class="btn btn-secondary" id="erp-onboard-later"></button><button type="button" class="btn btn-primary" id="erp-onboard-ok"></button></div></div>',document.body.appendChild(p);function l(){const i=document.getElementById("erp-onboard-title"),r=document.getElementById("erp-onboard-body"),d=document.getElementById("erp-onboard-ok"),c=document.getElementById("erp-onboard-later");i&&(i.textContent=t("erp-onboard-title")),r&&(r.textContent=t("erp-onboard-body")),d&&(d.textContent=t("erp-onboard-ok")),c&&(c.textContent=t("erp-onboard-later"))}l();function y(){p.style.display="none"}document.getElementById("erp-onboard-ok").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}y();try{const i=document.querySelector('#btn-add-endpoint, [data-action="erp-add-endpoint"]');i&&i.scrollIntoView({behavior:"smooth",block:"center"})}catch{}}),document.getElementById("erp-onboard-later").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}y()}),p.addEventListener("click",function(i){i.target===p&&y()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-onboard-modal",function(){p.style.display!=="none"&&l()})}function s(){if(!n){try{if(localStorage.getItem(e)==="1")return}catch{}a()||(n=!0,o(),requestAnimationFrame(function(){requestAnimationFrame(function(){if(a())return;const p=document.getElementById("erp-onboard-mask");p&&(p.style.display="flex")})}))}}document.addEventListener("click",function(p){const l=p.target.closest('.auto-nav-item[data-auto-tab="erp"]'),y=p.target.closest('.erp-subtab[data-erp-subtab="connect"]');(l||y)&&setTimeout(s,700)})})();(function(){const e={parse:{zh:"解析文件中",th:"กำลังอ่านไฟล์",en:"Parsing files",ja:"ファイル解析中"},report:{zh:"读取报告中",th:"กำลังอ่านรายงาน",en:"Reading report",ja:"レポート読込中"},reconcile:{zh:"对账中",th:"กำลังกระทบยอด",en:"Reconciling",ja:"照合中"},build:{zh:"生成中",th:"กำลังสร้างไฟล์",en:"Building",ja:"作成中"},persist:{zh:"保存中",th:"กำลังบันทึก",en:"Saving",ja:"保存中"},done:{zh:"完成",th:"เสร็จสิ้น",en:"Done",ja:"完了"}};window._reconProgressText=function(n,a){n=n||{},a=window._currentLang||a||localStorage.getItem("mrpilot_lang")||"th",e.parse[a]||(a="th");const o=n.stage||"parse",s=e[o]||e.parse,p=s[a]||s.th||s.en,l=n.stage_total,y=n.stage_done;if(o==="parse"&&Number.isFinite(l)&&l>0){const i={zh:"共 {d}/{t} 个文件",th:"{d}/{t} ไฟล์",en:"{d}/{t} files",ja:"{d}/{t} ファイル"}[a]||"{d}/{t} files";return p+" · "+i.replace("{d}",y||0).replace("{t}",l)}return p},window._reconPollJob=async function(n,a,o){o=o||{};const s=o.intervalMs||1500,p=o.maxMs||1200*1e3,l=Date.now();let y=0;for(;;){let i=null;try{const r=await fetch("/api/recon/jobs/"+encodeURIComponent(n),{headers:{Authorization:"Bearer "+a}});try{i=await r.json()}catch{i=null}(!r.ok||!i||!i.ok)&&(i=null)}catch{i=null}if(i){if(y=0,o.onProgress)try{o.onProgress(i.progress||{},i)}catch{}if(i.status==="done"||i.status==="failed"||i.status==="needs_review"||i.status==="needs_mapping")return i}else if(++y>=10)return{ok:!1,status:"failed",error_code:"poll_unreachable"};if(Date.now()-l>p)return{ok:!1,status:"timeout",error_code:"timeout"};await new Promise(r=>setTimeout(r,s))}}})();(function(){let e=!1,n=[],a=[],o=null,s="all",p=[],l={stmt:"",gl:""},y=[];const i=b=>document.getElementById(b);function r(b){if(b==null)return"—";const C=Number(b);return isNaN(C)?"—":C.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function d(b){return b?String(b).slice(0,10).split("-").reverse().join("/"):"—"}function c(b){return String(b||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function v(b,C){C=window._currentLang||C||"th";const T={stmt_headers_not_found:{zh:"认不出银行账单表头 · 请确认文件含日期/金额/余额列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตารางบัญชีธนาคารไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/จำนวนเงิน/ยอดคงเหลือ หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect bank statement headers · ensure the file has date/amount/balance columns, or re-upload as a clean Excel/CSV",ja:"銀行明細のヘッダーを認識できません · 日付/金額/残高列を確認するか、Excel/CSVに変換して再アップロードしてください"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含日期/科目/借方/贷方列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตาราง GL ไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต/เครดิต หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect GL headers · ensure the file has date/account/debit/credit columns, or re-upload as a clean Excel/CSV",ja:"GLのヘッダーを認識できません · 日付/科目/借方/貸方列を確認するか、Excel/CSVに変換して再アップロードしてください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水,或换更清晰的版本重传",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง หรือใช้เวอร์ชันที่ชัดเจนกว่า",en:"No transaction rows found · please upload the correct statement, or try a clearer version",ja:"取引データが見つかりません · 正しい明細をアップロードするか、より鮮明なファイルでお試しください"},no_rows:{zh:"解析后没有可对账的数据行 · 请确认文件内容完整,或换清晰版本重传",th:"ไม่มีแถวข้อมูลให้กระทบยอดหลังการอ่าน · ตรวจสอบความสมบูรณ์ของไฟล์ หรืออัปโหลดใหม่",en:"No reconcilable rows after parsing · check the file is complete, or re-upload a clearer version",ja:"解析後に照合可能な行がありません · ファイルの完全性を確認するか再アップロードしてください"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密 · 请换文件或转 PDF/Excel 重传",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส · ลองไฟล์อื่นหรือแปลงเป็น PDF/Excel",en:"File cannot be read · may be corrupted or encrypted · try another file or convert to PDF/Excel",ja:"ファイルを読み取れません · 破損または暗号化の可能性 · 別ファイルまたはPDF/Excelに変換してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロードしてください"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本,或转成 PDF / Excel / CSV 重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น PDF / Excel / CSV",en:"Could not read the file · try a clearer version, or convert to PDF / Excel / CSV",ja:"読み取りに失敗 · より鮮明なファイルか、PDF / Excel / CSV に変換して再試行してください"}},U={zh:"解析失败 · 请换更清晰的文件,或转成 Excel / CSV 后重新上传",th:"อ่านไฟล์ไม่สำเร็จ · ลองไฟล์ที่ชัดเจนกว่า หรือแปลงเป็น Excel / CSV แล้วอัปโหลดใหม่",en:"Parsing failed · try a clearer file, or convert to Excel / CSV and re-upload",ja:"解析に失敗しました · より鮮明なファイルか、Excel / CSV に変換して再アップロードしてください"},z=T[b]||U;return z[C]||z.th||z.en}function x(b){const C=b==="stmt"?n:a,T=i(`brv2-${b}-name`);if(T)if(C.length===0)T.textContent="";else{const z=window._currentLang||"zh",u={zh:"个文件",th:" ไฟล์",en:" file(s)",ja:" ファイル"};T.textContent=C.length+(u[z]||" 个文件")}const U=i("brv2-preview-panel");U&&U.style.display!=="none"&&j(b),_()}function _(){const b=i("brv2-toggle-preview"),C=i("brv2-preview-panel"),T=n.length+a.length>0;b&&(b.style.display=T?"":"none"),!T&&C&&(C.style.display="none",b&&b.classList.remove("open"))}function q(){j("stmt"),j("gl")}function j(b){const C=i(b==="stmt"?"brv2-pp-stmt-col":"brv2-pp-gl-col");if(!C)return;const T=b==="stmt"?n:a,U=window._currentLang||"zh",z={stmt:{zh:"① 银行账单",th:"① บัญชีธนาคาร",en:"① Bank Stmt",ja:"① 銀行明細"},gl:{zh:"② 总账 GL",th:"② GL รายงาน",en:"② GL Report",ja:"② GL帳簿"}},u=(z[b]||{})[U]||z[b].zh,P=c(window.t&&window.t("vex-preview-search")||"搜索文件名..."),O=c(window.t&&window.t("vex-preview-clear-all")||"全清"),Y=l[b]||"";C.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+c(u)+' <span class="vex-pp-col-count">'+T.length+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="brv2-pp-search-'+b+'" type="text" placeholder="'+P+'" value="'+c(Y)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="brv2-pp-clearall-'+b+'" type="button">'+O+'</button></div><div class="vex-pp-file-list" id="brv2-pp-'+b+'-list"></div><div class="vex-pp-pagination" id="brv2-pp-'+b+'-pg"></div>';const X=i("brv2-pp-search-"+b);X&&X.addEventListener("input",function(se){l[b]=se.target.value,k(b)});const de=i("brv2-pp-clearall-"+b);de&&de.addEventListener("click",function(){b==="stmt"?n.length=0:a.length=0,x(b),M()}),k(b)}function k(b){const C=i("brv2-pp-"+b+"-list"),T=i("brv2-pp-"+b+"-pg");if(!C)return;const U=b==="stmt"?n:a,z=(l[b]||"").toLowerCase(),u=z?U.filter(Y=>Y.name.toLowerCase().includes(z)):U.slice(),P='<svg class="vex-pp-fi-ico" viewBox="0 0 14 16" fill="none" stroke="currentColor" stroke-width="1.4" width="12" height="14"><path d="M3 1h6l3 3v11H3V1z"/><path d="M9 1v3h3"/></svg>',O='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" width="11" height="11"><path d="M2 4h10M5 4V2h4v2M5.5 7v4M8.5 7v4M3 4l1 8h6l1-8"/></svg>';if(C.innerHTML=u.map((Y,X)=>'<div class="vex-pp-file-row">'+P+'<span class="vex-pp-fi-name" title="'+c(Y.name)+'">'+c(Y.name)+'</span><span class="vex-pp-fi-size">'+B(Y.size)+'</span><button class="vex-pp-fi-del" type="button" data-zone="'+b+'" data-idx="'+U.indexOf(Y)+'" aria-label="remove">'+O+"</button></div>").join(""),C.querySelectorAll(".vex-pp-fi-del").forEach(function(Y){Y.addEventListener("click",function(){const X=parseInt(Y.dataset.idx,10);Y.dataset.zone==="stmt"?n.splice(X,1):a.splice(X,1),x(Y.dataset.zone),M()})}),T){const Y=window.t&&window.t("vex-preview-count")||"显示 {n} / 共 {m}";T.textContent=Y.replace("{n}",u.length).replace("{m}",U.length)}}function B(b){return b?b<1024?b+" B":b<1048576?(b/1024).toFixed(1)+" KB":(b/1048576).toFixed(1)+" MB":""}var N="pearnly.brv2.lastAnchorOcr";function R(b){try{var C=b&&b._anchor_ocr;if(!C||typeof C!="object")return;var T={stmt_opening:Number.isFinite(+C.stmt_opening)?+C.stmt_opening:null,gl_opening:Number.isFinite(+C.gl_opening)?+C.gl_opening:null,gl_closing:Number.isFinite(+C.gl_closing)?+C.gl_closing:null,stmt_closing:Number.isFinite(+C.stmt_closing)?+C.stmt_closing:null,ts:Date.now()};localStorage.setItem(N,JSON.stringify(T))}catch{}}function F(){try{var b=localStorage.getItem(N);if(!b)return null;var C=JSON.parse(b);return!C||typeof C!="object"?null:C}catch{return null}}function A(){var b=F();if(b){var C={"brv2-anchor-stmt-opening":b.stmt_opening,"brv2-anchor-gl-opening":b.gl_opening,"brv2-anchor-gl-closing":b.gl_closing,"brv2-anchor-stmt-closing":b.stmt_closing},T=0;Object.keys(C).forEach(function(O){var Y=document.getElementById(O);if(Y&&Y.value===""){var X=C[O];if(Number.isFinite(X)){Y.value=X.toFixed(2);var de=Y.closest&&Y.closest(".brv2-anchor-cell");de&&de.classList.add("is-prefilled"),T+=1}}});var U=document.getElementById("brv2-anchor-eq"),z=document.getElementById("brv2-anchor-eq-val");if(U&&z&&Number.isFinite(b.stmt_opening)&&Number.isFinite(b.gl_opening)){var u=b.stmt_opening-b.gl_opening;z.textContent=u.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),U.style.display=""}if(T>0){var P=document.getElementById("brv2-anchor-prefill-banner");P&&P.classList.add("show")}}}function g(){var b=document.getElementById("brv2-anchor-prefill-banner");if(b){var C=!1;["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"].forEach(function(T){var U=document.getElementById(T);if(U){var z=U.closest&&U.closest(".brv2-anchor-cell");z&&z.classList.contains("is-prefilled")&&(C=!0)}}),b.classList.toggle("show",C)}}var f=[["stmt_opening","brv2-anchor-stmt-opening"],["gl_opening","brv2-anchor-gl-opening"],["gl_closing","brv2-anchor-gl-closing"],["stmt_closing","brv2-anchor-stmt-closing"]];function h(b,C){return window.t&&window.t(b)||C}function I(b){return String(b??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function L(b){return Number.isFinite(+b)?(+b).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—"}function $(b){var C=document.getElementById("brv2-summary-collapse");if(!(!C||!C.parentNode)){var T=document.getElementById("brv2-anchor-audit"),U=b&&b._anchor_overrides;if(!U||typeof U!="object"||Object.keys(U).length===0){T&&T.parentNode&&T.parentNode.removeChild(T);return}T||(T=document.createElement("div"),T.id="brv2-anchor-audit",T.style.cssText="margin-top:14px;background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:14px 16px;",C.parentNode.insertBefore(T,C.nextSibling));var z=f.map(function(u){var P=U[u[0]];if(!P)return"";var O=+P.ocr||0,Y=+P.user||0,X=Y-O,de=X>0?"+":(X<0,""),se=Math.abs(X)<.005?"#6b7280":X>0?"#16a34a":"#dc2626";return'<tr><td style="padding:6px 10px;color:#111827;font-size:13px">'+I(h(u[1],u[0]))+'</td><td style="padding:6px 10px;color:#6b7280;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+I(L(O))+'</td><td style="padding:6px 10px;background:#fef08a;color:#92400e;font-weight:600;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+I(L(Y))+'</td><td style="padding:6px 10px;color:'+se+';font-weight:500;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+I(de+L(X))+"</td></tr>"}).join("");T.innerHTML='<div style="font-weight:600;color:#92400e;font-size:13px;margin-bottom:10px">'+I(h("brv2-anchor-audit-title","⚠ This run contains manually entered anchors"))+'</div><table style="width:100%;border-collapse:collapse;font-family:inherit"><thead><tr><th style="padding:6px 10px;text-align:left;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+I(h("brv2-anchor-audit-col-field","Field"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+I(h("brv2-anchor-audit-col-ocr","OCR"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+I(h("brv2-anchor-audit-col-user","User"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+I(h("brv2-anchor-audit-col-diff","Diff"))+"</th></tr></thead><tbody>"+z+"</tbody></table>"}}function E(){const b=i("brv2-toggle-preview");b&&!b._reconBound&&(b._reconBound=!0,b.addEventListener("click",function(){const C=i("brv2-preview-panel"),T=i("brv2-toggle-preview-label"),U=C&&C.style.display!=="none";C&&(C.style.display=U?"none":""),b.classList.toggle("open",!U),T&&(T.textContent=U?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),U||q()}))}function M(){const b=i("brv2-run-btn"),C=i("brv2-status"),T=n.length>0,U=a.length>0;if(b&&(b.disabled=!(T&&U)),C){const z=window._currentLang||"zh";if(!T&&!U){const u={zh:"请上传银行账单和 GL 文件",th:"กรุณาอัปโหลดบัญชีธนาคารและ GL",en:"Upload bank statement and GL files",ja:"銀行明細と GL を両方アップロードしてください"};C.textContent=u[z]||u.zh}else if(T)if(U){const u={zh:"两份文件已就绪",th:"พร้อมสอบทาน",en:"Ready to reconcile",ja:"照合を開始できます"};C.textContent=u[z]||u.zh}else{const u={zh:"还缺 GL 文件",th:"ยังขาดไฟล์ GL",en:"Missing GL file",ja:"GL ファイルが未アップロード"};C.textContent=u[z]||u.zh}else{const u={zh:"还缺银行账单 PDF",th:"ยังขาดไฟล์บัญชีธนาคาร PDF",en:"Missing bank statement PDF",ja:"銀行明細 PDF が未アップロード"};C.textContent=u[z]||u.zh}}}function K(b,C,T){const U=i(b),z=i(C);!U||!z||(U.addEventListener("click",()=>z.click()),U.addEventListener("keydown",u=>{(u.key==="Enter"||u.key===" ")&&(u.preventDefault(),z.click())}),U.addEventListener("dragover",u=>{u.preventDefault(),U.classList.add("drag-over")}),U.addEventListener("dragleave",()=>U.classList.remove("drag-over")),U.addEventListener("drop",u=>{u.preventDefault(),U.classList.remove("drag-over");const P=Array.from(u.dataTransfer.files||[]);T==="stmt"?n.push(...P):a.push(...P),x(T),M()}),z.addEventListener("change",()=>{const u=Array.from(z.files||[]);T==="stmt"?n.push(...u):a.push(...u),z.value="",x(T),M()}))}function G(b){const C=i("brv2-progress"),T=i("brv2-run-btn"),U=i("brv2-error");C&&(C.style.display=b?"":"none"),T&&(T.disabled=b),U&&(U.style.display="none")}function W(b){const C=i("brv2-error");C&&(C.textContent=b,C.style.display="",C.scrollIntoView({behavior:"smooth",block:"nearest"})),G(!1),M(),window.showToast&&window.showToast(b,"error")}async function te(){if(n.length===0||a.length===0)return;const b=localStorage.getItem("mrpilot_token")||"",C=window._currentLang||"zh",T=(i("brv2-acct-select")||{}).value||"";S(!1),G(!0);try{const U=new FormData;n.forEach(ae=>U.append("stmt_files",ae)),a.forEach(ae=>U.append("gl_files",ae)),U.append("gl_account",T),U.append("lang",C);const z=parseFloat((i("brv2-anchor-gl-closing")||{}).value),u=parseFloat((i("brv2-anchor-stmt-closing")||{}).value),P=parseFloat((i("brv2-anchor-stmt-opening")||{}).value),O=parseFloat((i("brv2-anchor-gl-opening")||{}).value);Number.isFinite(z)&&U.append("gl_closing_override",z),Number.isFinite(u)&&U.append("stmt_closing_override",u),Number.isFinite(P)&&U.append("stmt_opening_override",P),Number.isFinite(O)&&U.append("gl_opening_override",O);const Y=await fetch("/api/recon/bank-v2/submit",{method:"POST",headers:{Authorization:"Bearer "+b},body:U});let X=null;try{X=await Y.json()}catch{X=null}if(X&&X.needs_mapping){G(!1),window.ReconMapping?window.ReconMapping.show(X,{token:b,lang:C,onConfirmed:function(){te()}}):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(!Y.ok||!X||!X.ok||!X.job_id){G(!1),X&&(X.detail||X.error)?W(_humanizeBackendError(X.detail||X.error,"Error "+Y.status)):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const de=i("brv2-progress-sub"),se=await window._reconPollJob(X.job_id,b,{onProgress:ae=>{de&&(de.textContent=window._reconProgressText(ae,C))}});if(se&&se.status==="needs_mapping"&&se.mapping){G(!1),window.ReconMapping?window.ReconMapping.show(se.mapping,{token:b,lang:C,onConfirmed:function(){te()}}):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(se&&se.status==="needs_review"&&se.review){G(!1),window.ReconReview?window.ReconReview.show(se.review,{token:b,lang:C,jobId:X.job_id,onConfirmed:async function(ae){G(!0);const pe=await window._reconPollJob(ae,b,{onProgress:ve=>{de&&(de.textContent=window._reconProgressText(ve,C))}});await ce(pe)}}):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(se&&se.status==="failed"){G(!1),W(v(se.error_code,C));return}await ce(se);async function ce(ae){try{if(!ae||ae.status!=="done"||!ae.result_id){G(!1),W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const pe=await fetch("/api/recon/bank-v2/"+encodeURIComponent(ae.result_id),{headers:{Authorization:"Bearer "+b}});let ve=null;try{ve=await pe.json()}catch{ve=null}if(!pe.ok||ve===null||!ve.ok){G(!1),W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}(ve.gl_accounts||[]).length>1&&re(ve.gl_accounts),o=ve,p=ve.detail||[],s="all",document.querySelectorAll(".brv2-filter-btn").forEach(ge=>ge.classList.toggle("active",ge.dataset.filter==="all")),R(ve&&ve.summary),G(!1),D(ve),Z();const fe=i("brv2-summary-collapse");fe&&fe.scrollIntoView({behavior:"smooth",block:"nearest"})}catch(pe){G(!1),W(pe.message||"Network error")}}}catch(U){W(U.message||"Network error")}}function re(b){const C=i("brv2-acct-select");if(!C)return;const T=window._currentLang||"zh",U={zh:"全部账户",th:"ทุกบัญชี",en:"All Accounts",ja:"すべての口座"}[T]||"全部账户";C.innerHTML=`<option value="">${U}</option>`+b.map(z=>`<option value="${c(z)}">${c(z)}</option>`).join(""),C.style.display=""}function S(b){const C=i("brv2-summary-collapse"),T=i("brv2-detail-collapse"),U=i("brv2-export-btn"),z=i("brv2-new-btn"),u=i("brv2-parse-info-wrap");C&&(C.style.display=b?"":"none"),T&&(T.style.display=b?"":"none"),U&&(U.style.display=b?"":"none"),z&&(z.style.display=b?"":"none"),!b&&u&&(u.style.display="none");const P=i("brv2-warnings");!b&&P&&(P.style.display="none",P.innerHTML="")}function w(b){const C=i("brv2-parse-info-wrap"),T=i("brv2-parse-info-body");if(!C||!T)return;const U=b.parse_info;if(!U){C.style.display="none";return}const z=window._currentLang||"zh",u={title:{zh:"文件解析状态",th:"สถานะการอ่านไฟล์",en:"File Parse Status",ja:"ファイル解析状態"},type:{zh:"类型",th:"ประเภท",en:"Type",ja:"種別"},file:{zh:"文件名",th:"ชื่อไฟล์",en:"File",ja:"ファイル"},rows:{zh:"解析行数",th:"แถวที่พบ",en:"Rows Found",ja:"解析行数"},bank:{zh:"银行/科目",th:"ธนาคาร/บัญชี",en:"Bank/Account",ja:"銀行/科目"},status:{zh:"状态",th:"สถานะ",en:"Status",ja:"状態"},stmt:{zh:"账单",th:"บัญชีธนาคาร",en:"Stmt",ja:"明細"},gl:{zh:"总账GL",th:"GL",en:"GL",ja:"GL"},ok:{zh:"✓ 成功",th:"✓ สำเร็จ",en:"✓ OK",ja:"✓ 成功"},warn:{zh:"⚠ 0行",th:"⚠ 0 แถว",en:"⚠ 0 rows",ja:"⚠ 0行"},fail:{zh:"✗ 失败",th:"✗ ล้มเหลว",en:"✗ Failed",ja:"✗ 失敗"}},P=ce=>(u[ce]||{})[z]||(u[ce]||{}).zh||ce,O=[...(U.stmt_files||[]).map(ce=>({...ce,_type:"stmt",_extra:ce.bank_code||""})),...(U.gl_files||[]).map(ce=>({...ce,_type:"gl",_extra:(ce.accounts||[]).join(", ")}))],Y={stmt_headers_not_found:{zh:"认不出表头列 · 请确认文件含日期/金额/余额列",th:"หาคอลัมน์หัวตารางไม่เจอ · ตรวจสอบไฟล์มีวันที่/จำนวนเงิน/ยอดคงเหลือ",en:"Cannot detect column headers · ensure file has date/amount/balance columns",ja:"列ヘッダーが認識できません · 日付/金額/残高列を確認してください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง",en:"No transaction rows found · please check the file",ja:"取引データが見つかりません · ファイルを確認してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロード"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส",en:"File cannot be read · may be corrupted or encrypted",ja:"ファイルを読み取れません · 破損または暗号化の可能性"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本或换 PDF 格式重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่าหรือเปลี่ยนเป็น PDF",en:"Could not read file · try a clearer version or upload as PDF",ja:"読み取り失敗 · より鮮明なファイルまたは PDF 形式で再試行"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含科目/借方/贷方列",th:"หาหัวคอลัมน์ GL ไม่เจอ · ตรวจสอบมีคอลัมน์บัญชี/เดบิต/เครดิต",en:"Cannot detect GL column headers · ensure account/debit/credit columns exist",ja:"GL 列ヘッダー認識不可 · 科目/借方/貸方列を確認してください"}},X=ce=>{const ae=String(ce||"");return/Cannot detect bank statement column headers/i.test(ae)?"stmt_headers_not_found":/Cannot detect GL column headers/i.test(ae)?"gl_headers_not_found":/No transaction rows found|no pages parsed/i.test(ae)?"stmt_no_rows":/unsupported format/i.test(ae)?"file_not_supported":/Cannot read Excel|file_unreadable/i.test(ae)?"file_unreadable":/Gemini.*invalid JSON|Gemini.*parsed but failed|validation errors|BankStatementDocument schema|layer2:|layer1:/i.test(ae)?"ocr_failed":null},de=ce=>{const ae=ce.error_code||X(ce.error);if(ae&&Y[ae]){const pe=window._currentLang||"zh";return Y[ae][pe]||Y[ae].zh}return String(ce.error||"").slice(0,80)},se=ce=>!ce.ok&&ce.error?`<span style="color:#dc2626">${P("fail")} — ${c(de(ce))}</span>`:ce.rows?`<span style="color:#059669">${P("ok")} (${ce.rows})</span>`:`<span style="color:#d97706">${P("warn")}</span>`;T.innerHTML=`
            <div style="font-size:12px;font-weight:600;margin-bottom:6px;color:var(--ink-2)">${P("title")}</div>
            <table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:4px">
                <thead>
                    <tr style="background:#f3f4f6;font-weight:600">
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${P("type")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb">${P("file")}</th>
                        <th style="padding:6px 8px;text-align:center;border:1px solid #e5e7eb;white-space:nowrap">${P("rows")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${P("bank")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${P("status")}</th>
                    </tr>
                </thead>
                <tbody>
                    ${O.map(ce=>`<tr>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;white-space:nowrap">${ce._type==="stmt"?P("stmt"):P("gl")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${c(ce.file||"")}">${c(ce.file||"")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;text-align:center">${ce.rows||0}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;color:var(--ink-2)">${c(ce._extra||"")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb">${se(ce)}</td>
                    </tr>`).join("")}
                </tbody>
            </table>`,C.style.display=""}async function m(b){const C=localStorage.getItem("mrpilot_token")||"",T=window._currentLang||"zh";try{const U=await fetch("/api/recon/bank-v2/"+b+"/export?lang="+T,{headers:{Authorization:"Bearer "+C}});if(!U.ok){const de=await U.json().catch(()=>({}));window.showToast&&window.showToast(de.detail||"Export failed","error");return}const z=await U.blob(),P=(U.headers.get("content-disposition")||"").match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/),O=P?P[1].replace(/['"]/g,""):"reconciliation.xlsx",Y=URL.createObjectURL(z),X=document.createElement("a");X.href=Y,X.download=O,document.body.appendChild(X),X.click(),document.body.removeChild(X),URL.revokeObjectURL(Y)}catch(U){window.showToast&&window.showToast("Export error: "+U.message,"error")}}function H(b,C){const T=i("brv2-summary-collapse");let U=i("brv2-warnings");const z=window._currentLang||"zh",u={zh:"⏭ 已跳过无法识别的文件:",th:"⏭ ข้ามไฟล์ที่อ่านไม่ได้:",en:"⏭ Skipped unreadable file:",ja:"⏭ 読み取れないファイルをスキップ:"}[z]||"⏭ ",P=[];if((C||[]).forEach(O=>P.push(u+" "+O)),(b||[]).forEach(O=>P.push(O)),!P.length){U&&(U.style.display="none");return}if(!U)if(U=document.createElement("div"),U.id="brv2-warnings",T&&T.parentNode)T.parentNode.insertBefore(U,T);else return;U.style.cssText="display:block;margin:10px 0;padding:10px 14px;background:#FEF3C7;border:1px solid #FCD34D;border-radius:8px;color:#92400E;font-size:13px;line-height:1.6",U.innerHTML=P.map(O=>"<div>"+c(O)+"</div>").join("")}function D(b){w(b),H(b.warnings||[],b.skipped_files||[]),!b.ok&&b.error&&window.showToast&&window.showToast(b.error,"error");const C=b.stats||{},T=b.summary||{},U=C.matched||0,z=(C.gl_debit_only||0)+(C.gl_credit_only||0),u=(C.stmt_withdrawal_only||0)+(C.stmt_deposit_only||0),P=Number(T.formula_diff||0),O=Math.abs(P)<.05;i("brv2-kpi-matched")&&(i("brv2-kpi-matched").textContent=U),i("brv2-kpi-diff")&&(i("brv2-kpi-diff").textContent=r(P)),i("brv2-kpi-unmatched")&&(i("brv2-kpi-unmatched").textContent=z+u);const Y=i("brv2-kpi-diff-icon");Y&&(Y.style.background=O?"#d1fae5":"#fee2e2",Y.style.color=O?"#065f46":"#b91c1c");const X=i("brv2-formula-sub");if(X){const pe=window._currentLang||"zh";X.textContent=O?{zh:"✓ 平衡",th:"✓ สมดุล",en:"✓ Balanced",ja:"✓ 一致"}[pe]||"✓ 平衡":({zh:"差 ",th:"ต่าง ",en:"Diff ",ja:"差 "}[pe]||"差 ")+r(P)}const de=i("brv2-detail-sub");if(de){const pe=window._currentLang||"zh",ve={zh:"共 {n} 行",th:"ทั้งหมด {n} แถว",en:"{n} rows",ja:"計 {n} 行"}[pe]||"共 {n} 行";de.textContent=ve.replace("{n}",p.length)}function se(pe,ve,fe){const ge=i(pe);ge&&(ge.textContent=(fe&&ve>0?"(":"")+r(fe?-ve:ve)+(fe&&ve>0?")":""))}se("brf-gl-close",T.gl_closing||0),se("brf-open-diff",T.opening_diff||0),se("brf-gl-debit-only",T.gl_debit_only_amount||0,!0),se("brf-gl-credit-only",T.gl_credit_only_amount||0),se("brf-stmt-wd-only",T.stmt_withdrawal_only_amount||0,!0),se("brf-stmt-dep-only",T.stmt_deposit_only_amount||0),se("brf-calc-close",T.formula_stmt_closing||0),se("brf-stmt-close",T.stmt_closing||0),i("brf-diff")&&(i("brf-diff").textContent=r(P));const ce=i("brv2-fcell-diff");ce&&ce.classList.toggle("brv2-fcell-diff-ok",O);const ae=i("brv2-export-btn");ae&&(ae.onclick=()=>{o&&m(o.task_id)}),$(T),S(!0),J()}function J(){const b=i("brv2-tbody");if(!b)return;const C=p.filter(u=>s==="all"?!0:s==="matched"?u.match_status==="matched":s==="gl_only"?u.match_status.startsWith("gl_"):s==="stmt_only"?u.match_status.startsWith("stmt_"):!0);if(C.length===0){const u={zh:"无记录",th:"ไม่มีรายการ",en:"No rows",ja:"行なし"}[window._currentLang||"zh"]||"无记录";b.innerHTML=`<tr><td colspan="10" style="text-align:center;padding:20px;color:var(--ink-3)">${u}</td></tr>`;return}const T=window._currentLang||"zh",U={zh:"OCR 余额验证未通过 · 上一行余额 ± 金额 ≠ 本行余额，请核对原 PDF",th:"การตรวจสอบยอดคงเหลือไม่ผ่าน · ยอดก่อนหน้า ± จำนวน ≠ ยอดบรรทัดนี้ โปรดตรวจสอบ PDF ต้นฉบับ",en:"Balance check FAILED · prev_balance ± amount ≠ this row balance — verify against the original PDF",ja:"残高検証エラー · 前残高 ± 金額 ≠ この行残高 — 元のPDFと照合してください"}[T],z={zh:"OCR 低置信度 · 数字模糊或难以辨认，请核对原 PDF",th:"OCR ความมั่นใจต่ำ · ตัวเลขเบลอหรืออ่านยาก โปรดตรวจสอบ PDF ต้นฉบับ",en:"OCR low confidence · digit was blurry or hard to read — verify against the original PDF",ja:"OCR信頼度低 · 数字がぼやけている — 元のPDFと照合してください"}[T];b.innerHTML=C.map(u=>{const P=u.match_status,O=u.match_layer;let Y="",X="";P==="matched"?(O===1&&(Y="matched",X='<span class="brv2-status-badge brv2-badge-matched">L1 ✓</span>'),O===2&&(Y="matched-l2",X='<span class="brv2-status-badge brv2-badge-matched-l2">L2 ~</span>'),O===3&&(Y="matched-l3",X='<span class="brv2-status-badge brv2-badge-matched-l3">L3 ?</span>')):P==="gl_debit_only"||P==="gl_credit_only"?(Y="gl-only",X='<span class="brv2-status-badge brv2-badge-gl-only">GL</span>'):(Y="stmt-only",X=`<span class="brv2-status-badge brv2-badge-stmt-only">${{zh:"账单",th:"บัญชี",en:"Stmt",ja:"明細"}[T]||"账单"}</span>`);let de="";return u.stmt_balance_ok===!1&&(de+=`<span class="brv2-ocr-warn brv2-ocr-warn-bal" title="${c(U)}">⚠</span>`,Y+=" brv2-row-warn"),u.stmt_confidence==="low"&&(de+=`<span class="brv2-ocr-warn brv2-ocr-warn-conf" title="${c(z)}">◌</span>`,Y.includes("brv2-row-warn")||(Y+=" brv2-row-warn-soft")),`<tr class="${Y.trim()}">
              <td>${X}${de}</td>
              <td>${c(d(u.stmt_date))}</td>
              <td title="${c(u.stmt_desc)}" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${c(u.stmt_desc)}</td>
              <td class="num">${u.stmt_withdrawal?r(u.stmt_withdrawal):""}</td>
              <td class="num">${u.stmt_deposit?r(u.stmt_deposit):""}</td>
              <td>${c(d(u.gl_date))}</td>
              <td title="${c(u.gl_doc_no)}" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${c(u.gl_doc_no)}</td>
              <td class="num">${u.gl_debit?r(u.gl_debit):""}</td>
              <td class="num">${u.gl_credit?r(u.gl_credit):""}</td>
              <td>${O?"L"+O:"—"}</td>
            </tr>`}).join("")}async function Z(){const b=localStorage.getItem("mrpilot_token")||"";try{const T=await(await fetch("/api/recon/bank-v2/tasks",{headers:{Authorization:"Bearer "+b}})).json();ee(T.tasks||[])}catch{const T=i("brv2-history-empty"),U=window._currentLang||"zh",z={zh:"加载失败",th:"โหลดประวัติไม่ได้",en:"Load failed",ja:"読み込み失敗"}[U]||"加载失败";T&&(T.textContent=z,T.style.display="");const u=i("brv2-history-table-wrap");u&&(u.style.display="none")}}const le=10;let ie=1;function V(){const b=i("brv2-history-pager"),C=i("brv2-history-pager-info"),T=i("brv2-history-prev"),U=i("brv2-history-next");if(!b)return;if(y.length<=le){b.style.display="none";return}b.style.display="";const z=Math.ceil(y.length/le);C&&(C.textContent=ie+" / "+z),T&&(T.disabled=ie<=1),U&&(U.disabled=ie>=z)}function Q(){const b=i("brv2-history-prev"),C=i("brv2-history-next");b&&!b._brv2Bound&&(b._brv2Bound=!0,b.addEventListener("click",()=>{ie>1&&(ie--,ee(y))})),C&&!C._brv2Bound&&(C._brv2Bound=!0,C.addEventListener("click",()=>{const T=Math.ceil(y.length/le);ie<T&&(ie++,ee(y))}))}function ee(b){b!==void 0&&(y=b||[],ie=1);const C=y,T=i("brv2-history-empty"),U=i("brv2-history-table-wrap"),z=i("brv2-history-tbody");if(!z)return;const u=window._currentLang||"zh";if(!C.length){const ae={zh:"暂无对账记录",th:"ยังไม่มีประวัติ",en:"No records yet",ja:"記録なし"}[u]||"暂无对账记录";T&&(T.textContent=ae,T.style.display=""),U&&(U.style.display="none"),V();return}T&&(T.style.display="none"),U&&(U.style.display="");const P=Math.ceil(C.length/le);ie>P&&(ie=P);const O=(ie-1)*le,Y=C.slice(O,O+le),X=localStorage.getItem("mrpilot_token")||"",de='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><circle cx="8" cy="8" r="6"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',se='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',ce='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';z.innerHTML="",Y.forEach(ae=>{const pe=Number(ae.formula_diff||0),ve=Math.abs(pe)<.05,fe=(ae.stmt_files||"").split(";").map(ke=>ke.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),ge=(ae.gl_files||"").split(";").map(ke=>ke.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),be=ae.created_at?String(ae.created_at).slice(0,16).replace("T"," "):"",xe=document.createElement("tr");xe.dataset.taskId=ae.id;const De=document.createElement("td");De.textContent=be;const Le=document.createElement("td");Le.className="glv-history-file",Le.title=fe+" + "+ge,Le.textContent=fe+" + "+ge;const Ce=document.createElement("td");Ce.className="glv-num",Ce.textContent=(ae.stmt_row_count||0)+" / "+(ae.gl_row_count||0);const Ue=document.createElement("td");Ue.className="glv-num",Ue.textContent=ae.matched_count||0;const Ge=document.createElement("td");Ge.className="glv-num",Ge.textContent=ae.unmatched_gl||0;const Je=document.createElement("td");Je.className="glv-num",Je.textContent=ae.unmatched_stmt||0;const Re=document.createElement("td");Re.className="glv-num",Re.style.color=ve?"#059669":"#dc2626",Re.textContent=ve?"✓":r(pe);const Se=document.createElement("td");Se.className="glv-history-actions";const Ye=(ke,ot,st,At)=>{const Ee=document.createElement("button");return Ee.type="button",Ee.title=ot,Ee.setAttribute("aria-label",ot),st&&(Ee.className=st),Ee.innerHTML=ke,Ee.onclick=jt=>{jt.stopPropagation(),At()},Ee},Tt={zh:"删除这条记录?",th:"ลบรายการนี้?",en:"Delete this record?",ja:"この記録を削除しますか?"}[u]||"删除?",Mt={zh:"加载",th:"โหลด",en:"Load",ja:"読込"}[u]||"加载",$t={zh:"导出",th:"ส่งออก",en:"Export",ja:"エクスポート"}[u]||"导出",Ht={zh:"删除",th:"ลบ",en:"Delete",ja:"削除"}[u]||"删除";Se.appendChild(Ye(de,Mt,"",()=>oe(ae.id,X))),Se.appendChild(Ye(se,$t,"",()=>m(ae.id))),Se.appendChild(Ye(ce,Ht,"glv-del",async()=>{await showConfirm(Tt,{danger:!0})&&(await fetch("/api/recon/bank-v2/"+ae.id,{method:"DELETE",headers:{Authorization:"Bearer "+X}}),Z())})),[De,Le,Ce,Ue,Ge,Je,Re,Se].forEach(ke=>xe.appendChild(ke)),xe.style.cursor="pointer",xe.addEventListener("click",async ke=>{ke.target.closest(".glv-del")||ke.target.closest("button")||await oe(ae.id,X)}),z.appendChild(xe)}),V(),ne()}function ne(){const b=((i("brv2-hist-search")||{}).value||"").trim().toLowerCase(),C=i("brv2-history-tbody");C&&C.querySelectorAll("tr").forEach(T=>{T.dataset.taskId&&(T.style.display=!b||T.textContent.toLowerCase().includes(b)?"":"none")})}async function oe(b,C){try{const U=await(await fetch("/api/recon/bank-v2/"+b,{headers:{Authorization:"Bearer "+C}})).json();if(!U.ok)return;o={task_id:U.task_id,...U},p=U.detail||[],s="all",document.querySelectorAll(".brv2-filter-btn").forEach(z=>z.classList.toggle("active",z.dataset.filter==="all")),D(o)}catch{}}function ue(){if(e){Z();return}e=!0,K("brv2-stmt-zone","brv2-stmt-input","stmt"),K("brv2-gl-zone","brv2-gl-input","gl");const b=["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"];function C(){const O=parseFloat((i("brv2-anchor-stmt-opening")||{}).value),Y=parseFloat((i("brv2-anchor-gl-opening")||{}).value),X=i("brv2-anchor-eq"),de=i("brv2-anchor-eq-val");if(!(!X||!de))if(Number.isFinite(O)&&Number.isFinite(Y)){const se=O-Y;de.textContent=se.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),X.style.display=""}else X.style.display="none"}b.forEach(O=>{const Y=i(O);Y&&(Y.addEventListener("input",C),Y.addEventListener("input",()=>{const X=Y.closest(".brv2-anchor-cell");X&&X.classList.remove("is-prefilled"),g()}))}),A();const T=i("brv2-run-btn");T&&T.addEventListener("click",te);const U=i("brv2-reset-btn");U&&U.addEventListener("click",()=>{o=null,p=[],n=[],a=[],x("stmt"),x("gl"),M(),S(!1);const O=i("brv2-acct-select");O&&(O.style.display="none"),b.forEach(de=>{const se=i(de);if(se){se.value="";const ce=se.closest&&se.closest(".brv2-anchor-cell");ce&&ce.classList.remove("is-prefilled")}});const Y=i("brv2-anchor-eq");Y&&(Y.style.display="none");const X=i("brv2-anchor-prefill-banner");X&&X.classList.remove("show")});const z=i("brv2-new-btn");z&&z.addEventListener("click",()=>{o=null,p=[],n=[],a=[],x("stmt"),x("gl"),M(),S(!1)});const u=i("brv2-filter-tabs");u&&u.addEventListener("click",O=>{O.stopPropagation();const Y=O.target.closest(".brv2-filter-btn");Y&&(s=Y.dataset.filter,u.querySelectorAll(".brv2-filter-btn").forEach(X=>X.classList.toggle("active",X===Y)),J())}),E(),Q();const P=i("brv2-hist-search");P&&P.addEventListener("input",ne),Z(),M(),window._brv2LoadHistory=Z,Array.isArray(window.__i18nSubs)||(window.__i18nSubs=[]),window.__i18nSubs=window.__i18nSubs.filter(O=>O.name!=="brv2"),window.__i18nSubs.push({name:"brv2",fn:function(){M(),x("stmt"),x("gl"),o&&D(o),ee()}})}window._loadBankReconV2Panel=function(b){const C=b?document.getElementById(b):null;C&&C.id!=="recon-pane-bank"&&(C.innerHTML=`<div style="padding:16px;font-size:13px;color:var(--ink-3)">
                银行对账 v2 · 请前往对账中心使用</div>`),ue()},document.addEventListener("DOMContentLoaded",()=>{i("brv2-run-btn")&&ue()}),window._bankReconV2Init=ue})();(function(){const e=document.getElementById("general-lang");if(!e)return;e.addEventListener("change",a=>{const o=a.target.value;o&&applyLang(o)});const n=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";e.value=n})();(function(){const n="pearnly_general_tz",a="pearnly_general_date_format",o="pearnly_general_number_format",s={tz:"Asia/Bangkok",date:"YYYY-MM-DD",number:"comma_dot"};function p(){const r=document.getElementById("general-tz"),d=document.getElementById("general-date"),c=document.getElementById("general-number");if(!(!r||!d||!c))try{r.value=localStorage.getItem(n)||s.tz,d.value=localStorage.getItem(a)||s.date,c.value=localStorage.getItem(o)||s.number}catch{r.value=s.tz,d.value=s.date,c.value=s.number}}async function l(){const r=document.getElementById("btn-save-general"),d=document.getElementById("general-save-msg");if(!r)return;const c=r.innerHTML;r.disabled=!0,r.innerHTML="<span>"+(t("msg-saving")||"保存中...")+"</span>",d&&(d.textContent="",d.classList.remove("error"));try{const v=(document.getElementById("general-tz")||{}).value||s.tz,x=(document.getElementById("general-date")||{}).value||s.date,_=(document.getElementById("general-number")||{}).value||s.number;try{localStorage.setItem(n,v),localStorage.setItem(a,x),localStorage.setItem(o,_)}catch{}window._pearnlyGeneral={tz:v,date_format:x,number_format:_},d&&(d.textContent=t("msg-saved")||"已保存")}catch{d&&(d.textContent=t("msg-save-failed")||"保存失败",d.classList.add("error"))}finally{r.disabled=!1,r.innerHTML=c,setTimeout(function(){d&&(d.textContent="")},3e3)}}function y(){const r=document.getElementById("btn-save-general");if(!r){setTimeout(y,200);return}r._pearnlyGenBound||(r._pearnlyGenBound=!0,r.addEventListener("click",l),p())}function i(){p();const r=document.getElementById("general-lang");if(r){const d=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";r.value=d}}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",y):y(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("settings-general",i)})();(function(){const e="mrpilot_nav_collapsed",n={ocr:"sales",history:"sales",reconcile:"sales","sales-invoices":"sales",receivables:"sales",vouchers:"expense"};function a(){try{const l=localStorage.getItem(e);return l?JSON.parse(l):{}}catch{return{}}}function o(l){try{localStorage.setItem(e,JSON.stringify(l))}catch{}}function s(){const l=a();document.querySelectorAll(".nav-collapsible").forEach(function(y){const i=y.dataset.collapsible;l[i]?y.classList.add("collapsed"):y.classList.remove("collapsed")})}function p(l){const y=a();y[l]=!y[l],o(y),s()}(function(){const y=a();let i=!1;y.sales===void 0&&(y.sales=!1,i=!0),y.expense===void 0&&(y.expense=!0,i=!0),i&&o(y)})(),s(),document.querySelectorAll(".nav-group-toggle").forEach(function(l){l.addEventListener("click",function(){p(l.dataset.toggleGroup)})}),window.expandNavGroupForRoute=function(l){const y=n[l];if(!y)return;const i=a();i[y]&&(i[y]=!1,o(i),s())}})();const cn=`
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
    </div>`;function ct(){const e=document.getElementById("help-modal");if(!e||e.children.length)return;e.innerHTML=cn;const n=window._currentLang||"th",a=window.I18N&&window.I18N[n]||{};e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[s]&&(o.textContent=a[s])})}document.readyState,ct();(function(){function e(){const n=document.getElementById("help-modal"),a=document.getElementById("help-modal-close");n&&(a&&!a.dataset.bound&&(a.addEventListener("click",function(){n.style.display="none"}),a.dataset.bound="1"),n.dataset.maskBound||(n.addEventListener("click",function(o){o.target===n&&(n.style.display="none")}),n.dataset.maskBound="1"),window._helpModalEscBound||(document.addEventListener("keydown",function(o){o.key==="Escape"&&n.style.display==="flex"&&(n.style.display="none")}),window._helpModalEscBound=!0))}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",e):e()})();(function(){const e={line:"line",folder:"folder",gmail:"email",erp:"erp",alert:"alert"};document.addEventListener("click",function(n){const a=n.target.closest(".int-btn-configure");if(!a)return;const o=a.closest(".integration-row"),s=o?o.dataset.intAnchor:null;if(s&&e[s]){const p=o.querySelector(".int-name"),l=p?(p.textContent||p.innerText||"").trim():"配置";typeof window.openIntegrationDrawer=="function"&&window.openIntegrationDrawer(e[s],l)}})})();let we=[];window._erpEndpoints=we;let je=null;async function Fe(){try{const e=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(e.status===401){localStorage.removeItem("mrpilot_token");const a=await e.json().catch(()=>({}));if((typeof a.detail=="string"?a.detail:a.detail&&a.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}we=(await e.json()).items||[],window._erpEndpoints=we,kt()}catch(e){console.error("load endpoints failed",e)}}window._refreshErpEndpointsCache=function(){return Fe()};async function wt(){const e=document.getElementById("erp-today-stats");if(e){e.innerHTML="";try{const n=await fetch("/api/erp/stats/today",{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=a.total||0,s=a.success||0,p=a.failed||0,l=a.auto_cnt||0;if(o===0){e.innerHTML=`<span class="erp-today-empty">${escapeHtml(t("erp-today-none"))}</span>`;return}const y=[];y.push(`<span class="erp-today-item"><strong>${o}</strong> ${escapeHtml(t("erp-today-total"))}</span>`),s>0&&y.push(`<span class="erp-today-item ok"><strong>${s}</strong> ${escapeHtml(t("erp-today-success"))}</span>`),p>0&&y.push(`<span class="erp-today-item fail"><strong>${p}</strong> ${escapeHtml(t("erp-today-failed"))}</span>`),l>0&&y.push(`<span class="erp-today-item auto"><strong>${l}</strong> ${escapeHtml(t("erp-today-auto"))}</span>`),e.innerHTML=y.join("")}catch(n){console.warn("loadErpTodayStats failed",n)}}}function kt(){const e=document.getElementById("erp-endpoints-list"),n=document.getElementById("erp-status-summary"),a=document.getElementById("btn-add-endpoint");if(!e){console.warn("erp-endpoints-list 容器不存在");return}if(a&&_userInfo){const s=_userInfo.endpoints_limit;s!==-1&&we.length>=s?(a.disabled=!0,a.title=t("ep-limit-reached",{limit:s}),a.classList.add("btn-disabled-plus")):(a.disabled=!1,a.title="",a.classList.remove("btn-disabled-plus"))}if(we.length===0){e.innerHTML=`<div class="erp-empty">${escapeHtml(t("ep-list-empty"))}</div>`,n&&(n.textContent=t("auto-status-none"),n.className="auto-status-pill none");return}const o=we.some(s=>s.auto_push&&s.enabled);if(n&&(n.textContent=t("auto-status-active",{n:we.length,mode:o?t("auto-status-on"):t("auto-status-off")}),n.className="auto-status-pill "+(o?"active":"ready")),wt(),e.innerHTML=we.map(s=>{const p=s.config||{},l=escapeHtml(p.url||"");p._token_set;const y=s.enabled!==!1,i=[];s.is_default&&i.push(`<span class="ep-badge default">${escapeHtml(t("ep-default"))}</span>`),s.auto_push&&i.push(`<span class="ep-badge auto">${escapeHtml(t("ep-auto-push-on"))}</span>`),y||i.push(`<span class="ep-badge disabled">${escapeHtml(t("ep-disabled"))}</span>`);const r=[];return s.success_count>0&&r.push(`<span class="ep-stat ok">${escapeHtml(t("ep-success",{n:s.success_count}))}</span>`),s.failure_count>0&&r.push(`<span class="ep-stat fail">${escapeHtml(t("ep-failure",{n:s.failure_count}))}</span>`),`
            <div class="erp-endpoint" data-ep-id="${escapeHtml(s.id)}">
                <div class="ep-main">
                    <div class="ep-title-row">
                        <div class="ep-name">${escapeHtml(s.name)}</div>
                        <div class="ep-badges">${i.join("")}</div>
                    </div>
                    <div class="ep-url">${l||"-"}</div>
                    <div class="ep-stats">${r.join(" · ")}</div>
                </div>
                <div class="ep-actions">
                    <button class="btn btn-ghost btn-small" data-ep-edit="${escapeHtml(s.id)}">
                        <span>${escapeHtml(t("ep-edit"))}</span>
                    </button>
                    <button class="btn btn-ghost btn-small btn-danger" data-ep-del="${escapeHtml(s.id)}">
                        <span>${escapeHtml(t("ep-delete"))}</span>
                    </button>
                </div>
            </div>
        `}).join(""),_userInfo&&_userInfo.endpoints_limit!==-1){const s=we.length,p=_userInfo.endpoints_limit,l=_userInfo.plan,y=document.createElement("div");y.className="erp-limit-hint",l==="free"?y.innerHTML=`${escapeHtml(t("ep-free-limit-hint",{used:s,limit:p}))} <a data-upgrade="plus">${escapeHtml(t("upgrade-to-plus"))}</a>`:y.textContent=t("ep-plus-limit-hint",{used:s,limit:p}),e.appendChild(y)}}function dn(e){je=e||null;const n=document.getElementById("endpoint-modal"),a=document.getElementById("endpoint-modal-title");a.textContent=e?t("ep-modal-title-edit"):t("ep-modal-title-new");const o=document.getElementById("ep-name"),s=document.getElementById("ep-url"),p=document.getElementById("ep-token"),l=document.getElementById("ep-is-default"),y=document.getElementById("ep-auto-push"),i=document.getElementById("ep-test-result");i.style.display="none",i.textContent="";const r=document.getElementById("ep-save-error");if(r&&r.remove(),e){const c=we.find(v=>v.id===e);if(!c)return;o.value=c.name||"",s.value=(c.config||{}).url||"",p.value=(c.config||{})._token_set&&c.config.token||"",p.placeholder=(c.config||{})._token_set?"（已保存 · 留空保持不变）":t("ep-token-ph"),l.checked=!!c.is_default,y.checked=!!c.auto_push}else o.value="",s.value="",p.value="",p.placeholder=t("ep-token-ph"),l.checked=we.length===0,y.checked=!0;const d=y.closest(".form-switch-row");if(y.disabled=!1,d){d.classList.remove("disabled-plus"),d.title="",d.style.cursor="",d.onclick=null;const c=d.querySelector(".plus-badge");c&&c.remove()}n.style.display="",setTimeout(()=>o.focus(),50)}function xt(){document.getElementById("endpoint-modal").style.display="none",je=null;const e=document.getElementById("ep-save-error");e&&e.remove()}function _t(e){if(!e)return"";let n=e.trim();const a=n.search(/\s/);return a>=0&&(n=n.slice(0,a)),n}function Et(){const e=document.getElementById("ep-name").value.trim(),n=_t(document.getElementById("ep-url").value),a=document.getElementById("ep-token").value,o=document.getElementById("ep-is-default").checked,s=document.getElementById("ep-auto-push").checked,p={url:n};return a&&(p.token=a),{name:e,url:n,tokenVal:a,isDefault:o,autoPush:s,config:p}}async function pn(){const{url:e,config:n}=Et(),a=document.getElementById("ep-test-result");if(!e){a.style.display="",a.className="form-test-result fail",a.textContent=t("ep-required");return}a.style.display="",a.className="form-test-result running",a.textContent=t("ep-test-running");try{const s=await(await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({adapter:"webhook",config:n})})).json();s.success?(a.className="form-test-result ok",a.textContent=t("ep-test-ok",{status:s.http_status,ms:s.elapsed_ms})):(a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:s.error_msg||"unknown"}))}catch(o){a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:o.message})}}async function un(){const e=Et(),n=document.getElementById("ep-save-error");if(n&&(n.style.display="none"),!e.name||!e.url){dt(t("ep-required"));return}const a={name:e.name,adapter:"webhook",config:e.config,is_default:e.isDefault,auto_push:e.autoPush},o=document.getElementById("btn-ep-save"),s=o.innerHTML;o.disabled=!0,o.classList.add("loading");try{let p;if(je?p=await fetch(`/api/erp/endpoints/${encodeURIComponent(je)}`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}):p=await fetch("/api/erp/endpoints",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}),!p.ok){const y=(await p.json().catch(()=>({}))).detail||`HTTP ${p.status}`;throw new Error(typeof y=="string"?y:JSON.stringify(y))}xt(),showToast(t("ep-save-ok")),Fe()}catch(p){dt(`${t("ep-save-fail")} · ${p.message||"unknown"}`)}finally{o.disabled=!1,o.classList.remove("loading"),o.innerHTML=s}}function dt(e){let n=document.getElementById("ep-save-error");if(!n){const a=document.querySelector("#endpoint-modal .modal-foot");if(!a)return;n=document.createElement("div"),n.id="ep-save-error",n.className="ep-inline-error",a.parentNode.insertBefore(n,a)}n.textContent=e,n.style.display=""}async function vn(e){const n=we.find(o=>o.id===e);if(!(!n||!await showConfirm(t("ep-delete-confirm",{name:n.name}),{danger:!0})))try{if(!(await fetch(`/api/erp/endpoints/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showToast(t("ep-delete-ok")),Fe()}catch{showToast(t("ep-save-fail"),"fail")}}window.loadErpEndpoints=Fe;window.loadErpTodayStats=wt;window.renderErpEndpointsList=kt;window.openEndpointModal=dn;window.closeEndpointModal=xt;window.saveEndpoint=un;window.deleteEndpoint=vn;window.testEndpointConnection=pn;window._sanitizeUrl=_t;async function Bt(e){if(e=(e||"").trim(),!!e)try{await navigator.clipboard.writeText(e),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{try{const a=document.createElement("textarea");a.value=e,a.style.position="fixed",a.style.opacity="0",document.body.appendChild(a),a.select(),document.execCommand("copy"),a.remove(),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{showToast(t("erp-doc-copy-fail"),"error")}}}async function fn(e){const n=document.createElement("div");n.className="log-detail-modal",n.innerHTML=`
        <div class="log-detail-box">
            <div class="log-detail-loading">${escapeHtml(t("log-detail-loading"))}</div>
        </div>
    `,document.body.appendChild(n),n.addEventListener("click",async a=>{if(a.target===n||a.target.classList.contains("log-detail-close")){n.remove();return}const o=a.target.closest("[data-receipt-copy]");if(o){Bt(o.dataset.receiptCopy);return}const s=a.target.closest("[data-receipt-action]");if(s){const p=s.dataset.receiptAction;p==="retry"?window.retryPushLog(s.dataset.logId):p==="exceptions"?typeof routeTo=="function"&&routeTo("exceptions"):p==="mappings"&&typeof routeTo=="function"&&routeTo("integrations"),n.remove();return}});try{const a=await fetch(`/api/erp/logs/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!a.ok){n.remove();return}const o=await a.json(),s=window._erpEndpoints.find(L=>L.id===o.endpoint_id),p=o.endpoint_name||(s?s.name:o.endpoint_id?t("erp-log-endpoint-deleted"):"-"),l=(o.endpoint_adapter||s&&s.adapter||"").toLowerCase(),y=new Date(o.created_at).toLocaleString(),i=o.trigger==="auto"?t("log-tag-auto"):o.trigger==="retry"?t("log-tag-retry"):t("log-tag-manual"),r=o.request_body?JSON.stringify(o.request_body,null,2):t("erp-receipt-no-tech"),d=o.response_body||t("erp-receipt-no-tech"),c=o.status==="success";let v=typeof d=="string"?d:JSON.stringify(d,null,2);if(c)try{const L=typeof o.response_body=="string"?JSON.parse(o.response_body):o.response_body||{},$=L.row_count||(Array.isArray(L.imported_rows)?L.imported_rows.length:0);$>0&&(v=t("log-push-rows").replace("{n}",String($)))}catch{}const x=(o.external_doc_no||"").trim(),_=(o.external_url||"").trim(),q=(o.external_doc_hint||"").trim(),j=(o.ocr_buyer_name||"").trim()||o.client_name||"-",k=o.seller_name||"-";let B="-";const N=Number(o.total_amount);o.total_amount!=null&&o.total_amount!==""&&!isNaN(N)&&(B=N.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}));const R=c?t("erp-receipt-title-ok"):t("erp-receipt-title-fail"),F=c?"✓":"✗",A=[],g=(L,$)=>{A.push(`
                <div class="erp-receipt-row">
                    <span class="erp-receipt-key">${escapeHtml(L)}</span>
                    <span class="erp-receipt-val">${$}</span>
                </div>`)};if(g(t("erp-receipt-invoice-no"),`<strong>${escapeHtml(o.invoice_no||"-")}</strong>`),g(t("erp-receipt-erp-name"),escapeHtml(p)),c){let L;x?L=`<strong class="erp-receipt-docno">${escapeHtml(x)}</strong><button class="erp-receipt-copy-btn" type="button" data-receipt-copy="${escapeHtml(x)}" title="${escapeHtml(t("erp-doc-copy-tip"))}">${escapeHtml(t("erp-receipt-copy-btn"))}</button>`:L=`<span class="erp-receipt-docno-missing">${escapeHtml(t("erp-log-doc-missing"))}</span>`,g(t("erp-receipt-doc-no"),L)}g(t("erp-receipt-client"),escapeHtml(j)),g(t("erp-receipt-seller"),escapeHtml(k)),c&&g(t("erp-receipt-amount"),escapeHtml(B)),g(t("erp-receipt-time"),escapeHtml(y)),g(t("erp-receipt-elapsed"),escapeHtml((o.elapsed_ms!=null?o.elapsed_ms:"-")+"ms"));let f="";c&&_?f=`<a class="erp-receipt-primary-btn" href="${escapeHtml(_)}" target="_blank" rel="noopener">${escapeHtml(t("erp-receipt-open-erp"))}</a>`:c&&x&&(f=`<button class="erp-receipt-primary-btn" type="button" data-receipt-copy="${escapeHtml(x)}">${escapeHtml(t("erp-receipt-copy-docno"))}</button>`);let h="";if(c&&x&&q){const L="erp-receipt-hint-"+q,$=t(L);$&&$!==L&&(h=`<div class="erp-receipt-hint"><svg class="erp-receipt-hint-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span>${escapeHtml($)}</span></div>`)}let I="";if(!c){const L=(o.error_msg||"").match(/ERR_[A-Z0-9_]+/),$=L?L[0]:"",E=typeof currentLang=="string"&&currentLang||window._currentLang||"th",K=o.error_friendly&&o.error_friendly[E]||(o.error_msg?humanizeError(o.error_msg):t("erp-receipt-no-error")),G=/ERR_NO_CUSTOMER_MAPPING|ERR_NO_CLIENT|ERR_NO_SEED_CUSTOMER|ERR_NO_SEED_PRODUCT/.test(o.error_msg||""),W=!!(o.history_id&&o.endpoint_id),te=[];te.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="exceptions">${escapeHtml(t("erp-receipt-act-exceptions"))}</button>`),G&&te.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="mappings">${escapeHtml(t("erp-receipt-act-mapping"))}</button>`),W&&te.push(`<button class="erp-receipt-action-btn primary" type="button" data-receipt-action="retry" data-log-id="${escapeHtml(o.id)}">${escapeHtml(t("erp-receipt-act-retry"))}</button>`),I=`
                <div class="erp-receipt-fail-reason-label">${escapeHtml(t("erp-receipt-fail-reason"))}</div>
                <div class="erp-receipt-fail-box">
                    ${$?`<div class="erp-receipt-errcode">${escapeHtml($)}</div>`:""}
                    <div class="erp-receipt-friendly">${escapeHtml(K)}</div>
                </div>
                <div class="erp-receipt-actions-label">${escapeHtml(t("erp-receipt-suggest"))}</div>
                <div class="erp-receipt-actions">${te.join("")}</div>`}n.querySelector(".log-detail-box").innerHTML=`
            <div class="log-detail-head">
                <div class="log-detail-title">
                    <span class="log-detail-status-icon ${c?"ok":"fail"}">${F}</span>
                    ${escapeHtml(R)}
                    <span class="log-tag ${o.trigger}">${escapeHtml(i)}</span>
                </div>
                <button class="log-detail-close" type="button">✕</button>
            </div>

            <div class="erp-receipt-body">
                ${A.join("")}
            </div>

            ${h}
            ${f?`<div class="erp-receipt-primary-wrap">${f}</div>`:""}
            ${I}

            <details class="log-detail-collapsible">
                <summary>${escapeHtml(t("erp-receipt-tech-toggle"))}</summary>
                <div class="log-detail-meta" style="margin-top:8px;">
                    <span>HTTP ${o.http_status||"-"}</span>
                    <span>${o.elapsed_ms}ms</span>
                    <span>${escapeHtml(t("log-detail-attempt",{n:o.attempt||1}))}</span>
                </div>
                <div class="log-detail-section" style="margin-top:12px;">
                    <div class="log-detail-label">${escapeHtml(t("log-detail-request-human"))}</div>
                    <pre>${escapeHtml(r)}</pre>
                </div>
                <div class="log-detail-section">
                    <div class="log-detail-label">${escapeHtml(t("log-detail-response-human"))}</div>
                    <pre>${escapeHtml(v)}</pre>
                </div>
            </details>
        `}catch(a){console.error(a),n.remove()}}window.copyErpDocNo=Bt;window.showLogDetail=fn;let Be={key:"all",val:""},_e=new Set;window._erpSelected=_e;async function Pe(e){const n=document.getElementById("erp-logs-list");if(n){e||(n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`),window.loadErpTodayStats();try{const a=new URLSearchParams({limit:"30"});Be.key==="status"&&a.set("status",Be.val),Be.key==="trigger"&&a.set("trigger",Be.val),Be.key==="adapter"&&a.set("adapter",Be.val);const o=await fetch(`/api/erp/logs?${a}`,{headers:{Authorization:"Bearer "+token}});if(!o.ok){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const p=(await o.json()).items||[];if(window._erpLogPollTimer&&(clearTimeout(window._erpLogPollTimer),window._erpLogPollTimer=null),p.some(function(r){return r.status==="pending"})&&(window._erpLogPollTimer=setTimeout(function(){Pe(!0)},4e3)),p.length===0){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-empty"))}</div>`;return}const y='<div class="erp-log-row erp-log-row-header" data-log-header>'+(p.filter(function(r){var d=r.status==="failed"&&r.next_retry_at&&new Date(r.next_retry_at).getTime()>Date.now()-6e4;return!d}).map(function(r){return r.id}).length>0?`<input type="checkbox" class="erp-log-cb erp-log-cb-all" data-log-select-all title="${escapeHtml(t("erp-log-select-all-tip"))}">`:'<span class="erp-log-cb-spacer"></span>')+`<span class="log-time">${escapeHtml(t("erp-log-col-time"))}</span><span class="log-status">${escapeHtml(t("erp-log-col-status"))}</span><span class="log-tag-header">${escapeHtml(t("erp-log-col-trigger"))}</span><span class="log-invoice">${escapeHtml(t("erp-log-col-invoice"))}</span><span class="log-workspace">${escapeHtml(t("erp-log-col-workspace"))}</span><span class="log-client">${escapeHtml(t("erp-log-col-client"))}</span><span class="log-seller">${escapeHtml(t("erp-log-col-seller"))}</span><span class="log-erp">${escapeHtml(t("erp-log-col-erp"))}</span><span class="log-doc">${escapeHtml(t("erp-log-col-doc"))}</span><span class="log-http">${escapeHtml(t("erp-log-col-http"))}</span><span class="log-elapsed">${escapeHtml(t("erp-log-col-elapsed"))}</span><span class="log-actions"></span></div>`;n.innerHTML=y+p.map(r=>{const d=new Date(r.created_at),c=`${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")} ${String(d.getHours()).padStart(2,"0")}:${String(d.getMinutes()).padStart(2,"0")}`,v=r.status==="failed"&&r.next_retry_at&&new Date(r.next_retry_at).getTime()>Date.now()-6e4;let x,_,q;r.status==="pending"?(x="retrying",_="⟳",q=t("erp-status-pending")):r.status==="success"?(x="ok",_="✓",q=t("erp-status-success")):r.status==="skipped_dup"?(x="skipped",_="⏭",q=t("erp-status-skipped")):v?(x="retrying",_="↻",q=t("erp-status-retrying")):(x="fail",_="✗",q=t("erp-status-failed"));let j;r.trigger==="auto"?j=`<span class="log-tag auto">${escapeHtml(t("log-tag-auto"))}</span>`:r.trigger==="retry"?j=`<span class="log-tag retry">${escapeHtml(t("log-tag-retry"))}</span>`:j=`<span class="log-tag manual">${escapeHtml(t("log-tag-manual"))}</span>`;let k="";const B=r.retry_count||0,N=r.max_retries||3;if(v){const K=new Date(r.next_retry_at).getTime()-Date.now(),G=Math.max(0,Math.round(K/6e4)),W=G<=0?t("erp-retry-next-soon"):t("erp-retry-next-min",{n:G});k=`${t("erp-retry-attempt",{n:B,max:N})} · ${W}`}else r.status==="failed"&&B>=N&&!r.next_retry_at&&(k=t("erp-retry-exhausted",{n:B}));const R=r.status==="failed"&&!v?`<button class="log-retry-btn btn btn-icon" data-log-retry="${escapeHtml(r.id)}" title="${escapeHtml(t("log-retry-title"))}">↻</button>`:"",F=!v,A=_e.has(r.id)?"checked":"",g=F?`<input type="checkbox" class="erp-log-cb" data-log-cb="${escapeHtml(r.id)}" ${A}>`:'<span class="erp-log-cb-spacer"></span>',f=(r.ocr_buyer_name||"").trim()||(r.client_name||"").trim(),h=f?`<span class="log-client" title="${escapeHtml(f)}">${escapeHtml(f.substring(0,18))}</span>`:`<span class="log-client log-client-empty" title="${escapeHtml(t("erp-log-client-unassigned-tip"))}">${escapeHtml(t("erp-log-client-unassigned"))}</span>`,I=r.workspace_name?`<span class="log-workspace">${escapeHtml((r.workspace_name||"").substring(0,16))}</span>`:`<span class="log-workspace log-workspace-unresolved" title="${escapeHtml(t("erp-log-ws-unresolved-tip"))}">${escapeHtml(t("erp-log-ws-unresolved"))}</span>`,L=r.endpoint_name?`<span class="log-erp">${escapeHtml((r.endpoint_name||"").substring(0,14))}</span>`:`<span class="log-erp log-erp-deleted">${escapeHtml(t("erp-log-endpoint-deleted"))}</span>`,$=(r.external_doc_no||"").trim(),E=(r.external_url||"").trim();let M;return E?M=`<span class="log-doc"><a href="${escapeHtml(E)}" target="_blank" rel="noopener" class="log-doc-open" title="${escapeHtml($||"")}">${escapeHtml(t("erp-log-doc-open"))}</a></span>`:$?M=`<span class="log-doc log-doc-copy" data-copy-doc="${escapeHtml($)}" title="${escapeHtml(t("erp-log-doc-copy-tip"))}">${escapeHtml($.substring(0,18))}</span>`:r.status==="success"?M=`<span class="log-doc log-doc-missing" title="${escapeHtml(t("erp-log-doc-missing-tip"))}">${escapeHtml(t("erp-log-doc-missing"))}</span>`:M='<span class="log-doc log-doc-empty">-</span>',`
                <div class="erp-log-row ${x}" data-log-detail="${escapeHtml(r.id)}">
                    ${g}
                    <span class="log-time">${c}</span>
                    <span class="log-status" title="${escapeHtml(q+(k?" · "+k:""))}">${_}</span>
                    ${j}
                    <span class="log-invoice">${escapeHtml(r.invoice_no||"-")}</span>
                    ${I}
                    ${h}
                    <span class="log-seller">${escapeHtml((r.seller_name||"").substring(0,20))}</span>
                    ${L}
                    ${M}
                    <span class="log-http">HTTP ${r.http_status||"-"}</span>
                    <span class="log-elapsed">${r.elapsed_ms}ms</span>
                    <span class="log-actions">${R}</span>
                </div>
            `}).join("");const i=new Set(p.map(r=>r.id));for(const r of Array.from(_e))i.has(r)||_e.delete(r);window._refreshErpBatchBar()}catch(a){console.error("load erp logs failed",a),n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}async function It(e){try{const n=await fetch(`/api/erp/logs/${encodeURIComponent(e)}/retry`,{method:"POST",headers:{Authorization:"Bearer "+token}}),a=await n.json().catch(()=>({}));n.ok&&a.ok?showToast(t("log-retry-ok"),"success"):showToast(t("log-retry-fail")+" · HTTP "+(a.http_status||n.status),"error"),Pe(),window.loadErpEndpoints()}catch{showToast(t("log-retry-fail"),"error")}}(function(){document.getElementById("btn-add-endpoint").addEventListener("click",()=>window.openEndpointModal(null)),document.getElementById("endpoint-modal-close").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-cancel").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-test").addEventListener("click",window.testEndpointConnection),document.getElementById("btn-ep-save").addEventListener("click",window.saveEndpoint),document.getElementById("ep-url").addEventListener("blur",n=>{const a=window._sanitizeUrl(n.target.value);a!==n.target.value.trim()&&(n.target.value=a)}),document.addEventListener("click",n=>{const a=n.target.closest("[data-ep-edit]"),o=n.target.closest("[data-ep-del]");a&&window.openEndpointModal(a.dataset.epEdit),o&&window.deleteEndpoint(o.dataset.epDel);const s=n.target.closest("[data-log-retry]");if(s){n.stopPropagation(),It(s.dataset.logRetry);return}const p=n.target.closest("[data-log-cb]");if(p){n.stopPropagation();const d=p.dataset.logCb;p.checked?_e.add(d):_e.delete(d),window._refreshErpBatchBar();return}const l=n.target.closest("[data-log-select-all]");if(l){n.stopPropagation();const d=l.checked;document.querySelectorAll("[data-log-cb]").forEach(function(v){v.checked=d;const x=v.dataset.logCb;d?_e.add(x):_e.delete(x)}),window._refreshErpBatchBar();return}if(n.target.closest("#btn-erp-batch-retry")){n.stopPropagation(),window._runErpBatchRetry();return}if(n.target.closest("#btn-erp-batch-clear")){n.stopPropagation(),_e.clear(),document.querySelectorAll(".erp-log-cb").forEach(d=>{d.checked=!1}),window._refreshErpBatchBar();return}const y=n.target.closest("[data-log-detail]");if(y){if(n.target.closest("[data-log-cb]"))return;const d=n.target.closest("[data-copy-doc]");if(d){n.stopPropagation(),window.copyErpDocNo(d.dataset.copyDoc);return}if(n.target.closest(".log-doc-open"))return;window.showLogDetail(y.dataset.logDetail);return}const i=n.target.closest(".chip-filter");if(i){document.querySelectorAll("#erp-logs-filters .chip-filter").forEach(d=>d.classList.remove("active")),i.classList.add("active"),Be={key:i.dataset.filterKey,val:i.dataset.filterVal},Pe();return}if(n.target.closest("#btn-refresh-logs")){const d=n.target.closest("#btn-refresh-logs");d.classList.add("spinning"),setTimeout(()=>d.classList.remove("spinning"),600),Pe();return}const r=n.target.closest(".auto-nav-item");if(r&&r.dataset.autoTab){switchAutomationTab(r.dataset.autoTab);return}})})();window.loadErpLogs=Pe;window.retryPushLog=It;function Lt(){const e=document.getElementById("erp-logs-batch-bar"),n=document.getElementById("erp-logs-batch-count"),a=document.querySelector("[data-log-select-all]");if(a){const p=document.querySelectorAll("[data-log-cb]").length,l=window._erpSelected.size;l===0?(a.checked=!1,a.indeterminate=!1):l>=p?(a.checked=!0,a.indeterminate=!1):(a.checked=!1,a.indeterminate=!0)}if(!e||!n)return;const o=window._erpSelected.size;if(o===0){e.style.display="none";return}e.style.display="",n.textContent=t("erp-batch-selected",{n:o})}async function Ct(){console.info("[ErpBatch] retry triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-confirm",{n:e.length})))try{const a=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!a.ok){showToast(t("erp-logs-error"),"error");return}const o=await a.json(),s=t("erp-batch-result",{ok:o.succeeded||0,fail:o.failed||0,skip:o.skipped||0}),p=o.failed&&o.failed>0?"warn":"success";showToast(s,p),window._erpSelected.clear(),window.loadErpLogs()}catch(a){console.error("batch retry failed",a),showToast(t("erp-logs-error"),"error")}}async function St(){console.info("[ErpBatch] delete triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-delete-confirm",{n:e.length}),{danger:!0}))try{const o=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!o.ok){showToast(t("erp-logs-error"),"error");return}const s=await o.json();e.forEach(function(p){var l=document.querySelector('[data-log-detail="'+p+'"]');l&&l.remove()});var a=document.getElementById("erp-logs-batch-bar");a&&(a.style.display="none"),showToast(t("erp-batch-delete-result",{n:s.deleted||0,skip:s.skipped||0}),s.deleted>0?"success":"warn"),window._erpSelected.clear(),setTimeout(window.loadErpLogs,500)}catch(o){console.error("batch delete failed",o),showToast(t("erp-logs-error"),"error")}}(function(){function n(){var a=document.getElementById("btn-erp-batch-retry"),o=document.getElementById("btn-erp-batch-delete"),s=document.getElementById("btn-erp-batch-clear");a&&!a.dataset.boundDirect&&(a.addEventListener("click",function(p){p.preventDefault(),p.stopPropagation(),Ct()}),a.dataset.boundDirect="1"),o&&!o.dataset.boundDirect&&(o.addEventListener("click",function(p){p.preventDefault(),p.stopPropagation(),St()}),o.dataset.boundDirect="1"),s&&!s.dataset.boundDirect&&(s.addEventListener("click",function(p){p.preventDefault(),p.stopPropagation(),window._erpSelected.clear(),document.querySelectorAll(".erp-log-cb").forEach(function(l){l.checked=!1}),Lt()}),s.dataset.boundDirect="1")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n(),setTimeout(n,2e3),setTimeout(n,5e3),window._bindErpBatchButtons=n})();window._refreshErpBatchBar=Lt;window._runErpBatchRetry=Ct;window._runErpBatchDelete=St;(function(){let e=null,n=!1;function a(){if(e)return e;const y=document.createElement("div");y.id="line-email-modal",y.style.cssText="position:fixed;inset:0;background:rgba(10,14,39,0.85);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;",y.innerHTML=`
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
        `,document.body.appendChild(y),e=y;const i=y.querySelector("#line-email-input"),r=y.querySelector("#line-email-submit-btn"),d=y.querySelector("#line-email-err");async function c(){d.textContent="";const v=(i.value||"").trim().toLowerCase();if(!v||v.indexOf("@")<0||v.split("@")[1].indexOf(".")<0){d.textContent=t("line-email-err-invalid");return}r.disabled=!0,r.style.opacity="0.6";try{const x=await fetch("/api/me/line_complete_email",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},body:JSON.stringify({email:v})});if(!x.ok)throw new Error("http_"+x.status);const _=await x.json();_.token&&localStorage.setItem("mrpilot_token",_.token),typeof showToast=="function"&&showToast(_.merged?t("line-email-merged-toast"):t("line-email-saved-toast"),"success"),setTimeout(function(){window.location.reload()},600)}catch{d.textContent=t("line-email-err-failed"),r.disabled=!1,r.style.opacity="1"}}return r.addEventListener("click",c),i.addEventListener("keydown",function(v){v.key==="Enter"&&c()}),y}function o(){if(!e)return;const y=e.querySelector("#line-email-title-h"),i=e.querySelector("#line-email-sub-p"),r=e.querySelector("#line-email-input"),d=e.querySelector("#line-email-submit-btn");y&&(y.textContent=t("line-email-title")),i&&(i.textContent=t("line-email-sub")),r&&(r.placeholder=t("line-email-placeholder")),d&&(d.textContent=t("line-email-submit"))}function s(){a(),o(),e.style.display="flex",n=!0;const y=e.querySelector("#line-email-input");y&&setTimeout(function(){y.focus()},100)}async function p(){const y=localStorage.getItem("mrpilot_token");if(y)try{const i=await fetch("/api/me/needs_email",{headers:{Authorization:"Bearer "+y}});if(!i.ok)return;const r=await i.json();r&&r.needs_email&&s()}catch{}}function l(){setTimeout(p,800)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",l):l(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("line-email-modal",function(){n&&o()})})();(function(){function e(d){let c=0;return d.length>=8&&c++,d.length>=12&&c++,/[a-zA-Z]/.test(d)&&/\d/.test(d)&&c++,/[^a-zA-Z0-9]/.test(d)&&c++,Math.min(3,c)}function n(d,c){const v=document.getElementById("cpw-msg");v&&(v.textContent=d,v.className="cpw-msg "+(c||""))}function a(d){return typeof t=="function"?t(d):d}let o=!1;function s(){["cpw-old","cpw-new","cpw-confirm"].forEach(c=>{const v=document.getElementById(c);v&&(v.value="",v.setAttribute("readonly","readonly"))});const d=document.getElementById("cpw-strength-bar");d&&(d.style.width="0%",d.className="cpw-strength-bar"),n("","")}async function p(){const d=document.getElementById("btn-change-pw"),c=document.getElementById("cpw-old"),v=document.getElementById("cpw-new"),x=document.getElementById("cpw-confirm"),_=document.getElementById("cpw-strength-bar");if(!d||!c||!v||!x)return;const q=c.value,j=v.value,k=x.value;if(!q||!j||!k){n(a("settings-change-pw-empty"),"error");return}if(j.length<8){n(a("settings-change-pw-too-short"),"error");return}if(!(/[a-zA-Z]/.test(j)&&/\d/.test(j))){n(a("settings-change-pw-too-weak"),"error");return}if(j!==k){n(a("settings-change-pw-mismatch"),"error");return}d.disabled=!0;const B=d.textContent;d.textContent=a("settings-change-pw-submitting"),n("","");try{const N=localStorage.getItem("mrpilot_token"),R=await fetch("/api/me/change_password",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+N},body:JSON.stringify({old_password:q,new_password:j})}),F=await R.json().catch(()=>({}));if(R.ok&&F.ok)n(a("settings-change-pw-success"),"success"),typeof showToast=="function"&&showToast(a("settings-change-pw-success"),"success"),c.value="",v.value="",x.value="",_&&(_.style.width="0%",_.className="cpw-strength-bar");else{const A=F.detail||"";let g=a("settings-change-pw-success");A==="wrong_old_password"?g=a("settings-change-pw-wrong-old"):A==="password_too_short"?g=a("settings-change-pw-too-short"):A==="password_too_weak"?g=a("settings-change-pw-too-weak"):g=A||"Error",n(g,"error")}}catch(N){console.error("change_password",N),n("Network error","error")}finally{d.disabled=!1,d.textContent=B}}function l(){o||(o=!0,document.addEventListener("click",d=>{if(!d.target||!d.target.closest)return;const c=d.target.closest(".cpw-eye");if(c){const v=document.getElementById(c.dataset.target);v&&(v.type=v.type==="password"?"text":"password");return}if(d.target.closest("#cpw-forgot-link")){d.preventDefault(),y();return}if(d.target.closest("#btn-change-pw")){p();return}d.target.closest('.settings-nav-item[data-settings-tab="account"], .settings-nav-item[data-tab="account"], .settings-nav-item[data-tab="security"]')&&setTimeout(s,100)}),document.addEventListener("input",d=>{if(d.target&&d.target.id==="cpw-new"){const c=document.getElementById("cpw-strength-bar");if(!c)return;const v=e(d.target.value),x=["0%","33%","66%","100%"],_=["","weak","medium","strong"];c.style.width=x[v],c.className="cpw-strength-bar "+_[v]}}),document.addEventListener("focusin",d=>{d.target&&["cpw-old","cpw-new","cpw-confirm"].includes(d.target.id)&&d.target.removeAttribute("readonly")}),document.getElementById("cpw-old")&&s())}function y(){const d=window._userInfo||(typeof _userInfo<"u"?_userInfo:null),c=d&&d.username?d.username:"",v=i(c);let x=document.getElementById("cpw-forgot-overlay");x&&x.remove(),x=document.createElement("div"),x.id="cpw-forgot-overlay",x.className="cpw-forgot-overlay",x.innerHTML=`
            <div class="cpw-forgot-modal">
                <div class="cpw-forgot-head">
                    <div class="cpw-forgot-title">${r(a("cpw-forgot-title"))}</div>
                    <button class="cpw-forgot-close" id="cpw-forgot-close" aria-label="close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="cpw-forgot-body">
                    <p class="cpw-forgot-desc">${r(a("cpw-forgot-desc"))}</p>
                    <div class="cpw-forgot-email">${r(v)}</div>
                    <p class="cpw-forgot-tip">${r(a("cpw-forgot-tip"))}</p>
                    <div class="cpw-forgot-msg" id="cpw-forgot-msg"></div>
                </div>
                <div class="cpw-forgot-foot">
                    <button class="btn btn-ghost" id="cpw-forgot-cancel">${r(a("cpw-forgot-cancel"))}</button>
                    <button class="btn btn-primary" id="cpw-forgot-send">${r(a("cpw-forgot-send"))}</button>
                </div>
            </div>
        `,document.body.appendChild(x);const _=()=>x.remove();x.querySelector("#cpw-forgot-close").addEventListener("click",_),x.querySelector("#cpw-forgot-cancel").addEventListener("click",_),x.addEventListener("click",q=>{q.target===x&&_()}),x.querySelector("#cpw-forgot-send").addEventListener("click",async()=>{const q=x.querySelector("#cpw-forgot-send"),j=x.querySelector("#cpw-forgot-msg");q.disabled=!0;const k=q.textContent;q.textContent=a("cpw-forgot-sending");try{const B=await fetch("/api/auth/forgot_password",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:c})}),N=await B.json().catch(()=>({}));B.ok?(j.textContent=a("cpw-forgot-success"),j.className="cpw-forgot-msg success",q.style.display="none",x.querySelector("#cpw-forgot-cancel").textContent=a("cpw-forgot-close-btn")):(j.textContent=N.detail||a("cpw-forgot-fail"),j.className="cpw-forgot-msg error",q.disabled=!1,q.textContent=k)}catch{j.textContent=a("cpw-forgot-fail"),j.className="cpw-forgot-msg error",q.disabled=!1,q.textContent=k}})}function i(d){if(!d||!d.includes("@"))return d||"";const[c,v]=d.split("@");return c.length<=2?c+"****@"+v:c.slice(0,2)+"****@"+v}function r(d){return d==null?"":String(d).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c])}document.readyState==="complete"||document.readyState==="interactive"?l():document.addEventListener("DOMContentLoaded",l)})();(function(){let e=null,n=!1;async function a(){if(n)return;const s=localStorage.getItem("mrpilot_token");if(s){n=!0;try{const p=await fetch("/api/me",{headers:{Authorization:"Bearer "+s},cache:"no-store"});if(p.status===401){const l=await p.json().catch(()=>({})),y=l&&l.detail;let i="";if(typeof y=="string"?i=y:y&&typeof y=="object"&&(i=y.code||""),console.warn("[heartbeat] session revoked",i),localStorage.removeItem("mrpilot_token"),e&&(clearInterval(e),e=null),i==="auth.session_revoked")try{_showSessionRevokedModal()}catch{window.location.href="/"}else{const r=i==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";try{typeof showToast=="function"&&typeof t=="function"?showToast(t(r),"error"):alert("Session expired")}catch{}setTimeout(()=>{window.location.href="/"},1500)}}}catch{}finally{n=!1}}}function o(){e&&clearInterval(e),e=setInterval(a,15e3)}localStorage.getItem("mrpilot_token")&&o(),window.addEventListener("focus",a),document.addEventListener("visibilitychange",function(){document.hidden||a()}),window._sessionCheck=a})();async function Ve(){const e=document.getElementById("team-loading"),n=document.getElementById("team-list"),a=document.getElementById("team-empty"),o=document.getElementById("team-count");if(n){e&&(e.style.display=""),n.style.display="none",a&&(a.style.display="none");try{const s=await apiGet("/api/team/employees"),p=s&&s.employees||[];if(e&&(e.style.display="none"),o&&(o.textContent=(t("team-count")||"共 {n} 名员工").replace("{n}",p.length)),p.length===0){a&&(a.style.display="");return}n.style.display="",n.innerHTML=p.map(l=>{const y=l.last_login_at?new Date(l.last_login_at).toLocaleDateString():t("team-never-login")||"从未登录",i=l.is_active===!1?"team-status-off":"team-status-on",r=l.is_active===!1?t("team-status-disabled")||"已禁用":t("team-status-active")||"正常",d=l.email?`<span class="team-meta-sep">·</span><span>${escapeHtml(l.email)}</span>`:"";return`
            <div class="team-card" data-employee-id="${escapeHtml(l.id)}">
                <div class="team-card-main">
                    <div class="team-avatar">${escapeHtml((l.username||"?")[0].toUpperCase())}</div>
                    <div class="team-info">
                        <div class="team-name">${escapeHtml(l.username||"")}</div>
                        <div class="team-meta">
                            <span class="team-status-dot ${i}"></span>
                            <span>${escapeHtml(r)}</span>
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml(t("team-last-login")||"上次登录")}: ${escapeHtml(y)}</span>
                            ${d}
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml((t("team-assigned-clients")||"已分配 {n} 客户").replace("{n}",l.assigned_client_count||0))}</span>
                        </div>
                    </div>
                </div>
                <div class="team-card-actions">
                    <button class="btn btn-ghost btn-small" data-assign-clients="${escapeHtml(l.id)}" data-name="${escapeHtml(l.username||"")}">
                        ${escapeHtml(t("team-assign-clients")||"分配客户")}
                    </button>
                    <button class="btn btn-ghost btn-small" data-reset-pwd-employee="${escapeHtml(l.id)}" data-name="${escapeHtml(l.username||"")}" title="${escapeHtml(t("team-reset-pwd")||"重置密码")}">
                        ${escapeHtml(t("team-reset-pwd")||"重置密码")}
                    </button>
                    <button class="btn btn-ghost btn-small" data-toggle-employee="${escapeHtml(l.id)}" data-active="${l.is_active===!1?"false":"true"}">
                        ${escapeHtml(l.is_active===!1?t("team-enable")||"启用":t("team-disable")||"禁用")}
                    </button>
                    <button class="btn btn-ghost btn-small btn-danger-text" data-remove-employee="${escapeHtml(l.id)}" data-name="${escapeHtml(l.username||"")}">
                        ${escapeHtml(t("team-remove")||"移除")}
                    </button>
                </div>
            </div>`}).join("")}catch(s){console.error("loadTeamList failed:",s),e&&(e.textContent=t("team-load-failed")||"加载失败")}}}async function mn(){document.querySelectorAll(".add-emp-overlay").forEach(o=>o.remove());const e=document.createElement("div");e.className="add-emp-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const o=document.getElementById("add-emp-username");o&&o.focus()},200);function n(){e.classList.remove("show"),setTimeout(()=>e.remove(),220)}e.querySelector(".add-emp-close").addEventListener("click",n),e.querySelector("#add-emp-cancel").addEventListener("click",n),e.addEventListener("click",o=>{o.target===e&&n()}),e.querySelector("#add-emp-submit").addEventListener("click",async()=>{const o=document.getElementById("add-emp-username"),s=document.getElementById("add-emp-email"),p=document.getElementById("add-emp-password"),l=document.getElementById("add-emp-msg"),y=document.getElementById("add-emp-submit"),i=(o.value||"").trim(),r=(s.value||"").trim(),d=p.value||"";if(l.textContent="",l.classList.remove("error"),!i||i.length<3){l.textContent=t("team-modal-err-username")||"用户名至少 3 位",l.classList.add("error");return}if(!/^[a-zA-Z0-9_.\-]+$/.test(i)){l.textContent=t("team-modal-err-username-fmt")||"只能用字母 / 数字 / 下划线 / 点 / 横线",l.classList.add("error");return}if(r&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(r)){l.textContent=t("msg-email-invalid")||"邮箱格式不对",l.classList.add("error");return}if(d.length<8){l.textContent=t("pwd-too-short")||"密码至少 8 位",l.classList.add("error");return}if(/^\d+$/.test(d)){l.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",l.classList.add("error");return}if(!(/[a-zA-Z]/.test(d)&&/\d/.test(d))){l.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",l.classList.add("error");return}y.disabled=!0,y.textContent=t("msg-saving")||"保存中...";try{const c={username:i,password:d};r&&(c.email=r);const v=await apiPost("/api/team/employees",c),x=v?await v.json().catch(()=>({})):{};if(v&&v.ok&&x&&x.ok){showToast(t("team-added")||"员工已添加","success"),n(),Ve();return}const _=x&&x.detail||"unknown",q={"team.username_exists":t("team-username-exists")||"用户名已被占用","team.email_exists":t("team-email-exists")||"邮箱已被占用","team.create_failed":t("team-create-failed")||"创建失败","team.only_owner_or_super":t("team-no-permission")||"无权限","team.no_tenant":t("team-no-tenant")||"请先升级账号","pwd.too_short":t("pwd-too-short")||"密码至少 8 位","pwd.too_weak_numeric":t("pwd-too-weak-numeric")||"不能是纯数字","pwd.too_weak_common":t("pwd-too-weak-common")||"这个密码太常见 · 请换一个","pwd.too_weak":t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};l.textContent=q[_]||(t("team-create-failed")||"创建失败")+" ("+_+")",l.classList.add("error")}catch{l.textContent=t("team-create-failed")||"创建失败",l.classList.add("error")}finally{y.disabled=!1,y.textContent=t("team-add")||"添加员工"}});function a(o){o.key==="Escape"&&(n(),document.removeEventListener("keydown",a))}document.addEventListener("keydown",a)}async function hn(e,n){try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}/active`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({is_active:!!n})})).ok){Ve();return}showToast(t("team-toggle-failed")||"操作失败","error")}catch{showToast(t("team-toggle-failed")||"操作失败","error")}}async function gn(e,n){const o=(t("team-confirm-remove")||"确认移除员工「{name}」?他的所有识别记录会保留 · 但他将无法登录").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{danger:!0,okText:t("team-remove")}))try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){showToast(t("team-removed")||"已移除","success"),Ve();return}showToast(t("team-remove-failed")||"移除失败","error")}catch{showToast(t("team-remove-failed")||"移除失败","error")}}async function bn(e,n){const o=(t("team-reset-pwd-confirm")||"给员工「{name}」发送改密链接?系统将通过员工的邮箱或 LINE 发送一个 15 分钟内有效的链接 · 员工自己点链接改密码 · 您看不到密码").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{okText:t("team-reset-link-send-btn")||"发送链接"}))try{const p=await fetch(`/api/team/employees/${encodeURIComponent(e)}/reset-password`,{method:"POST",headers:{Authorization:"Bearer "+token}}),l=await p.json().catch(()=>({}));if(p.status===400&&l.detail==="team.reset_no_channel"){showToast(t("team-reset-no-channel")||"员工尚未绑定邮箱或 LINE · 请先帮员工补充邮箱再重置","error");return}if(!p.ok){showToast(t("team-reset-pwd-fail")||"发送失败","error");return}if(l.channel==="line"||l.channel==="email"){const y=t("team-reset-link-sent")||"改密链接已通过 {ch} 发送给员工 · 链接 15 分钟内有效",i=l.channel==="line"?"LINE":t("team-reset-via-email")||"邮箱";showToast(y.replace("{ch}",i),"success");return}showToast(t("team-reset-pwd-fail")||"发送失败","error")}catch{showToast(t("team-reset-pwd-fail")||"发送失败","error")}}document.addEventListener("click",e=>{if(e.target.closest("#btn-add-employee")){e.preventDefault(),mn();return}const n=e.target.closest("[data-toggle-employee]");if(n){e.preventDefault(),hn(n.dataset.toggleEmployee,n.dataset.active==="false");return}const a=e.target.closest("[data-remove-employee]");if(a){e.preventDefault(),gn(a.dataset.removeEmployee,a.dataset.name||"");return}const o=e.target.closest("[data-reset-pwd-employee]");if(o){e.preventDefault(),bn(o.dataset.resetPwdEmployee,o.dataset.name||"");return}const s=e.target.closest("[data-assign-clients]");if(s){e.preventDefault(),typeof window.openAssignClientsModal=="function"&&window.openAssignClientsModal(s.dataset.assignClients,s.dataset.name||"");return}});window.loadTeamList=Ve;function yn(e){document.querySelectorAll(".auto-nav-item").forEach(n=>{n.classList.toggle("active",n.dataset.autoTab===e)}),document.querySelectorAll(".auto-panel").forEach(n=>{n.classList.toggle("active",n.dataset.autoPanel===e)}),e==="email"&&typeof window._loadEmailIngestPanel=="function"?(window._loadEmailIngestPanel(),typeof window._startEmailLogAutoRefresh=="function"&&window._startEmailLogAutoRefresh()):typeof window._stopEmailLogAutoRefresh=="function"&&window._stopEmailLogAutoRefresh(),e==="bank"&&typeof window._loadBankReconPanel=="function"&&window._loadBankReconPanel(),e==="linebot"&&typeof window._loadLineBotPanel=="function"&&window._loadLineBotPanel(),e==="alert"&&typeof window._loadNotificationsPanel=="function"&&window._loadNotificationsPanel(),e==="folder"&&typeof window._loadFolderWatcherPanel=="function"&&window._loadFolderWatcherPanel()}window.switchAutomationTab=yn;typeof console<"u"&&typeof console.info=="function"&&console.info("[pearnly] vite bundle loaded · dashboard + billing + test-center + workspace-switcher + recon-center + assign-clients + access-log + notifications + recon-batch + welcome-wizard + archive-settings");
//# sourceMappingURL=main.js.map
