// ============================================================
// 录入工作台 · 汇总表批量建单 · 步骤4 提交 + 推送 ERP
// 硬阻断行后端已跳过(skipped);建成的写入 ocr_history 并当场转正式单据(intake_bridge)。
// 建单后就地选目标账套推 ERP —— 推送逻辑复用发票任务的共享单元(dms-intake-erp-push)。
// ============================================================
import { esc, $, showStep } from './dms-intake-core.js';
import { B, wsHeaders } from './dms-intake-batch.js';
import {
    fetchErpEndpoints,
    pickDefaultTarget,
    erpTargetCardsHtml,
    isErpAccountSelectionComplete,
    isErpTargetReady,
    pushHistory,
    selectedAccountKey,
    selectedCatalogEvidence,
    type ErpEndpoint,
} from './dms-intake-erp-push.js';
import { focusDxErpCards } from './dms-intake-erp-cards.js';
import {
    changeErpCatalogSelection,
    preOpenErpCatalog,
} from './dms-intake-erp-catalog-interaction.js';
import { CONVERT_REASON_KEY } from './dms-intake-review-convert.js';

function t(k: string): string {
    const w = window as unknown as { t?: (k: string) => string };
    return typeof w.t === 'function' ? w.t(k) : k;
}
function goRoute(name: string): void {
    const w = window as unknown as { routeTo?: (n: string) => void };
    if (typeof w.routeTo === 'function') w.routeTo(name);
}

interface RowResult {
    row_index: number;
    status: 'created' | 'failed' | 'skipped';
    ocr_history_id?: string;
    error?: string;
    warnings?: string[];
}
interface DocSkip {
    history_id: string;
    reason: string;
}
interface CommitData {
    results: RowResult[];
    created: number;
    failed: number;
    skipped: number;
    total: number;
    // 建成的记账料当场转正式单据(intake_bridge · 同一批 commit 内完成,不必再点别的按钮)。
    documents_booked: number;
    // 记账料建成但没能转正式单据的明细(intake_bridge convert_histories 的 skipped·
    // reason 见 dms-intake-review.ts 的 CONVERT_REASON_KEY)。此前只有 documents_booked
    // 一个汇总数,这批为什么没全转成正式单据无从查——四态里少了"部分失败"这一态。
    document_skipped: DocSkip[];
}

// duplicate/already_converted 不进 CONVERT_REASON_KEY(dms-intake-review.ts 里走
// convertChipHtml 的专属徽章分支),这里的分组同样单独归一桶,其余走那张表、查不到落
// 通用错误桶——与 convertChipHtml 同一套映射,不重开一套口径。
const DOC_SKIP_DUP_REASONS = new Set(['duplicate', 'already_converted']);
function docSkipLabelKey(reason: string): string {
    if (DOC_SKIP_DUP_REASONS.has(reason)) return 'dxi-conv-dup';
    return CONVERT_REASON_KEY[reason] || 'dxi-conv-r-error';
}

function docSkipBreakdownHtml(skipped: DocSkip[]): string {
    if (!skipped.length) return '';
    const counts = new Map<string, number>();
    skipped.forEach((s) => {
        const key = docSkipLabelKey(s.reason);
        counts.set(key, (counts.get(key) || 0) + 1);
    });
    const chips = Array.from(counts.entries())
        .map(([key, n]) => `<span class="dx-badge amber">${esc(t(key))}×${n}</span>`)
        .join(' ');
    return `<div class="dx-note" style="margin-top:6px">${chips}</div>`;
}

// 「已入账 N · 跳过 M」:N/M 两个数字与顶部 documents_booked 统计卡同源,但这里紧挨着
// 跳过原因分组一起看,不用再去数 document_skipped 数组长度。
function docSummaryLineHtml(d: CommitData): string {
    const skipped = d.document_skipped || [];
    const line = t('dxb-doc-summary')
        .replace('{n}', String(d.documents_booked || 0))
        .replace('{m}', String(skipped.length));
    return `<div class="dx-note" style="margin-top:10px">${esc(line)}</div>${docSkipBreakdownHtml(skipped)}`;
}

