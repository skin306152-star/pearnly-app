/*
 * scripts/_fix_scan_pos_verify.cjs · 收银台扫码「三路对抗审查揪出的错」的真浏览器复验
 *
 * 只验修掉的那几条行为,每条都对应一次真实发生过的错:
 *   P0-A 连扫  码举在框里 6 秒不动 = 1 件(旧行为按时间节流,6 秒收 5 件 ฿1750);
 *              反向:码离开画面再回来必须能再收一件(去重不能做成「同码一辈子只算一次」)。
 *   P0-C 连扫不同码  枪连打三个码 + 后端 500ms 往返 = 三件全到账(旧行为在忙就丢,只进第一件)。
 *   P1-E 相机释放    授权超时之后 stream 才兑现 → 那条 track 必须被 stop(旧行为漏收,灯常亮)。
 *   P1-H 零元闸      单位没设价的箱码不许进车,必须出可见错误(旧行为 ฿0.00 静默进车)。
 *   P1-I 参照系      屏上取景框映射回源像素 == 引擎真解的那块(旧行为按舞台画,框外的货也被解)。
 *
 * 真的东西:static/pos/pos.html + dist/pos.js + dist/scan.js + dist/zxing.js 全是本仓真产物;
 * 摄像头是 Chromium 假设备喂真合成 EAN-13,桌面 Chromium 没有原生 BarcodeDetector,所以走的是
 * 真 ZXing 真解码(holdSteady 当场断这一条);键盘是 page.keyboard 真按键。桩只有
 * /api/pos/products/by-barcode 的回包。文案期望值现场从真 window.POS_I18N 取,一个字都不注入。
 *
 * 跑法(仓库根目录):两句 python 生成素材,再 node 本脚本 <静态素材> <闪烁素材> [用例名]
 *   python scripts/_scan_ean_y4m.py .scan_fixture.y4m
 *   python scripts/_scan_ean_blink_y4m.py .scan_blink.y4m
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('@playwright/test');
const { ROOT, PHONE, serve, gun, shotter, runCases } = require('./_gun_wedge_lib.cjs');

const STEADY_Y4M = path.resolve(process.argv[2] || '.scan_fixture.y4m');
const BLINK_Y4M = path.resolve(process.argv[3] || '.scan_blink.y4m');
const ONLY = process.argv[4] || '';
const SHOTS = path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/fix-pos');
const shot = shotter(SHOTS);

const BOX = '8850999320014'; // y4m 里那张码 · 挂在「ลัง」单位上 ฿350
const NO_PRICE = '8850999320021'; // 只为库存换算建的箱码,售价栏空着
const BURST = ['8850999320045', '8850999320052', '8850999320069']; // ฿10 + ฿25 + ฿18

const seed = () => {
    localStorage.setItem('pos_store_token', 'fix-verify');
    localStorage.setItem('pos_store_name', 'ร้าน FIX');
    localStorage.setItem('mrpilot_lang', 'th');
};

// 信封形状照 /api/pos/products/by-barcode 的真回包(routes 那层归后端单测管)。matched_unit
// = 后端说这个码命中的是哪个售卖单位 —— 箱码按箱加、瓶码按瓶加就靠它。
function product(id, name, units, matchedUnit) {
    return {
        id,
        name: { th: name, en: name, zh: name, ja: name },
        category_id: 1,
        base_unit: units[0].unit_name,
        image_url: null,
        vat_applicable: true,
        units,
        track_batch: false,
        is_weighed: false,
        stock: { qty_base: '48.000', near_expiry: false },
        matched_unit: matchedUnit,
    };
}

const unit = (name, barcode, price, factor) => ({
    unit_name: name,
    factor: factor || '1.000',
    barcode,
    price,
    default_sell: !factor,
});

// 箱价空着 = 只为库存换算建的单位行。฿0 那一档必须被拦下,不能悄悄按 ฿0.00 收钱。
const coke = (boxPrice) =>
    product(
        'fix-coke',
        'โค้ก 325ml',
        [unit('ขวด', '8850999320007', '15.00'), unit('ลัง', BOX, boxPrice, '24.000')],
        'ลัง'
    );
const one = (id, name, unitName, barcode, price) =>
    product(id, name, [unit(unitName, barcode, price)], unitName);

const CATALOG = {
    [BOX]: coke('350.00'),
    [NO_PRICE]: coke(null),
    [BURST[0]]: one('fix-water', 'น้ำเปล่า', 'ขวด', BURST[0], '10.00'),
    [BURST[1]]: one('fix-bread', 'ขนมปัง', 'ถุง', BURST[1], '25.00'),
    [BURST[2]]: one('fix-milk', 'นมจืด', 'กล่อง', BURST[2], '18.00'),
};

// delayMs = 后端往返。连扫不同码那条必须让后两发落在「上一件还没回来」的窗口里,否则
// 串行化根本没被考到 —— 旧的「在忙就丢」在零延迟下也全绿。
async function routeCatalog(page, delayMs) {
    await page.route('**/api/pos/products/by-barcode*', async (route) => {
        const code = new URL(route.request().url()).searchParams.get('code');
        const hit = CATALOG[code];
        if (delayMs) await new Promise((r) => setTimeout(r, delayMs));
        await route.fulfill({
            status: hit ? 200 : 404,
            contentType: 'application/json',
            body: JSON.stringify(
                hit
                    ? { ok: true, data: hit }
                    : { ok: false, error: { code: 'pos.product_not_found', detail: null } }
            ),
        });
    });
}

