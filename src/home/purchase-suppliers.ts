// 商户采购 · 屏4 供应商管理(配置后台 · 平铺页)· 照搬设计稿 04-供应商管理。
// AI 拍票自动建档为主、手动加为辅 · 套账隔离 · owner/会计可改。加供应商 = 页内弹窗。四态。
/* global t, escapeHtml, showToast */
import {
    papi,
    purchaseErrMsg,
    fmtBaht,
    fmtMonthDay,
    injectPurBase,
    injectStyle,
    type Supplier,
} from './purchase-common.js';

const PAGE_CSS = `
.pur.s .wrap{max-width:760px;}
.pur.s .card{border-radius:14px;box-shadow:0 1px 2px rgba(17,24,39,.04),0 6px 20px rgba(17,24,39,.07);}
.pur .hd{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;}
.pur h1{font-size:20px;}
.pur .sub{color:var(--ink2);font-size:13px;margin-bottom:18px;}
.pur .add{height:38px;padding:0 14px;border:0;border-radius:9px;background:var(--blue);color:#fff;font-weight:700;font-size:13.5px;cursor:pointer;display:inline-flex;align-items:center;gap:6px;}
.pur .add:hover{background:var(--blue-d);}
.pur .aibar{display:flex;gap:9px;align-items:center;background:var(--blue-l);border:1px solid #c7d8fb;border-radius:10px;padding:10px 13px;margin-bottom:14px;font-size:12.5px;color:#1d4ed8;}
.pur .aibar svg{flex:0 0 16px;}
.pur .sup-card{overflow:hidden;}
.pur .srch{padding:11px 14px;border-bottom:1px solid #f0f0ec;display:flex;align-items:center;gap:8px;}
.pur .srch input{border:0;outline:0;flex:1;font-size:13.5px;background:transparent;}
.pur .srow{display:flex;align-items:center;gap:13px;padding:13px 15px;border-bottom:1px solid #f4f4f0;}
.pur .srow:last-child{border-bottom:0;}
.pur .av{width:40px;height:40px;border-radius:10px;background:#f0f0ec;color:var(--ink2);display:flex;align-items:center;justify-content:center;font-weight:700;flex:0 0 40px;}
.pur .sinfo{flex:1;min-width:0;} .pur .sinfo .n{font-size:14.5px;font-weight:600;} .pur .sinfo .m{font-size:12px;color:var(--ink2);margin-top:3px;}
.pur .stat{text-align:right;} .pur .stat .v{font-weight:700;} .pur .stat .l{font-size:11px;color:var(--ink3);}
.pur .op{height:32px;padding:0 11px;border:1px solid var(--line);border-radius:8px;background:#fff;color:var(--ink2);font-size:12.5px;cursor:pointer;}
.pur .op:hover{border-color:#c7d2fe;color:var(--blue);}
.pur .snote{margin-top:14px;font-size:12.5px;color:var(--ink2);background:#fff;border:1px solid var(--line);border-radius:12px;padding:13px 15px;line-height:1.6;}
.pur .snote b{color:var(--ink);}
.pur .smask{position:fixed;inset:0;background:rgba(17,24,39,.45);display:none;align-items:center;justify-content:center;z-index:1200;padding:18px;}
.pur .smask.show{display:flex;}
.pur .smodal{width:380px;max-width:92vw;background:#fff;border-radius:18px;overflow:hidden;box-shadow:0 24px 60px rgba(0,0,0,.25);}
.pur .smh{padding:16px 20px;border-bottom:1px solid #f0f0ec;font-weight:700;font-size:16px;}
.pur .smb{padding:18px 20px;} .pur .smb label{display:block;font-size:12.5px;color:var(--ink2);margin-bottom:7px;}
.pur .fld{height:44px;border:1px solid var(--line);border-radius:10px;padding:0 13px;display:flex;align-items:center;background:#fbfbf9;margin-bottom:14px;}
.pur .fld input{border:0;outline:0;background:transparent;flex:1;font-size:14.5px;}
.pur .smf{padding:0 20px 20px;display:flex;gap:10px;}
.pur .smf .g{height:46px;padding:0 16px;border:1px solid var(--line);border-radius:10px;background:#fff;color:var(--ink2);cursor:pointer;}
.pur .smf .ok{flex:1;height:46px;border:0;border-radius:10px;background:var(--blue);color:#fff;font-weight:700;font-size:15px;cursor:pointer;}
@media(max-width:600px){ .pur .stat{display:none;} }
`;

const ICON_STAR =
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l2.4 7.4H22l-6 4.6 2.3 7.4-6.3-4.6L5.7 21l2.3-7.4-6-4.6h7.6z"/></svg>';
const ICON_SEARCH =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>';
const ICON_PLUS =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>';

let all: Supplier[] = [];
let keyword = '';

function rowHtml(s: Supplier): string {
    const meta = s.tax_id ? `${t('pur-tax-id')} ${s.tax_id}` : t('pur-no-tax-receipt');
    const last = s.last_purchase_date
        ? ` · ${t('pur-last-buy')} ${fmtMonthDay(s.last_purchase_date)}`
        : '';
    return `<div class="srow">
        <div class="av">${escapeHtml((s.name || '?').slice(0, 1))}</div>
        <div class="sinfo"><div class="n">${escapeHtml(s.name)}</div><div class="m tnum">${escapeHtml(meta)}${escapeHtml(last)}</div></div>
        <div class="stat"><div class="v tnum">${fmtBaht(s.total_purchased)}</div><div class="l">${escapeHtml(t('pur-cum-buy'))}</div></div>
        <button class="op" data-edit="${escapeHtml(s.id)}">${escapeHtml(t('pur-edit'))}</button>
    </div>`;
}

