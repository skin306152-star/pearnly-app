/*
 * scripts/_hostile_scan_pos_verify.cjs · 对抗素材验收(收银台)
 *
 * 上一轮那份验收把失败排在队列第 3 位(五件里中间那一件)。这一轮把「失败」摆到更难的位置,
 * 并且专挑「失败之后店员会做的下一个动作」下手 —— 提示被抹掉这件事不止「下一件盖上来」一种走法:
 *   p1 twoFailsInBurst    连扫 5 件,第 2 与第 4 是未建档的码,后面都还有会命中的
 *   p2 searchOneFailEatsTheOther  两条失败并存时,点其中一条的「拿这个码去搜」
 *   p3 escapeEatsFails    两条失败并存时按 Esc(取景层已经关了)
 *   p4 onlyNamePriceNull  只填了名字建出来的货(unit_price=null)扫进收银台
 *   p5 boxOnlyBaseScan    units 里只有「ลัง」的货扫主码(matched_unit=基本单位,units 里没有)
 *
 * 真的东西:static/pos/pos.html + dist/pos.js 是本仓真产物;键盘是 page.keyboard 真按键。
 * 桩只有 /api/pos/**(带 180ms 真往返延时 —— 不延时就排不出队列,队列中间那条路一次都不走)。
 * 文案期望值现场从页面里的真 window.POS_I18N 取。
 *
 * 跑法(仓库根目录):node scripts/_hostile_scan_pos_verify.cjs [用例名]
 */
const path = require('path');
const { chromium } = require('@playwright/test');
const { ROOT, PHONE, serve, gun, shotter, runCases } = require('./_gun_wedge_lib.cjs');

const ONLY = process.argv[2] || '';
const SHOTS = path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/fix2');
const shot = shotter(SHOTS);

const Q1 = '8850999320045';
const GHOST_A = '8850111000039'; // 队列第 2 位:库里没有
const Q3 = '8850999320052';
const GHOST_B = '8850111000046'; // 队列第 4 位:库里没有
const Q5 = '8850999320069';
const BURST = [Q1, GHOST_A, Q3, GHOST_B, Q5];

const NO_PRICE = '8858899000029'; // 只填名字建出来的货:unit_price 为 null
const BOX_ONLY = '8858899000036'; // 主码 · base_unit=ขวด 而 units 里只有 ลัง
const BOX_CODE = '8858899000043'; // 同一件货的箱码

const seed = () => {
    localStorage.setItem('pos_store_token', 'hostile-verify');
    localStorage.setItem('pos_store_name', 'ร้าน HOSTILE');
    localStorage.setItem('mrpilot_lang', 'th');
};

function product(id, name, units, matchedUnit, extra) {
    return Object.assign(
        {
            id,
            name: { th: name, en: name, zh: name, ja: name },
            category_id: 1,
            base_unit: units[0].unit_name,
            base_price: units[0].price,
            image_url: null,
            vat_applicable: true,
            units,
            track_batch: false,
            is_weighed: false,
            stock: { qty_base: '48.000', near_expiry: false },
            matched_unit: matchedUnit,
        },
        extra || {}
    );
}
const unit = (name, barcode, price, factor) => ({
    unit_name: name,
    factor: factor || '1.000',
    barcode,
    price,
    default_sell: !factor,
});
const one = (id, name, unitName, barcode, price) =>
    product(id, name, [unit(unitName, barcode, price)], unitName);

// 「只填名字」那件货:后端 _row_to_item 在没有命名单位行时会现造一行基本单位,price 跟着
// products.unit_price 走 —— 没设价就是 null(不是 "0.00")。这是真回包的形状,不是我编的。
const NO_PRICE_ITEM = product(
    'p-noprice',
    'โยเกิร์ต',
    [{ unit_name: 'ชิ้น', factor: '1.000', barcode: NO_PRICE, price: null, default_sell: true }],
    'ชิ้น',
    { base_price: null }
);

// units 里只有「ลัง」的货:扫主码时后端把 matched_unit 填成 base_unit(ขวด),units 里找不到它。
const BOX_ONLY_ITEM = product(
    'p-boxonly',
    'น้ำอัดลม',
    [unit('ลัง', BOX_CODE, '350.00', '24.000')],
    'ขวด',
    { base_unit: 'ขวด', base_price: '15.00' }
);
const BOX_ONLY_BY_BOX = Object.assign({}, BOX_ONLY_ITEM, { matched_unit: 'ลัง' });

