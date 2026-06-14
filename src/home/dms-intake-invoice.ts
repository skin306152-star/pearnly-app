// ============================================================
// 录入工作台 · 发票/收据任务 · 上传 + 识别(复用 /api/ocr/recognize 全套语义,不重写后端)
//   多发票拆分:一个 PDF 可能 N 张发票 → 后端 invoice_grouper 已拆,响应给 invoices[];
//   本流按 invoices[] 逐张展示/导出(不再 mergeFields 压成一张)。
//   去重(name+size)/6 路并发/client_id 归属/needs_review·重复·自动推送 透出。
//   复核/导出/结果在 dms-intake-invoice-submit.ts(控行数)。
// ============================================================
/* global t, token, showToast */
import { S, esc, $, authHeaders } from './dms-intake-core.js';
import { enterSubmit, renderSubmit, renderReview, doFinish } from './dms-intake-invoice-submit.js';

export type Dict = Record<string, unknown>;
export interface IvFile {
    file: File;
    name: string;
    size: number;
    status: 'waiting' | 'processing' | 'success' | 'error';
    errorKey?: string;
}
// 一张发票(后端 invoices[] 的一项)· 多页跨页发票已由后端合并为一张
export interface IvInvoice {
    fields: Dict;
    history_id: string | null;
    idx: number; // 1-based 在本文件内第几张
    total: number; // 本文件共几张
}
export interface IvResult {
    filename: string;
    invoices: IvInvoice[];
    history_ids: string[];
    invoice_count: number;
    needs_review: boolean; // 后端 missed_invoice_warnings 非空 = 可能漏票需人工核对
    from_cache: boolean;
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
    sel: 0, // 复核中选中的文件下标
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
    getCurrentClientId?: () => unknown;
    mergeFields?: (pages: unknown) => Dict;
    routeTo?: (r: string) => void;
};

// 触屏设备才显示「拍照/相册」· 桌面端走「选择文件」支持所有格式(拍照/相册是图片专用入口)
const TOUCH =
    (typeof navigator !== 'undefined' && (navigator.maxTouchPoints || 0) > 0) ||
    'ontouchstart' in window;

const UPLOAD_ACCEPT =
    '.pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.bmp,.gif,.xlsx,.xls,.xlsm,.csv,.tsv,.docx,.doc,.txt';
const SUPPORTED = /\.(pdf|png|jpe?g|webp|tiff?|bmp|gif|xlsx?|xlsm|csv|tsv|docx?|txt)$/i;

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
    const camBtns = TOUCH
        ? `<button class="btn" id="dx-inv-camera">${esc(t('dxi-up-camera'))}</button>` +
          `<button class="btn" id="dx-inv-gallery">${esc(t('dxi-up-gallery'))}</button>`
        : '';
    return (
        '<div class="dx-drop" id="dx-inv-drop"><div>' +
        '<div class="dx-drop-g">↑</div>' +
        `<h3>${esc(t('dxi-up-title'))}</h3><p>${esc(t('dxi-up-hint'))}</p>` +
        '<div class="dx-up-btns">' +
        `<button class="btn primary" id="dx-inv-pick">${esc(t('dxi-up-pick'))}</button>` +
        camBtns +
        '</div>' +
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
                      : f.status === 'processing'
                        ? `<span class="dx-badge blue">…</span>`
                        : `<span class="dx-badge blue">${esc(t('dx-up-ready'))}</span>`;
            return (
                `<div class="dx-qrow"><div class="dx-file-ic">${esc(ext(f.name))}</div>` +
                `<div class="dx-file-c"><b>${esc(f.name)}</b><span>${(f.size / 1048576).toFixed(1)} MB</span></div>` +
                st +
                `<button class="dx-qx" data-iv-rm="${i}" title="${esc(t('dx-up-replace'))}">✕</button></div>`
            );
        })
        .join('');
    return (
        `<div class="dx-qlist">${rows}</div>` +
        `<div class="dx-bar"><div class="dx-note">${esc(t('dxi-side-flow1'))} · ${IV.files.length}</div>` +
        '<div style="display:flex;gap:8px">' +
        `<button class="btn" id="dx-inv-add">${esc(t('dxi-up-pick'))}</button>` +
        `<button class="btn primary" id="dx-inv-start"${IV.busy ? ' disabled' : ''}>${esc(t('btn-start'))}</button></div></div>`
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
    // 去重(name+size)· 防同一文件重复入队(用户多次选/拖同一文件)
    const seen = new Set(IV.files.map((f) => f.name + '_' + f.size));
    for (const f of Array.from(list)) {
        if (!SUPPORTED.test(f.name)) continue;
        const key = f.name + '_' + f.size;
        if (seen.has(key)) continue;
        if (IV.files.length >= maxF) break;
        seen.add(key);
        IV.files.push({ file: f, name: f.name, size: f.size, status: 'waiting' });
    }
    renderInvoiceUpload();
}

