// 自动报税 · 屏4 报税设置(照搬 Pearnly_报税_UI预览/04 · 配置后台)。
// 主体/税务登记(已登记VAT/总分公司)→ 提交方式(e-Tax 未接通的诚实文案,无假直报开关)
// → 提醒(截止前天数 / 0 税额也报)→ 保存。GET/PUT /api/tax/settings。
// 控件全用站内样式化 .sw/.seg(选中态 var(--accent)),不用原生 checkbox/select(THEME #2/#3)。
/* global t, escapeHtml, showToast */
import { aapi, acctErrMsg, injectStyle, withWs } from './acct-common.js';
import { injectTaxBase } from './tax-common.js';

const PAGE_CSS = `
.taxp.set .grp{padding:11px 22px;font-size:11.5px;color:var(--ink3);font-weight:600;letter-spacing:.3px;background:var(--bg);border-bottom:1px solid var(--line2);}
.taxp.set .item{display:flex;align-items:center;gap:14px;padding:15px 22px;border-bottom:1px solid var(--line2);}
.taxp.set .item .l{min-width:0;}
.taxp.set .item .t2{font-size:13.5px;font-weight:600;}
.taxp.set .item .d{color:var(--ink2);font-size:12px;margin-top:3px;}
.taxp.set .item .ctl{margin-left:auto;display:flex;align-items:center;gap:10px;flex-shrink:0;}
.taxp.set .sw{width:42px;height:24px;border-radius:999px;background:var(--line);position:relative;cursor:pointer;flex:0 0 42px;}
.taxp.set .sw.on{background:var(--accent);}
.taxp.set .sw i{position:absolute;top:3px;left:3px;width:18px;height:18px;border-radius:50%;background:var(--card);transition:.15s;}
.taxp.set .sw.on i{left:21px;}
.taxp.set .seg{display:inline-flex;gap:2px;border:1px solid var(--line);border-radius:9px;padding:3px;}
.taxp.set .seg .o{height:30px;padding:0 13px;border-radius:7px;display:flex;align-items:center;font-size:12.5px;color:var(--ink2);cursor:pointer;}
.taxp.set .seg .o.on{background:var(--accent-weak);color:var(--accent-deep);font-weight:600;}
.taxp.set .pill{font-size:11.5px;background:var(--line2);color:var(--ink2);padding:4px 11px;border-radius:8px;}
.taxp.set .pill.warn{background:var(--amber-weak);color:var(--amber);}
.taxp.set .inp{height:36px;border:1px solid var(--line);border-radius:9px;display:flex;align-items:center;padding:0 12px;font-size:13px;background:var(--card);gap:6px;}
.taxp.set .inp input{border:0;outline:0;background:transparent;width:42px;font:inherit;color:var(--ink);text-align:right;}
.taxp.set .lk{color:var(--accent);cursor:pointer;}
.taxp.set .foot{display:flex;justify-content:flex-end;padding:14px 22px;}
@media(max-width:600px){.taxp.set .item{flex-wrap:wrap;}.taxp.set .item .ctl{margin-left:0;width:100%;justify-content:flex-end;}}
`;

interface TaxSettings {
    vat_registered: boolean;
    branch_type: string;
    branch_no: string | null;
    efiling_connected: boolean;
    remind_days_before: number;
    file_zero: boolean;
}

let settings: TaxSettings | null = null;
let dirty: Partial<TaxSettings> = {};

function sw(id: string, on: boolean): string {
    return `<div class="sw ${on ? 'on' : ''}" id="${id}"><i></i></div>`;
}

function cur<K extends keyof TaxSettings>(k: K): TaxSettings[K] {
    return (k in dirty ? dirty[k] : settings![k]) as TaxSettings[K];
}

