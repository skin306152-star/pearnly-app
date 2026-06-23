// ============================================================
// 共享详情抽屉(openDrawer/closeDrawer + drawer-body 字段渲染)· 被识别记录(history-drawer)/对账(recon-drawer)复用。
// (原 OCR 结果表/搜索/排序已随「上传识别」页删除 · 2026-06-15)
//
// 来源:home.js verbatim 0 改逻辑 · renderResults / 结果表排序+搜索监听 /
//   updateResultsMatchCount / openDrawer / renderWhtBadge / renderField /
//   renderRdActions / renderItems / closeDrawer。
// 加载顺序:home.js(sync)先暴露公共全局(t/escapeHtml/_results/_drawerIdx/
//   onFieldEdit/updateDrawerEditCount/injectOcrPushButton...)→ 本 module(Vite bundle
//   · defer)后跑 · bare 调全局不 import。
// 桥回 home.js:window.renderResults / openDrawer / closeDrawer
//   (home.js bootstrap 的 applyLang 守卫调 + 多处 runtime 调)。
// ERP 推送三件套(injectOcrPushButton...)已迁 ocr-push.js(批2)· openDrawer 经 window.injectOcrPushButton 调。
// 仍在 home.js(后续批):RD 税务 API 簇(rdFetch/callRdVerify/callRdSync/openRdSyncModal)
//   + drawer-body 事件委托 + onFieldEdit/updateDrawerEditCount。
// ============================================================
/* global escapeHtml, _results, _drawerIdx, onFieldEdit, updateDrawerEditCount, injectOcrPushButton */

