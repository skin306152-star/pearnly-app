// ============================================================
// REFACTOR-WB (2026-06-02) · 异常栏 · 抽屉渲染 renderDrawer + renderWhyDetail · 从 exceptions.js 抽出 · verbatim 0 改逻辑。
// ============================================================
/* eslint-disable no-useless-assignment -- verbatim · 非 bug */
/* global escapeHtml, showConfirm, currentLang, humanizeError */
import { _drawer } from './exceptions-store.js';
import { _v, _money, excRuleLabel } from './exceptions-helpers.js';
import { _loadDrawerPdf, _extractFields, actionSaveFields } from './exceptions-drawer.js';
import { imageViewerHtml, mountImageViewer } from './image-viewer.js';

// 异常抽屉左栏原图查看器实例(重渲/换单前先清旧 · 防 window 监听泄漏)
let _excViewerCleanup: (() => void) | null = null;

type WhyDetail = {
    // 新引擎 finding 形状
    message_key?: string;
    evidence?: Record<string, unknown>;
    // 旧库存行(部署前)形状
    subtotal?: unknown;
    vat?: unknown;
    total_expected?: unknown;
    total_actual?: unknown;
    diff?: unknown;
    tax_id_normalized?: string;
    tax_id_raw?: string;
    actual_length?: unknown;
    level?: string;
    match_filename?: string;
    match_invoice_no?: string;
    confidence?: string;
};

type ExcRow = {
    seller_name?: string;
    filename?: string;
    status?: string;
    invoice_date?: string;
    created_at?: string;
    invoice_no?: string;
    severity?: string;
    rule_code?: string;
    detail?: WhyDetail;
    history_id?: string;
};

type DrawerHistory = {
    pages?: Array<{ is_duplicate?: boolean; is_copy?: boolean; fields?: unknown }>;
    _err?: unknown;
};

function _whyRow(labelKey: string, val: string, cls?: string) {
    return `<div class="exc-why-detail-row"><b>${escapeHtml(t(labelKey))}</b><span class="${cls || ''}">${escapeHtml(val)}</span></div>`;
}

// 新引擎 finding 的 detail = {message_key, evidence}。按 message_key 把证据渲成人话:
// 标红实测值(v-bad)、标绿应有值(v-good),与旧路径同一套视觉。
function renderRiskDetail(messageKey: string, ev: Record<string, unknown>) {
    const m = (k: string) => _money(ev[k]);
    const s = (k: string) => (ev[k] === null || ev[k] === undefined ? '—' : String(ev[k]));
    switch (messageKey) {
        case 'risk.vat_mismatch':
            return (
                _whyRow('exc-fld-subtotal', m('net_amount')) +
                _whyRow('exc-fld-vat', m('vat_amount'), 'v-bad') +
                _whyRow('exc-detail-expected', m('expected_vat'), 'v-good')
            );
        case 'risk.total_mismatch': {
            const net = Number(ev.net_amount) || 0;
            const vat = Number(ev.vat_amount) || 0;
            return (
                _whyRow('exc-fld-subtotal', m('net_amount')) +
                _whyRow('exc-fld-vat', m('vat_amount')) +
                _whyRow('exc-fld-total', m('total_amount'), 'v-bad') +
                _whyRow('exc-detail-expected', _money(net + vat), 'v-good')
            );
        }
        case 'risk.line_sum_mismatch':
            return (
                _whyRow('exc-ev-lines-sum', m('lines_sum'), 'v-bad') +
                _whyRow('exc-fld-subtotal', m('net_amount'), 'v-good')
            );
        case 'risk.line_amount_mismatch': {
            const qty = Number(ev.qty) || 0;
            const unit = Number(ev.unit_price) || 0;
            return (
                _whyRow('exc-ev-amount', m('amount'), 'v-bad') +
                _whyRow('exc-detail-expected', _money(qty * unit), 'v-good')
            );
        }
        case 'risk.multipage_mismatch':
            return _whyRow('exc-ev-pages', s('pages'));
        case 'risk.seller_tax_id_invalid':
            return _whyRow('exc-fld-seller-tax', s('seller_tax_id'), 'v-bad');
        case 'risk.buyer_tax_id_invalid':
            return _whyRow('exc-fld-buyer-tax', s('buyer_tax_id'), 'v-bad');
        case 'risk.tax_id_placeholder':
            return _whyRow('exc-ev-value', s('value'), 'v-bad');
        case 'risk.invoice_date_unparseable':
        case 'risk.invoice_date_future':
            return _whyRow('exc-fld-date', s('invoice_date'), 'v-bad');
        case 'risk.invoice_date_out_of_period':
            return (
                _whyRow('exc-fld-date', s('invoice_date'), 'v-bad') +
                _whyRow('exc-ev-period-start', s('period_start')) +
                _whyRow('exc-ev-period-end', s('period_end'))
            );
        case 'risk.duplicate_exact':
            return (
                (ev.invoice_no ? _whyRow('exc-fld-invoice-no', s('invoice_no')) : '') +
                _whyRow('exc-fld-seller-tax', s('seller_tax_id'))
            );
        case 'risk.duplicate_suspected': {
            const ids = Array.isArray(ev.candidate_history_ids)
                ? ev.candidate_history_ids.length
                : 0;
            return _whyRow('exc-ev-dup-count', String(ids));
        }
        case 'risk.supplier_not_allowlisted':
            return (
                _whyRow('exc-fld-seller', s('seller_name')) +
                _whyRow('exc-fld-seller-tax', s('seller_tax_id'))
            );
        case 'risk.supplier_force_review':
            return (
                _whyRow('exc-ev-reason', s('reason'), 'v-bad') +
                _whyRow('exc-fld-seller-tax', s('seller_tax_id'))
            );
        case 'risk.amount_over_limit':
            return (
                _whyRow('exc-ev-amount', m('value'), 'v-bad') +
                _whyRow('exc-ev-limit', m('limit'), 'v-good')
            );
        case 'risk.category_no_auto_push':
            return _whyRow('exc-ev-category', s('category'));
        default:
            return `<div class="exc-why-detail-row"><span style="font-size:11px;">${escapeHtml(JSON.stringify(ev))}</span></div>`;
    }
}

