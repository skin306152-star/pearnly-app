// 商户采购 · 屏7 记付款 / 屏8 商品匹配 / 屏9 供应商选择器 / 屏3 LINE 一句话记费用(说明)。
// 照搬设计稿 07/08/09/03。桌面居中 .modal / 手机底部抽屉(媒体查询)。挂 home.html 四个 mask 空壳。
/* global t, escapeHtml, showToast */
import {
    papi,
    purchaseErrMsg,
    fmtMoney,
    injectStyle,
    type DocDetail,
    type Supplier,
} from './purchase-common.js';

const CSS = `
.purm-scrim{position:fixed;inset:0;background:rgba(17,24,39,.42);display:flex;align-items:center;justify-content:center;padding:20px;z-index:1200;}
.purm{--blue:#2563EB;--blue-d:#1D4ED8;--blue-l:#DBEAFE;--ink:#111827;--ink2:#6B7280;--ink3:#9CA3AF;--line:#e8e8e3;--green:#16A34A;--amber:#F59E0B;
  background:#fff;border-radius:16px;width:100%;max-width:440px;box-shadow:0 20px 60px rgba(17,24,39,.3);overflow:hidden;color:var(--ink);font-size:13.5px;}
.purm.w480{max-width:480px;} .purm.w560{max-width:560px;}
.purm *{box-sizing:border-box;}
.purm .tnum{font-variant-numeric:tabular-nums;}
.purm .mh{padding:16px 20px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;}
.purm .mh .t{font-size:16px;font-weight:700;} .purm .mh .x{color:var(--ink3);font-size:20px;cursor:pointer;line-height:1;}
.purm .mb{padding:18px 20px;}
.purm .who{color:var(--ink2);font-size:12.5px;margin-bottom:14px;}
.purm .recap{background:#fafaf8;border:1px solid var(--line);border-radius:10px;padding:11px 13px;margin-bottom:16px;}
.purm .recap .row{display:flex;justify-content:space-between;padding:4px 0;font-size:13px;}
.purm .recap .row.due{font-weight:800;} .purm .recap .due .a{color:var(--amber);}
.purm .field{margin-bottom:14px;} .purm .field>label{display:block;font-size:12px;color:var(--ink2);margin-bottom:6px;}
.purm .inp{height:42px;border:1px solid var(--line);border-radius:10px;display:flex;align-items:center;padding:0 12px;font-size:15px;font-weight:700;background:#fff;}
.purm .inp .cur{color:var(--ink3);margin-right:6px;font-weight:400;}
.purm .inp input{border:0;outline:0;background:transparent;font:inherit;color:inherit;width:100%;}
.purm .seg{display:flex;gap:8px;} .purm .seg .o{flex:1;height:40px;border:1px solid var(--line);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:13px;color:var(--ink2);cursor:pointer;}
.purm .seg .o.on{border-color:var(--blue);background:var(--blue-l);color:var(--blue-d);font-weight:700;}
.purm .two{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.purm .quick{font-size:12px;color:var(--blue);margin-top:7px;cursor:pointer;}
.purm .after{font-size:12px;color:var(--ink2);background:#f0fdf4;border:1px solid #bbf7d0;border-radius:9px;padding:9px 11px;margin-top:4px;}
.purm .hint{background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:10px 12px;margin-bottom:14px;font-size:12.5px;color:#1e40af;}
.purm .from{background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:11px 13px;margin-bottom:16px;font-size:13px;} .purm .from .l{color:#b45309;font-size:11.5px;margin-bottom:3px;}
.purm .search{height:42px;background:#fff;border:1px solid var(--line);border-radius:10px;display:flex;align-items:center;gap:8px;padding:0 12px;margin-bottom:12px;}
.purm .search input{border:0;outline:0;flex:1;background:transparent;font-size:14px;}
.purm .list{display:flex;flex-direction:column;gap:8px;max-height:300px;overflow:auto;}
.purm .row{display:flex;align-items:center;gap:11px;border:1px solid var(--line);border-radius:10px;padding:11px 12px;cursor:pointer;}
.purm .row:hover{border-color:var(--blue);background:#fafaff;}
.purm .row .av{width:36px;height:36px;border-radius:9px;background:#f3f4f6;display:flex;align-items:center;justify-content:center;color:var(--ink2);font-weight:700;flex-shrink:0;}
.purm .row .nm{font-weight:600;font-size:13.5px;} .purm .row .meta{color:var(--ink3);font-size:11.5px;margin-top:2px;}
.purm .row .match{margin-left:auto;font-size:11px;color:var(--green);background:#dcfce7;padding:2px 8px;border-radius:6px;white-space:nowrap;}
.purm .row.new{border-style:dashed;color:var(--blue);justify-content:center;font-weight:700;}
.purm .step{display:flex;gap:11px;margin-bottom:13px;} .purm .step .n{width:24px;height:24px;border-radius:50%;background:var(--blue);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;flex:0 0 24px;}
.purm .step .tx{font-size:13px;line-height:1.5;} .purm .step .tx b{color:var(--ink);}
.purm .note{font-size:12px;color:var(--ink2);background:#f8f8f5;border:1px solid var(--line);border-radius:10px;padding:11px 13px;line-height:1.6;}
.purm .mf{padding:14px 20px;border-top:1px solid var(--line);display:flex;gap:10px;justify-content:flex-end;}
.purm .btn{height:42px;padding:0 18px;border:1px solid var(--line);border-radius:10px;background:#fff;color:var(--ink);font-size:14px;cursor:pointer;}
.purm .btn.primary{background:var(--blue);border-color:var(--blue);color:#fff;font-weight:700;}
@media(max-width:600px){
  .purm{max-width:100%;border-radius:16px 16px 0 0;align-self:flex-end;}
  .purm-scrim{align-items:flex-end;padding:0;}
}
`;

