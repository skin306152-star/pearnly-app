// 销项开票模块 PO-10 · 发票详情弹窗(.modal · 非抽屉)
// 接 GET /{id} + /pdf + /void + /credit-note + /debit-note + /convert + /promptpay-qr。
// 邮件 / LINE 后端未上线 → 按钮置灰标「接通中」(showToast)。视觉照 app.html openDetail。
/* global t, escapeHtml, apiGet, apiPost, showToast */
import { type SalesDoc, docTypeLabel, fmtMoney, fmtDate, salesFetch } from './sales-common.js';

const I = {
    x: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M18 6 6 18M6 6l12 12"/></svg>',
    dl: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>',
    print: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M6 9V2h12v7M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2M6 14h12v8H6z"/></svg>',
    send: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="m22 2-7 20-4-9-9-4Z"/></svg>',
    ban: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><circle cx="12" cy="12" r="9"/><path d="m5 5 14 14"/></svg>',
    undo: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M3 7v6h6M3 13a9 9 0 1 0 3-7.7L3 8"/></svg>',
    copy: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M9 9h11v11H9zM5 15H4V4h11v1"/></svg>',
    qr: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><path d="M14 14h3v3h-3zM21 14v7M17 21h4"/></svg>',
};

let sellers: Record<string, { name?: string; tax_id?: string; address?: string; branch?: string }> =
    {};
let current: SalesDoc | null = null;

function detailMask(): HTMLElement {
    return document.getElementById('sales-detail-mask')!;
}
function actionMask(): HTMLElement {
    return document.getElementById('sales-action-mask')!;
}
function closeDetail() {
    detailMask().style.display = 'none';
    detailMask().innerHTML = '';
}
function closeAction() {
    actionMask().style.display = 'none';
    actionMask().innerHTML = '';
}

async function ensureSellers() {
    if (Object.keys(sellers).length) return;
    try {
        const data = await apiGet('/api/sales/sellers');
        const list = (data && (data.sellers || data.items || data)) || [];
        if (Array.isArray(list)) {
            for (const s of list) sellers[String(s.workspace_client_id ?? s.id)] = s;
        }
    } catch (_) {
        /* 卖方资料拉取失败不阻断详情 */
    }
}

function miniInvoice(d: SalesDoc): string {
    const seller =
        sellers[
            String((d as { seller_workspace_client_id?: number }).seller_workspace_client_id ?? '')
        ] || {};
    const isCopy = false;
    const lines = (d.lines || [])
        .map(
            (ln, i) =>
                `<tr><td>${i + 1}</td><td>${escapeHtml(String(ln.description || '—'))}</td><td style="text-align:right">${fmtMoney(ln.amount ?? Number(ln.qty || 0) * Number(ln.unit_price || 0))}</td></tr>`
        )
        .join('');
    return `<div class="sx-inv">
        <div class="sx-cb">${isCopy ? 'สำเนา' : 'ต้นฉบับ'}</div>
        <h4>${escapeHtml(seller.name || t('sx-seller'))}</h4>
        <div class="sx-no">${escapeHtml(docTypeLabel(d.doc_type))} · ${escapeHtml(d.doc_number || t('sx-draft-tag'))} · ${escapeHtml(fmtDate(d.issue_date))}</div>
        <div class="sx-pp">
            <div><div class="sx-tt">ผู้ขาย / ${escapeHtml(t('sx-seller'))}</div>${escapeHtml(seller.name || '—')}<br><span style="color:var(--ink-3)">Tax ID ${escapeHtml(seller.tax_id || '—')}</span></div>
            <div><div class="sx-tt">ผู้ซื้อ / ${escapeHtml(t('sx-buyer'))}</div>${escapeHtml((d.buyer && d.buyer.name) || '—')}<br><span style="color:var(--ink-3)">${escapeHtml((d.buyer && d.buyer.tax_id) || '')}</span></div>
        </div>
        <table><thead><tr><th>#</th><th>${escapeHtml(t('sx-col-item'))}</th><th style="text-align:right">${escapeHtml(t('sx-col-amount'))}</th></tr></thead>
            <tbody>${lines || `<tr><td colspan="3" style="color:var(--ink-3)">—</td></tr>`}</tbody></table>
        <div class="sx-tot">
            <div class="sx-tr"><span>${escapeHtml(t('sx-subtotal'))}</span><span>${fmtMoney(d.subtotal)}</span></div>
            <div class="sx-tr"><span>VAT ${fmtMoney(d.vat_rate)}%</span><span>${fmtMoney(d.vat_amount)}</span></div>
            ${Number(d.wht_amount || 0) ? `<div class="sx-tr"><span>WHT</span><span>-${fmtMoney(d.wht_amount)}</span></div>` : ''}
            <div class="sx-tr g"><span>${escapeHtml(t('sx-grand'))}</span><span>฿ ${fmtMoney(d.grand_total)}</span></div>
        </div>
    </div>`;
}

