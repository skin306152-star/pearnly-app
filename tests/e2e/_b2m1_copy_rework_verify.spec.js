// 文案返工复验 · 真浏览器(Chromium)+ 真登录 + 真打包产物(static/dist/ai.js?v=108)
//
// 六条硬伤里 2/3/4/6 是渲染结构问题,只有把真页面画出来量像素才算验过(断言类名 / 看代码
// 「应该对了」不算)。管家的状态机需要真大脑 + 真桥才能自然走到「失败 / 追问 / 待授权」,
// 一轮几分钟且要烧钱,所以这里把 /api/ai/steward 的四个读端点换成定值 —— 但填进去的每一句
// 话都由 scripts/_steward_copy_fixtures.py 从真 copy 层现取(tests/e2e/_fixtures_steward_copy.json),
// 不在这里手写一份文案,否则验的是我自己编的字。
//
// 起法:PEARNLY_E2E_BASE_URL=http://127.0.0.1:7860 npx playwright test tests/e2e/_b2m1_copy_rework_verify.spec.js
/* global window, document, getComputedStyle */

const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const BASE = process.env.PEARNLY_E2E_BASE_URL || 'http://127.0.0.1:7860';
const USER = 'stw_e2e';
const PASS = 'StwVerify#2026';
const ART = path.join(__dirname, '_artifacts', 'steward_copy_rework');
const FIX = JSON.parse(
    fs.readFileSync(path.join(__dirname, '_fixtures_steward_copy.json'), 'utf8')
);

fs.mkdirSync(ART, { recursive: true });

let TOKEN = '';

test.beforeAll(async ({ request }) => {
    const r = await request.post(`${BASE}/api/login`, {
        data: { username: USER, password: PASS, entry: 'ai' },
    });
    expect(r.status()).toBe(200);
    TOKEN = (await r.json()).token;
});

function taskFailed(lang) {
    const reason = FIX[lang].bridge_offline;
    return {
        task_id: 't-1',
        title: FIX[lang].card_title,
        status: 'failed',
        started_at: new Date().toISOString(),
        agent_count: 1,
        error_code: 'steward.bridge_offline',
        error_reason: reason,
        cancellable: false,
        // 后端把同一句话复制进失败步的 detail(store.fail_steps)—— 三处同句的第三处。
        steps: [{ id: 's1', kind: 'tool', label: '推进 Express', state: 'failed', detail: reason }],
        artifacts: [],
    };
}

function taskAsking(lang) {
    const question =
        lang === 'zh'
            ? '是 Sister Makeup 还是 Sister Trading?'
            : 'Sister Makeup หรือ Sister Trading?';
    return {
        task_id: 't-2',
        title: FIX[lang].card_title,
        status: 'waiting_user',
        started_at: new Date().toISOString(),
        agent_count: 2,
        cancellable: false,
        steps: [
            { id: 's1', kind: 'ask', label: '待你回答', state: 'waiting_auth', detail: question },
        ],
        loop: {
            calls: 2,
            asked: 1,
            question: {
                field: 'client_name',
                text: question,
                options: ['Sister Makeup', 'Sister Trading'],
            },
        },
        artifacts: [],
        _question: question,
    };
}

function taskPendingAuthz(lang) {
    return {
        task_id: 't-3',
        title: FIX[lang].card_title,
        status: 'waiting_user',
        started_at: new Date().toISOString(),
        agent_count: 1,
        cancellable: false,
        steps: [{ id: 's1', kind: 'tool', label: '等你批准', state: 'waiting_auth' }],
        artifacts: [],
        authorization: {
            token: 'tok-1',
            tool: 'erp_push',
            title: FIX[lang].card_title,
            risk: 'write',
            status: 'pending',
            args: {
                invoice_no: 'INV-2569-0042',
                seller_name: 'Sister Trading',
                direction: 'sales',
                posting_kind: 'stock',
                total_amount: '128400.00',
                history_id: '6f1c-uuid',
            },
            args_display: FIX[lang].arg_rows,
            requested_at: new Date().toISOString(),
            expires_at: new Date(Date.now() + 240000).toISOString(),
        },
    };
}

// 会话流:失败/追问那一句同时也回到对话里(真后端就是这么写的 —— worker._finalize 把
// reply 与 error_message 填成同一个串)。
// 正题之前先真送几轮:390px 下一屏装不下才谈得上「谁在上谁在下」—— 内容短到不用滚,
// sticky 与 static 长得一模一样,量出来的数字对两种写法都成立(假绿)。
const FILLER_TURNS = 6;
const FILLER_REPLY = '这期 Sister Trading 有 12 张进项票,已推 9 张,剩下 3 张缺过账去向。';

