/*
 * scripts/_hostile_scan_cam_verify.cjs · 对抗素材验收(摄像头连扫去重 · 真相机真解码)
 *
 * 上一轮那份抖动素材是「清晰 19 帧 + 糊 11 帧」的固定周期 —— 读不出的帧永远连成整齐的一段。
 * 真机上手抖/对焦/反光是散着落的:偶尔连糊三帧,偶尔隔一帧就成。这一份改喂单帧成功率
 * p=0.8 / 0.6 / 0.5 的随机丢帧素材(seed 写死,丢帧位置随机而结论可复现),打的是同一条判据:
 * 「这个码离开过取景框没有」= 连着多少次采样没解出它(证据)+ 距最后一次解出它多久(物理),
 * 两把尺子都够才算离开(见 static/scan/scan-camera.js 里 sweep 上方)。素材自己把最长连续
 * 读不出印出来,三档都远在阈值以内 —— 越过那条线就该算真的离开,再断「只记一件」是在验一条
 * 不存在的规矩。
 *
 * 第二组(cam* 五条)验的是另一件事:【相机被系统收走之后屏上还说不说在扫】。收走的那一刻
 * <video> 停在最后一帧 —— readyState 仍是 4、videoWidth 仍是 640,引擎那句 videoReady() 恒真,
 * tick 一直在解同一张死图:屏上「对准条码」照旧、取景框还亮着、错误卡不出、件数不涨、查码
 * 0 次,店员把货一件件举过去全不算数。触发在泰国小店是日常:来电、切后台、锁屏、另一个 app
 * 开相机、拔掉 USB 摄像头。五条把两个方向都摆上:
 *   camRevoked        正向 · 收走 → 屏上真出错误卡 + 重试真能重开;件数/购物车一动不动
 *   camStaysLive      反向 · 同素材同节拍不收 → 件数接着涨、错误卡一次不冒
 *                     (没有它,上一条的「件数冻住」赖不到收相机头上)
 *   camCloseIsNotErr  反向 · 点「完成」/ Esc 关层是正常路径 → 不许弹这张卡
 *   camFrozenHidden   反向 · 转后台画面冻住(muted)→ 不许判死;回前台接着扫
 *   camFrozenWatching 正向 · 人在看着画面却一直冻着 → 宽限窗一过必须出声
 * 收走的手法用 track.stop() 而不是 CDP 撤权:规范上 stop()【不发】 ended 事件,只有每拍轮询
 * 照得到 —— 挑最难的那一路,「只订事件」的写法在这条底下红得出来。
 *
 * 五条素材用例也顺带守着同一个反向:cardShown 进 ok —— 正常扫码全程不许冒错误卡。
 *
 * 真的东西:Chromium 假摄像头喂真合成 EAN-13(桌面 Chromium 没有原生 BarcodeDetector,
 * 走的是本仓 dist/zxing.js 真解码);pos.html + dist/pos.js 是真产物。桩只有 by-barcode 回包。
 * 屏上那句话与按钮字样现场从真 POS.t 取,不在脚本里抄中文。
 *
 * 跑法(仓库根目录):
 *   python scripts/_scan_ean_pjitter_y4m.py .p80.y4m 0.8 13
 *   python scripts/_scan_ean_pjitter_y4m.py .p60.y4m 0.6 5
 *   python scripts/_scan_ean_pjitter_y4m.py .p50.y4m 0.5 3
 *   python scripts/_scan_ean_jitter_y4m.py .g600.y4m 8850999320014 19 9   # 糊 9 帧 @15fps = 600ms
 *   python scripts/_scan_ean_jitter_y4m.py .g800.y4m 8850999320014 19 12  # 糊 12 帧 = 800ms
 *   python scripts/_scan_ean_blink_y4m.py .blink20.y4m 8850999320014 2.0  # 离开 2.0s 再举回来
 *   node scripts/_hostile_scan_cam_verify.cjs [用例名前缀]
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('@playwright/test');
const { ROOT, PHONE, serve, shotter } = require('./_gun_wedge_lib.cjs');

const SHOTS = path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/fix2');
const shot = shotter(SHOTS);
const BOX = '8850999320014';
const ONLY = process.argv[2] || ''; // 只跑名字以它开头的用例(排障用;不给就全跑)

// 后两条是「一次长反光」:素材里的空白只有 600 / 800ms。解码器自己要花时间 —— ZXing 解不出
// 的一帧实测 ~120ms,于是【观测到的】空白比素材里的长一截,而判据的墙钟那把尺子量到的就是这个
// 被撑大的数。这两条量的就是那一截有多长(报告里的 gaps),也是「为什么不能只信墙钟」的现场证据。
const FIXTURES = [
    ['p80', path.resolve('.p80.y4m')],
    ['p60', path.resolve('.p60.y4m')],
    ['p50', path.resolve('.p50.y4m')],
    ['gap600', path.resolve('.g600.y4m')],
    ['gap800', path.resolve('.g800.y4m')],
];
// 相机那四条要的是「件数会一路涨」的素材(离开 2.0s > 引擎地板 → 引擎自己就认第二件),
// 冻住才有对照物。抖动素材举着不动只记一件,拿它验「涨没涨」等于什么都没验。
const BLINK20 = path.resolve('.blink20.y4m');
// 观察窗。blink20 一个周期是 4.0s(举着 2s / 拿走 2s),窗口必须明显长过一个周期 ——
// 只给一个周期的话,反向那条「件数没涨」可能只是相位没走到,断言就成了掷骰子。
const WATCH_MS = 7000;

const seed = () => {
    localStorage.setItem('pos_store_token', 'hostile-cam');
    localStorage.setItem('pos_store_name', 'ร้าน CAM');
    localStorage.setItem('mrpilot_lang', 'th');
};

const ITEM = {
    id: 'p-box',
    name: { th: 'โค้ก ลัง', en: 'Coke box', zh: '可乐箱', ja: 'コーラ箱' },
    category_id: 1,
    base_unit: 'ลัง',
    base_price: '350.00',
    image_url: null,
    vat_applicable: true,
    units: [
        { unit_name: 'ลัง', factor: '1.000', barcode: BOX, price: '350.00', default_sell: true },
    ],
    track_batch: false,
    is_weighed: false,
    stock: { qty_base: '48.000', near_expiry: false },
    matched_unit: 'ลัง',
};

/**
 * 屏上此刻是什么样。
 *
 * cardShown 走真几何 + getComputedStyle,不看 class 有没有 'show':CSS 属性写上了不等于
 * 效果生效(本仓 sticky 那次假绿就是只看 position)。要有面积、没被 display/visibility/opacity
 * 藏起来、而且真落在视口里 —— 三样缺一样,店员就是看不见。
 */
