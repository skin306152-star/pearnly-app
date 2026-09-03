/*
 * scripts/_inv_scan_smoke.cjs · 入库弹窗扫码加行的真浏览器验收(Chromium + 真键盘 + 假摄像头)
 *
 * 为什么不能只靠单测:落行判定是纯函数(已单测),但「枪扫到底收不收得到」「码有没有被打进
 * 数量框」「批次格有没有真的露出来」「取景框跟解码区对不对得上」「关弹窗相机灯灭没灭」这五件
 * 全在浏览器里才成立。grep 类名 / 断言 MODAL=true 都验不出它们。
 *
 * 真的东西:home.html、dist/main.js、dist/home.css、dist/pre.js、dist/scan.js、dist/zxing.js
 * 全是本仓真产物;键盘是真键盘(page.keyboard.type,不是 fill);摄像头是 Chromium 假设备喂
 * 一张真合成 EAN-13;文案期望值现场从页面里的真 window.I18N 取,一个字都不注入。
 * 只有 /api/** 与 window.getActiveWorkspaceClientId 是桩 —— 前者是后端,后者是账套切换器,
 * 都不在本轮改动面内。
 *
 * 用法(仓库根目录):
 *   python scripts/_scan_ean_y4m.py .scan_fixture.y4m
 *   node scripts/_inv_scan_smoke.cjs .scan_fixture.y4m [截图目录]
 * 退出码 0 = 全过。截图默认落 tests/e2e/_artifacts/inv_scan/。
 */
const fs = require('fs');
const path = require('path');
const { startStaticServer } = require('./_smoke_server.cjs');
const { chromium } = require('@playwright/test');

const ROOT = path.resolve(__dirname, '..');
const Y4M = path.resolve(process.argv[2] || '.scan_fixture.y4m');
const SHOTS = path.resolve(process.argv[3] || path.join(ROOT, 'tests/e2e/_artifacts/inv_scan'));

const COLA = '8850999320014'; // 假摄像头素材里的那张码
const MILK = '4901234567894'; // 批次品 · 用来验批号/效期格真的露出来
const BOX = '8850999320021'; // 同一件可乐的箱码(挂在 product_units 上 · 12 瓶一箱)
// 库里没有。不写成全 9：一串一模一样的字符会被楔子当「按住键不放」挡掉
// （looksLikeGun 的 hasTwoDistinct），在声明接枪的框里整发静默丢掉，验的就不是未命中了。
const GHOST = '9999999999994';
const BOX_UNIT = 'ลัง';

const P_COLA = {
    id: 'p-cola',
    name_th: 'โค้ก 325ml',
    name_en: 'Coke 325ml',
    name_zh: '可乐 325ml',
    default_cost: 7,
    track_batch: false,
};
const P_MILK = {
    id: 'p-milk',
    name_th: 'นมสด 1L',
    name_en: 'Milk 1L',
    name_zh: '鲜奶 1L',
    default_cost: 20,
    track_batch: true,
};

// 信封照 routes/products_routes.py 的 /lookup:{product: _out(row)} + matched_by/matched_unit
// (与建品侧 sales-products-scan.ts 读的是同一份)。主码命中那一档照 POS by-barcode 的老实现
// 把 base_unit 填进 matched_unit —— 那不是箱码,行上不该冒出单位。
const LOOKUP = {
    [COLA]: { product: P_COLA, matched_by: 'product', matched_unit: 'ขวด' },
    [MILK]: { product: P_MILK, matched_by: 'product', matched_unit: 'กล่อง' },
    [BOX]: { product: P_COLA, matched_by: 'unit', matched_unit: BOX_UNIT },
};

