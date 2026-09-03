/*
 * scripts/_gun_wedge_pos_verify.cjs · 收银主屏的条码枪真浏览器验收
 *
 * 枪的物理行为 = 极快地敲一串字符 + 一个 Enter。所以全程只用真键盘(keyboard.type +
 * press('Enter')),不用 fill():fill 直接改 value,楔子的 keydown 一个都收不到,那种绿是
 * 假的。每次扫之前先记 document.activeElement —— 「焦点在不在输入框」是楔子唯一的判据。
 *
 * 真的东西:static/pos/pos.html + static/dist/pos.js(含 pos-scan.js 与常驻楔子),文案取真
 * static/pos/pos-i18n.js(不注入任何字典 —— 注入过的字典验出来的文案不算数)。桩只有
 * /api/pos/**:by-barcode 由测控制并计数(「有没有被当成扫码」的硬证据),其余 404 让 POS
 * 走它自己的纯本地预览目录。
 *
 * 用法(仓库根目录):node scripts/_gun_wedge_pos_verify.cjs [截图目录]
 * 退出码 0 = 全过。截图默认落 tests/e2e/_artifacts/pos_barcode_scan/。
 */
const path = require('path');
const { chromium } = require('@playwright/test');
const {
    ROOT,
    PHONE,
    DESKTOP,
    BOX,
    BOTTLE,
    GUN_DELAY,
    HUMAN_DELAY,
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
const COKE_NAME = 'โค้ก 325ml / Coke 325ml / 可乐 325ml / コーラ 325ml';

// ── POS(收银主屏)────────────────────────────────────────────────────────
function posSeed() {
    localStorage.setItem('pos_store_token', 'gun-verify');
    localStorage.setItem('pos_store_name', 'ร้าน GUN');
    localStorage.setItem('mrpilot_lang', 'zh'); // 断言对着真 zh 字典,不注入任何文案
}

function posProduct(unit) {
    return {
        id: 'gun-coke',
        name: { th: 'โค้ก 325ml', en: 'Coke 325ml', zh: '可乐 325ml', ja: 'コーラ 325ml' },
        category_id: 1,
        base_unit: 'ขวด',
        image_url: null,
        vat_applicable: true,
        units: [
            {
                unit_name: 'ขวด',
                factor: '1.000',
                barcode: BOTTLE,
                price: '15.00',
                default_sell: true,
            },
            { unit_name: 'ลัง', factor: '24.000', barcode: BOX, price: '350.00' },
        ],
        track_batch: false,
        is_weighed: false,
        stock: { qty_base: '48.000', near_expiry: false },
        matched_unit: unit,
    };
}

// 取件口由测控制;计数器是「有没有被当成扫码」的硬证据(不触发 = 一次请求都不该发出去)
async function routePos(page) {
    const hits = [];
    await page.route('**/api/pos/products/by-barcode*', (route) => {
        const code = new URL(route.request().url()).searchParams.get('code');
        hits.push(code);
        const unit = code === BOX ? 'ลัง' : code === BOTTLE ? 'ขวด' : null;
        route.fulfill({
            status: unit ? 200 : 404,
            contentType: 'application/json',
            body: JSON.stringify(
                unit
                    ? { ok: true, data: posProduct(unit) }
                    : { ok: false, error: { code: 'pos.product_not_found', detail: null } }
            ),
        });
    });
    return hits;
}

async function posLogin(page, origin) {
    await page.goto(`${origin}/static/pos/pos.html`);
    await page.waitForSelector('#login-cashiers .ca', { timeout: 15000 });
    for (const d of ['1', '2', '3', '4']) {
        await page.click(`#view-login .pad .k[data-pin="${d}"]`);
    }
    await page.waitForSelector('#shift-mask.show', { timeout: 10000 });
    await page.click('#shift-open-go');
    await page.waitForSelector('#view-main.is-active', { timeout: 10000 });
    await page.waitForSelector('#main-grid .prod', { timeout: 10000 });
}

async function openPos(browser, origin, opts) {
    const page = await browser.newPage(opts || { viewport: PHONE });
    await page.addInitScript(posSeed);
    const hits = await routePos(page);
    await posLogin(page, origin);
    return { page, hits };
}

function cartState() {
    const lines = [...document.querySelectorAll('#cart-lines .line')];
    return {
        lineCount: lines.length,
        qtys: lines.map((l) => l.querySelector('.q[data-qi]').textContent),
        names: lines.map((l) => l.querySelector('.li-nm .n').textContent),
        grand: document.getElementById('cart-grand').textContent,
        sub: document.getElementById('cart-sub').textContent,
        search: document.getElementById('main-search').value,
    };
}

// ── ① 主屏扫枪进车 · ② 同码连扫 = 数量 2 不是两行 ────────────────────────
async function posCart(browser, origin) {
    const { page, hits } = await openPos(browser, origin);
    const focus1 = await gun(page, BOX);
    await page.waitForFunction(() => document.querySelectorAll('#cart-lines .line').length === 1, {
        timeout: 8000,
    });
    await page.waitForFunction(
        () => parseFloat(getComputedStyle(document.getElementById('pos-toast')).opacity) > 0.9,
        null,
        { timeout: 3000 }
    );
    const first = await page.evaluate(cartState);
    const toast = await page.evaluate(() => ({
        txt: document.getElementById('pos-toast-txt').textContent,
        opacity: getComputedStyle(document.getElementById('pos-toast')).opacity,
    }));
    await shot(page, '01-pos-gun-first-hit.png');

    // 同一个码再扫一次:数量该变 2,不是长出第二行
    const focus2 = await gun(page, BOX);
    await page.waitForFunction(
        () => document.querySelector('#cart-lines .q[data-qi]').textContent === '2',
        null,
        { timeout: 8000 }
    );
    const second = await page.evaluate(cartState);
    // 手机档购物车是底部抽屉:不展开的话截图上只看得见「2 件 ฿700」,看不见「一行 ×2」这件事。
    // 展开后再问一遍这一行是不是真画在视口里(有 class 不等于看得见)。
    await page.click('#cart-peek');
    const lineVisible = await page.locator('#cart-lines .line').first().isVisible();
    // 抽屉是 transform 滑上来的:立刻量到的是动画中间态。等它停稳(位置连续两帧不变)再问。
    await page
        .waitForFunction(
            () => {
                const b = document.querySelector('#cart-lines .line').getBoundingClientRect();
                const last = window.__lastTop;
                window.__lastTop = b.top;
                return last === b.top && b.top >= 0 && b.bottom <= innerHeight;
            },
            null,
            { timeout: 3000, polling: 100 }
        )
        .catch(() => undefined);
    const lineBox = await page.evaluate(() => {
        const el = document.querySelector('#cart-lines .line');
        const b = el.getBoundingClientRect();
        const q = el.querySelector('.q[data-qi]');
        const qb = q.getBoundingClientRect();
        // 「画在屏上」的最后一问:这一行中心点最上面那层是不是它自己(不是被别的层压住)
        const top = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2);
        return {
            h: b.height,
            inView: b.top >= 0 && b.bottom <= innerHeight,
            onTop: !!(top && el.contains(top)),
            qtyText: q.textContent,
            qtyVisible: qb.width > 0 && qb.height > 0,
            opacity: getComputedStyle(el).opacity,
        };
    });
    await shot(page, '02-pos-gun-same-code-qty2.png');

    // 反证:换成同一件货的瓶码 → 该是两行(否则「就一行」可能只是购物车压根不长行)
    await gun(page, BOTTLE);
    await page.waitForFunction(() => document.querySelectorAll('#cart-lines .line').length === 2, {
        timeout: 8000,
    });
    const third = await page.evaluate(cartState);
    await shot(page, '03-pos-gun-bottle-code-second-line.png');
    await page.close();

    return {
        ok:
            notInField(focus1) && // 焦点不在输入框 = 楦子该收
            notInField(focus2) &&
            first.lineCount === 1 &&
            first.qtys[0] === '1' &&
            first.grand === '350.00' && // 扫箱码按箱价,不是默认瓶价 15
            toast.txt === '已加入 ' + COKE_NAME && // 真 zh 字典,未注入
            parseFloat(toast.opacity) > 0.9 &&
            second.lineCount === 1 &&
            second.qtys[0] === '2' &&
            second.grand === '700.00' &&
            lineVisible &&
            lineBox.inView &&
            lineBox.onTop &&
            lineBox.qtyText === '2' &&
            lineBox.qtyVisible &&
            lineBox.opacity === '1' &&
            third.lineCount === 2 &&
            third.grand === '715.00' &&
            hits.join(',') === [BOX, BOX, BOTTLE].join(','),
        focus1,
        focus2,
        first,
        second,
        lineVisible,
        lineBox,
        third,
        toast,
        hits,
    };
}

