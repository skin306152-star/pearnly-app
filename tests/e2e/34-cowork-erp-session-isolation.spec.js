/* global window */

// 34-cowork-erp-session-isolation.spec.js
//
// 入口级会话隔离(2026-08-27 · 同一 Chrome 里 /cowork 与 /erp 用不同账号同时在线、互不覆盖)。
// ⚠️ 本 spec 依赖 src/home/session.ts 已 build 进 static/dist/main.js;若在未 build 的仓库跑会红
//    (dist 仍是旧单槽逻辑)。本地全量跑前先 `npm run build`。
//
// 断言不变量(不依赖字符串自镜像):
//   A. cowork 与 erp 两个 tab 的 /api/me 请求带【不同】Bearer token(各自槽),且 X-Workspace-Client-Id
//      也各自分槽(互不覆盖)。
//   B. 登出(cowork 槽 clear)只清 cowork 槽,erp 槽 token 仍在,reload 后 erp 仍用原 token。
//   C. legacy POS token(entry=pos)打 /erp 不被收养:仍停在 erp 登录页,不跳 /home?canonical=erp。

const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8998;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'cowork_erp_session');

const COW_TOKEN = 'cow-token-AAA';
const ERP_TOKEN = 'erp-token-BBB';
const COW_WS = '101';
const ERP_WS = '202';

