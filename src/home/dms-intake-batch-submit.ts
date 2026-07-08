// ============================================================
// 录入工作台 · 汇总表批量建单 · 步骤4 提交(调 /commit · 逐行结果如实展示)
// 硬阻断行后端已跳过(skipped);建成的既落账本草稿又写 ocr_history(可推 ERP)。失败行显错误码。
// ============================================================
import { esc, $, showStep } from './dms-intake-core.js';
import { B, wsHeaders } from './dms-intake-batch.js';

function t(k: string): string {
    const w = window as unknown as { t?: (k: string) => string };
    return typeof w.t === 'function' ? w.t(k) : k;
}

interface RowResult {
    row_index: number;
    status: 'created' | 'booked_no_push' | 'failed' | 'skipped';
    doc_id?: string;
    direction?: string;
    error?: string;
    warnings?: string[];
}
interface CommitData {
    results: RowResult[];
    created: number;
    booked_no_push: number;
    failed: number;
    skipped: number;
    total: number;
}

let _data: CommitData | null = null;

const STATUS_BADGE: Record<string, string> = {
    created: 'green',
    booked_no_push: 'amber',
    failed: 'red',
    skipped: 'blue',
};

function statHtml(d: CommitData): string {
    const chip = (n: number, label: string, cls: string) =>
        `<div class="dxb-stat ${cls}"><b>${n}</b><span>${esc(t(label))}</span></div>`;
    return (
        '<div class="dxb-stats">' +
        chip(d.created, 'dxb-st-created', 'green') +
        chip(d.booked_no_push, 'dxb-st-nopush', 'amber') +
        chip(d.failed, 'dxb-st-failed', 'red') +
        chip(d.skipped, 'dxb-st-skipped', 'blue') +
        '</div>'
    );
}

function rowLine(r: RowResult): string {
    const cls = STATUS_BADGE[r.status] || 'blue';
    const label = t('dxb-st-' + r.status.replace('booked_no_push', 'nopush'));
    const detail = r.error
        ? ` · ${esc(r.error)}`
        : r.doc_id
          ? ` · ${esc(r.doc_id.slice(0, 8))}`
          : '';
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
        B.view = 'submit';
        render();
        showStep(4, 'dx-s-batch-submit');
    } catch {
        showToast(t('dxb-commit-fail'), 'error');
    } finally {
        B.busy = false;
    }
}

export function onBatchSubmitClick(tg: HTMLElement): boolean {
    if (tg.closest('#dxb-view-list')) {
        // 销项批 → 销项列表;采购批 → 采购列表(与建单方向一致)。
        const route = B.constants.direction === 'sales' ? 'sales' : 'purchase';
        if (typeof window.routeTo === 'function') window.routeTo(route);
        return true;
    }
    if (tg.closest('#dxb-restart')) {
        // 重来一批:清状态回上传步(由 dms-intake 的 resetFlow 收口)。
        return false;
    }
    return false;
}
