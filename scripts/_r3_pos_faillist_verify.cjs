/*
 * scripts/_r3_pos_faillist_verify.cjs · 第三轮对抗 · 失败清单的生命周期
 *
 * 上一轮问的是「清单会不会被下一件抹掉」。这一轮问相反的三件事:
 *   f1 staleAfterFix   码 A 没建档 → 清单挂一条 → 老板建好档 → 同一个码再扫一次真加进车了
 *                      → 那条「这个码还没建成商品」还挂在屏上吗?(入库侧有 resolveFail,
 *                        收银侧 onHit 一个字都没动清单)
 *   f2 duplicateRows   同一个未建档的码连扫三次 → 三条一模一样的行?
 *   f3 coversTheTill   清单挂着时它盖住了收银主屏的哪一块(position:fixed · z=70 · top:62px)
 *
 * 跑法(仓库根目录):node scripts/_r3_pos_faillist_verify.cjs [用例名]
 */
const path = require('path');
const { chromium } = require('@playwright/test');
const { ROOT, PHONE, serve, gun, shotter, runCases } = require('./_gun_wedge_lib.cjs');

const ONLY = process.argv[2] || '';
const SHOTS = path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/round3');
const shot = shotter(SHOTS);

const LATER = '8850111000039'; // 先没建档,后来建好了
const WATER = '8850999320045';

const WATER_ITEM = {
    id: 'p-water',
    name: { th: 'น้ำเปล่า', en: 'Water', zh: '水', ja: '水' },
    category_id: 1,
    base_unit: 'ขวด',
    base_price: '10.00',
    image_url: null,
    vat_applicable: true,
    units: [{ unit_name: 'ขวด', factor: '1.000', barcode: WATER, price: '10.00', default_sell: true }],
    track_batch: false,
    is_weighed: false,
    stock: { qty_base: '48.000', near_expiry: false },
    matched_unit: 'ขวด',
};
const LATER_ITEM = Object.assign({}, WATER_ITEM, {
    id: 'p-later',
    name: { th: 'ขนมปัง', en: 'Bread', zh: '面包', ja: 'パン' },
    base_price: '25.00',
    units: [{ unit_name: 'ถุง', factor: '1.000', barcode: LATER, price: '25.00', default_sell: true }],
    base_unit: 'ถุง',
    matched_unit: 'ถุง',
});

const seed = () => {
    localStorage.setItem('pos_store_token', 'r3-verify');
    localStorage.setItem('pos_store_name', 'ร้าน R3');
    localStorage.setItem('mrpilot_lang', 'th');
};

async function routeCatalog(page, state) {
    await page.route('**/api/pos/products/by-barcode*', async (route) => {
        const code = new URL(route.request().url()).searchParams.get('code');
        let hit = null;
        if (code === WATER) hit = WATER_ITEM;
        if (code === LATER && state.laterExists) hit = LATER_ITEM;
        await new Promise((r) => setTimeout(r, 120));
        await route.fulfill({
            status: hit ? 200 : 404,
            contentType: 'application/json',
            body: JSON.stringify(
                hit
                    ? { ok: true, data: hit }
                    : { ok: false, error: { code: 'pos.product_not_found', detail: null } }
            ),
        });
    });
}

async function boot(browser, origin, state) {
    const page = await browser.newPage({ viewport: PHONE });
    await page.addInitScript(seed);
    await routeCatalog(page, state);
    await page.goto(`${origin}/static/pos/pos.html`);
    await page.waitForSelector('#login-cashiers .ca', { timeout: 20000 });
    for (const d of ['1', '2', '3', '4']) await page.click(`#view-login .pad .k[data-pin="${d}"]`);
    await page.waitForSelector('#shift-mask.show', { timeout: 10000 });
    await page.click('#shift-open-go');
    await page.waitForSelector('#view-main.is-active', { timeout: 10000 });
    await page.waitForSelector('#main-grid .prod', { timeout: 10000 });
    return page;
}

const failsState = (page) =>
    page.evaluate(() => {
        const box = document.getElementById('bscan-fails');
        const cs = getComputedStyle(box);
        const r = box.getBoundingClientRect();
        return {
            shown: box.classList.contains('show') && cs.display !== 'none' && r.height > 0,
            rows: box.querySelectorAll('.bscan-fail').length,
            head: (box.querySelector('.bscan-fails-n') || {}).textContent || '',
            codes: Array.from(box.querySelectorAll('.bscan-fail-code,.bscan-code')).map((e) =>
                e.textContent.trim()
            ),
            texts: Array.from(box.querySelectorAll('.bscan-fail-msg')).map((e) =>
                e.textContent.trim()
            ),
            rect: { top: Math.round(r.top), h: Math.round(r.height), z: cs.zIndex },
        };
    });

