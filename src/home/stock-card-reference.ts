import { formatDate } from './format-date.js';
import {
    fmtAmt,
    fmtQty,
    type StcGroup,
    type StcCardRow,
    type StcCardTotals,
} from './stock-card-api.js';
import './stock-card-reference.css';
const words = () =>
    ({
        zh: ['单据', '单位', '条明细', '种商品'],
        th: ['ใบสำคัญ', 'หน่วย', 'รายการ', 'สินค้า'],
        en: ['Document', 'Unit', 'movements', 'products'],
        ja: ['伝票', '単位', '明細', '商品'],
    })[String(window.currentLang || 'th')] || ['ใบสำคัญ', 'หน่วย', 'รายการ', 'สินค้า'];
const e = (s: unknown) => escapeHtml(String(s ?? ''));
const label = (key: string) => e(t(key));
export function referenceHead(): string {
    return `<colgroup><col style="width:120px"><col style="width:180px">${'<col>'.repeat(9)}</colgroup><thead><tr><th colspan="2">${e(words()[0])}</th>${['in', 'out', 'bal'].map((k) => `<th colspan="3">${label('stc-col-' + k)}</th>`).join('')}</tr><tr><th>${label('stc-col-date')}</th><th>${label('stc-col-doc')}</th>${Array.from({ length: 3 }, () => ['qty', 'price', 'amt'].map((k) => `<th class="num">${label('stc-col-' + k)}</th>`).join('')).join('')}</tr></thead>`;
}
function row(r: StcCardRow): string {
    const cols = ['in', 'out']
        .map((kind) =>
            r.kind === kind
                ? `<td class="num">${fmtQty(r.qty)}</td><td class="num">${fmtAmt(r.unit_price)}</td><td class="num">${fmtAmt(r.amount)}</td>`
                : '<td class="num"></td><td class="num"></td><td class="num"></td>'
        )
        .join('');
    return `<tr>${r.kind === 'open' ? `<td colspan="2">${label('stc-type-open')}</td>` : `<td>${e(formatDate(r.date, { style: 'DD/MM/YYYY' }))}</td><td>${e(r.doc_no)}</td>`}${cols}<td class="num">${fmtQty(r.bal_qty)}</td><td class="num">${fmtAmt(r.bal_unit_cost)}</td><td class="num">${fmtAmt(r.bal_value)}</td></tr>`;
}
function opening(rows: StcCardRow[]): string {
    const value = rows.find((r) => r.kind === 'open');
    if (!value) return '';
    return `<div class="stc-ref-opening"><strong>${label('stc-type-open')} · ${label('stc-col-bal')}</strong><span>${label('stc-col-qty')}<b>${fmtQty(value.bal_qty)}</b></span><span>${label('stc-col-price')}<b>${fmtAmt(value.bal_unit_cost)}</b></span><span>${label('stc-col-amt')}<b>${fmtAmt(value.bal_value)}</b></span></div>`;
}
function totals(value: StcCardTotals, title: string): string {
    return `<tr><td colspan="2">${title}</td><td class="num">${fmtQty(value.in_qty || '0')}</td><td></td><td class="num">${fmtAmt(value.in_amount ?? null)}</td><td class="num">${fmtQty(value.out_qty || '0')}</td><td></td><td class="num">${fmtAmt(value.out_amount ?? null)}</td><td class="num">${fmtQty(value.bal_qty || '0')}</td><td></td><td class="num">${fmtAmt(value.bal_value ?? null)}</td></tr>`;
}
export function referenceReport(groups: StcGroup[], _grand?: StcCardTotals): string {
    const body = groups
        .map(
            (g) =>
                `<details class="stc-ref-group" data-stock-key="${e(g.product.key)}"><summary><span class="stc-ref-arrow"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m9 5 7 7-7 7"/></svg></span><strong>${e(g.product.code || '')} ${e(g.product.name)}</strong><span class="stc-ref-unit">${e(words()[1])}: ${e(g.product.unit || '—')}</span></summary>${opening(g.rows)}<div class="stc-ref-scroll"><table class="stc-ref-table">${referenceHead()}<tbody>${g.rows
                    .filter((r) => r.kind !== 'open')
                    .map(row)
                    .join(
                        ''
                    )}</tbody><tfoot>${totals(g.totals, `${label('stc-total')} · ${g.rows.filter((r) => r.kind !== 'open').length} ${e(words()[2])}`)}</tfoot></table></div></details>`
        )
        .join('');
    return `<div class="stc-reference">${body}</div>`;
}
