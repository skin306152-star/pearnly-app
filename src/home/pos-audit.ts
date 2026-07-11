// POS 屏 · 操作记录/异常(老板后台 · 主程序 · window.loadPosAudit)
// 防内盗速览:进页先看每个收银员的异常汇总卡(作废/退货/折扣 次数+金额、长短款,异常值标红)
// → 点某项下钻到那几笔明细(时间/单号/金额/授权人)。对标 Square 的 Comps&Voids/Discounts。
// 接 GET /api/pos/admin/audit/summary(汇总)+ GET .../audit/events?kind=(下钻)。四态齐 · 手机优先。
// view 级权限(同报表 pos.report.view)。
/* global t, token, escapeHtml */
import { activeWsId, posErrMsg } from './inventory-common';

type Kind = 'void' | 'refund' | 'discount';

interface Row {
    cashier_id: string | null;
    cashier_name: string | null;
    sales_count: number;
    sales_amount: string;
    void_count: number;
    void_amount: string;
    refund_count: number;
    refund_amount: string;
    discount_count: number;
    discount_amount: string;
    cash_short_over: string;
}
interface Ev {
    sold_at: string | null;
    kind: Kind;
    cashier_name: string | null;
    amount: string;
    receipt_no: string;
    authorized_by: string | null;
}

type RangeKey = 'today' | 'week' | 'month' | 'custom';
let range: RangeKey = 'today';
let customFrom = '';
let customTo = '';
let cashierFilter = '';
let cashiers: { id: string; display_name: string }[] = [];
let ws = 0;
let rows: Row[] = [];
let total: Row | null = null;
let loaded = false;
let errCode = '';
// 当前下钻:哪张卡的哪个指标(点开显该收银员那几笔)。
let drill: { cashier: string | null; kind: Kind } | null = null;
let drillEvents: Ev[] = [];
let drillLoading = false;

function ymd(d: Date): string {
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return d.getFullYear() + '-' + m + '-' + day;
}

function resolveRange(): { from: string; to: string } {
    const now = new Date();
    const today = ymd(now);
    if (range === 'today') return { from: today, to: today };
    if (range === 'month') {
        const first = new Date(now.getFullYear(), now.getMonth(), 1);
        return { from: ymd(first), to: today };
    }
    if (range === 'custom') return { from: customFrom || today, to: customTo || today };
    const dow = (now.getDay() + 6) % 7;
    const mon = new Date(now);
    mon.setDate(now.getDate() - dow);
    return { from: ymd(mon), to: today };
}

function hdr(): Record<string, string> {
    return { Authorization: 'Bearer ' + (typeof token === 'string' ? token : '') };
}

function baht(v: string | number): string {
    return Math.round(Number(v) || 0).toLocaleString('en-US');
}

function fmtTime(iso: string | null): string {
    if (!iso) return '';
    const [d, rest] = iso.split('T');
    return d + ' ' + (rest || '').slice(0, 5);
}

