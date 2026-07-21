// 录入工作台 · 步③复核台(M2:批量按异常网格 + 逐张遮罩,替代旧手风琴 dms-intake-review)。
//
// 数据源 = 本批识别结果 IV.results(不是 /api/history)。每张 invoice → 一行;点行开逐张
// 遮罩(左真原图右可改字段)。字段改动实时写回 IV.results[fi].invoices[ii].fields —— 步④
// persistAllEdits 依赖此语义(与旧手风琴一致)。
//
// 诚实约束(沿用 M1):匹配/科目预填是 M3,此处不做 → 状态一律「待确认」,「已就绪」只反映
// 用户人工确认过的张数(不臆造机器就绪),科目/记账去向列留空 —。
import { renderReviewConsole } from './erp-review-console.js';
import type { ReviewRow, ConsoleData } from './erp-review-console.js';
import { createVerifyOverlay } from './erp-review-verify.js';
import type { VerifyRow, VerifyField } from './erp-review-verify.js';
import { CONSOLE_LABELS as M1_CONSOLE, VERIFY_LABELS } from './erp-review.js';
import { mountImageViewer } from './image-viewer.js';
import { IV, showStepInv } from './dms-intake-invoice.js';
import type { IvInvoice } from './dms-intake-invoice.js';
import { enterSubmit } from './dms-intake-invoice-submit.js';
import { $ } from './dms-intake-core.js';

// 步③沿用 M1 诚实 labels,仅换掉 dev 预览角标(真向导里不显「开发预览」)。
const CONSOLE_LABELS = {
    ...M1_CONSOLE,
    accountSet: '结果确认',
    agentOnline: '仅异常需人工确认',
    back: '返回上传',
};

// 可改字段(复用旧手风琴 REV_CORE 语义):[显示标签, 写回 IV 的字段键]。
const FIELDS: Array<[string, string]> = [
    ['单据号', 'invoice_number'],
    ['卖方', 'seller_name'],
    ['卖方税号', 'seller_tax'],
    ['日期(票面)', 'date_raw'],
    ['税前', 'subtotal'],
    ['VAT', 'vat'],
    ['合计', 'total_amount'],
];
const KEEP_EMPTY = new Set(['invoice_number', 'seller_name', 'total_amount']);

interface FlatRow {
    fi: number;
    ii: number;
    inv: IvInvoice;
    filename: string;
}

let flat: FlatRow[] = [];

function flatten(): FlatRow[] {
    const out: FlatRow[] = [];
    IV.results.forEach((r, fi) =>
        r.invoices.forEach((inv, ii) => out.push({ fi, ii, inv, filename: r.filename }))
    );
    return out;
}

// date_raw 缺 → 回落已归一 date(与旧手风琴一致,不让格子空着)。
function fval(inv: IvInvoice, k: string): string {
    const raw = k === 'date_raw' ? (inv.fields.date_raw ?? inv.fields.date) : inv.fields[k];
    return String(raw ?? '');
}

function fmtMoney(v: string): string {
    const n = parseFloat(v.replace(/,/g, ''));
    return isFinite(n)
        ? n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
        : '';
}

function rowId(fr: FlatRow): string {
    return `${fr.fi}:${fr.ii}`;
}

function toConsoleRow(fr: FlatRow): ReviewRow {
    return {
        id: rowId(fr),
        dir: 'in', // 真方向判定(税号比对)是 M3
        docno: fval(fr.inv, 'invoice_number') || fr.filename,
        party: fval(fr.inv, 'seller_name') || fval(fr.inv, 'buyer_name') || '—',
        amount: fmtMoney(fval(fr.inv, 'total_amount')),
        state: IV.confirmed.has(fr.fi) ? 'ready' : 'confirm',
    };
}

function toVerifyRow(fr: FlatRow): VerifyRow {
    const fields: VerifyField[] = FIELDS.map(([label, fk]) => ({
        key: label,
        fk,
        value: fval(fr.inv, fk),
    })).filter((f) => f.value !== '' || KEEP_EMPTY.has(f.fk as string));
    return {
        id: rowId(fr),
        docno: fval(fr.inv, 'invoice_number') || fr.filename,
        dir: 'in',
        fields,
    };
}

function openRow(id: string): void {
    const el = $('dx-s-inv-review');
    const mount = el?.querySelector('.dx-rc-overlay') as HTMLElement | null;
    if (!mount) return;
    const rows = flat.map(toVerifyRow);
    const start = flat.findIndex((fr) => rowId(fr) === id);
    const ctrl = createVerifyOverlay(mount, {
        rows,
        labels: VERIFY_LABELS,
        mountImage: (pane, row) => {
            const fr = flat.find((x) => rowId(x) === row.id);
            return mountImageViewer(pane, fr?.inv.history_id || null);
        },
        onFieldEdit: (rid, key, value) => {
            const fr = flat.find((x) => rowId(x) === rid);
            if (fr) fr.inv.fields[key] = value; // 实时写回 IV → 步④ persistAllEdits 生效
        },
        onConfirm: (rid) => IV.confirmed.add(+rid.split(':')[0]),
        onClose: renderReviewConsoleStep,
    });
    ctrl.open(Math.max(0, start));
}

function acceptAll(): void {
    IV.results.forEach((_, fi) => IV.confirmed.add(fi));
    renderReviewConsoleStep();
}

// 步③入口(替代旧 renderReview)。每次进/重渲 step③ 都调。
export function renderReviewConsoleStep(): void {
    IV.view = 'review';
    const el = $('dx-s-inv-review');
    if (!el) return;
    flat = flatten();
    el.innerHTML = '<div class="dx-rc-console"></div><div class="dx-rc-overlay"></div>';
    const rows = flat.map(toConsoleRow);
    const data: ConsoleData = {
        rows,
        readyCount: rows.filter((r) => r.state === 'ready').length,
        total: rows.length,
        unreadCount: 0,
    };
    renderReviewConsole(el.querySelector('.dx-rc-console') as HTMLElement, {
        data,
        labels: CONSOLE_LABELS,
        onOpenRow: openRow,
        onAcceptAll: acceptAll,
        onBack: () => showStepInv(1, 'dx-s-upload'), // 返回上传(补回删手风琴丢的那个按钮)
        onPush: () => void enterSubmit(), // 「全部确认 → 推送」= 进步④(推送仍是步④的事)
    });
    showStepInv(3, 'dx-s-inv-review');
}
