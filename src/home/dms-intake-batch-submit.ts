// ============================================================
// 录入工作台 · 汇总表批量建单 · 步骤4 提交 + 推送 ERP
// 硬阻断行后端已跳过(skipped);建成的写入 ocr_history(记账料·可推 ERP),不建账本/发票草稿。
// 建单后就地选目标账套推 ERP —— 推送逻辑复用发票任务的共享单元(dms-intake-erp-push)。
// ============================================================
import { esc, $, showStep } from './dms-intake-core.js';
import { B, wsHeaders } from './dms-intake-batch.js';
import {
    fetchErpEndpoints,
    pickDefaultTarget,
    erpTargetCardsHtml,
    pushHistory,
    type ErpEndpoint,
} from './dms-intake-erp-push.js';

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
interface CommitData {
    results: RowResult[];
    created: number;
    failed: number;
    skipped: number;
    total: number;
}

let _data: CommitData | null = null;
let _endpoints: ErpEndpoint[] = [];
let _target = '';
let _pushing = false;
let _pushed: { ok: number; fail: number } | null = null;

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
        '</div>'
    );
}

// 推送面板:无可建行不显;已推显结果;无端点走空态;否则目标卡 + 执行推送。
function pushPanelHtml(): string {
    if (!createdIds().length) return '';
    let body: string;
    if (_pushed) {
        body = pushResultHtml(_pushed);
    } else if (!_endpoints.filter((e) => e.enabled !== false).length) {
        body =
            '<div class="dx-erp-empty">' +
            `<h4>${esc(t('dxi-erp-empty-t'))}</h4><p>${esc(t('dxi-erp-empty-d'))}</p>` +
            `<button class="btn" id="dxb-go-int">${esc(t('dxi-erp-empty-btn'))}</button></div>`;
    } else {
        body =
            erpTargetCardsHtml(_endpoints, _target) +
            '<div class="dx-foot" style="margin-top:12px"><div class="dx-note"></div>' +
            `<button class="btn primary" id="dxb-push-go"${_pushing ? ' disabled' : ''}>` +
            `${esc(t(_pushing ? 'dxb-pushing' : 'dxb-push-go'))}</button></div>`;
    }
    return (
        '<div class="dx-panel" style="margin-top:12px"><div class="dx-panel-h">' +
        `<b>${esc(t('dxb-out-h'))}</b><span>${esc(t('dxb-out-s'))}</span></div>${body}</div>`
    );
}

function pushResultHtml(p: { ok: number; fail: number }): string {
    return (
        '<div class="dxb-stats">' +
        `<div class="dxb-stat green"><b>${p.ok}</b><span>${esc(t('dxb-push-ok'))}</span></div>` +
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
        _endpoints = createdIds().length ? await fetchErpEndpoints() : [];
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
    _pushing = true;
    render();
    let ok = 0;
    let fail = 0;
    for (const id of ids) {
        (await pushHistory(id, _target)) ? ok++ : fail++;
    }
    _pushing = false;
    _pushed = { ok, fail };
    render();
    showToast(
        fail === 0 ? t('dxb-push-ok-toast') : t('dxb-push-partial-toast'),
        fail === 0 ? 'success' : 'warn'
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
        goRoute('integrations');
        return true;
    }
    if (tg.closest('#dxb-view-list')) {
        // 记账料落「识别记录」,从那里也能推 ERP(不建账本/发票单,故不去销项/采购列表)。
        goRoute('history');
        return true;
    }
    // dxb-restart 由 dms-intake 的 resetFlow 收口(在本处理器之前拦截)。
    return false;
}
