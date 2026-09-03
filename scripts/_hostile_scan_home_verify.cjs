/*
 * scripts/_hostile_scan_home_verify.cjs · 对抗素材验收(主站 SPA)
 *
 * 目标不是「再绿一遍」,是找出【还能让它错的输入】。所以每一例喂的都是「两种可能性都沾一点」
 * 的串,而不是干净的枪扫 / 干净的手打:
 *   h1 typedWithBackspace  打一半打错 → 退格改掉 → 接着打完(上一轮五种分段里没有退格这一路;
 *                          退格也发 input 事件,而速度判据是按 input 事件数点的)
 *   h2 heldKeyBarcodeField 建品条码框里【按住一个键不放】—— 真 autoRepeat(Playwright 重复
 *                          keyboard.down 会发 repeat=true 的 keydown),约 30ms 一发:
 *                          速度过、长度过,只有「至少两种不同字符」拦得住,而这条判据
 *                          只在楔子的 MODE_GUN 里,建品条码框是裸声明(MODE_ALWAYS)
 *   h3 heldKeyBatchField   入库批号框里按住一个键不放 —— 同一发输入换个屏
 *   h4 midSpeedDateBox     效期框里按【中速】(120ms/字符)敲日期:比人手 260ms 快、比枪 50ms 慢,
 *                          楔子攒得成一串却判不成枪 —— 店员填的那个日期必须留在框里,
 *                          也不许被当成一发码查出去
 *   h5 onlyNameCreate      扫到未建档 → 去建这个商品 → 只填名字保存,截真 POST body
 *   h6 notInCacheBatch     列表缓存里没有这件货 → 扫码加行 → 批次格 + 真提交载荷
 *
 * 真的东西:home.html + dist/main.js + dist/pre.js 全是本仓真产物;键盘是 page.keyboard 真按键
 * (fill() 绕过 keydown,楔子一个键都收不到)。桩只有 /api/**。文案期望值现场从真 window.I18N 取。
 *
 * 跑法(仓库根目录):node scripts/_hostile_scan_home_verify.cjs [用例名]
 */
const path = require('path');
const { chromium } = require('@playwright/test');
const {
    ROOT,
    DESKTOP,
    GHOST,
    serve,
    gun,
    typeDateByHand,
    shotter,
    runCases,
} = require('./_gun_wedge_lib.cjs');

const ONLY = process.argv[2] || '';
const SHOTS = path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/fix2');
const shot = shotter(SHOTS);

const COLA = '8850999320014';
const MILK = '4901234567894';
const YOG = '8858899000012'; // 只在查码应答里存在 · /api/inventory/stock 里没有它

const P_COLA = { id: 'p-cola', name_th: 'โค้ก 325ml', name_zh: '可乐 325ml', track_batch: false };
const P_MILK = { id: 'p-milk', name_th: 'นมสด 1L', name_zh: '鲜奶 1L', track_batch: true };
const P_YOG = { id: 'p-yog', name_th: 'โยเกิร์ต', name_zh: '酸奶', track_batch: true };
const productName = (product) => [product.name_th, product.name_zh].filter(Boolean).join(' / ');

const LOOKUP = {
    [COLA]: { product: P_COLA, matched_by: 'product', matched_unit: 'ขวด' },
    [MILK]: { product: P_MILK, matched_by: 'product', matched_unit: 'กล่อง' },
    [YOG]: { product: P_YOG, matched_by: 'product', matched_unit: 'ถ้วย' },
};

