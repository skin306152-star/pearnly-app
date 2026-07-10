// POS 屏9 · 销售报表(主程序内 · window.loadSalesReport)
// 视觉照搬概念稿 桌面/Pearnly_POS_UI预览/09-销售报表.html(09 §H):结构移植到 .posrep 作用域,
// 只改三处 —— ① 假数据→GET /api/pos/admin/report(04 §7 · B6)② 写死文案→i18n(4 语)③ 补四态(07)。
// 数据=收银卖货自动长出,无手录;不造假(概念稿的「较上周 +%」是 mock,接口无此项→不展示)。
/* global t, token, escapeHtml, currentLang */
import { activeWsId, localizedName, posErrMsg, type InvName } from './inventory-common.js';

interface Kpi {
    gross: string;
    sales_count: number;
    avg_ticket: string;
    refund: string;
    cost: string;
    gross_profit: string | null;
    cost_complete: boolean;
}
interface DayRow {
    date: string;
    gross: string;
    cost: string | null;
    gross_profit: string | null;
    cost_complete: boolean;
}
interface TopProduct {
    product_id: string;
    name: InvName;
    qty: string;
    gross: string;
    cost: string;
    gross_profit: string | null;
    cost_complete: boolean;
}
interface CashierRow {
    cashier_id: string;
    name: string;
    sales_count: number;
    gross: string;
}
interface Report {
    kpi: Kpi;
    by_day: DayRow[];
    by_method: Record<string, string>;
    top_products: TopProduct[];
    by_cashier: CashierRow[];
}

type RangeKey = 'today' | 'week' | 'month' | 'custom';
let range: RangeKey = 'week';
let customFrom = '';
let customTo = '';

function ymd(d: Date): string {
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return d.getFullYear() + '-' + m + '-' + day;
}

// 区间 → [from, to](本地日期 · 含端点)
function resolveRange(): { from: string; to: string } {
    const now = new Date();
    const today = ymd(now);
    if (range === 'today') return { from: today, to: today };
    if (range === 'month') {
        const first = new Date(now.getFullYear(), now.getMonth(), 1);
        return { from: ymd(first), to: today };
    }
    if (range === 'custom') {
        return { from: customFrom || today, to: customTo || today };
    }
    // week:本周一 → 今天(周一为周首)
    const dow = (now.getDay() + 6) % 7; // 周一=0
    const mon = new Date(now);
    mon.setDate(now.getDate() - dow);
    return { from: ymd(mon), to: today };
}

function bahtInt(v: string | number): string {
    return Math.round(Number(v) || 0).toLocaleString('en-US');
}

// 毛利/成本可能诚实置空(老单据无成本快照)——跟真 0 分开渲染,不拿 "—" 冒充 0,也不拿 0 冒充有数据。
function moneyOrUnknown(v: string | null): string {
    return v == null ? '—' : '฿' + bahtInt(v);
}

async function fetchReport(): Promise<Report> {
    const wsId = activeWsId();
    const { from, to } = resolveRange();
    const params = new URLSearchParams({ workspace_client_id: String(wsId), from, to });
    let body: { ok?: boolean; data?: Report; error?: { code?: string } };
    try {
        const headers: Record<string, string> = {
            Authorization: 'Bearer ' + (typeof token === 'string' ? token : ''),
        };
        const ws = window._wsHeader && window._wsHeader();
        if (ws) for (const k in ws) if (ws[k] != null) headers[k] = ws[k] as string;
        const r = await fetch('/api/pos/admin/report?' + params.toString(), {
            headers: headers as HeadersInit,
        });
        body = await r.json();
    } catch (_) {
        throw new Error('pos.unexpected');
    }
    if (body && body.ok === true && body.data) return body.data;
    throw new Error((body && body.error && body.error.code) || 'pos.unexpected');
}

// ── 渲染片段 ──
function rangeBar(): string {
    const btn = (k: RangeKey, label: string) =>
        `<button class="${range === k ? 'on' : ''}" data-range="${k}">${escapeHtml(label)}</button>`;
    const custom =
        range === 'custom'
            ? `<input type="date" id="rep-from" value="${escapeHtml(customFrom)}" />
               <span class="rep-dash">–</span>
               <input type="date" id="rep-to" value="${escapeHtml(customTo)}" />`
            : '';
    return `<div class="range">
        <div class="seg">${btn('today', t('rep-range-today'))}${btn('week', t('rep-range-week'))}${btn('month', t('rep-range-month'))}${btn('custom', t('rep-range-custom'))}</div>
        ${custom}
    </div>`;
}

