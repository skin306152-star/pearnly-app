// 商户采购 · 屏10 费用/进项录入(★最重 · 唯一录入/编辑表单)· 照搬设计稿 10-费用进项录入。
// 桌面两栏(票图+凭据 左 / 信息+明细+合计 右)· 手机竖向堆叠。明细行 商品|服务 切换联动 WHT,
// 即时重算(税前→VAT→含税→WHT→实付 · purchase-calc 逐分取整)· AI 预填绿标 / 未抽到黄底 · 重复票红条。
// 入口:① intake OCR 落此(预填 draft)②主屏手动新建 ③详情编辑草稿。存草稿 / 确认入账 → POST /docs(+/post)。
/* global t, escapeHtml, showToast */
import {
    papi,
    activeWsId,
    purchaseErrMsg,
    openPurchasePdf,
    fmtMoney,
    normDetail,
    injectPurBase,
    injectStyle,
    type DocKind,
    type DocLine,
    type Category,
    type PurchaseSettings,
} from './purchase-common.js';
import { computePurchaseTotals } from './purchase-calc.js';
import { PURCHASE_FORM_CSS } from './purchase-form-css.js';

interface DraftIn {
    id?: string;
    doc_kind?: DocKind;
    supplier?: { name?: string; tax_id?: string; branch_type?: string } | null;
    doc_no?: string | null;
    doc_date?: string | null;
    due_date?: string | null;
    has_vat?: boolean;
    currency?: string;
    requester?: string | null;
    payment_status?: string;
    lines?: DocLine[];
    ai_fields?: number;
    dedupe_hit?: boolean;
}

interface FormState {
    id: string | null;
    doc_kind: DocKind;
    supplierName: string;
    taxId: string;
    branchType: string;
    address: string;
    docNo: string;
    docDate: string;
    dueLabel: string;
    hasVat: boolean;
    paymentStatus: 'unpaid' | 'paid';
    requester: string;
    currency: string;
    lines: DocLine[];
    aiFields: number;
    dedupeHit: boolean;
}

let st: FormState | null = null;
let pending: DraftIn | null = null;
let settings: PurchaseSettings | null = null;
let cats: Category[] = [];

function blankLine(): DocLine {
    return {
        item_type: 'goods',
        product_id: null,
        product_matched: false,
        description: '',
        qty: 1,
        unit: null,
        unit_price: 0,
        discount: 0,
        vat_rate: settings ? Number(settings.default_vat_rate) || 7 : 7,
        wht_rate: 0,
    };
}

function fromDraft(d: DraftIn): FormState {
    const sup = d.supplier || null;
    return {
        id: d.id || null,
        doc_kind: d.doc_kind || (sup ? 'purchase_invoice' : 'expense'),
        supplierName: (sup && sup.name) || '',
        taxId: (sup && sup.tax_id) || '',
        branchType: (sup && sup.branch_type) || 'none',
        address: '',
        docNo: d.doc_no || '',
        docDate: d.doc_date || todayIso(),
        dueLabel: d.due_date || '',
        hasVat: d.has_vat !== false,
        paymentStatus: d.payment_status === 'paid' ? 'paid' : 'unpaid',
        requester: d.requester || '',
        currency: d.currency || 'THB',
        lines: (d.lines && d.lines.length ? d.lines : [blankLine()]).map((l) => ({ ...l })),
        aiFields: d.ai_fields || 0,
        dedupeHit: !!d.dedupe_hit,
    };
}

function todayIso(): string {
    const n = new Date();
    return (
        n.getFullYear() +
        '-' +
        String(n.getMonth() + 1).padStart(2, '0') +
        '-' +
        String(n.getDate()).padStart(2, '0')
    );
}

function catOptions(selected: string | null | undefined): string {
    const opts: string[] = [`<option value="">${escapeHtml(t('pur-cat-none'))}</option>`];
    cats.forEach((c) => {
        const kids = c.children || [];
        if (!kids.length) {
            opts.push(opt(c.id, c.name, selected));
        } else {
            kids.forEach((k) => opts.push(opt(k.id, c.name + ' › ' + k.name, selected)));
        }
    });
    return opts.join('');
}
function opt(v: string, label: string, sel: string | null | undefined): string {
    return `<option value="${escapeHtml(v)}" ${v === sel ? 'selected' : ''}>${escapeHtml(label)}</option>`;
}

