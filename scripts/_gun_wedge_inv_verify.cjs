/*
 * scripts/_gun_wedge_inv_verify.cjs · 入库弹窗的条码枪真浏览器验收
 *
 * 只用真键盘(keyboard.type + press('Enter')),不用 fill()。扫之前记 activeElement:第一枪
 * 从按钮上打进去,第二枪是从「数量」框里打进去的(那个框带 data-enable-barcode 显式接枪),
 * 两种前提不写下来就说不清哪一绿是怎么来的。
 *
 * 真的东西:home.html + static/dist/main.js + static/dist/pre.js(常驻楔子在 pre.js 里),
 * 文案取真 static/i18n-data.js。桩只有 /api/**(lookup 由测控制并计数)与账套切换器
 * getActiveWorkspaceClientId —— 两者都不在扫码这条链上。
 *
 * 用法(仓库根目录):node scripts/_gun_wedge_inv_verify.cjs [截图目录]
 * 退出码 0 = 全过。截图默认落 tests/e2e/_artifacts/pos_barcode_scan/。
 */
const path = require('path');
const { chromium } = require('@playwright/test');
const {
    ROOT,
    DESKTOP,
    BOX,
    GHOST,
    serve,
    notInField,
    gun,
    shotter,
    runCases,
} = require('./_gun_wedge_lib.cjs');

const SHOTS = path.resolve(
    process.argv[2] || path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan')
);
const shot = shotter(SHOTS);

const INV_CATALOG = {
    [BOX]: { id: 'p-cola', name_th: 'โค้ก 325ml', name_en: 'Coke 325ml', name_zh: '可乐 325ml' },
};
const INV_STOCK = [
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

async function routeInv(page) {
    const hits = [];
    await page.route('**/api/**', async (route) => {
        const url = new URL(route.request().url());
        if (url.pathname === '/api/sales/products/lookup') {
            const code = url.searchParams.get('barcode');
            hits.push(code);
            const hit = INV_CATALOG[code];
            await route.fulfill(
                hit
                    ? { json: { product: hit } }
                    : { status: 404, json: { detail: 'sales.product_not_found' } }
            );
            return;
        }
        if (url.pathname === '/api/inventory/stock') {
            await route.fulfill({
                json: {
                    ok: true,
                    data: {
                        items: INV_STOCK,
                        summary: { sku_count: 1, stock_value: 114, low_count: 0, out_count: 0 },
                    },
                },
            });
            return;
        }
        if (url.pathname === '/api/me') {
            await route.fulfill({ json: { email: 'gun@e2e', role: 'owner', plan: 'pro' } });
            return;
        }
        await route.fulfill({ json: { ok: true, data: {} } });
    });
    return hits;
}

async function openInvPage(browser, origin) {
    const page = await browser.newPage({ viewport: DESKTOP });
    await page.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'gun-verify');
        localStorage.setItem('mrpilot_lang', 'zh'); // 断言对着真 zh 字典 · 截图给人眼看
    });
    const hits = await routeInv(page);
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
    await page.locator('#inv-tbody tr').first().waitFor();
    return { page, hits };
}

async function openInModal(page) {
    await page.locator('#inv-btn-in').click(); // 真点真按钮
    await page.locator('#inv-in-mask .inv-scan').waitFor();
}

// closeModal 只摘 show + 清 innerHTML,mask 本体留在 DOM 里 → 判据看 .inv-modal 还在不在
async function closeInModal(page) {
    await page.locator('#inv-in-mask .inv-modal-foot [data-inv-close]').click();
    await page.waitForFunction(() => !document.querySelector('#inv-in-mask .inv-modal'));
}

function invRows() {
    return [...document.querySelectorAll('#inv-in-mask-rows [data-row]')].map((row) => {
        const sel = row.querySelector('[data-k="product_id"]');
        return {
            product: sel.value,
            label: (sel.selectedOptions[0] || {}).textContent || '',
            qty: row.querySelector('[data-k="qty"]').value,
        };
    });
}

