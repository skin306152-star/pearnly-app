// POS 项目 · PO-A4 库存后台 · 数据适配层(类型 / 契约信封 / 接口适配 / 错误码本地化 / 格式化)
// 04 §0.1 信封:成功 {ok:true,data},失败 {ok:false,error:{code}};前端先看 ok,再读 data / error.code。
// 接真接口 /api/inventory/*(PO-A3 · routes/inventory_routes.py)· 全部端点要 workspace_client_id(按账套隔离)。
/* global t, currentLang, token */

export interface InvName {
    th: string | null;
    en: string | null;
    zh: string | null;
}
export interface InvBatch {
    batch_no: string | null;
    expiry_date: string | null;
    qty: number | null;
}
export interface InvItem {
    product_id: string;
    name: InvName;
    barcode: string | null;
    base_unit: string | null;
    qty_on_hand: number | null;
    min_stock: number | null;
    avg_cost: number | null;
    status: 'ok' | 'low' | 'out';
    batches: InvBatch[];
}
export interface InvSummary {
    sku_count: number;
    stock_value: number | null;
    low_count: number;
    out_count: number;
}
export interface StockResp {
    items: InvItem[];
    summary: InvSummary;
}
export interface NearExpiryItem {
    product_id: string;
    name: InvName;
    batch_no: string | null;
    expiry_date: string | null;
    qty: number | null;
    days_left: number | null;
}
export type StockFilter = 'all' | 'low' | 'out';

export interface InLine {
    product_id: string;
    qty: string;
    unit_cost?: string;
    batch_no?: string;
    expiry_date?: string;
}
export interface CountLine {
    product_id: string;
    counted_qty: string;
}

// 契约错误:携带 06 字典里的 code(pos.out_of_stock 等),调用方映射 4 语文案,绝不裸露 code。
export class InvError extends Error {
    code: string;
    constructor(code: string) {
        super(code);
        this.code = code;
    }
}

interface Envelope {
    ok?: boolean;
    data?: unknown;
    error?: { code?: string };
}

function unwrap(body: Envelope): unknown {
    if (body && body.ok === true) return body.data;
    const code = (body && body.error && body.error.code) || 'pos.unexpected';
    throw new InvError(code);
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

async function invGet(url: string): Promise<unknown> {
    let body: Envelope;
    try {
        const r = await fetch(url, { headers: authHeaders() as HeadersInit });
        body = await r.json();
    } catch (_) {
        throw new InvError('pos.unexpected'); // 网络/解析失败 → 兜底人话
    }
    return unwrap(body);
}

async function invPost(url: string, payload: unknown): Promise<unknown> {
    let body: Envelope;
    try {
        const r = await fetch(url, {
            method: 'POST',
            headers: { ...authHeaders(), 'Content-Type': 'application/json' } as HeadersInit,
            body: JSON.stringify(payload),
        });
        body = await r.json();
    } catch (_) {
        throw new InvError('pos.unexpected');
    }
    return unwrap(body);
}

// 当前账套(库存按 workspace_client_id 隔离)· 个人模式/未选 → null(调用方提示选账套)。
export function activeWsId(): number | null {
    try {
        const fn = window.getActiveWorkspaceClientId;
        const id = typeof fn === 'function' ? fn() : null;
        return typeof id === 'number' ? id : null;
    } catch (_) {
        return null;
    }
}

// 最近一次 stock 结果缓存:入库/盘点弹窗的商品下拉直接复用(都是本账套在售商品)。
let lastItems: InvItem[] = [];

export const invApi = {
    async getStock(wsId: number, filter: StockFilter, q: string): Promise<StockResp> {
        const params = new URLSearchParams({ workspace_client_id: String(wsId), filter });
        const kw = q.trim();
        if (kw) params.set('q', kw);
        const data = (await invGet('/api/inventory/stock?' + params.toString())) as StockResp;
        lastItems = data.items || [];
        return data;
    },

    async postIn(wsId: number, lines: InLine[]): Promise<void> {
        await invPost('/api/inventory/in', {
            workspace_client_id: wsId,
            ref_type: 'purchase',
            lines,
        });
    },

    async postCount(wsId: number, lines: CountLine[]): Promise<void> {
        await invPost('/api/inventory/count', { workspace_client_id: wsId, lines });
    },

    async getNearExpiry(wsId: number, days: number): Promise<NearExpiryItem[]> {
        const params = new URLSearchParams({
            workspace_client_id: String(wsId),
            days: String(days),
        });
        const data = (await invGet('/api/inventory/near-expiry?' + params.toString())) as {
            items: NearExpiryItem[];
        };
        return data.items || [];
    },

    // 列表行内「近效期」黄点:该商品有批次在 near_expiry_days 内 → true。
    hasNearExpiry(it: InvItem, days: number): boolean {
        return it.batches.some((b) => b.expiry_date != null && daysUntil(b.expiry_date) <= days);
    },

    // 入库/盘点弹窗商品下拉:用最近加载的本账套在售商品(无需另请求)。
    products(): { product_id: string; name: string }[] {
        return lastItems.map((it) => ({
            product_id: it.product_id,
            name: localizedName(it.name),
        }));
    },
};

export const NEAR_EXPIRY_DAYS = 30;

// ── 工具 ──────────────────────────────────────────────────────────────
export function daysUntil(isoDate: string): number {
    const target = new Date(isoDate + 'T00:00:00Z').getTime();
    const now = new Date();
    const today = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
    return Math.round((target - today) / 86400000);
}

export function localizedName(name: InvName): string {
    const lang = typeof currentLang === 'string' ? currentLang : 'th';
    if (lang === 'zh') return name.zh || name.th || name.en || '—';
    if (lang === 'en') return name.en || name.th || name.zh || '—';
    return name.th || name.en || name.zh || '—'; // th / ja 回退 th
}

export function fmtMoney(v: number | string | null | undefined): string {
    return Number(v || 0).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
}

// 数量:整数不带小数,非整数最多 3 位且去尾零(拆零/称重)。
export function fmtQty(v: number | string | null | undefined): string {
    const n = Number(v || 0);
    if (Number.isInteger(n)) return String(n);
    return n.toFixed(3).replace(/\.?0+$/, '');
}

// ── POS 家族统一失败文案(09 §A.3 铁律 · 对齐销项 salesErrMsg)──────────
// 用户在任何 确认/完成/删除/创建/保存/收款 失败时只看人话,绝不看到原始 code / HTTP / 英文原文。
// posErrText:06 字典里的 code(pos.out_of_stock 等)→ 当前语言文案;查不到返 null(交调用方兜底)。
export function posErrText(code: string | null | undefined): string | null {
    const c = String(code || '').trim();
    if (!c) return null;
    const msg = t(c);
    return msg && msg !== c ? msg : null;
}

// posErrMsg:查不到就回退一句本地化兜底,保证永远是人话。
export function posErrMsg(code: string | null | undefined, fallbackKey: string): string {
    return posErrText(code) || t(fallbackKey);
}

// InvError(契约信封 error.code)/ 网络异常 → 本地化文案。无 code → 走 fallbackKey 兜底。
export function invErrMsg(err: unknown, fallbackKey: string): string {
    const code = err instanceof InvError ? err.code : null;
    return posErrMsg(code, fallbackKey);
}
