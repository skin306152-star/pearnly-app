// ============================================================
// 录入工作台 · 汇总表 → 批量建单(第三任务卡)· 步骤1 上传 + 步骤2 列映射/批次常量
// 步骤3 预览见 dms-intake-batch-review.ts;步骤4 提交见 dms-intake-batch-submit.ts。
// 后端:/api/summary-import/{parse,validate,commit}。判方向/落点/缺字段全由后端真判(前端不假装)。
// ============================================================
import { esc, $, authHeaders, showStep } from './dms-intake-core.js';
import { enterBatchReview } from './dms-intake-batch-review.js';

function t(k: string): string {
    const w = window as unknown as { t?: (k: string) => string };
    return typeof w.t === 'function' ? w.t(k) : k;
}

export function wsHeaders(json = false): Record<string, string> {
    const h = authHeaders(json);
    try {
        const w = window as unknown as { getActiveWorkspaceClientId?: () => unknown };
        const id =
            typeof w.getActiveWorkspaceClientId === 'function'
                ? w.getActiveWorkspaceClientId()
                : null;
        if (id != null) h['X-Workspace-Client-Id'] = String(id);
    } catch {
        /* 切换器未就绪 · 个人模式 → 后端回落默认账套 */
    }
    return h;
}

export interface ParsedTable {
    sheet_name: string;
    headers: string[];
    rows: Array<{ index: number; cells: string[]; is_summary: boolean }>;
    row_count: number;
    truncated: boolean;
}

export interface BatchConstants {
    direction: 'sales' | 'purchase';
    counterparty_name: string;
    counterparty_tax: string;
    product_name: string;
    product_code: string;
    payment_method: string;
    doc_no_pattern: string;
    cash_walkin: boolean;
    has_vat: boolean;
}

// 可映射的目标字段(表里有的按列取)· label 走 i18n。
const COLS: Array<[string, string]> = [
    ['date', 'dxb-col-date'],
    ['qty', 'dxb-col-qty'],
    ['unit_price', 'dxb-col-price'],
    ['subtotal', 'dxb-col-subtotal'],
    ['vat', 'dxb-col-vat'],
    ['total_amount', 'dxb-col-total'],
];

// 表头猜列(命中即预选·可改)· 关键词多语言。
const GUESS: Record<string, string[]> = {
    date: ['date', 'วันที่', '日期'],
    qty: ['qty', 'quantity', 'จำนวน', 'ยอด', '数量'],
    unit_price: ['unit price', 'price', 'ราคา', '单价'],
    subtotal: ['subtotal', 'before vat', 'ก่อน vat', 'ก่อนแวต', '税前', 'ยอดเงินก่อน'],
    vat: ['vat', 'ภาษี', '税额', 'ยอดเงิน vat'],
    total_amount: ['total', 'รวม', '总额', '合计', 'ยอดเงินรวม', 'ยอดรวม'],
};

export const B = {
    view: 'upload' as 'upload' | 'map' | 'review' | 'submit',
    file: null as File | null,
    parsed: null as ParsedTable | null,
    columnMap: {} as Record<string, number>,
    constants: {
        direction: 'sales',
        counterparty_name: '',
        counterparty_tax: '',
        product_name: '',
        product_code: '',
        payment_method: '',
        doc_no_pattern: '',
        cash_walkin: false,
        has_vat: true,
    } as BatchConstants,
    busy: false,
};

export function resetBatch() {
    B.view = 'upload';
    B.file = null;
    B.parsed = null;
    B.columnMap = {};
    B.busy = false;
}

function guessColumns(headers: string[]): Record<string, number> {
    const map: Record<string, number> = {};
    COLS.forEach(([key]) => {
        const kws = GUESS[key] || [];
        const idx = headers.findIndex((h) => {
            const low = (h || '').toLowerCase();
            return kws.some((kw) => low.includes(kw));
        });
        if (idx >= 0) map[key] = idx;
    });
    return map;
}