// 库存列表里【没有】p-yog:模拟刚建完品(save() 后 load() 因 #sx-p-body 不在直接 return)。
const STOCK = [
    {
        product_id: 'p-cola',
        name: { th: 'โค้ก 325ml', en: 'Coke', zh: '可乐 325ml' },
        image_url: null,
        barcode: COLA,
        base_unit: 'ขวด',
        qty_on_hand: 12,
        min_stock: 5,
        avg_cost: 9.5,
        status: 'ok',
        track_batch: false,
        batches: [],
    },
    {
        product_id: 'p-milk',
        name: { th: 'นมสด 1L', en: 'Milk', zh: '鲜奶 1L' },
        image_url: null,
        barcode: MILK,
        base_unit: 'กล่อง',
        qty_on_hand: 6,
        min_stock: 4,
        avg_cost: 28,
        status: 'ok',
        track_batch: true,
        batches: [{ batch_id: 'b1', batch_no: 'L2026', expiry_date: '2026-12-31', qty: 6 }],
    },
];

const INIT = () => localStorage.setItem('mrpilot_token', 'hostile-verify');

async function stubApi(page, bag) {
    await page.route('https://cdnjs.cloudflare.com/**', (r) => r.abort());
    await page.route('**/api/**', async (route) => {
        const req = route.request();
        const url = new URL(req.url());
        if (url.pathname === '/api/sales/products/lookup') {
            const code = url.searchParams.get('barcode');
            bag.asked.push(code);
            const hit = LOOKUP[code];
            if (!hit)
                return route.fulfill({ status: 404, json: { detail: 'sales.product_not_found' } });
            return route.fulfill({ json: hit });
        }
        if (url.pathname === '/api/inventory/in') {
            bag.posted.push(req.postDataJSON());
            return route.fulfill({ json: { ok: true, data: { txn_ids: ['t1'] } } });
        }
        if (url.pathname === '/api/inventory/stock') {
            return route.fulfill({
                json: {
                    ok: true,
                    data: {
                        items: STOCK,
                        summary: { sku_count: 2, stock_value: 282, low_count: 0, out_count: 0 },
                    },
                },
            });
        }
        if (url.pathname === '/api/sales/products') {
            if (req.method() === 'POST') {
                bag.created.push(req.postDataJSON());
                return route.fulfill({ json: { product: { id: 'p-new' } } });
            }
            return route.fulfill({ json: { products: [] } });
        }
        if (url.pathname === '/api/me')
            return route.fulfill({ json: { email: 'h@e2e', role: 'owner', plan: 'pro' } });
        return route.fulfill({ json: { ok: true, data: {}, items: [] } });
    });
}

function newBag() {
    return { asked: [], posted: [], created: [] };
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
    return page;
}

async function waitQuiet(page, fn, timeout = 6000) {
    try {
        await page.waitForFunction(fn, null, { timeout });
    } catch (_) {
        /* 交给断言去报 */
    }
}

/**
 * 真的「按住一个键不放」:Playwright 对同一个 code 重复 down() 会把 keydown 的 repeat 标成
 * true(与系统自动重复一模一样)。keyboard.type() 发的是一串独立按键,拿它冒充按住是自欺。
 *
 * 间隔不靠 waitForTimeout 造:那条路一个来回就 40~60ms,已经掉出 GUN_MAX_GAP_MS(50)的区间,
 * 于是「按住不放」被自己的节拍救了 —— 那种绿是假的。这里背靠背发,并把浏览器里量到的真实
 * 间隔一起带回去当证据。目标节拍取 15ms 而不是 Windows 实测的 33ms:33 离 50 只剩一档,
 * 机器一忙调度抖一下就量到 52,这一例的前提当场不成立(实测栽过一次)。
 */
async function holdKey(page, key, times, targetGapMs) {
    await page.evaluate(() => {
        window.__rep = [];
        window.__repProbe = (e) => window.__rep.push({ r: e.repeat, t: performance.now() });
        document.addEventListener('keydown', window.__repProbe, true);
    });
    // 背靠背发会跑到 1~3ms/发,比真实自动重复还快;给一个目标节拍时按它排(仍然 ≤50ms)。
    const jobs = [];
    for (let i = 0; i < times; i++) {
        jobs.push(
            new Promise((r) => setTimeout(r, i * (targetGapMs || 0))).then(() =>
                page.keyboard.down(key)
            )
        );
    }
    await Promise.all(jobs);
    await page.keyboard.up(key);
    const raw = await page.evaluate(() => {
        document.removeEventListener('keydown', window.__repProbe, true);
        return window.__rep;
    });
    const gaps = raw.slice(1).map((e, i) => Math.round(e.t - raw[i].t));
    return { flags: raw.map((e) => e.r), gaps, maxGap: gaps.length ? Math.max(...gaps) : 0 };
}

