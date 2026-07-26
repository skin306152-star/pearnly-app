// 状态词典 #/states(B1 · 状态语言底座)· 本地真浏览器验收(跑 static/dist 真构建产物)
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**(同
// _settings_entry_local.spec.js 先例)。被断言的 DOM/CSS 全来自真产物:15 节真渲染、
// 八色族背景真有色差(getComputedStyle)、进度环/条/步骤真可见、可解释卡真展开、
// 按钮七态真禁用。截图存 tests/e2e/_artifacts/b1_states/。
//
// 起法:npx playwright test tests/e2e/_b1_states_local.spec.js
/* global window, document, getComputedStyle */

const { test, expect } = require('@playwright/test');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const ROOT = path.resolve(__dirname, '..', '..');
const PORT = 8989;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'b1_states');

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

async function boot(page, lang = 'zh') {
    await page.route('**/api/me**', (r) =>
        r.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({ username: 'skin', email: 'skin@example.com' }),
        })
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
            window.localStorage.setItem('mrpilot_token_ai', 'tok-b1states');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [lang]
    );
    await page.goto(`${BASE}/static/dist/ai.html#/states`);
    await page.waitForSelector('#v-states.on', { state: 'visible', timeout: 15000 });
}

test.describe('状态词典 #/states(本地 stub · 真构建产物)', () => {
    test('15 节全渲染 · 面包屑对 · 不占侧栏', async ({ page }) => {
        await boot(page);
        await expect(page.locator('#stsBody .panel')).toHaveCount(15);
        await expect(page.locator('#stsBody .panel .hd h3').first()).toContainText('数据状态');
        await expect(page.locator('#stsBody .panel .hd h3').last()).toContainText('动画反馈');
        await expect(page.locator('#crumb')).toContainText('状态词典');
        // 词典页不进侧栏:导航里没有任何指向 #/states 的项。
        expect(await page.locator('.snav a[href*="states"]').count()).toBe(0);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '01-states-zh-desktop.png'),
            fullPage: true,
        });
    });

    test('八色族真有色差(getComputedStyle)· 徽章是胶囊形', async ({ page }) => {
        await boot(page);
        const sw = page.locator('.sts-swatches .sts-swatch');
        await expect(sw).toHaveCount(8);
        const bgs = await sw.evaluateAll((els) =>
            els.map((el) => getComputedStyle(el).backgroundColor)
        );
        expect(new Set(bgs).size, `八族背景应各不相同,实得 ${bgs.join(' | ')}`).toBe(8);
        // AI 紫族取到 ai-theme 的 --brain-soft 真值(#ebe5f0)。
        expect(bgs[3]).toBe('rgb(235, 229, 240)');
        const badge = page.locator('#stsBody .st-badge').first();
        const shape = await badge.evaluate((el) => {
            const s = getComputedStyle(el);
            return { radius: s.borderRadius, display: s.display };
        });
        expect(shape.radius).toBe('99px');
        // 声明是 inline-flex;作为 flex 项时浏览器按规范块化成 flex,两者都算数。
        expect(['inline-flex', 'flex']).toContain(shape.display);
    });

    test('进度六件真可见 · 环带百分比 · 步骤 3/8', async ({ page }) => {
        await boot(page);
        const progressSec = page.locator('#stsBody .panel').nth(5);
        await expect(progressSec.locator('.st-bar').first()).toBeVisible();
        await expect(progressSec.locator('.st-ring b')).toContainText('%');
        await expect(progressSec.locator('.st-eta')).toBeVisible();
        await expect(progressSec.locator('.st-queue b')).toHaveText('5');
        const steps = progressSec.locator('.st-steps').first();
        await expect(steps.locator('i')).toHaveCount(8);
        await expect(steps.locator('i.on')).toHaveCount(3);
        // 条的填充宽度真跟 --p 走(不是 0 宽的摆设)。
        const w = await progressSec
            .locator('.st-bar > i')
            .first()
            .evaluate((el) => el.getBoundingClientRect().width);
        expect(w).toBeGreaterThan(10);
    });

    test('按钮七态:禁用真禁用 · loading 内嵌三点', async ({ page }) => {
        await boot(page);
        const btnSec = page.locator('#stsBody .panel').nth(11);
        await expect(btnSec.locator('.st-btn')).toHaveCount(7);
        await expect(btnSec.locator('.st-btn[disabled]')).toHaveCount(2);
        await expect(btnSec.locator('.st-btn.is-loading .st-dots i')).toHaveCount(3);
        const err = btnSec.locator('.st-btn.is-error');
        const bg = await err.evaluate((el) => getComputedStyle(el).backgroundColor);
        // 错误态吃 --st-err-bg = --crit-soft(#f4e3da)。
        expect(bg).toBe('rgb(244, 227, 218)');
    });

    test('AI 可解释卡:点「依据」真展开三条来源', async ({ page }) => {
        await boot(page);
        const card = page.locator('#stsBody .st-explain');
        await expect(card.locator('.st-explain-src').first()).toBeHidden();
        await card.locator('[data-action="sts-explain-toggle"]').click();
        await expect(card).toHaveClass(/\bon\b/);
        await expect(card.locator('.st-explain-src')).toHaveCount(3);
        await expect(card.locator('.st-explain-src').first()).toBeVisible();
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '02-explain-open.png') });
    });

    test('手机视口 390×844 · 页面不横向溢出', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await boot(page);
        await expect(page.locator('#stsBody .panel')).toHaveCount(15);
        const overflow = await page.evaluate(
            () => document.documentElement.scrollWidth - document.documentElement.clientWidth
        );
        expect(overflow, '手机上不许横滚').toBeLessThanOrEqual(1);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '03-states-mobile.png'),
            fullPage: true,
        });
    });

    test('泰语不露原始 key', async ({ page }) => {
        await boot(page, 'th');
        const text = await page.locator('#v-states').innerText();
        expect(text, 'th 漏了翻译').not.toContain('sts_');
        await expect(page.locator('#stsBody .panel .hd h3').first()).toContainText('สถานะข้อมูล');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '04-states-th.png'),
            fullPage: true,
        });
    });

    test('系统减弱动态:演示计时器不起 · 页面仍完整', async ({ page }) => {
        await page.emulateMedia({ reducedMotion: 'reduce' });
        await boot(page);
        await expect(page.locator('#stsBody .panel')).toHaveCount(15);
        const p1 = await page.locator('[data-demo="pct"]').first().getAttribute('style');
        await page.waitForTimeout(2200);
        const p2 = await page.locator('[data-demo="pct"]').first().getAttribute('style');
        expect(p2, '减弱动态下百分比不该滚动').toBe(p1);
    });
});
