// B-1 · 认不出类别的表格不许无痕当销项汇总收 · 本地 stub 真浏览器验收
// ============================================================
// 桩引导复用 _review_queue_stub.js(与 _a1/_a2/_a4/_b5/_b2 同一份)。
//
// 背景:表格类文件在 GL、银行两家判据都落空后一律兜底归销项汇总,且 flag_reason 为空。
// 兜底本身多半对(会计上传的就是它),但此前没有任何「这是不是销项汇总」的正面判据 ——
// 一份表头没被认出来的 GL 或银行流水走的是同一条路,它的数字直接进 R2 销售额且不留痕。
// 修后:三家都不像 = 盲猜 → 仍归销项汇总(下游口径不变)但标 flagged 要人确认一次。
//
// 本 spec 验读侧呈现:① 件进队列 ② 卡上说清「这是猜的」与猜错的后果 ③ 汇总表没有票面
// 钱字段 → 不摆读值表、给单键确认 ④ 无批量安全默认 ⑤ 四语不裸 key。
// 截图存 tests/e2e/_artifacts/b1/。
/* global window, document */
const { test, expect } = require('@playwright/test');
const path = require('path');
const stub = require('./_review_queue_stub');

// 后端 sort._bin_by_file 落的件形态:kind 仍是 sales_summary,但 status=flagged 带判据。
const ITEM = {
    item_id: 'it-tbl-1',
    kind: 'sales_summary',
    status: 'flagged',
    flag_reason: 'table_kind_unclear:xlsx',
    original_name: 'export_2569_05.xlsx',
    ocr_read: {},
    decision: null,
    verdict_hint: {
        narrative_key: 'verdict_table_kind_unclear',
        params: {},
        confidence: 'low',
        severity: 'crit',
        suggested_decision: null,
    },
    work_order_id: 'wo-b1',
    client_name: 'Sister Makeup',
    period: '2569-05',
};

const H = stub.harness(8991, 'b1', ITEM, 'wo-b1');

let server;
test.beforeAll(async () => {
    server = await H.start();
});
test.afterAll(() => H.stop(server));

test.describe('B-1 · 认不出类别的表格在审核队列里的呈现', () => {
    test('件进队列 · 说清「这是猜的」以及猜错会把数字当成销售额', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await H.boot(page, 'zh');

        const item = page.locator('.riq-item').first();
        await expect(item).toBeVisible();
        await page.screenshot({ path: path.join(H.ART, 'zh-queue.png'), fullPage: true });

        const narrative = await item.locator('.riq-narrative').innerText();
        expect(narrative).toContain('猜'); // 是猜测不是判断,必须说出来
        expect(narrative).toContain('销售额'); // 猜错的后果
        expect(narrative).toContain('总账'); // 猜错可能是什么
        expect(narrative).not.toContain('verdict_');

        const text = await item.innerText();
        expect(text).not.toContain('table_kind_unclear');

        const chipText = await page.locator('.riq-wo-flags .chip').first().innerText();
        expect(chipText).not.toContain('table_kind_unclear');
        expect(chipText).toContain('表');
    });

    test('汇总表没有票面钱字段 → 不摆读值表,动作是单键确认', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await H.boot(page, 'zh');

        // 一列「—」的读值表对一份表格文件毫无意义(A-4 同款教训)。
        await expect(page.locator('.riq-item .riq-fldt')).toHaveCount(0);

        const labels = await page.locator('.riq-item .riq-item-actions button').allInnerTexts();
        const joined = labels.join('|');
        expect(joined).not.toMatch(/采纳票面|改数/);
        expect(joined).toContain('确认');
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
            expect(narrative, `lang=${lang}`).not.toContain('verdict_table_kind_unclear');
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
