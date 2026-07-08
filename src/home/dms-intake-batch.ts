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
    preamble?: string;
    suggested_period?: number[] | null; // [公历 year, month] · 从标题自动认出
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
    period_year: string; // 批次年月:日期列只有日号时按此拼完整日期(佛历自动转公历)
    period_month: string;
    unit_price: string; // 固定单价:只填数量时按此算金额(税前=量×价)
}

export interface ManualRow {
    date: string;
    qty: string;
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
    mode: 'upload' as 'upload' | 'manual',
    view: 'upload' as 'upload' | 'map' | 'review' | 'submit',
    file: null as File | null,
    parsed: null as ParsedTable | null,
    columnMap: {} as Record<string, number>,
    rows: [] as ManualRow[], // 直接填模式:逐日 {日期, 数量}
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
        period_year: '',
        period_month: '',
        unit_price: '',
    } as BatchConstants,
    busy: false,
};

export function resetBatch() {
    B.mode = 'upload';
    B.view = 'upload';
    B.file = null;
    B.parsed = null;
    B.columnMap = {};
    B.rows = [];
    B.busy = false;
}

// 表头猜列:按「最长命中关键词」贪心配对,每个表头只归一个字段。
// (泰文表头 "ยอดเงินก่อน vat" 既含 subtotal 的 "ยอดเงินก่อน" 又含 vat 的裸 "vat" →
//  最长命中胜出,避免 subtotal/vat 撞同一列造成"金额不符"假阳。)
function guessColumns(headers: string[]): Record<string, number> {
    const cands: Array<{ key: string; idx: number; score: number }> = [];
    COLS.forEach(([key]) => {
        const kws = GUESS[key] || [];
        headers.forEach((h, idx) => {
            const low = (h || '').toLowerCase();
            const score = kws.reduce((m, kw) => (low.includes(kw) ? Math.max(m, kw.length) : m), 0);
            if (score > 0) cands.push({ key, idx, score });
        });
    });
    cands.sort((a, b) => b.score - a.score);
    const map: Record<string, number> = {};
    const usedIdx = new Set<number>();
    cands.forEach((c) => {
        if (c.key in map || usedIdx.has(c.idx)) return;
        map[c.key] = c.idx;
        usedIdx.add(c.idx);
    });
    return map;
}

// 模式选择:「我有汇总表(上传解析)」/「我没有表(直接填)」。选完各走各路,后面共用。
function modeTabs(): string {
    const tab = (m: 'upload' | 'manual', title: string, desc: string) =>
        `<button class="dxb-mode${B.mode === m ? ' active' : ''}" data-mode="${m}">` +
        `<b>${esc(t(title))}</b><span>${esc(t(desc))}</span></button>`;
    return (
        '<div class="dxb-modes">' +
        tab('upload', 'dxb-mode-upload', 'dxb-mode-upload-d') +
        tab('manual', 'dxb-mode-manual', 'dxb-mode-manual-d') +
        '</div>'
    );
}

// ── 步骤 1:选模式 + 上传(有表)/ 开始填(没表)─────────────────
export function renderBatchUpload() {
    const el = $('dx-s-batch-up');
    if (!el) return;
    const f = B.file;
    const uploadBody = f
        ? '<div class="dx-file"><div class="dx-file-ic">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" width="18" height="18"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M9 4v16"/></svg></div>' +
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
    const manualBody =
        '<div class="dx-drop"><div>' +
        `<div class="dx-drop-g">✎</div><h3>${esc(t('dxb-manual-title'))}</h3>` +
        `<p>${esc(t('dxb-manual-hint'))}</p>` +
        `<button class="btn primary" id="dxb-manual-start">${esc(t('dxb-manual-start'))}</button></div></div>`;
    const body = B.mode === 'manual' ? manualBody : uploadBody;
    el.innerHTML =
        '<div class="dx-two"><div class="dx-panel">' +
        `<div class="dx-panel-h"><b>${esc(t('dxb-up-title'))}</b><span>${esc(t('dxb-up-formats'))}</span></div>` +
        modeTabs() +
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
        // 标题里认出年月 → 预填(显示佛历,与表一致;后端 _period 会转公历)。日期是完整日期时此项忽略。
        const sp = B.parsed.suggested_period;
        if (sp && sp.length === 2) {
            B.constants.period_year = String(sp[0] + 543);
            B.constants.period_month = String(sp[1]);
        }
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
            `<span class="dx-map-arrow">→</span>` +
            `<select class="dx-inp" data-col="${key}">${headerOptions(B.columnMap[key])}</select>` +
            '</div>'
    ).join('');
    return (
        `<div class="dx-panel"><div class="dx-panel-h"><b>${esc(t('dxb-map-h'))}</b><span>${esc(t('dxb-map-s'))}</span></div>` +
        `<div class="dx-mapgrid">${rows}</div></div>`
    );
}

