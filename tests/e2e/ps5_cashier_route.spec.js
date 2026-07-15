// PS-5 · POS 路径迁址真浏览器 E2E · /cashier 收银台新家 + /pos 老板后台登录页 + 老设备接回
//
// 起真实 FastAPI app(uvicorn · 无 DB 也能跑本组纯页面路由),真浏览器验:
//   ① /cashier 渲染收银台绑定页 + PWA manifest 可达(start_url/scope=/cashier)+ SW 注册 scope=/cashier
//   ② /pos(无绑定凭据)渲染老板后台登录页,断言无 Google/LINE/注册旁路
//   ③ /pos(带伪造 pos_store_token)→ 立即跳 /cashier(老收银设备接回)
// 现有指 /pos 的 SPA 直载壳 spec(ps1_*)守老径兼容,本 spec 只加新径,不改它们。
// localhost 是安全上下文 → service worker 可注册。截图存 tests/e2e/_artifacts/ps5/。
/* global window, getComputedStyle */

const { test, expect } = require('@playwright/test');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const ROOT = path.resolve(__dirname, '..', '..');
const PORT = 8974;
const BASE = `http://127.0.0.1:${PORT}`;
const ART = path.join(__dirname, '_artifacts', 'ps5');

let server;

function waitUp(url, tries = 80) {
    return new Promise((resolve, reject) => {
        const hit = (n) => {
            http.get(url, (r) => {
                r.resume();
                if (r.statusCode && r.statusCode < 500) return resolve();
                if (n <= 0) return reject(new Error('server 5xx'));
                setTimeout(() => hit(n - 1), 250);
            }).on('error', () => {
                if (n <= 0) return reject(new Error('server not up'));
                setTimeout(() => hit(n - 1), 250);
            });
        };
        hit(tries);
    });
}

test.beforeAll(async () => {
    server = spawn(
        'python',
        [
            '-m',
            'uvicorn',
            'app:app',
            '--host',
            '127.0.0.1',
            '--port',
            String(PORT),
            '--no-access-log',
        ],
        { cwd: ROOT, stdio: 'ignore', env: { ...process.env, PYTHONUTF8: '1' } }
    );
    await waitUp(`${BASE}/cashier`);
});

test.afterAll(() => {
    if (server) server.kill();
});

test('① /cashier 渲染绑定页 + PWA manifest/SW 作用域 /cashier', async ({ page }) => {
    await page.goto(`${BASE}/cashier`, { waitUntil: 'networkidle' });
    await expect(page.locator('#view-bind')).toBeVisible();
    await expect(page.locator('#bind-code')).toBeVisible();

    // manifest 挂的是 /cashier 作用域的清单
    const manifestHref = await page.getAttribute('link[rel=manifest]', 'href');
    expect(manifestHref).toContain('cashier.webmanifest');
    const manURL = new URL(manifestHref, BASE).href;
    const man = await (await page.request.get(manURL)).json();
    expect(man.start_url).toBe('/cashier');
    expect(man.scope).toBe('/cashier');

    // service worker 注册在 /cashier 作用域(离线重开收银壳)
    await page.waitForTimeout(1500);
    const scopes = await page.evaluate(async () => {
        const rs = await navigator.serviceWorker.getRegistrations();
        return rs.map((r) => r.scope);
    });
    expect(scopes.some((s) => s.endsWith('/cashier'))).toBeTruthy();

    await page.screenshot({ path: path.join(ART, 'cashier_bind.png'), fullPage: true });
});

test('② /pos 无绑定凭据 → 老板后台登录页(无 Google/LINE/注册)', async ({ page }) => {
    await page.goto(`${BASE}/pos`, { waitUntil: 'networkidle' });
    await expect(page.locator('#p-email')).toBeVisible();
    await expect(page.locator('#p-pw')).toBeVisible();
    await expect(page.locator('#p-submit')).toBeVisible();

    const bodyText = (await page.locator('body').innerText()).toLowerCase();
    expect(/google|sign\s?up|注册|line\s*(login|登录)/.test(bodyText)).toBeFalsy();
    const html = await page.content();
    expect(html.includes('/api/auth/google') || html.includes('/api/auth/line')).toBeFalsy();

    await page.screenshot({ path: path.join(ART, 'pos_owner_login.png'), fullPage: true });
});

test('③ /pos 不再被残留店铺令牌劫持', async ({ page }) => {
    // /pos 现为老板后台登录页 · 删掉了「残留 pos_store_token 即劫持跳 /cashier」守卫
    // (老板浏览器残留令牌会被误劫持;收银设备的家在 /cashier,设备直开)。带伪造
    // pos_store_token 访问 /pos 应停在 /pos 登录页,不跳 /cashier。
    await page.goto(`${BASE}/pos`, { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => localStorage.setItem('pos_store_token', 'FORGED-STORE-TOKEN'));
    await page.goto(`${BASE}/pos`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(400);
    expect(page.url()).toContain('/pos');
    expect(page.url().endsWith('/cashier')).toBeFalsy();
});
