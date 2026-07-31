/*
 * scripts/_pos_fails_overlap_verify.cjs · 扫码失败清单挡不挡活路(真浏览器 · 真命中测试)
 *
 * 为什么非得真浏览器:这条问题的判据是「屏上这一点点到的是谁」。类名、z-index、
 * getComputedStyle 都答不了 —— 清单是 fixed 浮层时 .bscan-fails 与 #main-search 各自的样式
 * 全都"正确",可它们的盒子叠在一起,店员点搜索框点到的是清单。只有 document.elementFromPoint
 * 在真排版下答得了这个问题。
 *
 * 三条:
 *   ① 清单撑着时,#main-search 与 #main-grid 的采样点没有一个被清单接走(浮层版实测遮 34%)。
 *      这条是「用这个码搜商品」那颗按钮能不能用的前提:它干的正是把码填进 #main-search
 *      再重画 #main-grid,而浮层版把这两样一起盖住 —— 店员点完看不见自己刚要来的结果。
 *   ② 摄像头取景层开着时,清单仍画在画面之上(连扫时第 N 件失败得当场看得见)。
 *      清单从 fixed 改成 in-flow 之后,这一条靠的是 z-index 与层叠上下文,必须真渲染才作数。
 *   ③ 点「用这个码搜商品」:搜索框真填上这个码,清单只少那一条,另一条原样还在。
 *
 * 一个字的文案都不注入:期望值现场从页面里真的 window.POS_I18N 取。
 *
 * 用法(仓库根目录):node scripts/_pos_fails_overlap_verify.cjs [截图目录]
 * 退出码 0 = 全过。截图默认落 tests/e2e/_artifacts/pos_barcode_scan/fails-overlap/。
 */
const fs = require('fs');
const http = require('http');
const path = require('path');
const { chromium } = require('@playwright/test');

const ROOT = path.resolve(__dirname, '..');
const SHOTS = path.resolve(
    process.argv[2] || path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/fails-overlap')
);
const MIME = { '.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html' };
const PHONE = { width: 390, height: 780 };
const DESKTOP = { width: 1280, height: 800 };
// 后台没建档的四个码:报告里那条 265px / z=70 的清单就是四条时的高度。
const GHOSTS = ['8850111000015', '8850111000022', '8850111000039', '8850111000046'];

function serve() {
    const server = http.createServer((req, res) => {
        const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '');
        const fp = path.join(ROOT, rel);
        const ok = fp.startsWith(ROOT) && fs.existsSync(fp) && !fs.statSync(fp).isDirectory();
        res.writeHead(ok ? 200 : 404, {
            'content-type': ok ? MIME[path.extname(fp)] || 'application/octet-stream' : 'text/html',
        });
        if (ok) fs.createReadStream(fp).pipe(res);
        else res.end('not found');
    });
    return new Promise((r) => server.listen(0, '127.0.0.1', () => r(server)));
}

// 设备已绑店但不带账套 id → POS.allowMock() 为真,店员/商品走本地预览目录。
function seed(lang) {
    localStorage.setItem('pos_store_token', 'fails-overlap');
    localStorage.setItem('pos_store_name', 'ร้าน OVERLAP');
    localStorage.setItem('mrpilot_lang', lang);
}

async function login(page, origin) {
    await page.goto(`${origin}/static/pos/pos.html`);
    await page.waitForSelector('#login-cashiers .ca', { timeout: 15000 });
    for (const d of ['1', '2', '3', '4']) await page.click(`#view-login .pad .k[data-pin="${d}"]`);
    await page.waitForSelector('#shift-mask.show', { timeout: 10000 });
    await page.click('#shift-open-go');
    await page.waitForSelector('#view-main.is-active', { timeout: 10000 });
    await page.waitForSelector('#main-grid .prod', { timeout: 10000 });
}

async function route404(page) {
    await page.route('**/api/pos/products/by-barcode*', (route) =>
        route.fulfill({
            status: 404,
            contentType: 'application/json',
            body: JSON.stringify({ ok: false, error: { code: 'pos.product_not_found' } }),
        })
    );
}

// 在真排版下按格点做命中测试:这一格点到的是不是清单。
// 取样点落在目标元素自己的可见盒子里(超出视口的部分不算 —— 那不是被清单挡的)。
async function coverage(page, selector, steps) {
    return page.evaluate(
        ({ sel, n }) => {
            const el = document.querySelector(sel);
            const list = document.getElementById('bscan-fails');
            if (!el || !list) return null;
            const b = el.getBoundingClientRect();
            const x0 = Math.max(b.left, 0);
            const x1 = Math.min(b.right, innerWidth);
            const y0 = Math.max(b.top, 0);
            const y1 = Math.min(b.bottom, innerHeight);
            if (x1 <= x0 || y1 <= y0) return { points: 0, blocked: 0, ratio: 0, offscreen: true };
            let points = 0;
            let blocked = 0;
            for (let i = 0; i < n; i++) {
                for (let j = 0; j < n; j++) {
                    const x = x0 + ((x1 - x0) * (i + 0.5)) / n;
                    const y = y0 + ((y1 - y0) * (j + 0.5)) / n;
                    const hit = document.elementFromPoint(x, y);
                    points += 1;
                    if (hit && (hit === list || list.contains(hit))) blocked += 1;
                }
            }
            return { points, blocked, ratio: blocked / points, offscreen: false };
        },
        { sel: selector, n: steps }
    );
}

