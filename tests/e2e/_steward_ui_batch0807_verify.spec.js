// /ai 智能管家 UI 六项批次(2026-08-07)真浏览器验收 · static/dist 真构建产物 + page.route 桩。
// ============================================================
// 覆盖:
//   ① 询问栏已删除:#stwBar / .stw-bar 在 DOM 里彻底不存在(不是隐藏)。
//   ② 左侧主菜单折叠:真收合(量 .side 的 boundingClientRect 宽度)+ localStorage 持久化
//      (刷新页面直接是收起态,不闪一下展开再收)。
//   ③ 会话历史面板折叠:真收合(量 .stw-side 宽度),与 ②互相独立。
//   ④ 点历史会话加载消息:桩正常(消息真的渲染出来)与桩失败(错误态 + 重试按钮,
//      点重试后台恢复即读到消息)两态——这是 P0 bug 修复的回归锁,复现证据见
//      交付报告(桩 2.5s 延迟/500 两种条件下用 _scratch_repro_steward_history.js 真机
//      复现过,这里固化成常驻闸)。
//   ⑤ 回形针与发送键同高居中:getBoundingClientRect 量两颗键的高度与竖直中心。
//   ⑥ 执行过程条默认折叠:哪怕任务状态是 running/failed,历史轮补拉出来的过程条
//      默认也是折叠态(2026-08-07 拍板改的是"哪怕在跑也先收"),点开能展开。
//
// 跑法: npx playwright test tests/e2e/_steward_ui_batch0807_verify.spec.js
/* global window, document, getComputedStyle */

const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8918;
const BASE = `http://127.0.0.1:${PORT}`;
const ART = path.join(__dirname, '_artifacts', 'steward_ui_batch0807');
const LIMITS = require('./_fixtures_steward_limits.json');

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT, '/static/dist/ai.html');
    fs.mkdirSync(ART, { recursive: true });
});
test.afterAll(() => localServer.stop(server));

const SESSIONS = [
    { session_id: 's1', title: '历史会话一', last_active_at: '2026-08-01T09:00:00Z' },
    { session_id: 's2', title: '历史会话二', last_active_at: '2026-08-02T09:00:00Z' },
];

// s1 的历史消息里带一条引用 t1 的管家回复:切过去时 backfill() 会补拉 GET /tasks/t1,
// 用来验收 ⑥(过程条默认折叠,即便 t1 状态是 running)。
const S1_MESSAGES = {
    session_id: 's1',
    messages: [
        { id: 'm1', role: 'user', text: '第一条历史消息' },
        { id: 'm2', role: 'steward', text: '好的,已经处理', task_id: 't1' },
    ],
    has_more: false,
};

const T1_TASK = {
    task_id: 't1',
    status: 'running',
    steps: [{ label: '正在识别票据', state: 'running' }],
    started_at: '2026-08-01T09:00:05Z',
    cancellable: true,
};

// 基础桩:登录态 + 闸开 + 会话列表。每个 test 各自按需再叠加 /sessions/{sid} 的行为。
async function stubCommon(page) {
    await page.route('**/api/**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{}' })
    );
    await page.route('**/api/me', (r) =>
        r.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({ username: 'stw', tenant_name: 'stw' }),
        })
    );
    await page.route('**/api/ai/steward/status', (r) =>
        r.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({ enabled: true, attachments: LIMITS }),
        })
    );
    await page.route('**/api/ai/steward/sessions', (r) => {
        if (r.request().method() === 'POST') {
            return r.fulfill({
                contentType: 'application/json',
                body: JSON.stringify({ session_id: 'new-empty' }),
            });
        }
        return r.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({ sessions: SESSIONS }),
        });
    });
    await page.route('**/api/ai/steward/tasks/t1', (r) =>
        r.fulfill({ contentType: 'application/json', body: JSON.stringify(T1_TASK) })
    );
}

async function loginToken(page) {
    await page.addInitScript(() => {
        window.localStorage.setItem('mrpilot_token_ai', 'tok-e2e-uibatch0807');
        window.localStorage.setItem('mrpilot_lang', 'zh');
    });
}

async function openDashboard(page) {
    await stubCommon(page);
    await loginToken(page);
    await page.goto(`${BASE}/static/dist/ai.html`);
    await page.waitForSelector('#navDash.on', { state: 'visible', timeout: 15000 });
}

async function openSteward(page) {
    await stubCommon(page);
    await loginToken(page);
    await page.goto(`${BASE}/static/dist/ai.html#/steward`);
    await page.waitForSelector('#v-steward.on', { state: 'visible', timeout: 15000 });
    await page.waitForSelector('#stwSessList', { state: 'visible', timeout: 15000 });
}

// ---------- ① 询问栏已删除 ----------

test('① #stwBar / .stw-bar 在 DOM 里彻底不存在', async ({ page }) => {
    await openDashboard(page);
    expect(await page.locator('#stwBar').count()).toBe(0);
    expect(await page.locator('.stw-bar').count()).toBe(0);
    await page.screenshot({ path: path.join(ART, '01-no-steward-bar.png'), fullPage: true });
});

