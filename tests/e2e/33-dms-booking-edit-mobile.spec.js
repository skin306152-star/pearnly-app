const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
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

function liffMockScript() {
    return `window.__dmsPortalOpen=null;window.__dmsPortalClosed=false;window.liff={init:async()=>{},isLoggedIn:()=>true,getIDToken:()=>"LINE-ID-TOKEN",isInClient:()=>true,openWindow:(params)=>{window.__dmsPortalOpen=params;},closeWindow:()=>{window.__dmsPortalClosed=true;}};`;
}

const PORTAL_CHAT_HTML = `<!doctype html><html lang="th"><head><meta charset="utf-8"><style>
    body{margin:0;background:#171717;color:#fff;font-family:system-ui,sans-serif}.chat{min-height:100vh;padding:28px 14px 210px;box-sizing:border-box}.bubble{margin:20px 0 0 auto;max-width:78%;padding:12px 16px;border-radius:18px;background:#6ee787;color:#102416}.menu{position:fixed;left:0;right:0;bottom:0;display:grid;grid-template-columns:repeat(3,1fr);background:#f8f4ff;color:#30295f}.cell{height:94px;display:grid;place-items:center;text-align:center;border:1px solid #ddd5ff;color:inherit;text-decoration:none;font-weight:700}.placeholder{color:#aaa}
</style></head><body><main class="chat"><div class="bubble">เลือกเมนูที่ต้องการได้เลยครับ</div></main><nav class="menu" aria-label="เมนู DMS">
    <a class="cell" href="#customer">สร้างลูกค้า</a><a class="cell" href="#booking">สร้างการจองรถ</a><a id="dms-menu" class="cell" href="${BASE}/home?liff.state=%3Fportal%3Ddms">เข้าสู่ DMS</a>
    <a id="credentials-menu" class="cell" href="${BASE}/home?liff.state=%3Fcredentials%3Ddms">เปลี่ยนบัญชีและรหัสผ่าน</a><span class="cell placeholder">—</span><span class="cell placeholder">—</span>
</nav></body></html>`;

async function setupPortalTest(page) {
    let authBody;
    let ticketRequested = false;
    let ticketRequestCount = 0;
    await page.addInitScript(() => {
        try {
            localStorage.setItem('pearnly_lang', 'zh');
        } catch (_) {
            // The initial synthetic chat document has an opaque origin.
        }
    });
    const payload = Buffer.from(
        JSON.stringify({ entry: 'dms', exp: Math.floor(Date.now() / 1000) + 3600 })
    ).toString('base64url');
    const token = `e2e.${payload}.sig`;

    await page.route('https://static.line-scdn.net/**', (route) =>
        route.fulfill({ contentType: 'application/javascript', body: liffMockScript() })
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
    await page.route('**/api/line/dms-portal/ticket', async (route) => {
        ticketRequested = true;
        ticketRequestCount += 1;
        expect(route.request().method()).toBe('POST');
        await route.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({
                ok: true,
                data: { url: '/line/dms-portal?ticket=opaque-ticket' },
            }),
        });
    });
    await page.route(/\/home\?liff\.state=/, (route) =>
        route.fulfill({
            status: 302,
            headers: { location: `${BASE}/static/dist/dms-booking-edit.html?portal=dms` },
        })
    );
    return {
        authBody: () => authBody,
        ticketRequested: () => ticketRequested,
        ticketRequestCount: () => ticketRequestCount,
        token,
    };
}

test('LINE always opens MRERP DMS in external browser and closes launcher', async ({ page }) => {
    const h = await setupPortalTest(page);
    await page.setViewportSize({ width: 390, height: 844 });
    await page.setContent(PORTAL_CHAT_HTML);
    await page.screenshot({ path: path.join(OUT, 'portal-before-click-390.png') });
    await page.locator('#dms-menu').click();
    await expect
        .poll(() => page.evaluate(() => globalThis.__dmsPortalOpen))
        .toEqual({
            url: `${BASE}/line/dms-portal?ticket=opaque-ticket`,
            external: true,
        });
    await expect.poll(() => page.evaluate(() => globalThis.__dmsPortalClosed)).toBe(true);
    expect(h.ticketRequested()).toBe(true);
    expect(h.ticketRequestCount()).toBe(1);
    expect(await page.evaluate(() => localStorage.getItem('mrerp_password'))).toBeNull();
    await page.screenshot({
        path: path.join(OUT, 'portal-external-close-390.png'),
        fullPage: true,
    });
});

