// A-1 · 系统补的那行折扣要在审核队列里说人话 · 本地 stub 真浏览器验收
// ============================================================
// 起法同 _mc1b2_review_inbox_verify.spec.js:_local_static_server 起静态服(真 ai.js/ai.css/
// ai.html)+ page.route 桩 /api/**。真 DOM / 真 CSS / 真渲染,只桩网络层。
//
// 背景:sanity.infer_missing_discount 把「小计+VAT−总额」的差额当成漏抓的折扣回填进发票,
// 回填后勾稽闸自动放行(单测 test_ocr_discount_inferred_gate 已把这条事实钉成断言)。修前
// 工单侧只能靠回填文案里的「折」字撞进 classify._MATH_HINTS,人看到的是「票面自身不自洽」
// —— 可那三个数在回填后明明是平的,会计照着核对必然扑空。
//
// 本 spec 验修后的读侧呈现:① flag 标签是人话不是裸键 ② 判据副行说得出补了多少钱
// ③ 严重度红 ④ 不给「按建议处理」的安全默认(不许替人认下系统自己补的数字)⑤ 四语不裸 key。
// 截图存 tests/e2e/_artifacts/a1/。
/* global window, document */
const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8994;
const BASE = `http://127.0.0.1:${PORT}`;
const PAGE = BASE + '/static/dist/ai.html';
const ART = path.join(__dirname, '_artifacts', 'a1');

let server;
test.beforeAll(async () => {
    server = await localServer.start(PORT);
});
test.afterAll(() => localServer.stop(server));

function fakeToken() {
    const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
    return (
        b64({ alg: 'none' }) + '.' + b64({ sub: 'u-a1', email: 'reviewer@pearnly.test' }) + '.sig'
    );
}

// f003 真案的读数:回填后 5210 − 140 + 354.90 = 5424.90 三数已平 —— 正因为平,
// 「数字不自洽」那套话术在这张票上是错的。
const OCR_READ = {
    seller_tax: '0105558123456',
    subtotal: '5210.00',
    vat: '354.90',
    total_amount: '5424.90',
    discount: '140.00',
    invoice_number: 'INV2026030003',
};

// 后端 verdict.hint(flag_reason='discount_inferred') 的原样输出(services/workorder/verdict.py
// 的 _MAP:LOW 置信 / SEV_CRIT / suggested_decision=None)。
const ITEM = {
    item_id: 'it-disc-1',
    file_ref: 'C:/data/wo-a1/IMG_2647.jpg',
    kind: 'purchase_invoice',
    flag_reason: 'discount_inferred',
    ocr_read: OCR_READ,
    decision: null,
    verdict_hint: {
        narrative_key: 'verdict_discount_inferred',
        params: { discount: '140.00' },
        confidence: 'low',
        severity: 'crit',
        suggested_decision: null,
    },
    work_order_id: 'wo-a1',
    client_name: 'Sister Makeup',
    period: '2569-05',
};

function reviewQueueFixture() {
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
                        work_order_id: 'wo-a1',
                        workspace_client_id: 1,
                        client_name: 'Sister Makeup',
                        client_tax_id: '0105555167627',
                        period: '2569-05',
                        status: 'stuck',
                        current_step: 'reconcile',
                        updated_at: '2026-07-20T10:00:00+07:00',
                        next_due_efiling: '2569-06-15',
                        next_due_paper: '2569-06-07',
                        pool_pending: 0,
                        is_rework: false,
                        flagged_groups: [
                            { flag_reason: 'discount_inferred', severity: 'crit', count: 1 },
                        ],
                        flagged_total: 1,
                        top_severity: 'crit',
                    },
                ],
            },
        ],
        flagged_items: [ITEM],
        counts: { clients: 1, orders: 1, flagged: 1 },
    };
}

