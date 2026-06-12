// 银行对账 + 手工凭证 · 共享样式 + 弹窗(组合匹配 / 改科目 / 导入)。
// 交互基准 docs/accounting/bank-recon-mj/03-交互原型.html;真 API /api/accounting/bank/*。
// 颜色全走 home-01 令牌(浅/暗自适应),作用域 .ab(银行对账)/ .mjx(手工凭证)防全局串类。
/* global escapeHtml, t */
import {
    aapi,
    withWs,
    acctErrMsg,
    acctConfirm,
    openAcctModal,
    closeAcctModal,
    recentPeriods,
    periodLabel,
} from './acct-common.js';
import { fmtMoney } from './purchase-common.js';

// 断网守门:任何写动作前调 · 失败给人话、状态不乱(四-bis · 验收 Q4)。
export function offlineGuard(): boolean {
    if (typeof navigator !== 'undefined' && navigator.onLine === false) {
        window.showToast?.(t('acct-bank-offline'), 'error');
        return true;
    }
    return false;
}

interface BankToolbarState {
    filter: string;
    search: string;
    accountId: string;
    period: string;
    sortDesc: boolean;
    bankAccounts: Cand[];
}
// 工具栏:账户选择器 + 期间选择器 + 搜索 + 状态 pill + 排序 + 导入(原型照搬)。
export function toolbarHtml(S: BankToolbarState): string {
    const accOpts =
        `<option value="">${esc(t('acct-bank-acc-all'))}</option>` +
        S.bankAccounts
            .map(
                (a) =>
                    `<option value="${esc(a.id)}"${a.id === S.accountId ? ' selected' : ''}>${esc(a.bank_code)}${a.account_last4 ? ' ···' + esc(a.account_last4) : ''}</option>`
            )
            .join('');
    const perOpts =
        `<option value="">${esc(t('acct-bank-period-all'))}</option>` +
        recentPeriods()
            .map(
                (p) =>
                    `<option value="${p}"${p === S.period ? ' selected' : ''}>${periodLabel(p)}</option>`
            )
            .join('');
    const pills = [
        ['all', 'acct-bank-pill-all'],
        ['un', 'acct-bank-pill-un'],
        ['matched', 'acct-bank-pill-matched'],
        ['excluded', 'acct-bank-pill-excluded'],
    ]
        .map(
            (p) =>
                `<button class="pill${S.filter === p[0] ? ' on' : ''}" data-act="filter" data-f="${p[0]}">${esc(t(p[1]))}</button>`
        )
        .join('');
    const clear =
        S.search || S.filter !== 'all'
            ? `<button class="clearf" data-act="clearf">${esc(t('acct-bank-clearf'))}</button>`
            : '';
    return (
        `<div class="toolbar"><select class="sel" id="ab-acc">${accOpts}</select><select class="sel" id="ab-period">${perOpts}</select>` +
        `<input class="srch" id="ab-srch" placeholder="${esc(t('acct-bank-search-ph'))}" value="${esc(S.search)}">${pills}` +
        `<button class="pill" data-act="sort">${esc(t('acct-bank-date'))} ${S.sortDesc ? '↓' : '↑'}</button>` +
        `${clear}<span style="margin-left:auto"><button class="btn" data-act="import">${esc(t('acct-bank-import'))}</button></span></div>`
    );
}

const esc = (s: unknown) => escapeHtml(String(s == null ? '' : s));
// 带符号金额:负=支出灰、正=收入绿(原型 fmt)。
export function fmtSigned(n: number): string {
    return (n < 0 ? '− ' : '+ ') + fmtMoney(Math.abs(n));
}

const num = (v: unknown) => Number(v || 0);

// 点击即禁用+转圈,完成/失败必恢复(原型 busy · 四-bis 反馈纪律)。
export async function withBusy(btn: HTMLElement | null, fn: () => Promise<void>): Promise<void> {
    if (!btn) return fn();
    if (btn.getAttribute('aria-busy') === 'true') return;
    btn.setAttribute('aria-busy', 'true');
    btn.classList.add('busy');
    (btn as HTMLButtonElement).disabled = true;
    try {
        await fn();
    } finally {
        btn.removeAttribute('aria-busy');
        btn.classList.remove('busy');
    }
}

