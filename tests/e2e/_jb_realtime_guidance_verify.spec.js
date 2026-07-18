// J-B · 前端实时性 + 引导链 + 状态诚实 · 本地 stub 真浏览器验收(非 CI 用例 · 用完即删,
// 同 _r2f_r3_verify.spec.js 先例)
// ============================================================
// 真渲染代码(static/dist/ai.js/ai.css/ai.html 原样加载,零改造)+ 真 DOM,只桩网络层
// (page.route 拦 /api/*)。本文件盖派单书验收断言 1-5:
//   1) 分批上传(splitBatches 切多批)期间不触发 run,末批落定才触发一次
//   2) 跑批中 order_detail 轮询显真进度 + 5s 内自刷 + 终态后轮询停
//   3) stuck 单落非「等你审」列 + 工单页引导条可点跳待我处理;标记待签后「去签批 →」可点
//   4) 深链 period → 开单控件默认落该期
//   5) 手机 390 视口无横向溢出(既有基线 + 新增引导条)
//
// 起法:npx playwright test tests/e2e/_jb_realtime_guidance_verify.spec.js
/* global window, document */
const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8994;
const BASE = `http://127.0.0.1:${PORT}`;
const PAGE = BASE + '/static/dist/ai.html';
const ART = path.join(__dirname, '_artifacts', 'jb');

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT);
});

test.afterAll(() => {
    localServer.stop(server);
});

async function mockRoutes(page, table, opts = {}) {
    await page.route('**/api/**', async (route) => {
        const req = route.request();
        const url = new URL(req.url());
        const key = `${req.method()} ${url.pathname}`;
        const handler = table[key];
        if (handler) return handler(route, req, url);
        return route.fulfill({ contentType: 'application/json', body: '{}' });
    });
    await page.addInitScript(
        ([lang, token]) => {
            window.localStorage.setItem('mrpilot_token', token || 'tok-jb');
            window.localStorage.setItem('mrpilot_lang', lang || 'en');
        },
        [opts.lang, opts.token]
    );
}

function jsonRoute(body, status) {
    return (route) =>
        route.fulfill({
            status: status || 200,
            contentType: 'application/json',
            body: JSON.stringify(body),
        });
}

// splitBatches(BATCH_MAX_FILES=20) 触批切:21 个小合成文件(不需要真实图片内容,
// addMaterials 走 mock,不解析文件字节)。
function syntheticFiles(n) {
    return Array.from({ length: n }, (_, i) => ({
        name: `f${i}.jpg`,
        mimeType: 'image/jpeg',
        buffer: Buffer.from(`fake-${i}`),
    }));
}

// 迁移自 _r2f_r3_progress_verify.spec.js(R2 打回 #3:该文件不是"非 CI 用例",CI 的
// npx playwright test 全量跑 tests/e2e/*.spec.js,它就在里面,断言已随 AI.poll 改造
// (2s→5s 间隔 / 30 次→24 次上限)失效——断言原样搬进本文件、更新新数值口径,原文件删除。
const FIXTURES = path.join(__dirname, '..', 'fixtures', 'messy_intake_pack');

// 后端 409 结构化响应体(routes/workorder_routes.py::_run_in_progress_detail 逐字段对齐)。
function runInProgressBody(workOrderId) {
    return {
        detail: {
            code: 'workorder.run_in_progress',
            work_order_id: workOrderId,
            status: 'running',
            current_step: 'classify',
            run_lease: null,
        },
    };
}

