// 商户采购 · 屏1 采购/进项主屏(列表 + KPI · 桌面表格 / 手机卡片)· 照搬设计稿 01-采购进项主屏。
// KPI 4 张(本月进货/费用/可抵进项税/未付)· chip 筛(全部/进货/费用/未付)+ 搜 · 行点按 status 分流
// (draft→屏10 录入 / posted→屏6 详情)· 拍进项票(intake→录入)/ LINE 记费用(屏3 弹窗)· 四态。
/* global t, escapeHtml, showToast */
import {
    papi,
    activeWsId,
    purchaseErrMsg,
    fmtBaht,
    fmtMonthDay,
    srcLabelKey,
    kindLabelKey,
    normSummary,
    normListItem,
    injectPurBase,
    injectStyle,
    type DocListItem,
    type DocSummary,
} from './purchase-common.js';

const ICON_CAM =
    '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>';
const ICON_SEARCH =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>';
const ICON_CAM_SM =
    '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/></svg>';

type Chip = 'all' | 'purchase' | 'expense' | 'unpaid';

const PAGE_CSS = `
.pur .ph{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;}
.pur .ph .t{font-size:20px;font-weight:700;}
.pur .ph .sub{color:var(--ink2);font-size:13px;margin-top:3px;}
.pur .acts{display:flex;gap:9px;}
.pur .kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:14px;}
.pur .kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;box-shadow:var(--shadow);}
.pur .kpi .l{color:var(--ink2);font-size:12px;}
.pur .kpi .v{font-size:21px;font-weight:800;margin-top:5px;}
.pur .kpi .v.tax{color:var(--green);} .pur .kpi .v.unpaid{color:var(--amber);}
.pur .kpi .d{font-size:11px;color:var(--ink3);margin-top:3px;}
.pur .bar{display:flex;gap:8px;margin-bottom:12px;align-items:center;}
.pur .chip{height:32px;padding:0 14px;border-radius:999px;border:1px solid var(--line);background:#fff;color:var(--ink2);font-size:12.5px;cursor:pointer;display:inline-flex;align-items:center;}
.pur .chip.on{background:var(--ink);color:#fff;border-color:var(--ink);}
.pur .search{margin-left:auto;width:240px;height:34px;background:var(--card);border:1px solid var(--line);border-radius:9px;display:flex;align-items:center;gap:8px;padding:0 11px;}
.pur .search input{border:0;outline:0;flex:1;background:transparent;font-size:13px;}
.pur table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;box-shadow:var(--shadow);}
.pur th{text-align:left;font-size:11.5px;color:var(--ink2);font-weight:600;text-transform:uppercase;letter-spacing:.4px;padding:11px 14px;border-bottom:1px solid var(--line);background:#fafaf8;}
.pur td{padding:12px 14px;border-bottom:1px solid #f4f4f0;font-size:13.5px;}
.pur tr:last-child td{border-bottom:0;}
.pur tbody tr{cursor:pointer;}
.pur tbody tr:hover td{background:#fafaf8;}
.pur .src{display:inline-flex;align-items:center;gap:5px;font-size:11px;padding:2px 8px;border-radius:6px;background:#eef2ff;color:#4338ca;}
.pur .src.line{background:#dcfce7;color:#15803d;}
.pur .st{font-size:11px;padding:2px 9px;border-radius:6px;}
.pur .st.paid{background:#dcfce7;color:#15803d;} .pur .st.unpaid{background:#fef3c7;color:#b45309;} .pur .st.partial{background:#ffedd5;color:#c2410c;}
.pur .ty{font-size:11px;color:var(--ink2);}
.pur .cards{display:none;}
.pur .cards .card{padding:13px 14px;cursor:pointer;}
.pur .cards .r1{display:flex;justify-content:space-between;align-items:baseline;gap:10px;}
.pur .cards .nm{font-weight:600;font-size:14px;}
.pur .cards .amt{font-weight:800;font-size:16px;font-variant-numeric:tabular-nums;white-space:nowrap;}
.pur .cards .r2{display:flex;align-items:center;gap:7px;margin-top:9px;flex-wrap:wrap;}
.pur .cards .dt{color:var(--ink3);font-size:11px;margin-left:auto;}
.pur .cards .vat{font-size:11.5px;color:var(--ink2);}
@media(max-width:600px){
  .pur .ph{flex-direction:column;align-items:flex-start;gap:11px;}
  .pur .acts{width:100%;} .pur .acts .btn{flex:1;}
  .pur .kpis{grid-template-columns:repeat(2,1fr);}
  .pur .search{margin-left:0;width:100%;}
  .pur .bar{flex-wrap:wrap;}
  .pur table{display:none;}
  .pur .cards{display:flex;flex-direction:column;gap:10px;}
}
`;