function session(task, replyText) {
    return {
        session_id: 's-1',
        current_task_id: task.task_id,
        messages: [
            { id: 'm1', role: 'user', text: '把这张票推进 69EXP' },
            { id: 'm2', role: 'steward', text: replyText, task_id: task.task_id },
        ],
    };
}

// 真交互驱动:打开管家页 → 在真输入框里打字 → 点真「送出」。送出的回包与随后的任务查询
// 换成定值,别的都是产品自己的路(建会话、上屏、拉任务、轮询)。
async function open(page, { lang, task, reply, width, height }) {
    await page.setViewportSize({ width: width || 1280, height: height || 900 });
    await page.route('**/api/ai/steward/status', (r) =>
        r.fulfill({ json: { enabled: true, attachments: null } })
    );
    await page.route('**/api/ai/steward/sessions', (r) =>
        r.fulfill({ json: { session_id: 's-1' } })
    );
    await page.route('**/api/ai/steward/sessions/s-1', (r) =>
        r.fulfill({ json: session(task, reply) })
    );
    let sent = 0;
    await page.route('**/api/ai/steward/sessions/s-1/messages', (r) => {
        sent += 1;
        const last = sent > FILLER_TURNS;
        r.fulfill({
            json: {
                user_message_id: 'm' + sent,
                reply: last ? reply : FILLER_REPLY,
                task_id: last ? task.task_id : null,
            },
        });
    });
    await page.route(`**/api/ai/steward/tasks/${task.task_id}*`, (r) => r.fulfill({ json: task }));
    await page.addInitScript(
        ([t, l]) => {
            window.localStorage.setItem('mrpilot_token_ai', t);
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [TOKEN, lang]
    );
    await page.goto(`${BASE}/ai#/steward`, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#stwInput', { timeout: 20000 });
    for (let i = 0; i <= FILLER_TURNS; i++) {
        await page.click('#stwInput');
        await page.keyboard.type(i < FILLER_TURNS ? '这期 Sister 推完了吗' : '把这张票推进 69EXP');
        await page.click('[data-action="stw-send"]');
        await page.waitForFunction(
            (n) => document.querySelectorAll('.stw-feed .stw-msg').length >= n,
            (i + 1) * 2,
            { timeout: 20000 }
        );
    }
    await page.waitForSelector('#stwLeft .stw-task', { timeout: 20000 });
}

async function shot(page, name) {
    const p = path.join(ART, name);
    await page.screenshot({ path: p, fullPage: true });
    return p;
}

test.describe('硬伤 2 · 同一句错误一屏只印一次', () => {
    for (const lang of ['zh', 'th']) {
        test(`${lang} · 红条让位给气泡,失败步 detail 不复述`, async ({ page }) => {
            const task = taskFailed(lang);
            await open(page, { lang, task, reply: task.error_reason });
            const reason = task.error_reason;
            const count = await page.evaluate((r) => {
                const hit = (sel) =>
                    Array.from(document.querySelectorAll(sel)).filter(
                        (n) => n.innerText.trim().indexOf(r) >= 0
                    ).length;
                return {
                    bubble: hit('.stw-bubble'),
                    red: hit('.stw-reason'),
                    stepDetail: hit('.stw-step-d'),
                    badge: document.querySelector('#stwLeft .badge, #stwLeft [class*="badge"]')
                        ? 1
                        : 0,
                };
            }, reason);
            expect(count.bubble).toBe(1); // 那句话的家
            expect(count.red).toBe(0); // 红条让位
            expect(count.stepDetail).toBe(0); // 步骤不复述
            expect(count.badge).toBe(1); // 「失败」徽章还在,状态不靠那句话撑
            await shot(page, `01-failed-${lang}-1280.png`);
        });
    }

    test('气泡里没有那句话时红条照印(深链只开左窗)', async ({ page }) => {
        const task = taskFailed('zh');
        await open(page, { lang: 'zh', task, reply: '别的话' });
        const red = await page.locator('.stw-reason').first();
        expect(await red.isVisible()).toBe(true);
        expect((await red.innerText()).indexOf(task.error_reason)).toBeGreaterThanOrEqual(0);
        await shot(page, '02-failed-not-echoed-zh.png');
    });
});

test.describe('硬伤 4 · 追问态一份候选', () => {
    test('候选只在能点的 chips 上,气泡里不再列一遍', async ({ page }) => {
        const task = taskAsking('zh');
        await open(page, { lang: 'zh', task, reply: task._question });
        const chips = page.locator('.stw-ask-opts .stw-chip');
        expect(await chips.count()).toBe(2);
        expect(await chips.first().isVisible()).toBe(true);
        expect(await chips.first().isEnabled()).toBe(true);
        const bubbles = (await page.locator('.stw-bubble').allInnerTexts()).join('\n');
        expect(bubbles).toContain(task._question);
        expect(bubbles).not.toContain('候选');
        expect(bubbles).not.toContain('Sister Makeup / Sister Trading');
        await shot(page, '03-asking-zh-1280.png');
    });
});

test.describe('硬伤 3 · 授权卡摆的是会计的说法', () => {
    for (const lang of ['zh', 'th']) {
        test(`${lang} · 参数行是人话标签,机器槽名与 uuid 不上卡`, async ({ page }) => {
            const task = taskPendingAuthz(lang);
            await open(page, { lang, task, reply: FIX[lang].card_title });
            const dl = page.locator('.stw-authz-args');
            expect(await dl.isVisible()).toBe(true);
            const text = await dl.innerText();
            for (const row of FIX[lang].arg_rows) {
                expect(text).toContain(row.label);
                expect(text).toContain(row.value);
            }
            for (const raw of ['invoice_no', 'posting_kind', 'history_id', '6f1c-uuid', 'sales']) {
                expect(text).not.toContain(raw);
            }
            await shot(page, `04-authz-${lang}-1280.png`);
        });
    }
});

test.describe('硬伤 6 · 手机端消息在上、输入在下', () => {
    for (const lang of ['zh', 'th']) {
        test(`${lang} · 390px 下最后一条气泡在输入框上方`, async ({ page }) => {
            const task = taskFailed(lang);
            await open(page, { lang, task, reply: task.error_reason, width: 390, height: 700 });
            // 回到首屏再量:sticky 的病灶就在「页面还没往下滚时输入框被拽到眼前」,
            // 停在页尾量,两种写法量出来一模一样。
            const geom = await page.evaluate(() => {
                window.scrollTo(0, 0);
                const msgs = document.querySelectorAll('.stw-feed .stw-msg');
                const last = msgs[msgs.length - 1].getBoundingClientRect();
                const composer = document.querySelector('.stw-composer');
                const box = composer.getBoundingClientRect();
                return {
                    lastMsgBottom: last.bottom + window.scrollY,
                    composerTop: box.top + window.scrollY,
                    position: getComputedStyle(composer).position,
                    scrollable: document.documentElement.scrollHeight > window.innerHeight,
                    inputBelow:
                        document.querySelector('#stwInput').getBoundingClientRect().top +
                        window.scrollY,
                };
            });
            // 一屏就装下的对话对这条断言永远成立 —— 先证明这一屏真的滚得动。
            expect(geom.scrollable).toBe(true);
            // 输入框整块在消息流之后(sticky 会把它拽到首屏底部,消息还在下面没露头)。
            expect(geom.position).toBe('static');
            expect(geom.composerTop).toBeGreaterThan(geom.lastMsgBottom);
            expect(geom.inputBelow).toBeGreaterThan(geom.lastMsgBottom);
            await shot(page, `05-mobile-390-${lang}.png`);
        });
    }

    // 反证:把 sticky 塞回去,上面那把尺子必须当场量出「输入框跑到消息上面」——
    // 量不出来说明这条断言在任何写法下都会绿(CSS 属性设了 ≠ 效果成立的老坑)。
    test('尺子有牙:sticky 一回来就量得出输入框跑到了消息上面', async ({ page }) => {
        const task = taskFailed('zh');
        await open(page, { lang: 'zh', task, reply: task.error_reason, width: 390, height: 700 });
        await page.addStyleTag({
            content: '@media (max-width: 900px){ .stw-composer{ position: sticky !important; } }',
        });
        const geom = await page.evaluate(() => {
            window.scrollTo(0, 0);
            const msgs = document.querySelectorAll('.stw-feed .stw-msg');
            const last = msgs[msgs.length - 1].getBoundingClientRect();
            const box = document.querySelector('.stw-composer').getBoundingClientRect();
            return {
                lastMsgBottom: last.bottom + window.scrollY,
                composerTop: box.top + window.scrollY,
            };
        });
        expect(geom.composerTop).toBeLessThan(geom.lastMsgBottom);
        await shot(page, '05b-mobile-390-sticky-counterexample.png');
    });
});

test.describe('硬伤 1 / 5 · 指路真实 · 空态不提方位', () => {
    test('推送日志是真菜单名 · 空态不说「右侧」', async ({ page }) => {
        const task = taskFailed('zh');
        await open(page, { lang: 'zh', task, reply: FIX.zh.already_pushed });
        const bubble = (await page.locator('.stw-bubble').allInnerTexts()).join('\n');
        expect(bubble).toContain('「推送日志」');
        expect(bubble).not.toContain('ERP 桥');
        // 空态那一句在词典里,页面上要等没有任务才出现 —— 直接读渲染层用的那条词条。
        const empty = await page.evaluate(() => window.at('stw_no_task_s'));
        expect(empty).not.toContain('右侧');
        expect(empty).not.toContain('左侧');
        await shot(page, '06-signpost-zh.png');
    });
});
