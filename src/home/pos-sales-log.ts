// POS 屏 · 交易明细日志(老板后台 · 主程序 · window.loadPosSalesLog)
// 逐笔销售流水:时间/收据号/收银员/商品/金额/付款方式/所属班次。筛选=日期范围(今天/本周/
// 本月/自定义,同销售报表口径)+ 收银员。导出按当前筛选出 CSV(列口径同 Google Sheet 留档)。
// 接 GET /api/pos/admin/sales-log(分页)+ GET .../sales-log/export.csv(下载)。
// view 级权限(同销售报表 pos.report.view,非"收款设置"那类老板专属改配置)。四态齐。
/* global t, token, showToast, escapeHtml */
import { activeWsId, posErrMsg } from './inventory-common';

interface LogItem {
    id: string;
    receipt_no: string;
    sold_at: string;
    cashier_id: string | null;
    cashier_name: string;
    items: string;
    qty_total: string;
    grand_total: string;
    method: string;
    shift_opened_at: string;
    shift_closed_at: string;
}
interface CashierOpt {
    id: string;
    display_name: string;
}

interface DayGroup {
    date: string;
    rows: LogItem[];
    total: number;
}

type RangeKey = 'today' | 'week' | 'month' | 'custom';
let range: RangeKey = 'today';
let customFrom = '';
let customTo = '';
let cashierFilter = '';
let cashiers: CashierOpt[] = [];
let ws = 0;
let items: LogItem[] = [];
let total = 0;
let expandedDates = new Set<string>();
const PAGE_SIZE = 50;

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

function bahtInt(v: string | number): string {
    return Math.round(Number(v) || 0).toLocaleString('en-US');
}

function fmtTime(iso: string): { d: string; t: string } {
    if (!iso) return { d: '', t: '' };
    const [d, rest] = iso.split('T');
    return { d, t: (rest || '').slice(0, 8) };
}

function shiftLabel(item: LogItem): string {
    if (!item.shift_opened_at) return '';
    const open = fmtTime(item.shift_opened_at).t;
    const close = item.shift_closed_at ? fmtTime(item.shift_closed_at).t : t('poslog.shift_open');
    return open + '–' + close;
}

// 按日分组(照搬「采购/进项」按月分组折叠卡片的设计概念:标题行=日期+笔数+合计,
// 点击展开看逐笔明细)。items 本身已按 sold_at 倒序,分组保序即可,不用重排。
function groupByDay(rows: LogItem[]): DayGroup[] {
    const order: string[] = [];
    const map = new Map<string, LogItem[]>();
    for (const r of rows) {
        const d = fmtTime(r.sold_at).d || '—';
        if (!map.has(d)) {
            map.set(d, []);
            order.push(d);
        }
        map.get(d)!.push(r);
    }
    return order.map((date) => {
        const rows2 = map.get(date)!;
        return {
            date,
            rows: rows2,
            total: rows2.reduce((s, r) => s + (Number(r.grand_total) || 0), 0),
        };
    });
}

const STYLE = `
.poslog{width:100%;margin:0;padding:26px 0 60px 28px;font-size:13.5px;color:var(--ink);}
.poslog h1{font-size:21px;font-weight:700;color:var(--ink);margin:0 0 4px;}
.poslog .sub{color:var(--ink2);font-size:13px;margin-bottom:18px;}
.poslog .toolbar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:16px;}
.poslog .seg{display:inline-flex;border:1px solid var(--line);border-radius:10px;overflow:hidden;}
.poslog .seg button{border:0;background:var(--card);color:var(--ink2);padding:8px 14px;font-size:13px;cursor:pointer;}
.poslog .seg button.on{background:var(--btn-blue,var(--accent));color:var(--accent-ink);}
.poslog select,.poslog input[type=date]{height:36px;border:1px solid var(--line);border-radius:9px;padding:0 10px;background:var(--card);color:var(--ink);font-size:13px;}
.poslog .exp{margin-left:auto;height:36px;padding:0 16px;border-radius:9px;border:0;background:var(--btn-blue,var(--accent));color:var(--accent-ink);font-weight:600;font-size:13px;cursor:pointer;}
.poslog .cnt{color:var(--ink2);font-size:12.5px;margin-bottom:10px;}
.poslog .glist{border:1px solid var(--line);border-radius:14px;overflow:hidden;}
.poslog .grp+.grp,.poslog .grp-body+.grp{border-top:1px solid var(--line2);}
.poslog .grp{display:flex;align-items:center;gap:12px;padding:14px 16px;cursor:pointer;background:var(--card);}
.poslog .grp:hover{background:var(--line2);}
.poslog .grp .chev{transition:transform .15s;color:var(--ink3);flex:0 0 auto;}
.poslog .grp.open .chev{transform:rotate(90deg);}
.poslog .grp .d{font-weight:700;font-size:14px;color:var(--ink);}
.poslog .grp .n{color:var(--ink2);font-size:12.5px;}
.poslog .grp .t{margin-left:auto;font-weight:700;font-variant-numeric:tabular-nums;}
.poslog table{width:100%;border-collapse:collapse;font-size:13px;}
.poslog th{text-align:left;padding:9px 10px;color:var(--ink2);font-weight:600;border-bottom:1px solid var(--line);white-space:nowrap;}
.poslog td{padding:9px 10px;border-bottom:1px solid var(--line2);vertical-align:top;}
.poslog td.num{text-align:right;font-variant-numeric:tabular-nums;}
.poslog .more{width:100%;height:42px;margin-top:14px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--ink);font-size:13px;cursor:pointer;}
.poslog .state{padding:44px 0;text-align:center;color:var(--ink3);font-size:13.5px;}
`;

