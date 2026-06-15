// 商户采购 · 屏6 单据详情 · 布局照搬原型 pearnly_invoice_detail_preview
// (顶栏面包屑 + 摘要条 + 左主右栏 360 + 逐行税率税额 + 诚实时间线)。
// 右上动作:保留现有 作废/记付款(草稿=编辑)+ 新增 打印;不加复制/导出。
// 处理记录按真实 status/payment_status 诚实推导(无审计轨迹 · 不编造人名/时间)。
// 费用单(无 VAT)隐藏品项/进项税段;已作废 = 灰态 + 回冲提示。四态。
/* global t, escapeHtml, showToast */
import {
    papi,
    openPurchasePdf,
    purchaseErrMsg,
    activeWsId,
    fmtMoney,
    fmtQty,
    srcLabelKey,
    kindLabelKey,
    normDetail,
    fetchAuthedBlobUrl,
    injectPurBase,
    injectStyle,
    type DocDetail,
    type DocLine,
} from './purchase-common.js';
import { PURCHASE_DETAIL_CSS } from './purchase-detail-css.js';

let pendingId: string | null = null;
let cur: DocDetail | null = null;
let billBlobUrl = '';

const ICON = {
    info: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="4" y="3" width="16" height="18" rx="2"/><line x1="8" y1="8" x2="16" y2="8"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="8" y1="16" x2="13" y2="16"/></svg>',
    list: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><line x1="9" y1="6" x2="20" y2="6"/><line x1="9" y1="12" x2="20" y2="12"/><line x1="9" y1="18" x2="20" y2="18"/><circle cx="4.5" cy="6" r="1.3"/><circle cx="4.5" cy="12" r="1.3"/><circle cx="4.5" cy="18" r="1.3"/></svg>',
    money: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 7v10M9.5 9.5h3.2a1.8 1.8 0 010 3.6H9.5M9.5 14.5h4"/></svg>',
    pay: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="6" width="18" height="12" rx="2"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
    bill: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/></svg>',
    clock: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
    docPlaceholder:
        '<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2z"/><line x1="8" y1="8" x2="16" y2="8"/><line x1="8" y1="12" x2="16" y2="12"/></svg>',
};

function field(label: string, value: string, cls = ''): string {
    return `<div class="f"><div class="l">${escapeHtml(label)}</div><div class="v ${cls}">${value}</div></div>`;
}

function statusBadges(d: DocDetail): string {
    if (d.status === 'void')
        return `<span class="badge void">${escapeHtml(t('pur-status-void'))}</span>`;
    if (d.status === 'draft')
        return `<span class="badge warning">${escapeHtml(t('pur-status-draft'))}</span>`;
    const review = `<span class="badge success">${escapeHtml(t('pur-status-posted'))}</span>`;
    const pay = `<span class="badge ${d.payment_status}">${escapeHtml(t('pur-pay-' + d.payment_status))}</span>`;
    return review + pay;
}

function summaryStrip(d: DocDetail): string {
    const items: [string, string, string][] = [
        [t('pur-supplier'), escapeHtml((d.supplier && d.supplier.name) || '—'), ''],
        [t('pur-doc-date'), escapeHtml(d.doc_date || '—'), ''],
        [t('pur-type'), escapeHtml(t(kindLabelKey(d.doc_kind))), ''],
        [t('pur-grand'), '฿' + fmtMoney(d.grand_total), 'total'],
    ];
    return `<section class="summary">${items
        .map(
            ([l, v, c]) =>
                `<div class="si"><div class="eyebrow">${escapeHtml(l)}</div><div class="sv ${c}" title="${v}">${v}</div></div>`
        )
        .join('')}</section>`;
}

