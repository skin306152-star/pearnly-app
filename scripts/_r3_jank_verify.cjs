/*
 * scripts/_r3_jank_verify.cjs · 第三轮对抗 · 主线程卡一下就把真枪降级成「人在打字」
 *
 * 建品侧 burstIsGunSpeed() 与入库侧 onWedge() 判「这是不是枪」用的都是【input/keydown 事件在
 * 主线程上被处理的时刻差】,阈值 50ms。枪自己多快不重要 —— 只要这一串中间有任何一次主线程
 * 停顿超过 50ms(重渲、GC、图片解码、一次同步 localStorage 写),量到的 gap 就跨过阈值,
 * 这一发真枪扫被判成人手打字:字符原样留在框里跟旧码接成一串,而查重照旧回绿字。
 *
 * 这里用一个「一次性同步阻塞」把停顿做出来:它模拟的是真实页面上任何一次长任务,
 * 与枪本身的速度无关(枪跑 8ms/字符,比任何真枪都快)。
 *
 * 枪必须走 CDP 发了就走(_gun_wedge_lib.cjs 的 cdpGun)。page.keyboard.type 会 await 每一发
 * 的派发,主线程一卡它自己也跟着停 —— 「长任务」就被偷换成「枪打得慢」,这一例于是在验一件
 * 真枪身上不会发生的事(第一版就栽在这:实测事件产生时刻也跟着出现 136ms 的坎)。
 *
 * 跑法(仓库根目录):node scripts/_r3_jank_verify.cjs
 */
const path = require('path');
const { chromium } = require('@playwright/test');
const {
    ROOT,
    DESKTOP,
    serve,
    cdpGun,
    armLongTask,
    armTwoRulers,
    readTwoRulers,
    shotter,
    runCases,
} = require('./_gun_wedge_lib.cjs');

const SHOTS = path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/round3');
const shot = shotter(SHOTS);

const OLD = '8850999320014';
const NEW = '8851234567895';
const STALL_MS = 120; // 一次长任务;Chrome 自己把 >50ms 的任务叫 long task

const INIT = () => localStorage.setItem('mrpilot_token', 'r3-verify');

async function stubApi(page, bag) {
    await page.route('https://cdnjs.cloudflare.com/**', (r) => r.abort());
    await page.route('**/api/**', async (route) => {
        const req = route.request();
        const url = new URL(req.url());
        if (url.pathname === '/api/sales/products/lookup') {
            bag.asked.push(url.searchParams.get('barcode'));
            return route.fulfill({ status: 404, json: { detail: 'sales.product_not_found' } });
        }
        if (url.pathname === '/api/sales/products') {
            if (req.method() === 'POST') {
                bag.created.push(req.postDataJSON());
                return route.fulfill({ json: { product: { id: 'p-new' } } });
            }
            return route.fulfill({ json: { products: [] } });
        }
        if (url.pathname === '/api/me')
            return route.fulfill({ json: { email: 'r3@e2e', role: 'owner', plan: 'pro' } });
        return route.fulfill({ json: { ok: true, data: {}, items: [] } });
    });
}

async function boot(browser, bag, origin) {
    const page = await browser.newPage({ viewport: DESKTOP });
    await page.addInitScript(INIT);
    await stubApi(page, bag);
    await page.goto(`${origin}/home.html`);
    await page.waitForFunction(() => typeof window.routeTo === 'function', null, {
        timeout: 25000,
    });
    await page.evaluate(() => {
        window.isOwner = () => true;
        window.getActiveWorkspaceClientId = () => 1;
        document.body.classList.remove('workspace-gate-preboot');
        document.getElementById('workspace-gate-root')?.remove();
        const st = document.createElement('style');
        st.textContent = '#ws-modal,#workspace-gate-root{display:none!important;}';
        document.head.appendChild(st);
    });
    await page.evaluate(() => window.routeTo('sales-products'));
    await page.waitForSelector('#sx-p-add', { timeout: 20000 });
    return page;
}

async function openFormWith(page, code) {
    await page.evaluate((c) => window.openProductFormWithBarcode(c, { overlay: true }), code);
    await page.waitForSelector('#sx-pf-barcode', { timeout: 10000 });
    await page.waitForFunction(() => {
        const box = document.querySelector('#sales-prod-mask .modal');
        return !!box && getComputedStyle(box).opacity === '1';
    });
    await page.click('#sx-pf-barcode');
    await page.keyboard.press('End');
}

// ── j1 · 快枪 8ms/字符,中间主线程卡 120ms ────────────────────────────
async function fastGunSurvivesOneLongTask(browser, origin) {
    const bag = { asked: [], created: [] };
    const page = await boot(browser, bag, origin);
    await openFormWith(page, OLD);
    const cdp = await page.context().newCDPSession(page);
    await armTwoRulers(page);
    await armLongTask(page, 5, STALL_MS);
    await cdpGun(cdp, NEW, 8, 'Enter');
    const m = await readTwoRulers(page);
    await page.waitForTimeout(1200);
    const after = await page.inputValue('#sx-pf-barcode');
    const state = await page.evaluate(() => {
        const el = document.getElementById('sx-pf-bc-state');
        return el ? el.textContent.trim() : '';
    });
    await shot(page, 'j1-fast-gun-one-long-task.png');
    // 前提得先立住:长任务真的发生了(perfMax 跨过 50),而枪自己没被拖慢(stampMax 仍在枪速内)。
    // 少了这两条,after === NEW 也可能只是「这次没卡起来」,那种绿什么都没保住。
    const jankHappened = m.perfMax > 100 && m.stampMax <= 50;
    return {
        ok: jankHappened && after === NEW,
        after,
        wanted: NEW,
        jankHappened,
        measured: m,
        state,
        asked: bag.asked,
        why: !jankHappened
            ? `没造出「页面卡了但枪没慢」这个前提:处理 ${m.perfMax}ms / 产生 ${m.stampMax}ms`
            : after === NEW
              ? ''
              : '真枪(8ms/字符)只因主线程卡了一次就被判成人打字 → 新旧码相接',
    };
}

// ── j2 · 同一发枪,不卡(对照)──
async function fastGunNoStall(browser, origin) {
    const bag = { asked: [], created: [] };
    const page = await boot(browser, bag, origin);
    await openFormWith(page, OLD);
    const cdp = await page.context().newCDPSession(page);
    await armTwoRulers(page);
    await cdpGun(cdp, NEW, 8, 'Enter');
    const m = await readTwoRulers(page);
    await page.waitForTimeout(1200);
    const after = await page.inputValue('#sx-pf-barcode');
    return { ok: after === NEW, after, measured: m };
}

const CASES = [
    ['fastGunSurvivesOneLongTask', fastGunSurvivesOneLongTask],
    ['fastGunNoStall', fastGunNoStall],
];

(async () => {
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch();
    let failed = 0;
    try {
        failed = await runCases(
            CASES,
            async (fn) => fn(browser, origin),
            path.join(SHOTS, 'report-r3-jank.json')
        );
    } finally {
        await browser.close();
        server.close();
    }
    process.exit(failed ? 1 : 0);
})();
