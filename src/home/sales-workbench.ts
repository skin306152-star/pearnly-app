// 销项开票模块 PO-10 · 发票工作台(列表 / 汇总卡 / 筛选 / 搜索)
// 接真接口 GET /api/sales/documents · 四态 UI · 行点击进详情弹窗(sales-detail)。
// 视觉照桌面样稿 Pearnly开票UI预览/app.html vInv;令牌复用 home-39-sales.css。
/* global t, escapeHtml, apiGet, showToast, routeTo */
import { type SalesDoc, docTypeLabel, fmtMoney, fmtDate } from './sales-common.js';
import { BAHT } from './money.js';
import { setErpIntakeDirection } from './erp-intake.js';

const ICON_INV =
    '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 13h8M8 17h5"/></svg>';
const ICON_GEAR =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><circle cx="12" cy="12" r="3"/><path d="M19.4 13a7 7 0 0 0 0-2l2-1.5-2-3.5-2.3 1a7 7 0 0 0-1.7-1L15 3H9l-.4 2.5a7 7 0 0 0-1.7 1l-2.3-1-2 3.5L4.6 11a7 7 0 0 0 0 2l-2 1.5 2 3.5 2.3-1a7 7 0 0 0 1.7 1L9 21h6l.4-2.5a7 7 0 0 0 1.7-1l2.3 1 2-3.5-2-1.5Z"/></svg>';
const ICON_PLUS =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2"><path d="M12 5v14M5 12h14"/></svg>';
const ICON_CHEV =
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="m9 18 6-6-6-6"/></svg>';

const PAY_STATES = ['paid', 'unpaid', 'partial'];
type Filter = 'all' | 'draft' | 'issued' | 'void';
type PageMode = 'invoices' | 'records';

let allDocs: SalesDoc[] = []; // 汇总卡数据源(全量·不随筛选变)
let docs: SalesDoc[] = []; // 表格当前视图(服务端 status/q 筛选结果)
let filter: Filter = 'all';
let keyword = '';
let searchTimer: number | undefined;
let pageMode: PageMode = 'invoices';

function payState(d: SalesDoc): string {
    const s = (d.payment && d.payment.status) || '';
    return PAY_STATES.indexOf(s) >= 0 ? s : 'unpaid';
}

function buyerName(d: SalesDoc): string {
    return (d.buyer && d.buyer.name) || '—';
}

function inCurrentMonth(iso: string | null): boolean {
    if (!iso) return false;
    const now = new Date();
    const ym = now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0');
    return iso.slice(0, 7) === ym;
}

// 汇总卡始终基于全量(本月开票/草稿数/应收),不受表格筛选影响。
function summary() {
    const issued = allDocs.filter((d) => d.status === 'issued');
    const monthIssued = issued.filter((d) => inCurrentMonth(d.issue_date));
    const monthAmount = monthIssued.reduce((s, d) => s + Number(d.grand_total || 0), 0);
    const drafts = allDocs.filter((d) => d.status === 'draft').length;
    const due = issued
        .filter((d) => payState(d) !== 'paid')
        .reduce((s, d) => s + (Number(d.grand_total || 0) - Number(d.payment.paid_amount || 0)), 0);
    return { count: monthIssued.length, amount: monthAmount, drafts, due };
}

function rowsHtml(): string {
    const list = docs;
    if (!list.length) return '';
    return list
        .map((d) => {
            const pay = payState(d);
            const num = d.doc_number || t('sx-draft-tag');
            return `<tr class="click" data-doc="${escapeHtml(d.id)}">
                <td><b>${escapeHtml(num)}</b></td>
                <td style="color:var(--ink-3)">${escapeHtml(fmtDate(d.issue_date))}</td>
                <td>${escapeHtml(docTypeLabel(d.doc_type))}</td>
                <td>${escapeHtml(buyerName(d))}</td>
                <td class="r">${fmtMoney(d.grand_total)}</td>
                <td>${d.status === 'issued' ? `<span class="sx-badge ${pay}">${escapeHtml(t('sx-pay-' + pay))}</span>` : '—'}</td>
                <td><span class="sx-badge ${escapeHtml(d.status)}">${escapeHtml(t('sx-st-' + d.status))}</span></td>
                <td class="r"><button class="sx-chev" data-doc="${escapeHtml(d.id)}" aria-label="${escapeHtml(t('sx-detail-title'))}">${ICON_CHEV}</button></td>
            </tr>`;
        })
        .join('');
}

