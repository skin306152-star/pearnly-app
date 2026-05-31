const cn=`
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

`,dn=`        <!-- ── 销项税对账面板(v118.32.0 · 屏 A) ── -->
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


`;(function(){const e=document.getElementById("page-reconcile");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=cn+dn,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=document.getElementById("page-integrations");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const pn=`
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

`,un=`                    <!-- Tab: 邮箱抓取 (v0.17 · M6 · v93 在 Vultr 复活) -->
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
`;(function(){const e=document.getElementById("page-automation");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=pn+un,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e={"page-integration":`
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
`},n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;Object.keys(e).forEach(o=>{const s=document.getElementById(o);!s||s.dataset.wbInjected==="1"||(s.innerHTML=e[o],s.dataset.wbInjected="1",a&&a[n]&&s.querySelectorAll("[data-i18n]").forEach(p=>{const r=p.getAttribute("data-i18n");a[n][r]&&(p.textContent=a[n][r])}))})})();(function(){const e=document.getElementById("page-dashboard");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();function fn(e,n){const a=document.getElementById("alert-"+e);a&&(document.getElementById("alert-"+e+"-text").textContent=n,a.classList.add("show"))}function mn(){["info","warn","error"].forEach(e=>{document.getElementById("alert-"+e).classList.remove("show")})}function vn(e,n){if(e==null)return n||"操作失败";if(typeof e=="string")return e;if(Array.isArray(e)){const a=e[0]||{};return a.msg?a.msg:n||"请求格式错误"}if(typeof e=="object"){if(e.code){const a="err."+e.code;try{const o=t(a,e);if(o&&o!==a)return o}catch(o){console.warn("[i18n] t() failed for key:",a,o)}return e.code}if(e.message)return e.message;if(e.error)return e.error;if(e.detail&&typeof e.detail=="string")return e.detail;try{return JSON.stringify(e).slice(0,160)}catch{}}return n||String(e)}function hn(e){if(!e)return"";const n=String(e);return/ECONNREFUSED|Connection refused/i.test(n)?"连接被拒绝 · ERP 地址可能错了,或服务没启动":/listing fetch failed|wait_for_selector/i.test(n)?"拉取 MR.ERP 客户/商品列表超时 · 已重试 3 次仍不通 · 可能 MR.ERP 响应慢 · 稍后再试":/ETIMEDOUT|timeout/i.test(n)?"连接超时 · MR.ERP 响应慢 · 稍后再试":/ENOTFOUND|getaddrinfo/i.test(n)?"域名解析失败 · ERP 地址拼错了":/certificate|SSL/i.test(n)?"SSL 证书问题 · ERP 站点证书异常":/401|Unauthorized/i.test(n)?"HTTP 401 · 认证失败,检查 Token 是否正确":/403|Forbidden/i.test(n)?"HTTP 403 · 权限不足,ERP 拒绝访问":/404|Not Found/i.test(n)?"HTTP 404 · URL 路径不存在":/^5\d\d/.test(n)||/500|502|503|504/.test(n)?"ERP 服务器错误 · 不是你的问题,等会儿再试":n}function gn(e,n,a){let o=document.getElementById("mp-toast-wrap");o||(o=document.createElement("div"),o.id="mp-toast-wrap",document.body.appendChild(o)),n=n||"success",n==="ok"&&(n="success"),n==="warning"&&(n="warn"),n==="danger"&&(n="error");const s={success:'<path d="M3 8l3 3 7-7"/>',error:'<circle cx="8" cy="8" r="6"/><path d="M5.5 5.5l5 5M10.5 5.5l-5 5"/>',warn:'<path d="M8 2L1.5 13h13L8 2z"/><path d="M8 7v3M8 12v.01"/>',info:'<circle cx="8" cy="8" r="6"/><path d="M8 5.5v.01M8 8v3"/>',loading:'<path d="M8 1a7 7 0 017 7" stroke-linecap="round" class="mp-toast-spin"/>'},p=document.createElement("div");p.className="mp-toast "+n,p.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            ${s[n]||s.success}
        </svg>
        <span>${escapeHtml(e)}</span>
    `,o.appendChild(p),requestAnimationFrame(()=>p.classList.add("show"));const r=typeof a=="number"?a:2500;let f=null;const i=()=>{f&&(clearTimeout(f),f=null),p.classList.remove("show"),setTimeout(()=>{try{p.remove()}catch{}},300)};return r>0&&(f=setTimeout(i,r)),i}window.showAlert=fn;window.hideAlerts=mn;window._humanizeBackendError=vn;window.humanizeError=hn;window.showToast=gn;function bn(e){if(e){try{if(typeof shouldHideMoney=="function"&&shouldHideMoney(_userInfo)&&["team","api","plan","company"].indexOf(e)>=0){e="profile";try{localStorage.setItem("mrpilot_settings_tab","profile")}catch{}}}catch{}document.querySelectorAll(".settings-tab").forEach(n=>{n.classList.toggle("active",n.dataset.tab===e)}),document.querySelectorAll(".settings-pane").forEach(n=>{n.classList.toggle("active",n.dataset.pane===e)});try{localStorage.setItem("mrpilot_settings_tab",e)}catch{}try{e==="about"&&typeof window.loadAboutPanel=="function"&&window.loadAboutPanel(),e==="notifications"&&typeof window.loadPrefsSettings=="function"&&window.loadPrefsSettings(),e==="team"&&loadTeamList(),e==="learned"&&typeof window.loadLearnedRules=="function"&&window.loadLearnedRules(),e==="plan"&&typeof lt=="function"&&lt()}catch(n){console.warn("settings tab side effect failed:",n)}}}function yn(e){if(!e)return;const n=(a,o)=>{const s=document.getElementById(a);s&&(s.value=o||"")};n("profile-username",e.username||""),n("profile-email",e.username||""),n("profile-fullname",e.full_name||""),n("profile-phone",e.phone||""),n("profile-country",e.country||"TH"),n("profile-line",e.line_id||""),n("company-name",e.company_name||""),n("company-volume",e.monthly_volume||""),n("company-role",e.user_role||e.role_self||"")}async function wn(){const e=document.getElementById("btn-save-profile"),n=document.getElementById("profile-save-msg");if(!e)return;const a=e.innerHTML;e.disabled=!0,e.innerHTML=`<span>${t("msg-saving")||"保存中..."}</span>`,n&&(n.textContent="",n.classList.remove("error"));try{const o={full_name:(document.getElementById("profile-fullname")||{}).value||"",phone:(document.getElementById("profile-phone")||{}).value||"",country:(document.getElementById("profile-country")||{}).value||"TH",line_id:(document.getElementById("profile-line")||{}).value||""},s=await apiPut("/api/me/profile",o);if(s&&s.ok){n&&(n.textContent=t("msg-saved")||"已保存");try{const p=await apiGet("/api/me");_userInfo=p;try{window._userInfo=p}catch{}renderBrandWorkspace()}catch{}}else throw new Error("save failed")}catch{n&&(n.textContent=t("msg-save-failed")||"保存失败",n.classList.add("error"))}finally{e.disabled=!1,e.innerHTML=a,setTimeout(()=>{n&&(n.textContent="")},3e3)}}async function kn(){const e=document.getElementById("btn-save-company"),n=document.getElementById("company-save-msg");if(!e)return;const a=e.innerHTML;e.disabled=!0,e.innerHTML=`<span>${t("msg-saving")||"保存中..."}</span>`,n&&(n.textContent="",n.classList.remove("error"));try{const o={company_name:(document.getElementById("company-name")||{}).value||"",monthly_volume:(document.getElementById("company-volume")||{}).value||"",role:(document.getElementById("company-role")||{}).value||""},s=await apiPut("/api/me/profile",o);if(s&&s.ok){n&&(n.textContent=t("msg-saved")||"已保存");try{const p=await apiGet("/api/me");_userInfo=p;try{window._userInfo=p}catch{}renderBrandWorkspace()}catch{}}else throw new Error("save failed")}catch{n&&(n.textContent=t("msg-save-failed")||"保存失败",n.classList.add("error"))}finally{e.disabled=!1,e.innerHTML=a,setTimeout(()=>{n&&(n.textContent="")},3e3)}}function lt(){if(!_userInfo)return;typeof window.loadAboutPanel=="function"&&window.loadAboutPanel(),typeof window.loadPrefsSettings=="function"&&window.loadPrefsSettings();const e=document.getElementById("settings-info");if(!e)return;const n=_userInfo;if(n.is_super_admin){e.innerHTML=`
            <table style="width:100%; font-size:13px; border-collapse: collapse;">
                <tr><td style="color:#a0aec0; padding:8px 0; width:120px;">${t("settings-username")}</td><td style="padding:8px 0;">${escapeHtml(n.username)}</td></tr>
                <tr><td style="color:#a0aec0; padding:8px 0;">${t("settings-role")}</td><td style="padding:8px 0;"><strong style="color:#d97706;">🛡️ ${escapeHtml(t("settings-role-super-admin"))}</strong></td></tr>
            </table>
        `;const o=document.getElementById("api-key-card");o&&(o.style.display="");return}_n(n,e);const a=document.getElementById("api-key-card");if(a){const o=tt==="byo_api"||_userInfo&&_userInfo.is_super_admin;a.style.display=o?"":"none"}}function _n(e,n){const a=escapeHtml(e.username||e.email||"");n.innerHTML=`
        <table style="width:100%; font-size:13px; border-collapse: collapse;">
            <tr>
                <td style="color:#a0aec0; padding:8px 0; width:140px;">${escapeHtml(t("settings-username"))}</td>
                <td style="padding:8px 0;">${a}</td>
            </tr>
            <tr>
                <td style="color:#a0aec0; padding:8px 0;">${escapeHtml(t("settings-billing-mode-title"))}</td>
                <td style="padding:8px 0;"><strong>${escapeHtml(t("settings-billing-mode"))}</strong></td>
            </tr>
            <tr>
                <td colspan="2" style="color:#a0aec0; padding:8px 0; font-size:12px;">
                    ${escapeHtml(t("settings-billing-pricing"))}
                </td>
            </tr>
        </table>
    `}window.switchSettingsTab=bn;window.fillSettingsForms=yn;window.saveProfile=wn;window.saveCompany=kn;window.renderSettings=lt;function We(e){return e=e||_userInfo,!!(e&&e.is_super_admin)}function ut(e){return e=e||_userInfo,!!e&&(e.role==="owner"||We(e))}function Ct(e){return e=e||_userInfo,!!e&&e.role==="member"&&!We(e)}function xn(e){return e=e||_userInfo,!!e&&(e.effective_plan==="trial"||e.plan==="trial")&&!We(e)}function St(e){return e=e||_userInfo,!!e&&e.tenant_type==="byo_api"}function Tt(e){return Ct(e)}function En(e){return ut(e)}function Bn(e){return ut(e)&&St(e)}window.isMoneyHidden=Tt;window.isSuperAdmin=We;window.isOwner=ut;window.isEmployee=Ct;window.isTrial=xn;window.isLifetime=St;window.shouldHideMoney=Tt;window.canManageTeam=En;window.canManageApiKey=Bn;function In(){const e=document.getElementById("quota-banner");if(!e)return;if(!_userInfo){e.style.display="none";return}if(_userInfo.is_super_admin||_userInfo.tenant_type==="admin"||_userInfo.tenant_type==="byo_api"){e.style.display="none";return}let n=0,a=0;if(_userInfo.plan==="free"&&_quota&&_quota.ip_daily_limit)n=_quota.ip_used_today||0,a=_quota.ip_daily_limit;else if(_userInfo.tenant_quota!=null&&_userInfo.tenant_quota>0)n=_userInfo.tenant_used||0,a=_userInfo.tenant_quota;else if(_userInfo.monthly_quota&&_userInfo.monthly_quota>0)n=_userInfo.used_this_month||0,a=_userInfo.monthly_quota;else{e.style.display="none";return}if(a<=0){e.style.display="none";return}const o=Math.max(0,a-n),s=n/a*100,p="quota_banner_dismiss_"+new Date().toISOString().slice(0,10);if(localStorage.getItem(p)){e.style.display="none";return}let r,f;if(o===0)r="danger",f=t("quota-banner-exhausted");else if(s>=90)r="danger",f=t("quota-banner-very-low",{n:o});else if(s>=70)r="warn",f=t("quota-banner-low",{n:o});else{e.style.display="none";return}e.className="quota-banner "+r,e.innerHTML=`
        <span class="quota-banner-icon">${svgIcon("alert",18)}</span>
        <span class="quota-banner-msg">${escapeHtml(f)}</span>
        <button type="button" class="quota-banner-close" aria-label="dismiss" title="${escapeHtml(t("quota-banner-dismiss"))}">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
        </button>
    `,e.style.display="flex";const i=e.querySelector(".quota-banner-close");i&&i.addEventListener("click",()=>{localStorage.setItem(p,"1"),e.style.display="none"})}function Ln(){const e=_userInfo;if(!e)return;const n=shouldHideMoney(e),a=canManageTeam(e),o=canManageApiKey(e),s=document.querySelector('.nav-item[data-route="templates"]');s&&(s.classList.remove("locked-for-plan"),s.removeAttribute("data-locked-target"));const p=document.querySelector('.nav-item[data-route="api-keys"]');p&&(p.classList.remove("locked-for-plan"),p.removeAttribute("data-locked-target"));const r=document.getElementById("btn-custom-template");r&&(r.style.display="",r.classList.remove("locked-for-plan"));const f=document.querySelector('.settings-tab[data-tab="team"]');f&&(f.style.display=a?"":"none");const i=document.querySelector('.settings-panel[data-settings-panel="team"]');i&&(i.dataset.permHidden=a?"0":"1");const c=document.querySelector('.settings-tab[data-tab="api"]');c&&(c.style.display=o||isSuperAdmin(e)?"":"none");const l=document.querySelector('.settings-tab[data-tab="plan"]');l&&(l.style.display=n?"none":"");const d=document.querySelector('.settings-tab[data-tab="company"]');d&&(d.style.display=n?"none":"");const u=document.getElementById("info-bar");u&&(u.style.display=n?"none":"");const g=document.getElementById("trial-banner");g&&n&&(g.style.display="none");const w=document.getElementById("plan-banner");w&&n&&(w.style.display="none",document.body.classList.remove("has-plan-banner")),document.querySelectorAll("[data-upgrade-cta], .btn-upgrade, .topbar-upgrade").forEach($=>{$.style.display="none"}),document.body.classList.toggle("role-employee",isEmployee(e)),document.body.classList.toggle("role-owner",isOwner(e)),document.body.classList.toggle("role-super",isSuperAdmin(e));try{const $=document.querySelector(".settings-tab.active");$&&$.style.display==="none"&&(typeof window.switchSettingsTab=="function"?window.switchSettingsTab("profile"):typeof switchSettingsTab=="function"&&switchSettingsTab("profile"))}catch($){console.warn("[v118.12.3] failed to fix active tab:",$)}if(window.PEARNLY_ADMIN_MODE){const $=document.getElementById("admin-mode-banner");$&&($.style.display="flex"),document.querySelectorAll(".nav-item").forEach(B=>{B.classList.contains("nav-admin-only")||(B.style.display="none")}),document.querySelectorAll(".nav-group").forEach(B=>{B.classList.contains("nav-group-admin-only")||(B.style.display="none")});const E=document.getElementById("client-switcher");E&&(E.style.display="none"),document.body.classList.add("admin-mode");const _=["profile","security","notifications","about"];document.querySelectorAll(".settings-tab").forEach(B=>{const q=B.dataset.tab;q&&!_.includes(q)&&(B.style.display="none")}),document.querySelectorAll(".settings-pane").forEach(B=>{const q=B.dataset.pane;q&&!_.includes(q)&&(B.style.display="none")}),document.querySelectorAll(".settings-nav-group").forEach(B=>{const q=B.querySelectorAll(".settings-tab");Array.from(q).some(F=>F.style.display!=="none")||(B.style.display="none")})}}function Cn(){const e=_userInfo,n=document.getElementById("info-bar");if(!e||shouldHideMoney(e)){n&&(n.innerHTML="");return}let a="";const o=e.tenant_type;if(o==="byo_api")e.has_own_gemini_key?a=`
                <div class="info-chip">
                    <span class="chip-value chip-value-lifetime">${escapeHtml(t("info-unlimited-own-key"))}</span>
                </div>
            `:a=`
                <div class="info-chip chip-warn">
                    <span class="chip-value">${escapeHtml(t("info-need-api-key"))}</span>
                </div>
            `;else if(o==="admin"||e.is_super_admin)a=`
            <div class="info-chip">
                <span class="chip-value chip-value-lifetime">${escapeHtml(t("info-unlimited-own-key"))}</span>
            </div>
        `;else{const s=e.tenant_used!=null?e.tenant_used:e.used_this_month||0,p=e.tenant_quota!=null&&e.tenant_quota>0?e.tenant_quota:e.monthly_quota||0,r=p>0?Math.min(100,s/p*100):0;let f="";r>=95?f="danger":r>=80&&(f="warn"),p>0?a=`
                <div class="info-chip">
                    <span class="chip-label">${escapeHtml(t("info-monthly"))}</span>
                    <span class="chip-value">${s} / ${p}</span>
                    <div class="mini-bar"><div class="mini-bar-fill ${f}" style="width:${r}%"></div></div>
                </div>
            `:a=""}n&&(n.innerHTML=a)}window.renderQuotaBanner=In;window.applySidebarVisibility=Ln;window.renderInfoBar=Cn;async function $t(e,n){try{const a=await fetch(e,{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(n)});if(a.status===401){localStorage.removeItem("mrpilot_token");const o=await a.json().catch(()=>({}));return(typeof o.detail=="string"?o.detail:o.detail&&o.detail.code||"")==="auth.session_revoked"?(_showSessionRevokedModal(),null):(window.location.href="/",null)}return await a.json()}catch{return{ok:!1,error:"network"}}}function Mt(e){return{invalid_format:"rd-err-format",not_found:"rd-err-not-found",rd_unreachable:"rd-err-unreachable",parse_error:"rd-err-unknown",network:"rd-err-unreachable"}[e]||"rd-err-unknown"}function Ge(e){const n=document.querySelector(`[data-field="${e}"]`);return n?(n.value||"").trim():""}function Ce(e,n,a){const o=document.querySelector(`[data-rd-status="${e}"]`);o&&(o.innerHTML=n,o.className="rd-status"+(a?" "+a:""))}async function Sn(e){const a=Ge(e==="seller"?"seller_tax":"buyer_tax");Ce(e,t("rd-verifying"),"loading");const o=await $t("/api/rd/verify",{tax_id:a});if(!o)return;if(!o.ok){Ce(e,t(Mt(o.error)),"error");return}o.data&&o.data.valid?Ce(e,`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t("rd-status-valid"))}`,"valid"):Ce(e,t("rd-status-invalid"),"invalid")}async function Tn(e){const a=Ge(e==="seller"?"seller_tax":"buyer_tax");Ce(e,t("rd-syncing"),"loading");const o=await $t("/api/rd/lookup",{tax_id:a,branch:0});if(o){if(!o.ok){Ce(e,t(Mt(o.error)),"error");return}Ce(e,`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t("rd-status-valid"))}`,"valid"),$n(e,o.data)}}function $n(e,n){const a=e==="seller"?"seller_name":"buyer_name",o=e==="seller"?"seller_addr":"buyer_addr",s=Ge(a),p=Ge(o),r=[];n.name&&n.name!==s&&r.push({field:a,label:t("rd-field-name"),current:s,official:n.name}),n.address&&n.address!==p&&r.push({field:o,label:t("rd-field-address"),current:p,official:n.address});const f=[];n.branch_label&&f.push(`<strong>${t("rd-field-branch")}:</strong> ${escapeHtml(n.branch_label)}`),n.post_code&&f.push(`<strong>${t("rd-field-postcode")}:</strong> ${escapeHtml(n.post_code)}`);let i=document.getElementById("rd-sync-modal");if(i||(i=document.createElement("div"),i.id="rd-sync-modal",i.className="rd-modal-mask",document.body.appendChild(i)),r.length===0)i.innerHTML=`
            <div class="rd-modal">
                <div class="rd-modal-head">
                    <h3>${escapeHtml(t("rd-modal-title"))}</h3>
                    <button class="rd-modal-close" type="button">×</button>
                </div>
                <div class="rd-modal-body">
                    <div class="rd-modal-no-diff">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 12l5 5 9-9"/></svg>
                        ${escapeHtml(t("rd-modal-no-diff"))}
                    </div>
                    ${f.length?`<div class="rd-modal-extra">${f.join(" · ")}</div>`:""}
                </div>
                <div class="rd-modal-foot">
                    <button class="rd-modal-btn primary" type="button" data-rd-modal-close>${escapeHtml(t("rd-modal-cancel"))}</button>
                </div>
            </div>
        `;else{const d=r.map((u,g)=>`
            <label class="rd-diff-row">
                <input type="checkbox" data-rd-apply data-field="${u.field}" data-value="${escapeHtml(u.official)}" checked>
                <div class="rd-diff-label">${escapeHtml(u.label)}</div>
                <div class="rd-diff-col rd-diff-current">
                    <div class="rd-diff-col-label">${escapeHtml(t("rd-modal-current"))}</div>
                    <div class="rd-diff-val">${escapeHtml(u.current||"—")}</div>
                </div>
                <div class="rd-diff-arrow">→</div>
                <div class="rd-diff-col rd-diff-official">
                    <div class="rd-diff-col-label">${escapeHtml(t("rd-modal-official"))}</div>
                    <div class="rd-diff-val">${escapeHtml(u.official)}</div>
                </div>
            </label>
        `).join("");i.innerHTML=`
            <div class="rd-modal">
                <div class="rd-modal-head">
                    <h3>${escapeHtml(t("rd-modal-title"))}</h3>
                    <button class="rd-modal-close" type="button">×</button>
                </div>
                <div class="rd-modal-body">
                    ${d}
                    ${f.length?`<div class="rd-modal-extra">${f.join(" · ")}</div>`:""}
                </div>
                <div class="rd-modal-foot">
                    <button class="rd-modal-btn" type="button" data-rd-modal-close>${escapeHtml(t("rd-modal-cancel"))}</button>
                    <button class="rd-modal-btn primary" type="button" data-rd-modal-apply>${escapeHtml(t("rd-modal-apply"))}</button>
                </div>
            </div>
        `}i.classList.add("show");const c=()=>i.classList.remove("show");i.querySelector(".rd-modal-close").addEventListener("click",c),i.querySelectorAll("[data-rd-modal-close]").forEach(d=>d.addEventListener("click",c)),i.addEventListener("click",d=>{d.target===i&&c()});const l=i.querySelector("[data-rd-modal-apply]");l&&l.addEventListener("click",()=>{const d=_results[_drawerIdx];if(!d){c();return}i.querySelectorAll("[data-rd-apply]:checked").forEach(u=>{const g=u.dataset.field,w=u.dataset.value;d.edits[g]=w,d.merged_fields[g]=w;const $=document.querySelector(`[data-field="${g}"]`);$&&($.value=w);const E=document.querySelector(`[data-field-wrap="${g}"]`);E&&E.classList.add("edited")}),updateDrawerEditCount(),renderResults(),c()})}window.callRdVerify=Sn;window.callRdSync=Tn;function Xe(){const e=document.getElementById("results-card");if(_results.length===0){e.classList.remove("show");return}e.classList.add("show");let n=0;_results.forEach(r=>{const f=parseFloat(r.merged_fields.total_amount);isNaN(f)||(n+=f)}),_selectedFiles&&_selectedFiles.length||_results.length;const a=_results.length,o=n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2});document.getElementById("results-head-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-value">${a}</span>
            <span class="rh-stat-label">${t("stats-invoices")}</span>
        </div>
        <div class="rh-stat">
            <span class="rh-stat-label">${t("stats-total")}</span>
            <span class="rh-stat-value">฿ ${o}</span>
        </div>
    `;let s=_results.map((r,f)=>({...r,_idx:f}));if(_searchKeyword){const r=_searchKeyword.toLowerCase();s=s.filter(f=>(f.filename||"").toLowerCase().includes(r)||(f.merged_fields.invoice_number||"").toLowerCase().includes(r))}_sortKey&&s.sort((r,f)=>{let i,c;return _sortKey==="filename"?(i=r.filename,c=f.filename):_sortKey==="invoice_no"?(i=r.merged_fields.invoice_number,c=f.merged_fields.invoice_number):_sortKey==="invoice_date"?(i=r.merged_fields.date,c=f.merged_fields.date):_sortKey==="total"?(i=parseFloat(r.merged_fields.total_amount)||0,c=parseFloat(f.merged_fields.total_amount)||0):_sortKey==="confidence"?(i=r.confidence,c=f.confidence):(i="",c=""),i<c?_sortDir==="asc"?-1:1:i>c?_sortDir==="asc"?1:-1:0});const p=document.getElementById("results-tbody");p.innerHTML=s.map((r,f)=>{const i=r.merged_fields,c=`<span class="empty-cell">${t("empty-val")}</span>`,l="conf-tip-"+(r.confidence||"low"),d="conf-"+(r.confidence||"low"),u=t(l),g=t(d);return`
            <tr data-idx="${r._idx}">
                <td class="num">${f+1}</td>
                <td class="fname" title="${escapeHtml(r.filename)}">${escapeHtml(r.filename)}</td>
                <td class="inv">${i.invoice_number?escapeHtml(i.invoice_number):c}</td>
                <td class="date">${i.date?escapeHtml(i.date):c}</td>
                <td class="amount">${i.total_amount?Number(i.total_amount).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}):c}</td>
                <td><span class="conf-badge ${r.confidence}" data-tip="${escapeHtml(u)}">${g}</span></td>
            </tr>
        `}).join(""),document.querySelectorAll("#results-table th").forEach(r=>{r.classList.remove("sort-asc","sort-desc"),r.dataset.sort===_sortKey&&r.classList.add("sort-"+_sortDir)}),p.querySelectorAll("tr").forEach(r=>{r.addEventListener("click",()=>{const f=parseInt(r.dataset.idx,10);At(f)})})}document.querySelectorAll("#results-table th").forEach(e=>{e.classList.contains("no-sort")||e.addEventListener("click",()=>{const n=e.dataset.sort;_sortKey===n?_sortDir=_sortDir==="asc"?"desc":"asc":(_sortKey=n,_sortDir="asc"),Xe()})});let xt=null;document.getElementById("search-input").addEventListener("input",e=>{const n=e.target.value;document.getElementById("search-clear").style.display=n?"":"none",clearTimeout(xt),xt=setTimeout(()=>{_searchKeyword=n.trim(),Xe(),Ht()},200)});document.getElementById("search-clear").addEventListener("click",()=>{const e=document.getElementById("search-input");e.value="",_searchKeyword="",document.getElementById("search-clear").style.display="none",Xe(),Ht(),e.focus()});function Ht(){const e=document.getElementById("search-matches");if(!e)return;if(!_searchKeyword){e.textContent="";return}const n=_searchKeyword.toLowerCase();let a=0;for(const o of _results)[o.filename,o.merged_fields?.invoice_number,o.merged_fields?.seller_name,o.merged_fields?.buyer_name].filter(Boolean).join(" ").toLowerCase().includes(n)&&a++;e.textContent=t("search-matches",{n:a})}function At(e){_drawerIdx=e;const n=_results[e];if(!n)return;document.getElementById("drawer-title").textContent=n.filename;const a=n.engine==="cache"||n.from_cache,o=a?t("badge-cached-hint"):`${(n.elapsed_ms/1e3).toFixed(1)}s`;document.getElementById("drawer-sub").innerHTML=`
        <span>${n.page_count} ${t("pages-unit")} · ${escapeHtml(o)}</span>
        ${a?`<span class="engine-badge cached">${escapeHtml(t("badge-cached"))}</span>`:""}
        <span class="drawer-edit-count" id="drawer-edit-count-sub"></span>
    `,updateDrawerEditCount();const s=_userInfo&&_userInfo.can_edit_fields,p=_userInfo&&_userInfo.can_verify_tax,r=n.merged_fields,f=document.getElementById("drawer-body"),i=s?"":`
        <div class="drawer-readonly-banner">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="9" width="12" height="9" rx="1"/><path d="M7 9V6a3 3 0 016 0v3"/></svg>
            <span>${t("readonly-banner")}</span>
        </div>
    `,c=p?"":`<span class="tax-badge unverified" data-tip="${escapeHtml(t("tax-tip-unverified"))}">${t("tax-unverified")}</span>`;if(f.innerHTML=`
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
                        ${r.category||n.category_tag?`<span class="drawer-suggest-learned" id="drawer-cat-learned-tag" title="${escapeHtml(t("drawer-suggest-learned-tip"))}">${escapeHtml(t("drawer-suggest-learned"))}</span>`:`<span class="drawer-suggest-empty">${escapeHtml(t("drawer-suggest-empty"))}</span>`}
                    </div>
                    <div class="drawer-suggest-body">
                        <input type="text" class="drawer-suggest-input" id="drawer-cat-input" data-field="category_tag"
                               list="drawer-cat-datalist"
                               placeholder="${escapeHtml(t("drawer-suggest-placeholder"))}"
                               value="${escapeHtml((n.edits&&n.edits.category_tag!==void 0?n.edits.category_tag:r.category||n.category_tag)||"")}"
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
            ${ye("invoice_number","drawer-lbl-invoice",r.invoice_number,"input",s)}
            ${ye("date","drawer-lbl-date",r.date,"input",s)}
            ${r.date_raw&&r.date_raw!==r.date?`<div class="date-raw-hint" title="${escapeHtml(t("drawer-date-raw-tip"))}">${escapeHtml(t("drawer-date-raw-label"))}: ${escapeHtml(r.date_raw)}</div>`:""}
            ${ye("subtotal","drawer-lbl-subtotal",r.subtotal,"input",s)}
            ${ye("vat","drawer-lbl-vat",r.vat,"input",s)}
            ${ye("total_amount","drawer-lbl-total",r.total_amount,"input",s)}
            ${r.wht_amount||r.wht_rate?`
                ${ye("wht_amount","drawer-lbl-wht-amount",r.wht_amount,"input",s,Mn(r.wht_rate))}
            `:""}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 18V8h14v10M3 8l2-4h10l2 4M7 12h2M11 12h2"/></svg>
                ${t("drawer-sec-seller")}
            </div>
            ${ye("seller_name","drawer-lbl-name",r.seller_name,"input",s)}
            ${ye("seller_tax","drawer-lbl-tax",r.seller_tax,"input",s,c,Et("seller"))}
            ${ye("seller_addr","drawer-lbl-addr",r.seller_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="10" cy="6" r="3"/><path d="M3 18c0-3.9 3.1-7 7-7s7 3.1 7 7"/></svg>
                ${t("drawer-sec-buyer")}
            </div>
            ${ye("buyer_name","drawer-lbl-name",r.buyer_name,"input",s)}
            ${ye("buyer_tax","drawer-lbl-tax",r.buyer_tax,"input",s,c,Et("buyer"))}
            ${ye("buyer_addr","drawer-lbl-addr",r.buyer_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 7l7-4 7 4v7l-7 4-7-4z"/><path d="M3 7l7 4 7-4M10 11v8"/></svg>
                ${t("drawer-sec-items")}
            </div>
            ${r.items&&r.items.length>0?Hn(r.items):`<div class="drawer-items-empty">${t("drawer-items-empty")}</div>`}
        </div>

        <div class="drawer-section">
            ${ye("notes","drawer-lbl-notes",r.notes,"textarea",s)}
        </div>

        <details class="raw-text">
            <summary>${t("raw-text")}</summary>
            <pre>${escapeHtml(n.pages.map(l=>`--- Page ${l.page||l.page_number||"?"} ---
${l.raw_text||l.text||""}`).join(`

`))}</pre>
        </details>
    `,s?f.querySelectorAll("[data-field]").forEach(l=>{l.addEventListener("input",onFieldEdit)}):f.querySelectorAll("[data-field]").forEach(l=>{l.setAttribute("readonly","readonly")}),document.getElementById("drawer-mask").classList.add("show"),document.getElementById("drawer").classList.add("show"),injectOcrPushButton(),typeof window.bindDrawerClient=="function"){const l=n._historyId||n.history_id||null;window.bindDrawerClient(l,n.client_id||null)}typeof window.fillCategoryDatalist=="function"&&window.fillCategoryDatalist(),setTimeout(()=>{const l=document.getElementById("drawer-cat-input");l&&!l.value&&!l.readOnly&&l.focus()},80)}function Mn(e){return e?`<span class="wht-badge">${escapeHtml(e)}%</span>`:""}function ye(e,n,a,o,s,p,r){const f=_results[_drawerIdx],i=f&&f.edits[e]!==void 0?f.edits[e]:a,c=f&&f.edits[e]!==void 0&&f.edits[e]!==a,l=escapeHtml(i??""),d=s?"":"readonly",u=o==="textarea"?`<textarea data-field="${e}" rows="2">${l}</textarea>`:`<input type="text" data-field="${e}" value="${l}">`;return`
        <div class="drawer-field ${c?"edited":""} ${d}" data-field-wrap="${e}">
            <label class="drawer-field-label">
                <span class="drawer-field-edited-dot"></span>
                ${t(n)}
                ${p||""}
                ${r?`<span class="drawer-field-actions">${r}</span>`:""}
            </label>
            ${u}
        </div>
    `}function Et(e){return _userInfo&&_userInfo.can_verify_tax?`
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
        </button>`}function Hn(e){return`
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
    `}function An(){document.getElementById("drawer-mask").classList.remove("show"),document.getElementById("drawer").classList.remove("show");const e=document.getElementById("drawer-history-save");e&&e.remove();const n=document.getElementById("drawer-ocr-push");n&&n.remove();const a=document.getElementById("drawer-ocr-push-btn");a&&a.remove(),_drawerIdx=-1}window.renderResults=Xe;window.openDrawer=At;window.closeDrawer=An;function jn(){const e=_results[_drawerIdx];if(!e||e._historyMode||!_userInfo||!_userInfo.can_push_erp||!e._historyId&&!e.history_id)return;const n=e._historyId||e.history_id,a=document.querySelector(".drawer-header");if(!a||document.getElementById("drawer-ocr-push-btn"))return;const o=(window._erpEndpoints||_erpEndpoints||[]).filter(function(f){return f&&f.enabled!==!1});if(o.length===0)return;const s=document.createElement("button");s.id="drawer-ocr-push-btn",s.className="drawer-push-btn";let p;if(o.length===1){const f=o[0].name||o[0].adapter||"ERP";p=t("btn-push-to-name",{name:f}),s.title=p}else p=t("btn-push-erp")+" ▾",s.title=t("btn-push-erp-pick-tip");s.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 8h9M8 5l3 3-3 3"/>
            <rect x="11" y="3" width="3" height="10" rx="1"/>
        </svg>
        <span>${escapeHtml(p)}</span>
    `,s.addEventListener("click",function(f){f.preventDefault(),f.stopPropagation(),o.length===1?jt(n,o[0].id):Pn(s,n,o)});const r=a.querySelector(".drawer-diagnose");r?a.insertBefore(s,r):a.appendChild(s)}function Pn(e,n,a){document.querySelectorAll(".drawer-push-picker").forEach(i=>i.remove());const o=e.getBoundingClientRect(),s=document.createElement("div");s.className="drawer-push-picker history-popover",s.style.position="fixed",s.style.top=o.bottom+6+"px",s.style.left=Math.max(8,o.right-240)+"px",s.style.minWidth="220px",s.style.zIndex="12000";const p=a.map(function(i){const c=escapeHtml(i.name||i.adapter||"ERP"),l=escapeHtml((i.adapter||"").toLowerCase()),u=i.is_default?'<span style="font-size:10px;color:#0a7a2c;background:#d6f5e0;padding:1px 6px;border-radius:999px;margin-left:6px;">'+escapeHtml(t("ep-default"))+"</span>":"";return'<button type="button" data-ep-id="'+escapeHtml(i.id)+'" style="display:flex;align-items:center;justify-content:space-between;width:100%;text-align:left;"><span><span style="color:#5d5d57;font-size:11px;margin-right:6px;">'+l+"</span>"+c+u+"</span></button>"}).join("");s.innerHTML=p,document.body.appendChild(s);const r=()=>{s.remove(),document.removeEventListener("click",f,!0)},f=i=>{!s.contains(i.target)&&i.target!==e&&!e.contains(i.target)&&r()};setTimeout(()=>document.addEventListener("click",f,!0),0),s.addEventListener("click",i=>{const c=i.target.closest("[data-ep-id]");if(!c)return;const l=c.getAttribute("data-ep-id");r(),jt(n,l)})}async function jt(e,n){const a=document.getElementById("drawer-ocr-push-btn");a&&(a.disabled=!0);try{const o={history_id:e};n&&(o.endpoint_id=n);const s=await fetch("/api/erp/push",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(o)}),p=await s.json();if(!s.ok){const r=p&&p.detail?p.detail:"err.unknown";r==="erp.no_default_endpoint"?showToast(t("erp-push-no-endpoint"),"warn"):r==="erp.endpoint_disabled"?(showToast(t("erp-push-disabled-tip")||t("card-disabled-tip")||"Endpoint disabled","warn"),typeof window._refreshErpEndpointsCache=="function"&&window._refreshErpEndpointsCache()):showToast(t("erp-push-fail",{err:r}),"fail");return}p.ok?showToast(t("erp-push-ok",{name:p.endpoint_name||""})):showToast(t("erp-push-fail",{err:p.error_msg||"unknown"}),"fail")}catch(o){showToast(t("erp-push-fail",{err:o.message}),"fail")}finally{a&&(a.disabled=!1)}}window.injectOcrPushButton=jn;const Dn=[{id:"input_vat",nameKey:"tpl-input-vat",descKey:"tpl-input-vat-desc",badge:"recommended"},{id:"standard",nameKey:"tpl-standard",descKey:"tpl-standard-desc"},{id:"sales_detail_th",nameKey:"export-tpl-sales-detail",descKey:"export-tpl-sales-detail-desc",badge:"new"},{id:"print",nameKey:"tpl-print",descKey:"tpl-print-desc"}];function Pt(){try{const e=localStorage.getItem("pn_export_tpl")||"input_vat";return e==="erp"?"input_vat":e}catch{return"input_vat"}}function qn(e){try{localStorage.setItem("pn_export_tpl",e||"input_vat")}catch{}}async function Dt(e){if(_results.length===0)return;e=e||"input_vat";const n=document.getElementById("btn-export");n&&(n.disabled=!0,n.classList.add("loading"));try{let a,o=`pearnly-export-${Date.now()}.xlsx`;if(e==="sales_detail_th"){const c=[];for(const l of _results){const d=l.invoices&&l.invoices.length>0?l.invoices:null;if(d&&d.length>1)for(let u=0;u<d.length;u++){const g=d[u]||{};c.push({filename:l.filename+" #"+(u+1)+"/"+d.length,engine:l.engine,merged_fields:g.fields||{}})}else c.push({filename:l.filename,engine:l.engine,merged_fields:l.merged_fields})}a=await apiPost("/api/ocr/export",{records:c,lang:currentLang,template:"sales_detail_th"})}else{const c=[];for(const d of _results)d.history_ids&&Array.isArray(d.history_ids)?c.push(...d.history_ids):d.history_id&&c.push(d.history_id);if(c.length===0){showToast(t("toast-export-error"),"error");return}const l=localStorage.getItem("mrpilot_token");a=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+l,"Content-Type":"application/json"},body:JSON.stringify({template:e,lang:currentLang,history_ids:c,client_id:null})}),o=`pearnly-${e}-${Date.now()}.xlsx`}if(!a)return;if(!a.ok){let c="HTTP "+a.status;try{const d=await a.json();d&&d.detail&&(c=typeof d.detail=="string"?d.detail:JSON.stringify(d.detail))}catch(d){console.warn("[export] resp.json err.detail parse failed:",d)}const l=typeof c=="string"&&c.indexOf(".")>0?"err."+c:null;showToast(l?t(l):t("toast-export-error")+" · "+c,"error");return}const s=await a.blob();let p=o;const r=a.headers.get("X-Filename");if(r)p=r;else{const l=(a.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(l)try{p=decodeURIComponent(l[1])}catch{}}const f=URL.createObjectURL(s),i=document.createElement("a");i.href=f,i.download=p,document.body.appendChild(i),i.click(),document.body.removeChild(i),URL.revokeObjectURL(f),showToast(t("toast-export-success"),"success")}catch(a){console.error(a),showToast(t("toast-export-error"),"error")}finally{n&&(n.disabled=!1,n.classList.remove("loading"))}}document.getElementById("btn-export").addEventListener("click",()=>{Dt(Pt())});function Rn(){const e=document.getElementById("export-split-wrap");if(!e)return;let n=document.getElementById("export-dropdown");if(n){n.remove();return}n=document.createElement("div"),n.id="export-dropdown",n.className="export-dropdown";const a=Pt(),o=Dn.map(p=>{const r=p.badge==="recommended"?`<span class="export-dd-badge badge-rec">${escapeHtml(t("report-recommended"))}</span>`:p.badge==="new"?`<span class="export-dd-badge badge-new">${escapeHtml(t("tpl-badge-new"))}</span>`:"";return`
            <div class="export-dd-item ${p.id===a?"active":""}" data-tpl="${p.id}">
                <div class="export-dd-row">
                    <span class="export-dd-name">${escapeHtml(t(p.nameKey))}</span>
                    ${r}
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
    `;n.innerHTML=o+s,e.appendChild(n)}function it(){const e=document.getElementById("export-dropdown");e&&e.remove()}const rt=document.getElementById("btn-export-arrow");rt&&rt.addEventListener("click",e=>{e.stopPropagation(),!rt.disabled&&Rn()});document.addEventListener("click",e=>{const n=e.target.closest(".export-dd-item");if(n){const a=n.getAttribute("data-tpl");if(a==="__custom"){it(),showToast(t("cs-coming-soon"),"info");return}qn(a),it(),Dt(a);return}e.target.closest("#btn-export-arrow")||it()});function Nn(){const e=document.getElementById("btn-export-arrow"),n=document.getElementById("btn-export");e&&n&&(e.disabled=n.disabled)}setInterval(Nn,300);function ft(){const e=document.getElementById("history-batch-bar"),n=document.getElementById("history-batch-count"),a=document.getElementById("history-check-all");if(!e||!n)return;const o=_historySelected.size;if(o>0?(e.style.display="",n.textContent=t("history-batch-count",{n:o})):e.style.display="none",a){const s=_historyState.items||[];if(s.length===0)a.checked=!1,a.indeterminate=!1;else{const p=s.filter(r=>_historySelected.has(r.id)).length;a.checked=p===s.length,a.indeterminate=p>0&&p<s.length}}}function Fn(){_historySelected.clear(),ft()}async function mt(){if(!_userInfo){setTimeout(()=>mt(),300);return}const e=document.getElementById("history-free-block"),n=document.getElementById("history-main"),a=document.getElementById("history-empty");if(!e||!n||!a){console.warn("[History] container missing");return}if(!_userInfo.can_view_history){e.style.display="",n.style.display="none",a.style.display="none";return}e.style.display="none",_historyState.loading=!0;try{const o=_historyState.page*_historyState.pageSize,s=new URLSearchParams({limit:_historyState.pageSize,offset:o});_historyState.keyword&&s.set("keyword",_historyState.keyword);const p=typeof window.getCurrentClientId=="function"?window.getCurrentClientId():null;p&&s.set("client_id",String(p));const r=await fetch(`/api/history?${s}`,{headers:{Authorization:"Bearer "+token}});if(r.status===401){localStorage.removeItem("mrpilot_token");const c=await r.json().catch(()=>({}));if((typeof c.detail=="string"?c.detail:c.detail&&c.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}const f=await r.json();_historyState.items=f.items||[],_historyState.total=f.total||0;const i=new Set(_historyState.items.map(c=>c.id));for(const c of Array.from(_historySelected))i.has(c)||_historySelected.delete(c);qt()}catch(o){console.error("load history failed",o)}finally{_historyState.loading=!1}}function qt(){const e=document.getElementById("history-main"),n=document.getElementById("history-empty"),a=_historyState.items,o=document.getElementById("history-search-matches");if(o&&(o.textContent=_historyState.keyword?t("search-matches",{n:_historyState.total}):""),a.length===0&&_historyState.total===0&&!_historyState.keyword){e.style.display="none",n.style.display="";return}e.style.display="",n.style.display="none";let s=0;a.forEach(c=>{c.confidence==="high"&&s++});const p=a.length>0?Math.round(s/a.length*100):0;document.getElementById("history-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-label">${escapeHtml(t("history-total",{n:_historyState.total}))}</span>
        </div>
        <div class="rh-stat rh-stat-quality">
            <span class="rh-stat-dot"></span>
            <span class="rh-stat-label">${escapeHtml(t("history-avg-conf",{p}))}</span>
        </div>
    `;const r=document.getElementById("history-tbody");a.length===0?r.innerHTML=`<div class="history-row-empty">${escapeHtml(t("history-empty-title"))}</div>`:r.innerHTML=a.map(c=>{const l=new Date(c.created_at),d=String(l.getMonth()+1).padStart(2,"0"),u=String(l.getDate()).padStart(2,"0"),g=String(l.getHours()).padStart(2,"0"),w=String(l.getMinutes()).padStart(2,"0"),$=`${d}-${u} ${g}:${w}`,E=escapeHtml(c.filename||""),_=E.length>50?E.substring(0,50)+"…":E,B=c.invoice_no?escapeHtml(c.invoice_no):_,q=[];c.seller_name&&q.push(escapeHtml(c.seller_name)),c.invoice_no&&c.filename&&q.push(_);const H=q.join(" · ")||"-",F=c.category_tag?`<span class="history-badge category">${escapeHtml(c.category_tag)}</span>`:"",A=c.source_total&&c.source_total>1?`<span class="history-badge multi">${escapeHtml(t("invoice-part-of",{i:c.source_index||1,n:c.source_total}))}</span>`:"",y=c.total_amount!==null&&c.total_amount!==void 0?Number(c.total_amount).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):'<span class="history-cell-amount-empty">—</span>',v=[];(c.total_amount===null||c.total_amount===void 0)&&v.push(t("field-amount")),c.invoice_no||v.push(t("field-invoice-no")),c.invoice_date||v.push(t("field-invoice-date")),c.seller_name||v.push(t("field-seller-name")),v.length>0&&`${escapeHtml(c.id)}${escapeHtml(t("history-needs-review-tip")+" · "+v.join(" · "))}${escapeHtml(t("history-needs-review-tip"))}${svgIcon("alert",14)}`,c.edited&&`${escapeHtml(t("history-edited",{n:c.edit_count||1}))}`;const b=c.smart_assigned_flag?`<span class="history-badge smart-assigned" title="${escapeHtml(t("history-smart-assigned"))}">${svgIcon("sparkle",11)}</span>`:"",L=c.confidence==="high"?"high":c.confidence==="medium"?"mid":"low",C=c.confidence==="high"?t("conf-high"):c.confidence==="medium"?t("conf-medium"):t("conf-low"),P=`<span class="history-badge conf-${L}">${escapeHtml(C)}</span>`;let I="";const j=c.source||"manual";return j==="email"?I=`<span class="history-badge source source-email" title="${escapeHtml(t("history-source-email"))}">${svgIcon("mail",11)}<span>${escapeHtml(t("history-source-email"))}</span></span>`:j==="folder"?I=`<span class="history-badge source source-folder" title="${escapeHtml(t("history-source-folder"))}">${svgIcon("folder",11)}<span>${escapeHtml(t("history-source-folder"))}</span></span>`:j==="api"&&(I=`<span class="history-badge source source-api" title="${escapeHtml(t("history-source-api"))}">${svgIcon("api",11)}<span>${escapeHtml(t("history-source-api"))}</span></span>`),`
                <div class="history-row" data-hid="${escapeHtml(c.id)}">
                    <div class="history-cell-check">
                        <input type="checkbox" class="history-row-check" data-hid="${escapeHtml(c.id)}" ${_historySelected.has(c.id)?"checked":""} aria-label="select">
                    </div>
                    <div class="history-cell-date">${$}</div>
                    <div class="history-cell-file">
                        <div class="history-cell-filename">${B} ${F} ${A} ${I} ${b}</div>
                        <div class="history-cell-subtitle">${H}</div>
                    </div>
                    <div class="history-cell-amount">${y}</div>
                    <div class="history-cell-conf">${P}</div>
                    <div class="history-cell-menu">
                        <button class="history-menu-btn" data-hmenu="${escapeHtml(c.id)}" type="button" aria-label="menu">
                            <svg viewBox="0 0 16 16" fill="currentColor"><circle cx="3" cy="8" r="1.5"/><circle cx="8" cy="8" r="1.5"/><circle cx="13" cy="8" r="1.5"/></svg>
                        </button>
                    </div>
                </div>
            `}).join(""),ft();const f=a.length>0?_historyState.page*_historyState.pageSize+1:0,i=_historyState.page*_historyState.pageSize+a.length;document.getElementById("history-pager-info").textContent=t("history-pager",{from:f,to:i,total:_historyState.total}),document.getElementById("history-prev").disabled=_historyState.page===0,document.getElementById("history-next").disabled=(_historyState.page+1)*_historyState.pageSize>=_historyState.total}window.loadHistoryPage=mt;window.renderHistoryList=qt;window.updateHistoryBatchBar=ft;window.clearHistorySelection=Fn;typeof currentRoute<"u"&&currentRoute==="history"&&mt();async function Ke(e){try{const n=await fetch(`/api/history/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=mergeFields(a.pages||[]),s={filename:a.filename,pages:a.pages,page_count:a.page_count,elapsed_ms:a.elapsed_ms,engine:"history",merged_fields:o,edits:{},confidence:a.confidence,archive_name:a.archive_name||null,category_tag:a.category_tag||null,_historyId:a.id,_historyMode:!0,client_id:a.client_id||null};_results.push(s),_drawerIdx=_results.length-1,openDrawer(_drawerIdx),On(),typeof window.bindDrawerClient=="function"&&window.bindDrawerClient(a.id,a.client_id||null),Vn(a.id)}catch(n){console.error("open history detail failed",n)}}async function zn(e){await Ke(e),requestAnimationFrame(()=>{const n=document.querySelector('[data-field="total_amount"]');if(n){try{n.focus()}catch{}try{n.select()}catch{}try{n.scrollIntoView({block:"center",behavior:"smooth"})}catch{}}})}function On(){const e=document.getElementById("drawer-body");if(!e||document.getElementById("drawer-history-save"))return;const n=document.createElement("div");n.id="drawer-history-save",n.className="drawer-history-save-bar",n.innerHTML=`
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
    `,e.appendChild(n),document.getElementById("btn-save-history").addEventListener("click",Gn),document.getElementById("btn-push-erp").addEventListener("click",Un)}async function Vn(e){}async function Un(){showToast(t("erp-push-coming-soon")||"ERP 推送即将开放，敬请期待","info")}async function Gn(){const e=_results[_drawerIdx];if(!e||!e._historyId)return;const n=JSON.parse(JSON.stringify(e.pages||[]));if(n.length>0){const o=n.findIndex(f=>!f.is_duplicate&&!f.is_copy),s=o>=0?o:0,p=n[s].fields||(n[s].fields={}),r={...e.edits};r.category_tag!==void 0&&(r.category=r.category_tag,delete r.category_tag),Object.assign(p,r)}const a=document.getElementById("btn-save-history");a&&(a.disabled=!0);try{if(!(await fetch(`/api/history/${encodeURIComponent(e._historyId)}`,{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({pages:n})})).ok)throw new Error("save failed");showAlert("info",t("history-save-ok")),setTimeout(hideAlerts,1500),closeDrawer(),e._historyMode&&_results.pop(),loadHistoryPage()}catch{showAlert("error",t("history-save-fail")),a&&(a.disabled=!1)}}function Kn(e,n){document.querySelectorAll(".history-popover").forEach(c=>c.remove());const a=n.getBoundingClientRect(),o=(_historyState.items||[]).find(c=>c.id===e),s=o&&o.invoice_no?String(o.invoice_no):"",p=o&&o.has_pdf===!0,r=document.createElement("div");r.className="history-popover",r.innerHTML=`
        <button data-act="copy-invno" ${s?"":"disabled"}>${escapeHtml(t("history-menu-copy-invno"))}</button>
        <button data-act="download-pdf" ${p?"":"disabled"}>${escapeHtml(t("history-menu-download-pdf"))}</button>
        <button data-act="delete" class="danger">${escapeHtml(t("history-menu-delete"))}</button>
    `,r.style.top=a.bottom+4+"px",r.style.left=a.right-160+"px",document.body.appendChild(r);const f=()=>{r.remove(),document.removeEventListener("click",i,!0)},i=c=>{!r.contains(c.target)&&c.target!==n&&f()};setTimeout(()=>document.addEventListener("click",i,!0),0),r.addEventListener("click",async c=>{const l=c.target.closest("[data-act]");if(!l||l.disabled)return;const d=l.dataset.act;if(f(),d==="copy-invno"){if(!s)return;try{await navigator.clipboard.writeText(s),showToast(t("history-copy-invno-ok",{no:s}),"success")}catch{try{const g=document.createElement("textarea");g.value=s,g.style.position="fixed",g.style.opacity="0",document.body.appendChild(g),g.select(),document.execCommand("copy"),document.body.removeChild(g),showToast(t("history-copy-invno-ok",{no:s}),"success")}catch{showToast(t("history-copy-invno-fail"),"error")}}}else if(d==="download-pdf"){const u=showToast(t("history-download-pdf-loading"),"loading",0);try{const g=await fetch(`/api/history/${encodeURIComponent(e)}/pdf`,{headers:{Authorization:"Bearer "+token}});if(!g.ok)throw new Error("download failed");const w=await g.blob(),$=URL.createObjectURL(w),E=document.createElement("a");E.href=$,E.download=o&&o.filename?o.filename.endsWith(".pdf")?o.filename:o.filename+".pdf":"invoice.pdf",document.body.appendChild(E),E.click(),document.body.removeChild(E),setTimeout(()=>URL.revokeObjectURL($),5e3),u(),showToast(t("history-download-pdf-ok"),"success")}catch{u(),showToast(t("history-download-pdf-fail"),"error")}}else if(d==="delete"){if(!await showConfirm(t("history-confirm-delete"),{danger:!0}))return;try{if(!(await fetch(`/api/history/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showAlert("info",t("history-delete-ok")),setTimeout(hideAlerts,1500),loadHistoryPage()}catch{showAlert("error",t("history-delete-fail"))}}})}(function(){document.addEventListener("click",r=>{const f=r.target.closest(".history-row"),i=r.target.closest("[data-hmenu]");if(i){r.stopPropagation(),Kn(i.dataset.hmenu,i);return}const c=r.target.closest("[data-review]");if(c){r.stopPropagation(),Ke(c.dataset.review);return}const l=r.target.closest("[data-fill-amount]");if(l){r.stopPropagation(),zn(l.dataset.fillAmount);return}r.target.closest(".history-row-check")||r.target.closest(".history-cell-check")||f&&!r.target.closest("[data-hmenu]")&&Ke(f.dataset.hid)});const n=document.getElementById("history-tbody");n&&n.addEventListener("change",r=>{const f=r.target.closest(".history-row-check");if(!f)return;const i=f.dataset.hid;f.checked?_historySelected.add(i):_historySelected.delete(i),updateHistoryBatchBar()});const a=document.getElementById("history-check-all");a&&a.addEventListener("change",r=>{const f=r.target.checked;for(const i of _historyState.items)f?_historySelected.add(i.id):_historySelected.delete(i.id);document.querySelectorAll(".history-row-check").forEach(i=>{i.checked=f}),updateHistoryBatchBar()});const o=document.getElementById("history-batch-cancel");o&&o.addEventListener("click",()=>{clearHistorySelection(),document.querySelectorAll(".history-row-check").forEach(r=>{r.checked=!1})});const s=document.getElementById("history-batch-delete");s&&s.addEventListener("click",async()=>{const r=_historySelected.size;if(r===0||!await showConfirm(t("history-batch-confirm",{n:r}),{danger:!0}))return;const i=Array.from(_historySelected);try{const c=await fetch("/api/history/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({ids:i})});if(!c.ok)throw new Error("batch delete failed");const l=await c.json();showToast(t("history-batch-done",{n:l.deleted||0}),"success"),clearHistorySelection(),loadHistoryPage()}catch(c){console.error("batch delete",c),showToast(t("history-batch-fail"),"error")}});let p=null;document.getElementById("history-search").addEventListener("input",r=>{const f=r.target.value;document.getElementById("history-search-clear").style.display=f?"":"none",clearTimeout(p),p=setTimeout(()=>{_historyState.keyword=f.trim(),_historyState.page=0,clearHistorySelection(),loadHistoryPage()},300)}),document.getElementById("history-search-clear").addEventListener("click",()=>{const r=document.getElementById("history-search");r.value="",_historyState.keyword="",_historyState.page=0,clearHistorySelection(),document.getElementById("history-search-clear").style.display="none",loadHistoryPage(),r.focus()}),document.getElementById("history-range").addEventListener("change",r=>{_historyState.range=parseInt(r.target.value,10),_historyState.page=0,clearHistorySelection(),loadHistoryPage()}),document.getElementById("history-prev").addEventListener("click",()=>{_historyState.page>0&&(_historyState.page--,clearHistorySelection(),loadHistoryPage())}),document.getElementById("history-next").addEventListener("click",()=>{(_historyState.page+1)*_historyState.pageSize<_historyState.total&&(_historyState.page++,clearHistorySelection(),loadHistoryPage())})})();window.openHistoryDrawer=Ke;const Me=document.getElementById("drop-zone"),vt=document.getElementById("file-input");Me.addEventListener("click",()=>vt.click());vt.addEventListener("change",e=>Rt(e.target.files));["dragover","dragenter"].forEach(e=>{Me.addEventListener(e,n=>{n.preventDefault(),Me.classList.add("drag-over")})});["dragleave","drop"].forEach(e=>{Me.addEventListener(e,n=>{n.preventDefault(),Me.classList.remove("drag-over")})});Me.addEventListener("drop",e=>{e.preventDefault(),Rt(e.dataTransfer.files)});const Jn=/\.(pdf|png|jpe?g|webp|tiff?|bmp|gif|xlsx?|xlsm|csv|tsv|docx?|txt)$/i;function ct(e){return e.type&&e.type.startsWith("image/")||/\.(png|jpe?g|webp|tiff?|bmp|gif)$/i.test(e.name)}function Yn(e){return e.type==="application/pdf"||/\.pdf$/i.test(e.name)}function Wn(e){return Yn(e)||ct(e)||Jn.test(e.name)}function Rt(e){hideAlerts();const n=Array.from(e),a=n.filter(Wn);a.length!==n.length&&showAlert("warn",t("alert-unsupported-format"));const o=a.filter(f=>!ct(f)),s=a.filter(ct),p=new Set(_selectedFiles.map(f=>f.name+"_"+f.size));for(const f of o){const i=f.name+"_"+f.size;p.has(i)||(_selectedFiles.push({file:f,name:f.name,size:f.size,status:"waiting",errorKey:null,errorParams:null}),p.add(i))}if(s.length>0)try{handleCameraImages(s,"gallery")}catch(f){console.error("[upload] image route failed",f)}const r=getMaxFiles();_selectedFiles.length>r&&(showAlert("warn",t("alert-file-count",{n:r})),_selectedFiles=_selectedFiles.slice(0,r)),Qe(),ht(),vt.value=""}let Ve=!1;function Qe(){const e=document.getElementById("file-list");if(!e)return;if(_selectedFiles.length===0){e.classList.remove("has-files"),e.innerHTML="";return}e.classList.add("has-files");const n=_selectedFiles.length,a=_selectedFiles.filter(d=>d.status==="processing"||d.status==="retrying").length,o=_selectedFiles.filter(d=>d.status==="success").length,s=_selectedFiles.filter(d=>d.status==="error").length;let p=`<span class="count">${escapeHtml(t("file-list-total",{n}))}</span>`;const r=[];a&&r.push(`<span style="color: var(--accent, #111111);">${a} ${escapeHtml(t("status-processing"))}</span>`),o&&r.push(`<span style="color: var(--success, #059669);">${o} ${escapeHtml(t("status-success"))}</span>`),s&&r.push(`<span style="color: var(--danger, #dc2626);">${s} ${escapeHtml(t("status-error"))}</span>`),r.length&&(p+=" · "+r.join(" · "));const f=Ve?t("file-list-collapse"):t("file-list-expand"),i=_selectedFiles.map((d,u)=>{let g=t("status-"+d.status);d.status==="retrying"&&(g=t("status-retrying")),d.status==="error"&&d.errorKey&&(g=t(d.errorKey,d.errorParams||{}));const w=d.status==="processing"||d.status==="retrying"?'<span class="spinner"></span>':"",$=d.status==="error"&&d.canRetry?`<button class="file-retry-btn" data-retry-idx="${u}" title="${escapeHtml(t("upload-retry-btn"))}">${svgIcon("refresh",12)}<span>${escapeHtml(t("upload-retry-btn"))}</span></button>`:"",E=d.status==="success"&&d.fromCache?`<span class="file-cache-badge">${svgIcon("cache",11)}<span>${escapeHtml(t("cache-hit-badge"))}</span></span>`:"";return`
            <li class="file-item">
                <svg class="file-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M5 2h7l4 4v12H5z"/><path d="M12 2v4h4"/></svg>
                <span class="file-name" title="${escapeHtml(d.name)}">${escapeHtml(d.name)}</span>
                ${E}
                <span class="file-status ${d.status}">${w}${g}</span>
                ${$}
            </li>
        `}).join("");e.innerHTML=`
        <div class="file-list-head">
            <div>${p}</div>
            ${n>5?`<button class="toggle" id="file-list-toggle">${escapeHtml(f)}</button>`:""}
        </div>
        <ul class="file-list-body${Ve?" expanded":""}" id="file-list-body">
            ${i}
        </ul>
    `;const c=document.getElementById("file-list-toggle");c&&c.addEventListener("click",()=>{Ve=!Ve,Qe()});const l=document.getElementById("file-list-body");l&&!l.dataset.retryBound&&(l.dataset.retryBound="1",l.addEventListener("click",async d=>{const u=d.target.closest(".file-retry-btn");if(!u)return;const g=parseInt(u.dataset.retryIdx||"-1",10);if(g<0||g>=_selectedFiles.length)return;const w=_selectedFiles[g];!w||w.status!=="error"||typeof window._reprocessFile=="function"&&await window._reprocessFile(w,!0)}))}function ht(){const e=document.getElementById("btn-start"),n=document.getElementById("btn-clear"),a=document.getElementById("btn-export"),o=_selectedFiles.some(s=>s.status==="waiting");e.disabled=_selectedFiles.length===0||!o,n.disabled=_selectedFiles.length===0&&_results.length===0,a.disabled=_results.length===0}document.getElementById("btn-clear").addEventListener("click",()=>{_selectedFiles=[],_results=[],Qe(),renderResults(),ht(),hideAlerts()});window.renderFileList=Qe;window.updateStartButton=ht;(function(){const n=document.getElementById("upload-alt-row"),a=document.getElementById("gallery-input"),o=document.getElementById("camera-input");if(!n)return;n.style.display="";const s=document.getElementById("btn-scan-doc");s&&o&&(s.addEventListener("click",async()=>{!(localStorage.getItem("mrpilot_camera_tips_skip")==="1")&&!await Qn()||o.click()}),o.addEventListener("change",async f=>{const i=Array.from(f.target.files||[]);if(f.target.value="",i.length!==0)for(const c of i)await dt([c],"camera")}));const p=document.getElementById("btn-upload-pic");p&&a&&p.addEventListener("click",()=>a.click());const r=f=>async i=>{const c=Array.from(i.target.files||[]);if(i.target.value="",c.length===0)return;const l=c.filter(u=>u.type==="application/pdf"||/\.pdf$/i.test(u.name)),d=c.filter(u=>!l.includes(u));l.length>0&&await Xn(l),d.length>0&&await dt(d,f)};a&&a.addEventListener("change",r("gallery"))})();async function Xn(e){for(const a of e)_selectedFiles.push({file:a,name:a.name,size:a.size,status:"waiting",errorKey:null,errorParams:null});const n=getMaxFiles();_selectedFiles.length>n&&(showAlert("warn",t("alert-file-count",{n})),_selectedFiles=_selectedFiles.slice(0,n)),renderFileList(),updateStartButton()}function Qn(){return new Promise(e=>{const n=document.getElementById("camera-tips-modal"),a=document.getElementById("camera-tips-ok"),o=document.getElementById("camera-tips-cancel"),s=document.getElementById("camera-tips-skip");if(!n||!a){e(!0);return}s&&(s.checked=!1),n.style.display="flex";const p=f=>{n.style.display="none",s&&s.checked&&localStorage.setItem("mrpilot_camera_tips_skip","1"),a.onclick=null,o&&(o.onclick=null),n.onclick=null,document.removeEventListener("keydown",r),e(f)},r=f=>{f.key==="Escape"&&p(!1)};a.onclick=()=>p(!0),o&&(o.onclick=()=>p(!1)),n.onclick=f=>{f.target===n&&p(!1)},document.addEventListener("keydown",r),setTimeout(()=>a.focus(),50)})}async function Je(e){return new Promise(n=>{const a=new FileReader;a.onerror=()=>n({warnings:[],width:0,height:0,brightness:128}),a.onload=()=>{const o=new Image;o.onerror=()=>n({warnings:[],width:0,height:0,brightness:128}),o.onload=()=>{const s=[],p=o.naturalWidth,r=o.naturalHeight;(p<1e3||r<1e3)&&s.push("low_res");try{const f=document.createElement("canvas");f.width=64,f.height=64;const i=f.getContext("2d");i.drawImage(o,0,0,64,64);const c=i.getImageData(0,0,64,64).data;let l=0,d=0;for(let g=0;g<c.length;g+=4)l+=.299*c[g]+.587*c[g+1]+.114*c[g+2],d++;const u=d?l/d:128;u<70?s.push("too_dark"):u>235&&s.push("too_bright"),n({warnings:s,width:p,height:r,brightness:u})}catch{n({warnings:s,width:p,height:r,brightness:128})}},o.src=a.result},a.readAsDataURL(e)})}let ke=[],Le=null;async function dt(e,n){if(hideAlerts(),!(!e||e.length===0)){if(typeof window.jspdf>"u"||!window.jspdf.jsPDF){showToast(t("camera-loading"),"info");for(let a=0;a<30&&(await new Promise(o=>setTimeout(o,100)),!(window.jspdf&&window.jspdf.jsPDF));a++);if(!window.jspdf||!window.jspdf.jsPDF){showToast(t("camera-lib-fail"),"error");return}}if(n==="camera"&&e.length===1){const a=e[0];let o={};try{o=await Je(a)}catch{}ke.push({file:a,quality:o}),Le="camera",$e();return}if(n==="gallery"&&(e.length>=2||ke.length>0)){for(const a of e){let o={};try{o=await Je(a)}catch{}ke.push({file:a,quality:o})}Le="gallery",$e();return}await Nt(e)}}async function Zn(e){const n=new Set;for(const o of e)try{((await Je(o)).warnings||[]).forEach(p=>n.add(p))}catch{}try{const o=await Ft(e);o&&_selectedFiles.push({file:o,name:o.name,size:o.size,status:"waiting",errorKey:null,errorParams:null})}catch(o){console.error("[camera] convert failed",o),showToast(t("camera-convert-fail"),"error");return}const a=getMaxFiles();_selectedFiles.length>a&&(showAlert("warn",t("alert-file-count",{n:a})),_selectedFiles=_selectedFiles.slice(0,a)),renderFileList(),updateStartButton(),showToast(t("camera-added-merged",{n:e.length}),"success"),n.size>0&&setTimeout(()=>{n.has("too_dark")?showToast(t("camera-quality-dark"),"warn"):n.has("low_res")?showToast(t("camera-quality-lowres"),"warn"):n.has("too_bright")&&showToast(t("camera-quality-overexposed"),"warn")},1e3)}function $e(){let e=document.getElementById("camera-buffer-bar");if(ke.length===0){e&&e.remove(),Le=null;return}e||(e=document.createElement("div"),e.id="camera-buffer-bar",e.className="camera-buffer-bar",document.body.appendChild(e));const n=ke.length,a=n>=2,o=Le==="gallery",s=o?t("camera-buffer-more-gallery"):t("camera-buffer-more");let p;a?o?p=`
            <button type="button" class="btn btn-ghost btn-sm" data-cbb-action="merge">${escapeHtml(t("camera-buffer-done-merge"))}</button>
            <button type="button" class="btn btn-primary btn-sm" data-cbb-action="separate">${escapeHtml(t("camera-buffer-done-separate",{n}))}</button>
        `:p=`
            <button type="button" class="btn btn-ghost btn-sm" data-cbb-action="separate">${escapeHtml(t("camera-buffer-done-separate",{n}))}</button>
            <button type="button" class="btn btn-primary btn-sm" data-cbb-action="merge">${escapeHtml(t("camera-buffer-done-merge"))}</button>
        `:p=`<button type="button" class="btn btn-primary btn-sm" data-cbb-action="merge">${escapeHtml(t("camera-buffer-done"))}</button>`,e.innerHTML=`
        <div class="cbb-count">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 7h4l2-2h6l2 2h4a1 1 0 011 1v11a1 1 0 01-1 1H3a1 1 0 01-1-1V8a1 1 0 011-1z"/>
                <circle cx="12" cy="13" r="4"/>
            </svg>
            <span>${escapeHtml(t("camera-buffer-count",{n}))}</span>
        </div>
        <div class="cbb-actions">
            <button type="button" class="btn btn-ghost btn-sm" data-cbb-action="discard">${escapeHtml(t("camera-buffer-discard"))}</button>
            <button type="button" class="btn btn-ghost btn-sm" data-cbb-action="more">${escapeHtml(s)}</button>
            ${p}
        </div>
    `,e.querySelector('[data-cbb-action="discard"]').onclick=()=>{ke=[],Le=null,$e()},e.querySelector('[data-cbb-action="more"]').onclick=()=>{const i=o?"gallery-input":"camera-input",c=document.getElementById(i);c&&c.click()};const r=e.querySelector('[data-cbb-action="merge"]');r&&(r.onclick=async()=>{const i=ke.map(c=>c.file);ke=[],Le=null,$e(),await Zn(i)});const f=e.querySelector('[data-cbb-action="separate"]');f&&(f.onclick=async()=>{const i=ke.map(c=>c.file);ke=[],Le=null,$e(),await Nt(i)})}typeof window.subscribeI18n=="function"&&window.subscribeI18n("camera-buffer-bar",()=>{ke.length>0&&$e()});async function Nt(e){const n=new Set;let a=0;for(const s of e)try{((await Je(s)).warnings||[]).forEach(f=>n.add(f));const r=await Ft([s]);r&&(_selectedFiles.push({file:r,name:r.name,size:r.size,status:"waiting",errorKey:null,errorParams:null}),a++)}catch(p){console.error("[camera] separate convert failed",p)}if(a===0){showToast(t("camera-convert-fail"),"error");return}const o=getMaxFiles();_selectedFiles.length>o&&(showAlert("warn",t("alert-file-count",{n:o})),_selectedFiles=_selectedFiles.slice(0,o)),renderFileList(),updateStartButton(),showToast(t("camera-added-separate",{n:a}),"success"),n.size>0&&setTimeout(()=>{n.has("too_dark")?showToast(t("camera-quality-dark"),"warn"):n.has("low_res")?showToast(t("camera-quality-lowres"),"warn"):n.has("too_bright")&&showToast(t("camera-quality-overexposed"),"warn")},1e3)}async function Ft(e){if(!e||e.length===0)return null;const{jsPDF:n}=window.jspdf,a=210,o=297,s=new n({unit:"mm",format:"a4",orientation:"p"});for(let c=0;c<e.length;c++){const l=e[c],{dataUrl:d,naturalW:u,naturalH:g}=await ea(l);c>0&&s.addPage("a4","p");const w=u/g;let $=a-10,E=$/w;E>o-10&&(E=o-10,$=E*w);const _=(a-$)/2,B=(o-E)/2,q=l.type==="image/png"?"PNG":"JPEG";s.addImage(d,q,_,B,$,E,void 0,"FAST")}const p=s.output("blob"),r=new Date,f=r.getFullYear().toString()+String(r.getMonth()+1).padStart(2,"0")+String(r.getDate()).padStart(2,"0")+String(r.getHours()).padStart(2,"0")+String(r.getMinutes()).padStart(2,"0")+String(r.getSeconds()).padStart(2,"0"),i=e.length>1?`_${e.length}p`:"";return new File([p],`photo_${f}${i}.pdf`,{type:"application/pdf"})}function ea(e){return new Promise((n,a)=>{const o=new FileReader;o.onerror=a,o.onload=()=>{const s=new Image;s.onerror=a,s.onload=()=>n({dataUrl:o.result,naturalW:s.naturalWidth,naturalH:s.naturalHeight}),s.src=o.result},o.readAsDataURL(e)})}window.handleCameraImages=dt;document.getElementById("btn-start").addEventListener("click",async()=>{if(hideAlerts(),document.getElementById("btn-start").disabled=!0,_userInfo&&_userInfo.plan==="free"){const l=await fetch("/api/health").then(d=>d.json()).catch(()=>null);l&&!l.ocr_ready&&(showAlert("info",t("alert-loading-engine")),startEnginePolling())}const e=_selectedFiles.filter(l=>l.status==="waiting"),n=6;async function a(l,d){if(window._ocrAborted)return l.status="cancelled",l.errorKey=null,renderFileList(),{};l.status=d?"retrying":"processing",l.canRetry=!1,renderFileList();const u=new AbortController,g=setTimeout(()=>u.abort("timeout"),9e4);window._ocrCtrls=window._ocrCtrls||new Set,window._ocrCtrls.add(u);try{const w=new FormData;w.append("file",l.file,l.name);try{if(typeof window.getCurrentClientId=="function"){const q=window.getCurrentClientId();q!=null&&w.append("client_id",String(q))}}catch{}const $=await fetch("/api/ocr/recognize",{method:"POST",headers:{Authorization:"Bearer "+token},body:w,signal:u.signal});if(clearTimeout(g),window._ocrCtrls.delete(u),$.status===401||$.status===403){const H=await $.clone().json().catch(()=>({})),F=H&&H.detail,A=typeof F=="string"?F:F&&F.code||"";if(!A||A.startsWith("auth.")){if(localStorage.removeItem("mrpilot_token"),A==="auth.session_revoked")_showSessionRevokedModal();else{const y=A==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(t(y),"error"),setTimeout(()=>{window.location.href="/"},1200)}return{abort:!0}}A==="quota.need_api_key"&&showToast(t("err.quota.need_api_key"),"error")}if(!$.ok){const H=(await $.json().catch(()=>({}))).detail;return typeof H=="string"?(l.errorKey="err."+H,l.errorParams=null):H&&H.code?(l.errorKey="err."+H.code,l.errorParams={...H,mb:_quota.max_file_size_mb}):(l.errorKey="err.unknown",l.errorParams=null),(l.errorKey==="err.unknown"||l.errorKey==="err.ocr.engine_error")&&($.status===429?l.errorKey="err.rate_limit":$.status===502||$.status===503||$.status===504?l.errorKey="err.gemini_overloaded":$.status>=500&&(l.errorKey="err.server")),l.status="error",l.canRetry=!/not_pdf|invalid_pdf|file_too_large|too_many_pages|monthly_limit_exceeded|ip_limit_exceeded|plan_not_supported|need_api_key|not_invoice/.test(l.errorKey||""),renderFileList(),{}}const E=await $.json();l.status="success",l.fromCache=!!E.from_cache;const _=mergeFields(E.pages),B=E.confidence||(_.items&&_.items.length>0?"high":"low");if(_results.push({filename:E.filename,pages:E.pages,page_count:E.page_count,elapsed_ms:E.elapsed_ms,engine:E.engine,merged_fields:_,edits:{},confidence:B,history_id:E.history_id,history_ids:E.history_ids||[],invoice_count:E.invoice_count||1,invoices:E.invoices||[],archive_name:E.archive_name||null,category_tag:E.category_tag||null,auto_pushed:!!E.auto_pushed,typhoon_enhanced:!!E.typhoon_enhanced,typhoon_pages:E.typhoon_pages||[],from_cache:!!E.from_cache}),E.invoice_count&&E.invoice_count>1&&showToast(t("multi-invoice-toast",{file:E.filename,n:E.invoice_count}),"success"),E.missed_invoice_warnings&&E.missed_invoice_warnings.length){const q=E.missed_invoice_warnings.map(function(H){return H.page}).filter(function(H){return H!=null});showToast(t("missed-invoice-warn",{file:E.filename,pages:q.join(", ")}),"warn",8e3),console.warn("[OCR] possible missed invoice(s)",E.missed_invoice_warnings)}if(E.typhoon_enhanced&&E.typhoon_pages&&E.typhoon_pages.length&&showToast(t("typhoon-enhanced-toast",{file:E.filename,n:E.typhoon_pages.length}),"success"),E.fallback_used){const q=E.engine_chain||[],H=E.engine||"";let F;H==="typhoon_nvidia"?F="fallback-typhoon-nvidia-toast":H==="easyocr"?F="fallback-easyocr-toast":F="fallback-generic-toast",showToast(t(F,{file:E.filename}),"warn"),console.info("[OCR Chain]",q)}if(E.from_cache&&showToast(t("cache-hit-toast",{file:E.filename}),"info"),E.duplicate_warnings&&E.duplicate_warnings.length){window._dupQueue||(window._dupQueue=[]);for(const q of E.duplicate_warnings)window._dupQueue.push({filename:E.filename,...q})}return E.auto_pushed&&showToast(t("auto-push-fired",{file:E.filename}),"info"),E.quota&&E.quota.used_this_month!=null&&_userInfo&&(_userInfo.used_this_month=E.quota.used_this_month,_userInfo.tenant_used=E.quota.used_this_month,renderInfoBar(),renderQuotaBanner()),renderFileList(),renderResults(),updateStartButton(),{}}catch(w){clearTimeout(g);try{window._ocrCtrls&&window._ocrCtrls.delete(u)}catch{}console.error("[Upload] failed for",l.file.name,w);const $=w&&(w.name==="AbortError"||w==="timeout"),E=$&&(u.signal.reason==="timeout"||w==="timeout"),_=w&&w.message&&/NetworkError|Failed to fetch/i.test(w.message);return $&&(u.signal.reason==="user_stop"||window._ocrAborted)?(l.status="cancelled",l.errorKey=null,l.canRetry=!1,renderFileList(),{}):(E?l.errorKey="err.timeout":$?l.errorKey="err.aborted":_?l.errorKey="err.network":(l.errorKey="err.unknown",l.errorParams={msg:w&&w.message?w.message:String(w)}),l.status="error",!d&&!window._ocrAborted&&(_||E)&&navigator.onLine!==!1&&(l.canRetry=!0,renderFileList(),await new Promise(q=>setTimeout(q,2e3)),l.status==="error"&&navigator.onLine!==!1&&!window._ocrAborted)?a(l,!0):(l.canRetry=!0,renderFileList(),{}))}}window._reprocessFile=a;let o=0,s=!1;async function p(){for(;o<e.length&&!s&&!window._ocrAborted;){const l=o++,d=await a(e[l]);if(d&&d.abort){s=!0;return}}}window._ocrAborted=!1,window._ocrCtrls=window._ocrCtrls||new Set;const r=document.getElementById("btn-start"),f=document.getElementById("btn-stop");r&&(r.style.display="none"),f&&(f.style.display="");try{typeof window._bigBatchStart=="function"&&window._bigBatchStart(e)}catch{}const i=[];for(let l=0;l<Math.min(n,e.length);l++)i.push(p());await Promise.all(i);try{typeof window._bigBatchStop=="function"&&window._bigBatchStop()}catch{}r&&(r.style.display=""),f&&(f.style.display="none");const c=!!window._ocrAborted;window._ocrAborted=!1,window._ocrCtrls.clear(),updateStartButton(),stopEnginePolling(),document.getElementById("alert-info").classList.contains("show")&&(showAlert("info",t("alert-engine-ready")),setTimeout(hideAlerts,2e3));try{const l={success:0,cancelled:0,network:0,timeout:0,quota:0,overloaded:0,rate:0,other:0};for(const u of e)if(u.status==="success")l.success++;else if(u.status==="cancelled")l.cancelled++;else if(u.status==="error"){const g=u.errorKey||"";g==="err.network"?l.network++:g==="err.timeout"||g==="err.aborted"?l.timeout++:g.indexOf("quota")>=0||g==="err.monthly_limit_exceeded"?l.quota++:g==="err.gemini_overloaded"||g==="err.server"?l.overloaded++:g==="err.rate_limit"?l.rate++:l.other++}const d=e.length;c?showToast(ta(l,d),"warn",4e3):d>1&&l.network+l.timeout+l.quota+l.overloaded+l.rate+l.other>0&&showToast(na(l),"error",4500)}catch{}window._dupQueue&&window._dupQueue.length&&showDuplicateDialog()});function ta(e,n){return t("ocr-summary-aborted").replace("{success}",e.success).replace("{cancelled}",e.cancelled).replace("{total}",n)}function na(e){const n=[];return e.success&&n.push(t("ocr-summary-success").replace("{n}",e.success)),e.network&&n.push(t("ocr-summary-network").replace("{n}",e.network)),e.timeout&&n.push(t("ocr-summary-timeout").replace("{n}",e.timeout)),e.quota&&n.push(t("ocr-summary-quota").replace("{n}",e.quota)),e.overloaded&&n.push(t("ocr-summary-overloaded").replace("{n}",e.overloaded)),e.rate&&n.push(t("ocr-summary-rate").replace("{n}",e.rate)),e.other&&n.push(t("ocr-summary-other").replace("{n}",e.other)),n.join(" · ")}document.addEventListener("click",e=>{if(!e.target.closest("#btn-stop")||window._ocrAborted)return;window._ocrAborted=!0,window._ocrCtrls&&window._ocrCtrls.size&&window._ocrCtrls.forEach(a=>{try{a.abort("user_stop")}catch{}});const n=document.getElementById("btn-stop");n&&(n.disabled=!0),typeof showToast=="function"&&showToast(t("ocr-stop-toast"),"warn",2e3),setTimeout(()=>{n&&(n.disabled=!1)},800)});function zt(){if(!window._dupQueue||!window._dupQueue.length)return;const e=window._dupQueue.shift(),n=e.level==="exact",a=n?"dup-title-exact":"dup-title-likely",o=n?"dup-desc-exact":"dup-desc-likely",s=n?"#DC2626":"#D97706",p=n?"#FEE2E2":"#FEF3C7",r=g=>g!=null?Number(g).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—",f=g=>g||"—",i=g=>{try{const w=new Date(g);return`${w.getFullYear()}-${String(w.getMonth()+1).padStart(2,"0")}-${String(w.getDate()).padStart(2,"0")}`}catch{return g}},c=e.invoice_total>1?` · ${t("invoice-part-of",{i:e.invoice_index,n:e.invoice_total})}`:"",l=(e.matched_fields||[]).map(g=>{const w=t("dup-field-"+g.replace("_","-"))||g;return`<span class="dup-field-chip">${escapeHtml(w)}</span>`}).join(" "),d=document.createElement("div");d.className="log-detail-modal",d.innerHTML=`
        <div class="log-detail-box dup-dialog">
            <div class="dup-head" style="background:${p};">
                <div class="dup-title" style="color:${s};">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:22px;height:22px;vertical-align:-5px;margin-right:6px;">
                        <path d="M10 2.5L1 17h18L10 2.5z"/><path d="M10 8v4M10 14v0.5"/>
                    </svg>
                    ${escapeHtml(t(a))}
                </div>
                <button class="log-detail-close dup-close" type="button">✕</button>
            </div>
            <div class="dup-body">
                <div class="dup-desc">${escapeHtml(t(o))}</div>
                <div class="dup-source">
                    <div class="dup-source-label">${escapeHtml(t("dup-current-file"))}${escapeHtml(c)}</div>
                    <div class="dup-source-name">${escapeHtml(e.filename)}</div>
                </div>
                <div class="dup-matched-label">${escapeHtml(t("dup-matched-on"))} ${l}</div>
                <table class="dup-compare">
                    <thead>
                        <tr>
                            <th></th>
                            <th>${escapeHtml(t("dup-this-one"))}</th>
                            <th>${escapeHtml(t("dup-existing-one"))}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>${escapeHtml(t("dup-field-invoice-no"))}</td><td>${escapeHtml(e.current.invoice_no||"—")}</td><td>${escapeHtml(e.match.invoice_no||"—")}</td></tr>
                        <tr><td>${escapeHtml(t("dup-field-invoice-date"))}</td><td>${escapeHtml(f(e.current.invoice_date))}</td><td>${escapeHtml(f(e.match.invoice_date))}</td></tr>
                        <tr><td>${escapeHtml(t("dup-field-seller-name"))}</td><td>${escapeHtml(e.current.seller_name||"—")}</td><td>${escapeHtml(e.match.seller_name||"—")}</td></tr>
                        <tr><td>${escapeHtml(t("dup-field-total-amount"))}</td><td>${r(e.current.total_amount)}</td><td>${r(e.match.total_amount)}</td></tr>
                        <tr><td>${escapeHtml(t("dup-field-original-file"))}</td><td>—</td><td>${escapeHtml(e.match.filename||"—")}</td></tr>
                        <tr><td>${escapeHtml(t("dup-field-uploaded-at"))}</td><td>—</td><td>${escapeHtml(i(e.match.created_at))}</td></tr>
                    </tbody>
                </table>
            </div>
            <div class="dup-actions">
                <button class="btn btn-ghost btn-tiny" data-action="view">${escapeHtml(t("dup-action-view"))}</button>
                <button class="btn btn-danger btn-tiny" data-action="delete">${escapeHtml(t("dup-action-delete"))}</button>
                <button class="btn btn-primary btn-tiny" data-action="keep">${escapeHtml(t("dup-action-keep"))}</button>
            </div>
        </div>
    `,document.body.appendChild(d);const u=()=>{d.remove(),window._dupQueue&&window._dupQueue.length&&setTimeout(zt,200)};d.querySelector(".dup-close").addEventListener("click",u),d.querySelector('[data-action="view"]').addEventListener("click",()=>{const g=e.match.id;window.location.hash="#/history",setTimeout(()=>{typeof openHistoryDrawer=="function"&&openHistoryDrawer(g)},400),u()}),d.querySelector('[data-action="delete"]').addEventListener("click",async()=>{const g=e.new_history_id;if(!g){u();return}try{(await fetch(`/api/history/${encodeURIComponent(g)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok?showToast(t("dup-deleted-toast"),"success"):showToast(t("dup-delete-failed"),"error")}catch{showToast(t("dup-delete-failed"),"error")}u()}),d.querySelector('[data-action="keep"]').addEventListener("click",u)}window.showDuplicateDialog=zt;function Se(e,n){try{return typeof window.t=="function"?window.t(e):n}catch{return n}}function je(e){if(e==null||isNaN(e))return"—";try{return String(e).replace(/\B(?=(\d{3})+(?!\d))/g,",")}catch{return String(e)}}function aa(e){if(!e)return"";try{const n=new Date(e).getTime();if(!n)return"";const a=Math.floor((Date.now()-n)/1e3);return a<60?Se("time-just-now","刚刚"):a<3600?Math.floor(a/60)+Se("time-min-ago-suffix"," 分钟前"):a<86400?Math.floor(a/3600)+Se("time-hour-ago-suffix"," 小时前"):Math.floor(a/86400)+Se("time-day-ago-suffix"," 天前")}catch{return""}}async function gt(){Ot();const e=document.getElementById("dash-kpi-invoices"),n=document.getElementById("dash-kpi-pending"),a=document.getElementById("dash-kpi-exceptions"),o=document.getElementById("dash-kpi-plan"),s=document.getElementById("dash-kpi-plan-sub"),p=document.getElementById("dash-recent-list"),r=document.getElementById("dash-quick-exc-badge");try{const f={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},[i,c,l]=await Promise.all([fetch("/api/me/tenant-usage",{headers:f}).then(E=>E.ok?E.json():null).catch(()=>null),fetch("/api/history?limit=20",{headers:f}).then(E=>E.ok?E.json():null).catch(()=>null),fetch("/api/exceptions/stats?status=pending",{headers:f}).then(E=>E.ok?E.json():null).catch(()=>null)]),d=i&&i.ocr_this_month||0;let u=0;const g=c&&(c.items||c.history||c)||[],w=Array.isArray(g)?g:[];w.forEach(E=>{(E.status==="pending"||E.status==="reviewing")&&u++});const $=l&&(l.total||l.count||l.pending||0)||0;if(e&&(e.textContent=je(d)),n&&(n.textContent=je(u)),a&&(a.textContent=je($)),r&&($>0?(r.style.display="",r.textContent=$):r.style.display="none"),o&&i){const E=i.ocr_this_month||0,_=i.quota||0;o.textContent=je(E),s&&(s.textContent=_?E+" / "+je(_)+" 张":Se("dash-kpi-plan-sub","本月用量"))}if(p)if(w.length===0)p.innerHTML='<div class="dash-recent-empty">'+Se("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>";else{const E=w.slice(0,5).map(_=>{const B=(_.invoice_no||_.filename||_.id||"").toString(),q=(_.supplier_name||_.buyer_name||_.client_name||_.notes||"").toString(),H=aa(_.created_at||_.upload_time||_.date),F=A=>String(A).replace(/[&<>"']/g,y=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[y]);return'<div class="dash-recent-row"><span class="dash-recent-key" title="'+F(B)+'">'+F(B)+'</span><span class="dash-recent-mid" title="'+F(q)+'">'+F(q)+'</span><span class="dash-recent-time">'+F(H)+"</span></div>"}).join("");p.innerHTML=E}}catch{p&&(p.innerHTML='<div class="dash-recent-empty">'+Se("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>")}}window.loadDashboard=gt;async function Ot(){const e=document.getElementById("dash-kpi-balance-card"),n=document.getElementById("dash-kpi-usage-card"),a=document.getElementById("dash-kpi-balance"),o=document.getElementById("dash-kpi-balance-sub"),s=document.getElementById("dash-kpi-usage"),p=document.getElementById("dash-kpi-usage-sub");if(!(!e||!n))try{const r={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},f=await fetch("/api/me/credits",{headers:r,cache:"no-store"});if(!f.ok){e.style.display="none",s&&(s.textContent="—"),p&&(p.textContent="");return}const i=await f.json(),c=!!i.is_owner,l=!!i.is_billing_exempt;if(!c)e.style.display="none";else if(e.style.display="",l)a&&(a.textContent="∞",a.className="dash-kpi-val dash-green"),o&&(o.textContent=typeof window.t=="function"?window.t("dash-kpi-balance-exempt"):"Billing exempt");else{const u=typeof i.balance_thb=="number"?i.balance_thb:0;if(a&&(a.textContent="฿"+u.toFixed(2),a.className=u<50?"dash-kpi-val dash-red":"dash-kpi-val"),o){const g=typeof window.t=="function"?window.t("dash-kpi-balance-topup"):"Top up →",w=u<50?"#dc2626":"#6b7280",$=E=>typeof window.escapeHtml=="function"?window.escapeHtml(E):String(E).replace(/[&<>"']/g,_=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[_]);o.innerHTML='<a href="#" id="kpi-balance-topup-link" style="color:'+w+';text-decoration:underline;cursor:pointer;" onclick="event.preventDefault();window._openTopupModal&&window._openTopupModal();return false;">'+$(g)+"</a>"}}const d=typeof i.pages_this_month=="number"?i.pages_this_month:typeof i.my_invoice_count=="number"?i.my_invoice_count:0;if(n.style.display="",s&&(s.textContent=String(d)),p){const u=d>=200?"dash-kpi-usage-sub-high":"dash-kpi-usage-sub-low",g=typeof window.t=="function"?window.t(u,{used:d}):d+" pages";p.textContent=g}}catch(r){console.warn("[credits] loadCreditsCard failed:",r),e.style.display="none",s&&(s.textContent="—")}}window.loadCreditsCard=Ot;document.addEventListener("DOMContentLoaded",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&setTimeout(gt,500)});typeof window.subscribeI18n=="function"&&window.subscribeI18n("dashboard",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&gt()});function he(e){return(typeof window.t=="function"?window.t(e):null)||e}function bt(){return localStorage.getItem("mrpilot_token")||""}function ve(e){return document.getElementById(e)}var Ue=null,De=null;function Vt(){De||(De=setInterval(function(){if(!document.hidden){var e=bt();e&&(window._userInfo&&window._userInfo.is_billing_exempt||fetch("/api/me/credits",{headers:{Authorization:"Bearer "+e},cache:"no-store"}).then(function(n){return n.ok?n.json():null}).then(function(n){if(n){var a=n.balance_thb!=null?Number(n.balance_thb):0;Ue!==null&&a>Ue&&(window.showToast&&window.showToast(he("credits-updated"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard(),typeof window._refreshBalanceAlerts=="function"&&window._refreshBalanceAlerts()),Ue=a}}).catch(function(){}))}},3e4))}function oa(){De&&(clearInterval(De),De=null),Ue=null}window._startCreditsPoll=Vt;window._stopCreditsPoll=oa;Vt();var yt=null,wt=0;function sa(){if(!ve("topup-v2-ov")){var e=document.createElement("div");e.id="topup-v2-ov",e.className="topup-v2-ov",e.style.cssText="display:none;position:fixed;inset:0;background:rgba(15,23,42,.5);z-index:9500;align-items:center;justify-content:center;padding:16px",e.innerHTML=['<div class="topup-v2-box">','  <div class="topup-v2-head">','    <div class="topup-v2-title" id="tv2-title"></div>','    <button class="topup-v2-close" id="tv2-close" aria-label="close">','      <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="4" y1="4" x2="16" y2="16"/><line x1="16" y1="4" x2="4" y2="16"/></svg>',"    </button>","  </div>",'  <div class="topup-v2-steps">','    <div class="topup-v2-step" id="tv2-d1"><span class="topup-v2-dot">1</span><span class="topup-v2-slabel" id="tv2-sl1"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d2"><span class="topup-v2-dot">2</span><span class="topup-v2-slabel" id="tv2-sl2"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d3"><span class="topup-v2-dot">3</span><span class="topup-v2-slabel" id="tv2-sl3"></span></div>',"  </div>",'  <div class="topup-v2-body">','    <div id="tv2-s1">','      <label class="topup-v2-label" id="tv2-al"></label>','      <div class="topup-v2-qamts">','        <button class="topup-v2-qamt" data-val="100">฿100</button>','        <button class="topup-v2-qamt" data-val="500">฿500</button>','        <button class="topup-v2-qamt" data-val="1000">฿1,000</button>','        <button class="topup-v2-qamt" data-val="2000">฿2,000</button>',"      </div>",'      <input id="tv2-amt" type="number" min="10" step="1" class="topup-v2-input" placeholder="฿ ...">','      <div id="tv2-ae" class="topup-v2-err" style="display:none"></div>',"    </div>",'    <div id="tv2-s2" style="display:none">','      <p class="topup-v2-bank-label" id="tv2-bl"></p>','      <div class="topup-v2-bank-card">','        <div class="topup-v2-bank-name">ธนาคาร กรุงเทพ</div>','        <div class="topup-v2-bank-branch">สาขาโชคชัย 4 ลาดพร้าว</div>','        <div class="topup-v2-bank-acct">230-0-91368-4</div>','        <div class="topup-v2-bank-holder">บจ. มิสเตอร์ อี อาร์ พี</div>','        <button class="topup-v2-copy" id="tv2-copy"></button>',"      </div>",'      <div class="topup-v2-warn" id="tv2-bn"></div>',"    </div>",'    <div id="tv2-s3" style="display:none">','      <div class="topup-v2-drop" id="tv2-drop">','        <input type="file" id="tv2-file" accept="image/*,.pdf" style="display:none">','        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>','        <span class="topup-v2-drop-text" id="tv2-dt"></span>',"      </div>",'      <div id="tv2-se" class="topup-v2-err" style="display:none"></div>','      <label class="topup-v2-label" id="tv2-pl"></label>','      <input id="tv2-payer" type="text" maxlength="200" class="topup-v2-input">','      <label class="topup-v2-label" id="tv2-nl"></label>','      <input id="tv2-note" type="text" maxlength="500" class="topup-v2-input">','      <div id="tv2-ue" class="topup-v2-err" style="display:none"></div>',"    </div>","  </div>",'  <div class="topup-v2-foot">','    <button class="btn btn-ghost" id="tv2-back" style="display:none"></button>','    <button class="btn btn-primary" id="tv2-next"></button>',"  </div>","</div>"].join(""),document.body.appendChild(e),ia()}}function Ut(){var e=function(n,a){var o=ve(n);o&&(o.textContent=a)};e("tv2-title",he("topup-title")),e("tv2-sl1",he("topup-step1")),e("tv2-sl2",he("topup-step2")),e("tv2-sl3",he("topup-step3")),e("tv2-al",he("topup-amount-label")),e("tv2-bl",he("topup-bank-label")),e("tv2-copy",he("topup-copy-account")),e("tv2-dt",he("topup-slip-drop")),e("tv2-pl",he("topup-payer-label")),e("tv2-nl",he("topup-note-label"))}function Re(e){[1,2,3].forEach(function(s){var p=ve("tv2-s"+s);p&&(p.style.display=s===e?"":"none");var r=ve("tv2-d"+s);r&&r.classList.toggle("active",s<=e)});var n=ve("tv2-back"),a=ve("tv2-next");if(e===1?n&&(n.style.display="",n.textContent=he("topup-btn-cancel")):n&&(n.style.display="",n.textContent=he("topup-btn-back")),a&&(a.textContent=he(e===3?"topup-btn-submit":"topup-btn-next")),e===2){var o=ve("tv2-bn");o&&(o.innerHTML=he("topup-bank-note").replace("{amount}","<strong>฿"+Number(wt).toLocaleString()+"</strong>"))}}function pt(){for(var e=1;e<=3;e++){var n=ve("tv2-s"+e);if(n&&n.style.display!=="none")return e}return 1}function Ye(e){var n=ve(e);n&&(n.textContent="",n.style.display="none")}function qe(e,n){var a=ve(e);a&&(a.textContent=n,a.style.display="")}function Bt(e){var n=ve("tv2-dt");n&&(n.textContent=e.name);var a=ve("tv2-drop");a&&a.classList.add("has-file"),Ye("tv2-se")}function ia(){var e=ve("topup-v2-ov");ve("tv2-close").addEventListener("click",Pe),e.addEventListener("click",function(p){p.target===e&&Pe()}),document.addEventListener("keydown",function(p){p.key==="Escape"&&e&&e.style.display!=="none"&&Pe()}),e.addEventListener("click",function(p){var r=p.target.closest(".topup-v2-qamt");if(r){e.querySelectorAll(".topup-v2-qamt").forEach(function(i){i.classList.remove("active")}),r.classList.add("active");var f=ve("tv2-amt");f&&(f.value=r.dataset.val,Ye("tv2-ae"))}});var n=ve("tv2-amt");n&&n.addEventListener("input",function(){e.querySelectorAll(".topup-v2-qamt").forEach(function(p){p.classList.remove("active")}),Ye("tv2-ae")});var a=ve("tv2-copy");a&&a.addEventListener("click",function(){navigator.clipboard&&navigator.clipboard.writeText("2300913684").then(function(){var p=a.textContent;a.textContent=he("topup-copied"),setTimeout(function(){a.textContent=p},1500)})});var o=ve("tv2-drop"),s=ve("tv2-file");o&&(o.addEventListener("click",function(){s&&s.click()}),o.addEventListener("dragover",function(p){p.preventDefault(),o.classList.add("drag-over")}),o.addEventListener("dragleave",function(){o.classList.remove("drag-over")}),o.addEventListener("drop",function(p){p.preventDefault(),o.classList.remove("drag-over");var r=p.dataTransfer&&p.dataTransfer.files[0];r&&Bt(r)})),s&&s.addEventListener("change",function(){s.files[0]&&Bt(s.files[0])}),ve("tv2-back").addEventListener("click",function(){var p=pt();if(p<=1){Pe();return}Re(p-1)}),ve("tv2-next").addEventListener("click",function(){var p=pt();p===1?ra():p===2?Re(3):la()})}async function ra(){var e=ve("tv2-amt"),n=e?parseFloat(e.value):0;if(!n||n<10){qe("tv2-ae",he("topup-amount-invalid"));return}if(n>5e5){qe("tv2-ae",he("topup-amount-too-large"));return}wt=n;var a=ve("tv2-next");a&&(a.disabled=!0,a.textContent="…");try{var o=await fetch("/api/credits/topup/request",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+bt()},body:JSON.stringify({amount_thb:n})});if(!o.ok){var s=await o.text(),p=he("topup-submit-fail");try{var r=JSON.parse(s),f=r.detail;if(Array.isArray(f)&&f.length){var i=f[0]&&f[0].type||"";i.indexOf("less_than")>=0?p=he("topup-amount-too-large"):(i.indexOf("greater_than")>=0||i.indexOf("parsing")>=0)&&(p=he("topup-amount-invalid"))}else typeof f=="string"&&(p=f)}catch{}throw new Error(p)}var c=await o.json();yt=c.request_id,Re(2)}catch(l){qe("tv2-ae",l.message||he("topup-submit-fail"))}finally{a&&(a.disabled=!1,a.textContent=he("topup-btn-next"))}}async function la(){var e=ve("tv2-file");if(!e||!e.files||!e.files[0]){qe("tv2-se",he("topup-slip-required"));return}var n=ve("tv2-next");n&&(n.disabled=!0,n.textContent="…");try{var a=new FormData;a.append("file",e.files[0]);var o=ve("tv2-payer"),s=ve("tv2-note");o&&o.value.trim()&&a.append("payer_name",o.value.trim()),s&&s.value.trim()&&a.append("note",s.value.trim());var p=await fetch("/api/credits/topup/upload-slip/"+yt,{method:"POST",headers:{Authorization:"Bearer "+bt()},body:a});if(!p.ok)throw new Error(await p.text());var r=await p.json();r.auto_approved?(window.showToast&&window.showToast(he("topup-auto-approved"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard()):window.showToast&&window.showToast(he("topup-pending"),"info"),Pe()}catch(f){qe("tv2-ue",he("topup-upload-fail")+" · "+f.message),n&&(n.disabled=!1,n.textContent=he("topup-btn-submit"))}}function Pe(){var e=ve("topup-v2-ov");e&&(e.style.display="none"),typeof window.loadDashboard=="function"&&window.loadDashboard()}window._openTopupModal=function(){sa(),yt=null,wt=0,["tv2-amt","tv2-payer","tv2-note"].forEach(function(a){var o=ve(a);o&&(o.value="")});var e=ve("tv2-file");e&&(e.value="");var n=ve("tv2-drop");n&&n.classList.remove("has-file","drag-over"),ve("topup-v2-ov").querySelectorAll(".topup-v2-qamt").forEach(function(a){a.classList.remove("active")}),["tv2-ae","tv2-se","tv2-ue"].forEach(function(a){Ye(a)}),Ut(),Re(1),ve("topup-v2-ov").style.display="flex"};typeof window.subscribeI18n=="function"&&window.subscribeI18n("topup-v2",function(){var e=ve("topup-v2-ov");e&&e.style.display!=="none"&&e.style.display!==""&&(Ut(),Re(pt()))});(function(){const e="v118.28.5",n="pearnly_tc_results_"+e,a=[{id:"A1",group:"A · 异常栏 page-head(BUG1)",desc:"手机宽度进异常栏 · 标题「异常栏」横排正常 · 不再每字一行"},{id:"A2",group:"A · 异常栏 page-head(BUG1)",desc:"副标题「所有被规则拦截的单据集中复核…」也横排正常 · 不竖排"},{id:"A3",group:"A · 异常栏 page-head(BUG1)",desc:"客户筛选下拉 + 刷新按钮换到新一行 · 不抢标题宽度"},{id:"B1",group:"B · 客户管理 page-head(BUG2)",desc:"手机宽度进客户管理 · 标题「客户管理」横排正常"},{id:"B2",group:"B · 客户管理 page-head(BUG2)",desc:"副标题「为每家客户单独归档发票…」横排正常 · 不竖排"},{id:"B3",group:"B · 客户管理 page-head(BUG2)",desc:"「+ 新建客户」按钮换到新一行 · 不挤标题"},{id:"C1",group:"C · 客户卡片(BUG3)",desc:"客户卡片「编辑 / 导出本月」按钮文字清晰 · 不被截断"},{id:"D1",group:"D · 历史表头(BUG4)",desc:"手机宽度进单据记录 · 表头「文件·发票号·供应商」/「金额」单行 · 不竖排"},{id:"D2",group:"D · 历史表头(BUG4)",desc:"行内 INV-TH-202605-1006 这种长发票号正常单行展示 · 不一字一行"},{id:"E1",group:"E · 对账切换器(BUG6)",desc:"手机宽度进对账中心 · 顶栏点「全部客户」chip · 下拉从右上角向下展开 · 右对齐 · 不贴左屏边"},{id:"E2",group:"E · 对账切换器(BUG6)",desc:"下拉宽度自适应屏幕 · 不超出屏幕右边"},{id:"F1",group:"F · 通用设置回归",desc:"设置 → 个人资料 · 没有「界面语言」4 按钮卡"},{id:"F2",group:"F · 通用设置回归",desc:"左侧 nav 顺序:账户 / 公司 / 工作流 / 系统 / 关于"},{id:"F3",group:"F · 通用设置回归",desc:"系统 → 通用设置 · 4 行下拉(语言/时区/日期/数字)· 改语言立即切语言 · 改其他保存后 F5 仍保留"},{id:"G1",group:"G · 移动端 settings(回归)",desc:"手机宽度设置 tabs 不重叠 · 按分组分行 · chip 风格"},{id:"H1",group:"H · 回归",desc:"OCR 上传识别 / 客户管理 / 异常栏 / 对账中心 / 测试中心 全部仍工作"},{id:"H2",group:"H · 回归",desc:"4 语切换没新增异常(测试中心异常日志「API 失败」过滤无新条目)"},{id:"I1",group:"I · 三档移动 viewport",desc:"iPhone SE 375 · 上述 BUG 1-6 都修了"},{id:"I2",group:"I · 三档移动 viewport",desc:"Galaxy S 360 · 上述 BUG 1-6 都修了"},{id:"I3",group:"I · 三档移动 viewport",desc:"iPhone 12 Pro 414 · 上述 BUG 1-6 都修了"}];let o={},s="all",p=!1,r=!1;function f(G,W,te){let re=typeof t=="function"?t(G):null;return(!re||re===G)&&(re=W),te&&Object.keys(te).forEach(function(T){re=String(re).replace("{"+T+"}",String(te[T]))}),re}function i(){try{const G=localStorage.getItem(n);o=G?JSON.parse(G):{},(typeof o!="object"||!o)&&(o={})}catch{o={}}}function c(){try{localStorage.setItem(n,JSON.stringify(o))}catch{}}function l(G){const W=new Date(G),te=function(re){return re<10?"0"+re:""+re};return te(W.getHours())+":"+te(W.getMinutes())+":"+te(W.getSeconds())}function d(G){return String(G??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function u(G,W){try{typeof showToast=="function"?showToast(G,W||"info"):alert(G)}catch{}}function g(G){try{navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(G).then(function(){u(f("tc-toast-copied","已复制到剪贴板"),"success")}).catch(function(){w(G)}):w(G)}catch{w(G)}}function w(G){try{const W=document.createElement("textarea");W.value=G,W.style.position="fixed",W.style.opacity="0",document.body.appendChild(W),W.select();const te=document.execCommand("copy");document.body.removeChild(W),u(te?f("tc-toast-copied","已复制"):f("tc-toast-copy-fail","复制失败"),te?"success":"error")}catch{u(f("tc-toast-copy-fail","复制失败"),"error")}}function $(){const G=document.getElementById("tc-account-chip"),W=document.getElementById("tc-progress-chip");if(G&&(G.textContent=_userInfo&&(_userInfo.email||_userInfo.username)||"—"),W){const te=a.length,re=a.filter(function(T){return o[T.id]}).length;W.textContent=re+" / "+te}}function E(){const G=document.getElementById("tc-checklist-body");if(!G)return;const W={};a.forEach(function(re){W[re.group]||(W[re.group]=[]),W[re.group].push(re)});const te=[];Object.keys(W).forEach(function(re){te.push('<div class="tc-checklist-group">'),te.push('<div class="tc-checklist-group-title">'+d(re)+"</div>"),W[re].forEach(function(T){const x=o[T.id]||"",h=x?"is-"+x:"";te.push('<div class="tc-check-item '+h+'" data-id="'+d(T.id)+'"><div class="tc-check-id">'+d(T.id)+'</div><div class="tc-check-desc">'+d(T.desc)+'</div><div class="tc-check-actions">'+_(T.id,"pass",x)+_(T.id,"fail",x)+_(T.id,"skip",x)+"</div></div>")}),te.push("</div>")}),G.innerHTML=te.join("")}function _(G,W,te){const re=te===W,T={pass:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="4,11 8,15 16,5"/></svg>',fail:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="5" x2="15" y2="15"/><line x1="15" y1="5" x2="5" y2="15"/></svg>',skip:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="10" x2="15" y2="10"/></svg>'},x={pass:f("tc-status-pass","通过"),fail:f("tc-status-fail","失败"),skip:f("tc-status-skip","跳过")};return'<button type="button" class="tc-status-btn '+(re?"is-active "+W:"")+'" data-id="'+d(G)+'" data-kind="'+W+'" title="'+d(x[W])+'">'+T[W]+"</button>"}function B(G){return s==="all"?!0:s==="js_error"?G.type==="js_error"||G.type==="promise_error":s==="api"?G.type==="api_error"||G.type==="api_fail":s==="api_slow"?G.type==="api_slow":s==="console"?G.type==="console_error"||G.type==="console_warn":!0}function q(){const G=document.getElementById("tc-logs-body"),W=document.getElementById("tc-logs-count");if(!G)return;const te=(window._pearnlyTcLogs||[]).slice().reverse(),re=te.filter(B);if(W&&(W.textContent=String(te.length)),re.length===0){G.innerHTML='<div class="tc-logs-empty">'+d(f("tc-logs-empty","暂无异常"))+"</div>";return}const T=re.slice(0,100).map(function(x){const h=typeof x.detail=="object"?JSON.stringify(x.detail,null,2):String(x.detail||"");return'<div class="tc-log-item t-'+d(x.type)+'" data-ts="'+x.ts+'"><span class="tc-log-time">'+l(x.ts)+'</span><span class="tc-log-type">'+d(x.type)+'</span><div class="tc-log-summary">'+d(x.summary)+'<div class="tc-log-detail">'+d(h)+"</div></div></div>"}).join("");G.innerHTML=T,document.querySelectorAll("#tc-logs-filter .tc-filter-chip").forEach(function(x){x.classList.toggle("active",x.getAttribute("data-filter")===s)})}function H(){r||(r=!0,setTimeout(function(){r=!1,currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&q(),F()},200))}window._tcOnNewLog=H;function F(){const G=document.getElementById("nav-test-badge");if(!G)return;const W=(window._pearnlyTcLogs||[]).filter(function(te){return te.type==="js_error"||te.type==="promise_error"||te.type==="api_error"||te.type==="api_fail"||te.type==="console_error"}).length;W>0?(G.style.display="",G.textContent=W>99?"99+":String(W)):G.style.display="none"}function A(){$(),E(),q(),F()}function y(){const G=[],W=new Date,te=_userInfo&&(_userInfo.email||_userInfo.username)||"—";G.push("# Pearnly "+e+" 测试结果"),G.push("- 账号:"+te),G.push("- 时间:"+W.toISOString().replace("T"," ").slice(0,19));const re=a.length,T=a.filter(function(Q){return o[Q.id]==="pass"}).length,x=a.filter(function(Q){return o[Q.id]==="fail"}).length,h=a.filter(function(Q){return o[Q.id]==="skip"}).length,D=re-T-x-h;G.push("- 进度:"+(T+x+h)+" / "+re+" · ✅ "+T+" · ❌ "+x+" · ⏭ "+h+" · 未测 "+D),G.push(""),G.push("| ID | 描述 | 状态 |"),G.push("|---|---|---|"),a.forEach(function(Q){const le=o[Q.id],ie=le==="pass"?"✅":le==="fail"?"❌":le==="skip"?"⏭":"⬜";G.push("| "+Q.id+" | "+Q.desc.replace(/\|/g,"\\|")+" | "+ie+" |")});const N=a.filter(function(Q){return o[Q.id]==="fail"});N.length>0&&(G.push(""),G.push("## ❌ 失败项"),N.forEach(function(Q){G.push("- **"+Q.id+"** · "+Q.desc)}));const K=(window._pearnlyTcLogs||[]).slice(-30).reverse();return K.length>0&&(G.push(""),G.push("## 🔴 异常日志(最近 "+K.length+" 条)"),K.forEach(function(Q){if(G.push("- `"+l(Q.ts)+"` · **"+Q.type+"** · "+Q.summary),Q.detail){let le;try{le=JSON.stringify(Q.detail)}catch{le=String(Q.detail)}le&&le!=="{}"&&G.push("  - "+le.slice(0,600))}})),G.join(`
`)}function v(G){const W=(window._pearnlyTcLogs||[]).slice(-30).reverse();if(W.length===0)return"(暂无异常日志)";const te=["# Pearnly 异常日志(最近 "+W.length+" 条)"],re=_userInfo&&(_userInfo.email||_userInfo.username)||"—";return te.push("- 账号:"+re),te.push("- 当前页:"+(currentRoute||"?")),te.push("- UA:"+navigator.userAgent),te.push(""),W.forEach(function(T){if(te.push("## `"+l(T.ts)+"` · "+T.type),te.push("- "+T.summary),T.detail){te.push("```");try{te.push(JSON.stringify(T.detail,null,2).slice(0,2e3))}catch{te.push(String(T.detail).slice(0,2e3))}te.push("```")}}),te.join(`
`)}function b(){const G=Date.now();fetch("/api/health").then(function(W){const te=Date.now()-G;W.ok?u(f("tc-toast-health-ok","后端健康 ✓ {ms}ms",{ms:te}),"success"):u(f("tc-toast-health-fail","后端无响应")+" ("+W.status+")","error")}).catch(function(){u(f("tc-toast-health-fail","后端无响应"),"error")})}function L(){try{localStorage.removeItem(n),localStorage.removeItem("pearnly_current_client_id"),o={},(window._pearnlyTcLogs||[]).length=0,s="all",window.setCurrentClientId}catch{}A(),u(f("tc-toast-cleared","session 状态已清空"),"success")}function C(){try{fetch("/api/clients",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}).then(function(G){return G.json()}).then(function(G){window._clientsCache=G.clients||[],typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher(),typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter(),u("客户缓存已刷新 · "+(G.clients||[]).length+" 个客户","success")}).catch(function(){u("刷新失败","error")})}catch{}}function P(){if(p||!document.getElementById("page-test-center"))return;p=!0;const W=document.getElementById("tc-checklist-body");W&&W.addEventListener("click",function(le){const ie=le.target.closest(".tc-status-btn");if(!ie)return;const V=ie.getAttribute("data-id"),Z=ie.getAttribute("data-kind");!V||!Z||(o[V]===Z?delete o[V]:o[V]=Z,c(),E(),$())});const te=document.getElementById("tc-btn-reset-checklist");te&&te.addEventListener("click",function(){o={},c(),E(),$()});const re=document.getElementById("tc-btn-copy-all");re&&re.addEventListener("click",function(){g(y())});const T=document.getElementById("tc-btn-copy-logs");T&&T.addEventListener("click",function(){g(v())});const x=document.getElementById("tc-btn-clear-logs");x&&x.addEventListener("click",function(){(window._pearnlyTcLogs||[]).length=0,q(),F()});const h=document.getElementById("tc-logs-filter");h&&h.addEventListener("click",function(le){const ie=le.target.closest(".tc-filter-chip");ie&&(s=ie.getAttribute("data-filter")||"all",q())});const D=document.getElementById("tc-logs-body");D&&D.addEventListener("click",function(le){const ie=le.target.closest(".tc-log-item");ie&&ie.classList.toggle("expanded")});const N=document.getElementById("tc-tool-health");N&&N.addEventListener("click",b);const K=document.getElementById("tc-tool-clear-session");K&&K.addEventListener("click",L);const Q=document.getElementById("tc-tool-reload-clients");Q&&Q.addEventListener("click",C)}function I(){}window._tcApplyVisibility=I;let j=0;const Y=setInterval(function(){j++,_userInfo&&clearInterval(Y),j>60&&clearInterval(Y)},500);window.loadTestCenterPage=function(){i(),P(),A()},typeof window.subscribeI18n=="function"&&window.subscribeI18n("test-center",function(){F(),currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&A()})})();(function(){const e="pearnly_active_workspace_client_id",n="pearnly_work_mode";function a(B,q){if(typeof window.t=="function"){const H=window.t(B);if(H&&H!==B)return H}return q}function o(){const B=window._userInfo||{},q=String(B.role||"").toLowerCase(),H=String(B.tenant_role||"").toLowerCase();return B.is_super_admin===!0||B.is_owner===!0||q==="owner"||q==="admin"||H==="owner"||H==="admin"}function s(){return localStorage.getItem(n)==="client"?"client":"personal"}function p(){const B=localStorage.getItem(e);if(!B||B==="null"||B==="0"||B==="")return null;const q=parseInt(B,10);return isNaN(q)?null:q}function r(B){try{window.dispatchEvent(new CustomEvent("pearnly:workspace-changed",{detail:{id:B,mode:s()}}))}catch{}}function f(B){const q=p();B==null||B===0?localStorage.removeItem(e):(localStorage.setItem(e,String(B)),localStorage.setItem(n,"client")),String(q)!==String(B)&&r(B)}function i(){const B=p();localStorage.setItem(n,"personal"),localStorage.removeItem(e),B!=null&&r(null)}async function c(){try{const B=window.apiGet;if(typeof B!="function")return[];const q=await B("/api/workspace/clients");return q&&(q.clients||q.items)||[]}catch{return[]}}async function l(B){if(s()==="client"&&p()!=null)return typeof B=="function"&&B(),!0;const q=a("ws-need-client","这个功能需要先选择工作空间"),H=a("ws-btn-pick","选择工作空间"),F=a("ws-btn-cancel","取消");return typeof window.showConfirm=="function"?await window.showConfirm(q,{okText:H,cancelText:F})&&d(B):window.confirm(q+`

[`+H+" / "+F+"]")&&d(B),!1}async function d(B){const q=await c();if(typeof B=="function"&&s()!=="personal"&&q.length===1){f(Number(q[0].id)),B();return}if(typeof window.openWorkspaceChooserUI=="function"){window.openWorkspaceChooserUI({clients:q,canCreate:o(),active:p(),onPersonal:i,onPick:function(H){f(Number(H)),typeof B=="function"&&B()},emptyHint:q.length?null:o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。")});return}if(!q.length){const H=o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。");typeof window.showToast=="function"&&window.showToast(H,"info")}}function u(B){const q=B||document.getElementById("workspace-switcher-root");if(!q)return;const H=s(),F=p();let A,y;if(H==="client"&&F!=null){const L=(window._workspaceClientsCache||[]).find(C=>Number(C.id)===Number(F));A=w("building"),y=L?L.name:a("ws-current-label","当前工作空间")}else A=w("user"),y=a("ws-personal","个人事务");q.innerHTML='<button class="ws-ctrl-btn" id="ws-ctrl-btn" type="button">'+A+'<span class="ws-ctrl-label">'+g(y)+"</span></button>";const v=q.querySelector("#ws-ctrl-btn");v&&v.addEventListener("click",()=>d(null))}function g(B){return String(B??"").replace(/[&<>"']/g,function(q){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[q]})}function w(B){const q='<svg class="ws-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';return B==="building"?q+'<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>':q+'<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'}function $(B){B=B||{};const q=B.clients||[],H=B.active,F=document.getElementById("ws-modal");F&&F.remove();const A=document.createElement("div");A.id="ws-modal",A.className="ws-modal";const v='<button type="button" class="ws-modal-item'+(s()==="personal"||H==null?" active":"")+'" data-ws-personal="1"><span class="ws-modal-item-ic">'+w("user")+'</span><span class="ws-modal-item-text" style="display:flex;flex-direction:column;align-items:flex-start;min-width:0;"><span class="ws-modal-item-name">'+g(a("ws-personal","个人事务"))+'</span><span class="ws-modal-item-desc" style="font-size:11px;color:#6b7280;font-weight:400;margin-top:2px;line-height:1.35;white-space:normal;">'+g(a("ws-personal-desc","用于临时识别、测试或处理不归属任何公司的文件。"))+"</span></span></button>";let b="";if(q.length){const j=['<option value="">'+g(a("ws-select-ph","— 选择账套主体 —"))+"</option>"].concat(q.map(function(Y){const G=H!=null&&Number(H)===Number(Y.id);return'<option value="'+g(Y.id)+'"'+(G?" selected":"")+">"+g(Y.name||"#"+Y.id)+"</option>"}));b='<div class="ws-modal-select-row"><label class="ws-modal-select-label">'+g(a("ws-select-label","账套主体"))+'</label><select class="ws-modal-select" data-ws-select="1">'+j.join("")+"</select></div>"}const L=!q.length&&B.emptyHint?'<div class="ws-modal-empty">'+g(B.emptyHint)+"</div>":"",C=B.canCreate?'<div class="ws-modal-create"><button type="button" class="ws-modal-create-toggle" data-ws-create-toggle="1">+ '+g(a("ws-create-client","新建工作空间"))+'</button><div class="ws-modal-create-form" data-ws-create-form style="display:none;"><input type="text" class="ws-modal-create-input" data-ws-create-name placeholder="'+g(a("ws-create-ph","公司名称,例如 BAKELAB"))+'"><button type="button" class="ws-modal-create-submit" data-ws-create-submit="1">'+g(a("ws-create-submit","创建"))+"</button></div></div>":"";A.innerHTML='<div class="ws-modal-box" role="dialog" aria-modal="true"><div class="ws-modal-head"><span class="ws-modal-title">'+g(a("ws-chooser-title","选择工作空间"))+'</span><button type="button" class="ws-modal-close" data-ws-close="1" aria-label="close">✕</button></div><div class="ws-modal-subtitle" style="font-size:12px;color:#6b7280;padding:2px 4px 12px;line-height:1.45;white-space:normal;">'+g(a("ws-chooser-subtitle","账套主体 = 你的公司(发票卖方/开票方)。选择正在为哪家公司做账。"))+'</div><div class="ws-modal-list">'+v+b+"</div>"+L+C+"</div>",document.body.appendChild(A);const P=A.querySelector("[data-ws-select]");P&&P.addEventListener("change",function(){const j=P.value;j&&(typeof B.onPick=="function"&&B.onPick(j),I(),u())});function I(){A.remove()}A.addEventListener("click",function(j){if(j.target===A||j.target.closest("[data-ws-close]")){I();return}if(j.target.closest("[data-ws-personal]")){typeof B.onPersonal=="function"&&B.onPersonal(),I(),u();return}const G=j.target.closest("[data-ws-pick]");if(G){const re=G.getAttribute("data-ws-pick");typeof B.onPick=="function"&&B.onPick(re),I(),u();return}if(j.target.closest("[data-ws-create-toggle]")){const re=A.querySelector("[data-ws-create-form]");if(re){re.style.display=re.style.display==="none"?"flex":"none";const T=re.querySelector("[data-ws-create-name]");T&&T.focus()}return}if(j.target.closest("[data-ws-create-submit]")){E(A,B,I);return}})}async function E(B,q,H){const F=B.querySelector("[data-ws-create-name]"),A=F?(F.value||"").trim():"";if(!A){F&&F.focus();return}let y=null;try{if(typeof window.apiPost=="function"){const b=await window.apiPost("/api/workspace/clients",{name:A});y=b&&typeof b.json=="function"?await b.json().catch(()=>null):b}}catch{y=null}const v=y&&(y.id||y.client&&y.client.id);if(!v){typeof window.showToast=="function"&&window.showToast(a("ws-create-fail","新建工作空间失败 · 请重试"),"error");return}window._workspaceClientsCache=await c(),f(Number(v)),q.onPick,H(),u()}window.openWorkspaceChooserUI=$,window.addEventListener("pearnly:workspace-changed",function(){u()}),window.getWorkMode=s,window.getActiveWorkspaceClientId=p,window.setActiveWorkspaceClientId=f,window.enterPersonalMode=i,window.requireWorkspace=l,window.openWorkspaceChooser=d,window.renderWorkspaceControl=u,window.fetchWorkspaceClients=c;function _(){try{if(sessionStorage.getItem("pearnly_ws_login_prompted")==="1"||p()!=null||localStorage.getItem(n)==="personal")return;sessionStorage.setItem("pearnly_ws_login_prompted","1"),setTimeout(function(){d(null)},800)}catch{}}c().then(B=>{window._workspaceClientsCache=B,u(),_()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("workspace-switcher",u)})();(function(){const e=H=>document.querySelector('[data-num-target="'+H+'"]');function n(H){if(!H)return t("reconcile-last-activity-none");try{const F=new Date(H),A=new Date,y=A-F;if(y/6e4<5)return t("reconcile-last-activity-just-now");if(F.toDateString()===A.toDateString())return t("reconcile-last-activity-today");const b=Math.max(1,Math.floor(y/(24*3600*1e3)));return t("reconcile-last-activity-days-ago").replace("{n}",b)}catch{return t("reconcile-last-activity-none")}}function a(H,F,A){const y=e(H);y&&(y.textContent=A?"-":String(F),y.classList.toggle("is-empty",!!A))}function o(H){const F=document.getElementById("reconcile-error");F&&(F.style.display=H?"flex":"none")}function s(H){const F=document.getElementById("reconcile-empty");F&&(F.style.display=H?"flex":"none")}function p(H,F){const A=document.getElementById("reconcile-last-activity");A&&(A.textContent=H,A.classList.toggle("has-data",!!F))}function r(H){const F=!H||(H.total_sessions||0)===0;a("pending",H.pending||0,F),a("matched",H.matched||0,F),a("unmatched",H.unmatched||0,F),p(n(H.last_activity_at),!!H.last_activity_at),o(!1),s(F)}function f(H){const F=H.toUpperCase();return F==="KBANK"?"bank-chip-kbank":F==="SCB"?"bank-chip-scb":F==="BBL"?"bank-chip-bbl":F==="KTB"?"bank-chip-ktb":F==="TTB"?"bank-chip-ttb":"bank-chip-other"}function i(H,F){const A=y=>y?String(y).slice(0,10):"?";return!H&&!F?"":A(H)+" ~ "+A(F)}function c(H){return H==null?"":String(H).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function l(H){const F=document.getElementById("reconcile-recent"),A=document.getElementById("reconcile-recent-list");if(!F||!A)return;const y=(H||[]).slice(0,20);if(y.length===0){F.style.display="none";return}F.style.display="",s(!1),A.innerHTML=y.map(v=>{const b=v.parse_status==="parse_failed",L=v.bank_code||"OTHER",C=v.account_last4?" ···"+c(v.account_last4):"",P=i(v.period_start,v.period_end),I=c(v.source_filename||""),j=Number(v.tx_count||0),Y=b?'<span class="recon-card-fail" data-i18n="reconcile-card-parse-failed">'+t("reconcile-card-parse-failed")+"</span>":'<span class="recon-card-tx">'+t("reconcile-card-tx").replace("{n}",j)+"</span>";return'<div class="recon-card" data-session-id="'+c(v.id)+'" data-session-name="'+I+'"><span class="bank-chip '+f(L)+'">'+c(L)+'</span><div class="recon-card-main"><div class="recon-card-title">'+I+C+'</div><div class="recon-card-sub">'+c(P)+'</div></div><div class="recon-card-right">'+Y+'</div><button class="recon-card-trash" data-trash="'+c(v.id)+'" title="'+c(t("bank-session-delete-tip")||"删除")+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/></svg></button><svg class="recon-card-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg></div>'}).join(""),A.querySelectorAll(".recon-card").forEach(v=>{v.addEventListener("click",b=>{b.target.closest(".recon-card-trash")||(v.dataset.sessionId,d())})}),A.querySelectorAll(".recon-card-trash").forEach(v=>{v.addEventListener("click",b=>{b.stopPropagation();const L=v.dataset.trash,C=v.closest(".recon-card"),P=C&&C.dataset.sessionName||"";typeof window._deleteBankSession=="function"&&window._deleteBankSession(L,P)})})}function d(H){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const F=document.querySelector('[data-recon-tab="bank"]');F&&F.click()},150)}function u(){o(!0),s(!1)}function g(){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const H=document.querySelector('[data-recon-tab="bank"]');H&&H.click()},150)}async function w(){a("pending",0,!0),a("matched",0,!0),a("unmatched",0,!0),p("",!1),o(!1),s(!1);const H=document.getElementById("reconcile-recent");H&&(H.style.display="none");const F={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")};try{const[A,y]=await Promise.all([fetch("/api/bank-recon/stats",{headers:F}),fetch("/api/bank-recon/sessions?limit=20",{headers:F})]);if(!A.ok)throw new Error("http "+A.status);const v=await A.json(),b=y.ok?await y.json():[];r(v||{}),l(b||[])}catch(A){console.warn("[reconcile] load failed",A),u()}}function $(H){if(!H||!H.length)return;const F="Bearer "+(localStorage.getItem("mrpilot_token")||"");let A=0;const y=H.length;Array.from(H).forEach(function(v){const b=new FormData;b.append("file",v,v.name);const L=new XMLHttpRequest;L.open("POST","/api/bank-recon/upload"),L.setRequestHeader("Authorization",F),L.onload=function(){A++;try{const C=JSON.parse(L.responseText);L.status===200&&C.tx_count!==void 0?showToast((t("bank-upload-ok")||"解析成功 · 共 {n} 条流水").replace("{n}",C.tx_count),"success"):showToast(v.name+" "+(t("upload-failed")||"上传失败"),"error")}catch{showToast(v.name+" "+(t("upload-failed")||"上传失败"),"error")}A===y&&setTimeout(w,600)},L.onerror=function(){A++,showToast(v.name+" "+(t("upload-failed")||"上传失败"),"error"),A===y&&setTimeout(w,600)},L.send(b)}),showToast((t("bank-queue-status-uploading")||"上传中")+"…","info")}function E(){if(window.__reconcileBound)return;window.__reconcileBound=!0;const H=document.getElementById("reconcile-bank-file-input");H&&H.addEventListener("change",function(){$(this.files),this.value=""}),document.addEventListener("click",F=>{if(F.target.closest("#btn-reconcile-upload-top")||F.target.closest("#btn-reconcile-upload-empty")){g();return}if(F.target.closest("#btn-reconcile-retry")){w();return}if(F.target.closest("#btn-reconcile-dev-seed")){q();return}})}const _=["468b50c1-5593-4fd6-990d-515ce8085563"];function B(){const H=document.getElementById("btn-reconcile-dev-seed");if(!H)return;const F=typeof _userInfo<"u"?_userInfo:null,A=F&&F.id&&_.indexOf(String(F.id))>=0;H.style.display=A?"":"none"}async function q(){try{const H=await fetch("/api/bank-recon/_dev/seed",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!H.ok)throw new Error("seed:"+H.status);const F=await H.json(),A=(t("reconcile-dev-seed-ok")||"").replace("{n}",F.tx_count||0);showToast(A,"success"),typeof window.navigateTo=="function"?window.navigateTo("automation"):location.hash="#/automation",setTimeout(()=>{const y=document.querySelector('[data-auto-tab="bank"]');y&&y.click(),F.session_id&&typeof window._openBankSession=="function"&&window._openBankSession(F.session_id)},300)}catch(H){console.warn("[reconcile] dev seed failed",H),showToast(t("reconcile-dev-seed-fail")||"Seed failed","error")}}window.loadReconcilePage=async function(){E(),B(),typeof window._bankReconV2Init=="function"&&window._bankReconV2Init();try{await w()}catch{}},window._rerenderReconcile=function(){typeof currentRoute=="string"&&currentRoute==="reconcile"&&w().catch(()=>{})},typeof window.subscribeI18n=="function"&&window.subscribeI18n("reconcile",window._rerenderReconcile)})();(function(){const e=document.getElementById("assign-clients-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
    </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e={employeeId:null,employeeName:"",clients:[],selected:new Set,opened:!1};function n(){return document.getElementById("assign-clients-modal")}function a(){return document.getElementById("assign-clients-list")}function o(){return document.getElementById("assign-select-all")}function s(){return document.getElementById("assign-selected-count")}function p(){return document.getElementById("assign-modal-target")}function r(){const w=a();if(w){if(!e.clients.length){w.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-no-clients")||"暂无客户 · 请先到「客户管理」添加")+"</div>";return}w.innerHTML=e.clients.map($=>{const E=String($.id),_=e.selected.has(E)?"checked":"",B=escapeHtml($.name||$.label||"#"+E),q=$.code?'<span class="assign-row-code">'+escapeHtml($.code)+"</span>":"";return'<label class="assign-row"><input type="checkbox" data-cid="'+escapeHtml(E)+'" '+_+'><span class="assign-row-name">'+B+"</span>"+q+"</label>"}).join(""),f()}}function f(){const w=s();if(w){const E=t("assign-selected-count")||"已选 {n} / {total}";w.textContent=E.replace("{n}",e.selected.size).replace("{total}",e.clients.length)}const $=o();$&&($.checked=e.clients.length>0&&e.selected.size===e.clients.length)}function i(){const w=p();w&&(w.textContent=e.employeeName?" · "+e.employeeName:"")}async function c(w,$){e.employeeId=w,e.employeeName=$||"",e.opened=!0,e.selected=new Set,e.clients=[],i();const E=a();E&&(E.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-loading")||"加载中...")+"</div>");const _=n();_&&(_.style.display="flex");try{const[B,q]=await Promise.all([apiGet("/api/clients?include_inactive=false"),apiGet("/api/team/employees/"+encodeURIComponent(w)+"/assignments")]);e.clients=B&&B.clients||[];const H=q&&q.client_ids||[];e.selected=new Set(H.map(String)),r()}catch(B){console.error("[assign-clients] load failed",B);const q=a();q&&(q.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-load-failed")||"加载失败 · 请重试")+"</div>")}}function l(){e.opened=!1;const w=n();w&&(w.style.display="none")}async function d(){if(!e.employeeId)return;const w=Array.from(e.selected).map(E=>parseInt(E,10)).filter(E=>!isNaN(E)),$=document.getElementById("assign-modal-save");$&&($.disabled=!0);try{const E=await apiPost("/api/team/employees/"+encodeURIComponent(e.employeeId)+"/assignments",{client_ids:w});E&&E.ok!==!1?(showToast((t("assign-saved")||"已保存 {n} 个客户分配").replace("{n}",w.length),"success"),l(),typeof loadTeamList=="function"&&loadTeamList()):showToast(t("assign-save-failed")||"保存失败","error")}catch(E){console.error("[assign-clients] save failed",E),showToast(t("assign-save-failed")||"保存失败","error")}finally{$&&($.disabled=!1)}}function u(){const w=n();if(!w||w.dataset.bound==="1")return;w.dataset.bound="1";const $=document.getElementById("assign-modal-close");$&&$.addEventListener("click",l);const E=document.getElementById("assign-modal-cancel");E&&E.addEventListener("click",l);const _=document.getElementById("assign-modal-save");_&&_.addEventListener("click",d),w.addEventListener("click",function(H){H.target===w&&l()});const B=o();B&&B.addEventListener("change",function(){B.checked?e.selected=new Set(e.clients.map(H=>String(H.id))):e.selected=new Set,r()});const q=a();q&&q.addEventListener("change",function(H){const F=H.target.closest('input[type="checkbox"][data-cid]');if(!F)return;const A=F.dataset.cid;F.checked?e.selected.add(A):e.selected.delete(A),f()})}function g(){e.opened&&(i(),r())}typeof window.subscribeI18n=="function"&&window.subscribeI18n("assign-clients-modal",g),window.openAssignClientsModal=function(w,$){u(),c(w,$)}})();(function(){const e={page:1,per_page:50,q:"",total:0,rows:[],loaded:!1};function n(l){if(!l)return"";try{return new Date(l).toLocaleString()}catch{return l}}function a(l){const d=document.getElementById("access-log-table");d&&(d.innerHTML='<div class="access-log-empty">'+escapeHtml(l)+"</div>");const u=document.getElementById("access-log-pager");u&&(u.innerHTML="")}function o(){const l=document.getElementById("access-log-table");if(!l)return;const d=e.rows||[];if(!d.length){a(t("set-access-log-empty"));return}const u=`
            <div class="access-log-row access-log-head">
                <div>${escapeHtml(t("set-access-log-col-time"))}</div>
                <div>${escapeHtml(t("set-access-log-col-actor"))}</div>
                <div>${escapeHtml(t("set-access-log-col-action"))}</div>
                <div>${escapeHtml(t("set-access-log-col-target"))}</div>
                <div>${escapeHtml(t("set-access-log-col-ip"))}</div>
            </div>`,g=d.map(function(w){return`
                <div class="access-log-row">
                    <div class="access-log-time" data-label="${escapeHtml(t("set-access-log-col-time"))}">${escapeHtml(n(w.created_at))}</div>
                    <div class="access-log-actor" data-label="${escapeHtml(t("set-access-log-col-actor"))}">${escapeHtml(w.actor_username||"-")}</div>
                    <div data-label="${escapeHtml(t("set-access-log-col-action"))}"><span class="access-log-action">${escapeHtml(w.action||"-")}</span></div>
                    <div class="access-log-target" data-label="${escapeHtml(t("set-access-log-col-target"))}">${escapeHtml(w.target_name||w.target_type||"-")}</div>
                    <div class="access-log-ip" data-label="${escapeHtml(t("set-access-log-col-ip"))}">${escapeHtml(w.ip||"-")}</div>
                </div>`}).join("");l.innerHTML=u+g}function s(){const l=document.getElementById("access-log-pager");if(!l)return;const d=e.total||0;if(!d){l.innerHTML="";return}const u=e.page||1,g=e.per_page,w=Math.max(1,Math.ceil(d/g)),$=(t("set-access-log-pager-total")||"Total {n}").replace("{n}",d),E=(t("set-access-log-pager-page")||"Page {p} / {t}").replace("{p}",u).replace("{t}",w);l.innerHTML=`
            <div class="access-log-pager-info">${escapeHtml($)}</div>
            <div class="access-log-pager-ctrl">
                <button class="access-log-pager-btn" type="button" data-access-log-page="${u-1}" ${u<=1?"disabled":""}>← ${escapeHtml(t("set-access-log-pager-prev"))}</button>
                <span class="access-log-pager-page">${escapeHtml(E)}</span>
                <button class="access-log-pager-btn" type="button" data-access-log-page="${u+1}" ${u>=w?"disabled":""}>${escapeHtml(t("set-access-log-pager-next"))} →</button>
            </div>`}async function p(l){const d=localStorage.getItem("mrpilot_token");if(d){e.page=l||1,a(t("set-access-log-loading"));try{const u="/api/me/access_log?page="+e.page+"&per_page="+e.per_page+"&q="+encodeURIComponent(e.q||""),g=await fetch(u,{headers:{Authorization:"Bearer "+d}});if(g.status===403){a(t("set-access-log-empty"));return}if(!g.ok)throw new Error("http_"+g.status);const w=await g.json();e.rows=w.logs||[],e.total=w.total||0,e.loaded=!0,o(),s()}catch{a(t("set-access-log-fail"))}}}async function r(){const l=localStorage.getItem("mrpilot_token");if(l)try{const d="/api/me/access_log.csv?q="+encodeURIComponent(e.q||""),u=await fetch(d,{headers:{Authorization:"Bearer "+l}});if(!u.ok){showToast(t("set-access-log-csv-fail")||"Export failed","error");return}const g=await u.blob(),w=document.createElement("a"),$=URL.createObjectURL(g);w.href=$,w.download="pearnly_access_log.csv",document.body.appendChild(w),w.click(),setTimeout(function(){URL.revokeObjectURL($),w.remove()},100),showToast(t("set-access-log-csv-ok")||"Exported","success")}catch{showToast(t("set-access-log-csv-fail")||"Export failed","error")}}function f(){const l=document.querySelectorAll(".set-tab-owner-only"),d=!!(_userInfo&&(_userInfo.role==="owner"||_userInfo.is_super_admin));l.forEach(function(u){u.style.display=d?"":"none"})}document.addEventListener("click",function(l){if(l.target.closest('.settings-tab[data-tab="access-log"]')){setTimeout(function(){(!e.loaded||e.page!==1)&&p(1)},50);return}if(l.target.closest("#access-log-csv-btn")){l.preventDefault(),r();return}const g=l.target.closest(".access-log-pager-btn[data-access-log-page]");if(g&&!g.disabled){const w=parseInt(g.dataset.accessLogPage,10);p(w)}}),document.addEventListener("input",function(l){l.target&&l.target.id==="access-log-search"&&(clearTimeout(window.__accessLogSearchTimer),window.__accessLogSearchTimer=setTimeout(function(){e.q=(l.target.value||"").trim(),p(1)},350))});let i=0;const c=setInterval(function(){i++,_userInfo&&(f(),clearInterval(c)),i>60&&clearInterval(c)},500);typeof window.subscribeI18n=="function"&&window.subscribeI18n("me-access-log",function(){f(),e.loaded&&(o(),s())})})();(function(){const e=document.getElementById("notif-new-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=A=>document.getElementById(A);async function n(A,y){return await fetch(A,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(y||{})})}async function a(A){return await fetch(A,{method:"DELETE",headers:{Authorization:"Bearer "+token}})}let o=null;async function s(){try{o=await apiGet("/api/line/binding")}catch{o={bound:!1}}return o}function p(A,y){if(!A)return;A.style.display="",A.className="notif-line-check "+(y?"bound":"unbound");const v=y?'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>';A.innerHTML=v+"<span>"+escapeHtml(t(y?"notif-line-bound":"notif-line-not-bound"))+"</span>"}function r(A){if(A==null)return"-";const y=Number(A);return isNaN(y)?String(A):"฿ "+y.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function f(A){if(!A)return"-";try{const y=new Date(A),v=(y.getMonth()+1).toString().padStart(2,"0"),b=y.getDate().toString().padStart(2,"0"),L=y.getHours().toString().padStart(2,"0"),C=y.getMinutes().toString().padStart(2,"0");return`${v}-${b} ${L}:${C}`}catch{return A}}function i(A){const y=e("notif-rules-list"),v=e("notif-rules-empty"),b=e("notif-rules-count");if(!(!y||!v)){if(b.textContent=String(A.length),b.className="auto-status-pill "+(A.length>0?"active":"none"),!A.length){v.style.display="",y.style.display="none",y.innerHTML="";return}v.style.display="none",y.style.display="",y.innerHTML=A.map(L=>{const C=L.template_code==="large_invoice",P=C?"notif-rule-large-tag":"notif-rule-exception-tag",I=C?"large":"";let j=[];if(C){const G=L.params&&L.params.threshold?r(L.params.threshold):"-";j.push(escapeHtml(t("notif-rule-threshold-prefix"))+" "+G)}L.enabled||j.push('<span style="color:#9ca3af;">'+escapeHtml(t("notif-rule-disabled"))+"</span>");const Y=j.length?j.join(' <span class="dot"></span> '):"";return`
                <div class="notif-rule-row${L.enabled?"":" disabled"}" data-rule-id="${L.id}">
                    <span class="notif-rule-tmpl-badge ${I}">${escapeHtml(t(P))}</span>
                    <div class="notif-rule-main">
                        <div class="notif-rule-name">${escapeHtml(L.name)}</div>
                        <div class="notif-rule-meta">${Y}</div>
                    </div>
                    <div class="notif-rule-actions">
                        <button class="notif-rule-toggle ${L.enabled?"on":""}" data-action="toggle" aria-label="toggle"></button>
                        <button class="notif-rule-btn" data-action="test">${escapeHtml(t("notif-action-test"))}</button>
                        <button class="notif-rule-btn danger" data-action="delete">${escapeHtml(t("notif-action-delete"))}</button>
                    </div>
                </div>`}).join("")}}function c(A){const y=e("notif-logs-list");if(y){if(!A.length){y.innerHTML='<div class="notif-logs-empty">'+escapeHtml(t("notif-logs-empty"))+"</div>";return}y.innerHTML=A.map(v=>{const b=v.status==="sent",L=v.event_type==="exception_high"?"notif-event-exception-high":v.event_type==="large_invoice"?"notif-event-large-invoice":"notif-event-test-send",C=b?"":" · "+escapeHtml(v.error||"failed");return`
                <div class="notif-log-row">
                    <span class="notif-log-status ${b?"":"failed"}"></span>
                    <div class="notif-log-main">
                        <div class="notif-log-event">${escapeHtml(t(L))}</div>
                        <div class="notif-log-meta">${escapeHtml(v.template_code||"-")}${C}</div>
                    </div>
                    <div class="notif-log-time">${f(v.sent_at)}</div>
                </div>`}).join("")}}async function l(){try{const A=await apiGet("/api/notifications/rules");d=A&&A.items||[],i(d)}catch(A){console.warn("load rules fail",A)}try{const A=await apiGet("/api/notifications/logs?limit=20");u=A&&A.items||[],c(u)}catch(A){console.warn("load logs fail",A)}}let d=null,u=null;function g(){d&&i(d),u&&c(u);const A=e("notif-new-modal");A&&A.style.display!=="none"&&o&&p(e("notif-line-check"),!!(o&&o.bound))}function w(){const A=e("notif-new-modal");A&&(A.style.display="",e("notif-new-name").value="",e("notif-new-threshold").value="",e("notif-new-threshold-row").style.display="none",document.querySelectorAll('input[name="notif-template"]').forEach(y=>y.checked=!1),s().then(y=>p(e("notif-line-check"),!!(y&&y.bound))))}function $(){const A=e("notif-new-modal");A&&(A.style.display="none")}function E(){const A=document.querySelector('input[name="notif-template"]:checked'),y=e("notif-new-threshold-row");if(!A){y.style.display="none";return}y.style.display=A.value==="large_invoice"?"":"none";const v=e("notif-new-name");v&&!v.value.trim()&&(v.value=A.value==="large_invoice"?t("notif-tmpl-large-name"):t("notif-tmpl-exception-name"))}async function _(){const A=document.querySelector('input[name="notif-template"]:checked');if(!A){showToast(t("notif-new-template"),"error");return}const y=(e("notif-new-name").value||"").trim();if(!y){showToast(t("notif-name-required"),"error");return}const v={name:y,template_code:A.value,params:{},enabled:!0};if(A.value==="large_invoice"){const b=parseFloat(e("notif-new-threshold").value||"0");if(!b||b<=0){showToast(t("notif-threshold-required"),"error");return}v.params.threshold=b}try{const b=await apiPost("/api/notifications/rules",v);if(b&&b.ok)showToast(t("notif-toast-created"),"success"),$(),l();else{const L=await(b&&b.json&&b.json().catch(()=>({})))||{};showToast(L&&L.detail||"save failed","error")}}catch{showToast("save failed","error")}}async function B(A,y,v){if(A==="toggle"){const b=v.classList.contains("on"),L=await n("/api/notifications/rules/"+y,{enabled:!b});L&&L.ok?(showToast(t(b?"notif-toast-toggled-off":"notif-toast-toggled-on"),"success"),l()):showToast("toggle failed","error");return}if(A==="test"){const b=await s();if(!b||!b.bound){showToast(t("notif-line-error-bind-first"),"error");return}const L=await apiPost("/api/notifications/rules/"+y+"/test",{});if(L&&L.ok)showToast(t("notif-toast-test-sent"),"success"),l();else{const C=await(L&&L.json&&L.json().catch(()=>({})))||{},P=C&&C.detail||"";showToast(P||t("notif-toast-test-failed"),"error"),l()}return}if(A==="delete"){if(!await showConfirm(t("notif-confirm-delete"),{danger:!0}))return;const L=await a("/api/notifications/rules/"+y);L&&L.ok?(showToast(t("notif-toast-deleted"),"success"),l()):showToast("delete failed","error");return}}let q=!1;function H(){if(q)return;q=!0;const A=e("notif-btn-new");A&&A.addEventListener("click",w);const y=e("notif-btn-refresh-logs");y&&y.addEventListener("click",l);const v=e("notif-new-close");v&&v.addEventListener("click",$);const b=e("notif-new-cancel");b&&b.addEventListener("click",$);const L=e("notif-new-save");L&&L.addEventListener("click",_),document.querySelectorAll('input[name="notif-template"]').forEach(I=>{I.addEventListener("change",E)});const C=e("notif-rules-list");C&&C.addEventListener("click",I=>{const j=I.target.closest("button[data-action]");if(!j)return;const Y=j.closest("[data-rule-id]");Y&&B(j.getAttribute("data-action"),Y.getAttribute("data-rule-id"),j)});const P=e("notif-new-modal");P&&P.addEventListener("click",I=>{I.target===P&&$()})}async function F(){H(),await l()}window._loadNotificationsPanel=F,window._rerenderNotifications=g})();(function(){function n(_,B){try{return window.t&&window.t(_)||B}catch{return B}}function a(){var _="";try{_=localStorage.getItem("mrpilot_token")||""}catch{}return _?{Authorization:"Bearer "+_}:{}}var o=[{tbody:"vex-task-tbody",api:"/api/recon/tasks/batch_delete",reload:function(){try{window.loadRecentTasks&&window.loadRecentTasks()}catch{}},kind:"vex"},{tbody:"glv-history-tbody",api:"/api/recon/gl-vat/tasks/batch_delete",reload:function(){try{window._loadGlvHistory&&window._loadGlvHistory()}catch{}},kind:"glv"},{tbody:"brv2-history-tbody",api:"/api/recon/bank-v2/tasks/batch_delete",reload:function(){try{window._brv2LoadHistory&&window._brv2LoadHistory()}catch{}},kind:"brv2"}];function s(){if(!document.getElementById("recon-batch-style")){var _=document.createElement("style");_.id="recon-batch-style",_.textContent=".recon-sel-cell{width:36px;text-align:center;padding-left:10px!important;padding-right:6px!important}.recon-sel-cb,.recon-master-cb{cursor:pointer;width:14px;height:14px;accent-color:#111;margin:0;vertical-align:middle}th.recon-time-col,td.recon-time-col{white-space:nowrap}tr.recon-thead-batch{display:none}thead.recon-batch-mode tr.recon-thead-default{display:none}thead.recon-batch-mode tr.recon-thead-batch{display:table-row}tr.recon-thead-batch th{background:#fafaf8;border-bottom:1px solid #e8e8e3;padding:8px 12px}tr.recon-thead-batch .recon-batch-inline{display:flex;align-items:center;gap:10px;font-size:12px;color:#111;font-weight:normal}tr.recon-thead-batch .recon-batch-count-inline{font-weight:600;color:#111;margin-right:4px}tr.recon-thead-batch .recon-batch-del-inline{background:#dc2626;color:#fff;border:none;border-radius:6px;padding:4px 10px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:4px}tr.recon-thead-batch .recon-batch-del-inline:hover{background:#b91c1c}tr.recon-thead-batch .recon-batch-clear-inline{background:transparent;border:none;color:#555;cursor:pointer;font-size:12px;font-family:inherit;text-decoration:underline;padding:4px 2px}tr.recon-thead-batch .recon-batch-clear-inline:hover{color:#111}.recon-batch-bar{display:none!important}",document.head.appendChild(_)}}function p(_){return _?_.dataset&&_.dataset.taskId?_.dataset.taskId:_.dataset&&_.dataset.taskid?_.dataset.taskid:"":""}function r(_){var B=document.getElementById(_.tbody);if(!B)return null;var q=B.closest("table");if(!q)return null;var H=q.querySelector("thead");if(!H)return null;if(H._reconReady)return H;var F=H.querySelector("tr");if(!F)return null;if(F.classList.add("recon-thead-default"),!F.querySelector(".recon-master-cb")){var A=document.createElement("th");A.className="recon-sel-cell";var y=document.createElement("input");y.type="checkbox",y.className="recon-master-cb",y.setAttribute("aria-label","select all"),y.addEventListener("change",function(){l(_,y.checked)}),A.appendChild(y),F.insertBefore(A,F.firstElementChild)}var v=F.children[1];v&&!v.classList.contains("recon-time-col")&&v.classList.add("recon-time-col");var b=F.children.length,L=document.createElement("tr");L.className="recon-thead-batch";var C=document.createElement("th");C.className="recon-sel-cell";var P=document.createElement("input");P.type="checkbox",P.className="recon-master-cb",P.checked=!0,P.setAttribute("aria-label","select all"),P.addEventListener("change",function(){l(_,P.checked)}),C.appendChild(P);var I=document.createElement("th");return I.setAttribute("colspan",String(b-1)),I.innerHTML='<div class="recon-batch-inline"><span class="recon-batch-count-inline" data-recon-count></span><button type="button" class="recon-batch-del-inline" data-recon-del><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg><span data-recon-del-label></span></button><button type="button" class="recon-batch-clear-inline" data-recon-clear></button></div>',L.appendChild(C),L.appendChild(I),H.appendChild(L),I.querySelector("[data-recon-del]").addEventListener("click",function(){w(_)}),I.querySelector("[data-recon-clear]").addEventListener("click",function(){g(_)}),H._reconReady=!0,u(_),H}function f(_){var B=document.getElementById(_.tbody);if(B){var q=B.querySelectorAll("tr");q.forEach(function(H){var F=p(H);if(F&&!H.querySelector(".recon-sel-cb")){var A=H.querySelector("td");if(A){var y=document.createElement("td");y.className="recon-sel-cell";var v=document.createElement("input");v.type="checkbox",v.className="recon-sel-cb",v.dataset.taskId=F,v.dataset.kind=_.kind,v.addEventListener("click",function(L){L.stopPropagation()}),v.addEventListener("change",function(){d(_)}),y.appendChild(v),H.insertBefore(y,A);var b=H.children[1];b&&!b.classList.contains("recon-time-col")&&b.classList.add("recon-time-col")}}}),d(_)}}function i(_){var B=document.getElementById(_.tbody);return B?Array.prototype.slice.call(B.querySelectorAll(".recon-sel-cb")):[]}function c(_){return i(_).filter(function(B){return B.checked}).map(function(B){return B.dataset.taskId})}function l(_,B){i(_).forEach(function(q){q.checked=!!B}),d(_)}function d(_){var B=c(_),q=i(_),H=document.getElementById(_.tbody);if(H){var F=H.closest("table"),A=F&&F.querySelector("thead");if(A){B.length>0?A.classList.add("recon-batch-mode"):A.classList.remove("recon-batch-mode"),A.querySelectorAll(".recon-master-cb").forEach(function(v){if(q.length===0){v.checked=!1,v.indeterminate=!1;return}B.length===q.length?(v.checked=!0,v.indeterminate=!1):B.length===0?(v.checked=!1,v.indeterminate=!1):(v.checked=!1,v.indeterminate=!0)});var y=A.querySelector("[data-recon-count]");y&&(y.textContent=n("recon-batch-selected-n","已选 {n} 条").replace("{n}",B.length))}}}function u(_){var B=document.getElementById(_.tbody);if(B){var q=B.closest("table"),H=q&&q.querySelector("thead");if(H){var F=H.querySelector("[data-recon-del-label]"),A=H.querySelector("[data-recon-clear]");F&&(F.textContent=n("recon-batch-delete","批量删除")),A&&(A.textContent=n("recon-batch-clear","取消")),d(_)}}}function g(_){i(_).forEach(function(B){B.checked=!1}),d(_)}async function w(_){var B=c(_);if(B.length){var q=n("recon-batch-delete-confirm","确定删除选中的 {n} 条对账任务?此操作不可恢复").replace("{n}",B.length),H=!1;try{typeof window.pearnlyConfirm=="function"?H=await window.pearnlyConfirm(q,n("recon-batch-delete-title","批量删除")):H=window.confirm(q)}catch{H=!1}if(H)try{var F=Object.assign({"Content-Type":"application/json"},a()),A=_.kind==="glv"?B.map(function(L){return parseInt(L,10)}):B,y=await fetch(_.api,{method:"POST",headers:F,body:JSON.stringify({ids:A})});if(!y.ok){typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error");return}var v=await y.json(),b=v&&(v.deleted!=null?v.deleted:v.count)||B.length;typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-ok","已删除 {n} 条").replace("{n}",b),"success"),_.reload()}catch{typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error")}}}function $(_){r(_),f(_);var B=document.getElementById(_.tbody);if(!(!B||B._reconBatchWatched)){B._reconBatchWatched=!0;var q=new MutationObserver(function(){f(_)});q.observe(B,{childList:!0,subtree:!1})}}function E(){s(),o.forEach($),document.querySelectorAll(".recon-batch-bar").forEach(function(_){try{_.remove()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",E):E(),setTimeout(E,1500),setTimeout(E,4e3),document.addEventListener("keydown",function(_){_.key==="Escape"&&o.forEach(function(B){c(B).length>0&&g(B)})}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-batch-thead",function(){o.forEach(u)})})();(function(){let e={role:"",monthly_volume:"",country:"",line_id:""},n=1;const a=4,o="pilot_ob_dismiss",s="pilot_ob_done";window.maybeShowOnboarding=function(c){};function p(c){n=c;for(let u=1;u<=a;u++){const g=document.getElementById("ob-step-"+u);g&&(g.style.display=u===c?"block":"none")}document.querySelectorAll(".ob-dot").forEach(u=>{const g=parseInt(u.dataset.step,10);u.classList.toggle("active",g===c),u.classList.toggle("done",g<c)});const l=document.getElementById("ob-step-label");l&&(l.textContent=c+" / "+a);const d=document.getElementById("ob-next");if(d&&(d.textContent=c===a?t("ob-finish"):t("ob-next")),c===4){const u=document.getElementById("ob-line-input");u&&(u.value=e.line_id||"")}}function r(c){const l=document.querySelector(".onboarding-modal");if(!l)return;let d=l.querySelector(".ob-feedback");d||(d=document.createElement("div"),d.className="ob-feedback",l.appendChild(d)),d.textContent=c,d.classList.add("show"),setTimeout(()=>d.classList.remove("show"),1800)}document.addEventListener("click",c=>{const l=c.target.closest(".ob-option");if(!l)return;const d=l.parentElement;if(!d||!d.classList.contains("ob-options"))return;d.querySelectorAll(".ob-option").forEach(g=>g.classList.remove("selected")),l.classList.add("selected");const u=l.dataset.value;d.id==="ob-role-options"?e.role=u:d.id==="ob-volume-options"?e.monthly_volume=u:d.id==="ob-country-options"&&(e.country=u)}),document.addEventListener("click",c=>{c.target.id==="ob-skip"&&f()}),document.addEventListener("click",c=>{if(c.target.id==="ob-next"){if(n===4){const l=document.getElementById("ob-line-input");e.line_id=(l&&l.value||"").trim().replace(/^@+/,"")}f()}}),document.addEventListener("click",c=>{if(c.target.closest("#ob-close")){localStorage.setItem(o,String(Date.now()));const l=document.getElementById("onboarding-modal");l&&(l.style.display="none")}});function f(){n===1&&e.role?r(t("ob-fb-role")):n===2&&e.monthly_volume?r(t("ob-fb-volume")):n===3&&e.country?r(t("ob-fb-country")):n===4&&e.line_id&&r(t("ob-fb-line")),n<a?setTimeout(()=>p(n+1),e[Object.keys(e)[n-1]]?350:0):i()}async function i(){const c=document.getElementById("onboarding-modal");localStorage.setItem(s,"1"),localStorage.removeItem(o);const l={};if(e.role&&(l.role=e.role),e.monthly_volume&&(l.monthly_volume=e.monthly_volume),e.country&&(l.country=e.country),e.line_id&&(l.line_id=e.line_id),Object.keys(l).length===0){c&&(c.style.display="none");return}try{const d=await fetch("/api/me/profile",{method:"PUT",headers:{Authorization:"Bearer "+(window.token||localStorage.getItem("mrpilot_token")),"Content-Type":"application/json"},body:JSON.stringify(l)});d.ok?(r(t("ob-fb-done")),window._userInfo&&Object.assign(window._userInfo,l),setTimeout(()=>{c&&(c.style.display="none")},1200)):(localStorage.setItem("pilot_ob_pending",JSON.stringify(l)),console.warn("onboarding profile save failed",d.status),r(t("ob-fb-saved-local")),setTimeout(()=>{c&&(c.style.display="none")},1500))}catch(d){console.error("onboarding submit",d),localStorage.setItem("pilot_ob_pending",JSON.stringify(l)),c&&(c.style.display="none")}}})();(function(){const e=document.getElementById("archive-rule-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
        </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e=[],n="by_month_seller",a=-1,o=!1;const s={date:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="3.5" width="11" height="10" rx="1.5"/><path d="M2.5 6.5h11M5.5 2v3M10.5 2v3"/></svg>',seller:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13.5V4a1 1 0 011-1h5a1 1 0 011 1v9.5"/><path d="M10 7h2.5a.5.5 0 01.5.5v6"/><path d="M5 6h1M5 9h1M5 12h1M13.5 13.5h-12"/></svg>',category:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 2h6L13 5.5v7.5a1 1 0 01-1 1H3.5a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M9 2v4h4"/><path d="M5 9h6M5 11.5h4"/></svg>',amount:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M8 4.5v7M10 6.3a1.8 1.8 0 00-4 0c0 .9.7 1.3 2 1.6s2 .8 2 1.6a1.8 1.8 0 01-4 0"/></svg>',invoice:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3.5l1.5 10.5 1.5-1 1.5 1 1.5-1 1.5 1 1.5-1 1.5 1L13 3.5z"/><path d="M5.5 6.5h5M5.5 9h5M5.5 11.5h3"/></svg>',buyer:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="6" r="2.5"/><path d="M3 13.5c0-2.5 2.2-4.5 5-4.5s5 2 5 4.5"/></svg>',sep:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v10"/></svg>'},p={date:{label:"field-date",defaultCfg:{format:"YYYY-MM-DD"}},seller:{label:"field-seller",defaultCfg:{short:!0}},category:{label:"field-category",defaultCfg:{}},amount:{label:"field-amount",defaultCfg:{with_currency:!0}},invoice:{label:"field-invoice",defaultCfg:{}},buyer:{label:"field-buyer",defaultCfg:{}},sep:{label:"field-sep",defaultCfg:{val:"_"}}};function r(){return{zh:"运费",en:"Shipping",th:"ค่าขนส่ง",ja:"送料"}[currentLang]||"Shipping"}function f(){return"DHL Express (Thailand) Co., Ltd."}function i(){return{merged_fields:{invoice_date:"2026-04-15",seller_name:f(),category:r(),total_amount:1250,currency:"THB",invoice_no:"INV-2026030002",buyer_name:"Mr.ERP Co., Ltd."}}}window.loadAboutPanel=()=>c(),window.loadPrefsSettings=()=>l(),window.loadArchiveSettings=()=>u();function c(){const y=document.getElementById("settings-contact-grid");if(!y)return;const v=_contact?.phone||"086-889-2228",b=_contact?.line_id||"@Pearnly",L=_contact?.line_url||"https://line.me/R/ti/p/@059oupmg",C=_contact?.email||"hello@pearnly.com",P=_contact?.address||"Bangkok, Thailand";y.innerHTML=`
            <a class="contact-item" href="${escapeHtml(L)}" target="_blank" rel="noopener">
                <div class="contact-icon line">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.365 9.863c.349 0 .63.285.631.631 0 .345-.282.63-.631.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.282.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63.346 0 .628.285.628.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-line"))}</div>
                    <div class="contact-value">${escapeHtml(b)}</div>
                </div>
            </a>
            <a class="contact-item" href="mailto:${escapeHtml(C)}">
                <div class="contact-icon email">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-email"))}</div>
                    <div class="contact-value">${escapeHtml(C)}</div>
                </div>
            </a>
            <a class="contact-item" href="tel:${escapeHtml(v.replace(/[^\d+]/g,""))}">
                <div class="contact-icon phone">
                    <svg viewBox="0 0 20 20" fill="currentColor"><path d="M2 3a1 1 0 011-1h2.5a1 1 0 01.97.757l1 4a1 1 0 01-.29.986l-1.75 1.75a11 11 0 005.07 5.07l1.75-1.75a1 1 0 01.986-.29l4 1a1 1 0 01.757.97V17a1 1 0 01-1 1h-1C8.82 18 2 11.18 2 3V3z"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-phone"))}</div>
                    <div class="contact-value">${escapeHtml(v)}</div>
                </div>
            </a>
            <div class="contact-item">
                <div class="contact-icon address">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s-7-7.5-7-13a7 7 0 1114 0c0 5.5-7 13-7 13z"/><circle cx="12" cy="9" r="2.5"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-address"))}</div>
                    <div class="contact-value">${escapeHtml(P)}</div>
                </div>
            </div>
        `}async function l(){try{const y=await fetch("/api/settings/dup-check",{headers:{Authorization:"Bearer "+token}});if(!y.ok)return;const v=await y.json(),b=document.getElementById("pref-dup-check");b&&(b.checked=!!v.enabled)}catch(y){console.warn("load prefs failed",y)}}const d=document.getElementById("pref-dup-check");d&&!d.dataset.bound&&(d.dataset.bound="1",d.addEventListener("change",async y=>{const v=y.target.checked;try{(await fetch("/api/settings/dup-check",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({enabled:v})})).ok?showToast(v?t("pref-dup-check-on-toast"):t("pref-dup-check-off-toast"),"success"):(y.target.checked=!v,showToast(t("pref-save-failed"),"error"))}catch{y.target.checked=!v,showToast(t("pref-save-failed"),"error")}}));async function u(){const y=!!(_userInfo&&_userInfo.can_customize_archive);o=!y;const v=document.getElementById("archive-upgrade-banner");v&&(v.style.display=y?"none":"");const b=document.getElementById("archive-plus-badge");b&&(b.style.display=y?"none":"");try{const L=await fetch("/api/archive/settings",{headers:{Authorization:"Bearer "+token}});if(!L.ok)throw new Error("load failed");const C=await L.json();e=Array.isArray(C.name_template)?C.name_template:[],n=C.folder_strategy||"by_month_seller"}catch(L){console.error("load archive settings failed",L),showToast(t("archive-load-failed"),"error");return}g(),w(),$(),E()}function g(){const y=document.getElementById("archive-rule-canvas");if(y){if(e.length===0){y.innerHTML=`<div class="archive-empty">${escapeHtml(t("archive-rule-empty"))}</div>`;return}y.innerHTML=e.map((v,b)=>{const L=p[v.type]||{label:v.type},C=s[v.type]||"",P=v.type==="sep"?`"${escapeHtml(v.val||"_")}"`:escapeHtml(t(L.label));return`
                <span class="archive-token ${v.type}"
                      data-token-idx="${b}"
                      draggable="${o?"false":"true"}">
                    <span class="token-icon">${C}</span>
                    <span class="token-label">${P}</span>
                </span>
            `}).join("")}}function w(){const y=document.getElementById("archive-field-palette");if(!y)return;const v=["date","seller","category","amount","invoice","buyer","sep"];y.innerHTML=v.map(b=>{const L=p[b],C=s[b]||"";return`
                <button class="archive-palette-btn ${b}" data-add-field="${b}" ${o?"disabled":""}>
                    <span class="token-icon">${C}</span>
                    <span>${escapeHtml(t(L.label))}</span>
                </button>
            `}).join("")}function $(){document.querySelectorAll('input[name="folder-strategy"]').forEach(y=>{y.checked=y.value===n,y.disabled=o})}async function E(){const y=document.getElementById("archive-preview-name"),v=document.getElementById("archive-preview-hint");if(v&&(v.textContent=t("archive-preview-hint",{category:r()})),!!y){if(e.length===0){y.textContent="-";return}try{const L=await(await fetch("/api/archive/rename-preview",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({merged_fields:i().merged_fields,name_template:e})})).json();y.textContent=(L.name||"-")+".pdf"}catch{y.textContent="("+t("archive-preview-error")+")"}}}window._rerenderArchiveAll=function(){const y=document.getElementById("archive-rule-modal");!y||y.style.display==="none"||(g(),w(),E())};let _=-1;document.addEventListener("dragstart",y=>{const v=y.target.closest(".archive-token");!v||o||(_=parseInt(v.dataset.tokenIdx,10),v.classList.add("dragging"),y.dataTransfer.effectAllowed="move")}),document.addEventListener("dragend",y=>{document.querySelectorAll(".archive-token").forEach(v=>v.classList.remove("dragging","drop-target")),_=-1}),document.addEventListener("dragover",y=>{const v=y.target.closest(".archive-token");v&&(y.preventDefault(),y.dataTransfer.dropEffect="move",document.querySelectorAll(".archive-token").forEach(b=>b.classList.remove("drop-target")),v.classList.add("drop-target"))}),document.addEventListener("drop",y=>{const v=y.target.closest(".archive-token");if(!v||_<0||o)return;y.preventDefault();const b=parseInt(v.dataset.tokenIdx,10);if(b===_)return;const L=e.splice(_,1)[0];e.splice(b,0,L),_=-1,g(),E()}),document.addEventListener("click",y=>{if(y.target.closest("#btn-open-archive-rule")||y.target.closest("#btn-open-archive-rule-from-settings")){const C=document.getElementById("archive-rule-modal");C&&(C.style.display="",u());return}if(y.target.closest("#archive-rule-modal-close")||y.target.id==="archive-rule-modal"){const C=document.getElementById("archive-rule-modal");C&&(C.style.display="none");return}const v=y.target.closest(".settings-nav-item");if(v){switchSettingsTab(v.dataset.settingsTab);return}if(o&&y.target.closest(".archive-token, [data-add-field], #btn-archive-save, #btn-archive-reset")){showToast(t("feature-contact-us"),"info");return}const b=y.target.closest("[data-add-field]");if(b){const C=b.dataset.addField,P=p[C],I={type:C,...P.defaultCfg};e.push(I),g(),E();return}const L=y.target.closest(".archive-token");if(L&&!o){B(parseInt(L.dataset.tokenIdx,10));return}if(y.target.closest("#btn-archive-save"))return F();if(y.target.closest("#btn-archive-reset"))return A();(y.target.closest("#archive-token-close")||y.target.id==="archive-token-modal")&&(document.getElementById("archive-token-modal").style.display="none"),y.target.closest("#btn-archive-token-ok")&&q(),y.target.closest("#btn-archive-token-delete")&&H()}),document.addEventListener("change",y=>{y.target.name==="folder-strategy"&&(n=y.target.value)});function B(y){a=y;const v=e[y];if(!v)return;const b=document.getElementById("archive-token-body");let L="";v.type==="date"?L=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-date-format"))}</label>
                    <select class="form-input" id="token-date-format">
                        <option value="YYYY-MM-DD" ${v.format==="YYYY-MM-DD"?"selected":""}>YYYY-MM-DD (2026-04-15)</option>
                        <option value="YYYYMMDD"   ${v.format==="YYYYMMDD"?"selected":""}>YYYYMMDD (20260415)</option>
                        <option value="YY.MM"      ${v.format==="YY.MM"?"selected":""}>YY.MM (26.04)</option>
                        <option value="YYYY年MM月" ${v.format==="YYYY年MM月"?"selected":""}>YYYY年MM月 (2026年04月)</option>
                    </select>
                </div>`:v.type==="seller"?L=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-seller-short" ${v.short?"checked":""}> ${escapeHtml(t("archive-seller-short"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-seller-short-hint"))}</div>
                </div>`:v.type==="amount"?L=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-amount-currency" ${v.with_currency?"checked":""}> ${escapeHtml(t("archive-amount-currency"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-amount-currency-hint"))}</div>
                </div>`:v.type==="sep"?L=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-sep-val"))}</label>
                    <div class="sep-options">
                        <button type="button" class="sep-chip ${v.val==="_"?"active":""}" data-sep="_">_ (下划线)</button>
                        <button type="button" class="sep-chip ${v.val==="-"?"active":""}" data-sep="-">- (短横)</button>
                        <button type="button" class="sep-chip ${v.val===" "?"active":""}" data-sep=" ">(空格)</button>
                        <input type="text" id="token-sep-custom" class="form-input sep-custom" maxlength="3" placeholder="${escapeHtml(t("archive-sep-custom"))}" value="${["_","-"," "].includes(v.val)?"":escapeHtml(v.val||"")}">
                    </div>
                </div>`:L=`<div class="form-hint">${escapeHtml(t("archive-token-no-option"))}</div>`,b.innerHTML=L,document.getElementById("archive-token-modal").style.display="",b.querySelectorAll(".sep-chip").forEach(C=>{C.addEventListener("click",()=>{b.querySelectorAll(".sep-chip").forEach(I=>I.classList.remove("active")),C.classList.add("active");const P=document.getElementById("token-sep-custom");P&&(P.value="")})})}function q(){const y=e[a];if(y){if(y.type==="date")y.format=document.getElementById("token-date-format").value;else if(y.type==="seller")y.short=document.getElementById("token-seller-short").checked;else if(y.type==="amount")y.with_currency=document.getElementById("token-amount-currency").checked;else if(y.type==="sep"){const v=document.querySelector("#archive-token-body .sep-chip.active"),b=document.getElementById("token-sep-custom").value;y.val=b||(v?v.dataset.sep:"_")}document.getElementById("archive-token-modal").style.display="none",g(),E()}}function H(){a<0||(e.splice(a,1),document.getElementById("archive-token-modal").style.display="none",g(),E())}async function F(){if(e.length===0){showToast(t("archive-rule-cannot-empty"),"error");return}try{if(!(await fetch("/api/archive/settings",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({name_template:e,folder_strategy:n})})).ok)throw new Error("save failed");showToast(t("archive-save-ok"),"success");const v=document.getElementById("archive-rule-modal");v&&(v.style.display="none")}catch{showToast(t("archive-save-fail"),"error")}}async function A(){await showConfirm(t("archive-reset-confirm"),{danger:!0})&&(e=[{type:"date",format:"YYYY-MM-DD"},{type:"sep",val:"_"},{type:"seller",short:!0},{type:"sep",val:"_"},{type:"category"},{type:"sep",val:"_"},{type:"amount",with_currency:!0}],n="by_month_seller",g(),$(),E())}})();(function(){const o="pearnly_big_batch_tip_shown";let s=null,p=null,r=0,f=0,i=!1;function c(B){const q=typeof t=="function"?t("big-batch-unload-warn"):"Batch OCR running · close anyway?";return B.preventDefault(),B.returnValue=q,q}function l(){i||(i=!0,window.addEventListener("beforeunload",c))}function d(){i&&(i=!1,window.removeEventListener("beforeunload",c))}function u(){if(document.getElementById("big-batch-progress"))return;const B=document.getElementById("file-list");if(!B||!B.parentNode)return;const q=document.createElement("div");q.id="big-batch-progress",q.className="big-batch-progress",q.innerHTML='<div class="bbp-row"><svg class="bbp-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.5"/><path d="M8 4.5v3.5l2.5 1.5"/></svg><span class="bbp-text" id="bbp-text"></span></div><div class="bbp-track"><div class="bbp-fill" id="bbp-fill" style="width:0%"></div></div>',B.parentNode.insertBefore(q,B);const H=document.getElementById("bbp-text");H&&(H.textContent=typeof t=="function"?t("big-batch-progress-init"):"Starting...")}function g(){const B=document.getElementById("big-batch-progress");B&&B.remove()}function w(){if(!p)return;let B=0;for(let L=0;L<p.length;L++){const C=p[L].status;(C==="success"||C==="error"||C==="cancelled")&&B++}const q=r,H=q>0?Math.min(100,Math.floor(100*B/q)):0,F=(Date.now()-f)/1e3;let A;if(B>=3&&F>1){const L=F/B;A=(q-B)*L}else A=(q-B)*6/6;const y=Math.max(1,Math.ceil(A/60)),v=document.getElementById("bbp-fill"),b=document.getElementById("bbp-text");v&&(v.style.width=H+"%"),b&&(B>=q?b.textContent=t("big-batch-progress-done").replace("{total}",q):b.textContent=t("big-batch-progress-running").replace("{done}",B).replace("{total}",q).replace("{min}",y))}function $(B){try{if(localStorage.getItem(o)==="1")return}catch{}const q=Math.max(1,Math.ceil(B*6/6/60)),H=t("big-batch-first-tip").replace("{n}",B).replace("{min}",q);typeof showToast=="function"&&showToast(H,"info",8e3);try{localStorage.setItem(o,"1")}catch{}}function E(B){!B||B.length<100||(p=B,r=B.length,f=Date.now(),u(),l(),$(r),s&&clearInterval(s),s=setInterval(w,250),w())}function _(){s&&(clearInterval(s),s=null),d(),p&&r>=100?(w(),setTimeout(g,1200)):g(),p=null,r=0}window._bigBatchStart=E,window._bigBatchStop=_,typeof window.subscribeI18n=="function"&&window.subscribeI18n("big-batch-progress",function(){p&&w()})})();(function(){let e=null,n=!1,a=!1;function o(v){return typeof escapeHtml=="function"?escapeHtml(v==null?"":String(v)):String(v??"")}function s(v,b){try{typeof showToast=="function"&&showToast(v,b||"info")}catch{}}function p(){const v=typeof _userInfo<"u"?_userInfo:null;return!!(v&&(v.role==="owner"||v.is_super_admin))}function r(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function f(v){if(!v)return!1;const b=String(v.status||"").toLowerCase();return b==="exception"||b==="exception_pending"||b==="rejected"}async function i(v){if(n&&!v)return e;const b=localStorage.getItem("mrpilot_token");if(!b)return null;try{const L=await fetch("/api/erp/xero/status",{headers:{Authorization:"Bearer "+b}});if(!L.ok)throw new Error("http_"+L.status);e=await L.json(),n=!0}catch{e={configured:!1,connected:!1,organisations:[]},n=!1}return e}function c(){const v=document.getElementById("erp-connect-cards");if(!v)return;const b=e;let L,C=!1;b?b.configured?b.connected?(C=!0,L='<span class="mrerp-card-pill mrerp-pill-ok">'+o(t("xero-card-connected"))+"</span>"):L='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-connected"))+"</span>":L='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-configured"))+"</span>":L='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-connected"))+"</span>";let P="";if(!b||!b.configured)P='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+o(t("xero-connect-btn"))+"</button>";else if(!b.connected)p()&&(P='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+o(t("xero-connect-btn"))+"</button>");else{const x=!!b.auto_push,h=x?t("card-btn-disable"):t("card-btn-enable");P='<button type="button" class="'+(x?"mrerp-card-toggle mrerp-card-toggle-disable":"mrerp-card-toggle mrerp-card-toggle-enable")+'" id="btn-xero-toggle-enabled" data-xero-enabled="'+(x?"1":"0")+'" title="'+o(x?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip"))+'">'+o(h)+'</button><button type="button" class="int-btn-configure" id="btn-xero-edit-toggle">'+o(t("card-btn-edit"))+"</button>"}const I=b&&b.connected?"xero-card-desc-connected":"xero-card-desc-default",j=b&&b.connected?t("xero-card-connected")||"Connected · default org will receive pushes":"Cloud accounting · push invoices to your default Xero org",Y=(function(){const x=t(I);return x===I?j:x})();let G='<div class="integration-row erp-connect-xero'+(C?" connected":"")+'"><div class="int-icon ic-xero"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="9" cy="10" r="1.3" fill="currentColor"/><circle cx="15" cy="14" r="1.3" fill="currentColor"/><path d="M9 14l6-4"/></svg></div><div class="int-info"><div class="int-name"><span>'+o(t("xero-card-title")||"Xero")+"</span>"+L+'</div><div class="int-desc">'+o(Y)+'</div></div><div class="int-actions">'+P+"</div></div>";if(b&&b.configured&&b.connected&&p()){const x=b.organisations||[];let h="";if(x.length>0){h+='<div class="erp-cc-meta">'+o((t("xero-org-count")||"").replace("{n}",String(x.length)))+"</div>",h+='<div class="erp-cc-org-label">'+o(t("xero-default-org"))+":</div>",h+='<div class="erp-cc-orgs">',x.forEach(function(K){h+='<label class="erp-cc-org-row"><input type="radio" name="xero-default-org" value="'+o(K.id)+'"'+(K.is_default?" checked":"")+'><span class="erp-cc-org-name">'+o(K.organisation_name||K.organisation_id)+"</span></label>"}),h+="</div>";const D=!!b.auto_push,N=D?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip");h+='<div class="erp-cc-auto-push" title="'+o(N)+'"><label class="erp-cc-toggle"><input type="checkbox" id="xero-auto-push-toggle"'+(D?" checked":"")+'><span class="erp-cc-toggle-slider"></span><span class="erp-cc-toggle-label">'+o(t("erp-auto-push-label"))+"</span></label></div>",h+='<div class="erp-cc-actions"><button class="btn btn-ghost btn-tiny" type="button" id="btn-xero-disconnect">'+o(t("xero-disconnect-btn"))+"</button></div>"}G+='<div class="erp-xero-details" id="erp-xero-details" style="display:none; margin:8px 0 16px; padding:12px 14px; border:1px solid var(--line); border-radius:8px; background:var(--bg);">'+h+"</div>"}const W=v.querySelector(".erp-connect-xero"),te=v.querySelector("#erp-xero-details");te&&te.remove(),W?W.outerHTML=G:v.insertAdjacentHTML("afterbegin",G);const re=document.getElementById("btn-xero-edit-toggle");re&&re.addEventListener("click",function(x){x.preventDefault();const h=document.getElementById("erp-xero-details");h&&(h.style.display=h.style.display==="none"?"":"none")});const T=document.getElementById("btn-xero-toggle-enabled");T&&T.addEventListener("click",async function(x){if(x.preventDefault(),T.disabled)return;const D=!(T.getAttribute("data-xero-enabled")==="1");if(!D)try{if(!await window.pearnlyConfirm(t("card-toggle-disable-confirm")))return}catch{}T.disabled=!0,await g(D,null)})}async function l(){const v=localStorage.getItem("mrpilot_token");if(v)try{const b=await fetch("/api/erp/xero/auth/start",{method:"GET",headers:{Authorization:"Bearer "+v}});if(!b.ok){let C="unknown";try{C=(await b.json()).detail||"unknown"}catch{}const P=String(C).replace(/^xero\./,"").toLowerCase();s(t("xero-push-fail").replace("{err}",t("xero-err-"+P)||C),"error");return}const L=await b.json();L.redirect_url&&(window.location.href=L.redirect_url)}catch(b){s(t("xero-push-fail").replace("{err}",b.message||"network"),"error")}}async function d(){if(!await window.pearnlyConfirm(t("xero-disconnect-confirm")))return;const b=localStorage.getItem("mrpilot_token");try{const L=await fetch("/api/erp/xero/disconnect",{method:"POST",headers:{Authorization:"Bearer "+b}});if(!L.ok)throw new Error("http_"+L.status);await i(!0),c()}catch(L){s(t("xero-push-fail").replace("{err}",L.message),"error")}}async function u(v){const b=localStorage.getItem("mrpilot_token");try{const L=await fetch("/api/erp/xero/select_org",{method:"POST",headers:{Authorization:"Bearer "+b,"Content-Type":"application/json"},body:JSON.stringify({token_id:v})});if(!L.ok)throw new Error("http_"+L.status);await i(!0),c()}catch(L){s(t("xero-push-fail").replace("{err}",L.message),"error")}}async function g(v,b){const L=localStorage.getItem("mrpilot_token");b&&(b.disabled=!0);try{const C=await fetch("/api/erp/xero/auto-push",{method:"POST",headers:{Authorization:"Bearer "+L,"Content-Type":"application/json"},body:JSON.stringify({on:!!v})});if(!C.ok){let P="unknown";try{P=(await C.json()).detail||"unknown"}catch{}throw new Error(P)}s(v?t("erp-auto-push-toggled-on"):t("erp-auto-push-toggled-off"),"success"),n=!1,await i(!0),c()}catch(C){b&&(b.checked=!v),s(t("erp-auto-push-toggle-fail").replace("{err}",C.message||"network"),"error")}finally{b&&(b.disabled=!1)}}async function w(){const v=document.getElementById("drawer-history-save");if(!v||v.querySelector("#btn-xero-push")||v.querySelector("#pn-push-wrap")||(await i(!1),v.querySelector("#pn-push-wrap"))||v.querySelector("#btn-xero-push"))return;const b=r();if(!(b&&(b._historyId||b.history_id)))return;let C=!1,P="xero-push-tip";!e||!e.configured?(C=!0,P="xero-err-not_configured"):e.connected?f(b)&&(C=!0,P="xero-push-disabled-exc"):(C=!0,P="xero-push-disabled-no-conn");const I=document.createElement("button");I.type="button",I.id="btn-xero-push",I.className="btn btn-ghost"+(C?" disabled":""),I.disabled=C,I.title=t(P)||"",I.innerHTML='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5 8l2 2 4-4"/></svg><span style="margin-left:4px;">'+o(t("xero-push-btn"))+"</span>",I.addEventListener("click",$);const j=document.getElementById("btn-push-erp");j&&j.parentNode?j.parentNode.insertBefore(I,j.nextSibling):v.insertBefore(I,v.firstChild)}async function $(){const v=r(),b=v&&(v._historyId||v.history_id);if(!b)return;const L=document.getElementById("btn-xero-push");L&&(L.disabled=!0,L.classList.add("loading"));const C=localStorage.getItem("mrpilot_token");try{const P=await fetch("/api/erp/xero/push/"+encodeURIComponent(b),{method:"POST",headers:{Authorization:"Bearer "+C}});if(!P.ok){let I="unknown";try{I=(await P.json()).detail||"unknown"}catch{}const j=String(I).replace(/^xero\./,"").toLowerCase(),Y=t("xero-"+j),G=Y&&Y!=="xero-"+j?Y:I;s(t("xero-push-fail").replace("{err}",G),"error");return}s(t("xero-push-ok"),"success")}catch(P){s(t("xero-push-fail").replace("{err}",P.message||"network"),"error")}finally{L&&(L.disabled=!1,L.classList.remove("loading"))}}async function E(){await i(!0),c(),_()}async function _(){const v=document.getElementById("erp-global-push-mode");if(!v)return;const b=localStorage.getItem("mrpilot_token");if(b)try{const L=await fetch("/api/settings/erp-push-mode",{headers:{Authorization:"Bearer "+b}});if(L.ok){const C=await L.json();C.mode&&(v.value=C.mode,v.dataset.prev=C.mode)}}catch{}}async function B(v){const b=v.value,L=localStorage.getItem("mrpilot_token");try{(await fetch("/api/settings/erp-push-mode",{method:"PUT",headers:{Authorization:"Bearer "+L,"Content-Type":"application/json"},body:JSON.stringify({mode:b})})).ok?(v.dataset.prev=b,s(t("pref-erp-mode-saved"),"success")):(v.value=v.dataset.prev||"smart",s(t("pref-save-failed"),"error"))}catch{v.value=v.dataset.prev||"smart",s(t("pref-save-failed"),"error")}}function q(){try{const v=String(window.location.hash||"");if(v.indexOf("xero=ok")>=0){const b=v.match(/n=(\d+)/),L=b?b[1]:"1";s((t("xero-toast-redirected-ok")||"").replace("{n}",L),"success"),history.replaceState(null,"",window.location.pathname+"#automation"),i(!0).then(c)}else v.indexOf("xero=err")>=0&&(s(t("xero-toast-redirected-err"),"error"),history.replaceState(null,"",window.location.pathname+"#automation"))}catch{}}function H(){if(a)return;a=!0,document.addEventListener("click",function(b){if(b.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(E,50);return}if(b.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(E,80);return}if(b.target.closest("#btn-xero-connect")){b.preventDefault(),l();return}if(b.target.closest("#btn-xero-disconnect")){b.preventDefault(),d();return}}),document.addEventListener("change",function(b){b.target&&b.target.matches('input[name="xero-default-org"]')&&u(b.target.value),b.target&&b.target.id==="xero-auto-push-toggle"&&g(b.target.checked,b.target),b.target&&b.target.id==="erp-global-push-mode"&&B(b.target)});const v=function(){return document.getElementById("drawer-body")};try{const b=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("btn-xero-push")&&w()}),L=v();if(L)b.observe(L,{childList:!0,subtree:!0});else{const C=new MutationObserver(function(){const P=v();P&&(b.observe(P,{childList:!0,subtree:!0}),C.disconnect())});C.observe(document.body,{childList:!0,subtree:!0})}}catch{}setTimeout(q,500)}function F(){e&&c();const v=document.getElementById("btn-xero-push");if(v){const b=v.querySelector("span");b&&(b.textContent=t("xero-push-btn"))}}H(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("xero-adapter",F);async function A(v){const b=Date.now();for(;Date.now()-b<v;){if(typeof _userInfo<"u"&&_userInfo&&_userInfo.id)return _userInfo;await new Promise(L=>setTimeout(L,80))}return null}async function y(){await A(5e3);const v=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),b=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');v&&b&&await E()}setTimeout(y,200)})();(function(){const e={};function n(){if(document.getElementById("report-modal"))return;const c=`
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
        </div>`,l=document.createElement("div");l.innerHTML=c,document.body.appendChild(l.firstElementChild),document.getElementById("report-modal-close-x").addEventListener("click",a),document.getElementById("report-modal-cancel").addEventListener("click",a),document.getElementById("report-modal").addEventListener("click",d=>{d.target.id==="report-modal"&&a()})}function a(){const c=document.getElementById("report-modal");c&&(c.style.display="none"),o=null}let o=null;async function s(c,l){const d=c+":"+(l||"");if(e[d])return e[d];let u;try{const g=localStorage.getItem("mrpilot_token"),w=await fetch(`/api/reports/templates?lang=${encodeURIComponent(c)}`,{headers:{Authorization:"Bearer "+g}});if(!w.ok)throw new Error("templates fetch failed");u=(await w.json()).templates||[]}catch(g){console.error("fetchTemplates fail",g),u=[{code:"input_vat",name:t("tpl-input-vat"),desc:t("tpl-input-vat-desc"),recommended:!0},{code:"standard",name:t("tpl-standard"),desc:t("tpl-standard-desc"),recommended:!1},{code:"print",name:t("tpl-print"),desc:t("tpl-print-desc"),recommended:!1}]}if(u=u.filter(g=>g.code!=="erp"),l==="history-batch"){const g=u.findIndex($=>$.code==="standard"),w=g>=0?g+1:u.length;u.splice(w,0,{code:"sales_detail_th",name:t("export-tpl-sales-detail"),desc:t("export-tpl-sales-detail-desc"),recommended:!1,is_new:!0})}return e[d]=u,u}function p(c){const l=document.getElementById("report-tpl-list"),d=c.map((g,w)=>`
            <label class="report-tpl-item${g.recommended?" is-recommended":""}">
                <input type="radio" name="report-tpl" value="${g.code}" ${g.recommended||w===0?"checked":""}>
                <div class="report-tpl-content">
                    <div class="report-tpl-name">
                        ${r(g.name)}
                        ${g.recommended?`<span class="report-tpl-badge">${r(t("report-recommended"))}</span>`:""}
                    </div>
                    <div class="report-tpl-desc">${r(g.desc||"")}</div>
                </div>
            </label>
        `).join(""),u=`
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
        `;l.innerHTML=d+u}function r(c){return c==null?"":String(c).replace(/[&<>"']/g,l=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[l])}function f(c){const l=new Date,d=l.getFullYear(),u=l.getMonth()+1;if(c==="all")return"all";if(c==="this-month")return`${d}-${String(u).padStart(2,"0")}`;if(c==="last-month"){const g=new Date(d,u-2,1);return`${g.getFullYear()}-${String(g.getMonth()+1).padStart(2,"0")}`}return c==="this-year"?`${d}`:c==="this-quarter"?`${d}-Q${Math.floor((u-1)/3)+1}`:"all"}window.openReportModal=async function(c){c=c||{},n(),typeof applyLang=="function"?applyLang(currentLang):document.querySelectorAll("#report-modal [data-i18n]").forEach($=>{const E=$.getAttribute("data-i18n");I18N[currentLang]&&I18N[currentLang][E]&&($.textContent=I18N[currentLang][E])});const l=document.getElementById("report-period-section");l&&(l.style.display=c.mode==="client"?"":"none");const d=document.getElementById("report-tpl-list");d.innerHTML=`<div class="report-tpl-loading">${r(t("report-modal-loading"))}</div>`,document.getElementById("report-modal").style.display="";const u=await s(currentLang,c&&c.mode);p(u),o=c;const g=document.getElementById("report-modal-download"),w=g.cloneNode(!0);g.parentNode.replaceChild(w,g),w.addEventListener("click",()=>i(o))};async function i(c){if(!c)return;const l=document.querySelector('input[name="report-tpl"]:checked');if(!l){showToast(t("report-toast-no-selection"),"info");return}const d=l.value,u=document.querySelector('input[name="report-period"]:checked'),g=u?u.value:"all",w=f(g),$=document.getElementById("report-modal-download"),E=$.innerHTML;$.disabled=!0,$.innerHTML=`<span>${r(t("report-modal-loading"))}</span>`;try{const _=localStorage.getItem("mrpilot_token");let B,q;if(c.mode==="records")B=await fetch("/api/reports/export",{method:"POST",headers:{Authorization:"Bearer "+_,"Content-Type":"application/json"},body:JSON.stringify({template:d,lang:currentLang,records:c.records||[],meta:c.meta||{}})}),q=`mrpilot-${d}-${Date.now()}.xlsx`;else if(c.mode==="client"){const L=`/api/reports/clients/${c.clientId}/export?template=${encodeURIComponent(d)}&lang=${encodeURIComponent(currentLang)}&month=${encodeURIComponent(w)}`;B=await fetch(L,{headers:{Authorization:"Bearer "+_}}),q=`${(c.clientName||"client").replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40)}-${d}.xlsx`}else if(c.mode==="history-batch")d==="sales_detail_th"?(B=await fetch("/api/ocr/export-by-history-ids",{method:"POST",headers:{Authorization:"Bearer "+_,"Content-Type":"application/json"},body:JSON.stringify({template:"sales_detail_th",lang:currentLang,history_ids:c.historyIds||[],client_id:c.clientId||null})}),q=`Pearnly_SalesDetail_${Date.now()}.xlsx`):(B=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+_,"Content-Type":"application/json"},body:JSON.stringify({template:d,lang:currentLang,history_ids:c.historyIds||[],client_id:c.clientId||null})}),q=`mrpilot-batch-${d}-${Date.now()}.xlsx`);else throw new Error("unknown mode: "+c.mode);if(!B.ok){let L="HTTP "+B.status;try{const C=await B.json();C&&C.detail&&(L=C.detail)}catch(C){console.warn("[batch-export] resp.json err.detail parse failed:",C)}B.status===404?showToast(t("report-toast-empty"),"info"):showToast(t("report-toast-fail")+" · "+L,"error");return}const H=await B.blob();let F=q;const y=(B.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(y)try{F=decodeURIComponent(y[1])}catch{}const v=URL.createObjectURL(H),b=document.createElement("a");b.href=v,b.download=F,document.body.appendChild(b),b.click(),document.body.removeChild(b),URL.revokeObjectURL(v),showToast(t("report-toast-success"),"success"),a()}catch(_){console.error("doDownload fail",_),showToast(t("report-toast-fail")+" · "+(_.message||""),"error")}finally{$.disabled=!1,$.innerHTML=E}}document.addEventListener("DOMContentLoaded",()=>{const c=document.getElementById("btn-export");if(c){const d=c.cloneNode(!0);c.parentNode.replaceChild(d,c),d.addEventListener("click",()=>{if(typeof _results>"u"||!_results||_results.length===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"records",records:_results.map(u=>({filename:u.filename,merged_fields:u.merged_fields||{}}))})})}const l=document.getElementById("history-batch-export");l&&l.addEventListener("click",()=>{if(typeof _historySelected>"u"||_historySelected.size===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"history-batch",historyIds:Array.from(_historySelected)})})}),window.openClientExportModal=function(c,l){openReportModal({mode:"client",clientId:c,clientName:l||""})}})();(function(){const n=typeof window<"u"&&"showDirectoryPicker"in window,a=/\.(pdf|jpe?g|png|webp)$/i,o="mrpilot_folder_watcher",s=1;let p=null,r=null,f=null,i=60,c=!1,l=!1,d=0,u=0,g=0,w=[],$=null,E=!1;function _(){return p||(p=new Promise((k,S)=>{const M=indexedDB.open(o,s);M.onupgradeneeded=U=>{const z=U.target.result;z.objectStoreNames.contains("handles")||z.createObjectStore("handles"),z.objectStoreNames.contains("seen")||z.createObjectStore("seen"),z.objectStoreNames.contains("config")||z.createObjectStore("config")},M.onsuccess=U=>k(U.target.result),M.onerror=U=>S(U.target.error)}),p)}function B(k,S){return _().then(M=>new Promise((U,z)=>{const R=M.transaction(k,"readonly").objectStore(k).get(S);R.onsuccess=()=>U(R.result),R.onerror=()=>z(R.error)}))}function q(k,S,M){return _().then(U=>new Promise((z,m)=>{const R=U.transaction(k,"readwrite");R.objectStore(k).put(M,S),R.oncomplete=()=>z(),R.onerror=()=>m(R.error)}))}function H(k,S){return _().then(M=>new Promise((U,z)=>{const m=M.transaction(k,"readwrite");m.objectStore(k).delete(S),m.oncomplete=()=>U(),m.onerror=()=>z(m.error)}))}function F(k){return _().then(S=>new Promise((M,U)=>{const z=S.transaction(k,"readwrite");z.objectStore(k).clear(),z.oncomplete=()=>M(),z.onerror=()=>U(z.error)}))}async function A(k){if(!k)return!1;try{const S={mode:"read"};let M=await k.queryPermission(S);return M==="granted"?!0:(M=await k.requestPermission(S),M==="granted")}catch(S){return console.warn("[folder] permission check failed:",S),!1}}function y(k,S){const M=document.getElementById("folder-status-summary");M&&(M.setAttribute("data-i18n",k),M.textContent=t(k),M.className="auto-status-pill"+(S?" "+S:""))}function v(k){["folder-unsupported","folder-empty","folder-active"].forEach(S=>{const M=document.getElementById(S);M&&(M.style.display=S===k?"":"none")})}function b(k){if(!k)return"-";const S=k instanceof Date?k:new Date(k),M=String(S.getHours()).padStart(2,"0"),U=String(S.getMinutes()).padStart(2,"0"),z=String(S.getSeconds()).padStart(2,"0");return`${M}:${U}:${z}`}function L(){v("folder-active");const k=document.getElementById("folder-config-path");k&&r&&(k.textContent=r.name||"-");const S=document.getElementById("folder-interval-select");S&&(S.value=String(i)),document.getElementById("folder-stat-last").textContent=$?b($):"-",document.getElementById("folder-stat-processed").textContent=String(d),document.getElementById("folder-stat-failed").textContent=String(u),document.getElementById("folder-stat-queue").textContent=String(g);const M=document.getElementById("btn-folder-pause"),U=document.getElementById("btn-folder-resume");M&&(M.style.display=c?"none":""),U&&(U.style.display=c?"":"none"),c?y("folder-status-paused","paused"):y("folder-status-running","running");const z=document.getElementById("folder-status-text");z&&(z.setAttribute("data-i18n",c?"folder-status-paused":"folder-status-running"),z.textContent=t(c?"folder-status-paused":"folder-status-running"));const m=document.getElementById("folder-status-pulse");m&&(m.className="folder-status-pulse"+(c?" paused":"")),C()}function C(){const k=document.getElementById("folder-recent-list");if(k){if(w.length===0){k.innerHTML=`<div class="folder-recent-empty">${escapeHtml(t("folder-recent-empty"))}</div>`;return}k.innerHTML=w.slice(0,20).map(S=>{let M;S.status==="ok"?M=`<span class="folder-recent-icon ok">${svgIcon("check",12)}</span>`:S.status==="dup"?M=`<span class="folder-recent-icon dup" title="${escapeHtml(t("folder-recent-dup"))}">${svgIcon("copy",12)}</span>`:S.status==="skip"?M=`<span class="folder-recent-icon skip" title="${escapeHtml(t("folder-recent-skip"))}">${svgIcon("minus",12)}</span>`:M=`<span class="folder-recent-icon fail">${svgIcon("alert",12)}</span>`;const U=S.status==="fail"&&S.error?S.error:S.status==="dup"&&S.reason||S.status==="skip"&&S.reason?S.reason:"",z=U?`<div class="folder-recent-err">${escapeHtml(U)}</div>`:"";return`
                <div class="folder-recent-item">
                    ${M}
                    <div class="folder-recent-body">
                        <div class="folder-recent-name">${escapeHtml(S.name)}</div>
                        ${z}
                    </div>
                    <div class="folder-recent-time">${b(S.time)}</div>
                </div>
            `}).join("")}}function P(k){w.unshift(k),w.length>50&&(w.length=50),q("config","recent_list",w).catch(()=>{})}async function I(k){const S=new FormData;S.append("file",k,k.name),S.append("source","folder");const M=await fetch("/api/ocr/recognize?source=folder",{method:"POST",headers:{Authorization:"Bearer "+token,"X-Source":"folder"},body:S});if(!M.ok){let U="http_"+M.status;try{const z=await M.json();U=z&&z.detail?typeof z.detail=="string"?z.detail:z.detail.code||JSON.stringify(z.detail):U}catch{}throw new Error(U)}return await M.json()}async function j(k){try{const M=(await k.getFile()).size;return await new Promise(z=>setTimeout(z,3e3)),(await k.getFile()).size===M&&M>0}catch{return!1}}async function Y(k,S,M,U){if(U>10)return;let z;try{z=await k.queryPermission({mode:"read"})}catch{z="denied"}if(z==="granted")for await(const m of k.values()){const R=S?`${S}/${m.name}`:m.name;if(m.kind==="file"){if(!a.test(m.name))continue;let O;try{O=await m.getFile()}catch{continue}const J=`${R}::${O.size}::${O.lastModified}`;if(await B("seen",J))continue;M.push({entry:m,file:O,seenKey:J,relPath:R})}else if(m.kind==="directory")try{await Y(m,R,M,U+1)}catch{}}}async function G(){if(!(l||c||!r)){l=!0;try{if(await r.queryPermission({mode:"read"})!=="granted"){console.warn("[folder] permission lost · stop"),K(),showToast("warn",t("folder-permission-lost"));return}$=new Date;const S=[];await Y(r,"",S,0),g=S.length,L();for(const M of S){if(c)break;if(!await j(M.entry)){g=Math.max(0,g-1),L();continue}try{let z;try{z=await M.entry.getFile()}catch{z=M.file}const m=await I(z);await q("seen",M.seenKey,{name:z.name,relPath:M.relPath,size:z.size,lastModified:z.lastModified,processed_at:Date.now()});const R=m.history_ids||(m.history_id?[m.history_id]:[]),O=m.duplicate_warnings||[],J=M.relPath||z.name;R.length>0?(d+=R.length,P({name:J,status:"ok",time:new Date,history_id:R[0],count:R.length}),await q("config","processed_count",d)):O.length>0?P({name:J,status:"dup",time:new Date,reason:t("folder-recent-dup-reason")}):P({name:J,status:"skip",time:new Date,reason:t("folder-recent-skip-reason")})}catch(z){u++,P({name:M.relPath||M.file.name,status:"fail",time:new Date,error:String(z.message||z)}),await q("config","failed_count",u)}g=Math.max(0,g-1),L()}}catch(k){console.warn("[folder] scan error:",k)}finally{l=!1,L()}}}function W(){f&&clearInterval(f),f=setInterval(G,i*1e3)}function te(){f&&(clearInterval(f),f=null)}function re(k){if(!r||c)return;const S=typeof t=="function"?t("folder-unload-warn"):"Folder watcher running · close anyway?";return k.preventDefault(),k.returnValue=S,S}function T(){window._pearnlyFolderUnloadAttached||(window._pearnlyFolderUnloadAttached=!0,window.addEventListener("beforeunload",re))}function x(){window._pearnlyFolderUnloadAttached&&(window._pearnlyFolderUnloadAttached=!1,window.removeEventListener("beforeunload",re))}function h(){c=!1,W(),T(),L(),G()}function D(){c=!0,te(),x(),L()}function N(){c=!1,W(),T(),L(),G()}function K(){c=!0,te(),x()}async function Q(){try{const k=await window.showDirectoryPicker({mode:"read",startIn:"documents"});if(!await A(k)){showToast("warn",t("folder-permission-denied"));return}r=k,await q("handles","main",k),d=0,u=0,g=0,w=[],await q("config","processed_count",0),await q("config","failed_count",0),await F("seen"),h()}catch(k){k&&k.name!=="AbortError"&&console.warn("[folder] pick failed:",k)}}async function le(){await showConfirm(t("folder-confirm-remove"),{danger:!0})&&(K(),r=null,d=0,u=0,g=0,w=[],await H("handles","main"),await H("config","processed_count"),await H("config","failed_count"),await F("seen"),v("folder-empty"),y("folder-status-empty",""))}async function ie(){w=[];try{await H("config","recent_list")}catch{}C()}async function V(){if(E)return;if(E=!0,!n){v("folder-unsupported"),y("folder-status-unsupported",""),ne();return}Z();let k=null;try{k=await B("handles","main")}catch{}if(!k){v("folder-empty"),y("folder-status-empty","");return}if(!await A(k)){v("folder-empty"),y("folder-status-empty",""),await H("handles","main"),showToast("warn",t("folder-permission-lost-restart"));return}r=k;try{d=await B("config","processed_count")||0}catch{}try{u=await B("config","failed_count")||0}catch{}try{const M=await B("config","recent_list");Array.isArray(M)&&(w=M.map(U=>({...U,time:U.time?new Date(U.time):new Date})))}catch{}h()}function Z(){const k=document.getElementById("btn-folder-pick"),S=document.getElementById("btn-folder-pause"),M=document.getElementById("btn-folder-resume"),U=document.getElementById("btn-folder-scan-now"),z=document.getElementById("btn-folder-remove"),m=document.getElementById("btn-folder-clear-recent"),R=document.getElementById("folder-interval-select");k&&k.addEventListener("click",Q),S&&S.addEventListener("click",D),M&&M.addEventListener("click",N),U&&U.addEventListener("click",()=>{G()}),z&&z.addEventListener("click",le),m&&m.addEventListener("click",ie),R&&R.addEventListener("change",O=>{i=parseInt(O.target.value,10)||60,c||W()}),ee()}function ee(){document.querySelectorAll('[data-auto-panel="folder"] [data-tab-jump]').forEach(k=>{k.dataset.tabJumpBound||(k.dataset.tabJumpBound="1",k.addEventListener("click",S=>{const M=S.currentTarget.dataset.tabJump;if(M==="email")typeof switchAutomationTab=="function"&&switchAutomationTab("email");else if(M==="upload"){const U=document.querySelector('[data-page="recognize"]')||document.querySelector('[data-page="upload"]');U&&U.click()}}))})}function ne(){ee()}window._loadFolderWatcherPanel=V;function oe(){try{if(navigator.userAgentData&&Array.isArray(navigator.userAgentData.brands))return navigator.userAgentData.brands.some(S=>/chromium|google chrome|microsoft edge/i.test(S.brand||""))}catch{}const k=navigator.userAgent||"";return!!(/Edg\//.test(k)||/Chrome\//.test(k)&&!/OPR\/|YaBrowser|Opera/.test(k))}function ue(){try{if(oe()||localStorage.getItem("pearnly_chrome_banner_dismissed")==="1")return;const k=document.getElementById("chrome-only-banner");if(!k)return;const S=k.querySelector('[data-i18n="chrome-banner-msg"]'),M=k.querySelector('[data-i18n="chrome-banner-dismiss"]');S&&typeof t=="function"&&(S.textContent=t("chrome-banner-msg")),M&&typeof t=="function"&&(M.textContent=t("chrome-banner-dismiss")),k.style.display="";const U=document.getElementById("chrome-only-banner-close");U&&!U.dataset.bound&&(U.dataset.bound="1",U.addEventListener("click",()=>{k.style.display="none";try{localStorage.setItem("pearnly_chrome_banner_dismissed","1")}catch{}}))}catch{}}typeof document<"u"&&(document.readyState==="loading"?document.addEventListener("DOMContentLoaded",ue):setTimeout(ue,0)),window._refreshChromeBanner=ue})();(function(){let e=null,n=null,a="new",o=!1,s=!1;async function p(){const I=document.getElementById("email-empty"),j=document.getElementById("email-account-card");if(document.getElementById("email-logs-section"),!(!I||!j))try{const Y=await fetch("/api/email-ingest/account",{headers:{Authorization:"Bearer "+token}});if(Y.status===401){localStorage.removeItem("mrpilot_token");const W=await Y.json().catch(()=>({}));if((typeof W.detail=="string"?W.detail:W.detail&&W.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}if(!Y.ok){f("none");return}const G=await Y.json();e=G.account||null,n=G.presets||{},o=!0,r(),e&&b()}catch(Y){console.error("[email-ingest] load failed",Y),f("none")}}function r(){const I=document.getElementById("email-empty"),j=document.getElementById("email-account-card"),Y=document.getElementById("email-logs-section");if(!e){I.style.display="",j.style.display="none",Y&&(Y.style.display="none"),f("none");return}I.style.display="none",j.style.display="",Y&&(Y.style.display="");const G=document.getElementById("email-account-addr"),W=document.getElementById("email-account-host"),te=document.getElementById("email-account-last"),re=document.getElementById("email-last-error"),T=document.getElementById("email-enabled-toggle");if(G&&(G.textContent=e.email_address||"-"),W&&(W.textContent=`${e.imap_host||"-"}:${e.imap_port||993}`),te){const x=e.last_fetched_at;if(!x)te.textContent=t("email-last-never");else{const h=i(x),D=!e.last_error;te.textContent=D?t("email-last-ok",{time:h}):t("email-last-fail",{time:h})}}re&&(e.last_error?(re.style.display="",re.textContent=c(e.last_error)):re.style.display="none"),T&&(T.checked=!!e.enabled),e.enabled?e.last_error?f("error"):f("on"):f("off")}function f(I){const j=document.getElementById("email-status-summary");if(!j)return;j.classList.remove("none","ready","active","coming");let Y="auto-status-loading";I==="none"?(Y="email-status-none",j.classList.add("none")):I==="on"?(Y="email-status-on",j.classList.add("active")):I==="off"?(Y="email-status-off",j.classList.add("coming")):I==="error"&&(Y="email-status-error",j.classList.add("none")),j.setAttribute("data-i18n",Y),j.textContent=t(Y)}function i(I){if(!I)return"";const j=new Date(I);if(isNaN(j.getTime()))return"";const Y=G=>String(G).padStart(2,"0");return`${Y(j.getMonth()+1)}-${Y(j.getDate())} ${Y(j.getHours())}:${Y(j.getMinutes())}`}function c(I){if(!I)return"";const j=String(I);return/auth|AUTHENTICATIONFAILED|invalid credentials/i.test(j)?t("email-test-auth-fail"):/timeout|timed out/i.test(j)?t("email.timeout"):(/ENOTFOUND|getaddrinfo/i.test(j),j)}function l(I){a=I;const j=document.getElementById("email-modal");if(!j)return;const Y=document.getElementById("email-preset");Y.innerHTML="";const G=n||{},W=["gmail","outlook","yahoo","icloud","qq","163","custom"],te={gmail:"Gmail",outlook:"Outlook / Office365",yahoo:"Yahoo Mail",icloud:"iCloud",qq:"QQ 邮箱",163:"网易 163"};W.forEach(Z=>{if(!G[Z])return;const ee=document.createElement("option");ee.value=Z,ee.textContent=Z==="custom"?t("email-preset-custom"):te[Z]||Z,Y.appendChild(ee)});const re=document.getElementById("email-modal-title"),T=document.getElementById("email-address"),x=document.getElementById("email-password"),h=document.getElementById("email-imap-host"),D=document.getElementById("email-imap-port"),N=document.getElementById("email-imap-ssl"),K=document.getElementById("email-folder"),Q=document.getElementById("email-mark-read"),le=document.getElementById("email-bind-enabled"),ie=document.getElementById("email-test-result"),V=document.getElementById("email-adv-details");if(ie&&(ie.style.display="none",ie.textContent=""),I==="edit"&&e){re.setAttribute("data-i18n","email-modal-title-edit"),re.textContent=t("email-modal-title-edit"),T.value=e.email_address||"",x.value="",x.setAttribute("data-i18n-placeholder","email-field-password-edit-ph"),x.placeholder=t("email-field-password-edit-ph"),h.value=e.imap_host||"",D.value=e.imap_port||993,N.checked=e.imap_use_ssl!==!1,K.value=e.folder||"INBOX",Q.checked=e.mark_as_read!==!1,le.checked=e.enabled!==!1;const Z=document.getElementById("email-filter-sender"),ee=document.getElementById("email-filter-subject");Z&&(Z.value=e.filter_sender||""),ee&&(ee.value=e.filter_subject||""),B(e.interval_min||15),Y.value=$(e.imap_host)||"custom",V&&(V.open=!0)}else{re.setAttribute("data-i18n","email-modal-title-new"),re.textContent=t("email-modal-title-new"),T.value="",x.value="",x.setAttribute("data-i18n-placeholder","email-field-password-ph"),x.placeholder=t("email-field-password-ph"),Y.value="gmail",u("gmail"),K.value="INBOX",Q.checked=!0,le.checked=!0;const Z=document.getElementById("email-filter-sender"),ee=document.getElementById("email-filter-subject");Z&&(Z.value=""),ee&&(ee.value=""),B(15),V&&(V.open=!1)}_(),j.style.display="flex",setTimeout(()=>T.focus(),60)}function d(){const I=document.getElementById("email-modal");I&&(I.style.display="none")}function u(I){const j=(n||{})[I];if(!j||I==="custom")return;const Y=document.getElementById("email-imap-host"),G=document.getElementById("email-imap-port"),W=document.getElementById("email-imap-ssl");Y&&(Y.value=j.host||""),G&&(G.value=j.port||993),W&&(W.checked=j.ssl!==!1)}const g={"gmail.com":"gmail","googlemail.com":"gmail","outlook.com":"outlook","hotmail.com":"outlook","live.com":"outlook","office365.com":"outlook","msn.com":"outlook","yahoo.com":"yahoo","yahoo.co.jp":"yahoo","icloud.com":"icloud","me.com":"icloud","mac.com":"icloud","qq.com":"qq","foxmail.com":"qq","163.com":"163","126.com":"163","yeah.net":"163"};function w(I){if(!I||!I.includes("@"))return;const j=I.split("@")[1].toLowerCase().trim(),Y=g[j];if(!Y)return;const G=document.getElementById("email-preset");if(!G)return;const W=G.value;W&&W!=="custom"&&W!==""&&W===Y||(G.value=Y,u(Y))}function $(I){if(!I)return null;const j=n||{};for(const Y in j)if(Y!=="custom"&&j[Y]&&j[Y].host===I)return Y;return null}function E(){const I=document.querySelector("#email-interval-options .email-interval-btn.active"),j=I?parseInt(I.dataset.interval,10):15;return{email_address:(document.getElementById("email-address").value||"").trim(),password:document.getElementById("email-password").value||"",imap_host:(document.getElementById("email-imap-host").value||"").trim(),imap_port:parseInt(document.getElementById("email-imap-port").value||"993",10)||993,imap_use_ssl:document.getElementById("email-imap-ssl").checked,folder:(document.getElementById("email-folder").value||"INBOX").trim()||"INBOX",mark_as_read:document.getElementById("email-mark-read").checked,enabled:document.getElementById("email-bind-enabled").checked,interval_min:[5,15,60].includes(j)?j:15,filter_sender:(document.getElementById("email-filter-sender").value||"").trim()||null,filter_subject:(document.getElementById("email-filter-subject").value||"").trim()||null}}function _(){const I=document.getElementById("email-interval-options");!I||I._bound||(I._bound=!0,I.addEventListener("click",j=>{const Y=j.target.closest(".email-interval-btn");Y&&(I.querySelectorAll(".email-interval-btn").forEach(G=>G.classList.remove("active")),Y.classList.add("active"))}))}function B(I){const j=[5,15,60].includes(I)?I:15,Y=document.getElementById("email-interval-options");Y&&Y.querySelectorAll(".email-interval-btn").forEach(G=>{G.classList.toggle("active",parseInt(G.dataset.interval,10)===j)})}function q(I,j){const Y=document.getElementById("email-test-result");Y&&(Y.style.display="",Y.textContent=j,Y.className="form-test-result "+(I==="ok"?"ok":I==="running"?"running":"fail"))}async function H(){const I=E();if(!I.email_address){q("fail",t("email-addr-required"));return}if(!I.password){q("fail",t("email-password-required"));return}if(!I.imap_host){q("fail",t("email-host-required"));return}const j=document.getElementById("btn-email-modal-test");j&&(j.disabled=!0),q("running",t("email-test-running"));try{const Y=await fetch("/api/email-ingest/test",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:I.email_address,password:I.password,imap_host:I.imap_host,imap_port:I.imap_port,imap_use_ssl:I.imap_use_ssl,folder:I.folder})}),G=await Y.json().catch(()=>({}));if(Y.ok&&G.success)q("ok",t("email-test-ok",{folder:I.folder,n:G.folder_count??"?"}));else{const W=G.error_msg||"";W==="auth_failed"||/auth/i.test(W)?q("fail",t("email-test-auth-fail")):q("fail",t("email-test-fail",{msg:W||Y.status}))}}catch(Y){q("fail",t("email-test-fail",{msg:String(Y).slice(0,120)}))}finally{j&&(j.disabled=!1)}}async function F(){const I=E();if(!I.email_address){q("fail",t("email-addr-required"));return}if(a==="new"&&!I.password){q("fail",t("email-password-required"));return}if(!I.imap_host){q("fail",t("email-host-required"));return}const j=document.getElementById("btn-email-modal-save");j&&(j.disabled=!0);const Y={...I};a==="edit"&&!Y.password&&delete Y.password;try{const G=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(Y)}),W=await G.json().catch(()=>({}));if(G.ok&&W.ok)e=W.account,showToast(t("email-save-ok"),"success"),d(),r(),b();else{const re="email."+(W.detail||"").split(".").slice(-1)[0];q("fail",t(re)!==re?t(re):t("email-save-fail"))}}catch{q("fail",t("email-save-fail"))}finally{j&&(j.disabled=!1)}}async function A(){if(!(!e||!await showConfirm(t("email-unbind-confirm",{email:e.email_address}),{danger:!0,okText:t("email-btn-unbind")})))try{if((await fetch("/api/email-ingest/account",{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){e=null,showToast(t("email-unbind-ok"),"success"),r();const Y=document.getElementById("email-logs-list");Y&&(Y.innerHTML="")}else showToast(t("email-unbind-fail"),"error")}catch{showToast(t("email-unbind-fail"),"error")}}async function y(){if(!e||s)return;if(!e.enabled){showToast(t("email.disabled"),"error");return}s=!0;const I=document.getElementById("btn-email-trigger"),j=I?I.innerHTML:"";I&&(I.disabled=!0,I.innerHTML=`<span>${escapeHtml(t("email-trigger-running"))}</span>`);try{const Y=await fetch("/api/email-ingest/trigger",{method:"POST",headers:{Authorization:"Bearer "+token}}),G=await Y.json().catch(()=>({}));if(Y.ok){const W=G.emails_scanned||0,te=G.ocr_succeeded||0,re=G.ocr_failed||0;W===0&&te===0&&re===0?showToast(t("email-trigger-empty"),"success"):showToast(t("email-trigger-result",{scanned:W,ok:te,fail:re}),re>0?"warn":"success")}else{const te="email."+(G.detail||"").split(".").slice(-1)[0];showToast(t(te)!==te?t(te):t("email-trigger-fail"),"error")}await p()}catch{showToast(t("email-trigger-fail"),"error")}finally{s=!1,I&&(I.disabled=!1,I.innerHTML=j)}}async function v(){if(!e)return;const I=document.getElementById("email-enabled-toggle"),j=!!(I&&I.checked),Y=e.enabled;try{const G=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:e.email_address,imap_host:e.imap_host,imap_port:e.imap_port,imap_use_ssl:e.imap_use_ssl,folder:e.folder||"INBOX",filter_subject:e.filter_subject||null,filter_sender:e.filter_sender||null,mark_as_read:e.mark_as_read!==!1,enabled:j})}),W=await G.json().catch(()=>({}));G.ok&&W.ok?(e=W.account,r()):(I&&(I.checked=Y),showToast(t("email-toggle-fail"),"error"))}catch{I&&(I.checked=Y),showToast(t("email-toggle-fail"),"error")}}async function b(){const I=document.getElementById("email-logs-list");if(I){I.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`;try{const j=await fetch("/api/email-ingest/logs?limit=20",{headers:{Authorization:"Bearer "+token}});if(!j.ok){I.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const Y=await j.json();if(!Array.isArray(Y)||Y.length===0){I.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("email-logs-empty"))}</div>`;return}I.innerHTML=Y.map(L).join("")}catch{I.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}function L(I){const j=i(I.created_at),Y=I.status||"failed",G=Y==="success"?"ok":Y==="partial"?"partial":"fail",W=Y==="success"?"✓":Y==="partial"?"◐":"✗",te=I.trigger==="manual"?`<span class="log-tag manual">${escapeHtml(t("email-log-tag-manual"))}</span>`:`<span class="log-tag auto">${escapeHtml(t("email-log-tag-auto"))}</span>`,re=t("email-log-counts",{scanned:I.emails_scanned||0,att:I.attachments_found||0,ok:I.ocr_succeeded||0,fail:I.ocr_failed||0}),T=(I.elapsed_ms||0)+"ms";return`
            <div class="email-log-row ${G}">
                <span class="log-time">${escapeHtml(j)}</span>
                <span class="log-status">${W}</span>
                ${te}
                <span class="log-counts">${escapeHtml(re)}</span>
                <span class="log-elapsed">${escapeHtml(T)}</span>
            </div>
        `}function C(){const I=document.getElementById("btn-email-bind");I&&I.addEventListener("click",()=>l("new"));const j=document.getElementById("btn-email-edit");j&&j.addEventListener("click",()=>l("edit"));const Y=document.getElementById("btn-email-unbind");Y&&Y.addEventListener("click",A);const G=document.getElementById("btn-email-trigger");G&&G.addEventListener("click",y);const W=document.getElementById("email-enabled-toggle");W&&W.addEventListener("change",v);const te=document.getElementById("email-modal-close");te&&te.addEventListener("click",d);const re=document.getElementById("btn-email-modal-cancel");re&&re.addEventListener("click",d);const T=document.getElementById("btn-email-modal-test");T&&T.addEventListener("click",H);const x=document.getElementById("btn-email-modal-save");x&&x.addEventListener("click",F);const h=document.getElementById("email-preset");h&&h.addEventListener("change",K=>u(K.target.value));const D=document.getElementById("email-address");D&&!D.dataset.autoBound&&(D.dataset.autoBound="1",D.addEventListener("blur",K=>w((K.target.value||"").trim())),D.addEventListener("input",K=>{const Q=(K.target.value||"").trim();Q.includes("@")&&Q.split("@")[1].includes(".")&&w(Q)}));const N=document.getElementById("btn-email-refresh-logs");N&&N.addEventListener("click",()=>{N.classList.add("spinning"),setTimeout(()=>N.classList.remove("spinning"),600),b()})}C(),window._loadEmailIngestPanel=p,window._rerenderEmailIngest=function(){if(!o)return;r();const I=document.getElementById("email-logs-section");e&&I&&I.open&&b()};let P=null;window._startEmailLogAutoRefresh=function(){P||(P=setInterval(()=>{e&&o&&b()},3e4))},window._stopEmailLogAutoRefresh=function(){P&&(clearInterval(P),P=null)}})();(function(){let e=[],n=null,a=[],o="all",s=null,p=!1;async function r(){if(p){C();return}p=!0,f(),await i(),C()}function f(){const m=document.getElementById("bank-file-input");m&&!m._bound&&(m._bound=!0,m.addEventListener("change",w));const R=document.getElementById("btn-bank-queue-clear-done");R&&!R._bound&&(R._bound=!0,R.addEventListener("click",H));const O=document.getElementById("btn-bank-back");O&&!O._bound&&(O._bound=!0,O.addEventListener("click",()=>{n=null,a=[],te()}));const J=document.getElementById("btn-bank-delete");J&&!J._bound&&(J._bound=!0,J.addEventListener("click",v));const X=document.getElementById("btn-bank-run-match");X&&!X._bound&&(X._bound=!0,X.addEventListener("click",y)),document.querySelectorAll(".bank-filter-btn").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",()=>{o=fe.dataset.bankFilter||"all",document.querySelectorAll(".bank-filter-btn").forEach(me=>{me.classList.toggle("active",me===fe)}),Q()}))}),document.querySelectorAll("[data-bank-cand-close]").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",ne))});const de=document.getElementById("btn-bank-cand-pane-close");de&&!de._bound&&(de._bound=!0,de.addEventListener("click",ne));const se=document.getElementById("btn-bank-cand-ignore");se&&!se._bound&&(se._bound=!0,se.addEventListener("click",b));const ce=document.getElementById("btn-bank-cand-ignore-pane");ce&&!ce._bound&&(ce._bound=!0,ce.addEventListener("click",b));const ae=document.getElementById("bank-client-badge");ae&&!ae._bound&&(ae._bound=!0,ae.addEventListener("click",x)),document.querySelectorAll("[data-bank-client-picker-close]").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",h))});const pe=document.getElementById("btn-bank-client-picker-save");pe&&!pe._bound&&(pe._bound=!0,pe.addEventListener("click",N)),document.querySelectorAll(".bank-sessions-chip").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",()=>{P=fe.dataset.sessFilter||"all",document.querySelectorAll(".bank-sessions-chip").forEach(me=>{me.classList.toggle("active",me===fe)}),I()}))})}async function i(){try{const m=await fetch("/api/bank-recon/sessions?limit=30",{headers:{Authorization:"Bearer "+token}});if(!m.ok)throw new Error("sessions:"+m.status);e=await m.json(),I()}catch(m){console.warn("[bank-recon] loadSessions failed",m),e=[],I()}}async function c(m){try{const R="/api/bank-recon/sessions/"+encodeURIComponent(m)+(o!=="all"?"?filter="+o:""),O=await fetch(R,{headers:{Authorization:"Bearer "+token}});if(!O.ok)throw new Error("detail:"+O.status);const J=await O.json();n=J.session,a=J.transactions||[],W()}catch(R){console.warn("[bank-recon] loadSessionDetail failed",R),showToast(t("bank-load-failed"),"error")}}let l=[],d=0;const u=3;function g(){return d+=1,"q"+d+"_"+Date.now()}async function w(m){const R=Array.from(m.target.files||[]);if(m.target.value="",R.length!==0){for(const O of R){const J={id:g(),file:O,name:O.name,size:O.size,status:"pending",progress:0,error_code:null,tx_count:0,session_id:null};O.name.toLowerCase().endsWith(".pdf")?O.size>20*1024*1024&&(J.status="failed",J.error_code="bank_recon.file_too_large"):(J.status="failed",J.error_code="bank_recon.only_pdf"),l.push(J)}$(),E(),F()}}function $(){const m=document.getElementById("bank-upload-queue");m&&(m.style.display=""),oe(),ue()}function E(){const m=document.getElementById("bank-upload-queue-list"),R=document.getElementById("bank-upload-queue-summary");if(!m)return;if(l.length===0){m.innerHTML="",R&&(R.textContent="");const se=document.getElementById("bank-upload-queue");se&&(se.style.display="none");return}let O=0,J=0,X=0,de=0;for(const se of l)se.status==="ok"?O++:se.status==="failed"?J++:se.status==="uploading"||se.status==="parsing"?X++:de++;R&&(R.textContent=t("bank-queue-summary").replace("{ok}",O).replace("{run}",X).replace("{wait}",de).replace("{fail}",J)),m.innerHTML=l.map(_).join(""),m.querySelectorAll("[data-q-act]").forEach(se=>{const ce=se.dataset.qAct,ae=se.dataset.qId;se.addEventListener("click",()=>{ce==="retry"&&B(ae),ce==="remove"&&q(ae)})})}function _(m){const R=(m.size/1024).toFixed(0)+" KB";let O="",J="";if(m.status==="pending")O='<span class="bq-stat bq-wait">'+t("bank-queue-status-wait")+"</span>",J='<button data-q-act="remove" data-q-id="'+z(m.id)+'" class="bq-act">×</button>';else if(m.status==="uploading")O='<span class="bq-stat bq-run">'+t("bank-queue-status-uploading")+'</span><div class="bq-bar"><div class="bq-bar-fill" style="width:'+(m.progress||0)+'%"></div></div>';else if(m.status==="parsing")O='<span class="bq-stat bq-run">'+t("bank-queue-status-parsing")+'</span><div class="bq-bar"><div class="bq-bar-fill bq-bar-indet"></div></div>';else if(m.status==="ok")O='<span class="bq-stat bq-ok">'+t("bank-queue-status-ok").replace("{n}",m.tx_count||0)+"</span>",J='<button data-q-act="remove" data-q-id="'+z(m.id)+'" class="bq-act">×</button>';else if(m.status==="failed"){const X=k(m.error_code||"unknown");O='<span class="bq-stat bq-fail" title="'+z(X)+'">'+z(X)+"</span>",J='<button data-q-act="retry" data-q-id="'+z(m.id)+'" class="bq-act bq-act-retry">'+t("bank-queue-retry")+'</button><button data-q-act="remove" data-q-id="'+z(m.id)+'" class="bq-act">×</button>'}return'<div class="bq-row" data-q-row="'+z(m.id)+'"><div class="bq-name" title="'+z(m.name)+'">'+z(m.name)+'</div><div class="bq-size">'+R+'</div><div class="bq-status">'+O+'</div><div class="bq-actions">'+J+"</div></div>"}function B(m){const R=l.find(O=>O.id===m);R&&(R.status="pending",R.error_code=null,R.progress=0,E(),F())}function q(m){const R=l.findIndex(J=>J.id===m);if(R<0)return;const O=l[R];O.status==="uploading"||O.status==="parsing"||(l.splice(R,1),E())}function H(){l=l.filter(m=>m.status!=="ok"),E()}async function F(){for(;;){if(l.filter(O=>O.status==="uploading"||O.status==="parsing").length>=u)return;const R=l.find(O=>O.status==="pending");if(!R){l.every(O=>O.status==="ok"||O.status==="failed")&&(await i(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage());return}A(R).then(()=>F())}}async function A(m){m.status="uploading",m.progress=0,E();try{const R=new FormData;R.append("file",m.file,m.name);const O=await new Promise((X,de)=>{const se=new XMLHttpRequest;se.open("POST","/api/bank-recon/upload"),se.setRequestHeader("Authorization","Bearer "+token),se.upload.onprogress=ce=>{ce.lengthComputable&&(m.progress=Math.min(99,Math.round(ce.loaded/ce.total*100)),E())},se.upload.onload=()=>{m.status="parsing",E()},se.onload=()=>{se.status>=200&&se.status<300?X({status:se.status,text:se.responseText}):X({status:se.status,text:se.responseText})},se.onerror=()=>de(new Error("network")),se.send(R)});let J={};try{J=JSON.parse(O.text||"{}")}catch{J={}}if(O.status>=400){m.status="failed",m.error_code=J&&J.detail||"unknown",E();return}if(J.parse_status==="parse_failed"){m.status="failed",m.error_code=J.error==="scanned_pdf_not_yet"?"bank_recon.scanned":"bank_recon.no_tx",E();return}m.status="ok",m.tx_count=J.tx_count||0,m.session_id=J.session_id||null,E()}catch(R){console.warn("[bank-recon] upload failed",R),m.status="failed",m.error_code="network",E()}}async function y(){if(!n)return;const m=document.getElementById("btn-bank-run-match"),R=m.innerHTML;m.disabled=!0,m.innerHTML="<span>"+t("bank-matching")+"</span>";try{const O=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id)+"/match",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!O.ok)throw new Error("match:"+O.status);const J=await O.json();showToast(t("bank-match-done").replace("{matched}",J.matched).replace("{suggested}",J.suggested).replace("{unmatched}",J.unmatched),"success"),await c(n.id),await i()}catch(O){console.warn("[bank-recon] match failed",O),showToast(t("bank-match-failed"),"error")}finally{m.disabled=!1,m.innerHTML=R}}async function v(){if(!(!n||!await showConfirm(t("bank-delete-confirm"),{danger:!0})))try{const R=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!R.ok)throw new Error("delete:"+R.status);showToast(t("bank-deleted"),"success"),n=null,a=[],te(),await i()}catch(R){console.warn("[bank-recon] delete failed",R),showToast(t("bank-delete-failed"),"error")}}async function b(){if(s)try{const m=await fetch("/api/bank-recon/tx/"+encodeURIComponent(s.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"ignored"})});if(!m.ok)throw new Error("ignore:"+m.status);ne(),await c(n.id)}catch{showToast(t("bank-action-failed"),"error")}}async function L(m){if(s)try{const R=await fetch("/api/bank-recon/tx/"+encodeURIComponent(s.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"matched",history_id:m})});if(!R.ok)throw new Error("pick:"+R.status);showToast(t("bank-matched-ok"),"success"),ne(),await c(n.id)}catch{showToast(t("bank-action-failed"),"error")}}function C(){const m=document.getElementById("bank-status-summary");if(!m)return;if(e.length===0){m.textContent=t("bank-pill-none");return}let O=0;for(const J of e)J.parse_status==="parsed"&&(J.unmatched_count||0)>0&&O++;m.textContent=O>0?t("bank-pill-pending").replace("{n}",O):t("bank-pill-ok")}let P="all";function I(){const m=document.getElementById("bank-sessions-list");if(!m)return;let R=e||[];if(P==="parsed"?R=R.filter(O=>O.parse_status==="parsed"):P==="failed"&&(R=R.filter(O=>O.parse_status==="parse_failed")),!e||e.length===0){m.innerHTML='<div class="bank-empty" data-i18n="bank-sessions-empty">'+t("bank-sessions-empty")+"</div>";return}if(R.length===0){m.innerHTML='<div class="bank-empty">'+t("bank-sess-filter-empty")+"</div>";return}m.innerHTML=R.map(O=>Y(O)).join(""),m.querySelectorAll(".bank-session-row").forEach(O=>{O.addEventListener("click",J=>{J.target.closest(".bank-session-trash")||c(O.dataset.sessionId)})}),m.querySelectorAll(".bank-session-trash").forEach(O=>{O.addEventListener("click",J=>{J.stopPropagation();const X=O.dataset.sessionId,de=O.dataset.sessionName||"";j(X,de)})})}async function j(m,R){if(!m)return;const O=(t("bank-session-delete-confirm")||"确定删除这条对账记录吗?").replace("{name}",R||"");if(await showConfirm(O,{danger:!0}))try{const X=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(m),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!X.ok)throw new Error("delete:"+X.status);showToast(t("bank-deleted"),"success"),n&&n.id===m&&(n=null,a=[],te()),await i(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()}catch(X){console.warn("[bank-recon] delete failed",X),showToast(t("bank-delete-failed"),"error")}}window._deleteBankSession=j;function Y(m){const R=(m.bank_code||"OTHER").toUpperCase(),O=U(m.period_start,m.period_end),J=m.account_last4?"···"+m.account_last4:"",X=G(m),de=M(m.created_at);return`
            <div class="bank-session-row" data-session-id="${z(m.id)}">
                <div class="bank-session-bank bk-${z(R)}">${z(R)}</div>
                <div class="bank-session-info">
                    <div class="bank-session-title">${z(m.source_filename||O||"-")}</div>
                    <div class="bank-session-meta">${z(O)} · ${z(J)} · ${z(de)}</div>
                </div>
                <div class="bank-session-counts">${X}</div>
                <button class="bank-session-trash" data-session-id="${z(m.id)}" data-session-name="${z(m.source_filename||"")}" title="${z(t("bank-session-delete-tip")||"删除")}">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/>
                    </svg>
                </button>
                <div class="bank-session-arrow">
                    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg>
                </div>
            </div>
        `}function G(m){if(m.parse_status==="parse_failed")return`<span class="bank-session-count cnt-failed">${t("bank-count-parse-failed")}</span>`;if(m.parse_status!=="parsed")return`<span class="bank-session-count">${t("bank-count-parsing")}</span>`;const R=m.tx_count||0,O=m.matched_count||0,J=m.unmatched_count||0,X=[`<span class="bank-session-count">${R} ${t("bank-count-tx")}</span>`];return O>0&&X.push(`<span class="bank-session-count cnt-matched">${O} ${t("bank-count-matched")}</span>`),J>0&&X.push(`<span class="bank-session-count cnt-unmatched">${J} ${t("bank-count-unmatched")}</span>`),X.join("")}function W(){document.getElementById("bank-detail").style.display="",document.querySelector(".bank-sessions-section").style.display="none",K(),Q(),re()}function te(){document.getElementById("bank-detail").style.display="none",document.querySelector(".bank-sessions-section").style.display="";const m=document.getElementById("bank-detail-body");m&&m.classList.remove("has-pane"),s=null}function re(){const m=document.getElementById("bank-client-badge");if(!m||!n)return;const R=n.client_id,O=document.getElementById("bank-client-badge-dot"),J=document.getElementById("bank-client-badge-name"),X=document.getElementById("bank-client-badge-caret"),de=typeof _userInfo<"u"?_userInfo:null,se=!(de&&de.role==="member");if(R!=null){const ce=(window._clientsCache||[]).find(ae=>Number(ae.id)===Number(R));m.classList.remove("is-empty"),O&&(O.style.background=ce&&ce.color||"#111111"),J&&(J.textContent=ce&&(ce.short_name||ce.name)||"#"+R)}else m.classList.add("is-empty"),O&&(O.style.background=""),J&&(J.textContent=t("bank-client-none"));se?(m.classList.remove("is-readonly"),m.disabled=!1,X&&(X.style.display="")):(m.classList.add("is-readonly"),m.disabled=!0,X&&(X.style.display="none")),m.style.display=""}let T=null;function x(){if(!n)return;const m=typeof _userInfo<"u"?_userInfo:null;if(!!(m&&m.role==="member"))return;T=n.client_id!=null?Number(n.client_id):null,D();const O=document.getElementById("bank-client-picker-modal");O&&(O.style.display="")}function h(){const m=document.getElementById("bank-client-picker-modal");m&&(m.style.display="none"),T=null}function D(){const m=document.getElementById("bank-client-picker-list");if(!m)return;const R=(window._clientsCache||[]).filter(J=>J&&(J.is_active===!0||J.is_active===void 0)),O=[];O.push('<div class="bank-client-picker-row is-none'+(T==null?" is-selected":"")+'" data-cid=""><span class="bank-cp-dot"></span><span>'+z(t("bank-client-picker-none"))+"</span></div>"),R.forEach(J=>{const X=Number(J.id)===Number(T)?" is-selected":"";O.push('<div class="bank-client-picker-row'+X+'" data-cid="'+z(J.id)+'"><span class="bank-cp-dot" style="background:'+z(J.color||"#111111")+'"></span><span>'+z(J.short_name||J.name||"#"+J.id)+"</span></div>")}),m.innerHTML=O.join(""),m.querySelectorAll(".bank-client-picker-row").forEach(J=>{J.addEventListener("click",()=>{const X=J.dataset.cid;T=X?Number(X):null,D()})})}async function N(){if(n)try{const m=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id)+"/client",{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({client_id:T})});if(!m.ok)throw new Error("client:"+m.status);n.client_id=T,re(),showToast(t("bank-client-changed"),"success"),h();try{await i()}catch{}}catch(m){console.warn("[bank-recon] save client failed",m),showToast(t("bank-client-change-failed"),"error")}}function K(){if(!n)return;const m=n;document.getElementById("bank-detail-title").textContent=(m.bank_code||"-")+(m.account_last4?" ···"+m.account_last4:"")+" · "+(m.source_filename||""),document.getElementById("bank-meta-period").textContent=U(m.period_start,m.period_end)||"-",document.getElementById("bank-meta-opening").textContent=S(m.opening_balance),document.getElementById("bank-meta-inflow").textContent="+"+S(m.total_inflow),document.getElementById("bank-meta-outflow").textContent="-"+S(m.total_outflow),document.getElementById("bank-meta-closing").textContent=S(m.closing_balance);const R=a||[],O=R.length;let J=0,X=0,de=0;for(const se of R){const ce=se.match_status||"unmatched";ce==="matched"?J++:ce==="suggested"?X++:de++}document.getElementById("bank-stat-total").textContent=O,document.getElementById("bank-stat-matched").textContent=J,document.getElementById("bank-stat-suggested").textContent=X,document.getElementById("bank-stat-unmatched").textContent=de}function Q(){const m=document.getElementById("bank-tx-tbody");if(!m)return;let R=a||[];if(o!=="all"&&(R=R.filter(O=>o==="matched"?O.match_status==="matched":o==="suggested"?O.match_status==="suggested":o==="unmatched"?O.match_status==="unmatched"||O.match_status==="ignored":!0)),R.length===0){m.innerHTML=`<tr><td colspan="4" class="bank-empty">${t("bank-tx-empty")}</td></tr>`;return}if(m.innerHTML=R.map(O=>le(O)).join(""),m.querySelectorAll("tr[data-tx-id]").forEach(O=>{O.addEventListener("click",()=>{const J=O.dataset.txId,X=a.find(de=>de.id===J);X&&(m.querySelectorAll("tr.is-selected").forEach(de=>de.classList.remove("is-selected")),O.classList.add("is-selected"),ie(X))})}),s){const O=m.querySelector('tr[data-tx-id="'+s.id+'"]');O&&O.classList.add("is-selected")}}function le(m){const R=m.direction==="OUT",O=R?"-":"+",J=R?"bank-out":"bank-in",X=m.match_status||"unmatched",de=t("bank-match-"+X)||X,se=M(m.tx_date),ce=m.channel?`<span class="bank-tx-channel">${z(m.channel)}</span>`:"";return`
            <tr data-tx-id="${z(m.id)}">
                <td class="bank-tx-date">${z(se)}</td>
                <td class="bank-tx-desc">${ce}${z(m.description||"-")}</td>
                <td class="bank-td-amount ${J}">${O}${S(m.amount)}</td>
                <td><span class="bank-tx-match mt-${X}">${z(de)}</span></td>
            </tr>
        `}async function ie(m){s=m;const R=document.getElementById("bank-detail-body");R&&R.classList.add("has-pane");const O=document.getElementById("bank-cand-pane-title"),J=document.getElementById("bank-cand-pane-sub"),X=document.getElementById("bank-cand-pane-foot");if(O&&(O.textContent=t("bank-cand-pane-current")),J){const se=m.direction==="OUT"?"-":"+",ce=m.direction==="OUT"?"bank-out":"bank-in";J.innerHTML=`${z(M(m.tx_date))}
                <span style="margin:0 6px;color:#D1D5DB">·</span>
                <span>${z(m.description||"-")}</span>
                <span style="margin:0 6px;color:#D1D5DB">·</span>
                <strong class="${ce}">${se}${S(m.amount)}</strong>`}X&&(X.style.display="");const de=document.getElementById("bank-cand-pane-body");if(de){de.innerHTML=`<div class="bank-empty">${t("bank-cand-loading")}</div>`;try{const se=await fetch("/api/bank-recon/tx/"+encodeURIComponent(m.id)+"/candidates",{headers:{Authorization:"Bearer "+token}});if(!se.ok)throw new Error("cands:"+se.status);const ce=await se.json();ee(m,ce.candidates||[])}catch{de.innerHTML=`<div class="bank-empty">${t("bank-cand-load-failed")}</div>`}}}function V(m){const R=Number(m||0);let O="score-low";return R>=85?O="score-high":R>=60&&(O="score-mid"),'<span class="bank-cand-score '+O+'">'+R.toFixed(0)+" "+t("bank-cand-score-unit")+"</span>"}function Z(m,R,O){const J=R.history_id,X=R.invoice_no||"-",de=R.vendor||"-",se=R.amount_total!==null&&R.amount_total!==void 0?S(R.amount_total):"-",ce=R.invoice_date?M(R.invoice_date):"-",ae=R.filename||"",pe=!!O&&m.matched_history_id===J,fe="bank-cand-card"+(R.is_auto_picked?" is-auto":"")+(pe?" is-picked":"");let me="";return pe?me='<button class="btn btn-ghost btn-small" data-act="unmatch"><span>'+t("bank-cand-unmatch")+"</span></button>":me='<button class="btn btn-primary btn-small" data-act="pick" data-hid="'+z(J)+'"><span>'+t(R.is_auto_picked?"bank-cand-confirm":"bank-cand-pick-this")+"</span></button>",'<div class="'+fe+'" data-hid="'+z(J)+'"><div class="bank-cand-card-head"><div class="bank-cand-card-vendor">'+z(de)+"</div>"+V(R.score)+'</div><div class="bank-cand-card-fields"><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-invoice-no")+"</span> "+z(X)+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-amount")+"</span> "+se+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-date")+"</span> "+z(ce)+"</span></div>"+(ae?'<div class="bank-cand-card-file" title="'+z(ae)+'">'+z(ae)+"</div>":"")+(R.reason?'<div class="bank-cand-card-reason">'+z(R.reason)+"</div>":"")+'<div class="bank-cand-card-actions">'+me+"</div></div>"}function ee(m,R){const O=document.getElementById("bank-cand-pane-body");if(!O)return;const J=R||[];let X="";if(m.match_status==="matched")X='<div class="bank-cand-hint hint-matched">'+t("bank-cand-hint-matched").replace("{n}",J.length)+"</div>";else if(m.match_status==="suggested")X='<div class="bank-cand-hint hint-suggested">'+t("bank-cand-hint-suggested").replace("{n}",J.length)+"</div>";else if(J.length>0)X='<div class="bank-cand-hint hint-low">'+t("bank-cand-hint-low").replace("{n}",J.length)+"</div>";else{O.innerHTML='<div class="bank-empty">'+t("bank-cand-no-match-detail")+"</div>";return}const de=m.match_status==="matched",se=J.map(ce=>Z(m,ce,de)).join("");O.innerHTML=X+'<div class="bank-cand-list">'+se+"</div>",O.querySelectorAll('[data-act="pick"]').forEach(ce=>{ce.addEventListener("click",()=>{L(ce.dataset.hid)})}),O.querySelectorAll('[data-act="unmatch"]').forEach(ce=>{ce.addEventListener("click",async()=>{try{await fetch("/api/bank-recon/tx/"+encodeURIComponent(m.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"unmatched"})}),ne(),await c(n.id)}catch{showToast(t("bank-action-failed"),"error")}})})}function ne(){const m=document.getElementById("bank-detail-body");m&&m.classList.remove("has-pane");const R=document.getElementById("bank-cand-pane-title"),O=document.getElementById("bank-cand-pane-sub"),J=document.getElementById("bank-cand-pane-body"),X=document.getElementById("bank-cand-pane-foot");R&&(R.textContent=t("bank-cand-pane-empty-title")),O&&(O.textContent=t("bank-cand-pane-empty-sub")),X&&(X.style.display="none"),J&&(J.innerHTML='<div class="bank-cand-pane-empty"><svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="14" y="10" width="36" height="44" rx="3"/><path d="M22 22h20M22 30h20M22 38h12"/></svg><div>'+t("bank-cand-pane-empty-hint")+"</div></div>");const de=document.getElementById("bank-tx-tbody");de&&de.querySelectorAll("tr.is-selected").forEach(se=>se.classList.remove("is-selected")),s=null}function oe(m){const R=document.getElementById("bank-upload-progress");R&&(R.style.display="none")}function ue(){const m=document.getElementById("bank-upload-error");m&&(m.style.display="none")}function k(m){return{"bank_recon.only_pdf":t("bank-err-only-pdf"),"bank_recon.empty_file":t("bank-err-empty"),"bank_recon.file_too_large":t("bank-err-too-large"),"bank_recon.save_failed":t("bank-err-server"),"bank_recon.scanned":t("bank-err-scanned"),"bank_recon.no_tx":t("bank-err-no-tx"),network:t("bank-err-network")}[m]||t("bank-err-unknown")+" ("+m+")"}function S(m){if(m==null)return"-";const R=Number(m);return isNaN(R)?"-":R.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function M(m){if(!m)return"-";const R=String(m);return R.length>=10?R.slice(0,10):R}function U(m,R){return!m&&!R?"":(M(m)||"?")+" ~ "+(M(R)||"?")}function z(m){return m==null?"":String(m).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}window._loadBankReconPanel=r,window._rerenderBankRecon=function(){if(currentRoute==="automation"){if(I(),n&&(K(),Q(),re(),!s)){const m=document.getElementById("bank-cand-pane-title"),R=document.getElementById("bank-cand-pane-sub");m&&(m.textContent=t("bank-cand-pane-empty-title")),R&&(R.textContent=t("bank-cand-pane-empty-sub"))}E()}},typeof window.subscribeI18n=="function"&&window.subscribeI18n("bank-recon",window._rerenderBankRecon),window._openBankSession=async function(m){m&&(p||await r(),await c(m))}})();(function(){const e=document.getElementById("page-clients");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){let e=[],n=null,a="",o="seller";const s={page:0,pageSize:12,keyword:""},p=new Set;let r=[];const f={keyword:""};let i=null;function c(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}async function l(h,D={}){const N=await fetch(h,{...D,headers:{"Content-Type":"application/json",...c(),...D.headers||{}}});if(!N.ok){const K=await N.json().catch(()=>({}));throw new Error(K.detail||"HTTP "+N.status)}return N.json()}async function d(){try{e=(await l("/api/clients")).clients||[],window._clientsCache=e}catch(h){console.error("loadClientsCache fail",h),e=[]}try{typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter()}catch{}try{typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher()}catch{}return e}function u(h){o=h==="buyer"?"buyer":"seller",document.querySelectorAll("[data-cust-tab]").forEach(K=>K.classList.toggle("active",K.dataset.custTab===o));const D=document.getElementById("cust-pane-seller"),N=document.getElementById("cust-pane-buyer");D&&D.classList.toggle("active",o==="seller"),N&&N.classList.toggle("active",o==="buyer")}function g(){const h=window._userInfo||{},D=String(h.role||"").toLowerCase(),N=String(h.tenant_role||"").toLowerCase();return h.is_super_admin===!0||h.is_owner===!0||D==="owner"||D==="admin"||N==="owner"||N==="admin"}function w(){window._workspaceClientsCache=r,typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl()}async function $(){try{const h=await l("/api/workspace/clients");r=h&&(h.clients||h.items)||[],window._workspaceClientsCache=r}catch(h){console.error("loadSellerCache fail",h),r=[]}return r}function E(){const h=f.keyword.trim().toLowerCase();return h?r.filter(D=>(D.name||"").toLowerCase().includes(h)||(D.tax_id||"").toLowerCase().includes(h)):r}function _(){const h=document.getElementById("seller-tbody");if(!h)return;const D=g(),N=document.getElementById("btn-seller-new");N&&(N.style.display=D?"":"none");const K=E(),Q=typeof window.getActiveWorkspaceClientId=="function"?window.getActiveWorkspaceClientId():null;if(!K.length){h.innerHTML=`<div class="cust-empty">${escapeHtml(t(f.keyword?"cust-no-match":"seller-empty"))}</div>`;return}h.innerHTML=K.map(le=>{const V=Q!=null&&Number(Q)===Number(le.id)?`<span class="cust-badge-current"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7.5l3.2 3.2L12 4"/></svg>${escapeHtml(t("seller-current"))}</span>`:`<button class="cust-row-btn primary" data-saction="activate" data-wid="${le.id}">${escapeHtml(t("seller-set-current"))}</button>`,Z=D?`
                <button class="cust-row-btn" data-saction="edit" data-wid="${le.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
                <button class="cust-row-btn danger" data-saction="archive" data-wid="${le.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h10M4 4v7a1 1 0 001 1h4a1 1 0 001-1V4M5.5 4V2.8a1 1 0 011-1h1a1 1 0 011 1V4"/></svg><span>${escapeHtml(t("wsclient-archive"))}</span></button>`:"";return`<div class="cust-row seller-grid" data-wid="${le.id}">
                <div class="cust-cell-name"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" style="flex-shrink:0;opacity:.55"><rect x="2" y="5" width="12" height="9" rx="1"/><path d="M10 14V4a1 1 0 00-1-1H7a1 1 0 00-1 1v10"/></svg><span class="cust-name-text">${escapeHtml(le.name||"#"+le.id)}</span></div>
                <div class="cust-cell-tax">${escapeHtml(le.tax_id||"—")}</div>
                <div class="align-right">${le.invoice_count||0}</div>
                <div class="cust-row-actions">${V}${Z}</div>
            </div>`}).join("")}function B(h){i=h?h.id:null,document.getElementById("wsclient-modal-title").textContent=t(h?"wsclient-modal-edit":"wsclient-modal-new"),document.getElementById("wsclient-input-name").value=h&&h.name||"",document.getElementById("wsclient-input-tax").value=h&&h.tax_id||"",document.getElementById("wsclient-modal-archive").style.display=h?"":"none",document.getElementById("wsclient-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("wsclient-input-name").focus(),50)}function q(){document.getElementById("wsclient-modal-mask").style.display="none",i=null}async function H(){const h=document.getElementById("wsclient-input-name").value.trim(),D=document.getElementById("wsclient-input-tax").value.trim();if(!h){showToast(t("client-msg-name-required"),"fail");return}try{i?(await l("/api/workspace/clients/"+i,{method:"PATCH",body:JSON.stringify({name:h,tax_id:D})}),showToast(t("client-msg-updated"),"success")):(await l("/api/workspace/clients",{method:"POST",body:JSON.stringify({name:h,tax_id:D||null})}),showToast(t("client-msg-created"),"success")),q(),await $(),_(),w()}catch(N){const K=N&&N.message?N.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+K,"fail")}}async function F(){if(!i)return;const h=r.find(N=>Number(N.id)===Number(i));if(await showConfirm(t("wsclient-archive-confirm").replace("{name}",h?h.name:""),{danger:!0}))try{const N=i;await l("/api/workspace/clients/"+N,{method:"DELETE"}),showToast(t("wsclient-archived"),"success"),typeof window.getActiveWorkspaceClientId=="function"&&Number(window.getActiveWorkspaceClientId())===Number(N)&&typeof window.enterPersonalMode=="function"&&window.enterPersonalMode(),q(),await $(),_(),w()}catch{showToast(t("client-msg-save-fail"),"fail")}}function A(){const h=s.keyword.trim().toLowerCase();return h?e.filter(D=>(D.name||"").toLowerCase().includes(h)||(D.short_name||"").toLowerCase().includes(h)||(D.tax_id||"").toLowerCase().includes(h)):e}function y(){const h=A(),D=s.pageSize,N=Math.max(0,Math.ceil(h.length/D)-1);s.page>N&&(s.page=N);const K=s.page*D;return{all:h,items:h.slice(K,K+D),start:K,ps:D,total:h.length,maxPage:N}}function v(){const h=document.getElementById("buyer-tbody");if(!h)return;const{items:D,start:N,ps:K,total:Q,maxPage:le}=y();Q?h.innerHTML=D.map(ee=>{const ne=p.has(ee.id);return`<div class="cust-row buyer-grid${ne?" selected":""}" data-cid="${ee.id}">
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
                </div>`}).join(""):h.innerHTML=`<div class="cust-empty">${escapeHtml(t(s.keyword?"cust-no-match":"clients-empty"))}</div>`;const ie=document.getElementById("buyer-pager-info");ie&&(ie.textContent=Q?`${N+1}–${Math.min(N+K,Q)} / ${Q}`:"0");const V=document.getElementById("buyer-prev");V&&(V.disabled=s.page<=0);const Z=document.getElementById("buyer-next");Z&&(Z.disabled=s.page>=le),b()}function b(){const h=p.size,D=document.getElementById("buyer-batch-bar");D&&(D.style.display=h?"flex":"none");const N=document.getElementById("buyer-batch-count");N&&(N.textContent=t("cust-selected-n").replace("{n}",h));const K=document.getElementById("buyer-check-all");if(K){const{items:Q}=y(),le=Q.map(V=>V.id),ie=le.filter(V=>p.has(V)).length;K.checked=le.length>0&&ie===le.length,K.indeterminate=ie>0&&ie<le.length}}function L(){p.clear(),v()}async function C(){const h=Array.from(p);if(!(!h.length||!await showConfirm(t("cust-batch-del-confirm").replace("{n}",h.length),{danger:!0})))try{await l("/api/clients/batch-delete",{method:"POST",body:JSON.stringify({ids:h})}),showToast(t("client-msg-deleted"),"success"),p.clear(),await d(),v(),te(),x()}catch{showToast(t("client-msg-save-fail"),"fail")}}window.loadClientsPage=async function(){const h=document.getElementById("seller-tbody");h&&(h.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`);const D=document.getElementById("buyer-tbody");D&&(D.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`),await Promise.all([$(),d()]),_(),v()},window.addEventListener("pearnly:workspace-changed",function(){typeof currentRoute<"u"&&currentRoute==="clients"&&_()});function P(h){n=h?h.id:null;const D=!!h;document.getElementById("client-modal-title").textContent=t(D?"client-modal-edit":"client-modal-new"),document.getElementById("client-input-name").value=h&&h.name||"",document.getElementById("client-input-short").value=h&&h.short_name||"",document.getElementById("client-input-tax").value=h&&h.tax_id||"",document.getElementById("client-input-address").value=h&&h.address||"",document.getElementById("client-input-contact").value=h&&h.contact_person||"",document.getElementById("client-input-phone").value=h&&h.contact_phone||"",document.getElementById("client-input-email").value=h&&h.contact_email||"",document.getElementById("client-input-notes").value=h&&h.notes||"";const N=h&&h.color||"#111111";document.querySelectorAll("#client-color-picker .color-swatch").forEach(K=>{K.classList.toggle("active",K.dataset.color===N)}),document.getElementById("client-modal-delete").style.display=D?"":"none",document.getElementById("client-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("client-input-name").focus(),50)}function I(){document.getElementById("client-modal-mask").style.display="none",n=null}function j(){const h=document.querySelector("#client-color-picker .color-swatch.active");return h?h.dataset.color:"#111111"}async function Y(){const h=document.getElementById("client-input-name").value.trim();if(!h){showToast(t("client-msg-name-required"),"fail");return}const D={name:h,short_name:document.getElementById("client-input-short").value.trim()||null,tax_id:document.getElementById("client-input-tax").value.trim()||null,address:document.getElementById("client-input-address").value.trim()||null,contact_person:document.getElementById("client-input-contact").value.trim()||null,contact_phone:document.getElementById("client-input-phone").value.trim()||null,contact_email:document.getElementById("client-input-email").value.trim()||null,notes:document.getElementById("client-input-notes").value.trim()||null,color:j()};try{n?(await l(`/api/clients/${n}`,{method:"PATCH",body:JSON.stringify(D)}),showToast(t("client-msg-updated"),"success")):(await l("/api/clients",{method:"POST",body:JSON.stringify(D)}),showToast(t("client-msg-created"),"success")),I(),await d(),currentRoute==="clients"&&v(),te(),x()}catch(N){console.error("saveClient fail",N);const K=N&&N.message?N.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+K,"fail")}}async function G(){if(!n)return;const h=e.find(K=>K.id===n);if(!h)return;const D=t("client-delete-confirm").replace("{name}",h.name);if(await showConfirm(D,{danger:!0}))try{await l(`/api/clients/${n}`,{method:"DELETE"}),showToast(t("client-msg-deleted"),"success"),I(),await d(),currentRoute==="clients"&&v(),te(),x()}catch(K){console.error(K),showToast(t("client-msg-save-fail"),"fail")}}async function W(h){const D=e.find(N=>N.id===h);if(typeof window.openClientExportModal=="function"){window.openClientExportModal(h,D?D.name:"");return}try{const N=localStorage.getItem("mrpilot_token"),K=await fetch(`/api/clients/${h}/export?month=all`,{headers:{Authorization:"Bearer "+N}});if(!K.ok){let Z="HTTP "+K.status;try{const ee=await K.json();ee&&ee.detail&&(Z=ee.detail)}catch{}throw new Error(Z)}const Q=await K.blob();if(Q.size<200){showToast(t("client-export-month-empty"),"info");return}const le=D&&D.name?D.name.replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40):"client",ie=URL.createObjectURL(Q),V=document.createElement("a");V.href=ie,V.download=`${le}_export.csv`,V.click(),URL.revokeObjectURL(ie)}catch(N){console.error("exportClient fail",N),showToast(t("client-msg-save-fail")+" · "+(N.message||""),"fail")}}function te(){const h=document.getElementById("drawer-client-select");if(!h)return;const D=h.value;h.innerHTML=`<option value="">${escapeHtml(t("drawer-client-none"))}</option>`+e.map(N=>`<option value="${N.id}">${escapeHtml(N.name)}</option>`).join(""),h.value=D||""}window.bindDrawerClient=function(h,D){const N=document.getElementById("drawer-client-select");if(!N)return;if(te(),N.value=D?String(D):"",!h){N.onchange=null;const Q=document.getElementById("drawer-client-add");Q&&(Q.onclick=()=>P(null));return}N.onchange=async()=>{const Q=N.value?parseInt(N.value,10):null;try{await l(`/api/history/${h}/assign_client`,{method:"POST",body:JSON.stringify({client_id:Q})}),showToast(t("client-msg-updated"),"success");const le=_results[_drawerIdx];le&&(le.client_id=Q),await d()}catch(le){console.error(le),showToast(t("client-msg-save-fail"),"fail"),N.value=D?String(D):""}};const K=document.getElementById("drawer-client-add");K&&(K.onclick=()=>P(null))};let re={fetched:0,items:[],supplier_count:0};window.fillCategoryDatalist=async function(){try{const h=document.getElementById("drawer-cat-datalist"),D=Date.now();if(D-re.fetched<300*1e3){h&&(h.innerHTML=re.items.map(K=>`<option value="${escapeHtml(K)}">`).join("")),T(re.supplier_count);return}const N=await l("/api/categories",{method:"GET"});re.fetched=D,re.items=N&&N.categories||[],re.supplier_count=N&&N.supplier_count||0,h&&(h.innerHTML=re.items.map(K=>`<option value="${escapeHtml(K)}">`).join("")),T(re.supplier_count)}catch(h){console.warn("fillCategoryDatalist failed",h)}};function T(h){const D=document.getElementById("drawer-cat-learned-tag");D&&h>0&&(D.textContent=(t("drawer-suggest-learned-with-count")||"已学 {n}").replace("{n}",h))}function x(){const h=document.getElementById("history-client-filter");if(!h)return;const D=h.value;h.innerHTML=`<option value="">${escapeHtml(t("history-client-all"))}</option>`+e.map(N=>`<option value="${N.id}">${escapeHtml(N.name)}</option>`).join(""),h.value=D||""}window.getHistoryClientFilter=function(){return a},document.addEventListener("DOMContentLoaded",()=>{const h=document.querySelector(".cust-tab-bar");h&&h.addEventListener("click",ae=>{const pe=ae.target.closest("[data-cust-tab]");pe&&u(pe.dataset.custTab)});const D=document.getElementById("btn-buyer-new");D&&D.addEventListener("click",()=>P(null));const N=document.getElementById("buyer-tbody");N&&N.addEventListener("click",ae=>{const pe=ae.target.closest(".buyer-row-check");if(pe){const ge=parseInt(pe.dataset.cid,10);pe.checked?p.add(ge):p.delete(ge);const be=pe.closest(".cust-row");be&&be.classList.toggle("selected",pe.checked),b();return}const fe=ae.target.closest(".cust-row-btn");if(fe){ae.stopPropagation();const ge=parseInt(fe.dataset.cid,10);if(fe.dataset.action==="edit"){const be=e.find(xe=>xe.id===ge);be&&P(be)}else fe.dataset.action==="export"&&W(ge);return}const me=ae.target.closest(".cust-row");if(me&&!ae.target.closest(".cust-cell-check")){const ge=e.find(be=>be.id===parseInt(me.dataset.cid,10));ge&&P(ge)}});const K=document.getElementById("buyer-check-all");K&&K.addEventListener("change",()=>{const{items:ae}=y();ae.forEach(pe=>{K.checked?p.add(pe.id):p.delete(pe.id)}),v()});const Q=document.getElementById("buyer-batch-cancel");Q&&Q.addEventListener("click",L);const le=document.getElementById("buyer-batch-delete");le&&le.addEventListener("click",C);const ie=document.getElementById("buyer-prev");ie&&ie.addEventListener("click",()=>{s.page>0&&(s.page--,v())});const V=document.getElementById("buyer-next");V&&V.addEventListener("click",()=>{s.page++,v()});const Z=document.getElementById("buyer-search");if(Z){let ae;Z.addEventListener("input",()=>{clearTimeout(ae),ae=setTimeout(()=>{s.keyword=Z.value,s.page=0;const pe=document.getElementById("buyer-search-clear");pe&&(pe.style.display=Z.value?"":"none"),v()},200)})}const ee=document.getElementById("buyer-search-clear");ee&&ee.addEventListener("click",()=>{const ae=document.getElementById("buyer-search");ae&&(ae.value=""),s.keyword="",s.page=0,ee.style.display="none",v()});const ne=document.getElementById("btn-seller-new");ne&&ne.addEventListener("click",()=>B(null));const oe=document.getElementById("seller-tbody");oe&&oe.addEventListener("click",ae=>{const pe=ae.target.closest("[data-saction]");if(!pe)return;ae.stopPropagation();const fe=parseInt(pe.dataset.wid,10),me=pe.dataset.saction,ge=r.find(be=>Number(be.id)===fe);me==="activate"?(typeof window.setActiveWorkspaceClientId=="function"&&window.setActiveWorkspaceClientId(fe),_(),typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl(),showToast(t("seller-activated").replace("{name}",ge?ge.name:""),"success")):me==="edit"?ge&&B(ge):me==="archive"&&(i=fe,F())});const ue=document.getElementById("seller-search");if(ue){let ae;ue.addEventListener("input",()=>{clearTimeout(ae),ae=setTimeout(()=>{f.keyword=ue.value;const pe=document.getElementById("seller-search-clear");pe&&(pe.style.display=ue.value?"":"none"),_()},200)})}const k=document.getElementById("seller-search-clear");k&&k.addEventListener("click",()=>{const ae=document.getElementById("seller-search");ae&&(ae.value=""),f.keyword="",k.style.display="none",_()});const S=document.getElementById("wsclient-modal-close");S&&S.addEventListener("click",q);const M=document.getElementById("wsclient-modal-cancel");M&&M.addEventListener("click",q);const U=document.getElementById("wsclient-modal-save");U&&U.addEventListener("click",H);const z=document.getElementById("wsclient-modal-archive");z&&z.addEventListener("click",F);const m=document.getElementById("wsclient-modal-mask");m&&m.addEventListener("click",ae=>{ae.target===m&&q()});const R=document.getElementById("client-modal-close");R&&R.addEventListener("click",I);const O=document.getElementById("client-modal-cancel");O&&O.addEventListener("click",I);const J=document.getElementById("client-modal-save");J&&J.addEventListener("click",Y);const X=document.getElementById("client-modal-delete");X&&X.addEventListener("click",G);const de=document.getElementById("client-modal-mask");de&&de.addEventListener("click",ae=>{ae.target===de&&I()});const se=document.getElementById("client-color-picker");se&&se.addEventListener("click",ae=>{const pe=ae.target.closest(".color-swatch");pe&&(se.querySelectorAll(".color-swatch").forEach(fe=>fe.classList.remove("active")),pe.classList.add("active"))});const ce=document.getElementById("history-client-filter");ce&&ce.addEventListener("change",()=>{a=ce.value,typeof renderHistoryList=="function"&&renderHistoryList()})}),setTimeout(()=>d(),1e3)})();(function(){const e=document.getElementById("page-exceptions");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){let e={statsCache:null,listCache:[],currentRule:null,currentClient:"",currentStatus:"pending",loading:!1,selectedIds:new Set,offset:0,pageSize:50,total:0,loadFailed:!1,listScrollY:0};function n(T,x){let h=t(T)||T;if(x)for(const D in x)h=h.replace(new RegExp("\\{"+D+"\\}","g"),String(x[D]));return h}async function a(){try{const T=e.currentClient||"",x="/api/exceptions/stats?status=pending"+(T?"&client_id="+encodeURIComponent(T):""),h=await fetch(x,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!h.ok)return;const D=await h.json(),N=document.getElementById("nav-exc-badge");if(!N)return;const K=parseInt(D.pending||0,10);K>0?(N.textContent=K>99?"99+":String(K),N.style.display=""):N.style.display="none"}catch{}}function o(T){return T==="high"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M7 1.5L1 12.5h12L7 1.5z"/>
                <line x1="7" y1="6" x2="7" y2="9"/>
                <circle cx="7" cy="10.6" r="0.5" fill="currentColor"/>
            </svg>`:T==="medium"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="7" cy="7" r="5.5"/>
                <line x1="7" y1="4" x2="7" y2="7.5"/>
                <circle cx="7" cy="9.5" r="0.5" fill="currentColor"/>
            </svg>`:`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="7" cy="7" r="5.5"/>
            <line x1="4.5" y1="7" x2="9.5" y2="7"/>
        </svg>`}function s(){return`<svg class="exc-empty-icon" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 19l5 5 13-13"/>
            <circle cx="20" cy="20" r="17"/>
        </svg>`}function p(T){if(T==null)return"—";const x=parseFloat(T);return isNaN(x)?"—":"฿ "+x.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function r(T){return T?T.slice(0,10):"—"}function f(T){document.getElementById("exc-kpi-pending").textContent=T.pending||0,document.getElementById("exc-kpi-high").textContent=T.high_severity||0,document.getElementById("exc-kpi-resolved").textContent=T.resolved||0,document.getElementById("exc-kpi-learned").textContent=T.learned_rules||0;const x=document.getElementById("exc-status-tab-count-pending"),h=document.getElementById("exc-status-tab-count-resolved"),D=document.getElementById("exc-status-tab-count-ignored");x&&(x.textContent=T.pending||0),h&&(h.textContent=T.resolved||0),D&&(D.textContent=T.ignored||0),document.querySelectorAll("#exc-status-tabs .exc-status-tab").forEach(K=>{K.classList.toggle("active",K.dataset.status===(e.currentStatus||"pending"))})}function i(T){const x=document.getElementById("exc-chips");if(!x)return;const h=T.by_rule||{},D=["confidence_low","duplicate","amount_missing","math_mismatch","tax_id_format_invalid"];let K=`<button class="exc-chip ${!e.currentRule?"active":""}" data-rule="">
            <span>${escapeHtml(t("exc-chip-all"))}</span>
            <span class="exc-chip-count">${T.pending||0}</span>
        </button>`;for(const Q of D){const le=h[Q]||0;if(le===0&&e.currentRule!==Q)continue;const ie=e.currentRule===Q;K+=`<button class="exc-chip ${ie?"active":""}" data-rule="${escapeHtml(Q)}">
                <span>${escapeHtml(t("exc-chip-"+Q))}</span>
                <span class="exc-chip-count">${le}</span>
            </button>`}x.innerHTML=K,x.querySelectorAll(".exc-chip").forEach(Q=>{Q.addEventListener("click",()=>{const le=Q.dataset.rule||null;e.currentRule=le,w()})})}function c(T){const x=document.getElementById("exc-list");if(!x)return;if(!T||T.length===0){x.innerHTML=`<div class="exc-empty">
                ${s()}
                <div class="exc-empty-title">${escapeHtml(t("exc-empty-title"))}</div>
                <div>${escapeHtml(t("exc-empty-desc"))}</div>
            </div>`,d();return}const h='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7l3 3 5-5"/></svg>',D=(e.currentStatus||"pending")==="pending";x.innerHTML=T.map(N=>{const K=N.severity||"medium",Q=t("exc-rule-"+N.rule_code)||N.rule_code,le=N.seller_name&&N.seller_name.trim()?N.seller_name:t("exc-no-seller"),ie=N.filename||"—",V=r(N.invoice_date||N.created_at),Z=N.status==="pending",ee=e.selectedIds.has(N.id),ne=D&&Z;return`
                <div class="exc-row sev-${escapeHtml(K)} ${ee?"selected":""}" data-exc-id="${escapeHtml(String(N.id))}">
                    <div class="exc-row-check ${ee?"checked":""}" data-check-id="${escapeHtml(String(N.id))}" ${ne?"":'style="visibility:hidden;"'}>${h}</div>
                    <div class="exc-row-sev">${o(K)}</div>
                    <div class="exc-row-main">
                        <div class="exc-row-title">${escapeHtml(le)} · ${escapeHtml(ie)}</div>
                        <div class="exc-row-meta">
                            ${N.invoice_no?`<span><b>${escapeHtml(N.invoice_no)}</b></span>`:""}
                            <span>${escapeHtml(V)}</span>
                        </div>
                    </div>
                    <div class="exc-row-rule r-${escapeHtml(K)}">${escapeHtml(Q)}</div>
                    <div class="exc-row-amount">${escapeHtml(p(N.total_amount))}</div>
                </div>
            `}).join(""),x.querySelectorAll(".exc-row").forEach(N=>{N.addEventListener("click",K=>{if(K.target.closest(".exc-row-check"))return;const Q=N.dataset.excId;Q&&H(parseInt(Q,10))})}),x.querySelectorAll(".exc-row-check").forEach(N=>{N.addEventListener("click",K=>{K.stopPropagation();const Q=parseInt(N.dataset.checkId,10);Q&&(e.selectedIds.has(Q)?(e.selectedIds.delete(Q),N.classList.remove("checked"),N.closest(".exc-row").classList.remove("selected")):(e.selectedIds.add(Q),N.classList.add("checked"),N.closest(".exc-row").classList.add("selected")),l())})}),l(),d()}function l(){const T=document.getElementById("exc-batch-bar"),x=document.getElementById("exc-batch-count");if(!T||!x)return;const h=e.selectedIds.size;h===0?T.style.display="none":(T.style.display="",x.textContent=n("exc-batch-count",{n:h}))}function d(){const T=document.getElementById("exc-list-foot"),x=document.getElementById("exc-list-count"),h=document.getElementById("exc-loadmore");if(!T||!x||!h)return;const D=e.listCache.length;if(D===0){T.style.display="none";return}T.style.display="";let N=D;const K=e.statsCache;K&&(e.currentRule?N=(K.by_rule||{})[e.currentRule]||D:N=K.pending||D),e.total=N,x.textContent=n("exc-list-count",{shown:D,total:N});const Q=D<N&&D<500;h.style.display=Q?"":"none"}async function u(){try{if(navigator.onLine===!1)throw new Error("offline");const T=e.currentClient||"",x=e.currentStatus||"pending",h=new URLSearchParams;h.set("status",x),T&&h.set("client_id",T);const D="/api/exceptions/stats?"+h.toString(),N=await fetch(D,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!N.ok)throw new Error("http "+N.status);const K=await N.json();return e.statsCache=K,f(K),i(K),K}catch(T){return console.warn("loadExceptionsStats fail",T),null}}function g(T){const x=document.getElementById("exc-list");if(!x)return;const h=`<svg class="exc-error-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="18" cy="18" r="14"/>
            <line x1="18" y1="11" x2="18" y2="19"/>
            <circle cx="18" cy="23" r="0.8" fill="currentColor"/>
        </svg>`,D=T?t("exc-offline"):t("exc-error-retry-title"),N=T?"":t("exc-error-retry-desc");x.innerHTML=`
            <div class="exc-error">
                ${h}
                <div class="exc-error-msg">${escapeHtml(D)}${N?" · "+escapeHtml(N):""}</div>
                <button class="btn btn-sm btn-secondary" id="exc-retry-btn" type="button">${escapeHtml(t("exc-retry-btn"))}</button>
            </div>`;const K=document.getElementById("exc-retry-btn");K&&K.addEventListener("click",()=>window.loadExceptionsPage&&window.loadExceptionsPage())}async function w(T){T=T||{};const x=!!T.append,h=document.getElementById("exc-list");!x&&h&&e.listCache.length===0&&(h.innerHTML=`<div class="exc-loading">${escapeHtml(t("exc-loading"))}</div>`);const D=new URLSearchParams;D.set("status",e.currentStatus||"pending"),e.currentRule&&D.set("rule_code",e.currentRule),e.currentClient&&D.set("client_id",e.currentClient);const N=x?e.listCache.length:0;D.set("limit",String(e.pageSize)),D.set("offset",String(N));try{if(navigator.onLine===!1)throw new Error("offline");const K=await fetch("/api/exceptions/list?"+D.toString(),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!K.ok)throw new Error("http "+K.status);const le=(await K.json()).items||[];x?e.listCache=e.listCache.concat(le):(e.listCache=le,e.selectedIds.clear()),e.loadFailed=!1,c(e.listCache),e.statsCache&&i(e.statsCache)}catch(K){console.warn("loadExceptionsList fail",K),e.loadFailed=!0;const Q=navigator.onLine===!1||String(K.message||"").includes("offline");x?showToast(t("exc-toast-load-fail"),"error"):(g(Q),showToast(Q?t("exc-offline"):t("exc-toast-load-fail"),"error"))}}async function $(){if(!e.loading&&!(e.listCache.length>=500)){e.loading=!0;try{await w({append:!0})}finally{e.loading=!1}}}function E(){const T=document.getElementById("exc-client-filter");if(!T)return;const x=window._clientsCache||[],h=e.currentClient||"",D=typeof t=="function"?t("history-client-all"):"全部客户";T.innerHTML=`<option value="">${escapeHtml(D)}</option>`+x.map(N=>`<option value="${N.id}">${escapeHtml(N.name)}</option>`).join(""),T.value=h}window.loadExceptionsPage=async function(){if(!e.loading){e.loading=!0;try{E(),typeof window.loadErpExceptions=="function"&&window.loadErpExceptions(),await u(),await w()}finally{e.loading=!1}}},window.refreshExcBadge=a,window._refreshExcClientFilter=E,window._excState=e,window._rerenderExceptions=function(){try{E()}catch{}e.statsCache&&(f(e.statsCache),i(e.statsCache)),e.listCache&&e.listCache.length&&c(e.listCache);try{window._erpExcState&&window._erpExcState.items&&window._erpExcState.items.length&&typeof window._rerenderErpExceptions=="function"&&window._rerenderErpExceptions()}catch{}_.openExcId&&L()};let _={openExcId:null,excRow:null,history:null,loading:!1,pdfUrl:null,pdfStatus:"idle",editing:!1,editFields:null};function B(){if(_.pdfUrl){try{URL.revokeObjectURL(_.pdfUrl)}catch{}_.pdfUrl=null}_.pdfStatus="idle"}async function q(T,x){_.pdfStatus="loading",L();try{const h=await fetch("/api/history/"+encodeURIComponent(T)+"/pdf",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(_.openExcId!==x)return;if(h.status===404){_.pdfStatus="empty",L();return}if(!h.ok)throw new Error("http "+h.status);const D=await h.blob();if(_.openExcId!==x)return;B(),_.pdfUrl=URL.createObjectURL(D),_.pdfStatus="ready",L()}catch(h){if(_.openExcId!==x)return;console.warn("loadDrawerPdf fail",h),_.pdfStatus="error",L()}}function H(T){const x=(e.listCache||[]).find(h=>h.id===T);if(!x){showToast(t("exc-drawer-error"),"error");return}e.listScrollY=window.scrollY||document.documentElement.scrollTop||0,B(),_.editing=!1,_.editFields=null,_.openExcId=T,_.excRow=x,_.history=null,document.getElementById("exc-drawer-mask").classList.add("show"),document.getElementById("exc-drawer").classList.add("show"),L(),A(x.history_id),q(x.history_id,T)}function F(){B(),_.editing=!1,_.editFields=null,_.openExcId=null,_.excRow=null,_.history=null,document.getElementById("exc-drawer-mask").classList.remove("show"),document.getElementById("exc-drawer").classList.remove("show");const T=e.listScrollY||0;T>0&&requestAnimationFrame(()=>window.scrollTo(0,T))}async function A(T){try{const x=await fetch("/api/history/"+encodeURIComponent(T),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!x.ok)throw new Error("http "+x.status);_.history=await x.json()}catch(x){console.warn("loadHistoryDetail fail",x),_.history={_err:!0}}_.excRow&&L()}function y(T){if(!T||!T.pages)return{};const x=T.pages,h=x.find(D=>!D.is_duplicate&&!D.is_copy)||x[0];return h&&h.fields||{}}function v(T){if(T==null)return"—";const x=typeof T=="number"?T:parseFloat(String(T).replace(/,/g,""));return isNaN(x)?escapeHtml(String(T)):"฿ "+x.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function b(T,x){if(x=x||{},T==="math_mismatch")return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-subtotal"))}</b><span>${escapeHtml(v(x.subtotal))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-vat"))}</b><span>${escapeHtml(v(x.vat))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(v(x.total_expected))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-actual"))}</b><span class="v-bad">${escapeHtml(v(x.total_actual))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-diff"))}</b><span class="v-bad">${escapeHtml(v(x.diff))}</span></div>
            `;if(T==="tax_id_format_invalid")return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-seller-tax"))}</b><span class="v-bad">${escapeHtml(x.tax_id_normalized||x.tax_id_raw||"—")}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-tax-len"))}</b><span class="v-bad">${escapeHtml(String(x.actual_length||"?"))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(t("exc-detail-tax-expected"))}</span></div>
            `;if(T==="duplicate"){const h=x.level==="exact"?t("exc-detail-dup-level-exact"):t("exc-detail-dup-level-likely");return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-dup-match"))}</b><span>${escapeHtml(x.match_filename||"—")}</span></div>
                ${x.match_invoice_no?`<div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-invoice-no"))}</b><span>${escapeHtml(x.match_invoice_no)}</span></div>`:""}
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span>${escapeHtml(h)}</span></div>
            `}return T==="confidence_low"?`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-conf-label"))}</b><span class="v-bad">${escapeHtml(x.confidence||"—")}</span></div>
            `:T==="amount_missing"?`<div class="exc-why-detail-row" style="justify-content:center;color:var(--danger);"><span>${escapeHtml(t("exc-detail-missing"))}</span></div>`:`<div class="exc-why-detail-row"><span style="font-size:11px;">${escapeHtml(JSON.stringify(x))}</span></div>`}function L(){const T=_.excRow;if(!T)return;const x=T.seller_name&&T.seller_name.trim()?T.seller_name:t("exc-no-seller"),h=T.filename||"—";document.getElementById("exc-drawer-title").textContent=h;const D="exc-status-"+(T.status||"pending"),N=t(D)||T.status,K="s-"+(T.status||"pending"),Q=(T.invoice_date||T.created_at||"").slice(0,10);document.getElementById("exc-drawer-sub").innerHTML=`
            <span>${escapeHtml(x)}</span>
            ${T.invoice_no?`<span>· ${escapeHtml(T.invoice_no)}</span>`:""}
            ${Q?`<span>· ${escapeHtml(Q)}</span>`:""}
            <span class="exc-status-chip ${K}">${escapeHtml(N)}</span>
        `;const le=T.severity||"medium",ie=t("exc-rule-"+T.rule_code)||T.rule_code,V=b(T.rule_code,T.detail||{}),Z=y(_.history),ee=_.history===null,ne=_.history&&_.history._err,oe=new Set;T.rule_code==="math_mismatch"?(oe.add("subtotal"),oe.add("vat"),oe.add("total_amount")):T.rule_code==="tax_id_format_invalid"?oe.add("seller_tax"):T.rule_code==="amount_missing"&&(oe.add("total_amount"),oe.add("invoice_number"));const ue=!!_.editing,k=_.editFields||{},S=(ae,pe,fe)=>{if(ee)return`<div class="exc-field-row"><label>${escapeHtml(t(pe))}</label><span class="val empty">…</span></div>`;const me=ue?k[ae]!==void 0?k[ae]:Z[ae]!==void 0&&Z[ae]!==null?Z[ae]:"":Z[ae],ge=oe.has(ae)?"flagged":"";if(ue){const ze=fe?"number":"text",Te=fe?' step="0.01" inputmode="decimal"':"",He=me==null?"":String(me).replace(/"/g,"&quot;");return`<div class="exc-field-row ${ge} editing">
                    <label>${escapeHtml(t(pe))}</label>
                    <input class="exc-field-input" type="${ze}"${Te} data-edit-key="${escapeHtml(ae)}" value="${He}">
                </div>`}const be=fe?v(me):me||"",xe=me==null||me===""?`<span class="val empty">${escapeHtml(t("exc-empty-val"))}</span>`:`<span class="val">${escapeHtml(be)}</span>`;return`<div class="exc-field-row ${ge}"><label>${escapeHtml(t(pe))}</label>${xe}</div>`};let M="";ne?M=`<div class="exc-drawer-error">${escapeHtml(t("exc-drawer-error"))}</div>`:M=`
                <div class="exc-fields">
                    ${S("invoice_number","exc-fld-invoice-no",!1)}
                    ${S("date","exc-fld-date",!1)}
                    ${S("seller_name","exc-fld-seller",!1)}
                    ${S("seller_tax","exc-fld-seller-tax",!1)}
                    ${S("buyer_name","exc-fld-buyer",!1)}
                    ${S("buyer_tax","exc-fld-buyer-tax",!1)}
                    ${S("subtotal","exc-fld-subtotal",!0)}
                    ${S("vat","exc-fld-vat",!0)}
                    ${S("total_amount","exc-fld-total",!0)}
                </div>
            `;const U=(()=>{if(_.pdfStatus==="loading"||_.pdfStatus==="idle")return`
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
                `;const ae=_.pdfUrl;return`
                <div class="exc-pdf-toolbar">
                    <span class="exc-pdf-toolbar-title">${escapeHtml(h)}</span>
                    <div class="exc-pdf-toolbar-actions">
                        <a class="exc-pdf-icon-btn" id="exc-pdf-open-tab" href="${ae}" target="_blank" rel="noopener" title="${escapeHtml(t("exc-pdf-open-tab"))}">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M8 2h4v4M12 2L7 7"/>
                                <path d="M11 8v3a1 1 0 01-1 1H3a1 1 0 01-1-1V4a1 1 0 011-1h3"/>
                            </svg>
                        </a>
                        <a class="exc-pdf-icon-btn" id="exc-pdf-download" href="${ae}" download="${escapeHtml(h)}" title="${escapeHtml(t("exc-pdf-download"))}">
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
                        ${T.status==="pending"&&!ee&&!ne?ue?`
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
                    ${M}
                </div>
            </div>
        `;const z=document.getElementById("exc-fld-edit");z&&z.addEventListener("click",()=>{_.editing=!0,_.editFields={...y(_.history)},L()});const m=document.getElementById("exc-fld-cancel");m&&m.addEventListener("click",()=>{_.editing=!1,_.editFields=null,L()});const R=document.getElementById("exc-fld-save");R&&R.addEventListener("click",()=>C()),document.querySelectorAll(".exc-field-input").forEach(ae=>{ae.addEventListener("input",()=>{_.editFields||(_.editFields={}),_.editFields[ae.dataset.editKey]=ae.value})});const J=document.getElementById("exc-pdf-retry");J&&_.openExcId&&J.addEventListener("click",()=>{_.excRow&&q(_.excRow.history_id,_.openExcId)});const X=T.status==="pending",de=!!(T.seller_name&&T.seller_name.trim()),se=document.getElementById("exc-btn-resolve"),ce=document.getElementById("exc-btn-ignore");se.disabled=!X,ce.disabled=!X||!de,ce.title=de?t("exc-ignore-hint"):t("exc-ignore-no-seller")}async function C(){if(!_.openExcId||!_.history||!_.history.pages||_.loading)return;_.loading=!0;const T=showToast(t("exc-fld-saving"),"loading",0);try{const x=JSON.parse(JSON.stringify(_.history.pages||[]));let h=x.findIndex(ie=>!ie.is_duplicate&&!ie.is_copy);h<0&&(h=0),x[h]||(x[h]={fields:{}});const D=x[h].fields||{},N=_.editFields||{},K=new Set(["subtotal","vat","total_amount"]),Q={...D};for(const ie in N){let V=N[ie];if((V===""||V===void 0)&&(V=null),K.has(ie)&&V!==null){const Z=parseFloat(V);V=isNaN(Z)?null:Z}Q[ie]=V}x[h].fields=Q;const le=await fetch("/api/history/"+encodeURIComponent(_.history.id),{method:"PUT",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({pages:x})});if(!le.ok)throw new Error("http "+le.status);T(),showToast(t("exc-fld-save-ok"),"success"),F(),await u(),await w(),a()}catch(x){T(),console.warn("save fields fail",x),showToast(t("exc-fld-save-fail"),"error")}finally{_.loading=!1}}async function P(){if(!(!_.openExcId||_.loading)){_.loading=!0;try{const T=await fetch("/api/exceptions/"+_.openExcId+"/resolve",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!T.ok)throw new Error("http "+T.status);showToast(t("exc-toast-resolved"),"success"),F(),await u(),await w(),a()}catch(T){console.warn("resolve fail",T),showToast(t("exc-toast-action-fail"),"error")}finally{_.loading=!1}}}async function I(){if(!(!_.openExcId||_.loading)){_.loading=!0;try{const T=await fetch("/api/exceptions/"+_.openExcId+"/ignore",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!T.ok)throw new Error("http "+T.status);showToast(t("exc-toast-ignored"),"success"),F(),await u(),await w(),a()}catch(T){console.warn("ignore fail",T),showToast(t("exc-toast-action-fail"),"error")}finally{_.loading=!1}}}let j=!1;async function Y(){if(j)return;const T=Array.from(e.selectedIds);if(T.length===0||!await showConfirm(n("exc-batch-confirm-resolve",{n:T.length})))return;j=!0;const h=showToast(n("exc-batch-count",{n:T.length})+" …","loading",0);try{const D=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:T,action:"resolve"})});if(!D.ok)throw new Error("http "+D.status);const N=await D.json();h(),showToast(n("exc-toast-batch-resolved",{n:N.processed||0}),"success"),e.selectedIds.clear(),await u(),await w(),a()}catch(D){h(),console.warn("batch resolve fail",D),showToast(t("exc-toast-batch-fail"),"error")}finally{j=!1}}async function G(){if(j)return;const T=Array.from(e.selectedIds);if(T.length===0||!await showConfirm(n("exc-batch-confirm-ignore",{n:T.length}),{danger:!1}))return;j=!0;const h=showToast(n("exc-batch-count",{n:T.length})+" …","loading",0);try{const D=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:T,action:"ignore"})});if(!D.ok)throw new Error("http "+D.status);const N=await D.json();h(),showToast(n("exc-toast-batch-ignored",{n:N.processed||0,wl:N.whitelist_added||0}),"success"),e.selectedIds.clear(),await u(),await w(),a()}catch(D){h(),console.warn("batch ignore fail",D),showToast(t("exc-toast-batch-fail"),"error")}finally{j=!1}}function W(){e.selectedIds.clear(),c(e.listCache)}document.addEventListener("click",T=>{T.target.closest("#exc-drawer-close")&&F(),T.target.closest("#exc-drawer-mask")&&F(),T.target.closest("#exc-btn-resolve")&&P(),T.target.closest("#exc-btn-ignore")&&I(),T.target.closest("#exc-batch-resolve")&&Y(),T.target.closest("#exc-batch-ignore")&&G(),T.target.closest("#exc-batch-clear")&&W(),T.target.closest("#exc-loadmore")&&$()}),document.addEventListener("keydown",T=>{T.key==="Escape"&&_.openExcId&&F()}),document.addEventListener("click",T=>{T.target.closest("#btn-exc-refresh")&&(typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),a())}),document.addEventListener("change",T=>{if(!T.target.closest("#exc-client-filter"))return;const x=T.target;e.currentClient=x.value||"",e.currentRule=null,e.selectedIds.clear(),e.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),a()}),document.addEventListener("click",T=>{const x=T.target.closest("#exc-status-tabs .exc-status-tab");if(!x)return;const h=x.dataset.status||"pending";h!==e.currentStatus&&(e.currentStatus=h,e.currentRule=null,e.selectedIds.clear(),e.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage())}),window.addEventListener("online",()=>{e.loadFailed&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage&&window.loadExceptionsPage()}),setTimeout(a,1500),setInterval(a,6e4);function te(T){if(!T)return"—";try{const x=new Date(T),h=D=>String(D).padStart(2,"0");return`${x.getFullYear()}-${h(x.getMonth()+1)}-${h(x.getDate())} ${h(x.getHours())}:${h(x.getMinutes())}`}catch{return T.slice(0,16).replace("T"," ")}}async function re(){const T=document.getElementById("learned-list");if(T){T.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-loading"))}</div>`;try{const x=await fetch("/api/exception-whitelist",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!x.ok)throw new Error("http "+x.status);const D=(await x.json()).items||[];if(D.length===0){T.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-empty"))}</div>`;return}const N=`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 4h8M5.5 4V2.5h3V4M4 4l0.6 8.5h4.8L10 4"/>
            </svg>`;T.innerHTML=D.map(K=>{const Q=t("exc-rule-"+K.rule_code)||K.rule_code;return`
                    <div class="learned-row" data-wl-id="${escapeHtml(String(K.id))}">
                        <div class="learned-seller" title="${escapeHtml(K.seller_name)}">${escapeHtml(K.seller_name)}</div>
                        <div class="learned-rule">${escapeHtml(Q)}</div>
                        <div class="learned-date">${escapeHtml(te(K.created_at))}</div>
                        <button class="learned-del-btn" data-del-wl="${escapeHtml(String(K.id))}" title="${escapeHtml(t("set-learned-del"))}" type="button">${N}</button>
                    </div>
                `}).join("")}catch(x){console.warn("loadLearnedRules fail",x),T.innerHTML=`<div class="learned-empty">${escapeHtml(t("exc-toast-load-fail"))}</div>`}}}window.loadLearnedRules=re,document.addEventListener("click",async T=>{const x=T.target.closest("[data-del-wl]");if(!x)return;const h=parseInt(x.dataset.delWl,10);if(!h)return;const D=x.closest(".learned-row"),N=D&&D.querySelector(".learned-seller"),K=N?N.textContent.trim():"",Q=t("set-learned-del-confirm").replace("{seller}",K);if(await showConfirm(Q,{danger:!0}))try{const ie=await fetch("/api/exception-whitelist/"+h,{method:"DELETE",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!ie.ok)throw new Error("http "+ie.status);showToast(t("set-learned-del-ok"),"success"),re(),typeof window.loadExceptionsPage=="function"&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage()}catch(ie){console.warn("delete whitelist fail",ie),showToast(t("set-learned-del-fail"),"error")}})})();(function(){let e={items:[],q:"",cat:"",selected:new Set,total:0,categories:{},pageSize:30,loading:!1,focusSearch:!1,searchCaret:0},n=null;function a(){return localStorage.getItem("mrpilot_token")||""}function o(d){const u=typeof currentLang=="string"&&currentLang||window._currentLang||"th",g=d.error_friendly&&d.error_friendly[u];if(g)return g;if(typeof humanizeError=="function"&&d.error_msg)try{return humanizeError(d.error_msg)}catch{}return t("erp-exc-reason-"+(d.category||"other"))}function s(){const d=document.getElementById("erp-exc-batch");if(!d)return;const u=e.selected.size;d.hidden=u===0;const g=d.querySelector(".erp-exc-batch-count");g&&(g.textContent=String(u))}function p(){const d=document.getElementById("erp-exc-block");if(!d)return;const u=e;if(!(u.total>0||!!u.q||!!u.cat)){d.hidden=!0,d.innerHTML="";return}d.hidden=!1;const w=u.categories||{},$=Object.keys(w).reduce((b,L)=>b+w[L],0);let E=`<button class="erp-exc-chip ${u.cat===""?"active":""}" data-erpexc-cat=""><span>${escapeHtml(t("erp-exc-cat-all"))}</span><span class="erp-exc-chip-count">${$}</span></button>`;Object.keys(w).forEach(b=>{E+=`<button class="erp-exc-chip ${u.cat===b?"active":""}" data-erpexc-cat="${escapeHtml(b)}"><span>${escapeHtml(t("erp-exc-cat-"+b))}</span><span class="erp-exc-chip-count">${w[b]}</span></button>`});const _=u.items||[],B=_.length>0&&_.every(b=>u.selected.has(b.id)),q=_.map(b=>{const L=b.state==="needs_action"?"needs":b.state==="retrying"?"retry":"fail",C=t("erp-exc-state-"+(b.state||"failed")),P=o(b),I=u.selected.has(b.id)?"checked":"";return`<div class="erp-exc-row" data-erpexc-id="${escapeHtml(b.id)}">
                <span class="ex-cb"><input type="checkbox" class="erp-exc-cb" data-erpexc-cb="${escapeHtml(b.id)}" ${I}></span>
                <span class="ex-inv" title="${escapeHtml(b.invoice_no||"")}">${escapeHtml(b.invoice_no||"—")}</span>
                <span class="ex-seller" title="${escapeHtml(b.seller_name||"")}">${escapeHtml(b.seller_name||"—")}</span>
                <span class="ex-buyer" title="${escapeHtml(b.ocr_buyer_name||"")}">${escapeHtml(b.ocr_buyer_name||"—")}</span>
                <span class="ex-state"><span class="erp-exc-state ${L}">${escapeHtml(C)}</span></span>
                <span class="ex-reason" title="${escapeHtml(P)}">${escapeHtml(P)}${b.error_code?` <span class="erp-exc-code">${escapeHtml(b.error_code)}</span>`:""}</span>
                <span class="ex-act"><button class="btn btn-sm btn-secondary" type="button" data-erpexc-retry="${escapeHtml(b.id)}">${escapeHtml(t("erp-exc-retry"))}</button></span>
            </div>`}).join(""),H=_.length===0?`<div class="erp-exc-empty">${escapeHtml(t("erp-exc-empty"))}</div>`:"",F=_.length<u.total?`<button class="erp-exc-more" type="button" id="erp-exc-more">${escapeHtml(t("erp-exc-load-more"))} (${_.length}/${u.total})</button>`:u.total>0?`<div class="erp-exc-count">${escapeHtml(t("erp-exc-shown",{n:_.length,total:u.total}))}</div>`:"";d.innerHTML=`
            <div class="erp-exc-head">
                <h2 class="erp-exc-title">${escapeHtml(t("erp-exc-title"))}</h2>
                <span class="erp-exc-sub">${escapeHtml(t("erp-exc-sub"))}</span>
                <input type="search" class="erp-exc-search" id="erp-exc-search" placeholder="${escapeHtml(t("erp-exc-search-ph"))}" value="${escapeHtml(u.q)}">
            </div>
            <div class="erp-exc-chips">${E}</div>
            <div class="erp-exc-batch" id="erp-exc-batch" ${u.selected.size?"":"hidden"}>
                <span class="erp-exc-batch-info"><span class="erp-exc-batch-count">${u.selected.size}</span> ${escapeHtml(t("erp-exc-batch-selected"))}</span>
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
                ${q}${H}
            </div>
            <div class="erp-exc-foot">${F}</div>`;const A=document.getElementById("erp-exc-search");if(A){if(u.focusSearch){A.focus();try{A.setSelectionRange(u.searchCaret,u.searchCaret)}catch{}}A.addEventListener("input",()=>{u.q=A.value,u.focusSearch=!0,u.searchCaret=A.selectionStart||A.value.length,clearTimeout(n),n=setTimeout(()=>i(!1),350)}),A.addEventListener("blur",()=>{u.focusSearch=!1})}d.querySelectorAll(".erp-exc-chip").forEach(b=>{b.addEventListener("click",()=>{u.cat=b.dataset.erpexcCat||"",i(!1)})}),d.querySelectorAll("[data-erpexc-retry]").forEach(b=>{b.addEventListener("click",L=>{L.stopPropagation(),r(b.dataset.erpexcRetry,b)})}),d.querySelectorAll(".erp-exc-cb").forEach(b=>{b.addEventListener("change",()=>{const L=b.dataset.erpexcCb;b.checked?u.selected.add(L):u.selected.delete(L);const C=document.getElementById("erp-exc-cb-all");C&&(C.checked=_.length>0&&_.every(P=>u.selected.has(P.id))),s()})});const y=document.getElementById("erp-exc-cb-all");y&&y.addEventListener("change",()=>{_.forEach(b=>{y.checked?u.selected.add(b.id):u.selected.delete(b.id)}),d.querySelectorAll(".erp-exc-cb").forEach(b=>{b.checked=y.checked}),s()}),d.querySelectorAll("[data-erpexc-batch]").forEach(b=>{b.addEventListener("click",()=>f(b.dataset.erpexcBatch))});const v=document.getElementById("erp-exc-more");v&&v.addEventListener("click",()=>i(!0)),d.querySelectorAll(".erp-exc-row:not(.erp-exc-row-head)").forEach(b=>{b.addEventListener("click",L=>{L.target.closest("input,button")||typeof window._erpExcOpenEdit=="function"&&window._erpExcOpenEdit(b.dataset.erpexcId)})})}async function r(d,u){if(d){u&&(u.disabled=!0,u.textContent=t("erp-exc-retrying"));try{const g=await fetch("/api/erp/logs/"+encodeURIComponent(d)+"/retry",{method:"POST",headers:{Authorization:"Bearer "+a()}}),w=await g.json().catch(()=>({}));showToast(g.ok&&w.ok?t("erp-exc-retry-ok"):t("erp-exc-retry-fail"),g.ok&&w.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.delete(d),i(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function f(d){const u=Array.from(e.selected);if(d==="clear"){e.selected.clear(),p();return}if(u.length!==0){if(d==="delete"){if(!await showConfirm(t("erp-exc-batch-delete-confirm",{n:u.length}),{danger:!0}))return;try{const w=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:u.slice(0,200)})}),$=await w.json().catch(()=>({}));showToast(w.ok?t("erp-exc-batch-delete-ok",{n:$.deleted||0}):t("erp-exc-retry-fail"),w.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}}else if(d==="retry")try{const g=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:u.slice(0,50)})}),w=await g.json().catch(()=>({}));showToast(g.ok?t("erp-exc-batch-retry-ok",{ok:w.succeeded||0,fail:(w.failed||0)+(w.skipped||0)}):t("erp-exc-retry-fail"),g.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.clear(),i(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function i(d){const u=document.getElementById("erp-exc-block");if(!(!u||e.loading)){e.loading=!0;try{const g=new URLSearchParams;e.q&&g.set("q",e.q),e.cat&&g.set("category",e.cat),g.set("limit",String(e.pageSize)),g.set("offset",String(d?e.items.length:0));const w=await fetch("/api/erp/exceptions?"+g.toString(),{headers:{Authorization:"Bearer "+a()}});if(!w.ok){d||(u.hidden=!0);return}const $=await w.json(),E=$.items||[];e.items=d?e.items.concat(E):E,e.total=$.total||0,e.categories=$.categories||{},p()}catch{d||(u.hidden=!0)}finally{e.loading=!1}}}let c={};function l(){const d=document.getElementById("erp-exc-modal");d&&d.remove()}window._erpExcOpenEdit=function(d){const u=(e.items||[]).find(H=>String(H.id)===String(d));if(!u)return;const g=!!u.history_client_id&&u.category==="customer_mismatch",w=u.category==="product_mismatch"&&!!u.history_id&&!!u.endpoint_id,$=o(u),E=u.state==="needs_action"?"needs":u.state==="retrying"?"retry":"fail",_=(H,F)=>`<div class="erp-exc-m-row"><span class="erp-exc-m-k">${escapeHtml(H)}</span><span class="erp-exc-m-v">${escapeHtml(F||"—")}</span></div>`;let B="";if(g)B=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-pick"))}</div>
                    <input type="search" class="erp-exc-m-search" id="erp-exc-m-search" placeholder="${escapeHtml(t("erp-exc-edit-pick-ph"))}">
                    <div class="erp-exc-m-custlist" id="erp-exc-m-custlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-pick-loading"))}</div>
                    </div>
                </div>`;else if(w)B=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-prod-intro"))}</div>
                    <div class="erp-exc-m-custlist" id="erp-exc-m-prodlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-prod-loading"))}</div>
                    </div>
                </div>`;else{const H="erp-exc-edit-hint-"+(u.category||"other");let F=t(H);(!F||F===H)&&(F=$),B=`<div class="erp-exc-m-hint">${escapeHtml(F)}</div>`}const q=document.createElement("div");if(q.id="erp-exc-modal",q.className="erp-exc-modal-overlay",q.innerHTML=`
            <div class="erp-exc-modal" role="dialog" aria-modal="true">
                <div class="erp-exc-m-head">
                    <h3>${escapeHtml(t("erp-exc-edit-title"))}</h3>
                    <button class="erp-exc-m-close" type="button" id="erp-exc-m-close" aria-label="close">×</button>
                </div>
                <div class="erp-exc-m-body">
                    <div class="erp-exc-m-reason"><span class="erp-exc-state ${E}">${escapeHtml(t("erp-exc-state-"+(u.state||"failed")))}</span> ${escapeHtml($)}${u.error_code?` <span class="erp-exc-code">${escapeHtml(u.error_code)}</span>`:""}</div>
                    ${_(t("erp-exc-f-invoice"),u.invoice_no)}
                    ${_(t("erp-exc-f-seller"),u.seller_name)}
                    ${_(t("erp-exc-f-buyer"),u.ocr_buyer_name)}
                    ${_(t("erp-exc-edit-field-current"),u.client_name)}
                    ${B}
                </div>
                <div class="erp-exc-m-foot">
                    <button class="btn btn-sm btn-ghost" type="button" id="erp-exc-m-cancel">${escapeHtml(t("erp-exc-edit-close"))}</button>
                    <button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-retry">${escapeHtml(t("erp-exc-edit-retry"))}</button>
                    ${g?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind" disabled>${escapeHtml(t("erp-exc-edit-bind-retry"))}</button>`:""}
                    ${w?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind-prod" disabled>${escapeHtml(t("erp-exc-edit-bind-prod-retry"))}</button>`:""}
                </div>
            </div>`,document.body.appendChild(q),q.addEventListener("click",H=>{H.target===q&&l()}),document.getElementById("erp-exc-m-close").addEventListener("click",l),document.getElementById("erp-exc-m-cancel").addEventListener("click",l),document.getElementById("erp-exc-m-retry").addEventListener("click",()=>{l(),r(u.id,null)}),g){let H="";const F=document.getElementById("erp-exc-m-bind"),A=document.getElementById("erp-exc-m-custlist"),y=document.getElementById("erp-exc-m-search"),v=(L,C)=>{const P=(C||"").trim().toLowerCase(),I=P?L.filter(j=>(j.code||"").toLowerCase().includes(P)||(j.name||"").toLowerCase().includes(P)):L;if(I.length===0){A.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-empty"))}</div>`;return}A.innerHTML=I.slice(0,100).map(j=>`<div class="erp-exc-m-cust" data-cust-code="${escapeHtml(j.code||"")}">
                        <span class="erp-exc-m-cust-name">${escapeHtml(j.name||"")}</span>
                        <span class="erp-exc-m-cust-code">${escapeHtml(j.code||"")}</span>
                    </div>`).join(""),A.querySelectorAll(".erp-exc-m-cust").forEach(j=>{j.addEventListener("click",()=>{H=j.dataset.custCode||"",A.querySelectorAll(".erp-exc-m-cust").forEach(Y=>Y.classList.remove("sel")),j.classList.add("sel"),F&&(F.disabled=!H)})})},b=async()=>{const L=u.endpoint_id;if(c[L]){v(c[L],"");return}try{const C=await fetch("/api/erp/endpoints/"+encodeURIComponent(L)+"/customers",{headers:{Authorization:"Bearer "+a()}}),P=await C.json().catch(()=>({}));if(!C.ok||!P.ok){A.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`;return}const I=P.customers||[];c[L]=I,v(I,"")}catch{A.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`}};y&&y.addEventListener("input",()=>v(c[u.endpoint_id]||[],y.value)),b(),F&&F.addEventListener("click",async()=>{if(H){F.disabled=!0,F.textContent=t("erp-exc-retrying");try{if(!(await fetch("/api/erp/mappings/clients",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({client_id:u.history_client_id,erp_type:u.endpoint_adapter,erp_code:H})})).ok){showToast(t("erp-exc-retry-fail"),"error"),F.disabled=!1,F.textContent=t("erp-exc-edit-bind-retry");return}showToast(t("erp-exc-edit-bound-ok"),"success"),l(),await r(u.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),F.disabled=!1,F.textContent=t("erp-exc-edit-bind-retry")}}})}if(w){const H=document.getElementById("erp-exc-m-bind-prod"),F=document.getElementById("erp-exc-m-prodlist"),A={};let y=[];const v=()=>'<option value="">'+escapeHtml(t("erp-exc-edit-prod-choose"))+"</option>"+y.slice(0,500).map(C=>`<option value="${escapeHtml(C.code||"")}" data-pname="${escapeHtml(C.name||"")}">`+escapeHtml((C.name||"")+" · "+(C.code||""))+"</option>").join(""),b=C=>{if(!C.length){F.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-noitems"))}</div>`;return}F.innerHTML=C.map(P=>`<div class="erp-exc-m-cust" style="cursor:default">
                        <span class="erp-exc-m-cust-name" title="${escapeHtml(P)}">${escapeHtml(P)}</span>
                        <select class="erp-exc-m-prod-sel" data-item="${escapeHtml(P)}" style="max-width:55%;flex:0 0 auto;padding:4px 6px;border:1px solid var(--border,#e5e7eb);border-radius:6px;font-size:12px">${v()}</select>
                    </div>`).join(""),F.querySelectorAll(".erp-exc-m-prod-sel").forEach(P=>{P.addEventListener("change",()=>{const I=P.dataset.item,j=P.options[P.selectedIndex];P.value?A[I]={code:P.value,name:j&&j.dataset.pname||""}:delete A[I],H&&(H.disabled=Object.keys(A).length===0)})})};(async()=>{try{const P=await(await fetch("/api/history/"+encodeURIComponent(u.history_id),{headers:{Authorization:"Bearer "+a()}})).json().catch(()=>({})),I=P&&P.pages||[],j=[],Y={};(Array.isArray(I)?I:[]).forEach(te=>{const re=te&&te.fields&&te.fields.items||[];(Array.isArray(re)?re:[]).forEach(T=>{const x=(T&&(T.name||T.description)||"").trim();x&&!Y[x]&&(Y[x]=1,j.push(x))})});const G=await fetch("/api/erp/endpoints/"+encodeURIComponent(u.endpoint_id)+"/products",{headers:{Authorization:"Bearer "+a()}}),W=await G.json().catch(()=>({}));if(!G.ok||!W.ok){F.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`;return}y=W.products||[],b(j)}catch{F.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`}})(),H&&H.addEventListener("click",async()=>{const C=Object.entries(A);if(C.length){H.disabled=!0,H.textContent=t("erp-exc-retrying");try{for(const[P,I]of C)if(!(await fetch("/api/erp/mappings/products",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({erp_type:u.endpoint_adapter,item_name:P,erp_code:I.code,erp_name:I.name})})).ok){showToast(t("erp-exc-retry-fail"),"error"),H.disabled=!1,H.textContent=t("erp-exc-edit-bind-prod-retry");return}showToast(t("erp-exc-edit-prod-bound-ok"),"success"),l(),await r(u.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),H.disabled=!1,H.textContent=t("erp-exc-edit-bind-prod-retry")}}})}},window._rerenderErpExceptions=p,window.loadErpExceptions=i,window._erpExcState=e})();(function(){function e(d){try{if(location.search.indexOf("test_center=1")>=0||localStorage.getItem("pearnly_test_mode")==="1"||d&&d.id&&String(d.id)==="468b50c1-5593-4fd6-990d-515ce8085563")return!0}catch{}return!1}window.applyRoleVisibility=function(){var u=window._userInfo,g=!1,w=!0,$=!1,E=!1;u&&(g=typeof canManageTeam=="function"?canManageTeam(u):!!(u.role==="owner"||u.is_super_admin),w=typeof shouldHideMoney=="function"?shouldHideMoney(u):u.role==="member"&&!u.is_super_admin,$=typeof isSuperAdmin=="function"?isSuperAdmin(u):!!u.is_super_admin,E=e(u)),document.querySelectorAll("[data-show-if-team]").forEach(function(B){B.style.display=g?"":"none"}),document.querySelectorAll("[data-show-if-money]").forEach(function(B){B.style.display=w?"none":""}),document.querySelectorAll("[data-show-if-admin]").forEach(function(B){B.style.display=$?"":"none"}),document.querySelectorAll("[data-show-if-test]").forEach(function(B){B.style.display=E?"":"none"});var _=$||E;document.querySelectorAll("[data-show-if-special]").forEach(function(B){B.style.display=_?"":"none"})},window.renderAvatarMenu=function(u){if(u){var g=document.getElementById("avatar-btn"),w=document.getElementById("avatar-popup-name"),$=document.getElementById("avatar-popup-email");if(!(!g||!w||!$)){var E=(u.username||"").trim(),_=E.split("@")[0]||E||"—",B=(E.charAt(0)||"?").toUpperCase(),q=(u.avatar_url||"").trim();if(q){var H=q.replace(/"/g,"&quot;"),F=B.replace(/'/g,"\\'");g.innerHTML='<img src="'+H+'" alt="'+B+`" referrerpolicy="no-referrer" onerror="this.parentNode.textContent='`+F+`'">`}else g.textContent=B;w.textContent=_,$.textContent=E||"—",g.setAttribute("title",E||"")}}};function n(){var d=document.getElementById("avatar-wrap"),u=document.getElementById("avatar-btn"),g=document.getElementById("avatar-popup");if(!d||!u||!g)return;function w(){g.classList.remove("show"),u.setAttribute("aria-expanded","false")}function $(){g.classList.add("show"),u.setAttribute("aria-expanded","true")}u.addEventListener("click",function(E){E.stopPropagation(),g.classList.contains("show")?w():$()}),document.addEventListener("click",function(E){g.classList.contains("show")&&!d.contains(E.target)&&w()}),g.addEventListener("click",function(E){var _=E.target.closest(".avatar-popup-item");if(_){var B=_.dataset.action;switch(w(),B){case"settings":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings");break;case"team":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("team")},50);break;case"billing":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("plan")},50);break;case"shortcuts":if(typeof showToast=="function"){var q=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(q||"即将上线","info")}break;case"admin":window.location.href="/admin/cost";break;case"test-center":typeof routeTo=="function"&&routeTo("test-center");break;case"help":var H=document.getElementById("help-modal");H&&(H.style.display="flex");break;case"logout":try{localStorage.removeItem("mrpilot_token")}catch{}try{localStorage.removeItem("mrpilot_user")}catch{}window.location.href="/";break}}}),window._closeAvatarPopup=w}function a(){return[].slice.call(document.querySelectorAll(".cmdk-item")).filter(function(d){return d.style.display!=="none"})}function o(d){var u=a();u.forEach(function(g){g.classList.remove("focus")}),u[d]&&(u[d].classList.add("focus"),u[d].scrollIntoView({block:"nearest"}))}function s(d){var u=a();if(u.length){var g=u.findIndex(function($){return $.classList.contains("focus")});g<0&&(g=0);var w=(g+d+u.length)%u.length;o(w)}}function p(d){d=(d||"").toLowerCase().trim();var u=0,g=window._userInfo,w=typeof isSuperAdmin=="function"?isSuperAdmin(g):!!(g&&g.is_super_admin),$=e(g);document.querySelectorAll(".cmdk-item").forEach(function(_){if(_.dataset.showIfAdmin==="1"&&!w){_.style.display="none";return}if(_.dataset.showIfTest==="1"&&!$){_.style.display="none";return}var B=(_.dataset.cmdkText||_.textContent||"").toLowerCase(),q=!d||B.indexOf(d)>=0;_.style.display=q?"":"none",_.classList.remove("focus"),q&&u++}),document.querySelectorAll("[data-cmdk-section]").forEach(function(_){for(var B=_.nextElementSibling,q=!1;B&&!B.hasAttribute("data-cmdk-section");){if(B.classList&&B.classList.contains("cmdk-item")&&B.style.display!=="none"){q=!0;break}B=B.nextElementSibling}_.style.display=q?"":"none"});var E=document.getElementById("cmdk-empty");E&&(E.style.display=u===0?"flex":"none"),o(0)}window.openCmdk=function(){var u=document.getElementById("cmdk-mask");u&&(typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup(),u.classList.add("show"),typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility(),setTimeout(function(){var g=document.getElementById("cmdk-input");g&&(g.value="",p(""),g.focus(),o(0))},50))},window.closeCmdk=function(){var u=document.getElementById("cmdk-mask");u&&u.classList.remove("show")};function r(d){if(d){if(d.classList.contains("cmdk-item-locked")){if(typeof showToast=="function"){var u=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(u||"即将上线","info")}return}var g=d.dataset.cmdkRoute,w=d.dataset.cmdkAction;if(window.closeCmdk(),g){typeof routeTo=="function"&&routeTo(g);return}if(w){if(w==="open-admin"){window.location.href="/admin/cost";return}if(w.indexOf("lang-")===0){var $=w.slice(5);typeof applyLang=="function"&&applyLang($)}}}}function f(){var d=document.getElementById("cmdk-mask"),u=document.getElementById("cmdk-input"),g=document.getElementById("cmdk-body");if(!(!d||!u||!g)){d.addEventListener("click",function(E){E.target===d&&window.closeCmdk()});var w=document.getElementById("cmdk-esc-btn");w&&w.addEventListener("click",function(){window.closeCmdk()}),u.addEventListener("input",function(E){p(E.target.value)}),u.addEventListener("keydown",function(E){E.key==="ArrowDown"?(E.preventDefault(),s(1)):E.key==="ArrowUp"?(E.preventDefault(),s(-1)):E.key==="Enter"?(E.preventDefault(),r(d.querySelector(".cmdk-item.focus"))):E.key==="Escape"&&(E.preventDefault(),window.closeCmdk())}),g.addEventListener("click",function(E){var _=E.target.closest(".cmdk-item");_&&r(_)}),g.addEventListener("mousemove",function(E){var _=E.target.closest(".cmdk-item");!_||_.style.display==="none"||_.classList.contains("cmdk-item-locked")||(a().forEach(function(B){B.classList.remove("focus")}),_.classList.add("focus"))});var $=document.getElementById("topbar-search");$&&($.addEventListener("click",function(){window.openCmdk()}),$.addEventListener("keydown",function(E){(E.key==="Enter"||E.key===" ")&&(E.preventDefault(),window.openCmdk())}))}}document.addEventListener("keydown",function(d){if((d.metaKey||d.ctrlKey)&&(d.key==="k"||d.key==="K")){d.preventDefault(),window.openCmdk();return}if(d.key==="Escape"){var u=document.getElementById("cmdk-mask");if(u&&u.classList.contains("show")){window.closeCmdk();return}var g=document.getElementById("avatar-popup");g&&g.classList.contains("show")&&typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup()}});try{var i=(navigator.userAgent||"").toLowerCase(),c=i.indexOf("mac")>=0||i.indexOf("iphone")>=0||i.indexOf("ipad")>=0;c||document.body.classList.add("is-windows")}catch{}function l(){n(),f(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("nav-ia-phase1-role",function(){try{typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",l):l()})();(function(){function n(w){return String(w??"").replace(/[&<>"']/g,function($){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[$]})}function a(w){if(!w||isNaN(w))return"";var $=Number(w);return $<1024?$+" B":$<1024*1024?($/1024).toFixed(1)+" KB":($/1024/1024).toFixed(1)+" MB"}document.addEventListener("click",function(w){var $=w.target.closest&&w.target.closest(".recon-collapse-head");if($&&!(w.target.closest("button")||w.target.closest("a"))){var E=$.closest(".recon-collapse");if(E){var _=E.getAttribute("data-collapsed")==="true";E.setAttribute("data-collapsed",_?"false":"true"),_&&(E.id==="vex-summary-collapse"&&l(),E.id==="vex-detail-collapse"&&d())}}}),document.addEventListener("keydown",function(w){if(!(w.key!=="Enter"&&w.key!==" ")){var $=w.target.closest&&w.target.closest(".recon-collapse-head");$&&(w.preventDefault(),$.click())}});var o={vat:"",gl:""};window._glvClearPreviewSearch=function(){o.vat="",o.gl=""};var s='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',p='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function r(){i("vat"),i("gl")}function f(w){try{if(typeof window._glvPreviewFiles=="function")return window._glvPreviewFiles(w)||[]}catch{}var $=document.getElementById(w==="vat"?"glv-vat-input":"glv-gl-input");return $&&$.files?Array.from($.files):[]}function i(w){var $=document.getElementById(w==="vat"?"glv-pp-vat-col":"glv-pp-gl-col");if($){var E=f(w),_=w==="vat"?"glv-up-vat-title":"glv-up-gl-title",B=w==="vat"?"① 销项税报告":"② 总账 GL",q=window.t&&window.t(_)||B,H=n(window.t&&window.t("vex-preview-search")||"搜索文件名..."),F=n(window.t&&window.t("vex-preview-clear-all")||"全清"),A=o[w]||"",y=E.length;$.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+n(q)+' <span class="vex-pp-col-count">'+y+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="glv-pp-search-'+w+'" type="text" placeholder="'+H+'" value="'+n(A)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="glv-pp-clearall-'+w+'" type="button">'+F+'</button></div><div class="vex-pp-file-list" id="glv-pp-'+w+'-list"></div><div class="vex-pp-pagination" id="glv-pp-'+w+'-pg"></div>';var v=document.getElementById("glv-pp-search-"+w);v&&v.addEventListener("input",function(L){o[w]=L.target.value,c(w)});var b=document.getElementById("glv-pp-clearall-"+w);b&&b.addEventListener("click",function(){window._glvRemoveFile&&window._glvRemoveFile(w)}),c(w)}}function c(w){var $=document.getElementById("glv-pp-"+w+"-list"),E=document.getElementById("glv-pp-"+w+"-pg");if($){var _=f(w),B=(o[w]||"").toLowerCase(),q=_.map(function(A,y){return{f:A,i:y}}),H=B?q.filter(function(A){return A.f.name.toLowerCase().indexOf(B)>=0}):q;if($.innerHTML=H.map(function(A){var y=A.f;return'<div class="vex-pp-file-row">'+s+'<span class="vex-pp-fi-name" title="'+n(y.name)+'">'+n(y.name)+'</span><span class="vex-pp-fi-size">'+a(y.size)+'</span><button class="vex-pp-fi-del" type="button" data-kind="'+w+'" data-idx="'+A.i+'" aria-label="remove">'+p+"</button></div>"}).join(""),$.querySelectorAll(".vex-pp-fi-del").forEach(function(A){A.addEventListener("click",function(){var y=A.dataset.kind,v=parseInt(A.dataset.idx,10);window._glvRemoveFile&&window._glvRemoveFile(y,isNaN(v)?null:v)})}),E){var F=window.t&&window.t("vex-preview-count")||"显示前 {n} / 共 {m}";E.textContent=F.replace("{n}",H.length).replace("{m}",H.length)}}}function l(){var w=function(E,_){var B=document.getElementById(E);B&&(B.textContent=_==null?"—":String(_))},$=window._vexLastTask||{};w("vex-sum-total",$.total),w("vex-sum-matched",$.matched),w("vex-sum-diff",$.diff),w("vex-sum-incomplete",$.incomplete),w("vex-sum-cash",$.cash),document.getElementById("vex-summary-sub")}function d(){var w=window._vexLastTask&&window._vexLastTask.diff_rows||[],$=document.getElementById("vex-detail-tbody"),E=document.getElementById("vex-detail-table"),_=document.getElementById("vex-detail-empty");if(!(!$||!E||!_)){if(w.length===0){E.style.display="none",_.style.display="";return}_.style.display="none",E.style.display="";var B=w.map(function(H){return'<tr><td class="recon-detail-cell-mono">'+n(H.invoice_no||"")+"</td><td>"+n(H.field||"")+"</td><td>"+n(H.report_value||"")+"</td><td>"+n(H.invoice_value||"")+"</td><td>"+n(H.kind||"")+"</td></tr>"}).join("");$.innerHTML=B;var q=document.getElementById("vex-detail-sub");q&&(q.textContent=String(w.length))}}function u(){var w=document.getElementById("glv-toggle-preview");w&&!w._reconBound&&(w._reconBound=!0,w.addEventListener("click",function(){var $=document.getElementById("glv-preview-panel"),E=document.getElementById("glv-toggle-preview-label"),_=$&&$.style.display!=="none";$&&($.style.display=_?"none":""),w.classList.toggle("open",!_),E&&(E.textContent=_?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),_||r()})),["glv-vat-input","glv-gl-input"].forEach(function($){var E=document.getElementById($);!E||E._reconWatched||(E._reconWatched=!0,E.addEventListener("change",function(){var _=document.getElementById("glv-preview-panel");_&&_.style.display!=="none"&&r()}))})}function g(){var w=document.getElementById("vex-summary-collapse"),$=document.getElementById("vex-detail-collapse");w&&(w.style.display=""),$&&($.style.display=""),l(),d()}window._fillVexSummary=l,window._fillVexDetail=d,window._onVexResultShown=g,document.addEventListener("DOMContentLoaded",function(){u()}),setTimeout(u,1500),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-collapse",function(){var w=document.getElementById("glv-preview-panel");w&&w.style.display!=="none"&&r();var $=document.getElementById("glv-toggle-preview-label"),E=document.getElementById("glv-toggle-preview");$&&E&&($.textContent=E.classList.contains("open")?window.t&&window.t("vex-toggle-preview-close")||"收起清单":window.t&&window.t("vex-toggle-preview-open")||"查看清单")}),window._reconCollapse={renderGlvPreview:r,fillVexSummary:l,fillVexDetail:d}})();(function(){function e(p){}function n(){const p=document.querySelectorAll("[data-recon-tab]");p.forEach(f=>{f.addEventListener("click",()=>{p.forEach(u=>u.classList.remove("active")),f.classList.add("active");const i=f.dataset.reconTab,c=document.getElementById("recon-pane-bank"),l=document.getElementById("recon-pane-sale-vat"),d=document.getElementById("recon-pane-gl-vat");c&&(c.style.display=i==="bank"?"":"none"),l&&(l.style.display=i==="sale-vat"?"":"none"),d&&(d.style.display=i==="gl-vat"?"":"none"),i==="gl-vat"&&window.GlVatRecon&&window.GlVatRecon.ensureInit(),i==="bank"&&typeof window._bankReconV2Init=="function"&&window._bankReconV2Init()})});const r=document.querySelector("[data-recon-tab].active");r&&(r.dataset.reconTab,void 0)}function a(){const p=document.getElementById("page-settings");if(!p)return null;let r=document.getElementById("settings-modal-overlay");if(r)return r;r=document.createElement("div"),r.id="settings-modal-overlay",r.className="settings-modal-overlay",r.style.display="none",p.parentElement.insertBefore(r,p),r.appendChild(p);const f=document.createElement("button");return f.id="settings-modal-close",f.className="settings-modal-close",f.setAttribute("aria-label","close"),f.innerHTML='<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 5l10 10M15 5L5 15"/></svg>',p.insertBefore(f,p.firstChild),f.addEventListener("click",s),r.addEventListener("click",i=>{i.target===r&&s()}),r}function o(){const p=a();if(!p)return;p.style.display="flex",document.body.classList.add("settings-modal-open");const r=document.getElementById("page-settings");r&&(r.style.display="block"),setTimeout(()=>{try{typeof renderSettings=="function"&&renderSettings()}catch(i){console.warn("renderSettings:",i)}let f=document.querySelector(".settings-tab.active")||document.querySelector('.settings-tab[data-tab="profile"]');f&&f.click()},50)}function s(){const p=document.getElementById("settings-modal-overlay");p&&(p.style.display="none"),document.body.classList.remove("settings-modal-open")}window.openSettingsModal=o,window.closeSettingsModal=s,document.addEventListener("keydown",p=>{if(p.key==="Escape"){const r=document.getElementById("settings-modal-overlay");r&&r.style.display==="flex"&&s()}}),window.addEventListener("hashchange",()=>{location.hash==="#/settings"&&o()}),window.addEventListener("DOMContentLoaded",()=>{location.hash==="#/settings"&&o()}),document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){const a=/\.(pdf|jpe?g|png|webp|tiff?|xlsx?|xlsm|csv|tsv|docx?)$/i,o=V=>document.getElementById(V);function s(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}function p(V){return String(V??"").replace(/[&<>"']/g,Z=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[Z])}function r(V){return V<1024?V+" B":V<1024*1024?(V/1024).toFixed(1)+" KB":(V/1024/1024).toFixed(1)+" MB"}let f=[],i=[],c=!1,l=[],d=50,u=50,g="",w="";async function $(){try{const V=await fetch("/api/vat_excel/tasks?page=1&page_size=1",{headers:s()});if(!V.ok)return;const ee=(await V.json()).kpi||{};[["vex-kpi-month-val",ee.this_month],["vex-kpi-running-val",ee.running],["vex-kpi-done-val",ee.done],["vex-kpi-failed-val",ee.failed]].forEach(([ne,oe])=>{const ue=document.getElementById(ne);ue&&(ue.textContent=oe??0)})}catch{}}async function E(){try{const V=await fetch("/api/vat_excel/tasks?page=1&page_size=100",{headers:s()});if(!V.ok)return;const Z=await V.json();H(Z.rows||[])}catch{}}const _=10;var B=1;function q(){var V=((document.getElementById("vex-task-search")||{}).value||"").trim().toLowerCase();if(B=1,H(l),!!V){var Z=document.getElementById("vex-task-tbody");Z&&Z.querySelectorAll("tr").forEach(function(ee){ee.dataset.taskId&&(ee.style.display=ee.textContent.toLowerCase().indexOf(V)>=0?"":"none")})}}function H(V){l=V||l;const Z=document.getElementById("vex-task-tbody");if(!Z)return;if(!l.length){Z.innerHTML='<tr><td colspan="9" class="vex-task-empty">'+(t("sv-empty-title")||"还没有对账任务")+"</td></tr>",F(0);return}const ee=Math.ceil(l.length/_);B>ee&&(B=ee);const ne=(B-1)*_;A(l.slice(ne,ne+_)),F(l.length)}function F(V){const Z=document.getElementById("vex-task-pager"),ee=document.getElementById("vex-task-pager-info"),ne=document.getElementById("vex-task-prev"),oe=document.getElementById("vex-task-next");if(!Z)return;if(V<=_){Z.style.display="none";return}Z.style.display="";const ue=Math.ceil(V/_);ee&&(ee.textContent=B+" / "+ue),ne&&(ne.disabled=B<=1),oe&&(oe.disabled=B>=ue)}function A(V){const Z=document.getElementById("vex-task-tbody");if(!Z)return;const ee={pending:t("vex-status-pending")||"待处理",running:t("vex-status-running")||"处理中",done:t("vex-status-done")||"已完成",failed:t("vex-status-failed")||"失败"},ne={pending:"badge-gray",running:"badge-blue",done:"badge-green",failed:"badge-red"},oe='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',ue='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h10M6 4V3h4v1M5 4v8a1 1 0 001 1h4a1 1 0 001-1V4"/></svg>';Z.innerHTML=V.map(k=>{const S=k.created_at?new Date(k.created_at).toLocaleString([],{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}):"—",M=k.period||"—",U=k.matched_count!=null?k.matched_count+" ✓ · "+k.mismatched_count+" ⚠":"—",z=k.mismatch_amount!=null?"฿ "+Number(k.mismatch_amount).toLocaleString():"—",m=k.elapsed_seconds!=null?k.elapsed_seconds.toFixed(1)+" s":"—",R=k.status||"pending",O=k.client_name&&k.client_name!=="client"?k.client_name:t("vex-client-all")||"全部客户";return`<tr class="vex-task-row" data-task-id="${p(k.id)}" style="cursor:pointer">
                <td>${S}</td>
                <td>${p(O)}</td>
                <td>${p(M)}</td>
                <td>${(k.invoice_count||0)+" / "+(k.report_count||0)}</td>
                <td>${U}</td>
                <td>${z}</td>
                <td><span class="badge ${ne[R]||"badge-gray"}">${ee[R]||R}</span></td>
                <td>${m}</td>
                <td><div class="vex-task-actions">
                    <button class="vex-task-dl-btn" data-task-id="${p(k.id)}" title="${t("hist_export")||"导出"}">${oe}</button>
                    <button class="vex-task-del-btn" data-task-id="${p(k.id)}" title="${t("vex-task-delete-confirm-title")||"删除"}">${ue}</button>
                </div></td>
            </tr>`}).join(""),Z.querySelectorAll(".vex-task-dl-btn").forEach(k=>{k.addEventListener("click",async S=>{S.stopPropagation();const M=k.dataset.taskId;try{const U=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(M)+"/download",{credentials:"include",headers:s()});if(U.status===410){showToast(t("vex-toast-expired")||"数据已过期 · 请重新对账","warn");return}if(!U.ok){showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error");return}const z=await U.blob(),R=(U.headers.get("Content-Disposition")||"").match(/filename\*?=(?:UTF-8''|")?([^";]+)/i),O=R?decodeURIComponent(R[1]):"vat_recon_"+M+".xlsx",J=URL.createObjectURL(z),X=document.createElement("a");X.href=J,X.download=O,X.click(),setTimeout(()=>URL.revokeObjectURL(J),1e3)}catch{showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error")}})}),Z.querySelectorAll(".vex-task-del-btn").forEach(k=>{k.addEventListener("click",S=>{S.stopPropagation(),v(k.dataset.taskId)})}),q()}function y(){var V=document.getElementById("vex-task-prev"),Z=document.getElementById("vex-task-next");V&&!V._vexBound&&(V._vexBound=!0,V.addEventListener("click",function(){B>1&&(B--,H())})),Z&&!Z._vexBound&&(Z._vexBound=!0,Z.addEventListener("click",function(){var ee=Math.ceil(l.length/_);B<ee&&(B++,H())}))}async function v(V){const Z=t("vex-task-delete-confirm-title")||"删除对账任务?",ee=t("vex-task-delete-confirm-body")||"同时清掉对应的发票识别缓存 · 不可恢复";if(await showConfirm(ee,{title:Z,danger:!0,okText:t("vex-task-delete-confirm-title")||"确认删除"}))try{const oe=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(V),{method:"DELETE",credentials:"include",headers:s()});if(!oe.ok)throw new Error(oe.status);showToast(t("vex-task-delete-ok")||"已删除","success"),E(),$()}catch{showToast(t("vex-task-delete-fail")||"删除失败","error")}}function b(V){const Z=window._currentLang||"th",ee={zh:`已忽略 ${V} 个不支持的文件 · 仅支持 PDF / 图片 / Excel / CSV / Word`,th:`ข้ามไฟล์ที่ไม่รองรับ ${V} ไฟล์ · รองรับเฉพาะ PDF / รูปภาพ / Excel / CSV / Word`,en:`Ignored ${V} unsupported file(s) · only PDF / image / Excel / CSV / Word are supported`,ja:`非対応ファイル ${V} 件をスキップ · 対応形式は PDF / 画像 / Excel / CSV / Word のみ`};showToast(ee[Z]||ee.th,"warn")}function L(V){const Z=new Set(f.map(ne=>ne.name+"|"+ne.size));let ee=0;for(const ne of V){if(!a.test(ne.name)){ee++;continue}const oe=ne.name+"|"+ne.size;if(!Z.has(oe)&&(Z.add(oe),f.push(ne),f.length>=1e3))break}ee>0&&b(ee),f.length>1e3&&(f=f.slice(0,1e3),showToast(t("vex-toast-cap-inv"),"warn")),j()}function C(V){const Z=new Set(i.map(ne=>ne.name+"|"+ne.size));let ee=0;for(const ne of V){if(!a.test(ne.name)){ee++;continue}const oe=ne.name+"|"+ne.size;if(!Z.has(oe)&&(Z.add(oe),i.push(ne),i.length>=30))break}ee>0&&b(ee),i.length>30&&(i=i.slice(0,30),showToast(t("vex-toast-cap-rep"),"warn")),j()}function P(V){f.splice(V,1),j()}function I(V){i.splice(V,1),j()}function j(){const V=o("vex-list-invoice"),Z=o("vex-list-report"),ee=o("vex-count-invoice"),ne=o("vex-count-report");ee&&(ee.textContent=f.length),ne&&(ne.textContent=i.length);const oe=(S,M,U)=>`<div class="vex-fi">
            <svg class="vex-fi-ic" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2h6l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M10 2v4h4"/></svg>
            <span class="vex-fi-n" title="${p(S.name)}">${p(S.name)}</span>
            <span class="vex-fi-s">${r(S.size)}</span>
            <button class="vex-fi-x" type="button" data-vex-kind="${U}" data-vex-idx="${M}" aria-label="remove">×</button>
        </div>`;V&&(V.innerHTML=f.map((S,M)=>oe(S,M,"inv")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),Z&&(Z.innerHTML=i.map((S,M)=>oe(S,M,"rep")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),document.querySelectorAll(".vex-fi-x").forEach(S=>{S.addEventListener("click",M=>{const U=S.dataset.vexKind,z=parseInt(S.dataset.vexIdx,10);U==="inv"?P(z):I(z)})});const ue=f.length>0&&i.length>0;o("vex-build").disabled=!ue||c;const k=o("vex-action-info");k&&(!f.length||!i.length?(k.textContent=t("vex-need-both")||"需要至少 1 张发票 + 1 份 VAT 报告",k.className="vex-action-info muted"):(k.textContent=(t("vex-ready")||"已就绪 · {a} 张发票 · {b} 份报告").replace("{a}",f.length).replace("{b}",i.length),k.className="vex-action-info ok")),te()}const Y='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>',G='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',W='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function te(){const V=o("vex-preview-panel");if(!V||V.style.display==="none")return;re("inv"),re("rep");const Z=o("vex-pp-guide");Z&&(Z.style.display=f.length>100?"flex":"none")}function re(V){const Z=o(V==="inv"?"vex-pp-invoice-col":"vex-pp-report-col");if(!Z)return;const ee=V==="inv"?f:i,ne=V==="inv"?g:w,oe=t(V==="inv"?"vex-preview-invoice":"vex-preview-report")||(V==="inv"?"销售发票":"VAT 报告"),ue=p(t("vex-preview-search")||"搜索文件名..."),k=p(t("vex-preview-clear-all")||"全清");Z.innerHTML=`
            <div class="vex-pp-col-title">
                <span class="vex-pp-col-name">${p(oe)} <span class="vex-pp-col-count">${ee.length}</span></span>
            </div>
            <div class="vex-pp-search-row">
                <input class="vex-pp-search" id="vex-pp-search-${V}" type="text"
                       placeholder="${ue}" value="${p(ne)}" autocomplete="off">
                <button class="vex-pp-clear-btn" id="vex-pp-clearall-${V}" type="button">${k}</button>
            </div>
            <div class="vex-pp-file-list" id="vex-pp-${V}-list"></div>
            <div class="vex-pp-pagination" id="vex-pp-${V}-pg"></div>`;const S=o("vex-pp-search-"+V);S&&S.addEventListener("input",U=>{V==="inv"?(g=U.target.value,d=50):(w=U.target.value,u=50),T(V)});const M=o("vex-pp-clearall-"+V);M&&M.addEventListener("click",()=>{V==="inv"?(f=[],g="",d=50):(i=[],w="",u=50),j()}),T(V)}function T(V){const Z=o("vex-pp-"+V+"-list"),ee=o("vex-pp-"+V+"-pg");if(!Z)return;const ne=V==="inv"?f:i,oe=V==="inv"?g:w,ue=V==="inv"?d:u,k=V==="inv"?Y:G,S=ne.map((z,m)=>({f:z,i:m})),M=oe?S.filter(({f:z})=>z.name.toLowerCase().includes(oe.toLowerCase())):S,U=M.slice(0,ue);if(Z.innerHTML=U.map(({f:z,i:m})=>`
            <div class="vex-pp-file-row">
                ${k}
                <span class="vex-pp-fi-name" title="${p(z.name)}">${p(z.name)}</span>
                <span class="vex-pp-fi-size">${r(z.size)}</span>
                <button class="vex-pp-fi-del" type="button" data-kind="${V}" data-ridx="${m}" aria-label="remove">${W}</button>
            </div>`).join("")+`<div id="vex-pp-sentinel-${V}" style="height:1px;flex-shrink:0"></div>`,Z.querySelectorAll(".vex-pp-fi-del").forEach(z=>{z.addEventListener("click",()=>{const m=parseInt(z.dataset.ridx,10);z.dataset.kind==="inv"?P(m):I(m)})}),ee){const z=t("vex-preview-count")||"显示前 {n} / 共 {m}";ee.textContent=z.replace("{n}",U.length).replace("{m}",M.length)}x(V,M.length)}function x(V,Z){if((V==="inv"?d:u)>=Z)return;const ne=o("vex-pp-sentinel-"+V),oe=o("vex-pp-"+V+"-list");if(!ne||!oe)return;const ue=new IntersectionObserver(k=>{k[0].isIntersecting&&(ue.disconnect(),V==="inv"?d+=50:u+=50,T(V))},{root:oe,threshold:.8});ue.observe(ne)}function h(V,Z,ee,ne){const oe=o(V),ue=o(Z);!oe||!ue||(oe.addEventListener("click",()=>ue.click()),oe.addEventListener("keydown",k=>{(k.key==="Enter"||k.key===" ")&&(k.preventDefault(),ue.click())}),oe.addEventListener("dragover",k=>{k.preventDefault(),oe.classList.add("drag-over")}),oe.addEventListener("dragleave",()=>oe.classList.remove("drag-over")),oe.addEventListener("drop",k=>{k.preventDefault(),oe.classList.remove("drag-over");const M=Array.from(k.dataTransfer.files).filter(U=>a.test(U.name));if(!M.length){showToast(t("vex-toast-bad-ext"),"error");return}ee(M)}),ue.addEventListener("change",()=>{const k=Array.from(ue.files);ee(k),ue.value=""}))}async function D(){if(c||!f.length||!i.length)return;c=!0,o("vex-build").disabled=!0,o("vex-progress").style.display="flex";var V=document.getElementById("vex-download");V&&(V.style.display="none"),["vex-summary-collapse","vex-detail-collapse"].forEach(function(oe){var ue=document.getElementById(oe);ue&&(ue.style.display="none")});const Z=Date.now();o("vex-progress-title").textContent=t("vex-progress-running")||"AI 抽取中",o("vex-progress-sub").textContent=(t("vex-progress-sub")||"{a} 张发票 + {b} 份报告 · 并行处理").replace("{a}",f.length).replace("{b}",i.length);const ee=setInterval(()=>{const oe=Math.floor((Date.now()-Z)/1e3);o("vex-progress-sub").textContent=(t("vex-progress-elapsed")||"已 {s} 秒 · {a} 张发票 + {b} 份报告").replace("{s}",oe).replace("{a}",f.length).replace("{b}",i.length)},1e3);try{const oe=new FormData;for(const pe of f)oe.append("invoices",pe);for(const pe of i)oe.append("reports",pe);const ue=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";oe.append("lang",ue);const k=localStorage.getItem("mrpilot_token")||"",S=await fetch("/api/vat_excel/submit",{method:"POST",headers:s(),body:oe});let M=null;try{M=await S.json()}catch{M=null}if(!S.ok||!M||!M.ok||!M.job_id)throw clearInterval(ee),new Error(M&&M.detail||"HTTP "+S.status);const U=o("vex-progress-sub"),z=await window._reconPollJob(M.job_id,k,{onProgress:pe=>{U&&(U.textContent=window._reconProgressText(pe,ue))}});if(clearInterval(ee),!z||z.status!=="done"||!z.result_id)throw new Error(t("vex-toast-fail")||"生成失败");const m=z.result_id;let R=0;const O=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(m)+"/download",{headers:s()});if(!O.ok)throw new Error("HTTP "+O.status);const X=(O.headers.get("Content-Disposition")||"").match(/filename="([^"]+)"/),de=X&&X[1]||"vat_recon_"+Date.now()+".xlsx",se=await O.blob(),ce=URL.createObjectURL(se),ae=o("vex-download");ae.href=ce,ae.download=de;try{const pe=document.createElement("a");pe.href=ce,pe.download=de,document.body.appendChild(pe),pe.click(),setTimeout(()=>pe.remove(),100)}catch{}o("vex-progress").style.display="none";var ne=document.getElementById("vex-download");ne&&(ne.style.display=""),m&&(R=await Q(m)),window._onVexResultShown&&window._onVexResultShown(),R>0?showToast((t("vex-toast-some-fail")||"有 {n} 张发票 OCR 失败").replace("{n}",R),"warn"):showToast(t("vex-toast-done")||"Excel 已生成","success"),$(),setTimeout(E,800)}catch(oe){clearInterval(ee),o("vex-progress").style.display="none";const ue=(t("vex-toast-fail")||"生成失败")+": "+(oe.message||oe);showToast(ue,"error")}finally{c=!1,o("vex-build").disabled=!1}}function N(){f=[],i=[];var V=document.getElementById("vex-download");V&&(V.style.display="none"),j()}function K(V){if(V==null)return"—";var Z=parseFloat(V);return isNaN(Z)?"—":Z.toLocaleString("th-TH",{minimumFractionDigits:2,maximumFractionDigits:2})}async function Q(V){try{var Z=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(V),{headers:s()});if(!Z.ok)throw new Error(Z.status);var ee=await Z.json(),ne=ee.raw_data_json;if(typeof ne=="string")try{ne=JSON.parse(ne)}catch{ne={}}ne=ne||{};var oe=ne.rows||[],ue=[];oe.forEach(function(M){M.kind==="invoice_orphan"?ue.push({invoice_no:M.invoice_no||"",field:"仅发票有",report_value:"—",invoice_value:K(M.amount_inv),kind:M.kind}):M.kind==="report_orphan"?ue.push({invoice_no:M.invoice_no||"",field:"仅报告有",report_value:K(M.amount_rep),invoice_value:"—",kind:M.kind}):M.dims&&Object.keys(M.dims).length>0&&Object.keys(M.dims).forEach(function(U){var z=String(M.dims[U]||""),m=z.split(" ≠ ");ue.push({invoice_no:M.invoice_no||"",field:U,report_value:m[0]||z,invoice_value:m.length>1?m[1]:"—",kind:"diff"})})});var k=oe.filter(function(M){return M.kind==="matched_cash"}).length,S=Math.max(0,parseInt(ne.invoice_ocr_failed_count||0,10));return window._vexLastTask={total:ne.n_total||0,matched:ne.n_ok||0,diff:ne.n_diff||0,incomplete:S,cash:k,diff_rows:ue,task_id:V},window._fillVexSummary&&window._fillVexSummary(),window._fillVexDetail&&window._fillVexDetail(),S}catch{return 0}}function le(){const V=document.getElementById("vex-pane");V&&V.querySelectorAll("[data-i18n]").forEach(Z=>{const ee=t(Z.dataset.i18n);ee&&(Z.textContent=ee)}),j(),E()}function ie(){h("vex-drop-invoice","vex-input-invoice",L),h("vex-drop-report","vex-input-report",C);const V=o("vex-build"),Z=o("vex-reset");V&&V.addEventListener("click",D),Z&&Z.addEventListener("click",N),document.querySelectorAll('[data-recon-tab="sale-vat"]').forEach(oe=>{oe.addEventListener("click",()=>{$(),E()})}),y();const ee=document.getElementById("vex-task-search");ee&&ee.addEventListener("input",q);const ne=document.getElementById("vex-toggle-preview");ne&&ne.addEventListener("click",()=>{const oe=o("vex-preview-panel"),ue=o("vex-toggle-preview-label"),k=oe&&oe.style.display!=="none";oe&&(oe.style.display=k?"none":""),ne&&ne.classList.toggle("open",!k),ue&&(ue.textContent=k?t("vex-toggle-preview-open")||"查看清单":t("vex-toggle-preview-close")||"收起清单"),k||te()}),j(),$()}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",ie):ie(),typeof window.subscribeI18n=="function"&&(window.subscribeI18n("vex-excel",le),window.subscribeI18n("vex-preview-panel",te))})();(function(){const e=x=>document.getElementById(x),n=()=>localStorage.getItem("mrpilot_token")||"",a=()=>typeof window.currentLang=="string"&&window.currentLang?window.currentLang:localStorage.getItem("mrpilot_lang")||"th",o=()=>({Authorization:"Bearer "+n()}),s={inited:!1,glFile:[],vatFile:[],running:!1,currentTaskId:null,lastDetail:[],lastSummary:null},p={th:{not_found:"ไม่พบข้อมูล",running:"กำลังกระทบยอด…",error:"เกิดข้อผิดพลาด",need_files:"กรุณาเลือกไฟล์ทั้งสอง",done:"เสร็จสิ้น",hint_need_both:"อัปโหลด ① รายงานภาษีขาย + ② GL",hint_need_one_more:"อัปโหลดอีก 1 ไฟล์",hint_ready:"พร้อมแล้ว · กดเริ่มกระทบยอด",hist_load:"โหลด",hist_export:"ส่งออก",hist_delete:"ลบ",confirm_delete:"ยืนยันการลบงานนี้?",s_gl_total:"ยอดรวมตามบัญชีแยกประเภท",s_minus_gl_cr:"หัก : รายการเครดิตที่ไม่มีในรายงานภาษีขาย",s_plus_gl_dr:"บวก : รายการเดบิตที่ไม่มีในรายงานภาษีขาย",s_plus_vat_p:"บวก : รายการยอดขายที่ไม่มีในบัญชีแยกประเภท",s_minus_vat_n:"หัก : รายการลดหนี้ที่ไม่มีในบัญชีแยกประเภท",s_vat_total:"ยอดรวมตามรายงานภาษีขาย"},zh:{not_found:"未找到数据",running:"正在对账中...",error:"出错了",need_files:"请先选择两个文件",done:"完成",hint_need_both:"请上传① 销项税报告 + ② 总账 GL",hint_need_one_more:"还需上传 1 份文件",hint_ready:"已就绪 · 点击开始对账",hist_load:"加载",hist_export:"导出",hist_delete:"删除",confirm_delete:"确认删除此任务？",s_gl_total:"总账金额合计",s_minus_gl_cr:"减：销项税报告中未列的贷方记录",s_plus_gl_dr:"加：销项税报告中未列的借方记录",s_plus_vat_p:"加：总账中未列的销售记录",s_minus_vat_n:"减：总账中未列的贷项凭单(credit note)记录",s_vat_total:"销项税报告金额合计"},en:{not_found:"Not found",running:"Reconciling...",error:"Error",need_files:"Please select both files",done:"Done",hint_need_both:"Upload ① Output VAT report + ② GL file",hint_need_one_more:"1 more file required",hint_ready:"Ready · click Run to start",hist_load:"Load",hist_export:"Export",hist_delete:"Delete",confirm_delete:"Delete this task?",s_gl_total:"Total per General Ledger",s_minus_gl_cr:"Less: GL credits not in VAT Report",s_plus_gl_dr:"Add: GL debits not in VAT Report",s_plus_vat_p:"Add: Sales in VAT Report not in GL",s_minus_vat_n:"Less: Credit notes in VAT Report not in GL",s_vat_total:"Total per VAT Sales Report"},ja:{not_found:"データなし",running:"照合中…",error:"エラー",need_files:"両方のファイルを選択してください",done:"完了",hint_need_both:"① 売上税報告 + ② GL をアップロード",hint_need_one_more:"あと 1 ファイル必要",hint_ready:"準備完了 · 「開始」をクリック",hist_load:"読込",hist_export:"出力",hist_delete:"削除",confirm_delete:"このタスクを削除しますか?",s_gl_total:"総勘定元帳合計",s_minus_gl_cr:"減：売上税報告にないGL貸方記録",s_plus_gl_dr:"加：売上税報告にないGL借方記録",s_plus_vat_p:"加：GLにない売上記録",s_minus_vat_n:"減：GLにない赤伝記録",s_vat_total:"売上税報告合計"}},r=x=>(p[a()]||p.th)[x]||x;function f(x){const h=a(),N={gl_no_revenue_rows:{zh:"GL 中未找到收入科目行。请确认「收入科目前缀」是否正确(收入科目通常以 4 开头),改对后重试。",th:"ไม่พบรายการบัญชีรายได้ใน GL · ตรวจสอบ «คำนำหน้าบัญชีรายได้» (รายได้มักขึ้นต้นด้วย 4) แล้วลองใหม่",en:"No revenue-account rows found in the GL. Check the “revenue account prefix” (revenue usually starts with 4) and retry.",ja:"GL に収益科目の行が見つかりません。「収益科目プレフィックス」(通常 4 で始まる)を確認して再試行してください。"},gl_parse_failed:{zh:"GL 文件解析失败。请确认文件含日期/科目/借贷列,或换清晰的 Excel/CSV 重传。",th:"อ่านไฟล์ GL ไม่สำเร็จ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต-เครดิต หรืออัปโหลด Excel/CSV ที่ชัดเจน",en:"Failed to parse the GL file. Ensure it has date/account/debit-credit columns, or re-upload a clean Excel/CSV.",ja:"GL ファイルの解析に失敗しました。日付/科目/借方貸方列を確認するか、Excel/CSV を再アップロードしてください。"},vat_no_rows:{zh:"销项税报告里没有可对账的数据行。请确认上传了正确的销项税报告。",th:"ไม่พบแถวข้อมูลในรายงานภาษีขาย · ตรวจสอบว่าอัปโหลดรายงานที่ถูกต้อง",en:"No rows found in the sales-VAT report. Please check you uploaded the correct report.",ja:"売上VATレポートに行が見つかりません。正しいレポートをアップロードしたか確認してください。"},vat_parse_failed:{zh:"销项税报告解析失败。请换更清晰的版本,或转成 Excel/PDF 重传。",th:"อ่านรายงานภาษีขายไม่สำเร็จ · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น Excel/PDF",en:"Failed to parse the sales-VAT report. Try a clearer version, or convert to Excel/PDF.",ja:"売上VATレポートの解析に失敗しました。より鮮明な版か、Excel/PDF に変換してください。"}}[x];return N?N[h]||N.th||N.en:r("error")||"Error"}const i=x=>x==null||isNaN(x)?"":Number(x).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});function c(x,h,D,N){const K=e(x),Q=e(h),le=e(D);if(!K||!Q||!le)return;const ie=V=>{if(!V||!V.length)return;const Z=Array.isArray(s[N])?s[N].slice():[],ee=new Set(Z.map(ne=>ne.name+"|"+ne.size));for(const ne of V){if(!ne)continue;const oe=ne.name+"|"+ne.size;ee.has(oe)||(Z.push(ne),ee.add(oe))}s[N]=Z,l(le,Z),u(),g(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()};K.addEventListener("click",()=>Q.click()),K.addEventListener("keydown",V=>{(V.key==="Enter"||V.key===" ")&&(V.preventDefault(),Q.click())}),Q.addEventListener("change",()=>{ie(Array.from(Q.files||[])),Q.value=""}),K.addEventListener("dragover",V=>{V.preventDefault(),K.classList.add("drag-over")}),K.addEventListener("dragleave",()=>K.classList.remove("drag-over")),K.addEventListener("drop",V=>{V.preventDefault(),K.classList.remove("drag-over");const Z=V.dataTransfer&&V.dataTransfer.files?Array.from(V.dataTransfer.files):[];ie(Z)})}function l(x,h){if(!x)return;if(!h||h.length===0){x.textContent="";return}const D=h.reduce((N,K)=>N+Math.round(K.size/1024),0);if(h.length===1)x.textContent=h[0].name+"  ("+D+" KB)";else{const N=window.t&&window.t("glv-files-count")||"{n} 个文件";x.textContent=N.replace("{n}",h.length)+"  ("+D+" KB)"}}function d(x){const h=s[x];return Array.isArray(h)?h:h?[h]:[]}function u(){const x=e("btn-glv-run");if(!x)return;const h=d("glFile").length>0&&d("vatFile").length>0;x.disabled=!h||s.running}function g(){const x=e("glv-status");if(!x||s.running)return;const h=d("vatFile").length,D=d("glFile").length;h===0&&D===0?(x.className="vex-action-info muted",x.innerHTML="<span>"+r("hint_need_both")+"</span>"):h>0&&D>0?(x.className="vex-action-info ok",x.innerHTML="<span>"+r("hint_ready")+"</span>"):(x.className="vex-action-info muted",x.innerHTML="<span>"+r("hint_need_one_more")+"</span>")}function w(x,h){const D=x==="vat"?"vatFile":"glFile",N=x==="vat"?"glv-vat-input":"glv-gl-input",K=x==="vat"?"glv-vat-name":"glv-gl-name",Q=d(D);h==null?s[D]=[]:s[D]=Q.filter((ie,V)=>V!==h);const le=e(N);le&&(le.value=""),l(e(K),d(D)),u(),g(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}window._glvRemoveFile=w;function $(){s.glFile=[],s.vatFile=[],s.currentTaskId=null,s.lastDetail=[],s.lastSummary=null;const x=e("glv-vat-input");x&&(x.value="");const h=e("glv-gl-input");h&&(h.value="");const D=e("glv-vat-name");D&&(D.textContent="");const N=e("glv-gl-name");N&&(N.textContent="");const K=e("glv-result");K&&(K.style.display="none");const Q=e("glv-kpi-strip");Q&&(Q.style.display="none"),u(),g(),window._glvClearPreviewSearch&&window._glvClearPreviewSearch(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}function E(x){const h=e("glv-tbody");if(!h)return;re(x.length),h.innerHTML="";const D=r("not_found"),N=document.createDocumentFragment();x.forEach(K=>{const Q=document.createElement("tr"),le=(ne,oe)=>{const ue=document.createElement("td");return oe&&(ue.className=oe),ue.textContent=ne,ue},ie=K.gl_amount===null||K.gl_amount===void 0,V=K.diff;let Z="glv-num",ee="glv-num";ie?(ee+=" glv-cell-missing",Z+=" glv-cell-missing"):Math.abs(V||0)<.005?Z+=" glv-cell-ok":Z+=" glv-cell-diff",Q.appendChild(le(K.doc_no||"","glv-doc")),Q.appendChild(le(K.date||"","")),Q.appendChild(le(K.customer_name||"","")),Q.appendChild(le(i(K.vat_amount),"glv-num")),Q.appendChild(le(ie?D:i(K.gl_amount),ee)),Q.appendChild(le(ie?D:i(K.diff),Z)),Q.appendChild(le(K.account_codes||"","glv-doc")),N.appendChild(Q)}),h.appendChild(N)}function _(x){const h=e("glv-summary-table")&&e("glv-summary-table").querySelector("tbody");if(!h)return;h.innerHTML="",[{label:r("s_gl_total"),amount:x.gl_total,emph:!0,items:[],negate:!1},{label:r("s_minus_gl_cr"),amount:-(x.gl_only_credit||0),emph:!1,items:x.gl_only_credit_items||[],negate:!0},{label:r("s_plus_gl_dr"),amount:x.gl_only_debit||0,emph:!1,items:x.gl_only_debit_items||[],negate:!1},{label:r("s_plus_vat_p"),amount:x.vat_only_positive||0,emph:!1,items:x.vat_only_positive_items||[],negate:!1},{label:r("s_minus_vat_n"),amount:x.vat_only_negative||0,emph:!1,items:x.vat_only_negative_items||[],negate:!1},{label:r("s_vat_total"),amount:x.vat_total,emph:!0,items:[],negate:!1}].forEach(({label:N,amount:K,emph:Q,items:le,negate:ie})=>{const V=document.createElement("tr");V.className=Q?"glv-summary-total":"glv-summary-sect";const Z=document.createElement("td"),ee=document.createElement("td");Z.textContent=N,ee.textContent=Q?i(K):"",V.appendChild(Z),V.appendChild(ee),h.appendChild(V),(le||[]).forEach(ne=>{const oe=document.createElement("tr");oe.className="glv-summary-item";const ue=document.createElement("td"),k=document.createElement("td"),S=[ne.doc_no,ne.date,ne.name].filter(Boolean);ue.textContent="· "+S.join("  ·  ");const M=ie?-(ne.amount||0):ne.amount||0;k.textContent=i(M),oe.appendChild(ue),oe.appendChild(k),h.appendChild(oe)})})}function B(x){e("glv-kpi-matched")&&(e("glv-kpi-matched").textContent=x&&x.matched!=null?x.matched:"—"),e("glv-kpi-diff")&&(e("glv-kpi-diff").textContent=x&&x.diff!=null?x.diff:"—"),e("glv-kpi-unmatched")&&(e("glv-kpi-unmatched").textContent=x&&x.unmatched!=null?x.unmatched:"—")}function q(x){if(!x)return"";try{const h=new Date(x);if(isNaN(h.getTime()))return x;const D=N=>String(N).padStart(2,"0");return h.getFullYear()+"-"+D(h.getMonth()+1)+"-"+D(h.getDate())+" "+D(h.getHours())+":"+D(h.getMinutes())}catch{return x}}const H=10;var F=[],A=1;function y(){A=1,v();var x=((e("glv-hist-search")||{}).value||"").trim().toLowerCase();if(x){var h=e("glv-history-tbody");h&&h.querySelectorAll("tr").forEach(function(D){D.dataset.taskId&&(D.style.display=D.textContent.toLowerCase().indexOf(x)>=0?"":"none")})}}function v(){const x=e("glv-history-table-wrap"),h=e("glv-history-empty"),D=e("glv-history-tbody"),N=e("glv-history-pager"),K=e("glv-history-pager-info"),Q=e("glv-history-prev"),le=e("glv-history-next");if(!D)return;if(D.innerHTML="",!F.length){x&&(x.style.display="none"),h&&(h.style.display=""),N&&(N.style.display="none");return}x&&(x.style.display=""),h&&(h.style.display="none");const ie=Math.ceil(F.length/H);A>ie&&(A=ie);const V=(A-1)*H,Z=F.slice(V,V+H);N&&(N.style.display=F.length>H?"":"none",K&&(K.textContent=A+" / "+ie),Q&&(Q.disabled=A<=1),le&&(le.disabled=A>=ie)),Z.forEach(ne=>{const oe=document.createElement("tr");oe.dataset.taskId=ne.id;const ue=document.createElement("td");ue.textContent=q(ne.created_at);const k=document.createElement("td");k.className="glv-history-file",k.title=(ne.vat_filename||"")+" + "+(ne.gl_filename||""),k.textContent=(ne.vat_filename||"?")+" + "+(ne.gl_filename||"?");const S=document.createElement("td");S.className="glv-num",S.textContent=(ne.vat_row_count||0)+" / "+(ne.gl_row_count||0);const M=document.createElement("td");M.className="glv-num",M.textContent=ne.matched_count||0;const U=document.createElement("td");U.className="glv-num",U.textContent=ne.diff_count||0;const z=document.createElement("td");z.className="glv-num",z.textContent=ne.unmatched_count||0;const m=document.createElement("td");m.className="glv-history-actions";const R=(de,se,ce,ae)=>{const pe=document.createElement("button");return pe.type="button",ce&&(pe.className=ce),pe.title=se,pe.setAttribute("aria-label",se),pe.innerHTML=de,pe.onclick=ae,pe},O='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 8a6 6 0 1 0 12 0A6 6 0 0 0 2 8z"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',J='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',X='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';m.appendChild(R(O,r("hist_load"),"",()=>C(ne.id))),m.appendChild(R(J,r("hist_export"),"",()=>P(ne.id))),m.appendChild(R(X,r("hist_delete"),"glv-del",()=>I(ne.id))),[ue,k,S,M,U,z,m].forEach(de=>oe.appendChild(de)),D.appendChild(oe)})}function b(){var x=e("glv-history-prev"),h=e("glv-history-next");x&&!x._glvBound&&(x._glvBound=!0,x.addEventListener("click",function(){A>1&&(A--,v())})),h&&!h._glvBound&&(h._glvBound=!0,h.addEventListener("click",function(){var D=Math.ceil(F.length/H);A<D&&(A++,v())}))}async function L(){try{const h=await(await fetch("/api/recon/gl-vat/tasks",{headers:o()})).json();F=h&&h.tasks||[],A=1,v(),b()}catch(x){console.error("[gl-vat] history load failed:",x)}}async function C(x){try{const D=await(await fetch("/api/recon/gl-vat/"+x,{headers:o()})).json();if(!D||!D.ok)throw new Error("load_failed");s.currentTaskId=x,s.lastDetail=D.detail||[],s.lastSummary=D.summary||{},B(D.stats||{}),E(s.lastDetail),_(s.lastSummary);const N=e("glv-result");N&&(N.style.display=""),W(),window.scrollTo({top:N?N.offsetTop-80:0,behavior:"smooth"})}catch(h){console.error("[gl-vat] load task failed:",h),alert(r("error")+": "+(h.message||h))}}async function P(x){try{const h="/api/recon/gl-vat/"+x+"/export?lang="+encodeURIComponent(a()),D=await fetch(h,{headers:o()});if(!D.ok)throw new Error("HTTP "+D.status);const N=await D.blob(),K=document.createElement("a");K.href=URL.createObjectURL(N),K.download="GL_VAT_recon_"+x+".xlsx",document.body.appendChild(K),K.click(),setTimeout(()=>{URL.revokeObjectURL(K.href),K.remove()},200)}catch(h){console.error("[gl-vat] exportTask failed:",h),typeof showToast=="function"&&showToast(r("error")+": "+(h.message||h),"error")}}async function I(x){let h;if(typeof window.showConfirm=="function"?h=await window.showConfirm(r("confirm_delete"),{danger:!0}):h=confirm(r("confirm_delete")),!!h)try{const D=await fetch("/api/recon/gl-vat/"+x,{method:"DELETE",headers:o()});if(!D.ok)throw new Error("HTTP "+D.status);L()}catch(D){console.error("[gl-vat] delete failed:",D),typeof showToast=="function"&&showToast(r("error")+": "+(D.message||D),"error")}}async function j(){if(!s.glFile||!s.vatFile){typeof showToast=="function"&&showToast(r("need_files"),"warn");return}s.running=!0,u();const x=e("glv-status"),h=e("glv-progress"),D=e("glv-progress-sub");x&&(x.className="vex-action-info muted",x.style.color="",x.innerHTML="<span>"+r("running")+"</span>"),h&&(h.style.display=""),D&&(D.textContent=(s.vatFile.name||"VAT")+" + "+(s.glFile.name||"GL"));const N=new FormData,K=d("vatFile"),Q=d("glFile");for(const ie of K)N.append("vat_files",ie,ie.name);for(const ie of Q)N.append("gl_files",ie,ie.name);const le=(e("glv-prefix")&&e("glv-prefix").value||"4").trim()||"4";N.append("revenue_prefix",le),N.append("lang",a());try{const ie=await fetch("/api/recon/gl-vat/submit",{method:"POST",headers:o(),body:N});let V=null;try{V=await ie.json()}catch{V=null}if(!ie.ok||!V||!V.ok||!V.job_id)throw new Error(V&&V.detail||V&&V.error||"HTTP "+ie.status);const Z=e("glv-progress-sub"),ee=await window._reconPollJob(V.job_id,n(),{onProgress:k=>{Z&&(Z.textContent=window._reconProgressText(k,a()))}});if(!ee||ee.status!=="done"||!ee.result_id)throw ee&&ee.status==="failed"&&ee.error_code?new Error(f(ee.error_code)):new Error(r("error")||"Error");const ne=await fetch("/api/recon/gl-vat/"+encodeURIComponent(ee.result_id),{headers:o()});let oe=null;try{oe=await ne.json()}catch{oe=null}if(!ne.ok||!oe||!oe.ok)throw new Error(oe&&oe.detail||oe&&oe.error||"HTTP "+ne.status);s.currentTaskId=oe.task_id,s.lastDetail=oe.detail||[],s.lastSummary=oe.summary||{},B(oe.stats||{}),E(s.lastDetail),_(s.lastSummary);const ue=e("glv-result");ue&&(ue.style.display=""),W(),x&&(x.className="vex-action-info ok",x.style.color="",x.innerHTML="<span>"+r("done")+" · GL "+(oe.gl_row_count||0)+" · VAT "+(oe.vat_row_count||0)+"</span>"),L()}catch(ie){console.error("[gl-vat] run failed:",ie),x&&(x.className="vex-action-info",x.style.color="#ef4444",x.innerHTML="<span>"+r("error")+": "+(ie.message||ie)+"</span>")}finally{s.running=!1,h&&(h.style.display="none"),u()}}async function Y(){if(s.currentTaskId)try{const x="/api/recon/gl-vat/"+s.currentTaskId+"/export?lang="+encodeURIComponent(a()),h=await fetch(x,{headers:o()});if(!h.ok)throw new Error("HTTP "+h.status);const D=await h.blob(),N=document.createElement("a");N.href=URL.createObjectURL(D),N.download="GL_VAT_recon_"+s.currentTaskId+".xlsx",document.body.appendChild(N),N.click(),setTimeout(()=>{URL.revokeObjectURL(N.href),N.remove()},200)}catch(x){console.error("[gl-vat] export failed:",x),typeof showToast=="function"&&showToast(r("error")+": "+(x.message||x),"error")}}function G(){s.running||g(),L(),s.lastDetail&&s.lastDetail.length&&E(s.lastDetail),s.lastSummary&&_(s.lastSummary)}function W(){var x=e("glv-kpi-strip");x&&(x.style.display="");var h=e("glv-section-summary");h&&h.setAttribute("data-collapsed","false");var D=e("glv-section-detail");D&&D.setAttribute("data-collapsed","false")}function te(){document.querySelectorAll(".glv-section-head[data-toggle]").forEach(x=>{const h=x.getAttribute("data-toggle"),D=document.getElementById(h);if(!D)return;const N=K=>{if(K.target&&K.target.closest("button")!==null&&!K.target.classList.contains("glv-section-head"))return;const Q=D.getAttribute("data-collapsed")==="true";D.setAttribute("data-collapsed",Q?"false":"true")};x.addEventListener("click",N),x.addEventListener("keydown",K=>{(K.key==="Enter"||K.key===" ")&&(K.preventDefault(),N(K))})})}function re(x){const h=e("glv-detail-count");h&&(h.textContent=x!=null?String(x):"")}function T(){if(s.inited){L();return}s.inited=!0,c("glv-drop-gl","glv-gl-input","glv-gl-name","glFile"),c("glv-drop-vat","glv-vat-input","glv-vat-name","vatFile");const x=e("btn-glv-run");x&&x.addEventListener("click",j);const h=e("btn-glv-export");h&&h.addEventListener("click",Y);const D=e("btn-glv-reset");D&&D.addEventListener("click",$);const N=e("glv-hist-search");N&&N.addEventListener("input",y),te(),B(null),g(),window._loadGlvHistory=L,L(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("gl-vat-recon",G)}window.GlVatRecon={ensureInit:T},window._glvPreviewFiles=function(x){return d(x==="vat"?"vatFile":"glFile")}})();(function(){const e=["flowaccount","peak","xero","quickbooks","express"],n={flowaccount:"FlowAccount",peak:"PEAK",xero:"Xero",quickbooks:"QuickBooks",express:"Express"},a=["expense_office","expense_travel","expense_utility","asset_inventory","asset_fixed","liability_ap","revenue_sales","revenue_service","other"],o=["vat_7","vat_0","vat_exempt","wht_1","wht_3","wht_5","non_vat"],s="468b50c1-5593-4fd6-990d-515ce8085563";let p={sub:"clients",loaded:{clients:!1,accounts:!1,taxes:!1,products:!1},items:{clients:[],accounts:[],taxes:[],products:[]},clientList:[],clientLoaded:!1,addingNew:{clients:!1,accounts:!1,taxes:!1,products:!1},bound:!1};function r(){const C=typeof _userInfo<"u"?_userInfo:null;return!!(C&&(C.role==="owner"||C.is_super_admin))}function f(){const C=typeof _userInfo<"u"?_userInfo:null;return!!(C&&C.id===s)}function i(C){return typeof escapeHtml=="function"?escapeHtml(C==null?"":String(C)):String(C??"")}function c(C,P){try{typeof showToast=="function"&&showToast(C,P||"info")}catch{}}async function l(C,P){const I=localStorage.getItem("mrpilot_token");if(I&&!(p.loaded[C]&&!P))try{const j=await fetch("/api/erp/mappings/"+C,{headers:{Authorization:"Bearer "+I}});if(!j.ok)throw new Error("http_"+j.status);const Y=await j.json();p.items[C]=Y.items||[],p.loaded[C]=!0}catch{p.items[C]=[],p.loaded[C]=!1}}async function d(C){if(p.clientLoaded)return;const P=localStorage.getItem("mrpilot_token");if(P)try{const I=await fetch("/api/clients?include_inactive=false",{headers:{Authorization:"Bearer "+P}});if(!I.ok)throw new Error("http_"+I.status);const j=await I.json();p.clientList=(j.clients||j.items||[]).filter(Y=>Y.is_active!==!1),p.clientLoaded=!0}catch{p.clientList=[]}}function u(){const C=document.getElementById("erp-map-pane-wrap");if(!C)return;const P=!r();let I="";P&&(I+='<div class="erp-map-readonly-banner"><svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="8"/><path d="M10 6v4M10 13v0.01"/></svg>'+i(t("erp-map-readonly-tip"))+"</div>"),I+='<div class="erp-map-toolbar">',!P&&p.sub!=="products"&&(I+='<button class="btn btn-primary" type="button" id="erp-map-add-btn" data-i18n="erp-map-add-row">'+i(t("erp-map-add-row"))+"</button>"),I+="</div>",I+='<div class="erp-map-table" id="erp-map-table-host"></div>',C.innerHTML=I,g();const j=document.getElementById("erp-map-dev-bar");j&&(j.style.display=r()&&f()?"":"none")}function g(){const C=document.getElementById("erp-map-table-host");if(!C)return;const P=p.sub,I=p.items[P]||[],j=p.addingNew[P],Y=!r();if(!I.length&&!j){C.innerHTML='<div class="erp-map-empty"><strong>'+i(t("erp-map-empty-"+P))+"</strong>"+i(t("erp-map-empty-"+P+"-sub"))+"</div>";return}let G="";G+=w(P),j&&!Y&&(G+=q(P)),I.forEach(function(W){G+=H(P,W,Y)}),C.innerHTML=G}function w(C){return C==="clients"?'<div class="erp-map-row erp-map-head row-clients"><div>'+i(t("erp-map-col-client"))+"</div><div>"+i(t("erp-map-col-erp"))+"</div><div>"+i(t("erp-map-col-erp-code"))+"</div><div>"+i(t("erp-map-col-notes"))+"</div><div>"+i(t("erp-map-col-actions"))+"</div></div>":C==="accounts"?'<div class="erp-map-row erp-map-head row-accounts"><div>'+i(t("erp-map-col-erp"))+"</div><div>"+i(t("erp-map-col-category"))+"</div><div>"+i(t("erp-map-col-erp-code"))+"</div><div>"+i(t("erp-map-col-erp-name"))+"</div><div>"+i(t("erp-map-col-notes"))+"</div><div>"+i(t("erp-map-col-actions"))+"</div></div>":C==="products"?'<div class="erp-map-row erp-map-head row-products"><div>'+i(t("erp-map-col-item-name"))+"</div><div>"+i(t("erp-map-col-erp-product-code"))+"</div><div>"+i(t("erp-map-col-erp-name"))+"</div><div>"+i(t("erp-map-col-notes"))+"</div><div>"+i(t("erp-map-col-actions"))+"</div></div>":'<div class="erp-map-row erp-map-head row-taxes"><div>'+i(t("erp-map-col-erp"))+"</div><div>"+i(t("erp-map-col-tax"))+"</div><div>"+i(t("erp-map-col-erp-tax-code"))+"</div><div>"+i(t("erp-map-col-notes"))+"</div><div>"+i(t("erp-map-col-actions"))+"</div></div>"}function $(C,P){let I='<select class="form-input" data-erp-field="'+P+'">';return I+='<option value="">'+i(t("erp-map-pick-erp"))+"</option>",e.forEach(function(j){const Y=j===C?" selected":"";I+='<option value="'+j+'"'+Y+">"+i(n[j])+"</option>"}),I+="</select>",I}function E(C){let P='<select class="form-input" data-erp-field="client_id">';return P+='<option value="">'+i(t("erp-map-pick-client"))+"</option>",(p.clientList||[]).forEach(function(I){const j=String(I.id)===String(C)?" selected":"";P+='<option value="'+I.id+'"'+j+">"+i(I.name||"#"+I.id)+"</option>"}),P+="</select>",P}function _(C){let P='<select class="form-input" data-erp-field="pearnly_category">';return P+='<option value="">'+i(t("erp-map-pick-cat"))+"</option>",a.forEach(function(I){const j=I===C?" selected":"";P+='<option value="'+I+'"'+j+">"+i(t("erp-map-cat-"+I))+"</option>"}),P+="</select>",P}function B(C){let P='<select class="form-input" data-erp-field="pearnly_tax_kind">';return P+='<option value="">'+i(t("erp-map-pick-tax"))+"</option>",o.forEach(function(I){const j=I===C?" selected":"";P+='<option value="'+I+'"'+j+">"+i(t("erp-map-tax-"+I))+"</option>"}),P+="</select>",P}function q(C){const P='<button class="btn btn-primary" type="button" data-erp-save="new" style="padding:6px 12px;height:32px;">'+i(t("erp-map-save"))+"</button>";return C==="clients"?'<div class="erp-map-row erp-map-row-add row-clients" data-erp-row="new"><div data-label="'+i(t("erp-map-col-client"))+'">'+E("")+'</div><div data-label="'+i(t("erp-map-col-erp"))+'">'+$("","erp_type")+'</div><div data-label="'+i(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+i(t("erp-map-ph-erp-code"))+'"></div><div data-label="'+i(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+i(t("erp-map-ph-notes"))+'"></div><div>'+P+"</div></div>":C==="accounts"?'<div class="erp-map-row erp-map-row-add row-accounts" data-erp-row="new"><div data-label="'+i(t("erp-map-col-erp"))+'">'+$("","erp_type")+'</div><div data-label="'+i(t("erp-map-col-category"))+'">'+_("")+'</div><div data-label="'+i(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+i(t("erp-map-ph-acc-code"))+'"></div><div data-label="'+i(t("erp-map-col-erp-name"))+'"><input type="text" class="form-input" data-erp-field="erp_name" placeholder="'+i(t("erp-map-ph-acc-name"))+'"></div><div data-label="'+i(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+i(t("erp-map-ph-notes"))+'"></div><div>'+P+"</div></div>":'<div class="erp-map-row erp-map-row-add row-taxes" data-erp-row="new"><div data-label="'+i(t("erp-map-col-erp"))+'">'+$("","erp_type")+'</div><div data-label="'+i(t("erp-map-col-tax"))+'">'+B("")+'</div><div data-label="'+i(t("erp-map-col-erp-tax-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+i(t("erp-map-ph-tax-code"))+'"></div><div data-label="'+i(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+i(t("erp-map-ph-notes"))+'"></div><div>'+P+"</div></div>"}function H(C,P,I){const j=I?"":'<button class="erp-map-del-btn" type="button" data-erp-del="'+i(P.id)+'" title="'+i(t("erp-map-delete"))+'"><svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h12M8 6V4h4v2M6 6l1 11h6l1-11"/></svg></button>',Y='<span class="erp-map-erp-badge">'+i(n[P.erp_type]||P.erp_type)+"</span>";if(C==="clients")return'<div class="erp-map-row row-clients"><div data-label="'+i(t("erp-map-col-client"))+'" class="erp-map-cell-name">'+i(P.client_name||"#"+P.client_id)+'</div><div data-label="'+i(t("erp-map-col-erp"))+'">'+Y+'</div><div data-label="'+i(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+i(P.erp_code||"")+'</div><div data-label="'+i(t("erp-map-col-notes"))+'">'+i(P.notes||"")+"</div><div>"+j+"</div></div>";if(C==="accounts"){const W=t("erp-map-cat-"+(P.pearnly_category||"other"))||P.pearnly_category;return'<div class="erp-map-row row-accounts"><div data-label="'+i(t("erp-map-col-erp"))+'">'+Y+'</div><div data-label="'+i(t("erp-map-col-category"))+'" class="erp-map-cell-name">'+i(W)+'</div><div data-label="'+i(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+i(P.erp_code||"")+'</div><div data-label="'+i(t("erp-map-col-erp-name"))+'">'+i(P.erp_name||"")+'</div><div data-label="'+i(t("erp-map-col-notes"))+'">'+i(P.notes||"")+"</div><div>"+j+"</div></div>"}if(C==="products")return'<div class="erp-map-row row-products"><div data-label="'+i(t("erp-map-col-item-name"))+'" class="erp-map-cell-name">'+i(P.item_name||"")+'</div><div data-label="'+i(t("erp-map-col-erp-product-code"))+'" class="erp-map-code">'+i(P.erp_code||"")+'</div><div data-label="'+i(t("erp-map-col-erp-name"))+'">'+i(P.erp_name||"")+'</div><div data-label="'+i(t("erp-map-col-notes"))+'">'+i(P.notes||"")+"</div><div>"+j+"</div></div>";const G=t("erp-map-tax-"+(P.pearnly_tax_kind||""))||P.pearnly_tax_kind;return'<div class="erp-map-row row-taxes"><div data-label="'+i(t("erp-map-col-erp"))+'">'+Y+'</div><div data-label="'+i(t("erp-map-col-tax"))+'" class="erp-map-cell-name"><span class="erp-map-tax-badge">'+i(G)+'</span></div><div data-label="'+i(t("erp-map-col-erp-tax-code"))+'" class="erp-map-code">'+i(P.erp_code||"")+'</div><div data-label="'+i(t("erp-map-col-notes"))+'">'+i(P.notes||"")+"</div><div>"+j+"</div></div>"}async function F(C){const P=p.sub,I={};C.querySelectorAll("[data-erp-field]").forEach(function(W){I[W.dataset.erpField]=(W.value||"").trim()});const j=localStorage.getItem("mrpilot_token");if(!j)return;let Y={},G="/api/erp/mappings/"+P;if(P==="clients"){if(!I.client_id||!I.erp_type||!I.erp_code){c(t("erp-map-save-fail"),"error");return}Y={client_id:parseInt(I.client_id,10),erp_type:I.erp_type,erp_code:I.erp_code,notes:I.notes||""}}else if(P==="accounts"){if(!I.erp_type||!I.pearnly_category||!I.erp_code){c(t("erp-map-save-fail"),"error");return}Y={erp_type:I.erp_type,pearnly_category:I.pearnly_category,erp_code:I.erp_code,erp_name:I.erp_name||"",notes:I.notes||""}}else{if(!I.erp_type||!I.pearnly_tax_kind||!I.erp_code){c(t("erp-map-save-fail"),"error");return}Y={erp_type:I.erp_type,pearnly_tax_kind:I.pearnly_tax_kind,erp_code:I.erp_code,notes:I.notes||""}}try{const W=await fetch(G,{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+j},body:JSON.stringify(Y)});if(!W.ok)throw new Error("http_"+W.status);p.addingNew[P]=!1,await l(P,!0),g(),c(t("erp-map-saved-toast"),"success")}catch{c(t("erp-map-save-fail"),"error")}}async function A(C){if(!await window.pearnlyConfirm(t("erp-map-confirm-delete")))return;const I=p.sub,j=localStorage.getItem("mrpilot_token");try{const Y=await fetch("/api/erp/mappings/"+I+"/"+encodeURIComponent(C),{method:"DELETE",headers:{Authorization:"Bearer "+j}});if(!Y.ok)throw new Error("http_"+Y.status);await l(I,!0),g(),c(t("erp-map-deleted-toast"),"success")}catch{c(t("erp-map-delete-fail"),"error")}}async function y(){await d(),await l(p.sub,!1),u()}function v(C){C!==p.sub&&(p.sub=C,p.addingNew[C]=!1,["clients","accounts","taxes","products"].forEach(function(P){P!==C&&(p.addingNew[P]=!1)}),document.querySelectorAll(".erp-map-subtab").forEach(function(P){P.classList.toggle("active",P.dataset.erpSubtab===C)}),l(C,!1).then(function(){u()}))}function b(){p.bound||(p.bound=!0,document.addEventListener("click",function(C){const P=C.target.closest(".erp-subtab[data-erp-subtab]");if(P){C.preventDefault();const W=P.dataset.erpSubtab;document.querySelectorAll(".erp-subtab").forEach(function(te){te.classList.toggle("active",te.dataset.erpSubtab===W)}),document.querySelectorAll(".erp-subpanel").forEach(function(te){te.classList.toggle("active",te.dataset.erpSubpanel===W)}),W==="mappings"&&setTimeout(y,50);return}const I=C.target.closest(".erp-map-subtab[data-erp-subtab]");if(I){C.preventDefault(),v(I.dataset.erpSubtab);return}if(C.target.closest("#erp-map-add-btn")){if(C.preventDefault(),!r())return;p.addingNew[p.sub]=!0,g();return}const Y=C.target.closest('[data-erp-save="new"]');if(Y){C.preventDefault();const W=Y.closest('[data-erp-row="new"]');W&&F(W);return}const G=C.target.closest("[data-erp-del]");if(G){C.preventDefault(),A(G.dataset.erpDel);return}}))}function L(){const C=document.getElementById("erp-map-pane-wrap");C&&C.children.length>0&&u(),document.querySelectorAll(".erp-map-subtab").forEach(function(P){const I="erp-map-subtab-"+P.dataset.erpSubtab,j=t(I);j&&j!==I&&(P.textContent=j)})}b(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-mappings",L)})();(function(){let e=null,n=0,a=!1;function o(y){return typeof escapeHtml=="function"?escapeHtml(y==null?"":String(y)):String(y??"")}function s(y,v){try{typeof showToast=="function"&&showToast(y,v||"info")}catch{}}async function p(y){const v=Date.now();if(e&&v-n<3e4)return e;const b=localStorage.getItem("mrpilot_token");if(!b)return[];try{const L=await fetch("/api/erp/connectors/status",{headers:{Authorization:"Bearer "+b}});if(!L.ok)return[];const C=await L.json();return e=C&&C.connectors||[],n=v,e}catch{return[]}}function r(){try{return localStorage.getItem("pn_push_default_connector")||""}catch{return""}}function f(y){try{localStorage.setItem("pn_push_default_connector",y||"")}catch{}}function i(y){if(!y||!y.length)return null;const v=r();if(v){const L=y.find(C=>C.id===v);if(L)return L}const b=y.find(L=>L.is_default);return b||y[0]}function c(y){if(!y)return!1;const v=String(y.status||"").toLowerCase();return v==="exception"||v==="exception_pending"||v==="rejected"}function l(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function d(y){const v=y&&(y.type||y.id);return v==="xero"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5.5 8l2 2 3-3.5"/></svg>':v==="webhook"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="11.5" r="1.8"/><circle cx="11" cy="4.5" r="1.8"/><path d="M6.4 10l3.2-4M5 9.6V5.5a3 3 0 016 0"/></svg>':'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/><rect x="11" y="3" width="3" height="10" rx="1"/></svg>'}async function u(y,v){if(!y||!v)return!1;const b=document.getElementById("btn-push-default");b&&(b.disabled=!0,b.classList.add("loading"));const L=localStorage.getItem("mrpilot_token");try{let C,P={method:"POST",headers:{Authorization:"Bearer "+L}};y.type==="xero"?C="/api/erp/xero/push/"+encodeURIComponent(v):(C="/api/erp/push",P.headers["Content-Type"]="application/json",P.body=JSON.stringify({history_id:v,endpoint_id:y.endpoint_id||void 0}));const I=await fetch(C,P);let j={};try{j=await I.json()}catch{}if(!I.ok){let Y=j&&j.detail||"unknown";typeof Y=="object"&&(Y=Y.code||JSON.stringify(Y));let G=String(Y||"unknown");if(y.type==="xero"){const W=G.replace(/^xero\./,"").toLowerCase(),te=t("xero-"+W);te&&te!=="xero-"+W&&(G=te)}return s(t("unified-push-fail").replace("{name}",y.name).replace("{err}",G),"error"),!1}if(j&&j.ok===!1){let Y=j.error_msg||j.error_code||"unknown";return Y=String(Y).slice(0,200),s(t("unified-push-fail").replace("{name}",y.name).replace("{err}",Y),"error"),!1}return s(t("unified-push-ok").replace("{name}",y.name),"success"),!0}catch(C){return s(t("unified-push-fail").replace("{name}",y.name).replace("{err}",C.message||"network"),"error"),!1}finally{b&&(b.disabled=!1,b.classList.remove("loading"))}}async function g(y,v){for(const b of y)await u(b,v)}function w(y,v){const b=document.createElement("div");b.className="pn-push-dropdown",b.id="pn-push-dropdown";const L=(y||[]).map(P=>{const I=!!(v&&P.id===v.id),j=P.method==="download"?t("unified-push-tag-download"):I?t("unified-push-tag-default"):"";return'<div class="pn-pd-item" data-cid="'+o(P.id)+'"><span class="pn-pd-icon">'+d(P)+'</span><span class="pn-pd-name">'+o(P.name)+"</span>"+(j?'<span class="pn-pd-tag">'+o(j)+"</span>":"")+(I?'<span class="pn-pd-check">✓</span>':"")+"</div>"}).join(""),C=y&&y.length>1?'<div class="pn-pd-divider"></div><div class="pn-pd-item pn-pd-all" data-cid="__all__"><span class="pn-pd-icon"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h10M3 10h10M3 13.5h6"/></svg></span><span class="pn-pd-name">'+o(t("unified-push-all").replace("{n}",y.length))+"</span></div>":"";return b.innerHTML=L+C,b}function $(){const y=document.getElementById("pn-push-dropdown");y&&y.remove()}async function E(){if(document.getElementById("pn-push-dropdown")){$();return}const y=await p()||[],v=i(y),b=w(y,v),L=document.getElementById("pn-push-wrap");L&&L.appendChild(b)}async function _(){const y=await p()||[],v=i(y);if(!v)return;const b=l(),L=b&&(b._historyId||b.history_id);if(L){if(c(b)){s(t("unified-push-disabled-exc"),"warn");return}await u(v,L)}}async function B(y){$();const v=await p()||[],b=l(),L=b&&(b._historyId||b.history_id);if(!L)return;if(c(b)){s(t("unified-push-disabled-exc"),"warn");return}if(y==="__all__"){await g(v,L);return}const C=v.find(P=>P.id===y);C&&(f(y),await u(C,L),H())}async function q(){const y=document.getElementById("drawer-history-save");if(!y||y.querySelector("#pn-push-wrap"))return;const v=document.createElement("div");v.id="pn-push-wrap",v.className="pn-push-wrap",v.dataset.loading="1",y.insertBefore(v,y.firstChild),["btn-push-erp","btn-xero-push"].forEach(j=>{y.querySelectorAll("#"+j).forEach(Y=>{Y.style.display="none"})});const b=await p()||[],L=i(b),C=b.length>0;if(!C)v.innerHTML='<button type="button" class="btn btn-ghost pn-push-empty" id="btn-push-default" disabled title="'+o(t("unified-push-empty-tip"))+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/></svg><span style="margin-left:4px;">'+o(t("unified-push-empty"))+"</span></button>";else{const j=b.length>1;v.innerHTML='<div class="pn-push-split"><button type="button" class="pn-push-main" id="btn-push-default" title="'+o(t("unified-push-tip"))+'">'+d(L)+"<span>"+o(t("unified-push-to").replace("{name}",L?L.name:""))+"</span></button>"+(j?'<button type="button" class="pn-push-arrow" id="btn-push-arrow" title="'+o(t("unified-push-other"))+'"><svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5l3 3 3-3"/></svg></button>':"")+"</div>"}delete v.dataset.loading;const P=v.querySelector("#btn-push-default");P&&C&&P.addEventListener("click",_);const I=v.querySelector("#btn-push-arrow");I&&I.addEventListener("click",function(j){j.stopPropagation(),E()}),a||(a=!0,document.addEventListener("click",function(j){const Y=j.target.closest(".pn-pd-item");if(Y){const G=Y.getAttribute("data-cid");B(G);return}j.target.closest("#btn-push-arrow")||$()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("unified-push",H))}function H(){const y=document.getElementById("pn-push-wrap");y&&(y.remove(),e=null,n=0,q())}function F(){const y=document.getElementById("drawer-history-save");if(!y||!y.querySelector("#pn-push-wrap"))return;["btn-push-erp","btn-xero-push"].forEach(b=>{y.querySelectorAll("#"+b).forEach(L=>{L.style.display!=="none"&&(L.style.display="none")})});const v=y.querySelectorAll("#pn-push-wrap");if(v.length>1)for(let b=1;b<v.length;b++)v[b].remove()}function A(){try{const y=function(){return document.getElementById("drawer-body")},v=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&q(),F()}),b=y();if(b)v.observe(b,{childList:!0,subtree:!0});else{const L=new MutationObserver(function(){const C=y();C&&(v.observe(C,{childList:!0,subtree:!0}),L.disconnect())});L.observe(document.body,{childList:!0,subtree:!0})}setTimeout(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&q(),F()},200)}catch{}}A()})();(function(){function e(){const a=document.getElementById("erp-map-show-advanced-btn");if(!a)return;const o=document.getElementById("erp-map-subtabs");if(!o)return;const s=o.classList.contains("show-advanced"),p=a.querySelector(".erp-map-adv-btn-label");if(p&&typeof t=="function"){const r=s?"erp-map-hide-advanced":"erp-map-show-advanced",f=t(r);f&&f!==r&&(p.textContent=f)}a.setAttribute("aria-pressed",s?"true":"false")}document.addEventListener("click",function(a){if(!a.target.closest("#erp-map-show-advanced-btn"))return;a.preventDefault();const s=document.getElementById("erp-map-subtabs");if(s&&(s.classList.toggle("show-advanced"),e(),!s.classList.contains("show-advanced")&&s.querySelector(".erp-map-subtab.active.erp-map-subtab-advanced"))){const r=s.querySelector('.erp-map-subtab[data-erp-subtab="clients"]');r&&r.click()}});function n(){e()}typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-map-advanced-toggle",n)})();(function(){const e="pearnly_erp_onboard_shown";let n=!1;function a(){try{return Array.isArray(window._erpEndpoints)&&window._erpEndpoints.length>0}catch{return!1}}function o(){if(document.getElementById("erp-onboard-mask"))return;const p=document.createElement("div");p.id="erp-onboard-mask",p.className="erp-onboard-mask",p.innerHTML='<div class="erp-onboard-modal" role="dialog" aria-modal="true"><div class="erp-onboard-icon"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="6" width="24" height="20" rx="3"/><path d="M9 13h14M9 18h10"/><path d="M22 22l3 3 5-5"/></svg></div><div class="erp-onboard-title" id="erp-onboard-title"></div><div class="erp-onboard-body" id="erp-onboard-body"></div><div class="erp-onboard-btns"><button type="button" class="btn btn-secondary" id="erp-onboard-later"></button><button type="button" class="btn btn-primary" id="erp-onboard-ok"></button></div></div>',document.body.appendChild(p);function r(){const i=document.getElementById("erp-onboard-title"),c=document.getElementById("erp-onboard-body"),l=document.getElementById("erp-onboard-ok"),d=document.getElementById("erp-onboard-later");i&&(i.textContent=t("erp-onboard-title")),c&&(c.textContent=t("erp-onboard-body")),l&&(l.textContent=t("erp-onboard-ok")),d&&(d.textContent=t("erp-onboard-later"))}r();function f(){p.style.display="none"}document.getElementById("erp-onboard-ok").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}f();try{const i=document.querySelector('#btn-add-endpoint, [data-action="erp-add-endpoint"]');i&&i.scrollIntoView({behavior:"smooth",block:"center"})}catch{}}),document.getElementById("erp-onboard-later").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}f()}),p.addEventListener("click",function(i){i.target===p&&f()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-onboard-modal",function(){p.style.display!=="none"&&r()})}function s(){if(!n){try{if(localStorage.getItem(e)==="1")return}catch{}a()||(n=!0,o(),requestAnimationFrame(function(){requestAnimationFrame(function(){if(a())return;const p=document.getElementById("erp-onboard-mask");p&&(p.style.display="flex")})}))}}document.addEventListener("click",function(p){const r=p.target.closest('.auto-nav-item[data-auto-tab="erp"]'),f=p.target.closest('.erp-subtab[data-erp-subtab="connect"]');(r||f)&&setTimeout(s,700)})})();(function(){const e={parse:{zh:"解析文件中",th:"กำลังอ่านไฟล์",en:"Parsing files",ja:"ファイル解析中"},report:{zh:"读取报告中",th:"กำลังอ่านรายงาน",en:"Reading report",ja:"レポート読込中"},reconcile:{zh:"对账中",th:"กำลังกระทบยอด",en:"Reconciling",ja:"照合中"},build:{zh:"生成中",th:"กำลังสร้างไฟล์",en:"Building",ja:"作成中"},persist:{zh:"保存中",th:"กำลังบันทึก",en:"Saving",ja:"保存中"},done:{zh:"完成",th:"เสร็จสิ้น",en:"Done",ja:"完了"}};window._reconProgressText=function(n,a){n=n||{},a=window._currentLang||a||localStorage.getItem("mrpilot_lang")||"th",e.parse[a]||(a="th");const o=n.stage||"parse",s=e[o]||e.parse,p=s[a]||s.th||s.en,r=n.stage_total,f=n.stage_done;if(o==="parse"&&Number.isFinite(r)&&r>0){const i={zh:"共 {d}/{t} 个文件",th:"{d}/{t} ไฟล์",en:"{d}/{t} files",ja:"{d}/{t} ファイル"}[a]||"{d}/{t} files";return p+" · "+i.replace("{d}",f||0).replace("{t}",r)}return p},window._reconPollJob=async function(n,a,o){o=o||{};const s=o.intervalMs||1500,p=o.maxMs||1200*1e3,r=Date.now();let f=0;for(;;){let i=null;try{const c=await fetch("/api/recon/jobs/"+encodeURIComponent(n),{headers:{Authorization:"Bearer "+a}});try{i=await c.json()}catch{i=null}(!c.ok||!i||!i.ok)&&(i=null)}catch{i=null}if(i){if(f=0,o.onProgress)try{o.onProgress(i.progress||{},i)}catch{}if(i.status==="done"||i.status==="failed"||i.status==="needs_review"||i.status==="needs_mapping")return i}else if(++f>=10)return{ok:!1,status:"failed",error_code:"poll_unreachable"};if(Date.now()-r>p)return{ok:!1,status:"timeout",error_code:"timeout"};await new Promise(c=>setTimeout(c,s))}}})();(function(){let e=!1,n=[],a=[],o=null,s="all",p=[],r={stmt:"",gl:""},f=[];const i=k=>document.getElementById(k);function c(k){if(k==null)return"—";const S=Number(k);return isNaN(S)?"—":S.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function l(k){return k?String(k).slice(0,10).split("-").reverse().join("/"):"—"}function d(k){return String(k||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function u(k,S){S=window._currentLang||S||"th";const M={stmt_headers_not_found:{zh:"认不出银行账单表头 · 请确认文件含日期/金额/余额列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตารางบัญชีธนาคารไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/จำนวนเงิน/ยอดคงเหลือ หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect bank statement headers · ensure the file has date/amount/balance columns, or re-upload as a clean Excel/CSV",ja:"銀行明細のヘッダーを認識できません · 日付/金額/残高列を確認するか、Excel/CSVに変換して再アップロードしてください"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含日期/科目/借方/贷方列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตาราง GL ไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต/เครดิต หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect GL headers · ensure the file has date/account/debit/credit columns, or re-upload as a clean Excel/CSV",ja:"GLのヘッダーを認識できません · 日付/科目/借方/貸方列を確認するか、Excel/CSVに変換して再アップロードしてください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水,或换更清晰的版本重传",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง หรือใช้เวอร์ชันที่ชัดเจนกว่า",en:"No transaction rows found · please upload the correct statement, or try a clearer version",ja:"取引データが見つかりません · 正しい明細をアップロードするか、より鮮明なファイルでお試しください"},no_rows:{zh:"解析后没有可对账的数据行 · 请确认文件内容完整,或换清晰版本重传",th:"ไม่มีแถวข้อมูลให้กระทบยอดหลังการอ่าน · ตรวจสอบความสมบูรณ์ของไฟล์ หรืออัปโหลดใหม่",en:"No reconcilable rows after parsing · check the file is complete, or re-upload a clearer version",ja:"解析後に照合可能な行がありません · ファイルの完全性を確認するか再アップロードしてください"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密 · 请换文件或转 PDF/Excel 重传",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส · ลองไฟล์อื่นหรือแปลงเป็น PDF/Excel",en:"File cannot be read · may be corrupted or encrypted · try another file or convert to PDF/Excel",ja:"ファイルを読み取れません · 破損または暗号化の可能性 · 別ファイルまたはPDF/Excelに変換してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロードしてください"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本,或转成 PDF / Excel / CSV 重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น PDF / Excel / CSV",en:"Could not read the file · try a clearer version, or convert to PDF / Excel / CSV",ja:"読み取りに失敗 · より鮮明なファイルか、PDF / Excel / CSV に変換して再試行してください"}},U={zh:"解析失败 · 请换更清晰的文件,或转成 Excel / CSV 后重新上传",th:"อ่านไฟล์ไม่สำเร็จ · ลองไฟล์ที่ชัดเจนกว่า หรือแปลงเป็น Excel / CSV แล้วอัปโหลดใหม่",en:"Parsing failed · try a clearer file, or convert to Excel / CSV and re-upload",ja:"解析に失敗しました · より鮮明なファイルか、Excel / CSV に変換して再アップロードしてください"},z=M[k]||U;return z[S]||z.th||z.en}function g(k){const S=k==="stmt"?n:a,M=i(`brv2-${k}-name`);if(M)if(S.length===0)M.textContent="";else{const z=window._currentLang||"zh",m={zh:"个文件",th:" ไฟล์",en:" file(s)",ja:" ファイル"};M.textContent=S.length+(m[z]||" 个文件")}const U=i("brv2-preview-panel");U&&U.style.display!=="none"&&E(k),w()}function w(){const k=i("brv2-toggle-preview"),S=i("brv2-preview-panel"),M=n.length+a.length>0;k&&(k.style.display=M?"":"none"),!M&&S&&(S.style.display="none",k&&k.classList.remove("open"))}function $(){E("stmt"),E("gl")}function E(k){const S=i(k==="stmt"?"brv2-pp-stmt-col":"brv2-pp-gl-col");if(!S)return;const M=k==="stmt"?n:a,U=window._currentLang||"zh",z={stmt:{zh:"① 银行账单",th:"① บัญชีธนาคาร",en:"① Bank Stmt",ja:"① 銀行明細"},gl:{zh:"② 总账 GL",th:"② GL รายงาน",en:"② GL Report",ja:"② GL帳簿"}},m=(z[k]||{})[U]||z[k].zh,R=d(window.t&&window.t("vex-preview-search")||"搜索文件名..."),O=d(window.t&&window.t("vex-preview-clear-all")||"全清"),J=r[k]||"";S.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+d(m)+' <span class="vex-pp-col-count">'+M.length+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="brv2-pp-search-'+k+'" type="text" placeholder="'+R+'" value="'+d(J)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="brv2-pp-clearall-'+k+'" type="button">'+O+'</button></div><div class="vex-pp-file-list" id="brv2-pp-'+k+'-list"></div><div class="vex-pp-pagination" id="brv2-pp-'+k+'-pg"></div>';const X=i("brv2-pp-search-"+k);X&&X.addEventListener("input",function(se){r[k]=se.target.value,_(k)});const de=i("brv2-pp-clearall-"+k);de&&de.addEventListener("click",function(){k==="stmt"?n.length=0:a.length=0,g(k),j()}),_(k)}function _(k){const S=i("brv2-pp-"+k+"-list"),M=i("brv2-pp-"+k+"-pg");if(!S)return;const U=k==="stmt"?n:a,z=(r[k]||"").toLowerCase(),m=z?U.filter(J=>J.name.toLowerCase().includes(z)):U.slice(),R='<svg class="vex-pp-fi-ico" viewBox="0 0 14 16" fill="none" stroke="currentColor" stroke-width="1.4" width="12" height="14"><path d="M3 1h6l3 3v11H3V1z"/><path d="M9 1v3h3"/></svg>',O='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" width="11" height="11"><path d="M2 4h10M5 4V2h4v2M5.5 7v4M8.5 7v4M3 4l1 8h6l1-8"/></svg>';if(S.innerHTML=m.map((J,X)=>'<div class="vex-pp-file-row">'+R+'<span class="vex-pp-fi-name" title="'+d(J.name)+'">'+d(J.name)+'</span><span class="vex-pp-fi-size">'+B(J.size)+'</span><button class="vex-pp-fi-del" type="button" data-zone="'+k+'" data-idx="'+U.indexOf(J)+'" aria-label="remove">'+O+"</button></div>").join(""),S.querySelectorAll(".vex-pp-fi-del").forEach(function(J){J.addEventListener("click",function(){const X=parseInt(J.dataset.idx,10);J.dataset.zone==="stmt"?n.splice(X,1):a.splice(X,1),g(J.dataset.zone),j()})}),M){const J=window.t&&window.t("vex-preview-count")||"显示 {n} / 共 {m}";M.textContent=J.replace("{n}",m.length).replace("{m}",U.length)}}function B(k){return k?k<1024?k+" B":k<1048576?(k/1024).toFixed(1)+" KB":(k/1048576).toFixed(1)+" MB":""}var q="pearnly.brv2.lastAnchorOcr";function H(k){try{var S=k&&k._anchor_ocr;if(!S||typeof S!="object")return;var M={stmt_opening:Number.isFinite(+S.stmt_opening)?+S.stmt_opening:null,gl_opening:Number.isFinite(+S.gl_opening)?+S.gl_opening:null,gl_closing:Number.isFinite(+S.gl_closing)?+S.gl_closing:null,stmt_closing:Number.isFinite(+S.stmt_closing)?+S.stmt_closing:null,ts:Date.now()};localStorage.setItem(q,JSON.stringify(M))}catch{}}function F(){try{var k=localStorage.getItem(q);if(!k)return null;var S=JSON.parse(k);return!S||typeof S!="object"?null:S}catch{return null}}function A(){var k=F();if(k){var S={"brv2-anchor-stmt-opening":k.stmt_opening,"brv2-anchor-gl-opening":k.gl_opening,"brv2-anchor-gl-closing":k.gl_closing,"brv2-anchor-stmt-closing":k.stmt_closing},M=0;Object.keys(S).forEach(function(O){var J=document.getElementById(O);if(J&&J.value===""){var X=S[O];if(Number.isFinite(X)){J.value=X.toFixed(2);var de=J.closest&&J.closest(".brv2-anchor-cell");de&&de.classList.add("is-prefilled"),M+=1}}});var U=document.getElementById("brv2-anchor-eq"),z=document.getElementById("brv2-anchor-eq-val");if(U&&z&&Number.isFinite(k.stmt_opening)&&Number.isFinite(k.gl_opening)){var m=k.stmt_opening-k.gl_opening;z.textContent=m.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),U.style.display=""}if(M>0){var R=document.getElementById("brv2-anchor-prefill-banner");R&&R.classList.add("show")}}}function y(){var k=document.getElementById("brv2-anchor-prefill-banner");if(k){var S=!1;["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"].forEach(function(M){var U=document.getElementById(M);if(U){var z=U.closest&&U.closest(".brv2-anchor-cell");z&&z.classList.contains("is-prefilled")&&(S=!0)}}),k.classList.toggle("show",S)}}var v=[["stmt_opening","brv2-anchor-stmt-opening"],["gl_opening","brv2-anchor-gl-opening"],["gl_closing","brv2-anchor-gl-closing"],["stmt_closing","brv2-anchor-stmt-closing"]];function b(k,S){return window.t&&window.t(k)||S}function L(k){return String(k??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function C(k){return Number.isFinite(+k)?(+k).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—"}function P(k){var S=document.getElementById("brv2-summary-collapse");if(!(!S||!S.parentNode)){var M=document.getElementById("brv2-anchor-audit"),U=k&&k._anchor_overrides;if(!U||typeof U!="object"||Object.keys(U).length===0){M&&M.parentNode&&M.parentNode.removeChild(M);return}M||(M=document.createElement("div"),M.id="brv2-anchor-audit",M.style.cssText="margin-top:14px;background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:14px 16px;",S.parentNode.insertBefore(M,S.nextSibling));var z=v.map(function(m){var R=U[m[0]];if(!R)return"";var O=+R.ocr||0,J=+R.user||0,X=J-O,de=X>0?"+":(X<0,""),se=Math.abs(X)<.005?"#6b7280":X>0?"#16a34a":"#dc2626";return'<tr><td style="padding:6px 10px;color:#111827;font-size:13px">'+L(b(m[1],m[0]))+'</td><td style="padding:6px 10px;color:#6b7280;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+L(C(O))+'</td><td style="padding:6px 10px;background:#fef08a;color:#92400e;font-weight:600;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+L(C(J))+'</td><td style="padding:6px 10px;color:'+se+';font-weight:500;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+L(de+C(X))+"</td></tr>"}).join("");M.innerHTML='<div style="font-weight:600;color:#92400e;font-size:13px;margin-bottom:10px">'+L(b("brv2-anchor-audit-title","⚠ This run contains manually entered anchors"))+'</div><table style="width:100%;border-collapse:collapse;font-family:inherit"><thead><tr><th style="padding:6px 10px;text-align:left;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+L(b("brv2-anchor-audit-col-field","Field"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+L(b("brv2-anchor-audit-col-ocr","OCR"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+L(b("brv2-anchor-audit-col-user","User"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+L(b("brv2-anchor-audit-col-diff","Diff"))+"</th></tr></thead><tbody>"+z+"</tbody></table>"}}function I(){const k=i("brv2-toggle-preview");k&&!k._reconBound&&(k._reconBound=!0,k.addEventListener("click",function(){const S=i("brv2-preview-panel"),M=i("brv2-toggle-preview-label"),U=S&&S.style.display!=="none";S&&(S.style.display=U?"none":""),k.classList.toggle("open",!U),M&&(M.textContent=U?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),U||$()}))}function j(){const k=i("brv2-run-btn"),S=i("brv2-status"),M=n.length>0,U=a.length>0;if(k&&(k.disabled=!(M&&U)),S){const z=window._currentLang||"zh";if(!M&&!U){const m={zh:"请上传银行账单和 GL 文件",th:"กรุณาอัปโหลดบัญชีธนาคารและ GL",en:"Upload bank statement and GL files",ja:"銀行明細と GL を両方アップロードしてください"};S.textContent=m[z]||m.zh}else if(M)if(U){const m={zh:"两份文件已就绪",th:"พร้อมสอบทาน",en:"Ready to reconcile",ja:"照合を開始できます"};S.textContent=m[z]||m.zh}else{const m={zh:"还缺 GL 文件",th:"ยังขาดไฟล์ GL",en:"Missing GL file",ja:"GL ファイルが未アップロード"};S.textContent=m[z]||m.zh}else{const m={zh:"还缺银行账单 PDF",th:"ยังขาดไฟล์บัญชีธนาคาร PDF",en:"Missing bank statement PDF",ja:"銀行明細 PDF が未アップロード"};S.textContent=m[z]||m.zh}}}function Y(k,S,M){const U=i(k),z=i(S);!U||!z||(U.addEventListener("click",()=>z.click()),U.addEventListener("keydown",m=>{(m.key==="Enter"||m.key===" ")&&(m.preventDefault(),z.click())}),U.addEventListener("dragover",m=>{m.preventDefault(),U.classList.add("drag-over")}),U.addEventListener("dragleave",()=>U.classList.remove("drag-over")),U.addEventListener("drop",m=>{m.preventDefault(),U.classList.remove("drag-over");const R=Array.from(m.dataTransfer.files||[]);M==="stmt"?n.push(...R):a.push(...R),g(M),j()}),z.addEventListener("change",()=>{const m=Array.from(z.files||[]);M==="stmt"?n.push(...m):a.push(...m),z.value="",g(M),j()}))}function G(k){const S=i("brv2-progress"),M=i("brv2-run-btn"),U=i("brv2-error");S&&(S.style.display=k?"":"none"),M&&(M.disabled=k),U&&(U.style.display="none")}function W(k){const S=i("brv2-error");S&&(S.textContent=k,S.style.display="",S.scrollIntoView({behavior:"smooth",block:"nearest"})),G(!1),j(),window.showToast&&window.showToast(k,"error")}async function te(){if(n.length===0||a.length===0)return;const k=localStorage.getItem("mrpilot_token")||"",S=window._currentLang||"zh",M=(i("brv2-acct-select")||{}).value||"";T(!1),G(!0);try{const U=new FormData;n.forEach(ae=>U.append("stmt_files",ae)),a.forEach(ae=>U.append("gl_files",ae)),U.append("gl_account",M),U.append("lang",S);const z=parseFloat((i("brv2-anchor-gl-closing")||{}).value),m=parseFloat((i("brv2-anchor-stmt-closing")||{}).value),R=parseFloat((i("brv2-anchor-stmt-opening")||{}).value),O=parseFloat((i("brv2-anchor-gl-opening")||{}).value);Number.isFinite(z)&&U.append("gl_closing_override",z),Number.isFinite(m)&&U.append("stmt_closing_override",m),Number.isFinite(R)&&U.append("stmt_opening_override",R),Number.isFinite(O)&&U.append("gl_opening_override",O);const J=await fetch("/api/recon/bank-v2/submit",{method:"POST",headers:{Authorization:"Bearer "+k},body:U});let X=null;try{X=await J.json()}catch{X=null}if(X&&X.needs_mapping){G(!1),window.ReconMapping?window.ReconMapping.show(X,{token:k,lang:S,onConfirmed:function(){te()}}):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(!J.ok||!X||!X.ok||!X.job_id){G(!1),X&&(X.detail||X.error)?W(_humanizeBackendError(X.detail||X.error,"Error "+J.status)):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const de=i("brv2-progress-sub"),se=await window._reconPollJob(X.job_id,k,{onProgress:ae=>{de&&(de.textContent=window._reconProgressText(ae,S))}});if(se&&se.status==="needs_mapping"&&se.mapping){G(!1),window.ReconMapping?window.ReconMapping.show(se.mapping,{token:k,lang:S,onConfirmed:function(){te()}}):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(se&&se.status==="needs_review"&&se.review){G(!1),window.ReconReview?window.ReconReview.show(se.review,{token:k,lang:S,jobId:X.job_id,onConfirmed:async function(ae){G(!0);const pe=await window._reconPollJob(ae,k,{onProgress:fe=>{de&&(de.textContent=window._reconProgressText(fe,S))}});await ce(pe)}}):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(se&&se.status==="failed"){G(!1),W(u(se.error_code,S));return}await ce(se);async function ce(ae){try{if(!ae||ae.status!=="done"||!ae.result_id){G(!1),W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const pe=await fetch("/api/recon/bank-v2/"+encodeURIComponent(ae.result_id),{headers:{Authorization:"Bearer "+k}});let fe=null;try{fe=await pe.json()}catch{fe=null}if(!pe.ok||fe===null||!fe.ok){G(!1),W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}(fe.gl_accounts||[]).length>1&&re(fe.gl_accounts),o=fe,p=fe.detail||[],s="all",document.querySelectorAll(".brv2-filter-btn").forEach(ge=>ge.classList.toggle("active",ge.dataset.filter==="all")),H(fe&&fe.summary),G(!1),N(fe),Q();const me=i("brv2-summary-collapse");me&&me.scrollIntoView({behavior:"smooth",block:"nearest"})}catch(pe){G(!1),W(pe.message||"Network error")}}}catch(U){W(U.message||"Network error")}}function re(k){const S=i("brv2-acct-select");if(!S)return;const M=window._currentLang||"zh",U={zh:"全部账户",th:"ทุกบัญชี",en:"All Accounts",ja:"すべての口座"}[M]||"全部账户";S.innerHTML=`<option value="">${U}</option>`+k.map(z=>`<option value="${d(z)}">${d(z)}</option>`).join(""),S.style.display=""}function T(k){const S=i("brv2-summary-collapse"),M=i("brv2-detail-collapse"),U=i("brv2-export-btn"),z=i("brv2-new-btn"),m=i("brv2-parse-info-wrap");S&&(S.style.display=k?"":"none"),M&&(M.style.display=k?"":"none"),U&&(U.style.display=k?"":"none"),z&&(z.style.display=k?"":"none"),!k&&m&&(m.style.display="none");const R=i("brv2-warnings");!k&&R&&(R.style.display="none",R.innerHTML="")}function x(k){const S=i("brv2-parse-info-wrap"),M=i("brv2-parse-info-body");if(!S||!M)return;const U=k.parse_info;if(!U){S.style.display="none";return}const z=window._currentLang||"zh",m={title:{zh:"文件解析状态",th:"สถานะการอ่านไฟล์",en:"File Parse Status",ja:"ファイル解析状態"},type:{zh:"类型",th:"ประเภท",en:"Type",ja:"種別"},file:{zh:"文件名",th:"ชื่อไฟล์",en:"File",ja:"ファイル"},rows:{zh:"解析行数",th:"แถวที่พบ",en:"Rows Found",ja:"解析行数"},bank:{zh:"银行/科目",th:"ธนาคาร/บัญชี",en:"Bank/Account",ja:"銀行/科目"},status:{zh:"状态",th:"สถานะ",en:"Status",ja:"状態"},stmt:{zh:"账单",th:"บัญชีธนาคาร",en:"Stmt",ja:"明細"},gl:{zh:"总账GL",th:"GL",en:"GL",ja:"GL"},ok:{zh:"✓ 成功",th:"✓ สำเร็จ",en:"✓ OK",ja:"✓ 成功"},warn:{zh:"⚠ 0行",th:"⚠ 0 แถว",en:"⚠ 0 rows",ja:"⚠ 0行"},fail:{zh:"✗ 失败",th:"✗ ล้มเหลว",en:"✗ Failed",ja:"✗ 失敗"}},R=ce=>(m[ce]||{})[z]||(m[ce]||{}).zh||ce,O=[...(U.stmt_files||[]).map(ce=>({...ce,_type:"stmt",_extra:ce.bank_code||""})),...(U.gl_files||[]).map(ce=>({...ce,_type:"gl",_extra:(ce.accounts||[]).join(", ")}))],J={stmt_headers_not_found:{zh:"认不出表头列 · 请确认文件含日期/金额/余额列",th:"หาคอลัมน์หัวตารางไม่เจอ · ตรวจสอบไฟล์มีวันที่/จำนวนเงิน/ยอดคงเหลือ",en:"Cannot detect column headers · ensure file has date/amount/balance columns",ja:"列ヘッダーが認識できません · 日付/金額/残高列を確認してください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง",en:"No transaction rows found · please check the file",ja:"取引データが見つかりません · ファイルを確認してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロード"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส",en:"File cannot be read · may be corrupted or encrypted",ja:"ファイルを読み取れません · 破損または暗号化の可能性"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本或换 PDF 格式重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่าหรือเปลี่ยนเป็น PDF",en:"Could not read file · try a clearer version or upload as PDF",ja:"読み取り失敗 · より鮮明なファイルまたは PDF 形式で再試行"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含科目/借方/贷方列",th:"หาหัวคอลัมน์ GL ไม่เจอ · ตรวจสอบมีคอลัมน์บัญชี/เดบิต/เครดิต",en:"Cannot detect GL column headers · ensure account/debit/credit columns exist",ja:"GL 列ヘッダー認識不可 · 科目/借方/貸方列を確認してください"}},X=ce=>{const ae=String(ce||"");return/Cannot detect bank statement column headers/i.test(ae)?"stmt_headers_not_found":/Cannot detect GL column headers/i.test(ae)?"gl_headers_not_found":/No transaction rows found|no pages parsed/i.test(ae)?"stmt_no_rows":/unsupported format/i.test(ae)?"file_not_supported":/Cannot read Excel|file_unreadable/i.test(ae)?"file_unreadable":/Gemini.*invalid JSON|Gemini.*parsed but failed|validation errors|BankStatementDocument schema|layer2:|layer1:/i.test(ae)?"ocr_failed":null},de=ce=>{const ae=ce.error_code||X(ce.error);if(ae&&J[ae]){const pe=window._currentLang||"zh";return J[ae][pe]||J[ae].zh}return String(ce.error||"").slice(0,80)},se=ce=>!ce.ok&&ce.error?`<span style="color:#dc2626">${R("fail")} — ${d(de(ce))}</span>`:ce.rows?`<span style="color:#059669">${R("ok")} (${ce.rows})</span>`:`<span style="color:#d97706">${R("warn")}</span>`;M.innerHTML=`
            <div style="font-size:12px;font-weight:600;margin-bottom:6px;color:var(--ink-2)">${R("title")}</div>
            <table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:4px">
                <thead>
                    <tr style="background:#f3f4f6;font-weight:600">
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${R("type")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb">${R("file")}</th>
                        <th style="padding:6px 8px;text-align:center;border:1px solid #e5e7eb;white-space:nowrap">${R("rows")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${R("bank")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${R("status")}</th>
                    </tr>
                </thead>
                <tbody>
                    ${O.map(ce=>`<tr>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;white-space:nowrap">${ce._type==="stmt"?R("stmt"):R("gl")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${d(ce.file||"")}">${d(ce.file||"")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;text-align:center">${ce.rows||0}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;color:var(--ink-2)">${d(ce._extra||"")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb">${se(ce)}</td>
                    </tr>`).join("")}
                </tbody>
            </table>`,S.style.display=""}async function h(k){const S=localStorage.getItem("mrpilot_token")||"",M=window._currentLang||"zh";try{const U=await fetch("/api/recon/bank-v2/"+k+"/export?lang="+M,{headers:{Authorization:"Bearer "+S}});if(!U.ok){const de=await U.json().catch(()=>({}));window.showToast&&window.showToast(de.detail||"Export failed","error");return}const z=await U.blob(),R=(U.headers.get("content-disposition")||"").match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/),O=R?R[1].replace(/['"]/g,""):"reconciliation.xlsx",J=URL.createObjectURL(z),X=document.createElement("a");X.href=J,X.download=O,document.body.appendChild(X),X.click(),document.body.removeChild(X),URL.revokeObjectURL(J)}catch(U){window.showToast&&window.showToast("Export error: "+U.message,"error")}}function D(k,S){const M=i("brv2-summary-collapse");let U=i("brv2-warnings");const z=window._currentLang||"zh",m={zh:"⏭ 已跳过无法识别的文件:",th:"⏭ ข้ามไฟล์ที่อ่านไม่ได้:",en:"⏭ Skipped unreadable file:",ja:"⏭ 読み取れないファイルをスキップ:"}[z]||"⏭ ",R=[];if((S||[]).forEach(O=>R.push(m+" "+O)),(k||[]).forEach(O=>R.push(O)),!R.length){U&&(U.style.display="none");return}if(!U)if(U=document.createElement("div"),U.id="brv2-warnings",M&&M.parentNode)M.parentNode.insertBefore(U,M);else return;U.style.cssText="display:block;margin:10px 0;padding:10px 14px;background:#FEF3C7;border:1px solid #FCD34D;border-radius:8px;color:#92400E;font-size:13px;line-height:1.6",U.innerHTML=R.map(O=>"<div>"+d(O)+"</div>").join("")}function N(k){x(k),D(k.warnings||[],k.skipped_files||[]),!k.ok&&k.error&&window.showToast&&window.showToast(k.error,"error");const S=k.stats||{},M=k.summary||{},U=S.matched||0,z=(S.gl_debit_only||0)+(S.gl_credit_only||0),m=(S.stmt_withdrawal_only||0)+(S.stmt_deposit_only||0),R=Number(M.formula_diff||0),O=Math.abs(R)<.05;i("brv2-kpi-matched")&&(i("brv2-kpi-matched").textContent=U),i("brv2-kpi-diff")&&(i("brv2-kpi-diff").textContent=c(R)),i("brv2-kpi-unmatched")&&(i("brv2-kpi-unmatched").textContent=z+m);const J=i("brv2-kpi-diff-icon");J&&(J.style.background=O?"#d1fae5":"#fee2e2",J.style.color=O?"#065f46":"#b91c1c");const X=i("brv2-formula-sub");if(X){const pe=window._currentLang||"zh";X.textContent=O?{zh:"✓ 平衡",th:"✓ สมดุล",en:"✓ Balanced",ja:"✓ 一致"}[pe]||"✓ 平衡":({zh:"差 ",th:"ต่าง ",en:"Diff ",ja:"差 "}[pe]||"差 ")+c(R)}const de=i("brv2-detail-sub");if(de){const pe=window._currentLang||"zh",fe={zh:"共 {n} 行",th:"ทั้งหมด {n} แถว",en:"{n} rows",ja:"計 {n} 行"}[pe]||"共 {n} 行";de.textContent=fe.replace("{n}",p.length)}function se(pe,fe,me){const ge=i(pe);ge&&(ge.textContent=(me&&fe>0?"(":"")+c(me?-fe:fe)+(me&&fe>0?")":""))}se("brf-gl-close",M.gl_closing||0),se("brf-open-diff",M.opening_diff||0),se("brf-gl-debit-only",M.gl_debit_only_amount||0,!0),se("brf-gl-credit-only",M.gl_credit_only_amount||0),se("brf-stmt-wd-only",M.stmt_withdrawal_only_amount||0,!0),se("brf-stmt-dep-only",M.stmt_deposit_only_amount||0),se("brf-calc-close",M.formula_stmt_closing||0),se("brf-stmt-close",M.stmt_closing||0),i("brf-diff")&&(i("brf-diff").textContent=c(R));const ce=i("brv2-fcell-diff");ce&&ce.classList.toggle("brv2-fcell-diff-ok",O);const ae=i("brv2-export-btn");ae&&(ae.onclick=()=>{o&&h(o.task_id)}),P(M),T(!0),K()}function K(){const k=i("brv2-tbody");if(!k)return;const S=p.filter(m=>s==="all"?!0:s==="matched"?m.match_status==="matched":s==="gl_only"?m.match_status.startsWith("gl_"):s==="stmt_only"?m.match_status.startsWith("stmt_"):!0);if(S.length===0){const m={zh:"无记录",th:"ไม่มีรายการ",en:"No rows",ja:"行なし"}[window._currentLang||"zh"]||"无记录";k.innerHTML=`<tr><td colspan="10" style="text-align:center;padding:20px;color:var(--ink-3)">${m}</td></tr>`;return}const M=window._currentLang||"zh",U={zh:"OCR 余额验证未通过 · 上一行余额 ± 金额 ≠ 本行余额，请核对原 PDF",th:"การตรวจสอบยอดคงเหลือไม่ผ่าน · ยอดก่อนหน้า ± จำนวน ≠ ยอดบรรทัดนี้ โปรดตรวจสอบ PDF ต้นฉบับ",en:"Balance check FAILED · prev_balance ± amount ≠ this row balance — verify against the original PDF",ja:"残高検証エラー · 前残高 ± 金額 ≠ この行残高 — 元のPDFと照合してください"}[M],z={zh:"OCR 低置信度 · 数字模糊或难以辨认，请核对原 PDF",th:"OCR ความมั่นใจต่ำ · ตัวเลขเบลอหรืออ่านยาก โปรดตรวจสอบ PDF ต้นฉบับ",en:"OCR low confidence · digit was blurry or hard to read — verify against the original PDF",ja:"OCR信頼度低 · 数字がぼやけている — 元のPDFと照合してください"}[M];k.innerHTML=S.map(m=>{const R=m.match_status,O=m.match_layer;let J="",X="";R==="matched"?(O===1&&(J="matched",X='<span class="brv2-status-badge brv2-badge-matched">L1 ✓</span>'),O===2&&(J="matched-l2",X='<span class="brv2-status-badge brv2-badge-matched-l2">L2 ~</span>'),O===3&&(J="matched-l3",X='<span class="brv2-status-badge brv2-badge-matched-l3">L3 ?</span>')):R==="gl_debit_only"||R==="gl_credit_only"?(J="gl-only",X='<span class="brv2-status-badge brv2-badge-gl-only">GL</span>'):(J="stmt-only",X=`<span class="brv2-status-badge brv2-badge-stmt-only">${{zh:"账单",th:"บัญชี",en:"Stmt",ja:"明細"}[M]||"账单"}</span>`);let de="";return m.stmt_balance_ok===!1&&(de+=`<span class="brv2-ocr-warn brv2-ocr-warn-bal" title="${d(U)}">⚠</span>`,J+=" brv2-row-warn"),m.stmt_confidence==="low"&&(de+=`<span class="brv2-ocr-warn brv2-ocr-warn-conf" title="${d(z)}">◌</span>`,J.includes("brv2-row-warn")||(J+=" brv2-row-warn-soft")),`<tr class="${J.trim()}">
              <td>${X}${de}</td>
              <td>${d(l(m.stmt_date))}</td>
              <td title="${d(m.stmt_desc)}" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${d(m.stmt_desc)}</td>
              <td class="num">${m.stmt_withdrawal?c(m.stmt_withdrawal):""}</td>
              <td class="num">${m.stmt_deposit?c(m.stmt_deposit):""}</td>
              <td>${d(l(m.gl_date))}</td>
              <td title="${d(m.gl_doc_no)}" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${d(m.gl_doc_no)}</td>
              <td class="num">${m.gl_debit?c(m.gl_debit):""}</td>
              <td class="num">${m.gl_credit?c(m.gl_credit):""}</td>
              <td>${O?"L"+O:"—"}</td>
            </tr>`}).join("")}async function Q(){const k=localStorage.getItem("mrpilot_token")||"";try{const M=await(await fetch("/api/recon/bank-v2/tasks",{headers:{Authorization:"Bearer "+k}})).json();ee(M.tasks||[])}catch{const M=i("brv2-history-empty"),U=window._currentLang||"zh",z={zh:"加载失败",th:"โหลดประวัติไม่ได้",en:"Load failed",ja:"読み込み失敗"}[U]||"加载失败";M&&(M.textContent=z,M.style.display="");const m=i("brv2-history-table-wrap");m&&(m.style.display="none")}}const le=10;let ie=1;function V(){const k=i("brv2-history-pager"),S=i("brv2-history-pager-info"),M=i("brv2-history-prev"),U=i("brv2-history-next");if(!k)return;if(f.length<=le){k.style.display="none";return}k.style.display="";const z=Math.ceil(f.length/le);S&&(S.textContent=ie+" / "+z),M&&(M.disabled=ie<=1),U&&(U.disabled=ie>=z)}function Z(){const k=i("brv2-history-prev"),S=i("brv2-history-next");k&&!k._brv2Bound&&(k._brv2Bound=!0,k.addEventListener("click",()=>{ie>1&&(ie--,ee(f))})),S&&!S._brv2Bound&&(S._brv2Bound=!0,S.addEventListener("click",()=>{const M=Math.ceil(f.length/le);ie<M&&(ie++,ee(f))}))}function ee(k){k!==void 0&&(f=k||[],ie=1);const S=f,M=i("brv2-history-empty"),U=i("brv2-history-table-wrap"),z=i("brv2-history-tbody");if(!z)return;const m=window._currentLang||"zh";if(!S.length){const ae={zh:"暂无对账记录",th:"ยังไม่มีประวัติ",en:"No records yet",ja:"記録なし"}[m]||"暂无对账记录";M&&(M.textContent=ae,M.style.display=""),U&&(U.style.display="none"),V();return}M&&(M.style.display="none"),U&&(U.style.display="");const R=Math.ceil(S.length/le);ie>R&&(ie=R);const O=(ie-1)*le,J=S.slice(O,O+le),X=localStorage.getItem("mrpilot_token")||"",de='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><circle cx="8" cy="8" r="6"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',se='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',ce='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';z.innerHTML="",J.forEach(ae=>{const pe=Number(ae.formula_diff||0),fe=Math.abs(pe)<.05,me=(ae.stmt_files||"").split(";").map(_e=>_e.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),ge=(ae.gl_files||"").split(";").map(_e=>_e.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),be=ae.created_at?String(ae.created_at).slice(0,16).replace("T"," "):"",xe=document.createElement("tr");xe.dataset.taskId=ae.id;const ze=document.createElement("td");ze.textContent=be;const Te=document.createElement("td");Te.className="glv-history-file",Te.title=me+" + "+ge,Te.textContent=me+" + "+ge;const He=document.createElement("td");He.className="glv-num",He.textContent=(ae.stmt_row_count||0)+" / "+(ae.gl_row_count||0);const nt=document.createElement("td");nt.className="glv-num",nt.textContent=ae.matched_count||0;const at=document.createElement("td");at.className="glv-num",at.textContent=ae.unmatched_gl||0;const ot=document.createElement("td");ot.className="glv-num",ot.textContent=ae.unmatched_stmt||0;const Oe=document.createElement("td");Oe.className="glv-num",Oe.style.color=fe?"#059669":"#dc2626",Oe.textContent=fe?"✓":c(pe);const Ae=document.createElement("td");Ae.className="glv-history-actions";const st=(_e,kt,_t,rn)=>{const Be=document.createElement("button");return Be.type="button",Be.title=kt,Be.setAttribute("aria-label",kt),_t&&(Be.className=_t),Be.innerHTML=_e,Be.onclick=ln=>{ln.stopPropagation(),rn()},Be},nn={zh:"删除这条记录?",th:"ลบรายการนี้?",en:"Delete this record?",ja:"この記録を削除しますか?"}[m]||"删除?",an={zh:"加载",th:"โหลด",en:"Load",ja:"読込"}[m]||"加载",on={zh:"导出",th:"ส่งออก",en:"Export",ja:"エクスポート"}[m]||"导出",sn={zh:"删除",th:"ลบ",en:"Delete",ja:"削除"}[m]||"删除";Ae.appendChild(st(de,an,"",()=>oe(ae.id,X))),Ae.appendChild(st(se,on,"",()=>h(ae.id))),Ae.appendChild(st(ce,sn,"glv-del",async()=>{await showConfirm(nn,{danger:!0})&&(await fetch("/api/recon/bank-v2/"+ae.id,{method:"DELETE",headers:{Authorization:"Bearer "+X}}),Q())})),[ze,Te,He,nt,at,ot,Oe,Ae].forEach(_e=>xe.appendChild(_e)),xe.style.cursor="pointer",xe.addEventListener("click",async _e=>{_e.target.closest(".glv-del")||_e.target.closest("button")||await oe(ae.id,X)}),z.appendChild(xe)}),V(),ne()}function ne(){const k=((i("brv2-hist-search")||{}).value||"").trim().toLowerCase(),S=i("brv2-history-tbody");S&&S.querySelectorAll("tr").forEach(M=>{M.dataset.taskId&&(M.style.display=!k||M.textContent.toLowerCase().includes(k)?"":"none")})}async function oe(k,S){try{const U=await(await fetch("/api/recon/bank-v2/"+k,{headers:{Authorization:"Bearer "+S}})).json();if(!U.ok)return;o={task_id:U.task_id,...U},p=U.detail||[],s="all",document.querySelectorAll(".brv2-filter-btn").forEach(z=>z.classList.toggle("active",z.dataset.filter==="all")),N(o)}catch{}}function ue(){if(e){Q();return}e=!0,Y("brv2-stmt-zone","brv2-stmt-input","stmt"),Y("brv2-gl-zone","brv2-gl-input","gl");const k=["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"];function S(){const O=parseFloat((i("brv2-anchor-stmt-opening")||{}).value),J=parseFloat((i("brv2-anchor-gl-opening")||{}).value),X=i("brv2-anchor-eq"),de=i("brv2-anchor-eq-val");if(!(!X||!de))if(Number.isFinite(O)&&Number.isFinite(J)){const se=O-J;de.textContent=se.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),X.style.display=""}else X.style.display="none"}k.forEach(O=>{const J=i(O);J&&(J.addEventListener("input",S),J.addEventListener("input",()=>{const X=J.closest(".brv2-anchor-cell");X&&X.classList.remove("is-prefilled"),y()}))}),A();const M=i("brv2-run-btn");M&&M.addEventListener("click",te);const U=i("brv2-reset-btn");U&&U.addEventListener("click",()=>{o=null,p=[],n=[],a=[],g("stmt"),g("gl"),j(),T(!1);const O=i("brv2-acct-select");O&&(O.style.display="none"),k.forEach(de=>{const se=i(de);if(se){se.value="";const ce=se.closest&&se.closest(".brv2-anchor-cell");ce&&ce.classList.remove("is-prefilled")}});const J=i("brv2-anchor-eq");J&&(J.style.display="none");const X=i("brv2-anchor-prefill-banner");X&&X.classList.remove("show")});const z=i("brv2-new-btn");z&&z.addEventListener("click",()=>{o=null,p=[],n=[],a=[],g("stmt"),g("gl"),j(),T(!1)});const m=i("brv2-filter-tabs");m&&m.addEventListener("click",O=>{O.stopPropagation();const J=O.target.closest(".brv2-filter-btn");J&&(s=J.dataset.filter,m.querySelectorAll(".brv2-filter-btn").forEach(X=>X.classList.toggle("active",X===J)),K())}),I(),Z();const R=i("brv2-hist-search");R&&R.addEventListener("input",ne),Q(),j(),window._brv2LoadHistory=Q,Array.isArray(window.__i18nSubs)||(window.__i18nSubs=[]),window.__i18nSubs=window.__i18nSubs.filter(O=>O.name!=="brv2"),window.__i18nSubs.push({name:"brv2",fn:function(){j(),g("stmt"),g("gl"),o&&N(o),ee()}})}window._loadBankReconV2Panel=function(k){const S=k?document.getElementById(k):null;S&&S.id!=="recon-pane-bank"&&(S.innerHTML=`<div style="padding:16px;font-size:13px;color:var(--ink-3)">
                银行对账 v2 · 请前往对账中心使用</div>`),ue()},document.addEventListener("DOMContentLoaded",()=>{i("brv2-run-btn")&&ue()}),window._bankReconV2Init=ue})();(function(){const e=document.getElementById("general-lang");if(!e)return;e.addEventListener("change",a=>{const o=a.target.value;o&&applyLang(o)});const n=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";e.value=n})();(function(){const n="pearnly_general_tz",a="pearnly_general_date_format",o="pearnly_general_number_format",s={tz:"Asia/Bangkok",date:"YYYY-MM-DD",number:"comma_dot"};function p(){const c=document.getElementById("general-tz"),l=document.getElementById("general-date"),d=document.getElementById("general-number");if(!(!c||!l||!d))try{c.value=localStorage.getItem(n)||s.tz,l.value=localStorage.getItem(a)||s.date,d.value=localStorage.getItem(o)||s.number}catch{c.value=s.tz,l.value=s.date,d.value=s.number}}async function r(){const c=document.getElementById("btn-save-general"),l=document.getElementById("general-save-msg");if(!c)return;const d=c.innerHTML;c.disabled=!0,c.innerHTML="<span>"+(t("msg-saving")||"保存中...")+"</span>",l&&(l.textContent="",l.classList.remove("error"));try{const u=(document.getElementById("general-tz")||{}).value||s.tz,g=(document.getElementById("general-date")||{}).value||s.date,w=(document.getElementById("general-number")||{}).value||s.number;try{localStorage.setItem(n,u),localStorage.setItem(a,g),localStorage.setItem(o,w)}catch{}window._pearnlyGeneral={tz:u,date_format:g,number_format:w},l&&(l.textContent=t("msg-saved")||"已保存")}catch{l&&(l.textContent=t("msg-save-failed")||"保存失败",l.classList.add("error"))}finally{c.disabled=!1,c.innerHTML=d,setTimeout(function(){l&&(l.textContent="")},3e3)}}function f(){const c=document.getElementById("btn-save-general");if(!c){setTimeout(f,200);return}c._pearnlyGenBound||(c._pearnlyGenBound=!0,c.addEventListener("click",r),p())}function i(){p();const c=document.getElementById("general-lang");if(c){const l=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";c.value=l}}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",f):f(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("settings-general",i)})();(function(){const e="mrpilot_nav_collapsed",n={ocr:"sales",history:"sales",reconcile:"sales","sales-invoices":"sales",receivables:"sales",vouchers:"expense"};function a(){try{const r=localStorage.getItem(e);return r?JSON.parse(r):{}}catch{return{}}}function o(r){try{localStorage.setItem(e,JSON.stringify(r))}catch{}}function s(){const r=a();document.querySelectorAll(".nav-collapsible").forEach(function(f){const i=f.dataset.collapsible;r[i]?f.classList.add("collapsed"):f.classList.remove("collapsed")})}function p(r){const f=a();f[r]=!f[r],o(f),s()}(function(){const f=a();let i=!1;f.sales===void 0&&(f.sales=!1,i=!0),f.expense===void 0&&(f.expense=!0,i=!0),i&&o(f)})(),s(),document.querySelectorAll(".nav-group-toggle").forEach(function(r){r.addEventListener("click",function(){p(r.dataset.toggleGroup)})}),window.expandNavGroupForRoute=function(r){const f=n[r];if(!f)return;const i=a();i[f]&&(i[f]=!1,o(i),s())}})();const ca=`
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
    </div>`;function It(){const e=document.getElementById("help-modal");if(!e||e.children.length)return;e.innerHTML=ca;const n=window._currentLang||"th",a=window.I18N&&window.I18N[n]||{};e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[s]&&(o.textContent=a[s])})}document.readyState,It();(function(){function e(){const n=document.getElementById("help-modal"),a=document.getElementById("help-modal-close");n&&(a&&!a.dataset.bound&&(a.addEventListener("click",function(){n.style.display="none"}),a.dataset.bound="1"),n.dataset.maskBound||(n.addEventListener("click",function(o){o.target===n&&(n.style.display="none")}),n.dataset.maskBound="1"),window._helpModalEscBound||(document.addEventListener("keydown",function(o){o.key==="Escape"&&n.style.display==="flex"&&(n.style.display="none")}),window._helpModalEscBound=!0))}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",e):e()})();(function(){const e={line:"line",folder:"folder",gmail:"email",erp:"erp",alert:"alert"};document.addEventListener("click",function(n){const a=n.target.closest(".int-btn-configure");if(!a)return;const o=a.closest(".integration-row"),s=o?o.dataset.intAnchor:null;if(s&&e[s]){const p=o.querySelector(".int-name"),r=p?(p.textContent||p.innerText||"").trim():"配置";typeof window.openIntegrationDrawer=="function"&&window.openIntegrationDrawer(e[s],r)}})})();let we=[];window._erpEndpoints=we;let Ne=null;async function Ze(){try{const e=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(e.status===401){localStorage.removeItem("mrpilot_token");const a=await e.json().catch(()=>({}));if((typeof a.detail=="string"?a.detail:a.detail&&a.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}we=(await e.json()).items||[],window._erpEndpoints=we,Kt()}catch(e){console.error("load endpoints failed",e)}}window._refreshErpEndpointsCache=function(){return Ze()};async function Gt(){const e=document.getElementById("erp-today-stats");if(e){e.innerHTML="";try{const n=await fetch("/api/erp/stats/today",{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=a.total||0,s=a.success||0,p=a.failed||0,r=a.auto_cnt||0;if(o===0){e.innerHTML=`<span class="erp-today-empty">${escapeHtml(t("erp-today-none"))}</span>`;return}const f=[];f.push(`<span class="erp-today-item"><strong>${o}</strong> ${escapeHtml(t("erp-today-total"))}</span>`),s>0&&f.push(`<span class="erp-today-item ok"><strong>${s}</strong> ${escapeHtml(t("erp-today-success"))}</span>`),p>0&&f.push(`<span class="erp-today-item fail"><strong>${p}</strong> ${escapeHtml(t("erp-today-failed"))}</span>`),r>0&&f.push(`<span class="erp-today-item auto"><strong>${r}</strong> ${escapeHtml(t("erp-today-auto"))}</span>`),e.innerHTML=f.join("")}catch(n){console.warn("loadErpTodayStats failed",n)}}}function Kt(){const e=document.getElementById("erp-endpoints-list"),n=document.getElementById("erp-status-summary"),a=document.getElementById("btn-add-endpoint");if(!e){console.warn("erp-endpoints-list 容器不存在");return}if(a&&_userInfo){const s=_userInfo.endpoints_limit;s!==-1&&we.length>=s?(a.disabled=!0,a.title=t("ep-limit-reached",{limit:s}),a.classList.add("btn-disabled-plus")):(a.disabled=!1,a.title="",a.classList.remove("btn-disabled-plus"))}if(we.length===0){e.innerHTML=`<div class="erp-empty">${escapeHtml(t("ep-list-empty"))}</div>`,n&&(n.textContent=t("auto-status-none"),n.className="auto-status-pill none");return}const o=we.some(s=>s.auto_push&&s.enabled);if(n&&(n.textContent=t("auto-status-active",{n:we.length,mode:o?t("auto-status-on"):t("auto-status-off")}),n.className="auto-status-pill "+(o?"active":"ready")),Gt(),e.innerHTML=we.map(s=>{const p=s.config||{},r=escapeHtml(p.url||"");p._token_set;const f=s.enabled!==!1,i=[];s.is_default&&i.push(`<span class="ep-badge default">${escapeHtml(t("ep-default"))}</span>`),s.auto_push&&i.push(`<span class="ep-badge auto">${escapeHtml(t("ep-auto-push-on"))}</span>`),f||i.push(`<span class="ep-badge disabled">${escapeHtml(t("ep-disabled"))}</span>`);const c=[];return s.success_count>0&&c.push(`<span class="ep-stat ok">${escapeHtml(t("ep-success",{n:s.success_count}))}</span>`),s.failure_count>0&&c.push(`<span class="ep-stat fail">${escapeHtml(t("ep-failure",{n:s.failure_count}))}</span>`),`
            <div class="erp-endpoint" data-ep-id="${escapeHtml(s.id)}">
                <div class="ep-main">
                    <div class="ep-title-row">
                        <div class="ep-name">${escapeHtml(s.name)}</div>
                        <div class="ep-badges">${i.join("")}</div>
                    </div>
                    <div class="ep-url">${r||"-"}</div>
                    <div class="ep-stats">${c.join(" · ")}</div>
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
        `}).join(""),_userInfo&&_userInfo.endpoints_limit!==-1){const s=we.length,p=_userInfo.endpoints_limit,r=_userInfo.plan,f=document.createElement("div");f.className="erp-limit-hint",r==="free"?f.innerHTML=`${escapeHtml(t("ep-free-limit-hint",{used:s,limit:p}))} <a data-upgrade="plus">${escapeHtml(t("upgrade-to-plus"))}</a>`:f.textContent=t("ep-plus-limit-hint",{used:s,limit:p}),e.appendChild(f)}}function da(e){Ne=e||null;const n=document.getElementById("endpoint-modal"),a=document.getElementById("endpoint-modal-title");a.textContent=e?t("ep-modal-title-edit"):t("ep-modal-title-new");const o=document.getElementById("ep-name"),s=document.getElementById("ep-url"),p=document.getElementById("ep-token"),r=document.getElementById("ep-is-default"),f=document.getElementById("ep-auto-push"),i=document.getElementById("ep-test-result");i.style.display="none",i.textContent="";const c=document.getElementById("ep-save-error");if(c&&c.remove(),e){const d=we.find(u=>u.id===e);if(!d)return;o.value=d.name||"",s.value=(d.config||{}).url||"",p.value=(d.config||{})._token_set&&d.config.token||"",p.placeholder=(d.config||{})._token_set?"（已保存 · 留空保持不变）":t("ep-token-ph"),r.checked=!!d.is_default,f.checked=!!d.auto_push}else o.value="",s.value="",p.value="",p.placeholder=t("ep-token-ph"),r.checked=we.length===0,f.checked=!0;const l=f.closest(".form-switch-row");if(f.disabled=!1,l){l.classList.remove("disabled-plus"),l.title="",l.style.cursor="",l.onclick=null;const d=l.querySelector(".plus-badge");d&&d.remove()}n.style.display="",setTimeout(()=>o.focus(),50)}function Jt(){document.getElementById("endpoint-modal").style.display="none",Ne=null;const e=document.getElementById("ep-save-error");e&&e.remove()}function Yt(e){if(!e)return"";let n=e.trim();const a=n.search(/\s/);return a>=0&&(n=n.slice(0,a)),n}function Wt(){const e=document.getElementById("ep-name").value.trim(),n=Yt(document.getElementById("ep-url").value),a=document.getElementById("ep-token").value,o=document.getElementById("ep-is-default").checked,s=document.getElementById("ep-auto-push").checked,p={url:n};return a&&(p.token=a),{name:e,url:n,tokenVal:a,isDefault:o,autoPush:s,config:p}}async function pa(){const{url:e,config:n}=Wt(),a=document.getElementById("ep-test-result");if(!e){a.style.display="",a.className="form-test-result fail",a.textContent=t("ep-required");return}a.style.display="",a.className="form-test-result running",a.textContent=t("ep-test-running");try{const s=await(await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({adapter:"webhook",config:n})})).json();s.success?(a.className="form-test-result ok",a.textContent=t("ep-test-ok",{status:s.http_status,ms:s.elapsed_ms})):(a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:s.error_msg||"unknown"}))}catch(o){a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:o.message})}}async function ua(){const e=Wt(),n=document.getElementById("ep-save-error");if(n&&(n.style.display="none"),!e.name||!e.url){Lt(t("ep-required"));return}const a={name:e.name,adapter:"webhook",config:e.config,is_default:e.isDefault,auto_push:e.autoPush},o=document.getElementById("btn-ep-save"),s=o.innerHTML;o.disabled=!0,o.classList.add("loading");try{let p;if(Ne?p=await fetch(`/api/erp/endpoints/${encodeURIComponent(Ne)}`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}):p=await fetch("/api/erp/endpoints",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}),!p.ok){const f=(await p.json().catch(()=>({}))).detail||`HTTP ${p.status}`;throw new Error(typeof f=="string"?f:JSON.stringify(f))}Jt(),showToast(t("ep-save-ok")),Ze()}catch(p){Lt(`${t("ep-save-fail")} · ${p.message||"unknown"}`)}finally{o.disabled=!1,o.classList.remove("loading"),o.innerHTML=s}}function Lt(e){let n=document.getElementById("ep-save-error");if(!n){const a=document.querySelector("#endpoint-modal .modal-foot");if(!a)return;n=document.createElement("div"),n.id="ep-save-error",n.className="ep-inline-error",a.parentNode.insertBefore(n,a)}n.textContent=e,n.style.display=""}async function fa(e){const n=we.find(o=>o.id===e);if(!(!n||!await showConfirm(t("ep-delete-confirm",{name:n.name}),{danger:!0})))try{if(!(await fetch(`/api/erp/endpoints/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showToast(t("ep-delete-ok")),Ze()}catch{showToast(t("ep-save-fail"),"fail")}}window.loadErpEndpoints=Ze;window.loadErpTodayStats=Gt;window.renderErpEndpointsList=Kt;window.openEndpointModal=da;window.closeEndpointModal=Jt;window.saveEndpoint=ua;window.deleteEndpoint=fa;window.testEndpointConnection=pa;window._sanitizeUrl=Yt;async function Xt(e){if(e=(e||"").trim(),!!e)try{await navigator.clipboard.writeText(e),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{try{const a=document.createElement("textarea");a.value=e,a.style.position="fixed",a.style.opacity="0",document.body.appendChild(a),a.select(),document.execCommand("copy"),a.remove(),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{showToast(t("erp-doc-copy-fail"),"error")}}}async function ma(e){const n=document.createElement("div");n.className="log-detail-modal",n.innerHTML=`
        <div class="log-detail-box">
            <div class="log-detail-loading">${escapeHtml(t("log-detail-loading"))}</div>
        </div>
    `,document.body.appendChild(n),n.addEventListener("click",async a=>{if(a.target===n||a.target.classList.contains("log-detail-close")){n.remove();return}const o=a.target.closest("[data-receipt-copy]");if(o){Xt(o.dataset.receiptCopy);return}const s=a.target.closest("[data-receipt-action]");if(s){const p=s.dataset.receiptAction;p==="retry"?window.retryPushLog(s.dataset.logId):p==="exceptions"?typeof routeTo=="function"&&routeTo("exceptions"):p==="mappings"&&typeof routeTo=="function"&&routeTo("integrations"),n.remove();return}});try{const a=await fetch(`/api/erp/logs/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!a.ok){n.remove();return}const o=await a.json(),s=window._erpEndpoints.find(C=>C.id===o.endpoint_id),p=o.endpoint_name||(s?s.name:o.endpoint_id?t("erp-log-endpoint-deleted"):"-"),r=(o.endpoint_adapter||s&&s.adapter||"").toLowerCase(),f=new Date(o.created_at).toLocaleString(),i=o.trigger==="auto"?t("log-tag-auto"):o.trigger==="retry"?t("log-tag-retry"):t("log-tag-manual"),c=o.request_body?JSON.stringify(o.request_body,null,2):t("erp-receipt-no-tech"),l=o.response_body||t("erp-receipt-no-tech"),d=o.status==="success";let u=typeof l=="string"?l:JSON.stringify(l,null,2);if(d)try{const C=typeof o.response_body=="string"?JSON.parse(o.response_body):o.response_body||{},P=C.row_count||(Array.isArray(C.imported_rows)?C.imported_rows.length:0);P>0&&(u=t("log-push-rows").replace("{n}",String(P)))}catch{}const g=(o.external_doc_no||"").trim(),w=(o.external_url||"").trim(),$=(o.external_doc_hint||"").trim(),E=(o.ocr_buyer_name||"").trim()||o.client_name||"-",_=o.seller_name||"-";let B="-";const q=Number(o.total_amount);o.total_amount!=null&&o.total_amount!==""&&!isNaN(q)&&(B=q.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}));const H=d?t("erp-receipt-title-ok"):t("erp-receipt-title-fail"),F=d?"✓":"✗",A=[],y=(C,P)=>{A.push(`
                <div class="erp-receipt-row">
                    <span class="erp-receipt-key">${escapeHtml(C)}</span>
                    <span class="erp-receipt-val">${P}</span>
                </div>`)};if(y(t("erp-receipt-invoice-no"),`<strong>${escapeHtml(o.invoice_no||"-")}</strong>`),y(t("erp-receipt-erp-name"),escapeHtml(p)),d){let C;g?C=`<strong class="erp-receipt-docno">${escapeHtml(g)}</strong><button class="erp-receipt-copy-btn" type="button" data-receipt-copy="${escapeHtml(g)}" title="${escapeHtml(t("erp-doc-copy-tip"))}">${escapeHtml(t("erp-receipt-copy-btn"))}</button>`:C=`<span class="erp-receipt-docno-missing">${escapeHtml(t("erp-log-doc-missing"))}</span>`,y(t("erp-receipt-doc-no"),C)}y(t("erp-receipt-client"),escapeHtml(E)),y(t("erp-receipt-seller"),escapeHtml(_)),d&&y(t("erp-receipt-amount"),escapeHtml(B)),y(t("erp-receipt-time"),escapeHtml(f)),y(t("erp-receipt-elapsed"),escapeHtml((o.elapsed_ms!=null?o.elapsed_ms:"-")+"ms"));let v="";d&&w?v=`<a class="erp-receipt-primary-btn" href="${escapeHtml(w)}" target="_blank" rel="noopener">${escapeHtml(t("erp-receipt-open-erp"))}</a>`:d&&g&&(v=`<button class="erp-receipt-primary-btn" type="button" data-receipt-copy="${escapeHtml(g)}">${escapeHtml(t("erp-receipt-copy-docno"))}</button>`);let b="";if(d&&g&&$){const C="erp-receipt-hint-"+$,P=t(C);P&&P!==C&&(b=`<div class="erp-receipt-hint"><svg class="erp-receipt-hint-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span>${escapeHtml(P)}</span></div>`)}let L="";if(!d){const C=(o.error_msg||"").match(/ERR_[A-Z0-9_]+/),P=C?C[0]:"",I=typeof currentLang=="string"&&currentLang||window._currentLang||"th",Y=o.error_friendly&&o.error_friendly[I]||(o.error_msg?humanizeError(o.error_msg):t("erp-receipt-no-error")),G=/ERR_NO_CUSTOMER_MAPPING|ERR_NO_CLIENT|ERR_NO_SEED_CUSTOMER|ERR_NO_SEED_PRODUCT/.test(o.error_msg||""),W=!!(o.history_id&&o.endpoint_id),te=[];te.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="exceptions">${escapeHtml(t("erp-receipt-act-exceptions"))}</button>`),G&&te.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="mappings">${escapeHtml(t("erp-receipt-act-mapping"))}</button>`),W&&te.push(`<button class="erp-receipt-action-btn primary" type="button" data-receipt-action="retry" data-log-id="${escapeHtml(o.id)}">${escapeHtml(t("erp-receipt-act-retry"))}</button>`),L=`
                <div class="erp-receipt-fail-reason-label">${escapeHtml(t("erp-receipt-fail-reason"))}</div>
                <div class="erp-receipt-fail-box">
                    ${P?`<div class="erp-receipt-errcode">${escapeHtml(P)}</div>`:""}
                    <div class="erp-receipt-friendly">${escapeHtml(Y)}</div>
                </div>
                <div class="erp-receipt-actions-label">${escapeHtml(t("erp-receipt-suggest"))}</div>
                <div class="erp-receipt-actions">${te.join("")}</div>`}n.querySelector(".log-detail-box").innerHTML=`
            <div class="log-detail-head">
                <div class="log-detail-title">
                    <span class="log-detail-status-icon ${d?"ok":"fail"}">${F}</span>
                    ${escapeHtml(H)}
                    <span class="log-tag ${o.trigger}">${escapeHtml(i)}</span>
                </div>
                <button class="log-detail-close" type="button">✕</button>
            </div>

            <div class="erp-receipt-body">
                ${A.join("")}
            </div>

            ${b}
            ${v?`<div class="erp-receipt-primary-wrap">${v}</div>`:""}
            ${L}

            <details class="log-detail-collapsible">
                <summary>${escapeHtml(t("erp-receipt-tech-toggle"))}</summary>
                <div class="log-detail-meta" style="margin-top:8px;">
                    <span>HTTP ${o.http_status||"-"}</span>
                    <span>${o.elapsed_ms}ms</span>
                    <span>${escapeHtml(t("log-detail-attempt",{n:o.attempt||1}))}</span>
                </div>
                <div class="log-detail-section" style="margin-top:12px;">
                    <div class="log-detail-label">${escapeHtml(t("log-detail-request-human"))}</div>
                    <pre>${escapeHtml(c)}</pre>
                </div>
                <div class="log-detail-section">
                    <div class="log-detail-label">${escapeHtml(t("log-detail-response-human"))}</div>
                    <pre>${escapeHtml(u)}</pre>
                </div>
            </details>
        `}catch(a){console.error(a),n.remove()}}window.copyErpDocNo=Xt;window.showLogDetail=ma;let Ie={key:"all",val:""},Ee=new Set;window._erpSelected=Ee;async function Fe(e){const n=document.getElementById("erp-logs-list");if(n){e||(n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`),window.loadErpTodayStats();try{const a=new URLSearchParams({limit:"30"});Ie.key==="status"&&a.set("status",Ie.val),Ie.key==="trigger"&&a.set("trigger",Ie.val),Ie.key==="adapter"&&a.set("adapter",Ie.val);const o=await fetch(`/api/erp/logs?${a}`,{headers:{Authorization:"Bearer "+token}});if(!o.ok){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const p=(await o.json()).items||[];if(window._erpLogPollTimer&&(clearTimeout(window._erpLogPollTimer),window._erpLogPollTimer=null),p.some(function(c){return c.status==="pending"})&&(window._erpLogPollTimer=setTimeout(function(){Fe(!0)},4e3)),p.length===0){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-empty"))}</div>`;return}const f='<div class="erp-log-row erp-log-row-header" data-log-header>'+(p.filter(function(c){var l=c.status==="failed"&&c.next_retry_at&&new Date(c.next_retry_at).getTime()>Date.now()-6e4;return!l}).map(function(c){return c.id}).length>0?`<input type="checkbox" class="erp-log-cb erp-log-cb-all" data-log-select-all title="${escapeHtml(t("erp-log-select-all-tip"))}">`:'<span class="erp-log-cb-spacer"></span>')+`<span class="log-time">${escapeHtml(t("erp-log-col-time"))}</span><span class="log-status">${escapeHtml(t("erp-log-col-status"))}</span><span class="log-tag-header">${escapeHtml(t("erp-log-col-trigger"))}</span><span class="log-invoice">${escapeHtml(t("erp-log-col-invoice"))}</span><span class="log-workspace">${escapeHtml(t("erp-log-col-workspace"))}</span><span class="log-client">${escapeHtml(t("erp-log-col-client"))}</span><span class="log-seller">${escapeHtml(t("erp-log-col-seller"))}</span><span class="log-erp">${escapeHtml(t("erp-log-col-erp"))}</span><span class="log-doc">${escapeHtml(t("erp-log-col-doc"))}</span><span class="log-http">${escapeHtml(t("erp-log-col-http"))}</span><span class="log-elapsed">${escapeHtml(t("erp-log-col-elapsed"))}</span><span class="log-actions"></span></div>`;n.innerHTML=f+p.map(c=>{const l=new Date(c.created_at),d=`${String(l.getMonth()+1).padStart(2,"0")}-${String(l.getDate()).padStart(2,"0")} ${String(l.getHours()).padStart(2,"0")}:${String(l.getMinutes()).padStart(2,"0")}`,u=c.status==="failed"&&c.next_retry_at&&new Date(c.next_retry_at).getTime()>Date.now()-6e4;let g,w,$;c.status==="pending"?(g="retrying",w="⟳",$=t("erp-status-pending")):c.status==="success"?(g="ok",w="✓",$=t("erp-status-success")):c.status==="skipped_dup"?(g="skipped",w="⏭",$=t("erp-status-skipped")):u?(g="retrying",w="↻",$=t("erp-status-retrying")):(g="fail",w="✗",$=t("erp-status-failed"));let E;c.trigger==="auto"?E=`<span class="log-tag auto">${escapeHtml(t("log-tag-auto"))}</span>`:c.trigger==="retry"?E=`<span class="log-tag retry">${escapeHtml(t("log-tag-retry"))}</span>`:E=`<span class="log-tag manual">${escapeHtml(t("log-tag-manual"))}</span>`;let _="";const B=c.retry_count||0,q=c.max_retries||3;if(u){const Y=new Date(c.next_retry_at).getTime()-Date.now(),G=Math.max(0,Math.round(Y/6e4)),W=G<=0?t("erp-retry-next-soon"):t("erp-retry-next-min",{n:G});_=`${t("erp-retry-attempt",{n:B,max:q})} · ${W}`}else c.status==="failed"&&B>=q&&!c.next_retry_at&&(_=t("erp-retry-exhausted",{n:B}));const H=c.status==="failed"&&!u?`<button class="log-retry-btn btn btn-icon" data-log-retry="${escapeHtml(c.id)}" title="${escapeHtml(t("log-retry-title"))}">↻</button>`:"",F=!u,A=Ee.has(c.id)?"checked":"",y=F?`<input type="checkbox" class="erp-log-cb" data-log-cb="${escapeHtml(c.id)}" ${A}>`:'<span class="erp-log-cb-spacer"></span>',v=(c.ocr_buyer_name||"").trim()||(c.client_name||"").trim(),b=v?`<span class="log-client" title="${escapeHtml(v)}">${escapeHtml(v.substring(0,18))}</span>`:`<span class="log-client log-client-empty" title="${escapeHtml(t("erp-log-client-unassigned-tip"))}">${escapeHtml(t("erp-log-client-unassigned"))}</span>`,L=c.workspace_name?`<span class="log-workspace">${escapeHtml((c.workspace_name||"").substring(0,16))}</span>`:`<span class="log-workspace log-workspace-unresolved" title="${escapeHtml(t("erp-log-ws-unresolved-tip"))}">${escapeHtml(t("erp-log-ws-unresolved"))}</span>`,C=c.endpoint_name?`<span class="log-erp">${escapeHtml((c.endpoint_name||"").substring(0,14))}</span>`:`<span class="log-erp log-erp-deleted">${escapeHtml(t("erp-log-endpoint-deleted"))}</span>`,P=(c.external_doc_no||"").trim(),I=(c.external_url||"").trim();let j;return I?j=`<span class="log-doc"><a href="${escapeHtml(I)}" target="_blank" rel="noopener" class="log-doc-open" title="${escapeHtml(P||"")}">${escapeHtml(t("erp-log-doc-open"))}</a></span>`:P?j=`<span class="log-doc log-doc-copy" data-copy-doc="${escapeHtml(P)}" title="${escapeHtml(t("erp-log-doc-copy-tip"))}">${escapeHtml(P.substring(0,18))}</span>`:c.status==="success"?j=`<span class="log-doc log-doc-missing" title="${escapeHtml(t("erp-log-doc-missing-tip"))}">${escapeHtml(t("erp-log-doc-missing"))}</span>`:j='<span class="log-doc log-doc-empty">-</span>',`
                <div class="erp-log-row ${g}" data-log-detail="${escapeHtml(c.id)}">
                    ${y}
                    <span class="log-time">${d}</span>
                    <span class="log-status" title="${escapeHtml($+(_?" · "+_:""))}">${w}</span>
                    ${E}
                    <span class="log-invoice">${escapeHtml(c.invoice_no||"-")}</span>
                    ${L}
                    ${b}
                    <span class="log-seller">${escapeHtml((c.seller_name||"").substring(0,20))}</span>
                    ${C}
                    ${j}
                    <span class="log-http">HTTP ${c.http_status||"-"}</span>
                    <span class="log-elapsed">${c.elapsed_ms}ms</span>
                    <span class="log-actions">${H}</span>
                </div>
            `}).join("");const i=new Set(p.map(c=>c.id));for(const c of Array.from(Ee))i.has(c)||Ee.delete(c);window._refreshErpBatchBar()}catch(a){console.error("load erp logs failed",a),n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}async function Qt(e){try{const n=await fetch(`/api/erp/logs/${encodeURIComponent(e)}/retry`,{method:"POST",headers:{Authorization:"Bearer "+token}}),a=await n.json().catch(()=>({}));n.ok&&a.ok?showToast(t("log-retry-ok"),"success"):showToast(t("log-retry-fail")+" · HTTP "+(a.http_status||n.status),"error"),Fe(),window.loadErpEndpoints()}catch{showToast(t("log-retry-fail"),"error")}}(function(){document.getElementById("btn-add-endpoint").addEventListener("click",()=>window.openEndpointModal(null)),document.getElementById("endpoint-modal-close").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-cancel").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-test").addEventListener("click",window.testEndpointConnection),document.getElementById("btn-ep-save").addEventListener("click",window.saveEndpoint),document.getElementById("ep-url").addEventListener("blur",n=>{const a=window._sanitizeUrl(n.target.value);a!==n.target.value.trim()&&(n.target.value=a)}),document.addEventListener("click",n=>{const a=n.target.closest("[data-ep-edit]"),o=n.target.closest("[data-ep-del]");a&&window.openEndpointModal(a.dataset.epEdit),o&&window.deleteEndpoint(o.dataset.epDel);const s=n.target.closest("[data-log-retry]");if(s){n.stopPropagation(),Qt(s.dataset.logRetry);return}const p=n.target.closest("[data-log-cb]");if(p){n.stopPropagation();const l=p.dataset.logCb;p.checked?Ee.add(l):Ee.delete(l),window._refreshErpBatchBar();return}const r=n.target.closest("[data-log-select-all]");if(r){n.stopPropagation();const l=r.checked;document.querySelectorAll("[data-log-cb]").forEach(function(u){u.checked=l;const g=u.dataset.logCb;l?Ee.add(g):Ee.delete(g)}),window._refreshErpBatchBar();return}if(n.target.closest("#btn-erp-batch-retry")){n.stopPropagation(),window._runErpBatchRetry();return}if(n.target.closest("#btn-erp-batch-clear")){n.stopPropagation(),Ee.clear(),document.querySelectorAll(".erp-log-cb").forEach(l=>{l.checked=!1}),window._refreshErpBatchBar();return}const f=n.target.closest("[data-log-detail]");if(f){if(n.target.closest("[data-log-cb]"))return;const l=n.target.closest("[data-copy-doc]");if(l){n.stopPropagation(),window.copyErpDocNo(l.dataset.copyDoc);return}if(n.target.closest(".log-doc-open"))return;window.showLogDetail(f.dataset.logDetail);return}const i=n.target.closest(".chip-filter");if(i){document.querySelectorAll("#erp-logs-filters .chip-filter").forEach(l=>l.classList.remove("active")),i.classList.add("active"),Ie={key:i.dataset.filterKey,val:i.dataset.filterVal},Fe();return}if(n.target.closest("#btn-refresh-logs")){const l=n.target.closest("#btn-refresh-logs");l.classList.add("spinning"),setTimeout(()=>l.classList.remove("spinning"),600),Fe();return}const c=n.target.closest(".auto-nav-item");if(c&&c.dataset.autoTab){switchAutomationTab(c.dataset.autoTab);return}})})();window.loadErpLogs=Fe;window.retryPushLog=Qt;function Zt(){const e=document.getElementById("erp-logs-batch-bar"),n=document.getElementById("erp-logs-batch-count"),a=document.querySelector("[data-log-select-all]");if(a){const p=document.querySelectorAll("[data-log-cb]").length,r=window._erpSelected.size;r===0?(a.checked=!1,a.indeterminate=!1):r>=p?(a.checked=!0,a.indeterminate=!1):(a.checked=!1,a.indeterminate=!0)}if(!e||!n)return;const o=window._erpSelected.size;if(o===0){e.style.display="none";return}e.style.display="",n.textContent=t("erp-batch-selected",{n:o})}async function en(){console.info("[ErpBatch] retry triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-confirm",{n:e.length})))try{const a=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!a.ok){showToast(t("erp-logs-error"),"error");return}const o=await a.json(),s=t("erp-batch-result",{ok:o.succeeded||0,fail:o.failed||0,skip:o.skipped||0}),p=o.failed&&o.failed>0?"warn":"success";showToast(s,p),window._erpSelected.clear(),window.loadErpLogs()}catch(a){console.error("batch retry failed",a),showToast(t("erp-logs-error"),"error")}}async function tn(){console.info("[ErpBatch] delete triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-delete-confirm",{n:e.length}),{danger:!0}))try{const o=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!o.ok){showToast(t("erp-logs-error"),"error");return}const s=await o.json();e.forEach(function(p){var r=document.querySelector('[data-log-detail="'+p+'"]');r&&r.remove()});var a=document.getElementById("erp-logs-batch-bar");a&&(a.style.display="none"),showToast(t("erp-batch-delete-result",{n:s.deleted||0,skip:s.skipped||0}),s.deleted>0?"success":"warn"),window._erpSelected.clear(),setTimeout(window.loadErpLogs,500)}catch(o){console.error("batch delete failed",o),showToast(t("erp-logs-error"),"error")}}(function(){function n(){var a=document.getElementById("btn-erp-batch-retry"),o=document.getElementById("btn-erp-batch-delete"),s=document.getElementById("btn-erp-batch-clear");a&&!a.dataset.boundDirect&&(a.addEventListener("click",function(p){p.preventDefault(),p.stopPropagation(),en()}),a.dataset.boundDirect="1"),o&&!o.dataset.boundDirect&&(o.addEventListener("click",function(p){p.preventDefault(),p.stopPropagation(),tn()}),o.dataset.boundDirect="1"),s&&!s.dataset.boundDirect&&(s.addEventListener("click",function(p){p.preventDefault(),p.stopPropagation(),window._erpSelected.clear(),document.querySelectorAll(".erp-log-cb").forEach(function(r){r.checked=!1}),Zt()}),s.dataset.boundDirect="1")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n(),setTimeout(n,2e3),setTimeout(n,5e3),window._bindErpBatchButtons=n})();window._refreshErpBatchBar=Zt;window._runErpBatchRetry=en;window._runErpBatchDelete=tn;(function(){let e=null,n=!1;function a(){if(e)return e;const f=document.createElement("div");f.id="line-email-modal",f.style.cssText="position:fixed;inset:0;background:rgba(10,14,39,0.85);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;",f.innerHTML=`
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
        `,document.body.appendChild(f),e=f;const i=f.querySelector("#line-email-input"),c=f.querySelector("#line-email-submit-btn"),l=f.querySelector("#line-email-err");async function d(){l.textContent="";const u=(i.value||"").trim().toLowerCase();if(!u||u.indexOf("@")<0||u.split("@")[1].indexOf(".")<0){l.textContent=t("line-email-err-invalid");return}c.disabled=!0,c.style.opacity="0.6";try{const g=await fetch("/api/me/line_complete_email",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},body:JSON.stringify({email:u})});if(!g.ok)throw new Error("http_"+g.status);const w=await g.json();w.token&&localStorage.setItem("mrpilot_token",w.token),typeof showToast=="function"&&showToast(w.merged?t("line-email-merged-toast"):t("line-email-saved-toast"),"success"),setTimeout(function(){window.location.reload()},600)}catch{l.textContent=t("line-email-err-failed"),c.disabled=!1,c.style.opacity="1"}}return c.addEventListener("click",d),i.addEventListener("keydown",function(u){u.key==="Enter"&&d()}),f}function o(){if(!e)return;const f=e.querySelector("#line-email-title-h"),i=e.querySelector("#line-email-sub-p"),c=e.querySelector("#line-email-input"),l=e.querySelector("#line-email-submit-btn");f&&(f.textContent=t("line-email-title")),i&&(i.textContent=t("line-email-sub")),c&&(c.placeholder=t("line-email-placeholder")),l&&(l.textContent=t("line-email-submit"))}function s(){a(),o(),e.style.display="flex",n=!0;const f=e.querySelector("#line-email-input");f&&setTimeout(function(){f.focus()},100)}async function p(){const f=localStorage.getItem("mrpilot_token");if(f)try{const i=await fetch("/api/me/needs_email",{headers:{Authorization:"Bearer "+f}});if(!i.ok)return;const c=await i.json();c&&c.needs_email&&s()}catch{}}function r(){setTimeout(p,800)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",r):r(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("line-email-modal",function(){n&&o()})})();(function(){function e(l){let d=0;return l.length>=8&&d++,l.length>=12&&d++,/[a-zA-Z]/.test(l)&&/\d/.test(l)&&d++,/[^a-zA-Z0-9]/.test(l)&&d++,Math.min(3,d)}function n(l,d){const u=document.getElementById("cpw-msg");u&&(u.textContent=l,u.className="cpw-msg "+(d||""))}function a(l){return typeof t=="function"?t(l):l}let o=!1;function s(){["cpw-old","cpw-new","cpw-confirm"].forEach(d=>{const u=document.getElementById(d);u&&(u.value="",u.setAttribute("readonly","readonly"))});const l=document.getElementById("cpw-strength-bar");l&&(l.style.width="0%",l.className="cpw-strength-bar"),n("","")}async function p(){const l=document.getElementById("btn-change-pw"),d=document.getElementById("cpw-old"),u=document.getElementById("cpw-new"),g=document.getElementById("cpw-confirm"),w=document.getElementById("cpw-strength-bar");if(!l||!d||!u||!g)return;const $=d.value,E=u.value,_=g.value;if(!$||!E||!_){n(a("settings-change-pw-empty"),"error");return}if(E.length<8){n(a("settings-change-pw-too-short"),"error");return}if(!(/[a-zA-Z]/.test(E)&&/\d/.test(E))){n(a("settings-change-pw-too-weak"),"error");return}if(E!==_){n(a("settings-change-pw-mismatch"),"error");return}l.disabled=!0;const B=l.textContent;l.textContent=a("settings-change-pw-submitting"),n("","");try{const q=localStorage.getItem("mrpilot_token"),H=await fetch("/api/me/change_password",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+q},body:JSON.stringify({old_password:$,new_password:E})}),F=await H.json().catch(()=>({}));if(H.ok&&F.ok)n(a("settings-change-pw-success"),"success"),typeof showToast=="function"&&showToast(a("settings-change-pw-success"),"success"),d.value="",u.value="",g.value="",w&&(w.style.width="0%",w.className="cpw-strength-bar");else{const A=F.detail||"";let y=a("settings-change-pw-success");A==="wrong_old_password"?y=a("settings-change-pw-wrong-old"):A==="password_too_short"?y=a("settings-change-pw-too-short"):A==="password_too_weak"?y=a("settings-change-pw-too-weak"):y=A||"Error",n(y,"error")}}catch(q){console.error("change_password",q),n("Network error","error")}finally{l.disabled=!1,l.textContent=B}}function r(){o||(o=!0,document.addEventListener("click",l=>{if(!l.target||!l.target.closest)return;const d=l.target.closest(".cpw-eye");if(d){const u=document.getElementById(d.dataset.target);u&&(u.type=u.type==="password"?"text":"password");return}if(l.target.closest("#cpw-forgot-link")){l.preventDefault(),f();return}if(l.target.closest("#btn-change-pw")){p();return}l.target.closest('.settings-nav-item[data-settings-tab="account"], .settings-nav-item[data-tab="account"], .settings-nav-item[data-tab="security"]')&&setTimeout(s,100)}),document.addEventListener("input",l=>{if(l.target&&l.target.id==="cpw-new"){const d=document.getElementById("cpw-strength-bar");if(!d)return;const u=e(l.target.value),g=["0%","33%","66%","100%"],w=["","weak","medium","strong"];d.style.width=g[u],d.className="cpw-strength-bar "+w[u]}}),document.addEventListener("focusin",l=>{l.target&&["cpw-old","cpw-new","cpw-confirm"].includes(l.target.id)&&l.target.removeAttribute("readonly")}),document.getElementById("cpw-old")&&s())}function f(){const l=window._userInfo||(typeof _userInfo<"u"?_userInfo:null),d=l&&l.username?l.username:"",u=i(d);let g=document.getElementById("cpw-forgot-overlay");g&&g.remove(),g=document.createElement("div"),g.id="cpw-forgot-overlay",g.className="cpw-forgot-overlay",g.innerHTML=`
            <div class="cpw-forgot-modal">
                <div class="cpw-forgot-head">
                    <div class="cpw-forgot-title">${c(a("cpw-forgot-title"))}</div>
                    <button class="cpw-forgot-close" id="cpw-forgot-close" aria-label="close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="cpw-forgot-body">
                    <p class="cpw-forgot-desc">${c(a("cpw-forgot-desc"))}</p>
                    <div class="cpw-forgot-email">${c(u)}</div>
                    <p class="cpw-forgot-tip">${c(a("cpw-forgot-tip"))}</p>
                    <div class="cpw-forgot-msg" id="cpw-forgot-msg"></div>
                </div>
                <div class="cpw-forgot-foot">
                    <button class="btn btn-ghost" id="cpw-forgot-cancel">${c(a("cpw-forgot-cancel"))}</button>
                    <button class="btn btn-primary" id="cpw-forgot-send">${c(a("cpw-forgot-send"))}</button>
                </div>
            </div>
        `,document.body.appendChild(g);const w=()=>g.remove();g.querySelector("#cpw-forgot-close").addEventListener("click",w),g.querySelector("#cpw-forgot-cancel").addEventListener("click",w),g.addEventListener("click",$=>{$.target===g&&w()}),g.querySelector("#cpw-forgot-send").addEventListener("click",async()=>{const $=g.querySelector("#cpw-forgot-send"),E=g.querySelector("#cpw-forgot-msg");$.disabled=!0;const _=$.textContent;$.textContent=a("cpw-forgot-sending");try{const B=await fetch("/api/auth/forgot_password",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:d})}),q=await B.json().catch(()=>({}));B.ok?(E.textContent=a("cpw-forgot-success"),E.className="cpw-forgot-msg success",$.style.display="none",g.querySelector("#cpw-forgot-cancel").textContent=a("cpw-forgot-close-btn")):(E.textContent=q.detail||a("cpw-forgot-fail"),E.className="cpw-forgot-msg error",$.disabled=!1,$.textContent=_)}catch{E.textContent=a("cpw-forgot-fail"),E.className="cpw-forgot-msg error",$.disabled=!1,$.textContent=_}})}function i(l){if(!l||!l.includes("@"))return l||"";const[d,u]=l.split("@");return d.length<=2?d+"****@"+u:d.slice(0,2)+"****@"+u}function c(l){return l==null?"":String(l).replace(/[&<>"']/g,d=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[d])}document.readyState==="complete"||document.readyState==="interactive"?r():document.addEventListener("DOMContentLoaded",r)})();(function(){let e=null,n=!1;async function a(){if(n)return;const s=localStorage.getItem("mrpilot_token");if(s){n=!0;try{const p=await fetch("/api/me",{headers:{Authorization:"Bearer "+s},cache:"no-store"});if(p.status===401){const r=await p.json().catch(()=>({})),f=r&&r.detail;let i="";if(typeof f=="string"?i=f:f&&typeof f=="object"&&(i=f.code||""),console.warn("[heartbeat] session revoked",i),localStorage.removeItem("mrpilot_token"),e&&(clearInterval(e),e=null),i==="auth.session_revoked")try{_showSessionRevokedModal()}catch{window.location.href="/"}else{const c=i==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";try{typeof showToast=="function"&&typeof t=="function"?showToast(t(c),"error"):alert("Session expired")}catch{}setTimeout(()=>{window.location.href="/"},1500)}}}catch{}finally{n=!1}}}function o(){e&&clearInterval(e),e=setInterval(a,15e3)}localStorage.getItem("mrpilot_token")&&o(),window.addEventListener("focus",a),document.addEventListener("visibilitychange",function(){document.hidden||a()}),window._sessionCheck=a})();async function et(){const e=document.getElementById("team-loading"),n=document.getElementById("team-list"),a=document.getElementById("team-empty"),o=document.getElementById("team-count");if(n){e&&(e.style.display=""),n.style.display="none",a&&(a.style.display="none");try{const s=await apiGet("/api/team/employees"),p=s&&s.employees||[];if(e&&(e.style.display="none"),o&&(o.textContent=(t("team-count")||"共 {n} 名员工").replace("{n}",p.length)),p.length===0){a&&(a.style.display="");return}n.style.display="",n.innerHTML=p.map(r=>{const f=r.last_login_at?new Date(r.last_login_at).toLocaleDateString():t("team-never-login")||"从未登录",i=r.is_active===!1?"team-status-off":"team-status-on",c=r.is_active===!1?t("team-status-disabled")||"已禁用":t("team-status-active")||"正常",l=r.email?`<span class="team-meta-sep">·</span><span>${escapeHtml(r.email)}</span>`:"";return`
            <div class="team-card" data-employee-id="${escapeHtml(r.id)}">
                <div class="team-card-main">
                    <div class="team-avatar">${escapeHtml((r.username||"?")[0].toUpperCase())}</div>
                    <div class="team-info">
                        <div class="team-name">${escapeHtml(r.username||"")}</div>
                        <div class="team-meta">
                            <span class="team-status-dot ${i}"></span>
                            <span>${escapeHtml(c)}</span>
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml(t("team-last-login")||"上次登录")}: ${escapeHtml(f)}</span>
                            ${l}
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
            </div>`}).join("")}catch(s){console.error("loadTeamList failed:",s),e&&(e.textContent=t("team-load-failed")||"加载失败")}}}async function va(){document.querySelectorAll(".add-emp-overlay").forEach(o=>o.remove());const e=document.createElement("div");e.className="add-emp-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const o=document.getElementById("add-emp-username");o&&o.focus()},200);function n(){e.classList.remove("show"),setTimeout(()=>e.remove(),220)}e.querySelector(".add-emp-close").addEventListener("click",n),e.querySelector("#add-emp-cancel").addEventListener("click",n),e.addEventListener("click",o=>{o.target===e&&n()}),e.querySelector("#add-emp-submit").addEventListener("click",async()=>{const o=document.getElementById("add-emp-username"),s=document.getElementById("add-emp-email"),p=document.getElementById("add-emp-password"),r=document.getElementById("add-emp-msg"),f=document.getElementById("add-emp-submit"),i=(o.value||"").trim(),c=(s.value||"").trim(),l=p.value||"";if(r.textContent="",r.classList.remove("error"),!i||i.length<3){r.textContent=t("team-modal-err-username")||"用户名至少 3 位",r.classList.add("error");return}if(!/^[a-zA-Z0-9_.\-]+$/.test(i)){r.textContent=t("team-modal-err-username-fmt")||"只能用字母 / 数字 / 下划线 / 点 / 横线",r.classList.add("error");return}if(c&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(c)){r.textContent=t("msg-email-invalid")||"邮箱格式不对",r.classList.add("error");return}if(l.length<8){r.textContent=t("pwd-too-short")||"密码至少 8 位",r.classList.add("error");return}if(/^\d+$/.test(l)){r.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",r.classList.add("error");return}if(!(/[a-zA-Z]/.test(l)&&/\d/.test(l))){r.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",r.classList.add("error");return}f.disabled=!0,f.textContent=t("msg-saving")||"保存中...";try{const d={username:i,password:l};c&&(d.email=c);const u=await apiPost("/api/team/employees",d),g=u?await u.json().catch(()=>({})):{};if(u&&u.ok&&g&&g.ok){showToast(t("team-added")||"员工已添加","success"),n(),et();return}const w=g&&g.detail||"unknown",$={"team.username_exists":t("team-username-exists")||"用户名已被占用","team.email_exists":t("team-email-exists")||"邮箱已被占用","team.create_failed":t("team-create-failed")||"创建失败","team.only_owner_or_super":t("team-no-permission")||"无权限","team.no_tenant":t("team-no-tenant")||"请先升级账号","pwd.too_short":t("pwd-too-short")||"密码至少 8 位","pwd.too_weak_numeric":t("pwd-too-weak-numeric")||"不能是纯数字","pwd.too_weak_common":t("pwd-too-weak-common")||"这个密码太常见 · 请换一个","pwd.too_weak":t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};r.textContent=$[w]||(t("team-create-failed")||"创建失败")+" ("+w+")",r.classList.add("error")}catch{r.textContent=t("team-create-failed")||"创建失败",r.classList.add("error")}finally{f.disabled=!1,f.textContent=t("team-add")||"添加员工"}});function a(o){o.key==="Escape"&&(n(),document.removeEventListener("keydown",a))}document.addEventListener("keydown",a)}async function ha(e,n){try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}/active`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({is_active:!!n})})).ok){et();return}showToast(t("team-toggle-failed")||"操作失败","error")}catch{showToast(t("team-toggle-failed")||"操作失败","error")}}async function ga(e,n){const o=(t("team-confirm-remove")||"确认移除员工「{name}」?他的所有识别记录会保留 · 但他将无法登录").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{danger:!0,okText:t("team-remove")}))try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){showToast(t("team-removed")||"已移除","success"),et();return}showToast(t("team-remove-failed")||"移除失败","error")}catch{showToast(t("team-remove-failed")||"移除失败","error")}}async function ba(e,n){const o=(t("team-reset-pwd-confirm")||"给员工「{name}」发送改密链接?系统将通过员工的邮箱或 LINE 发送一个 15 分钟内有效的链接 · 员工自己点链接改密码 · 您看不到密码").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{okText:t("team-reset-link-send-btn")||"发送链接"}))try{const p=await fetch(`/api/team/employees/${encodeURIComponent(e)}/reset-password`,{method:"POST",headers:{Authorization:"Bearer "+token}}),r=await p.json().catch(()=>({}));if(p.status===400&&r.detail==="team.reset_no_channel"){showToast(t("team-reset-no-channel")||"员工尚未绑定邮箱或 LINE · 请先帮员工补充邮箱再重置","error");return}if(!p.ok){showToast(t("team-reset-pwd-fail")||"发送失败","error");return}if(r.channel==="line"||r.channel==="email"){const f=t("team-reset-link-sent")||"改密链接已通过 {ch} 发送给员工 · 链接 15 分钟内有效",i=r.channel==="line"?"LINE":t("team-reset-via-email")||"邮箱";showToast(f.replace("{ch}",i),"success");return}showToast(t("team-reset-pwd-fail")||"发送失败","error")}catch{showToast(t("team-reset-pwd-fail")||"发送失败","error")}}document.addEventListener("click",e=>{if(e.target.closest("#btn-add-employee")){e.preventDefault(),va();return}const n=e.target.closest("[data-toggle-employee]");if(n){e.preventDefault(),ha(n.dataset.toggleEmployee,n.dataset.active==="false");return}const a=e.target.closest("[data-remove-employee]");if(a){e.preventDefault(),ga(a.dataset.removeEmployee,a.dataset.name||"");return}const o=e.target.closest("[data-reset-pwd-employee]");if(o){e.preventDefault(),ba(o.dataset.resetPwdEmployee,o.dataset.name||"");return}const s=e.target.closest("[data-assign-clients]");if(s){e.preventDefault(),typeof window.openAssignClientsModal=="function"&&window.openAssignClientsModal(s.dataset.assignClients,s.dataset.name||"");return}});window.loadTeamList=et;function ya(e){document.querySelectorAll(".auto-nav-item").forEach(n=>{n.classList.toggle("active",n.dataset.autoTab===e)}),document.querySelectorAll(".auto-panel").forEach(n=>{n.classList.toggle("active",n.dataset.autoPanel===e)}),e==="email"&&typeof window._loadEmailIngestPanel=="function"?(window._loadEmailIngestPanel(),typeof window._startEmailLogAutoRefresh=="function"&&window._startEmailLogAutoRefresh()):typeof window._stopEmailLogAutoRefresh=="function"&&window._stopEmailLogAutoRefresh(),e==="bank"&&typeof window._loadBankReconPanel=="function"&&window._loadBankReconPanel(),e==="linebot"&&typeof window._loadLineBotPanel=="function"&&window._loadLineBotPanel(),e==="alert"&&typeof window._loadNotificationsPanel=="function"&&window._loadNotificationsPanel(),e==="folder"&&typeof window._loadFolderWatcherPanel=="function"&&window._loadFolderWatcherPanel()}window.switchAutomationTab=ya;typeof console<"u"&&typeof console.info=="function"&&console.info("[pearnly] vite bundle loaded · dashboard + billing + test-center + workspace-switcher + recon-center + assign-clients + access-log + notifications + recon-batch + welcome-wizard + archive-settings");
//# sourceMappingURL=main.js.map
