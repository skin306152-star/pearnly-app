// 自动做账 · 屏1 主屏(照搬设计稿 01-做账主屏收拢版 · DESIGN_LANGUAGE)。
// 一个面板分三层:① 主信息带(本月已自动做账北极星 + 待审行动卡)② 控件带(筛选 seg +
// 月份 + 出账本入口)③ 凭证列表(行点开行内展开借贷表 + 动作)。路由 key 沿用 vouchers。
/* global t, escapeHtml, showToast */
import {
    aapi,
    acctConfirm,
    acctErrMsg,
    closeAcctModal,
    currentPeriod,
    injectAcctBase,
    injectStyle,
    isMappingShell,
    ledgerTable,
    normVoucher,
    periodLabel,
    recentPeriods,
    srcKey,
    withWs,
    type Voucher,
    type VoucherSummary,
} from './acct-common.js';
import { fmtBaht } from './purchase-common.js';
import { openAcctAccountPicker } from './acct-modals.js';
import { MORE_SVG } from './more-menu.js';

type Chip = 'all' | 'pending' | 'purchase' | 'sale' | 'pos' | 'payment';

const PAGE_CSS = `
.acct.al .band{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:20px 22px;border-bottom:1px solid var(--line2);}
.acct.al .star .lbl{color:var(--ink2);font-size:12.5px;margin-bottom:5px;}
.acct.al .star .num{font-size:30px;font-weight:740;letter-spacing:-1px;line-height:1;}
.acct.al .star .num small{font-size:15px;font-weight:600;color:var(--ink2);}
.acct.al .star .ctx{margin-top:8px;color:var(--ink2);font-size:12.5px;}
.acct.al .star .ctx .g{color:var(--green);font-weight:600;}
.acct.al .attn{display:flex;align-items:center;gap:13px;background:var(--amber-weak);border:1px solid var(--amber-weak);border-radius:12px;padding:10px 12px 10px 14px;cursor:pointer;}
.acct.al .attn .l{display:flex;align-items:center;gap:6px;font-size:11.5px;color:var(--amber);font-weight:600;}
.acct.al .attn .l .pip{width:6px;height:6px;border-radius:50%;background:var(--amber);}
.acct.al .attn .m{font-size:14px;font-weight:700;margin-top:2px;}
.acct.al .attn .go{height:34px;padding:0 13px;border-radius:9px;background:var(--card);border:1px solid var(--amber-weak);color:var(--amber);font-weight:650;font-size:12.5px;display:flex;align-items:center;}
.acct.al .toolbar{display:flex;align-items:center;gap:12px;padding:11px 18px;border-bottom:1px solid var(--line2);background:var(--line2);flex-wrap:wrap;}
.acct.al .seg{display:inline-flex;gap:2px;}
.acct.al .seg .o{height:30px;padding:0 13px;border-radius:8px;display:flex;align-items:center;font-size:12.5px;color:var(--ink2);cursor:pointer;}
.acct.al .seg .o.on{background:var(--ink);color:var(--card);font-weight:600;}
.acct.al .seg .o .b{margin-left:5px;background:var(--amber-weak);color:var(--amber);font-size:10px;padding:0 5px;border-radius:5px;font-weight:600;}
.acct.al .mctl{margin-left:auto;display:inline-flex;align-items:center;gap:10px;}
.acct.al .mctl select{height:32px;border:1px solid var(--line);border-radius:9px;background:var(--card);color:var(--ink2);font-size:12.5px;padding:0 8px;outline:0;}
.acct.al .row{display:flex;align-items:center;gap:13px;padding:14px 18px;border-bottom:1px solid var(--line2);cursor:pointer;}
.acct.al .row:hover{background:var(--line2);}
.acct.al .row .no{width:64px;color:var(--ink3);font-size:11.5px;flex:0 0 64px;}
.acct.al .src{font-size:10.5px;padding:2px 9px;border-radius:6px;white-space:nowrap;min-width:50px;text-align:center;background:var(--line2);color:var(--ink2);}
.acct.al .src.purchase{background:var(--accent-weak);color:var(--accent-deep);}
.acct.al .src.sale{background:var(--green-weak);color:var(--green);}
.acct.al .src.pos{background:var(--amber-weak);color:var(--amber);}
.acct.al .row .sum{flex:1;min-width:0;font-size:13.5px;}
.acct.al .row .amt{font-weight:700;font-variant-numeric:tabular-nums;font-size:14px;}
.acct.al .tag{font-size:10.5px;padding:3px 9px;border-radius:6px;min-width:62px;text-align:center;line-height:1.25;}
.acct.al .tag.auto{background:var(--green-weak);color:var(--green);}
.acct.al .tag.manual{background:var(--line2);color:var(--ink2);}
.acct.al .tag.todo{background:var(--amber-weak);color:var(--amber);font-weight:600;}
.acct.al .tag.void{background:var(--line2);color:var(--ink3);text-decoration:line-through;}
.acct.al .open{background:var(--line2);border-bottom:1px solid var(--line2);padding:4px 18px 16px 18px;}
.acct.al .open .ttl{font-size:12px;color:var(--ink2);padding:12px 0 9px;}
.acct.al .open .foot{display:flex;align-items:center;gap:12px;margin-top:11px;}
.acct.al .open .human{flex:1;font-size:12px;color:var(--ink2);}
.acct.al .more-wrap{position:relative;}
@media(max-width:600px){
  .acct.al .band{flex-direction:column;align-items:stretch;gap:14px;}
  .acct.al .row{flex-wrap:wrap;}
  .acct.al .row .no{width:auto;flex:0 0 auto;}
  .acct.al .mctl{margin-left:0;width:100%;justify-content:space-between;}
  .acct.al .open{padding-left:18px;}
  .acct.al .open .foot{flex-wrap:wrap;}
}
`;

