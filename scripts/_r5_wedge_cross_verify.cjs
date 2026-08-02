/*
 * scripts/_r5_wedge_cross_verify.cjs · 第五轮:跨界快照 + 框外那半条判据
 *
 * 前四轮补的都是「这一串是不是枪打的」这把尺子本身。这一轮补的是尺子挂在哪儿:
 *
 *   ② 跨界 —— 快照只在本串第一个键上取,而 currentTarget 每个键都更新。一串枪从框外开头、
 *      结尾落进声明接枪的框(产品自己制造这个场景:inventory-scan.ts 命中后 qty.focus(),
 *      枪比网络快时上一箱的应答就落在这一串中间),info.field 停在 false ——
 *      looksLikeGun 不判、restoreField 不还原,两道保护同时失效,而码照旧发出去查。
 *   ③ 框外 —— `if (info.field && !looksLikeGun(...))`,repeat / 整串一个字符只在落进框里时
 *      被问到。收银主屏的焦点常态就在 body 上,压住一个键的那一串直接被当条码查了。
 *
 * 每条都验两个方向,四轮的原话是「只量了一侧的代价」:
 *   正向 c1/c1b/c2  别再犯原病(数量框不许被写脏、按住键不放不许当扫码)
 *   反向 c3/c4      别把对面弄坏(框外真枪照旧能扫、真枪打进已填的框照旧还原)
 *
 * 跑法(仓库根目录):node scripts/_r5_wedge_cross_verify.cjs [用例名]
 */
const path = require('path');
const { chromium } = require('@playwright/test');
const {
    ROOT,
    PHONE,
    DESKTOP,
    serve,
    cdpGun,
    armTwoRulers,
    readTwoRulers,
    shotter,
    runCases,
} = require('./_gun_wedge_lib.cjs');

const ONLY = process.argv[2] || '';
const SHOTS = path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/fix4');
const shot = shotter(SHOTS);

const COLA = '8850999320014';
const MILK = '4901234567894';
const LOT = 'LOT-B240301';
const JUMP_AT = 5; // 第 5 个 keydown 时上一箱的应答回来 → 光标被塞进数量框

// ── 收银台侧 ───────────────────────────────────────────────────────────────
const POS_SEED = () => {
    localStorage.setItem('pos_store_token', 'r5-cross');
    localStorage.setItem('pos_store_name', 'ร้าน CROSS');
    localStorage.setItem('mrpilot_lang', 'th');
};

const COLA_ITEM = {
    id: 'p-cola',
    name: { th: 'โค้ก', en: 'Coke', zh: '可乐', ja: 'コーラ' },
    category_id: 1,
    base_unit: 'ขวด',
    base_price: '15.00',
    image_url: null,
    vat_applicable: true,
    units: [
        { unit_name: 'ขวด', factor: '1.000', barcode: COLA, price: '15.00', default_sell: true },
    ],
    track_batch: false,
    is_weighed: false,
    stock: { qty_base: '48.000', near_expiry: false },
    matched_unit: 'ขวด',
};

