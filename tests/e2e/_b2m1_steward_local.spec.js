// 智能管家(B2-M1 · 前端)· 本地真浏览器验收(跑 static/dist 真构建产物)
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**(同
// _b1_states_local.spec.js 先例)。断言的 DOM/CSS 全来自真产物:命令条真在矩阵上方、
// 五个步骤态真是 B1 五个色族(getComputedStyle 背景色两两有色差,不是同一片灰)、
// 轮询真把 running 翻成 done、闸关真什么都不渲染。截图存 _artifacts/b2m1_steward/。
//
// 起法:npx playwright test tests/e2e/_b2m1_steward_local.spec.js
/* global window, document, getComputedStyle */

const { test, expect } = require('@playwright/test');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const ROOT = path.resolve(__dirname, '..', '..');
const PORT = 8991;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'b2m1_steward');

let server;

function waitUp(url, tries = 40) {
    return new Promise((resolve, reject) => {
        const hit = (n) => {
            http.get(url, (r) => {
                r.resume();
                resolve();
            }).on('error', () => {
                if (n <= 0) return reject(new Error('server not up'));
                setTimeout(() => hit(n - 1), 150);
            });
        };
        hit(tries);
    });
}

test.beforeAll(async () => {
    server = spawn('python', ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1'], {
        cwd: ROOT,
        stdio: 'ignore',
    });
    await waitUp(`${BASE}/static/dist/ai.html`);
});

test.afterAll(() => {
    if (server) server.kill();
});

// 五个步骤态各一条 + 一条深链 + 一张表格产物:左窗要能同时表达 B1 的五个色族。
function taskPayload(status) {
    return {
        task_id: 't1',
        title: '2569-06 缺料盘点',
        status,
        started_at: '2026-07-26T09:05:00Z',
        agent_count: 3,
        steps: [
            { id: 's1', label: '解析期间', state: 'done', detail: '2569-06', links: [] },
            {
                id: 's2',
                label: '查事务所矩阵',
                state: status === 'done' ? 'done' : 'running',
                detail: '扫 12 家客户',
                links: [{ label: '打开矩阵', href: '#/' }],
            },
            { id: 's3', label: '汇总缺料清单', state: status === 'done' ? 'done' : 'queued' },
            { id: 's4', label: '读推送日志', state: 'waiting_auth', detail: '需要 ERP 授权' },
            { id: 's5', label: '拉历史票据', state: 'failed', detail: 'ERR_TIMEOUT' },
        ],
        artifacts: [
            {
                kind: 'deeplink',
                label: '去 SM 的工单页',
                href: '#/client/c-sm/wo?period=2569-06',
            },
            // 形状必须与后端真实产出逐字段一致(services/steward/copy.py _table:
            // columns=[{key,label}] + dict 行)。首版桩抄的是产品里不存在的旧形状
            // (字符串列 + 数组行),于是表格全渲染成 [object Object] 却全绿——
            // 桩的形状不是随便编的,它就是被验的契约本身。
            {
                kind: 'table',
                label: '要盯的格子',
                columns: [
                    { key: 'name', label: '客户' },
                    { key: 'obligation_code', label: '义务' },
                    { key: 'badge', label: '状态' },
                ],
                rows: [
                    { name: 'SM', obligation_code: 'PP30', badge: 'missing_materials' },
                    { name: 'MR.ERP', obligation_code: 'PND3', badge: null },
                ],
            },
        ],
    };
}

const REPLY = '这一期有 2 家还缺料,清单贴在左边。';

// 授权卡桩:形状逐键抄 services/steward/authz.py 的 _CARD_PUBLIC_KEYS(冻结契约),
// 不多不少 —— args_fp 等内部字段后端永不外泄,桩里也不许有。
function authzCard(status) {
    const pending = status === 'pending';
    return {
        token: 'tok-e2e-authz-0001',
        tool: 'erp_push_sales_summary',
        title: '把 SM 2569-06 的销项汇总推送进 Express(影响 3 条,可在 Express 撤销)',
        risk: 'write',
        args: { client: 'SM', period: '2569-06', rows: '3' },
        status,
        requested_at: new Date(Date.now() - 5000).toISOString(),
        expires_at: new Date(Date.now() + 295000).toISOString(),
        decided_by: pending ? null : 'u1',
        decided_at: pending ? null : new Date().toISOString(),
    };
}

