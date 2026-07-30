/*
 * scripts/_inv_p1_verify.cjs · 入库侧 P1-⑦ / P1-② / P1-⑧ / P0-④ 的真浏览器反证
 *
 * 上一轮那批反证全绿却让病灶原样复发,根因是「用不会出事的输入,验会出事的判据」。这一份
 * 每一例喂的都是会出事的那种输入,前提写在各例头上:
 *   ① 会出事的商品 = 列表缓存里【没有】的那件(刚建完品 · 库存页在搜索态)—— 缓存里有的
 *      那件恰好是唯一走得通的分法,验它永远绿。
 *   ② 会出事的落点 = 光标真的在 type=date 那个框里(不是数量框)—— 数量框有 stripScanned
 *      兜着,验它同样永远绿。
 *   ③ 会出事的顺序 = 失败夹在队列中间、后面还有成功的 —— 失败排最后时旧代码也「看着对」。
 *   ④ 会出事的速度 = 慢到楔子都不认的一串码打进效期框 —— 枪速那档已被 ② 收掉,这一档专验
 *      提交闸(前端最后一道)。
 *
 * 真的东西:home.html + static/dist/{main.js,home.css,pre.js}(常驻楔子在 pre.js 里)、
 * 真键盘(keyboard.type,不用 fill 造扫码)、文案期望值现场从页面里的真 window.I18N 取。
 * 桩只有 /api/**(后端)与 getActiveWorkspaceClientId(账套切换器),都不在本轮改动面内。
 *
 * 用法(仓库根目录):node scripts/_inv_p1_verify.cjs [截图目录]
 * 退出码 0 = 全过。截图默认落 tests/e2e/_artifacts/inv_p1/。
 */
const path = require('path');
const { chromium } = require('@playwright/test');
const { ROOT, DESKTOP, serve, gun, shotter, runCases } = require('./_gun_wedge_lib.cjs');

const SHOTS = path.resolve(process.argv[2] || path.join(ROOT, 'tests/e2e/_artifacts/inv_p1'));
const shot = shotter(SHOTS);

const COLA = '8850999320014'; // 非批次品 · 缓存里有
const MILK = '4901234567894'; // 批次品 · 缓存里有(用来先造出一个批次格)
const YOG = '8850111000015'; // 批次品 · 缓存里【没有】—— 刚建完品的那件
const GHOST_A = '9999999999991';
const GHOST_B = '9999999999992';

const HUMAN_MS = 260; // 每字符都超过楔子 MAX_GAP_MS=150 → 一串都攒不起来
const SLOW_GUN_MS = 80; // 攒得起一串,但超过 GUN_MAX_GAP_MS=50 → 判不成枪速

const P_COLA = { id: 'p-cola', name_th: 'โค้ก 325ml', name_zh: '可乐 325ml', track_batch: false };
const P_MILK = { id: 'p-milk', name_th: 'นมสด 1L', name_zh: '鲜奶 1L', track_batch: true };
// 刚在「用这个码建商品」里勾了批次管理保存出来的那件:建品的 save() 之后 load() 因为库存页
// 没有 #sx-p-body 直接 return,列表缓存一点没刷 —— 所以它只在查码应答里存在。
const P_YOG = { id: 'p-yog', name_th: 'โยเกิร์ต', name_zh: '酸奶杯', track_batch: true };

const LOOKUP = {
    [COLA]: { product: P_COLA, matched_by: 'product', matched_unit: 'ขวด' },
    [MILK]: { product: P_MILK, matched_by: 'product', matched_unit: 'กล่อง' },
    [YOG]: { product: P_YOG, matched_by: 'product', matched_unit: 'ถ้วย' },
};

const stockItem = (id, th, zh, batch) => ({
    product_id: id,
    name: { th, en: null, zh },
    image_url: null,
    barcode: null,
    base_unit: 'ชิ้น',
    qty_on_hand: 6,
    min_stock: 2,
    avg_cost: 10,
    status: 'ok',
    track_batch: batch,
    batches: [],
});
// 缓存 = 最近一次 /api/inventory/stock。p-yog 不在里面,这是本轮第一例的全部前提。
const STOCK = [
    stockItem('p-cola', 'โค้ก 325ml', '可乐 325ml', false),
    stockItem('p-milk', 'นมสด 1L', '鲜奶 1L', true),
];