// 鉴权/模块/网络门态(状态诚实 · 每态有人话)。
export function gateHtml(gate: string): string {
    const G: Record<string, [string, string, string]> = {
        plan: ['acct-bank-gate-plan-t', 'acct-bank-gate-plan-d', 'acct-bank-gate-plan-b'],
        noperm: ['acct-bank-gate-perm-t', 'acct-bank-gate-perm-d', ''],
        nows: ['acct-bank-gate-nows-t', 'acct-bank-gate-nows-d', ''],
        error: ['acct-bank-load-fail', 'acct-bank-load-fail-d', 'acct-retry'],
    };
    const g = G[gate] || G.error;
    const btn = g[2]
        ? `<button class="btn primary" data-act="${gate === 'error' ? 'reload' : 'stub'}" style="margin-top:14px">${esc(t(g[2]))}</button>`
        : '';
    return `<div class="ab"><div class="panel"><div class="gate"><div class="gt">${esc(t(g[0]))}</div><div class="gd">${esc(t(g[1]))}</div>${btn}</div></div></div>`;
}

// 三余额带 + 进度(summary · 差额 amber/归零 green)。
export function bandHtml(s: Record<string, unknown>): string {
    const diff = num(s.difference);
    const total = num(s.total_count);
    const matched = num(s.matched_count);
    const pct = total ? Math.round((matched / total) * 100) : 100;
    return (
        `<div class="band"><div class="bal"><div class="lbl">${esc(t('acct-bank-bal-bank'))}</div><div class="num tnum">${fmtMoney(num(s.bank_balance))}</div><div class="ctx">${esc(t('acct-bank-bal-bank-ctx'))}</div></div>` +
        `<div class="bal"><div class="lbl">${esc(t('acct-bank-bal-book'))}</div><div class="num tnum">${fmtMoney(num(s.book_balance))}</div><div class="ctx">${esc(t('acct-bank-bal-book-ctx'))}</div></div>` +
        `<div class="bal diff${Math.abs(diff) < 0.005 ? ' zero' : ''}"><div class="lbl">${esc(t('acct-bank-bal-diff'))}</div><div class="num tnum">${fmtMoney(diff)}</div><div class="ctx">${esc(t('acct-bank-bal-diff-ctx'))}</div></div>` +
        `<div class="prog"><div class="lbl" style="color:var(--ink2);font-size:11.5px">${esc(t('acct-bank-progress'))}</div><div class="bar"><i style="width:${pct}%"></i></div>` +
        `<div class="ctx tnum">${esc(t('acct-bank-progress-ctx', { total: String(total), matched: String(matched), pending: String(num(s.unmatched_count)) }))}</div></div></div>`
    );
}

// 行内「新建交易」卡(记收入/支出/内部转账 + 科目 + 摘要 → match new_tx)。
export function createCard(l: Record<string, unknown>, accounts: Cand[], txKind: string): string {
    const amt = Math.abs(Number(l.amount) || 0);
    const kinds = [
        ['income', 'acct-bank-kind-income'],
        ['expense', 'acct-bank-kind-expense'],
        ['transfer', 'acct-bank-kind-transfer'],
    ];
    const segs = kinds
        .map(
            (k) =>
                `<button data-act="txkind" data-k="${k[0]}" class="${txKind === k[0] ? 'on' : ''}">${esc(t(k[1]))}</button>`
        )
        .join('');
    const accs = accounts
        .map(
            (a) =>
                `<option value="${esc(a.id)}">${esc(a.code)} ${esc(a.name_zh || a.name_th || '')}</option>`
        )
        .join('');
    return (
        `<div class="create" data-id="${esc(l.id)}"><div class="seg">${segs}</div>` +
        `<div class="frow"><div class="fld"><label>${esc(t('acct-bank-tx-acc'))} *</label><select id="tx-acc"><option value="">${esc(t('acct-bank-tx-pick'))}</option>${accs}</select></div>` +
        `<div class="fld" style="flex:0 0 140px"><label>${esc(t('acct-bank-tx-amt'))}</label><input value="${esc(fmtMoney(amt))}" disabled></div></div>` +
        `<div class="frow" style="margin-bottom:2px"><div class="fld"><label>${esc(t('acct-bank-tx-memo'))}</label><input id="tx-memo" value="${esc(l.description)}"></div>` +
        `<div style="display:flex;align-items:flex-end;gap:8px"><button class="btn" data-act="txcancel">${esc(t('acct-bank-tx-collapse'))}</button>` +
        `<button class="btn primary" data-act="txsave" data-id="${esc(l.id)}" style="height:32px">${esc(t('acct-bank-tx-save'))}</button></div></div></div>`
    );
}