test('second menu click issues a fresh ticket after closeWindow', async ({ page }) => {
    const h = await setupPortalTest(page);
    await page.setViewportSize({ width: 390, height: 844 });
    await page.setContent(PORTAL_CHAT_HTML);
    await page.locator('#dms-menu').click();
    await expect.poll(() => page.evaluate(() => globalThis.__dmsPortalOpen)).toBeTruthy();
    // Simulate closeWindow returning the user to the LINE chat, then click the
    // menu again to prove a fresh ticket is issued rather than a stale reuse.
    await page.setContent(PORTAL_CHAT_HTML);
    await page.locator('#dms-menu').click();
    await expect
        .poll(() => page.evaluate(() => globalThis.__dmsPortalOpen))
        .toEqual({
            url: `${BASE}/line/dms-portal?ticket=opaque-ticket`,
            external: true,
        });
    await expect.poll(() => page.evaluate(() => globalThis.__dmsPortalClosed)).toBe(true);
    expect(h.ticketRequestCount()).toBe(2);
});

test('menu 4 opens the operator credential editor and saves only the entered pair', async ({
    page,
}) => {
    let updateBody;
    let updateCount = 0;
    await page.setViewportSize({ width: 390, height: 844 });
    await page.addInitScript(() => {
        const payload = btoa(
            JSON.stringify({ entry: 'dms', exp: Math.floor(Date.now() / 1000) + 3600 })
        )
            .replace(/=/g, '')
            .replace(/\+/g, '-')
            .replace(/\//g, '_');
        localStorage.setItem('mrpilot_token', `e2e.${payload}.sig`);
        localStorage.setItem('pearnly_lang', 'th');
    });
    await page.route('**/api/line/dms-credentials', async (route) => {
        if (route.request().method() === 'GET') {
            return route.fulfill({
                contentType: 'application/json',
                body: JSON.stringify({ ok: true, data: { username: 'sale02' } }),
            });
        }
        updateCount += 1;
        updateBody = route.request().postDataJSON();
        return route.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, data: { updated: true } }),
        });
    });
    await page.route(/\/home\?liff\.state=.*credentials/, (route) =>
        route.fulfill({
            status: 302,
            headers: {
                location: `${BASE}/static/dist/dms-booking-edit.html?credentials=dms`,
            },
        })
    );

    await page.setContent(PORTAL_CHAT_HTML);
    await page.locator('#credentials-menu').click();
    await expect(page.locator('#credentials-username')).toBeVisible();
    await expect(page.locator('#credentials-username')).toHaveValue('sale02');
    await expect(page.locator('#credentials-password')).toHaveValue('');
    await expect(page.locator('body')).not.toContainText('secret');

    await page.locator('#credentials-password').click();
    await page.keyboard.type('updated-pass');
    expect(await page.evaluate(() => globalThis.document.activeElement.id)).toBe(
        'credentials-password'
    );
    await page.locator('#credentials-confirm').click();
    await page.keyboard.type('wrong-pass');
    await page.locator('#credentials-save').click();
    await expect(page.locator('#credentials-error')).toContainText('ไม่ตรงกัน');
    expect(updateCount).toBe(0);

    await page.locator('#credentials-confirm').fill('');
    await page.locator('#credentials-confirm').click();
    await page.keyboard.type('updated-pass');
    await page.screenshot({
        path: path.join(OUT, 'credentials-editor-390.png'),
        fullPage: true,
    });
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.screenshot({
        path: path.join(OUT, 'credentials-editor-1280.png'),
        fullPage: true,
    });
    await page.setViewportSize({ width: 390, height: 844 });

    for (const language of ['en', 'zh', 'ja', 'th']) {
        await page.locator('#language').selectOption(language);
        await expect(page.locator('.credentials-editor h1')).not.toBeEmpty();
        expect(
            await page.evaluate(
                () => globalThis.document.documentElement.scrollWidth <= globalThis.innerWidth
            )
        ).toBe(true);
    }
    await page.locator('#credentials-save').click();
    await expect(page.locator('#credentials-done')).toBeVisible();
    expect(updateCount).toBe(1);
    expect(updateBody).toEqual({ username: 'sale02', password: 'updated-pass' });
    await page.screenshot({
        path: path.join(OUT, 'credentials-saved-390.png'),
        fullPage: true,
    });
});

