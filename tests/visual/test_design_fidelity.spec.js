/*
 * 视觉照搬机械闸(docs/pos/12-visual-fidelity-gate.md)· 治"施工不照搬设计稿反复返工"。
 *
 * 对每个照搬稿页:把【设计稿 file://】与【生产页本地渲染】的关键元素 getComputedStyle 逐项比对:
 * 主色 Purple v2 #7C4DFF(rgb(124,77,255))/ 圆角 / box-shadow / font-size / font-family / 无 emoji(线性 svg);
 * 容器另查"左对齐不居中飘"(marginLeft=0,不 auto)。不一致 = 退出码 1 + 打印 哪页/哪选择器/稿X 生产Y。
 *
 * 自洽跑(无需真账号 / 真后端):内置静态服务器伺服 repo + stub 所有 /api/**,渲染本地 dist 真 bundle。
 * 跑法:node tests/visual/test_design_fidelity.spec.js  · 挂 pre-push(改 static/pos 或 src/home/{pos,inventory,purchase}-*)。
 * 加新页怎么补映射:见 README「视觉照搬闸」段 + 本文件 MAPPINGS 数组。
 */
/* eslint-disable no-undef, no-console */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..', '..');
// 设计稿快照入库(tests/visual/design/)→ 闸自洽:pre-push + CI 都能跑(不依赖桌面)。
// 设计稿改了 → 更新这里的快照副本(README「视觉照搬闸」段)。
const DESIGN_DIR = path.join(__dirname, 'design');
const PORT = 8791;
const DEFAULT_PRIMARY = 'rgb(124, 77, 255)'; // Purple v2 --accent #7C4DFF

