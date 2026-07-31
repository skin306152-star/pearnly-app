/*
 * scripts/_r4_wedge_split_verify.cjs · 第四轮对抗:长任务比【断串计时器】还长
 *
 * 这一轮把「量事件产生时刻」这把尺子修准了 —— 间隔算的是 KeyboardEvent.timeStamp,主线程卡
 * 多久都不影响。但楔子里还有第二把墙钟尺子没跟着换:onKeydown 末尾那只
 * `setTimeout(finalize, MAX_GAP_MS=150)`。它是 setTimeout,主线程被堵住时它跟着延后,解封后
 * 立刻到期 —— 而排在它后面的正是同一发枪剩下的那半串字符。
 *
 * 上一轮的取证用例(_gun_ruler_verify.cjs 的 ruler)堵的是 120ms:比 150ms 短,计时器还没到
 * 期就被后续按键 clearTimeout 掉了,所以量不出这条。真页面上 120ms 不是上限 —— 收银主屏
 * loadGrid() 重画、切屏、GC、同步写 localStorage 都能轻松过 200ms。
 *
 * 所以本脚本只把那个数从 120 抬到 300,别的一律照旧(真产品页、CDP 发了就走的真枪、
 * 8ms/字符、两把尺子同时量)。两屏各打一发:
 *   w1 cashierSplit  收银主屏(焦点在 body · 楔子直接收)
 *   w2 batchSplit    入库弹窗批号框(声明接枪 · 店员已经手写了批号在里面)
 *   w3 heldKeyOnMain 收银主屏按住一个键不放(框外那条路上 looksLikeGun 根本不参与)
 *
 * 跑法(仓库根目录):node scripts/_r4_wedge_split_verify.cjs [用例名]
 */
const path = require('path');
const { chromium } = require('@playwright/test');
const {
    ROOT,
    PHONE,
    DESKTOP,
    serve,
    cdpGun,
    armLongTask,
    armTwoRulers,
    readTwoRulers,
    shotter,
    runCases,
} = require('./_gun_wedge_lib.cjs');

const ONLY = process.argv[2] || '';
const SHOTS = path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/fix3');
const shot = shotter(SHOTS);

const COLA = '8850999320014';
const MILK = '4901234567894';
const LOT = 'LOT-B240301';
// > 楔子的 MAX_GAP_MS(150):这一个数就是本脚本与上一轮取证的全部差别。留成可调是为了扫一遍
// ——「300 过了」不等于「600 也过」,而计时器饿死保护这类调度行为只有换着数字量才看得出。
const BLOCK_MS = Number(process.env.R4_BLOCK_MS || 300);
const AT_NTH = 5;

// ── 收银台侧 ───────────────────────────────────────────────────────────────
const POS_SEED = () => {
    localStorage.setItem('pos_store_token', 'r4-split');
    localStorage.setItem('pos_store_name', 'ร้าน SPLIT');
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
        names: [...document.querySelectorAll('#cart-lines .li-nm .n')].map((e) => e.textContent),
        qtys: [...document.querySelectorAll('#cart-lines .q[data-qi]')].map((e) => e.textContent),
        grand: document.getElementById('cart-grand').textContent,
        fails: [...document.querySelectorAll('#bscan-fails .bscan-fail')].map((r) =>
            (
                r.querySelector('.bscan-code') ||
                r.querySelector('.bscan-fail-code') || { textContent: '' }
            ).textContent.trim()
        ),
    }));

// ── w1 · 收银主屏:一发真枪,中间堵 300ms ───────────────────────────────────
async function cashierSplit(browser, origin) {
    const bag = { asked: [] };
    const page = await posBoot(browser, origin, bag);
    const focus = await page.evaluate(() => document.activeElement.tagName);
    const cdp = await page.context().newCDPSession(page);
    await armTwoRulers(page);
    await armLongTask(page, AT_NTH, BLOCK_MS);
    await cdpGun(cdp, COLA, 8, 'Enter');
    const m = await readTwoRulers(page);
    await page.waitForTimeout(1500);
    const c = await posCart(page);
    await shot(page, 'w1-cashier-split.png');
    await page.close();
    // 一发枪 = 一件货。断的是网络上真发出去的那几个码,不是某个函数回了什么。
    const ok = bag.asked.length === 1 && bag.asked[0] === COLA && c.qtys.join(',') === '1';
    return {
        ok,
        focusWas: focus,
        blockedMs: m.blockedMs,
        stampMax: m.stampMax,
        perfMax: m.perfMax,
        asked: bag.asked,
        cart: c,
        why: ok
            ? ''
            : `一发枪(${COLA})被拆成 ${bag.asked.length} 发查码:${JSON.stringify(bag.asked)} · ` +
              `车里 ${c.names.length} 行 · 失败清单 ${JSON.stringify(c.fails)}`,
    };
}