const STOCK_ITEMS = [
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

const serve = () => startStaticServer({ root: ROOT, index: 'home.html' });

async function stubApi(page, posted) {
    await page.route('https://cdnjs.cloudflare.com/**', (r) => r.abort());
    await page.route('**/api/**', async (route) => {
        const url = new URL(route.request().url());
        if (url.pathname === '/api/sales/products/lookup') {
            const hit = LOOKUP[url.searchParams.get('barcode')];
            if (!hit) {
                await route.fulfill({ status: 404, json: { detail: 'sales.product_not_found' } });
                return;
            }
            await route.fulfill({ json: hit });
            return;
        }
        // 入库真载荷:屏上看着对不算数,发出去的那份才是进流水的东西
        if (url.pathname === '/api/inventory/in') {
            if (posted) posted.push(route.request().postDataJSON());
            await route.fulfill({ json: { ok: true, data: { txn_ids: ['t1'] } } });
            return;
        }
        if (url.pathname === '/api/inventory/stock') {
            await route.fulfill({
                json: {
                    ok: true,
                    data: {
                        items: STOCK_ITEMS,
                        cost_visible: true,
                        summary: {
                            sku_count: 2,
                            stock_value: 282,
                            low_count: 0,
                            out_count: 0,
                        },
                    },
                },
            });
            return;
        }
        if (url.pathname === '/api/me') {
            await route.fulfill({ json: { email: 'inv-scan@e2e', role: 'owner', plan: 'pro' } });
            return;
        }
        await route.fulfill({ json: { ok: true, data: {} } });
    });
}

// 相机释放只能从外面看流:包一层 getUserMedia 记下真 stream,关弹窗后断言 track 全 ended。
const INIT = () => {
    localStorage.setItem('mrpilot_token', 'inv-scan-e2e');
    const md = navigator.mediaDevices;
    const orig = md.getUserMedia.bind(md);
    window.__streams = [];
    md.getUserMedia = async (c) => {
        const s = await orig(c);
        window.__streams.push(s);
        return s;
    };
};

async function openInModal(page, origin) {
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
    await page.locator('#inv-btn-in').click(); // 真点真按钮,不直接调 openInventoryIn
    await page.locator('#inv-in-mask .inv-scan').waitFor();
}

// 枪 = 极快的键盘 + 回车。delay 5ms 远小于楔子的 150ms 间隔阈值。
async function gunScan(page, code) {
    await page.keyboard.type(code, { delay: 5 });
    await page.keyboard.press('Enter');
}

// 旧行为下有些等待本来就等不到(那正是反证要证的),超时该报一条干净的 FAIL 而不是 CRASH。
async function waitQuiet(page, fn, arg, timeout = 6000) {
    try {
        await page.waitForFunction(fn, arg, { timeout });
    } catch (_) {
        /* 交给下面的断言去报 */
    }
}

function rowSnapshot() {
    return Array.from(document.querySelectorAll('#inv-in-mask-rows [data-row]')).map((row) => {
        const unit = row.querySelector('[data-runit]');
        return {
            product: row.querySelector('[data-k="product_id"]').value,
            label: row.querySelector('[data-k="product_id"]').selectedOptions[0]?.textContent || '',
            qty: row.querySelector('[data-k="qty"]').value,
            cost: row.querySelector('[data-k="unit_cost"]').value,
            unit: row.querySelector('[data-k="unit_name"]').value,
            unitShown: getComputedStyle(unit).display !== 'none',
            unitText: unit.textContent,
            batchCellShown:
                getComputedStyle(row.querySelector('[data-batchcell]')).display !== 'none',
        };
    });
}

// 批号/效期只有在批次格真露出来时才填得进去 —— 填不进去本身就是「这箱的批次无处可写」。
async function fillBatch(page, idx, batchNo, expiry) {
    const row = page.locator('#inv-in-mask-rows [data-row]').nth(idx);
    if (!(await row.locator('[data-batchcell]').isVisible())) return false;
    await row.locator('[data-k="batch_no"]').fill(batchNo);
    await row.locator('[data-k="expiry_date"]').fill(expiry);
    return true;
}

// 文案期望值只能从页面里的真 window.I18N 取:自己在脚本里抄一份 = 拿自己比自己,漏译照绿。
async function copyOf(page, key, params) {
    return page.evaluate(
        ([k, p]) => {
            let s = window.I18N[window._currentLang][k];
            for (const name in p) s = s.replace('{' + name + '}', p[name]);
            return s;
        },
        [key, params || {}]
    );
}

async function submitIn(page) {
    await page.locator('#inv-in-mask-submit').click();
    await waitQuiet(page, () => !document.getElementById('inv-in-mask').classList.contains('show'));
}

async function shot(page, name) {
    await page.screenshot({ path: path.join(SHOTS, name), fullPage: false });
}

async function gunFlow(browser, origin) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await page.addInitScript(INIT);
    await stubApi(page);
    await openInModal(page, origin);

    const bar = page.locator('#inv-in-mask .inv-scan');
    const visible = await bar.isVisible();
    const camBtn = page.locator('#inv-in-mask-scan-cam');
    const camStyle = await camBtn.evaluate((el) => {
        const cs = getComputedStyle(el);
        return { display: cs.display, disabled: el.disabled, text: el.textContent.trim() };
    });
    await shot(page, '01-scanbar-desktop.png');

    // ① 枪扫第一件:焦点在刚点过的按钮上(非输入框)→ 楔子该收到
    await gunScan(page, COLA);
    await page.waitForFunction(
        () => document.querySelector('#inv-in-mask-rows [data-k="product_id"]').value !== ''
    );
    await page.locator('[data-scan-success-fly]').waitFor({ state: 'attached' });
    const afterFirst = await page.evaluate(rowSnapshot);
    const focusFirst = await page.evaluate(() => document.activeElement?.dataset.k || '');
    const visualFirst = await page.evaluate(() => {
        const fly = document.querySelector('[data-scan-success-fly]');
        return {
            label: fly?.querySelector('.scan-success-name')?.textContent || '',
            increment: fly?.querySelector('.scan-success-amount')?.textContent || '',
            pointerEvents: fly ? getComputedStyle(fly).pointerEvents : '',
        };
    });
    await shot(page, '02-gun-visual-first.png');

    // ② 同一个码再扫一次:此刻焦点在数量框里(枪的字符会落进去)→ 该 +1 且不生成第二行,
    //    数量框里不许留下一串条码
    await gunScan(page, COLA);
    await page.waitForFunction(
        () => document.querySelector('#inv-in-mask-rows [data-k="qty"]').value === '2'
    );
    const afterSecond = await page.evaluate(rowSnapshot);
    const overlappingVisuals = await page.locator('[data-scan-success-fly]').count();

    // ③ 批次品:批号/效期格必须真的露出来(走 onProductChange 同一套显隐)
    await gunScan(page, MILK);
    await page.waitForFunction(
        () =>
            document.querySelectorAll('#inv-in-mask-rows [data-k="product_id"]')[1].value ===
            'p-milk'
    );
    const afterMilk = await page.evaluate(rowSnapshot);
    await shot(page, '02-gun-rows.png');

    // ④ 未命中:必须把扫到的码显出来 + 给「去建这个商品」
    await gunScan(page, GHOST);
    await page.locator('#inv-in-mask-scan-msg [data-scan-create]').waitFor();
    const notFound = await page.evaluate(() => {
        const msg = document.getElementById('inv-in-mask-scan-msg');
        return {
            text: msg.textContent,
            tone: msg.className,
            code: msg.querySelector('[data-scan-create]').dataset.scanCreate,
            shown: getComputedStyle(msg).display !== 'none',
        };
    });
    const rowsAfterGhost = await page.evaluate(rowSnapshot);
    await shot(page, '03-notfound.png');

    await page.close();
    return {
        ok:
            visible &&
            camStyle.display !== 'none' &&
            camStyle.disabled === false &&
            afterFirst[0].product === 'p-cola' &&
            afterFirst[0].qty === '1' &&
            afterFirst[0].cost === '9.5' &&
            focusFirst === 'qty' &&
            visualFirst.label === P_COLA.name_th &&
            visualFirst.increment === '+1' &&
            visualFirst.pointerEvents === 'none' &&
            afterSecond.length === 2 &&
            afterSecond[0].qty === '2' &&
            overlappingVisuals >= 2 &&
            !afterSecond[0].qty.includes(COLA) &&
            afterSecond[1].product === '' &&
            afterMilk[1].product === 'p-milk' &&
            afterMilk[1].qty === '1' &&
            afterMilk[1].batchCellShown === true &&
            afterMilk[0].batchCellShown === false &&
            notFound.shown &&
            // 码显在屏上这件事要有真文案才看得出,验在 copyPreview 里;这里验它被带住了
            notFound.code === GHOST &&
            rowsAfterGhost.length === 2,
        camStyle,
        afterFirst,
        focusFirst,
        visualFirst,
        overlappingVisuals,
        afterSecond,
        afterMilk,
        notFound,
        rowsAfterGhost,
    };
}

