// UI1 · /ai 设计令牌升级(赤陶橙+动效)+ 四处做工修复 · 本地 stub 真浏览器验收
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**(同
// _navclose_verify.spec.js 先例,自起服务不依赖外部 server)。验收(派单 UI-1 硬门 4):
//   ① focus-visible 柔环 getComputedStyle 命中 --acc(#c2683f = rgb(194, 104, 63))
//   ② 矩阵冻结列实底非透明 + 横滚不透字 + --sh-pin 投影
//   ③ 顶级页面包屑无「工作台 /」前缀;真下级(档案页)保留真上级链
//   ④ 左下角文本 == 用户名(/api/me),不含「Earn」
//   ⑤ 工作台无统计大卡残留(.stat=0),摘要条 pill 在场
//   ⑥ 390×844 无横向溢出;⑦ reduced-motion 兜底未被绕过;⑧ 弹窗打开态
// 截图存 tests/e2e/_artifacts/ui1/(1280×900 + 390×844 双端)。
//
// 起法:npx playwright test tests/e2e/_ui1_design_tokens_verify.spec.js
/* global window, document */

const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8986;
const BASE = `http://127.0.0.1:${PORT}`;
const PAGE = `${BASE}/static/dist/ai.html`;
const ART = path.join(__dirname, '_artifacts', 'ui1');

// ai-theme.css 令牌逐字节抄自 UI-Canon-v5;E2E 用换算后的 rgb 断言 computed style。
const ACC_RGB = 'rgb(194, 104, 63)'; // --acc #c2683f
const ACC_SOFT_RGB = 'rgb(246, 230, 221)'; // --acc-soft #f6e6dd

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT);
});

test.afterAll(() => {
    localServer.stop(server);
});

const MATRIX = {
    period: '2569-06',
    clients: [
        {
            id: 1,
            name: 'Sister Makeup',
            tax_id: '1234567890123',
            missing_order: false,
            profile_completeness: 0.5,
        },
        {
            id: 2,
            name: 'โรงน้ำแข็งเจริญ จำกัด',
            tax_id: '9876543210987',
            missing_order: true,
            profile_completeness: 1.0,
        },
    ],
    obligation_codes: ['pp30', 'pnd1', 'pnd3', 'pnd53', 'pp36', 'sso'],
    obligation_labels: {
        pp30: { zh: '增值税申报(PP30)' },
        pnd1: { zh: '预扣税 PND1' },
        pnd3: { zh: '预扣税 PND3' },
        pnd53: { zh: '预扣税 PND53' },
        pp36: { zh: 'PP36' },
        sso: { zh: '社保' },
    },
    cells: [
        {
            client_id: 1,
            obligation_code: 'pp30',
            obligation_status: 'due',
            order_status: 'running',
            work_order_id: 'wo-1',
            due_paper: null,
            due_efiling: null,
            badge: 'in_progress',
        },
        {
            client_id: 1,
            obligation_code: 'pnd1',
            obligation_status: 'due',
            order_status: null,
            work_order_id: null,
            due_paper: null,
            due_efiling: null,
            badge: 'missing_materials',
        },
    ],
};

function fulfillJson(route, body, status = 200) {
    return route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
}

async function boot(page, { lang = 'zh', hash = '#/' } = {}) {
    await page.route('**/api/**', (route) => {
        const p = new URL(route.request().url()).pathname;
        if (p === '/api/workorder/orders') return fulfillJson(route, { orders: [] });
        if (p === '/api/me') {
            return fulfillJson(route, { username: 'somchai-acct', email: 'somchai@firm.example' });
        }
        if (p === '/api/tax-profile/matrix') return fulfillJson(route, MATRIX);
        if (p === '/api/workspace/clients') {
            return fulfillJson(route, { clients: MATRIX.clients });
        }
        if (p === '/api/workspace/clients/can-create') {
            return fulfillJson(route, { allowed: true });
        }
        if (p === '/api/workorder/review-queue') {
            return fulfillJson(route, {
                period: null,
                clients: [],
                counts: { clients: 0, orders: 0, flagged: 0 },
            });
        }
        if (p === '/api/ai/client-pool') return fulfillJson(route, { groups: [] });
        return fulfillJson(route, {});
    });
    await page.addInitScript(
        ([l]) => {
            window.localStorage.setItem('mrpilot_token_ai', 'tok-ui1');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [lang]
    );
    await page.goto(PAGE + hash);
    await page.waitForSelector('.shell', { timeout: 15000 });
}

async function noHorizontalOverflow(page) {
    return page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth <= 1
    );
}

