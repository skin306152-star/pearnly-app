// 万能口(F1 · 前端)· 本地真浏览器验收(跑 static/dist 真构建产物)
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**(同
// _b2m1_steward_local.spec.js 先例)。验的是「一份料从进浏览器到进对话」这条线:
// 三种入口(回形针 / 拖拽 / 粘贴)、附件盘四态、送出闸、用户气泡下的只读原件行、
// 回执卡上的闭集动作按钮回传。截图存 _artifacts/f1_steward_attach/。
//
// ⚠️ 桩的形状不是随便编的,它就是被验的契约本身 —— 逐字段抄自真后端:
//   attachments.public_attachment(...)  → Attachment
//   copy_file.files_table / actions_block → artifacts kind=table / kind=actions
//   attachments.limits()                 → GET /status 的 attachments 块
// 抄错一处就会像 B2-M1 那次一样「桩和前端自洽、产品里全废」。
//
// 起法:npx playwright test tests/e2e/_f1_steward_attach_local.spec.js
/* global window, document, DataTransfer, DragEvent, ClipboardEvent, getComputedStyle */

const { test, expect } = require('@playwright/test');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const ROOT = path.resolve(__dirname, '..', '..');
const PORT = 8993;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'f1_steward_attach');

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

// services/steward/attachments.limits() 逐键。
const LIMITS = {
    max_file_bytes: 20971520,
    max_batch_bytes: 36700160,
    max_files: 20,
    // 运输皮(zip/heic)必须在 accept 里:漏了它们,<input accept> 在文件对话框就把 zip
    // 滤掉,拖进来的也被当坏格式灰掉 —— 后端「zip 自动展开 / HEIC 转 JPEG」永远跑不到。
    accept: ['.csv', '.heic', '.jpg', '.pdf', '.png', '.xls', '.xlsx', '.zip'],
    ttl_days: 30,
};

// services/steward/attachments.public_attachment() 逐键。
function attachment(id, name, kind, extra) {
    return Object.assign(
        {
            attachment_id: id,
            name,
            size_bytes: 4,
            mime: 'application/pdf',
            kind,
            kind_source: kind === 'unknown' ? 'unknown' : 'rule',
            kind_reason: 'gl_name_or_text',
            page_count: 3,
            needs_model: false,
            actions: kind === 'gl_ledger' ? ['file_convert'] : [],
            quote: { allowed: true, error_code: null, kind: 'pdf', units: 3, page_count: 3 },
            status: 'ready',
        },
        extra || {}
    );
}

// attach_turn._receipt_card() 的产物形状(copy_file.files_table + actions_block)。
function receiptTask() {
    return {
        task_id: 't1',
        title: '收到的文件',
        status: 'waiting_user',
        started_at: '2026-07-27T09:05:00Z',
        agent_count: 1,
        cancellable: false,
        steps: [
            { id: 'understand', label: '听懂要干嘛', state: 'done' },
            { id: 'detect', label: '认一下这是什么料', state: 'done', detail: '2 份' },
            { id: 'summarize', label: '汇总', state: 'queued', detail: '等你选一个' },
        ],
        artifacts: [
            {
                kind: 'table',
                label: '收到的文件',
                columns: [
                    { key: 'name', label: '文件' },
                    { key: 'kind', label: '认成什么' },
                    { key: 'pages', label: '页数' },
                    { key: 'note', label: '说明' },
                ],
                rows: [
                    { name: 'gl.pdf', kind: 'GL 台账', pages: 3, note: '' },
                    { name: 'mystery.pdf', kind: '认不出是什么', pages: 1, note: '' },
                ],
            },
            {
                kind: 'actions',
                label: '你想让我做哪一样',
                actions: [
                    {
                        tool: 'file_convert',
                        label: '转成 Excel · gl.pdf',
                        attachment_ids: ['u1'],
                        confirm_spend: false,
                        cost: { wallet_charge: false, model_call: false, page_count: 3 },
                    },
                ],
            },
        ],
    };
}

function json(route, payload) {
    return route.fulfill({ contentType: 'application/json', body: JSON.stringify(payload) });
}

