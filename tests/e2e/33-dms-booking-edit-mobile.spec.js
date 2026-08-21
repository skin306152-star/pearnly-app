const fs = require('fs');
const path = require('path');
const { test, expect } = require('@playwright/test');
const localServer = require('./_local_static_server');

const PORT = 8994;
const BASE = `http://127.0.0.1:${PORT}`;
const OUT = path.join(__dirname, '_artifacts', 'dms-booking-edit');
fs.mkdirSync(OUT, { recursive: true });

let server;
test.beforeAll(async () => {
    server = await localServer.start(PORT, '/static/dist/dms-booking-edit.html');
});
test.afterAll(() => localServer.stop(server));

const DRAFT = {
    form: {
        advisor: { name: 'dmstest' },
        customer: {
            prefix_id: '',
            name: 'Mobile Layout',
            people_id: '1101700998118',
            birthday_be: '15/05/2530',
            phone: '0811111111',
        },
        answers: {},
        payments: [{ channel: 'cash', amount: '90000.00', extra: {} }],
        files: { id_card: true, slip: true },
    },
    masters: {
        prefixes: [],
        places: [],
        cars: [],
        paints: [],
        terms: [],
        regis: [],
        company_banks: [],
    },
};

const PREFIX_DRAFT = {
    ...DRAFT,
    masters: {
        ...DRAFT.masters,
        prefixes: [
            { id: '17', label: 'นาย' },
            { id: '18', label: 'น.ส.' },
            { id: '19', label: 'คุณ' },
        ],
    },
};

const GEO_DRAFT = {
    ...DRAFT,
    form: {
        ...DRAFT.form,
        customer: {
            ...DRAFT.form.customer,
            province_id: '1',
            district_id: '18',
            subdistrict_id: '72',
            zipcode_id: '197',
        },
    },
};

const GEO = {
    provinces: [
        { id: '1', label: 'กรุงเทพมหานคร' },
        { id: '65', label: 'กระบี่' },
    ],
    districts: {
        1: [{ id: '18', label: 'คลองสาน' }],
        65: [{ id: '804', label: 'คลองท่อม' }],
    },
    subdistricts: {
        18: [{ id: '72', label: 'คลองต้นไทร' }],
        804: [{ id: '6472', label: 'คลองท่อมเหนือ' }],
    },
    zipcodes: {
        72: [{ id: '197', label: '10600' }],
        6472: [{ id: '6477', label: '81120' }],
    },
};

test('LINE portal authenticates and opens the DMS portal', async ({ page }) => {
    let authBody;
    const payload = Buffer.from(
        JSON.stringify({ entry: 'dms', exp: Math.floor(Date.now() / 1000) + 3600 })
    ).toString('base64url');
    const token = `e2e.${payload}.sig`;

    await page.route('https://static.line-scdn.net/**', (route) =>
        route.fulfill({
            contentType: 'application/javascript',
            body: `window.liff={init:async()=>{},isLoggedIn:()=>true,getIDToken:()=>"LINE-ID-TOKEN",isInClient:()=>false};`,
        })
    );
    await page.route('**/api/line/dms-booking/config', (route) =>
        route.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, data: { liff_id: 'DMS-LIFF' } }),
        })
    );
    await page.route('**/api/line/dms-booking/auth', async (route) => {
        authBody = route.request().postDataJSON();
        await route.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, data: { token } }),
        });
    });
    await page.route('**/dms', (route) =>
        route.fulfill({ contentType: 'text/html', body: '<h1 id="dms-portal">DMS portal</h1>' })
    );

    await page.goto(`${BASE}/static/dist/dms-booking-edit.html?portal=dms`);
    await expect(page).toHaveURL(`${BASE}/dms`);
    await expect(page.locator('#dms-portal')).toBeVisible();
    expect(authBody).toEqual({ id_token: 'LINE-ID-TOKEN' });
    expect(await page.evaluate(() => localStorage.getItem('mrpilot_token'))).toBe(token);
});

