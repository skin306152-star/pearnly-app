// E2E 真浏览器验收(2026-08-27 · Earn 超管 /admin/erp ERP 邀请页)· 只新增本文件与截图,不改任何源码/测试/dist。
//
// 验收目标(对应 .claude/skills/verification → 截图范式:isVisible + getComputedStyle,输入用 keyboard.type):
//   1. /admin/erp 侧栏「ERP 邀请」与页面都可见(#page-admin-erp.active + nav-item active)。
//   2. overview 名单 tenant-first 信息渲染:tenant 行显示 owner 用户名 + 公司名;user 行显示用户名;
//      unknown 行显示失联占位词。期望值从页面真词典(window.ADMIN_I18N)取,脚本不注入任何词典。
//   3. 已有账号邀请:POST /api/admin/erp/invite 的 payload 精确(仅 username_or_email,无 password 字段),
//      成功走后刷新(overview 重拉一次,名单新增该账号)。
//   4. 创建新账号:一次性密码展示(#adm-erp-pwd-box visible + 值 + 归属账号行)+ 复制按钮把密码写进剪贴板。
//   5. 撤销必须经过确认弹窗(#adm-confirm-modal),取消不发请求;确认才 POST subject_id,成功后刷新。
//   6. 没有 ERP 重置密码功能(页面无 reset 元素/按钮,会话期间未发出 reset-password 请求)。
//   7. 中文/泰文至少切换显示(页面标题 + 侧栏标签 + 语言属性)。
//
// 对端 = 本地已起的真实 app。网络 API 用 page.route 精确桩(只桩 /api/**,静态资源走真实 server)。
// 只读源码与导航清洗;nth/first/last 一律不用(点选必唯一定位)。
//
// 跑法:node scripts/_erp_admin_invite_verify.cjs   (失败 exit 非零)
/* eslint-disable no-undef */
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const BASE = 'http://127.0.0.1:8765';
const ROOT = path.resolve(__dirname, '..');
const ART = path.join(ROOT, 'tests', 'e2e', '_artifacts', 'erp-admin-invite');

const DESKTOP = { width: 1280, height: 900 };
const MOBILE = { width: 390, height: 844 };

// 桩的超管身份(/api/me 要求 is_super_admin,否则 admin.js 会把页面甩回 /earn)。
const ME = {
    id: 'admin1',
    username: 'superadmin',
    email: 'super@pearnly.com',
    role: 'super_admin',
    is_super_admin: true,
    tenant_role: 'owner',
    company_name: 'Pearnly Admin',
};

const CREATE_PWD = 'A1b2C3d4E5f6G7h8';

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

