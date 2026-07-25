// 过账去向开关 真浏览器验收:不预选 + 选了才随上传发 posting_kind。
// 用 getComputedStyle 验勾选态(类名/HTML 文本自欺过不了),用真 multipart body 验字段。
// 跑法: node scripts/_posting_kind_ui_verify.cjs → tests/visual/_shot/postingkind-*.png
/* eslint-disable no-undef */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'tests', 'visual', '_shot');
const PORT = 8796;
const TYPES = {
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.html': 'text/html',
    '.map': 'application/json',
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
};

function serve() {
    const srv = http.createServer((req, res) => {
        let p = decodeURIComponent(req.url.split('?')[0]);
        if (p === '/home') p = '/home.html';
        const file = path.join(ROOT, p);
        if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
            res.writeHead(404);
            return res.end('nf');
        }
        res.writeHead(200, {
            'content-type': TYPES[path.extname(file)] || 'text/plain',
            'cache-control': 'no-store',
        });
        fs.createReadStream(file).pipe(res);
    });
    return new Promise((r) => srv.listen(PORT, () => r(srv)));
}

// 开关只在有启用的 Express 端点时渲染(hasEnabledExpressTarget)。
const EPS = {
    items: [{ id: 'e1', adapter: 'express', name: 'Express', enabled: true, is_default: true }],
};
const RECOG = {
    ok: true,
    filename: 'a.pdf',
    document_type: 'tax_invoice',
    elapsed_ms: 5,
    page_count: 1,
    history_id: 'h1',
    history_ids: ['h1'],
    invoice_count: 1,
    confidence: 'high',
    pages: [{ fields: {} }],
    invoices: [
        {
            history_id: 'h1',
            source_index: 1,
            source_total: 1,
            page_indices: [1],
            fields: {
                seller_name: 'A Co',
                invoice_number: 'INV-1',
                date: '2026-03-01',
                total_amount: '107',
            },
        },
    ],
};

async function boot(ctx, seenBodies) {
    const page = await ctx.newPage();
    await page.setViewportSize({ width: 1320, height: 980 });
    await page.addInitScript(() => localStorage.setItem('mrpilot_token', 'tok'));
    await page.route('**/api/**', async (route) => {
        const u = route.request().url();
        if (u.includes('/api/ocr/recognize') || u.includes('/api/ocr/submit')) {
            // postData() 对带文件的 multipart 返回 null → 断言会空过;必须取 buffer。
            const buf = route.request().postDataBuffer();
            seenBodies.push(buf ? buf.toString('latin1') : '');
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(RECOG),
            });
        }
        if (u.includes('/api/erp/endpoints'))
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(EPS),
            });
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true }),
        });
    });
    const errs = [];
    page.on('pageerror', (e) => errs.push(String(e)));
    await page.goto('http://localhost:' + PORT + '/home', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof window.routeTo === 'function', { timeout: 20000 });
    await page.evaluate(() => {
        window.isOwner = () => true;
        window._userInfo = Object.assign(window._userInfo || {}, {
            can_push_erp: true,
            plan: 'lifetime',
        });
        document.body.classList.remove('workspace-gate-preboot');
        document.getElementById('workspace-gate-root')?.remove();
        const st = document.createElement('style');
        st.textContent =
            '#ws-modal{display:none!important}#workspace-gate-root{display:none!important}';
        document.head.appendChild(st);
        window.routeTo('dms-intake');
    });
    await page.waitForSelector('#dx-inv-drop', { timeout: 8000 });
    await page.waitForSelector('[data-iv-posting]', { timeout: 8000 });
    return { page, errs };
}

// 勾选态取 .dx-choice-chk 的真实计算样式:未选 color:transparent,选中 color:#fff + 有底色。
const checkedState = (page, kind) =>
    page.evaluate((k) => {
        const el = document.querySelector(`[data-iv-posting="${k}"] .dx-choice-chk`);
        if (!el) return null;
        const cs = getComputedStyle(el);
        return { color: cs.color, bg: cs.backgroundColor };
    }, kind);
const isChecked = (s) => !!s && s.color !== 'rgba(0, 0, 0, 0)' && s.bg !== 'rgba(0, 0, 0, 0)';

