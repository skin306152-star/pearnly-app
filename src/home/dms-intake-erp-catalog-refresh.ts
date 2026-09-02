import { authHeaders } from './dms-intake-core.js';

export type FreshErpCatalogResult =
    | { status: 'loaded'; accountSets: unknown; requestId: string; revision: number }
    | { status: 'failed' | 'timeout' };

const FAST_POLL_MS = 800;
const SLOW_POLL_MS = 2_500;
const SLOW_NOTICE_MS = 120_000;
const TOTAL_TIMEOUT_MS = 930_000;
const FETCH_TIMEOUT_MS = 30_000;

async function fetchBeforeDeadline(
    url: string,
    init: RequestInit,
    deadline: number
): Promise<Response> {
    const remaining = deadline - Date.now();
    if (remaining <= 0) throw new DOMException('ERP catalog refresh timed out', 'TimeoutError');
    const controller = new AbortController();
    const timer = window.setTimeout(
        () => controller.abort(),
        Math.min(remaining, FETCH_TIMEOUT_MS)
    );
    try {
        return await fetch(url, { ...init, cache: 'no-store', signal: controller.signal });
    } finally {
        window.clearTimeout(timer);
    }
}

async function pauseBeforeNextPoll(delay: number, deadline: number): Promise<void> {
    const remaining = deadline - Date.now();
    if (remaining <= 0) return;
    await new Promise((resolve) => window.setTimeout(resolve, Math.min(delay, remaining)));
}

export async function fetchFreshErpCatalog(
    endpointId: string,
    onSlow: () => void
): Promise<FreshErpCatalogResult> {
    const startedAt = Date.now();
    const deadline = startedAt + TOTAL_TIMEOUT_MS;
    const slowTimer = window.setTimeout(onSlow, SLOW_NOTICE_MS);
    const base = `/api/erp/endpoints/${encodeURIComponent(endpointId)}/target-projection`;
    try {
        const refreshResponse = await fetchBeforeDeadline(
            `${base}/refresh`,
            { method: 'POST', headers: authHeaders() },
            deadline
        );
        const refreshResult = (await refreshResponse.json().catch(() => ({}))) as {
            refresh?: { request_id?: unknown };
        };
        const requestId = String(refreshResult.refresh?.request_id || '');
        if (!refreshResponse.ok || !requestId) return { status: 'failed' };

        let revision = 0;
        while (Date.now() < deadline) {
            const statusResponse = await fetchBeforeDeadline(
                `${base}/refresh/${encodeURIComponent(requestId)}`,
                { headers: authHeaders() },
                deadline
            );
            const statusResult = (await statusResponse.json().catch(() => ({}))) as {
                refresh?: { status?: unknown; result_revision?: unknown };
            };
            if (!statusResponse.ok) return { status: 'failed' };
            const status = String(statusResult.refresh?.status || '').toLowerCase();
            if (status === 'failed') return { status: 'failed' };
            if (status === 'succeeded') {
                const value = Number(statusResult.refresh?.result_revision || 0);
                revision = Number.isFinite(value) ? value : 0;
                break;
            }
            const delay = Date.now() - startedAt < 10_000 ? FAST_POLL_MS : SLOW_POLL_MS;
            await pauseBeforeNextPoll(delay, deadline);
        }
        if (Date.now() >= deadline) return { status: 'timeout' };

        const projectionResponse = await fetchBeforeDeadline(
            base,
            { headers: authHeaders() },
            deadline
        );
        const projectionResult = (await projectionResponse.json().catch(() => ({}))) as {
            data?: { snapshot?: { revision?: unknown; account_sets?: unknown } | null };
        };
        const snapshot = projectionResult.data?.snapshot;
        const snapshotRevision = Number(snapshot?.revision || 0);
        if (!projectionResponse.ok || !snapshot || revision <= 0 || snapshotRevision !== revision) {
            return { status: 'failed' };
        }
        return {
            status: 'loaded',
            accountSets: snapshot.account_sets,
            requestId,
            revision: snapshotRevision,
        };
    } catch {
        return { status: Date.now() >= deadline ? 'timeout' : 'failed' };
    } finally {
        window.clearTimeout(slowTimer);
    }
}
