// ============================================================
// 录入工作台 · 发票/收据任务(精简流)· 复用现有 OCR 接口,不重写后端。
//   上传 → /api/ocr/recognize → 复核(队列+可编辑)→ 导出/推送 → 结果。
// 与 #page-ocr 完整发票页相互独立(本模块状态 IV 自持,不碰 window._results)。
// 导出/推送/结果在 dms-intake-invoice-submit.ts(控行数);本文件管上传/识别/复核/事件分发。
// ============================================================
/* global t, token, showToast */
import { S, esc, $, authHeaders } from './dms-intake-core.js';
import { enterSubmit, renderSubmit, doFinish } from './dms-intake-invoice-submit.js';

export type Dict = Record<string, unknown>;
export interface IvFile {
    file: File;
    name: string;
    status: 'waiting' | 'processing' | 'success' | 'error';
    errorKey?: string;
}
export interface IvResult {
    filename: string;
    pages: unknown[];
    merged: Dict;
    history_ids: string[];
    invoice_count: number;
    confidence: string;
}
export interface Endpoint {
    id?: unknown;
    adapter?: string;
    name?: string;
    enabled?: boolean;
    is_default?: boolean;
}

export const IV = {
    files: [] as IvFile[],
    results: [] as IvResult[],
    sel: 0, // 复核中选中的结果下标
    showAll: false,
    output: { excel: true, erp: false },
    tpl: 'input_vat',
    endpoints: [] as Endpoint[],
    target: '' as string,
    busy: false,
    view: 'upload' as 'upload' | 'review' | 'submit' | 'success',
};

export const w = window as unknown as {
    getMaxFiles?: () => number;
    getMaxMbPerFile?: () => number;
    mergeFields?: (pages: unknown) => Dict;
    routeTo?: (r: string) => void;
};

const UPLOAD_ACCEPT =
    '.pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.bmp,.gif,.xlsx,.xls,.xlsm,.csv,.tsv,.docx,.doc,.txt';
const SUPPORTED = /\.(pdf|png|jpe?g|webp|tiff?|bmp|gif|xlsx?|xlsm|csv|tsv|docx?|txt)$/i;

// 复核预览字段(复用 OCR 抽屉的字段标签键)· warn=低置信常需确认
const REV_CORE: Array<[string, string]> = [
    ['seller_name', 'drawer-lbl-name'],
    ['seller_tax', 'drawer-lbl-tax'],
    ['invoice_number', 'drawer-lbl-invoice'],
    ['date', 'drawer-lbl-date'],
    ['subtotal', 'drawer-lbl-subtotal'],
    ['vat', 'drawer-lbl-vat'],
];
const REV_MORE: Array<[string, string]> = [
    ['total_amount', 'drawer-lbl-total'],
    ['buyer_name', 'drawer-lbl-name'],
    ['wht_amount', 'drawer-lbl-wht-amount'],
];

export function resetInvoice() {
    IV.files = [];
    IV.results = [];
    IV.sel = 0;
    IV.showAll = false;
    IV.output = { excel: true, erp: false };
    IV.target = '';
    IV.busy = false;
    IV.view = 'upload';
}

// 语言切换时按当前视图重渲(由 dms-intake.ts 的 subscribeI18n 调)
export function rerenderInvoice() {
    if (IV.view === 'review') renderReview();
    else if (IV.view === 'submit') renderSubmit();
    else {
        renderInvoiceUpload();
        showStepInv(1, 'dx-s-upload');
    }
}

export function ext(name: string) {
    const m = /\.([a-z0-9]+)$/i.exec(name);
    return (m ? m[1] : 'file').toUpperCase().slice(0, 4);
}
// 步骤条(发票 4 步)· 复用 core.showStep 的 DOM 操作
export function showStepInv(step: number, stateId: string) {
    S.step = step;
    const sc = document.getElementById('page-dms-intake');
    sc?.querySelectorAll('.dx-state').forEach((s) => s.classList.remove('active'));
    document.getElementById(stateId)?.classList.add('active');
    sc?.querySelector('.dx-stepper')?.setAttribute('data-frac', step + ' / 4');
    sc?.querySelectorAll('.dx-step').forEach((el, i) => {
        const n = i + 1;
        el.classList.toggle('active', n === step);
        el.classList.toggle('done', n < step);
        const no = el.querySelector('.dx-step-no');
        if (no) no.textContent = n < step ? '✓' : String(n);
    });
}

