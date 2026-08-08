// 事务所端 · 商品收发存报表 · 纯渲染层(HTML 字符串拼装 · 无状态 · 不碰 DOM)
// 三段式表头配色(入=绿/出=粉/结存=紫)+ 负库存整行标红照实显示 · 视觉规格见桌面原型
// stock-card-prototype-v1.html(拍板稿),令牌换成本仓 static/pearnly-ui.css + home-01-base.css。
/* global t, escapeHtml */
import {
    fmtAmt,
    fmtQty,
    type StcCardResp,
    type StcCardRow,
    type StcExcludedReason,
    type StcExcludedRow,
    type StcProduct,
} from './stock-card-api.js';

const IC_BOX =
    '<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M21 16V8a2 2 0 0 0-1-1.7l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.7l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><path d="M3.3 7 12 12l8.7-5M12 22V12"/></svg>';

const STC_REASON_KEY: Record<StcExcludedReason, string> = {
    service: 'stc-reason-service',
    no_qty_price: 'stc-reason-no-qty-price',
    total_only: 'stc-reason-total-only',
};

export function stcChip(cls: string, label: string): string {
    return `<span class="stc-chip stc-chip-${cls}">${escapeHtml(label)}</span>`;
}

function statusChips(p: StcProduct): string {
    const chips: string[] = [];
    if (p.negative) chips.push(stcChip('neg', t('stc-st-neg')));
    if (!p.matched)
        chips.push(
            stcChip('um', t('stc-st-unmatched')) +
                ` <button type="button" class="stc-link" data-stc-merge="${escapeHtml(p.key)}">${escapeHtml(t('stc-act-merge'))}</button>`
        );
    if (!chips.length) chips.push(stcChip('ok', t('stc-st-ok')));
    return chips.join(' ');
}

export function stcListHead(): string {
    return `<thead>
        <tr class="stc-grp">
            <th rowspan="2">${escapeHtml(t('stc-col-product'))}</th>
            <th rowspan="2">${escapeHtml(t('stc-col-unit'))}</th>
            <th rowspan="2" class="num">${escapeHtml(t('stc-col-opening'))}</th>
            <th class="stc-g-in num">${escapeHtml(t('stc-col-in'))}</th>
            <th class="stc-g-out num">${escapeHtml(t('stc-col-out'))}</th>
            <th class="stc-g-bal" colspan="3">${escapeHtml(t('stc-col-bal'))}</th>
            <th rowspan="2">${escapeHtml(t('stc-col-status'))}</th>
        </tr>
        <tr>
            <th class="stc-g-in num">${escapeHtml(t('stc-col-qty'))}</th>
            <th class="stc-g-out num">${escapeHtml(t('stc-col-qty'))}</th>
            <th class="stc-g-bal num">${escapeHtml(t('stc-col-qty'))}</th>
            <th class="stc-g-bal num">${escapeHtml(t('stc-col-price'))}</th>
            <th class="stc-g-bal num">${escapeHtml(t('stc-col-amt'))}</th>
        </tr>
    </thead>`;
}

export function stcListRow(p: StcProduct): string {
    const neg = p.negative;
    return `<tr class="stc-row${neg ? ' neg' : ''}" data-stc-key="${escapeHtml(p.key)}">
        <td>${escapeHtml(p.name)}</td>
        <td class="c">${escapeHtml(p.unit)}</td>
        <td class="num">${p.opening_qty == null ? '—' : fmtQty(p.opening_qty)}</td>
        <td class="num stc-c-in">${fmtQty(p.in_qty)}</td>
        <td class="num stc-c-out">${fmtQty(p.out_qty)}</td>
        <td class="num stc-c-bal">${fmtQty(p.bal_qty)}</td>
        <td class="num stc-c-bal">${fmtAmt(p.bal_unit_cost)}</td>
        <td class="num stc-c-bal">${fmtAmt(p.bal_value)}</td>
        <td class="c">${statusChips(p)}</td>
    </tr>`;
}

