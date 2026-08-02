// /ai 失败态出路 · 本地真浏览器验收(跑 static/dist 真构建产物)
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**
// (同 _b5_billing_local.spec.js 先例)。被断言的文字/可见性全来自真产物,stub 只兜后端响应。
//
// 验收两条缺口:
//  ① 点「开当期工单」失败此前页面零反应 —— 现在按钮回可点 + 卡里说清哪一步/为什么/下一步;
//  ② 收料上传失败此前只有「N 个文件失败 · 重传」—— 现在先说原因;余额不足(402)另给
//     「去充值」直达设置页计费区(重传一百次也不会好的失败不能只给重传)。
// 截图存 tests/e2e/_artifacts/fail_ways_out/。
//
// 402 的落点:add_materials 已接余额闸(routes/workorder_routes.py → ocr_balance.batch_denial,
// PEARNLY_WORKORDER_BILLING 开时余额不足整批拒),所以「收料 402 → 去充值」验的是真出路。
// create_order 那两条仍是契约验证:开单本身永远不计费,生产里不会从开单收到 402。
// 本 spec 用 stub 兜响应验前端渲染;后端真会返 402 由 tests/unit/test_workorder_billing.py 锁。
//
// 起法:npx playwright test tests/e2e/_fail_ways_out_local.spec.js
/* global window, document */

const { test, expect } = require('@playwright/test');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const ROOT = path.resolve(__dirname, '..', '..');
const PORT = 8993;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'fail_ways_out');

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

const CLIENT = { id: 1, name: 'บริษัท ทดสอบ', tax_id: '0105551234567' };

// 「去充值」深链的落点是设置页计费区。要验它真滚到了,视口必须是「不滚就看不见」的:
// 1280×800 下整页 fit,任何位置断言都恒真(D1 假绿的根因)。手机是这条出路的主场景。
const MOBILE = { width: 390, height: 844 };

// 老板视角余额(员工视角无 balance_thb → 没有充值按钮,验不了落点)。
const OWNER_CREDITS = {
    has_tenant: true,
    is_owner: true,
    is_billing_exempt: false,
    balance_thb: 1250.5,
    pages_this_month: 64,
    current_rate: 1.5,
};
const TOPUP_HISTORY = [1, 2, 3, 4, 5, 6].map((i) => ({
    created_at: `2026-0${i}-11T03:00:00Z`,
    amount_thb: 500,
    status: 'approved',
}));
// 计费区数据故意慢:挂载那一刻它还是骨架、整页撑不出滚动条,scrollIntoView 会被 clamp 成
// no-op(ai.js restoreScrollAfterPaint 早写过这个坑)。秒回的 stub 根本测不出来。
const BILLING_DELAY_MS = 600;

// createOrder / addMaterials 的失败模式由 opts 注入:{status, code} 或 abort:true(网络断)。
async function boot(page, opts = {}) {
    await page.route('**/api/**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{}' })
    );
    await page.route('**/api/me**', (r) =>
        r.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({ username: 'skin', email: 's@e.com', tenant_name: 'skin' }),
        })
    );
    // 后注册者优先:这两条必须排在 **/api/me** 之后,否则 /api/me/credits 被它吃掉。
    await page.route('**/api/me/credits', async (r) => {
        await new Promise((s) => setTimeout(s, BILLING_DELAY_MS));
        await r.fulfill({ contentType: 'application/json', body: JSON.stringify(OWNER_CREDITS) });
    });
    await page.route('**/api/credits/topup/history', (r) =>
        r.fulfill({ contentType: 'application/json', body: JSON.stringify(TOPUP_HISTORY) })
    );
    await page.route('**/api/workspace/clients/**', (r) =>
        r.fulfill({ contentType: 'application/json', body: JSON.stringify(CLIENT) })
    );
    // 零工单:wo / intake 两个 tab 都落「开当期工单」空态。
    await page.route('**/api/workorder/orders?**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{"orders":[]}' })
    );
    const fail = (route, mode) => {
        if (mode.abort) return route.abort('failed');
        return route.fulfill({
            status: mode.status,
            contentType: 'application/json',
            body: JSON.stringify({ detail: mode.code ? { code: mode.code } : 'generic' }),
        });
    };
    if (opts.createOrder) {
        await page.route(
            (u) => u.pathname === '/api/workorder/orders',
            (r) => (r.request().method() === 'POST' ? fail(r, opts.createOrder) : r.fallback())
        );
    }
    if (opts.materials) {
        await page.route('**/materials', (r) => fail(r, opts.materials));
    }
    await page.addInitScript((lang) => {
        window.localStorage.setItem('mrpilot_token_ai', 'tok-failways');
        window.localStorage.setItem('mrpilot_lang', lang);
    }, opts.lang || 'zh');
}

