// 事务所端 · 商品收发存报表(Stock Card)· 数据适配层(类型 / 取数 / 金额与数量格式化)
// 契约信封与 /api/inventory/* 不同(顶层直出 products/rows/excluded_count,不套一层 data),
// 故不复用 inventory-common 的 invGet/unwrap,只借它的 activeWsId/fmtQty/fmtMoney(单出口,不重复造)。
/* global token */
import { activeWsId, fmtMoney, fmtQty } from './inventory-common.js';
import { BAHT } from './money.js';

export { activeWsId, fmtQty };

export interface StcProduct {
    key: string;
    product_id: string;
    name: string;
    unit: string;
    opening_qty: string | null;
    in_qty: string;
    out_qty: string;
    bal_qty: string;
    bal_unit_cost: string | null;
    bal_value: string | null;
    negative: boolean;
    matched: boolean;
}
export interface StcSummaryResp {
    products: StcProduct[];
    excluded_count: number;
}
export type StcMoveKind = 'open' | 'in' | 'out';
export interface StcCardRow {
    date: string;
    doc_no: string | null;
    kind: StcMoveKind;
    desc: string | null;
    qty: string;
    unit_price: string | null;
    amount: string | null;
    bal_qty: string;
    bal_unit_cost: string | null;
    bal_value: string | null;
}
// 后端 totals 字段形状未逐一约定死;按需读取,缺的那块由 stock-card-render 从 rows 现算兜底
// (求和口径与后端一致——kind 分组求 qty/amount,结存取最后一行),不整段依赖这个类型齐全。
export interface StcCardTotals {
    in_qty?: string;
    in_amount?: string;
    out_qty?: string;
    out_amount?: string;
    bal_qty?: string;
    bal_unit_cost?: string | null;
    bal_value?: string | null;
}
export interface StcCardResp {
    product: { product_id: string; name: string; unit: string; matched: boolean };
    rows: StcCardRow[];
    totals: StcCardTotals;
}
export type StcExcludedReason = 'service' | 'no_qty_price' | 'total_only';
export interface StcExcludedRow {
    date: string;
    doc_no: string | null;
    desc: string | null;
    amount: string;
    reason: StcExcludedReason;
    side: string;
}
export interface StcOpeningRow {
    product_id?: string;
    name_key?: string;
    qty: string;
    unit_cost: string;
    as_of_date: string;
}
export interface StcMergePayload {
    name_keys: string[];
    target_product_id?: string;
    new_product_name?: string;
}

export class StcError extends Error {
    code: string;
    constructor(code: string) {
        super(code);
        this.code = code;
    }
}

function authHeaders(): Record<string, string> {
    const h: Record<string, string> = {
        Authorization: 'Bearer ' + (typeof token === 'string' ? token : ''),
    };
    try {
        const ws = window._wsHeader && window._wsHeader();
        if (ws) for (const k in ws) if (ws[k] != null) h[k] = ws[k] as string;
    } catch (_) {
        /* 切换器未就绪 · 静默 */
    }
    return h;
}

interface StcEnvelope {
    ok?: boolean;
    error?: { code?: string };
    [key: string]: unknown;
}

async function stcFetch(url: string, init?: RequestInit): Promise<StcEnvelope> {
    let body: StcEnvelope;
    try {
        const r = await fetch(url, { ...init, headers: { ...authHeaders(), ...init?.headers } });
        body = await r.json();
    } catch (_) {
        throw new StcError('stc.unexpected'); // 网络/解析失败
    }
    if (!body || body.ok !== true)
        throw new StcError((body && body.error && body.error.code) || 'stc.unexpected');
    return body;
}

export async function stcGetStatus(): Promise<boolean> {
    const body = await stcFetch('/api/stockcard/status');
    return body.enabled === true;
}

export async function stcGetSummary(
    wsId: number,
    dateFrom: string,
    dateTo: string
): Promise<StcSummaryResp> {
    const q = new URLSearchParams({
        workspace_client_id: String(wsId),
        date_from: dateFrom,
        date_to: dateTo,
    });
    const body = await stcFetch('/api/stockcard/summary?' + q.toString());
    return {
        products: (body.products as StcProduct[]) || [],
        excluded_count: Number(body.excluded_count) || 0,
    };
}

export async function stcGetCard(
    wsId: number,
    key: string,
    dateFrom: string,
    dateTo: string
): Promise<StcCardResp> {
    const q = new URLSearchParams({
        workspace_client_id: String(wsId),
        key,
        date_from: dateFrom,
        date_to: dateTo,
    });
    const body = await stcFetch('/api/stockcard/card?' + q.toString());
    return {
        product: body.product as StcCardResp['product'],
        rows: (body.rows as StcCardRow[]) || [],
        totals: (body.totals as StcCardTotals) || {},
    };
}

export async function stcGetExcluded(
    wsId: number,
    dateFrom: string,
    dateTo: string
): Promise<StcExcludedRow[]> {
    const q = new URLSearchParams({
        workspace_client_id: String(wsId),
        date_from: dateFrom,
        date_to: dateTo,
    });
    const body = await stcFetch('/api/stockcard/excluded?' + q.toString());
    return (body.rows as StcExcludedRow[]) || [];
}

export async function stcPostOpenings(wsId: number, rows: StcOpeningRow[]): Promise<void> {
    await stcFetch('/api/stockcard/openings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_client_id: wsId, rows }),
    });
}

export async function stcPostMerge(wsId: number, payload: StcMergePayload): Promise<void> {
    await stcFetch('/api/stockcard/merge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_client_id: wsId, ...payload }),
    });
}

// 无成本可算(老单据/期初未填)诚实置空 —— "—" 不是 0,不四舍五入造假(任务口径明文要求)。
export function fmtAmt(v: string | number | null | undefined): string {
    return v == null ? '—' : BAHT + fmtMoney(v);
}
