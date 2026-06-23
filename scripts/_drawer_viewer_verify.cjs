// 识别记录抽屉 原图查看器(采购同款 .pv-*)真浏览器验收 · 用真实尺寸图验「按比例铺开」(非占位小图)。
// 跑法: node scripts/_drawer_viewer_verify.cjs → tests/visual/_shot/hd-viewer.png
/* eslint-disable no-undef */
const http = require('http');
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
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

// 真实尺寸 PNG(400×560 红块)· 比查看器大 → max-width/height 94% 真生效 → 能验「铺开」
function crc32(buf) {
    let crc = 0xffffffff;
    for (let i = 0; i < buf.length; i++) {
        crc ^= buf[i];
        for (let k = 0; k < 8; k++) crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
    }
    return (crc ^ 0xffffffff) >>> 0;
}
function makePNG(w, h) {
    const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
    const ihdr = Buffer.alloc(13);
    ihdr.writeUInt32BE(w, 0);
    ihdr.writeUInt32BE(h, 4);
    ihdr[8] = 8;
    ihdr[9] = 2;
    const raw = Buffer.alloc((w * 3 + 1) * h);
    for (let y = 0; y < h; y++) {
        raw[y * (w * 3 + 1)] = 0;
        for (let x = 0; x < w; x++) {
            const o = y * (w * 3 + 1) + 1 + x * 3;
            raw[o] = 230;
            raw[o + 1] = 60;
            raw[o + 2] = 60;
        }
    }
    const idat = zlib.deflateSync(raw);
    const chunk = (type, data) => {
        const len = Buffer.alloc(4);
        len.writeUInt32BE(data.length, 0);
        const td = Buffer.concat([Buffer.from(type), data]);
        const crc = Buffer.alloc(4);
        crc.writeUInt32BE(crc32(td), 0);
        return Buffer.concat([len, td, crc]);
    };
    return Buffer.concat([
        sig,
        chunk('IHDR', ihdr),
        chunk('IDAT', idat),
        chunk('IEND', Buffer.alloc(0)),
    ]);
}
const PNG = makePNG(400, 560);

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

    const { page, errs } = await boot(ctx);
    await page.evaluate(() => window.openHistoryDrawer('h1'));
    await page.waitForSelector('.drawer.hd-wide .hd-twopane', { timeout: 8000 });
    await chk('识别记录·抽屉两栏(加宽 hd-wide)', vis(page, '.drawer.hd-wide'));
    await chk('识别记录·左栏查看器(采购同款 pv-viewer)', vis(page, '.hd-imgpane .pv-viewer'));
    // 原图重试后加载(404×2→200)
    await page
        .waitForFunction(
            () => {
                const i = document.querySelector('.hd-imgpane .pv-img');
                return i && i.src && i.src.startsWith('blob:');
            },
            { timeout: 8000 }
        )
        .catch(() => {});
    await chk(
        '识别记录·原图重试后加载(404→blob)',
        page.evaluate(() => {
            const v = document.querySelector('.hd-imgpane .pv-viewer');
            const i = document.querySelector('.hd-imgpane .pv-img');
            return !!i && i.src.startsWith('blob:') && !v.classList.contains('noimg');
        })
    );
    // ★ 关键:图真的按比例铺开(填满查看器某一维 ≥80%)· 不是固定小图
    await page
        .waitForFunction(
            () => {
                const i = document.querySelector('.hd-imgpane .pv-img');
                return i && i.complete && i.clientHeight > 0;
            },
            { timeout: 4000 }
        )
        .catch(() => {});
    const fill = await page.evaluate(() => {
        const v = document.querySelector('.hd-imgpane .pv-viewer');
        const i = document.querySelector('.hd-imgpane .pv-img');
        if (!v || !i) return 0;
        return Math.max(i.clientWidth / v.clientWidth, i.clientHeight / v.clientHeight);
    });
    console.log('     图填充比例:', fill.toFixed(2));
    await chk('★识别记录·图按比例铺开(≥0.8 · 非固定小图)', Promise.resolve(fill >= 0.8));
    // 工具栏放大
    await page.click('.hd-imgpane .pv-tools button[data-z="in"]');
    await chk(
        '识别记录·放大按钮改变缩放标签',
        page
            .locator('.hd-imgpane .pv-zoom')
            .innerText()
            .then((s) => s !== '100%')
    );
    await page.click('.hd-imgpane .pv-tools button[data-z="reset"]');
    await chk(
        '识别记录·复位回 100%',
        page
            .locator('.hd-imgpane .pv-zoom')
            .innerText()
            .then((s) => s === '100%')
    );
    await chk('识别记录·右栏内容(tab)在', vis(page, '.hd-twopane .hd-root .hd-tabs'));
    await page.screenshot({ path: path.join(ROOT, 'tests', 'visual', '_shot', 'hd-viewer.png') });
    await chk('识别记录·无 JS 报错', Promise.resolve(errs.length === 0));
    if (errs.length) console.log('  errs:', errs.slice(0, 3));

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