// 收料区选一份料再点上传。文件框是 ai-intake.js 运行时建的隐藏 #ikFileInput,
// 直接 setInputFiles 触发它自己的 change(点「选择文件」会开系统对话框,headless 里点不了)。
async function pickAndUpload(page) {
    const input = page.locator('#ikFileInput');
    await expect(input).toBeAttached({ timeout: 15000 });
    await input.setInputFiles({
        name: 'bill.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('%PDF-1.4 test'),
    });
    await page.locator('[data-action="ik-upload"]').click();
}

const INTAKE_ORDER =
    '{"orders":[{"id":"wo-1","period":"2569-07","intent":"monthly_vat","status":"intake","current_step":"intake"}]}';

// 开单成功(默认 stub 200)→ 进收料区 → 选一份料 → 上传撞 materials 指定的失败,
// 停在失败批横幅上。上传失败态的每条用例都得先走这一趟,差别只在撞哪个码。
async function openUploadFailureCard(page, materials, lang) {
    await boot(page, { lang: lang, materials: materials });
    await page.goto(`${BASE}/static/dist/ai.html#/client/1/intake`);
    const openBtn = page.locator('[data-action="intake-open-order"]');
    await expect(openBtn).toBeVisible({ timeout: 15000 });
    await page.unroute('**/api/workorder/orders?**');
    await page.route('**/api/workorder/orders?**', (r) =>
        r.fulfill({ contentType: 'application/json', body: INTAKE_ORDER })
    );
    await openBtn.click();
    await pickAndUpload(page);
    return page.locator('.needs-card');
}

function open402Card(page, lang) {
    return openUploadFailureCard(page, { status: 402, code: 'insufficient_balance' }, lang);
}