// 「为什么被拦」详情段 · 新引擎走 message_key/evidence;旧库存行与 confidence_low 走旧形状
function renderWhyDetail(rule: string, detail: WhyDetail) {
    detail = detail || {};
    if (detail.message_key) {
        return renderRiskDetail(detail.message_key, detail.evidence || {});
    }
    if (rule === 'math_mismatch') {
        return `
            <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-fld-subtotal'))}</b><span>${escapeHtml(_money(detail.subtotal))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-fld-vat'))}</b><span>${escapeHtml(_money(detail.vat))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-detail-expected'))}</b><span class="v-good">${escapeHtml(_money(detail.total_expected))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-detail-actual'))}</b><span class="v-bad">${escapeHtml(_money(detail.total_actual))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-detail-diff'))}</b><span class="v-bad">${escapeHtml(_money(detail.diff))}</span></div>
        `;
    }
    if (rule === 'tax_id_format_invalid') {
        return `
            <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-fld-seller-tax'))}</b><span class="v-bad">${escapeHtml(detail.tax_id_normalized || detail.tax_id_raw || '—')}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-detail-tax-len'))}</b><span class="v-bad">${escapeHtml(String(detail.actual_length || '?'))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-detail-expected'))}</b><span class="v-good">${escapeHtml(t('exc-detail-tax-expected'))}</span></div>
        `;
    }
    if (rule === 'duplicate') {
        const lvl =
            detail.level === 'exact'
                ? t('exc-detail-dup-level-exact')
                : t('exc-detail-dup-level-likely');
        return `
            <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-detail-dup-match'))}</b><span>${escapeHtml(detail.match_filename || '—')}</span></div>
            ${detail.match_invoice_no ? `<div class="exc-why-detail-row"><b>${escapeHtml(t('exc-fld-invoice-no'))}</b><span>${escapeHtml(detail.match_invoice_no)}</span></div>` : ''}
            <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-detail-expected'))}</b><span>${escapeHtml(lvl)}</span></div>
        `;
    }
    if (rule === 'confidence_low') {
        return `
            <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-detail-conf-label'))}</b><span class="v-bad">${escapeHtml(detail.confidence || '—')}</span></div>
        `;
    }
    if (rule === 'amount_missing') {
        return `<div class="exc-why-detail-row" style="justify-content:center;color:var(--danger);"><span>${escapeHtml(t('exc-detail-missing'))}</span></div>`;
    }
    // 兜底:JSON 直出
    return `<div class="exc-why-detail-row"><span style="font-size:11px;">${escapeHtml(JSON.stringify(detail))}</span></div>`;
}

