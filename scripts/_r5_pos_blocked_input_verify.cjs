/*
 * scripts/_r5_pos_blocked_input_verify.cjs · 收下了却没进车的那一发,屏上到底有没有字
 *
 * 病:pos-scan.js 的页面级订阅者对「弹窗开着」那一档是 `return;` —— 一声不吭。收款弹窗开着
 * 正是最后一件货最容易被补扫的时刻:枪响了、灯闪了,而 toast 没有、失败清单 0 条、连查码
 * 请求都没发。店员没有任何办法知道这一件没算进去。
 *
 * 每一条都量两个方向,只量正向就是上一轮的错法(「别记成两件」量得很细,「还认不认第二件」
 * 一个数都没量过):
 *   正向  屏上真有字 —— 读 #pos-toast 的真文本 + 真 opacity(class 加上了而 opacity 还是 0
 *         等于屏上什么都没有)、读失败清单里那一行的码与指路句。
 *   反向  说了不许顺手办事 —— 收款期间不许发查码请求、车与应付分文不动、不许遮住 #pay-due
 *         或收款按钮(几何交叠面积,不是 z-index)、不许抢焦点;店员回头补扫时那笔欠账要销掉
 *         (留着就是「这件没进车」而车里明明有它 = 收两遍钱)。
 *
 * 验收陷阱(第四轮自己踩过):扫第二发时上一发的 toast 还挂在屏上(2600ms 才自收),读到它
 * 就会误判「有反馈」。所以「扫之前 toast 必须是空的」是前提断言,不是等一等就算了。
 *
 * 手打那一档(onTyped)收银台今天没有框声明接枪,所以那一例由脚本在运行期给 #main-search 加
 * data-enable-barcode="gun" —— 声明是测试注入的,被验的行为(楔子判成人在打字 → 收银台说不说
 * 话)是真产品的。两把尺子同时量,把这一串真的落在「人手速度」那一档里当证据交出来。
 *
 * 跑法(仓库根目录):node scripts/_r5_pos_blocked_input_verify.cjs [用例名]
 * 退出码 0 = 全过。截图落 tests/e2e/_artifacts/pos_barcode_scan/r5/。
 */
const path = require('path');
const { chromium } = require('@playwright/test');
const {
    ROOT,
    DESKTOP,
    serve,
    armTwoRulers,
    readTwoRulers,
    shotter,
    runCases,
} = require('./_gun_wedge_lib.cjs');

const ONLY = process.argv[2] || '';
const SHOTS = path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/r5');
const shot = shotter(SHOTS);

const COLA = '8850999320014';
// 后台没建档的码:用来在【本轮改动之外】的那条路上记一笔欠账(见用例②)。
const GHOST = '8850111000039';
// 人手速度:> 楔子的 GUN_MAX_GAP_MS(50)所以判不成枪,< MAX_GAP_MS(150)所以整串仍是一发。
// 这两个数之间正是「慢枪 / 人手」分不开的那一档 —— 楔子宁可判人手,代价由 onTyped 兜。
const HAND_GAP = 100;

const POS_SEED = () => {
    localStorage.setItem('pos_store_token', 'r5-blocked');
    localStorage.setItem('pos_store_name', 'ร้าน BLOCKED');
    localStorage.setItem('mrpilot_lang', 'th');
};

const COLA_ITEM = {
    id: 'p-cola',
    name: { th: 'โค้ก', en: 'Coke', zh: '可乐', ja: 'コーラ' },
    category_id: 1,
    base_unit: 'ขวด',
    base_price: '15.00',
    image_url: null,
    vat_applicable: true,
    units: [
        { unit_name: 'ขวด', factor: '1.000', barcode: COLA, price: '15.00', default_sell: true },
    ],
    track_batch: false,
    is_weighed: false,
    stock: { qty_base: '48.000', near_expiry: false },
    matched_unit: 'ขวด',
};

