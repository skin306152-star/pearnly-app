const { test, expect } = require('@playwright/test');
const path = require('path');

const root = path.resolve(__dirname, '../..');
const shell = path.join(root, 'static/dist/dms-booking-edit.html');
const artifact = (name) => path.join(__dirname, '_artifacts/dms-binding-integrity', name);

async function fixture(page, mode = 'credentials', language = 'th', options = {}) {
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
            body: `window.liff={
                init:async()=>{},isLoggedIn:()=>true,isInClient:()=>false,
                getIDToken:()=> ${options.expired === true} && !sessionStorage.getItem('test-line-renewed') ? 'expired-LINE-token' : 'verified-LINE-user',
                logout:()=>sessionStorage.setItem('test-line-logout-count',String(Number(sessionStorage.getItem('test-line-logout-count')||0)+1)),
                login:()=>{
                    if (${options.renewSucceeds !== false} || sessionStorage.getItem('test-allow-renewal')) sessionStorage.setItem('test-line-renewed','1');
                    location.reload();
                }
            };`,
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
            state.authCount++;
            if (request.postDataJSON().id_token === 'expired-LINE-token') {
                return route.fulfill({
                    status: 401,
                    json: { ok: false, error: { code: 'dms_booking.line_auth_required' } },
                });
            }
            expect(request.postDataJSON()).toEqual({ id_token: 'verified-LINE-user' });
            if (options.unbound)
                return route.fulfill({
                    status: 403,
                    json: { ok: false, error: { code: 'dms_booking.not_bound' } },
                });
            if (options.accountDisabled)
                return route.fulfill({ status: 403, json: { detail: 'auth.account_disabled' } });
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
                } else data = { username: `operator-${state.binding}` };
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

test('expired LINE login renews once before showing an editable credential form', async ({
    page,
}) => {
    const state = await fixture(page, 'credentials', 'zh', { expired: true });
    await fillCredentials(page);
    expect(state.authCount).toBe(2);
    expect(await page.evaluate(() => sessionStorage.getItem('test-line-logout-count'))).toBe('1');
    expect(state.puts).toHaveLength(0);
    await page.locator('#credentials-save').click();
    await expect(page.locator('#credentials-done')).toBeVisible();
    expect(state.records).toEqual({ A: 'old-A', B: 'new-test-password-B' });
});

for (const language of ['th', 'en', 'zh', 'ja']) {
    test(`failed LINE renewal offers explicit recovery without a redirect loop (${language})`, async ({
        page,
    }) => {
        await page.setViewportSize({ width: 430, height: 932 });
        const state = await fixture(page, 'credentials', language, {
            expired: true,
            renewSucceeds: false,
        });
        await expect(page.locator('#credentials-retry')).toBeVisible();
        const expected = await page.evaluate(
            (lang) => globalThis.DMS_CREDENTIALS_TEXT[lang].lineAuthRequired,
            language
        );
        await expect(page.locator('#result h1')).toHaveText(expected);
        expect(state.authCount).toBe(2);
        expect(await page.evaluate(() => sessionStorage.getItem('test-line-logout-count'))).toBe(
            '1'
        );
        expect(state.puts).toHaveLength(0);
        await page.screenshot({
            path: artifact(`line-auth-recovery-${language}.png`),
            fullPage: true,
        });
        await page.evaluate(() => sessionStorage.setItem('test-allow-renewal', '1'));
        await page.locator('#credentials-retry').click();
        await expect(page.locator('#credentials-username')).toHaveValue('operator-B');
        await expect(page.locator('#credentials-password')).toHaveValue('');
        expect(state.puts).toHaveLength(0);
    });
}

test('unbound LINE identity is shown as a binding problem rather than save failure', async ({
    page,
}) => {
    await fixture(page, 'credentials', 'zh', { unbound: true });
    const expected = await page.evaluate(() => globalThis.DMS_CREDENTIALS_TEXT.zh.bindingChanged);
    await expect(page.locator('#result h1')).toHaveText(expected);
    await expect(page.locator('#credentials-retry')).toBeVisible();
});

test('plain HTTP authentication details survive the LINE exchange', async ({ page }) => {
    await fixture(page, 'credentials', 'zh', { accountDisabled: true });
    const expected = await page.evaluate(() => globalThis.DMS_CREDENTIALS_TEXT.zh.operatorInactive);
    await expect(page.locator('#result h1')).toHaveText(expected);
});

test('recovering an old form clears its password and requires a new submission', async ({
    page,
}) => {
    const state = await fixture(page, 'credentials', 'zh');
    await fillCredentials(page);
    state.binding = 'C';
    await page.locator('#credentials-save').click();
    await expect(page.locator('#credentials-retry')).toBeVisible();
    await page.locator('#credentials-retry').click();
    await expect(page.locator('#credentials-username')).toHaveValue('operator-C');
    await expect(page.locator('#credentials-password')).toHaveValue('');
    await expect(page.locator('#credentials-confirm')).toHaveValue('');
    expect(state.puts).toHaveLength(0);
    expect(state.records).toEqual({ A: 'old-A', B: 'old-B' });
});
