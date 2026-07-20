// GC-D-4/5 · 工单页缺料键人话化 + 逐笔对账空态文案诚实化 · 本地 stub 真浏览器验收
// (同 _jb_realtime_guidance_verify.spec.js 先例:真渲染 dist 资产 + 真 DOM,只桩 /api/*)
//   D4) 状态头缺料清单不裸显 needs 键——sales_summary 显示为四语人话「销项汇总」
//   D5) bank_recon 为空时空态卡不再断言「还没有银行流水」,显示「逐笔银行对账清单未产出」
//
// 起法:npx playwright test tests/e2e/_gcd45_wo_copy_verify.spec.js
/* global window */
const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8997;
const BASE = `http://127.0.0.1:${PORT}`;
const PAGE = BASE + '/static/dist/ai.html';
const ART = path.join(__dirname, '_artifacts', 'gcd45');

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT);
});

test.afterAll(() => {
    localServer.stop(server);
});

async function mockRoutes(page, table) {
    await page.route('**/api/**', async (route) => {
        const req = route.request();
        const url = new URL(req.url());
        const handler = table[`${req.method()} ${url.pathname}`];
        if (handler) return handler(route, req, url);
        return route.fulfill({ contentType: 'application/json', body: '{}' });
    });
    await page.addInitScript(() => {
        window.localStorage.setItem('mrpilot_token_ai', 'tok-gcd45');
        window.localStorage.setItem('mrpilot_lang', 'zh');
    });
}

function jsonRoute(body) {
    return (route) =>
        route.fulfill({ contentType: 'application/json', body: JSON.stringify(body) });
}

test('D4/D5 · 缺料键人话 + 逐笔对账空态诚实', async ({ page }) => {
    await mockRoutes(page, {
        'GET /api/workspace/clients/c1': jsonRoute({ client: { id: 'c1', name: 'Acme Co' } }),
        'GET /api/workorder/orders': jsonRoute({ orders: [{ id: 'wo-1', period: '2569-05' }] }),
        'GET /api/workorder/orders/wo-1': jsonRoute({
            id: 'wo-1',
            status: 'collecting',
            current_step: 'intake',
            needs: ['sales_summary'],
            blocked_reasons: [],
            numbers: {},
            flagged: [],
            bank_recon: null,
        }),
    });
    await page.goto(`${PAGE}#/client/c1/wo`);
    await page.waitForSelector('#woSummaryPanel', { timeout: 15000 });

    // D4:缺料项走 fieldLabel 四语查表,不裸显键名。
    const needItem = page.locator('.ni');
    await expect(needItem).toBeVisible({ timeout: 8000 });
    await expect(needItem).toContainText('销项汇总');
    await expect(needItem).not.toContainText('sales_summary');

    // D5:E2 空态卡不再宣称「还没有银行流水」。
    const brx = page.locator('#brxRoot');
    await expect(brx).toContainText('逐笔银行对账清单未产出', { timeout: 8000 });
    await expect(brx).not.toContainText('还没有银行流水');

    await page.screenshot({ path: path.join(ART, '01-wo-needs-and-brx.png'), fullPage: true });
});