// 桌面档:手机档购物车是底部抽屉,「收款」要先展开抽屉才点得到,与本脚本要验的事无关。
async function posBoot(browser, origin, bag) {
    const page = await browser.newPage({ viewport: DESKTOP });
    await page.addInitScript(POS_SEED);
    await page.route('**/api/pos/products/by-barcode*', async (route) => {
        const code = new URL(route.request().url()).searchParams.get('code');
        bag.asked.push(code);
        const hit = code === COLA;
        await route.fulfill({
            status: hit ? 200 : 404,
            contentType: 'application/json',
            body: JSON.stringify(
                hit
                    ? { ok: true, data: COLA_ITEM }
                    : { ok: false, error: { code: 'pos.product_not_found', detail: null } }
            ),
        });
    });
    await page.goto(`${origin}/static/pos/pos.html`);
    await page.waitForSelector('#login-cashiers .ca', { timeout: 20000 });
    for (const d of ['1', '2', '3', '4']) await page.click(`#view-login .pad .k[data-pin="${d}"]`);
    await page.waitForSelector('#shift-mask.show', { timeout: 10000 });
    await page.click('#shift-open-go');
    await page.waitForSelector('#view-main.is-active', { timeout: 10000 });
    await page.waitForSelector('#main-grid .prod', { timeout: 10000 });
    return page;
}

const gun = (page, code) =>
    page.keyboard.type(code, { delay: 6 }).then(() => page.keyboard.press('Enter'));

// 屏上到底有没有这句话。class 不算数:.pos-toast 靠 opacity 过渡,class 加上而 opacity 还是 0
// 时店员什么都看不到。文本、透明度、盒子一起交出来。
const toastState = (page) =>
    page.evaluate(() => {
        const el = document.getElementById('pos-toast');
        const cs = getComputedStyle(el);
        const b = el.getBoundingClientRect();
        return {
            shown: el.classList.contains('show'),
            error: el.classList.contains('error'),
            opacity: Number(cs.opacity),
            pointerEvents: cs.pointerEvents,
            text: document.getElementById('pos-toast-txt').textContent,
            rect: { x: b.x, y: b.y, w: b.width, h: b.height },
        };
    });

// 那句话旁边那个图标现在画的是哪个字形。断 classList.contains('error') 只证明标记挂上了,
// 证不了店员看见的是什么 —— 收银台的 toast 图标是写死在 pos.html 里的一枚 ✓,红档只换底色
// 不换字形,于是「没加进购物车」旁边照样立着一个对勾。取渲染出来的 d 与 currentColor。
const toastIcon = (page) =>
    page.evaluate(() => {
        const svg = document.querySelector('#pos-toast .ic');
        const p = svg && svg.querySelector('path');
        const bar = document.getElementById('pos-toast');
        return {
            d: p ? p.getAttribute('d') : '',
            stroke: svg ? getComputedStyle(svg).color : '',
            bg: getComputedStyle(bar).backgroundColor,
        };
    });

const failRows = (page) =>
    page.evaluate(() =>
        [...document.querySelectorAll('#bscan-fails .bscan-fail')].map((r) => ({
            code: (
                r.querySelector('.bscan-code') ||
                r.querySelector('.bscan-fail-code') || { textContent: '' }
            ).textContent.trim(),
            text: r.textContent,
        }))
    );

// 收款窗那一侧此刻的样子:金额的字与它的盒子、按钮的盒子、焦点落在哪、车里几件。
const payScene = (page) =>
    page.evaluate(() => {
        const box = (sel) => {
            const el = document.querySelector(sel);
            if (!el) return null;
            const b = el.getBoundingClientRect();
            return { x: b.x, y: b.y, w: b.width, h: b.height };
        };
        const el = document.activeElement;
        return {
            payShown: document.getElementById('pay-mask').classList.contains('show'),
            due: document.getElementById('pay-due').textContent,
            grand: document.getElementById('cart-grand').textContent,
            qtys: [...document.querySelectorAll('#cart-lines .q[data-qi]')].map(
                (e) => e.textContent
            ),
            dueBox: box('#pay-due'),
            modalBox: box('#pay-mask .modal'),
            confirmBox: box('#pay-cash-confirm'),
            focus: ((el && el.tagName) || '') + '#' + ((el && el.id) || ''),
        };
    });

