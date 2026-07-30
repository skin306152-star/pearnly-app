/*
 * scripts/_pos_fail_list_verify.cjs · 收银台「扫码失败清单」的真浏览器验收(P0-④ / P1-⑤)
 *
 * 只验两件这一轮改的事,而且都用会出事的输入:
 *   ① 连扫 5 件,没建档的那件排在【队列中间】(不是最后)。旧代码 lookup() 第一句 dropCard()
 *      把上一件的失败卡摘掉,中间只隔几个 microtask —— 屏上什么都没留下。断的是「后面两件
 *      都落地之后,那件失败仍然被 getComputedStyle 判定为可见、码还在屏上」。
 *   ② 只建了「箱」单位行的货扫主码:后端回 matched_unit=ขวด(基本单位)+ base_price。
 *      修过头的那版一律拒收 = 这瓶货在收银台卖不出去;这里断的是它按 ฿15 真进了车。
 *
 * 真的东西:static/pos/pos.html + static/dist/pos.js(含 pos-scan.js)+ 真 pos-i18n.js 字典。
 * 桩只有 /api/pos/products/by-barcode(带 180ms 往返延时 —— 不延时就排不出队列,这条路
 * 永远走不到)。文案期望值现场从页面里的 window.POS_I18N 取,脚本一个字都不注入。
 *
 * 用法(仓库根目录):node scripts/_pos_fail_list_verify.cjs [截图目录]
 * 退出码 0 = 全过。截图默认落 tests/e2e/_artifacts/pos_fail_list/。
 */
const path = require('path');
const { chromium } = require('@playwright/test');
const { ROOT, PHONE, DESKTOP, serve, gun, shotter, runCases } = require('./_gun_wedge_lib.cjs');

const SHOTS = path.resolve(
    process.argv[2] || path.join(ROOT, 'tests/e2e/_artifacts/pos_fail_list')
);
const shot = shotter(SHOTS);

const SOAP = '8850111000015';
const PASTE = '8850111000022';
const GHOST = '8850111000039'; // 柜台上有货、后台没建档 —— 排在队列第 3 位
const POWDER = '8850111000046';
const TISSUE = '8850111000053';
const MASTER = '8858888100022'; // 只建了「箱」的货,主码印在瓶上
const BOX = '18851959131010';
const ROUNDTRIP_MS = 180; // 后端往返:枪比它快得多,后面几件必然压在队列里

function seed() {
    localStorage.setItem('pos_store_token', 'fail-list-verify');
    localStorage.setItem('pos_store_name', 'ร้าน FAILS');
    localStorage.setItem('mrpilot_lang', 'zh'); // 断言对着真 zh 字典
}

function simple(id, name, unit, code, price) {
    return {
        id,
        name: { th: name, en: name, zh: name, ja: name },
        category_id: 1,
        base_unit: unit,
        base_price: price,
        image_url: null,
        vat_applicable: true,
        units: [{ unit_name: unit, factor: '1.000', barcode: code, price, default_sell: true }],
        track_batch: false,
        is_weighed: false,
        stock: { qty_base: '10.000', near_expiry: false },
        matched_unit: unit,
    };
}

// base_unit=ขวด 而 units 里只有 ลัง:units 载不动基本单位的价,只能靠 base_price 下发。
function boxOnly(matchedUnit) {
    return {
        id: 'box-only',
        name: { th: 'โค้กยกลัง', en: 'Coke by case', zh: '可乐整箱', ja: 'コーラ' },
        category_id: 1,
        base_unit: 'ขวด',
        base_price: '15.00',
        image_url: null,
        vat_applicable: true,
        units: [
            {
                unit_name: 'ลัง',
                factor: '24.000',
                barcode: BOX,
                price: '350.00',
                default_sell: true,
            },
        ],
        track_batch: false,
        is_weighed: false,
        stock: { qty_base: '48.000', near_expiry: false },
        matched_unit: matchedUnit,
    };
}

const CATALOG = {
    [SOAP]: simple('p10', 'สบู่', 'ก้อน', SOAP, '32.00'),
    [PASTE]: simple('p11', 'ยาสีฟัน', 'หลอด', PASTE, '45.00'),
    [POWDER]: simple('p12', 'ผงซักฟอก', 'ถุง', POWDER, '59.00'),
    [TISSUE]: simple('p13', 'ทิชชู่', 'ห่อ', TISSUE, '25.00'),
    [MASTER]: boxOnly('ขวด'),
    [BOX]: boxOnly('ลัง'),
};