const SNAP = () => {
    const card = document.getElementById('bscan-card');
    const box = card.getBoundingClientRect();
    const cs = getComputedStyle(card);
    const v = document.querySelector('#bscan-stage video');
    return {
        count: document.getElementById('bscan-count').textContent,
        last: document.getElementById('bscan-last').textContent,
        hint: document.getElementById('bscan-hint').textContent,
        frameLive: document.getElementById('bscan-frame').classList.contains('live'),
        maskShown: document.getElementById('bscan-mask').classList.contains('show'),
        qtys: [...document.querySelectorAll('#cart-lines .q[data-qi]')].map((e) => e.textContent),
        grand: document.getElementById('cart-grand').textContent,
        cardClass: card.classList.contains('show'),
        cardShown:
            cs.display !== 'none' &&
            cs.visibility !== 'hidden' &&
            cs.opacity !== '0' &&
            box.width > 0 &&
            box.height > 0 &&
            box.top < innerHeight &&
            box.bottom > 0 &&
            box.left < innerWidth &&
            box.right > 0,
        cardMsg: document.getElementById('bscan-card-msg').textContent.trim(),
        acts: [...document.querySelectorAll('#bscan-acts .bscan-act')].map((b) => {
            const r = b.getBoundingClientRect();
            return {
                label: b.textContent.trim(),
                w: Math.round(r.width),
                h: Math.round(r.height),
                inView: r.top < innerHeight && r.bottom > 0,
            };
        }),
        // 「引擎那把旧尺子仍然说画面是好的」的现场证据:收走之后它俩照旧是 4 / 640。
        videoReadyState: v ? v.readyState : -1,
        videoW: v ? v.videoWidth : 0,
        // 画面还在不在走。这是唯一跟机器快慢无关的「还活着」凭据:件数涨不涨要看去重地板
        // (慢机器上地板能到 5 秒),拿它当反向那条的判据,CI 一忙就假红。
        videoTime: v ? v.currentTime : -1,
    };
};

