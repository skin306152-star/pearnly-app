// 管家办公工具箱(S2 第一波:读文问答 · 表格生成 + doc_read_qa 的 OCR 计费网关)真浏览器验收 ·
// 跑 static/dist 真构建产物 + stub /api/**。这三只场景零新增前端组件——产物形状复用现成
// kind:table / actions / deeplink 渲染,本脚本因此保的不是"新组件画对了",而是"后端吐出来
// 的产物形状,真的能被今天已经在跑的通用渲染器正确画出来"(copy_table.py/copy_doc.py/
// copy_file.py 的契约漂了,这里当场看得出来)。
//
// 剧本:①上传 xlsx + 打字「按供应商汇总金额」→ table_generate → 完成卡里预览表 + 下载按钮;
//       ②新对话 → 上传 pdf + 打字问题 → doc_read_qa → 答案正文 + 引用页码表;
//       ③新对话 → 上传扫描件图片 + 打字问题 → 没 model_ok,attach_turn 弹计费确认卡(问答
//         口吻,不是「转换」那句)→ 点确认按钮 → doc_read_qa 真跑 → 答案正文 + 引用页码表。
//         场景③钉的是 tools_doc_qa 的 OCR 计费网关接得通:卡不是弹完就完事,点确认真的能
//         带着 model_ok 把活续上,不是弹完卡就没有下文。
// 跑法: node scripts/_steward_toolbox_verify.cjs → tests/e2e/_artifacts/steward_toolbox/
/* eslint-disable no-undef */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const PORT = 8918;
const BASE = `http://127.0.0.1:${PORT}`;
const OUT = path.join(ROOT, 'tests', 'e2e', '_artifacts', 'steward_toolbox');
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

// ---------- 桩世界 ----------

const TABLE_TASK_DONE = {
    task_id: 't-table',
    title: '表格生成',
    started_at: new Date(Date.now() - 3000).toISOString(),
    finished_at: new Date().toISOString(),
    agent_count: 1,
    cancellable: false,
    status: 'done',
    artifacts: [
        {
            kind: 'deeplink',
            label: '下载生成的表',
            href: '/api/ai/steward/attachments/art-e2e-0001/download',
        },
        {
            kind: 'table',
            label: '预览(前 20 行)',
            columns: [
                { key: 'supplier', label: 'supplier' },
                { key: 'amount_sum', label: 'amount_sum' },
            ],
            rows: [
                { supplier: '7-Eleven', amount_sum: '300.75' },
                { supplier: 'Makro', amount_sum: '300' },
            ],
        },
    ],
    steps: [
        { id: 'understand', label: '理解指令', state: 'done', detail: '表格生成', links: [] },
        { id: 'table_generate', label: '表格生成', state: 'done', detail: '生成完成', links: [] },
        { id: 'summarize', label: '整理答复', state: 'done', detail: '', links: [] },
    ],
};

const DOC_QA_TASK_DONE = {
    task_id: 't-doc',
    title: '读文问答',
    started_at: new Date(Date.now() - 3000).toISOString(),
    finished_at: new Date().toISOString(),
    agent_count: 1,
    cancellable: false,
    status: 'done',
    artifacts: [
        {
            kind: 'table',
            label: '引用原文',
            columns: [
                { key: 'page', label: '页' },
                { key: 'quote', label: '原文' },
            ],
            rows: [{ page: 1, quote: '付款期限为收到发票之日起 30 天' }],
        },
    ],
    steps: [
        { id: 'understand', label: '理解指令', state: 'done', detail: '读文问答', links: [] },
        { id: 'doc_read_qa', label: '读文问答', state: 'done', detail: '答复完成', links: [] },
        { id: 'summarize', label: '整理答复', state: 'done', detail: '', links: [] },
    ],
};

// 计费确认卡(status=waiting_user):与真后端 attach_turn._spend_card 同一份形状(actions
// 产物只有一个按钮,confirm_spend=true,cost.model_call=true)——点了这个按钮才把 model_ok
// 续给 doc_read_qa,不点永远停在这一张卡上。
const IMG_CARD_TASK = {
    task_id: 't-img-card',
    title: '读文问答',
    started_at: new Date(Date.now() - 1000).toISOString(),
    finished_at: new Date().toISOString(),
    agent_count: 1,
    cancellable: false,
    status: 'waiting_user',
    artifacts: [
        {
            kind: 'actions',
            label: '可执行的操作',
            actions: [
                {
                    tool: 'doc_read_qa',
                    label: '用 OCR 识别',
                    attachment_ids: ['att-img-1'],
                    confirm_spend: true,
                    cost: { wallet_charge: false, model_call: true, page_count: null },
                },
            ],
        },
    ],
    steps: [
        { id: 'understand', label: '理解指令', state: 'done', detail: '读文问答', links: [] },
        { id: 'doc_read_qa', label: '读文问答', state: 'queued', detail: '等你选一个', links: [] },
        { id: 'summarize', label: '整理答复', state: 'queued', detail: '', links: [] },
    ],
};

