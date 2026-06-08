// 商户采购 · 屏6 单据详情(主屏点 posted 行进来)· 照搬设计稿 06-单据详情。
// 桌面两栏(信息+品项 左 / 票图+金额+付款 右)/ 手机单列。记付款(屏7)/ 作废 / (草稿)编辑。
// 费用单(无 VAT)隐藏 进项税 / 品项 SKU 段;已作废 = 灰态 + 回冲提示。四态。
/* global t, escapeHtml, showToast */
import {
    papi,
    purchaseErrMsg,
    fmtMoney,
    fmtQty,
    srcLabelKey,
    kindLabelKey,
    normDetail,
    injectPurBase,
    injectStyle,
    type DocDetail,
    type DocLine,
} from './purchase-common.js';

let pendingId: string | null = null;
let cur: DocDetail | null = null;

const PAGE_CSS = `
.pur.d .wrap{max-width:1000px;}
.pur .back{display:inline-flex;align-items:center;gap:6px;color:var(--ink2);font-size:12.5px;margin-bottom:12px;cursor:pointer;}
.pur .ph{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:16px;}
.pur .ph .t{font-size:20px;font-weight:700;display:flex;align-items:center;gap:10px;}
.pur .ph .sub{color:var(--ink2);font-size:13px;margin-top:4px;}
.pur .acts{display:flex;gap:9px;flex-shrink:0;}
.pur .badge{font-size:11px;padding:2px 9px;border-radius:6px;}
.pur .badge.paid{background:#dcfce7;color:#15803d;} .pur .badge.unpaid{background:#fef3c7;color:#b45309;} .pur .badge.partial{background:#ffedd5;color:#c2410c;} .pur .badge.void{background:#f3f4f6;color:#6b7280;}
.pur .grid{display:grid;grid-template-columns:1fr 360px;gap:14px;align-items:start;}
.pur .col{display:flex;flex-direction:column;gap:14px;}
.pur .card .hd{padding:13px 16px;border-bottom:1px solid var(--line);font-weight:600;font-size:13px;display:flex;justify-content:space-between;align-items:center;}
.pur .card .hd .muted{color:var(--ink3);font-weight:400;}
.pur .card .bd{padding:14px 16px;}
.pur .meta{display:grid;grid-template-columns:1fr 1fr;gap:12px 18px;}
.pur .meta .f .l{color:var(--ink2);font-size:11.5px;}
.pur .meta .f .v{font-size:14px;margin-top:3px;font-weight:600;}
.pur .src{display:inline-flex;align-items:center;gap:5px;font-size:11px;padding:2px 8px;border-radius:6px;background:#eef2ff;color:#4338ca;}
.pur .src.line{background:#dcfce7;color:#15803d;}
.pur table{width:100%;border-collapse:collapse;}
.pur .card th{text-align:left;font-size:11.5px;color:var(--ink2);font-weight:600;padding:9px 0;border-bottom:1px solid var(--line);background:transparent;text-transform:none;letter-spacing:0;}
.pur .card td{padding:11px 0;border-bottom:1px solid #f4f4f0;font-size:13px;vertical-align:top;}
.pur .card tr:last-child td{border-bottom:0;}
.pur .pill{font-size:10.5px;padding:1px 7px;border-radius:5px;margin-left:6px;}
.pur .pill.ok{background:#dcfce7;color:#15803d;} .pur .pill.warn{background:#fef3c7;color:#b45309;cursor:pointer;}
.pur .sum{display:flex;justify-content:space-between;padding:7px 0;font-size:13px;}
.pur .sum.tot{border-top:1px solid var(--line);margin-top:6px;padding-top:11px;font-weight:800;font-size:15px;}
.pur .sum .tax{color:var(--green);}
.pur .pay{display:flex;justify-content:space-between;align-items:baseline;padding:6px 0;font-size:13px;}
.pur .pay .due{color:var(--amber);font-weight:700;}
.pur .img{aspect-ratio:3/4;background:#fafaf8;border:1px dashed var(--line);border-radius:10px;display:flex;align-items:center;justify-content:center;color:var(--ink3);margin-bottom:10px;overflow:hidden;}
.pur .img img{width:100%;height:100%;object-fit:cover;}
.pur .stocknote{margin-top:10px;font-size:12px;color:var(--ink2);background:#f0fdf4;border:1px solid #bbf7d0;border-radius:9px;padding:9px 11px;}
.pur.voided{opacity:.62;}
@media(max-width:600px){
  .pur .ph{flex-direction:column;} .pur .acts{width:100%;} .pur .acts .btn{flex:1;}
  .pur .grid{grid-template-columns:1fr;}
}
`;

const ICON_DOC =
    '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2z"/><line x1="8" y1="8" x2="16" y2="8"/><line x1="8" y1="12" x2="16" y2="12"/></svg>';

