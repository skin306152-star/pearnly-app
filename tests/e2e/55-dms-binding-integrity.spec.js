const { test, expect } = require('@playwright/test');
const path = require('path');

const root = path.resolve(__dirname, '../..');
const shell = path.join(root, 'static/dist/dms-booking-edit.html');
const artifact = (name) => path.join(__dirname, '_artifacts/dms-binding-integrity', name);

async function fixture(page, mode = 'credentials', language = 'th') {
    const state = {
        binding: 'B',
        authCount: 0,
        puts: [],
        tickets: [],
        records: { A: 'old-A', B: 'old-B' },
    };
    await page.addInitScript(
        ({ language }) => {
            localStorage.setItem('mrpilot_token', 'OLD_SHARED_TOKEN_A');
            localStorage.setItem('pearnly_lang', language);
        },
        { language }
    );
    await page.route('https://static.line-scdn.net/**', (route) =>
        route.fulfill({
            contentType: 'application/javascript',
            body: "window.liff={init:async()=>{},isLoggedIn:()=>true,getIDToken:()=> 'verified-LINE-user',isInClient:()=>false};",
        })
    );
    await page.route('**/home/dms-booking?**', (route) =>
        route.fulfill({ path: shell, contentType: 'text/html' })
    );
    await page.route('**/api/line/**', async (route) => {
        const request = route.request();
        const pathname = new URL(request.url()).pathname;
        const token = request.headers().authorization;
        let data;
        if (pathname.endsWith('/config')) data = { liff_id: 'test-liff' };
        else if (pathname.endsWith('/auth')) {
            expect(request.postDataJSON()).toEqual({ id_token: 'verified-LINE-user' });
            state.authCount++;
            data = { token: `FRESH_BINDING_${state.binding}` };
        } else {
            if (token !== `Bearer FRESH_BINDING_${state.binding}`) {
                return route.fulfill({
                    status: 401,
                    json: {
                        ok: false,
                        error: { code: 'dms_booking.not_bound', detail: 'line_binding_changed' },
                    },
                });
            }
            if (pathname.endsWith('/dms-credentials')) {
                if (request.method() === 'PUT') {
                    state.puts.push({ token, body: request.postDataJSON() });
                    state.records[state.binding] = request.postDataJSON().password;
                    data = { updated: true };
                } else data = { username: 'operator-B' };
            } else if (pathname.endsWith('/ticket')) {
                state.tickets.push(token);
                data = { url: '/test-portal-complete', expires_at: '2099-01-01T00:00:00Z' };
            } else throw new Error(`Unexpected DMS API: ${pathname}`);
        }
        return route.fulfill({ json: { ok: true, data } });
    });
    await page.route('**/test-portal-complete', (route) =>
        route.fulfill({
            contentType: 'text/html',
            body: '<p>Portal opened for current binding</p>',
        })
    );
    await page.goto(`/home/dms-booking?${mode}=dms`);
    return state;
}

async function fillCredentials(page) {
    await expect(page.locator('#credentials-username')).toHaveValue('operator-B');
    await page.locator('#credentials-password').fill('new-test-password-B');
    await page.locator('#credentials-confirm').fill('new-test-password-B');
}

for (const [device, viewport] of [
    ['mobile', { width: 430, height: 932 }],
    ['desktop', { width: 1280, height: 800 }],
]) {
    test(`menu 4 ignores old browser account and saves current LINE binding (${device})`, async ({
        page,
    }) => {
        await page.setViewportSize(viewport);
        const state = await fixture(page);
        await fillCredentials(page);
        await page.locator('#credentials-save').click();
        await expect(page.locator('#credentials-done')).toBeVisible();
        expect(state.authCount).toBe(1);
        expect(state.puts).toHaveLength(1);
        expect(state.puts[0].token).toBe('Bearer FRESH_BINDING_B');
        expect(state.records).toEqual({ A: 'old-A', B: 'new-test-password-B' });
        expect(await page.evaluate(() => localStorage.getItem('mrpilot_token'))).toBe(
            'OLD_SHARED_TOKEN_A'
        );
        await page.screenshot({
            path: artifact(`credentials-current-${device}.png`),
            fullPage: true,
        });
    });
}

for (const language of ['th', 'en', 'zh', 'ja']) {
    test(`an open form stops after rebind and never retries under another user (${language})`, async ({
        page,
    }) => {
        await page.setViewportSize({ width: 430, height: 932 });
        const state = await fixture(page, 'credentials', language);
        await fillCredentials(page);
        state.binding = 'C';
        await page.locator('#credentials-save').click();
        const expected = await page.evaluate(
            (lang) => globalThis.DMS_CREDENTIALS_TEXT[lang].bindingChanged,
            language
        );
        await expect(page.locator('#credentials-error')).toHaveText(expected);
        expect(state.authCount).toBe(1);
        expect(state.puts).toHaveLength(0);
        expect(state.records).toEqual({ A: 'old-A', B: 'old-B' });
        await expect(page.locator('#credentials-done')).toHaveCount(0);
        expect(
            await page.evaluate(
                () => globalThis.document.documentElement.scrollWidth <= globalThis.innerWidth
            )
        ).toBe(true);
        await page.screenshot({
            path: artifact(`credentials-rebound-${language}.png`),
            fullPage: true,
        });
    });
}

test('menu 3 also exchanges current LINE identity before requesting its ticket', async ({
    page,
}) => {
    const state = await fixture(page, 'portal');
    await expect(page).toHaveURL(/test-portal-complete$/);
    expect(state.authCount).toBe(1);
    expect(state.tickets).toEqual(['Bearer FRESH_BINDING_B']);
});