async function wireApi(page) {
    await page.route('**/api/**', async (route) => {
        const p = new URL(route.request().url()).pathname;
        if (p === '/api/ai/session') return route.fulfill({ json: { ok: true } });
        if (p === '/api/me')
            return route.fulfill({ json: { id: 'u-a1', username: 'reviewer', role: 'owner' } });
        if (p === '/api/workorder/orders')
            return route.fulfill({ json: { orders: [], count: 0, limit: 1, offset: 0 } });
        if (p === '/api/workorder/review-queue')
            return route.fulfill({ json: reviewQueueFixture() });
        if (p === '/api/ai/client-pool') return route.fulfill({ json: { groups: [] } });
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
    await page.waitForSelector('.riq-item', { timeout: 10000 });
}

test.describe('A-1 · 系统补的折扣行在审核队列里的呈现', () => {
    test('判据副行说出补了多少钱 · 不说「票面自身不自洽」', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await wireApi(page);
        await gotoPool(page, 'zh');

        const item = page.locator('.riq-item').first();
        await expect(item).toBeVisible();
        await page.screenshot({ path: path.join(ART, 'zh-queue.png'), fullPage: true });

        const narrative = await item.locator('.riq-narrative').innerText();
        expect(narrative).toContain('140.00'); // 改了多少钱必须说出来,否则无从核对
        expect(narrative).toContain('折扣');
        expect(narrative).not.toContain('verdict_'); // 不裸 i18n key
        expect(narrative).not.toContain('不自洽'); // 回填后三数已平,这话在本票上是错的

        const text = await item.innerText();
        expect(text).not.toContain('discount_inferred'); // 不把后端原始键糊给会计
    });

    test('严重度红 + 不提供「按建议处理」的安全默认', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await wireApi(page);
        await gotoPool(page, 'zh');

        // 严重度取后端 verdict_hint.severity(政策单一事实源 verdict.py)→ 分组头 chip 走
        // crit 的 `b` 档。类名在不算数,配色必须真落到像素上。
        const chip = page.locator('.riq-group-hd .chip').first();
        await expect(chip).toBeVisible();
        const chipStyle = await chip.evaluate((el) => {
            const cs = window.getComputedStyle(el);
            return { cls: el.className, bg: cs.backgroundColor, color: cs.color };
        });
        expect(chipStyle.cls).toContain('b');
        expect(chipStyle.bg).not.toBe('rgba(0, 0, 0, 0)');

        // suggested_decision=null → 分组头不给「N 张全部按建议处理」,只给逐张审的说明。
        // 系统自己补的数字,不许被一键替人认下。
        await expect(page.locator('.riq-group-bulk')).toHaveCount(0);
        await expect(page.locator('.riq-group-manual')).toBeVisible();

        // 分组头文案(riq_group_hd_manual)本就只报「N 张同类·逐张审」不带判据名,判据在
        // 卡片 narrative 上(上一个用例已验)。这里只守住:后端原始键不许漏到分组头。
        const head = await page.locator('.riq-group-hd').first().innerText();
        expect(head).not.toContain('discount_inferred');
        expect(head).not.toContain('rv_flag_');
        await page.screenshot({ path: path.join(ART, 'zh-group-head.png'), fullPage: true });
    });

    test('四语都不裸 key', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        for (const lang of ['zh', 'th', 'en', 'ja']) {
            await wireApi(page);
            await gotoPool(page, lang);
            const text = await page.locator('.riq-item').first().innerText();
            expect(text).not.toContain('verdict_');
            expect(text).not.toContain('rv_flag_');
            expect(text).not.toContain('riq_expl_');
            expect(text).not.toContain('discount_inferred');
            expect(text).toContain('140.00');
            await page.screenshot({ path: path.join(ART, `lang-${lang}.png`) });
        }
    });

    test('手机端不横向溢出', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await wireApi(page);
        await gotoPool(page, 'zh');
        await expect(page.locator('.riq-item').first()).toBeVisible();
        const overflow = await page.evaluate(
            () => document.documentElement.scrollWidth > window.innerWidth + 1
        );
        expect(overflow).toBe(false);
        await page.screenshot({ path: path.join(ART, 'mobile.png'), fullPage: true });
    });
});