// 真可见 + 真画在最上面(中心点命中自己)。
async function seen(page, sel) {
    const vis = await page.locator(sel).isVisible();
    const probe = await page.evaluate((s) => {
        const el = document.querySelector(s);
        if (!el) return null;
        const cs = getComputedStyle(el);
        const b = el.getBoundingClientRect();
        const top = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2);
        return {
            display: cs.display,
            position: cs.position,
            h: Math.round(b.height),
            top: Math.round(b.top),
            onTop: !!(top && (el === top || el.contains(top))),
            topTag: top ? top.id || top.className || top.tagName : null,
        };
    }, sel);
    return Object.assign({ isVisible: vis }, probe);
}

async function pushGhosts(page, codes) {
    for (const code of codes) {
        await page.evaluate((c) => window.POS.scan.submit(c), code);
    }
    await page.waitForFunction(
        (n) => document.querySelectorAll('#bscan-fails .bscan-fail').length === n,
        codes.length,
        { timeout: 10000 }
    );
}

// ── ① 清单撑着时,搜索框与商品网格一点都不许被它接走 ──────────────────────
async function blocksNothing(browser, origin, viewport, tag) {
    const page = await browser.newPage({ viewport });
    await page.addInitScript(seed, 'th');
    await route404(page);
    await login(page, origin);
    await pushGhosts(page, GHOSTS);

    const list = await seen(page, '#bscan-fails');
    const search = await coverage(page, '#main-search', 5);
    const grid = await coverage(page, '#main-grid', 6);
    const searchBox = await seen(page, '#main-search');
    await page.screenshot({ path: path.join(SHOTS, `01-${tag}-four-fails.png`), fullPage: false });
    await page.close();
    return {
        ok:
            list.isVisible &&
            list.h > 0 &&
            search.blocked === 0 &&
            grid.blocked === 0 &&
            searchBox.onTop,
        list,
        searchBox,
        searchCoverage: search,
        gridCoverage: grid,
    };
}

// ── ② 取景层开着时清单仍在画面之上 ───────────────────────────────────────
// in-flow 之后这条不再是 position:fixed 白送的,靠的是 z-index 与「.left 到 .pos-view 之间
// 没人另起层叠上下文」。那是渲染期才成立的事,只有真浏览器答得了。
async function aboveCameraLayer(browser, origin) {
    const page = await browser.newPage({ viewport: PHONE });
    await page.addInitScript(seed, 'th');
    await route404(page);
    // 解码器拉不下来 → 停在错误卡,取景层已经开着(本条只验层叠,不验解码)。
    await page.route('**/static/dist/scan.js*', (r) => r.fulfill({ status: 404, body: '' }));
    await login(page, origin);
    await pushGhosts(page, GHOSTS.slice(0, 2));
    await page.click('#main-scan-btn');
    await page.waitForSelector('#bscan-mask.show', { timeout: 10000 });
    const list = await seen(page, '#bscan-fails');
    const maskUp = await page.locator('#bscan-mask').isVisible();
    await page.screenshot({ path: path.join(SHOTS, '02-over-camera-layer.png') });
    await page.close();
    return { ok: maskUp && list.isVisible && list.onTop, maskUp, list };
}

// ── ③「用这个码搜商品」只销那一条 ────────────────────────────────────────
async function searchSettlesOneRow(browser, origin) {
    const page = await browser.newPage({ viewport: PHONE });
    await page.addInitScript(seed, 'th');
    await route404(page);
    await login(page, origin);
    await pushGhosts(page, GHOSTS.slice(0, 2));
    const th = await page.evaluate(() => window.POS_I18N.th);
    const label = th['posui.bscan.search_code'];
    const before = await page.locator('#bscan-fails .bscan-fail').count();
    // 最上面那条是最后扫进来的(unshift)· 点它自己那颗按钮
    await page
        .locator('#bscan-fails .bscan-fail', { hasText: GHOSTS[1] })
        .locator('button', { hasText: label })
        .click();
    await page.waitForTimeout(300);
    const after = await page.locator('#bscan-fails .bscan-fail').count();
    const searchValue = await page.inputValue('#main-search');
    const otherStays = (await page.locator('#bscan-fails').textContent()).includes(GHOSTS[0]);
    await page.screenshot({ path: path.join(SHOTS, '03-after-search-this-code.png') });
    await page.close();
    return {
        ok: before === 2 && after === 1 && searchValue === GHOSTS[1] && otherStays,
        before,
        after,
        searchValue,
        otherStays,
    };
}

// 一档驱不动(按钮被浮层挡住 → Playwright 的可操作性检查直接超时)也是失败的一种,
// 不是脚本崩了:整条报告因此少掉的那几档才是最该被看见的证据。
async function attempt(name, fn) {
    try {
        return await fn();
    } catch (e) {
        return { ok: false, crash: String((e && e.message) || e).split('\n')[0] };
    }
}

(async () => {
    fs.mkdirSync(SHOTS, { recursive: true });
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch();
    const report = {
        phoneBlocksNothing: await attempt('phone', () =>
            blocksNothing(browser, origin, PHONE, 'phone')
        ),
        desktopBlocksNothing: await attempt('desktop', () =>
            blocksNothing(browser, origin, DESKTOP, 'desktop')
        ),
        aboveCameraLayer: await attempt('camera', () => aboveCameraLayer(browser, origin)),
        searchSettlesOneRow: await attempt('search', () => searchSettlesOneRow(browser, origin)),
    };
    await browser.close();
    server.close();

    const failed = Object.keys(report).filter((k) => !report[k].ok);
    fs.writeFileSync(
        path.join(SHOTS, 'report-fails-overlap.json'),
        JSON.stringify(report, null, 2)
    );
    console.log(JSON.stringify(report, null, 2));
    console.log(failed.length ? `FAIL: ${failed.join(', ')}` : `PASS · 截图在 ${SHOTS}`);
    process.exit(failed.length ? 1 : 0);
})().catch((e) => {
    console.error('POS FAILS OVERLAP CRASH', e);
    process.exit(2);
});