const countOf = (s) => Number((String(s && s.count).match(/\d+/) || [0])[0]);

const waitCount = (page, want) =>
    page
        .waitForFunction(
            (n) => {
                const m = (document.getElementById('bscan-count').textContent || '').match(/\d+/);
                return !!m && Number(m[0]) >= n;
            },
            want,
            { timeout: 60000 }
        )
        .then(
            () => true,
            () => false
        );

/** 登录 → 开班 → 收银主屏 → 打开取景层。asked 记下真发出去的查码(时刻是相对开页的毫秒)。 */
async function openScanLayer(browser, origin) {
    const page = await browser.newPage({ viewport: PHONE });
    await page.addInitScript(seed);
    const asked = [];
    const t0 = Date.now();
    await page.route('**/api/pos/products/by-barcode*', async (route) => {
        asked.push({
            code: new URL(route.request().url()).searchParams.get('code'),
            at: Date.now() - t0,
        });
        await route.fulfill({ json: { ok: true, data: ITEM } });
    });
    await page.goto(`${origin}/static/pos/pos.html`);
    await page.waitForSelector('#login-cashiers .ca', { timeout: 20000 });
    for (const d of ['1', '2', '3', '4']) await page.click(`#view-login .pad .k[data-pin="${d}"]`);
    await page.waitForSelector('#shift-mask.show', { timeout: 10000 });
    await page.click('#shift-open-go');
    await page.waitForSelector('#view-main.is-active', { timeout: 10000 });
    await page.click('#main-scan-btn');
    await page.waitForSelector('#bscan-mask.show', { timeout: 5000 });
    return { page, asked };
}

/** 等第一件真解出来(相机出帧 + ZXing 下载)。回 false = 没起来,由用例判红。 */
const firstHit = (page) =>
    page
        .waitForFunction(
            () => (document.getElementById('bscan-last').textContent || '').length > 0,
            null,
            { timeout: 45000 }
        )
        .then(
            () => true,
            () => false
        );

async function run(browser, origin, label) {
    const { page, asked } = await openScanLayer(browser, origin);
    await firstHit(page);
    await page.waitForTimeout(7000); // 让整段素材跑完
    const state = await page.evaluate(SNAP);
    await shot(page, `c-${label}-jitter.png`);
    await page.close();
    // 两次取件之间隔了多久 = 引擎认为「这个码离开画面」了多久。素材里的空白只有几百毫秒,
    // 这个数才是判据真正吃到的那个数 —— 差出来的就是解码器自己烧掉的墙钟。
    const gaps = asked.slice(1).map((a, i) => a.at - asked[i].at);
    return { label, state, lookups: asked.length, asked, gaps };
}

