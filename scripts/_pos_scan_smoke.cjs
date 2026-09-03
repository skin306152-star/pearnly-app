/*
 * scripts/_pos_scan_smoke.cjs · 收银台扫码取件的真浏览器验收(Chromium + 假摄像头)
 *
 * 验的是产品页本身:真 static/pos/pos.html + 真 dist/pos.js(含 pos-scan.js)+ 真扫码引擎 +
 * 真 ZXing 从假摄像头的画面里解出一个真 EAN-13 → 真的进购物车。桩只有两处,都是数据不是界面:
 *   · /api/pos/products/by-barcode 用 page.route 回真信封(后端契约归 routes 的单测管);
 *   · 其余 /api/pos/* 让静态服务 404 → POS 自己的纯本地预览 mock(店员列表/PIN/商品网格)。
 * 「被验的东西必须是真产物」那条血泪:这里点的是 #main-scan-btn,读的是 #bscan-* 真节点,
 * 文案期望值现场从页面里的真 window.POS_I18N 取 —— 脚本一个字都不注入,漏译才照得出来。
 *
 * 用法(仓库根目录):
 *   python scripts/_scan_ean_y4m.py .scan_fixture.y4m
 *   node scripts/_pos_scan_smoke.cjs .scan_fixture.y4m [截图目录]
 * 退出码 0 = 全过。截图默认落 tests/e2e/_artifacts/pos_scan/。
 */
const fs = require('fs');
const path = require('path');
const { startStaticServer } = require('./_smoke_server.cjs');
const { chromium } = require('@playwright/test');

const ROOT = path.resolve(__dirname, '..');
const Y4M = path.resolve(process.argv[2] || '.scan_fixture.y4m');
const SHOTS = path.resolve(process.argv[3] || path.join(ROOT, 'tests/e2e/_artifacts/pos_scan'));
const CODE = '8850999320014'; // 假摄像头画面里那个码(泰国 GS1 前缀 885)
const PHONE = { width: 390, height: 780 };

const serve = () => startStaticServer({ root: ROOT, notFoundBody: 'not found' });

function seed() {
    // 设备已绑店(过绑定屏)但不带账套 id → POS.allowMock() 为真,商品/店员走本地预览。
    localStorage.setItem('pos_store_token', 'e2e-smoke');
    localStorage.setItem('pos_store_name', 'ร้าน E2E');
    localStorage.setItem('mrpilot_lang', 'th');
    localStorage.removeItem('pos_held_orders');
}

function instrumentFeedback() {
    window.__scanFeedback = { starts: 0, stops: 0, vibrates: [], buffer: null };
    window.__scanSamples = null;
    class ScanAudioContext {
        constructor() {
            this.state = 'running';
            this.currentTime = 1;
            this.destination = {};
            this.sampleRate = 48000;
        }
        createBuffer(channels, length, rate) {
            window.__scanSamples = new Float32Array(length);
            window.__scanFeedback.buffer = { channels, length, rate };
            return {
                duration: length / rate,
                getChannelData: () => window.__scanSamples,
            };
        }
        createBufferSource() {
            return {
                buffer: null,
                connect() {},
                start: () => (window.__scanFeedback.starts += 1),
                stop: () => (window.__scanFeedback.stops += 1),
            };
        }
    }
    window.AudioContext = ScanAudioContext;
    Object.defineProperty(navigator, 'vibrate', {
        configurable: true,
        value: (duration) => window.__scanFeedback.vibrates.push(duration),
    });
}

// 期望文案现场从页面里的真 window.POS_I18N 取。脚本自带一份副本再注进去 = 拿自己比自己,
// 漏译永远照不出来;顺带把「语言到底切没切」一起验了(切没切成,下面所有文案断言都无意义)。
async function dict(page) {
    return page.evaluate(() => ({
        lang: window.POS.state.lang,
        copy: window.POS_I18N[window.POS.state.lang],
    }));
}

