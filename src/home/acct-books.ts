// 自动做账 · 屏4 出账本/报税包(照搬设计稿 04-出账本报税包 · 月末出口)。
// 信息带(月份 + 结账状态/结账按钮)→ 法定账本(总账/明细账/试算表)→ 报税材料(VAT/WHT)
// → 财报 → 打包条。未结 → 提示先结账 + 结账(二次确认 · 待审挡结给去逐笔审落点)。
/* global t, escapeHtml, showToast, currentLang */
import {
    AcctError,
    aapi,
    acctConfirm,
    acctErrMsg,
    currentPeriod,
    injectAcctBase,
    injectStyle,
    openAcctFile,
    periodLabel,
    recentPeriods,
    withWs,
} from './acct-common.js';
import { fmtBaht } from './purchase-common.js';

const PAGE_CSS = `
.acct.ab .band{display:flex;align-items:center;justify-content:space-between;padding:18px 22px;border-bottom:1px solid var(--line2);flex-wrap:wrap;gap:10px;}
.acct.ab .band .num{font-size:24px;font-weight:740;letter-spacing:-.5px;}
.acct.ab .band .lbl{color:var(--ink2);font-size:12.5px;margin-top:5px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;}
.acct.ab .ok{font-size:11px;background:var(--green-weak);color:var(--green);padding:2px 9px;border-radius:6px;font-weight:600;}
.acct.ab .openlbl{font-size:11px;background:var(--amber-weak);color:var(--amber);padding:2px 9px;border-radius:6px;font-weight:600;}
.acct.ab .mctl{display:flex;align-items:center;gap:10px;}
.acct.ab .mctl select{height:34px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--ink2);font-size:12.5px;padding:0 9px;outline:0;}
.acct.ab .grp{padding:11px 22px 5px;font-size:11.5px;color:var(--ink3);font-weight:600;letter-spacing:.3px;}
.acct.ab .row{display:flex;align-items:center;gap:14px;padding:13px 22px;border-bottom:1px solid var(--line2);}
.acct.ab .row:last-child{border-bottom:0;}
.acct.ab .row .nm{font-weight:600;font-size:13.5px;}
.acct.ab .row .d{color:var(--ink3);font-size:11.5px;margin-top:2px;}
.acct.ab .row .act{margin-left:auto;display:flex;gap:8px;flex-shrink:0;}
.acct.ab .allbar{padding:14px 22px;background:var(--line2);border-top:1px solid var(--line2);display:flex;align-items:center;gap:12px;flex-wrap:wrap;}
.acct.ab .allbar .t2{flex:1;min-width:180px;font-size:12.5px;color:var(--ink2);}
.acct.ab .closebar{display:flex;align-items:center;gap:12px;padding:13px 22px;background:var(--amber-weak);border-bottom:1px solid var(--line2);font-size:13px;color:var(--amber);flex-wrap:wrap;}
.acct.ab .closebar .msg{flex:1;min-width:180px;}
@media(max-width:600px){
  .acct.ab .row{flex-wrap:wrap;}
  .acct.ab .row .act{margin-left:0;width:100%;}
  .acct.ab .row .act .btn{flex:1;}
}
`;

interface BookRow {
    kind: string;
    path: 'books' | 'tax-reports' | 'financials';
    nameKey: string;
    descKey: string;
}

const GROUPS: { titleKey: string; rows: BookRow[] }[] = [
    {
        titleKey: 'acct-books-grp-legal',
        rows: [
            { kind: 'gl', path: 'books', nameKey: 'acct-book-gl', descKey: 'acct-book-gl-d' },
            {
                kind: 'subsidiary',
                path: 'books',
                nameKey: 'acct-book-sub',
                descKey: 'acct-book-sub-d',
            },
            {
                kind: 'trial_balance',
                path: 'books',
                nameKey: 'acct-book-tb',
                descKey: 'acct-book-tb-d',
            },
        ],
    },
    {
        titleKey: 'acct-books-grp-tax',
        rows: [
            {
                kind: 'vat',
                path: 'tax-reports',
                nameKey: 'acct-book-vat',
                descKey: 'acct-book-vat-d',
            },
            {
                kind: 'wht',
                path: 'tax-reports',
                nameKey: 'acct-book-wht',
                descKey: 'acct-book-wht-d',
            },
        ],
    },
    {
        titleKey: 'acct-books-grp-fin',
        rows: [
            {
                kind: 'financials',
                path: 'financials',
                nameKey: 'acct-book-fin',
                descKey: 'acct-book-fin-d',
            },
        ],
    },
];

