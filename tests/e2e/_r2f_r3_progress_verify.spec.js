// R2F-R3 #5 · 跑批进度诚实 + 409 接线 · 本地 stub 真浏览器验收(非 CI 用例 · 用完即删,
// 同 _r2f_r3_verify.spec.js 先例)
// ============================================================
// 拆成独立文件的理由:轮询超时用例要真等 POLL_MAX_TRIES(30)× POLL_INTERVAL_MS(2s)=
// 60 秒真实时间才能诚实验证"没有假装成功也没有无声空转"这件事本身,不拖慢
// _r2f_r3_verify.spec.js 里那批秒级用例。
//
// 起法:npx playwright test tests/e2e/_r2f_r3_progress_verify.spec.js
/* global window */
const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8993;
const BASE = `http://127.0.0.1:${PORT}`;
const PAGE = BASE + '/static/dist/ai.html';
const ART = path.join(__dirname, '_artifacts', 'r2f_r3');
const FIXTURES = path.join(__dirname, '..', 'fixtures', 'messy_intake_pack');

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
            window.localStorage.setItem('mrpilot_token', token || 'tok-r2f-r3-progress');
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

test.describe('R2F-R3 #5 · 收料页(ai-intake.js)跑批进度 + 409', () => {
    test('409 显示专属"正在跑"文案且继续轮询;classify 进度显示「识别中 X/N」', async ({ page }) => {
        test.setTimeout(30000);
        let runCalls = 0;
        let pollCalls = 0;
        await mockRoutes(page, {
            'GET /api/workspace/clients/c1': jsonRoute({ client: { id: 'c1', name: 'Acme Co' } }),
            'GET /api/workorder/orders': jsonRoute({ orders: [{ id: 'wo-1', period: '2569-05' }] }),
            'GET /api/workorder/orders/wo-1': async (route) => {
                pollCalls += 1;
                if (pollCalls === 1) {
                    // 首次挂载读详情:干净待跑(触发上传把 dirty 打真)。
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
                // 之后每次轮询:仍在 classify 步,processed 单调递增,永不收口(stuck+无
                // numbers/flagged/blocked_reasons/needs)——测的是进度呈现,不是终态路由。
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
        await page.click('[data-action="ik-upload"]');
        await expect(page.locator('[data-action="ik-rerun"]')).toBeVisible({ timeout: 8000 });

        await page.click('[data-action="ik-rerun"]');
        // 409 专属文案(非通用 err_generic)立即可见——不是终态,按钮仍是等待态(继续轮询)。
        const rerunCard = page.locator('.rerun-card');
        await expect(rerunCard).toContainText('running', { timeout: 3000 });
        await expect(rerunCard.locator('button[disabled]')).toBeVisible();
        await page.screenshot({ path: path.join(ART, '11-409-run-in-progress.png') });

        // 等 1-2 个轮询周期(2s 一次),断言真进度数字出现在等待态按钮文案里。
        await expect(rerunCard).toContainText(/\d+\/8/, { timeout: 8000 });
        await page.screenshot({ path: path.join(ART, '12-classify-progress.png') });
    });

    test('轮询次数用尽:诚实显示"仍在后台跑" + 手动刷新钮可用', async ({ page }) => {
        test.setTimeout(90000);
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
        await page.click('[data-action="ik-upload"]');
        await expect(page.locator('[data-action="ik-rerun"]')).toBeVisible({ timeout: 8000 });
        await page.click('[data-action="ik-rerun"]');

        // 真等 POLL_MAX_TRIES(30)× POLL_INTERVAL_MS(2s)= 60 秒——不假装收口,也不能
        // 无声挂着不给反馈。诚实文案 + 刷新钮同时出现才算过。
        const rerunCard = page.locator('.rerun-card');
        await expect(page.locator('[data-action="ik-refresh-status"]')).toBeVisible({
            timeout: 70000,
        });
        await expect(rerunCard).not.toContainText('err_generic');
        await page.screenshot({ path: path.join(ART, '13-poll-timeout-honest.png') });

        // 手动刷新钮点了确实重新起一轮轮询(转回等待态,不是死按钮)。
        await page.click('[data-action="ik-refresh-status"]');
        await expect(rerunCard.locator('button[disabled]')).toBeVisible({ timeout: 3000 });
        await page.screenshot({ path: path.join(ART, '14-manual-refresh-resumes-poll.png') });
    });
});

test.describe('R2F-R3 #5 · 审核队列(ai-review.js)409 接线', () => {
    test('裁决后重新跑撞 409:专属"正在跑"文案而非通用错误', async ({ page }) => {
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
        await page.screenshot({ path: path.join(ART, '15-review-409-run-in-progress.png') });
    });
});