test.describe('J-B #1 · 收齐才开跑', () => {
    test('分批上传:第一批落定不触发 run,末批落定才触发一次', async ({ page }) => {
        test.setTimeout(30000);
        let materialsCalls = 0;
        let runCalls = 0;
        await mockRoutes(page, {
            'GET /api/workspace/clients/c1': jsonRoute({ client: { id: 'c1', name: 'Acme Co' } }),
            'GET /api/workorder/orders': jsonRoute({ orders: [{ id: 'wo-1', period: '2569-05' }] }),
            'GET /api/workorder/orders/wo-1': jsonRoute({
                id: 'wo-1',
                status: 'collecting',
                needs: [],
                blocked_reasons: [],
                numbers: {},
                flagged: [],
            }),
            'POST /api/workorder/orders/wo-1/materials': async (route) => {
                materialsCalls += 1;
                return route.fulfill({
                    contentType: 'application/json',
                    body: JSON.stringify({
                        registered: [{ item_id: 'a' + materialsCalls }],
                        count: 1,
                    }),
                });
            },
            'POST /api/workorder/orders/wo-1/run': async (route) => {
                runCalls += 1;
                return route.fulfill({
                    contentType: 'application/json',
                    body: JSON.stringify({ queued: true, status: 'running' }),
                });
            },
        });

        await page.goto(`${PAGE}#/client/c1/intake`);
        await page.waitForSelector('#ikDrop', { timeout: 15000 });
        // 21 张切成 2 批(20+1,BATCH_MAX_FILES=20)。
        await page.setInputFiles('#ikFileInput', syntheticFiles(21));
        await page.click('[data-action="ik-upload"]');

        // 第一批(20 件)落定后立即探一次:此刻第二批仍在传或刚开始,run 尚不该被触发。
        await expect.poll(() => materialsCalls, { timeout: 8000 }).toBeGreaterThanOrEqual(1);
        expect(runCalls, '第一批落定不该已经触发 run').toBe(0);

        // 整趟(两批)收尾后才触发一次 run。
        await expect.poll(() => materialsCalls, { timeout: 8000 }).toBe(2);
        await expect.poll(() => runCalls, { timeout: 8000 }).toBe(1);
        // 稳定态复核:不会再追加第二次 run。
        await page.waitForTimeout(500);
        expect(runCalls).toBe(1);
        await page.screenshot({ path: path.join(ART, '01-batch-collect-then-run.png') });
    });
});

test.describe('J-B #2 · 工单页活着就自动刷 + 真进度 + 终态即停', () => {
    test('reconcile 步「读对账单 X/N」5s 内自刷,终态(archive)后轮询停', async ({ page }) => {
        test.setTimeout(40000);
        let pollCalls = 0;
        await mockRoutes(page, {
            'GET /api/workspace/clients/c1': jsonRoute({ client: { id: 'c1', name: 'Acme Co' } }),
            'GET /api/workorder/orders': jsonRoute({ orders: [{ id: 'wo-1', period: '2569-05' }] }),
            'GET /api/workorder/orders/wo-1': async (route) => {
                pollCalls += 1;
                if (pollCalls < 3) {
                    return route.fulfill({
                        contentType: 'application/json',
                        body: JSON.stringify({
                            id: 'wo-1',
                            status: 'running',
                            current_step: 'reconcile',
                            bank_progress: { step: 'reconcile', processed: pollCalls, total: 4 },
                            needs: [],
                            blocked_reasons: [],
                            numbers: {},
                            flagged: [],
                        }),
                    });
                }
                // 第 3 次起收口归档(终态)——之后轮询应停,不再追加请求。
                return route.fulfill({
                    contentType: 'application/json',
                    body: JSON.stringify({
                        id: 'wo-1',
                        status: 'archive',
                        current_step: 'archive',
                        needs: [],
                        blocked_reasons: [],
                        numbers: { tax_due: '100.00' },
                        flagged: [],
                    }),
                });
            },
        });

        await page.goto(`${PAGE}#/client/c1/wo`);
        await page.waitForSelector('#woSummaryPanel', { timeout: 15000 });

        // 真进度数字出现,不是死转省略号(J-1/J-9)。
        await expect(page.locator('.wo-progress')).toContainText(/\d+\/4/, { timeout: 12000 });
        await page.screenshot({ path: path.join(ART, '02-wo-bank-progress.png') });

        // 5s 一轮自动刷新——不手动 F5,断言 pollCalls 会自己涨到 3+(即走到终态)。
        await expect.poll(() => pollCalls, { timeout: 20000 }).toBeGreaterThanOrEqual(3);
        await expect(page.locator('.chip')).toContainText(/./, { timeout: 5000 });
        await page.screenshot({ path: path.join(ART, '03-wo-archived.png') });

        // 终态后轮询停:等一轮以上的间隔,pollCalls 不再增长(断言无多余请求)。
        const afterTerminal = pollCalls;
        await page.waitForTimeout(6000);
        expect(pollCalls, '终态后不该再轮询').toBe(afterTerminal);
    });
});