test('external relay logs in through a top-level MRERP window', async ({ page, context }) => {
    const relayHtml = execFileSync(
        'python',
        [
            '-c',
            'from services.line_dms.mrerp_portal import render_login_relay; print(render_login_relay("staff", "secret")[0])',
        ],
        {
            cwd: path.join(__dirname, '..', '..'),
            encoding: 'utf8',
            env: { ...process.env, PYTHONUTF8: '1' },
        }
    );
    const requests = [];
    await context.route(/https:\/\/www\.mrerp4sme\.com\/dms(?:\/.*)?$/, async (route) => {
        const request = route.request();
        requests.push({ url: request.url(), method: request.method(), body: request.postData() });
        if (request.url().includes('checklogin.php')) {
            return route.fulfill({ contentType: 'text/plain', body: 'lct::2::1' });
        }
        if (request.url().includes('home/home.php')) {
            return route.fulfill({
                contentType: 'text/html; charset=utf-8',
                body: '<main id="mrerp-home">เข้าสู่ระบบ DMS สำเร็จ</main>',
            });
        }
        return route.fulfill({
            contentType: 'text/html; charset=utf-8',
            body: '<main id="mrerp-root">ระบบ DMS</main>',
        });
    });

    await page.setViewportSize({ width: 390, height: 844 });
    await page.setContent(relayHtml);
    await expect(page.locator('html')).toHaveAttribute('lang', 'th');
    await expect(page.locator('#open-dms')).toHaveText('เข้าสู่ระบบ DMS');
    await expect(page.locator('iframe')).toHaveCount(0);
    await expect(page.locator('link[rel="dns-prefetch"]')).toHaveAttribute(
        'href',
        'https://www.mrerp4sme.com'
    );
    await expect(page.locator('link[rel="preconnect"]')).toHaveAttribute(
        'href',
        'https://www.mrerp4sme.com'
    );
    await page.screenshot({ path: path.join(OUT, 'portal-thai-confirm-390.png'), fullPage: true });

    await page.setViewportSize({ width: 1280, height: 900 });
    await page.screenshot({ path: path.join(OUT, 'portal-thai-confirm-1280.png'), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });

    const popupPromise = page.waitForEvent('popup');
    await page.locator('#open-dms').click();
    const popup = await popupPromise;
    await expect(popup.locator('#mrerp-home')).toBeVisible({ timeout: 10_000 });
    expect(requests.map((request) => request.url)).toEqual([
        'https://www.mrerp4sme.com/dms/login/checklogin.php',
        'https://www.mrerp4sme.com/dms/home/home.php',
    ]);
    expect(requests[0].method).toBe('POST');
    const loginForm = new URLSearchParams(requests[0].body);
    expect(loginForm.get('txtusers')).toBe('staff');
    expect(loginForm.get('txtpasswords')).toBe('secret');
    expect(loginForm.get('btnsubmit')).toBe('Submit');
    expect(relayHtml).not.toContain('localStorage');
    expect(relayHtml).not.toContain('sessionStorage');
    expect(relayHtml).not.toContain('1800');
    expect(relayHtml).not.toContain('4000');
    expect(relayHtml).not.toContain('document.write');
    expect(relayHtml).not.toContain('setTimeout(goHome');
    await popup.screenshot({ path: path.join(OUT, 'portal-mrerp-home-390.png'), fullPage: true });
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