async function route(page, state) {
    await page.route('https://cdnjs.cloudflare.com/**', (r) => r.abort());
    await page.route('**/api/**', async (r) => {
        const url = new URL(r.request().url());
        if (url.pathname === '/api/sales/products/lookup') {
            const code = url.searchParams.get('barcode');
            const hit = state.extra[code] || LOOKUP[code];
            await r.fulfill(
                hit ? { json: hit } : { status: 404, json: { detail: 'sales.product_not_found' } }
            );
            return;
        }
        if (url.pathname === '/api/inventory/in') {
            state.posted.push(r.request().postDataJSON());
            await r.fulfill({ json: { ok: true, data: { txn_ids: ['t1'] } } });
            return;
        }
        if (url.pathname === '/api/inventory/stock') {
            await r.fulfill({
                json: {
                    ok: true,
                    data: {
                        items: STOCK,
                        summary: { sku_count: 2, stock_value: 120, low_count: 0, out_count: 0 },
                    },
                },
            });
            return;
        }
        if (url.pathname === '/api/me') {
            await r.fulfill({ json: { email: 'inv-p1@e2e', role: 'owner', plan: 'pro' } });
            return;
        }
        await r.fulfill({ json: { ok: true, data: {} } });
    });
}

async function openModal(browser, origin) {
    const state = { posted: [], extra: {} };
    const page = await browser.newPage({ viewport: DESKTOP });
    await page.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'inv-p1-e2e');
        localStorage.setItem('mrpilot_lang', 'zh'); // 断言对真 zh 词典 · 截图给人眼看
    });
    await route(page, state);
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
    await page.locator('#inv-btn-in').click(); // 真点真按钮
    await page.locator('#inv-in-mask .inv-scan').waitFor();
    return { page, state };
}

// 旧行为下有些等待本来就等不到(那正是反证要证的):超时该落成一条干净的 FAIL,不是 CRASH。
async function quiet(page, fn, arg, timeout = 6000) {
    try {
        await page.waitForFunction(fn, arg, { timeout });
    } catch (_) {
        /* 交给下面的断言去报 */
    }
}

function rows() {
    return [...document.querySelectorAll('#inv-in-mask-rows [data-row]')].map((row) => {
        const sel = row.querySelector('[data-k="product_id"]');
        const cell = row.querySelector('[data-batchcell]');
        return {
            product: sel.value,
            label: (sel.selectedOptions[0] || {}).textContent || '',
            qty: row.querySelector('[data-k="qty"]').value,
            batchNo: row.querySelector('[data-k="batch_no"]').value,
            expiry: row.querySelector('[data-k="expiry_date"]').value,
            batchCellShown: getComputedStyle(cell).display !== 'none',
        };
    });
}

const focusK = () => ({
    k: (document.activeElement && document.activeElement.dataset.k) || '',
    type: (document.activeElement && document.activeElement.type) || '',
});

// 文案期望值现场从页面里的真 window.I18N 取:脚本自己抄一份 = 拿自己比自己,漏译照绿。
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
    await quiet(page, () => !document.getElementById('inv-in-mask').classList.contains('show'));
}

// 真人填日期的打法:段内打数字、按 → 换段(Chrome 的 date 控件就是这么用的;一口气打 8 个
// 数字在任何段序下都填不出日期)。段序跟浏览器区域设置走,故现场问 Intl,不押死在某个国家。
async function typeDateByHand(page, iso, delay) {
    const order = await page.evaluate(() =>
        new Intl.DateTimeFormat()
            .formatToParts(new Date())
            .map((p) => p.type)
            .filter((t) => t === 'year' || t === 'month' || t === 'day')
    );
    const seg = { year: iso.slice(0, 4), month: iso.slice(5, 7), day: iso.slice(8, 10) };
    for (let i = 0; i < order.length; i++) {
        await page.keyboard.type(seg[order[i]], { delay });
        if (i < order.length - 1) await page.keyboard.press('ArrowRight');
    }
}

// 点进 date 框的左边那一段。点正中间落到的是中间那一段,后面打进去的东西会随区域设置飘 ——
// 这一串到底落在哪一段决定了框里最后剩什么,前提不钉死,同一份断言在别的机器上就是另一回事。
const clickDateBox = (box) => box.click({ position: { x: 8, y: 10 } });

