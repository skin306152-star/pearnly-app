// 做账 5 屏 · 真浏览器冒烟(本地 bundle + stub /api/accounting · 一次性脚本)
// 验:5 屏渲染 isVisible + 关键交互(行展开/改科目弹窗/结账确认)+ 浅暗截图。
// 跑法: node scripts/_acct_shot.cjs → tests/visual/_shot/acct-*.png
/* eslint-disable no-undef, no-console */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'tests', 'visual', '_shot');
const PORT = 8794;

const VOUCHER = {
    id: 'v1',
    voucher_no: 'JV2606-0001',
    voucher_date: '2026-06-08',
    period: '2026-06',
    source_type: 'purchase',
    source_ref: 'PI-0012',
    description: '向 ทิปโก้ 进货付款',
    human_note: '这批货 17,000 进库存,另付 1,190 的税(以后能抵),18,190 先欠供应商。',
    rule_key: 'R1',
    confidence: 95,
    method: 'auto',
    status: 'auto_posted',
    review_reason: null,
    total_debit: 18190,
    total_credit: 18190,
    lines: [
        { id: 'l1', account_id: 'a1', account_code: '1150', account_name: '库存商品', dr_cr: 'debit', amount: 17000, memo: null },
        { id: 'l2', account_id: 'a2', account_code: '1140', account_name: '进项税', dr_cr: 'debit', amount: 1190, memo: null },
        { id: 'l3', account_id: 'a3', account_code: '2010', account_name: '应付账款', dr_cr: 'credit', amount: 18190, memo: null },
    ],
};
const PENDING = {
    ...VOUCHER,
    id: 'v2',
    voucher_no: 'JV2606-0002',
    source_type: 'payment',
    description: '付设计服务费(含预扣税)',
    status: 'pending_review',
    method: 'suggested',
    review_reason: 'suggest_mode',
    rule_key: 'R2',
};
const ACCOUNTS = [
    { id: 'a1', code: '1150', name_zh: '库存商品', name_th: 'สินค้าคงเหลือ', acct_type: 'asset', is_preset: true, is_active: true },
    { id: 'a2', code: '1140', name_zh: '进项税', name_th: 'ภาษีซื้อ', acct_type: 'asset', is_preset: true, is_active: true },
    { id: 'a3', code: '2010', name_zh: '应付账款', name_th: 'เจ้าหนี้การค้า', acct_type: 'liability', is_preset: true, is_active: true },
    { id: 'a4', code: '4010', name_zh: '销售收入', name_th: 'รายได้จากการขาย', acct_type: 'revenue', is_preset: true, is_active: true },
];
const API = {
    'GET /api/accounting/vouchers': {
        summary: { auto_count: 244, posted_count: 245, pending_count: 1 },
        items: [VOUCHER, PENDING],
    },
    'GET /api/accounting/vouchers/v1': { voucher: VOUCHER },
    'GET /api/accounting/vouchers/v2': { voucher: PENDING },
    'GET /api/accounting/review': { count: 1, items: [PENDING] },
    'GET /api/accounting/accounts': { accounts: ACCOUNTS },
    'GET /api/accounting/mappings': {
        mappings: [
            { role: 'inventory', account_id: 'a1' },
            { role: 'input_vat', account_id: 'a2' },
            { role: 'ap', account_id: 'a3' },
        ],
    },
    'GET /api/accounting/settings': {
        settings: {
            auto_post: false,
            auto_post_threshold: 90,
            auto_post_rules: { R1: true },
            accounting_standard: 'TFRS_NPAE',
            inventory_method: 'periodic',
            base_currency: 'THB',
            start_period: '2026-06',
            closed_through: null,
        },
    },
    'GET /api/accounting/learned': {
        items: [{ id: 'lr1', scope_key: 'supplier:abc-design', decision: { confirmed_rule: 'R2' } }],
    },
};

