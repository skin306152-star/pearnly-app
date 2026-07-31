/*
 * scripts/_inv_guards_verify.cjs · 入库弹窗几道兜底的真浏览器验收(两个方向各自量)
 *
 * ① 摄像头把第二箱当成「同一件还在画面里」挡下的那一次(scan-camera.js 的 onDuplicate)。
 *    引擎两把尺子 AND 起来必然有个地板;地板【以下】拿走 A 再举 B,与一次长反光在解码结果上
 *    完全同形 —— 引擎分不出,只能问店员。这一条只有真解码器 + 真节拍答得了:单测里的
 *    gapMs/misses 是喂进去的,这里的是 ZXing 自己烧出来的。
 *      正向 .blink12(货离开 1.2s < 地板)→ 屏上必须出现那句问话 + 一点就补上的路;
 *      反向 .blink20(离开 2.0s > 地板)→ 引擎自己就认第二件,数量直接变 2、不许冒那句问话;
 *      正向 .blinkmix(1.2s 与 2.0s 交替)→ 那句问话【活得下来】:全程没人碰屏,它不许自己没掉。
 *    前两条只验「出没出来」;第三条补的是「出来之后还在不在」—— 那行原先占的是瞬时行(一格),
 *    下一次扫的第一句「正在查这个条码」就把它整格盖掉。实测(修之前 · 14.1 秒):出现 3 次、
 *    无人触碰下消失 2 次,收货单最后 3 件而柜台上过了 6 箱,少的三箱屏上零痕迹。
 *    单一空档的素材验不了它:「被挡下」与「后面真记上一件」只有在同一份素材里才会先后发生。
 *
 * ② 提交前的数量兜底(isSaneQty)。楔子那层再准也有漏(残串只剩三四位时谁也分不出来)。
 *      正向:19 亿件必须被拦在提交之外,且屏上真看得见那句话(量 getComputedStyle + 面积);
 *      反向:25 万件这种真实大批量必须照旧提交得出去(拿真发出的 POST 载荷当证据)。
 *
 * ③ 单价格的同两层。它漏过枪 opt-in:光标停在单价格时来一发枪,฿8850999320014/瓶 原样
 *    提交、零查码、屏上零字(下面 costGunLandsAsARow 复现的就是这一幕)。它比数量更该有
 *    兜底 —— 数量错了架上一点就对不上,单价错了只动库存估值与移动加权成本,当场看不出来。
 *      正向:枪扫进单价格 → 单价格回到扫之前 + 这一发落成一行;条码当单价必须拦在提交外;
 *      反向:฿2,400,000/件(一公斤金条)这种真实高价必须照旧提交得出去。
 *
 * ④ 相机被系统收走(来电 / 切后台 / 别的 app 抢 / 拔 USB)之后,收货单上还说不说在扫。
 *    收走的那一刻 <video> 停在最后一帧:readyState 仍是 4、videoWidth 仍是 640,引擎那句
 *    videoReady() 恒真 → 一直在解同一张死图,屏上「对准条码」照旧而数量再也不涨。
 *    引擎是收银台与入库共用的一份,上一轮的教训正是「同一个洞的两个消费方,修了一个漏了
 *    一个」—— 收银台那一侧归 scripts/_hostile_scan_cam_verify.cjs 的 cam* 五条,这一条守入库。
 *      正向 .blink20 + 真 track.stop():屏上必须出现那句话 + 一条走得通的重试,数量一件不多;
 *      反向由 ① 的两条兼着:相机好好的时候一次都不许冒这句红字(errLine 进它们的 ok)。
 *
 * 「枪比网络快 → 后半串落进数量格」那条(跨界快照)不在本脚本里,验它的是
 * scripts/_r5_wedge_cross_verify.cjs 的 c1/c1b —— 那条的修在楔子层,归那份。
 *
 * 真的东西:home.html + dist/{main.js,pre.js,home.css,scan.js,zxing.js} 全是本仓真产物;
 * 摄像头是 Chromium 假设备喂真合成 EAN-13;期望文案现场从页面里的真 window.I18N 取。
 * 桩只有 /api/**(查码 / 货架 / 入库)与账套切换器 —— 都不在被验的那条链上。
 *
 * 跑法(仓库根目录):
 *   python scripts/_scan_ean_blink_y4m.py .blink12.y4m 8850999320014 1.2
 *   python scripts/_scan_ean_blink_y4m.py .blink20.y4m 8850999320014 2.0
 *   python scripts/_scan_ean_blink_y4m.py .blinkmix.y4m 8850999320014 1.2 2.0
 *   node scripts/_inv_guards_verify.cjs [截图目录]
 * 退出码 0 = 全过。截图默认落 tests/e2e/_artifacts/inv_guards/。
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('@playwright/test');
const { ROOT, PHONE, BOX, cdpGun, serve, shotter, runCases } = require('./_gun_wedge_lib.cjs');

const SHOTS = path.resolve(process.argv[2] || path.join(ROOT, 'tests/e2e/_artifacts/inv_guards'));
const shot = shotter(SHOTS);
const BLINK12 = path.resolve('.blink12.y4m'); // 离开 1.2s:地板以下 → 该被挡下并问一句
const BLINK20 = path.resolve('.blink20.y4m'); // 离开 2.0s:地板以上 → 引擎自己认第二件
const BLINKMIX = path.resolve('.blinkmix.y4m'); // 两档交替 → 挡下与真记一件在同一跑里各来一遍
const WATCH_MS = 14000; // 观察窗口:够 .blinkmix(5.6s 一圈)走完两圈半

// 那句问话所在的那一行。从按钮往上找,不写死行的类名 —— 它这一轮从瞬时行搬进了累积清单,
// 类名跟着变(tip → warn);写死类名的判据会跟着搬家漂,漂完量的是「找不到元素」。
const DUP_LINE = '#inv-in-mask-scan-msg .inv-scan-line:has([data-scan-dup])';

const P_COLA = {
    id: 'p-cola',
    name_th: 'โค้ก 325ml',
    name_en: 'Coke 325ml',
    name_zh: '可乐 325ml',
    track_batch: false,
};
const STOCK = [
    {
        product_id: 'p-cola',
        name: { th: 'โค้ก 325ml', en: 'Coke 325ml', zh: '可乐 325ml' },
        image_url: null,
        barcode: BOX,
        base_unit: 'ขวด',
        qty_on_hand: 12,
        min_stock: 5,
        avg_cost: 9.5,
        status: 'ok',
        track_batch: false,
        batches: [],
    },
];

/** 收货弹窗开在手机宽度上(用手机相机收货才是这功能的真实场景)。bag 记下真发出去的请求。 */
async function openInModal(browser, origin) {
    const page = await browser.newPage({ viewport: PHONE });
    const bag = { lookups: [], posted: [] };
    await page.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'inv-guards');
        localStorage.setItem('mrpilot_lang', 'zh');
    });
    await page.route('**/api/**', async (route) => {
        const url = new URL(route.request().url());
        if (url.pathname === '/api/sales/products/lookup') {
            const code = url.searchParams.get('code') || url.searchParams.get('barcode');
            bag.lookups.push(code);
            return route.fulfill(
                code === BOX
                    ? { json: { product: P_COLA, matched_by: 'product' } }
                    : { status: 404, json: { detail: 'sales.product_not_found' } }
            );
        }
        if (url.pathname === '/api/inventory/in') {
            bag.posted.push(route.request().postDataJSON());
            return route.fulfill({ json: { ok: true, data: {} } });
        }
        if (url.pathname === '/api/inventory/stock')
            return route.fulfill({
                json: {
                    ok: true,
                    data: {
                        items: STOCK,
                        summary: { sku_count: 1, stock_value: 114, low_count: 0, out_count: 0 },
                    },
                },
            });
        if (url.pathname === '/api/me')
            return route.fulfill({ json: { email: 'guards@e2e', role: 'owner', plan: 'pro' } });
        return route.fulfill({ json: { ok: true, data: {}, items: [] } });
    });
    await page.goto(`${origin}/home.html`);
    await page.waitForFunction(() => typeof window.openInventoryIn === 'function');
    await page.evaluate(() => {
        document.body.classList.remove('workspace-gate-preboot');
        document.getElementById('workspace-gate-root')?.remove();
        window.getActiveWorkspaceClientId = () => 1;
        document.querySelectorAll('.page').forEach((p) => p.classList.remove('active'));
        document.getElementById('page-inventory').classList.add('active');
        window.loadInventoryPage();
    });
    // 等货架真到了:行里的商品下拉是开窗那一刻现拼的,货没到就拼出一个只有「—」的空下拉
    await page.waitForFunction(() => {
        const b = document.getElementById('inv-tbody');
        return !!b && b.textContent.includes('可乐');
    });
    await page.locator('#inv-btn-in').click();
    await page.locator('#inv-in-mask .inv-scan').waitFor();
    return { page, bag };
}

