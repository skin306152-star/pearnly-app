// B3 收官 · 真浏览器视觉验收(Zihao 闭环判据:真浏览器跑通 + 截图为证 + 视觉合格)
// 被验:① running 真实推进 ② 授权卡 ③ 主动汇报 ④ 成本超限 ⑤ 四态 ⑥ 四语 ⑦ 移动端 ⑧ 文案与能力一致
// 跑法:PEARNLY_E2E_BASE_URL=http://127.0.0.1:7860 npx playwright test tests/e2e/_b3_closeout_verify.spec.js
//
// 真栈为主(登录/会话/消息/任务/工人/大脑全真)。仅两类场景真栈物理造不出,走网络层
// 注入 + 真 dist 产品代码:授权卡(注册表六工具全 readonly,大脑铸不出写卡)与成本超限
// (真烧 ฿5 才能触发)。注入形状逐键抄冻结契约(routes/steward_routes.py · B3 第二段),
// 断言的每个选择器/文案都来自真实产物(ai-steward-*.js / ai-i18n-steward.js)。
/* global window, document */

const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const BASE = process.env.PEARNLY_E2E_BASE_URL || 'http://127.0.0.1:7860';
const USER = 'stw_e2e';
const PASS = 'StwVerify#2026';
// 货币前缀借真源:฿ 与数字之间垫不垫窄空格由 ai-format.js 单点声明(排版口径),
// 断言只管数字对不对。
const { BAHT } = require('../../static/ai/ai-format.js');

const ART = path.join(__dirname, '_artifacts', 'b3_closeout');
const EVID = path.join(ART, 'evidence.json');

// 本机真栈专用:登录/会话/消息/任务/工人/大脑全走真后端,登录号 stw_e2e 只存在于本地
// docker 库 —— CI 打 pearnly.com 那边不认这个号,beforeAll 必红在 401。
// 本机跑法:PEARNLY_E2E_LOCAL=1 PEARNLY_E2E_BASE_URL=http://127.0.0.1:7860 npx playwright test tests/e2e/_b3_closeout_verify.spec.js
test.skip(process.env.PEARNLY_E2E_LOCAL !== '1', '需本机真栈(PEARNLY_E2E_LOCAL=1)');

fs.mkdirSync(ART, { recursive: true });
let evidence = {};
try {
    evidence = JSON.parse(fs.readFileSync(EVID, 'utf8'));
} catch (e) {
    evidence = {};
}
function record(k, v) {
    evidence[k] = v;
    fs.writeFileSync(EVID, JSON.stringify(evidence, null, 2), 'utf8');
}

let TOKEN = '';

test.beforeAll(async ({ request }) => {
    const r = await request.post(`${BASE}/api/login`, {
        data: { username: USER, password: PASS, entry: 'ai' },
    });
    expect(r.status()).toBe(200);
    TOKEN = (await r.json()).token;
    expect(TOKEN.length).toBeGreaterThan(20);
});