function field(
    bk: keyof BatchConstants,
    label: string,
    ph = '',
    req = false,
    hintKey = ''
): string {
    const v = String(B.constants[bk] ?? '');
    const hint = hintKey ? `<div class="dx-hint">${esc(t(hintKey))}</div>` : '';
    return (
        '<div class="dx-fld">' +
        `<label>${esc(t(label))}${req ? ' <span class="dx-req">*</span>' : ''}</label>` +
        `<input class="dx-inp" data-bk="${bk}" value="${esc(v)}" placeholder="${esc(ph)}">` +
        hint +
        '</div>'
    );
}

function constHtml(): string {
    const c = B.constants;
    const dirSel = (v: string, k: string) =>
        `<option value="${v}"${c.direction === v ? ' selected' : ''}>${esc(t(k))}</option>`;
    const chk = (bk: keyof BatchConstants, label: string, hintKey: string) =>
        '<div class="dx-chk-row"><label class="dx-chk">' +
        `<input type="checkbox" data-bk="${bk}"${c[bk] ? ' checked' : ''}> ${esc(t(label))}</label>` +
        `<div class="dx-hint">${esc(t(hintKey))}</div></div>`;
    const directionFld =
        '<div class="dx-fld">' +
        `<label>${esc(t('dxb-f-direction'))}</label>` +
        `<select class="dx-inp" data-bk="direction">${dirSel('sales', 'dxb-dir-sales')}${dirSel('purchase', 'dxb-dir-purchase')}</select>` +
        `<div class="dx-hint">${esc(t('dxb-h-direction'))}</div></div>`;
    const periodFld =
        '<div class="dx-fld"><label>' +
        esc(t('dxb-f-period')) +
        `</label><div class="dx-period"><input class="dx-inp" data-bk="period_year" value="${esc(String(c.period_year ?? ''))}" placeholder="${esc(t('dxb-f-period-year-ph'))}" inputmode="numeric"><input class="dx-inp" data-bk="period_month" value="${esc(String(c.period_month ?? ''))}" placeholder="${esc(t('dxb-f-period-month-ph'))}" inputmode="numeric"></div>` +
        `<div class="dx-hint">${esc(t('dxb-f-period-hint'))}</div></div>`;
    return (
        `<div class="dx-panel"><div class="dx-panel-h"><b>${esc(t('dxb-const-h'))}</b><span>${esc(t('dxb-const-s'))}</span></div>` +
        '<div class="dx-fillgrid">' +
        directionFld +
        periodFld +
        field('counterparty_name', 'dxb-f-counterparty', '', true, 'dxb-h-counterparty') +
        field('counterparty_tax', 'dxb-f-tax', t('dxb-f-tax-ph'), false, 'dxb-h-tax') +
        chk('cash_walkin', 'dxb-f-walkin', 'dxb-h-walkin') +
        field('product_name', 'dxb-f-product', '', true, 'dxb-h-product') +
        field('product_code', 'dxb-f-code', t('dxb-f-code-ph'), false, 'dxb-h-code') +
        field(
            'unit_price',
            'dxb-f-price',
            t('dxb-f-price-ph'),
            B.mode === 'manual',
            'dxb-h-price'
        ) +
        field('payment_method', 'dxb-f-payment', t('dxb-f-payment-ph'), false, 'dxb-h-payment') +
        field('doc_no_pattern', 'dxb-f-docno', t('dxb-f-docno-ph'), true, 'dxb-h-docno') +
        chk('has_vat', 'dxb-f-vat', 'dxb-h-vat') +
        '</div></div>'
    );
}

// 直接填模式:逐日 {日期 | 数量} 网格(单价固定,金额自动算)。
function gridHtml(): string {
    const head =
        '<div class="dxb-gridrow dxb-gridhead">' +
        `<span class="dxb-gno">#</span><span>${esc(t('dxb-grid-date'))}</span>` +
        `<span>${esc(t('dxb-grid-qty'))}</span><span></span></div>`;
    const rows = B.rows
        .map(
            (r, i) =>
                '<div class="dxb-gridrow">' +
                `<span class="dxb-gno">${i + 1}</span>` +
                `<input class="dx-inp" data-grid-row="${i}" data-grid-field="date" value="${esc(r.date)}" placeholder="${esc(t('dxb-grid-date-ph'))}">` +
                `<input class="dx-inp" data-grid-row="${i}" data-grid-field="qty" value="${esc(r.qty)}" placeholder="${esc(t('dxb-grid-qty-ph'))}" inputmode="decimal">` +
                `<button class="dxb-gdel" data-row="${i}" aria-label="${esc(t('dxb-grid-del'))}">×</button>` +
                '</div>'
        )
        .join('');
    return (
        `<div class="dx-panel"><div class="dx-panel-h"><b>${esc(t('dxb-grid-h'))}</b><span>${esc(t('dxb-grid-s'))}</span></div>` +
        head +
        `<div class="dxb-grid">${rows}</div>` +
        '<div class="dx-bar" style="margin-top:10px;justify-content:flex-start;gap:8px">' +
        `<button class="btn" id="dxb-grid-add">${esc(t('dxb-grid-add'))}</button>` +
        `<button class="btn" id="dxb-grid-genmonth">${esc(t('dxb-grid-genmonth'))}</button></div></div>`
    );
}