let period = currentPeriod();
let closedThrough: string | null = null;
let pendingCount = 0;
let postedCount = 0;

function isClosed(): boolean {
    return !!closedThrough && period <= closedThrough;
}

function fileUrl(row: BookRow, fmt: 'pdf'): string {
    const kindParam = row.path === 'financials' ? '' : `&kind=${row.kind}`;
    const lang = (typeof currentLang === 'string' && currentLang) || 'th';
    return withWs(
        `/api/accounting/${row.path}?period=${period}${kindParam}&format=${fmt}&lang=${lang}`
    );
}

function rowsHtml(): string {
    return GROUPS.map(
        (g) =>
            `<div class="grp">${escapeHtml(t(g.titleKey))}</div>` +
            g.rows
                .map(
                    (r) => `<div class="row" data-kind="${r.kind}" data-path="${r.path}">
                <div><div class="nm">${escapeHtml(t(r.nameKey))}</div><div class="d">${escapeHtml(t(r.descKey))}</div></div>
                <div class="act"><button class="btn" data-act="preview">${escapeHtml(t('acct-preview'))}</button>
                <button class="btn primary" data-act="download">${escapeHtml(t('acct-download'))}</button></div>
            </div>`
                )
                .join('')
    ).join('');
}

function bandHtml(): string {
    const status = isClosed()
        ? `<span class="ok">${escapeHtml(t('acct-books-closed'))}</span>`
        : `<span class="openlbl">${escapeHtml(t('acct-books-open'))}</span>`;
    return `<div><div class="num tnum">${escapeHtml(periodLabel(period))}</div>
        <div class="lbl">${status}<span>${postedCount} ${escapeHtml(t('acct-posted-count'))}</span></div></div>
        <div class="mctl"><select id="acct-books-month">${recentPeriods()
            .map(
                (p) =>
                    `<option value="${p}" ${p === period ? 'selected' : ''}>${escapeHtml(periodLabel(p))}</option>`
            )
            .join('')}</select></div>`;
}

function closebarHtml(): string {
    if (isClosed()) return '';
    const pendingMsg = pendingCount
        ? `<span class="msg">${escapeHtml(t('acct-close-blocked-pre'))} ${pendingCount} ${escapeHtml(t('acct-close-blocked-post'))}</span>
           <button class="btn" id="acct-close-goreview">${escapeHtml(t('acct-go-review'))} →</button>`
        : `<span class="msg">${escapeHtml(t('acct-close-hint'))}</span>
           <button class="btn primary" id="acct-close-btn">${escapeHtml(t('acct-close-action'))}</button>`;
    return `<div class="closebar">${pendingMsg}</div>`;
}

function shellHtml(): string {
    return `<div class="acct ab"><div class="wrap">
        <div class="ph"><div><div class="t">${escapeHtml(t('acct-books-title'))}</div><div class="sub">${escapeHtml(t('acct-books-subtitle'))}</div></div></div>
        <div class="panel">
            <div class="band" id="acct-books-band">${bandHtml()}</div>
            <div id="acct-books-closebar">${closebarHtml()}</div>
            <div id="acct-books-rows">${rowsHtml()}</div>
            <div class="allbar">
                <div class="t2">${escapeHtml(t('acct-books-pack-d'))}</div>
                <button class="btn primary" id="acct-books-pack" style="height:38px;padding:0 18px;">${escapeHtml(t('acct-books-pack'))}</button>
            </div>
        </div>
    </div></div>`;
}