// ── 组合匹配:从候选单据勾选,合计须 == 流水金额(差额非零禁确认)──────────
type Cand = Record<string, unknown>;
let _combo: { line: Cand; docs: Cand[]; sel: boolean[] } | null = null;

export function openComboModal(line: Cand, candidates: Cand[], onDone: () => void): void {
    const docs = candidates.filter((c) => c.action === 'combo');
    _combo = { line, docs, sel: docs.map(() => false) };
    _renderCombo(onDone);
}

function _renderCombo(onDone: () => void): void {
    if (!_combo) return;
    const { line, docs, sel } = _combo;
    const amt = Math.abs(Number(line.amount) || 0);
    const sum = docs.reduce((s, d, i) => s + (sel[i] ? Number(d.amount) || 0 : 0), 0);
    const okEq = Math.abs(sum - amt) < 0.005 && sel.some(Boolean);
    const n = sel.filter(Boolean).length;
    const rows = docs.length
        ? docs
              .map(
                  (d, i) =>
                      `<div class="pick${sel[i] ? ' on' : ''}" data-combo-i="${i}"><span class="cb"></span>` +
                      `<span style="flex:1">${esc(d.doc_no || d.label || '')} · ${esc(d.label || '')} · ${esc(d.date || '')}</span>` +
                      `<b class="tnum">${fmtMoney(Number(d.amount) || 0)}</b></div>`
              )
              .join('')
        : `<div style="color:var(--ink3);padding:14px 0">${esc(t('acct-bank-combo-empty'))}</div>`;
    const inner = `<div class="acctm w560"><div class="mh"><div class="t">${esc(t('acct-bank-combo-title'))} · ${esc(fmtSigned(Number(line.amount) || 0))}</div><div class="x" data-close>×</div></div>
        <div class="mb"><div style="font-size:12px;color:var(--ink2);margin-bottom:7px">${esc(t('acct-bank-combo-hint'))}</div>${rows}
        <div class="sum ${okEq ? 'ok' : 'bad'}"><span>${esc(t('acct-bank-combo-picked'))} ${n} · ${fmtMoney(sum)}</span><span>${okEq ? esc(t('acct-bank-combo-zero')) : esc(t('acct-bank-combo-diff')) + ' ' + fmtMoney(Math.abs(amt - sum))}</span></div></div>
        <div class="mf"><button class="btn" data-close>${esc(t('acct-cancel'))}</button><button class="btn primary" id="combo-ok" ${okEq ? '' : 'disabled'}>${esc(t('acct-bank-combo-ok'))} ${n}</button></div></div>`;
    const mask = openAcctModal(inner);
    if (!mask) return;
    mask.querySelectorAll<HTMLElement>('[data-combo-i]').forEach((el) => {
        el.onclick = () => {
            const i = Number(el.dataset.comboI);
            if (_combo) _combo.sel[i] = !_combo.sel[i];
            _renderCombo(onDone);
        };
    });
    const ok = mask.querySelector<HTMLButtonElement>('#combo-ok');
    if (ok)
        ok.onclick = async () => {
            const ids = docs.filter((_, i) => sel[i]).map((d) => String(d.doc_id));
            try {
                await withLoading(ok, () =>
                    aapi('POST', withWs(`/api/accounting/bank/lines/${line.id}/match`), {
                        doc_ids: ids,
                    })
                );
                closeAcctModal();
                window.showToast?.(t('acct-bank-combo-done'), 'success');
                onDone();
            } catch (e) {
                window.showToast?.(acctErrMsg(e, 'acct-bank-match-fail'), 'error');
            }
        };
}