async function openBlankProductForm(page) {
    await page.click('#sx-p-add');
    await page.waitForSelector('#sx-pf-barcode', { timeout: 10000 });
    await page.waitForFunction(() => {
        const box = document.querySelector('#sales-prod-mask .modal');
        return !!box && getComputedStyle(box).opacity === '1';
    });
    await page.click('#sx-pf-barcode');
}

async function toProducts(page) {
    await page.evaluate(() => window.routeTo('sales-products'));
    await page.waitForSelector('#sx-p-add', { timeout: 20000 });
}

async function openInModal(page) {
    await page.evaluate(() => {
        document.querySelectorAll('.page').forEach((p) => p.classList.remove('active'));
        document.getElementById('page-inventory').classList.add('active');
        window.loadInventoryPage();
    });
    await page.locator('#inv-tbody tr').first().waitFor({ timeout: 20000 });
    await page.locator('#inv-btn-in').click();
    await page.locator('#inv-in-mask .inv-scan').waitFor({ timeout: 10000 });
}

// ── h1 · 打一半打错 → 退格改掉 → 接着打完 ───────────────────────────────
// 上一轮五种分段全是「只往前打」;退格也发 input 事件,而速度判据(burstChars/burstGap)
// 是按 input 事件点的 —— 删几下再接着打,这条判据点到的数就跟真打进去的位数对不上了。
async function typedWithBackspace(browser, origin) {
    const bag = newBag();
    const page = await boot(browser, bag, origin);
    await toProducts(page);
    await openBlankProductForm(page);
    bag.asked.length = 0;
    const seen = [];
    await page.keyboard.type('8850', { delay: 60 });
    await page.waitForTimeout(400);
    seen.push(await page.inputValue('#sx-pf-barcode'));
    await page.keyboard.type('99993', { delay: 60 }); // 打错两位
    await page.waitForTimeout(400);
    seen.push(await page.inputValue('#sx-pf-barcode'));
    for (let i = 0; i < 2; i++) {
        await page.keyboard.press('Backspace');
        await page.waitForTimeout(200);
    }
    await page.waitForTimeout(400);
    seen.push(await page.inputValue('#sx-pf-barcode'));
    await page.keyboard.type('320014', { delay: 60 });
    await page.waitForTimeout(900);
    seen.push(await page.inputValue('#sx-pf-barcode'));
    const state = await page.evaluate(() => {
        const el = document.getElementById('sx-pf-bc-state');
        return { text: el.textContent.trim(), h: el.getBoundingClientRect().height };
    });
    const wantDup = await page.evaluate(
        (name) => window.I18N[window._currentLang]['sx-p-bc-dup'].replace('{name}', name),
        productName(P_COLA)
    );
    await shot(page, 'h1-typed-with-backspace.png');
    await page.close();
    return {
        ok:
            seen.join('|') === ['8850', '885099993', '8850999', COLA].join('|') &&
            bag.asked[bag.asked.length - 1] === COLA &&
            bag.asked.every((a) => COLA.startsWith(a) || '885099993'.startsWith(a)) &&
            state.h > 0 &&
            state.text.startsWith(wantDup),
        seen,
        want: ['8850', '885099993', '8850999', COLA],
        asked: bag.asked.slice(),
        state,
        wantDup,
    };
}

