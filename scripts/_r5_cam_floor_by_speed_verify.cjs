/*
 * scripts/_r5_cam_floor_by_speed_verify.cjs · 地板是解码器速度的函数 —— 三档机器各量一遍
 *
 * 去重判据是两把尺子 AND(墙钟 clearAfterMs 且连着 clearAfterMisses 次采样没解出),于是
 * 「同一个码隔多久才重新算得上一件」有个地板。地板跟机器走:采样那把尺子的刻度 = 一次
 * 【解不出】的采样要多久 —— 快机器十几毫秒、店里那台一百多、老安卓平板四百多。第四轮只在
 * 店里那台上量过,于是「换台机器地板会不会翻三倍」一个数都没有,而地板以下拿走 A 举回同款
 * 的 B 是不记账的。
 *
 * 本脚本三档解码器各跑一遍,两个方向一起量:
 *   反向 · 地板    离开多久才真能再记一件(bracket:地板下那一档不许再记、上那一档必须再记)
 *   反向 · 代价    地板以下【不许一声不吭】—— 屏上那行提示必须真看得见(真 DOM:有盒子、
 *                  不透明、在视口内),不是断 classList 有没有 show
 *   反向 · 静默区  告警门槛底下那一段(400/600ms)照样跑,量出还有多宽的空档是真没声音的;
 *                  判据是它必须留在 SWAP_FLOOR_MS 以下 —— 人手换货够不到那么快
 *   正向 · 别退回   举着不动(p=0.5 散帧)三档都必须仍然只有一件,钱一分不许多
 *
 * 三档解码器哪来的:
 *   native  桌面 Chromium 没有 BarcodeDetector,而安卓 Chrome 上引擎走的正是那条路。这一档
 *           装一个同形状的桩,它只回答「这一帧是清晰条码还是糊/白墙」,答得快 —— 本脚本要
 *           量的自变量就是「解码有多快」。判据、采样调度、去重全是真产品代码,一个字没改。
 *           桩跟真解码器把帧分成同一类,这件事由结果自证:同一份 blink 素材上两档的地板
 *           bracket 一模一样(1400 不认 / 1600 认),差的只有快慢。采样成功率则【不可跨档比】
 *           (见 readScreen 里那段:档越快,糊帧被采得越密)。
 *   zxing   本仓 dist/zxing.js 原样(店里那台平板就是这条路)。
 *   slow    同上,真解完再压 EXTRA_MS —— 一次采样 ≈400ms 的老机器。
 *
 * R5_LOWFLOOR=1 · 「那把地板压到 1.2 秒不就完了」的反证(见文件末 LOWFLOOR):
 *   把门槛真按那个提议改下去,再拿真素材跑正向那一侧。带对照组 —— 同一台机器同一份素材,
 *   只有改了门槛的那一跑多记货,才说得清多记是门槛改的、不是这一档本来就飘。
 *
 * 跑法(仓库根目录):
 *   python scripts/_scan_ean_blink_y4m.py .blink04.y4m 8850999320014 0.4
 *   python scripts/_scan_ean_blink_y4m.py .blink06.y4m 8850999320014 0.6
 *   python scripts/_scan_ean_blink_y4m.py .blink14.y4m 8850999320014 1.4
 *   python scripts/_scan_ean_blink_y4m.py .blink16.y4m 8850999320014 1.6
 *   python scripts/_scan_ean_blink_y4m.py .blink40.y4m 8850999320014 4.0
 *   python scripts/_scan_ean_blink_y4m.py .blink60.y4m 8850999320014 6.0
 *   python scripts/_scan_ean_pjitter_y4m.py .p50.y4m 0.5 3
 *   python scripts/_scan_ean_jitter_y4m.py .g1200.y4m 8850999320014 19 18
 *   python scripts/_scan_ean_jitter_y4m.py .g2800.y4m 8850999320014 19 42
 *   node scripts/_r5_cam_floor_by_speed_verify.cjs
 *   R5_LOWFLOOR=1 node scripts/_r5_cam_floor_by_speed_verify.cjs
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('@playwright/test');
const { ROOT, PHONE, serve, shotter } = require('./_gun_wedge_lib.cjs');

const SHOTS = path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/fix5');
const shot = shotter(SHOTS);
const BOX = '8850999320014';
// 真 ZXing 解不出一帧实测 114~121ms;+280 ≈ 400ms,配上 probeIntervalMs=15 就是一次采样
// ≈415ms 的老安卓平板 —— 店里真在用的那一档最慢的机器。
const EXTRA_MS = 280;
const HOLD_MS = 7000;
// 人把 A 拿开、再把同款的 B 举进取景框,手要走两趟四十来公分 —— 700ms 是这个动作的下限。
// 比它还短的空档产品仍然一声不吭(告警门槛 dupNoticeMs=800,减去引擎自己烧掉的一次采样,
// 折回真空档 ≈620ms);静默区不为零,但必须留在人手够不到的那一段以下,这条就是那个判据。
const SWAP_FLOOR_MS = 700;
const LOWFLOOR = process.env.R5_LOWFLOOR === '1';

const blinkFixture = (legMs) => path.resolve(`.blink${String(legMs / 100).padStart(2, '0')}.y4m`);

// 地板预测值 = max(clearAfterMs, clearAfterMisses × 一次失败采样)。native/zxing 由墙钟挡
// (12 次采样只要 ≈0.2s / ≈1.6s),slow 由采样数挡(12 × 415ms ≈ 5s)—— bracket 就照这个下注,
// 猜错了 bracket 会当场露(地板下那一档记了货 / 上那一档没记)。
// probeLegs 是告警门槛底下那一段:那里既不再记一件、也未必出声,静默区有多宽就由它量出来。
// 每一档都带 6000ms 那一腿:地板不是机器的常数,同一台机器忙起来解码就慢,采样那把尺子的
// 刻度跟着变粗 —— 实测同一份 dist/zxing.js,机器空着时一次失败采样 116ms(地板 1.4~1.6s)、
// 连着跑了四十分钟浏览器之后 240ms(地板爬到 ≈2.9s,1600ms 那一腿于是不再记第二件,改成出声)。
// 所以「必须存在地板」这条判据得钉在一个哪台机器都够得着的腿上,不然红的是机器状态不是产品。
const TIERS = [
    { name: 'native', native: true, probeLegs: [400, 600], legs: [1400, 1600, 6000] },
    { name: 'zxing', extraMs: 0, probeLegs: [400, 600], legs: [1400, 1600, 6000] },
    { name: 'slow', extraMs: EXTRA_MS, probeLegs: [600], legs: [1600, 4000, 6000] },
];

const seed = () => {
    localStorage.setItem('pos_store_token', 'r5-floor');
    localStorage.setItem('pos_store_name', 'ร้าน FLOOR');
    localStorage.setItem('mrpilot_lang', 'th');
};

// 解码器有多快 = 本脚本的自变量;判据一个字不改(cfg.patch 只在 LOWFLOOR 反证里给值)。
// 挂法必须是【确定性】的:scan.js 一落地 pos-scan.js 就同步 create(),轮询等它出现稳稳输 ——
// 所以在两个全局键上放存取器,谁来赋值都得从这儿过。
const installTier = (cfg) => {
    // 采样【周期】才是采样那把尺子的刻度:12 次没解出来要多久 = 12 × 这个数。单量解码耗时会
    // 漏掉引擎自己的 probeIntervalMs,也漏掉注进去的那点慢 —— 所以量的是两次 detect 之间隔多久。
    window.__dec = {
        hit: 0,
        miss: 0,
        failMs: [],
        cycleMs: [],
        last: 0,
        lastMiss: false,
        lastHit: 0,
        maxGapMs: 0,
    };
    const mark = (t0, ok) => {
        const d = window.__dec;
        const now = performance.now();
        // 只收「上一拍和这一拍都没解出来」的那些周期:解出来的那一拍前面跟着 probeIntervalMs
        // 但自己只花一两毫秒、后面又跟着 intervalMs(省电的常态间隔),两头都不是连续失败那一段
        // 的节拍。地板只由连续失败那一段决定,刻度就只能从那一段里取。
        if (d.last && d.lastMiss && !ok) d.cycleMs.push(Math.round(now - d.last));
        d.last = now;
        d.lastMiss = !ok;
        if (ok) {
            // 两次解出来之间隔了多久 —— 引擎在 accept 里看到的 gapMs 就是这个数。举着不动时
            // 它就是「这台机器最长能糊多久」,而给采样尺封顶的提议正是拿一个常数去赌它。
            if (d.lastHit) d.maxGapMs = Math.max(d.maxGapMs, Math.round(now - d.lastHit));
            d.lastHit = now;
            d.hit += 1;
        } else {
            d.miss += 1;
            d.failMs.push(Math.round(now - t0));
        }
    };
    const shell = window.PearnlyScanCamera || (window.PearnlyScanCamera = {});
    let realCreate = null;
    Object.defineProperty(shell, 'create', {
        configurable: true,
        get() {
            if (!realCreate) return undefined;
            return (opts) => realCreate.call(shell, Object.assign({}, opts, cfg.patch || {}));
        },
        set(fn) {
            realCreate = fn;
        },
    });

    if (cfg.native) {
        const FORMATS = ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'code_39', 'itf'];
        function Stub() {}
        Stub.getSupportedFormats = () => Promise.resolve(FORMATS.slice());
        // 「这一帧是不是清晰的条码」:清晰条纹里有纯黑像素;素材里的糊帧是 25px 盒式模糊,
        // EAN-13 最长的黑条才 4 个码元(≈20px),平均下来最黑也只到 ≈51;白墙全是 255。
        // 阈值取 20,两类之间隔着三十个灰阶 —— 不是拍脑袋取的中点。
        Stub.prototype.detect = function (canvas) {
            const t0 = performance.now();
            const ctx = canvas.getContext('2d', { willReadFrequently: true });
            const px = ctx.getImageData(0, canvas.height >> 1, canvas.width, 1).data;
            let dark = 0;
            for (let i = 0; i < px.length; i += 4) if (px[i] < 20) dark += 1;
            const hit = dark >= 8;
            mark(t0, hit);
            return Promise.resolve(hit ? [{ rawValue: cfg.code, format: 'ean_13' }] : []);
        };
        window.BarcodeDetector = Stub;
        return;
    }

    let realZX = null;
    Object.defineProperty(window, 'PearnlyScanZXing', {
        configurable: true,
        get() {
            if (!realZX) return undefined;
            return {
                FORMAT_NAMES: realZX.FORMAT_NAMES,
                build(ZX) {
                    const Ctor = realZX.build(ZX);
                    const inner = Ctor.prototype.detect;
                    // 慢机器那一档:真解完再压 extraMs,记账记在延时【之后】—— 引擎等的是整段,
                    // 报告里那个数要跟引擎等的是同一段,不然量的是别的东西。
                    Ctor.prototype.detect = function (canvas) {
                        const t0 = performance.now();
                        return inner
                            .call(this, canvas)
                            .then((hits) =>
                                cfg.extraMs
                                    ? new Promise((r) => setTimeout(() => r(hits), cfg.extraMs))
                                    : hits
                            )
                            .then((hits) => {
                                mark(t0, hits.length > 0);
                                return hits;
                            });
                    };
                    return Ctor;
                },
            };
        },
        set(v) {
            realZX = v;
        },
    });
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

async function openScanner(page, origin, tier, asked, clock) {
    await page.addInitScript(seed);
    await page.addInitScript(installTier, Object.assign({ code: BOX }, tier));
    await page.route('**/api/pos/products/by-barcode*', async (route) => {
        asked.push(Date.now() - clock.t0);
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
    // 计时从第一次真解出来那一刻起(相机预热 + ZXing 下载不算进观察窗口)
    await page.waitForFunction(
        () => (document.getElementById('bscan-last').textContent || '').length > 0,
        null,
        { timeout: 45000 }
    );
}

