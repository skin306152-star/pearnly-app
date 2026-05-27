// Pearnly E2E · 05 异常处理页 · REFACTOR-D1
// ============================================================
// 进异常栏 → KPI / 状态 tab / 列表渲染 → 筛选可用(切状态 tab + 客户筛选下拉可见)。
// 只读:不放行 / 不忽略 / 不批量改 · 只验渲染与筛选交互跑通。
// ============================================================

const { test, expect } = require('@playwright/test');
const { hasCreds, ensureStorageState, STORAGE_STATE } = require('./_helpers/auth');
const { enterApp, openRoute } = require('./_helpers/app');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

test.describe('异常处理页', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');
    test.use({ storageState: STORAGE_STATE });
    test.beforeAll(async ({ browser }) => {
        await ensureStorageState(browser);
    });

    test('KPI + 状态 tab + 列表渲染 + 筛选可用', async ({ page }) => {
        const guard = attachConsoleGuard(page);
        await enterApp(page);
        await openRoute(page, 'exceptions');

        // ────── 顶部 4 KPI
        await expect(page.locator('#exc-kpi-row'), 'KPI 行').toBeVisible();

        // ────── 状态 tab(待复核默认 active)
        await expect(page.locator('#exc-status-tabs .exc-status-tab'), '3 个状态 tab').toHaveCount(
            3
        );
        await expect(
            page.locator('.exc-status-tab[data-status="pending"]'),
            '待复核 tab 默认 active'
        ).toHaveClass(/active/);

        // ────── 列表 loading 解析完(异常行或空态)
        await expect(
            page.locator('#exc-list :is(.exc-row, .exc-empty)').first(),
            '异常列表渲染(行或空态)'
        ).toBeVisible({ timeout: 15_000 });

        // ────── 筛选可用:客户筛选下拉可见 + 切「已处理」状态 tab 生效
        await expect(page.locator('#exc-client-filter'), '客户筛选下拉').toBeVisible();
        await page.locator('.exc-status-tab[data-status="resolved"]').click();
        await expect(
            page.locator('.exc-status-tab[data-status="resolved"]'),
            '已处理 tab 切换为 active'
        ).toHaveClass(/active/);
        // 切后列表重渲(行或空态再次稳定)
        await expect(page.locator('#exc-list :is(.exc-row, .exc-empty)').first()).toBeVisible({
            timeout: 15_000,
        });

        assertNoConsoleErrors(expect, guard);
    });
});