/** 屏上真看得见吗:有面积、没被 display/visibility/opacity 藏起来、而且真落在视口里。 */
function onScreen(sel) {
    const el = document.querySelector(sel);
    if (!el) return { found: false };
    const box = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return {
        found: true,
        w: Math.round(box.width),
        h: Math.round(box.height),
        display: cs.display,
        visibility: cs.visibility,
        opacity: cs.opacity,
        inView: box.top < innerHeight && box.bottom > 0 && box.left < innerWidth && box.right > 0,
        text: el.innerText.trim(),
    };
}

/** 「这台机器扫不了」那一档红字在不在。正常扫码路上它一次都不许冒。 */
const errLine = (page) =>
    page.evaluate(() => !!document.querySelector('#inv-in-mask-scan-msg .inv-scan-line.err'));

const dict = (page, key) => page.evaluate((k) => window.I18N.zh[k], key);
const qtyOf = (page) =>
    page.evaluate(() => document.querySelector('#inv-in-mask-rows [data-k="qty"]').value);

// 相机开起来 + 第一箱真解出来(qty=1)。回 false = 素材/解码器没就绪,由用例判红。
async function firstBoxScanned(page) {
    await page.locator('#inv-in-mask-scan-cam').click();
    return page
        .waitForFunction(
            () => document.querySelector('#inv-in-mask-rows [data-k="qty"]').value === '1',
            null,
            { timeout: 60000 }
        )
        .then(
            () => true,
            () => false
        );
}

