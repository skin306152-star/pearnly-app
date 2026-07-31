// 录入工作台 ERP 卡「小助手掉线」真浏览器验收。
// 断言取 getComputedStyle 的真实颜色 + 真实文字,不看类名(类名对了颜色被压过的坑犯过)。
// 中泰两遍都跑:泰文界面是会计的日常语言,只验中文等于没验。
// 最后一项真等一轮轮询,验证小助手上线后卡片自己回绿 —— 不靠刷新页面。
// 跑法: node scripts/_erp_card_offline_ui_verify.cjs → tests/visual/_shot/erpcard-*.png
/* eslint-disable no-undef */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'tests', 'visual', '_shot');
const PORT = 8797;
const TYPES = {
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.html': 'text/html',
    '.map': 'application/json',
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.woff2': 'font/woff2',
};

// 令牌真值:--dx-green #2aa971 / --dx-amber #c98a1e。颜色是断言的锚,别退化成类名比对。
const GREEN = 'rgb(42, 169, 113)';
const AMBER = 'rgb(201, 138, 30)';

// 四语都认:同一份断言跑任何语言,顺带证明该语种没落下翻译。
const SAY = {
    connected: /已连接|เชื่อมต่อแล้ว|Connected|接続済み/,
    offline: /离线|ออฟไลน์|Offline|オフライン/,
    auto: /自动推送|ส่งอัตโนมัติ|Auto push|自動送信/,
    disabled: /已停用|ปิดใช้งานแล้ว|Disabled|無効/,
};

function serve() {
    const srv = http.createServer((req, res) => {
        let p = decodeURIComponent(req.url.split('?')[0]);
        if (p === '/home') p = '/home.html';
        const file = path.join(ROOT, p);
        if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
            res.writeHead(404);
            return res.end('nf');
        }
        res.writeHead(200, {
            'content-type': TYPES[path.extname(file)] || 'text/plain',
            'cache-control': 'no-store',
        });
        fs.createReadStream(file).pipe(res);
    });
    return new Promise((r) => srv.listen(PORT, () => r(srv)));
}

const ago = (ms) => new Date(Date.now() - ms).toISOString();

// 端点响应由 scenario 决定,轮询期间换 scenario 即可模拟小助手上下线。
let scenario = 'online';
function endpoints() {
    const express = {
        id: 'e1',
        adapter: 'express',
        name: 'Express',
        enabled: true,
        auto_push: true,
        config: {},
    };
    const mrerp = {
        id: 'e2',
        adapter: 'mrerp',
        name: 'MR.ERP',
        enabled: true,
        auto_push: true,
        config: {},
    };
    if (scenario === 'online') express.config.agent_last_seen_at = ago(30000);
    else if (scenario === 'offline') express.config.agent_last_seen_at = ago(600000);
    else if (scenario === 'shutdown') express.config.agent_last_seen_at = '1970-01-01T00:00:00Z';
    else if (scenario === 'disabled') {
        express.enabled = false;
        express.config.agent_last_seen_at = ago(30000);
    }
    // never: config 保持空 —— 从未配对过
    return { items: [express, mrerp] };
}

const CARD_READY = '.dx-erp-card[data-erp="express"] [data-erp-status]';

async function boot(ctx, lang) {
    const page = await ctx.newPage();
    // 没有 token 前端停在未认证态,routeTo 永远不会挂上 window。
    await page.addInitScript((lg) => {
        localStorage.setItem('mrpilot_token', 'tok');
        localStorage.setItem('mrpilot_lang', lg);
    }, lang);
    await page.route('**/api/**', (route) => {
        const u = route.request().url();
        if (u.includes('/api/erp/endpoints'))
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(endpoints()),
            });
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true }),
        });
    });
    const errs = [];
    page.on('pageerror', (e) => errs.push(String(e)));
    await page.goto('http://localhost:' + PORT + '/home', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof window.routeTo === 'function');
    await page.evaluate(() => {
        window.isOwner = () => true;
        window._userInfo = Object.assign(window._userInfo || {}, {
            can_push_erp: true,
            plan: 'lifetime',
        });
        document.body.classList.remove('workspace-gate-preboot');
        document.getElementById('workspace-gate-root')?.remove();
        const st = document.createElement('style');
        st.textContent =
            '#ws-modal{display:none!important}#workspace-gate-root{display:none!important}';
        document.head.appendChild(st);
        window.routeTo('dms-intake');
    });
    await page.waitForSelector(CARD_READY, { timeout: 15000 });
    return { page, errs };
}