async function routeBarcode(page) {
    const hits = [];
    await page.route('**/api/pos/products/by-barcode*', async (route) => {
        const code = new URL(route.request().url()).searchParams.get('code');
        hits.push(code);
        const item = CATALOG[code];
        // 真延时:队列是靠「上一件还没回来」形成的,秒回就退化成串行五次独立扫码。
        await new Promise((r) => setTimeout(r, ROUNDTRIP_MS));
        await route.fulfill({
            status: item ? 200 : 404,
            contentType: 'application/json',
            body: JSON.stringify(
                item
                    ? { ok: true, data: item }
                    : { ok: false, error: { code: 'pos.product_not_found', detail: null } }
            ),
        });
    });
    return hits;
}

async function open(browser, origin, viewport) {
    const page = await browser.newPage({ viewport });
    await page.addInitScript(seed);
    const hits = await routeBarcode(page);
    await page.goto(`${origin}/static/pos/pos.html`);
    await page.waitForSelector('#login-cashiers .ca', { timeout: 15000 });
    for (const d of ['1', '2', '3', '4']) await page.click(`#view-login .pad .k[data-pin="${d}"]`);
    await page.waitForSelector('#shift-mask.show', { timeout: 10000 });
    await page.click('#shift-open-go');
    await page.waitForSelector('#view-main.is-active', { timeout: 10000 });
    await page.waitForSelector('#main-grid .prod', { timeout: 10000 });
    return { page, hits };
}

// 「看得见」只认真实排版:元素有 display、有面积、在视口里。断 classList 有没有 show
// 是这轮要根治的那种自欺 —— 类挂上了而整层被别的东西盖住,店员照样什么都没看到。
function panelProbe() {
    const box = document.getElementById('bscan-fails');
    const cs = getComputedStyle(box);
    const r = box.getBoundingClientRect();
    const rows = [...box.querySelectorAll('.bscan-fail')];
    const ack = box.querySelector('.bscan-fails-ack');
    const ackRect = ack ? ack.getBoundingClientRect() : null;
    return {
        display: cs.display,
        visibility: cs.visibility,
        opacity: cs.opacity,
        w: Math.round(r.width),
        h: Math.round(r.height),
        inViewport: r.top >= 0 && r.left >= 0 && r.bottom <= innerHeight && r.right <= innerWidth,
        head: (box.querySelector('.bscan-fails-n') || {}).textContent || '',
        rowCount: rows.length,
        rowText: rows.map((x) => x.textContent).join(' | '),
        codes: [...box.querySelectorAll('.bscan-code')].map((x) => x.textContent),
        ackH: ackRect ? Number(ackRect.height.toFixed(2)) : 0,
        // 清单挂在最上层才有意义:被取景层/购物车盖住 = 挂了等于没挂。
        onTop: (() => {
            const hit = document.elementFromPoint(r.left + r.width / 2, r.top + 8);
            return !!hit && (hit === box || box.contains(hit));
        })(),
    };
}

const cartProbe = () => ({
    lines: [...document.querySelectorAll('#cart-lines .line')].map((l) => ({
        name: l.querySelector('.li-nm .n').textContent,
        price: l.querySelector('.li-nm .u').textContent.trim(),
        qty: l.querySelector('.q[data-qi]').textContent,
    })),
    sub: document.getElementById('cart-subtotal').textContent,
});

const dict = (page) => page.evaluate(() => window.POS_I18N[window.POS.state.lang]);
const fmt = (s, v) => String(s).replace(/\{(\w+)\}/g, (_, k) => v[k]);