function renderDrawer() {
    const row = _drawer.excRow as ExcRow;
    if (!row) return;

    // Header
    const seller = row.seller_name && row.seller_name.trim() ? row.seller_name : t('exc-no-seller');
    const filename = row.filename || '—';
    document.getElementById('exc-drawer-title')!.textContent = filename;

    const statusKey = 'exc-status-' + (row.status || 'pending');
    const statusLabel = t(statusKey) || row.status;
    const statusCls = 's-' + (row.status || 'pending');
    const date = (row.invoice_date || row.created_at || '').slice(0, 10);
    document.getElementById('exc-drawer-sub')!.innerHTML = `
        <span>${escapeHtml(seller)}</span>
        ${row.invoice_no ? `<span>· ${escapeHtml(row.invoice_no)}</span>` : ''}
        ${date ? `<span>· ${escapeHtml(date)}</span>` : ''}
        <span class="exc-status-chip ${statusCls}">${escapeHtml(statusLabel)}</span>
    `;

    // Body · 两段
    const sev = row.severity || 'medium';
    const ruleLabel = excRuleLabel(row);
    const whyDetail = renderWhyDetail(row.rule_code!, row.detail || {});

    const f = _extractFields(_drawer.history as DrawerHistory) as Record<string, unknown>;
    const fieldsLoading = _drawer.history === null;
    const fieldsErr = _drawer.history && (_drawer.history as DrawerHistory)._err;

    // 标记哪些字段触发了规则(高亮红)· 新码与对应旧码归同一组字段
    const flagSet = new Set();
    const fc = row.rule_code || '';
    if (['math_mismatch', 'R-VAT-01', 'R-VAT-02', 'R-SUM-01', 'R-LINE-01'].includes(fc)) {
        flagSet.add('subtotal');
        flagSet.add('vat');
        flagSet.add('total_amount');
    } else if (fc === 'R-MULTIPAGE-01' || fc === 'R-LIMIT-01') {
        flagSet.add('total_amount');
    } else if (fc === 'tax_id_format_invalid' || fc === 'R-TAXID-01') {
        flagSet.add('seller_tax');
    } else if (fc === 'R-TAXID-02') {
        flagSet.add('buyer_tax');
    } else if (fc === 'R-TAXID-03') {
        flagSet.add('seller_tax');
        flagSet.add('buyer_tax');
    } else if (fc === 'R-DATE-01' || fc === 'R-DATE-02') {
        flagSet.add('date');
    } else if (fc === 'R-DUP-01' || fc === 'R-DUP-02') {
        flagSet.add('invoice_number');
    } else if (fc === 'R-SUP-01' || fc === 'R-SUP-02') {
        flagSet.add('seller_name');
        flagSet.add('seller_tax');
    } else if (fc === 'amount_missing') {
        flagSet.add('total_amount');
        flagSet.add('invoice_number');
    }

    const editing = !!_drawer.editing;
    const editF = (_drawer.editFields || {}) as Record<string, unknown>;
    const fld = (key: string, labelKey: string, isMoney: boolean) => {
        if (fieldsLoading) {
            return `<div class="exc-field-row"><label>${escapeHtml(t(labelKey))}</label><span class="val empty">…</span></div>`;
        }
        const v = editing
            ? editF[key] !== undefined
                ? editF[key]
                : f[key] !== undefined && f[key] !== null
                  ? f[key]
                  : ''
            : f[key];
        const flagged = flagSet.has(key) ? 'flagged' : '';
        if (editing) {
            const inputType = isMoney ? 'number' : 'text';
            const stepAttr = isMoney ? ' step="0.01" inputmode="decimal"' : '';
            const safeVal = v === null || v === undefined ? '' : String(v).replace(/"/g, '&quot;');
            return `<div class="exc-field-row ${flagged} editing">
                <label>${escapeHtml(t(labelKey))}</label>
                <input class="exc-field-input" type="${inputType}"${stepAttr} data-edit-key="${escapeHtml(key)}" value="${safeVal}">
            </div>`;
        }
        const display = isMoney ? _money(v) : v || '';
        const valHtml =
            v === null || v === undefined || v === ''
                ? `<span class="val empty">${escapeHtml(t('exc-empty-val'))}</span>`
                : `<span class="val">${escapeHtml(display)}</span>`;
        return `<div class="exc-field-row ${flagged}"><label>${escapeHtml(t(labelKey))}</label>${valHtml}</div>`;
    };

    let fieldsHtml = '';
    if (fieldsErr) {
        fieldsHtml = `<div class="exc-drawer-error">${escapeHtml(t('exc-drawer-error'))}</div>`;
    } else {
        fieldsHtml = `
            <div class="exc-fields">
                ${fld('invoice_number', 'exc-fld-invoice-no', false)}
                ${fld('date', 'exc-fld-date', false)}
                ${fld('seller_name', 'exc-fld-seller', false)}
                ${fld('seller_tax', 'exc-fld-seller-tax', false)}
                ${fld('buyer_name', 'exc-fld-buyer', false)}
                ${fld('buyer_tax', 'exc-fld-buyer-tax', false)}
                ${fld('subtotal', 'exc-fld-subtotal', true)}
                ${fld('vat', 'exc-fld-vat', true)}
                ${fld('total_amount', 'exc-fld-total', true)}
            </div>
        `;
    }

    // v118.20.7 · 左栏 PDF 预览(blob URL · 状态机)
    const pdfPaneHtml = (() => {
        if (_drawer.pdfStatus === 'loading' || _drawer.pdfStatus === 'idle') {
            return `
                <div class="exc-pdf-toolbar">
                    <span class="exc-pdf-toolbar-title">${escapeHtml(t('exc-pdf-loading'))}</span>
                </div>
                <div class="exc-pdf-empty">
                    <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M18 4v8a14 14 0 1014 14"/>
                    </svg>
                    <div class="exc-pdf-empty-msg">${escapeHtml(t('exc-pdf-loading'))}</div>
                </div>
            `;
        }
        if (_drawer.pdfStatus === 'empty') {
            return `
                <div class="exc-pdf-toolbar">
                    <span class="exc-pdf-toolbar-title">${escapeHtml(t('exc-pdf-empty-title'))}</span>
                </div>
                <div class="exc-pdf-empty">
                    <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M9 4h12l6 6v22H9z"/>
                        <path d="M21 4v6h6"/>
                        <line x1="14" y1="20" x2="22" y2="20"/>
                    </svg>
                    <div class="exc-pdf-empty-msg">${escapeHtml(t('exc-pdf-empty'))}</div>
                </div>
            `;
        }
        if (_drawer.pdfStatus === 'error') {
            return `
                <div class="exc-pdf-toolbar">
                    <span class="exc-pdf-toolbar-title">${escapeHtml(t('exc-pdf-error-title'))}</span>
                    <div class="exc-pdf-toolbar-actions">
                        <button class="exc-pdf-icon-btn" id="exc-pdf-retry" title="${escapeHtml(t('exc-pdf-retry'))}" type="button">
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
                    <div class="exc-pdf-empty-msg">${escapeHtml(t('exc-pdf-error'))}</div>
                </div>
            `;
        }
        // ready
        const url = _drawer.pdfUrl;
        return `
            <div class="exc-pdf-toolbar">
                <span class="exc-pdf-toolbar-title">${escapeHtml(filename)}</span>
                <div class="exc-pdf-toolbar-actions">
                    <a class="exc-pdf-icon-btn" id="exc-pdf-open-tab" href="${url}" target="_blank" rel="noopener" title="${escapeHtml(t('exc-pdf-open-tab'))}">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M8 2h4v4M12 2L7 7"/>
                            <path d="M11 8v3a1 1 0 01-1 1H3a1 1 0 01-1-1V4a1 1 0 011-1h3"/>
                        </svg>
                    </a>
                    <a class="exc-pdf-icon-btn" id="exc-pdf-download" href="${url}" download="${escapeHtml(filename)}" title="${escapeHtml(t('exc-pdf-download'))}">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M7 2v8M3.5 6.5L7 10l3.5-3.5M2 12h10"/>
                        </svg>
                    </a>
                </div>
            </div>
            ${imageViewerHtml({ help: t('exc-pdf-drag'), noimg: t('exc-pdf-empty'), loading: t('exc-pdf-loading') })}
        `;
    })();

    document.getElementById('exc-drawer-body')!.innerHTML = `
        <div class="exc-pdf-pane">${pdfPaneHtml}</div>
        <div class="exc-fields-pane">
            <div class="exc-section">
                <div class="exc-section-title">
                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="7" cy="7" r="5.5"/><line x1="7" y1="4" x2="7" y2="7.5"/>
                        <circle cx="7" cy="9.6" r="0.5" fill="currentColor"/>
                    </svg>
                    <span>${escapeHtml(t('exc-sect-why'))}</span>
                </div>
                <div class="exc-why sev-${escapeHtml(sev)}">
                    <div class="exc-why-rule">${escapeHtml(ruleLabel)}</div>
                    <div class="exc-why-detail">${whyDetail}</div>
                </div>
            </div>
            <div class="exc-section">
                <div class="exc-section-title">
                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="2" y="2.5" width="10" height="9" rx="1"/>
                        <line x1="4" y1="5.5" x2="10" y2="5.5"/>
                        <line x1="4" y1="8.5" x2="10" y2="8.5"/>
                    </svg>
                    <span>${escapeHtml(t('exc-sect-fields'))}</span>
                    ${
                        row.status === 'pending' && !fieldsLoading && !fieldsErr
                            ? editing
                                ? `
                            <span class="exc-section-actions">
                                <button class="exc-edit-btn ghost" id="exc-fld-cancel" type="button">${escapeHtml(t('exc-fld-cancel'))}</button>
                                <button class="exc-edit-btn primary" id="exc-fld-save" type="button">${escapeHtml(t('exc-fld-save'))}</button>
                            </span>
                        `
                                : `
                            <span class="exc-section-actions">
                                <button class="exc-edit-btn ghost" id="exc-fld-edit" type="button">
                                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M2.5 11.5l1-3 6.5-6.5 2 2-6.5 6.5z"/>
                                        <path d="M9 2.5l2 2"/>
                                    </svg>
                                    <span>${escapeHtml(t('exc-fld-edit'))}</span>
                                </button>
                            </span>
                        `
                            : ''
                    }
                </div>
                ${fieldsHtml}
            </div>
        </div>
    `;

    // 原图就绪后挂共用查看器(page.png · 拖拽/缩放)· 每次重渲先清旧实例
    if (_excViewerCleanup) {
        _excViewerCleanup();
        _excViewerCleanup = null;
    }
    const ivCardEl = document.querySelector('.exc-pdf-pane .iv-card') as HTMLElement | null;
    if (ivCardEl) _excViewerCleanup = mountImageViewer(ivCardEl, row.history_id || null);

    // v118.21.3 · 编辑模式按钮事件
    const editBtn = document.getElementById('exc-fld-edit');
    if (editBtn)
        editBtn.addEventListener('click', () => {
            _drawer.editing = true;
            _drawer.editFields = { ..._extractFields(_drawer.history as DrawerHistory) };
            renderDrawer();
        });
    const cancelBtn = document.getElementById('exc-fld-cancel');
    if (cancelBtn)
        cancelBtn.addEventListener('click', () => {
            _drawer.editing = false;
            _drawer.editFields = null;
            renderDrawer();
        });
    const saveBtn = document.getElementById('exc-fld-save');
    if (saveBtn) saveBtn.addEventListener('click', () => actionSaveFields());
    // 输入收集到 _drawer.editFields(逐字符同步 · 防 renderDrawer 重渲丢值)
    const inputs = document.querySelectorAll('.exc-field-input');
    inputs.forEach((inp) => {
        inp.addEventListener('input', () => {
            if (!_drawer.editFields) _drawer.editFields = {};
            (_drawer.editFields as Record<string, unknown>)[
                (inp as HTMLInputElement).dataset.editKey!
            ] = (inp as HTMLInputElement).value;
        });
    });

    // PDF 重试按钮
    const pdfRetry = document.getElementById('exc-pdf-retry');
    if (pdfRetry && _drawer.openExcId) {
        pdfRetry.addEventListener('click', () => {
            if (_drawer.excRow)
                _loadDrawerPdf((_drawer.excRow as ExcRow).history_id!, _drawer.openExcId);
        });
    }

    // 底部按钮 · 仅 pending 可操作
    const isPending = row.status === 'pending';
    const hasSeller = !!(row.seller_name && row.seller_name.trim());
    const btnResolve = document.getElementById('exc-btn-resolve') as HTMLButtonElement | null;
    const btnIgnore = document.getElementById('exc-btn-ignore') as HTMLButtonElement | null;
    btnResolve!.disabled = !isPending;
    btnIgnore!.disabled = !isPending || !hasSeller;
    // 「忽略此类」副提示(在按钮上方 · 用 title attr)
    btnIgnore!.title = hasSeller ? t('exc-ignore-hint') : t('exc-ignore-no-seller');
}

export { renderDrawer };
