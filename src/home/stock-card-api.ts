// ERP 门户 · 商品收发存报表(Stock Card)· 数据适配层(类型 / 取数 / 金额与数量格式化)
// 契约信封与 /api/inventory/* 不同(顶层直出 groups/rows,不套一层 data),故不复用
// inventory-common 的 invGet/unwrap,只借它的 activeWsId/authHeaders/fmtQty/fmtMoney
// (单出口,不重复造)。
import { activeWsId, authHeaders, fmtMoney, fmtQty } from './inventory-common.js';

export { activeWsId, fmtQty };

export type StcMoveKind = 'open' | 'in' | 'out';
// 13 列表格的一行(期初 / 采购入库 / 销售出库),数字字段字符串,未知成本为 null。
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
// 商品标题只带名称/编码/单位,以及期初录入所需的 key —— 参考图没有状态/归并等附加字段。
export interface StcGroupProduct {
    key: string;
    product_id: string | null;
    name: string;
    unit: string | null;
}
export interface StcCardTotals {
    in_qty?: string;
    in_amount?: string | null;
    out_qty?: string;
    out_amount?: string | null;
    bal_qty?: string;
    bal_unit_cost?: string | null;
    bal_value?: string | null;
}
export interface StcGroup {
    product: StcGroupProduct;
    rows: StcCardRow[];
    totals: StcCardTotals;
}
// /api/stockcard/report 信封:主视图只用这一次请求,不含汇总/未入账等旧视图。
export interface StcReportResp {
    groups: StcGroup[];
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

// report/openings 都按账套 + 期间查询 —— 拼装收成一处,不留多份逐字重复的样板。
function stcRangeParams(wsId: number, dateFrom: string, dateTo: string): URLSearchParams {
    return new URLSearchParams({
        workspace_client_id: String(wsId),
        date_from: dateFrom,
        date_to: dateTo,
    });
}

export async function stcGetStatus(): Promise<boolean> {
    const body = await stcFetch('/api/stockcard/status');
    return body.enabled === true;
}

export async function stcGetReport(
    wsId: number,
    dateFrom: string,
    dateTo: string
): Promise<StcReportResp> {
    const q = stcRangeParams(wsId, dateFrom, dateTo);
    const body = await stcFetch('/api/stockcard/report?' + q.toString());
    return {
        groups: (body.groups as StcGroup[]) || [],
    };
}

// 已存用户期初(GET 与 POST 同一路径,靠方法区分;期初弹窗开起时预填用)。
export async function stcGetOpenings(wsId: number): Promise<StcOpeningSaved[]> {
    const body = await stcFetch(`/api/stockcard/openings?workspace_client_id=${wsId}`);
    return (body.rows as StcOpeningSaved[]) || [];
}

// 写路径的 workspace_client_id 走 URL query —— 路由签名是 Query(...),塞 body 会被
// FastAPI 422 拒之门外(2026-08-08 实锤)。
export async function stcPostOpenings(wsId: number, rows: StcOpeningRow[]): Promise<void> {
    await stcFetch(`/api/stockcard/openings?workspace_client_id=${wsId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rows }),
    });
}

// 无成本可算(老单据/期初未填)诚实置空 —— "—" 不是 0,不四舍五入造假(任务口径明文要求)。
export function fmtAmt(v: string | number | null | undefined): string {
    return v == null ? '—' : fmtMoney(v);
}