test.describe('J-B #3 · 看板状态诚实 + 引导链②③', () => {
    test('stuck 单(卡住但无真队列)落非「等你审」列', async ({ page }) => {
        await mockRoutes(page, {
            'GET /api/workspace/clients': jsonRoute({
                clients: [{ id: 'c1', name: 'Acme Co' }],
            }),
            'GET /api/workorder/orders': jsonRoute({
                orders: [
                    { id: 'wo-1', workspace_client_id: 'c1', period: '2569-05', status: 'stuck' },
                ],
            }),
            'GET /api/workorder/orders/wo-1': jsonRoute({
                id: 'wo-1',
                status: 'stuck',
                needs: [],
                blocked_reasons: ['reconcile.input_vat_mismatch'],
                numbers: {},
                flagged: [], // 卡住但没有真的待裁决票——不该落「等你审」
            }),
        });
        await page.goto(`${PAGE}#/board`);
        await page.waitForSelector('.kcard', { timeout: 15000 });
        const card = page.locator('.kcard', { hasText: 'Acme Co' });
        await expect(card).toBeVisible();
        // .hot 类只在「等你审」列的卡片上加(见 ai-kanban-render.js::cardHtml)——断言没有,
        // 即该卡没有被塞进等你审列。
        await expect(card).not.toHaveClass(/hot/);
        await page.screenshot({ path: path.join(ART, '04-board-stuck-not-review.png') });
    });

    // 2026-07-17 S2 拍板 banner 分叉:有未判票=就地去本客户审核 tab(判完回来还在同一单),
    // 不再甩去跨客户的「待我处理」;review(轮到签批)才跳 pool——断言随产品决定更新。
    test('工单页引导条「有 N 张票等你判」可点跳本客户审核', async ({ page }) => {
        await mockRoutes(page, {
            'GET /api/workspace/clients/c1': jsonRoute({ client: { id: 'c1', name: 'Acme Co' } }),
            'GET /api/workorder/orders': jsonRoute({ orders: [{ id: 'wo-1', period: '2569-05' }] }),
            'GET /api/workorder/orders/wo-1': jsonRoute({
                id: 'wo-1',
                status: 'stuck',
                needs: [],
                blocked_reasons: [],
                numbers: {},
                flagged: [
                    {
                        item_id: 'i1',
                        file_ref: 'f1.jpg',
                        kind: 'purchase_invoice',
                        flag_reason: 'validation_fail',
                        ocr_read: {},
                        decision: null,
                    },
                ],
            }),
        });
        await page.goto(`${PAGE}#/client/c1/wo`);
        await page.waitForSelector('#woSummaryPanel', { timeout: 15000 });
        const guideBtn = page.locator('[data-action="wo-goto-review"]');
        await expect(guideBtn).toBeVisible({ timeout: 8000 });
        await expect(guideBtn).toContainText('1');
        await page.screenshot({ path: path.join(ART, '05-wo-guidance-banner.png') });
        await guideBtn.click();
        await expect
            .poll(() => page.evaluate(() => window.location.hash))
            .toBe('#/client/c1/review');
    });

    test('交付包「已标记待签」旁「去签批 →」可见可点', async ({ page }) => {
        await mockRoutes(page, {
            'GET /api/workspace/clients/c1': jsonRoute({ client: { id: 'c1', name: 'Acme Co' } }),
            'GET /api/workorder/orders': jsonRoute({ orders: [{ id: 'wo-1', period: '2569-05' }] }),
            'GET /api/workorder/orders/wo-1': jsonRoute({
                id: 'wo-1',
                status: 'review',
                needs: [],
                blocked_reasons: [],
                numbers: { tax_due: '100.00' },
                flagged: [],
            }),
            'GET /api/workorder/orders/wo-1/deliverables': jsonRoute({
                deliverables: [{ kind: 'pp30_draft', numbers: { tax_due: '100.00' } }],
            }),
            'POST /api/workorder/orders/wo-1/review': jsonRoute({ ok: true, event_id: 1 }),
        });
        await page.goto(`${PAGE}#/client/c1/pkg`);
        await page.waitForSelector('[data-action="pkg-sign"]', { timeout: 15000 });
        await page.click('[data-action="pkg-sign"]');
        const gotoSignoff = page.locator('[data-action="pkg-goto-pool"]');
        await expect(gotoSignoff).toBeVisible({ timeout: 8000 });
        await page.screenshot({ path: path.join(ART, '06-pkg-goto-signoff.png') });
        await gotoSignoff.click();
        await expect.poll(() => page.evaluate(() => window.location.hash)).toBe('#/pool');
    });
});

