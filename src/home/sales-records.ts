/* global t, escapeHtml, apiGet, showToast */
import { type SalesDoc, fmtMoney } from './sales-common.js';
import { BAHT } from './money.js';
import { injectStyle } from './purchase-common.js';
import { PURCHASE_LIST_CSS } from './purchase-list-css.js';
import { MORE_SVG } from './more-menu.js';
import { setErpIntakeDirection } from './erp-intake.js';
import { fetchErpEndpoints, pickDefaultTarget, pushHistory } from './dms-intake-erp-push.js';
import { SALES_RECORDS_CSS } from './sales-records-css.js';

type Segment = 'all' | 'goods' | 'service' | 'unpaid';
type SelectKey = 'date' | 'doc' | 'source' | 'push';
type DateBasis = 'doc' | 'upload';

const ICON_SEARCH =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>';
const ICON_PEN =
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>';
const CHEV =
    '<svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>';

let docs: SalesDoc[] = [];
let segment: Segment = 'all';
let keyword = '';
let searchTimer: number | undefined;
let dateBasis: DateBasis = 'doc';
const selects: Record<SelectKey, string> = { date: '', doc: '', source: '', push: '' };

function payState(doc: SalesDoc): string {
    const value = doc.payment?.status || 'unpaid';
    return ['paid', 'partial'].includes(value) ? value : 'unpaid';
}

function lineKinds(doc: SalesDoc): Set<string> {
    const kinds = new Set<string>();
    (doc.lines || []).forEach((line) => {
        if (line.item_type) kinds.add(line.item_type);
    });
    if (!kinds.size && doc.posting_kind)
        kinds.add(doc.posting_kind === 'stock' ? 'goods' : 'service');
    return kinds;
}

function kindOf(doc: SalesDoc): 'goods' | 'service' | 'mixed' {
    const kinds = lineKinds(doc);
    if (kinds.has('goods') && kinds.has('service')) return 'mixed';
    return kinds.has('service') ? 'service' : 'goods';
}

function sourceOf(doc: SalesDoc): string {
    if (doc.source === 'line_erp') return 'line';
    if (doc.source === 'erp_web') return 'web';
    return 'legacy';
}