// P1-G 反证 · 两箱牛奶不同效期:同码再扫必须【另起一行】,不能把第二箱并进第一箱那一行。
// 并进去 = 两箱全落在第一箱的批号/效期下,POS 的 FEFO 出货顺序与近效期告警从此按错日期算。
// 判据落在发出去的载荷上:屏上两行也可能提交成一行。
async function batchSplitFlow(browser, origin) {
    const posted = [];
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await page.addInitScript(INIT);
    await stubApi(page, posted);
    await openInModal(page, origin);

    // 两箱连着扫(焦点停在数量框,枪的下一发照旧收得到),再逐行填各自的批号/效期。
    // 顺序不能倒过来:光标一旦停在批号/效期框里,楔子按 opt-in 规则让开,枪那一发会被吞掉
    // (见交付报告里的遗留问题),那验的就不是本条修复了。
    await gunScan(page, MILK); // 第一箱
    await waitQuiet(
        page,
        () => document.querySelector('#inv-in-mask-rows [data-k="product_id"]').value === 'p-milk'
    );
    await gunScan(page, MILK); // 第二箱:批号/效期跟第一箱不同
    await waitQuiet(page, () => {
        const rows = document.querySelectorAll('#inv-in-mask-rows [data-row]');
        return rows.length > 1 && rows[1].querySelector('[data-k="product_id"]').value === 'p-milk';
    });
    // 另起一行必须当场说清为什么,否则店员只看见行数变多。期望值取页面里的真词条。
    const msgText = await page.locator('#inv-in-mask-scan-msg').innerText();
    const wantMsg = await copyOf(page, 'inv-scan-batch-row', { name: P_MILK.name_th });
    const filledFirst = await fillBatch(page, 0, 'A-01', '2026-08-10');
    const filledSecond = await fillBatch(page, 1, 'B-02', '2026-11-02');
    const rows = await page.evaluate(rowSnapshot);
    await shot(page, '07-batch-second-box-own-row.png');

    await submitIn(page);
    await page.close();
    const lines = (posted[0] && posted[0].lines) || [];
    const milk = rows.filter((r) => r.product === 'p-milk');
    return {
        ok:
            msgText === wantMsg &&
            filledFirst &&
            filledSecond &&
            milk.length === 2 &&
            milk.every((r) => r.qty === '1' && r.cost === '28' && r.batchCellShown) &&
            lines.length === 2 &&
            lines.every(
                (l) =>
                    l.product_id === 'p-milk' && Number(l.qty) === 1 && Number(l.unit_cost) === 28
            ) &&
            lines[0].batch_no === 'A-01' &&
            lines[0].expiry_date === '2026-08-10' &&
            lines[1].batch_no === 'B-02' &&
            lines[1].expiry_date === '2026-11-02',
        msgText,
        wantMsg,
        filledFirst,
        filledSecond,
        rows,
        lines,
    };
}

