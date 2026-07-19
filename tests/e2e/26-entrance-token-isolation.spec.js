/* global getComputedStyle */

const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8997;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'gc0719_a');
const AI_TOKEN = 'ai-fake-token';
const POS_TOKEN = 'pos-fake-token';

let server;

test.beforeAll(async () => {
    fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
    server = await localServer.start(PORT);
});

test.afterAll(() => localServer.stop(server));

async function installShellRoutes(context) {
    await context.route(`${BASE}/ai`, (route) =>
        route.fulfill({
            path: path.join(localServer.ROOT, 'static', 'dist', 'ai.html'),
            contentType: 'text/html',
        })
    );
    await context.route(`${BASE}/pos`, (route) =>
        route.fulfill({
            path: path.join(localServer.ROOT, 'static', 'dist', 'pos-login.html'),
            contentType: 'text/html',
        })
    );
}

async function installApiRoutes(context, state) {
    await context.route('**/api/**', async (route) => {
        const request = route.request();
        const pathname = new URL(request.url()).pathname;
        const method = request.method();

        if (pathname === '/api/login' && method === 'POST') {
            const body = request.postDataJSON();
            const token = body.entry === 'pos' ? POS_TOKEN : AI_TOKEN;
            return route.fulfill({ json: { access_token: token, user: { id: 'u1' } } });
        }
        if (pathname === '/api/ai/session') return route.fulfill({ json: { ok: true } });
        if (pathname === '/api/me') {
            return route.fulfill({ json: { id: 'u1', username: 'gc-accountant' } });
        }
        if (pathname === '/api/workorder/orders' && method === 'GET') {
            return route.fulfill({
                json: { orders: [{ id: 'wo-1', workspace_client_id: 'c1', period: '2569-05' }] },
            });
        }
        if (pathname === '/api/workorder/orders/wo-1' && method === 'GET') {
            return route.fulfill({
                json: {
                    id: 'wo-1',
                    status: 'stuck',
                    needs: ['sales_summary'],
                    numbers: {},
                    flagged: [],
                    material_count: 0,
                },
            });
        }
        if (pathname === '/api/workspace/clients/c1') {
            return route.fulfill({ json: { client: { id: 'c1', name: 'GC Test Client' } } });
        }
        if (pathname === '/api/ai/front-desk/status') {
            return route.fulfill({ json: { enabled: false } });
        }
        if (pathname === '/api/workorder/orders/wo-1/sales-summary' && method === 'POST') {
            state.salesAuthorization = request.headers().authorization || '';
            if (state.submitMode === 'network') return route.abort('failed');
            if (state.submitMode === 'session') {
                return route.fulfill({ status: 401, json: { detail: 'auth.invalid_token' } });
            }
            if (state.submitMode === 'entrance') {
                return route.fulfill({
                    status: 403,
                    json: { detail: 'authz.entrance_scope' },
                });
            }
            return route.fulfill({ json: { ok: true } });
        }
        return route.fulfill({ status: 404, json: { detail: `not_stubbed:${pathname}` } });
    });
}

async function bootIntake(page) {
    await page.addInitScript(() => localStorage.setItem('mrpilot_lang', 'zh'));
    await page.goto(`${BASE}/ai#/client/c1/intake`);
    await expect(page.locator('#gateLoginForm')).toBeVisible();
    await page.locator('#gateUsername').fill('accountant@example.com');
    await page.locator('#gatePassword').fill('secret');
    await page.locator('#gateLoginForm button[type="submit"]').click();
    await expect(page.locator('#ikDrop')).toBeVisible({ timeout: 15_000 });
    await page.locator('[data-action="ik-open-form"]').click();
    await expect(page.locator('#ikSalesForm')).toBeVisible();
}

async function fillSalesForm(page) {
    await page.locator('#ikSales').fill('1000.00');
    await page.locator('#ikVat').fill('70.00');
    await page.locator('#ikNote').fill('POS monthly report');
}

