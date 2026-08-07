// 大脑循环左窗渲染验收 —— 步骤按真实条数画、失败的步骤留得住、追问那步的候选是能点的按钮。
// ============================================================
// 跑 static/dist 真构建产物(python http.server),API 走 page.route stub。
// 关键点:桩里那份任务载荷【不是手写的】—— 由真代码生成(loop_state.Ledger +
// loop_state.public_loop + store.public_task),生成命令见下面 GENERATOR。手写桩会造出
// 产品里根本不存在的形状,然后验证自己(2026-07-26 血泪:深链 35 条全落空却 16 项全绿)。
//
// 起法:npx playwright test tests/e2e/_steward_loop_ui_verify.spec.js
/* global window, getComputedStyle */

const { test, expect } = require('@playwright/test');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const fs = require('fs');

const ROOT = path.resolve(__dirname, '..', '..');
const PORT = 8993;
const BASE = `http://127.0.0.1:${PORT}`;
const ART = path.join(__dirname, '_artifacts', 'steward_loop_ui');
// 上传限额:真后端 GET /status 无条件带这一块(routes/steward_routes.py::get_status),
// 前端拿它才画回形针与输入区说明。同 TASK 一样,值取自真代码(attachments.limits()),不手写。
const LIMITS = require('./_fixtures_steward_limits.json');

// GENERATOR(改契约后重跑它,把输出贴回来):
//   python - <<'PY'
//   from unittest import mock; import json, datetime
//   from services.steward import loop_state, store, copy, copy_loop
//   steps = loop_state.initial_steps("zh")
//   with mock.patch.object(loop_state.Ledger, "_persist", lambda self: None):
//       led = loop_state.Ledger("t-1", "task-1", steps)
//       ... open/close 三步 ... ; steps = led.finish_final("", state=store.STEP_QUEUED)
//   print(json.dumps(store.public_task(row), ensure_ascii=False))
//   PY
const TASK = {
    task_id: 'task-1',
    title: 'sister 这期报完了没',
    status: 'waiting_user',
    started_at: '2026-07-27T02:05:00',
    finished_at: null,
    agent_count: 2,
    cancellable: false,
    steps: [
        { id: 's0', label: '听懂你要什么', state: 'done', detail: '', links: [] },
        {
            id: 's1',
            kind: 'tool',
            label: '查客户名录',
            state: 'done',
            detail: '「sister」名录里有 2 家:Sister Makeup, Sister Trading。',
            links: [],
        },
        {
            id: 's2',
            kind: 'tool',
            label: '查应交税额',
            state: 'failed',
            detail: '叫「sister」的有 2 家:Sister Makeup, Sister Trading。指明是哪一家。',
            links: [],
        },
        {
            id: 's3',
            kind: 'ask',
            label: '问你一件事',
            state: 'done',
            detail: '是 Sister Makeup 还是 Sister Trading?',
            links: [],
        },
        { id: 'final', label: '整理答复', state: 'queued', detail: '', links: [] },
    ],
    artifacts: [],
    loop: {
        calls: 3,
        tool_calls: 2,
        asked: 1,
        wrote: false,
        waiting_auth: false,
        question: {
            field: 'client_name',
            text: '是 Sister Makeup 还是 Sister Trading?',
            options: ['Sister Makeup', 'Sister Trading'],
        },
    },
};

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
    fs.mkdirSync(ART, { recursive: true });
    server = spawn('python', ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1'], {
        cwd: ROOT,
        stdio: 'ignore',
    });
    await waitUp(`${BASE}/static/dist/ai.html`);
});

test.afterAll(() => {
    if (server) server.kill();
});

function json(route, payload) {
    return route.fulfill({ contentType: 'application/json', body: JSON.stringify(payload) });
}