let vouchers: Voucher[] = [];
let summary: VoucherSummary | null = null;
let chip: Chip = 'all';
let period = currentPeriod();
let openId: string | null = null;

function matchChip(v: Voucher): boolean {
    if (chip === 'pending') return v.status === 'pending_review';
    if (chip === 'all') return true;
    return v.source_type === chip;
}

function starHtml(): string {
    const s = summary;
    const ctx = s
        ? `<span class="g">${s.posted_count} ${escapeHtml(t('acct-posted-count'))}</span> · ${escapeHtml(t('acct-star-ctx'))}`
        : '—';
    return `<div class="lbl">${escapeHtml(t('acct-star-label'))}</div>
        <div class="num tnum">${s ? s.posted_count + s.pending_count : 0} <small>${escapeHtml(t('acct-unit-vouchers'))}</small></div>
        <div class="ctx">${ctx}</div>`;
}

function attnHtml(): string {
    const n = summary ? summary.pending_count : 0;
    if (!n) return '';
    return `<div class="attn" id="acct-attn">
        <div><div class="l"><span class="pip"></span>${escapeHtml(t('acct-attn-label'))}</div>
        <div class="m tnum">${n} ${escapeHtml(t('acct-attn-count'))}</div></div>
        <div class="go">${escapeHtml(t('acct-go-review'))} →</div></div>`;
}

function segHtml(): string {
    const defs: [Chip, string][] = [
        ['all', 'acct-chip-all'],
        ['pending', 'acct-chip-pending'],
        ['purchase', 'acct-src-purchase'],
        ['sale', 'acct-src-sale'],
        ['pos', 'acct-src-pos'],
        ['payment', 'acct-src-payment'],
    ];
    const n = summary ? summary.pending_count : 0;
    return defs
        .map(([k, key]) => {
            const badge = k === 'pending' && n ? `<span class="b tnum">${n}</span>` : '';
            return `<div class="o ${k === chip ? 'on' : ''}" data-chip="${k}">${escapeHtml(t(key))}${badge}</div>`;
        })
        .join('');
}

function monthOptions(): string {
    return recentPeriods()
        .map(
            (p) =>
                `<option value="${p}" ${p === period ? 'selected' : ''}>${escapeHtml(periodLabel(p))}</option>`
        )
        .join('');
}

function tagHtml(v: Voucher): string {
    if (v.status === 'void')
        return `<span class="tag void">${escapeHtml(t('acct-tag-void'))}</span>`;
    if (v.status === 'pending_review')
        return `<span class="tag todo">${escapeHtml(t('acct-tag-pending'))}</span>`;
    if (v.method === 'auto')
        return `<span class="tag auto">${escapeHtml(t('acct-tag-auto'))}</span>`;
    return `<span class="tag manual">${escapeHtml(t('acct-tag-manual'))}</span>`;
}

function rowsHtml(list: Voucher[]): string {
    return list
        .map((v) => {
            const open = v.id === openId ? openHtml(v) : '';
            return `<div class="row" data-id="${escapeHtml(v.id)}">
                <span class="no tnum">${escapeHtml(v.voucher_no || '—')}</span>
                <span class="src ${escapeHtml(v.source_type)}">${escapeHtml(t(srcKey(v.source_type)))}</span>
                <div class="sum">${escapeHtml(v.description || v.source_ref || '—')}</div>
                <span class="amt tnum">${fmtBaht(v.total_debit)}</span>
                ${tagHtml(v)}
            </div>${open}`;
        })
        .join('');
}