test.describe('UI1 · 设计令牌 + 四处做工修复(本地 stub 真浏览器)', () => {
    test('工作台:统计大卡撤干净,摘要条 pill 带真数 + 账期', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await boot(page);
        await page.waitForSelector('.mx-table', { timeout: 15000 });

        await expect(page.locator('.stat')).toHaveCount(0);
        await expect(page.locator('.sum-pill:visible')).toHaveCount(4);
        await expect(page.locator('#statClientsV')).toHaveText('2');
        await expect(page.locator('#sumPeriodV')).toHaveText('2569-06');
        await page.screenshot({ path: path.join(ART, '01-dashboard-1280.png'), fullPage: true });

        await page.setViewportSize({ width: 390, height: 844 });
        expect(await noHorizontalOverflow(page)).toBe(true);
        await page.screenshot({ path: path.join(ART, '01-dashboard-390.png'), fullPage: true });
    });

    test('focus-visible 柔环:键盘聚焦命中 --acc 赤陶橙', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await boot(page);
        await page.waitForSelector('.mx-table', { timeout: 15000 });

        // 键盘 Tab 走到视图切换按钮(page.focus 不稳定触发 :focus-visible,真按键才算数)
        let focusedId = '';
        for (let i = 0; i < 25 && focusedId !== 'vtMatrix'; i++) {
            await page.keyboard.press('Tab');
            focusedId = await page.evaluate(() => (document.activeElement || {}).id || '');
        }
        expect(focusedId).toBe('vtMatrix');
        const ringShadow = await page.evaluate(
            () => window.getComputedStyle(document.activeElement).boxShadow
        );
        console.log('UI1_FOCUS_RING=' + ringShadow);
        expect(ringShadow).toContain(ACC_RGB);
        expect(ringShadow).toContain(ACC_SOFT_RGB);

        // 搜索框:环画在胶囊容器上(输入框本体无边框)。box-shadow 有 120ms 过渡,
        // 聚焦后轮询到终值再断言,不抓中间帧。
        await page.focus('#searchInput');
        await expect
            .poll(() =>
                page.evaluate(
                    () => window.getComputedStyle(document.querySelector('.search')).boxShadow
                )
            )
            .toContain(ACC_SOFT_RGB);
        await page.screenshot({ path: path.join(ART, '02-focus-ring.png') });
    });

    test('矩阵冻结列:实底非透明 + sh-pin 投影 + 横滚不透字', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await boot(page);
        await page.waitForSelector('.mx-table', { timeout: 15000 });

        await page.evaluate(() => {
            document.querySelector('.mx-scroll').scrollLeft = 240;
        });
        const cellStyle = await page.evaluate(() => {
            const cell = document.querySelector('.mx-table tbody .mx-namecell');
            const head = document.querySelector('.mx-table thead .mx-namecell');
            const cs = window.getComputedStyle(cell);
            const hs = window.getComputedStyle(head);
            return {
                cellBg: cs.backgroundColor,
                cellShadow: cs.boxShadow,
                cellSticky: cs.position,
                headBg: hs.backgroundColor,
            };
        });
        console.log('UI1_PINNED_COL=' + JSON.stringify(cellStyle));
        expect(cellStyle.cellSticky).toBe('sticky');
        expect(cellStyle.cellBg).not.toBe('rgba(0, 0, 0, 0)');
        expect(cellStyle.headBg).not.toBe('rgba(0, 0, 0, 0)');
        expect(cellStyle.cellShadow).not.toBe('none');
        await page.screenshot({ path: path.join(ART, '03-pinned-col-scrolled.png') });
    });

    test('面包屑修真:顶级栏目无「工作台 /」前缀,档案页链回真上级', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await boot(page);
        await page.waitForSelector('.mx-table', { timeout: 15000 });
        const dashCrumb = (await page.locator('#crumb').innerText()).trim();
        expect(dashCrumb).toBe('工作台');

        for (const [hash, label] of [
            ['#/pool', '待我处理'],
            ['#/clients', '客户'],
            ['#/reports', '报表'],
            ['#/settings', '设置'],
        ]) {
            await page.evaluate((h) => {
                window.location.hash = h;
            }, hash);
            await expect(page.locator('#crumb')).toContainText(label);
            const text = (await page.locator('#crumb').innerText()).trim();
            expect(text).not.toContain('/');
            expect(text).not.toContain('工作台');
        }

        // 真下级:单客户档案页保留上级链,且链指向客户目录(不是工作台)
        await page.evaluate(() => {
            window.location.hash = '#/clients/1/profile';
        });
        await expect(page.locator('#crumb')).toContainText('/');
        await expect(page.locator('#crumb a')).toHaveText('客户');
        await page.click('#crumb a');
        await expect(page).toHaveURL(/#\/clients$/);
    });

    test('左下角=登录用户名(/api/me),不含 Earn/邀请字样', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await boot(page);
        await expect(page.locator('#footName')).toHaveText('somchai-acct', { timeout: 10000 });
        await expect(page.locator('#footAv')).toHaveText('S');
        const footText = await page.locator('#footUser').innerText();
        expect(footText).not.toContain('Earn');
        expect(footText).not.toContain('邀请');
        expect(footText).not.toContain('Pearnly');
        await page.screenshot({ path: path.join(ART, '04-foot-user.png') });
    });

    test('客户列表分层:名/税号/完成度环/义务计数标签/箭头,手机端收列', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await boot(page, { hash: '#/clients' });
        await page.waitForSelector('#clientsBody .cl-list', { timeout: 15000 });

        const row = page.locator('#clientsBody .cl-row').first();
        await expect(row.locator('.cl-name')).toHaveText('Sister Makeup');
        await expect(row.locator('.cl-taxid')).toHaveText('1234567890123');
        await expect(row.locator('.cl-prog')).toContainText('50%');
        await expect(row.locator('.cl-ring')).toBeVisible();
        await expect(row.locator('.cl-obl')).toContainText('2');
        await expect(row.locator('.cl-arrow')).toBeVisible();
        // 义务不再平铺逐义务徽章(v5 §六):一行至多一枚计数 chip
        expect(await row.locator('.chip').count()).toBeLessThanOrEqual(1);
        await page.screenshot({ path: path.join(ART, '05-clients-1280.png'), fullPage: true });

        await page.setViewportSize({ width: 390, height: 844 });
        await expect(row.locator('.cl-taxid')).toBeHidden();
        await expect(row.locator('.cl-prog')).toBeHidden();
        await expect(row.locator('.cl-name')).toBeVisible();
        await expect(row.locator('.cl-obl')).toBeVisible();
        expect(await noHorizontalOverflow(page)).toBe(true);
        await page.screenshot({ path: path.join(ART, '05-clients-390.png'), fullPage: true });

        // 整行可点进档案页
        await row.click();
        await expect(page).toHaveURL(/#\/clients\/1\/profile$/);
    });

    test('待我处理:面包屑直显栏目名,两端截图', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await boot(page, { hash: '#/pool' });
        await page.waitForSelector('#v-pool.on', { timeout: 15000 });
        const crumb = (await page.locator('#crumb').innerText()).trim();
        expect(crumb).toBe('待我处理');
        await page.screenshot({ path: path.join(ART, '06-pool-1280.png'), fullPage: true });

        await page.setViewportSize({ width: 390, height: 844 });
        expect(await noHorizontalOverflow(page)).toBe(true);
        await page.screenshot({ path: path.join(ART, '06-pool-390.png'), fullPage: true });
    });

    test('弹窗打开态:pkg-mask 通用外壳可见 + Esc 关闭,两端截图', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await boot(page, { hash: '#/clients' });
        await page.waitForSelector('#clientsNewBtn', { state: 'visible', timeout: 15000 });
        await page.click('#clientsNewBtn');
        await expect(page.locator('.pkg-mask.on')).toBeVisible();
        await expect(page.locator('.pkg-modal')).toBeVisible();
        // 进场动画 240ms,轮询到淡入完成(终值 opacity=1)再截图。
        await expect
            .poll(() =>
                page.evaluate(
                    () => window.getComputedStyle(document.querySelector('.pkg-mask.on')).opacity
                )
            )
            .toBe('1');
        await page.screenshot({ path: path.join(ART, '07-modal-1280.png') });

        await page.setViewportSize({ width: 390, height: 844 });
        await expect(page.locator('.pkg-modal')).toBeVisible();
        expect(await noHorizontalOverflow(page)).toBe(true);
        await page.screenshot({ path: path.join(ART, '07-modal-390.png') });

        await page.keyboard.press('Escape');
        await expect(page.locator('.pkg-mask')).toHaveCount(0);
    });

    test('reduced-motion 兜底:过渡/动画全灭,弹窗照常可用', async ({ page }) => {
        await page.emulateMedia({ reducedMotion: 'reduce' });
        await page.setViewportSize({ width: 1280, height: 900 });
        await boot(page, { hash: '#/clients' });
        await page.waitForSelector('#clientsNewBtn', { state: 'visible', timeout: 15000 });

        const btnDur = await page.evaluate(() => {
            const el = document.querySelector('.btn');
            return window.getComputedStyle(el).transitionDuration;
        });
        console.log('UI1_REDUCED_MOTION_BTN_DUR=' + btnDur);
        expect(btnDur.split(',').every((d) => parseFloat(d) === 0)).toBe(true);

        await page.click('#clientsNewBtn');
        await expect(page.locator('.pkg-modal')).toBeVisible();
        const animName = await page.evaluate(
            () => window.getComputedStyle(document.querySelector('.pkg-mask.on')).animationName
        );
        expect(animName).toBe('none');
        await page.screenshot({ path: path.join(ART, '08-reduced-motion-modal.png') });
    });

    for (const lang of ['th', 'en', 'ja']) {
        test(`四语(${lang}):义务计数标签/面包屑非原始 key`, async ({ page }) => {
            await boot(page, { lang, hash: '#/clients' });
            await page.waitForSelector('#clientsBody .cl-list', { timeout: 15000 });
            const oblText = await page.locator('.cl-obl').first().innerText();
            console.log(`UI1_LANG_${lang}_OBL=` + oblText);
            expect(oblText).not.toContain('clients_obligations_n');
            expect(oblText).toContain('2');

            await page.evaluate(() => {
                window.location.hash = '#/clients/1/profile';
            });
            const crumbText = (await page.locator('#crumb').innerText()).trim();
            expect(crumbText).not.toContain('crumb_archive');
            expect(crumbText).toContain('/');
        });
    }
});