function product(matchedUnit) {
    return {
        id: 'e2e-coke',
        name: { th: 'โค้ก 325ml', en: 'Coke 325ml', zh: '可乐 325ml', ja: 'コーラ 325ml' },
        category_id: 1,
        base_unit: 'ขวด',
        image_url: null,
        avg_cost: '10.00',
        vat_applicable: true,
        units: [
            {
                unit_name: 'ขวด',
                factor: '1.000',
                barcode: '8850999320007',
                price: '15.00',
                default_sell: true,
            },
            {
                unit_name: 'ลัง',
                factor: '24.000',
                barcode: CODE,
                price: '350.00',
                default_sell: false,
            },
        ],
        track_batch: false,
        is_weighed: false,
        stock: { qty_base: '48.000', near_expiry: false },
        matched_unit: matchedUnit,
    };
}

// by-barcode 这一口由测控制:hit = 扫到的是箱码(回箱单位),miss = 后端说没有这个条码。
async function routeBarcode(page, mode) {
    await page.route('**/api/pos/products/by-barcode*', (route) => {
        const hit = mode === 'hit';
        route.fulfill({
            status: hit ? 200 : 404,
            contentType: 'application/json',
            body: JSON.stringify(
                hit
                    ? { ok: true, data: product('ลัง') }
                    : { ok: false, error: { code: 'pos.product_not_found', detail: null } }
            ),
        });
    });
}

async function login(page, origin, costVisible) {
    if (typeof costVisible === 'boolean') {
        await page.route('**/api/pos/auth/pin', (route) =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    ok: true,
                    data: {
                        token: 'e2e-cashier-token',
                        offline_ttl_hours: 12,
                        cashier: {
                            id: 'mock-c1',
                            display_name: 'Nok',
                            caps: { cost_visible: costVisible },
                        },
                        shift: null,
                    },
                }),
            })
        );
        await page.route('**/api/pos/products?*', (route) =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ ok: true, data: { items: [product(null)] } }),
            })
        );
    }
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

async function costVisibility(browser, origin) {
    const authorized = await browser.newPage({ viewport: PHONE });
    await authorized.addInitScript(seed);
    await login(authorized, origin, true);
    const th = await dict(authorized);
    const expected = th.copy['posui.product.cost'] + ' ฿10.00';
    const productCost = await text(authorized, '#main-grid .prod .cost');
    const productCostVisible = await authorized.evaluate(() => {
        const card = document.querySelector('#main-grid .prod').getBoundingClientRect();
        const cost = document.querySelector('#main-grid .prod .cost').getBoundingClientRect();
        return cost.top >= card.top && cost.bottom <= card.bottom + 0.5;
    });
    await authorized.click('#main-grid .prod');
    await authorized.click('#cart-peek');
    await authorized.waitForTimeout(350);
    const cartCost = await text(authorized, '#cart-lines .cost');
    await authorized.screenshot({ path: path.join(SHOTS, '11-cost-visible.png') });
    const safety = await authorized.evaluate(() => {
        document.getElementById('cart-hold-btn').click();
        const held = JSON.parse(localStorage.getItem('pos_held_orders') || '[]');
        window.POS.offline.cacheCatalog([
            {
                id: 'secret-cost',
                name: { th: 'สินค้า' },
                avg_cost: '7.00',
                units: [],
                stock: { qty_base: '1' },
            },
        ]);
        const cached = window.POS.offline.filterCached('', null)[0];
        return {
            costVisible: window.POS.cost.visible(),
            heldHasCost: Object.prototype.hasOwnProperty.call(held[0].cart[0], 'unitCost'),
            cachedHasCost: Object.prototype.hasOwnProperty.call(cached, 'avg_cost'),
        };
    });
    await authorized.close();

    const unauthorized = await browser.newPage({ viewport: PHONE });
    await unauthorized.addInitScript(seed);
    await login(unauthorized, origin, false);
    const productCostCount = await unauthorized.locator('#main-grid .prod .cost').count();
    await unauthorized.click('#main-grid .prod');
    await unauthorized.click('#cart-peek');
    await unauthorized.waitForTimeout(350);
    const cartCostCount = await unauthorized.locator('#cart-lines .cost').count();
    const hidden = await unauthorized.evaluate(() => !window.POS.cost.visible());
    await unauthorized.screenshot({ path: path.join(SHOTS, '12-cost-hidden.png') });
    await unauthorized.close();

    return {
        ok:
            th.lang === 'th' &&
            productCost === expected &&
            productCostVisible &&
            cartCost === expected &&
            safety.costVisible &&
            !safety.heldHasCost &&
            !safety.cachedHasCost &&
            hidden &&
            productCostCount === 0 &&
            cartCostCount === 0,
        productCost,
        productCostVisible,
        cartCost,
        expected,
        safety,
        unauthorized: { hidden, productCostCount, cartCostCount },
    };
}

