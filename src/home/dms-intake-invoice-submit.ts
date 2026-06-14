// ============================================================
// 录入工作台 · 发票任务 复核(步骤3)+ 导出/推送/结果(步骤4)· 从 invoice.ts 拆出控行数
//   复核按 invoices[] 逐张展示(一个 PDF N 张 = N 组),透出 needs_review;
//   导出复用 /api/ocr/export·mrerp-xlsx-batch·reports/history/batch_export(多发票按 invoices 展平);
//   推送复用 /api/erp/push;端点读 /api/erp/endpoints(排除 mrerp_dms)。
// ============================================================
/* global t, showToast, currentLang */
import { esc, $, authHeaders } from './dms-intake-core.js';
import { IV, ext, showStepInv } from './dms-intake-invoice.js';
import type { Dict, Endpoint, IvInvoice } from './dms-intake-invoice.js';

// 复核预览字段(复用 OCR 抽屉字段标签键)· warn=低置信常需确认
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
function warnFields(f: Dict): Set<string> {
    const s = new Set<string>();
    ['invoice_number', 'seller_tax', 'total_amount'].forEach((k) => {
        if (!String(f[k] || '').trim()) s.add(k);
    });
    return s;
}

// ── 步骤 3:复核(逐文件 · 多发票逐张)──────────────────────────
export function renderReview() {
    IV.view = 'review';
    const el = $('dx-s-inv-review');
    if (!el) return;
    const anyReview = IV.results.some((r) => r.needs_review);
    const banner = anyReview
        ? `<div class="dx-recheck-banner">${esc(t('dxi-needs-review'))}</div>`
        : '';
    const rows = IV.results
        .map((r, i) => {
            const sel = i === IV.sel ? ' sel' : '';
            const warns = r.invoices.reduce((n, inv) => n + warnFields(inv.fields).size, 0);
            const status = r.needs_review
                ? `<b style="color:var(--dx-amber)">${esc(t('dxi-rev-recheck'))}</b>`
                : warns > 0
                  ? `<b style="color:var(--dx-amber)">${esc(t('dxi-rev-need').replace('{n}', String(warns)))}</b>`
                  : `<b style="color:var(--dx-green)">${esc(t('dxi-rev-ok'))}</b>`;
            const sub =
                (r.invoice_count > 1
                    ? esc(t('dxi-multi').replace('{n}', String(r.invoice_count)))
                    : esc(t(warns ? 'dxi-rev-only' : 'dxi-rev-noneed'))) +
                (r.from_cache ? ' · ' + esc(t('cache-hit-badge')) : '');
            return (
                `<div class="dx-frow${sel}" data-iv-sel="${i}"><div class="dx-file-ic">${esc(ext(r.filename))}</div>` +
                `<div class="dx-file-c"><b>${esc(r.filename)}</b><span>${sub}</span></div>` +
                `<div class="dx-fstatus">${status}</div>` +
                `<button class="btn small" data-iv-sel="${i}">${esc(t('dxi-rev-view'))}</button></div>`
            );
        })
        .join('');
    el.innerHTML =
        banner + `<div class="dx-queue">${rows}</div>` + previewHtml() + reviewFootHtml();
    showStepInv(3, 'dx-s-inv-review');
}
function previewHtml() {
    const r = IV.results[IV.sel];
    if (!r) return '';
    const fields = IV.showAll ? REV_CORE.concat(REV_MORE) : REV_CORE;
    // 每张发票一组(多发票 PDF → N 组,逐张可编辑)
    const groups = r.invoices.map((inv, ii) => invoiceGroupHtml(ii, inv, fields)).join('');
    return (
        '<div class="dx-review-card"><div class="dx-review-h">' +
        `<b>${esc(r.filename)} · ${esc(t('dxi-rev-h'))}</b>` +
        `<button class="dx-toggle" id="dx-inv-toggle">${esc(t(IV.showAll ? 'dxi-rev-toggle-less' : 'dxi-rev-toggle-all'))}</button></div>` +
        groups +
        '</div>'
    );
}
function invoiceGroupHtml(ii: number, inv: IvInvoice, fields: Array<[string, string]>) {
    const warns = warnFields(inv.fields);
    const head =
        inv.total > 1
            ? `<div class="dx-inv-head">${esc(t('dxi-inv-no').replace('{i}', String(inv.idx)).replace('{n}', String(inv.total)))}</div>`
            : '';
    const cells = fields
        .map(([k, lk]) => {
            const warn = warns.has(k) ? ' warn' : '';
            const v = String(inv.fields[k] ?? '');
            return (
                `<div class="dx-rv${warn}"><label>${esc(t(lk))}</label>` +
                `<input class="dx-rv-in" data-iv-field="${IV.sel}:${ii}:${esc(k)}" value="${esc(v)}"></div>`
            );
        })
        .join('');
    return head + `<div class="dx-review-grid">${cells}</div>`;
}
function reviewFootHtml() {
    return (
        `<div class="dx-foot"><div class="dx-note">${esc(t('dxi-rev-hint'))}</div>` +
        '<div style="display:flex;gap:8px">' +
        `<button class="btn" id="dx-inv-rev-back">${esc(t('dxi-rev-back'))}</button>` +
        `<button class="btn primary" id="dx-inv-rev-next">${esc(t('dxi-rev-next'))}</button></div></div>`
    );
}

