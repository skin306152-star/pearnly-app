// ============================================================
// 录入工作台 · 发票任务 导出/推送/结果(步骤4)· 从 invoice.ts 拆出控行数
//   导出复用 /api/ocr/export·mrerp-xlsx-batch·reports/history/batch_export(多发票按 invoices 展平);
//   推送复用 /api/erp/push;端点读 /api/erp/endpoints(排除 mrerp_dms)。
//   复核(步骤3)在 dms-intake-review.ts。
// ============================================================
/* global t, showToast, currentLang */
import { esc, $, authHeaders } from './dms-intake-core.js';
import { IV, showStepInv } from './dms-intake-invoice.js';
import type { Dict, Endpoint } from './dms-intake-invoice.js';
import {
    erpTargetCardsHtml,
    fetchErpEndpoints,
    isErpAccountSelectionComplete,
    isErpTargetReady,
    pickDefaultTarget,
    pushHistory,
    selectedAccountKey,
    selectedAccountLabel,
    selectedCatalogEvidence,
} from './dms-intake-erp-push.js';
import { renderReview } from './dms-intake-review.js';
import {
    confirmIndices,
    confirmedIndices,
    convertedHistoryIds,
    pagesForInvoice,
} from './dms-intake-review-convert.js';
import { isErpEntry } from './erp-intake.js';

// ── 步骤 4:导出 / 推送 ──────────────────────────────────────
export async function enterSubmit() {
    if (!(await ensureErpFormalConfirmation())) return;
    await loadEndpoints();
    renderSubmit();
}

async function ensureErpFormalConfirmation(): Promise<boolean> {
    if (!isErpEntry()) return true;
    const confirmed = confirmedIndices();
    if (!IV.results.length || confirmed.length !== IV.results.length) {
        returnToReviewForConfirmation();
        return false;
    }
    const converted = await confirmIndices(confirmed);
    const ids = Array.from(new Set(allHistoryIds().filter(Boolean)));
    if (!converted || convertedHistoryIds(ids).length !== ids.length) {
        returnToReviewForConfirmation();
        return false;
    }
    return true;
}

function returnToReviewForConfirmation(): void {
    renderReview();
    showToast(t('dxi-erp-confirm-required'), 'error');
}
async function loadEndpoints() {
    IV.endpoints = (await fetchErpEndpoints(false, IV.endpoints)) as Endpoint[];
    IV.target = pickDefaultTarget(IV.endpoints, IV.target);
}
function targetName(): string {
    const e = IV.endpoints.find((x) => String(x.id) === IV.target);
    if (!e) return t('dxi-target-export-only');
    const account = selectedAccountLabel(IV.endpoints, IV.target);
    return [e.name || e.adapter || 'ERP', account].filter(Boolean).join(' · ');
}
function totalInvoices(): number {
    return IV.results.reduce((n, r) => n + (r.invoice_count || 1), 0);
}

