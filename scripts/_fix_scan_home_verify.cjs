/*
 * scripts/_fix_scan_home_verify.cjs · 主站 SPA 扫码「审查揪出的错」的真浏览器复验
 *
 * 只验修掉的那几条行为:
 *   P0-B 手打条码  按五种断法分段慢打 13 位(尾段 / 中段 / 官方印刷分组)→ 框里每一步都
 *                  必须是"到目前为止打过的全部字符",查重问出去的也只能是框里那串
 *                  (旧行为把够 8 位又不是前缀的那一段当成枪扫的整串写回框里,最后只剩
 *                   半截码,存下去 POS 永远扫不出这件货,后台却一切正常);
 *   P1-D 桥        入库未命中卡点「用这个码建商品」→ 建品表单叠在入库弹窗【之上】开出来、
 *                  码已填好、半张入库单一行不丢(旧行为是死胡同);
 *   P1-G 批次分叉  批次品同码连扫两次 = 两行(各填各的批号效期);非批次品同码连扫 = 一行 qty 2。
 *
 * 真的东西:home.html + dist/main.js + dist/home.css + dist/pre.js 全是本仓真产物;键盘是
 * page.keyboard 真按键(fill() 绕过 keydown,楔子一个键都收不到,那种绿是假的)。桩只有
 * /api/** 的回包与账套切换器。文案期望值现场从页面里的真 window.I18N 取,一个字都不注入。
 *
 * 跑法(仓库根目录):node scripts/_fix_scan_home_verify.cjs [用例名]
 */
const path = require('path');
const { chromium } = require('@playwright/test');
const { ROOT, DESKTOP, serve, gun, shotter, runCases } = require('./_gun_wedge_lib.cjs');

const ONLY = process.argv[2] || '';
const SHOTS = path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/fix');
const shot = shotter(SHOTS);

const COLA = '8850999320014'; // 非批次品
const MILK = '4901234567894'; // 批次品
const GHOST = '9999999999999'; // 库里没有
// 手打分段:每段内部是正常打字速度(段内攒得起来),段间停 400ms(远超楔子 150ms 的收尾线)。
// 断在哪由人在哪停顿决定,不由条码的印刷分组决定。只验官方分组 8/850999/320014 会全绿 ——
// 它每一段都恰好是框里那串的前缀,老规则正好盖住;店里真出事的是下面那几种尾段/中段。
const TYPED_SPLITS = [
    ['8850', '999320014'], // 尾段 9 位
    ['885', '0999320014'], // 尾段 10 位
    ['88509', '99320014'], // 尾段 8 位 · 正好卡在零售条码最短长度上
    ['88', '50999320', '014'], // 中段 8 位 · 既不是前缀也不是后缀
    ['8', '850999', '320014'], // 官方印刷分组 · 防回归
];

const P_COLA = {
    id: 'p-cola',
    name_th: 'โค้ก 325ml',
    name_en: 'Coke 325ml',
    name_zh: '可乐 325ml',
    track_batch: false,
};
const P_MILK = {
    id: 'p-milk',
    name_th: 'นมสด 1L',
    name_en: 'Milk 1L',
    name_zh: '鲜奶 1L',
    track_batch: true,
};
// 一件"只填了名字就建档"的货(unit_price 为 null)+ 一件正常有价的货
const PRICED = [
    { id: 'p-new', name_th: 'น้ำเปล่า', unit_price: null, vat_applicable: true },
    { id: 'p-cola', name_th: 'โค้ก 325ml', unit_price: 15, vat_applicable: true },
];

const LOOKUP = {
    [COLA]: { product: P_COLA, matched_by: 'product', matched_unit: 'ขวด' },
    [MILK]: { product: P_MILK, matched_by: 'product', matched_unit: 'กล่อง' },
};