// 两个盒子叠了多少 px²。z-index / getComputedStyle 答不了「有没有挡住金额」—— 只有真排版下的
// 几何答得了(而 .pos-toast 是 pointer-events:none,elementFromPoint 这条路在它身上失效)。
function overlap(a, b) {
    if (!a || !b) return -1;
    const w = Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x));
    const h = Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y));
    return Math.round(w * h);
}

const sameBox = (a, b) => !!a && !!b && a.x === b.x && a.y === b.y && a.w === b.w && a.h === b.h;

// 前提断言:上一发的 toast 必须已经退场。读到它就会把「有反馈」判绿,而那正是这条 bug 骗人
// 的方式(第四轮头一版就是这么绿的)。
async function waitToastGone(page) {
    await page.waitForFunction(
        () => !document.getElementById('pos-toast').classList.contains('show'),
        null,
        { timeout: 8000 }
    );
    return toastState(page);
}

// ── ① 收款弹窗开着时扫一发:说了没有 / 说了会不会碍事 ────────────────────────
async function payModalScanSpeaksUp(browser, origin) {
    const bag = { asked: [] };
    const page = await posBoot(browser, origin, bag);
    await gun(page, COLA);
    await page.waitForFunction(
        () => document.querySelectorAll('#cart-lines .q[data-qi]').length === 1,
        null,
        { timeout: 8000 }
    );
    await page.click('#cart-pay-btn');
    await page.waitForSelector('#pay-mask.show', { timeout: 10000 });

    const before = await waitToastGone(page); // 前提:屏上此刻没有任何 toast
    const sceneBefore = await payScene(page);
    bag.asked.length = 0;

    // 这一发到底是不是一发:主线程偶尔卡出 >150ms 的坎时楔子会把它断成两串,那时屏上的字
    // 是「半个码」而不是「没有字」—— 两种红的病因完全不同,量一把尺子就分得开(不是装饰)。
    await armTwoRulers(page);
    await gun(page, COLA);
    const ruler = await readTwoRulers(page);
    await page
        .waitForFunction(
            () => document.getElementById('pos-toast').classList.contains('show'),
            null,
            { timeout: 5000 }
        )
        .catch(() => {});
    await page.waitForTimeout(400); // 过渡 .25s:等 opacity 真的走完再量
    const toast = await toastState(page);
    const rows = await failRows(page);
    const sceneAfter = await payScene(page);
    const copy = await page.evaluate(() => window.POS_I18N.th);
    await shot(page, 'c1-pay-modal-scan-speaks-up.png');
    await page.close();

    const want = copy['posui.bscan.modal_busy'].replace('{code}', COLA);
    const spoke = toast.shown && toast.opacity > 0.9 && toast.text === want;
    const listed = rows.length === 1 && rows[0].code === COLA;
    const hinted = rows.length === 1 && rows[0].text.indexOf(copy['posui.bscan.modal_hint']) >= 0;
    const overDue = overlap(toast.rect, sceneAfter.dueBox);
    const overModal = overlap(toast.rect, sceneAfter.modalBox);
    const overConfirm = overlap(toast.rect, sceneAfter.confirmBox);
    const undisturbed =
        bag.asked.length === 0 &&
        sceneAfter.payShown &&
        sceneAfter.due === sceneBefore.due &&
        sceneAfter.grand === sceneBefore.grand &&
        sceneAfter.qtys.join(',') === sceneBefore.qtys.join(',') &&
        sceneAfter.focus === sceneBefore.focus &&
        sameBox(sceneAfter.dueBox, sceneBefore.dueBox) &&
        overDue === 0 &&
        overModal === 0 &&
        overConfirm === 0;
    // 一发 = 13 个字符 + 一个 Enter,且没有哪两下之间跨过楔子的断串线(150ms)。
    const oneBurst = ruler.n === COLA.length + 1 && ruler.stampMax <= 150;
    return {
        ok: before.shown === false && oneBurst && spoke && listed && hinted && undisturbed,
        staleToastShownBeforeScan: before.shown, // false = 屏上干净,这一绿不是读到上一发
        staleToastText: before.text,
        burst: { n: ruler.n, stampMax: ruler.stampMax, perfMax: ruler.perfMax },
        toast,
        wantText: want,
        rows,
        askedDuringModal: bag.asked,
        sceneBefore,
        sceneAfter,
        overlapPx: { due: overDue, modal: overModal, confirm: overConfirm },
        why: !oneBurst
            ? `量测环境问题,不是产品的红:这一发被拆开了(${ruler.n} 下按键 · 最大间隔 ` +
              `${ruler.stampMax}ms > 楔子的 150ms),屏上出现的会是半个码`
            : !spoke
              ? '收款弹窗开着时扫的那一发没在屏上留下字:枪响了灯闪了,店员没办法知道这件货没算进去'
              : !listed || !hinted
                ? '当下说了,但回头找不到是哪一个码 / 没告诉店员怎么补'
                : !undisturbed
                  ? '反馈干扰了收款本身(遮住金额或按钮 / 抢了焦点 / 动了车)'
                  : '',
    };
}

