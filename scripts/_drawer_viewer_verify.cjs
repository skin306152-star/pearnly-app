// 识别记录 / 异常 抽屉原图查看器 真浏览器验收(共用 iv-* 查看器 · page.png stub 含 404→重试)。
// 跑法: node scripts/_drawer_viewer_verify.cjs
/* eslint-disable no-undef */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const PORT = 8798;
const TYPES = {
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.html': 'text/html',
    '.map': 'application/json',
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
};
const PNG = Buffer.from(
    'iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAEklEQVR4nGP8z8Dwn4EBiBkYAA8wAf/h3iEAAAAAAElFTkSuQmCC',
    'base64'
);

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

const DETAIL = {
    id: 'h1',
    filename: 'receipt_demo.pdf',
    page_count: 1,
    confidence: 'high',
    created_at: '2026-06-23T08:00:00Z',
    client_id: null,
    pages: [
        {
            fields: {
                seller_name: '7-Eleven',
                seller_tax: '0105546015062',
                invoice_number: 'INV-001',
                date: '2026-06-09',
                subtotal: '115',
                vat: '8.05',
                total_amount: '123.05',
                buyer_name: '',
            },
        },
    ],
};

async function stub(page) {
    let pngHits = 0;
    await page.route('**/api/**', async (route) => {
        const u = route.request().url();
        if (/\/api\/history\/[^/]+\/page\/\d+\.png/.test(u)) {
            pngHits++;
            if (pngHits <= 2)
                return route.fulfill({ status: 404, contentType: 'application/json', body: '{}' });
            return route.fulfill({ status: 200, contentType: 'image/png', body: PNG });
        }
        if (/\/api\/history\/[^/]+\/pdf/.test(u))
            return route.fulfill({
                status: 200,
                contentType: 'application/pdf',
                headers: { 'X-Filename': 'd.pdf' },
                body: Buffer.from('%PDF-1.4'),
            });
        if (/\/api\/history\/h1(\?|$)/.test(u))
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(DETAIL),
            });
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, items: [] }),
        });
    });
}

async function boot(ctx) {
    const page = await ctx.newPage();
    await page.setViewportSize({ width: 1400, height: 980 });
    await page.addInitScript(() => localStorage.setItem('mrpilot_token', 'tok'));
    await stub(page);
    const errs = [];
    page.on('pageerror', (e) => errs.push(String(e)));
    await page.goto('http://localhost:' + PORT + '/home', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof window.routeTo === 'function', { timeout: 20000 });
    await page.evaluate(() => {
        window.isOwner = () => true;
        window._userInfo = Object.assign(window._userInfo || {}, {
            can_push_erp: true,
            can_edit_fields: true,
            plan: 'lifetime',
        });
        document.body.classList.remove('workspace-gate-preboot');
        document.getElementById('workspace-gate-root')?.remove();
    });
    return { page, errs };
}

async function run() {
    const browser = await chromium.launch();
    const ctx = await browser.newContext();
    let pass = 0,
        fail = 0;
    const vis = (page, sel) => page.locator(sel).first().isVisible();
    const chk = async (k, cond) => {
        cond = await cond;
        cond ? pass++ : fail++;
        console.log((cond ? 'PASS' : 'FAIL').padEnd(5), k);
        return cond;
    };

    // ── 识别记录抽屉:两栏 + 左原图查看器 ──
    const { page, errs } = await boot(ctx);
    await page.evaluate(() => window.openHistoryDrawer('h1'));
    await page.waitForSelector('.drawer.hd-wide .hd-twopane', { timeout: 8000 });
    await chk('识别记录·抽屉两栏(加宽 hd-wide)', vis(page, '.drawer.hd-wide'));
    await chk('识别记录·左栏查看器存在', vis(page, '.hd-imgpane .iv-card'));
    await page
        .waitForFunction(
            () => {
                const i = document.querySelector('.hd-imgpane .iv-img');
                return i && i.src && i.src.startsWith('blob:');
            },
            { timeout: 8000 }
        )
        .catch(() => {});
    await chk(
        '识别记录·原图重试后加载(404→blob)',
        page.evaluate(() => {
            const c = document.querySelector('.hd-imgpane .iv-card');
            const i = document.querySelector('.hd-imgpane .iv-img');
            return !!i && i.src.startsWith('blob:') && !c.classList.contains('noimg');
        })
    );
    await page.click('.hd-imgpane [data-iv="in"]');
    await chk(
        '识别记录·放大改变缩放标签',
        page
            .locator('.hd-imgpane .iv-zoom')
            .innerText()
            .then((s) => s !== '100%')
    );
    await chk('识别记录·右栏内容(tab)在', vis(page, '.hd-twopane .hd-root .hd-tabs'));
    await page.screenshot({ path: path.join(ROOT, 'tests', 'visual', '_shot', 'hd-viewer.png') });
    await chk('识别记录·无 JS 报错', Promise.resolve(errs.length === 0));
    if (errs.length) console.log('  errs:', errs.slice(0, 3));

    // ── 对账中心复用同抽屉不被加宽(hd-wide 只在 history)──
    await page.evaluate(() => {
        window.openHistoryDrawer && document.getElementById('drawer')?.classList.remove('hd-wide');
    });

    await browser.close();
    console.log(`\n结果: ${pass} PASS / ${fail} FAIL`);
    process.exit(fail ? 1 : 0);
}
serve()
    .then(run)
    .catch((e) => {
        console.error(e);
        process.exit(1);
    });