// ── ① 正向:地板以下的第二箱被挡下 → 屏上有问话,点一下补得回来 ─────────────
async function suppressedSecondBoxSpeaksUp(browser, origin) {
    const { page, bag } = await openInModal(browser, origin);
    const first = await firstBoxScanned(page);
    // 素材循环播:货离开 1.2s 再举回来 —— 这一回合引擎会挡下它(地板 ≈1.6s)
    const appeared = await page
        .waitForSelector('#inv-in-mask-scan-msg [data-scan-dup]', { timeout: 60000 })
        .then(
            () => true,
            () => false
        );
    const note = await page.evaluate(onScreen, DUP_LINE);
    const btn = await page.evaluate(onScreen, '#inv-in-mask-scan-msg [data-scan-dup]');
    const copy = await dict(page, 'inv-scan-dup');
    const qtyBefore = await qtyOf(page);
    await shot(page, '01-dup-notice.png');
    if (appeared) await page.locator('#inv-in-mask-scan-msg [data-scan-dup]').click();
    const qtyAfter = await page
        .waitForFunction(
            () => Number(document.querySelector('#inv-in-mask-rows [data-k="qty"]').value) >= 2,
            null,
            { timeout: 15000 }
        )
        .then(
            () => qtyOf(page),
            () => qtyOf(page)
        );
    await shot(page, '02-dup-added.png');
    const rows = await page.evaluate(
        () => document.querySelectorAll('#inv-in-mask-rows [data-row]').length
    );
    const err = await errLine(page); // 相机好好的却报「这台机器扫不了」= 跟不报一样是骗人
    await page.close();
    return {
        ok:
            first &&
            appeared &&
            !err &&
            note.found &&
            note.h > 0 &&
            note.display !== 'none' &&
            note.visibility !== 'hidden' &&
            note.opacity !== '0' &&
            note.text.includes(copy) && // 屏上那句 = 真词典里那一句(不在脚本里抄中文)
            note.text.includes(BOX) &&
            btn.found &&
            btn.h > 0 &&
            qtyBefore === '1' && // 被挡下时数量确实没动 —— 不然验的不是「压制」
            String(qtyAfter) === '2' &&
            rows === 2, // 补一件是累加,不是另起一行
        first,
        appeared,
        qtyBefore,
        qtyAfter,
        rows,
        err,
        note,
        btn,
        copy,
        lookups: bag.lookups.length,
    };
}