// 有状态 /api/** 桩:invite 已有账号 → 名单新增;create → 名单新增 + 回一次性密码;revoke → 名单剔除。
// 这样「成功后刷新」才真的可判别(列表内容随刷新变化),而不是拿同一份静态数据比两次。
function makeStub() {
    const net = { overview: 0, invite: [], revoke: [], resetSeen: 0 };
    const knownExisting = new Set(['acmeowner', 'solo_member', 'boss2']);
    const rows = [
        {
            subject_id: 't1',
            joined_at: '2026-08-27T09:30:00',
            invited: true,
            subject_type: 'tenant',
            username: 'acmeowner',
            email: 'owner@acme.com',
            company_name: 'Acme Co Ltd',
        },
        {
            subject_id: 'u2',
            joined_at: '2026-08-26T11:00:00',
            invited: true,
            subject_type: 'user',
            username: 'solo_member',
            email: '',
            company_name: '',
        },
        {
            subject_id: 'u9',
            joined_at: null,
            invited: true,
            subject_type: 'unknown',
            username: '',
            email: '',
            company_name: '',
        },
    ];
    const EXISTING = {
        boss2: {
            subject_id: 't2',
            joined_at: '2026-08-27T12:00:00',
            invited: true,
            subject_type: 'tenant',
            username: 'boss2',
            email: 'boss@auto.com',
            company_name: 'Boss Auto Co',
        },
    };

    const handler = (route) => {
        const url = new URL(route.request().url());
        const p = url.pathname;
        const method = route.request().method();

        if (p === '/api/me' && method === 'GET') return route.fulfill(json(ME));
        if (p.includes('erp/reset-password')) {
            net.resetSeen++;
            return route.fulfill(json({ ok: true }));
        }
        if (p === '/api/admin/erp/overview' && method === 'GET') {
            net.overview++;
            return route.fulfill(
                json({
                    flag: {
                        enabled: true,
                        rollout: 'allowlist',
                        updated_at: '2026-08-27T10:00:00',
                    },
                    allowlist: rows,
                })
            );
        }
        if (p === '/api/admin/erp/invite' && method === 'POST') {
            const body = route.request().postDataJSON() || {};
            net.invite.push(body);
            const who = String(body.username_or_email || '').trim();
            if (!knownExisting.has(who)) {
                // 建号:把 @ 前缀当用户名 + 顺手落 email;名单追加,响应回一次性密码。
                const user = who.split('@')[0].trim() || 'erp-portal';
                if (!rows.some((r) => r.username === user)) {
                    rows.push({
                        subject_id: 'tnew' + net.invite.length,
                        joined_at: '2026-08-27T13:00:00',
                        invited: true,
                        subject_type: 'tenant',
                        username: user,
                        email: who,
                        company_name: user,
                    });
                }
                return route.fulfill(
                    json({
                        ok: true,
                        created_account: true,
                        subject_id: 'tnew' + net.invite.length,
                        username: user,
                        initial_password: CREATE_PWD,
                    })
                );
            }
            // 已有账号:按判据加名单(新增一行可见),响应 created_account:false。
            const ex = EXISTING[who] || {
                subject_id: 't2',
                joined_at: '2026-08-27T12:00:00',
                invited: true,
                subject_type: 'tenant',
                username: who,
                email: who + '@x.com',
                company_name: 'Co ' + who,
            };
            if (!rows.some((r) => r.subject_id === ex.subject_id)) rows.push(ex);
            return route.fulfill(
                json({
                    ok: true,
                    created_account: false,
                    subject_id: ex.subject_id,
                    username: ex.username,
                })
            );
        }
        if (p === '/api/admin/erp/revoke' && method === 'POST') {
            const body = route.request().postDataJSON() || {};
            net.revoke.push(body);
            const idx = rows.findIndex((r) => r.subject_id === body.subject_id);
            if (idx >= 0) rows.splice(idx, 1);
            return route.fulfill(json({ ok: true }));
        }
        // 语言切换会触发 _renderCostPage()(角标页重拉),给安全的空形状,别让异步 reject 污染 pageerror。
        if (p === '/api/admin/cost/overview')
            return route.fulfill(json({ today: {}, month: {}, total: {}, engines: [] }));
        if (p === '/api/admin/cost/by_user') return route.fulfill(json({ users: [] }));
        if (p === '/api/admin/cost/daily_trend')
            return route.fulfill(json({ days: [], by_engine: {} }));
        if (p === '/api/admin/credits/overview') return route.fulfill(json({}));
        if (p === '/api/admin/credits/tenants') return route.fulfill(json({ tenants: [] }));
        return route.fulfill(json({}));
    };
    return { net, handler };
}

// 起一个已登录超管、停在 /admin/erp 的 page;返回 {ctx,page,net,pageerrs}。
async function boot(browser, { viewport }) {
    const stub = makeStub();
    const ctx = await browser.newContext({ viewport });
    const page = await ctx.newPage();
    await page.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'tok');
        localStorage.setItem('mrpilot_lang', 'zh');
        // 记录复制按钮真正写入剪贴板的文本(规避无头环境剪贴板不可用;仅记录写入,不污染页面词典)。
        window.__clipboardWrites = [];
        try {
            if (!navigator.clipboard) navigator.clipboard = {};
            navigator.clipboard.writeText = (t) => {
                window.__clipboardWrites.push(String(t));
                return Promise.resolve();
            };
        } catch (_) {}
    });
    await page.route('**/api/**', stub.handler);
    const pageerrs = [];
    page.on('pageerror', (e) => pageerrs.push(String(e)));
    await page.goto(BASE + '/admin/erp', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#adm-erp-list .adm-ai-list-row', { timeout: 15000 });
    await page.waitForTimeout(600);
    return { ctx, page, net: stub.net, pageerrs };
}

