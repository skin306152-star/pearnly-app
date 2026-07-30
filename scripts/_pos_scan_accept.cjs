/*
 * scripts/_pos_scan_accept.cjs · 收银台摄像头扫码的独立验收(第二双眼睛)
 *
 * 与 _pos_scan_smoke.cjs 的分工:那个是施工者自己的回归脚本,这个是验收脚本,专挑它没验到的
 * 五处 —— 真被拒权限、超时的重试入口、解码器拉不下来的重试入口、iOS 回落真的去拉了
 * dist/zxing.js、关层后相机轨道真的 ended。另有一条硬规矩上的不同:
 *
 *   本脚本一个字的文案都不注入。期望值全部现场从页面里的真 window.POS_I18N 取(那是
 *   static/pos/pos-i18n.js 的真产物),再自己做 {code}/{n}/{name} 代入。测试自带一份文案
 *   去比对,等于拿桩验桩 —— 键没落地也照样绿。
 *
 * 桩只有三处,都不是界面:① /api/pos/products/by-barcode 的信封(后端归 routes 单测);
 * ② 其余 /api/pos/* 让静态服务 404 → POS 自己的本地预览目录;③ 个别档位的 getUserMedia
 * (哪几档、为什么,见各 case 头上的注释,报告里逐条标注)。
 *
 * 用法(仓库根目录):
 *   python scripts/_scan_ean_y4m.py <fixture.y4m>
 *   node scripts/_pos_scan_accept.cjs <fixture.y4m> [截图目录]
 * 退出码 0 = 全过。截图默认落 tests/e2e/_artifacts/pos_barcode_scan/。
 */
const fs = require('fs');
const http = require('http');
const path = require('path');
const { chromium } = require('@playwright/test');

const ROOT = path.resolve(__dirname, '..');
const Y4M = path.resolve(process.argv[2] || '.scan_fixture.y4m');
const SHOTS = path.resolve(
    process.argv[3] || path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan')
);
const CODE = '8850999320014'; // 假摄像头画面里那张真 EAN-13(泰国 GS1 前缀 885)
const BOTTLE = '8850999320007'; // 同商品的瓶码 · 用来证明扫箱码不是碰巧对上默认单位
const MIME = { '.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html' };
const PHONE = { width: 390, height: 780 };
const DESKTOP = { width: 1280, height: 800 };
const FAKE_CAM = ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'];

function serve() {
    const server = http.createServer((req, res) => {
        const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '');
        const fp = path.join(ROOT, rel);
        const ok = fp.startsWith(ROOT) && fs.existsSync(fp) && !fs.statSync(fp).isDirectory();
        res.writeHead(ok ? 200 : 404, {
            'content-type': ok ? MIME[path.extname(fp)] || 'application/octet-stream' : 'text/html',
        });
        if (ok) fs.createReadStream(fp).pipe(res);
        else res.end('not found');
    });
    return new Promise((r) => server.listen(0, '127.0.0.1', () => r(server)));
}

// 设备已绑店但不带账套 id → POS.allowMock() 为真,店员/商品走本地预览目录。
function seed(lang) {
    localStorage.setItem('pos_store_token', 'accept-eyes');
    localStorage.setItem('pos_store_name', 'ร้าน ACCEPT');
    localStorage.setItem('mrpilot_lang', lang);
}

// 纯旁听:原样调真 getUserMedia,只把 track 和 video 元素记下来,好在关层后问它们死没死。
function instrument() {
    window.__tracks = [];
    const md = navigator.mediaDevices;
    if (!md || !md.getUserMedia) return;
    const orig = md.getUserMedia.bind(md);
    md.getUserMedia = function (c) {
        return orig(c).then(function (s) {
            window.__tracks = window.__tracks.concat(s.getTracks());
            return s;
        });
    };
}