function infoCard(d: DocDetail): string {
    const batch = d.doc_date
        ? `${escapeHtml(d.doc_date.slice(0, 7))} · ${escapeHtml(t(kindLabelKey(d.doc_kind)))}`
        : '—';
    const fx = `${escapeHtml(d.currency || 'THB')} / 1.0000`;
    return `<article class="card"><div class="hd"><div class="ct"><span class="ico">${ICON.info}</span>${escapeHtml(t('pur-doc-info'))}</div><span class="badge neutral">${escapeHtml(t('pur-readonly'))}</span></div>
        <dl class="meta">
            ${field(t('pur-supplier'), escapeHtml((d.supplier && d.supplier.name) || '—'))}
            ${field(t('pur-tax-id'), escapeHtml((d.supplier && d.supplier.tax_id) || '—'), 'tnum')}
            ${field(t('pur-doc-no'), escapeHtml(d.doc_no || '—'))}
            ${field(t('pur-type'), `<span class="badge purple">${escapeHtml(t(kindLabelKey(d.doc_kind)))}</span>`)}
            ${field(t('pur-doc-date'), escapeHtml(d.doc_date || '—'), 'tnum')}
            ${field(t('pur-currency-fx'), fx)}
            ${field(t('pur-col-source'), `<span class="badge neutral">${escapeHtml(t(srcLabelKey(d.source)))}</span>`)}
            ${field(t('pur-batch'), batch)}
        </dl></article>`;
}

function lineRow(l: DocLine, i: number, hasVat: boolean): string {
    const tag = l.product_matched
        ? `<span class="pill ok">${escapeHtml(t('pur-matched'))}</span>`
        : `<span class="pill warn" data-match="1">${escapeHtml(t('pur-match'))}</span>`;
    const net = Number(l.qty) * Number(l.unit_price) - Number(l.discount || 0);
    const rate = Number(l.vat_rate) || 0;
    const tax = hasVat ? (net * rate) / 100 : 0;
    return `<tr>
        <td>${i + 1}</td>
        <td><span class="pname">${escapeHtml(l.description)}</span>${tag}</td>
        <td class="num">${rate}%</td>
        <td class="num">${fmtQty(l.qty)}</td>
        <td class="num">${fmtMoney(l.unit_price)}</td>
        <td class="num">${fmtMoney(net)}</td>
        <td class="num">${fmtMoney(tax)}</td>
    </tr>`;
}

function itemsCard(d: DocDetail): string {
    if (d.doc_kind === 'expense' && !d.has_vat) return '';
    return `<article class="card"><div class="hd"><div class="ct"><span class="ico">${ICON.list}</span>${escapeHtml(t('pur-items'))}</div><span class="muted">${d.lines.length} ${escapeHtml(t('pur-unit-rows'))}</span></div>
        <div class="table-wrap"><table><thead><tr>
            <th style="width:56px">${escapeHtml(t('pur-seq'))}</th>
            <th>${escapeHtml(t('pur-line-name'))}</th>
            <th class="num">${escapeHtml(t('pur-vat-rate'))}</th>
            <th class="num">${escapeHtml(t('pur-qty'))}</th>
            <th class="num">${escapeHtml(t('pur-price'))}</th>
            <th class="num">${escapeHtml(t('pur-line-total'))}</th>
            <th class="num">${escapeHtml(t('pur-tax-amt'))}</th>
        </tr></thead><tbody>${d.lines.map((l, i) => lineRow(l, i, d.has_vat)).join('')}</tbody></table></div></article>`;
}