function renderDetail(d: SalesDoc) {
    const voided = d.status === 'void';
    const isQuote = d.doc_type === 'quotation';
    const unpaid = d.status === 'issued' && (d.payment?.status || 'unpaid') !== 'paid';
    const acts = voided
        ? `<span style="color:var(--ink-3)">${escapeHtml(t('sx-voided-note'))}</span>`
        : `<button class="btn btn-ghost btn-sm" data-act="download">${I.dl}<span>${escapeHtml(t('sx-download'))}</span></button>
           <button class="btn btn-ghost btn-sm" data-act="print">${I.print}<span>${escapeHtml(t('sx-print'))}</span></button>
           <button class="btn btn-ghost btn-sm" data-act="send">${I.send}<span>${escapeHtml(t('sx-send-to'))}</span></button>
           ${unpaid ? `<button class="btn btn-accent btn-sm" data-act="promptpay">${I.qr}<span>${escapeHtml(t('sx-promptpay'))}</span></button>` : ''}
           <button class="btn btn-ghost btn-sm" data-act="copy">${I.copy}<span>${escapeHtml(t('sx-copy'))}</span></button>`;
    const mutate = voided
        ? ''
        : `${isQuote ? `<button class="btn btn-ghost btn-sm" data-act="convert">${escapeHtml(t('sx-convert'))}</button>` : ''}
           <button class="btn btn-ghost btn-sm" data-act="credit">${I.undo}<span>${escapeHtml(t('sx-credit'))}</span></button>
           <button class="btn btn-ghost btn-sm" data-act="debit"><span>${escapeHtml(t('sx-debit'))}</span></button>
           <button class="btn btn-danger btn-sm" data-act="void">${I.ban}<span>${escapeHtml(t('sx-void'))}</span></button>`;
    detailMask().innerHTML = `<div class="modal" role="dialog" style="max-width:640px">
        <div class="modal-header">
            <div class="modal-title">${escapeHtml(t('sx-detail-title'))} · ${escapeHtml(d.doc_number || t('sx-draft-tag'))}
                <span class="sx-badge ${escapeHtml(d.status)}" style="margin-left:6px">${escapeHtml(t('sx-st-' + d.status))}</span></div>
            <button class="modal-close" id="sx-detail-close">${I.x}</button>
        </div>
        <div class="modal-body">
            <div class="sx-detail-acts">${acts}</div>
            ${miniInvoice(d)}
            <div class="sx-banner">${escapeHtml(t('sx-archived'))}${(d as { pdf_sha256?: string }).pdf_sha256 ? ' · sha256 ✓' : ''}</div>
        </div>
        <div class="modal-footer" style="justify-content:space-between">
            <div style="display:flex;gap:7px;flex-wrap:wrap">${mutate}</div>
            <button class="btn btn-ghost" id="sx-detail-close2">${escapeHtml(t('sx-close'))}</button>
        </div>
    </div>`;
    detailMask().style.display = 'flex';
    bindDetail(d);
}

