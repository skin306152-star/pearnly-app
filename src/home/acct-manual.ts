// 手工凭证(window.loadAcctManual · 入口=做账主屏「+手工凭证」按钮,不进导航)。
// 交互基准 docs/accounting/bank-recon-mj/03-交互原型.html — 配平门控/全键盘/模板/过账二次确认/红冲只读 100% 照搬。
// 真 API:POST /api/accounting/vouchers/manual(draft) · voucher-templates CRUD · vouchers/{id}/void。
/* global escapeHtml, t */
import { aapi, withWs, acctErrMsg, acctConfirm, AcctError } from './acct-common.js';
import { fmtMoney } from './purchase-common.js';
import { withBusy, openTemplateModal, openSaveTplModal } from './acct-bank-modals.js';

type Acc = Record<string, unknown>;
type Tpl = { id: string; name: string; lines: Acc[]; use_count?: number };
interface MjRow {
    acc: string;
    memo: string;
    dr: number;
    cr: number;
    bad?: boolean;
}

function todayIso(): string {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

const M = {
    date: '',
    memo: '',
    state: 'editing' as 'editing' | 'posted' | 'voided',
    dirty: false,
    saved: false,
    lastRow: 0,
    rows: [] as MjRow[],
    voucherId: '',
    voucherNo: '',
    voidNo: '',
    accounts: [] as Acc[],
    templates: [] as Tpl[],
    loaded: false,
    periodClosed: false,
};

const esc = (s: unknown) => escapeHtml(String(s == null ? '' : s));
const N = (v: unknown) => Number(String(v).replace(/,/g, '')) || 0;
const sec = () => document.getElementById('page-acct-manual');

function freshRows(): MjRow[] {
    return [
        { acc: '', memo: '', dr: 0, cr: 0 },
        { acc: '', memo: '', dr: 0, cr: 0 },
    ];
}
function totals(): [number, number, number] {
    let d = 0,
        c = 0;
    M.rows.forEach((r) => {
        d += N(r.dr);
        c += N(r.cr);
    });
    return [d, c, d - c];
}

async function loadRefs(): Promise<void> {
    try {
        const [a, tp] = await Promise.all([
            aapi('GET', withWs('/api/accounting/accounts')) as Promise<{ accounts?: Acc[] }>,
            aapi('GET', withWs('/api/accounting/voucher-templates')) as Promise<{
                templates?: Tpl[];
            }>,
        ]);
        M.accounts = a.accounts || [];
        M.templates = tp.templates || [];
    } catch (_) {
        /* 参考数据失败不致命 · 仍可手填 */
    }
    M.loaded = true;
    render();
}

function accOpts(cur: string): string {
    return (
        `<option value="">${esc(t('acct-mj-acc-ph'))}</option>` +
        M.accounts
            .map(
                (a) =>
                    `<option value="${esc(a.id)}"${a.id === cur ? ' selected' : ''}>${esc(a.code)} ${esc(a.name_zh || a.name_th || '')}</option>`
            )
            .join('')
    );
}

function rowsHtml(): string {
    const ro = M.state !== 'editing';
    return M.rows
        .map((r, i) => {
            if (ro)
                return (
                    `<tr><td>${esc(accLabel(r.acc))}</td><td style="color:var(--ink3)">${esc(r.memo || M.memo)}</td>` +
                    `<td class="r tnum">${r.dr ? fmtMoney(r.dr) : '—'}</td><td class="r tnum">${r.cr ? fmtMoney(r.cr) : '—'}</td><td></td></tr>`
                );
            return (
                `<tr><td><select data-mj="acc" data-i="${i}" class="${r.bad ? 'bad' : ''}">${accOpts(r.acc)}</select></td>` +
                `<td><input data-mj="memo" data-i="${i}" placeholder="${esc(M.memo || t('acct-mj-row-memo'))}" value="${esc(r.memo)}"></td>` +
                `<td><input data-mj="dr" data-i="${i}" class="r" inputmode="decimal" value="${r.dr || ''}"></td>` +
                `<td><input data-mj="cr" data-i="${i}" class="r" inputmode="decimal" value="${r.cr || ''}"></td>` +
                `<td><button class="del" data-act="mjdel" data-i="${i}" title="${esc(t('acct-mj-delrow'))}">✕</button></td></tr>`
            );
        })
        .join('');
}

function accLabel(code: string): string {
    const a = M.accounts.find((x) => x.id === code);
    return a ? `${a.code} ${a.name_zh || a.name_th || ''}` : code;
}

function footHtml(): string {
    const [td, tc, diff] = totals();
    if (M.state === 'posted')
        return (
            `<span class="bi" style="color:var(--ink3)">${esc(t('acct-mj-posted-note'))}</span>` +
            `<div class="sp2"><button class="btn" data-act="mjcopy">${esc(t('acct-mj-copy'))}</button><button class="btn danger" data-act="mjvoid">${esc(t('acct-mj-void'))}</button></div>`
        );
    if (M.state === 'voided')
        return (
            `<span class="bi" style="color:var(--ink3)">${esc(t('acct-mj-voided-note', { no: M.voidNo }))}</span>` +
            `<div class="sp2"><button class="btn" data-act="mjcopy">${esc(t('acct-mj-copy'))}</button></div>`
        );
    const bal =
        Math.abs(diff) < 0.005
            ? `<span class="ok-t">${esc(t('acct-mj-balanced'))}</span>`
            : `<span class="bad-t">${esc(t('acct-mj-diff'))} ${fmtMoney(diff)}${diff > 0 ? esc(t('acct-mj-diff-dr')) : esc(t('acct-mj-diff-cr'))}</span>`;
    const fill =
        Math.abs(diff) >= 0.005
            ? `<button class="btn" data-act="mjfill" data-tip="${esc(t('acct-mj-fill-tip'))}">${esc(t('acct-mj-fill'))}</button>`
            : '';
    const postOff = Math.abs(diff) >= 0.005 || td === 0 || M.periodClosed;
    return (
        `<span class="bi">${esc(t('acct-mj-dr-total'))} <b class="tnum">${fmtMoney(td)}</b></span>` +
        `<span class="bi">${esc(t('acct-mj-cr-total'))} <b class="tnum">${fmtMoney(tc)}</b></span>${bal}` +
        `<div class="sp2">${fill}<button class="btn" data-act="mjdraft">${esc(t('acct-mj-draft'))}</button>` +
        `<button class="btn primary" data-act="mjpost" ${postOff ? 'disabled' : ''}>${esc(t('acct-mj-post'))}</button></div>`
    );
}

function render(): void {
    const el = sec();
    if (!el) return;
    const ro = M.state !== 'editing';
    const badge =
        M.state === 'posted'
            ? `<span class="badge posted">${esc(t('acct-mj-badge-posted'))}</span>`
            : M.state === 'voided'
              ? `<span class="badge voided">${esc(t('acct-mj-badge-voided'))}</span>`
              : M.saved
                ? `<span class="badge draft">${esc(t('acct-mj-badge-draft'))}</span>`
                : '';
    const dirty = !ro && M.dirty ? `<span class="dirty">● ${esc(t('acct-mj-dirty'))}</span>` : '';
    const noVal = M.voucherNo || t('acct-mj-no-auto');
    const head = `<div class="ph"><div><div class="t">${esc(t('acct-mj-title'))}</div><div class="sub">${esc(t('acct-mj-subtitle'))}</div></div>${
        M.state === 'editing'
            ? `<span style="display:flex;gap:8px"><button class="btn" data-act="mjtpl">${esc(t('acct-mj-from-tpl'))} ▾</button><button class="btn ghost" data-act="mjsavetpl">${esc(t('acct-mj-save-tpl'))}</button></span>`
            : ''
    }</div>`;
    const lock =
        M.periodClosed && !ro ? `<div class="lockbar">${esc(t('acct-mj-lockbar'))}</div>` : '';
    el.innerHTML =
        `<div class="mjx">${head}${lock}<div class="panel"><div class="vh-grid">` +
        `<div class="fld" style="width:150px"><label>${esc(t('acct-mj-date'))}</label><input type="date" data-mj="date" value="${esc(M.date)}" ${ro ? 'disabled' : ''}></div>` +
        `<div class="fld" style="width:180px"><label>${esc(t('acct-mj-no'))}</label><input value="${esc(noVal)}" disabled></div>` +
        `<div class="fld" style="flex:1;min-width:200px"><label>${esc(t('acct-mj-memo'))}</label><input data-mj="hmemo" value="${esc(M.memo)}" ${ro ? 'disabled' : ''}></div>` +
        `<div style="padding-bottom:7px;display:flex;gap:8px;align-items:center">${badge}${dirty}</div></div>` +
        `<table class="mj"><tr><th style="width:32%">${esc(t('acct-mj-th-acc'))}</th><th>${esc(t('acct-mj-th-memo'))}</th><th class="r" style="width:125px">${esc(t('acct-mj-th-dr'))}</th><th class="r" style="width:125px">${esc(t('acct-mj-th-cr'))}</th><th style="width:34px"></th></tr>${rowsHtml()}</table>` +
        (ro
            ? ''
            : `<div class="addrow"><button data-act="mjadd">${esc(t('acct-mj-addrow'))}</button></div>` +
              `<div class="keys">${esc(t('acct-mj-keys'))}<span><b>Enter</b> ${esc(t('acct-mj-key-enter'))}</span><span><b>Alt + =</b> ${esc(t('acct-mj-key-fill'))}</span><span><b>Ctrl + S</b> ${esc(t('acct-mj-key-save'))}</span></div>`) +
        `<div class="balbar">${footHtml()}</div></div></div>`;
}

// ── 输入 / 键盘 ──────────────────────────────────────────────────────────────
function onInput(elm: HTMLInputElement | HTMLSelectElement): void {
    const k = elm.dataset.mj;
    if (k === 'date') {
        M.date = elm.value;
        M.dirty = true;
        M.periodClosed = false;
        render();
        return;
    }
    if (k === 'hmemo') {
        M.memo = elm.value;
        M.dirty = true;
        refreshBalbar();
        return;
    }
    const i = Number(elm.dataset.i);
    if (!M.rows[i]) return;
    M.lastRow = i;
    M.dirty = true;
    if (k === 'acc') {
        M.rows[i].acc = elm.value;
        M.rows[i].bad = false;
        elm.classList.remove('bad');
        return;
    }
    if (k === 'memo') {
        M.rows[i].memo = elm.value;
        return;
    }
    const v = N(elm.value);
    if (k === 'dr') {
        M.rows[i].dr = v;
        if (v) M.rows[i].cr = 0;
    }
    if (k === 'cr') {
        M.rows[i].cr = v;
        if (v) M.rows[i].dr = 0;
    }
    refreshBalbar();
}

function refreshBalbar(): void {
    const bb = sec()?.querySelector('.balbar');
    if (bb) bb.innerHTML = footHtml();
}

function addRow(): void {
    M.rows.push({ acc: '', memo: '', dr: 0, cr: 0 });
    M.dirty = true;
    render();
    const sels = sec()?.querySelectorAll<HTMLElement>('[data-mj="acc"]');
    if (sels && sels.length) sels[sels.length - 1].focus();
}
function fill(): void {
    const [, , diff] = totals();
    if (Math.abs(diff) < 0.005) {
        window.showToast?.(t('acct-mj-already-bal'), 'info');
        return;
    }
    const r = M.rows[Math.min(M.lastRow, M.rows.length - 1)] || M.rows[M.rows.length - 1];
    if (diff > 0) {
        r.cr = N(r.cr) + diff;
        r.dr = 0;
    } else {
        r.dr = N(r.dr) - diff;
        r.cr = 0;
    }
    M.dirty = true;
    render();
    window.showToast?.(t('acct-mj-filled'), 'info');
}
function validate(): boolean {
    let ok = true;
    M.rows.forEach((r) => {
        if ((N(r.dr) > 0 || N(r.cr) > 0) && !r.acc) {
            r.bad = true;
            ok = false;
        }
    });
    if (!ok) {
        render();
        window.showToast?.(t('acct-mj-need-acc'), 'error');
    }
    return ok;
}
function payload(draft: boolean): Record<string, unknown> {
    const lines = M.rows
        .filter((r) => N(r.dr) > 0 || N(r.cr) > 0)
        .map((r) => ({
            account_id: r.acc,
            dr_cr: N(r.dr) > 0 ? 'debit' : 'credit',
            amount: N(r.dr) > 0 ? N(r.dr) : N(r.cr),
            memo: r.memo || null,
        }));
    return { voucher_date: M.date, description: M.memo, lines, draft };
}

async function submit(btn: HTMLElement, draft: boolean): Promise<void> {
    await withBusy(btn, async () => {
        try {
            const r = (await aapi(
                'POST',
                withWs('/api/accounting/vouchers/manual'),
                payload(draft)
            )) as {
                voucher?: { id?: string; voucher_no?: string };
            };
            const v = r.voucher || {};
            if (draft) {
                M.saved = true;
                M.dirty = false;
                render();
                window.showToast?.(t('acct-mj-draft-done'), 'success');
            } else {
                M.state = 'posted';
                M.dirty = false;
                M.voucherId = String(v.id || '');
                M.voucherNo = String(v.voucher_no || '');
                render();
                window.showToast?.(t('acct-mj-post-done', { no: M.voucherNo }), 'success');
            }
        } catch (e) {
            if (e instanceof AcctError && e.code === 'acct.period_closed') {
                M.periodClosed = true;
                render();
            }
            window.showToast?.(acctErrMsg(e, 'acct-mj-save-fail'), 'error');
        }
    });
}

// ── 事件 ─────────────────────────────────────────────────────────────────────
function bind(): void {
    const el = sec();
    if (!el) return;
    // change 只接 select(acc)/日期:金额输入的 blur-change 若也重渲 balbar,会在 mousedown/mouseup
    // 之间替换掉「存草稿/过账」按钮 → click 事件不触发(真用户填完金额点保存会丢)。金额走 input。
    el.onchange = (e) => {
        const tgt = e.target as HTMLInputElement | HTMLSelectElement;
        const mj = tgt.dataset && tgt.dataset.mj;
        if (mj === 'acc' || mj === 'date') onInput(tgt);
    };
    el.oninput = (e) => {
        const tgt = e.target as HTMLInputElement;
        const mj = tgt.dataset && tgt.dataset.mj;
        if (mj && mj !== 'acc' && mj !== 'date') onInput(tgt);
    };
    el.onkeydown = (e) => {
        if (M.state !== 'editing') return;
        const tgt = e.target as HTMLElement;
        if (e.key === 'Enter' && tgt.dataset && tgt.dataset.mj && tgt.dataset.mj !== 'hmemo') {
            e.preventDefault();
            const cells = [
                ...el.querySelectorAll<HTMLElement>(
                    '[data-mj="acc"],[data-mj="memo"],[data-mj="dr"],[data-mj="cr"]'
                ),
            ];
            const idx = cells.indexOf(tgt);
            if (idx === cells.length - 1) addRow();
            else if (idx >= 0) cells[idx + 1].focus();
        }
        if (e.altKey && (e.key === '=' || e.key === '+')) {
            e.preventDefault();
            fill();
        }
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            const b = el.querySelector<HTMLElement>('[data-act="mjdraft"]');
            if (validate() && b) submit(b, true);
        }
    };
    el.onclick = (e) => {
        const b = (e.target as HTMLElement).closest<HTMLElement>('[data-act]');
        if (!b) return;
        const act = b.dataset.act;
        const i = Number(b.dataset.i);
        if (act === 'mjadd') addRow();
        else if (act === 'mjdel') {
            if (M.rows.length <= 2) {
                window.showToast?.(t('acct-mj-min-rows'), 'error');
                return;
            }
            M.rows.splice(i, 1);
            M.dirty = true;
            render();
        } else if (act === 'mjfill') fill();
        else if (act === 'mjdraft') {
            if (validate()) submit(b, true);
        } else if (act === 'mjpost') {
            if (!validate()) return;
            acctConfirm(
                t('acct-mj-post-confirm-t'),
                t('acct-mj-post-confirm-m', { amt: fmtMoney(totals()[0]) }),
                () => submit(b, false)
            );
        } else if (act === 'mjvoid') {
            acctConfirm(t('acct-mj-void-confirm-t'), t('acct-mj-void-confirm-m'), async () => {
                try {
                    const r = (await aapi(
                        'POST',
                        withWs(`/api/accounting/vouchers/${M.voucherId}/void`)
                    )) as {
                        voucher?: { voucher_no?: string };
                    };
                    M.state = 'voided';
                    M.voidNo = String((r.voucher && r.voucher.voucher_no) || '');
                    render();
                    window.showToast?.(t('acct-mj-void-done', { no: M.voidNo }), 'info');
                } catch (err) {
                    window.showToast?.(acctErrMsg(err, 'acct-mj-save-fail'), 'error');
                }
            });
        } else if (act === 'mjcopy') {
            M.rows = M.rows.map((r) => ({ acc: r.acc, memo: r.memo, dr: r.dr, cr: r.cr }));
            M.state = 'editing';
            M.saved = false;
            M.dirty = true;
            M.voucherId = '';
            M.voucherNo = '';
            render();
            window.showToast?.(t('acct-mj-copied'), 'success');
        } else if (act === 'mjtpl') openTemplateModal(M, render);
        else if (act === 'mjsavetpl') openSaveTplModal(M);
    };
}

window.loadAcctManual = function () {
    const el = sec();
    if (!el) return;
    M.date = todayIso();
    M.memo = '';
    M.state = 'editing';
    M.dirty = false;
    M.saved = false;
    M.lastRow = 0;
    M.rows = freshRows();
    M.voucherId = '';
    M.voucherNo = '';
    render();
    bind();
    loadRefs();
};

if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('acct-manual', () => {
        if (sec()?.querySelector('.mjx')) render();
    });
}