// 弹窗上的每一格点到的是谁。清单原来 z=70 压在弹窗(50)之上,它在流里又横跨整个商品列 ——
// 收款窗的关闭键正好落在它下面,真浏览器里点不动(Playwright 报 intercepts pointer events)。
// 类名、z-index、getComputedStyle 都答不了这个问题,只有真排版下的命中测试答得了。
async function stolenByList(page, selector, steps) {
    return page.evaluate(
        ({ sel, n }) => {
            const el = document.querySelector(sel);
            const list = document.getElementById('bscan-fails');
            if (!el || !list) return null;
            const b = el.getBoundingClientRect();
            let points = 0;
            let stolen = 0;
            for (let i = 0; i < n; i++) {
                for (let j = 0; j < n; j++) {
                    const x = b.left + (b.width * (i + 0.5)) / n;
                    const y = b.top + (b.height * (j + 0.5)) / n;
                    const hit = document.elementFromPoint(x, y);
                    points += 1;
                    if (hit && (hit === list || list.contains(hit))) stolen += 1;
                }
            }
            return { points, stolen };
        },
        { sel: selector, n: steps }
    );
}

// ── ② 清单一格都不许压在收款窗上 ─────────────────────────────────────────────
// 清单欠着账时店员照样要收钱(那几件货本来就在等他处理完这一单)。清单原来 z=70 压过弹窗
// (50),在流里又横跨整个商品列,收款窗的关闭键正落在它下面 —— 点不动。这条的欠账用「扫了
// 个没建档的码」来记:那条路本来就有,与本轮改动无关,所以它在改动前后都成立,是把可比的尺子。
async function listNeverBlocksPay(browser, origin) {
    const bag = { asked: [] };
    const page = await posBoot(browser, origin, bag);
    await gun(page, COLA);
    await page.waitForFunction(
        () => document.querySelectorAll('#cart-lines .q[data-qi]').length === 1,
        null,
        { timeout: 8000 }
    );
    await gun(page, GHOST); // 后台没建档 → 清单记一笔(既有的那条路)
    await page.waitForFunction(
        () => document.querySelectorAll('#bscan-fails .bscan-fail').length === 1,
        null,
        { timeout: 8000 }
    );
    await page.click('#cart-pay-btn');
    await page.waitForSelector('#pay-mask.show', { timeout: 10000 });
    const blocked = await failRows(page);
    const modalHits = await stolenByList(page, '#pay-mask .modal', 6);
    const closeHits = await stolenByList(page, '#pay-close-btn', 3);
    const confirmHits = await stolenByList(page, '#pay-cash-confirm', 3);
    await shot(page, 'c2-list-behind-pay-modal.png');

    // 真点一下关闭键:能不能点得动是这条的终审(Playwright 的可操作性检查会把被接走的点击
    // 卡到超时 —— 那正是清单压在弹窗上时的表现)。
    let closeClicked = true;
    await page.click('#pay-close-btn', { timeout: 8000 }).catch(() => (closeClicked = false));
    if (closeClicked) {
        await page
            .waitForFunction(
                () => !document.getElementById('pay-mask').classList.contains('show'),
                null,
                { timeout: 5000 }
            )
            .catch(() => (closeClicked = false));
    }
    const rows = await failRows(page);
    await page.close();

    const layered = modalHits.stolen === 0 && closeHits.stolen === 0 && confirmHits.stolen === 0;
    const ok = blocked.length === 1 && layered && closeClicked && rows.length === 1;
    return {
        ok,
        seededRows: blocked,
        modalHits,
        closeHits,
        confirmHits,
        closeClicked,
        rowsAfter: rows,
        why: ok
            ? ''
            : !layered || !closeClicked
              ? `失败清单压在收款窗上:弹窗 ${modalHits.stolen}/${modalHits.points} 个采样点被它` +
                `接走 · 关闭键点${closeClicked ? '得动' : '不动'}`
              : `判据前提不成立:清单开窗前 ${blocked.length} 条 / 关窗后 ${rows.length} 条`,
    };
}