const text = (page, sel) => page.textContent(sel);

// ── ① 连扫命中:真解码 → 按箱价进车 → 完成关层 ─────────────────────────
async function liveHit(browser, origin, viewport, tag) {
    const page = await browser.newPage({ viewport });
    await page.addInitScript(seed);
    await page.addInitScript(instrumentFeedback);
    await routeBarcode(page, 'hit');
    await login(page, origin);
    const th = await dict(page);
    if (tag === 'phone') await page.screenshot({ path: path.join(SHOTS, '01-main-th.png') });

    await page.click('#main-scan-btn');
    await page.waitForSelector('#bscan-mask.show', { timeout: 5000 });
    const starting = await text(page, '#bscan-hint');
    // 真解码要等相机出帧 + ZXing 下载(桌面 Chromium 无原生 BarcodeDetector)
    await page.waitForFunction(
        () => (document.getElementById('bscan-last').textContent || '').length > 0,
        null,
        { timeout: 25000 }
    );
    const shot = tag === 'phone' ? '02-scanning-hit.png' : '07-desktop-scanning.png';
    await page.screenshot({ path: path.join(SHOTS, shot) });

    const live = await page.evaluate(() => {
        const v = document.querySelector('.bscan-video');
        const f = document.getElementById('bscan-frame');
        const vb = v.getBoundingClientRect();
        const fb = f.getBoundingClientRect();
        // 参照系一旦错位(框按舞台画、或预览改成 cover),框外那一段仍在解码区里,紧挨着的
        // 另一件货会被解出来直接进购物车。判据不能只看 CSS 属性,要量真实几何:按浏览器实际
        // 用的 fit 求缩放(cover 取 max、contain 取 min),把屏上的框映射回源像素再跟解码区比。
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
        // 期望值从真引擎的 cropRatio() 现取(建个空 handle 只读比例,不开相机),
        // 脚本里再抄一份 0.9/0.5 就是拿桩验桩:引擎改了比例这条闸照样绿。
        const probe = window.PearnlyScanCamera.create({ container: document.createElement('div') });
        const crop = probe.cropRatio();
        probe.destroy();
        const srcFrame = {
            w: fb.width / scale,
            h: fb.height / scale,
            cx: (fb.left + fb.width / 2 - pic.l) / scale,
            cy: (fb.top + fb.height / 2 - pic.t) / scale,
        };
        const cs = getComputedStyle(f);
        const done = document.getElementById('bscan-done');
        const fly = document.querySelector('[data-scan-success-fly]');
        const controls = document.querySelector('[data-scan-view-controls]');
        const motion = controls?.querySelector('[data-scan-motion-toggle]');
        const torch = controls?.querySelector('.scan-view-torch');
        let crossings = 0;
        const samples = window.__scanSamples || [];
        for (let i = 1; i < samples.length; i++) {
            if (samples[i - 1] <= 0 && samples[i] > 0) crossings += 1;
        }
        return {
            videoW: v.videoWidth,
            playing: v.readyState >= 2,
            objectFit: fit,
            frameSize: [f.style.width, f.style.height],
            wantSize: [
                Math.round(pic.w * crop.width) + 'px',
                Math.round(pic.h * crop.height) + 'px',
            ],
            frameVisible: cs.display !== 'none' && parseFloat(cs.width) > 0,
            frameLive: f.classList.contains('live'),
            // 屏上的框映射回源像素,必须就是引擎解的那块(居中 · 90%×50%)。差 3px 以上就是
            // 参照系错位:框外的另一件货照样被解出来直接进购物车。
            frameEqualsCrop:
                Math.abs(srcFrame.w - v.videoWidth * crop.width) <= 3 &&
                Math.abs(srcFrame.h - v.videoHeight * crop.height) <= 3 &&
                Math.abs(srcFrame.cx - v.videoWidth / 2) <= 3 &&
                Math.abs(srcFrame.cy - v.videoHeight / 2) <= 3,
            srcFrame: srcFrame,
            // 框不许越出画面:越出的那一圈是黑边,店员看不到货却仍在解码区里。
            frameInsidePicture:
                fb.left >= pic.l - 1 &&
                fb.top >= pic.t - 1 &&
                fb.right <= pic.l + pic.w + 1 &&
                fb.bottom <= pic.t + pic.h + 1,
            doneH: done.getBoundingClientRect().height,
            doneLabel: done.textContent, // 空按钮不是"没验到"就没事:第一版就是一个没字的紫方块

            count: document.getElementById('bscan-count').textContent,
            last: document.getElementById('bscan-last').textContent,
            visual: fly
                ? {
                      count: document.querySelectorAll('[data-scan-success-fly]').length,
                      label: fly.querySelector('.scan-success-name')?.textContent || '',
                      increment: fly.querySelector('.scan-success-amount')?.textContent || '',
                      pointerEvents: getComputedStyle(fly).pointerEvents,
                  }
                : null,
            controls: {
                exists: !!controls,
                motionChecked: !!motion?.checked,
                motionLabel: motion?.parentElement?.textContent?.trim() || '',
                pointerEvents: controls ? getComputedStyle(controls).pointerEvents : '',
                torchHidden: !!torch?.hidden,
            },
            feedback: {
                ...window.__scanFeedback,
                crossings,
                active: [...samples].filter((v) => Math.abs(v) > 0.0001).length,
            },
        };
    });

    await page.click('#bscan-done');
    const closed = await page.evaluate(() => {
        const m = document.getElementById('bscan-mask');
        return {
            hidden: getComputedStyle(m).display === 'none',
            tracks: document.querySelectorAll('.bscan-video').length,
            controls: document.querySelectorAll('[data-scan-view-controls]').length,
            grand: document.getElementById('cart-grand').textContent,
            items: document.getElementById('cart-sub').textContent,
        };
    });
    if (tag === 'phone') {
        await page.screenshot({ path: path.join(SHOTS, '03-cart-after-done.png') });
    }
    await page.close();
    const ok =
        th.lang === 'th' &&
        starting.trim() === th.copy['posui.bscan.starting'] &&
        live.videoW > 0 &&
        live.playing &&
        live.frameVisible &&
        live.frameLive &&
        live.frameSize[0] === live.wantSize[0] &&
        live.frameSize[1] === live.wantSize[1] &&
        live.frameEqualsCrop &&
        live.frameInsidePicture &&
        live.doneH >= 44 &&
        live.doneLabel === th.copy['posui.bscan.done'] &&
        live.count === th.copy['posui.bscan.count'].replace('{n}', '1') &&
        live.last === th.copy['posui.bscan.added'].replace('{name}', 'โค้ก 325ml') &&
        live.visual &&
        live.visual.count === 1 &&
        live.visual.label === 'โค้ก 325ml' &&
        live.visual.increment === '+1' &&
        live.visual.pointerEvents === 'none' &&
        live.controls.exists &&
        live.controls.motionChecked &&
        live.controls.motionLabel === th.copy['scan-controls.animation'] &&
        live.controls.pointerEvents === 'auto' &&
        live.controls.torchHidden &&
        live.feedback.starts === 1 &&
        live.feedback.stops === 1 &&
        live.feedback.vibrates.join(',') === '60' &&
        live.feedback.buffer.channels === 1 &&
        live.feedback.buffer.length === 4800 &&
        live.feedback.crossings > 185 &&
        live.feedback.crossings < 200 &&
        live.feedback.active > 3500 &&
        closed.hidden &&
        closed.tracks === 0 && // destroy() 把自建的 video 摘掉了
        closed.controls === 0 &&
        closed.grand === '350.00'; // 扫箱码 = 箱价,不是默认瓶价 15
    return { ok, lang: th.lang, starting, live, closed };
}

