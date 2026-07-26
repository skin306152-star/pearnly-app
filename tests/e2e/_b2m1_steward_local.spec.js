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

function json(route, payload) {
    return route.fulfill({ contentType: 'application/json', body: JSON.stringify(payload) });
}

async function boot(page, opts) {
    opts = opts || {};
    const gate = opts.stewardEnabled !== false;
    const taskStates = opts.taskStates || ['running'];
    let taskCall = 0;

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
        if (p.endsWith('/steward/status')) return json(r, { enabled: gate });
        if (p.endsWith('/messages')) {
            if (opts.sendFails) {
                return r.fulfill({
                    status: 500,
                    contentType: 'application/json',
                    body: '{"detail":{"code":"generic"}}',
                });
            }
            return json(r, { message_id: 'm1', reply: REPLY, task_id: 't1' });
        }
        if (p.indexOf('/steward/tasks/') >= 0) {
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
        return json(r, { session_id: 's1' });
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

        // 左窗:任务标题 + 3 个 Agent + 五个步骤。
        await page.waitForSelector('#stwLeft .stw-task', { state: 'visible', timeout: 15000 });
        await expect(page.locator('#stwLeft .panel .hd h3')).toContainText('缺料盘点');
        await expect(page.locator('#stwLeft .stw-meta')).toContainText('3 个 Agent');
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