let _data: CommitData | null = null;
let _endpoints: ErpEndpoint[] = [];
let _target = '';
let _pushing = false;
let _pushed: { ok: number; pending: number; fail: number } | null = null;

const STATUS_BADGE: Record<string, string> = {
    created: 'green',
    failed: 'red',
    skipped: 'blue',
};

// 建成行的 ocr_history_id(推送读源)· 失败/跳过行无 id 不参与推送。
function createdIds(): string[] {
    return (_data?.results || [])
        .filter((r) => r.status === 'created' && r.ocr_history_id)
        .map((r) => r.ocr_history_id as string);
}

function statHtml(d: CommitData): string {
    const chip = (n: number, label: string, cls: string) =>
        `<div class="dxb-stat ${cls}"><b>${n}</b><span>${esc(t(label))}</span></div>`;
    return (
        '<div class="dxb-stats">' +
        chip(d.created, 'dxb-st-created', 'green') +
        chip(d.failed, 'dxb-st-failed', 'red') +
        chip(d.skipped, 'dxb-st-skipped', 'blue') +
        chip(d.documents_booked || 0, 'dxb-st-booked', 'green') +
        '</div>'
    );
}

// 推送面板:无可建行不显;已推显结果;无端点走空态;否则目标卡 + 执行推送。
function pushPanelHtml(): string {
    if (!createdIds().length) return '';
    let body: string;
    if (_pushed) {
        body = pushResultHtml(_pushed);
    } else if (!_endpoints.length) {
        body =
            '<div class="dx-erp-empty">' +
            `<h4>${esc(t('dxi-erp-empty-t'))}</h4><p>${esc(t('dxi-erp-empty-d'))}</p>` +
            `<button class="btn" id="dxb-go-int">${esc(t('dxi-erp-empty-btn'))}</button></div>`;
    } else {
        const pushDisabled =
            _pushing || !_target || !isErpAccountSelectionComplete(_endpoints, _target);
        body =
            erpTargetCardsHtml(_endpoints, _target) +
            '<div class="dx-foot" style="margin-top:12px"><div class="dx-note"></div>' +
            `<button class="btn primary" id="dxb-push-go"${pushDisabled ? ' disabled' : ''}>` +
            `${esc(t(_pushing ? 'dxb-pushing' : 'dxb-push-go'))}</button></div>`;
    }
    return (
        '<div class="dx-panel" style="margin-top:12px"><div class="dx-panel-h">' +
        `<b>${esc(t('dxb-out-h'))}</b><span>${esc(t('dxb-out-s'))}</span></div>${body}</div>`
    );
}

function pushResultHtml(p: { ok: number; pending: number; fail: number }): string {
    return (
        '<div class="dxb-stats">' +
        `<div class="dxb-stat green"><b>${p.ok}</b><span>${esc(t('dxb-push-ok'))}</span></div>` +
        (p.pending
            ? `<div class="dxb-stat"><b>${p.pending}</b><span>${esc(t('erp-status-pending'))}</span></div>`
            : '') +
        (p.fail
            ? `<div class="dxb-stat red"><b>${p.fail}</b><span>${esc(t('dxb-push-fail'))}</span></div>`
            : '') +
        '</div>'
    );
}

function rowLine(r: RowResult): string {
    const cls = STATUS_BADGE[r.status] || 'blue';
    const label = t('dxb-st-' + r.status);
    const detail = r.error ? ` · ${esc(r.error)}` : '';
    return (
        '<div class="dxb-rline">' +
        `<span class="dxb-rno">#${esc(String((r.row_index ?? 0) + 1))}</span>` +
        `<span class="dx-badge ${cls}">${esc(label)}</span>` +
        `<span class="dxb-rdet">${detail}</span></div>`
    );
}

function render() {
    const el = $('dx-s-batch-submit');
    if (!el || !_data) return;
    const d = _data;
    el.innerHTML =
        `<div class="dx-rbanner"><div class="dx-rsym">✓</div><div class="dx-rc">` +
        `<b>${esc(t('dxb-done-t'))}</b><p>${esc(t('dxb-done-s'))}</p></div></div>` +
        statHtml(d) +
        docSummaryLineHtml(d) +
        pushPanelHtml() +
        `<div class="dxb-rlist">${d.results.map(rowLine).join('')}</div>` +
        '<div class="dx-actions" style="margin-top:14px">' +
        `<button class="btn" id="dxb-restart">${esc(t('dxb-restart'))}</button>` +
        `<button class="btn primary" id="dxb-view-list">${esc(t('dxb-view-list'))}</button></div>`;
}