// stub:让生产页在无后端下渲染到目标子页。
const API = {
    '/api/me': {
        id: 'u1',
        username: 'designgate',
        role: 'owner',
        is_super_admin: false,
        tenant_id: 't1',
    },
    '/api/ocr/quota': { used: 0, limit: 100 },
    // S7(2026-06-10):充值按钮与余额卡同生死 · stub 需 owner+余额才渲染 dashboard 主按钮
    '/api/me/credits': { is_owner: true, is_billing_exempt: false, balance_thb: 100 },
    '/api/me/plan': {},
    '/api/contact': {},
    '/api/me/modules': {
        ok: true,
        data: {
            modules: { pos: { enabled: true }, inventory: { enabled: true } },
            business_type: 'restaurant',
            needs_onboarding: false,
        },
    },
    '/api/pos/admin/restaurant/areas': {
        ok: true,
        data: { areas: [{ id: 1, name: '大厅', is_active: true, table_count: 2 }] },
    },
    '/api/pos/admin/restaurant/tables': {
        ok: true,
        data: {
            tables: [
                { id: 1, name: 'A1', area_id: 1, seats: 4, is_active: true },
                { id: 2, name: 'A2', area_id: 1, seats: 2, is_active: false },
            ],
        },
    },
    '/api/pos/admin/payment-settings': {
        ok: true,
        data: {
            promptpay_enabled: true,
            card_enabled: true,
            service_charge_rate: '10',
            price_includes_vat: true,
            promptpay_id: '',
        },
    },
    // 做账 Phase 2(屏1/2/3/5/4):列表带待审 → 主屏行动卡/逐笔审有内容渲染
    '/api/accounting/vouchers': {
        ok: true,
        data: {
            summary: { auto_count: 244, posted_count: 245, pending_count: 1 },
            items: [
                {
                    id: 'v1',
                    voucher_no: 'JV2606-0001',
                    voucher_date: '2026-06-08',
                    period: '2026-06',
                    source_type: 'purchase',
                    description: '向 ทิปโก้ 进货付款',
                    rule_key: 'R1',
                    confidence: 95,
                    method: 'auto',
                    status: 'auto_posted',
                    total_debit: 18190,
                    total_credit: 18190,
                },
                {
                    id: 'v2',
                    voucher_no: 'JV2606-0002',
                    voucher_date: '2026-06-07',
                    period: '2026-06',
                    source_type: 'payment',
                    description: '付设计服务费(含预扣税)',
                    rule_key: 'R2',
                    confidence: 60,
                    method: 'suggested',
                    status: 'pending_review',
                    review_reason: 'suggest_mode',
                    total_debit: 10700,
                    total_credit: 10700,
                },
            ],
        },
    },
    '/api/accounting/vouchers/v2': {
        ok: true,
        data: {
            voucher: {
                id: 'v2',
                voucher_no: 'JV2606-0002',
                voucher_date: '2026-06-07',
                period: '2026-06',
                source_type: 'payment',
                description: '付设计服务费(含预扣税)',
                human_note: '选「服务」会自动多一笔代扣,实付对方少 300。',
                rule_key: 'R2',
                method: 'suggested',
                status: 'pending_review',
                review_reason: 'suggest_mode',
                total_debit: 10700,
                total_credit: 10700,
                lines: [
                    {
                        id: 'l1',
                        account_id: 'a1',
                        account_code: '5210',
                        account_name: '外包服务费',
                        dr_cr: 'debit',
                        amount: 10000,
                    },
                    {
                        id: 'l2',
                        account_id: 'a2',
                        account_code: '1140',
                        account_name: '进项税',
                        dr_cr: 'debit',
                        amount: 700,
                    },
                    {
                        id: 'l3',
                        account_id: 'a3',
                        account_code: '1020',
                        account_name: '银行存款',
                        dr_cr: 'credit',
                        amount: 10400,
                    },
                    {
                        id: 'l4',
                        account_id: 'a4',
                        account_code: '2050',
                        account_name: '预扣税应缴',
                        dr_cr: 'credit',
                        amount: 300,
                    },
                ],
            },
        },
    },
    '/api/accounting/review': {
        ok: true,
        data: {
            count: 1,
            items: [
                {
                    id: 'v2',
                    voucher_no: 'JV2606-0002',
                    source_type: 'payment',
                    description: '付设计服务费(含预扣税)',
                    status: 'pending_review',
                    review_reason: 'suggest_mode',
                    total_debit: 10700,
                    total_credit: 10700,
                },
            ],
        },
    },
    '/api/accounting/accounts': {
        ok: true,
        data: {
            accounts: [
                {
                    id: 'a1',
                    code: '1010',
                    name_zh: '现金',
                    name_th: 'เงินสด',
                    acct_type: 'asset',
                    is_preset: true,
                    is_active: true,
                },
                {
                    id: 'a2',
                    code: '2010',
                    name_zh: '应付账款',
                    name_th: 'เจ้าหนี้การค้า',
                    acct_type: 'liability',
                    is_preset: true,
                    is_active: true,
                },
                {
                    id: 'a3',
                    code: '4010',
                    name_zh: '销售收入',
                    name_th: 'รายได้จากการขาย',
                    acct_type: 'revenue',
                    is_preset: true,
                    is_active: true,
                },
            ],
        },
    },
    '/api/accounting/settings': {
        ok: true,
        data: {
            settings: {
                auto_post: false,
                auto_post_threshold: 90,
                auto_post_rules: {},
                accounting_standard: 'TFRS_NPAE',
                inventory_method: 'periodic',
                base_currency: 'THB',
                start_period: '2026-06',
                closed_through: null,
            },
        },
    },
    '/api/accounting/learned': { ok: true, data: { items: [] } },
    '/api/accounting/bank/accounts': {
        ok: true,
        data: {
            accounts: [
                {
                    id: 'ba1',
                    bank_code: 'KBANK',
                    account_last4: '1234',
                    coa_account_id: 'a1',
                    is_active: true,
                },
            ],
        },
    },
    '/api/accounting/bank/summary': {
        ok: true,
        data: {
            summary: {
                bank_balance: 412350,
                book_balance: 400000,
                difference: 12350,
                balance_gap: 12350,
                unmatched_net: 12350,
                total_count: 5,
                matched_count: 3,
                unmatched_count: 2,
                progress: 0.6,
                done: false,
            },
        },
    },
    '/api/accounting/bank/lines': {
        ok: true,
        data: {
            count: 1,
            items: [
                {
                    id: 'l1',
                    line_date: '2026-06-08',
                    amount: 18190,
                    direction: 'out',
                    description: '向供应商转账',
                    bank_ref: '转账',
                    status: 'unmatched',
                },
            ],
        },
    },
    '/api/accounting/bank/lines/l1/candidates': {
        ok: true,
        data: {
            candidates: [
                {
                    kind: 'voucher',
                    action: 'link',
                    voucher_id: 'v1',
                    label: '付款凭证 #0248',
                    date: '2026-06-08',
                    amount: 18190,
                    score: 95,
                    reason: '金额一致 · 日期差 0 天',
                },
            ],
        },
    },
    '/api/accounting/voucher-templates': { ok: true, data: { templates: [] } },
};

