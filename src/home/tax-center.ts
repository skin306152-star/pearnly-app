// 自动报税 · 屏1 报税中心(照搬 Pearnly_报税_UI预览/01 · 一站列本期所有税种)。
// 北极星(本月要交税合计)+ 最近截止行动卡 → 税种列表(PP30/PND53/PND3 × 状态 × 截止)。
// 这是对 PEAK「报税埋三处」的差异点:一个入口看全。点行进对应复核屏。
// GET /api/tax/filings?period= → {summary,items}。空/未结账 = 诚实提示去做账。
/* global t, escapeHtml */
import {
    aapi,
    acctErrMsg,
    currentPeriod,
    injectStyle,
    periodLabel,
    recentPeriods,
    withWs,
} from './acct-common.js';
import { fmtBaht } from './purchase-common.js';
import { injectTaxBase, kindKey, normFiling, statusChip } from './tax-common.js';
import type { Filing, FilingKind } from './tax-common.js';

const PAGE_CSS = `
.taxp.tc .row{display:flex;align-items:center;gap:14px;padding:15px 22px;border-bottom:1px solid var(--line2);cursor:pointer;}
.taxp.tc .row:last-child{border-bottom:0;}
.taxp.tc .row:hover{background:var(--bg);}
.taxp.tc .row .ic{width:40px;height:40px;border-radius:10px;background:var(--accent-weak);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:var(--accent-deep);flex-shrink:0;}
.taxp.tc .row .nm{font-weight:650;font-size:14px;}
.taxp.tc .row .d{color:var(--ink3);font-size:12px;margin-top:2px;}
.taxp.tc .row .amt{text-align:right;margin-left:auto;}
.taxp.tc .row .amt .v{font-weight:700;font-size:15px;font-variant-numeric:tabular-nums;}
.taxp.tc .row .amt .dd{font-size:11.5px;color:var(--ink3);margin-top:2px;}
.taxp.tc .attn{display:flex;align-items:center;gap:13px;background:var(--amber-weak);border:1px solid var(--amber-weak);border-radius:12px;padding:10px 12px 10px 14px;}
.taxp.tc .attn .l{display:flex;align-items:center;gap:6px;font-size:11.5px;color:var(--amber);font-weight:600;}
.taxp.tc .attn .l .pip{width:6px;height:6px;border-radius:50%;background:var(--amber);}
.taxp.tc .attn .m{font-size:14px;font-weight:700;margin-top:2px;color:var(--ink);}
.taxp.tc .attn .go{height:34px;padding:0 13px;border-radius:9px;background:var(--card);border:1px solid var(--amber-weak);color:var(--amber);font-weight:650;font-size:12.5px;display:flex;align-items:center;cursor:pointer;}
`;

const KIND_IC: Record<FilingKind, string> = { pp30: 'VAT', pnd53: '53', pnd3: '3' };

let period = currentPeriod();

interface Summary {
    total_due: number;
    next_due_date: string | null;
    filed_count: number;
    pending_count: number;
}

function rowDesc(f: Filing): string {
    if (f.kind === 'pp30') {
        const b = f.breakdown as Record<string, number>;
        return `${t('tax-pp30-out')} ${fmtBaht(b.output_vat)} − ${t('tax-pp30-in')} ${fmtBaht(b.input_vat_claimable)} = ${fmtBaht(b.net)}`;
    }
    const b = f.breakdown as Record<string, number>;
    return `${t('tax-pnd-desc')} · ${b.line_count || 0} ${t('tax-pnd-count')}`;
}

// 详情副文案:已报显回执;留抵显「留抵下月」非负数;待报显截止。
function rowMeta(f: Filing): string {
    if (f.status === 'filed')
        return f.receipt_no ? `${t('tax-filed-on')} ${f.receipt_no}` : t('tax-st-filed');
    const b = f.breakdown as Record<string, number>;
    if (f.kind === 'pp30' && Number(b.net) < 0)
        return `${t('tax-carry-forward')} ${fmtBaht(b.carry_forward)}`;
    return f.due_date ? `${t('tax-due')} ${window.formatDate?.(f.due_date) || f.due_date}` : '—';
}

function rowAmount(f: Filing): string {
    const b = f.breakdown as Record<string, number>;
    if (f.kind === 'pp30' && Number(b.net) < 0)
        return `<span class="v tnum" style="color:var(--green);">${fmtBaht(b.carry_forward)}</span>`;
    return `<span class="v tnum">${fmtBaht(f.net_amount)}</span>`;
}

function rowHtml(f: Filing): string {
    return `<div class="row" data-id="${escapeHtml(f.id)}" data-kind="${f.kind}">
        <div class="ic">${KIND_IC[f.kind]}</div>
        <div><div class="nm">${escapeHtml(t(kindKey(f.kind)))}</div><div class="d">${escapeHtml(rowDesc(f))}</div></div>
        <div class="amt">${rowAmount(f)}<div class="dd">${escapeHtml(rowMeta(f))}</div></div>
        ${statusChip(f)}</div>`;
}