// ── h2 · 建品条码框里按住一个键不放 ─────────────────────────────────────
// 框里已经有一串手打好的完整码,店员手指压住 '0' 不放:autoRepeat 约 30ms 一发,
// 长度(≥8)和速度(≤50ms)两条判据都过。楔子里拦这一发的是 looksLikeGun 的第三条
// (至少两种不同字符),而它只在 data-enable-barcode="gun" 那档跑;这个框是裸声明。
async function heldKeyBarcodeField(browser, origin) {
    const bag = newBag();
    const page = await boot(browser, bag, origin);
    await toProducts(page);
    await openBlankProductForm(page);
    await page.keyboard.type(COLA, { delay: 60 }); // 人手打完整码
    await page.waitForTimeout(900);
    const before = await page.inputValue('#sx-pf-barcode');
    bag.asked.length = 0;
    // 目标节拍留足余量：这一例的前提是「速度这条线拦不住它，只有 repeat 标志拦得住」，
    // 而 33ms 离 GUN_MAX_GAP_MS（50）太近 —— 机器一忙调度抖一下就量到 52，前提当场不成立
    // （那不是产品的问题，是这一例自己没造出该造的输入）。15ms 仍是真键盘做得到的重复率。
    const held = await holdKey(page, '0', 10, 15);
    await page.waitForTimeout(900);
    const after = await page.inputValue('#sx-pf-barcode');
    const state = await page.evaluate(() =>
        document.getElementById('sx-pf-bc-state').textContent.trim()
    );
    await shot(page, 'h2-held-key-barcode-field.png');
    await page.close();
    return {
        // 按住一个键不放不是扫码:框里那串手打好的码不许被整框换掉
        ok:
            before === COLA &&
            after.startsWith(COLA) &&
            held.flags.slice(1).every(Boolean) &&
            held.maxGap <= 50,
        before,
        after,
        wantPrefix: COLA,
        asked: bag.asked.slice(),
        state,
        held,
    };
}

// ── h3 · 入库批号框里按住一个键不放 ─────────────────────────────────────
async function heldKeyBatchField(browser, origin) {
    const bag = newBag();
    const page = await boot(browser, bag, origin);
    await openInModal(page);
    await gun(page, MILK); // 批次品:批号/效期格露出来
    await waitQuiet(
        page,
        () => document.querySelector('#inv-in-mask-rows [data-k="product_id"]').value === 'p-milk'
    );
    const box = page.locator('#inv-in-mask-rows [data-row]').first().locator('[data-k="batch_no"]');
    await box.click();
    await page.keyboard.type('L2026', { delay: 200 }); // 人手填批号
    await page.waitForTimeout(400);
    const before = await box.inputValue();
    bag.asked.length = 0;
    const held = await holdKey(page, '0', 10, 15); // 同上：留余量，见 h2
    await page.waitForTimeout(900);
    const after = await box.inputValue();
    const msg = await page.locator('#inv-in-mask-scan-msg').innerText();
    await shot(page, 'h3-held-key-batch-field.png');
    await page.close();
    return {
        // 按住一个键不放不是扫码:不许查这个「码」、不许把店员填的批号动掉
        ok:
            before === 'L2026' &&
            after.startsWith('L2026') &&
            bag.asked.length === 0 &&
            held.flags.slice(1).every(Boolean) &&
            held.maxGap <= 50,
        before,
        after,
        asked: bag.asked.slice(),
        msg,
        held,
    };
}

