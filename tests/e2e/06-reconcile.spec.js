// Pearnly E2E · 06/07 对账中心入口(销项税核查 + 收入对账)· REFACTOR-D1
// ============================================================
// 进对账中心,分别切到「销项税报告核查」(sale-vat)与「收入对账」(gl-vat)tab:
//   - pane 渲染 · 上传 / 对账入口可见
// 边界:绝不点拖拽区(会弹系统文件选择器)· 绝不点「开始对账」· 不真跑对账(会扣费 / 造记录)。
//      到此为止——上传/对账入口元素可见即达标。
// ============================================================

const { test, expect } = require('@playwright/test');
const { hasCreds, ensureStorageState, STORAGE_STATE } = require('./_helpers/auth');
const { enterApp, openRoute } = require('./_helpers/app');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

test.describe('对账中心入口', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');
    test.use({ storageState: STORAGE_STATE });
    test.beforeAll(async ({ browser }) => {
        await ensureStorageState(browser);
    });

    test('06 · 销项税报告核查入口渲染 + 上传区可见(不真跑)', async ({ page }) => {
        const guard = attachConsoleGuard(page);
        await enterApp(page);
        await openRoute(page, 'reconcile');

        // 切「销项税报告核查」tab
        await page.locator('[data-recon-tab="sale-vat"]').click();
        await expect(page.locator('#recon-pane-sale-vat'), 'sale-vat pane 显示').toBeVisible();

        // 上传入口(销售发票 + VAT 报告)· 只看可见 · 不点(点会弹文件选择器)
        await expect(page.locator('#vex-drop-invoice'), '销售发票上传区').toBeVisible();
        await expect(page.locator('#vex-drop-report'), 'VAT 报告上传区').toBeVisible();
        // 对账入口按钮在(无文件时 disabled · 仅验存在可见 · 不点)
        await expect(page.locator('#vex-build'), '「开始对账」入口').toBeVisible();

        assertNoConsoleErrors(expect, guard);
    });

    test('07 · 收入对账入口渲染 + 对账入口可见(不真跑)', async ({ page }) => {
        const guard = attachConsoleGuard(page);
        await enterApp(page);
        await openRoute(page, 'reconcile');

        // 切「收入对账」tab
        await page.locator('[data-recon-tab="gl-vat"]').click();
        await expect(page.locator('#recon-pane-gl-vat'), 'gl-vat pane 显示').toBeVisible();

        // 上传入口(销项税报告 + 总账 GL)+ KPI 条 · 只看可见 · 不点
        await expect(page.locator('#glv-drop-vat'), '销项税报告上传区').toBeVisible();
        await expect(page.locator('#glv-drop-gl'), '总账 GL 上传区').toBeVisible();
        await expect(page.locator('#glv-kpi-strip'), '收入对账 KPI 条').toBeVisible();

        assertNoConsoleErrors(expect, guard);
    });
});
