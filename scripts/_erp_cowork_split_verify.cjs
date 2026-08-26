// E2E 真浏览器验收(2026-08-26 · cowork/erp 门壳拆分)· 只新增本文件与截图,不改任何源码/测试/dist。
//
// 验收目标(逐条对应前端 skill「verification→截图」范式:isVisible + getComputedStyle,输入用 keyboard.type):
//   1. /login 302 → /cowork(不再直接出登录页)。
//   2. /cowork 未登录 = 旧登录 UI(landing.js 的 auth-shell / #form-login),不是 ERP 门;桌面 + 390x844 截图。
//   3. /erp 未登录 = 独立 ERP 登录门(#p-form / #p-email),不是主站登录;桌面 + 390x844 截图。
//   4. 带 localStorage token + API 桩进共享 home SPA:
//        cowork 顶级菜单严格 = 首页 · Pearnly Cowork · 主数据 · 使用教程;
//        erp   顶级菜单严格 = 首页 · 商品 · 采购系统 · 销售系统 · 主数据;
//        两边左下账号信息(#sb-user)可见、右上账套切换器(#ws-ctrl-btn)与头像(#avatar-btn)可见。
//   5. 全局 topbar 无搜索、无 CmdK 命令面板;但账套切换器(orgsw-pop)内部搜索存在且能聚焦收键盘输入。
//   6. 跨壳深链:入口守卫(_entryGuardRoute/COWORK·ERP_ALLOWED_ROUTES)——未纳入本壳白名单的路由
//        回当前入口首页(dashboard);白名单内的可深链子页不回退(同一路由两壳行为相反,如 stock-card/history)。
//
// 对端 = 本地已起的真实 app。网络 API 全部用 page.route 精确桩(只桩 /api/**,静态资源走真实 server)。
// 只读源码与导航清洗,nth/first/last 一律不用(点选必唯一定位)。
//
// 跑法:node scripts/_erp_cowork_split_verify.cjs   (失败 exit 非零)
/* eslint-disable no-undef */
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const BASE = 'http://127.0.0.1:8765';
const ROOT = path.resolve(__dirname, '..');
const ART = path.join(ROOT, 'tests', 'e2e', '_artifacts', 'erp-cowork-split');

const DESKTOP = { width: 1280, height: 900 };
const MOBILE = { width: 390, height: 844 };

const COWORK_MENU = ['首页', 'Pearnly Cowork', '主数据', '使用教程'];
const ERP_MENU = ['首页', '商品', '采购系统', '销售系统', '主数据'];

// 桩的账号/账套内容(验收对象是导航壳,不是数据;但主体列表要给几个可搜的,才会触发内部搜索过滤)。
const ME = {
    id: 'u1',
    username: 'demo',
    email: 'demo@pearnly.com',
    role: 'owner',
    is_owner: true,
    is_super_admin: false,
    tenant_role: 'owner',
    company_name: 'Demo Co Ltd',
};
const CLIENTS = [
    { id: 1, name: 'Demo Co Ltd', tax_id: '0105567178203' },
    { id: 2, name: 'Second Co', tax_id: '0994000333444' },
];

const tally = { pass: 0, fail: 0 };
function chk(name, ok, extra) {
    ok ? tally.pass++ : tally.fail++;
    console.log((ok ? 'PASS' : 'FAIL').padEnd(5), name, extra === undefined ? '' : '· ' + extra);
    return ok;
}
function summary() {
    console.log(`\n${tally.pass} passed, ${tally.fail} failed`);
    return tally.fail ? 1 : 0;
}

const json = (body, status = 200) => ({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
});

// /api/** 精确桩。只返回 SPA boot 必需的最小集,其余给空对象(apiGet 见到 200 + 可 json 化即不抛)。
function routeStub(entry) {
    return (route) => {
        const p = new URL(route.request().url()).pathname;
        if (p === '/api/me') return route.fulfill(json(ME));
        if (p === '/api/me/modules')
            return route.fulfill(json({ data: { modules: {}, business_type: 'firm', entry } }));
        if (p === '/api/workspace/clients') return route.fulfill(json({ clients: CLIENTS }));
        if (p === '/api/ocr/quota') return route.fulfill(json({ ok: true, pages: 100 }));
        return route.fulfill(json({}));
    };
}