test.describe('J-B #4 · 深链账期 → 开单控件默认', () => {
    test('#/client/x/intake?period=2569-05 → 开单账期选择器默认 2569-05', async ({ page }) => {
        await mockRoutes(page, {
            'GET /api/workspace/clients/c1': jsonRoute({ client: { id: 'c1', name: 'Acme Co' } }),
            'GET /api/workorder/orders': jsonRoute({ orders: [] }), // 零工单空态
        });
        await page.goto(`${PAGE}#/client/c1/intake?period=2569-05`);
        await page.waitForSelector('#ikEmptyPeriodSel', { timeout: 15000 });
        await expect(page.locator('#ikEmptyPeriodSel')).toHaveValue('2569-05');
        const openCard = page.locator('#cv-intake .order-open-empty');
        const openForm = openCard.locator('.order-open-form');
        await expect(openCard).toBeVisible();
        await expect(openCard.locator('label[for="ikEmptyPeriodSel"]')).toContainText(
            'Filing period'
        );
        const [cardBox, formBox, selectBox, buttonBox] = await Promise.all([
            openCard.boundingBox(),
            openForm.boundingBox(),
            openForm.locator('#ikEmptyPeriodSel').boundingBox(),
            openForm.locator('[data-action="intake-open-order"]').boundingBox(),
        ]);
        expect(
            Math.abs(formBox.x + formBox.width / 2 - (cardBox.x + cardBox.width / 2))
        ).toBeLessThan(2);
        expect(
            Math.abs(selectBox.y + selectBox.height - (buttonBox.y + buttonBox.height))
        ).toBeLessThan(2);
        await expect(page.locator('#periodValue')).toHaveText('2569-05');
        await page.screenshot({ path: path.join(ART, '07-deeplink-period-default.png') });
    });

    test('#/client/x/wo?period=2569-05 → 工单开单也保留深链账期', async ({ page }) => {
        await mockRoutes(page, {
            'GET /api/workspace/clients/c1': jsonRoute({ client: { id: 'c1', name: 'Acme Co' } }),
            'GET /api/workorder/orders': jsonRoute({ orders: [] }),
        });
        await page.goto(`${PAGE}#/client/c1/wo?period=2569-05`);
        await page.waitForSelector('#woEmptyPeriodSel', { timeout: 15000 });
        await expect(page.locator('#woEmptyPeriodSel')).toHaveValue('2569-05');
        await page.screenshot({ path: path.join(ART, '07b-wo-deeplink-period-default.png') });
    });
});

test.describe('Open-order empty state · mobile layout', () => {
    test('390px stacks the period field and primary action at full width', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await mockRoutes(page, {
            'GET /api/workspace/clients/c1': jsonRoute({ client: { id: 'c1', name: 'Acme Co' } }),
            'GET /api/workorder/orders': jsonRoute({ orders: [] }),
        });
        await page.goto(`${PAGE}#/client/c1/intake?period=2569-05`);
        const openForm = page.locator('#cv-intake .order-open-form');
        await expect(openForm).toBeVisible({ timeout: 15000 });
        const [formBox, selectBox, buttonBox] = await Promise.all([
            openForm.boundingBox(),
            openForm.locator('#ikEmptyPeriodSel').boundingBox(),
            openForm.locator('[data-action="intake-open-order"]').boundingBox(),
        ]);
        expect(buttonBox.y).toBeGreaterThan(selectBox.y + selectBox.height);
        expect(Math.abs(selectBox.width - formBox.width)).toBeLessThan(2);
        expect(Math.abs(buttonBox.width - formBox.width)).toBeLessThan(2);
        await page.screenshot({ path: path.join(ART, '07c-open-order-mobile.png') });
    });
});

