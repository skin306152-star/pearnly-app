// B-5 · 缺票号的疑似重复票要进队列交人裁,不许自动扔 · 本地 stub 真浏览器验收
// ============================================================
// 桩引导复用 _review_queue_stub.js(与 _a1/_a2/_a4 同一份)。
//
// 背景:防重指纹 = 税号|票号|含税合计。票号读不出时退化成「税号|空|金额」,同一供应商
// 开两张金额相同的票(月度固定费用/同款复购)会撞成同一枚。修前撞车即 status=excluded +
// flagged=false —— 真票的进项税被静默扔掉,且不进人审队列,没有任何人会知道。
//
// 本 spec 验修后的读侧呈现:① 件真进了队列 ② 卡上说清「认不准」而不是「重复」
// ③ 严重度红 ④ 不给批量安全默认(一键排除会把真票批量扔掉)⑤ 四语不裸 key。
// 截图存 tests/e2e/_artifacts/b5/。
/* global window, document */
const { test, expect } = require('@playwright/test');
const path = require('path');
const stub = require('./_review_queue_stub');

// 后端 classify 落的件形态:留在进项堆、flagged,尾巴带疑似撞上的那张原件名。
const ITEM = {
    item_id: 'it-dupsus-1',
    kind: 'purchase_invoice',
    status: 'flagged',
    flag_reason: 'duplicate_suspect:IMG_0001.jpg',
    original_name: 'IMG_0002.jpg',
    ocr_read: {
        subtotal: '467.29',
        vat: '32.71',
        total_amount: '500.00',
        invoice_number: '',
        seller_tax: '0735527000289',
    },
    decision: null,
    // 后端 verdict.hint(flag_reason='duplicate_suspect:IMG_0001.jpg') 原样输出。
    verdict_hint: {
        narrative_key: 'verdict_duplicate_suspect',
        params: { of: 'IMG_0001.jpg' },
        confidence: 'low',
        severity: 'crit',
        suggested_decision: null,
    },
    work_order_id: 'wo-b5',
    client_name: 'Sister Makeup',
    period: '2569-05',
};

const H = stub.harness(8993, 'b5', ITEM, 'wo-b5');

let server;
test.beforeAll(async () => {
    server = await H.start();
});
test.afterAll(() => H.stop(server));

test.describe('B-5 · 疑似重复(缺票号)在审核队列里的呈现', () => {
    test('件进队列 · 说清是「认不准」不是「重复」· 点名疑似撞上的那张', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await H.boot(page, 'zh');

        const item = page.locator('.riq-item').first();
        await expect(item).toBeVisible();
        await page.screenshot({ path: path.join(H.ART, 'zh-queue.png'), fullPage: true });

        const narrative = await item.locator('.riq-narrative').innerText();
        expect(narrative).toContain('IMG_0001.jpg'); // 疑似撞上的是哪张
        expect(narrative).toContain('票号'); // 说清认不准的原因
        expect(narrative).toContain('可能'); // 是「可能」不是断言重复
        expect(narrative).not.toContain('verdict_');

        const text = await item.innerText();
        expect(text).not.toContain('duplicate_suspect'); // 机器名不甩给会计

        // 工单卡 chip 也要人话。
        const chipText = await page.locator('.riq-wo-flags .chip').first().innerText();
        expect(chipText).not.toContain('duplicate_suspect');
        expect(chipText).toContain('疑似重复');
    });

    test('未裁决前签批冻结被挡住', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await H.boot(page, 'zh');
        const freeze = page.locator('[data-action="riq-archive"]').first();
        await expect(freeze).toBeVisible();
        const state = await freeze.evaluate((el) => ({
            disabled: el.disabled || el.getAttribute('aria-disabled') === 'true',
            pointer: window.getComputedStyle(el).pointerEvents,
        }));
        expect(state.disabled || state.pointer === 'none').toBe(true);
    });

    test('严重度红 + 不提供批量一键排除(会把真票整组扔掉)', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await H.boot(page, 'zh');

        const chip = page.locator('.riq-group-hd .chip').first();
        await expect(chip).toBeVisible();
        const cls = await chip.evaluate((el) => el.className);
        expect(cls).toContain('b');

        await expect(page.locator('.riq-group-bulk')).toHaveCount(0);
        await expect(page.locator('.riq-group-manual')).toBeVisible();

        // 进项票卡:读值表在场(这是真有票面钱字段的件,与银行件不同)。
        await expect(page.locator('.riq-item .riq-fldt')).toHaveCount(1);
    });

    test('四语都不裸 key', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        for (const lang of ['zh', 'th', 'en', 'ja']) {
            await H.boot(page, lang);
            const narrative = await page.locator('.riq-item .riq-narrative').first().innerText();
            expect(narrative, `lang=${lang}`).not.toContain('verdict_duplicate_suspect');
            expect(narrative.trim().length, `lang=${lang}`).toBeGreaterThan(20);
            await page.screenshot({ path: path.join(H.ART, `${lang}-queue.png`) });
        }
    });

    test('手机端不横向溢出', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await H.boot(page, 'zh');
        await expect(page.locator('.riq-item').first()).toBeVisible();
        const overflow = await page.evaluate(
            () => document.documentElement.scrollWidth > window.innerWidth + 1
        );
        expect(overflow).toBe(false);
        await page.screenshot({ path: path.join(H.ART, 'mobile.png'), fullPage: true });
    });
});