// ── 步骤 1:上传 ──────────────────────────────────────────────
export function renderBatchUpload() {
    const el = $('dx-s-batch-up');
    if (!el) return;
    const f = B.file;
    const body = f
        ? '<div class="dx-file"><div class="dx-file-ic">📊</div>' +
          `<div class="dx-file-c"><b>${esc(f.name)}</b><span>${(f.size / 1048576).toFixed(2)} MB</span></div>` +
          `<span class="dx-badge green">${esc(t('dx-up-ready'))}</span></div>` +
          '<div class="dx-bar"><div class="dx-note"></div><div style="display:flex;gap:8px">' +
          `<button class="btn" id="dxb-replace">${esc(t('dx-up-replace'))}</button>` +
          `<button class="btn primary" id="dxb-parse">${esc(t('dxb-up-parse'))}</button></div></div>`
        : '<div class="dx-drop up-dz" id="dxb-drop">' +
          `<div><div class="dx-drop-g">↑</div><h3>${esc(t('dxb-up-title'))}</h3>` +
          `<p>${esc(t('dxb-up-hint'))}</p>` +
          `<button class="btn primary" id="dxb-pick">${esc(t('dx-up-pick'))}</button>` +
          `<div class="dx-hint" style="margin-top:10px">${esc(t('dxb-up-formats'))}</div></div></div>`;
    el.innerHTML =
        '<div class="dx-two"><div class="dx-panel">' +
        `<div class="dx-panel-h"><b>${esc(t('dxb-up-title'))}</b><span>${esc(t('dxb-up-formats'))}</span></div>` +
        body +
        '</div>' +
        '<div class="dx-side"><div class="dx-side-box">' +
        `<b>${esc(t('dx-side-cur'))}</b><ul>` +
        `<li>${esc(t('dxb-flow1'))}</li><li>${esc(t('dxb-flow2'))}</li><li>${esc(t('dxb-flow3'))}</li></ul></div>` +
        `<div class="dx-side-box"><b>${esc(t('dx-side-rule'))}</b><p>${esc(t('dxb-side-tip'))}</p></div></div>` +
        '</div>' +
        '<input type="file" id="dxb-file" accept=".xlsx,.xls,.csv,.tsv" style="display:none">';
}

function pickFile() {
    ($('dxb-file') as HTMLInputElement)?.click();
}
function onFile(f: File | null) {
    if (!f) return;
    B.file = f;
    renderBatchUpload();
}

async function doParse() {
    if (!B.file || B.busy) return;
    B.busy = true;
    try {
        const form = new FormData();
        form.append('file', B.file, B.file.name);
        const r = await fetch('/api/summary-import/parse', {
            method: 'POST',
            headers: wsHeaders(),
            body: form,
        });
        const d = await r.json().catch(() => ({}));
        if (!r.ok || !d?.ok) {
            showToast(t('dxb-parse-fail'), 'error');
            return;
        }
        B.parsed = d.data as ParsedTable;
        B.columnMap = guessColumns(B.parsed.headers);
        B.view = 'map';
        renderBatchMap();
        showStep(2, 'dx-s-batch-map');
    } catch {
        showToast(t('dxb-parse-fail'), 'error');
    } finally {
        B.busy = false;
    }
}

// ── 步骤 2:列映射 + 批次常量 ─────────────────────────────────
function headerOptions(sel: number | undefined): string {
    const heads = B.parsed?.headers || [];
    const none = `<option value="-1"${sel == null ? ' selected' : ''}>${esc(t('dxb-col-none'))}</option>`;
    return (
        none +
        heads
            .map(
                (h, i) =>
                    `<option value="${i}"${sel === i ? ' selected' : ''}>${esc(h || '#' + (i + 1))}</option>`
            )
            .join('')
    );
}

function colMapHtml(): string {
    const rows = COLS.map(
        ([key, label]) =>
            '<div class="dx-map-row">' +
            `<span class="dx-map-k">${esc(t(label))}</span>` +
            `<select class="dx-inp" data-col="${key}">${headerOptions(B.columnMap[key])}</select>` +
            '</div>'
    ).join('');
    return `<div class="dx-panel"><div class="dx-panel-h"><b>${esc(t('dxb-map-h'))}</b><span>${esc(t('dxb-map-s'))}</span></div>${rows}</div>`;
}

function field(bk: keyof BatchConstants, label: string, ph = '', req = false): string {
    const v = String(B.constants[bk] ?? '');
    return (
        '<div class="dx-fld">' +
        `<label>${esc(t(label))}${req ? ' <span class="dx-req">*</span>' : ''}</label>` +
        `<input class="dx-inp" data-bk="${bk}" value="${esc(v)}" placeholder="${esc(ph)}">` +
        '</div>'
    );
}