export function renderSubmit() {
    IV.view = 'submit';
    const el = $('dx-s-inv-submit');
    if (!el) return;
    el.innerHTML =
        '<div class="dx-panel"><div class="dx-panel-h">' +
        `<b>${esc(t('dxi-out-h'))}</b><span>${esc(t('dxi-out-s'))}</span></div>` +
        '<div class="dx-ogrid">' +
        outChoice('excel', 'dxi-out-excel-t', 'dxi-out-excel-d') +
        outChoice('erp', 'dxi-out-erp-t', 'dxi-out-erp-d') +
        '</div>' +
        (IV.output.excel ? tplRowHtml() : '') +
        (IV.output.erp ? erpTargetsHtml() : '') +
        '</div>' +
        summaryHtml() +
        submitFootHtml();
    showStepInv(4, 'dx-s-inv-submit');
}
function outChoice(key: 'excel' | 'erp', tk: string, dk: string) {
    const on = IV.output[key] ? ' active' : '';
    return (
        `<div class="dx-choice${on}" data-iv-out="${key}"><b>${esc(t(tk))}` +
        `<span class="dx-choice-chk">✓</span></b><p>${esc(t(dk))}</p></div>`
    );
}
function tplRowHtml() {
    const opts: Array<[string, string]> = [
        ['input_vat', 'dxi-tpl-input_vat'],
        ['standard', 'dxi-tpl-standard'],
        ['sales_detail_th', 'dxi-tpl-sales'],
        ['print', 'dxi-tpl-print'],
        ['mrerp', 'dxi-tpl-mrerp'],
    ];
    const body = opts
        .map(
            ([v, lk]) =>
                `<option value="${v}"${v === IV.tpl ? ' selected' : ''}>${esc(t(lk))}</option>`
        )
        .join('');
    return (
        `<div class="dx-tpl-row"><label>${esc(t('dxi-tpl-label'))}</label>` +
        `<select class="dx-tpl-sel" id="dx-inv-tpl">${body}</select></div>`
    );
}
function erpTargetsHtml() {
    if (!IV.endpoints.length) {
        return (
            '<div class="dx-erp-empty"><div class="dx-erp-empty-ic">⚙</div>' +
            `<h4>${esc(t('dxi-erp-empty-t'))}</h4><p>${esc(t('dxi-erp-empty-d'))}</p>` +
            `<button class="btn" id="dx-inv-go-int">${esc(t('dxi-erp-empty-btn'))}</button></div>`
        );
    }
    return erpTargetCardsHtml(IV.endpoints, IV.target, 'data-iv-erp');
}
function summaryHtml() {
    const item = (lk: string, v: string) =>
        `<div class="dx-chip"><label>${esc(t(lk))}</label><strong>${esc(v)}</strong></div>`;
    return (
        '<div class="dx-panel" style="margin-top:11px"><div class="dx-panel-h">' +
        `<b>${esc(t('dxi-sum-h'))}</b></div><div class="dx-scan">` +
        item('dxi-sum-files', String(IV.results.length)) +
        item('dxi-sum-rows', String(totalInvoices())) +
        item('dxi-sum-confirm', '0') +
        item('dxi-sum-target', targetSummary()) +
        '</div></div>'
    );
}
// 目标系统四态:空选=仅入库(只落识别记录)/ 仅导出 / 推送目标 / 导出+推送。
function targetSummary(): string {
    const { excel, erp } = IV.output;
    if (excel && erp) return t('dxi-target-export-push');
    if (erp) return targetName();
    if (excel) return t('dxi-target-export-only');
    return t('dxi-target-staged-only');
}
function submitFootHtml() {
    // 空选 → 按钮=「完成」(仅落识别记录);选了导出/推送 → 「执行导出 / 推送」。两者都先落识别记录。
    const goKey = IV.output.excel || IV.output.erp ? 'dxi-submit-go' : 'dxi-submit-finish-only';
    const disabled =
        IV.busy || (IV.output.erp && !isErpAccountSelectionComplete(IV.endpoints, IV.target));
    return (
        `<div class="dx-foot"><div class="dx-note">${esc(t('dxi-submit-hint'))}</div>` +
        '<div style="display:flex;gap:8px">' +
        `<button class="btn" id="dx-inv-sub-back">${esc(t('dxi-submit-back'))}</button>` +
        `<button class="btn primary" id="dx-inv-finish"${disabled ? ' disabled' : ''}>${esc(t(goKey))}</button></div></div>`
    );
}

