// 管家办公工具箱(S2 第一波:读文问答 · 表格生成)真浏览器验收 · 跑 static/dist 真构建产物 +
// stub /api/**。这两只工具零新增前端组件——产物形状复用现成 kind:table / deeplink 渲染,
// 本脚本因此保的不是"新组件画对了",而是"后端两只新工具吐出来的产物形状,真的能被今天
// 已经在跑的通用渲染器正确画出来"(copy_table.py/copy_doc.py 的契约漂了,这里当场看得出来)。
//
// 剧本:①上传 xlsx + 打字「按供应商汇总金额」→ table_generate → 完成卡里预览表 + 下载按钮;
//       ②新对话 → 上传 pdf + 打字问题 → doc_read_qa → 答案正文 + 引用页码表。
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
        { kind: 'deeplink', label: '下载生成的表', href: '/api/ai/steward/attachments/art-e2e-0001/download' },
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

const DOC_QA_ANSWER = '付款期限为收到发票之日起 30 天。';
const TABLE_REPLY = '「sales.xlsx」按「按供应商汇总金额」整理好了:2 行,已生成新表。';

function sse(frames) {
    return frames.map((f) => `event: ${f.event}\ndata: ${JSON.stringify(f.data)}\n\n`).join('');
}

function attachmentRow(id, name, kind) {
    return {
        attachment_id: id,
        name,
        size_bytes: 1024,
        mime: 'application/octet-stream',
        kind,
        kind_source: 'rule',
        kind_reason: '',
        page_count: null,
        needs_model: false,
        actions: [],
        quote: {},
        status: 'ready',
    };
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
        if (p.endsWith('/steward/sessions') && req.method() === 'GET') return json(r, { sessions: [] });
        if (p.endsWith('/steward/sessions') && req.method() === 'POST') {
            world.seq += 1;
            const sid = 's-n' + world.seq;
            // 每个场景各起一条独立会话:第一条会话跑表格生成,第二条(点「新对话」之后)
            // 跑读文问答——按会话序号钉死场景,不按"这个会话第几次上传"猜(会话内始终只
            // 上传一次,猜错一次两个场景就串到同一个 kind 上,SSE 路由跟着全错)。
            const kind = world.seq === 1 ? 'table' : 'doc';
            world.sessions[sid] = { posted: false, kind };
            return json(r, { session_id: sid });
        }
        const sessMatch = p.match(/\/sessions\/(s-n\d+)\/attachments$/);
        if (sessMatch && req.method() === 'POST') {
            const sid = sessMatch[1];
            const kind = world.sessions[sid].kind;
            const row =
                kind === 'table'
                    ? attachmentRow('att-table-1', 'sales.xlsx', 'sales_summary')
                    : attachmentRow('att-doc-1', 'contract.pdf', 'unknown');
            return json(r, { attachments: [row], count: 1 });
        }
        const msgMatch = p.match(/\/sessions\/(s-n\d+)\/messages$/);
        if (msgMatch && req.method() === 'POST') {
            const sid = msgMatch[1];
            const kind = world.sessions[sid].kind;
            world.sessions[sid].posted = true;
            const taskId = kind === 'table' ? 't-table' : 't-doc';
            const ack =
                kind === 'table'
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
        // _steward_chat_v2_verify.cjs 验过,本脚本只关心"两只新工具的产物形状画得对不对"。
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
        const getSessMatch = p.match(/\/sessions\/(s-n\d+)$/);
        if (getSessMatch) {
            const sid = getSessMatch[1];
            const state = world.sessions[sid] || {};
            const messages = [];
            if (state.posted) {
                const askedText =
                    state.kind === 'table' ? '按供应商汇总金额' : '合同的付款期限是多久';
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
            }
            const out = { session_id: sid, messages };
            if (state.posted) out.current_task_id = state.kind === 'table' ? 't-table' : 't-doc';
            return json(r, out);
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

    await browser.close();
    srv.close();
    fs.rmSync(tmpDir, { recursive: true, force: true });
    console.log(`\n全部通过 · 截图在 ${path.relative(ROOT, OUT)}`);
})().catch((err) => {
    console.error('❌ 验收失败:', err);
    process.exit(1);
});