function bindDetail(d: SalesDoc) {
    document.getElementById('sx-detail-close')!.onclick = closeDetail;
    document.getElementById('sx-detail-close2')!.onclick = closeDetail;
    detailMask().onclick = (e) => {
        if (e.target === detailMask()) closeDetail();
    };
    detailMask()
        .querySelectorAll<HTMLElement>('[data-soft]')
        .forEach((el) => (el.onclick = () => showToast(t(el.dataset.soft!), 'info')));
    detailMask()
        .querySelectorAll<HTMLElement>('[data-act]')
        .forEach((el) => (el.onclick = () => runAction(el.dataset.act!, d)));
}

async function downloadPdf(d: SalesDoc, forPrint: boolean) {
    try {
        const resp = await salesFetch(`/api/sales/documents/${d.id}/pdf?page=A4&copy=original`);
        if (!resp.ok) {
            showToast(t('sx-pdf-fail'), 'error');
            return;
        }
        const url = URL.createObjectURL(await resp.blob());
        const w = window.open(url, '_blank');
        if (forPrint && w) w.addEventListener('load', () => w.print());
        setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (_) {
        showToast(t('sx-pdf-fail'), 'error');
    }
}

async function promptpay(d: SalesDoc) {
    try {
        const resp = await salesFetch(`/api/sales/documents/${d.id}/promptpay-qr`);
        if (!resp.ok) {
            const body = await resp.json().catch(() => ({}));
            const code = String(body.detail || '').replace('sales.', '');
            showToast(t('sx-pp-' + code) || t('sx-pp-fail'), 'error');
            return;
        }
        const url = URL.createObjectURL(await resp.blob());
        const due = Number(d.grand_total || 0) - Number(d.payment?.paid_amount || 0);
        actionMask().innerHTML = `<div class="modal" role="dialog" style="max-width:380px">
            <div class="modal-header"><div class="modal-title">${escapeHtml(t('sx-promptpay'))} · PromptPay</div>
                <button class="modal-close" id="sx-pp-close">${I.x}</button></div>
            <div class="modal-body" style="text-align:center">
                <div class="sx-qr"><img src="${url}" alt="PromptPay QR"></div>
                <div style="font-weight:700;font-size:16px">฿ ${fmtMoney(due)}</div>
                <div style="color:var(--ink-3);font-size:12px;margin-top:4px">${escapeHtml(t('sx-pp-scan'))}</div>
            </div></div>`;
        actionMask().style.display = 'flex';
        document.getElementById('sx-pp-close')!.onclick = closeAction;
        actionMask().onclick = (e) => {
            if (e.target === actionMask()) closeAction();
        };
        setTimeout(() => URL.revokeObjectURL(url), 120000);
    } catch (_) {
        showToast(t('sx-pp-fail'), 'error');
    }
}

function noteModal(d: SalesDoc, type: 'credit_note' | 'debit_note') {
    const title = type === 'credit_note' ? t('sx-credit-title') : t('sx-debit-title');
    actionMask().innerHTML = `<div class="modal" role="dialog" style="max-width:460px">
        <div class="modal-header"><div class="modal-title">${escapeHtml(title)}</div>
            <button class="modal-close" id="sx-note-close">${I.x}</button></div>
        <div class="modal-body">
            <div class="sx-banner">${escapeHtml(type === 'credit_note' ? t('sx-credit-note') : t('sx-debit-note'))}</div>
            <div class="form-row"><label>${escapeHtml(t('sx-reason'))}</label><input type="text" id="sx-note-reason" maxlength="200"></div>
            <div class="form-row"><label>${escapeHtml(t('sx-note-amount'))}</label><input type="number" id="sx-note-amount" min="0" step="0.01" placeholder="0.00"></div>
        </div>
        <div class="modal-footer" style="justify-content:flex-end;gap:8px">
            <button class="btn btn-ghost" id="sx-note-cancel">${escapeHtml(t('sx-cancel'))}</button>
            <button class="btn btn-primary" id="sx-note-ok">${escapeHtml(t('sx-note-ok'))}</button>
        </div></div>`;
    actionMask().style.display = 'flex';
    document.getElementById('sx-note-close')!.onclick = closeAction;
    document.getElementById('sx-note-cancel')!.onclick = closeAction;
    actionMask().onclick = (e) => {
        if (e.target === actionMask()) closeAction();
    };
    document.getElementById('sx-note-ok')!.onclick = async () => {
        const reason = (document.getElementById('sx-note-reason') as HTMLInputElement).value.trim();
        const amount = Number(
            (document.getElementById('sx-note-amount') as HTMLInputElement).value
        );
        if (!(amount > 0)) {
            showToast(t('sx-note-amount-required'), 'error');
            return;
        }
        const ok = await postMutate(
            `/api/sales/documents/${d.id}/${type === 'credit_note' ? 'credit-note' : 'debit-note'}`,
            {
                reason: reason || title,
                vat_rate: Number(d.vat_rate || 7),
                wht_rate: 0,
                lines: [
                    {
                        description: reason || title,
                        qty: 1,
                        unit_price: amount,
                        vat_applicable: true,
                    },
                ],
            }
        );
        if (ok) {
            closeAction();
            closeDetail();
            showToast(t('sx-done'), 'success');
            window.dispatchEvent(new CustomEvent('pearnly:sales-changed'));
        }
    };
}

function voidModal(d: SalesDoc) {
    actionMask().innerHTML = `<div class="modal" role="dialog" style="max-width:440px">
        <div class="modal-header"><div class="modal-title">${escapeHtml(t('sx-void-title'))}</div>
            <button class="modal-close" id="sx-void-close">${I.x}</button></div>
        <div class="modal-body"><div class="sx-banner warn">${escapeHtml(t('sx-void-warn'))}</div></div>
        <div class="modal-footer" style="justify-content:flex-end;gap:8px">
            <button class="btn btn-ghost" id="sx-void-cancel">${escapeHtml(t('sx-cancel'))}</button>
            <button class="btn btn-danger" id="sx-void-ok">${escapeHtml(t('sx-void'))}</button>
        </div></div>`;
    actionMask().style.display = 'flex';
    document.getElementById('sx-void-close')!.onclick = closeAction;
    document.getElementById('sx-void-cancel')!.onclick = closeAction;
    actionMask().onclick = (e) => {
        if (e.target === actionMask()) closeAction();
    };
    document.getElementById('sx-void-ok')!.onclick = async () => {
        const ok = await postMutate(`/api/sales/documents/${d.id}/void`, {});
        if (ok) {
            closeAction();
            closeDetail();
            showToast(t('sx-done'), 'success');
            window.dispatchEvent(new CustomEvent('pearnly:sales-changed'));
        }
    };
}

async function convert(d: SalesDoc) {
    const ok = await postMutate(`/api/sales/documents/${d.id}/convert`, {
        target_doc_type: 'tax_invoice',
    });
    if (ok) {
        closeDetail();
        showToast(t('sx-converted'), 'success');
        window.dispatchEvent(new CustomEvent('pearnly:sales-changed'));
    }
}

async function postMutate(url: string, body: unknown): Promise<boolean> {
    try {
        const resp = await apiPost(url, body);
        if (resp && resp.ok) return true;
        const data = resp ? await resp.json().catch(() => ({})) : {};
        showToast(t('sx-action-fail') + (data.detail ? ' · ' + data.detail : ''), 'error');
        return false;
    } catch (_) {
        showToast(t('sx-action-fail'), 'error');
        return false;
    }
}

// 发送给买家 · 两档(Zihao 砍掉私人 Gmail / 官号推送):
// 邮件 = Pearnly 代发(填买家邮箱)· LINE = 生成分享链接卖方自己转。
// 后端 POST /{id}/send 未上线 → 发送按钮置「接通中」。
let sendCh: 'email' | 'line' = 'email';

function seg(opts: [string, string][], cur: string, attr: string): string {
    return `<div class="sx-seg" style="width:100%">${opts
        .map(
            (o) =>
                `<button type="button" data-${attr}="${o[0]}" class="${cur === o[0] ? 'on' : ''}" style="flex:1">${escapeHtml(o[1])}</button>`
        )
        .join('')}</div>`;
}

function sendModal(d: SalesDoc) {
    const body =
        sendCh === 'email'
            ? `<div class="sx-banner" style="margin-top:4px">${escapeHtml(t('sx-send-email-hint'))}</div>
               <div class="form-row" style="margin-top:12px"><label>${escapeHtml(t('sx-send-buyer-email'))}</label><input type="email" id="sx-send-email" placeholder="buyer@example.com"></div>`
            : `<div class="sx-banner" style="margin-top:4px">${escapeHtml(t('sx-send-line-hint'))}</div>`;
    actionMask().innerHTML = `<div class="modal" role="dialog" style="max-width:460px">
        <div class="modal-header"><div class="modal-title">${escapeHtml(t('sx-send-to-title'))}</div>
            <button class="modal-close" id="sx-send-close">${I.x}</button></div>
        <div class="modal-body">
            <div class="form-row"><label>${escapeHtml(t('sx-send-how'))}</label>
                ${seg(
                    [
                        ['email', t('sx-send-opt-email')],
                        ['line', t('sx-send-opt-line')],
                    ],
                    sendCh,
                    'ch'
                )}</div>
            ${body}
        </div>
        <div class="modal-footer" style="justify-content:flex-end;gap:8px">
            <button class="btn btn-ghost" id="sx-send-cancel">${escapeHtml(t('sx-cancel'))}</button>
            <button class="btn btn-primary" id="sx-send-do">${escapeHtml(sendCh === 'email' ? t('sx-send-do') : t('sx-send-genlink'))}</button>
        </div></div>`;
    actionMask().style.display = 'flex';
    document.getElementById('sx-send-close')!.onclick = closeAction;
    document.getElementById('sx-send-cancel')!.onclick = closeAction;
    actionMask().onclick = (e) => {
        if (e.target === actionMask()) closeAction();
    };
    actionMask()
        .querySelectorAll<HTMLElement>('[data-ch]')
        .forEach(
            (el) =>
                (el.onclick = () => ((sendCh = el.dataset.ch as 'email' | 'line'), sendModal(d)))
        );
    document.getElementById('sx-send-do')!.onclick = () => doSend(d);
}

async function doSend(d: SalesDoc) {
    if (sendCh === 'email') {
        const to = (document.getElementById('sx-send-email') as HTMLInputElement).value.trim();
        if (!to) return showToast(t('sx-send-email-required'), 'error');
        const r = await apiPost(`/api/sales/documents/${d.id}/send`, { channel: 'email', to });
        if (r && r.ok) {
            closeAction();
            showToast(t('sx-send-email-ok'), 'success');
        } else {
            showToast(t('sx-send-fail'), 'error');
        }
        return;
    }
    // line:后端生成公开分享链接,卖方自己用 LINE 转
    const r = await apiPost(`/api/sales/documents/${d.id}/send`, { channel: 'line' });
    const data = r ? await r.json().catch(() => ({})) : {};
    if (!r || !r.ok || !data.share_url) return showToast(t('sx-send-fail'), 'error');
    const url = String(data.share_url);
    actionMask().innerHTML = `<div class="modal" role="dialog" style="max-width:480px">
        <div class="modal-header"><div class="modal-title">${escapeHtml(t('sx-send-line-title'))}</div>
            <button class="modal-close" id="sx-link-close">${I.x}</button></div>
        <div class="modal-body">
            <div class="sx-banner">${escapeHtml(t('sx-send-line-ready'))}</div>
            <div class="form-row" style="margin-top:10px"><input type="text" id="sx-link-url" readonly value="${escapeHtml(url)}"></div>
        </div>
        <div class="modal-footer" style="justify-content:flex-end;gap:8px">
            <button class="btn btn-ghost" id="sx-link-done">${escapeHtml(t('sx-close'))}</button>
            <button class="btn btn-primary" id="sx-link-copy">${escapeHtml(t('sx-send-copy'))}</button>
        </div></div>`;
    document.getElementById('sx-link-close')!.onclick = closeAction;
    document.getElementById('sx-link-done')!.onclick = closeAction;
    document.getElementById('sx-link-copy')!.onclick = () => {
        const inp = document.getElementById('sx-link-url') as HTMLInputElement;
        inp.select();
        navigator.clipboard?.writeText(url).catch(() => {});
        showToast(t('sx-send-copied'), 'success');
    };
}

// 复制再开:用本单内容(双方/明细/税率)建一张新草稿,回流工作台。
async function copyDoc(d: SalesDoc) {
    const dd = d as unknown as {
        client_id: number | null;
        seller_workspace_client_id: number | null;
        currency: string;
        header_discount_amount: number | string;
        header_discount_pct: number | string;
    };
    const lines = (d.lines || [])
        .map((l) => {
            const ln = l as unknown as {
                description?: string;
                qty?: number | string;
                unit_price?: number | string;
                discount?: number | string;
                vat_applicable?: boolean;
            };
            return {
                description: (ln.description || '').trim(),
                qty: Number(ln.qty || 0),
                unit_price: Number(ln.unit_price || 0),
                discount: Number(ln.discount || 0),
                vat_applicable: ln.vat_applicable !== false,
            };
        })
        .filter((l) => l.description);
    if (!lines.length) return showToast(t('sx-action-fail'), 'error');
    const body = {
        doc_type: d.doc_type,
        client_id: dd.client_id,
        seller_workspace_client_id: dd.seller_workspace_client_id,
        currency: dd.currency || 'THB',
        vat_rate: Number(d.vat_rate || 0),
        wht_rate: Number(d.wht_rate || 0),
        header_discount_amount: Number(dd.header_discount_amount || 0),
        header_discount_pct: Number(dd.header_discount_pct || 0),
        price_includes_vat: !!d.price_includes_vat,
        lines,
        buyer: d.buyer && d.buyer.type ? { ...d.buyer } : null,
        payment: null,
    };
    const ok = await postMutate('/api/sales/documents', body);
    if (ok) {
        closeDetail();
        showToast(t('sx-copied'), 'success');
        window.dispatchEvent(new CustomEvent('pearnly:sales-changed'));
    }
}

function runAction(act: string, d: SalesDoc) {
    if (act === 'download') return void downloadPdf(d, false);
    if (act === 'print') return void downloadPdf(d, true);
    if (act === 'send') return sendModal(d);
    if (act === 'promptpay') return void promptpay(d);
    if (act === 'copy') return void copyDoc(d);
    if (act === 'credit') return noteModal(d, 'credit_note');
    if (act === 'debit') return noteModal(d, 'debit_note');
    if (act === 'void') return voidModal(d);
    if (act === 'convert') return void convert(d);
}

window.openSalesDetail = async function (docId: string) {
    detailMask().innerHTML = `<div class="modal" role="dialog" style="max-width:640px"><div class="modal-body"><div class="sx-state">${escapeHtml(t('sx-loading'))}</div></div></div>`;
    detailMask().style.display = 'flex';
    await ensureSellers();
    try {
        const data = await apiGet(`/api/sales/documents/${docId}`);
        if (!data) return;
        current = data.document as SalesDoc;
        renderDetail(current);
    } catch (_) {
        detailMask().innerHTML = `<div class="modal" role="dialog" style="max-width:480px"><div class="modal-body"><div class="sx-state error">${escapeHtml(t('sx-error'))}</div></div></div>`;
        const m = detailMask();
        m.onclick = (e) => {
            if (e.target === m) closeDetail();
        };
    }
};