// P1-J 反证 · 箱码入库按箱算:命中的是单位码时这一行必须带上单位(屏上看得见 + 载荷里发得出),
// 且不能跟同一件货的瓶码合并成一行(1 箱 ≠ 1 瓶)。换算交后端 factor_to_base,前端不自己乘。
async function unitCodeFlow(browser, origin) {
    const posted = [];
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await page.addInitScript(INIT);
    await stubApi(page, posted);
    await openInModal(page, origin);

    await gunScan(page, BOX);
    await waitQuiet(
        page,
        () => document.querySelector('#inv-in-mask-rows [data-k="unit_name"]').value !== ''
    );
    const msgText = await page.locator('#inv-in-mask-scan-msg').innerText();
    const wantMsg =
        (await copyOf(page, 'inv-scan-added', { name: P_COLA.name_th })) +
        ' · ' +
        (await copyOf(page, 'inv-scan-unit-hit', { unit: BOX_UNIT }));

    await gunScan(page, COLA); // 同一件货的瓶码:不许并进箱那一行
    await waitQuiet(page, () => {
        const rows = document.querySelectorAll('#inv-in-mask-rows [data-row]');
        return rows.length > 1 && rows[1].querySelector('[data-k="product_id"]').value === 'p-cola';
    });
    const rows = await page.evaluate(rowSnapshot);
    await shot(page, '08-unit-code-row.png');

    // 手机上收货是常态:单位标签只能在自己那一格里收边(ellipsis),不许把行撑宽。
    // 行本身在窄屏是否已经横向溢出是存量问题,这里只量不断言。
    await page.setViewportSize({ width: 390, height: 820 });
    const mobile = await page.evaluate(() => {
        const wrap = document.getElementById('inv-in-mask-rows');
        const cell = wrap.querySelector('.inv-qtycell');
        const unit = wrap.querySelector('[data-runit]');
        return {
            unitShown: getComputedStyle(unit).display !== 'none',
            fitsCell: unit.getBoundingClientRect().width <= cell.getBoundingClientRect().width + 1,
            rowsOverflow: wrap.scrollWidth - wrap.clientWidth,
        };
    });
    await shot(page, '08b-unit-code-mobile.png');
    await page.setViewportSize({ width: 1280, height: 900 });

    await submitIn(page);
    await page.close();
    const lines = (posted[0] && posted[0].lines) || [];
    return {
        ok:
            rows.length === 2 &&
            rows[0].unit === BOX_UNIT &&
            rows[0].unitShown &&
            rows[0].unitText === BOX_UNIT &&
            rows[0].qty === '1' &&
            rows[0].cost === '9.5' &&
            rows[1].product === 'p-cola' &&
            rows[1].unit === '' &&
            rows[1].qty === '1' &&
            rows[1].cost === '9.5' &&
            // 屏上要说清这一行按什么单位入(逐字对真词条 · 裸键在这一步就现形)
            msgText === wantMsg &&
            lines.length === 2 &&
            lines[0].unit_name === BOX_UNIT &&
            Number(lines[0].qty) === 1 &&
            lines[1].unit_name === undefined &&
            mobile.unitShown &&
            mobile.fitsCell,
        msgText,
        wantMsg,
        rows,
        mobile,
        lines,
    };
}