// 屏上真看得见与否只认真 DOM。解码节拍一起读回来:一次失败采样多久,是地板的刻度本身。
const readScreen = () => {
    const box = document.getElementById('bscan-fails');
    const row = box.querySelector('.bscan-fail');
    const r = box.getBoundingClientRect();
    const cs = getComputedStyle(box);
    const d = window.__dec;
    const fail = d.failMs.slice().sort((a, b) => a - b);
    const cycle = d.cycleMs.slice().sort((a, b) => a - b);
    return {
        count: document.getElementById('bscan-count').textContent,
        qtys: [...document.querySelectorAll('#cart-lines .q[data-qi]')].map((e) => e.textContent),
        noticeText: row ? row.textContent : '',
        noticeOnScreen:
            !!row &&
            cs.display !== 'none' &&
            cs.visibility !== 'hidden' &&
            Number(cs.opacity) > 0.9 &&
            r.width > 100 &&
            r.height > 40 &&
            r.top < window.innerHeight &&
            r.bottom > 0,
        // 采样成功率不能跨档比:解不出来时引擎按 probeIntervalMs(15ms)紧着补采样,解出来
        // 之后按 intervalMs(120ms)歇着 —— 档越快,糊帧就被采得越密,同一份素材的这个数就越低。
        // 它在这里只用来确认「这一跑真在解真素材」,不是解码器准不准的对照。
        sampleHitRate: d.hit + d.miss ? Math.round((d.hit / (d.hit + d.miss)) * 100) : null,
        maxGapMs: d.maxGapMs,
        failCycleMs: cycle.length ? cycle[cycle.length >> 1] : null,
        failDecodeMs: fail.length ? fail[fail.length >> 1] : null,
        samples: d.hit + d.miss,
    };
};

