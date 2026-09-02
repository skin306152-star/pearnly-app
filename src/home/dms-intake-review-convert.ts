/* global t */
import { esc, authHeaders } from './dms-intake-core.js';
import { IV } from './dms-intake-invoice.js';
import type { IvInvoice, IvResult } from './dms-intake-invoice.js';
import { isErpEntry } from './erp-intake.js';

interface ConvertResult {
    status: 'converted' | 'skipped';
    reason?: string;
}

interface ConversionState {
    resolved: string[];
    unresolved: string[];
}

const convertStatus = new Map<string, ConvertResult>();
let confirmationErrorCode = '';

const CONFIRM_ERROR_KEYS: Record<string, string> = {
    'history.date_unreadable': 'dxi-err-date-unreadable',
    'erp.workspace_mismatch': 'dxi-err-workspace-mismatch',
    'erp.formal_document_locked': 'dxi-err-formal-locked',
    'erp.formal_document_required': 'dxi-erp-confirm-required',
    'erp.declaration_required': 'dxi-item-type-required',
    formal_document_required: 'dxi-erp-confirm-required',
    item_name_required: 'dxi-item-name-required',
    item_qty_required: 'dxi-item-qty-required',
    posting_kind_required: 'dxi-item-type-required',
    no_items: 'dxi-conv-r-no-items',
    no_direction: 'dxi-conv-r-no-direction',
    no_workspace: 'dxi-conv-r-no-workspace',
    network_error: 'dxi-err-confirm-status',
    status_unavailable: 'dxi-err-confirm-status',
};

export function confirmationErrorMessage(): string {
    const code = confirmationErrorCode || 'status_unavailable';
    const key = CONFIRM_ERROR_KEYS[code];
    if (key) {
        const message = t(key);
        if (message !== key) return message;
    }
    const fallback = t('dxi-err-save-http').replace('{code}', code);
    return fallback === 'dxi-err-save-http' ? `${t('dxi-rev-save-fail')} (${code})` : fallback;
}

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

function responseErrorCode(payload: unknown, status: number): string {
    if (payload && typeof payload === 'object') {
        const detail = (payload as { detail?: unknown }).detail;
        if (typeof detail === 'string' && detail) return detail;
        if (detail && typeof detail === 'object') {
            const error = detail as { code?: unknown; histories?: unknown };
            const code = error.code;
            if (code === 'erp.declaration_required' && error.histories) {
                const reasons = Object.values(error.histories as Record<string, unknown>);
                const reason = reasons.find(
                    (value) => typeof value === 'string' && Boolean(CONFIRM_ERROR_KEYS[value])
                );
                if (typeof reason === 'string') return reason;
            }
            if (typeof code === 'string' && code) return code;
        }
    }
    return `http_${status}`;
}

async function conversionState(ids: string[]): Promise<ConversionState | null> {
    const unique = Array.from(new Set(ids.filter(Boolean)));
    if (!unique.length) return { resolved: [], unresolved: [] };
    const ws = activeWorkspaceId();
    if (!ws) {
        confirmationErrorCode = 'no_workspace';
        return null;
    }
    try {
        const response = await fetch('/api/ocr/convert-documents/status', {
            method: 'POST',
            headers: authHeaders(true),
            body: JSON.stringify({ history_ids: unique, workspace_client_id: ws }),
        });
        const payload = (await response.json().catch(() => ({}))) as {
            resolved?: unknown;
            unresolved?: unknown;
        };
        if (!response.ok) {
            confirmationErrorCode = responseErrorCode(payload, response.status);
            return null;
        }
        const resolved = Array.isArray(payload.resolved)
            ? payload.resolved.map(String).filter((id) => unique.includes(id))
            : [];
        const resolvedSet = new Set(resolved);
        const unresolved = Array.isArray(payload.unresolved)
            ? payload.unresolved.map(String).filter((id) => unique.includes(id))
            : unique.filter((id) => !resolvedSet.has(id));
        resolved.forEach((id) =>
            convertStatus.set(id, { status: 'skipped', reason: 'already_converted' })
        );
        return { resolved, unresolved };
    } catch {
        confirmationErrorCode = 'status_unavailable';
        return null;
    }
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
        const result = (await response.json().catch(() => ({}))) as {
            converted?: { history_id: string }[];
            skipped?: { history_id: string; reason: string }[];
        };
        if (!response.ok) {
            confirmationErrorCode = responseErrorCode(result, response.status);
            return;
        }
        (result.converted || []).forEach((row: { history_id: string }) =>
            convertStatus.set(row.history_id, { status: 'converted' })
        );
        (result.skipped || []).forEach((row: { history_id: string; reason: string }) => {
            convertStatus.set(row.history_id, { status: 'skipped', reason: row.reason });
            if (!confirmationErrorCode && row.reason) confirmationErrorCode = row.reason;
        });
    } catch {
        confirmationErrorCode = 'network_error';
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

async function persistIndices(indices: number[], pendingIds: Set<string>): Promise<boolean> {
    try {
        const responses = await Promise.all(
            indices.flatMap((index) =>
                (IV.results[index]?.invoices || [])
                    .filter((invoice) => invoice.history_id && pendingIds.has(invoice.history_id))
                    .map((invoice) =>
                        fetch(`/api/history/${encodeURIComponent(invoice.history_id as string)}`, {
                            method: 'PUT',
                            headers: authHeaders(true),
                            body: JSON.stringify({
                                pages: pagesForInvoice(IV.results[index], invoice),
                            }),
                        }).then(async (response) => {
                            const payload = await response.json().catch(() => ({}));
                            return {
                                ok: response.ok,
                                code: response.ok
                                    ? ''
                                    : responseErrorCode(payload, response.status),
                            };
                        })
                    )
            )
        );
        const failure = responses.find((response) => !response.ok);
        if (failure) {
            confirmationErrorCode = failure.code;
            return false;
        }
        return true;
    } catch {
        confirmationErrorCode = 'network_error';
        return false;
    }
}

export async function confirmIndices(indices: number[]): Promise<boolean> {
    const ids = indices.flatMap((index) => IV.results[index]?.history_ids || []);
    if (!ids.length) return false;
    confirmationErrorCode = '';
    if (isErpEntry()) {
        const before = await conversionState(ids);
        if (!before) return false;
        if (before.unresolved.length) {
            const pending = new Set(before.unresolved);
            if (!(await persistIndices(indices, pending))) {
                if (confirmationErrorCode !== 'erp.formal_document_locked') return false;
                const raced = await conversionState(ids);
                if (!raced || raced.unresolved.some((id) => pending.has(id))) return false;
            } else {
                before.unresolved.forEach((id) => convertStatus.delete(id));
                await convertHistoryIds(before.unresolved);
            }
        }
        const after = await conversionState(ids);
        if (!after || after.unresolved.length) {
            if (!confirmationErrorCode) confirmationErrorCode = 'formal_document_required';
            return false;
        }
    } else {
        await convertHistoryIds(ids);
    }
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

export async function verifyFormalConfirmation(indices: number[]): Promise<boolean> {
    if (!isErpEntry()) return true;
    confirmationErrorCode = '';
    const ids = indices.flatMap((index) => IV.results[index]?.history_ids || []);
    const state = await conversionState(ids);
    if (!state || state.unresolved.length) {
        if (!confirmationErrorCode) confirmationErrorCode = 'formal_document_required';
        return false;
    }
    indices.forEach((index) => IV.confirmed.add(index));
    return true;
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