// ── 步骤 1:上传 ──────────────────────────────────────────────
export function renderInvoiceUpload() {
    IV.view = 'upload';
    const el = $('dx-s-upload');
    if (!el) return;
    const maxF = w.getMaxFiles?.() || 500;
    const maxMb = w.getMaxMbPerFile?.() || 100;
    const fmt = t('dxi-up-formats').replace('{mb}', String(maxMb)).replace('{n}', String(maxF));
    el.innerHTML =
        '<div class="dx-two"><div class="dx-panel"><div class="dx-panel-h">' +
        `<b>${esc(t('dxi-up-title'))}</b><span>${esc(fmt)}</span></div>` +
        (IV.files.length ? queueHtml() : dropHtml()) +
        '</div>' +
        sideHtml() +
        '</div>' +
        `<input type="file" id="dx-inv-file" accept="${UPLOAD_ACCEPT}" multiple style="display:none">` +
        '<input type="file" id="dx-inv-cam" accept="image/*" capture="environment" style="display:none">' +
        '<input type="file" id="dx-inv-gal" accept="image/*" multiple style="display:none">';
}
function dropHtml() {
    return (
        '<div class="dx-drop" id="dx-inv-drop"><div>' +
        '<div class="dx-drop-g">↑</div>' +
        `<h3>${esc(t('dxi-up-title'))}</h3><p>${esc(t('dxi-up-hint'))}</p>` +
        '<div class="dx-up-btns">' +
        `<button class="btn primary" id="dx-inv-pick">${esc(t('dxi-up-pick'))}</button>` +
        `<button class="btn" id="dx-inv-camera">${esc(t('dxi-up-camera'))}</button>` +
        `<button class="btn" id="dx-inv-gallery">${esc(t('dxi-up-gallery'))}</button></div>` +
        `<div class="dx-hint" style="margin-top:10px">${esc(t('dxi-up-drag'))}</div></div></div>`
    );
}
function queueHtml() {
    const rows = IV.files
        .map((f, i) => {
            const st =
                f.status === 'error'
                    ? `<span class="dx-badge amber">${esc(t(f.errorKey || 'dxi-recognize-fail'))}</span>`
                    : f.status === 'success'
                      ? `<span class="dx-badge green">${esc(t('dxi-rev-ok'))}</span>`
                      : `<span class="dx-badge blue">${esc(t('dx-up-ready'))}</span>`;
            return (
                `<div class="dx-file"><div class="dx-file-ic">${esc(ext(f.name))}</div>` +
                `<div class="dx-file-c"><b>${esc(f.name)}</b><span>${(f.file.size / 1048576).toFixed(1)} MB</span></div>` +
                st +
                `<button class="btn small" data-iv-rm="${i}" title="${esc(t('dx-up-replace'))}">✕</button></div>`
            );
        })
        .join('');
    return (
        `<div class="dx-queue">${rows}</div>` +
        `<div class="dx-bar"><div class="dx-note">${esc(t('dxi-side-flow1'))}</div>` +
        '<div style="display:flex;gap:8px">' +
        `<button class="btn" id="dx-inv-add">${esc(t('dxi-up-pick'))}</button>` +
        `<button class="btn primary" id="dx-inv-start"${IV.busy ? ' disabled' : ''}>${esc(t('dx-up-start'))}</button></div></div>`
    );
}
function sideHtml() {
    const tips = [t('dxi-side-flow1'), t('dxi-side-flow2'), t('dxi-side-flow3')];
    return (
        '<div class="dx-side"><div class="dx-side-box">' +
        `<b>${esc(t('dx-side-cur'))}</b><ul>${tips.map((x) => `<li>${esc(x)}</li>`).join('')}</ul></div>` +
        `<div class="dx-side-box"><b>${esc(t('dx-side-rule'))}</b><p>${esc(t('dxi-side-flow3'))}</p></div></div>`
    );
}
function addFiles(list: FileList | null | undefined) {
    if (!list || !list.length) return;
    const maxF = w.getMaxFiles?.() || 500;
    for (const f of Array.from(list)) {
        if (!SUPPORTED.test(f.name)) continue;
        if (IV.files.length >= maxF) break;
        IV.files.push({ file: f, name: f.name, status: 'waiting' });
    }
    renderInvoiceUpload();
}