// ============================================================
// 抽屉
// ============================================================
function openDrawer(idx: number) {
    _drawerIdx = idx;
    const r = _results[idx];
    if (!r) return;
    // 默认窄抽屉;两栏加宽只在识别记录(historizeDrawer 再加 hd-wide)· 不影响对账/OCR 结果
    document.getElementById('drawer')?.classList.remove('hd-wide');

    document.getElementById('drawer-title')!.textContent = r.filename as string;

    // 副标题:页数 + 耗时 + 缓存标记(隐藏引擎档位 · v0.15.6)
    const isCached = !!r.from_cache;
    const timeText = isCached
        ? t('badge-cached-hint')
        : `${((r.elapsed_ms as number) / 1000).toFixed(1)}s`;
    document.getElementById('drawer-sub')!.innerHTML = `
        <span>${r.page_count} ${t('pages-unit')} · ${escapeHtml(timeText)}</span>
        ${isCached ? `<span class="engine-badge cached">${escapeHtml(t('badge-cached'))}</span>` : ''}
        <span class="drawer-edit-count" id="drawer-edit-count-sub"></span>
    `;
    updateDrawerEditCount();

    const canEdit = _userInfo && _userInfo.can_edit_fields;
    const canVerifyTax = _userInfo && _userInfo.can_verify_tax;

    const f = r.merged_fields;
    const body = document.getElementById('drawer-body') as HTMLElement;

    const readonlyBanner = canEdit
        ? ''
        : `
        <div class="drawer-readonly-banner">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="9" width="12" height="9" rx="1"/><path d="M7 9V6a3 3 0 016 0v3"/></svg>
            <span>${t('readonly-banner')}</span>
        </div>
    `;

    const taxBadge = canVerifyTax
        ? ''
        : `<span class="tax-badge unverified" data-tip="${escapeHtml(t('tax-tip-unverified'))}">${t('tax-unverified')}</span>`;

    body.innerHTML = `
        ${readonlyBanner}

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
                <span>${escapeHtml(t('drawer-decision-title'))}</span>
            </div>
            <div class="drawer-decision-grid">
                <!-- 归属客户(左) -->
                <div class="drawer-client-card" data-field-wrap="client_id">
                    <div class="drawer-client-head">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M11 14v-1.2a2.4 2.4 0 00-2.4-2.4H4a2.4 2.4 0 00-2.4 2.4V14"/>
                            <circle cx="6.4" cy="5.2" r="2.4"/>
                        </svg>
                        <span>${escapeHtml(t('drawer-client-label'))}</span>
                    </div>
                    <div class="drawer-client-body">
                        <select class="drawer-client-select" id="drawer-client-select" ${canEdit ? '' : 'disabled'}>
                            <option value="">${escapeHtml(t('drawer-client-none'))}</option>
                        </select>
                        <button class="drawer-client-add" id="drawer-client-add" type="button" title="${escapeHtml(t('client-new'))}">
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
                        <span>${escapeHtml(t('drawer-suggest-category'))}</span>
                        ${
                            f.category || r.category_tag
                                ? `<span class="drawer-suggest-learned" id="drawer-cat-learned-tag" title="${escapeHtml(t('drawer-suggest-learned-tip'))}">${escapeHtml(t('drawer-suggest-learned'))}</span>`
                                : `<span class="drawer-suggest-empty">${escapeHtml(t('drawer-suggest-empty'))}</span>`
                        }
                    </div>
                    <div class="drawer-suggest-body">
                        <input type="text" class="drawer-suggest-input" id="drawer-cat-input" data-field="category_tag"
                               list="drawer-cat-datalist"
                               placeholder="${escapeHtml(t('drawer-suggest-placeholder'))}"
                               value="${escapeHtml((r.edits && r.edits.category_tag !== undefined ? r.edits.category_tag : f.category || r.category_tag) || '')}"
                               ${canEdit ? '' : 'readonly'}>
                        <datalist id="drawer-cat-datalist"></datalist>
                    </div>
                </div>
            </div>
            <div class="drawer-decision-hint">${escapeHtml(t('drawer-suggest-hint'))}</div>
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 2h8l3 3v13H5z"/><path d="M13 2v3h3"/><path d="M8 10h6M8 13h6"/></svg>
                ${t('drawer-sec-basic')}
            </div>
            ${renderField('invoice_number', 'drawer-lbl-invoice', f.invoice_number, 'input', canEdit)}
            ${renderField('date', 'drawer-lbl-date', f.date, 'input', canEdit)}
            ${f.date_raw && f.date_raw !== f.date ? `<div class="date-raw-hint" title="${escapeHtml(t('drawer-date-raw-tip'))}">${escapeHtml(t('drawer-date-raw-label'))}: ${escapeHtml(f.date_raw)}</div>` : ''}
            ${renderField('subtotal', 'drawer-lbl-subtotal', f.subtotal, 'input', canEdit)}
            ${renderField('vat', 'drawer-lbl-vat', f.vat, 'input', canEdit)}
            ${renderField('total_amount', 'drawer-lbl-total', f.total_amount, 'input', canEdit)}
            ${
                f.wht_amount || f.wht_rate
                    ? `
                ${renderField('wht_amount', 'drawer-lbl-wht-amount', f.wht_amount, 'input', canEdit, renderWhtBadge(f.wht_rate))}
            `
                    : ''
            }
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 18V8h14v10M3 8l2-4h10l2 4M7 12h2M11 12h2"/></svg>
                ${t('drawer-sec-seller')}
            </div>
            ${renderField('seller_name', 'drawer-lbl-name', f.seller_name, 'input', canEdit)}
            ${renderField('seller_tax', 'drawer-lbl-tax', f.seller_tax, 'input', canEdit, taxBadge, renderRdActions('seller'))}
            ${renderField('seller_addr', 'drawer-lbl-addr', f.seller_addr, 'textarea', canEdit)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="10" cy="6" r="3"/><path d="M3 18c0-3.9 3.1-7 7-7s7 3.1 7 7"/></svg>
                ${t('drawer-sec-buyer')}
            </div>
            ${renderField('buyer_name', 'drawer-lbl-name', f.buyer_name, 'input', canEdit)}
            ${renderField('buyer_tax', 'drawer-lbl-tax', f.buyer_tax, 'input', canEdit, taxBadge, renderRdActions('buyer'))}
            ${renderField('buyer_addr', 'drawer-lbl-addr', f.buyer_addr, 'textarea', canEdit)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 7l7-4 7 4v7l-7 4-7-4z"/><path d="M3 7l7 4 7-4M10 11v8"/></svg>
                ${t('drawer-sec-items')}
            </div>
            ${f.items && (f.items as unknown[]).length > 0 ? renderItems(f.items as Array<Record<string, unknown>>) : `<div class="drawer-items-empty">${t('drawer-items-empty')}</div>`}
        </div>

        <div class="drawer-section">
            ${renderField('notes', 'drawer-lbl-notes', f.notes, 'textarea', canEdit)}
        </div>

        <details class="raw-text">
            <summary>${t('raw-text')}</summary>
            <pre>${escapeHtml((r.pages as Array<Record<string, unknown>>).map((p) => `--- Page ${p.page || p.page_number || '?'} ---\n${p.raw_text || p.text || ''}`).join('\n\n'))}</pre>
        </details>
    `;

    if (canEdit) {
        body.querySelectorAll('[data-field]').forEach((input) => {
            input.addEventListener('input', onFieldEdit);
        });
    } else {
        // v0.15 · 扁平权限下所有人都能编辑 · 此分支保留只读状态(不再弹升级)
        body.querySelectorAll('[data-field]').forEach((input) => {
            input.setAttribute('readonly', 'readonly');
        });
    }

    document.getElementById('drawer-mask')!.classList.add('show');
    document.getElementById('drawer')!.classList.add('show');

    // 识别页抽屉底部推 ERP 按钮(历史模式由另一个函数 injectHistorySaveButton 处理)
    injectOcrPushButton();

    // v118.16 · 修 BUG · 识别中心抽屉打开时也填充客户下拉(之前漏调 · 单据记录抽屉有但识别中心没有)
    if (typeof window.bindDrawerClient === 'function') {
        const hid = r._historyId || r.history_id || null;
        window.bindDrawerClient(hid, r.client_id || null);
    }

    // v118.18 · 推荐分类 datalist 自动补全(用过的科目)
    if (typeof window.fillCategoryDatalist === 'function') {
        window.fillCategoryDatalist();
    }

    // v118.19 · 键盘流 · 如果记账科目为空 · 自动 focus 让会计直接键盘录入
    // 之所以 focus 科目而不是客户:学过的供应商客户通常自动绑定 · 科目才是会计每天主动填的字段
    setTimeout(() => {
        const catInput = document.getElementById('drawer-cat-input') as HTMLInputElement | null;
        if (catInput && !catInput.value && !catInput.readOnly) {
            catInput.focus();
        }
    }, 80);
}