// 起一个已登录、已选中账套、停在指定 hash 的 home SPA page(返回 {ctx,page,pageerrs})。
async function boot(browser, { entry, hash, viewport }) {
    const ctx = await browser.newContext({ viewport });
    const page = await ctx.newPage();
    await page.addInitScript((e) => {
        localStorage.setItem('mrpilot_token', 'tok');
        localStorage.setItem('mrpilot_lang', 'zh');
        localStorage.setItem('pearnly_entry', e);
        localStorage.setItem('pearnly_active_workspace_client_id', '1');
    }, entry);
    await page.route('**/api/**', routeStub(entry));
    const pageerrs = [];
    page.on('pageerror', (e) => pageerrs.push(String(e)));
    await page.goto(BASE + '/home?canonical=' + entry + (hash ? '#' + hash : ''), {
        waitUntil: 'domcontentloaded',
    });
    await page.waitForSelector('#sidebar .nav-item[data-route="dashboard"]', { timeout: 15000 });
    await page.waitForTimeout(1200);
    return { ctx, page, pageerrs };
}

// 顶层菜单项(DOM 顺序,含可见性/display)。只收 .sb-nav 直属的折叠组与单页项,不含分隔线/底部用户卡。
async function menuItems(page) {
    const sel =
        '#sidebar .sb-nav > .nav-group[data-collapsible], ' +
        '#sidebar .sb-nav > .nav-item[data-route]';
    const els = await page.locator(sel).all();
    const out = [];
    for (const el of els) {
        const vis = await el.isVisible();
        const display = await el.evaluate((e) => getComputedStyle(e).display);
        const text = await el.evaluate((e) => {
            const t = e.classList.contains('nav-group')
                ? e.querySelector('.nav-group-toggle .nav-label')
                : e.querySelector('.nav-label');
            return t ? t.textContent.trim() : null;
        });
        out.push({ vis, display, text });
    }
    return out;
}

// 验证一个 shell 的顶级菜单严格等于预期(不多不少,顺序一致),并对每项做 isVisible + getComputedStyle。
async function verifyMenu(page, shell, expected) {
    const items = await menuItems(page);
    const visible = items.filter((i) => i.vis && i.display !== 'none' && i.text).map((i) => i.text);
    chk(
        `${shell} 顶级菜单严格仅 ${expected.length} 项:${expected.join(' / ')}`,
        visible.length === expected.length && JSON.stringify(visible) === JSON.stringify(expected),
        '实际=' + JSON.stringify(visible)
    );
    for (const label of expected) {
        const m = items.filter((i) => i.text === label);
        chk(
            `${shell} 顶级菜单项「${label}」可见(isVisible + display!==none)`,
            m.length === 1 && m[0].vis && m[0].display !== 'none',
            'display=' + (m[0] && m[0].display)
        );
    }
    // 反向互证:非白名单顶级组必须 display:none(确认「严格只有」不是靠漏测)。
    const others = items.filter((i) => i.text && !expected.includes(i.text));
    const wrong = others.some((i) => i.vis || i.display !== 'none');
    chk(
        `${shell} 非白名单顶级项均被隐藏`,
        !wrong,
        others.map((i) => `${i.text}=${i.display}`).join(', ')
    );
}

