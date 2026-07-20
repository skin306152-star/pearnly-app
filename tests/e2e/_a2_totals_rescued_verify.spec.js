// A-2 · 第二个模型重读出来的钱要在审核队列里说清楚 · 本地 stub 真浏览器验收
// ============================================================
// 桩引导复用 _review_queue_stub.js(与 _a1_discount_inferred_verify.spec.js 同一份)。
//
// 背景:L3 视觉复读失败后,totals_rescue 让第二个模型窄口径重读四个金额并整体替换。修前
// 那条成功分支是 page_runner 里唯一不设 needs_manual_review 的出口、warnings 也为空,
// 工单侧因此拿到 flag_reason=None —— 钱面四数换过一双眼睛就直接进 R1 合计,签字页上
// 一个字都看不到(复现口径见 scratchpad/repro_a2.py:救援成功反而比救援失败更危险)。
//
// 本 spec 验修后的读侧呈现:① 卡上说得出重读后的三个数 ② 明说「只验过算术能对上」
// ③ 严重度红 ④ 不给批量安全默认 ⑤ 四语不裸 key。截图存 tests/e2e/_artifacts/a2/。
/* global window, document */
const { test, expect } = require('@playwright/test');
const path = require('path');
const stub = require('./_review_queue_stub');

// NBC 折扣票实案(tests/unit/test_page_runner_totals_rescue.py 的夹具):第一次读成
// 53129.00/4060.05/57189.05(自洽却整体错),第二个模型重读成下面这三个数。
const ITEM = {
    item_id: 'it-rescue-1',
    file_ref: 'C:/data/wo-a2/NBC_57016198.jpg',
    kind: 'purchase_invoice',
    flag_reason: 'totals_rescued',
    ocr_read: {
        seller_tax: '0105558123456',
        subtotal: '58129.35',
        vat: '4069.05',
        total_amount: '62198.40',
        invoice_number: 'NBC-57016198',
    },
    decision: null,
    // 后端 verdict.hint(flag_reason='totals_rescued') 原样输出(verdict.py 的 _MAP)。
    verdict_hint: {
        narrative_key: 'verdict_totals_rescued',
        params: { net: '58129.35', vat: '4069.05', total: '62198.40' },
        confidence: 'low',
        severity: 'crit',
        suggested_decision: null,
    },
    work_order_id: 'wo-a2',
    client_name: 'Sister Makeup',
    period: '2569-05',
};

const H = stub.harness(8995, 'a2', ITEM, 'wo-a2');

let server;
test.beforeAll(async () => {
    server = await H.start();
});
test.afterAll(() => H.stop(server));

test.describe('A-2 · 换过眼睛的钱数在审核队列里的呈现', () => {
    test('卡上说出重读后的三个数 · 并说明只验过算术', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await H.boot(page, 'zh');

        const item = page.locator('.riq-item').first();
        await expect(item).toBeVisible();
        await page.screenshot({ path: path.join(H.ART, 'zh-queue.png'), fullPage: true });

        const narrative = await item.locator('.riq-narrative').innerText();
        // 人要核的就是这三个数,不摆出来「请核对」是空话。
        expect(narrative).toContain('58129.35');
        expect(narrative).toContain('4069.05');
        expect(narrative).toContain('62198.40');
        // 「自洽」不等于「读对」这层意思必须写在脸上,否则会计以为系统验过了。
        expect(narrative).toContain('第二个模型');
        expect(narrative).not.toContain('verdict_');

        const text = await item.innerText();
        expect(text).not.toContain('totals_rescued');
    });

    test('严重度红 + 不提供「按建议处理」的安全默认', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await H.boot(page, 'zh');

        const chip = page.locator('.riq-group-hd .chip').first();
        await expect(chip).toBeVisible();
        const style = await chip.evaluate((el) => {
            const cs = window.getComputedStyle(el);
            return { cls: el.className, bg: cs.backgroundColor };
        });
        expect(style.cls).toContain('b');
        expect(style.bg).not.toBe('rgba(0, 0, 0, 0)');

        await expect(page.locator('.riq-group-bulk')).toHaveCount(0);
        await expect(page.locator('.riq-group-manual')).toBeVisible();
    });

    test('四语都不裸 key', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        for (const lang of ['zh', 'th', 'en', 'ja']) {
            await H.boot(page, lang);
            const text = await page.locator('.riq-item').first().innerText();
            expect(text).not.toContain('verdict_');
            expect(text).not.toContain('rv_flag_');
            expect(text).not.toContain('riq_expl_');
            expect(text).not.toContain('totals_rescued');
            expect(text).toContain('58129.35');
            await page.screenshot({ path: path.join(H.ART, `lang-${lang}.png`) });
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