async function withCamera(y4m, fn) {
    const browser = await chromium.launch({
        args: [
            '--use-fake-ui-for-media-stream',
            '--use-fake-device-for-media-stream',
            `--use-file-for-fake-video-capture=${y4m}`,
        ],
    });
    try {
        return await fn(browser);
    } finally {
        await browser.close();
    }
}

// 一次跑动 = 开一个真浏览器、真假摄像头、真 POS 页面,盯 watchMs,读屏。
async function run(origin, tier, y4m, watchMs, label) {
    return withCamera(y4m, async (browser) => {
        const page = await browser.newPage({ viewport: PHONE });
        const asked = [];
        const clock = { t0: 0 };
        await openScanner(page, origin, tier, asked, clock);
        clock.t0 = Date.now();
        asked.length = 0;
        await page.waitForTimeout(watchMs);
        const state = await page.evaluate(readScreen);
        await shot(page, `${label}.png`);
        await page.close();
        return { lookups: asked.length, ...state };
    });
}

async function floorByTier(origin, tier) {
    const away = {};
    const legs = [...tier.probeLegs, ...tier.legs];
    for (const legMs of legs) {
        // 至少两个完整周期:一个周期只能证明「回来过一次」,两个才排得掉相位撞巧。
        const watchMs = Math.min(24000, Math.max(9000, legMs * 4.4));
        const cycles = Math.floor(watchMs / (legMs * 2));
        const r = await run(
            origin,
            tier,
            blinkFixture(legMs),
            watchMs,
            `r5f-${tier.name}-away${legMs}`
        );
        away[legMs] = { legMs, cyclesInWindow: cycles, ...r };
        console.log(
            `  空档${legMs}ms · 窗口 ${watchMs}ms(${cycles} 个来回)· 真再记 ${r.lookups} 件 · ` +
                `屏上提示看得见=${r.noticeOnScreen} · 车 ${JSON.stringify(r.qtys)} · ` +
                `失败采样周期中位 ${r.failCycleMs}ms`
        );
    }
    const rearmed = legs.filter((ms) => away[ms].lookups >= 1);
    const floorMs = rearmed.length ? Math.min(...rearmed) : null;
    const below = legs.filter((ms) => !floorMs || ms < floorMs);
    // 地板以下那几档:不许再记(那是判据的本意)+ 不许一声不吭(那是它的代价)。
    // 一声不吭的那几档单独拎出来 —— 静默区不是零,它只被压到人手够不到的那一段以下。
    const silent = below.filter((ms) => !away[ms].noticeOnScreen);
    const silentBelowMs = silent.length ? Math.max(...silent) : 0;
    const belowOk = below.every((ms) => away[ms].lookups === 0);
    const hold = await run(
        origin,
        tier,
        path.resolve('.p50.y4m'),
        HOLD_MS,
        `r5f-${tier.name}-hold`
    );
    console.log(
        `  举着不动(p=0.5)· 第一件之后又查码 ${hold.lookups} 次 · 车 ${JSON.stringify(hold.qtys)} · ` +
            `${hold.count} · 最长糊了 ${hold.maxGapMs}ms · 采样成功率 ${hold.sampleHitRate}% · ` +
            `失败采样周期中位 ${hold.failCycleMs}ms`
    );
    return {
        floorMs,
        floorBracket: `(${Math.max(...below, 0)}, ${floorMs}]`,
        silentBelowMs,
        away,
        hold,
        // 三条一起才算这一档过:
        //  · 地板存在(6000ms 那一腿兜底)、地板以下不多记(判据的本意)
        //  · 还静默着的那一段必须留在 SWAP_FLOOR_MS 以下 —— 人把 A 拿开再举 B 够不到那么快,
        //    够得到的那一段必须出声(这一侧四轮一个数都没量过,正是它翻车的地方)
        //  · 举着不动仍然只有一件:第一件落地之后不许再查码,车里也只许有一件
        ok:
            belowOk &&
            !!floorMs &&
            silentBelowMs <= SWAP_FLOOR_MS &&
            hold.lookups === 0 &&
            hold.qtys.join(',') === '1',
    };
}