function lineTotal(l: DocLine): number {
    return Math.max(0, Number(l.qty) * Number(l.unit_price) - Number(l.discount || 0));
}

function lineHtml(l: DocLine, i: number): string {
    const isSvc = l.item_type === 'service';
    const extra = isSvc
        ? `<span class="pill warn">${escapeHtml(t('pur-svc-wht'))} ${l.wht_rate}%</span>`
        : l.product_matched
          ? `<span class="pill ok">${escapeHtml(t('pur-matched'))}</span> · <span class="link" data-stock="${i}">${escapeHtml(t('pur-stock-in'))} ✓</span>`
          : `<span class="pill warn">${escapeHtml(t('pur-unmatched'))}</span> · <span class="link" data-match="${i}">${escapeHtml(t('pur-match'))}</span>`;
    return `<div class="item" data-line="${i}">
        <div class="irow1">
            <div class="seg sm2"><div class="o ${isSvc ? '' : 'on'}" data-it="${i}:goods">${escapeHtml(t('pur-goods'))}</div><div class="o ${isSvc ? 'on' : ''}" data-it="${i}:service">${escapeHtml(t('pur-service'))}</div></div>
            <div class="iname"><input class="fin" data-fld="${i}:description" value="${escapeHtml(l.description)}" placeholder="${escapeHtml(t('pur-line-name'))}"></div>
            <span class="x" data-del="${i}">×</span>
        </div>
        <div class="igrid">
            <div class="f"><label>${escapeHtml(t('pur-qty'))}</label><div class="inp sm"><input class="fin tnum" type="number" data-fld="${i}:qty" value="${l.qty}"></div></div>
            <div class="f"><label>${escapeHtml(t('pur-price'))}</label><div class="inp sm"><input class="fin tnum" type="number" data-fld="${i}:unit_price" value="${l.unit_price}"></div></div>
            <div class="f"><label>${escapeHtml(t('pur-category'))}</label><div class="inp sm"><select class="fsel" data-fld="${i}:category_id">${catOptions(l.category_id)}</select></div></div>
            <div class="f"><label>VAT</label><div class="inp sm"><select class="fsel" data-fld="${i}:vat_rate"><option value="0" ${l.vat_rate == 0 ? 'selected' : ''}>0%</option><option value="7" ${l.vat_rate == 7 ? 'selected' : ''}>7%</option></select></div></div>
            <div class="f"><label>${escapeHtml(t('pur-line-total'))}</label><div class="inp sm ro tnum" data-lt="${i}">฿${fmtMoney(lineTotal(l))}</div></div>
        </div>
        <div class="iextra">${extra}</div>
    </div>`;
}

function totalsHtml(): string {
    const r = computePurchaseTotals(st!.lines, {});
    const vatRow = st!.hasVat
        ? `<div class="sum"><span>${escapeHtml(t('pur-vat-in'))} <span class="pill ok">${escapeHtml(t('pur-creditable'))}</span></span><span class="tnum tax">+฿${r.vat_amount}</span></div>`
        : '';
    const whtRow =
        Number(r.wht_amount) > 0
            ? `<div class="sum"><span>${escapeHtml(t('pur-wht'))} <span class="pill warn">${escapeHtml(t('pur-withheld'))}</span></span><span class="tnum wht">−฿${r.wht_amount}</span></div>`
            : '';
    return `<div class="sum"><span>${escapeHtml(t('pur-subtotal'))}</span><span class="tnum">฿${r.subtotal}</span></div>
        <div class="sum"><span>${escapeHtml(t('pur-discount'))}</span><span class="tnum">−฿${r.discount_total}</span></div>
        ${vatRow}
        <div class="sum mid"><span>${escapeHtml(t('pur-grand'))}</span><span class="tnum">฿${r.grand_total}</span></div>
        ${whtRow}
        <div class="sum tot"><span>${escapeHtml(t('pur-net-payable'))}</span><span class="tnum">฿${r.net_payable}</span></div>`;
}

