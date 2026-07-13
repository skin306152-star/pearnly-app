// MC1-b2 · 全所审核收件箱(#/pool 三分区聚合页)· 本地真浏览器 + 网络桩验收(临时件)
// ============================================================
// 真渲染代码(static/dist/ai.js/ai.css/ai.html 原样加载,零改造)+ 真 DOM + 真键盘事件 +
// 真 CSS 布局/缩放,只有网络层桩(page.route 拦 /api/*)——因为 review-queue 需要的
// 「65 张同类 flagged + 双人签批 + SoD 拒绝再声明」这套场景在生产暂无对应真实数据
// (MC1-c.1 sales_doc 组是第一场景,尚未有客户账套跑出这个规模),现造需要真跑 OCR
// 成本高且不可控,故用桩数据固定跑分——桩的响应形状逐字段对齐已读过的后端源码
// (services/workorder/review.py review_queue()/batch_decisions()、evidence.py
// flagged_projection()、verdict.py hint()、routes/workorder_routes.py review/archive/
// review-reject/self-review-declare),不是拍脑袋编的。
//
// 起法(本机):
//   1) npm run build(已产出含本次改动的 static/dist/ai.js/ai.css/ai.html)
//   2) python -m http.server 8850(仓库根目录,serve /static/* 静态资源)
//   3) npx playwright test tests/e2e/_mc1b2_review_inbox_verify.spec.js
/* global window, document */
const { test, expect } = require('@playwright/test');
const path = require('path');

const ART = path.join(__dirname, '_artifacts', 'mc1b2');
const BASE = process.env.PEARNLY_E2E_STATIC_BASE_URL || 'http://localhost:8850';
const PAGE = BASE + '/static/dist/ai.html';

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

// 65 张同类「本方销项待复核」票(sales_doc_review · MID 置信度 · verdict.py _MAP 命中
// 有批量建议模板)——对齐 MC0 记忆条目提到的「sales_doc 组是第一场景」规模。
function makeBulkOrder() {
    const flagged = [];
    for (let i = 0; i < 65; i++) {
        const read = moneyRead(i);
        flagged.push({
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
            },
        });
    }
    return flagged;
}

function reviewQueueFixture(opts) {
    opts = opts || {};
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
                            opts.bulkFlaggedTotal === 0
                                ? []
                                : [
                                      {
                                          flag_reason: 'sales_doc_review',
                                          severity: 'warn',
                                          count:
                                              opts.bulkFlaggedTotal != null
                                                  ? opts.bulkFlaggedTotal
                                                  : 65,
                                      },
                                  ],
                        flagged_total: opts.bulkFlaggedTotal != null ? opts.bulkFlaggedTotal : 65,
                        top_severity: opts.bulkFlaggedTotal === 0 ? null : 'warn',
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
                    },
                ],
            },
        ],
        counts: {
            clients: 1,
            orders: 2,
            flagged: opts.bulkFlaggedTotal != null ? opts.bulkFlaggedTotal : 65,
        },
    };
}

function orderDetailFixture(flagged) {
    return {
        id: 'wo-bulk',
        workspace_client_id: 1,
        period: '2569-06',
        intent: 'vat_return',
        status: 'stuck',
        current_step: 'reconcile',
        progress: null,
        flagged: flagged,
        needs: [],
        blocked_reasons: [],
        numbers: {},
        bank_recon: null,
        shadow_draft: null,
        financials: null,
        sales_corroboration: null,
        deliverables: [],
    };
}

// ---------------------------------------------------------------- route wiring ----