// 「地板压到 1.2 秒 / 给采样尺封顶」这个提议,拿真素材跑正向那一侧。每一行都带预期:
// 对照组(不改门槛的那两跑)必须仍是一件,不然多记就赖不到门槛头上。
const LOW = [
    {
        label: 'low-native-glare1200',
        tier: { name: 'native', native: true, patch: { clearAfterMs: 1200, clearAfterMisses: 8 } },
        y4m: '.g1200.y4m',
        expect: 'double',
        why: '把地板压到 1.2s:一次 1.2 秒的反光在快机器上直接被判成「货走了」',
    },
    {
        label: 'low-native-glare1200-control',
        tier: { name: 'native', native: true },
        y4m: '.g1200.y4m',
        expect: 'single',
        why: '对照:同机器同素材,门槛不动',
    },
    // 封顶那两跑用【定长】的糊(2.8 秒一段),不用 p=0.5 的散帧:老机器一次采样 415ms,
    // 6 次连着没解出来要 2.5 秒,散帧素材上凑齐这一串是 0.5^6 ≈ 1.6% 的事 —— 七秒窗口里
    // 多半撞不上,于是「没多记」量的是这一跑运气好,不是封顶安全(第一版就这么假绿过)。
    {
        label: 'low-slow-cap2500',
        tier: { name: 'slow', extraMs: EXTRA_MS, patch: { clearAfterMisses: 6 } },
        y4m: '.g2800.y4m',
        expect: 'double',
        why: '给采样尺封顶 ≈2.5s:老机器上一次 2.8 秒的反光就把一次持握记成两件',
    },
    {
        label: 'low-slow-cap2500-control',
        tier: { name: 'slow', extraMs: EXTRA_MS },
        y4m: '.g2800.y4m',
        expect: 'single',
        why: '对照:同机器同素材,采样尺不封顶',
    },
];

