/*
 * scripts/_hostile_scan_cam_verify.cjs · 对抗素材验收(摄像头连扫去重 · 真相机真解码)
 *
 * 上一轮那份抖动素材是「清晰 19 帧 + 糊 11 帧」的固定周期 —— 读不出的帧永远连成整齐的一段。
 * 真机上手抖/对焦/反光是散着落的:偶尔连糊三帧,偶尔隔一帧就成。这一份改喂单帧成功率
 * p=0.8 / 0.6 / 0.5 的随机丢帧素材(seed 写死,丢帧位置随机而结论可复现),打的是同一条判据:
 * 「这个码有多久没再被解出来」。素材自己把最长连续读不出印出来,三档都远小于 clearAfterMs
 * (1200ms)—— 越过那条线就该算真的离开画面,再断「只记一件」是在验一条不存在的规矩。
 *
 * 真的东西:Chromium 假摄像头喂真合成 EAN-13(桌面 Chromium 没有原生 BarcodeDetector,
 * 走的是本仓 dist/zxing.js 真解码);pos.html + dist/pos.js 是真产物。桩只有 by-barcode 回包。
 *
 * 跑法(仓库根目录):
 *   python scripts/_scan_ean_pjitter_y4m.py .p80.y4m 0.8 13
 *   python scripts/_scan_ean_pjitter_y4m.py .p60.y4m 0.6 5
 *   python scripts/_scan_ean_pjitter_y4m.py .p50.y4m 0.5 3
 *   node scripts/_hostile_scan_cam_verify.cjs
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('@playwright/test');
const { ROOT, PHONE, serve, shotter } = require('./_gun_wedge_lib.cjs');

const SHOTS = path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/fix2');
const shot = shotter(SHOTS);
const BOX = '8850999320014';

// 后两条是「一次长反光」:素材里的空白只有 600 / 800ms,远小于 clearAfterMs(1200)。
// 但解码器自己要花时间 —— ZXing 解不出的一帧实测 ~120ms,加上 intervalMs 120,一个「读不出」
// 的采样周期约 240ms,于是【观测到的】空白比素材里的长一截。这两条量的就是那一截有多长。
const FIXTURES = [
    ['p80', path.resolve('.p80.y4m')],
    ['p60', path.resolve('.p60.y4m')],
    ['p50', path.resolve('.p50.y4m')],
    ['gap600', path.resolve('.g600.y4m')],
    ['gap800', path.resolve('.g800.y4m')],
];

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

async function run(browser, origin, label) {
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
    // 等第一次真解出来(相机出帧 + ZXing 下载),再让整段素材跑完
    await page
        .waitForFunction(
            () => (document.getElementById('bscan-last').textContent || '').length > 0,
            null,
            { timeout: 45000 }
        )
        .catch(() => {});
    await page.waitForTimeout(7000);
    const state = await page.evaluate(() => ({
        count: document.getElementById('bscan-count').textContent,
        last: document.getElementById('bscan-last').textContent,
        qtys: [...document.querySelectorAll('#cart-lines .q[data-qi]')].map((e) => e.textContent),
        grand: document.getElementById('cart-grand').textContent,
    }));
    await shot(page, `c-${label}-jitter.png`);
    await page.close();
    // 两次取件之间隔了多久 = 引擎认为「这个码离开画面」了多久。素材里的空白只有几百毫秒,
    // 这个数才是判据真正吃到的那个数 —— 差出来的就是解码器自己烧掉的墙钟。
    const gaps = asked.slice(1).map((a, i) => a.at - asked[i].at);
    return { label, state, lookups: asked.length, asked, gaps };
}

(async () => {
    for (const [, f] of FIXTURES) {
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
      for (let rep = 1; rep <= REPEATS; rep++) {
        const label = REPEATS > 1 ? `${label0}#${rep}` : label0;
        const browser = await chromium.launch({
            args: [
                '--use-fake-ui-for-media-stream',
                '--use-fake-device-for-media-stream',
                `--use-file-for-fake-video-capture=${y4m}`,
            ],
        });
        let row;
        try {
            row = await run(browser, origin, label);
        } catch (e) {
            row = { label, crash: String(e && e.message ? e.message : e) };
        }
        await browser.close();
        // 一直举在框里没动过 = 一件。屏上件数、购物车数量、真发出去的查询次数三处都得是 1。
        row.ok =
            !!row.state &&
            /(^|\D)1(\D|$)/.test(row.state.count) &&
            row.state.qtys.join(',') === '1' &&
            row.lookups === 1;
        report[label] = row;
        console.log(
            `${row.ok ? 'PASS' : 'FAIL'} ${label} n=${row.lookups} gaps=${JSON.stringify(
                row.gaps || []
            )} ${JSON.stringify(row.state || {})}`
        );
      }
    }
    fs.writeFileSync(
        path.join(SHOTS, 'report-hostile-cam.json'),
        JSON.stringify(report, null, 2)
    );
    server.close();
    process.exit(Object.values(report).every((r) => r.ok) ? 0 : 1);
})().catch((e) => {
    console.error('HOSTILE CAM CRASH', e);
    process.exit(2);
});
