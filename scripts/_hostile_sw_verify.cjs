/*
 * scripts/_hostile_sw_verify.cjs · 对抗素材验收(离线外壳 Service Worker · 真浏览器真 SW)
 *
 * 上一轮那条是在 node 里拿手写的 caches/fetch 桩跑 install/activate 的函数体。桩看不见两件
 * 真实存在的事:① CacheStorage 是【按源】的,不按 SW 作用域分家;② 装失败之后老 SW 还在不在、
 * 断网还开不开得了 /cashier,只有真浏览器答得出。所以这一份全程用真 SW:
 *   s1 deployWindow   已经有一版装好并在用 → 部署中 /cashier 回 502 → 新版必须装不上,
 *                     老缓存原样留着,断网仍能开 /cashier;恢复 200 后再更新才换代
 *   s2 twoScopes      老设备的 /pos 外壳先装好,再开 /cashier(产品里 pos.js 就是这么注册的)
 *                     —— 两个作用域「互不干扰」是不是真的
 *   s4 freshNavigation 联网重开 /cashier 必须拿到新外壳;断网才回落刚缓存的新外壳
 *
 * 真的东西:static/pos/cashier-sw.js 与 static/pos/pos-sw.js 是本仓真文件,由真
 * navigator.serviceWorker.register 装进真浏览器;缓存与断网都是浏览器自己的。上一版 SW 用
 * 同一份文件把 V 换成「当前版本减一」得到,当前版本现读真文件 —— 抄一份常量在这里,别人
 * bump 一次这份验收就为了两个数字对不上而红。
 * 桩只有承载页面(注册用的空壳)与 /cashier、/pos 两个 URL 的回包状态。
 *
 * 跑法(仓库根目录):node scripts/_hostile_sw_verify.cjs [用例名]
 */
const fs = require('fs');
const http = require('http');
const path = require('path');
const { chromium } = require('@playwright/test');
const { ROOT, shotter, runCases } = require('./_gun_wedge_lib.cjs');

const ONLY = process.argv[2] || '';
const SHOTS = path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/fix2');
const shot = shotter(SHOTS);

const CASHIER_SW = fs.readFileSync(path.join(ROOT, 'static/pos/cashier-sw.js'), 'utf8');
const POS_SW = fs.readFileSync(path.join(ROOT, 'static/pos/pos-sw.js'), 'utf8');
// 版本号现场从真文件里读,不抄一份常量:抄的那份跟着别人 bump 一次就过期,而过期的表现是
// 「素材换不成功」抛异常(2026-07-31 真栽过一次)—— 一个纯粹为了对齐两个数字而红的验收。
const V_RE = /const V = '(\d+)'/;
function versionOf(src) {
    const m = src.match(V_RE);
    if (!m) throw new Error('SW 里找不到 const V —— 文件结构变了,这份素材已经不成立');
    return m[1];
}
const NEW_V = versionOf(CASHIER_SW);
const OLD_V = String(Number(NEW_V) - 1); // 「它的上一版」只需要不是当前这个

function swAt(src, version) {
    return src.replace(V_RE, `const V = '${version}'`);
}

// 承载页:只做注册,不掺产品逻辑 —— 被验的是 SW 文件本身。
const SHELL = (marker) => `<!doctype html><meta charset="utf-8"><title>${marker}</title>
<body><h1 id="m">${marker}</h1></body>`;

const state = {
    cashierV: OLD_V,
    posV: NEW_V,
    shell: 200,
    posShell: 200,
    cashierMarker: 'CASHIER-SHELL',
};

