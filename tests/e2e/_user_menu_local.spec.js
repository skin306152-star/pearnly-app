// /ai 设置搬进左下角用户块 · 本地真浏览器验收(跑的是 static/dist 真实构建产物)
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**(同
// _k1b_fileconv_local.spec.js 先例)。被断言的 DOM/CSS 全部来自真构建产物,stub 只
// 兜后端响应——不是造个假对象来验自己。
//
// 验收:侧栏「设置」条目已消失;点用户块【一次】就直接出语言/账号/退出三块内容
// (不是先弹菜单再点「设置」);浮层贴左下角;点外部与 Esc 都能关。
// 截图存 tests/e2e/_artifacts/user_menu/。
//
// 起法:npx playwright test tests/e2e/_user_menu_local.spec.js
/* global window, getComputedStyle */

const { test, expect } = require('@playwright/test');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const ROOT = path.resolve(__dirname, '..', '..');
const PORT = 8987;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'user_menu');

let server;

function waitUp(url, tries = 40) {
    return new Promise((resolve, reject) => {
        const hit = (n) => {
            http.get(url, (r) => {
                r.resume();
                resolve();
            }).on('error', () => {
                if (n <= 0) return reject(new Error('server not up'));
                setTimeout(() => hit(n - 1), 150);
            });
        };
        hit(tries);
    });
}

test.beforeAll(async () => {
    server = spawn('python', ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1'], {
        cwd: ROOT,
        stdio: 'ignore',
    });
    await waitUp(`${BASE}/static/dist/ai.html`);
});

test.afterAll(() => {
    if (server) server.kill();
});

const ME = { username: 'skin', email: 'skin@example.com', tenant_name: 'skin' };

async function bootShell(page, lang = 'zh') {
    await page.route('**/api/me**', (r) =>
        r.fulfill({ contentType: 'application/json', body: JSON.stringify(ME) })
    );
    await page.route('**/api/workorder/orders**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{"orders":[]}' })
    );
    await page.route('**/api/**', (r) => {
        const url = r.request().url();
        if (url.includes('/api/me') || url.includes('/api/workorder/orders')) return r.fallback();
        return r.fulfill({ contentType: 'application/json', body: '{}' });
    });
    await page.addInitScript(
        ([l]) => {
            window.localStorage.setItem('mrpilot_token_ai', 'tok-usermenu');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [lang]
    );
    await page.goto(`${BASE}/static/dist/ai.html#/`);
    await page.waitForSelector('#footUser', { state: 'visible', timeout: 15000 });
}

test.describe('用户块浮层(本地 stub · 真构建产物)', () => {
    test('侧栏不再有「设置」条目,用户块成为唯一入口', async ({ page }) => {
        await bootShell(page);
        await expect(page.locator('#navSettings')).toHaveCount(0);
        await expect(page.locator('#v-settings')).toHaveCount(0);
        await expect(page.locator('#footUser')).toBeVisible();
    });

    test('点一次用户块 → 语言/账号/退出直接出现(不是先弹菜单再点设置)', async ({ page }) => {
        await bootShell(page);
        const popover = page.locator('#userPop');
        await expect(popover).toBeHidden();

        await page.locator('#footUser').click();
        await expect(popover).toBeVisible();

        // 一次点击后三块内容必须【已经在】浮层里——中间若插了一层「设置」菜单项,
        // 这三条会全落空,这正是本条要钉死的东西。
        await expect(popover.locator('#stLangSeg .vt-btn')).toHaveCount(4);
        await expect(popover.locator('.wosum .cell')).toHaveCount(2);
        await expect(popover.locator('[data-action="settings-logout"]')).toBeVisible();

        // 语言按钮/账号值不是原始 i18n key,也不是空壳
        const langLabels = await popover.locator('#stLangSeg .vt-btn').allInnerTexts();
        expect(langLabels.join('')).not.toContain('settings_lang_');
        expect(langLabels.every((t) => t.trim().length > 0)).toBe(true);
        await expect(popover.locator('.wosum .cell .v').first()).toContainText('skin@example.com');

        const st = await popover.evaluate((el) => {
            const s = getComputedStyle(el);
            return { display: s.display, visibility: s.visibility };
        });
        expect(st.display).not.toBe('none');
        expect(st.visibility).toBe('visible');

        await page.screenshot({ path: path.join(ARTIFACT_DIR, '01-open-zh.png'), fullPage: false });
    });

    test('浮层贴在左下角用户块上方,没被视口切掉', async ({ page }) => {
        await bootShell(page);
        await page.locator('#footUser').click();
        await expect(page.locator('#userPop')).toBeVisible();

        const pop = await page.locator('#userPop').boundingBox();
        const foot = await page.locator('#footUser').boundingBox();
        const vp = page.viewportSize();

        expect(pop.width, '浮层得有实际宽度').toBeGreaterThan(150);
        expect(pop.height, '浮层得有实际高度').toBeGreaterThan(100);
        expect(pop.x, '贴左边').toBeLessThan(60);
        expect(pop.y, '不能被视口顶切掉').toBeGreaterThanOrEqual(0);
        expect(pop.y + pop.height, '在用户块之上').toBeLessThanOrEqual(foot.y + 2);
        expect(pop.y + pop.height, '不能溢出视口底').toBeLessThanOrEqual(vp.height);
    });

    test('点外部关闭 · Esc 关闭', async ({ page }) => {
        await bootShell(page);
        const popover = page.locator('#userPop');

        await page.locator('#footUser').click();
        await expect(popover).toBeVisible();
        // 坐标要落在浮层【外面】:浮层宽 300 贴左下,故往右上角点(早先点 .main 的
        // {40,300} 正好被浮层盖住,测的是"点浮层自己",过不了才发现)。
        const box = await popover.boundingBox();
        await page.mouse.click(box.x + box.width + 200, 80);
        await expect(popover).toBeHidden();

        await page.locator('#footUser').click();
        await expect(popover).toBeVisible();
        await page.keyboard.press('Escape');
        await expect(popover).toBeHidden();
    });

    // 每语一个独立 test = 每次一张干净的 page:同一个 page 反复 bootShell 会把
    // page.route 的 stub 一层层叠上去,后果不可预期(早先写成循环,后两语必挂)。
    for (const lang of ['th', 'en', 'ja']) {
        test(`${lang} 不露原始 key`, async ({ page }) => {
            await bootShell(page, lang);
            await page.locator('#footUser').click();
            await expect(page.locator('#userPop')).toBeVisible();
            // 打开先渲加载骨架(无文案),等真内容落地再读文本——否则读到的是骨架,
            // 断言的是个瞬态,时快时慢地假红/假绿。
            await expect(page.locator('#userPop #stLangSeg')).toBeVisible();
            const text = await page.locator('#userPop').innerText();
            expect(text, `${lang} 漏了翻译`).not.toContain('settings_');
            expect(text.trim().length).toBeGreaterThan(10);
            await page.screenshot({
                path: path.join(ARTIFACT_DIR, `02-open-${lang}.png`),
                fullPage: false,
            });
        });
    }
});