// ── ③ 关掉窗口回头补扫:货进车,那笔欠账跟着销 ───────────────────────────────
// 反向的另一半。清单留着说「这件没进车」而车里明明有它,店员照着再补一件就是收两遍钱 ——
// 上一轮栽的正是只量了其中一侧。
async function rescanAfterCloseAddsOnce(browser, origin) {
    const bag = { asked: [] };
    const page = await posBoot(browser, origin, bag);
    await gun(page, COLA);
    await page.waitForFunction(
        () => document.querySelectorAll('#cart-lines .q[data-qi]').length === 1,
        null,
        { timeout: 8000 }
    );
    await page.click('#cart-pay-btn');
    await page.waitForSelector('#pay-mask.show', { timeout: 10000 });
    await waitToastGone(page);
    await gun(page, COLA); // 这一发被挡下 → 清单欠一笔
    await page.waitForTimeout(500);
    const blocked = await failRows(page);

    await page.click('#pay-close-btn');
    await page.waitForFunction(
        () => !document.getElementById('pay-mask').classList.contains('show'),
        null,
        { timeout: 5000 }
    );
    bag.asked.length = 0;
    await gun(page, COLA);
    await page.waitForTimeout(800);
    const after = await payScene(page);
    const rows = await failRows(page);
    await shot(page, 'c3-rescan-after-close.png');
    await page.close();

    const ok =
        blocked.length === 1 &&
        bag.asked.join(',') === COLA &&
        after.qtys.join(',') === '2' &&
        rows.length === 0;
    return {
        ok,
        blockedRows: blocked,
        askedOnRescan: bag.asked,
        qtysAfter: after.qtys,
        rowsAfter: rows,
        why: ok
            ? ''
            : !blocked.length
              ? '收款窗开着时那一发连条记录都没有 —— 回头没人知道欠的是哪一件'
              : rows.length
                ? '货已经在车里了,清单还挂着「这件没进车」—— 店员照着补一件就是收两遍钱'
                : `补扫这条路被弄坏了:查码 ${JSON.stringify(bag.asked)} · 车里数量 ${after.qtys}`,
    };
}