async function login(page, origin) {
    await page.goto(`${origin}/static/pos/pos.html`);
    await page.waitForSelector('#login-cashiers .ca', { timeout: 20000 });
    for (const d of ['1', '2', '3', '4']) await page.click(`#view-login .pad .k[data-pin="${d}"]`);
    await page.waitForSelector('#shift-mask.show', { timeout: 10000 });
    await page.click('#shift-open-go');
    await page.waitForSelector('#view-main.is-active', { timeout: 10000 });
    await page.waitForSelector('#main-grid .prod', { timeout: 10000 });
}

// 期望文案从页面里的真字典现取。脚本自带一份副本 = 拿自己比自己,漏译永远照不出来。
const dict = (page) =>
    page.evaluate(() => ({
        lang: window.POS.state.lang,
        copy: window.POS_I18N[window.POS.state.lang],
    }));

const cart = (page) =>
    page.evaluate(() => ({
        grand: document.getElementById('cart-grand').textContent,
        qtys: [...document.querySelectorAll('#cart-lines .q[data-qi]')].map((e) => e.textContent),
        names: [...document.querySelectorAll('#cart-lines .li-nm .n')].map((e) => e.textContent),
        count: document.getElementById('bscan-count').textContent,
        last: document.getElementById('bscan-last').textContent,
    }));

async function openCamera(page) {
    await page.click('#main-scan-btn');
    await page.waitForSelector('#bscan-mask.show', { timeout: 5000 });
    // 真解码要等相机出帧 + ZXing 下载(桌面 Chromium 无原生 BarcodeDetector)
    await page.waitForFunction(
        () => (document.getElementById('bscan-last').textContent || '').length > 0,
        null,
        { timeout: 40000 }
    );
}

async function bootCam(browser, origin, delayMs) {
    const page = await browser.newPage({ viewport: PHONE });
    await page.addInitScript(seed);
    await routeCatalog(page, delayMs);
    await login(page, origin);
    return page;
}

// 屏上的取景框 ↔ 引擎真解的那块像素,在浏览器里量真盒子。参照系有三层(舞台 / 画面 /
// 原生帧),错一层就是「框里对准了读不出」或「框外的货被解进购物车」,而两种都不报错。
const FRAME_GEOM = () => {
    const v = document.querySelector('.bscan-video');
    const f = document.getElementById('bscan-frame');
    const vb = v.getBoundingClientRect();
    const fb = f.getBoundingClientRect();
    // 缩放按浏览器实际用的 fit 求(cover 取 max、contain 取 min),不按 CSS 里写的那份猜
    const fit = getComputedStyle(v).objectFit;
    const scale =
        fit === 'cover'
            ? Math.max(vb.width / v.videoWidth, vb.height / v.videoHeight)
            : Math.min(vb.width / v.videoWidth, vb.height / v.videoHeight);
    const pic = {
        w: v.videoWidth * scale,
        h: v.videoHeight * scale,
        l: vb.left + (vb.width - v.videoWidth * scale) / 2,
        t: vb.top + (vb.height - v.videoHeight * scale) / 2,
    };
    // 期望值从真 handle 的 cropRatio() 现取(建个空 handle 只读比例,不开相机)
    const probe = window.PearnlyScanCamera.create({ container: document.createElement('div') });
    const crop = probe.cropRatio();
    probe.destroy();
    return {
        crop,
        videoW: v.videoWidth,
        videoH: v.videoHeight,
        objectFit: fit,
        frameVisible: getComputedStyle(f).display !== 'none' && fb.width > 0,
        src: {
            w: fb.width / scale,
            h: fb.height / scale,
            cx: (fb.left + fb.width / 2 - pic.l) / scale,
            cy: (fb.top + fb.height / 2 - pic.t) / scale,
        },
        want: {
            w: v.videoWidth * crop.width,
            h: v.videoHeight * crop.height,
            cx: v.videoWidth / 2,
            cy: v.videoHeight / 2,
        },
        // 框不许越出画面:越出的那一圈是黑边,店员看不到货却以为那也在框里
        insidePicture:
            fb.left >= pic.l - 1 &&
            fb.top >= pic.t - 1 &&
            fb.right <= pic.l + pic.w + 1 &&
            fb.bottom <= pic.t + pic.h + 1,
    };
};

