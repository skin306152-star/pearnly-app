// 商户采购 · 前端 mock 兜底(后端 /api/purchase/* 未上线时供 UI 跑起来 · 上线即自动旁路)
// 数据照设计稿 Pearnly_采购_UI预览/ 样例(ทิปโก้/แม็คโคร/打车…),让各屏渲染即像稿、可点通全流程。
// mockHandle 返回的是「已脱信封的 data」(对齐 papi.unwrap 的返回);契约错误抛 PurchaseError。
import {
    PurchaseError,
    type DocDetail,
    type DocListItem,
    type Supplier,
    type Category,
    type PurchaseSettings,
} from './purchase-common.js';

let seq = 1000;
const nid = (pfx: string) => pfx + '-' + ++seq;

const SUPPLIERS: Supplier[] = [
    {
        id: 'sup-1',
        name: 'บริษัท ทิปโก้ จำกัด',
        tax_id: '0105512345678',
        branch_type: 'head_office',
        branch_no: null,
        address: null,
        phone: null,
        note: null,
        is_active: true,
        total_purchased: 182400,
        last_purchase_date: '2026-06-08',
    },
    {
        id: 'sup-2',
        name: 'สยามแม็คโคร',
        tax_id: '0107536000123',
        branch_type: 'head_office',
        branch_no: null,
        address: null,
        phone: null,
        note: null,
        is_active: true,
        total_purchased: 96300,
        last_purchase_date: '2026-06-07',
    },
    {
        id: 'sup-3',
        name: 'ออฟฟิศเมท',
        tax_id: null,
        branch_type: 'none',
        branch_no: null,
        address: null,
        phone: null,
        note: null,
        is_active: true,
        total_purchased: 2180,
        last_purchase_date: '2026-06-06',
    },
];

const LIST: DocListItem[] = [
    mkItem(
        'doc-1',
        '2026-06-08',
        'บริษัท ทิปโก้',
        '进货 12 项',
        'purchase_invoice',
        '进货',
        'photo',
        18190,
        1190,
        'unpaid',
        'tax_invoice',
        3
    ),
    mkItem('doc-2', '2026-06-08', 'แท็กซี่', '打车', 'expense', '交通费', 'line', 200, 0, 'paid'),
    mkItem(
        'doc-3',
        '2026-06-07',
        'การไฟฟ้า',
        '电费',
        'expense',
        '水电费',
        'line',
        1840,
        120,
        'paid'
    ),
    mkItem(
        'doc-4',
        '2026-06-07',
        'สยามแม็คโคร',
        '进货 8 项',
        'purchase_invoice',
        '进货',
        'photo',
        9630,
        630,
        'paid'
    ),
    mkItem(
        'doc-5',
        '2026-06-06',
        'ออฟฟิศเมท',
        '办公用品',
        'expense',
        '办公费',
        'upload',
        560,
        37,
        'paid'
    ),
];

function mkItem(
    id: string,
    date: string,
    sup: string,
    title: string,
    kind: DocListItem['doc_kind'],
    cat: string,
    src: DocListItem['source'],
    grand: number,
    vat: number,
    pay: DocListItem['payment_status'],
    docType?: string,
    atts = 1
): DocListItem {
    const hasVat = vat > 0;
    return {
        id,
        doc_date: date,
        supplier_name: sup,
        title,
        doc_kind: kind,
        doc_type:
            docType ||
            (kind === 'purchase_order'
                ? 'purchase_order'
                : hasVat
                  ? kind === 'purchase_invoice'
                      ? 'tax_invoice'
                      : 'simple_tax_receipt'
                  : 'receipt'),
        category_label: cat,
        source: src,
        grand_total: grand,
        vat_amount: vat,
        has_vat: hasVat,
        payment_status: pay,
        status: 'posted',
        upload_date: date,
        attachment_count: atts,
    };
}

// mock 是 common/mock 循环导入的一端:不在模块顶层读 common 的运行时常量(TDZ),用本地字面量。
const SETTINGS: PurchaseSettings = {
    default_vat_rate: 7,
    auto_stock_in: true,
    dedupe_block: true,
    default_due_days: 0,
    pay_needs_approval: false,
    default_wht_service_rate: 3,
    base_currency: 'THB',
};

const CATEGORIES: Category[] = [
    cat('c1', '进货', [cat('c1a', '商品成本'), cat('c1b', '原材料')]),
    cat('c2', '交通费', [cat('c2a', '打车'), cat('c2b', '油费')]),
    cat('c3', '水电费', [cat('c3a', '水费'), cat('c3b', '电费')]),
    cat('c4', '办公费', [cat('c4a', '文具'), cat('c4b', '设备')]),
    cat('c5', '清洁费', []),
    cat('c6', '租金', []),
    cat('c7', '广告费', []),
    cat('c8', '维修费', []),
    cat('c9', '服务', [cat('c9a', '外包费')]),
];

function cat(id: string, name: string, children: Category[] = []): Category {
    return { id, parent_id: null, name, is_active: true, children };
}