const IMG_DONE_TASK = {
    task_id: 't-img-run',
    title: '读文问答',
    started_at: new Date(Date.now() - 2000).toISOString(),
    finished_at: new Date().toISOString(),
    agent_count: 1,
    cancellable: false,
    status: 'done',
    artifacts: [
        {
            kind: 'table',
            label: '引用原文',
            columns: [
                { key: 'page', label: '页' },
                { key: 'quote', label: '原文' },
            ],
            rows: [{ page: 1, quote: '合计金额 500.00 铢' }],
        },
    ],
    steps: [
        { id: 'understand', label: '理解指令', state: 'done', detail: '读文问答', links: [] },
        { id: 'doc_read_qa', label: '读文问答', state: 'done', detail: '答复完成', links: [] },
        { id: 'summarize', label: '整理答复', state: 'done', detail: '', links: [] },
    ],
};

const DOC_QA_ANSWER = '付款期限为收到发票之日起 30 天。';
const TABLE_REPLY = '「sales.xlsx」按「按供应商汇总金额」整理好了:2 行,已生成新表。';
const IMG_CARD_REPLY =
    '「receipt.jpg」是扫描件或图片,要回答你的问题需先过一次 OCR 识别(按量计费,与识别票据同一个计费口)。';
const IMG_RUN_ACK = '「读文问答」已开始,结果回到这里。';
const IMG_ANSWER = '这张票的合计金额是 500.00 铢。';

function sse(frames) {
    return frames.map((f) => `event: ${f.event}\ndata: ${JSON.stringify(f.data)}\n\n`).join('');
}

function attachmentRow(id, name, kind, needsModel) {
    return {
        attachment_id: id,
        name,
        size_bytes: 1024,
        mime: 'application/octet-stream',
        kind,
        kind_source: 'rule',
        kind_reason: '',
        page_count: null,
        needs_model: !!needsModel,
        actions: [],
        quote: {},
        status: 'ready',
    };
}

// GET /sessions/{sid} 的权威消息重建(syncSession 靠它):三种 kind 各自的问句 + 落点任务
// id 按 stage 现算,不平行维护一份"当前该有几条消息"的计数器——stage 本身就是那份状态。
function sessionSnapshot(sid, state) {
    const messages = [];
    if (state.kind === 'img') {
        if (state.stage >= 1) {
            messages.push(
                {
                    id: 'um-' + sid,
                    role: 'user',
                    text: '这张票的合计金额是多少',
                    ts: new Date().toISOString(),
                },
                {
                    id: 'sm-' + sid,
                    role: 'steward',
                    text: IMG_CARD_REPLY,
                    ts: new Date().toISOString(),
                    task_id: 't-img-card',
                }
            );
        }
        if (state.stage >= 2) {
            messages.push(
                { id: 'um2-' + sid, role: 'user', text: '', ts: new Date().toISOString() },
                {
                    id: 'sm2-' + sid,
                    role: 'steward',
                    text: IMG_ANSWER,
                    ts: new Date().toISOString(),
                    task_id: 't-img-run',
                }
            );
        }
        const out = { session_id: sid, messages };
        if (state.stage >= 1) out.current_task_id = state.stage >= 2 ? 't-img-run' : 't-img-card';
        return out;
    }
    if (state.stage < 1) return { session_id: sid, messages };
    const askedText = state.kind === 'table' ? '按供应商汇总金额' : '合同的付款期限是多久';
    const taskId = state.kind === 'table' ? 't-table' : 't-doc';
    messages.push(
        { id: 'um-' + sid, role: 'user', text: askedText, ts: new Date().toISOString() },
        {
            id: 'sm-' + sid,
            role: 'steward',
            text: state.kind === 'table' ? TABLE_REPLY : DOC_QA_ANSWER,
            ts: new Date().toISOString(),
            task_id: taskId,
        }
    );
    return { session_id: sid, messages, current_task_id: taskId };
}