// ── ① P1-⑦ / P1-② · 缓存里没有这件货,批次格照样得露出来 ─────────────────
// 会出事的输入:p-yog 只在查码应答里存在,列表缓存(/api/inventory/stock)里没有它。
// 旧行为 syncRow 只传 row,那边照旧拿商品 id 去缓存里查 → 查不到 → 当非批次品 → 批次格隐藏
// 并清空 → 提交不带 batch_no → 一批批次品静默落进散装桶,近效期告警与 FEFO 全瞎。
// 用缓存里有的 p-milk 验就永远绿:那是唯一走得通的那种货。
async function freshProduct(browser, origin) {
    const { page, state } = await openModal(browser, origin);
    const inCache = await page.evaluate(
        (id) =>
            [...document.querySelectorAll('#inv-in-mask-rows [data-k="product_id"] option')].some(
                (o) => o.value === id
            ),
        P_YOG.id
    );

    const focus = await gun(page, YOG); // 焦点在刚点过的按钮上(非输入框)
    await quiet(
        page,
        (id) => document.querySelector('#inv-in-mask-rows [data-k="product_id"]').value === id,
        P_YOG.id
    );
    const afterScan = await page.evaluate(rows);

    // P1-② 的另一条路:店员在下拉里切走再切回来(此刻 onProductChange 没有查码应答可用)
    const sel = page.locator('#inv-in-mask-rows [data-k="product_id"]').first();
    await sel.selectOption('p-cola');
    await sel.selectOption(P_YOG.id);
    const afterReselect = await page.evaluate(rows);
    await shot(page, '01-fresh-product-batch-cell.png');

    // 批号/效期填不进去本身就是「这箱的批次无处可写」——填之前先看格子在不在
    const fillable = afterReselect[0].batchCellShown;
    if (fillable) {
        await page.locator('#inv-in-mask-rows [data-k="batch_no"]').first().fill('Y-77');
        await page.locator('#inv-in-mask-rows [data-k="expiry_date"]').first().fill('2027-03-15');
    }
    await submitIn(page);
    await page.close();

    const line = ((state.posted[0] || {}).lines || [])[0] || {};
    return {
        ok:
            inCache === false && // 前提:缓存里确实没有这件货
            focus.tag !== 'INPUT' &&
            afterScan[0].product === P_YOG.id &&
            afterScan[0].label === P_YOG.name_zh &&
            afterScan[0].batchCellShown === true &&
            afterReselect[0].batchCellShown === true &&
            fillable &&
            line.product_id === P_YOG.id &&
            line.batch_no === 'Y-77' &&
            line.expiry_date === '2027-03-15',
        inCache,
        focus,
        afterScan,
        afterReselect,
        posted: state.posted,
    };
}

// ── ② P1-⑧ · 光标真的在效期/批号框里再扫 ─────────────────────────────────
// 会出事的输入:焦点落在 type=date 上。旧行为楔子按 opt-in 规则让开输入框 → 整发被吞:
// 零回调、第二箱那一行不出现、屏上一句话都没有,而 13 位数字照旧落进 date 控件 →
// 效期变 49012-03-31(date 收 6 位年份,提交也不拦)。
// 数量框那条路验不出这个:那边早就 opt-in 了,还有 stripScanned 兜着。
async function gunFromDateField(browser, origin) {
    const { page } = await openModal(browser, origin);
    await gun(page, MILK); // 先造出一行带批次格的货
    await quiet(
        page,
        () => document.querySelector('#inv-in-mask-rows [data-k="qty"]').value === '1'
    );

    const dateBox = page.locator('#inv-in-mask-rows [data-k="expiry_date"]').first();
    await clickDateBox(dateBox); // 真点进去 —— 焦点必须真的在这个框里
    const focusDate = await page.evaluate(focusK);
    const before = await page.evaluate(rows);

    const atDate = await gun(page, MILK); // 第二箱:批次品必须另起一行
    await quiet(page, () => {
        const r = document.querySelectorAll('#inv-in-mask-rows [data-row]');
        return r.length > 1 && r[1].querySelector('[data-k="product_id"]').value === 'p-milk';
    });
    const afterGun = await page.evaluate(rows);

    // 慢枪(80ms/字符):判不成枪速,但日期被打坏这件事与速度无关 —— 照样得还原 + 加行
    await clickDateBox(dateBox);
    await gun(page, COLA, SLOW_GUN_MS);
    await quiet(page, () => {
        const r = document.querySelectorAll('#inv-in-mask-rows [data-row]');
        return [...r].some((x) => x.querySelector('[data-k="product_id"]').value === 'p-cola');
    });
    const afterSlow = await page.evaluate(rows);

    // 别把人手填日期也抢走:按真人的打法(段内打数字、→ 换段)填一个效期,日期得留下,
    // 也不许被当成扫了一件货
    await clickDateBox(dateBox);
    await typeDateByHand(page, '2027-05-20', HUMAN_MS);
    const afterHuman = await page.evaluate(rows);

    // 批号框(text)同样得接枪:整发被吞时它跟效期框是同一个病
    const batchBox = page.locator('#inv-in-mask-rows [data-k="batch_no"]').first();
    await batchBox.fill('L-2026');
    await batchBox.click();
    const focusBatch = await page.evaluate(focusK);
    await gun(page, YOG);
    await quiet(page, () => {
        const r = document.querySelectorAll('#inv-in-mask-rows [data-row]');
        return [...r].some((x) => x.querySelector('[data-k="product_id"]').value === 'p-yog');
    });
    const afterBatchField = await page.evaluate(rows);
    await shot(page, '02-gun-from-date-field.png');
    await page.close();

    const yog = afterBatchField.filter((r) => r.product === 'p-yog');
    return {
        ok:
            // 前提:两次扫之前焦点真的在那两个框里
            focusDate.k === 'expiry_date' &&
            focusDate.type === 'date' &&
            atDate.tag === 'INPUT' &&
            focusBatch.k === 'batch_no' &&
            before[0].expiry === '' &&
            // 日期没被写坏(旧行为这里是 49012-03-31 之类)
            afterGun[0].expiry === '' &&
            // 扫码真的被处理了:第二箱另起了一行
            afterGun[1].product === 'p-milk' &&
            afterGun[1].batchCellShown === true &&
            // 慢枪:日期还原 + 货照旧加进来
            afterSlow[0].expiry === '' &&
            afterSlow.some((r) => r.product === 'p-cola') &&
            // 人手填的日期留住了,且没被当成一件货
            afterHuman[0].expiry === '2027-05-20' &&
            afterHuman.length === afterSlow.length &&
            // 批号框:枪扫加了行,店员填的批号一个字符都没被动
            yog.length === 1 &&
            afterBatchField[0].batchNo === 'L-2026',
        focusDate,
        atDate,
        focusBatch,
        before,
        afterGun,
        afterSlow,
        afterHuman,
        afterBatchField,
    };
}

