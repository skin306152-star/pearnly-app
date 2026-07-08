// ============================================================
// 录入工作台 · 汇总表批量建单 · 步骤3 预览(调 /validate · 徽章/警告全用后端真判)
// 方向/现金落点徽章直接渲染后端返回的 source + why;缺字段警告映射本地文案。硬阻断行标红。
// ============================================================
import { esc, $, showStep } from './dms-intake-core.js';
import { B, wsHeaders } from './dms-intake-batch.js';
import { enterBatchSubmit } from './dms-intake-batch-submit.js';

function t(k: string): string {
    const w = window as unknown as { t?: (k: string) => string };
    return typeof w.t === 'function' ? w.t(k) : k;
}

interface RowJudge {
    row_index: number;
    direction: { direction: string; source: string; why: string };
    payment: { target: string; source: string; why: string };
    warnings: string[];
    blocked: boolean;
    fields: Record<string, unknown>;
}
interface ValidateData {
    preview: RowJudge[];
    dup_doc_nos: string[];
    own_tax_present: boolean;
    workspace_name: string;
    total: number;
    blocked_count: number;
}

// 后端警告码 → i18n 文案键。
const W_KEY: Record<string, string> = {
    no_doc_no: 'dxb-w-nodocno',
    dup_doc_no: 'dxb-w-dupdocno',
    no_tax_not_walkin: 'dxb-w-notax',
    bad_date: 'dxb-w-baddate',
    amount_inconsistent: 'dxb-w-amount',
    no_product: 'dxb-w-noproduct',
    no_total: 'dxb-w-nototal',
};

let _data: ValidateData | null = null;

function dirBadge(j: RowJudge): string {
    const dir = j.direction.direction === 'sales' ? t('dxb-dir-sales') : t('dxb-dir-purchase');
    const cash = j.payment.target === 'cash' ? t('dxb-tag-cash') : t('dxb-tag-credit');
    // 方向来源:税号复核=绿(confirmed)· 按你所选=蓝(human_declared)。
    const dcls = j.direction.source === 'tax_confirmed' ? 'green' : 'blue';
    // 落点来源:有付款信号=绿(auto)· 默认赊账=琥珀(default·待确认)。
    const pcls = j.payment.source === 'auto' ? 'green' : 'amber';
    return (
        `<span class="dx-badge ${dcls}" title="${esc(j.direction.why)}">${esc(dir)}</span> ` +
        `<span class="dx-badge ${pcls}" title="${esc(j.payment.why)}">${esc(cash)}</span>`
    );
}

function warnHtml(j: RowJudge): string {
    if (!j.warnings.length) return `<span class="dx-badge green">${esc(t('dxb-w-ok'))}</span>`;
    return j.warnings
        .map((w) => {
            const key = W_KEY[w] || w;
            const cls = j.blocked ? 'red' : 'amber';
            return `<span class="dx-badge ${cls}">${esc(t(key))}</span>`;
        })
        .join(' ');
}

function rowHtml(j: RowJudge): string {
    const f = j.fields || {};
    const cell = (v: unknown) => esc(v == null ? '' : String(v));
    const buyer = (f.buyer_name as string) || (f.seller_name as string) || '';
    return (
        `<tr${j.blocked ? ' class="dxb-blocked"' : ''}>` +
        `<td>${cell(f.invoice_number)}</td>` +
        `<td>${cell(f.date)}</td>` +
        `<td>${cell(buyer)}</td>` +
        `<td class="dxb-num">${cell(f.total_amount)}</td>` +
        `<td>${dirBadge(j)}</td>` +
        `<td>${warnHtml(j)}</td>` +
        '</tr>'
    );
}

function summaryHtml(d: ValidateData): string {
    const ok = d.total - d.blocked_count;
    const taxWarn = d.own_tax_present
        ? ''
        : `<div class="dx-banner amber" style="margin-bottom:10px">${esc(t('dxb-no-own-tax'))}</div>`;
    return (
        taxWarn +
        `<div class="dx-note" style="margin-bottom:10px">${esc(
            t('dxb-rev-summary')
                .replace('{ok}', String(ok))
                .replace('{blocked}', String(d.blocked_count))
                .replace('{ws}', d.workspace_name || '—')
        )}</div>`
    );
}

function render() {
    const el = $('dx-s-batch-review');
    if (!el || !_data) return;
    const d = _data;
    const head =
        '<tr>' +
        `<th>${esc(t('dxb-th-docno'))}</th><th>${esc(t('dxb-th-date'))}</th>` +
        `<th>${esc(t('dxb-th-party'))}</th><th class="dxb-num">${esc(t('dxb-th-total'))}</th>` +
        `<th>${esc(t('dxb-th-route'))}</th><th>${esc(t('dxb-th-check'))}</th></tr>`;
    // 固定列宽:短列收窄,徽章列(方向/落点、检查)多分位置,消掉右侧空白。
    const cols =
        '<colgroup>' +
        '<col style="width:15%"><col style="width:11%"><col style="width:15%">' +
        '<col style="width:13%"><col style="width:27%"><col style="width:19%"></colgroup>';
    const canCommit = d.total - d.blocked_count > 0;
    el.innerHTML =
        summaryHtml(d) +
        `<div class="dxb-tblwrap"><table class="dxb-tbl">${cols}<thead>${head}</thead><tbody>` +
        d.preview.map(rowHtml).join('') +
        '</tbody></table></div>' +
        '<div class="dx-actions" style="margin-top:14px">' +
        `<button class="btn" id="dxb-back-map">${esc(t('dx-back'))}</button>` +
        `<button class="btn primary" id="dxb-commit"${canCommit ? '' : ' disabled'}>${esc(t('dxb-commit'))}</button></div>`;
}

export async function enterBatchReview() {
    if (B.busy || !B.parsed) return;
    B.busy = true;
    try {
        const r = await fetch('/api/summary-import/validate', {
            method: 'POST',
            headers: wsHeaders(true),
            body: JSON.stringify({
                parsed: B.parsed,
                column_map: B.columnMap,
                constants: B.constants,
            }),
        });
        const d = await r.json().catch(() => ({}));
        if (!r.ok || !d?.ok) {
            showToast(t('dxb-validate-fail'), 'error');
            return;
        }
        _data = d.data as ValidateData;
        B.view = 'review';
        render();
        showStep(3, 'dx-s-batch-review');
    } catch {
        showToast(t('dxb-validate-fail'), 'error');
    } finally {
        B.busy = false;
    }
}

export function onBatchReviewClick(tg: HTMLElement): boolean {
    if (tg.closest('#dxb-back-map')) {
        B.view = 'map';
        showStep(2, 'dx-s-batch-map');
        return true;
    }
    if (tg.closest('#dxb-commit')) {
        void enterBatchSubmit();
        return true;
    }
    return false;
}

export function rerenderBatchReview(): boolean {
    if (B.view === 'review' && _data) {
        render();
        showStep(3, 'dx-s-batch-review');
        return true;
    }
    return false;
}