function listHtml(): string {
    const kw = keyword.trim().toLowerCase();
    const list = all.filter(
        (s) => !kw || (s.name + ' ' + (s.tax_id || '')).toLowerCase().includes(kw)
    );
    if (!list.length) return `<div class="state">${escapeHtml(t('pur-supplier-empty'))}</div>`;
    return list.map(rowHtml).join('');
}

function shell(): string {
    return `<div class="pur s"><div class="wrap">
        <div class="hd"><h1>${escapeHtml(t('pur-suppliers'))}</h1><button class="add" id="pur-sup-add">${ICON_PLUS}${escapeHtml(t('pur-supplier-add'))}</button></div>
        <div class="sub">${escapeHtml(t('pur-suppliers-sub'))}</div>
        <div class="aibar">${ICON_STAR}${escapeHtml(t('pur-suppliers-ai'))}</div>
        <div class="card sup-card">
            <div class="srch">${ICON_SEARCH}<input id="pur-sup-search" placeholder="${escapeHtml(t('pur-supplier-search'))}" value="${escapeHtml(keyword)}"></div>
            <div id="pur-sup-list">${listHtml()}</div>
        </div>
        <div class="snote">${escapeHtml(t('pur-suppliers-note'))}</div>
        <div class="smask" id="pur-sup-mask"><div class="smodal">
            <div class="smh" id="pur-sup-mtitle">${escapeHtml(t('pur-supplier-add'))}</div>
            <div class="smb">
                <label>${escapeHtml(t('pur-supplier-name'))}</label><div class="fld"><input id="pur-sf-name" placeholder="บริษัท ... จำกัด"></div>
                <label>${escapeHtml(t('pur-supplier-tax-opt'))}</label><div class="fld"><input id="pur-sf-tax" class="tnum" placeholder="13"></div>
                <label>${escapeHtml(t('pur-supplier-phone'))}</label><div class="fld"><input id="pur-sf-phone"></div>
            </div>
            <div class="smf"><button class="g" id="pur-sf-cancel">${escapeHtml(t('pur-cancel'))}</button><button class="ok" id="pur-sf-save">${escapeHtml(t('pur-save'))}</button></div>
        </div></div>
    </div></div>`;
}

function refreshList(): void {
    const el = document.getElementById('pur-sup-list');
    if (el) el.innerHTML = listHtml();
    bindRows();
}

function bindRows(): void {
    document.querySelectorAll<HTMLElement>('#pur-sup-list [data-edit]').forEach((el) => {
        el.onclick = () => openModal(all.find((s) => s.id === el.dataset.edit) || null);
    });
}

let editing: Supplier | null = null;

function openModal(s: Supplier | null): void {
    editing = s;
    const mask = document.getElementById('pur-sup-mask');
    if (!mask) return;
    (document.getElementById('pur-sup-mtitle') as HTMLElement).textContent = t(
        s ? 'pur-supplier-edit' : 'pur-supplier-add'
    );
    (document.getElementById('pur-sf-name') as HTMLInputElement).value = s ? s.name : '';
    (document.getElementById('pur-sf-tax') as HTMLInputElement).value = (s && s.tax_id) || '';
    (document.getElementById('pur-sf-phone') as HTMLInputElement).value = (s && s.phone) || '';
    mask.classList.add('show');
}

function bind(): void {
    const search = document.getElementById('pur-sup-search') as HTMLInputElement;
    search.oninput = () => {
        keyword = search.value;
        refreshList();
    };
    document.getElementById('pur-sup-add')!.onclick = () => openModal(null);
    const mask = document.getElementById('pur-sup-mask')!;
    document.getElementById('pur-sf-cancel')!.onclick = () => mask.classList.remove('show');
    mask.onclick = (e) => {
        if (e.target === mask) mask.classList.remove('show');
    };
    document.getElementById('pur-sf-save')!.onclick = save;
    bindRows();
}

async function save(): Promise<void> {
    const name = (document.getElementById('pur-sf-name') as HTMLInputElement).value.trim();
    if (!name) {
        showToast(t('pur-supplier-name-req'), 'error');
        return;
    }
    const body = {
        name,
        tax_id: (document.getElementById('pur-sf-tax') as HTMLInputElement).value.trim() || null,
        phone: (document.getElementById('pur-sf-phone') as HTMLInputElement).value.trim() || null,
    };
    try {
        if (editing) await papi('PATCH', `/api/purchase/suppliers/${editing.id}`, body);
        else await papi('POST', '/api/purchase/suppliers', body);
        document.getElementById('pur-sup-mask')!.classList.remove('show');
        showToast(t('pur-saved'), 'success');
        load();
    } catch (e) {
        showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
    }
}

async function load(): Promise<void> {
    const sec = document.getElementById('page-purchase-suppliers');
    if (!sec) return;
    try {
        const d = (await papi('GET', '/api/purchase/suppliers')) as { suppliers?: Supplier[] };
        all = d.suppliers || [];
    } catch (_) {
        all = [];
    }
    sec.innerHTML = shell();
    bind();
}

window.loadPurchaseSuppliers = function () {
    injectPurBase();
    injectStyle('pur-suppliers-css', PAGE_CSS);
    load();
};