// ---------- ② 左侧主菜单折叠 ----------

test('② 左侧主菜单 toggle 真收合(量宽度)+ 刷新后持久化', async ({ page }) => {
    await openDashboard(page);
    const before = await page.locator('.side').boundingBox();
    expect(before.width).toBeGreaterThan(180); // 展开态 224px

    await page.click('#sideToggle');
    await page.waitForFunction(
        () => document.body.classList.contains('side-collapsed'),
        undefined,
        { timeout: 3000 }
    );
    // 宽度有 --dur-base(180ms)过渡动画,量的是终值——用 poll 等它停,不是猜一个
    // sleep 时长(那样在慢 CI 上会假红)。
    await expect
        .poll(async () => (await page.locator('.side').boundingBox()).width, { timeout: 2000 })
        .toBeLessThan(100); // 折叠态 64px
    const after = await page.locator('.side').boundingBox();
    expect(after.width).toBeLessThan(before.width - 100);
    await page.screenshot({ path: path.join(ART, '02-nav-collapsed.png'), fullPage: true });

    // localStorage 落了持久化键。
    const persisted = await page.evaluate(() => localStorage.getItem('mrpilot_ai_side_collapsed'));
    expect(persisted).toBe('1');

    // 刷新:折叠态在脚本加载期就应用,不该闪一下展开再收起。
    await page.reload();
    await page.waitForSelector('#navDash.on', { state: 'visible', timeout: 15000 });
    await expect
        .poll(async () => (await page.locator('.side').boundingBox()).width, { timeout: 2000 })
        .toBeLessThan(100);

    // 再点一次能展开回去(不是单向死开关)。
    await page.click('#sideToggle');
    await page.waitForFunction(
        () => !document.body.classList.contains('side-collapsed'),
        undefined,
        { timeout: 3000 }
    );
    await expect
        .poll(async () => (await page.locator('.side').boundingBox()).width, { timeout: 2000 })
        .toBeGreaterThan(180);
});

// ---------- ③ 会话历史面板折叠 ----------

test('③ 会话历史面板 toggle 真收合(量宽度,与②互相独立)', async ({ page }) => {
    await openSteward(page);
    const before = await page.locator('#stwSide').boundingBox();
    expect(before.width).toBeGreaterThan(220); // 展开态 256px

    await page.click('[data-action="stw-side-toggle"]');
    await page.waitForFunction(
        () => document.getElementById('stwSide').classList.contains('collapsed'),
        undefined,
        { timeout: 3000 }
    );
    await expect
        .poll(async () => (await page.locator('#stwSide').boundingBox()).width, { timeout: 2000 })
        .toBeLessThan(80); // 折叠态 56px
    const after = await page.locator('#stwSide').boundingBox();
    // 收起态只留展开/收起图标(Zihao 2026-08-08 拍板,推翻 08-07「新对话按钮还在」):
    // 历史列表与「+」新对话一起藏,唯一出路 = 居中的 toggle,展开后按钮回来。
    expect(await page.locator('#stwSessList').isVisible()).toBe(false);
    expect(await page.locator('[data-action="stw-new-session"]').isVisible()).toBe(false);
    expect(await page.locator('[data-action="stw-side-toggle"]').isVisible()).toBe(true);
    await page.screenshot({
        path: path.join(ART, '03-session-side-collapsed.png'),
        fullPage: true,
    });

    await page.click('[data-action="stw-side-toggle"]');
    await page.waitForFunction(
        () => !document.getElementById('stwSide').classList.contains('collapsed'),
        undefined,
        { timeout: 3000 }
    );
    expect(await page.locator('#stwSessList').isVisible()).toBe(true);
});

// ---------- ④ 历史会话点击:桩正常 / 桩失败两态(P0 bug 回归锁) ----------

// s1 桩必须在 openSteward() 之后注册:Playwright 路由是后注册者优先,stubCommon() 的
// 通配 **/api/** 若排在后面会盖掉这里的专属响应(同 _gate_probe_honesty_local.spec.js
// 的 boot() 先例)。openSteward() 只跑到「侧栏可见」为止,还没点历史项,注册不晚。
test('④a 点历史会话(网络正常)→ 消息真的渲染出来', async ({ page }) => {
    await openSteward(page);
    await page.route('**/api/ai/steward/sessions/s1**', (r) =>
        r.fulfill({ contentType: 'application/json', body: JSON.stringify(S1_MESSAGES) })
    );
    await page.click('[data-action="stw-sess-open"][data-sid="s1"]');
    await expect(page.locator('#stwFeed')).toContainText('第一条历史消息', { timeout: 10000 });
    await expect(page.locator('#stwFeed')).toContainText('好的,已经处理');
    await page.screenshot({ path: path.join(ART, '04a-history-loaded.png'), fullPage: true });
});

