// Pearnly E2E · 05 异常栏下线闸 · 2026-07-26
// ============================================================
// 异常栏(Zihao:用下来毫无用处)已全链下线,本 spec 从「验它能用」改成「验它真的没了」:
// 侧栏无入口(按 getComputedStyle 判,不看 class)· 深链 #/exceptions 回落录入工作台 ·
// 命令面板搜不到。要复活异常栏,见 src/home/route-table.ts 的下线注释。
// ============================================================

/* global window */

const { test, expect } = require('@playwright/test');
const { hasCreds, ensureStorageState, STORAGE_STATE } = require('./_helpers/auth');
const { enterApp, visibleNavItems, SIDEBAR } = require('./_helpers/app');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

test.describe('异常栏已下线', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');
    test.use({ storageState: STORAGE_STATE });
    test.beforeAll(async ({ browser }) => {
        await ensureStorageState(browser);
    });

    test('侧栏无入口 + 深链回落 + 命令面板搜不到', async ({ page }) => {
        const guard = attachConsoleGuard(page);
        await enterApp(page);

        // ────── ① 侧栏:真实可见的 nav-item 里没有 exceptions
        const routes = await visibleNavItems(page);
        expect(routes, '侧栏不该还有异常栏入口').not.toContain('exceptions');
        await expect(page.locator(SIDEBAR.exceptions), '异常栏菜单项应恒隐').toBeHidden();

        // ────── ② 深链:手敲 #/exceptions → 不在 VALID_ROUTES → 回落录入工作台
        await page.evaluate(() => {
            window.location.hash = '#/exceptions';
        });
        await expect(page.locator('#page-dms-intake'), '深链回落录入工作台').toHaveClass(/active/, {
            timeout: 15_000,
        });
        await expect(page.locator('#page-exceptions'), '异常页不该激活').not.toHaveClass(/active/);

        // ────── ③ 命令面板(⌘K)已于 2026-08-26 整体下线(需求批 B4),异常栏项无从残留——
        //        此处不再验命令面板,保留深链回落 + 侧栏恒隐两条防线。
        assertNoConsoleErrors(expect, guard);
    });
});
