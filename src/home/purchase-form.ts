// 商户采购 · 复核/录入屏(★唯一录入表单 · 照搬 docs/smart-intake 原型)。桌面左票图右信息/明细/汇总三卡常驻;
// 手机三段连续滚 + 吸顶 Tab + scroll-spy。需复核 banner 消费 confidence_band/field_confidence;字段三态、
// 图查看器拖拽缩放旋转、多文件相册、币种汇率、小类联动、行折扣、手动改额+价内外、硬必填——见各子模块。
// 入口:intake OCR 落此(预填 draft)/ 主屏手动新建 / 详情编辑草稿。存草稿 / 确认入账 → POST /docs(+/post)。
/* global t, escapeHtml, showToast */
import {
    papi,
    activeWsId,
    purchaseErrMsg,
    openPurchasePdf,
    normDetail,
    injectPurBase,
    injectStyle,
    type DocKind,
    type Category,
    type PurchaseSettings,
} from './purchase-common.js';
import { PURCHASE_FORM_CSS } from './purchase-form-css.js';
import { leftColHtml, mountViewer } from './purchase-form-bill.js';
import {
    infoCardHtml,
    validateInfo,
    markErrors,
    isReqEmpty,
    mapConf,
    type MissingField,
} from './purchase-form-info.js';
import {
    linesHtml,
    blankLine,
    computeForm,
    mountLines,
    mergeLines,
    overrideConsistent,
} from './purchase-form-lines.js';
import { totalsCardHtml, totalsHtml, bindTotals } from './purchase-form-totals.js';
import type { DraftIn, FormState } from './purchase-form-types.js';

let st: FormState | null = null;
let pending: DraftIn | null = null;
let settings: PurchaseSettings | null = null;
let cats: Category[] = [];

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

function fromDraft(d: DraftIn): FormState {
    const sup = d.supplier || null;
    const urls: string[] = [];
    if (d.bill_image_local) urls.push(d.bill_image_local);
    else if (d.bill_image_url) urls.push(d.bill_image_url);
    (d.attachments || []).forEach((a) => {
        if (a.kind === 'bill' && a.url && !urls.includes(a.url)) urls.push(a.url);
    });
    return {
        id: d.id || null,
        doc_kind: d.doc_kind || (sup ? 'purchase_invoice' : 'expense'),
        supplierName: (sup && sup.name) || '',
        taxId: (sup && sup.tax_id) || '',
        branchType: (sup && sup.branch_type) || 'none',
        branchNo: (sup && sup.branch_no) || '',
        branchName: '',
        address: (sup && sup.address) || '',
        docNo: d.doc_no || '',
        docDate: d.doc_date || todayIso(),
        dueLabel: d.due_date || '',
        hasVat: d.has_vat !== false,
        paymentStatus: d.payment_status === 'paid' ? 'paid' : 'unpaid',
        requester: d.requester || '',
        currency: d.currency || 'THB',
        fxRate: d.fx_rate != null ? String(d.fx_rate) : '',
        lines: (d.lines && d.lines.length
            ? d.lines
            : [blankLine(settings ? Number(settings.default_vat_rate) || 7 : 7)]
        ).map((l) => ({ ...l })),
        mergeMode: false,
        priceMode: 'exclusive',
        manualOn: false,
        override: { subtotal: 0, discount: 0, vat: 0, grand: 0 },
        aiFields: d.ai_fields || 0,
        dedupeHit: !!d.dedupe_hit,
        confidenceBand: d.confidence_band || 'auto',
        fieldConf: mapConf(d.field_confidence),
        billRef: d.bill_image_ref || '',
        billUrls: urls,
        billIdx: 0,
    };
}

function wsName(): string {
    return (
        (window._userInfo && (window._userInfo as { company_name?: string }).company_name) || '—'
    );
}

const WARN_SVG =
    '<svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/></svg>';

// 需复核 banner:band 非 auto 且有「请确认」字段 → 列出可跳转。
function reviewFields(): MissingField[] {
    const out: MissingField[] = [];
    const map: Record<string, string> = {
        supplier: 'f-supplier',
        doc_date: 'f-docdate',
        doc_no: 'f-taxno',
    };
    for (const k in st!.fieldConf) {
        if (st!.fieldConf[k] === 'fix' && map[k])
            out.push({ field: map[k], label: t('pur-fld-' + k) });
    }
    return out;
}