// 空态卡是表格的兄弟节点、不是 <td colspan>:窄屏下 .sx-panel 横向滚、表格 min-width 640,
// 放进单元格就按表格滚动宽度居中 → 「暂无发票」被推到视口外(手机 390 实测半张卡在屏外)。
function emptyHtml(show: boolean): string {
    return `<div class="sx-state" id="sx-wb-empty"${show ? '' : ' hidden'}>${ICON_INV}<div>${escapeHtml(
        t(pageMode === 'records' ? 'sx-records-empty' : 'sx-empty')
    )}</div></div>`;
}

function listInnerHtml(): string {
    const s = summary();
    const seg = (['all', 'draft', 'issued', 'void'] as Filter[])
        .map(
            (f) =>
                `<button data-flt="${f}" class="${filter === f ? 'on' : ''}">${escapeHtml(t('sx-f-' + f))}</button>`
        )
        .join('');
    const empty = !docs.length;
    return `<div class="sx-cards">
        <div class="sx-stat"><div class="sx-l">${escapeHtml(t(pageMode === 'records' ? 'sx-records-card-month' : 'sx-card-month'))}</div><div class="sx-v">${s.count} <small>${escapeHtml(t('sx-unit-docs'))}</small></div></div>
        <div class="sx-stat"><div class="sx-l">${escapeHtml(t(pageMode === 'records' ? 'sx-records-card-amount' : 'sx-card-amount'))}</div><div class="sx-v">${BAHT}${fmtMoney(s.amount)}</div></div>
        <div class="sx-stat"><div class="sx-l">${escapeHtml(t('sx-card-draft'))}</div><div class="sx-v">${s.drafts}</div></div>
        <div class="sx-stat"><div class="sx-l">${escapeHtml(t('sx-card-due'))}</div><div class="sx-v warn">${BAHT}${fmtMoney(s.due)}</div></div>
    </div>
    <div class="sx-toolbar">
        <div class="sx-seg">${seg}</div>
        <div class="sx-search"><input type="text" id="sx-wb-search" value="${escapeHtml(keyword)}" placeholder="${escapeHtml(t('sx-search-ph'))}"></div>
    </div>
    <div class="sx-panel"><table class="sx-tbl" id="sx-wb-tbl"${empty ? ' hidden' : ''}>
        <thead><tr>
            <th>${escapeHtml(t('sx-col-no'))}</th><th>${escapeHtml(t('sx-col-date'))}</th>
            <th>${escapeHtml(t('sx-col-type'))}</th><th>${escapeHtml(t('sx-col-client'))}</th>
            <th class="r">${escapeHtml(t('sx-col-amount'))}</th><th>${escapeHtml(t('sx-col-pay'))}</th>
            <th>${escapeHtml(t('sx-col-status'))}</th><th></th>
        </tr></thead>
        <tbody id="sx-wb-tbody">${rowsHtml()}</tbody>
    </table>${emptyHtml(empty)}</div>`;
}

function pageShell(mode: PageMode): string {
    const titleKey = mode === 'records' ? 'sx-records-title' : 'sx-wb-title';
    const actions =
        mode === 'records'
            ? `<button class="btn btn-primary" id="sx-record-btn">${ICON_PLUS}<span data-i18n="sx-record-sale">${escapeHtml(t('sx-record-sale'))}</span></button>`
            : `<button class="btn btn-ghost" id="sx-settings-btn">${ICON_GEAR}<span>${escapeHtml(t('sx-settings'))}</span></button>
                <button class="btn btn-primary" id="sx-new-btn">${ICON_PLUS}<span>${escapeHtml(t('sx-new'))}</span></button>`;
    return `<div class="wrap sx-page">
        <div class="pagehead">
            <div>
                <div class="h1" data-i18n="${titleKey}">${escapeHtml(t(titleKey))}</div>
            </div>
            <div class="sx-actions">${actions}</div>
        </div>
        <div id="sx-wb-body"></div>
    </div>`;
}

function renderBody(html: string) {
    const body = document.getElementById('sx-wb-body');
    if (body) body.innerHTML = html;
}

// 搜索/筛选只换行,不重渲整页(重渲会丢搜索框焦点)· 有数据与没数据的互换在这里同步表格与空态卡。
function rerenderRows() {
    const tb = document.getElementById('sx-wb-tbody');
    if (tb) tb.innerHTML = rowsHtml();
    const tbl = document.getElementById('sx-wb-tbl');
    const empty = document.getElementById('sx-wb-empty');
    if (tbl) (tbl as HTMLElement).hidden = !docs.length;
    if (empty) (empty as HTMLElement).hidden = !!docs.length;
    bindRows();
}

