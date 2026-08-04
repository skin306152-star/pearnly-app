// 销售仪表盘 · ① Hero 大横幅:大数字 count-up + 环比副行 + 中缝脉搏 + 右侧三徽章 +
// 内嵌全局日期器(按日/按月 seg + 前后翻页 + date/month input)。
// 日期器改动通过 ctx.onChange 回给主模块(状态与取数都在主模块,这里只管画和收事件)。
/* global t, escapeHtml */
import { posErrMsg } from './inventory-common.js';
import {
    CHEV_L,
    CHEV_R,
    type Granularity,
    type Kpi,
    type Live,
    type Report,
    type SectionState,
    addDays,
    addMonths,
    baht,
    moneyOrUnknown,
    pad2,
    parseYmd,
    ymd,
} from './sales-report-common.js';

export interface HeroCtx {
    gran: Granularity;
    gDate: string;
    gMonth: string;
    state: SectionState;
    errCode?: string;
    data: Report | null;
    onChange(next: { gran?: Granularity; gDate?: string; gMonth?: string }): void;
}

const HOUR_LO = 8;
const HOUR_HI = 22;

function ctlHtml(ctx: HeroCtx): string {
    const segBtn = (g: Granularity, label: string) =>
        `<button data-gran="${g}" class="${ctx.gran === g ? 'on' : ''}">${escapeHtml(label)}</button>`;
    return `<div class="ctl">
        <div class="seg" id="rep-gran">${segBtn('day', t('rep-gran-day'))}${segBtn('month', t('rep-gran-month'))}</div>
        <div class="datebar">
            <button class="nav" id="rep-g-prev" aria-label="prev">${CHEV_L}</button>
            <input type="date" id="rep-g-date" value="${ctx.gDate}"${ctx.gran === 'day' ? '' : ' style="display:none"'}>
            <input type="month" id="rep-g-month" value="${ctx.gMonth}"${ctx.gran === 'month' ? '' : ' style="display:none"'}>
            <button class="nav" id="rep-g-next" aria-label="next">${CHEV_R}</button>
        </div>
    </div>`;
}

function cmpHtml(ctx: HeroCtx, k: Kpi, prev: Kpi | null): string {
    const base =
        ctx.gran === 'day'
            ? t('rep-vs-day').replace('{wd}', t('rep-wd-' + parseYmd(ctx.gDate).getDay()))
            : t('rep-vs-month');
    const pg = prev ? Number(prev.gross) : 0;
    const pct = prev && pg > 0 ? ((Number(k.gross) - pg) / pg) * 100 : null;
    const pctHtml =
        pct == null
            ? `<b title="${escapeHtml(t('rep-prev-none'))}">—</b>`
            : `<b class="${pct >= 0 ? 'up' : 'down'}">${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%</b>`;
    return `${escapeHtml(base)} ${pctHtml} · ${escapeHtml(t('rep-kpi-profit'))} <b>${moneyOrUnknown(
        k.gross_profit
    )}</b> · ${escapeHtml(t('rep-kpi-count'))} <b class="tnum">${k.sales_count}</b>`;
}

// 中缝脉搏:按日=当天分时节奏(几点卖得多,与下方按月走势不重复);按月=当月逐日节奏。
function sparkHtml(ctx: HeroCtx, data: Report): string {
    let vals: number[];
    let cap: string;
    if (ctx.gran === 'day') {
        const byH = new Map((data.by_hour || []).map((h) => [h.hour, Number(h.gross)]));
        vals = [];
        for (let h = HOUR_LO; h <= HOUR_HI; h++) vals.push(byH.get(h) || 0);
        cap = t('rep-spark-day');
        if (!vals.some((v) => v > 0)) return '';
    } else {
        vals = (data.by_day || []).map((d) => Number(d.gross) || 0);
        cap = t('rep-spark-month');
        if (vals.length < 2) return '';
    }
    const W = 240;
    const H = 64;
    const mx = Math.max(...vals) || 1;
    const pts = vals.map(
        (v, i) =>
            `${((i / (vals.length - 1)) * W).toFixed(1)},${(H - 2 - (v / mx) * (H - 6)).toFixed(1)}`
    );
    const lastY = pts[pts.length - 1].split(',')[1];
    return `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" aria-hidden="true">
        <polygon class="spark-area" points="0,${H} ${pts.join(' ')} ${W},${H}"></polygon>
        <polyline class="spark-line" points="${pts.join(' ')}"></polyline>
        <circle class="spark-dot" cx="${W}" cy="${lastY}" r="3"></circle></svg>
        <span class="cap2">${escapeHtml(cap)}</span>`;
}

