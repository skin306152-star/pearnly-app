// 事务所端 · 商品收发存报表(Stock Card)· 数据适配层(类型 / 取数 / 金额与数量格式化)
// 契约信封与 /api/inventory/* 不同(顶层直出 products/rows/excluded_count,不套一层 data),
// 故不复用 inventory-common 的 invGet/unwrap,只借它的 activeWsId/authHeaders/fmtQty/fmtMoney
// (单出口,不重复造)。
import { activeWsId, authHeaders, fmtMoney, fmtQty } from './inventory-common.js';
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
// 与 routes/stock_card_routes.py 的 OpeningIn 同形(product_id 或 name 二选一)。
export interface StcOpeningRow {
    product_id?: string;
    name?: string;
    qty: string;
    unit_cost: string;
    as_of_date: string;
}
// 与 routes/stock_card_routes.py 的 _public_opening 同形(GET /openings 每行)。
export interface StcOpeningSaved {
    id: string;
    product_id: string | null;
    name_key: string | null;
    qty: string;
    unit_cost: string;
    as_of_date: string;
}
// 与 routes/stock_card_routes.py 的 MergeIn 同形(契约测试锁字段面,别单侧改)。
export interface StcMergePayload {
    name_keys: string[];
    target_product_id?: string;
    new_product_name?: string;
    unit?: string;
}

export class StcError extends Error {
    code: string;
    constructor(code: string) {
        super(code);
        this.code = code;
    }
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

// summary/card/excluded 三个 GET 都按账套 + 期间查询,card 多带一个 key —— 拼装收成一处,
// 不留三份逐字重复的 URLSearchParams 样板。
function stcRangeParams(
    wsId: number,
    dateFrom: string,
    dateTo: string,
    extra?: Record<string, string>
): URLSearchParams {
    return new URLSearchParams({
        workspace_client_id: String(wsId),
        date_from: dateFrom,
        date_to: dateTo,
        ...extra,
    });
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
    const q = stcRangeParams(wsId, dateFrom, dateTo);
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
    const q = stcRangeParams(wsId, dateFrom, dateTo, { key });
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
    const q = stcRangeParams(wsId, dateFrom, dateTo);
    const body = await stcFetch('/api/stockcard/excluded?' + q.toString());
    return (body.rows as StcExcludedRow[]) || [];
}

// 已存用户期初(GET 与 POST 同一路径,靠方法区分;期初弹窗开起时预填用)。
export async function stcGetOpenings(wsId: number): Promise<StcOpeningSaved[]> {
    const body = await stcFetch(`/api/stockcard/openings?workspace_client_id=${wsId}`);
    return (body.rows as StcOpeningSaved[]) || [];
}

// 两条写路径的 workspace_client_id 走 URL query —— 路由签名是 Query(...),塞 body 会被
// FastAPI 422 拒之门外(2026-08-08 实锤:期初/归并上线以来从没成功过一次)。
export async function stcPostOpenings(wsId: number, rows: StcOpeningRow[]): Promise<void> {
    await stcFetch(`/api/stockcard/openings?workspace_client_id=${wsId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rows }),
    });
}

export async function stcPostMerge(wsId: number, payload: StcMergePayload): Promise<void> {
    await stcFetch(`/api/stockcard/merge?workspace_client_id=${wsId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
}

// 无成本可算(老单据/期初未填)诚实置空 —— "—" 不是 0,不四舍五入造假(任务口径明文要求)。
export function fmtAmt(v: string | number | null | undefined): string {
    return v == null ? '—' : BAHT + fmtMoney(v);
}