function serve() {
    const server = http.createServer((req, res) => {
        const url = req.url.split('?')[0];
        const send = (code, type, body) => {
            res.writeHead(code, { 'content-type': type, 'cache-control': 'no-store' });
            res.end(body);
        };
        if (url === '/cashier-sw.js')
            return send(200, 'text/javascript', swAt(CASHIER_SW, state.cashierV));
        if (url === '/pos-sw.js') return send(200, 'text/javascript', swAt(POS_SW, state.posV));
        if (url === '/cashier') {
            if (state.shell !== 200) return send(state.shell, 'text/html', 'deploying');
            return send(200, 'text/html', SHELL(state.cashierMarker));
        }
        if (url === '/pos') {
            if (state.posShell !== 200) return send(state.posShell, 'text/html', 'deploying');
            return send(200, 'text/html', SHELL('POS-SHELL'));
        }
        const fp = path.join(ROOT, decodeURIComponent(url).replace(/^\/+/, ''));
        if (fp.startsWith(ROOT) && fs.existsSync(fp) && !fs.statSync(fp).isDirectory()) {
            res.writeHead(200, { 'content-type': 'text/javascript' });
            return fs.createReadStream(fp).pipe(res);
        }
        send(404, 'text/html', 'nope');
    });
    return new Promise((r) => server.listen(0, '127.0.0.1', () => r(server)));
}

const cacheKeys = (page) => page.evaluate(() => caches.keys());

// 断网导航失败要当结论带回去,不能把整例炸成 crash —— 「打不开」正是要断的那件事。
async function gotoText(page, url) {
    try {
        await page.goto(url);
        return await page.textContent('#m');
    } catch (_) {
        // goto 抛完页面是白的,截不到证据。改用页内跳转把浏览器【自己那张错误页】留在屏上 ——
        // 店员在店里看到的就是它,不是一句 ERR_FAILED。
        await page.evaluate((u) => (window.location.href = u), url).catch(() => {});
        await page.waitForTimeout(1500);
        const title = await page.title().catch(() => '');
        const body = await page
            .evaluate(() => document.body.innerText.slice(0, 120))
            .catch(() => '');
        return `NAV_FAILED · 浏览器错误页 [${title}] ${body.replace(/\s+/g, ' ').trim()}`;
    }
}

const hasShell = (page, key, url) =>
    page.evaluate(([k, u]) => caches.open(k).then((c) => c.match(u).then((m) => !!m)), [key, url]);

async function registerSw(page, script, scope) {
    return page.evaluate(
        ([s, sc]) =>
            navigator.serviceWorker
                .register(s, { scope: sc })
                .then((r) =>
                    navigator.serviceWorker.ready.then(() => ({ ok: true, scope: r.scope }))
                )
                .catch((e) => ({ ok: false, err: String(e) })),
        [script, scope]
    );
}

// 更新一版:register 同一个 URL 会走 update 流程。install 失败时 promise 仍可能 resolve,
// 所以结论一律看缓存与 controller,不看这一步的返回值。
async function updateSw(page) {
    await page.evaluate(() =>
        navigator.serviceWorker
            .getRegistration('/cashier')
            .then((r) => (r ? r.update() : null))
            .catch(() => null)
    );
    await page.waitForTimeout(1500);
}