// 真 JWT 样式(带 entry 字段)用于 POS 拒绝测试。
function jwtLike(entry) {
    const payload = Buffer.from(JSON.stringify({ entry }))
        .toString('base64')
        .replace(/=+$/, '')
        .replace(/\+/g, '-')
        .replace(/\//g, '_');
    return `a.${payload}.sig`;
}

let server;

test.beforeAll(async () => {
    fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
    server = await localServer.start(PORT, '/home.html');
});
test.afterAll(() => localServer.stop(server));

async function stubShellRoutes(context, { erpShell = 'shell/erp.html' } = {}) {
    // 主壳 app 在 /cowork|/erp 下由同源 home.html 承接(生产经 pages_routes 出 app 壳;
    // 本地静态服没有 /cowork 文件,故 route 兜底 home.html,语义等价于生产 canonical 壳)。
    // /erp 门在「登出/未授权」场景(passShell='shell/erp.html')用源码 erp.html 呈登录门。
    await context.route(`${BASE}/cowork`, (route) =>
        route.fulfill({
            path: path.join(localServer.ROOT, 'home.html'),
            contentType: 'text/html',
        })
    );
    await context.route(`${BASE}/erp`, (route) =>
        route.fulfill({
            path:
                erpShell === 'app'
                    ? path.join(localServer.ROOT, 'home.html')
                    : path.join(localServer.ROOT, 'static', 'erp', 'erp.html'),
            contentType: 'text/html',
        })
    );
}

// 记录 /api/me 请求的 Authorization + X-Workspace-Client-Id 头。
async function stubApi(context, state) {
    await context.route('**/api/**', async (route) => {
        const req = route.request();
        const url = new URL(req.url());
        if (url.pathname === '/api/me') {
            state.meCalls.push({
                auth: req.headers().authorization || '',
                ws: req.headers()['x-workspace-client-id'] || '',
            });
        }
        // 后端按 token.entry 下发壳的权威 entry(cowork/erp)。按 Authorization 区分两个 tab。
        const auth = req.headers().authorization || '';
        const moduleEntry = auth === `Bearer ${ERP_TOKEN}` ? 'erp' : 'cowork';
        const body = (() => {
            if (url.pathname === '/api/me') {
                return { id: 'u1', username: 'e2e-user', is_super_admin: false };
            }
            if (url.pathname === '/api/workspace/clients') {
                return { clients: [{ id: 101, name: 'CoWorkspace', subject_type: 'company' }] };
            }
            if (url.pathname === '/api/me/modules') {
                return { data: { modules: {}, business_type: 'firm', entry: moduleEntry } };
            }
            return { ok: true };
        })();
        const code = /\/api\/login/.test(url.pathname) ? 200 : 200;
        return route.fulfill({
            status: code,
            contentType: 'application/json',
            body: JSON.stringify(body),
        });
    });
}

function seedSession(context, { setCowork, setErp }) {
    return context.addInitScript(
        ({ setCowork, setErp }) => {
            localStorage.clear();
            localStorage.setItem('mrpilot_lang', 'zh');
            localStorage.setItem('pearnly_entry', 'cowork');
            if (setCowork) {
                localStorage.setItem('mrpilot_token_cowork', 'cow-token-AAA');
                localStorage.setItem('pearnly_active_workspace_client_id_cowork', '101');
            }
            if (setErp) {
                localStorage.setItem('mrpilot_token_erp', 'erp-token-BBB');
                localStorage.setItem('pearnly_active_workspace_client_id_erp', '202');
            }
        },
        { setCowork, setErp }
    );
}

test('cowork 与 erp 两个 tab 用不同 token + 不同 workspace 头,互不覆盖', async ({ context }) => {
    const state = { meCalls: [] };
    await stubApi(context, state);
    await stubShellRoutes(context, { erpShell: 'app' }); // 两个 tab 都进主壳 app
    await seedSession(context, { setCowork: true, setErp: true });

    const coworkPage = await context.newPage();
    const erpPage = await context.newPage();

    await coworkPage.goto(`${BASE}/cowork`, { waitUntil: 'domcontentloaded' });
    await erpPage.goto(`${BASE}/erp`, { waitUntil: 'domcontentloaded' });

    // ① token 槽隔离:两个 tab 各自读自己的入口槽,绝不共读/互写。
    const coworkSlot = await coworkPage.evaluate(() => ({
        entry: window.session.entry(),
        token: window.session.getToken(),
        wsKey: window.session.workspaceKey(),
        ws: window.session.getWorkspaceClientId(),
        hdr: window._wsHeader(),
    }));
    const erpSlot = await erpPage.evaluate(() => ({
        entry: window.session.entry(),
        token: window.session.getToken(),
        wsKey: window.session.workspaceKey(),
        ws: window.session.getWorkspaceClientId(),
        hdr: window._wsHeader(),
    }));

    expect(coworkSlot.entry, 'cowork tab 的 entry').toBe('cowork');
    expect(erpSlot.entry, 'erp tab 的 entry').toBe('erp');
    expect(coworkSlot.token, 'cowork tab 读自己的槽 token').toBe(COW_TOKEN);
    expect(erpSlot.token, 'erp tab 读自己的槽 token').toBe(ERP_TOKEN);
    expect(coworkSlot.token, '两个槽 token 必须不同').not.toBe(erpSlot.token);
    expect(coworkSlot.wsKey).toBe('pearnly_active_workspace_client_id_cowork');
    expect(erpSlot.wsKey).toBe('pearnly_active_workspace_client_id_erp');

    // ② workspace 槽隔离:X-Workspace-Client-Id 由各入口槽决定(不可互改)。
    expect(coworkSlot.hdr['X-Workspace-Client-Id'], 'cowork 的 ws 头').toBe('101');
    expect(erpSlot.hdr['X-Workspace-Client-Id'], 'erp 的 ws 头').toBe('202');

    // ③ 线上隔离:两个 tab 发出的 /api/me 确实带各自入口 token(session-heartbeat 也发 /api/me)。
    await expect
        .poll(
            () =>
                state.meCalls.some((m) => m.auth === `Bearer ${COW_TOKEN}`) &&
                state.meCalls.some((m) => m.auth === `Bearer ${ERP_TOKEN}`),
            { timeout: 20_000 }
        )
        .toBe(true);
    // 绝不出现"用同事 token 发请求"这种跨槽串号。
    expect(
        state.meCalls.some((m) => m.auth === `Bearer ${COW_TOKEN}` && m.ws === '202'),
        'cowork token 不应带 erp workspace 头'
    ).toBe(false);
    expect(
        state.meCalls.some((m) => m.auth === `Bearer ${ERP_TOKEN}` && m.ws === '101'),
        'erp token 不应带 cowork workspace 头'
    ).toBe(false);

    await coworkPage.screenshot({
        path: path.join(ARTIFACT_DIR, '01-two-tabs-different-slots.png'),
        fullPage: true,
    });
});

test('登出清 cowork 槽不改 erp 槽,reload 后 erp 仍用原 token', async ({ context }) => {
    const state = { meCalls: [] };
    await stubApi(context, state);
    await stubShellRoutes(context, { erpShell: 'app' }); // 两个 tab 都进主壳 app
    await seedSession(context, { setCowork: true, setErp: true });

    const coworkPage = await context.newPage();
    const erpPage = await context.newPage();

    await coworkPage.goto(`${BASE}/cowork`, { waitUntil: 'domcontentloaded' });
    await erpPage.goto(`${BASE}/erp`, { waitUntil: 'domcontentloaded' });

    // 模拟 cowork 登出:只清当前入口槽(与 topbar-avatar logout 的 session.clearToken 一致)。
    await coworkPage.evaluate(() => window.session.clearToken());
    expect(
        await coworkPage.evaluate(() => localStorage.getItem('mrpilot_token_cowork'))
    ).toBeNull();
    // erp 槽 token 不受影响(同一 localStorage,但槽位不同)。
    expect(await coworkPage.evaluate(() => localStorage.getItem('mrpilot_token_erp'))).toBe(
        ERP_TOKEN
    );
    expect(
        await coworkPage.evaluate(() =>
            localStorage.getItem('pearnly_active_workspace_client_id_erp')
        )
    ).toBe(ERP_WS);

    // reload erp 页后仍以原 erp token + erp workspace 头(证明另一边没被清)。
    await erpPage.reload({ waitUntil: 'domcontentloaded' });
    const erpAfter = await erpPage.evaluate(() => ({
        token: window.session.getToken(),
        ws: window.session.getWorkspaceClientId(),
        hdr: window._wsHeader(),
    }));
    expect(erpAfter.token, 'reload 后 erp 仍用 erp 槽 token').toBe(ERP_TOKEN);
    expect(erpAfter.ws, 'reload 后 erp 仍用 erp workspace 槽').toBe(202);
    expect(erpAfter.hdr['X-Workspace-Client-Id']).toBe('202');
    // erp /api/me 仍带 erp token 打到线上(证明隔离没被登出破坏)。
    await expect
        .poll(() => state.meCalls.some((m) => m.auth === `Bearer ${ERP_TOKEN}`), {
            timeout: 20_000,
        })
        .toBe(true);
});

test('页面实际 fetch 带正确 Authorization 与 X-Workspace-Client-Id(非仅 helper 断言)', async ({
    context,
}) => {
    const captured = [];
    await context.route('**/api/session-probe', async (route) => {
        const req = route.request();
        captured.push({
            url: req.url(),
            auth: req.headers().authorization || '',
            ws: req.headers()['x-workspace-client-id'] || '',
        });
        return route.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true}' });
    });
    await stubShellRoutes(context, { erpShell: 'app' });
    await seedSession(context, { setCowork: true, setErp: true });

    const coworkPage = await context.newPage();
    const erpPage = await context.newPage();

    await coworkPage.goto(`${BASE}/cowork`, { waitUntil: 'domcontentloaded' });
    await erpPage.goto(`${BASE}/erp`, { waitUntil: 'domcontentloaded' });

    // 从 cowork 页用 session 模块构建 headers 发真实 fetch。
    await coworkPage.evaluate(async () => {
        const hdr = window._wsHeader();
        hdr['Authorization'] = 'Bearer ' + window.session.getToken();
        await fetch('/api/session-probe', { method: 'GET', headers: hdr });
    });
    // 从 erp 页同理。
    await erpPage.evaluate(async () => {
        const hdr = window._wsHeader();
        hdr['Authorization'] = 'Bearer ' + window.session.getToken();
        await fetch('/api/session-probe', { method: 'GET', headers: hdr });
    });

    // 等两次 probe 都被 Playwright route 捕获。
    await expect.poll(() => captured.length >= 2, { timeout: 10_000 }).toBe(true);

    const cowProbe = captured.find((c) => c.auth === `Bearer ${COW_TOKEN}`);
    const erpProbe = captured.find((c) => c.auth === `Bearer ${ERP_TOKEN}`);

    expect(cowProbe, 'cowork fetch 应被捕获').toBeTruthy();
    expect(erpProbe, 'erp fetch 应被捕获').toBeTruthy();
    expect(cowProbe.ws, 'cowork fetch 的 X-Workspace-Client-Id').toBe(COW_WS);
    expect(erpProbe.ws, 'erp fetch 的 X-Workspace-Client-Id').toBe(ERP_WS);
    // 交叉污染检查:绝不出现 cowork token + erp workspace 或反之。
    expect(
        captured.some((c) => c.auth === `Bearer ${COW_TOKEN}` && c.ws === ERP_WS),
        'cowork token 不应带 erp workspace'
    ).toBe(false);
    expect(
        captured.some((c) => c.auth === `Bearer ${ERP_TOKEN}` && c.ws === COW_WS),
        'erp token 不应带 cowork workspace'
    ).toBe(false);
});