const STOCK = [
    {
        product_id: 'p-cola',
        name: { th: 'โค้ก 325ml', en: 'Coke 325ml', zh: '可乐 325ml' },
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
        name: { th: 'นมสด 1L', en: 'Milk 1L', zh: '鲜奶 1L' },
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

const INIT = () => localStorage.setItem('mrpilot_token', 'fix-verify');

// asked = 查重/查商品实际问出去的那些码。屏上的值对了不算数,发出去的那份才是要存的东西。
async function stubApi(page, asked, posted) {
    await page.route('https://cdnjs.cloudflare.com/**', (r) => r.abort());
    await page.route('**/api/**', async (route) => {
        const req = route.request();
        const url = new URL(req.url());
        if (url.pathname === '/api/sales/products/lookup') {
            const code = url.searchParams.get('barcode');
            if (asked) asked.push(code);
            const hit = LOOKUP[code];
            if (!hit)
                return route.fulfill({ status: 404, json: { detail: 'sales.product_not_found' } });
            return route.fulfill({ json: hit });
        }
        if (url.pathname === '/api/inventory/in') {
            if (posted) posted.push(req.postDataJSON());
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
        if (url.pathname === '/api/sales/products')
            return route.fulfill({ json: { products: [] } });
        if (url.pathname === '/api/me') {
            return route.fulfill({ json: { email: 'fix@e2e', role: 'owner', plan: 'pro' } });
        }
        return route.fulfill({ json: { ok: true, data: {}, items: [] } });
    });
}

async function boot(browser, asked, posted, origin) {
    const page = await browser.newPage({ viewport: DESKTOP });
    await page.addInitScript(INIT);
    await stubApi(page, asked, posted);
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

async function openInModal(page) {
    await page.evaluate(() => {
        document.querySelectorAll('.page').forEach((p) => p.classList.remove('active'));
        document.getElementById('page-inventory').classList.add('active');
        window.loadInventoryPage();
    });
    await page.locator('#inv-tbody tr').first().waitFor();
    await page.locator('#inv-btn-in').click(); // 真点真按钮
    await page.locator('#inv-in-mask .inv-scan').waitFor();
}

const rowSnapshot = () =>
    Array.from(document.querySelectorAll('#inv-in-mask-rows [data-row]')).map((row) => ({
        product: row.querySelector('[data-k="product_id"]').value,
        qty: row.querySelector('[data-k="qty"]').value,
        batchCellShown: getComputedStyle(row.querySelector('[data-batchcell]')).display !== 'none',
    }));

// 旧行为下有些等待本来就等不到(那正是反证要证的),超时该报一条干净的 FAIL 而不是 CRASH。
async function waitQuiet(page, fn, timeout = 8000) {
    try {
        await page.waitForFunction(fn, null, { timeout });
    } catch (_) {
        /* 交给断言去报 */
    }
}

// ── P0-B · 分段慢打 13 位,框里必须是完整的那一串 ────────────────────────────
async function openBlankProductForm(page) {
    await page.click('#sx-p-add');
    await page.waitForSelector('#sx-pf-barcode', { timeout: 10000 });
    await page.waitForFunction(() => {
        const box = document.querySelector('#sales-prod-mask .modal');
        return !!box && getComputedStyle(box).opacity === '1';
    });
    await page.click('#sx-pf-barcode');
    return page.evaluate(() => document.activeElement.id);
}

async function typeOneSplit(page, segs, asked, copy) {
    const focused = await openBlankProductForm(page);
    asked.length = 0;
    // 真按键分段慢打:段内 60ms/字符(楔子攒得起来),段间 400ms(远超它 150ms 的收尾线)。
    // 用 fill() 就不会有 keydown,楔子收不到 —— 那正是这条 bug 的发生条件,绕过去等于没验。
    const seen = [];
    for (const seg of segs) {
        await page.keyboard.type(seg, { delay: 60 });
        await page.waitForTimeout(400);
        seen.push(await page.inputValue('#sx-pf-barcode'));
    }
    await page.waitForTimeout(900); // 让 400ms 防抖的那次查重跑完,才看得出问出去的是哪串码
    const value = await page.inputValue('#sx-pf-barcode');
    const state = await page.evaluate(() => {
        const el = document.getElementById('sx-pf-bc-state');
        return { text: el.textContent.trim(), visible: el.getBoundingClientRect().height > 0 };
    });
    await shot(page, `fix-b-typed-${segs.join('-')}.png`);
    await page.click('#sx-p-cancel');
    // 每一段打完,框里都得是"到目前为止打过的全部字符";查重问出去的也只能是框里那串
    // (旧行为把尾段/中段整框盖掉,于是问出去的是半截码,状态行绿字说"没人用")。
    const grew = segs.map((_, i) => segs.slice(0, i + 1).join(''));
    return {
        split: segs.join('/'),
        ok:
            focused === 'sx-pf-barcode' &&
            value === COLA &&
            seen.join('|') === grew.join('|') &&
            asked.length > 0 &&
            asked.every((a) => COLA.startsWith(a)) &&
            asked[asked.length - 1] === COLA &&
            state.visible &&
            state.text.startsWith(copy),
        focused,
        seen,
        want: grew,
        value,
        asked: asked.slice(),
        state,
    };
}

// ── P0-① · 没设价的货在后台看得出来,且表单说清留空意味着什么 ──────────────
async function noPriceIsVisible(browser, origin) {
    const page = await boot(browser, [], null, origin);
    // 后端 unit_price 可空:没设过价回 null(routes/products_routes._out)
    await page.route('**/api/sales/products?*', (r) => r.fulfill({ json: { products: PRICED } }));
    await page.route('**/api/sales/products', (r) => r.fulfill({ json: { products: PRICED } }));
    await page.evaluate(() => window.routeTo('sales-products'));
    await page.waitForSelector('#sx-p-tbody tr', { timeout: 20000 });
    const want = await page.evaluate(() => ({
        noprice: window.I18N[window._currentLang]['sx-p-noprice'],
        hint: window.I18N[window._currentLang]['sx-p-f-price-hint'],
    }));
    const cells = await page.$$eval('#sx-p-tbody tr', (rows) =>
        rows.map((r) => r.children[4].textContent.trim())
    );
    await shot(page, 'fix-a-noprice-column.png');
    await openBlankProductForm(page); // 等淡入跑完再取证,不然截到的是半透明的过渡态
    const hint = await page.evaluate(() => {
        const el = document.getElementById('sx-pf-price').nextElementSibling;
        return { text: el.textContent.trim(), h: el.getBoundingClientRect().height };
    });
    await shot(page, 'fix-a-price-hint.png');
    await page.close();
    return {
        // 老行为:fmtMoney(null) → "0.00",后台列表把「没设价」画成一个真金额
        ok:
            cells[0] === want.noprice &&
            cells[1] === '15.00' &&
            hint.text === want.hint &&
            hint.h > 0,
        cells,
        hint,
        want,
    };
}

async function typedBarcodeKept(browser, origin) {
    const asked = [];
    const page = await boot(browser, asked, null, origin);
    await page.evaluate(() => window.routeTo('sales-products'));
    await page.waitForSelector('#sx-p-add', { timeout: 20000 });
    // 查重落在完整那一串上才算数:桩里 COLA 是别人的码,状态行必须是撞码那一句。
    // 旧行为查的是半截码(桩里没有)→ 这里会变成「这个码没人用」的绿字,放行撞码。
    const copy = await page.evaluate(
        (name) => window.I18N[window._currentLang]['sx-p-bc-dup'].replace('{name}', name),
        P_COLA.name_th
    );
    const runs = [];
    for (const segs of TYPED_SPLITS) runs.push(await typeOneSplit(page, segs, asked, copy));
    await page.close();
    return { ok: runs.every((r) => r.ok), runs, wantState: copy };
}

// ── P1-D · 未命中 →「用这个码建商品」→ 建品表单叠在入库弹窗之上 ───────────────
async function createOverlay(browser, origin) {
    const page = await boot(browser, [], null, origin);
    await openInModal(page);
    await gun(page, COLA); // 先扫进一件:叠上去之后它必须还在
    await waitQuiet(
        page,
        () => document.querySelector('#inv-in-mask-rows [data-k="product_id"]').value === 'p-cola'
    );
    await gun(page, GHOST);
    await page.locator('#inv-in-mask-scan-msg [data-scan-create]').waitFor({ timeout: 8000 });
    await page.locator('#inv-in-mask-scan-msg [data-scan-create]').click();
    await waitQuiet(page, () => {
        const box = document.getElementById('sales-prod-mask');
        return (
            !!document.getElementById('sx-pf-barcode') &&
            !!box &&
            getComputedStyle(box).opacity === '1'
        );
    });
    const state = await page.evaluate(() => {
        const form = document.getElementById('sx-pf-barcode');
        const box = document.getElementById('sales-prod-mask');
        const inv = document.getElementById('inv-in-mask');
        const zOf = (el) => (el ? Number(getComputedStyle(el).zIndex) || 0 : 0);
        const rows = document.querySelectorAll('#inv-in-mask-rows [data-row]');
        const first = rows[0] && rows[0].querySelector('[data-k="product_id"]');
        const invBox = inv ? inv.getBoundingClientRect() : { height: 0 };
        const page = document.getElementById('page-inventory');
        return {
            formVisible:
                !!form &&
                !!box &&
                getComputedStyle(box).display !== 'none' &&
                form.getBoundingClientRect().height > 0,
            barcode: form ? form.value : null,
            invShown:
                !!inv && inv.classList.contains('show') && getComputedStyle(inv).display !== 'none',
            invPainted: invBox.height > 0,
            // 「叠上去」不只是弹窗还在:底下那一屏也必须还是库存页。跳页去商品数据再开表单
            // 时弹窗照样浮着(它不随路由拆),但店员一关表单就落在别的屏上,半张入库单等于没了。
            invPageActive: !!page && page.classList.contains('active'),
            invRows: rows.length,
            invFirstProduct: first ? first.value : '',
            aboveInv: zOf(box) > zOf(inv),
            zForm: zOf(box),
            zInv: zOf(inv),
        };
    });
    await shot(page, 'fix-d-create-form-over-inventory.png');
    await page.close();
    return {
        ok:
            state.formVisible &&
            state.barcode === GHOST &&
            state.invShown &&
            state.invPainted &&
            state.invPageActive &&
            state.invRows === 2 &&
            state.invFirstProduct === 'p-cola' &&
            state.aboveInv,
        state,
    };
}

// ── P1-G · 批次品同码连扫 = 两行;非批次品同码连扫 = 一行 qty 2 ───────────────
async function batchFork(browser, origin) {
    const posted = [];
    const page = await boot(browser, [], posted, origin);
    await openInModal(page);

    await gun(page, MILK);
    await waitQuiet(
        page,
        () => document.querySelector('#inv-in-mask-rows [data-k="product_id"]').value === 'p-milk'
    );
    await gun(page, MILK);
    await waitQuiet(page, () => {
        const rows = document.querySelectorAll('#inv-in-mask-rows [data-row]');
        return rows.length > 1 && rows[1].querySelector('[data-k="product_id"]').value === 'p-milk';
    });
    // 另起一行必须当场说清为什么,期望值取页面里的真词条
    const splitMsg = await page.locator('#inv-in-mask-scan-msg').innerText();
    const wantSplit = await page.evaluate(
        (name) => window.I18N[window._currentLang]['inv-scan-batch-row'].replace('{name}', name),
        P_MILK.name_th
    );
    const batchRows = await page.evaluate(rowSnapshot);
    // 各填各的批号/效期:填得进去本身就是「第二箱有地方写自己的效期」
    const filled = [];
    for (const [i, no, exp] of [
        [0, 'A-01', '2026-08-10'],
        [1, 'B-02', '2026-11-02'],
    ]) {
        const row = page.locator('#inv-in-mask-rows [data-row]').nth(i);
        if (await row.locator('[data-batchcell]').isVisible()) {
            await row.locator('[data-k="batch_no"]').fill(no);
            await row.locator('[data-k="expiry_date"]').fill(exp);
            filled.push(true);
        } else filled.push(false);
    }
    await shot(page, 'fix-g1-batch-two-rows.png');

    // 非批次品:同一个码连扫两次只该是一行 qty 2
    await page.locator('#inv-in-mask-rows [data-row]').nth(0).locator('[data-k="batch_no"]').blur();
    await page.evaluate(() => document.getElementById('inv-in-mask-scan-cam').focus());
    await gun(page, COLA);
    await waitQuiet(page, () => {
        const rows = document.querySelectorAll('#inv-in-mask-rows [data-row]');
        return rows.length > 2 && rows[2].querySelector('[data-k="product_id"]').value === 'p-cola';
    });
    await gun(page, COLA);
    await waitQuiet(page, () => {
        const rows = document.querySelectorAll('#inv-in-mask-rows [data-row]');
        return rows.length > 2 && rows[2].querySelector('[data-k="qty"]').value === '2';
    });
    const bumpMsg = await page.locator('#inv-in-mask-scan-msg').innerText();
    const wantBump = await page.evaluate(
        (name) => window.I18N[window._currentLang]['inv-scan-bumped'].replace('{name}', name),
        P_COLA.name_th
    );
    const allRows = await page.evaluate(rowSnapshot);
    await shot(page, 'fix-g2-nonbatch-one-row-qty2.png');

    await page.locator('#inv-in-mask-submit').click();
    await waitQuiet(page, () => !document.getElementById('inv-in-mask').classList.contains('show'));
    await page.close();

    const lines = (posted[0] && posted[0].lines) || [];
    const milk = allRows.filter((r) => r.product === 'p-milk');
    const cola = allRows.filter((r) => r.product === 'p-cola');
    const milkLines = lines.filter((l) => l.product_id === 'p-milk');
    const colaLines = lines.filter((l) => l.product_id === 'p-cola');
    return {
        ok:
            batchRows.filter((r) => r.product === 'p-milk').length === 2 &&
            milk.length === 2 &&
            milk.every((r) => r.qty === '1' && r.batchCellShown) &&
            filled.join('|') === 'true|true' &&
            splitMsg === wantSplit &&
            cola.length === 1 &&
            cola[0].qty === '2' &&
            cola[0].batchCellShown === false &&
            bumpMsg === wantBump &&
            // 屏上两行也可能提交成一行:判据落在真发出去的载荷上
            milkLines.length === 2 &&
            milkLines[0].batch_no === 'A-01' &&
            milkLines[0].expiry_date === '2026-08-10' &&
            milkLines[1].batch_no === 'B-02' &&
            milkLines[1].expiry_date === '2026-11-02' &&
            colaLines.length === 1 &&
            Number(colaLines[0].qty) === 2,
        splitMsg,
        wantSplit,
        bumpMsg,
        wantBump,
        filled,
        allRows,
        lines,
    };
}

const CASES = [
    ['noPriceIsVisible', noPriceIsVisible],
    ['typedBarcodeKept', typedBarcodeKept],
    ['createOverlay', createOverlay],
    ['batchFork', batchFork],
];

(async () => {
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch();
    const failed = await runCases(
        CASES.filter(([name]) => !ONLY || name === ONLY),
        (fn) => fn(browser, origin),
        path.join(SHOTS, 'report-home-fix.json')
    );
    await browser.close();
    server.close();
    process.exit(failed ? 1 : 0);
})().catch((e) => {
    console.error('HOME FIX VERIFY CRASH', e);
    process.exit(2);
});