// ── w3 · 收银主屏按住一个键不放 ─────────────────────────────────────────────
// 框外那条路上 finalize 直接 `s.cb(code)` —— looksLikeGun 的 repeat / hasTwoDistinct 一条都
// 不走。收银主屏正是店员手边最常被压住的地方(靠在柜台上、猫踩键盘、枪的触发键卡住)。
async function heldKeyOnMain(browser, origin) {
    const bag = { asked: [] };
    const page = await posBoot(browser, origin, bag);
    const cdp = await page.context().newCDPSession(page);
    await armTwoRulers(page);
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
        tap('0', i > 0);
        await new Promise((r) => setTimeout(r, 25));
    }
    for (const ch of '57') {
        tap(ch, false);
        await new Promise((r) => setTimeout(r, 25));
    }
    const m = await readTwoRulers(page);
    await page.waitForTimeout(1200);
    const c = await posCart(page);
    await shot(page, 'w3-held-key-on-main.png');
    await page.close();
    const ok = bag.asked.length === 0;
    return {
        ok,
        repeatFlags: m.repeats,
        stampMax: m.stampMax,
        asked: bag.asked,
        cart: c,
        why: ok
            ? ''
            : `按住一个键不放在收银主屏被当成扫码:查了 ${JSON.stringify(bag.asked)} · ` +
              `屏上冒出失败条 ${JSON.stringify(c.fails)}`,
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
    await page.addInitScript(() => localStorage.setItem('mrpilot_token', 'r4-split'));
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
            return route.fulfill({ json: { email: 'r4@e2e', role: 'owner', plan: 'pro' } });
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

// ── w2 · 批号框里已经有店员手写的批号,再来一发被堵住的真枪 ─────────────────
async function batchSplit(browser, origin) {
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
    await armLongTask(page, AT_NTH, BLOCK_MS);
    await cdpGun(cdp, COLA, 8, 'Enter');
    const m = await readTwoRulers(page);
    await page.waitForTimeout(1500);
    const after = await batch.inputValue();
    const rows = await page.locator('#inv-in-mask-rows [data-row]').count();
    const msg = await page.locator('#inv-in-mask-scan-msg').innerText();
    await shot(page, 'w2-batch-split.png');
    await page.close();
    const ok = before === LOT && after === LOT && bag.asked.length === 1 && bag.asked[0] === COLA;
    return {
        ok,
        before,
        after,
        blockedMs: m.blockedMs,
        stampMax: m.stampMax,
        perfMax: m.perfMax,
        asked: bag.asked,
        rows,
        msg,
        why: ok
            ? ''
            : `批号 ${before} → ${after} · 一发枪(${COLA})发出了 ` +
              `${bag.asked.length} 次查码 ${JSON.stringify(bag.asked)}`,
    };
}

// ── w4 · 长任务落在两发按键【之间】(不是某一发的派发里)────────────────────
// w1/w2 里的长任务挂在 keydown 捕获上,于是它跟楔子的处理器在同一个事件派发里跑完 ——
// 楔子那句 clearTimeout 紧跟在后面,150ms 计时器一次机会都没有。真页面上堵住主线程的东西
// 大多不在按键派发里:上一件货查回来之后的 renderCart、切屏重画、GC。那种堵法下 150ms
// 计时器会在堵的过程中到期,解封时它跟排队的后半串字符抢先后 —— 抢赢了就把一发拆成两发。
async function armGapTask(page, nth, ms) {
    await page.evaluate(
        ([atNth, blockMs]) => {
            window.__lt = { n: 0, blocked: 0 };
            window.__ltProbe = () => {
                window.__lt.n += 1;
                if (window.__lt.n !== atNth) return;
                // 排进宏任务队列:这一发按键派发完了才开始堵,楔子的 150ms 计时器已经挂上
                setTimeout(() => {
                    const end = Date.now() + blockMs;
                    while (Date.now() < end) {
                        /* 同步长任务 */
                    }
                    window.__lt.blocked = blockMs;
                }, 0);
            };
            window.addEventListener('keydown', window.__ltProbe, true);
        },
        [nth, ms]
    );
}

async function gapTaskSplit(browser, origin) {
    const bag = { asked: [] };
    const page = await posBoot(browser, origin, bag);
    const cdp = await page.context().newCDPSession(page);
    await armTwoRulers(page);
    await armGapTask(page, AT_NTH, BLOCK_MS);
    await cdpGun(cdp, COLA, 8, 'Enter');
    const m = await readTwoRulers(page);
    await page.waitForTimeout(1500);
    const c = await posCart(page);
    await shot(page, 'w4-gap-task-split.png');
    await page.close();
    const ok = bag.asked.length === 1 && bag.asked[0] === COLA && c.qtys.join(',') === '1';
    return {
        ok,
        blockedMs: m.blockedMs,
        stampMax: m.stampMax,
        perfMax: m.perfMax,
        asked: bag.asked,
        cart: c,
        why: ok
            ? ''
            : `一发枪(${COLA})被拆成 ${bag.asked.length} 发:${JSON.stringify(bag.asked)} · ` +
              `车里 ${c.names.length} 行 · 失败清单 ${JSON.stringify(c.fails)}`,
    };
}

// ── w5 · 收款弹窗开着时扫一发枪 ─────────────────────────────────────────────
// pos-scan.js 的页面级订阅者是 `if (!isMainActive() || modalOpen()) return;` —— 一声不吭。
// 「店员正在办别的事,别偷偷加进车」这个决定没问题;问题是【他不知道这一发没算】。收款弹窗
// 开着正是最后一件货最容易被补扫的时刻:枪响了、灯闪了、屏上什么都没变,那件货就跟着顾客
// 出门了。这与本轮给慢枪补的 onTyped 是同一类病(静默丢掉一发输入),只是换了个入口。
async function scanDuringPayModal(browser, origin) {
    const bag = { asked: [] };
    // 「收款」按钮在手机版收在底部 sheet 里(视口外)。这一例验的是静默不静默,不是那颗
    // 按钮藏在哪 —— 用桌面版视口,购物车面板整个都在屏上。
    const page = await posBoot(browser, origin, bag, DESKTOP);
    await page.keyboard.type(COLA, { delay: 6 });
    await page.keyboard.press('Enter');
    await page.waitForTimeout(700);
    const seeded = await posCart(page);
    await page.click('#cart-pay-btn');
    await page.waitForSelector('#pay-mask.show', { timeout: 10000 });
    // toast 挂 2600ms 才自己收。不等它退场就扫第二发,读到的「เพิ่มแล้ว」是【第一发的】——
    // 这一例头一版就是这么绿的,而那种绿正好复刻了这条 bug 骗人的方式。等到确实空了再开始。
    await page.waitForFunction(
        () => !document.getElementById('pos-toast').classList.contains('show'),
        null,
        { timeout: 6000 }
    );
    const toastClear = await page.evaluate(() =>
        document.getElementById('pos-toast').classList.contains('show')
    );
    bag.asked.length = 0;
    await page.keyboard.type(COLA, { delay: 6 });
    await page.keyboard.press('Enter');
    await page.waitForTimeout(900);
    const after = await page.evaluate(() => ({
        toastShown: document.getElementById('pos-toast').classList.contains('show'),
        toastText: (document.getElementById('pos-toast-txt') || { textContent: '' }).textContent,
        failRows: document.querySelectorAll('#bscan-fails .bscan-fail').length,
        payOpen: document.getElementById('pay-mask').classList.contains('show'),
        qtys: [...document.querySelectorAll('#cart-lines .q[data-qi]')].map((e) => e.textContent),
    }));
    await shot(page, 'w5-scan-during-pay-modal.png');
    await page.close();
    // 不加进车是对的;但「这一发我没算」必须在屏上留下点什么。
    const silent = !after.toastShown && after.failRows === 0;
    return {
        ok: !silent && toastClear === false,
        seededQtys: seeded.qtys,
        toastClearedBeforeScan: toastClear === false,
        askedDuringModal: bag.asked,
        after,
        why: silent
            ? '收款弹窗开着时扫的那一发被静默丢掉:没 toast、没失败条、车没变 —— ' +
              '枪响了灯闪了,店员没有任何办法知道这件货没算进去'
            : '',
    };
}

const CASES = [
    ['w1_cashierSplit', cashierSplit],
    ['w2_batchSplit', batchSplit],
    ['w3_heldKeyOnMain', heldKeyOnMain],
    ['w4_gapTaskSplit', gapTaskSplit],
    ['w5_scanDuringPayModal', scanDuringPayModal],
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
            path.join(SHOTS, 'report-r4-wedge-split.json')
        );
    } finally {
        await browser.close();
        server.close();
    }
    process.exit(failed ? 1 : 0);
})().catch((e) => {
    console.error('R4 WEDGE SPLIT CRASH', e);
    process.exit(2);
});
