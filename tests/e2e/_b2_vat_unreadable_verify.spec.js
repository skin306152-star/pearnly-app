// B-2/B-3 · 票面 VAT 读不出的票要交人定向,不许当「没有 VAT」静默排掉 · 真浏览器验收
// ============================================================
// 桩引导复用 _review_queue_stub.js(与 _a1/_a2/_a4/_b5 同一份)。
//
// 背景:sort._has_vat 把「VAT 读不出」与「本来就没有 VAT」都归成 False,于是读花一个字符
// (7O.00)的税票会走两个静默出口 —— 判成银行流水页,或判成无税务要素的 non_tax 再被
// classify 无条件 status=excluded(B-3:零人复核的自动终态)。进项税就这么消失。
// 修后:kind=unknown + vat_unreadable 走既有方向裁决通道(P/S/X),无裁决 R1 停机点名。
//
// 本 spec 验读侧呈现:① 件进队列 ② 卡上说清「读不出 ≠ 没有」以及按没有处理的后果
// ③ 给的是方向三键不是金额三键 ④ 无批量安全默认 ⑤ 四语不裸 key。
// 截图存 tests/e2e/_artifacts/b2/。
/* global window, document */
const { test, expect } = require('@playwright/test');
const path = require('path');
const stub = require('./_review_queue_stub');

// 后端 sort.bin_ocr_fields 落的件形态:kind=unknown + 方向通道 reason(尾巴是 document_type)。
const ITEM = {
    item_id: 'it-vatunread-1',
    kind: 'unknown',
    status: 'flagged',
    flag_reason: 'vat_unreadable:receipt',
    original_name: 'IMG_2647.jpg',
    ocr_read: {
        subtotal: '1428.57',
        vat: '7O.00',
        total_amount: '1498.57',
        seller_tax: '0735527000289',
        vendor: 'NBC Trading',
    },
    decision: null,
    // 后端 verdict.hint(flag_reason='vat_unreadable:receipt') 原样输出。
    verdict_hint: {
        narrative_key: 'verdict_vat_unreadable',
        params: { seller_tax: '0735527000289', vendor: 'NBC Trading' },
        confidence: 'low',
        severity: 'crit',
        suggested_decision: null,
    },
    work_order_id: 'wo-b2',
    client_name: 'Sister Makeup',
    period: '2569-05',
};

const H = stub.harness(8992, 'b2', ITEM, 'wo-b2');

let server;
test.beforeAll(async () => {
    server = await H.start();
});
test.afterAll(() => H.stop(server));

test.describe('B-2/B-3 · VAT 读不出的票在审核队列里的呈现', () => {
    test('件进队列 · 说清「读不出 ≠ 没有」以及按没有处理会丢进项税', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await H.boot(page, 'zh');

        const item = page.locator('.riq-item').first();
        await expect(item).toBeVisible();
        await page.screenshot({ path: path.join(H.ART, 'zh-queue.png'), fullPage: true });

        const narrative = await item.locator('.riq-narrative').innerText();
        expect(narrative).toContain('读不出'); // 病根说出来
        expect(narrative).toContain('没有 VAT'); // 「不能当没有处理」这层意思
        expect(narrative).toContain('进项税'); // 说清后果:钱会丢
        expect(narrative).not.toContain('verdict_');

        const text = await item.innerText();
        expect(text).not.toContain('vat_unreadable'); // 机器名不甩给会计

        const chipText = await page.locator('.riq-wo-flags .chip').first().innerText();
        expect(chipText).not.toContain('vat_unreadable');
        expect(chipText).toContain('VAT');
    });

    test('给的是方向三键(P/S/X)不是金额三键 —— 方向都判不了,谈不上采纳票面', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await H.boot(page, 'zh');

        const labels = await page.locator('.riq-item .riq-item-actions button').allInnerTexts();
        const joined = labels.join('|');
        expect(joined).not.toContain('采纳票面');
        expect(joined).toContain('进项');
        expect(joined).toContain('销项');
    });

    test('未裁决前签批冻结被挡住 + 无批量安全默认', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await H.boot(page, 'zh');

        const freeze = page.locator('[data-action="riq-archive"]').first();
        await expect(freeze).toBeVisible();
        const state = await freeze.evaluate((el) => ({
            disabled: el.disabled || el.getAttribute('aria-disabled') === 'true',
            pointer: window.getComputedStyle(el).pointerEvents,
        }));
        expect(state.disabled || state.pointer === 'none').toBe(true);
        await expect(page.locator('.riq-group-bulk')).toHaveCount(0);
    });

    test('四语都不裸 key', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        for (const lang of ['zh', 'th', 'en', 'ja']) {
            await H.boot(page, lang);
            const narrative = await page.locator('.riq-item .riq-narrative').first().innerText();
            expect(narrative, `lang=${lang}`).not.toContain('verdict_vat_unreadable');
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
