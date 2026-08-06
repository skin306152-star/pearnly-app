// POS 屏9 · 销售仪表盘(主程序内 · window.loadSalesReport)
// 2026-08-04 按 Zihao 定稿交互原型(交互原型v2)重建:① Hero 大横幅(内嵌全局日期器,按日/按月,
// 横幅与商品构成一起切,见 sales-report-hero)② 营业额走势(按月一页 · 点某天 → 全局切到那天)
// ③ 商品销售构成(sales-report-mix)④ 分时热力(近 14 天 × 8:00–22:00)。
// 环比口径:按日=上周同日(零售星期节律),按月=上一自然月,窗口语义由这里传 prev_from/prev_to。
// 本文件只管状态编排 + 走势/热力两卡;图表件在 sales-report-charts,类型与取数在 sales-report-common。
/* global t, escapeHtml */
import { activeWsId, posErrMsg } from './inventory-common.js';
import {
    barChartHtml,
    lineChartHtml,
    tipCardHtml,
    tipHide,
    tipShow,
    type XyBucket,
} from './sales-report-charts.js';
import {
    CHEV_L,
    CHEV_R,
    type DayRow,
    type Granularity,
    HEAT_DAYS,
    HOUR_HI,
    HOUR_LO,
    type Report,
    type SectionState,
    addDays,
    addMonths,
    axisFmt,
    baht,
    fetchReport,
    moneyOrUnknown,
    monthDays,
    pad2,
    parseYmd,
    ymd,
} from './sales-report-common.js';
import { renderHero } from './sales-report-hero.js';
import { renderMix } from './sales-report-mix.js';

// ── 全局状态:一个日期器管横幅 + 商品构成;走势卡自己按月翻页 ──
let gran: Granularity = 'day';
let gDate = ymd(new Date());
let gMonth = gDate.slice(0, 7);
let tMonth = gDate.slice(0, 7);
let mainData: Report | null = null;
let mainTo = ''; // 本次全局窗口的 to(热力网格锚 · 与后端 heat 窗口同源)
let trendRows: TrendRow[] = [];

// 图型偏好跨会话记住:店主每天看同一张图,别让他每天点一次。
const CHART_MODE_LS = 'pearnly_rep_chart_mode';
let chartMode: 'bar' | 'line' = 'bar';
try {
    if (localStorage.getItem(CHART_MODE_LS) === 'line') chartMode = 'line';
} catch (_) {
    /* 私模/配额:回落默认柱状 */
}

// 全局窗口 + 环比窗口(按日=上周同日 · 按月=上一自然月;当月截到今天,热力锚才不会落在未来)
function globalRange(): { from: string; to: string; prev_from: string; prev_to: string } {
    if (gran === 'day') {
        const prev = addDays(gDate, -7);
        return { from: gDate, to: gDate, prev_from: prev, prev_to: prev };
    }
    const today = ymd(new Date());
    const last = gMonth + '-' + pad2(monthDays(gMonth));
    const pm = addMonths(gMonth, -1);
    return {
        from: gMonth + '-01',
        to: gMonth === today.slice(0, 7) ? today : last,
        prev_from: pm + '-01',
        prev_to: pm + '-' + pad2(monthDays(pm)),
    };
}

function periodLabel(): string {
    return gran === 'day' ? gDate : gMonth;
}

// ── ② 营业额走势(按月一页)──
interface TrendRow {
    date: string;
    gross: number;
    profit: string | null;
    orders: number;
    has: boolean;
}

function buildTrendRows(byDay: DayRow[]): TrendRow[] {
    const byDate = new Map(byDay.map((d) => [d.date, d]));
    const rows: TrendRow[] = [];
    for (let day = 1; day <= monthDays(tMonth); day++) {
        const date = tMonth + '-' + pad2(day);
        const r = byDate.get(date);
        rows.push({
            date,
            gross: r ? Number(r.gross) || 0 : 0,
            profit: r ? r.gross_profit : null,
            orders: r ? r.sales_count : 0,
            has: !!r,
        });
    }
    return rows;
}

function trendTipHtml(row: TrendRow): string {
    return tipCardHtml(row.date, [
        [t('rep-kpi-gross'), baht(row.gross)],
        [t('rep-kpi-profit'), moneyOrUnknown(row.profit)],
        [t('rep-kpi-count'), String(row.orders)],
    ]);
}

