// 销售仪表盘 · ③ 商品销售构成卡:环图(top5+其他)+ 图例 + 当期数据(环比徽章)+ 收款构成。
// 支付构成按后端 by_method 全量画(cash/promptpay/card/transfer+未知键兜底)——写死三种曾把
// 「银行转账」整笔吞掉(2026-08-04 真机对出 935−835=100 正是那笔转账),这条账务修复不许回退。
/* global t, escapeHtml */
import { fmtQty, localizedName } from './inventory-common.js';
import { donutHtml, tipHide, tipShow, type DonutSlice } from './sales-report-charts.js';
import {
    type Kpi,
    type Report,
    type SectionState,
    baht,
    moneyOrUnknown,
} from './sales-report-common.js';

export interface MixCtx {
    periodLabel: string; // 全局日期器当前值(YYYY-MM-DD / YYYY-MM)
    state: SectionState;
    errCode?: string;
    data: Report | null;
    errorHtml(code: string): string; // 错误态由主模块统一出(重试按钮的绑定也在那边)
}

const PM_META: Record<string, { colorVar: string; key: string }> = {
    cash: { colorVar: '--ch-1', key: 'rep-pm-cash' },
    promptpay: { colorVar: '--ch-2', key: 'rep-pm-promptpay' },
    card: { colorVar: '--ch-3', key: 'rep-pm-card' },
    transfer: { colorVar: '--ch-4', key: 'rep-pm-transfer' },
};

function paySlices(byMethod: Record<string, string>): DonutSlice[] {
    const order = Object.keys(PM_META).filter((m) => byMethod[m] != null);
    for (const m of Object.keys(byMethod)) if (!PM_META[m]) order.push(m);
    return order
        .map((m) => ({
            key: m,
            label: PM_META[m] ? t(PM_META[m].key) : m,
            value: Number(byMethod[m]) || 0,
            colorVar: PM_META[m] ? PM_META[m].colorVar : '--ink3',
        }))
        .filter((s) => s.value !== 0);
}

interface MixSlice extends DonutSlice {
    qty: string | null; // 「其他」是差额算出来的,没有件数可言 → null 不冒充 0
}

function mixSlices(data: Report): MixSlice[] {
    const top = (data.top_products || []).slice(0, 5);
    const slices: MixSlice[] = top
        .filter((p) => Number(p.gross) > 0)
        .map((p, i) => ({
            key: p.product_id,
            label: localizedName(p.name),
            value: Number(p.gross),
            colorVar: `--chp-${i + 1}`,
            qty: p.qty,
        }));
    const other = (Number(data.kpi.gross) || 0) - slices.reduce((s, x) => s + x.value, 0);
    if (other > 0.005)
        slices.push({
            key: '__other',
            label: t('rep-mix-other'),
            value: other,
            colorVar: '--chp-x',
            qty: null,
        });
    return slices;
}

function tipHtml(s: MixSlice, total: number): string {
    const qtyRow =
        s.qty != null
            ? `<span>${escapeHtml(t('rep-tip-qty'))} <em class="tnum">${escapeHtml(fmtQty(s.qty))}</em></span>`
            : '';
    return `<b>${escapeHtml(s.label)}</b>${qtyRow}
        <span>${escapeHtml(t('rep-tip-amount'))} <em class="tnum">${baht(s.value)}</em></span>
        <span>${escapeHtml(t('rep-tip-share'))} <em class="tnum">${total ? Math.round((s.value / total) * 100) : 0}%</em></span>`;
}

// 环比徽章:上期为 0 没有比率可言 → 「—」+ 悬浮说明,绝不显示 ∞%。invert=涨了是坏事(退货)。
function deltaChip(cur: number, prev: number | null, invert = false): string {
    if (prev == null) return '';
    if (prev === 0)
        return `<span class="kdelta none" title="${escapeHtml(t('rep-prev-none'))}">—</span>`;
    const pct = ((cur - prev) / prev) * 100;
    if (Math.abs(pct) < 0.05) return '<span class="kdelta none">0%</span>';
    const up = pct > 0;
    const good = invert ? !up : up;
    return `<span class="kdelta ${good ? 'good' : 'bad'}">${up ? '↑' : '↓'}${Math.abs(pct).toFixed(1)}%</span>`;
}