function kpiCards(k: Kpi): string {
    const card = (label: string, value: string, unknown?: boolean, title?: string) =>
        `<div class="kpi"><div class="l">${escapeHtml(label)}</div><div class="v tnum${unknown ? ' unknown' : ''}"${
            title ? ` title="${escapeHtml(title)}"` : ''
        }>${value}</div></div>`;
    const profitUnknown = k.gross_profit == null;
    return `<div class="kpis">
        ${card(t('rep-kpi-gross'), '฿' + bahtInt(k.gross))}
        ${card(t('rep-kpi-count'), String(k.sales_count))}
        ${card(t('rep-kpi-avg'), '฿' + bahtInt(k.avg_ticket))}
        ${card(t('rep-kpi-refund'), '฿' + bahtInt(k.refund))}
        ${card(
            t('rep-kpi-profit'),
            moneyOrUnknown(k.gross_profit),
            profitUnknown,
            profitUnknown ? t('rep-profit-unknown') : undefined
        )}
    </div>`;
}

function chartPanel(byDay: DayRow[], byMethod: Record<string, string>): string {
    const max = byDay.reduce((m, d) => Math.max(m, Number(d.gross) || 0), 0) || 1;
    const cols = byDay.length
        ? byDay
              .map((d) => {
                  const h = Math.max(3, Math.round(((Number(d.gross) || 0) / max) * 100));
                  const lbl = d.date.slice(5).replace('-', '/'); // MM/DD
                  const tip = `${t('rep-kpi-gross')} ฿${bahtInt(d.gross)} · ${t('rep-kpi-profit')} ${moneyOrUnknown(d.gross_profit)}`;
                  return `<div class="col" title="${escapeHtml(tip)}"><div class="b" style="height:${h}%"></div><div class="x">${escapeHtml(lbl)}</div></div>`;
              })
              .join('')
        : `<div class="rep-state">${escapeHtml(t('rep-empty'))}</div>`;
    const pm = (color: string, label: string, amount: string) =>
        `<div class="pm"><div class="l"><span class="dot" style="background:var(--${color})"></span>${escapeHtml(label)}</div><div class="v tnum">฿${bahtInt(amount)}</div></div>`;
    return `<div class="panel">
        <div class="h">${escapeHtml(t('rep-chart-daily'))}</div>
        <div class="chart">${cols}</div>
        <div class="pmrow">
            ${pm('rep-green', t('rep-pm-cash'), byMethod.cash || '0')}
            ${pm('rep-blue', t('rep-pm-promptpay'), byMethod.promptpay || '0')}
            ${pm('rep-amber', t('rep-pm-card'), byMethod.card || '0')}
        </div>
    </div>`;
}

function listsPanel(top: TopProduct[], cashiers: CashierRow[]): string {
    const topRows = top.length
        ? top
              .map((p, i) => {
                  const profitUnknown = p.gross_profit == null;
                  return `<div class="row"><span class="rk">${i + 1}</span><span class="nm">${escapeHtml(
                      localizedName(p.name)
                  )} <span class="q">· ${escapeHtml(p.qty)} ${escapeHtml(t('rep-unit-items'))}</span></span><span class="v-col"><span class="v tnum">฿${bahtInt(
                      p.gross
                  )}</span><span class="pf tnum${profitUnknown ? ' unknown' : ''}">${escapeHtml(
                      t('rep-kpi-profit')
                  )} ${moneyOrUnknown(p.gross_profit)}</span></span></div>`;
              })
              .join('')
        : `<div class="rep-state sm">${escapeHtml(t('rep-empty'))}</div>`;
    const cashierRows = cashiers.length
        ? cashiers
              .map(
                  (c) =>
                      `<div class="row"><span class="nm">${escapeHtml(c.name || '—')}</span><span class="q">${c.sales_count} ${escapeHtml(t('rep-unit-orders'))}</span><span class="v tnum">฿${bahtInt(c.gross)}</span></div>`
              )
              .join('')
        : `<div class="rep-state sm">${escapeHtml(t('rep-empty'))}</div>`;
    return `<div class="panel">
        <div class="h">${escapeHtml(t('rep-top-products'))}</div>
        <div class="rows">${topRows}</div>
        <div class="h border-top">${escapeHtml(t('rep-by-cashier'))}</div>
        <div class="rows">${cashierRows}</div>
    </div>`;
}

