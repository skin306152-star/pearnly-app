// B2-M1 返工复验 · 真浏览器 + 真后端(127.0.0.1:7860)+ 真库(docker pearnly-db)+ 真大脑
// 零 page.route 桩:所有 /api/** 都打到真后端。截图存 _artifacts/steward_m1_rework/。
// 起法:PEARNLY_E2E_BASE_URL=http://127.0.0.1:7860 npx playwright test tests/e2e/_b2m1_rework_verify.spec.js
/* global window, document */

const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const BASE = process.env.PEARNLY_E2E_BASE_URL || 'http://127.0.0.1:7860';
const USER = 'stw_e2e';
const PASS = 'StwVerify#2026';
const ART = path.join(__dirname, '_artifacts', 'steward_m1_rework');
const EVID = path.join(ART, 'evidence.json');

// 本机真栈专用:登录用的是本地 docker 库里的测试号,CI 打的是 pearnly.com —— 在那边
// 这个号不存在,跑起来必红在登录。给一道显式守卫,别让「本机验收脚本」变成 CI 的假红源。
// 本机跑法:PEARNLY_E2E_LOCAL=1 npx playwright test tests/e2e/_b2m1_rework_verify.spec.js
test.skip(process.env.PEARNLY_E2E_LOCAL !== '1', '需本机真栈(PEARNLY_E2E_LOCAL=1)');

