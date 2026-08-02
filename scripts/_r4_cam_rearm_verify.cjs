/*
 * scripts/_r4_cam_rearm_verify.cjs · 去重那把尺子的地板:量在哪儿 + 两侧各该发生什么
 *
 * 三轮到四轮打的全是「举着不动别记成两件」。判据因此被调紧成两把尺子 AND(墙钟 clearAfterMs
 * 且连着 clearAfterMisses 次采样没解出),而两把尺子 AND 起来必然有个地板:同一个码真的离开
 * 画面之后,得等这么久才重新算得上一件。
 *
 * 于是「连着扫两瓶一模一样的可乐」这个收银台最日常的动作分成两侧,产品的设计是:
 *   地板以上   引擎自己认出第二件 —— 直接进车,店员什么都不用做
 *   地板以下   不自动重记(1.2 秒的空档跟 1.2 秒的反光在解码结果上是同一串「连着 N 次没解出」,
 *              分不开),但失败清单里挂一行条件句 + 一颗「+1」,店员点一下就补上
 *
 * 本脚本三条判据,全部按【这一跑现场量出来的地板】分侧,不写死毫秒数 —— 地板不是常数,它是
 * 「一次解不出的采样有多久 × clearAfterMisses」的函数,机器忙起来解码变慢地板就往上爬
 * (实测同一份 dist/zxing.js:空机器 1.4~1.6s、连跑四十分钟后爬到 ≈2.9s)。写死档位的判据在
 * 慢机器上红的是机器状态不是产品,而那种红会把人训练成无视红 —— 上一版就是这么恒红的。
 *
 *   ① 地板存在      这一梯子里至少有一档真自然重记。一档都没有 = 同一个码永远记不上第二件
 *   ② 单调          地板【以上】每一档都必须自然重记(窗口里有几个来回就该记几件)。
 *                   leg1600 认得出而 leg2000 认不出 = 尺子本身坏了,这条抓的正是那种坏法
 *   ③ 不许静默      地板【以下】每一档:那行提示必须真在屏上(真 DOM + elementFromPoint),
 *                   而且那颗「+1」点下去真发查码请求、购物车数量真的动 —— 顾客那件货才没白拿走
 *
 * 与 scripts/_r5_cam_dupnotice_verify.cjs 的分工:那份逐档量【代价】(提示出现率、静默区宽度、
 * 举着不动那一侧的误报),本份量【地板本身】并顺着梯子验单调。地板漂了先看这一份。
 *
 * 跑法(仓库根目录):
 *   python scripts/_scan_ean_blink_y4m.py .blink20.y4m 8850999320014 2.0
 *   python scripts/_scan_ean_blink_y4m.py .blink18.y4m 8850999320014 1.8
 *   python scripts/_scan_ean_blink_y4m.py .blink16.y4m 8850999320014 1.6
 *   python scripts/_scan_ean_blink_y4m.py .blink12.y4m 8850999320014 1.2
 *   python scripts/_scan_ean_blink_y4m.py .blink08.y4m 8850999320014 0.8
 *   node scripts/_r4_cam_rearm_verify.cjs
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('@playwright/test');
const { ROOT, PHONE, serve, shotter } = require('./_gun_wedge_lib.cjs');

const SHOTS = path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/fix3');
const shot = shotter(SHOTS);
const BOX = '8850999320014';
const WATCH_MS = 14000; // 至少三个完整周期(leg=2.0s 时一周期 4s)

// 梯子从长到短:地板 = 这一列里最短的那个「还能自然重记」的空档。
const FIXTURES = [
    ['leg2000', path.resolve('.blink20.y4m'), 2000],
    ['leg1800', path.resolve('.blink18.y4m'), 1800],
    ['leg1600', path.resolve('.blink16.y4m'), 1600],
    ['leg1200', path.resolve('.blink12.y4m'), 1200],
    ['leg0800', path.resolve('.blink08.y4m'), 800],
];

const seed = () => {
    localStorage.setItem('pos_store_token', 'r4-rearm');
    localStorage.setItem('pos_store_name', 'ร้าน REARM');
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

// 「屏上看得见」只认真 DOM:有盒子 + 不透明 + 在视口内 + 那块像素上站着的就是它。
// 断 classList 有没有 show 的那种绿骗过前几轮 —— 清单挂在收银主屏上,而取景层是一张
// z-index 46 的整屏遮罩,几何上「在视口内」跟「店员看得见」是两件事。
const readScreen = () => {
    const box = document.getElementById('bscan-fails');
    const row = box.querySelector('.bscan-fail');
    const r = box.getBoundingClientRect();
    const cs = getComputedStyle(box);
    const rr = row ? row.getBoundingClientRect() : null;
    const cx = rr ? Math.min(window.innerWidth - 1, Math.max(1, rr.left + rr.width / 2)) : 0;
    const cy = rr ? Math.min(window.innerHeight - 1, Math.max(1, rr.top + rr.height / 2)) : 0;
    const top = rr ? document.elementFromPoint(cx, cy) : null;
    const onTop = !!top && (top === row || row.contains(top) || box.contains(top));
    return {
        count: document.getElementById('bscan-count').textContent,
        qtys: [...document.querySelectorAll('#cart-lines .q[data-qi]')].map((e) => e.textContent),
        grand: document.getElementById('cart-grand').textContent,
        noticeText: row ? row.textContent : '',
        coveredBy: onTop ? '' : (top && (top.id || top.className || top.tagName)) || 'nothing',
        noticeOnScreen:
            !!row &&
            cs.display !== 'none' &&
            cs.visibility !== 'hidden' &&
            Number(cs.opacity) > 0.9 &&
            r.width > 100 &&
            r.height > 40 &&
            r.top < window.innerHeight &&
            r.bottom > 0 &&
            onTop,
    };
};

async function run(browser, origin, label) {
    const page = await browser.newPage({ viewport: PHONE });
    await page.addInitScript(seed);
    const asked = [];
    let t0 = 0;
    await page.route('**/api/pos/products/by-barcode*', async (route) => {
        asked.push(Date.now() - t0);
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
    t0 = Date.now();
    asked.length = 0;
    await page.waitForTimeout(WATCH_MS);
    const state = await page.evaluate(readScreen);
    await shot(page, `r-${label}-rearm.png`);
    // 【自然】发生的重记必须在点「+1」之前定格:asked 是同一个数组,点完再读会把人手点出来的
    // 那一次算进产品自己认出来的份额里 —— 次数会把地板算低一档,而首次重记的时刻会变成
    // 「开窗后 14 秒才认出第二件」这种读上去像产品行为、其实是脚本自己那一下的数。
    const rescans = asked.length;
    const rearmMs = rescans ? asked[0] : null;
    let plusOne = null;
    if (state.noticeOnScreen) {
        const before = state.qtys.join(',');
        await page.click('#bscan-fails .bscan-fail-act');
        await page.waitForTimeout(1200);
        const after = await page.evaluate(readScreen);
        plusOne = {
            before,
            after: after.qtys.join(','),
            lookups: asked.length - rescans,
            added: after.qtys.join(',') !== before && asked.length - rescans >= 1,
        };
        await shot(page, `r-${label}-plusone.png`);
    }
    await page.close();
    return { state, asked, rescans, rearmMs, plusOne };
}

