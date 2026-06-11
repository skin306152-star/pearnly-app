// 银行对账主屏(window.loadAcctBank · 做账组排出账本前)。
// 交互基准 docs/accounting/bank-recon-mj/03-交互原型.html — 行为/文案/状态/差额门控/部分失败 100% 照搬;
// 数据全走真 API /api/accounting/bank/*(summary/lines/candidates/match/harvest/exclude/restore/unmatch)。
/* global escapeHtml, t */
import { aapi, withWs, acctErrMsg, AcctError, acctConfirm } from './acct-common.js';
import {
    openComboModal,
    openChAccModal,
    openImportModal,
    fmtSigned,
    withBusy,
    gateHtml,
    bandHtml,
    createCard,
    toolbarHtml,
    offlineGuard,
} from './acct-bank-modals.js';

type Row = Record<string, unknown>;
type Cand = Record<string, unknown>;
const HIGH = 85; // THRESH_AUTO(bank_recon_scoring)· 与后端 harvest 自动阈值一致
const SUGGEST = 60; // THRESH_SUGGEST

const S = {
    gate: '' as string,
    accounts: [] as Cand[], // COA 科目(新建交易/改科目 select)
    bankAccounts: [] as Cand[],
    summary: null as Record<string, unknown> | null,
    lines: [] as Row[],
    cand: {} as Record<string, Cand[]>, // line_id → 候选(降序)
    accountId: '' as string,
    period: '' as string,
    filter: 'all',
    search: '',
    sortDesc: true,
    page: 1,
    pageSize: 10,
    expanded: null as string | null,
    txKind: 'income',
};

const esc = (s: unknown) => escapeHtml(String(s == null ? '' : s));
const num = (v: unknown) => Number(v || 0);
const signed = (l: Row) => (l.direction === 'in' ? 1 : -1) * Math.abs(num(l.amount));

// 流水 → 建议等级(后端候选驱动 · 与 harvest 阈值对齐)。
function confOf(l: Row): { conf: string; top: Cand | null } {
    const cands = S.cand[String(l.id)] || [];
    const top = cands[0] || null;
    if (!top) return { conf: 'none', top: null };
    if (top.kind === 'learned') return { conf: 'learn', top };
    if (top.action === 'link' && num(top.score) >= HIGH) return { conf: 'high', top };
    if (top.action === 'link' && num(top.score) >= SUGGEST) return { conf: 'sugg', top };
    return { conf: 'none', top };
}

function sec(): HTMLElement | null {
    return document.getElementById('page-acct-bank');
}

// ── 数据加载 ───────────────────────────────────────────────────────────────
async function load(): Promise<void> {
    S.gate = '';
    try {
        const [acc, ba, sm] = await Promise.all([
            aapi('GET', withWs('/api/accounting/accounts')) as Promise<{ accounts?: Cand[] }>,
            aapi('GET', withWs('/api/accounting/bank/accounts')) as Promise<{ accounts?: Cand[] }>,
            aapi('GET', withWs('/api/accounting/bank/summary')) as Promise<{ summary?: Row }>,
        ]);
        S.accounts = acc.accounts || [];
        S.bankAccounts = ba.accounts || [];
        S.summary = sm.summary || null;
        const path =
            '/api/accounting/bank/lines' +
            (S.accountId ? '?account=' + encodeURIComponent(S.accountId) : '') +
            (S.period ? (S.accountId ? '&' : '?') + 'period=' + encodeURIComponent(S.period) : '');
        const lr = (await aapi('GET', withWs(path))) as { items?: Row[] };
        S.lines = lr.items || [];
        const un = S.lines.filter((l) => l.status === 'unmatched');
        const got = await Promise.all(
            un.map((l) =>
                aapi('GET', withWs(`/api/accounting/bank/lines/${l.id}/candidates`))
                    .then((r) => (r as { candidates?: Cand[] }).candidates || [])
                    .catch(() => [] as Cand[])
            )
        );
        S.cand = {};
        un.forEach((l, i) => (S.cand[String(l.id)] = got[i]));
    } catch (e) {
        const code = e instanceof AcctError ? e.code : 'acct.unexpected';
        S.gate =
            code === 'pos.module_disabled'
                ? 'plan'
                : code === 'acct.forbidden'
                  ? 'noperm'
                  : code === 'workspace.required'
                    ? 'nows'
                    : 'error';
    }
    render();
}