test('POS legacy token(entry=pos)打 /erp 不被收养,留在登录页', async ({ context }) => {
    await stubShellRoutes(context);
    // 只放一个 legacy POS token(类似 POS 已登录),没有任何 erp 槽 token。
    await context.addInitScript(
        ({ posTok }) => {
            localStorage.clear();
            localStorage.setItem('mrpilot_lang', 'zh');
            localStorage.setItem('mrpilot_token', posTok);
            localStorage.setItem('pearnly_entry', 'pos');
        },
        { posTok: jwtLike('pos') }
    );

    const page = await context.newPage();
    // 若 POS token 被 erp 收养会 302 去 /home?canonical=erp;不被收养则停在登录门 #p-form。
    await page.goto(`${BASE}/erp`, { waitUntil: 'domcontentloaded' });
    await expect(page.locator('#p-form')).toBeVisible({ timeout: 10_000 });
    expect(new URL(page.url()).pathname, 'POS token 不应把 /erp 拽去 /home').not.toMatch(/^\/home/);
    // erp 槽绝不应出现被收养的 POS token。
    expect(await page.evaluate(() => localStorage.getItem('mrpilot_token_erp'))).toBeNull();
    await page.screenshot({
        path: path.join(ARTIFACT_DIR, '02-pos-token-rejected-by-erp.png'),
        fullPage: true,
    });
});
