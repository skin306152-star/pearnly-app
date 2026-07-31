/*
 * scripts/_r5_cam_dupnotice_verify.cjs · 第五轮:去重那把尺子【两侧】一起量
 *
 * 第四轮把「举着不动别记成两件」修好了,代价这一侧一个数都没量过 —— 而代价是真的:两把尺子
 * AND 起来必然有个地板(本脚本实测:真 Chromium + 本仓 dist/zxing.js 上落在 1400~1600ms 之间),
 * 地板以下拿走 A 再举同款的 B,屏上跟成功扫码一模一样,顾客拿两件付一件的钱。地板降不下来
 * (1.2 秒的空档跟 1.2 秒的反光在解码结果上是同一串「连着 N 次没解出」),所以改成:压下去的
 * 那次要出声(引擎 onDuplicate → 失败清单里一行条件句 + 一颗「+1」)。
 *
 * 本脚本两个方向各跑一遍,每一档的实测数都进报告:
 *   反向(别再压第二件)  空档 800~2000ms 逐档:要么真再记一件,要么屏上真有一行看得见的提示。
 *                        再验那颗「+1」不是装饰:点下去购物车数量真的从 1 变 2。
 *   反向(别把提示弄没)  长短空档交替(1.2s 被挡下 / 2.0s 真记一件,同一个码 —— 连着扫三瓶
 *                        一样的可乐本来就是这个样子):全程没人碰屏,那行提示就不许自己消失。
 *   正向(别退回老病)    p=0.5 散帧素材举着不动跑 6 遍必须都是 1 件;反光 600/800/1200ms 同样。
 *
 * 本机实测(14 秒观察窗口 · 数字全在 report-r5-dupnotice.json 里):
 *   空档 800/1000/1200/1400ms → 自然重记 0 次,提示 8/6/5/4 次,「+1」把车从 1 点到 2;
 *   空档 1600/1800/2000ms     → 自然重记 4/3/3 次(= 窗口内的周期数),一次提示都不出;
 *   举着不动 9 遍             → 查码 1 次、车 1 件、件数 1,钱一分没动(误报只多一行字);
 *   长短交替                  → 修之前:那行被后面真记上的那一件顺手销掉 2 次(车 3 件而柜台
 *                              上是 6 件,屏上还剩一行);修之后:0 次(见 pos-scan.js
 *                              的 resolveFail —— dup 行只有店员销得掉)。
 *
 * 真的东西:Chromium 假摄像头喂真合成 EAN-13(桌面 Chromium 没有原生 BarcodeDetector,走本仓
 * dist/zxing.js 真解码);pos.html + dist/pos.js 是真产物。桩只有 by-barcode 回包。
 * 提示条数用 addInitScript 在 create() 外面挂一层计数(不改门槛、不改行为),屏上看得见与否
 * 仍由真 DOM 判 —— 计数只是给报告用的刻度。
 *
 * 跑法(仓库根目录):
 *   for s in 0.8 1.0 1.2 1.4 1.6 1.8 2.0; do
 *     python scripts/_scan_ean_blink_y4m.py .blink${s/./}.y4m 8850999320014 $s; done
 *   python scripts/_scan_ean_pjitter_y4m.py .p50.y4m 0.5 3
 *   python scripts/_scan_ean_jitter_y4m.py .g600.y4m 8850999320014 19 9
 *   python scripts/_scan_ean_jitter_y4m.py .g800.y4m 8850999320014 19 12
 *   python scripts/_scan_ean_jitter_y4m.py .g1200.y4m 8850999320014 19 18
 *   python scripts/_scan_ean_blink_y4m.py .blinkmix.y4m 8850999320014 1.2 2.0
 *   node scripts/_r5_cam_dupnotice_verify.cjs
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('@playwright/test');
const { ROOT, PHONE, serve, shotter } = require('./_gun_wedge_lib.cjs');

const SHOTS = path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/fix5');
const shot = shotter(SHOTS);
const BOX = '8850999320014';
const WATCH_MS = 14000;

// R5_MUTE_PROOF=1:把告警门槛推到够不着,只跑地板以下那两档 —— 这几条判据必须跟着变红。
// 全绿说明它们量的不是这条提示,那这份报告就一文不值(闸报绿 ≠ 闸看过)。
const MUTE_PROOF = process.env.R5_MUTE_PROOF === '1';
// R5_ONLY=mixed(逗号分隔 away/hold/mixed):整套十几分钟,改完一处不该为了看那一处重跑全套。
// 只影响跑哪几段,不影响任何判据 —— 出结论前仍要跑全套。
const ONLY = (process.env.R5_ONLY || '').split(',').filter(Boolean);
const runs = (name) => !ONLY.length || ONLY.indexOf(name) >= 0;

// 反向:每一档都是「举着 leg 毫秒 → 拿走 leg 毫秒 → 再举回来」,Chromium 循环播。
const AWAY = (MUTE_PROOF ? [800, 1200] : [800, 1000, 1200, 1400, 1600, 1800, 2000]).map((ms) => ({
    label: `away${String(ms).padStart(4, '0')}`,
    y4m: path.resolve(`.blink${String(ms / 100).padStart(2, '0')}.y4m`),
    legMs: ms,
}));

// 正向:货全程没离开过。p50 跑 6 遍(散帧素材每跑一遍相位都不同,一遍绿说明不了什么),
// 三档反光是成段的糊,长度写死在素材里。
const HOLD = MUTE_PROOF
    ? []
    : [
          ...Array.from({ length: 6 }, (_, i) => ({
              label: `hold-p50-${i + 1}`,
              y4m: path.resolve('.p50.y4m'),
          })),
          { label: 'glare600', y4m: path.resolve('.g600.y4m') },
          { label: 'glare800', y4m: path.resolve('.g800.y4m') },
          { label: 'glare1200', y4m: path.resolve('.g1200.y4m') },
      ];

const seed = () => {
    localStorage.setItem('pos_store_token', 'r5-dupnotice');
    localStorage.setItem('pos_store_name', 'ร้าน DUP');
    localStorage.setItem('mrpilot_lang', 'th');
};

// 在 create() 外面套一层只做计数的壳:门槛/回调一个字不改,屏上的行为跟店里完全一样。
// 挂法必须是【确定性】的:上一版用 setInterval 轮询等 create 出现,而 scan.js 一落地
// pos-scan.js 就同步 create(),20ms 的轮询稳稳输掉这场比赛 —— 计数器于是全程读 0,
// 报告里「提示 0 次 · 屏上看得见 true」自相矛盾,量的是钩子没挂上而不是产品行为。
// scan-loader.js 是 `root.PearnlyScanCamera = root.PearnlyScanCamera || {}`,所以先把壳
// 摆好、在 create 这个键上放一对存取器:谁来赋值都得从这儿过。
const teeDuplicates = (mute) => {
    window.__dupFires = [];
    const shell = window.PearnlyScanCamera || (window.PearnlyScanCamera = {});
    let real = null;
    Object.defineProperty(shell, 'create', {
        configurable: true,
        get() {
            if (!real) return undefined;
            return function (opts) {
                const user = opts && opts.onDuplicate;
                const patch = {
                    onDuplicate: function (code, info) {
                        window.__dupFires.push({
                            code: code,
                            at: Date.now(),
                            gapMs: info.gapMs,
                            misses: info.misses,
                        });
                        if (user) user(code, info);
                    },
                };
                // 反证开关(见 MUTE_PROOF):把告警门槛推到够不着,别的一个字不改。
                // 判据要是这么干还全绿,那几条绿就不是这条提示给的 —— 前几轮全死在这上面。
                if (mute) patch.dupNoticeMs = 10 ** 7;
                return real.call(shell, Object.assign({}, opts, patch));
            };
        },
        set(fn) {
            real = fn;
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

async function openScanner(page, origin, asked, clock) {
    await page.addInitScript(seed);
    await page.addInitScript(teeDuplicates, MUTE_PROOF);
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

// 屏上真看得见与否只认真 DOM:清单在流里(不是 fixed),看得见 = 有盒子 + 不透明 + 在视口内
// 【而且那块像素上站着的就是它】。grep 类名 / 断 classList 有 show 都不算 —— 那种绿骗过前几轮。
// 最后那一条是这一轮补的:清单挂在收银主屏上,而取景层是一张 z-index 46 的整屏遮罩,几何上
// 「在视口内」跟「店员看得见」根本是两件事。判据只量几何 = 上一轮那种「闸绿而截图上没有」。
const readScreen = () => {
    const box = document.getElementById('bscan-fails');
    const row = box.querySelector('.bscan-fail');
    const act = box.querySelector('.bscan-fail-act');
    const r = box.getBoundingClientRect();
    const cs = getComputedStyle(box);
    const inView =
        r.width > 100 &&
        r.height > 40 &&
        r.top < window.innerHeight &&
        r.bottom > 0 &&
        r.left < window.innerWidth &&
        r.right > 0;
    // 取那一行自己的中心点(夹回视口内),问问那个点上最上面站的是谁。
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
        actLabel: act ? act.textContent : '',
        coveredBy: onTop ? '' : (top && (top.id || top.className || top.tagName)) || 'nothing',
        visible:
            !!row &&
            cs.display !== 'none' &&
            cs.visibility !== 'hidden' &&
            Number(cs.opacity) > 0.9 &&
            inView &&
            onTop,
        fires: window.__dupFires.length,
        worstGapMs: Math.max(0, ...window.__dupFires.map((f) => f.gapMs)),
    };
};

async function runAway(browser, origin, item) {
    const page = await browser.newPage({ viewport: PHONE });
    const asked = [];
    const clock = { t0: 0 };
    await openScanner(page, origin, asked, clock);
    clock.t0 = Date.now();
    asked.length = 0;
    await page.evaluate(() => {
        window.__dupFires.length = 0;
    });
    await page.waitForTimeout(WATCH_MS);
    const state = await page.evaluate(readScreen);
    await shot(page, `r5-${item.label}.png`);
    // 观察窗口里【自然】发生的重记有几次,必须在点「+1」之前定格:asked 是同一个数组,
    // 点完再读会把人手点出来的那一次算成产品自己认出来的(上一版 leg0800 的 rescans=1
    // 全是那一下点出来的,真值是 0)。
    const rescans = asked.length;
    // 提示不是装饰:那颗「+1」点下去,购物车真的多一件。
    let plusOne = null;
    if (state.visible) {
        const before = state.qtys.join(',');
        await page.click('#bscan-fails .bscan-fail-act');
        await page.waitForTimeout(1200);
        const after = await page.evaluate(readScreen);
        // rowGone 只记录不当判据:素材是循环播的,点掉之后画面又走了一个来回,
        // 下一次压制照样把这一行重新挂上来 —— 那正是它该干的事。
        plusOne = {
            before: before,
            after: after.qtys.join(','),
            lookups: asked.length - rescans,
            rowGone: !after.visible,
        };
        await shot(page, `r5-${item.label}-plusone.png`);
    }
    await page.close();
    const cycles = Math.floor(WATCH_MS / (item.legMs * 2));
    return {
        legMs: item.legMs,
        cyclesInWindow: cycles,
        rescans: rescans,
        noticeFires: state.fires,
        worstGapMs: state.worstGapMs,
        noticeOnScreen: state.visible,
        noticeText: state.noticeText,
        plusOne: plusOne,
        state: state,
        // 判据:这一档【没有一次是静默的】。真再记一件算数(地板以上),屏上真有一行、
        // 而且那颗「+1」真把货补进车也算数(地板以下)。两样都没有 = 顾客那件货白拿走。
        ok:
            (rescans >= cycles && !state.visible) ||
            (state.visible &&
                state.fires > 0 &&
                !!plusOne &&
                plusOne.after !== plusOne.before &&
                plusOne.lookups >= 1),
    };
}

async function runHold(browser, origin, item) {
    const page = await browser.newPage({ viewport: PHONE });
    const asked = [];
    const clock = { t0: Date.now() };
    await openScanner(page, origin, asked, clock);
    await page.waitForTimeout(7000);
    const state = await page.evaluate(readScreen);
    await shot(page, `r5-${item.label}.png`);
    await page.close();
    return {
        lookups: asked.length,
        qtys: state.qtys.join(','),
        count: state.count,
        noticeFires: state.fires,
        worstGapMs: state.worstGapMs,
        noticeOnScreen: state.visible,
        // 举着不动 = 一件。真发出去的查询、屏上件数、购物车数量三处都得是 1 ——
        // 提示喊不喊是另一回事(它只是一行条件句),但钱这一侧一动都不许动。
        ok: asked.length === 1 && state.qtys.join(',') === '1' && /(^|\D)1(\D|$)/.test(state.count),
    };
}

// 长短空档交替的素材(1.2s 挡下 / 2.0s 真记一件,同一个码):店里连着扫三瓶一样的可乐,
// 手速本来就有快有慢,这两种结局本来就会交替出现。
// 判的是【那行提示会不会自己没掉】—— 这一跑全程没人点任何按钮,所以行只可能被产品自己抹掉。
// 抹掉一次 = 一件没进车的货连最后一条线索也没了,屏上跟全都扫上了一模一样。
// 只看窗口末尾那一眼没用:素材是循环播的,末尾正好停在哪一段是随机的,那种绿是掷骰子掷来的。
async function runMixed(browser, origin, y4m) {
    const page = await browser.newPage({ viewport: PHONE });
    const asked = [];
    const clock = { t0: 0 };
    await openScanner(page, origin, asked, clock);
    await page.evaluate(() => {
        window.__rowLog = [];
        window.__rowTimer = setInterval(() => {
            const box = document.getElementById('bscan-fails');
            const q = document.querySelector('#cart-lines .q[data-qi]');
            window.__rowLog.push({
                row: !!box.querySelector('.bscan-fail'),
                q: q ? q.textContent : '',
            });
        }, 100);
    });
    clock.t0 = Date.now();
    asked.length = 0;
    await page.evaluate(() => {
        window.__dupFires.length = 0;
    });
    await page.waitForTimeout(WATCH_MS);
    const seen = await page.evaluate(() => {
        clearInterval(window.__rowTimer);
        const log = window.__rowLog;
        let appeared = 0;
        let vanished = 0;
        for (let i = 1; i < log.length; i++) {
            if (log[i].row && !log[i - 1].row) appeared += 1;
            if (!log[i].row && log[i - 1].row) vanished += 1;
        }
        return { appeared, vanished, samples: log.length, fires: window.__dupFires.length };
    });
    const state = await page.evaluate(readScreen);
    await shot(page, 'r5-mixed-1200-2000.png');
    await page.close();
    return {
        y4m: path.basename(y4m),
        rearms: asked.length,
        noticeFires: seen.fires,
        appeared: seen.appeared,
        vanished: seen.vanished,
        pollSamples: seen.samples,
        qtys: state.qtys.join(','),
        noticeOnScreen: state.visible,
        // 三条都要:真发生过「被挡下」(fires)、那行真上过屏(appeared)、期间真也记上过货
        // (rearms —— 没有它就没走到「后面那一件把前面那行销掉」的路上,这一绿不算数),
        // 然后才轮到判据本身:没人动手,行就不许消失。
        ok: seen.fires > 0 && seen.appeared > 0 && asked.length > 0 && seen.vanished === 0,
    };
}

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

// 长短空档交替那一份素材(挡下与真记一件在同一跑里各来一遍)。MUTE_PROOF 下也跑:
// 关掉告警之后这一档必须跟着变红,不然它量的就不是这条提示。
const MIXED = path.resolve('.blinkmix.y4m');

(async () => {
    for (const it of [...AWAY, ...HOLD, { y4m: MIXED }]) {
        if (!fs.existsSync(it.y4m)) {
            console.error(`缺素材 ${it.y4m} —— 见本文件头部的跑法`);
            process.exit(2);
        }
    }
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const report = { away: {}, hold: {}, mixed: {} };

    for (const item of runs('away') ? AWAY : []) {
        let row;
        try {
            row = await withCamera(item.y4m, (b) => runAway(b, origin, item));
        } catch (e) {
            row = { ok: false, crash: String((e && e.message) || e).split('\n')[0] };
        }
        report.away[item.label] = row;
        console.log(
            `${row.ok ? 'PASS' : 'FAIL'} ${item.label} 空档${item.legMs}ms · 窗口内该再收 ` +
                `${row.cyclesInWindow} 件 · 真再记 ${row.rescans} · 提示 ${row.noticeFires} 次` +
                `(最长空档 ${row.worstGapMs}ms)· 屏上看得见=${row.noticeOnScreen} · ` +
                `+1 ${JSON.stringify(row.plusOne)}`
        );
    }

    for (const item of runs('hold') ? HOLD : []) {
        let row;
        try {
            row = await withCamera(item.y4m, (b) => runHold(b, origin, item));
        } catch (e) {
            row = { ok: false, crash: String((e && e.message) || e).split('\n')[0] };
        }
        report.hold[item.label] = row;
        console.log(
            `${row.ok ? 'PASS' : 'FAIL'} ${item.label} 查码 ${row.lookups} 次 · 车 ${row.qtys} · ` +
                `${row.count} · 提示 ${row.noticeFires} 次(最长空档 ${row.worstGapMs}ms)`
        );
    }

    // 跳过的那一段不许留下任何一行 PASS:没跑过的东西印成绿的,比不印危险得多。
    if (runs('mixed')) {
        let mixed;
        try {
            mixed = await withCamera(MIXED, (b) => runMixed(b, origin, MIXED));
        } catch (e) {
            mixed = { ok: false, crash: String((e && e.message) || e).split('\n')[0] };
        }
        report.mixed['mix1200-2000'] = mixed;
        console.log(
            `${mixed.ok ? 'PASS' : 'FAIL'} mix1200-2000 长短空档交替 · 真记 ${mixed.rearms} 件 · ` +
                `提示 ${mixed.noticeFires} 次 · 那行上屏 ${mixed.appeared} 次 · ` +
                `没人动它却消失 ${mixed.vanished} 次(必须 0)· 车 ${mixed.qtys}`
        );
    }

    // 只跑了一段就换个名字落盘:半份报告顶着正式名字躺在那里,下一个人会当成跑全了。
    const name = MUTE_PROOF
        ? 'report-r5-muteproof.json'
        : ONLY.length
          ? 'report-r5-dupnotice-partial.json'
          : 'report-r5-dupnotice.json';
    fs.writeFileSync(path.join(SHOTS, name), JSON.stringify(report, null, 2));
    server.close();
    const rows = [
        ...Object.values(report.away),
        ...Object.values(report.hold),
        ...Object.values(report.mixed),
    ];
    // 反证跑法下判据反过来:每一档都必须红。有一档还绿 = 那条绿不是这条提示给的。
    if (MUTE_PROOF) {
        const stillGreen = rows.filter((r) => r.ok).length;
        console.log(`MUTE_PROOF · 关掉告警后仍判绿的档数 ${stillGreen}(必须是 0)`);
        process.exit(stillGreen === 0 ? 0 : 1);
    }
    process.exit(rows.every((r) => r.ok) ? 0 : 1);
})().catch((e) => {
    console.error('R5 DUP NOTICE CRASH', e);
    process.exit(2);
});
