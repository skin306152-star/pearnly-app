// ============================================================
// ERP 推送失败卡 · 自助修复动作(待补科目 / 绑主体)
//
// 「推送异常」tab 并入「推送日志」后(2026-06-26)· 这些修复入口挂在推送日志的失败卡上。
// 卡内下拉面板(科目槽 / 账套主体)+ 提交(补科目重推 / 绑主体重推)· 成功后重拉推送日志
// (单一状态源 · 铁律 #12 · 修好的行自动翻态/消失,不维护乐观态)。面板 HTML 由 erp-log-card
// 注入失败卡,事件在 erp-integration 的列表委托里绑定(调本模块函数)。
// ============================================================
/* global t, escapeHtml, showToast */

// 失败卡修复面板要用到的最小字段(由 list_push_logs 在失败行附带)。
type RepairItem = {
    id: string;
    endpoint_id?: string;
    account_fix?: { direction?: string; slots?: string[]; bad_code?: string };
    bind_fix?: { can_bind?: boolean };
    // 缺库存商品 → 会计补期初(数量/单位成本/日期)后重推(B1·批次二)。
    stock_fix?: { items?: Array<{ name?: string; stkcod?: string }> };
};

// 待补科目卡:科目槽 → 角色文案键(收入/应收/销项税 + 采购/应付/进项税)。
const _ERP_ACCT_SLOT_LABEL: Record<string, string> = {
    revenue_acc: 'erp-acctfix-revenue',
    ar_acc: 'erp-acctfix-ar',
    vat_output_acc: 'erp-acctfix-vat-output',
    fallback_acc: 'erp-acctfix-purchase',
    ap_acc: 'erp-acctfix-ap',
    vat_input_acc: 'erp-acctfix-vat-input',
};

function _erpExcTok(): string {
    return localStorage.getItem('mrpilot_token') || '';
}

// 该端点上报的账套科目表(GLACC)· 供待补科目卡下拉(显示 代码 · 名字)。
function _erpExcChart(endpointId?: string): Array<{ code: string; name?: string }> {
    const eps = Array.isArray(window._erpEndpoints) ? window._erpEndpoints : [];
    const ep = eps.find((e: any) => e && String(e.id) === String(endpointId || ''));
    const ra = ep && (ep as any).config && (ep as any).config.reported_accounts;
    return Array.isArray(ra) ? ra : [];
}

// 修复成功后重拉推送日志 + 刷新侧栏异常红点(OCR 异常徽标 · 无害共用)。
function _erpExcReload() {
    if (typeof window.loadErpLogs === 'function') {
        try {
            window.loadErpLogs();
        } catch (_) {}
    }
    if (typeof window.refreshExcBadge === 'function') {
        try {
            window.refreshExcBadge();
        } catch (_) {}
    }
}

// 待补科目卡的下拉面板(每个缺的科目槽一个下拉 · 选项=该账套上报科目表 代码·名字)。
function _erpExcAcctPanel(it: RepairItem): string {
    const slots = (it.account_fix && it.account_fix.slots) || [];
    const chart = _erpExcChart(it.endpoint_id);
    if (!chart.length) {
        return `<div class="erp-exc-acctfix" data-acctfix-panel="${escapeHtml(it.id)}" hidden>
            <div class="erp-exc-acctfix-nochart">${escapeHtml(t('erp-acctfix-nochart'))}</div></div>`;
    }
    const opts = chart
        .map(
            (a) =>
                `<option value="${escapeHtml(a.code)}">${escapeHtml(a.code)}${a.name ? ' · ' + escapeHtml(a.name) : ''}</option>`
        )
        .join('');
    const slotsHtml = slots
        .map(
            (s) =>
                `<label class="erp-exc-acctfix-slot"><span>${escapeHtml(t(_ERP_ACCT_SLOT_LABEL[s] || s))}</span>` +
                `<select data-acctfix-slot="${escapeHtml(s)}"><option value="">${escapeHtml(t('erp-acctfix-pick'))}</option>${opts}</select></label>`
        )
        .join('');
    return `<div class="erp-exc-acctfix" data-acctfix-panel="${escapeHtml(it.id)}" hidden>
        <div class="erp-exc-acctfix-slots">${slotsHtml}</div>
        <label class="erp-exc-acctfix-remember"><input type="checkbox" data-acctfix-remember> ${escapeHtml(t('erp-acctfix-remember'))}</label>
        <div class="erp-exc-acctfix-act">
            <button class="btn btn-sm btn-primary" type="button" data-acctfix-submit="${escapeHtml(it.id)}">${escapeHtml(t('erp-acctfix-submit'))}</button>
            <button class="btn btn-sm btn-ghost" type="button" data-acctfix-cancel="${escapeHtml(it.id)}">${escapeHtml(t('erp-acctfix-cancel'))}</button>
        </div></div>`;
}

