// 自动做账 · 屏2 逐笔审(照搬设计稿 02-逐笔审 · 审例外核心)。
// 队列逐笔:进度带 → 拿不准点(amber)→ 业务来源行 → 借贷预览 → 跳过/改科目/确认·下一笔。
// 缺映射壳 → 行动卡直达做账设置(四-bis 入口落点);最后一笔审完 → 空态「都记好了 ✓」。
/* global t, escapeHtml, showToast */
import {
    aapi,
    acctErrMsg,
    injectAcctBase,
    injectStyle,
    isMappingShell,
    ledgerTable,
    normVoucher,
    closeAcctModal,
    reasonKey,
    srcKey,
    type Voucher,
} from './acct-common.js';
import { activeWsId, fmtBaht, fmtMoney } from './purchase-common.js';
import { openAcctAccountPicker } from './acct-modals.js';

const PAGE_CSS = `
.acct.ar .band{display:flex;align-items:center;justify-content:space-between;padding:16px 22px;border-bottom:1px solid var(--line2);flex-wrap:wrap;gap:8px;}
.acct.ar .band .prog{font-size:14px;font-weight:700;}
.acct.ar .band .prog small{color:var(--ink2);font-weight:500;font-size:12.5px;margin-left:6px;}
.acct.ar .band .meta{color:var(--ink2);font-size:12.5px;}
.acct.ar .q{display:flex;align-items:center;gap:9px;padding:13px 22px;background:var(--amber-weak);border-bottom:1px solid var(--line2);font-size:13.5px;color:var(--amber);}
.acct.ar .q .pip{width:7px;height:7px;border-radius:50%;background:var(--amber);flex-shrink:0;}
.acct.ar .body{padding:18px 22px;}
.acct.ar .evt{font-size:12.5px;color:var(--ink2);margin-bottom:14px;}
.acct.ar .evt b{color:var(--ink);font-size:14px;}
.acct.ar .foot{display:flex;align-items:center;gap:11px;margin-top:16px;flex-wrap:wrap;}
.acct.ar .human{flex:1;min-width:200px;font-size:12px;color:var(--ink2);}
.acct.ar .queue{padding:12px 22px;border-top:1px solid var(--line2);background:var(--line2);display:flex;align-items:center;gap:14px;font-size:12.5px;color:var(--ink2);flex-wrap:wrap;}
.acct.ar .queue .q2{display:flex;align-items:center;gap:7px;}
.acct.ar .queue .dotg{width:6px;height:6px;border-radius:50%;background:var(--amber);}
@media(max-width:600px){
  .acct.ar .foot{flex-direction:column;align-items:stretch;}
  .acct.ar .foot .btn{width:100%;}
}
`;

let queue: Voucher[] = [];
let idx = 0;
let postedCount = 0;

function withWs(path: string): string {
    const ws = activeWsId();
    if (ws == null) return path;
    return path + (path.includes('?') ? '&' : '?') + 'workspace_client_id=' + ws;
}

function cur(): Voucher | null {
    return queue[idx] || null;
}

function doneHtml(): string {
    return `<div class="state">${escapeHtml(t('acct-review-done'))}<br>
        <button class="btn" id="acct-back-list" style="margin-top:12px;">${escapeHtml(t('acct-back-list'))}</button></div>`;
}

function itemHtml(v: Voucher): string {
    const shell = isMappingShell(v);
    const table = shell
        ? `<div class="state" style="padding:18px;">${escapeHtml(t('acct-shell-hint'))}<br>
            <button class="btn" id="acct-goto-settings" style="margin-top:10px;">${escapeHtml(t('acct-goto-settings'))} →</button></div>`
        : ledgerTable(v, fmtMoney);
    const actions = shell
        ? `<button class="btn" data-act="skip">${escapeHtml(t('acct-skip'))}</button>`
        : `<button class="btn" data-act="skip">${escapeHtml(t('acct-skip'))}</button>
           <button class="btn" data-act="override">${escapeHtml(t('acct-change-account'))}</button>
           <button class="btn primary" data-act="confirm">${escapeHtml(t('acct-confirm-next'))}</button>`;
    const rest = queue
        .slice(idx + 1, idx + 3)
        .map(
            (q) =>
                `<span class="q2"><span class="dotg"></span>${escapeHtml(q.voucher_no || '')} ${escapeHtml(q.description || '')}</span>`
        )
        .join('');
    return `
        <div class="band">
            <div class="prog">${escapeHtml(t('acct-review-nth'))} ${idx + 1} <small>/ ${queue.length} ${escapeHtml(t('acct-review-total'))}</small></div>
            <div class="meta">${postedCount ? `${postedCount} ${escapeHtml(t('acct-posted-count'))} · ` : ''}${queue.length} ${escapeHtml(t('acct-review-need'))}</div>
        </div>
        <div class="q"><span class="pip"></span>${escapeHtml(t(reasonKey(v.review_reason)))}</div>
        <div class="body">
            <div class="evt">${escapeHtml(t('acct-evt-source'))}:${escapeHtml(t(srcKey(v.source_type)))} ${escapeHtml(v.source_ref || '')} · ${escapeHtml(v.voucher_date || '')} · <b>${escapeHtml(v.description || '—')} ${fmtBaht(v.total_debit)}</b></div>
            ${table}
            <div class="foot"><div class="human">${escapeHtml(v.human_note || '')}</div>${actions}</div>
        </div>
        ${rest ? `<div class="queue">${escapeHtml(t('acct-review-waiting'))}:${rest}</div>` : ''}`;
}

