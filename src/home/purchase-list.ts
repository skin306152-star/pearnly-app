// 商户采购 · 屏1 采购/进项主屏(收拢版 · 照搬 docs/smart-intake 原型)。
// 面板分层:① 北极星带(本月花费 + 拍票/手动/LINE 动作)② 未付行动条 ③ 段控(全部/进货/费用/未付)+ 搜
// ④ 多选筛选条(日期/文档类型/付款状态/分类 · 票面/上传口径)⑤ 批量条 ⑥ 按月分组列表(逐行多选+折叠)。
// 行点 status 分流(draft→录入 / posted→详情);筛选/分组/批量见 purchase-list-filters。无报销人列。
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
    type Category,
} from './purchase-common.js';
import { PURCHASE_LIST_CSS } from './purchase-list-css.js';
import {
    filterBarHtml,
    bindFilterChips,
    applyFilters,
    dateRangeParams,
    groupByMonth,
    monthLabel,
} from './purchase-list-filters.js';
import { MORE_SVG } from './more-menu.js';

const ICON_SEARCH =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>';
const ICON_CAM_SM =
    '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/></svg>';
const ICON_TRASH =
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 7h14M9 7V5h6v2M7 7l1 13h8l1-13"/></svg>';
const ICON_PEN =
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>';
const CHECK_SVG =
    '<svg viewBox="0 0 24 24" fill="none" stroke-width="3"><path d="M5 12l5 5 9-11"/></svg>';
const CHEV_SVG =
    '<svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>';

type Chip = 'all' | 'purchase' | 'expense' | 'unpaid';

let allDocs: DocListItem[] = [];
let summary: DocSummary | null = null;
let cats: Category[] = [];
let chip: Chip = 'all';
let keyword = '';
let searchTimer: number | undefined;
const selected = new Set<string>();

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
    return applyFilters(allDocs.filter((d) => matchChip(d) && matchKw(d)));
}

function srcChip(d: DocListItem): string {
    const cls = d.source === 'line' ? 'src line' : 'src';
    const ico = d.source === 'photo' ? ICON_CAM_SM : '';
    return `<span class="${cls}">${ico}${escapeHtml(t(srcLabelKey(d.source)))}</span>`;
}
function typeLabel(d: DocListItem): string {
    return d.category_label || t(kindLabelKey(d.doc_kind));
}

function starHtml(s: DocSummary | null): string {
    // 照草稿 .northstar:大数字在左 +「本月花费」在其下 · 进货/费用/可抵 inline(label 上、值下)。
    const spend = s ? s.purchase_total + s.expense_total : 0;
    const ci = (label: string, val: string, g?: boolean): string =>
        `<div><span>${escapeHtml(label)}</span><b${g ? ' class="g"' : ''}>${val}</b></div>`;
    const ctx = s
        ? ci(t('pur-chip-purchase'), fmtBaht(s.purchase_total)) +
          ci(t('pur-chip-expense'), fmtBaht(s.expense_total)) +
          ci(t('pur-kpi-vat'), fmtBaht(s.vat_creditable), true)
        : '';
    return `<div class="big tnum">${fmtBaht(spend)}<small>${escapeHtml(t('pur-month-spend'))}</small></div><div class="ctx">${ctx}</div>`;
}
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

function rowHtml(d: DocListItem): string {
    const sup = escapeHtml(d.supplier_name || '—');
    const vat =
        d.vat_amount > 0
            ? `<div class="vat">${escapeHtml(t('pur-vat-in'))} ${fmtBaht(d.vat_amount)}</div>`
            : '';
    const att = d.attachment_count > 1 ? `<span class="att">+${d.attachment_count - 1}</span>` : '';
    const on = selected.has(d.id) ? 'on' : '';
    return `<div class="row" data-id="${escapeHtml(d.id)}" data-status="${d.status}">
        <span class="rowchk ${on}" data-pick="${escapeHtml(d.id)}">${CHECK_SVG}</span>
        <span class="dt tnum">${escapeHtml(fmtMonthDay(d.doc_date))}</span>
        <div class="who"><div class="nm">${sup}</div><div class="meta">${srcChip(d)}<span>${escapeHtml(typeLabel(d))}</span>${att}</div></div>
        <div class="amt"><div class="v">${fmtBaht(d.grand_total)}</div>${vat}</div>
        <span class="st ${d.payment_status}">${escapeHtml(t('pur-pay-' + d.payment_status))}</span>
    </div>`;
}