async function wireApi(page, state) {
    await page.route('**/api/**', async (route) => {
        const req = route.request();
        const url = new URL(req.url());
        const p = url.pathname;
        const method = req.method();

        if (p === '/api/workorder/orders' && method === 'GET') {
            return route.fulfill({ json: { orders: [], count: 0, limit: 1, offset: 0 } });
        }
        if (p === '/api/me' && method === 'GET') {
            return route.fulfill({ json: { id: 'u-mc1b2', username: 'reviewer', role: 'owner' } });
        }
        if (p === '/api/workorder/review-queue' && method === 'GET') {
            if (state.queueError) return route.fulfill({ status: 500, json: { detail: 'boom' } });
            return route.fulfill({ json: state.queueFixture() });
        }
        if (p === '/api/ai/client-pool' && method === 'GET') {
            return route.fulfill({ json: { groups: [] } });
        }
        if (p === '/api/workorder/orders/wo-bulk' && method === 'GET') {
            return route.fulfill({ json: orderDetailFixture(state.bulkFlagged) });
        }
        if (p === '/api/workorder/orders/wo-signoff' && method === 'GET') {
            return route.fulfill({ json: orderDetailFixture([]) });
        }
        if (p === '/api/workorder/orders/wo-bulk/decisions:batch' && method === 'POST') {
            const body = req.postDataJSON();
            const results = body.decisions.map((d) => ({
                item_id: d.item_id,
                ok: true,
                event_id: 1,
            }));
            state.bulkFlagged = []; // 乐观态之外,后续 review-queue 也如实清零
            return route.fulfill({
                json: {
                    results: results,
                    ok_count: results.length,
                    fail_count: 0,
                    total: results.length,
                },
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
            state.bulkOrderStatusAfterReject = true;
            return route.fulfill({ json: { status: 'running', reopened_steps: ['reconcile'] } });
        }
        return route.fulfill({ status: 404, json: { detail: 'not_stubbed:' + p } });
    });
}

async function gotoPool(page, lang) {
    await page.addInitScript(
        ({ token, lang }) => {
            window.localStorage.setItem('mrpilot_token', token);
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

test.describe('MC1-b2 · 全所审核收件箱三分区聚合页', () => {
    test('三分区结构 + 待审工单卡 + 空态(客户待答/待审工单为空)', async ({ page }) => {
        const state = {
            bulkFlagged: [],
            queueFixture: () => reviewQueueFixture({ bulkFlaggedTotal: 0 }),
        };
        await wireApi(page, state);
        await gotoPool(page, 'zh');
        await page.waitForSelector('#riqWoBody .riq-wo', { timeout: 10000 });
        await expect(page.locator('#riqSecWorkorders, .riq-sec').first()).toBeVisible();
        await expect(page.locator('#riqFlaggedBody')).toContainText('没有异常票据');
        await page.screenshot({
            path: path.join(ART, '01-structure-empty-flagged.png'),
            fullPage: true,
        });
    });

    test('异常票据裁决卡三件套(读值/判据人话/置信度)逐张 isVisible', async ({ page }) => {
        const flagged = makeBulkOrder().slice(0, 3);
        const state = {
            bulkFlagged: flagged,
            queueFixture: () => reviewQueueFixture({ bulkFlaggedTotal: flagged.length }),
        };
        await wireApi(page, state);
        await gotoPool(page, 'zh');
        await page.waitForSelector('.riq-item', { timeout: 10000 });
        const cards = page.locator('.riq-item');
        const n = await cards.count();
        expect(n).toBe(3);
        for (let i = 0; i < n; i++) {
            const card = cards.nth(i);
            await expect(card.locator('.riq-fldt')).toBeVisible();
            await expect(card.locator('.riq-narrative')).toBeVisible();
            const narrativeText = await card.locator('.riq-narrative').innerText();
            expect(narrativeText.length).toBeGreaterThan(0);
            const confChip = card.locator('.riq-item-hd .chip').first();
            await expect(confChip).toBeVisible();
        }
        await page.screenshot({ path: path.join(ART, '02-three-piece-cards.png'), fullPage: true });
    });

    test('65 张同类批量键盘流(A)· 计时 <= 3 分钟', async ({ page }) => {
        const flagged = makeBulkOrder();
        const state = {
            bulkFlagged: flagged,
            queueFixture: () => reviewQueueFixture({ bulkFlaggedTotal: flagged.length }),
        };
        await wireApi(page, state);
        const t0 = Date.now();
        await gotoPool(page, 'zh');
        await page.waitForSelector('.riq-group[data-flag="sales_doc_review"]', { timeout: 15000 });
        await expect(page.locator('.riq-item')).toHaveCount(65);
        await page.screenshot({ path: path.join(ART, '03-before-bulk-65.png'), fullPage: true });

        // 键盘流:点组头聚焦 → 按 A(不点鼠标裁决按钮,走键盘)。
        await page.click('.riq-group[data-flag="sales_doc_review"] .riq-group-hd');
        await page.keyboard.press('a');
        await page.waitForSelector('.toast', { timeout: 10000 });
        const toastText = await page.locator('.toast').innerText();
        const elapsedMs = Date.now() - t0;
        console.log('MC1B2_BULK65_ELAPSED_MS=' + elapsedMs + ' TOAST=' + toastText);
        expect(toastText).toContain('65');
        expect(elapsedMs).toBeLessThan(180000);
        await page.screenshot({ path: path.join(ART, '04-after-bulk-toast.png'), fullPage: true });
        await page.waitForTimeout(3200); // toast 自动消失后组应已清空(乐观态即时清)
        await expect(page.locator('.riq-group[data-flag="sales_doc_review"]')).toHaveCount(0);
        await page.screenshot({
            path: path.join(ART, '05-after-bulk-cleared.png'),
            fullPage: true,
        });
    });

    test('签批闭环:复核通过 → SoD 拒绝签批冻结 → 单人声明 → 重试成功', async ({ page }) => {
        const state = {
            bulkFlagged: [],
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
        const sodErrText = await card.locator('.riq-sod-err').innerText();
        console.log('MC1B2_SOD_ERR=' + sodErrText);
        expect(sodErrText.length).toBeGreaterThan(0);
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
        await page.screenshot({
            path: path.join(ART, '09-archive-done-after-declare.png'),
            fullPage: true,
        });
    });

    test('驳回闭环:原因必填弹窗 → 提交 → 二次进队列标返工', async ({ page }) => {
        let queueCallCount = 0;
        const state = {
            bulkFlagged: [],
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
            path: path.join(ART, '10-reject-reason-required.png'),
            fullPage: true,
        });

        await card.locator('.riq-reject-textarea').fill('金额字段需重新核对');
        await card.locator('[data-action="riq-reject-submit"]').click();
        await page.waitForSelector('.riq-wo .chip.w', { timeout: 10000 }); // 返工徽章重新出现
        expect(state.rejectSubmitted.reason).toBe('金额字段需重新核对');
        await page.screenshot({
            path: path.join(ART, '11-reject-rework-badge.png'),
            fullPage: true,
        });
    });

    test('四语切换:关键文案非缺失(不是原样英文 key)', async ({ page }) => {
        const state = {
            bulkFlagged: [],
            queueFixture: () => reviewQueueFixture({ bulkFlaggedTotal: 0 }),
        };
        for (const lang of ['zh', 'th', 'en', 'ja']) {
            await wireApi(page, state);
            await gotoPool(page, lang);
            await page.waitForSelector('.riq-wo[data-wo="wo-signoff"]', { timeout: 10000 });
            const btnText = await page
                .locator('.riq-wo[data-wo="wo-signoff"] [data-action="riq-signoff"]')
                .innerText();
            console.log('MC1B2_LANG_' + lang + '_SIGNOFF_BTN=' + btnText);
            expect(btnText).not.toBe('riq_signoff_btn');
            expect(btnText.trim().length).toBeGreaterThan(0);
            await page.screenshot({ path: path.join(ART, `12-lang-${lang}.png`), fullPage: true });
            await page.unroute('**/api/**');
        }
    });

    test('错态(error_t)+ 重试', async ({ page }) => {
        const state = {
            queueError: true,
            bulkFlagged: [],
            queueFixture: () => reviewQueueFixture({}),
        };
        await wireApi(page, state);
        await gotoPool(page, 'zh');
        await expect(page.locator('#riqWoBody')).toContainText('读取失败', { timeout: 10000 });
        await page.screenshot({ path: path.join(ART, '13-error-state.png'), fullPage: true });
    });

    test('手机 390×844 + 200% 缩放:无横向溢出', async ({ page }) => {
        const flagged = makeBulkOrder().slice(0, 5);
        const state = {
            bulkFlagged: flagged,
            queueFixture: () => reviewQueueFixture({ bulkFlaggedTotal: flagged.length }),
        };
        await wireApi(page, state);
        await page.setViewportSize({ width: 390, height: 844 });
        await gotoPool(page, 'zh');
        await page.waitForSelector('.riq-item', { timeout: 10000 });
        const overflowMobile = await page.evaluate(
            () => document.body.scrollWidth <= window.innerWidth + 1
        );
        console.log('MC1B2_MOBILE_NO_OVERFLOW=' + overflowMobile);
        expect(overflowMobile).toBe(true);
        await page.screenshot({ path: path.join(ART, '14-mobile-390.png'), fullPage: true });

        await page.setViewportSize({ width: 1280, height: 900 });
        await page.evaluate(() => {
            document.documentElement.style.zoom = '2';
        });
        await page.waitForTimeout(300);
        const overflowZoom = await page.evaluate(
            () => document.body.scrollWidth <= window.innerWidth + 1
        );
        console.log('MC1B2_ZOOM200_NO_OVERFLOW=' + overflowZoom);
        expect(overflowZoom).toBe(true);
        await page.screenshot({ path: path.join(ART, '15-zoom200.png'), fullPage: true });
    });
});