// ⑧ 弹窗开着扫枪 = 真加一行且商品选中 · ⑨ 同码连扫 = qty 2 不是两行
async function invGun(browser, origin) {
    const { page, hits } = await openInvPage(browser, origin);
    await openInModal(page);
    const barVisible = await page.locator('#inv-in-mask .inv-scan').isVisible();
    const focus1 = await gun(page, BOX);
    await page.waitForFunction(
        () => document.querySelector('#inv-in-mask-rows [data-k="product_id"]').value !== '',
        null,
        { timeout: 8000 }
    );
    const first = await page.evaluate(invRows);
    const focusAfter = await page.evaluate(() => ({
        k: (document.activeElement.dataset || {}).k || '',
        tag: document.activeElement.tagName,
        optIn: document.activeElement.hasAttribute('data-enable-barcode'),
    }));
    const msg1 = await page.locator('#inv-in-mask-scan-msg').innerText();
    await shot(page, '11-inv-gun-row-added.png');

    // 第二枪:此刻焦点在数量框里(带 data-enable-barcode 显式接枪)→ 该 +1 且码不能留在框里
    const focus2 = await gun(page, BOX);
    await page.waitForFunction(
        () => document.querySelector('#inv-in-mask-rows [data-k="qty"]').value === '2',
        null,
        { timeout: 8000 }
    );
    const second = await page.evaluate(invRows);
    await shot(page, '12-inv-gun-same-code-qty2.png');
    await page.close();
    return {
        ok:
            barVisible &&
            notInField(focus1) &&
            first.length === 2 && // 弹窗默认两行空行:第一枪填掉第一行,第二行仍空
            first[0].product === 'p-cola' &&
            first[0].label.includes('可乐') &&
            first[0].qty === '1' &&
            focusAfter.k === 'qty' &&
            focusAfter.optIn === true &&
            focus2.tag === 'INPUT' && // 第二枪确实是从输入框里打进去的
            focus2.id === '' &&
            second.length === 2 && // 没长出第三行
            second[0].qty === '2' &&
            second[0].product === 'p-cola' &&
            !second[0].qty.includes(BOX) && // 数量框里没留下一串条码
            second[1].product === '' &&
            hits.join(',') === [BOX, BOX].join(','),
        barVisible,
        focus1,
        first,
        focusAfter,
        msg1,
        focus2,
        second,
        hits,
    };
}

// ⑩ exclusive 独占:弹窗开着时,底下页面的订阅者收不到;弹窗关了才轮到它
async function invExclusive(browser, origin) {
    const { page } = await openInvPage(browser, origin);
    // 探针 = 「底下那一页的订阅者」。主 SPA 目前只有入库弹窗一个真订阅者,独占的另一半
    // 只能靠一个非独占订阅者照出来 —— 用真 window.PearnlyScanWedge,不替换实现。
    await page.evaluate(() => {
        window.__probe = [];
        window.__off = window.PearnlyScanWedge.register((code) => window.__probe.push(code));
    });
    const before = await page.evaluate(() => window.PearnlyScanWedge.subscriberCount());
    await openInModal(page);
    const during = await page.evaluate(() => window.PearnlyScanWedge.subscriberCount());
    await gun(page, BOX);
    await page.waitForFunction(
        () => document.querySelector('#inv-in-mask-rows [data-k="qty"]').value === '1',
        null,
        { timeout: 8000 }
    );
    const probeDuring = await page.evaluate(() => window.__probe.slice());
    await shot(page, '13-inv-exclusive-modal-open.png');

    // 真点「取消」关弹窗 → 独占撤掉 → 同一枪该落到探针上
    await closeInModal(page);
    const after = await page.evaluate(() => window.PearnlyScanWedge.subscriberCount());
    await gun(page, BOX);
    await page.waitForFunction(() => window.__probe.length > 0, null, { timeout: 5000 });
    const probeAfter = await page.evaluate(() => window.__probe.slice());
    await page.close();
    return {
        ok:
            before === 1 &&
            during === 2 &&
            probeDuring.length === 0 && // 弹窗开着时探针一个码都没收到
            after === 1 &&
            probeAfter.join(',') === BOX,
        before,
        during,
        probeDuring,
        after,
        probeAfter,
    };
}