function leftCol(): string {
    const aiMark = st!.aiFields
        ? `<span class="aimark">${escapeHtml(t('pur-ai-read'))} ${st!.aiFields}</span>`
        : '';
    return `<div class="col">
        <div class="card"><div class="hd">${escapeHtml(t('pur-bill'))}</div><div class="bd">
            <div class="img">${ICON_DOC}${aiMark}</div>
            <div class="seg2"><button class="btn sm" id="pur-reshoot">${escapeHtml(t('pur-reshoot'))}</button><button class="btn sm" id="pur-zoom">${escapeHtml(t('pur-zoom'))}</button></div>
        </div></div>
        <div class="card"><div class="hd">${escapeHtml(t('pur-vouchers-hd'))}</div><div class="bd">
            <div class="hint">${escapeHtml(t('pur-sub-receipt-hint'))}</div>
            <button class="btn full ghost mt" id="pur-gen-receipt" style="margin-bottom:8px;">+ ${escapeHtml(t('pur-gen-receipt'))}</button>
            <button class="btn full ghost" id="pur-attach">+ ${escapeHtml(t('pur-attach'))}</button>
            <div class="field mt"><label>${escapeHtml(t('pur-requester'))}</label><div class="inp"><input class="fin" data-fld="requester" value="${escapeHtml(st!.requester)}" placeholder="—"></div></div>
        </div></div>
    </div>`;
}

function infoCard(): string {
    const k = st!.doc_kind;
    const supMark = st!.supplierName
        ? `<span class="aimark">${escapeHtml(t('pur-ai-supplier'))}</span>`
        : '';
    const taxCls = st!.taxId ? 'inp tnum ai' : 'inp tnum todo';
    return `<div class="card"><div class="hd">${escapeHtml(t('pur-doc-info'))}</div><div class="bd">
        <div class="field"><label>${escapeHtml(t('pur-type'))}</label><div class="seg" id="pur-kind">
            <div class="o ${k === 'purchase_invoice' ? 'on' : ''}" data-kind="purchase_invoice">${escapeHtml(t('pur-kind-invoice'))}</div>
            <div class="o ${k === 'expense' ? 'on' : ''}" data-kind="expense">${escapeHtml(t('pur-kind-expense'))}</div>
            <div class="o ${k === 'purchase_order' ? 'on' : ''}" data-kind="purchase_order">${escapeHtml(t('pur-kind-order'))}</div></div></div>
        <div class="field"><label>${escapeHtml(t('pur-supplier'))} ${supMark}</label><div class="inp pick" id="pur-supplier-pick">${escapeHtml(st!.supplierName || t('pur-supplier-choose'))} <span style="color:var(--ink3)">${escapeHtml(t('pur-switch'))} ▾</span></div></div>
        <div class="two">
            <div class="field"><label>${escapeHtml(t('pur-tax-id'))}</label><div class="${taxCls}"><input class="fin tnum" data-fld="taxId" value="${escapeHtml(st!.taxId)}" placeholder="13"></div></div>
            <div class="field"><label>${escapeHtml(t('pur-branch'))}</label><div class="inp"><select class="fsel" data-fld="branchType"><option value="head_office" ${st!.branchType === 'head_office' ? 'selected' : ''}>${escapeHtml(t('pur-branch-head'))}</option><option value="branch" ${st!.branchType === 'branch' ? 'selected' : ''}>${escapeHtml(t('pur-branch-sub'))}</option><option value="none" ${st!.branchType === 'none' ? 'selected' : ''}>${escapeHtml(t('pur-branch-na'))}</option></select></div></div>
        </div>
        <div class="field"><label>${escapeHtml(t('pur-address'))}</label><div class="inp"><input class="fin" data-fld="address" value="${escapeHtml(st!.address)}" placeholder="—"></div></div>
        <div class="two">
            <div class="field"><label>${escapeHtml(t('pur-doc-date'))}</label><div class="inp"><input class="fin tnum" type="date" data-fld="docDate" value="${escapeHtml(st!.docDate)}"></div></div>
            <div class="field"><label>${escapeHtml(t('pur-doc-no'))}</label><div class="inp"><input class="fin" data-fld="docNo" value="${escapeHtml(st!.docNo)}"></div></div>
        </div>
        <div class="two">
            <div class="field"><label>${escapeHtml(t('pur-has-vat'))}</label><div class="seg sm2" id="pur-hasvat"><div class="o ${st!.hasVat ? 'on' : ''}" data-vat="1">${escapeHtml(t('pur-yes'))}</div><div class="o ${st!.hasVat ? '' : 'on'}" data-vat="0">${escapeHtml(t('pur-no'))}</div></div></div>
            <div class="field"><label>${escapeHtml(t('pur-pay-status'))}</label><div class="seg sm2" id="pur-pay"><div class="o ${st!.paymentStatus === 'paid' ? 'on' : ''}" data-pay="paid">${escapeHtml(t('pur-pay-paid'))}</div><div class="o ${st!.paymentStatus === 'unpaid' ? 'on' : ''}" data-pay="unpaid">${escapeHtml(t('pur-pay-ap'))}</div></div></div>
        </div>
    </div></div>`;
}