// ── 渲染 ────────────────────────────────────────────────────────────────────
function rowLeft(l: Row): string {
    return (
        `<div class="bank"><div class="d">${esc(l.description)}</div><div class="m tnum">${esc(String(l.line_date).slice(5))} · ${esc(l.bank_ref || '')}</div></div>` +
        `<span class="amt tnum ${l.direction === 'in' ? 'in' : ''}">${esc(fmtSigned(signed(l)))}</span><span class="arrow">→</span>`
    );
}

function rowHtml(l: Row, zone: string): string {
    if (zone === 'matched') {
        return (
            `<div class="row fade" data-id="${esc(l.id)}">${rowLeft(l)}<div class="match"><div class="v">${esc(t('acct-bank-matched-to'))}</div></div>` +
            `<span class="done-tag" style="margin-left:auto">${esc(t('acct-bank-done'))}</span><button class="lnk" data-act="undo" data-id="${esc(l.id)}">${esc(t('acct-bank-undo'))}</button></div>`
        );
    }
    if (zone === 'excluded') {
        return (
            `<div class="row fade" data-id="${esc(l.id)}">${rowLeft(l)}<div class="match"><div class="v mut">${esc(t('acct-bank-excluded'))}</div></div>` +
            `<button class="lnk" data-act="restore" data-id="${esc(l.id)}" style="margin-left:auto">${esc(t('acct-bank-restore'))}</button></div>`
        );
    }
    const { conf, top } = confOf(l);
    const sug = top ? String(top.label || '') : '';
    const reason = top ? String(top.reason || '') : '';
    let mid: string, acts: string;
    if (conf === 'high') {
        mid = `<div class="match"><div class="v">${esc(sug)}<span class="conf" data-tip="${esc(t('acct-bank-high-tip'))}">${esc(t('acct-bank-high'))}</span></div><div class="m">${esc(reason)}</div></div>`;
        acts = `<button class="btn ghost" data-act="notmine" data-id="${esc(l.id)}">${esc(t('acct-bank-notmine'))}</button><button class="btn primary" data-act="confirm" data-id="${esc(l.id)}">${esc(t('acct-bank-confirm'))}</button>`;
    } else if (conf === 'learn') {
        mid = `<div class="match"><div class="v">${esc(sug)}<span class="conf learn" data-tip="${esc(t('acct-bank-learn-tip'))}">${esc(t('acct-bank-learn'))}</span></div><div class="m">${esc(reason)}</div></div>`;
        acts = `<button class="btn" data-act="chacc" data-id="${esc(l.id)}">${esc(t('acct-bank-chacc'))}</button><button class="btn primary" data-act="confirm" data-id="${esc(l.id)}">${esc(t('acct-bank-confirm'))}</button>`;
    } else if (conf === 'sugg') {
        mid = `<div class="match"><div class="v">${esc(sug)}</div><div class="m">${esc(reason || t('acct-bank-sugg-sub'))}</div></div>`;
        acts = `<button class="btn" data-act="combo" data-id="${esc(l.id)}">${esc(t('acct-bank-combo'))}</button><button class="btn primary" data-act="confirm" data-id="${esc(l.id)}">${esc(t('acct-bank-confirm'))}</button>`;
    } else {
        mid = `<div class="match"><div class="v mut">${esc(t('acct-bank-nomatch'))}</div><div class="m">${esc(t('acct-bank-nomatch-sub'))}</div></div>`;
        acts = `<button class="btn" data-act="combo" data-id="${esc(l.id)}">${esc(t('acct-bank-combo'))}</button><button class="btn" data-act="newtx" data-id="${esc(l.id)}">${esc(t('acct-bank-newtx'))} ▾</button><button class="lnk" data-act="exclude" data-id="${esc(l.id)}">${esc(t('acct-bank-exclude'))}</button>`;
    }
    let html = `<div class="row" data-id="${esc(l.id)}">${rowLeft(l)}${mid}<div class="act">${acts}</div></div>`;
    if (S.expanded === String(l.id)) html += createCard(l, S.accounts, S.txKind);
    return html;
}

