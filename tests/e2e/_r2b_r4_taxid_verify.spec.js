// R4 税号错录守护卡 · 本地 stub 真浏览器验收(非 CI · 用完即删,同 _r2f_r3_verify 先例)。
// 真渲染 static/dist/ai.js/ai.css/ai.html(零改造)+ 真 DOM,只桩网络层(page.route)。
// 盖:守护卡可见 + 文案带票上/登记税号 + 有权限显「一键改」按钮(点击真发 PATCH+realign)/
// 无权限诚实降级文案(无假按钮)。抓 isVisible + getComputedStyle,截图存 _artifacts/r2b_r4。
// 起法:npx playwright test tests/e2e/_r2b_r4_taxid_verify.spec.js
/* global window */
const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8994;
const BASE = `http://127.0.0.1:${PORT}`;
const PAGE = BASE + '/static/dist/ai.html';
const ART = path.join(__dirname, '_artifacts', 'r2b_r4');

const REG = '0105567178203';
const SUS = '0105567178230';

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT);
});
test.afterAll(() => localServer.stop(server));

function jsonRoute(body, status) {
    return (route) =>
        route.fulfill({
            status: status || 200,
            contentType: 'application/json',
            body: JSON.stringify(body),
        });
}

const CLIENT = { id: 5, name: 'Sister Makeup', tax_id: REG };
const ORDER = { id: 'wo-1', period: '2569-05', workspace_client_id: 5, status: 'stuck' };
const FLAGGED = [
    {
        item_id: 'it-1',
        kind: 'unknown',
        flag_reason: 'direction_ambiguous',
        file_ref: '/x/a.jpg',
        ocr_read: { seller_tax: SUS, subtotal: '100.00', vat: '7.00', total_amount: '107.00' },
    },
];
const ALERT = {
    type: 'taxid_typo_suspected',
    registered: REG,
    suspected: SUS,
    doc_count: 4,
    distance: 1,
    kind: 'transposition',
};

async function mount(page, table, opts = {}) {
    await page.route('**/api/**', async (route) => {
        const req = route.request();
        const url = new URL(req.url());
        const h = table[`${req.method()} ${url.pathname}`];
        if (h) return h(route, req, url);
        return route.fulfill({ contentType: 'application/json', body: '{}' });
    });
    await page.addInitScript((lang) => {
        window.localStorage.setItem('mrpilot_token_ai', 'tok-r2b-r4');
        window.localStorage.setItem('mrpilot_lang', lang || 'zh');
    }, opts.lang);
}

function baseTable(detailAlerts, canManage) {
    return {
        'GET /api/workspace/clients': jsonRoute([CLIENT]),
        'GET /api/workorder/orders': jsonRoute({ orders: [ORDER] }),
        'GET /api/workorder/orders/wo-1': jsonRoute({
            id: 'wo-1',
            workspace_client_id: 5,
            period: '2569-05',
            status: 'stuck',
            flagged: FLAGGED,
            alerts: detailAlerts,
            needs: [],
            blocked_reasons: [],
            numbers: {},
        }),
        'GET /api/workspace/clients/can-create': canManage
            ? jsonRoute({ ok: true })
            : jsonRoute({ detail: 'authz.forbidden' }, 403),
    };
}

test('有权限:守护卡显文案 + 一键改按钮,点击真发 PATCH+realign', async ({ page }) => {
    const calls = { patch: null, realign: null };
    const table = Object.assign(baseTable([ALERT], true), {
        'PATCH /api/workspace/clients/5': async (route, req) => {
            calls.patch = JSON.parse(req.postData() || '{}');
            return jsonRoute({ ok: true, id: 5 })(route);
        },
        'POST /api/workorder/orders/wo-1/realign-taxid': async (route, req) => {
            calls.realign = JSON.parse(req.postData() || '{}');
            return jsonRoute({ ok: true, reset_count: 1 })(route);
        },
    });
    await mount(page, table, { lang: 'zh' });
    await page.goto(`${PAGE}#/client/5/review?period=2569-05`);

    const alertBox = page.locator('.rv-taxid-alert');
    await expect(alertBox).toBeVisible({ timeout: 15000 });
    // 文案带票上税号(suspected)与登记税号(registered)。
    await expect(page.locator('.rv-taxid-msg')).toContainText(SUS);
    await expect(page.locator('.rv-taxid-msg')).toContainText(REG);
    // 真按钮(非假门),有背景色(btn pri)。
    const btn = page.locator('.rv-taxid-alert button.btn.pri');
    await expect(btn).toBeVisible();
    const bg = await btn.evaluate((el) => window.getComputedStyle(el).backgroundColor);
    expect(bg).not.toBe('rgba(0, 0, 0, 0)');
    await page.screenshot({ path: path.join(ART, 'canmanage_card.png'), fullPage: true });

    await btn.click();
    await expect.poll(() => calls.patch, { timeout: 8000 }).toEqual({ tax_id: SUS });
    await expect.poll(() => calls.realign).toEqual({ registered: REG, suspected: SUS });
});

test('无权限:诚实降级文案,无假按钮', async ({ page }) => {
    await mount(page, baseTable([ALERT], false), { lang: 'zh' });
    await page.goto(`${PAGE}#/client/5/review?period=2569-05`);

    const alertBox = page.locator('.rv-taxid-alert');
    await expect(alertBox).toBeVisible({ timeout: 15000 });
    await expect(page.locator('.rv-taxid-hint')).toBeVisible();
    await expect(page.locator('.rv-taxid-alert button.btn.pri')).toHaveCount(0);
    await page.screenshot({ path: path.join(ART, 'nopermission_card.png'), fullPage: true });
});

test('无嫌疑(alerts 空):不渲染守护卡', async ({ page }) => {
    await mount(page, baseTable([], true), { lang: 'zh' });
    await page.goto(`${PAGE}#/client/5/review?period=2569-05`);
    await page.waitForSelector('#cv-review', { timeout: 15000 });
    await expect(page.locator('.rv-taxid-alert')).toHaveCount(0);
});
