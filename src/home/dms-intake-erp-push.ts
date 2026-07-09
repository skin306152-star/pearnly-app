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

// 单条推送:每条 ocr_history 一次 POST /api/erp/push。true=成功。
export async function pushHistory(historyId: string, target: string): Promise<boolean> {
    try {
        const body: Record<string, unknown> = { history_id: historyId };
        if (target) body.endpoint_id = target;
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
