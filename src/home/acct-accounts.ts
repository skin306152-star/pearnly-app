// 自动做账 · 屏3 科目表(照搬设计稿 03-科目表 · 老板配置后台)。
// 信息带(N 个科目 + 加科目)→ 控件带(类型 seg + 搜)→ 按类型分组行(预置标签 · hover 编辑)。
// 预置不可删可停;加/改 = 站内 .modal(acct-modals)。
/* global t, escapeHtml */
import { acctErrMsg, injectAcctBase, injectStyle, type Account } from './acct-common.js';
import { fetchAccounts, openAcctAccountForm } from './acct-modals.js';

type TypeChip = 'all' | Account['acct_type'];

const PAGE_CSS = `
.acct.aa .band{display:flex;align-items:center;justify-content:space-between;padding:18px 22px;border-bottom:1px solid var(--line2);}
.acct.aa .band .num{font-size:26px;font-weight:740;letter-spacing:-.5px;}
.acct.aa .band .num small{font-size:14px;color:var(--ink2);font-weight:600;}
.acct.aa .band .lbl{color:var(--ink2);font-size:12.5px;margin-top:4px;}
.acct.aa .toolbar{display:flex;align-items:center;gap:12px;padding:11px 18px;border-bottom:1px solid var(--line2);background:var(--line2);flex-wrap:wrap;}
.acct.aa .seg{display:inline-flex;gap:2px;}
.acct.aa .seg .o{height:30px;padding:0 13px;border-radius:8px;display:flex;align-items:center;font-size:12.5px;color:var(--ink2);cursor:pointer;}
.acct.aa .seg .o.on{background:var(--accent-weak);color:var(--accent-deep);font-weight:600;}
.acct.aa .search{margin-left:auto;width:200px;height:34px;background:var(--card);border:1px solid var(--line);border-radius:9px;display:flex;align-items:center;gap:8px;padding:0 11px;}
.acct.aa .search input{border:0;outline:0;flex:1;background:transparent;font-size:13px;color:var(--ink);}
.acct.aa .grp{padding:9px 22px;font-size:11.5px;color:var(--ink3);font-weight:600;letter-spacing:.3px;background:var(--line2);border-bottom:1px solid var(--line2);}
.acct.aa .row{display:flex;align-items:center;gap:14px;padding:12px 22px;border-bottom:1px solid var(--line2);}
.acct.aa .row:hover{background:var(--line2);}
.acct.aa .row .code{width:60px;color:var(--ink3);font-size:12px;font-variant-numeric:tabular-nums;flex:0 0 60px;}
.acct.aa .row .nm{flex:1;font-size:13.5px;font-weight:550;min-width:0;}
.acct.aa .row .th{color:var(--ink3);font-size:12px;width:200px;}
.acct.aa .row .edit{color:var(--accent);font-size:12px;cursor:pointer;opacity:0;}
.acct.aa .row:hover .edit{opacity:1;}
.acct.aa .preset{font-size:10.5px;background:var(--line2);color:var(--ink2);padding:1px 7px;border-radius:5px;}
.acct.aa .offtag{font-size:10.5px;background:var(--line2);color:var(--ink3);padding:1px 7px;border-radius:5px;}
@media(max-width:600px){
  .acct.aa .row .th{display:none;}
  .acct.aa .search{width:100%;margin-left:0;}
  .acct.aa .row .edit{opacity:1;}
}
`;

const TYPE_KEYS: Record<Account['acct_type'], string> = {
    asset: 'acct-type-asset',
    liability: 'acct-type-liability',
    equity: 'acct-type-equity',
    revenue: 'acct-type-revenue',
    expense: 'acct-type-expense',
};

let accounts: Account[] = [];
let chip: TypeChip = 'all';
let keyword = '';
let searchTimer: number | undefined;

function view(): Account[] {
    const kw = keyword.trim().toLowerCase();
    return accounts.filter((a) => {
        if (chip !== 'all' && a.acct_type !== chip) return false;
        if (!kw) return true;
        return (a.code + ' ' + a.name_zh + ' ' + (a.name_th || '')).toLowerCase().includes(kw);
    });
}

function segHtml(): string {
    const defs: [TypeChip, string][] = [
        ['all', 'acct-chip-all'],
        ['asset', 'acct-type-asset'],
        ['liability', 'acct-type-liability'],
        ['equity', 'acct-type-equity'],
        ['revenue', 'acct-type-revenue'],
        ['expense', 'acct-type-expense'],
    ];
    return defs
        .map(
            ([k, key]) =>
                `<div class="o ${k === chip ? 'on' : ''}" data-chip="${k}">${escapeHtml(t(key))}</div>`
        )
        .join('');
}