// ── ③ 搜索框里正常打字,楦子不许抢(回归保护)────────────────────────────
async function posSearchTyping(browser, origin) {
    const { page, hits } = await openPos(browser, origin);
    await page.click('#main-search');
    const focusIn = await page.evaluate(() => ({
        id: document.activeElement.id,
        tag: document.activeElement.tagName,
    }));
    // 人在搜商品:两个中文字
    await page.keyboard.type('可乐', { delay: 40 });
    const cn = await page.evaluate(() => ({
        value: document.getElementById('main-search').value,
        active: document.activeElement.id,
    }));
    await shot(page, '04-pos-search-cn-typed.png');
    // 再来一串「长得像条码」的:13 位数字打进搜索框,楦子照旧不许吃(枪速也不许)
    await page.locator('#main-search').selectText();
    await page.keyboard.type(BOX, { delay: GUN_DELAY });
    const digits = await page.evaluate(() => document.getElementById('main-search').value);
    await page.keyboard.press('Enter');
    await page.waitForTimeout(500); // 给楦子的 150ms 收尾窗 + 取件请求留出时间
    const after = await page.evaluate(cartState);
    const hitsWhileTyping = hits.length; // 控制组之前的读数才算「打字没触发取件」
    await shot(page, '05-pos-search-barcode-typed.png');

    // 控制组:把焦点挪出输入框(点「全部」分类)→ 同一串码必须能扫进车,
    // 证明上面的「没进车」是楦子让路,而不是这一页压根扫不了
    await page.click('#main-cats .cat[data-cat=""]');
    const focusOut = await page.evaluate(() => ({
        id: document.activeElement.id,
        tag: document.activeElement.tagName,
    }));
    await gun(page, BOX);
    await page.waitForFunction(() => document.querySelectorAll('#cart-lines .line').length === 1, {
        timeout: 8000,
    });
    const control = await page.evaluate(cartState);
    await shot(page, '06-pos-control-focus-out-scans.png');
    await page.close();

    return {
        ok:
            focusIn.id === 'main-search' &&
            focusIn.tag === 'INPUT' &&
            cn.value === '可乐' && // 中文真的落进框里,没被楦子吃掉
            cn.active === 'main-search' &&
            digits === BOX && // 13 位数字也没被吃
            after.lineCount === 0 && // 一件都没进车
            after.search === BOX &&
            hitsWhileTyping === 0 && // 取件口一次都没被调用
            notInField(focusOut) &&
            control.lineCount === 1 &&
            control.grand === '350.00' &&
            hits.length === 1,
        focusIn,
        cn,
        digits,
        after,
        hitsWhileTyping,
        focusOut,
        control,
        hits,
    };
}