// 行内展开:借贷表 + 人话 + 动作(pending=改科目/确认;posted=⋯ 撤销重做/作废)。
function openHtml(v: Voucher): string {
    const meta = `${escapeHtml(t('acct-voucher'))} ${escapeHtml(v.voucher_no || '')} · ${escapeHtml(t(srcKey(v.source_type)))} · ${escapeHtml(v.voucher_date || '')}`;
    const shell = isMappingShell(v);
    const table = shell
        ? `<div class="state" style="padding:18px;">${escapeHtml(t('acct-shell-hint'))}<br><button class="btn" id="acct-goto-settings" style="margin-top:10px;">${escapeHtml(t('acct-goto-settings'))} →</button></div>`
        : ledgerTable(v);
    let actions = '';
    if (v.status === 'pending_review' && !shell) {
        actions = `<button class="btn" data-act="override">${escapeHtml(t('acct-change-account'))}</button>
            <button class="btn primary" data-act="confirm">${escapeHtml(t('acct-confirm'))}</button>`;
    } else if (v.status !== 'void' && v.status !== 'pending_review') {
        actions = `<div class="more-wrap"><button class="btn" aria-label="more">${MORE_SVG}</button>
            <div class="more-menu right" hidden>
                <button class="mi" data-act="unpost">${escapeHtml(t('acct-unpost'))}</button>
                <button class="mi" data-act="void">${escapeHtml(t('acct-void'))}</button>
            </div></div>`;
    }
    const human = v.human_note
        ? `<div class="human">${escapeHtml(v.human_note)}</div>`
        : '<div class="human"></div>';
    return `<div class="open" data-open="${escapeHtml(v.id)}">
        <div class="ttl">${meta}</div>${table}
        <div class="foot">${human}${actions}</div></div>`;
}

function shellHtml(): string {
    return `<div class="acct al"><div class="wrap">
        <div class="ph"><div><div class="t">${escapeHtml(t('acct-title'))}</div><div class="sub">${escapeHtml(t('acct-subtitle'))}</div></div></div>
        <div class="panel">
            <div class="band"><div class="star" id="acct-star">${starHtml()}</div><div id="acct-attn-slot">${attnHtml()}</div></div>
            <div class="toolbar">
                <div class="seg" id="acct-seg">${segHtml()}</div>
                <div class="mctl">
                    <select id="acct-month">${monthOptions()}</select>
                    <button class="btn primary" id="acct-books-btn">${escapeHtml(t('acct-go-books'))} →</button>
                </div>
            </div>
            <div id="acct-body"></div>
        </div>
    </div></div>`;
}

function renderBody(): void {
    const star = document.getElementById('acct-star');
    if (star) star.innerHTML = starHtml();
    const slot = document.getElementById('acct-attn-slot');
    if (slot) {
        slot.innerHTML = attnHtml();
        const attn = document.getElementById('acct-attn');
        if (attn) attn.onclick = () => window.routeTo?.('acct-review');
    }
    const seg = document.getElementById('acct-seg');
    if (seg) {
        seg.innerHTML = segHtml();
        seg.querySelectorAll<HTMLElement>('.o').forEach((el) => {
            el.onclick = () => {
                chip = el.dataset.chip as Chip;
                renderBody();
            };
        });
    }
    const body = document.getElementById('acct-body');
    if (!body) return;
    const list = vouchers.filter(matchChip);
    body.innerHTML = list.length
        ? rowsHtml(list)
        : `<div class="state">${escapeHtml(t('acct-empty'))}</div>`;
    bindRows(body);
}

function bindRows(body: HTMLElement): void {
    body.querySelectorAll<HTMLElement>('.row[data-id]').forEach((el) => {
        el.onclick = () => toggleOpen(el.dataset.id!);
    });
    const open = body.querySelector<HTMLElement>('.open[data-open]');
    if (!open) return;
    const id = open.dataset.open!;
    const goto = open.querySelector<HTMLElement>('#acct-goto-settings');
    if (goto) goto.onclick = () => window.routeTo?.('acct-settings');
    open.querySelectorAll<HTMLElement>('[data-act]').forEach((btn) => {
        btn.onclick = (e) => {
            e.stopPropagation();
            const act = btn.dataset.act!;
            if (act === 'confirm') confirmVoucher(id, btn as HTMLButtonElement);
            else if (act === 'override') overrideAccounts(id);
            else if (act === 'unpost') unpostVoucher(id);
            else if (act === 'void') voidVoucher(id);
        };
    });
}

