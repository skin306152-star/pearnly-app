// /ai 失败态出路 · 本地真浏览器验收(跑 static/dist 真构建产物)
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**
// (同 _b5_billing_local.spec.js 先例)。被断言的文字/可见性全来自真产物,stub 只兜后端响应。
//
// 验收两条缺口:
//  ① 点「开当期工单」失败此前页面零反应 —— 现在按钮回可点 + 卡里说清哪一步/为什么/下一步;
//  ② 收料上传失败此前只有「N 个文件失败 · 重传」—— 现在先说原因;余额不足(402)另给
//     「去充值」直达设置页计费区(重传一百次也不会好的失败不能只给重传)。
// 截图存 tests/e2e/_artifacts/fail_ways_out/。
//
// 起法:npx playwright test tests/e2e/_fail_ways_out_local.spec.js
/* global window */

const { test, expect } = require('@playwright/test');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const ROOT = path.resolve(__dirname, '..', '..');
const PORT = 8993;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'fail_ways_out');

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

const CLIENT = { id: 1, name: 'บริษัท ทดสอบ', tax_id: '0105551234567' };

// createOrder / addMaterials 的失败模式由 opts 注入:{status, code} 或 abort:true(网络断)。
async function boot(page, opts = {}) {
    await page.route('**/api/**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{}' })
    );
    await page.route('**/api/me**', (r) =>
        r.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({ username: 'skin', email: 's@e.com', tenant_name: 'skin' }),
        })
    );
    await page.route('**/api/workspace/clients/**', (r) =>
        r.fulfill({ contentType: 'application/json', body: JSON.stringify(CLIENT) })
    );
    // 零工单:wo / intake 两个 tab 都落「开当期工单」空态。
    await page.route('**/api/workorder/orders?**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{"orders":[]}' })
    );
    const fail = (route, mode) => {
        if (mode.abort) return route.abort('failed');
        return route.fulfill({
            status: mode.status,
            contentType: 'application/json',
            body: JSON.stringify({ detail: mode.code ? { code: mode.code } : 'generic' }),
        });
    };
    if (opts.createOrder) {
        await page.route(
            (u) => u.pathname === '/api/workorder/orders',
            (r) => (r.request().method() === 'POST' ? fail(r, opts.createOrder) : r.fallback())
        );
    }
    if (opts.materials) {
        await page.route('**/materials', (r) => fail(r, opts.materials));
    }
    await page.addInitScript(() => {
        window.localStorage.setItem('mrpilot_token_ai', 'tok-failways');
        window.localStorage.setItem('mrpilot_lang', 'zh');
    });
}

// 收料区选一份料再点上传。文件框是 ai-intake.js 运行时建的隐藏 #ikFileInput,
// 直接 setInputFiles 触发它自己的 change(点「选择文件」会开系统对话框,headless 里点不了)。
async function pickAndUpload(page) {
    const input = page.locator('#ikFileInput');
    await expect(input).toBeAttached({ timeout: 15000 });
    await input.setInputFiles({
        name: 'bill.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('%PDF-1.4 test'),
    });
    await page.locator('[data-action="ik-upload"]').click();
}