// ── ④ 打字慢不算枪 · ⑤ 长度 < 3 不触发 ──────────────────────────────────
async function posNegatives(browser, origin) {
    const { page, hits } = await openPos(browser, origin);
    // 慢打(每字符 260ms > 150ms 阈值):焦点不在输入框,字符都到 document,但攒不成一串
    const slowFocus = await gun(page, BOX, HUMAN_DELAY);
    await page.waitForTimeout(600);
    const afterSlow = await page.evaluate(cartState);
    const slowHits = hits.length;
    await shot(page, '07-pos-slow-typing-no-trigger.png');

    // 两位数(< MIN_LENGTH=3)+ Enter:枪速也不许触发
    await gun(page, '12');
    await page.waitForTimeout(500);
    const afterShort = await page.evaluate(cartState);
    const shortHits = hits.length;
    await shot(page, '08-pos-short-code-no-trigger.png');

    // 控制组:同一页、同一个焦点,枪速全长码必须进车
    await gun(page, BOX);
    await page.waitForFunction(() => document.querySelectorAll('#cart-lines .line').length === 1, {
        timeout: 8000,
    });
    const control = await page.evaluate(cartState);
    await page.close();

    return {
        ok:
            notInField(slowFocus) &&
            afterSlow.lineCount === 0 &&
            slowHits === 0 &&
            afterShort.lineCount === 0 &&
            shortHits === 0 &&
            control.lineCount === 1 &&
            control.grand === '350.00' &&
            hits.length === 1,
        slowFocus,
        afterSlow,
        slowHits,
        afterShort,
        shortHits,
        control,
    };
}

// ── 「多慢才算人打字」这条线画在哪:拿真键盘从两边逼,别只信源码里的常数 ──────
async function posGapThreshold(browser, origin) {
    const { page, hits } = await openPos(browser, origin);
    const probe = [];
    // 阈值上方(每字符 170ms):字符间隔 > MAX_GAP_MS=150 → 每个字符各自收尾,攒不成码
    await gun(page, BOX, 170);
    await page.waitForTimeout(600);
    probe.push({ delay: 170, hits: hits.length });
    // 阈值下方(每字符 60ms):这已经是人手打不出的速度,该被当成枪
    await gun(page, BOX, 60);
    await page.waitForFunction(() => document.querySelectorAll('#cart-lines .line').length === 1, {
        timeout: 8000,
    });
    probe.push({ delay: 60, hits: hits.length });
    await page.close();
    return {
        ok: probe[0].hits === 0 && probe[1].hits === 1,
        probe,
        note: 'MAX_GAP_MS=150 · 170ms/字符不算枪,60ms/字符算',
    };
}