// ── ④ 楔子判成「人在打字」的那一发(onTyped)──────────────────────────────────
// 收银台今天没有框声明接枪,声明由脚本注入;被验的是真楔子的判据 + 真收银台的反应。
async function typedBurstSpeaksUp(browser, origin) {
    const bag = { asked: [] };
    const page = await posBoot(browser, origin, bag);
    await page.evaluate(() => {
        const el = document.getElementById('main-search');
        el.setAttribute('data-enable-barcode', 'gun');
        el.focus();
    });
    await armTwoRulers(page);
    await page.keyboard.type(COLA, { delay: HAND_GAP });
    await page.keyboard.press('Enter');
    const ruler = await readTwoRulers(page);
    await page.waitForTimeout(500);
    const toast = await toastState(page);
    const rows = await failRows(page);
    const copy = await page.evaluate(() => window.POS_I18N.th);
    const kept = await page.inputValue('#main-search');
    await shot(page, 'c4-typed-burst-speaks-up.png');

    // 反向:数量框里打个 240 这种短串不在此列,不许打扰。等上一发退场再打,免得读到它。
    await waitToastGone(page);
    const rowsBeforeShort = (await failRows(page)).length;
    await page.keyboard.type('240', { delay: HAND_GAP });
    await page.keyboard.press('Enter');
    await page.waitForTimeout(600);
    const shortToast = await toastState(page);
    const rowsAfterShort = await failRows(page);
    await shot(page, 'c5-short-typing-stays-quiet.png');
    await page.close();

    const want = copy['posui.bscan.typed'].replace('{code}', COLA);
    // 前提:这一串真的落在「人手」那一档 —— 判不成枪(gap > 50)且没被拆成两发(gap ≤ 150)
    const inHandBand = ruler.stampMax > 50 && ruler.stampMax <= 150 && ruler.n === COLA.length + 1;
    const spoke = toast.shown && toast.opacity > 0.9 && toast.text === want;
    const listed = rows.length === 1 && rows[0].code === COLA;
    const notLookedUp = bag.asked.length === 0;
    const keptTyping = kept.indexOf(COLA) >= 0; // 人打的那串归人,楔子和收银台都不许动它
    const quietOnShort = !shortToast.shown && rowsAfterShort.length === rowsBeforeShort;
    return {
        ok: inHandBand && spoke && listed && notLookedUp && keptTyping && quietOnShort,
        ruler: { n: ruler.n, stampMax: ruler.stampMax, perfMax: ruler.perfMax },
        inHandBand,
        toast,
        wantText: want,
        rows,
        askedDuringTyping: bag.asked,
        searchBoxKept: kept,
        shortBurst: { toastShown: shortToast.shown, rowsBefore: rowsBeforeShort, rowsAfterShort },
        why: !inHandBand
            ? `判据前提不成立:这一串的最大间隔 ${ruler.stampMax}ms / ${ruler.n} 发,没落在人手那一档`
            : !spoke || !listed
              ? '楔子把这一发判给了人,收银台一声不吭 —— 慢枪扫的那件货就这么没了'
              : !notLookedUp
                ? '把判成手打的那一串又拿去查码了 = 推翻了「人在打字」这个结论'
                : !quietOnShort
                  ? '店员往框里打个短串也弹提示 = 这一路成了骚扰'
                  : '',
    };
}