async function lowfloor(origin) {
    const report = {};
    for (const c of LOW) {
        const r = await run(origin, c.tier, path.resolve(c.y4m), HOLD_MS, `r5f-${c.label}`);
        // lookups 从第一件落地那一刻起数 —— 举着不动的整段里再查一次码就是多记了一件。
        const doubled = r.lookups >= 1 || r.qtys.some((q) => Number(q) > 1);
        const ok = doubled === (c.expect === 'double');
        report[c.label] = { expect: c.expect, why: c.why, doubled, ok, ...r };
        console.log(
            `${ok ? 'PASS' : 'FAIL'} ${c.label} 预期${c.expect} · 第一件之后又查码 ${r.lookups} ` +
                `次 · 车 ${JSON.stringify(r.qtys)} · ${c.why}`
        );
    }
    return report;
}

(async () => {
    const need = LOWFLOOR
        ? [...new Set(LOW.map((c) => c.y4m))]
        : [
              ...new Set(TIERS.flatMap((t) => [...t.probeLegs, ...t.legs].map(blinkFixture))),
              path.resolve('.p50.y4m'),
          ];
    for (const f of need) {
        if (!fs.existsSync(path.resolve(f))) {
            console.error(`缺素材 ${f} —— 见本文件头部的跑法`);
            process.exit(2);
        }
    }
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    let report;
    let bad;
    if (LOWFLOOR) {
        report = await lowfloor(origin);
        bad = Object.values(report).filter((r) => !r.ok).length;
    } else {
        report = {};
        for (const tier of TIERS) {
            console.log(`── ${tier.name} ──`);
            report[tier.name] = await floorByTier(origin, tier);
            const t = report[tier.name];
            console.log(
                `${t.ok ? 'PASS' : 'FAIL'} ${tier.name} 地板 ${t.floorBracket}ms · ` +
                    `还静默着的最大空档 ${t.silentBelowMs}ms(上限 ${SWAP_FLOOR_MS}ms)`
            );
        }
        bad = Object.values(report).filter((r) => !r.ok).length;
    }
    const name = LOWFLOOR ? 'report-r5-lowfloor.json' : 'report-r5-floor-by-speed.json';
    fs.writeFileSync(path.join(SHOTS, name), JSON.stringify(report, null, 2));
    server.close();
    console.log(bad ? `FAIL · ${bad} 档没过` : `PASS · 报告 ${name}`);
    process.exit(bad ? 1 : 0);
})().catch((e) => {
    console.error('R5 FLOOR BY SPEED CRASH', e);
    process.exit(2);
});