// ── ① 反向:地板以上的第二箱,引擎自己就认 —— 数量直接变 2,不许冒那句问话 ───
async function secondBoxAboveTheFloorJustCounts(browser, origin) {
    const { page, bag } = await openInModal(browser, origin);
    const first = await firstBoxScanned(page);
    const counted = await page
        .waitForFunction(
            () => document.querySelector('#inv-in-mask-rows [data-k="qty"]').value === '2',
            null,
            { timeout: 60000 }
        )
        .then(
            () => true,
            () => false
        );
    const nagged = await page.evaluate(
        () => !!document.querySelector('#inv-in-mask-scan-msg [data-scan-dup]')
    );
    const text = await page.evaluate(
        () => document.getElementById('inv-in-mask-scan-msg').innerText
    );
    const err = await errLine(page); // 同上:正常连扫路上不许冒「这台机器扫不了」
    await shot(page, '03-above-floor-counts.png');
    await page.close();
    return {
        ok: first && counted && !nagged && !err,
        first,
        counted,
        nagged,
        err,
        text,
        lookups: bag.lookups,
    };
}

// ── ④ 相机被系统收走 → 入库这一侧也得出声(同一个洞的第二个消费方)────────────────
// 引擎在收银台和入库弹窗上是同一份;上一轮的教训正是「同一个洞的两个消费方,修了一个漏了
// 一个」。收银台那一侧由 scripts/_hostile_scan_cam_verify.cjs 的 cam* 五条守着,这一条守
// 入库:相机被收走之后,收货单上必须看得见一句话 + 一条走得通的重试,数量一件不许多。
// 收走用真 API track.stop():规范上它【不发】 ended 事件,只有引擎每拍轮询照得到。
async function cameraRevokedSpeaksUpOnIntake(browser, origin) {
    const { page, bag } = await openInModal(browser, origin);
    const first = await firstBoxScanned(page);
    // 素材是「离开 2.0s 再举回来」(地板以上)→ 数量本来会一路涨,冻住才有对照物。
    const grew = await page
        .waitForFunction(
            () => Number(document.querySelector('#inv-in-mask-rows [data-k="qty"]').value) >= 2,
            null,
            { timeout: 60000 }
        )
        .then(
            () => true,
            () => false
        );
    const qtyBefore = await qtyOf(page);
    const lookupsBefore = bag.lookups.length;
    const tracks = await page.evaluate(() => {
        const v = document.querySelector('#inv-in-mask-scan-stage video');
        if (!v || !v.srcObject) return null;
        const ts = v.srcObject.getTracks();
        ts.forEach((t) => t.stop());
        return ts.map((t) => ({ st: t.readyState }));
    });
    const spoke = await page
        .waitForSelector('#inv-in-mask-scan-msg [data-scan-retry]', { timeout: 15000 })
        .then(
            () => true,
            () => false
        );
    await page.waitForTimeout(6000); // 一个多周期:收走之后数量一件都不许再涨
    const line = await page.evaluate(onScreen, '#inv-in-mask-scan-msg .inv-scan-line.err');
    const btn = await page.evaluate(onScreen, '#inv-in-mask-scan-msg [data-scan-retry]');
    const copy = await dict(page, 'bscan.err.busy');
    const retryCopy = await dict(page, 'inv-scan-retry');
    const qtyFrozen = await qtyOf(page);
    const lookupsFrozen = bag.lookups.length;
    await shot(page, '09-cam-revoked.png');
    // 重试得是真出口:点下去必须重新开起来,数量接着涨 —— 不然那颗按钮只是句安慰话。
    if (spoke) await page.locator('#inv-in-mask-scan-msg [data-scan-retry]').click();
    const resumed = await page
        .waitForFunction(
            (n) => Number(document.querySelector('#inv-in-mask-rows [data-k="qty"]').value) > n,
            Number(qtyFrozen),
            { timeout: 60000 }
        )
        .then(
            () => true,
            () => false
        );
    const qtyAfter = await qtyOf(page);
    const errAfter = await errLine(page);
    await shot(page, '10-cam-revoked-retry.png');
    await page.close();
    return {
        ok:
            first &&
            grew &&
            !!tracks &&
            tracks.every((t) => t.st === 'ended') && // 相机真被收走了,不然验的是别的事
            spoke &&
            line.found &&
            line.h > 0 &&
            line.display !== 'none' &&
            line.visibility !== 'hidden' &&
            line.opacity !== '0' &&
            line.inView &&
            line.text.includes(copy) && // 屏上那句 = 真词典里那一句
            btn.found &&
            btn.h > 0 &&
            btn.text === retryCopy &&
            qtyFrozen === qtyBefore && // 收走之后数量诚实:没扫上就是没扫上
            lookupsFrozen === lookupsBefore && // 也没在背地里查码 —— 收走之后真的什么都没发生
            resumed &&
            Number(qtyAfter) > Number(qtyFrozen) &&
            !errAfter, // 重开之后那句红字得收掉,不能一直挂着吓人
        first,
        grew,
        tracks,
        spoke,
        qtyBefore,
        qtyFrozen,
        qtyAfter,
        lookupsBefore,
        lookupsFrozen,
        line,
        btn,
        copy,
        retryCopy,
        resumed,
        errAfter,
        lookups: bag.lookups.length,
    };
}