function product(matchedUnit) {
    return {
        id: 'accept-coke',
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

async function login(page, origin) {
    await page.goto(`${origin}/static/pos/pos.html`);
    await page.waitForSelector('#login-cashiers .ca', { timeout: 15000 });
    for (const d of ['1', '2', '3', '4']) await page.click(`#view-login .pad .k[data-pin="${d}"]`);
    await page.waitForSelector('#shift-mask.show', { timeout: 10000 });
    await page.click('#shift-open-go');
    await page.waitForSelector('#view-main.is-active', { timeout: 10000 });
    await page.waitForSelector('#main-grid .prod', { timeout: 10000 });
}

// 真词典(static/pos/pos-i18n.js 的真产物)。期望文案只能从这里来。
const dict = (page, lang) => page.evaluate((l) => window.POS_I18N[l], lang);
const fmt = (s, vars) =>
    Object.keys(vars || {}).reduce((acc, k) => acc.split('{' + k + '}').join(vars[k]), String(s));

// 真可见性:computed style + 真盒子 + 中心点命中测试(「画在最上面」不靠类名判断)
async function seen(page, sel) {
    const vis = await page.locator(sel).isVisible();
    const probe = await page.evaluate((s) => {
        const el = document.querySelector(s);
        if (!el) return null;
        const cs = getComputedStyle(el);
        const b = el.getBoundingClientRect();
        const top = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2);
        return {
            display: cs.display,
            visibility: cs.visibility,
            opacity: cs.opacity,
            w: Math.round(b.width),
            h: Math.round(b.height),
            inViewport: b.top >= -1 && b.left >= -1 && b.bottom <= innerHeight + 1,
            onTop: !!(top && (el.contains(top) || el === top || top.contains(el))),
            text: (el.textContent || '').trim(),
        };
    }, sel);
    return Object.assign({ isVisible: vis }, probe);
}

const painted = (s) =>
    !!s &&
    s.isVisible &&
    s.display !== 'none' &&
    s.visibility === 'visible' &&
    parseFloat(s.opacity) > 0.9 &&
    s.w > 0 &&
    s.h > 0;

// ── ① 相机层真显示 + 真解码进车 + 关层真放相机 ────────────────────────────
async function cameraToCart(browser, origin, viewport, tag) {
    const page = await browser.newPage({ viewport });
    await page.addInitScript(seed, 'th');
    await page.addInitScript(instrument);
    await routeBarcode(page, 'hit');
    const zxingHits = [];
    page.on('request', (r) => {
        if (r.url().indexOf('/static/dist/zxing.js') >= 0) zxingHits.push(r.url());
    });
    await login(page, origin);
    const th = await dict(page, 'th');

    await page.click('#main-scan-btn');
    await page.waitForSelector('#bscan-mask.show', { timeout: 5000 });
    const starting = await seen(page, '#bscan-hint');
    const mask = await seen(page, '#bscan-mask');

    await page.waitForFunction(
        () => (document.getElementById('bscan-last').textContent || '').length > 0,
        null,
        { timeout: 30000 }
    );
    const video = await page.evaluate(() => {
        const v = document.querySelector('.bscan-video');
        if (!v) return null;
        const cs = getComputedStyle(v);
        const b = v.getBoundingClientRect();
        window.__vid = v; // 关层后还要问它 srcObject 有没有清
        return {
            display: cs.display,
            objectFit: cs.objectFit,
            w: Math.round(b.width),
            h: Math.round(b.height),
            videoW: v.videoWidth,
            videoH: v.videoHeight,
            readyState: v.readyState,
            hasStream: !!v.srcObject,
        };
    });
    const frame = await seen(page, '#bscan-frame');
    const aim = await seen(page, '#bscan-hint');
    const bar = await page.evaluate(() => ({
        count: document.getElementById('bscan-count').textContent,
        last: document.getElementById('bscan-last').textContent,
        done: document.getElementById('bscan-done').textContent,
    }));
    await page.screenshot({
        path: path.join(
            SHOTS,
            tag === 'phone' ? 'cam-01-camera-live-390.png' : 'cam-11-camera-live-1280.png'
        ),
    });

    // 移动端不破版:没有横向溢出,底部条与「完成」整体在视口内
    const layout = await page.evaluate(() => {
        const doc = document.documentElement;
        const d = document.getElementById('bscan-done').getBoundingClientRect();
        const b = document.querySelector('.bscan-bar').getBoundingClientRect();
        const f = document.getElementById('bscan-frame').getBoundingClientRect();
        return {
            hOverflow: doc.scrollWidth - doc.clientWidth,
            doneInside: d.right <= innerWidth + 1 && d.bottom <= innerHeight + 1,
            doneH: Math.round(d.height),
            barInside: b.right <= innerWidth + 1 && b.bottom <= innerHeight + 1,
            frameBelowBar: f.bottom <= b.top + 1,
            frameInside: f.left >= -1 && f.right <= innerWidth + 1,
        };
    });

    await page.click('#bscan-done');
    const closed = await page.evaluate(() => ({
        maskHidden: getComputedStyle(document.getElementById('bscan-mask')).display === 'none',
        videoGone: document.querySelectorAll('.bscan-video').length === 0,
        srcObjectNull: window.__vid ? window.__vid.srcObject === null : null,
        detached: window.__vid ? !window.__vid.isConnected : null,
        trackCount: window.__tracks.length,
        trackStates: window.__tracks.map((t) => t.readyState),
        grand: document.getElementById('cart-grand').textContent,
        lines: [...document.querySelectorAll('#cart-lines')].map((n) => n.textContent.trim()),
    }));
    if (tag === 'phone')
        await page.screenshot({ path: path.join(SHOTS, 'cam-02-cart-box-price.png') });
    await page.close();

    const wantCount = fmt(th['posui.bscan.count'], { n: 1 });
    const wantAdded = fmt(th['posui.bscan.added'], { name: 'โค้ก 325ml' });
    return {
        ok:
            painted(mask) &&
            starting.text === th['posui.bscan.starting'] &&
            aim.text === th['posui.bscan.aim'] &&
            painted(frame) &&
            frame.onTop &&
            !!video &&
            video.videoW > 0 &&
            video.readyState >= 2 &&
            video.hasStream &&
            video.w > 0 &&
            bar.count === wantCount &&
            bar.last === wantAdded &&
            bar.done === th['posui.bscan.done'] &&
            layout.hOverflow <= 0 &&
            layout.doneInside &&
            layout.doneH >= 44 &&
            layout.barInside &&
            layout.frameBelowBar &&
            layout.frameInside &&
            closed.maskHidden &&
            closed.videoGone &&
            closed.srcObjectNull === true &&
            closed.detached === true &&
            closed.trackCount > 0 &&
            closed.trackStates.every((s) => s === 'ended') &&
            closed.grand === '350.00' && // 箱价 · 不是默认瓶价 15
            closed.lines.join('').indexOf('โค้ก 325ml') >= 0 &&
            zxingHits.length > 0,
        starting,
        mask,
        video,
        frame,
        bar,
        layout,
        closed,
        zxingHits,
    };
}

// ── ② 未命中:扫到的那串码真的显示在屏幕上 ────────────────────────────────
async function missShowsCode(browser, origin) {
    const page = await browser.newPage({ viewport: PHONE });
    await page.addInitScript(seed, 'th');
    await routeBarcode(page, 'miss');
    await login(page, origin);
    const th = await dict(page, 'th');
    await page.click('#main-scan-btn');
    await page.waitForSelector('#bscan-card.show', { timeout: 30000 });
    const code = await seen(page, '#bscan-card-msg .bscan-code');
    const msg = await seen(page, '#bscan-card-msg');
    const hint = await seen(page, '#bscan-card-hint');
    await page.screenshot({ path: path.join(SHOTS, 'cam-03-notfound-code-390.png') });
    const acts = await page.evaluate(() =>
        [...document.querySelectorAll('#bscan-acts .bscan-act')].map((b) => ({
            label: b.textContent,
            h: Math.round(b.getBoundingClientRect().height),
            visible: getComputedStyle(b).display !== 'none',
        }))
    );
    const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth
    );
    await page.click('#bscan-acts .bscan-act:nth-child(2)');
    const after = await page.evaluate(() => ({
        search: document.getElementById('main-search').value,
        hidden: getComputedStyle(document.getElementById('bscan-mask')).display === 'none',
    }));
    await page.close();
    return {
        ok:
            painted(code) &&
            code.onTop &&
            code.text === CODE &&
            msg.text === fmt(th['bscan.notfound'], { code: CODE }) &&
            hint.text === th['posui.bscan.create_where'] &&
            acts.length === 2 &&
            acts.every((a) => a.visible && a.h >= 44) &&
            acts[0].label === th['posui.bscan.continue'] &&
            acts[1].label === th['posui.bscan.search_code'] &&
            overflow <= 0 &&
            after.search === CODE &&
            after.hidden,
        code,
        msg,
        hint,
        acts,
        overflow,
        after,
    };
}

