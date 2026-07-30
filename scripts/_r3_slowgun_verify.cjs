/*
 * scripts/_r3_slowgun_verify.cjs · 第三轮对抗 · 慢枪(带 intercharacter delay / 蓝牙 HID)
 *
 * 前两轮的枪一律 ≤8ms/字符。真机上蓝牙 HID 枪与带 transmit delay 设置的有线枪常年跑在
 * 50~100ms/字符 —— 那正好落在两条判据中间的洞里:
 *   楔子 MAX_GAP_MS = 150 → 攒得成一串,回调照发
 *   建品侧 GUN_MAX_GAP_MS = 50 → burstIsGunSpeed() 判它是「人在打字」→ applyCode 直接 return
 * 于是这一发既不被当成打字丢掉,也不被当成扫码消费掉:字符原样留在框里,跟框里已有的码接成
 * 一条新串,查重按接出来的那条串问,回绿字「没人用这个码」。
 *
 * 跑法(仓库根目录):node scripts/_r3_slowgun_verify.cjs [用例名]
 */
const path = require('path');
const { chromium } = require('@playwright/test');
const { ROOT, DESKTOP, serve, shotter, runCases } = require('./_gun_wedge_lib.cjs');

const ONLY = process.argv[2] || '';
const SHOTS = path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/round3');
const shot = shotter(SHOTS);

const OLD = '8850999320014'; // 商品资料里已经有的码
const NEW = '8851234567895'; // 要用扫码换上去的新码
const SLOW = 70; // 蓝牙枪常见节拍:> GUN_MAX_GAP_MS(50),< MAX_GAP_MS(150)

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
    await page.waitForFunction(() => typeof window.routeTo === 'function', null, { timeout: 25000 });
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

// 表单由产品自己的桥打开并预填码 —— 与「别处扫到未建档 → 去建这个商品」同一条路。
async function openFormWith(page, code) {
    await page.evaluate((c) => window.openProductFormWithBarcode(c, { overlay: true }), code);
    await page.waitForSelector('#sx-pf-barcode', { timeout: 10000 });
    await page.waitForFunction(() => {
        const box = document.querySelector('#sales-prod-mask .modal');
        return !!box && getComputedStyle(box).opacity === '1';
    });
    await page.click('#sx-pf-barcode');
    await page.keyboard.press('End'); // 光标落到已有码的末尾(枪不会替你选中全文)
}

// 真按键 + 实测每个字符的落点间隔(不靠 delay 参数自称)。
async function typeMeasured(page, text, delayMs) {
    await page.evaluate(() => {
        window.__ks = [];
        window.__kp = () => window.__ks.push(performance.now());
        document.addEventListener('keydown', window.__kp, true);
    });
    await page.keyboard.type(text, { delay: delayMs });
    const raw = await page.evaluate(() => {
        document.removeEventListener('keydown', window.__kp, true);
        return window.__ks;
    });
    const gaps = raw.slice(1).map((t, i) => Math.round(t - raw[i]));
    return { gaps, maxGap: gaps.length ? Math.max(...gaps) : 0, minGap: Math.min(...gaps) };
}

// ── r1 · 框里已有旧码,用慢枪扫新码替换 ────────────────────────────────
async function slowGunReplacesDirtyField(browser, origin) {
    const bag = { asked: [], created: [] };
    const page = await boot(browser, bag, origin);
    await openFormWith(page, OLD);
    const before = await page.inputValue('#sx-pf-barcode');
    const timing = await typeMeasured(page, NEW, SLOW);
    await page.keyboard.press('Enter'); // 枪的后缀
    await page.waitForTimeout(1200); // 让 150ms 收尾 + 400ms 防抖都跑完
    const after = await page.inputValue('#sx-pf-barcode');
    const state = await page.evaluate(() => {
        const el = document.getElementById('sx-pf-bc-state');
        return { text: el.textContent.trim(), cls: el.className };
    });
    await shot(page, 'r1-slow-gun-dirty-field.png');
    // 保存,截真发出去的 body:落库的到底是哪一串
    await page.evaluate(() => {
        const n = document.getElementById('sx-pf-name-th');
        if (n) n.value = 'ทดสอบ';
    });
    await page.click('#sx-p-save');
    await page.waitForTimeout(800);
    const posted = bag.created[bag.created.length - 1] || null;
    const ok = after === NEW;
    return {
        ok,
        before,
        after,
        wanted: NEW,
        measuredGaps: timing.gaps,
        maxGap: timing.maxGap,
        state,
        postedBarcode: posted ? posted.barcode : null,
        asked: bag.asked,
        why: ok ? '' : `慢枪(${timing.maxGap}ms/字符)扫进已有码的框:框里成了新旧相接的一串`,
    };
}

// ── r2 · 同一发慢枪打进空框(对照:这一档没病,证明病灶只在「框里已有内容」)──
async function slowGunIntoEmptyField(browser, origin) {
    const bag = { asked: [], created: [] };
    const page = await boot(browser, bag, origin);
    await page.click('#sx-p-add');
    await page.waitForSelector('#sx-pf-barcode', { timeout: 10000 });
    await page.click('#sx-pf-barcode');
    const timing = await typeMeasured(page, NEW, SLOW);
    await page.keyboard.press('Enter');
    await page.waitForTimeout(1200);
    const after = await page.inputValue('#sx-pf-barcode');
    return { ok: after === NEW, after, wanted: NEW, maxGap: timing.maxGap };
}

// ── r3 · 快枪(8ms)扫进已有码的框(对照:快枪这一档是好的)──
async function fastGunReplacesDirtyField(browser, origin) {
    const bag = { asked: [], created: [] };
    const page = await boot(browser, bag, origin);
    await openFormWith(page, OLD);
    const timing = await typeMeasured(page, NEW, 8);
    await page.keyboard.press('Enter');
    await page.waitForTimeout(1200);
    const after = await page.inputValue('#sx-pf-barcode');
    return { ok: after === NEW, after, wanted: NEW, maxGap: timing.maxGap };
}

// ── r4 · 慢枪节拍扫描(50~150 这一段每 10ms 一档,划出洞的边界)──
async function slowGunSweep(browser, origin) {
    const bag = { asked: [], created: [] };
    const page = await boot(browser, bag, origin);
    const rows = [];
    for (const d of [30, 45, 55, 70, 90, 110, 140]) {
        await openFormWith(page, OLD);
        const timing = await typeMeasured(page, NEW, d);
        await page.keyboard.press('Enter');
        await page.waitForTimeout(900);
        const after = await page.inputValue('#sx-pf-barcode');
        rows.push({ delay: d, measuredMax: timing.maxGap, value: after, replaced: after === NEW });
        await page.evaluate(() => document.getElementById('sx-p-cancel')?.click());
        await page.waitForTimeout(300);
    }
    await shot(page, 'r4-slow-gun-sweep.png');
    // 「至少有一档慢枪没替换成功」= 洞真的存在
    const broken = rows.filter((r) => !r.replaced);
    return { ok: broken.length === 0, rows, broken };
}

const CASES = [
    ['slowGunReplacesDirtyField', slowGunReplacesDirtyField],
    ['slowGunIntoEmptyField', slowGunIntoEmptyField],
    ['fastGunReplacesDirtyField', fastGunReplacesDirtyField],
    ['slowGunSweep', slowGunSweep],
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
            async (fn) => {
                const r = await fn(browser, origin);
                return r;
            },
            path.join(SHOTS, 'report-r3-slowgun.json')
        );
    } finally {
        await browser.close();
        server.close();
    }
    process.exit(failed ? 1 : 0);
})();