// ⑪ 弹窗关掉后:楦子该整个撤掉,枪扫任何码都不该再打扰底下的库存页
async function invDetached(browser, origin) {
    const { page, hits } = await openInvPage(browser, origin);
    const beforeOpen = await page.evaluate(() => window.PearnlyScanWedge.subscriberCount());
    await openInModal(page);
    await gun(page, BOX);
    await page.waitForFunction(
        () => document.querySelector('#inv-in-mask-rows [data-k="qty"]').value === '1',
        null,
        { timeout: 8000 }
    );
    const hitsInModal = hits.length;
    await closeInModal(page);
    const focus = await gun(page, BOX);
    await page.waitForTimeout(700);
    const state = await page.evaluate(() => ({
        subs: window.PearnlyScanWedge.subscriberCount(),
        rows: document.querySelectorAll('#inv-tbody tr').length,
        modal: !!document.querySelector('#inv-in-mask .inv-modal'),
    }));
    await shot(page, '14-inv-closed-wedge-detached.png');
    await page.close();
    return {
        ok:
            beforeOpen === 0 &&
            hitsInModal === 1 &&
            notInField(focus) &&
            state.subs === 0 &&
            state.modal === false &&
            hits.length === 1, // 关了之后那一枪没再发出任何取件请求
        beforeOpen,
        hitsInModal,
        focus,
        state,
        hits,
    };
}

// ⑫ 未命中那条出路:枪扫一个库里没有的码 → 码要显在屏上 + 「去建这个商品」真的能点动
async function invNotFoundCreate(browser, origin) {
    const { page } = await openInvPage(browser, origin);
    await openInModal(page);
    await gun(page, GHOST);
    await page.locator('#inv-in-mask-scan-msg [data-scan-create]').waitFor();
    const card = await page.evaluate(() => {
        const msg = document.getElementById('inv-in-mask-scan-msg');
        const btn = msg.querySelector('[data-scan-create]');
        return {
            text: msg.innerText,
            tone: msg.className,
            code: btn.dataset.scanCreate,
            btnH: btn.getBoundingClientRect().height,
            bridge: typeof window.openSalesProductWithBarcode,
        };
    });
    await shot(page, '15-inv-notfound-create.png');
    await page.locator('#inv-in-mask-scan-msg [data-scan-create]').click();
    const afterClick = await page.evaluate(() => {
        const msg = document.getElementById('inv-in-mask-scan-msg');
        return {
            text: msg.innerText,
            productForm: !!document.getElementById('sx-pf-barcode'),
            barcodeValue: (document.getElementById('sx-pf-barcode') || {}).value || null,
        };
    });
    await shot(page, '16-inv-notfound-create-clicked.png');
    await page.close();
    return {
        // 断言只锁「说了什么就该做到什么」:码显在屏上、按钮点得动、点完不假装成功。
        ok:
            card.code === GHOST &&
            card.text.includes(GHOST) &&
            card.btnH >= 24 &&
            afterClick.text.includes(GHOST),
        card,
        afterClick,
    };
}

(async () => {
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch();
    const failed = await runCases(
        [
            ['invGun', invGun],
            ['invExclusive', invExclusive],
            ['invDetached', invDetached],
            ['invNotFoundCreate', invNotFoundCreate],
        ],
        (fn) => fn(browser, origin),
        path.join(SHOTS, 'report-inv.json')
    );
    await browser.close();
    server.close();
    process.exit(failed ? 1 : 0);
})().catch((e) => {
    console.error('INV GUN VERIFY CRASH', e);
    process.exit(2);
});