// ── 四语:同一层界面换语言后画的是那门语言的真词条(不是漏译回落泰文)────────────
async function langCopy(browser, origin) {
    const out = {};
    for (const lang of ['th', 'en', 'zh', 'ja']) {
        const page = await browser.newPage({ viewport: PHONE });
        await page.addInitScript(seed, lang);
        await routeBarcode(page, 'miss');
        await login(page, origin);
        const d = await dict(page, lang);
        await page.click('#main-scan-btn');
        await page.waitForSelector('#bscan-card.show', { timeout: 30000 });
        const got = await page.evaluate(() => ({
            msg: document.getElementById('bscan-card-msg').textContent.trim(),
            hint: document.getElementById('bscan-card-hint').textContent.trim(),
            code: (document.querySelector('#bscan-card-msg .bscan-code') || {}).textContent || '',
            done: document.getElementById('bscan-done').textContent,
            acts: [...document.querySelectorAll('#bscan-acts .bscan-act')].map(
                (b) => b.textContent
            ),
        }));
        if (lang === 'zh' || lang === 'en') {
            await page.screenshot({ path: path.join(SHOTS, `cam-10-notfound-${lang}.png`) });
        }
        await page.close();
        out[lang] = {
            ok:
                got.msg === fmt(d['bscan.notfound'], { code: CODE }) &&
                got.hint === d['posui.bscan.create_where'].trim() &&
                got.code === CODE &&
                got.done === d['posui.bscan.done'] &&
                got.acts.join('|') ===
                    [d['posui.bscan.continue'], d['posui.bscan.search_code']].join('|'),
            got,
        };
    }
    return { ok: Object.values(out).every((v) => v.ok), byLang: out };
}

