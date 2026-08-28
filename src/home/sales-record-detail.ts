/* global t, escapeHtml, showToast */
import { PURCHASE_DETAIL_CSS } from './purchase-detail-css.js';
import { injectPurBase, injectStyle } from './purchase-common.js';
import { type SalesDoc, type SalesLine, fmtMoney, salesFetch } from './sales-common.js';
import { fetchErpEndpoints, pickDefaultTarget, pushHistory } from './dms-intake-erp-push.js';
import { BAHT } from './money.js';
import { SALES_RECORD_DETAIL_CSS } from './sales-record-detail-css.js';

let pendingId: string | null = null;
let current: SalesDoc | null = null;
let originalUrl = '';

const ICON = {
    info: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/></svg>',
    list: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r="1.3"/><circle cx="4.5" cy="12" r="1.3"/><circle cx="4.5" cy="18" r="1.3"/></svg>',
    money: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 7v10M9.5 9.5h3.2a1.8 1.8 0 010 3.6H9.5"/></svg>',
    pay: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 10h18"/></svg>',
    clock: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
    original:
        '<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2z"/><path d="M8 8h8M8 12h8"/></svg>',
};

function kindOf(doc: SalesDoc): 'goods' | 'service' | 'mixed' {
    const kinds = new Set((doc.lines || []).map((line) => line.item_type || 'goods'));
    if (kinds.has('goods') && kinds.has('service')) return 'mixed';
    return kinds.has('service') ? 'service' : 'goods';
}

function sourceKey(doc: SalesDoc): string {
    if (doc.source === 'line_erp') return 'sr-source-line';
    if (doc.source === 'erp_web') return 'sr-source-web';
    return 'sr-source-legacy';
}

function payState(doc: SalesDoc): string {
    const value = doc.payment?.status || 'unpaid';
    return ['paid', 'partial'].includes(value) ? value : 'unpaid';
}

function statusBadge(doc: SalesDoc): string {
    const key = doc.status === 'void' ? 'srd-status-void' : 'srd-status-posted';
    const cls = doc.status === 'void' ? 'void' : 'success';
    return `<span class="badge ${cls}">${escapeHtml(t(key))}</span>`;
}

function field(label: string, value: string): string {
    return `<div class="f"><div class="l">${escapeHtml(label)}</div><div class="v">${value}</div></div>`;
}

function summary(doc: SalesDoc): string {
    const values = [
        [t('srd-buyer'), escapeHtml(doc.buyer?.name || '—'), ''],
        [t('srd-date'), escapeHtml(doc.issue_date || '—'), ''],
        [t('srd-classification'), escapeHtml(t('sr-kind-' + kindOf(doc))), ''],
        [t('srd-grand'), BAHT + fmtMoney(doc.grand_total), 'total'],
    ];
    return `<section class="summary">${values.map(([label, value, cls]) => `<div class="si"><div class="eyebrow">${escapeHtml(label)}</div><div class="sv ${cls}">${value}</div></div>`).join('')}</section>`;
}

function originalCard(doc: SalesDoc): string {
    const disabled = doc.ocr_history_id ? '' : ' disabled';
    return `<article class="card"><div class="hd"><div class="ct"><span class="ico">${ICON.info}</span>${escapeHtml(t('srd-original'))}</div></div>
        <div class="bd" style="padding:14px"><div class="img" id="srd-original-img">${ICON.original}</div>
        <button class="btn view-btn" id="srd-zoom"${disabled}>${escapeHtml(t('pur-zoom'))}</button></div>
        <div class="original-note">${escapeHtml(t(doc.ocr_history_id ? 'srd-original-note' : 'srd-original-missing'))}</div></article>`;
}

function infoCard(doc: SalesDoc): string {
    const buyer = doc.buyer || {};
    const kind = `<span class="kind-label">${escapeHtml(t('sr-kind-' + kindOf(doc)))}</span>`;
    return `<article class="card"><div class="hd"><div class="ct"><span class="ico">${ICON.info}</span>${escapeHtml(t('srd-info'))}</div></div><dl class="meta">
        ${field(t('srd-buyer'), escapeHtml(buyer.name || '—'))}
        ${field(t('srd-tax-id'), escapeHtml(buyer.tax_id || '—'))}
        ${field(t('srd-address'), escapeHtml(buyer.address || '—'))}
        ${field(t('srd-doc-no'), escapeHtml(doc.doc_number || '—'))}
        ${field(t('srd-date'), escapeHtml(doc.issue_date || '—'))}
        ${field(t('srd-due'), escapeHtml(doc.due_date || '—'))}
        ${field(t('srd-source'), `<span class="badge neutral">${escapeHtml(t(sourceKey(doc)))}</span>`)}
        ${field(t('srd-classification'), kind)}
    </dl></article>`;
}