// 全局 topbar 无搜索 / 无 CmdK;但账套切换器内部搜索存在且能聚焦收键盘输入。
async function verifyTopbarAndWsSearch(page, shell) {
    const topbar = await page.evaluate(() => ({
        inputs: document.querySelectorAll(
            '#topbar input, #topbar [type=search], #topbar [role=searchbox]'
        ).length,
        searchbar: document.querySelectorAll('#topbar .topbar-search, #topbar [data-global-search]')
            .length,
    }));
    chk(`${shell} 全局 topbar 无搜索输入`, topbar.inputs === 0 && topbar.searchbar === 0);

    const paletteSel =
        '#cmdk, [data-cmdk], .cmdk, .cmdk-palette, .command-palette, [data-command-palette], .palette';
    const overlaySig = () =>
        page.evaluate((ps) => {
            const palette = document.querySelectorAll(ps).length;
            const dialogs = [...document.querySelectorAll('[role=dialog], .modal-overlay')].filter(
                (e) => {
                    const c = getComputedStyle(e);
                    return c.display !== 'none' && c.visibility !== 'hidden';
                }
            ).length;
            return { palette, dialogs, url: location.href };
        }, paletteSel);
    const sigBefore = await overlaySig();
    chk(`${shell} 无 CmdK 命令面板元素(静态)`, sigBefore.palette === 0);
    await page.keyboard.press('Meta+k');
    await page.waitForTimeout(300);
    const sigAfter = await overlaySig();
    chk(
        `${shell} 按 Cmd/Ctrl+K 不弹命令面板、不盖弹层、不改 URL`,
        sigAfter.palette === 0 &&
            sigAfter.dialogs === sigBefore.dialogs &&
            sigAfter.url === sigBefore.url
    );

    // 账套切换器内部搜索
    await page.click('#ws-ctrl-btn');
    await page.waitForTimeout(250);
    const pop = await page.evaluate(() => ({
        pop: !!document.getElementById('orgsw-pop'),
        srch: !!document.getElementById('orgsw-srch-in'),
    }));
    chk(`${shell} 账套切换器打开且内部搜索存在`, pop.pop && pop.srch);

    await page.click('#orgsw-srch-in');
    await page.keyboard.type('Second');
    await page.waitForTimeout(200);
    const st = await page.evaluate(() => ({
        activeId: document.activeElement ? document.activeElement.id : null,
        val: document.getElementById('orgsw-srch-in')
            ? document.getElementById('orgsw-srch-in').value
            : null,
        filtered: [...document.querySelectorAll('[data-orgpick] .onm')].map((e) =>
            e.textContent.trim()
        ),
    }));
    chk(
        `${shell} 内部搜索框获得焦点且收下键盘输入`,
        st.activeId === 'orgsw-srch-in' && st.val === 'Second',
        `active=${st.activeId}, val=${st.val}`
    );
    chk(
        `${shell} 内部搜索按词过滤主体`,
        st.filtered.length === 1 && st.filtered[0] === 'Second Co'
    );
    await page.screenshot({ path: path.join(ART, `${shell}-ws-switcher-search.png`) });

    // 收起切换器,别挡下面截图。
    await page.keyboard.press('Escape');
    await page.keyboard.press('Escape');
    await page.click('body', { position: { x: 5, y: 5 } }).catch(() => {});
    await page.waitForTimeout(150);
}

// 左下账号信息 + 右上账套切换器/头像 可见性(isVisible + getComputedStyle)。
async function verifyChrome(page, shell) {
    const vis = await page.evaluate((sels) => {
        const iv = (sel) => {
            const e = document.querySelector(sel);
            if (!e) return { exists: false };
            const cs = getComputedStyle(e);
            const r = e.getBoundingClientRect();
            return {
                exists: true,
                display: cs.display,
                visibility: cs.visibility,
                hasBox: r.width > 0 && r.height > 0,
            };
        };
        return {
            sbUser: iv('#sb-user'),
            sbUserName: iv('#sb-user-name'),
            sbMail: iv('#sb-user-mail'),
            wsCtrl: iv('#ws-ctrl-btn'),
            avatar: iv('#avatar-btn'),
        };
    }, shell);
    // Playwright 层面再各用一次 isVisible(真渲染可见),与 getComputedStyle 双证。
    const pw = {
        sbUser: await page.locator('#sb-user').isVisible(),
        wsCtrl: await page.locator('#ws-ctrl-btn').isVisible(),
        avatar: await page.locator('#avatar-btn').isVisible(),
    };
    chk(
        `${shell} 左下账号信息可见(isVisible + getComputedStyle)`,
        vis.sbUser.exists &&
            vis.sbUser.display !== 'none' &&
            vis.sbUser.hasBox &&
            pw.sbUser &&
            vis.sbUserName.exists &&
            vis.sbUserName.hasBox &&
            vis.sbMail.exists &&
            vis.sbMail.hasBox,
        `sbUser.isVisible=${pw.sbUser}, display=${vis.sbUser.display}`
    );
    chk(
        `${shell} 右上账套切换器(#ws-ctrl-btn)可见`,
        vis.wsCtrl.exists && vis.wsCtrl.display !== 'none' && vis.wsCtrl.hasBox && pw.wsCtrl,
        `isVisible=${pw.wsCtrl}, display=${vis.wsCtrl.display}`
    );
    chk(
        `${shell} 右上头像(#avatar-btn)可见`,
        vis.avatar.exists && vis.avatar.display !== 'none' && vis.avatar.hasBox && pw.avatar,
        `isVisible=${pw.avatar}, display=${vis.avatar.display}`
    );
}

const shot = (page, name) => page.screenshot({ path: path.join(ART, name) });

async function verifyLogin302() {
    const resp = await fetch(BASE + '/login', { redirect: 'manual' }).catch(() => null);
    const loc = resp && resp.headers ? resp.headers.get('location') : null;
    chk('/login 返回 302', resp && resp.status === 302, `status=${resp && resp.status}`);
    chk('/login 302 → /cowork', loc === '/cowork', 'location=' + loc);
}