function ensureCss(): void {
    injectStyle('pur-modal-css', CSS);
}

function openMask(maskId: string, inner: string): HTMLElement | null {
    ensureCss();
    const mask = document.getElementById(maskId);
    if (!mask) return null;
    mask.innerHTML = `<div class="purm-scrim">${inner}</div>`;
    mask.style.display = 'block';
    const scrim = mask.querySelector('.purm-scrim') as HTMLElement;
    scrim.onclick = (e) => {
        if (e.target === scrim) closeMask(maskId);
    };
    mask.querySelectorAll<HTMLElement>('[data-close]').forEach((el) => {
        el.onclick = () => closeMask(maskId);
    });
    return mask;
}

function closeMask(maskId: string): void {
    const mask = document.getElementById(maskId);
    if (mask) {
        mask.style.display = 'none';
        mask.innerHTML = '';
    }
}

// ── 屏7 记付款 ────────────────────────────────────────────────────────
window.openPurchasePay = function (docArg, onDone) {
    const d = docArg as DocDetail;
    const due = d.grand_total - d.paid_amount;
    const inner = `<div class="purm"><div class="mh"><div class="t">${escapeHtml(t('pur-pay'))}</div><div class="x" data-close>×</div></div>
        <div class="mb">
            <div class="who">${escapeHtml(t('pur-pay-to'))} <b>${escapeHtml((d.supplier && d.supplier.name) || '—')}</b>${d.doc_no ? ' · ' + escapeHtml(d.doc_no) : ''}</div>
            <div class="recap">
                <div class="row"><span>${escapeHtml(t('pur-payable'))}</span><span class="tnum">฿${fmtMoney(d.grand_total)}</span></div>
                <div class="row"><span>${escapeHtml(t('pur-paid'))}</span><span class="tnum">฿${fmtMoney(d.paid_amount)}</span></div>
                <div class="row due"><span>${escapeHtml(t('pur-due-balance'))}</span><span class="tnum"><span class="a">฿${fmtMoney(due)}</span></span></div>
            </div>
            <div class="field"><label>${escapeHtml(t('pur-pay-amount'))}</label><div class="inp"><span class="cur">฿</span><input class="tnum" id="purm-amt" type="number" value="${due.toFixed(2)}"></div><div class="quick" id="purm-payfull">${escapeHtml(t('pur-pay-full'))}</div></div>
            <div class="field"><label>${escapeHtml(t('pur-pay-method'))}</label><div class="seg" id="purm-method"><div class="o on" data-m="cash">${escapeHtml(t('pur-m-cash'))}</div><div class="o" data-m="transfer">${escapeHtml(t('pur-m-transfer'))}</div><div class="o" data-m="promptpay">PromptPay</div></div></div>
            <div class="two">
                <div class="field"><label>${escapeHtml(t('pur-pay-date'))}</label><div class="inp" style="font-weight:400;font-size:14px;"><input type="date" id="purm-date"></div></div>
                <div class="field"><label>${escapeHtml(t('pur-note'))}</label><div class="inp" style="font-weight:400;font-size:13px;"><input id="purm-note" placeholder="—"></div></div>
            </div>
            <div class="after">${escapeHtml(t('pur-pay-after'))}</div>
        </div>
        <div class="mf"><button class="btn" data-close>${escapeHtml(t('pur-cancel'))}</button><button class="btn primary" id="purm-confirm">${escapeHtml(t('pur-pay-confirm'))}</button></div>
    </div>`;
    const mask = openMask('purchase-pay-mask', inner);
    if (!mask) return;
    let method = 'cash';
    mask.querySelectorAll<HTMLElement>('#purm-method .o').forEach((o) => {
        o.onclick = () => {
            mask.querySelectorAll('#purm-method .o').forEach((x) => x.classList.remove('on'));
            o.classList.add('on');
            method = o.dataset.m!;
        };
    });
    const amt = mask.querySelector('#purm-amt') as HTMLInputElement;
    (mask.querySelector('#purm-payfull') as HTMLElement).onclick = () =>
        (amt.value = due.toFixed(2));
    (mask.querySelector('#purm-confirm') as HTMLElement).onclick = async () => {
        const v = Number(amt.value);
        if (!(v > 0) || v > due + 0.001) {
            showToast(t('pur-pay-over'), 'error');
            return;
        }
        try {
            await papi('POST', `/api/purchase/docs/${d.id}/pay`, {
                amount: v,
                method,
                date: (mask.querySelector('#purm-date') as HTMLInputElement).value,
                note: (mask.querySelector('#purm-note') as HTMLInputElement).value,
            });
            showToast(t('pur-pay-ok'), 'success');
            closeMask('purchase-pay-mask');
            onDone && onDone();
        } catch (e) {
            showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
        }
    };
};

