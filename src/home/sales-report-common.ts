// 销售仪表盘 · 共享地基:报表 API 类型 / 日期与金额小工具 / 取数(sales-report-* 模块共用)。
// 日期运算全走本地时区构造,不走 Date.parse(它把 YYYY-MM-DD 当 UTC,跨时区会漂一天)。
import { activeWsId, invGet, type InvName } from './inventory-common.js';
import { BAHT, bahtInt } from './money.js';
import { toDate, ymdIso } from './format-date.js';

export interface Kpi {
    gross: string;
    sales_count: number;
    avg_ticket: string;
    refund: string;
    cost: string;
    gross_profit: string | null;
    cost_complete: boolean;
}
export interface DayRow {
    date: string;
    gross: string;
    sales_count: number;
    gross_profit: string | null;
}
export interface HourRow {
    hour: number;
    gross: string;
    sales_count: number;
}
export interface TopProduct {
    product_id: string;
    name: InvName;
    qty: string;
    gross: string;
    gross_profit: string | null;
}
export interface HeatCell {
    date: string;
    hour: number;
    gross: string;
}
export interface Live {
    last_sale_at: string | null;
    open_shift: { cashier_name: string | null; shift_seq: number | null } | null;
}
export interface Report {
    kpi: Kpi;
    by_day: DayRow[];
    by_hour: HourRow[] | null;
    by_method: Record<string, string>;
    top_products: TopProduct[];
    prev_kpi: Kpi | null;
    heat: HeatCell[];
    live: Live;
}

export type Granularity = 'day' | 'month';
export type SectionState = 'loading' | 'error' | 'ready';

// 翻页箭头统一 lucide 线条 chevron(设计系统禁字符图标;实心三角字符属 emoji 面,顶 lint-ui 棘轮)
export const CHEV_L =
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 18l-6-6 6-6"/></svg>';
export const CHEV_R =
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 18l6-6-6-6"/></svg>';

// 店内营业钟点与热力窗口:Hero 分时脉搏与热力网格共用同一根轴,只许在这里定义。
export const HOUR_LO = 8;
export const HOUR_HI = 22;
export const HEAT_DAYS = 14;

export function pad2(n: number): string {
    return String(n).padStart(2, '0');
}
export const ymd = ymdIso;
// YYYY-MM-DD → 本地时区 Date(口径与坑同 format-date.toDate,此处只收窄签名)。
export function parseYmd(iso: string): Date {
    return toDate(iso) as Date;
}
export function addDays(iso: string, n: number): string {
    const d = parseYmd(iso);
    d.setDate(d.getDate() + n);
    return ymd(d);
}
export function addMonths(ymStr: string, n: number): string {
    const [y, m] = ymStr.split('-').map(Number);
    const d = new Date(y, m - 1 + n, 1);
    return d.getFullYear() + '-' + pad2(d.getMonth() + 1);
}
export function monthDays(ymStr: string): number {
    const [y, m] = ymStr.split('-').map(Number);
    return new Date(y, m, 0).getDate();
}

export { bahtInt };

export function baht(v: string | number): string {
    return BAHT + bahtInt(v);
}

// 环比:上期缺失/为 0 没有比率可言 → null(渲染层给「—」,绝不显示 ∞%)。
// hero 副行与构成卡徽章共用这一份口径,只许在这里改。
export function pctVsPrev(cur: number, prev: number | null): number | null {
    if (prev == null || !(prev > 0)) return null;
    return ((cur - prev) / prev) * 100;
}

// 轴刻度紧凑写法:1250 → 1.3k(轴上的字要退后,不跟数据抢眼)。
export function axisFmt(v: number): string {
    if (v >= 1000) {
        const k = v / 1000;
        return (k >= 10 ? Math.round(k) : Math.round(k * 10) / 10) + 'k';
    }
    return String(Math.round(v));
}

// 毛利可能诚实置空(老单据无成本快照)——跟真 0 分开渲染,不拿 "—" 冒充 0。
export function moneyOrUnknown(v: string | null): string {
    return v == null ? '—' : baht(v);
}

// 取数走 POS 家族共用的 invGet(鉴权头 + 信封拆包单出口);抛 InvError,message=错误码,
// 调用方的 posErrMsg(e.message) 口径不变。
export async function fetchReport(params: Record<string, string>): Promise<Report> {
    const q = new URLSearchParams({ workspace_client_id: String(activeWsId()), ...params });
    return (await invGet('/api/pos/admin/report?' + q.toString())) as Report;
}