test.describe('J-B #5 · 手机 390 视口无横向溢出', () => {
    test('clientTabs + 新增引导条在 390×844 下不新增横向溢出', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await mockRoutes(page, {
            'GET /api/workspace/clients/c1': jsonRoute({ client: { id: 'c1', name: 'Acme Co' } }),
            'GET /api/workorder/orders': jsonRoute({ orders: [{ id: 'wo-1', period: '2569-05' }] }),
            'GET /api/workorder/orders/wo-1': jsonRoute({
                id: 'wo-1',
                status: 'stuck',
                needs: [],
                blocked_reasons: [],
                numbers: {},
                flagged: [
                    {
                        item_id: 'i1',
                        file_ref: 'f1.jpg',
                        kind: 'purchase_invoice',
                        flag_reason: 'validation_fail',
                        ocr_read: {},
                        decision: null,
                    },
                ],
            }),
        });
        await page.goto(`${PAGE}#/client/c1/wo`);
        await page.waitForSelector('[data-action="wo-goto-review"]', { timeout: 15000 });
        const overflow = await page.evaluate(() => document.body.scrollWidth - window.innerWidth);
        expect(overflow, '390 视口不该有横向溢出').toBeLessThanOrEqual(1);
        const tabsBox = await page.locator('#clientTabs').boundingBox();
        expect(tabsBox.x).toBeGreaterThanOrEqual(0);
        expect(tabsBox.x + tabsBox.width).toBeLessThanOrEqual(390 + 1);
        await page.screenshot({
            path: path.join(ART, '08-mobile-390-no-overflow.png'),
            fullPage: true,
        });
    });
});