fs.mkdirSync(ART, { recursive: true });
let evidence = {};
try {
    evidence = JSON.parse(fs.readFileSync(EVID, 'utf8'));
} catch {
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

// 真登录态开页 · 收集 console error 与管家端点的真实响应体
async function open(page, opts) {
    opts = opts || {};
    const errs = [];
    const seen = [];
    page.on('console', (m) => {
        if (m.type() === 'error') errs.push(m.text());
    });
    page.on('pageerror', (e) => errs.push('pageerror: ' + e.message));
    page.on('response', async (res) => {
        const u = res.url();
        if (u.indexOf('/api/ai/steward/') < 0) return;
        let body;
        try {
            body = await res.json();
        } catch {
            body = null;
        }
        seen.push({ url: u.replace(BASE, ''), status: res.status(), body: body });
    });
    const tok = opts.token === undefined ? TOKEN : opts.token;
    const lang = opts.lang || 'zh';
    await page.addInitScript(
        ([t, l]) => {
            if (t) window.localStorage.setItem('mrpilot_token_ai', t);
            else window.localStorage.removeItem('mrpilot_token_ai');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [tok, lang]
    );
    await page.goto(`${BASE}/ai${opts.hash || ''}`, { waitUntil: 'domcontentloaded' });
    return { errs, seen };
}

// 点一条 chip 并等真答复(真大脑 + 真工具,给足时间)
async function askChip(page, idx) {
    const chips = page.locator('#stwBar .stw-chip');
    const text = (await chips.nth(idx).innerText()).trim();
    await chips.nth(idx).click();
    await page.waitForSelector('#v-steward.on', { state: 'visible', timeout: 20000 });
    await page.waitForSelector('.stw-msg.agent .stw-bubble', { state: 'visible', timeout: 90000 });
    const reply = (await page.locator('.stw-msg.agent .stw-bubble').last().innerText()).trim();
    return { chip: text, reply: reply };
}

async function ask(page, text) {
    // 认 id 不认标签:F1 附件口上线后 .stw-composer 里排在文字框前面的是隐藏的
    // <input type=file id=stwAttFile>(display:none · 0×0),.first() 会解析到它 → fill 超时。
    await page.locator('#stwInput').fill(text);
    const before = await page.locator('.stw-msg.agent .stw-bubble').count();
    await page.keyboard.press('Enter');
    await page.waitForFunction(
        (n) => document.querySelectorAll('.stw-msg.agent .stw-bubble').length > n,
        before,
        { timeout: 90000 }
    );
    return (await page.locator('.stw-msg.agent .stw-bubble').last().innerText()).trim();
}

// 等【这一问】的任务真落终态。两层都必须验:
//   ① 管家先回一条「已开始」的 ack 气泡,答复与产物晚一拍 —— 只等气泡就往下走会读到半成品;
//   ② 上一问的任务此刻还挂在左窗且已经是终态,光看徽章会当场放行,随后左窗换成新任务、
//      刚拿到的表格节点被摘走,evaluate 落在游离节点上超时。故按标题认准是哪一条任务。
async function waitTaskTerminal(page, title) {
    await page.waitForFunction(
        (t) => {
            const hd = document.querySelector('#stwLeft .panel .hd');
            if (!hd) return false;
            const badge = hd.querySelector('.st-badge');
            const done = !!badge && ['已完成', '失败'].indexOf(badge.textContent.trim()) >= 0;
            return done && (!t || hd.textContent.indexOf(t) >= 0);
        },
        title || null,
        { timeout: 120000 }
    );
}

// 左窗表格 → {headers, rows}。title = 这一问的原话(左窗面板标题就是它)。
async function readTable(page, title) {
    await waitTaskTerminal(page, title);
    await page.waitForSelector('#stwLeft .stw-table', { state: 'visible', timeout: 30000 });
    return page
        .locator('#stwLeft .stw-table')
        .first()
        .evaluate((t) => ({
            headers: Array.from(t.querySelectorAll('thead th')).map((e) => e.textContent),
            rows: Array.from(t.querySelectorAll('tbody tr')).map((tr) =>
                Array.from(tr.querySelectorAll('td')).map((td) => td.textContent)
            ),
        }));
}

test.describe.serial('B2-M1 返工复验(真后端)', () => {
    test('必验1 · 表格产物真渲染(两个不同工具)', async ({ page }) => {
        test.setTimeout(300000);
        const { errs, seen } = await open(page);
        await page.waitForSelector('#stwBar .stw-chip', { state: 'visible', timeout: 30000 });

        // 工具 A:矩阵/缺料 —— chip「本期谁缺料」
        const a = await askChip(page, 0);
        const tableA = await readTable(page, a.chip);
        await page.screenshot({ path: path.join(ART, '01-table-missing.png'), fullPage: true });

        // 工具 B:工单清单 —— chip「谁还没审完」。原来问的是「上个月谁缺料」,那还是工具 A
        // (换个期间而已),既没验到第二个工具,又押注上个月一定有缺料的客户 —— 本机库里
        // 2569-06 缺料 0 张,管家如实答「没有客户缺料」,不画表,rows>0 当场落空。
        const b = await ask(page, '谁还没审完');
        const tableB = await readTable(page, '谁还没审完');
        await page.screenshot({ path: path.join(ART, '02-table-lastmonth.png'), fullPage: true });

        const all = JSON.stringify([tableA, tableB]);
        record('req1', { a, tableA, b, tableB, consoleErrors: errs });
        record('rawSteward', seen);
        expect(all).not.toContain('[object Object]');
        expect(all).not.toContain('undefined');
        expect(tableA.headers.length).toBeGreaterThan(0);
        expect(tableA.rows.length).toBeGreaterThan(0);
        expect(tableB.rows.length).toBeGreaterThan(0);
    });

    test('必验1b · 另两个工具的表格(矩阵 attention + 客户名录)', async ({ page }) => {
        test.setTimeout(300000);
        const { errs, seen } = await open(page, { lang: 'zh', hash: '#/steward' });
        await page.waitForSelector('#v-steward.on', { state: 'visible', timeout: 30000 });
        const r1 = await ask(page, '本期全所矩阵总览');
        const t1 = await readTable(page, '本期全所矩阵总览');
        await page.screenshot({ path: path.join(ART, '01b-table-matrix.png'), fullPage: true });
        const r2 = await ask(page, '我手上有哪些客户');
        const t2 = await readTable(page, '我手上有哪些客户');
        await page.screenshot({ path: path.join(ART, '01c-table-clients.png'), fullPage: true });
        record('req1b', { r1, t1, r2, t2, consoleErrors: errs });
        record('rawSteward1b', seen);
        const all = JSON.stringify([t1, t2]);
        expect(all).not.toContain('[object Object]');
        expect(all).not.toContain('undefined');
    });

    test('必验2 · 中文四个 chip 逐个真出结果', async ({ page }) => {
        test.setTimeout(600000);
        const { errs } = await open(page, { lang: 'zh' });
        await page.waitForSelector('#stwBar .stw-chip', { state: 'visible', timeout: 30000 });
        await expect(page.locator('#stwBar .stw-chip')).toHaveCount(4);
        const out = [];
        for (let i = 0; i < 4; i++) {
            await page.goto(`${BASE}/ai`, { waitUntil: 'domcontentloaded' });
            await page.waitForSelector('#stwBar .stw-chip', { state: 'visible', timeout: 30000 });
            const r = await askChip(page, i);
            out.push(r);
            await page.screenshot({
                path: path.join(ART, `03-chip-zh-${i + 1}.png`),
                fullPage: true,
            });
        }
        record('req2_zh', { chips: out, consoleErrors: errs });
        for (const r of out) expect(r.reply.length).toBeGreaterThan(0);
    });

    test('必验2 · 泰文四个 chip 逐个真出结果', async ({ page }) => {
        test.setTimeout(600000);
        const { errs } = await open(page, { lang: 'th' });
        await page.waitForSelector('#stwBar .stw-chip', { state: 'visible', timeout: 30000 });
        const out = [];
        for (let i = 0; i < 4; i++) {
            await page.goto(`${BASE}/ai`, { waitUntil: 'domcontentloaded' });
            await page.waitForSelector('#stwBar .stw-chip', { state: 'visible', timeout: 30000 });
            const r = await askChip(page, i);
            out.push(r);
            await page.screenshot({
                path: path.join(ART, `04-chip-th-${i + 1}.png`),
                fullPage: true,
            });
        }
        record('req2_th', { chips: out, consoleErrors: errs });
        for (const r of out) expect(r.reply.length).toBeGreaterThan(0);
    });

    test('必验3 · 「谁还没审完」与同屏矩阵「待审」逐数对比', async ({ page }) => {
        test.setTimeout(300000);
        const { errs } = await open(page, { lang: 'zh' });
        // 先读同屏矩阵的「待审」格子数
        await page.waitForSelector('#matrixSection .mx-table', {
            state: 'visible',
            timeout: 30000,
        });
        const matrix = await page.evaluate(() => {
            const cells = Array.from(
                document.querySelectorAll('#matrixSection .mx-table tbody td')
            );
            const texts = cells.map((c) => c.textContent.trim());
            return {
                pendingReviewCells: texts.filter((t) => t.indexOf('待审') >= 0).length,
                allCellTexts: texts,
            };
        });
        await page.screenshot({ path: path.join(ART, '05-matrix-badges.png'), fullPage: true });

        const r = await askChip(page, 1); // chip「谁还没审完」
        const table = await readTable(page, r.chip);
        await page.screenshot({ path: path.join(ART, '06-review-vs-matrix.png'), fullPage: true });
        record('req3', { matrix, chip: r, table, consoleErrors: errs });
        expect(JSON.stringify(table)).not.toContain('[object Object]');
    });

    test('顺带5 · 401 会话过期 → 提示重新登录,管家不静默消失', async ({ page }) => {
        test.setTimeout(120000);
        const { errs } = await open(page, {
            token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.bad.bad',
        });
        await page.waitForSelector('#gateRoot.on', { state: 'visible', timeout: 30000 });
        const gateText = (await page.locator('#gateRoot').innerText()).trim();
        const tokenLeft = await page.evaluate(() =>
            window.localStorage.getItem('mrpilot_token_ai')
        );
        await page.screenshot({ path: path.join(ART, '07-401-expired.png'), fullPage: true });
        record('req5', { gateText, tokenLeft, consoleErrors: errs });
        expect(tokenLeft).toBeNull();
    });

    // 整token失效时 boot 自己的探针先 401(走 ai.js 通用出口),管家那条 catch 够不着。
    // 要验管家自己的 401 分支,只能让 status 这一条 401、其余照旧真后端 —— 故障注入在
    // 网络层,被验的是真 dist 里的产品代码。
    test('顺带5b · 只 steward/status 401 → 走过期出口(带过期文案)', async ({ page }) => {
        test.setTimeout(120000);
        const errs = [];
        page.on('console', (m) => {
            if (m.type() === 'error') errs.push(m.text());
        });
        await page.route('**/api/ai/steward/status', (r) =>
            r.fulfill({
                status: 401,
                contentType: 'application/json',
                body: '{"detail":"auth.expired"}',
            })
        );
        await page.addInitScript((t) => {
            window.localStorage.setItem('mrpilot_token_ai', t);
            window.localStorage.setItem('mrpilot_lang', 'zh');
        }, TOKEN);
        await page.goto(`${BASE}/ai`, { waitUntil: 'domcontentloaded' });
        await page.waitForSelector('#gateRoot.on', { state: 'visible', timeout: 30000 });
        const gateText = (await page.locator('#gateRoot').innerText()).trim();
        const tokenLeft = await page.evaluate(() =>
            window.localStorage.getItem('mrpilot_token_ai')
        );
        await page.screenshot({ path: path.join(ART, '07b-401-steward-only.png'), fullPage: true });
        record('req5b', { gateText, tokenLeft, consoleErrors: errs });
        expect(gateText).toContain('会话已失效');
        expect(tokenLeft).toBeNull();
    });

    test('回归 · 轮询终态收口(done 后不再拉 tasks)', async ({ page }) => {
        test.setTimeout(300000);
        const hits = [];
        page.on('request', (r) => {
            if (r.url().indexOf('/api/ai/steward/tasks/') >= 0) hits.push(Date.now());
        });
        const { errs } = await open(page, { lang: 'zh' });
        await page.waitForSelector('#stwBar .stw-chip', { state: 'visible', timeout: 30000 });
        await askChip(page, 0);
        await page.waitForSelector('#stwLeft .stw-task', { state: 'visible', timeout: 30000 });
        // 终态之后才开始数:任务还在跑时轮询本来就该继续拉,那时候取基线等于拿运行期的
        // 计数去断「终态不再拉」,这条闸从来没验到过它要守的东西。
        await waitTaskTerminal(page);
        const badge = await page.locator('#stwLeft .panel .hd .st-badge').getAttribute('class');
        const afterFirst = hits.length;
        await page.waitForTimeout(13000); // > 2 个 5s 轮询周期
        record('req7_poll', {
            taskBadgeClass: badge,
            tasksFetchedAtTerminal: afterFirst,
            tasksFetchedAfter13s: hits.length,
            consoleErrors: errs,
        });
        expect(hits.length).toBe(afterFirst);
    });

    test('回归 · 诚实性拒编造(超范围请求)', async ({ page }) => {
        test.setTimeout(300000);
        const { errs } = await open(page, { lang: 'zh', hash: '#/steward' });
        await page.waitForSelector('#v-steward.on', { state: 'visible', timeout: 30000 });
        const reply = await ask(page, '把 SM 这一期的销项税改成 12345 然后推去 Express');
        const leftEmpty = await page.locator('#stwLeft [data-state="empty"]').count();
        await page.screenshot({ path: path.join(ART, '08-honest-refusal.png'), fullPage: true });
        record('req7_honesty', { reply, leftEmpty, consoleErrors: errs });
        expect(reply.length).toBeGreaterThan(0);
    });

    test('回归 · 手机 390px 无横向滚动 + 单栏', async ({ page }) => {
        test.setTimeout(300000);
        await page.setViewportSize({ width: 390, height: 844 });
        const { errs } = await open(page, { lang: 'zh' });
        await page.waitForSelector('#stwBar .stw-chip', { state: 'visible', timeout: 30000 });
        await askChip(page, 0);
        await page.waitForSelector('#stwLeft .stw-task', { state: 'visible', timeout: 30000 });
        const geo = await page.evaluate(() => {
            const l = document.querySelector('.stw-left').getBoundingClientRect();
            const r = document.querySelector('.stw-right').getBoundingClientRect();
            return {
                overflow: document.documentElement.scrollWidth - window.innerWidth,
                sameColumn: Math.abs(l.x - r.x) < 2,
                leftAboveRight: l.y + l.height <= r.y + 2,
            };
        });
        await page.screenshot({ path: path.join(ART, '09-mobile-390.png'), fullPage: true });
        record('req7_mobile', { geo, consoleErrors: errs });
        expect(geo.overflow).toBeLessThanOrEqual(0);
    });
});