// ── ② 未命中:码 + 建品指路 + 拿码去搜 ──────────────────────────────────
// 未命中不再弹单张卡(那张卡会被队列里下一件当场换掉),落在 #bscan-fails 这份清单上 ——
// 断言因此改读真行:一件失败 = 一行,行里带码、带指路、带那颗「拿这个码去搜」。
async function notFound(browser, origin) {
    const page = await browser.newPage({ viewport: PHONE });
    await page.addInitScript(seed);
    await routeBarcode(page, 'miss');
    await login(page, origin);
    const th = await dict(page);
    await page.click('#main-scan-btn');
    await page.waitForSelector('#bscan-fails.show .bscan-fail', { timeout: 25000 });
    await page.screenshot({ path: path.join(SHOTS, '04-notfound-fail-row.png') });
    const card = await page.evaluate(() => {
        const box = document.getElementById('bscan-fails');
        const row = box.querySelector('.bscan-fail');
        const act = row.querySelector('.bscan-fail-act');
        const cs = getComputedStyle(box);
        const rect = row.getBoundingClientRect();
        return {
            rows: box.querySelectorAll('.bscan-fail').length,
            msg: row.querySelector('.bscan-fail-msg').textContent,
            code: (row.querySelector('.bscan-code') || {}).textContent || '',
            hint: (row.querySelector('.bscan-fail-hint') || {}).textContent || '',
            actLabel: act.textContent,
            actHeight: act.getBoundingClientRect().height,
            headN: box.querySelector('.bscan-fails-n').textContent,
            ackLabel: box.querySelector('.bscan-fails-ack').textContent,
            // 摄像头层还开着(z=60)· 清单画在它之上才看得见 —— 「有面积」不等于「露在外面」
            onScreen: cs.display !== 'none' && cs.visibility !== 'hidden' && rect.height > 0,
            onTop: document
                .elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2)
                ?.closest('#bscan-fails')
                ? true
                : false,
        };
    });
    // 「用这个码搜商品」= 关层 + 把码填进搜索框 + 销掉这一条(已建档但没录条码的货靠这条救)
    await page.click('#bscan-fails .bscan-fail-act');
    const after = await page.evaluate(() => ({
        search: document.getElementById('main-search').value,
        hidden: getComputedStyle(document.getElementById('bscan-mask')).display === 'none',
        left: document.querySelectorAll('#bscan-fails .bscan-fail').length,
    }));
    await page.close();
    const ok =
        th.lang === 'th' &&
        card.rows === 1 &&
        card.code === CODE &&
        card.msg === th.copy['bscan.notfound'].replace('{code}', CODE) &&
        card.hint.trim() === th.copy['posui.bscan.create_where'] &&
        card.actLabel === th.copy['posui.bscan.search_code'] &&
        card.actHeight >= 44 &&
        card.headN === th.copy['posui.bscan.fails_n'].replace('{n}', '1') &&
        card.ackLabel === th.copy['posui.bscan.fails_ack'] &&
        card.onScreen &&
        card.onTop &&
        after.search === CODE &&
        after.hidden &&
        after.left === 0; // 带去搜索框了 = 这笔欠账销掉,别让店员照着清单再补一件
    return { ok, lang: th.lang, card, after };
}

