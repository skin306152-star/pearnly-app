// 智能管家会话流(S1 改版)真浏览器验收 · 跑 static/dist 真构建产物 + stub /api/**。
// 剧本:空态欢迎屏 → 键盘真输入发消息 → 内联过程条(SSE 帧驱动)→ 停止键形态 →
//       授权卡 → 批准 → 完成卡 + 收尾正文(markdown 表格)→ 侧栏历史 → 切会话
//       (历史过程条按需补拉)→ 新对话回空态 → 390 宽抽屉。
// 期望文案一律现场取页面词典(window.at),脚本零词典副本;点击全部唯一定位。
// 跑法: node scripts/_steward_chat_v2_verify.cjs → tests/e2e/_artifacts/steward-chat-v2/
/* eslint-disable no-undef */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const PORT = 8917;
const BASE = `http://127.0.0.1:${PORT}`;
const OUT = path.join(ROOT, 'tests', 'e2e', '_artifacts', 'steward-chat-v2');
const LIMITS = require(path.join(ROOT, 'tests', 'e2e', '_fixtures_steward_limits.json'));

const TYPES = {
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.html': 'text/html',
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
    '.ico': 'image/x-icon',
    '.woff2': 'font/woff2',
};

function serve() {
    const srv = http.createServer((req, res) => {
        const p = decodeURIComponent(req.url.split('?')[0]);
        const file = path.join(ROOT, p);
        if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
            res.writeHead(404);
            return res.end('nf');
        }
        res.writeHead(200, {
            'content-type': TYPES[path.extname(file)] || 'text/plain',
            'cache-control': 'no-store',
        });
        fs.createReadStream(file).pipe(res);
    });
    return new Promise((r) => srv.listen(PORT, () => r(srv)));
}

// ---------- 桩世界(形状逐键对齐真后端投影) ----------

const ACK = '已受理:读取并识别票据,完成后在此汇报。';
const FINAL =
    '两张票据已识别并写入 Express:\n\n' +
    '| 商户 | 日期 | 金额 |\n| --- | --- | --- |\n' +
    '| 7-Eleven | 2026-07-28 | ฿428.50 |\n| Makro | 2026-07-30 | ฿856.00 |\n\n' +
    '合计 **฿1,284.50**,回读校验一致。';
const HIST_REPLY = '6 月 **KBank** 流水 412 笔已全部对平,差异 **0** 笔。';

function authzCard(status) {
    const pending = status === 'pending';
    return {
        token: 'tok-e2e-chatv2-0001',
        tool: 'erp_push_sales_summary',
        title: '将 2 张进项票据写入 Express(69EXP · 2026-07)',
        risk: 'write',
        args: { rows: '2', total: '฿1,284.50' },
        status,
        requested_at: new Date(Date.now() - 5000).toISOString(),
        expires_at: new Date(Date.now() + 295000).toISOString(),
        decided_by: pending ? null : 'u1',
        decided_at: pending ? null : new Date().toISOString(),
    };
}