function ensureStyle(): void {
    if (document.getElementById('poslog-style')) return;
    const s = document.createElement('style');
    s.id = 'poslog-style';
    s.textContent = STYLE;
    document.head.appendChild(s);
}

function ensureShell(sec: HTMLElement): void {
    if (sec.dataset.poslogInit === '1') return;
    ensureStyle();
    sec.innerHTML = `<div class="poslog">
        <h1>${escapeHtml(t('poslog.title'))}</h1>
        <div class="sub">${escapeHtml(t('poslog.sub'))}</div>
        <div id="poslog-body"><div class="state">${escapeHtml(t('rpay.loading'))}</div></div>
    </div>`;
    sec.dataset.poslogInit = '1';
}

function toolbarHtml(): string {
    const btn = (k: RangeKey, label: string) =>
        `<button class="${range === k ? 'on' : ''}" data-range="${k}">${escapeHtml(label)}</button>`;
    const custom =
        range === 'custom'
            ? `<input type="date" id="poslog-from" value="${escapeHtml(customFrom)}">
               <span>–</span>
               <input type="date" id="poslog-to" value="${escapeHtml(customTo)}">`
            : '';
    const cashierOpts =
        `<option value="">${escapeHtml(t('poslog.all_cashiers'))}</option>` +
        cashiers
            .map(
                (c) =>
                    `<option value="${escapeHtml(c.id)}"${c.id === cashierFilter ? ' selected' : ''}>${escapeHtml(c.display_name)}</option>`
            )
            .join('');
    return `<div class="toolbar">
        <div class="seg">${btn('today', t('rep-range-today'))}${btn('week', t('rep-range-week'))}${btn('month', t('rep-range-month'))}${btn('custom', t('rep-range-custom'))}</div>
        ${custom}
        <select id="poslog-cashier">${cashierOpts}</select>
        <button class="exp" id="poslog-export">${escapeHtml(t('poslog.export'))}</button>
    </div>`;
}

function rowHtml(item: LogItem): string {
    const { t: tm } = fmtTime(item.sold_at);
    return `<tr>
        <td>${escapeHtml(tm)}</td>
        <td>${escapeHtml(item.receipt_no)}</td>
        <td>${escapeHtml(item.cashier_name || '—')}</td>
        <td>${escapeHtml(item.items)}</td>
        <td class="num">${escapeHtml(item.qty_total)}</td>
        <td class="num">฿${bahtInt(item.grand_total)}</td>
        <td>${escapeHtml(item.method)}</td>
        <td>${escapeHtml(shiftLabel(item))}</td>
    </tr>`;
}

function groupHtml(g: DayGroup): string {
    const open = expandedDates.has(g.date);
    const rows = g.rows.map(rowHtml).join('');
    return `<div class="grp${open ? ' open' : ''}" data-date="${escapeHtml(g.date)}">
        <svg class="chev" viewBox="0 0 20 20" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 5l6 5-6 5"/></svg>
        <span class="d">${escapeHtml(g.date)}</span>
        <span class="n">${escapeHtml(t('poslog.group_count', { n: String(g.rows.length) }))}</span>
        <span class="t">${escapeHtml(t('poslog.group_total'))} ฿${bahtInt(g.total)}</span>
    </div>
    <div class="grp-body"${open ? '' : ' style="display:none;"'}>
        <table><thead><tr>
            <th>${escapeHtml(t('poslog.col_time'))}</th>
            <th>${escapeHtml(t('poslog.col_receipt'))}</th>
            <th>${escapeHtml(t('poslog.col_cashier'))}</th>
            <th>${escapeHtml(t('poslog.col_items'))}</th>
            <th>${escapeHtml(t('poslog.col_qty'))}</th>
            <th>${escapeHtml(t('poslog.col_amount'))}</th>
            <th>${escapeHtml(t('poslog.col_method'))}</th>
            <th>${escapeHtml(t('poslog.col_shift'))}</th>
        </tr></thead><tbody>${rows}</tbody></table>
    </div>`;
}

function tableHtml(): string {
    if (!items.length) return `<div class="state">${escapeHtml(t('rep-empty'))}</div>`;
    const groups = groupByDay(items);
    const groupsHtml = groups.map(groupHtml).join('');
    const moreBtn =
        items.length < total
            ? `<button class="more" id="poslog-more">${escapeHtml(t('poslog.load_more'))}</button>`
            : '';
    return `<div class="cnt">${escapeHtml(t('poslog.count', { n: String(total) }))}</div>
        <div class="glist">${groupsHtml}</div>
        ${moreBtn}`;
}