// 详情:屏6 的 Tipco 进项票样例 + 一笔费用样例。其余 list 行点开回退一份精简详情。
const DETAILS: Record<string, DocDetail> = {
    'doc-1': {
        id: 'doc-1',
        doc_kind: 'purchase_invoice',
        status: 'posted',
        supplier: SUPPLIERS[0],
        doc_no: 'INV-25060801',
        doc_date: '2026-06-08',
        due_date: '2026-07-08',
        has_vat: true,
        currency: 'THB',
        source: 'photo',
        requester: 'Patrakorn A.',
        lines: [
            line('โค้ก 325ml', 240, 15, 'goods', true),
            line('น้ำเปล่า 600ml', 600, 6.5, 'goods', true),
            line('ขนมปัง', 80, 22, 'goods', false),
        ],
        attachments: [{ id: 'a1', kind: 'bill', url: null, generated: false }],
        bill_image_url: null,
        subtotal: 17000,
        discount_total: 0,
        vat_amount: 1190,
        wht_amount: 0,
        rounding: 0,
        grand_total: 18190,
        net_payable: 18190,
        paid_amount: 0,
        payment_status: 'unpaid',
        stock_applied: true,
    },
};

function line(desc: string, qty: number, price: number, it: 'goods' | 'service', matched: boolean) {
    return {
        item_type: it,
        product_id: matched ? 'p-' + desc : null,
        product_matched: matched,
        description: desc,
        qty,
        unit: null,
        unit_price: price,
        discount: 0,
        vat_rate: 7,
        wht_rate: it === 'service' ? 3 : 0,
        stock_in: true,
    };
}

function fallbackDetail(id: string): DocDetail {
    const it = LIST.find((d) => d.id === id);
    const supplier = SUPPLIERS.find((s) => s.name === it?.supplier_name) || null;
    const grand = it ? it.grand_total : 0;
    const vat = it ? it.vat_amount : 0;
    return {
        id,
        doc_kind: it ? it.doc_kind : 'expense',
        status: 'posted',
        supplier,
        doc_no: null,
        doc_date: it ? it.doc_date : null,
        due_date: null,
        has_vat: vat > 0,
        currency: 'THB',
        source: it ? it.source : 'manual',
        requester: null,
        lines: [line(it?.title || '—', 1, grand - vat, 'goods', false)],
        attachments: [],
        bill_image_url: null,
        subtotal: grand - vat,
        discount_total: 0,
        vat_amount: vat,
        wht_amount: 0,
        rounding: 0,
        grand_total: grand,
        net_payable: grand,
        paid_amount: it && it.payment_status === 'paid' ? grand : 0,
        payment_status: it ? it.payment_status : 'unpaid',
        stock_applied: false,
    };
}

// 后端 _summary 形:goods_total/expense_total/vat_claimable/unpaid_total(无计数 · normSummary 兼容)。
function summary() {
    return {
        goods_total: 62400,
        expense_total: 8150,
        vat_claimable: 4613,
        unpaid_total: 21000,
    };
}

// 后端 get_doc 形:嵌套 {doc, lines, attachments}(扁平详情包成 doc·normDetail 解包)。
function wrapDetail(d: DocDetail) {
    return { doc: d, lines: d.lines, attachments: d.attachments };
}

// 13 位泰国税号校验(mock 端模拟后端 purchase.tax_id_invalid)。
function badTaxId(tax: unknown): boolean {
    const s = String(tax || '').replace(/\D/g, '');
    return s.length > 0 && s.length !== 13;
}

interface Body {
    [k: string]: unknown;
}

// path 末段 id 解析(/api/purchase/docs/{id}/post → id)。
function seg(path: string, after: string): string {
    const m = path.split('?')[0].split('/');
    const i = m.indexOf(after);
    return i >= 0 && m[i + 1] ? m[i + 1] : '';
}