export async function doFinish() {
    if (IV.busy) return;
    if (IV.output.erp && !isErpAccountSelectionComplete(IV.endpoints, IV.target)) {
        showToast(t('dxi-need-erp-account'), 'warn');
        renderSubmit();
        return;
    }
    if (!(await ensureErpFormalConfirmation())) return;
    // 空选合法(= 仅完成入库);只在选了推送但无可用端点时拦。
    if (IV.output.erp) {
        IV.endpoints = (await fetchErpEndpoints(true, IV.endpoints)) as Endpoint[];
        if (!isErpTargetReady(IV.endpoints, IV.target)) {
            showToast(t('dxi-need-erp'), 'warn');
            renderSubmit();
            return;
        }
        if (!isErpAccountSelectionComplete(IV.endpoints, IV.target)) {
            showToast(t('dxi-need-erp-account'), 'warn');
            renderSubmit();
            return;
        }
    }
    IV.busy = true;
    renderSubmit();
    // 终态:① 先把复核面改过的字段(已实时写入 IV.results)全部写进各自记录 →
    // ② 再 commit 草稿→正式落识别记录。顺序不能反,否则落库的是识别时原值(治"改了不同步")。
    const saved = await persistAllEdits();
    if (isErpEntry() && !saved) {
        IV.busy = false;
        renderReview();
        return;
    }
    const committed = await commitStaged();
    if (isErpEntry() && !committed) {
        showToast(t('dxi-rev-save-fail'), 'error');
        IV.busy = false;
        renderReview();
        return;
    }
    let excelOk = false;
    let erpOk = 0;
    let erpFail = 0;
    let erpPending = 0;
    if (IV.output.excel) excelOk = await doExport();
    if (IV.output.erp && (!isErpEntry() || (saved && committed))) {
        const ids = allHistoryIds();
        const pushIds = isErpEntry() ? convertedHistoryIds(ids) : ids;
        erpFail += ids.length - pushIds.length;
        for (const id of pushIds) {
            const outcome = await pushOne(id);
            if (outcome === 'success') erpOk++;
            else if (outcome === 'waiting') erpPending++;
            else erpFail++;
        }
    } else if (IV.output.erp) {
        erpFail = allHistoryIds().length;
    }
    IV.busy = false;
    renderResult(excelOk, erpOk, erpFail, erpPending);
}
// 第4步落库前:把所有发票当前字段(复核面改后·已实时写入 IV.results)写进各自记录。
// 不依赖用户是否点过「保存修改」→ 用户看到什么改值,就一定落进识别记录(治"改了不同步")。
async function persistAllEdits(): Promise<boolean> {
    const puts: Promise<Response>[] = [];
    IV.results.forEach((r) => {
        r.invoices.forEach((inv) => {
            if (!inv.history_id) return;
            puts.push(
                fetch(`/api/history/${encodeURIComponent(inv.history_id)}`, {
                    method: 'PUT',
                    headers: authHeaders(true),
                    body: JSON.stringify({ pages: pagesForInvoice(r, inv) }),
                })
            );
        });
    });
    try {
        const responses = await Promise.all(puts);
        if (responses.some((r) => !r.ok)) {
            showToast(t('dxi-rev-save-fail'), 'error');
            return false;
        }
        return true;
    } catch {
        showToast(t('dxi-rev-save-fail'), 'error');
        return false;
    }
}

