// ============================================================
// 录入工作台 · ERP 推送共享单元(发票任务 + 汇总批量共用·唯一事实源)
//   端点读 /api/erp/endpoints(排除 mrerp_dms=DMS 客户档,非记账推送目标);
//   推送 /api/erp/push(每条 ocr_history 一次·后端按账套税号判方向,入队 Express 或直写 MR.ERP)。
// 只放两条流程都用得上的通用件;各自的输出面板(发票有 Excel 选择)仍留各自模块。
// ============================================================
import { esc, authHeaders } from './dms-intake-core.js';

function t(k: string): string {
    const w = window as unknown as { t?: (k: string) => string };
    return typeof w.t === 'function' ? w.t(k) : k;
}

export interface ErpEndpoint {
    id: string | number;
    name?: string;
    adapter?: string;
    enabled?: boolean;
    is_default?: boolean;
}

// 拉可选 ERP 端点(排除 DMS 客户档)。失败回空,由调用方走空态。
export async function fetchErpEndpoints(): Promise<ErpEndpoint[]> {
    try {
        const r = await fetch('/api/erp/endpoints', { headers: authHeaders() });
        const d = (await r.json().catch(() => ({}))) as { items?: ErpEndpoint[] };
        return (d.items || []).filter((e) => (e.adapter || '').toLowerCase() !== 'mrerp_dms');
    } catch {
        return [];
    }
}

// 选默认推送目标:已选且仍启用则保留,否则取 is_default,再否则第一个启用端点。
export function pickDefaultTarget(endpoints: ErpEndpoint[], current: string): string {
    const enabled = endpoints.filter((e) => e.enabled !== false);
    if (current && enabled.some((e) => String(e.id) === current)) return current;
    const def = enabled.find((e) => e.is_default) || enabled[0];
    return def ? String(def.id) : '';
}

// 目标卡 HTML(只列启用端点·data-erp-target 供点击委托)。停用端点是「同批不误投多个 ERP」的闸。
export function erpTargetCardsHtml(endpoints: ErpEndpoint[], target: string): string {
    const cards = endpoints
        .filter((e) => e.enabled !== false)
        .map((e) => {
            const on = String(e.id) === target ? ' active' : '';
            const lg = (e.adapter || '').slice(0, 2).toUpperCase();
            const meta = (e.is_default ? t('dxi-erp-default') + ' · ' : '') + t('dxi-erp-enabled');
            return (
                `<div class="dx-erp${on}" data-erp-target="${esc(String(e.id))}">` +
                `<div class="dx-erp-lg">${esc(lg)}</div>` +
                `<div class="dx-erp-c"><b>${esc(e.name || e.adapter || 'ERP')}</b>` +
                `<span>${esc(meta)}</span></div><div class="dx-erp-chk" aria-hidden="true"></div></div>`
            );
        })
        .join('');
    return `<div class="dx-erps">${cards}</div>`;
}

// 单条推送 POST /api/erp/push。已受理=true:ok=true(success/skipped_dup)或 status='pending'(Express 出站拉取异步入队·非失败);failed/manual=false。对齐后端 counts_as_endpoint_success。
// postingKind:本批过账去向('stock'|'service')· 仅 Express 销项后端消费,'stock'=商品按库存出库。
export type PushOutcome = 'success' | 'waiting' | 'failed' | 'needs_action';

export function operationId(): string {
    if (typeof crypto.randomUUID === 'function') return crypto.randomUUID();
    const bytes = crypto.getRandomValues(new Uint8Array(16));
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    const hex = Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('');
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

export function pushState(status: string | null | undefined): PushOutcome {
    const value = String(status || '').toLowerCase();
    if (value === 'success' || value === 'skipped_dup') return 'success';
    if (value === 'pending' || value === 'retrying' || value === 'leased') return 'waiting';
    if (
        value === 'manual' ||
        value === 'blocked' ||
        value === 'needs_mapping' ||
        value === 'needs_review'
    )
        return 'needs_action';
    return 'failed';
}

export function aggregatePushState(
    statuses: Array<string | null | undefined>,
    fallback?: string | null
): PushOutcome {
    const states = statuses.filter(Boolean).map(pushState);
    if (!states.length) return pushState(fallback);
    if (states.includes('needs_action')) return 'needs_action';
    if (states.includes('failed')) return 'failed';
    if (states.includes('waiting')) return 'waiting';
    return 'success';
}

export function pushStateLabel(state: PushOutcome): string {
    const keys: Record<PushOutcome, string> = {
        waiting: 'expd-tl-pending',
        success: 'erp-status-success',
        failed: 'erp-status-failed',
        needs_action: 'expd-tl-manual',
    };
    return t(keys[state]);
}

export function pushToastKind(state: PushOutcome): 'success' | 'info' | 'warn' | 'error' {
    if (state === 'success') return 'success';
    if (state === 'waiting') return 'info';
    if (state === 'needs_action') return 'warn';
    return 'error';
}

export async function pushHistory(
    historyId: string,
    target: string,
    postingKind?: string
): Promise<PushOutcome> {
    try {
        const body: Record<string, unknown> = {
            history_id: historyId,
            operation_id: operationId(),
        };
        if (target) body.endpoint_id = target;
        if (postingKind) body.posting_kind = postingKind;
        const r = await fetch('/api/erp/push', {
            method: 'POST',
            headers: authHeaders(true),
            body: JSON.stringify(body),
        });
        const d = (await r.json().catch(() => ({}))) as {
            ok?: boolean;
            status?: string;
            stage?: string;
            rows?: number;
        };
        if (!r.ok) return 'failed';
        if (d.rows === 0) return 'needs_action';
        const declared = d.status || d.stage;
        const state = pushState(declared);
        if (state === 'needs_action') return state;
        if (d.ok === false) return 'failed';
        if (state === 'waiting') return state;
        if (d.ok === true && (!declared || state === 'success')) return 'success';
        return 'failed';
    } catch {
        return 'failed';
    }
}
