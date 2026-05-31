const $t=`
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

`,Ht=`        <!-- ── 销项税对账面板(v118.32.0 · 屏 A) ── -->
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


`;(function(){const e=document.getElementById("page-reconcile");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=$t+Ht,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=document.getElementById("page-integrations");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const At=`
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

`,jt=`                    <!-- Tab: 邮箱抓取 (v0.17 · M6 · v93 在 Vultr 复活) -->
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
`;(function(){const e=document.getElementById("page-automation");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=At+jt,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e={"page-integration":`
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
`},n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;Object.keys(e).forEach(o=>{const s=document.getElementById(o);!s||s.dataset.wbInjected==="1"||(s.innerHTML=e[o],s.dataset.wbInjected="1",a&&a[n]&&s.querySelectorAll("[data-i18n]").forEach(u=>{const l=u.getAttribute("data-i18n");a[n][l]&&(u.textContent=a[n][l])}))})})();(function(){const e=document.getElementById("page-dashboard");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();function ze(){const e=document.getElementById("results-card");if(_results.length===0){e.classList.remove("show");return}e.classList.add("show");let n=0;_results.forEach(l=>{const k=parseFloat(l.merged_fields.total_amount);isNaN(k)||(n+=k)}),_selectedFiles&&_selectedFiles.length||_results.length;const a=_results.length,o=n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2});document.getElementById("results-head-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-value">${a}</span>
            <span class="rh-stat-label">${t("stats-invoices")}</span>
        </div>
        <div class="rh-stat">
            <span class="rh-stat-label">${t("stats-total")}</span>
            <span class="rh-stat-value">฿ ${o}</span>
        </div>
    `;let s=_results.map((l,k)=>({...l,_idx:k}));if(_searchKeyword){const l=_searchKeyword.toLowerCase();s=s.filter(k=>(k.filename||"").toLowerCase().includes(l)||(k.merged_fields.invoice_number||"").toLowerCase().includes(l))}_sortKey&&s.sort((l,k)=>{let i,p;return _sortKey==="filename"?(i=l.filename,p=k.filename):_sortKey==="invoice_no"?(i=l.merged_fields.invoice_number,p=k.merged_fields.invoice_number):_sortKey==="invoice_date"?(i=l.merged_fields.date,p=k.merged_fields.date):_sortKey==="total"?(i=parseFloat(l.merged_fields.total_amount)||0,p=parseFloat(k.merged_fields.total_amount)||0):_sortKey==="confidence"?(i=l.confidence,p=k.confidence):(i="",p=""),i<p?_sortDir==="asc"?-1:1:i>p?_sortDir==="asc"?1:-1:0});const u=document.getElementById("results-tbody");u.innerHTML=s.map((l,k)=>{const i=l.merged_fields,p=`<span class="empty-cell">${t("empty-val")}</span>`,c="conf-tip-"+(l.confidence||"low"),r="conf-"+(l.confidence||"low"),v=t(c),E=t(r);return`
            <tr data-idx="${l._idx}">
                <td class="num">${k+1}</td>
                <td class="fname" title="${escapeHtml(l.filename)}">${escapeHtml(l.filename)}</td>
                <td class="inv">${i.invoice_number?escapeHtml(i.invoice_number):p}</td>
                <td class="date">${i.date?escapeHtml(i.date):p}</td>
                <td class="amount">${i.total_amount?Number(i.total_amount).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}):p}</td>
                <td><span class="conf-badge ${l.confidence}" data-tip="${escapeHtml(v)}">${E}</span></td>
            </tr>
        `}).join(""),document.querySelectorAll("#results-table th").forEach(l=>{l.classList.remove("sort-asc","sort-desc"),l.dataset.sort===_sortKey&&l.classList.add("sort-"+_sortDir)}),u.querySelectorAll("tr").forEach(l=>{l.addEventListener("click",()=>{const k=parseInt(l.dataset.idx,10);ct(k)})})}document.querySelectorAll("#results-table th").forEach(e=>{e.classList.contains("no-sort")||e.addEventListener("click",()=>{const n=e.dataset.sort;_sortKey===n?_sortDir=_sortDir==="asc"?"desc":"asc":(_sortKey=n,_sortDir="asc"),ze()})});let at=null;document.getElementById("search-input").addEventListener("input",e=>{const n=e.target.value;document.getElementById("search-clear").style.display=n?"":"none",clearTimeout(at),at=setTimeout(()=>{_searchKeyword=n.trim(),ze(),lt()},200)});document.getElementById("search-clear").addEventListener("click",()=>{const e=document.getElementById("search-input");e.value="",_searchKeyword="",document.getElementById("search-clear").style.display="none",ze(),lt(),e.focus()});function lt(){const e=document.getElementById("search-matches");if(!e)return;if(!_searchKeyword){e.textContent="";return}const n=_searchKeyword.toLowerCase();let a=0;for(const o of _results)[o.filename,o.merged_fields?.invoice_number,o.merged_fields?.seller_name,o.merged_fields?.buyer_name].filter(Boolean).join(" ").toLowerCase().includes(n)&&a++;e.textContent=t("search-matches",{n:a})}function ct(e){_drawerIdx=e;const n=_results[e];if(!n)return;document.getElementById("drawer-title").textContent=n.filename;const a=n.engine==="cache"||n.from_cache,o=a?t("badge-cached-hint"):`${(n.elapsed_ms/1e3).toFixed(1)}s`;document.getElementById("drawer-sub").innerHTML=`
        <span>${n.page_count} ${t("pages-unit")} · ${escapeHtml(o)}</span>
        ${a?`<span class="engine-badge cached">${escapeHtml(t("badge-cached"))}</span>`:""}
        <span class="drawer-edit-count" id="drawer-edit-count-sub"></span>
    `,updateDrawerEditCount();const s=_userInfo&&_userInfo.can_edit_fields,u=_userInfo&&_userInfo.can_verify_tax,l=n.merged_fields,k=document.getElementById("drawer-body"),i=s?"":`
        <div class="drawer-readonly-banner">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="9" width="12" height="9" rx="1"/><path d="M7 9V6a3 3 0 016 0v3"/></svg>
            <span>${t("readonly-banner")}</span>
        </div>
    `,p=u?"":`<span class="tax-badge unverified" data-tip="${escapeHtml(t("tax-tip-unverified"))}">${t("tax-unverified")}</span>`;if(k.innerHTML=`
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
                ${ye("wht_amount","drawer-lbl-wht-amount",l.wht_amount,"input",s,Pt(l.wht_rate))}
            `:""}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 18V8h14v10M3 8l2-4h10l2 4M7 12h2M11 12h2"/></svg>
                ${t("drawer-sec-seller")}
            </div>
            ${ye("seller_name","drawer-lbl-name",l.seller_name,"input",s)}
            ${ye("seller_tax","drawer-lbl-tax",l.seller_tax,"input",s,p,ot("seller"))}
            ${ye("seller_addr","drawer-lbl-addr",l.seller_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="10" cy="6" r="3"/><path d="M3 18c0-3.9 3.1-7 7-7s7 3.1 7 7"/></svg>
                ${t("drawer-sec-buyer")}
            </div>
            ${ye("buyer_name","drawer-lbl-name",l.buyer_name,"input",s)}
            ${ye("buyer_tax","drawer-lbl-tax",l.buyer_tax,"input",s,p,ot("buyer"))}
            ${ye("buyer_addr","drawer-lbl-addr",l.buyer_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 7l7-4 7 4v7l-7 4-7-4z"/><path d="M3 7l7 4 7-4M10 11v8"/></svg>
                ${t("drawer-sec-items")}
            </div>
            ${l.items&&l.items.length>0?Dt(l.items):`<div class="drawer-items-empty">${t("drawer-items-empty")}</div>`}
        </div>

        <div class="drawer-section">
            ${ye("notes","drawer-lbl-notes",l.notes,"textarea",s)}
        </div>

        <details class="raw-text">
            <summary>${t("raw-text")}</summary>
            <pre>${escapeHtml(n.pages.map(c=>`--- Page ${c.page||c.page_number||"?"} ---
${c.raw_text||c.text||""}`).join(`

`))}</pre>
        </details>
    `,s?k.querySelectorAll("[data-field]").forEach(c=>{c.addEventListener("input",onFieldEdit)}):k.querySelectorAll("[data-field]").forEach(c=>{c.setAttribute("readonly","readonly")}),document.getElementById("drawer-mask").classList.add("show"),document.getElementById("drawer").classList.add("show"),injectOcrPushButton(),typeof window.bindDrawerClient=="function"){const c=n._historyId||n.history_id||null;window.bindDrawerClient(c,n.client_id||null)}typeof window.fillCategoryDatalist=="function"&&window.fillCategoryDatalist(),setTimeout(()=>{const c=document.getElementById("drawer-cat-input");c&&!c.value&&!c.readOnly&&c.focus()},80)}function Pt(e){return e?`<span class="wht-badge">${escapeHtml(e)}%</span>`:""}function ye(e,n,a,o,s,u,l){const k=_results[_drawerIdx],i=k&&k.edits[e]!==void 0?k.edits[e]:a,p=k&&k.edits[e]!==void 0&&k.edits[e]!==a,c=escapeHtml(i??""),r=s?"":"readonly",v=o==="textarea"?`<textarea data-field="${e}" rows="2">${c}</textarea>`:`<input type="text" data-field="${e}" value="${c}">`;return`
        <div class="drawer-field ${p?"edited":""} ${r}" data-field-wrap="${e}">
            <label class="drawer-field-label">
                <span class="drawer-field-edited-dot"></span>
                ${t(n)}
                ${u||""}
                ${l?`<span class="drawer-field-actions">${l}</span>`:""}
            </label>
            ${v}
        </div>
    `}function ot(e){return _userInfo&&_userInfo.can_verify_tax?`
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
        </button>`}function Dt(e){return`
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
    `}function qt(){document.getElementById("drawer-mask").classList.remove("show"),document.getElementById("drawer").classList.remove("show");const e=document.getElementById("drawer-history-save");e&&e.remove();const n=document.getElementById("drawer-ocr-push");n&&n.remove();const a=document.getElementById("drawer-ocr-push-btn");a&&a.remove(),_drawerIdx=-1}window.renderResults=ze;window.openDrawer=ct;window.closeDrawer=qt;function Rt(){const e=_results[_drawerIdx];if(!e||e._historyMode||!_userInfo||!_userInfo.can_push_erp||!e._historyId&&!e.history_id)return;const n=e._historyId||e.history_id,a=document.querySelector(".drawer-header");if(!a||document.getElementById("drawer-ocr-push-btn"))return;const o=(window._erpEndpoints||_erpEndpoints||[]).filter(function(k){return k&&k.enabled!==!1});if(o.length===0)return;const s=document.createElement("button");s.id="drawer-ocr-push-btn",s.className="drawer-push-btn";let u;if(o.length===1){const k=o[0].name||o[0].adapter||"ERP";u=t("btn-push-to-name",{name:k}),s.title=u}else u=t("btn-push-erp")+" ▾",s.title=t("btn-push-erp-pick-tip");s.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 8h9M8 5l3 3-3 3"/>
            <rect x="11" y="3" width="3" height="10" rx="1"/>
        </svg>
        <span>${escapeHtml(u)}</span>
    `,s.addEventListener("click",function(k){k.preventDefault(),k.stopPropagation(),o.length===1?dt(n,o[0].id):Nt(s,n,o)});const l=a.querySelector(".drawer-diagnose");l?a.insertBefore(s,l):a.appendChild(s)}function Nt(e,n,a){document.querySelectorAll(".drawer-push-picker").forEach(i=>i.remove());const o=e.getBoundingClientRect(),s=document.createElement("div");s.className="drawer-push-picker history-popover",s.style.position="fixed",s.style.top=o.bottom+6+"px",s.style.left=Math.max(8,o.right-240)+"px",s.style.minWidth="220px",s.style.zIndex="12000";const u=a.map(function(i){const p=escapeHtml(i.name||i.adapter||"ERP"),c=escapeHtml((i.adapter||"").toLowerCase()),v=i.is_default?'<span style="font-size:10px;color:#0a7a2c;background:#d6f5e0;padding:1px 6px;border-radius:999px;margin-left:6px;">'+escapeHtml(t("ep-default"))+"</span>":"";return'<button type="button" data-ep-id="'+escapeHtml(i.id)+'" style="display:flex;align-items:center;justify-content:space-between;width:100%;text-align:left;"><span><span style="color:#5d5d57;font-size:11px;margin-right:6px;">'+c+"</span>"+p+v+"</span></button>"}).join("");s.innerHTML=u,document.body.appendChild(s);const l=()=>{s.remove(),document.removeEventListener("click",k,!0)},k=i=>{!s.contains(i.target)&&i.target!==e&&!e.contains(i.target)&&l()};setTimeout(()=>document.addEventListener("click",k,!0),0),s.addEventListener("click",i=>{const p=i.target.closest("[data-ep-id]");if(!p)return;const c=p.getAttribute("data-ep-id");l(),dt(n,c)})}async function dt(e,n){const a=document.getElementById("drawer-ocr-push-btn");a&&(a.disabled=!0);try{const o={history_id:e};n&&(o.endpoint_id=n);const s=await fetch("/api/erp/push",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(o)}),u=await s.json();if(!s.ok){const l=u&&u.detail?u.detail:"err.unknown";l==="erp.no_default_endpoint"?showToast(t("erp-push-no-endpoint"),"warn"):l==="erp.endpoint_disabled"?(showToast(t("erp-push-disabled-tip")||t("card-disabled-tip")||"Endpoint disabled","warn"),typeof window._refreshErpEndpointsCache=="function"&&window._refreshErpEndpointsCache()):showToast(t("erp-push-fail",{err:l}),"fail");return}u.ok?showToast(t("erp-push-ok",{name:u.endpoint_name||""})):showToast(t("erp-push-fail",{err:u.error_msg||"unknown"}),"fail")}catch(o){showToast(t("erp-push-fail",{err:o.message}),"fail")}finally{a&&(a.disabled=!1)}}window.injectOcrPushButton=Rt;const zt=[{id:"input_vat",nameKey:"tpl-input-vat",descKey:"tpl-input-vat-desc",badge:"recommended"},{id:"standard",nameKey:"tpl-standard",descKey:"tpl-standard-desc"},{id:"sales_detail_th",nameKey:"export-tpl-sales-detail",descKey:"export-tpl-sales-detail-desc",badge:"new"},{id:"print",nameKey:"tpl-print",descKey:"tpl-print-desc"}];function pt(){try{const e=localStorage.getItem("pn_export_tpl")||"input_vat";return e==="erp"?"input_vat":e}catch{return"input_vat"}}function Ot(e){try{localStorage.setItem("pn_export_tpl",e||"input_vat")}catch{}}async function ut(e){if(_results.length===0)return;e=e||"input_vat";const n=document.getElementById("btn-export");n&&(n.disabled=!0,n.classList.add("loading"));try{let a,o=`pearnly-export-${Date.now()}.xlsx`;if(e==="sales_detail_th"){const p=[];for(const c of _results){const r=c.invoices&&c.invoices.length>0?c.invoices:null;if(r&&r.length>1)for(let v=0;v<r.length;v++){const E=r[v]||{};p.push({filename:c.filename+" #"+(v+1)+"/"+r.length,engine:c.engine,merged_fields:E.fields||{}})}else p.push({filename:c.filename,engine:c.engine,merged_fields:c.merged_fields})}a=await apiPost("/api/ocr/export",{records:p,lang:currentLang,template:"sales_detail_th"})}else{const p=[];for(const r of _results)r.history_ids&&Array.isArray(r.history_ids)?p.push(...r.history_ids):r.history_id&&p.push(r.history_id);if(p.length===0){showToast(t("toast-export-error"),"error");return}const c=localStorage.getItem("mrpilot_token");a=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+c,"Content-Type":"application/json"},body:JSON.stringify({template:e,lang:currentLang,history_ids:p,client_id:null})}),o=`pearnly-${e}-${Date.now()}.xlsx`}if(!a)return;if(!a.ok){let p="HTTP "+a.status;try{const r=await a.json();r&&r.detail&&(p=typeof r.detail=="string"?r.detail:JSON.stringify(r.detail))}catch(r){console.warn("[export] resp.json err.detail parse failed:",r)}const c=typeof p=="string"&&p.indexOf(".")>0?"err."+p:null;showToast(c?t(c):t("toast-export-error")+" · "+p,"error");return}const s=await a.blob();let u=o;const l=a.headers.get("X-Filename");if(l)u=l;else{const c=(a.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(c)try{u=decodeURIComponent(c[1])}catch{}}const k=URL.createObjectURL(s),i=document.createElement("a");i.href=k,i.download=u,document.body.appendChild(i),i.click(),document.body.removeChild(i),URL.revokeObjectURL(k),showToast(t("toast-export-success"),"success")}catch(a){console.error(a),showToast(t("toast-export-error"),"error")}finally{n&&(n.disabled=!1,n.classList.remove("loading"))}}document.getElementById("btn-export").addEventListener("click",()=>{ut(pt())});function Ft(){const e=document.getElementById("export-split-wrap");if(!e)return;let n=document.getElementById("export-dropdown");if(n){n.remove();return}n=document.createElement("div"),n.id="export-dropdown",n.className="export-dropdown";const a=pt(),o=zt.map(u=>{const l=u.badge==="recommended"?`<span class="export-dd-badge badge-rec">${escapeHtml(t("report-recommended"))}</span>`:u.badge==="new"?`<span class="export-dd-badge badge-new">${escapeHtml(t("tpl-badge-new"))}</span>`:"";return`
            <div class="export-dd-item ${u.id===a?"active":""}" data-tpl="${u.id}">
                <div class="export-dd-row">
                    <span class="export-dd-name">${escapeHtml(t(u.nameKey))}</span>
                    ${l}
                    ${u.id===a?'<span class="export-dd-check">✓</span>':""}
                </div>
                <div class="export-dd-desc">${escapeHtml(t(u.descKey))}</div>
            </div>
        `}).join(""),s=`
        <div class="export-dd-divider"></div>
        <div class="export-dd-item export-dd-custom" data-tpl="__custom" title="${escapeHtml(t("tpl-custom-coming"))}">
            <div class="export-dd-row">
                <span class="export-dd-name">+ ${escapeHtml(t("tpl-custom-new"))}</span>
                <span class="export-dd-badge badge-soon">${escapeHtml(t("cs-coming-soon"))}</span>
            </div>
        </div>
    `;n.innerHTML=o+s,e.appendChild(n)}function Je(){const e=document.getElementById("export-dropdown");e&&e.remove()}const Ke=document.getElementById("btn-export-arrow");Ke&&Ke.addEventListener("click",e=>{e.stopPropagation(),!Ke.disabled&&Ft()});document.addEventListener("click",e=>{const n=e.target.closest(".export-dd-item");if(n){const a=n.getAttribute("data-tpl");if(a==="__custom"){Je(),showToast(t("cs-coming-soon"),"info");return}Ot(a),Je(),ut(a);return}e.target.closest("#btn-export-arrow")||Je()});function Vt(){const e=document.getElementById("btn-export-arrow"),n=document.getElementById("btn-export");e&&n&&(e.disabled=n.disabled)}setInterval(Vt,300);function Ie(e,n){try{return typeof window.t=="function"?window.t(e):n}catch{return n}}function Te(e){if(e==null||isNaN(e))return"—";try{return String(e).replace(/\B(?=(\d{3})+(?!\d))/g,",")}catch{return String(e)}}function Ut(e){if(!e)return"";try{const n=new Date(e).getTime();if(!n)return"";const a=Math.floor((Date.now()-n)/1e3);return a<60?Ie("time-just-now","刚刚"):a<3600?Math.floor(a/60)+Ie("time-min-ago-suffix"," 分钟前"):a<86400?Math.floor(a/3600)+Ie("time-hour-ago-suffix"," 小时前"):Math.floor(a/86400)+Ie("time-day-ago-suffix"," 天前")}catch{return""}}async function Xe(){vt();const e=document.getElementById("dash-kpi-invoices"),n=document.getElementById("dash-kpi-pending"),a=document.getElementById("dash-kpi-exceptions"),o=document.getElementById("dash-kpi-plan"),s=document.getElementById("dash-kpi-plan-sub"),u=document.getElementById("dash-recent-list"),l=document.getElementById("dash-quick-exc-badge");try{const k={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},[i,p,c]=await Promise.all([fetch("/api/me/tenant-usage",{headers:k}).then(D=>D.ok?D.json():null).catch(()=>null),fetch("/api/history?limit=20",{headers:k}).then(D=>D.ok?D.json():null).catch(()=>null),fetch("/api/exceptions/stats?status=pending",{headers:k}).then(D=>D.ok?D.json():null).catch(()=>null)]),r=i&&i.ocr_this_month||0;let v=0;const E=p&&(p.items||p.history||p)||[],x=Array.isArray(E)?E:[];x.forEach(D=>{(D.status==="pending"||D.status==="reviewing")&&v++});const R=c&&(c.total||c.count||c.pending||0)||0;if(e&&(e.textContent=Te(r)),n&&(n.textContent=Te(v)),a&&(a.textContent=Te(R)),l&&(R>0?(l.style.display="",l.textContent=R):l.style.display="none"),o&&i){const D=i.ocr_this_month||0,w=i.quota||0;o.textContent=Te(D),s&&(s.textContent=w?D+" / "+Te(w)+" 张":Ie("dash-kpi-plan-sub","本月用量"))}if(u)if(x.length===0)u.innerHTML='<div class="dash-recent-empty">'+Ie("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>";else{const D=x.slice(0,5).map(w=>{const B=(w.invoice_no||w.filename||w.id||"").toString(),z=(w.supplier_name||w.buyer_name||w.client_name||w.notes||"").toString(),q=Ut(w.created_at||w.upload_time||w.date),F=A=>String(A).replace(/[&<>"']/g,g=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[g]);return'<div class="dash-recent-row"><span class="dash-recent-key" title="'+F(B)+'">'+F(B)+'</span><span class="dash-recent-mid" title="'+F(z)+'">'+F(z)+'</span><span class="dash-recent-time">'+F(q)+"</span></div>"}).join("");u.innerHTML=D}}catch{u&&(u.innerHTML='<div class="dash-recent-empty">'+Ie("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>")}}window.loadDashboard=Xe;async function vt(){const e=document.getElementById("dash-kpi-balance-card"),n=document.getElementById("dash-kpi-usage-card"),a=document.getElementById("dash-kpi-balance"),o=document.getElementById("dash-kpi-balance-sub"),s=document.getElementById("dash-kpi-usage"),u=document.getElementById("dash-kpi-usage-sub");if(!(!e||!n))try{const l={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},k=await fetch("/api/me/credits",{headers:l,cache:"no-store"});if(!k.ok){e.style.display="none",s&&(s.textContent="—"),u&&(u.textContent="");return}const i=await k.json(),p=!!i.is_owner,c=!!i.is_billing_exempt;if(!p)e.style.display="none";else if(e.style.display="",c)a&&(a.textContent="∞",a.className="dash-kpi-val dash-green"),o&&(o.textContent=typeof window.t=="function"?window.t("dash-kpi-balance-exempt"):"Billing exempt");else{const v=typeof i.balance_thb=="number"?i.balance_thb:0;if(a&&(a.textContent="฿"+v.toFixed(2),a.className=v<50?"dash-kpi-val dash-red":"dash-kpi-val"),o){const E=typeof window.t=="function"?window.t("dash-kpi-balance-topup"):"Top up →",x=v<50?"#dc2626":"#6b7280",R=D=>typeof window.escapeHtml=="function"?window.escapeHtml(D):String(D).replace(/[&<>"']/g,w=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[w]);o.innerHTML='<a href="#" id="kpi-balance-topup-link" style="color:'+x+';text-decoration:underline;cursor:pointer;" onclick="event.preventDefault();window._openTopupModal&&window._openTopupModal();return false;">'+R(E)+"</a>"}}const r=typeof i.pages_this_month=="number"?i.pages_this_month:typeof i.my_invoice_count=="number"?i.my_invoice_count:0;if(n.style.display="",s&&(s.textContent=String(r)),u){const v=r>=200?"dash-kpi-usage-sub-high":"dash-kpi-usage-sub-low",E=typeof window.t=="function"?window.t(v,{used:r}):r+" pages";u.textContent=E}}catch(l){console.warn("[credits] loadCreditsCard failed:",l),e.style.display="none",s&&(s.textContent="—")}}window.loadCreditsCard=vt;document.addEventListener("DOMContentLoaded",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&setTimeout(Xe,500)});typeof window.subscribeI18n=="function"&&window.subscribeI18n("dashboard",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&Xe()});function he(e){return(typeof window.t=="function"?window.t(e):null)||e}function Ze(){return localStorage.getItem("mrpilot_token")||""}function me(e){return document.getElementById(e)}var Re=null,$e=null;function ft(){$e||($e=setInterval(function(){if(!document.hidden){var e=Ze();e&&(window._userInfo&&window._userInfo.is_billing_exempt||fetch("/api/me/credits",{headers:{Authorization:"Bearer "+e},cache:"no-store"}).then(function(n){return n.ok?n.json():null}).then(function(n){if(n){var a=n.balance_thb!=null?Number(n.balance_thb):0;Re!==null&&a>Re&&(window.showToast&&window.showToast(he("credits-updated"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard(),typeof window._refreshBalanceAlerts=="function"&&window._refreshBalanceAlerts()),Re=a}}).catch(function(){}))}},3e4))}function Gt(){$e&&(clearInterval($e),$e=null),Re=null}window._startCreditsPoll=ft;window._stopCreditsPoll=Gt;ft();var Qe=null,et=0;function Yt(){if(!me("topup-v2-ov")){var e=document.createElement("div");e.id="topup-v2-ov",e.className="topup-v2-ov",e.style.cssText="display:none;position:fixed;inset:0;background:rgba(15,23,42,.5);z-index:9500;align-items:center;justify-content:center;padding:16px",e.innerHTML=['<div class="topup-v2-box">','  <div class="topup-v2-head">','    <div class="topup-v2-title" id="tv2-title"></div>','    <button class="topup-v2-close" id="tv2-close" aria-label="close">','      <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="4" y1="4" x2="16" y2="16"/><line x1="16" y1="4" x2="4" y2="16"/></svg>',"    </button>","  </div>",'  <div class="topup-v2-steps">','    <div class="topup-v2-step" id="tv2-d1"><span class="topup-v2-dot">1</span><span class="topup-v2-slabel" id="tv2-sl1"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d2"><span class="topup-v2-dot">2</span><span class="topup-v2-slabel" id="tv2-sl2"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d3"><span class="topup-v2-dot">3</span><span class="topup-v2-slabel" id="tv2-sl3"></span></div>',"  </div>",'  <div class="topup-v2-body">','    <div id="tv2-s1">','      <label class="topup-v2-label" id="tv2-al"></label>','      <div class="topup-v2-qamts">','        <button class="topup-v2-qamt" data-val="100">฿100</button>','        <button class="topup-v2-qamt" data-val="500">฿500</button>','        <button class="topup-v2-qamt" data-val="1000">฿1,000</button>','        <button class="topup-v2-qamt" data-val="2000">฿2,000</button>',"      </div>",'      <input id="tv2-amt" type="number" min="10" step="1" class="topup-v2-input" placeholder="฿ ...">','      <div id="tv2-ae" class="topup-v2-err" style="display:none"></div>',"    </div>",'    <div id="tv2-s2" style="display:none">','      <p class="topup-v2-bank-label" id="tv2-bl"></p>','      <div class="topup-v2-bank-card">','        <div class="topup-v2-bank-name">ธนาคาร กรุงเทพ</div>','        <div class="topup-v2-bank-branch">สาขาโชคชัย 4 ลาดพร้าว</div>','        <div class="topup-v2-bank-acct">230-0-91368-4</div>','        <div class="topup-v2-bank-holder">บจ. มิสเตอร์ อี อาร์ พี</div>','        <button class="topup-v2-copy" id="tv2-copy"></button>',"      </div>",'      <div class="topup-v2-warn" id="tv2-bn"></div>',"    </div>",'    <div id="tv2-s3" style="display:none">','      <div class="topup-v2-drop" id="tv2-drop">','        <input type="file" id="tv2-file" accept="image/*,.pdf" style="display:none">','        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>','        <span class="topup-v2-drop-text" id="tv2-dt"></span>',"      </div>",'      <div id="tv2-se" class="topup-v2-err" style="display:none"></div>','      <label class="topup-v2-label" id="tv2-pl"></label>','      <input id="tv2-payer" type="text" maxlength="200" class="topup-v2-input">','      <label class="topup-v2-label" id="tv2-nl"></label>','      <input id="tv2-note" type="text" maxlength="500" class="topup-v2-input">','      <div id="tv2-ue" class="topup-v2-err" style="display:none"></div>',"    </div>","  </div>",'  <div class="topup-v2-foot">','    <button class="btn btn-ghost" id="tv2-back" style="display:none"></button>','    <button class="btn btn-primary" id="tv2-next"></button>',"  </div>","</div>"].join(""),document.body.appendChild(e),Jt()}}function mt(){var e=function(n,a){var o=me(n);o&&(o.textContent=a)};e("tv2-title",he("topup-title")),e("tv2-sl1",he("topup-step1")),e("tv2-sl2",he("topup-step2")),e("tv2-sl3",he("topup-step3")),e("tv2-al",he("topup-amount-label")),e("tv2-bl",he("topup-bank-label")),e("tv2-copy",he("topup-copy-account")),e("tv2-dt",he("topup-slip-drop")),e("tv2-pl",he("topup-payer-label")),e("tv2-nl",he("topup-note-label"))}function Ae(e){[1,2,3].forEach(function(s){var u=me("tv2-s"+s);u&&(u.style.display=s===e?"":"none");var l=me("tv2-d"+s);l&&l.classList.toggle("active",s<=e)});var n=me("tv2-back"),a=me("tv2-next");if(e===1?n&&(n.style.display="",n.textContent=he("topup-btn-cancel")):n&&(n.style.display="",n.textContent=he("topup-btn-back")),a&&(a.textContent=he(e===3?"topup-btn-submit":"topup-btn-next")),e===2){var o=me("tv2-bn");o&&(o.innerHTML=he("topup-bank-note").replace("{amount}","<strong>฿"+Number(et).toLocaleString()+"</strong>"))}}function We(){for(var e=1;e<=3;e++){var n=me("tv2-s"+e);if(n&&n.style.display!=="none")return e}return 1}function Ne(e){var n=me(e);n&&(n.textContent="",n.style.display="none")}function He(e,n){var a=me(e);a&&(a.textContent=n,a.style.display="")}function st(e){var n=me("tv2-dt");n&&(n.textContent=e.name);var a=me("tv2-drop");a&&a.classList.add("has-file"),Ne("tv2-se")}function Jt(){var e=me("topup-v2-ov");me("tv2-close").addEventListener("click",Me),e.addEventListener("click",function(u){u.target===e&&Me()}),document.addEventListener("keydown",function(u){u.key==="Escape"&&e&&e.style.display!=="none"&&Me()}),e.addEventListener("click",function(u){var l=u.target.closest(".topup-v2-qamt");if(l){e.querySelectorAll(".topup-v2-qamt").forEach(function(i){i.classList.remove("active")}),l.classList.add("active");var k=me("tv2-amt");k&&(k.value=l.dataset.val,Ne("tv2-ae"))}});var n=me("tv2-amt");n&&n.addEventListener("input",function(){e.querySelectorAll(".topup-v2-qamt").forEach(function(u){u.classList.remove("active")}),Ne("tv2-ae")});var a=me("tv2-copy");a&&a.addEventListener("click",function(){navigator.clipboard&&navigator.clipboard.writeText("2300913684").then(function(){var u=a.textContent;a.textContent=he("topup-copied"),setTimeout(function(){a.textContent=u},1500)})});var o=me("tv2-drop"),s=me("tv2-file");o&&(o.addEventListener("click",function(){s&&s.click()}),o.addEventListener("dragover",function(u){u.preventDefault(),o.classList.add("drag-over")}),o.addEventListener("dragleave",function(){o.classList.remove("drag-over")}),o.addEventListener("drop",function(u){u.preventDefault(),o.classList.remove("drag-over");var l=u.dataTransfer&&u.dataTransfer.files[0];l&&st(l)})),s&&s.addEventListener("change",function(){s.files[0]&&st(s.files[0])}),me("tv2-back").addEventListener("click",function(){var u=We();if(u<=1){Me();return}Ae(u-1)}),me("tv2-next").addEventListener("click",function(){var u=We();u===1?Kt():u===2?Ae(3):Wt()})}async function Kt(){var e=me("tv2-amt"),n=e?parseFloat(e.value):0;if(!n||n<10){He("tv2-ae",he("topup-amount-invalid"));return}if(n>5e5){He("tv2-ae",he("topup-amount-too-large"));return}et=n;var a=me("tv2-next");a&&(a.disabled=!0,a.textContent="…");try{var o=await fetch("/api/credits/topup/request",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+Ze()},body:JSON.stringify({amount_thb:n})});if(!o.ok){var s=await o.text(),u=he("topup-submit-fail");try{var l=JSON.parse(s),k=l.detail;if(Array.isArray(k)&&k.length){var i=k[0]&&k[0].type||"";i.indexOf("less_than")>=0?u=he("topup-amount-too-large"):(i.indexOf("greater_than")>=0||i.indexOf("parsing")>=0)&&(u=he("topup-amount-invalid"))}else typeof k=="string"&&(u=k)}catch{}throw new Error(u)}var p=await o.json();Qe=p.request_id,Ae(2)}catch(c){He("tv2-ae",c.message||he("topup-submit-fail"))}finally{a&&(a.disabled=!1,a.textContent=he("topup-btn-next"))}}async function Wt(){var e=me("tv2-file");if(!e||!e.files||!e.files[0]){He("tv2-se",he("topup-slip-required"));return}var n=me("tv2-next");n&&(n.disabled=!0,n.textContent="…");try{var a=new FormData;a.append("file",e.files[0]);var o=me("tv2-payer"),s=me("tv2-note");o&&o.value.trim()&&a.append("payer_name",o.value.trim()),s&&s.value.trim()&&a.append("note",s.value.trim());var u=await fetch("/api/credits/topup/upload-slip/"+Qe,{method:"POST",headers:{Authorization:"Bearer "+Ze()},body:a});if(!u.ok)throw new Error(await u.text());var l=await u.json();l.auto_approved?(window.showToast&&window.showToast(he("topup-auto-approved"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard()):window.showToast&&window.showToast(he("topup-pending"),"info"),Me()}catch(k){He("tv2-ue",he("topup-upload-fail")+" · "+k.message),n&&(n.disabled=!1,n.textContent=he("topup-btn-submit"))}}function Me(){var e=me("topup-v2-ov");e&&(e.style.display="none"),typeof window.loadDashboard=="function"&&window.loadDashboard()}window._openTopupModal=function(){Yt(),Qe=null,et=0,["tv2-amt","tv2-payer","tv2-note"].forEach(function(a){var o=me(a);o&&(o.value="")});var e=me("tv2-file");e&&(e.value="");var n=me("tv2-drop");n&&n.classList.remove("has-file","drag-over"),me("topup-v2-ov").querySelectorAll(".topup-v2-qamt").forEach(function(a){a.classList.remove("active")}),["tv2-ae","tv2-se","tv2-ue"].forEach(function(a){Ne(a)}),mt(),Ae(1),me("topup-v2-ov").style.display="flex"};typeof window.subscribeI18n=="function"&&window.subscribeI18n("topup-v2",function(){var e=me("topup-v2-ov");e&&e.style.display!=="none"&&e.style.display!==""&&(mt(),Ae(We()))});(function(){const e="v118.28.5",n="pearnly_tc_results_"+e,a=[{id:"A1",group:"A · 异常栏 page-head(BUG1)",desc:"手机宽度进异常栏 · 标题「异常栏」横排正常 · 不再每字一行"},{id:"A2",group:"A · 异常栏 page-head(BUG1)",desc:"副标题「所有被规则拦截的单据集中复核…」也横排正常 · 不竖排"},{id:"A3",group:"A · 异常栏 page-head(BUG1)",desc:"客户筛选下拉 + 刷新按钮换到新一行 · 不抢标题宽度"},{id:"B1",group:"B · 客户管理 page-head(BUG2)",desc:"手机宽度进客户管理 · 标题「客户管理」横排正常"},{id:"B2",group:"B · 客户管理 page-head(BUG2)",desc:"副标题「为每家客户单独归档发票…」横排正常 · 不竖排"},{id:"B3",group:"B · 客户管理 page-head(BUG2)",desc:"「+ 新建客户」按钮换到新一行 · 不挤标题"},{id:"C1",group:"C · 客户卡片(BUG3)",desc:"客户卡片「编辑 / 导出本月」按钮文字清晰 · 不被截断"},{id:"D1",group:"D · 历史表头(BUG4)",desc:"手机宽度进单据记录 · 表头「文件·发票号·供应商」/「金额」单行 · 不竖排"},{id:"D2",group:"D · 历史表头(BUG4)",desc:"行内 INV-TH-202605-1006 这种长发票号正常单行展示 · 不一字一行"},{id:"E1",group:"E · 对账切换器(BUG6)",desc:"手机宽度进对账中心 · 顶栏点「全部客户」chip · 下拉从右上角向下展开 · 右对齐 · 不贴左屏边"},{id:"E2",group:"E · 对账切换器(BUG6)",desc:"下拉宽度自适应屏幕 · 不超出屏幕右边"},{id:"F1",group:"F · 通用设置回归",desc:"设置 → 个人资料 · 没有「界面语言」4 按钮卡"},{id:"F2",group:"F · 通用设置回归",desc:"左侧 nav 顺序:账户 / 公司 / 工作流 / 系统 / 关于"},{id:"F3",group:"F · 通用设置回归",desc:"系统 → 通用设置 · 4 行下拉(语言/时区/日期/数字)· 改语言立即切语言 · 改其他保存后 F5 仍保留"},{id:"G1",group:"G · 移动端 settings(回归)",desc:"手机宽度设置 tabs 不重叠 · 按分组分行 · chip 风格"},{id:"H1",group:"H · 回归",desc:"OCR 上传识别 / 客户管理 / 异常栏 / 对账中心 / 测试中心 全部仍工作"},{id:"H2",group:"H · 回归",desc:"4 语切换没新增异常(测试中心异常日志「API 失败」过滤无新条目)"},{id:"I1",group:"I · 三档移动 viewport",desc:"iPhone SE 375 · 上述 BUG 1-6 都修了"},{id:"I2",group:"I · 三档移动 viewport",desc:"Galaxy S 360 · 上述 BUG 1-6 都修了"},{id:"I3",group:"I · 三档移动 viewport",desc:"iPhone 12 Pro 414 · 上述 BUG 1-6 都修了"}];let o={},s="all",u=!1,l=!1;function k(G,W,te){let re=typeof t=="function"?t(G):null;return(!re||re===G)&&(re=W),te&&Object.keys(te).forEach(function(S){re=String(re).replace("{"+S+"}",String(te[S]))}),re}function i(){try{const G=localStorage.getItem(n);o=G?JSON.parse(G):{},(typeof o!="object"||!o)&&(o={})}catch{o={}}}function p(){try{localStorage.setItem(n,JSON.stringify(o))}catch{}}function c(G){const W=new Date(G),te=function(re){return re<10?"0"+re:""+re};return te(W.getHours())+":"+te(W.getMinutes())+":"+te(W.getSeconds())}function r(G){return String(G??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function v(G,W){try{typeof showToast=="function"?showToast(G,W||"info"):alert(G)}catch{}}function E(G){try{navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(G).then(function(){v(k("tc-toast-copied","已复制到剪贴板"),"success")}).catch(function(){x(G)}):x(G)}catch{x(G)}}function x(G){try{const W=document.createElement("textarea");W.value=G,W.style.position="fixed",W.style.opacity="0",document.body.appendChild(W),W.select();const te=document.execCommand("copy");document.body.removeChild(W),v(te?k("tc-toast-copied","已复制"):k("tc-toast-copy-fail","复制失败"),te?"success":"error")}catch{v(k("tc-toast-copy-fail","复制失败"),"error")}}function R(){const G=document.getElementById("tc-account-chip"),W=document.getElementById("tc-progress-chip");if(G&&(G.textContent=_userInfo&&(_userInfo.email||_userInfo.username)||"—"),W){const te=a.length,re=a.filter(function(S){return o[S.id]}).length;W.textContent=re+" / "+te}}function D(){const G=document.getElementById("tc-checklist-body");if(!G)return;const W={};a.forEach(function(re){W[re.group]||(W[re.group]=[]),W[re.group].push(re)});const te=[];Object.keys(W).forEach(function(re){te.push('<div class="tc-checklist-group">'),te.push('<div class="tc-checklist-group-title">'+r(re)+"</div>"),W[re].forEach(function(S){const y=o[S.id]||"",m=y?"is-"+y:"";te.push('<div class="tc-check-item '+m+'" data-id="'+r(S.id)+'"><div class="tc-check-id">'+r(S.id)+'</div><div class="tc-check-desc">'+r(S.desc)+'</div><div class="tc-check-actions">'+w(S.id,"pass",y)+w(S.id,"fail",y)+w(S.id,"skip",y)+"</div></div>")}),te.push("</div>")}),G.innerHTML=te.join("")}function w(G,W,te){const re=te===W,S={pass:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="4,11 8,15 16,5"/></svg>',fail:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="5" x2="15" y2="15"/><line x1="15" y1="5" x2="5" y2="15"/></svg>',skip:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="10" x2="15" y2="10"/></svg>'},y={pass:k("tc-status-pass","通过"),fail:k("tc-status-fail","失败"),skip:k("tc-status-skip","跳过")};return'<button type="button" class="tc-status-btn '+(re?"is-active "+W:"")+'" data-id="'+r(G)+'" data-kind="'+W+'" title="'+r(y[W])+'">'+S[W]+"</button>"}function B(G){return s==="all"?!0:s==="js_error"?G.type==="js_error"||G.type==="promise_error":s==="api"?G.type==="api_error"||G.type==="api_fail":s==="api_slow"?G.type==="api_slow":s==="console"?G.type==="console_error"||G.type==="console_warn":!0}function z(){const G=document.getElementById("tc-logs-body"),W=document.getElementById("tc-logs-count");if(!G)return;const te=(window._pearnlyTcLogs||[]).slice().reverse(),re=te.filter(B);if(W&&(W.textContent=String(te.length)),re.length===0){G.innerHTML='<div class="tc-logs-empty">'+r(k("tc-logs-empty","暂无异常"))+"</div>";return}const S=re.slice(0,100).map(function(y){const m=typeof y.detail=="object"?JSON.stringify(y.detail,null,2):String(y.detail||"");return'<div class="tc-log-item t-'+r(y.type)+'" data-ts="'+y.ts+'"><span class="tc-log-time">'+c(y.ts)+'</span><span class="tc-log-type">'+r(y.type)+'</span><div class="tc-log-summary">'+r(y.summary)+'<div class="tc-log-detail">'+r(m)+"</div></div></div>"}).join("");G.innerHTML=S,document.querySelectorAll("#tc-logs-filter .tc-filter-chip").forEach(function(y){y.classList.toggle("active",y.getAttribute("data-filter")===s)})}function q(){l||(l=!0,setTimeout(function(){l=!1,currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&z(),F()},200))}window._tcOnNewLog=q;function F(){const G=document.getElementById("nav-test-badge");if(!G)return;const W=(window._pearnlyTcLogs||[]).filter(function(te){return te.type==="js_error"||te.type==="promise_error"||te.type==="api_error"||te.type==="api_fail"||te.type==="console_error"}).length;W>0?(G.style.display="",G.textContent=W>99?"99+":String(W)):G.style.display="none"}function A(){R(),D(),z(),F()}function g(){const G=[],W=new Date,te=_userInfo&&(_userInfo.email||_userInfo.username)||"—";G.push("# Pearnly "+e+" 测试结果"),G.push("- 账号:"+te),G.push("- 时间:"+W.toISOString().replace("T"," ").slice(0,19));const re=a.length,S=a.filter(function(Z){return o[Z.id]==="pass"}).length,y=a.filter(function(Z){return o[Z.id]==="fail"}).length,m=a.filter(function(Z){return o[Z.id]==="skip"}).length,$=re-S-y-m;G.push("- 进度:"+(S+y+m)+" / "+re+" · ✅ "+S+" · ❌ "+y+" · ⏭ "+m+" · 未测 "+$),G.push(""),G.push("| ID | 描述 | 状态 |"),G.push("|---|---|---|"),a.forEach(function(Z){const le=o[Z.id],ie=le==="pass"?"✅":le==="fail"?"❌":le==="skip"?"⏭":"⬜";G.push("| "+Z.id+" | "+Z.desc.replace(/\|/g,"\\|")+" | "+ie+" |")});const P=a.filter(function(Z){return o[Z.id]==="fail"});P.length>0&&(G.push(""),G.push("## ❌ 失败项"),P.forEach(function(Z){G.push("- **"+Z.id+"** · "+Z.desc)}));const Y=(window._pearnlyTcLogs||[]).slice(-30).reverse();return Y.length>0&&(G.push(""),G.push("## 🔴 异常日志(最近 "+Y.length+" 条)"),Y.forEach(function(Z){if(G.push("- `"+c(Z.ts)+"` · **"+Z.type+"** · "+Z.summary),Z.detail){let le;try{le=JSON.stringify(Z.detail)}catch{le=String(Z.detail)}le&&le!=="{}"&&G.push("  - "+le.slice(0,600))}})),G.join(`
`)}function f(G){const W=(window._pearnlyTcLogs||[]).slice(-30).reverse();if(W.length===0)return"(暂无异常日志)";const te=["# Pearnly 异常日志(最近 "+W.length+" 条)"],re=_userInfo&&(_userInfo.email||_userInfo.username)||"—";return te.push("- 账号:"+re),te.push("- 当前页:"+(currentRoute||"?")),te.push("- UA:"+navigator.userAgent),te.push(""),W.forEach(function(S){if(te.push("## `"+c(S.ts)+"` · "+S.type),te.push("- "+S.summary),S.detail){te.push("```");try{te.push(JSON.stringify(S.detail,null,2).slice(0,2e3))}catch{te.push(String(S.detail).slice(0,2e3))}te.push("```")}}),te.join(`
`)}function h(){const G=Date.now();fetch("/api/health").then(function(W){const te=Date.now()-G;W.ok?v(k("tc-toast-health-ok","后端健康 ✓ {ms}ms",{ms:te}),"success"):v(k("tc-toast-health-fail","后端无响应")+" ("+W.status+")","error")}).catch(function(){v(k("tc-toast-health-fail","后端无响应"),"error")})}function I(){try{localStorage.removeItem(n),localStorage.removeItem("pearnly_current_client_id"),o={},(window._pearnlyTcLogs||[]).length=0,s="all",window.setCurrentClientId}catch{}A(),v(k("tc-toast-cleared","session 状态已清空"),"success")}function L(){try{fetch("/api/clients",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}).then(function(G){return G.json()}).then(function(G){window._clientsCache=G.clients||[],typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher(),typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter(),v("客户缓存已刷新 · "+(G.clients||[]).length+" 个客户","success")}).catch(function(){v("刷新失败","error")})}catch{}}function H(){if(u||!document.getElementById("page-test-center"))return;u=!0;const W=document.getElementById("tc-checklist-body");W&&W.addEventListener("click",function(le){const ie=le.target.closest(".tc-status-btn");if(!ie)return;const V=ie.getAttribute("data-id"),Q=ie.getAttribute("data-kind");!V||!Q||(o[V]===Q?delete o[V]:o[V]=Q,p(),D(),R())});const te=document.getElementById("tc-btn-reset-checklist");te&&te.addEventListener("click",function(){o={},p(),D(),R()});const re=document.getElementById("tc-btn-copy-all");re&&re.addEventListener("click",function(){E(g())});const S=document.getElementById("tc-btn-copy-logs");S&&S.addEventListener("click",function(){E(f())});const y=document.getElementById("tc-btn-clear-logs");y&&y.addEventListener("click",function(){(window._pearnlyTcLogs||[]).length=0,z(),F()});const m=document.getElementById("tc-logs-filter");m&&m.addEventListener("click",function(le){const ie=le.target.closest(".tc-filter-chip");ie&&(s=ie.getAttribute("data-filter")||"all",z())});const $=document.getElementById("tc-logs-body");$&&$.addEventListener("click",function(le){const ie=le.target.closest(".tc-log-item");ie&&ie.classList.toggle("expanded")});const P=document.getElementById("tc-tool-health");P&&P.addEventListener("click",h);const Y=document.getElementById("tc-tool-clear-session");Y&&Y.addEventListener("click",I);const Z=document.getElementById("tc-tool-reload-clients");Z&&Z.addEventListener("click",L)}function _(){}window._tcApplyVisibility=_;let M=0;const K=setInterval(function(){M++,_userInfo&&clearInterval(K),M>60&&clearInterval(K)},500);window.loadTestCenterPage=function(){i(),H(),A()},typeof window.subscribeI18n=="function"&&window.subscribeI18n("test-center",function(){F(),currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&A()})})();(function(){const e="pearnly_active_workspace_client_id",n="pearnly_work_mode";function a(B,z){if(typeof window.t=="function"){const q=window.t(B);if(q&&q!==B)return q}return z}function o(){const B=window._userInfo||{},z=String(B.role||"").toLowerCase(),q=String(B.tenant_role||"").toLowerCase();return B.is_super_admin===!0||B.is_owner===!0||z==="owner"||z==="admin"||q==="owner"||q==="admin"}function s(){return localStorage.getItem(n)==="client"?"client":"personal"}function u(){const B=localStorage.getItem(e);if(!B||B==="null"||B==="0"||B==="")return null;const z=parseInt(B,10);return isNaN(z)?null:z}function l(B){try{window.dispatchEvent(new CustomEvent("pearnly:workspace-changed",{detail:{id:B,mode:s()}}))}catch{}}function k(B){const z=u();B==null||B===0?localStorage.removeItem(e):(localStorage.setItem(e,String(B)),localStorage.setItem(n,"client")),String(z)!==String(B)&&l(B)}function i(){const B=u();localStorage.setItem(n,"personal"),localStorage.removeItem(e),B!=null&&l(null)}async function p(){try{const B=window.apiGet;if(typeof B!="function")return[];const z=await B("/api/workspace/clients");return z&&(z.clients||z.items)||[]}catch{return[]}}async function c(B){if(s()==="client"&&u()!=null)return typeof B=="function"&&B(),!0;const z=a("ws-need-client","这个功能需要先选择工作空间"),q=a("ws-btn-pick","选择工作空间"),F=a("ws-btn-cancel","取消");return typeof window.showConfirm=="function"?await window.showConfirm(z,{okText:q,cancelText:F})&&r(B):window.confirm(z+`

[`+q+" / "+F+"]")&&r(B),!1}async function r(B){const z=await p();if(typeof B=="function"&&s()!=="personal"&&z.length===1){k(Number(z[0].id)),B();return}if(typeof window.openWorkspaceChooserUI=="function"){window.openWorkspaceChooserUI({clients:z,canCreate:o(),active:u(),onPersonal:i,onPick:function(q){k(Number(q)),typeof B=="function"&&B()},emptyHint:z.length?null:o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。")});return}if(!z.length){const q=o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。");typeof window.showToast=="function"&&window.showToast(q,"info")}}function v(B){const z=B||document.getElementById("workspace-switcher-root");if(!z)return;const q=s(),F=u();let A,g;if(q==="client"&&F!=null){const I=(window._workspaceClientsCache||[]).find(L=>Number(L.id)===Number(F));A=x("building"),g=I?I.name:a("ws-current-label","当前工作空间")}else A=x("user"),g=a("ws-personal","个人事务");z.innerHTML='<button class="ws-ctrl-btn" id="ws-ctrl-btn" type="button">'+A+'<span class="ws-ctrl-label">'+E(g)+"</span></button>";const f=z.querySelector("#ws-ctrl-btn");f&&f.addEventListener("click",()=>r(null))}function E(B){return String(B??"").replace(/[&<>"']/g,function(z){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[z]})}function x(B){const z='<svg class="ws-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';return B==="building"?z+'<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>':z+'<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'}function R(B){B=B||{};const z=B.clients||[],q=B.active,F=document.getElementById("ws-modal");F&&F.remove();const A=document.createElement("div");A.id="ws-modal",A.className="ws-modal";const f='<button type="button" class="ws-modal-item'+(s()==="personal"||q==null?" active":"")+'" data-ws-personal="1"><span class="ws-modal-item-ic">'+x("user")+'</span><span class="ws-modal-item-text" style="display:flex;flex-direction:column;align-items:flex-start;min-width:0;"><span class="ws-modal-item-name">'+E(a("ws-personal","个人事务"))+'</span><span class="ws-modal-item-desc" style="font-size:11px;color:#6b7280;font-weight:400;margin-top:2px;line-height:1.35;white-space:normal;">'+E(a("ws-personal-desc","用于临时识别、测试或处理不归属任何公司的文件。"))+"</span></span></button>";let h="";if(z.length){const M=['<option value="">'+E(a("ws-select-ph","— 选择账套主体 —"))+"</option>"].concat(z.map(function(K){const G=q!=null&&Number(q)===Number(K.id);return'<option value="'+E(K.id)+'"'+(G?" selected":"")+">"+E(K.name||"#"+K.id)+"</option>"}));h='<div class="ws-modal-select-row"><label class="ws-modal-select-label">'+E(a("ws-select-label","账套主体"))+'</label><select class="ws-modal-select" data-ws-select="1">'+M.join("")+"</select></div>"}const I=!z.length&&B.emptyHint?'<div class="ws-modal-empty">'+E(B.emptyHint)+"</div>":"",L=B.canCreate?'<div class="ws-modal-create"><button type="button" class="ws-modal-create-toggle" data-ws-create-toggle="1">+ '+E(a("ws-create-client","新建工作空间"))+'</button><div class="ws-modal-create-form" data-ws-create-form style="display:none;"><input type="text" class="ws-modal-create-input" data-ws-create-name placeholder="'+E(a("ws-create-ph","公司名称,例如 BAKELAB"))+'"><button type="button" class="ws-modal-create-submit" data-ws-create-submit="1">'+E(a("ws-create-submit","创建"))+"</button></div></div>":"";A.innerHTML='<div class="ws-modal-box" role="dialog" aria-modal="true"><div class="ws-modal-head"><span class="ws-modal-title">'+E(a("ws-chooser-title","选择工作空间"))+'</span><button type="button" class="ws-modal-close" data-ws-close="1" aria-label="close">✕</button></div><div class="ws-modal-subtitle" style="font-size:12px;color:#6b7280;padding:2px 4px 12px;line-height:1.45;white-space:normal;">'+E(a("ws-chooser-subtitle","账套主体 = 你的公司(发票卖方/开票方)。选择正在为哪家公司做账。"))+'</div><div class="ws-modal-list">'+f+h+"</div>"+I+L+"</div>",document.body.appendChild(A);const H=A.querySelector("[data-ws-select]");H&&H.addEventListener("change",function(){const M=H.value;M&&(typeof B.onPick=="function"&&B.onPick(M),_(),v())});function _(){A.remove()}A.addEventListener("click",function(M){if(M.target===A||M.target.closest("[data-ws-close]")){_();return}if(M.target.closest("[data-ws-personal]")){typeof B.onPersonal=="function"&&B.onPersonal(),_(),v();return}const G=M.target.closest("[data-ws-pick]");if(G){const re=G.getAttribute("data-ws-pick");typeof B.onPick=="function"&&B.onPick(re),_(),v();return}if(M.target.closest("[data-ws-create-toggle]")){const re=A.querySelector("[data-ws-create-form]");if(re){re.style.display=re.style.display==="none"?"flex":"none";const S=re.querySelector("[data-ws-create-name]");S&&S.focus()}return}if(M.target.closest("[data-ws-create-submit]")){D(A,B,_);return}})}async function D(B,z,q){const F=B.querySelector("[data-ws-create-name]"),A=F?(F.value||"").trim():"";if(!A){F&&F.focus();return}let g=null;try{if(typeof window.apiPost=="function"){const h=await window.apiPost("/api/workspace/clients",{name:A});g=h&&typeof h.json=="function"?await h.json().catch(()=>null):h}}catch{g=null}const f=g&&(g.id||g.client&&g.client.id);if(!f){typeof window.showToast=="function"&&window.showToast(a("ws-create-fail","新建工作空间失败 · 请重试"),"error");return}window._workspaceClientsCache=await p(),k(Number(f)),z.onPick,q(),v()}window.openWorkspaceChooserUI=R,window.addEventListener("pearnly:workspace-changed",function(){v()}),window.getWorkMode=s,window.getActiveWorkspaceClientId=u,window.setActiveWorkspaceClientId=k,window.enterPersonalMode=i,window.requireWorkspace=c,window.openWorkspaceChooser=r,window.renderWorkspaceControl=v,window.fetchWorkspaceClients=p;function w(){try{if(sessionStorage.getItem("pearnly_ws_login_prompted")==="1"||u()!=null||localStorage.getItem(n)==="personal")return;sessionStorage.setItem("pearnly_ws_login_prompted","1"),setTimeout(function(){r(null)},800)}catch{}}p().then(B=>{window._workspaceClientsCache=B,v(),w()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("workspace-switcher",v)})();(function(){const e=q=>document.querySelector('[data-num-target="'+q+'"]');function n(q){if(!q)return t("reconcile-last-activity-none");try{const F=new Date(q),A=new Date,g=A-F;if(g/6e4<5)return t("reconcile-last-activity-just-now");if(F.toDateString()===A.toDateString())return t("reconcile-last-activity-today");const h=Math.max(1,Math.floor(g/(24*3600*1e3)));return t("reconcile-last-activity-days-ago").replace("{n}",h)}catch{return t("reconcile-last-activity-none")}}function a(q,F,A){const g=e(q);g&&(g.textContent=A?"-":String(F),g.classList.toggle("is-empty",!!A))}function o(q){const F=document.getElementById("reconcile-error");F&&(F.style.display=q?"flex":"none")}function s(q){const F=document.getElementById("reconcile-empty");F&&(F.style.display=q?"flex":"none")}function u(q,F){const A=document.getElementById("reconcile-last-activity");A&&(A.textContent=q,A.classList.toggle("has-data",!!F))}function l(q){const F=!q||(q.total_sessions||0)===0;a("pending",q.pending||0,F),a("matched",q.matched||0,F),a("unmatched",q.unmatched||0,F),u(n(q.last_activity_at),!!q.last_activity_at),o(!1),s(F)}function k(q){const F=q.toUpperCase();return F==="KBANK"?"bank-chip-kbank":F==="SCB"?"bank-chip-scb":F==="BBL"?"bank-chip-bbl":F==="KTB"?"bank-chip-ktb":F==="TTB"?"bank-chip-ttb":"bank-chip-other"}function i(q,F){const A=g=>g?String(g).slice(0,10):"?";return!q&&!F?"":A(q)+" ~ "+A(F)}function p(q){return q==null?"":String(q).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function c(q){const F=document.getElementById("reconcile-recent"),A=document.getElementById("reconcile-recent-list");if(!F||!A)return;const g=(q||[]).slice(0,20);if(g.length===0){F.style.display="none";return}F.style.display="",s(!1),A.innerHTML=g.map(f=>{const h=f.parse_status==="parse_failed",I=f.bank_code||"OTHER",L=f.account_last4?" ···"+p(f.account_last4):"",H=i(f.period_start,f.period_end),_=p(f.source_filename||""),M=Number(f.tx_count||0),K=h?'<span class="recon-card-fail" data-i18n="reconcile-card-parse-failed">'+t("reconcile-card-parse-failed")+"</span>":'<span class="recon-card-tx">'+t("reconcile-card-tx").replace("{n}",M)+"</span>";return'<div class="recon-card" data-session-id="'+p(f.id)+'" data-session-name="'+_+'"><span class="bank-chip '+k(I)+'">'+p(I)+'</span><div class="recon-card-main"><div class="recon-card-title">'+_+L+'</div><div class="recon-card-sub">'+p(H)+'</div></div><div class="recon-card-right">'+K+'</div><button class="recon-card-trash" data-trash="'+p(f.id)+'" title="'+p(t("bank-session-delete-tip")||"删除")+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/></svg></button><svg class="recon-card-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg></div>'}).join(""),A.querySelectorAll(".recon-card").forEach(f=>{f.addEventListener("click",h=>{h.target.closest(".recon-card-trash")||(f.dataset.sessionId,r())})}),A.querySelectorAll(".recon-card-trash").forEach(f=>{f.addEventListener("click",h=>{h.stopPropagation();const I=f.dataset.trash,L=f.closest(".recon-card"),H=L&&L.dataset.sessionName||"";typeof window._deleteBankSession=="function"&&window._deleteBankSession(I,H)})})}function r(q){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const F=document.querySelector('[data-recon-tab="bank"]');F&&F.click()},150)}function v(){o(!0),s(!1)}function E(){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const q=document.querySelector('[data-recon-tab="bank"]');q&&q.click()},150)}async function x(){a("pending",0,!0),a("matched",0,!0),a("unmatched",0,!0),u("",!1),o(!1),s(!1);const q=document.getElementById("reconcile-recent");q&&(q.style.display="none");const F={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")};try{const[A,g]=await Promise.all([fetch("/api/bank-recon/stats",{headers:F}),fetch("/api/bank-recon/sessions?limit=20",{headers:F})]);if(!A.ok)throw new Error("http "+A.status);const f=await A.json(),h=g.ok?await g.json():[];l(f||{}),c(h||[])}catch(A){console.warn("[reconcile] load failed",A),v()}}function R(q){if(!q||!q.length)return;const F="Bearer "+(localStorage.getItem("mrpilot_token")||"");let A=0;const g=q.length;Array.from(q).forEach(function(f){const h=new FormData;h.append("file",f,f.name);const I=new XMLHttpRequest;I.open("POST","/api/bank-recon/upload"),I.setRequestHeader("Authorization",F),I.onload=function(){A++;try{const L=JSON.parse(I.responseText);I.status===200&&L.tx_count!==void 0?showToast((t("bank-upload-ok")||"解析成功 · 共 {n} 条流水").replace("{n}",L.tx_count),"success"):showToast(f.name+" "+(t("upload-failed")||"上传失败"),"error")}catch{showToast(f.name+" "+(t("upload-failed")||"上传失败"),"error")}A===g&&setTimeout(x,600)},I.onerror=function(){A++,showToast(f.name+" "+(t("upload-failed")||"上传失败"),"error"),A===g&&setTimeout(x,600)},I.send(h)}),showToast((t("bank-queue-status-uploading")||"上传中")+"…","info")}function D(){if(window.__reconcileBound)return;window.__reconcileBound=!0;const q=document.getElementById("reconcile-bank-file-input");q&&q.addEventListener("change",function(){R(this.files),this.value=""}),document.addEventListener("click",F=>{if(F.target.closest("#btn-reconcile-upload-top")||F.target.closest("#btn-reconcile-upload-empty")){E();return}if(F.target.closest("#btn-reconcile-retry")){x();return}if(F.target.closest("#btn-reconcile-dev-seed")){z();return}})}const w=["468b50c1-5593-4fd6-990d-515ce8085563"];function B(){const q=document.getElementById("btn-reconcile-dev-seed");if(!q)return;const F=typeof _userInfo<"u"?_userInfo:null,A=F&&F.id&&w.indexOf(String(F.id))>=0;q.style.display=A?"":"none"}async function z(){try{const q=await fetch("/api/bank-recon/_dev/seed",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!q.ok)throw new Error("seed:"+q.status);const F=await q.json(),A=(t("reconcile-dev-seed-ok")||"").replace("{n}",F.tx_count||0);showToast(A,"success"),typeof window.navigateTo=="function"?window.navigateTo("automation"):location.hash="#/automation",setTimeout(()=>{const g=document.querySelector('[data-auto-tab="bank"]');g&&g.click(),F.session_id&&typeof window._openBankSession=="function"&&window._openBankSession(F.session_id)},300)}catch(q){console.warn("[reconcile] dev seed failed",q),showToast(t("reconcile-dev-seed-fail")||"Seed failed","error")}}window.loadReconcilePage=async function(){D(),B(),typeof window._bankReconV2Init=="function"&&window._bankReconV2Init();try{await x()}catch{}},window._rerenderReconcile=function(){typeof currentRoute=="string"&&currentRoute==="reconcile"&&x().catch(()=>{})},typeof window.subscribeI18n=="function"&&window.subscribeI18n("reconcile",window._rerenderReconcile)})();(function(){const e=document.getElementById("assign-clients-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
    </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e={employeeId:null,employeeName:"",clients:[],selected:new Set,opened:!1};function n(){return document.getElementById("assign-clients-modal")}function a(){return document.getElementById("assign-clients-list")}function o(){return document.getElementById("assign-select-all")}function s(){return document.getElementById("assign-selected-count")}function u(){return document.getElementById("assign-modal-target")}function l(){const x=a();if(x){if(!e.clients.length){x.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-no-clients")||"暂无客户 · 请先到「客户管理」添加")+"</div>";return}x.innerHTML=e.clients.map(R=>{const D=String(R.id),w=e.selected.has(D)?"checked":"",B=escapeHtml(R.name||R.label||"#"+D),z=R.code?'<span class="assign-row-code">'+escapeHtml(R.code)+"</span>":"";return'<label class="assign-row"><input type="checkbox" data-cid="'+escapeHtml(D)+'" '+w+'><span class="assign-row-name">'+B+"</span>"+z+"</label>"}).join(""),k()}}function k(){const x=s();if(x){const D=t("assign-selected-count")||"已选 {n} / {total}";x.textContent=D.replace("{n}",e.selected.size).replace("{total}",e.clients.length)}const R=o();R&&(R.checked=e.clients.length>0&&e.selected.size===e.clients.length)}function i(){const x=u();x&&(x.textContent=e.employeeName?" · "+e.employeeName:"")}async function p(x,R){e.employeeId=x,e.employeeName=R||"",e.opened=!0,e.selected=new Set,e.clients=[],i();const D=a();D&&(D.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-loading")||"加载中...")+"</div>");const w=n();w&&(w.style.display="flex");try{const[B,z]=await Promise.all([apiGet("/api/clients?include_inactive=false"),apiGet("/api/team/employees/"+encodeURIComponent(x)+"/assignments")]);e.clients=B&&B.clients||[];const q=z&&z.client_ids||[];e.selected=new Set(q.map(String)),l()}catch(B){console.error("[assign-clients] load failed",B);const z=a();z&&(z.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-load-failed")||"加载失败 · 请重试")+"</div>")}}function c(){e.opened=!1;const x=n();x&&(x.style.display="none")}async function r(){if(!e.employeeId)return;const x=Array.from(e.selected).map(D=>parseInt(D,10)).filter(D=>!isNaN(D)),R=document.getElementById("assign-modal-save");R&&(R.disabled=!0);try{const D=await apiPost("/api/team/employees/"+encodeURIComponent(e.employeeId)+"/assignments",{client_ids:x});D&&D.ok!==!1?(showToast((t("assign-saved")||"已保存 {n} 个客户分配").replace("{n}",x.length),"success"),c(),typeof loadTeamList=="function"&&loadTeamList()):showToast(t("assign-save-failed")||"保存失败","error")}catch(D){console.error("[assign-clients] save failed",D),showToast(t("assign-save-failed")||"保存失败","error")}finally{R&&(R.disabled=!1)}}function v(){const x=n();if(!x||x.dataset.bound==="1")return;x.dataset.bound="1";const R=document.getElementById("assign-modal-close");R&&R.addEventListener("click",c);const D=document.getElementById("assign-modal-cancel");D&&D.addEventListener("click",c);const w=document.getElementById("assign-modal-save");w&&w.addEventListener("click",r),x.addEventListener("click",function(q){q.target===x&&c()});const B=o();B&&B.addEventListener("change",function(){B.checked?e.selected=new Set(e.clients.map(q=>String(q.id))):e.selected=new Set,l()});const z=a();z&&z.addEventListener("change",function(q){const F=q.target.closest('input[type="checkbox"][data-cid]');if(!F)return;const A=F.dataset.cid;F.checked?e.selected.add(A):e.selected.delete(A),k()})}function E(){e.opened&&(i(),l())}typeof window.subscribeI18n=="function"&&window.subscribeI18n("assign-clients-modal",E),window.openAssignClientsModal=function(x,R){v(),p(x,R)}})();(function(){const e={page:1,per_page:50,q:"",total:0,rows:[],loaded:!1};function n(c){if(!c)return"";try{return new Date(c).toLocaleString()}catch{return c}}function a(c){const r=document.getElementById("access-log-table");r&&(r.innerHTML='<div class="access-log-empty">'+escapeHtml(c)+"</div>");const v=document.getElementById("access-log-pager");v&&(v.innerHTML="")}function o(){const c=document.getElementById("access-log-table");if(!c)return;const r=e.rows||[];if(!r.length){a(t("set-access-log-empty"));return}const v=`
            <div class="access-log-row access-log-head">
                <div>${escapeHtml(t("set-access-log-col-time"))}</div>
                <div>${escapeHtml(t("set-access-log-col-actor"))}</div>
                <div>${escapeHtml(t("set-access-log-col-action"))}</div>
                <div>${escapeHtml(t("set-access-log-col-target"))}</div>
                <div>${escapeHtml(t("set-access-log-col-ip"))}</div>
            </div>`,E=r.map(function(x){return`
                <div class="access-log-row">
                    <div class="access-log-time" data-label="${escapeHtml(t("set-access-log-col-time"))}">${escapeHtml(n(x.created_at))}</div>
                    <div class="access-log-actor" data-label="${escapeHtml(t("set-access-log-col-actor"))}">${escapeHtml(x.actor_username||"-")}</div>
                    <div data-label="${escapeHtml(t("set-access-log-col-action"))}"><span class="access-log-action">${escapeHtml(x.action||"-")}</span></div>
                    <div class="access-log-target" data-label="${escapeHtml(t("set-access-log-col-target"))}">${escapeHtml(x.target_name||x.target_type||"-")}</div>
                    <div class="access-log-ip" data-label="${escapeHtml(t("set-access-log-col-ip"))}">${escapeHtml(x.ip||"-")}</div>
                </div>`}).join("");c.innerHTML=v+E}function s(){const c=document.getElementById("access-log-pager");if(!c)return;const r=e.total||0;if(!r){c.innerHTML="";return}const v=e.page||1,E=e.per_page,x=Math.max(1,Math.ceil(r/E)),R=(t("set-access-log-pager-total")||"Total {n}").replace("{n}",r),D=(t("set-access-log-pager-page")||"Page {p} / {t}").replace("{p}",v).replace("{t}",x);c.innerHTML=`
            <div class="access-log-pager-info">${escapeHtml(R)}</div>
            <div class="access-log-pager-ctrl">
                <button class="access-log-pager-btn" type="button" data-access-log-page="${v-1}" ${v<=1?"disabled":""}>← ${escapeHtml(t("set-access-log-pager-prev"))}</button>
                <span class="access-log-pager-page">${escapeHtml(D)}</span>
                <button class="access-log-pager-btn" type="button" data-access-log-page="${v+1}" ${v>=x?"disabled":""}>${escapeHtml(t("set-access-log-pager-next"))} →</button>
            </div>`}async function u(c){const r=localStorage.getItem("mrpilot_token");if(r){e.page=c||1,a(t("set-access-log-loading"));try{const v="/api/me/access_log?page="+e.page+"&per_page="+e.per_page+"&q="+encodeURIComponent(e.q||""),E=await fetch(v,{headers:{Authorization:"Bearer "+r}});if(E.status===403){a(t("set-access-log-empty"));return}if(!E.ok)throw new Error("http_"+E.status);const x=await E.json();e.rows=x.logs||[],e.total=x.total||0,e.loaded=!0,o(),s()}catch{a(t("set-access-log-fail"))}}}async function l(){const c=localStorage.getItem("mrpilot_token");if(c)try{const r="/api/me/access_log.csv?q="+encodeURIComponent(e.q||""),v=await fetch(r,{headers:{Authorization:"Bearer "+c}});if(!v.ok){showToast(t("set-access-log-csv-fail")||"Export failed","error");return}const E=await v.blob(),x=document.createElement("a"),R=URL.createObjectURL(E);x.href=R,x.download="pearnly_access_log.csv",document.body.appendChild(x),x.click(),setTimeout(function(){URL.revokeObjectURL(R),x.remove()},100),showToast(t("set-access-log-csv-ok")||"Exported","success")}catch{showToast(t("set-access-log-csv-fail")||"Export failed","error")}}function k(){const c=document.querySelectorAll(".set-tab-owner-only"),r=!!(_userInfo&&(_userInfo.role==="owner"||_userInfo.is_super_admin));c.forEach(function(v){v.style.display=r?"":"none"})}document.addEventListener("click",function(c){if(c.target.closest('.settings-tab[data-tab="access-log"]')){setTimeout(function(){(!e.loaded||e.page!==1)&&u(1)},50);return}if(c.target.closest("#access-log-csv-btn")){c.preventDefault(),l();return}const E=c.target.closest(".access-log-pager-btn[data-access-log-page]");if(E&&!E.disabled){const x=parseInt(E.dataset.accessLogPage,10);u(x)}}),document.addEventListener("input",function(c){c.target&&c.target.id==="access-log-search"&&(clearTimeout(window.__accessLogSearchTimer),window.__accessLogSearchTimer=setTimeout(function(){e.q=(c.target.value||"").trim(),u(1)},350))});let i=0;const p=setInterval(function(){i++,_userInfo&&(k(),clearInterval(p)),i>60&&clearInterval(p)},500);typeof window.subscribeI18n=="function"&&window.subscribeI18n("me-access-log",function(){k(),e.loaded&&(o(),s())})})();(function(){const e=document.getElementById("notif-new-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=A=>document.getElementById(A);async function n(A,g){return await fetch(A,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(g||{})})}async function a(A){return await fetch(A,{method:"DELETE",headers:{Authorization:"Bearer "+token}})}let o=null;async function s(){try{o=await apiGet("/api/line/binding")}catch{o={bound:!1}}return o}function u(A,g){if(!A)return;A.style.display="",A.className="notif-line-check "+(g?"bound":"unbound");const f=g?'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>';A.innerHTML=f+"<span>"+escapeHtml(t(g?"notif-line-bound":"notif-line-not-bound"))+"</span>"}function l(A){if(A==null)return"-";const g=Number(A);return isNaN(g)?String(A):"฿ "+g.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function k(A){if(!A)return"-";try{const g=new Date(A),f=(g.getMonth()+1).toString().padStart(2,"0"),h=g.getDate().toString().padStart(2,"0"),I=g.getHours().toString().padStart(2,"0"),L=g.getMinutes().toString().padStart(2,"0");return`${f}-${h} ${I}:${L}`}catch{return A}}function i(A){const g=e("notif-rules-list"),f=e("notif-rules-empty"),h=e("notif-rules-count");if(!(!g||!f)){if(h.textContent=String(A.length),h.className="auto-status-pill "+(A.length>0?"active":"none"),!A.length){f.style.display="",g.style.display="none",g.innerHTML="";return}f.style.display="none",g.style.display="",g.innerHTML=A.map(I=>{const L=I.template_code==="large_invoice",H=L?"notif-rule-large-tag":"notif-rule-exception-tag",_=L?"large":"";let M=[];if(L){const G=I.params&&I.params.threshold?l(I.params.threshold):"-";M.push(escapeHtml(t("notif-rule-threshold-prefix"))+" "+G)}I.enabled||M.push('<span style="color:#9ca3af;">'+escapeHtml(t("notif-rule-disabled"))+"</span>");const K=M.length?M.join(' <span class="dot"></span> '):"";return`
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
                </div>`}).join("")}}function p(A){const g=e("notif-logs-list");if(g){if(!A.length){g.innerHTML='<div class="notif-logs-empty">'+escapeHtml(t("notif-logs-empty"))+"</div>";return}g.innerHTML=A.map(f=>{const h=f.status==="sent",I=f.event_type==="exception_high"?"notif-event-exception-high":f.event_type==="large_invoice"?"notif-event-large-invoice":"notif-event-test-send",L=h?"":" · "+escapeHtml(f.error||"failed");return`
                <div class="notif-log-row">
                    <span class="notif-log-status ${h?"":"failed"}"></span>
                    <div class="notif-log-main">
                        <div class="notif-log-event">${escapeHtml(t(I))}</div>
                        <div class="notif-log-meta">${escapeHtml(f.template_code||"-")}${L}</div>
                    </div>
                    <div class="notif-log-time">${k(f.sent_at)}</div>
                </div>`}).join("")}}async function c(){try{const A=await apiGet("/api/notifications/rules");r=A&&A.items||[],i(r)}catch(A){console.warn("load rules fail",A)}try{const A=await apiGet("/api/notifications/logs?limit=20");v=A&&A.items||[],p(v)}catch(A){console.warn("load logs fail",A)}}let r=null,v=null;function E(){r&&i(r),v&&p(v);const A=e("notif-new-modal");A&&A.style.display!=="none"&&o&&u(e("notif-line-check"),!!(o&&o.bound))}function x(){const A=e("notif-new-modal");A&&(A.style.display="",e("notif-new-name").value="",e("notif-new-threshold").value="",e("notif-new-threshold-row").style.display="none",document.querySelectorAll('input[name="notif-template"]').forEach(g=>g.checked=!1),s().then(g=>u(e("notif-line-check"),!!(g&&g.bound))))}function R(){const A=e("notif-new-modal");A&&(A.style.display="none")}function D(){const A=document.querySelector('input[name="notif-template"]:checked'),g=e("notif-new-threshold-row");if(!A){g.style.display="none";return}g.style.display=A.value==="large_invoice"?"":"none";const f=e("notif-new-name");f&&!f.value.trim()&&(f.value=A.value==="large_invoice"?t("notif-tmpl-large-name"):t("notif-tmpl-exception-name"))}async function w(){const A=document.querySelector('input[name="notif-template"]:checked');if(!A){showToast(t("notif-new-template"),"error");return}const g=(e("notif-new-name").value||"").trim();if(!g){showToast(t("notif-name-required"),"error");return}const f={name:g,template_code:A.value,params:{},enabled:!0};if(A.value==="large_invoice"){const h=parseFloat(e("notif-new-threshold").value||"0");if(!h||h<=0){showToast(t("notif-threshold-required"),"error");return}f.params.threshold=h}try{const h=await apiPost("/api/notifications/rules",f);if(h&&h.ok)showToast(t("notif-toast-created"),"success"),R(),c();else{const I=await(h&&h.json&&h.json().catch(()=>({})))||{};showToast(I&&I.detail||"save failed","error")}}catch{showToast("save failed","error")}}async function B(A,g,f){if(A==="toggle"){const h=f.classList.contains("on"),I=await n("/api/notifications/rules/"+g,{enabled:!h});I&&I.ok?(showToast(t(h?"notif-toast-toggled-off":"notif-toast-toggled-on"),"success"),c()):showToast("toggle failed","error");return}if(A==="test"){const h=await s();if(!h||!h.bound){showToast(t("notif-line-error-bind-first"),"error");return}const I=await apiPost("/api/notifications/rules/"+g+"/test",{});if(I&&I.ok)showToast(t("notif-toast-test-sent"),"success"),c();else{const L=await(I&&I.json&&I.json().catch(()=>({})))||{},H=L&&L.detail||"";showToast(H||t("notif-toast-test-failed"),"error"),c()}return}if(A==="delete"){if(!await showConfirm(t("notif-confirm-delete"),{danger:!0}))return;const I=await a("/api/notifications/rules/"+g);I&&I.ok?(showToast(t("notif-toast-deleted"),"success"),c()):showToast("delete failed","error");return}}let z=!1;function q(){if(z)return;z=!0;const A=e("notif-btn-new");A&&A.addEventListener("click",x);const g=e("notif-btn-refresh-logs");g&&g.addEventListener("click",c);const f=e("notif-new-close");f&&f.addEventListener("click",R);const h=e("notif-new-cancel");h&&h.addEventListener("click",R);const I=e("notif-new-save");I&&I.addEventListener("click",w),document.querySelectorAll('input[name="notif-template"]').forEach(_=>{_.addEventListener("change",D)});const L=e("notif-rules-list");L&&L.addEventListener("click",_=>{const M=_.target.closest("button[data-action]");if(!M)return;const K=M.closest("[data-rule-id]");K&&B(M.getAttribute("data-action"),K.getAttribute("data-rule-id"),M)});const H=e("notif-new-modal");H&&H.addEventListener("click",_=>{_.target===H&&R()})}async function F(){q(),await c()}window._loadNotificationsPanel=F,window._rerenderNotifications=E})();(function(){function n(w,B){try{return window.t&&window.t(w)||B}catch{return B}}function a(){var w="";try{w=localStorage.getItem("mrpilot_token")||""}catch{}return w?{Authorization:"Bearer "+w}:{}}var o=[{tbody:"vex-task-tbody",api:"/api/recon/tasks/batch_delete",reload:function(){try{window.loadRecentTasks&&window.loadRecentTasks()}catch{}},kind:"vex"},{tbody:"glv-history-tbody",api:"/api/recon/gl-vat/tasks/batch_delete",reload:function(){try{window._loadGlvHistory&&window._loadGlvHistory()}catch{}},kind:"glv"},{tbody:"brv2-history-tbody",api:"/api/recon/bank-v2/tasks/batch_delete",reload:function(){try{window._brv2LoadHistory&&window._brv2LoadHistory()}catch{}},kind:"brv2"}];function s(){if(!document.getElementById("recon-batch-style")){var w=document.createElement("style");w.id="recon-batch-style",w.textContent=".recon-sel-cell{width:36px;text-align:center;padding-left:10px!important;padding-right:6px!important}.recon-sel-cb,.recon-master-cb{cursor:pointer;width:14px;height:14px;accent-color:#111;margin:0;vertical-align:middle}th.recon-time-col,td.recon-time-col{white-space:nowrap}tr.recon-thead-batch{display:none}thead.recon-batch-mode tr.recon-thead-default{display:none}thead.recon-batch-mode tr.recon-thead-batch{display:table-row}tr.recon-thead-batch th{background:#fafaf8;border-bottom:1px solid #e8e8e3;padding:8px 12px}tr.recon-thead-batch .recon-batch-inline{display:flex;align-items:center;gap:10px;font-size:12px;color:#111;font-weight:normal}tr.recon-thead-batch .recon-batch-count-inline{font-weight:600;color:#111;margin-right:4px}tr.recon-thead-batch .recon-batch-del-inline{background:#dc2626;color:#fff;border:none;border-radius:6px;padding:4px 10px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:4px}tr.recon-thead-batch .recon-batch-del-inline:hover{background:#b91c1c}tr.recon-thead-batch .recon-batch-clear-inline{background:transparent;border:none;color:#555;cursor:pointer;font-size:12px;font-family:inherit;text-decoration:underline;padding:4px 2px}tr.recon-thead-batch .recon-batch-clear-inline:hover{color:#111}.recon-batch-bar{display:none!important}",document.head.appendChild(w)}}function u(w){return w?w.dataset&&w.dataset.taskId?w.dataset.taskId:w.dataset&&w.dataset.taskid?w.dataset.taskid:"":""}function l(w){var B=document.getElementById(w.tbody);if(!B)return null;var z=B.closest("table");if(!z)return null;var q=z.querySelector("thead");if(!q)return null;if(q._reconReady)return q;var F=q.querySelector("tr");if(!F)return null;if(F.classList.add("recon-thead-default"),!F.querySelector(".recon-master-cb")){var A=document.createElement("th");A.className="recon-sel-cell";var g=document.createElement("input");g.type="checkbox",g.className="recon-master-cb",g.setAttribute("aria-label","select all"),g.addEventListener("change",function(){c(w,g.checked)}),A.appendChild(g),F.insertBefore(A,F.firstElementChild)}var f=F.children[1];f&&!f.classList.contains("recon-time-col")&&f.classList.add("recon-time-col");var h=F.children.length,I=document.createElement("tr");I.className="recon-thead-batch";var L=document.createElement("th");L.className="recon-sel-cell";var H=document.createElement("input");H.type="checkbox",H.className="recon-master-cb",H.checked=!0,H.setAttribute("aria-label","select all"),H.addEventListener("change",function(){c(w,H.checked)}),L.appendChild(H);var _=document.createElement("th");return _.setAttribute("colspan",String(h-1)),_.innerHTML='<div class="recon-batch-inline"><span class="recon-batch-count-inline" data-recon-count></span><button type="button" class="recon-batch-del-inline" data-recon-del><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg><span data-recon-del-label></span></button><button type="button" class="recon-batch-clear-inline" data-recon-clear></button></div>',I.appendChild(L),I.appendChild(_),q.appendChild(I),_.querySelector("[data-recon-del]").addEventListener("click",function(){x(w)}),_.querySelector("[data-recon-clear]").addEventListener("click",function(){E(w)}),q._reconReady=!0,v(w),q}function k(w){var B=document.getElementById(w.tbody);if(B){var z=B.querySelectorAll("tr");z.forEach(function(q){var F=u(q);if(F&&!q.querySelector(".recon-sel-cb")){var A=q.querySelector("td");if(A){var g=document.createElement("td");g.className="recon-sel-cell";var f=document.createElement("input");f.type="checkbox",f.className="recon-sel-cb",f.dataset.taskId=F,f.dataset.kind=w.kind,f.addEventListener("click",function(I){I.stopPropagation()}),f.addEventListener("change",function(){r(w)}),g.appendChild(f),q.insertBefore(g,A);var h=q.children[1];h&&!h.classList.contains("recon-time-col")&&h.classList.add("recon-time-col")}}}),r(w)}}function i(w){var B=document.getElementById(w.tbody);return B?Array.prototype.slice.call(B.querySelectorAll(".recon-sel-cb")):[]}function p(w){return i(w).filter(function(B){return B.checked}).map(function(B){return B.dataset.taskId})}function c(w,B){i(w).forEach(function(z){z.checked=!!B}),r(w)}function r(w){var B=p(w),z=i(w),q=document.getElementById(w.tbody);if(q){var F=q.closest("table"),A=F&&F.querySelector("thead");if(A){B.length>0?A.classList.add("recon-batch-mode"):A.classList.remove("recon-batch-mode"),A.querySelectorAll(".recon-master-cb").forEach(function(f){if(z.length===0){f.checked=!1,f.indeterminate=!1;return}B.length===z.length?(f.checked=!0,f.indeterminate=!1):B.length===0?(f.checked=!1,f.indeterminate=!1):(f.checked=!1,f.indeterminate=!0)});var g=A.querySelector("[data-recon-count]");g&&(g.textContent=n("recon-batch-selected-n","已选 {n} 条").replace("{n}",B.length))}}}function v(w){var B=document.getElementById(w.tbody);if(B){var z=B.closest("table"),q=z&&z.querySelector("thead");if(q){var F=q.querySelector("[data-recon-del-label]"),A=q.querySelector("[data-recon-clear]");F&&(F.textContent=n("recon-batch-delete","批量删除")),A&&(A.textContent=n("recon-batch-clear","取消")),r(w)}}}function E(w){i(w).forEach(function(B){B.checked=!1}),r(w)}async function x(w){var B=p(w);if(B.length){var z=n("recon-batch-delete-confirm","确定删除选中的 {n} 条对账任务?此操作不可恢复").replace("{n}",B.length),q=!1;try{typeof window.pearnlyConfirm=="function"?q=await window.pearnlyConfirm(z,n("recon-batch-delete-title","批量删除")):q=window.confirm(z)}catch{q=!1}if(q)try{var F=Object.assign({"Content-Type":"application/json"},a()),A=w.kind==="glv"?B.map(function(I){return parseInt(I,10)}):B,g=await fetch(w.api,{method:"POST",headers:F,body:JSON.stringify({ids:A})});if(!g.ok){typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error");return}var f=await g.json(),h=f&&(f.deleted!=null?f.deleted:f.count)||B.length;typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-ok","已删除 {n} 条").replace("{n}",h),"success"),w.reload()}catch{typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error")}}}function R(w){l(w),k(w);var B=document.getElementById(w.tbody);if(!(!B||B._reconBatchWatched)){B._reconBatchWatched=!0;var z=new MutationObserver(function(){k(w)});z.observe(B,{childList:!0,subtree:!1})}}function D(){s(),o.forEach(R),document.querySelectorAll(".recon-batch-bar").forEach(function(w){try{w.remove()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",D):D(),setTimeout(D,1500),setTimeout(D,4e3),document.addEventListener("keydown",function(w){w.key==="Escape"&&o.forEach(function(B){p(B).length>0&&E(B)})}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-batch-thead",function(){o.forEach(v)})})();(function(){let e={role:"",monthly_volume:"",country:"",line_id:""},n=1;const a=4,o="pilot_ob_dismiss",s="pilot_ob_done";window.maybeShowOnboarding=function(p){};function u(p){n=p;for(let v=1;v<=a;v++){const E=document.getElementById("ob-step-"+v);E&&(E.style.display=v===p?"block":"none")}document.querySelectorAll(".ob-dot").forEach(v=>{const E=parseInt(v.dataset.step,10);v.classList.toggle("active",E===p),v.classList.toggle("done",E<p)});const c=document.getElementById("ob-step-label");c&&(c.textContent=p+" / "+a);const r=document.getElementById("ob-next");if(r&&(r.textContent=p===a?t("ob-finish"):t("ob-next")),p===4){const v=document.getElementById("ob-line-input");v&&(v.value=e.line_id||"")}}function l(p){const c=document.querySelector(".onboarding-modal");if(!c)return;let r=c.querySelector(".ob-feedback");r||(r=document.createElement("div"),r.className="ob-feedback",c.appendChild(r)),r.textContent=p,r.classList.add("show"),setTimeout(()=>r.classList.remove("show"),1800)}document.addEventListener("click",p=>{const c=p.target.closest(".ob-option");if(!c)return;const r=c.parentElement;if(!r||!r.classList.contains("ob-options"))return;r.querySelectorAll(".ob-option").forEach(E=>E.classList.remove("selected")),c.classList.add("selected");const v=c.dataset.value;r.id==="ob-role-options"?e.role=v:r.id==="ob-volume-options"?e.monthly_volume=v:r.id==="ob-country-options"&&(e.country=v)}),document.addEventListener("click",p=>{p.target.id==="ob-skip"&&k()}),document.addEventListener("click",p=>{if(p.target.id==="ob-next"){if(n===4){const c=document.getElementById("ob-line-input");e.line_id=(c&&c.value||"").trim().replace(/^@+/,"")}k()}}),document.addEventListener("click",p=>{if(p.target.closest("#ob-close")){localStorage.setItem(o,String(Date.now()));const c=document.getElementById("onboarding-modal");c&&(c.style.display="none")}});function k(){n===1&&e.role?l(t("ob-fb-role")):n===2&&e.monthly_volume?l(t("ob-fb-volume")):n===3&&e.country?l(t("ob-fb-country")):n===4&&e.line_id&&l(t("ob-fb-line")),n<a?setTimeout(()=>u(n+1),e[Object.keys(e)[n-1]]?350:0):i()}async function i(){const p=document.getElementById("onboarding-modal");localStorage.setItem(s,"1"),localStorage.removeItem(o);const c={};if(e.role&&(c.role=e.role),e.monthly_volume&&(c.monthly_volume=e.monthly_volume),e.country&&(c.country=e.country),e.line_id&&(c.line_id=e.line_id),Object.keys(c).length===0){p&&(p.style.display="none");return}try{const r=await fetch("/api/me/profile",{method:"PUT",headers:{Authorization:"Bearer "+(window.token||localStorage.getItem("mrpilot_token")),"Content-Type":"application/json"},body:JSON.stringify(c)});r.ok?(l(t("ob-fb-done")),window._userInfo&&Object.assign(window._userInfo,c),setTimeout(()=>{p&&(p.style.display="none")},1200)):(localStorage.setItem("pilot_ob_pending",JSON.stringify(c)),console.warn("onboarding profile save failed",r.status),l(t("ob-fb-saved-local")),setTimeout(()=>{p&&(p.style.display="none")},1500))}catch(r){console.error("onboarding submit",r),localStorage.setItem("pilot_ob_pending",JSON.stringify(c)),p&&(p.style.display="none")}}})();(function(){const e=document.getElementById("archive-rule-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
        </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e=[],n="by_month_seller",a=-1,o=!1;const s={date:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="3.5" width="11" height="10" rx="1.5"/><path d="M2.5 6.5h11M5.5 2v3M10.5 2v3"/></svg>',seller:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13.5V4a1 1 0 011-1h5a1 1 0 011 1v9.5"/><path d="M10 7h2.5a.5.5 0 01.5.5v6"/><path d="M5 6h1M5 9h1M5 12h1M13.5 13.5h-12"/></svg>',category:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 2h6L13 5.5v7.5a1 1 0 01-1 1H3.5a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M9 2v4h4"/><path d="M5 9h6M5 11.5h4"/></svg>',amount:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M8 4.5v7M10 6.3a1.8 1.8 0 00-4 0c0 .9.7 1.3 2 1.6s2 .8 2 1.6a1.8 1.8 0 01-4 0"/></svg>',invoice:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3.5l1.5 10.5 1.5-1 1.5 1 1.5-1 1.5 1 1.5-1 1.5 1L13 3.5z"/><path d="M5.5 6.5h5M5.5 9h5M5.5 11.5h3"/></svg>',buyer:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="6" r="2.5"/><path d="M3 13.5c0-2.5 2.2-4.5 5-4.5s5 2 5 4.5"/></svg>',sep:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v10"/></svg>'},u={date:{label:"field-date",defaultCfg:{format:"YYYY-MM-DD"}},seller:{label:"field-seller",defaultCfg:{short:!0}},category:{label:"field-category",defaultCfg:{}},amount:{label:"field-amount",defaultCfg:{with_currency:!0}},invoice:{label:"field-invoice",defaultCfg:{}},buyer:{label:"field-buyer",defaultCfg:{}},sep:{label:"field-sep",defaultCfg:{val:"_"}}};function l(){return{zh:"运费",en:"Shipping",th:"ค่าขนส่ง",ja:"送料"}[currentLang]||"Shipping"}function k(){return"DHL Express (Thailand) Co., Ltd."}function i(){return{merged_fields:{invoice_date:"2026-04-15",seller_name:k(),category:l(),total_amount:1250,currency:"THB",invoice_no:"INV-2026030002",buyer_name:"Mr.ERP Co., Ltd."}}}window.loadAboutPanel=()=>p(),window.loadPrefsSettings=()=>c(),window.loadArchiveSettings=()=>v();function p(){const g=document.getElementById("settings-contact-grid");if(!g)return;const f=_contact?.phone||"086-889-2228",h=_contact?.line_id||"@Pearnly",I=_contact?.line_url||"https://line.me/R/ti/p/@059oupmg",L=_contact?.email||"hello@pearnly.com",H=_contact?.address||"Bangkok, Thailand";g.innerHTML=`
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
                    <div class="contact-value">${escapeHtml(H)}</div>
                </div>
            </div>
        `}async function c(){try{const g=await fetch("/api/settings/dup-check",{headers:{Authorization:"Bearer "+token}});if(!g.ok)return;const f=await g.json(),h=document.getElementById("pref-dup-check");h&&(h.checked=!!f.enabled)}catch(g){console.warn("load prefs failed",g)}}const r=document.getElementById("pref-dup-check");r&&!r.dataset.bound&&(r.dataset.bound="1",r.addEventListener("change",async g=>{const f=g.target.checked;try{(await fetch("/api/settings/dup-check",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({enabled:f})})).ok?showToast(f?t("pref-dup-check-on-toast"):t("pref-dup-check-off-toast"),"success"):(g.target.checked=!f,showToast(t("pref-save-failed"),"error"))}catch{g.target.checked=!f,showToast(t("pref-save-failed"),"error")}}));async function v(){const g=!!(_userInfo&&_userInfo.can_customize_archive);o=!g;const f=document.getElementById("archive-upgrade-banner");f&&(f.style.display=g?"none":"");const h=document.getElementById("archive-plus-badge");h&&(h.style.display=g?"none":"");try{const I=await fetch("/api/archive/settings",{headers:{Authorization:"Bearer "+token}});if(!I.ok)throw new Error("load failed");const L=await I.json();e=Array.isArray(L.name_template)?L.name_template:[],n=L.folder_strategy||"by_month_seller"}catch(I){console.error("load archive settings failed",I),showToast(t("archive-load-failed"),"error");return}E(),x(),R(),D()}function E(){const g=document.getElementById("archive-rule-canvas");if(g){if(e.length===0){g.innerHTML=`<div class="archive-empty">${escapeHtml(t("archive-rule-empty"))}</div>`;return}g.innerHTML=e.map((f,h)=>{const I=u[f.type]||{label:f.type},L=s[f.type]||"",H=f.type==="sep"?`"${escapeHtml(f.val||"_")}"`:escapeHtml(t(I.label));return`
                <span class="archive-token ${f.type}"
                      data-token-idx="${h}"
                      draggable="${o?"false":"true"}">
                    <span class="token-icon">${L}</span>
                    <span class="token-label">${H}</span>
                </span>
            `}).join("")}}function x(){const g=document.getElementById("archive-field-palette");if(!g)return;const f=["date","seller","category","amount","invoice","buyer","sep"];g.innerHTML=f.map(h=>{const I=u[h],L=s[h]||"";return`
                <button class="archive-palette-btn ${h}" data-add-field="${h}" ${o?"disabled":""}>
                    <span class="token-icon">${L}</span>
                    <span>${escapeHtml(t(I.label))}</span>
                </button>
            `}).join("")}function R(){document.querySelectorAll('input[name="folder-strategy"]').forEach(g=>{g.checked=g.value===n,g.disabled=o})}async function D(){const g=document.getElementById("archive-preview-name"),f=document.getElementById("archive-preview-hint");if(f&&(f.textContent=t("archive-preview-hint",{category:l()})),!!g){if(e.length===0){g.textContent="-";return}try{const I=await(await fetch("/api/archive/rename-preview",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({merged_fields:i().merged_fields,name_template:e})})).json();g.textContent=(I.name||"-")+".pdf"}catch{g.textContent="("+t("archive-preview-error")+")"}}}window._rerenderArchiveAll=function(){const g=document.getElementById("archive-rule-modal");!g||g.style.display==="none"||(E(),x(),D())};let w=-1;document.addEventListener("dragstart",g=>{const f=g.target.closest(".archive-token");!f||o||(w=parseInt(f.dataset.tokenIdx,10),f.classList.add("dragging"),g.dataTransfer.effectAllowed="move")}),document.addEventListener("dragend",g=>{document.querySelectorAll(".archive-token").forEach(f=>f.classList.remove("dragging","drop-target")),w=-1}),document.addEventListener("dragover",g=>{const f=g.target.closest(".archive-token");f&&(g.preventDefault(),g.dataTransfer.dropEffect="move",document.querySelectorAll(".archive-token").forEach(h=>h.classList.remove("drop-target")),f.classList.add("drop-target"))}),document.addEventListener("drop",g=>{const f=g.target.closest(".archive-token");if(!f||w<0||o)return;g.preventDefault();const h=parseInt(f.dataset.tokenIdx,10);if(h===w)return;const I=e.splice(w,1)[0];e.splice(h,0,I),w=-1,E(),D()}),document.addEventListener("click",g=>{if(g.target.closest("#btn-open-archive-rule")||g.target.closest("#btn-open-archive-rule-from-settings")){const L=document.getElementById("archive-rule-modal");L&&(L.style.display="",v());return}if(g.target.closest("#archive-rule-modal-close")||g.target.id==="archive-rule-modal"){const L=document.getElementById("archive-rule-modal");L&&(L.style.display="none");return}const f=g.target.closest(".settings-nav-item");if(f){switchSettingsTab(f.dataset.settingsTab);return}if(o&&g.target.closest(".archive-token, [data-add-field], #btn-archive-save, #btn-archive-reset")){showToast(t("feature-contact-us"),"info");return}const h=g.target.closest("[data-add-field]");if(h){const L=h.dataset.addField,H=u[L],_={type:L,...H.defaultCfg};e.push(_),E(),D();return}const I=g.target.closest(".archive-token");if(I&&!o){B(parseInt(I.dataset.tokenIdx,10));return}if(g.target.closest("#btn-archive-save"))return F();if(g.target.closest("#btn-archive-reset"))return A();(g.target.closest("#archive-token-close")||g.target.id==="archive-token-modal")&&(document.getElementById("archive-token-modal").style.display="none"),g.target.closest("#btn-archive-token-ok")&&z(),g.target.closest("#btn-archive-token-delete")&&q()}),document.addEventListener("change",g=>{g.target.name==="folder-strategy"&&(n=g.target.value)});function B(g){a=g;const f=e[g];if(!f)return;const h=document.getElementById("archive-token-body");let I="";f.type==="date"?I=`
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
                </div>`:I=`<div class="form-hint">${escapeHtml(t("archive-token-no-option"))}</div>`,h.innerHTML=I,document.getElementById("archive-token-modal").style.display="",h.querySelectorAll(".sep-chip").forEach(L=>{L.addEventListener("click",()=>{h.querySelectorAll(".sep-chip").forEach(_=>_.classList.remove("active")),L.classList.add("active");const H=document.getElementById("token-sep-custom");H&&(H.value="")})})}function z(){const g=e[a];if(g){if(g.type==="date")g.format=document.getElementById("token-date-format").value;else if(g.type==="seller")g.short=document.getElementById("token-seller-short").checked;else if(g.type==="amount")g.with_currency=document.getElementById("token-amount-currency").checked;else if(g.type==="sep"){const f=document.querySelector("#archive-token-body .sep-chip.active"),h=document.getElementById("token-sep-custom").value;g.val=h||(f?f.dataset.sep:"_")}document.getElementById("archive-token-modal").style.display="none",E(),D()}}function q(){a<0||(e.splice(a,1),document.getElementById("archive-token-modal").style.display="none",E(),D())}async function F(){if(e.length===0){showToast(t("archive-rule-cannot-empty"),"error");return}try{if(!(await fetch("/api/archive/settings",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({name_template:e,folder_strategy:n})})).ok)throw new Error("save failed");showToast(t("archive-save-ok"),"success");const f=document.getElementById("archive-rule-modal");f&&(f.style.display="none")}catch{showToast(t("archive-save-fail"),"error")}}async function A(){await showConfirm(t("archive-reset-confirm"),{danger:!0})&&(e=[{type:"date",format:"YYYY-MM-DD"},{type:"sep",val:"_"},{type:"seller",short:!0},{type:"sep",val:"_"},{type:"category"},{type:"sep",val:"_"},{type:"amount",with_currency:!0}],n="by_month_seller",E(),R(),D())}})();(function(){const o="pearnly_big_batch_tip_shown";let s=null,u=null,l=0,k=0,i=!1;function p(B){const z=typeof t=="function"?t("big-batch-unload-warn"):"Batch OCR running · close anyway?";return B.preventDefault(),B.returnValue=z,z}function c(){i||(i=!0,window.addEventListener("beforeunload",p))}function r(){i&&(i=!1,window.removeEventListener("beforeunload",p))}function v(){if(document.getElementById("big-batch-progress"))return;const B=document.getElementById("file-list");if(!B||!B.parentNode)return;const z=document.createElement("div");z.id="big-batch-progress",z.className="big-batch-progress",z.innerHTML='<div class="bbp-row"><svg class="bbp-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.5"/><path d="M8 4.5v3.5l2.5 1.5"/></svg><span class="bbp-text" id="bbp-text"></span></div><div class="bbp-track"><div class="bbp-fill" id="bbp-fill" style="width:0%"></div></div>',B.parentNode.insertBefore(z,B);const q=document.getElementById("bbp-text");q&&(q.textContent=typeof t=="function"?t("big-batch-progress-init"):"Starting...")}function E(){const B=document.getElementById("big-batch-progress");B&&B.remove()}function x(){if(!u)return;let B=0;for(let I=0;I<u.length;I++){const L=u[I].status;(L==="success"||L==="error"||L==="cancelled")&&B++}const z=l,q=z>0?Math.min(100,Math.floor(100*B/z)):0,F=(Date.now()-k)/1e3;let A;if(B>=3&&F>1){const I=F/B;A=(z-B)*I}else A=(z-B)*6/6;const g=Math.max(1,Math.ceil(A/60)),f=document.getElementById("bbp-fill"),h=document.getElementById("bbp-text");f&&(f.style.width=q+"%"),h&&(B>=z?h.textContent=t("big-batch-progress-done").replace("{total}",z):h.textContent=t("big-batch-progress-running").replace("{done}",B).replace("{total}",z).replace("{min}",g))}function R(B){try{if(localStorage.getItem(o)==="1")return}catch{}const z=Math.max(1,Math.ceil(B*6/6/60)),q=t("big-batch-first-tip").replace("{n}",B).replace("{min}",z);typeof showToast=="function"&&showToast(q,"info",8e3);try{localStorage.setItem(o,"1")}catch{}}function D(B){!B||B.length<100||(u=B,l=B.length,k=Date.now(),v(),c(),R(l),s&&clearInterval(s),s=setInterval(x,250),x())}function w(){s&&(clearInterval(s),s=null),r(),u&&l>=100?(x(),setTimeout(E,1200)):E(),u=null,l=0}window._bigBatchStart=D,window._bigBatchStop=w,typeof window.subscribeI18n=="function"&&window.subscribeI18n("big-batch-progress",function(){u&&x()})})();(function(){let e=null,n=!1,a=!1;function o(f){return typeof escapeHtml=="function"?escapeHtml(f==null?"":String(f)):String(f??"")}function s(f,h){try{typeof showToast=="function"&&showToast(f,h||"info")}catch{}}function u(){const f=typeof _userInfo<"u"?_userInfo:null;return!!(f&&(f.role==="owner"||f.is_super_admin))}function l(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function k(f){if(!f)return!1;const h=String(f.status||"").toLowerCase();return h==="exception"||h==="exception_pending"||h==="rejected"}async function i(f){if(n&&!f)return e;const h=localStorage.getItem("mrpilot_token");if(!h)return null;try{const I=await fetch("/api/erp/xero/status",{headers:{Authorization:"Bearer "+h}});if(!I.ok)throw new Error("http_"+I.status);e=await I.json(),n=!0}catch{e={configured:!1,connected:!1,organisations:[]},n=!1}return e}function p(){const f=document.getElementById("erp-connect-cards");if(!f)return;const h=e;let I,L=!1;h?h.configured?h.connected?(L=!0,I='<span class="mrerp-card-pill mrerp-pill-ok">'+o(t("xero-card-connected"))+"</span>"):I='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-connected"))+"</span>":I='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-configured"))+"</span>":I='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-connected"))+"</span>";let H="";if(!h||!h.configured)H='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+o(t("xero-connect-btn"))+"</button>";else if(!h.connected)u()&&(H='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+o(t("xero-connect-btn"))+"</button>");else{const y=!!h.auto_push,m=y?t("card-btn-disable"):t("card-btn-enable");H='<button type="button" class="'+(y?"mrerp-card-toggle mrerp-card-toggle-disable":"mrerp-card-toggle mrerp-card-toggle-enable")+'" id="btn-xero-toggle-enabled" data-xero-enabled="'+(y?"1":"0")+'" title="'+o(y?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip"))+'">'+o(m)+'</button><button type="button" class="int-btn-configure" id="btn-xero-edit-toggle">'+o(t("card-btn-edit"))+"</button>"}const _=h&&h.connected?"xero-card-desc-connected":"xero-card-desc-default",M=h&&h.connected?t("xero-card-connected")||"Connected · default org will receive pushes":"Cloud accounting · push invoices to your default Xero org",K=(function(){const y=t(_);return y===_?M:y})();let G='<div class="integration-row erp-connect-xero'+(L?" connected":"")+'"><div class="int-icon ic-xero"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="9" cy="10" r="1.3" fill="currentColor"/><circle cx="15" cy="14" r="1.3" fill="currentColor"/><path d="M9 14l6-4"/></svg></div><div class="int-info"><div class="int-name"><span>'+o(t("xero-card-title")||"Xero")+"</span>"+I+'</div><div class="int-desc">'+o(K)+'</div></div><div class="int-actions">'+H+"</div></div>";if(h&&h.configured&&h.connected&&u()){const y=h.organisations||[];let m="";if(y.length>0){m+='<div class="erp-cc-meta">'+o((t("xero-org-count")||"").replace("{n}",String(y.length)))+"</div>",m+='<div class="erp-cc-org-label">'+o(t("xero-default-org"))+":</div>",m+='<div class="erp-cc-orgs">',y.forEach(function(Y){m+='<label class="erp-cc-org-row"><input type="radio" name="xero-default-org" value="'+o(Y.id)+'"'+(Y.is_default?" checked":"")+'><span class="erp-cc-org-name">'+o(Y.organisation_name||Y.organisation_id)+"</span></label>"}),m+="</div>";const $=!!h.auto_push,P=$?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip");m+='<div class="erp-cc-auto-push" title="'+o(P)+'"><label class="erp-cc-toggle"><input type="checkbox" id="xero-auto-push-toggle"'+($?" checked":"")+'><span class="erp-cc-toggle-slider"></span><span class="erp-cc-toggle-label">'+o(t("erp-auto-push-label"))+"</span></label></div>",m+='<div class="erp-cc-actions"><button class="btn btn-ghost btn-tiny" type="button" id="btn-xero-disconnect">'+o(t("xero-disconnect-btn"))+"</button></div>"}G+='<div class="erp-xero-details" id="erp-xero-details" style="display:none; margin:8px 0 16px; padding:12px 14px; border:1px solid var(--line); border-radius:8px; background:var(--bg);">'+m+"</div>"}const W=f.querySelector(".erp-connect-xero"),te=f.querySelector("#erp-xero-details");te&&te.remove(),W?W.outerHTML=G:f.insertAdjacentHTML("afterbegin",G);const re=document.getElementById("btn-xero-edit-toggle");re&&re.addEventListener("click",function(y){y.preventDefault();const m=document.getElementById("erp-xero-details");m&&(m.style.display=m.style.display==="none"?"":"none")});const S=document.getElementById("btn-xero-toggle-enabled");S&&S.addEventListener("click",async function(y){if(y.preventDefault(),S.disabled)return;const $=!(S.getAttribute("data-xero-enabled")==="1");if(!$)try{if(!await window.pearnlyConfirm(t("card-toggle-disable-confirm")))return}catch{}S.disabled=!0,await E($,null)})}async function c(){const f=localStorage.getItem("mrpilot_token");if(f)try{const h=await fetch("/api/erp/xero/auth/start",{method:"GET",headers:{Authorization:"Bearer "+f}});if(!h.ok){let L="unknown";try{L=(await h.json()).detail||"unknown"}catch{}const H=String(L).replace(/^xero\./,"").toLowerCase();s(t("xero-push-fail").replace("{err}",t("xero-err-"+H)||L),"error");return}const I=await h.json();I.redirect_url&&(window.location.href=I.redirect_url)}catch(h){s(t("xero-push-fail").replace("{err}",h.message||"network"),"error")}}async function r(){if(!await window.pearnlyConfirm(t("xero-disconnect-confirm")))return;const h=localStorage.getItem("mrpilot_token");try{const I=await fetch("/api/erp/xero/disconnect",{method:"POST",headers:{Authorization:"Bearer "+h}});if(!I.ok)throw new Error("http_"+I.status);await i(!0),p()}catch(I){s(t("xero-push-fail").replace("{err}",I.message),"error")}}async function v(f){const h=localStorage.getItem("mrpilot_token");try{const I=await fetch("/api/erp/xero/select_org",{method:"POST",headers:{Authorization:"Bearer "+h,"Content-Type":"application/json"},body:JSON.stringify({token_id:f})});if(!I.ok)throw new Error("http_"+I.status);await i(!0),p()}catch(I){s(t("xero-push-fail").replace("{err}",I.message),"error")}}async function E(f,h){const I=localStorage.getItem("mrpilot_token");h&&(h.disabled=!0);try{const L=await fetch("/api/erp/xero/auto-push",{method:"POST",headers:{Authorization:"Bearer "+I,"Content-Type":"application/json"},body:JSON.stringify({on:!!f})});if(!L.ok){let H="unknown";try{H=(await L.json()).detail||"unknown"}catch{}throw new Error(H)}s(f?t("erp-auto-push-toggled-on"):t("erp-auto-push-toggled-off"),"success"),n=!1,await i(!0),p()}catch(L){h&&(h.checked=!f),s(t("erp-auto-push-toggle-fail").replace("{err}",L.message||"network"),"error")}finally{h&&(h.disabled=!1)}}async function x(){const f=document.getElementById("drawer-history-save");if(!f||f.querySelector("#btn-xero-push")||f.querySelector("#pn-push-wrap")||(await i(!1),f.querySelector("#pn-push-wrap"))||f.querySelector("#btn-xero-push"))return;const h=l();if(!(h&&(h._historyId||h.history_id)))return;let L=!1,H="xero-push-tip";!e||!e.configured?(L=!0,H="xero-err-not_configured"):e.connected?k(h)&&(L=!0,H="xero-push-disabled-exc"):(L=!0,H="xero-push-disabled-no-conn");const _=document.createElement("button");_.type="button",_.id="btn-xero-push",_.className="btn btn-ghost"+(L?" disabled":""),_.disabled=L,_.title=t(H)||"",_.innerHTML='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5 8l2 2 4-4"/></svg><span style="margin-left:4px;">'+o(t("xero-push-btn"))+"</span>",_.addEventListener("click",R);const M=document.getElementById("btn-push-erp");M&&M.parentNode?M.parentNode.insertBefore(_,M.nextSibling):f.insertBefore(_,f.firstChild)}async function R(){const f=l(),h=f&&(f._historyId||f.history_id);if(!h)return;const I=document.getElementById("btn-xero-push");I&&(I.disabled=!0,I.classList.add("loading"));const L=localStorage.getItem("mrpilot_token");try{const H=await fetch("/api/erp/xero/push/"+encodeURIComponent(h),{method:"POST",headers:{Authorization:"Bearer "+L}});if(!H.ok){let _="unknown";try{_=(await H.json()).detail||"unknown"}catch{}const M=String(_).replace(/^xero\./,"").toLowerCase(),K=t("xero-"+M),G=K&&K!=="xero-"+M?K:_;s(t("xero-push-fail").replace("{err}",G),"error");return}s(t("xero-push-ok"),"success")}catch(H){s(t("xero-push-fail").replace("{err}",H.message||"network"),"error")}finally{I&&(I.disabled=!1,I.classList.remove("loading"))}}async function D(){await i(!0),p(),w()}async function w(){const f=document.getElementById("erp-global-push-mode");if(!f)return;const h=localStorage.getItem("mrpilot_token");if(h)try{const I=await fetch("/api/settings/erp-push-mode",{headers:{Authorization:"Bearer "+h}});if(I.ok){const L=await I.json();L.mode&&(f.value=L.mode,f.dataset.prev=L.mode)}}catch{}}async function B(f){const h=f.value,I=localStorage.getItem("mrpilot_token");try{(await fetch("/api/settings/erp-push-mode",{method:"PUT",headers:{Authorization:"Bearer "+I,"Content-Type":"application/json"},body:JSON.stringify({mode:h})})).ok?(f.dataset.prev=h,s(t("pref-erp-mode-saved"),"success")):(f.value=f.dataset.prev||"smart",s(t("pref-save-failed"),"error"))}catch{f.value=f.dataset.prev||"smart",s(t("pref-save-failed"),"error")}}function z(){try{const f=String(window.location.hash||"");if(f.indexOf("xero=ok")>=0){const h=f.match(/n=(\d+)/),I=h?h[1]:"1";s((t("xero-toast-redirected-ok")||"").replace("{n}",I),"success"),history.replaceState(null,"",window.location.pathname+"#automation"),i(!0).then(p)}else f.indexOf("xero=err")>=0&&(s(t("xero-toast-redirected-err"),"error"),history.replaceState(null,"",window.location.pathname+"#automation"))}catch{}}function q(){if(a)return;a=!0,document.addEventListener("click",function(h){if(h.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(D,50);return}if(h.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(D,80);return}if(h.target.closest("#btn-xero-connect")){h.preventDefault(),c();return}if(h.target.closest("#btn-xero-disconnect")){h.preventDefault(),r();return}}),document.addEventListener("change",function(h){h.target&&h.target.matches('input[name="xero-default-org"]')&&v(h.target.value),h.target&&h.target.id==="xero-auto-push-toggle"&&E(h.target.checked,h.target),h.target&&h.target.id==="erp-global-push-mode"&&B(h.target)});const f=function(){return document.getElementById("drawer-body")};try{const h=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("btn-xero-push")&&x()}),I=f();if(I)h.observe(I,{childList:!0,subtree:!0});else{const L=new MutationObserver(function(){const H=f();H&&(h.observe(H,{childList:!0,subtree:!0}),L.disconnect())});L.observe(document.body,{childList:!0,subtree:!0})}}catch{}setTimeout(z,500)}function F(){e&&p();const f=document.getElementById("btn-xero-push");if(f){const h=f.querySelector("span");h&&(h.textContent=t("xero-push-btn"))}}q(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("xero-adapter",F);async function A(f){const h=Date.now();for(;Date.now()-h<f;){if(typeof _userInfo<"u"&&_userInfo&&_userInfo.id)return _userInfo;await new Promise(I=>setTimeout(I,80))}return null}async function g(){await A(5e3);const f=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),h=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');f&&h&&await D()}setTimeout(g,200)})();(function(){const e={};function n(){if(document.getElementById("report-modal"))return;const p=`
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
        </div>`,c=document.createElement("div");c.innerHTML=p,document.body.appendChild(c.firstElementChild),document.getElementById("report-modal-close-x").addEventListener("click",a),document.getElementById("report-modal-cancel").addEventListener("click",a),document.getElementById("report-modal").addEventListener("click",r=>{r.target.id==="report-modal"&&a()})}function a(){const p=document.getElementById("report-modal");p&&(p.style.display="none"),o=null}let o=null;async function s(p,c){const r=p+":"+(c||"");if(e[r])return e[r];let v;try{const E=localStorage.getItem("mrpilot_token"),x=await fetch(`/api/reports/templates?lang=${encodeURIComponent(p)}`,{headers:{Authorization:"Bearer "+E}});if(!x.ok)throw new Error("templates fetch failed");v=(await x.json()).templates||[]}catch(E){console.error("fetchTemplates fail",E),v=[{code:"input_vat",name:t("tpl-input-vat"),desc:t("tpl-input-vat-desc"),recommended:!0},{code:"standard",name:t("tpl-standard"),desc:t("tpl-standard-desc"),recommended:!1},{code:"print",name:t("tpl-print"),desc:t("tpl-print-desc"),recommended:!1}]}if(v=v.filter(E=>E.code!=="erp"),c==="history-batch"){const E=v.findIndex(R=>R.code==="standard"),x=E>=0?E+1:v.length;v.splice(x,0,{code:"sales_detail_th",name:t("export-tpl-sales-detail"),desc:t("export-tpl-sales-detail-desc"),recommended:!1,is_new:!0})}return e[r]=v,v}function u(p){const c=document.getElementById("report-tpl-list"),r=p.map((E,x)=>`
            <label class="report-tpl-item${E.recommended?" is-recommended":""}">
                <input type="radio" name="report-tpl" value="${E.code}" ${E.recommended||x===0?"checked":""}>
                <div class="report-tpl-content">
                    <div class="report-tpl-name">
                        ${l(E.name)}
                        ${E.recommended?`<span class="report-tpl-badge">${l(t("report-recommended"))}</span>`:""}
                    </div>
                    <div class="report-tpl-desc">${l(E.desc||"")}</div>
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
        `;c.innerHTML=r+v}function l(p){return p==null?"":String(p).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c])}function k(p){const c=new Date,r=c.getFullYear(),v=c.getMonth()+1;if(p==="all")return"all";if(p==="this-month")return`${r}-${String(v).padStart(2,"0")}`;if(p==="last-month"){const E=new Date(r,v-2,1);return`${E.getFullYear()}-${String(E.getMonth()+1).padStart(2,"0")}`}return p==="this-year"?`${r}`:p==="this-quarter"?`${r}-Q${Math.floor((v-1)/3)+1}`:"all"}window.openReportModal=async function(p){p=p||{},n(),typeof applyLang=="function"?applyLang(currentLang):document.querySelectorAll("#report-modal [data-i18n]").forEach(R=>{const D=R.getAttribute("data-i18n");I18N[currentLang]&&I18N[currentLang][D]&&(R.textContent=I18N[currentLang][D])});const c=document.getElementById("report-period-section");c&&(c.style.display=p.mode==="client"?"":"none");const r=document.getElementById("report-tpl-list");r.innerHTML=`<div class="report-tpl-loading">${l(t("report-modal-loading"))}</div>`,document.getElementById("report-modal").style.display="";const v=await s(currentLang,p&&p.mode);u(v),o=p;const E=document.getElementById("report-modal-download"),x=E.cloneNode(!0);E.parentNode.replaceChild(x,E),x.addEventListener("click",()=>i(o))};async function i(p){if(!p)return;const c=document.querySelector('input[name="report-tpl"]:checked');if(!c){showToast(t("report-toast-no-selection"),"info");return}const r=c.value,v=document.querySelector('input[name="report-period"]:checked'),E=v?v.value:"all",x=k(E),R=document.getElementById("report-modal-download"),D=R.innerHTML;R.disabled=!0,R.innerHTML=`<span>${l(t("report-modal-loading"))}</span>`;try{const w=localStorage.getItem("mrpilot_token");let B,z;if(p.mode==="records")B=await fetch("/api/reports/export",{method:"POST",headers:{Authorization:"Bearer "+w,"Content-Type":"application/json"},body:JSON.stringify({template:r,lang:currentLang,records:p.records||[],meta:p.meta||{}})}),z=`mrpilot-${r}-${Date.now()}.xlsx`;else if(p.mode==="client"){const I=`/api/reports/clients/${p.clientId}/export?template=${encodeURIComponent(r)}&lang=${encodeURIComponent(currentLang)}&month=${encodeURIComponent(x)}`;B=await fetch(I,{headers:{Authorization:"Bearer "+w}}),z=`${(p.clientName||"client").replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40)}-${r}.xlsx`}else if(p.mode==="history-batch")r==="sales_detail_th"?(B=await fetch("/api/ocr/export-by-history-ids",{method:"POST",headers:{Authorization:"Bearer "+w,"Content-Type":"application/json"},body:JSON.stringify({template:"sales_detail_th",lang:currentLang,history_ids:p.historyIds||[],client_id:p.clientId||null})}),z=`Pearnly_SalesDetail_${Date.now()}.xlsx`):(B=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+w,"Content-Type":"application/json"},body:JSON.stringify({template:r,lang:currentLang,history_ids:p.historyIds||[],client_id:p.clientId||null})}),z=`mrpilot-batch-${r}-${Date.now()}.xlsx`);else throw new Error("unknown mode: "+p.mode);if(!B.ok){let I="HTTP "+B.status;try{const L=await B.json();L&&L.detail&&(I=L.detail)}catch(L){console.warn("[batch-export] resp.json err.detail parse failed:",L)}B.status===404?showToast(t("report-toast-empty"),"info"):showToast(t("report-toast-fail")+" · "+I,"error");return}const q=await B.blob();let F=z;const g=(B.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(g)try{F=decodeURIComponent(g[1])}catch{}const f=URL.createObjectURL(q),h=document.createElement("a");h.href=f,h.download=F,document.body.appendChild(h),h.click(),document.body.removeChild(h),URL.revokeObjectURL(f),showToast(t("report-toast-success"),"success"),a()}catch(w){console.error("doDownload fail",w),showToast(t("report-toast-fail")+" · "+(w.message||""),"error")}finally{R.disabled=!1,R.innerHTML=D}}document.addEventListener("DOMContentLoaded",()=>{const p=document.getElementById("btn-export");if(p){const r=p.cloneNode(!0);p.parentNode.replaceChild(r,p),r.addEventListener("click",()=>{if(typeof _results>"u"||!_results||_results.length===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"records",records:_results.map(v=>({filename:v.filename,merged_fields:v.merged_fields||{}}))})})}const c=document.getElementById("history-batch-export");c&&c.addEventListener("click",()=>{if(typeof _historySelected>"u"||_historySelected.size===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"history-batch",historyIds:Array.from(_historySelected)})})}),window.openClientExportModal=function(p,c){openReportModal({mode:"client",clientId:p,clientName:c||""})}})();(function(){const n=typeof window<"u"&&"showDirectoryPicker"in window,a=/\.(pdf|jpe?g|png|webp)$/i,o="mrpilot_folder_watcher",s=1;let u=null,l=null,k=null,i=60,p=!1,c=!1,r=0,v=0,E=0,x=[],R=null,D=!1;function w(){return u||(u=new Promise((b,C)=>{const T=indexedDB.open(o,s);T.onupgradeneeded=U=>{const N=U.target.result;N.objectStoreNames.contains("handles")||N.createObjectStore("handles"),N.objectStoreNames.contains("seen")||N.createObjectStore("seen"),N.objectStoreNames.contains("config")||N.createObjectStore("config")},T.onsuccess=U=>b(U.target.result),T.onerror=U=>C(U.target.error)}),u)}function B(b,C){return w().then(T=>new Promise((U,N)=>{const j=T.transaction(b,"readonly").objectStore(b).get(C);j.onsuccess=()=>U(j.result),j.onerror=()=>N(j.error)}))}function z(b,C,T){return w().then(U=>new Promise((N,d)=>{const j=U.transaction(b,"readwrite");j.objectStore(b).put(T,C),j.oncomplete=()=>N(),j.onerror=()=>d(j.error)}))}function q(b,C){return w().then(T=>new Promise((U,N)=>{const d=T.transaction(b,"readwrite");d.objectStore(b).delete(C),d.oncomplete=()=>U(),d.onerror=()=>N(d.error)}))}function F(b){return w().then(C=>new Promise((T,U)=>{const N=C.transaction(b,"readwrite");N.objectStore(b).clear(),N.oncomplete=()=>T(),N.onerror=()=>U(N.error)}))}async function A(b){if(!b)return!1;try{const C={mode:"read"};let T=await b.queryPermission(C);return T==="granted"?!0:(T=await b.requestPermission(C),T==="granted")}catch(C){return console.warn("[folder] permission check failed:",C),!1}}function g(b,C){const T=document.getElementById("folder-status-summary");T&&(T.setAttribute("data-i18n",b),T.textContent=t(b),T.className="auto-status-pill"+(C?" "+C:""))}function f(b){["folder-unsupported","folder-empty","folder-active"].forEach(C=>{const T=document.getElementById(C);T&&(T.style.display=C===b?"":"none")})}function h(b){if(!b)return"-";const C=b instanceof Date?b:new Date(b),T=String(C.getHours()).padStart(2,"0"),U=String(C.getMinutes()).padStart(2,"0"),N=String(C.getSeconds()).padStart(2,"0");return`${T}:${U}:${N}`}function I(){f("folder-active");const b=document.getElementById("folder-config-path");b&&l&&(b.textContent=l.name||"-");const C=document.getElementById("folder-interval-select");C&&(C.value=String(i)),document.getElementById("folder-stat-last").textContent=R?h(R):"-",document.getElementById("folder-stat-processed").textContent=String(r),document.getElementById("folder-stat-failed").textContent=String(v),document.getElementById("folder-stat-queue").textContent=String(E);const T=document.getElementById("btn-folder-pause"),U=document.getElementById("btn-folder-resume");T&&(T.style.display=p?"none":""),U&&(U.style.display=p?"":"none"),p?g("folder-status-paused","paused"):g("folder-status-running","running");const N=document.getElementById("folder-status-text");N&&(N.setAttribute("data-i18n",p?"folder-status-paused":"folder-status-running"),N.textContent=t(p?"folder-status-paused":"folder-status-running"));const d=document.getElementById("folder-status-pulse");d&&(d.className="folder-status-pulse"+(p?" paused":"")),L()}function L(){const b=document.getElementById("folder-recent-list");if(b){if(x.length===0){b.innerHTML=`<div class="folder-recent-empty">${escapeHtml(t("folder-recent-empty"))}</div>`;return}b.innerHTML=x.slice(0,20).map(C=>{let T;C.status==="ok"?T=`<span class="folder-recent-icon ok">${svgIcon("check",12)}</span>`:C.status==="dup"?T=`<span class="folder-recent-icon dup" title="${escapeHtml(t("folder-recent-dup"))}">${svgIcon("copy",12)}</span>`:C.status==="skip"?T=`<span class="folder-recent-icon skip" title="${escapeHtml(t("folder-recent-skip"))}">${svgIcon("minus",12)}</span>`:T=`<span class="folder-recent-icon fail">${svgIcon("alert",12)}</span>`;const U=C.status==="fail"&&C.error?C.error:C.status==="dup"&&C.reason||C.status==="skip"&&C.reason?C.reason:"",N=U?`<div class="folder-recent-err">${escapeHtml(U)}</div>`:"";return`
                <div class="folder-recent-item">
                    ${T}
                    <div class="folder-recent-body">
                        <div class="folder-recent-name">${escapeHtml(C.name)}</div>
                        ${N}
                    </div>
                    <div class="folder-recent-time">${h(C.time)}</div>
                </div>
            `}).join("")}}function H(b){x.unshift(b),x.length>50&&(x.length=50),z("config","recent_list",x).catch(()=>{})}async function _(b){const C=new FormData;C.append("file",b,b.name),C.append("source","folder");const T=await fetch("/api/ocr/recognize?source=folder",{method:"POST",headers:{Authorization:"Bearer "+token,"X-Source":"folder"},body:C});if(!T.ok){let U="http_"+T.status;try{const N=await T.json();U=N&&N.detail?typeof N.detail=="string"?N.detail:N.detail.code||JSON.stringify(N.detail):U}catch{}throw new Error(U)}return await T.json()}async function M(b){try{const T=(await b.getFile()).size;return await new Promise(N=>setTimeout(N,3e3)),(await b.getFile()).size===T&&T>0}catch{return!1}}async function K(b,C,T,U){if(U>10)return;let N;try{N=await b.queryPermission({mode:"read"})}catch{N="denied"}if(N==="granted")for await(const d of b.values()){const j=C?`${C}/${d.name}`:d.name;if(d.kind==="file"){if(!a.test(d.name))continue;let O;try{O=await d.getFile()}catch{continue}const J=`${j}::${O.size}::${O.lastModified}`;if(await B("seen",J))continue;T.push({entry:d,file:O,seenKey:J,relPath:j})}else if(d.kind==="directory")try{await K(d,j,T,U+1)}catch{}}}async function G(){if(!(c||p||!l)){c=!0;try{if(await l.queryPermission({mode:"read"})!=="granted"){console.warn("[folder] permission lost · stop"),Y(),showToast("warn",t("folder-permission-lost"));return}R=new Date;const C=[];await K(l,"",C,0),E=C.length,I();for(const T of C){if(p)break;if(!await M(T.entry)){E=Math.max(0,E-1),I();continue}try{let N;try{N=await T.entry.getFile()}catch{N=T.file}const d=await _(N);await z("seen",T.seenKey,{name:N.name,relPath:T.relPath,size:N.size,lastModified:N.lastModified,processed_at:Date.now()});const j=d.history_ids||(d.history_id?[d.history_id]:[]),O=d.duplicate_warnings||[],J=T.relPath||N.name;j.length>0?(r+=j.length,H({name:J,status:"ok",time:new Date,history_id:j[0],count:j.length}),await z("config","processed_count",r)):O.length>0?H({name:J,status:"dup",time:new Date,reason:t("folder-recent-dup-reason")}):H({name:J,status:"skip",time:new Date,reason:t("folder-recent-skip-reason")})}catch(N){v++,H({name:T.relPath||T.file.name,status:"fail",time:new Date,error:String(N.message||N)}),await z("config","failed_count",v)}E=Math.max(0,E-1),I()}}catch(b){console.warn("[folder] scan error:",b)}finally{c=!1,I()}}}function W(){k&&clearInterval(k),k=setInterval(G,i*1e3)}function te(){k&&(clearInterval(k),k=null)}function re(b){if(!l||p)return;const C=typeof t=="function"?t("folder-unload-warn"):"Folder watcher running · close anyway?";return b.preventDefault(),b.returnValue=C,C}function S(){window._pearnlyFolderUnloadAttached||(window._pearnlyFolderUnloadAttached=!0,window.addEventListener("beforeunload",re))}function y(){window._pearnlyFolderUnloadAttached&&(window._pearnlyFolderUnloadAttached=!1,window.removeEventListener("beforeunload",re))}function m(){p=!1,W(),S(),I(),G()}function $(){p=!0,te(),y(),I()}function P(){p=!1,W(),S(),I(),G()}function Y(){p=!0,te(),y()}async function Z(){try{const b=await window.showDirectoryPicker({mode:"read",startIn:"documents"});if(!await A(b)){showToast("warn",t("folder-permission-denied"));return}l=b,await z("handles","main",b),r=0,v=0,E=0,x=[],await z("config","processed_count",0),await z("config","failed_count",0),await F("seen"),m()}catch(b){b&&b.name!=="AbortError"&&console.warn("[folder] pick failed:",b)}}async function le(){await showConfirm(t("folder-confirm-remove"),{danger:!0})&&(Y(),l=null,r=0,v=0,E=0,x=[],await q("handles","main"),await q("config","processed_count"),await q("config","failed_count"),await F("seen"),f("folder-empty"),g("folder-status-empty",""))}async function ie(){x=[];try{await q("config","recent_list")}catch{}L()}async function V(){if(D)return;if(D=!0,!n){f("folder-unsupported"),g("folder-status-unsupported",""),ne();return}Q();let b=null;try{b=await B("handles","main")}catch{}if(!b){f("folder-empty"),g("folder-status-empty","");return}if(!await A(b)){f("folder-empty"),g("folder-status-empty",""),await q("handles","main"),showToast("warn",t("folder-permission-lost-restart"));return}l=b;try{r=await B("config","processed_count")||0}catch{}try{v=await B("config","failed_count")||0}catch{}try{const T=await B("config","recent_list");Array.isArray(T)&&(x=T.map(U=>({...U,time:U.time?new Date(U.time):new Date})))}catch{}m()}function Q(){const b=document.getElementById("btn-folder-pick"),C=document.getElementById("btn-folder-pause"),T=document.getElementById("btn-folder-resume"),U=document.getElementById("btn-folder-scan-now"),N=document.getElementById("btn-folder-remove"),d=document.getElementById("btn-folder-clear-recent"),j=document.getElementById("folder-interval-select");b&&b.addEventListener("click",Z),C&&C.addEventListener("click",$),T&&T.addEventListener("click",P),U&&U.addEventListener("click",()=>{G()}),N&&N.addEventListener("click",le),d&&d.addEventListener("click",ie),j&&j.addEventListener("change",O=>{i=parseInt(O.target.value,10)||60,p||W()}),ee()}function ee(){document.querySelectorAll('[data-auto-panel="folder"] [data-tab-jump]').forEach(b=>{b.dataset.tabJumpBound||(b.dataset.tabJumpBound="1",b.addEventListener("click",C=>{const T=C.currentTarget.dataset.tabJump;if(T==="email")typeof switchAutomationTab=="function"&&switchAutomationTab("email");else if(T==="upload"){const U=document.querySelector('[data-page="recognize"]')||document.querySelector('[data-page="upload"]');U&&U.click()}}))})}function ne(){ee()}window._loadFolderWatcherPanel=V;function oe(){try{if(navigator.userAgentData&&Array.isArray(navigator.userAgentData.brands))return navigator.userAgentData.brands.some(C=>/chromium|google chrome|microsoft edge/i.test(C.brand||""))}catch{}const b=navigator.userAgent||"";return!!(/Edg\//.test(b)||/Chrome\//.test(b)&&!/OPR\/|YaBrowser|Opera/.test(b))}function ue(){try{if(oe()||localStorage.getItem("pearnly_chrome_banner_dismissed")==="1")return;const b=document.getElementById("chrome-only-banner");if(!b)return;const C=b.querySelector('[data-i18n="chrome-banner-msg"]'),T=b.querySelector('[data-i18n="chrome-banner-dismiss"]');C&&typeof t=="function"&&(C.textContent=t("chrome-banner-msg")),T&&typeof t=="function"&&(T.textContent=t("chrome-banner-dismiss")),b.style.display="";const U=document.getElementById("chrome-only-banner-close");U&&!U.dataset.bound&&(U.dataset.bound="1",U.addEventListener("click",()=>{b.style.display="none";try{localStorage.setItem("pearnly_chrome_banner_dismissed","1")}catch{}}))}catch{}}typeof document<"u"&&(document.readyState==="loading"?document.addEventListener("DOMContentLoaded",ue):setTimeout(ue,0)),window._refreshChromeBanner=ue})();(function(){let e=null,n=null,a="new",o=!1,s=!1;async function u(){const _=document.getElementById("email-empty"),M=document.getElementById("email-account-card");if(document.getElementById("email-logs-section"),!(!_||!M))try{const K=await fetch("/api/email-ingest/account",{headers:{Authorization:"Bearer "+token}});if(K.status===401){localStorage.removeItem("mrpilot_token");const W=await K.json().catch(()=>({}));if((typeof W.detail=="string"?W.detail:W.detail&&W.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}if(!K.ok){k("none");return}const G=await K.json();e=G.account||null,n=G.presets||{},o=!0,l(),e&&h()}catch(K){console.error("[email-ingest] load failed",K),k("none")}}function l(){const _=document.getElementById("email-empty"),M=document.getElementById("email-account-card"),K=document.getElementById("email-logs-section");if(!e){_.style.display="",M.style.display="none",K&&(K.style.display="none"),k("none");return}_.style.display="none",M.style.display="",K&&(K.style.display="");const G=document.getElementById("email-account-addr"),W=document.getElementById("email-account-host"),te=document.getElementById("email-account-last"),re=document.getElementById("email-last-error"),S=document.getElementById("email-enabled-toggle");if(G&&(G.textContent=e.email_address||"-"),W&&(W.textContent=`${e.imap_host||"-"}:${e.imap_port||993}`),te){const y=e.last_fetched_at;if(!y)te.textContent=t("email-last-never");else{const m=i(y),$=!e.last_error;te.textContent=$?t("email-last-ok",{time:m}):t("email-last-fail",{time:m})}}re&&(e.last_error?(re.style.display="",re.textContent=p(e.last_error)):re.style.display="none"),S&&(S.checked=!!e.enabled),e.enabled?e.last_error?k("error"):k("on"):k("off")}function k(_){const M=document.getElementById("email-status-summary");if(!M)return;M.classList.remove("none","ready","active","coming");let K="auto-status-loading";_==="none"?(K="email-status-none",M.classList.add("none")):_==="on"?(K="email-status-on",M.classList.add("active")):_==="off"?(K="email-status-off",M.classList.add("coming")):_==="error"&&(K="email-status-error",M.classList.add("none")),M.setAttribute("data-i18n",K),M.textContent=t(K)}function i(_){if(!_)return"";const M=new Date(_);if(isNaN(M.getTime()))return"";const K=G=>String(G).padStart(2,"0");return`${K(M.getMonth()+1)}-${K(M.getDate())} ${K(M.getHours())}:${K(M.getMinutes())}`}function p(_){if(!_)return"";const M=String(_);return/auth|AUTHENTICATIONFAILED|invalid credentials/i.test(M)?t("email-test-auth-fail"):/timeout|timed out/i.test(M)?t("email.timeout"):(/ENOTFOUND|getaddrinfo/i.test(M),M)}function c(_){a=_;const M=document.getElementById("email-modal");if(!M)return;const K=document.getElementById("email-preset");K.innerHTML="";const G=n||{},W=["gmail","outlook","yahoo","icloud","qq","163","custom"],te={gmail:"Gmail",outlook:"Outlook / Office365",yahoo:"Yahoo Mail",icloud:"iCloud",qq:"QQ 邮箱",163:"网易 163"};W.forEach(Q=>{if(!G[Q])return;const ee=document.createElement("option");ee.value=Q,ee.textContent=Q==="custom"?t("email-preset-custom"):te[Q]||Q,K.appendChild(ee)});const re=document.getElementById("email-modal-title"),S=document.getElementById("email-address"),y=document.getElementById("email-password"),m=document.getElementById("email-imap-host"),$=document.getElementById("email-imap-port"),P=document.getElementById("email-imap-ssl"),Y=document.getElementById("email-folder"),Z=document.getElementById("email-mark-read"),le=document.getElementById("email-bind-enabled"),ie=document.getElementById("email-test-result"),V=document.getElementById("email-adv-details");if(ie&&(ie.style.display="none",ie.textContent=""),_==="edit"&&e){re.setAttribute("data-i18n","email-modal-title-edit"),re.textContent=t("email-modal-title-edit"),S.value=e.email_address||"",y.value="",y.setAttribute("data-i18n-placeholder","email-field-password-edit-ph"),y.placeholder=t("email-field-password-edit-ph"),m.value=e.imap_host||"",$.value=e.imap_port||993,P.checked=e.imap_use_ssl!==!1,Y.value=e.folder||"INBOX",Z.checked=e.mark_as_read!==!1,le.checked=e.enabled!==!1;const Q=document.getElementById("email-filter-sender"),ee=document.getElementById("email-filter-subject");Q&&(Q.value=e.filter_sender||""),ee&&(ee.value=e.filter_subject||""),B(e.interval_min||15),K.value=R(e.imap_host)||"custom",V&&(V.open=!0)}else{re.setAttribute("data-i18n","email-modal-title-new"),re.textContent=t("email-modal-title-new"),S.value="",y.value="",y.setAttribute("data-i18n-placeholder","email-field-password-ph"),y.placeholder=t("email-field-password-ph"),K.value="gmail",v("gmail"),Y.value="INBOX",Z.checked=!0,le.checked=!0;const Q=document.getElementById("email-filter-sender"),ee=document.getElementById("email-filter-subject");Q&&(Q.value=""),ee&&(ee.value=""),B(15),V&&(V.open=!1)}w(),M.style.display="flex",setTimeout(()=>S.focus(),60)}function r(){const _=document.getElementById("email-modal");_&&(_.style.display="none")}function v(_){const M=(n||{})[_];if(!M||_==="custom")return;const K=document.getElementById("email-imap-host"),G=document.getElementById("email-imap-port"),W=document.getElementById("email-imap-ssl");K&&(K.value=M.host||""),G&&(G.value=M.port||993),W&&(W.checked=M.ssl!==!1)}const E={"gmail.com":"gmail","googlemail.com":"gmail","outlook.com":"outlook","hotmail.com":"outlook","live.com":"outlook","office365.com":"outlook","msn.com":"outlook","yahoo.com":"yahoo","yahoo.co.jp":"yahoo","icloud.com":"icloud","me.com":"icloud","mac.com":"icloud","qq.com":"qq","foxmail.com":"qq","163.com":"163","126.com":"163","yeah.net":"163"};function x(_){if(!_||!_.includes("@"))return;const M=_.split("@")[1].toLowerCase().trim(),K=E[M];if(!K)return;const G=document.getElementById("email-preset");if(!G)return;const W=G.value;W&&W!=="custom"&&W!==""&&W===K||(G.value=K,v(K))}function R(_){if(!_)return null;const M=n||{};for(const K in M)if(K!=="custom"&&M[K]&&M[K].host===_)return K;return null}function D(){const _=document.querySelector("#email-interval-options .email-interval-btn.active"),M=_?parseInt(_.dataset.interval,10):15;return{email_address:(document.getElementById("email-address").value||"").trim(),password:document.getElementById("email-password").value||"",imap_host:(document.getElementById("email-imap-host").value||"").trim(),imap_port:parseInt(document.getElementById("email-imap-port").value||"993",10)||993,imap_use_ssl:document.getElementById("email-imap-ssl").checked,folder:(document.getElementById("email-folder").value||"INBOX").trim()||"INBOX",mark_as_read:document.getElementById("email-mark-read").checked,enabled:document.getElementById("email-bind-enabled").checked,interval_min:[5,15,60].includes(M)?M:15,filter_sender:(document.getElementById("email-filter-sender").value||"").trim()||null,filter_subject:(document.getElementById("email-filter-subject").value||"").trim()||null}}function w(){const _=document.getElementById("email-interval-options");!_||_._bound||(_._bound=!0,_.addEventListener("click",M=>{const K=M.target.closest(".email-interval-btn");K&&(_.querySelectorAll(".email-interval-btn").forEach(G=>G.classList.remove("active")),K.classList.add("active"))}))}function B(_){const M=[5,15,60].includes(_)?_:15,K=document.getElementById("email-interval-options");K&&K.querySelectorAll(".email-interval-btn").forEach(G=>{G.classList.toggle("active",parseInt(G.dataset.interval,10)===M)})}function z(_,M){const K=document.getElementById("email-test-result");K&&(K.style.display="",K.textContent=M,K.className="form-test-result "+(_==="ok"?"ok":_==="running"?"running":"fail"))}async function q(){const _=D();if(!_.email_address){z("fail",t("email-addr-required"));return}if(!_.password){z("fail",t("email-password-required"));return}if(!_.imap_host){z("fail",t("email-host-required"));return}const M=document.getElementById("btn-email-modal-test");M&&(M.disabled=!0),z("running",t("email-test-running"));try{const K=await fetch("/api/email-ingest/test",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:_.email_address,password:_.password,imap_host:_.imap_host,imap_port:_.imap_port,imap_use_ssl:_.imap_use_ssl,folder:_.folder})}),G=await K.json().catch(()=>({}));if(K.ok&&G.success)z("ok",t("email-test-ok",{folder:_.folder,n:G.folder_count??"?"}));else{const W=G.error_msg||"";W==="auth_failed"||/auth/i.test(W)?z("fail",t("email-test-auth-fail")):z("fail",t("email-test-fail",{msg:W||K.status}))}}catch(K){z("fail",t("email-test-fail",{msg:String(K).slice(0,120)}))}finally{M&&(M.disabled=!1)}}async function F(){const _=D();if(!_.email_address){z("fail",t("email-addr-required"));return}if(a==="new"&&!_.password){z("fail",t("email-password-required"));return}if(!_.imap_host){z("fail",t("email-host-required"));return}const M=document.getElementById("btn-email-modal-save");M&&(M.disabled=!0);const K={..._};a==="edit"&&!K.password&&delete K.password;try{const G=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(K)}),W=await G.json().catch(()=>({}));if(G.ok&&W.ok)e=W.account,showToast(t("email-save-ok"),"success"),r(),l(),h();else{const re="email."+(W.detail||"").split(".").slice(-1)[0];z("fail",t(re)!==re?t(re):t("email-save-fail"))}}catch{z("fail",t("email-save-fail"))}finally{M&&(M.disabled=!1)}}async function A(){if(!(!e||!await showConfirm(t("email-unbind-confirm",{email:e.email_address}),{danger:!0,okText:t("email-btn-unbind")})))try{if((await fetch("/api/email-ingest/account",{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){e=null,showToast(t("email-unbind-ok"),"success"),l();const K=document.getElementById("email-logs-list");K&&(K.innerHTML="")}else showToast(t("email-unbind-fail"),"error")}catch{showToast(t("email-unbind-fail"),"error")}}async function g(){if(!e||s)return;if(!e.enabled){showToast(t("email.disabled"),"error");return}s=!0;const _=document.getElementById("btn-email-trigger"),M=_?_.innerHTML:"";_&&(_.disabled=!0,_.innerHTML=`<span>${escapeHtml(t("email-trigger-running"))}</span>`);try{const K=await fetch("/api/email-ingest/trigger",{method:"POST",headers:{Authorization:"Bearer "+token}}),G=await K.json().catch(()=>({}));if(K.ok){const W=G.emails_scanned||0,te=G.ocr_succeeded||0,re=G.ocr_failed||0;W===0&&te===0&&re===0?showToast(t("email-trigger-empty"),"success"):showToast(t("email-trigger-result",{scanned:W,ok:te,fail:re}),re>0?"warn":"success")}else{const te="email."+(G.detail||"").split(".").slice(-1)[0];showToast(t(te)!==te?t(te):t("email-trigger-fail"),"error")}await u()}catch{showToast(t("email-trigger-fail"),"error")}finally{s=!1,_&&(_.disabled=!1,_.innerHTML=M)}}async function f(){if(!e)return;const _=document.getElementById("email-enabled-toggle"),M=!!(_&&_.checked),K=e.enabled;try{const G=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:e.email_address,imap_host:e.imap_host,imap_port:e.imap_port,imap_use_ssl:e.imap_use_ssl,folder:e.folder||"INBOX",filter_subject:e.filter_subject||null,filter_sender:e.filter_sender||null,mark_as_read:e.mark_as_read!==!1,enabled:M})}),W=await G.json().catch(()=>({}));G.ok&&W.ok?(e=W.account,l()):(_&&(_.checked=K),showToast(t("email-toggle-fail"),"error"))}catch{_&&(_.checked=K),showToast(t("email-toggle-fail"),"error")}}async function h(){const _=document.getElementById("email-logs-list");if(_){_.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`;try{const M=await fetch("/api/email-ingest/logs?limit=20",{headers:{Authorization:"Bearer "+token}});if(!M.ok){_.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const K=await M.json();if(!Array.isArray(K)||K.length===0){_.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("email-logs-empty"))}</div>`;return}_.innerHTML=K.map(I).join("")}catch{_.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}function I(_){const M=i(_.created_at),K=_.status||"failed",G=K==="success"?"ok":K==="partial"?"partial":"fail",W=K==="success"?"✓":K==="partial"?"◐":"✗",te=_.trigger==="manual"?`<span class="log-tag manual">${escapeHtml(t("email-log-tag-manual"))}</span>`:`<span class="log-tag auto">${escapeHtml(t("email-log-tag-auto"))}</span>`,re=t("email-log-counts",{scanned:_.emails_scanned||0,att:_.attachments_found||0,ok:_.ocr_succeeded||0,fail:_.ocr_failed||0}),S=(_.elapsed_ms||0)+"ms";return`
            <div class="email-log-row ${G}">
                <span class="log-time">${escapeHtml(M)}</span>
                <span class="log-status">${W}</span>
                ${te}
                <span class="log-counts">${escapeHtml(re)}</span>
                <span class="log-elapsed">${escapeHtml(S)}</span>
            </div>
        `}function L(){const _=document.getElementById("btn-email-bind");_&&_.addEventListener("click",()=>c("new"));const M=document.getElementById("btn-email-edit");M&&M.addEventListener("click",()=>c("edit"));const K=document.getElementById("btn-email-unbind");K&&K.addEventListener("click",A);const G=document.getElementById("btn-email-trigger");G&&G.addEventListener("click",g);const W=document.getElementById("email-enabled-toggle");W&&W.addEventListener("change",f);const te=document.getElementById("email-modal-close");te&&te.addEventListener("click",r);const re=document.getElementById("btn-email-modal-cancel");re&&re.addEventListener("click",r);const S=document.getElementById("btn-email-modal-test");S&&S.addEventListener("click",q);const y=document.getElementById("btn-email-modal-save");y&&y.addEventListener("click",F);const m=document.getElementById("email-preset");m&&m.addEventListener("change",Y=>v(Y.target.value));const $=document.getElementById("email-address");$&&!$.dataset.autoBound&&($.dataset.autoBound="1",$.addEventListener("blur",Y=>x((Y.target.value||"").trim())),$.addEventListener("input",Y=>{const Z=(Y.target.value||"").trim();Z.includes("@")&&Z.split("@")[1].includes(".")&&x(Z)}));const P=document.getElementById("btn-email-refresh-logs");P&&P.addEventListener("click",()=>{P.classList.add("spinning"),setTimeout(()=>P.classList.remove("spinning"),600),h()})}L(),window._loadEmailIngestPanel=u,window._rerenderEmailIngest=function(){if(!o)return;l();const _=document.getElementById("email-logs-section");e&&_&&_.open&&h()};let H=null;window._startEmailLogAutoRefresh=function(){H||(H=setInterval(()=>{e&&o&&h()},3e4))},window._stopEmailLogAutoRefresh=function(){H&&(clearInterval(H),H=null)}})();(function(){let e=[],n=null,a=[],o="all",s=null,u=!1;async function l(){if(u){L();return}u=!0,k(),await i(),L()}function k(){const d=document.getElementById("bank-file-input");d&&!d._bound&&(d._bound=!0,d.addEventListener("change",x));const j=document.getElementById("btn-bank-queue-clear-done");j&&!j._bound&&(j._bound=!0,j.addEventListener("click",q));const O=document.getElementById("btn-bank-back");O&&!O._bound&&(O._bound=!0,O.addEventListener("click",()=>{n=null,a=[],te()}));const J=document.getElementById("btn-bank-delete");J&&!J._bound&&(J._bound=!0,J.addEventListener("click",f));const X=document.getElementById("btn-bank-run-match");X&&!X._bound&&(X._bound=!0,X.addEventListener("click",g)),document.querySelectorAll(".bank-filter-btn").forEach(ve=>{ve._bound||(ve._bound=!0,ve.addEventListener("click",()=>{o=ve.dataset.bankFilter||"all",document.querySelectorAll(".bank-filter-btn").forEach(fe=>{fe.classList.toggle("active",fe===ve)}),Z()}))}),document.querySelectorAll("[data-bank-cand-close]").forEach(ve=>{ve._bound||(ve._bound=!0,ve.addEventListener("click",ne))});const de=document.getElementById("btn-bank-cand-pane-close");de&&!de._bound&&(de._bound=!0,de.addEventListener("click",ne));const se=document.getElementById("btn-bank-cand-ignore");se&&!se._bound&&(se._bound=!0,se.addEventListener("click",h));const ce=document.getElementById("btn-bank-cand-ignore-pane");ce&&!ce._bound&&(ce._bound=!0,ce.addEventListener("click",h));const ae=document.getElementById("bank-client-badge");ae&&!ae._bound&&(ae._bound=!0,ae.addEventListener("click",y)),document.querySelectorAll("[data-bank-client-picker-close]").forEach(ve=>{ve._bound||(ve._bound=!0,ve.addEventListener("click",m))});const pe=document.getElementById("btn-bank-client-picker-save");pe&&!pe._bound&&(pe._bound=!0,pe.addEventListener("click",P)),document.querySelectorAll(".bank-sessions-chip").forEach(ve=>{ve._bound||(ve._bound=!0,ve.addEventListener("click",()=>{H=ve.dataset.sessFilter||"all",document.querySelectorAll(".bank-sessions-chip").forEach(fe=>{fe.classList.toggle("active",fe===ve)}),_()}))})}async function i(){try{const d=await fetch("/api/bank-recon/sessions?limit=30",{headers:{Authorization:"Bearer "+token}});if(!d.ok)throw new Error("sessions:"+d.status);e=await d.json(),_()}catch(d){console.warn("[bank-recon] loadSessions failed",d),e=[],_()}}async function p(d){try{const j="/api/bank-recon/sessions/"+encodeURIComponent(d)+(o!=="all"?"?filter="+o:""),O=await fetch(j,{headers:{Authorization:"Bearer "+token}});if(!O.ok)throw new Error("detail:"+O.status);const J=await O.json();n=J.session,a=J.transactions||[],W()}catch(j){console.warn("[bank-recon] loadSessionDetail failed",j),showToast(t("bank-load-failed"),"error")}}let c=[],r=0;const v=3;function E(){return r+=1,"q"+r+"_"+Date.now()}async function x(d){const j=Array.from(d.target.files||[]);if(d.target.value="",j.length!==0){for(const O of j){const J={id:E(),file:O,name:O.name,size:O.size,status:"pending",progress:0,error_code:null,tx_count:0,session_id:null};O.name.toLowerCase().endsWith(".pdf")?O.size>20*1024*1024&&(J.status="failed",J.error_code="bank_recon.file_too_large"):(J.status="failed",J.error_code="bank_recon.only_pdf"),c.push(J)}R(),D(),F()}}function R(){const d=document.getElementById("bank-upload-queue");d&&(d.style.display=""),oe(),ue()}function D(){const d=document.getElementById("bank-upload-queue-list"),j=document.getElementById("bank-upload-queue-summary");if(!d)return;if(c.length===0){d.innerHTML="",j&&(j.textContent="");const se=document.getElementById("bank-upload-queue");se&&(se.style.display="none");return}let O=0,J=0,X=0,de=0;for(const se of c)se.status==="ok"?O++:se.status==="failed"?J++:se.status==="uploading"||se.status==="parsing"?X++:de++;j&&(j.textContent=t("bank-queue-summary").replace("{ok}",O).replace("{run}",X).replace("{wait}",de).replace("{fail}",J)),d.innerHTML=c.map(w).join(""),d.querySelectorAll("[data-q-act]").forEach(se=>{const ce=se.dataset.qAct,ae=se.dataset.qId;se.addEventListener("click",()=>{ce==="retry"&&B(ae),ce==="remove"&&z(ae)})})}function w(d){const j=(d.size/1024).toFixed(0)+" KB";let O="",J="";if(d.status==="pending")O='<span class="bq-stat bq-wait">'+t("bank-queue-status-wait")+"</span>",J='<button data-q-act="remove" data-q-id="'+N(d.id)+'" class="bq-act">×</button>';else if(d.status==="uploading")O='<span class="bq-stat bq-run">'+t("bank-queue-status-uploading")+'</span><div class="bq-bar"><div class="bq-bar-fill" style="width:'+(d.progress||0)+'%"></div></div>';else if(d.status==="parsing")O='<span class="bq-stat bq-run">'+t("bank-queue-status-parsing")+'</span><div class="bq-bar"><div class="bq-bar-fill bq-bar-indet"></div></div>';else if(d.status==="ok")O='<span class="bq-stat bq-ok">'+t("bank-queue-status-ok").replace("{n}",d.tx_count||0)+"</span>",J='<button data-q-act="remove" data-q-id="'+N(d.id)+'" class="bq-act">×</button>';else if(d.status==="failed"){const X=b(d.error_code||"unknown");O='<span class="bq-stat bq-fail" title="'+N(X)+'">'+N(X)+"</span>",J='<button data-q-act="retry" data-q-id="'+N(d.id)+'" class="bq-act bq-act-retry">'+t("bank-queue-retry")+'</button><button data-q-act="remove" data-q-id="'+N(d.id)+'" class="bq-act">×</button>'}return'<div class="bq-row" data-q-row="'+N(d.id)+'"><div class="bq-name" title="'+N(d.name)+'">'+N(d.name)+'</div><div class="bq-size">'+j+'</div><div class="bq-status">'+O+'</div><div class="bq-actions">'+J+"</div></div>"}function B(d){const j=c.find(O=>O.id===d);j&&(j.status="pending",j.error_code=null,j.progress=0,D(),F())}function z(d){const j=c.findIndex(J=>J.id===d);if(j<0)return;const O=c[j];O.status==="uploading"||O.status==="parsing"||(c.splice(j,1),D())}function q(){c=c.filter(d=>d.status!=="ok"),D()}async function F(){for(;;){if(c.filter(O=>O.status==="uploading"||O.status==="parsing").length>=v)return;const j=c.find(O=>O.status==="pending");if(!j){c.every(O=>O.status==="ok"||O.status==="failed")&&(await i(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage());return}A(j).then(()=>F())}}async function A(d){d.status="uploading",d.progress=0,D();try{const j=new FormData;j.append("file",d.file,d.name);const O=await new Promise((X,de)=>{const se=new XMLHttpRequest;se.open("POST","/api/bank-recon/upload"),se.setRequestHeader("Authorization","Bearer "+token),se.upload.onprogress=ce=>{ce.lengthComputable&&(d.progress=Math.min(99,Math.round(ce.loaded/ce.total*100)),D())},se.upload.onload=()=>{d.status="parsing",D()},se.onload=()=>{se.status>=200&&se.status<300?X({status:se.status,text:se.responseText}):X({status:se.status,text:se.responseText})},se.onerror=()=>de(new Error("network")),se.send(j)});let J={};try{J=JSON.parse(O.text||"{}")}catch{J={}}if(O.status>=400){d.status="failed",d.error_code=J&&J.detail||"unknown",D();return}if(J.parse_status==="parse_failed"){d.status="failed",d.error_code=J.error==="scanned_pdf_not_yet"?"bank_recon.scanned":"bank_recon.no_tx",D();return}d.status="ok",d.tx_count=J.tx_count||0,d.session_id=J.session_id||null,D()}catch(j){console.warn("[bank-recon] upload failed",j),d.status="failed",d.error_code="network",D()}}async function g(){if(!n)return;const d=document.getElementById("btn-bank-run-match"),j=d.innerHTML;d.disabled=!0,d.innerHTML="<span>"+t("bank-matching")+"</span>";try{const O=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id)+"/match",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!O.ok)throw new Error("match:"+O.status);const J=await O.json();showToast(t("bank-match-done").replace("{matched}",J.matched).replace("{suggested}",J.suggested).replace("{unmatched}",J.unmatched),"success"),await p(n.id),await i()}catch(O){console.warn("[bank-recon] match failed",O),showToast(t("bank-match-failed"),"error")}finally{d.disabled=!1,d.innerHTML=j}}async function f(){if(!(!n||!await showConfirm(t("bank-delete-confirm"),{danger:!0})))try{const j=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!j.ok)throw new Error("delete:"+j.status);showToast(t("bank-deleted"),"success"),n=null,a=[],te(),await i()}catch(j){console.warn("[bank-recon] delete failed",j),showToast(t("bank-delete-failed"),"error")}}async function h(){if(s)try{const d=await fetch("/api/bank-recon/tx/"+encodeURIComponent(s.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"ignored"})});if(!d.ok)throw new Error("ignore:"+d.status);ne(),await p(n.id)}catch{showToast(t("bank-action-failed"),"error")}}async function I(d){if(s)try{const j=await fetch("/api/bank-recon/tx/"+encodeURIComponent(s.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"matched",history_id:d})});if(!j.ok)throw new Error("pick:"+j.status);showToast(t("bank-matched-ok"),"success"),ne(),await p(n.id)}catch{showToast(t("bank-action-failed"),"error")}}function L(){const d=document.getElementById("bank-status-summary");if(!d)return;if(e.length===0){d.textContent=t("bank-pill-none");return}let O=0;for(const J of e)J.parse_status==="parsed"&&(J.unmatched_count||0)>0&&O++;d.textContent=O>0?t("bank-pill-pending").replace("{n}",O):t("bank-pill-ok")}let H="all";function _(){const d=document.getElementById("bank-sessions-list");if(!d)return;let j=e||[];if(H==="parsed"?j=j.filter(O=>O.parse_status==="parsed"):H==="failed"&&(j=j.filter(O=>O.parse_status==="parse_failed")),!e||e.length===0){d.innerHTML='<div class="bank-empty" data-i18n="bank-sessions-empty">'+t("bank-sessions-empty")+"</div>";return}if(j.length===0){d.innerHTML='<div class="bank-empty">'+t("bank-sess-filter-empty")+"</div>";return}d.innerHTML=j.map(O=>K(O)).join(""),d.querySelectorAll(".bank-session-row").forEach(O=>{O.addEventListener("click",J=>{J.target.closest(".bank-session-trash")||p(O.dataset.sessionId)})}),d.querySelectorAll(".bank-session-trash").forEach(O=>{O.addEventListener("click",J=>{J.stopPropagation();const X=O.dataset.sessionId,de=O.dataset.sessionName||"";M(X,de)})})}async function M(d,j){if(!d)return;const O=(t("bank-session-delete-confirm")||"确定删除这条对账记录吗?").replace("{name}",j||"");if(await showConfirm(O,{danger:!0}))try{const X=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(d),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!X.ok)throw new Error("delete:"+X.status);showToast(t("bank-deleted"),"success"),n&&n.id===d&&(n=null,a=[],te()),await i(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()}catch(X){console.warn("[bank-recon] delete failed",X),showToast(t("bank-delete-failed"),"error")}}window._deleteBankSession=M;function K(d){const j=(d.bank_code||"OTHER").toUpperCase(),O=U(d.period_start,d.period_end),J=d.account_last4?"···"+d.account_last4:"",X=G(d),de=T(d.created_at);return`
            <div class="bank-session-row" data-session-id="${N(d.id)}">
                <div class="bank-session-bank bk-${N(j)}">${N(j)}</div>
                <div class="bank-session-info">
                    <div class="bank-session-title">${N(d.source_filename||O||"-")}</div>
                    <div class="bank-session-meta">${N(O)} · ${N(J)} · ${N(de)}</div>
                </div>
                <div class="bank-session-counts">${X}</div>
                <button class="bank-session-trash" data-session-id="${N(d.id)}" data-session-name="${N(d.source_filename||"")}" title="${N(t("bank-session-delete-tip")||"删除")}">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/>
                    </svg>
                </button>
                <div class="bank-session-arrow">
                    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg>
                </div>
            </div>
        `}function G(d){if(d.parse_status==="parse_failed")return`<span class="bank-session-count cnt-failed">${t("bank-count-parse-failed")}</span>`;if(d.parse_status!=="parsed")return`<span class="bank-session-count">${t("bank-count-parsing")}</span>`;const j=d.tx_count||0,O=d.matched_count||0,J=d.unmatched_count||0,X=[`<span class="bank-session-count">${j} ${t("bank-count-tx")}</span>`];return O>0&&X.push(`<span class="bank-session-count cnt-matched">${O} ${t("bank-count-matched")}</span>`),J>0&&X.push(`<span class="bank-session-count cnt-unmatched">${J} ${t("bank-count-unmatched")}</span>`),X.join("")}function W(){document.getElementById("bank-detail").style.display="",document.querySelector(".bank-sessions-section").style.display="none",Y(),Z(),re()}function te(){document.getElementById("bank-detail").style.display="none",document.querySelector(".bank-sessions-section").style.display="";const d=document.getElementById("bank-detail-body");d&&d.classList.remove("has-pane"),s=null}function re(){const d=document.getElementById("bank-client-badge");if(!d||!n)return;const j=n.client_id,O=document.getElementById("bank-client-badge-dot"),J=document.getElementById("bank-client-badge-name"),X=document.getElementById("bank-client-badge-caret"),de=typeof _userInfo<"u"?_userInfo:null,se=!(de&&de.role==="member");if(j!=null){const ce=(window._clientsCache||[]).find(ae=>Number(ae.id)===Number(j));d.classList.remove("is-empty"),O&&(O.style.background=ce&&ce.color||"#111111"),J&&(J.textContent=ce&&(ce.short_name||ce.name)||"#"+j)}else d.classList.add("is-empty"),O&&(O.style.background=""),J&&(J.textContent=t("bank-client-none"));se?(d.classList.remove("is-readonly"),d.disabled=!1,X&&(X.style.display="")):(d.classList.add("is-readonly"),d.disabled=!0,X&&(X.style.display="none")),d.style.display=""}let S=null;function y(){if(!n)return;const d=typeof _userInfo<"u"?_userInfo:null;if(!!(d&&d.role==="member"))return;S=n.client_id!=null?Number(n.client_id):null,$();const O=document.getElementById("bank-client-picker-modal");O&&(O.style.display="")}function m(){const d=document.getElementById("bank-client-picker-modal");d&&(d.style.display="none"),S=null}function $(){const d=document.getElementById("bank-client-picker-list");if(!d)return;const j=(window._clientsCache||[]).filter(J=>J&&(J.is_active===!0||J.is_active===void 0)),O=[];O.push('<div class="bank-client-picker-row is-none'+(S==null?" is-selected":"")+'" data-cid=""><span class="bank-cp-dot"></span><span>'+N(t("bank-client-picker-none"))+"</span></div>"),j.forEach(J=>{const X=Number(J.id)===Number(S)?" is-selected":"";O.push('<div class="bank-client-picker-row'+X+'" data-cid="'+N(J.id)+'"><span class="bank-cp-dot" style="background:'+N(J.color||"#111111")+'"></span><span>'+N(J.short_name||J.name||"#"+J.id)+"</span></div>")}),d.innerHTML=O.join(""),d.querySelectorAll(".bank-client-picker-row").forEach(J=>{J.addEventListener("click",()=>{const X=J.dataset.cid;S=X?Number(X):null,$()})})}async function P(){if(n)try{const d=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id)+"/client",{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({client_id:S})});if(!d.ok)throw new Error("client:"+d.status);n.client_id=S,re(),showToast(t("bank-client-changed"),"success"),m();try{await i()}catch{}}catch(d){console.warn("[bank-recon] save client failed",d),showToast(t("bank-client-change-failed"),"error")}}function Y(){if(!n)return;const d=n;document.getElementById("bank-detail-title").textContent=(d.bank_code||"-")+(d.account_last4?" ···"+d.account_last4:"")+" · "+(d.source_filename||""),document.getElementById("bank-meta-period").textContent=U(d.period_start,d.period_end)||"-",document.getElementById("bank-meta-opening").textContent=C(d.opening_balance),document.getElementById("bank-meta-inflow").textContent="+"+C(d.total_inflow),document.getElementById("bank-meta-outflow").textContent="-"+C(d.total_outflow),document.getElementById("bank-meta-closing").textContent=C(d.closing_balance);const j=a||[],O=j.length;let J=0,X=0,de=0;for(const se of j){const ce=se.match_status||"unmatched";ce==="matched"?J++:ce==="suggested"?X++:de++}document.getElementById("bank-stat-total").textContent=O,document.getElementById("bank-stat-matched").textContent=J,document.getElementById("bank-stat-suggested").textContent=X,document.getElementById("bank-stat-unmatched").textContent=de}function Z(){const d=document.getElementById("bank-tx-tbody");if(!d)return;let j=a||[];if(o!=="all"&&(j=j.filter(O=>o==="matched"?O.match_status==="matched":o==="suggested"?O.match_status==="suggested":o==="unmatched"?O.match_status==="unmatched"||O.match_status==="ignored":!0)),j.length===0){d.innerHTML=`<tr><td colspan="4" class="bank-empty">${t("bank-tx-empty")}</td></tr>`;return}if(d.innerHTML=j.map(O=>le(O)).join(""),d.querySelectorAll("tr[data-tx-id]").forEach(O=>{O.addEventListener("click",()=>{const J=O.dataset.txId,X=a.find(de=>de.id===J);X&&(d.querySelectorAll("tr.is-selected").forEach(de=>de.classList.remove("is-selected")),O.classList.add("is-selected"),ie(X))})}),s){const O=d.querySelector('tr[data-tx-id="'+s.id+'"]');O&&O.classList.add("is-selected")}}function le(d){const j=d.direction==="OUT",O=j?"-":"+",J=j?"bank-out":"bank-in",X=d.match_status||"unmatched",de=t("bank-match-"+X)||X,se=T(d.tx_date),ce=d.channel?`<span class="bank-tx-channel">${N(d.channel)}</span>`:"";return`
            <tr data-tx-id="${N(d.id)}">
                <td class="bank-tx-date">${N(se)}</td>
                <td class="bank-tx-desc">${ce}${N(d.description||"-")}</td>
                <td class="bank-td-amount ${J}">${O}${C(d.amount)}</td>
                <td><span class="bank-tx-match mt-${X}">${N(de)}</span></td>
            </tr>
        `}async function ie(d){s=d;const j=document.getElementById("bank-detail-body");j&&j.classList.add("has-pane");const O=document.getElementById("bank-cand-pane-title"),J=document.getElementById("bank-cand-pane-sub"),X=document.getElementById("bank-cand-pane-foot");if(O&&(O.textContent=t("bank-cand-pane-current")),J){const se=d.direction==="OUT"?"-":"+",ce=d.direction==="OUT"?"bank-out":"bank-in";J.innerHTML=`${N(T(d.tx_date))}
                <span style="margin:0 6px;color:#D1D5DB">·</span>
                <span>${N(d.description||"-")}</span>
                <span style="margin:0 6px;color:#D1D5DB">·</span>
                <strong class="${ce}">${se}${C(d.amount)}</strong>`}X&&(X.style.display="");const de=document.getElementById("bank-cand-pane-body");if(de){de.innerHTML=`<div class="bank-empty">${t("bank-cand-loading")}</div>`;try{const se=await fetch("/api/bank-recon/tx/"+encodeURIComponent(d.id)+"/candidates",{headers:{Authorization:"Bearer "+token}});if(!se.ok)throw new Error("cands:"+se.status);const ce=await se.json();ee(d,ce.candidates||[])}catch{de.innerHTML=`<div class="bank-empty">${t("bank-cand-load-failed")}</div>`}}}function V(d){const j=Number(d||0);let O="score-low";return j>=85?O="score-high":j>=60&&(O="score-mid"),'<span class="bank-cand-score '+O+'">'+j.toFixed(0)+" "+t("bank-cand-score-unit")+"</span>"}function Q(d,j,O){const J=j.history_id,X=j.invoice_no||"-",de=j.vendor||"-",se=j.amount_total!==null&&j.amount_total!==void 0?C(j.amount_total):"-",ce=j.invoice_date?T(j.invoice_date):"-",ae=j.filename||"",pe=!!O&&d.matched_history_id===J,ve="bank-cand-card"+(j.is_auto_picked?" is-auto":"")+(pe?" is-picked":"");let fe="";return pe?fe='<button class="btn btn-ghost btn-small" data-act="unmatch"><span>'+t("bank-cand-unmatch")+"</span></button>":fe='<button class="btn btn-primary btn-small" data-act="pick" data-hid="'+N(J)+'"><span>'+t(j.is_auto_picked?"bank-cand-confirm":"bank-cand-pick-this")+"</span></button>",'<div class="'+ve+'" data-hid="'+N(J)+'"><div class="bank-cand-card-head"><div class="bank-cand-card-vendor">'+N(de)+"</div>"+V(j.score)+'</div><div class="bank-cand-card-fields"><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-invoice-no")+"</span> "+N(X)+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-amount")+"</span> "+se+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-date")+"</span> "+N(ce)+"</span></div>"+(ae?'<div class="bank-cand-card-file" title="'+N(ae)+'">'+N(ae)+"</div>":"")+(j.reason?'<div class="bank-cand-card-reason">'+N(j.reason)+"</div>":"")+'<div class="bank-cand-card-actions">'+fe+"</div></div>"}function ee(d,j){const O=document.getElementById("bank-cand-pane-body");if(!O)return;const J=j||[];let X="";if(d.match_status==="matched")X='<div class="bank-cand-hint hint-matched">'+t("bank-cand-hint-matched").replace("{n}",J.length)+"</div>";else if(d.match_status==="suggested")X='<div class="bank-cand-hint hint-suggested">'+t("bank-cand-hint-suggested").replace("{n}",J.length)+"</div>";else if(J.length>0)X='<div class="bank-cand-hint hint-low">'+t("bank-cand-hint-low").replace("{n}",J.length)+"</div>";else{O.innerHTML='<div class="bank-empty">'+t("bank-cand-no-match-detail")+"</div>";return}const de=d.match_status==="matched",se=J.map(ce=>Q(d,ce,de)).join("");O.innerHTML=X+'<div class="bank-cand-list">'+se+"</div>",O.querySelectorAll('[data-act="pick"]').forEach(ce=>{ce.addEventListener("click",()=>{I(ce.dataset.hid)})}),O.querySelectorAll('[data-act="unmatch"]').forEach(ce=>{ce.addEventListener("click",async()=>{try{await fetch("/api/bank-recon/tx/"+encodeURIComponent(d.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"unmatched"})}),ne(),await p(n.id)}catch{showToast(t("bank-action-failed"),"error")}})})}function ne(){const d=document.getElementById("bank-detail-body");d&&d.classList.remove("has-pane");const j=document.getElementById("bank-cand-pane-title"),O=document.getElementById("bank-cand-pane-sub"),J=document.getElementById("bank-cand-pane-body"),X=document.getElementById("bank-cand-pane-foot");j&&(j.textContent=t("bank-cand-pane-empty-title")),O&&(O.textContent=t("bank-cand-pane-empty-sub")),X&&(X.style.display="none"),J&&(J.innerHTML='<div class="bank-cand-pane-empty"><svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="14" y="10" width="36" height="44" rx="3"/><path d="M22 22h20M22 30h20M22 38h12"/></svg><div>'+t("bank-cand-pane-empty-hint")+"</div></div>");const de=document.getElementById("bank-tx-tbody");de&&de.querySelectorAll("tr.is-selected").forEach(se=>se.classList.remove("is-selected")),s=null}function oe(d){const j=document.getElementById("bank-upload-progress");j&&(j.style.display="none")}function ue(){const d=document.getElementById("bank-upload-error");d&&(d.style.display="none")}function b(d){return{"bank_recon.only_pdf":t("bank-err-only-pdf"),"bank_recon.empty_file":t("bank-err-empty"),"bank_recon.file_too_large":t("bank-err-too-large"),"bank_recon.save_failed":t("bank-err-server"),"bank_recon.scanned":t("bank-err-scanned"),"bank_recon.no_tx":t("bank-err-no-tx"),network:t("bank-err-network")}[d]||t("bank-err-unknown")+" ("+d+")"}function C(d){if(d==null)return"-";const j=Number(d);return isNaN(j)?"-":j.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function T(d){if(!d)return"-";const j=String(d);return j.length>=10?j.slice(0,10):j}function U(d,j){return!d&&!j?"":(T(d)||"?")+" ~ "+(T(j)||"?")}function N(d){return d==null?"":String(d).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}window._loadBankReconPanel=l,window._rerenderBankRecon=function(){if(currentRoute==="automation"){if(_(),n&&(Y(),Z(),re(),!s)){const d=document.getElementById("bank-cand-pane-title"),j=document.getElementById("bank-cand-pane-sub");d&&(d.textContent=t("bank-cand-pane-empty-title")),j&&(j.textContent=t("bank-cand-pane-empty-sub"))}D()}},typeof window.subscribeI18n=="function"&&window.subscribeI18n("bank-recon",window._rerenderBankRecon),window._openBankSession=async function(d){d&&(u||await l(),await p(d))}})();(function(){const e=document.getElementById("page-clients");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){let e=[],n=null,a="",o="seller";const s={page:0,pageSize:12,keyword:""},u=new Set;let l=[];const k={keyword:""};let i=null;function p(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}async function c(m,$={}){const P=await fetch(m,{...$,headers:{"Content-Type":"application/json",...p(),...$.headers||{}}});if(!P.ok){const Y=await P.json().catch(()=>({}));throw new Error(Y.detail||"HTTP "+P.status)}return P.json()}async function r(){try{e=(await c("/api/clients")).clients||[],window._clientsCache=e}catch(m){console.error("loadClientsCache fail",m),e=[]}try{typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter()}catch{}try{typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher()}catch{}return e}function v(m){o=m==="buyer"?"buyer":"seller",document.querySelectorAll("[data-cust-tab]").forEach(Y=>Y.classList.toggle("active",Y.dataset.custTab===o));const $=document.getElementById("cust-pane-seller"),P=document.getElementById("cust-pane-buyer");$&&$.classList.toggle("active",o==="seller"),P&&P.classList.toggle("active",o==="buyer")}function E(){const m=window._userInfo||{},$=String(m.role||"").toLowerCase(),P=String(m.tenant_role||"").toLowerCase();return m.is_super_admin===!0||m.is_owner===!0||$==="owner"||$==="admin"||P==="owner"||P==="admin"}function x(){window._workspaceClientsCache=l,typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl()}async function R(){try{const m=await c("/api/workspace/clients");l=m&&(m.clients||m.items)||[],window._workspaceClientsCache=l}catch(m){console.error("loadSellerCache fail",m),l=[]}return l}function D(){const m=k.keyword.trim().toLowerCase();return m?l.filter($=>($.name||"").toLowerCase().includes(m)||($.tax_id||"").toLowerCase().includes(m)):l}function w(){const m=document.getElementById("seller-tbody");if(!m)return;const $=E(),P=document.getElementById("btn-seller-new");P&&(P.style.display=$?"":"none");const Y=D(),Z=typeof window.getActiveWorkspaceClientId=="function"?window.getActiveWorkspaceClientId():null;if(!Y.length){m.innerHTML=`<div class="cust-empty">${escapeHtml(t(k.keyword?"cust-no-match":"seller-empty"))}</div>`;return}m.innerHTML=Y.map(le=>{const V=Z!=null&&Number(Z)===Number(le.id)?`<span class="cust-badge-current"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7.5l3.2 3.2L12 4"/></svg>${escapeHtml(t("seller-current"))}</span>`:`<button class="cust-row-btn primary" data-saction="activate" data-wid="${le.id}">${escapeHtml(t("seller-set-current"))}</button>`,Q=$?`
                <button class="cust-row-btn" data-saction="edit" data-wid="${le.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
                <button class="cust-row-btn danger" data-saction="archive" data-wid="${le.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h10M4 4v7a1 1 0 001 1h4a1 1 0 001-1V4M5.5 4V2.8a1 1 0 011-1h1a1 1 0 011 1V4"/></svg><span>${escapeHtml(t("wsclient-archive"))}</span></button>`:"";return`<div class="cust-row seller-grid" data-wid="${le.id}">
                <div class="cust-cell-name"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" style="flex-shrink:0;opacity:.55"><rect x="2" y="5" width="12" height="9" rx="1"/><path d="M10 14V4a1 1 0 00-1-1H7a1 1 0 00-1 1v10"/></svg><span class="cust-name-text">${escapeHtml(le.name||"#"+le.id)}</span></div>
                <div class="cust-cell-tax">${escapeHtml(le.tax_id||"—")}</div>
                <div class="align-right">${le.invoice_count||0}</div>
                <div class="cust-row-actions">${V}${Q}</div>
            </div>`}).join("")}function B(m){i=m?m.id:null,document.getElementById("wsclient-modal-title").textContent=t(m?"wsclient-modal-edit":"wsclient-modal-new"),document.getElementById("wsclient-input-name").value=m&&m.name||"",document.getElementById("wsclient-input-tax").value=m&&m.tax_id||"",document.getElementById("wsclient-modal-archive").style.display=m?"":"none",document.getElementById("wsclient-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("wsclient-input-name").focus(),50)}function z(){document.getElementById("wsclient-modal-mask").style.display="none",i=null}async function q(){const m=document.getElementById("wsclient-input-name").value.trim(),$=document.getElementById("wsclient-input-tax").value.trim();if(!m){showToast(t("client-msg-name-required"),"fail");return}try{i?(await c("/api/workspace/clients/"+i,{method:"PATCH",body:JSON.stringify({name:m,tax_id:$})}),showToast(t("client-msg-updated"),"success")):(await c("/api/workspace/clients",{method:"POST",body:JSON.stringify({name:m,tax_id:$||null})}),showToast(t("client-msg-created"),"success")),z(),await R(),w(),x()}catch(P){const Y=P&&P.message?P.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+Y,"fail")}}async function F(){if(!i)return;const m=l.find(P=>Number(P.id)===Number(i));if(await showConfirm(t("wsclient-archive-confirm").replace("{name}",m?m.name:""),{danger:!0}))try{const P=i;await c("/api/workspace/clients/"+P,{method:"DELETE"}),showToast(t("wsclient-archived"),"success"),typeof window.getActiveWorkspaceClientId=="function"&&Number(window.getActiveWorkspaceClientId())===Number(P)&&typeof window.enterPersonalMode=="function"&&window.enterPersonalMode(),z(),await R(),w(),x()}catch{showToast(t("client-msg-save-fail"),"fail")}}function A(){const m=s.keyword.trim().toLowerCase();return m?e.filter($=>($.name||"").toLowerCase().includes(m)||($.short_name||"").toLowerCase().includes(m)||($.tax_id||"").toLowerCase().includes(m)):e}function g(){const m=A(),$=s.pageSize,P=Math.max(0,Math.ceil(m.length/$)-1);s.page>P&&(s.page=P);const Y=s.page*$;return{all:m,items:m.slice(Y,Y+$),start:Y,ps:$,total:m.length,maxPage:P}}function f(){const m=document.getElementById("buyer-tbody");if(!m)return;const{items:$,start:P,ps:Y,total:Z,maxPage:le}=g();Z?m.innerHTML=$.map(ee=>{const ne=u.has(ee.id);return`<div class="cust-row buyer-grid${ne?" selected":""}" data-cid="${ee.id}">
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
                </div>`}).join(""):m.innerHTML=`<div class="cust-empty">${escapeHtml(t(s.keyword?"cust-no-match":"clients-empty"))}</div>`;const ie=document.getElementById("buyer-pager-info");ie&&(ie.textContent=Z?`${P+1}–${Math.min(P+Y,Z)} / ${Z}`:"0");const V=document.getElementById("buyer-prev");V&&(V.disabled=s.page<=0);const Q=document.getElementById("buyer-next");Q&&(Q.disabled=s.page>=le),h()}function h(){const m=u.size,$=document.getElementById("buyer-batch-bar");$&&($.style.display=m?"flex":"none");const P=document.getElementById("buyer-batch-count");P&&(P.textContent=t("cust-selected-n").replace("{n}",m));const Y=document.getElementById("buyer-check-all");if(Y){const{items:Z}=g(),le=Z.map(V=>V.id),ie=le.filter(V=>u.has(V)).length;Y.checked=le.length>0&&ie===le.length,Y.indeterminate=ie>0&&ie<le.length}}function I(){u.clear(),f()}async function L(){const m=Array.from(u);if(!(!m.length||!await showConfirm(t("cust-batch-del-confirm").replace("{n}",m.length),{danger:!0})))try{await c("/api/clients/batch-delete",{method:"POST",body:JSON.stringify({ids:m})}),showToast(t("client-msg-deleted"),"success"),u.clear(),await r(),f(),te(),y()}catch{showToast(t("client-msg-save-fail"),"fail")}}window.loadClientsPage=async function(){const m=document.getElementById("seller-tbody");m&&(m.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`);const $=document.getElementById("buyer-tbody");$&&($.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`),await Promise.all([R(),r()]),w(),f()},window.addEventListener("pearnly:workspace-changed",function(){typeof currentRoute<"u"&&currentRoute==="clients"&&w()});function H(m){n=m?m.id:null;const $=!!m;document.getElementById("client-modal-title").textContent=t($?"client-modal-edit":"client-modal-new"),document.getElementById("client-input-name").value=m&&m.name||"",document.getElementById("client-input-short").value=m&&m.short_name||"",document.getElementById("client-input-tax").value=m&&m.tax_id||"",document.getElementById("client-input-address").value=m&&m.address||"",document.getElementById("client-input-contact").value=m&&m.contact_person||"",document.getElementById("client-input-phone").value=m&&m.contact_phone||"",document.getElementById("client-input-email").value=m&&m.contact_email||"",document.getElementById("client-input-notes").value=m&&m.notes||"";const P=m&&m.color||"#111111";document.querySelectorAll("#client-color-picker .color-swatch").forEach(Y=>{Y.classList.toggle("active",Y.dataset.color===P)}),document.getElementById("client-modal-delete").style.display=$?"":"none",document.getElementById("client-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("client-input-name").focus(),50)}function _(){document.getElementById("client-modal-mask").style.display="none",n=null}function M(){const m=document.querySelector("#client-color-picker .color-swatch.active");return m?m.dataset.color:"#111111"}async function K(){const m=document.getElementById("client-input-name").value.trim();if(!m){showToast(t("client-msg-name-required"),"fail");return}const $={name:m,short_name:document.getElementById("client-input-short").value.trim()||null,tax_id:document.getElementById("client-input-tax").value.trim()||null,address:document.getElementById("client-input-address").value.trim()||null,contact_person:document.getElementById("client-input-contact").value.trim()||null,contact_phone:document.getElementById("client-input-phone").value.trim()||null,contact_email:document.getElementById("client-input-email").value.trim()||null,notes:document.getElementById("client-input-notes").value.trim()||null,color:M()};try{n?(await c(`/api/clients/${n}`,{method:"PATCH",body:JSON.stringify($)}),showToast(t("client-msg-updated"),"success")):(await c("/api/clients",{method:"POST",body:JSON.stringify($)}),showToast(t("client-msg-created"),"success")),_(),await r(),currentRoute==="clients"&&f(),te(),y()}catch(P){console.error("saveClient fail",P);const Y=P&&P.message?P.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+Y,"fail")}}async function G(){if(!n)return;const m=e.find(Y=>Y.id===n);if(!m)return;const $=t("client-delete-confirm").replace("{name}",m.name);if(await showConfirm($,{danger:!0}))try{await c(`/api/clients/${n}`,{method:"DELETE"}),showToast(t("client-msg-deleted"),"success"),_(),await r(),currentRoute==="clients"&&f(),te(),y()}catch(Y){console.error(Y),showToast(t("client-msg-save-fail"),"fail")}}async function W(m){const $=e.find(P=>P.id===m);if(typeof window.openClientExportModal=="function"){window.openClientExportModal(m,$?$.name:"");return}try{const P=localStorage.getItem("mrpilot_token"),Y=await fetch(`/api/clients/${m}/export?month=all`,{headers:{Authorization:"Bearer "+P}});if(!Y.ok){let Q="HTTP "+Y.status;try{const ee=await Y.json();ee&&ee.detail&&(Q=ee.detail)}catch{}throw new Error(Q)}const Z=await Y.blob();if(Z.size<200){showToast(t("client-export-month-empty"),"info");return}const le=$&&$.name?$.name.replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40):"client",ie=URL.createObjectURL(Z),V=document.createElement("a");V.href=ie,V.download=`${le}_export.csv`,V.click(),URL.revokeObjectURL(ie)}catch(P){console.error("exportClient fail",P),showToast(t("client-msg-save-fail")+" · "+(P.message||""),"fail")}}function te(){const m=document.getElementById("drawer-client-select");if(!m)return;const $=m.value;m.innerHTML=`<option value="">${escapeHtml(t("drawer-client-none"))}</option>`+e.map(P=>`<option value="${P.id}">${escapeHtml(P.name)}</option>`).join(""),m.value=$||""}window.bindDrawerClient=function(m,$){const P=document.getElementById("drawer-client-select");if(!P)return;if(te(),P.value=$?String($):"",!m){P.onchange=null;const Z=document.getElementById("drawer-client-add");Z&&(Z.onclick=()=>H(null));return}P.onchange=async()=>{const Z=P.value?parseInt(P.value,10):null;try{await c(`/api/history/${m}/assign_client`,{method:"POST",body:JSON.stringify({client_id:Z})}),showToast(t("client-msg-updated"),"success");const le=_results[_drawerIdx];le&&(le.client_id=Z),await r()}catch(le){console.error(le),showToast(t("client-msg-save-fail"),"fail"),P.value=$?String($):""}};const Y=document.getElementById("drawer-client-add");Y&&(Y.onclick=()=>H(null))};let re={fetched:0,items:[],supplier_count:0};window.fillCategoryDatalist=async function(){try{const m=document.getElementById("drawer-cat-datalist"),$=Date.now();if($-re.fetched<300*1e3){m&&(m.innerHTML=re.items.map(Y=>`<option value="${escapeHtml(Y)}">`).join("")),S(re.supplier_count);return}const P=await c("/api/categories",{method:"GET"});re.fetched=$,re.items=P&&P.categories||[],re.supplier_count=P&&P.supplier_count||0,m&&(m.innerHTML=re.items.map(Y=>`<option value="${escapeHtml(Y)}">`).join("")),S(re.supplier_count)}catch(m){console.warn("fillCategoryDatalist failed",m)}};function S(m){const $=document.getElementById("drawer-cat-learned-tag");$&&m>0&&($.textContent=(t("drawer-suggest-learned-with-count")||"已学 {n}").replace("{n}",m))}function y(){const m=document.getElementById("history-client-filter");if(!m)return;const $=m.value;m.innerHTML=`<option value="">${escapeHtml(t("history-client-all"))}</option>`+e.map(P=>`<option value="${P.id}">${escapeHtml(P.name)}</option>`).join(""),m.value=$||""}window.getHistoryClientFilter=function(){return a},document.addEventListener("DOMContentLoaded",()=>{const m=document.querySelector(".cust-tab-bar");m&&m.addEventListener("click",ae=>{const pe=ae.target.closest("[data-cust-tab]");pe&&v(pe.dataset.custTab)});const $=document.getElementById("btn-buyer-new");$&&$.addEventListener("click",()=>H(null));const P=document.getElementById("buyer-tbody");P&&P.addEventListener("click",ae=>{const pe=ae.target.closest(".buyer-row-check");if(pe){const ge=parseInt(pe.dataset.cid,10);pe.checked?u.add(ge):u.delete(ge);const be=pe.closest(".cust-row");be&&be.classList.toggle("selected",pe.checked),h();return}const ve=ae.target.closest(".cust-row-btn");if(ve){ae.stopPropagation();const ge=parseInt(ve.dataset.cid,10);if(ve.dataset.action==="edit"){const be=e.find(xe=>xe.id===ge);be&&H(be)}else ve.dataset.action==="export"&&W(ge);return}const fe=ae.target.closest(".cust-row");if(fe&&!ae.target.closest(".cust-cell-check")){const ge=e.find(be=>be.id===parseInt(fe.dataset.cid,10));ge&&H(ge)}});const Y=document.getElementById("buyer-check-all");Y&&Y.addEventListener("change",()=>{const{items:ae}=g();ae.forEach(pe=>{Y.checked?u.add(pe.id):u.delete(pe.id)}),f()});const Z=document.getElementById("buyer-batch-cancel");Z&&Z.addEventListener("click",I);const le=document.getElementById("buyer-batch-delete");le&&le.addEventListener("click",L);const ie=document.getElementById("buyer-prev");ie&&ie.addEventListener("click",()=>{s.page>0&&(s.page--,f())});const V=document.getElementById("buyer-next");V&&V.addEventListener("click",()=>{s.page++,f()});const Q=document.getElementById("buyer-search");if(Q){let ae;Q.addEventListener("input",()=>{clearTimeout(ae),ae=setTimeout(()=>{s.keyword=Q.value,s.page=0;const pe=document.getElementById("buyer-search-clear");pe&&(pe.style.display=Q.value?"":"none"),f()},200)})}const ee=document.getElementById("buyer-search-clear");ee&&ee.addEventListener("click",()=>{const ae=document.getElementById("buyer-search");ae&&(ae.value=""),s.keyword="",s.page=0,ee.style.display="none",f()});const ne=document.getElementById("btn-seller-new");ne&&ne.addEventListener("click",()=>B(null));const oe=document.getElementById("seller-tbody");oe&&oe.addEventListener("click",ae=>{const pe=ae.target.closest("[data-saction]");if(!pe)return;ae.stopPropagation();const ve=parseInt(pe.dataset.wid,10),fe=pe.dataset.saction,ge=l.find(be=>Number(be.id)===ve);fe==="activate"?(typeof window.setActiveWorkspaceClientId=="function"&&window.setActiveWorkspaceClientId(ve),w(),typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl(),showToast(t("seller-activated").replace("{name}",ge?ge.name:""),"success")):fe==="edit"?ge&&B(ge):fe==="archive"&&(i=ve,F())});const ue=document.getElementById("seller-search");if(ue){let ae;ue.addEventListener("input",()=>{clearTimeout(ae),ae=setTimeout(()=>{k.keyword=ue.value;const pe=document.getElementById("seller-search-clear");pe&&(pe.style.display=ue.value?"":"none"),w()},200)})}const b=document.getElementById("seller-search-clear");b&&b.addEventListener("click",()=>{const ae=document.getElementById("seller-search");ae&&(ae.value=""),k.keyword="",b.style.display="none",w()});const C=document.getElementById("wsclient-modal-close");C&&C.addEventListener("click",z);const T=document.getElementById("wsclient-modal-cancel");T&&T.addEventListener("click",z);const U=document.getElementById("wsclient-modal-save");U&&U.addEventListener("click",q);const N=document.getElementById("wsclient-modal-archive");N&&N.addEventListener("click",F);const d=document.getElementById("wsclient-modal-mask");d&&d.addEventListener("click",ae=>{ae.target===d&&z()});const j=document.getElementById("client-modal-close");j&&j.addEventListener("click",_);const O=document.getElementById("client-modal-cancel");O&&O.addEventListener("click",_);const J=document.getElementById("client-modal-save");J&&J.addEventListener("click",K);const X=document.getElementById("client-modal-delete");X&&X.addEventListener("click",G);const de=document.getElementById("client-modal-mask");de&&de.addEventListener("click",ae=>{ae.target===de&&_()});const se=document.getElementById("client-color-picker");se&&se.addEventListener("click",ae=>{const pe=ae.target.closest(".color-swatch");pe&&(se.querySelectorAll(".color-swatch").forEach(ve=>ve.classList.remove("active")),pe.classList.add("active"))});const ce=document.getElementById("history-client-filter");ce&&ce.addEventListener("change",()=>{a=ce.value,typeof renderHistoryList=="function"&&renderHistoryList()})}),setTimeout(()=>r(),1e3)})();(function(){const e=document.getElementById("page-exceptions");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){let e={statsCache:null,listCache:[],currentRule:null,currentClient:"",currentStatus:"pending",loading:!1,selectedIds:new Set,offset:0,pageSize:50,total:0,loadFailed:!1,listScrollY:0};function n(S,y){let m=t(S)||S;if(y)for(const $ in y)m=m.replace(new RegExp("\\{"+$+"\\}","g"),String(y[$]));return m}async function a(){try{const S=e.currentClient||"",y="/api/exceptions/stats?status=pending"+(S?"&client_id="+encodeURIComponent(S):""),m=await fetch(y,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!m.ok)return;const $=await m.json(),P=document.getElementById("nav-exc-badge");if(!P)return;const Y=parseInt($.pending||0,10);Y>0?(P.textContent=Y>99?"99+":String(Y),P.style.display=""):P.style.display="none"}catch{}}function o(S){return S==="high"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
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
        </svg>`}function u(S){if(S==null)return"—";const y=parseFloat(S);return isNaN(y)?"—":"฿ "+y.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function l(S){return S?S.slice(0,10):"—"}function k(S){document.getElementById("exc-kpi-pending").textContent=S.pending||0,document.getElementById("exc-kpi-high").textContent=S.high_severity||0,document.getElementById("exc-kpi-resolved").textContent=S.resolved||0,document.getElementById("exc-kpi-learned").textContent=S.learned_rules||0;const y=document.getElementById("exc-status-tab-count-pending"),m=document.getElementById("exc-status-tab-count-resolved"),$=document.getElementById("exc-status-tab-count-ignored");y&&(y.textContent=S.pending||0),m&&(m.textContent=S.resolved||0),$&&($.textContent=S.ignored||0),document.querySelectorAll("#exc-status-tabs .exc-status-tab").forEach(Y=>{Y.classList.toggle("active",Y.dataset.status===(e.currentStatus||"pending"))})}function i(S){const y=document.getElementById("exc-chips");if(!y)return;const m=S.by_rule||{},$=["confidence_low","duplicate","amount_missing","math_mismatch","tax_id_format_invalid"];let Y=`<button class="exc-chip ${!e.currentRule?"active":""}" data-rule="">
            <span>${escapeHtml(t("exc-chip-all"))}</span>
            <span class="exc-chip-count">${S.pending||0}</span>
        </button>`;for(const Z of $){const le=m[Z]||0;if(le===0&&e.currentRule!==Z)continue;const ie=e.currentRule===Z;Y+=`<button class="exc-chip ${ie?"active":""}" data-rule="${escapeHtml(Z)}">
                <span>${escapeHtml(t("exc-chip-"+Z))}</span>
                <span class="exc-chip-count">${le}</span>
            </button>`}y.innerHTML=Y,y.querySelectorAll(".exc-chip").forEach(Z=>{Z.addEventListener("click",()=>{const le=Z.dataset.rule||null;e.currentRule=le,x()})})}function p(S){const y=document.getElementById("exc-list");if(!y)return;if(!S||S.length===0){y.innerHTML=`<div class="exc-empty">
                ${s()}
                <div class="exc-empty-title">${escapeHtml(t("exc-empty-title"))}</div>
                <div>${escapeHtml(t("exc-empty-desc"))}</div>
            </div>`,r();return}const m='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7l3 3 5-5"/></svg>',$=(e.currentStatus||"pending")==="pending";y.innerHTML=S.map(P=>{const Y=P.severity||"medium",Z=t("exc-rule-"+P.rule_code)||P.rule_code,le=P.seller_name&&P.seller_name.trim()?P.seller_name:t("exc-no-seller"),ie=P.filename||"—",V=l(P.invoice_date||P.created_at),Q=P.status==="pending",ee=e.selectedIds.has(P.id),ne=$&&Q;return`
                <div class="exc-row sev-${escapeHtml(Y)} ${ee?"selected":""}" data-exc-id="${escapeHtml(String(P.id))}">
                    <div class="exc-row-check ${ee?"checked":""}" data-check-id="${escapeHtml(String(P.id))}" ${ne?"":'style="visibility:hidden;"'}>${m}</div>
                    <div class="exc-row-sev">${o(Y)}</div>
                    <div class="exc-row-main">
                        <div class="exc-row-title">${escapeHtml(le)} · ${escapeHtml(ie)}</div>
                        <div class="exc-row-meta">
                            ${P.invoice_no?`<span><b>${escapeHtml(P.invoice_no)}</b></span>`:""}
                            <span>${escapeHtml(V)}</span>
                        </div>
                    </div>
                    <div class="exc-row-rule r-${escapeHtml(Y)}">${escapeHtml(Z)}</div>
                    <div class="exc-row-amount">${escapeHtml(u(P.total_amount))}</div>
                </div>
            `}).join(""),y.querySelectorAll(".exc-row").forEach(P=>{P.addEventListener("click",Y=>{if(Y.target.closest(".exc-row-check"))return;const Z=P.dataset.excId;Z&&q(parseInt(Z,10))})}),y.querySelectorAll(".exc-row-check").forEach(P=>{P.addEventListener("click",Y=>{Y.stopPropagation();const Z=parseInt(P.dataset.checkId,10);Z&&(e.selectedIds.has(Z)?(e.selectedIds.delete(Z),P.classList.remove("checked"),P.closest(".exc-row").classList.remove("selected")):(e.selectedIds.add(Z),P.classList.add("checked"),P.closest(".exc-row").classList.add("selected")),c())})}),c(),r()}function c(){const S=document.getElementById("exc-batch-bar"),y=document.getElementById("exc-batch-count");if(!S||!y)return;const m=e.selectedIds.size;m===0?S.style.display="none":(S.style.display="",y.textContent=n("exc-batch-count",{n:m}))}function r(){const S=document.getElementById("exc-list-foot"),y=document.getElementById("exc-list-count"),m=document.getElementById("exc-loadmore");if(!S||!y||!m)return;const $=e.listCache.length;if($===0){S.style.display="none";return}S.style.display="";let P=$;const Y=e.statsCache;Y&&(e.currentRule?P=(Y.by_rule||{})[e.currentRule]||$:P=Y.pending||$),e.total=P,y.textContent=n("exc-list-count",{shown:$,total:P});const Z=$<P&&$<500;m.style.display=Z?"":"none"}async function v(){try{if(navigator.onLine===!1)throw new Error("offline");const S=e.currentClient||"",y=e.currentStatus||"pending",m=new URLSearchParams;m.set("status",y),S&&m.set("client_id",S);const $="/api/exceptions/stats?"+m.toString(),P=await fetch($,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!P.ok)throw new Error("http "+P.status);const Y=await P.json();return e.statsCache=Y,k(Y),i(Y),Y}catch(S){return console.warn("loadExceptionsStats fail",S),null}}function E(S){const y=document.getElementById("exc-list");if(!y)return;const m=`<svg class="exc-error-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="18" cy="18" r="14"/>
            <line x1="18" y1="11" x2="18" y2="19"/>
            <circle cx="18" cy="23" r="0.8" fill="currentColor"/>
        </svg>`,$=S?t("exc-offline"):t("exc-error-retry-title"),P=S?"":t("exc-error-retry-desc");y.innerHTML=`
            <div class="exc-error">
                ${m}
                <div class="exc-error-msg">${escapeHtml($)}${P?" · "+escapeHtml(P):""}</div>
                <button class="btn btn-sm btn-secondary" id="exc-retry-btn" type="button">${escapeHtml(t("exc-retry-btn"))}</button>
            </div>`;const Y=document.getElementById("exc-retry-btn");Y&&Y.addEventListener("click",()=>window.loadExceptionsPage&&window.loadExceptionsPage())}async function x(S){S=S||{};const y=!!S.append,m=document.getElementById("exc-list");!y&&m&&e.listCache.length===0&&(m.innerHTML=`<div class="exc-loading">${escapeHtml(t("exc-loading"))}</div>`);const $=new URLSearchParams;$.set("status",e.currentStatus||"pending"),e.currentRule&&$.set("rule_code",e.currentRule),e.currentClient&&$.set("client_id",e.currentClient);const P=y?e.listCache.length:0;$.set("limit",String(e.pageSize)),$.set("offset",String(P));try{if(navigator.onLine===!1)throw new Error("offline");const Y=await fetch("/api/exceptions/list?"+$.toString(),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!Y.ok)throw new Error("http "+Y.status);const le=(await Y.json()).items||[];y?e.listCache=e.listCache.concat(le):(e.listCache=le,e.selectedIds.clear()),e.loadFailed=!1,p(e.listCache),e.statsCache&&i(e.statsCache)}catch(Y){console.warn("loadExceptionsList fail",Y),e.loadFailed=!0;const Z=navigator.onLine===!1||String(Y.message||"").includes("offline");y?showToast(t("exc-toast-load-fail"),"error"):(E(Z),showToast(Z?t("exc-offline"):t("exc-toast-load-fail"),"error"))}}async function R(){if(!e.loading&&!(e.listCache.length>=500)){e.loading=!0;try{await x({append:!0})}finally{e.loading=!1}}}function D(){const S=document.getElementById("exc-client-filter");if(!S)return;const y=window._clientsCache||[],m=e.currentClient||"",$=typeof t=="function"?t("history-client-all"):"全部客户";S.innerHTML=`<option value="">${escapeHtml($)}</option>`+y.map(P=>`<option value="${P.id}">${escapeHtml(P.name)}</option>`).join(""),S.value=m}window.loadExceptionsPage=async function(){if(!e.loading){e.loading=!0;try{D(),typeof window.loadErpExceptions=="function"&&window.loadErpExceptions(),await v(),await x()}finally{e.loading=!1}}},window.refreshExcBadge=a,window._refreshExcClientFilter=D,window._excState=e,window._rerenderExceptions=function(){try{D()}catch{}e.statsCache&&(k(e.statsCache),i(e.statsCache)),e.listCache&&e.listCache.length&&p(e.listCache);try{window._erpExcState&&window._erpExcState.items&&window._erpExcState.items.length&&typeof window._rerenderErpExceptions=="function"&&window._rerenderErpExceptions()}catch{}w.openExcId&&I()};let w={openExcId:null,excRow:null,history:null,loading:!1,pdfUrl:null,pdfStatus:"idle",editing:!1,editFields:null};function B(){if(w.pdfUrl){try{URL.revokeObjectURL(w.pdfUrl)}catch{}w.pdfUrl=null}w.pdfStatus="idle"}async function z(S,y){w.pdfStatus="loading",I();try{const m=await fetch("/api/history/"+encodeURIComponent(S)+"/pdf",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(w.openExcId!==y)return;if(m.status===404){w.pdfStatus="empty",I();return}if(!m.ok)throw new Error("http "+m.status);const $=await m.blob();if(w.openExcId!==y)return;B(),w.pdfUrl=URL.createObjectURL($),w.pdfStatus="ready",I()}catch(m){if(w.openExcId!==y)return;console.warn("loadDrawerPdf fail",m),w.pdfStatus="error",I()}}function q(S){const y=(e.listCache||[]).find(m=>m.id===S);if(!y){showToast(t("exc-drawer-error"),"error");return}e.listScrollY=window.scrollY||document.documentElement.scrollTop||0,B(),w.editing=!1,w.editFields=null,w.openExcId=S,w.excRow=y,w.history=null,document.getElementById("exc-drawer-mask").classList.add("show"),document.getElementById("exc-drawer").classList.add("show"),I(),A(y.history_id),z(y.history_id,S)}function F(){B(),w.editing=!1,w.editFields=null,w.openExcId=null,w.excRow=null,w.history=null,document.getElementById("exc-drawer-mask").classList.remove("show"),document.getElementById("exc-drawer").classList.remove("show");const S=e.listScrollY||0;S>0&&requestAnimationFrame(()=>window.scrollTo(0,S))}async function A(S){try{const y=await fetch("/api/history/"+encodeURIComponent(S),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!y.ok)throw new Error("http "+y.status);w.history=await y.json()}catch(y){console.warn("loadHistoryDetail fail",y),w.history={_err:!0}}w.excRow&&I()}function g(S){if(!S||!S.pages)return{};const y=S.pages,m=y.find($=>!$.is_duplicate&&!$.is_copy)||y[0];return m&&m.fields||{}}function f(S){if(S==null)return"—";const y=typeof S=="number"?S:parseFloat(String(S).replace(/,/g,""));return isNaN(y)?escapeHtml(String(S)):"฿ "+y.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function h(S,y){if(y=y||{},S==="math_mismatch")return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-subtotal"))}</b><span>${escapeHtml(f(y.subtotal))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-vat"))}</b><span>${escapeHtml(f(y.vat))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(f(y.total_expected))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-actual"))}</b><span class="v-bad">${escapeHtml(f(y.total_actual))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-diff"))}</b><span class="v-bad">${escapeHtml(f(y.diff))}</span></div>
            `;if(S==="tax_id_format_invalid")return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-seller-tax"))}</b><span class="v-bad">${escapeHtml(y.tax_id_normalized||y.tax_id_raw||"—")}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-tax-len"))}</b><span class="v-bad">${escapeHtml(String(y.actual_length||"?"))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(t("exc-detail-tax-expected"))}</span></div>
            `;if(S==="duplicate"){const m=y.level==="exact"?t("exc-detail-dup-level-exact"):t("exc-detail-dup-level-likely");return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-dup-match"))}</b><span>${escapeHtml(y.match_filename||"—")}</span></div>
                ${y.match_invoice_no?`<div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-invoice-no"))}</b><span>${escapeHtml(y.match_invoice_no)}</span></div>`:""}
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span>${escapeHtml(m)}</span></div>
            `}return S==="confidence_low"?`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-conf-label"))}</b><span class="v-bad">${escapeHtml(y.confidence||"—")}</span></div>
            `:S==="amount_missing"?`<div class="exc-why-detail-row" style="justify-content:center;color:var(--danger);"><span>${escapeHtml(t("exc-detail-missing"))}</span></div>`:`<div class="exc-why-detail-row"><span style="font-size:11px;">${escapeHtml(JSON.stringify(y))}</span></div>`}function I(){const S=w.excRow;if(!S)return;const y=S.seller_name&&S.seller_name.trim()?S.seller_name:t("exc-no-seller"),m=S.filename||"—";document.getElementById("exc-drawer-title").textContent=m;const $="exc-status-"+(S.status||"pending"),P=t($)||S.status,Y="s-"+(S.status||"pending"),Z=(S.invoice_date||S.created_at||"").slice(0,10);document.getElementById("exc-drawer-sub").innerHTML=`
            <span>${escapeHtml(y)}</span>
            ${S.invoice_no?`<span>· ${escapeHtml(S.invoice_no)}</span>`:""}
            ${Z?`<span>· ${escapeHtml(Z)}</span>`:""}
            <span class="exc-status-chip ${Y}">${escapeHtml(P)}</span>
        `;const le=S.severity||"medium",ie=t("exc-rule-"+S.rule_code)||S.rule_code,V=h(S.rule_code,S.detail||{}),Q=g(w.history),ee=w.history===null,ne=w.history&&w.history._err,oe=new Set;S.rule_code==="math_mismatch"?(oe.add("subtotal"),oe.add("vat"),oe.add("total_amount")):S.rule_code==="tax_id_format_invalid"?oe.add("seller_tax"):S.rule_code==="amount_missing"&&(oe.add("total_amount"),oe.add("invoice_number"));const ue=!!w.editing,b=w.editFields||{},C=(ae,pe,ve)=>{if(ee)return`<div class="exc-field-row"><label>${escapeHtml(t(pe))}</label><span class="val empty">…</span></div>`;const fe=ue?b[ae]!==void 0?b[ae]:Q[ae]!==void 0&&Q[ae]!==null?Q[ae]:"":Q[ae],ge=oe.has(ae)?"flagged":"";if(ue){const De=ve?"number":"text",Le=ve?' step="0.01" inputmode="decimal"':"",Ce=fe==null?"":String(fe).replace(/"/g,"&quot;");return`<div class="exc-field-row ${ge} editing">
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
        `;const N=document.getElementById("exc-fld-edit");N&&N.addEventListener("click",()=>{w.editing=!0,w.editFields={...g(w.history)},I()});const d=document.getElementById("exc-fld-cancel");d&&d.addEventListener("click",()=>{w.editing=!1,w.editFields=null,I()});const j=document.getElementById("exc-fld-save");j&&j.addEventListener("click",()=>L()),document.querySelectorAll(".exc-field-input").forEach(ae=>{ae.addEventListener("input",()=>{w.editFields||(w.editFields={}),w.editFields[ae.dataset.editKey]=ae.value})});const J=document.getElementById("exc-pdf-retry");J&&w.openExcId&&J.addEventListener("click",()=>{w.excRow&&z(w.excRow.history_id,w.openExcId)});const X=S.status==="pending",de=!!(S.seller_name&&S.seller_name.trim()),se=document.getElementById("exc-btn-resolve"),ce=document.getElementById("exc-btn-ignore");se.disabled=!X,ce.disabled=!X||!de,ce.title=de?t("exc-ignore-hint"):t("exc-ignore-no-seller")}async function L(){if(!w.openExcId||!w.history||!w.history.pages||w.loading)return;w.loading=!0;const S=showToast(t("exc-fld-saving"),"loading",0);try{const y=JSON.parse(JSON.stringify(w.history.pages||[]));let m=y.findIndex(ie=>!ie.is_duplicate&&!ie.is_copy);m<0&&(m=0),y[m]||(y[m]={fields:{}});const $=y[m].fields||{},P=w.editFields||{},Y=new Set(["subtotal","vat","total_amount"]),Z={...$};for(const ie in P){let V=P[ie];if((V===""||V===void 0)&&(V=null),Y.has(ie)&&V!==null){const Q=parseFloat(V);V=isNaN(Q)?null:Q}Z[ie]=V}y[m].fields=Z;const le=await fetch("/api/history/"+encodeURIComponent(w.history.id),{method:"PUT",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({pages:y})});if(!le.ok)throw new Error("http "+le.status);S(),showToast(t("exc-fld-save-ok"),"success"),F(),await v(),await x(),a()}catch(y){S(),console.warn("save fields fail",y),showToast(t("exc-fld-save-fail"),"error")}finally{w.loading=!1}}async function H(){if(!(!w.openExcId||w.loading)){w.loading=!0;try{const S=await fetch("/api/exceptions/"+w.openExcId+"/resolve",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!S.ok)throw new Error("http "+S.status);showToast(t("exc-toast-resolved"),"success"),F(),await v(),await x(),a()}catch(S){console.warn("resolve fail",S),showToast(t("exc-toast-action-fail"),"error")}finally{w.loading=!1}}}async function _(){if(!(!w.openExcId||w.loading)){w.loading=!0;try{const S=await fetch("/api/exceptions/"+w.openExcId+"/ignore",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!S.ok)throw new Error("http "+S.status);showToast(t("exc-toast-ignored"),"success"),F(),await v(),await x(),a()}catch(S){console.warn("ignore fail",S),showToast(t("exc-toast-action-fail"),"error")}finally{w.loading=!1}}}let M=!1;async function K(){if(M)return;const S=Array.from(e.selectedIds);if(S.length===0||!await showConfirm(n("exc-batch-confirm-resolve",{n:S.length})))return;M=!0;const m=showToast(n("exc-batch-count",{n:S.length})+" …","loading",0);try{const $=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:S,action:"resolve"})});if(!$.ok)throw new Error("http "+$.status);const P=await $.json();m(),showToast(n("exc-toast-batch-resolved",{n:P.processed||0}),"success"),e.selectedIds.clear(),await v(),await x(),a()}catch($){m(),console.warn("batch resolve fail",$),showToast(t("exc-toast-batch-fail"),"error")}finally{M=!1}}async function G(){if(M)return;const S=Array.from(e.selectedIds);if(S.length===0||!await showConfirm(n("exc-batch-confirm-ignore",{n:S.length}),{danger:!1}))return;M=!0;const m=showToast(n("exc-batch-count",{n:S.length})+" …","loading",0);try{const $=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:S,action:"ignore"})});if(!$.ok)throw new Error("http "+$.status);const P=await $.json();m(),showToast(n("exc-toast-batch-ignored",{n:P.processed||0,wl:P.whitelist_added||0}),"success"),e.selectedIds.clear(),await v(),await x(),a()}catch($){m(),console.warn("batch ignore fail",$),showToast(t("exc-toast-batch-fail"),"error")}finally{M=!1}}function W(){e.selectedIds.clear(),p(e.listCache)}document.addEventListener("click",S=>{S.target.closest("#exc-drawer-close")&&F(),S.target.closest("#exc-drawer-mask")&&F(),S.target.closest("#exc-btn-resolve")&&H(),S.target.closest("#exc-btn-ignore")&&_(),S.target.closest("#exc-batch-resolve")&&K(),S.target.closest("#exc-batch-ignore")&&G(),S.target.closest("#exc-batch-clear")&&W(),S.target.closest("#exc-loadmore")&&R()}),document.addEventListener("keydown",S=>{S.key==="Escape"&&w.openExcId&&F()}),document.addEventListener("click",S=>{S.target.closest("#btn-exc-refresh")&&(typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),a())}),document.addEventListener("change",S=>{if(!S.target.closest("#exc-client-filter"))return;const y=S.target;e.currentClient=y.value||"",e.currentRule=null,e.selectedIds.clear(),e.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),a()}),document.addEventListener("click",S=>{const y=S.target.closest("#exc-status-tabs .exc-status-tab");if(!y)return;const m=y.dataset.status||"pending";m!==e.currentStatus&&(e.currentStatus=m,e.currentRule=null,e.selectedIds.clear(),e.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage())}),window.addEventListener("online",()=>{e.loadFailed&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage&&window.loadExceptionsPage()}),setTimeout(a,1500),setInterval(a,6e4);function te(S){if(!S)return"—";try{const y=new Date(S),m=$=>String($).padStart(2,"0");return`${y.getFullYear()}-${m(y.getMonth()+1)}-${m(y.getDate())} ${m(y.getHours())}:${m(y.getMinutes())}`}catch{return S.slice(0,16).replace("T"," ")}}async function re(){const S=document.getElementById("learned-list");if(S){S.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-loading"))}</div>`;try{const y=await fetch("/api/exception-whitelist",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!y.ok)throw new Error("http "+y.status);const $=(await y.json()).items||[];if($.length===0){S.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-empty"))}</div>`;return}const P=`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 4h8M5.5 4V2.5h3V4M4 4l0.6 8.5h4.8L10 4"/>
            </svg>`;S.innerHTML=$.map(Y=>{const Z=t("exc-rule-"+Y.rule_code)||Y.rule_code;return`
                    <div class="learned-row" data-wl-id="${escapeHtml(String(Y.id))}">
                        <div class="learned-seller" title="${escapeHtml(Y.seller_name)}">${escapeHtml(Y.seller_name)}</div>
                        <div class="learned-rule">${escapeHtml(Z)}</div>
                        <div class="learned-date">${escapeHtml(te(Y.created_at))}</div>
                        <button class="learned-del-btn" data-del-wl="${escapeHtml(String(Y.id))}" title="${escapeHtml(t("set-learned-del"))}" type="button">${P}</button>
                    </div>
                `}).join("")}catch(y){console.warn("loadLearnedRules fail",y),S.innerHTML=`<div class="learned-empty">${escapeHtml(t("exc-toast-load-fail"))}</div>`}}}window.loadLearnedRules=re,document.addEventListener("click",async S=>{const y=S.target.closest("[data-del-wl]");if(!y)return;const m=parseInt(y.dataset.delWl,10);if(!m)return;const $=y.closest(".learned-row"),P=$&&$.querySelector(".learned-seller"),Y=P?P.textContent.trim():"",Z=t("set-learned-del-confirm").replace("{seller}",Y);if(await showConfirm(Z,{danger:!0}))try{const ie=await fetch("/api/exception-whitelist/"+m,{method:"DELETE",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!ie.ok)throw new Error("http "+ie.status);showToast(t("set-learned-del-ok"),"success"),re(),typeof window.loadExceptionsPage=="function"&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage()}catch(ie){console.warn("delete whitelist fail",ie),showToast(t("set-learned-del-fail"),"error")}})})();(function(){let e={items:[],q:"",cat:"",selected:new Set,total:0,categories:{},pageSize:30,loading:!1,focusSearch:!1,searchCaret:0},n=null;function a(){return localStorage.getItem("mrpilot_token")||""}function o(r){const v=typeof currentLang=="string"&&currentLang||window._currentLang||"th",E=r.error_friendly&&r.error_friendly[v];if(E)return E;if(typeof humanizeError=="function"&&r.error_msg)try{return humanizeError(r.error_msg)}catch{}return t("erp-exc-reason-"+(r.category||"other"))}function s(){const r=document.getElementById("erp-exc-batch");if(!r)return;const v=e.selected.size;r.hidden=v===0;const E=r.querySelector(".erp-exc-batch-count");E&&(E.textContent=String(v))}function u(){const r=document.getElementById("erp-exc-block");if(!r)return;const v=e;if(!(v.total>0||!!v.q||!!v.cat)){r.hidden=!0,r.innerHTML="";return}r.hidden=!1;const x=v.categories||{},R=Object.keys(x).reduce((h,I)=>h+x[I],0);let D=`<button class="erp-exc-chip ${v.cat===""?"active":""}" data-erpexc-cat=""><span>${escapeHtml(t("erp-exc-cat-all"))}</span><span class="erp-exc-chip-count">${R}</span></button>`;Object.keys(x).forEach(h=>{D+=`<button class="erp-exc-chip ${v.cat===h?"active":""}" data-erpexc-cat="${escapeHtml(h)}"><span>${escapeHtml(t("erp-exc-cat-"+h))}</span><span class="erp-exc-chip-count">${x[h]}</span></button>`});const w=v.items||[],B=w.length>0&&w.every(h=>v.selected.has(h.id)),z=w.map(h=>{const I=h.state==="needs_action"?"needs":h.state==="retrying"?"retry":"fail",L=t("erp-exc-state-"+(h.state||"failed")),H=o(h),_=v.selected.has(h.id)?"checked":"";return`<div class="erp-exc-row" data-erpexc-id="${escapeHtml(h.id)}">
                <span class="ex-cb"><input type="checkbox" class="erp-exc-cb" data-erpexc-cb="${escapeHtml(h.id)}" ${_}></span>
                <span class="ex-inv" title="${escapeHtml(h.invoice_no||"")}">${escapeHtml(h.invoice_no||"—")}</span>
                <span class="ex-seller" title="${escapeHtml(h.seller_name||"")}">${escapeHtml(h.seller_name||"—")}</span>
                <span class="ex-buyer" title="${escapeHtml(h.ocr_buyer_name||"")}">${escapeHtml(h.ocr_buyer_name||"—")}</span>
                <span class="ex-state"><span class="erp-exc-state ${I}">${escapeHtml(L)}</span></span>
                <span class="ex-reason" title="${escapeHtml(H)}">${escapeHtml(H)}${h.error_code?` <span class="erp-exc-code">${escapeHtml(h.error_code)}</span>`:""}</span>
                <span class="ex-act"><button class="btn btn-sm btn-secondary" type="button" data-erpexc-retry="${escapeHtml(h.id)}">${escapeHtml(t("erp-exc-retry"))}</button></span>
            </div>`}).join(""),q=w.length===0?`<div class="erp-exc-empty">${escapeHtml(t("erp-exc-empty"))}</div>`:"",F=w.length<v.total?`<button class="erp-exc-more" type="button" id="erp-exc-more">${escapeHtml(t("erp-exc-load-more"))} (${w.length}/${v.total})</button>`:v.total>0?`<div class="erp-exc-count">${escapeHtml(t("erp-exc-shown",{n:w.length,total:v.total}))}</div>`:"";r.innerHTML=`
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
            <div class="erp-exc-foot">${F}</div>`;const A=document.getElementById("erp-exc-search");if(A){if(v.focusSearch){A.focus();try{A.setSelectionRange(v.searchCaret,v.searchCaret)}catch{}}A.addEventListener("input",()=>{v.q=A.value,v.focusSearch=!0,v.searchCaret=A.selectionStart||A.value.length,clearTimeout(n),n=setTimeout(()=>i(!1),350)}),A.addEventListener("blur",()=>{v.focusSearch=!1})}r.querySelectorAll(".erp-exc-chip").forEach(h=>{h.addEventListener("click",()=>{v.cat=h.dataset.erpexcCat||"",i(!1)})}),r.querySelectorAll("[data-erpexc-retry]").forEach(h=>{h.addEventListener("click",I=>{I.stopPropagation(),l(h.dataset.erpexcRetry,h)})}),r.querySelectorAll(".erp-exc-cb").forEach(h=>{h.addEventListener("change",()=>{const I=h.dataset.erpexcCb;h.checked?v.selected.add(I):v.selected.delete(I);const L=document.getElementById("erp-exc-cb-all");L&&(L.checked=w.length>0&&w.every(H=>v.selected.has(H.id))),s()})});const g=document.getElementById("erp-exc-cb-all");g&&g.addEventListener("change",()=>{w.forEach(h=>{g.checked?v.selected.add(h.id):v.selected.delete(h.id)}),r.querySelectorAll(".erp-exc-cb").forEach(h=>{h.checked=g.checked}),s()}),r.querySelectorAll("[data-erpexc-batch]").forEach(h=>{h.addEventListener("click",()=>k(h.dataset.erpexcBatch))});const f=document.getElementById("erp-exc-more");f&&f.addEventListener("click",()=>i(!0)),r.querySelectorAll(".erp-exc-row:not(.erp-exc-row-head)").forEach(h=>{h.addEventListener("click",I=>{I.target.closest("input,button")||typeof window._erpExcOpenEdit=="function"&&window._erpExcOpenEdit(h.dataset.erpexcId)})})}async function l(r,v){if(r){v&&(v.disabled=!0,v.textContent=t("erp-exc-retrying"));try{const E=await fetch("/api/erp/logs/"+encodeURIComponent(r)+"/retry",{method:"POST",headers:{Authorization:"Bearer "+a()}}),x=await E.json().catch(()=>({}));showToast(E.ok&&x.ok?t("erp-exc-retry-ok"):t("erp-exc-retry-fail"),E.ok&&x.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.delete(r),i(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function k(r){const v=Array.from(e.selected);if(r==="clear"){e.selected.clear(),u();return}if(v.length!==0){if(r==="delete"){if(!await showConfirm(t("erp-exc-batch-delete-confirm",{n:v.length}),{danger:!0}))return;try{const x=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:v.slice(0,200)})}),R=await x.json().catch(()=>({}));showToast(x.ok?t("erp-exc-batch-delete-ok",{n:R.deleted||0}):t("erp-exc-retry-fail"),x.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}}else if(r==="retry")try{const E=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:v.slice(0,50)})}),x=await E.json().catch(()=>({}));showToast(E.ok?t("erp-exc-batch-retry-ok",{ok:x.succeeded||0,fail:(x.failed||0)+(x.skipped||0)}):t("erp-exc-retry-fail"),E.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.clear(),i(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function i(r){const v=document.getElementById("erp-exc-block");if(!(!v||e.loading)){e.loading=!0;try{const E=new URLSearchParams;e.q&&E.set("q",e.q),e.cat&&E.set("category",e.cat),E.set("limit",String(e.pageSize)),E.set("offset",String(r?e.items.length:0));const x=await fetch("/api/erp/exceptions?"+E.toString(),{headers:{Authorization:"Bearer "+a()}});if(!x.ok){r||(v.hidden=!0);return}const R=await x.json(),D=R.items||[];e.items=r?e.items.concat(D):D,e.total=R.total||0,e.categories=R.categories||{},u()}catch{r||(v.hidden=!0)}finally{e.loading=!1}}}let p={};function c(){const r=document.getElementById("erp-exc-modal");r&&r.remove()}window._erpExcOpenEdit=function(r){const v=(e.items||[]).find(q=>String(q.id)===String(r));if(!v)return;const E=!!v.history_client_id&&v.category==="customer_mismatch",x=v.category==="product_mismatch"&&!!v.history_id&&!!v.endpoint_id,R=o(v),D=v.state==="needs_action"?"needs":v.state==="retrying"?"retry":"fail",w=(q,F)=>`<div class="erp-exc-m-row"><span class="erp-exc-m-k">${escapeHtml(q)}</span><span class="erp-exc-m-v">${escapeHtml(F||"—")}</span></div>`;let B="";if(E)B=`
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
            </div>`,document.body.appendChild(z),z.addEventListener("click",q=>{q.target===z&&c()}),document.getElementById("erp-exc-m-close").addEventListener("click",c),document.getElementById("erp-exc-m-cancel").addEventListener("click",c),document.getElementById("erp-exc-m-retry").addEventListener("click",()=>{c(),l(v.id,null)}),E){let q="";const F=document.getElementById("erp-exc-m-bind"),A=document.getElementById("erp-exc-m-custlist"),g=document.getElementById("erp-exc-m-search"),f=(I,L)=>{const H=(L||"").trim().toLowerCase(),_=H?I.filter(M=>(M.code||"").toLowerCase().includes(H)||(M.name||"").toLowerCase().includes(H)):I;if(_.length===0){A.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-empty"))}</div>`;return}A.innerHTML=_.slice(0,100).map(M=>`<div class="erp-exc-m-cust" data-cust-code="${escapeHtml(M.code||"")}">
                        <span class="erp-exc-m-cust-name">${escapeHtml(M.name||"")}</span>
                        <span class="erp-exc-m-cust-code">${escapeHtml(M.code||"")}</span>
                    </div>`).join(""),A.querySelectorAll(".erp-exc-m-cust").forEach(M=>{M.addEventListener("click",()=>{q=M.dataset.custCode||"",A.querySelectorAll(".erp-exc-m-cust").forEach(K=>K.classList.remove("sel")),M.classList.add("sel"),F&&(F.disabled=!q)})})},h=async()=>{const I=v.endpoint_id;if(p[I]){f(p[I],"");return}try{const L=await fetch("/api/erp/endpoints/"+encodeURIComponent(I)+"/customers",{headers:{Authorization:"Bearer "+a()}}),H=await L.json().catch(()=>({}));if(!L.ok||!H.ok){A.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`;return}const _=H.customers||[];p[I]=_,f(_,"")}catch{A.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`}};g&&g.addEventListener("input",()=>f(p[v.endpoint_id]||[],g.value)),h(),F&&F.addEventListener("click",async()=>{if(q){F.disabled=!0,F.textContent=t("erp-exc-retrying");try{if(!(await fetch("/api/erp/mappings/clients",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({client_id:v.history_client_id,erp_type:v.endpoint_adapter,erp_code:q})})).ok){showToast(t("erp-exc-retry-fail"),"error"),F.disabled=!1,F.textContent=t("erp-exc-edit-bind-retry");return}showToast(t("erp-exc-edit-bound-ok"),"success"),c(),await l(v.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),F.disabled=!1,F.textContent=t("erp-exc-edit-bind-retry")}}})}if(x){const q=document.getElementById("erp-exc-m-bind-prod"),F=document.getElementById("erp-exc-m-prodlist"),A={};let g=[];const f=()=>'<option value="">'+escapeHtml(t("erp-exc-edit-prod-choose"))+"</option>"+g.slice(0,500).map(L=>`<option value="${escapeHtml(L.code||"")}" data-pname="${escapeHtml(L.name||"")}">`+escapeHtml((L.name||"")+" · "+(L.code||""))+"</option>").join(""),h=L=>{if(!L.length){F.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-noitems"))}</div>`;return}F.innerHTML=L.map(H=>`<div class="erp-exc-m-cust" style="cursor:default">
                        <span class="erp-exc-m-cust-name" title="${escapeHtml(H)}">${escapeHtml(H)}</span>
                        <select class="erp-exc-m-prod-sel" data-item="${escapeHtml(H)}" style="max-width:55%;flex:0 0 auto;padding:4px 6px;border:1px solid var(--border,#e5e7eb);border-radius:6px;font-size:12px">${f()}</select>
                    </div>`).join(""),F.querySelectorAll(".erp-exc-m-prod-sel").forEach(H=>{H.addEventListener("change",()=>{const _=H.dataset.item,M=H.options[H.selectedIndex];H.value?A[_]={code:H.value,name:M&&M.dataset.pname||""}:delete A[_],q&&(q.disabled=Object.keys(A).length===0)})})};(async()=>{try{const H=await(await fetch("/api/history/"+encodeURIComponent(v.history_id),{headers:{Authorization:"Bearer "+a()}})).json().catch(()=>({})),_=H&&H.pages||[],M=[],K={};(Array.isArray(_)?_:[]).forEach(te=>{const re=te&&te.fields&&te.fields.items||[];(Array.isArray(re)?re:[]).forEach(S=>{const y=(S&&(S.name||S.description)||"").trim();y&&!K[y]&&(K[y]=1,M.push(y))})});const G=await fetch("/api/erp/endpoints/"+encodeURIComponent(v.endpoint_id)+"/products",{headers:{Authorization:"Bearer "+a()}}),W=await G.json().catch(()=>({}));if(!G.ok||!W.ok){F.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`;return}g=W.products||[],h(M)}catch{F.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`}})(),q&&q.addEventListener("click",async()=>{const L=Object.entries(A);if(L.length){q.disabled=!0,q.textContent=t("erp-exc-retrying");try{for(const[H,_]of L)if(!(await fetch("/api/erp/mappings/products",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({erp_type:v.endpoint_adapter,item_name:H,erp_code:_.code,erp_name:_.name})})).ok){showToast(t("erp-exc-retry-fail"),"error"),q.disabled=!1,q.textContent=t("erp-exc-edit-bind-prod-retry");return}showToast(t("erp-exc-edit-prod-bound-ok"),"success"),c(),await l(v.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),q.disabled=!1,q.textContent=t("erp-exc-edit-bind-prod-retry")}}})}},window._rerenderErpExceptions=u,window.loadErpExceptions=i,window._erpExcState=e})();(function(){function e(r){try{if(location.search.indexOf("test_center=1")>=0||localStorage.getItem("pearnly_test_mode")==="1"||r&&r.id&&String(r.id)==="468b50c1-5593-4fd6-990d-515ce8085563")return!0}catch{}return!1}window.applyRoleVisibility=function(){var v=window._userInfo,E=!1,x=!0,R=!1,D=!1;v&&(E=typeof canManageTeam=="function"?canManageTeam(v):!!(v.role==="owner"||v.is_super_admin),x=typeof shouldHideMoney=="function"?shouldHideMoney(v):v.role==="member"&&!v.is_super_admin,R=typeof isSuperAdmin=="function"?isSuperAdmin(v):!!v.is_super_admin,D=e(v)),document.querySelectorAll("[data-show-if-team]").forEach(function(B){B.style.display=E?"":"none"}),document.querySelectorAll("[data-show-if-money]").forEach(function(B){B.style.display=x?"none":""}),document.querySelectorAll("[data-show-if-admin]").forEach(function(B){B.style.display=R?"":"none"}),document.querySelectorAll("[data-show-if-test]").forEach(function(B){B.style.display=D?"":"none"});var w=R||D;document.querySelectorAll("[data-show-if-special]").forEach(function(B){B.style.display=w?"":"none"})},window.renderAvatarMenu=function(v){if(v){var E=document.getElementById("avatar-btn"),x=document.getElementById("avatar-popup-name"),R=document.getElementById("avatar-popup-email");if(!(!E||!x||!R)){var D=(v.username||"").trim(),w=D.split("@")[0]||D||"—",B=(D.charAt(0)||"?").toUpperCase(),z=(v.avatar_url||"").trim();if(z){var q=z.replace(/"/g,"&quot;"),F=B.replace(/'/g,"\\'");E.innerHTML='<img src="'+q+'" alt="'+B+`" referrerpolicy="no-referrer" onerror="this.parentNode.textContent='`+F+`'">`}else E.textContent=B;x.textContent=w,R.textContent=D||"—",E.setAttribute("title",D||"")}}};function n(){var r=document.getElementById("avatar-wrap"),v=document.getElementById("avatar-btn"),E=document.getElementById("avatar-popup");if(!r||!v||!E)return;function x(){E.classList.remove("show"),v.setAttribute("aria-expanded","false")}function R(){E.classList.add("show"),v.setAttribute("aria-expanded","true")}v.addEventListener("click",function(D){D.stopPropagation(),E.classList.contains("show")?x():R()}),document.addEventListener("click",function(D){E.classList.contains("show")&&!r.contains(D.target)&&x()}),E.addEventListener("click",function(D){var w=D.target.closest(".avatar-popup-item");if(w){var B=w.dataset.action;switch(x(),B){case"settings":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings");break;case"team":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("team")},50);break;case"billing":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("plan")},50);break;case"shortcuts":if(typeof showToast=="function"){var z=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(z||"即将上线","info")}break;case"admin":window.location.href="/admin/cost";break;case"test-center":typeof routeTo=="function"&&routeTo("test-center");break;case"help":var q=document.getElementById("help-modal");q&&(q.style.display="flex");break;case"logout":try{localStorage.removeItem("mrpilot_token")}catch{}try{localStorage.removeItem("mrpilot_user")}catch{}window.location.href="/";break}}}),window._closeAvatarPopup=x}function a(){return[].slice.call(document.querySelectorAll(".cmdk-item")).filter(function(r){return r.style.display!=="none"})}function o(r){var v=a();v.forEach(function(E){E.classList.remove("focus")}),v[r]&&(v[r].classList.add("focus"),v[r].scrollIntoView({block:"nearest"}))}function s(r){var v=a();if(v.length){var E=v.findIndex(function(R){return R.classList.contains("focus")});E<0&&(E=0);var x=(E+r+v.length)%v.length;o(x)}}function u(r){r=(r||"").toLowerCase().trim();var v=0,E=window._userInfo,x=typeof isSuperAdmin=="function"?isSuperAdmin(E):!!(E&&E.is_super_admin),R=e(E);document.querySelectorAll(".cmdk-item").forEach(function(w){if(w.dataset.showIfAdmin==="1"&&!x){w.style.display="none";return}if(w.dataset.showIfTest==="1"&&!R){w.style.display="none";return}var B=(w.dataset.cmdkText||w.textContent||"").toLowerCase(),z=!r||B.indexOf(r)>=0;w.style.display=z?"":"none",w.classList.remove("focus"),z&&v++}),document.querySelectorAll("[data-cmdk-section]").forEach(function(w){for(var B=w.nextElementSibling,z=!1;B&&!B.hasAttribute("data-cmdk-section");){if(B.classList&&B.classList.contains("cmdk-item")&&B.style.display!=="none"){z=!0;break}B=B.nextElementSibling}w.style.display=z?"":"none"});var D=document.getElementById("cmdk-empty");D&&(D.style.display=v===0?"flex":"none"),o(0)}window.openCmdk=function(){var v=document.getElementById("cmdk-mask");v&&(typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup(),v.classList.add("show"),typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility(),setTimeout(function(){var E=document.getElementById("cmdk-input");E&&(E.value="",u(""),E.focus(),o(0))},50))},window.closeCmdk=function(){var v=document.getElementById("cmdk-mask");v&&v.classList.remove("show")};function l(r){if(r){if(r.classList.contains("cmdk-item-locked")){if(typeof showToast=="function"){var v=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(v||"即将上线","info")}return}var E=r.dataset.cmdkRoute,x=r.dataset.cmdkAction;if(window.closeCmdk(),E){typeof routeTo=="function"&&routeTo(E);return}if(x){if(x==="open-admin"){window.location.href="/admin/cost";return}if(x.indexOf("lang-")===0){var R=x.slice(5);typeof applyLang=="function"&&applyLang(R)}}}}function k(){var r=document.getElementById("cmdk-mask"),v=document.getElementById("cmdk-input"),E=document.getElementById("cmdk-body");if(!(!r||!v||!E)){r.addEventListener("click",function(D){D.target===r&&window.closeCmdk()});var x=document.getElementById("cmdk-esc-btn");x&&x.addEventListener("click",function(){window.closeCmdk()}),v.addEventListener("input",function(D){u(D.target.value)}),v.addEventListener("keydown",function(D){D.key==="ArrowDown"?(D.preventDefault(),s(1)):D.key==="ArrowUp"?(D.preventDefault(),s(-1)):D.key==="Enter"?(D.preventDefault(),l(r.querySelector(".cmdk-item.focus"))):D.key==="Escape"&&(D.preventDefault(),window.closeCmdk())}),E.addEventListener("click",function(D){var w=D.target.closest(".cmdk-item");w&&l(w)}),E.addEventListener("mousemove",function(D){var w=D.target.closest(".cmdk-item");!w||w.style.display==="none"||w.classList.contains("cmdk-item-locked")||(a().forEach(function(B){B.classList.remove("focus")}),w.classList.add("focus"))});var R=document.getElementById("topbar-search");R&&(R.addEventListener("click",function(){window.openCmdk()}),R.addEventListener("keydown",function(D){(D.key==="Enter"||D.key===" ")&&(D.preventDefault(),window.openCmdk())}))}}document.addEventListener("keydown",function(r){if((r.metaKey||r.ctrlKey)&&(r.key==="k"||r.key==="K")){r.preventDefault(),window.openCmdk();return}if(r.key==="Escape"){var v=document.getElementById("cmdk-mask");if(v&&v.classList.contains("show")){window.closeCmdk();return}var E=document.getElementById("avatar-popup");E&&E.classList.contains("show")&&typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup()}});try{var i=(navigator.userAgent||"").toLowerCase(),p=i.indexOf("mac")>=0||i.indexOf("iphone")>=0||i.indexOf("ipad")>=0;p||document.body.classList.add("is-windows")}catch{}function c(){n(),k(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("nav-ia-phase1-role",function(){try{typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",c):c()})();(function(){function n(x){return String(x??"").replace(/[&<>"']/g,function(R){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[R]})}function a(x){if(!x||isNaN(x))return"";var R=Number(x);return R<1024?R+" B":R<1024*1024?(R/1024).toFixed(1)+" KB":(R/1024/1024).toFixed(1)+" MB"}document.addEventListener("click",function(x){var R=x.target.closest&&x.target.closest(".recon-collapse-head");if(R&&!(x.target.closest("button")||x.target.closest("a"))){var D=R.closest(".recon-collapse");if(D){var w=D.getAttribute("data-collapsed")==="true";D.setAttribute("data-collapsed",w?"false":"true"),w&&(D.id==="vex-summary-collapse"&&c(),D.id==="vex-detail-collapse"&&r())}}}),document.addEventListener("keydown",function(x){if(!(x.key!=="Enter"&&x.key!==" ")){var R=x.target.closest&&x.target.closest(".recon-collapse-head");R&&(x.preventDefault(),R.click())}});var o={vat:"",gl:""};window._glvClearPreviewSearch=function(){o.vat="",o.gl=""};var s='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',u='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function l(){i("vat"),i("gl")}function k(x){try{if(typeof window._glvPreviewFiles=="function")return window._glvPreviewFiles(x)||[]}catch{}var R=document.getElementById(x==="vat"?"glv-vat-input":"glv-gl-input");return R&&R.files?Array.from(R.files):[]}function i(x){var R=document.getElementById(x==="vat"?"glv-pp-vat-col":"glv-pp-gl-col");if(R){var D=k(x),w=x==="vat"?"glv-up-vat-title":"glv-up-gl-title",B=x==="vat"?"① 销项税报告":"② 总账 GL",z=window.t&&window.t(w)||B,q=n(window.t&&window.t("vex-preview-search")||"搜索文件名..."),F=n(window.t&&window.t("vex-preview-clear-all")||"全清"),A=o[x]||"",g=D.length;R.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+n(z)+' <span class="vex-pp-col-count">'+g+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="glv-pp-search-'+x+'" type="text" placeholder="'+q+'" value="'+n(A)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="glv-pp-clearall-'+x+'" type="button">'+F+'</button></div><div class="vex-pp-file-list" id="glv-pp-'+x+'-list"></div><div class="vex-pp-pagination" id="glv-pp-'+x+'-pg"></div>';var f=document.getElementById("glv-pp-search-"+x);f&&f.addEventListener("input",function(I){o[x]=I.target.value,p(x)});var h=document.getElementById("glv-pp-clearall-"+x);h&&h.addEventListener("click",function(){window._glvRemoveFile&&window._glvRemoveFile(x)}),p(x)}}function p(x){var R=document.getElementById("glv-pp-"+x+"-list"),D=document.getElementById("glv-pp-"+x+"-pg");if(R){var w=k(x),B=(o[x]||"").toLowerCase(),z=w.map(function(A,g){return{f:A,i:g}}),q=B?z.filter(function(A){return A.f.name.toLowerCase().indexOf(B)>=0}):z;if(R.innerHTML=q.map(function(A){var g=A.f;return'<div class="vex-pp-file-row">'+s+'<span class="vex-pp-fi-name" title="'+n(g.name)+'">'+n(g.name)+'</span><span class="vex-pp-fi-size">'+a(g.size)+'</span><button class="vex-pp-fi-del" type="button" data-kind="'+x+'" data-idx="'+A.i+'" aria-label="remove">'+u+"</button></div>"}).join(""),R.querySelectorAll(".vex-pp-fi-del").forEach(function(A){A.addEventListener("click",function(){var g=A.dataset.kind,f=parseInt(A.dataset.idx,10);window._glvRemoveFile&&window._glvRemoveFile(g,isNaN(f)?null:f)})}),D){var F=window.t&&window.t("vex-preview-count")||"显示前 {n} / 共 {m}";D.textContent=F.replace("{n}",q.length).replace("{m}",q.length)}}}function c(){var x=function(D,w){var B=document.getElementById(D);B&&(B.textContent=w==null?"—":String(w))},R=window._vexLastTask||{};x("vex-sum-total",R.total),x("vex-sum-matched",R.matched),x("vex-sum-diff",R.diff),x("vex-sum-incomplete",R.incomplete),x("vex-sum-cash",R.cash),document.getElementById("vex-summary-sub")}function r(){var x=window._vexLastTask&&window._vexLastTask.diff_rows||[],R=document.getElementById("vex-detail-tbody"),D=document.getElementById("vex-detail-table"),w=document.getElementById("vex-detail-empty");if(!(!R||!D||!w)){if(x.length===0){D.style.display="none",w.style.display="";return}w.style.display="none",D.style.display="";var B=x.map(function(q){return'<tr><td class="recon-detail-cell-mono">'+n(q.invoice_no||"")+"</td><td>"+n(q.field||"")+"</td><td>"+n(q.report_value||"")+"</td><td>"+n(q.invoice_value||"")+"</td><td>"+n(q.kind||"")+"</td></tr>"}).join("");R.innerHTML=B;var z=document.getElementById("vex-detail-sub");z&&(z.textContent=String(x.length))}}function v(){var x=document.getElementById("glv-toggle-preview");x&&!x._reconBound&&(x._reconBound=!0,x.addEventListener("click",function(){var R=document.getElementById("glv-preview-panel"),D=document.getElementById("glv-toggle-preview-label"),w=R&&R.style.display!=="none";R&&(R.style.display=w?"none":""),x.classList.toggle("open",!w),D&&(D.textContent=w?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),w||l()})),["glv-vat-input","glv-gl-input"].forEach(function(R){var D=document.getElementById(R);!D||D._reconWatched||(D._reconWatched=!0,D.addEventListener("change",function(){var w=document.getElementById("glv-preview-panel");w&&w.style.display!=="none"&&l()}))})}function E(){var x=document.getElementById("vex-summary-collapse"),R=document.getElementById("vex-detail-collapse");x&&(x.style.display=""),R&&(R.style.display=""),c(),r()}window._fillVexSummary=c,window._fillVexDetail=r,window._onVexResultShown=E,document.addEventListener("DOMContentLoaded",function(){v()}),setTimeout(v,1500),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-collapse",function(){var x=document.getElementById("glv-preview-panel");x&&x.style.display!=="none"&&l();var R=document.getElementById("glv-toggle-preview-label"),D=document.getElementById("glv-toggle-preview");R&&D&&(R.textContent=D.classList.contains("open")?window.t&&window.t("vex-toggle-preview-close")||"收起清单":window.t&&window.t("vex-toggle-preview-open")||"查看清单")}),window._reconCollapse={renderGlvPreview:l,fillVexSummary:c,fillVexDetail:r}})();(function(){function e(u){}function n(){const u=document.querySelectorAll("[data-recon-tab]");u.forEach(k=>{k.addEventListener("click",()=>{u.forEach(v=>v.classList.remove("active")),k.classList.add("active");const i=k.dataset.reconTab,p=document.getElementById("recon-pane-bank"),c=document.getElementById("recon-pane-sale-vat"),r=document.getElementById("recon-pane-gl-vat");p&&(p.style.display=i==="bank"?"":"none"),c&&(c.style.display=i==="sale-vat"?"":"none"),r&&(r.style.display=i==="gl-vat"?"":"none"),i==="gl-vat"&&window.GlVatRecon&&window.GlVatRecon.ensureInit(),i==="bank"&&typeof window._bankReconV2Init=="function"&&window._bankReconV2Init()})});const l=document.querySelector("[data-recon-tab].active");l&&(l.dataset.reconTab,void 0)}function a(){const u=document.getElementById("page-settings");if(!u)return null;let l=document.getElementById("settings-modal-overlay");if(l)return l;l=document.createElement("div"),l.id="settings-modal-overlay",l.className="settings-modal-overlay",l.style.display="none",u.parentElement.insertBefore(l,u),l.appendChild(u);const k=document.createElement("button");return k.id="settings-modal-close",k.className="settings-modal-close",k.setAttribute("aria-label","close"),k.innerHTML='<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 5l10 10M15 5L5 15"/></svg>',u.insertBefore(k,u.firstChild),k.addEventListener("click",s),l.addEventListener("click",i=>{i.target===l&&s()}),l}function o(){const u=a();if(!u)return;u.style.display="flex",document.body.classList.add("settings-modal-open");const l=document.getElementById("page-settings");l&&(l.style.display="block"),setTimeout(()=>{try{typeof renderSettings=="function"&&renderSettings()}catch(i){console.warn("renderSettings:",i)}let k=document.querySelector(".settings-tab.active")||document.querySelector('.settings-tab[data-tab="profile"]');k&&k.click()},50)}function s(){const u=document.getElementById("settings-modal-overlay");u&&(u.style.display="none"),document.body.classList.remove("settings-modal-open")}window.openSettingsModal=o,window.closeSettingsModal=s,document.addEventListener("keydown",u=>{if(u.key==="Escape"){const l=document.getElementById("settings-modal-overlay");l&&l.style.display==="flex"&&s()}}),window.addEventListener("hashchange",()=>{location.hash==="#/settings"&&o()}),window.addEventListener("DOMContentLoaded",()=>{location.hash==="#/settings"&&o()}),document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){const a=/\.(pdf|jpe?g|png|webp|tiff?|xlsx?|xlsm|csv|tsv|docx?)$/i,o=V=>document.getElementById(V);function s(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}function u(V){return String(V??"").replace(/[&<>"']/g,Q=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[Q])}function l(V){return V<1024?V+" B":V<1024*1024?(V/1024).toFixed(1)+" KB":(V/1024/1024).toFixed(1)+" MB"}let k=[],i=[],p=!1,c=[],r=50,v=50,E="",x="";async function R(){try{const V=await fetch("/api/vat_excel/tasks?page=1&page_size=1",{headers:s()});if(!V.ok)return;const ee=(await V.json()).kpi||{};[["vex-kpi-month-val",ee.this_month],["vex-kpi-running-val",ee.running],["vex-kpi-done-val",ee.done],["vex-kpi-failed-val",ee.failed]].forEach(([ne,oe])=>{const ue=document.getElementById(ne);ue&&(ue.textContent=oe??0)})}catch{}}async function D(){try{const V=await fetch("/api/vat_excel/tasks?page=1&page_size=100",{headers:s()});if(!V.ok)return;const Q=await V.json();q(Q.rows||[])}catch{}}const w=10;var B=1;function z(){var V=((document.getElementById("vex-task-search")||{}).value||"").trim().toLowerCase();if(B=1,q(c),!!V){var Q=document.getElementById("vex-task-tbody");Q&&Q.querySelectorAll("tr").forEach(function(ee){ee.dataset.taskId&&(ee.style.display=ee.textContent.toLowerCase().indexOf(V)>=0?"":"none")})}}function q(V){c=V||c;const Q=document.getElementById("vex-task-tbody");if(!Q)return;if(!c.length){Q.innerHTML='<tr><td colspan="9" class="vex-task-empty">'+(t("sv-empty-title")||"还没有对账任务")+"</td></tr>",F(0);return}const ee=Math.ceil(c.length/w);B>ee&&(B=ee);const ne=(B-1)*w;A(c.slice(ne,ne+w)),F(c.length)}function F(V){const Q=document.getElementById("vex-task-pager"),ee=document.getElementById("vex-task-pager-info"),ne=document.getElementById("vex-task-prev"),oe=document.getElementById("vex-task-next");if(!Q)return;if(V<=w){Q.style.display="none";return}Q.style.display="";const ue=Math.ceil(V/w);ee&&(ee.textContent=B+" / "+ue),ne&&(ne.disabled=B<=1),oe&&(oe.disabled=B>=ue)}function A(V){const Q=document.getElementById("vex-task-tbody");if(!Q)return;const ee={pending:t("vex-status-pending")||"待处理",running:t("vex-status-running")||"处理中",done:t("vex-status-done")||"已完成",failed:t("vex-status-failed")||"失败"},ne={pending:"badge-gray",running:"badge-blue",done:"badge-green",failed:"badge-red"},oe='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',ue='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h10M6 4V3h4v1M5 4v8a1 1 0 001 1h4a1 1 0 001-1V4"/></svg>';Q.innerHTML=V.map(b=>{const C=b.created_at?new Date(b.created_at).toLocaleString([],{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}):"—",T=b.period||"—",U=b.matched_count!=null?b.matched_count+" ✓ · "+b.mismatched_count+" ⚠":"—",N=b.mismatch_amount!=null?"฿ "+Number(b.mismatch_amount).toLocaleString():"—",d=b.elapsed_seconds!=null?b.elapsed_seconds.toFixed(1)+" s":"—",j=b.status||"pending",O=b.client_name&&b.client_name!=="client"?b.client_name:t("vex-client-all")||"全部客户";return`<tr class="vex-task-row" data-task-id="${u(b.id)}" style="cursor:pointer">
                <td>${C}</td>
                <td>${u(O)}</td>
                <td>${u(T)}</td>
                <td>${(b.invoice_count||0)+" / "+(b.report_count||0)}</td>
                <td>${U}</td>
                <td>${N}</td>
                <td><span class="badge ${ne[j]||"badge-gray"}">${ee[j]||j}</span></td>
                <td>${d}</td>
                <td><div class="vex-task-actions">
                    <button class="vex-task-dl-btn" data-task-id="${u(b.id)}" title="${t("hist_export")||"导出"}">${oe}</button>
                    <button class="vex-task-del-btn" data-task-id="${u(b.id)}" title="${t("vex-task-delete-confirm-title")||"删除"}">${ue}</button>
                </div></td>
            </tr>`}).join(""),Q.querySelectorAll(".vex-task-dl-btn").forEach(b=>{b.addEventListener("click",async C=>{C.stopPropagation();const T=b.dataset.taskId;try{const U=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(T)+"/download",{credentials:"include",headers:s()});if(U.status===410){showToast(t("vex-toast-expired")||"数据已过期 · 请重新对账","warn");return}if(!U.ok){showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error");return}const N=await U.blob(),j=(U.headers.get("Content-Disposition")||"").match(/filename\*?=(?:UTF-8''|")?([^";]+)/i),O=j?decodeURIComponent(j[1]):"vat_recon_"+T+".xlsx",J=URL.createObjectURL(N),X=document.createElement("a");X.href=J,X.download=O,X.click(),setTimeout(()=>URL.revokeObjectURL(J),1e3)}catch{showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error")}})}),Q.querySelectorAll(".vex-task-del-btn").forEach(b=>{b.addEventListener("click",C=>{C.stopPropagation(),f(b.dataset.taskId)})}),z()}function g(){var V=document.getElementById("vex-task-prev"),Q=document.getElementById("vex-task-next");V&&!V._vexBound&&(V._vexBound=!0,V.addEventListener("click",function(){B>1&&(B--,q())})),Q&&!Q._vexBound&&(Q._vexBound=!0,Q.addEventListener("click",function(){var ee=Math.ceil(c.length/w);B<ee&&(B++,q())}))}async function f(V){const Q=t("vex-task-delete-confirm-title")||"删除对账任务?",ee=t("vex-task-delete-confirm-body")||"同时清掉对应的发票识别缓存 · 不可恢复";if(await showConfirm(ee,{title:Q,danger:!0,okText:t("vex-task-delete-confirm-title")||"确认删除"}))try{const oe=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(V),{method:"DELETE",credentials:"include",headers:s()});if(!oe.ok)throw new Error(oe.status);showToast(t("vex-task-delete-ok")||"已删除","success"),D(),R()}catch{showToast(t("vex-task-delete-fail")||"删除失败","error")}}function h(V){const Q=window._currentLang||"th",ee={zh:`已忽略 ${V} 个不支持的文件 · 仅支持 PDF / 图片 / Excel / CSV / Word`,th:`ข้ามไฟล์ที่ไม่รองรับ ${V} ไฟล์ · รองรับเฉพาะ PDF / รูปภาพ / Excel / CSV / Word`,en:`Ignored ${V} unsupported file(s) · only PDF / image / Excel / CSV / Word are supported`,ja:`非対応ファイル ${V} 件をスキップ · 対応形式は PDF / 画像 / Excel / CSV / Word のみ`};showToast(ee[Q]||ee.th,"warn")}function I(V){const Q=new Set(k.map(ne=>ne.name+"|"+ne.size));let ee=0;for(const ne of V){if(!a.test(ne.name)){ee++;continue}const oe=ne.name+"|"+ne.size;if(!Q.has(oe)&&(Q.add(oe),k.push(ne),k.length>=1e3))break}ee>0&&h(ee),k.length>1e3&&(k=k.slice(0,1e3),showToast(t("vex-toast-cap-inv"),"warn")),M()}function L(V){const Q=new Set(i.map(ne=>ne.name+"|"+ne.size));let ee=0;for(const ne of V){if(!a.test(ne.name)){ee++;continue}const oe=ne.name+"|"+ne.size;if(!Q.has(oe)&&(Q.add(oe),i.push(ne),i.length>=30))break}ee>0&&h(ee),i.length>30&&(i=i.slice(0,30),showToast(t("vex-toast-cap-rep"),"warn")),M()}function H(V){k.splice(V,1),M()}function _(V){i.splice(V,1),M()}function M(){const V=o("vex-list-invoice"),Q=o("vex-list-report"),ee=o("vex-count-invoice"),ne=o("vex-count-report");ee&&(ee.textContent=k.length),ne&&(ne.textContent=i.length);const oe=(C,T,U)=>`<div class="vex-fi">
            <svg class="vex-fi-ic" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2h6l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M10 2v4h4"/></svg>
            <span class="vex-fi-n" title="${u(C.name)}">${u(C.name)}</span>
            <span class="vex-fi-s">${l(C.size)}</span>
            <button class="vex-fi-x" type="button" data-vex-kind="${U}" data-vex-idx="${T}" aria-label="remove">×</button>
        </div>`;V&&(V.innerHTML=k.map((C,T)=>oe(C,T,"inv")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),Q&&(Q.innerHTML=i.map((C,T)=>oe(C,T,"rep")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),document.querySelectorAll(".vex-fi-x").forEach(C=>{C.addEventListener("click",T=>{const U=C.dataset.vexKind,N=parseInt(C.dataset.vexIdx,10);U==="inv"?H(N):_(N)})});const ue=k.length>0&&i.length>0;o("vex-build").disabled=!ue||p;const b=o("vex-action-info");b&&(!k.length||!i.length?(b.textContent=t("vex-need-both")||"需要至少 1 张发票 + 1 份 VAT 报告",b.className="vex-action-info muted"):(b.textContent=(t("vex-ready")||"已就绪 · {a} 张发票 · {b} 份报告").replace("{a}",k.length).replace("{b}",i.length),b.className="vex-action-info ok")),te()}const K='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>',G='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',W='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function te(){const V=o("vex-preview-panel");if(!V||V.style.display==="none")return;re("inv"),re("rep");const Q=o("vex-pp-guide");Q&&(Q.style.display=k.length>100?"flex":"none")}function re(V){const Q=o(V==="inv"?"vex-pp-invoice-col":"vex-pp-report-col");if(!Q)return;const ee=V==="inv"?k:i,ne=V==="inv"?E:x,oe=t(V==="inv"?"vex-preview-invoice":"vex-preview-report")||(V==="inv"?"销售发票":"VAT 报告"),ue=u(t("vex-preview-search")||"搜索文件名..."),b=u(t("vex-preview-clear-all")||"全清");Q.innerHTML=`
            <div class="vex-pp-col-title">
                <span class="vex-pp-col-name">${u(oe)} <span class="vex-pp-col-count">${ee.length}</span></span>
            </div>
            <div class="vex-pp-search-row">
                <input class="vex-pp-search" id="vex-pp-search-${V}" type="text"
                       placeholder="${ue}" value="${u(ne)}" autocomplete="off">
                <button class="vex-pp-clear-btn" id="vex-pp-clearall-${V}" type="button">${b}</button>
            </div>
            <div class="vex-pp-file-list" id="vex-pp-${V}-list"></div>
            <div class="vex-pp-pagination" id="vex-pp-${V}-pg"></div>`;const C=o("vex-pp-search-"+V);C&&C.addEventListener("input",U=>{V==="inv"?(E=U.target.value,r=50):(x=U.target.value,v=50),S(V)});const T=o("vex-pp-clearall-"+V);T&&T.addEventListener("click",()=>{V==="inv"?(k=[],E="",r=50):(i=[],x="",v=50),M()}),S(V)}function S(V){const Q=o("vex-pp-"+V+"-list"),ee=o("vex-pp-"+V+"-pg");if(!Q)return;const ne=V==="inv"?k:i,oe=V==="inv"?E:x,ue=V==="inv"?r:v,b=V==="inv"?K:G,C=ne.map((N,d)=>({f:N,i:d})),T=oe?C.filter(({f:N})=>N.name.toLowerCase().includes(oe.toLowerCase())):C,U=T.slice(0,ue);if(Q.innerHTML=U.map(({f:N,i:d})=>`
            <div class="vex-pp-file-row">
                ${b}
                <span class="vex-pp-fi-name" title="${u(N.name)}">${u(N.name)}</span>
                <span class="vex-pp-fi-size">${l(N.size)}</span>
                <button class="vex-pp-fi-del" type="button" data-kind="${V}" data-ridx="${d}" aria-label="remove">${W}</button>
            </div>`).join("")+`<div id="vex-pp-sentinel-${V}" style="height:1px;flex-shrink:0"></div>`,Q.querySelectorAll(".vex-pp-fi-del").forEach(N=>{N.addEventListener("click",()=>{const d=parseInt(N.dataset.ridx,10);N.dataset.kind==="inv"?H(d):_(d)})}),ee){const N=t("vex-preview-count")||"显示前 {n} / 共 {m}";ee.textContent=N.replace("{n}",U.length).replace("{m}",T.length)}y(V,T.length)}function y(V,Q){if((V==="inv"?r:v)>=Q)return;const ne=o("vex-pp-sentinel-"+V),oe=o("vex-pp-"+V+"-list");if(!ne||!oe)return;const ue=new IntersectionObserver(b=>{b[0].isIntersecting&&(ue.disconnect(),V==="inv"?r+=50:v+=50,S(V))},{root:oe,threshold:.8});ue.observe(ne)}function m(V,Q,ee,ne){const oe=o(V),ue=o(Q);!oe||!ue||(oe.addEventListener("click",()=>ue.click()),oe.addEventListener("keydown",b=>{(b.key==="Enter"||b.key===" ")&&(b.preventDefault(),ue.click())}),oe.addEventListener("dragover",b=>{b.preventDefault(),oe.classList.add("drag-over")}),oe.addEventListener("dragleave",()=>oe.classList.remove("drag-over")),oe.addEventListener("drop",b=>{b.preventDefault(),oe.classList.remove("drag-over");const T=Array.from(b.dataTransfer.files).filter(U=>a.test(U.name));if(!T.length){showToast(t("vex-toast-bad-ext"),"error");return}ee(T)}),ue.addEventListener("change",()=>{const b=Array.from(ue.files);ee(b),ue.value=""}))}async function $(){if(p||!k.length||!i.length)return;p=!0,o("vex-build").disabled=!0,o("vex-progress").style.display="flex";var V=document.getElementById("vex-download");V&&(V.style.display="none"),["vex-summary-collapse","vex-detail-collapse"].forEach(function(oe){var ue=document.getElementById(oe);ue&&(ue.style.display="none")});const Q=Date.now();o("vex-progress-title").textContent=t("vex-progress-running")||"AI 抽取中",o("vex-progress-sub").textContent=(t("vex-progress-sub")||"{a} 张发票 + {b} 份报告 · 并行处理").replace("{a}",k.length).replace("{b}",i.length);const ee=setInterval(()=>{const oe=Math.floor((Date.now()-Q)/1e3);o("vex-progress-sub").textContent=(t("vex-progress-elapsed")||"已 {s} 秒 · {a} 张发票 + {b} 份报告").replace("{s}",oe).replace("{a}",k.length).replace("{b}",i.length)},1e3);try{const oe=new FormData;for(const pe of k)oe.append("invoices",pe);for(const pe of i)oe.append("reports",pe);const ue=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";oe.append("lang",ue);const b=localStorage.getItem("mrpilot_token")||"",C=await fetch("/api/vat_excel/submit",{method:"POST",headers:s(),body:oe});let T=null;try{T=await C.json()}catch{T=null}if(!C.ok||!T||!T.ok||!T.job_id)throw clearInterval(ee),new Error(T&&T.detail||"HTTP "+C.status);const U=o("vex-progress-sub"),N=await window._reconPollJob(T.job_id,b,{onProgress:pe=>{U&&(U.textContent=window._reconProgressText(pe,ue))}});if(clearInterval(ee),!N||N.status!=="done"||!N.result_id)throw new Error(t("vex-toast-fail")||"生成失败");const d=N.result_id;let j=0;const O=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(d)+"/download",{headers:s()});if(!O.ok)throw new Error("HTTP "+O.status);const X=(O.headers.get("Content-Disposition")||"").match(/filename="([^"]+)"/),de=X&&X[1]||"vat_recon_"+Date.now()+".xlsx",se=await O.blob(),ce=URL.createObjectURL(se),ae=o("vex-download");ae.href=ce,ae.download=de;try{const pe=document.createElement("a");pe.href=ce,pe.download=de,document.body.appendChild(pe),pe.click(),setTimeout(()=>pe.remove(),100)}catch{}o("vex-progress").style.display="none";var ne=document.getElementById("vex-download");ne&&(ne.style.display=""),d&&(j=await Z(d)),window._onVexResultShown&&window._onVexResultShown(),j>0?showToast((t("vex-toast-some-fail")||"有 {n} 张发票 OCR 失败").replace("{n}",j),"warn"):showToast(t("vex-toast-done")||"Excel 已生成","success"),R(),setTimeout(D,800)}catch(oe){clearInterval(ee),o("vex-progress").style.display="none";const ue=(t("vex-toast-fail")||"生成失败")+": "+(oe.message||oe);showToast(ue,"error")}finally{p=!1,o("vex-build").disabled=!1}}function P(){k=[],i=[];var V=document.getElementById("vex-download");V&&(V.style.display="none"),M()}function Y(V){if(V==null)return"—";var Q=parseFloat(V);return isNaN(Q)?"—":Q.toLocaleString("th-TH",{minimumFractionDigits:2,maximumFractionDigits:2})}async function Z(V){try{var Q=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(V),{headers:s()});if(!Q.ok)throw new Error(Q.status);var ee=await Q.json(),ne=ee.raw_data_json;if(typeof ne=="string")try{ne=JSON.parse(ne)}catch{ne={}}ne=ne||{};var oe=ne.rows||[],ue=[];oe.forEach(function(T){T.kind==="invoice_orphan"?ue.push({invoice_no:T.invoice_no||"",field:"仅发票有",report_value:"—",invoice_value:Y(T.amount_inv),kind:T.kind}):T.kind==="report_orphan"?ue.push({invoice_no:T.invoice_no||"",field:"仅报告有",report_value:Y(T.amount_rep),invoice_value:"—",kind:T.kind}):T.dims&&Object.keys(T.dims).length>0&&Object.keys(T.dims).forEach(function(U){var N=String(T.dims[U]||""),d=N.split(" ≠ ");ue.push({invoice_no:T.invoice_no||"",field:U,report_value:d[0]||N,invoice_value:d.length>1?d[1]:"—",kind:"diff"})})});var b=oe.filter(function(T){return T.kind==="matched_cash"}).length,C=Math.max(0,parseInt(ne.invoice_ocr_failed_count||0,10));return window._vexLastTask={total:ne.n_total||0,matched:ne.n_ok||0,diff:ne.n_diff||0,incomplete:C,cash:b,diff_rows:ue,task_id:V},window._fillVexSummary&&window._fillVexSummary(),window._fillVexDetail&&window._fillVexDetail(),C}catch{return 0}}function le(){const V=document.getElementById("vex-pane");V&&V.querySelectorAll("[data-i18n]").forEach(Q=>{const ee=t(Q.dataset.i18n);ee&&(Q.textContent=ee)}),M(),D()}function ie(){m("vex-drop-invoice","vex-input-invoice",I),m("vex-drop-report","vex-input-report",L);const V=o("vex-build"),Q=o("vex-reset");V&&V.addEventListener("click",$),Q&&Q.addEventListener("click",P),document.querySelectorAll('[data-recon-tab="sale-vat"]').forEach(oe=>{oe.addEventListener("click",()=>{R(),D()})}),g();const ee=document.getElementById("vex-task-search");ee&&ee.addEventListener("input",z);const ne=document.getElementById("vex-toggle-preview");ne&&ne.addEventListener("click",()=>{const oe=o("vex-preview-panel"),ue=o("vex-toggle-preview-label"),b=oe&&oe.style.display!=="none";oe&&(oe.style.display=b?"none":""),ne&&ne.classList.toggle("open",!b),ue&&(ue.textContent=b?t("vex-toggle-preview-open")||"查看清单":t("vex-toggle-preview-close")||"收起清单"),b||te()}),M(),R()}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",ie):ie(),typeof window.subscribeI18n=="function"&&(window.subscribeI18n("vex-excel",le),window.subscribeI18n("vex-preview-panel",te))})();(function(){const e=y=>document.getElementById(y),n=()=>localStorage.getItem("mrpilot_token")||"",a=()=>typeof window.currentLang=="string"&&window.currentLang?window.currentLang:localStorage.getItem("mrpilot_lang")||"th",o=()=>({Authorization:"Bearer "+n()}),s={inited:!1,glFile:[],vatFile:[],running:!1,currentTaskId:null,lastDetail:[],lastSummary:null},u={th:{not_found:"ไม่พบข้อมูล",running:"กำลังกระทบยอด…",error:"เกิดข้อผิดพลาด",need_files:"กรุณาเลือกไฟล์ทั้งสอง",done:"เสร็จสิ้น",hint_need_both:"อัปโหลด ① รายงานภาษีขาย + ② GL",hint_need_one_more:"อัปโหลดอีก 1 ไฟล์",hint_ready:"พร้อมแล้ว · กดเริ่มกระทบยอด",hist_load:"โหลด",hist_export:"ส่งออก",hist_delete:"ลบ",confirm_delete:"ยืนยันการลบงานนี้?",s_gl_total:"ยอดรวมตามบัญชีแยกประเภท",s_minus_gl_cr:"หัก : รายการเครดิตที่ไม่มีในรายงานภาษีขาย",s_plus_gl_dr:"บวก : รายการเดบิตที่ไม่มีในรายงานภาษีขาย",s_plus_vat_p:"บวก : รายการยอดขายที่ไม่มีในบัญชีแยกประเภท",s_minus_vat_n:"หัก : รายการลดหนี้ที่ไม่มีในบัญชีแยกประเภท",s_vat_total:"ยอดรวมตามรายงานภาษีขาย"},zh:{not_found:"未找到数据",running:"正在对账中...",error:"出错了",need_files:"请先选择两个文件",done:"完成",hint_need_both:"请上传① 销项税报告 + ② 总账 GL",hint_need_one_more:"还需上传 1 份文件",hint_ready:"已就绪 · 点击开始对账",hist_load:"加载",hist_export:"导出",hist_delete:"删除",confirm_delete:"确认删除此任务？",s_gl_total:"总账金额合计",s_minus_gl_cr:"减：销项税报告中未列的贷方记录",s_plus_gl_dr:"加：销项税报告中未列的借方记录",s_plus_vat_p:"加：总账中未列的销售记录",s_minus_vat_n:"减：总账中未列的贷项凭单(credit note)记录",s_vat_total:"销项税报告金额合计"},en:{not_found:"Not found",running:"Reconciling...",error:"Error",need_files:"Please select both files",done:"Done",hint_need_both:"Upload ① Output VAT report + ② GL file",hint_need_one_more:"1 more file required",hint_ready:"Ready · click Run to start",hist_load:"Load",hist_export:"Export",hist_delete:"Delete",confirm_delete:"Delete this task?",s_gl_total:"Total per General Ledger",s_minus_gl_cr:"Less: GL credits not in VAT Report",s_plus_gl_dr:"Add: GL debits not in VAT Report",s_plus_vat_p:"Add: Sales in VAT Report not in GL",s_minus_vat_n:"Less: Credit notes in VAT Report not in GL",s_vat_total:"Total per VAT Sales Report"},ja:{not_found:"データなし",running:"照合中…",error:"エラー",need_files:"両方のファイルを選択してください",done:"完了",hint_need_both:"① 売上税報告 + ② GL をアップロード",hint_need_one_more:"あと 1 ファイル必要",hint_ready:"準備完了 · 「開始」をクリック",hist_load:"読込",hist_export:"出力",hist_delete:"削除",confirm_delete:"このタスクを削除しますか?",s_gl_total:"総勘定元帳合計",s_minus_gl_cr:"減：売上税報告にないGL貸方記録",s_plus_gl_dr:"加：売上税報告にないGL借方記録",s_plus_vat_p:"加：GLにない売上記録",s_minus_vat_n:"減：GLにない赤伝記録",s_vat_total:"売上税報告合計"}},l=y=>(u[a()]||u.th)[y]||y;function k(y){const m=a(),P={gl_no_revenue_rows:{zh:"GL 中未找到收入科目行。请确认「收入科目前缀」是否正确(收入科目通常以 4 开头),改对后重试。",th:"ไม่พบรายการบัญชีรายได้ใน GL · ตรวจสอบ «คำนำหน้าบัญชีรายได้» (รายได้มักขึ้นต้นด้วย 4) แล้วลองใหม่",en:"No revenue-account rows found in the GL. Check the “revenue account prefix” (revenue usually starts with 4) and retry.",ja:"GL に収益科目の行が見つかりません。「収益科目プレフィックス」(通常 4 で始まる)を確認して再試行してください。"},gl_parse_failed:{zh:"GL 文件解析失败。请确认文件含日期/科目/借贷列,或换清晰的 Excel/CSV 重传。",th:"อ่านไฟล์ GL ไม่สำเร็จ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต-เครดิต หรืออัปโหลด Excel/CSV ที่ชัดเจน",en:"Failed to parse the GL file. Ensure it has date/account/debit-credit columns, or re-upload a clean Excel/CSV.",ja:"GL ファイルの解析に失敗しました。日付/科目/借方貸方列を確認するか、Excel/CSV を再アップロードしてください。"},vat_no_rows:{zh:"销项税报告里没有可对账的数据行。请确认上传了正确的销项税报告。",th:"ไม่พบแถวข้อมูลในรายงานภาษีขาย · ตรวจสอบว่าอัปโหลดรายงานที่ถูกต้อง",en:"No rows found in the sales-VAT report. Please check you uploaded the correct report.",ja:"売上VATレポートに行が見つかりません。正しいレポートをアップロードしたか確認してください。"},vat_parse_failed:{zh:"销项税报告解析失败。请换更清晰的版本,或转成 Excel/PDF 重传。",th:"อ่านรายงานภาษีขายไม่สำเร็จ · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น Excel/PDF",en:"Failed to parse the sales-VAT report. Try a clearer version, or convert to Excel/PDF.",ja:"売上VATレポートの解析に失敗しました。より鮮明な版か、Excel/PDF に変換してください。"}}[y];return P?P[m]||P.th||P.en:l("error")||"Error"}const i=y=>y==null||isNaN(y)?"":Number(y).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});function p(y,m,$,P){const Y=e(y),Z=e(m),le=e($);if(!Y||!Z||!le)return;const ie=V=>{if(!V||!V.length)return;const Q=Array.isArray(s[P])?s[P].slice():[],ee=new Set(Q.map(ne=>ne.name+"|"+ne.size));for(const ne of V){if(!ne)continue;const oe=ne.name+"|"+ne.size;ee.has(oe)||(Q.push(ne),ee.add(oe))}s[P]=Q,c(le,Q),v(),E(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()};Y.addEventListener("click",()=>Z.click()),Y.addEventListener("keydown",V=>{(V.key==="Enter"||V.key===" ")&&(V.preventDefault(),Z.click())}),Z.addEventListener("change",()=>{ie(Array.from(Z.files||[])),Z.value=""}),Y.addEventListener("dragover",V=>{V.preventDefault(),Y.classList.add("drag-over")}),Y.addEventListener("dragleave",()=>Y.classList.remove("drag-over")),Y.addEventListener("drop",V=>{V.preventDefault(),Y.classList.remove("drag-over");const Q=V.dataTransfer&&V.dataTransfer.files?Array.from(V.dataTransfer.files):[];ie(Q)})}function c(y,m){if(!y)return;if(!m||m.length===0){y.textContent="";return}const $=m.reduce((P,Y)=>P+Math.round(Y.size/1024),0);if(m.length===1)y.textContent=m[0].name+"  ("+$+" KB)";else{const P=window.t&&window.t("glv-files-count")||"{n} 个文件";y.textContent=P.replace("{n}",m.length)+"  ("+$+" KB)"}}function r(y){const m=s[y];return Array.isArray(m)?m:m?[m]:[]}function v(){const y=e("btn-glv-run");if(!y)return;const m=r("glFile").length>0&&r("vatFile").length>0;y.disabled=!m||s.running}function E(){const y=e("glv-status");if(!y||s.running)return;const m=r("vatFile").length,$=r("glFile").length;m===0&&$===0?(y.className="vex-action-info muted",y.innerHTML="<span>"+l("hint_need_both")+"</span>"):m>0&&$>0?(y.className="vex-action-info ok",y.innerHTML="<span>"+l("hint_ready")+"</span>"):(y.className="vex-action-info muted",y.innerHTML="<span>"+l("hint_need_one_more")+"</span>")}function x(y,m){const $=y==="vat"?"vatFile":"glFile",P=y==="vat"?"glv-vat-input":"glv-gl-input",Y=y==="vat"?"glv-vat-name":"glv-gl-name",Z=r($);m==null?s[$]=[]:s[$]=Z.filter((ie,V)=>V!==m);const le=e(P);le&&(le.value=""),c(e(Y),r($)),v(),E(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}window._glvRemoveFile=x;function R(){s.glFile=[],s.vatFile=[],s.currentTaskId=null,s.lastDetail=[],s.lastSummary=null;const y=e("glv-vat-input");y&&(y.value="");const m=e("glv-gl-input");m&&(m.value="");const $=e("glv-vat-name");$&&($.textContent="");const P=e("glv-gl-name");P&&(P.textContent="");const Y=e("glv-result");Y&&(Y.style.display="none");const Z=e("glv-kpi-strip");Z&&(Z.style.display="none"),v(),E(),window._glvClearPreviewSearch&&window._glvClearPreviewSearch(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}function D(y){const m=e("glv-tbody");if(!m)return;re(y.length),m.innerHTML="";const $=l("not_found"),P=document.createDocumentFragment();y.forEach(Y=>{const Z=document.createElement("tr"),le=(ne,oe)=>{const ue=document.createElement("td");return oe&&(ue.className=oe),ue.textContent=ne,ue},ie=Y.gl_amount===null||Y.gl_amount===void 0,V=Y.diff;let Q="glv-num",ee="glv-num";ie?(ee+=" glv-cell-missing",Q+=" glv-cell-missing"):Math.abs(V||0)<.005?Q+=" glv-cell-ok":Q+=" glv-cell-diff",Z.appendChild(le(Y.doc_no||"","glv-doc")),Z.appendChild(le(Y.date||"","")),Z.appendChild(le(Y.customer_name||"","")),Z.appendChild(le(i(Y.vat_amount),"glv-num")),Z.appendChild(le(ie?$:i(Y.gl_amount),ee)),Z.appendChild(le(ie?$:i(Y.diff),Q)),Z.appendChild(le(Y.account_codes||"","glv-doc")),P.appendChild(Z)}),m.appendChild(P)}function w(y){const m=e("glv-summary-table")&&e("glv-summary-table").querySelector("tbody");if(!m)return;m.innerHTML="",[{label:l("s_gl_total"),amount:y.gl_total,emph:!0,items:[],negate:!1},{label:l("s_minus_gl_cr"),amount:-(y.gl_only_credit||0),emph:!1,items:y.gl_only_credit_items||[],negate:!0},{label:l("s_plus_gl_dr"),amount:y.gl_only_debit||0,emph:!1,items:y.gl_only_debit_items||[],negate:!1},{label:l("s_plus_vat_p"),amount:y.vat_only_positive||0,emph:!1,items:y.vat_only_positive_items||[],negate:!1},{label:l("s_minus_vat_n"),amount:y.vat_only_negative||0,emph:!1,items:y.vat_only_negative_items||[],negate:!1},{label:l("s_vat_total"),amount:y.vat_total,emph:!0,items:[],negate:!1}].forEach(({label:P,amount:Y,emph:Z,items:le,negate:ie})=>{const V=document.createElement("tr");V.className=Z?"glv-summary-total":"glv-summary-sect";const Q=document.createElement("td"),ee=document.createElement("td");Q.textContent=P,ee.textContent=Z?i(Y):"",V.appendChild(Q),V.appendChild(ee),m.appendChild(V),(le||[]).forEach(ne=>{const oe=document.createElement("tr");oe.className="glv-summary-item";const ue=document.createElement("td"),b=document.createElement("td"),C=[ne.doc_no,ne.date,ne.name].filter(Boolean);ue.textContent="· "+C.join("  ·  ");const T=ie?-(ne.amount||0):ne.amount||0;b.textContent=i(T),oe.appendChild(ue),oe.appendChild(b),m.appendChild(oe)})})}function B(y){e("glv-kpi-matched")&&(e("glv-kpi-matched").textContent=y&&y.matched!=null?y.matched:"—"),e("glv-kpi-diff")&&(e("glv-kpi-diff").textContent=y&&y.diff!=null?y.diff:"—"),e("glv-kpi-unmatched")&&(e("glv-kpi-unmatched").textContent=y&&y.unmatched!=null?y.unmatched:"—")}function z(y){if(!y)return"";try{const m=new Date(y);if(isNaN(m.getTime()))return y;const $=P=>String(P).padStart(2,"0");return m.getFullYear()+"-"+$(m.getMonth()+1)+"-"+$(m.getDate())+" "+$(m.getHours())+":"+$(m.getMinutes())}catch{return y}}const q=10;var F=[],A=1;function g(){A=1,f();var y=((e("glv-hist-search")||{}).value||"").trim().toLowerCase();if(y){var m=e("glv-history-tbody");m&&m.querySelectorAll("tr").forEach(function($){$.dataset.taskId&&($.style.display=$.textContent.toLowerCase().indexOf(y)>=0?"":"none")})}}function f(){const y=e("glv-history-table-wrap"),m=e("glv-history-empty"),$=e("glv-history-tbody"),P=e("glv-history-pager"),Y=e("glv-history-pager-info"),Z=e("glv-history-prev"),le=e("glv-history-next");if(!$)return;if($.innerHTML="",!F.length){y&&(y.style.display="none"),m&&(m.style.display=""),P&&(P.style.display="none");return}y&&(y.style.display=""),m&&(m.style.display="none");const ie=Math.ceil(F.length/q);A>ie&&(A=ie);const V=(A-1)*q,Q=F.slice(V,V+q);P&&(P.style.display=F.length>q?"":"none",Y&&(Y.textContent=A+" / "+ie),Z&&(Z.disabled=A<=1),le&&(le.disabled=A>=ie)),Q.forEach(ne=>{const oe=document.createElement("tr");oe.dataset.taskId=ne.id;const ue=document.createElement("td");ue.textContent=z(ne.created_at);const b=document.createElement("td");b.className="glv-history-file",b.title=(ne.vat_filename||"")+" + "+(ne.gl_filename||""),b.textContent=(ne.vat_filename||"?")+" + "+(ne.gl_filename||"?");const C=document.createElement("td");C.className="glv-num",C.textContent=(ne.vat_row_count||0)+" / "+(ne.gl_row_count||0);const T=document.createElement("td");T.className="glv-num",T.textContent=ne.matched_count||0;const U=document.createElement("td");U.className="glv-num",U.textContent=ne.diff_count||0;const N=document.createElement("td");N.className="glv-num",N.textContent=ne.unmatched_count||0;const d=document.createElement("td");d.className="glv-history-actions";const j=(de,se,ce,ae)=>{const pe=document.createElement("button");return pe.type="button",ce&&(pe.className=ce),pe.title=se,pe.setAttribute("aria-label",se),pe.innerHTML=de,pe.onclick=ae,pe},O='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 8a6 6 0 1 0 12 0A6 6 0 0 0 2 8z"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',J='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',X='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';d.appendChild(j(O,l("hist_load"),"",()=>L(ne.id))),d.appendChild(j(J,l("hist_export"),"",()=>H(ne.id))),d.appendChild(j(X,l("hist_delete"),"glv-del",()=>_(ne.id))),[ue,b,C,T,U,N,d].forEach(de=>oe.appendChild(de)),$.appendChild(oe)})}function h(){var y=e("glv-history-prev"),m=e("glv-history-next");y&&!y._glvBound&&(y._glvBound=!0,y.addEventListener("click",function(){A>1&&(A--,f())})),m&&!m._glvBound&&(m._glvBound=!0,m.addEventListener("click",function(){var $=Math.ceil(F.length/q);A<$&&(A++,f())}))}async function I(){try{const m=await(await fetch("/api/recon/gl-vat/tasks",{headers:o()})).json();F=m&&m.tasks||[],A=1,f(),h()}catch(y){console.error("[gl-vat] history load failed:",y)}}async function L(y){try{const $=await(await fetch("/api/recon/gl-vat/"+y,{headers:o()})).json();if(!$||!$.ok)throw new Error("load_failed");s.currentTaskId=y,s.lastDetail=$.detail||[],s.lastSummary=$.summary||{},B($.stats||{}),D(s.lastDetail),w(s.lastSummary);const P=e("glv-result");P&&(P.style.display=""),W(),window.scrollTo({top:P?P.offsetTop-80:0,behavior:"smooth"})}catch(m){console.error("[gl-vat] load task failed:",m),alert(l("error")+": "+(m.message||m))}}async function H(y){try{const m="/api/recon/gl-vat/"+y+"/export?lang="+encodeURIComponent(a()),$=await fetch(m,{headers:o()});if(!$.ok)throw new Error("HTTP "+$.status);const P=await $.blob(),Y=document.createElement("a");Y.href=URL.createObjectURL(P),Y.download="GL_VAT_recon_"+y+".xlsx",document.body.appendChild(Y),Y.click(),setTimeout(()=>{URL.revokeObjectURL(Y.href),Y.remove()},200)}catch(m){console.error("[gl-vat] exportTask failed:",m),typeof showToast=="function"&&showToast(l("error")+": "+(m.message||m),"error")}}async function _(y){let m;if(typeof window.showConfirm=="function"?m=await window.showConfirm(l("confirm_delete"),{danger:!0}):m=confirm(l("confirm_delete")),!!m)try{const $=await fetch("/api/recon/gl-vat/"+y,{method:"DELETE",headers:o()});if(!$.ok)throw new Error("HTTP "+$.status);I()}catch($){console.error("[gl-vat] delete failed:",$),typeof showToast=="function"&&showToast(l("error")+": "+($.message||$),"error")}}async function M(){if(!s.glFile||!s.vatFile){typeof showToast=="function"&&showToast(l("need_files"),"warn");return}s.running=!0,v();const y=e("glv-status"),m=e("glv-progress"),$=e("glv-progress-sub");y&&(y.className="vex-action-info muted",y.style.color="",y.innerHTML="<span>"+l("running")+"</span>"),m&&(m.style.display=""),$&&($.textContent=(s.vatFile.name||"VAT")+" + "+(s.glFile.name||"GL"));const P=new FormData,Y=r("vatFile"),Z=r("glFile");for(const ie of Y)P.append("vat_files",ie,ie.name);for(const ie of Z)P.append("gl_files",ie,ie.name);const le=(e("glv-prefix")&&e("glv-prefix").value||"4").trim()||"4";P.append("revenue_prefix",le),P.append("lang",a());try{const ie=await fetch("/api/recon/gl-vat/submit",{method:"POST",headers:o(),body:P});let V=null;try{V=await ie.json()}catch{V=null}if(!ie.ok||!V||!V.ok||!V.job_id)throw new Error(V&&V.detail||V&&V.error||"HTTP "+ie.status);const Q=e("glv-progress-sub"),ee=await window._reconPollJob(V.job_id,n(),{onProgress:b=>{Q&&(Q.textContent=window._reconProgressText(b,a()))}});if(!ee||ee.status!=="done"||!ee.result_id)throw ee&&ee.status==="failed"&&ee.error_code?new Error(k(ee.error_code)):new Error(l("error")||"Error");const ne=await fetch("/api/recon/gl-vat/"+encodeURIComponent(ee.result_id),{headers:o()});let oe=null;try{oe=await ne.json()}catch{oe=null}if(!ne.ok||!oe||!oe.ok)throw new Error(oe&&oe.detail||oe&&oe.error||"HTTP "+ne.status);s.currentTaskId=oe.task_id,s.lastDetail=oe.detail||[],s.lastSummary=oe.summary||{},B(oe.stats||{}),D(s.lastDetail),w(s.lastSummary);const ue=e("glv-result");ue&&(ue.style.display=""),W(),y&&(y.className="vex-action-info ok",y.style.color="",y.innerHTML="<span>"+l("done")+" · GL "+(oe.gl_row_count||0)+" · VAT "+(oe.vat_row_count||0)+"</span>"),I()}catch(ie){console.error("[gl-vat] run failed:",ie),y&&(y.className="vex-action-info",y.style.color="#ef4444",y.innerHTML="<span>"+l("error")+": "+(ie.message||ie)+"</span>")}finally{s.running=!1,m&&(m.style.display="none"),v()}}async function K(){if(s.currentTaskId)try{const y="/api/recon/gl-vat/"+s.currentTaskId+"/export?lang="+encodeURIComponent(a()),m=await fetch(y,{headers:o()});if(!m.ok)throw new Error("HTTP "+m.status);const $=await m.blob(),P=document.createElement("a");P.href=URL.createObjectURL($),P.download="GL_VAT_recon_"+s.currentTaskId+".xlsx",document.body.appendChild(P),P.click(),setTimeout(()=>{URL.revokeObjectURL(P.href),P.remove()},200)}catch(y){console.error("[gl-vat] export failed:",y),typeof showToast=="function"&&showToast(l("error")+": "+(y.message||y),"error")}}function G(){s.running||E(),I(),s.lastDetail&&s.lastDetail.length&&D(s.lastDetail),s.lastSummary&&w(s.lastSummary)}function W(){var y=e("glv-kpi-strip");y&&(y.style.display="");var m=e("glv-section-summary");m&&m.setAttribute("data-collapsed","false");var $=e("glv-section-detail");$&&$.setAttribute("data-collapsed","false")}function te(){document.querySelectorAll(".glv-section-head[data-toggle]").forEach(y=>{const m=y.getAttribute("data-toggle"),$=document.getElementById(m);if(!$)return;const P=Y=>{if(Y.target&&Y.target.closest("button")!==null&&!Y.target.classList.contains("glv-section-head"))return;const Z=$.getAttribute("data-collapsed")==="true";$.setAttribute("data-collapsed",Z?"false":"true")};y.addEventListener("click",P),y.addEventListener("keydown",Y=>{(Y.key==="Enter"||Y.key===" ")&&(Y.preventDefault(),P(Y))})})}function re(y){const m=e("glv-detail-count");m&&(m.textContent=y!=null?String(y):"")}function S(){if(s.inited){I();return}s.inited=!0,p("glv-drop-gl","glv-gl-input","glv-gl-name","glFile"),p("glv-drop-vat","glv-vat-input","glv-vat-name","vatFile");const y=e("btn-glv-run");y&&y.addEventListener("click",M);const m=e("btn-glv-export");m&&m.addEventListener("click",K);const $=e("btn-glv-reset");$&&$.addEventListener("click",R);const P=e("glv-hist-search");P&&P.addEventListener("input",g),te(),B(null),E(),window._loadGlvHistory=I,I(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("gl-vat-recon",G)}window.GlVatRecon={ensureInit:S},window._glvPreviewFiles=function(y){return r(y==="vat"?"vatFile":"glFile")}})();(function(){const e=["flowaccount","peak","xero","quickbooks","express"],n={flowaccount:"FlowAccount",peak:"PEAK",xero:"Xero",quickbooks:"QuickBooks",express:"Express"},a=["expense_office","expense_travel","expense_utility","asset_inventory","asset_fixed","liability_ap","revenue_sales","revenue_service","other"],o=["vat_7","vat_0","vat_exempt","wht_1","wht_3","wht_5","non_vat"],s="468b50c1-5593-4fd6-990d-515ce8085563";let u={sub:"clients",loaded:{clients:!1,accounts:!1,taxes:!1,products:!1},items:{clients:[],accounts:[],taxes:[],products:[]},clientList:[],clientLoaded:!1,addingNew:{clients:!1,accounts:!1,taxes:!1,products:!1},bound:!1};function l(){const L=typeof _userInfo<"u"?_userInfo:null;return!!(L&&(L.role==="owner"||L.is_super_admin))}function k(){const L=typeof _userInfo<"u"?_userInfo:null;return!!(L&&L.id===s)}function i(L){return typeof escapeHtml=="function"?escapeHtml(L==null?"":String(L)):String(L??"")}function p(L,H){try{typeof showToast=="function"&&showToast(L,H||"info")}catch{}}async function c(L,H){const _=localStorage.getItem("mrpilot_token");if(_&&!(u.loaded[L]&&!H))try{const M=await fetch("/api/erp/mappings/"+L,{headers:{Authorization:"Bearer "+_}});if(!M.ok)throw new Error("http_"+M.status);const K=await M.json();u.items[L]=K.items||[],u.loaded[L]=!0}catch{u.items[L]=[],u.loaded[L]=!1}}async function r(L){if(u.clientLoaded)return;const H=localStorage.getItem("mrpilot_token");if(H)try{const _=await fetch("/api/clients?include_inactive=false",{headers:{Authorization:"Bearer "+H}});if(!_.ok)throw new Error("http_"+_.status);const M=await _.json();u.clientList=(M.clients||M.items||[]).filter(K=>K.is_active!==!1),u.clientLoaded=!0}catch{u.clientList=[]}}function v(){const L=document.getElementById("erp-map-pane-wrap");if(!L)return;const H=!l();let _="";H&&(_+='<div class="erp-map-readonly-banner"><svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="8"/><path d="M10 6v4M10 13v0.01"/></svg>'+i(t("erp-map-readonly-tip"))+"</div>"),_+='<div class="erp-map-toolbar">',!H&&u.sub!=="products"&&(_+='<button class="btn btn-primary" type="button" id="erp-map-add-btn" data-i18n="erp-map-add-row">'+i(t("erp-map-add-row"))+"</button>"),_+="</div>",_+='<div class="erp-map-table" id="erp-map-table-host"></div>',L.innerHTML=_,E();const M=document.getElementById("erp-map-dev-bar");M&&(M.style.display=l()&&k()?"":"none")}function E(){const L=document.getElementById("erp-map-table-host");if(!L)return;const H=u.sub,_=u.items[H]||[],M=u.addingNew[H],K=!l();if(!_.length&&!M){L.innerHTML='<div class="erp-map-empty"><strong>'+i(t("erp-map-empty-"+H))+"</strong>"+i(t("erp-map-empty-"+H+"-sub"))+"</div>";return}let G="";G+=x(H),M&&!K&&(G+=z(H)),_.forEach(function(W){G+=q(H,W,K)}),L.innerHTML=G}function x(L){return L==="clients"?'<div class="erp-map-row erp-map-head row-clients"><div>'+i(t("erp-map-col-client"))+"</div><div>"+i(t("erp-map-col-erp"))+"</div><div>"+i(t("erp-map-col-erp-code"))+"</div><div>"+i(t("erp-map-col-notes"))+"</div><div>"+i(t("erp-map-col-actions"))+"</div></div>":L==="accounts"?'<div class="erp-map-row erp-map-head row-accounts"><div>'+i(t("erp-map-col-erp"))+"</div><div>"+i(t("erp-map-col-category"))+"</div><div>"+i(t("erp-map-col-erp-code"))+"</div><div>"+i(t("erp-map-col-erp-name"))+"</div><div>"+i(t("erp-map-col-notes"))+"</div><div>"+i(t("erp-map-col-actions"))+"</div></div>":L==="products"?'<div class="erp-map-row erp-map-head row-products"><div>'+i(t("erp-map-col-item-name"))+"</div><div>"+i(t("erp-map-col-erp-product-code"))+"</div><div>"+i(t("erp-map-col-erp-name"))+"</div><div>"+i(t("erp-map-col-notes"))+"</div><div>"+i(t("erp-map-col-actions"))+"</div></div>":'<div class="erp-map-row erp-map-head row-taxes"><div>'+i(t("erp-map-col-erp"))+"</div><div>"+i(t("erp-map-col-tax"))+"</div><div>"+i(t("erp-map-col-erp-tax-code"))+"</div><div>"+i(t("erp-map-col-notes"))+"</div><div>"+i(t("erp-map-col-actions"))+"</div></div>"}function R(L,H){let _='<select class="form-input" data-erp-field="'+H+'">';return _+='<option value="">'+i(t("erp-map-pick-erp"))+"</option>",e.forEach(function(M){const K=M===L?" selected":"";_+='<option value="'+M+'"'+K+">"+i(n[M])+"</option>"}),_+="</select>",_}function D(L){let H='<select class="form-input" data-erp-field="client_id">';return H+='<option value="">'+i(t("erp-map-pick-client"))+"</option>",(u.clientList||[]).forEach(function(_){const M=String(_.id)===String(L)?" selected":"";H+='<option value="'+_.id+'"'+M+">"+i(_.name||"#"+_.id)+"</option>"}),H+="</select>",H}function w(L){let H='<select class="form-input" data-erp-field="pearnly_category">';return H+='<option value="">'+i(t("erp-map-pick-cat"))+"</option>",a.forEach(function(_){const M=_===L?" selected":"";H+='<option value="'+_+'"'+M+">"+i(t("erp-map-cat-"+_))+"</option>"}),H+="</select>",H}function B(L){let H='<select class="form-input" data-erp-field="pearnly_tax_kind">';return H+='<option value="">'+i(t("erp-map-pick-tax"))+"</option>",o.forEach(function(_){const M=_===L?" selected":"";H+='<option value="'+_+'"'+M+">"+i(t("erp-map-tax-"+_))+"</option>"}),H+="</select>",H}function z(L){const H='<button class="btn btn-primary" type="button" data-erp-save="new" style="padding:6px 12px;height:32px;">'+i(t("erp-map-save"))+"</button>";return L==="clients"?'<div class="erp-map-row erp-map-row-add row-clients" data-erp-row="new"><div data-label="'+i(t("erp-map-col-client"))+'">'+D("")+'</div><div data-label="'+i(t("erp-map-col-erp"))+'">'+R("","erp_type")+'</div><div data-label="'+i(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+i(t("erp-map-ph-erp-code"))+'"></div><div data-label="'+i(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+i(t("erp-map-ph-notes"))+'"></div><div>'+H+"</div></div>":L==="accounts"?'<div class="erp-map-row erp-map-row-add row-accounts" data-erp-row="new"><div data-label="'+i(t("erp-map-col-erp"))+'">'+R("","erp_type")+'</div><div data-label="'+i(t("erp-map-col-category"))+'">'+w("")+'</div><div data-label="'+i(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+i(t("erp-map-ph-acc-code"))+'"></div><div data-label="'+i(t("erp-map-col-erp-name"))+'"><input type="text" class="form-input" data-erp-field="erp_name" placeholder="'+i(t("erp-map-ph-acc-name"))+'"></div><div data-label="'+i(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+i(t("erp-map-ph-notes"))+'"></div><div>'+H+"</div></div>":'<div class="erp-map-row erp-map-row-add row-taxes" data-erp-row="new"><div data-label="'+i(t("erp-map-col-erp"))+'">'+R("","erp_type")+'</div><div data-label="'+i(t("erp-map-col-tax"))+'">'+B("")+'</div><div data-label="'+i(t("erp-map-col-erp-tax-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+i(t("erp-map-ph-tax-code"))+'"></div><div data-label="'+i(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+i(t("erp-map-ph-notes"))+'"></div><div>'+H+"</div></div>"}function q(L,H,_){const M=_?"":'<button class="erp-map-del-btn" type="button" data-erp-del="'+i(H.id)+'" title="'+i(t("erp-map-delete"))+'"><svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h12M8 6V4h4v2M6 6l1 11h6l1-11"/></svg></button>',K='<span class="erp-map-erp-badge">'+i(n[H.erp_type]||H.erp_type)+"</span>";if(L==="clients")return'<div class="erp-map-row row-clients"><div data-label="'+i(t("erp-map-col-client"))+'" class="erp-map-cell-name">'+i(H.client_name||"#"+H.client_id)+'</div><div data-label="'+i(t("erp-map-col-erp"))+'">'+K+'</div><div data-label="'+i(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+i(H.erp_code||"")+'</div><div data-label="'+i(t("erp-map-col-notes"))+'">'+i(H.notes||"")+"</div><div>"+M+"</div></div>";if(L==="accounts"){const W=t("erp-map-cat-"+(H.pearnly_category||"other"))||H.pearnly_category;return'<div class="erp-map-row row-accounts"><div data-label="'+i(t("erp-map-col-erp"))+'">'+K+'</div><div data-label="'+i(t("erp-map-col-category"))+'" class="erp-map-cell-name">'+i(W)+'</div><div data-label="'+i(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+i(H.erp_code||"")+'</div><div data-label="'+i(t("erp-map-col-erp-name"))+'">'+i(H.erp_name||"")+'</div><div data-label="'+i(t("erp-map-col-notes"))+'">'+i(H.notes||"")+"</div><div>"+M+"</div></div>"}if(L==="products")return'<div class="erp-map-row row-products"><div data-label="'+i(t("erp-map-col-item-name"))+'" class="erp-map-cell-name">'+i(H.item_name||"")+'</div><div data-label="'+i(t("erp-map-col-erp-product-code"))+'" class="erp-map-code">'+i(H.erp_code||"")+'</div><div data-label="'+i(t("erp-map-col-erp-name"))+'">'+i(H.erp_name||"")+'</div><div data-label="'+i(t("erp-map-col-notes"))+'">'+i(H.notes||"")+"</div><div>"+M+"</div></div>";const G=t("erp-map-tax-"+(H.pearnly_tax_kind||""))||H.pearnly_tax_kind;return'<div class="erp-map-row row-taxes"><div data-label="'+i(t("erp-map-col-erp"))+'">'+K+'</div><div data-label="'+i(t("erp-map-col-tax"))+'" class="erp-map-cell-name"><span class="erp-map-tax-badge">'+i(G)+'</span></div><div data-label="'+i(t("erp-map-col-erp-tax-code"))+'" class="erp-map-code">'+i(H.erp_code||"")+'</div><div data-label="'+i(t("erp-map-col-notes"))+'">'+i(H.notes||"")+"</div><div>"+M+"</div></div>"}async function F(L){const H=u.sub,_={};L.querySelectorAll("[data-erp-field]").forEach(function(W){_[W.dataset.erpField]=(W.value||"").trim()});const M=localStorage.getItem("mrpilot_token");if(!M)return;let K={},G="/api/erp/mappings/"+H;if(H==="clients"){if(!_.client_id||!_.erp_type||!_.erp_code){p(t("erp-map-save-fail"),"error");return}K={client_id:parseInt(_.client_id,10),erp_type:_.erp_type,erp_code:_.erp_code,notes:_.notes||""}}else if(H==="accounts"){if(!_.erp_type||!_.pearnly_category||!_.erp_code){p(t("erp-map-save-fail"),"error");return}K={erp_type:_.erp_type,pearnly_category:_.pearnly_category,erp_code:_.erp_code,erp_name:_.erp_name||"",notes:_.notes||""}}else{if(!_.erp_type||!_.pearnly_tax_kind||!_.erp_code){p(t("erp-map-save-fail"),"error");return}K={erp_type:_.erp_type,pearnly_tax_kind:_.pearnly_tax_kind,erp_code:_.erp_code,notes:_.notes||""}}try{const W=await fetch(G,{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+M},body:JSON.stringify(K)});if(!W.ok)throw new Error("http_"+W.status);u.addingNew[H]=!1,await c(H,!0),E(),p(t("erp-map-saved-toast"),"success")}catch{p(t("erp-map-save-fail"),"error")}}async function A(L){if(!await window.pearnlyConfirm(t("erp-map-confirm-delete")))return;const _=u.sub,M=localStorage.getItem("mrpilot_token");try{const K=await fetch("/api/erp/mappings/"+_+"/"+encodeURIComponent(L),{method:"DELETE",headers:{Authorization:"Bearer "+M}});if(!K.ok)throw new Error("http_"+K.status);await c(_,!0),E(),p(t("erp-map-deleted-toast"),"success")}catch{p(t("erp-map-delete-fail"),"error")}}async function g(){await r(),await c(u.sub,!1),v()}function f(L){L!==u.sub&&(u.sub=L,u.addingNew[L]=!1,["clients","accounts","taxes","products"].forEach(function(H){H!==L&&(u.addingNew[H]=!1)}),document.querySelectorAll(".erp-map-subtab").forEach(function(H){H.classList.toggle("active",H.dataset.erpSubtab===L)}),c(L,!1).then(function(){v()}))}function h(){u.bound||(u.bound=!0,document.addEventListener("click",function(L){const H=L.target.closest(".erp-subtab[data-erp-subtab]");if(H){L.preventDefault();const W=H.dataset.erpSubtab;document.querySelectorAll(".erp-subtab").forEach(function(te){te.classList.toggle("active",te.dataset.erpSubtab===W)}),document.querySelectorAll(".erp-subpanel").forEach(function(te){te.classList.toggle("active",te.dataset.erpSubpanel===W)}),W==="mappings"&&setTimeout(g,50);return}const _=L.target.closest(".erp-map-subtab[data-erp-subtab]");if(_){L.preventDefault(),f(_.dataset.erpSubtab);return}if(L.target.closest("#erp-map-add-btn")){if(L.preventDefault(),!l())return;u.addingNew[u.sub]=!0,E();return}const K=L.target.closest('[data-erp-save="new"]');if(K){L.preventDefault();const W=K.closest('[data-erp-row="new"]');W&&F(W);return}const G=L.target.closest("[data-erp-del]");if(G){L.preventDefault(),A(G.dataset.erpDel);return}}))}function I(){const L=document.getElementById("erp-map-pane-wrap");L&&L.children.length>0&&v(),document.querySelectorAll(".erp-map-subtab").forEach(function(H){const _="erp-map-subtab-"+H.dataset.erpSubtab,M=t(_);M&&M!==_&&(H.textContent=M)})}h(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-mappings",I)})();(function(){let e=null,n=0,a=!1;function o(g){return typeof escapeHtml=="function"?escapeHtml(g==null?"":String(g)):String(g??"")}function s(g,f){try{typeof showToast=="function"&&showToast(g,f||"info")}catch{}}async function u(g){const f=Date.now();if(e&&f-n<3e4)return e;const h=localStorage.getItem("mrpilot_token");if(!h)return[];try{const I=await fetch("/api/erp/connectors/status",{headers:{Authorization:"Bearer "+h}});if(!I.ok)return[];const L=await I.json();return e=L&&L.connectors||[],n=f,e}catch{return[]}}function l(){try{return localStorage.getItem("pn_push_default_connector")||""}catch{return""}}function k(g){try{localStorage.setItem("pn_push_default_connector",g||"")}catch{}}function i(g){if(!g||!g.length)return null;const f=l();if(f){const I=g.find(L=>L.id===f);if(I)return I}const h=g.find(I=>I.is_default);return h||g[0]}function p(g){if(!g)return!1;const f=String(g.status||"").toLowerCase();return f==="exception"||f==="exception_pending"||f==="rejected"}function c(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function r(g){const f=g&&(g.type||g.id);return f==="xero"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5.5 8l2 2 3-3.5"/></svg>':f==="webhook"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="11.5" r="1.8"/><circle cx="11" cy="4.5" r="1.8"/><path d="M6.4 10l3.2-4M5 9.6V5.5a3 3 0 016 0"/></svg>':'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/><rect x="11" y="3" width="3" height="10" rx="1"/></svg>'}async function v(g,f){if(!g||!f)return!1;const h=document.getElementById("btn-push-default");h&&(h.disabled=!0,h.classList.add("loading"));const I=localStorage.getItem("mrpilot_token");try{let L,H={method:"POST",headers:{Authorization:"Bearer "+I}};g.type==="xero"?L="/api/erp/xero/push/"+encodeURIComponent(f):(L="/api/erp/push",H.headers["Content-Type"]="application/json",H.body=JSON.stringify({history_id:f,endpoint_id:g.endpoint_id||void 0}));const _=await fetch(L,H);let M={};try{M=await _.json()}catch{}if(!_.ok){let K=M&&M.detail||"unknown";typeof K=="object"&&(K=K.code||JSON.stringify(K));let G=String(K||"unknown");if(g.type==="xero"){const W=G.replace(/^xero\./,"").toLowerCase(),te=t("xero-"+W);te&&te!=="xero-"+W&&(G=te)}return s(t("unified-push-fail").replace("{name}",g.name).replace("{err}",G),"error"),!1}if(M&&M.ok===!1){let K=M.error_msg||M.error_code||"unknown";return K=String(K).slice(0,200),s(t("unified-push-fail").replace("{name}",g.name).replace("{err}",K),"error"),!1}return s(t("unified-push-ok").replace("{name}",g.name),"success"),!0}catch(L){return s(t("unified-push-fail").replace("{name}",g.name).replace("{err}",L.message||"network"),"error"),!1}finally{h&&(h.disabled=!1,h.classList.remove("loading"))}}async function E(g,f){for(const h of g)await v(h,f)}function x(g,f){const h=document.createElement("div");h.className="pn-push-dropdown",h.id="pn-push-dropdown";const I=(g||[]).map(H=>{const _=!!(f&&H.id===f.id),M=H.method==="download"?t("unified-push-tag-download"):_?t("unified-push-tag-default"):"";return'<div class="pn-pd-item" data-cid="'+o(H.id)+'"><span class="pn-pd-icon">'+r(H)+'</span><span class="pn-pd-name">'+o(H.name)+"</span>"+(M?'<span class="pn-pd-tag">'+o(M)+"</span>":"")+(_?'<span class="pn-pd-check">✓</span>':"")+"</div>"}).join(""),L=g&&g.length>1?'<div class="pn-pd-divider"></div><div class="pn-pd-item pn-pd-all" data-cid="__all__"><span class="pn-pd-icon"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h10M3 10h10M3 13.5h6"/></svg></span><span class="pn-pd-name">'+o(t("unified-push-all").replace("{n}",g.length))+"</span></div>":"";return h.innerHTML=I+L,h}function R(){const g=document.getElementById("pn-push-dropdown");g&&g.remove()}async function D(){if(document.getElementById("pn-push-dropdown")){R();return}const g=await u()||[],f=i(g),h=x(g,f),I=document.getElementById("pn-push-wrap");I&&I.appendChild(h)}async function w(){const g=await u()||[],f=i(g);if(!f)return;const h=c(),I=h&&(h._historyId||h.history_id);if(I){if(p(h)){s(t("unified-push-disabled-exc"),"warn");return}await v(f,I)}}async function B(g){R();const f=await u()||[],h=c(),I=h&&(h._historyId||h.history_id);if(!I)return;if(p(h)){s(t("unified-push-disabled-exc"),"warn");return}if(g==="__all__"){await E(f,I);return}const L=f.find(H=>H.id===g);L&&(k(g),await v(L,I),q())}async function z(){const g=document.getElementById("drawer-history-save");if(!g||g.querySelector("#pn-push-wrap"))return;const f=document.createElement("div");f.id="pn-push-wrap",f.className="pn-push-wrap",f.dataset.loading="1",g.insertBefore(f,g.firstChild),["btn-push-erp","btn-xero-push"].forEach(M=>{g.querySelectorAll("#"+M).forEach(K=>{K.style.display="none"})});const h=await u()||[],I=i(h),L=h.length>0;if(!L)f.innerHTML='<button type="button" class="btn btn-ghost pn-push-empty" id="btn-push-default" disabled title="'+o(t("unified-push-empty-tip"))+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/></svg><span style="margin-left:4px;">'+o(t("unified-push-empty"))+"</span></button>";else{const M=h.length>1;f.innerHTML='<div class="pn-push-split"><button type="button" class="pn-push-main" id="btn-push-default" title="'+o(t("unified-push-tip"))+'">'+r(I)+"<span>"+o(t("unified-push-to").replace("{name}",I?I.name:""))+"</span></button>"+(M?'<button type="button" class="pn-push-arrow" id="btn-push-arrow" title="'+o(t("unified-push-other"))+'"><svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5l3 3 3-3"/></svg></button>':"")+"</div>"}delete f.dataset.loading;const H=f.querySelector("#btn-push-default");H&&L&&H.addEventListener("click",w);const _=f.querySelector("#btn-push-arrow");_&&_.addEventListener("click",function(M){M.stopPropagation(),D()}),a||(a=!0,document.addEventListener("click",function(M){const K=M.target.closest(".pn-pd-item");if(K){const G=K.getAttribute("data-cid");B(G);return}M.target.closest("#btn-push-arrow")||R()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("unified-push",q))}function q(){const g=document.getElementById("pn-push-wrap");g&&(g.remove(),e=null,n=0,z())}function F(){const g=document.getElementById("drawer-history-save");if(!g||!g.querySelector("#pn-push-wrap"))return;["btn-push-erp","btn-xero-push"].forEach(h=>{g.querySelectorAll("#"+h).forEach(I=>{I.style.display!=="none"&&(I.style.display="none")})});const f=g.querySelectorAll("#pn-push-wrap");if(f.length>1)for(let h=1;h<f.length;h++)f[h].remove()}function A(){try{const g=function(){return document.getElementById("drawer-body")},f=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&z(),F()}),h=g();if(h)f.observe(h,{childList:!0,subtree:!0});else{const I=new MutationObserver(function(){const L=g();L&&(f.observe(L,{childList:!0,subtree:!0}),I.disconnect())});I.observe(document.body,{childList:!0,subtree:!0})}setTimeout(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&z(),F()},200)}catch{}}A()})();(function(){function e(){const a=document.getElementById("erp-map-show-advanced-btn");if(!a)return;const o=document.getElementById("erp-map-subtabs");if(!o)return;const s=o.classList.contains("show-advanced"),u=a.querySelector(".erp-map-adv-btn-label");if(u&&typeof t=="function"){const l=s?"erp-map-hide-advanced":"erp-map-show-advanced",k=t(l);k&&k!==l&&(u.textContent=k)}a.setAttribute("aria-pressed",s?"true":"false")}document.addEventListener("click",function(a){if(!a.target.closest("#erp-map-show-advanced-btn"))return;a.preventDefault();const s=document.getElementById("erp-map-subtabs");if(s&&(s.classList.toggle("show-advanced"),e(),!s.classList.contains("show-advanced")&&s.querySelector(".erp-map-subtab.active.erp-map-subtab-advanced"))){const l=s.querySelector('.erp-map-subtab[data-erp-subtab="clients"]');l&&l.click()}});function n(){e()}typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-map-advanced-toggle",n)})();(function(){const e="pearnly_erp_onboard_shown";let n=!1;function a(){try{return Array.isArray(window._erpEndpoints)&&window._erpEndpoints.length>0}catch{return!1}}function o(){if(document.getElementById("erp-onboard-mask"))return;const u=document.createElement("div");u.id="erp-onboard-mask",u.className="erp-onboard-mask",u.innerHTML='<div class="erp-onboard-modal" role="dialog" aria-modal="true"><div class="erp-onboard-icon"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="6" width="24" height="20" rx="3"/><path d="M9 13h14M9 18h10"/><path d="M22 22l3 3 5-5"/></svg></div><div class="erp-onboard-title" id="erp-onboard-title"></div><div class="erp-onboard-body" id="erp-onboard-body"></div><div class="erp-onboard-btns"><button type="button" class="btn btn-secondary" id="erp-onboard-later"></button><button type="button" class="btn btn-primary" id="erp-onboard-ok"></button></div></div>',document.body.appendChild(u);function l(){const i=document.getElementById("erp-onboard-title"),p=document.getElementById("erp-onboard-body"),c=document.getElementById("erp-onboard-ok"),r=document.getElementById("erp-onboard-later");i&&(i.textContent=t("erp-onboard-title")),p&&(p.textContent=t("erp-onboard-body")),c&&(c.textContent=t("erp-onboard-ok")),r&&(r.textContent=t("erp-onboard-later"))}l();function k(){u.style.display="none"}document.getElementById("erp-onboard-ok").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}k();try{const i=document.querySelector('#btn-add-endpoint, [data-action="erp-add-endpoint"]');i&&i.scrollIntoView({behavior:"smooth",block:"center"})}catch{}}),document.getElementById("erp-onboard-later").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}k()}),u.addEventListener("click",function(i){i.target===u&&k()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-onboard-modal",function(){u.style.display!=="none"&&l()})}function s(){if(!n){try{if(localStorage.getItem(e)==="1")return}catch{}a()||(n=!0,o(),requestAnimationFrame(function(){requestAnimationFrame(function(){if(a())return;const u=document.getElementById("erp-onboard-mask");u&&(u.style.display="flex")})}))}}document.addEventListener("click",function(u){const l=u.target.closest('.auto-nav-item[data-auto-tab="erp"]'),k=u.target.closest('.erp-subtab[data-erp-subtab="connect"]');(l||k)&&setTimeout(s,700)})})();(function(){const e={parse:{zh:"解析文件中",th:"กำลังอ่านไฟล์",en:"Parsing files",ja:"ファイル解析中"},report:{zh:"读取报告中",th:"กำลังอ่านรายงาน",en:"Reading report",ja:"レポート読込中"},reconcile:{zh:"对账中",th:"กำลังกระทบยอด",en:"Reconciling",ja:"照合中"},build:{zh:"生成中",th:"กำลังสร้างไฟล์",en:"Building",ja:"作成中"},persist:{zh:"保存中",th:"กำลังบันทึก",en:"Saving",ja:"保存中"},done:{zh:"完成",th:"เสร็จสิ้น",en:"Done",ja:"完了"}};window._reconProgressText=function(n,a){n=n||{},a=window._currentLang||a||localStorage.getItem("mrpilot_lang")||"th",e.parse[a]||(a="th");const o=n.stage||"parse",s=e[o]||e.parse,u=s[a]||s.th||s.en,l=n.stage_total,k=n.stage_done;if(o==="parse"&&Number.isFinite(l)&&l>0){const i={zh:"共 {d}/{t} 个文件",th:"{d}/{t} ไฟล์",en:"{d}/{t} files",ja:"{d}/{t} ファイル"}[a]||"{d}/{t} files";return u+" · "+i.replace("{d}",k||0).replace("{t}",l)}return u},window._reconPollJob=async function(n,a,o){o=o||{};const s=o.intervalMs||1500,u=o.maxMs||1200*1e3,l=Date.now();let k=0;for(;;){let i=null;try{const p=await fetch("/api/recon/jobs/"+encodeURIComponent(n),{headers:{Authorization:"Bearer "+a}});try{i=await p.json()}catch{i=null}(!p.ok||!i||!i.ok)&&(i=null)}catch{i=null}if(i){if(k=0,o.onProgress)try{o.onProgress(i.progress||{},i)}catch{}if(i.status==="done"||i.status==="failed"||i.status==="needs_review"||i.status==="needs_mapping")return i}else if(++k>=10)return{ok:!1,status:"failed",error_code:"poll_unreachable"};if(Date.now()-l>u)return{ok:!1,status:"timeout",error_code:"timeout"};await new Promise(p=>setTimeout(p,s))}}})();(function(){let e=!1,n=[],a=[],o=null,s="all",u=[],l={stmt:"",gl:""},k=[];const i=b=>document.getElementById(b);function p(b){if(b==null)return"—";const C=Number(b);return isNaN(C)?"—":C.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function c(b){return b?String(b).slice(0,10).split("-").reverse().join("/"):"—"}function r(b){return String(b||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function v(b,C){C=window._currentLang||C||"th";const T={stmt_headers_not_found:{zh:"认不出银行账单表头 · 请确认文件含日期/金额/余额列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตารางบัญชีธนาคารไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/จำนวนเงิน/ยอดคงเหลือ หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect bank statement headers · ensure the file has date/amount/balance columns, or re-upload as a clean Excel/CSV",ja:"銀行明細のヘッダーを認識できません · 日付/金額/残高列を確認するか、Excel/CSVに変換して再アップロードしてください"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含日期/科目/借方/贷方列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตาราง GL ไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต/เครดิต หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect GL headers · ensure the file has date/account/debit/credit columns, or re-upload as a clean Excel/CSV",ja:"GLのヘッダーを認識できません · 日付/科目/借方/貸方列を確認するか、Excel/CSVに変換して再アップロードしてください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水,或换更清晰的版本重传",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง หรือใช้เวอร์ชันที่ชัดเจนกว่า",en:"No transaction rows found · please upload the correct statement, or try a clearer version",ja:"取引データが見つかりません · 正しい明細をアップロードするか、より鮮明なファイルでお試しください"},no_rows:{zh:"解析后没有可对账的数据行 · 请确认文件内容完整,或换清晰版本重传",th:"ไม่มีแถวข้อมูลให้กระทบยอดหลังการอ่าน · ตรวจสอบความสมบูรณ์ของไฟล์ หรืออัปโหลดใหม่",en:"No reconcilable rows after parsing · check the file is complete, or re-upload a clearer version",ja:"解析後に照合可能な行がありません · ファイルの完全性を確認するか再アップロードしてください"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密 · 请换文件或转 PDF/Excel 重传",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส · ลองไฟล์อื่นหรือแปลงเป็น PDF/Excel",en:"File cannot be read · may be corrupted or encrypted · try another file or convert to PDF/Excel",ja:"ファイルを読み取れません · 破損または暗号化の可能性 · 別ファイルまたはPDF/Excelに変換してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロードしてください"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本,或转成 PDF / Excel / CSV 重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น PDF / Excel / CSV",en:"Could not read the file · try a clearer version, or convert to PDF / Excel / CSV",ja:"読み取りに失敗 · より鮮明なファイルか、PDF / Excel / CSV に変換して再試行してください"}},U={zh:"解析失败 · 请换更清晰的文件,或转成 Excel / CSV 后重新上传",th:"อ่านไฟล์ไม่สำเร็จ · ลองไฟล์ที่ชัดเจนกว่า หรือแปลงเป็น Excel / CSV แล้วอัปโหลดใหม่",en:"Parsing failed · try a clearer file, or convert to Excel / CSV and re-upload",ja:"解析に失敗しました · より鮮明なファイルか、Excel / CSV に変換して再アップロードしてください"},N=T[b]||U;return N[C]||N.th||N.en}function E(b){const C=b==="stmt"?n:a,T=i(`brv2-${b}-name`);if(T)if(C.length===0)T.textContent="";else{const N=window._currentLang||"zh",d={zh:"个文件",th:" ไฟล์",en:" file(s)",ja:" ファイル"};T.textContent=C.length+(d[N]||" 个文件")}const U=i("brv2-preview-panel");U&&U.style.display!=="none"&&D(b),x()}function x(){const b=i("brv2-toggle-preview"),C=i("brv2-preview-panel"),T=n.length+a.length>0;b&&(b.style.display=T?"":"none"),!T&&C&&(C.style.display="none",b&&b.classList.remove("open"))}function R(){D("stmt"),D("gl")}function D(b){const C=i(b==="stmt"?"brv2-pp-stmt-col":"brv2-pp-gl-col");if(!C)return;const T=b==="stmt"?n:a,U=window._currentLang||"zh",N={stmt:{zh:"① 银行账单",th:"① บัญชีธนาคาร",en:"① Bank Stmt",ja:"① 銀行明細"},gl:{zh:"② 总账 GL",th:"② GL รายงาน",en:"② GL Report",ja:"② GL帳簿"}},d=(N[b]||{})[U]||N[b].zh,j=r(window.t&&window.t("vex-preview-search")||"搜索文件名..."),O=r(window.t&&window.t("vex-preview-clear-all")||"全清"),J=l[b]||"";C.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+r(d)+' <span class="vex-pp-col-count">'+T.length+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="brv2-pp-search-'+b+'" type="text" placeholder="'+j+'" value="'+r(J)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="brv2-pp-clearall-'+b+'" type="button">'+O+'</button></div><div class="vex-pp-file-list" id="brv2-pp-'+b+'-list"></div><div class="vex-pp-pagination" id="brv2-pp-'+b+'-pg"></div>';const X=i("brv2-pp-search-"+b);X&&X.addEventListener("input",function(se){l[b]=se.target.value,w(b)});const de=i("brv2-pp-clearall-"+b);de&&de.addEventListener("click",function(){b==="stmt"?n.length=0:a.length=0,E(b),M()}),w(b)}function w(b){const C=i("brv2-pp-"+b+"-list"),T=i("brv2-pp-"+b+"-pg");if(!C)return;const U=b==="stmt"?n:a,N=(l[b]||"").toLowerCase(),d=N?U.filter(J=>J.name.toLowerCase().includes(N)):U.slice(),j='<svg class="vex-pp-fi-ico" viewBox="0 0 14 16" fill="none" stroke="currentColor" stroke-width="1.4" width="12" height="14"><path d="M3 1h6l3 3v11H3V1z"/><path d="M9 1v3h3"/></svg>',O='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" width="11" height="11"><path d="M2 4h10M5 4V2h4v2M5.5 7v4M8.5 7v4M3 4l1 8h6l1-8"/></svg>';if(C.innerHTML=d.map((J,X)=>'<div class="vex-pp-file-row">'+j+'<span class="vex-pp-fi-name" title="'+r(J.name)+'">'+r(J.name)+'</span><span class="vex-pp-fi-size">'+B(J.size)+'</span><button class="vex-pp-fi-del" type="button" data-zone="'+b+'" data-idx="'+U.indexOf(J)+'" aria-label="remove">'+O+"</button></div>").join(""),C.querySelectorAll(".vex-pp-fi-del").forEach(function(J){J.addEventListener("click",function(){const X=parseInt(J.dataset.idx,10);J.dataset.zone==="stmt"?n.splice(X,1):a.splice(X,1),E(J.dataset.zone),M()})}),T){const J=window.t&&window.t("vex-preview-count")||"显示 {n} / 共 {m}";T.textContent=J.replace("{n}",d.length).replace("{m}",U.length)}}function B(b){return b?b<1024?b+" B":b<1048576?(b/1024).toFixed(1)+" KB":(b/1048576).toFixed(1)+" MB":""}var z="pearnly.brv2.lastAnchorOcr";function q(b){try{var C=b&&b._anchor_ocr;if(!C||typeof C!="object")return;var T={stmt_opening:Number.isFinite(+C.stmt_opening)?+C.stmt_opening:null,gl_opening:Number.isFinite(+C.gl_opening)?+C.gl_opening:null,gl_closing:Number.isFinite(+C.gl_closing)?+C.gl_closing:null,stmt_closing:Number.isFinite(+C.stmt_closing)?+C.stmt_closing:null,ts:Date.now()};localStorage.setItem(z,JSON.stringify(T))}catch{}}function F(){try{var b=localStorage.getItem(z);if(!b)return null;var C=JSON.parse(b);return!C||typeof C!="object"?null:C}catch{return null}}function A(){var b=F();if(b){var C={"brv2-anchor-stmt-opening":b.stmt_opening,"brv2-anchor-gl-opening":b.gl_opening,"brv2-anchor-gl-closing":b.gl_closing,"brv2-anchor-stmt-closing":b.stmt_closing},T=0;Object.keys(C).forEach(function(O){var J=document.getElementById(O);if(J&&J.value===""){var X=C[O];if(Number.isFinite(X)){J.value=X.toFixed(2);var de=J.closest&&J.closest(".brv2-anchor-cell");de&&de.classList.add("is-prefilled"),T+=1}}});var U=document.getElementById("brv2-anchor-eq"),N=document.getElementById("brv2-anchor-eq-val");if(U&&N&&Number.isFinite(b.stmt_opening)&&Number.isFinite(b.gl_opening)){var d=b.stmt_opening-b.gl_opening;N.textContent=d.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),U.style.display=""}if(T>0){var j=document.getElementById("brv2-anchor-prefill-banner");j&&j.classList.add("show")}}}function g(){var b=document.getElementById("brv2-anchor-prefill-banner");if(b){var C=!1;["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"].forEach(function(T){var U=document.getElementById(T);if(U){var N=U.closest&&U.closest(".brv2-anchor-cell");N&&N.classList.contains("is-prefilled")&&(C=!0)}}),b.classList.toggle("show",C)}}var f=[["stmt_opening","brv2-anchor-stmt-opening"],["gl_opening","brv2-anchor-gl-opening"],["gl_closing","brv2-anchor-gl-closing"],["stmt_closing","brv2-anchor-stmt-closing"]];function h(b,C){return window.t&&window.t(b)||C}function I(b){return String(b??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function L(b){return Number.isFinite(+b)?(+b).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—"}function H(b){var C=document.getElementById("brv2-summary-collapse");if(!(!C||!C.parentNode)){var T=document.getElementById("brv2-anchor-audit"),U=b&&b._anchor_overrides;if(!U||typeof U!="object"||Object.keys(U).length===0){T&&T.parentNode&&T.parentNode.removeChild(T);return}T||(T=document.createElement("div"),T.id="brv2-anchor-audit",T.style.cssText="margin-top:14px;background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:14px 16px;",C.parentNode.insertBefore(T,C.nextSibling));var N=f.map(function(d){var j=U[d[0]];if(!j)return"";var O=+j.ocr||0,J=+j.user||0,X=J-O,de=X>0?"+":(X<0,""),se=Math.abs(X)<.005?"#6b7280":X>0?"#16a34a":"#dc2626";return'<tr><td style="padding:6px 10px;color:#111827;font-size:13px">'+I(h(d[1],d[0]))+'</td><td style="padding:6px 10px;color:#6b7280;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+I(L(O))+'</td><td style="padding:6px 10px;background:#fef08a;color:#92400e;font-weight:600;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+I(L(J))+'</td><td style="padding:6px 10px;color:'+se+';font-weight:500;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+I(de+L(X))+"</td></tr>"}).join("");T.innerHTML='<div style="font-weight:600;color:#92400e;font-size:13px;margin-bottom:10px">'+I(h("brv2-anchor-audit-title","⚠ This run contains manually entered anchors"))+'</div><table style="width:100%;border-collapse:collapse;font-family:inherit"><thead><tr><th style="padding:6px 10px;text-align:left;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+I(h("brv2-anchor-audit-col-field","Field"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+I(h("brv2-anchor-audit-col-ocr","OCR"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+I(h("brv2-anchor-audit-col-user","User"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+I(h("brv2-anchor-audit-col-diff","Diff"))+"</th></tr></thead><tbody>"+N+"</tbody></table>"}}function _(){const b=i("brv2-toggle-preview");b&&!b._reconBound&&(b._reconBound=!0,b.addEventListener("click",function(){const C=i("brv2-preview-panel"),T=i("brv2-toggle-preview-label"),U=C&&C.style.display!=="none";C&&(C.style.display=U?"none":""),b.classList.toggle("open",!U),T&&(T.textContent=U?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),U||R()}))}function M(){const b=i("brv2-run-btn"),C=i("brv2-status"),T=n.length>0,U=a.length>0;if(b&&(b.disabled=!(T&&U)),C){const N=window._currentLang||"zh";if(!T&&!U){const d={zh:"请上传银行账单和 GL 文件",th:"กรุณาอัปโหลดบัญชีธนาคารและ GL",en:"Upload bank statement and GL files",ja:"銀行明細と GL を両方アップロードしてください"};C.textContent=d[N]||d.zh}else if(T)if(U){const d={zh:"两份文件已就绪",th:"พร้อมสอบทาน",en:"Ready to reconcile",ja:"照合を開始できます"};C.textContent=d[N]||d.zh}else{const d={zh:"还缺 GL 文件",th:"ยังขาดไฟล์ GL",en:"Missing GL file",ja:"GL ファイルが未アップロード"};C.textContent=d[N]||d.zh}else{const d={zh:"还缺银行账单 PDF",th:"ยังขาดไฟล์บัญชีธนาคาร PDF",en:"Missing bank statement PDF",ja:"銀行明細 PDF が未アップロード"};C.textContent=d[N]||d.zh}}}function K(b,C,T){const U=i(b),N=i(C);!U||!N||(U.addEventListener("click",()=>N.click()),U.addEventListener("keydown",d=>{(d.key==="Enter"||d.key===" ")&&(d.preventDefault(),N.click())}),U.addEventListener("dragover",d=>{d.preventDefault(),U.classList.add("drag-over")}),U.addEventListener("dragleave",()=>U.classList.remove("drag-over")),U.addEventListener("drop",d=>{d.preventDefault(),U.classList.remove("drag-over");const j=Array.from(d.dataTransfer.files||[]);T==="stmt"?n.push(...j):a.push(...j),E(T),M()}),N.addEventListener("change",()=>{const d=Array.from(N.files||[]);T==="stmt"?n.push(...d):a.push(...d),N.value="",E(T),M()}))}function G(b){const C=i("brv2-progress"),T=i("brv2-run-btn"),U=i("brv2-error");C&&(C.style.display=b?"":"none"),T&&(T.disabled=b),U&&(U.style.display="none")}function W(b){const C=i("brv2-error");C&&(C.textContent=b,C.style.display="",C.scrollIntoView({behavior:"smooth",block:"nearest"})),G(!1),M(),window.showToast&&window.showToast(b,"error")}async function te(){if(n.length===0||a.length===0)return;const b=localStorage.getItem("mrpilot_token")||"",C=window._currentLang||"zh",T=(i("brv2-acct-select")||{}).value||"";S(!1),G(!0);try{const U=new FormData;n.forEach(ae=>U.append("stmt_files",ae)),a.forEach(ae=>U.append("gl_files",ae)),U.append("gl_account",T),U.append("lang",C);const N=parseFloat((i("brv2-anchor-gl-closing")||{}).value),d=parseFloat((i("brv2-anchor-stmt-closing")||{}).value),j=parseFloat((i("brv2-anchor-stmt-opening")||{}).value),O=parseFloat((i("brv2-anchor-gl-opening")||{}).value);Number.isFinite(N)&&U.append("gl_closing_override",N),Number.isFinite(d)&&U.append("stmt_closing_override",d),Number.isFinite(j)&&U.append("stmt_opening_override",j),Number.isFinite(O)&&U.append("gl_opening_override",O);const J=await fetch("/api/recon/bank-v2/submit",{method:"POST",headers:{Authorization:"Bearer "+b},body:U});let X=null;try{X=await J.json()}catch{X=null}if(X&&X.needs_mapping){G(!1),window.ReconMapping?window.ReconMapping.show(X,{token:b,lang:C,onConfirmed:function(){te()}}):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(!J.ok||!X||!X.ok||!X.job_id){G(!1),X&&(X.detail||X.error)?W(_humanizeBackendError(X.detail||X.error,"Error "+J.status)):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const de=i("brv2-progress-sub"),se=await window._reconPollJob(X.job_id,b,{onProgress:ae=>{de&&(de.textContent=window._reconProgressText(ae,C))}});if(se&&se.status==="needs_mapping"&&se.mapping){G(!1),window.ReconMapping?window.ReconMapping.show(se.mapping,{token:b,lang:C,onConfirmed:function(){te()}}):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(se&&se.status==="needs_review"&&se.review){G(!1),window.ReconReview?window.ReconReview.show(se.review,{token:b,lang:C,jobId:X.job_id,onConfirmed:async function(ae){G(!0);const pe=await window._reconPollJob(ae,b,{onProgress:ve=>{de&&(de.textContent=window._reconProgressText(ve,C))}});await ce(pe)}}):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(se&&se.status==="failed"){G(!1),W(v(se.error_code,C));return}await ce(se);async function ce(ae){try{if(!ae||ae.status!=="done"||!ae.result_id){G(!1),W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const pe=await fetch("/api/recon/bank-v2/"+encodeURIComponent(ae.result_id),{headers:{Authorization:"Bearer "+b}});let ve=null;try{ve=await pe.json()}catch{ve=null}if(!pe.ok||ve===null||!ve.ok){G(!1),W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}(ve.gl_accounts||[]).length>1&&re(ve.gl_accounts),o=ve,u=ve.detail||[],s="all",document.querySelectorAll(".brv2-filter-btn").forEach(ge=>ge.classList.toggle("active",ge.dataset.filter==="all")),q(ve&&ve.summary),G(!1),P(ve),Z();const fe=i("brv2-summary-collapse");fe&&fe.scrollIntoView({behavior:"smooth",block:"nearest"})}catch(pe){G(!1),W(pe.message||"Network error")}}}catch(U){W(U.message||"Network error")}}function re(b){const C=i("brv2-acct-select");if(!C)return;const T=window._currentLang||"zh",U={zh:"全部账户",th:"ทุกบัญชี",en:"All Accounts",ja:"すべての口座"}[T]||"全部账户";C.innerHTML=`<option value="">${U}</option>`+b.map(N=>`<option value="${r(N)}">${r(N)}</option>`).join(""),C.style.display=""}function S(b){const C=i("brv2-summary-collapse"),T=i("brv2-detail-collapse"),U=i("brv2-export-btn"),N=i("brv2-new-btn"),d=i("brv2-parse-info-wrap");C&&(C.style.display=b?"":"none"),T&&(T.style.display=b?"":"none"),U&&(U.style.display=b?"":"none"),N&&(N.style.display=b?"":"none"),!b&&d&&(d.style.display="none");const j=i("brv2-warnings");!b&&j&&(j.style.display="none",j.innerHTML="")}function y(b){const C=i("brv2-parse-info-wrap"),T=i("brv2-parse-info-body");if(!C||!T)return;const U=b.parse_info;if(!U){C.style.display="none";return}const N=window._currentLang||"zh",d={title:{zh:"文件解析状态",th:"สถานะการอ่านไฟล์",en:"File Parse Status",ja:"ファイル解析状態"},type:{zh:"类型",th:"ประเภท",en:"Type",ja:"種別"},file:{zh:"文件名",th:"ชื่อไฟล์",en:"File",ja:"ファイル"},rows:{zh:"解析行数",th:"แถวที่พบ",en:"Rows Found",ja:"解析行数"},bank:{zh:"银行/科目",th:"ธนาคาร/บัญชี",en:"Bank/Account",ja:"銀行/科目"},status:{zh:"状态",th:"สถานะ",en:"Status",ja:"状態"},stmt:{zh:"账单",th:"บัญชีธนาคาร",en:"Stmt",ja:"明細"},gl:{zh:"总账GL",th:"GL",en:"GL",ja:"GL"},ok:{zh:"✓ 成功",th:"✓ สำเร็จ",en:"✓ OK",ja:"✓ 成功"},warn:{zh:"⚠ 0行",th:"⚠ 0 แถว",en:"⚠ 0 rows",ja:"⚠ 0行"},fail:{zh:"✗ 失败",th:"✗ ล้มเหลว",en:"✗ Failed",ja:"✗ 失敗"}},j=ce=>(d[ce]||{})[N]||(d[ce]||{}).zh||ce,O=[...(U.stmt_files||[]).map(ce=>({...ce,_type:"stmt",_extra:ce.bank_code||""})),...(U.gl_files||[]).map(ce=>({...ce,_type:"gl",_extra:(ce.accounts||[]).join(", ")}))],J={stmt_headers_not_found:{zh:"认不出表头列 · 请确认文件含日期/金额/余额列",th:"หาคอลัมน์หัวตารางไม่เจอ · ตรวจสอบไฟล์มีวันที่/จำนวนเงิน/ยอดคงเหลือ",en:"Cannot detect column headers · ensure file has date/amount/balance columns",ja:"列ヘッダーが認識できません · 日付/金額/残高列を確認してください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง",en:"No transaction rows found · please check the file",ja:"取引データが見つかりません · ファイルを確認してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロード"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส",en:"File cannot be read · may be corrupted or encrypted",ja:"ファイルを読み取れません · 破損または暗号化の可能性"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本或换 PDF 格式重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่าหรือเปลี่ยนเป็น PDF",en:"Could not read file · try a clearer version or upload as PDF",ja:"読み取り失敗 · より鮮明なファイルまたは PDF 形式で再試行"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含科目/借方/贷方列",th:"หาหัวคอลัมน์ GL ไม่เจอ · ตรวจสอบมีคอลัมน์บัญชี/เดบิต/เครดิต",en:"Cannot detect GL column headers · ensure account/debit/credit columns exist",ja:"GL 列ヘッダー認識不可 · 科目/借方/貸方列を確認してください"}},X=ce=>{const ae=String(ce||"");return/Cannot detect bank statement column headers/i.test(ae)?"stmt_headers_not_found":/Cannot detect GL column headers/i.test(ae)?"gl_headers_not_found":/No transaction rows found|no pages parsed/i.test(ae)?"stmt_no_rows":/unsupported format/i.test(ae)?"file_not_supported":/Cannot read Excel|file_unreadable/i.test(ae)?"file_unreadable":/Gemini.*invalid JSON|Gemini.*parsed but failed|validation errors|BankStatementDocument schema|layer2:|layer1:/i.test(ae)?"ocr_failed":null},de=ce=>{const ae=ce.error_code||X(ce.error);if(ae&&J[ae]){const pe=window._currentLang||"zh";return J[ae][pe]||J[ae].zh}return String(ce.error||"").slice(0,80)},se=ce=>!ce.ok&&ce.error?`<span style="color:#dc2626">${j("fail")} — ${r(de(ce))}</span>`:ce.rows?`<span style="color:#059669">${j("ok")} (${ce.rows})</span>`:`<span style="color:#d97706">${j("warn")}</span>`;T.innerHTML=`
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
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${r(ce.file||"")}">${r(ce.file||"")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;text-align:center">${ce.rows||0}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;color:var(--ink-2)">${r(ce._extra||"")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb">${se(ce)}</td>
                    </tr>`).join("")}
                </tbody>
            </table>`,C.style.display=""}async function m(b){const C=localStorage.getItem("mrpilot_token")||"",T=window._currentLang||"zh";try{const U=await fetch("/api/recon/bank-v2/"+b+"/export?lang="+T,{headers:{Authorization:"Bearer "+C}});if(!U.ok){const de=await U.json().catch(()=>({}));window.showToast&&window.showToast(de.detail||"Export failed","error");return}const N=await U.blob(),j=(U.headers.get("content-disposition")||"").match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/),O=j?j[1].replace(/['"]/g,""):"reconciliation.xlsx",J=URL.createObjectURL(N),X=document.createElement("a");X.href=J,X.download=O,document.body.appendChild(X),X.click(),document.body.removeChild(X),URL.revokeObjectURL(J)}catch(U){window.showToast&&window.showToast("Export error: "+U.message,"error")}}function $(b,C){const T=i("brv2-summary-collapse");let U=i("brv2-warnings");const N=window._currentLang||"zh",d={zh:"⏭ 已跳过无法识别的文件:",th:"⏭ ข้ามไฟล์ที่อ่านไม่ได้:",en:"⏭ Skipped unreadable file:",ja:"⏭ 読み取れないファイルをスキップ:"}[N]||"⏭ ",j=[];if((C||[]).forEach(O=>j.push(d+" "+O)),(b||[]).forEach(O=>j.push(O)),!j.length){U&&(U.style.display="none");return}if(!U)if(U=document.createElement("div"),U.id="brv2-warnings",T&&T.parentNode)T.parentNode.insertBefore(U,T);else return;U.style.cssText="display:block;margin:10px 0;padding:10px 14px;background:#FEF3C7;border:1px solid #FCD34D;border-radius:8px;color:#92400E;font-size:13px;line-height:1.6",U.innerHTML=j.map(O=>"<div>"+r(O)+"</div>").join("")}function P(b){y(b),$(b.warnings||[],b.skipped_files||[]),!b.ok&&b.error&&window.showToast&&window.showToast(b.error,"error");const C=b.stats||{},T=b.summary||{},U=C.matched||0,N=(C.gl_debit_only||0)+(C.gl_credit_only||0),d=(C.stmt_withdrawal_only||0)+(C.stmt_deposit_only||0),j=Number(T.formula_diff||0),O=Math.abs(j)<.05;i("brv2-kpi-matched")&&(i("brv2-kpi-matched").textContent=U),i("brv2-kpi-diff")&&(i("brv2-kpi-diff").textContent=p(j)),i("brv2-kpi-unmatched")&&(i("brv2-kpi-unmatched").textContent=N+d);const J=i("brv2-kpi-diff-icon");J&&(J.style.background=O?"#d1fae5":"#fee2e2",J.style.color=O?"#065f46":"#b91c1c");const X=i("brv2-formula-sub");if(X){const pe=window._currentLang||"zh";X.textContent=O?{zh:"✓ 平衡",th:"✓ สมดุล",en:"✓ Balanced",ja:"✓ 一致"}[pe]||"✓ 平衡":({zh:"差 ",th:"ต่าง ",en:"Diff ",ja:"差 "}[pe]||"差 ")+p(j)}const de=i("brv2-detail-sub");if(de){const pe=window._currentLang||"zh",ve={zh:"共 {n} 行",th:"ทั้งหมด {n} แถว",en:"{n} rows",ja:"計 {n} 行"}[pe]||"共 {n} 行";de.textContent=ve.replace("{n}",u.length)}function se(pe,ve,fe){const ge=i(pe);ge&&(ge.textContent=(fe&&ve>0?"(":"")+p(fe?-ve:ve)+(fe&&ve>0?")":""))}se("brf-gl-close",T.gl_closing||0),se("brf-open-diff",T.opening_diff||0),se("brf-gl-debit-only",T.gl_debit_only_amount||0,!0),se("brf-gl-credit-only",T.gl_credit_only_amount||0),se("brf-stmt-wd-only",T.stmt_withdrawal_only_amount||0,!0),se("brf-stmt-dep-only",T.stmt_deposit_only_amount||0),se("brf-calc-close",T.formula_stmt_closing||0),se("brf-stmt-close",T.stmt_closing||0),i("brf-diff")&&(i("brf-diff").textContent=p(j));const ce=i("brv2-fcell-diff");ce&&ce.classList.toggle("brv2-fcell-diff-ok",O);const ae=i("brv2-export-btn");ae&&(ae.onclick=()=>{o&&m(o.task_id)}),H(T),S(!0),Y()}function Y(){const b=i("brv2-tbody");if(!b)return;const C=u.filter(d=>s==="all"?!0:s==="matched"?d.match_status==="matched":s==="gl_only"?d.match_status.startsWith("gl_"):s==="stmt_only"?d.match_status.startsWith("stmt_"):!0);if(C.length===0){const d={zh:"无记录",th:"ไม่มีรายการ",en:"No rows",ja:"行なし"}[window._currentLang||"zh"]||"无记录";b.innerHTML=`<tr><td colspan="10" style="text-align:center;padding:20px;color:var(--ink-3)">${d}</td></tr>`;return}const T=window._currentLang||"zh",U={zh:"OCR 余额验证未通过 · 上一行余额 ± 金额 ≠ 本行余额，请核对原 PDF",th:"การตรวจสอบยอดคงเหลือไม่ผ่าน · ยอดก่อนหน้า ± จำนวน ≠ ยอดบรรทัดนี้ โปรดตรวจสอบ PDF ต้นฉบับ",en:"Balance check FAILED · prev_balance ± amount ≠ this row balance — verify against the original PDF",ja:"残高検証エラー · 前残高 ± 金額 ≠ この行残高 — 元のPDFと照合してください"}[T],N={zh:"OCR 低置信度 · 数字模糊或难以辨认，请核对原 PDF",th:"OCR ความมั่นใจต่ำ · ตัวเลขเบลอหรืออ่านยาก โปรดตรวจสอบ PDF ต้นฉบับ",en:"OCR low confidence · digit was blurry or hard to read — verify against the original PDF",ja:"OCR信頼度低 · 数字がぼやけている — 元のPDFと照合してください"}[T];b.innerHTML=C.map(d=>{const j=d.match_status,O=d.match_layer;let J="",X="";j==="matched"?(O===1&&(J="matched",X='<span class="brv2-status-badge brv2-badge-matched">L1 ✓</span>'),O===2&&(J="matched-l2",X='<span class="brv2-status-badge brv2-badge-matched-l2">L2 ~</span>'),O===3&&(J="matched-l3",X='<span class="brv2-status-badge brv2-badge-matched-l3">L3 ?</span>')):j==="gl_debit_only"||j==="gl_credit_only"?(J="gl-only",X='<span class="brv2-status-badge brv2-badge-gl-only">GL</span>'):(J="stmt-only",X=`<span class="brv2-status-badge brv2-badge-stmt-only">${{zh:"账单",th:"บัญชี",en:"Stmt",ja:"明細"}[T]||"账单"}</span>`);let de="";return d.stmt_balance_ok===!1&&(de+=`<span class="brv2-ocr-warn brv2-ocr-warn-bal" title="${r(U)}">⚠</span>`,J+=" brv2-row-warn"),d.stmt_confidence==="low"&&(de+=`<span class="brv2-ocr-warn brv2-ocr-warn-conf" title="${r(N)}">◌</span>`,J.includes("brv2-row-warn")||(J+=" brv2-row-warn-soft")),`<tr class="${J.trim()}">
              <td>${X}${de}</td>
              <td>${r(c(d.stmt_date))}</td>
              <td title="${r(d.stmt_desc)}" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${r(d.stmt_desc)}</td>
              <td class="num">${d.stmt_withdrawal?p(d.stmt_withdrawal):""}</td>
              <td class="num">${d.stmt_deposit?p(d.stmt_deposit):""}</td>
              <td>${r(c(d.gl_date))}</td>
              <td title="${r(d.gl_doc_no)}" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${r(d.gl_doc_no)}</td>
              <td class="num">${d.gl_debit?p(d.gl_debit):""}</td>
              <td class="num">${d.gl_credit?p(d.gl_credit):""}</td>
              <td>${O?"L"+O:"—"}</td>
            </tr>`}).join("")}async function Z(){const b=localStorage.getItem("mrpilot_token")||"";try{const T=await(await fetch("/api/recon/bank-v2/tasks",{headers:{Authorization:"Bearer "+b}})).json();ee(T.tasks||[])}catch{const T=i("brv2-history-empty"),U=window._currentLang||"zh",N={zh:"加载失败",th:"โหลดประวัติไม่ได้",en:"Load failed",ja:"読み込み失敗"}[U]||"加载失败";T&&(T.textContent=N,T.style.display="");const d=i("brv2-history-table-wrap");d&&(d.style.display="none")}}const le=10;let ie=1;function V(){const b=i("brv2-history-pager"),C=i("brv2-history-pager-info"),T=i("brv2-history-prev"),U=i("brv2-history-next");if(!b)return;if(k.length<=le){b.style.display="none";return}b.style.display="";const N=Math.ceil(k.length/le);C&&(C.textContent=ie+" / "+N),T&&(T.disabled=ie<=1),U&&(U.disabled=ie>=N)}function Q(){const b=i("brv2-history-prev"),C=i("brv2-history-next");b&&!b._brv2Bound&&(b._brv2Bound=!0,b.addEventListener("click",()=>{ie>1&&(ie--,ee(k))})),C&&!C._brv2Bound&&(C._brv2Bound=!0,C.addEventListener("click",()=>{const T=Math.ceil(k.length/le);ie<T&&(ie++,ee(k))}))}function ee(b){b!==void 0&&(k=b||[],ie=1);const C=k,T=i("brv2-history-empty"),U=i("brv2-history-table-wrap"),N=i("brv2-history-tbody");if(!N)return;const d=window._currentLang||"zh";if(!C.length){const ae={zh:"暂无对账记录",th:"ยังไม่มีประวัติ",en:"No records yet",ja:"記録なし"}[d]||"暂无对账记录";T&&(T.textContent=ae,T.style.display=""),U&&(U.style.display="none"),V();return}T&&(T.style.display="none"),U&&(U.style.display="");const j=Math.ceil(C.length/le);ie>j&&(ie=j);const O=(ie-1)*le,J=C.slice(O,O+le),X=localStorage.getItem("mrpilot_token")||"",de='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><circle cx="8" cy="8" r="6"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',se='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',ce='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';N.innerHTML="",J.forEach(ae=>{const pe=Number(ae.formula_diff||0),ve=Math.abs(pe)<.05,fe=(ae.stmt_files||"").split(";").map(ke=>ke.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),ge=(ae.gl_files||"").split(";").map(ke=>ke.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),be=ae.created_at?String(ae.created_at).slice(0,16).replace("T"," "):"",xe=document.createElement("tr");xe.dataset.taskId=ae.id;const De=document.createElement("td");De.textContent=be;const Le=document.createElement("td");Le.className="glv-history-file",Le.title=fe+" + "+ge,Le.textContent=fe+" + "+ge;const Ce=document.createElement("td");Ce.className="glv-num",Ce.textContent=(ae.stmt_row_count||0)+" / "+(ae.gl_row_count||0);const Ve=document.createElement("td");Ve.className="glv-num",Ve.textContent=ae.matched_count||0;const Ue=document.createElement("td");Ue.className="glv-num",Ue.textContent=ae.unmatched_gl||0;const Ge=document.createElement("td");Ge.className="glv-num",Ge.textContent=ae.unmatched_stmt||0;const qe=document.createElement("td");qe.className="glv-num",qe.style.color=ve?"#059669":"#dc2626",qe.textContent=ve?"✓":p(pe);const Se=document.createElement("td");Se.className="glv-history-actions";const Ye=(ke,tt,nt,Tt)=>{const Ee=document.createElement("button");return Ee.type="button",Ee.title=tt,Ee.setAttribute("aria-label",tt),nt&&(Ee.className=nt),Ee.innerHTML=ke,Ee.onclick=Mt=>{Mt.stopPropagation(),Tt()},Ee},It={zh:"删除这条记录?",th:"ลบรายการนี้?",en:"Delete this record?",ja:"この記録を削除しますか?"}[d]||"删除?",Lt={zh:"加载",th:"โหลด",en:"Load",ja:"読込"}[d]||"加载",Ct={zh:"导出",th:"ส่งออก",en:"Export",ja:"エクスポート"}[d]||"导出",St={zh:"删除",th:"ลบ",en:"Delete",ja:"削除"}[d]||"删除";Se.appendChild(Ye(de,Lt,"",()=>oe(ae.id,X))),Se.appendChild(Ye(se,Ct,"",()=>m(ae.id))),Se.appendChild(Ye(ce,St,"glv-del",async()=>{await showConfirm(It,{danger:!0})&&(await fetch("/api/recon/bank-v2/"+ae.id,{method:"DELETE",headers:{Authorization:"Bearer "+X}}),Z())})),[De,Le,Ce,Ve,Ue,Ge,qe,Se].forEach(ke=>xe.appendChild(ke)),xe.style.cursor="pointer",xe.addEventListener("click",async ke=>{ke.target.closest(".glv-del")||ke.target.closest("button")||await oe(ae.id,X)}),N.appendChild(xe)}),V(),ne()}function ne(){const b=((i("brv2-hist-search")||{}).value||"").trim().toLowerCase(),C=i("brv2-history-tbody");C&&C.querySelectorAll("tr").forEach(T=>{T.dataset.taskId&&(T.style.display=!b||T.textContent.toLowerCase().includes(b)?"":"none")})}async function oe(b,C){try{const U=await(await fetch("/api/recon/bank-v2/"+b,{headers:{Authorization:"Bearer "+C}})).json();if(!U.ok)return;o={task_id:U.task_id,...U},u=U.detail||[],s="all",document.querySelectorAll(".brv2-filter-btn").forEach(N=>N.classList.toggle("active",N.dataset.filter==="all")),P(o)}catch{}}function ue(){if(e){Z();return}e=!0,K("brv2-stmt-zone","brv2-stmt-input","stmt"),K("brv2-gl-zone","brv2-gl-input","gl");const b=["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"];function C(){const O=parseFloat((i("brv2-anchor-stmt-opening")||{}).value),J=parseFloat((i("brv2-anchor-gl-opening")||{}).value),X=i("brv2-anchor-eq"),de=i("brv2-anchor-eq-val");if(!(!X||!de))if(Number.isFinite(O)&&Number.isFinite(J)){const se=O-J;de.textContent=se.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),X.style.display=""}else X.style.display="none"}b.forEach(O=>{const J=i(O);J&&(J.addEventListener("input",C),J.addEventListener("input",()=>{const X=J.closest(".brv2-anchor-cell");X&&X.classList.remove("is-prefilled"),g()}))}),A();const T=i("brv2-run-btn");T&&T.addEventListener("click",te);const U=i("brv2-reset-btn");U&&U.addEventListener("click",()=>{o=null,u=[],n=[],a=[],E("stmt"),E("gl"),M(),S(!1);const O=i("brv2-acct-select");O&&(O.style.display="none"),b.forEach(de=>{const se=i(de);if(se){se.value="";const ce=se.closest&&se.closest(".brv2-anchor-cell");ce&&ce.classList.remove("is-prefilled")}});const J=i("brv2-anchor-eq");J&&(J.style.display="none");const X=i("brv2-anchor-prefill-banner");X&&X.classList.remove("show")});const N=i("brv2-new-btn");N&&N.addEventListener("click",()=>{o=null,u=[],n=[],a=[],E("stmt"),E("gl"),M(),S(!1)});const d=i("brv2-filter-tabs");d&&d.addEventListener("click",O=>{O.stopPropagation();const J=O.target.closest(".brv2-filter-btn");J&&(s=J.dataset.filter,d.querySelectorAll(".brv2-filter-btn").forEach(X=>X.classList.toggle("active",X===J)),Y())}),_(),Q();const j=i("brv2-hist-search");j&&j.addEventListener("input",ne),Z(),M(),window._brv2LoadHistory=Z,Array.isArray(window.__i18nSubs)||(window.__i18nSubs=[]),window.__i18nSubs=window.__i18nSubs.filter(O=>O.name!=="brv2"),window.__i18nSubs.push({name:"brv2",fn:function(){M(),E("stmt"),E("gl"),o&&P(o),ee()}})}window._loadBankReconV2Panel=function(b){const C=b?document.getElementById(b):null;C&&C.id!=="recon-pane-bank"&&(C.innerHTML=`<div style="padding:16px;font-size:13px;color:var(--ink-3)">
                银行对账 v2 · 请前往对账中心使用</div>`),ue()},document.addEventListener("DOMContentLoaded",()=>{i("brv2-run-btn")&&ue()}),window._bankReconV2Init=ue})();(function(){const e=document.getElementById("general-lang");if(!e)return;e.addEventListener("change",a=>{const o=a.target.value;o&&applyLang(o)});const n=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";e.value=n})();(function(){const n="pearnly_general_tz",a="pearnly_general_date_format",o="pearnly_general_number_format",s={tz:"Asia/Bangkok",date:"YYYY-MM-DD",number:"comma_dot"};function u(){const p=document.getElementById("general-tz"),c=document.getElementById("general-date"),r=document.getElementById("general-number");if(!(!p||!c||!r))try{p.value=localStorage.getItem(n)||s.tz,c.value=localStorage.getItem(a)||s.date,r.value=localStorage.getItem(o)||s.number}catch{p.value=s.tz,c.value=s.date,r.value=s.number}}async function l(){const p=document.getElementById("btn-save-general"),c=document.getElementById("general-save-msg");if(!p)return;const r=p.innerHTML;p.disabled=!0,p.innerHTML="<span>"+(t("msg-saving")||"保存中...")+"</span>",c&&(c.textContent="",c.classList.remove("error"));try{const v=(document.getElementById("general-tz")||{}).value||s.tz,E=(document.getElementById("general-date")||{}).value||s.date,x=(document.getElementById("general-number")||{}).value||s.number;try{localStorage.setItem(n,v),localStorage.setItem(a,E),localStorage.setItem(o,x)}catch{}window._pearnlyGeneral={tz:v,date_format:E,number_format:x},c&&(c.textContent=t("msg-saved")||"已保存")}catch{c&&(c.textContent=t("msg-save-failed")||"保存失败",c.classList.add("error"))}finally{p.disabled=!1,p.innerHTML=r,setTimeout(function(){c&&(c.textContent="")},3e3)}}function k(){const p=document.getElementById("btn-save-general");if(!p){setTimeout(k,200);return}p._pearnlyGenBound||(p._pearnlyGenBound=!0,p.addEventListener("click",l),u())}function i(){u();const p=document.getElementById("general-lang");if(p){const c=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";p.value=c}}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",k):k(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("settings-general",i)})();(function(){const e="mrpilot_nav_collapsed",n={ocr:"sales",history:"sales",reconcile:"sales","sales-invoices":"sales",receivables:"sales",vouchers:"expense"};function a(){try{const l=localStorage.getItem(e);return l?JSON.parse(l):{}}catch{return{}}}function o(l){try{localStorage.setItem(e,JSON.stringify(l))}catch{}}function s(){const l=a();document.querySelectorAll(".nav-collapsible").forEach(function(k){const i=k.dataset.collapsible;l[i]?k.classList.add("collapsed"):k.classList.remove("collapsed")})}function u(l){const k=a();k[l]=!k[l],o(k),s()}(function(){const k=a();let i=!1;k.sales===void 0&&(k.sales=!1,i=!0),k.expense===void 0&&(k.expense=!0,i=!0),i&&o(k)})(),s(),document.querySelectorAll(".nav-group-toggle").forEach(function(l){l.addEventListener("click",function(){u(l.dataset.toggleGroup)})}),window.expandNavGroupForRoute=function(l){const k=n[l];if(!k)return;const i=a();i[k]&&(i[k]=!1,o(i),s())}})();const Xt=`
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
    </div>`;function it(){const e=document.getElementById("help-modal");if(!e||e.children.length)return;e.innerHTML=Xt;const n=window._currentLang||"th",a=window.I18N&&window.I18N[n]||{};e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[s]&&(o.textContent=a[s])})}document.readyState,it();(function(){function e(){const n=document.getElementById("help-modal"),a=document.getElementById("help-modal-close");n&&(a&&!a.dataset.bound&&(a.addEventListener("click",function(){n.style.display="none"}),a.dataset.bound="1"),n.dataset.maskBound||(n.addEventListener("click",function(o){o.target===n&&(n.style.display="none")}),n.dataset.maskBound="1"),window._helpModalEscBound||(document.addEventListener("keydown",function(o){o.key==="Escape"&&n.style.display==="flex"&&(n.style.display="none")}),window._helpModalEscBound=!0))}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",e):e()})();(function(){const e={line:"line",folder:"folder",gmail:"email",erp:"erp",alert:"alert"};document.addEventListener("click",function(n){const a=n.target.closest(".int-btn-configure");if(!a)return;const o=a.closest(".integration-row"),s=o?o.dataset.intAnchor:null;if(s&&e[s]){const u=o.querySelector(".int-name"),l=u?(u.textContent||u.innerText||"").trim():"配置";typeof window.openIntegrationDrawer=="function"&&window.openIntegrationDrawer(e[s],l)}})})();let we=[];window._erpEndpoints=we;let je=null;async function Oe(){try{const e=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(e.status===401){localStorage.removeItem("mrpilot_token");const a=await e.json().catch(()=>({}));if((typeof a.detail=="string"?a.detail:a.detail&&a.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}we=(await e.json()).items||[],window._erpEndpoints=we,gt()}catch(e){console.error("load endpoints failed",e)}}window._refreshErpEndpointsCache=function(){return Oe()};async function ht(){const e=document.getElementById("erp-today-stats");if(e){e.innerHTML="";try{const n=await fetch("/api/erp/stats/today",{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=a.total||0,s=a.success||0,u=a.failed||0,l=a.auto_cnt||0;if(o===0){e.innerHTML=`<span class="erp-today-empty">${escapeHtml(t("erp-today-none"))}</span>`;return}const k=[];k.push(`<span class="erp-today-item"><strong>${o}</strong> ${escapeHtml(t("erp-today-total"))}</span>`),s>0&&k.push(`<span class="erp-today-item ok"><strong>${s}</strong> ${escapeHtml(t("erp-today-success"))}</span>`),u>0&&k.push(`<span class="erp-today-item fail"><strong>${u}</strong> ${escapeHtml(t("erp-today-failed"))}</span>`),l>0&&k.push(`<span class="erp-today-item auto"><strong>${l}</strong> ${escapeHtml(t("erp-today-auto"))}</span>`),e.innerHTML=k.join("")}catch(n){console.warn("loadErpTodayStats failed",n)}}}function gt(){const e=document.getElementById("erp-endpoints-list"),n=document.getElementById("erp-status-summary"),a=document.getElementById("btn-add-endpoint");if(!e){console.warn("erp-endpoints-list 容器不存在");return}if(a&&_userInfo){const s=_userInfo.endpoints_limit;s!==-1&&we.length>=s?(a.disabled=!0,a.title=t("ep-limit-reached",{limit:s}),a.classList.add("btn-disabled-plus")):(a.disabled=!1,a.title="",a.classList.remove("btn-disabled-plus"))}if(we.length===0){e.innerHTML=`<div class="erp-empty">${escapeHtml(t("ep-list-empty"))}</div>`,n&&(n.textContent=t("auto-status-none"),n.className="auto-status-pill none");return}const o=we.some(s=>s.auto_push&&s.enabled);if(n&&(n.textContent=t("auto-status-active",{n:we.length,mode:o?t("auto-status-on"):t("auto-status-off")}),n.className="auto-status-pill "+(o?"active":"ready")),ht(),e.innerHTML=we.map(s=>{const u=s.config||{},l=escapeHtml(u.url||"");u._token_set;const k=s.enabled!==!1,i=[];s.is_default&&i.push(`<span class="ep-badge default">${escapeHtml(t("ep-default"))}</span>`),s.auto_push&&i.push(`<span class="ep-badge auto">${escapeHtml(t("ep-auto-push-on"))}</span>`),k||i.push(`<span class="ep-badge disabled">${escapeHtml(t("ep-disabled"))}</span>`);const p=[];return s.success_count>0&&p.push(`<span class="ep-stat ok">${escapeHtml(t("ep-success",{n:s.success_count}))}</span>`),s.failure_count>0&&p.push(`<span class="ep-stat fail">${escapeHtml(t("ep-failure",{n:s.failure_count}))}</span>`),`
            <div class="erp-endpoint" data-ep-id="${escapeHtml(s.id)}">
                <div class="ep-main">
                    <div class="ep-title-row">
                        <div class="ep-name">${escapeHtml(s.name)}</div>
                        <div class="ep-badges">${i.join("")}</div>
                    </div>
                    <div class="ep-url">${l||"-"}</div>
                    <div class="ep-stats">${p.join(" · ")}</div>
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
        `}).join(""),_userInfo&&_userInfo.endpoints_limit!==-1){const s=we.length,u=_userInfo.endpoints_limit,l=_userInfo.plan,k=document.createElement("div");k.className="erp-limit-hint",l==="free"?k.innerHTML=`${escapeHtml(t("ep-free-limit-hint",{used:s,limit:u}))} <a data-upgrade="plus">${escapeHtml(t("upgrade-to-plus"))}</a>`:k.textContent=t("ep-plus-limit-hint",{used:s,limit:u}),e.appendChild(k)}}function Zt(e){je=e||null;const n=document.getElementById("endpoint-modal"),a=document.getElementById("endpoint-modal-title");a.textContent=e?t("ep-modal-title-edit"):t("ep-modal-title-new");const o=document.getElementById("ep-name"),s=document.getElementById("ep-url"),u=document.getElementById("ep-token"),l=document.getElementById("ep-is-default"),k=document.getElementById("ep-auto-push"),i=document.getElementById("ep-test-result");i.style.display="none",i.textContent="";const p=document.getElementById("ep-save-error");if(p&&p.remove(),e){const r=we.find(v=>v.id===e);if(!r)return;o.value=r.name||"",s.value=(r.config||{}).url||"",u.value=(r.config||{})._token_set&&r.config.token||"",u.placeholder=(r.config||{})._token_set?"（已保存 · 留空保持不变）":t("ep-token-ph"),l.checked=!!r.is_default,k.checked=!!r.auto_push}else o.value="",s.value="",u.value="",u.placeholder=t("ep-token-ph"),l.checked=we.length===0,k.checked=!0;const c=k.closest(".form-switch-row");if(k.disabled=!1,c){c.classList.remove("disabled-plus"),c.title="",c.style.cursor="",c.onclick=null;const r=c.querySelector(".plus-badge");r&&r.remove()}n.style.display="",setTimeout(()=>o.focus(),50)}function bt(){document.getElementById("endpoint-modal").style.display="none",je=null;const e=document.getElementById("ep-save-error");e&&e.remove()}function yt(e){if(!e)return"";let n=e.trim();const a=n.search(/\s/);return a>=0&&(n=n.slice(0,a)),n}function wt(){const e=document.getElementById("ep-name").value.trim(),n=yt(document.getElementById("ep-url").value),a=document.getElementById("ep-token").value,o=document.getElementById("ep-is-default").checked,s=document.getElementById("ep-auto-push").checked,u={url:n};return a&&(u.token=a),{name:e,url:n,tokenVal:a,isDefault:o,autoPush:s,config:u}}async function Qt(){const{url:e,config:n}=wt(),a=document.getElementById("ep-test-result");if(!e){a.style.display="",a.className="form-test-result fail",a.textContent=t("ep-required");return}a.style.display="",a.className="form-test-result running",a.textContent=t("ep-test-running");try{const s=await(await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({adapter:"webhook",config:n})})).json();s.success?(a.className="form-test-result ok",a.textContent=t("ep-test-ok",{status:s.http_status,ms:s.elapsed_ms})):(a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:s.error_msg||"unknown"}))}catch(o){a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:o.message})}}async function en(){const e=wt(),n=document.getElementById("ep-save-error");if(n&&(n.style.display="none"),!e.name||!e.url){rt(t("ep-required"));return}const a={name:e.name,adapter:"webhook",config:e.config,is_default:e.isDefault,auto_push:e.autoPush},o=document.getElementById("btn-ep-save"),s=o.innerHTML;o.disabled=!0,o.classList.add("loading");try{let u;if(je?u=await fetch(`/api/erp/endpoints/${encodeURIComponent(je)}`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}):u=await fetch("/api/erp/endpoints",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}),!u.ok){const k=(await u.json().catch(()=>({}))).detail||`HTTP ${u.status}`;throw new Error(typeof k=="string"?k:JSON.stringify(k))}bt(),showToast(t("ep-save-ok")),Oe()}catch(u){rt(`${t("ep-save-fail")} · ${u.message||"unknown"}`)}finally{o.disabled=!1,o.classList.remove("loading"),o.innerHTML=s}}function rt(e){let n=document.getElementById("ep-save-error");if(!n){const a=document.querySelector("#endpoint-modal .modal-foot");if(!a)return;n=document.createElement("div"),n.id="ep-save-error",n.className="ep-inline-error",a.parentNode.insertBefore(n,a)}n.textContent=e,n.style.display=""}async function tn(e){const n=we.find(o=>o.id===e);if(!(!n||!await showConfirm(t("ep-delete-confirm",{name:n.name}),{danger:!0})))try{if(!(await fetch(`/api/erp/endpoints/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showToast(t("ep-delete-ok")),Oe()}catch{showToast(t("ep-save-fail"),"fail")}}window.loadErpEndpoints=Oe;window.loadErpTodayStats=ht;window.renderErpEndpointsList=gt;window.openEndpointModal=Zt;window.closeEndpointModal=bt;window.saveEndpoint=en;window.deleteEndpoint=tn;window.testEndpointConnection=Qt;window._sanitizeUrl=yt;async function kt(e){if(e=(e||"").trim(),!!e)try{await navigator.clipboard.writeText(e),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{try{const a=document.createElement("textarea");a.value=e,a.style.position="fixed",a.style.opacity="0",document.body.appendChild(a),a.select(),document.execCommand("copy"),a.remove(),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{showToast(t("erp-doc-copy-fail"),"error")}}}async function nn(e){const n=document.createElement("div");n.className="log-detail-modal",n.innerHTML=`
        <div class="log-detail-box">
            <div class="log-detail-loading">${escapeHtml(t("log-detail-loading"))}</div>
        </div>
    `,document.body.appendChild(n),n.addEventListener("click",async a=>{if(a.target===n||a.target.classList.contains("log-detail-close")){n.remove();return}const o=a.target.closest("[data-receipt-copy]");if(o){kt(o.dataset.receiptCopy);return}const s=a.target.closest("[data-receipt-action]");if(s){const u=s.dataset.receiptAction;u==="retry"?window.retryPushLog(s.dataset.logId):u==="exceptions"?typeof routeTo=="function"&&routeTo("exceptions"):u==="mappings"&&typeof routeTo=="function"&&routeTo("integrations"),n.remove();return}});try{const a=await fetch(`/api/erp/logs/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!a.ok){n.remove();return}const o=await a.json(),s=window._erpEndpoints.find(L=>L.id===o.endpoint_id),u=o.endpoint_name||(s?s.name:o.endpoint_id?t("erp-log-endpoint-deleted"):"-"),l=(o.endpoint_adapter||s&&s.adapter||"").toLowerCase(),k=new Date(o.created_at).toLocaleString(),i=o.trigger==="auto"?t("log-tag-auto"):o.trigger==="retry"?t("log-tag-retry"):t("log-tag-manual"),p=o.request_body?JSON.stringify(o.request_body,null,2):t("erp-receipt-no-tech"),c=o.response_body||t("erp-receipt-no-tech"),r=o.status==="success";let v=typeof c=="string"?c:JSON.stringify(c,null,2);if(r)try{const L=typeof o.response_body=="string"?JSON.parse(o.response_body):o.response_body||{},H=L.row_count||(Array.isArray(L.imported_rows)?L.imported_rows.length:0);H>0&&(v=t("log-push-rows").replace("{n}",String(H)))}catch{}const E=(o.external_doc_no||"").trim(),x=(o.external_url||"").trim(),R=(o.external_doc_hint||"").trim(),D=(o.ocr_buyer_name||"").trim()||o.client_name||"-",w=o.seller_name||"-";let B="-";const z=Number(o.total_amount);o.total_amount!=null&&o.total_amount!==""&&!isNaN(z)&&(B=z.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}));const q=r?t("erp-receipt-title-ok"):t("erp-receipt-title-fail"),F=r?"✓":"✗",A=[],g=(L,H)=>{A.push(`
                <div class="erp-receipt-row">
                    <span class="erp-receipt-key">${escapeHtml(L)}</span>
                    <span class="erp-receipt-val">${H}</span>
                </div>`)};if(g(t("erp-receipt-invoice-no"),`<strong>${escapeHtml(o.invoice_no||"-")}</strong>`),g(t("erp-receipt-erp-name"),escapeHtml(u)),r){let L;E?L=`<strong class="erp-receipt-docno">${escapeHtml(E)}</strong><button class="erp-receipt-copy-btn" type="button" data-receipt-copy="${escapeHtml(E)}" title="${escapeHtml(t("erp-doc-copy-tip"))}">${escapeHtml(t("erp-receipt-copy-btn"))}</button>`:L=`<span class="erp-receipt-docno-missing">${escapeHtml(t("erp-log-doc-missing"))}</span>`,g(t("erp-receipt-doc-no"),L)}g(t("erp-receipt-client"),escapeHtml(D)),g(t("erp-receipt-seller"),escapeHtml(w)),r&&g(t("erp-receipt-amount"),escapeHtml(B)),g(t("erp-receipt-time"),escapeHtml(k)),g(t("erp-receipt-elapsed"),escapeHtml((o.elapsed_ms!=null?o.elapsed_ms:"-")+"ms"));let f="";r&&x?f=`<a class="erp-receipt-primary-btn" href="${escapeHtml(x)}" target="_blank" rel="noopener">${escapeHtml(t("erp-receipt-open-erp"))}</a>`:r&&E&&(f=`<button class="erp-receipt-primary-btn" type="button" data-receipt-copy="${escapeHtml(E)}">${escapeHtml(t("erp-receipt-copy-docno"))}</button>`);let h="";if(r&&E&&R){const L="erp-receipt-hint-"+R,H=t(L);H&&H!==L&&(h=`<div class="erp-receipt-hint"><svg class="erp-receipt-hint-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span>${escapeHtml(H)}</span></div>`)}let I="";if(!r){const L=(o.error_msg||"").match(/ERR_[A-Z0-9_]+/),H=L?L[0]:"",_=typeof currentLang=="string"&&currentLang||window._currentLang||"th",K=o.error_friendly&&o.error_friendly[_]||(o.error_msg?humanizeError(o.error_msg):t("erp-receipt-no-error")),G=/ERR_NO_CUSTOMER_MAPPING|ERR_NO_CLIENT|ERR_NO_SEED_CUSTOMER|ERR_NO_SEED_PRODUCT/.test(o.error_msg||""),W=!!(o.history_id&&o.endpoint_id),te=[];te.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="exceptions">${escapeHtml(t("erp-receipt-act-exceptions"))}</button>`),G&&te.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="mappings">${escapeHtml(t("erp-receipt-act-mapping"))}</button>`),W&&te.push(`<button class="erp-receipt-action-btn primary" type="button" data-receipt-action="retry" data-log-id="${escapeHtml(o.id)}">${escapeHtml(t("erp-receipt-act-retry"))}</button>`),I=`
                <div class="erp-receipt-fail-reason-label">${escapeHtml(t("erp-receipt-fail-reason"))}</div>
                <div class="erp-receipt-fail-box">
                    ${H?`<div class="erp-receipt-errcode">${escapeHtml(H)}</div>`:""}
                    <div class="erp-receipt-friendly">${escapeHtml(K)}</div>
                </div>
                <div class="erp-receipt-actions-label">${escapeHtml(t("erp-receipt-suggest"))}</div>
                <div class="erp-receipt-actions">${te.join("")}</div>`}n.querySelector(".log-detail-box").innerHTML=`
            <div class="log-detail-head">
                <div class="log-detail-title">
                    <span class="log-detail-status-icon ${r?"ok":"fail"}">${F}</span>
                    ${escapeHtml(q)}
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
                    <pre>${escapeHtml(p)}</pre>
                </div>
                <div class="log-detail-section">
                    <div class="log-detail-label">${escapeHtml(t("log-detail-response-human"))}</div>
                    <pre>${escapeHtml(v)}</pre>
                </div>
            </details>
        `}catch(a){console.error(a),n.remove()}}window.copyErpDocNo=kt;window.showLogDetail=nn;let Be={key:"all",val:""},_e=new Set;window._erpSelected=_e;async function Pe(e){const n=document.getElementById("erp-logs-list");if(n){e||(n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`),window.loadErpTodayStats();try{const a=new URLSearchParams({limit:"30"});Be.key==="status"&&a.set("status",Be.val),Be.key==="trigger"&&a.set("trigger",Be.val),Be.key==="adapter"&&a.set("adapter",Be.val);const o=await fetch(`/api/erp/logs?${a}`,{headers:{Authorization:"Bearer "+token}});if(!o.ok){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const u=(await o.json()).items||[];if(window._erpLogPollTimer&&(clearTimeout(window._erpLogPollTimer),window._erpLogPollTimer=null),u.some(function(p){return p.status==="pending"})&&(window._erpLogPollTimer=setTimeout(function(){Pe(!0)},4e3)),u.length===0){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-empty"))}</div>`;return}const k='<div class="erp-log-row erp-log-row-header" data-log-header>'+(u.filter(function(p){var c=p.status==="failed"&&p.next_retry_at&&new Date(p.next_retry_at).getTime()>Date.now()-6e4;return!c}).map(function(p){return p.id}).length>0?`<input type="checkbox" class="erp-log-cb erp-log-cb-all" data-log-select-all title="${escapeHtml(t("erp-log-select-all-tip"))}">`:'<span class="erp-log-cb-spacer"></span>')+`<span class="log-time">${escapeHtml(t("erp-log-col-time"))}</span><span class="log-status">${escapeHtml(t("erp-log-col-status"))}</span><span class="log-tag-header">${escapeHtml(t("erp-log-col-trigger"))}</span><span class="log-invoice">${escapeHtml(t("erp-log-col-invoice"))}</span><span class="log-workspace">${escapeHtml(t("erp-log-col-workspace"))}</span><span class="log-client">${escapeHtml(t("erp-log-col-client"))}</span><span class="log-seller">${escapeHtml(t("erp-log-col-seller"))}</span><span class="log-erp">${escapeHtml(t("erp-log-col-erp"))}</span><span class="log-doc">${escapeHtml(t("erp-log-col-doc"))}</span><span class="log-http">${escapeHtml(t("erp-log-col-http"))}</span><span class="log-elapsed">${escapeHtml(t("erp-log-col-elapsed"))}</span><span class="log-actions"></span></div>`;n.innerHTML=k+u.map(p=>{const c=new Date(p.created_at),r=`${String(c.getMonth()+1).padStart(2,"0")}-${String(c.getDate()).padStart(2,"0")} ${String(c.getHours()).padStart(2,"0")}:${String(c.getMinutes()).padStart(2,"0")}`,v=p.status==="failed"&&p.next_retry_at&&new Date(p.next_retry_at).getTime()>Date.now()-6e4;let E,x,R;p.status==="pending"?(E="retrying",x="⟳",R=t("erp-status-pending")):p.status==="success"?(E="ok",x="✓",R=t("erp-status-success")):p.status==="skipped_dup"?(E="skipped",x="⏭",R=t("erp-status-skipped")):v?(E="retrying",x="↻",R=t("erp-status-retrying")):(E="fail",x="✗",R=t("erp-status-failed"));let D;p.trigger==="auto"?D=`<span class="log-tag auto">${escapeHtml(t("log-tag-auto"))}</span>`:p.trigger==="retry"?D=`<span class="log-tag retry">${escapeHtml(t("log-tag-retry"))}</span>`:D=`<span class="log-tag manual">${escapeHtml(t("log-tag-manual"))}</span>`;let w="";const B=p.retry_count||0,z=p.max_retries||3;if(v){const K=new Date(p.next_retry_at).getTime()-Date.now(),G=Math.max(0,Math.round(K/6e4)),W=G<=0?t("erp-retry-next-soon"):t("erp-retry-next-min",{n:G});w=`${t("erp-retry-attempt",{n:B,max:z})} · ${W}`}else p.status==="failed"&&B>=z&&!p.next_retry_at&&(w=t("erp-retry-exhausted",{n:B}));const q=p.status==="failed"&&!v?`<button class="log-retry-btn btn btn-icon" data-log-retry="${escapeHtml(p.id)}" title="${escapeHtml(t("log-retry-title"))}">↻</button>`:"",F=!v,A=_e.has(p.id)?"checked":"",g=F?`<input type="checkbox" class="erp-log-cb" data-log-cb="${escapeHtml(p.id)}" ${A}>`:'<span class="erp-log-cb-spacer"></span>',f=(p.ocr_buyer_name||"").trim()||(p.client_name||"").trim(),h=f?`<span class="log-client" title="${escapeHtml(f)}">${escapeHtml(f.substring(0,18))}</span>`:`<span class="log-client log-client-empty" title="${escapeHtml(t("erp-log-client-unassigned-tip"))}">${escapeHtml(t("erp-log-client-unassigned"))}</span>`,I=p.workspace_name?`<span class="log-workspace">${escapeHtml((p.workspace_name||"").substring(0,16))}</span>`:`<span class="log-workspace log-workspace-unresolved" title="${escapeHtml(t("erp-log-ws-unresolved-tip"))}">${escapeHtml(t("erp-log-ws-unresolved"))}</span>`,L=p.endpoint_name?`<span class="log-erp">${escapeHtml((p.endpoint_name||"").substring(0,14))}</span>`:`<span class="log-erp log-erp-deleted">${escapeHtml(t("erp-log-endpoint-deleted"))}</span>`,H=(p.external_doc_no||"").trim(),_=(p.external_url||"").trim();let M;return _?M=`<span class="log-doc"><a href="${escapeHtml(_)}" target="_blank" rel="noopener" class="log-doc-open" title="${escapeHtml(H||"")}">${escapeHtml(t("erp-log-doc-open"))}</a></span>`:H?M=`<span class="log-doc log-doc-copy" data-copy-doc="${escapeHtml(H)}" title="${escapeHtml(t("erp-log-doc-copy-tip"))}">${escapeHtml(H.substring(0,18))}</span>`:p.status==="success"?M=`<span class="log-doc log-doc-missing" title="${escapeHtml(t("erp-log-doc-missing-tip"))}">${escapeHtml(t("erp-log-doc-missing"))}</span>`:M='<span class="log-doc log-doc-empty">-</span>',`
                <div class="erp-log-row ${E}" data-log-detail="${escapeHtml(p.id)}">
                    ${g}
                    <span class="log-time">${r}</span>
                    <span class="log-status" title="${escapeHtml(R+(w?" · "+w:""))}">${x}</span>
                    ${D}
                    <span class="log-invoice">${escapeHtml(p.invoice_no||"-")}</span>
                    ${I}
                    ${h}
                    <span class="log-seller">${escapeHtml((p.seller_name||"").substring(0,20))}</span>
                    ${L}
                    ${M}
                    <span class="log-http">HTTP ${p.http_status||"-"}</span>
                    <span class="log-elapsed">${p.elapsed_ms}ms</span>
                    <span class="log-actions">${q}</span>
                </div>
            `}).join("");const i=new Set(u.map(p=>p.id));for(const p of Array.from(_e))i.has(p)||_e.delete(p);window._refreshErpBatchBar()}catch(a){console.error("load erp logs failed",a),n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}async function xt(e){try{const n=await fetch(`/api/erp/logs/${encodeURIComponent(e)}/retry`,{method:"POST",headers:{Authorization:"Bearer "+token}}),a=await n.json().catch(()=>({}));n.ok&&a.ok?showToast(t("log-retry-ok"),"success"):showToast(t("log-retry-fail")+" · HTTP "+(a.http_status||n.status),"error"),Pe(),window.loadErpEndpoints()}catch{showToast(t("log-retry-fail"),"error")}}(function(){document.getElementById("btn-add-endpoint").addEventListener("click",()=>window.openEndpointModal(null)),document.getElementById("endpoint-modal-close").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-cancel").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-test").addEventListener("click",window.testEndpointConnection),document.getElementById("btn-ep-save").addEventListener("click",window.saveEndpoint),document.getElementById("ep-url").addEventListener("blur",n=>{const a=window._sanitizeUrl(n.target.value);a!==n.target.value.trim()&&(n.target.value=a)}),document.addEventListener("click",n=>{const a=n.target.closest("[data-ep-edit]"),o=n.target.closest("[data-ep-del]");a&&window.openEndpointModal(a.dataset.epEdit),o&&window.deleteEndpoint(o.dataset.epDel);const s=n.target.closest("[data-log-retry]");if(s){n.stopPropagation(),xt(s.dataset.logRetry);return}const u=n.target.closest("[data-log-cb]");if(u){n.stopPropagation();const c=u.dataset.logCb;u.checked?_e.add(c):_e.delete(c),window._refreshErpBatchBar();return}const l=n.target.closest("[data-log-select-all]");if(l){n.stopPropagation();const c=l.checked;document.querySelectorAll("[data-log-cb]").forEach(function(v){v.checked=c;const E=v.dataset.logCb;c?_e.add(E):_e.delete(E)}),window._refreshErpBatchBar();return}if(n.target.closest("#btn-erp-batch-retry")){n.stopPropagation(),window._runErpBatchRetry();return}if(n.target.closest("#btn-erp-batch-clear")){n.stopPropagation(),_e.clear(),document.querySelectorAll(".erp-log-cb").forEach(c=>{c.checked=!1}),window._refreshErpBatchBar();return}const k=n.target.closest("[data-log-detail]");if(k){if(n.target.closest("[data-log-cb]"))return;const c=n.target.closest("[data-copy-doc]");if(c){n.stopPropagation(),window.copyErpDocNo(c.dataset.copyDoc);return}if(n.target.closest(".log-doc-open"))return;window.showLogDetail(k.dataset.logDetail);return}const i=n.target.closest(".chip-filter");if(i){document.querySelectorAll("#erp-logs-filters .chip-filter").forEach(c=>c.classList.remove("active")),i.classList.add("active"),Be={key:i.dataset.filterKey,val:i.dataset.filterVal},Pe();return}if(n.target.closest("#btn-refresh-logs")){const c=n.target.closest("#btn-refresh-logs");c.classList.add("spinning"),setTimeout(()=>c.classList.remove("spinning"),600),Pe();return}const p=n.target.closest(".auto-nav-item");if(p&&p.dataset.autoTab){switchAutomationTab(p.dataset.autoTab);return}})})();window.loadErpLogs=Pe;window.retryPushLog=xt;function _t(){const e=document.getElementById("erp-logs-batch-bar"),n=document.getElementById("erp-logs-batch-count"),a=document.querySelector("[data-log-select-all]");if(a){const u=document.querySelectorAll("[data-log-cb]").length,l=window._erpSelected.size;l===0?(a.checked=!1,a.indeterminate=!1):l>=u?(a.checked=!0,a.indeterminate=!1):(a.checked=!1,a.indeterminate=!0)}if(!e||!n)return;const o=window._erpSelected.size;if(o===0){e.style.display="none";return}e.style.display="",n.textContent=t("erp-batch-selected",{n:o})}async function Et(){console.info("[ErpBatch] retry triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-confirm",{n:e.length})))try{const a=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!a.ok){showToast(t("erp-logs-error"),"error");return}const o=await a.json(),s=t("erp-batch-result",{ok:o.succeeded||0,fail:o.failed||0,skip:o.skipped||0}),u=o.failed&&o.failed>0?"warn":"success";showToast(s,u),window._erpSelected.clear(),window.loadErpLogs()}catch(a){console.error("batch retry failed",a),showToast(t("erp-logs-error"),"error")}}async function Bt(){console.info("[ErpBatch] delete triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-delete-confirm",{n:e.length}),{danger:!0}))try{const o=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!o.ok){showToast(t("erp-logs-error"),"error");return}const s=await o.json();e.forEach(function(u){var l=document.querySelector('[data-log-detail="'+u+'"]');l&&l.remove()});var a=document.getElementById("erp-logs-batch-bar");a&&(a.style.display="none"),showToast(t("erp-batch-delete-result",{n:s.deleted||0,skip:s.skipped||0}),s.deleted>0?"success":"warn"),window._erpSelected.clear(),setTimeout(window.loadErpLogs,500)}catch(o){console.error("batch delete failed",o),showToast(t("erp-logs-error"),"error")}}(function(){function n(){var a=document.getElementById("btn-erp-batch-retry"),o=document.getElementById("btn-erp-batch-delete"),s=document.getElementById("btn-erp-batch-clear");a&&!a.dataset.boundDirect&&(a.addEventListener("click",function(u){u.preventDefault(),u.stopPropagation(),Et()}),a.dataset.boundDirect="1"),o&&!o.dataset.boundDirect&&(o.addEventListener("click",function(u){u.preventDefault(),u.stopPropagation(),Bt()}),o.dataset.boundDirect="1"),s&&!s.dataset.boundDirect&&(s.addEventListener("click",function(u){u.preventDefault(),u.stopPropagation(),window._erpSelected.clear(),document.querySelectorAll(".erp-log-cb").forEach(function(l){l.checked=!1}),_t()}),s.dataset.boundDirect="1")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n(),setTimeout(n,2e3),setTimeout(n,5e3),window._bindErpBatchButtons=n})();window._refreshErpBatchBar=_t;window._runErpBatchRetry=Et;window._runErpBatchDelete=Bt;(function(){let e=null,n=!1;function a(){if(e)return e;const k=document.createElement("div");k.id="line-email-modal",k.style.cssText="position:fixed;inset:0;background:rgba(10,14,39,0.85);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;",k.innerHTML=`
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
        `,document.body.appendChild(k),e=k;const i=k.querySelector("#line-email-input"),p=k.querySelector("#line-email-submit-btn"),c=k.querySelector("#line-email-err");async function r(){c.textContent="";const v=(i.value||"").trim().toLowerCase();if(!v||v.indexOf("@")<0||v.split("@")[1].indexOf(".")<0){c.textContent=t("line-email-err-invalid");return}p.disabled=!0,p.style.opacity="0.6";try{const E=await fetch("/api/me/line_complete_email",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},body:JSON.stringify({email:v})});if(!E.ok)throw new Error("http_"+E.status);const x=await E.json();x.token&&localStorage.setItem("mrpilot_token",x.token),typeof showToast=="function"&&showToast(x.merged?t("line-email-merged-toast"):t("line-email-saved-toast"),"success"),setTimeout(function(){window.location.reload()},600)}catch{c.textContent=t("line-email-err-failed"),p.disabled=!1,p.style.opacity="1"}}return p.addEventListener("click",r),i.addEventListener("keydown",function(v){v.key==="Enter"&&r()}),k}function o(){if(!e)return;const k=e.querySelector("#line-email-title-h"),i=e.querySelector("#line-email-sub-p"),p=e.querySelector("#line-email-input"),c=e.querySelector("#line-email-submit-btn");k&&(k.textContent=t("line-email-title")),i&&(i.textContent=t("line-email-sub")),p&&(p.placeholder=t("line-email-placeholder")),c&&(c.textContent=t("line-email-submit"))}function s(){a(),o(),e.style.display="flex",n=!0;const k=e.querySelector("#line-email-input");k&&setTimeout(function(){k.focus()},100)}async function u(){const k=localStorage.getItem("mrpilot_token");if(k)try{const i=await fetch("/api/me/needs_email",{headers:{Authorization:"Bearer "+k}});if(!i.ok)return;const p=await i.json();p&&p.needs_email&&s()}catch{}}function l(){setTimeout(u,800)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",l):l(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("line-email-modal",function(){n&&o()})})();(function(){function e(c){let r=0;return c.length>=8&&r++,c.length>=12&&r++,/[a-zA-Z]/.test(c)&&/\d/.test(c)&&r++,/[^a-zA-Z0-9]/.test(c)&&r++,Math.min(3,r)}function n(c,r){const v=document.getElementById("cpw-msg");v&&(v.textContent=c,v.className="cpw-msg "+(r||""))}function a(c){return typeof t=="function"?t(c):c}let o=!1;function s(){["cpw-old","cpw-new","cpw-confirm"].forEach(r=>{const v=document.getElementById(r);v&&(v.value="",v.setAttribute("readonly","readonly"))});const c=document.getElementById("cpw-strength-bar");c&&(c.style.width="0%",c.className="cpw-strength-bar"),n("","")}async function u(){const c=document.getElementById("btn-change-pw"),r=document.getElementById("cpw-old"),v=document.getElementById("cpw-new"),E=document.getElementById("cpw-confirm"),x=document.getElementById("cpw-strength-bar");if(!c||!r||!v||!E)return;const R=r.value,D=v.value,w=E.value;if(!R||!D||!w){n(a("settings-change-pw-empty"),"error");return}if(D.length<8){n(a("settings-change-pw-too-short"),"error");return}if(!(/[a-zA-Z]/.test(D)&&/\d/.test(D))){n(a("settings-change-pw-too-weak"),"error");return}if(D!==w){n(a("settings-change-pw-mismatch"),"error");return}c.disabled=!0;const B=c.textContent;c.textContent=a("settings-change-pw-submitting"),n("","");try{const z=localStorage.getItem("mrpilot_token"),q=await fetch("/api/me/change_password",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+z},body:JSON.stringify({old_password:R,new_password:D})}),F=await q.json().catch(()=>({}));if(q.ok&&F.ok)n(a("settings-change-pw-success"),"success"),typeof showToast=="function"&&showToast(a("settings-change-pw-success"),"success"),r.value="",v.value="",E.value="",x&&(x.style.width="0%",x.className="cpw-strength-bar");else{const A=F.detail||"";let g=a("settings-change-pw-success");A==="wrong_old_password"?g=a("settings-change-pw-wrong-old"):A==="password_too_short"?g=a("settings-change-pw-too-short"):A==="password_too_weak"?g=a("settings-change-pw-too-weak"):g=A||"Error",n(g,"error")}}catch(z){console.error("change_password",z),n("Network error","error")}finally{c.disabled=!1,c.textContent=B}}function l(){o||(o=!0,document.addEventListener("click",c=>{if(!c.target||!c.target.closest)return;const r=c.target.closest(".cpw-eye");if(r){const v=document.getElementById(r.dataset.target);v&&(v.type=v.type==="password"?"text":"password");return}if(c.target.closest("#cpw-forgot-link")){c.preventDefault(),k();return}if(c.target.closest("#btn-change-pw")){u();return}c.target.closest('.settings-nav-item[data-settings-tab="account"], .settings-nav-item[data-tab="account"], .settings-nav-item[data-tab="security"]')&&setTimeout(s,100)}),document.addEventListener("input",c=>{if(c.target&&c.target.id==="cpw-new"){const r=document.getElementById("cpw-strength-bar");if(!r)return;const v=e(c.target.value),E=["0%","33%","66%","100%"],x=["","weak","medium","strong"];r.style.width=E[v],r.className="cpw-strength-bar "+x[v]}}),document.addEventListener("focusin",c=>{c.target&&["cpw-old","cpw-new","cpw-confirm"].includes(c.target.id)&&c.target.removeAttribute("readonly")}),document.getElementById("cpw-old")&&s())}function k(){const c=window._userInfo||(typeof _userInfo<"u"?_userInfo:null),r=c&&c.username?c.username:"",v=i(r);let E=document.getElementById("cpw-forgot-overlay");E&&E.remove(),E=document.createElement("div"),E.id="cpw-forgot-overlay",E.className="cpw-forgot-overlay",E.innerHTML=`
            <div class="cpw-forgot-modal">
                <div class="cpw-forgot-head">
                    <div class="cpw-forgot-title">${p(a("cpw-forgot-title"))}</div>
                    <button class="cpw-forgot-close" id="cpw-forgot-close" aria-label="close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="cpw-forgot-body">
                    <p class="cpw-forgot-desc">${p(a("cpw-forgot-desc"))}</p>
                    <div class="cpw-forgot-email">${p(v)}</div>
                    <p class="cpw-forgot-tip">${p(a("cpw-forgot-tip"))}</p>
                    <div class="cpw-forgot-msg" id="cpw-forgot-msg"></div>
                </div>
                <div class="cpw-forgot-foot">
                    <button class="btn btn-ghost" id="cpw-forgot-cancel">${p(a("cpw-forgot-cancel"))}</button>
                    <button class="btn btn-primary" id="cpw-forgot-send">${p(a("cpw-forgot-send"))}</button>
                </div>
            </div>
        `,document.body.appendChild(E);const x=()=>E.remove();E.querySelector("#cpw-forgot-close").addEventListener("click",x),E.querySelector("#cpw-forgot-cancel").addEventListener("click",x),E.addEventListener("click",R=>{R.target===E&&x()}),E.querySelector("#cpw-forgot-send").addEventListener("click",async()=>{const R=E.querySelector("#cpw-forgot-send"),D=E.querySelector("#cpw-forgot-msg");R.disabled=!0;const w=R.textContent;R.textContent=a("cpw-forgot-sending");try{const B=await fetch("/api/auth/forgot_password",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:r})}),z=await B.json().catch(()=>({}));B.ok?(D.textContent=a("cpw-forgot-success"),D.className="cpw-forgot-msg success",R.style.display="none",E.querySelector("#cpw-forgot-cancel").textContent=a("cpw-forgot-close-btn")):(D.textContent=z.detail||a("cpw-forgot-fail"),D.className="cpw-forgot-msg error",R.disabled=!1,R.textContent=w)}catch{D.textContent=a("cpw-forgot-fail"),D.className="cpw-forgot-msg error",R.disabled=!1,R.textContent=w}})}function i(c){if(!c||!c.includes("@"))return c||"";const[r,v]=c.split("@");return r.length<=2?r+"****@"+v:r.slice(0,2)+"****@"+v}function p(c){return c==null?"":String(c).replace(/[&<>"']/g,r=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[r])}document.readyState==="complete"||document.readyState==="interactive"?l():document.addEventListener("DOMContentLoaded",l)})();(function(){let e=null,n=!1;async function a(){if(n)return;const s=localStorage.getItem("mrpilot_token");if(s){n=!0;try{const u=await fetch("/api/me",{headers:{Authorization:"Bearer "+s},cache:"no-store"});if(u.status===401){const l=await u.json().catch(()=>({})),k=l&&l.detail;let i="";if(typeof k=="string"?i=k:k&&typeof k=="object"&&(i=k.code||""),console.warn("[heartbeat] session revoked",i),localStorage.removeItem("mrpilot_token"),e&&(clearInterval(e),e=null),i==="auth.session_revoked")try{_showSessionRevokedModal()}catch{window.location.href="/"}else{const p=i==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";try{typeof showToast=="function"&&typeof t=="function"?showToast(t(p),"error"):alert("Session expired")}catch{}setTimeout(()=>{window.location.href="/"},1500)}}}catch{}finally{n=!1}}}function o(){e&&clearInterval(e),e=setInterval(a,15e3)}localStorage.getItem("mrpilot_token")&&o(),window.addEventListener("focus",a),document.addEventListener("visibilitychange",function(){document.hidden||a()}),window._sessionCheck=a})();async function Fe(){const e=document.getElementById("team-loading"),n=document.getElementById("team-list"),a=document.getElementById("team-empty"),o=document.getElementById("team-count");if(n){e&&(e.style.display=""),n.style.display="none",a&&(a.style.display="none");try{const s=await apiGet("/api/team/employees"),u=s&&s.employees||[];if(e&&(e.style.display="none"),o&&(o.textContent=(t("team-count")||"共 {n} 名员工").replace("{n}",u.length)),u.length===0){a&&(a.style.display="");return}n.style.display="",n.innerHTML=u.map(l=>{const k=l.last_login_at?new Date(l.last_login_at).toLocaleDateString():t("team-never-login")||"从未登录",i=l.is_active===!1?"team-status-off":"team-status-on",p=l.is_active===!1?t("team-status-disabled")||"已禁用":t("team-status-active")||"正常",c=l.email?`<span class="team-meta-sep">·</span><span>${escapeHtml(l.email)}</span>`:"";return`
            <div class="team-card" data-employee-id="${escapeHtml(l.id)}">
                <div class="team-card-main">
                    <div class="team-avatar">${escapeHtml((l.username||"?")[0].toUpperCase())}</div>
                    <div class="team-info">
                        <div class="team-name">${escapeHtml(l.username||"")}</div>
                        <div class="team-meta">
                            <span class="team-status-dot ${i}"></span>
                            <span>${escapeHtml(p)}</span>
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml(t("team-last-login")||"上次登录")}: ${escapeHtml(k)}</span>
                            ${c}
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
            </div>`}).join("")}catch(s){console.error("loadTeamList failed:",s),e&&(e.textContent=t("team-load-failed")||"加载失败")}}}async function an(){document.querySelectorAll(".add-emp-overlay").forEach(o=>o.remove());const e=document.createElement("div");e.className="add-emp-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const o=document.getElementById("add-emp-username");o&&o.focus()},200);function n(){e.classList.remove("show"),setTimeout(()=>e.remove(),220)}e.querySelector(".add-emp-close").addEventListener("click",n),e.querySelector("#add-emp-cancel").addEventListener("click",n),e.addEventListener("click",o=>{o.target===e&&n()}),e.querySelector("#add-emp-submit").addEventListener("click",async()=>{const o=document.getElementById("add-emp-username"),s=document.getElementById("add-emp-email"),u=document.getElementById("add-emp-password"),l=document.getElementById("add-emp-msg"),k=document.getElementById("add-emp-submit"),i=(o.value||"").trim(),p=(s.value||"").trim(),c=u.value||"";if(l.textContent="",l.classList.remove("error"),!i||i.length<3){l.textContent=t("team-modal-err-username")||"用户名至少 3 位",l.classList.add("error");return}if(!/^[a-zA-Z0-9_.\-]+$/.test(i)){l.textContent=t("team-modal-err-username-fmt")||"只能用字母 / 数字 / 下划线 / 点 / 横线",l.classList.add("error");return}if(p&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(p)){l.textContent=t("msg-email-invalid")||"邮箱格式不对",l.classList.add("error");return}if(c.length<8){l.textContent=t("pwd-too-short")||"密码至少 8 位",l.classList.add("error");return}if(/^\d+$/.test(c)){l.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",l.classList.add("error");return}if(!(/[a-zA-Z]/.test(c)&&/\d/.test(c))){l.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",l.classList.add("error");return}k.disabled=!0,k.textContent=t("msg-saving")||"保存中...";try{const r={username:i,password:c};p&&(r.email=p);const v=await apiPost("/api/team/employees",r),E=v?await v.json().catch(()=>({})):{};if(v&&v.ok&&E&&E.ok){showToast(t("team-added")||"员工已添加","success"),n(),Fe();return}const x=E&&E.detail||"unknown",R={"team.username_exists":t("team-username-exists")||"用户名已被占用","team.email_exists":t("team-email-exists")||"邮箱已被占用","team.create_failed":t("team-create-failed")||"创建失败","team.only_owner_or_super":t("team-no-permission")||"无权限","team.no_tenant":t("team-no-tenant")||"请先升级账号","pwd.too_short":t("pwd-too-short")||"密码至少 8 位","pwd.too_weak_numeric":t("pwd-too-weak-numeric")||"不能是纯数字","pwd.too_weak_common":t("pwd-too-weak-common")||"这个密码太常见 · 请换一个","pwd.too_weak":t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};l.textContent=R[x]||(t("team-create-failed")||"创建失败")+" ("+x+")",l.classList.add("error")}catch{l.textContent=t("team-create-failed")||"创建失败",l.classList.add("error")}finally{k.disabled=!1,k.textContent=t("team-add")||"添加员工"}});function a(o){o.key==="Escape"&&(n(),document.removeEventListener("keydown",a))}document.addEventListener("keydown",a)}async function on(e,n){try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}/active`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({is_active:!!n})})).ok){Fe();return}showToast(t("team-toggle-failed")||"操作失败","error")}catch{showToast(t("team-toggle-failed")||"操作失败","error")}}async function sn(e,n){const o=(t("team-confirm-remove")||"确认移除员工「{name}」?他的所有识别记录会保留 · 但他将无法登录").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{danger:!0,okText:t("team-remove")}))try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){showToast(t("team-removed")||"已移除","success"),Fe();return}showToast(t("team-remove-failed")||"移除失败","error")}catch{showToast(t("team-remove-failed")||"移除失败","error")}}async function rn(e,n){const o=(t("team-reset-pwd-confirm")||"给员工「{name}」发送改密链接?系统将通过员工的邮箱或 LINE 发送一个 15 分钟内有效的链接 · 员工自己点链接改密码 · 您看不到密码").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{okText:t("team-reset-link-send-btn")||"发送链接"}))try{const u=await fetch(`/api/team/employees/${encodeURIComponent(e)}/reset-password`,{method:"POST",headers:{Authorization:"Bearer "+token}}),l=await u.json().catch(()=>({}));if(u.status===400&&l.detail==="team.reset_no_channel"){showToast(t("team-reset-no-channel")||"员工尚未绑定邮箱或 LINE · 请先帮员工补充邮箱再重置","error");return}if(!u.ok){showToast(t("team-reset-pwd-fail")||"发送失败","error");return}if(l.channel==="line"||l.channel==="email"){const k=t("team-reset-link-sent")||"改密链接已通过 {ch} 发送给员工 · 链接 15 分钟内有效",i=l.channel==="line"?"LINE":t("team-reset-via-email")||"邮箱";showToast(k.replace("{ch}",i),"success");return}showToast(t("team-reset-pwd-fail")||"发送失败","error")}catch{showToast(t("team-reset-pwd-fail")||"发送失败","error")}}document.addEventListener("click",e=>{if(e.target.closest("#btn-add-employee")){e.preventDefault(),an();return}const n=e.target.closest("[data-toggle-employee]");if(n){e.preventDefault(),on(n.dataset.toggleEmployee,n.dataset.active==="false");return}const a=e.target.closest("[data-remove-employee]");if(a){e.preventDefault(),sn(a.dataset.removeEmployee,a.dataset.name||"");return}const o=e.target.closest("[data-reset-pwd-employee]");if(o){e.preventDefault(),rn(o.dataset.resetPwdEmployee,o.dataset.name||"");return}const s=e.target.closest("[data-assign-clients]");if(s){e.preventDefault(),typeof window.openAssignClientsModal=="function"&&window.openAssignClientsModal(s.dataset.assignClients,s.dataset.name||"");return}});window.loadTeamList=Fe;function ln(e){document.querySelectorAll(".auto-nav-item").forEach(n=>{n.classList.toggle("active",n.dataset.autoTab===e)}),document.querySelectorAll(".auto-panel").forEach(n=>{n.classList.toggle("active",n.dataset.autoPanel===e)}),e==="email"&&typeof window._loadEmailIngestPanel=="function"?(window._loadEmailIngestPanel(),typeof window._startEmailLogAutoRefresh=="function"&&window._startEmailLogAutoRefresh()):typeof window._stopEmailLogAutoRefresh=="function"&&window._stopEmailLogAutoRefresh(),e==="bank"&&typeof window._loadBankReconPanel=="function"&&window._loadBankReconPanel(),e==="linebot"&&typeof window._loadLineBotPanel=="function"&&window._loadLineBotPanel(),e==="alert"&&typeof window._loadNotificationsPanel=="function"&&window._loadNotificationsPanel(),e==="folder"&&typeof window._loadFolderWatcherPanel=="function"&&window._loadFolderWatcherPanel()}window.switchAutomationTab=ln;typeof console<"u"&&typeof console.info=="function"&&console.info("[pearnly] vite bundle loaded · dashboard + billing + test-center + workspace-switcher + recon-center + assign-clients + access-log + notifications + recon-batch + welcome-wizard + archive-settings");
//# sourceMappingURL=main.js.map