function step2Actions(): string {
    return (
        '<div class="dx-actions" style="margin-top:14px">' +
        `<button class="btn" id="dxb-back-up">${esc(t('dx-back'))}</button>` +
        `<button class="btn primary" id="dxb-to-review">${esc(t('dxb-to-review'))}</button></div>`
    );
}

export function renderBatchMap() {
    const el = $('dx-s-batch-map');
    if (!el) return;
    if (B.mode === 'manual') {
        el.innerHTML =
            `<div class="dx-note" style="margin-bottom:10px">${esc(t('dxb-manual-note'))}</div>` +
            `<div class="dxb-step2">${gridHtml()}${constHtml()}</div>` +
            step2Actions();
        return;
    }
    if (!B.parsed) return;
    const p = B.parsed;
    el.innerHTML =
        `<div class="dx-note" style="margin-bottom:10px">${esc(t('dxb-parsed-note').replace('{n}', String(p.row_count)).replace('{sheet}', p.sheet_name))}</div>` +
        `<div class="dxb-step2">${colMapHtml()}${constHtml()}</div>` +
        step2Actions();
}

// ── 事件(由 dms-intake.ts 委托进来)──────────────────────────
// 直接填 → 合成 parsed(cells=[日期,数量]),复用同一条 validate/commit 链。
function manualToReview() {
    const rows = B.rows
        .filter((r) => (r.date || '').trim() || (r.qty || '').trim())
        .map((r, i) => ({
            index: i,
            cells: [(r.date || '').trim(), (r.qty || '').trim()],
            is_summary: false,
        }));
    B.parsed = {
        sheet_name: 'manual',
        headers: ['date', 'qty'],
        rows,
        row_count: rows.length,
        truncated: false,
    };
    B.columnMap = { date: 0, qty: 1 };
    void enterBatchReview();
}

// 按批次年月生成整月逐日行(日期填日号,后端配年月拼完整日期)。
function genMonthRows() {
    const m = parseInt(B.constants.period_month, 10);
    let y = parseInt(B.constants.period_year, 10);
    if (!(m >= 1 && m <= 12) || !y) return showToast(t('dxb-grid-needperiod'), 'error');
    if (y >= 2400) y -= 543; // 佛历 → 公历取当月天数
    const days = new Date(y, m, 0).getDate();
    B.rows = Array.from({ length: days }, (_, i) => ({ date: String(i + 1), qty: '' }));
    renderBatchMap();
}

export function onBatchClick(tg: HTMLElement) {
    const hit = (id: string) => tg.closest('#' + id);
    const modeBtn = tg.closest('[data-mode]');
    if (modeBtn) {
        B.mode = modeBtn.getAttribute('data-mode') === 'manual' ? 'manual' : 'upload';
        B.file = null;
        return renderBatchUpload();
    }
    if (hit('dxb-manual-start')) {
        if (!B.rows.length) B.rows = Array.from({ length: 5 }, () => ({ date: '', qty: '' }));
        B.view = 'map';
        renderBatchMap();
        return showStep(2, 'dx-s-batch-map');
    }
    if (hit('dxb-grid-add')) {
        B.rows.push({ date: '', qty: '' });
        return renderBatchMap();
    }
    if (hit('dxb-grid-genmonth')) return genMonthRows();
    const del = tg.closest('.dxb-gdel');
    if (del) {
        B.rows.splice(parseInt(del.getAttribute('data-row') || '-1', 10), 1);
        return renderBatchMap();
    }
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
    if (hit('dxb-to-review'))
        return B.mode === 'manual' ? manualToReview() : void enterBatchReview();
}

export function onBatchChange(tg: HTMLElement) {
    if (tg.id === 'dxb-file') return onFile((tg as HTMLInputElement).files?.[0] || null);
    const gr = (tg as HTMLElement).dataset?.gridRow;
    if (gr !== undefined) {
        const row = B.rows[parseInt(gr, 10)];
        const fld = (tg as HTMLElement).dataset?.gridField as keyof ManualRow | undefined;
        if (row && fld) row[fld] = (tg as HTMLInputElement).value;
        return;
    }
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
    if (B.view === 'map' && (B.parsed || B.mode === 'manual')) {
        renderBatchMap();
        showStep(2, 'dx-s-batch-map');
        return true;
    }
    return false;
}
