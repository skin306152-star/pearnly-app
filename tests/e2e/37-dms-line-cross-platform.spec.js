const fs = require('fs');
const http = require('http');
const net = require('net');
const path = require('path');
const { execFileSync, spawn } = require('child_process');
const { test, expect, chromium, firefox, webkit, devices } = require('@playwright/test');

const ROOT = path.join(__dirname, '..', '..');
const OUT = path.join(__dirname, '_artifacts', 'dms-line-cross-platform');
const PYTHON = process.env.PEARNLY_E2E_PYTHON || 'python';

const iphone = { ...devices['iPhone 15'] };
const pixel = { ...devices['Pixel 7'] };
delete iphone.defaultBrowserType;
delete pixel.defaultBrowserType;

const PLATFORMS = [
    {
        id: 'ios-webkit',
        label: 'iOS Safari-compatible WebKit emulation',
        engine: 'webkit',
        browserType: webkit,
        os: 'ios',
        mobile: true,
        context: { ...iphone, locale: 'th-TH' },
    },
    {
        id: 'android-chromium',
        label: 'Android Chrome-compatible Chromium emulation',
        engine: 'chromium',
        browserType: chromium,
        os: 'android',
        mobile: true,
        context: { ...pixel, locale: 'th-TH' },
    },
    {
        id: 'macos-chromium',
        label: 'macOS Chrome-compatible Chromium browser model',
        engine: 'chromium',
        browserType: chromium,
        os: 'web',
        mobile: false,
        context: {
            viewport: { width: 1440, height: 900 },
            deviceScaleFactor: 2,
            locale: 'th-TH',
            userAgent:
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/537.36 ' +
                '(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        },
    },
    {
        id: 'windows-firefox',
        label: 'Windows Firefox-compatible browser model',
        engine: 'firefox',
        browserType: firefox,
        os: 'web',
        mobile: false,
        context: {
            viewport: { width: 1366, height: 768 },
            deviceScaleFactor: 1,
            locale: 'th-TH',
            userAgent:
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) ' +
                'Gecko/20100101 Firefox/128.0',
        },
    },
    {
        id: 'windows-chromium',
        label: 'Windows Edge-compatible Chromium browser model',
        engine: 'chromium',
        browserType: chromium,
        os: 'web',
        mobile: false,
        context: {
            viewport: { width: 1366, height: 768 },
            deviceScaleFactor: 1,
            locale: 'th-TH',
            userAgent:
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
                '(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0',
        },
    },
];

let server;
let base;
let serverOutput = '';
let contracts;
const evidence = {
    generatedAt: null,
    disclaimer:
        'Browser-engine and device-profile emulation on macOS; this is not native LINE, iOS, Android, or Windows device proof.',
    platforms: {},
};

function freePort() {
    return new Promise((resolve, reject) => {
        const probe = net.createServer();
        probe.unref();
        probe.on('error', reject);
        probe.listen(0, '127.0.0.1', () => {
            const address = probe.address();
            probe.close(() => resolve(address.port));
        });
    });
}

function waitUp(url, tries = 100) {
    return new Promise((resolve, reject) => {
        const hit = (remaining) => {
            http.get(url, (response) => {
                response.resume();
                if (response.statusCode && response.statusCode < 500) return resolve();
                if (remaining <= 0) {
                    return reject(new Error(`uvicorn returned ${response.statusCode}`));
                }
                setTimeout(() => hit(remaining - 1), 200);
            }).on('error', () => {
                if (remaining <= 0) {
                    return reject(new Error(`uvicorn did not start:\n${serverOutput}`));
                }
                setTimeout(() => hit(remaining - 1), 200);
            });
        };
        hit(tries);
    });
}

function readMenuContracts() {
    const source = [
        'import json',
        'from services.line_dms.menu_cards import menu_card',
        'from services.line_dms.rich_menu import build_payload',
        "flex = [row['action'] for row in menu_card()['contents']['body']['contents'] if row.get('action')]",
        "rich = [area['action'] for area in build_payload()['areas']]",
        "print(json.dumps({'flex': flex, 'rich': rich}, ensure_ascii=False))",
    ].join(';');
    return JSON.parse(
        execFileSync(PYTHON, ['-c', source], {
            cwd: ROOT,
            encoding: 'utf8',
            env: { ...process.env, PYTHONUTF8: '1', LINE_DMS_LIFF_ID: 'DMS-LIFF' },
        })
    );
}

function stateFor(mode, platform) {
    const external = platform.mobile ? '&openExternalBrowser=1' : '';
    return `/dms-booking?${mode}=dms${external}`;
}