// ── ⑤ 说了没进车,长得能不能跟「已加入」分开 ──────────────────────────────────
// 收款窗开着时清单在弹窗后面(z 47 < 50,②那条正是这么定的),所以当下唯一的通道就是这句
// toast。它要是长得像「已加入」,这条修复等于没做:店员抬头一眼扫过就当加上了,那件货照样
// 跟着顾客出门 —— 只是这次屏上还留了个证据说他被告知过。
// 三句话在同一页里量,顺序不能反:成功 → 没进车 → 再成功。第三句是反向 —— 红档标记设了不收
// 的话,此后每一句「已加入」都戴着出事的脸,店员很快就学会不看它了。
async function notAddedLooksNothingLikeAdded(browser, origin) {
    const bag = { asked: [] };
    const page = await posBoot(browser, origin, bag);
    await gun(page, COLA);
    await page.waitForFunction(
        () => document.querySelectorAll('#cart-lines .q[data-qi]').length === 1,
        null,
        { timeout: 8000 }
    );
    await page.waitForTimeout(400);
    const okIcon = await toastIcon(page);
    const okToast = await toastState(page);
    await shot(page, 'c6-added-look.png');

    await page.click('#cart-pay-btn');
    await page.waitForSelector('#pay-mask.show', { timeout: 10000 });
    const gapA = await waitToastGone(page); // 前提:量下一句之前上一句必须已经退场
    await gun(page, COLA);
    await page
        .waitForFunction(
            () => document.getElementById('pos-toast').classList.contains('show'),
            null,
            {
                timeout: 5000,
            }
        )
        .catch(() => {});
    await page.waitForTimeout(400);
    const errIcon = await toastIcon(page);
    const errToast = await toastState(page);
    await shot(page, 'c7-not-added-look.png');

    await page.click('#pay-close-btn');
    await page.waitForFunction(
        () => !document.getElementById('pay-mask').classList.contains('show'),
        null,
        { timeout: 5000 }
    );
    const gapB = await waitToastGone(page);
    await gun(page, COLA);
    await page.waitForFunction(
        () => (document.querySelectorAll('#cart-lines .q[data-qi]')[0] || {}).textContent === '2',
        null,
        { timeout: 8000 }
    );
    await page.waitForTimeout(400);
    const backIcon = await toastIcon(page);
    const backToast = await toastState(page);
    const rows = await failRows(page);
    await shot(page, 'c8-added-look-again.png');
    await page.close();

    const clean = gapA.shown === false && gapB.shown === false;
    const glyphDiffers = !!okIcon.d && !!errIcon.d && okIcon.d !== errIcon.d;
    const colorDiffers = okIcon.stroke !== errIcon.stroke && okIcon.bg !== errIcon.bg;
    const restored =
        backIcon.d === okIcon.d &&
        backIcon.stroke === okIcon.stroke &&
        backIcon.bg === okIcon.bg &&
        backToast.error === false &&
        rows.length === 0;
    const textsDiffer = okToast.text !== errToast.text && errToast.error === true;
    return {
        ok: clean && glyphDiffers && colorDiffers && restored && textsDiffer,
        // false = 量下一句之前屏上是干净的(两个 false 才说明这三句是三句,不是同一句读了三遍)
        staleToastShownBetween: { beforeErr: gapA.shown, beforeBack: gapB.shown },
        added: { icon: okIcon, text: okToast.text, error: okToast.error },
        notAdded: { icon: errIcon, text: errToast.text, error: errToast.error },
        addedAgain: { icon: backIcon, text: backToast.text, error: backToast.error },
        rowsAfter: rows,
        why: !clean
            ? '量到的是上一句还没退场的 toast —— 这条判据自己先假绿了'
            : !glyphDiffers
              ? `「没加进购物车」旁边画的还是「已加入」那个字形(${errIcon.d})· 一眼扫过去仍是办好了`
              : !colorDiffers
                ? '两句话的底色/图标颜色一模一样'
                : !restored
                  ? '红档的脸没收回去:此后每一句「已加入」都戴着出事的脸'
                  : !textsDiffer
                    ? '两句话的文字没分开'
                    : '',
    };
}

const CASES = [
    ['c1_payModalScanSpeaksUp', payModalScanSpeaksUp],
    ['c2_listNeverBlocksPay', listNeverBlocksPay],
    ['c3_rescanAfterCloseAddsOnce', rescanAfterCloseAddsOnce],
    ['c4_typedBurstSpeaksUp', typedBurstSpeaksUp],
    ['c5_notAddedLooksNothingLikeAdded', notAddedLooksNothingLikeAdded],
];

(async () => {
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch();
    let failed = 0;
    try {
        failed = await runCases(
            CASES.filter(([n]) => !ONLY || n.indexOf(ONLY) >= 0),
            (fn) => fn(browser, origin),
            path.join(SHOTS, 'report-r5-blocked-input.json')
        );
    } finally {
        await browser.close();
        server.close();
    }
    process.exit(failed ? 1 : 0);
})().catch((e) => {
    console.error('R5 POS BLOCKED INPUT CRASH', e);
    process.exit(2);
});