function amountCard(d: DocDetail): string {
    if (d.doc_kind === 'expense' && !d.has_vat) {
        return `<article class="card"><div class="hd"><div class="ct"><span class="ico">${ICON.money}</span>${escapeHtml(t('pur-amount'))}</div></div>
            <div class="mlist"><div class="mrow total"><span>${escapeHtml(t('pur-grand'))}</span><strong>฿${fmtMoney(d.grand_total)}</strong></div></div></article>`;
    }
    const wht =
        d.wht_amount > 0
            ? `<div class="mrow"><span>${escapeHtml(t('pur-wht'))}</span><strong>−฿${fmtMoney(d.wht_amount)}</strong></div>`
            : '';
    return `<article class="card"><div class="hd"><div class="ct"><span class="ico">${ICON.money}</span>${escapeHtml(t('pur-amount'))}</div></div>
        <div class="mlist">
            <div class="mrow"><span>${escapeHtml(t('pur-subtotal-ex'))}</span><strong>฿${fmtMoney(d.subtotal)}</strong></div>
            <div class="mrow tax"><span>${escapeHtml(t('pur-vat-in'))} <span class="pill ok">${escapeHtml(t('pur-creditable'))}</span></span><strong>฿${fmtMoney(d.vat_amount)}</strong></div>
            ${wht}
            <div class="mrow total"><span>${escapeHtml(t('pur-grand'))}</span><strong>฿${fmtMoney(d.grand_total)}</strong></div>
        </div></article>`;
}

function payCard(d: DocDetail): string {
    const due = d.net_payable - d.paid_amount;
    const pst = d.status === 'void' ? 'void' : d.payment_status;
    return `<article class="card"><div class="hd"><div class="ct"><span class="ico">${ICON.pay}</span>${escapeHtml(t('pur-payment'))}</div><span class="badge ${pst}">${escapeHtml(t(d.status === 'void' ? 'pur-status-void' : 'pur-pay-' + d.payment_status))}</span></div>
        <div class="mlist">
            <div class="mrow"><span>${escapeHtml(t('pur-payable'))}</span><strong>฿${fmtMoney(d.net_payable)}</strong></div>
            <div class="mrow"><span>${escapeHtml(t('pur-paid'))}</span><strong>฿${fmtMoney(d.paid_amount)}</strong></div>
            <div class="mrow unpaid"><span>${escapeHtml(t('pur-due-balance'))}</span><strong>฿${fmtMoney(due)}</strong></div>
        </div></article>`;
}

function billCard(d: DocDetail): string {
    return `<article class="card"><div class="hd"><div class="ct"><span class="ico">${ICON.bill}</span>${escapeHtml(t('pur-bill'))}</div></div>
        <div class="bd" style="padding:14px;">
            <div class="img" id="pur-bill-img">${ICON.docPlaceholder}</div>
            <button class="btn view-btn" id="pur-zoom"${d.bill_image_url ? '' : ' disabled'}>${escapeHtml(t('pur-zoom'))}</button>
        </div></article>`;
}

// 处理记录:无审计轨迹 → 按真实 status/payment_status 诚实推导(不编人名/时间戳)。
function timelineCard(d: DocDetail): string {
    type Step = { title: string; dot: string };
    const steps: Step[] = [{ title: t('pur-step-created'), dot: 'ok' }];
    if (d.status === 'void') {
        steps.push({ title: t('pur-step-posted'), dot: 'ok' });
        steps.push({ title: t('pur-status-void'), dot: 'void' });
    } else {
        steps.push({ title: t('pur-step-posted'), dot: d.status === 'posted' ? 'ok' : 'active' });
        const pdot =
            d.payment_status === 'paid' ? 'ok' : d.payment_status === 'partial' ? 'active' : '';
        steps.push({ title: t('pur-step-paid'), dot: pdot });
    }
    const rows = steps
        .map(
            (s) =>
                `<div class="step"><span class="dot ${s.dot}"></span><div><div class="st">${escapeHtml(s.title)}</div></div></div>`
        )
        .join('');
    return `<article class="card"><div class="hd"><div class="ct"><span class="ico">${ICON.clock}</span>${escapeHtml(t('pur-timeline'))}</div></div>
        <div class="timeline">${rows}</div>
        <div class="note">${escapeHtml(t('pur-detail-note'))}</div></article>`;
}