function renderLivebar(row: TrendRow | null): void {
    const el = document.getElementById('rep-livebar');
    if (!el) return;
    if (!row) {
        el.innerHTML = '';
        return;
    }
    const avg = row.orders ? row.gross / row.orders : 0;
    const seg = (label: string, value: string) =>
        `<span>${escapeHtml(label)} <b class="tnum">${value}</b></span>`;
    el.innerHTML =
        `<span>${row.date}</span>` +
        seg(t('rep-kpi-gross'), baht(row.gross)) +
        seg(t('rep-kpi-profit'), moneyOrUnknown(row.profit)) +
        seg(t('rep-kpi-count'), String(row.orders)) +
        seg(t('rep-kpi-avg'), baht(avg));
}

function renderTrend(state: SectionState, errCode?: string): void {
    const el = document.getElementById('rep-trend-card');
    if (!el) return;
    const modeBtn = (m: 'bar' | 'line', label: string, icon: string) =>
        `<button data-chart-mode="${m}" class="${chartMode === m ? 'on' : ''}" title="${escapeHtml(label)}" aria-label="${escapeHtml(label)}">${icon}</button>`;
    let body = '';
    if (state === 'loading') {
        body = `<div class="ch-plot">${'<div class="ch-col"><div class="ch-bar skel" style="height:55%"></div></div>'.repeat(12)}</div>`;
    } else if (state === 'error') {
        body = errorHtml(errCode || 'pos.unexpected', 'rep-t-retry');
    } else {
        const buckets: XyBucket[] = trendRows.map((r) => ({
            label: pad2(parseYmd(r.date).getDate()),
            value: r.gross,
        }));
        body = trendRows.some((r) => r.has)
            ? (chartMode === 'line' ? lineChartHtml : barChartHtml)(buckets, axisFmt)
            : `<div class="rep-state">${escapeHtml(t('rep-empty'))}</div>`;
    }
    el.innerHTML = `<div class="hd">
        <div class="t">${escapeHtml(t('rep-trend-title'))}</div>
        <div class="livebar" id="rep-livebar"></div>
        <div class="hdctl">
            <div class="datebar">
                <button class="nav" id="rep-t-prev" aria-label="prev">${CHEV_L}</button>
                <input type="month" id="rep-t-month" value="${tMonth}">
                <button class="nav" id="rep-t-next" aria-label="next">${CHEV_R}</button>
            </div>
            <div class="ch-toggle" role="group">
                ${modeBtn('bar', t('rep-view-bar'), '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="3" y="12" width="4" height="9" rx="1"/><rect x="10" y="6" width="4" height="15" rx="1"/><rect x="17" y="9" width="4" height="12" rx="1"/></svg>')}
                ${modeBtn('line', t('rep-view-line'), '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M3 17l6-6 4 4 8-8"/></svg>')}
            </div>
        </div>
    </div>
    <div class="plotwrap" id="rep-t-plot">${body}</div>
    <div class="hint">${escapeHtml(t('rep-trend-hint'))}</div>`;
    bindTrendCtl();
    if (state === 'ready') {
        const withData = trendRows.filter((r) => r.has);
        renderLivebar(withData.length ? withData[withData.length - 1] : null);
        bindTrendPlot();
    }
}

function bindTrendCtl(): void {
    const stepT = (k: number) => {
        tMonth = addMonths(tMonth, k);
        loadTrend();
    };
    const prev = document.getElementById('rep-t-prev');
    const next = document.getElementById('rep-t-next');
    if (prev) prev.onclick = () => stepT(-1);
    if (next) next.onclick = () => stepT(1);
    const monthIn = document.getElementById('rep-t-month') as HTMLInputElement | null;
    if (monthIn)
        monthIn.onchange = () => {
            if (monthIn.value) tMonth = monthIn.value;
            loadTrend();
        };
    document.querySelectorAll<HTMLElement>('#rep-trend-card [data-chart-mode]').forEach((b) => {
        b.onclick = () => {
            chartMode = b.dataset.chartMode as 'bar' | 'line';
            try {
                localStorage.setItem(CHART_MODE_LS, chartMode);
            } catch (_) {
                /* 私模/配额:本次会话内仍生效 */
            }
            renderTrend('ready');
        };
    });
}