function bannerInner(items: MissingField[], titleKey: string): string {
    const jumps = items
        .map((f) => `<span class="j" data-jump="${f.field}">${escapeHtml(f.label)}</span>`)
        .join('、');
    return `${WARN_SVG}<div><b>${escapeHtml(t(titleKey, { n: String(items.length) }))}</b> ${jumps}</div>`;
}

function shell(): string {
    const dup = st!.dedupeHit
        ? `<div class="dupbar">${escapeHtml(t('purchase.dup_invoice'))}</div>`
        : '';
    const fx = reviewFields();
    const showBanner = st!.confidenceBand !== 'auto' && fx.length;
    return `<div class="pur f"><div class="wrap">
        <div class="ph">
            <div class="phl"><span class="back" id="pur-back" title="${escapeHtml(t('pur-back'))}" aria-label="${escapeHtml(t('pur-back'))}">‹</span><div><div class="t">${escapeHtml(t('pur-review-title'))}</div><div class="sub">${escapeHtml(st!.supplierName || t('pur-form-sub'))}</div></div></div>
        </div>
        ${dup}
        <div class="vbanner ${showBanner ? 'show' : ''}" id="pur-vbanner">${showBanner ? bannerInner(fx, 'pur-review-n') : ''}</div>
        <div class="ctxbar" id="pur-ctx">
            <div class="wsbar">${escapeHtml(t('pur-ws-for'))} <b>${escapeHtml(wsName())}</b></div>
            <div class="etabs" id="pur-etabs"><button class="on" data-tab="doc">${escapeHtml(t('pur-tab-doc'))}</button><button data-tab="info">${escapeHtml(t('pur-tab-info'))}</button><button data-tab="items">${escapeHtml(t('pur-tab-items'))}</button></div>
        </div>
        <div class="grid">
            ${leftColHtml(st!)}
            <div class="rcol">
                <div id="pane-info">${infoCardHtml(st!)}</div>
                <div id="pane-items">
                    <div class="card"><div class="hd">${escapeHtml(t('pur-lines'))}</div><div class="bd">
                        <div class="seg sm2" id="pur-linemode" style="margin-bottom:12px;"><div class="o ${st!.mergeMode ? '' : 'on'}" data-merge="0">${escapeHtml(t('pur-line-split'))}</div><div class="o ${st!.mergeMode ? 'on' : ''}" data-merge="1">${escapeHtml(t('pur-line-merge'))}</div></div>
                        <div class="infonote">${escapeHtml(t('pur-lines-note'))}</div>
                        <div id="pur-lines">${linesHtml(st!, cats)}</div>
                    </div></div>
                    ${totalsCardHtml(st!)}
                </div>
            </div>
        </div>
        <div class="editfoot"><button class="btn danger" id="pur-delete">${escapeHtml(t('pur-delete'))}</button><button class="btn" id="pur-save-draft2">${escapeHtml(t('pur-save-draft'))}</button><button class="btn primary save" id="pur-post2">${escapeHtml(t('pur-post'))}</button></div>
    </div></div>`;
}

function refreshTotals(): void {
    const el = document.getElementById('pur-totals');
    if (el) el.innerHTML = totalsHtml(st!);
}

function rerender(): void {
    const sec = document.getElementById('page-purchase-form');
    if (!sec) return;
    sec.innerHTML = shell();
    bindShell();
}

function setTop(key: string, val: string): void {
    (st as unknown as Record<string, unknown>)[key] = val;
}

