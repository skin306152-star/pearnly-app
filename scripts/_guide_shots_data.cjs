// 使用教程配图的假接口数据。教程截图不连生产库 —— 公司名/税号/金额全部用示例值,
// 真实客户信息一律不得出现在教程里(图会随 dist 发到所有租户手上)。
// 被 _guide_shots.cjs 的 page.route('**/api/**') 调:apiBody(url, lang) → 命中返回 body 对象,未命中返回 null。
/* eslint-disable no-undef */

// 示例主体:税号取 0105560000011 这类一眼假的号段,公司名统一「ตัวอย่าง(示例)」。
const BUYER_A = 'บริษัท ตัวอย่าง จำกัด';
const BUYER_B = 'บริษัท ตัวอย่างสอง จำกัด';
const BUYER_C = 'ห้างหุ้นส่วนจำกัด ตัวอย่างสาม';
const SELLER = 'บริษัท ตัวอย่างผู้ขาย จำกัด';
const TAX_SELLER = '0105560000011';
const TAX_BUYER = '0105560000029';

const ME = {
    id: 'demo-user',
    username: 'demo',
    email: null,
    account_type: 'lifetime',
    plan: 'lifetime',
    used_this_month: 0,
    can_edit_fields: true,
    can_verify_tax: true,
    can_extract_items: true,
    can_use_gemini: true,
    can_use_typhoon: true,
    can_view_history: true,
    history_retention_days: 365,
    can_push_erp: true,
    can_auto_push_erp: true,
    endpoints_limit: 5,
    can_archive: true,
    can_customize_archive: true,
    zip_batch_limit: 50,
};

// Express 端点:agent_token_tail 让向导第 2 步走「已配置 → 只显掩码 + 重置」分支。
const ENDPOINTS = {
    items: [
        {
            id: 'e1',
            adapter: 'express',
            name: 'Express',
            enabled: true,
            auto_push: true,
            config: {
                agent_last_seen_at: new Date().toISOString(),
                agent_token_tail: 'K7M2',
                agent_device_name: 'ACC-PC',
                account_set: 'C:\\ACCOUNT\\DEMO',
                account_company: BUYER_A,
            },
        },
    ],
};

function histRow(id, at, file, no, buyer, total, vat, status, source) {
    return {
        id,
        created_at: at,
        filename: file,
        invoice_no: no,
        page_count: 1,
        buyer_name: buyer,
        total_amount: total,
        vat_amount: vat,
        status,
        confidence: status === 'confirmed' ? 'high' : 'medium',
        source,
    };
}

const HISTORY_ITEMS = [
    histRow(
        'h-1',
        '2026-07-20T10:24:00',
        'INV-2569-07-01.pdf',
        'INV-2569/0001',
        BUYER_A,
        32100,
        2100,
        'confirmed',
        'upload'
    ),
    histRow(
        'h-2',
        '2026-07-20T10:26:00',
        'INV-2569-07-02.pdf',
        'INV-2569/0002',
        BUYER_B,
        10700,
        700,
        'confirmed',
        'upload'
    ),
    histRow(
        'h-3',
        '2026-07-19T16:02:00',
        'RECEIPT-2569-07-03.jpg',
        'INV-2569/0003',
        BUYER_C,
        5350,
        350,
        'pending',
        'line'
    ),
    histRow(
        'h-4',
        '2026-07-19T15:48:00',
        'INV-2569-07-04.pdf',
        'INV-2569/0004',
        BUYER_A,
        21400,
        1400,
        'confirmed',
        'email'
    ),
    histRow(
        'h-5',
        '2026-07-18T09:12:00',
        'INV-2569-07-05.pdf',
        'INV-2569/0005',
        BUYER_B,
        8560,
        560,
        'confirmed',
        'upload'
    ),
];

const HISTORY = {
    items: HISTORY_ITEMS,
    total: HISTORY_ITEMS.length,
    status_counts: { all: 5, confirmed: 4, pending: 1, failed: 0 },
};