function bindTrendPlot(): void {
    const plot = document.getElementById('rep-t-plot');
    if (!plot) return;
    const dots = plot.querySelectorAll<SVGElement>('.ch-dot');
    const todayIso = ymd(new Date());
    plot.querySelectorAll<HTMLElement>('.ch-col').forEach((col) => {
        const i = Number(col.dataset.tipI);
        const row = trendRows[i];
        if (!row) return;
        if (row.date === todayIso) col.classList.add('today');
        const show = (ev: PointerEvent) => {
            renderLivebar(row);
            tipShow(ev, trendTipHtml(row));
            dots.forEach((d) =>
                d.classList.toggle('on', d.getAttribute('data-dot-i') === String(i))
            );
        };
        col.onpointerenter = show;
        col.onpointermove = show;
        col.onpointerleave = () => {
            tipHide();
            dots.forEach((d) => d.classList.remove('on'));
        };
        // 联动:点一天 → 全局切到那天(横幅 + 商品构成)并滚回顶部
        col.onclick = () => {
            gran = 'day';
            gDate = row.date;
            loadMain();
            document
                .getElementById('page-sales-report')
                ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        };
    });
}

// ── ④ 分时热力(近 14 天 × 8:00–22:00)──
// 五档色阶:--hm-* 定义收敛在 home-43(取值 = 现成蓝紫阶令牌 200/400/600/800,亮暗各自成梯)
function heatShadeVar(v: number, mx: number): string {
    const k = v / mx;
    if (k < 0.08) return '--line2';
    if (k < 0.3) return '--hm-1';
    if (k < 0.55) return '--hm-2';
    if (k < 0.8) return '--hm-3';
    return '--hm-4';
}

function renderHeat(state: SectionState, errCode?: string): void {
    const el = document.getElementById('rep-heat-card');
    if (!el) return;
    // 后端随 heat 回显实际锚窗(曼谷日),标题标注期间,不自己推算
    const hr = mainData?.heat_range;
    let body: string;
    if (state === 'loading') {
        body = `<div class="heatwrap">${'<div class="rep-skel line"></div>'.repeat(6)}</div>`;
    } else if (state === 'error') {
        body = errorHtml(errCode || 'pos.unexpected', 'rep-h-retry');
    } else {
        const cells = new Map(
            (mainData?.heat || []).map((c) => [c.date + '#' + c.hour, Number(c.gross) || 0])
        );
        const days: string[] = [];
        for (let i = HEAT_DAYS - 1; i >= 0; i--) days.push(addDays(mainTo, -i));
        let mx = 0;
        for (const d of days)
            for (let h = HOUR_LO; h <= HOUR_HI; h++) mx = Math.max(mx, cells.get(d + '#' + h) || 0);
        mx = mx || 1;
        const rows = days
            .map((d) => {
                const cols = [];
                for (let h = HOUR_LO; h <= HOUR_HI; h++) {
                    const v = cells.get(d + '#' + h) || 0;
                    cols.push(
                        `<i class="cell" data-d="${d}" data-h="${h}" data-v="${v}" style="background:var(${heatShadeVar(v, mx)})"></i>`
                    );
                }
                return `<div class="hrow"><span class="d">${d.slice(5).replace('-', '/')}</span>${cols.join('')}</div>`;
            })
            .join('');
        const xlabels = Array.from(
            { length: HOUR_HI - HOUR_LO + 1 },
            (_, j) => `<span>${HOUR_LO + j}</span>`
        ).join('');
        body = `<div class="heatwrap" id="rep-heat">${rows}<div class="hx"><span class="d"></span>${xlabels}</div></div>
            <div class="heatlegend">${escapeHtml(t('rep-heat-less'))}
                <i style="background:var(--line2)"></i><i style="background:var(--hm-1)"></i><i style="background:var(--hm-2)"></i><i style="background:var(--hm-3)"></i><i style="background:var(--hm-4)"></i>
            ${escapeHtml(t('rep-heat-more'))}</div>`;
    }
    el.innerHTML = `<div class="hd"><div class="t">${escapeHtml(t('rep-heat-title'))}${
        hr ? `<span class="sub">${escapeHtml(hr.from)} – ${escapeHtml(hr.to)}</span>` : ''
    }</div></div>${body}`;
    el.querySelectorAll<HTMLElement>('.cell').forEach((c) => {
        const show = (ev: PointerEvent) =>
            tipShow(
                ev,
                tipCardHtml(`${c.dataset.d} · ${c.dataset.h}:00`, [
                    [t('rep-kpi-gross'), baht(Number(c.dataset.v))],
                ])
            );
        c.onpointerenter = show;
        c.onpointermove = show;
        c.onpointerleave = tipHide;
    });
}