// 最近截止行动卡:最早到期的未报税表(有则显,催办)。
function attnHtml(items: Filing[]): string {
    const next = items
        .filter((f) => f.status !== 'filed' && f.due_date)
        .sort((a, b) => (a.due_date! < b.due_date! ? -1 : 1))[0];
    if (!next) return '';
    const days = next.due_date
        ? Math.ceil((new Date(next.due_date).getTime() - Date.now()) / 86400000)
        : null;
    const daysText =
        days != null && days >= 0
            ? ` · ${t('tax-days-left').replace('{n}', String(days))}`
            : days != null
              ? ` · ${t('tax-overdue')}`
              : '';
    return `<div class="attn">
        <div><div class="l"><span class="pip"></span>${escapeHtml(t('tax-nearest-due'))}</div>
        <div class="m">${escapeHtml(t(kindKey(next.kind)))} · ${escapeHtml(window.formatDate?.(next.due_date!) || next.due_date!)}${escapeHtml(daysText)}</div></div>
        <div class="go" data-go="${escapeHtml(next.id)}" data-kind="${next.kind}">${escapeHtml(t('tax-go-file'))} →</div></div>`;
}

function shellHtml(items: Filing[], summary: Summary): string {
    const rows = items.length
        ? items.map(rowHtml).join('')
        : `<div class="state">${escapeHtml(t('tax-empty'))}<br><span style="font-size:12px;">${escapeHtml(t('tax-empty-hint'))}</span></div>`;
    const months = recentPeriods()
        .map(
            (p) =>
                `<option value="${p}" ${p === period ? 'selected' : ''}>${escapeHtml(periodLabel(p))}</option>`
        )
        .join('');
    return `<div class="taxp tc"><div class="wrap">
        <div class="ph">
            <div><div class="t">${escapeHtml(t('tax-center-title'))}</div><div class="sub">${escapeHtml(t('tax-center-subtitle'))}</div></div>
            <select class="mo" id="tax-center-month">${months}</select>
        </div>
        <div class="panel">
            <div class="band">
                <div class="star">
                    <div class="lbl">${escapeHtml(t('tax-total-due'))}</div>
                    <div class="num tnum">${fmtBaht(summary.total_due)}</div>
                    <div class="ctx">${escapeHtml(t('tax-pending-n').replace('{n}', String(summary.pending_count)))} · ${escapeHtml(t('tax-filed-n').replace('{n}', String(summary.filed_count)))}</div>
                </div>
                ${attnHtml(items)}
            </div>
            ${rows}
        </div>
    </div></div>`;
}

function goReview(id: string, kind: string): void {
    pendingFiling = { id, kind: kind as FilingKind, period };
    window.routeTo?.(kind === 'pp30' ? 'tax-pp30' : 'tax-pnd');
}

interface PendingFiling {
    id: string;
    kind: FilingKind;
    period: string;
}

let pendingFiling: PendingFiling | null = null;

export function takePendingFiling(): PendingFiling | null {
    const p = pendingFiling;
    pendingFiling = null;
    return p;
}

function bind(sec: HTMLElement): void {
    const month = sec.querySelector<HTMLSelectElement>('#tax-center-month');
    if (month)
        month.onchange = () => {
            period = month.value;
            load();
        };
    sec.querySelectorAll<HTMLElement>('.row[data-id]').forEach((row) => {
        row.onclick = () => goReview(row.dataset.id!, row.dataset.kind!);
    });
    const go = sec.querySelector<HTMLElement>('.go[data-go]');
    if (go) go.onclick = () => goReview(go.dataset.go!, go.dataset.kind!);
}

async function load(): Promise<void> {
    const sec = document.getElementById('page-tax-center');
    if (!sec) return;
    sec.innerHTML = `<div class="taxp tc"><div class="wrap"><div class="panel"><div class="state">${escapeHtml(t('tax-loading'))}</div></div></div></div>`;
    try {
        const data = (await aapi('GET', withWs(`/api/tax/filings?period=${period}`))) as {
            summary?: Summary;
            items?: Record<string, unknown>[];
        };
        const items = (data.items || []).map(normFiling);
        const summary = data.summary || {
            total_due: 0,
            next_due_date: null,
            filed_count: 0,
            pending_count: 0,
        };
        sec.innerHTML = shellHtml(items, summary);
        bind(sec);
    } catch (e) {
        sec.innerHTML = `<div class="taxp tc"><div class="wrap"><div class="panel"><div class="state">${escapeHtml(acctErrMsg(e, 'tax.unexpected'))}<br><button class="btn" id="tax-center-retry" style="margin-top:12px;">${escapeHtml(t('tax-retry'))}</button></div></div></div></div>`;
        const retry = document.getElementById('tax-center-retry');
        if (retry) retry.onclick = () => load();
    }
}

window.loadTaxCenter = function () {
    const sec = document.getElementById('page-tax-center');
    if (!sec) return;
    injectTaxBase();
    injectStyle('tax-center-css', PAGE_CSS);
    load();
};

if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('tax-center', () => {
        if (document.getElementById('page-tax-center')?.querySelector('.taxp.tc'))
            window.loadTaxCenter?.();
    });
}