// ── 正向:相机被收走 → 屏上必须出得来一张看得见的错误卡 + 一条走得通的重试 ──────────
async function cameraRevoked(browser, origin) {
    const { page, asked } = await openScanLayer(browser, origin);
    const first = await firstHit(page);
    // 先等件数涨到 2:证明这台机器上素材确实在一路出码,后面「冻住」才赖得到收相机头上。
    const grew = await waitCount(page, 2);
    const before = await page.evaluate(SNAP);
    const lookupsBefore = asked.length;
    // 收走相机:stop() 之后 readyState 变 'ended',但按规范一声不吭(不发 ended 事件)。
    const tracks = await page.evaluate(() => {
        const v = document.querySelector('#bscan-stage video');
        if (!v || !v.srcObject) return null;
        const ts = v.srcObject.getTracks();
        ts.forEach((t) => t.stop());
        return ts.map((t) => ({ st: t.readyState, muted: t.muted }));
    });
    await page.waitForSelector('#bscan-card.show', { timeout: 10000 }).catch(() => {});
    await page.waitForTimeout(WATCH_MS); // 再看一个多周期:件数 / 购物车 / 查码必须一动不动
    const after = await page.evaluate(SNAP);
    const lookupsFrozen = asked.length; // 取在点重试【之前】—— 重试成功后当然会再查一次
    const busy = await page.evaluate(() => window.POS.t('bscan.err.busy'));
    const retryLabel = await page.evaluate(() => window.POS.t('posui.retry'));
    await shot(page, 'x-cam-revoked.png');
    // 重试是不是真出口:点下去必须重新开起来(卡收掉 + 件数接着涨),不然那颗按钮是摆设。
    const retry = after.acts.find((a) => a.label === retryLabel);
    if (retry) await page.click(`#bscan-acts .bscan-act >> text="${retryLabel}"`);
    const resumed = retry ? await waitCount(page, countOf(after) + 1) : false;
    const back = await page.evaluate(SNAP);
    await shot(page, 'x-cam-revoked-retry.png');
    await page.close();
    return {
        ok:
            first &&
            grew &&
            !!tracks &&
            tracks.every((t) => t.st === 'ended') && // 相机真被收走了,不然验的是别的事
            !before.cardShown && // 收之前干干净净 —— 这张卡是这一下逼出来的
            after.cardShown &&
            after.cardMsg === busy && // 屏上那句 = 真词典里那一句
            !!retry &&
            retry.h > 0 &&
            retry.inView &&
            !after.frameLive && // 取景框不许还亮着说在扫
            after.count === before.count && // 件数诚实:没扫上就是没扫上
            after.qtys.join(',') === before.qtys.join(',') &&
            after.grand === before.grand &&
            lookupsFrozen === lookupsBefore && // 收走之后零查码
            resumed &&
            countOf(back) > countOf(after) && // 重试之后件数真的接着涨
            !back.cardShown,
        first,
        grew,
        tracks,
        before,
        after,
        back,
        busy,
        retryLabel,
        resumed,
        lookupsBefore,
        lookupsFrozen,
        lookupsAfter: asked.length,
    };
}

// ── 反向:不收相机 —— 同素材同节拍,件数必须接着涨、错误卡一次不许冒 ────────────────
async function cameraStaysLive(browser, origin) {
    const { page, asked } = await openScanLayer(browser, origin);
    const first = await firstHit(page);
    const grew = await waitCount(page, 2);
    const before = await page.evaluate(SNAP);
    const lookupsBefore = asked.length;
    await page.waitForTimeout(WATCH_MS); // 与上一条一模一样的窗口,唯一的差别就是没收相机
    const after = await page.evaluate(SNAP);
    await shot(page, 'x-cam-control.png');
    await page.close();
    return {
        ok:
            first &&
            grew &&
            !before.cardShown &&
            !after.cardShown &&
            after.frameLive && // 屏上还在说「在扫」…
            after.hint !== '' &&
            after.videoTime > before.videoTime, // …而且画面确实还在走(件数涨不涨看地板,不算数)
        first,
        grew,
        before,
        after,
        counted: [countOf(before), countOf(after)], // 只记录不断言:同一段时间涨几件由去重地板定
        lookupsBefore,
        lookupsAfter: asked.length,
    };
}

// ── 反向:主动关层(完成 / Esc)是正常路径 —— 不许弹「相机被收走」那张卡 ──────────────
async function cameraCloseIsNotAnError(browser, origin) {
    const { page } = await openScanLayer(browser, origin);
    const first = await firstHit(page);
    await page.click('#bscan-done');
    await page.waitForTimeout(1500); // 留够时间:轮询那条路要是判错了,这会儿卡已经出来了
    const afterDone = await page.evaluate(SNAP);
    await shot(page, 'x-cam-closed-done.png');
    // 再开一次并用 Esc 关:两条关法各走一遍(Esc 那条另有 keydown 监听,不是同一段代码)
    await page.click('#main-scan-btn');
    await page.waitForSelector('#bscan-mask.show', { timeout: 5000 });
    const reopened = await firstHit(page);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1500);
    const afterEsc = await page.evaluate(SNAP);
    await shot(page, 'x-cam-closed-esc.png');
    await page.close();
    return {
        ok:
            first &&
            reopened && // 关了还能再开:destroy 之后重开这条路没被弄坏
            !afterDone.maskShown &&
            !afterDone.cardClass &&
            afterDone.cardMsg === '' &&
            !afterEsc.maskShown &&
            !afterEsc.cardClass &&
            afterEsc.cardMsg === '',
        first,
        reopened,
        afterDone,
        afterEsc,
    };
}

