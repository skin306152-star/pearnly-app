// 矩阵「当期一项义务都没物化」空态(2026-07-27 Zihao 自己看出来的:只剩「客户」一列的
// 残缺表比空态还难看)· 本地真浏览器验收 —— 跑 static/dist 真构建产物,不跑源文件。
// ============================================================
// python http.server 静态服 + page.route stub /api/**(同 _board_tools_local.spec.js
// 先例)。断言的选择器/文案全来自真实产物(ai-matrix-render.js / ai-i18n-empty.js),
// 可见性一律 toBeVisible/isVisible 判。截图存 tests/e2e/_artifacts/matrix_empty/。
//
// 起法:npx playwright test tests/e2e/_matrix_empty_local.spec.js
/* global window */

const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8994;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'matrix_empty');

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT);
});

test.afterAll(() => localServer.stop(server));

const PERIOD = '2569-07';
const CLIENTS = [
    { id: 1, name: 'บริษัท เอ' },
    { id: 2, name: 'บริษัท บี' },
];

// 有客户、但当期一格义务都没物化:后端把 obligation_code 全为 null 的行折成空列集合。
const MATRIX_NO_OBLIGATIONS = {
    period: PERIOD,
    clients: CLIENTS.map((c) => Object.assign({ missing_order: true }, c)),
    obligation_codes: [],
    obligation_labels: {},
    cells: [],
};

const MATRIX_WITH_OBLIGATIONS = {
    period: PERIOD,
    clients: CLIENTS.map((c) => Object.assign({ missing_order: true }, c)),
    obligation_codes: ['pp30'],
    obligation_labels: { pp30: { zh: '增值税', th: 'ภ.พ.30' } },
    cells: [{ client_id: 1, obligation_code: 'pp30', badge: 'pending_order' }],
};

function json(body) {
    return { contentType: 'application/json', body: JSON.stringify(body) };
}

async function boot(page, { lang = 'zh', matrix = MATRIX_NO_OBLIGATIONS } = {}) {
    await page.route('**/api/**', (r) => {
        const url = r.request().url();
        if (url.includes('/api/tax-profile/matrix')) return r.fulfill(json(matrix));
        if (url.includes('/api/workorder/orders')) return r.fulfill(json({ orders: [] }));
        if (url.includes('/api/workspace/clients')) return r.fulfill(json({ clients: CLIENTS }));
        if (url.includes('/api/me')) return r.fulfill(json({ username: 'skin' }));
        return r.fulfill(json({}));
    });
    await page.addInitScript(
        ([l]) => {
            window.localStorage.setItem('mrpilot_token_ai', 'tok-matrix');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [lang]
    );
    await page.goto(`${BASE}/static/dist/ai.html#/`);
    await page.waitForSelector('#matrixBody .state-block, #matrixBody .mx-table', {
        state: 'visible',
        timeout: 15000,
    });
}

test.describe('当期无义务的矩阵', () => {
    test('出空态而不是只剩一列的残缺表 · 说清为什么空', async ({ page }) => {
        await boot(page);
        await expect(page.locator('#matrixBody .mx-noobl')).toBeVisible();
        await expect(page.locator('#matrixBody .mx-table')).toHaveCount(0);
        const text = await page.locator('#matrixBody .mx-noobl').innerText();
        expect(text).not.toContain('emp_mx_noobl'); // i18n key 不许露脸
        expect(text.length).toBeGreaterThan(20); // 空标题糊弄不算说清
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '01-no-obligations-zh.png'),
            fullPage: true,
        });
    });

    test('两条出路都能点 · 落到真路由', async ({ page }) => {
        await boot(page);
        const profileBtn = page.locator('#matrixBody .mx-noobl a[href="#/clients"]');
        const boardBtn = page.locator('#matrixBody .mx-noobl a[href="#/board"]');
        await expect(profileBtn).toBeVisible();
        await expect(boardBtn).toBeVisible();
        await boardBtn.click();
        await page.waitForSelector('#boardSection', { state: 'visible', timeout: 10000 });
        expect(page.url()).toContain('#/board');
    });

    test('泰语也是整句泰文', async ({ page }) => {
        await boot(page, { lang: 'th' });
        const text = await page.locator('#matrixBody .mx-noobl').innerText();
        expect(text).toContain('งวดนี้');
        expect(text).not.toContain('这一期');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '02-no-obligations-th.png'),
            fullPage: true,
        });
    });

    test('有义务列时照旧出表格(空态不误伤正常矩阵)', async ({ page }) => {
        await boot(page, { matrix: MATRIX_WITH_OBLIGATIONS });
        await expect(page.locator('#matrixBody .mx-table')).toBeVisible();
        await expect(page.locator('#matrixBody .mx-noobl')).toHaveCount(0);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '03-matrix-with-obligations.png'),
            fullPage: true,
        });
    });
});