const shot = (page, name) => page.screenshot({ path: path.join(ART, name) });

// 从页面真词典取词(只读,不注入)。
function dictGet(page, lang, key) {
    return page.evaluate(
        ([l, k]) => (window.ADMIN_I18N && window.ADMIN_I18N[l] && window.ADMIN_I18N[l][k]) || '',
        [lang, key]
    );
}

// 页面上当前生效的语言(admin.js 落在 document.documentElement.lang)。
function pageLang(page) {
    return page.evaluate(() => document.documentElement.lang);
}

// 名单行(全量读,不做按位置点击)。
function listRows(page) {
    return page.evaluate(() =>
        [...document.querySelectorAll('#adm-erp-list .adm-ai-list-row')].map((row) => {
            const name = row.querySelector('.adm-ai-list-name');
            const meta = row.querySelector('.adm-ai-list-meta');
            const revoke = row.querySelector('[data-adm-erp-revoke]');
            return {
                name: name ? name.textContent.trim() : '',
                meta: meta ? meta.textContent.trim() : '',
                subject: revoke ? revoke.getAttribute('data-adm-erp-revoke') : null,
            };
        })
    );
}

async function run(browser) {
    fs.mkdirSync(ART, { recursive: true });

    // 预检:本地 app 与 admin 静态资源可达。
    const up = await fetch(BASE + '/admin/erp')
        .then((r) => r.ok)
        .catch(() => false);
    const jsUp = await fetch(BASE + '/static/admin/admin.js?v=0')
        .then((r) => r.ok)
        .catch(() => false);
    if (!up || !jsUp) {
        console.error(`本地 app 不在 ${BASE}(或 /static/admin/admin.js 不可达)—— 起好后重跑。`);
        return process.exit(1);
    }

    // ---- 桌面:主验收流 ----
    const { ctx, page, net, pageerrs } = await boot(browser, { viewport: DESKTOP });

    // 侧栏 + 页面可见
    const nav = await page.evaluate(() => {
        const item = document.querySelector('.admin-layout-nav-item[data-admin-route="erp"]');
        const pg = document.getElementById('page-admin-erp');
        const cs = pg ? getComputedStyle(pg) : null;
        const box = pg ? pg.getBoundingClientRect() : null;
        return {
            navExists: !!item,
            navActive: !!(item && item.classList.contains('active')),
            navVisible: item
                ? item.offsetParent !== null && getComputedStyle(item).display !== 'none'
                : false,
            navLabel:
                item && item.querySelector('span[data-i18n="adm-sidebar-erp"]')
                    ? item.querySelector('span[data-i18n="adm-sidebar-erp"]').textContent.trim()
                    : '',
            pageActive: !!(pg && pg.classList.contains('active')),
            pageDisplay: cs ? cs.display : null,
            pageHasBox: !!(box && box.width > 0 && box.height > 0),
        };
    });
    chk(
        '/admin/erp 侧栏 ERP 邀请项存在且激活',
        nav.navExists && nav.navActive,
        'active=' + nav.navActive
    );
    chk('/admin/erp 侧栏 ERP 邀请项可见', nav.navVisible, nav.navLabel);
    chk(
        '/admin/erp 页面可见(#page-admin-erp.active + display!=none + 有盒子)',
        nav.pageActive && nav.pageDisplay !== 'none' && nav.pageHasBox,
        `display=${nav.pageDisplay}`
    );
    chk(
        '/admin/erp 页面可 Playwright isVisible',
        await page.locator('#page-admin-erp').isVisible()
    );
    chk(
        '侧栏标签 ERP 邀请 从真词典取到',
        nav.navLabel === (await dictGet(page, 'zh', 'adm-sidebar-erp')),
        nav.navLabel
    );

    // 页面头 + 邀请区头部
    const head = await page.evaluate(() => {
        const title = document.querySelector('#page-admin-erp .page-title');
        const sub = document.querySelector('#page-admin-erp .page-subtitle');
        const inviteBtn = document.getElementById('adm-erp-invite-btn');
        const input = document.getElementById('adm-erp-invite-input');
        const pw = document.getElementById('adm-erp-invite-password');
        return {
            title: title ? title.textContent.trim() : '',
            sub: sub ? sub.textContent.trim() : '',
            inviteBtn: inviteBtn ? inviteBtn.textContent.trim() : '',
            btnVisible: inviteBtn ? getComputedStyle(inviteBtn).display !== 'none' : false,
            inputPh: input ? input.getAttribute('placeholder') : '',
            pwPh: pw ? pw.getAttribute('placeholder') : '',
            listTitle:
                (document.querySelector('#page-admin-erp .cost-section-head h3') || {})
                    .textContent || '',
        };
    });
    chk(
        '页面标题 = 词典 adm-erp-title',
        head.title === (await dictGet(page, 'zh', 'adm-erp-title')),
        head.title
    );
    chk('页面副标题非空', typeof head.sub === 'string' && head.sub.length > 0, head.sub);
    chk(
        '邀请按钮文字 = 词典 adm-erp-invite-btn',
        head.inviteBtn === (await dictGet(page, 'zh', 'adm-erp-invite-btn')),
        head.inviteBtn
    );
    chk('邀请按钮可见', head.btnVisible);
    chk(
        '用户名输入框 placeholder = 词典 adm-erp-invite-ph',
        head.inputPh === (await dictGet(page, 'zh', 'adm-erp-invite-ph')),
        head.inputPh
    );
    chk(
        '密码输入框 placeholder = 词典 adm-erp-invite-pwd-ph',
        head.pwPh === (await dictGet(page, 'zh', 'adm-erp-invite-pwd-ph')),
        head.pwPh
    );

    // overview:邀请名单是唯一准入,不受旧总闸字段影响;名单 tenant-first 信息渲染。
    const flagZh = await dictGet(page, 'zh', 'adm-erp-flag-on');
    const rollZh = await dictGet(page, 'zh', 'adm-erp-flag-rollout-allowlist');
    const flagText = await page.locator('#adm-erp-flag-line').textContent();
    chk('开通方式 = 邀请即生效 · 仅邀请名单内', flagText === flagZh + ' · ' + rollZh, flagText);

    const rows0 = await listRows(page);
    chk('overview 名单初始 3 行', rows0.length === 3, '实际 ' + rows0.length);
    // tenant 行:owner 用户名 + 公司名(B.E. 日期由页面自己的 window._adminDate 算,不脚本复制)。
    const t1Meta = await page.evaluate(() => {
        const who = window._adminDate('2026-08-27T09:30:00', true);
        return ['Acme Co Ltd', who].join(' · ');
    });
    const t1 = rows0.find((r) => r.subject === 't1');
    chk(
        'tenant 行渲染 owner 用户名 + 公司名(tenant-first)',
        t1 && t1.name === 'acmeowner' && t1.meta === t1Meta,
        `name=${t1 && t1.name}, meta=${t1 && t1.meta}`
    );
    const u2 = rows0.find((r) => r.subject === 'u2');
    chk('user 行渲染用户名(个人套账无公司)', u2 && u2.name === 'solo_member', u2 && u2.meta);
    const u9 = rows0.find((r) => r.subject === 'u9');
    chk(
        'unknown 行渲染失联占位词(取真词典)',
        u9 && u9.name === (await dictGet(page, 'zh', 'adm-erp-list-unknown')) && u9.meta === '',
        u9 && u9.name
    );

    // 无重置密码:页面无 reset 元素/按钮,且会话期未发 reset-password 请求。
    const resetDom = await page.evaluate(() => {
        const scope = document.getElementById('page-admin-erp');
        const resetAttr = scope
            ? scope.querySelectorAll(
                  '[data-adm-erp-reset], [id*="erp-reset"], [class*="erp-reset"]'
              ).length
            : 0;
        const btnTexts = scope
            ? [...scope.querySelectorAll('button')].map((b) => b.textContent.trim())
            : [];
        return { resetAttr, btnTexts };
    });
    const resetZh = await dictGet(page, 'zh', 'adm-dms-reset-btn');
    const resetTh = await dictGet(page, 'th', 'adm-dms-reset-btn');
    chk(
        'ERP 页无任何 reset 元素/按钮(zh/th 都查)',
        resetDom.resetAttr === 0 &&
            !resetDom.btnTexts.includes(resetZh) &&
            !resetDom.btnTexts.includes(resetTh),
        `attrs=${resetDom.resetAttr}, btns=${resetDom.btnTexts.join('|')}`
    );
    chk(
        '会话期间无 /api/admin/erp/reset-password 请求',
        net.resetSeen === 0,
        'seen=' + net.resetSeen
    );

    await shot(page, 'erp-invite-desktop.png');

    // ---- 已有账号邀请:POST payload 精确 + 成功后刷新 ----
    const ovBefore = net.overview;
    await page.click('#adm-erp-invite-input');
    await page.keyboard.type('boss2');
    const typed = await page.evaluate(() => ({
        activeId: document.activeElement ? document.activeElement.id : null,
        val: document.getElementById('adm-erp-invite-input')
            ? document.getElementById('adm-erp-invite-input').value
            : null,
    }));
    chk(
        '邀请输入框获焦且收下键盘输入',
        typed.activeId === 'adm-erp-invite-input' && typed.val === 'boss2',
        `active=${typed.activeId}, val=${typed.val}`
    );
    await page.click('#adm-erp-invite-btn');
    await page.waitForFunction(() =>
        [...document.querySelectorAll('#adm-erp-list .adm-ai-list-name')].some(
            (e) => e.textContent.trim() === 'boss2'
        )
    );
    chk(
        '已有账号邀请 POST payload = {username_or_email} 且无 password 字段',
        net.invite.length === 1 &&
            net.invite[0].username_or_email === 'boss2' &&
            !('password' in net.invite[0]),
        JSON.stringify(net.invite[0])
    );
    chk(
        '已有账号邀请成功后刷新(overview 重拉 +1)',
        net.overview === ovBefore + 1,
        `before=${ovBefore}, after=${net.overview}`
    );
    const rowsAfterInvite = await listRows(page);
    chk(
        '刷新后名单新增 boss2(Boss Auto Co)',
        rowsAfterInvite.length === 4 &&
            !!rowsAfterInvite.find((r) => r.subject === 't2' && r.name === 'boss2')
    );
    const okToast = await dictGet(page, 'zh', 'adm-erp-invite-existing-ok');
    await page.waitForFunction(
        (t) =>
            (
                document.getElementById('admin-toast-host') || { textContent: '' }
            ).textContent.includes(t),
        okToast
    );
    chk('已有账号邀请成功 toast = 词典 adm-erp-invite-existing-ok', true, okToast);
    const cleared = await page.evaluate(() =>
        document.getElementById('adm-erp-invite-input')
            ? document.getElementById('adm-erp-invite-input').value
            : null
    );
    chk('邀请成功后输入框清空', cleared === '', 'val=' + cleared);

    // ---- 创建新账号:一次性密码展示 + 复制按钮 ----
    await page.click('#adm-erp-invite-input');
    await page.keyboard.type('newclient@example.com');
    await page.click('#adm-erp-invite-btn');
    await page.waitForFunction(() => {
        const box = document.getElementById('adm-erp-pwd-box');
        return (
            box &&
            !box.hidden &&
            (document.getElementById('adm-erp-pwd-value') || { value: '' }).value.length > 0
        );
    });
    const pwdBox = await page.evaluate(() => {
        const box = document.getElementById('adm-erp-pwd-box');
        const val = document.getElementById('adm-erp-pwd-value');
        const forLine = document.getElementById('adm-erp-pwd-for');
        const cs = box ? getComputedStyle(box) : null;
        return {
            hidden: box ? box.hidden : null,
            display: cs ? cs.display : null,
            val: val ? val.value : '',
            forLine: forLine ? forLine.textContent : '',
        };
    });
    chk(
        '创建新账号一次性密码框可见(hidden=false + display!=none)',
        pwdBox.hidden === false && pwdBox.display === 'block',
        `display=${pwdBox.display}`
    );
    chk('一次性密码值展示为后端发放值', pwdBox.val === CREATE_PWD, pwdBox.val);
    const forLabel = (await dictGet(page, 'zh', 'adm-erp-pwd-for-label')).replace(
        '{n}',
        'newclient'
    );
    chk('一次性密码归属账号行 = 账号:newclient', pwdBox.forLine === forLabel, pwdBox.forLine);
    const pageUrlAfterCreate = await page.evaluate(() => location.href);
    chk(
        '建号成功后页面保持在 /admin/erp',
        pageUrlAfterCreate.includes('/admin/erp'),
        pageUrlAfterCreate
    );
    await shot(page, 'erp-create-pwd-box-desktop.png');

    // 复制按钮:点击后剪贴板(桩)写入一次性密码 + toast。
    await page.click('#adm-erp-pwd-copy');
    const copyRes = await page.evaluate(() => ({
        writes: (window.__clipboardWrites || []).slice(),
    }));
    chk(
        '复制按钮把一次性密码写入剪贴板',
        copyRes.writes.includes(CREATE_PWD),
        JSON.stringify(copyRes.writes)
    );
    const copiedToast = await dictGet(page, 'zh', 'adm-erp-pwd-copied');
    await page.waitForFunction(
        (t) =>
            (
                document.getElementById('admin-toast-host') || { textContent: '' }
            ).textContent.includes(t),
        copiedToast
    );
    chk('复制后 toast = 词典 adm-erp-pwd-copied', true, copiedToast);

    // 关闭密码框后不再显示(轻量确认 close 也解绑值)。
    await page.click('#adm-erp-pwd-close');
    const closed = await page.evaluate(() => ({
        hidden: (document.getElementById('adm-erp-pwd-box') || {}).hidden,
        val: (document.getElementById('adm-erp-pwd-value') || { value: 'x' }).value,
    }));
    chk('「我已保存,关闭」隐藏密码框并清空值', closed.hidden === true && closed.val === '');

    // ---- 撤销:必须过确认弹窗,取消不发请求;确认才 POST subject_id ----
    await page.click('[data-adm-erp-revoke="t1"]');
    await page.waitForSelector('#adm-confirm-modal', { timeout: 5000 });
    const modalShown = await page.evaluate(() => {
        const m = document.getElementById('adm-confirm-modal');
        return !!m && getComputedStyle(m).display !== 'none';
    });
    chk(
        '点撤销先弹确认弹窗(未发请求)',
        modalShown && net.revoke.length === 0,
        'revoke=' + net.revoke.length
    );
    const confirmTitle = await page.evaluate(() => {
        const t = document.querySelector('#adm-confirm-modal .cpw-forgot-title');
        return t ? t.textContent.trim() : '';
    });
    chk(
        '确认弹窗标题 = 词典 adm-erp-revoke-btn',
        confirmTitle === (await dictGet(page, 'zh', 'adm-erp-revoke-btn')),
        confirmTitle
    );
    await page.waitForTimeout(200); // 等待 150ms 淡入动画结束，截图必须肉眼可见弹窗。
    await shot(page, 'erp-revoke-confirm-desktop.png');

    // 取消:不发请求。
    await page.click('#adm-cf-cancel');
    await page.waitForSelector('#adm-confirm-modal', { state: 'detached' });
    chk('取消关弹窗且不发 revoke 请求', net.revoke.length === 0, 'revoke=' + net.revoke.length);

    // 确认:POST subject_id,成功后刷新(t1 被剔除)。
    const ovBeforeRevoke = net.overview;
    await page.click('[data-adm-erp-revoke="t1"]');
    await page.waitForSelector('#adm-confirm-modal', { timeout: 5000 });
    await page.click('#adm-cf-ok');
    await page.waitForFunction(
        () =>
            !document.querySelector('#adm-erp-list .adm-ai-list-name') ||
            ![...document.querySelectorAll('#adm-erp-list .adm-ai-list-name')].some(
                (e) => e.textContent.trim() === 'acmeowner'
            )
    );
    chk(
        '确认后 revoke POST body = {subject_id: t1}',
        net.revoke.length === 1 && net.revoke[0].subject_id === 't1',
        JSON.stringify(net.revoke[0])
    );
    chk(
        '撤销成功后刷新(overview 重拉 +1)且名单剔除 t1',
        net.overview === ovBeforeRevoke + 1 &&
            !(await listRows(page)).some((r) => r.subject === 't1'),
        `before=${ovBeforeRevoke}, after=${net.overview}`
    );

    // ---- 中文/泰文至少切换显示 ----
    const zhTitle = await page.locator('#page-admin-erp .page-title').textContent();
    await page.click('#admin-lang-btn');
    await page.click('button[data-admin-lang="th"]');
    await page.waitForFunction(() => document.documentElement.lang === 'th');
    const thTitle = await page.locator('#page-admin-erp .page-title').textContent();
    const thExplicit = await dictGet(page, 'th', 'adm-erp-title');
    const thNav = await page
        .locator('.admin-layout-nav-item[data-admin-route="erp"] span[data-i18n="adm-sidebar-erp"]')
        .textContent();
    chk('切换泰文后 document lang=th', (await pageLang(page)) === 'th');
    chk(
        '页面标题 zh→th 且 = 词典 th adm-erp-title',
        zhTitle !== thTitle && thTitle === thExplicit && thTitle.length > 0,
        `zh=${zhTitle}, th=${thTitle}`
    );
    chk(
        '侧栏 ERP 标签切换为泰文(词典 adm-sidebar-erp)',
        thNav === (await dictGet(page, 'th', 'adm-sidebar-erp')),
        thNav
    );
    await shot(page, 'erp-invite-th-desktop.png');

    chk('桌面流程无未捕获页面错误', pageerrs.length === 0, pageerrs.slice(0, 2).join(' ; '));
    await ctx.close();

    // ---- 手机 390x844:页面与侧栏渲染 + 截图 ----
    const m = await boot(browser, { viewport: MOBILE });
    const mNav = await m.page.evaluate(() => {
        const item = document.querySelector('.admin-layout-nav-item[data-admin-route="erp"]');
        const pg = document.getElementById('page-admin-erp');
        return {
            navVisible: item
                ? item.offsetParent !== null && getComputedStyle(item).display !== 'none'
                : false,
            pageActive: !!(pg && pg.classList.contains('active')),
            inviteVisible: (() => {
                const b = document.getElementById('adm-erp-invite-btn');
                return !!b && getComputedStyle(b).display !== 'none';
            })(),
        };
    });
    chk('手机 390x844:ERP 邀请项可见', mNav.navVisible);
    chk('手机 390x844:ERP 页面 active 且邀请按钮可见', mNav.pageActive && mNav.inviteVisible);
    await shot(m.page, 'erp-invite-mobile-390.png');
    chk('手机流程无未捕获页面错误', m.pageerrs.length === 0, m.pageerrs.slice(0, 2).join(' ; '));
    await m.ctx.close();

    return summary();
}

let browser;
(async () => {
    browser = await chromium.launch();
    const code = await run(browser);
    await browser.close();
    process.exit(code);
})().catch((e) => {
    console.error(e);
    if (browser) browser.close().catch(() => {});
    process.exit(1);
});