function callbackUrl(mode, platform) {
    const params = new URLSearchParams({
        'liff.state': stateFor(mode, platform),
        code: `line-code-${platform.id}-${mode}`,
        state: `line-state-${platform.id}-${mode}`,
        liffClientId: 'DMS-LIFF',
        liffRedirectUri: `${base}/home?liff.state=%2Fdms-booking`,
    });
    return `${base}/home?${params.toString()}`;
}

function token() {
    const payload = Buffer.from(
        JSON.stringify({ entry: 'dms', exp: Math.floor(Date.now() / 1000) + 3600 })
    ).toString('base64url');
    return `e2e.${payload}.sig`;
}

function liffSdk(platform) {
    return `
        (() => {
            const params = new URLSearchParams(location.search);
            const callbackParamsPresent = Boolean(
                params.get('liff.state') &&
                params.get('code') &&
                params.get('state') &&
                params.get('liffClientId') &&
                params.get('liffRedirectUri')
            );
            let loggedIn = false;
            const trace = window.__liffTrace = {
                callbackParamsPresent,
                callbackConsumed: false,
                initCalls: [],
                loginCalls: [],
                idTokenCalls: 0,
            };
            const persist = () => localStorage.setItem('__dmsLiffTrace', JSON.stringify(trace));
            persist();
            window.liff = {
                init: async (options) => {
                    trace.initCalls.push(options);
                    loggedIn = callbackParamsPresent;
                    trace.callbackConsumed = loggedIn;
                    persist();
                    await window.__recordHarnessEvent({ type: 'liff.init', options });
                },
                isLoggedIn: () => loggedIn,
                login: (options) => {
                    trace.loginCalls.push(options);
                    persist();
                    window.__recordHarnessEvent({ type: 'liff.login', options });
                },
                getIDToken: () => {
                    trace.idTokenCalls += 1;
                    persist();
                    return loggedIn ? ${JSON.stringify(`LINE-ID-TOKEN-${platform.id}`)} : null;
                },
                isInClient: () => false,
                getOS: () => ${JSON.stringify(platform.os)},
                openWindow: (options) => window.__recordHarnessEvent({ type: 'liff.openWindow', options }),
                closeWindow: () => window.__recordHarnessEvent({ type: 'liff.closeWindow' }),
            };
        })();
    `;
}