// 差 3px 以内算重合:亚像素舍入不该判红,参照系错位差的是几十上百 px。
function frameMatches(g) {
    const near = (a, b) => Math.abs(a - b) <= 3;
    return (
        g.frameVisible &&
        g.insidePicture &&
        near(g.src.w, g.want.w) &&
        near(g.src.h, g.want.h) &&
        near(g.src.cx, g.want.cx) &&
        near(g.src.cy, g.want.cy)
    );
}

// ── P0-A 正向 · 举着不动 6 秒只能算一件 + P1-I 取景框对得上解码区 ────────────
async function holdSteady(browser, origin) {
    const page = await bootCam(browser, origin, 0);
    const th = await dict(page);
    // 「解码是真的不是桩」得当场证一次:桌面 Chromium 没有原生 BarcodeDetector,所以进车的
    // 那一件必然是懒加载下来的 vendored ZXing 从假摄像头的画面里真读出来的。
    const lazy = [];
    page.on('request', (r) => {
        const m = r.url().match(/\/static\/dist\/(scan|zxing)\.js/);
        if (m) lazy.push(m[1]);
    });
    const native = await page.evaluate(() => 'BarcodeDetector' in window);
    await openCamera(page);
    const firstAt = Date.now();
    // 「6 秒不动」是店员真会做的动作(一手举着货一手点屏)。不能只等一个固定睡眠就下结论,
    // 中途每秒采一次:旧行为是逐次累加,采样序列会长出 2、3、4… 一眼看得出是哪一秒破的。
    const samples = [];
    while (Date.now() - firstAt < 6000) {
        await page.waitForTimeout(1000);
        samples.push((await cart(page)).grand);
    }
    const held = await cart(page);
    await shot(page, 'fix-a1-hold-steady-6s-one-item.png');

    // P1-I:屏上的框映射回源像素,必须就是引擎真解的那块(期望值从真 handle 的 cropRatio()
    // 现取,脚本里再抄一份 0.9/0.5 就是拿桩验桩)。量竖屏和横屏两个画幅:letterbox 的方向
    // 正相反,只量一个时「按舞台画框」在另一个画幅上照样能蒙对,那种绿是碰巧。
    const geom = await page.evaluate(FRAME_GEOM);
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.waitForTimeout(400); // resize → sizeFrame() 重算,等它落定再量
    const geomWide = await page.evaluate(FRAME_GEOM);
    await shot(page, 'fix-i-frame-matches-decode-area.png');
    await page.close();
    const frameOk = frameMatches(geom) && frameMatches(geomWide);
    return {
        ok:
            th.lang === 'th' &&
            native === false &&
            lazy.includes('scan') &&
            lazy.includes('zxing') &&
            held.grand === '350.00' &&
            held.qtys.join('|') === '1' &&
            held.count === th.copy['posui.bscan.count'].replace('{n}', '1') &&
            held.last === th.copy['posui.bscan.added'].replace('{name}', 'โค้ก 325ml') &&
            samples.every((g) => g === '350.00') &&
            frameOk,
        native,
        lazy,
        samples,
        held,
        geom,
        geomWide,
        frameOk,
    };
}