// 那行问话在这一跑里只可能被产品自己抹掉(全程没人点任何按钮)。抹一次 = 被挡下的那一箱最后
// 一条线索也没了,屏上跟全都收上了一模一样。整格是 innerHTML 重写,消失只在重画那一刻发生
// → MutationObserver 抓每一次重画;再叠一层 100ms 轮询兜底(同一条线程写同一个数组,时序
// 天然对得上)。只看窗口末尾那一眼没用:素材循环播,末尾正好停在哪一段是随机的。
function watchDupRow() {
    const box = document.getElementById('inv-in-mask-scan-msg');
    const sample = () => {
        const qty = document.querySelector('#inv-in-mask-rows [data-k="qty"]');
        window.__dupLog.push({
            row: !!box.querySelector('[data-scan-dup]'),
            qty: qty ? qty.value : '',
        });
    };
    window.__dupLog = [];
    sample();
    window.__dupObs = new MutationObserver(sample);
    window.__dupObs.observe(box, { childList: true, subtree: true, characterData: true });
    window.__dupTimer = setInterval(sample, 100);
}

function readDupWatch() {
    clearInterval(window.__dupTimer);
    window.__dupObs.disconnect();
    const log = window.__dupLog;
    let appeared = 0;
    let vanished = 0;
    for (let i = 1; i < log.length; i++) {
        if (log[i].row && !log[i - 1].row) appeared += 1;
        if (!log[i].row && log[i - 1].row) vanished += 1;
    }
    return { appeared, vanished, samples: log.length };
}

// ── ① 正向 b:那句问话活得下来(长短空档交替 · 全程无人触碰)────────────────
// 上面两条只验它出没出来。它原先占瞬时行(一格),下一次扫的第一句 setMsg('busy') 整格覆盖 ——
// 修之前实测 14.1 秒里出现 3 次、无人触碰下消失 2 次(t=6515ms / t=12131ms),两次都被
// 「正在查这个条码…」顶掉,收货单最后 3 件而这段里柜台上过了 6 箱。
// 收银台那一侧的同一条在 scripts/_r5_cam_dupnotice_verify.cjs 的 mix1200-2000。
async function theDupNoticeSurvivesTheNextScan(browser, origin) {
    const { page, bag } = await openInModal(browser, origin);
    const first = await firstBoxScanned(page);
    await page.evaluate(watchDupRow);
    const lookupsBefore = bag.lookups.length;
    await page.waitForTimeout(WATCH_MS);
    const seen = await page.evaluate(readDupWatch);
    const rearms = bag.lookups.length - lookupsBefore;
    const note = await page.evaluate(onScreen, DUP_LINE);
    const qty = await qtyOf(page);
    const rows = await page.evaluate(
        () => document.querySelectorAll('#inv-in-mask-rows [data-row]').length
    );
    await shot(page, '02b-dup-notice-survives.png');
    await page.close();
    return {
        ok:
            first &&
            seen.appeared > 0 && // 真被挡下过 —— 没有它,vanished=0 只是「从来没出现过」
            rearms > 0 && // 期间真也记上过货 —— 没走到「后面那一件把前面那行销掉」的路上,这一绿不算数
            seen.vanished === 0 && // 判据本身:没人动它,行就不许消失
            note.found &&
            note.h > 0 &&
            note.display !== 'none' &&
            note.visibility !== 'hidden' &&
            note.opacity !== '0' &&
            Number(qty) >= 2 && // 地板以上那几次照旧真记进单(没把「还认不认第二件」弄坏)
            rows === 2, // 同一件非批次货只该累加,不许每挡一次多出一行
        first,
        appeared: seen.appeared,
        vanished: seen.vanished,
        samples: seen.samples,
        rearms,
        qty,
        rows,
        note,
    };
}