// 状态的真实观测:文字 + 计算色。两者都要 —— 文字对了颜色不对照样是半成品。
const readCard = (page, adapter) =>
    page.evaluate((a) => {
        const el = document.querySelector(`.dx-erp-card[data-erp="${a}"] [data-erp-status]`);
        if (!el) return null;
        return { text: el.textContent.trim(), color: getComputedStyle(el).color };
    }, adapter);

// 换场景后强制重渲(轮询用例除外,那里要的就是不重渲)。
async function reload(page, next) {
    scenario = next;
    await page.evaluate(() => window.routeTo('dashboard'));
    await page.evaluate(() => window.routeTo('dms-intake'));
    await page.waitForSelector(CARD_READY, { timeout: 15000 });
    await page.waitForTimeout(400);
}

let pass = 0;
let fail = 0;
function chk(name, ok) {
    ok ? pass++ : fail++;
    console.log((ok ? 'PASS' : 'FAIL').padEnd(5), name);
    return ok;
}
// 翻译漏一语就会把 key 原样吐给会计,比不显示更糟。
const notRawKey = (s) => !/^dx-erp-/.test(s.text);

async function runLang(ctx, lang, withPolling) {
    console.log(`\n———— 语言 ${lang} ————`);
    scenario = 'online';
    const { page, errs } = await boot(ctx, lang);

    let s = await readCard(page, 'express');
    console.log('  在线:', JSON.stringify(s));
    chk(`[${lang}] 在线:说「已连接」`, SAY.connected.test(s.text));
    chk(`[${lang}] 在线:带推送方式`, SAY.auto.test(s.text));
    chk(`[${lang}] 在线:计算色=令牌绿`, s.color === GREEN);
    chk(`[${lang}] 在线:不是裸 key`, notRawKey(s));
    await page.screenshot({ path: path.join(OUT, `erpcard-online-${lang}.png`) });

    await reload(page, 'offline');
    s = await readCard(page, 'express');
    console.log('  离线:', JSON.stringify(s));
    chk(`[${lang}] ★离线:说「离线」`, SAY.offline.test(s.text));
    chk(`[${lang}] ★离线:不再谎称已连接`, !SAY.connected.test(s.text));
    chk(`[${lang}] ★离线:计算色=令牌琥珀(不是绿)`, s.color === AMBER);
    chk(`[${lang}] ★离线:不是裸 key`, notRawKey(s));
    await page.screenshot({ path: path.join(OUT, `erpcard-offline-${lang}.png`) });

    // MR.ERP 云端直连,没有小助手 —— 不能被离线判定误伤。
    const m = await readCard(page, 'mrerp');
    console.log('  MR.ERP:', JSON.stringify(m));
    chk(`[${lang}] MR.ERP 未被误伤,仍已连接`, SAY.connected.test(m.text));
    chk(`[${lang}] MR.ERP 计算色仍是绿`, m.color === GREEN);

    await reload(page, 'shutdown');
    s = await readCard(page, 'express');
    chk(`[${lang}] 小助手主动退出(1970 哨兵)→ 离线`, SAY.offline.test(s.text));

    await reload(page, 'never');
    s = await readCard(page, 'express');
    chk(`[${lang}] 从未配对(无心跳字段)→ 离线`, SAY.offline.test(s.text));

    await reload(page, 'disabled');
    s = await readCard(page, 'express');
    chk(`[${lang}] 已停用优先于离线`, SAY.disabled.test(s.text));

    if (withPolling) {
        // 会计照教程启动小助手后回到这一页:不刷新,卡片必须自己回绿。
        await reload(page, 'offline');
        s = await readCard(page, 'express');
        chk(`[${lang}] 轮询前置:先处于离线`, SAY.offline.test(s.text));
        scenario = 'online';
        await page.waitForTimeout(35000);
        s = await readCard(page, 'express');
        console.log('  轮询 35s 后:', JSON.stringify(s));
        chk(`[${lang}] ★★轮询:小助手上线后自己回绿(未刷新)`, SAY.connected.test(s.text));
        chk(`[${lang}] ★★轮询:回绿后计算色=令牌绿`, s.color === GREEN);
        await page.screenshot({ path: path.join(OUT, `erpcard-recovered-${lang}.png`) });
    }

    chk(`[${lang}] 无页面 JS 错误`, errs.length === 0);
    if (errs.length) console.log('  pageerror:', errs.slice(0, 3));
    await page.close();
}

async function run() {
    fs.mkdirSync(OUT, { recursive: true });
    const srv = await serve();
    const browser = await chromium.launch();
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });

    await runLang(ctx, 'th', true);
    await runLang(ctx, 'zh', false);

    await browser.close();
    srv.close();
    console.log(`\n${pass} passed, ${fail} failed`);
    process.exit(fail ? 1 : 0);
}

run().catch((e) => {
    console.error(e);
    process.exit(1);
});