// P1-D 正面 · 真桥不打桩:点「去建这个商品」必须把建品表单【叠在入库弹窗之上】开出来,
// 半张入库单(已扫进去的行)一行都不能丢,码要已经填在建品表单的条码位上。
async function createOverlayFlow(browser, origin) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await page.addInitScript(INIT);
    await stubApi(page);
    await openInModal(page, origin);

    await gunScan(page, COLA); // 先扫进一件:叠上去之后它必须还在
    await waitQuiet(
        page,
        () => document.querySelector('#inv-in-mask-rows [data-k="product_id"]').value === 'p-cola'
    );
    await gunScan(page, GHOST);
    await page.locator('#inv-in-mask-scan-msg [data-scan-create]').click();
    await waitQuiet(page, () => !!document.getElementById('sx-pf-barcode'));
    // 建品弹窗是淡入的:动画没走完就照,截出来的是两层半透明叠在一起,看不出谁在上面
    await waitQuiet(page, () => {
        const box = document.getElementById('sales-prod-mask');
        return !!box && getComputedStyle(box).opacity === '1';
    });
    // 表单没开出来时这里的元素全是 null:照旧读完给一份「都是 false」的快照,让断言去报 FAIL
    // ——— 崩在 getComputedStyle(null) 上只会显得是脚本坏了。
    const state = await page.evaluate(() => {
        const form = document.getElementById('sx-pf-barcode');
        const inv = document.getElementById('inv-in-mask');
        const box = document.getElementById('sales-prod-mask');
        const zOf = (el) => (el ? Number(getComputedStyle(el).zIndex) || 0 : 0);
        return {
            formOpen: !!form && !!box && getComputedStyle(box).display !== 'none',
            barcode: form ? form.value : null,
            invStillOpen: !!inv && inv.classList.contains('show'),
            rowKept: (document.querySelector('#inv-in-mask-rows [data-k="product_id"]') || {})
                .value,
            // 叠上去 = 建品那层压在入库那层之上,不是把入库那层顶掉
            aboveInv: zOf(box) > zOf(inv),
        };
    });
    await shot(page, '10-create-form-overlaid.png');
    await page.close();
    return {
        ok:
            state.formOpen &&
            state.barcode === GHOST &&
            state.invStillOpen &&
            state.rowKept === 'p-cola' &&
            state.aboveInv,
        state,
    };
}