export function mockHandle(method: string, rawPath: string, payload?: unknown): unknown {
    const path = rawPath.split('?')[0];
    const body = (payload || {}) as Body;

    // ── intake 智能分流(文字→expense / 图→进项票判方向 / 低置信→inbox)──
    if (path === '/api/purchase/intake') {
        if (body.text) {
            return {
                kind: 'expense',
                confidence: 0.96,
                route: 'expense',
                draft: expenseDraft(String(body.text)),
                dedupe_hit: false,
            };
        }
        return {
            kind: 'purchase_invoice',
            confidence: 0.93,
            route: 'purchase',
            draft: invoiceDraft(),
            dedupe_hit: false,
        };
    }
    if (path === '/api/purchase/expense') {
        const doc = expenseDraft(String(body.text || '杂费 0'));
        return {
            doc,
            category: doc.lines[0].category_label,
            substitute_receipt: {
                id: nid('att'),
                kind: 'substitute_receipt',
                generated: true,
                url: null,
            },
        };
    }

    // ── 单据 ──
    if (path === '/api/purchase/docs' && method === 'GET') {
        return { docs: LIST.slice(), summary: summary() };
    }
    if (path === '/api/purchase/docs' && method === 'POST') {
        if (badTaxId((body.supplier as Body)?.tax_id))
            throw new PurchaseError('purchase.tax_id_invalid');
        const id = nid('doc');
        return { doc: { id, status: body.status === 'posted' ? 'posted' : 'draft' } };
    }
    if (path.startsWith('/api/purchase/docs/')) {
        const id = seg(path, 'docs');
        if (path.endsWith('/post'))
            return { doc: { id, status: 'posted' }, stock_applied: SETTINGS.auto_stock_in };
        if (path.endsWith('/pay')) {
            const det = DETAILS[id] || fallbackDetail(id);
            const amt = Number(body.amount || 0);
            const paid = det.paid_amount + amt;
            const status = paid >= det.grand_total ? 'paid' : 'partial';
            return { payment_status: status, paid_amount: paid };
        }
        if (path.endsWith('/void')) return { id, status: 'void' };
        if (path.endsWith('/substitute-receipt'))
            return {
                attachment: {
                    id: nid('att'),
                    kind: 'substitute_receipt',
                    generated: true,
                    url: null,
                },
            };
        if (path.endsWith('/wht-cert'))
            return { attachment: { id: nid('att'), kind: 'wht_cert', generated: true, url: null } };
        if (method === 'DELETE') return { id, deleted: true };
        // GET 详情(后端嵌套形 {doc,lines,attachments})
        return wrapDetail(DETAILS[id] || fallbackDetail(id));
    }

    // ── 行/商品 ──
    if (path.includes('/lines/') && path.endsWith('/match-product')) {
        return {
            line_id: seg(path, 'lines'),
            product_id: (body.product_id as string) || nid('p'),
            matched: true,
        };
    }

    // ── 供应商 ──
    if (path === '/api/purchase/suppliers' && method === 'GET')
        return { suppliers: SUPPLIERS.slice() };
    if (path === '/api/purchase/suppliers' && method === 'POST') {
        if (badTaxId(body.tax_id)) throw new PurchaseError('purchase.tax_id_invalid');
        const s: Supplier = {
            id: nid('sup'),
            name: String(body.name || ''),
            tax_id: (body.tax_id as string) || null,
            branch_type: (body.branch_type as Supplier['branch_type']) || 'none',
            branch_no: (body.branch_no as string) || null,
            address: (body.address as string) || null,
            phone: (body.phone as string) || null,
            note: (body.note as string) || null,
            is_active: true,
            total_purchased: 0,
            last_purchase_date: null,
        };
        SUPPLIERS.push(s);
        return { supplier: s };
    }
    if (path.startsWith('/api/purchase/suppliers/')) {
        const id = seg(path, 'suppliers');
        const s = SUPPLIERS.find((x) => x.id === id);
        if (s) Object.assign(s, body);
        return { supplier: s };
    }

    // ── 科目 / 设置 ──
    if (path === '/api/purchase/categories' && method === 'GET')
        return { categories: CATEGORIES.slice() };
    if (path === '/api/purchase/categories')
        return {
            category: {
                id: nid('cat'),
                name: String(body.name || ''),
                parent_id: (body.parent_id as string) || null,
            },
        };
    if (path === '/api/purchase/settings' && method === 'GET') return { ...SETTINGS };
    if (path === '/api/purchase/settings') {
        Object.assign(SETTINGS, body);
        return { ...SETTINGS };
    }
    if (path === '/api/purchase/summary') return summary();

    throw new PurchaseError('purchase.unexpected');
}

function invoiceDraft() {
    return {
        supplier: {
            name: 'บริษัท ทิปโก้ จำกัด',
            tax_id: '0105512345678',
            branch_type: 'head_office',
        },
        doc_no: 'INV-25060801',
        doc_date: '2026-06-08',
        has_vat: true,
        currency: 'THB',
        lines: [
            line('โค้ก 325ml', 240, 15, 'goods', true),
            line('น้ำเปล่า 600ml', 600, 6.5, 'goods', true),
            line('ขนมปัง', 80, 22, 'goods', false),
        ],
        subtotal: 17000,
        vat_amount: 1190,
        wht_amount: 0,
        grand_total: 18190,
        net_payable: 18190,
        ai_fields: 9,
        dedupe_hit: false,
    };
}

function expenseDraft(text: string) {
    const m = text.match(/(\d+(?:\.\d+)?)/);
    const amt = m ? Number(m[1]) : 0;
    const name = text.replace(/[\d.]+/g, '').trim() || '杂费';
    return {
        supplier: null,
        doc_no: null,
        doc_date: '2026-06-08',
        has_vat: false,
        currency: 'THB',
        lines: [
            {
                item_type: 'goods',
                product_id: null,
                description: name,
                qty: 1,
                unit: null,
                unit_price: amt,
                discount: 0,
                vat_rate: 0,
                wht_rate: 0,
                category_label: '其他',
            },
        ],
        subtotal: amt,
        vat_amount: 0,
        wht_amount: 0,
        grand_total: amt,
        net_payable: amt,
    };
}