test('mobile payment and attachment controls stay aligned', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.addInitScript(() => {
        const payload = btoa(
            JSON.stringify({ entry: 'dms', exp: Math.floor(Date.now() / 1000) + 3600 })
        )
            .replace(/=/g, '')
            .replace(/\+/g, '-')
            .replace(/\//g, '_');
        localStorage.setItem('mrpilot_token', `e2e.${payload}.sig`);
        localStorage.setItem('pearnly_lang', 'zh');
    });
    await page.route('**/api/line/dms-booking/**', (route) => {
        const url = route.request().url();
        const data = url.includes('/draft') ? DRAFT : [];
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, data }),
        });
    });

    await page.goto(`${BASE}/static/dist/dms-booking-edit.html?draft=layout-test`);
    await page.waitForSelector('#editor:not([hidden])');

    const boxes = await page
        .locator('.payment, .pay-channel, .amount, .remove')
        .evaluateAll((elements) =>
            elements.map((element) => {
                const rect = element.getBoundingClientRect();
                return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
            })
        );
    const [payment, channel, amount, remove] = boxes;
    expect(Math.abs(channel.y + channel.height - (remove.y + remove.height))).toBeLessThanOrEqual(
        1
    );
    expect(amount.width).toBeGreaterThan(payment.width * 0.9);

    const switches = await page.locator('.switch').evaluateAll((elements) =>
        elements.map((element) => {
            const rect = element.getBoundingClientRect();
            return { x: rect.x, width: rect.width, height: rect.height };
        })
    );
    expect(switches).toHaveLength(2);
    for (const control of switches) {
        expect(control.width).toBe(22);
        expect(control.height).toBe(22);
    }
    expect(Math.abs(switches[0].x - switches[1].x)).toBeLessThanOrEqual(1);

    await page.screenshot({ path: path.join(OUT, 'mobile-controls.png'), fullPage: true });
});

test('booking editor exposes every live DMS title option', async ({ page }) => {
    await page.addInitScript(() => {
        const payload = btoa(
            JSON.stringify({ entry: 'dms', exp: Math.floor(Date.now() / 1000) + 3600 })
        )
            .replace(/=/g, '')
            .replace(/\+/g, '-')
            .replace(/\//g, '_');
        localStorage.setItem('mrpilot_token', `e2e.${payload}.sig`);
        localStorage.setItem('pearnly_lang', 'zh');
    });
    await page.route('**/api/line/dms-booking/**', (route) => {
        const data = route.request().url().includes('/draft') ? PREFIX_DRAFT : [];
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, data }),
        });
    });

    for (const viewport of [
        { width: 390, height: 844 },
        { width: 1280, height: 900 },
    ]) {
        await page.setViewportSize(viewport);
        await page.goto(`${BASE}/static/dist/dms-booking-edit.html?draft=prefix-${viewport.width}`);
        await page.waitForSelector('#editor:not([hidden])');
        await expect(page.locator('#prefix_id option')).toHaveCount(
            PREFIX_DRAFT.masters.prefixes.length
        );
        await expect(page.locator('#prefix_id option[value="18"]')).toHaveText('น.ส.');
        await expect(page.locator('#prefix_id option[value="19"]')).toHaveText('คุณ');
        await page.locator('#prefix_id').selectOption('19');
        await expect(page.locator('#prefix_id')).toHaveValue('19');
        const state = await page.locator('#prefix_id').evaluate((element) => {
            const style = element.ownerDocument.defaultView.getComputedStyle(element);
            return { visible: element.getBoundingClientRect().height > 0, display: style.display };
        });
        expect(state.visible).toBe(true);
        expect(state.display).not.toBe('none');
        await page.screenshot({
            path: path.join(OUT, `prefix-options-${viewport.width}.png`),
            fullPage: true,
        });
    }
});