// ── 改科目(学习建议):换入账科目后确认入账(new_tx,remember 学习)─────────
export function openChAccModal(
    line: Cand,
    accounts: Cand[],
    suggestedAccId: string,
    onDone: () => void
): void {
    const opts = accounts
        .map(
            (a) =>
                `<option value="${esc(a.id)}"${a.id === suggestedAccId ? ' selected' : ''}>${esc(a.code)} ${esc(a.name_zh || a.name_th || '')}</option>`
        )
        .join('');
    const inner = `<div class="acctm"><div class="mh"><div class="t">${esc(t('acct-bank-chacc-title'))} · ${esc(line.description || '')}</div><div class="x" data-close>×</div></div>
        <div class="mb"><div class="field"><label>${esc(t('acct-bank-chacc-acc'))}</label><select class="inp" id="ch-acc">${opts}</select></div>
        <div style="font-size:11px;color:var(--ink3)">${esc(t('acct-bank-chacc-learn'))}</div></div>
        <div class="mf"><button class="btn" data-close>${esc(t('acct-cancel'))}</button><button class="btn primary" id="ch-ok">${esc(t('acct-bank-chacc-save'))}</button></div></div>`;
    const mask = openAcctModal(inner);
    if (!mask) return;
    const ok = mask.querySelector<HTMLButtonElement>('#ch-ok');
    const sel = mask.querySelector<HTMLSelectElement>('#ch-acc');
    if (ok && sel)
        ok.onclick = async () => {
            const kind = (Number(line.amount) || 0) >= 0 ? 'income' : 'expense';
            try {
                await withLoading(ok, () =>
                    aapi('POST', withWs(`/api/accounting/bank/lines/${line.id}/match`), {
                        new_tx: {
                            kind,
                            account_id: sel.value,
                            memo: line.description || '',
                            remember: true,
                        },
                    })
                );
                closeAcctModal();
                window.showToast?.(t('acct-bank-chacc-done'), 'success');
                onDone();
            } catch (e) {
                window.showToast?.(acctErrMsg(e, 'acct-bank-match-fail'), 'error');
            }
        };
}

// ── 导入对账单(multipart;sha256 查重 409;坏文件 422 人话不扣费)──────────
export function openImportModal(onDone: () => void): void {
    const inp = document.createElement('input');
    inp.type = 'file';
    inp.accept = '.pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.xlsx,.xls,.xlsm,.csv,.tsv';
    inp.style.display = 'none';
    document.body.appendChild(inp);
    inp.onchange = async () => {
        const file = inp.files && inp.files[0];
        inp.remove();
        if (!file) return;
        const inner = `<div class="acctm"><div class="mh"><div class="t">${esc(t('acct-bank-import-title'))}</div></div>
            <div class="mb"><div style="font-size:12.5px;margin-bottom:9px">${esc(file.name)} · ${Math.round(file.size / 1024)}KB</div>
            <div class="ab"><div class="bar"><i style="width:40%"></i></div></div>
            <div style="font-size:11.5px;color:var(--ink2);margin-top:8px" id="imp-msg">${esc(t('acct-bank-import-parsing'))}</div></div></div>`;
        openAcctModal(inner);
        const fd = new FormData();
        fd.append('file', file);
        try {
            const headers: Record<string, string> = {
                Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
            };
            try {
                const ws = window._wsHeader && window._wsHeader();
                if (ws) for (const k in ws) if (ws[k] != null) headers[k] = ws[k] as string;
            } catch (_) {
                /* 切换器未就绪 · 静默 */
            }
            const r = await fetch(withWs('/api/accounting/bank/import'), {
                method: 'POST',
                headers: headers as HeadersInit,
                body: fd,
            });
            const body = (await r.json().catch(() => null)) as {
                ok?: boolean;
                data?: { inserted?: number; skipped?: number; parsed?: number };
                error?: { code?: string };
            } | null;
            closeAcctModal();
            if (body && body.ok && body.data) {
                const d = body.data;
                window.showToast?.(
                    t('acct-bank-import-done', {
                        parsed: String(d.parsed ?? 0),
                        inserted: String(d.inserted ?? 0),
                        skipped: String(d.skipped ?? 0),
                    }),
                    'success'
                );
                onDone();
            } else {
                const code = (body && body.error && body.error.code) || 'acct.unexpected';
                const key =
                    code === 'acct.bank.duplicate_file'
                        ? 'acct-bank-import-dup'
                        : 'acct-bank-import-fail';
                window.showToast?.(t(key), 'error');
            }
        } catch (_) {
            closeAcctModal();
            window.showToast?.(t('acct-bank-import-fail'), 'error');
        }
    };
    inp.click();
}

// ── 手工凭证模板弹窗(从手工凭证屏移入以控行数 · M=手工凭证状态上下文)──────────
interface MjTplCtx {
    templates: { id: string; name: string; lines: Cand[]; use_count?: number }[];
    rows: { acc: string; memo: string; dr: number; cr: number; bad?: boolean }[];
    memo: string;
    dirty: boolean;
}

