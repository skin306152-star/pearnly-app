// 商户采购 · 待归类收件箱(F13 · 长尾安全网)· 拿不准/低置信/糊图的票都落这,绝不静默丢错。
// 每条 = 票图 + 智能猜测 + 关键字段(供应商/金额/日期,缺则「未识别」)+ 一排归类按钮:
//   记进项/记费用 → 后端据 raw 建草稿单 → 开录入屏确认;这是销项/银行单 → 移出去对应模块;不是票 → 忽略。
// 单面板分层(DESIGN_LANGUAGE)· 四态(loading/空/错误/离线)· 每动作三态反馈。
/* global t, escapeHtml, showToast */
import {
    papi,
    activeWsId,
    purchaseErrMsg,
    fmtBaht,
    fmtMonthDay,
    injectPurBase,
    injectStyle,
} from './purchase-common.js';

interface InboxRaw {
    seller_name?: string;
    seller_tax?: string;
    total_amount?: string | number;
    subtotal?: string | number;
    date?: string;
    invoice_number?: string;
}
interface InboxItem {
    id: string;
    source: string;
    raw: InboxRaw;
    image_url: string | null;
    ai_guess: { kind?: string; route?: string; confidence?: string };
    created_at: string | null;
}

const PAGE_CSS = `
.pur.ibx .wrap{max-width:760px;}
.pur.ibx .phd{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:18px 20px;border-bottom:1px solid var(--line,#ECECE7);}
.pur.ibx .phd .t{font-size:21px;font-weight:700;}
.pur.ibx .phd .s{color:var(--ink2,#64748B);font-size:13px;margin-top:3px;}
.pur.ibx .phd .cnt{flex:0 0 auto;text-align:right;}
.pur.ibx .phd .cnt .n{font-size:26px;font-weight:740;line-height:1;}
.pur.ibx .phd .cnt .l{font-size:11.5px;color:var(--ink3,#94A3B8);margin-top:3px;}
.pur.ibx .item{display:flex;gap:14px;padding:16px 20px;border-bottom:1px solid #F1F1EC;}
.pur.ibx .item:last-child{border-bottom:0;}
.pur.ibx .thumb{width:56px;height:56px;flex:0 0 56px;border-radius:10px;background:#F4F4F0;border:1px solid var(--line,#ECECE7);object-fit:cover;display:flex;align-items:center;justify-content:center;color:var(--ink3,#94A3B8);}
.pur.ibx .body{flex:1;min-width:0;}
.pur.ibx .meta{font-size:13.5px;}
.pur.ibx .meta .nm{font-weight:600;}
.pur.ibx .meta .amt{font-weight:700;}
.pur.ibx .miss{color:var(--ink3,#94A3B8);}
.pur.ibx .guess{display:inline-flex;align-items:center;gap:6px;margin-top:5px;font-size:12px;color:#1D4ED8;background:#EFF4FF;border-radius:999px;padding:3px 9px;}
.pur.ibx .src{font-size:11.5px;color:var(--ink3,#94A3B8);margin-left:8px;}
.pur.ibx .acts{display:flex;flex-wrap:wrap;gap:7px;margin-top:11px;}
.pur.ibx .acts .b{border:1px solid var(--line,#ECECE7);background:#fff;border-radius:9px;padding:6px 11px;font-size:12.5px;cursor:pointer;font-weight:600;}
.pur.ibx .acts .b.pri{background:var(--blue,#2563EB);border-color:var(--blue,#2563EB);color:#fff;}
.pur.ibx .acts .b.warn{color:var(--ink2,#64748B);}
.pur.ibx .acts .b[disabled]{opacity:.5;cursor:default;}
.pur.ibx .state{padding:56px 20px;text-align:center;color:var(--ink2,#64748B);font-size:14px;}
.pur.ibx .state .rt{margin-top:12px;border:1px solid var(--line,#ECECE7);background:#fff;border-radius:9px;padding:7px 14px;font-size:13px;cursor:pointer;}
`;

let items: InboxItem[] = [];

function kindLabel(g: InboxItem['ai_guess']): string {
    const k = g && g.kind;
    if (k === 'purchase_invoice') return t('pur-kind-invoice');
    if (k === 'expense') return t('pur-kind-expense');
    if (k === 'sales') return t('pur-inbox-guess-sales');
    return t('pur-inbox-guess-unknown');
}

function amountOf(r: InboxRaw): string {
    const v = r.total_amount ?? r.subtotal;
    return v != null && Number(v) > 0 ? fmtBaht(v) : '';
}