test('master-data save errors are actionable on mobile and desktop', async ({ page }) => {
    const message = '可选项目已更新，请使用 LINE 中的最新预览卡后重试。';
    await page.addInitScript(() => {
        const payload = btoa(
            JSON.stringify({ entry: 'dms', exp: Math.floor(Date.now() / 1000) + 3600 })
        )
            .replace(/=/g, '')
            .replace(/\+/g, '-')
            .replace(/\//g, '_');
        localStorage.setItem('mrpilot_token', `e2e.${payload}.sig`);
        localStorage.setItem('pearnly_lang', 'zh');
    });
    await page.route('**/api/line/dms-booking/**', (route) => {
        if (route.request().method() === 'POST') {
            return route.fulfill({
                status: 400,
                contentType: 'application/json',
                body: JSON.stringify({
                    ok: false,
                    error: {
                        code: 'dms_booking.invalid_master',
                        detail: 'dms_booking.invalid_master',
                    },
                }),
            });
        }
        const url = route.request().url();
        const data = url.includes('/draft') ? DRAFT : [];
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, data }),
        });
    });

    for (const viewport of [
        { width: 390, height: 844 },
        { width: 1280, height: 900 },
    ]) {
        await page.setViewportSize(viewport);
        await page.goto(`${BASE}/static/dist/dms-booking-edit.html?draft=error-${viewport.width}`, {
            waitUntil: 'domcontentloaded',
        });
        await page.waitForSelector('#editor:not([hidden])');
        await page.waitForSelector('#save:not([disabled])');
        await page.locator('#save').click();
        const error = page.locator('#form-error');
        await expect(error).toBeVisible();
        await expect(error).toHaveText(message);
        const state = await error.evaluate((element) => {
            const style = element.ownerDocument.defaultView.getComputedStyle(element);
            return { visible: element.getBoundingClientRect().height > 0, color: style.color };
        });
        expect(state.visible).toBe(true);
        expect(state.color).toBeTruthy();
        await page.screenshot({
            path: path.join(OUT, `master-error-${viewport.width}.png`),
            fullPage: true,
        });
    }
});

test('geo master selects stay populated through the cascade', async ({ page }) => {
    await page.addInitScript(() => {
        const payload = btoa(
            JSON.stringify({ entry: 'dms', exp: Math.floor(Date.now() / 1000) + 3600 })
        )
            .replace(/=/g, '')
            .replace(/\+/g, '-')
            .replace(/\//g, '_');
        localStorage.setItem('mrpilot_token', `e2e.${payload}.sig`);
        localStorage.setItem('pearnly_lang', 'zh');
    });
    await page.route('**/api/line/dms-booking/**', (route) => {
        const url = new URL(route.request().url());
        let data = [];
        if (url.pathname.endsWith('/draft')) data = GEO_DRAFT;
        if (url.pathname.endsWith('/geo')) {
            const level = url.searchParams.get('level');
            const parent = url.searchParams.get('parent_id') || '';
            data = level === 'provinces' ? GEO.provinces : GEO[level]?.[parent] || [];
        }
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, data }),
        });
    });

    for (const viewport of [
        { width: 390, height: 844 },
        { width: 1280, height: 900 },
    ]) {
        await page.setViewportSize(viewport);
        await page.goto(`${BASE}/static/dist/dms-booking-edit.html?draft=geo-${viewport.width}`);
        await page.waitForSelector('#editor:not([hidden])');
        await page.waitForSelector('#save:not([disabled])');
        await page.locator('#province_id').selectOption('65');
        await expect(page.locator('#district_id')).toHaveValue('804');
        await page.locator('#district_id').selectOption('804');
        await expect(page.locator('#subdistrict_id')).toHaveValue('6472');
        await page.locator('#subdistrict_id').selectOption('6472');
        await expect(page.locator('#zipcode_id')).toHaveValue('6477');
        await expect(page.locator('#province_id option')).not.toHaveCount(0);
        await expect(page.locator('#district_id option')).not.toHaveCount(0);
        await expect(page.locator('#subdistrict_id option')).not.toHaveCount(0);
        await expect(page.locator('#zipcode_id option')).not.toHaveCount(0);
        await page.screenshot({
            path: path.join(OUT, `geo-selects-${viewport.width}.png`),
            fullPage: true,
        });
    }
});