// ── ③ P0-④ · 失败夹在队列中间,后面还有成功的 ────────────────────────────
// 会出事的输入:GHOST_A → COLA → GHOST_B → COLA。旧行为一格消息共用一个 setMsg,最后那句
// 「已加入」把两条「这个码没建档」全盖掉 —— 店员按屏上反馈收货,那两件就是「扫了、没进单、
// 也没人告诉他」的货。失败排在最后那种顺序旧代码也「看着对」,验不出这条。
async function failuresSurvive(browser, origin) {
    const { page, state } = await openModal(browser, origin);
    const creates = (n) =>
        quiet(
            page,
            (want) =>
                document.querySelectorAll('#inv-in-mask-scan-msg [data-scan-create]').length ===
                want,
            n
        );
    await gun(page, GHOST_A);
    await creates(1);
    await gun(page, COLA);
    await quiet(
        page,
        () => document.querySelector('#inv-in-mask-rows [data-k="qty"]').value === '1'
    );
    await gun(page, GHOST_B);
    await creates(2);
    await gun(page, COLA); // 最后一件是成功的 —— 旧行为正是在这一步把两条失败全盖掉
    await quiet(
        page,
        () => document.querySelector('#inv-in-mask-rows [data-k="qty"]').value === '2'
    );
    const wantHit = await copyOf(page, 'inv-scan-bumped', { name: P_COLA.name_zh });
    const wantCount = await copyOf(page, 'inv-scan-fails-n', { n: 2 });
    const msg = await page.evaluate(() => {
        const el = document.getElementById('inv-in-mask-scan-msg');
        return {
            text: el.innerText,
            tone: el.className,
            codes: [...el.querySelectorAll('[data-scan-create]')].map((b) => b.dataset.scanCreate),
            lines: el.querySelectorAll('.inv-scan-line').length,
        };
    });
    await shot(page, '03-failures-survive-next-item.png');

    // 建完品回来重扫:那一条的待办到此为止,另一条不许跟着消失
    state.extra[GHOST_A] = { product: P_YOG, matched_by: 'product' };
    await gun(page, GHOST_A);
    await quiet(page, () => {
        const el = document.getElementById('inv-in-mask-scan-msg');
        return el.querySelectorAll('[data-scan-create]').length === 1;
    });
    const afterFix = await page.evaluate(() => {
        const el = document.getElementById('inv-in-mask-scan-msg');
        return {
            codes: [...el.querySelectorAll('[data-scan-create]')].map((b) => b.dataset.scanCreate),
            text: el.innerText,
        };
    });
    await shot(page, '04-resolved-one-kept-other.png');
    await page.close();

    return {
        ok:
            // 两条失败都还在,各自带着自己那串码
            msg.codes.length === 2 &&
            // 最新的排最上面(与收银台那份 fails 同序)
            msg.codes[0] === GHOST_B &&
            msg.codes[1] === GHOST_A &&
            msg.text.includes(GHOST_A) &&
            msg.text.includes(GHOST_B) &&
            // 成功那句照旧看得见(它只是不许盖掉失败)· 逐字对真词条
            msg.text.includes(wantHit) &&
            // 计数行 + 两条失败 + 那句「已加入/+1」
            msg.text.includes(wantCount) &&
            msg.lines === 4 &&
            msg.tone.includes('warn') &&
            // 屏上不许出现裸键
            !/inv-scan-[a-z]|bscan\./.test(msg.text) &&
            afterFix.codes.length === 1 &&
            afterFix.codes[0] === GHOST_B &&
            !afterFix.text.includes(GHOST_A),
        msg,
        wantHit,
        wantCount,
        afterFix,
    };
}

