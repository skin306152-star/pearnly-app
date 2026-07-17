// DL-4b 真浏览器验收(选车面板 + /dms 向导管理员账密 + LINE 绑定卡)。stub 三 API,
// 不碰真库/真后端。跑法: node scripts/_dl4b_verify.cjs → tests/e2e/_artifacts/dl4b/*.png
/* eslint-disable no-undef */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'tests/e2e/_artifacts/dl4b');
const PORT = 8799;
const TYPES = { '.js': 'application/javascript', '.css': 'text/css', '.html': 'text/html' };

fs.mkdirSync(OUT, { recursive: true });

function serve() {
    return http
        .createServer((req, res) => {
            const url = new URL(req.url, 'http://x');
            const fp = path.join(ROOT, decodeURIComponent(url.pathname));
            fs.readFile(fp, (err, data) => {
                if (err) {
                    res.writeHead(404);
                    return res.end('not found');
                }
                res.writeHead(200, {
                    'Content-Type': TYPES[path.extname(fp)] || 'application/octet-stream',
                });
                res.end(data);
            });
        })
        .listen(PORT);
}

function assert(cond, msg) {
    if (!cond) throw new Error('ASSERT FAIL: ' + msg);
}

async function shot(page, name) {
    await page.screenshot({ path: path.join(OUT, name), fullPage: true });
    console.log('  [shot]', name);
}

const CARS = [
    ['c1', 'ALTIS', 'Corolla Altis', ...Array(13).fill(''), '899000'],
    ['c2', 'CAMRY', 'Camry Hybrid', ...Array(13).fill(''), '1650000'],
];
const PAINTS = [
    ['p1', '040', 'White Pearl'],
    ['p2', '218', 'Attitude Black'],
];
const ADVISORS = [['a1', 'AD01', 'Somchai']];

// ── Part A: 选车面板(自包含 dms-pick.html)── 全流程 + 401 过期态。
async function verifyPickPanel(browser) {
    console.log('== Part A: dms-pick.html ==');
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await ctx.newPage();

    // A1) 正常数据 → 选车 → 联动颜色 → 选顾问/日期 → 提交 → 成功屏
    await page.route('**/api/dms/pick/data*', (route) =>
        route.fulfill({
            json: {
                ok: true,
                customer: { name: 'สมชาย ใจดี' },
                cars: CARS,
                advisors: ADVISORS,
                defaults: { advisor_id: 'a1', delivery_date_be: '01/08/2568' },
            },
        })
    );
    let paintsCarId = null;
    await page.route('**/api/dms/pick/paints*', (route, req) => {
        paintsCarId = new URL(req.url()).searchParams.get('car_id');
        route.fulfill({ json: { ok: true, paints: PAINTS } });
    });
    let submitBody = null;
    await page.route('**/api/dms/pick/submit', async (route, req) => {
        submitBody = JSON.parse(req.postData());
        route.fulfill({ json: { ok: true } });
    });

    await page.goto(`http://localhost:${PORT}/static/dist/dms-pick.html?t=tok123`);
    await page.waitForSelector('.card', { timeout: 5000 });
    await shot(page, '01-loading-then-form.png');

    const searchVisible = await page.locator('#pk-search').isVisible();
    assert(searchVisible, 'search box visible');

    await page.locator('[data-car="c1"]').click();
    await page.waitForFunction(() => document.querySelector('[data-paint]'));
    assert(paintsCarId === 'c1', 'paints fetch carried car_id=c1, got ' + paintsCarId);
    await shot(page, '02-car-selected-paints-loaded.png');

    await page.locator('[data-paint="p1"]').click();
    const submitBtn = page.locator('#pk-submit');
    assert(!(await submitBtn.isDisabled()), 'submit enabled after car+paint+advisor+date');
    const btnColor = await submitBtn.evaluate((el) => getComputedStyle(el).backgroundColor);
    assert(btnColor === 'rgb(47, 107, 255)', 'submit button is system blue, got ' + btnColor);

    await submitBtn.click();
    await page.waitForSelector('.state.ok', { timeout: 5000 });
    assert(submitBody.t === 'tok123', 'submit body has t');
    assert(submitBody.car_id === 'c1', 'submit body car_id');
    assert(submitBody.paint_id === 'p1', 'submit body paint_id');
    assert(submitBody.advisor_id === 'a1', 'submit body advisor_id');
    assert(submitBody.delivery_date_be === '01/08/2568', 'submit body delivery_date_be');
    assert(Object.keys(submitBody).length === 5, 'submit body has exactly 5 keys');
    const successVisible = await page.locator('.state.ok h2').isVisible();
    assert(successVisible, 'success screen visible');
    const successText = await page.locator('.state.ok p').textContent();
    assert(successText.includes('LINE'), 'success text mentions LINE, got: ' + successText);
    await shot(page, '03-success.png');
    await ctx.close();

    // A2) 401 过期态(独立 context,干净重来)
    const ctx401 = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page401 = await ctx401.newPage();
    await page401.route('**/api/dms/pick/data*', (route) =>
        route.fulfill({ status: 401, json: { detail: 'dms_pick.expired' } })
    );
    await page401.goto(`http://localhost:${PORT}/static/dist/dms-pick.html?t=stale`);
    await page401.waitForSelector('.state.err', { timeout: 5000 });
    const errTitle = await page401.locator('.state.err h2').textContent();
    assert(errTitle.includes('หมดอายุ'), '401 shows expired-link copy, got: ' + errTitle);
    const errColor = await page401
        .locator('.state.err .ic')
        .evaluate((el) => getComputedStyle(el).color);
    assert(errColor === 'rgb(214, 88, 106)', '401 icon uses red token, got ' + errColor);
    await shot(page401, '04-err-401-expired.png');
    await ctx401.close();

    // A3) 404 未开通态
    const ctx404 = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page404 = await ctx404.newPage();
    await page404.route('**/api/dms/pick/data*', (route) =>
        route.fulfill({ status: 404, json: { detail: 'dms_pick.not_found' } })
    );
    await page404.goto(`http://localhost:${PORT}/static/dist/dms-pick.html?t=x`);
    await page404.waitForSelector('.state.err', { timeout: 5000 });
    await shot(page404, '05-err-404-not-enabled.png');
    await ctx404.close();

    // A4) 空车型态
    const ctxEmpty = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const pageEmpty = await ctxEmpty.newPage();
    await pageEmpty.route('**/api/dms/pick/data*', (route) =>
        route.fulfill({
            json: { ok: true, customer: { name: 'x' }, cars: [], advisors: [], defaults: {} },
        })
    );
    await pageEmpty.goto(`http://localhost:${PORT}/static/dist/dms-pick.html?t=y`);
    await pageEmpty.waitForSelector('.muted', { timeout: 5000 });
    await shot(pageEmpty, '06-empty-no-cars.png');
    await ctxEmpty.close();

    console.log('Part A: PASS');
}

