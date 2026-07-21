// ============================================================
// 录入工作台 · 步④结果页「本批推送状态」内嵌(数据互通 · 2026-07-21)
//
// 推完不必跳独立「推送日志」页:直接读 /api/erp/logs?history_ids=<本批> 的折叠状态,
// 逐单显示 成功 / 推送中 / 重试中 / 失败 + 失败原因 + 就地重推。Express 出站是异步
// (pending → 成功/失败),故有 pending 行时每 4s 轮询原地翻成 ✓/✗。
//
// 自包含:自己的重推(data-dxp-retry)+ 轮询,不接独立页那套 document 级全局委托
// (data-log-retry / 批量栏),避免跨页 ID 与选择态耦合。独立推送日志页原样不动。
// ============================================================
import { esc, authHeaders } from './dms-intake-core.js';

function t(k: string): string {
    const w = window as unknown as { t?: (k: string) => string };
    return typeof w.t === 'function' ? w.t(k) : k;
}
function toast(msg: string, kind: string): void {
    const w = window as unknown as { showToast?: (m: string, k: string) => void };
    if (typeof w.showToast === 'function') w.showToast(msg, kind);
}

export interface PushLog {
    id: string;
    history_id?: string;
    invoice_no?: string;
    status?: string;
    next_retry_at?: string | null;
    error_friendly?: Record<string, string> | null;
    error_msg?: string;
}

export type PushView = 'ok' | 'pending' | 'retrying' | 'failed';

// 后端折叠态 → 展示态(与推送日志页 erp-log-card 同口径:success/skipped_dup=成功;
// pending=推送中;failed 且仍在重试队列(next_retry_at)=重试中;failed 终态=失败可重推)。
export function pushView(log: PushLog): PushView {
    const s = log.status || '';
    if (s === 'success' || s === 'skipped_dup') return 'ok';
    if (s === 'failed') return log.next_retry_at ? 'retrying' : 'failed';
    return 'pending';
}

const VIEW_LABEL: Record<PushView, string> = {
    ok: 'erp-logs-filter-ok',
    pending: 'dx-push-pending',
    retrying: 'erp-logs-filter-retrying',
    failed: 'erp-logs-filter-fail',
};

function friendlyErr(log: PushLog): string {
    const ef = log.error_friendly;
    if (ef && typeof ef === 'object') {
        const w = window as unknown as { _currentLang?: string };
        const lang = w._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
        return ef[lang] || ef.en || ef.th || log.error_msg || '';
    }
    return log.error_msg || '';
}

// 纯函数(t 注入 · 可单测):一批 log → 逐单状态行 HTML。空批返回空串。
export function pushStatusListHtml(logs: PushLog[], tt: (k: string) => string): string {
    if (!logs.length) return '';
    const rows = logs
        .map((log) => {
            const v = pushView(log);
            const docno = log.invoice_no || (log.history_id || '').slice(0, 8) || '—';
            const err =
                v === 'failed' || v === 'retrying'
                    ? `<div class="dxp-err">${esc(friendlyErr(log))}</div>`
                    : '';
            const retry =
                v === 'failed'
                    ? `<button class="dxp-retry" data-dxp-retry="${esc(log.id)}">${esc(tt('erp-exc-retry'))}</button>`
                    : '';
            return (
                `<div class="dxp-row ${v}"><span class="dxp-dot"></span>` +
                `<div class="dxp-main"><div class="dxp-doc" title="${esc(docno)}">${esc(docno)}</div>${err}</div>` +
                `<span class="dxp-state">${esc(tt(VIEW_LABEL[v]))}</span>${retry}</div>`
            );
        })
        .join('');
    return `<div class="dxp-list">${rows}</div>`;
}

let _pollTimer: number | null = null;

async function fetchBatchLogs(ids: string[]): Promise<PushLog[]> {
    try {
        const q = new URLSearchParams({ history_ids: ids.join(','), limit: '200' });
        const r = await fetch(`/api/erp/logs?${q}`, { headers: authHeaders() });
        const d = (await r.json().catch(() => ({}))) as { items?: PushLog[] };
        return d.items || [];
    } catch {
        return [];
    }
}

function bindRetryOnce(container: HTMLElement): void {
    if (container.dataset.dxpBound === '1') return;
    container.dataset.dxpBound = '1';
    container.addEventListener('click', (e) => {
        const btn = (e.target as HTMLElement).closest('[data-dxp-retry]') as HTMLElement | null;
        if (btn) void retryOne(container, btn);
    });
}

async function retryOne(container: HTMLElement, btn: HTMLElement): Promise<void> {
    const logId = btn.dataset.dxpRetry || '';
    if (!logId) return;
    btn.setAttribute('disabled', '');
    let ok = false;
    try {
        const r = await fetch(`/api/erp/logs/${encodeURIComponent(logId)}/retry`, {
            method: 'POST',
            headers: authHeaders(),
        });
        const d = (await r.json().catch(() => ({}))) as { ok?: boolean };
        ok = r.ok && d.ok === true;
    } catch {
        ok = false;
    }
    toast(t(ok ? 'log-retry-ok' : 'log-retry-fail'), ok ? 'success' : 'error');
    const ids = (container.dataset.dxpIds || '').split(',').filter(Boolean);
    void renderBatchPushStatus(container, ids);
}

// 拉本批 → 渲染 → 绑就地重推(一次)→ 有 pending 则 4s 后再拉。
// container 离屏(结果页切走 / 新建下一批)即停轮询,防残留计时。
export async function renderBatchPushStatus(
    container: HTMLElement,
    historyIds: string[]
): Promise<void> {
    if (_pollTimer) {
        clearTimeout(_pollTimer);
        _pollTimer = null;
    }
    const ids = historyIds.filter(Boolean);
    if (!ids.length) {
        container.innerHTML = '';
        return;
    }
    container.classList.add('dxp');
    container.dataset.dxpIds = ids.join(',');
    bindRetryOnce(container);
    const logs = await fetchBatchLogs(ids);
    if (!container.isConnected) return;
    container.innerHTML =
        `<div class="dxp-h">${esc(t('dx-push-status-h'))}</div>` + pushStatusListHtml(logs, t);
    if (logs.some((l) => (l.status || '') === 'pending')) {
        _pollTimer = window.setTimeout(() => {
            if (container.isConnected) void renderBatchPushStatus(container, ids);
        }, 4000);
    }
}