// ── ④ 坏效期不许进流水(前端最后一道)─────────────────────────────────────
// 会出事的输入:把一串条码用【人手速度】打进效期框(每字符 260ms → 楔子每个字符各自收尾,
// 一次回调都不发)。这条路绕过扫码那一层的全部判据,13 位数字原样落进 date 控件 —— 效期变成
// 49012-03-31,提交出去后端照收,那批货从此永远不进近效期名单、FEFO 永远把它排在最后。
// 枪速那一档已经被 ② 的还原收掉了,所以这一例专挑楔子看不见的速度:提交闸是最后一道。
async function badExpiryBlocked(browser, origin) {
    const { page, state } = await openModal(browser, origin);
    await gun(page, MILK);
    await quiet(
        page,
        () => document.querySelector('#inv-in-mask-rows [data-k="qty"]').value === '1'
    );
    const dateBox = page.locator('#inv-in-mask-rows [data-k="expiry_date"]').first();
    // 批次格没露出来就填不进去(旧行为下会这样)。这里不许崩:崩掉 30 秒超时会把「这一单带着
    // 坏日期进了流水」这条真正要看的证据挡住。
    const beforeFill = await page.evaluate(rows);
    if (beforeFill[0].batchCellShown) {
        await page.locator('#inv-in-mask-rows [data-k="batch_no"]').first().fill('L-9');
    }
    await clickDateBox(dateBox);
    await page.keyboard.type(MILK, { delay: HUMAN_MS });
    const wrecked = await page.evaluate(
        () => document.querySelector('#inv-in-mask-rows [data-k="expiry_date"]').value
    );

    await page.locator('#inv-in-mask-submit').click();
    await page.waitForTimeout(400);
    const err = await page.evaluate(() => {
        const box = document.getElementById('inv-in-mask-err');
        return {
            text: box ? box.textContent : null,
            open: document.getElementById('inv-in-mask').classList.contains('show'),
        };
    });
    await shot(page, '05-bad-expiry-blocked.png');
    const want = await copyOf(page, 'inv-err-bad-expiry');

    // 改回一个正常日期 → 这一单必须还能提交出去(闸不能把人堵死在这里)。
    // 闸没拦住时弹窗已经关了、行也没了,这一步得跳过 —— 否则一条干净的 FAIL 会变成 30 秒超时
    // 崩溃,红在哪反而看不见(要看的正是那一单带着坏日期进了流水)。
    if (err.open) {
        await dateBox.fill('2027-01-31');
        await submitIn(page);
    }
    await page.close();

    const line = ((state.posted[0] || {}).lines || [])[0] || {};
    return {
        ok:
            // 前提:这一串真把日期打成了 5 位年份(不是脚本自己塞进去的常量)
            /^\d{5,}-\d{2}-\d{2}$/.test(wrecked) &&
            // 拦住了:一条都没发出去,弹窗还开着,话是真词典里的人话
            err.open === true &&
            err.text === want &&
            state.posted.length === 1 &&
            line.expiry_date === '2027-01-31',
        wrecked,
        beforeFill,
        err,
        want,
        posted: state.posted,
    };
}

(async () => {
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch();
    const failed = await runCases(
        [
            ['freshProduct', freshProduct],
            ['gunFromDateField', gunFromDateField],
            ['failuresSurvive', failuresSurvive],
            ['badExpiryBlocked', badExpiryBlocked],
        ],
        (fn) => fn(browser, origin),
        path.join(SHOTS, 'report.json')
    );
    await browser.close();
    server.close();
    process.exit(failed ? 1 : 0);
})().catch((e) => {
    console.error('VERIFY CRASH', e);
    process.exit(2);
});