// 等批文的任务:status=waiting_user + 工具步 waiting_auth + 顶层 authorization(冻结契约)。
function waitingAuthzPayload() {
    const t = taskPayload('running');
    t.status = 'waiting_user';
    t.steps = [
        { id: 's1', label: '解析期间', state: 'done', detail: '2569-06', links: [] },
        { id: 's2', label: '推送销项汇总', state: 'waiting_auth', detail: '等你批准' },
    ];
    t.authorization = authzCard('pending');
    return t;
}

// 人拒/人取消后的终态:error_code + error_reason(人话)照 store.public_task 的输出形状。
function cancelledPayload(code, reason, authStatus) {
    const t = taskPayload('running');
    t.status = 'cancelled';
    t.steps = [
        { id: 's1', label: '解析期间', state: 'done', detail: '2569-06', links: [] },
        { id: 's2', label: '推送销项汇总', state: 'failed', detail: reason },
    ];
    t.error_code = code;
    t.error_reason = reason;
    if (authStatus) t.authorization = authzCard(authStatus);
    return t;
}

function json(route, payload) {
    return route.fulfill({ contentType: 'application/json', body: JSON.stringify(payload) });
}

async function boot(page, opts) {
    opts = opts || {};
    const gate = opts.stewardEnabled !== false;
    const taskStates = opts.taskStates || ['running'];
    let taskCall = 0;
    // 记下打到管家端点的每个 POST(路径 + body),断言「点了按钮真发了什么」用。
    const posts = [];
    let sessionPosts = 0;

    await page.route('**/api/me**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{"username":"skin"}' })
    );
    await page.route('**/api/workorder/orders**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{"orders":[]}' })
    );
    // 管家五端点走一个 handler 按 path 分派:多个 glob 会互相盖(.../sessions** 会把
    // .../sessions/s1/messages 一并吃掉),分派表一眼看得出哪条 URL 回什么。
    await page.route('**/api/ai/steward/**', (r) => {
        const p = new URL(r.request().url()).pathname;
        if (r.request().method() === 'POST') {
            posts.push({ path: p, body: r.request().postDataJSON() });
        }
        if (p.endsWith('/steward/status')) return json(r, { enabled: gate });
        // B3 决断二端点:成功响应 {task_id, authorization}(状态已翻)——冻结契约。
        if (p.endsWith('/authorizations/approve')) {
            return json(r, { task_id: 't1', authorization: authzCard('approved') });
        }
        if (p.endsWith('/authorizations/reject')) {
            return json(r, { task_id: 't1', authorization: authzCard('rejected') });
        }
        if (p.endsWith('/cancel')) {
            return json(
                r,
                cancelledPayload('steward.cancelled', '你取消了这条任务,后面的步骤没有跑。')
            );
        }
        if (p.endsWith('/messages')) {
            if (opts.sendFails) {
                return r.fulfill({
                    status: 500,
                    contentType: 'application/json',
                    body: '{"detail":{"code":"generic"}}',
                });
            }
            // 超限轮(冻结契约):reply 即人话,budget 三键,无 task_id(不建任务)。
            if (opts.budget) {
                return json(r, {
                    message_id: 'm1',
                    user_message_id: 'um1',
                    reply: '这个会话的 AI 花费到上限了(฿5.00),先停在这里。开个新会话继续,或让管理员调高上限。',
                    budget: {
                        code: 'steward.budget_session_exceeded',
                        cap_thb: '5.00',
                        spent_thb: '5.02',
                    },
                });
            }
            return json(r, { message_id: 'm1', reply: REPLY, task_id: 't1' });
        }
        if (p.indexOf('/steward/tasks/') >= 0) {
            // taskSeq 优先(整份载荷桩,授权卡/终态流转用);否则按状态名走老路。
            if (opts.taskSeq) {
                const payload = opts.taskSeq[Math.min(taskCall, opts.taskSeq.length - 1)];
                taskCall += 1;
                return json(r, payload);
            }
            const state = taskStates[Math.min(taskCall, taskStates.length - 1)];
            taskCall += 1;
            return json(r, taskPayload(state));
        }
        // GET /sessions/{sid}:服务端权威消息流(前端回本页/任务收尾时重建)。
        if (/\/steward\/sessions\/[^/]+$/.test(p)) {
            return json(r, {
                session_id: 's1',
                messages: [
                    { role: 'user', text: '本期谁缺料', ts: '2026-07-26T09:05:00Z' },
                    { role: 'steward', text: REPLY, ts: '2026-07-26T09:05:04Z', task_id: 't1' },
                ],
                current_task_id: 't1',
            });
        }
        if (p.endsWith('/steward/sessions')) sessionPosts += 1;
        return json(r, { session_id: 's' + sessionPosts });
    });
    await page.route('**/api/**', (r) => {
        const url = r.request().url();
        if (url.includes('/api/me') || url.includes('/api/workorder/orders')) return r.fallback();
        if (url.includes('/api/ai/steward/')) return r.fallback();
        return r.fulfill({ contentType: 'application/json', body: '{}' });
    });
    await page.addInitScript(() => {
        window.localStorage.setItem('mrpilot_token_ai', 'tok-b2m1');
        window.localStorage.setItem('mrpilot_lang', 'zh');
    });
    await page.goto(`${BASE}/static/dist/ai.html${opts.hash || ''}`);
    return { posts };
}

