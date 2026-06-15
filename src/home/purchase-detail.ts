// 商户采购 · 屏6 单据详情(主屏点 posted 行进来)· 照搬设计稿 06-单据详情。
// 桌面两栏(信息+品项 左 / 票图+金额+付款 右)/ 手机单列。记付款(屏7)/ 作废 / (草稿)编辑。
// 费用单(无 VAT)隐藏 进项税 / 品项 SKU 段;已作废 = 灰态 + 回冲提示。四态。
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

let pendingId: string | null = null;
let cur: DocDetail | null = null;
let billBlobUrl = '';

const PAGE_CSS = `
.pur.d .wrap{width:100%;}
/* 全宽 wrap(视觉闸要 maxWidth:none)· 内层 ph/grid 居中约束到可读宽度,详情字段才不在宽屏上散开。*/
.pur.d .ph,.pur.d .grid{max-width:1120px;margin-left:auto;margin-right:auto;}
.pur .ph{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:16px;}
.pur.d .ph .phl{display:flex;align-items:center;gap:11px;}
.pur.d .ph .back{font-size:24px;line-height:1;color:var(--ink2);flex:none;cursor:pointer;}
.pur .ph .t{font-size:20px;font-weight:700;display:flex;align-items:center;gap:10px;}
.pur .ph .sub{color:var(--ink2);font-size:13px;margin-top:4px;}
.pur .acts{display:flex;gap:9px;flex-shrink:0;}
.pur .badge{font-size:11px;padding:2px 9px;border-radius:6px;}
.pur .badge.paid{background:var(--green-weak);color:var(--green);} .pur .badge.unpaid{background:var(--amber-weak);color:var(--amber);} .pur .badge.partial{background:var(--amber-weak);color:var(--amber);} .pur .badge.void{background:var(--line2);color:var(--ink2);}
.pur .grid{display:grid;grid-template-columns:1fr 360px;gap:14px;align-items:start;}
.pur .col{display:flex;flex-direction:column;gap:14px;}
.pur .card .hd{padding:13px 16px;border-bottom:1px solid var(--line);font-weight:600;font-size:13px;display:flex;justify-content:space-between;align-items:center;}
.pur .card .hd .muted{color:var(--ink3);font-weight:400;}
.pur .card .bd{padding:14px 16px;}
.pur .meta{display:grid;grid-template-columns:1fr 1fr;gap:12px 18px;}
.pur .meta .f .l{color:var(--ink2);font-size:11.5px;}
.pur .meta .f .v{font-size:14px;margin-top:3px;font-weight:600;}
.pur .src{display:inline-flex;align-items:center;gap:5px;font-size:11px;padding:2px 8px;border-radius:6px;background:var(--accent-weak);color:var(--accent-deep);}
.pur .src.line{background:var(--green-weak);color:var(--green);}
.pur table{width:100%;border-collapse:collapse;}
.pur .card th{text-align:left;font-size:11.5px;color:var(--ink2);font-weight:600;padding:9px 0;border-bottom:1px solid var(--line);background:transparent;text-transform:none;letter-spacing:0;}
.pur .card td{padding:11px 0;border-bottom:1px solid var(--line2);font-size:13px;vertical-align:top;}
.pur .card tr:last-child td{border-bottom:0;}
.pur .pill{font-size:10.5px;padding:1px 7px;border-radius:5px;margin-left:6px;}
.pur .pill.ok{background:var(--green-weak);color:var(--green);} .pur .pill.warn{background:var(--amber-weak);color:var(--amber);cursor:pointer;}
.pur .sum{display:flex;justify-content:space-between;padding:7px 0;font-size:13px;}
.pur .sum.tot{border-top:1px solid var(--line);margin-top:6px;padding-top:11px;font-weight:800;font-size:15px;}
.pur .sum .tax{color:var(--green);}
.pur .pay{display:flex;justify-content:space-between;align-items:baseline;padding:6px 0;font-size:13px;}
.pur .pay .due{color:var(--amber);font-weight:700;}
.pur .img{aspect-ratio:3/4;background:var(--line2);border:1px dashed var(--line);border-radius:10px;display:flex;align-items:center;justify-content:center;color:var(--ink3);margin-bottom:10px;overflow:hidden;cursor:zoom-in;}
.pur .img img{width:100%;height:100%;object-fit:cover;}
.pur-lightbox{position:fixed;inset:0;background:rgba(17,24,39,.86);z-index:1100;display:flex;align-items:center;justify-content:center;padding:32px;cursor:zoom-out;}
.pur-lightbox img{max-width:100%;max-height:100%;object-fit:contain;border-radius:8px;}
.pur .stocknote{margin-top:10px;font-size:12px;color:var(--ink2);background:var(--green-weak);border:1px solid var(--green-weak);border-radius:9px;padding:9px 11px;}
.pur.voided{opacity:.62;}
.pur .vch{display:flex;flex-direction:column;gap:8px;}
.pur .vch .btn{width:100%;justify-content:flex-start;}
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

// 凭证 surface(documents.py 已建):无原始票据 → 生成替代收据;WHT>0 → 生成扣缴凭证;
// 已生成的凭证可下载(复用 openPurchasePdf 带 Bearer 取 PDF blob)。已作废单不显。
function voucherCard(d: DocDetail): string {
    if (d.status === 'void') return '';
    const hasSub = d.attachments.some((a) => a.kind === 'substitute_receipt');
    const hasWht = d.attachments.some((a) => a.kind === 'wht_cert');
    const noBill = !d.bill_image_url;
    const rows: string[] = [];
    if (hasSub)
        rows.push(
            `<button class="btn" data-dl="substitute_receipt">${escapeHtml(t('pur-dl-substitute'))}</button>`
        );
    if (hasWht)
        rows.push(`<button class="btn" data-dl="wht_cert">${escapeHtml(t('pur-dl-wht'))}</button>`);
    if (noBill && !hasSub)
        rows.push(
            `<button class="btn" data-gen="substitute_receipt">${escapeHtml(t('pur-gen-substitute'))}</button>`
        );
    if (d.wht_amount > 0 && !hasWht)
        rows.push(
            `<button class="btn" data-gen="wht_cert">${escapeHtml(t('pur-gen-wht'))}</button>`
        );
    if (!rows.length) return '';
    return `<div class="card"><div class="hd">${escapeHtml(t('pur-voucher'))}</div><div class="bd vch">${rows.join('')}</div></div>`;
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
        <div class="ph">
            <div class="phl"><span class="back" id="pur-back" title="${escapeHtml(t('pur-back'))}" aria-label="${escapeHtml(t('pur-back'))}">‹</span>
            <div><div class="t">${escapeHtml(t('pur-detail-title'))} ${badge}</div>
            <div class="sub">${escapeHtml((d.supplier && d.supplier.name) || '—')}${d.doc_no ? ' · ' + escapeHtml(d.doc_no) : ''}${d.doc_date ? ' · ' + escapeHtml(d.doc_date) : ''}</div></div></div>
            <div class="acts">${acts}</div>
        </div>
        <div class="grid">
            <div class="col">${metaCard(d)}${itemsCard(d)}</div>
            <div class="col">
                <div class="card"><div class="hd">${escapeHtml(t('pur-bill'))}</div><div class="bd">
                    <div class="img" id="pur-bill-img">${ICON_DOC}</div>
                    <button class="btn" style="width:100%;" id="pur-zoom"${d.bill_image_url ? '' : ' disabled'}>${escapeHtml(t('pur-zoom'))}</button>
                </div></div>
                ${amountCard(d)}${payCard(d)}${voucherCard(d)}${stock}${voidNote}
            </div>
        </div>
    </div></div>`;
}

// 票图是鉴权端点(/api/purchase/docs/{id}/bill-image · 需 Bearer),不能直接塞 <img src> 否则 401 破图。
// 先渲占位 svg(视觉闸要 .pur .img 内有 svg),再带令牌取 blob 换上;放大看复用同一 blob。
async function loadBillImage(): Promise<void> {
    billBlobUrl = '';
    const url = cur && cur.bill_image_url;
    const box = document.getElementById('pur-bill-img');
    if (!url || !box) return;
    try {
        billBlobUrl = await fetchAuthedBlobUrl(url);
        box.innerHTML = `<img src="${billBlobUrl}" alt="">`;
    } catch (_) {
        /* 取图失败 → 保留占位 svg,放大看按钮已 disabled */
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
    injectStyle('pur-detail-css', PAGE_CSS);
    if (!pendingId) {
        window.routeTo?.('purchase');
        return;
    }
    const id = pendingId;
    load(id);
};
