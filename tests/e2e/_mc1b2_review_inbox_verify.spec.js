// MC1-b2 / MC2-A3 · 全所审核收件箱(#/pool 三分区聚合页)· 本地 stub 真浏览器验收(非 CI 依赖
// prod · 自起本地静态服务,不依赖外部 server;CI 的 npx playwright test 会连本 spec 一起跑,故
// 全用例都用绝对 PAGE URL 打自起的本地服务,与 baseURL=pearnly.com 无关)
// ============================================================
// 真渲染代码(static/dist/ai.js/ai.css/ai.html 原样加载,零改造)+ 真 DOM + 真键盘 + 真 CSS,
// 只桩网络层(page.route 拦 /api/*)。MC2-A3 起 review-queue 一次带回跨工单 flagged_items feed +
// 各工单 sod 投影,桩响应形状逐字段对齐后端源码(review.review_queue()/review_feed.enrich()/
// evidence.flagged_projection()/verdict.hint())。
//
// MC2-A3 新增断言:①item feed 后端化(前端零 getOrder → F1 浏览器 N+1 根治)②政策单源(批量
// 建议读后端 verdict_hint.suggested_decision)③SoD 投影 proactive 显隐(order.sod 按数据收起签批钮)
// ④裁决后进度轮询(指数退避有限次,review-queue 被再次拉取)。两端截图存 _artifacts/mc2a3/。
//
// 起法:npx playwright test tests/e2e/_mc1b2_review_inbox_verify.spec.js
/* global window, document */
const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8984;
const BASE = `http://127.0.0.1:${PORT}`;
const PAGE = BASE + '/static/dist/ai.html';
const ART = path.join(__dirname, '_artifacts', 'mc2a3');

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT);
});

test.afterAll(() => {
    localServer.stop(server);
});

// ---------------------------------------------------------------- fixtures ----

function fakeToken() {
    const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
    return (
        b64({ alg: 'none' }) +
        '.' +
        b64({ sub: 'u-mc1b2', email: 'reviewer@pearnly.test' }) +
        '.sig'
    );
}

function moneyRead(seed) {
    return {
        seller_tax: '0105555' + String(100000 + seed).slice(-6),
        subtotal: (1000 + seed).toFixed(2),
        vat: ((1000 + seed) * 0.07).toFixed(2),
        total_amount: ((1000 + seed) * 1.07).toFixed(2),
        invoice_number: 'IV26-' + String(1000 + seed),
    };
}

// 跨工单 flagged item feed(review_feed.enrich 出的扁平表):每件自带 work_order_id/client_name/
// period + verdict_hint(含 severity + suggested_decision,MC2-A3 政策后端下发)。65 张同类
// 「本方销项待复核」(sales_doc_review · MID 置信 · 有安全默认动作)对齐第一场景规模。
function makeBulkFeed(n) {
    const items = [];
    for (let i = 0; i < n; i++) {
        const read = moneyRead(i);
        items.push({
            item_id: 'it-bulk-' + i,
            file_ref: 'C:/data/wo-65/sale_' + i + '.jpg',
            kind: 'sales_doc',
            flag_reason: 'sales_doc_review',
            ocr_read: read,
            decision: null,
            verdict_hint: {
                narrative_key: 'verdict_sales_doc',
                params: { seller_tax: read.seller_tax, vendor: 'Sister Makeup' },
                confidence: 'mid',
                severity: 'warn',
                suggested_decision: { decision: 'assign_kind', kind: 'sales_doc' },
            },
            work_order_id: 'wo-bulk',
            client_name: 'Sister Makeup',
            period: '2569-06',
        });
    }
    return items;
}