function lastSaleText(iso: string): string {
    const d = new Date(iso);
    const mins = Math.max(0, Math.round((Date.now() - d.getTime()) / 60000));
    const hhmm = pad2(d.getHours()) + ':' + pad2(d.getMinutes());
    if (mins < 60) return hhmm + ' · ' + t('rep-min-ago').replace('{n}', String(mins));
    if (mins < 1440)
        return hhmm + ' · ' + t('rep-hour-ago').replace('{n}', String(Math.round(mins / 60)));
    return ymd(d) + ' ' + hhmm;
}

function badgesHtml(k: Kpi, live: Live): string {
    const badge = (label: string, value: string) =>
        `<div class="badge"><span>${escapeHtml(label)}</span><b class="tnum">${value}</b></div>`;
    const shift = live.open_shift
        ? `${escapeHtml(live.open_shift.cashier_name || '—')} · ${escapeHtml(
              t('rep-live-shift').replace('{n}', String(live.open_shift.shift_seq ?? '—'))
          )}`
        : escapeHtml(t('rep-live-none'));
    return (
        badge(
            t('rep-live-last'),
            live.last_sale_at ? escapeHtml(lastSaleText(live.last_sale_at)) : '—'
        ) +
        badge(t('rep-live-cashier'), shift) +
        badge(t('rep-kpi-avg'), baht(k.avg_ticket))
    );
}

// 载入数字滚上去(650ms 缓出):大数字是这页的主角,给它一个入场。
function countUp(el: HTMLElement, target: number): void {
    const t0 = performance.now();
    const step = (now: number) => {
        const k = Math.min(1, (now - t0) / 650);
        el.textContent = baht(target * (1 - Math.pow(1 - k, 3)));
        if (k < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
}

function bindCtl(ctx: HeroCtx): void {
    document.querySelectorAll<HTMLElement>('#rep-gran button').forEach((b) => {
        b.onclick = () => ctx.onChange({ gran: b.dataset.gran as Granularity });
    });
    const dateIn = document.getElementById('rep-g-date') as HTMLInputElement | null;
    const monthIn = document.getElementById('rep-g-month') as HTMLInputElement | null;
    if (dateIn) dateIn.onchange = () => ctx.onChange(dateIn.value ? { gDate: dateIn.value } : {});
    if (monthIn)
        monthIn.onchange = () => ctx.onChange(monthIn.value ? { gMonth: monthIn.value } : {});
    const step = (k: number) =>
        ctx.gran === 'day'
            ? ctx.onChange({ gDate: addDays(ctx.gDate, k) })
            : ctx.onChange({ gMonth: addMonths(ctx.gMonth, k) });
    const prev = document.getElementById('rep-g-prev');
    const next = document.getElementById('rep-g-next');
    if (prev) prev.onclick = () => step(-1);
    if (next) next.onclick = () => step(1);
}

export function renderHero(ctx: HeroCtx): void {
    const el = document.getElementById('rep-hero');
    if (!el) return;
    const isToday = ctx.gran === 'day' && ctx.gDate === ymd(new Date());
    const cap =
        ctx.gran === 'month'
            ? t('rep-hero-month')
            : isToday
              ? t('rep-hero-today')
              : t('rep-hero-day');
    let big = '—';
    let cmp = '';
    let spark = '';
    let badges = '';
    if (ctx.state === 'loading') {
        cmp = '<span class="rep-skel line"></span>';
    } else if (ctx.state === 'error') {
        cmp = escapeHtml(posErrMsg(ctx.errCode || 'pos.unexpected', 'rep-error'));
    } else if (ctx.data) {
        big = baht(0);
        cmp = cmpHtml(ctx, ctx.data.kpi, ctx.data.prev_kpi);
        spark = sparkHtml(ctx, ctx.data);
        badges = badgesHtml(ctx.data.kpi, ctx.data.live);
    }
    el.innerHTML = `<div class="in">
        <div class="l">
            <div class="cap"><span>${escapeHtml(cap)}</span><span class="capdate tnum">${ctx.gran === 'day' ? ctx.gDate : ctx.gMonth}</span></div>
            <div class="big tnum" id="rep-big">${ctx.state === 'loading' ? '<span class="rep-skel big"></span>' : big}</div>
            <div class="cmp" id="rep-cmp">${cmp}</div>
            ${ctlHtml(ctx)}
        </div>
        <div class="mid">${spark}</div>
        <div class="r">${badges}</div>
    </div>`;
    bindCtl(ctx);
    if (ctx.state === 'ready' && ctx.data) {
        const bigEl = document.getElementById('rep-big');
        if (bigEl) countUp(bigEl, Number(ctx.data.kpi.gross) || 0);
    }
}