const HISTORY_DETAIL = {
    id: 'h-1',
    filename: 'INV-2569-07-01.pdf',
    page_count: 1,
    elapsed_ms: 2400,
    confidence: 'high',
    created_at: '2026-07-20T10:24:00',
    archive_name: null,
    category_tag: null,
    client_id: null,
    workspace_client_id: null,
    pages: [
        {
            fields: {
                invoice_number: 'INV-2569/0001',
                date: '2026-07-20',
                date_raw: '20/07/2569',
                total_amount: 32100,
                subtotal: 30000,
                vat: 2100,
                seller_name: SELLER,
                seller_tax: TAX_SELLER,
                buyer_name: BUYER_A,
                buyer_tax: TAX_BUYER,
                items: [
                    { name: 'สินค้าตัวอย่าง A', qty: 10, unit_price: 1500, amount: 15000 },
                    { name: 'สินค้าตัวอย่าง B', qty: 5, unit_price: 3000, amount: 15000 },
                ],
            },
        },
    ],
};

function logRow(id, at, no, buyer, status, extra) {
    return Object.assign(
        {
            id,
            created_at: at,
            invoice_no: no,
            ocr_buyer_name: buyer,
            push_type: 'invoice',
            endpoint_name: 'Express',
            http_status: 200,
            elapsed_ms: 1800,
            retry_count: 0,
            max_retries: 3,
            status,
        },
        extra || {}
    );
}

// 四种状态各一条:成功 / 成功但欠成本 / 失败 / 推送中 —— 筛选 chip 那一栏的说明要对得上。
const ERP_LOGS = {
    items: [
        logRow('l-1', '2026-07-20T10:25:00', 'INV-2569/0001', BUYER_A, 'success', {
            trigger: 'auto',
            external_doc_no: 'IV2607-0001',
        }),
        logRow('l-2', '2026-07-20T10:27:00', 'INV-2569/0002', BUYER_B, 'success', {
            trigger: 'auto',
            external_doc_no: 'IV2607-0002',
            uncosted_lines: 2,
        }),
        logRow('l-3', '2026-07-19T16:05:00', 'INV-2569/0003', BUYER_C, 'failed', {
            trigger: 'manual',
            http_status: 422,
            error_msg: 'EXPRESS_MANUAL: no_revenue_account',
            retry_count: 3,
        }),
        logRow('l-4', '2026-07-19T15:50:00', 'INV-2569/0004', BUYER_A, 'pending', {
            trigger: 'auto',
            http_status: null,
        }),
    ],
    total: 4,
};

const ERP_TODAY = { total: 4, success: 2, failed: 1, auto_cnt: 3 };

const EXC_STATS = {
    pending: 3,
    high_severity: 1,
    resolved: 12,
    ignored: 2,
    learned_rules: 4,
    by_rule: { 'R-VAT-01': 1, 'R-TAXID-01': 1, 'R-DUP-01': 1 },
};

function excRow(id, rule, sev, seller, file, no, date, total) {
    return {
        id,
        rule_code: rule,
        severity: sev,
        status: 'pending',
        seller_name: seller,
        filename: file,
        invoice_no: no,
        invoice_date_raw: date,
        total_amount: total,
        created_at: '2026-07-20T10:24:00',
    };
}

const EXC_LIST = {
    items: [
        excRow(
            1,
            'R-VAT-01',
            'high',
            SELLER,
            'INV-2569-07-11.pdf',
            'INV-2569/0011',
            '20/07/2569',
            32100
        ),
        excRow(
            2,
            'R-TAXID-01',
            'medium',
            BUYER_B,
            'INV-2569-07-12.pdf',
            'INV-2569/0012',
            '19/07/2569',
            10700
        ),
        excRow(
            3,
            'R-DUP-01',
            'medium',
            BUYER_C,
            'RECEIPT-2569-07-13.jpg',
            'INV-2569/0013',
            '18/07/2569',
            5350
        ),
    ],
    total: 3,
};

