// 销项开票向导 PO-10 · 数据与接口:卖方/商品加载 · 税号验真带出(RD)· 建草稿 + 开出
// 接真接口 GET /api/sales/sellers · /api/sales/products · POST /api/rd/verify|lookup ·
// POST /api/sales/documents(+/{id}/issue)。把向导状态映射成后端 DocumentIn 契约。
/* global apiGet, apiPost */
import { type WState, calc, payApplicable } from './sales-wizard-calc.js';

export interface WSeller {
    id: number;
    name?: string;
    tax_id?: string;
    address?: string;
    branch?: string;
    phone?: string;
    promptpay_id?: string;
}
export interface WProduct {
    id: string;
    code?: string;
    name_th?: string;
    name_en?: string;
    name_zh?: string;
    unit?: string;
    unit_price: number;
    vat_applicable: boolean;
    image_url?: string;
}

let sellers: WSeller[] = [];
let products: WProduct[] = [];

export function getSellers(): WSeller[] {
    return sellers;
}
export function getProducts(): WProduct[] {
    return products;
}

export async function loadWizardData(): Promise<void> {
    const [s, p] = await Promise.all([
        apiGet('/api/sales/sellers').catch(() => null),
        apiGet('/api/sales/products').catch(() => null),
    ]);
    sellers = (s && s.sellers) || [];
    products = (p && p.products) || [];
}

// 税号验真(任意类型)→ {valid}
export async function rdVerify(taxId: string): Promise<{ valid: boolean }> {
    const resp = await apiPost('/api/rd/verify', { tax_id: taxId });
    if (!resp || !resp.ok) return { valid: false };
    const data = await resp.json().catch(() => ({}));
    return { valid: !!data.valid };
}

// 一键带出(仅公司)→ 税局登记名称/地址/分店
export interface RdLookup {
    found: boolean;
    name?: string;
    address?: string;
    branch_no?: string;
}
export async function rdLookup(taxId: string, branch = 0): Promise<RdLookup> {
    const resp = await apiPost('/api/rd/lookup', { tax_id: taxId, branch });
    if (!resp || !resp.ok) return { found: false };
    const d = await resp.json().catch(() => ({}));
    return {
        found: !!(d.found || d.name),
        name: d.name || d.company_name,
        address: d.address || d.full_address,
        branch_no: d.branch_no || d.branch,
    };
}

function buildPayload(st: WState) {
    const seller = sellers[st.sellerIdx];
    const c = calc(st);
    const lines = st.lines
        .filter((l) => (l.desc || '').trim())
        .map((l) => ({
            description: l.desc.trim(),
            product_id: l.product_id || null,
            qty: +l.qty || 0,
            unit_price: +l.price || 0,
            discount: +l.disc || 0,
            vat_applicable: !!l.vat,
        }));
    let payment = null;
    if (payApplicable(st)) {
        const paid =
            st.pay.status === 'paid'
                ? c.grand
                : st.pay.status === 'partial'
                  ? +(st.pay.paidAmt || 0)
                  : 0;
        payment = {
            status: st.pay.status,
            paid_amount: paid,
            method: st.pay.method,
            date: st.pay.date,
        };
    }
    return {
        doc_type: st.docType,
        seller_workspace_client_id: seller ? seller.id : null,
        currency: 'THB',
        vat_rate: +st.vatRate || 0,
        wht_rate: +st.whtRate || 0,
        header_discount_amount: +st.hdisc || 0,
        header_discount_pct: 0,
        price_includes_vat: false,
        due_date: st.docType === 'tax_invoice' && st.dueDate ? st.dueDate : null,
        lines,
        buyer: {
            type: st.buyer.type,
            name: st.buyer.name || null,
            address: st.buyer.addr || null,
            tax_id: st.buyer.tin || null,
            branch_type: st.buyer.type === 'company' ? st.buyer.branchType : null,
            branch_no: st.buyer.branchType === 'branch' ? st.buyer.branchNo : null,
        },
        payment,
    };
}

interface SaveResult {
    ok: boolean;
    id?: string;
    error?: string;
}
async function interpret(resp: Response | null): Promise<SaveResult> {
    if (!resp) return { ok: false, error: 'network' };
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) return { ok: false, error: data.detail || 'http_' + resp.status };
    return { ok: true, id: data.document && String(data.document.id) };
}

// 「存入商品库」勾选的自定义行 → 创建为商品主数据(供以后复用)。
// best-effort:单行失败不阻塞存草稿/开票;成功即回填 product_id 并清 save 标志,
// 避免「存草稿→开票」两次都经 saveDraft 时重复创建同一商品。
async function persistSavedLines(st: WState): Promise<void> {
    const targets = st.lines.filter(
        (l) => l.save && l.custom && !l.product_id && (l.desc || '').trim()
    );
    for (const l of targets) {
        try {
            const resp = await apiPost('/api/sales/products', {
                name_th: l.desc.trim(),
                unit_price: +l.price || 0,
                vat_applicable: !!l.vat,
            });
            if (!resp || !resp.ok) continue;
            const d = await resp.json().catch(() => ({}));
            if (d && d.product && d.product.id) l.product_id = String(d.product.id);
            l.save = false;
        } catch (_) {
            /* 单行失败不阻塞主流程 */
        }
    }
}

// 存草稿:首次 POST,已有 draftId 则 PATCH(原始 fetch · apiPost 仅 POST)
export async function saveDraft(st: WState): Promise<SaveResult> {
    const body = buildPayload(st);
    let result: SaveResult;
    if (st.draftId) {
        const { salesFetch } = await import('./sales-common.js');
        const resp = await salesFetch(`/api/sales/documents/${st.draftId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        result = await interpret(resp);
    } else {
        result = await interpret(await apiPost('/api/sales/documents', body));
    }
    if (result.ok) await persistSavedLines(st);
    return result;
}

// 开出:确保有草稿(建/更新)→ POST /{id}/issue
export async function issueDraft(st: WState): Promise<SaveResult> {
    const saved = await saveDraft(st);
    if (!saved.ok || !saved.id) return saved;
    const resp = await apiPost(`/api/sales/documents/${saved.id}/issue`, {
        issue_date: st.issueDate || null,
    });
    const r = await interpret(resp);
    return r.ok ? { ok: true, id: saved.id } : r;
}