async function posBoot(browser, origin, bag, viewport) {
    const page = await browser.newPage({ viewport: viewport || PHONE });
    await page.addInitScript(POS_SEED);
    await page.route('**/api/pos/products/by-barcode*', async (route) => {
        const code = new URL(route.request().url()).searchParams.get('code');
        bag.asked.push(code);
        const hit = code === COLA;
        await route.fulfill({
            status: hit ? 200 : 404,
            contentType: 'application/json',
            body: JSON.stringify(
                hit
                    ? { ok: true, data: COLA_ITEM }
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

const posCart = (page) =>
    page.evaluate(() => ({
        focus: document.activeElement.tagName,
        qtys: [...document.querySelectorAll('#cart-lines .q[data-qi]')].map((e) => e.textContent),
        grand: document.getElementById('cart-grand').textContent,
        fails: [...document.querySelectorAll('#bscan-fails .bscan-fail')].map((r) =>
            (r.querySelector('.bscan-code') || { textContent: '' }).textContent.trim()
        ),
    }));

// ── c2 · 收银主屏按住一个键不放(正向)────────────────────────────────────
// 柜台上东西压住一个键、枪的触发键卡住,都走框外这条路 —— 那里 looksLikeGun 一次都不被问到。
async function heldKeyOnCashierMain(browser, origin) {
    const bag = { asked: [] };
    const page = await posBoot(browser, origin, bag);
    const cdp = await page.context().newCDPSession(page);
    await armTwoRulers(page);
    const focusWas = await page.evaluate(() => document.activeElement.tagName);
    const tap = (ch, repeat) =>
        cdp
            .send('Input.dispatchKeyEvent', {
                type: 'keyDown',
                key: ch,
                text: ch,
                windowsVirtualKeyCode: ch.charCodeAt(0),
                autoRepeat: repeat,
            })
            .catch(() => {});
    for (let i = 0; i < 12; i += 1) {
        tap('0', i > 0); // 第一发是真按下,后面 11 发是系统自动重复
        await new Promise((r) => setTimeout(r, 25));
    }
    for (const ch of '57') {
        tap(ch, false); // 松手时手指蹭到旁边两个键
        await new Promise((r) => setTimeout(r, 25));
    }
    const m = await readTwoRulers(page);
    await page.waitForTimeout(1200);
    const c = await posCart(page);
    await shot(page, 'c2-held-key-cashier-main.png');
    await page.close();
    const ok = bag.asked.length === 0 && c.fails.length === 0;
    return {
        ok,
        focusWas,
        repeatFlags: m.repeats,
        stampMax: m.stampMax,
        asked: bag.asked,
        fails: c.fails,
        why: ok
            ? ''
            : `按住一个键不放在收银主屏被当成扫码:查了 ${JSON.stringify(bag.asked)} · ` +
              `屏上冒出失败条 ${JSON.stringify(c.fails)}`,
    };
}

// ── c3 · 收银主屏真枪(反向)──────────────────────────────────────────────
// c2 那条判据搬到框外之后,主路径必须原样活着 —— 收银主屏扫码是整个功能的主路径。
async function realGunOnCashierMain(browser, origin) {
    const bag = { asked: [] };
    const page = await posBoot(browser, origin, bag);
    const cdp = await page.context().newCDPSession(page);
    await armTwoRulers(page);
    const focusWas = await page.evaluate(() => document.activeElement.tagName);
    await cdpGun(cdp, COLA, 8, 'Enter');
    const fast = await readTwoRulers(page);
    await page.waitForTimeout(1200);
    const c = await posCart(page);
    await shot(page, 'c3-real-gun-cashier-main.png');
    await page.close();
    const ok = bag.asked.length === 1 && bag.asked[0] === COLA && c.qtys.join(',') === '1';
    return {
        ok,
        focusWas,
        stampMax: fast.stampMax,
        asked: bag.asked,
        cart: c,
        why: ok
            ? ''
            : `收银主屏的真枪不灵了:查了 ${JSON.stringify(bag.asked)} · 车里数量 ` +
              `${JSON.stringify(c.qtys)} · 失败清单 ${JSON.stringify(c.fails)}`,
    };
}

// ── 主站入库弹窗侧 ─────────────────────────────────────────────────────────
const P_COLA = { id: 'p-cola', name_th: 'โค้ก', name_zh: '可乐', track_batch: false };
const P_MILK = { id: 'p-milk', name_th: 'นมสด', name_zh: '鲜奶', track_batch: true };
const LOOKUP = {
    [COLA]: { product: P_COLA, matched_by: 'product', matched_unit: 'ขวด' },
    [MILK]: { product: P_MILK, matched_by: 'product', matched_unit: 'กล่อง' },
};
const STOCK = {
    ok: true,
    data: {
        items: [
            {
                product_id: 'p-cola',
                name: { th: 'โค้ก', zh: '可乐' },
                barcode: COLA,
                base_unit: 'ขวด',
                qty_on_hand: 12,
                min_stock: 5,
                avg_cost: 9.5,
                status: 'ok',
                track_batch: false,
                batches: [],
            },
        ],
        summary: { sku_count: 1, stock_value: 114, low_count: 0, out_count: 0 },
    },
};

async function homeBoot(browser, origin, bag) {
    const page = await browser.newPage({ viewport: DESKTOP });
    await page.addInitScript(() => localStorage.setItem('mrpilot_token', 'r5-cross'));
    await page.route('https://cdnjs.cloudflare.com/**', (r) => r.abort());
    await page.route('**/api/**', async (route) => {
        const url = new URL(route.request().url());
        if (url.pathname === '/api/sales/products/lookup') {
            const code = url.searchParams.get('barcode');
            bag.asked.push(code);
            const hit = LOOKUP[code];
            if (!hit) return route.fulfill({ status: 404, json: { detail: 'not_found' } });
            return route.fulfill({ json: hit });
        }
        if (url.pathname === '/api/inventory/stock') return route.fulfill({ json: STOCK });
        if (url.pathname === '/api/me')
            return route.fulfill({ json: { email: 'r5@e2e', role: 'owner', plan: 'pro' } });
        return route.fulfill({ json: { ok: true, data: {}, items: [] } });
    });
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
        document.querySelectorAll('.page').forEach((p) => p.classList.remove('active'));
        document.getElementById('page-inventory').classList.add('active');
        window.loadInventoryPage();
    });
    await page.locator('#inv-tbody tr').first().waitFor({ timeout: 15000 });
    await page.locator('#inv-btn-in').click();
    await page.locator('#inv-in-mask .inv-scan').waitFor({ timeout: 10000 });
    await page.keyboard.type(MILK, { delay: 5 });
    await page.keyboard.press('Enter');
    await page.locator('#inv-in-mask-rows [data-row] [data-batchcell]').first().waitFor({
        state: 'visible',
        timeout: 10000,
    });
    return page;
}

/**
 * 上一箱的查码应答回来时把光标塞进数量框 —— 产品自己干的事(inventory-scan.ts 命中后
 * qty.focus())。这里按第几个 keydown 触发,好让「应答落在这一串中间」变成确定的。
 *
 * inDispatch=false 走 setTimeout(0):落在两发按键【之间】,跟真应答同形(它是网络回调)。
 * inDispatch=true  在 keydown 处理器里直接挪:那一发的 keydown target 还是旧位置,字符却
 *   落进新框 —— 只认 keydown 取快照会把头一个字符漏在外面,还原成「1 加一位」照样是错的数量。
 */
async function armFocusJump(page, nth, sel, inDispatch) {
    await page.evaluate(
        ([atNth, selector, sync]) => {
            window.__fj = { n: 0, hit: 0 };
            window.__fjProbe = () => {
                window.__fj.n += 1;
                if (window.__fj.n !== atNth) return;
                const jump = () => {
                    const el = document.querySelector(selector);
                    if (!el) return;
                    el.focus();
                    window.__fj.hit = 1;
                };
                if (sync) jump();
                else setTimeout(jump, 0);
            };
            window.addEventListener('keydown', window.__fjProbe, true);
        },
        [nth, sel, !!inDispatch]
    );
}

const QTY_SEL = '#inv-in-mask-rows [data-row] [data-k="qty"]';

// ── c1 · 一串枪从框外开头、结尾落进数量框(正向 + 反向绑在一起)───────────
async function crossBoundaryGun(browser, origin, inDispatch) {
    const bag = { asked: [] };
    const page = await homeBoot(browser, origin, bag);
    const qty = page.locator(QTY_SEL).first();
    // 焦点先离开数量框:这一串要从框外开头(收银/入库屏的常态),中途才被塞进去。
    await page.evaluate(() => document.activeElement.blur());
    const focusWas = await page.evaluate(() => document.activeElement.tagName);
    const before = await qty.inputValue();
    bag.asked.length = 0;

    const cdp = await page.context().newCDPSession(page);
    await armTwoRulers(page);
    await armFocusJump(page, JUMP_AT, QTY_SEL, inDispatch);
    await cdpGun(cdp, COLA, 8, 'Enter');
    const m = await readTwoRulers(page);
    await page.waitForTimeout(1500);
    const jumped = await page.evaluate(() => (window.__fj || {}).hit === 1);
    const after = await qty.inputValue();
    const rows = await page.locator('#inv-in-mask-rows [data-row]').count();
    await shot(page, inDispatch ? 'c1b-cross-in-dispatch.png' : 'c1-cross-boundary-gun.png');
    await page.close();
    // 两侧同时成立才算过:数量框回到扫之前(正向)且这一发照旧发出去查了(反向)。
    const ok =
        jumped && after === before && bag.asked.length === 1 && bag.asked[0] === COLA && rows === 2;
    return {
        ok,
        focusWas,
        focusJumped: jumped,
        qtyBefore: before,
        qtyAfter: after,
        stampMax: m.stampMax,
        asked: bag.asked,
        rows,
        why: ok
            ? ''
            : `数量框 ${before} → ${after} · 一发枪(${COLA})发出 ${bag.asked.length} 次查码 ` +
              `${JSON.stringify(bag.asked)} · 单上 ${rows} 行 · 光标真挪进去了=${jumped}`,
    };
}

// ── c4 · 真枪打进已填好的批号框(反向)────────────────────────────────────
// 还原从「只还原最后那个框」改成「碰过的逐个还原」,原本就对的那条路必须原样活着。
async function gunIntoFilledBatch(browser, origin) {
    const bag = { asked: [] };
    const page = await homeBoot(browser, origin, bag);
    const batch = page.locator('#inv-in-mask-rows [data-row] [data-k="batch_no"]').first();
    await batch.click();
    await page.keyboard.type(LOT, { delay: 120 });
    await page.waitForTimeout(400); // 手写与枪之间隔开(引擎语义,不是本例要验的东西)
    const before = await batch.inputValue();
    bag.asked.length = 0;

    const cdp = await page.context().newCDPSession(page);
    await armTwoRulers(page);
    await cdpGun(cdp, COLA, 8, 'Enter');
    const m = await readTwoRulers(page);
    await page.waitForTimeout(1500);
    const after = await batch.inputValue();
    const rows = await page.locator('#inv-in-mask-rows [data-row]').count();
    await shot(page, 'c4-gun-into-filled-batch.png');
    await page.close();
    const ok = before === LOT && after === LOT && bag.asked.length === 1 && bag.asked[0] === COLA;
    return {
        ok,
        batchBefore: before,
        batchAfter: after,
        stampMax: m.stampMax,
        asked: bag.asked,
        rows,
        why: ok
            ? ''
            : `批号 ${before} → ${after} · 一发枪(${COLA})发出 ${bag.asked.length} 次查码 ` +
              JSON.stringify(bag.asked),
    };
}

const CASES = [
    ['c1_crossBoundaryGun', (b, o) => crossBoundaryGun(b, o, false)],
    ['c1b_crossBoundaryInDispatch', (b, o) => crossBoundaryGun(b, o, true)],
    ['c2_heldKeyOnCashierMain', heldKeyOnCashierMain],
    ['c3_realGunOnCashierMain', realGunOnCashierMain],
    ['c4_gunIntoFilledBatch', gunIntoFilledBatch],
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
            path.join(SHOTS, 'report-r5-wedge-cross.json')
        );
    } finally {
        await browser.close();
        server.close();
    }
    process.exit(failed ? 1 : 0);
})().catch((e) => {
    console.error('R5 WEDGE CROSS CRASH', e);
    process.exit(2);
});