function shellHtml(): string {
    const isBranch = cur('branch_type') === 'branch';
    return `<div class="taxp set"><div class="wrap">
        <div class="ph"><div><div class="t">${escapeHtml(t('tax-set-title'))}</div><div class="sub">${escapeHtml(t('tax-set-subtitle'))}</div></div></div>
        <div class="panel">
            <div class="grp">${escapeHtml(t('tax-set-grp-entity'))}</div>
            <div class="item"><div class="l"><div class="t2">${escapeHtml(t('tax-set-taxid'))}</div><div class="d">${escapeHtml(t('tax-set-taxid-d'))} · <span class="lk" id="tax-set-goseller">${escapeHtml(t('tax-set-taxid-edit'))}</span></div></div></div>
            <div class="item"><div class="l"><div class="t2">${escapeHtml(t('tax-set-vat'))}</div><div class="d">${escapeHtml(t('tax-set-vat-d'))}</div></div><div class="ctl">${sw('tax-sw-vat', !!cur('vat_registered'))}</div></div>
            <div class="item"><div class="l"><div class="t2">${escapeHtml(t('tax-set-branch'))}</div><div class="d">${escapeHtml(t('tax-set-branch-d'))}</div></div>
                <div class="ctl"><div class="seg" id="tax-seg-branch">
                    <div class="o ${!isBranch ? 'on' : ''}" data-v="main">${escapeHtml(t('tax-set-branch-main'))}</div>
                    <div class="o ${isBranch ? 'on' : ''}" data-v="branch">${escapeHtml(t('tax-set-branch-sub'))}</div>
                </div>
                <div class="inp" id="tax-branch-no-wrap" style="${isBranch ? '' : 'display:none;'}"><input id="tax-branch-no" maxlength="5" placeholder="00000" value="${escapeHtml(cur('branch_no') || '')}" style="width:60px;"></div></div></div>

            <div class="grp">${escapeHtml(t('tax-set-grp-submit'))}</div>
            <div class="item"><div class="l"><div class="t2">${escapeHtml(t('tax-set-etax'))}</div><div class="d">${escapeHtml(t('tax-set-etax-d'))}</div></div><div class="ctl"><span class="pill warn">${escapeHtml(t('tax-set-etax-soon'))}</span></div></div>
            <div class="item"><div class="l"><div class="t2">${escapeHtml(t('tax-set-export'))}</div><div class="d">${escapeHtml(t('tax-set-export-d'))}</div></div><div class="ctl"><span class="pill">${escapeHtml(t('tax-set-export-pill'))}</span></div></div>

            <div class="grp">${escapeHtml(t('tax-set-grp-remind'))}</div>
            <div class="item"><div class="l"><div class="t2">${escapeHtml(t('tax-set-remind'))}</div><div class="d">${escapeHtml(t('tax-set-remind-d'))}</div></div>
                <div class="ctl"><div class="inp">${escapeHtml(t('tax-set-remind-pre'))} <input id="tax-remind-days" type="number" min="0" max="30" value="${Number(cur('remind_days_before')) || 0}"> ${escapeHtml(t('tax-set-remind-post'))}</div></div></div>
            <div class="item"><div class="l"><div class="t2">${escapeHtml(t('tax-set-filezero'))}</div><div class="d">${escapeHtml(t('tax-set-filezero-d'))}</div></div><div class="ctl">${sw('tax-sw-filezero', !!cur('file_zero'))}</div></div>

            <div class="foot"><button class="btn primary" id="tax-set-save" style="height:40px;padding:0 22px;">${escapeHtml(t('tax-save'))}</button></div>
        </div>
    </div></div>`;
}

function bind(sec: HTMLElement): void {
    const goSeller = sec.querySelector<HTMLElement>('#tax-set-goseller');
    if (goSeller) goSeller.onclick = () => window.routeTo?.('sales-account');
    const bindSwitch = (id: string, key: 'vat_registered' | 'file_zero') => {
        const el = sec.querySelector<HTMLElement>('#' + id);
        if (el)
            el.onclick = () => {
                const on = !el.classList.contains('on');
                el.classList.toggle('on', on);
                dirty[key] = on;
            };
    };
    bindSwitch('tax-sw-vat', 'vat_registered');
    bindSwitch('tax-sw-filezero', 'file_zero');
    sec.querySelectorAll<HTMLElement>('#tax-seg-branch .o').forEach((el) => {
        el.onclick = () => {
            sec.querySelectorAll<HTMLElement>('#tax-seg-branch .o').forEach((o) =>
                o.classList.toggle('on', o === el)
            );
            dirty.branch_type = el.dataset.v;
            const wrap = sec.querySelector<HTMLElement>('#tax-branch-no-wrap');
            if (wrap) wrap.style.display = el.dataset.v === 'branch' ? '' : 'none';
        };
    });
    const branchNo = sec.querySelector<HTMLInputElement>('#tax-branch-no');
    if (branchNo) branchNo.onchange = () => (dirty.branch_no = branchNo.value.trim() || null);
    const days = sec.querySelector<HTMLInputElement>('#tax-remind-days');
    if (days) days.onchange = () => (dirty.remind_days_before = Number(days.value) || 0);
    const save = sec.querySelector<HTMLButtonElement>('#tax-set-save');
    if (save)
        save.onclick = async () => {
            try {
                await withLoading(save, () => aapi('PUT', withWs('/api/tax/settings'), dirty));
                showToast(t('tax-set-saved'), 'success');
                dirty = {};
                load();
            } catch (e) {
                showToast(acctErrMsg(e, 'tax.unexpected'), 'error');
            }
        };
}

async function load(): Promise<void> {
    const sec = document.getElementById('page-tax-settings');
    if (!sec) return;
    sec.innerHTML = `<div class="taxp set"><div class="wrap"><div class="panel"><div class="state">${escapeHtml(t('tax-loading'))}</div></div></div></div>`;
    try {
        const data = (await aapi('GET', withWs('/api/tax/settings'))) as {
            settings?: TaxSettings;
        };
        settings = data.settings || null;
        if (!settings) throw new Error('no settings');
        dirty = {};
        sec.innerHTML = shellHtml();
        bind(sec);
    } catch (e) {
        sec.innerHTML = `<div class="taxp set"><div class="wrap"><div class="panel"><div class="state">${escapeHtml(acctErrMsg(e, 'tax.unexpected'))}<br><button class="btn" id="tax-set-retry" style="margin-top:12px;">${escapeHtml(t('tax-retry'))}</button></div></div></div></div>`;
        const retry = document.getElementById('tax-set-retry');
        if (retry) retry.onclick = () => load();
    }
}

window.loadTaxSettings = function () {
    const sec = document.getElementById('page-tax-settings');
    if (!sec) return;
    injectTaxBase();
    injectStyle('tax-settings-css', PAGE_CSS);
    load();
};

if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('tax-settings', () => {
        if (document.getElementById('page-tax-settings')?.querySelector('.taxp.set'))
            window.loadTaxSettings?.();
    });
}