// ── 四态 · 装配 ──
function errorHtml(code: string, retryCls: string): string {
    return `<div class="rep-state error">${escapeHtml(posErrMsg(code, 'rep-error'))}<br><button class="rep-retry ${retryCls}">${escapeHtml(t('rep-retry'))}</button></div>`;
}

function paintMain(state: SectionState, errCode?: string): void {
    renderHero({ gran, gDate, gMonth, state, errCode, data: mainData, onChange: applyGlobal });
    renderMix({
        periodLabel: periodLabel(),
        state,
        errCode,
        data: mainData,
        errorHtml: (code) => errorHtml(code, 'rep-m-retry'),
    });
    renderHeat(state, errCode);
}

function applyGlobal(next: { gran?: Granularity; gDate?: string; gMonth?: string }): void {
    if (next.gran) gran = next.gran;
    if (next.gDate) gDate = next.gDate;
    if (next.gMonth) gMonth = next.gMonth;
    loadMain();
}

async function loadMain(): Promise<void> {
    mainData = null;
    paintMain('loading');
    const range = globalRange();
    mainTo = range.to;
    try {
        mainData = await fetchReport(range);
        // 信封 ok 但形状不对(缺 kpi)→ 当空数据诚实渲染,不让渲染层崩在 kpi.xx 上
        if (!mainData || !mainData.kpi) mainData = null;
    } catch (e) {
        const code = e instanceof Error ? e.message : 'pos.unexpected';
        paintMain('error', code);
        document.querySelectorAll<HTMLElement>('.rep-m-retry, .rep-h-retry').forEach((b) => {
            b.onclick = () => loadMain();
        });
        return;
    }
    paintMain('ready');
}

async function loadTrend(): Promise<void> {
    renderTrend('loading');
    try {
        // 走势翻页只画按月 by_day 一条曲线:轻参数只取该分区,省掉白拉的 4 句 SQL。
        const data = await fetchReport({
            from: tMonth + '-01',
            to: tMonth + '-' + pad2(monthDays(tMonth)),
            sections: 'by_day',
        });
        trendRows = buildTrendRows(data.by_day || []);
    } catch (e) {
        const code = e instanceof Error ? e.message : 'pos.unexpected';
        renderTrend('error', code);
        document.querySelectorAll<HTMLElement>('.rep-t-retry').forEach((b) => {
            b.onclick = () => loadTrend();
        });
        return;
    }
    renderTrend('ready');
}

function needWorkspaceHtml(): string {
    return `<div class="card"><div class="rep-state">${escapeHtml(t('rep-need-workspace'))}
        <br><button class="rep-retry" id="rep-pick-ws">${escapeHtml(t('rep-pick-workspace'))}</button></div></div>`;
}

window.loadSalesReport = function () {
    const sec = document.getElementById('page-sales-report');
    if (!sec) return;
    // 不挂设计 kit 的 .ui 命名空间:kit 里 .ui .seg(2px 进度条)/.ui .dot 会压过本页同名件,
    // 本页样式全部自包含在 .posrep 作用域里
    sec.classList.remove('ui');
    if (activeWsId() == null) {
        sec.innerHTML = `<div class="posrep">${needWorkspaceHtml()}</div>`;
        const pick = document.getElementById('rep-pick-ws');
        if (pick)
            pick.onclick = () =>
                window.requireWorkspace
                    ? window.requireWorkspace(() => window.loadSalesReport!())
                    : window.openWorkspaceChooserUI?.();
        return;
    }
    sec.innerHTML = `<div class="posrep" role="region" aria-label="${escapeHtml(t('rep-title'))}">
        <div class="hero" id="rep-hero"></div>
        <div class="card" id="rep-trend-card"></div>
        <div class="card" id="rep-mix-card"></div>
        <div class="card" id="rep-heat-card"></div>
    </div>`;
    loadMain();
    loadTrend();
};

if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('sales-report', () => {
        if (document.getElementById('page-sales-report')?.querySelector('.posrep'))
            window.loadSalesReport?.();
    });
}