// P1-D 反证 · 未命中那张卡上的「去建这个商品」必须真的按跨页带码桥的契约调用:
//   window.openProductFormWithBarcode(code, { overlay: true }) → 返回 true 才算真打开。
// 桩顶掉真桥(真桥会 routeTo 跳走),先记下真产物里这个名字确实存在,再验两个分支。
async function createBridgeFlow(browser, origin) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await page.addInitScript(INIT);
    await stubApi(page);
    await openInModal(page, origin);
    const realBridge = await page.evaluate(() => typeof window.openProductFormWithBarcode);
    await page.evaluate(() => {
        window.__calls = [];
        window.__answer = true;
        window.openProductFormWithBarcode = (code, opts) => {
            window.__calls.push({ code, opts });
            return window.__answer;
        };
    });

    await gunScan(page, GHOST);
    await page.locator('#inv-in-mask-scan-msg [data-scan-create]').click();
    const opened = await page.evaluate(() => ({
        calls: window.__calls,
        // 表单叠在上面 = 入库单还在,行没被清、卡也没被换成「自己去建」
        cardStill: !!document.querySelector('#inv-in-mask-scan-msg [data-scan-create]'),
        rows: document.querySelectorAll('#inv-in-mask-rows [data-row]').length,
        modalOpen: document.getElementById('inv-in-mask').classList.contains('show'),
    }));

    // 桥说打不开 → 不许假装成功:回落成带着那串码的诚实文案
    await page.evaluate(() => {
        window.__answer = false;
    });
    await gunScan(page, GHOST);
    await page.locator('#inv-in-mask-scan-msg [data-scan-create]').click();
    const refused = await page.evaluate(() => {
        const msg = document.getElementById('inv-in-mask-scan-msg');
        return {
            text: msg.innerText,
            tone: msg.className,
            btnLeft: !!msg.querySelector('[data-scan-create]'),
        };
    });
    await shot(page, '09-create-bridge-refused.png');
    await page.close();
    return {
        ok:
            realBridge === 'function' &&
            opened.calls.length === 1 &&
            opened.calls[0].code === GHOST &&
            opened.calls[0].opts &&
            opened.calls[0].opts.overlay === true &&
            opened.cardStill &&
            opened.rows === 2 &&
            opened.modalOpen &&
            !refused.btnLeft &&
            refused.tone.includes('warn') &&
            refused.text.includes(GHOST) &&
            !/inv-scan-[a-z]|bscan\./.test(refused.text),
        realBridge,
        opened,
        refused,
    };
}