let allDocs: DocListItem[] = [];
let summary: DocSummary | null = null;
let chip: Chip = 'all';
let keyword = '';
let searchTimer: number | undefined;

function matchChip(d: DocListItem): boolean {
    if (chip === 'purchase') return d.doc_kind !== 'expense';
    if (chip === 'expense') return d.doc_kind === 'expense';
    if (chip === 'unpaid') return d.payment_status !== 'paid';
    return true;
}

function matchKw(d: DocListItem): boolean {
    const kw = keyword.trim().toLowerCase();
    if (!kw) return true;
    return ((d.supplier_name || '') + ' ' + (d.title || '')).toLowerCase().includes(kw);
}

function view(): DocListItem[] {
    return allDocs.filter((d) => matchChip(d) && matchKw(d));
}

function payBadge(d: DocListItem): string {
    return `<span class="st ${d.payment_status}">${escapeHtml(t('pur-pay-' + d.payment_status))}</span>`;
}

function srcChip(d: DocListItem): string {
    const cls = d.source === 'line' ? 'src line' : 'src';
    const ico = d.source === 'photo' ? ICON_CAM_SM : '';
    return `<span class="${cls}">${ico}${escapeHtml(t(srcLabelKey(d.source)))}</span>`;
}

// 类型列:有细分科目名用之,否则回退票种(进货/费用/采购单)· 后端列表暂只返 doc_kind。
function typeLabel(d: DocListItem): string {
    return d.category_label || t(kindLabelKey(d.doc_kind));
}

function rowsHtml(list: DocListItem[]): string {
    return list
        .map((d) => {
            const sup = escapeHtml(d.supplier_name || '—');
            const title = d.title ? ' · ' + escapeHtml(d.title) : '';
            const vat = d.vat_amount > 0 ? fmtBaht(d.vat_amount) : '—';
            return `<tr data-id="${escapeHtml(d.id)}" data-status="${d.status}">
                <td class="tnum">${escapeHtml(fmtMonthDay(d.doc_date))}</td>
                <td>${sup}${title}</td>
                <td class="ty">${escapeHtml(typeLabel(d))}</td>
                <td>${srcChip(d)}</td>
                <td class="num">${fmtBaht(d.grand_total)}</td>
                <td class="num">${vat}</td>
                <td>${payBadge(d)}</td></tr>`;
        })
        .join('');
}

function cardsHtml(list: DocListItem[]): string {
    return list
        .map((d) => {
            const sup = escapeHtml(d.supplier_name || '—');
            const title = d.title ? ' · ' + escapeHtml(d.title) : '';
            const vat =
                d.vat_amount > 0
                    ? `<span class="vat">${escapeHtml(t('pur-vat-in'))} ${fmtBaht(d.vat_amount)}</span>`
                    : '';
            return `<div class="card" data-id="${escapeHtml(d.id)}" data-status="${d.status}">
                <div class="r1"><div class="nm">${sup}${title}</div><div class="amt">${fmtBaht(d.grand_total)}</div></div>
                <div class="r2"><span class="ty">${escapeHtml(typeLabel(d))}</span>${srcChip(d)}${payBadge(d)}${vat}<span class="dt tnum">${escapeHtml(fmtMonthDay(d.doc_date))}</span></div>
            </div>`;
        })
        .join('');
}

