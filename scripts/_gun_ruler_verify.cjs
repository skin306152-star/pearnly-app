/*
 * scripts/_gun_ruler_verify.cjs · 「枪 vs 人」这把尺子的真浏览器取证
 *
 * 单测里的按键是造出来的:时刻由脚本填,日期控件由桩模拟。那能验判据的逻辑,验不了判据
 * 依赖的两条【浏览器事实】—— 而前三轮栽的正是这两条:
 *   ① 主线程被长任务堵住时,KeyboardEvent.timeStamp 到底跟不跟着一起晚?(尺子的地基)
 *   ② <input type=date> 吃了一串数字之后 value 长什么样?(上一版拿它当第二判据的地基)
 * 所以这个脚本只做一件事:在真 Chromium + 真产品 DOM 上把这两条量出来,顺带把五档对抗
 * 输入在真界面上跑一遍。数字进报告,报告进 tests/e2e/_artifacts/pos_barcode_scan/ruler/。
 *
 * 靶子全是产品自己的框(入库弹窗的数量/批号/效期 + 建品表单的条码框),不是脚本现造的
 * 元素 —— 造一个产品不使用的元素来验自己,本仓吃过这个亏。
 *
 * 跑法(仓库根目录):node scripts/_gun_ruler_verify.cjs [用例名]
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

const ONLY = process.argv[2] || '';
const SHOTS = path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/ruler');
const shot = shotter(SHOTS);

const COLA = '8850999320014'; // 非批次品
const MILK = '4901234567894'; // 批次品 · 扫它才有批号/效期格
const NEW_CODE = '8851234567895'; // 要用扫码换上去的新码
const LOT = 'LOT-B240301'; // 店员手写的批号
const EXPIRY = '2027-12-31';

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

const INIT = () => localStorage.setItem('mrpilot_token', 'ruler-verify');

async function stubApi(page, bag) {
    await page.route('https://cdnjs.cloudflare.com/**', (r) => r.abort());
    await page.route('**/api/**', async (route) => {
        const req = route.request();
        const url = new URL(req.url());
        if (url.pathname === '/api/sales/products/lookup') {
            const code = url.searchParams.get('barcode');
            bag.asked.push(code);
            const hit = LOOKUP[code];
            if (!hit) return route.fulfill({ status: 404, json: { detail: 'not_found' } });
            return route.fulfill({ json: hit });
        }
        if (url.pathname === '/api/sales/products') {
            if (req.method() === 'POST') {
                bag.created.push(req.postDataJSON());
                return route.fulfill({ json: { product: { id: 'p-new' } } });
            }
            return route.fulfill({ json: { products: [] } });
        }
        if (url.pathname === '/api/inventory/stock') return route.fulfill({ json: STOCK });
        if (url.pathname === '/api/me')
            return route.fulfill({ json: { email: 'ruler@e2e', role: 'owner', plan: 'pro' } });
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
    return page;
}

// 入库弹窗:真点真按钮开,再扫一发批次品把批号/效期格逼出来。
async function openReceiveWithBatchRow(page) {
    await page.evaluate(() => {
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
}

// 建品表单:走产品自己的桥打开并预填码(与「别处扫到未建档 → 去建这个商品」同一条路)。
async function openProductFormWith(page, code) {
    await page.evaluate(() => window.routeTo('sales-products'));
    await page.waitForSelector('#sx-p-add', { timeout: 20000 });
    await page.evaluate((c) => window.openProductFormWithBarcode(c, { overlay: true }), code);
    await page.waitForSelector('#sx-pf-barcode', { timeout: 10000 });
    await page.click('#sx-pf-barcode');
    await page.keyboard.press('End'); // 光标落到已有码的末尾(枪不会替你选中全文)
}

// 真枪的两条硬要求(CDP 发了就走 + 两把尺子同时量)已抽进 _gun_wedge_lib.cjs:量错尺子
// 是本仓栽过三轮的那件事,harness 也只该有一份,不然改准了一处别处照旧量墙钟。
async function armRuler(page, blockAtNth, blockMs) {
    await armTwoRulers(page);
    if (blockAtNth) await armLongTask(page, blockAtNth, blockMs);
}

const readRuler = readTwoRulers;

// ── ruler · 前提①:长任务下两把尺子分道扬镳 ────────────────────────────
async function ruler(browser, origin) {
    const bag = { asked: [], created: [] };
    const page = await boot(browser, bag, origin);
    await openReceiveWithBatchRow(page);
    const batch = page.locator('#inv-in-mask-rows [data-row] [data-k="batch_no"]').first();
    await batch.click();
    await page.keyboard.type(LOT, { delay: 120 }); // 店员先手写批号
    // 手写完到举起枪之间必须留够 MAX_GAP_MS,不然两段会被当成同一串 —— 那串里带着人手的
    // 120ms 间隔,整串照人手判(店员真这么快也是同样结果,而且看得见:字符留在框里)。
    // 这一条是引擎的语义,不是这一例要验的东西,所以在这儿等掉。
    await page.waitForTimeout(400);
    bag.asked.length = 0;

    const cdp = await page.context().newCDPSession(page);
    await armRuler(page, 5, 120); // 第 5 个字符处堵 120ms
    await cdpGun(cdp, COLA, 8, 'Enter');
    const m = await readRuler(page);
    await page.waitForTimeout(900);
    const batchValue = await batch.inputValue();
    await shot(page, 'ruler-long-task.png');

    const ok = m.perfMax > 100 && m.stampMax < 30 && bag.asked.includes(COLA) && batchValue === LOT;
    return {
        ok,
        measured: m,
        batchValue,
        wantedBatch: LOT,
        asked: bag.asked,
        why: ok
            ? ''
            : `长任务下:处理时刻最大间隔 ${m.perfMax}ms,产生时刻最大间隔 ${m.stampMax}ms · ` +
              `批号成了 ${batchValue}`,
    };
}

// ── dateResidue · 前提②:日期控件吃了数字之后 value 长什么样 ──────────
// 上一版拿「残渣像不像 yyyy-mm-dd」当第二判据。这一例把人打的和机器打的残渣并排量出来:
// 只要两边互相穿帮,这条判据就是反的 —— 它已经被删掉,这里留着防有人再装回去。
async function dateResidue(browser, origin) {
    const bag = { asked: [], created: [] };
    const page = await boot(browser, bag, origin);
    await openReceiveWithBatchRow(page);
    const exp = page.locator('#inv-in-mask-rows [data-row] [data-k="expiry_date"]').first();
    const ISO = /^\d{4}-\d{2}-\d{2}$/;

    const probe = async (text, delay, seed) => {
        await exp.evaluate((el, v) => {
            el.value = v;
            el.blur();
        }, seed);
        await exp.click();
        await page.keyboard.type(text, { delay });
        await page.waitForTimeout(400);
        return exp.inputValue();
    };

    const human = await probe('20271231', 120, '');
    // 慢串(> 枪速上限)楔子不插手,框里留下的就是【原始残渣】—— 机器打的那一半只能这么量:
    // 快枪那两档会被楔子当场还原,量到的是还原后的值,证明不了残渣长什么样。
    const machineEmpty = await probe(MILK, 70, '');
    const machineFilled = await probe(MILK, 70, EXPIRY);
    await shot(page, 'date-residue.png');

    // 一个方向反了这条判据就不成立,不必等两个都反:人打的留下非 ISO 残渣 → 「不像日期就是
    // 机器打的」当场把店员填的效期判成扫码,整框抹掉再发一次查码。这一半是稳定复现的。
    // (另一半 —— 机器残渣看着像合法日期 —— 取决于光标停在哪一段,这条产品路径上复现不了,
    //  所以不拿它当判定,只把量到的值记进报告。)
    const humanLooksMachine = human !== '' && !ISO.test(human);
    const machineLooksHuman = machineEmpty === '' || ISO.test(machineFilled);
    return {
        ok: humanLooksMachine,
        humanTyped: { text: '20271231', gapMs: 120, residue: human },
        machineIntoEmpty: { text: MILK, gapMs: 70, residue: machineEmpty },
        machineIntoFilled: { text: MILK, gapMs: 70, seed: EXPIRY, residue: machineFilled },
        humanLooksMachine,
        machineLooksHuman,
        why: humanLooksMachine
            ? '残渣判据被实测推翻(所以引擎里没有它)'
            : `人手 120ms 打出来的残渣是 ${human || '(空)'} · 这一轮没量出穿帮,` +
              '别据此把残渣判据装回去,先看清楚是不是探针失效',
    };
}

// ── gunIntoFilledExpiry · 反证 5:防修过头 ──────────────────────────────
async function gunIntoFilledExpiry(browser, origin) {
    const bag = { asked: [], created: [] };
    const page = await boot(browser, bag, origin);
    await openReceiveWithBatchRow(page);
    const row = page.locator('#inv-in-mask-rows [data-row]').first();
    const exp = row.locator('[data-k="expiry_date"]');
    await exp.evaluate((el, v) => (el.value = v), EXPIRY);
    await exp.click();
    bag.asked.length = 0;

    await page.keyboard.type(COLA, { delay: 5 });
    await page.keyboard.press('Enter');
    await page.waitForTimeout(900);
    const after = await exp.inputValue();
    const rows = await page.locator('#inv-in-mask-rows [data-row]').count();
    await shot(page, 'gun-into-filled-expiry.png');

    const ok = after === EXPIRY && bag.asked.includes(COLA);
    return {
        ok,
        expiryAfter: after,
        wanted: EXPIRY,
        asked: bag.asked,
        rows,
        why: ok ? '' : `枪扫进已填好的效期框:效期成了 ${after || '(空)'}`,
    };
}

// ── humanTypesExpiry · 反证 4:人手中速填日期 ────────────────────────────
async function humanTypesExpiry(browser, origin) {
    const bag = { asked: [], created: [] };
    const page = await boot(browser, bag, origin);
    await openReceiveWithBatchRow(page);
    const exp = page.locator('#inv-in-mask-rows [data-row] [data-k="expiry_date"]').first();
    const rows = [];
    for (const delay of [100, 120, 140, 180, 260]) {
        await exp.evaluate((el) => {
            el.value = '';
            el.blur();
        });
        await exp.click();
        bag.asked.length = 0;
        await armRuler(page, 0, 0);
        await page.keyboard.type('20271231', { delay });
        const m = await readRuler(page);
        await page.keyboard.press('Tab');
        await page.waitForTimeout(700);
        rows.push({
            delay,
            measuredMax: m.stampMax,
            value: await exp.inputValue(),
            asked: bag.asked.slice(),
            stolen: bag.asked.length > 0,
        });
    }
    await shot(page, 'human-types-expiry.png');
    const broken = rows.filter((r) => r.stolen);
    return {
        ok: broken.length === 0,
        rows,
        broken,
        why: broken.length ? '人手填的效期被当成扫码抢走并发了查码' : '',
    };
}

// ── heldKey · 反证 3:按住一个键不放 ────────────────────────────────────
async function heldKey(browser, origin) {
    const bag = { asked: [], created: [] };
    const page = await boot(browser, bag, origin);
    await openProductFormWith(page, COLA);
    bag.asked.length = 0;
    await armRuler(page, 0, 0);
    // 同一个键连按 = Chromium 给后续几发打上 autoRepeat(与真键盘按住不放同一条码路)。
    // 两处都是刻意的:
    //  · 节拍压到 25ms,把这一串逼进枪速区间(实测落 28~33ms)—— 速度这条判据在这档完全
    //    失效。放到 45ms 上去这一例会「因为慢所以过」,是假绿。
    //  · 末尾补两个不同的数字。整串全是 0 的话,拦住它的是「至少两种字符」那条兜底,
    //    repeat 一点力都没出 —— 把 repeat 判据删掉这一例照样绿(实测过)。补上之后,
    //    长度/速度/字符种类三条全过,只剩 repeat 这个物理事实答得了。
    const cdp = await page.context().newCDPSession(page);
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
    const m = await readRuler(page);
    await page.waitForTimeout(900);
    const value = await page.inputValue('#sx-pf-barcode');
    const state = await page.evaluate(() => {
        const el = document.getElementById('sx-pf-bc-state');
        return { text: el.textContent.trim(), cls: el.className };
    });
    await shot(page, 'held-key.png');

    const typed = value.slice(COLA.length);
    const inGunBand = m.stampMax <= 50;
    // 三条前提缺一条,这一绿就不是 repeat 挣来的
    const onlyRepeatCanBlock =
        inGunBand && typed.length >= 8 && new Set(typed).size >= 2 && m.repeats >= 10;
    const ok = value.startsWith(COLA) && onlyRepeatCanBlock;
    return {
        ok,
        keys: m.n,
        repeatFlags: m.repeats,
        gaps: m.stampGaps,
        inGunBand,
        typedRun: typed,
        distinctChars: new Set(typed).size,
        onlyRepeatCanBlock,
        value,
        state,
        asked: bag.asked,
        // 楔子没插手(框里的字是浏览器落进去的,店员看得见)。但那一串又被条码框自己的
        // 防抖查了一次码 —— 那是建品侧的事,记在这儿给下游看,别当成这一例过了就没事。
        downstream: bag.asked.filter((c) => c !== COLA),
        why: ok
            ? ''
            : onlyRepeatCanBlock
              ? `按住一个键不放:框里成了 ${value}(原码 ${COLA})`
              : `这一轮没把局面逼到「只剩 repeat 拦得住」(间隔 ${m.stampMax}ms · ` +
                `${new Set(typed).size} 种字符 · ${m.repeats} 发带 repeat)· 过了也不算数`,
    };
}

// ── slowBurstSweep · 反证 1:慢串 55~149ms 六档 ──────────────────────────
// 结论是明确选的:落在框里的慢串一律当人打的。所以断言的是「楔子没插手」——
// 没发回调、没吃回车、没动框(字符照旧落进去,那是浏览器干的,店员看得见)。
async function slowBurstSweep(browser, origin) {
    const bag = { asked: [], created: [] };
    const page = await boot(browser, bag, origin);
    const rows = [];
    for (const delay of [55, 70, 90, 110, 140, 149]) {
        await openProductFormWith(page, COLA);
        bag.asked.length = 0;
        await armRuler(page, 0, 0);
        await page.keyboard.type(NEW_CODE, { delay });
        const m = await readRuler(page);
        await page.keyboard.press('Enter');
        await page.waitForTimeout(900);
        const value = await page.inputValue('#sx-pf-barcode');
        rows.push({
            delay,
            measuredMax: m.stampMax,
            value,
            // 楔子插手 = 把框还原成扫前的样子(只剩旧码)。没插手 = 字符原样留着。
            wedgeTookIt: value === NEW_CODE,
            asked: bag.asked.slice(),
        });
        await page.evaluate(() => document.getElementById('sx-p-cancel')?.click());
        await page.waitForTimeout(300);
    }
    await shot(page, 'slow-burst-sweep.png');
    const stolen = rows.filter((r) => r.wedgeTookIt);
    return {
        ok: stolen.length === 0,
        rows,
        stolen,
        note:
            '慢串归人手是选出来的结论:没有哪个阈值分得开「慢枪 50~100ms」和「打字快的人 ' +
            '100~260ms」。字符原样留在框里是可见的(店员看得见能改),比静默改效期轻得多。',
        // 楔子放手之后,那 26 位串被条码框自己的 400ms 防抖拿去查了码 —— 一个不可能是条码的
        // 长度也照查照答。这条归建品侧(sales-products-scan.ts),记在这儿别让它消失。
        downstream: rows
            .map((r) => r.asked)
            .flat()
            .filter((c) => c !== COLA && c !== NEW_CODE),
        why: stolen.length ? '慢串被当成枪扫抢走了 · 人手打字会被抹掉' : '',
    };
}

const CASES = [
    ['ruler', ruler],
    ['dateResidue', dateResidue],
    ['gunIntoFilledExpiry', gunIntoFilledExpiry],
    ['humanTypesExpiry', humanTypesExpiry],
    ['heldKey', heldKey],
    ['slowBurstSweep', slowBurstSweep],
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
            (fn) => fn(browser, origin),
            path.join(SHOTS, 'report-ruler.json')
        );
    } finally {
        await browser.close();
        server.close();
    }
    process.exit(failed ? 1 : 0);
})();