async function verifyCoworkLogin(browser) {
    const ctx = await browser.newContext({ viewport: DESKTOP });
    const page = await ctx.newPage();
    await page.goto(BASE + '/cowork', { waitUntil: 'domcontentloaded' }).catch(() => {});
    await page.waitForSelector('#form-login', { timeout: 15000 });
    const r = await page.evaluate(() => ({
        url: location.href,
        pathname: location.pathname,
        authRoot: !!document.getElementById('pearnly-auth-root'),
        authShell: document.querySelectorAll('.auth-shell').length,
        formLogin: document.querySelectorAll('#form-login').length,
        liUser: document.querySelectorAll('#li-username').length,
        liPw: document.querySelectorAll('#li-password').length,
        erpForm: document.querySelectorAll('#p-form').length,
    }));
    chk('/cowork 未登录停留在 /cowork', r.pathname === '/cowork', r.url);
    chk(
        '/cowork 呈现旧登录 UI(auth-shell + form-login)',
        r.authRoot && r.authShell === 1 && r.formLogin === 1
    );
    chk('/cowork 不是独立 ERP 登录门', r.erpForm === 0);
    const es = await page.locator('.auth-shell').isVisible();
    chk('/cowork 登录卡片可见(isVisible)', es);

    // 输入焦点用 keyboard.type 验,不用 fill。
    await page.click('#li-username');
    await page.keyboard.type('pearnly');
    const f = await page.evaluate(() => ({
        activeId: document.activeElement ? document.activeElement.id : null,
        val: document.getElementById('li-username')
            ? document.getElementById('li-username').value
            : null,
    }));
    chk(
        '/cowork 登录账号框获焦且收下键盘输入',
        f.activeId === 'li-username' && f.val === 'pearnly'
    );

    await page.keyboard.press('Escape');
    await shot(page, 'cowork-login-desktop.png');
    await ctx.close();

    // 手机
    const mctx = await browser.newContext({ viewport: MOBILE });
    const mpage = await mctx.newPage();
    await mpage.goto(BASE + '/cowork', { waitUntil: 'domcontentloaded' }).catch(() => {});
    await mpage.waitForSelector('#form-login', { timeout: 15000 });
    chk('/cowork 手机 390x844 仍为旧登录 UI', (await mpage.locator('#form-login').count()) === 1);
    await shot(mpage, 'cowork-login-mobile-390.png');
    await mctx.close();
}

async function verifyErpLogin(browser) {
    const ctx = await browser.newContext({ viewport: DESKTOP });
    const page = await ctx.newPage();
    await page.goto(BASE + '/erp', { waitUntil: 'domcontentloaded' }).catch(() => {});
    await page.waitForSelector('#p-form', { timeout: 15000 });
    const r = await page.evaluate(() => ({
        url: location.href,
        pathname: location.pathname,
        form: document.querySelectorAll('#p-form').length,
        email: document.querySelectorAll('#p-email').length,
        pw: document.querySelectorAll('#p-pw').length,
        submit: document.querySelectorAll('#p-submit').length,
        coworkAuth: document.querySelectorAll('#pearnly-auth-root, #form-login').length,
        tag: (document.getElementById('p-tag') || {}).textContent,
    }));
    chk('/erp 未登录停留在 /erp', r.pathname === '/erp', r.url);
    chk(
        '/erp 呈现独立 ERP 登录门(p-form/p-email/p-pw/p-submit)',
        r.form === 1 && r.email === 1 && r.pw === 1 && r.submit === 1
    );
    chk('/erp 不是主站登录 UI', r.coworkAuth === 0);
    chk('/erp 门头标注 ERP 门户', typeof r.tag === 'string' && r.tag.length > 0, r.tag);
    chk('/erp 登录卡片可见(isVisible)', await page.locator('#p-form').isVisible());

    await page.click('#p-email');
    await page.keyboard.type('pearnly');
    const f = await page.evaluate(() => ({
        activeId: document.activeElement ? document.activeElement.id : null,
        val: document.getElementById('p-email') ? document.getElementById('p-email').value : null,
    }));
    chk('/erp 账号框获焦且收下键盘输入', f.activeId === 'p-email' && f.val === 'pearnly');

    await shot(page, 'erp-login-desktop.png');
    await ctx.close();

    const mctx = await browser.newContext({ viewport: MOBILE });
    const mpage = await mctx.newPage();
    await mpage.goto(BASE + '/erp', { waitUntil: 'domcontentloaded' }).catch(() => {});
    await mpage.waitForSelector('#p-form', { timeout: 15000 });
    chk('/erp 手机 390x844 仍为独立 ERP 登录门', (await mpage.locator('#p-form').count()) === 1);
    await shot(mpage, 'erp-login-mobile-390.png');
    await mctx.close();
}