async function boot(page) {
    // world.phase 由「送出」推进:idle → running → done,每个会话各自一条任务。
    const world = { seq: 0, sessions: {} };

    const json = (r, payload) =>
        r.fulfill({ contentType: 'application/json', body: JSON.stringify(payload) });

    await page.route('**/api/**', (r) => {
        const req = r.request();
        const p = new URL(req.url()).pathname;
        if (p.includes('/api/me')) return json(r, { username: 'skin' });
        if (!p.includes('/api/ai/steward/')) return json(r, {});

        if (p.endsWith('/steward/status')) return json(r, { enabled: true, attachments: LIMITS });
        if (p.endsWith('/steward/budget')) {
            return json(r, {
                available: true,
                session: { spent_thb: '0.10', cap_thb: '12.00' },
                tenant_day: { spent_thb: '0.40', cap_thb: '150.00' },
            });
        }
        if (p.endsWith('/steward/sessions') && req.method() === 'GET')
            return json(r, { sessions: [] });
        if (p.endsWith('/steward/sessions') && req.method() === 'POST') {
            world.seq += 1;
            const sid = 's-n' + world.seq;
            // 每个场景各起一条独立会话:第一条跑表格生成,第二条(点「新对话」之后)跑
            // 读文问答(有文字层直读),第三条跑读文问答的 OCR 计费网关(扫描件图片,先弹卡
            // 再点确认)——按会话序号钉死场景,不按"这个会话第几次上传"猜(会话内始终只
            // 上传一次,猜错一次场景就串到别的 kind 上,路由跟着全错)。
            const kind = world.seq === 1 ? 'table' : world.seq === 2 ? 'doc' : 'img';
            world.sessions[sid] = { stage: 0, kind };
            return json(r, { session_id: sid });
        }
        const sessMatch = p.match(/\/sessions\/(s-n\d+)\/attachments$/);
        if (sessMatch && req.method() === 'POST') {
            const sid = sessMatch[1];
            const kind = world.sessions[sid].kind;
            const row =
                kind === 'table'
                    ? attachmentRow('att-table-1', 'sales.xlsx', 'sales_summary')
                    : kind === 'doc'
                      ? attachmentRow('att-doc-1', 'contract.pdf', 'unknown')
                      : attachmentRow('att-img-1', 'receipt.jpg', 'invoice', true);
            return json(r, { attachments: [row], count: 1 });
        }
        const msgMatch = p.match(/\/sessions\/(s-n\d+)\/messages$/);
        if (msgMatch && req.method() === 'POST') {
            const sid = msgMatch[1];
            const state = world.sessions[sid];
            const body = req.postDataJSON() || {};
            if (state.kind === 'img') {
                // 场景③的两段:先问(没 model_ok)→ 弹计费卡;点确认按钮(action.confirm_spend)
                // → 真派 doc_read_qa,task_id 换成另一条(卡的任务与真跑的任务不是同一条,
                // 与真后端 attach_turn._card + orchestrator._enqueue 各建一条任务行一致)。
                if (body.action && body.action.confirm_spend) {
                    state.stage = 2;
                    return json(r, {
                        message_id: 'sm2-' + sid,
                        user_message_id: 'um2-' + sid,
                        reply: IMG_RUN_ACK,
                        task_id: 't-img-run',
                        task_status: 'running',
                    });
                }
                state.stage = 1;
                return json(r, {
                    message_id: 'sm-' + sid,
                    user_message_id: 'um-' + sid,
                    reply: IMG_CARD_REPLY,
                    task_id: 't-img-card',
                    task_status: 'waiting_user',
                });
            }
            state.stage = 1;
            const taskId = state.kind === 'table' ? 't-table' : 't-doc';
            const ack =
                state.kind === 'table'
                    ? '「表格生成」已开始,结果回到这里。'
                    : '「读文问答」已开始,结果回到这里。';
            return json(r, {
                message_id: 'sm-' + sid,
                user_message_id: 'um-' + sid,
                reply: ack,
                task_id: taskId,
                task_status: 'running',
            });
        }
        // /tasks/{id}(非 SSE)在这套桩里直接给终态:loadTask() 第一次轮询就判定任务已终态,
        // 不会再开 SSE watch,而是直接 syncSession() 拉最终消息——SSE 帧驱动的逐步点亮已由
        // _steward_chat_v2_verify.cjs 验过,本脚本只关心"新工具/新网关吐出来的产物形状
        // 画得对不对"。t-img-card 的 status=waiting_user 同样是终态(前端轮询判据把它算
        // 进去)——按钮就是靠这一态才画成"可点"而不是置灰。
        if (p.endsWith('/tasks/t-table/events') || p.endsWith('/tasks/t-doc/events')) {
            const data = p.includes('t-table') ? TABLE_TASK_DONE : DOC_QA_TASK_DONE;
            return r.fulfill({
                contentType: 'text/event-stream',
                body: sse([
                    { event: 'task', data },
                    { event: 'end', data: { reason: 'terminal' } },
                ]),
            });
        }
        if (p.endsWith('/tasks/t-table')) return json(r, TABLE_TASK_DONE);
        if (p.endsWith('/tasks/t-doc')) return json(r, DOC_QA_TASK_DONE);
        if (p.endsWith('/tasks/t-img-card')) return json(r, IMG_CARD_TASK);
        if (p.endsWith('/tasks/t-img-run')) return json(r, IMG_DONE_TASK);
        const getSessMatch = p.match(/\/sessions\/(s-n\d+)$/);
        if (getSessMatch) {
            const sid = getSessMatch[1];
            const state = world.sessions[sid] || {};
            return json(r, sessionSnapshot(sid, state));
        }
        return json(r, {});
    });

    await page.addInitScript(() => {
        window.localStorage.setItem('mrpilot_token_ai', 'tok-toolbox-e2e');
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

async function shot(page, name) {
    await page.screenshot({ path: path.join(OUT, name), fullPage: false });
}

function writeFixture(dir, name, content) {
    const p = path.join(dir, name);
    fs.writeFileSync(p, content);
    return p;
}

(async () => {
    fs.mkdirSync(OUT, { recursive: true });
    const srv = await serve();
    const browser = await chromium.launch();
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await boot(page);

    // 假 xlsx/pdf 字节落临时目录,不落 OUT:桩世界不解析文件内容,只需要真实存在的文件
    // 供 setInputFiles 用——这两份不是要保留的产物,混进 OUT 会把"只认截图"的台账目录
    // 弄脏,每次跑都产生一份与本次验收无关的 diff。
    const tmpDir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'stw-toolbox-'));
    const xlsxPath = writeFixture(tmpDir, 'sales.xlsx', 'not-a-real-xlsx-stub-bytes');
    const pdfPath = writeFixture(tmpDir, 'contract.pdf', '%PDF-1.4 stub bytes for e2e upload only');
    const imgPath = writeFixture(tmpDir, 'receipt.jpg', 'not-a-real-jpeg-stub-bytes-for-e2e');

    // ===== 场景一:表格生成 =====
    // 附件上传前必须等会话真落地(ensureSession 的 POST /sessions 回来 S.sessionId 才有值,
    // 否则 attach.upload() 因 !S.sessionId 静默 return,chip 卡在 queued 永远等不到 ready)。
    const sessionReady = () =>
        page.waitForResponse(
            (r) => r.url().includes('/steward/sessions') && r.request().method() === 'POST',
            { timeout: 15000 }
        );
    const firstSession = sessionReady();
    await page.waitForSelector('.stw-welcome', { state: 'visible', timeout: 15000 });
    await firstSession;
    await page.setInputFiles('#stwAttFile', xlsxPath);
    // 等到 ready 而不是一出现就打字:还在 uploading/queued 时送出闸(canSubmit)不放行,
    // 过早按 Enter 只会是静默的空操作,断言会卡在下一步等不到东西。
    await page.waitForSelector('.stw-att-chip.ready', { state: 'visible', timeout: 10000 });
    await page.locator('#stwInput').click();
    await page.keyboard.type('按供应商汇总金额');
    await page.keyboard.press('Enter');
    ok('上传 xlsx + 打字整理指令 → 送出');

    await page.waitForSelector('.stw-donecard', { state: 'visible', timeout: 15000 });
    const previewTable = page.locator('.stw-donecard .stw-art table.stw-table');
    await previewTable.waitFor({ state: 'visible', timeout: 10000 });
    const previewText = await previewTable.innerText();
    if (!previewText.includes('300.75') || !previewText.includes('Makro')) {
        throw new Error(`表格生成预览没画对数字:${previewText}`);
    }
    const dlBtn = page.locator('[data-action="stw-att-dl"][data-aid="art-e2e-0001"]');
    if (!(await dlBtn.isVisible())) throw new Error('表格生成完成卡没有下载按钮');
    await shot(page, '01-table-generate-done.png');
    ok('table_generate 完成卡:预览表数字正确 + 下载按钮在场');

    // ===== 场景二:读文问答(新对话) =====
    const secondSession = sessionReady();
    await page.locator('.stw-new-chat').click();
    await page.waitForSelector('.stw-welcome', { state: 'visible', timeout: 10000 });
    await secondSession;
    await page.setInputFiles('#stwAttFile', pdfPath);
    // 等到 ready 而不是一出现就打字:还在 uploading/queued 时送出闸(canSubmit)不放行,
    // 过早按 Enter 只会是静默的空操作,断言会卡在下一步等不到东西。
    await page.waitForSelector('.stw-att-chip.ready', { state: 'visible', timeout: 10000 });
    await page.locator('#stwInput').click();
    await page.keyboard.type('合同的付款期限是多久');
    await page.keyboard.press('Enter');
    ok('新对话:上传 pdf + 打字问题 → 送出');

    // 断言目标是"答案正文那个气泡",不是随便哪里出现这句话——citations 表里的 quote
    // 列恰好也含这句话,只查 body.innerText 会连假绿都测不出来(quote 表渲染错了,这条
    // 断言照样通过)。故认 .stw-ai-body 这个具体元素。
    await page.waitForFunction(
        () => {
            var bodies = document.querySelectorAll('.stw-ai-body');
            for (var i = 0; i < bodies.length; i++) {
                if ((bodies[i].innerText || '').includes('付款期限为收到发票之日起')) return true;
            }
            return false;
        },
        { timeout: 15000 }
    );
    const citeTable = page.locator('.stw-art table.stw-table');
    await citeTable.waitFor({ state: 'visible', timeout: 10000 });
    const citeText = await citeTable.innerText();
    if (!citeText.includes('1') || !citeText.includes('付款期限为收到发票之日起 30 天')) {
        throw new Error(`引用表没画对页码/原文:${citeText}`);
    }
    await shot(page, '02-doc-read-qa-done.png');
    ok('doc_read_qa 答案卡:答案正文 + 引用页码表在场');

    // ===== 场景三:读文问答的 OCR 计费网关(扫描件图片,先弹卡再点确认) =====
    const thirdSession = sessionReady();
    await page.locator('.stw-new-chat').click();
    await page.waitForSelector('.stw-welcome', { state: 'visible', timeout: 10000 });
    await thirdSession;
    await page.setInputFiles('#stwAttFile', imgPath);
    await page.waitForSelector('.stw-att-chip.ready', { state: 'visible', timeout: 10000 });
    await page.locator('#stwInput').click();
    await page.keyboard.type('这张票的合计金额是多少');
    await page.keyboard.press('Enter');
    ok('新对话:上传扫描件图片 + 打字问题 → 送出');

    // 没 model_ok 那一轮必须停在计费卡上,不许自己把 OCR 跑了——按钮要活着(status=
    // waiting_user 才不置灰),文案要是问答口吻(不是 file_convert 那句「才能读出内容」)。
    const confirmBtn = page.locator('.stw-arts button[data-tool="doc_read_qa"][data-spend="1"]');
    await confirmBtn.waitFor({ state: 'visible', timeout: 15000 });
    if (await confirmBtn.isDisabled()) throw new Error('计费确认按钮被置灰,点不动');
    await page.waitForFunction(
        () => {
            var bodies = document.querySelectorAll('.stw-ai-body');
            for (var i = 0; i < bodies.length; i++) {
                if ((bodies[i].innerText || '').includes('OCR 识别')) return true;
            }
            return false;
        },
        { timeout: 10000 }
    );
    await shot(page, '03a-doc-read-qa-spend-card.png');
    ok('OCR 计费确认卡出现:问答口吻文案 + 可点的确认按钮');

    // 点确认:model_ok 续给 doc_read_qa,真跑出答案——弹完卡不是死路一条。
    await confirmBtn.click();
    await page.waitForFunction(
        () => {
            var bodies = document.querySelectorAll('.stw-ai-body');
            for (var i = 0; i < bodies.length; i++) {
                if ((bodies[i].innerText || '').includes('合计金额是 500.00 铢')) return true;
            }
            return false;
        },
        { timeout: 15000 }
    );
    const imgCiteTable = page.locator('.stw-art table.stw-table').last();
    await imgCiteTable.waitFor({ state: 'visible', timeout: 10000 });
    const imgCiteText = await imgCiteTable.innerText();
    if (!imgCiteText.includes('500.00')) {
        throw new Error(`OCR 网关答案卡的引用表没画对内容:${imgCiteText}`);
    }
    await shot(page, '03b-doc-read-qa-ocr-answer.png');
    ok('点确认后 doc_read_qa 真跑:答案正文 + 引用页码表在场');

    await browser.close();
    srv.close();
    fs.rmSync(tmpDir, { recursive: true, force: true });
    console.log(`\n全部通过 · 截图在 ${path.relative(ROOT, OUT)}`);
})().catch((err) => {
    console.error('❌ 验收失败:', err);
    process.exit(1);
});