const CATALOG = {
    [Q1]: one('p-water', 'น้ำเปล่า', 'ขวด', Q1, '10.00'),
    [Q3]: one('p-bread', 'ขนมปัง', 'ถุง', Q3, '25.00'),
    [Q5]: one('p-milk', 'นมจืด', 'กล่อง', Q5, '18.00'),
    [NO_PRICE]: NO_PRICE_ITEM,
    [BOX_ONLY]: BOX_ONLY_ITEM,
    [BOX_CODE]: BOX_ONLY_BY_BOX,
};

async function routeCatalog(page, delayMs) {
    await page.route('**/api/pos/products/by-barcode*', async (route) => {
        const code = new URL(route.request().url()).searchParams.get('code');
        const hit = CATALOG[code];
        if (delayMs) await new Promise((r) => setTimeout(r, delayMs));
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

async function login(page, origin) {
    await page.goto(`${origin}/static/pos/pos.html`);
    await page.waitForSelector('#login-cashiers .ca', { timeout: 20000 });
    for (const d of ['1', '2', '3', '4']) await page.click(`#view-login .pad .k[data-pin="${d}"]`);
    await page.waitForSelector('#shift-mask.show', { timeout: 10000 });
    await page.click('#shift-open-go');
    await page.waitForSelector('#view-main.is-active', { timeout: 10000 });
    await page.waitForSelector('#main-grid .prod', { timeout: 10000 });
}

async function boot(browser, origin, delayMs) {
    const page = await browser.newPage({ viewport: PHONE });
    await page.addInitScript(seed);
    await routeCatalog(page, delayMs === undefined ? 180 : delayMs);
    await login(page, origin);
    return page;
}

const failsState = (page) =>
    page.evaluate(() => {
        const box = document.getElementById('bscan-fails');
        return {
            shown: box.classList.contains('show') && box.getBoundingClientRect().height > 0,
            head: (box.querySelector('.bscan-fails-n') || { textContent: '' }).textContent,
            rows: [...box.querySelectorAll('.bscan-fail')].map((r) => ({
                msg: (r.querySelector('.bscan-fail-msg') || { textContent: '' }).textContent,
                code: (
                    r.querySelector('.bscan-code') ||
                    r.querySelector('.bscan-fail-code') || {
                        textContent: '',
                    }
                ).textContent,
                hint: (r.querySelector('.bscan-fail-hint') || { textContent: '' }).textContent,
            })),
        };
    });

const cart = (page) =>
    page.evaluate(() => ({
        grand: document.getElementById('cart-grand').textContent,
        names: [...document.querySelectorAll('#cart-lines .li-nm .n')].map((e) => e.textContent),
        qtys: [...document.querySelectorAll('#cart-lines .q[data-qi]')].map((e) => e.textContent),
    }));

// 枪连扫:一串接一串,不等上一件回来(180ms 往返 → 后面几发落在「还没回来」的窗口里)
async function burstScan(page, codes) {
    for (const c of codes) {
        await page.keyboard.type(c, { delay: 6 });
        await page.keyboard.press('Enter');
        await page.waitForTimeout(20);
    }
    await page.waitForTimeout(180 * codes.length + 900);
}

// ── p1 · 连扫 5 件,第 2 与第 4 是未建档的码 ──────────────────────────────
async function twoFailsInBurst(browser, origin) {
    const page = await boot(browser, origin);
    await burstScan(page, BURST);
    const fails = await failsState(page);
    const c = await cart(page);
    const copy = await page.evaluate(() => {
        const d = window.POS_I18N[window.POS.state.lang];
        return { notfound: d['bscan.notfound'], hint: d['posui.bscan.create_where'] };
    });
    await shot(page, 'p1-two-fails-in-burst.png');
    await page.close();
    const codes = fails.rows.map((r) => r.code);
    return {
        // 扫完之后,店员仍看得见这两件失败了、失败的是哪两个码
        ok:
            fails.shown &&
            fails.rows.length === 2 &&
            codes.includes(GHOST_A) &&
            codes.includes(GHOST_B) &&
            fails.rows.every((r) => r.hint === copy.hint) &&
            c.names.length === 3,
        fails,
        cart: c,
        copy,
    };
}

// ── p2 · 两条失败并存,点其中一条的「拿这个码去搜」 ────────────────────────
// 店员看到两条失败,先处理第一条 —— 另一条不该跟着消失(它那件货还没卖出去)。
async function searchOneFailEatsTheOther(browser, origin) {
    const page = await boot(browser, origin);
    await burstScan(page, [GHOST_A, Q1, GHOST_B]);
    const before = await failsState(page);
    await shot(page, 'p2-before-search.png');
    const act = page.locator('#bscan-fails .bscan-fail').first().locator('.bscan-fail-act');
    const hasAct = (await act.count()) > 0;
    if (hasAct) await act.click();
    await page.waitForTimeout(600);
    const after = await failsState(page);
    await shot(page, 'p2-after-search.png');
    await page.close();
    return {
        // 点掉一条 ≠ 另一条也算完了
        ok: before.rows.length === 2 && hasAct && after.rows.length === 1,
        before,
        after,
        hasAct,
    };
}

// ── p3 · 两条失败并存时按 Esc ────────────────────────────────────────────
async function escapeEatsFails(browser, origin) {
    const page = await boot(browser, origin);
    await burstScan(page, [GHOST_A, Q1, GHOST_B]);
    const before = await failsState(page);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);
    const after = await failsState(page);
    await shot(page, 'p3-after-escape.png');
    await page.close();
    return {
        // Esc 是「关掉最上面那层」的通用手势,不是「这两件货我都不管了」
        ok: before.rows.length === 2 && after.rows.length === 2,
        before,
        after,
    };
}

// ── p4 · 只填名字建出来的货扫进收银台 ────────────────────────────────────
async function onlyNamePriceNull(browser, origin) {
    const page = await boot(browser, origin);
    await gun(page, NO_PRICE);
    await page.waitForTimeout(900);
    const fails = await failsState(page);
    const c = await cart(page);
    const copy = await page.evaluate(() => {
        const d = window.POS_I18N[window.POS.state.lang];
        return {
            noprice: d['posui.cart.unit_no_price'],
            unknown: d['posui.cart.unit_unknown'],
            hint: d['posui.cart.fix_in_backoffice'],
        };
    });
    await shot(page, 'p4-only-name-price-null.png');
    await page.close();
    const want = copy.noprice.replace('{name}', 'โยเกิร์ต').replace('{unit}', 'ชิ้น');
    return {
        // ฿0 不许进车;拒收那句话得说清是「没设价」,不是「单位不认识」
        ok:
            c.names.length === 0 &&
            fails.rows.length === 1 &&
            fails.rows[0].msg === want &&
            fails.rows[0].hint === copy.hint,
        fails,
        cart: c,
        want,
        copy,
    };
}

// ── p5 · units 里只有「ลัง」的货扫主码 ────────────────────────────────────
async function boxOnlyBaseScan(browser, origin) {
    const page = await boot(browser, origin);
    await gun(page, BOX_ONLY); // 主码 → matched_unit=ขวด,units 里没有这一行
    await page.waitForTimeout(900);
    const afterBase = await cart(page);
    await gun(page, BOX_CODE); // 同一件货的箱码
    await page.waitForTimeout(900);
    const afterBox = await cart(page);
    const fails = await failsState(page);
    await shot(page, 'p5-box-only-base-scan.png');
    await page.close();
    return {
        // 扫主码按基本单位 ฿15 卖得出去;再扫箱码必须落成【另一行】——
        // 并成一行就说明刚才那扫其实挂在 ลัง 上,库存要扣 24 瓶
        ok:
            afterBase.names.length === 1 &&
            afterBase.grand.indexOf('15') >= 0 &&
            afterBox.names.length === 2 &&
            fails.rows.length === 0,
        afterBase,
        afterBox,
        fails,
    };
}

const CASES = [
    ['p1_twoFailsInBurst', twoFailsInBurst],
    ['p2_searchOneFailEatsTheOther', searchOneFailEatsTheOther],
    ['p3_escapeEatsFails', escapeEatsFails],
    ['p4_onlyNamePriceNull', onlyNamePriceNull],
    ['p5_boxOnlyBaseScan', boxOnlyBaseScan],
];

(async () => {
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch();
    const failed = await runCases(
        CASES.filter(([name]) => !ONLY || name.indexOf(ONLY) >= 0),
        (fn) => fn(browser, origin),
        path.join(SHOTS, 'report-hostile-pos.json')
    );
    await browser.close();
    server.close();
    process.exit(failed ? 1 : 0);
})().catch((e) => {
    console.error('HOSTILE POS CRASH', e);
    process.exit(2);
});