// ── h4 · 效期框里中速敲(120ms/字符)──────────────────────────────────────
// 比人手 260ms 快、比枪 50ms 慢:楔子按 150ms 收尾,这个速度攒得起一整串;而
// machine 判据(框里不是像样日期 = 机器打的)在日期还没敲完时为真 → 速度那道闸被绕开。
async function midSpeedDateBox(browser, origin) {
    const bag = newBag();
    const page = await boot(browser, bag, origin);
    await openInModal(page);
    await gun(page, MILK);
    await waitQuiet(
        page,
        () => document.querySelector('#inv-in-mask-rows [data-k="product_id"]').value === 'p-milk'
    );
    const box = page
        .locator('#inv-in-mask-rows [data-row]')
        .first()
        .locator('[data-k="expiry_date"]');
    await box.click({ position: { x: 8, y: 12 } });
    const focus = await page.evaluate(() => {
        const el = document.activeElement;
        return { k: el && el.dataset ? el.dataset.k : '', type: el ? el.type : '' };
    });
    bag.asked.length = 0;
    // 真人填日期的打法(段内打数字、按 → 换段),只是节拍快到 120ms/字符:比人手典型的 260ms
    // 快、比枪速上限 50ms 慢,楔子攒得成一串却判不成枪。一口气打 8 个数字不是这一例要验的东西
    // ——那样填出来的是什么由浏览器区域设置决定(ISO 那一档年份段会吃掉六位),断的就成了 locale。
    await typeDateByHand(page, '2027-12-31', 120);
    await page.waitForTimeout(900);
    const value = await box.inputValue();
    const msg = await page.locator('#inv-in-mask-scan-msg').innerText();
    await shot(page, 'h4-midspeed-date-box.png');
    await page.close();
    return {
        // 人手敲的日期不是扫码:框里得留着这个日期,也不许当成一发码查出去
        ok:
            focus.k === 'expiry_date' &&
            focus.type === 'date' &&
            value === '2027-12-31' &&
            bag.asked.length === 0,
        focus,
        value,
        asked: bag.asked.slice(),
        msg,
    };
}

// ── h5 · 扫到未建档 → 去建这个商品 → 只填名字保存 ────────────────────────
async function onlyNameCreate(browser, origin) {
    const bag = newBag();
    const page = await boot(browser, bag, origin);
    await toProducts(page);
    // 走产品自己的桥(POS/入库未命中卡点的就是它),不自己造表单
    const opened = await page.evaluate(
        (code) => window.openProductFormWithBarcode(code, { overlay: true }) === true,
        GHOST
    );
    await page.waitForSelector('#sx-pf-barcode', { timeout: 10000 });
    const prefill = await page.inputValue('#sx-pf-barcode');
    await page.click('#sx-pf-th');
    await page.keyboard.type('โยเกิร์ต', { delay: 40 });
    const priceBefore = await page.inputValue('#sx-pf-price');
    await shot(page, 'h5-only-name-create.png');
    await page.click('#sx-p-save');
    await waitQuiet(page, () => !document.getElementById('sx-pf-barcode'), 8000);
    await page.close();
    const body = bag.created[0] || null;
    return {
        ok:
            opened &&
            prefill === GHOST &&
            priceBefore === '' &&
            !!body &&
            body.unit_price === null &&
            body.barcode === GHOST,
        opened,
        prefill,
        priceBefore,
        body,
    };
}

// ── h6 · 列表缓存里没有这件货 → 扫码加行 → 批次格 + 真提交载荷 ────────────
async function notInCacheBatch(browser, origin) {
    const bag = newBag();
    const page = await boot(browser, bag, origin);
    await openInModal(page);
    const inCache = await page.evaluate(
        (id) => !!document.querySelector(`#inv-in-mask-rows option[value="${id}"]`),
        'p-yog'
    );
    await gun(page, YOG);
    await waitQuiet(
        page,
        () => document.querySelector('#inv-in-mask-rows [data-k="product_id"]').value === 'p-yog'
    );
    const shown = await page.evaluate(() => {
        const row = document.querySelector('#inv-in-mask-rows [data-row]');
        const cell = row.querySelector('[data-batchcell]');
        return getComputedStyle(cell).display !== 'none';
    });
    const row = page.locator('#inv-in-mask-rows [data-row]').first();
    if (shown) {
        await row.locator('[data-k="batch_no"]').fill('Y-77');
        await row.locator('[data-k="expiry_date"]').fill('2026-09-30');
    }
    // 切到别的商品再切回来:这一步连查码应答都没有,只有记下来的事实撑得住
    await row.locator('[data-k="product_id"]').selectOption('p-cola');
    await row.locator('[data-k="product_id"]').selectOption('p-yog');
    const shownAgain = await page.evaluate(() => {
        const r = document.querySelector('#inv-in-mask-rows [data-row]');
        return getComputedStyle(r.querySelector('[data-batchcell]')).display !== 'none';
    });
    if (shownAgain) {
        await row.locator('[data-k="batch_no"]').fill('Y-77');
        await row.locator('[data-k="expiry_date"]').fill('2026-09-30');
    }
    await shot(page, 'h6-not-in-cache-batch.png');
    await page.locator('#inv-in-mask-submit').click();
    await waitQuiet(page, () => !document.getElementById('inv-in-mask').classList.contains('show'));
    await page.close();
    const lines = (bag.posted[0] && bag.posted[0].lines) || [];
    const yog = lines.filter((l) => l.product_id === 'p-yog');
    return {
        ok:
            inCache === false &&
            shown &&
            shownAgain &&
            yog.length === 1 &&
            yog[0].batch_no === 'Y-77' &&
            yog[0].expiry_date === '2026-09-30',
        inCache,
        shown,
        shownAgain,
        lines,
    };
}

