// /ai 设置入口从侧栏挪到左下角用户块 · 本地真浏览器验收(跑 static/dist 真构建产物)
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**(同
// _k1b_fileconv_local.spec.js 先例)。被断言的 DOM/CSS 全来自真产物,stub 只兜后端响应。
//
// 验收:侧栏「设置」条目已删;点左下角用户块 → 右侧照常渲染设置页(语言/账号/退出),
// 页面本身没搬家、没变成浮层。截图存 tests/e2e/_artifacts/settings_entry/。
//
// 起法:npx playwright test tests/e2e/_settings_entry_local.spec.js
/* global window, getComputedStyle */

const { test, expect } = require('@playwright/test');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const ROOT = path.resolve(__dirname, '..', '..');
const PORT = 8988;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'settings_entry');

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

async function boot(page, lang = 'zh') {
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
            window.localStorage.setItem('mrpilot_token_ai', 'tok-setentry');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [lang]
    );
    await page.goto(`${BASE}/static/dist/ai.html#/`);
    await page.waitForSelector('#footUser', { state: 'visible', timeout: 15000 });
}

test.describe('设置入口挪到用户块(本地 stub · 真构建产物)', () => {
    test('侧栏「设置」条目已删', async ({ page }) => {
        await boot(page);
        await expect(page.locator('#navSettings')).toHaveCount(0);
        await expect(page.locator('#footUser')).toBeVisible();
    });

    test('点用户块 → 右侧照常出设置页(不是浮层)', async ({ page }) => {
        await boot(page);
        await expect(page.locator('#v-settings')).not.toHaveClass(/\bon\b/);

        await page.locator('#footUser').click();

        // 设置内容渲染在右侧正文区 v-settings 里,不是任何浮层/抽屉
        const view = page.locator('#v-settings');
        await expect(view).toHaveClass(/\bon\b/);
        await expect(view.locator('#stLangSeg .vt-btn')).toHaveCount(4);
        await expect(view.locator('.wosum .cell')).toHaveCount(2);
        await expect(view.locator('[data-action="settings-logout"]')).toBeVisible();
        await expect(view.locator('.wosum .cell .v').first()).toContainText('skin@example.com');

        // 位置证据:设置内容必须落在侧栏右边的正文区,不是压在侧栏上的浮层
        const side = await page.locator('.side').boundingBox();
        const seg = await view.locator('#stLangSeg').boundingBox();
        expect(seg.x, '设置内容应在侧栏右侧').toBeGreaterThanOrEqual(side.x + side.width);

        const st = await view.evaluate((el) => {
            const s = getComputedStyle(el);
            return { display: s.display, position: s.position };
        });
        expect(st.display).toBe('block');
        expect(st.position, '不该是浮层').not.toBe('absolute');

        // 面包屑跟着切到「设置」,用户块高亮
        await expect(page.locator('#crumb')).toContainText('设置');
        await expect(page.locator('#footUser')).toHaveClass(/\bon\b/);

        await page.screenshot({ path: path.join(ARTIFACT_DIR, '01-settings-zh.png') });
    });

    for (const lang of ['th', 'en', 'ja']) {
        test(`${lang} 不露原始 key`, async ({ page }) => {
            await boot(page, lang);
            await page.locator('#footUser').click();
            await expect(page.locator('#v-settings #stLangSeg')).toBeVisible();
            const text = await page.locator('#v-settings').innerText();
            expect(text, `${lang} 漏了翻译`).not.toContain('settings_');
            expect(text, `${lang} 漏了翻译`).not.toContain('nav_settings');
            await page.screenshot({ path: path.join(ARTIFACT_DIR, `02-settings-${lang}.png`) });
        });
    }
});