async function _erpExcAccountFix(logId: string, panel: HTMLElement, btn: HTMLButtonElement | null) {
    const accounts: Record<string, string> = {};
    panel.querySelectorAll('select[data-acctfix-slot]').forEach((sel) => {
        const slot = (sel as HTMLElement).dataset.acctfixSlot as string;
        const val = (sel as HTMLSelectElement).value.trim();
        if (slot && val) accounts[slot] = val;
    });
    if (!Object.keys(accounts).length) {
        showToast(t('erp-acctfix-need-pick'), 'error');
        return;
    }
    const remember = !!(panel.querySelector('[data-acctfix-remember]') as HTMLInputElement | null)
        ?.checked;
    if (btn) {
        btn.disabled = true;
        btn.textContent = t('erp-exc-retrying');
    }
    try {
        const resp = await fetch(
            '/api/erp/logs/' + encodeURIComponent(logId) + '/express-account-fix',
            {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + _erpExcTok(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ accounts, remember }),
            }
        );
        const data = await resp.json().catch(() => ({}));
        showToast(
            resp.ok && data.ok ? t('erp-acctfix-ok') : t('erp-acctfix-fail'),
            resp.ok && data.ok ? 'success' : 'error'
        );
    } catch (e) {
        showToast(t('erp-acctfix-fail'), 'error');
    }
    _erpExcReload();
}

// 账套主体(workspace_clients)· 绑主体面板下拉的数据源(全站共用 _workspaceClientsCache)。
function _erpExcClients(): Array<{ id: number; name?: string; tax_id?: string }> {
    const c = window._workspaceClientsCache;
    return Array.isArray(c) ? (c as Array<{ id: number; name?: string; tax_id?: string }>) : [];
}

// 列表可能先于账套切换器加载 → 懒取一次主体(绑主体面板同步渲染前须有数据)。
// 复用账套切换器的 canonical loader(带 workspace 作用域头 + 401 处理),不另起 fetch。
async function _erpExcEnsureClients(): Promise<void> {
    if (_erpExcClients().length) return;
    const fn = window.fetchWorkspaceClients;
    if (typeof fn !== 'function') return;
    try {
        const l = await fn();
        if (Array.isArray(l)) window._workspaceClientsCache = l;
    } catch (_) {
        /* 退化为空面板 · 不致命 */
    }
}

// 绑主体卡的下拉面板(方向判不出·主体没绑 → 选账套主体后重推)· 复用待补科目卡样式与开关/取消句柄。
function _erpExcBindPanel(it: RepairItem): string {
    const clients = _erpExcClients();
    if (!clients.length) {
        return `<div class="erp-exc-acctfix" data-acctfix-panel="${escapeHtml(it.id)}" hidden>
            <div class="erp-exc-acctfix-nochart">${escapeHtml(t('erp-bind-noclients'))}</div></div>`;
    }
    const opts = clients
        .map(
            (c) =>
                `<option value="${escapeHtml(String(c.id))}">${escapeHtml(c.name || String(c.id))}${c.tax_id ? ' · ' + escapeHtml(c.tax_id) : ''}</option>`
        )
        .join('');
    return `<div class="erp-exc-acctfix" data-acctfix-panel="${escapeHtml(it.id)}" hidden>
        <div class="erp-exc-acctfix-slots"><label class="erp-exc-acctfix-slot"><span>${escapeHtml(t('erp-bind-subject'))}</span>
        <select data-bindfix-select><option value="">${escapeHtml(t('erp-bind-pick'))}</option>${opts}</select></label></div>
        <div class="erp-exc-acctfix-act">
            <button class="btn btn-sm btn-primary" type="button" data-bindfix-submit="${escapeHtml(it.id)}">${escapeHtml(t('erp-bind-submit'))}</button>
            <button class="btn btn-sm btn-ghost" type="button" data-acctfix-cancel="${escapeHtml(it.id)}">${escapeHtml(t('erp-acctfix-cancel'))}</button>
        </div></div>`;
}

async function _erpExcBindSubject(
    logId: string,
    panel: HTMLElement,
    btn: HTMLButtonElement | null
) {
    const sel = panel.querySelector('[data-bindfix-select]') as HTMLSelectElement | null;
    const wcId = sel ? parseInt(sel.value, 10) : 0;
    if (!wcId) {
        showToast(t('erp-bind-need-pick'), 'error');
        return;
    }
    if (btn) {
        btn.disabled = true;
        btn.textContent = t('erp-exc-retrying');
    }
    try {
        const resp = await fetch(
            '/api/erp/logs/' + encodeURIComponent(logId) + '/express-bind-subject',
            {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + _erpExcTok(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ workspace_client_id: wcId }),
            }
        );
        const data = await resp.json().catch(() => ({}));
        showToast(
            resp.ok && data.ok ? t('erp-bind-ok') : t('erp-bind-fail'),
            resp.ok && data.ok ? 'success' : 'error'
        );
    } catch (e) {
        showToast(t('erp-bind-fail'), 'error');
    }
    _erpExcReload();
}