async function newHarnessPage(context, platform, mode) {
    const page = await context.newPage();
    const events = [];
    const responses = [];
    let authBody = null;

    await page.addInitScript(() => {
        try {
            localStorage.removeItem('mrpilot_token');
        } catch {
            // The first about:blank document can have an opaque origin.
        }
    });
    await page.exposeFunction('__recordHarnessEvent', (event) => events.push(event));
    page.on('response', (response) => {
        responses.push({
            url: response.url(),
            status: response.status(),
            redirectedFrom: response.request().redirectedFrom()?.url() || null,
        });
    });
    await page.route('https://static.line-scdn.net/**', (route) =>
        route.fulfill({ contentType: 'application/javascript', body: liffSdk(platform) })
    );
    await page.route('**/api/line/dms-booking/config', async (route) => {
        events.push({ type: 'config' });
        await route.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, data: { liff_id: 'DMS-LIFF' } }),
        });
    });
    await page.route('**/api/line/dms-booking/auth', async (route) => {
        events.push({ type: 'auth', method: route.request().method() });
        authBody = route.request().postDataJSON();
        await route.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, data: { token: token() } }),
        });
    });

    if (mode === 'portal') {
        await page.route('**/api/line/dms-portal/ticket', async (route) => {
            events.push({ type: 'ticket', method: route.request().method() });
            await route.fulfill({
                contentType: 'application/json',
                body: JSON.stringify({
                    ok: true,
                    data: { url: `/home/dms-booking/portal?ticket=opaque-${platform.id}` },
                }),
            });
        });
        await page.route('**/home/dms-booking/portal?ticket=*', async (route) => {
            events.push({ type: 'relay', method: route.request().method() });
            await route.fulfill({
                contentType: 'text/html; charset=utf-8',
                body: `<!doctype html><html><head><meta name="viewport" content="width=device-width"><style>
                    body{margin:0;background:#f5f2ff;color:#211a45;font-family:system-ui,sans-serif}
                    main{max-width:680px;margin:8vh auto;padding:32px;border-radius:24px;background:white;box-shadow:0 18px 60px #5236a326}
                    h1{margin-top:0;color:#6146bf}.ok{color:#157a58;font-weight:700}code{word-break:break-all}
                </style></head><body><main id="relay"><h1>DMS relay reached</h1>
                    <p>${platform.label}</p><p class="ok">LIFF callback → auth → one-time ticket → relay</p>
                    <p><code>opaque-${platform.id}</code></p></main></body></html>`,
            });
        });
    } else {
        await page.route('**/api/line/dms-credentials', async (route) => {
            events.push({
                type: 'credentials',
                method: route.request().method(),
                authorization: route.request().headers().authorization || '',
            });
            await route.fulfill({
                contentType: 'application/json',
                body: JSON.stringify({ ok: true, data: { username: `operator-${platform.id}` } }),
            });
        });
    }

    const requestedCallback = callbackUrl(mode, platform);
    const committed = await page.goto(requestedCallback, { waitUntil: 'commit' });
    expect(committed, `${platform.id} ${mode} callback response`).not.toBeNull();
    expect(committed.status(), `${platform.id} ${mode} callback must be HTTP 200`).toBe(200);
    expect(committed.url(), `${platform.id} ${mode} callback URL must stay intact`).toBe(
        requestedCallback
    );
    expect(new URL(committed.url()).searchParams.get('liff.state')).toBe(stateFor(mode, platform));
    expect(
        committed.request().redirectedFrom(),
        `${platform.id} ${mode} callback must not be redirected before LIFF consumes OAuth params`
    ).toBeNull();

    if (mode === 'portal') {
        await expect(page.locator('#relay')).toBeVisible({ timeout: 15_000 });
    } else {
        await expect(page.locator('#credentials-username')).toHaveValue(`operator-${platform.id}`, {
            timeout: 15_000,
        });
    }

    const liffTrace = await page.evaluate(() =>
        JSON.parse(localStorage.getItem('__dmsLiffTrace') || 'null')
    );
    const callbackResponses = responses.filter((response) => {
        const url = new URL(response.url);
        return url.origin === base && url.pathname === '/home';
    });
    const redirects = responses.filter(
        (response) => response.status >= 300 && response.status < 400
    );

    expect(callbackResponses, `${platform.id} ${mode} callback response count`).toHaveLength(1);
    expect(callbackResponses[0].status).toBe(200);
    expect(callbackResponses[0].redirectedFrom).toBeNull();
    expect(redirects, `${platform.id} ${mode} must not pass through a 302/expired shell`).toEqual(
        []
    );
    expect(liffTrace.callbackParamsPresent).toBe(true);
    expect(liffTrace.callbackConsumed, 'liff.init must consume the callback before auth').toBe(
        true
    );
    expect(liffTrace.initCalls).toEqual([{ liffId: 'DMS-LIFF' }]);
    expect(liffTrace.loginCalls, `${platform.id} ${mode} must not restart LINE Login`).toEqual([]);
    expect(liffTrace.idTokenCalls).toBe(1);
    expect(authBody).toEqual({ id_token: `LINE-ID-TOKEN-${platform.id}` });

    const eventTypes = events.map((event) => event.type);
    expect(eventTypes.slice(0, 3)).toEqual(['config', 'liff.init', 'auth']);
    if (mode === 'portal') {
        expect(eventTypes).toEqual(['config', 'liff.init', 'auth', 'ticket', 'relay']);
        expect(events.find((event) => event.type === 'ticket').method).toBe('POST');
        await expect(page).toHaveURL(
            `${base}/home/dms-booking/portal?ticket=opaque-${platform.id}`
        );
    } else {
        expect(eventTypes).toEqual(['config', 'liff.init', 'auth', 'credentials']);
        expect(events.find((event) => event.type === 'credentials')).toMatchObject({
            method: 'GET',
            authorization: expect.stringMatching(/^Bearer e2e\./),
        });
        await expect(page).toHaveURL(requestedCallback);
    }
    expect(await page.locator('body').innerText()).not.toMatch(/expired|หมดอายุ|已过期|期限切れ/i);

    return {
        page,
        facts: {
            requestedCallback,
            callbackHttpStatus: committed.status(),
            callbackRedirectedFrom: null,
            finalUrl: page.url(),
            liffInitCalls: liffTrace.initCalls,
            liffLoginCount: liffTrace.loginCalls.length,
            authBody,
            eventSequence: eventTypes,
            redirectResponses: redirects,
        },
    };
}

test.describe.configure({ mode: 'serial' });

