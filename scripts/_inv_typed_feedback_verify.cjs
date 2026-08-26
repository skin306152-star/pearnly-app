/*
 * scripts/_inv_typed_feedback_verify.cjs · 入库弹窗:被判成「人在打字」的那一发 + 窄屏行宽
 *
 * 两件只有真浏览器答得了的事:
 *
 *  ① 那句话真的在屏上吗。楔子判不出是枪打的就把这一发交还给人 —— 不回调、不动框里的内容。
 *     三轮实测的那一幕就是这里:慢枪扫的第二箱整箱从收货单消失,消息还停在上一件的「已加入」,
 *     店员以为枪没响。单测能断「变量里有这句话」,断不了「这句话在屏上看得见」——
 *     所以这里量 getComputedStyle + getBoundingClientRect,期望文本现场从真 window.I18N 取
 *     (不在脚本里抄一份中文,抄的那份跟词典一漂,断言就变成断自己)。
 *  ② 390 宽下那一行到底多宽。批号框被四列网格挤到 30px、只显得下两个字符这件事,
 *     只有真 CSS + 真布局量得出来;grep 类名和「CSS 属性设上了」都不算(本仓吃过这个亏)。
 *
 * 真的东西:home.html + static/dist/{main.js,pre.js,home.css} + 真 static/i18n-data.js,
 * 按键全走 keyboard.type(fill() 一个 keydown 都不发,楔子收不到 = 假绿)。
 * 桩只有 /api/**(查码由本脚本应答并计数)与账套切换器 —— 两者都不在判定这条链上。
 *
 * 用法(仓库根目录):node scripts/_inv_typed_feedback_verify.cjs [截图目录]
 * 退出码 0 = 全过。截图默认落 tests/e2e/_artifacts/inv_typed_feedback/。
 */
/* eslint-disable no-undef */
const path = require('path');
const { chromium } = require('@playwright/test');
const {
    ROOT,
    PHONE,
    DESKTOP,
    BOX,
    serve,
    gun,
    shotter,
    runCases,
} = require('./_gun_wedge_lib.cjs');

const MILK = '4901234567894'; // 批次品 · 慢枪那一发打的就是它
const SHOTS = path.resolve(
    process.argv[2] || path.join(ROOT, 'tests/e2e/_artifacts/inv_typed_feedback')
);
const shot = shotter(SHOTS);

const SLOW_GUN_MS = 90; // 过不了楔子 50ms 那条,又没到 150ms 的断串线 —— 就是「慢枪」那一档

const CATALOG = {
    [BOX]: { id: 'p-cola', name_th: 'โค้ก 325ml', name_en: 'Coke 325ml', name_zh: '可乐 325ml' },
    [MILK]: {
        id: 'p-milk',
        name_th: 'นมจืด 180ml',
        name_en: 'Milk 180ml',
        name_zh: '牛奶 180ml',
        track_batch: true,
    },
};

function stockRow(id, name, barcode, trackBatch) {
    return {
        product_id: id,
        name,
        image_url: null,
        barcode,
        base_unit: 'ขวด',
        qty_on_hand: 12,
        min_stock: 5,
        avg_cost: 9.5,
        status: 'ok',
        track_batch: trackBatch,
        batches: [],
    };
}

const STOCK = [
    stockRow('p-cola', { th: 'โค้ก 325ml', en: 'Coke 325ml', zh: '可乐 325ml' }, BOX, false),
    stockRow('p-milk', { th: 'นมจืด 180ml', en: 'Milk 180ml', zh: '牛奶 180ml' }, MILK, true),
];

async function openInModal(browser, origin, viewport) {
    const page = await browser.newPage({ viewport });
    await page.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'typed-verify');
        localStorage.setItem('mrpilot_lang', 'zh'); // 期望值仍现场从 I18N 取,这里只定屏上语言
        localStorage.setItem('pearnly_entry', 'pos');
        localStorage.setItem('pearnly_active_workspace_client_id', '1');
    });
    const hits = [];
    await page.route('**/api/**', async (route) => {
        const url = new URL(route.request().url());
        if (url.pathname === '/api/sales/products/lookup') {
            const code = url.searchParams.get('barcode');
            hits.push(code);
            const hit = CATALOG[code];
            await route.fulfill(
                hit
                    ? { json: { product: hit, matched_by: 'product' } }
                    : { status: 404, json: { detail: 'sales.product_not_found' } }
            );
            return;
        }
        if (url.pathname === '/api/inventory/stock') {
            await route.fulfill({
                json: {
                    ok: true,
                    data: {
                        items: STOCK,
                        summary: { sku_count: 2, stock_value: 228, low_count: 0, out_count: 0 },
                    },
                },
            });
            return;
        }
        if (url.pathname === '/api/me') {
            await route.fulfill({ json: { email: 'typed@e2e', role: 'owner', plan: 'pro' } });
            return;
        }
        if (url.pathname === '/api/me/modules') {
            await route.fulfill({
                json: {
                    data: {
                        modules: { pos: { enabled: true }, inventory: { enabled: true } },
                        business_type: 'pos_only',
                        entry: 'pos',
                    },
                },
            });
            return;
        }
        if (url.pathname === '/api/workspace/clients') {
            await route.fulfill({
                json: { clients: [{ id: 1, name: 'Demo Co Ltd', tax_id: '0105567178203' }] },
            });
            return;
        }
        await route.fulfill({ json: { ok: true, data: {} } });
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
    // 等的是「货架真到了」,不是「表格里有行」:第一行可能是加载态占位。行的商品下拉是开窗
    // 那一刻用 invApi.products() 现拼的,货架没到就拼出一个只有「—」的空下拉,后面选谁都选不中
    // (实测:这一步只等 tr 时,rowAt390 约三次一次卡在等批号格露出来)。
    await page.waitForFunction((name) => {
        const body = document.getElementById('inv-tbody'); // 表体本身也是渲染出来的,先判在不在
        return !!body && body.textContent.includes(name);
    }, STOCK[1].name.zh);
    await page.locator('#inv-btn-in').click();
    await page.locator('#inv-in-mask .inv-scan').waitFor();
    return { page, hits };
}

/** 屏上真看得见吗:不是「有这个节点」,是它有面积、没被 display/visibility 藏起来。 */
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
        text: el.innerText.trim(),
    };
}