// ── h7 · 效期框:同一段人手输入,只改打字速度 ────────────────────────────
// 「人手打不出 ≤50ms/字符」这句话是对的,但楔子把「一串」的边界画在 150ms —— 中间那一段
// (50~150ms)既攒得起一串、又不是枪。这一例把速度做成唯一变量,量出病灶从哪一档开始。
async function dateBoxSpeedSweep(browser, origin) {
    const bag = newBag();
    const page = await boot(browser, bag, origin);
    await openInModal(page);
    await gun(page, MILK);
    await waitQuiet(
        page,
        () => document.querySelector('#inv-in-mask-rows [data-k="product_id"]').value === 'p-milk'
    );
    const box = page
        .locator('#inv-in-mask-rows [data-row]')
        .first()
        .locator('[data-k="expiry_date"]');
    // 这台浏览器上 date 控件的段序(value 一律 yyyy-mm-dd,显示序不是)。先量出来再造素材,
    // 不然「人正常会怎么敲」这个前提就是我拍脑袋定的。
    await box.click({ position: { x: 8, y: 12 } });
    await page.keyboard.type('2027', { delay: 300 });
    const firstSeg = await box.inputValue();
    const runs = [];
    // 同一串按键、同一个起点段,只有速度是变量。260ms 是上一轮验过的那一档,当对照组。
    for (const [label, keys, delay] of [
        ['plain-8-at-260ms(上一轮验的那一档)', '20271231', 260],
        ['plain-8-at-180ms', '20271231', 180],
        ['plain-8-at-140ms', '20271231', 140],
        ['plain-8-at-120ms', '20271231', 120],
        ['plain-8-at-100ms', '20271231', 100],
        ['with-slash-at-120ms', '2027/12/31', 120],
    ]) {
        // 点最左边那一段:date 控件按点到哪一段决定从哪起,点中间就成了先填别的段。
        await box.click({ position: { x: 8, y: 12 } });
        await page.evaluate(() => {
            document.querySelector('#inv-in-mask-rows [data-k="expiry_date"]').value = '';
        });
        bag.asked.length = 0;
        await page.keyboard.type(keys, { delay });
        await page.waitForTimeout(700);
        runs.push({
            label,
            keys,
            delay,
            value: await box.inputValue(),
            asked: bag.asked.slice(),
            phantomScan: bag.asked.length > 0,
        });
    }
    await shot(page, 'h7-date-box-speed-sweep.png');
    await page.close();
    // 人手敲日期:任何速度都不该被当成扫了一件货,框里也不该被清空
    return {
        ok: runs.every((r) => !r.phantomScan),
        firstSeg,
        runs,
    };
}