// 服务端 list_templates 的镜像(erp 模板前端自己会滤掉 · sales_detail_th 前端自己会加)。
const TPL_TEXT = {
    input_vat: {
        zh: ['进项税明细 (ภ.พ.30)', '法定报税格式 · 直接交给 RD 税务局'],
        th: ['ภาษีซื้อ (ภ.พ.30)', 'รูปแบบยื่นภาษีตามกฎหมาย · ส่งกรมสรรพากรได้ทันที'],
    },
    standard: {
        zh: ['标准明细', '全字段明细 · 给老板汇报 / 内部审核'],
        th: ['รายการมาตรฐาน', 'รายละเอียดครบ · รายงานเจ้านาย / ตรวจสอบภายใน'],
    },
    print: {
        zh: ['凭证装订清单', 'A4 横版 · 行高大 · 适合打印装订'],
        th: ['ใบรายการสำหรับเย็บเล่ม', 'A4 แนวนอน · บรรทัดสูง · เหมาะสำหรับพิมพ์เย็บเล่ม'],
    },
};

function templates(lang) {
    const lg = TPL_TEXT.input_vat[lang] ? lang : 'zh';
    return {
        ok: true,
        default: 'input_vat',
        templates: Object.keys(TPL_TEXT).map((code) => ({
            code,
            name: TPL_TEXT[code][lg][0],
            desc: TPL_TEXT[code][lg][1],
            recommended: code === 'input_vat',
        })),
    };
}

// 账套主体(套账硬门 / 顶栏切换器 · GET /api/workspace/clients)。
const SUBJECTS = [
    { id: 9001, name: BUYER_A, tax_id: TAX_BUYER, invoice_count: 128 },
    { id: 9002, name: BUYER_B, tax_id: '0105560000037', invoice_count: 46 },
    { id: 9003, name: BUYER_C, tax_id: '0105560000045', invoice_count: 7 },
];

const CREDITS = { is_owner: true, is_billing_exempt: false, balance_thb: 1250 };

// 复核屏两张票:第一张缺发票号 —— 核心六格里那一格是黄底,教程正文教的正是「先补黄底的」;
// 第二张字段齐全,同屏能看到「需确认」与「可通过」两种状态。
function ocrResult(second) {
    const fields = {
        direction: 'purchase',
        seller_name: SELLER,
        seller_tax: TAX_SELLER,
        buyer_name: BUYER_A,
        buyer_tax: TAX_BUYER,
        invoice_number: second ? 'INV-2569/0002' : '',
        date: '2026-07-20',
        date_raw: '20/07/2569',
        subtotal: second ? 10000 : 30000,
        vat: second ? 700 : 2100,
        total_amount: second ? 10700 : 32100,
        wht_amount: '',
        items: second
            ? [{ name: 'ค่าขนส่ง ตัวอย่าง', qty: 1, price: 10000, subtotal: 10000 }]
            : [
                  { name: 'สินค้าตัวอย่าง A', qty: 10, price: 1500, subtotal: 15000 },
                  { name: 'สินค้าตัวอย่าง B', qty: 5, price: 3000, subtotal: 15000 },
              ],
    };
    const hid = second ? 'h-2' : 'h-1';
    return {
        filename: second ? 'INV-2569-07-02.pdf' : 'INV-2569-07-01.pdf',
        history_id: hid,
        history_ids: [hid],
        invoice_count: 1,
        needs_review: false,
        invoices: [
            { fields, history_id: hid, source_index: 1, source_total: 1, page_indices: [1] },
        ],
    };
}