// 映射表:稿 ↔ 生产路由 ↔ 关键选择器比对项。
// token: 设计选择器 vs 生产选择器,getComputedStyle props 必须相等。
// layout: 仅查生产容器左对齐(marginLeft=0)。
const MAPPINGS = [
    {
        name: '首页 dashboard(样板 · A组屏)',
        design: 'dashboard-final.html',
        route: 'dashboard',
        ready: '#page-dashboard .band .btn.pri',
        layout: { sel: '#page-dashboard .wrap', maxWidth: 'none', centered: true },
        tokens: [
            {
                design: '.btn',
                prod: '#page-dashboard .band .btn.pri',
                props: ['backgroundColor', 'borderRadius', 'fontSize'],
            },
            {
                design: '.panel',
                prod: '#page-dashboard .panel',
                props: ['borderRadius', 'boxShadow'],
            },
        ],
        bluemust: '#page-dashboard .band .btn.pri',
        nosvgemoji: '#page-dashboard .qa .qb svg',
    },
    {
        name: '上传识别 OCR(A组屏)',
        design: 'ocr.html',
        route: 'ocr',
        ready: '#page-ocr .panel',
        layout: { sel: '#page-ocr .wrap', maxWidth: 'none', centered: true },
        tokens: [
            // #btn-start 开始时 disabled → home-38 .btn:disabled!important 覆盖背景色 → 测 panel 代替
            { design: '.panel', prod: '#page-ocr .panel', props: ['borderRadius', 'boxShadow'] },
            { design: '.h1', prod: '#page-ocr .pagehead .h1', props: ['fontSize', 'fontWeight'] },
        ],
        // 无 bluemust:所有操作按钮初始 disabled,颜色被 home-38 disabled!important 覆盖(正确行为)
        nosvgemoji: '#page-ocr .drop-zone svg',
    },
    {
        name: '识别记录 history(A组屏)',
        design: 'history.html',
        route: 'history',
        ready: '#page-history .pagehead',
        layout: { sel: '#page-history .wrap', maxWidth: 'none', centered: true },
        tokens: [
            // #history-main 初始 display:none — getComputedStyle 仍计算结构属性(borderRadius/boxShadow)
            { design: '.panel', prod: '#history-main', props: ['borderRadius', 'boxShadow'] },
            {
                design: '.h1',
                prod: '#page-history .pagehead .h1',
                props: ['fontSize', 'fontWeight'],
            },
        ],
        // 无 bluemust:history-main 初始隐藏,无可见主色按钮可验
        nosvgemoji: '#history-empty svg',
    },
    {
        name: '对账中心 reconcile(A组屏)',
        design: 'reconcile.html',
        route: 'reconcile',
        ready: '#page-reconcile .pagehead',
        layout: { sel: '#page-reconcile .wrap', maxWidth: 'none', centered: true },
        tokens: [
            {
                design: '.h1',
                prod: '#page-reconcile .pagehead .h1',
                props: ['fontSize', 'fontWeight'],
            },
            {
                design: '.recon-tab-btn.active',
                prod: '.recon-tab-btn.active',
                props: ['boxShadow', 'borderRadius'],
            },
        ],
        // 无 bluemust:对账中心 tab 用中性色(白底·非主色)
        nosvgemoji: '.recon-tab-btn.active svg',
    },
    {
        name: '销售工作台 sales-invoices(A组屏)',
        design: 'sales-invoices.html',
        route: 'sales-invoices',
        ready: '#sx-new-btn',
        layout: { sel: '#page-sales-invoices .wrap', maxWidth: 'none', centered: true },
        tokens: [
            {
                design: '.btn-primary',
                prod: '#sx-new-btn',
                props: ['backgroundColor', 'borderRadius'],
            },
            {
                design: '.h1',
                prod: '#page-sales-invoices .pagehead .h1',
                props: ['fontSize', 'fontWeight'],
            },
        ],
        bluemust: '#sx-new-btn',
        nosvgemoji: '#sx-new-btn svg',
    },
    {
        name: '客户管理 clients(A组屏)',
        design: 'clients.html',
        route: 'clients',
        ready: '#page-clients .pagehead .h1',
        layout: { sel: '#page-clients .wrap', maxWidth: 'none', centered: true },
        tokens: [
            {
                design: '.h1',
                prod: '#page-clients .pagehead .h1',
                props: ['fontSize', 'fontWeight'],
            },
        ],
        // 无 bluemust:seller 面板 #btn-seller-new display:none · buyer 面板初始隐藏
        nosvgemoji: '.cust-tab-bar .recon-tab-btn svg',
    },
    {
        name: '销售报表 sales-report(A组屏)',
        design: 'sales-report.html',
        route: 'sales-report',
        ready: '.posrep .ph .t',
        layout: { sel: '.posrep .wrap', maxWidth: 'none', centered: true },
        tokens: [
            // 报表头字体照搬 home-43-pos-report.css(.posrep .ph .t) · 19px 非 kit 22px
            { design: '.ph .t', prod: '.posrep .ph .t', props: ['fontSize', 'fontWeight'] },
        ],
        // 无 bluemust:报表页无 primary 按钮 · 无 nosvgemoji:范围选择栏文字按钮无 SVG
    },
    {
        name: '桌台管理(05 v2)',
        design: '05-tables.html',
        route: 'pos-tables',
        ready: '.ptbl .btn.primary',
        layout: { sel: '.ptbl', maxWidth: 'none', centered: true }, // B6d:去 max-width:960px → 真铺满
        tokens: [
            {
                design: '.btn.primary',
                prod: '.ptbl .btn.primary',
                props: ['backgroundColor', 'borderRadius', 'fontSize'],
            },
            { design: '.btn', prod: '.ptbl .btn', props: ['backgroundColor', 'borderRadius'] },
            { design: '.card', prod: '.ptbl .card', props: ['borderRadius', 'boxShadow'] },
            { design: '.zone', prod: '.ptbl .zone', props: ['borderRadius'] },
            { design: '.t', prod: '.ptbl .t', props: ['borderRadius'] },
        ],
        bluemust: '.ptbl .btn.primary',
        nosvgemoji: '.ptbl .btn.primary svg',
    },
    {
        name: '收款设置(13)',
        design: '13-payment.html',
        route: 'pos-payment',
        ready: '.rpay .save',
        layout: { sel: '.rpay', maxWidth: 'none', centered: true }, // B6e:去 max-width:760px → 真铺满
        tokens: [
            { design: '.save', prod: '.rpay .save', props: ['backgroundColor', 'borderRadius'] },
            { design: '.card', prod: '.rpay .card', props: ['borderRadius'] },
        ],
        bluemust: '.rpay .save',
        nosvgemoji: '.rpay .pm .ic svg',
    },
    {
        name: '采购/进项主屏(01 收拢版)',
        design: 'pur-list.html',
        route: 'purchase',
        ready: '.pur .btn.primary',
        layout: { sel: '.pur .wrap', maxWidth: 'none', centered: true },
        tokens: [
            {
                design: '.btn.primary',
                prod: '.pur .btn.primary',
                props: ['backgroundColor', 'borderRadius', 'fontSize'],
            },
            { design: '.panel', prod: '.pur .panel', props: ['borderRadius', 'boxShadow'] },
            { design: '.seg .o', prod: '.pur .seg .o', props: ['borderRadius'] },
        ],
        bluemust: '.pur .btn.primary',
        nosvgemoji: '.pur .btn.primary svg',
    },
    {
        name: '费用/进项录入(10)',
        design: 'pur-form.html',
        route: 'purchase-form',
        ready: '.pur .btn.primary',
        layout: { sel: '.pur .wrap', maxWidth: 'none', centered: true },
        tokens: [
            {
                design: '.btn.primary',
                prod: '.pur .btn.primary',
                props: ['backgroundColor', 'borderRadius', 'fontSize'],
            },
            { design: '.card', prod: '.pur .card', props: ['borderRadius', 'boxShadow'] },
        ],
        bluemust: '.pur .btn.primary',
        nosvgemoji: '.pur .img svg',
    },
    {
        name: '单据详情(06)',
        design: 'pur-detail.html',
        route: 'purchase-detail',
        pre: () => window.openPurchaseDetail && window.openPurchaseDetail('doc-1'),
        ready: '.pur .btn.primary',
        layout: { sel: '.pur .wrap', maxWidth: 'none', centered: true },
        tokens: [
            {
                design: '.btn.primary',
                prod: '.pur .btn.primary',
                props: ['backgroundColor', 'borderRadius'],
            },
            { design: '.card', prod: '.pur .card', props: ['borderRadius', 'boxShadow'] },
        ],
        bluemust: '.pur .btn.primary',
        nosvgemoji: '.pur .img svg',
    },
    {
        name: '供应商管理(04 收拢版)',
        design: 'pur-suppliers.html',
        route: 'purchase-suppliers',
        ready: '.pur .add',
        layout: { sel: '.pur .wrap', maxWidth: 'none', centered: true },
        tokens: [
            {
                design: '.btn',
                prod: '.pur .add',
                props: ['backgroundColor', 'borderRadius', 'fontSize'],
            },
            { design: '.panel', prod: '.pur .panel', props: ['borderRadius', 'boxShadow'] },
        ],
        bluemust: '.pur .add',
        nosvgemoji: '.pur .add svg',
    },
    {
        name: '采购设置(05 收拢版)',
        design: 'pur-settings.html',
        route: 'purchase-settings',
        ready: '.pur .save',
        layout: { sel: '.pur .wrap', maxWidth: 'none', centered: true },
        tokens: [
            {
                design: '.btn',
                prod: '.pur .save',
                props: ['backgroundColor', 'borderRadius', 'fontSize'],
            },
            { design: '.panel', prod: '.pur .panel', props: ['borderRadius', 'boxShadow'] },
        ],
        bluemust: '.pur .save',
        nosvgemoji: '.pur .addcat svg',
    },
    {
        name: '做账主屏(01 收拢版)',
        design: 'acct-list.html',
        route: 'vouchers',
        ready: '#acct-star',
        layout: { sel: '#page-vouchers .acct .wrap', maxWidth: 'none', centered: true },
        tokens: [
            {
                design: '.panel',
                prod: '#page-vouchers .acct .panel',
                props: ['borderRadius', 'boxShadow'],
            },
            {
                design: '.ph .t',
                prod: '#page-vouchers .acct .ph .t',
                props: ['fontSize', 'fontWeight'],
            },
            {
                design: '.mctl .exp',
                prod: '#acct-books-btn',
                props: ['backgroundColor', 'borderRadius'],
            },
        ],
        bluemust: '#acct-books-btn',
    },
    {
        name: '做账逐笔审(02)',
        design: 'acct-review.html',
        route: 'acct-review',
        ready: '#page-acct-review .led',
        layout: { sel: '#page-acct-review .acct .wrap', maxWidth: 'none', centered: true },
        tokens: [
            {
                design: '.panel',
                prod: '#page-acct-review .acct .panel',
                props: ['borderRadius', 'boxShadow'],
            },
            {
                design: '.btn.primary',
                prod: '#page-acct-review [data-act="confirm"]',
                props: ['backgroundColor', 'borderRadius', 'fontSize'],
            },
        ],
        bluemust: '#page-acct-review [data-act="confirm"]',
    },
    {
        name: '做账科目表(03)',
        design: 'acct-accounts.html',
        route: 'acct-accounts',
        ready: '#acct-acc-add',
        layout: { sel: '#page-acct-accounts .acct .wrap', maxWidth: 'none', centered: true },
        tokens: [
            {
                design: '.panel',
                prod: '#page-acct-accounts .acct .panel',
                props: ['borderRadius', 'boxShadow'],
            },
            {
                design: '.btn.primary',
                prod: '#acct-acc-add',
                props: ['backgroundColor', 'borderRadius', 'fontSize'],
            },
        ],
        bluemust: '#acct-acc-add',
    },
    {
        name: '做账设置(05)',
        design: 'acct-settings.html',
        route: 'acct-settings',
        ready: '#acct-set-save',
        layout: { sel: '#page-acct-settings .acct .wrap', maxWidth: 'none', centered: true },
        tokens: [
            {
                design: '.panel',
                prod: '#page-acct-settings .acct .panel',
                props: ['borderRadius', 'boxShadow'],
            },
            {
                design: '.foot .btn',
                prod: '#acct-set-save',
                props: ['backgroundColor', 'borderRadius', 'fontSize'],
            },
        ],
        bluemust: '#acct-set-save',
    },
    {
        name: '做账出账本/报税包(04)',
        design: 'acct-books.html',
        route: 'acct-books',
        ready: '#acct-books-pack',
        layout: { sel: '#page-acct-books .acct .wrap', maxWidth: 'none', centered: true },
        tokens: [
            {
                design: '.panel',
                prod: '#page-acct-books .acct .panel',
                props: ['borderRadius', 'boxShadow'],
            },
            {
                design: '.btn.primary',
                prod: '#acct-books-pack',
                props: ['backgroundColor', 'borderRadius'],
            },
        ],
        bluemust: '#acct-books-pack',
    },
    {
        name: '银行对账(bank-recon-mj 01)',
        design: 'acct-bank.html',
        route: 'acct-bank',
        ready: '#page-acct-bank .ab .band',
        layout: { sel: '#page-acct-bank .ab', maxWidth: 'none', centered: false },
        tokens: [
            {
                design: '.panel',
                prod: '#page-acct-bank .ab .panel',
                props: ['borderRadius', 'boxShadow'],
            },
            {
                design: '.ph .t',
                prod: '#page-acct-bank .ab .ph .t',
                props: ['fontSize', 'fontWeight'],
            },
            {
                design: '.btn.primary',
                prod: '#page-acct-bank .ab .btn.primary',
                props: ['backgroundColor', 'borderRadius', 'fontSize'],
            },
        ],
        bluemust: '#page-acct-bank .ab .btn.primary',
    },
    {
        name: '手工凭证(bank-recon-mj 02)',
        design: 'acct-manual.html',
        route: 'acct-manual',
        ready: '#page-acct-manual .mjx table.mj',
        layout: { sel: '#page-acct-manual .mjx', maxWidth: 'none', centered: false },
        tokens: [
            {
                design: '.panel',
                prod: '#page-acct-manual .mjx .panel',
                props: ['borderRadius', 'boxShadow'],
            },
            {
                design: '.ph .t',
                prod: '#page-acct-manual .mjx .ph .t',
                props: ['fontSize', 'fontWeight'],
            },
            {
                // 过账按钮初始禁用(空/未配平)→ 灰底是正确禁用态;主色已由银行屏同一 .btn.primary 规则验证
                design: '.btn.primary',
                prod: '#page-acct-manual .mjx .btn.primary',
                props: ['borderRadius', 'fontSize'],
            },
        ],
    },
];