// 凭证 surface:无原始票据 → 生成替代收据;WHT>0 → 生成扣缴凭证;已生成可下载。已作废不显。
function voucherCard(d: DocDetail): string {
    if (d.status === 'void') return '';
    const hasSub = d.attachments.some((a) => a.kind === 'substitute_receipt');
    const hasWht = d.attachments.some((a) => a.kind === 'wht_cert');
    const rows: string[] = [];
    if (hasSub)
        rows.push(
            `<button class="btn" data-dl="substitute_receipt">${escapeHtml(t('pur-dl-substitute'))}</button>`
        );
    if (hasWht)
        rows.push(`<button class="btn" data-dl="wht_cert">${escapeHtml(t('pur-dl-wht'))}</button>`);
    if (!d.bill_image_url && !hasSub)
        rows.push(
            `<button class="btn" data-gen="substitute_receipt">${escapeHtml(t('pur-gen-substitute'))}</button>`
        );
    if (d.wht_amount > 0 && !hasWht)
        rows.push(
            `<button class="btn" data-gen="wht_cert">${escapeHtml(t('pur-gen-wht'))}</button>`
        );
    if (!rows.length) return '';
    return `<article class="card"><div class="hd"><div class="ct">${escapeHtml(t('pur-voucher'))}</div></div><div class="vch">${rows.join('')}</div></article>`;
}

function actions(d: DocDetail): string {
    if (d.status === 'void') return '';
    if (d.status === 'draft')
        return `<button class="btn" id="pur-edit-btn">${escapeHtml(t('pur-edit'))}</button>`;
    return `<button class="btn danger" id="pur-void-btn">${escapeHtml(t('pur-void'))}</button><button class="btn primary" id="pur-pay-btn2"${d.payment_status === 'paid' ? ' disabled' : ''}>${escapeHtml(t('pur-pay'))}</button>`;
}

function shell(d: DocDetail): string {
    const stock =
        d.stock_applied && d.doc_kind !== 'expense'
            ? `<div class="stocknote">✓ ${escapeHtml(t('pur-stock-applied'))}</div>`
            : '';
    const voidNote =
        d.status === 'void' ? `<div class="stocknote">${escapeHtml(t('pur-void-note'))}</div>` : '';
    return `<div class="pur d ${d.status === 'void' ? 'voided' : ''}"><div class="wrap">
        <header class="ph">
            <div class="phl"><span class="back" id="pur-back" title="${escapeHtml(t('pur-back'))}" aria-label="${escapeHtml(t('pur-back'))}">‹</span>
            <div><div class="t">${escapeHtml(t('pur-detail-title'))} ${statusBadges(d)}</div>
            <div class="crumb">${escapeHtml(t('pur-crumb-home'))} <i>/</i> ${escapeHtml(t('pur-crumb-list'))} <i>/</i> ${escapeHtml(t('pur-detail-title'))}</div></div></div>
            <div class="acts">${actions(d)}</div>
        </header>
        ${summaryStrip(d)}
        <div class="grid">
            <div class="col">
                ${infoCard(d)}
                ${itemsCard(d)}
                <div class="bottom">${amountCard(d)}${payCard(d)}</div>
            </div>
            <aside class="side">
                ${billCard(d)}
                ${voucherCard(d)}
                ${timelineCard(d)}
                ${stock}${voidNote}
            </aside>
        </div>
    </div></div>`;
}

// 票图是鉴权端点 · 不能直接塞 <img src> 否则 401 破图 · 先占位 svg 再带令牌取 blob 换上。
async function loadBillImage(): Promise<void> {
    billBlobUrl = '';
    const url = cur && cur.bill_image_url;
    const box = document.getElementById('pur-bill-img');
    if (!url || !box) return;
    try {
        billBlobUrl = await fetchAuthedBlobUrl(url);
        box.innerHTML = `<img src="${billBlobUrl}" alt="">`;
    } catch (_) {
        /* 取图失败 → 保留占位 svg · 放大按钮已 disabled */
    }
}