async function bg(page, selector) {
    return page.locator(selector).evaluate((el) => getComputedStyle(el).backgroundColor);
}

test.describe('智能管家 B2-M1(本地 stub · 真构建产物)', () => {
    test('闸开:命令条在矩阵上方 · 四个 chips · 侧栏有管家', async ({ page }) => {
        await boot(page);
        await page.waitForSelector('#stwBar .stw-bar-row', { state: 'visible', timeout: 15000 });
        await expect(page.locator('#navSteward')).toBeVisible();
        await expect(page.locator('#stwBar .stw-chip')).toHaveCount(4);
        // 「上方」不是看代码顺序,是看真实几何:命令条底边必须在矩阵区顶边之上。
        const bar = await page.locator('#stwBar').boundingBox();
        const matrix = await page.locator('#matrixSection').boundingBox();
        expect(bar.y + bar.height).toBeLessThanOrEqual(matrix.y);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '01-bar-on-dashboard.png'),
            fullPage: true,
        });
    });

    test('点 chip → 进管家页 · 对话上屏 · 左窗五态各是各的色族', async ({ page }) => {
        await boot(page);
        await page.waitForSelector('#stwBar .stw-chip', { state: 'visible', timeout: 15000 });
        const chipText = await page.locator('#stwBar .stw-chip').first().innerText();
        await page.locator('#stwBar .stw-chip').first().click();
        await page.waitForSelector('#v-steward.on', { state: 'visible', timeout: 15000 });
        expect(page.url()).toContain('#/steward');

        // 用户气泡 = 点的那条 chip 原话;管家气泡 = 后端 reply(前端不自己编措辞)。
        await expect(page.locator('.stw-msg.me .stw-bubble').first()).toContainText(chipText);
        await expect(page.locator('.stw-msg.agent .stw-bubble').first()).toContainText('还缺料');

        // 左窗:任务标题 + 查询次数 + 五个步骤。
        await page.waitForSelector('#stwLeft .stw-task', { state: 'visible', timeout: 15000 });
        await expect(page.locator('#stwLeft .panel .hd h3')).toContainText('缺料盘点');
        await expect(page.locator('#stwLeft .stw-meta')).toContainText('查询 3 次');
        await expect(page.locator('#stwLeft .stw-step')).toHaveCount(5);

        // 五个 state → 五个 B1 色族类,且真有色差(同一片灰 = 状态语言白写了)。
        const fams = ['st-ok', 'st-run', 'st-off', 'st-warn', 'st-err'];
        for (let i = 0; i < fams.length; i++) {
            await expect(
                page.locator(`#stwLeft .stw-step:nth-child(${i + 1}) .st-badge`)
            ).toHaveClass(new RegExp(fams[i]));
        }
        const colors = [];
        for (let i = 1; i <= 5; i++) {
            colors.push(await bg(page, `#stwLeft .stw-step:nth-child(${i}) .st-badge`));
        }
        expect(new Set(colors).size).toBe(5);

        // 执行中那一步有三点(活着的证据),排队中那步没有。
        await expect(page.locator('#stwLeft .stw-step:nth-child(2) .st-dots')).toBeVisible();
        expect(await page.locator('#stwLeft .stw-step:nth-child(3) .st-dots').count()).toBe(0);

        // 产物深链指回 SPA 内部(白名单只放 #/ 与同源路径)。
        await expect(page.locator('#stwLeft .stw-art .stw-link').first()).toHaveAttribute(
            'href',
            '#/client/c-sm/wo?period=2569-06'
        );
        await expect(page.locator('#stwLeft .stw-table tbody tr')).toHaveCount(2);

        // 表头按 label 显示、单元格按 column.key 从 dict 行取值,缺值给空格子。
        await expect(page.locator('#stwLeft .stw-table thead th')).toHaveText([
            '客户',
            '义务',
            '状态',
        ]);
        await expect(page.locator('#stwLeft .stw-table tbody tr').first().locator('td')).toHaveText(
            ['SM', 'PP30', 'missing_materials']
        );
        // 反证闸:任何一格印出 [object Object] = 契约又漂了(这次就是这么漏过去的)。
        const cellTexts = await page.locator('#stwLeft .stw-table td').allInnerTexts();
        expect(cellTexts.length).toBe(6);
        expect(cellTexts.join('|')).not.toContain('[object Object]');
        expect(cellTexts.join('|')).not.toContain('undefined');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '02-steward-two-pane.png'),
            fullPage: true,
        });
    });

    test('轮询把 running 翻成 done(5s 一跳 · 终态收口)', async ({ page }) => {
        await boot(page, { taskStates: ['running', 'done'] });
        await page.waitForSelector('#stwBar .stw-chip', { state: 'visible', timeout: 15000 });
        await page.locator('#stwBar .stw-chip').first().click();
        await page.waitForSelector('#stwLeft .stw-task', { state: 'visible', timeout: 15000 });
        await expect(page.locator('#stwLeft .panel .hd .st-badge')).toHaveClass(/st-run/);
        // 轮询 5s 后第二次回包是 done:任务徽章翻绿、第三步从排队灰变完成绿。
        await expect(page.locator('#stwLeft .panel .hd .st-badge')).toHaveClass(/st-ok/, {
            timeout: 20000,
        });
        await expect(page.locator('#stwLeft .stw-step:nth-child(3) .st-badge')).toHaveClass(
            /st-ok/
        );
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '03-task-done-after-poll.png'),
            fullPage: true,
        });
    });

    test('深链点了真跳客户页并带期间', async ({ page }) => {
        await boot(page);
        await page.waitForSelector('#stwBar .stw-chip', { state: 'visible', timeout: 15000 });
        await page.locator('#stwBar .stw-chip').first().click();
        await page.waitForSelector('#stwLeft .stw-art .stw-link', {
            state: 'visible',
            timeout: 15000,
        });
        await page.locator('#stwLeft .stw-art .stw-link').first().click();
        await page.waitForFunction(() => window.location.hash.indexOf('#/client/') === 0, null, {
            timeout: 10000,
        });
        expect(page.url()).toContain('period=2569-06');
    });

    test('闸关:侧栏没有管家 · 命令条不渲染 · 深链落回工作台', async ({ page }) => {
        await boot(page, { stewardEnabled: false, hash: '#/steward' });
        await page.waitForSelector('#v-dashboard.on', { state: 'visible', timeout: 15000 });
        await page.waitForFunction(() => window.location.hash === '#/', null, { timeout: 10000 });
        await expect(page.locator('#navSteward')).toBeHidden();
        await expect(page.locator('#stwBar')).toBeHidden();
        expect(await page.locator('#stwBar').innerHTML()).toBe('');
        await expect(page.locator('#v-steward')).toBeHidden();
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '04-gate-closed-dashboard.png'),
            fullPage: true,
        });
    });

    test('手机 390px:单栏 · 状态卡在对话上方 · 无横向滚动', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await boot(page);
        await page.waitForSelector('#stwBar .stw-chip', { state: 'visible', timeout: 15000 });
        await page.locator('#stwBar .stw-chip').first().click();
        await page.waitForSelector('#stwLeft .stw-task', { state: 'visible', timeout: 15000 });
        const left = await page.locator('.stw-left').boundingBox();
        const right = await page.locator('.stw-right').boundingBox();
        // 单栏:两块同一列(左边界相同),状态卡在对话之上。
        expect(Math.abs(left.x - right.x)).toBeLessThan(2);
        expect(left.y + left.height).toBeLessThanOrEqual(right.y + 2);
        const overflow = await page.evaluate(
            () => document.documentElement.scrollWidth - window.innerWidth
        );
        expect(overflow).toBeLessThanOrEqual(0);
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '05-mobile-390-top.png') });

        // 滚到底:sticky 输入条不许压住最后一条消息(手机上被输入条盖掉的对话 = 看不见)。
        await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
        await page.waitForTimeout(300);
        const lastMsg = await page.locator('.stw-msg').last().boundingBox();
        const composer = await page.locator('.stw-composer').boundingBox();
        expect(lastMsg.y + lastMsg.height).toBeLessThanOrEqual(composer.y + 1);
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '05-mobile-390-bottom.png') });
    });

    test('送不出去时说人话:错误横幅 + 用户那条留在原地可重发', async ({ page }) => {
        await boot(page, { sendFails: true });
        await page.waitForSelector('#stwBar .stw-chip', { state: 'visible', timeout: 15000 });
        await page.locator('#stwBar .stw-chip').first().click();
        await page.waitForSelector('#v-steward.on', { state: 'visible', timeout: 15000 });
        await expect(page.locator('.stw-err')).toBeVisible();
        // 用户打的字不被吞:气泡还在,旁边有「重发」。
        await expect(page.locator('.stw-msg.me .stw-bubble')).toHaveCount(1);
        await expect(page.locator('[data-action="stw-resend"]')).toBeVisible();
        // 左窗没有任务就照实说空,不摆一个假的执行中。
        await expect(page.locator('#stwLeft [data-state="empty"]')).toBeVisible();
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '06-send-failed-honest.png'),
            fullPage: true,
        });
    });
});