// cols 按目标表头实际列数传:骨架行只是过渡态,但列数对不上表头会在加载那一瞬把表格撑变形。
export function stcSkeletonBody(cols: number): string {
    const cell = '<td><div class="stc-skel"></div></td>';
    return `<tbody>${`<tr>${cell.repeat(cols)}</tr>`.repeat(5)}</tbody>`;
}

export function stcEmptyRow(msg: string): string {
    return `<tbody><tr><td colspan="9"><div class="stc-state">${IC_BOX}<div>${escapeHtml(msg)}</div></div></td></tr></tbody>`;
}

// ── 单品收发存流水(单品卡)──────────────────────────────────────────
const MOVE_CHIP_CLS: Record<StcCardRow['kind'], string> = { open: 'open', in: 'in', out: 'out' };
const MOVE_CHIP_KEY: Record<StcCardRow['kind'], string> = {
    open: 'stc-type-open',
    in: 'stc-type-in',
    out: 'stc-type-out',
};

export function stcDetailHead(): string {
    return `<thead>
        <tr class="stc-grp">
            <th rowspan="2">${escapeHtml(t('stc-col-date'))}</th>
            <th rowspan="2">${escapeHtml(t('stc-col-doc'))}</th>
            <th rowspan="2">${escapeHtml(t('stc-col-type'))}</th>
            <th rowspan="2">${escapeHtml(t('stc-col-desc'))}</th>
            <th class="stc-g-in" colspan="3">${escapeHtml(t('stc-col-in'))}</th>
            <th class="stc-g-out" colspan="3">${escapeHtml(t('stc-col-out'))}</th>
            <th class="stc-g-bal" colspan="3">${escapeHtml(t('stc-col-bal'))}</th>
        </tr>
        <tr>
            <th class="stc-g-in num">${escapeHtml(t('stc-col-qty'))}</th>
            <th class="stc-g-in num">${escapeHtml(t('stc-col-price'))}</th>
            <th class="stc-g-in num">${escapeHtml(t('stc-col-amt'))}</th>
            <th class="stc-g-out num">${escapeHtml(t('stc-col-qty'))}</th>
            <th class="stc-g-out num">${escapeHtml(t('stc-col-price'))}</th>
            <th class="stc-g-out num">${escapeHtml(t('stc-col-amt'))}</th>
            <th class="stc-g-bal num">${escapeHtml(t('stc-col-qty'))}</th>
            <th class="stc-g-bal num">${escapeHtml(t('stc-col-price'))}</th>
            <th class="stc-g-bal num">${escapeHtml(t('stc-col-amt'))}</th>
        </tr>
    </thead>`;
}

export function stcDetailRow(r: StcCardRow): string {
    const neg = Number(r.bal_qty) < 0;
    const isIn = r.kind === 'in';
    const isOut = r.kind === 'out';
    const chip = stcChip(MOVE_CHIP_CLS[r.kind], t(MOVE_CHIP_KEY[r.kind]));
    return `<tr${neg ? ' class="neg"' : ''}>
        <td class="c">${escapeHtml(r.date)}</td>
        <td class="c">${escapeHtml(r.doc_no || '—')}</td>
        <td class="c">${chip}</td>
        <td>${escapeHtml(r.desc || '—')}</td>
        <td class="num stc-c-in">${isIn ? fmtQty(r.qty) : '—'}</td>
        <td class="num stc-c-in">${isIn ? fmtAmt(r.unit_price) : '—'}</td>
        <td class="num stc-c-in">${isIn ? fmtAmt(r.amount) : '—'}</td>
        <td class="num stc-c-out">${isOut ? fmtQty(r.qty) : '—'}</td>
        <td class="num stc-c-out">${isOut ? fmtAmt(r.unit_price) : '—'}</td>
        <td class="num stc-c-out">${isOut ? fmtAmt(r.amount) : '—'}</td>
        <td class="num stc-c-bal">${fmtQty(r.bal_qty)}</td>
        <td class="num stc-c-bal">${fmtAmt(r.bal_unit_cost)}</td>
        <td class="num stc-c-bal">${fmtAmt(r.bal_value)}</td>
    </tr>`;
}

