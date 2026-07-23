// A-4 · 银行流水金额被余额链反推改写 → 必须进审核队列 · 本地 stub 真浏览器验收
// ============================================================
// 桩引导复用 _review_queue_stub.js(与 _a1/_a2 同一份)。
//
// 背景:_repair_amount_from_balance 在差异 ≤30% 时把行金额改成反推值,同时把 balance_ok
// 由 False 翻 True。翻绿后该行退出所有「需人看」的口径 —— 修前件仍 status=ok,不进审核
// 队列、不挡签批,只剩 Excel 标黄与机器改动清单在「建议复核」。而这笔数正是销项倒推
// (÷1.07)与逐笔对账的基数。
//
// 本 spec 验修后的读侧呈现:① 件真进了队列 ② 卡上说得出被改了几行、且说明「不是读出来的」
// ③ 严重度红 ④ 不给批量安全默认(改过的钱不能一键放行)⑤ 四语不裸 key。
// 截图存 tests/e2e/_artifacts/a4/。
/* global window, document */
const { test, expect } = require('@playwright/test');
const path = require('path');
const stub = require('./_review_queue_stub');

// 后端 reconcile_bank._flag_if_amounts_rewritten 落的件形态:flag_reason 带改写行数。
const ITEM = {
    item_id: 'it-bank-1',
    kind: 'bank_statement',
    status: 'flagged',
    flag_reason: 'bank_amount_rewritten:2',
    original_name: 'KBANK-2569-05.pdf',
    ocr_read: {},
    decision: null,
    // 后端 verdict.hint(flag_reason='bank_amount_rewritten:2') 原样输出(verdict.py 的 _MAP)。
    verdict_hint: {
        narrative_key: 'verdict_bank_amount_rewritten',
        params: { rows: '2' },
        confidence: 'low',
        severity: 'crit',
        suggested_decision: null,
    },
    work_order_id: 'wo-a4',
    client_name: 'Sister Makeup',
    period: '2569-05',
};

const H = stub.harness(8994, 'a4', ITEM, 'wo-a4');

let server;
test.beforeAll(async () => {
    server = await H.start();
});
test.afterAll(() => H.stop(server));

test.describe('A-4 · 被改写过金额的银行件在审核队列里的呈现', () => {
    test('件进队列 · 说得出改了几行、且说明这数不是读出来的', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await H.boot(page, 'zh');

        const item = page.locator('.riq-item').first();
        await expect(item).toBeVisible();
        await page.screenshot({ path: path.join(H.ART, 'zh-queue.png'), fullPage: true });

        const narrative = await item.locator('.riq-narrative').innerText();
        expect(narrative).toContain('2 行'); // 改了几行,不说数字等于没说
        expect(narrative).toContain('不是读出来的'); // 这才是要人核的那件事
        expect(narrative).toContain('反推'); // 说清来路
        expect(narrative).not.toContain('verdict_'); // 不裸 key

        const text = await item.innerText();
        expect(text).not.toContain('bank_amount_rewritten'); // 机器名不甩给会计

        // 上一版这四条没断言,截图才发现界面不对(断言全绿≠界面对)。逐条钉死:
        // ① 工单卡的 chip 也要人话,不许把 flag_reason 原样糊脸
        const chipText = await page.locator('.riq-wo-flags .chip').first().innerText();
        expect(chipText).not.toContain('bank_amount_rewritten');
        expect(chipText).toContain('账单');
        // ② 银行件没有票面钱字段 → 不许摆那张只会渲染出一列「—」的读值表
        await expect(item.locator('.riq-fldt')).toHaveCount(0);
        // ③ 动作只有「确认」——「采纳票面」「改数」「剔除」对一份银行账单都不成立
        const actions = item.locator('.riq-item-actions button');
        const labels = await actions.allInnerTexts();
        expect(labels.join('|')).not.toMatch(/采纳票面|改数|剔除/);
        expect(labels.join('|')).toContain('确认');
    });

    test('未裁决前签批冻结被挡住(这条闸就是 A-4 要补的牙齿)', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await H.boot(page, 'zh');

        // 「签批冻结」= riq-archive(冻结归档),不是想当然的 wo-freeze。
        const freeze = page.locator('[data-action="riq-archive"]').first();
        await expect(freeze).toBeVisible();
        const state = await freeze.evaluate((el) => ({
            disabled: el.disabled || el.getAttribute('aria-disabled') === 'true',
            pointer: window.getComputedStyle(el).pointerEvents,
        }));
        expect(state.disabled || state.pointer === 'none').toBe(true);
        await expect(page.locator('.riq-wo-blocked-note')).toContainText('待裁决');
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

        // 改过的钱绝不能一键批量放行 —— 只留逐件人工出口。
        await expect(page.locator('.riq-group-bulk')).toHaveCount(0);
        await expect(page.locator('.riq-group-manual')).toBeVisible();
    });

    test('四语都不裸 key', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        for (const lang of ['zh', 'th', 'en', 'ja']) {
            await H.boot(page, lang);
            const narrative = await page.locator('.riq-item .riq-narrative').first().innerText();
            expect(narrative, `lang=${lang}`).not.toContain('verdict_bank_amount_rewritten');
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