function render(): void {
    const sec = document.getElementById('page-acct-review');
    if (!sec) return;
    const v = cur();
    sec.innerHTML = `<div class="acct ar"><div class="wrap">
        <div class="ph"><div><div class="t">${escapeHtml(t('acct-review-title'))}</div><div class="sub">${escapeHtml(t('acct-review-subtitle'))}</div></div></div>
        <div class="panel">${v ? itemHtml(v) : doneHtml()}</div>
    </div></div>`;
    bind(sec);
}

function bind(sec: HTMLElement): void {
    const back = sec.querySelector<HTMLElement>('#acct-back-list');
    if (back) back.onclick = () => window.routeTo?.('vouchers');
    const goto = sec.querySelector<HTMLElement>('#acct-goto-settings');
    if (goto) goto.onclick = () => window.routeTo?.('acct-settings');
    sec.querySelectorAll<HTMLButtonElement>('[data-act]').forEach((btn) => {
        btn.onclick = () => {
            const act = btn.dataset.act!;
            const v = cur();
            if (!v) return;
            if (act === 'skip') {
                idx += 1;
                if (idx >= queue.length) idx = queue.length;
                showToast(t('acct-skip-ok'), 'info');
                render();
            } else if (act === 'confirm') {
                btn.disabled = true;
                submit(v.id, {});
            } else if (act === 'override') {
                openAcctAccountPicker(v, (overrides) => {
                    closeAcctModal();
                    submit(v.id, overrides);
                });
            }
        };
    });
}

async function submit(id: string, overrides: Record<string, string>): Promise<void> {
    const payload: Record<string, unknown> = { remember: true };
    if (Object.keys(overrides).length) payload.account_overrides = overrides;
    try {
        await aapi('POST', withWs(`/api/accounting/vouchers/${id}/review`), payload);
        showToast(t('acct-confirm-ok'), 'success');
        postedCount += 1;
        queue = queue.filter((q) => q.id !== id);
        if (idx >= queue.length) idx = Math.max(0, queue.length - 1);
        if (queue.length) loadDetail(queue[idx].id);
        else render();
    } catch (e) {
        showToast(acctErrMsg(e, 'acct.unexpected'), 'error');
        render();
    }
}

async function loadDetail(id: string): Promise<void> {
    try {
        const data = (await aapi('GET', withWs(`/api/accounting/vouchers/${id}`))) as {
            voucher?: Record<string, unknown>;
        };
        const v = normVoucher((data && data.voucher) || (data as Record<string, unknown>));
        const i = queue.findIndex((q) => q.id === id);
        if (i >= 0) queue[i] = v;
        render();
    } catch (_) {
        render();
    }
}

async function load(): Promise<void> {
    const sec = document.getElementById('page-acct-review');
    if (sec)
        sec.innerHTML = `<div class="acct ar"><div class="wrap"><div class="panel"><div class="state">${escapeHtml(t('acct-loading'))}</div></div></div></div>`;
    try {
        const data = (await aapi('GET', withWs('/api/accounting/review'))) as {
            count?: number;
            items?: Record<string, unknown>[];
        };
        queue = (data.items || []).map(normVoucher);
        idx = 0;
        postedCount = 0;
        if (queue.length) await loadDetail(queue[0].id);
        else render();
    } catch (e) {
        if (sec)
            sec.innerHTML = `<div class="acct ar"><div class="wrap"><div class="panel"><div class="state">${escapeHtml(acctErrMsg(e, 'acct.unexpected'))}<br><button class="btn" id="acct-rev-retry" style="margin-top:12px;">${escapeHtml(t('acct-retry'))}</button></div></div></div></div>`;
        const retry = document.getElementById('acct-rev-retry');
        if (retry) retry.onclick = () => load();
    }
}

window.loadAcctReview = function () {
    const sec = document.getElementById('page-acct-review');
    if (!sec) return;
    injectAcctBase();
    injectStyle('acct-review-css', PAGE_CSS);
    load();
};

if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('acct-review', () => {
        if (document.getElementById('page-acct-review')?.querySelector('.acct.ar'))
            window.loadAcctReview?.();
    });
}