async function boot(page, opts) {
    opts = opts || {};
    const posts = [];
    const uploads = [];

    await page.route('**/api/me**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{"username":"skin"}' })
    );
    await page.route('**/api/workorder/orders**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{"orders":[]}' })
    );
    await page.route('**/api/ai/steward/**', async (r) => {
        const p = new URL(r.request().url()).pathname;
        const method = r.request().method();

        if (p.endsWith('/steward/status')) {
            return json(r, { enabled: true, attachments: opts.noLimits ? undefined : LIMITS });
        }
        if (p.endsWith('/attachments') && method === 'POST') {
            uploads.push(p);
            if (opts.uploadStatus) {
                return r.fulfill({
                    status: opts.uploadStatus,
                    contentType: 'application/json',
                    body: JSON.stringify({ detail: opts.uploadDetail }),
                });
            }
            const n = uploads.length;
            const kind = n === 1 ? 'gl_ledger' : 'unknown';
            const name = n === 1 ? 'gl.pdf' : 'mystery.pdf';
            return json(r, { attachments: [attachment('u' + n, name, kind)], count: 1 });
        }
        if (p.endsWith('/messages') && method === 'POST') {
            posts.push(r.request().postDataJSON());
            return json(r, {
                message_id: 'm1',
                user_message_id: 'um1',
                reply: '收到 2 份:1 份 GL 台账,1 份认不出是什么。想让我做哪一样?',
                task_id: 't1',
                task_status: 'waiting_user',
                attachments: [
                    attachment('u1', 'gl.pdf', 'gl_ledger'),
                    attachment('u2', 'mystery.pdf', 'unknown'),
                ],
            });
        }
        if (p.indexOf('/steward/tasks/') >= 0) return json(r, receiptTask());
        if (/\/steward\/sessions\/[^/]+$/.test(p)) {
            return json(r, { session_id: 's1', messages: [] });
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
        window.localStorage.setItem('mrpilot_token_ai', 'tok-f1');
        window.localStorage.setItem('mrpilot_lang', 'zh');
    });
    await page.goto(`${BASE}/static/dist/ai.html#/steward`);
    await page.waitForSelector('#v-steward.on #stwInput', { state: 'visible', timeout: 15000 });
    return { posts, uploads };
}

// 拖拽:构造真 DataTransfer 再派发真 dragenter/drop(不是直接调 addFiles —— 那样
// 验的是自己的函数,不是浏览器里真的拖得动)。
async function dragFiles(page, files) {
    await page.evaluate((specs) => {
        const dt = new DataTransfer();
        specs.forEach((s) => dt.items.add(new File([s.body], s.name, { type: s.type })));
        const host = document.getElementById('stwBody');
        host.dispatchEvent(new DragEvent('dragenter', { dataTransfer: dt, bubbles: true }));
        window.__dropDT = dt;
    }, files);
}

async function dropNow(page) {
    await page.evaluate(() => {
        const host = document.getElementById('stwBody');
        host.dispatchEvent(new DragEvent('drop', { dataTransfer: window.__dropDT, bubbles: true }));
    });
}