function bindShell(): void {
    document.getElementById('pur-back')!.onclick = () => window.routeTo?.('purchase');
    // 套账切换走顶栏现有切换器(不在表单内放第二个 · 防 ws 不同步)· wsbar 仅只读提示「记账给」。
    mountViewer(st!, rerender);
    mountLines(
        st!,
        cats,
        settings ? Number(settings.default_vat_rate) || 7 : 7,
        settings ? Number(settings.default_wht_service_rate) || 3 : 3,
        refreshTotals
    );
    bindTotals(st!, rerender);
    // 明细 拆分多条/合并记一条:合并 = 不逐项记一条(多行折成单行·净额求和)· 默认拆分。
    document.querySelectorAll<HTMLElement>('#pur-linemode [data-merge]').forEach((el) => {
        el.onclick = () => {
            const merge = el.dataset.merge === '1';
            if (merge === st!.mergeMode) return;
            if (merge) {
                // 进合并:先存原始逐项明细,再折成单行 → 切回拆分能恢复(此前直接覆盖 → 回不去)。
                if (st!.lines.length > 1) {
                    st!.splitLines = st!.lines.map((l) => ({ ...l }));
                    st!.lines = mergeLines(st!.lines);
                }
            } else if (st!.splitLines && st!.splitLines.length) {
                st!.lines = st!.splitLines;
                st!.splitLines = undefined;
            }
            st!.mergeMode = merge;
            rerender();
        };
    });

    const supPick = document.getElementById('pur-supplier-pick');
    if (supPick)
        supPick.onclick = () =>
            window.openPurchaseSupplierPicker?.((s) => {
                const sp = s as {
                    name?: string;
                    tax_id?: string;
                    branch_type?: string;
                    branch_no?: string;
                    address?: string;
                };
                st!.supplierName = sp.name || '';
                st!.taxId = sp.tax_id || '';
                st!.branchType = sp.branch_type || 'none';
                st!.branchNo = sp.branch_no || '';
                st!.address = sp.address || st!.address;
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
    const bt = document.getElementById('pur-branchtype') as HTMLSelectElement | null;
    if (bt)
        bt.onchange = () => {
            st!.branchType = bt.value;
            rerender();
        };
    const cur = document.getElementById('pur-cur') as HTMLSelectElement | null;
    if (cur)
        cur.onchange = () => {
            st!.currency = cur.value;
            rerender();
        };
    // 文本字段(非结构变 · 不重渲免失焦)· 必填字段填了即时清「需补红」。
    const reqKey: Record<string, string> = {
        branchNo: 'branchNo',
        docNo: 'doc_no',
        fxRate: 'fx',
        docDate: 'doc_date',
    };
    document
        .querySelectorAll<HTMLInputElement>('#pane-info [data-fld], #pane-doc [data-fld]')
        .forEach((el) => {
            const f = el.dataset.fld!;
            if (['branchType', 'currency'].includes(f)) return;
            el.oninput = () => {
                setTop(f, el.value);
                const key = reqKey[f];
                if (!key) return;
                const field = el.closest('.field');
                const need = isReqEmpty(st!, key);
                field?.classList.toggle('need', need);
                if (!need) field?.querySelector('.tg-need')?.remove(); // 填了即去「需补」徽章(免文字滞留)
            };
        });
    bindGenReceipt();
    bindBannerJumps();
    bindMobileTabs();
    document.getElementById('pur-delete')!.onclick = () => onDelete();
    document.getElementById('pur-save-draft2')!.onclick = () => submit('draft');
    document.getElementById('pur-post2')!.onclick = () => onPost();
}

function bindGenReceipt(): void {
    const genBtn = document.getElementById('pur-gen-receipt') as HTMLButtonElement | null;
    if (!genBtn) return;
    genBtn.onclick = async () => {
        const id = st && st.id;
        if (!id) return showToast(t('pur-receipt-need-save'), 'error');
        try {
            genBtn.disabled = true;
            await papi('POST', `/api/purchase/docs/${id}/substitute-receipt`, {
                workspace_client_id: activeWsId(),
            });
            showToast(t('pur-receipt-generated'), 'success');
            await openPurchasePdf(`/api/purchase/docs/${id}/document.pdf?kind=substitute_receipt`);
        } catch (e) {
            showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
        } finally {
            genBtn.disabled = false;
        }
    };
}

function bindBannerJumps(): void {
    document.querySelectorAll<HTMLElement>('#pur-vbanner [data-jump]').forEach((j) => {
        j.onclick = () => {
            const el = document.getElementById(j.dataset.jump!);
            if (!el) return;
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            el.querySelector('input')?.focus();
        };
    });
}

// 手机:点 Tab 平滑滚到该段 + 滚动联动高亮(scroll-spy)。桌面 etabs 不显故无效。
// 真 app 的滚动容器是 window/document(无 #content · 原型才有)→ 监听 window scroll。
let mobileSpy: (() => void) | null = null;
function bindMobileTabs(): void {
    const tabs = document.getElementById('pur-etabs');
    if (!tabs) return;
    tabs.querySelectorAll<HTMLElement>('button').forEach((b) => {
        b.onclick = () =>
            document
                .getElementById('pane-' + b.dataset.tab)
                ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    if (mobileSpy) window.removeEventListener('scroll', mobileSpy);
    mobileSpy = () => {
        const tb = document.getElementById('pur-etabs');
        if (!tb) {
            if (mobileSpy) window.removeEventListener('scroll', mobileSpy);
            return;
        }
        const ids = ['doc', 'info', 'items'];
        let curId = 'doc';
        for (const id of ids) {
            const r = document.getElementById('pane-' + id)?.getBoundingClientRect();
            if (r && r.top < 160) curId = id;
        }
        tb.querySelectorAll<HTMLElement>('button').forEach((x) =>
            x.classList.toggle('on', x.dataset.tab === curId)
        );
    };
    window.addEventListener('scroll', mobileSpy, { passive: true });
}

function onPost(): void {
    if (st!.manualOn && !overrideConsistent(st!)) {
        // 手动改额一致性不过 → 拦(后端也会再校验借贷平)
        showToast(t('pur-consist-block'), 'error');
        return;
    }
    const miss = validateInfo(st!);
    markErrors(miss);
    if (miss.length) {
        const vb = document.getElementById('pur-vbanner');
        if (vb) {
            vb.innerHTML = bannerInner(miss, 'pur-miss-n');
            vb.classList.add('show');
            bindBannerJumps();
            vb.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        return;
    }
    submit('posted');
}

async function onDelete(): Promise<void> {
    if (!st!.id) return window.routeTo?.('purchase');
    if (typeof window.showConfirm === 'function') {
        const okc = await window.showConfirm(t('pur-delete-confirm'));
        if (!okc) return;
    }
    try {
        await papi('DELETE', `/api/purchase/docs/${st!.id}?workspace_client_id=${activeWsId()}`);
        showToast(t('pur-deleted-ok'), 'success');
        window.routeTo?.('purchase');
    } catch (e) {
        showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
    }
}

function payload(status: 'draft' | 'posted'): unknown {
    const r = computeForm(st!);
    const base: Record<string, unknown> = {
        workspace_client_id: activeWsId(),
        doc_kind: st!.doc_kind,
        supplier: {
            name: st!.supplierName,
            tax_id: st!.taxId,
            branch_type: st!.branchType,
            branch_no: st!.branchNo,
            branch_name: st!.branchName,
            address: st!.address,
        },
        doc_no: st!.docNo,
        doc_date: st!.docDate,
        has_vat: st!.hasVat,
        currency: st!.currency,
        fx_rate: st!.currency !== 'THB' ? Number(st!.fxRate) || 1 : 1,
        requester: st!.requester,
        payment_status: st!.paymentStatus,
        price_mode: st!.priceMode,
        lines: st!.lines,
        subtotal: r.subtotal,
        discount_total: r.discount_total,
        vat_amount: r.vat_amount,
        wht_amount: r.wht_amount,
        rounding: r.rounding,
        grand_total: r.grand_total,
        net_payable: r.net_payable,
        bill_image_ref: st!.billRef || undefined,
        status,
    };
    if (st!.manualOn) {
        // 键名对齐后端契约(routes/purchase_routes.py DocIn.amount_override)。
        base.amount_override = {
            override_on: true,
            subtotal: st!.override.subtotal,
            discount_total: st!.override.discount,
            vat_amount: st!.override.vat,
            grand_total: st!.override.grand,
        };
    }
    return base;
}

async function submit(status: 'draft' | 'posted'): Promise<void> {
    try {
        const body = payload(status);
        const path = st!.id ? `/api/purchase/docs/${st!.id}` : '/api/purchase/docs';
        // 已存在草稿走 PUT 原地更新(防保存时新建重复单),新单才 POST。
        const res = (await papi(st!.id ? 'PUT' : 'POST', path, body)) as { doc?: { id?: string } };
        const docId = st!.id || (res.doc && res.doc.id);
        if (status === 'posted' && docId)
            await papi('POST', `/api/purchase/docs/${docId}/post`, {});
        showToast(t(status === 'posted' ? 'pur-posted-ok' : 'pur-draft-ok'), 'success');
        window.routeTo?.('purchase');
    } catch (e) {
        showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
    }
}

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
    const detailP =
        draft.id && !draft.lines
            ? papi('GET', `/api/purchase/docs/${draft.id}`).catch(() => null)
            : Promise.resolve(null);
    const [, det] = await Promise.all([ensureRefs(), detailP]);
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
