// Pearnly E2E · 21 销项开票向导「续步记忆」守门 · UI-UNIFY 模块3
// ============================================================
// 销项向导是全屏模态(window.openSalesWizard)。续步(src/home/sales-wizard.ts):
// 关掉向导(不清内存 st)再重开 → 回到离开的那一步;硬刷新后 st 已空 → 守门不过 → 全新单据。
//
// 本 spec 锁安全降级路径(确定性):新页面(内存无 st)即便有步号记忆,重开也必须从第 1 步开始
//   + 清记忆。正向(关掉再开回到原步)依赖向导交互,走人工 live 截图验。
// ============================================================

const { test, expect } = require('@playwright/test');
const { hasCreds, ensureStorageState, STORAGE_STATE } = require('./_helpers/auth');
const { enterApp } = require('./_helpers/app');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

const MEMO_KEY = 'pearnly_step_sales-wizard';

test.describe('销项开票向导 · 续步记忆守门', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');
    test.use({ storageState: STORAGE_STATE });
    test.beforeAll(async ({ browser }) => {
        await ensureStorageState(browser);
    });

    test('新页面有步号记忆但内存无 st → 重开回第 1 步并清记忆', async ({ page }) => {
        const guard = attachConsoleGuard(page);
        await enterApp(page);

        // 模拟「上次停在第 3 步」的残留记忆(本次是新页面,内存无 st → 不该复原到第 3 步)
        await page.evaluate(
            ([k]) => localStorage.setItem(k, JSON.stringify({ step: 3 })),
            [MEMO_KEY]
        );

        await page.evaluate(() => window.openSalesWizard && window.openSalesWizard());
        await expect(page.locator('.sw-stepper'), '向导步骤条渲染').toBeVisible({ timeout: 15_000 });

        const steps = page.locator('.sw-step');
        await expect(steps.nth(0), '第 1 步高亮(全新开始)').toHaveClass(/active/);
        await expect(page.locator('.sw-step.active'), '当前激活步唯一').toHaveCount(1);

        const memo = await page.evaluate(([k]) => localStorage.getItem(k), [MEMO_KEY]);
        expect(memo, '降级后记忆已清掉').toBeNull();

        assertNoConsoleErrors(expect, guard);
    });
});
