/*
 * scripts/_r4_fails_verify.cjs · 第四轮对抗:失败清单的四个清空口子(真浏览器 · 真点击)
 *
 * 三轮的原始复现条件是「两条失败并存 → 点第一条的『搜这个码』/ 按 Esc → 整份被清空」。
 * 本轮那份验收(_hostile_scan_pos_verify.cjs 的 p3)按了 Esc,但它整例没开过取景层 ——
 * 而产品里那句是 `if (e.key === 'Escape' && cameraOpen()) close()`。取景层没开,close() 压根
 * 不会被调用,断言于是在一条走不到的路上绿。f0 把这件事量出来(取景层开没开是可读的事实),
 * f1 才是三轮那一幕的真复现:取景层真开着,Esc 真关掉它,再看清单还在不在。
 *
 * 另外三条是本轮新加的销账口,同样只认「屏上还剩几条」:
 *   f2 命中后销账      老板补录了条码,店员回头重扫 → 那条欠账得消失,不能让他再补一件
 *   f3 同码连扫去重    店员以为没扫上又扫一遍 → 还是一条,不是三条
 *   f4 收单时清        这一单结束(点「清空」)→ 上一位客人的欠账不许顶在下一位的屏上
 *
 * 文案期望值现场从页面里真的 window.POS_I18N 取,零注入。
 *
 * 跑法(仓库根目录):node scripts/_r4_fails_verify.cjs [用例名]
 */
const path = require('path');
const { chromium } = require('@playwright/test');
const { ROOT, PHONE, DESKTOP, serve, shotter, runCases } = require('./_gun_wedge_lib.cjs');

const ONLY = process.argv[2] || '';
const SHOTS = path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/fix3');
const shot = shotter(SHOTS);

const GHOST_A = '8850111000039';
const GHOST_B = '8850111000046';
const LATE = '8850111000053'; // 老板补录之后才认得的码

const ITEM = {
    id: 'p-late',
    name: { th: 'โยเกิร์ต', en: 'Yogurt', zh: '酸奶', ja: 'ヨーグルト' },
    category_id: 1,
    base_unit: 'ถ้วย',
    base_price: '22.00',
    image_url: null,
    vat_applicable: true,
    units: [
        { unit_name: 'ถ้วย', factor: '1.000', barcode: LATE, price: '22.00', default_sell: true },
    ],
    track_batch: false,
    is_weighed: false,
    stock: { qty_base: '30.000', near_expiry: false },
    matched_unit: 'ถ้วย',
};

const seed = () => {
    localStorage.setItem('pos_store_token', 'r4-fails');
    localStorage.setItem('pos_store_name', 'ร้าน FAILS');
    localStorage.setItem('mrpilot_lang', 'th');
};

// known 是可变的:f2 要在跑到一半时让后端「认得」这个码(老板刚在后台补录)。
async function boot(browser, origin, known, viewport) {
    const page = await browser.newPage({ viewport: viewport || PHONE });
    await page.addInitScript(seed);
    await page.route('**/api/pos/products/by-barcode*', async (route) => {
        const code = new URL(route.request().url()).searchParams.get('code');
        const hit = known.has(code);
        await route.fulfill({
            status: hit ? 200 : 404,
            contentType: 'application/json',
            body: JSON.stringify(
                hit
                    ? { ok: true, data: Object.assign({}, ITEM, { units: ITEM.units }) }
                    : { ok: false, error: { code: 'pos.product_not_found', detail: null } }
            ),
        });
    });
    await page.goto(`${origin}/static/pos/pos.html`);
    await page.waitForSelector('#login-cashiers .ca', { timeout: 20000 });
    for (const d of ['1', '2', '3', '4']) await page.click(`#view-login .pad .k[data-pin="${d}"]`);
    await page.waitForSelector('#shift-mask.show', { timeout: 10000 });
    await page.click('#shift-open-go');
    await page.waitForSelector('#view-main.is-active', { timeout: 10000 });
    await page.waitForSelector('#main-grid .prod', { timeout: 10000 });
    return page;
}

// 真按键进产品自己的楔子(不走 POS.scan.submit 后门):失败是怎么进清单的也是被验的一部分。
async function gunScan(page, code) {
    await page.keyboard.type(code, { delay: 6 });
    await page.keyboard.press('Enter');
    await page.waitForTimeout(500);
}

const state = (page) =>
    page.evaluate(() => ({
        cameraOpen: document.getElementById('bscan-mask').classList.contains('show'),
        failCodes: [...document.querySelectorAll('#bscan-fails .bscan-fail')].map((r) =>
            (
                r.querySelector('.bscan-code') ||
                r.querySelector('.bscan-fail-code') || { textContent: '' }
            ).textContent.trim()
        ),
        head: (
            document.querySelector('#bscan-fails .bscan-fails-n') || { textContent: '' }
        ).textContent.trim(),
        cartNames: [...document.querySelectorAll('#cart-lines .li-nm .n')].map(
            (e) => e.textContent
        ),
    }));

// 取景层开着但不真开相机:解码器 404 → 停在错误卡。本组验的是清单的生死,不是解码。
async function openCameraLayer(page) {
    await page.route('**/static/dist/scan.js*', (r) => r.fulfill({ status: 404, body: '' }));
    await page.click('#main-scan-btn');
    await page.waitForSelector('#bscan-mask.show', { timeout: 10000 });
}