// 计数副标(本月笔数/欠款供应商数):后端 summary 暂不返计数 → >0 才显,缺则留空不显假「0 笔」。
function countSub(n: number, unitKey: string): string {
    return n > 0 ? n + ' ' + escapeHtml(t(unitKey)) : '';
}

function kpisHtml(s: DocSummary): string {
    return `<div class="kpis">
        <div class="kpi"><div class="l">${escapeHtml(t('pur-kpi-purchase'))}</div><div class="v tnum">${fmtBaht(s.purchase_total)}</div><div class="d">${countSub(s.purchase_count, 'pur-unit-rows')}</div></div>
        <div class="kpi"><div class="l">${escapeHtml(t('pur-kpi-expense'))}</div><div class="v tnum">${fmtBaht(s.expense_total)}</div><div class="d">${countSub(s.expense_count, 'pur-unit-rows')}</div></div>
        <div class="kpi"><div class="l">${escapeHtml(t('pur-kpi-vat'))}</div><div class="v tax tnum">${fmtBaht(s.vat_creditable)}</div><div class="d">${escapeHtml(t('pur-kpi-vat-d'))}</div></div>
        <div class="kpi"><div class="l">${escapeHtml(t('pur-kpi-unpaid'))}</div><div class="v unpaid tnum">${fmtBaht(s.unpaid_total)}</div><div class="d">${countSub(s.unpaid_suppliers, 'pur-unit-suppliers')}</div></div>
    </div>`;
}

function chipsHtml(): string {
    const defs: [Chip, string][] = [
        ['all', 'pur-chip-all'],
        ['purchase', 'pur-chip-purchase'],
        ['expense', 'pur-chip-expense'],
        ['unpaid', 'pur-chip-unpaid'],
    ];
    return defs
        .map(
            ([k, key]) =>
                `<div class="chip ${k === chip ? 'on' : ''}" data-chip="${k}">${escapeHtml(t(key))}</div>`
        )
        .join('');
}

function tableHtml(): string {
    const list = view();
    if (!list.length) {
        return `<div class="state" id="pur-empty">${escapeHtml(t('pur-empty'))}</div>`;
    }
    return `<table>
        <thead><tr>
            <th>${escapeHtml(t('pur-col-date'))}</th><th>${escapeHtml(t('pur-col-supplier'))}</th>
            <th>${escapeHtml(t('pur-col-type'))}</th><th>${escapeHtml(t('pur-col-source'))}</th>
            <th class="num">${escapeHtml(t('pur-col-total'))}</th><th class="num">${escapeHtml(t('pur-col-vat'))}</th>
            <th>${escapeHtml(t('pur-col-pay'))}</th>
        </tr></thead>
        <tbody>${rowsHtml(list)}</tbody>
    </table>
    <div class="cards">${cardsHtml(list)}</div>`;
}

function shell(): string {
    return `<div class="pur"><div class="wrap">
        <div class="ph">
            <div><div class="t">${escapeHtml(t('pur-title'))}</div><div class="sub">${escapeHtml(t('pur-subtitle'))}</div></div>
            <div class="acts">
                <button class="btn" id="pur-line-btn">${escapeHtml(t('pur-line-expense'))}</button>
                <button class="btn primary" id="pur-cam-btn">${ICON_CAM}${escapeHtml(t('pur-photo'))}</button>
            </div>
        </div>
        <div id="pur-kpis"></div>
        <div class="bar">${chipsHtml()}
            <div class="search">${ICON_SEARCH}<input id="pur-search" placeholder="${escapeHtml(t('pur-search-ph'))}" value="${escapeHtml(keyword)}"></div>
        </div>
        <div id="pur-body"></div>
        <input type="file" id="pur-cam-input" accept="image/*,application/pdf" style="display:none">
    </div></div>`;
}