async function run() {
    fs.mkdirSync(OUT, { recursive: true });
    const browser = await chromium.launch();
    const ctx = await browser.newContext();
    const bodies = [];
    let pass = 0,
        fail = 0;
    const chk = async (k, cond) => {
        cond = await cond;
        cond ? pass++ : fail++;
        console.log((cond ? 'PASS' : 'FAIL').padEnd(5), k);
        return cond;
    };

    const { page, errs } = await boot(ctx, bodies);

    await chk(
        '两个去向选项都渲染出来',
        page
            .locator('[data-iv-posting]')
            .count()
            .then((n) => n === 2)
    );
    await chk(
        '★初始:服务 未勾选(computed)',
        checkedState(page, 'service').then((s) => !isChecked(s))
    );
    await chk(
        '★初始:库存 未勾选(computed)',
        checkedState(page, 'stock').then((s) => !isChecked(s))
    );
    await chk(
        '文案不再自称「当前默认」',
        page
            .locator('[data-iv-posting="service"]')
            .innerText()
            .then((s) => !/当前默认|current default|ค่าเริ่มต้น|既定/.test(s))
    );
    await chk(
        '服务项写明会建服务商品档',
        page
            .locator('[data-iv-posting="service"]')
            .innerText()
            .then((s) => /服务商品档|service product|สินค้าบริการ|サービス商品/.test(s))
    );
    await page.screenshot({ path: path.join(OUT, 'postingkind-unset.png'), fullPage: false });

    // 未选就上传 → multipart 里不该出现 posting_kind
    await page.setInputFiles('#dx-inv-file', {
        name: 'a.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('x'),
    });
    await page.waitForSelector('#dx-inv-start', { timeout: 5000 });
    await page.click('#dx-inv-start');
    await page.waitForFunction(() => document.querySelectorAll('.dx-acc-item').length > 0, {
        timeout: 10000,
    });
    // 先证明抓到的确实是表单体(否则下面的「不含」是空断言)。
    await chk(
        '抓到真实 multipart 体(非空断言守卫)',
        Promise.resolve(bodies.length > 0 && bodies.every((b) => /name="file"/.test(b)))
    );
    await chk(
        '★未选 → 上传请求不带 posting_kind',
        Promise.resolve(bodies.length > 0 && bodies.every((b) => !/name="posting_kind"/.test(b)))
    );

    // 回到上传屏,点「库存」再传 → 必须带 stock
    bodies.length = 0;
    await page.evaluate(() => window.routeTo && window.routeTo('dms-intake'));
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof window.routeTo === 'function', { timeout: 20000 });
    await page.evaluate(() => {
        window.isOwner = () => true;
        document.body.classList.remove('workspace-gate-preboot');
        document.getElementById('workspace-gate-root')?.remove();
        window.routeTo('dms-intake');
    });
    await page.waitForSelector('[data-iv-posting="stock"]', { timeout: 8000 });
    await page.click('[data-iv-posting="stock"]');
    await chk('★点库存后:库存 已勾选(computed)', checkedState(page, 'stock').then(isChecked));
    await chk(
        '★点库存后:服务 仍未勾选(computed)',
        checkedState(page, 'service').then((s) => !isChecked(s))
    );
    await page.screenshot({ path: path.join(OUT, 'postingkind-stock.png'), fullPage: false });

    await page.setInputFiles('#dx-inv-file', {
        name: 'b.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('x'),
    });
    await page.waitForSelector('#dx-inv-start', { timeout: 5000 });
    await page.click('#dx-inv-start');
    await page.waitForFunction(() => document.querySelectorAll('.dx-acc-item').length > 0, {
        timeout: 10000,
    });
    await chk(
        '★选了库存 → 上传请求带 posting_kind=stock',
        Promise.resolve(
            bodies.length > 0 &&
                bodies.every(
                    (b) =>
                        /name="posting_kind"/.test(b) &&
                        /name="posting_kind"[\s\S]{0,40}stock/.test(b)
                )
        )
    );

    await chk('零 console 报错', Promise.resolve(errs.length === 0));
    if (errs.length) console.log(errs.join('\n'));

    await browser.close();
    console.log(`\n${pass} PASS / ${fail} FAIL`);
    process.exit(fail ? 1 : 0);
}

serve().then(run);
