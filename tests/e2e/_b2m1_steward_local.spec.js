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

// GET /status 的第二个键,值取自 services/steward/attachments.limits()(fixture 与后端
// 逐键相等由 tests/unit/test_e2e_stub_contract_gate.py 锁住)。真后端
// (routes/steward_routes.get_status)【无条件】把它带出去,闸关也带 —— 桩此前只回
// {enabled},于是这批用例里 composer 一路走的都是「没有附件口」那条分支:回形针没渲染、
// 输入区注脚没渲染、占位符是短的那句,连截图证据一起失真了。桩比真后端少给东西 = 假绿。
const ATTACH_LIMITS = require('./_fixtures_steward_limits.json');

const REPLY = '这一期有 2 家还缺料,清单贴在左边。';
// 任务落终态时服务端往会话追写的收尾那句(worker._finalize_result)。POST /messages 的即时
// 应承里没有它,只有 GET /sessions 吐得出来 —— 前端不去拉,这句就永远上不了屏。
const CLOSEOUT = '查完了:SM、MR.ERP 两家缺料,清单已经贴在左边。';

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
    // 各 GET 端点被打了几次:「补一次就够」「没多打一遍」这类幂等断言 DOM 上看不出来。
    const hits = { task: 0, session: 0 };
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
        // 限额跟着闸态一起回:真后端不看闸开没开,attachments 一律带(见 get_status)。
        if (p.endsWith('/steward/status'))
            return json(r, { enabled: gate, attachments: ATTACH_LIMITS });
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
            const nth = hits.task;
            hits.task += 1;
            // taskSeq 优先(整份载荷桩,授权卡/终态流转用);否则按状态名走老路。
            if (opts.taskSeq) {
                return json(r, opts.taskSeq[Math.min(nth, opts.taskSeq.length - 1)]);
            }
            return json(r, taskPayload(taskStates[Math.min(nth, taskStates.length - 1)]));
        }
        // GET /sessions/{sid}:服务端权威消息流(前端回本页/任务收尾时重建)。
        if (/\/steward\/sessions\/[^/]+$/.test(p)) {
            hits.session += 1;
            const messages = [
                { role: 'user', text: '本期谁缺料', ts: '2026-07-26T09:05:00Z' },
                { role: 'steward', text: REPLY, ts: '2026-07-26T09:05:04Z', task_id: 't1' },
            ];
            // closeout:任务已收尾的账套 —— 服务端多吐一条收尾追写(默认关,老用例不受影响)。
            if (opts.closeout) {
                messages.push({
                    role: 'steward',
                    text: CLOSEOUT,
                    ts: '2026-07-26T09:05:09Z',
                    task_id: 't1',
                });
            }
            return json(r, { session_id: 's1', messages, current_task_id: 't1' });
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
    return { posts, hits };
}

async function bg(page, selector) {
    return page.locator(selector).evaluate((el) => getComputedStyle(el).backgroundColor);
}