/**
 * 「画面冻住」这个平台信号是注入的,不是浏览器自己给的 —— 这一点必须写在明处。
 *
 * 轨道被系统挂起时发的是 muted(切后台 / 锁屏 / 别的应用短暂抢走),真机上很常见;
 * 但 headless Chromium 的假摄像头永远不会 mute,标签页也永远是 visible(实测:同 context
 * 开第二页 + bringToFront,第一页仍报 'visible',新旧两种 headless 都一样)。所以这两样
 * 由页面里现改:muted 是在【真的那条 MediaStreamTrack 实例】上盖一个 getter,
 * visibilityState 同理 —— 被测的仍然是真引擎 + 真收银台 DOM,只有平台那一下是喂的。
 * 收走相机那条(camRevoked)不需要这么做,它用的是真 API track.stop()。
 */
// 一个对象参数,不是两个位置参数:page.evaluate 只递一个实参,写成 (on, hidden) 的话
// 第二个永远是 undefined —— 「后台」那一半会静默退化成「前台」,用例照样跑得下去。
const setFreeze = ({ on, hidden }) => {
    const v = document.querySelector('#bscan-stage video');
    if (!v || !v.srcObject) return false;
    v.srcObject.getTracks().forEach((t) => {
        Object.defineProperty(t, 'muted', { get: () => on, configurable: true });
    });
    Object.defineProperty(document, 'visibilityState', {
        get: () => (hidden ? 'hidden' : 'visible'),
        configurable: true,
    });
    document.dispatchEvent(new Event('visibilitychange'));
    return document.visibilityState === (hidden ? 'hidden' : 'visible');
};

// ── 反向:转后台画面冻住 —— 回来轨道还活着就得接着扫,不许卡在错误态 ──────────────────
async function cameraFrozenWhileHidden(browser, origin) {
    const { page, asked } = await openScanLayer(browser, origin);
    const first = await firstHit(page);
    const grew = await waitCount(page, 2);
    const froze = await page.evaluate(setFreeze, { on: true, hidden: true });
    // 待够一个多周期,也远长过引擎给冻结画面的宽限窗(3s)。后台期间不许计时 —— 计了就是
    // 「切出去久一点、回来说相机坏了」,那正是这条要挡的。
    await page.waitForTimeout(WATCH_MS);
    const hidden = await page.evaluate(SNAP);
    await shot(page, 'x-cam-frozen-hidden.png');
    const back = await page.evaluate(setFreeze, { on: false, hidden: false }); // 切回前台,画面也活了
    const lookupsBefore = asked.length;
    const resumed = await waitCount(page, countOf(hidden) + 1);
    const after = await page.evaluate(SNAP);
    await shot(page, 'x-cam-frozen-hidden-back.png');
    await page.close();
    return {
        ok:
            first &&
            grew &&
            froze &&
            back &&
            !hidden.cardShown && // 后台冻着的这 7 秒不许判死
            !after.cardShown &&
            after.frameLive &&
            resumed && // 回来接着扫
            asked.length > lookupsBefore,
        first,
        grew,
        froze,
        back,
        hidden,
        after,
        resumed,
        lookupsBefore,
        lookupsAfter: asked.length,
    };
}