export async function enterBatchSubmit() {
    if (B.busy || !B.parsed) return;
    B.busy = true;
    try {
        const r = await fetch('/api/summary-import/commit', {
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
            showToast(t('dxb-commit-fail'), 'error');
            return;
        }
        _data = d.data as CommitData;
        _pushed = null;
        _pushing = false;
        // 有可建行才拉端点(空批省一次请求)。目标保留上次选择(仍启用则不变)。
        _endpoints = createdIds().length ? await fetchErpEndpoints(false, _endpoints) : [];
        _target = pickDefaultTarget(_endpoints, _target);
        B.view = 'submit';
        render();
        showStep(4, 'dx-s-batch-submit');
    } catch {
        showToast(t('dxb-commit-fail'), 'error');
    } finally {
        B.busy = false;
    }
}

// 逐条推送本批建成记录(每条 ocr_history 一次·后端判方向入队 Express / 直写 MR.ERP)。
async function doPush(): Promise<void> {
    const ids = createdIds();
    if (_pushing || !ids.length || !_target) return;
    if (!isErpAccountSelectionComplete(_endpoints, _target)) {
        showToast(t('dxi-need-erp-account'), 'warn');
        render();
        return;
    }
    _endpoints = await fetchErpEndpoints(true, _endpoints);
    if (!isErpTargetReady(_endpoints, _target)) {
        _target = pickDefaultTarget(_endpoints, _target);
        render();
        showToast(t('dxi-need-erp'), 'warn');
        return;
    }
    if (!isErpAccountSelectionComplete(_endpoints, _target)) {
        render();
        showToast(t('dxi-need-erp-account'), 'warn');
        return;
    }
    _pushing = true;
    render();
    let ok = 0;
    let pending = 0;
    let fail = 0;
    for (const id of ids) {
        const outcome = await pushHistory(
            id,
            _target,
            undefined,
            selectedAccountKey(_endpoints, _target),
            selectedCatalogEvidence(_endpoints, _target)
        );
        if (outcome === 'success') ok++;
        else if (outcome === 'waiting') pending++;
        else fail++;
    }
    _pushing = false;
    _pushed = { ok, pending, fail };
    render();
    showToast(
        fail === 0 && pending === 0 ? t('dxb-push-ok-toast') : t('dxb-push-partial-toast'),
        fail === 0 && pending === 0 ? 'success' : 'warn'
    );
}

export function onBatchSubmitClick(tg: HTMLElement): boolean {
    const card = tg.closest('[data-erp-target]') as HTMLElement | null;
    if (card) {
        _target = card.getAttribute('data-erp-target') || '';
        render();
        return true;
    }
    if (tg.closest('#dxb-push-go')) {
        void doPush();
        return true;
    }
    if (tg.closest('#dxb-go-int')) {
        focusDxErpCards();
        return true;
    }
    if (tg.closest('#dxb-view-list')) {
        // 记账料落「识别记录」,从那里也能推 ERP;正式单据已当场转好(购销文档在各自列表页看)。
        goRoute('history');
        return true;
    }
    // dxb-restart 由 dms-intake 的 resetFlow 收口(在本处理器之前拦截)。
    return false;
}

export function onBatchErpCatalogPreOpen(tg: HTMLElement, source: 'pointer' | 'focus'): boolean {
    return preOpenErpCatalog({
        target: tg,
        endpoints: _endpoints,
        source,
        render,
        onFailure: (result) =>
            showToast(
                t(result === 'timeout' ? 'dx-erp-catalog-timeout' : 'dx-erp-catalog-load-failed'),
                'warn'
            ),
    });
}

export function onBatchSubmitChange(tg: HTMLElement): boolean {
    return changeErpCatalogSelection(tg, _endpoints, render);
}