test.describe('智能管家 B2-M1(本地 stub · 真构建产物)', () => {
    test('闸开:工作台无命令条(2026-08-07 拍板删除)· 侧栏有管家', async ({ page }) => {
        await boot(page);
        await page.waitForSelector('#matrixSection', { state: 'visible', timeout: 15000 });
        await expect(page.locator('#navSteward')).toBeVisible();
        // 命令条整块已按拍板删除:工作台只留矩阵/看板,问事情去管家页。
        await expect(page.locator('#stwBar')).toHaveCount(0);
        await expect(page.locator('.stw-bar-row')).toHaveCount(0);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '01-bar-on-dashboard.png'),
            fullPage: true,
        });
    });

    test('管家页打字提问 · 对话上屏 · 左窗五态各是各的色族', async ({ page }) => {
        // 命令条已删,入口=侧栏进管家页自己打字(与真实用户动线一致)。
        const chipText = '本期谁缺料';
        await boot(page, { hash: '#/steward' });
        await page.waitForSelector('#v-steward.on', { state: 'visible', timeout: 15000 });
        expect(page.url()).toContain('#/steward');
        await page.fill('#stwInput', chipText);
        await page.locator('.stw-send-btn').click();

        // 用户气泡 = 打的原话;管家气泡 = 后端 reply(前端不自己编措辞)。
        await expect(page.locator('.stw-msg.me .stw-bubble').first()).toContainText(chipText);
        await expect(page.locator('.stw-msg.agent .stw-ai-body').first()).toContainText('还缺料');

        // 过程条:聊天标题 = 用户这轮原话;任务摘要 + 查询次数 + 五个步骤(S1 起挂在对话流里)。
        // 2026-08-07 拍板:执行过程条默认恒折叠 —— 先断言默认收起,再点开验内容。
        await page.waitForSelector('.stw-msg.agent .stw-proc', {
            state: 'visible',
            timeout: 15000,
        });
        await expect(page.locator('.stw-msg.agent .stw-proc .stw-steps')).not.toBeVisible();
        await page.locator('.stw-msg.agent .stw-proc .stw-proc-hd').click();
        await expect(page.locator('.stw-msg.agent .stw-proc .stw-proc-hd')).toContainText(
            '查事务所矩阵'
        );
        await expect(page.locator('.stw-msg.agent .stw-proc .stw-meta')).toContainText('查询 3 次');
        await expect(page.locator('.stw-msg.agent .stw-proc .stw-steps .stw-step')).toHaveCount(5);

        // 五个 state → 五个 B1 色族类,且真有色差(同一片灰 = 状态语言白写了)。
        const fams = ['st-ok', 'st-run', 'st-off', 'st-warn', 'st-err'];
        for (let i = 0; i < fams.length; i++) {
            await expect(
                page.locator(
                    `.stw-msg.agent .stw-proc .stw-steps .stw-step:nth-child(${i + 1}) .st-badge`
                )
            ).toHaveClass(new RegExp(fams[i]));
        }
        const colors = [];
        for (let i = 1; i <= 5; i++) {
            colors.push(
                await bg(
                    page,
                    `.stw-msg.agent .stw-proc .stw-steps .stw-step:nth-child(${i}) .st-badge`
                )
            );
        }
        expect(new Set(colors).size).toBe(5);

        // 执行中那一步有三点(活着的证据),排队中那步没有。
        await expect(
            page.locator('.stw-msg.agent .stw-proc .stw-steps .stw-step:nth-child(2) .st-dots')
        ).toBeVisible();
        expect(
            await page
                .locator('.stw-msg.agent .stw-proc .stw-steps .stw-step:nth-child(3) .st-dots')
                .count()
        ).toBe(0);

        // 产物深链指回 SPA 内部(白名单只放 #/ 与同源路径)。
        await expect(
            page.locator('.stw-msg.agent .stw-ai-flow .stw-art .stw-link').first()
        ).toHaveAttribute('href', '#/client/c-sm/wo?period=2569-06');
        await expect(page.locator('.stw-msg.agent .stw-ai-flow .stw-table tbody tr')).toHaveCount(
            2
        );

        // 表头按 label 显示、单元格按 column.key 从 dict 行取值,缺值给空格子。
        await expect(page.locator('.stw-msg.agent .stw-ai-flow .stw-table thead th')).toHaveText([
            '客户',
            '义务',
            '状态',
        ]);
        await expect(
            page.locator('.stw-msg.agent .stw-ai-flow .stw-table tbody tr').first().locator('td')
        ).toHaveText(['SM', 'PP30', 'missing_materials']);
        // 反证闸:任何一格印出 [object Object] = 契约又漂了(这次就是这么漏过去的)。
        const cellTexts = await page
            .locator('.stw-msg.agent .stw-ai-flow .stw-table td')
            .allInnerTexts();
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
        // 命令条已删(2026-08-07 拍板):入场=管家页打字发送,与真实动线一致。
        await page.evaluate(() => {
            location.hash = '#/steward';
        });
        await page.waitForSelector('#stwInput', { state: 'visible', timeout: 15000 });
        await page.fill('#stwInput', '本期谁缺料');
        await page.locator('.stw-send-btn').click();
        await page.waitForSelector('.stw-msg.agent .stw-proc', {
            state: 'visible',
            timeout: 15000,
        });
        await expect(page.locator('.stw-msg.agent .stw-proc .stw-proc-hd .st-badge')).toHaveClass(
            /st-run/
        );
        // 轮询 5s 后第二次回包是 done:任务徽章翻绿、第三步从排队灰变完成绿。
        await expect(page.locator('.stw-msg.agent .stw-proc .stw-proc-hd .st-badge')).toHaveClass(
            /st-ok/,
            {
                timeout: 20000,
            }
        );
        await expect(
            page.locator('.stw-msg.agent .stw-proc .stw-steps .stw-step:nth-child(3) .st-badge')
        ).toHaveClass(/st-ok/);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '03-task-done-after-poll.png'),
            fullPage: true,
        });
    });

    // 工具比第一拍还快时任务已经是终态,轮询压根不启动 —— 收尾追写此前只挂在轮询的
    // onTerminal 上,于是右窗停在「我去查」,答复要等人离页回页才补得上。
    test('首拍就是终态:收尾那句当场补回来,不用离页回页', async ({ page }) => {
        const h = await boot(page, { taskStates: ['done'], closeout: true });
        // 命令条已删(2026-08-07 拍板):入场=管家页打字发送,与真实动线一致。
        await page.evaluate(() => {
            location.hash = '#/steward';
        });
        await page.waitForSelector('#stwInput', { state: 'visible', timeout: 15000 });
        await page.fill('#stwInput', '本期谁缺料');
        await page.locator('.stw-send-btn').click();
        await page.waitForSelector('.stw-msg.agent .stw-proc', {
            state: 'visible',
            timeout: 15000,
        });
        await expect(page.locator('.stw-msg.agent .stw-proc .stw-proc-hd .st-badge')).toHaveClass(
            /st-ok/
        );

        // 收尾那句真上屏:管家消息两条(即时应承 + 服务端追写),末条是收尾。
        const agent = page.locator('.stw-msg.agent .stw-ai-body');
        await expect(agent).toHaveCount(2, { timeout: 15000 });
        await expect(agent.last()).toContainText(CLOSEOUT);

        // 反证一:全程没离开过管家页 —— 补上来的不是 mount 那次 syncSession 的功劳。
        expect(page.url()).toContain('#/steward');
        await page.waitForTimeout(500); // 数「没多打」之前先让后续请求有机会发出来
        // 反证二:任务只拉了一次(终态没启动轮询),修的确实是首拍这条路。
        expect(h.hits.task).toBe(1);
        // 反证三:会话只补一次 —— 多打一次就是把 syncSession 触发成了两遍。
        expect(h.hits.session).toBe(1);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '12-first-poll-terminal-closeout.png'),
            fullPage: true,
        });
    });

    // fromSync 守卫的反证:syncSession → loadTask(终态)→ syncSession 会串成两次拉取。
    test('回页时手上没有任务:会话端点只补一次,不来回串', async ({ page }) => {
        const h = await boot(page, { taskStates: ['done'], closeout: true, hash: '#/steward' });
        // 首次挂载只建会话不同步,等空态出来说明会话已落地。
        await page.waitForSelector('.stw-welcome', { state: 'visible', timeout: 15000 });
        expect(h.hits.session).toBe(0);

        await page.evaluate(() => {
            window.location.hash = '#/';
        });
        await expect(page.locator('#v-steward')).not.toHaveClass(/\bon\b/);
        await page.evaluate(() => {
            window.location.hash = '#/steward';
        });
        await expect(page.locator('.stw-msg.agent .stw-ai-body').last()).toContainText(CLOSEOUT, {
            timeout: 15000,
        });
        // 回页拉一次会话 → 发现有在跑的任务 → 拉任务(loadTask)+ backfill 补拉各一次。
        // 会话端点只打一次:不来回串。任务两条 = loadTask 本体 + backfill 补拉(历史轮过程条)。
        await expect.poll(() => h.hits.task).toBe(2);
        await page.waitForTimeout(500);
        expect(h.hits.session).toBe(1);
        expect(h.hits.task).toBe(2);
    });

    test('深链点了真跳客户页并带期间', async ({ page }) => {
        await boot(page);
        // 命令条已删(2026-08-07 拍板):入场=管家页打字发送,与真实动线一致。
        await page.evaluate(() => {
            location.hash = '#/steward';
        });
        await page.waitForSelector('#stwInput', { state: 'visible', timeout: 15000 });
        await page.fill('#stwInput', '本期谁缺料');
        await page.locator('.stw-send-btn').click();
        await page.waitForSelector('.stw-msg.agent .stw-ai-flow .stw-art .stw-link', {
            state: 'visible',
            timeout: 15000,
        });
        await page.locator('.stw-msg.agent .stw-ai-flow .stw-art .stw-link').first().click();
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
        await expect(page.locator('#stwBar')).toHaveCount(0);
        await expect(page.locator('#v-steward')).toBeHidden();
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '04-gate-closed-dashboard.png'),
            fullPage: true,
        });
    });

    test('手机 390px:单栏 · 状态卡在对话上方 · 无横向滚动', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await boot(page);
        // 命令条已删(2026-08-07 拍板):入场=管家页打字发送,与真实动线一致。
        await page.evaluate(() => {
            location.hash = '#/steward';
        });
        await page.waitForSelector('#stwInput', { state: 'visible', timeout: 15000 });
        await page.fill('#stwInput', '本期谁缺料');
        await page.locator('.stw-send-btn').click();
        await page.waitForSelector('.stw-msg.agent .stw-proc', {
            state: 'visible',
            timeout: 15000,
        });
        // 单栏:对话流铺满视口宽(没有并排分栏),过程条在对话里。
        const feed = await page.locator('.stw-feed').boundingBox();
        const chat = await page.locator('.stw-chat-main').boundingBox();
        expect(Math.abs(feed.x - chat.x)).toBeLessThan(2);
        expect(feed.width).toBeGreaterThanOrEqual(chat.width - 2);
        const overflow = await page.evaluate(
            () => document.documentElement.scrollWidth - window.innerWidth
        );
        expect(overflow).toBeLessThanOrEqual(0);

        // 输入区是完整件:回形针 + 「或拖入文件」占位符 + 注脚。这两张手机图是几何证据,
        // 缺件的输入区量出来的宽度全是假的 —— 回形针挤掉 52px 之后送出按钮才是真的窄。
        await expect(page.locator('.stw-clip')).toBeVisible();
        expect(await page.locator('#stwInput').getAttribute('placeholder')).toContain('拖入文件');
        // 回形针挤掉一截行宽之后,剩下两件不许被压到裁字 —— 判据是 clientWidth 装不装得下
        // scrollWidth,不是「框还在」。触控目标那条在 _f1_steward_attach_local,不重复一遍。
        const squeezed = await page.evaluate(() =>
            [
                '#stwInput',
                '.stw-composer [data-action="stw-send"], .stw-composer [data-action="stw-stop"]',
            ].filter((s) => {
                const el = document.querySelector(s);
                return el.clientWidth < el.scrollWidth;
            })
        );
        expect(squeezed).toEqual([]);
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
        // 命令条已删(2026-08-07 拍板):入场=管家页打字发送,与真实动线一致。
        await page.evaluate(() => {
            location.hash = '#/steward';
        });
        await page.waitForSelector('#stwInput', { state: 'visible', timeout: 15000 });
        await page.fill('#stwInput', '本期谁缺料');
        await page.locator('.stw-send-btn').click();
        await page.waitForSelector('#v-steward.on', { state: 'visible', timeout: 15000 });
        await expect(page.locator('.stw-err')).toBeVisible();
        // 用户打的字不被吞:气泡还在,旁边有「重发」。
        await expect(page.locator('.stw-msg.me .stw-bubble')).toHaveCount(1);
        await expect(page.locator('[data-action="stw-resend"]')).toBeVisible();
        // 左窗没有任务就照实说空,不摆一个假的执行中。
        await expect(page.locator('.stw-msg.agent .stw-proc')).toHaveCount(0);
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
        // 命令条已删(2026-08-07 拍板):入场=管家页打字发送,与真实动线一致。
        await page.evaluate(() => {
            location.hash = '#/steward';
        });
        await page.waitForSelector('#stwInput', { state: 'visible', timeout: 15000 });
        await page.fill('#stwInput', '本期谁缺料');
        await page.locator('.stw-send-btn').click();
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
        // S1 起这条自述落在欢迎屏能力行(stw_note),不再有独立页头 note。
        await expect(page.locator('.stw-authz-title')).toContainText('撤销');
        // 这句只在页头印一次:composer 注脚曾经复读同一句,是同屏第二遍,已删。守的是
        // 「同屏不复读」,不是「注脚不许存在」—— 有附件口时注脚回来,但只说输入框自己
        // 给不出的那件事(文件能拖能粘)。原来那条 toHaveCount(0) 只在「没有附件口」的
        // 前提下成立,而那个前提是桩漏给 attachments 造出来的,产品里不存在。
        await expect(page.locator('.stw-comp-note')).toHaveCount(1);
        const composerNote = await page.locator('.stw-comp-note').innerText();
        expect(composerNote).toContain('文件');
        expect(composerNote).not.toContain('撤销');
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
        await expect(page.locator('.stw-msg.agent .stw-proc .stw-proc-hd .st-badge')).toHaveClass(
            /st-run/,
            {
                timeout: 15000,
            }
        );
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
        await expect(page.locator('.stw-msg.agent .stw-proc .stw-proc-hd .st-badge')).toHaveClass(
            /st-off/,
            {
                timeout: 15000,
            }
        );
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
        await page.waitForSelector('[data-action="stw-stop"]', {
            state: 'visible',
            timeout: 15000,
        });
        await page.locator('[data-action="stw-stop"]').click();
        await expect(page.locator('.stw-msg.agent .stw-proc .stw-proc-hd .st-badge')).toHaveClass(
            /st-off/,
            {
                timeout: 15000,
            }
        );
        await expect(page.locator('.stw-reason')).toContainText('你取消了这条任务');
        expect(await page.locator('[data-action="stw-stop"]').count()).toBe(0);
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
        await expect(page.locator('.stw-msg.agent .stw-ai-body')).toContainText('฿5.00');
        await expect(page.locator('.stw-budget')).toContainText('5.02');
        await expect(page.locator('.stw-budget')).toContainText('5.00');
        // 超限轮不建任务:左窗诚实空态,不摆假执行中。
        await expect(page.locator('.stw-msg.agent .stw-proc')).toHaveCount(0);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '11-budget-session-exceeded.png'),
            fullPage: true,
        });
        await page.locator('[data-action="stw-new-session"]').first().click();
        // 出口是真的:第二次 POST /sessions 打出去,对话面回到空态指路。
        await expect(page.locator('.stw-welcome')).toBeVisible({ timeout: 10000 });
        const sessionPosts = h.posts.filter((x) => x.path.endsWith('/steward/sessions'));
        expect(sessionPosts.length).toBe(2);
    });
});