// 期望文案现场从真词典取:脚本里抄一份中文,词典一改断言就在断自己抄的那份。
const dict = (page, key) => page.evaluate((k) => window.I18N.zh[k], key);

// ① 慢枪打进数量框 → 屏上必须出现「按手输处理」那句,且给得出一条回得来的路
async function typedFeedbackIsOnScreen(browser, origin) {
    const { page, hits } = await openInModal(browser, origin, DESKTOP);
    await gun(page, BOX); // 第一箱正常进单 · 光标停在数量框
    await page.waitForFunction(
        () => document.querySelector('#inv-in-mask-rows [data-k="qty"]').value === '1',
        null,
        { timeout: 8000 }
    );
    const addedText = await page.locator('#inv-in-mask-scan-msg').innerText();
    const focus = await page.evaluate(() => ({
        k: (document.activeElement.dataset || {}).k || '',
        optIn: document.activeElement.hasAttribute('data-enable-barcode'),
    }));

    // 慢枪:同一个框、同一种打法,只是每个字符慢到 90ms
    await gun(page, MILK, SLOW_GUN_MS);
    await page.waitForSelector('#inv-in-mask-scan-msg [data-scan-typed]', { timeout: 8000 });
    const note = await page.evaluate(onScreen, '#inv-in-mask-scan-msg .inv-scan-line.tip');
    const btn = await page.evaluate(onScreen, '#inv-in-mask-scan-msg [data-scan-typed]');
    const dirtyQty = await page.evaluate(
        () => document.querySelector('#inv-in-mask-rows [data-k="qty"]').value
    );
    const typedCopy = await dict(page, 'inv-scan-typed');
    const addedCopy = await dict(page, 'inv-scan-added');
    await shot(page, '01-typed-not-scanned.png');

    // 出路:点一下 = 当条码用 —— 码要真查,数量框要还原成这一串开始之前的样子
    await page.locator('#inv-in-mask-scan-msg [data-scan-typed]').click();
    await page.waitForFunction(
        () => document.querySelectorAll('#inv-in-mask-rows [data-k="product_id"]')[1].value !== '',
        null,
        { timeout: 8000 }
    );
    const rows = await page.evaluate(() =>
        [...document.querySelectorAll('#inv-in-mask-rows [data-row]')].map((r) => ({
            product: r.querySelector('[data-k="product_id"]').value,
            qty: r.querySelector('[data-k="qty"]').value,
        }))
    );
    await shot(page, '02-used-as-barcode.png');
    await page.close();
    return {
        ok:
            focus.k === 'qty' &&
            focus.optIn === true && // 慢枪确实打进了一个声明接枪的框
            hits.join(',') === [BOX, MILK].join(',') && // 慢枪那一发【当时】没查,点了才查
            addedText.includes(addedCopy.replace('{name}', '').trim().slice(0, 4)) &&
            note.found &&
            note.h > 0 &&
            note.display !== 'none' &&
            note.visibility !== 'hidden' &&
            note.opacity !== '0' &&
            note.text.includes(typedCopy) && // 屏上那句话 = 真词典里那一句
            note.text.includes(MILK) && // 带着那串字符,店员才认得出是自己刚才那一枪
            btn.found &&
            btn.h > 0 &&
            dirtyQty === '1' + MILK && // 楔子没动过框:码确实还留在里面(否则还原无从谈起)
            rows.length === 2 &&
            rows[0].qty === '1' && // 点完把那串码从数量框里摘干净了
            rows[1].product === 'p-milk',
        focus,
        hits,
        note,
        btn,
        dirtyQty,
        typedCopy,
        rows,
    };
}

// 弹窗默认开两行空行 → 选择器必须自己钉死是哪一行(:first-child),不靠 .first() 把
// Playwright 的严格模式关掉:关掉之后点偏了也不抛,那种绿正是这批栽过的跟头。
const ROW1 = '#inv-in-mask-rows [data-row]:first-child';