// ── ③ 条码枪:主屏零 UI 扫一下就进车;光标在搜索框里时不抢 ────────────────
async function gun(browser, origin) {
    const page = await browser.newPage({ viewport: PHONE });
    await page.addInitScript(seed);
    await routeBarcode(page, 'hit');
    await login(page, origin);
    const th = await dict(page);
    await page.keyboard.type(CODE, { delay: 0 }); // 枪速
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => document.getElementById('cart-grand').textContent !== '0.00', {
        timeout: 8000,
    });
    // toast 有 .25s 淡入:光断 class 有 'show' 是假绿(截图上什么都看不见)。等真透明度上来再拍。
    await page.waitForFunction(
        () => parseFloat(getComputedStyle(document.getElementById('pos-toast')).opacity) > 0.9,
        null,
        { timeout: 3000 }
    );
    await page.screenshot({ path: path.join(SHOTS, '05-gun-toast.png') });
    const afterGun = await page.evaluate(() => {
        const el = document.getElementById('pos-toast');
        const box = el.getBoundingClientRect();
        // 真的画在屏幕上、没被顶栏盖住:取中心点问一句"这里最上面那层是谁"。
        // toast 自带 pointer-events:none(不挡点击),而 elementFromPoint 会跳过这种元素 →
        // 探测期间临时打开命中测试(不影响绘制层序),这样问出来的才是真的"谁在最上面"。
        const prev = el.style.pointerEvents;
        el.style.pointerEvents = 'auto';
        const hitEl = document.elementFromPoint(box.left + box.width / 2, box.top + box.height / 2);
        el.style.pointerEvents = prev;
        return {
            grand: document.getElementById('cart-grand').textContent,
            toast: document.getElementById('pos-toast-txt').textContent,
            toastOpacity: getComputedStyle(el).opacity,
            toastOnTop: !!(hitEl && el.contains(hitEl)),
            maskHidden: getComputedStyle(document.getElementById('bscan-mask')).display === 'none',
        };
    });
    // 店员正在搜索框里打字 → 枪不抢键(否则输入框吞字)
    await page.click('#main-search');
    await page.keyboard.type('8850999320007', { delay: 0 });
    await page.keyboard.press('Enter');
    const typed = await page.evaluate(() => ({
        value: document.getElementById('main-search').value,
        grand: document.getElementById('cart-grand').textContent,
    }));
    await page.close();
    const ok =
        th.lang === 'th' &&
        afterGun.grand === '350.00' &&
        parseFloat(afterGun.toastOpacity) > 0.9 &&
        afterGun.toastOnTop &&
        afterGun.toast === th.copy['posui.bscan.added'].replace('{name}', 'โค้ก 325ml') &&
        afterGun.maskHidden && // 枪走的路不该弹出取景层
        typed.value === '8850999320007' &&
        typed.grand === '350.00'; // 搜索框里打的字没被当成扫码
    return { ok, lang: th.lang, afterGun, typed };
}