// ── h8 · 三段不等分 / 前导零碎片 ─────────────────────────────────────────
// 上一轮五种分段都是两段(外加一次官方三段)。这里换成不等长三段,并且专挑「后一段以 0
// 开头」——那种碎片单看像个合法短码,存下去后台一切正常,只有收银台扫不出这件货。
async function unevenSplits(browser, origin) {
    const bag = newBag();
    const page = await boot(browser, bag, origin);
    await toProducts(page);
    const runs = [];
    for (const segs of [
        ['885', '09993', '20014'],
        ['88509993', '2', '0014'],
        ['8850999320', '0', '14'],
    ]) {
        await openBlankProductForm(page);
        bag.asked.length = 0;
        const seen = [];
        for (const seg of segs) {
            await page.keyboard.type(seg, { delay: 60 });
            await page.waitForTimeout(400);
            seen.push(await page.inputValue('#sx-pf-barcode'));
        }
        await page.waitForTimeout(900);
        const value = await page.inputValue('#sx-pf-barcode');
        const grew = segs.map((_, i) => segs.slice(0, i + 1).join(''));
        runs.push({
            split: segs.join('/'),
            seen,
            want: grew,
            value,
            asked: bag.asked.slice(),
            ok:
                seen.join('|') === grew.join('|') &&
                value === COLA &&
                bag.asked[bag.asked.length - 1] === COLA,
        });
        await page.click('#sx-p-cancel');
    }
    await shot(page, 'h8-uneven-splits.png');
    await page.close();
    return { ok: runs.every((r) => r.ok), runs };
}

// ── h9 · 真枪扫进效期框(claimed fix 的正面)────────────────────────────
// 反证只证「人手打的没被吞」还不够 —— 修过头就是枪扫也不认了,那条 P1-⑧ 等于没修。
async function realGunIntoDateBox(browser, origin) {
    const bag = newBag();
    const page = await boot(browser, bag, origin);
    await openInModal(page);
    await gun(page, MILK);
    await waitQuiet(
        page,
        () => document.querySelector('#inv-in-mask-rows [data-k="product_id"]').value === 'p-milk'
    );
    const box = page
        .locator('#inv-in-mask-rows [data-row]')
        .first()
        .locator('[data-k="expiry_date"]');
    await box.click({ position: { x: 8, y: 12 } });
    await box.evaluate((el) => (el.value = '2026-12-31')); // 店员已经填好的效期
    bag.asked.length = 0;
    await gun(page, COLA, 5); // 枪速 5ms/字符
    await page.waitForTimeout(900);
    const value = await box.inputValue();
    const rows = await page.evaluate(() =>
        [...document.querySelectorAll('#inv-in-mask-rows [data-row]')].map(
            (r) => r.querySelector('[data-k="product_id"]').value
        )
    );
    await shot(page, 'h9-real-gun-into-date-box.png');
    await page.close();
    return {
        // 枪扫要被处理成一件货(加行),而店员填好的效期原样还回去,不许剩下 49012-03-31
        ok: value === '2026-12-31' && bag.asked.includes(COLA) && rows.includes('p-cola'),
        value,
        asked: bag.asked.slice(),
        rows,
    };
}

const CASES = [
    ['h1_typedWithBackspace', typedWithBackspace],
    ['h2_heldKeyBarcodeField', heldKeyBarcodeField],
    ['h3_heldKeyBatchField', heldKeyBatchField],
    ['h4_midSpeedDateBox', midSpeedDateBox],
    ['h5_onlyNameCreate', onlyNameCreate],
    ['h6_notInCacheBatch', notInCacheBatch],
    ['h7_dateBoxSpeedSweep', dateBoxSpeedSweep],
    ['h8_unevenSplits', unevenSplits],
    ['h9_realGunIntoDateBox', realGunIntoDateBox],
];

(async () => {
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch();
    const failed = await runCases(
        CASES.filter(([name]) => !ONLY || name.indexOf(ONLY) >= 0),
        (fn) => fn(browser, origin),
        path.join(SHOTS, 'report-hostile-home.json')
    );
    await browser.close();
    server.close();
    process.exit(failed ? 1 : 0);
})().catch((e) => {
    console.error('HOSTILE HOME CRASH', e);
    process.exit(2);
});