function lineRow(l: DocLine): string {
    // 仅商品行/进项票显品项 · 费用单(无 VAT)整段已隐藏(见 itemsCard),此处恒显配对标。
    const tag = l.product_matched
        ? `<span class="pill ok">${escapeHtml(t('pur-matched'))}</span>`
        : `<span class="pill warn" data-match="1">${escapeHtml(t('pur-unmatched'))} · ${escapeHtml(t('pur-match'))}</span>`;
    const total = Number(l.qty) * Number(l.unit_price) - Number(l.discount || 0);
    return `<tr><td>${escapeHtml(l.description)} ${tag}</td><td class="num">${fmtQty(l.qty)}</td><td class="num">${fmtMoney(l.unit_price)}</td><td class="num">฿${fmtMoney(total)}</td></tr>`;
}

function metaCard(d: DocDetail): string {
    const src = d.source === 'line' ? 'src line' : 'src';
    return `<div class="card"><div class="hd">${escapeHtml(t('pur-doc-info'))}</div><div class="bd meta">
        <div class="f"><div class="l">${escapeHtml(t('pur-supplier'))}</div><div class="v">${escapeHtml((d.supplier && d.supplier.name) || '—')}</div></div>
        <div class="f"><div class="l">${escapeHtml(t('pur-tax-id'))}</div><div class="v tnum">${escapeHtml((d.supplier && d.supplier.tax_id) || '—')}</div></div>
        <div class="f"><div class="l">${escapeHtml(t('pur-type'))}</div><div class="v">${escapeHtml(t(kindLabelKey(d.doc_kind)))}</div></div>
        <div class="f"><div class="l">${escapeHtml(t('pur-col-source'))}</div><div class="v"><span class="${src}">${escapeHtml(t(srcLabelKey(d.source)))}</span></div></div>
        <div class="f"><div class="l">${escapeHtml(t('pur-doc-date'))}</div><div class="v tnum">${escapeHtml(d.doc_date || '—')}</div></div>
        <div class="f"><div class="l">${escapeHtml(t('pur-due'))}</div><div class="v tnum">${escapeHtml(d.due_date || '—')}</div></div>
    </div></div>`;
}

function itemsCard(d: DocDetail): string {
    if (d.doc_kind === 'expense' && !d.has_vat) return '';
    return `<div class="card"><div class="hd">${escapeHtml(t('pur-items'))} <span class="muted">${d.lines.length} ${escapeHtml(t('pur-unit-rows'))}</span></div><div class="bd">
        <table><thead><tr><th>${escapeHtml(t('pur-line-name'))}</th><th class="num">${escapeHtml(t('pur-qty'))}</th><th class="num">${escapeHtml(t('pur-price'))}</th><th class="num">${escapeHtml(t('pur-line-total'))}</th></tr></thead>
        <tbody>${d.lines.map(lineRow).join('')}</tbody></table>
    </div></div>`;
}

function amountCard(d: DocDetail): string {
    if (d.doc_kind === 'expense' && !d.has_vat) {
        return `<div class="card"><div class="hd">${escapeHtml(t('pur-amount'))}</div><div class="bd">
            <div class="sum tot"><span>${escapeHtml(t('pur-grand'))}</span><span class="tnum">฿${fmtMoney(d.grand_total)}</span></div></div></div>`;
    }
    const wht =
        d.wht_amount > 0
            ? `<div class="sum"><span>${escapeHtml(t('pur-wht'))}</span><span class="tnum">−฿${fmtMoney(d.wht_amount)}</span></div>
        <div class="sum tot"><span>${escapeHtml(t('pur-net-payable'))}</span><span class="tnum">฿${fmtMoney(d.net_payable)}</span></div>`
            : '';
    return `<div class="card"><div class="hd">${escapeHtml(t('pur-amount'))}</div><div class="bd">
        <div class="sum"><span>${escapeHtml(t('pur-subtotal-ex'))}</span><span class="tnum">฿${fmtMoney(d.subtotal)}</span></div>
        <div class="sum"><span>${escapeHtml(t('pur-vat-in'))} <span class="pill ok">${escapeHtml(t('pur-creditable'))}</span></span><span class="tnum tax">฿${fmtMoney(d.vat_amount)}</span></div>
        <div class="sum tot"><span>${escapeHtml(t('pur-grand'))}</span><span class="tnum">฿${fmtMoney(d.grand_total)}</span></div>
        ${wht}
    </div></div>`;
}