// ── 屏8 商品匹配 / 建商品 ─────────────────────────────────────────────
const MATCH_CANDIDATES = [
    { id: 'p-br1', name: 'ขนมปังโฮลวีท', meta: 'SKU BR-001', suggest: true },
    { id: 'p-br2', name: 'ขนมปังแซนวิช', meta: 'SKU BR-002', suggest: false },
];

window.openPurchaseMatch = function (lineArg, onDone) {
    const ln = (lineArg || {}) as {
        id?: string;
        description?: string;
        qty?: number;
        unit_price?: number;
    };
    const from = `${escapeHtml(ln.description || '—')}${ln.qty ? ' · ' + ln.qty + ' × ฿' + fmtMoney(ln.unit_price) : ''}`;
    const rows = MATCH_CANDIDATES.map(
        (c) =>
            `<div class="row" data-pid="${c.id}"><div class="av">▢</div><div><div class="nm">${escapeHtml(c.name)}</div><div class="meta">${escapeHtml(c.meta)}</div></div>${c.suggest ? `<span class="match">${escapeHtml(t('pur-ai-suggest'))}</span>` : ''}</div>`
    ).join('');
    const inner = `<div class="purm w480"><div class="mh"><div class="t">${escapeHtml(t('pur-match-title'))}</div><div class="x" data-close>×</div></div>
        <div class="mb">
            <div class="from"><div class="l">${escapeHtml(t('pur-from-bill'))}</div><b>${from}</b></div>
            <div class="search"><input id="purm-msearch" placeholder="${escapeHtml(t('pur-match-search'))}" value="${escapeHtml(ln.description || '')}"></div>
            <div class="list">${rows}<div class="row new" data-pid="__new__">+ ${escapeHtml(t('pur-make-new'))}</div></div>
        </div>
        <div class="mf"><button class="btn" data-close>${escapeHtml(t('pur-skip'))}</button><button class="btn primary" id="purm-mok" disabled>${escapeHtml(t('pur-match-confirm'))}</button></div>
    </div>`;
    const mask = openMask('purchase-match-mask', inner);
    if (!mask) return;
    let picked: string | null = null;
    const okBtn = mask.querySelector('#purm-mok') as HTMLButtonElement;
    mask.querySelectorAll<HTMLElement>('[data-pid]').forEach((el) => {
        el.onclick = () => {
            picked = el.dataset.pid!;
            mask.querySelectorAll('[data-pid]').forEach((x) => x.classList.remove('on'));
            el.style.borderColor = 'var(--blue)';
            okBtn.disabled = false;
        };
    });
    okBtn.onclick = async () => {
        const isNew = picked === '__new__';
        const payload = isNew ? { create: { name: ln.description || '' } } : { product_id: picked };
        try {
            // 已持久化的行(有 line_id · 详情侧)→ 调后端 match-product;录入屏未保存行(无 id)→ 仅本地回填。
            const res = ln.id
                ? await papi('POST', `/api/purchase/lines/${ln.id}/match-product`, payload)
                : { product_id: isNew ? null : picked, create: isNew ? payload.create : undefined };
            closeMask('purchase-match-mask');
            onDone && onDone(res);
        } catch (e) {
            showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
        }
    };
};