// ── Part B: /dms SPA(向导 admin 两键 + LINE 绑定卡)── stub 登录/门禁/erp/line。
async function verifyDmsSpa(browser) {
    console.log('== Part B: /dms SPA ==');
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await ctx.newPage();

    await page.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'faketoken');
        localStorage.setItem('mrpilot_lang', 'th');
    });
    await page.route('**/api/dms/session', (route) => route.fulfill({ json: { ok: true } }));
    await page.route('**/api/erp/endpoints', (route) =>
        route.fulfill({
            json: {
                items: [
                    {
                        id: 'ep1',
                        adapter: 'mrerp_dms',
                        enabled: true,
                        config: {
                            id_card_auto_push: true,
                            admin_username_enc: 'gAAAAA-fake-ciphertext',
                        },
                    },
                ],
            },
        })
    );
    let bindGenerated = false;
    await page.route('**/api/dms/line/binding', (route) => {
        if (route.request().method() === 'DELETE') return route.fulfill({ json: { ok: true } });
        route.fulfill({
            json: bindGenerated
                ? { bound: false, display_name: null, bound_at: null }
                : { bound: false, display_name: null, bound_at: null },
        });
    });
    await page.route('**/api/dms/line/bind-code', (route) => {
        bindGenerated = true;
        const exp = new Date(Date.now() + 9 * 60000 + 59000).toISOString();
        route.fulfill({ json: { code: '482913', expires_at: exp } });
    });

    await page.goto(`http://localhost:${PORT}/static/dist/dms.html`);
    await page.waitForSelector('#dx-erp-cards .dx-erp-card', { timeout: 8000 });
    await page.waitForSelector('.dms-line-card', { timeout: 8000 });

    const erpBadgeVisible = await page.locator('.dx-erp-status').isVisible();
    assert(erpBadgeVisible, 'erp card status visible');
    const erpStatusText = await page.locator('.dx-erp-status').textContent();
    assert(erpStatusText.includes('แอดมิน'), 'erp card shows admin badge, got: ' + erpStatusText);

    const genBtn = page.locator('#dms-line-gen-btn');
    assert(await genBtn.isVisible(), 'LINE generate-code button visible (unbound state)');
    await shot(page, '07-dms-spa-cards-unbound.png');

    await genBtn.click();
    await page.waitForSelector('.dms-line-code', { timeout: 5000 });
    const codeText = await page.locator('.dms-line-code').textContent();
    assert(codeText.trim() === '482913', '6-digit code shown, got: ' + codeText);
    await page.waitForFunction(
        () => (document.getElementById('dms-line-countdown') || {}).textContent > ''
    );
    const countdownText = await page.locator('#dms-line-countdown').textContent();
    assert(/\d:\d\d/.test(countdownText), 'countdown mm:ss shown, got: ' + countdownText);
    const codeColor = await page
        .locator('.dms-line-code')
        .evaluate((el) => getComputedStyle(el).color);
    assert(codeColor === 'rgb(47, 107, 255)', 'active code uses brand blue, got ' + codeColor);
    await shot(page, '08-dms-spa-line-code-countdown.png');

    // 向导:打开配置 → admin 两键的占位符提示「已配置」→ 填新值保存 → 断言请求体 config 下两键。
    await page.locator('[data-erp-config]').click();
    await page.waitForSelector('#dms-w-admin-user', { timeout: 5000 });
    const adminPh = await page.locator('#dms-w-admin-user').getAttribute('placeholder');
    assert(adminPh.includes('กำหนดค่าแล้ว'), 'admin field shows configured hint, got: ' + adminPh);
    await shot(page, '09-wizard-admin-fields.png');

    await page.route('**/api/erp/test-connection', (route) =>
        route.fulfill({ json: { ok: true } })
    );
    let saveBody = null;
    await page.route('**/api/erp/endpoints/ep1', async (route, req) => {
        saveBody = JSON.parse(req.postData());
        route.fulfill({ json: { ok: true } });
    });
    page.on('pageerror', (e) => console.log('  [pageerror]', e.message));
    await page.locator('#dms-w-user').fill('dmsuser');
    await page.locator('#dms-w-pass').fill('dmspass');
    await page.locator('#dms-w-admin-user').fill('admin1');
    await page.locator('#dms-w-admin-pass').fill('adminpass1');
    await page.locator('#dms-w-save').click();
    try {
        await page.waitForFunction(() => !document.getElementById('dms-wizard-overlay'), null, {
            timeout: 5000,
        });
    } catch (e) {
        const errText = await page
            .locator('#dms-w-err')
            .textContent()
            .catch(() => '(n/a)');
        console.log('  [wizErr text]', errText);
        throw e;
    }
    assert(saveBody, 'save request captured');
    console.log('  [saveBody.config]', JSON.stringify(saveBody.config));
    assert(
        saveBody.config.admin_username_enc === 'admin1',
        'admin_username_enc in config, got: ' + JSON.stringify(saveBody.config)
    );
    assert(saveBody.config.admin_password_enc === 'adminpass1', 'admin_password_enc in config');

    await ctx.close();
    console.log('Part B: PASS');
}

