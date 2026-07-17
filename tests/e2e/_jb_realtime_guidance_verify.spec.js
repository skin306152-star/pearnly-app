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

    test('工单页引导条「有 N 件事等你」可点跳待我处理', async ({ page }) => {
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
        const guideBtn = page.locator('[data-action="wo-goto-pool"]');
        await expect(guideBtn).toBeVisible({ timeout: 8000 });
        await expect(guideBtn).toContainText('1');
        await page.screenshot({ path: path.join(ART, '05-wo-guidance-banner.png') });
        await guideBtn.click();
        await expect.poll(() => page.evaluate(() => window.location.hash)).toBe('#/pool');
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
        await page.screenshot({ path: path.join(ART, '07-deeplink-period-default.png') });
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
        await page.waitForSelector('[data-action="wo-goto-pool"]', { timeout: 15000 });
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