test.describe('J-B #6 · 迁移自 R2F-R3(409 接线 + classify 进度 + 轮询超时诚实)', () => {
    test('收料页:409 显示专属"正在跑"文案且继续轮询;classify 进度显示「识别中 X/N」', async ({
        page,
    }) => {
        test.setTimeout(30000);
        let runCalls = 0;
        let pollCalls = 0;
        await mockRoutes(page, {
            'GET /api/workspace/clients/c1': jsonRoute({ client: { id: 'c1', name: 'Acme Co' } }),
            'GET /api/workorder/orders': jsonRoute({ orders: [{ id: 'wo-1', period: '2569-05' }] }),
            'GET /api/workorder/orders/wo-1': async (route) => {
                pollCalls += 1;
                if (pollCalls === 1) {
                    return route.fulfill({
                        contentType: 'application/json',
                        body: JSON.stringify({
                            id: 'wo-1',
                            status: 'collecting',
                            needs: [],
                            numbers: {},
                            flagged: [],
                        }),
                    });
                }
                const processed = Math.min(pollCalls - 1, 5);
                return route.fulfill({
                    contentType: 'application/json',
                    body: JSON.stringify({
                        id: 'wo-1',
                        status: 'stuck',
                        current_step: 'classify',
                        progress: { step: 'classify', processed, total: 8 },
                        needs: [],
                        blocked_reasons: [],
                        numbers: {},
                        flagged: [],
                    }),
                });
            },
            'POST /api/workorder/orders/wo-1/materials': jsonRoute({
                registered: [{ item_id: 'a' }],
                count: 1,
            }),
            'POST /api/workorder/orders/wo-1/run': async (route) => {
                runCalls += 1;
                if (runCalls === 1) {
                    return route.fulfill({
                        status: 409,
                        contentType: 'application/json',
                        body: JSON.stringify(runInProgressBody('wo-1')),
                    });
                }
                return route.fulfill({
                    contentType: 'application/json',
                    body: JSON.stringify({ queued: true, status: 'running' }),
                });
            },
        });

        await page.goto(`${PAGE}#/client/c1/intake`);
        await page.waitForSelector('#ikDrop', { timeout: 15000 });
        await page.setInputFiles('#ikFileInput', path.join(FIXTURES, 'normal_receipt.jpg'));
        // 收齐才开跑(J-B):upload() 落定后自动触发 startRerun(),不必再手点「重新跑」
        // ——ik-rerun 按钮只在 idle 态渲染,自动续跑直接跳过 idle 落到 waiting/409 态,
        // 旧测试手点这步已经不成立(元素压根不出现),等 .rerun-card 直接进等待态即可。
        await page.click('[data-action="ik-upload"]');
        // 409 专属文案(非通用 err_generic)立即可见——不是终态,按钮仍是等待态(继续轮询)。
        const rerunCard = page.locator('.rerun-card');
        await expect(rerunCard).toContainText('running', { timeout: 8000 });
        await expect(rerunCard.locator('button[disabled]')).toBeVisible();
        await page.screenshot({ path: path.join(ART, '09-intake-409-run-in-progress.png') });

        // AI.poll 默认 5s 一轮(J-B 改造前是 2s)——等真进度数字出现在等待态按钮文案里。
        await expect(rerunCard).toContainText(/\d+\/8/, { timeout: 8000 });
        await page.screenshot({ path: path.join(ART, '10-intake-classify-progress.png') });
    });

    test('收料页:轮询次数用尽诚实显示"仍在后台跑" + 手动刷新钮可用', async ({ page }) => {
        // AI.poll 默认 intervalMs=5000 × maxTries=24 = 120s 才耗尽——page.clock.runFor/
        // fastForward 试过都追不上"这一轮 fetch(真 mock 往返)落定才排下一轮定时器"的链式
        // 调度(虚拟时钟只接管 setTimeout/Date,route 的 mock 响应仍走真 CDP 往返,两者没对
        // 齐,runFor 卡在第一轮不再推进——实测证据见收尾报告)。这里就真等,不弄虚的。
        test.setTimeout(150000);
        await mockRoutes(page, {
            'GET /api/workspace/clients/c1': jsonRoute({ client: { id: 'c1', name: 'Acme Co' } }),
            'GET /api/workorder/orders': jsonRoute({ orders: [{ id: 'wo-1', period: '2569-05' }] }),
            'GET /api/workorder/orders/wo-1': jsonRoute({
                id: 'wo-1',
                status: 'stuck',
                current_step: 'classify',
                needs: [],
                blocked_reasons: [],
                numbers: {},
                flagged: [],
            }),
            'POST /api/workorder/orders/wo-1/materials': jsonRoute({
                registered: [{ item_id: 'a' }],
                count: 1,
            }),
            'POST /api/workorder/orders/wo-1/run': jsonRoute({ queued: true, status: 'running' }),
        });

        await page.goto(`${PAGE}#/client/c1/intake`);
        await page.waitForSelector('#ikDrop', { timeout: 15000 });
        await page.setInputFiles('#ikFileInput', path.join(FIXTURES, 'normal_receipt.jpg'));
        // 收齐才开跑(J-B):upload() 落定即自动触发续跑,不必手点 ik-rerun(同上一用例注释)。
        await page.click('[data-action="ik-upload"]');
        await expect(page.locator('.rerun-body button[disabled]')).toBeVisible({ timeout: 8000 });

        // 真等 24 轮 × 5s = 120s 耗尽——不假装收口也不能无声挂着不给反馈。
        const rerunCard = page.locator('.rerun-card');
        await expect(page.locator('[data-action="ik-refresh-status"]')).toBeVisible({
            timeout: 130000,
        });
        await expect(rerunCard).not.toContainText('err_generic');
        await page.screenshot({ path: path.join(ART, '11-poll-timeout-honest.png') });

        // 手动刷新钮点了确实重新起一轮轮询(转回等待态,不是死按钮)。
        await page.click('[data-action="ik-refresh-status"]');
        await expect(rerunCard.locator('button[disabled]')).toBeVisible({ timeout: 3000 });
        await page.screenshot({ path: path.join(ART, '12-manual-refresh-resumes-poll.png') });
    });

    test('审核队列:裁决后重新跑撞 409:专属"正在跑"文案而非通用错误', async ({ page }) => {
        test.setTimeout(30000);
        let runCalls = 0;
        await mockRoutes(page, {
            'GET /api/workspace/clients/c1': jsonRoute({ client: { id: 'c1', name: 'Acme Co' } }),
            'GET /api/workorder/orders': jsonRoute({
                orders: [{ id: 'wo-r1', period: '2569-05' }],
            }),
            'GET /api/workorder/orders/wo-r1': jsonRoute({
                id: 'wo-r1',
                status: 'stuck',
                needs: [],
                numbers: {},
                flagged: [
                    {
                        item_id: 'i1',
                        file_ref: 'f1.jpg',
                        kind: 'purchase_invoice',
                        flag_reason: 'validation_fail',
                        ocr_read: {
                            seller_tax: '0105551234567',
                            subtotal: '100.00',
                            vat: '7.00',
                            total_amount: '107.00',
                            invoice_number: 'IV-1',
                        },
                        decision: null,
                        verdict_hint: { severity: 'crit' },
                    },
                ],
            }),
            'POST /api/workorder/orders/wo-r1/decisions': jsonRoute({ ok: true }),
            'POST /api/workorder/orders/wo-r1/run': async (route) => {
                runCalls += 1;
                if (runCalls === 1) {
                    return route.fulfill({
                        status: 409,
                        contentType: 'application/json',
                        body: JSON.stringify(runInProgressBody('wo-r1')),
                    });
                }
                return route.fulfill({
                    contentType: 'application/json',
                    body: JSON.stringify({ queued: true, status: 'running' }),
                });
            },
        });

        await page.goto(`${PAGE}#/client/c1/review`);
        await page.waitForSelector('[data-action="rv-accept"]', { timeout: 15000 });
        await page.click('[data-action="rv-accept"]');
        await expect(page.locator('[data-action="rv-rerun"]')).toBeVisible({ timeout: 8000 });

        await page.click('[data-action="rv-rerun"]');
        const doneCard = page.locator('.rv-done');
        await expect(doneCard).toContainText('running', { timeout: 3000 });
        await expect(doneCard.locator('button[disabled]')).toBeVisible();
        await page.screenshot({ path: path.join(ART, '13-review-409-run-in-progress.png') });
    });

    test('审核队列:票已审完但缺销项汇总:明确返回收料而非假装可出包', async ({ page }) => {
        await mockRoutes(page, {
            'GET /api/workspace/clients/c1': jsonRoute({ client: { id: 'c1', name: 'Acme Co' } }),
            'GET /api/workorder/orders': jsonRoute({
                orders: [{ id: 'wo-r2', period: '2569-05' }],
            }),
            'GET /api/workorder/orders/wo-r2': jsonRoute({
                id: 'wo-r2',
                status: 'stuck',
                needs: ['sales_summary'],
                blocked_reasons: [],
                numbers: {},
                flagged: [
                    {
                        item_id: 'i1',
                        file_ref: 'f1.jpg',
                        kind: 'purchase_invoice',
                        flag_reason: 'validation_fail',
                        ocr_read: {},
                        decision: { decision: 'face_value' },
                    },
                ],
            }),
        });

        await page.goto(`${PAGE}#/client/c1/review`);
        const doneCard = page.locator('.rv-done');
        await expect(doneCard.locator('[data-action="rv-go-intake"]')).toBeVisible({
            timeout: 15000,
        });
        await expect(doneCard.locator('.chip')).toContainText('Missing docs');
        await expect(doneCard.locator('[data-action="rv-rerun"]')).toHaveCount(0);
        await page.screenshot({ path: path.join(ART, '14-review-missing-sales-summary.png') });

        await doneCard.locator('[data-action="rv-go-intake"]').click();
        await expect(page).toHaveURL(/#\/client\/c1\/intake/);
        await expect(page.locator('.needs-card')).toBeVisible({ timeout: 8000 });
    });
});