// ── 步骤 4:导出 / 推送 ──────────────────────────────────────
export async function enterSubmit() {
    await loadEndpoints();
    renderSubmit();
}
async function loadEndpoints() {
    try {
        const r = await fetch('/api/erp/endpoints', { headers: authHeaders() });
        const d = (await r.json().catch(() => ({}))) as { items?: Endpoint[] };
        IV.endpoints = (d.items || []).filter(
            (e) => (e.adapter || '').toLowerCase() !== 'mrerp_dms'
        );
    } catch {
        const cached = ((window as unknown as { _erpEndpoints?: Endpoint[] })._erpEndpoints ||
            []) as Endpoint[];
        IV.endpoints = cached.filter((e) => (e.adapter || '').toLowerCase() !== 'mrerp_dms');
    }
    const enabled = IV.endpoints.filter((e) => e.enabled !== false);
    if (!IV.target || !enabled.some((e) => String(e.id) === IV.target)) {
        const def = enabled.find((e) => e.is_default) || enabled[0];
        IV.target = def ? String(def.id) : '';
    }
}
function targetName(): string {
    const e = IV.endpoints.find((x) => String(x.id) === IV.target);
    return e ? e.name || e.adapter || 'ERP' : t('dxi-target-export-only');
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
    const enabled = IV.endpoints.filter((e) => e.enabled !== false);
    if (!enabled.length) {
        return (
            '<div class="dx-erp-empty"><div class="dx-erp-empty-ic">⚙</div>' +
            `<h4>${esc(t('dxi-erp-empty-t'))}</h4><p>${esc(t('dxi-erp-empty-d'))}</p>` +
            `<button class="btn" id="dx-inv-go-int">${esc(t('dxi-erp-empty-btn'))}</button></div>`
        );
    }
    const cards = IV.endpoints
        .map((e) => {
            const dis = e.enabled === false;
            const on = !dis && String(e.id) === IV.target ? ' active' : '';
            const lg = (e.adapter || '').slice(0, 2).toUpperCase();
            const meta = dis
                ? t('dxi-erp-disabled')
                : (e.is_default ? t('dxi-erp-default') + ' · ' : '') + t('dxi-erp-enabled');
            return (
                `<div class="dx-erp${on}${dis ? ' dis' : ''}"${dis ? '' : ` data-iv-erp="${esc(e.id)}"`}>` +
                `<div class="dx-erp-lg">${esc(lg)}</div>` +
                `<div class="dx-erp-c"><b>${esc(e.name || e.adapter)}</b><span>${esc(meta)}</span></div>` +
                '<div class="dx-erp-chk">✓</div></div>'
            );
        })
        .join('');
    return `<div class="dx-erps">${cards}</div>`;
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
        item('dxi-sum-target', IV.output.erp ? targetName() : t('dxi-target-export-only')) +
        '</div></div>'
    );
}
function submitFootHtml() {
    return (
        `<div class="dx-foot"><div class="dx-note">${esc(t('dxi-submit-hint'))}</div>` +
        '<div style="display:flex;gap:8px">' +
        `<button class="btn" id="dx-inv-sub-back">${esc(t('dxi-submit-back'))}</button>` +
        `<button class="btn primary" id="dx-inv-finish"${IV.busy ? ' disabled' : ''}>${esc(t('dxi-submit-go'))}</button></div></div>`
    );
}

export async function doFinish() {
    if (IV.busy) return;
    if (!IV.output.excel && !IV.output.erp) return showToast(t('dxi-need-output'), 'warn');
    const enabled = IV.endpoints.filter((e) => e.enabled !== false);
    if (IV.output.erp && !enabled.length) return showToast(t('dxi-need-erp'), 'warn');
    IV.busy = true;
    renderSubmit();
    let excelOk = false;
    let erpOk = 0;
    let erpFail = 0;
    if (IV.output.excel) excelOk = await doExport();
    if (IV.output.erp) {
        for (const id of allHistoryIds()) {
            (await pushOne(id)) ? erpOk++ : erpFail++;
        }
    }
    IV.busy = false;
    renderResult(excelOk, erpOk, erpFail);
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
async function pushOne(historyId: string): Promise<boolean> {
    try {
        const body: Dict = { history_id: historyId };
        if (IV.target) body.endpoint_id = IV.target;
        const r = await fetch('/api/erp/push', {
            method: 'POST',
            headers: authHeaders(true),
            body: JSON.stringify(body),
        });
        const d = (await r.json().catch(() => ({}))) as { ok?: boolean };
        return r.ok && d.ok !== false;
    } catch {
        return false;
    }
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

function renderResult(excelOk: boolean, erpOk: number, erpFail: number) {
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
                  (erpFail ? ` · ✗${erpFail}` : ` · ✓${erpOk}`),
              erpFail === 0
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