// ── ② 正向:一串条码当数量 → 拦住 + 屏上说得出为什么 ────────────────────────
async function barcodeAsQuantityIsStopped(browser, origin) {
    const { page, bag } = await openInModal(browser, origin);
    await page.selectOption(
        '#inv-in-mask-rows [data-row]:first-child [data-k="product_id"]',
        'p-cola'
    );
    const qty = page.locator('#inv-in-mask-rows [data-row]:first-child [data-k="qty"]');
    await qty.click();
    await page.keyboard.type('1' + BOX, { delay: 200 }); // 200ms/字符 = 人手,不会被楔子抢走
    await page.locator('#inv-in-mask-submit').click();
    await page.waitForTimeout(600);
    const err = await page.evaluate(onScreen, '#inv-in-mask-err');
    const copy = await dict(page, 'inv-err-bad-qty');
    const focused = await page.evaluate(() => (document.activeElement.dataset || {}).k === 'qty');
    const open = await page.evaluate(() =>
        document.getElementById('inv-in-mask').classList.contains('show')
    );
    await shot(page, '04-qty-backstop.png');
    await page.close();
    return {
        ok:
            bag.posted.length === 0 &&
            err.found &&
            err.h > 0 &&
            err.display !== 'none' &&
            err.text === copy &&
            focused &&
            open,
        posted: bag.posted,
        err,
        copy,
        focused,
        open,
    };
}

// ── ② 反向:真实大批量照旧提交得出去(载荷为证)────────────────────────────
async function aRealBulkReceiptStillPosts(browser, origin) {
    const { page, bag } = await openInModal(browser, origin);
    await page.selectOption(
        '#inv-in-mask-rows [data-row]:first-child [data-k="product_id"]',
        'p-cola'
    );
    await page.locator('#inv-in-mask-rows [data-row]:first-child [data-k="qty"]').click();
    await page.keyboard.type('250000', { delay: 120 });
    await page.locator('#inv-in-mask-submit').click();
    const closed = await page
        .waitForFunction(
            () => !document.getElementById('inv-in-mask').classList.contains('show'),
            null,
            { timeout: 15000 }
        )
        .then(
            () => true,
            () => false
        );
    await shot(page, '05-bulk-posted.png');
    await page.close();
    const line = bag.posted[0] && bag.posted[0].lines && bag.posted[0].lines[0];
    return {
        ok: closed && !!line && line.qty === '250000' && line.product_id === 'p-cola',
        closed,
        posted: bag.posted,
    };
}

// ── ③ 正向 a:枪打进单价格 —— 框回到扫之前,这一发落成一行 ───────────────────
// 修之前实测(同一段代码,只是单价框没写 data-enable-barcode):unit_cost 变成
// "8850999320014"、lookups 一次都没发、扫码消息格是空串、提交照样成功关窗。
async function costGunLandsAsARow(browser, origin) {
    const { page, bag } = await openInModal(browser, origin);
    await page.selectOption(
        '#inv-in-mask-rows [data-row]:first-child [data-k="product_id"]',
        'p-cola'
    );
    const cost = page.locator('#inv-in-mask-rows [data-row]:first-child [data-k="unit_cost"]');
    await cost.click();
    await page.keyboard.type('9.5', { delay: 200 }); // 人手先填好真单价:还原得对得上它
    const before = await cost.inputValue();
    bag.lookups.length = 0;
    const cdp = await page.context().newCDPSession(page);
    await cdpGun(cdp, BOX, 8, 'Enter');
    await page.waitForTimeout(1500);
    const after = await cost.inputValue();
    const msg = await page.evaluate(onScreen, '#inv-in-mask-scan-msg');
    const qty = await qtyOf(page);
    await shot(page, '06-cost-gun-lands.png');
    await page.close();
    return {
        // 两侧同时成立:单价格干净(正向)且这一发真去查了码、真落了行(不是被吞掉)
        ok:
            before === '9.5' &&
            after === '9.5' &&
            bag.lookups.length === 1 &&
            bag.lookups[0] === BOX &&
            qty === '1',
        costBefore: before,
        costAfter: after,
        lookups: bag.lookups,
        qty,
        msg,
    };
}

