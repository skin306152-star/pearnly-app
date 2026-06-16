// 商户采购(进项)Phase 1 · 数据适配层(类型 / 契约信封 / mock 兜底 / 错误码本地化 / 格式化 / 作用域样式)
// 接口契约见 docs/purchasing/02。信封同 POS:成功 {ok:true,data},失败 {ok:false,error:{code,message_key}}。
// mock 兜底:后端 /api/purchase/* 未上线(404 / 非信封)时落本地 mock(purchase-mock.ts);上线后自动切真。
// 全接口要 workspace_client_id(按套账隔离);个人模式/未选账套 → null,调用方提示先选公司。
/* global t, token */
import { mockHandle } from './purchase-mock.js';

export type DocKind = 'purchase_invoice' | 'purchase_order' | 'expense';
export type PaymentStatus = 'unpaid' | 'partial' | 'paid';
export type DocStatus = 'draft' | 'posted' | 'void';
export type ItemType = 'goods' | 'service';
export type Source = 'photo' | 'line' | 'manual' | 'upload';

export interface DocListItem {
    id: string;
    doc_date: string | null;
    supplier_name: string | null;
    title: string | null; // 「进货 12 项」/「打车」等列表副标
    doc_kind: DocKind;
    doc_type: string; // 精简文档类型:tax_invoice/simple_tax_receipt/receipt/purchase_order/substitute_receipt/other
    category_label: string | null;
    source: Source;
    grand_total: number;
    vat_amount: number;
    has_vat: boolean;
    payment_status: PaymentStatus;
    status: DocStatus;
    upload_date: string | null; // 上传/创建日期(票面/上传日期口径切换用)
    attachment_count: number; // 附件张数(列表「+N」用)
}

export interface DocSummary {
    purchase_total: number;
    purchase_count: number;
    expense_total: number;
    expense_count: number;
    vat_creditable: number;
    unpaid_total: number;
    unpaid_suppliers: number;
}

export interface Supplier {
    id: string;
    name: string;
    tax_id: string | null;
    branch_type: 'head_office' | 'branch' | 'none';
    branch_no: string | null;
    address: string | null;
    phone: string | null;
    note: string | null;
    is_active: boolean;
    total_purchased: number;
    last_purchase_date: string | null;
}

export interface Category {
    id: string;
    parent_id: string | null;
    name: string;
    is_active: boolean;
    children?: Category[];
}

export interface PurchaseSettings {
    default_vat_rate: number;
    auto_stock_in: boolean;
    dedupe_block: boolean;
    default_due_days: number;
    pay_needs_approval: boolean;
    default_wht_service_rate: number;
    base_currency: string;
    auto_book: boolean;
}

export interface DocLine {
    id?: string;
    item_type: ItemType;
    product_id: string | null;
    product_matched?: boolean;
    description: string;
    qty: number;
    unit: string | null;
    unit_price: number;
    discount: number;
    vat_rate: number;
    wht_rate: number;
    category_label?: string | null;
    category_id?: string | null;
    subcategory_id?: string | null;
    stock_in?: boolean;
    discountOn?: boolean; // 行折扣开关(UI 态 · 控制是否显示/计折扣输入)
}

export interface DocAttachment {
    id: string;
    kind: 'bill' | 'substitute_receipt' | 'payment_proof' | 'wht_cert';
    url: string | null;
    generated: boolean;
}

export interface DocDetail {
    id: string;
    doc_kind: DocKind;
    status: DocStatus;
    supplier: Supplier | null;
    doc_no: string | null;
    doc_date: string | null;
    due_date: string | null;
    has_vat: boolean;
    currency: string;
    source: Source;
    requester: string | null;
    lines: DocLine[];
    attachments: DocAttachment[];
    bill_image_url: string | null;
    subtotal: number;
    discount_total: number;
    vat_amount: number;
    wht_amount: number;
    rounding: number;
    grand_total: number;
    net_payable: number;
    paid_amount: number;
    payment_status: PaymentStatus;
    stock_applied: boolean;
    dedupe_hit?: boolean;
}

