// 第三档 UI 走查(2026-07-30 四语双端)修完的样子 · 本地真浏览器验收,跑 static/dist 真产物
// ============================================================
// python http.server 静态服 static/dist + page.route stub /api/**(同 _board_tools_local.spec.js
// / _home_ux_fix5_local.spec.js 先例)。三个壳一份 spec:这批改动是同一件事——窄容器里
// 挤不下的真实译文,以及手机上按不准的导航。断言的选择器全部来自真实产物
// (ai-kanban-render.js / ai-shell.css / ai-clients-render.js / dms.html / src/home/*.ts),
// 几何一律 getBoundingClientRect + getComputedStyle,不看类名判死活。
//
// 钉住的六条(修前实测值写在各 test 注释里,来源 scratchpad 走查 measured.json):
//   1 看板开单钮 ja 越出卡片 2.6px           → 标签折行,整颗留在卡内
//   2 看板客户名单行硬切(泰文只剩 43%)     → 折两行
//   3 客户目录手机端名字横向切掉            → 折两行
//   4 窄轨侧栏标签切在词中间 + anchor 39px 宽 → 三行 + anchor ≥44
//   5 /dms 导航 37px 高                     → ≥44
//   6 /home 汉堡 36 / 切账套 36 / 门上退出 34 → ≥44;฿ 后一律窄空格 U+2009
//
// 起法:npx playwright test tests/e2e/_ui_tier3_local.spec.js
/* global window, document, getComputedStyle, NodeFilter */

const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8992;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'ui_tier3');
const PHONE = { width: 390, height: 844 };
const DESKTOP = { width: 1280, height: 900 };
const TAP = 44; // Canon §7 触控目标下限

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT);
});

test.afterAll(() => localServer.stop(server));

const json = (body, status = 200) => ({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
});

const PERIOD = '2569-07';
// 长名取真实形态的泰国公司抬头(บริษัท…จำกัด (มหาชน)),短名做对照——对照项不该被这批改动动到。
const LONG_TH = 'บริษัท สยามพัฒนาก่อสร้างและวิศวกรรม จำกัด (มหาชน)';
const AI_CLIENTS = [
    { id: 1, name: 'Sister Makeup Steward', tax_id: '0105567178203' },
    { id: 2, name: 'บริษัท บี', tax_id: '0994000333444' },
    { id: 3, name: LONG_TH, tax_id: '0105500000001' },
];
const ORDERS = [{ id: 'wo-2', workspace_client_id: 2, period: PERIOD, status: 'collecting' }];
const MATRIX = {
    period: PERIOD,
    clients: AI_CLIENTS.map((c) => ({ id: c.id, name: c.name, missing_order: c.id === 1 })),
    obligation_codes: ['pnd1', 'pp30'],
    obligation_labels: {
        pp30: { zh: '增值税', th: 'ภ.พ.30' },
        pnd1: { zh: '预扣税', th: 'ภ.ง.ด.1' },
    },
    cells: [
        {
            client_id: 1,
            obligation_code: 'pp30',
            badge: 'pending_order',
            due_efiling: '2599-12-31',
        },
    ],
};