// ── ⑥ 收款弹窗开着时,枪扫的码不许偷偷进购物车(店员正在收钱)──────────────
// 不拿手输弹窗验:那张弹窗本身就是「扫/输条码」的入口(pos-cashier 的物理键盘加成会把枪的
// 数字喂给它、Enter 直接取件),枪落在那儿加货是对的,拿它验守门等于验错了对象。
async function posModalGuard(browser, origin) {
    // 桌面档:手机档的购物车是底部抽屉,收款键要先展开抽屉才点得到,与本例要验的事无关
    const { page, hits } = await openPos(browser, origin, { viewport: DESKTOP });
    await gun(page, BOX); // 先有一件货才能进收款
    await page.waitForFunction(() => document.querySelectorAll('#cart-lines .line').length === 1, {
        timeout: 8000,
    });
    await page.click('#cart-pay-btn');
    await page.waitForSelector('#pay-mask.show', { timeout: 5000 });
    const focus = await gun(page, BOX);
    await page.waitForTimeout(700);
    const state = await page.evaluate(() => ({
        lineCount: document.querySelectorAll('#cart-lines .line').length,
        qty: (document.querySelector('#cart-lines .q[data-qi]') || {}).textContent,
        grand: document.getElementById('cart-grand').textContent,
        payShown: document.getElementById('pay-mask').classList.contains('show'),
        payVisible: getComputedStyle(document.getElementById('pay-mask')).display !== 'none',
        payDue: document.getElementById('pay-due').textContent,
    }));
    await shot(page, '09-pos-pay-modal-gun-ignored.png');
    await page.close();
    return {
        ok:
            notInField(focus) && // 焦点不在输入框 → 楦子本来会收,是页面订阅者按 modalOpen 让开的
            state.lineCount === 1 &&
            state.qty === '1' && // 收款期间那一枪没把数量顶到 2
            state.grand === '350.00' &&
            state.payShown &&
            state.payVisible &&
            state.payDue === '350.00' &&
            hits.length === 1, // 只有开头那一次取件
        focus,
        state,
        hits,
    };
}

// ── ⑦ 安卓平板那条路:楦子会塞一个隐藏水槽 input 接键 ────────────────────
async function posTouchSink(browser, origin) {
    const { page, hits } = await openPos(browser, origin, { viewport: PHONE, hasTouch: true });
    const sink = await page.evaluate(() => {
        const el = document.querySelector('input.bscan-sink');
        if (!el) return null;
        const cs = getComputedStyle(el);
        return { inputmode: el.getAttribute('inputmode'), opacity: cs.opacity, w: cs.width };
    });
    const focus = await gun(page, BOX);
    await page.waitForFunction(() => document.querySelectorAll('#cart-lines .line').length === 1, {
        timeout: 8000,
    });
    const cart = await page.evaluate(cartState);
    const sinkAfter = await page.evaluate(() => {
        const el = document.querySelector('input.bscan-sink');
        return {
            value: el ? el.value : null,
            focused: !!(document.activeElement && document.activeElement === el),
        };
    });
    await shot(page, '10-pos-touch-sink-gun.png');
    await page.close();
    return {
        ok:
            !!sink &&
            sink.inputmode === 'none' && // 不弹系统软键盘
            sink.opacity === '0' &&
            cart.lineCount === 1 &&
            cart.grand === '350.00' &&
            sinkAfter.value === '' && // 收尾后清空,不给下一枪留残字
            hits.length === 1,
        sink,
        focus,
        cart,
        sinkAfter,
    };
}

(async () => {
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch();
    const failed = await runCases(
        [
            ['posCart', posCart],
            ['posSearchTyping', posSearchTyping],
            ['posNegatives', posNegatives],
            ['posGapThreshold', posGapThreshold],
            ['posModalGuard', posModalGuard],
            ['posTouchSink', posTouchSink],
        ],
        (fn) => fn(browser, origin),
        path.join(SHOTS, 'report-pos.json')
    );
    await browser.close();
    server.close();
    process.exit(failed ? 1 : 0);
})().catch((e) => {
    console.error('POS GUN VERIFY CRASH', e);
    process.exit(2);
});