function itemHtml(it: InboxItem): string {
    const r = it.raw || {};
    const name = (r.seller_name || '').trim();
    const amt = amountOf(r);
    const date = r.date ? fmtMonthDay(r.date) : '';
    const srcKey = it.source === 'line' ? 'pur-src-line' : 'pur-src-photo';
    const thumb = it.image_url
        ? `<img class="thumb" src="${escapeHtml(it.image_url)}" alt="">`
        : `<div class="thumb">≈</div>`;
    const nameHtml = name
        ? `<span class="nm">${escapeHtml(name)}</span>`
        : `<span class="nm miss">${escapeHtml(t('pur-inbox-unrecognized'))}</span>`;
    const amtHtml = amt
        ? ` · <span class="amt">${amt}</span>`
        : ` · <span class="miss">${escapeHtml(t('pur-inbox-no-amount'))}</span>`;
    const dateHtml = date ? `<span class="src">${escapeHtml(date)}</span>` : '';
    return `<div class="item" data-id="${escapeHtml(it.id)}">
        ${thumb}
        <div class="body">
            <div class="meta">${nameHtml}${amtHtml}${dateHtml}</div>
            <div class="guess">${escapeHtml(t('pur-inbox-guess'))}: ${escapeHtml(kindLabel(it.ai_guess))}<span class="src">${escapeHtml(t(srcKey))}</span></div>
            <div class="acts">
                <button class="b pri" data-act="purchase">${escapeHtml(t('pur-inbox-act-purchase'))}</button>
                <button class="b" data-act="expense">${escapeHtml(t('pur-inbox-act-expense'))}</button>
                <button class="b" data-act="sales">${escapeHtml(t('pur-inbox-act-sales'))}</button>
                <button class="b" data-act="recon">${escapeHtml(t('pur-inbox-act-recon'))}</button>
                <button class="b warn" data-act="dismiss">${escapeHtml(t('pur-inbox-act-dismiss'))}</button>
            </div>
        </div>
    </div>`;
}

function listHtml(): string {
    if (!items.length) return `<div class="state">${escapeHtml(t('pur-inbox-empty'))}</div>`;
    return items.map(itemHtml).join('');
}

function shell(): string {
    return `<div class="pur ibx"><div class="wrap">
        <div class="panel">
            <div class="phd">
                <div><div class="t">${escapeHtml(t('pur-inbox-title'))}</div>
                <div class="s">${escapeHtml(t('pur-inbox-sub'))}</div></div>
                ${items.length ? `<div class="cnt"><div class="n tnum">${items.length}</div><div class="l">${escapeHtml(t('pur-inbox-pending-unit'))}</div></div>` : ''}
            </div>
            <div id="ibx-list">${listHtml()}</div>
        </div>
    </div></div>`;
}

async function resolve(
    id: string,
    action: string,
    btns: NodeListOf<HTMLButtonElement>
): Promise<void> {
    btns.forEach((b) => (b.disabled = true));
    try {
        const res = (await papi('POST', `/api/purchase/inbox/${id}/resolve`, {
            action,
            workspace_client_id: activeWsId(),
        })) as { doc_id?: string };
        items = items.filter((x) => x.id !== id);
        const listEl = document.getElementById('ibx-list');
        if (listEl) listEl.innerHTML = listHtml();
        bindItems();
        if ((action === 'purchase' || action === 'expense') && res.doc_id) {
            showToast(t('pur-inbox-created'), 'success');
            window.openPurchaseForm?.(res.doc_id);
        } else if (action === 'dismiss') {
            showToast(t('pur-inbox-dismissed'), 'success');
        } else {
            showToast(
                action === 'sales' ? t('pur-intake-sales') : t('pur-intake-recon'),
                'success'
            );
        }
    } catch (e) {
        btns.forEach((b) => (b.disabled = false));
        showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
    }
}

function bindItems(): void {
    document.querySelectorAll<HTMLElement>('#ibx-list .item').forEach((row) => {
        const id = row.dataset.id!;
        const btns = row.querySelectorAll<HTMLButtonElement>('.acts .b');
        btns.forEach((b) => {
            b.onclick = () => resolve(id, b.dataset.act!, btns);
        });
    });
}

const stateShell = (inner: string): string =>
    `<div class="pur ibx"><div class="wrap"><div class="panel"><div class="state">${inner}</div></div></div></div>`;

async function load(): Promise<void> {
    const sec = document.getElementById('page-purchase-inbox');
    if (!sec) return;
    sec.innerHTML = stateShell(escapeHtml(t('pur-loading')));
    let failed = false;
    try {
        const d = (await papi('GET', '/api/purchase/inbox')) as { items?: InboxItem[] };
        items = d.items || [];
    } catch (_) {
        failed = true;
    }
    if (failed) {
        sec.innerHTML = stateShell(
            `${escapeHtml(t('pur-error'))}<br><span class="rt" id="ibx-retry">${escapeHtml(t('pur-retry'))}</span>`
        );
        const rt = document.getElementById('ibx-retry');
        if (rt) rt.onclick = load;
        return;
    }
    sec.innerHTML = shell();
    bindItems();
}

window.loadPurchaseInbox = function () {
    injectPurBase();
    injectStyle('pur-inbox-css', PAGE_CSS);
    load();
};