async function bootAi(page, hash, lang, vp) {
    await page.setViewportSize(vp);
    // 一个 handler 分发全部 /api/**:Playwright 路由后注册先匹配,拆多条再加兜底会互相盖掉。
    await page.route('**/api/**', (r) => {
        const url = r.request().url();
        if (url.includes('/api/workorder/orders')) {
            const m = url.match(/\/api\/workorder\/orders\/([^/?]+)/);
            if (m) {
                const order = ORDERS.filter((o) => o.id === m[1])[0] || {};
                return r.fulfill(
                    json(
                        Object.assign(
                            { needs: [], blocked_reasons: [], flagged: [], numbers: {} },
                            order
                        )
                    )
                );
            }
            return r.fulfill(json({ orders: ORDERS }));
        }
        if (url.includes('/api/tax-profile/matrix')) return r.fulfill(json(MATRIX));
        if (url.includes('/api/workspace/clients')) return r.fulfill(json({ clients: AI_CLIENTS }));
        if (url.includes('/api/me')) return r.fulfill(json({ username: 'skin' }));
        return r.fulfill(json({}));
    });
    await page.addInitScript(
        ([l]) => {
            window.localStorage.setItem('mrpilot_token_ai', 'tok-tier3');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [lang]
    );
    await page.goto(`${BASE}/static/dist/ai.html#${hash}`);
}

const shot = (page, name) => page.screenshot({ path: path.join(ARTIFACT_DIR, name) });

// -webkit-box + line-clamp 的 scrollHeight 会比 clientHeight 多出个把像素(行高 9.5×1.1
// 取整),1px 不算截断;真被 clamp 掉一整行才算。
const CLAMP_SLACK = 2;

test.describe('/ai 看板卡片(1280)', () => {
    test('开单按钮整颗留在卡内 · 日文长标签靠折行不靠越界', async ({ page }) => {
        // 修前实测 ja:按钮 self 右缘 436 > 卡片右缘 433.4(父元素 overflow-x:visible,
        // 是真漏在卡外);zh/th/en 因为标签短没触发。
        await bootAi(page, '/board', 'ja', DESKTOP);
        await page.waitForSelector('#dashBody .kanban', { state: 'visible', timeout: 20000 });
        await shot(page, '01-board-ja-desktop1280.png');

        const btns = await page.locator('#dashBody .kcard .kopen .btn').evaluateAll((els) =>
            els.map((el) => {
                const b = el.getBoundingClientRect();
                const card = el.closest('.kcard').getBoundingClientRect();
                return { label: el.textContent.trim(), out: b.right - card.right, h: b.height };
            })
        );
        expect(btns.length).toBeGreaterThan(0);
        for (const b of btns) {
            expect(b.label.length, '日文标签确实是长的那条,不然这条断言没判别力').toBeGreaterThan(
                6
            );
            expect(b.out, `「${b.label}」越出卡片右缘 ${b.out}px`).toBeLessThanOrEqual(0);
        }
        // 同一颗按钮的账期下拉不许被挤没(修前它被 flex-shrink:0 的按钮压成 0 宽)。
        const sel = await page
            .locator('#dashBody .kcard .kopen .period-sel')
            .first()
            .evaluate((el) => el.getBoundingClientRect().width);
        expect(sel, '账期下拉还在,选期这一步没被按钮挤掉').toBeGreaterThan(40);
    });

    test('客户名折两行:长泰文抬头露出的比单行时多一倍', async ({ page }) => {
        // 修前实测:.kcard b 单行 nowrap+ellipsis,内容宽 134px —— LONG_TH 需 310px,
        // 只露 43%;同一家事务所里前缀相同的两家公司在板上会长得一模一样。
        await bootAi(page, '/board', 'th', DESKTOP);
        await page.waitForSelector('#dashBody .kcard b', { state: 'visible', timeout: 20000 });
        await shot(page, '02-board-th-names-desktop1280.png');

        const names = await page.locator('#dashBody .kcard b').evaluateAll((els) =>
            els.map((el) => ({
                text: el.textContent.trim(),
                scrollW: el.scrollWidth,
                clientW: el.clientWidth,
                scrollH: el.scrollHeight,
                clientH: el.clientHeight,
                clamp: getComputedStyle(el).webkitLineClamp,
                title: el.getAttribute('title'),
            }))
        );
        const long = names.filter((n) => n.text === LONG_TH)[0];
        expect(long, '长名那张卡在场').toBeTruthy();
        expect(long.clamp, '两行封顶,不让一个抬头把整列撑变形').toBe('2');
        // 横向不再溢出 = 不再是「一行砍掉」;纵向可视高度真的占了两行。
        expect(long.scrollW).toBeLessThanOrEqual(long.clientW);
        // 单行是 22px(修前实测),两行 43px —— 拿短名那行的高度当尺子,不写死数字。
        const oneLine = names.filter((n) => n.text === 'บริษัท บี')[0];
        expect(long.clientH, '可视高度真的是两行,不只是 CSS 写了').toBeGreaterThan(
            oneLine.clientH * 1.5
        );
        // 全名仍挂 title(桌面悬停兜底),超长的部分继续由 line-clamp 收省略号。
        expect(long.title).toBe(LONG_TH);

        // 短名必须整条露出来,一个像素都不许被截。
        const short = names.filter((n) => n.text === 'Sister Makeup Steward')[0];
        expect(short.scrollH - short.clientH, '普通长度的名字不该再被截').toBeLessThanOrEqual(
            CLAMP_SLACK
        );
    });
});

test.describe('/ai 窄轨侧栏(390)', () => {
    test('导航标签不再切在词中间 · 整条 anchor 是 ≥44 的触控目标', async ({ page }) => {
        // 修前实测 th:栏宽 64、标签单行可视 60px,「ตรวจสามด้านรายงานภาษีขาย」需 119px,
        // 只露一半;anchor 39×47.4,宽度不够手指按。
        await bootAi(page, '/board', 'th', PHONE);
        await page.waitForSelector('#navDash span', { state: 'visible', timeout: 20000 });
        await shot(page, '03-rail-th-mobile390.png');

        const items = await page.locator('.snav a').evaluateAll((els) =>
            els
                .filter((el) => el.offsetParent)
                .map((el) => {
                    const s = el.querySelector('span');
                    const b = el.getBoundingClientRect();
                    return {
                        text: s ? s.textContent.trim() : '',
                        w: b.width,
                        h: b.height,
                        clampedLines: s ? s.scrollHeight - s.clientHeight : 0,
                        clamp: s ? getComputedStyle(s).webkitLineClamp : null,
                    };
                })
        );
        expect(items.length, '导航项都在').toBeGreaterThanOrEqual(6);
        for (const it of items) {
            // 亚像素:headless 下 flex 行的 cross size 会落在分数上(本仓实测量到过
            // 43.999969),取整再比,不然会随机红。
            expect(Math.round(it.w), `「${it.text}」宽 ${it.w}`).toBeGreaterThanOrEqual(TAP);
            expect(Math.round(it.h), `「${it.text}」高 ${it.h}`).toBeGreaterThanOrEqual(TAP);
            expect(it.clamp, '标签三行封顶').toBe('3');
        }
        // 泰文里最长的那条仍要收省略号(64px 的轨道装不下 24 个泰文字),但除它以外
        // 一条都不许再被截 —— 修前是「除了最短的几条,长的全被砍」。
        const clipped = items.filter((it) => it.clampedLines > CLAMP_SLACK);
        expect(
            clipped.map((c) => c.text),
            '只剩最长那一条吃省略号'
        ).toEqual(['ตรวจสามด้านรายงานภาษีขาย']);

        // 标签变高 = 导航变高:底部用户块(设置入口)不许被顶出视口。
        const foot = await page
            .locator('.side .foot')
            .evaluate((el) => el.getBoundingClientRect().bottom);
        expect(foot).toBeLessThanOrEqual(PHONE.height);
    });
});

test.describe('/ai 客户目录(390)', () => {
    test('长公司名折两行,整行读得出是哪一家', async ({ page }) => {
        // 修前实测 th:.cl-name 单行可视 201px,LONG_TH 需 322px。
        await bootAi(page, '/clients', 'th', PHONE);
        await page.waitForSelector('.cl-name', { state: 'visible', timeout: 20000 });
        await shot(page, '04-clients-th-mobile390.png');

        const rows = await page.locator('.cl-name').evaluateAll((els) =>
            els.map((el) => ({
                text: el.textContent.trim(),
                scrollW: el.scrollWidth,
                clientW: el.clientWidth,
                scrollH: el.scrollHeight,
                clientH: el.clientHeight,
            }))
        );
        const long = rows.filter((r) => r.text === LONG_TH)[0];
        expect(long, '长名那行在场').toBeTruthy();
        expect(long.scrollW, '不再横向砍').toBeLessThanOrEqual(long.clientW);
        expect(long.scrollH - long.clientH, '两行放得下,没被纵向 clamp').toBeLessThanOrEqual(
            CLAMP_SLACK
        );
        const overflow = await page.evaluate(
            () => document.documentElement.scrollWidth - document.documentElement.clientWidth
        );
        expect(overflow, '折行没把整页撑横滚').toBeLessThanOrEqual(0);
    });
});

test.describe('/dms 手机端导航(390)', () => {
    test('四条导航是 ≥44 的触控目标', async ({ page }) => {
        // 修前实测:.dms-nav-item 35~37px 高。DMS 是车行操作员拿手机用的,这四条就是全部导航。
        await page.setViewportSize(PHONE);
        await page.route('**/api/**', (r) => {
            const url = r.request().url();
            if (url.includes('/api/dms/session'))
                return r.fulfill(json({ operator: 'tier3', tenant_id: 't1' }));
            if (url.includes('/api/me')) return r.fulfill(json({ username: 'tier3' }));
            return r.fulfill(json({}));
        });
        await page.addInitScript(() => {
            localStorage.setItem('mrpilot_token', 'tok-dms-tier3');
            localStorage.setItem('mrpilot_lang', 'zh');
        });
        await page.goto(`${BASE}/static/dist/dms.html`);
        await page.waitForSelector('.dms-nav-item', { state: 'visible', timeout: 20000 });
        await shot(page, '05-dms-zh-mobile390.png');

        const items = await page.locator('.dms-nav-item').evaluateAll((els) =>
            els
                .filter((el) => el.offsetParent)
                .map((el) => {
                    const b = el.getBoundingClientRect();
                    return { text: el.textContent.trim(), w: b.width, h: b.height };
                })
        );
        expect(items.length, '导航项渲染出来了').toBeGreaterThanOrEqual(3);
        for (const it of items) {
            expect(Math.round(it.h), `「${it.text}」高 ${it.h}`).toBeGreaterThanOrEqual(TAP);
        }
    });
});

const HOME_ME = { username: 'tier3', role: 'owner', is_owner: true, tenant_id: 'tier3-tenant' };
const HOME_SUBJECTS = [
    { id: 1, name: 'Sister Makeup Steward Co., Ltd.', tax_id: '0105567178203', invoice_count: 12 },
];

// 进 /home:preboot 早于 main.js 就查 token,先 addInitScript 落 localStorage;套账硬门整页
// visibility:hidden,必须真点一个主体过门(摘 class 量到的「可见」是假的)。
async function bootHome(page, vp) {
    await page.setViewportSize(vp);
    await page.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'tier3-stub-token');
        localStorage.setItem('mrpilot_lang', 'zh');
        // Keep static home.html tests on the internal full shell.
        localStorage.setItem('pearnly_entry', 'firm');
    });
    await page.route('**/api/**', (r) => {
        const p = new URL(r.request().url()).pathname;
        if (p === '/api/me/credits')
            return r.fulfill(
                json({ balance_thb: 1234.5, is_owner: true, is_billing_exempt: false })
            );
        if (p === '/api/me') return r.fulfill(json(HOME_ME));
        if (p === '/api/workspace/clients') return r.fulfill(json({ clients: HOME_SUBJECTS }));
        return r.fulfill(json({}));
    });
    await page.goto(`${BASE}/static/dist/home.html`, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#workspace-gate-root [data-wsg-pick]', { timeout: 20000 });
}