const cart = (page) =>
    page.evaluate(() => ({
        lines: document.getElementById('cart-lines').children.length,
        peek: (document.getElementById('cart-peek-count') || {}).textContent || '',
        total: (document.getElementById('cart-grand') || {}).textContent || '',
    }));

// ── f1 · 建好档之后重扫成功,那条旧的「还没建档」还挂着吗 ───────────────
async function staleAfterFix(browser, origin) {
    const state = { laterExists: false };
    const page = await boot(browser, origin, state);
    await page.click('body');
    await gun(page, LATER); // 还没建档 → 进清单
    await page.waitForTimeout(700);
    const before = await failsState(page);
    state.laterExists = true; // 老板在后台把这件货建好了
    await page.click('body');
    await gun(page, LATER); // 同一个码重扫 → 这次真加进车
    await page.waitForTimeout(900);
    const after = await failsState(page);
    const c = await cart(page);
    await shot(page, 'f1-stale-fail-after-success.png');
    const ok = after.rows === 0;
    return {
        ok,
        beforeRows: before.rows,
        afterRows: after.rows,
        afterTexts: after.texts,
        afterHead: after.head,
        cart: c,
        why: ok
            ? ''
            : '同一个码已经真加进购物车了,清单上那条「这个码还没建成商品」原样挂着 —— 店员照它去建第二次',
    };
}

// ── f2 · 同一个未建档的码连扫三次 ──────────────────────────────────────
async function duplicateRows(browser, origin) {
    const state = { laterExists: false };
    const page = await boot(browser, origin, state);
    for (let i = 0; i < 3; i++) {
        await page.click('body');
        await gun(page, LATER);
        await page.waitForTimeout(500);
    }
    const st = await failsState(page);
    await shot(page, 'f2-duplicate-fail-rows.png');
    const ok = st.rows === 1;
    return {
        ok,
        rows: st.rows,
        head: st.head,
        texts: st.texts,
        why: ok ? '' : `同一个码扫 3 次堆出 ${st.rows} 条一模一样的行(入库侧按码去重,收银侧没有)`,
    };
}

// ── f3 · 清单挂着时盖住了收银主屏的什么 ────────────────────────────────
async function coversTheTill(browser, origin) {
    const state = { laterExists: false };
    const page = await boot(browser, origin, state);
    for (let i = 0; i < 4; i++) {
        await page.click('body');
        await gun(page, LATER.slice(0, 12) + String(i)); // 四个都查不到的码
        await page.waitForTimeout(420);
    }
    const st = await failsState(page);
    // 清单矩形里,最上层命中的是谁 —— 底下本来是什么被盖住了
    const occluded = await page.evaluate(() => {
        const box = document.getElementById('bscan-fails');
        const r = box.getBoundingClientRect();
        const pts = [];
        for (const [dx, dy] of [
            [0.5, 0.1],
            [0.5, 0.5],
            [0.5, 0.9],
        ]) {
            const x = r.left + r.width * dx;
            const y = r.top + r.height * dy;
            const top = document.elementFromPoint(x, y);
            box.style.pointerEvents = 'none';
            box.style.visibility = 'hidden';
            const under = document.elementFromPoint(x, y);
            box.style.visibility = '';
            box.style.pointerEvents = '';
            pts.push({
                y: Math.round(y),
                top: top ? top.className || top.tagName : null,
                under: under ? (under.id || under.className || under.tagName) : null,
                underText: under ? (under.textContent || '').trim().slice(0, 40) : '',
            });
        }
        return pts;
    });
    await shot(page, 'f3-fails-cover-till.png');
    return { ok: true, rows: st.rows, rect: st.rect, occluded };
}

const CASES = [
    ['staleAfterFix', staleAfterFix],
    ['duplicateRows', duplicateRows],
    ['coversTheTill', coversTheTill],
];

(async () => {
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch();
    const picked = ONLY ? CASES.filter(([n]) => n === ONLY) : CASES;
    let failed = 0;
    try {
        failed = await runCases(
            picked,
            async (fn) => fn(browser, origin),
            path.join(SHOTS, 'report-r3-faillist.json')
        );
    } finally {
        await browser.close();
        server.close();
    }
    process.exit(failed ? 1 : 0);
})();