test('④b 点历史会话(慢网络)→ 骨架屏而不是"看起来空空的欢迎屏"', async ({ page }) => {
    await openSteward(page);
    await page.route('**/api/ai/steward/sessions/s1**', async (r) => {
        await new Promise((res) => setTimeout(res, 1200));
        return r.fulfill({ contentType: 'application/json', body: JSON.stringify(S1_MESSAGES) });
    });
    await page.click('[data-action="stw-sess-open"][data-sid="s1"]');
    // 请求还在飞:不能是欢迎屏(那与"这个会话真没消息"长得一样),必须是骨架屏。
    await expect(page.locator('#stwFeed [data-state="loading"]')).toBeVisible({ timeout: 2000 });
    await expect(page.locator('.stw-welcome')).toHaveCount(0);
    await page.screenshot({
        path: path.join(ART, '04b-history-loading-skeleton.png'),
        fullPage: true,
    });
    await expect(page.locator('#stwFeed')).toContainText('第一条历史消息', { timeout: 10000 });
});

test('④c 点历史会话(后端 500)→ 错误态 + 重试,不是静默空白', async ({ page }) => {
    await openSteward(page);
    let fail = true;
    await page.route('**/api/ai/steward/sessions/s1**', (r) => {
        if (fail) {
            return r.fulfill({
                status: 500,
                contentType: 'application/json',
                body: '{"detail":"boom"}',
            });
        }
        return r.fulfill({ contentType: 'application/json', body: JSON.stringify(S1_MESSAGES) });
    });
    await page.click('[data-action="stw-sess-open"][data-sid="s1"]');
    await expect(page.locator('[data-state="error"]')).toBeVisible({ timeout: 10000 });
    // 不能是"看起来像空会话"——欢迎屏不该同时出现。
    await expect(page.locator('.stw-welcome')).toHaveCount(0);
    await page.screenshot({ path: path.join(ART, '04c-history-error-state.png'), fullPage: true });

    // 点重试:后端恢复,消息应声出现(不用刷新页面、不用退出重进)。
    fail = false;
    await page.click('[data-action="stw-history-retry"]');
    await expect(page.locator('#stwFeed')).toContainText('第一条历史消息', { timeout: 10000 });
    await page.screenshot({
        path: path.join(ART, '04d-history-retry-recovered.png'),
        fullPage: true,
    });
});

// ---------- ⑤ 回形针与发送键同高居中 ----------

test('⑤ .stw-clip 与 .stw-send-btn 同高、竖直中心对齐', async ({ page }) => {
    await openSteward(page);
    await page.waitForSelector('.stw-clip', { state: 'visible', timeout: 10000 });
    const geo = await page.evaluate(() => {
        const box = (el) => {
            const r = el.getBoundingClientRect();
            return { top: r.top, height: r.height, centerY: r.top + r.height / 2 };
        };
        return {
            clip: box(document.querySelector('.stw-clip')),
            send: box(document.querySelector('.stw-send-btn')),
            clipHeight: getComputedStyle(document.querySelector('.stw-clip')).height,
            sendHeight: getComputedStyle(document.querySelector('.stw-send-btn')).height,
        };
    });
    expect(geo.clipHeight).toBe('34px');
    expect(geo.sendHeight).toBe('34px');
    expect(Math.abs(geo.clip.height - geo.send.height)).toBeLessThanOrEqual(0.5);
    expect(Math.abs(geo.clip.centerY - geo.send.centerY)).toBeLessThanOrEqual(0.5);
    fs.writeFileSync(path.join(ART, '05-clip-geometry.json'), JSON.stringify(geo, null, 2) + '\n');
    await page.screenshot({ path: path.join(ART, '05-composer-buttons.png') });
});

// ---------- ⑥ 执行过程条默认折叠 ----------

test('⑥ 历史轮补拉出的过程条默认折叠(即便任务在跑),点开能展开', async ({ page }) => {
    await openSteward(page);
    await page.route('**/api/ai/steward/sessions/s1**', (r) =>
        r.fulfill({ contentType: 'application/json', body: JSON.stringify(S1_MESSAGES) })
    );
    await page.click('[data-action="stw-sess-open"][data-sid="s1"]');
    // t1 状态是 running(离终态最远的那一档,旧逻辑本该默认展开)——新规矩恒折叠。
    const proc = page.locator('.stw-proc[data-proc="t1"]');
    await expect(proc).toBeVisible({ timeout: 10000 });
    await expect(proc).toHaveClass(/collapsed/);
    await page.screenshot({
        path: path.join(ART, '06a-proc-default-collapsed.png'),
        fullPage: true,
    });

    await proc.locator('.stw-proc-hd').click();
    await expect(proc).not.toHaveClass(/collapsed/);
    await expect(proc.locator('.stw-proc-bd')).toContainText('正在识别票据');
    await page.screenshot({ path: path.join(ART, '06b-proc-expanded.png'), fullPage: true });
});