function rightCol(): string {
    return `<div class="col">
        ${infoCard()}
        <div class="card"><div class="hd">${escapeHtml(t('pur-lines'))} <span class="muted">${escapeHtml(t('pur-currency'))} ${escapeHtml(st!.currency)} ▾</span></div><div class="bd" id="pur-lines">
            ${st!.lines.map((l, i) => lineHtml(l, i)).join('')}
            <button class="btn full ghost" id="pur-add-line">+ ${escapeHtml(t('pur-add-line'))}</button>
        </div></div>
        <div class="card"><div class="hd">${escapeHtml(t('pur-totals'))}</div><div class="bd" id="pur-totals">${totalsHtml()}</div></div>
    </div>`;
}

function shell(): string {
    const dup = st!.dedupeHit
        ? `<div class="dupbar">${escapeHtml(t('purchase.dup_invoice'))}</div>`
        : '';
    return `<div class="pur f"><div class="wrap">
        <div class="back" id="pur-back">‹ ${escapeHtml(t('pur-back'))}</div>
        <div class="ph">
            <div><div class="t">${escapeHtml(t('pur-form-title'))}</div><div class="sub">${escapeHtml(t('pur-form-sub'))}</div></div>
            <div class="acts"><button class="btn" id="pur-save-draft">${escapeHtml(t('pur-save-draft'))}</button><button class="btn primary" id="pur-post">${escapeHtml(t('pur-post'))}</button></div>
        </div>
        ${dup}
        <div class="wsbar">${escapeHtml(t('pur-ws-for'))} <b id="pur-ws-name">${escapeHtml(wsName())}</b> · <span class="link" id="pur-ws-switch">${escapeHtml(t('pur-ws-switch'))}</span></div>
        <div class="grid">${leftCol()}${rightCol()}</div>
    </div></div>`;
}

function wsName(): string {
    return (
        (window._userInfo && (window._userInfo as { company_name?: string }).company_name) || '—'
    );
}

const ICON_DOC =
    '<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2z"/><line x1="8" y1="8" x2="16" y2="8"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="8" y1="16" x2="13" y2="16"/></svg>';

function refreshLines(): void {
    const box = document.getElementById('pur-lines');
    if (box) {
        box.innerHTML =
            st!.lines.map((l, i) => lineHtml(l, i)).join('') +
            `<button class="btn full ghost" id="pur-add-line">+ ${escapeHtml(t('pur-add-line'))}</button>`;
    }
    refreshTotals();
    bindLines();
}

function refreshTotals(): void {
    const el = document.getElementById('pur-totals');
    if (el) el.innerHTML = totalsHtml();
}

function setField(path: string, value: string): void {
    const [iStr, key] = path.split(':');
    if (key === undefined) {
        (st as unknown as Record<string, unknown>)[iStr] = value;
        return;
    }
    const l = st!.lines[Number(iStr)] as unknown as Record<string, unknown>;
    if (key === 'qty' || key === 'unit_price' || key === 'discount' || key === 'vat_rate') {
        l[key] = Number(value) || 0;
    } else {
        l[key] = value;
    }
}