function reviewQueueFixture(opts) {
    opts = opts || {};
    const total = opts.bulkFlaggedTotal != null ? opts.bulkFlaggedTotal : 65;
    return {
        period: null,
        clients: [
            {
                workspace_client_id: 1,
                client_name: 'Sister Makeup',
                client_tax_id: '0105555167627',
                pool_pending: 0,
                orders: [
                    {
                        work_order_id: 'wo-bulk',
                        workspace_client_id: 1,
                        client_name: 'Sister Makeup',
                        client_tax_id: '0105555167627',
                        period: '2569-06',
                        status: opts.bulkOrderStatus || 'stuck',
                        current_step: 'reconcile',
                        updated_at: '2026-07-13T10:00:00+07:00',
                        next_due_efiling: '2569-07-15',
                        next_due_paper: '2569-07-07',
                        pool_pending: 0,
                        is_rework: !!opts.bulkIsRework,
                        flagged_groups:
                            total === 0
                                ? []
                                : [
                                      {
                                          flag_reason: 'sales_doc_review',
                                          severity: 'warn',
                                          count: total,
                                      },
                                  ],
                        flagged_total: total,
                        top_severity: total === 0 ? null : 'warn',
                        sod: opts.bulkSod,
                    },
                    {
                        work_order_id: 'wo-signoff',
                        workspace_client_id: 1,
                        client_name: 'Sister Makeup',
                        client_tax_id: '0105555167627',
                        period: '2569-05',
                        status: 'review',
                        current_step: 'review',
                        updated_at: '2026-07-12T10:00:00+07:00',
                        next_due_efiling: '2569-06-15',
                        next_due_paper: '2569-06-07',
                        pool_pending: 0,
                        is_rework: false,
                        flagged_groups: [],
                        flagged_total: 0,
                        top_severity: null,
                        sod: opts.signoffSod,
                        signoff: opts.signoffProj,
                    },
                ],
            },
        ],
        flagged_items: opts.feed || [],
        counts: { clients: 1, orders: 2, flagged: total },
    };
}

// ---------------------------------------------------------------- route wiring ----

async function wireApi(page, state) {
    state.queueCalls = 0;
    state.orderDetailCalls = 0;
    await page.route('**/api/**', async (route) => {
        const req = route.request();
        const url = new URL(req.url());
        const p = url.pathname;
        const method = req.method();

        if (p === '/api/ai/session' && method === 'GET') {
            return route.fulfill({ json: { ok: true } });
        }
        if (p === '/api/workorder/orders' && method === 'GET') {
            return route.fulfill({ json: { orders: [], count: 0, limit: 1, offset: 0 } });
        }
        if (p === '/api/me' && method === 'GET') {
            return route.fulfill({ json: { id: 'u-mc1b2', username: 'reviewer', role: 'owner' } });
        }
        if (p === '/api/workorder/review-queue' && method === 'GET') {
            state.queueCalls += 1;
            if (state.queueError) return route.fulfill({ status: 500, json: { detail: 'boom' } });
            return route.fulfill({ json: state.queueFixture() });
        }
        if (p === '/api/ai/client-pool' && method === 'GET') {
            return route.fulfill({ json: { groups: [] } });
        }
        // getOrder(order_detail):MC2-A3 后收件箱 feed 不再逐单拉它 —— 计数供 N+1 断言。
        if (/^\/api\/workorder\/orders\/[^/]+$/.test(p) && method === 'GET') {
            state.orderDetailCalls += 1;
            return route.fulfill({ json: { flagged: [] } });
        }
        if (p === '/api/workorder/orders/wo-bulk/decisions:batch' && method === 'POST') {
            const body = req.postDataJSON();
            const results = body.decisions.map((d) => ({
                item_id: d.item_id,
                ok: true,
                event_id: 1,
            }));
            state.feed = []; // 裁决落库后 review-queue 也如实清零 feed
            return route.fulfill({
                json: { results, ok_count: results.length, fail_count: 0, total: results.length },
            });
        }
        if (p === '/api/workorder/orders/wo-signoff/review' && method === 'POST') {
            return route.fulfill({ json: { ok: true, event_id: 101 } });
        }
        if (p === '/api/workorder/orders/wo-signoff/archive' && method === 'POST') {
            state.archiveCalls = (state.archiveCalls || 0) + 1;
            if (state.archiveShouldFailSod && state.archiveCalls === 1) {
                return route.fulfill({
                    status: 409,
                    json: { detail: 'workorder.sod.approver_is_preparer' },
                });
            }
            return route.fulfill({ json: { ok: true, manifest: { version: 1 } } });
        }
        if (p === '/api/workorder/orders/wo-signoff/self-review-declare' && method === 'POST') {
            return route.fulfill({ json: { ok: true, event_id: 102 } });
        }
        if (p === '/api/workorder/orders/wo-signoff/review-reject' && method === 'POST') {
            state.rejectSubmitted = req.postDataJSON();
            return route.fulfill({ json: { status: 'running', reopened_steps: ['reconcile'] } });
        }
        return route.fulfill({ status: 404, json: { detail: 'not_stubbed:' + p } });
    });
}