function renderBody(): void {
    const kpis = document.getElementById('pur-kpis');
    if (kpis && summary) kpis.innerHTML = kpisHtml(summary);
    const body = document.getElementById('pur-body');
    if (body) body.innerHTML = tableHtml();
    bindRows();
}

function bindRows(): void {
    document.querySelectorAll<HTMLElement>('#pur-body [data-id]').forEach((el) => {
        el.onclick = () => {
            const id = el.dataset.id!;
            if (el.dataset.status === 'draft') window.openPurchaseForm?.(id);
            else window.openPurchaseDetail?.(id);
        };
    });
}

function bindChrome(): void {
    document.querySelectorAll<HTMLElement>('[data-chip]').forEach((el) => {
        el.onclick = () => {
            chip = el.dataset.chip as Chip;
            document.querySelectorAll('[data-chip]').forEach((c) => c.classList.remove('on'));
            el.classList.add('on');
            renderBody();
        };
    });
    const search = document.getElementById('pur-search') as HTMLInputElement | null;
    if (search) {
        search.oninput = () => {
            keyword = search.value;
            clearTimeout(searchTimer);
            searchTimer = window.setTimeout(renderBody, 200);
        };
    }
    const lineBtn = document.getElementById('pur-line-btn');
    if (lineBtn) lineBtn.onclick = () => window.openPurchaseLine?.();
    const camBtn = document.getElementById('pur-cam-btn');
    const camInput = document.getElementById('pur-cam-input') as HTMLInputElement | null;
    if (camBtn && camInput) camBtn.onclick = () => camInput.click();
    if (camInput) camInput.onchange = () => onCapture(camInput);
}

// 拍进项票 → intake 分流 → 落屏10 录入(预填识别 draft)。图走 multipart 真上传给 OCR。
// 后端返分流信封 {route,draft,dedupe_hit}:有 draft → 预填录入;低置信/看不清(inbox·draft=null)
// → 不静默丢,提示手填并开空表单(四态诚实)。
async function onCapture(input: HTMLInputElement): Promise<void> {
    const f = input.files && input.files[0];
    input.value = '';
    if (!f) return;
    const ws = activeWsId();
    const fd = new FormData();
    fd.append('image', f);
    if (ws != null) fd.append('workspace_client_id', String(ws));
    try {
        const res = (await papi('POST', '/api/purchase/intake', fd)) as {
            draft?: Record<string, unknown> | null;
            dedupe_hit?: boolean;
        };
        const d = res && res.draft;
        if (d) {
            window.openPurchaseForm?.(null, { ...d, dedupe_hit: res.dedupe_hit });
        } else {
            showToast(t('pur-intake-manual'), 'error');
            window.openPurchaseForm?.(null, {});
        }
    } catch (e) {
        showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
    }
}

function showState(html: string): void {
    const body = document.getElementById('pur-body');
    if (body) body.innerHTML = `<div class="state">${html}</div>`;
}

async function load(): Promise<void> {
    showState(escapeHtml(t('pur-loading')));
    const ws = activeWsId();
    try {
        const params = ws != null ? '?workspace_client_id=' + ws : '';
        const data = (await papi('GET', '/api/purchase/docs' + params)) as {
            docs?: Record<string, unknown>[];
            summary?: Record<string, unknown>;
        };
        allDocs = (data.docs || []).map(normListItem);
        summary = data.summary ? normSummary(data.summary) : null;
        renderBody();
    } catch (e) {
        showState(
            `${escapeHtml(purchaseErrMsg(e, 'purchase.unexpected'))}<br><button class="btn" id="pur-retry">${escapeHtml(t('pur-retry'))}</button>`
        );
        const retry = document.getElementById('pur-retry');
        if (retry) retry.onclick = () => load();
    }
}

window.loadPurchaseList = function () {
    const sec = document.getElementById('page-purchase');
    if (!sec) return;
    injectPurBase();
    injectStyle('pur-list-css', PAGE_CSS);
    sec.innerHTML = shell();
    bindChrome();
    load();
};
