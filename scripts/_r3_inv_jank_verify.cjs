/*
 * scripts/_r3_inv_jank_verify.cjs · 第三轮对抗 · 入库批号框:枪扫被主线程一次长任务判成「人在打字」
 *
 * src/home/inventory-scan.ts::onWedge()
 *     if (snap && snap.maxGap > gunGapMs() && !machine) return;
 * gunGapMs() 向楔子要 GUN_MAX_GAP_MS = 50。snap.maxGap 是【keydown 在主线程被处理的时刻差】,
 * 不是枪打字符的物理间隔。批号框 type != 'date' → machine 恒 false,速度这一条是唯一的门。
 * 于是这一串真枪扫在中间卡一下就走进 return:
 *   · 不加行(这箱货没进收货单)
 *   · 不查码(后端一次都没被问)
 *   · 屏上一个字都不出(既不是失败清单,也不是「正在查」)
 *   · 那串码原样留在店员填的批号里
 *
 * 对照组:同一发枪不卡 → 正常还原批号 + 加行。
 *
 * 跑法(仓库根目录):node scripts/_r3_inv_jank_verify.cjs
 */
const path = require('path');
const { chromium } = require('@playwright/test');
const { ROOT, DESKTOP, serve, shotter, runCases } = require('./_gun_wedge_lib.cjs');

const SHOTS = path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/round3');
const shot = shotter(SHOTS);

const MILK = '4901234567894'; // 批次品:扫它要加一行 + 露批号格
const STALL_MS = 120;

const P_MILK = { id: 'p-milk', name_th: 'นมสด 1L', name_zh: '鲜奶 1L', track_batch: true };
const STOCK = [
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

const INIT = () => localStorage.setItem('mrpilot_token', 'r3-verify');

async function boot(browser, bag, origin) {
    const page = await browser.newPage({ viewport: DESKTOP });
    await page.addInitScript(INIT);
    await page.route('https://cdnjs.cloudflare.com/**', (r) => r.abort());
    await page.route('**/api/**', async (route) => {
        const url = new URL(route.request().url());
        if (url.pathname === '/api/sales/products/lookup') {
            const code = url.searchParams.get('barcode');
            bag.asked.push(code);
            if (code === MILK)
                return route.fulfill({
                    json: { product: P_MILK, matched_by: 'product', matched_unit: 'กล่อง' },
                });
            return route.fulfill({ status: 404, json: { detail: 'sales.product_not_found' } });
        }
        if (url.pathname === '/api/inventory/stock')
            return route.fulfill({
                json: {
                    ok: true,
                    data: {
                        items: STOCK,
                        summary: { sku_count: 1, stock_value: 168, low_count: 0, out_count: 0 },
                    },
                },
            });
        if (url.pathname === '/api/me')
            return route.fulfill({ json: { email: 'r3@e2e', role: 'owner', plan: 'pro' } });
        return route.fulfill({ json: { ok: true, data: {}, items: [] } });
    });
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
    await page.evaluate(() => {
        document.querySelectorAll('.page').forEach((p) => p.classList.remove('active'));
        document.getElementById('page-inventory').classList.add('active');
        window.loadInventoryPage();
    });
    await page.locator('#inv-tbody tr').first().waitFor({ timeout: 20000 });
    await page.locator('#inv-btn-in').click();
    await page.locator('#inv-in-mask .inv-scan').waitFor({ timeout: 10000 });
    return page;
}

// 先扫一件把批次行做出来,再把光标放进那一行的批号框、填一个真批号。
async function primeBatchRow(page) {
    const input = page.locator('#inv-in-mask-scan-code');
    await input.click();
    await page.keyboard.type(MILK, { delay: 6 });
    await page.keyboard.press('Enter');
    await page.waitForTimeout(900);
    const cell = page.locator('#inv-in-mask [data-k="batch_no"]').first();
    await cell.click();
    await page.keyboard.type('L2027', { delay: 200 });
    await page.waitForTimeout(400);
    return await cell.inputValue();
}

async function armStall(page, nth, ms) {
    await page.evaluate(
        ([n, blockMs]) => {
            window.__n = 0;
            window.__stalled = null;
            window.__stallProbe = () => {
                window.__n += 1;
                if (window.__n !== n) return;
                const t0 = performance.now();
                while (performance.now() - t0 < blockMs) {
                    /* 长任务 */
                }
                window.__stalled = Math.round(performance.now() - t0);
            };
            document.addEventListener('keydown', window.__stallProbe, true);
        },
        [nth, ms]
    );
}

async function snapshot(page) {
    return page.evaluate(() => {
        const rows = Array.from(document.querySelectorAll('#inv-in-mask [data-row]'));
        const msg = document.getElementById('inv-in-mask-scan-msg');
        return {
            rows: rows.map((r) => ({
                product: (r.querySelector('[data-k="product_id"]') || {}).value || '',
                qty: (r.querySelector('[data-k="qty"]') || {}).value || '',
                batch: (r.querySelector('[data-k="batch_no"]') || {}).value || '',
            })),
            msgText: msg ? msg.textContent.trim() : null,
            msgHtmlLen: msg ? msg.innerHTML.length : -1,
        };
    });
}

async function gunIntoBatch(browser, origin, stall) {
    const bag = { asked: [] };
    const page = await boot(browser, bag, origin);
    const typedBatch = await primeBatchRow(page);
    const before = await snapshot(page);
    bag.asked.length = 0;
    if (stall) await armStall(page, 4, STALL_MS);
    // 第二箱:枪 6ms/字符打进批号框(光标就停在店员刚填批号的地方 —— 这是真实动作顺序)
    await page.evaluate(() => {
        window.__ks = [];
        window.__kp = () => window.__ks.push(performance.now());
        document.addEventListener('keydown', window.__kp, true);
    });
    await page.keyboard.type(MILK, { delay: 6 });
    await page.keyboard.press('Enter');
    const raw = await page.evaluate(() => {
        document.removeEventListener('keydown', window.__kp, true);
        return window.__ks;
    });
    const gaps = raw.slice(1).map((t, i) => Math.round(t - raw[i]));
    await page.waitForTimeout(1100);
    const after = await snapshot(page);
    await shot(page, stall ? 'i1-gun-into-batch-with-stall.png' : 'i2-gun-into-batch-clean.png');
    // 「这一箱进单了吗」= 带商品的行多了一条(空占位行会被 planRow 填掉,不是追加)
    const filled = (rs) => rs.filter((r) => r.product).length;
    const addedRow = filled(after.rows) > filled(before.rows);
    const batchRestored = after.rows[0] && after.rows[0].batch === typedBatch;
    const ok = addedRow && batchRestored && bag.asked.includes(MILK);
    return {
        ok,
        stall: !!stall,
        typedBatch,
        maxGap: gaps.length ? Math.max(...gaps) : 0,
        beforeRows: before.rows,
        afterRows: after.rows,
        asked: bag.asked,
        msgText: after.msgText,
        why: ok
            ? ''
            : '这一发枪扫既没加行也没查码,屏上零提示,码原样怼在店员填好的批号里',
    };
}

const CASES = [
    ['gunIntoBatchWithOneLongTask', (b, o) => gunIntoBatch(b, o, true)],
    ['gunIntoBatchClean', (b, o) => gunIntoBatch(b, o, false)],
];

(async () => {
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch();
    let failed = 0;
    try {
        failed = await runCases(
            CASES,
            async (fn) => fn(browser, origin),
            path.join(SHOTS, 'report-r3-inv-jank.json')
        );
    } finally {
        await browser.close();
        server.close();
    }
    process.exit(failed ? 1 : 0);
})();