// 右列当期数据 + 收款构成细条(照定稿原型;环比沿用 KPI 口径,退货反向)
function statsHtml(data: Report): string {
    const k = data.kpi;
    const prev: Kpi | null = data.prev_kpi;
    const n = (v: string | number | null | undefined) => (v == null ? null : Number(v));
    const row = (label: string, value: string, delta: string, unknown?: boolean, title?: string) =>
        `<div class="s"><span class="l">${escapeHtml(label)}</span><span class="v tnum${unknown ? ' unknown' : ''}"${
            title ? ` title="${escapeHtml(title)}"` : ''
        }>${value}${delta}</span></div>`;
    const profitUnknown = k.gross_profit == null;
    const profitPrev = prev && prev.gross_profit != null ? Number(prev.gross_profit) : null;
    const pm = paySlices(data.by_method || {});
    const pmTotal = pm.reduce((s, x) => s + x.value, 0);
    const payBar = pmTotal
        ? `<div class="paybar">${pm
              .map(
                  (s) =>
                      `<i style="background:var(${s.colorVar});width:${((s.value / pmTotal) * 100).toFixed(2)}%"></i>`
              )
              .join('')}</div>
           <div class="paychips">${pm
               .map(
                   (s) =>
                       `<span><span class="dot" style="background:var(${s.colorVar})"></span>${escapeHtml(s.label)} <b class="tnum">${baht(s.value)}</b></span>`
               )
               .join('')}</div>`
        : `<div class="rep-state sm">${escapeHtml(t('rep-empty'))}</div>`;
    return (
        row(t('rep-kpi-gross'), baht(k.gross), deltaChip(Number(k.gross), n(prev && prev.gross))) +
        row(
            t('rep-kpi-count'),
            String(k.sales_count),
            deltaChip(k.sales_count, prev ? prev.sales_count : null)
        ) +
        row(
            t('rep-kpi-avg'),
            baht(k.avg_ticket),
            deltaChip(Number(k.avg_ticket), n(prev && prev.avg_ticket))
        ) +
        row(
            t('rep-kpi-profit'),
            moneyOrUnknown(k.gross_profit),
            profitUnknown ? '' : deltaChip(Number(k.gross_profit), profitPrev),
            profitUnknown,
            profitUnknown ? t('rep-profit-unknown') : undefined
        ) +
        row(
            t('rep-kpi-refund'),
            baht(k.refund),
            deltaChip(Number(k.refund), n(prev && prev.refund), true)
        ) +
        `<div class="paymix"><div class="pt">${escapeHtml(t('rep-pm-title'))}</div>${payBar}</div>`
    );
}

export function renderMix(ctx: MixCtx): void {
    const el = document.getElementById('rep-mix-card');
    if (!el) return;
    let body: string;
    if (ctx.state === 'loading') {
        body = `<div class="topgrid"><div class="rep-skel round"></div><div>${'<div class="rep-skel line"></div>'.repeat(5)}</div><div>${'<div class="rep-skel line"></div>'.repeat(6)}</div></div>`;
    } else if (ctx.state === 'error') {
        body = ctx.errorHtml(ctx.errCode || 'pos.unexpected');
    } else if (!ctx.data || (ctx.data.kpi.sales_count === 0 && Number(ctx.data.kpi.gross) === 0)) {
        body = `<div class="rep-state">${escapeHtml(t('rep-empty'))}</div>`;
    } else {
        const slices = mixSlices(ctx.data);
        const total = slices.reduce((s, x) => s + x.value, 0);
        const legend = slices
            .map(
                (s) =>
                    `<div class="r"><span class="dot" style="background:var(${s.colorVar})"></span><span class="nm">${escapeHtml(
                        s.label
                    )}${s.qty != null ? ` <span class="q">· ${escapeHtml(t('rep-mix-qty').replace('{n}', fmtQty(s.qty)))}</span>` : ''}</span><span class="pc tnum">${
                        total ? Math.round((s.value / total) * 100) : 0
                    }%</span><span class="v tnum">${baht(s.value)}</span></div>`
            )
            .join('');
        body = `<div class="topgrid">
            <div id="rep-pie">${donutHtml(slices, t('rep-kpi-gross'), baht(ctx.data.kpi.gross))}</div>
            <div class="plegend">${legend}</div>
            <div class="stats">${statsHtml(ctx.data)}</div>
        </div>`;
    }
    el.innerHTML = `<div class="hd"><div class="t">${escapeHtml(t('rep-mix-title'))} · <span class="tnum">${ctx.periodLabel}</span></div></div>${body}`;
    if (ctx.state === 'ready' && ctx.data) {
        const slices = mixSlices(ctx.data);
        const total = slices.reduce((s, x) => s + x.value, 0);
        el.querySelectorAll<HTMLElement>('.dn-seg').forEach((seg) => {
            const s = slices[Number(seg.dataset.tipI)];
            if (!s) return;
            const show = (ev: PointerEvent) => tipShow(ev, tipHtml(s, total));
            seg.onpointerenter = show;
            seg.onpointermove = show;
            seg.onpointerleave = tipHide;
        });
    }
}