// 按钮上写的字就是找它的唯一凭据(顺序会随档位变,不能写死下标)
async function clickAct(page, label) {
    const i = await page.evaluate(
        (t) =>
            [...document.querySelectorAll('#bscan-acts .bscan-act')].findIndex(
                (b) => b.textContent === t
            ),
        label
    );
    if (i < 0) throw new Error('卡上没有这个按钮: ' + label);
    // SELECTOR-INDEX-OK: i 是上面按按钮文案算出来的(找不到就抛)· 身份是文案不是位置
    await page.locator('#bscan-acts .bscan-act').nth(i).click();
}

// 卡片上的那句话 + 手输出路(错误档共用的断言)
async function errorCard(page, shot) {
    await page.waitForSelector('#bscan-card.show', { timeout: 30000 });
    const msg = await seen(page, '#bscan-card-msg');
    const acts = await page.evaluate(() =>
        [...document.querySelectorAll('#bscan-acts .bscan-act')].map((b) => ({
            label: b.textContent,
            h: Math.round(b.getBoundingClientRect().height),
            visible: getComputedStyle(b).display !== 'none',
        }))
    );
    if (shot) await page.screenshot({ path: path.join(SHOTS, shot) });
    return { msg, acts };
}

// ── ③ 真被拒:不给 --use-fake-ui,让真 Chromium 自己拒(实测发 NotSupportedError)────
async function realDenied(origin) {
    const browser = await chromium.launch({
        args: ['--use-fake-device-for-media-stream', `--use-file-for-fake-video-capture=${Y4M}`],
    });
    const page = await browser.newPage({ viewport: PHONE });
    await page.addInitScript(seed, 'th');
    await routeBarcode(page, 'hit');
    await login(page, origin);
    const th = await dict(page, 'th');
    const gum = await page.evaluate(() =>
        navigator.mediaDevices
            .getUserMedia({ video: true })
            .then(() => 'granted')
            .catch((e) => e.name)
    );
    await page.click('#main-scan-btn');
    const card = await errorCard(page, 'cam-04-camera-denied-real.png');
    await clickAct(page, th['bscan.manual']);
    await page.waitForSelector('#pad-mask.show', { timeout: 5000 });
    const pad = await seen(page, '#pad-label');
    await browser.close();
    const expect = th[gum === 'NotAllowedError' ? 'bscan.err.permission' : 'bscan.err.unsupported'];
    return {
        ok:
            gum !== 'granted' &&
            painted(card.msg) &&
            card.msg.text === expect &&
            card.msg.text.length > 10 &&
            card.acts.some((a) => a.label === th['bscan.manual'] && a.visible && a.h >= 44) &&
            painted(pad) &&
            pad.text === expect,
        gumError: gum,
        card,
        pad,
    };
}

