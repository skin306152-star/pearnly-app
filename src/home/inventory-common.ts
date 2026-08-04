// POS 项目 · PO-A4 库存后台 · 数据适配层(类型 / 契约信封 / 接口适配 / 错误码本地化 / 格式化)
// 04 §0.1 信封:成功 {ok:true,data},失败 {ok:false,error:{code}};前端先看 ok,再读 data / error.code。
// 接真接口 /api/inventory/*(PO-A3 · routes/inventory_routes.py)· 全部端点要 workspace_client_id(按账套隔离)。
/* global t, currentLang, token */

import { BAHT } from './money.js';

export interface InvName {
    th: string | null;
    en: string | null;
    zh: string | null;
}
export interface InvBatch {
    batch_id?: string;
    batch_no: string | null;
    expiry_date: string | null;
    qty: number | null;
}
export interface InvItem {
    product_id: string;
    name: InvName;
    image_url: string | null;
    barcode: string | null;
    base_unit: string | null;
    qty_on_hand: number | null;
    min_stock: number | null;
    avg_cost: number | null;
    status: 'ok' | 'low' | 'out';
    track_batch: boolean;
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
    // 入库单位(扫到箱码时带回来)· 后端 resolve_factor 按 product_units.factor_to_base 折算;
    // 缺省 = 基本单位。前端不自己乘系数:系数改一次两处漂。
    unit_name?: string;
    unit_cost?: string;
    batch_no?: string;
    expiry_date?: string;
}
export interface CountLine {
    product_id: string;
    batch_id?: string;
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

export async function invGet(url: string): Promise<unknown> {
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
    // track_batch/batches 一并带出:入库按它显隐批号/效期、盘点按它决定是否逐批。
    products(): { product_id: string; name: string; track_batch: boolean; batches: InvBatch[] }[] {
        return lastItems.map((it) => ({
            product_id: it.product_id,
            name: localizedName(it.name),
            track_batch: !!it.track_batch,
            batches: it.batches || [],
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

// 成本/货值列:无 field.cost.view 码的角色,后端把均价/货值返 null(G4 遮蔽)→ 显「--」;
// 真零成本仍是数字 0 → 显示成 0.00,只有 null 才是被遮蔽。
export function fmtCost(v: number | string | null | undefined): string {
    return v == null ? '--' : BAHT + fmtMoney(v);
}

// 效期的年份带子。上限是 4 位年份这条硬线;下限挡的是 0490-12-31 这种「四位但明显不是人填的」
// 值 —— 店里不会有 1900 年之前到期的货。
const EXPIRY_YEARS = { min: 1900, max: 2999 };

/**
 * 「这个框里现在是一个人填完了的日期」。type=date 的控件自己收得下 6 位年份:一串条码打进去
 * (枪扫时字符照旧落在光标所在的框里)留下的是 49012-03-31,人填完留下的一定是 4 位年份 ——
 * 扫码侧靠这一条把机器打的一串跟人手填的分开,不必去猜速度。
 */
export function isPlausibleDate(value: string): boolean {
    const v = String(value || '').trim();
    if (!/^\d{4}-\d{2}-\d{2}$/.test(v)) return false;
    const year = Number(v.slice(0, 4));
    return year >= EXPIRY_YEARS.min && year <= EXPIRY_YEARS.max;
}

/**
 * 效期要么没填,要么是个像样的日期。49012-03-31 提交出去后端照收,那批货从此永远不会进近效期
 * 名单、FEFO 也永远把它排在最后。扫码侧已经把码从框里退回去了,但粘贴/回填/别的浏览器都绕得过
 * 那一层 —— 进流水之前必须还有这一道。
 */
export function isSaneExpiry(value: string): boolean {
    const v = String(value || '').trim();
    return !v || isPlausibleDate(v);
}

// 数量的位数上限。这条线不是拍脑袋的:零售条码最短的一档(EAN-8 / UPC-E)就是 8 位数字,
// 所以一整串条码掉进数量框,留下的必然是 8 位起的一串;而单子上某一行填到八位数(一千万件
// 起)在便利店/小零售不存在 —— 真的大批量是按箱收的,箱数仍是三四位数,「箱」由那一行的
// unit_name 表达(后端按 factor_to_base 折算成基本单位)。7 位因此是「拦得住整串条码」与
// 「挡不着真实大批量」之间唯一有物理依据的位置,离最夸张的真实用量(十万件级)还有两个
// 数量级的余地。
const MAX_QTY_DIGITS = 7;

// 进货单价的位数上限。跟数量同一个数,但理由是另一条 —— 两处的上限各按各的业务顶算,
// 谁也不该因为另一头改了就跟着动。泰国小零售单件最贵的真实进货是金饰店:一公斤金条
// ≈ ฿ 2,400,000(七位)。7 位(≤ ฿ 9,999,999.99/件)因此把最贵的那档真货留了四倍余量,
// 同时仍在「整串条码留下的 8 位起」之下 —— 拦得住掉进来的码,挡不着真买卖。
const MAX_COST_DIGITS = 7;

/** 整数部分的位数与量级各挡一头。少一条就有漏,见两个调用点的注释。 */
function withinDigits(value: string, maxDigits: number): boolean {
    const n = Number(value);
    if (!Number.isFinite(n)) return false;
    const digits = (value.split('.')[0].match(/\d/g) || []).length;
    return digits <= maxDigits && Math.abs(n) < Math.pow(10, maxDigits);
}

/**
 * 「这个数量不是一串条码掉进来的」。
 *
 * 楔子已经在框那一层把枪打的串还原回去了,但那一层漏一次(焦点在两个框之间被异步挪走、
 * 换个浏览器、粘贴)就是 19 亿件跟着整张单子进库存和成本 —— 同 isSaneExpiry 的道理,
 * 进流水之前必须还有这一道。
 *
 * 只挡量级这一档:残串只剩三四位时跟真实数量长得一模一样,谁也分不出来,那一半只有楔子
 * 修得了。0 / 负数不归这里管(入库按 >0 过滤,盘点的 0 是「架上真没有」这个合法答案)。
 *
 * 位数与量级各挡一头,少一条就有漏:EAN-8 的 01234567 数值只有 1234567(量级那条放它过),
 * 而 1e10 这种写法只有两个数字(位数那条放它过)。
 */
export function isSaneQty(value: string): boolean {
    const v = String(value || '').trim();
    if (!v) return true; // 空 = 这一行本来就不提交,不在射程内
    return withinDigits(v, MAX_QTY_DIGITS);
}

/**
 * 「这个进货单价不是一串条码掉进来的」。
 *
 * 单价框比数量框更该有这一道,因为它错了没人看得见:数量错了架上一点就对不上,单价错了
 * 只改库存估值与移动加权成本 —— 真浏览器实测(枪扫时光标停在单价格)฿ 8850999320014/瓶
 * 原样进了 POST /api/inventory/in,屏上一个字都没有,弹窗照常关掉报成功。
 *
 * 同 isSaneQty:只挡量级这一档,残串短到跟真价格同形时谁也分不出来。
 */
export function isSaneCost(value: string): boolean {
    const v = String(value || '').trim();
    if (!v) return true; // 空 = 单价缺省,后端按 0 落账
    return withinDigits(v, MAX_COST_DIGITS);
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