// 选一件批次品:批号/效期格只在这时候露出来,平时 display:none —— 量不到就无从谈起。
async function showBatchCell(page) {
    // 选之前先确认这个下拉里真有这件货 —— 选不中时 selectOption 的报错跟「批次格没露出来」
    // 长得完全不一样,分得开才知道该修哪一头。
    await page.waitForFunction(
        (sel) => [...document.querySelector(sel).options].some((o) => o.value === 'p-milk'),
        `${ROW1} [data-k="product_id"]`
    );
    await page.selectOption(`${ROW1} [data-k="product_id"]`, 'p-milk');
    await page.waitForFunction(
        (sel) => document.querySelector(sel).style.display !== 'none',
        `${ROW1} [data-batchcell]`
    );
}

// ② 390 宽:批号/效期不许被挤成两个字符的窄条
async function rowFitsOnAPhone(browser, origin) {
    const { page } = await openInModal(browser, origin, PHONE);
    await showBatchCell(page);
    const geo = await page.evaluate((rowSel) => {
        const row = document.querySelector(rowSel);
        const at = (sel) => Math.round(row.querySelector(sel).getBoundingClientRect().width);
        const body = document.querySelector('#inv-in-mask .inv-modal-body');
        return {
            product: at('[data-k="product_id"]'),
            qty: at('[data-k="qty"]'),
            batch: at('[data-k="batch_no"]'),
            expiry: at('[data-k="expiry_date"]'),
            rowWidth: Math.round(row.getBoundingClientRect().width),
            bodyWidth: Math.round(body.getBoundingClientRect().width),
            // 弹窗里有没有东西顶出屏外。只量弹窗自己 —— 这一页在打开弹窗【之前】就已经横向
            // 溢出(库存表 479 > 390,是存量问题,记在交接里),拿整页当判据就是在验别人的债。
            spill: [...document.querySelectorAll('#inv-in-mask *')].filter(
                (el) => el.getBoundingClientRect().right > document.documentElement.clientWidth + 1
            ).length,
        };
    }, ROW1);
    // 批号真填得进去吗:打一串真批号,看框里显示区能不能装下它(scrollWidth 超了就是看不全)
    await page.locator(`${ROW1} [data-k="batch_no"]`).click();
    await page.keyboard.type('LOT-B240301', { delay: 200 }); // 200ms/字符 = 人手,别被当成枪
    const lot = await page.evaluate((sel) => {
        const el = document.querySelector(sel);
        return { value: el.value, scrollW: el.scrollWidth, clientW: el.clientWidth };
    }, `${ROW1} [data-k="batch_no"]`);
    await shot(page, '03-row-at-390.png');
    await page.close();
    return {
        ok:
            geo.batch >= 100 &&
            geo.expiry >= 100 &&
            geo.product >= 100 &&
            geo.qty >= 40 &&
            geo.spill === 0 &&
            geo.rowWidth <= geo.bodyWidth &&
            lot.value === 'LOT-B240301' && // 人手打的批号没被楔子当成扫码抢走
            lot.scrollW <= lot.clientW + 1, // 整串批号在框里看得全
        geo,
        lot,
    };
}

// ③ 桌面那一档也得量:批号/效期原先只分到 1fr,640px 的弹窗里两个框各 85px,
//    效期是原生 date 控件,yyyy-mm-dd 显不全 —— 这一条是窄屏那条的另一半,不是同一件事。
async function rowOnDesktop(browser, origin) {
    const { page } = await openInModal(browser, origin, DESKTOP);
    await showBatchCell(page);
    const geo = await page.evaluate((rowSel) => {
        const row = document.querySelector(rowSel);
        const at = (sel) => Math.round(row.querySelector(sel).getBoundingClientRect().width);
        const date = row.querySelector('[data-k="expiry_date"]');
        return {
            product: at('[data-k="product_id"]'),
            batch: at('[data-k="batch_no"]'),
            expiry: at('[data-k="expiry_date"]'),
            // 原生 date 控件把 yyyy/mm/dd + 日历钮画满就是它的 scrollWidth,装不下就是显不全
            dateFits: date.scrollWidth <= date.clientWidth + 1,
            rows: document.querySelectorAll('#inv-in-mask-rows [data-row]').length,
        };
    }, ROW1);
    await shot(page, '04-row-on-desktop.png');
    await page.close();
    return {
        ok: geo.batch >= 100 && geo.expiry >= 100 && geo.product >= 140 && geo.dateFits,
        geo,
    };
}

(async () => {
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch();
    const failed = await runCases(
        [
            ['typedFeedback', typedFeedbackIsOnScreen],
            ['rowAt390', rowFitsOnAPhone],
            ['rowOnDesktop', rowOnDesktop],
        ],
        (fn) => fn(browser, origin),
        path.join(SHOTS, 'report.json')
    );
    await browser.close();
    server.close();
    process.exit(failed ? 1 : 0);
})();