function constHtml(): string {
    const c = B.constants;
    const dirSel = (v: string, k: string) =>
        `<option value="${v}"${c.direction === v ? ' selected' : ''}>${esc(t(k))}</option>`;
    const chk = (bk: keyof BatchConstants, label: string) =>
        '<label class="dx-chk">' +
        `<input type="checkbox" data-bk="${bk}"${c[bk] ? ' checked' : ''}> ${esc(t(label))}</label>`;
    return (
        `<div class="dx-panel"><div class="dx-panel-h"><b>${esc(t('dxb-const-h'))}</b><span>${esc(t('dxb-const-s'))}</span></div>` +
        '<div class="dx-fld">' +
        `<label>${esc(t('dxb-f-direction'))}</label>` +
        `<select class="dx-inp" data-bk="direction">${dirSel('sales', 'dxb-dir-sales')}${dirSel('purchase', 'dxb-dir-purchase')}</select></div>` +
        field('counterparty_name', 'dxb-f-counterparty', '', true) +
        field('counterparty_tax', 'dxb-f-tax', t('dxb-f-tax-ph')) +
        chk('cash_walkin', 'dxb-f-walkin') +
        field('product_name', 'dxb-f-product', '', true) +
        field('product_code', 'dxb-f-code', t('dxb-f-code-ph')) +
        field('payment_method', 'dxb-f-payment', t('dxb-f-payment-ph')) +
        field('doc_no_pattern', 'dxb-f-docno', t('dxb-f-docno-ph'), true) +
        chk('has_vat', 'dxb-f-vat') +
        '</div>'
    );
}

export function renderBatchMap() {
    const el = $('dx-s-batch-map');
    if (!el || !B.parsed) return;
    const p = B.parsed;
    el.innerHTML =
        `<div class="dx-note" style="margin-bottom:10px">${esc(t('dxb-parsed-note').replace('{n}', String(p.row_count)).replace('{sheet}', p.sheet_name))}</div>` +
        '<div class="dx-two">' +
        colMapHtml() +
        constHtml() +
        '</div>' +
        '<div class="dx-actions" style="margin-top:14px">' +
        `<button class="btn" id="dxb-back-up">${esc(t('dx-back'))}</button>` +
        `<button class="btn primary" id="dxb-to-review">${esc(t('dxb-to-review'))}</button></div>`;
}

// ── 事件(由 dms-intake.ts 委托进来)──────────────────────────
export function onBatchClick(tg: HTMLElement) {
    const hit = (id: string) => tg.closest('#' + id);
    if (hit('dxb-pick') || (tg.closest('#dxb-drop') && !B.file)) return pickFile();
    if (hit('dxb-replace')) {
        B.file = null;
        return renderBatchUpload();
    }
    if (hit('dxb-parse')) return void doParse();
    if (hit('dxb-back-up')) {
        B.view = 'upload';
        renderBatchUpload();
        return showStep(1, 'dx-s-batch-up');
    }
    if (hit('dxb-to-review')) return void enterBatchReview();
}

export function onBatchChange(tg: HTMLElement) {
    if (tg.id === 'dxb-file') return onFile((tg as HTMLInputElement).files?.[0] || null);
    const col = (tg as HTMLElement).dataset?.col;
    if (col) {
        const v = parseInt((tg as HTMLSelectElement).value, 10);
        if (v < 0) delete B.columnMap[col];
        else B.columnMap[col] = v;
        return;
    }
    const bk = (tg as HTMLElement).dataset?.bk as keyof BatchConstants | undefined;
    if (bk) {
        const inp = tg as HTMLInputElement;
        if (inp.type === 'checkbox') (B.constants[bk] as unknown) = inp.checked;
        else (B.constants[bk] as unknown) = inp.value;
    }
}

export function onBatchDrop(files: FileList | undefined) {
    onFile(files?.[0] || null);
}

// 续步:软导航回来时复原到离开的步骤(硬刷新内存空 → 回落上传步)。
export function rerenderBatch(): boolean {
    if (B.view === 'map' && B.parsed) {
        renderBatchMap();
        showStep(2, 'dx-s-batch-map');
        return true;
    }
    return false;
}