// ── s1 · 部署窗口:装不上就别上位 ─────────────────────────────────────────
async function deployWindow(browser, origin) {
    const ctx = await browser.newContext({ baseURL: origin });
    const page = await ctx.newPage();
    state.cashierV = OLD_V;
    state.shell = 200;
    await page.goto(`${origin}/cashier`);
    const reg = await registerSw(page, '/cashier-sw.js', '/cashier');
    await page.waitForTimeout(1200);
    const beforeKeys = await cacheKeys(page);
    const beforeShell = await hasShell(page, `pearnly-cashier-v${OLD_V}`, '/cashier');

    // 断网重开:这一版真的能离线开机(不然后面「老缓存还在」就只是个名字)
    await ctx.setOffline(true);
    await page.goto(`${origin}/cashier`);
    const offlineBefore = await page.textContent('#m').catch(() => '');
    await ctx.setOffline(false);

    // 部署中:新版 SW 已经发下来了,而 /cashier 正回 502
    state.cashierV = NEW_V;
    state.shell = 502;
    await page.goto(`${origin}/cashier`);
    await updateSw(page);
    const midKeys = await cacheKeys(page);
    const midShell = await hasShell(page, `pearnly-cashier-v${OLD_V}`, '/cashier');
    await ctx.setOffline(true);
    await page.goto(`${origin}/cashier`);
    const offlineMid = await page.textContent('#m').catch(() => '');
    await shot(page, 's1-offline-during-deploy.png');
    await ctx.setOffline(false);

    // 部署结束:再更新一次才该换代
    state.shell = 200;
    await page.goto(`${origin}/cashier`);
    await updateSw(page);
    await page.waitForTimeout(1200);
    const afterKeys = await cacheKeys(page);
    const afterShell = await hasShell(page, `pearnly-cashier-v${NEW_V}`, '/cashier');
    await ctx.setOffline(true);
    await page.goto(`${origin}/cashier`);
    const offlineAfter = await page.textContent('#m').catch(() => '');
    await ctx.setOffline(false);
    await page.close();
    await ctx.close();
    return {
        ok:
            reg.ok &&
            beforeKeys.includes(`pearnly-cashier-v${OLD_V}`) &&
            beforeShell &&
            offlineBefore === 'CASHIER-SHELL' &&
            // 装不上 → 老缓存原样留着,断网照旧开得了
            midKeys.includes(`pearnly-cashier-v${OLD_V}`) &&
            midShell &&
            offlineMid === 'CASHIER-SHELL' &&
            // 恢复之后才换代,且换完仍然离线可用
            afterKeys.includes(`pearnly-cashier-v${NEW_V}`) &&
            !afterKeys.includes(`pearnly-cashier-v${OLD_V}`) &&
            afterShell &&
            offlineAfter === 'CASHIER-SHELL',
        reg,
        beforeKeys,
        beforeShell,
        offlineBefore,
        midKeys,
        midShell,
        offlineMid,
        afterKeys,
        afterShell,
        offlineAfter,
    };
}

// ── s2 · 老设备的 /pos 外壳 + 新家 /cashier 同时在 ───────────────────────
// 产品里 pos.js 明写「老 /pos 作用域 SW 故意保留 …… 各管各的作用域,互不干扰」。
// 作用域分得开的是导航;CacheStorage 是按源的,分不开。
async function twoScopes(browser, origin) {
    const ctx = await browser.newContext({ baseURL: origin });
    const page = await ctx.newPage();
    state.cashierV = NEW_V;
    state.shell = 200;
    state.posShell = 200;

    // 老设备:先有 /pos 的离线外壳
    await gotoText(page, `${origin}/pos`);
    const posReg = await registerSw(page, '/pos-sw.js', '/pos');
    await page.waitForTimeout(1200);
    const posKeyName = `pearnly-pos-v${NEW_V}`;
    const afterPos = await cacheKeys(page);
    const posShellCached = await hasShell(page, posKeyName, '/pos');
    await ctx.setOffline(true);
    const posOfflineBefore = await gotoText(page, `${origin}/pos`);
    await ctx.setOffline(false);

    // 同一台机器改用新家 /cashier(pos.js 在这里注册 cashier-sw)
    await gotoText(page, `${origin}/cashier`);
    const cashReg = await registerSw(page, '/cashier-sw.js', '/cashier');
    await page.waitForTimeout(1500);
    const afterCash = await cacheKeys(page);
    const posStillCached = await hasShell(page, posKeyName, '/pos');

    // 回头再点老书签 / 桌面图标 → /pos 断网还开不开得了
    await ctx.setOffline(true);
    const posOfflineAfter = await gotoText(page, `${origin}/pos`);
    await shot(page, 's2-pos-offline-after-cashier.png');
    await ctx.setOffline(false);
    await page.close();
    await ctx.close();
    return {
        ok:
            posReg.ok &&
            cashReg.ok &&
            afterPos.includes(posKeyName) &&
            posShellCached &&
            posOfflineBefore === 'POS-SHELL' &&
            // 开一次 /cashier 不该把老设备的 /pos 离线外壳清掉
            afterCash.includes(posKeyName) &&
            posStillCached &&
            posOfflineAfter === 'POS-SHELL',
        posReg,
        cashReg,
        afterPos,
        posShellCached,
        posOfflineBefore,
        afterCash,
        posStillCached,
        posOfflineAfter,
    };
}