function serveStatic() {
    const types = {
        '.js': 'application/javascript',
        '.css': 'text/css',
        '.html': 'text/html',
        '.map': 'application/json',
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

let failures = 0;
function check(name, ok) {
    console.log((ok ? 'PASS' : 'FAIL') + ' ' + name);
    if (!ok) failures += 1;
}

(async () => {
    fs.mkdirSync(OUT, { recursive: true });
    const srv = await serveStatic();
    const browser = await chromium.launch();
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    await page.route('**/api/**', (route) => {
        const req = route.request();
        const u = new URL(req.url());
        const key = req.method() + ' ' + u.pathname;
        const hit = API[key];
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(hit !== undefined ? { ok: true, data: hit } : { ok: true, data: {} }),
        });
    });
    await ctx.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'designgate.fake.token');
        localStorage.setItem('mrpilot_lang', 'zh');
        localStorage.setItem('pearnly_work_mode', 'personal');
    });
    await page.goto('http://localhost:' + PORT + '/home', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof window.routeTo === 'function', { timeout: 20000 });
    await page.evaluate(() => {
        window.isOwner = () => true;
        window.getActiveWorkspaceClientId = () => 1;
        const st = document.createElement('style');
        st.textContent = '#ws-modal{display:none!important;}';
        document.head.appendChild(st);
    });

    for (const theme of ['light', 'dark']) {
        await page.evaluate(
            (t) => document.documentElement.classList.toggle('dark', t === 'dark'),
            theme
        );
        await page.waitForTimeout(300);

        // 屏1 主屏:北极星 + 待审行动卡 + 列表行
        await page.evaluate(() => window.routeTo('vouchers'));
        await page.waitForTimeout(1000);
        check(`list star ${theme}`, await page.locator('#acct-star').isVisible());
        check(`list attn ${theme}`, await page.locator('#acct-attn').isVisible());
        check(`list rows ${theme}`, (await page.locator('#acct-body .row').count()) === 2);
        await page.screenshot({ path: path.join(OUT, `acct-list-${theme}.png`) });
        // 行展开(借贷表)
        await page.locator('#acct-body .row').first().click();
        await page.waitForTimeout(600);
        check(`list expand led ${theme}`, await page.locator('#acct-body .open .led').isVisible());
        await page.screenshot({ path: path.join(OUT, `acct-list-open-${theme}.png`) });

        // 屏2 逐笔审:进度带 + 拿不准 + 借贷 + 三按钮
        await page.evaluate(() => window.routeTo('acct-review'));
        await page.waitForTimeout(1000);
        check(`review q ${theme}`, await page.locator('#page-acct-review .q').isVisible());
        check(`review led ${theme}`, await page.locator('#page-acct-review .led').isVisible());
        check(
            `review confirm btn ${theme}`,
            await page.locator('#page-acct-review [data-act="confirm"]').isVisible()
        );
        await page.screenshot({ path: path.join(OUT, `acct-review-${theme}.png`) });
        // 改科目弹窗(.modal 非原生)
        await page.locator('#page-acct-review [data-act="override"]').click();
        await page.waitForTimeout(700);
        check(`review picker modal ${theme}`, await page.locator('.acctm select[data-line]').count() === 3);
        await page.screenshot({ path: path.join(OUT, `acct-review-modal-${theme}.png`) });
        await page.locator('.acctm .x').click();
        await page.waitForTimeout(300);

        // 屏3 科目表:分组行 + 预置标签
        await page.evaluate(() => window.routeTo('acct-accounts'));
        await page.waitForTimeout(1000);
        check(`accounts rows ${theme}`, (await page.locator('#acct-acc-body .row').count()) === 4);
        check(`accounts preset ${theme}`, await page.locator('#acct-acc-body .preset').first().isVisible());
        await page.screenshot({ path: path.join(OUT, `acct-accounts-${theme}.png`) });

        // 屏5 设置:开关 + 粒度规则 + 可见规则
        await page.evaluate(() => window.routeTo('acct-settings'));
        await page.waitForTimeout(1000);
        check(`settings sw ${theme}`, await page.locator('#acct-sw-auto').isVisible());
        check(`settings rule R1 on ${theme}`, await page.locator('#acct-rule-sw-R1.on').isVisible());
        check(`settings learned ${theme}`, await page.locator('.learned-row').first().isVisible());
        await page.screenshot({ path: path.join(OUT, `acct-settings-${theme}.png`) });

        // 屏4 出账本:未结提示 + 结账按钮(pending=1 → 挡结显示去逐笔审)
        await page.evaluate(() => window.routeTo('acct-books'));
        await page.waitForTimeout(1000);
        check(`books rows ${theme}`, (await page.locator('#acct-books-rows .row').count()) === 6);
        check(`books closebar ${theme}`, await page.locator('.closebar').isVisible());
        check(
            `books blocked goreview ${theme}`,
            await page.locator('#acct-close-goreview').isVisible()
        );
        await page.screenshot({ path: path.join(OUT, `acct-books-${theme}.png`) });
    }

    // 手机视口(主屏 + 逐笔审)
    await page.setViewportSize({ width: 390, height: 844 });
    await page.evaluate(() => document.documentElement.classList.remove('dark'));
    await page.evaluate(() => window.routeTo('vouchers'));
    await page.waitForTimeout(900);
    await page.screenshot({ path: path.join(OUT, 'acct-list-mobile.png') });
    await page.evaluate(() => window.routeTo('acct-review'));
    await page.waitForTimeout(900);
    await page.screenshot({ path: path.join(OUT, 'acct-review-mobile.png') });

    await browser.close();
    srv.close();
    console.log(failures ? `FAILURES: ${failures}` : 'ALL PASS');
    process.exit(failures ? 1 : 0);
})();