function bindRows() {
    document.querySelectorAll<HTMLElement>('#sx-wb-body [data-doc]').forEach((el) => {
        el.onclick = (e) => {
            e.stopPropagation();
            if (window.openSalesDetail) window.openSalesDetail(el.dataset.doc!);
        };
    });
}

function bindBody() {
    document.querySelectorAll<HTMLElement>('#sx-wb-body [data-flt]').forEach((el) => {
        el.onclick = async () => {
            filter = el.dataset.flt as Filter;
            try {
                docs = await fetchDocs();
            } catch (_) {
                return;
            }
            renderBody(listInnerHtml());
            bindBody();
        };
    });
    const search = document.getElementById('sx-wb-search') as HTMLInputElement | null;
    if (search) {
        search.oninput = () => {
            keyword = search.value;
            clearTimeout(searchTimer);
            searchTimer = window.setTimeout(refreshView, 250);
        };
    }
    bindRows();
}

// 服务端筛选:GET /api/sales/documents?status=&q=('all' 不传 status,空关键词不传 q)。
async function fetchDocs(): Promise<SalesDoc[]> {
    const params = new URLSearchParams();
    if (filter !== 'all') params.set('status', filter);
    const kw = keyword.trim();
    if (kw) params.set('q', kw);
    const qs = params.toString();
    const data = await apiGet('/api/sales/documents' + (qs ? '?' + qs : ''));
    return (data && (data.documents as SalesDoc[])) || [];
}

// 搜索输入:只刷表格行(不重渲整页 → 不丢搜索框焦点/光标)。
async function refreshView() {
    try {
        docs = await fetchDocs();
    } catch (_) {
        return;
    }
    rerenderRows();
}

function bindShell() {
    const recordBtn = document.getElementById('sx-record-btn');
    if (recordBtn) recordBtn.onclick = () => setErpIntakeDirection('sales');
    const newBtn = document.getElementById('sx-new-btn');
    if (newBtn) newBtn.onclick = () => window.openSalesWizard?.();
    const setBtn = document.getElementById('sx-settings-btn');
    if (setBtn) setBtn.onclick = () => window.openSalesSettings?.();
}

async function load() {
    renderBody(`<div class="sx-state">${escapeHtml(t('sx-loading'))}</div>`);
    try {
        const data = await apiGet('/api/sales/documents');
        if (!data) return; // 鉴权失败已由 apiGet 处理
        allDocs = (data.documents || []) as SalesDoc[];
        // 有筛选/搜索在身则取服务端结果,否则全量即视图(省一次请求)。
        docs = filter !== 'all' || keyword.trim() ? await fetchDocs() : allDocs;
        renderBody(listInnerHtml());
        bindBody();
    } catch (e) {
        renderBody(
            `<div class="sx-state error">${escapeHtml(t('sx-error'))}<br><button class="btn btn-ghost" id="sx-retry">${escapeHtml(t('sx-retry'))}</button></div>`
        );
        const retry = document.getElementById('sx-retry');
        if (retry) retry.onclick = () => load();
    }
}

function mount(pageId: string, mode: PageMode): void {
    const sec = document.getElementById(pageId);
    if (!sec) return;
    pageMode = mode;
    const siblingId = mode === 'records' ? 'page-sales-invoices' : 'page-sales-records';
    const sibling = document.getElementById(siblingId);
    if (sibling) sibling.innerHTML = '';
    sec.classList.add('ui');
    sec.innerHTML = pageShell(mode);
    bindShell();
    load();
}

window.loadSalesWorkbench = function () {
    mount('page-sales-invoices', 'invoices');
};

window.loadSalesRecords = function () {
    mount('page-sales-records', 'records');
};

// 详情里作废/红冲后回流刷新工作台
window.addEventListener('pearnly:sales-changed', () => {
    if (
        typeof currentRoute !== 'undefined' &&
        (currentRoute === 'sales-invoices' || currentRoute === 'sales-records')
    )
        load();
});

if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('sales-workbench', () => {
        if (typeof currentRoute === 'undefined') return;
        if (currentRoute === 'sales-invoices') window.loadSalesWorkbench?.();
        if (currentRoute === 'sales-records') window.loadSalesRecords?.();
    });
}

// 切账套重载已统一收口到 core-boot 全局 pearnly:workspace-changed → reloadCurrentRoute。

// 2026-06-10 Claude 式导航:销售发票二级子组拍平为一级子项 · 原 initSalesSubnav 随之退场。