function bindToolbar(): void {
    document.querySelectorAll<HTMLElement>('#poslog-body [data-range]').forEach((b) => {
        b.onclick = () => {
            range = b.dataset.range as RangeKey;
            if (range === 'custom') {
                const today = ymd(new Date());
                if (!customTo) customTo = today;
                if (!customFrom) customFrom = today;
            }
            fetchPage(true);
        };
    });
    const from = document.getElementById('poslog-from') as HTMLInputElement | null;
    const to = document.getElementById('poslog-to') as HTMLInputElement | null;
    if (from) from.onchange = () => ((customFrom = from.value), fetchPage(true));
    if (to) to.onchange = () => ((customTo = to.value), fetchPage(true));
    const cashierSel = document.getElementById('poslog-cashier') as HTMLSelectElement | null;
    if (cashierSel)
        cashierSel.onchange = () => ((cashierFilter = cashierSel.value), fetchPage(true));
    const exportBtn = document.getElementById('poslog-export');
    if (exportBtn) exportBtn.addEventListener('click', exportCsv);
    const moreBtn = document.getElementById('poslog-more');
    if (moreBtn) moreBtn.addEventListener('click', () => fetchPage(false));
    document.querySelectorAll<HTMLElement>('#poslog-body .grp').forEach((g) => {
        g.onclick = () => {
            const date = g.dataset.date || '';
            if (expandedDates.has(date)) expandedDates.delete(date);
            else expandedDates.add(date);
            render();
        };
    });
}

function render(): void {
    const body = document.getElementById('poslog-body');
    if (!body) return;
    body.innerHTML = toolbarHtml() + tableHtml();
    bindToolbar();
}

function queryString(extra?: Record<string, string>): string {
    const { from, to } = resolveRange();
    const p = new URLSearchParams({
        workspace_client_id: String(ws),
        from,
        to,
        lang: window._currentLang || 'th',
    });
    if (cashierFilter) p.set('cashier_id', cashierFilter);
    if (extra) for (const k in extra) p.set(k, extra[k]);
    return p.toString();
}

async function fetchPage(reset: boolean): Promise<void> {
    const body = document.getElementById('poslog-body');
    if (reset && body) {
        body.innerHTML = `<div class="state">${escapeHtml(t('rpay.loading'))}</div>`;
        expandedDates = new Set();
    }
    const offset = reset ? 0 : items.length;
    try {
        const r = await fetch(
            '/api/pos/admin/sales-log?' +
                queryString({ limit: String(PAGE_SIZE), offset: String(offset) }),
            { headers: hdr() }
        );
        const env = await r.json();
        if (!env || env.ok !== true)
            throw new Error((env && env.error && env.error.code) || 'pos.unexpected');
        items = reset ? env.data.items : items.concat(env.data.items);
        total = env.data.total;
        if (reset) {
            // 只有一天的数据(比如筛"今天")没什么好折叠的,首次加载直接摊开看;
            // 这一步只在刚拉到新数据时做一次,不能放进 render()——那样每次重渲染
            // (包括用户手动点击折叠)都会被重新摊开,点了等于没点。
            const groups = groupByDay(items);
            if (groups.length === 1) expandedDates.add(groups[0].date);
        }
        render();
    } catch (e) {
        if (body)
            body.innerHTML = `<div class="state">${escapeHtml(posErrMsg(e instanceof Error ? e.message : 'pos.unexpected', 'rep-error'))}</div>`;
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

async function exportCsv(): Promise<void> {
    try {
        const r = await fetch('/api/pos/admin/sales-log/export.csv?' + queryString(), {
            headers: hdr(),
        });
        if (!r.ok) throw new Error('pos.unexpected');
        const blob = await r.blob();
        const a = document.createElement('a');
        const objUrl = URL.createObjectURL(blob);
        a.href = objUrl;
        a.download = 'pearnly_pos_sales_log.csv';
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
            URL.revokeObjectURL(objUrl);
            a.remove();
        }, 100);
    } catch (_) {
        showToast(posErrMsg('pos.unexpected', 'pos.unexpected'), 'error');
    }
}

window.loadPosSalesLog = function () {
    const sec = document.getElementById('page-pos-sales-log');
    if (!sec) return;
    ensureShell(sec);
    const id = activeWsId();
    const body = document.getElementById('poslog-body');
    if (id == null) {
        if (body) body.innerHTML = window.wsEmptyHtml ? window.wsEmptyHtml('poslog-pick-ws') : '';
        const pick = document.getElementById('poslog-pick-ws');
        if (pick)
            pick.onclick = () =>
                window.requireWorkspace
                    ? window.requireWorkspace(() => window.loadPosSalesLog!())
                    : window.openWorkspaceChooserUI?.();
        return;
    }
    ws = id;
    range = 'today';
    cashierFilter = '';
    loadCashiers().then(() => fetchPage(true));
};