// 补期初卡:缺库存的商品逐行 → 会计填 数量/单位成本/日期 → 提交后先写期初再重推。
// 小助手至今没有客户实际进价,期初成本必须由会计据真实单据填(不静默填 0)。
function _erpExcStockOpeningPanel(it: RepairItem): string {
    const items = (it.stock_fix && it.stock_fix.items) || [];
    if (!items.length) {
        return `<div class="erp-exc-acctfix" data-acctfix-panel="${escapeHtml(it.id)}" hidden>
            <div class="erp-exc-acctfix-nochart">${escapeHtml(t('erp-stockopen-noitems'))}</div></div>`;
    }
    const rows = items
        .map(
            (p) =>
                `<div class="erp-exc-stockopen-row">` +
                `<span class="erp-exc-stockopen-name" title="${escapeHtml(p.name || p.stkcod || '')}">${escapeHtml(p.name || p.stkcod || '')}</span>` +
                `<input type="hidden" data-stockopen-key="${escapeHtml(p.stkcod || p.name || '')}">` +
                `<label>${escapeHtml(t('erp-stockopen-qty'))}<input type="number" min="0" step="any" data-stockopen-qty></label>` +
                `<label>${escapeHtml(t('erp-stockopen-cost'))}<input type="number" min="0" step="any" data-stockopen-cost></label>` +
                `<label>${escapeHtml(t('erp-stockopen-date'))}<input type="date" data-stockopen-date></label>` +
                `</div>`
        )
        .join('');
    return `<div class="erp-exc-acctfix erp-exc-stockopen" data-acctfix-panel="${escapeHtml(it.id)}" hidden>
        <div class="erp-exc-stockopen-hint">${escapeHtml(t('erp-stockopen-hint'))}</div>
        <div class="erp-exc-stockopen-rows">${rows}</div>
        <div class="erp-exc-acctfix-act">
            <button class="btn btn-sm btn-primary" type="button" data-stockopen-submit="${escapeHtml(it.id)}">${escapeHtml(t('erp-stockopen-submit'))}</button>
            <button class="btn btn-sm btn-ghost" type="button" data-acctfix-cancel="${escapeHtml(it.id)}">${escapeHtml(t('erp-acctfix-cancel'))}</button>
        </div></div>`;
}

async function _erpExcStockOpening(
    logId: string,
    panel: HTMLElement,
    btn: HTMLButtonElement | null
) {
    const items: Array<{ key: string; qty: number; unit_cost: number; date: string }> = [];
    let bad = false;
    panel.querySelectorAll('.erp-exc-stockopen-row').forEach((row) => {
        const key =
            (row.querySelector('[data-stockopen-key]') as HTMLInputElement | null)?.value.trim() ||
            '';
        const qty = parseFloat(
            (row.querySelector('[data-stockopen-qty]') as HTMLInputElement | null)?.value || ''
        );
        const cost = parseFloat(
            (row.querySelector('[data-stockopen-cost]') as HTMLInputElement | null)?.value || ''
        );
        const date =
            (row.querySelector('[data-stockopen-date]') as HTMLInputElement | null)?.value || '';
        // 成本可为 0 只在真无成本时(罕见)· 数量必须 >0 · 日期必填(期初日 ≤ 出库日)。
        if (!(qty > 0) || !(cost >= 0) || Number.isNaN(cost) || !date) {
            bad = true;
            return;
        }
        items.push({ key, qty, unit_cost: cost, date });
    });
    if (bad || !items.length) {
        showToast(t('erp-stockopen-need-all'), 'error');
        return;
    }
    if (btn) {
        btn.disabled = true;
        btn.textContent = t('erp-exc-retrying');
    }
    try {
        const resp = await fetch(
            '/api/erp/logs/' + encodeURIComponent(logId) + '/express-stock-opening',
            {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + _erpExcTok(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ items }),
            }
        );
        const data = await resp.json().catch(() => ({}));
        showToast(
            resp.ok && data.ok ? t('erp-stockopen-ok') : t('erp-stockopen-fail'),
            resp.ok && data.ok ? 'success' : 'error'
        );
    } catch (e) {
        showToast(t('erp-stockopen-fail'), 'error');
    }
    _erpExcReload();
}

export type { RepairItem };
export {
    _erpExcAcctPanel,
    _erpExcAccountFix,
    _erpExcBindPanel,
    _erpExcBindSubject,
    _erpExcStockOpeningPanel,
    _erpExcStockOpening,
    _erpExcEnsureClients,
};