test.beforeAll(async () => {
    fs.rmSync(OUT, { recursive: true, force: true });
    fs.mkdirSync(OUT, { recursive: true });
    contracts = readMenuContracts();
    const port = await freePort();
    base = `http://127.0.0.1:${port}`;
    server = spawn(
        PYTHON,
        [
            '-m',
            'uvicorn',
            'app:app',
            '--host',
            '127.0.0.1',
            '--port',
            String(port),
            '--no-access-log',
        ],
        {
            cwd: ROOT,
            stdio: ['ignore', 'pipe', 'pipe'],
            env: { ...process.env, PYTHONUTF8: '1' },
        }
    );
    server.stdout.on('data', (chunk) => (serverOutput += chunk.toString()));
    server.stderr.on('data', (chunk) => (serverOutput += chunk.toString()));
    await waitUp(`${base}/api/health`);
    evidence.generatedAt = new Date().toISOString();
    evidence.server = { base, runtime: 'real local uvicorn app:app' };
    evidence.menuContracts = contracts;
});

test.afterAll(() => {
    evidence.completedAt = new Date().toISOString();
    fs.writeFileSync(
        path.join(OUT, 'matrix-evidence.json'),
        `${JSON.stringify(evidence, null, 2)}\n`,
        'utf8'
    );
    if (server) server.kill('SIGTERM');
});

test('LINE menu 1-4 contracts preserve postbacks, mobile external URIs, and desktop altUri', () => {
    const [customer, booking, portal, credentialsAction] = contracts.flex;
    expect(customer).toEqual({ type: 'postback', data: 'action=menu_customer' });
    expect(booking).toEqual({ type: 'postback', data: 'action=menu_booking' });
    expect(portal).toMatchObject({
        type: 'uri',
        uri: 'https://pearnly.com/home/dms-booking?portal=dms&openExternalBrowser=1',
        altUri: { desktop: 'https://pearnly.com/home/dms-booking?portal=dms' },
    });
    expect(credentialsAction).toMatchObject({
        type: 'uri',
        uri: 'https://pearnly.com/home/dms-booking?credentials=dms&openExternalBrowser=1',
        altUri: { desktop: 'https://pearnly.com/home/dms-booking?credentials=dms' },
    });

    expect(contracts.rich.map((action) => [action.type, action.data || action.uri])).toEqual([
        ['postback', 'action=menu_customer'],
        ['postback', 'action=menu_booking'],
        ['uri', 'https://pearnly.com/home/dms-booking?portal=dms&openExternalBrowser=1'],
        ['uri', 'https://pearnly.com/home/dms-booking?credentials=dms&openExternalBrowser=1'],
    ]);
});

for (const platform of PLATFORMS) {
    test(`${platform.label}: menu 3 and menu 4 complete the primary LIFF callback`, async () => {
        test.setTimeout(90_000);
        const browser = await platform.browserType.launch({ headless: true });
        const context = await browser.newContext(platform.context);
        try {
            const portalAction = contracts.flex[2];
            const credentialsAction = contracts.flex[3];
            const selectedPortalUri = platform.mobile
                ? portalAction.uri
                : portalAction.altUri.desktop;
            const selectedCredentialsUri = platform.mobile
                ? credentialsAction.uri
                : credentialsAction.altUri.desktop;
            expect(selectedPortalUri).toContain('portal=dms');
            expect(selectedCredentialsUri).toContain('credentials=dms');
            expect(selectedPortalUri.includes('openExternalBrowser=1')).toBe(platform.mobile);
            expect(selectedCredentialsUri.includes('openExternalBrowser=1')).toBe(platform.mobile);

            const portal = await newHarnessPage(context, platform, 'portal');
            await portal.page.screenshot({
                path: path.join(OUT, `${platform.id}-menu3-relay.png`),
                fullPage: true,
            });
            await portal.page.close();

            const credentialsFlow = await newHarnessPage(context, platform, 'credentials');
            expect(
                await credentialsFlow.page.evaluate(
                    () => globalThis.document.documentElement.scrollWidth <= globalThis.innerWidth
                )
            ).toBe(true);
            await credentialsFlow.page.screenshot({
                path: path.join(OUT, `${platform.id}-menu4-credentials.png`),
                fullPage: true,
            });
            await credentialsFlow.page.close();

            const platformEvidence = {
                label: platform.label,
                engine: platform.engine,
                nativeDeviceOrOs: false,
                selectedMenuUris: {
                    menu3: selectedPortalUri,
                    menu4: selectedCredentialsUri,
                },
                menu1Postback: contracts.flex[0].data,
                menu2Postback: contracts.flex[1].data,
                portal: portal.facts,
                credentials: credentialsFlow.facts,
            };
            evidence.platforms[platform.id] = platformEvidence;
            fs.writeFileSync(
                path.join(OUT, `${platform.id}.json`),
                `${JSON.stringify(platformEvidence, null, 2)}\n`,
                'utf8'
            );
        } finally {
            await context.close();
            await browser.close();
        }
    });
}