// ── ④ 权限被拒那一档的文案(getUserMedia 打桩发 NotAllowedError · 报告里标为桩)──────
async function permissionCopy(browser, origin) {
    const page = await browser.newPage({ viewport: PHONE });
    await page.addInitScript(seed, 'th');
    await page.addInitScript(() => {
        navigator.mediaDevices.getUserMedia = () =>
            Promise.reject(new DOMException('Permission denied', 'NotAllowedError'));
    });
    await routeBarcode(page, 'hit');
    await login(page, origin);
    const th = await dict(page, 'th');
    await page.click('#main-scan-btn');
    const card = await errorCard(page, 'cam-05-permission-denied-copy.png');
    await page.close();
    return {
        ok:
            painted(card.msg) &&
            card.msg.text === th['bscan.err.permission'] &&
            !card.acts.some((a) => a.label === th['posui.retry']) && // 权限档重试没意义
            card.acts.some((a) => a.label === th['bscan.manual'] && a.h >= 44),
        card,
    };
}

// ── ⑤ 超时:真 MediaStream 但永远不出帧(canvas.captureStream(0))→ 必须有重试入口 ──
async function timeoutRetry(browser, origin) {
    const page = await browser.newPage({ viewport: PHONE });
    await page.addInitScript(seed, 'th');
    await page.addInitScript(() => {
        // 真 MediaStream / 真 MediaStreamTrack,只是帧率 0 → 画面永远不 ready。
        // 素材层面造不出这种流(实测零帧 y4m 直接报 NotFoundError),只能从这一口换。
        navigator.mediaDevices.getUserMedia = () => {
            const c = document.createElement('canvas');
            c.width = 640;
            c.height = 480;
            c.getContext('2d').fillRect(0, 0, 1, 1);
            const s = c.captureStream(0);
            // captureStream(0) 自己会送第一帧(实测 readyState 直接到 4),摘掉轨道才是
            // 「相机开了但永远不出帧」—— 也就是 Odoo 那个 FIXME 死等的真实故障形态。
            s.getTracks().forEach((t) => s.removeTrack(t));
            return Promise.resolve(s);
        };
    });
    await routeBarcode(page, 'hit');
    await login(page, origin);
    const th = await dict(page, 'th');
    await page.click('#main-scan-btn');
    const card = await errorCard(page, 'cam-06-timeout-retry.png');
    const retry = card.acts.find((a) => a.label === th['posui.retry']);
    let restarted = null;
    if (retry) {
        await clickAct(page, th['posui.retry']);
        restarted = await page.evaluate(() => ({
            hint: document.getElementById('bscan-hint').textContent,
            cardHidden: !document.getElementById('bscan-card').classList.contains('show'),
        }));
    }
    await page.close();
    return {
        ok:
            painted(card.msg) &&
            card.msg.text === th['bscan.err.timeout'] &&
            !!retry &&
            retry.visible &&
            retry.h >= 44 &&
            !!restarted &&
            restarted.cardHidden &&
            restarted.hint === th['posui.bscan.starting'],
        card,
        restarted,
    };
}

// ── ⑥ 解码器拉不下来(真断网:abort dist/zxing.js)→ 重试入口 · 放开后真扫得出 ─────
async function decoderBlocked(browser, origin) {
    const page = await browser.newPage({ viewport: PHONE });
    await page.addInitScript(seed, 'th');
    await routeBarcode(page, 'hit');
    await page.route('**/static/dist/zxing.js*', (r) => r.abort('failed'));
    await login(page, origin);
    const th = await dict(page, 'th');
    await page.click('#main-scan-btn');
    const card = await errorCard(page, 'cam-07-decoder-blocked-retry.png');
    const retry = card.acts.find((a) => a.label === th['posui.retry']);
    await page.unroute('**/static/dist/zxing.js*');
    let recovered = null;
    if (retry) {
        await clickAct(page, th['posui.retry']);
        await page
            .waitForFunction(
                () => document.getElementById('cart-grand').textContent !== '0.00',
                null,
                { timeout: 30000 }
            )
            .catch(() => {});
        recovered = await page.evaluate(() => ({
            grand: document.getElementById('cart-grand').textContent,
            last: document.getElementById('bscan-last').textContent,
        }));
        await page.screenshot({ path: path.join(SHOTS, 'cam-08-decoder-retry-recovered.png') });
    }
    await page.close();
    return {
        ok:
            painted(card.msg) &&
            card.msg.text === th['bscan.err.decoder'] &&
            !!retry &&
            retry.h >= 44 &&
            !!recovered &&
            recovered.grand === '350.00',
        card,
        recovered,
    };
}