const STYLE = `
.posaud{width:100%;margin:0;padding:26px 0 60px 28px;font-size:13.5px;color:var(--ink);}
.posaud h1{font-size:21px;font-weight:700;margin:0 0 4px;}
.posaud .sub{color:var(--ink2);font-size:13px;margin-bottom:18px;}
.posaud .toolbar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:16px;}
.posaud .seg{display:inline-flex;border:1px solid var(--line);border-radius:10px;overflow:hidden;}
.posaud .seg button{border:0;background:var(--card);color:var(--ink2);padding:8px 14px;font-size:13px;cursor:pointer;}
.posaud .seg button.on{background:var(--btn-blue,var(--accent));color:var(--accent-ink);}
.posaud select,.posaud input[type=date]{height:36px;border:1px solid var(--line);border-radius:9px;padding:0 10px;background:var(--card);color:var(--ink);font-size:13px;}
.posaud .cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;}
.posaud .card{border:1px solid var(--line);border-radius:14px;background:var(--card);overflow:hidden;}
.posaud .card.total{border-color:var(--btn-blue,var(--accent));}
.posaud .chead{display:flex;align-items:center;gap:8px;padding:13px 16px;border-bottom:1px solid var(--line2);}
.posaud .chead .nm{font-weight:700;font-size:14.5px;}
.posaud .chead .sc{margin-left:auto;color:var(--ink2);font-size:12.5px;font-variant-numeric:tabular-nums;}
.posaud .met{display:grid;grid-template-columns:repeat(2,1fr);}
.posaud .m{padding:12px 16px;border-top:1px solid var(--line2);cursor:pointer;background:none;border-left:0;border-right:0;border-bottom:0;text-align:left;color:var(--ink);}
.posaud .m:nth-child(even){border-left:1px solid var(--line2);}
.posaud .m.static{cursor:default;}
.posaud .m:not(.static):hover{background:var(--line2);}
.posaud .m .lbl{color:var(--ink2);font-size:12px;margin-bottom:3px;display:flex;align-items:center;gap:5px;}
.posaud .m .val{font-size:15px;font-weight:700;font-variant-numeric:tabular-nums;}
.posaud .m .cnt{font-size:12px;color:var(--ink3);margin-left:5px;font-weight:600;}
.posaud .m.warn .val,.posaud .m.warn .cnt{color:#c2410c;}
.posaud .m.bad .val,.posaud .m.bad .cnt{color:#dc2626;}
.posaud .m.on{background:var(--line2);box-shadow:inset 3px 0 0 var(--btn-blue,var(--accent));}
.posaud .drill{border-top:1px solid var(--line);background:var(--bg,transparent);}
.posaud table{width:100%;border-collapse:collapse;font-size:12.5px;}
.posaud th{text-align:left;padding:8px 14px;color:var(--ink2);font-weight:600;border-bottom:1px solid var(--line2);white-space:nowrap;}
.posaud td{padding:8px 14px;border-bottom:1px solid var(--line2);vertical-align:top;}
.posaud td.num{text-align:right;font-variant-numeric:tabular-nums;}
.posaud .state{padding:44px 0;text-align:center;color:var(--ink3);font-size:13.5px;}
.posaud .dstate{padding:18px;text-align:center;color:var(--ink3);font-size:12.5px;}
@media(max-width:640px){.posaud{padding:20px 0 50px 16px;}.posaud .cards{grid-template-columns:1fr;}}
`;

function ensureStyle(): void {
    if (document.getElementById('posaud-style')) return;
    const s = document.createElement('style');
    s.id = 'posaud-style';
    s.textContent = STYLE;
    document.head.appendChild(s);
}

function ensureShell(sec: HTMLElement): void {
    if (sec.dataset.posaudInit === '1') return;
    ensureStyle();
    sec.innerHTML = `<div class="posaud">
        <h1>${escapeHtml(t('posaudit.title'))}</h1>
        <div class="sub">${escapeHtml(t('posaudit.sub'))}</div>
        <div id="posaud-body"><div class="state">${escapeHtml(t('rpay.loading'))}</div></div>
    </div>`;
    sec.dataset.posaudInit = '1';
}

function toolbarHtml(): string {
    const btn = (k: RangeKey, label: string) =>
        `<button class="${range === k ? 'on' : ''}" data-range="${k}">${escapeHtml(label)}</button>`;
    const custom =
        range === 'custom'
            ? `<input type="date" id="posaud-from" value="${escapeHtml(customFrom)}">
               <span>–</span>
               <input type="date" id="posaud-to" value="${escapeHtml(customTo)}">`
            : '';
    const opts =
        `<option value="">${escapeHtml(t('posaudit.all_cashiers'))}</option>` +
        cashiers
            .map(
                (c) =>
                    `<option value="${escapeHtml(c.id)}"${c.id === cashierFilter ? ' selected' : ''}>${escapeHtml(c.display_name)}</option>`
            )
            .join('');
    return `<div class="toolbar">
        <div class="seg">${btn('today', t('rep-range-today'))}${btn('week', t('rep-range-week'))}${btn('month', t('rep-range-month'))}${btn('custom', t('rep-range-custom'))}</div>
        ${custom}
        <select id="posaud-cashier">${opts}</select>
    </div>`;
}

