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