// 契约错误:携带 02/05 字典里的 code(purchase.dup_invoice 等),调用方映射 4 语,绝不裸露 code。
export class PurchaseError extends Error {
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

export function authHeaders(): Record<string, string> {
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

function unwrap(body: Envelope): unknown {
    if (body && body.ok === true) return body.data;
    throw new PurchaseError((body && body.error && body.error.code) || 'purchase.unexpected');
}

// papi:打真接口 /api/purchase/*。后端已上线(S1-S5)→ 一律走真:成功取 data,失败抛 code。
// 仅当路由「不存在」(HTTP 404)才落本地 mock —— 这只发生在离线视觉闸/冒烟 harness(stub 回 404);
// 线上路由存在(鉴权失败回 401 等),走真信封/真错误,绝不静默吞成 mock(状态诚实)。
// payload 传 FormData = multipart 上传(拍进项票真传图):浏览器自带边界,不塞 Content-Type。
export async function papi(method: string, path: string, payload?: unknown): Promise<unknown> {
    const isForm = payload instanceof FormData;
    let status = 0;
    let body: Envelope | null = null;
    let netFail = false;
    try {
        const headers = authHeaders();
        if (payload !== undefined && !isForm) headers['Content-Type'] = 'application/json';
        const r = await fetch(path, {
            method,
            headers: headers as HeadersInit,
            body: isForm
                ? (payload as FormData)
                : payload !== undefined
                  ? JSON.stringify(payload)
                  : undefined,
        });
        status = r.status;
        body = (await r.json().catch(() => null)) as Envelope | null;
    } catch (_) {
        netFail = true;
    }
    if (status === 404) return mockHandle(method, path, isForm ? {} : payload); // 路由不存在(harness)→ mock
    if (netFail) throw new PurchaseError('purchase.unexpected'); // 网络/解析失败 → 诚实报错
    if (body != null && typeof body.ok === 'boolean') return unwrap(body); // 真信封
    throw new PurchaseError('purchase.unexpected'); // 401/500/非信封 → 诚实报错,不吞成 mock
}

// 受鉴权的 PDF(替代收据/扣缴凭证/票图)→ blob → 新标签打开。window.open 无法带 Bearer,
// 故 fetch(authHeaders) 取 blob 再开 object URL(对齐销项 loadAuthedImg 思路)。失败抛 code。
export async function openPurchasePdf(path: string): Promise<void> {
    let r: Response;
    try {
        r = await fetch(path, { headers: authHeaders() as HeadersInit });
    } catch (_) {
        throw new PurchaseError('purchase.unexpected');
    }
    if (!r.ok) throw new PurchaseError('purchase.unexpected');
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
    setTimeout(() => URL.revokeObjectURL(url), 60000);
}

// 受鉴权资源(票图)→ blob → object URL · 供 <img src> 与「放大看」新标签复用(同带 Bearer)。
export async function fetchAuthedBlobUrl(path: string): Promise<string> {
    let r: Response;
    try {
        r = await fetch(path, { headers: authHeaders() as HeadersInit });
    } catch (_) {
        throw new PurchaseError('purchase.unexpected');
    }
    if (!r.ok) throw new PurchaseError('purchase.unexpected');
    return URL.createObjectURL(await r.blob());
}

// 票图 url → 可直接喂 <img src> 的源:本地 blob:/data: 原样返回,鉴权 serving url 取 blob 并按 url
// 缓存(详情票图 + 复核查看器/缩略图共用 · 同图去重取图 · 切页/重渲不重拉)。取图失败 → null(留占位)。
const billBlobCache = new Map<string, string>();
export async function resolveBillSrc(url: string): Promise<string | null> {
    if (url.startsWith('blob:') || url.startsWith('data:')) return url;
    const cached = billBlobCache.get(url);
    if (cached) return cached;
    try {
        const src = await fetchAuthedBlobUrl(url);
        billBlobCache.set(url, src);
        return src;
    } catch (_) {
        return null;
    }
}

// 当前账套(进项按 workspace_client_id 隔离)· 个人模式/未选 → null(调用方提示选账套)。
export function activeWsId(): number | null {
    try {
        const fn = window.getActiveWorkspaceClientId;
        const id = typeof fn === 'function' ? fn() : null;
        return typeof id === 'number' ? id : null;
    } catch (_) {
        return null;
    }
}

// ── 失败文案(铁律 · 对齐 POS posErrMsg / 销项 salesErrMsg)─────────────
// 用户在任何 确认/入账/删除/记付款 失败时只看人话,绝不看到原始 code / HTTP / 英文原文。
export function purchaseErrMsg(err: unknown, fallbackKey: string): string {
    const code = err instanceof PurchaseError ? err.code : null;
    const c = String(code || '').trim();
    if (c) {
        const msg = t(c);
        if (msg && msg !== c) return msg;
    }
    return t(fallbackKey);
}

// ── 格式化 ────────────────────────────────────────────────────────────
export function fmtMoney(v: number | string | null | undefined): string {
    return Number(v || 0).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
}

// KPI / 列表用:฿62,400 风格(整数无小数,有角分时显 2 位)。
export function fmtBaht(v: number | string | null | undefined): string {
    const n = Number(v || 0);
    const opts = Number.isInteger(n)
        ? { maximumFractionDigits: 0 }
        : { minimumFractionDigits: 2, maximumFractionDigits: 2 };
    return '฿' + n.toLocaleString('en-US', opts);
}

export function fmtQty(v: number | string | null | undefined): string {
    const n = Number(v || 0);
    if (Number.isInteger(n)) return String(n);
    return n.toFixed(3).replace(/\.?0+$/, '');
}

// 月-日(列表紧凑显示):2026-06-08 → 06-08。
export function fmtMonthDay(iso: string | null | undefined): string {
    if (!iso || iso.length < 10) return '—';
    return iso.slice(5, 10);
}

// ── 作用域样式注入(.pur · 逐令牌照搬设计稿 · 幂等)──────────────────────
// 视觉照搬闸比对的就是这套注入式作用域 CSS;生产端容器左对齐(marginLeft=0 贴侧栏),令牌逐字搬。
export function injectStyle(id: string, css: string): void {
    if (document.getElementById(id)) return;
    const st = document.createElement('style');
    st.id = id;
    st.textContent = css;
    document.head.appendChild(st);
}

// ── 后端 raw → 前端模型规整(收口契约差异 · 单处适配)──────────────────
// 后端(services/purchase)实际返回:列表=doc 原始列 + supplier_name;详情/建单=嵌套
// {doc, lines, attachments};summary=goods_total/vat_claimable;line 靠 product_id 判匹配;
// 票图走 attachments(kind=bill).url。这些 02 未精确钉 JSON 形,此处一处对齐,页面只认前端模型。
type Raw = Record<string, unknown>;
const numOf = (v: unknown): number => Number(v || 0);

export function normSummary(raw: Raw): DocSummary {
    return {
        purchase_total: numOf(raw.goods_total ?? raw.purchase_total),
        purchase_count: numOf(raw.purchase_count),
        expense_total: numOf(raw.expense_total),
        expense_count: numOf(raw.expense_count),
        vat_creditable: numOf(raw.vat_claimable ?? raw.vat_creditable),
        unpaid_total: numOf(raw.unpaid_total),
        unpaid_suppliers: numOf(raw.unpaid_suppliers),
    };
}

// 精简文档类型:后端给 doc_type 用之,否则从 doc_kind + 有无税票推(列表筛选「文档类型」用)。
function deriveDocType(raw: Raw, kind: DocKind, hasVat: boolean): string {
    const given = (raw.doc_type as string) || '';
    if (given) return given;
    if (kind === 'purchase_order') return 'purchase_order';
    if (hasVat) return kind === 'purchase_invoice' ? 'tax_invoice' : 'simple_tax_receipt';
    return 'receipt';
}

export function normListItem(raw: Raw): DocListItem {
    const kind = (raw.doc_kind as DocKind) || 'expense';
    const hasVat = raw.has_vat != null ? !!raw.has_vat : numOf(raw.vat_amount) > 0;
    return {
        id: String(raw.id),
        doc_date: (raw.doc_date as string) || null,
        supplier_name: (raw.supplier_name as string) || null,
        title: (raw.title as string) || (raw.doc_no as string) || null,
        doc_kind: kind,
        doc_type: deriveDocType(raw, kind, hasVat),
        category_label: (raw.category_label as string) || null,
        source: (raw.source as Source) || 'manual',
        grand_total: numOf(raw.grand_total),
        vat_amount: numOf(raw.vat_amount),
        has_vat: hasVat,
        payment_status: (raw.payment_status as PaymentStatus) || 'unpaid',
        status: (raw.status as DocStatus) || 'posted',
        upload_date:
            (raw.upload_date as string) ||
            (raw.created_at as string) ||
            (raw.doc_date as string) ||
            null,
        attachment_count: numOf(raw.attachment_count),
    };
}

function normLine(raw: Raw): DocLine {
    return {
        id: raw.id != null ? String(raw.id) : undefined,
        item_type: (raw.item_type as ItemType) || 'goods',
        product_id: (raw.product_id as string) || null,
        product_matched: raw.product_id != null,
        description: (raw.description as string) || '',
        qty: numOf(raw.qty),
        unit: (raw.unit as string) || null,
        unit_price: numOf(raw.unit_price),
        discount: numOf(raw.discount),
        vat_rate: numOf(raw.vat_rate),
        wht_rate: numOf(raw.wht_rate),
        category_id: (raw.category_id as string) || null,
        subcategory_id: (raw.subcategory_id as string) || null,
    };
}

// 后端 {doc, lines, attachments}(或已扁平的 mock)→ DocDetail。供应商名后端 get_doc 暂不返(见上报缺口),
// 有 supplier(对象)用之,否则按 supplier_id 占位。票图取 attachments(kind=bill)。
export function normDetail(raw: Raw): DocDetail {
    const doc = (raw.doc as Raw) || raw;
    const atts = ((raw.attachments as Raw[]) || []).map((a) => ({
        id: String(a.id),
        kind: (a.kind as DocAttachment['kind']) || 'bill',
        url: (a.url as string) || null,
        generated: !!a.generated,
    }));
    const lines = ((raw.lines as Raw[]) || (doc.lines as Raw[]) || []).map(normLine);
    const supObj = doc.supplier as Raw | undefined;
    const supplier: Supplier | null = supObj
        ? (supObj as unknown as Supplier)
        : doc.supplier_id != null
          ? ({
                id: String(doc.supplier_id),
                name: (doc.supplier_name as string) || '—',
                tax_id: (doc.supplier_tax_id as string) || null,
                branch_type: 'none',
                branch_no: null,
                address: null,
                phone: null,
                note: null,
                is_active: true,
                total_purchased: 0,
                last_purchase_date: null,
            } as Supplier)
          : null;
    const bill = atts.find((a) => a.kind === 'bill');
    return {
        id: String(doc.id),
        doc_kind: (doc.doc_kind as DocKind) || 'expense',
        status: (doc.status as DocStatus) || 'draft',
        supplier,
        doc_no: (doc.doc_no as string) || null,
        doc_date: (doc.doc_date as string) || null,
        due_date: (doc.due_date as string) || null,
        has_vat: !!doc.has_vat,
        currency: (doc.currency as string) || 'THB',
        source: (doc.source as Source) || 'manual',
        requester: (doc.requester as string) || null,
        lines,
        attachments: atts,
        bill_image_url: (doc.bill_image_url as string) || (bill && bill.url) || null,
        subtotal: numOf(doc.subtotal),
        discount_total: numOf(doc.discount_total),
        vat_amount: numOf(doc.vat_amount),
        wht_amount: numOf(doc.wht_amount),
        rounding: numOf(doc.rounding),
        grand_total: numOf(doc.grand_total),
        net_payable: numOf(doc.net_payable),
        paid_amount: numOf(doc.paid_amount),
        payment_status: (doc.payment_status as PaymentStatus) || 'unpaid',
        stock_applied: !!doc.stock_applied,
    };
}

// 来源 / 票种 → i18n 键(列表/详情共用 · 单一来源防漂移)。
export function srcLabelKey(src: Source): string {
    const m: Record<Source, string> = {
        photo: 'pur-src-photo',
        line: 'pur-src-line',
        upload: 'pur-src-receipt',
        manual: 'pur-src-manual',
    };
    return m[src] || 'pur-src-manual';
}

export function kindLabelKey(kind: DocKind): string {
    const m: Record<DocKind, string> = {
        purchase_invoice: 'pur-kind-invoice',
        expense: 'pur-kind-expense',
        purchase_order: 'pur-kind-order',
    };
    return m[kind] || 'pur-kind-expense';
}

// 采购设置默认值(mock 种子 + 前端 GET 失败回退共用 · 单一来源)。
export const DEFAULT_PURCHASE_SETTINGS: PurchaseSettings = {
    default_vat_rate: 7,
    auto_stock_in: true,
    dedupe_block: true,
    default_due_days: 0,
    pay_needs_approval: false,
    default_wht_service_rate: 3,
    base_currency: 'THB',
    auto_book: false,
};

// ── 共享设计令牌(.pur 作用域 · 逐字搬自设计稿 :root + .btn + .card)──────
// 各屏注入自身页样式前先注入这套基底。容器 .pur .wrap 左对齐(margin:0)贴侧栏 —— 视觉闸要 marginLeft=0;
// 令牌(主色/圆角/阴影/字号)与设计稿逐字相等,闸逐项比对生产页 getComputedStyle。
// PO 全站标准化(2026-06-09 · 风格 B Emerald):.pur 不再自定义令牌,继承全局
// home-01-base :root(浅 + :root.dark 暗夜)→ 换肤/暗夜随令牌翻面,零本地阴影裸值。
// 主按钮 emerald(--accent);.wrap 去小固定宽 → 流式居中填满(对标 history,DESIGN_SYSTEM §2)。
const PUR_BASE_CSS = `
.pur{color:var(--ink);font-size:13.5px;}
.pur *{box-sizing:border-box;}
.pur .tnum{font-variant-numeric:tabular-nums;}
.pur .wrap{width:100%;}
.pur .num{text-align:right;font-variant-numeric:tabular-nums;}
.pur .btn{height:40px;padding:0 15px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--ink);font-size:13.5px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:7px;text-decoration:none;}
.pur .btn.primary{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:700;}
.pur .btn.primary:hover{background:var(--accent-deep);}
.pur .btn.danger{color:var(--red);}
.pur .btn:disabled{opacity:.55;cursor:not-allowed;}
/* .pur .card 只给视觉(无 padding/margin)· 面板内嵌的无边框卡(.preview-pane/.section/.sheet 下)须自行 reset padding:0;margin:0,否则叠加各自 hd/bd 内边距=双重留白 */
.pur .card{background:var(--card);border:1px solid var(--line);border-radius:12px;box-shadow:var(--sh);}
/* 收拢版面板(钉死令牌:圆角16 + 卡阴影 --sh)· 单一来源 · 进项4屏(list/suppliers/settings/inbox)共用 */
.pur .panel{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--sh);overflow:hidden;}
.pur .state{padding:48px 20px;text-align:center;color:var(--ink3);font-size:13px;}
.pur .state .btn{margin-top:12px;}
`;

export function injectPurBase(): void {
    injectStyle('pur-base-css', PUR_BASE_CSS);
}