// ── P0-A 反向 · 码离开画面再回来必须能再收一件 ─────────────────────────────
// 素材是「举进来 2 秒 → 拿走 2 秒」的循环 y4m,画面里的码是真的消失了再出现,
// 不是脚本改引擎状态 —— 去重被做成「同码一辈子只算一次」时这里会一直停在 1 件。
async function leaveAndReturn(browser, origin) {
    const page = await bootCam(browser, origin, 0);
    const th = await dict(page);
    await openCamera(page);
    const one = await cart(page);
    let two = one;
    try {
        await page.waitForFunction(
            () => document.getElementById('cart-grand').textContent === '700.00',
            null,
            { timeout: 40000 }
        );
        two = await cart(page);
    } catch (_) {
        two = await cart(page); // 等不到就是没再收第二件:让下面的断言去报 FAIL
    }
    await shot(page, 'fix-a2-leave-and-return-two-items.png');
    await page.close();
    return {
        ok:
            th.lang === 'th' &&
            one.grand === '350.00' &&
            two.grand === '700.00' &&
            two.qtys.join('|') === '2' &&
            two.count === th.copy['posui.bscan.count'].replace('{n}', '2'),
        one,
        two,
    };
}

// ── P0-C · 枪连扫三个不同的码 + 后端 500ms 往返 → 三件全到账 ────────────────
async function burstThree(browser, origin) {
    const page = await bootCam(browser, origin, 500);
    const th = await dict(page);
    // 积压提示是转瞬即逝的 toast:旁听记下来(原函数照跑),不然「店员看得见排队」没法验
    await page.evaluate(() => {
        window.__toasts = [];
        const orig = window.POS.toast;
        window.POS.toast = (m, t) => {
            window.__toasts.push(m);
            return orig(m, t);
        };
    });
    const focus = [];
    for (const code of BURST) focus.push(await gun(page, code));
    let reached = true;
    try {
        await page.waitForFunction(
            () => document.getElementById('cart-grand').textContent === '53.00',
            null,
            { timeout: 20000 }
        );
    } catch (_) {
        reached = false;
    }
    const after = await cart(page);
    const toasts = await page.evaluate(() => window.__toasts);
    await shot(page, 'fix-c-burst-three-codes.png');
    await page.close();
    const q = (n) => th.copy['posui.bscan.queued'].replace('{n}', String(n));
    return {
        ok:
            reached &&
            focus.every((f) => f.tag !== 'INPUT') && // 枪那条路的前提:焦点不在输入框
            after.grand === '53.00' &&
            after.names.join('|') === 'น้ำเปล่า|ขนมปัง|นมจืด' && // 落地顺序 = 扫的顺序
            after.qtys.join('|') === '1|1|1' &&
            toasts.includes(q(1)) &&
            toasts.includes(q(2)),
        reached,
        focus,
        after,
        toasts,
    };
}

// ── P1-E · 授权超时之后 stream 才兑现 → 那条 track 必须被 stop ──────────────
// 真店里就是这样:权限弹窗挂了半分钟,店员点「允许」时引擎早已报超时。没人认领的那条
// MediaStream 会让相机灯一直亮着,重试还会被自己占住的相机顶成「被别的应用占用」。
// 这里不动引擎的 grantTimeoutMs(30s),走的是收银台真路径 —— 所以这一例要跑 35 秒左右。
const LATE_GRANT = () => {
    const md = navigator.mediaDevices;
    const orig = md.getUserMedia.bind(md);
    window.__late = [];
    md.getUserMedia = (c) =>
        new Promise((resolve, reject) => {
            setTimeout(() => {
                orig(c).then((s) => {
                    window.__late.push(s);
                    resolve(s);
                }, reject);
            }, 31000);
        });
};

async function lateGrantRelease(browser, origin) {
    const page = await browser.newPage({ viewport: PHONE });
    await page.addInitScript(seed);
    await page.addInitScript(LATE_GRANT);
    await routeCatalog(page, 0);
    await login(page, origin);
    const th = await dict(page);
    await page.click('#main-scan-btn');
    await page.waitForSelector('#bscan-card.show', { timeout: 40000 });
    const card = await page.evaluate(() => {
        const msg = document.getElementById('bscan-card-msg');
        return {
            text: msg.textContent,
            visible:
                getComputedStyle(msg).display !== 'none' && msg.getBoundingClientRect().height > 0,
            acts: [...document.querySelectorAll('#bscan-acts .bscan-act')].map(
                (b) => b.textContent
            ),
        };
    });
    // 兑现发生在超时之后:等它到货,再问那条 track 还活着没有
    await page.waitForFunction(() => window.__late.length > 0, null, { timeout: 20000 });
    await page.waitForTimeout(500);
    const streams = await page.evaluate(() => ({
        count: window.__late.length,
        states: window.__late.flatMap((s) => s.getTracks().map((t) => t.readyState)),
    }));
    await shot(page, 'fix-e-late-grant-track-released.png');
    await page.close();
    return {
        ok:
            th.lang === 'th' &&
            card.visible &&
            card.text === th.copy['bscan.err.timeout'] &&
            card.acts.includes(th.copy['posui.retry']) &&
            streams.count === 1 &&
            streams.states.length > 0 &&
            streams.states.every((s) => s === 'ended'),
        card,
        streams,
    };
}