// ── 步骤 2:识别(6 路并发 · client_id 归属 · 多发票/警告透出)──
async function startRecognize() {
    const waiting = IV.files.filter((f) => f.status === 'waiting');
    if (!waiting.length || IV.busy) return;
    IV.busy = true;
    const total = waiting.length;
    let done = 0;
    renderProcessing(0, total);
    showStepInv(2, 'dx-s-searching');
    const cid = typeof w.getCurrentClientId === 'function' ? w.getCurrentClientId() : null;
    const queue = waiting.slice();
    const dupWarn: unknown[] = [];
    let autoPushed = 0;
    async function worker() {
        while (queue.length) {
            const f = queue.shift()!;
            f.status = 'processing';
            try {
                const form = new FormData();
                form.append('file', f.file, f.name);
                if (cid != null) form.append('client_id', String(cid));
                const r = await fetch('/api/ocr/recognize', {
                    method: 'POST',
                    headers: authHeaders(),
                    body: form,
                });
                const d = (await r.json().catch(() => ({}))) as Dict;
                if (!r.ok) {
                    const detail = (d.detail as { code?: string } | string) || 'unknown';
                    f.status = 'error';
                    f.errorKey =
                        'err.' + (typeof detail === 'string' ? detail : detail.code || 'unknown');
                } else {
                    f.status = 'success';
                    IV.results.push(ingestResult(d));
                    if (((d.duplicate_warnings as unknown[]) || []).length)
                        dupWarn.push(...(d.duplicate_warnings as unknown[]));
                    if (d.auto_pushed) autoPushed++;
                }
            } catch {
                f.status = 'error';
                f.errorKey = 'dxi-recognize-fail';
            }
            done++;
            renderProcessing(done, total);
        }
    }
    const PAR = Math.min(6, total);
    await Promise.all(Array.from({ length: PAR }, () => worker()));
    IV.busy = false;
    const failN = waiting.filter((f) => f.status === 'error').length;
    if (dupWarn.length) showToast(t('dxi-dup-warn').replace('{n}', String(dupWarn.length)), 'warn');
    if (autoPushed) showToast(t('dxi-auto-pushed').replace('{n}', String(autoPushed)), 'success');
    if (!IV.results.length) {
        showToast(t('dxi-rev-empty'), 'error');
        renderInvoiceUpload();
        return showStepInv(1, 'dx-s-upload');
    }
    if (failN)
        showToast(
            t('dxi-batch-fail')
                .replace('{ok}', String(IV.results.length))
                .replace('{fail}', String(failN)),
            'warn'
        );
    IV.sel = 0;
    renderReview();
}
function ingestResult(d: Dict): IvResult {
    const pages = (d.pages as unknown[]) || [];
    const raw = (d.invoices as Array<Record<string, unknown>>) || [];
    const invoices: IvInvoice[] = raw.length
        ? raw.map((x, i) => ({
              fields: (x.fields as Dict) || {},
              history_id: (x.history_id as string) || null,
              idx: (x.source_index as number) || i + 1,
              total: (x.source_total as number) || raw.length,
          }))
        : [
              {
                  fields: w.mergeFields ? w.mergeFields(pages) : (pages[0] as Dict) || {},
                  history_id: (d.history_id as string) || null,
                  idx: 1,
                  total: 1,
              },
          ];
    return {
        filename: (d.filename as string) || '',
        invoices,
        history_ids: (d.history_ids as string[]) || (d.history_id ? [d.history_id as string] : []),
        invoice_count: (d.invoice_count as number) || invoices.length,
        needs_review:
            !!d.needs_review || ((d.missed_invoice_warnings as unknown[]) || []).length > 0,
        from_cache: !!d.from_cache,
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
    if (hit('dx-inv-sub-back')) return (renderReview(), true);
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
    // 复核字段编辑:data-iv-field="fileIdx:invIdx:key"
    const fk = tg.getAttribute('data-iv-field');
    if (fk) {
        const [fi, ii, key] = fk.split(':');
        const inv = IV.results[+fi]?.invoices[+ii];
        if (inv) inv.fields[key] = (tg as HTMLInputElement).value;
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