function bodyHtml(): string {
    let L = S.lines.slice().sort((a, b) => {
        const da = String(a.line_date),
            db = String(b.line_date);
        return S.sortDesc ? (da < db ? 1 : -1) : da > db ? 1 : -1;
    });
    if (S.search)
        L = L.filter((l) =>
            String(l.description || '')
                .toLowerCase()
                .includes(S.search.toLowerCase())
        );
    if (S.filter !== 'all')
        L = L.filter((l) => l.status === (S.filter === 'un' ? 'unmatched' : S.filter));

    const un = S.lines.filter((l) => l.status === 'unmatched');
    if (L.length === 0) {
        const big = S.search
            ? t('acct-bank-empty-search', { q: S.search })
            : t('acct-bank-empty-filter');
        return `<div class="empty"><div class="big">${esc(big)}</div><div class="d">${esc(t('acct-bank-empty-filter-d'))}</div><button class="btn" data-act="clearf">${esc(t('acct-bank-clearf'))}</button></div>`;
    }
    if (un.length === 0 && S.filter === 'all' && !S.search) {
        return (
            `<div class="donebox"><div class="ic">✓</div><div style="font-weight:700;font-size:15px">${esc(t('acct-bank-done-title'))}</div>` +
            `<div style="color:var(--ink2);font-size:12.5px;margin-top:5px">${esc(t('acct-bank-done-sub', { total: String(S.lines.length) }))}</div>` +
            `<div style="margin-top:13px"><button class="btn" data-act="gobooks">${esc(t('acct-bank-goclose'))}</button>` +
            `<button class="lnk" data-act="filter" data-f="matched" style="margin-left:10px">${esc(t('acct-bank-view-matched'))}</button></div></div>`
        );
    }
    const high = L.filter((l) => l.status === 'unmatched' && confOf(l).conf === 'high');
    const rest = L.filter((l) => l.status === 'unmatched' && confOf(l).conf !== 'high');
    const done = L.filter((l) => l.status === 'matched');
    const exc = L.filter((l) => l.status === 'excluded');
    const paged = rest.length > S.pageSize;
    const restShow = paged ? rest.slice((S.page - 1) * S.pageSize, S.page * S.pageSize) : rest;
    let body = '';
    if (high.length)
        body +=
            `<div class="sect"><span class="st">${esc(t('acct-bank-sec-high', { n: String(high.length) }))}</span><span class="sc">${esc(t('acct-bank-sec-high-d'))}</span>` +
            `<span class="hv"><button class="btn primary" data-act="harvest">${esc(t('acct-bank-harvest', { n: String(high.length) }))}</button></span></div>` +
            high.map((l) => rowHtml(l, 'un')).join('');
    if (rest.length)
        body +=
            `<div class="sect"${high.length ? ' style="border-top:1px solid var(--line2);margin-top:4px"' : ''}><span class="st">${esc(t('acct-bank-sec-rest', { n: String(rest.length) }))}</span><span class="sc">${esc(t('acct-bank-sec-rest-d'))}</span></div>` +
            restShow.map((l) => rowHtml(l, 'un')).join('');
    if (paged)
        body +=
            `<div class="pager"><span>${esc(t('acct-bank-pager', { total: String(rest.length), page: String(S.page), pages: String(Math.ceil(rest.length / S.pageSize)) }))}</span>` +
            `<button class="btn ghost" data-act="page" data-p="-1" ${S.page <= 1 ? 'disabled' : ''}>${esc(t('acct-bank-prev'))}</button>` +
            `<button class="btn ghost" data-act="page" data-p="1" ${S.page >= Math.ceil(rest.length / S.pageSize) ? 'disabled' : ''}>${esc(t('acct-bank-next'))}</button></div>`;
    if (done.length && (S.filter === 'all' || S.filter === 'matched'))
        body +=
            `<div class="sect" style="border-top:1px solid var(--line2);margin-top:4px"><span class="st" style="color:var(--ink2)">${esc(t('acct-bank-sec-done', { n: String(done.length) }))}</span></div>` +
            done.map((l) => rowHtml(l, 'matched')).join('');
    if (exc.length && (S.filter === 'all' || S.filter === 'excluded'))
        body += exc.map((l) => rowHtml(l, 'excluded')).join('');
    return body;
}