async function cameraFlow(browser, origin) {
    const page = await browser.newPage({ viewport: { width: 390, height: 820 } });
    await page.addInitScript(INIT);
    await stubApi(page);
    await openInModal(page, origin);

    const lazy = [];
    page.on('request', (r) => {
        const m = r.url().match(/\/static\/dist\/(scan|zxing)\.js/);
        if (m) lazy.push(m[1]);
    });
    const beforeLoad = await page.evaluate(() => typeof window.PearnlyScanCamera.create);

    await page.locator('#inv-in-mask-scan-cam').click();
    await page.locator('#inv-in-mask-scan-stage .bscan-video').waitFor();
    // 解出码 = 该行数量从空变 1
    await page.waitForFunction(
        () => document.querySelector('#inv-in-mask-rows [data-k="qty"]').value === '1',
        null,
        { timeout: 25000 }
    );
    const decoded = await page.evaluate(rowSnapshot);
    // 取景框必须落在真正被解码的那块区域【之内】(预览 object-fit:cover 只裁不补)
    const geom = await page.evaluate(() => {
        const v = document.querySelector('#inv-in-mask-scan-stage .bscan-video');
        const f = document.querySelector('#inv-in-mask-scan-stage .inv-scan-frame');
        const probe = window.PearnlyScanCamera.create({});
        const crop = probe.cropRatio();
        probe.destroy();
        const vr = v.getBoundingClientRect();
        const fr = f.getBoundingClientRect();
        const controls = document.querySelector(
            '#inv-in-mask-scan-stage [data-scan-view-controls]'
        );
        const motion = controls?.querySelector('[data-scan-motion-toggle]');
        const torch = controls?.querySelector('.scan-view-torch');
        return {
            crop,
            wRatio: fr.width / vr.width,
            hRatio: fr.height / vr.height,
            inside: fr.left >= vr.left && fr.right <= vr.right && fr.top >= vr.top,
            frameVisible: getComputedStyle(f).borderTopWidth !== '0px',
            controls: {
                exists: !!controls,
                motionChecked: !!motion?.checked,
                pointerEvents: controls ? getComputedStyle(controls).pointerEvents : '',
                torchHidden: !!torch?.hidden,
            },
        };
    });
    await shot(page, '04-camera-live-mobile.png');

    // 关弹窗 = 放相机 + 退订楔子:走 closeModal → unmountInvScan 这条真路。
    // 按 '.inv-mbtn' 取第一个会点到摄像头按钮(DOM 序是 [扫码-cam, 取消, 提交]),那走的是
    // stopCamera(),unmount 那条从来没被覆盖过 —— 楔子没反注册的话,关窗之后全站扫码都进不来。
    await page.locator('#inv-in-mask .inv-modal-foot [data-inv-close]').click();
    const released = await page.evaluate(() => {
        const tracks = window.__streams.flatMap((s) => s.getTracks());
        return {
            streams: window.__streams.length,
            live: tracks.filter((t) => t.readyState === 'live').length,
            videoLeft: document.querySelectorAll('#inv-in-mask .bscan-video').length,
            wedgeSubs: window.PearnlyScanWedge.subscriberCount(),
            modalOpen: document.getElementById('inv-in-mask').classList.contains('show'),
        };
    });
    await page.close();
    return {
        ok:
            beforeLoad === 'undefined' &&
            lazy.includes('scan') &&
            decoded[0].product === 'p-cola' &&
            decoded[0].qty === '1' &&
            geom.inside &&
            geom.frameVisible &&
            geom.wRatio < geom.crop.width &&
            geom.hRatio < geom.crop.height &&
            released.streams === 1 &&
            released.live === 0 &&
            released.videoLeft === 0 &&
            geom.controls.exists &&
            geom.controls.motionChecked &&
            geom.controls.pointerEvents === 'auto' &&
            geom.controls.torchHidden &&
            released.wedgeSubs === 0 &&
            !released.modalOpen,
        beforeLoad,
        lazy,
        decoded,
        geom,
        released,
    };
}