// ── ④ 相机用不了:说清原因 + 手输弹窗摆上来(不静默隐藏入口)──────────────
function killCamera() {
    Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: undefined });
}

async function manualFallback(browser, origin) {
    const page = await browser.newPage({ viewport: PHONE });
    await page.addInitScript(seed);
    await page.addInitScript(killCamera);
    await routeBarcode(page, 'hit');
    await login(page, origin);
    const th = await dict(page);
    await page.click('#main-scan-btn');
    await page.waitForSelector('#pad-mask.show', { timeout: 5000 });
    await page.screenshot({ path: path.join(SHOTS, '06-manual-fallback.png') });
    const state = await page.evaluate(() => {
        const note = document.getElementById('pad-label');
        return {
            note: note.textContent,
            noteVisible: getComputedStyle(note).display !== 'none',
            padTitle: document.getElementById('pad-title').textContent,
            maskHidden: getComputedStyle(document.getElementById('bscan-mask')).display === 'none',
        };
    });
    // 手输的码走同一条取件路:填 13 位 → 确定 → 进车
    for (const d of CODE.split('')) await page.click(`#pad-keypad .key[data-key="${d}"]`);
    await page.click('#pad-confirm');
    await page.waitForFunction(() => document.getElementById('cart-grand').textContent !== '0.00', {
        timeout: 8000,
    });
    const grand = await text(page, '#cart-grand');
    await page.close();
    const ok =
        th.lang === 'th' &&
        state.noteVisible &&
        state.note === th.copy['bscan.err.unsupported'] &&
        state.maskHidden &&
        state.padTitle.trim().length > 0 &&
        grand === '350.00';
    return { ok, lang: th.lang, state, grand };
}