test.describe('/ai 失败态出路(本地 stub · 真构建产物)', () => {
    test('开当期工单:服务端 500 → 按钮回可点 + 说清哪一步为什么', async ({ page }) => {
        await boot(page, { createOrder: { status: 500 } });
        await page.goto(`${BASE}/static/dist/ai.html#/client/1/wo`);
        const btn = page.locator('[data-action="wo-open-first"]');
        await expect(btn).toBeVisible({ timeout: 15000 });
        await btn.click();

        const note = page.locator('.order-open-empty [role="alert"]');
        await expect(note).toBeVisible();
        await expect(note).toContainText('开单没成功');
        await expect(note).toContainText('服务器出错了');
        await expect(btn).toBeEnabled();
        await expect(btn).toHaveText('按所选账期开工单'); // 不再卡在「开单中…」
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '01-open-order-500.png'),
            fullPage: true,
        });
    });

    test('开当期工单:网络断 → 说的是网络不是服务器', async ({ page }) => {
        await boot(page, { createOrder: { abort: true } });
        await page.goto(`${BASE}/static/dist/ai.html#/client/1/wo`);
        const btn = page.locator('[data-action="wo-open-first"]');
        await expect(btn).toBeVisible({ timeout: 15000 });
        await btn.click();
        const note = page.locator('.order-open-empty [role="alert"]');
        await expect(note).toContainText('请求没发出去');
        await expect(btn).toBeEnabled();
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '02-open-order-network.png'),
            fullPage: true,
        });
    });

    test('开当期工单:余额不足 402 → 卡里直接给「去充值」并真落在计费区', async ({ page }) => {
        await boot(page, { createOrder: { status: 402, code: 'insufficient_balance' } });
        await page.goto(`${BASE}/static/dist/ai.html#/client/1/wo`);
        const btn = page.locator('[data-action="wo-open-first"]');
        await expect(btn).toBeVisible({ timeout: 15000 });
        await btn.click();
        const note = page.locator('.order-open-empty [role="alert"]');
        await expect(note).toContainText('OCR 余额不足');
        const topup = page.locator('.order-open-empty a.btn.pri');
        await expect(topup).toBeVisible();
        await expect(topup).toHaveText('去充值');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '03-open-order-402.png'),
            fullPage: true,
        });

        await topup.click();
        await expect(page.locator('#v-settings')).toHaveClass(/on/);
        await expect(page.locator('#stBillingWrap')).toBeVisible({ timeout: 15000 });
        // 深链的意义在「落地就看得见」:计费区必须在视口内,不是滚到页面顶部要人自己找。
        const inView = await page
            .locator('#stBillingWrap')
            .evaluate((el) => el.getBoundingClientRect().top < window.innerHeight);
        expect(inView).toBe(true);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '04-topup-deeplink-landing.png'),
            fullPage: true,
        });
    });

    test('收料上传:401 → 失败批说的是登录过期,不是干巴巴「上传失败」', async ({ page }) => {
        await boot(page, { materials: { status: 401 } });
        await page.goto(`${BASE}/static/dist/ai.html#/client/1/intake`);
        const openBtn = page.locator('[data-action="intake-open-order"]');
        await expect(openBtn).toBeVisible({ timeout: 15000 });
        // 开单成功(默认 stub 200)后才有上传区;这里只验上传失败态。
        await page.unroute('**/api/workorder/orders?**');
        await page.route('**/api/workorder/orders?**', (r) =>
            r.fulfill({
                contentType: 'application/json',
                body: '{"orders":[{"id":"wo-1","period":"2569-07","intent":"monthly_vat","status":"intake","current_step":"intake"}]}',
            })
        );
        await openBtn.click();

        await pickAndUpload(page);

        const banner = page.locator('.needs-card [role="alert"]');
        await expect(banner).toBeVisible({ timeout: 15000 });
        await expect(banner).toContainText('这些文件没传上去');
        await expect(banner).toContainText('登录已过期');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '05-upload-401.png'),
            fullPage: true,
        });
    });

    test('收料上传:余额不足 402 → 重传旁边多一个「去充值」', async ({ page }) => {
        await boot(page, { materials: { status: 402, code: 'insufficient_balance' } });
        await page.goto(`${BASE}/static/dist/ai.html#/client/1/intake`);
        const openBtn = page.locator('[data-action="intake-open-order"]');
        await expect(openBtn).toBeVisible({ timeout: 15000 });
        await page.unroute('**/api/workorder/orders?**');
        await page.route('**/api/workorder/orders?**', (r) =>
            r.fulfill({
                contentType: 'application/json',
                body: '{"orders":[{"id":"wo-1","period":"2569-07","intent":"monthly_vat","status":"intake","current_step":"intake"}]}',
            })
        );
        await openBtn.click();

        await pickAndUpload(page);

        const card = page.locator('.needs-card');
        await expect(card.locator('[role="alert"]')).toContainText('OCR 余额不足');
        await expect(card.locator('[data-action="ik-retry-failed"]')).toBeVisible();
        await expect(card.locator('a.btn.pri')).toHaveText('去充值');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '06-upload-402.png'),
            fullPage: true,
        });
    });
});