// ── ① 队列中间那件失败,扫完还看得见 ─────────────────────────────────────
async function midQueueFailure(browser, origin) {
    const { page, hits } = await open(browser, origin, PHONE);
    const zh = await dict(page);
    // 五枪连着打,不等任何一件回来 —— 真实店里就是这个节奏。
    for (const code of [SOAP, PASTE, GHOST, POWDER, TISSUE]) await gun(page, code);
    await page.waitForFunction(
        () => document.querySelectorAll('#cart-lines .line').length === 4,
        null,
        { timeout: 15000 }
    );
    const burst = hits.slice(); // 这一串是五枪打出来的;下面还要再补一枪
    const panel = await page.evaluate(panelProbe);
    const cart = await page.evaluate(cartProbe);
    await shot(page, '01-mid-queue-failure-390.png');
    // 队列排空之后又扫中一件:命中不许把上一件的失败顺手收掉(旧代码正是在这一步抹的)。
    await gun(page, TISSUE);
    await page.waitForFunction(
        () =>
            [...document.querySelectorAll('#cart-lines .q[data-qi]')].some(
                (q) => q.textContent === '2'
            ),
        null,
        { timeout: 15000 }
    );
    const afterHit = await page.evaluate(panelProbe);
    await shot(page, '02-still-there-after-next-hit-390.png');
    // 清单会一直挂到店员点掉,期间完全可能切语言:pos.js 的 rerenderActive() 只重渲当前那一屏,
    // 覆不到这个跨屏常驻浮层 —— 不接线就永远停在旧语言。
    await page.click('.topbar-langs button[data-lang="th"]');
    await page.waitForTimeout(150);
    const afterLang = await page.evaluate(panelProbe);
    const th = await dict(page);
    await shot(page, '03-relang-th-390.png');
    await page.click('#bscan-fails .bscan-fails-ack');
    await page.waitForTimeout(150);
    const afterAck = await page.evaluate(panelProbe);
    await page.close();
    return {
        ok:
            burst.length === 5 &&
            hits.length === 6 &&
            cart.lines.length === 4 &&
            cart.sub === '161.00' &&
            panel.display !== 'none' &&
            panel.visibility === 'visible' &&
            Number(panel.opacity) === 1 &&
            panel.w > 0 &&
            panel.h > 0 &&
            panel.inViewport &&
            panel.onTop &&
            panel.rowCount === 1 &&
            panel.codes.includes(GHOST) &&
            panel.head === fmt(zh['posui.bscan.fails_n'], { n: 1 }) &&
            panel.rowText.includes(zh['posui.bscan.create_where']) &&
            panel.ackH >= 44 &&
            afterHit.display !== 'none' &&
            afterHit.rowCount === 1 &&
            afterLang.head === fmt(th['posui.bscan.fails_n'], { n: 1 }) &&
            afterLang.rowText.includes(th['posui.bscan.create_where']) &&
            // 正文也得跟着换：存死译好的句子时，标题泰文正文中文——真截图上抓到过
            afterLang.rowText.includes(th['bscan.notfound'].split('{code}')[0].trim()) &&
            !afterLang.rowText.includes(zh['bscan.notfound'].split('{code}')[0].trim()) &&
            afterAck.display === 'none',
        burst,
        hits,
        cart,
        panel,
        afterHit,
        afterLangHead: afterLang.head,
        afterAckDisplay: afterAck.display,
    };
}

// ── ② 只建了「箱」的货扫主码:按基本单位真卖得出去 ───────────────────────
async function baseUnitSells(browser, origin) {
    const { page } = await open(browser, origin, DESKTOP);
    await gun(page, MASTER);
    await page.waitForFunction(() => document.querySelectorAll('#cart-lines .line').length === 1, {
        timeout: 15000,
    });
    const afterMaster = await page.evaluate(cartProbe);
    const panel = await page.evaluate(panelProbe);
    await gun(page, BOX); // 同一件货的箱码:必须另起一行,并成一行 = 刚才那扫其实按箱卖了
    await page.waitForFunction(() => document.querySelectorAll('#cart-lines .line').length === 2, {
        timeout: 15000,
    });
    const afterBox = await page.evaluate(cartProbe);
    await shot(page, '04-base-unit-sells-1280.png');
    await page.close();
    return {
        ok:
            afterMaster.lines.length === 1 &&
            afterMaster.lines[0].price.includes('15.00') &&
            panel.display === 'none' && // 能卖的货不许报错
            afterBox.lines.length === 2 &&
            afterBox.sub === '365.00',
        afterMaster,
        afterBox,
        panelDisplay: panel.display,
    };
}

(async () => {
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch();
    const code = await runCases(
        [
            ['mid_queue_failure', midQueueFailure],
            ['base_unit_sells', baseUnitSells],
        ],
        (fn) => fn(browser, origin),
        path.join(SHOTS, 'report.json')
    );
    await browser.close();
    server.close();
    process.exit(code);
})();