// 把本次草稿记录落进识别记录(staged→正式)。ERP 推送要求这一步返回成功。
async function commitStaged(): Promise<boolean> {
    const ids = allHistoryIds();
    if (!ids.length) return true;
    try {
        const r = await fetch('/api/ocr/commit', {
            method: 'POST',
            headers: authHeaders(true),
            body: JSON.stringify({ ids }),
        });
        if (!r.ok) return false;
        const d = (await r.json().catch(() => ({}))) as { committed?: unknown };
        return !isErpEntry() || typeof d.committed === 'number';
    } catch {
        return false;
    }
}
function allHistoryIds(): string[] {
    const ids: string[] = [];
    IV.results.forEach((r) => ids.push(...r.history_ids));
    return ids;
}
async function doExport(): Promise<boolean> {
    try {
        let resp: Response;
        let name = `pearnly-${IV.tpl}-${stamp()}.xlsx`;
        if (IV.tpl === 'sales_detail_th') {
            // 多发票按 invoices[] 逐张展平(一个 PDF N 张 = N 行)· 不再 mergeFields 压成一张
            const records: Array<{ filename: string; merged_fields: Dict }> = [];
            IV.results.forEach((r) => {
                r.invoices.forEach((inv) => {
                    records.push({
                        filename:
                            inv.total > 1 ? `${r.filename} #${inv.idx}/${inv.total}` : r.filename,
                        merged_fields: inv.fields,
                    });
                });
            });
            resp = await fetch('/api/ocr/export', {
                method: 'POST',
                headers: authHeaders(true),
                body: JSON.stringify({ records, lang: currentLang, template: 'sales_detail_th' }),
            });
        } else if (IV.tpl === 'mrerp') {
            const ids = allHistoryIds();
            if (!ids.length) return false;
            resp = await fetch('/api/erp/mrerp-xlsx-batch', {
                method: 'POST',
                headers: authHeaders(true),
                body: JSON.stringify({ history_ids: ids }),
            });
            name = `pearnly-mrerp-${stamp()}.xlsx`;
        } else {
            const ids = allHistoryIds();
            if (!ids.length) return false;
            resp = await fetch('/api/reports/history/batch_export', {
                method: 'POST',
                headers: authHeaders(true),
                body: JSON.stringify({
                    template: IV.tpl,
                    lang: currentLang,
                    history_ids: ids,
                    client_id: null,
                }),
            });
        }
        if (!resp.ok) {
            showToast(t('dxi-export-fail'), 'error');
            return false;
        }
        const blob = await resp.blob();
        downloadBlob(blob, resp.headers.get('X-Filename') || name);
        showToast(t('dxi-export-ok'), 'success');
        return true;
    } catch {
        showToast(t('dxi-export-fail'), 'error');
        return false;
    }
}
async function pushOne(historyId: string): Promise<import('./dms-intake-erp-push.js').PushOutcome> {
    return pushHistory(
        historyId,
        IV.target,
        IV.postingKind,
        selectedAccountKey(IV.endpoints, IV.target),
        selectedCatalogEvidence(IV.endpoints, IV.target)
    );
}
function downloadBlob(blob: Blob, name: string) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
function stamp() {
    return String(new Date().getTime());
}

function renderResult(excelOk: boolean, erpOk: number, erpFail: number, erpPending = 0) {
    IV.view = 'success';
    const el = $('dx-s-success');
    if (!el) return;
    const exLine = IV.output.excel
        ? sitem(
              'dxi-res-excel',
              excelOk
                  ? t('dxi-res-excel-ok').replace('{n}', String(totalInvoices()))
                  : t('dxi-export-fail'),
              excelOk
          )
        : sitem('dxi-res-excel', t('dxi-res-none'), null);
    const erpLine = IV.output.erp
        ? sitem(
              'dxi-res-erp',
              t('dxi-res-erp-ok').replace('{name}', targetName()) +
                  ` · ✓${erpOk}` +
                  (erpPending ? ` · ${t('erp-status-pending')} ${erpPending}` : '') +
                  (erpFail ? ` · ✗${erpFail}` : ''),
              erpFail === 0 && erpPending === 0
          )
        : sitem('dxi-res-erp', t('dxi-res-none'), null);
    el.innerHTML =
        '<div class="dx-success"><div class="dx-suc-ic">✓</div>' +
        `<h3>${esc(t('dxi-res-title'))}</h3><p>${esc(t('dxi-res-sub'))}</p>` +
        `<div class="dx-sgrid">${exLine}${erpLine}</div>` +
        '<div class="dx-sact">' +
        `<button class="btn" id="dx-inv-view-rec">${esc(t('dxi-res-view-record'))}</button>` +
        `<button class="btn" id="dx-inv-view-push">${esc(t('dxi-res-view-push'))}</button>` +
        `<button class="btn primary" id="dx-inv-new">${esc(t('dxi-res-new'))}</button></div></div>`;
    showStepInv(4, 'dx-s-success');
}
function sitem(lk: string, val: string, ok: boolean | null) {
    const cls = ok === null ? '' : ok ? ' ok' : ' fail';
    return `<div class="dx-sitem${cls}"><label>${esc(t(lk))}</label><strong>${esc(val)}</strong></div>`;
}