// ── P1-H · 单位没设价的箱码不许进车,且必须出可见错误文案 ────────────────────
async function zeroPriceBlocked(browser, origin) {
    const page = await bootCam(browser, origin, 0);
    const th = await dict(page);
    await gun(page, NO_PRICE);
    let shown = true;
    try {
        // 拒收落在 #bscan-fails 清单上,不再是那张会被下一件顶掉的单卡
        await page.waitForSelector('#bscan-fails.show .bscan-fail', { timeout: 10000 });
    } catch (_) {
        shown = false;
    }
    const card = await page.evaluate(() => {
        const row = document.querySelector('#bscan-fails .bscan-fail');
        if (!row) return { text: '', hint: '', visible: false, maskShown: false };
        const msg = row.querySelector('.bscan-fail-msg');
        const box = row.getBoundingClientRect();
        const cs = getComputedStyle(row);
        const top = document.elementFromPoint(box.left + box.width / 2, box.top + box.height / 2);
        return {
            text: msg.textContent,
            hint: (row.querySelector('.bscan-fail-hint') || {}).textContent || '',
            visible: cs.display !== 'none' && cs.visibility !== 'hidden' && box.height > 0,
            // 枪那条路上没有取景层:清单必须独立于它 —— 靠撑一层暗底来显形的旧拒收卡在枪扫时
            // 会凭空糊住整个收银主屏,而店员这一刻正要接着扫下一件。
            maskShown: document.getElementById('bscan-mask').classList.contains('show'),
            onTop: !!(top && row.contains(top)),
        };
    });
    const after = await cart(page);
    await shot(page, 'fix-h-zero-price-refused.png');
    await page.close();
    return {
        ok:
            shown &&
            card.visible &&
            card.onTop &&
            card.maskShown === false &&
            card.text ===
                th.copy['posui.cart.unit_no_price']
                    .replace('{unit}', 'ลัง')
                    .replace('{name}', 'โค้ก 325ml') &&
            card.hint === th.copy['posui.cart.fix_in_backoffice'] &&
            after.grand === '0.00' &&
            after.names.length === 0,
        shown,
        card,
        after,
    };
}

// 举着不动 / 离开再回来用的是两段不同的假摄像头素材,只能各起一个浏览器(Chromium 的
// --use-file-for-fake-video-capture 是启动参数,开完改不了)。
const CASES = [
    ['holdSteady', holdSteady, 'steady'],
    ['leaveAndReturn', leaveAndReturn, 'blink'],
    ['burstThree', burstThree, 'steady'],
    ['lateGrantRelease', lateGrantRelease, 'steady'],
    ['zeroPriceBlocked', zeroPriceBlocked, 'steady'],
];

const launch = (y4m) =>
    chromium.launch({
        args: [
            '--use-fake-ui-for-media-stream',
            '--use-fake-device-for-media-stream',
            `--use-file-for-fake-video-capture=${y4m}`,
        ],
    });

(async () => {
    for (const f of [STEADY_Y4M, BLINK_Y4M]) {
        if (!fs.existsSync(f)) {
            console.error(`缺假摄像头素材 ${f} —— 见本文件头部的跑法`);
            process.exit(2);
        }
    }
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const picked = CASES.filter(([name]) => !ONLY || name === ONLY);
    const browsers = {};
    const failed = await runCases(
        picked.map(([name, fn, feed]) => [name, { fn, feed }]),
        async ({ fn, feed }) => {
            if (!browsers[feed])
                browsers[feed] = await launch(feed === 'blink' ? BLINK_Y4M : STEADY_Y4M);
            return fn(browsers[feed], origin);
        },
        path.join(SHOTS, 'report-pos-fix.json')
    );
    for (const b of Object.values(browsers)) await b.close();
    server.close();
    process.exit(failed ? 1 : 0);
})().catch((e) => {
    console.error('POS FIX VERIFY CRASH', e);
    process.exit(2);
});