function liveTask(phase) {
    const base = {
        task_id: 't-live',
        title: '两张票据识别并写入 Express',
        started_at: new Date(Date.now() - 20000).toISOString(),
        finished_at: null,
        agent_count: 2,
        cancellable: true,
        artifacts: [],
    };
    if (phase === 'reading') {
        return {
            ...base,
            status: 'running',
            steps: [
                {
                    id: 's1',
                    kind: 'tool',
                    label: '读取票据原件',
                    state: 'done',
                    detail: '2 份',
                    links: [],
                },
                {
                    id: 's2',
                    kind: 'tool',
                    label: 'OCR 识别',
                    state: 'running',
                    detail: '',
                    links: [],
                },
                { id: 'final', label: '整理答复', state: 'queued', detail: '', links: [] },
            ],
        };
    }
    if (phase === 'authz') {
        return {
            ...base,
            status: 'waiting_user',
            cancellable: false,
            authorization: authzCard('pending'),
            steps: [
                {
                    id: 's1',
                    kind: 'tool',
                    label: '读取票据原件',
                    state: 'done',
                    detail: '2 份',
                    links: [],
                },
                {
                    id: 's2',
                    kind: 'tool',
                    label: 'OCR 识别',
                    state: 'done',
                    detail: '2 张有效',
                    links: [],
                },
                {
                    id: 's3',
                    kind: 'tool',
                    label: '写入 Express',
                    state: 'waiting_auth',
                    detail: '',
                    links: [],
                },
                { id: 'final', label: '整理答复', state: 'queued', detail: '', links: [] },
            ],
        };
    }
    if (phase === 'pushing') {
        return {
            ...base,
            status: 'running',
            cancellable: false,
            authorization: authzCard('approved'),
            steps: [
                {
                    id: 's1',
                    kind: 'tool',
                    label: '读取票据原件',
                    state: 'done',
                    detail: '2 份',
                    links: [],
                },
                {
                    id: 's2',
                    kind: 'tool',
                    label: 'OCR 识别',
                    state: 'done',
                    detail: '2 张有效',
                    links: [],
                },
                {
                    id: 's3',
                    kind: 'tool',
                    label: '写入 Express',
                    state: 'running',
                    detail: '',
                    links: [],
                },
                { id: 'final', label: '整理答复', state: 'queued', detail: '', links: [] },
            ],
        };
    }
    return {
        ...base,
        status: 'done',
        finished_at: new Date().toISOString(),
        authorization: authzCard('approved'),
        artifacts: [{ kind: 'deeplink', label: '查看推送日志', href: '#/reports' }],
        steps: [
            {
                id: 's1',
                kind: 'tool',
                label: '读取票据原件',
                state: 'done',
                detail: '2 份',
                links: [],
            },
            {
                id: 's2',
                kind: 'tool',
                label: 'OCR 识别',
                state: 'done',
                detail: '2 张有效',
                links: [],
            },
            {
                id: 's3',
                kind: 'tool',
                label: '写入 Express',
                state: 'done',
                detail: '回读一致',
                links: [],
            },
            { id: 'final', label: '整理答复', state: 'done', detail: '', links: [] },
        ],
    };
}

const HIST_TASK = {
    task_id: 't-hist',
    title: '6 月银行对账核对',
    status: 'done',
    started_at: '2026-07-30T02:00:00Z',
    finished_at: '2026-07-30T02:03:00Z',
    agent_count: 3,
    cancellable: false,
    artifacts: [{ kind: 'deeplink', label: '查看对账底稿', href: '#/reports' }],
    steps: [
        {
            id: 's1',
            kind: 'tool',
            label: '拉取 KBank 6 月流水',
            state: 'done',
            detail: '412 笔',
            links: [],
        },
        { id: 's2', kind: 'tool', label: '逐笔比对账面', state: 'done', detail: '', links: [] },
        { id: 'final', label: '整理答复', state: 'done', detail: '差异 0 笔', links: [] },
    ],
};

function sse(frames) {
    return frames.map((f) => `event: ${f.event}\ndata: ${JSON.stringify(f.data)}\n\n`).join('');
}