async function toggleOpen(id: string): Promise<void> {
    if (openId === id) {
        openId = null;
        renderBody();
        return;
    }
    openId = id;
    try {
        const data = (await aapi('GET', withWs(`/api/accounting/vouchers/${id}`))) as {
            voucher?: Record<string, unknown>;
        };
        const v = normVoucher((data && data.voucher) || (data as Record<string, unknown>));
        const i = vouchers.findIndex((x) => x.id === id);
        if (i >= 0) vouchers[i] = v;
    } catch (e) {
        showToast(acctErrMsg(e, 'acct.unexpected'), 'error');
    }
    renderBody();
}

async function confirmVoucher(id: string, btn: HTMLButtonElement): Promise<void> {
    btn.disabled = true;
    try {
        await aapi('POST', withWs(`/api/accounting/vouchers/${id}/review`), { remember: true });
        showToast(t('acct-confirm-ok'), 'success');
        openId = null;
        await load();
    } catch (e) {
        btn.disabled = false;
        showToast(acctErrMsg(e, 'acct.unexpected'), 'error');
    }
}

// 改科目:.modal 选科目(非原生 prompt)· 逐笔审与主屏共用 acct-modals 的选择器。
function overrideAccounts(id: string): void {
    const v = vouchers.find((x) => x.id === id);
    if (!v || !v.lines || !v.lines.length) return;
    openAcctAccountPicker(v, async (overrides) => {
        try {
            await aapi('POST', withWs(`/api/accounting/vouchers/${id}/review`), {
                account_overrides: overrides,
                remember: true,
            });
            showToast(t('acct-confirm-ok'), 'success');
            closeAcctModal();
            openId = null;
            await load();
        } catch (e) {
            showToast(acctErrMsg(e, 'acct.unexpected'), 'error');
        }
    });
}

// 撤销重做(安全带②):确认 → void+重判,toast 报重判结果。
function unpostVoucher(id: string): void {
    acctConfirm(t('acct-unpost'), t('acct-unpost-confirm'), async () => {
        try {
            const data = (await aapi('POST', withWs(`/api/accounting/vouchers/${id}/unpost`))) as {
                voucher?: Record<string, unknown> | null;
            };
            const nv = data && data.voucher ? normVoucher(data.voucher) : null;
            showToast(
                nv
                    ? t(
                          nv.status === 'pending_review'
                              ? 'acct-unpost-pending'
                              : 'acct-unpost-reposted'
                      )
                    : t('acct-unpost-only'),
                'success'
            );
            openId = null;
            await load();
        } catch (e) {
            showToast(acctErrMsg(e, 'acct.period_closed'), 'error');
        }
    });
}

function voidVoucher(id: string): void {
    acctConfirm(t('acct-void'), t('acct-void-confirm'), async () => {
        try {
            await aapi('POST', withWs(`/api/accounting/vouchers/${id}/void`));
            showToast(t('acct-void-ok'), 'success');
            openId = null;
            await load();
        } catch (e) {
            showToast(acctErrMsg(e, 'acct.period_closed'), 'error');
        }
    });
}

function showState(html: string): void {
    const body = document.getElementById('acct-body');
    if (body) body.innerHTML = `<div class="state">${html}</div>`;
}

async function load(): Promise<void> {
    showState(escapeHtml(t('acct-loading')));
    try {
        const data = (await aapi('GET', withWs(`/api/accounting/vouchers?period=${period}`))) as {
            summary?: VoucherSummary;
            items?: Record<string, unknown>[];
        };
        vouchers = (data.items || []).map(normVoucher);
        summary = data.summary || null;
        renderBody();
    } catch (e) {
        showState(
            `${escapeHtml(acctErrMsg(e, 'acct.unexpected'))}<br><button class="btn" id="acct-retry">${escapeHtml(t('acct-retry'))}</button>`
        );
        const retry = document.getElementById('acct-retry');
        if (retry) retry.onclick = () => load();
    }
}

window.loadAcctList = function () {
    const sec = document.getElementById('page-vouchers');
    if (!sec) return;
    injectAcctBase();
    injectStyle('acct-list-css', PAGE_CSS);
    openId = null;
    sec.innerHTML = shellHtml();
    const month = document.getElementById('acct-month') as HTMLSelectElement | null;
    if (month)
        month.onchange = () => {
            period = month.value;
            load();
        };
    const books = document.getElementById('acct-books-btn');
    if (books) books.onclick = () => window.routeTo?.('acct-books');
    renderBody();
    load();
};

if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('acct-list', () => {
        if (document.getElementById('acct-body')) window.loadAcctList?.();
    });
}