// ── s3 · 反方向:在用的收银台被「顺手点了一下老 /pos」清掉离线外壳 ──────────
// 老 /pos 那个 SW 的字节在本批也 bump 过(见 routes/pages_routes.py 的 /pos-sw.js 注),
// 所以老书签/桌面图标被点一下就会触发它的 install→activate。
async function posVisitEatsCashier(browser, origin) {
    const ctx = await browser.newContext({ baseURL: origin });
    const page = await ctx.newPage();
    state.cashierV = NEW_V;
    state.posV = OLD_V;
    state.shell = 200;
    state.posShell = 200;

    // 这台机器是真在用的收银台:/cashier 外壳装好、断网开得了
    await gotoText(page, `${origin}/cashier`);
    await registerSw(page, '/cashier-sw.js', '/cashier');
    await page.waitForTimeout(1200);
    const cashKey = `pearnly-cashier-v${NEW_V}`;
    const beforeKeys = await cacheKeys(page);
    await ctx.setOffline(true);
    const cashOfflineBefore = await gotoText(page, `${origin}/cashier`);
    await ctx.setOffline(false);

    // 老设备上那个 /pos 的 SW 也还在(装的是上一版)
    await gotoText(page, `${origin}/pos`);
    await registerSw(page, '/pos-sw.js', '/pos');
    await page.waitForTimeout(1200);

    // 本批 bump 之后再点一下老 /pos:它更新 → install → activate
    state.posV = NEW_V;
    await gotoText(page, `${origin}/pos`);
    await page.evaluate(() =>
        navigator.serviceWorker
            .getRegistration('/pos')
            .then((r) => (r ? r.update() : null))
            .catch(() => null)
    );
    await page.waitForTimeout(2000);
    const afterKeys = await cacheKeys(page);
    const cashStillCached = await hasShell(page, cashKey, '/cashier');
    await ctx.setOffline(true);
    const cashOfflineAfter = await gotoText(page, `${origin}/cashier`);
    await shot(page, 's3-cashier-offline-after-pos-visit.png');
    await ctx.setOffline(false);
    await page.close();
    await ctx.close();
    return {
        // 点一下老 /pos 不该把在用的收银台离线外壳清掉
        ok:
            beforeKeys.includes(cashKey) &&
            cashOfflineBefore === 'CASHIER-SHELL' &&
            afterKeys.includes(cashKey) &&
            cashStillCached &&
            cashOfflineAfter === 'CASHIER-SHELL',
        beforeKeys,
        cashOfflineBefore,
        afterKeys,
        cashStillCached,
        cashOfflineAfter,
    };
}

// ── s4 · 联网导航先问服务器,断网才回落缓存 ───────────────────────────────
async function freshNavigation(browser, origin) {
    const ctx = await browser.newContext({ baseURL: origin });
    const page = await ctx.newPage();
    state.cashierV = NEW_V;
    state.shell = 200;
    state.cashierMarker = 'CASHIER-OLD';
    await gotoText(page, `${origin}/cashier`);
    await registerSw(page, '/cashier-sw.js', '/cashier');
    await page.waitForTimeout(1200);

    state.cashierMarker = 'CASHIER-NEW';
    const online = await gotoText(page, `${origin}/cashier`);
    await ctx.setOffline(true);
    const offline = await gotoText(page, `${origin}/cashier`);
    await shot(page, 's4-current-shell-offline.png');
    await ctx.setOffline(false);
    await page.close();
    await ctx.close();
    state.cashierMarker = 'CASHIER-SHELL';
    return { ok: online === 'CASHIER-NEW' && offline === 'CASHIER-NEW', online, offline };
}

const CASES = [
    ['s1_deployWindow', deployWindow],
    ['s2_twoScopes', twoScopes],
    ['s3_posVisitEatsCashier', posVisitEatsCashier],
    ['s4_freshNavigation', freshNavigation],
];

(async () => {
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch();
    const failed = await runCases(
        CASES.filter(([name]) => !ONLY || name.indexOf(ONLY) >= 0),
        (fn) => fn(browser, origin),
        path.join(SHOTS, 'report-hostile-sw.json')
    );
    await browser.close();
    server.close();
    process.exit(failed ? 1 : 0);
})().catch((e) => {
    console.error('HOSTILE SW CRASH', e);
    process.exit(2);
});