async function boot(page) {
    // 桩世界状态机:phase 由「送出/批准」推进;消息流按 phase 重建。
    const world = { phase: 'idle', posted: false, streamHits: 0, seq: 0 };

    const json = (r, payload) =>
        r.fulfill({ contentType: 'application/json', body: JSON.stringify(payload) });

    await page.route('**/api/**', (r) => {
        const req = r.request();
        const p = new URL(req.url()).pathname;
        if (p.includes('/api/me')) return json(r, { username: 'skin' });
        if (!p.includes('/api/ai/steward/')) return json(r, {});

        if (p.endsWith('/steward/status')) return json(r, { enabled: true, attachments: LIMITS });
        if (p.endsWith('/steward/sessions') && req.method() === 'POST') {
            world.seq += 1;
            return json(r, { session_id: 's-n' + world.seq });
        }
        if (p.endsWith('/steward/sessions') && req.method() === 'GET') {
            const sessions = [
                {
                    session_id: 's-hist',
                    title: '6 月银行对账核对',
                    last_active_at: '2026-08-04T10:00:00Z',
                },
            ];
            if (world.posted) {
                sessions.unshift({
                    session_id: 's-n1',
                    title: '这两张票帮我入账,推到 Express',
                    last_active_at: new Date().toISOString(),
                });
            }
            return json(r, { sessions });
        }
        if (p.endsWith('/steward/budget'))
            return json(r, {
                available: true,
                session: { spent_thb: '0.85', cap_thb: '12.00' },
                tenant_day: { spent_thb: '3.10', cap_thb: '150.00' },
            });
        if (/\/sessions\/s-n\d+\/messages$/.test(p)) {
            world.posted = true;
            world.phase = 'reading';
            return json(r, {
                message_id: 'sm1',
                user_message_id: 'um1',
                reply: ACK,
                task_id: 't-live',
                task_status: 'running',
            });
        }
        if (p.endsWith('/authorizations/approve')) {
            world.phase = 'pushing';
            return json(r, { task_id: 't-live', authorization: authzCard('approved') });
        }
        if (p.endsWith('/tasks/t-live/events')) {
            world.streamHits += 1;
            let frames;
            if (world.phase === 'reading') {
                frames = [
                    { event: 'task', data: liveTask('reading') },
                    { event: 'task', data: liveTask('authz') },
                    { event: 'end', data: { reason: 'terminal' } },
                ];
                world.phase = 'authz';
            } else {
                frames = [
                    { event: 'task', data: liveTask('pushing') },
                    { event: 'task', data: liveTask('done') },
                    { event: 'end', data: { reason: 'terminal' } },
                ];
                // 流播完即收口:流后的 syncSession 要拿得到收尾正文(与真后端时序一致)。
                world.phase = 'done';
            }
            // 晚 600ms 落帧:留出「running + 停止键」可断言可截图的窗口。
            return new Promise((done) =>
                setTimeout(
                    () =>
                        done(
                            r.fulfill({
                                contentType: 'text/event-stream',
                                body: sse(frames),
                            })
                        ),
                    600
                )
            );
        }
        if (p.endsWith('/tasks/t-live')) {
            return json(r, liveTask(world.phase === 'idle' ? 'reading' : world.phase));
        }
        if (p.endsWith('/tasks/t-hist')) return json(r, HIST_TASK);
        if (/\/sessions\/s-n\d+$/.test(p)) {
            const sid = p.split('/').pop();
            const messages = [];
            if (world.posted && sid === 's-n1') {
                messages.push(
                    {
                        id: 'um1',
                        role: 'user',
                        text: '这两张票帮我入账,推到 Express',
                        ts: '2026-08-05T03:00:00Z',
                    },
                    {
                        id: 'sm1',
                        role: 'steward',
                        text: ACK,
                        ts: '2026-08-05T03:00:01Z',
                        task_id: 't-live',
                    }
                );
                if (world.phase === 'done') {
                    messages.push({
                        id: 'sm2',
                        role: 'steward',
                        text: FINAL,
                        ts: '2026-08-05T03:00:40Z',
                        task_id: 't-live',
                    });
                }
            }
            const out = { session_id: sid, messages };
            if (world.posted && sid === 's-n1') out.current_task_id = 't-live';
            return json(r, out);
        }
        if (p.endsWith('/sessions/s-hist')) {
            return json(r, {
                session_id: 's-hist',
                messages: [
                    {
                        id: 'hm1',
                        role: 'user',
                        text: '6 月银行对账做完了吗?',
                        ts: '2026-07-30T02:00:00Z',
                    },
                    {
                        id: 'hm2',
                        role: 'steward',
                        text: HIST_REPLY,
                        ts: '2026-07-30T02:03:00Z',
                        task_id: 't-hist',
                    },
                ],
                current_task_id: 't-hist',
            });
        }
        return json(r, {});
    });

    await page.addInitScript(() => {
        window.localStorage.setItem('mrpilot_token_ai', 'tok-s1-chat');
        window.localStorage.setItem('mrpilot_lang', 'zh');
    });
    await page.goto(`${BASE}/static/dist/ai.html#/steward`);
    return world;
}

// ---------- 断言小件 ----------

let step = 0;
function ok(label) {
    step += 1;
    console.log(`  ✅ ${String(step).padStart(2, '0')} ${label}`);
}

async function word(page, key) {
    return page.evaluate((k) => window.at(k), key);
}

async function shot(page, name) {
    await page.screenshot({ path: path.join(OUT, name), fullPage: false });
}