// 一个可下钻指标格:severity 决定标红(bad)/标橙(warn)/常态。count>0 才可点开。
function metricHtml(
    r: Row,
    kind: Kind,
    label: string,
    count: number,
    amount: string,
    sev: 'bad' | 'warn' | ''
): string {
    const active = drill && drill.cashier === r.cashier_id && drill.kind === kind;
    const cls = ['m', count > 0 ? sev : '', active ? 'on' : ''].filter(Boolean).join(' ');
    const cnt = count > 0 ? `<span class="cnt">×${count}</span>` : '';
    return `<button class="${cls}" data-cashier="${escapeHtml(r.cashier_id || '')}" data-kind="${kind}">
        <div class="lbl">${escapeHtml(label)}</div>
        <div><span class="val">฿${baht(amount)}</span>${cnt}</div>
    </button>`;
}

function cashHtml(r: Row): string {
    const n = Number(r.cash_short_over) || 0;
    const sev = n < 0 ? 'bad' : n > 0 ? 'warn' : '';
    const sign = n > 0 ? '+' : '';
    const cls = ['m', 'static', sev].filter(Boolean).join(' ');
    return `<div class="${cls}">
        <div class="lbl">${escapeHtml(t('posaudit.cash_diff'))}</div>
        <div><span class="val">${sign}฿${baht(Math.abs(n))}</span></div>
    </div>`;
}

function cardHtml(r: Row, isTotal: boolean): string {
    const name = isTotal
        ? t('posaudit.total_label')
        : r.cashier_name || t('posaudit.unknown_cashier');
    const drillPanel = !isTotal && drill && drill.cashier === r.cashier_id ? drillHtml() : '';
    return `<div class="card${isTotal ? ' total' : ''}">
        <div class="chead">
            <span class="nm">${escapeHtml(name)}</span>
            <span class="sc">${escapeHtml(t('posaudit.sales_n', { n: String(r.sales_count) }))} · ฿${baht(r.sales_amount)}</span>
        </div>
        <div class="met">
            ${metricHtml(r, 'void', t('posaudit.void'), r.void_count, r.void_amount, 'bad')}
            ${metricHtml(r, 'refund', t('posaudit.refund'), r.refund_count, r.refund_amount, 'bad')}
            ${metricHtml(r, 'discount', t('posaudit.discount'), r.discount_count, r.discount_amount, 'warn')}
            ${cashHtml(r)}
        </div>
        ${drillPanel}
    </div>`;
}

function drillHtml(): string {
    if (drillLoading)
        return `<div class="drill"><div class="dstate">${escapeHtml(t('rpay.loading'))}</div></div>`;
    if (!drillEvents.length)
        return `<div class="drill"><div class="dstate">${escapeHtml(t('posaudit.no_events'))}</div></div>`;
    const body = drillEvents
        .map(
            (e) => `<tr>
            <td>${escapeHtml(fmtTime(e.sold_at))}</td>
            <td>${escapeHtml(e.receipt_no)}</td>
            <td class="num">฿${baht(e.amount)}</td>
            <td>${escapeHtml(e.authorized_by || '—')}</td>
        </tr>`
        )
        .join('');
    return `<div class="drill"><table><thead><tr>
        <th>${escapeHtml(t('posaudit.ev_time'))}</th>
        <th>${escapeHtml(t('posaudit.ev_receipt'))}</th>
        <th>${escapeHtml(t('posaudit.ev_amount'))}</th>
        <th>${escapeHtml(t('posaudit.ev_auth'))}</th>
    </tr></thead><tbody>${body}</tbody></table></div>`;
}

function bodyHtml(): string {
    if (errCode) return `<div class="state">${escapeHtml(posErrMsg(errCode, 'rep-error'))}</div>`;
    if (!loaded) return `<div class="state">${escapeHtml(t('rpay.loading'))}</div>`;
    if (!rows.length) return `<div class="state">${escapeHtml(t('rep-empty'))}</div>`;
    const totalCard = total ? cardHtml(total, true) : '';
    const cards = rows.map((r) => cardHtml(r, false)).join('');
    return `<div class="cards">${totalCard}${cards}</div>`;
}