async function verifyHome(browser, entry, shell) {
    const expected = entry === 'erp' ? ERP_MENU : COWORK_MENU;

    // 桌面
    const { ctx, page, pageerrs } = await boot(browser, {
        entry,
        hash: '/dashboard',
        viewport: DESKTOP,
    });
    await verifyMenu(page, shell, expected);
    await verifyChrome(page, shell);
    await verifyTopbarAndWsSearch(page, shell);
    chk(
        `${shell} 停在 dashboard`,
        (await page.evaluate(() => document.querySelector('.page.active')?.id)) === 'page-dashboard'
    );
    await shot(page, `${shell}-home-desktop.png`);
    await ctx.close();

    // 手机:开抽屉菜单截图 + 复验顶级菜单结构
    const m = await boot(browser, { entry, hash: '/dashboard', viewport: MOBILE });
    await m.page.click('#topbar-hamburger').catch(() => {});
    await m.page.waitForTimeout(300);
    const mItems = await menuItems(m.page);
    const mVis = mItems.filter((i) => i.vis && i.display !== 'none' && i.text).map((i) => i.text);
    chk(
        `${shell} 手机(抽屉开)顶级菜单仍严格 = ${expected.join(' / ')}`,
        JSON.stringify(mVis) === JSON.stringify(expected),
        '实际=' + JSON.stringify(mVis)
    );
    await shot(m.page, `${shell}-home-mobile-390.png`);
    await m.ctx.close();

    chk(`${shell} 无未捕获页面错误`, pageerrs.length === 0, pageerrs.slice(0, 2).join(' ; '));
}

async function verifyDeepLink(browser, { entry, hash, expectHash, expectActive, shell }) {
    const { ctx, page } = await boot(browser, { entry, hash, viewport: DESKTOP });
    const r = await page.evaluate(() => ({
        hash: location.hash,
        active: document.querySelector('.page.active')
            ? document.querySelector('.page.active').id
            : null,
    }));
    chk(`${shell} 深链 ${hash} 落到 ${expectHash}`, r.hash === expectHash, `实际 ${r.hash}`);
    chk(
        `${shell} 深链回落/保持页面=${expectActive}`,
        r.active === expectActive,
        `实际 ${r.active}`
    );
    await ctx.close();
}

async function run() {
    fs.mkdirSync(ART, { recursive: true });

    // 预检:本地 app 是否在 8765。
    const up = await fetch(BASE + '/cowork')
        .then((r) => r.ok)
        .catch(() => false);
    if (!up) {
        console.error(`本地 app 不在 ${BASE} —— 起好后重跑。`);
        return process.exit(1);
    }

    await verifyLogin302();
    await verifyCoworkLogin(browser);
    await verifyErpLogin(browser);

    // 共享 home SPA(带 token + API 桩)
    await verifyHome(browser, 'cowork', 'cowork');
    await verifyHome(browser, 'erp', 'erp');

    // 跨壳深链:入口守卫(_entryGuardRoute / COWORK·ERP_ALLOWED_ROUTES)决定——
    //   未纳入本壳白名单的路由 → 回当前入口首页(dashboard);白名单内的可深链子页 → 不回退。
    //   stock-card 在 cowork 被拦、在 erp 放行;history 在 cowork 放行、在 erp 被拦 —— 同一路由两壳行为相反。
    await verifyDeepLink(browser, {
        entry: 'cowork',
        hash: '/stock-card',
        expectHash: '#/dashboard',
        expectActive: 'page-dashboard',
        shell: 'cowork',
    });
    await verifyDeepLink(browser, {
        entry: 'cowork',
        hash: '/reconcile',
        expectHash: '#/reconcile',
        expectActive: 'page-reconcile',
        shell: 'cowork',
    });
    await verifyDeepLink(browser, {
        entry: 'erp',
        hash: '/history',
        expectHash: '#/dashboard',
        expectActive: 'page-dashboard',
        shell: 'erp',
    });
    await verifyDeepLink(browser, {
        entry: 'erp',
        hash: '/stock-card',
        expectHash: '#/stock-card',
        expectActive: 'page-stock-card',
        shell: 'erp',
    });

    return summary();
}

let browser;
(async () => {
    browser = await chromium.launch();
    const code = await run();
    await browser.close();
    process.exit(code);
})().catch((e) => {
    console.error(e);
    if (browser) browser.close().catch(() => {});
    process.exit(1);
});