(async () => {
    fs.mkdirSync(OUT, { recursive: true });
    const srv = await serve();
    const browser = await chromium.launch();
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    const world = await boot(page);

    // 1) 空态欢迎屏:标题词条真渲染 + 三条示例问法 + 输入卡在场。
    await page.waitForSelector('.stw-welcome', { state: 'visible', timeout: 15000 });
    const welcomeT = await word(page, 'stw_welcome_t');
    if (!(await page.locator('.stw-welcome h1').innerText()).includes(welcomeT)) {
        throw new Error('欢迎屏标题与词典不符');
    }
    const prompts = await page.locator('.stw-w-prompt').count();
    if (prompts !== 3) throw new Error(`示例问法应 3 条,实得 ${prompts}`);
    if (!(await page.locator('#stwInput').isVisible())) throw new Error('输入框不可见');
    if (!(await page.locator('.stw-clip').isVisible())) throw new Error('回形针不可见');
    // 侧栏:历史一条 + 余额行(数字来自桩后端)。
    await page.waitForSelector('.stw-sess-t', { state: 'visible' });
    const foot = await page.locator('.stw-side-foot').innerText();
    if (!foot.includes('0.85') || !foot.includes('12.00')) {
        throw new Error(`侧栏余额行没画对:${foot}`);
    }
    await shot(page, '01-empty-welcome.png');
    ok('空态欢迎屏 + 三示例 + 侧栏历史与余额行');

    // 2) 键盘真输入(不用 fill)→ Enter 送出 → 右对齐用户气泡。
    await page.locator('#stwInput').click();
    await page.keyboard.type('这两张票帮我入账,推到 Express');
    const active = await page.evaluate(() => document.activeElement && document.activeElement.id);
    if (active !== 'stwInput') throw new Error('焦点不在输入框');
    if (await page.locator('#stwSendBtn').isDisabled()) throw new Error('有字了发送键仍禁用');
    await page.keyboard.press('Enter');
    await page.waitForSelector('.stw-msg.me .stw-bubble', { state: 'visible' });
    // 一次 evaluate 里取两个矩形:feed 在 SSE 帧到达时会重画,分两次查会撞上换节点的窗口。
    const geom = await page.evaluate(() => {
        const bub = document.querySelector('.stw-msg.me .stw-bubble');
        const feed = document.getElementById('stwFeed');
        if (!bub || !feed) return null;
        const b = bub.getBoundingClientRect();
        const f = feed.getBoundingClientRect();
        return { bubMid: b.x + b.width / 2, feedMid: f.x + f.width / 2 };
    });
    if (!geom || geom.bubMid <= geom.feedMid) throw new Error('用户气泡没有靠右');
    ok('键盘输入 → Enter 送出 → 用户气泡右对齐');

    // 3) 过程条 running(SSE 首帧前靠 GET 种子)+ 发送键翻成停止形态。
    await page.waitForSelector('.stw-proc', { state: 'visible' });
    const runningLabel = await page.locator('.stw-proc-sum').innerText();
    if (!runningLabel.includes('OCR 识别')) {
        throw new Error(`running 摘要应带正在跑那一步,实得:${runningLabel}`);
    }
    const stopBtn = page.locator('#stwSendBtn.stop');
    if (!(await stopBtn.isVisible())) throw new Error('running 时发送键没翻停止形态');
    if ((await stopBtn.getAttribute('title')) !== (await word(page, 'stw_stop'))) {
        throw new Error('可停任务的停止键 title 不对');
    }
    await shot(page, '02-proc-running-stop.png');
    ok('过程条 running(摘要=当前步)+ 停止键形态');

    // 4) SSE 帧推进到授权卡:待批准徽章 + 批准/拒绝按钮 + 倒计时。
    await page.waitForSelector('.stw-authz', { state: 'visible', timeout: 15000 });
    const approveLabel = await word(page, 'stw_authz_approve');
    const approveBtn = page.locator('.stw-authz button', { hasText: approveLabel });
    if (!(await approveBtn.isVisible())) throw new Error('批准按钮不可见');
    if (!(await page.locator('#stwAuthzCd').innerText()).match(/\d/)) {
        throw new Error('授权倒计时没数字');
    }
    // 等确认时任务不在跑:发送键回到发送形态(能回话/追问)。
    if (await page.locator('#stwSendBtn.stop').isVisible()) {
        throw new Error('waiting_user 还挂着停止键');
    }
    await shot(page, '03-authz-card.png');
    ok('授权卡入流(待批准 + 倒计时)· 等确认时发送键复位');

    // 5) 批准 → 第二段 SSE → 完成卡 + 收尾正文 markdown 表格 + 过程条自动折叠。
    await approveBtn.click();
    await page.waitForSelector('.stw-donecard', { state: 'visible', timeout: 15000 });
    if (world.phase !== 'done') throw new Error(`批准后桩世界没推进:${world.phase}`);
    await page.waitForSelector('.stw-ai-body table', { state: 'visible', timeout: 15000 });
    const numCells = await page.locator('.stw-ai-body td.num').count();
    if (numCells < 2) throw new Error('金额列没按数字列右对齐标记');
    const procCollapsed = await page
        .locator('[data-proc="t-live"]')
        .evaluate((el) => el.classList.contains('collapsed'));
    if (!procCollapsed) throw new Error('任务收尾后过程条没自动折叠');
    const doneSum = await page.locator('[data-proc="t-live"] .stw-proc-sum').innerText();
    if (!doneSum.includes('4')) throw new Error(`折叠摘要应带步数,实得:${doneSum}`);
    await shot(page, '04-done-card-final.png');
    ok('批准 → 完成卡 + markdown 表格 + 过程条折叠摘要');

    // 6) 点开折叠的过程条还能看明细(已发生的事实不消失)。
    // SELECTOR-INDEX-OK: 页面此刻只有 t-live 一条过程条,data-proc 已唯一定位。
    await page.locator('[data-proc="t-live"] .stw-proc-hd').click();
    await page.waitForSelector('[data-proc="t-live"] .stw-steps', { state: 'visible' });
    ok('折叠过程条点开可回看步骤明细');

    // 7) 切到历史会话:消息重建 + 历史任务过程条后台补拉(默认折叠)。
    await page.locator('.stw-sess-t[data-sid="s-hist"]').click();
    await page.waitForSelector('[data-proc="t-hist"]', { state: 'visible', timeout: 15000 });
    const histCollapsed = await page
        .locator('[data-proc="t-hist"]')
        .evaluate((el) => el.classList.contains('collapsed'));
    if (!histCollapsed) throw new Error('历史 done 任务的过程条应默认折叠');
    if (!(await page.locator('.stw-ai-body b', { hasText: 'KBank' }).isVisible())) {
        throw new Error('历史正文粗体没渲染');
    }
    await shot(page, '05-history-session.png');
    ok('切会话:历史消息 + 补拉的过程条(默认折叠)');

    // 8) 新对话回空态,标题复位。
    await page.locator('.stw-new-chat').click();
    await page.waitForSelector('.stw-welcome', { state: 'visible' });
    const title = await page.locator('#stwChatTitle').innerText();
    if (title !== (await word(page, 'stw_sess_untitled'))) {
        throw new Error(`新对话标题应是词条「新对话」,实得:${title}`);
    }
    await shot(page, '06-new-chat-empty.png');
    ok('新对话 → 空态欢迎屏 + 标题复位');

    // 9) 390×844:侧栏收成抽屉,菜单钮开、遮罩收。
    await page.setViewportSize({ width: 390, height: 844 });
    if (!(await page.locator('#stwMenuBtn').isVisible())) throw new Error('390 宽菜单钮不可见');
    // 收起态判据:滑出 + 隐身(getComputedStyle 抓真值,不看类名)。visibility 的切换
    // 挂着「滑完再隐」的过渡延迟,等它落定。
    await page.waitForFunction(() => {
        const el = document.getElementById('stwSide');
        return el && getComputedStyle(el).visibility === 'hidden';
    });
    await page.locator('#stwMenuBtn').click();
    await page.waitForFunction(() => {
        const el = document.getElementById('stwSide');
        const host = document.getElementById('stwBody');
        return (
            el &&
            getComputedStyle(el).visibility === 'visible' &&
            Math.abs(el.getBoundingClientRect().left - host.getBoundingClientRect().left) < 2
        );
    });
    if (!(await page.locator('#stwScrim').isVisible())) throw new Error('抽屉开着没有遮罩');
    await shot(page, '07-mobile-drawer.png');
    // 遮罩中心被抽屉盖着(这正是抽屉的意义),点它右侧真正露出的那条。
    const scrimBox = await page.locator('#stwScrim').boundingBox();
    await page
        .locator('#stwScrim')
        .click({ position: { x: scrimBox.width - 8, y: scrimBox.height / 2 } });
    await page.waitForFunction(() => {
        const el = document.getElementById('stwSide');
        return el && getComputedStyle(el).visibility === 'hidden';
    });
    await shot(page, '08-mobile-empty.png');
    ok('390 宽:抽屉开合(真隐身/真滑入)+ 遮罩点击关闭');

    // 10) 移动端横向不溢出。
    const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth
    );
    if (overflow > 1) throw new Error(`移动端横向溢出 ${overflow}px`);
    ok('390 宽零横向溢出');

    await browser.close();
    srv.close();
    console.log(`\n全部通过 · 截图在 ${path.relative(ROOT, OUT)}`);
})().catch((err) => {
    console.error('❌ 验收失败:', err);
    process.exit(1);
});
