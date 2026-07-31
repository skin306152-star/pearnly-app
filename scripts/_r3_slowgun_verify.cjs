/*
 * scripts/_r3_slowgun_verify.cjs · 慢枪(蓝牙 HID / 带 transmit delay 的有线枪)扫进建品条码框
 *
 * 真机上这类枪常年跑在 50~100ms/字符,正落在两条判据中间:楔子 MAX_GAP_MS=150 攒得成一串,
 * GUN_MAX_GAP_MS=50 又判它不是枪速。引擎在这一档上是【故意】偏向人手的 —— 这一段与店员填
 * 批号/效期的节拍是叠着的,没有哪个阈值分得开(见 static/scan/scan-wedge.js)。
 *
 * 所以这份验收不再断「慢枪必须替换整框」(那是引擎明确否掉的语义),断的是引擎承诺的那份
 * 代价:判成人打字的那一发【不许静默】。三件事各断各的 ——
 *   ① 屏上得有话说,且不能是绿字「没人用这个码」;
 *   ② 查重不许对「旧码 + 这一串」拼出来的东西回可用 —— 那串东西根本不是任何一个码;
 *   ③ 得给一条一点就补回来的出路(入库侧已有:data-scan-typed「当条码用」)。
 * 判错一半不是问题,问题是判错之后店员既看不见也补不回来。
 *
 * 跑法(仓库根目录):node scripts/_r3_slowgun_verify.cjs [用例名]
 */
const path = require('path');
const { chromium } = require('@playwright/test');
const {
    ROOT,
    DESKTOP,
    serve,
    cdpGun,
    armTwoRulers,
    readTwoRulers,
    shotter,
    runCases,
} = require('./_gun_wedge_lib.cjs');

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

// 真按键 + 实测每个字符【产生】的间隔(楔子量的就是这把尺子;墙钟量出来的是页面忙不忙)。
// 走 CDP 发了就走:page.keyboard.type 会 await 每一发,页面一忙节拍就跟着被拖慢,量出来的
// 「慢枪」有一半是 harness 自己造的。
async function gunMeasured(page, text, delayMs) {
    const cdp = await page.context().newCDPSession(page);
    await armTwoRulers(page);
    await cdpGun(cdp, text, delayMs, 'Enter');
    return readTwoRulers(page);
}

// 屏上这一刻到底在说什么。绿字(.sx-bc-ok)= 查重放行了框里那串东西 —— 慢枪拼接之后
// 出现绿字是最坏的一档:店员看到的是「这个码可以用」,而那串东西根本不是任何一个码。
async function stateOf(page) {
    return page.evaluate(() => {
        const el = document.getElementById('sx-pf-bc-state');
        const box = el ? el.getBoundingClientRect() : { height: 0 };
        return {
            text: el ? el.textContent.trim() : '',
            html: el ? el.innerHTML : '',
            blessed: !!(el && el.querySelector('.sx-bc-ok')),
            visible: !!el && box.height > 0,
            hasWayBack: !!(el && el.querySelector('[data-scan-typed]')),
        };
    });
}

// ── r1 · 框里已有旧码,慢枪扫新码进来 ──────────────────────────────────
// 引擎会把这一发判成人打字(故意的)。那这一发去哪了、店员怎么补回来,必须看得见。
async function slowGunIntoDirtyFieldIsNotSilent(browser, origin) {
    const bag = { asked: [], created: [] };
    const page = await boot(browser, bag, origin);
    await openFormWith(page, OLD);
    const before = await page.inputValue('#sx-pf-barcode');
    const m = await gunMeasured(page, NEW, SLOW);
    await page.waitForTimeout(1200); // 让 150ms 收尾 + 400ms 防抖都跑完
    const after = await page.inputValue('#sx-pf-barcode');
    const state = await stateOf(page);
    await shot(page, 'r1-slow-gun-dirty-field.png');

    // 走那条回路:店员说「这一串确实是扫的」→ 框还原成扫之前的样子再整框按条码走
    let recovered = '';
    bag.asked.length = 0;
    if (state.hasWayBack) {
        await page.click('#sx-pf-bc-state [data-scan-typed]');
        await page.waitForTimeout(900);
        recovered = await page.inputValue('#sx-pf-barcode');
    }

    const stitched = after !== NEW && after !== before; // 新旧接成了一串
    const inGunBand = m.stampMax > 50 && m.stampMax < 150; // 前提:节拍真落在那个洞里
    const ok =
        inGunBand &&
        stitched && // 前提:这一发确实把框写脏了,不然验的是空档
        state.visible &&
        !state.blessed && // 拼出来的东西不许被查重放行
        state.hasWayBack && // 判错了要有一条一点就补回来的路
        recovered === NEW &&
        bag.asked.includes(NEW); // 补回来之后系统真按这个码去查了(不是只把框改好看)
    return {
        ok,
        before,
        after,
        recovered,
        stitched,
        inGunBand,
        measured: m,
        state,
        askedAfterRecovery: bag.asked,
        why: ok
            ? ''
            : !inGunBand || !stitched
              ? `没造出「慢枪把框写脏」这个前提:节拍 ${m.stampMax}ms · 框里 ${after}`
              : state.blessed
                ? `框里成了「旧码+这一串」= ${after},而屏上回的是绿字「${state.text}」—— ` +
                  `店员照这句话点保存,落库的条码 POS 永远扫不出来`
                : !state.hasWayBack
                  ? `这一发被判成人打字,屏上却没给回路(data-scan-typed):框里剩 ${after}`
                  : `回路点了没补回来:框里 ${recovered},查的是 ${bag.asked.join(',')}`,
    };
}