// ── ⑤ 加不进车必须出声 + 连扫一件不丢 ─────────────────────────────────
// 都走条码枪那条零 UI 的路(取景层不开):拒收卡自己撑一层暗底,连扫的积压落在 toast 上。
const NO_PRICE = '8850999320021'; // 「ลัง」只为库存换算而建,售价栏空着
const UNIT_GONE = '8850999320038'; // 只建了「箱」一条单位行,后端靠主码命中回基本单位「ขวด」
const BURST = ['8850999320045', '8850999320052', '8850999320069']; // 三件不同的货 · 10+25+18

function simple(id, name, unitName, barcode, price, matched) {
    return {
        id,
        name: { th: name, en: name, zh: name, ja: name },
        category_id: 1,
        base_unit: unitName,
        image_url: null,
        vat_applicable: true,
        units: [{ unit_name: unitName, factor: '1.000', barcode, price, default_sell: true }],
        track_batch: false,
        is_weighed: false,
        stock: { qty_base: '10.000', near_expiry: false },
        matched_unit: matched === undefined ? unitName : matched,
    };
}

function refusalCatalog() {
    const noPrice = product('ลัง');
    noPrice.units[1].price = null;
    const gone = simple('e2e-box', 'โค้กยกลัง', 'ลัง', UNIT_GONE, '350.00', 'ขวด');
    gone.base_unit = 'ขวด';
    return {
        [NO_PRICE]: noPrice,
        [UNIT_GONE]: gone,
        [BURST[0]]: simple('e2e-water', 'น้ำเปล่า', 'ขวด', BURST[0], '10.00'),
        [BURST[1]]: simple('e2e-bread', 'ขนมปัง', 'ถุง', BURST[1], '25.00'),
        [BURST[2]]: simple('e2e-milk', 'นมจืด', 'กล่อง', BURST[2], '18.00'),
    };
}