function skeleton(): string {
    const kp = '<div class="kpi"><div class="rep-skel"></div></div>'.repeat(5);
    return `<div class="kpis">${kp}</div>
        <div class="cards2">
            <div class="panel"><div class="chart">${'<div class="col"><div class="b skel" style="height:60%"></div></div>'.repeat(7)}</div></div>
            <div class="panel"><div class="rows">${'<div class="row"><div class="rep-skel"></div></div>'.repeat(5)}</div></div>
        </div>`;
}

function setBody(html: string) {
    const b = document.getElementById('rep-body');
    if (b) b.innerHTML = html;
}

function bindRange() {
    document.querySelectorAll<HTMLElement>('#page-sales-report [data-range]').forEach((b) => {
        b.onclick = () => {
            range = b.dataset.range as RangeKey;
            if (range === 'custom') {
                const today = ymd(new Date());
                if (!customTo) customTo = today;
                if (!customFrom) customFrom = today;
            }
            renderHead();
            load();
        };
    });
    const from = document.getElementById('rep-from') as HTMLInputElement | null;
    const to = document.getElementById('rep-to') as HTMLInputElement | null;
    if (from)
        from.onchange = () => {
            customFrom = from.value;
            load();
        };
    if (to)
        to.onchange = () => {
            customTo = to.value;
            load();
        };
}

function renderHead() {
    const head = document.getElementById('rep-head');
    if (head) head.innerHTML = `<div class="t">${escapeHtml(t('rep-title'))}</div>${rangeBar()}`;
    bindRange();
}

async function load() {
    setBody(skeleton());
    let data: Report;
    try {
        data = await fetchReport();
    } catch (e) {
        const code = e instanceof Error ? e.message : 'pos.unexpected';
        setBody(
            `<div class="rep-state error">${escapeHtml(posErrMsg(code, 'rep-error'))}<br><button class="rep-retry" id="rep-retry">${escapeHtml(t('rep-retry'))}</button></div>`
        );
        const retry = document.getElementById('rep-retry');
        if (retry) retry.onclick = () => load();
        return;
    }
    const empty =
        (!data.kpi || data.kpi.sales_count === 0) && (!data.by_day || data.by_day.length === 0);
    if (empty) {
        setBody(`<div class="rep-state">${escapeHtml(t('rep-empty'))}</div>`);
        return;
    }
    setBody(
        kpiCards(data.kpi) +
            `<div class="cards2">${chartPanel(data.by_day || [], data.by_method || {})}${listsPanel(
                data.top_products || [],
                data.by_cashier || []
            )}</div>`
    );
}

function needWorkspaceHtml(): string {
    return `<div class="rep-state">${escapeHtml(t('rep-need-workspace'))}
        <button class="rep-retry" id="rep-pick-ws">${escapeHtml(t('rep-pick-workspace'))}</button></div>`;
}

window.loadSalesReport = function () {
    const sec = document.getElementById('page-sales-report');
    if (!sec) return;
    if (sec.dataset.repInit !== '1') {
        sec.classList.add('ui');
        sec.innerHTML = `<div class="posrep"><div class="wrap"><div class="ph" id="rep-head"></div><div id="rep-body"></div></div></div>`;
        sec.dataset.repInit = '1';
    }
    renderHead();
    if (activeWsId() == null) {
        setBody(needWorkspaceHtml());
        const pick = document.getElementById('rep-pick-ws');
        if (pick)
            pick.onclick = () =>
                window.requireWorkspace
                    ? window.requireWorkspace(() => window.loadSalesReport!())
                    : window.openWorkspaceChooserUI?.();
        return;
    }
    load();
};