function render(): void {
    const body = document.getElementById('posaud-body');
    if (!body) return;
    body.innerHTML = toolbarHtml() + bodyHtml();
    bind();
}

function bind(): void {
    document.querySelectorAll<HTMLElement>('#posaud-body [data-range]').forEach((b) => {
        b.onclick = () => {
            range = b.dataset.range as RangeKey;
            if (range === 'custom') {
                const today = ymd(new Date());
                if (!customTo) customTo = today;
                if (!customFrom) customFrom = today;
            }
            drill = null;
            fetchSummary();
        };
    });
    const from = document.getElementById('posaud-from') as HTMLInputElement | null;
    const to = document.getElementById('posaud-to') as HTMLInputElement | null;
    if (from) from.onchange = () => ((customFrom = from.value), (drill = null), fetchSummary());
    if (to) to.onchange = () => ((customTo = to.value), (drill = null), fetchSummary());
    const sel = document.getElementById('posaud-cashier') as HTMLSelectElement | null;
    if (sel) sel.onchange = () => ((cashierFilter = sel.value), (drill = null), fetchSummary());
    document.querySelectorAll<HTMLElement>('#posaud-body .m[data-kind]').forEach((m) => {
        m.onclick = () => onDrill(m.dataset.cashier || '', m.dataset.kind as Kind);
    });
}

function qs(extra?: Record<string, string>): string {
    const { from, to } = resolveRange();
    const p = new URLSearchParams({ workspace_client_id: String(ws), from, to });
    if (cashierFilter) p.set('cashier_id', cashierFilter);
    if (extra) for (const k in extra) p.set(k, extra[k]);
    return p.toString();
}

async function fetchSummary(): Promise<void> {
    loaded = false;
    errCode = '';
    render();
    try {
        const r = await fetch('/api/pos/admin/audit/summary?' + qs(), { headers: hdr() });
        const env = await r.json();
        if (!env || env.ok !== true)
            throw new Error((env && env.error && env.error.code) || 'pos.unexpected');
        rows = env.data.rows || [];
        total = env.data.total || null;
        loaded = true;
        render();
    } catch (e) {
        errCode = e instanceof Error ? e.message : 'pos.unexpected';
        render();
    }
}

async function onDrill(cashier: string, kind: Kind): Promise<void> {
    // 再点同一格=收起。
    if (drill && drill.cashier === (cashier || null) && drill.kind === kind) {
        drill = null;
        render();
        return;
    }
    drill = { cashier: cashier || null, kind };
    drillEvents = [];
    drillLoading = true;
    render();
    try {
        const extra: Record<string, string> = { kind };
        if (cashier) extra.cashier_id = cashier;
        const r = await fetch('/api/pos/admin/audit/events?' + qs(extra), { headers: hdr() });
        const env = await r.json();
        drillEvents = (env && env.ok === true && env.data && env.data.events) || [];
    } catch (_) {
        drillEvents = [];
    } finally {
        drillLoading = false;
        render();
    }
}

async function loadCashiers(): Promise<void> {
    try {
        const r = await fetch('/api/pos/admin/cashiers?workspace_client_id=' + ws, {
            headers: hdr(),
        });
        const env = await r.json();
        cashiers = (env && env.ok === true && env.data && env.data.cashiers) || [];
    } catch (_) {
        cashiers = [];
    }
}

window.loadPosAudit = function () {
    const sec = document.getElementById('page-pos-audit');
    if (!sec) return;
    ensureShell(sec);
    const id = activeWsId();
    const body = document.getElementById('posaud-body');
    if (id == null) {
        if (body) body.innerHTML = window.wsEmptyHtml ? window.wsEmptyHtml('posaud-pick-ws') : '';
        const pick = document.getElementById('posaud-pick-ws');
        if (pick)
            pick.onclick = () =>
                window.requireWorkspace
                    ? window.requireWorkspace(() => window.loadPosAudit!())
                    : window.openWorkspaceChooserUI?.();
        return;
    }
    ws = id;
    range = 'today';
    cashierFilter = '';
    drill = null;
    loadCashiers().then(() => fetchSummary());
};