const fails = [];
const ok = (c, m) => {
    if (!c) {
        fails.push(m);
        console.log('  ❌ ' + m);
    } else console.log('  ✅ ' + m);
};

function serveStatic() {
    const types = {
        '.js': 'application/javascript',
        '.css': 'text/css',
        '.html': 'text/html',
        '.map': 'application/json',
        '.webmanifest': 'application/json',
        '.png': 'image/png',
        '.svg': 'image/svg+xml',
    };
    const srv = http.createServer((req, res) => {
        let p = decodeURIComponent(req.url.split('?')[0]);
        if (p === '/home') p = '/home.html';
        const file = path.join(ROOT, p);
        if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
            res.writeHead(404);
            return res.end('nf');
        }
        res.writeHead(200, {
            'content-type': types[path.extname(file)] || 'text/plain',
            'cache-control': 'no-store',
        });
        fs.createReadStream(file).pipe(res);
    });
    return new Promise((r) => srv.listen(PORT, () => r(srv)));
}

async function styleOf(page, sel, props) {
    return await page.evaluate(
        ([s, ps]) => {
            const el = document.querySelector(s);
            if (!el) return null;
            const cs = getComputedStyle(el);
            const out = {};
            ps.forEach((p) => (out[p] = cs[p]));
            out.fontFamily = cs.fontFamily;
            return out;
        },
        [sel, props]
    );
}