function render(): void {
    const el = sec();
    if (!el) return;
    let inner: string;
    if (S.gate) {
        inner = gateHtml(S.gate);
    } else {
        const head = `<div class="ph"><div><div class="t">${esc(t('acct-bank-title'))}</div><div class="sub">${esc(t('acct-bank-subtitle'))}</div></div></div>`;
        if (!S.summary && !S.lines.length) {
            inner = `<div class="ab">${head}<div class="panel"><div style="padding:22px 18px;display:flex;flex-direction:column;gap:13px"><div class="skel" style="width:46%"></div><div class="skel" style="width:88%"></div><div class="skel" style="width:74%"></div></div></div></div>`;
        } else if (S.lines.length === 0) {
            inner =
                `<div class="ab">${head}<div class="panel"><div class="empty"><div class="big">${esc(t('acct-bank-onb-title'))}</div>` +
                `<div class="d">${esc(t('acct-bank-onb-d'))}</div><div class="steps">` +
                [1, 2, 3]
                    .map(
                        (n) =>
                            `<div class="step"><div class="n">${n}</div><div class="t">${esc(t('acct-bank-onb-s' + n + '-t'))}</div><div class="d">${esc(t('acct-bank-onb-s' + n + '-d'))}</div></div>`
                    )
                    .join('') +
                `</div><div style="margin-top:16px"><button class="btn primary" style="height:36px;padding:0 17px" data-act="import">${esc(t('acct-bank-onb-import'))}</button></div></div></div></div>`;
        } else {
            const offbar =
                typeof navigator !== 'undefined' && navigator.onLine === false
                    ? `<div class="offbar">${esc(t('acct-bank-offbar'))}</div>`
                    : '';
            inner = `<div class="ab">${head}${offbar}<div class="panel">${bandHtml(S.summary || {})}${toolbarHtml(S)}${bodyHtml()}</div></div>`;
        }
    }
    el.innerHTML = inner;
    const accSel = el.querySelector<HTMLSelectElement>('#ab-acc');
    if (accSel)
        accSel.onchange = () => {
            S.accountId = accSel.value;
            S.page = 1;
            load();
        };
    const perSel = el.querySelector<HTMLSelectElement>('#ab-period');
    if (perSel)
        perSel.onchange = () => {
            S.period = perSel.value;
            S.page = 1;
            load();
        };
    const sr = el.querySelector<HTMLInputElement>('#ab-srch');
    if (sr)
        sr.oninput = () => {
            S.search = sr.value;
            S.page = 1;
            const pos = sr.selectionStart;
            render();
            const n = sec()?.querySelector<HTMLInputElement>('#ab-srch');
            if (n) {
                n.focus();
                try {
                    n.setSelectionRange(pos, pos);
                } catch (_) {
                    /* noop */
                }
            }
        };
}

// ── 动作 ────────────────────────────────────────────────────────────────────
function lineById(id: string): Row | undefined {
    return S.lines.find((l) => String(l.id) === id);
}

async function doConfirm(l: Row, top: Cand): Promise<void> {
    const body =
        top.action === 'link'
            ? { voucher_id: top.voucher_id }
            : {
                  new_tx: {
                      kind: top.tx_kind || (l.direction === 'in' ? 'income' : 'expense'),
                      account_id: top.account_id,
                      memo: l.description || '',
                      remember: top.kind === 'learned',
                  },
              };
    await aapi('POST', withWs(`/api/accounting/bank/lines/${l.id}/match`), body);
    window.showToast?.(
        t(top.kind === 'learned' ? 'acct-bank-confirm-learn' : 'acct-bank-confirm-ok'),
        'success'
    );
    await load();
}