// ── 正向:人在看着,画面却一直冻着 —— 宽限窗一过必须出声 ──────────────────────────────
async function cameraFrozenWhileWatching(browser, origin) {
    const { page, asked } = await openScanLayer(browser, origin);
    const first = await firstHit(page);
    const grew = await waitCount(page, 2);
    const before = await page.evaluate(SNAP);
    const froze = await page.evaluate(setFreeze, { on: true, hidden: false });
    const lookupsBefore = asked.length;
    await page.waitForSelector('#bscan-card.show', { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(WATCH_MS);
    const after = await page.evaluate(SNAP);
    const busy = await page.evaluate(() => window.POS.t('bscan.err.busy'));
    const retryLabel = await page.evaluate(() => window.POS.t('posui.retry'));
    await shot(page, 'x-cam-frozen-watching.png');
    await page.close();
    const retry = after.acts.find((a) => a.label === retryLabel);
    return {
        ok:
            first &&
            grew &&
            froze &&
            !before.cardShown &&
            after.cardShown &&
            after.cardMsg === busy &&
            !!retry &&
            retry.h > 0 &&
            retry.inView &&
            !after.frameLive &&
            after.count === before.count && // 冻住期间件数不许再涨
            after.qtys.join(',') === before.qtys.join(',') &&
            asked.length === lookupsBefore,
        first,
        grew,
        froze,
        before,
        after,
        busy,
        retryLabel,
        lookupsBefore,
        lookupsAfter: asked.length,
    };
}

const CAM_LEGS = [
    ['camRevoked', cameraRevoked],
    ['camStaysLive', cameraStaysLive],
    ['camCloseIsNotErr', cameraCloseIsNotAnError],
    ['camFrozenHidden', cameraFrozenWhileHidden],
    ['camFrozenWatching', cameraFrozenWhileWatching],
];

function launch(y4m) {
    return chromium.launch({
        args: [
            '--use-fake-ui-for-media-stream',
            '--use-fake-device-for-media-stream',
            `--use-file-for-fake-video-capture=${y4m}`,
        ],
    });
}

(async () => {
    for (const f of [...FIXTURES.map(([, p]) => p), BLINK20]) {
        if (!fs.existsSync(f)) {
            console.error(`缺素材 ${f} —— 见本文件头部的跑法`);
            process.exit(2);
        }
    }
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const report = {};
    const REPEATS = Number(process.env.HOSTILE_CAM_REPEATS || 1);
    for (const [label0, y4m] of FIXTURES) {
        if (ONLY && !label0.startsWith(ONLY)) continue;
        for (let rep = 1; rep <= REPEATS; rep++) {
            const label = REPEATS > 1 ? `${label0}#${rep}` : label0;
            const browser = await launch(y4m);
            let row;
            try {
                row = await run(browser, origin, label);
            } catch (e) {
                row = { label, crash: String(e && e.message ? e.message : e) };
            }
            await browser.close();
            // 一直举在框里没动过 = 一件。屏上件数、购物车数量、真发出去的查询次数三处都得是 1,
            // 而且全程不许冒错误卡 —— 相机好好的却报「被收走」,跟不报一样是骗人。
            row.ok =
                !!row.state &&
                /(^|\D)1(\D|$)/.test(row.state.count) &&
                row.state.qtys.join(',') === '1' &&
                row.lookups === 1 &&
                !row.state.cardShown;
            report[label] = row;
            console.log(
                `${row.ok ? 'PASS' : 'FAIL'} ${label} n=${row.lookups} gaps=${JSON.stringify(
                    row.gaps || []
                )} card=${row.state ? row.state.cardShown : '?'} ${JSON.stringify(
                    row.state ? { count: row.state.count, qtys: row.state.qtys } : {}
                )}`
            );
        }
    }
    for (const [name, fn] of CAM_LEGS) {
        if (ONLY && !name.startsWith(ONLY)) continue;
        const browser = await launch(BLINK20);
        let row;
        try {
            row = await fn(browser, origin);
        } catch (e) {
            row = { ok: false, crash: String(e && e.message ? e.message : e) };
        }
        await browser.close();
        report[name] = row;
        console.log(`${row.ok ? 'PASS' : 'FAIL'} ${name} ${row.crash || ''}`);
    }
    fs.writeFileSync(path.join(SHOTS, 'report-hostile-cam.json'), JSON.stringify(report, null, 2));
    server.close();
    const failed = Object.keys(report).filter((k) => !report[k].ok);
    console.log(failed.length ? `FAIL: ${failed.join(', ')}` : 'PASS · 全部');
    process.exit(failed.length ? 1 : 0);
})().catch((e) => {
    console.error('HOSTILE CAM CRASH', e);
    process.exit(2);
});