// ── ③ 正向 b:条码当单价被拦在提交之外 ─────────────────────────────────────
async function barcodeAsCostIsStopped(browser, origin) {
    const { page, bag } = await openInModal(browser, origin);
    await page.selectOption(
        '#inv-in-mask-rows [data-row]:first-child [data-k="product_id"]',
        'p-cola'
    );
    await page.locator('#inv-in-mask-rows [data-row]:first-child [data-k="qty"]').click();
    await page.keyboard.type('12', { delay: 200 });
    const cost = page.locator('#inv-in-mask-rows [data-row]:first-child [data-k="unit_cost"]');
    await cost.click();
    await page.keyboard.type(BOX, { delay: 200 }); // 200ms/字符 = 人手,楔子不抢
    await page.locator('#inv-in-mask-submit').click();
    await page.waitForTimeout(600);
    const err = await page.evaluate(onScreen, '#inv-in-mask-err');
    const copy = await dict(page, 'inv-err-bad-cost');
    const focused = await page.evaluate(
        () => (document.activeElement.dataset || {}).k === 'unit_cost'
    );
    const open = await page.evaluate(() =>
        document.getElementById('inv-in-mask').classList.contains('show')
    );
    await shot(page, '07-cost-backstop.png');
    await page.close();
    return {
        ok:
            bag.posted.length === 0 &&
            err.found &&
            err.h > 0 &&
            err.display !== 'none' &&
            err.text === copy &&
            focused &&
            open,
        posted: bag.posted,
        err,
        copy,
        focused,
        open,
    };
}

// ── ③ 反向:真实高价照旧提交得出去(฿2,400,000/件 ≈ 一公斤金条)────────────────
async function aRealHighCostStillPosts(browser, origin) {
    const { page, bag } = await openInModal(browser, origin);
    await page.selectOption(
        '#inv-in-mask-rows [data-row]:first-child [data-k="product_id"]',
        'p-cola'
    );
    await page.locator('#inv-in-mask-rows [data-row]:first-child [data-k="qty"]').click();
    await page.keyboard.type('2', { delay: 120 });
    await page.locator('#inv-in-mask-rows [data-row]:first-child [data-k="unit_cost"]').click();
    await page.keyboard.type('2400000', { delay: 120 });
    await page.locator('#inv-in-mask-submit').click();
    const closed = await page
        .waitForFunction(
            () => !document.getElementById('inv-in-mask').classList.contains('show'),
            null,
            { timeout: 15000 }
        )
        .then(
            () => true,
            () => false
        );
    await shot(page, '08-high-cost-posted.png');
    await page.close();
    const line = bag.posted[0] && bag.posted[0].lines && bag.posted[0].lines[0];
    return {
        ok: closed && !!line && line.unit_cost === '2400000' && line.qty === '2',
        closed,
        posted: bag.posted,
    };
}

(async () => {
    for (const f of [BLINK12, BLINK20, BLINKMIX]) {
        if (!fs.existsSync(f)) {
            console.error(`缺素材 ${f} —— 见本文件头部的跑法`);
            process.exit(2);
        }
    }
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    // 假摄像头素材是浏览器启动参数 → 一个用例一台浏览器;不吃素材的两条用同一台。
    const CAM = (y4m) => [
        '--use-fake-ui-for-media-stream',
        '--use-fake-device-for-media-stream',
        `--use-file-for-fake-video-capture=${y4m}`,
    ];
    const cases = [
        ['dupNoticeBelowFloor', suppressedSecondBoxSpeaksUp, CAM(BLINK12)],
        ['secondBoxAboveFloor', secondBoxAboveTheFloorJustCounts, CAM(BLINK20)],
        ['dupNoticeSurvivesMixed', theDupNoticeSurvivesTheNextScan, CAM(BLINKMIX)],
        ['camRevokedSpeaksUp', cameraRevokedSpeaksUpOnIntake, CAM(BLINK20)],
        ['barcodeAsQuantityStopped', barcodeAsQuantityIsStopped, []],
        ['realBulkStillPosts', aRealBulkReceiptStillPosts, []],
        ['costGunLandsAsARow', costGunLandsAsARow, []],
        ['barcodeAsCostStopped', barcodeAsCostIsStopped, []],
        ['realHighCostStillPosts', aRealHighCostStillPosts, []],
    ];
    const failed = await runCases(
        cases.map(([name, fn, args]) => [name, { fn, args }]),
        async ({ fn, args }) => {
            const browser = await chromium.launch(args.length ? { args } : {});
            try {
                return await fn(browser, origin);
            } finally {
                await browser.close();
            }
        },
        path.join(SHOTS, 'report.json')
    );
    server.close();
    process.exit(failed ? 1 : 0);
})();