function bind(sec: HTMLElement): void {
    const month = sec.querySelector<HTMLSelectElement>('#acct-books-month');
    if (month)
        month.onchange = () => {
            period = month.value;
            load();
        };
    sec.querySelectorAll<HTMLElement>('.row[data-kind]').forEach((rowEl) => {
        const def = GROUPS.flatMap((g) => g.rows).find((r) => r.kind === rowEl.dataset.kind)!;
        rowEl.querySelectorAll<HTMLButtonElement>('[data-act]').forEach((btn) => {
            btn.onclick = async () => {
                btn.disabled = true;
                try {
                    await openAcctFile(
                        fileUrl(def, 'pdf'),
                        btn.dataset.act === 'download' ? `${def.kind}_${period}.pdf` : undefined
                    );
                } catch (e) {
                    showToast(acctErrMsg(e, 'acct.export_failed'), 'error');
                } finally {
                    btn.disabled = false;
                }
            };
        });
    });
    const pack = sec.querySelector<HTMLButtonElement>('#acct-books-pack');
    if (pack)
        pack.onclick = async () => {
            pack.disabled = true;
            try {
                await openAcctFile(
                    withWs(`/api/accounting/export-package?period=${period}`),
                    `pearnly_books_${period}.zip`
                );
            } catch (e) {
                showToast(acctErrMsg(e, 'acct.export_failed'), 'error');
            } finally {
                pack.disabled = false;
            }
        };
    const goReview = sec.querySelector<HTMLElement>('#acct-close-goreview');
    if (goReview) goReview.onclick = () => window.routeTo?.('acct-review');
    const closeBtn = sec.querySelector<HTMLButtonElement>('#acct-close-btn');
    if (closeBtn) closeBtn.onclick = () => confirmClose();
}

// 月末结账:不可逆 → 二次确认;成功报 VAT 结转结果;待审挡结给逐笔审落点。
function confirmClose(): void {
    acctConfirm(t('acct-close-action'), t('acct-close-confirm'), async () => {
        try {
            const data = (await aapi('POST', withWs('/api/accounting/close-period'), {
                period,
            })) as { closed?: string; vat_payable?: number };
            const vat = Number(data && data.vat_payable) || 0;
            showToast(`${t('acct-close-ok')} · ${t('acct-close-vat')} ${fmtBaht(vat)}`, 'success');
        } catch (e) {
            if (e instanceof AcctError && e.code === 'acct.unbalanced') {
                showToast(t('acct-close-blocked-toast'), 'error');
            } else {
                showToast(acctErrMsg(e, 'acct.unexpected'), 'error');
            }
        }
        load();
    });
}

async function load(): Promise<void> {
    const sec = document.getElementById('page-acct-books');
    if (!sec) return;
    sec.innerHTML = `<div class="acct ab"><div class="wrap"><div class="panel"><div class="state">${escapeHtml(t('acct-loading'))}</div></div></div></div>`;
    try {
        const [setData, sumData] = await Promise.all([
            aapi('GET', withWs('/api/accounting/settings')) as Promise<{
                settings?: { closed_through?: string | null };
            }>,
            aapi('GET', withWs(`/api/accounting/vouchers?period=${period}`)) as Promise<{
                summary?: { pending_count?: number; posted_count?: number };
            }>,
        ]);
        closedThrough = (setData.settings && setData.settings.closed_through) || null;
        pendingCount = (sumData.summary && sumData.summary.pending_count) || 0;
        postedCount = (sumData.summary && sumData.summary.posted_count) || 0;
        sec.innerHTML = shellHtml();
        bind(sec);
    } catch (e) {
        sec.innerHTML = `<div class="acct ab"><div class="wrap"><div class="panel"><div class="state">${escapeHtml(acctErrMsg(e, 'acct.unexpected'))}<br><button class="btn" id="acct-books-retry" style="margin-top:12px;">${escapeHtml(t('acct-retry'))}</button></div></div></div></div>`;
        const retry = document.getElementById('acct-books-retry');
        if (retry) retry.onclick = () => load();
    }
}

window.loadAcctBooks = function () {
    const sec = document.getElementById('page-acct-books');
    if (!sec) return;
    injectAcctBase();
    injectStyle('acct-books-css', PAGE_CSS);
    load();
};

if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('acct-books', () => {
        if (document.getElementById('page-acct-books')?.querySelector('.acct.ab'))
            window.loadAcctBooks?.();
    });
}