// 共用 stub:门禁通过 + 一个已配 admin 的 mrerp_dms 端点 + LINE 未绑定态。
async function stubDmsSpaRoutes(page) {
    await page.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'faketoken');
        localStorage.setItem('mrpilot_lang', 'th');
    });
    await page.route('**/api/dms/session', (route) => route.fulfill({ json: { ok: true } }));
    await page.route('**/api/erp/endpoints', (route) =>
        route.fulfill({
            json: {
                items: [
                    {
                        id: 'ep1',
                        adapter: 'mrerp_dms',
                        enabled: true,
                        config: { id_card_auto_push: true, admin_username_enc: 'gAAAAA-fake' },
                    },
                ],
            },
        })
    );
    await page.route('**/api/dms/line/binding', (route) =>
        route.fulfill({ json: { bound: false, display_name: null, bound_at: null } })
    );
    await page.route('**/api/dms/line/bind-code', (route) => {
        const exp = new Date(Date.now() + 9 * 60000 + 59000).toISOString();
        route.fulfill({ json: { code: '482913', expires_at: exp } });
    });
}

// ── Part C: R1 追加 · LINE 绑定卡桌面端(≥768px)收窄验证(1280 宽)+ 手机端(390)不变复核。
async function verifyLineCardWidths(browser) {
    console.log('== Part C: LINE card width (desktop narrow / mobile unchanged) ==');

    // C1) 桌面 1280×900:卡片本身跟着宽容器拉满,但码框 + 按钮应收窄到 <=400px 列宽。
    const deskCtx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const deskPage = await deskCtx.newPage();
    await stubDmsSpaRoutes(deskPage);
    await deskPage.goto(`http://localhost:${PORT}/static/dist/dms.html`);
    await deskPage.waitForSelector('.dms-line-card', { timeout: 8000 });
    await deskPage.locator('#dms-line-gen-btn').click();
    await deskPage.waitForSelector('.dms-line-code', { timeout: 5000 });

    const cardBox = await deskPage.locator('.dms-line-card').boundingBox();
    const zoneBox = await deskPage.locator('#dms-line-code-zone').boundingBox();
    const genBox = await deskPage.locator('#dms-line-gen-btn').boundingBox();
    assert(
        cardBox.width > 600,
        'desktop card itself is wide (unconstrained), got ' + cardBox.width
    );
    assert(
        zoneBox.width <= 410,
        'code zone narrowed to ~400px column on desktop, got ' + zoneBox.width
    );
    assert(
        genBox.width <= 410,
        'regenerate button narrowed to ~400px column on desktop, got ' + genBox.width
    );
    // 左对齐随卡内文案:码框左边不应比卡片本身左边内边距差太多(不是被居中推到中间)。
    assert(
        zoneBox.x - cardBox.x < 40,
        'code zone stays left-aligned with card padding, offset=' + (zoneBox.x - cardBox.x)
    );
    await shot(deskPage, '10-desktop-1280-line-card-narrowed.png');
    await deskCtx.close();
    console.log(
        '  desktop: card=' +
            cardBox.width.toFixed(0) +
            'px, code-zone=' +
            zoneBox.width.toFixed(0) +
            'px, button=' +
            genBox.width.toFixed(0) +
            'px'
    );

    // C2) 手机 390×844:同一套 stub,确认没有被桌面 @media 误伤,依旧全宽贴满卡片。
    const mobCtx = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const mobPage = await mobCtx.newPage();
    await stubDmsSpaRoutes(mobPage);
    await mobPage.goto(`http://localhost:${PORT}/static/dist/dms.html`);
    await mobPage.waitForSelector('.dms-line-card', { timeout: 8000 });
    await mobPage.locator('#dms-line-gen-btn').click();
    await mobPage.waitForSelector('.dms-line-code', { timeout: 5000 });
    const mobCardBox = await mobPage.locator('.dms-line-card').boundingBox();
    const mobZoneBox = await mobPage.locator('#dms-line-code-zone').boundingBox();
    assert(
        mobZoneBox.width > mobCardBox.width - 40,
        'mobile code zone still fills the card (unaffected by desktop @media), zone=' +
            mobZoneBox.width +
            ' card=' +
            mobCardBox.width
    );
    await shot(mobPage, '11-mobile-390-line-card-unchanged.png');
    await mobCtx.close();
    console.log(
        '  mobile: card=' +
            mobCardBox.width.toFixed(0) +
            'px, code-zone=' +
            mobZoneBox.width.toFixed(0) +
            'px'
    );

    // C3) 已绑定态(desktop):restructure 后 boundBodyHtml/boundActionHtml 两条新分支
    // 之前没截过图——解绑按钮应同样落进标题行、同款紧凑 pill,不该悄悄裂开。
    const boundCtx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const boundPage = await boundCtx.newPage();
    await boundPage.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'faketoken');
        localStorage.setItem('mrpilot_lang', 'th');
    });
    await boundPage.route('**/api/dms/session', (route) => route.fulfill({ json: { ok: true } }));
    await boundPage.route('**/api/erp/endpoints', (route) =>
        route.fulfill({ json: { items: [] } })
    );
    await boundPage.route('**/api/dms/line/binding', (route) =>
        route.fulfill({
            json: { bound: true, display_name: 'Somchai (LINE)', bound_at: '2026-07-15T03:00:00Z' },
        })
    );
    await boundPage.goto(`http://localhost:${PORT}/static/dist/dms.html`);
    await boundPage.waitForSelector('#dms-line-unbind-btn', { timeout: 8000 });
    const unbindBox = await boundPage.locator('#dms-line-unbind-btn').boundingBox();
    assert(
        unbindBox.width <= 200,
        'bound-state unbind button is compact pill, got ' + unbindBox.width
    );
    const unbindColor = await boundPage
        .locator('#dms-line-unbind-btn')
        .evaluate((el) => getComputedStyle(el).color);
    assert(unbindColor === 'rgb(214, 88, 106)', 'unbind stays red-tinted, got ' + unbindColor);
    await shot(boundPage, '12-desktop-1280-line-card-bound-state.png');
    await boundCtx.close();
    console.log('  bound-state desktop unbind button width=' + unbindBox.width.toFixed(0) + 'px');

    console.log('Part C: PASS');
}

(async () => {
    const server = serve();
    const browser = await chromium.launch();
    try {
        await verifyPickPanel(browser);
        await verifyDmsSpa(browser);
        await verifyLineCardWidths(browser);
        console.log('\nALL DL-4b CHECKS PASSED');
    } finally {
        await browser.close();
        server.close();
    }
})().catch((e) => {
    console.error(e);
    process.exit(1);
});