function bind(): void {
    const el = sec();
    if (!el) return;
    el.onclick = async (e) => {
        const target = (e.target as HTMLElement).closest<HTMLElement>('[data-act]');
        if (!target) return;
        const act = target.dataset.act as string;
        const id = target.dataset.id || '';
        const l = id ? lineById(id) : undefined;
        // 断网时所有写动作早退人话(验收 Q4 · 状态不乱)
        if (
            [
                'import',
                'harvest',
                'confirm',
                'combo',
                'chacc',
                'txsave',
                'exclude',
                'restore',
                'undo',
            ].includes(act) &&
            offlineGuard()
        )
            return;
        switch (act) {
            case 'reload':
                render();
                load();
                break;
            case 'stub':
                break;
            case 'gobooks':
                window.routeTo?.('acct-books');
                break;
            case 'filter':
                S.filter = target.dataset.f || 'all';
                S.page = 1;
                render();
                break;
            case 'clearf':
                S.filter = 'all';
                S.search = '';
                S.page = 1;
                render();
                break;
            case 'sort':
                S.sortDesc = !S.sortDesc;
                render();
                break;
            case 'page':
                S.page += Number(target.dataset.p);
                render();
                break;
            case 'import':
                openImportModal(load);
                break;
            case 'harvest': {
                const high = S.lines.filter(
                    (x) => x.status === 'unmatched' && confOf(x).conf === 'high'
                );
                await withBusy(target, async () => {
                    try {
                        const r = (await aapi('POST', withWs('/api/accounting/bank/harvest'), {
                            line_ids: high.map((x) => String(x.id)),
                        })) as { matched?: number; total?: number };
                        const m = num(r.matched),
                            tot = num(r.total);
                        if (m < tot)
                            window.showToast?.(
                                t('acct-bank-harvest-partial', {
                                    ok: String(m),
                                    fail: String(tot - m),
                                }),
                                'warn'
                            );
                        else
                            window.showToast?.(
                                t('acct-bank-harvest-done', { n: String(m) }),
                                'success'
                            );
                        await load();
                    } catch (err) {
                        window.showToast?.(acctErrMsg(err, 'acct-bank-match-fail'), 'error');
                    }
                });
                break;
            }
            case 'confirm': {
                if (!l) break;
                const { top } = confOf(l);
                if (!top) break;
                await withBusy(target, async () => {
                    try {
                        await doConfirm(l, top);
                    } catch (err) {
                        window.showToast?.(acctErrMsg(err, 'acct-bank-match-fail'), 'error');
                    }
                });
                break;
            }
            case 'notmine':
                if (l) S.cand[id] = [];
                render();
                window.showToast?.(t('acct-bank-notmine-done'), 'info');
                break;
            case 'combo':
                if (l) openComboModal(l, S.cand[id] || [], load);
                break;
            case 'chacc': {
                if (!l) break;
                const top = confOf(l).top;
                openChAccModal(l, S.accounts, top ? String(top.account_id || '') : '', load);
                break;
            }
            case 'newtx':
                S.expanded = S.expanded === id ? null : id;
                render();
                break;
            case 'txkind':
                S.txKind = target.dataset.k || 'income';
                render();
                break;
            case 'txcancel':
                S.expanded = null;
                render();
                break;
            case 'txsave': {
                if (!l) break;
                const accSel = el.querySelector<HTMLSelectElement>('#tx-acc');
                const memo = el.querySelector<HTMLInputElement>('#tx-memo');
                if (!accSel || !accSel.value) {
                    accSel?.classList.add('bad');
                    window.showToast?.(t('acct-bank-tx-need-acc'), 'error');
                    break;
                }
                await withBusy(target, async () => {
                    try {
                        await aapi('POST', withWs(`/api/accounting/bank/lines/${l.id}/match`), {
                            new_tx: {
                                kind: S.txKind,
                                account_id: accSel.value,
                                memo: (memo && memo.value) || l.description || '',
                            },
                        });
                        S.expanded = null;
                        window.showToast?.(t('acct-bank-tx-done'), 'success');
                        await load();
                    } catch (err) {
                        window.showToast?.(acctErrMsg(err, 'acct-bank-match-fail'), 'error');
                    }
                });
                break;
            }
            case 'exclude':
            case 'restore':
                if (!l) break;
                await aapi('POST', withWs(`/api/accounting/bank/lines/${l.id}/${act}`)).catch(
                    () => {}
                );
                window.showToast?.(
                    t(act === 'exclude' ? 'acct-bank-exclude-done' : 'acct-bank-restore-done'),
                    'info'
                );
                await load();
                break;
            case 'undo':
                if (!l) break;
                acctConfirm(t('acct-bank-undo-title'), t('acct-bank-undo-msg'), async () => {
                    try {
                        await aapi('POST', withWs(`/api/accounting/bank/lines/${l.id}/unmatch`));
                        window.showToast?.(t('acct-bank-undo-done'), 'info');
                        await load();
                    } catch (err) {
                        window.showToast?.(acctErrMsg(err, 'acct-bank-match-fail'), 'error');
                    }
                });
                break;
        }
    };
}

window.loadAcctBank = function () {
    const el = sec();
    if (!el) return;
    S.summary = null;
    S.lines = [];
    S.gate = '';
    S.filter = 'all';
    S.search = '';
    S.page = 1;
    S.expanded = null;
    render();
    bind();
    load();
};

if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('acct-bank', () => {
        if (document.getElementById('page-acct-bank')?.querySelector('.ab')) render();
    });
}
