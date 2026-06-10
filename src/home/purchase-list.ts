// 商户采购 · 屏1 采购/进项主屏 · 收拢版(照搬设计稿 01-采购进项主屏收拢版 · DESIGN_LANGUAGE)。
// 一个面板分层:① 主信息带(本月花费北极星 + 手动/LINE/拍票动作)② 未付行动条 ③ 控件带(筛选 seg + 搜)
// ④ 列表行(桌面/手机同一面板内 row · 不再 4 卡碎片飘灰底)。行点按 status 分流(draft→录入 / posted→详情)。
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
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>';
const ICON_SEARCH =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>';
const ICON_CAM_SM =
    '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/></svg>';

type Chip = 'all' | 'purchase' | 'expense' | 'unpaid';

// ⋯ 下拉点外关 · 全局只绑一次(bindChrome 每次重渲都会跑)
let purMoreCloserBound = false;

// 收拢版令牌页内自定义(.pur.pl 作用域 · 不动 base/detail/form):面板圆角16 · 按钮圆角11。
// PO 标准化:裸 hex 全换全局令牌(暗夜随翻面);.wrap 流式宽继承 base(去 1020 固定宽)。
const PAGE_CSS = `
.pur.pl .ph{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:16px;}
.pur.pl .ph .t{font-size:21px;font-weight:680;letter-spacing:-.2px;}
.pur.pl .ph .sub{color:var(--ink2);font-size:13px;margin-top:5px;}
.pur.pl .band{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:20px 22px;border-bottom:1px solid var(--line2);}
.pur.pl .star .lbl{color:var(--ink2);font-size:12.5px;margin-bottom:5px;}
.pur.pl .star .num{font-size:30px;font-weight:740;letter-spacing:-1px;line-height:1;}
.pur.pl .star .ctx{margin-top:8px;color:var(--ink2);font-size:12.5px;}
.pur.pl .star .ctx .g{color:var(--green);font-weight:600;}
.pur.pl .acts{display:flex;gap:9px;}
.pur.pl .btn{border-radius:11px;}
.pur.pl .btn.primary{font-weight:650;}
.pur.pl .alert{display:flex;align-items:center;gap:9px;padding:11px 22px;background:var(--amber-weak);border-bottom:1px solid var(--line2);font-size:13px;color:var(--amber);cursor:pointer;}
.pur.pl .alert .pip{width:7px;height:7px;border-radius:50%;background:var(--amber);flex:0 0 7px;}
.pur.pl .alert b{font-weight:700;color:var(--amber);}
.pur.pl .alert .go{margin-left:auto;color:var(--amber);font-weight:650;font-size:12.5px;}
.pur.pl .toolbar{display:flex;align-items:center;gap:12px;padding:11px 18px;border-bottom:1px solid var(--line2);background:var(--line2);}
.pur.pl .seg{display:inline-flex;gap:2px;}
.pur.pl .seg .o{height:30px;padding:0 13px;border-radius:8px;display:flex;align-items:center;font-size:12.5px;color:var(--ink2);cursor:pointer;}
.pur.pl .seg .o.on{background:var(--ink);color:var(--card);font-weight:600;}
.pur.pl .search{margin-left:auto;width:230px;height:34px;background:var(--card);border:1px solid var(--line);border-radius:9px;display:flex;align-items:center;gap:8px;padding:0 11px;}
.pur.pl .search input{border:0;outline:0;flex:1;background:transparent;font-size:13px;color:var(--ink);}
.pur.pl .row{display:flex;align-items:center;gap:14px;padding:15px 18px;border-bottom:1px solid var(--line2);cursor:pointer;}
.pur.pl .row:last-child{border-bottom:0;} .pur.pl .row:hover{background:var(--line2);}
.pur.pl .row .dt{width:46px;color:var(--ink3);font-size:12px;flex:0 0 46px;}
.pur.pl .row .who{flex:1;min-width:0;}
.pur.pl .row .nm{font-weight:600;font-size:14px;}
.pur.pl .row .meta{color:var(--ink3);font-size:12px;margin-top:2px;display:flex;align-items:center;gap:8px;}
.pur.pl .src{font-size:10.5px;padding:1px 7px;border-radius:5px;background:var(--line2);color:var(--ink2);}
.pur.pl .src.line{background:var(--green-weak);color:var(--green);}
.pur.pl .amt{text-align:right;}
.pur.pl .amt .v{font-weight:700;font-size:14.5px;font-variant-numeric:tabular-nums;}
.pur.pl .amt .vat{color:var(--ink3);font-size:11px;margin-top:2px;}
.pur.pl .st{font-size:11px;padding:3px 10px;border-radius:7px;min-width:52px;text-align:center;}
.pur.pl .st.paid{background:var(--line2);color:var(--ink2);}
.pur.pl .st.unpaid{background:var(--amber-weak);color:var(--amber);font-weight:600;}
.pur.pl .st.partial{background:var(--amber-weak);color:var(--amber);font-weight:600;}
@media(max-width:600px){
  .pur.pl .ph{flex-direction:column;align-items:flex-start;gap:11px;}
  .pur.pl .band{flex-direction:column;align-items:stretch;gap:14px;}
  .pur.pl .acts{width:100%;} .pur.pl .acts .btn{flex:1;}
  .pur.pl .search{width:100%;margin-left:0;}
  .pur.pl .toolbar{flex-wrap:wrap;}
  .pur.pl .row{flex-wrap:wrap;}
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

function srcChip(d: DocListItem): string {
    const cls = d.source === 'line' ? 'src line' : 'src';
    const ico = d.source === 'photo' ? ICON_CAM_SM : '';
    return `<span class="${cls}">${ico}${escapeHtml(t(srcLabelKey(d.source)))}</span>`;
}

// 类型:有细分科目名用之,否则回退票种(进货/费用/采购单)。
function typeLabel(d: DocListItem): string {
    return d.category_label || t(kindLabelKey(d.doc_kind));
}

// ① 主信息带北极星:本月花费(进货+费用)+ 上下文(进货/费用/可抵进项税)。summary 缺 → 占位。
function starHtml(s: DocSummary | null): string {
    const spend = s ? s.purchase_total + s.expense_total : 0;
    const ctx = s
        ? `${escapeHtml(t('pur-chip-purchase'))} ${fmtBaht(s.purchase_total)} · ${escapeHtml(t('pur-chip-expense'))} ${fmtBaht(s.expense_total)} · <span class="g">${escapeHtml(t('pur-kpi-vat'))} ${fmtBaht(s.vat_creditable)}</span>`
        : '—';
    return `<div class="lbl">${escapeHtml(t('pur-month-spend'))}</div><div class="num tnum">${fmtBaht(spend)}</div><div class="ctx">${ctx}</div>`;
}

// ② 未付行动条:有未付才显(行动卡 · 点去未付筛选)。
function alertHtml(s: DocSummary | null): string {
    if (!s || s.unpaid_total <= 0) return '';
    const sup =
        s.unpaid_suppliers > 0
            ? ` · ${s.unpaid_suppliers} ${escapeHtml(t('pur-unit-suppliers'))}`
            : '';
    return `<div class="alert" id="pur-alert"><span class="pip"></span><b>${fmtBaht(s.unpaid_total)} ${escapeHtml(t('pur-kpi-unpaid'))}</b><span>${sup}</span><span class="go">${escapeHtml(t('pur-go-process'))} →</span></div>`;
}

function segHtml(): string {
    const defs: [Chip, string][] = [
        ['all', 'pur-chip-all'],
        ['purchase', 'pur-chip-purchase'],
        ['expense', 'pur-chip-expense'],
        ['unpaid', 'pur-chip-unpaid'],
    ];
    return defs
        .map(
            ([k, key]) =>
                `<div class="o ${k === chip ? 'on' : ''}" data-chip="${k}">${escapeHtml(t(key))}</div>`
        )
        .join('');
}

function rowsHtml(list: DocListItem[]): string {
    return list
        .map((d) => {
            const sup = escapeHtml(d.supplier_name || '—');
            const vat =
                d.vat_amount > 0
                    ? `<div class="vat">${escapeHtml(t('pur-vat-in'))} ${fmtBaht(d.vat_amount)}</div>`
                    : '';
            const pay = d.payment_status;
            return `<div class="row" data-id="${escapeHtml(d.id)}" data-status="${d.status}">
                <span class="dt tnum">${escapeHtml(fmtMonthDay(d.doc_date))}</span>
                <div class="who"><div class="nm">${sup}</div><div class="meta">${srcChip(d)}<span>${escapeHtml(typeLabel(d))}</span></div></div>
                <div class="amt"><div class="v">${fmtBaht(d.grand_total)}</div>${vat}</div>
                <span class="st ${pay}">${escapeHtml(t('pur-pay-' + pay))}</span>
            </div>`;
        })
        .join('');
}

function shell(): string {
    return `<div class="pur pl"><div class="wrap">
        <div class="ph"><div><div class="t">${escapeHtml(t('pur-title'))}</div><div class="sub">${escapeHtml(t('pur-subtitle'))}</div></div></div>
        <div class="panel">
            <div class="band">
                <div class="star" id="pur-star">${starHtml(summary)}</div>
                <div class="acts">
                    <button class="btn primary" id="pur-cam-btn">${ICON_CAM}${escapeHtml(t('pur-photo'))}</button>
                    <div class="more-wrap">
                        <button class="btn" id="pur-more-btn" aria-label="more"><svg viewBox="0 0 16 16" fill="currentColor" width="15" height="15"><circle cx="3" cy="8" r="1.3"/><circle cx="8" cy="8" r="1.3"/><circle cx="13" cy="8" r="1.3"/></svg></button>
                        <div class="more-menu right" id="pur-more-menu" hidden>
                            <button class="mi" id="pur-manual-btn">${escapeHtml(t('pur-manual-new'))}</button>
                            <button class="mi" id="pur-line-btn">${escapeHtml(t('pur-line-expense'))}</button>
                        </div>
                    </div>
                </div>
            </div>
            <div id="pur-alert-slot">${alertHtml(summary)}</div>
            <div class="toolbar">
                <div class="seg" id="pur-seg">${segHtml()}</div>
                <div class="search">${ICON_SEARCH}<input id="pur-search" placeholder="${escapeHtml(t('pur-search-ph'))}" value="${escapeHtml(keyword)}"></div>
            </div>
            <div id="pur-body"></div>
        </div>
        <input type="file" id="pur-cam-input" accept="image/*,application/pdf" style="display:none">
    </div></div>`;
}

function renderBody(): void {
    const star = document.getElementById('pur-star');
    if (star) star.innerHTML = starHtml(summary);
    const slot = document.getElementById('pur-alert-slot');
    if (slot) {
        slot.innerHTML = alertHtml(summary);
        const al = document.getElementById('pur-alert');
        if (al) al.onclick = () => setChip('unpaid');
    }
    const body = document.getElementById('pur-body');
    if (body) {
        const list = view();
        body.innerHTML = list.length
            ? rowsHtml(list)
            : `<div class="state">${escapeHtml(t('pur-empty'))}</div>`;
    }
    bindRows();
}

function setChip(c: Chip): void {
    chip = c;
    document.querySelectorAll<HTMLElement>('#pur-seg .o').forEach((el) => {
        el.classList.toggle('on', el.dataset.chip === c);
    });
    renderBody();
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
    document.querySelectorAll<HTMLElement>('#pur-seg .o').forEach((el) => {
        el.onclick = () => setChip(el.dataset.chip as Chip);
    });
    const search = document.getElementById('pur-search') as HTMLInputElement | null;
    if (search) {
        search.oninput = () => {
            keyword = search.value;
            clearTimeout(searchTimer);
            searchTimer = window.setTimeout(renderBody, 200);
        };
    }
    // S9 4-bis:拍票=唯一主入口 · 手动/LINE 收 ⋯ 下拉
    const moreBtn = document.getElementById('pur-more-btn');
    const moreMenu = document.getElementById('pur-more-menu');
    if (moreBtn && moreMenu) {
        moreBtn.onclick = (e) => {
            e.stopPropagation();
            moreMenu.hidden = !moreMenu.hidden;
        };
        if (!purMoreCloserBound) {
            purMoreCloserBound = true;
            document.addEventListener(
                'click',
                (e) => {
                    const el = e.target as HTMLElement;
                    if (el.closest('#pur-more-btn')) return;
                    const m = document.getElementById('pur-more-menu');
                    if (m && !m.hidden && !el.closest('#pur-more-menu')) m.hidden = true;
                },
                true
            );
        }
    }
    const manualBtn = document.getElementById('pur-manual-btn');
    // F3a · 手动记一笔(没发票费用)→ 直接进录入屏费用模式。
    if (manualBtn)
        manualBtn.onclick = () => {
            if (moreMenu) moreMenu.hidden = true;
            window.openPurchaseForm?.(null, { doc_kind: 'expense' });
        };
    const lineBtn = document.getElementById('pur-line-btn');
    if (lineBtn)
        lineBtn.onclick = () => {
            if (moreMenu) moreMenu.hidden = true;
            window.openPurchaseLine?.();
        };
    const camBtn = document.getElementById('pur-cam-btn');
    const camInput = document.getElementById('pur-cam-input') as HTMLInputElement | null;
    if (camBtn && camInput) camBtn.onclick = () => camInput.click();
    if (camInput) camInput.onchange = () => onCapture(camInput);
}

// 拍进项票 → 统一智能入口分流(F12)。后端返 {route,draft}:purchase/expense+draft→录入;
// sales/recon→提示去对应模块;inbox(低置信/糊图฿0/拿不准)→ 安全落待归类并带去收件箱(绝不进฿0单)。
async function onCapture(input: HTMLInputElement): Promise<void> {
    const f = input.files && input.files[0];
    input.value = '';
    if (!f) return;
    const ws = activeWsId();
    const fd = new FormData();
    fd.append('image', f);
    if (ws != null) fd.append('workspace_client_id', String(ws));
    showToast(t('pur-intake-reading'), 'info');
    try {
        const res = (await papi('POST', '/api/purchase/intake', fd)) as {
            route?: string;
            draft?: Record<string, unknown> | null;
            dedupe_hit?: boolean;
        };
        const d = res && res.draft;
        if (d) {
            // 刚拍那张本地 blob 即时显示(不等后端 serving)· 后端已存盘,保存时按 ref 挂附件。
            window.openPurchaseForm?.(null, {
                ...d,
                dedupe_hit: res.dedupe_hit,
                bill_image_local: URL.createObjectURL(f),
            });
            return;
        }
        const route = (res && res.route) || 'inbox';
        if (route === 'sales') {
            showToast(t('pur-intake-sales'), 'error');
        } else if (route === 'recon') {
            showToast(t('pur-intake-recon'), 'error');
        } else {
            showToast(t('pur-intake-inbox'), 'success');
            window.routeTo?.('purchase-inbox');
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