function isThisMonth(value: string | null): boolean {
    if (!value) return false;
    const now = new Date();
    return (
        value.slice(0, 7) === `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
    );
}

function summary(): { total: number; goods: number; service: number; vat: number } {
    const month = docs.filter((doc) => doc.status !== 'void' && isThisMonth(doc.issue_date));
    let goods = 0;
    let service = 0;
    month.forEach((doc) => {
        (doc.lines || []).forEach((line) => {
            const amount =
                line.line_total == null
                    ? Number(line.amount ?? line.unit_price ?? 0) * Number(line.qty || 1)
                    : Number(line.line_total);
            if (line.item_type === 'service') service += amount;
            else goods += amount;
        });
    });
    return {
        total: month.reduce((sum, doc) => sum + Number(doc.grand_total || 0), 0),
        goods,
        service,
        vat: month.reduce((sum, doc) => sum + Number(doc.vat_amount || 0), 0),
    };
}

function inDateRange(doc: SalesDoc): boolean {
    if (!selects.date) return true;
    const date = basisDate(doc);
    const now = new Date();
    const month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    if (selects.date === 'this') return date.startsWith(month);
    const prev = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const prevMonth = `${prev.getFullYear()}-${String(prev.getMonth() + 1).padStart(2, '0')}`;
    return date.startsWith(prevMonth);
}

function basisDate(doc: SalesDoc): string {
    const value = dateBasis === 'upload' ? doc.created_at || doc.issue_date : doc.issue_date;
    return (value || '').slice(0, 10);
}

function view(): SalesDoc[] {
    const key = keyword.trim().toLowerCase();
    return docs.filter((doc) => {
        const kind = kindOf(doc);
        if (segment === 'goods' && kind === 'service') return false;
        if (segment === 'service' && kind === 'goods') return false;
        if (segment === 'unpaid' && payState(doc) === 'paid') return false;
        if (!inDateRange(doc)) return false;
        if (selects.doc && doc.doc_type !== selects.doc) return false;
        if (selects.source && sourceOf(doc) !== selects.source) return false;
        if (selects.push && (doc.push_status || 'not_pushed') !== selects.push) return false;
        if (!key) return true;
        const lineText = (doc.lines || []).map((line) => line.description || '').join(' ');
        return `${doc.doc_number || ''} ${doc.buyer?.name || ''} ${lineText}`
            .toLowerCase()
            .includes(key);
    });
}

function segmentHtml(): string {
    return (['all', 'goods', 'service', 'unpaid'] as Segment[])
        .map(
            (value) =>
                `<span class="o${segment === value ? ' on' : ''}" data-sr-seg="${value}">${escapeHtml(t('sr-seg-' + value))}</span>`
        )
        .join('');
}

function option(value: string, key: string): string {
    return `<option value="${value}">${escapeHtml(t(key))}</option>`;
}

function filterHtml(): string {
    return `<div class="sr-filter">
        <label>${escapeHtml(t('sr-filter-date'))}<select data-sr-select="date">${option('', 'sr-filter-all')}${option('this', 'sr-date-this')}${option('last', 'sr-date-last')}</select></label>
        <label>${escapeHtml(t('sr-filter-doc'))}<select data-sr-select="doc">${option('', 'sr-filter-all')}${option('tax_invoice', 'sx-dt-tax_invoice')}${option('receipt', 'sx-dt-receipt')}${option('tax_invoice_simple', 'sx-dt-tax_invoice_simple')}</select></label>
        <label>${escapeHtml(t('sr-filter-source'))}<select data-sr-select="source">${option('', 'sr-filter-all')}${option('web', 'sr-source-web')}${option('line', 'sr-source-line')}${option('legacy', 'sr-source-legacy')}</select></label>
        <label>${escapeHtml(t('sr-filter-push'))}<select data-sr-select="push">${option('', 'sr-filter-all')}${option('not_pushed', 'sr-push-not_pushed')}${option('pending', 'sr-push-pending')}${option('success', 'sr-push-success')}${option('failed', 'sr-push-failed')}</select></label>
        <div class="datebasis" id="sr-datebasis">
            <span class="o ${dateBasis === 'doc' ? 'on' : ''}" data-sr-basis="doc">${escapeHtml(t('pur-basis-doc'))}</span>
            <span class="o ${dateBasis === 'upload' ? 'on' : ''}" data-sr-basis="upload">${escapeHtml(t('pur-basis-upload'))}</span>
        </div>
    </div>`;
}

function monthKey(doc: SalesDoc): string {
    return (basisDate(doc) || '0000-00').slice(0, 7);
}

function monthLabel(key: string): string {
    if (!/^\d{4}-\d{2}$/.test(key)) return t('sr-date-unknown');
    return new Intl.DateTimeFormat(document.documentElement.lang || 'th', {
        year: 'numeric',
        month: 'long',
    }).format(new Date(`${key}-01T00:00:00`));
}

function sourceChip(doc: SalesDoc): string {
    const source = sourceOf(doc);
    return `<span class="src ${source}">${escapeHtml(t('sr-source-' + source))}</span>`;
}

function kindChip(doc: SalesDoc): string {
    const kind = kindOf(doc);
    return `<span class="kind ${kind}">${escapeHtml(t('sr-kind-' + kind))}</span>`;
}

function pushButton(doc: SalesDoc): string {
    const status = doc.push_status || 'not_pushed';
    const disabled = status === 'success' ? ' disabled' : '';
    return `<button class="erp ${status}" data-sr-push="${escapeHtml(doc.id)}"${disabled}>${escapeHtml(t('sr-push-' + status))}</button>`;
}

function rowHtml(doc: SalesDoc): string {
    const date = (basisDate(doc) || '—').slice(5, 10).replace('-', '/');
    const vat =
        Number(doc.vat_amount || 0) > 0
            ? `<div class="vat">${escapeHtml(t('sr-output-vat'))} ${BAHT}${fmtMoney(doc.vat_amount)}</div>`
            : '';
    return `<div class="row" data-sr-doc="${escapeHtml(doc.id)}">
        <span class="dt tnum">${escapeHtml(date)}</span>
        <div class="who"><div class="nm">${escapeHtml(doc.buyer?.name || t('sr-buyer-unknown'))}</div>
            <div class="meta">${sourceChip(doc)}${kindChip(doc)}<span class="docno">${escapeHtml(doc.doc_number || '—')}</span></div></div>
        <div class="amt"><div class="v">${BAHT}${fmtMoney(doc.grand_total)}</div>${vat}</div>
        <span class="st ${payState(doc)}">${escapeHtml(t('sx-pay-' + payState(doc)))}</span>
        <div class="erpbox">${pushButton(doc)}</div>
    </div>`;
}

function groupsHtml(list: SalesDoc[]): string {
    const groups = new Map<string, SalesDoc[]>();
    list.forEach((doc) => groups.set(monthKey(doc), [...(groups.get(monthKey(doc)) || []), doc]));
    return [...groups.entries()]
        .map(([key, items], index) => {
            const sum = items.reduce((value, doc) => value + Number(doc.grand_total || 0), 0);
            return `<div class="monthgrp"><div class="gh" data-sr-group="${index}">${escapeHtml(monthLabel(key))}<span class="cnt">${items.length} ${escapeHtml(t('sr-unit-records'))}</span><span class="sum">${escapeHtml(t('sr-group-total'))} ${BAHT}${fmtMoney(sum)}</span>${CHEV}</div><div class="glist">${items.map(rowHtml).join('')}</div></div>`;
        })
        .join('');
}

function renderBody(): void {
    const body = document.getElementById('sr-body');
    const list = view();
    if (body)
        body.innerHTML = list.length
            ? groupsHtml(list)
            : `<div class="state">${escapeHtml(t('sx-records-empty'))}</div>`;
    const count = document.getElementById('sr-count');
    if (count) count.textContent = list.length ? t('sr-count', { n: String(list.length) }) : '';
    bindRows();
}

async function push(doc: SalesDoc, button: HTMLButtonElement): Promise<void> {
    if (!doc.ocr_history_id) return;
    button.disabled = true;
    const endpoints = await fetchErpEndpoints();
    const target = pickDefaultTarget(endpoints, '');
    if (!target) {
        showToast(t('sr-no-endpoint'), 'error');
        button.disabled = false;
        return;
    }
    const outcome = await pushHistory(doc.ocr_history_id, target);
    showToast(t('sr-push-result-' + outcome), outcome === 'failed' ? 'error' : 'success');
    await load();
}

function exportRecords(): void {
    const historyIds = view()
        .map((doc) => doc.ocr_history_id)
        .filter((id): id is string => !!id);
    if (!historyIds.length) {
        showToast(t('sr-export-empty'), 'info');
        return;
    }
    window.openSalesExport?.(historyIds);
}

function bindRows(): void {
    document.querySelectorAll<HTMLElement>('[data-sr-doc]').forEach((row) => {
        row.onclick = () => window.openSalesRecordDetail?.(row.dataset.srDoc!);
    });
    document.querySelectorAll<HTMLButtonElement>('[data-sr-push]').forEach((button) => {
        button.onclick = (event) => {
            event.stopPropagation();
            const doc = docs.find((item) => item.id === button.dataset.srPush);
            if (doc) void push(doc, button);
        };
    });
    document.querySelectorAll<HTMLElement>('[data-sr-group]').forEach((head) => {
        head.onclick = () => head.closest('.monthgrp')?.classList.toggle('collapsed');
    });
}

function bindControls(): void {
    document.querySelectorAll<HTMLElement>('[data-sr-seg]').forEach((item) => {
        item.onclick = () => {
            segment = item.dataset.srSeg as Segment;
            document
                .querySelectorAll<HTMLElement>('[data-sr-seg]')
                .forEach((node) => node.classList.toggle('on', node === item));
            renderBody();
        };
    });
    const search = document.getElementById('sr-search') as HTMLInputElement | null;
    if (search)
        search.oninput = () => {
            keyword = search.value;
            clearTimeout(searchTimer);
            searchTimer = window.setTimeout(renderBody, 180);
        };
    document.querySelectorAll<HTMLSelectElement>('[data-sr-select]').forEach((select) => {
        select.value = selects[select.dataset.srSelect as SelectKey];
        select.onchange = () => {
            selects[select.dataset.srSelect as SelectKey] = select.value;
            renderBody();
        };
    });
    document.querySelectorAll<HTMLElement>('[data-sr-basis]').forEach((item) => {
        item.onclick = () => {
            dateBasis = item.dataset.srBasis as DateBasis;
            document
                .querySelectorAll<HTMLElement>('[data-sr-basis]')
                .forEach((node) => node.classList.toggle('on', node === item));
            renderBody();
        };
    });
    document
        .getElementById('sr-record-btn')
        ?.addEventListener('click', () => setErpIntakeDirection('sales'));
    document
        .getElementById('sr-line-btn')
        ?.addEventListener('click', () => window.routeTo?.('integrations'));
    document
        .getElementById('sr-logs-btn')
        ?.addEventListener('click', () => window.routeTo?.('push-logs'));
    document.getElementById('sr-export-btn')?.addEventListener('click', exportRecords);
}

function shell(): string {
    const stat = summary();
    const cell = (key: string, value: number, green = false) =>
        `<div><span>${escapeHtml(t(key))}</span><b${green ? ' class="g"' : ''}>${BAHT}${fmtMoney(value)}</b></div>`;
    return `<div class="pur pl sr"><div class="wrap">
        <div class="ph"><div><div class="t">${escapeHtml(t('sx-records-title'))}</div><div class="sub">${escapeHtml(t('sr-subtitle'))}</div></div></div>
        <div class="panel"><div class="band"><div class="star"><div class="big tnum">${BAHT}${fmtMoney(stat.total)}<small>${escapeHtml(t('sr-month-sales'))}</small></div><div class="ctx">${cell('sr-goods-sales', stat.goods)}${cell('sr-service-sales', stat.service)}${cell('sr-output-vat', stat.vat, true)}</div></div>
        <div class="acts"><button class="btn" id="sr-export-btn">${escapeHtml(t('sr-export-archive'))}</button><button class="btn primary" id="sr-record-btn">${ICON_PEN}${escapeHtml(t('sx-record-sale'))}</button><div class="more-wrap"><button class="btn" aria-label="more">${MORE_SVG}</button><div class="more-menu right" hidden><button class="mi" id="sr-line-btn">${escapeHtml(t('sr-line-entry'))}</button><button class="mi" id="sr-logs-btn">${escapeHtml(t('sr-push-logs'))}</button></div></div></div></div>
        <div class="toolbar"><div class="seg">${segmentHtml()}</div><div class="search">${ICON_SEARCH}<input id="sr-search" value="${escapeHtml(keyword)}" placeholder="${escapeHtml(t('sr-search'))}"></div></div>
        ${filterHtml()}<div id="sr-body"><div class="state">${escapeHtml(t('sx-loading'))}</div></div><div class="listfoot" id="sr-count"></div>
        </div></div></div>`;
}

async function load(): Promise<void> {
    try {
        const data = await apiGet('/api/sales/documents');
        docs = ((data?.documents || []) as SalesDoc[]).filter((doc) => !!doc.ocr_history_id);
        const sec = document.getElementById('page-sales-records');
        if (!sec) return;
        sec.innerHTML = shell();
        bindControls();
        renderBody();
    } catch {
        const body = document.getElementById('sr-body');
        if (body) body.innerHTML = `<div class="state">${escapeHtml(t('sx-error'))}</div>`;
    }
}

window.loadSalesRecords = function () {
    const sec = document.getElementById('page-sales-records');
    if (!sec) return;
    document.getElementById('page-sales-invoices')!.innerHTML = '';
    sec.classList.add('ui');
    injectStyle('pur-list-css', PURCHASE_LIST_CSS);
    injectStyle('sales-records-css', SALES_RECORDS_CSS);
    sec.innerHTML = `<div class="wrap"><div class="state">${escapeHtml(t('sx-loading'))}</div></div>`;
    void load();
};

window.addEventListener('pearnly:sales-changed', () => {
    if (typeof currentRoute !== 'undefined' && currentRoute === 'sales-records') void load();
});

window.subscribeI18n?.('sales-records', () => {
    if (typeof currentRoute !== 'undefined' && currentRoute === 'sales-records')
        window.loadSalesRecords?.();
});