// ── f0 · 上一轮那条 Esc 用例到底走没走到 close() ────────────────────────────
// 不开取景层就按 Esc:产品里那句直接短路。断言的是「这条路走不到」,所以这一例 ok 的含义是
// 「上一轮那份绿是空转出来的」—— 它绿不绿跟 close() 清不清清单没有任何关系。
async function escIsInertWithoutCamera(browser, origin) {
    const page = await boot(browser, origin, new Set());
    await gunScan(page, GHOST_A);
    await gunScan(page, GHOST_B);
    const before = await state(page);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);
    const after = await state(page);
    await shot(page, 'f0-esc-without-camera.png');
    await page.close();
    return {
        ok: before.cameraOpen === false && before.failCodes.length === 2,
        note: '取景层没开 → Escape 分支短路,close() 一次都没被调用',
        cameraOpenBefore: before.cameraOpen,
        before: before.failCodes,
        after: after.failCodes,
    };
}

// ── f1 · 三轮那一幕的真复现:取景层真开着,Esc 真关掉它 ─────────────────────
async function escWithCameraOpen(browser, origin) {
    const page = await boot(browser, origin, new Set());
    await gunScan(page, GHOST_A);
    await gunScan(page, GHOST_B);
    await openCameraLayer(page);
    const before = await state(page);
    await shot(page, 'f1-before-esc-camera-open.png');
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);
    const after = await state(page);
    await shot(page, 'f1-after-esc-camera-open.png');
    await page.close();
    return {
        // 前提:Esc 之前取景层真开着(不然这一例跟 f0 一样是空转)
        ok:
            before.cameraOpen === true &&
            before.failCodes.length === 2 &&
            after.cameraOpen === false &&
            after.failCodes.length === 2,
        before,
        after,
        why:
            before.cameraOpen && after.failCodes.length !== 2
                ? `Esc 关取景层顺手清掉了失败清单:2 条 → ${after.failCodes.length} 条`
                : '',
    };
}

// ── f2 · 老板补录条码后重扫 → 那条欠账销掉 ──────────────────────────────────
async function resolveOnHit(browser, origin) {
    const known = new Set();
    const page = await boot(browser, origin, known);
    await gunScan(page, LATE);
    const before = await state(page);
    known.add(LATE); // 老板在后台把条码补上了
    await gunScan(page, LATE);
    const after = await state(page);
    await shot(page, 'f2-resolved-on-hit.png');
    await page.close();
    return {
        ok:
            before.failCodes.length === 1 &&
            before.failCodes[0] === LATE &&
            after.failCodes.length === 0 &&
            after.cartNames.length === 1,
        before,
        after,
        why:
            after.failCodes.length !== 0
                ? '货已经进车了,清单还写着它没进 —— 店员照着补一件就是收两遍钱'
                : '',
    };
}

// ── f3 · 同一个码连扫三遍 → 清单上还是一条 ─────────────────────────────────
async function dedupeSameCode(browser, origin) {
    const page = await boot(browser, origin, new Set());
    for (let i = 0; i < 3; i += 1) await gunScan(page, GHOST_A);
    const s = await state(page);
    const want = await page.evaluate(() =>
        window.POS_I18N[window.POS.state.lang]['posui.bscan.fails_n'].replace('{n}', '1')
    );
    await shot(page, 'f3-dedupe-same-code.png');
    await page.close();
    return {
        ok: s.failCodes.length === 1 && s.head === want,
        head: s.head,
        want,
        failCodes: s.failCodes,
        why: s.failCodes.length !== 1 ? `同一件货记了 ${s.failCodes.length} 笔欠账` : '',
    };
}

// ── f4 · 这一单结束 → 上一位客人的欠账不许留在屏上 ───────────────────────────
async function clearedOnSaleEnd(browser, origin) {
    const known = new Set([LATE]);
    // 「清空」在手机版收在底部 sheet 里(视口外,点不到)。这一例验的是清单跟不跟着一单走,
    // 不是那颗按钮藏在哪 —— 用桌面版视口,按钮就在购物车面板上,真点得到。
    const page = await boot(browser, origin, known, DESKTOP);
    await gunScan(page, LATE); // 车里先有一件真货,「清空」按钮才有意义
    known.delete(LATE);
    await gunScan(page, GHOST_A);
    await gunScan(page, GHOST_B);
    const before = await state(page);
    await page.click('#cart-clear-btn'); // 真按钮,不是 POS.scan.saleEnded()
    await page.waitForTimeout(400);
    const after = await state(page);
    await shot(page, 'f4-cleared-on-sale-end.png');
    await page.close();
    return {
        ok:
            before.failCodes.length === 2 &&
            before.cartNames.length === 1 &&
            after.failCodes.length === 0 &&
            after.cartNames.length === 0,
        before,
        after,
        why: after.failCodes.length !== 0 ? '上一位客人那两件没进车的货顶在下一位客人的屏上' : '',
    };
}

const CASES = [
    ['f0_escIsInertWithoutCamera', escIsInertWithoutCamera],
    ['f1_escWithCameraOpen', escWithCameraOpen],
    ['f2_resolveOnHit', resolveOnHit],
    ['f3_dedupeSameCode', dedupeSameCode],
    ['f4_clearedOnSaleEnd', clearedOnSaleEnd],
];

(async () => {
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch();
    let failed = 0;
    try {
        failed = await runCases(
            CASES.filter(([n]) => !ONLY || n.indexOf(ONLY) >= 0),
            (fn) => fn(browser, origin),
            path.join(SHOTS, 'report-r4-fails.json')
        );
    } finally {
        await browser.close();
        server.close();
    }
    process.exit(failed ? 1 : 0);
})().catch((e) => {
    console.error('R4 FAILS CRASH', e);
    process.exit(2);
});