function rowsHtml(list: Account[]): string {
    const order: Account['acct_type'][] = ['asset', 'liability', 'equity', 'revenue', 'expense'];
    let html = '';
    for (const type of order) {
        const group = list.filter((a) => a.acct_type === type);
        if (!group.length) continue;
        html += `<div class="grp">${escapeHtml(t(TYPE_KEYS[type]))}</div>`;
        html += group
            .map(
                (a) => `<div class="row" data-id="${escapeHtml(a.id)}">
                <span class="code">${escapeHtml(a.code)}</span>
                <span class="nm">${escapeHtml(a.name_zh)}</span>
                <span class="th">${escapeHtml(a.name_th || '—')}</span>
                ${a.is_preset ? `<span class="preset">${escapeHtml(t('acct-preset'))}</span>` : ''}
                ${!a.is_active ? `<span class="offtag">${escapeHtml(t('acct-active-off'))}</span>` : ''}
                <span class="edit">${escapeHtml(t('acct-edit'))}</span>
            </div>`
            )
            .join('');
    }
    return html;
}

function renderBody(): void {
    const body = document.getElementById('acct-acc-body');
    if (!body) return;
    const list = view();
    body.innerHTML = list.length
        ? rowsHtml(list)
        : `<div class="state">${escapeHtml(t('acct-acc-empty'))}</div>`;
    body.querySelectorAll<HTMLElement>('.row[data-id]').forEach((el) => {
        el.onclick = () => {
            const acct = accounts.find((a) => a.id === el.dataset.id);
            if (acct) openAcctAccountForm(acct, load);
        };
    });
    const num = document.getElementById('acct-acc-count');
    if (num) num.textContent = String(accounts.length);
}

function shellHtml(): string {
    return `<div class="acct aa"><div class="wrap">
        <div class="ph"><div><div class="t">${escapeHtml(t('acct-acc-title'))}</div><div class="sub">${escapeHtml(t('acct-acc-subtitle'))}</div></div></div>
        <div class="panel">
            <div class="band">
                <div><div class="num tnum"><span id="acct-acc-count">0</span> <small>${escapeHtml(t('acct-acc-unit'))}</small></div>
                <div class="lbl">${escapeHtml(t('acct-acc-band'))}</div></div>
                <button class="btn primary" id="acct-acc-add">+ ${escapeHtml(t('acct-add-account'))}</button>
            </div>
            <div class="toolbar">
                <div class="seg" id="acct-acc-seg">${segHtml()}</div>
                <div class="search"><input id="acct-acc-search" placeholder="${escapeHtml(t('acct-acc-search'))}"></div>
            </div>
            <div id="acct-acc-body"></div>
        </div>
    </div></div>`;
}

async function load(): Promise<void> {
    const body = document.getElementById('acct-acc-body');
    if (body) body.innerHTML = `<div class="state">${escapeHtml(t('acct-loading'))}</div>`;
    try {
        accounts = await fetchAccounts();
        renderBody();
    } catch (e) {
        if (body)
            body.innerHTML = `<div class="state">${escapeHtml(acctErrMsg(e, 'acct.unexpected'))}<br><button class="btn" id="acct-acc-retry" style="margin-top:12px;">${escapeHtml(t('acct-retry'))}</button></div>`;
        const retry = document.getElementById('acct-acc-retry');
        if (retry) retry.onclick = () => load();
    }
}

window.loadAcctAccounts = function () {
    const sec = document.getElementById('page-acct-accounts');
    if (!sec) return;
    injectAcctBase();
    injectStyle('acct-accounts-css', PAGE_CSS);
    sec.innerHTML = shellHtml();
    document.querySelectorAll<HTMLElement>('#acct-acc-seg .o').forEach((el) => {
        el.onclick = () => {
            chip = el.dataset.chip as TypeChip;
            document
                .querySelectorAll<HTMLElement>('#acct-acc-seg .o')
                .forEach((o) => o.classList.toggle('on', o.dataset.chip === chip));
            renderBody();
        };
    });
    const search = document.getElementById('acct-acc-search') as HTMLInputElement | null;
    if (search)
        search.oninput = () => {
            keyword = search.value;
            clearTimeout(searchTimer);
            searchTimer = window.setTimeout(renderBody, 200);
        };
    const add = document.getElementById('acct-acc-add');
    if (add) add.onclick = () => openAcctAccountForm(null, load);
    load();
};

if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('acct-accounts', () => {
        if (document.getElementById('acct-acc-body')) window.loadAcctAccounts?.();
    });
}