export function openTemplateModal(M: MjTplCtx, render: () => void): void {
    const list = M.templates.length
        ? M.templates
              .map(
                  (tp, i) =>
                      `<div class="pick" style="cursor:default"><div style="flex:1"><div style="font-weight:650;font-size:13px">${esc(tp.name)}</div>` +
                      `<div style="color:var(--ink3);font-size:11px;margin-top:2px">${tp.lines.length} ${esc(t('acct-mj-tpl-rows'))} · ${esc(t('acct-mj-tpl-used', { n: String(tp.use_count || 0) }))}</div></div>` +
                      `<button class="btn primary" data-tplact="use" data-i="${i}">${esc(t('acct-mj-tpl-use'))}</button><button class="btn ghost" data-tplact="del" data-i="${i}">${esc(t('acct-mj-tpl-del'))}</button></div>`
              )
              .join('')
        : `<div style="color:var(--ink3);padding:14px 0">${esc(t('acct-mj-tpl-empty'))}</div>`;
    const mask = openAcctModal(
        `<div class="acctm w560"><div class="mh"><div class="t">${esc(t('acct-mj-tpl-title'))}</div><div class="x" data-close>×</div></div>` +
            `<div class="mb mjx">${list}<div style="padding:9px 0 2px;color:var(--ink3);font-size:11px">${esc(t('acct-mj-tpl-note'))}</div></div></div>`
    );
    mask?.querySelectorAll<HTMLElement>('[data-tplact]').forEach((b) => {
        b.onclick = () => {
            const i = Number(b.dataset.i);
            if (b.dataset.tplact === 'use') _useTpl(M, render, i);
            else _delTpl(M, render, i);
        };
    });
}

function _useTpl(M: MjTplCtx, render: () => void, i: number): void {
    const tp = M.templates[i];
    if (!tp) return;
    M.rows = tp.lines.map((l) => ({ acc: String(l.account_id || ''), memo: '', dr: 0, cr: 0 }));
    while (M.rows.length < 2) M.rows.push({ acc: '', memo: '', dr: 0, cr: 0 });
    M.memo = tp.name;
    M.dirty = true;
    closeAcctModal();
    render();
    window.showToast?.(
        t('acct-mj-tpl-applied', { name: tp.name, n: String(tp.lines.length) }),
        'success'
    );
    document
        .getElementById('page-acct-manual')
        ?.querySelector<HTMLElement>('[data-mj="dr"]')
        ?.focus();
}

function _delTpl(M: MjTplCtx, render: () => void, i: number): void {
    const tp = M.templates[i];
    if (!tp) return;
    acctConfirm(
        t('acct-mj-tpl-del-title', { name: tp.name }),
        t('acct-mj-tpl-del-msg'),
        async () => {
            try {
                await aapi('DELETE', withWs(`/api/accounting/voucher-templates/${tp.id}`));
                M.templates.splice(i, 1);
                openTemplateModal(M, render);
                window.showToast?.(t('acct-mj-tpl-deleted'), 'info');
            } catch (e) {
                window.showToast?.(acctErrMsg(e, 'acct-mj-save-fail'), 'error');
            }
        }
    );
}

export function openSaveTplModal(M: MjTplCtx): void {
    const mask = openAcctModal(
        `<div class="acctm"><div class="mh"><div class="t">${esc(t('acct-mj-save-tpl'))}</div><div class="x" data-close>×</div></div>` +
            `<div class="mb"><div class="field"><label>${esc(t('acct-mj-tpl-name'))}</label><input class="inp" id="tpl-name" placeholder="${esc(t('acct-mj-tpl-name-ph'))}"></div></div>` +
            `<div class="mf"><button class="btn" data-close>${esc(t('acct-cancel'))}</button><button class="btn primary" id="tpl-save">${esc(t('acct-ok'))}</button></div></div>`
    );
    const inp = mask?.querySelector<HTMLInputElement>('#tpl-name');
    mask?.querySelector<HTMLButtonElement>('#tpl-save')?.addEventListener('click', async () => {
        const name = (inp?.value || '').trim();
        if (!name) {
            inp?.classList.add('bad');
            return;
        }
        const lines = M.rows
            .filter((r) => r.acc)
            .map((r) => ({
                account_id: r.acc,
                dr_cr: r.dr > 0 ? 'debit' : 'credit',
                memo: r.memo || null,
            }));
        try {
            const r = (await aapi('POST', withWs('/api/accounting/voucher-templates'), {
                name,
                lines,
            })) as { template?: MjTplCtx['templates'][number] };
            if (r.template) M.templates.push(r.template);
            closeAcctModal();
            window.showToast?.(t('acct-mj-tpl-saved', { name }), 'success');
        } catch (e) {
            window.showToast?.(acctErrMsg(e, 'acct-mj-save-fail'), 'error');
        }
    });
}