// ── 屏9 供应商选择器 ──────────────────────────────────────────────────
window.openPurchaseSupplierPicker = function (onPick) {
    const inner = `<div class="purm"><div class="mh"><div class="t">${escapeHtml(t('pur-supplier-pick-title'))}</div><div class="x" data-close>×</div></div>
        <div class="mb">
            <div class="hint">${escapeHtml(t('pur-supplier-pick-hint'))}</div>
            <div class="search"><input id="purm-ssearch" placeholder="${escapeHtml(t('pur-supplier-search'))}"></div>
            <div class="list" id="purm-slist"><div class="state" style="padding:18px;color:var(--ink3);">${escapeHtml(t('pur-loading'))}</div></div>
        </div></div>`;
    const mask = openMask('purchase-supplier-mask', inner);
    if (!mask) return;
    const listEl = mask.querySelector('#purm-slist') as HTMLElement;
    const search = mask.querySelector('#purm-ssearch') as HTMLInputElement;
    let all: Supplier[] = [];
    const render = () => {
        const kw = search.value.trim().toLowerCase();
        const list = all.filter(
            (s) => !kw || (s.name + ' ' + (s.tax_id || '')).toLowerCase().includes(kw)
        );
        listEl.innerHTML =
            list
                .map(
                    (s) =>
                        `<div class="row" data-sid="${escapeHtml(s.id)}"><div class="av">${escapeHtml((s.name || '?').slice(0, 1))}</div><div><div class="nm">${escapeHtml(s.name)}</div><div class="meta tnum">${s.tax_id ? escapeHtml(t('pur-tax-id')) + ' ' + escapeHtml(s.tax_id) : escapeHtml(t('pur-no-tax'))}</div></div></div>`
                )
                .join('') +
            `<div class="row new" data-sid="__new__">+ ${escapeHtml(t('pur-supplier-new'))}${kw ? '「' + escapeHtml(search.value) + '」' : ''}</div>`;
        listEl.querySelectorAll<HTMLElement>('[data-sid]').forEach((el) => {
            el.onclick = async () => {
                const sid = el.dataset.sid!;
                if (sid === '__new__') {
                    try {
                        const res = (await papi('POST', '/api/purchase/suppliers', {
                            name: search.value.trim() || t('pur-supplier-new'),
                        })) as { supplier?: Supplier };
                        onPick(res.supplier);
                    } catch (e) {
                        showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
                        return;
                    }
                } else {
                    onPick(all.find((s) => s.id === sid));
                }
                closeMask('purchase-supplier-mask');
            };
        });
    };
    search.oninput = render;
    papi('GET', '/api/purchase/suppliers')
        .then((d) => {
            all = (d as { suppliers?: Supplier[] }).suppliers || [];
            render();
        })
        .catch(() => {
            listEl.innerHTML = `<div class="state" style="padding:18px;color:var(--ink3);">${escapeHtml(t('pur-error'))}</div>`;
        });
};

// ── 屏3 LINE 一句话记费用(说明 + 内嵌一句话)──────────────────────────
window.openPurchaseLine = function () {
    const inner = `<div class="purm w480"><div class="mh"><div class="t">${escapeHtml(t('pur-line-title'))}</div><div class="x" data-close>×</div></div>
        <div class="mb">
            <div class="step"><span class="n">1</span><div class="tx"><b>${escapeHtml(t('pur-line-s1-b'))}</b>:${escapeHtml(t('pur-line-s1'))}</div></div>
            <div class="step"><span class="n">2</span><div class="tx"><b>${escapeHtml(t('pur-line-s2-b'))}</b>:${escapeHtml(t('pur-line-s2'))}</div></div>
            <div class="step"><span class="n">3</span><div class="tx"><b>${escapeHtml(t('pur-line-s3-b'))}</b>:${escapeHtml(t('pur-line-s3'))}</div></div>
            <div class="field" style="margin-top:6px;"><label>${escapeHtml(t('pur-line-try'))}</label><div class="inp" style="font-weight:400;"><input id="purm-ltext" placeholder="${escapeHtml(t('pur-line-ph'))}"></div></div>
            <div class="note">${escapeHtml(t('pur-line-note'))}</div>
        </div>
        <div class="mf"><button class="btn" data-close>${escapeHtml(t('pur-close'))}</button><button class="btn primary" id="purm-lrec">${escapeHtml(t('pur-line-record'))}</button></div>
    </div>`;
    const mask = openMask('purchase-line-mask', inner);
    if (!mask) return;
    (mask.querySelector('#purm-lrec') as HTMLElement).onclick = async () => {
        const text = (mask.querySelector('#purm-ltext') as HTMLInputElement).value.trim();
        if (!text) {
            closeMask('purchase-line-mask');
            return;
        }
        try {
            await papi('POST', '/api/purchase/expense', { text });
            showToast(t('pur-line-recorded'), 'success');
            closeMask('purchase-line-mask');
            if (window.routeTo) window.routeTo('purchase');
            window.loadPurchaseList?.();
        } catch (e) {
            showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
        }
    };
};
