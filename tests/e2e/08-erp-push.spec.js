// Pearnly E2E · 08 ERP 推送入口 · REFACTOR-D1
// ============================================================
// 进集成页:ERP 卡片 + 「配置」入口可见 → 推送日志 tab 渲染 → 打开 ERP 配置抽屉(可见即关)。
// 边界:绝不真推 ERP(会往真 MR.ERP 写)· 只验入口 / 抽屉可见。推送日志只读拉取。
// ============================================================

const { test, expect } = require('@playwright/test');
const { hasCreds, ensureStorageState, STORAGE_STATE } = require('./_helpers/auth');
const { enterApp, openRoute } = require('./_helpers/app');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

test.describe('ERP 推送入口', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');
    test.use({ storageState: STORAGE_STATE });
    test.beforeAll(async ({ browser }) => {
        await ensureStorageState(browser);
    });

    test('ERP 卡片 + 配置入口 + 推送日志 tab + 配置抽屉可见(不真推)', async ({ page }) => {
        const guard = attachConsoleGuard(page);
        await enterApp(page);
        await openRoute(page, 'integrations');

        // ────── ERP 集成卡片 + 「配置」入口
        const erpRow = page.locator('.integration-row[data-int-anchor="erp"]');
        await expect(erpRow, 'ERP 集成卡片').toBeVisible();
        await expect(erpRow.locator('.int-btn-configure'), 'ERP「配置」入口').toBeVisible();

        // ────── 推送日志 tab → panel 激活 + 日志区渲染(只读)
        await page.locator('[data-int-top-tab="logs"]').click();
        await expect(
            page.locator('[data-int-top-panel="logs"]'),
            '推送日志 panel 激活'
        ).toHaveClass(/active/);
        await expect(page.locator('#erp-logs-section'), '推送日志区').toBeVisible();

        // ────── 回卡片 tab → 打开 ERP 配置抽屉(可见即关 · 不真推)
        await page.locator('[data-int-top-tab="cards"]').click();
        await expect(page.locator('[data-int-top-panel="cards"]')).toHaveClass(/active/);
        await erpRow.locator('.int-btn-configure').click();
        await expect(page.locator('#int-drawer'), 'ERP 配置抽屉打开').toHaveClass(/open/);
        // 关抽屉 · 不做任何推送配置改动
        await page.locator('#int-drawer-close').click();
        await expect(page.locator('#int-drawer'), 'ERP 配置抽屉关闭').not.toHaveClass(/open/);

        assertNoConsoleErrors(expect, guard);
    });
});