async function boot(page, opts) {
    opts = opts || {};
    const posts = [];
    await page.route('**/api/me**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{"username":"skin"}' })
    );
    await page.route('**/api/workorder/orders**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{"orders":[]}' })
    );
    await page.route('**/api/ai/steward/**', (r) => {
        const p = new URL(r.request().url()).pathname;
        if (r.request().method() === 'POST') {
            posts.push({ path: p, body: r.request().postDataJSON() });
        }
        if (p.endsWith('/steward/status')) {
            return json(r, { enabled: true, attachments: LIMITS });
        }
        if (p.endsWith('/messages')) {
            return json(r, { message_id: 'm2', user_message_id: 'um2', task_id: 'task-1' });
        }
        if (p.indexOf('/steward/tasks/') >= 0) {
            return json(r, Object.assign({}, TASK, opts.taskOverride || {}));
        }
        if (/\/steward\/sessions\/[^/]+$/.test(p)) {
            return json(r, {
                session_id: 's1',
                messages: [
                    { role: 'user', text: 'sister 这期报完了没' },
                    { role: 'steward', text: TASK.loop.question.text, task_id: 'task-1' },
                ],
                current_task_id: 'task-1',
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
        window.localStorage.setItem('mrpilot_token_ai', 'tok-loop-ui');
        window.localStorage.setItem('mrpilot_lang', 'zh');
    });
    await page.goto(`${BASE}/static/dist/ai.html#/steward`);
    // 左窗要有内容得先有一条任务:走产品自己的路(说一句话 → 回包给 task_id → loadTask),
    // 不直接往 S 里塞状态 —— 塞进去验的就不是产品那条路了。
    await page.waitForSelector('#stwInput', { state: 'visible', timeout: 15000 });
    await page.locator('#stwInput').fill('sister 这期报完了没');
    await page.locator('#stwInput').press('Enter');
    await page.waitForSelector('.stw-msg.agent .stw-proc', { state: 'visible', timeout: 15000 });
    // 2026-08-07 拍板:过程条默认恒折叠 —— 本 spec 验的是展开后的内容,先点开。
    await page.locator('.stw-msg.agent .stw-proc .stw-proc-hd').click();
    return { posts };
}

test.describe('大脑循环左窗(本地 stub · 真构建产物)', () => {
    test('步骤按真实条数渲染,失败那步留得住', async ({ page }) => {
        await boot(page);
        const steps = page.locator('.stw-msg.agent .stw-proc .stw-steps .stw-step');
        await expect(steps).toHaveCount(TASK.steps.length); // 不是写死三步
        // 失败的中间步不许被收尾抹掉:会计要看得见它撞了哪堵墙。
        const failed = page.locator('.stw-msg.agent .stw-proc .stw-steps .stw-step', {
            hasText: '查应交税额',
        });
        await expect(failed).toBeVisible();
        await expect(failed.locator('.stw-step-d')).toContainText('指明是哪一家');
        await page.screenshot({ path: path.join(ART, '01-steps-with-failed.png'), fullPage: true });
    });

    test('追问那步把候选画成能点的按钮', async ({ page }) => {
        await boot(page);
        const chips = page.locator('.stw-msg.agent .stw-proc .stw-ask-opts .stw-chip');
        await expect(chips).toHaveCount(2);
        await expect(chips.nth(0)).toHaveText('Sister Makeup');
        await expect(chips.nth(1)).toHaveText('Sister Trading');
        // 真能点:可见 + 未禁用 + 有可点的尺寸(CSS 属性设上了 ≠ 效果生效)。
        await expect(chips.nth(0)).toBeEnabled();
        const box = await chips.nth(0).boundingBox();
        expect(box.width).toBeGreaterThan(40);
        expect(box.height).toBeGreaterThan(16);
        // 候选摆在追问那一行里,不是另起一块飘在下面。
        const inAskStep = await page
            .locator('.stw-msg.agent .stw-proc .stw-steps .stw-step', { hasText: '问你一件事' })
            .locator('.stw-ask-opts')
            .count();
        expect(inAskStep).toBe(1);
        await page.screenshot({ path: path.join(ART, '02-ask-options.png'), fullPage: true });
    });

    test('点候选 = 把这句话当回答送出去', async ({ page }) => {
        const { posts } = await boot(page);
        await page
            .locator('.stw-msg.agent .stw-proc .stw-ask-opts .stw-chip', {
                hasText: 'Sister Trading',
            })
            .click();
        await page.waitForTimeout(400);
        const sent = posts.filter((p) => p.path.endsWith('/messages'));
        expect(sent.length).toBe(2); // 开场那句 + 点候选这一下
        expect(sent[1].body.text).toBe('Sister Trading');
        await page.screenshot({ path: path.join(ART, '03-picked-option.png'), fullPage: true });
    });

    test('任务已终态时候选置灰 —— 不摆点下去必报错的按钮', async ({ page }) => {
        await boot(page, { taskOverride: { status: 'done', cancellable: false } });
        // 终态过程条默认折叠:先展开,候选才看得见(折叠态 = 根本不该见)。
        await page.locator('.stw-msg.agent .stw-proc .stw-proc-hd').first().click();
        const chips = page.locator('.stw-msg.agent .stw-proc .stw-ask-opts .stw-chip');
        await expect(chips).toHaveCount(2);
        await expect(chips.nth(0)).toBeDisabled();
        const opacity = await chips
            .nth(0)
            .evaluate((el) => parseFloat(getComputedStyle(el).opacity));
        expect(opacity).toBeLessThan(1); // 置灰是真画出来了,不只是 disabled 属性
        await page.screenshot({ path: path.join(ART, '04-options-dead.png'), fullPage: true });
    });

    test('左窗那个数说的是查询次数,不是 Agent', async ({ page }) => {
        await boot(page);
        const meta = await page.locator('.stw-msg.agent .stw-proc .stw-meta').innerText();
        expect(meta).toContain('查询 2 次'); // agent_count = kind=tool 的行数,追问不算
        expect(meta).not.toContain('Agent');
    });
});