function groupsHtml(list: DocListItem[]): string {
    return groupByMonth(list)
        .map((g, gi) => {
            const allOn = g.docs.every((d) => selected.has(d.id)) ? 'on' : '';
            return `<div class="monthgrp" data-grp="${gi}">
                <div class="gh" data-grphead="${gi}"><span class="gchk ${allOn}" data-grpchk="${gi}">${CHECK_SVG}</span>${escapeHtml(monthLabel(g.key))} <span class="cnt">${g.docs.length} ${escapeHtml(t('pur-unit-rows'))}</span><span class="sum">${escapeHtml(t('pur-group-sum'))} ${fmtBaht(g.sum)}</span>${CHEV_SVG}</div>
                <div class="glist">${g.docs.map(rowHtml).join('')}</div>
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
                    <button class="btn primary" id="pur-record-btn">${ICON_PEN}${escapeHtml(t('pur-record-purchase'))}</button>
                    <div class="more-wrap">
                        <button class="btn" id="pur-more-btn" aria-label="more">${MORE_SVG}</button>
                        <div class="more-menu right" id="pur-more-menu" hidden>
                            <button class="mi" id="pur-export-btn">${escapeHtml(t('pur-export-archive'))}</button>
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
            <div id="pur-filterbar"></div>
            <div class="bulkbar" id="pur-bulkbar">${escapeHtml(t('pur-bulk-selected'))} <b id="pur-bulk-n">0</b><span class="del" id="pur-bulk-del">${ICON_TRASH} ${escapeHtml(t('pur-bulk-delete'))}</span></div>
            <div id="pur-body"></div>
            <div class="listfoot" id="pur-listfoot"></div>
        </div>
    </div></div>`;
}

function renderFilterbar(): void {
    const fb = document.getElementById('pur-filterbar');
    if (!fb) return;
    fb.innerHTML = filterBarHtml(cats);
    bindFilterChips(renderBody);
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
    const list = view();
    if (body) {
        body.innerHTML = list.length
            ? groupsHtml(list)
            : `<div class="state">${escapeHtml(t('pur-empty'))}</div>`;
    }
    const foot = document.getElementById('pur-listfoot');
    if (foot) foot.textContent = list.length ? t('pur-list-count', { n: String(list.length) }) : '';
    bindRows();
    updateBulk();
}

function setChip(c: Chip): void {
    chip = c;
    document.querySelectorAll<HTMLElement>('#pur-seg .o').forEach((el) => {
        el.classList.toggle('on', el.dataset.chip === c);
    });
    renderBody();
}

function updateBulk(): void {
    const bar = document.getElementById('pur-bulkbar');
    const n = document.getElementById('pur-bulk-n');
    if (n) n.textContent = String(selected.size);
    if (bar) bar.classList.toggle('show', selected.size > 0);
}

function bindRows(): void {
    document.querySelectorAll<HTMLElement>('#pur-body [data-id]').forEach((el) => {
        el.onclick = () => {
            const id = el.dataset.id!;
            if (el.dataset.status === 'draft') window.openPurchaseForm?.(id);
            else window.openPurchaseDetail?.(id);
        };
    });
    document.querySelectorAll<HTMLElement>('#pur-body [data-pick]').forEach((el) => {
        el.onclick = (e) => {
            e.stopPropagation();
            const id = el.dataset.pick!;
            if (selected.has(id)) selected.delete(id);
            else selected.add(id);
            el.classList.toggle('on', selected.has(id));
            syncGroupChecks();
            updateBulk();
        };
    });
    document.querySelectorAll<HTMLElement>('#pur-body [data-grpchk]').forEach((el) => {
        el.onclick = (e) => {
            e.stopPropagation();
            const grp = el.closest('.monthgrp')!;
            const ids = Array.from(grp.querySelectorAll<HTMLElement>('[data-pick]')).map(
                (r) => r.dataset.pick!
            );
            const turnOn = !ids.every((id) => selected.has(id));
            ids.forEach((id) => (turnOn ? selected.add(id) : selected.delete(id)));
            grp.querySelectorAll<HTMLElement>('[data-pick]').forEach((r) =>
                r.classList.toggle('on', turnOn)
            );
            el.classList.toggle('on', turnOn);
            updateBulk();
        };
    });
    document.querySelectorAll<HTMLElement>('#pur-body [data-grphead]').forEach((el) => {
        el.onclick = (e) => {
            if ((e.target as HTMLElement).closest('[data-grpchk]')) return;
            el.closest('.monthgrp')!.classList.toggle('collapsed');
        };
    });
}

function syncGroupChecks(): void {
    document.querySelectorAll<HTMLElement>('#pur-body .monthgrp').forEach((grp) => {
        const ids = Array.from(grp.querySelectorAll<HTMLElement>('[data-pick]')).map(
            (r) => r.dataset.pick!
        );
        const all = ids.length > 0 && ids.every((id) => selected.has(id));
        grp.querySelector<HTMLElement>('[data-grpchk]')?.classList.toggle('on', all);
    });
}

async function bulkDelete(): Promise<void> {
    if (!selected.size) return;
    if (!window.confirm(t('pur-bulk-confirm', { n: String(selected.size) }))) return;
    const ws = activeWsId();
    const ids = Array.from(selected);
    const q = ws != null ? '?workspace_client_id=' + ws : '';
    try {
        await Promise.all(ids.map((id) => papi('DELETE', `/api/purchase/docs/${id}${q}`)));
        showToast(t('pur-bulk-deleted', { n: String(ids.length) }), 'success');
        selected.clear();
        load();
    } catch (e) {
        showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
        load();
    }
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
    const exportBtn = document.getElementById('pur-export-btn');
    if (exportBtn)
        exportBtn.onclick = () =>
            window.openPurchaseExport
                ? window.openPurchaseExport()
                : showToast(t('nav-soon'), 'info');
    // 主操作:记一笔采购 → 采集屏(草稿 s-capture · 桌面上传/手工 · 手机拍照/相册/文件/手工)。
    const recordBtn = document.getElementById('pur-record-btn');
    if (recordBtn) recordBtn.onclick = () => window.routeTo?.('purchase-capture');
    const lineBtn = document.getElementById('pur-line-btn');
    if (lineBtn) lineBtn.onclick = () => window.openPurchaseLine?.();
    const bulkDel = document.getElementById('pur-bulk-del');
    if (bulkDel) bulkDel.onclick = bulkDelete;
}

function showState(html: string): void {
    const body = document.getElementById('pur-body');
    if (body) body.innerHTML = `<div class="state">${html}</div>`;
}

async function load(): Promise<void> {
    showState(escapeHtml(t('pur-loading')));
    const ws = activeWsId();
    try {
        const range = dateRangeParams();
        const qs: string[] = [];
        if (ws != null) qs.push('workspace_client_id=' + ws);
        if (keyword.trim()) qs.push('q=' + encodeURIComponent(keyword.trim()));
        if (range.date_from) qs.push('date_from=' + range.date_from);
        if (range.date_to) qs.push('date_to=' + range.date_to);
        const params = qs.length ? '?' + qs.join('&') : '';
        const [data, catRes] = await Promise.all([
            papi('GET', '/api/purchase/docs' + params) as Promise<{
                docs?: Record<string, unknown>[];
                summary?: Record<string, unknown>;
            }>,
            cats.length
                ? Promise.resolve({ categories: cats })
                : (papi('GET', '/api/purchase/categories').catch(() => ({
                      categories: [],
                  })) as Promise<{
                      categories?: Category[];
                  }>),
        ]);
        allDocs = (data.docs || []).map(normListItem);
        summary = data.summary ? normSummary(data.summary) : null;
        cats = catRes.categories || cats;
        renderFilterbar();
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
    injectStyle('pur-list-css', PURCHASE_LIST_CSS);
    selected.clear();
    sec.innerHTML = shell();
    bindChrome();
    load();
};