function bindLines(): void {
    document.querySelectorAll<HTMLInputElement>('#pur-lines [data-fld]').forEach((el) => {
        el.oninput = () => {
            setField(el.dataset.fld!, el.value);
            const i = el.dataset.fld!.split(':')[0];
            const lt = document.querySelector<HTMLElement>(`[data-lt="${i}"]`);
            if (lt) lt.textContent = '฿' + fmtMoney(lineTotal(st!.lines[Number(i)]));
            refreshTotals();
        };
    });
    document.querySelectorAll<HTMLElement>('#pur-lines [data-it]').forEach((el) => {
        el.onclick = () => {
            const [i, it] = el.dataset.it!.split(':');
            const l = st!.lines[Number(i)];
            l.item_type = it as 'goods' | 'service';
            l.wht_rate =
                it === 'service'
                    ? settings
                        ? Number(settings.default_wht_service_rate) || 3
                        : 3
                    : 0;
            refreshLines();
        };
    });
    document.querySelectorAll<HTMLElement>('#pur-lines [data-del]').forEach((el) => {
        el.onclick = () => {
            if (st!.lines.length <= 1) return;
            st!.lines.splice(Number(el.dataset.del), 1);
            refreshLines();
        };
    });
    document.querySelectorAll<HTMLElement>('#pur-lines [data-match]').forEach((el) => {
        el.onclick = () => {
            const i = Number(el.dataset.match);
            window.openPurchaseMatch?.(st!.lines[i], (res) => {
                const r = res as { product_id?: string };
                st!.lines[i].product_id = r.product_id || 'matched';
                st!.lines[i].product_matched = true;
                refreshLines();
            });
        };
    });
    const add = document.getElementById('pur-add-line');
    if (add)
        add.onclick = () => {
            st!.lines.push(blankLine());
            refreshLines();
        };
}

function bindShell(): void {
    document.getElementById('pur-back')!.onclick = () => window.routeTo?.('purchase');
    document.getElementById('pur-ws-switch')!.onclick = () =>
        document.getElementById('workspace-switcher-root')?.querySelector('button')?.click();
    const supPick = document.getElementById('pur-supplier-pick');
    if (supPick)
        supPick.onclick = () =>
            window.openPurchaseSupplierPicker?.((s) => {
                const sp = s as { name?: string; tax_id?: string; branch_type?: string };
                st!.supplierName = sp.name || '';
                st!.taxId = sp.tax_id || '';
                st!.branchType = sp.branch_type || 'none';
                rerender();
            });
    document.querySelectorAll<HTMLElement>('#pur-kind [data-kind]').forEach((el) => {
        el.onclick = () => {
            st!.doc_kind = el.dataset.kind as DocKind;
            rerender();
        };
    });
    document.querySelectorAll<HTMLElement>('#pur-hasvat [data-vat]').forEach((el) => {
        el.onclick = () => {
            st!.hasVat = el.dataset.vat === '1';
            rerender();
        };
    });
    document.querySelectorAll<HTMLElement>('#pur-pay [data-pay]').forEach((el) => {
        el.onclick = () => {
            st!.paymentStatus = el.dataset.pay as 'paid' | 'unpaid';
            rerender();
        };
    });
    document
        .querySelectorAll<HTMLInputElement>('.pur .bd > [data-fld], .pur .field [data-fld]')
        .forEach((el) => {
            if (el.closest('#pur-lines')) return;
            el.oninput = () => setField(el.dataset.fld!, el.value);
            el.onchange = () => setField(el.dataset.fld!, el.value);
        });
    // F3b · 替代收据:存单后调后端生成凭据 PDF 并打开(禁连点 · 三态反馈)。需单据已存(有 id)。
    const genBtn = document.getElementById('pur-gen-receipt') as HTMLButtonElement | null;
    if (genBtn)
        genBtn.onclick = async () => {
            const id = st && st.id;
            if (!id) return showToast(t('pur-receipt-need-save'), 'error');
            genBtn.disabled = true;
            try {
                await papi('POST', `/api/purchase/docs/${id}/substitute-receipt`, {
                    workspace_client_id: activeWsId(),
                });
                showToast(t('pur-receipt-generated'), 'success');
                await openPurchasePdf(
                    `/api/purchase/docs/${id}/document.pdf?kind=substitute_receipt`
                );
            } catch (e) {
                showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
            } finally {
                genBtn.disabled = false;
            }
        };
    const save = document.getElementById('pur-save-draft');
    if (save) save.onclick = () => submit('draft');
    const post = document.getElementById('pur-post');
    if (post) post.onclick = () => submit('posted');
    bindLines();
}