// ── 步骤 2:识别(顺序 · 复用 /api/ocr/recognize)─────────────
async function startRecognize() {
    const waiting = IV.files.filter((f) => f.status === 'waiting');
    if (!waiting.length || IV.busy) return;
    IV.busy = true;
    renderProcessing(0, waiting.length);
    showStepInv(2, 'dx-s-searching');
    let done = 0;
    for (const f of waiting) {
        f.status = 'processing';
        try {
            const form = new FormData();
            form.append('file', f.file, f.name);
            const r = await fetch('/api/ocr/recognize', {
                method: 'POST',
                headers: authHeaders(),
                body: form,
            });
            const d = (await r.json().catch(() => ({}))) as Dict;
            if (!r.ok) {
                const detail = (d.detail as { code?: string } | string) || 'unknown';
                const code = typeof detail === 'string' ? detail : detail.code || 'unknown';
                f.status = 'error';
                f.errorKey = 'err.' + code;
            } else {
                f.status = 'success';
                IV.results.push(ingestResult(d));
            }
        } catch {
            f.status = 'error';
            f.errorKey = 'dxi-recognize-fail';
        }
        done++;
        renderProcessing(done, waiting.length);
    }
    IV.busy = false;
    if (!IV.results.length) {
        showToast(t('dxi-rev-empty'), 'error');
        renderInvoiceUpload();
        return showStepInv(1, 'dx-s-upload');
    }
    IV.sel = 0;
    renderReview();
}
function ingestResult(d: Dict): IvResult {
    const pages = (d.pages as unknown[]) || [];
    const merged = w.mergeFields ? w.mergeFields(pages) : (pages[0] as Dict) || {};
    const hids = (d.history_ids as string[]) || (d.history_id ? [d.history_id as string] : []);
    return {
        filename: (d.filename as string) || '',
        pages,
        merged: merged || {},
        history_ids: hids,
        invoice_count: (d.invoice_count as number) || 1,
        confidence:
            (d.confidence as string) ||
            (((merged?.items as unknown[]) || []).length ? 'high' : 'low'),
    };
}
function renderProcessing(done: number, total: number) {
    const el = $('dx-s-searching');
    if (!el) return;
    const pct = total ? Math.round((done / total) * 100) : 0;
    el.innerHTML =
        '<div class="dx-searching"><div class="dx-spin"></div>' +
        `<h3>${esc(t('dxi-proc-title'))}</h3><p>${esc(t('dxi-proc-sub'))}</p>` +
        `<div class="dx-schips"><span class="dx-schip">${done}/${total} · ${pct}%</span></div></div>`;
}

// ── 步骤 3:复核 ─────────────────────────────────────────────
export function warnFields(merged: Dict): Set<string> {
    const s = new Set<string>();
    ['invoice_number', 'seller_tax', 'total_amount'].forEach((k) => {
        if (!String(merged[k] || '').trim()) s.add(k);
    });
    return s;
}
export function renderReview() {
    IV.view = 'review';
    const el = $('dx-s-inv-review');
    if (!el) return;
    const rows = IV.results
        .map((r, i) => {
            const sel = i === IV.sel ? ' sel' : '';
            const warns = warnFields(r.merged);
            const status =
                warns.size > 0
                    ? `<b style="color:var(--dx-amber)">${esc(t('dxi-rev-need').replace('{n}', String(warns.size)))}</b>`
                    : `<b style="color:var(--dx-green)">${esc(t('dxi-rev-ok'))}</b>`;
            const sub =
                r.invoice_count > 1
                    ? r.invoice_count + ' ' + esc(t('dxi-sum-files'))
                    : esc(t(warns.size ? 'dxi-rev-only' : 'dxi-rev-noneed'));
            return (
                `<div class="dx-frow${sel}" data-iv-sel="${i}"><div class="dx-file-ic">${esc(ext(r.filename))}</div>` +
                `<div class="dx-file-c"><b>${esc(r.filename)}</b><span>${sub}</span></div>` +
                `<div class="dx-fstatus">${status}</div>` +
                `<button class="btn small" data-iv-sel="${i}">${esc(t('dxi-rev-view'))}</button></div>`
            );
        })
        .join('');
    el.innerHTML = `<div class="dx-queue">${rows}</div>` + previewHtml() + reviewFootHtml();
    showStepInv(3, 'dx-s-inv-review');
}
function previewHtml() {
    const r = IV.results[IV.sel];
    if (!r) return '';
    const warns = warnFields(r.merged);
    const fields = IV.showAll ? REV_CORE.concat(REV_MORE) : REV_CORE;
    const cells = fields
        .map(([k, lk]) => {
            const warn = warns.has(k) ? ' warn' : '';
            const v = String(r.merged[k] ?? '');
            return (
                `<div class="dx-rv${warn}"><label>${esc(t(lk))}</label>` +
                `<input class="dx-rv-in" data-iv-field="${esc(k)}" value="${esc(v)}"></div>`
            );
        })
        .join('');
    return (
        '<div class="dx-review-card"><div class="dx-review-h">' +
        `<b>${esc(r.filename)} · ${esc(t('dxi-rev-h'))}</b>` +
        `<button class="dx-toggle" id="dx-inv-toggle">${esc(t(IV.showAll ? 'dxi-rev-toggle-less' : 'dxi-rev-toggle-all'))}</button></div>` +
        `<div class="dx-review-grid">${cells}</div></div>`
    );
}
function reviewFootHtml() {
    return (
        `<div class="dx-foot"><div class="dx-note">${esc(t('dxi-rev-hint'))}</div>` +
        '<div style="display:flex;gap:8px">' +
        `<button class="btn" id="dx-inv-rev-back">${esc(t('dxi-rev-back'))}</button>` +
        `<button class="btn primary" id="dx-inv-rev-next">${esc(t('dxi-rev-next'))}</button></div></div>`
    );
}

