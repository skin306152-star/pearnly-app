// ERP 门户 · 商品收发存报表 · 纯渲染层(HTML 字符串拼装 · 无状态 · 不碰 DOM)
// 一份按商品连续排列的 13 列长表:每个商品一段头(名称/编码/单位)+ 参考图原样 13 列表格
// (期初行 + 期间逐笔 + 该组合计)。三段式表头配色(入=绿/出=粉/结存=紫),负数按原值
// 显示 · 视觉规格按业务参考图锁定,令牌换成本仓
// static/pearnly-ui.css + home-01-base.css。
/* global t, escapeHtml */
import { formatDate } from './format-date.js';
import { fmtAmt, fmtQty, type StcCardRow, type StcGroup } from './stock-card-api.js';

const IC_BOX =
    '<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M21 16V8a2 2 0 0 0-1-1.7l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.7l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><path d="M3.3 7 12 12l8.7-5M12 22V12"/></svg>';

// ── 参考图原样 13 列表格(每商品一张)────────────────────────────────
const _COLS = [
    'stc-col-date',
    'stc-col-doc',
    'stc-col-type',
    'stc-col-desc',
    'stc-col-in',
    'stc-col-out',
    'stc-col-bal',
] as const;

export function stc13Head(): string {
    return `<colgroup>
        <col class="stc-w-date"><col class="stc-w-doc"><col class="stc-w-type"><col class="stc-w-desc">
        ${'<col class="stc-w-num">'.repeat(9)}
    </colgroup><thead>
        <tr class="stc-grp">
            <th rowspan="2">${escapeHtml(t(_COLS[0]))}</th>
            <th rowspan="2">${escapeHtml(t(_COLS[1]))}</th>
            <th rowspan="2">${escapeHtml(t(_COLS[2]))}</th>
            <th rowspan="2">${escapeHtml(t(_COLS[3]))}</th>
            <th class="stc-g-in" colspan="3">${escapeHtml(t(_COLS[4]))}</th>
            <th class="stc-g-out" colspan="3">${escapeHtml(t(_COLS[5]))}</th>
            <th class="stc-g-bal" colspan="3">${escapeHtml(t(_COLS[6]))}</th>
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

const MOVE_TYPE_KEY: Record<StcCardRow['kind'], string> = {
    open: 'stc-type-open',
    in: 'stc-type-in',
    out: 'stc-type-out',
};

export function stc13Row(r: StcCardRow): string {
    const isIn = r.kind === 'in';
    const isOut = r.kind === 'out';
    const date = formatDate(r.date, { style: 'DD/MM/YYYY' }) || r.date;
    return `<tr>
        <td class="c">${escapeHtml(date)}</td>
        <td class="c">${escapeHtml(r.doc_no || '—')}</td>
        <td class="c"><span class="stc-type stc-type-${r.kind}">${escapeHtml(t(MOVE_TYPE_KEY[r.kind]))}</span></td>
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

// 后端 totals 缺的字段从 rows 现算兜底(口径与后端一致:按 kind 分组求 qty/金额;结存取
// 最后一行,无行则回落 0/null)——不让页面因为 totals 形状不齐就崩。
// 金额合计沿用诚实口径:任一行金额未知就整组置 null,不拿已知部分的和冒充。空值一路
// 传导到合计,不在 Number(null)||0 处被焊死成 0(后端 _sum_amount_known 同一口径)。
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

export function stc13Foot(g: StcGroup): string {
    const totals = g.totals;
    const last = g.rows.length ? g.rows[g.rows.length - 1] : null;
    const inS = sumKind(g.rows, 'in');
    const outS = sumKind(g.rows, 'out');
    const inQty = totals.in_qty ?? String(inS.qty);
    const outQty = totals.out_qty ?? String(outS.qty);
    const balQty = totals.bal_qty ?? last?.bal_qty ?? '0';
    const balUnit =
        totals.bal_unit_cost !== undefined ? totals.bal_unit_cost : (last?.bal_unit_cost ?? null);
    const balVal = totals.bal_value !== undefined ? totals.bal_value : (last?.bal_value ?? null);
    return `<tfoot>
        <tr>
            <td colspan="4">${escapeHtml(t('stc-total'))}</td>
            <td class="num stc-t-in">${fmtQty(inQty)}</td><td class="stc-t-in"></td>
            <td class="num stc-t-in">${fmtAmt(totals.in_amount ?? inS.amt)}</td>
            <td class="num stc-t-out">${fmtQty(outQty)}</td><td class="stc-t-out"></td>
            <td class="num stc-t-out">${fmtAmt(totals.out_amount ?? outS.amt)}</td>
            <td class="num">${fmtQty(balQty)}</td>
            <td class="num">${fmtAmt(balUnit)}</td>
            <td class="num">${fmtAmt(balVal)}</td>
        </tr>
    </tfoot>`;
}

// 一个商品块:标题(名称/编码/单位) + 独立横滚的 13 列表格容器。
export function stcGroupBlock(g: StcGroup): string {
    const p = g.product;
    const code = p.product_id
        ? `<span class="stc-group-code">${escapeHtml(p.product_id)}</span>`
        : '';
    const unit = p.unit ? `<span class="stc-group-unit">${escapeHtml(p.unit)}</span>` : '';
    return `<section class="stc-group">
        <div class="stc-group-title">
            <span class="stc-group-name">${escapeHtml(p.name || '—')}</span>
            ${code}${unit}
        </div>
        <div class="stc-scroll">
            <table>${stc13Head()}<tbody>${g.rows.map(stc13Row).join('')}</tbody>${stc13Foot(g)}</table>
        </div>
    </section>`;
}

// cols 按目标表头实际列数传:骨架行只是过渡态,但列数对不上表头会在加载那一瞬把表格撑变形。
export function stcSkeletonBody(cols: number): string {
    const cell = '<td><div class="stc-skel"></div></td>';
    return `<tbody>${`<tr>${cell.repeat(cols)}</tr>`.repeat(5)}</tbody>`;
}

// ── 四态公共壳 ──────────────────────────────────────────────────────
export function stcEmptyState(msg: string): string {
    return `<div class="stc-state">${IC_BOX}<div>${escapeHtml(msg)}</div></div>`;
}

export function stcNeedWorkspaceHtml(): string {
    return `<div class="stc-state">${escapeHtml(t('stc-need-workspace'))}<br><button type="button" class="btn btn-primary btn-sm" id="stc-pick-ws">${escapeHtml(t('stc-pick-workspace'))}</button></div>`;
}

export function stcNotEnabledHtml(): string {
    return `<div class="stc-state">${IC_BOX}<div>${escapeHtml(t('stc-not-enabled'))}</div></div>`;
}