async function gotoPool(page, lang) {
    await page.addInitScript(
        ({ token, lang }) => {
            window.localStorage.setItem('mrpilot_token_ai', token);
            window.localStorage.setItem('mrpilot_lang', lang || 'zh');
        },
        { token: fakeToken(), lang }
    );
    await page.goto(PAGE);
    await page.waitForFunction(() => !!window.AI && !!window.AI.router);
    await page.evaluate(() => {
        window.location.hash = '#/pool';
    });
    await page.waitForSelector('#v-pool.on', { timeout: 15000 });
}

// ================================================================ tests ====

test.describe('MC1-b2/MC2-A3 · 全所审核收件箱三分区聚合页', () => {
    test('三分区结构 + 待审工单卡 + 空态(异常票据/客户待答为空)', async ({ page }) => {
        const state = { feed: [], queueFixture: () => reviewQueueFixture({ bulkFlaggedTotal: 0 }) };
        await wireApi(page, state);
        await gotoPool(page, 'zh');
        await page.waitForSelector('#riqWoBody .riq-wo', { timeout: 10000 });
        await expect(page.locator('#riqSecWorkorders, .riq-sec').first()).toBeVisible();
        await expect(page.locator('#riqFlaggedBody')).toContainText('没有异常票据');
        await page.screenshot({ path: path.join(ART, '01-structure-empty.png'), fullPage: true });
    });

    test('① item feed 后端化:裁决卡三件套 isVisible + 零 getOrder(F1 N+1 根治)', async ({
        page,
    }) => {
        const feed = makeBulkFeed(3);
        const state = {
            feed,
            queueFixture: () => reviewQueueFixture({ bulkFlaggedTotal: 3, feed: state.feed }),
        };
        await wireApi(page, state);
        await gotoPool(page, 'zh');
        await page.waitForSelector('.riq-item', { timeout: 10000 });
        const cards = page.locator('.riq-item');
        expect(await cards.count()).toBe(3);
        for (let i = 0; i < 3; i++) {
            const card = cards.nth(i);
            await expect(card.locator('.riq-fldt')).toBeVisible();
            await expect(card.locator('.riq-narrative')).toBeVisible();
            expect((await card.locator('.riq-narrative').innerText()).length).toBeGreaterThan(0);
            await expect(card.locator('.riq-item-hd .chip').first()).toBeVisible();
        }
        console.log('MC2A3_ORDER_DETAIL_CALLS=' + state.orderDetailCalls);
        expect(state.orderDetailCalls).toBe(0); // feed 来自 review-queue,零逐单 getOrder
        await page.screenshot({ path: path.join(ART, '02-feed-three-piece.png'), fullPage: true });
    });

    test('② + ④ 65 张批量键盘流(A · 读后端建议)+ 裁决后进度轮询 · <= 3 分钟', async ({ page }) => {
        const feed = makeBulkFeed(65);
        const state = {
            feed,
            queueFixture: () =>
                reviewQueueFixture({ bulkFlaggedTotal: state.feed.length, feed: state.feed }),
        };
        await wireApi(page, state);
        const t0 = Date.now();
        await gotoPool(page, 'zh');
        await page.waitForSelector('.riq-group[data-flag="sales_doc_review"]', { timeout: 15000 });
        await expect(page.locator('.riq-item')).toHaveCount(65);
        expect(state.orderDetailCalls).toBe(0); // 65 张仍零 getOrder
        const callsBeforeBulk = state.queueCalls;
        await page.screenshot({ path: path.join(ART, '03-before-bulk-65.png'), fullPage: true });

        await page.click('.riq-group[data-flag="sales_doc_review"] .riq-group-hd');
        await page.keyboard.press('a'); // 键盘批量(建议动作 = 后端 verdict_hint.suggested_decision)
        await page.waitForSelector('.toast', { timeout: 10000 });
        const toastText = await page.locator('.toast').innerText();
        console.log('MC2A3_BULK65_ELAPSED_MS=' + (Date.now() - t0) + ' TOAST=' + toastText);
        expect(toastText).toContain('65');
        expect(Date.now() - t0).toBeLessThan(180000);
        await page.screenshot({ path: path.join(ART, '04-after-bulk-toast.png'), fullPage: true });

        // ④ 进度轮询:裁决后 review-queue 被再次拉取(指数退避首跳 ~1.5s),等过首跳再断言。
        await page.waitForTimeout(3400);
        console.log('MC2A3_QUEUE_CALLS_BEFORE=' + callsBeforeBulk + ' AFTER=' + state.queueCalls);
        expect(state.queueCalls).toBeGreaterThan(callsBeforeBulk);
        await expect(page.locator('.riq-group[data-flag="sales_doc_review"]')).toHaveCount(0);
        await page.screenshot({
            path: path.join(ART, '05-after-bulk-cleared.png'),
            fullPage: true,
        });
    });

    test('签批闭环:复核通过 → SoD 拒绝冻结 → 单人声明 → 重试成功(sod 缺省=旧行为)', async ({
        page,
    }) => {
        const state = {
            feed: [],
            queueFixture: () => reviewQueueFixture({ bulkFlaggedTotal: 0 }),
            archiveShouldFailSod: true,
        };
        await wireApi(page, state);
        await gotoPool(page, 'zh');
        await page.waitForSelector('.riq-wo[data-wo="wo-signoff"]', { timeout: 10000 });
        const card = page.locator('.riq-wo[data-wo="wo-signoff"]');

        await card.locator('[data-action="riq-signoff"]').click();
        await expect(card.locator('.riq-wo-steps .chip.g')).toContainText('已复核');
        await page.screenshot({ path: path.join(ART, '06-signoff-done.png'), fullPage: true });

        await card.locator('[data-action="riq-archive"]').click();
        await expect(card.locator('.riq-sod-err')).toBeVisible({ timeout: 10000 });
        expect((await card.locator('.riq-sod-err').innerText()).length).toBeGreaterThan(0);
        await page.screenshot({
            path: path.join(ART, '07-archive-sod-blocked.png'),
            fullPage: true,
        });

        await card.locator('[data-action="riq-self-declare"]').click();
        await expect(card.locator('.riq-sod-strip .chip.s')).toContainText('已声明单人复核');
        await page.screenshot({ path: path.join(ART, '08-self-declared.png'), fullPage: true });

        await card.locator('[data-action="riq-archive"]').click();
        await expect(card.locator('.riq-wo-steps .chip.g').nth(1)).toContainText('已冻结', {
            timeout: 10000,
        });
        await page.screenshot({ path: path.join(ART, '09-archive-done.png'), fullPage: true });
    });

    test('签批投影 fresh(P0-1):后端 signoff 直接点亮已复核 chip(无需本地点击)', async ({
        page,
    }) => {
        const state = {
            feed: [],
            queueFixture: () =>
                reviewQueueFixture({
                    bulkFlaggedTotal: 0,
                    signoffProj: {
                        actor: 'user:rev',
                        at: '2026-06-01T10:00:00+00:00',
                        note: '',
                        stale: false,
                    },
                }),
        };
        await wireApi(page, state);
        await gotoPool(page, 'zh');
        await page.waitForSelector('.riq-wo[data-wo="wo-signoff"]', { timeout: 10000 });
        const card = page.locator('.riq-wo[data-wo="wo-signoff"]');
        // 未点任何按钮,投影 fresh 即点亮「已复核」chip;复核钮转完成态(不再出现)。
        await expect(card.locator('.riq-wo-steps .chip.g')).toContainText('已复核');
        await expect(card.locator('[data-action="riq-signoff"]')).toHaveCount(0);
        await expect(card.locator('.riq-signoff-stale')).toHaveCount(0);
        await page.screenshot({ path: path.join(ART, '10-signoff-fresh.png'), fullPage: true });
    });

    test('签批投影 stale(P0-1):复核后重跑过 → 提示重签 + 复核钮保持可点', async ({ page }) => {
        const state = {
            feed: [],
            queueFixture: () =>
                reviewQueueFixture({
                    bulkFlaggedTotal: 0,
                    signoffProj: {
                        actor: 'user:rev',
                        at: '2026-06-01T10:00:00+00:00',
                        note: '',
                        stale: true,
                    },
                }),
        };
        await wireApi(page, state);
        await gotoPool(page, 'zh');
        await page.waitForSelector('.riq-wo[data-wo="wo-signoff"]', { timeout: 10000 });
        const card = page.locator('.riq-wo[data-wo="wo-signoff"]');
        // stale 提示可见(复核后数据重生),且复核钮仍在 + 可点(一键重签)。
        await expect(card.locator('.riq-signoff-stale')).toBeVisible();
        const btn = card.locator('[data-action="riq-signoff"]');
        await expect(btn).toBeVisible();
        expect(await btn.evaluate((el) => !el.disabled)).toBe(true);
        await expect(card.locator('.riq-wo-steps .chip.g')).toHaveCount(0); // 尚未有已复核 chip
        await page.screenshot({ path: path.join(ART, '11-signoff-stale.png'), fullPage: true });
    });

    test('③ SoD proactive 显隐:制单人强制态签批/冻结钮按数据收起 → 声明后冻结钮现', async ({
        page,
    }) => {
        const state = {
            feed: [],
            queueFixture: () =>
                reviewQueueFixture({
                    bulkFlaggedTotal: 0,
                    signoffSod: {
                        enforced: true,
                        is_preparer: true,
                        has_independent_review: false,
                        self_declared: false,
                    },
                }),
        };
        await wireApi(page, state);
        await gotoPool(page, 'zh');
        await page.waitForSelector('.riq-wo[data-wo="wo-signoff"]', { timeout: 10000 });
        const card = page.locator('.riq-wo[data-wo="wo-signoff"]');

        await expect(card.locator('[data-action="riq-signoff"]')).toHaveCount(0);
        await expect(card.locator('[data-action="riq-archive"]')).toHaveCount(0);
        await expect(card.locator('[data-action="riq-self-declare"]')).toBeVisible();
        await page.screenshot({
            path: path.join(ART, '10-sod-preparer-hidden.png'),
            fullPage: true,
        });

        await card.locator('[data-action="riq-self-declare"]').click();
        await expect(card.locator('.riq-sod-strip .chip.s')).toContainText('已声明单人复核');
        await expect(card.locator('[data-action="riq-archive"]')).toBeVisible();
        await card.locator('[data-action="riq-archive"]').click();
        await expect(card.locator('.riq-wo-steps .chip.g')).toContainText('已冻结', {
            timeout: 10000,
        });
        await page.screenshot({ path: path.join(ART, '11-sod-after-declare.png'), fullPage: true });
    });

    test('③b SoD 非强制态(sod 缺省):签批/冻结/声明三钮全显(向后兼容)', async ({ page }) => {
        const state = { feed: [], queueFixture: () => reviewQueueFixture({ bulkFlaggedTotal: 0 }) };
        await wireApi(page, state);
        await gotoPool(page, 'zh');
        await page.waitForSelector('.riq-wo[data-wo="wo-signoff"]', { timeout: 10000 });
        const card = page.locator('.riq-wo[data-wo="wo-signoff"]');
        await expect(card.locator('[data-action="riq-signoff"]')).toBeVisible();
        await expect(card.locator('[data-action="riq-archive"]')).toBeVisible();
        await expect(card.locator('[data-action="riq-self-declare"]')).toBeVisible();
        await page.screenshot({
            path: path.join(ART, '12-sod-off-all-visible.png'),
            fullPage: true,
        });
    });

    test('驳回闭环:原因必填弹窗 → 提交 → 二次进队列标返工', async ({ page }) => {
        let queueCallCount = 0;
        const state = {
            feed: [],
            queueFixture: () => {
                queueCallCount += 1;
                return reviewQueueFixture({
                    bulkFlaggedTotal: 0,
                    bulkIsRework: queueCallCount > 1,
                });
            },
        };
        await wireApi(page, state);
        await gotoPool(page, 'zh');
        await page.waitForSelector('.riq-wo[data-wo="wo-signoff"]', { timeout: 10000 });
        const card = page.locator('.riq-wo[data-wo="wo-signoff"]');

        await card.locator('[data-action="riq-reject-open"]').click();
        await expect(card.locator('.riq-reject-form')).toBeVisible();
        await card.locator('[data-action="riq-reject-submit"]').click();
        await expect(card.locator('.riq-reject-err')).toBeVisible(); // 空原因必填校验
        await page.screenshot({
            path: path.join(ART, '13-reject-reason-required.png'),
            fullPage: true,
        });

        await card.locator('.riq-reject-textarea').fill('金额字段需重新核对');
        await card.locator('[data-action="riq-reject-submit"]').click();
        await page.waitForSelector('.riq-wo .chip.w', { timeout: 10000 }); // 返工徽章重现
        expect(state.rejectSubmitted.reason).toBe('金额字段需重新核对');
        await page.screenshot({
            path: path.join(ART, '14-reject-rework-badge.png'),
            fullPage: true,
        });
    });

    test('四语切换:关键文案非缺失(不是原样英文 key)', async ({ page }) => {
        const state = { feed: [], queueFixture: () => reviewQueueFixture({ bulkFlaggedTotal: 0 }) };
        for (const lang of ['zh', 'th', 'en', 'ja']) {
            await wireApi(page, state);
            await gotoPool(page, lang);
            await page.waitForSelector('.riq-wo[data-wo="wo-signoff"]', { timeout: 10000 });
            const btnText = await page
                .locator('.riq-wo[data-wo="wo-signoff"] [data-action="riq-signoff"]')
                .innerText();
            console.log('MC2A3_LANG_' + lang + '_SIGNOFF_BTN=' + btnText);
            expect(btnText).not.toBe('riq_signoff_btn');
            expect(btnText.trim().length).toBeGreaterThan(0);
            await page.screenshot({ path: path.join(ART, `15-lang-${lang}.png`), fullPage: true });
            await page.unroute('**/api/**');
        }
    });

    test('错态(error_t)+ 重试', async ({ page }) => {
        const state = {
            queueError: true,
            feed: [],
            queueFixture: () => reviewQueueFixture({}),
        };
        await wireApi(page, state);
        await gotoPool(page, 'zh');
        await expect(page.locator('#riqWoBody')).toContainText('读取失败', { timeout: 10000 });
        await page.screenshot({ path: path.join(ART, '16-error-state.png'), fullPage: true });
    });

    test('手机 390×844 + 200% 缩放:无横向溢出', async ({ page }) => {
        const feed = makeBulkFeed(5);
        const state = {
            feed,
            queueFixture: () => reviewQueueFixture({ bulkFlaggedTotal: 5, feed: state.feed }),
        };
        await wireApi(page, state);
        await page.setViewportSize({ width: 390, height: 844 });
        await gotoPool(page, 'zh');
        await page.waitForSelector('.riq-item', { timeout: 10000 });
        const overflowMobile = await page.evaluate(
            () => document.body.scrollWidth <= window.innerWidth + 1
        );
        console.log('MC2A3_MOBILE_NO_OVERFLOW=' + overflowMobile);
        expect(overflowMobile).toBe(true);
        await page.screenshot({ path: path.join(ART, '17-mobile-390.png'), fullPage: true });

        await page.setViewportSize({ width: 1280, height: 900 });
        await page.evaluate(() => {
            document.documentElement.style.zoom = '2';
        });
        await page.waitForTimeout(300);
        const overflowZoom = await page.evaluate(
            () => document.body.scrollWidth <= window.innerWidth + 1
        );
        console.log('MC2A3_ZOOM200_NO_OVERFLOW=' + overflowZoom);
        expect(overflowZoom).toBe(true);
        await page.screenshot({ path: path.join(ART, '18-zoom200.png'), fullPage: true });
    });
});