function payCard(d: DocDetail): string {
    const due = d.net_payable - d.paid_amount;
    const btn =
        d.status === 'posted' && d.payment_status !== 'paid'
            ? `<button class="btn primary" id="pur-pay-btn" style="width:100%;margin-top:10px;">${escapeHtml(t('pur-pay'))}</button>`
            : '';
    return `<div class="card"><div class="hd">${escapeHtml(t('pur-payment'))}</div><div class="bd">
        <div class="pay"><span>${escapeHtml(t('pur-payable'))}</span><span class="tnum">฿${fmtMoney(d.net_payable)}</span></div>
        <div class="pay"><span>${escapeHtml(t('pur-paid'))}</span><span class="tnum">฿${fmtMoney(d.paid_amount)}</span></div>
        <div class="pay"><span>${escapeHtml(t('pur-due-balance'))}</span><span class="tnum due">฿${fmtMoney(due)}</span></div>
        ${btn}
    </div></div>`;
}

function shell(d: DocDetail): string {
    const pay = d.status === 'void' ? 'void' : d.payment_status;
    const badge = `<span class="badge ${pay}">${escapeHtml(t(d.status === 'void' ? 'pur-status-void' : 'pur-pay-' + d.payment_status))}</span>`;
    const acts =
        d.status === 'void'
            ? ''
            : d.status === 'draft'
              ? `<button class="btn" id="pur-edit-btn">${escapeHtml(t('pur-edit'))}</button>`
              : `<button class="btn danger" id="pur-void-btn">${escapeHtml(t('pur-void'))}</button><button class="btn primary" id="pur-pay-btn2" ${d.payment_status === 'paid' ? 'disabled' : ''}>${escapeHtml(t('pur-pay'))}</button>`;
    const stock =
        d.stock_applied && !(d.doc_kind === 'expense')
            ? `<div class="stocknote">✓ ${escapeHtml(t('pur-stock-applied'))}</div>`
            : '';
    const voidNote =
        d.status === 'void' ? `<div class="stocknote">${escapeHtml(t('pur-void-note'))}</div>` : '';
    return `<div class="pur d ${d.status === 'void' ? 'voided' : ''}"><div class="wrap">
        <div class="back" id="pur-back">‹ ${escapeHtml(t('pur-back'))}</div>
        <div class="ph">
            <div><div class="t">${escapeHtml(t('pur-detail-title'))} ${badge}</div>
            <div class="sub">${escapeHtml((d.supplier && d.supplier.name) || '—')}${d.doc_no ? ' · ' + escapeHtml(d.doc_no) : ''}${d.doc_date ? ' · ' + escapeHtml(d.doc_date) : ''}</div></div>
            <div class="acts">${acts}</div>
        </div>
        <div class="grid">
            <div class="col">${metaCard(d)}${itemsCard(d)}</div>
            <div class="col">
                <div class="card"><div class="hd">${escapeHtml(t('pur-bill'))}</div><div class="bd">
                    <div class="img">${d.bill_image_url ? `<img src="${escapeHtml(d.bill_image_url)}" alt="">` : ICON_DOC}</div>
                    <button class="btn" style="width:100%;" id="pur-zoom">${escapeHtml(t('pur-zoom'))}</button>
                </div></div>
                ${amountCard(d)}${payCard(d)}${stock}${voidNote}
            </div>
        </div>
    </div></div>`;
}

function bind(): void {
    document.getElementById('pur-back')!.onclick = () => window.routeTo?.('purchase');
    const edit = document.getElementById('pur-edit-btn');
    if (edit) edit.onclick = () => window.openPurchaseForm?.(cur!.id);
    const pay1 = document.getElementById('pur-pay-btn');
    const pay2 = document.getElementById('pur-pay-btn2');
    const onPay = () => window.openPurchasePay?.(cur, () => load(cur!.id));
    if (pay1) pay1.onclick = onPay;
    if (pay2) pay2.onclick = onPay;
    const voidBtn = document.getElementById('pur-void-btn');
    if (voidBtn) voidBtn.onclick = doVoid;
    document.querySelectorAll<HTMLElement>('[data-match]').forEach((el) => {
        el.onclick = () => window.openPurchaseMatch?.({}, () => load(cur!.id));
    });
}

async function doVoid(): Promise<void> {
    if (typeof window.showConfirm === 'function') {
        const okc = await window.showConfirm(t('pur-void-confirm'));
        if (!okc) return;
    }
    try {
        await papi('POST', `/api/purchase/docs/${cur!.id}/void`, {});
        // 交互完整性:作废成功反馈;已入库的单回冲库存 → 明示"库存已回冲"(连带影响说明)。
        showToast(t(cur!.stock_applied ? 'pur-void-ok-stock' : 'pur-void-ok'), 'success');
        load(cur!.id);
    } catch (e) {
        showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
    }
}

function showState(html: string): void {
    const sec = document.getElementById('page-purchase-detail');
    if (sec)
        sec.innerHTML = `<div class="pur"><div class="wrap"><div class="state">${html}</div></div></div>`;
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
    injectStyle('pur-detail-css', PAGE_CSS);
    if (!pendingId) {
        window.routeTo?.('purchase');
        return;
    }
    const id = pendingId;
    load(id);
};