// 复核屏右侧的原图查看器要一张真图(/api/history/{id}/page/{n}.png)。放灰色占位块讲不出
// 「边看原件边改字段」,所以排一张示例泰文税票、由 _guide_shots.cjs 渲成 PNG 回给页面。
const INVOICE_HTML = `<style>
  body{margin:0;font:13px/1.7 "Sarabun","Noto Sans Thai",system-ui;background:#fff;color:#111;padding:44px 46px}
  h1{font-size:19px;margin:0 0 2px;letter-spacing:.5px}
  .sub{color:#666;font-size:12px;margin-bottom:22px}
  .box{border:1px solid #d5d5d5;padding:14px 16px;border-radius:4px;margin-bottom:14px}
  .box b{display:block;font-size:12px;color:#666;font-weight:600;margin-bottom:3px}
  table{width:100%;border-collapse:collapse;margin-top:6px}
  th,td{border:1px solid #d5d5d5;padding:8px 10px;text-align:left}
  th{background:#f4f4f4;font-size:12px}
  td.r,th.r{text-align:right}
  .tot{margin-top:18px;width:52%;margin-left:auto}
  .tot div{display:flex;justify-content:space-between;padding:5px 0}
  .tot .g{border-top:1px solid #111;font-weight:700;margin-top:4px;padding-top:8px}
  .meta{display:flex;gap:44px;margin-bottom:16px;font-size:12px}
</style>
<h1>ใบกำกับภาษี / ใบส่งของ</h1>
<div class="sub">TAX INVOICE — ตัวอย่างประกอบคู่มือ (ไม่ใช่เอกสารจริง)</div>
<div class="meta"><div><b>เลขที่ / No.</b>INV-2569/0001</div><div><b>วันที่ / Date</b>20/07/2569</div></div>
<div class="box"><b>ผู้ขาย / Seller</b>${SELLER}<br>เลขประจำตัวผู้เสียภาษี ${TAX_SELLER}</div>
<div class="box"><b>ผู้ซื้อ / Buyer</b>${BUYER_A}<br>เลขประจำตัวผู้เสียภาษี ${TAX_BUYER}</div>
<table><thead><tr><th>รายการ</th><th class="r">จำนวน</th><th class="r">ราคา</th><th class="r">จำนวนเงิน</th></tr></thead>
<tbody>
  <tr><td>สินค้าตัวอย่าง A</td><td class="r">10</td><td class="r">1,500</td><td class="r">15,000</td></tr>
  <tr><td>สินค้าตัวอย่าง B</td><td class="r">5</td><td class="r">3,000</td><td class="r">15,000</td></tr>
</tbody></table>
<div class="tot">
  <div><span>รวมเป็นเงิน</span><span>30,000</span></div>
  <div><span>ภาษีมูลค่าเพิ่ม 7%</span><span>2,100</span></div>
  <div class="g"><span>จำนวนเงินรวมทั้งสิ้น</span><span>32,100</span></div>
</div>`;

// url → body。命中顺序按前缀,最长/最具体的先判。
function apiBody(url, lang) {
    const p = url.split('?')[0];
    if (p.endsWith('/api/me')) return ME;
    if (p.endsWith('/api/me/credits')) return CREDITS;
    if (p.endsWith('/api/workspace/clients')) return { clients: SUBJECTS };
    if (p.endsWith('/api/erp/endpoints')) return ENDPOINTS;
    if (p.endsWith('/api/erp/stats/today')) return ERP_TODAY;
    if (p.endsWith('/api/erp/logs')) return ERP_LOGS;
    if (p.endsWith('/api/reports/templates')) return templates(lang);
    if (p.endsWith('/api/exceptions/stats')) return EXC_STATS;
    if (p.endsWith('/api/exceptions/list')) return EXC_LIST;
    if (/\/api\/history\/[^/]+$/.test(p)) return HISTORY_DETAIL;
    if (p.endsWith('/api/history')) return HISTORY;
    return null;
}

module.exports = { apiBody, ocrResult, INVOICE_HTML, SUBJECTS };