function lineRow(line: SalesLine, index: number): string {
    const qty = Number(line.qty || 0);
    const unit = Number(line.unit_price || line.amount || 0);
    const total = line.line_total == null ? qty * unit : Number(line.line_total);
    const kind = line.item_type === 'service' ? 'service' : 'goods';
    return `<tr><td>${index + 1}</td><td><span class="pname">${escapeHtml(line.description || '—')}</span></td>
        <td><span class="kind-label">${escapeHtml(t('sr-kind-' + kind))}</span></td>
        <td class="num">${escapeHtml(String(line.qty || '—'))}</td><td class="num">${fmtMoney(unit)}</td><td class="num">${fmtMoney(total)}</td></tr>`;
}

function itemsCard(doc: SalesDoc): string {
    return `<article class="card"><div class="hd"><div class="ct"><span class="ico">${ICON.list}</span>${escapeHtml(t('srd-items'))}</div><span class="muted">${doc.lines.length} ${escapeHtml(t('pur-unit-rows'))}</span></div>
        <div class="table-wrap"><table><thead><tr><th>${escapeHtml(t('pur-seq'))}</th><th>${escapeHtml(t('pur-line-name'))}</th><th>${escapeHtml(t('srd-item-type'))}</th><th class="num">${escapeHtml(t('pur-qty'))}</th><th class="num">${escapeHtml(t('pur-price'))}</th><th class="num">${escapeHtml(t('pur-line-total'))}</th></tr></thead>
        <tbody>${doc.lines.map(lineRow).join('')}</tbody></table></div></article>`;
}

function amountCard(doc: SalesDoc): string {
    return `<article class="card"><div class="hd"><div class="ct"><span class="ico">${ICON.money}</span>${escapeHtml(t('pur-amount'))}</div></div><div class="mlist">
        <div class="mrow"><span>${escapeHtml(t('pur-subtotal-ex'))}</span><strong>${BAHT}${fmtMoney(doc.subtotal)}</strong></div>
        <div class="mrow tax"><span>${escapeHtml(t('srd-output-vat'))}</span><strong>${BAHT}${fmtMoney(doc.vat_amount)}</strong></div>
        <div class="mrow total"><span>${escapeHtml(t('srd-grand'))}</span><strong>${BAHT}${fmtMoney(doc.grand_total)}</strong></div></div></article>`;
}

function paymentCard(doc: SalesDoc): string {
    const paid = Number(doc.payment?.paid_amount || 0);
    const due = Math.max(0, Number(doc.grand_total || 0) - paid);
    const status = payState(doc);
    return `<article class="card"><div class="hd"><div class="ct"><span class="ico">${ICON.pay}</span>${escapeHtml(t('pur-payment'))}</div><span class="badge ${status}">${escapeHtml(t('sx-pay-' + status))}</span></div><div class="mlist">
        <div class="mrow"><span>${escapeHtml(t('srd-received'))}</span><strong>${BAHT}${fmtMoney(paid)}</strong></div>
        <div class="mrow unpaid"><span>${escapeHtml(t('srd-outstanding'))}</span><strong>${BAHT}${fmtMoney(due)}</strong></div></div></article>`;
}

function timelineCard(doc: SalesDoc): string {
    const steps = [t('srd-step-created'), t('srd-step-confirmed')];
    if (payState(doc) === 'paid') steps.push(t('srd-step-paid'));
    if (doc.status === 'void') steps.push(t('srd-status-void'));
    return `<article class="card"><div class="hd"><div class="ct"><span class="ico">${ICON.clock}</span>${escapeHtml(t('pur-timeline'))}</div></div><div class="timeline">${steps.map((title) => `<div class="step"><span class="dot ok"></span><div><div class="st">${escapeHtml(title)}</div></div></div>`).join('')}</div></article>`;
}

function pushCard(doc: SalesDoc): string {
    const status = doc.push_status || 'not_pushed';
    const disabled = !doc.ocr_history_id || status === 'success' ? ' disabled' : '';
    return `<div class="pushbox"><div class="row"><span>${escapeHtml(t('srd-erp-status'))}</span><strong>${escapeHtml(t('sr-push-' + status))}</strong></div>
        <button class="btn primary" id="srd-push"${disabled}>${escapeHtml(t('sr-push-' + status))}</button></div>`;
}