const tapBox = (loc) =>
    loc.evaluate((el) => {
        const b = el.getBoundingClientRect();
        return { w: b.width, h: b.height };
    });

test.describe('/home 手机端(390)', () => {
    test('账套门上的退出是 ≥44 的目标(成员空态下它是屏上唯一的控件)', async ({ page }) => {
        // 修前实测:.wsg-logout 84×34。
        await bootHome(page, PHONE);
        await shot(page, '06-home-gate-zh-mobile390.png');
        const box = await tapBox(page.locator('.wsg-logout'));
        expect(Math.round(box.h), `退出 ${box.h}px`).toBeGreaterThanOrEqual(TAP);
    });

    test('汉堡与切账套是 ≥44 的目标 · 桌面尺寸不受影响', async ({ page }) => {
        // 修前实测:topbar-hamburger 36×36(手机端唯一的主导航键)、wsw 180×36。
        await bootHome(page, PHONE);
        await page.locator('#workspace-gate-root [data-wsg-pick]').first().click();
        await expect(page.locator('#workspace-gate-root')).toHaveCount(0, { timeout: 20000 });
        expect(await page.evaluate(() => document.body.className)).not.toContain(
            'workspace-gate-preboot'
        );
        await shot(page, '07-home-topbar-zh-mobile390.png');

        const burger = page.locator('button.topbar-hamburger');
        await expect(burger, '汉堡在手机端是显示的').toBeVisible();
        const bb = await tapBox(burger);
        expect(Math.round(bb.w)).toBeGreaterThanOrEqual(TAP);
        expect(Math.round(bb.h)).toBeGreaterThanOrEqual(TAP);
        const wb = await tapBox(page.locator('button.wsw'));
        expect(Math.round(wb.h), `切账套 ${wb.h}px`).toBeGreaterThanOrEqual(TAP);

        // 桌面端按原尺寸不动:抬触控目标不许顺手把桌面顶栏撑高。
        await page.setViewportSize(DESKTOP);
        await page.waitForTimeout(200);
        expect(await burger.evaluate((el) => getComputedStyle(el).display)).toBe('none');
        expect(Math.round((await tapBox(page.locator('button.wsw'))).h)).toBe(36);
    });

    test('฿ 后面永远是窄空格 U+2009(逐字符按码点读,不做空白归一)', async ({ page }) => {
        // 修前实测(把 main.js 换回 HEAD 那版跑同一屏):余额是「฿ 1234.50」,฿ 后 U+0020,
        // 而同屏词典来的两处已经是 U+2009 —— 一屏两种写法。
        await bootHome(page, PHONE);
        await page.locator('#workspace-gate-root [data-wsg-pick]').first().click();
        await expect(page.locator('#workspace-gate-root')).toHaveCount(0, { timeout: 20000 });
        await page.evaluate(() => {
            window.location.hash = '#/dashboard';
        });
        await page.waitForFunction(
            () => {
                const el = document.getElementById('dash-kpi-balance');
                return el && (el.textContent || '').indexOf('฿') >= 0;
            },
            { timeout: 20000 }
        );
        await shot(page, '08-home-baht-zh-mobile390.png');

        const seen = await page.evaluate(() => {
            const counts = {};
            const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            let n;
            while ((n = w.nextNode())) {
                if (!n.parentElement || !n.parentElement.offsetParent) continue;
                const s = n.nodeValue || '';
                for (let i = 0; i < s.length; i++) {
                    if (s[i] !== '฿') continue;
                    const c = s.codePointAt(i + 1);
                    const k = c == null ? 'EOL' : 'U+' + c.toString(16).toUpperCase();
                    counts[k] = (counts[k] || 0) + 1;
                }
            }
            return counts;
        });
        // 判据自检:一个 ฿ 都没渲染出来的话下面那条断言绿得毫无意义。
        const total = Object.keys(seen).reduce((a, k) => a + seen[k], 0);
        expect(total, '这一屏真的印了泰铢符号').toBeGreaterThan(0);
        expect(Object.keys(seen).sort(), `฿ 后出现过这些码点:${JSON.stringify(seen)}`).toEqual([
            'U+2009',
        ]);
    });
});