// 这一屏照人眼验版式,顺带把文案验实:期望值现场从页面里的真 window.I18N 取,一个字都不注入。
// 注入过的版本(哪怕「只补字典里没有的键」)会把漏译照成绿的 —— 拿自己比自己,永远相等。
async function copyPreview(browser, origin, lang) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await page.addInitScript(INIT);
    await page.addInitScript((l) => localStorage.setItem('mrpilot_lang', l), lang);
    await stubApi(page);
    await openInModal(page, origin);
    const copy = await page.evaluate(() => ({
        lang: window._currentLang,
        dict: window.I18N[window._currentLang],
    }));
    await gunScan(page, COLA);
    await page.waitForFunction(
        () => document.querySelector('#inv-in-mask-rows [data-k="qty"]').value === '1'
    );
    await shot(page, `05-copy-${lang}.png`);
    const hit = await page.locator('#inv-in-mask .inv-scan').innerText();

    // 未命中那张卡:扫到的码必须真的显在屏上(店员靠它分辨码错了还是没建档)
    await gunScan(page, GHOST);
    await page.locator('#inv-in-mask-scan-msg [data-scan-create]').waitFor();
    const miss = await page.locator('#inv-in-mask-scan-msg').innerText();
    await shot(page, `06-notfound-copy-${lang}.png`);
    await page.close();
    // 没落地的码挂在一份失败清单上(计数行 + 「知道了」 + 每条一行),不是一句会被下一件盖掉
    // 的话 —— 这四行逐字对真词条,少一行或多一行都说明清单的样子变了。
    const wantMiss = [
        copy.dict['inv-scan-fails-n'].replace('{n}', '1'),
        copy.dict['inv-scan-fails-ack'],
        copy.dict['bscan.notfound'].replace('{code}', GHOST),
        copy.dict['bscan.notfound_create'],
    ].join('|');
    return {
        // 屏上不许出现裸键(键名漏了 i18n 就长这样),未命中那张卡逐字对真词条
        ok:
            copy.lang === lang &&
            !/inv-scan-[a-z]|bscan\./.test(hit + miss) &&
            hit.includes(copy.dict['inv-scan-hint']) &&
            miss
                .trim()
                .split(/\s*\n\s*/)
                .join('|') === wantMiss,
        lang: copy.lang,
        hit,
        miss,
        wantMiss,
    };
}

(async () => {
    if (!fs.existsSync(Y4M)) {
        console.error(`缺假摄像头素材 ${Y4M} —— 先跑 python scripts/_scan_ean_y4m.py ${Y4M}`);
        process.exit(2);
    }
    fs.mkdirSync(SHOTS, { recursive: true });
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch({
        args: [
            '--use-fake-ui-for-media-stream',
            '--use-fake-device-for-media-stream',
            `--use-file-for-fake-video-capture=${Y4M}`,
        ],
    });
    const report = {
        gunFlow: await gunFlow(browser, origin),
        batchSplitFlow: await batchSplitFlow(browser, origin),
        unitCodeFlow: await unitCodeFlow(browser, origin),
        createOverlayFlow: await createOverlayFlow(browser, origin),
        createBridgeFlow: await createBridgeFlow(browser, origin),
        cameraFlow: await cameraFlow(browser, origin),
        copyZh: await copyPreview(browser, origin, 'zh'),
        copyTh: await copyPreview(browser, origin, 'th'),
    };
    await browser.close();
    server.close();

    const failed = Object.keys(report).filter((k) => !report[k].ok);
    console.log(JSON.stringify(report, null, 2));
    console.log(failed.length ? `FAIL: ${failed.join(', ')}` : `PASS · 截图在 ${SHOTS}`);
    process.exit(failed.length ? 1 : 0);
})().catch((e) => {
    console.error('SMOKE CRASH', e);
    process.exit(2);
});