function shell(doc: SalesDoc): string {
    const voidButton =
        doc.status === 'void'
            ? ''
            : `<button class="btn danger" id="srd-void">${escapeHtml(t('pur-void'))}</button>`;
    return `<div class="pur d srd ${doc.status === 'void' ? 'voided' : ''}"><div class="wrap"><header class="ph"><div class="phl"><span class="back" id="srd-back">‹</span><div><div class="t">${escapeHtml(t('srd-title'))} ${statusBadge(doc)}</div><div class="crumb">${escapeHtml(t('pur-crumb-home'))} <i>/</i> ${escapeHtml(t('sx-records-title'))} <i>/</i> ${escapeHtml(t('srd-title'))}</div></div></div></header>
        ${summary(doc)}<div class="sheet"><aside class="preview-pane">${originalCard(doc)}${timelineCard(doc)}${pushCard(doc)}</aside>
        <section class="form-pane"><div class="scroll"><section class="section">${infoCard(doc)}</section><section class="section">${itemsCard(doc)}</section><section class="section">${amountCard(doc)}</section><section class="section">${paymentCard(doc)}</section></div>
        ${voidButton ? `<div class="editfoot">${voidButton}</div>` : ''}</section></div></div></div>`;
}

async function loadOriginal(): Promise<void> {
    originalUrl = '';
    const box = document.getElementById('srd-original-img');
    if (!box || !current?.ocr_history_id) return;
    const response = await salesFetch(`/api/history/${current.ocr_history_id}/page/1.png`);
    if (!response.ok) return;
    originalUrl = URL.createObjectURL(await response.blob());
    box.innerHTML = `<img src="${originalUrl}" alt="">`;
    box.classList.add('has-img');
}

function openOriginal(): void {
    if (!originalUrl) return;
    const overlay = document.createElement('div');
    overlay.className = 'pur-lightbox';
    overlay.innerHTML = `<img src="${originalUrl}" alt="">`;
    overlay.onclick = () => overlay.remove();
    document.body.appendChild(overlay);
}

async function pushToErp(): Promise<void> {
    if (!current?.ocr_history_id) return;
    const target = pickDefaultTarget(await fetchErpEndpoints(), '');
    if (!target) return showToast(t('sr-no-endpoint'), 'error');
    const outcome = await pushHistory(current.ocr_history_id, target);
    showToast(t('sr-push-result-' + outcome), outcome === 'failed' ? 'error' : 'success');
    await load(current.id);
}

async function voidRecord(): Promise<void> {
    if (!current) return;
    if (
        typeof window.showConfirm === 'function' &&
        !(await window.showConfirm(t('srd-void-confirm')))
    )
        return;
    const response = await salesFetch(`/api/sales/documents/${current.id}/void`, {
        method: 'POST',
    });
    if (!response.ok) return showToast(t('srd-action-failed'), 'error');
    showToast(t('srd-void-ok'), 'success');
    await load(current.id);
}

function bind(): void {
    const root = document.getElementById('page-sales-record-detail');
    root?.querySelector<HTMLElement>('#srd-back')?.addEventListener('click', () =>
        window.routeTo?.('sales-records')
    );
    root?.querySelector<HTMLElement>('#srd-original-img')?.addEventListener('click', openOriginal);
    root?.querySelector<HTMLElement>('#srd-zoom')?.addEventListener('click', openOriginal);
    root?.querySelector<HTMLElement>('#srd-push')?.addEventListener(
        'click',
        () => void pushToErp()
    );
    root?.querySelector<HTMLElement>('#srd-void')?.addEventListener(
        'click',
        () => void voidRecord()
    );
}

async function load(id: string): Promise<void> {
    const root = document.getElementById('page-sales-record-detail');
    if (root)
        root.innerHTML = `<div class="pur d srd"><div class="state">${escapeHtml(t('pur-loading'))}</div></div>`;
    try {
        const response = await salesFetch(`/api/sales/documents/${id}`);
        const body = await response.json();
        if (!response.ok || !body.document) throw new Error('load');
        current = body.document as SalesDoc;
        if (root) root.innerHTML = shell(current);
        bind();
        await loadOriginal();
    } catch (_) {
        if (root)
            root.innerHTML = `<div class="pur d srd"><div class="state">${escapeHtml(t('srd-load-failed'))}</div></div>`;
    }
}

window.openSalesRecordDetail = (docId: string) => {
    pendingId = docId;
    window.routeTo?.('sales-record-detail');
};

window.loadSalesRecordDetail = () => {
    injectPurBase();
    injectStyle('pur-detail-css', PURCHASE_DETAIL_CSS);
    injectStyle('sales-record-detail-css', SALES_RECORD_DETAIL_CSS);
    if (!pendingId) return window.routeTo?.('sales-records');
    void load(pendingId);
};