test.describe('万能口 F1(本地 stub · 真构建产物)', () => {
    test('三种入口都在:回形针可点 · 拖拽亮落区 · 粘贴收文件', async ({ page }) => {
        await boot(page);

        // ① 回形针:限额从 /status 读到了才渲染,accept 用后端给的那份(不硬编码)。
        const clip = page.locator('.stw-clip');
        await expect(clip).toBeVisible();
        await expect(page.locator('#stwAttFile')).toHaveAttribute(
            'accept',
            LIMITS.accept.join(',')
        );

        // ② 拖拽:落区在 dragenter 时真的可见(不是只把 hidden 属性摘了)。
        await expect(page.locator('#stwDrop')).toBeHidden();
        await dragFiles(page, [{ name: 'gl.pdf', body: 'x', type: 'application/pdf' }]);
        await expect(page.locator('#stwDrop')).toBeVisible();
        const box = await page.locator('#stwDrop').boundingBox();
        const col = await page.locator('.stw-col.stw-right').boundingBox();
        // 落区要盖住整条对话栏,不是只盖输入框那一条(拖着一叠文件的手不该被要求瞄准)。
        expect(box.height).toBeGreaterThan(col.height * 0.9);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '01-drop-overlay-zh.png'),
            fullPage: true,
        });

        await dropNow(page);
        await expect(page.locator('#stwDrop')).toBeHidden();
        await expect(page.locator('.stw-att-chip')).toHaveCount(1);

        // ③ 粘贴:焦点不在输入框上也要收得到(截图刚复制完常常如此)。
        await page.evaluate(() => {
            const dt = new DataTransfer();
            dt.items.add(new File(['y'], 'slip.jpg', { type: 'image/jpeg' }));
            document.body.dispatchEvent(
                new ClipboardEvent('paste', { clipboardData: dt, bubbles: true })
            );
        });
        await expect(page.locator('.stw-att-chip')).toHaveCount(2);
    });

    test('传完显示认成什么 · 认不出就说认不出 · 可移除', async ({ page }) => {
        await boot(page);
        await dragFiles(page, [
            { name: 'gl.pdf', body: 'x', type: 'application/pdf' },
            { name: 'mystery.pdf', body: 'y', type: 'application/pdf' },
        ]);
        await dropNow(page);

        await expect(page.locator('.stw-att-chip.ready')).toHaveCount(2);
        const metas = await page.locator('.stw-chip-meta').allInnerTexts();
        expect(metas[0]).toContain('GL 台账');
        expect(metas[0]).toContain('3 页');
        // 认不出的必须写「认不出是什么」,不许回落成「其他」这类假装认过的词。
        expect(metas[1]).toContain('认不出是什么');
        expect(metas.join('|')).not.toContain('undefined');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '02-chips-ready-zh.png'),
            fullPage: true,
        });

        await page.locator('.stw-att-chip').first().locator('.stw-chip-x').click();
        await expect(page.locator('.stw-att-chip')).toHaveCount(1);
    });

    test('选文件的当下就拒:超限/坏格式/空文件不发一次请求', async ({ page }) => {
        const h = await boot(page);
        await dragFiles(page, [
            { name: 'big.pdf', body: 'z'.repeat(21 * 1024 * 1024), type: 'application/pdf' },
            // 坏格式拿 .rar(收料口明说只吃 zip)。这里原来放的是 a.zip —— 那条断言把
            // 「zip 传不上去」当成了预期,把真 bug 焊成了绿灯。
            { name: 'a.rar', body: 'zz', type: 'application/x-rar' },
            { name: 'empty.pdf', body: '', type: 'application/pdf' },
        ]);
        await dropNow(page);

        await expect(page.locator('.stw-att-chip.rejected')).toHaveCount(3);
        // 三条各说各的原因 —— 统一一句「上传失败」不告诉人是哪道上限卡住了。
        const errs = await page.locator('.stw-chip-err').allInnerTexts();
        expect(new Set(errs).size).toBe(3);
        // 反证闸:印出来的必须是人话,不是 stw_att_err_* 原始 key(首版三条全是 key,
        // 单测只比了「六个 key 互不相同」所以全绿 —— 断言得盯真渲染出来的字)。
        expect(errs.join('|')).not.toMatch(/\bstw_[a-z0-9_]+/);
        expect(h.uploads.length).toBe(0);
        // 被拒的不算数:一个字没打时送不出去。
        await expect(page.locator('[data-action="stw-send"]')).toBeEnabled();
        await page.locator('[data-action="stw-send"]').click();
        expect(h.posts.length).toBe(0);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '03-chips-rejected-zh.png'),
            fullPage: true,
        });
    });

    test('zip 与 HEIC 是运输皮不是坏格式:真传上去,不在选文件那一刻被灰掉', async ({ page }) => {
        const h = await boot(page);
        await dragFiles(page, [
            { name: 'มิ.ย.69.zip', body: 'PK', type: 'application/zip' },
            { name: 'IMG_2647.heic', body: 'x', type: 'image/heic' },
        ]);
        await dropNow(page);

        await expect(page.locator('.stw-att-chip.rejected')).toHaveCount(0);
        await expect(page.locator('.stw-att-chip.ready')).toHaveCount(2);
        expect(h.uploads.length).toBe(2); // 拆壳在后端,前端不许自己判它「吃不了」
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '03b-zip-heic-accepted-zh.png'),
            fullPage: true,
        });
    });

    test('还在传就不许送:送出按钮 disabled,传完才放行', async ({ page }) => {
        const h = await boot(page);
        let release;
        const gate = new Promise((r) => {
            release = r;
        });
        // 压住上传不让它落地。必须在 boot() 之后注册:Playwright 后注册的路由优先,
        // 先注册会被 boot 里那条 **/api/ai/steward/** 盖掉,上传瞬间就成功了 ——
        // 那样这条用例会在 uploading 的一瞬间擦边过,验的其实是竞态不是闸。
        await page.route('**/api/ai/steward/sessions/*/attachments', async (r) => {
            await gate;
            return json(r, {
                attachments: [attachment('u1', 'gl.pdf', 'gl_ledger')],
                count: 1,
            });
        });
        await dragFiles(page, [{ name: 'gl.pdf', body: 'x', type: 'application/pdf' }]);
        await dropNow(page);

        await expect(page.locator('.stw-att-chip.uploading')).toHaveCount(1);
        await expect(page.locator('.stw-att-chip .st-bar')).toBeVisible();
        await expect(page.locator('[data-action="stw-send"]')).toBeDisabled();
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '04-chip-uploading-zh.png'),
            fullPage: true,
        });

        release();
        await expect(page.locator('.stw-att-chip.ready')).toHaveCount(1);
        await expect(page.locator('[data-action="stw-send"]')).toBeEnabled();
        expect(h.posts.length).toBe(0);
    });

    test('传失败能重传 · 加密 PDF 就地问密码', async ({ page }) => {
        const h = await boot(page, {
            uploadStatus: 422,
            uploadDetail: {
                code: 'workorder.intake.pdf_password_required',
                message: {
                    zh: '这份 PDF 有密码,填了才解得开。',
                    th: 'ไฟล์นี้มีรหัสผ่าน',
                    en: '',
                    ja: '',
                },
                filename: 'kbank.pdf',
            },
        });
        await dragFiles(page, [{ name: 'kbank.pdf', body: 'x', type: 'application/pdf' }]);
        await dropNow(page);

        await expect(page.locator('.stw-att-chip.failed')).toHaveCount(1);
        // 422 的四语 message 后端已给,直接印那一份,不再过前端 i18n。
        await expect(page.locator('.stw-chip-err')).toContainText('这份 PDF 有密码');
        await expect(page.locator('#stwAttPw')).toBeVisible();
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '05-password-row-zh.png'),
            fullPage: true,
        });

        const before = h.uploads.length;
        await page.locator('#stwAttPw').fill('1234');
        await page.locator('[data-action="stw-att-pw-go"]').click();
        await expect.poll(() => h.uploads.length).toBeGreaterThan(before);
        // 重传入口也在(失败的件不静默消失)。
        await expect(page.locator('[data-action="stw-att-retry"]')).toBeVisible();
    });

    test('密码填错不是死胡同:密码框再长出来 · 重传不带旧密码', async ({ page }) => {
        await boot(page);
        const bodies = [];
        // 第一次要密码,之后一律「密码不对」——会计填错一次就到这个状态。
        await page.route('**/api/ai/steward/sessions/*/attachments', (r) => {
            bodies.push(r.request().postData() || '');
            const first = bodies.length === 1;
            return r.fulfill({
                status: 422,
                contentType: 'application/json',
                body: JSON.stringify({
                    detail: {
                        code: first
                            ? 'workorder.intake.pdf_password_required'
                            : 'workorder.intake.pdf_password_wrong',
                        message: {
                            zh: first
                                ? '这份 PDF 有密码,填了才解得开。'
                                : 'PDF 密码不正确,请重试。',
                            th: first ? 'ไฟล์นี้มีรหัสผ่าน' : 'รหัสผ่าน PDF ไม่ถูกต้อง',
                            en: '',
                            ja: '',
                        },
                        filename: 'kbank.pdf',
                    },
                }),
            });
        });
        await dragFiles(page, [{ name: 'kbank.pdf', body: 'x', type: 'application/pdf' }]);
        await dropNow(page);
        await expect(page.locator('#stwAttPw')).toBeVisible();

        await page.locator('#stwAttPw').fill('0000');
        await page.locator('[data-action="stw-att-pw-go"]').click();
        await expect.poll(() => bodies.length).toBe(2);
        expect(bodies[1]).toContain('0000');

        // 这里是原来的死胡同:密码框不再出现,重传永远带着那个错密码。
        await expect(page.locator('.stw-chip-err')).toContainText('密码不正确');
        await expect(page.locator('#stwAttPw')).toBeVisible();
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '05b-password-wrong-zh.png'),
            fullPage: true,
        });

        await page.locator('#stwAttPw').fill('5678');
        await page.locator('[data-action="stw-att-pw-go"]').click();
        await expect.poll(() => bodies.length).toBe(3);
        expect(bodies[2]).toContain('5678');
        expect(bodies[2]).not.toContain('0000');

        // 直接点「重传」也不许再拿那个错密码去撞同一个 422。
        await page.locator('[data-action="stw-att-retry"]').click();
        await expect.poll(() => bodies.length).toBe(4);
        expect(bodies[3]).not.toContain('name="password"');
    });

    test('纯文件送出 → 气泡下有只读原件行 · 回执卡按钮把参数原样带回', async ({ page }) => {
        const h = await boot(page);
        await dragFiles(page, [
            { name: 'gl.pdf', body: 'x', type: 'application/pdf' },
            { name: 'mystery.pdf', body: 'y', type: 'application/pdf' },
        ]);
        await dropNow(page);
        await expect(page.locator('.stw-att-chip.ready')).toHaveCount(2);

        // 一个字不打,直接送出(万能口的核心手势)。
        await page.locator('[data-action="stw-send"]').click();
        await expect(page.locator('.stw-msg.agent .stw-bubble')).toContainText('想让我做哪一样');
        expect(h.posts[0].text).toBe('');
        expect(h.posts[0].attachment_ids).toEqual(['u1', 'u2']);
        // 送出后附件盘清空(件搬进气泡了,不该在盘里留一份)。
        await expect(page.locator('.stw-att-chip')).toHaveCount(0);

        // 用户气泡下的只读原件行:带鉴权头下载的按钮,不是会 401 的裸 <a>。
        const pills = page.locator('.stw-msg.me .stw-file-pill');
        await expect(pills).toHaveCount(2);
        await expect(pills.first()).toContainText('gl.pdf');
        await expect(pills.nth(1)).toContainText('认不出是什么');
        expect(await page.locator('.stw-msg.me a').count()).toBe(0);

        // 左窗回执卡:表格是渲好的人话,三步不许把「等你选」画成「在跑」。
        await page.waitForSelector('#stwLeft .stw-task', { state: 'visible', timeout: 15000 });
        const cells = await page.locator('#stwLeft .stw-table td').allInnerTexts();
        expect(cells.join('|')).not.toContain('[object Object]');
        expect(cells).toContain('GL 台账');
        await expect(page.locator('#stwLeft .stw-step:nth-child(3) .st-badge')).toHaveClass(
            /st-off/
        );

        // 闭集动作按钮:label 直接当文字,点一下把 tool/ids/confirm_spend 原样回传。
        const act = page.locator('#stwLeft .stw-act');
        await expect(act).toHaveCount(1);
        await expect(act).toContainText('转成 Excel · gl.pdf');
        await expect(act).toBeEnabled();
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '06-receipt-card-zh.png'),
            fullPage: true,
        });

        await act.click();
        await expect.poll(() => h.posts.length).toBe(2);
        expect(h.posts[1].action).toEqual({
            tool: 'file_convert',
            attachment_ids: ['u1'],
            confirm_spend: false,
        });
    });

    test('后端没给限额 → 整块不给附件口(不拿自己编的数字拒文件)', async ({ page }) => {
        await boot(page, { noLimits: true });
        expect(await page.locator('.stw-clip').count()).toBe(0);
        expect(await page.locator('#stwAttFile').count()).toBe(0);
        // 纯文字仍然能用(降级不是把整页弄死)。
        await expect(page.locator('#stwInput')).toBeEnabled();
        await expect(page.locator('[data-action="stw-send"]')).toBeEnabled();
    });

    test('手机端(390×844):回形针与动作按钮触控目标 ≥44px', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await boot(page);
        // 两件事分开验:①「设计上就是 44」看 CSS 意图,②「实际没被挤扁」看画出来的框。
        // 画出来的框要取整再比 —— headless 下 flex 行的 cross size 会落在分数上(实测量到
        // 43.999969…),拿浮点直接比 44 会随机红,那是断言精度问题,不是触控目标真不够大。
        const clipMinH = await page
            .locator('.stw-clip')
            .evaluate((el) => getComputedStyle(el).minHeight);
        expect(clipMinH).toBe('44px');
        const clip = await page.locator('.stw-clip').boundingBox();
        expect(Math.round(clip.width)).toBeGreaterThanOrEqual(44);
        expect(Math.round(clip.height)).toBeGreaterThanOrEqual(44);

        await dragFiles(page, [{ name: 'gl.pdf', body: 'x', type: 'application/pdf' }]);
        await dropNow(page);
        await expect(page.locator('.stw-att-chip.ready')).toHaveCount(1);
        await page.locator('[data-action="stw-send"]').click();
        await page.waitForSelector('#stwLeft .stw-act', { state: 'visible', timeout: 15000 });
        const act = await page.locator('#stwLeft .stw-act').boundingBox();
        expect(act.height).toBeGreaterThanOrEqual(44);
        // 页面本体永不横滚。
        const overflow = await page.evaluate(
            () => document.documentElement.scrollWidth - document.documentElement.clientWidth
        );
        expect(overflow).toBeLessThanOrEqual(1);
        // 输入口在流里排在对话之后(composer 是 sticky,fullPage 截图会把它钉在视口底
        // 拼进画面中段 —— 那是截图的拼接位,不是真实排序,所以顺序看 DOM 不看图)。
        const order = await page.evaluate(() =>
            [...document.querySelector('#stwRight').children].map((e) => e.className)
        );
        expect(order[order.length - 1]).toContain('stw-composer');
        // 视口截图(非 fullPage)= 手机上真正看到的那一屏。
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '07-mobile-zh.png') });
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '07b-mobile-full-zh.png'),
            fullPage: true,
        });
    });

    test('泰文:附件盘与回执卡按钮不露原始 key', async ({ page }) => {
        await page.addInitScript(() => window.localStorage.setItem('mrpilot_lang', 'th'));
        await boot(page);
        await page.evaluate(() => window.atSetLang && window.atSetLang('th'));
        await dragFiles(page, [{ name: 'gl.pdf', body: 'x', type: 'application/pdf' }]);
        await dropNow(page);
        await expect(page.locator('.stw-att-chip.ready')).toHaveCount(1);
        const tray = await page.locator('.stw-att-tray').innerText();
        expect(tray).not.toMatch(/\bstw_[a-z0-9_]+/);
        const note = await page.locator('.stw-composer-note').innerText();
        expect(note).not.toMatch(/\bstw_[a-z0-9_]+/);
        // 回形针挤掉了输入行的宽度:送出按钮不许被压到把字裁掉(泰文比中文长,先在这儿炸)。
        const send = await page
            .locator('.stw-composer [data-action="stw-send"]')
            .evaluate((el) => ({ w: el.clientWidth, need: el.scrollWidth }));
        expect(send.w).toBeGreaterThanOrEqual(send.need);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '08-chips-ready-th.png'),
            fullPage: true,
        });
    });
});