async function open(page, opts) {
    opts = opts || {};
    const errs = [];
    page.on('console', (m) => {
        if (m.type() === 'error') errs.push(m.text());
    });
    page.on('pageerror', (e) => errs.push('pageerror: ' + e.message));
    await page.addInitScript(
        ([t, l]) => {
            window.localStorage.setItem('mrpilot_token_ai', t);
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [TOKEN, opts.lang || 'zh']
    );
    await page.goto(`${BASE}/ai#/steward`, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#v-steward.on', { state: 'visible', timeout: 30000 });
    return { errs };
}

async function typeAndSend(page, text) {
    await page.waitForSelector('#stwInput:not([disabled])', { state: 'visible', timeout: 30000 });
    await page.click('#stwInput');
    await page.keyboard.type(text);
    await page.keyboard.press('Enter');
}

// ---- 契约真形状(逐键抄冻结契约,仅用于真栈造不出的授权/预算两场景) ----

const TID = '9f3e2b10-0000-4000-8000-b3c105e0ca5d';
const AUTHZ_TOKEN = 'tok_b3_closeout_verify_0001';

function iso(offsetMs) {
    return new Date(Date.now() + (offsetMs || 0)).toISOString().replace('Z', '+00:00');
}

function authzCard(lang, over) {
    const zh = { title: '把 SM 2569-06 工单的销项税额改为 ฿12,500 并重新过账' };
    const th = { title: 'แก้ยอดภาษีขายของงาน SM งวด มิ.ย. 69 เป็น ฿12,500 แล้วบันทึกใหม่' };
    return Object.assign(
        {
            token: AUTHZ_TOKEN,
            tool: 'workorder_amount_update',
            title: (lang === 'th' ? th : zh).title,
            risk: 'write',
            args: { client_name: 'SM', period: '2569-06', amount_thb: '12500.00' },
            status: 'pending',
            requested_at: iso(-60000),
            expires_at: iso(4 * 60000),
            decided_by: null,
            decided_at: null,
        },
        over || {}
    );
}

function taskBody(lang, status, over) {
    const L =
        lang === 'th'
            ? {
                  title: 'แก้ยอดภาษีขายแล้วบันทึกใหม่',
                  s1: 'ตีความคำสั่ง',
                  s2: 'ตรวจงานเป้าหมาย',
                  s3: 'ลงมือแก้ข้อมูล',
                  wait: 'รอคุณอนุมัติก่อนถึงจะทำ',
              }
            : {
                  title: '改销项税额并重新过账',
                  s1: '解析指令',
                  s2: '核对目标工单',
                  s3: '执行改数',
                  wait: '等你批准后执行',
              };
    const stepState = { waiting_user: 'waiting_auth', running: 'running', cancelled: 'failed' }[
        status
    ];
    return Object.assign(
        {
            task_id: TID,
            title: L.title,
            status: status,
            started_at: iso(-90000),
            agent_count: 1,
            steps: [
                { id: 's1', label: L.s1, state: 'done', detail: '', links: [] },
                { id: 's2', label: L.s2, state: 'done', detail: 'SM · 2569-06', links: [] },
                { id: 's3', label: L.s3, state: stepState, detail: L.wait, links: [] },
            ],
            artifacts: [],
        },
        over || {}
    );
}

// 拦 messages POST(回带 task_id 的契约形状)+ tasks GET(按 mode.fn() 出当前任务态)。
// 其余端点(login/sessions/status/静态资源)全走真后端 —— 被验的是真 dist 产品代码。
async function injectAuthzRoutes(page, lang, mode) {
    await page.route(`**/api/ai/steward/sessions/*/messages`, (r) => {
        if (r.request().method() !== 'POST') return r.fallback();
        r.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                message_id: 'stub-m1',
                user_message_id: 'stub-u1',
                reply:
                    lang === 'th'
                        ? 'งานนี้จะแก้ข้อมูล ผมออกการ์ดขออนุมัติแล้ว คุณกดอนุมัติก่อนถึงจะทำ'
                        : '这个操作会改数,我先出授权卡,你批准后我才动手。',
                task_id: TID,
            }),
        });
    });
    await page.route(`**/api/ai/steward/tasks/${TID}`, (r) => {
        if (r.request().method() !== 'GET') return r.fallback();
        r.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(mode.fn()),
        });
    });
}