// ── 事件入口(由 dms-intake.ts 单一委托转发)──────────────────
export function onInvoiceClick(tg: HTMLElement): boolean {
    const hit = (id: string) => tg.closest('#' + id);
    if (
        hit('dx-inv-pick') ||
        hit('dx-inv-add') ||
        (tg.closest('#dx-inv-drop') && !tg.closest('button'))
    )
        return (click('dx-inv-file'), true);
    if (hit('dx-inv-camera')) return (click('dx-inv-cam'), true);
    if (hit('dx-inv-gallery')) return (click('dx-inv-gal'), true);
    const rm = tg.closest('[data-iv-rm]') as HTMLElement | null;
    if (rm) {
        IV.files.splice(+rm.dataset.ivRm!, 1);
        renderInvoiceUpload();
        return true;
    }
    if (hit('dx-inv-start')) return (void startRecognize(), true);
    const sel = tg.closest('[data-iv-sel]') as HTMLElement | null;
    if (sel) {
        IV.sel = +sel.dataset.ivSel!;
        renderReview();
        return true;
    }
    if (hit('dx-inv-toggle')) {
        IV.showAll = !IV.showAll;
        renderReview();
        return true;
    }
    if (hit('dx-inv-rev-back')) {
        renderInvoiceUpload();
        showStepInv(1, 'dx-s-upload');
        return true;
    }
    if (hit('dx-inv-rev-next')) return (void enterSubmit(), true);
    const out = tg.closest('[data-iv-out]') as HTMLElement | null;
    if (out) {
        const k = out.dataset.ivOut as 'excel' | 'erp';
        IV.output[k] = !IV.output[k];
        if (!IV.output.excel && !IV.output.erp) IV.output[k] = true;
        renderSubmit();
        return true;
    }
    const erp = tg.closest('[data-iv-erp]') as HTMLElement | null;
    if (erp) {
        IV.target = erp.dataset.ivErp!;
        renderSubmit();
        return true;
    }
    if (hit('dx-inv-go-int')) return (go('integration'), true);
    if (hit('dx-inv-sub-back')) {
        renderReview();
        return true;
    }
    if (hit('dx-inv-finish')) return (void doFinish(), true);
    if (hit('dx-inv-view-rec')) return (go('history'), true);
    if (hit('dx-inv-view-push')) return (go('integration'), true);
    if (hit('dx-inv-new')) {
        resetInvoice();
        renderInvoiceUpload();
        showStepInv(1, 'dx-s-upload');
        return true;
    }
    return false;
}
export function onInvoiceChange(tg: HTMLElement): boolean {
    const id = (tg as HTMLInputElement).id;
    if (id === 'dx-inv-file' || id === 'dx-inv-cam' || id === 'dx-inv-gal') {
        addFiles((tg as HTMLInputElement).files);
        (tg as HTMLInputElement).value = '';
        return true;
    }
    if (id === 'dx-inv-tpl') {
        IV.tpl = (tg as HTMLSelectElement).value;
        return true;
    }
    const fk = tg.getAttribute('data-iv-field');
    if (fk) {
        const r = IV.results[IV.sel];
        if (r) r.merged[fk] = (tg as HTMLInputElement).value;
        return true;
    }
    return false;
}
export function onInvoiceDrop(files: FileList | null | undefined): boolean {
    addFiles(files);
    return true;
}
function click(id: string) {
    ($(id) as HTMLInputElement | null)?.click();
}
export function go(route: string) {
    if (typeof w.routeTo === 'function') w.routeTo(route);
}