// 地板 = 梯子里最短的那个还能自然重记的空档。以上必须自然重记,以下必须出声 + 「+1」点得动。
function judge(report) {
    const rows = Object.values(report);
    const rearmed = rows.filter((r) => r.rescans >= 1).map((r) => r.legMs);
    const floorMs = rearmed.length ? Math.min(...rearmed) : null;
    for (const r of rows) {
        // 崩掉那一跑没有 state:当成「屏上什么都没有」判,别让判据自己抛异常把整份报告吞了
        const seen = r.state || {};
        r.side = floorMs && r.legMs >= floorMs ? 'above' : 'below';
        r.ok =
            r.side === 'above'
                ? r.rescans >= r.cyclesInWindow
                : !!seen.noticeOnScreen && !!r.plusOne && r.plusOne.added;
        r.why = r.ok
            ? ''
            : r.side === 'above'
              ? `地板(${floorMs}ms)以上却没自然重记满:窗口里 ${r.cyclesInWindow} 个来回只记了 ${r.rescans} 件`
              : `地板以下这一档是静默的:屏上提示=${!!seen.noticeOnScreen} · +1=${JSON.stringify(r.plusOne)}` +
                (seen.coveredBy ? ` · 那一行被 ${seen.coveredBy} 盖住` : '');
    }
    return {
        floorMs,
        floorBracket: `(${Math.max(0, ...rows.filter((r) => r.side === 'below').map((r) => r.legMs))}, ${floorMs}]`,
    };
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
    for (const [label, y4m, legMs] of FIXTURES) {
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
            row = { crash: String((e && e.message) || e).split('\n')[0], asked: [], rescans: 0 };
        }
        await browser.close();
        row.legMs = legMs;
        // 观察窗口里码消失又回来几次 —— 地板以上就该记这么多件。
        row.cyclesInWindow = Math.floor(WATCH_MS / (legMs * 2));
        report[label] = row;
        // 判绿判红要等整条梯子跑完(地板是从这一列里量出来的),但一档要一分半钟,中间一声
        // 不吭就没人知道它是在跑还是挂了。这一行只报实测数,不下结论。
        console.log(
            `  ${label} 空档${legMs}ms · 窗口内 ${row.cyclesInWindow} 个来回 · ` +
                `自然重记 ${row.rescans} 件 · 首次重记距开窗 ${row.rearmMs}ms · ` +
                `屏上提示=${(row.state || {}).noticeOnScreen}`
        );
    }
    const { floorMs, floorBracket } = judge(report);
    for (const [label, row] of Object.entries(report)) {
        console.log(
            `${row.ok ? 'PASS' : 'FAIL'} ${label} 空档${row.legMs}ms(地板${row.side === 'above' ? '以上' : '以下'})· ` +
                `窗口内 ${row.cyclesInWindow} 个来回 · 自然重记 ${row.rescans} 件 · ` +
                `首次重记距开窗 ${row.rearmMs}ms · 屏上提示=${(row.state || {}).noticeOnScreen} · ` +
                `+1 ${JSON.stringify(row.plusOne)}${row.why ? ' · ' + row.why : ''}`
        );
    }
    // 地板必须真存在:一档都不自然重记 = 同一个码永远记不上第二件,那时上面每一档都会被判成
    // 「地板以下」而只靠提示过关 —— 没有这一条,那种全线退化会安安静静地全绿。
    const hasFloor = !!floorMs;
    const bad = Object.values(report).filter((r) => !r.ok).length + (hasFloor ? 0 : 1);
    fs.writeFileSync(
        path.join(SHOTS, 'report-r4-cam-rearm.json'),
        JSON.stringify({ floorMs, floorBracket, legs: report }, null, 2)
    );
    server.close();
    console.log(
        hasFloor
            ? `地板 ${floorBracket}ms · ${bad ? `FAIL · ${bad} 档没过` : 'PASS'}`
            : 'FAIL · 整条梯子一档都没自然重记 —— 同一个码永远记不上第二件'
    );
    process.exit(bad ? 1 : 0);
})().catch((e) => {
    console.error('R4 CAM REARM CRASH', e);
    process.exit(2);
});