function openLightbox(): void {
    if (!billBlobUrl) return;
    const ov = document.createElement('div');
    ov.className = 'pur-lightbox';
    ov.innerHTML = `<img src="${billBlobUrl}" alt="">`;
    ov.onclick = () => ov.remove();
    document.body.appendChild(ov);
}

function bind(): void {
    document.getElementById('pur-back')!.onclick = () => window.routeTo?.('purchase');
    const zoom = document.getElementById('pur-zoom');
    if (zoom) zoom.onclick = openLightbox;
    const edit = document.getElementById('pur-edit-btn');
    if (edit) edit.onclick = () => window.openPurchaseForm?.(cur!.id);
    const pay2 = document.getElementById('pur-pay-btn2');
    if (pay2) pay2.onclick = () => window.openPurchasePay?.(cur, () => load(cur!.id));
    const voidBtn = document.getElementById('pur-void-btn');
    if (voidBtn) voidBtn.onclick = doVoid;
    document.querySelectorAll<HTMLElement>('[data-match]').forEach((el) => {
        el.onclick = () => window.openPurchaseMatch?.({}, () => load(cur!.id));
    });
    document.querySelectorAll<HTMLElement>('[data-gen]').forEach((el) => {
        el.onclick = () => genCredential(el.dataset.gen as string);
    });
    document.querySelectorAll<HTMLElement>('[data-dl]').forEach((el) => {
        el.onclick = () => downloadDoc(el.dataset.dl as string);
    });
}

async function genCredential(kind: string): Promise<void> {
    const path = kind === 'wht_cert' ? 'wht-cert' : 'substitute-receipt';
    try {
        await papi('POST', `/api/purchase/docs/${cur!.id}/${path}`, {
            workspace_client_id: activeWsId(),
        });
        showToast(t('pur-gen-ok'), 'success');
        load(cur!.id);
    } catch (e) {
        showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
    }
}

async function downloadDoc(kind: string): Promise<void> {
    const ws = activeWsId();
    const q = ws != null ? `&workspace_client_id=${ws}` : '';
    try {
        await openPurchasePdf(`/api/purchase/docs/${cur!.id}/document.pdf?kind=${kind}${q}`);
    } catch (e) {
        showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
    }
}

async function doVoid(): Promise<void> {
    if (typeof window.showConfirm === 'function') {
        const okc = await window.showConfirm(t('pur-void-confirm'));
        if (!okc) return;
    }
    try {
        await papi('POST', `/api/purchase/docs/${cur!.id}/void`, {});
        showToast(t(cur!.stock_applied ? 'pur-void-ok-stock' : 'pur-void-ok'), 'success');
        load(cur!.id);
    } catch (e) {
        showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
    }
}

function showState(html: string): void {
    const sec = document.getElementById('page-purchase-detail');
    if (sec)
        sec.innerHTML = `<div class="pur d"><div class="wrap"><div class="state">${html}</div></div></div>`;
}

async function load(id: string): Promise<void> {
    showState(escapeHtml(t('pur-loading')));
    try {
        cur = normDetail(
            (await papi('GET', `/api/purchase/docs/${id}`)) as Record<string, unknown>
        );
        const sec = document.getElementById('page-purchase-detail');
        if (sec) sec.innerHTML = shell(cur);
        bind();
        loadBillImage();
    } catch (e) {
        showState(
            `${escapeHtml(purchaseErrMsg(e, 'purchase.unexpected'))}<br><button class="btn" id="pur-retry">${escapeHtml(t('pur-retry'))}</button>`
        );
        const retry = document.getElementById('pur-retry');
        if (retry) retry.onclick = () => load(id);
    }
}

window.openPurchaseDetail = function (id) {
    pendingId = id;
    window.routeTo?.('purchase-detail');
};

window.loadPurchaseDetail = function () {
    injectPurBase();
    injectStyle('pur-detail-css', PURCHASE_DETAIL_CSS);
    if (!pendingId) {
        window.routeTo?.('purchase');
        return;
    }
    load(pendingId);
};