function rerender(): void {
    const sec = document.getElementById('page-purchase-form');
    if (sec) sec.innerHTML = shell();
    bindShell();
}

function payload(status: 'draft' | 'posted'): unknown {
    const r = computePurchaseTotals(st!.lines, {});
    return {
        workspace_client_id: activeWsId(),
        doc_kind: st!.doc_kind,
        supplier: {
            name: st!.supplierName,
            tax_id: st!.taxId,
            branch_type: st!.branchType,
            address: st!.address,
        },
        doc_no: st!.docNo,
        doc_date: st!.docDate,
        has_vat: st!.hasVat,
        currency: st!.currency,
        requester: st!.requester,
        payment_status: st!.paymentStatus,
        lines: st!.lines,
        subtotal: r.subtotal,
        discount_total: r.discount_total,
        vat_amount: r.vat_amount,
        wht_amount: r.wht_amount,
        rounding: r.rounding,
        grand_total: r.grand_total,
        net_payable: r.net_payable,
        status,
    };
}

async function submit(status: 'draft' | 'posted'): Promise<void> {
    try {
        const res = (await papi('POST', '/api/purchase/docs', payload(status))) as {
            doc?: { id?: string };
        };
        const id = res.doc && res.doc.id;
        if (status === 'posted' && id) await papi('POST', `/api/purchase/docs/${id}/post`, {});
        showToast(t(status === 'posted' ? 'pur-posted-ok' : 'pur-draft-ok'), 'success');
        window.routeTo?.('purchase');
    } catch (e) {
        showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
    }
}

// 设置 + 科目两个独立 GET 并行拉(互不依赖)· 各自兜底,任一失败用空/默认不阻塞表单。
async function ensureRefs(): Promise<void> {
    const needSettings = !settings;
    const needCats = !cats.length;
    if (!needSettings && !needCats) return;
    const [s, c] = await Promise.all([
        needSettings
            ? papi('GET', '/api/purchase/settings').catch(() => null)
            : Promise.resolve(settings),
        needCats
            ? papi('GET', '/api/purchase/categories').catch(() => ({ categories: [] }))
            : Promise.resolve({ categories: cats }),
    ]);
    if (needSettings) settings = s as PurchaseSettings | null;
    if (needCats) cats = (c as { categories?: Category[] }).categories || [];
}

// 跨屏唤起:从主屏「拍进项票」(draft)/ 编辑草稿(id)/ 手动新建(都空)进入。
window.openPurchaseForm = function (id, draft) {
    if (draft) pending = draft as DraftIn;
    else if (id) pending = { id };
    else pending = {};
    window.routeTo?.('purchase-form');
};

window.loadPurchaseForm = async function () {
    const sec = document.getElementById('page-purchase-form');
    if (!sec) return;
    injectPurBase();
    injectStyle('pur-form-css', PURCHASE_FORM_CSS);
    const draft = pending || {};
    pending = null;
    // 参照(设置/科目)与草稿详情互不依赖 → 并行拉,省串行往返。
    const detailP =
        draft.id && !draft.lines
            ? papi('GET', `/api/purchase/docs/${draft.id}`).catch(() => null)
            : Promise.resolve(null);
    const [, det] = await Promise.all([ensureRefs(), detailP]);
    // 编辑既有草稿:后端 {doc,lines,attachments} → normDetail → 结构兼容 DraftIn 喂 fromDraft。
    st = fromDraft(
        draft.id && !draft.lines
            ? det
                ? (normDetail(det as Record<string, unknown>) as unknown as DraftIn)
                : {}
            : draft
    );
    sec.innerHTML = shell();
    bindShell();
};