// ── r2 · 同一发慢枪打进空框(对照:框里本来是空的,字符留下来就等于码本身)──
async function slowGunIntoEmptyField(browser, origin) {
    const bag = { asked: [], created: [] };
    const page = await boot(browser, bag, origin);
    await page.click('#sx-p-add');
    await page.waitForSelector('#sx-pf-barcode', { timeout: 10000 });
    await page.click('#sx-pf-barcode');
    const m = await gunMeasured(page, NEW, SLOW);
    await page.waitForTimeout(1200);
    const after = await page.inputValue('#sx-pf-barcode');
    return { ok: after === NEW, after, wanted: NEW, measured: m };
}

// ── r3 · 快枪(8ms)扫进已有码的框(对照:枪速这一档判得准,整框换掉)──
async function fastGunReplacesDirtyField(browser, origin) {
    const bag = { asked: [], created: [] };
    const page = await boot(browser, bag, origin);
    await openFormWith(page, OLD);
    const m = await gunMeasured(page, NEW, 8);
    await page.waitForTimeout(1200);
    const after = await page.inputValue('#sx-pf-barcode');
    return { ok: after === NEW, after, wanted: NEW, measured: m };
}

// ── r4 · 节拍扫描:引擎【认下了这一串】的每一档都不许出现「拼接串被查重放行」──
// 只断这一条,不断「必须替换」:后者是引擎明确否掉的语义,断它等于把一条设计决定当成 bug。
// 判定只在 50 < 实测节拍 ≤ MAX_GAP_MS(150) 这一段:
//   ≤50   楔子判它是枪,整框换掉 —— 不在这一例的射程里;
//   >150  楔子连一串都攒不起来(每个字符各自成串、长度不够被丢),这一发跟人手一个个敲
//         完全同形,没有任何信息能把两者分开 —— 要求引擎在这里出声等于要求它猜。
// 这条边界是引擎自己的承诺范围,写死在这里,免得下次有人拿 200ms 的输入来判它有病。
async function sweepNeverBlessesAStitchedCode(browser, origin) {
    const bag = { asked: [], created: [] };
    const page = await boot(browser, bag, origin);
    const rows = [];
    for (const d of [30, 45, 55, 70, 90, 110, 140]) {
        await openFormWith(page, OLD);
        const m = await gunMeasured(page, NEW, d);
        await page.waitForTimeout(900);
        const after = await page.inputValue('#sx-pf-barcode');
        const state = await stateOf(page);
        rows.push({
            delay: d,
            stampMax: m.stampMax,
            value: after,
            replaced: after === NEW,
            stitched: after !== NEW && after !== OLD,
            blessed: state.blessed,
            stateText: state.text,
        });
        await page.evaluate(() => document.getElementById('sx-p-cancel')?.click());
        await page.waitForTimeout(300);
    }
    await shot(page, 'r4-slow-gun-sweep.png');
    const inBand = rows.filter((r) => r.stampMax > 50 && r.stampMax <= 150);
    const blessed = inBand.filter((r) => r.stitched && r.blessed);
    return {
        // 带内一档都没扫到 = 这次跑的节拍全落在两头,这一例什么都没验 —— 那也算红
        ok: inBand.length >= 3 && blessed.length === 0,
        rows,
        inBandCount: inBand.length,
        blessed,
        why: !inBand.length
            ? '实测节拍没有一档落进 50~150,这一例没验到东西'
            : blessed.length
              ? `${blessed.length} 档节拍下框里是拼接串、屏上却回绿字 —— 这串东西会被当成条码存下去`
              : '',
    };
}

const CASES = [
    ['slowGunIntoDirtyFieldIsNotSilent', slowGunIntoDirtyFieldIsNotSilent],
    ['slowGunIntoEmptyField', slowGunIntoEmptyField],
    ['fastGunReplacesDirtyField', fastGunReplacesDirtyField],
    ['sweepNeverBlessesAStitchedCode', sweepNeverBlessesAStitchedCode],
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