function renderWhtBadge(rate: unknown) {
    if (!rate) return '';
    return `<span class="wht-badge">${escapeHtml(rate)}%</span>`;
}

function renderField(
    key: string,
    labelKey: string,
    value: unknown,
    type: string,
    canEdit: unknown,
    badgeHtml?: string,
    actionsHtml?: string
) {
    const r = _results[_drawerIdx];
    const editedValue = r && r.edits[key] !== undefined ? r.edits[key] : value;
    const edited = r && r.edits[key] !== undefined && r.edits[key] !== value;
    const valEscaped = escapeHtml(editedValue ?? '');
    const readonlyCls = canEdit ? '' : 'readonly';
    const inputHtml =
        type === 'textarea'
            ? `<textarea data-field="${key}" rows="2">${valEscaped}</textarea>`
            : `<input type="text" data-field="${key}" value="${valEscaped}">`;
    return `
        <div class="drawer-field ${edited ? 'edited' : ''} ${readonlyCls}" data-field-wrap="${key}">
            <label class="drawer-field-label">
                <span class="drawer-field-edited-dot"></span>
                ${t(labelKey)}
                ${badgeHtml || ''}
                ${actionsHtml ? `<span class="drawer-field-actions">${actionsHtml}</span>` : ''}
            </label>
            ${inputHtml}
        </div>
    `;
}

// 渲染税号字段右上角的 RD 按钮(校验 + 同步)
function renderRdActions(side: string) {
    // side: 'seller' 或 'buyer'
    const canVerify = _userInfo && _userInfo.can_verify_tax;
    if (!canVerify) {
        // Free 用户:显示锁标(点击触发升级弹窗)
        return `<button class="rd-btn-locked" data-upgrade="plus" type="button" title="${escapeHtml(t('rd-tip-upgrade'))}">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="7" width="10" height="7" rx="1"/><path d="M5 7V5a3 3 0 016 0v2"/></svg>
        </button>`;
    }
    return `
        <button class="rd-btn rd-btn-verify" data-rd-action="verify" data-rd-side="${side}" type="button">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 8l3 3 7-7"/></svg>
            ${t('rd-btn-verify')}
        </button>
        <button class="rd-btn rd-btn-sync" data-rd-action="sync" data-rd-side="${side}" type="button">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 8a5 5 0 019-3l1.5 1.5M13 8a5 5 0 01-9 3L2.5 9.5M13 3v3h-3M3 13v-3h3"/></svg>
            ${t('rd-btn-sync')}
        </button>
        <span class="rd-status" data-rd-status="${side}"></span>
    `;
}

function renderItems(items: Array<Record<string, unknown>>) {
    return `
        <div class="drawer-items-header">
            <div>${t('drawer-item-name')}</div>
            <div>${t('drawer-item-qty')}</div>
            <div>${t('drawer-item-price')}</div>
            <div>${t('drawer-item-sub')}</div>
        </div>
        ${items
            .map(
                (it) => `
            <div class="drawer-item-row">
                <div>${escapeHtml(it.name || '')}</div>
                <div>${escapeHtml(it.qty || it.quantity || '')}</div>
                <div>${escapeHtml(it.price || it.unit_price || '')}</div>
                <div>${escapeHtml(it.subtotal || it.total || '')}</div>
            </div>
        `
            )
            .join('')}
    `;
}

function closeDrawer() {
    document.getElementById('drawer-mask')!.classList.remove('show');
    const dr = document.getElementById('drawer')!;
    dr.classList.remove('show');
    dr.classList.remove('hd-wide'); // 关抽屉即回窄态默认(识别记录两栏加宽的对称复位)
    // 清理抽屉底部的按钮栏(下次打开会重新注入)
    const existingHistoryBar = document.getElementById('drawer-history-save');
    if (existingHistoryBar) existingHistoryBar.remove();
    const existingOcrBar = document.getElementById('drawer-ocr-push');
    if (existingOcrBar) existingOcrBar.remove();
    // v105.2 · 清掉头部推送按钮
    const headerPushBtn = document.getElementById('drawer-ocr-push-btn');
    if (headerPushBtn) headerPushBtn.remove();
    _drawerIdx = -1;
}

// 桥回 home.js:bootstrap(applyLang 守卫)与多处 runtime 调用
window.openDrawer = openDrawer;
window.closeDrawer = closeDrawer;