// ── ⑦ iOS 回落:没有 BarcodeDetector → 真的去拉 dist/zxing.js(带 ?v)且真解得出 ────
async function iosFallback(browser, origin) {
    const page = await browser.newPage({ viewport: PHONE });
    await page.addInitScript(seed, 'th');
    const reqs = [];
    page.on('request', (r) => {
        if (/\/static\/dist\/(zxing|scan)\.js/.test(r.url())) reqs.push(r.url());
    });
    await routeBarcode(page, 'hit');
    await login(page, origin);
    const nativeBefore = await page.evaluate(() => 'BarcodeDetector' in window);
    await page.evaluate(() => {
        delete window.BarcodeDetector;
    });
    await page.click('#main-scan-btn');
    await page.waitForFunction(
        () => (document.getElementById('bscan-last').textContent || '').length > 0,
        null,
        { timeout: 30000 }
    );
    await page.screenshot({ path: path.join(SHOTS, 'cam-09-ios-zxing-fallback.png') });
    const decoded = await page.evaluate(() => ({
        grand: document.getElementById('cart-grand').textContent,
        engine: !!window.ZXing && !!window.PearnlyScanZXing,
    }));
    await page.close();
    const zx = reqs.filter((u) => u.indexOf('zxing.js') >= 0);
    return {
        ok:
            zx.length > 0 &&
            /[?&]v=/.test(zx[0]) &&
            decoded.engine &&
            decoded.grand === '350.00' &&
            reqs.some((u) => u.indexOf('scan.js') >= 0),
        nativeBarcodeDetectorPresent: nativeBefore,
        requests: reqs,
    };
}

// 有原生 BarcodeDetector 时不该白拉 340KB(原生 Detector 是桩 · 验的是分支选择)
async function nativePathSkipsZxing(browser, origin) {
    const page = await browser.newPage({ viewport: PHONE });
    await page.addInitScript(seed, 'th');
    await page.addInitScript((code) => {
        window.BarcodeDetector = class {
            static getSupportedFormats() {
                return Promise.resolve(['ean_13']);
            }
            constructor() {}
            detect() {
                return Promise.resolve([{ rawValue: code, format: 'ean_13' }]);
            }
        };
    }, CODE);
    const reqs = [];
    page.on('request', (r) => {
        if (r.url().indexOf('zxing.js') >= 0) reqs.push(r.url());
    });
    await routeBarcode(page, 'hit');
    await login(page, origin);
    await page.click('#main-scan-btn');
    await page.waitForFunction(
        () => document.getElementById('cart-grand').textContent !== '0.00',
        null,
        { timeout: 20000 }
    );
    await page.close();
    return { ok: reqs.length === 0, zxingRequests: reqs };
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
        args: FAKE_CAM.concat([`--use-file-for-fake-video-capture=${Y4M}`]),
    });
    const report = {
        phoneCameraToCart: await cameraToCart(browser, origin, PHONE, 'phone'),
        desktopCameraToCart: await cameraToCart(browser, origin, DESKTOP, 'desktop'),
        missShowsCode: await missShowsCode(browser, origin),
        langCopy: await langCopy(browser, origin),
        permissionCopy: await permissionCopy(browser, origin),
        timeoutRetry: await timeoutRetry(browser, origin),
        decoderBlocked: await decoderBlocked(browser, origin),
        iosFallback: await iosFallback(browser, origin),
        nativePathSkipsZxing: await nativePathSkipsZxing(browser, origin),
    };
    await browser.close();
    report.realDenied = await realDenied(origin);
    server.close();

    const failed = Object.keys(report).filter((k) => !report[k].ok);
    fs.writeFileSync(path.join(SHOTS, 'camera-report.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report, null, 2));
    console.log(failed.length ? `FAIL: ${failed.join(', ')}` : `PASS · 截图在 ${SHOTS}`);
    process.exit(failed.length ? 1 : 0);
})().catch((e) => {
    console.error('POS SCAN ACCEPT CRASH', e);
    process.exit(2);
});