test.describe('/ai 失败态出路(本地 stub · 真构建产物)', () => {
    test('开当期工单:服务端 500 → 按钮回可点 + 说清哪一步为什么', async ({ page }) => {
        await boot(page, { createOrder: { status: 500 } });
        await page.goto(`${BASE}/static/dist/ai.html#/client/1/wo`);
        const btn = page.locator('[data-action="wo-open-first"]');
        await expect(btn).toBeVisible({ timeout: 15000 });
        await btn.click();

        const note = page.locator('.order-open-empty [role="alert"]');
        await expect(note).toBeVisible();
        await expect(note).toContainText('开单没成功');
        await expect(note).toContainText('服务器出错了');
        await expect(btn).toBeEnabled();
        await expect(btn).toHaveText('按所选账期开工单'); // 不再卡在「开单中…」
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '01-open-order-500.png'),
            fullPage: true,
        });
    });

    // 开单成功、刷新列表那一跳挂了:徽章此前照样打「开单没成功」——单其实已经躺在库里,
    // 用户会以为白点了、跑去别处再开一次。徽章必须点对步。
    test('开当期工单:单已开出但刷列表 500 → 说的是列表没刷新,不是开单没成功', async ({ page }) => {
        await boot(page);
        await page.goto(`${BASE}/static/dist/ai.html#/client/1/wo`);
        const btn = page.locator('[data-action="wo-open-first"]');
        await expect(btn).toBeVisible({ timeout: 15000 });
        // 开单(POST)照旧成功,只截停之后那一跳列表刷新(GET)。
        await page.unroute('**/api/workorder/orders?**');
        await page.route('**/api/workorder/orders?**', (r) =>
            r.fulfill({ status: 500, contentType: 'application/json', body: '{"detail":"boom"}' })
        );
        await btn.click();

        const note = page.locator('.order-open-empty [role="alert"]');
        await expect(note).toBeVisible({ timeout: 15000 });
        await expect(note.locator('.st-badge.st-err')).toHaveText('列表没刷新出来');
        await expect(note).toContainText('工单已经开出来了');
        await expect(note).not.toContainText('开单没成功');
        // 覆盖原因时不摆按钮:出路(再点一次)写在文案里,再挂一个按 500 算出来的按钮会指错地方。
        await expect(page.locator('.order-open-empty .needs-paths')).toHaveCount(0);
        await expect(btn).toBeEnabled();
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '07-open-order-created-but-stale.png'),
            fullPage: true,
        });
    });

    test('开当期工单:网络断 → 说的是网络不是服务器', async ({ page }) => {
        await boot(page, { createOrder: { abort: true } });
        await page.goto(`${BASE}/static/dist/ai.html#/client/1/wo`);
        const btn = page.locator('[data-action="wo-open-first"]');
        await expect(btn).toBeVisible({ timeout: 15000 });
        await btn.click();
        const note = page.locator('.order-open-empty [role="alert"]');
        await expect(note).toContainText('请求没发出去');
        await expect(btn).toBeEnabled();
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '02-open-order-network.png'),
            fullPage: true,
        });
    });

    test('开当期工单:余额不足 402 → 卡里直接给「去充值」', async ({ page }) => {
        await boot(page, { createOrder: { status: 402, code: 'insufficient_balance' } });
        await page.goto(`${BASE}/static/dist/ai.html#/client/1/wo`);
        const btn = page.locator('[data-action="wo-open-first"]');
        await expect(btn).toBeVisible({ timeout: 15000 });
        await btn.click();
        const note = page.locator('.order-open-empty [role="alert"]');
        await expect(note).toContainText('OCR 余额不足');
        const topup = page.locator('.order-open-empty a.btn.pri');
        await expect(topup).toBeVisible();
        await expect(topup).toHaveText('去充值');
        await expect(topup).toHaveAttribute('href', '#/settings?focus=billing');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '03-open-order-402.png'),
            fullPage: true,
        });
    });

    // 落点验收:深链的承诺是「落地就看得见充值」。旧断言只判 rect.top < innerHeight,而
    // 桌面视口下设置页整页 fit、根本没有滚动条 —— 把 scrollIntoView 整个删掉它照样绿。
    // 现在改成手机视口(必须滚)+ 断言真滚过(scrollY>0)+ 断言充值按钮整颗在视口内。
    test('「去充值」深链在会滚动的视口里真滚到计费区(390×844)', async ({ page }) => {
        await page.setViewportSize(MOBILE);
        await boot(page, { createOrder: { status: 402, code: 'insufficient_balance' } });
        await page.goto(`${BASE}/static/dist/ai.html#/client/1/wo`);
        const btn = page.locator('[data-action="wo-open-first"]');
        await expect(btn).toBeVisible({ timeout: 15000 });
        await btn.click();
        await page.locator('.order-open-empty a.btn.pri').click();

        await expect(page.locator('#v-settings')).toHaveClass(/on/);
        const topupBtn = page.locator('[data-action="bill-topup"]');
        await expect(topupBtn).toBeVisible({ timeout: 15000 });
        // 页面被真内容撑开后才有得滚,补滚是异步重试的——轮询等它到位,别只量落地那一帧。
        await expect
            .poll(() => page.evaluate(() => window.scrollY), { timeout: 10000 })
            .toBeGreaterThan(0);
        const geo = await topupBtn.evaluate((el) => {
            const r = el.getBoundingClientRect();
            return {
                top: r.top,
                bottom: r.bottom,
                vh: window.innerHeight,
                scrollY: window.scrollY,
                docHeight: document.documentElement.scrollHeight,
            };
        });
        // 前提自检:页面真的需要滚(否则这条测试又退化成恒真)。
        expect(geo.docHeight).toBeGreaterThan(geo.vh);
        expect(geo.top).toBeGreaterThanOrEqual(0);
        expect(geo.bottom).toBeLessThanOrEqual(geo.vh);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '04-topup-deeplink-landing.png'),
            fullPage: false,
        });
    });

    // 对照组:同一页、同一视口,只是不带 ?focus=billing。scrollY 必须留在 0 ——
    // 证明上一条量到的位移是深链滚的,不是页面自己就那样。
    test('不带 focus 进设置页不滚(对照组 · 证明上条量的是深链的功劳)', async ({ page }) => {
        await page.setViewportSize(MOBILE);
        await boot(page);
        await page.goto(`${BASE}/static/dist/ai.html#/settings`);
        await expect(page.locator('[data-action="bill-topup"]')).toBeVisible({ timeout: 15000 });
        await page.waitForTimeout(1500); // 深链那条的重试窗口全部走完,仍不该动
        expect(await page.evaluate(() => window.scrollY)).toBe(0);
    });

    // 员工落地页:没有充值按钮是对的(后端 owner_only),但只留一句「仅负责人可见」就是
    // 死胡同——「去充值」的文案已经许了出路,落地必须说清该找谁、让谁在哪儿点。
    test('员工点「去充值」落地不是死胡同:说清该找谁充', async ({ page }) => {
        await page.setViewportSize(MOBILE);
        await boot(page);
        await page.route('**/api/me/credits', (r) =>
            r.fulfill({
                contentType: 'application/json',
                body: JSON.stringify({ has_tenant: true, is_owner: false, my_invoice_count: 7 }),
            })
        );
        await page.goto(`${BASE}/static/dist/ai.html#/settings?focus=billing`);
        const panel = page.locator('#stBillingWrap');
        await expect(panel).toContainText('余额与充值仅事务所负责人可见', { timeout: 15000 });
        await expect(panel).toContainText('设置 → OCR 识别余额 → 充值');
        await expect(panel.locator('[data-action="bill-topup"]')).toHaveCount(0);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '08-topup-landing-employee.png'),
            fullPage: true,
        });
    });

    // 影子底稿/报表包「跑完但降级」:工单一路走到 review、status 里没有任何痕迹,只认 stuck
    // 的旧判据会继续说「不用管它,会自动生成」。后端 *_state 直报 degraded 才说得对。
    test('工单跑到 review 但影子/报表降级 → 说的是生成失败,不是「会自动生成」', async ({
        page,
    }) => {
        await boot(page);
        await page.unroute('**/api/workorder/orders?**');
        await page.route('**/api/workorder/orders?**', (r) =>
            r.fulfill({
                contentType: 'application/json',
                body: JSON.stringify({
                    orders: [
                        {
                            id: 'wo-1',
                            period: '2569-07',
                            intent: 'monthly_vat',
                            status: 'review',
                            current_step: 'review',
                        },
                    ],
                }),
            })
        );
        await page.route('**/api/workorder/orders/wo-1', (r) =>
            r.fulfill({
                contentType: 'application/json',
                body: JSON.stringify({
                    id: 'wo-1',
                    period: '2569-07',
                    status: 'review',
                    current_step: 'review',
                    numbers: {},
                    flagged: [],
                    needs: [],
                    blocked_reasons: [],
                    shadow_draft: null,
                    financials: null,
                    shadow_draft_state: 'degraded',
                    financials_state: 'degraded',
                }),
            })
        );
        await page.goto(`${BASE}/static/dist/ai.html#/client/1/wo`);

        const shadow = page.locator('#shadowRoot');
        await expect(shadow).toContainText('影子底稿生成失败', { timeout: 15000 });
        await expect(shadow).not.toContainText('不用管它');
        await expect(shadow.locator('[data-action="wo-retry-stuck"]')).toHaveCount(0);
        const fin = page.locator('#financialsRoot');
        await expect(fin).toContainText('报表包生成失败');
        await expect(fin).not.toContainText('不用管它');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '09-wo-degraded-sections.png'),
            fullPage: true,
        });
    });

    test('收料上传:401 → 失败批说的是登录过期,不是干巴巴「上传失败」', async ({ page }) => {
        const card = await openUploadFailureCard(page, { status: 401 });
        const banner = card.locator('[role="alert"]');
        await expect(banner).toBeVisible({ timeout: 15000 });
        await expect(banner).toContainText('这些文件没传上去');
        await expect(banner).toContainText('登录已过期');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '05-upload-401.png'),
            fullPage: true,
        });
    });

    test('收料上传:余额不足 402 → 重传旁边多一个「去充值」', async ({ page }) => {
        const card = await open402Card(page, 'zh');
        await expect(card.locator('[role="alert"]')).toContainText('OCR 余额不足');
        await expect(card.locator('[data-action="ik-retry-failed"]')).toBeVisible();
        await expect(card.locator('a.btn.pri')).toHaveText('去充值');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '06-upload-402.png'),
            fullPage: true,
        });
    });

    // 原因行与「重传」之间那一句此前是 intake_failed_batch_n 原样上屏(四份词典都没这条,
    // at() 回落成 key 本身),中泰两语的 402 卡上肉眼可见。断言盯这句话的字 + 反证卡上
    // 没有下划线标识符;机械面由 scripts/check_ai_i18n_refs.py 兜底,不让它再犯第二次。
    for (const c of [
        { lang: 'zh', says: '还没进系统', shot: '07-upload-402-count-zh.png' },
        { lang: 'th', says: 'ยังไม่เข้าระบบ', shot: '07-upload-402-count-th.png' },
    ]) {
        test(`收料上传 402:件数那句是人话不是生 key(${c.lang})`, async ({ page }) => {
            const card = await open402Card(page, c.lang);
            const line = card.locator('p.needs-sub').last();
            await expect(line).toBeVisible();
            await expect(line).toContainText(c.says);
            await expect(card).not.toContainText('intake_failed_batch_n');
            await page.screenshot({ path: path.join(ARTIFACT_DIR, c.shot), fullPage: true });
        });
    }
});