// B3:写授权卡 / 取消 / 成本封顶 / 文案纠偏。桩形状逐键对齐冻结契约
// (routes/steward_routes.py 顶注 + authz.public_authorization_card + orchestrator budget)。
test.describe('智能管家 B3(授权卡 · 取消 · 预算 · 本地 stub)', () => {
    async function openWithTask(page, opts) {
        const h = await boot(page, opts);
        await page.waitForSelector('#stwBar .stw-chip', { state: 'visible', timeout: 15000 });
        await page.locator('#stwBar .stw-chip').first().click();
        await page.waitForSelector('#v-steward.on', { state: 'visible', timeout: 15000 });
        return h;
    }

    test('待批卡:说清做什么 · 批/拒两动作 · 倒计时活的 · 文案不承诺没有的能力', async ({
        page,
    }) => {
        await openWithTask(page, { taskSeq: [waitingAuthzPayload()] });
        await page.waitForSelector('.stw-authz', { state: 'visible', timeout: 15000 });

        // 卡自述:标题(要对哪个账套做什么/影响几条/可不可撤销)+ 待批徽章 + 风险徽章。
        await expect(page.locator('.stw-authz-title')).toContainText('SM 2569-06');
        await expect(page.locator('.stw-authz-title')).toContainText('可在 Express 撤销');
        await expect(page.locator('.stw-authz .st-badge').first()).toHaveClass(/st-warn/);
        // 参数逐行摆给人复核(3 个槽 = 3 行)。
        await expect(page.locator('.stw-authz-args dt')).toHaveCount(3);
        await expect(page.locator('[data-action="stw-authz-approve"]')).toBeVisible();
        await expect(page.locator('[data-action="stw-authz-reject"]')).toBeVisible();
        // 倒计时真在走:两次采样文字不同(纯静态字符串 = 死表)。
        const cd1 = await page.locator('#stwAuthzCd').innerText();
        await page.waitForTimeout(2200);
        const cd2 = await page.locator('#stwAuthzCd').innerText();
        expect(cd1).toMatch(/\d+:\d\d/);
        expect(cd2).not.toBe(cd1);
        // 工具步是 waiting_auth 橙(B1 既有色族,契约点名)。
        await expect(page.locator('.stw-step:nth-child(2) .st-badge')).toHaveClass(/st-warn/);
        // 文案与能力一致(双向闸在 tests/unit/test_ai_steward_pure.py):闭集里已经有写工具
        // (erp_push),页面自述就必须说「会改数据的操作要你先批准」,不许再自称只查不改。
        const noteTexts = await page.evaluate(() => [
            document.querySelector('#v-steward .board-head .note').textContent,
            document.querySelector('.stw-composer-note').textContent,
        ]);
        for (const t of noteTexts) {
            expect(t).not.toContain('只查不改数');
            expect(t).toContain('会改数据的操作需你先批准');
        }
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '07-authz-pending-card.png'),
            fullPage: true,
        });
    });

    test('批准:POST approve 带 token · 任务复跑回 running', async ({ page }) => {
        const h = await openWithTask(page, {
            taskSeq: [waitingAuthzPayload(), taskPayload('running')],
        });
        await page.waitForSelector('[data-action="stw-authz-approve"]', {
            state: 'visible',
            timeout: 15000,
        });
        await page.locator('[data-action="stw-authz-approve"]').click();
        await expect(page.locator('#stwLeft .panel .hd .st-badge')).toHaveClass(/st-run/, {
            timeout: 15000,
        });
        const approvePost = h.posts.find((x) => x.path.endsWith('/authorizations/approve'));
        expect(approvePost.body).toEqual({ token: 'tok-e2e-authz-0001' });
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '08-authz-approved-resumed.png'),
            fullPage: true,
        });
    });

    test('拒绝:任务收 cancelled · 灰徽章 + 人话原因 + 已拒卡盖章', async ({ page }) => {
        const h = await openWithTask(page, {
            taskSeq: [
                waitingAuthzPayload(),
                cancelledPayload(
                    'steward.authz_rejected',
                    '这个操作被拒绝了,一步都没有执行。要做的话重新说一次、批准后才会动手。',
                    'rejected'
                ),
            ],
        });
        await page.waitForSelector('[data-action="stw-authz-reject"]', {
            state: 'visible',
            timeout: 15000,
        });
        await page.locator('[data-action="stw-authz-reject"]').click();
        await expect(page.locator('#stwLeft .panel .hd .st-badge')).toHaveClass(/st-off/, {
            timeout: 15000,
        });
        // 原因面:人话 + 机器码,cancelled 用中性灰(人停的不是错误红)。
        await expect(page.locator('.stw-reason')).toContainText('一步都没有执行');
        await expect(page.locator('.stw-reason code')).toContainText('steward.authz_rejected');
        await expect(page.locator('.stw-reason')).toHaveClass(/off/);
        // 卡已盖「已拒绝」章,批/拒按钮消失(不摆点了才知道死了的按钮)。
        expect(await page.locator('[data-action="stw-authz-approve"]').count()).toBe(0);
        expect(h.posts.some((x) => x.path.endsWith('/authorizations/reject'))).toBe(true);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '09-authz-rejected-cancelled.png'),
            fullPage: true,
        });
    });

    test('执行中可取消:点取消 → POST cancel → 终态灰 + 原因 + 按钮收走', async ({ page }) => {
        const h = await openWithTask(page, { taskStates: ['running'] });
        await page.waitForSelector('[data-action="stw-cancel"]', {
            state: 'visible',
            timeout: 15000,
        });
        await page.locator('[data-action="stw-cancel"]').click();
        await expect(page.locator('#stwLeft .panel .hd .st-badge')).toHaveClass(/st-off/, {
            timeout: 15000,
        });
        await expect(page.locator('.stw-reason')).toContainText('你取消了这条任务');
        expect(await page.locator('[data-action="stw-cancel"]').count()).toBe(0);
        expect(h.posts.some((x) => x.path.endsWith('/cancel'))).toBe(true);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '10-cancel-running-task.png'),
            fullPage: true,
        });
    });

    test('会话超限:人话 + 已用/上限数字 + 「开新会话」真开新会话', async ({ page }) => {
        const h = await openWithTask(page, { budget: true });
        await page.waitForSelector('.stw-budget', { state: 'visible', timeout: 15000 });
        // reply 人话在气泡里,数字块给已用/上限(decimal 字符串原样印,不重算)。
        await expect(page.locator('.stw-msg.agent .stw-bubble')).toContainText('฿5.00');
        await expect(page.locator('.stw-budget')).toContainText('5.02');
        await expect(page.locator('.stw-budget')).toContainText('5.00');
        // 超限轮不建任务:左窗诚实空态,不摆假执行中。
        await expect(page.locator('#stwLeft [data-state="empty"]')).toBeVisible();
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '11-budget-session-exceeded.png'),
            fullPage: true,
        });
        await page.locator('[data-action="stw-new-session"]').click();
        // 出口是真的:第二次 POST /sessions 打出去,对话面回到空态指路。
        await expect(page.locator('.stw-feed-empty')).toBeVisible({ timeout: 10000 });
        const sessionPosts = h.posts.filter((x) => x.path.endsWith('/steward/sessions'));
        expect(sessionPosts.length).toBe(2);
    });
});