(async () => {
    const srv = await serveStatic();
    const browser = await chromium.launch();
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await ctx.newPage();
    await page.route('**/api/**', (route) => {
        const u = new URL(route.request().url());
        // 采购模块:后端未上线时 papi 走前端 mock 兜底(purchase-mock)· 这里回 404 触发兜底,让页渲染真 mock 数据。
        if (u.pathname.startsWith('/api/purchase/')) {
            return route.fulfill({ status: 404, contentType: 'application/json', body: '{}' });
        }
        const body = API[u.pathname] !== undefined ? API[u.pathname] : { ok: true, data: {} };
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
    });
    await ctx.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'designgate.fake.token');
        localStorage.setItem('mrpilot_lang', 'zh');
        localStorage.setItem('pearnly_work_mode', 'personal');
    });

    for (const m of MAPPINGS) {
        console.log('\n[' + m.name + ']');
        // 1) 设计稿基线
        const designFile = 'file://' + path.join(DESIGN_DIR, m.design).replace(/\\/g, '/');
        await page.goto(designFile, { waitUntil: 'domcontentloaded' });
        const expected = {};
        for (const tk of m.tokens) expected[tk.design] = await styleOf(page, tk.design, tk.props);

        // 2) 生产页本地渲染
        await page
            .goto('http://localhost:' + PORT + '/home', { waitUntil: 'domcontentloaded' })
            .catch(() => {});
        // bundle 就绪 = routeTo 在(各页 loader 由 routeTo 经 ROUTE_LOADERS 表调度,无需逐个探)。
        // 数据驱动:加新页只往 MAPPINGS 加一项即可,这里不必改(曾写死 loadPosTables/loadPosPayment → 加页必踩)。
        const fnReady = await page
            .waitForFunction(() => typeof window.routeTo === 'function', { timeout: 20000 })
            .then(() => true)
            .catch(() => false);
        ok(fnReady, '生产 bundle 就绪');
        if (!fnReady) continue;
        await page.evaluate(() => {
            window.isOwner = () => true;
            window.getActiveWorkspaceClientId = () => 1;
            const st = document.createElement('style');
            st.textContent = '#ws-modal{display:none!important;}';
            document.head.appendChild(st);
        });
        // 进路由前可选预置(如详情屏需先 openPurchaseDetail 置当前单据 id)。
        if (m.pre) await page.evaluate(m.pre);
        await page.evaluate((r) => window.routeTo(r), m.route);
        const rendered = await page
            .waitForSelector(m.ready, { timeout: 15000 })
            .then(() => true)
            .catch(() => false);
        ok(rendered, '生产页渲染 ' + m.ready);
        if (!rendered) continue;

        // 3) 容器左对齐(不居中飘)+ max-width
        const lay = await page.evaluate((s) => {
            const el = document.querySelector(s);
            if (!el) return null;
            const cs = getComputedStyle(el);
            return {
                maxWidth: cs.maxWidth,
                marginLeft: cs.marginLeft,
                marginRight: cs.marginRight,
            };
        }, m.layout.sel);
        ok(
            lay && lay.maxWidth === m.layout.maxWidth,
            `容器 ${m.layout.sel} max-width=${m.layout.maxWidth}(got ${lay && lay.maxWidth})`
        );
        if (m.layout.centered) {
            // A 组屏流式居中(.ui .wrap margin:0 auto)· 两侧 margin 相等 = 居中不跑偏
            ok(
                lay && lay.marginLeft === lay.marginRight,
                `容器流式居中 marginLeft==marginRight(got ${lay && lay.marginLeft} / ${lay && lay.marginRight})`
            );
        } else {
            ok(
                lay && lay.marginLeft === '0px',
                `容器左对齐 marginLeft=0(got ${lay && lay.marginLeft})`
            );
        }

        // 4) token 逐项比对(稿 vs 生产)
        for (const tk of m.tokens) {
            const exp = expected[tk.design];
            const act = await styleOf(page, tk.prod, tk.props);
            if (!exp || !act) {
                ok(false, `选择器缺失 ${tk.design}/${tk.prod}`);
                continue;
            }
            for (const p of tk.props) {
                ok(exp[p] === act[p], `${tk.prod} ${p}: 稿 ${exp[p]} == 生产 ${act[p]}`);
            }
        }

        // 5) 主色 + 图标是线性 svg(无 emoji) · bluemust 不设则跳过主色检查
        if (m.bluemust) {
            const blue = await page.evaluate((s) => {
                const el = document.querySelector(s);
                return el ? getComputedStyle(el).backgroundColor : null;
            }, m.bluemust);
            const wantPrimary = m.primary || DEFAULT_PRIMARY;
            ok(blue === wantPrimary, `主按钮主色 ${wantPrimary}(got ${blue})`);
        }
        if (m.nosvgemoji) {
            const hasSvg = await page.$(m.nosvgemoji);
            ok(!!hasSvg, `图标为线性 svg(无 emoji)· ${m.nosvgemoji}`);
        }
    }

    await browser.close();
    srv.close();
    console.log(
        '\n' +
            (fails.length
                ? `❌ 视觉照搬闸 FAIL · ${fails.length} 项不一致(回去对齐设计稿)`
                : '✅ 视觉照搬闸 PASS · 关键令牌全等设计稿')
    );
    process.exit(fails.length ? 1 : 0);
})().catch((e) => {
    console.error('design-fidelity gate error:', e);
    process.exit(2);
});