test.describe.serial('B3 收官视觉验收', () => {
    // ① running 真实推进 ③ 主动汇报 ⑤ 空态/成功态 ⑧ 文案与能力一致 —— 全真栈,零注入
    test('T1 · zh 桌面 · 真栈全程:空态 → running 推进 → done → 管家主动汇报 + 文案诚实', async ({
        page,
    }) => {
        test.setTimeout(360000);
        await page.setViewportSize({ width: 1280, height: 900 });
        const taskPolls = [];
        page.on('response', async (res) => {
            if (res.url().indexOf('/api/ai/steward/tasks/') < 0 || res.request().method() !== 'GET')
                return;
            try {
                const b = await res.json();
                taskPolls.push({
                    status: b.status,
                    stepsDone: (b.steps || []).filter((s) => s.state === 'done').length,
                    stepsTotal: (b.steps || []).length,
                });
            } catch (e) {
                /* 非 JSON 不计 */
            }
        });
        const { errs } = await open(page, { lang: 'zh' });

        // ⑧ 文案与能力一致:注册表挂上写工具后,页头自述必须跟着换成「会改数的先批准」,
        // 且全页不许再留只读期的「只查不改数」—— 那句话现在是谎。词典侧由双向闸
        // tests/unit/test_ai_steward_pure.py::CopyMatchesCapabilityTests 管,这里管真渲染上屏那份。
        await page.waitForSelector('#stwInput', { state: 'visible', timeout: 30000 });
        const note = (
            await page.locator('#v-steward .note[data-at="stw_note"]').innerText()
        ).trim();
        const composerNote = (await page.locator('.stw-composer-note').innerText()).trim();
        const bodyText = await page.evaluate(() => document.body.innerText);
        expect(note).toContain('需你先批准');
        expect(bodyText).not.toContain('只查不改数');
        // 同一条规则整页只说一遍(2026-07-27 去重):注脚只补输入框自己说不出的那件事。
        expect(composerNote).toContain('文件可拖入或粘贴');
        expect(composerNote).not.toContain('批准');

        // ⑤ 空态:左窗指路空态 + 右窗空态带 4 个快捷 chips
        await page.waitForSelector('#stwLeft [data-state="empty"]', {
            state: 'visible',
            timeout: 30000,
        });
        await expect(page.locator('.stw-feed-empty .stw-chip')).toHaveCount(4);
        await page.screenshot({
            path: path.join(ART, '01-empty-4state-zh-desktop.png'),
            fullPage: true,
        });

        // 真键盘输入(不 fill)→ 真大脑 → 真任务
        await typeAndSend(page, '本期谁缺料');
        await page.waitForSelector('#stwLeft .stw-task', { state: 'visible', timeout: 120000 });
        await page.screenshot({
            path: path.join(ART, '02-running-zh-desktop.png'),
            fullPage: true,
        });

        // running → done(轮询真推进,以 DOM 徽章文字为准)
        await page.waitForFunction(
            () => {
                const b = document.querySelector('#stwLeft .panel .hd .st-badge');
                return !!b && b.textContent.trim() === '已完成';
            },
            null,
            { timeout: 240000 }
        );

        // ③ 主动汇报:任务收尾后 worker 往会话追写管家消息,前端 syncSession 补回
        await page.waitForFunction(
            () => document.querySelectorAll('.stw-msg.agent .stw-bubble').length >= 2,
            null,
            { timeout: 60000 }
        );
        const agentMsgs = await page.locator('.stw-msg.agent .stw-bubble').allInnerTexts();
        await page.screenshot({
            path: path.join(ART, '03-done-report-zh-desktop.png'),
            fullPage: true,
        });

        const leftText = await page.locator('#stwLeft').innerText();
        expect(leftText).not.toContain('[object Object]');
        expect(leftText).not.toContain('undefined');
        expect(bodyText).not.toMatch(/\bstw_[a-z_]+\b/);

        // ① running 真实推进:轮询流水里见过非终态,最后一拍是 done
        const statuses = taskPolls.map((p) => p.status);
        record('t1', { note, composerNote, taskPolls, agentMsgs, consoleErrors: errs });
        expect(statuses).toContain('running');
        expect(statuses[statuses.length - 1]).toBe('done');
    });

    // ⑤ 错误态 + 重试恢复(网络层故障注入 · 被验的是真 dist 四态代码)
    test('T2 · zh 桌面 · 四态:会话错误态 / 任务加载态 / 任务错误态 → 重试恢复', async ({
        page,
    }) => {
        test.setTimeout(120000);
        await page.setViewportSize({ width: 1280, height: 900 });

        // 右窗错误态:建会话 500 → stw_session_err + 重试
        let failSession = true;
        await page.route('**/api/ai/steward/sessions', (r) => {
            if (r.request().method() === 'POST' && failSession) {
                return r.fulfill({
                    status: 500,
                    contentType: 'application/json',
                    body: '{"detail":"boom"}',
                });
            }
            return r.fallback();
        });
        const { errs } = await open(page, { lang: 'zh' });
        await page.waitForSelector('#stwRight [data-state="error"]', {
            state: 'visible',
            timeout: 30000,
        });
        const sessionErrText = (await page.locator('#stwRight').innerText()).trim();
        await page.screenshot({
            path: path.join(ART, '04-session-error-retry-zh-desktop.png'),
            fullPage: true,
        });
        expect(sessionErrText).toContain('会话建不起来');

        // 点重试 → 真后端恢复
        failSession = false;
        await page.click('#stwRight [data-action="retry"]');
        await page.waitForSelector('#stwInput', { state: 'visible', timeout: 30000 });

        // 左窗加载态(骨架):tasks GET 延迟 1.5s,窗口期截骨架
        let taskMode = 'slow-ok';
        await page.route(`**/api/ai/steward/tasks/${TID}`, async (r) => {
            if (r.request().method() !== 'GET') return r.fallback();
            if (taskMode === 'slow-ok') {
                await new Promise((res) => setTimeout(res, 1500));
                return r.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(
                        taskBody('zh', 'waiting_user', { authorization: authzCard('zh') })
                    ),
                });
            }
            return r.fulfill({
                status: 500,
                contentType: 'application/json',
                body: '{"detail":"boom"}',
            });
        });
        const stubAsk = '把 SM 六月销项税改成 12500 重新过账';
        const stubReply = '这个操作会改数,我先出授权卡,你批准后我才动手。';
        await page.route('**/api/ai/steward/sessions/*/messages', (r) => {
            if (r.request().method() !== 'POST') return r.fallback();
            r.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    message_id: 'stub-m1',
                    user_message_id: 'stub-u1',
                    reply: stubReply,
                    task_id: TID,
                }),
            });
        });
        // 服务端消息流是权威的:任务一落 waiting_user(终态之一)产品就用 syncSession 整份
        // 重建右窗(ai-steward.js)。送出走的是桩,真库那条会话一条消息都没有 —— 不把
        // GET /sessions/{id} 一起桩上,重建当场把刚上屏的两条抹掉,气泡下「回到那条任务」
        // 的入口跟着消失。T1 长期红,T2-T9 从没跑到,这条一直没人撞见。
        await page.route('**/api/ai/steward/sessions/*', (r) => {
            if (r.request().method() !== 'GET') return r.fallback();
            const sid = r.request().url().split('?')[0].split('/').pop();
            r.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    session_id: sid,
                    current_task_id: TID,
                    messages: [
                        { id: 'stub-u1', role: 'user', text: stubAsk },
                        { id: 'stub-m1', role: 'steward', text: stubReply, task_id: TID },
                    ],
                }),
            });
        });
        await typeAndSend(page, stubAsk);
        await page.waitForSelector('#stwLeft [data-state="loading"]', {
            state: 'visible',
            timeout: 10000,
        });
        await page.screenshot({
            path: path.join(ART, '05-task-loading-zh-desktop.png'),
            fullPage: true,
        });
        await page.waitForSelector('#stwLeft .stw-task', { state: 'visible', timeout: 15000 });

        // 左窗错误态:轻刷改 500 → 手动触发重载 → 错误态 + 重试;重试恢复
        taskMode = 'fail';
        await page.click('.stw-msg.agent [data-action="stw-open-task"]');
        await page.waitForSelector('#stwLeft [data-state="error"]', {
            state: 'visible',
            timeout: 15000,
        });
        const taskErrText = (await page.locator('#stwLeft').innerText()).trim();
        await page.screenshot({
            path: path.join(ART, '06-task-error-retry-zh-desktop.png'),
            fullPage: true,
        });
        expect(taskErrText).toContain('任务状态拉不到');
        taskMode = 'slow-ok';
        await page.click('#stwLeft [data-action="retry"]');
        await page.waitForSelector('#stwLeft .stw-task', { state: 'visible', timeout: 15000 });
        record('t2', { sessionErrText, taskErrText, consoleErrors: errs });
    });

    // ② 授权卡:pending 视觉 + 倒计时真走 + 决断错误码人话 + 拒绝落 cancelled
    test('T3 · zh 桌面 · 授权卡 pending → 409 used 人话 → 拒绝 → cancelled', async ({ page }) => {
        test.setTimeout(180000);
        await page.setViewportSize({ width: 1280, height: 900 });
        const mode = {
            fn: () => taskBody('zh', 'waiting_user', { authorization: authzCard('zh') }),
        };
        await injectAuthzRoutes(page, 'zh', mode);

        let decideMode = 'used-409';
        await page.route('**/api/ai/steward/authorizations/reject', (r) => {
            if (decideMode === 'used-409') {
                return r.fulfill({
                    status: 409,
                    contentType: 'application/json',
                    body: '{"detail":"steward.authz_used"}',
                });
            }
            return r.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    task_id: TID,
                    authorization: authzCard('zh', {
                        status: 'rejected',
                        decided_by: 'stw_e2e',
                        decided_at: iso(0),
                    }),
                }),
            });
        });

        const { errs } = await open(page, { lang: 'zh' });
        await typeAndSend(page, '把 SM 六月销项税改成 12500 重新过账');
        await page.waitForSelector('#stwLeft .stw-authz', { state: 'visible', timeout: 30000 });

        // 卡面:头部/状态章/风险章/参数行/双按钮/倒计时,waiting_user 任务章 + waiting_auth 步骤章
        const card = page.locator('#stwLeft .stw-authz');
        await expect(card.locator('.stw-authz-hd')).toContainText('写操作授权');
        await expect(card.locator('.st-badge').first()).toContainText('待批准');
        await expect(card.locator('.st-badge').nth(1)).toContainText('会改数据');
        await expect(card.locator('.stw-authz-args dt')).toHaveCount(3);
        await expect(card.locator('.stw-authz-args')).toContainText('12500.00');
        await expect(card.locator('[data-action="stw-authz-approve"]')).toContainText('批准执行');
        await expect(card.locator('[data-action="stw-authz-reject"]')).toContainText('拒绝');
        await expect(page.locator('#stwLeft .panel .hd .st-badge')).toContainText('等你确认');
        await expect(page.locator('#stwLeft .stw-steps')).toContainText('待授权');

        // 倒计时真走(1s tick 只改文字)
        const cd1 = (await page.locator('#stwAuthzCd').innerText()).trim();
        await page.waitForFunction(
            (prev) => {
                const el = document.getElementById('stwAuthzCd');
                return !!el && el.textContent.trim() !== prev;
            },
            cd1,
            { timeout: 5000 }
        );
        const cd2 = (await page.locator('#stwAuthzCd').innerText()).trim();
        expect(cd1).toMatch(/[0-4]:\d\d/);
        await page.screenshot({
            path: path.join(ART, '07-authz-pending-zh-desktop.png'),
            fullPage: true,
        });

        // 409 authz_used → 面板层人话错误行(不糊一句失败)
        await page.click('[data-action="stw-authz-reject"]');
        await page.waitForSelector('#stwLeft .stw-err', { state: 'visible', timeout: 15000 });
        const errLine = (await page.locator('#stwLeft .stw-err').innerText()).trim();
        expect(errLine).toContain('这张卡已被处理过');
        await page.screenshot({
            path: path.join(ART, '08-authz-err-used-zh-desktop.png'),
            fullPage: true,
        });

        // 换成功路:拒绝 → 任务 cancelled + error_code steward.authz_rejected + 卡盖「已拒绝」章
        decideMode = 'ok';
        mode.fn = () =>
            taskBody('zh', 'cancelled', {
                error_code: 'steward.authz_rejected',
                error_reason: '这个操作被拒绝,未执行任何步骤。',
                authorization: authzCard('zh', {
                    status: 'rejected',
                    decided_by: 'stw_e2e',
                    decided_at: iso(0),
                }),
            });
        await page.click('[data-action="stw-authz-reject"]');
        await page.waitForFunction(
            () => {
                const b = document.querySelector('#stwLeft .panel .hd .st-badge');
                return !!b && b.textContent.trim() === '已取消';
            },
            null,
            { timeout: 15000 }
        );
        await expect(page.locator('#stwLeft .stw-authz .st-badge').first()).toContainText('已拒绝');
        await expect(page.locator('#stwLeft .stw-reason')).toContainText('steward.authz_rejected');
        // 已决断卡不再摆动作按钮
        await expect(page.locator('[data-action="stw-authz-approve"]')).toHaveCount(0);
        await page.screenshot({
            path: path.join(ART, '09-authz-rejected-cancelled-zh-desktop.png'),
            fullPage: true,
        });
        record('t3', { cd1, cd2, errLine, consoleErrors: errs });
    });

    // ② 批准 → 任务回 running(重启轮询 · 取消按钮回位)
    test('T4 · zh 桌面 · 授权卡批准 → running 恢复', async ({ page }) => {
        test.setTimeout(120000);
        await page.setViewportSize({ width: 1280, height: 900 });
        const mode = {
            fn: () => taskBody('zh', 'waiting_user', { authorization: authzCard('zh') }),
        };
        await injectAuthzRoutes(page, 'zh', mode);
        await page.route('**/api/ai/steward/authorizations/approve', (r) =>
            r.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    task_id: TID,
                    authorization: authzCard('zh', {
                        status: 'approved',
                        decided_by: 'stw_e2e',
                        decided_at: iso(0),
                    }),
                }),
            })
        );
        const { errs } = await open(page, { lang: 'zh' });
        await typeAndSend(page, '把 SM 六月销项税改成 12500 重新过账');
        await page.waitForSelector('[data-action="stw-authz-approve"]', {
            state: 'visible',
            timeout: 30000,
        });
        mode.fn = () =>
            taskBody('zh', 'running', {
                authorization: authzCard('zh', {
                    status: 'approved',
                    decided_by: 'stw_e2e',
                    decided_at: iso(0),
                }),
            });
        await page.click('[data-action="stw-authz-approve"]');
        await page.waitForFunction(
            () => {
                const b = document.querySelector('#stwLeft .panel .hd .st-badge');
                return !!b && b.textContent.trim() === '执行中';
            },
            null,
            { timeout: 15000 }
        );
        await expect(page.locator('#stwLeft .stw-authz .st-badge').first()).toContainText('已批准');
        await expect(page.locator('[data-action="stw-cancel"]')).toBeVisible();
        await page.screenshot({
            path: path.join(ART, '10-authz-approved-running-zh-desktop.png'),
            fullPage: true,
        });
        record('t4', { consoleErrors: errs });
    });

    // ④ 成本封顶:超限轮 reply + budget 数字块 + 「开新会话」出口真开新会话
    test('T5 · zh 桌面 · 会话级成本超限 → 数字块 + 开新会话恢复', async ({ page }) => {
        test.setTimeout(120000);
        await page.setViewportSize({ width: 1280, height: 900 });
        const sessionIds = [];
        page.on('response', async (res) => {
            if (
                res.url().indexOf('/api/ai/steward/sessions') < 0 ||
                res.request().method() !== 'POST' ||
                res.url().indexOf('/messages') >= 0
            )
                return;
            try {
                sessionIds.push((await res.json()).session_id);
            } catch (e) {
                /* ignore */
            }
        });
        await page.route('**/api/ai/steward/sessions/*/messages', (r) => {
            if (r.request().method() !== 'POST') return r.fallback();
            r.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    message_id: 'stub-m2',
                    user_message_id: 'stub-u2',
                    reply: '这个会话的模型开销已经到上限 ฿5.00,先开个新会话再继续。',
                    budget: {
                        code: 'steward.budget_session_exceeded',
                        cap_thb: '5.00',
                        spent_thb: '5.02',
                    },
                }),
            });
        });
        const { errs } = await open(page, { lang: 'zh' });
        await typeAndSend(page, '本期谁缺料');
        await page.waitForSelector('.stw-budget', { state: 'visible', timeout: 30000 });
        const budgetText = (await page.locator('.stw-budget').innerText()).trim();
        expect(budgetText).toContain(`已用 ${BAHT}5.02 / 上限 ${BAHT}5.00`);
        await expect(page.locator('[data-action="stw-new-session"]')).toContainText(
            '开个新会话继续'
        );
        // 超限轮无 task_id:左窗仍是空态,不臆造任务
        await expect(page.locator('#stwLeft [data-state="empty"]')).toBeVisible();
        await page.screenshot({
            path: path.join(ART, '11-budget-cap-zh-desktop.png'),
            fullPage: true,
        });

        // 出口:开新会话 → 真 POST /sessions → 消息流清零回空态
        await page.click('[data-action="stw-new-session"]');
        await page.waitForSelector('.stw-feed-empty', { state: 'visible', timeout: 30000 });
        await page.screenshot({
            path: path.join(ART, '12-budget-new-session-zh-desktop.png'),
            fullPage: true,
        });
        expect(sessionIds.length).toBeGreaterThanOrEqual(2);
        expect(sessionIds[sessionIds.length - 1]).not.toBe(sessionIds[0]);
        record('t5', { budgetText, sessionIds, consoleErrors: errs });
    });

    // ⑥ 泰语:页文案 + 授权卡整卡泰语 + 页面自述与能力一致
    test('T6 · th 桌面 · 泰语授权卡 + 文案诚实', async ({ page }) => {
        test.setTimeout(120000);
        await page.setViewportSize({ width: 1280, height: 900 });
        const mode = {
            fn: () => taskBody('th', 'waiting_user', { authorization: authzCard('th') }),
        };
        await injectAuthzRoutes(page, 'th', mode);
        const { errs } = await open(page, { lang: 'th' });
        await page.waitForSelector('#stwInput', { state: 'visible', timeout: 30000 });
        const note = (
            await page.locator('#v-steward .note[data-at="stw_note"]').innerText()
        ).trim();
        // 与 T1 同一条口径的泰语面:有写工具了,页头自述必须是「改数要先批准」,
        // 不许还留着只读期的 อ่านอย่างเดียว ไม่แก้ตัวเลข。
        expect(note).toContain('ต้องให้คุณอนุมัติก่อน');
        expect(note).not.toContain('อ่านอย่างเดียว');
        await typeAndSend(page, 'แก้ยอดภาษีขายของ SM งวด มิ.ย. เป็น 12500');
        await page.waitForSelector('#stwLeft .stw-authz', { state: 'visible', timeout: 30000 });
        const card = page.locator('#stwLeft .stw-authz');
        await expect(card.locator('.stw-authz-hd')).toContainText('ขออนุมัติแก้ข้อมูล');
        await expect(card.locator('.st-badge').first()).toContainText('รออนุมัติ');
        await expect(card.locator('.st-badge').nth(1)).toContainText('จะแก้ข้อมูล');
        await expect(card.locator('[data-action="stw-authz-approve"]')).toContainText(
            'อนุมัติให้ทำ'
        );
        await expect(page.locator('#stwLeft .panel .hd .st-badge')).toContainText('รอคุณยืนยัน');
        await page.screenshot({
            path: path.join(ART, '13-authz-pending-th-desktop.png'),
            fullPage: true,
        });
        record('t6', { note, consoleErrors: errs });
    });

    // ⑥ en/ja:管家词条按 adm-* 先例只写 zh+th,en/ja 由 at() 回落 zh —— 断没有裸 key
    test('T7 · en+ja 桌面 · 词条回落 zh 且零裸 key', async ({ page }) => {
        test.setTimeout(120000);
        await page.setViewportSize({ width: 1280, height: 900 });
        const out = {};
        await page.addInitScript((t) => {
            window.localStorage.setItem('mrpilot_token_ai', t);
        }, TOKEN);
        for (const lang of ['en', 'ja']) {
            // 同 URL 只换 hash 不触发重载:先落语言再整页 reload,才是该语言的真渲染
            await page.goto(`${BASE}/ai#/steward`, { waitUntil: 'domcontentloaded' });
            await page.evaluate((l) => window.localStorage.setItem('mrpilot_lang', l), lang);
            await page.reload({ waitUntil: 'domcontentloaded' });
            await page.waitForSelector('#stwInput', { state: 'visible', timeout: 30000 });
            const navLang = (await page.locator('#navClients').innerText()).trim();
            expect(navLang).toBe(lang === 'en' ? 'Clients' : '顧客');
            const note = (
                await page.locator('#v-steward .note[data-at="stw_note"]').innerText()
            ).trim();
            const stwText = await page.evaluate(
                () => document.getElementById('v-steward').innerText
            );
            expect(note).toContain('需你先批准'); // 回落 zh 的诚实文案
            expect(stwText).not.toMatch(/\bstw_[a-z_]+\b/);
            expect(stwText).not.toContain('只查不改数');
            const shot = lang === 'en' ? '14-steward-en-desktop.png' : '15-steward-ja-desktop.png';
            await page.screenshot({ path: path.join(ART, shot), fullPage: true });
            out[lang] = { note };
        }
        record('t7', out);
    });

    // ⑦ 移动端:真栈全程(键盘真输入)+ 单栏不横滚;授权卡在 390 宽下按钮可点不溢出
    test('T8 · zh 移动 390×844 · 真栈任务 + 授权卡布局', async ({ page }) => {
        test.setTimeout(360000);
        await page.setViewportSize({ width: 390, height: 844 });
        const { errs } = await open(page, { lang: 'zh' });
        await typeAndSend(page, '本期谁缺料');
        await page.waitForSelector('#stwLeft .stw-task', { state: 'visible', timeout: 120000 });
        await page.waitForFunction(
            () => {
                const b = document.querySelector('#stwLeft .panel .hd .st-badge');
                return !!b && b.textContent.trim() === '已完成';
            },
            null,
            { timeout: 240000 }
        );
        const geo = await page.evaluate(() => {
            const l = document.querySelector('.stw-left').getBoundingClientRect();
            const r = document.querySelector('.stw-right').getBoundingClientRect();
            return {
                overflow: document.documentElement.scrollWidth - window.innerWidth,
                sameColumn: Math.abs(l.x - r.x) < 2,
                leftAboveRight: l.y + l.height <= r.y + 2,
                leftWidth: l.width,
            };
        });
        expect(geo.overflow).toBeLessThanOrEqual(0);
        expect(geo.sameColumn).toBe(true);
        await page.screenshot({
            path: path.join(ART, '16-mobile-task-zh-390.png'),
            fullPage: true,
        });
        record('t8_real', { geo, consoleErrors: errs });
    });

    test('T9 · zh 移动 390×844 · 授权卡布局(按钮真在视口内可点)', async ({ page }) => {
        test.setTimeout(120000);
        await page.setViewportSize({ width: 390, height: 844 });
        const mode = {
            fn: () => taskBody('zh', 'waiting_user', { authorization: authzCard('zh') }),
        };
        await injectAuthzRoutes(page, 'zh', mode);
        const { errs } = await open(page, { lang: 'zh' });
        await typeAndSend(page, '把 SM 六月销项税改成 12500 重新过账');
        await page.waitForSelector('#stwLeft .stw-authz', { state: 'visible', timeout: 30000 });
        const geo = await page.evaluate(() => {
            const card = document.querySelector('#stwLeft .stw-authz').getBoundingClientRect();
            const ok = document
                .querySelector('[data-action="stw-authz-approve"]')
                .getBoundingClientRect();
            return {
                overflow: document.documentElement.scrollWidth - window.innerWidth,
                cardRight: card.right,
                vw: window.innerWidth,
                approveW: ok.width,
                approveH: ok.height,
            };
        });
        expect(geo.overflow).toBeLessThanOrEqual(0);
        expect(geo.cardRight).toBeLessThanOrEqual(geo.vw + 1);
        expect(geo.approveH).toBeGreaterThanOrEqual(24); // 可点面积不塌
        await page
            .locator('#stwLeft .stw-authz')
            .screenshot({ path: path.join(ART, '17-authz-pending-zh-390.png') });
        await page.screenshot({
            path: path.join(ART, '17b-authz-page-zh-390.png'),
            fullPage: true,
        });
        record('t9', { geo, consoleErrors: errs });
    });
});