async function expectRendered(locator) {
    await expect(locator).toBeVisible();
    const style = await locator.evaluate((element) => {
        const computed = getComputedStyle(element);
        return {
            display: computed.display,
            visibility: computed.visibility,
            opacity: computed.opacity,
        };
    });
    expect(style.display).not.toBe('none');
    expect(style.visibility).not.toBe('hidden');
    expect(Number(style.opacity)).toBeGreaterThan(0);
}

test('同一 Chrome 的 AI 与 POS 登录互不覆盖,入口 403 如实显示并锁提交', async ({ context }) => {
    const state = { submitMode: 'entrance', salesAuthorization: '' };
    await installShellRoutes(context);
    await installApiRoutes(context, state);

    const aiPage = await context.newPage();
    await bootIntake(aiPage);

    const posPage = await context.newPage();
    await posPage.goto(`${BASE}/pos`);
    await posPage.locator('#p-email').fill('cashier@example.com');
    await posPage.locator('#p-pw').fill('secret');
    await posPage.locator('#p-form button[type="submit"]').click();
    await expect
        .poll(() => aiPage.evaluate(() => localStorage.getItem('mrpilot_token')))
        .toBe(POS_TOKEN);

    await fillSalesForm(aiPage);
    await aiPage.locator('#ikSalesForm button[type="submit"]').click();

    const error = aiPage.locator('#ikFormErr');
    await expectRendered(error);
    await expect(error).toHaveText('当前登录入口无权申报，请在 Pearnly AI 入口重新登录');
    await expect(error).not.toContainText('请填有效的销售额和销项税');
    await expect(aiPage.locator('#ikSalesForm button[type="submit"]')).toBeDisabled();
    expect(state.salesAuthorization).toBe(`Bearer ${AI_TOKEN}`);
    expect(await aiPage.evaluate(() => localStorage.getItem('mrpilot_token_ai'))).toBe(AI_TOKEN);
    expect(await aiPage.evaluate(() => localStorage.getItem('mrpilot_token'))).toBe(POS_TOKEN);
    await aiPage.screenshot({
        path: path.join(ARTIFACT_DIR, '01-token-isolation-entrance-403.png'),
        fullPage: true,
    });
});

test('断网显示可重试提示且不锁提交', async ({ context, page }) => {
    const state = { submitMode: 'network', salesAuthorization: '' };
    await installShellRoutes(context);
    await installApiRoutes(context, state);
    await bootIntake(page);
    await fillSalesForm(page);
    await page.locator('#ikSalesForm button[type="submit"]').click();

    const error = page.locator('#ikFormErr');
    await expectRendered(error);
    await expect(error).toHaveText('网络异常，请重试');
    await expect(page.locator('#ikSalesForm button[type="submit"]')).toBeEnabled();
    await page.screenshot({
        path: path.join(ARTIFACT_DIR, '02-network-retryable.png'),
        fullPage: true,
    });
});

test('格式错留在表单,401 清 AI 令牌并在登录卡说明会话失效', async ({ context, page }) => {
    const state = { submitMode: 'session', salesAuthorization: '' };
    await installShellRoutes(context);
    await installApiRoutes(context, state);
    await bootIntake(page);

    await page.locator('#ikSalesForm button[type="submit"]').click();
    await expect(page.locator('#ikFormErr')).toHaveText('请填有效的销售额和销项税(非负数字)');
    await expect(page.locator('#ikSalesForm button[type="submit"]')).toBeEnabled();

    await fillSalesForm(page);
    await page.locator('#ikSalesForm button[type="submit"]').click();
    const message = page.locator('#gateMsg');
    await expectRendered(message);
    await expect(message).toHaveText('会话已失效，请重新登录');
    expect(await page.evaluate(() => localStorage.getItem('mrpilot_token_ai'))).toBeNull();
    await page.screenshot({
        path: path.join(ARTIFACT_DIR, '03-session-expired-login.png'),
        fullPage: true,
    });
});
