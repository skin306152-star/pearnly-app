// 销项开票模块 PO-10 · 共享叶子:类型 / 金额日期格式化 / 单据类型映射 / 带鉴权 fetch
// 纯工具 · 无副作用 · 被 sales-workbench / sales-detail import。t / escapeHtml 用全局。
/* global t, escapeHtml */

export interface SalesLine {
    description?: string;
    qty?: number | string;
    unit_price?: number | string;
    amount?: number | string;
}
export interface SalesDoc {
    id: string;
    doc_type: string;
    doc_number: string | null;
    client_id: number | null;
    issue_date: string | null;
    status: string;
    currency: string;
    subtotal: number | string;
    vat_rate: number | string;
    vat_amount: number | string;
    wht_amount: number | string;
    grand_total: number | string;
    price_includes_vat: boolean;
    due_date: string | null;
    buyer: { type?: string; name?: string; address?: string; tax_id?: string; branch_no?: string };
    payment: { status?: string; paid_amount?: number | string; method?: string; date?: string };
    references_document_id: string | null;
    created_at: string | null;
    lines: SalesLine[];
}

// 单据类型 → i18n key(label 走 t())
export const DOC_TYPE_KEY: Record<string, string> = {
    tax_invoice: 'sx-dt-tax_invoice',
    tax_invoice_receipt: 'sx-dt-tax_invoice_receipt',
    tax_invoice_simple: 'sx-dt-tax_invoice_simple',
    receipt: 'sx-dt-receipt',
    quotation: 'sx-dt-quotation',
    credit_note: 'sx-dt-credit_note',
    debit_note: 'sx-dt-debit_note',
};

export function docTypeLabel(dt: string | null): string {
    const key = dt ? DOC_TYPE_KEY[dt] : null;
    return key ? t(key) : dt || '—';
}

export function fmtMoney(v: number | string | null | undefined): string {
    const n = Number(v || 0);
    return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function fmtDate(iso: string | null | undefined): string {
    return iso ? iso.slice(0, 10) : '—';
}

// 表单初值转义:null/undefined → ''、其余 → escapeHtml(String(v))。用于 value="${...}"。
export function htmlVal(v: string | number | null | undefined): string {
    return escapeHtml(v == null ? '' : String(v));
}

function authHeaders(): Record<string, string> {
    const h: Record<string, string> = {
        Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
    };
    try {
        const ws = window._wsHeader && window._wsHeader();
        if (ws) Object.assign(h, ws);
    } catch (_) {
        /* 切换器未就绪 · 静默 */
    }
    return h;
}

// 带鉴权的原始 fetch(用于 PDF / PromptPay 等非 JSON 响应)。
export function salesFetch(url: string, opts: RequestInit = {}): Promise<Response> {
    return fetch(url, { ...opts, headers: { ...authHeaders(), ...(opts.headers || {}) } });
}
