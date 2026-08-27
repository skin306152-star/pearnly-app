/* global t, showToast */
import { esc, authHeaders } from './dms-intake-core.js';
import { IV } from './dms-intake-invoice.js';
import type { IvInvoice, IvResult } from './dms-intake-invoice.js';
import { isErpEntry } from './erp-intake.js';

interface ConvertResult {
    status: 'converted' | 'skipped';
    reason?: string;
}

const convertStatus = new Map<string, ConvertResult>();

export function convertedHistoryIds(ids: string[]): string[] {
    return Array.from(
        new Set(
            ids.filter((id) => {
                const result = convertStatus.get(id);
                return result?.status === 'converted' || result?.reason === 'already_converted';
            })
        )
    );
}

function activeWorkspaceId(): number | null {
    const w = window as unknown as { getActiveWorkspaceClientId?: () => number | null };
    return typeof w.getActiveWorkspaceClientId === 'function'
        ? w.getActiveWorkspaceClientId()
        : null;
}

async function convertHistoryIds(ids: string[]): Promise<void> {
    const pending = Array.from(new Set(ids.filter((id) => id && !convertStatus.has(id))));
    if (!pending.length) return;
    const ws = activeWorkspaceId();
    if (!ws) {
        pending.forEach((id) =>
            convertStatus.set(id, { status: 'skipped', reason: 'no_workspace' })
        );
        return;
    }
    try {
        const response = await fetch('/api/ocr/convert-documents', {
            method: 'POST',
            headers: authHeaders(true),
            body: JSON.stringify({ history_ids: pending, workspace_client_id: ws }),
        });
        const result = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(String(response.status));
        (result.converted || []).forEach((row: { history_id: string }) =>
            convertStatus.set(row.history_id, { status: 'converted' })
        );
        (result.skipped || []).forEach((row: { history_id: string; reason: string }) =>
            convertStatus.set(row.history_id, { status: 'skipped', reason: row.reason })
        );
    } catch {
        pending.forEach((id) => convertStatus.set(id, { status: 'skipped', reason: 'error' }));
    }
}

export function confirmedIndices(): number[] {
    const indices: number[] = [];
    IV.results.forEach((_result, index) => {
        if (IV.confirmed.has(index)) indices.push(index);
    });
    return indices;
}

export function pagesForInvoice(result: IvResult, invoice: IvInvoice): unknown[] {
    const source = Array.isArray(result.pages) ? result.pages : [];
    const selected = invoice.pageIndices?.length
        ? invoice.pageIndices
              .map((number) => source[number - 1])
              .filter((page) => page !== undefined)
        : source;
    const pages = selected.map((page) =>
        page && typeof page === 'object' ? { ...(page as Record<string, unknown>) } : page
    );
    if (pages.length && pages[0] && typeof pages[0] === 'object') {
        (pages[0] as Record<string, unknown>).fields = invoice.fields;
    }
    return pages.length ? pages : [{ fields: invoice.fields }];
}

async function persistIndices(indices: number[]): Promise<boolean> {
    try {
        await Promise.all(
            indices.flatMap((index) =>
                (IV.results[index]?.invoices || [])
                    .filter((invoice) => invoice.history_id)
                    .map((invoice) =>
                        fetch(`/api/history/${encodeURIComponent(invoice.history_id as string)}`, {
                            method: 'PUT',
                            headers: authHeaders(true),
                            body: JSON.stringify({
                                pages: pagesForInvoice(IV.results[index], invoice),
                            }),
                        }).then((response) => {
                            if (!response.ok) throw new Error(String(response.status));
                        })
                    )
            )
        );
        return true;
    } catch {
        showToast(t('dxi-rev-save-fail'), 'error');
        return false;
    }
}

export async function confirmIndices(indices: number[]): Promise<boolean> {
    if (isErpEntry() && !(await persistIndices(indices))) return false;
    const ids = indices.flatMap((index) => IV.results[index]?.history_ids || []);
    if (!ids.length) return false;
    if (isErpEntry()) {
        ids.forEach((id) => {
            if (convertStatus.get(id)?.status !== 'converted') convertStatus.delete(id);
        });
    }
    await convertHistoryIds(ids);
    let ok = true;
    indices.forEach((index) => {
        const result = IV.results[index];
        if (!result) return;
        const converted = result.history_ids.filter(Boolean).every((id) => {
            const status = convertStatus.get(id);
            return status?.status === 'converted' || status?.reason === 'already_converted';
        });
        if (!isErpEntry() || converted) IV.confirmed.add(index);
        else ok = false;
    });
    return ok;
}

export const CONVERT_REASON_KEY: Record<string, string> = {
    no_items: 'dxi-conv-r-no-items',
    no_direction: 'dxi-conv-r-no-direction',
    no_workspace: 'dxi-conv-r-no-workspace',
    no_doc_no: 'dxi-conv-r-no-doc-no',
    no_date: 'dxi-conv-r-no-date',
    not_found: 'dxi-conv-r-error',
};

export function convertChipHtml(historyId: string | null): string {
    if (!historyId) return '';
    const status = convertStatus.get(historyId);
    if (!status) return '';
    if (status.status === 'converted')
        return `<span class="dx-badge green">${esc(t('dxi-conv-done'))}</span>`;
    if (status.reason === 'duplicate' || status.reason === 'already_converted')
        return `<span class="dx-badge blue">${esc(t('dxi-conv-dup'))}</span>`;
    const reason = CONVERT_REASON_KEY[status.reason || ''] || 'dxi-conv-r-error';
    return `<span class="dx-badge amber">${esc(t('dxi-conv-skip').replace('{reason}', t(reason)))}</span>`;
}