// 后端 totals 缺的字段从 rows 现算兜底(口径与后端一致:按 kind 分组求和;结存取最后一行,
// 无行则回落 0/null)——不让页面因为 totals 形状不齐就崩或印错数。
// amt 只要这组里有一行金额未知就整组置 null(不拿 0 顶替未知再求和):否则「有几行没成本」
// 混几行有成本一起加,和会悄悄把「不知道」印成一个看着精确的数字,踩任务口径明文禁的
// 「不四舍五入造假」——空值必须一路传导到合计,不能在中途被 Number(null)||0 焊死成 0。
function sumKind(
    rows: StcCardRow[],
    kind: StcCardRow['kind']
): { qty: number; amt: number | null } {
    let qty = 0;
    let amt = 0;
    let amtKnown = true;
    for (const r of rows) {
        if (r.kind !== kind) continue;
        qty += Number(r.qty) || 0;
        if (r.amount == null) amtKnown = false;
        else amt += Number(r.amount) || 0;
    }
    return { qty, amt: amtKnown ? amt : null };
}

export function stcDetailFoot(card: StcCardResp): string {
    const { rows, totals } = card;
    const last = rows.length ? rows[rows.length - 1] : null;
    const inS = sumKind(rows, 'in');
    const outS = sumKind(rows, 'out');
    const balQty = totals.bal_qty ?? last?.bal_qty ?? '0';
    const balUnit =
        totals.bal_unit_cost !== undefined ? totals.bal_unit_cost : (last?.bal_unit_cost ?? null);
    const balVal = totals.bal_value !== undefined ? totals.bal_value : (last?.bal_value ?? null);
    const neg = Number(balQty) < 0;
    return `<tfoot>
        <tr>
            <td colspan="4">${escapeHtml(t('stc-total'))}</td>
            <td class="num stc-t-in">${fmtQty(totals.in_qty ?? inS.qty)}</td><td class="stc-t-in"></td>
            <td class="num stc-t-in">${fmtAmt(totals.in_amount ?? inS.amt)}</td>
            <td class="num stc-t-out">${fmtQty(totals.out_qty ?? outS.qty)}</td><td class="stc-t-out"></td>
            <td class="num stc-t-out">${fmtAmt(totals.out_amount ?? outS.amt)}</td>
            <td class="num${neg ? ' stc-neg-txt' : ''}">${fmtQty(balQty)}</td>
            <td class="num">${fmtAmt(balUnit)}</td>
            <td class="num${neg ? ' stc-neg-txt' : ''}">${fmtAmt(balVal)}</td>
        </tr>
    </tfoot>`;
}

// ── 未入账清单 ──────────────────────────────────────────────────────
export function stcExcludedHead(): string {
    return `<thead><tr>
        <th>${escapeHtml(t('stc-col-date'))}</th>
        <th>${escapeHtml(t('stc-col-doc'))}</th>
        <th>${escapeHtml(t('stc-col-desc'))}</th>
        <th class="num">${escapeHtml(t('stc-col-amt'))}</th>
        <th>${escapeHtml(t('stc-col-reason'))}</th>
    </tr></thead>`;
}

export function stcExcludedRow(x: StcExcludedRow): string {
    return `<tr>
        <td class="c">${escapeHtml(x.date)}</td>
        <td class="c">${escapeHtml(x.doc_no || '—')}</td>
        <td>${escapeHtml(x.desc || '—')}</td>
        <td class="num">${fmtAmt(x.amount)}</td>
        <td class="c">${stcChip('um', t(STC_REASON_KEY[x.reason] || 'stc-reason-no-qty-price'))}</td>
    </tr>`;
}

// ── 四态公共壳 ──────────────────────────────────────────────────────
export function stcNeedWorkspaceHtml(): string {
    return `<div class="stc-state">${escapeHtml(t('stc-need-workspace'))}<br><button type="button" class="btn btn-primary btn-sm" id="stc-pick-ws">${escapeHtml(t('stc-pick-workspace'))}</button></div>`;
}

export function stcNotEnabledHtml(): string {
    return `<div class="stc-state">${IC_BOX}<div>${escapeHtml(t('stc-not-enabled'))}</div></div>`;
}