async function refusals(browser, origin) {
    const page = await browser.newPage({ viewport: PHONE });
    await page.addInitScript(seed);
    const catalog = refusalCatalog();
    await page.route('**/api/pos/products/by-barcode*', async (route) => {
        const code = new URL(route.request().url()).searchParams.get('code');
        const hit = catalog[code];
        // 后端往返 300ms 是店里的常态:连扫的后两件必然落在「上一件还没回来」的窗口里。
        if (hit) await new Promise((r) => setTimeout(r, 300));
        route.fulfill({
            status: hit ? 200 : 404,
            contentType: 'application/json',
            body: JSON.stringify(
                hit
                    ? { ok: true, data: hit }
                    : { ok: false, error: { code: 'pos.product_not_found', detail: null } }
            ),
        });
    });
    await login(page, origin);
    const th = await dict(page);

    // 拒收两档也进 #bscan-fails 清单 —— 读最新那一行(pushFail 把新的排最上面)。
    const topFail = () =>
        page.evaluate(() => {
            const row = document.querySelector('#bscan-fails .bscan-fail');
            const msg = row.querySelector('.bscan-fail-msg');
            const cs = getComputedStyle(row);
            return {
                text: msg.textContent,
                hint: (row.querySelector('.bscan-fail-hint') || {}).textContent || '',
                code: (row.querySelector('.bscan-fail-code') || {}).textContent || '',
                visible:
                    cs.display !== 'none' &&
                    cs.visibility !== 'hidden' &&
                    row.getBoundingClientRect().height > 0,
                grand: document.getElementById('cart-grand').textContent,
            };
        });
    const failRows = () => page.locator('#bscan-fails .bscan-fail').count();
    const gunScan = async (code) => {
        await page.keyboard.type(code, { delay: 0 });
        await page.keyboard.press('Enter');
    };

    await gunScan(NO_PRICE);
    await page.waitForSelector('#bscan-fails.show .bscan-fail', { timeout: 8000 });
    await page.screenshot({ path: path.join(SHOTS, '08-unit-no-price.png') });
    const noPrice = await topFail();

    await gunScan(UNIT_GONE);
    await page.waitForFunction(
        () => document.querySelectorAll('#bscan-fails .bscan-fail').length === 2,
        { timeout: 8000 }
    );
    await page.screenshot({ path: path.join(SHOTS, '09-unit-unknown.png') });
    const unitGone = await topFail();
    // 两条并存 = 清单不被下一件抹掉。清一遍再验连扫,免得混淆。
    const bothKept = await failRows();
    await page.click('#bscan-fails .bscan-fails-ack');

    // 连扫:三个码在第一件查回来之前全打进去,一件都不许少。toast 是转瞬即逝的,
    // 包一层把每条都记下来(只旁听,原函数照跑)。
    await page.evaluate(() => {
        window.__toasts = [];
        const orig = window.POS.toast;
        window.POS.toast = (m, t) => {
            window.__toasts.push(m);
            return orig(m, t);
        };
    });
    for (const code of BURST) await gunScan(code);
    await page.waitForFunction(
        () => document.getElementById('cart-grand').textContent === '53.00',
        {
            timeout: 15000,
        }
    );
    await page.screenshot({ path: path.join(SHOTS, '10-burst-three.png') });
    const burst = await page.evaluate(() => ({
        grand: document.getElementById('cart-grand').textContent,
        lines: [...document.querySelectorAll('#cart-lines .li-nm .n')].map((e) => e.textContent),
        toasts: window.__toasts,
        visuals: [...document.querySelectorAll('[data-scan-success-fly]')].map((el) => ({
            label: el.querySelector('.scan-success-name')?.textContent || '',
            pointerEvents: getComputedStyle(el).pointerEvents,
        })),
    }));
    await page.close();

    const q = (n) => th.copy['posui.bscan.queued'].replace('{n}', String(n));
    const ok =
        th.lang === 'th' &&
        noPrice.visible &&
        noPrice.text ===
            th.copy['posui.cart.unit_no_price']
                .replace('{unit}', 'ลัง')
                .replace('{name}', 'โค้ก 325ml') &&
        noPrice.hint === th.copy['posui.cart.fix_in_backoffice'] &&
        noPrice.grand === '0.00' && // ฿0 的整箱货没能混进车
        unitGone.visible &&
        unitGone.text ===
            th.copy['posui.cart.unit_unknown']
                .replace('{unit}', 'ขวด')
                .replace('{name}', 'โค้กยกลัง') &&
        unitGone.grand === '0.00' && // 也没按箱价 ฿350 收
        bothKept === 2 && // 第二件失败没把第一件顶掉
        burst.grand === '53.00' &&
        burst.lines.join('|') === 'น้ำเปล่า|ขนมปัง|นมจืด' && // 落地顺序 = 扫的顺序
        burst.visuals.length >= 2 && // 前一件还在飞,下一件已经独立进车
        burst.visuals.every((visual) => visual.pointerEvents === 'none') &&
        burst.toasts.includes(q(1)) &&
        burst.toasts.includes(q(2));
    return { ok, lang: th.lang, noPrice, unitGone, bothKept, burst };
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
        phoneHit: await liveHit(browser, origin, PHONE, 'phone'),
        desktopHit: await liveHit(browser, origin, { width: 1280, height: 800 }, 'desktop'),
        notFound: await notFound(browser, origin),
        gun: await gun(browser, origin),
        manualFallback: await manualFallback(browser, origin),
        refusals: await refusals(browser, origin),
        costVisibility: await costVisibility(browser, origin),
    };
    await browser.close();
    server.close();

    const failed = Object.keys(report).filter((k) => !report[k].ok);
    console.log(JSON.stringify(report, null, 2));
    console.log(failed.length ? `FAIL: ${failed.join(', ')}` : `PASS · 截图在 ${SHOTS}`);
    process.exit(failed.length ? 1 : 0);
})().catch((e) => {
    console.error('POS SCAN SMOKE CRASH', e);
    process.exit(2);
});
