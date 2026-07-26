// Pearnly E2E · 05 异常栏下线闸 · 2026-07-26
// ============================================================
// 异常栏(Zihao:用下来毫无用处)已全链下线,本 spec 从「验它能用」改成「验它真的没了」:
// 侧栏无入口(按 getComputedStyle 判,不看 class)· 深链 #/exceptions 回落录入工作台 ·
// 命令面板搜不到。外加一条连带闸:寄生在异常页头部的「客户规矩」入口没被误伤,
// 仍在客户知识页可开。要复活异常栏,见 src/home/route-table.ts 的下线注释。
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

        // ────── ③ 命令面板(真按键 Ctrl+K)里没有异常栏项
        await page.keyboard.press('Control+k');
        await expect(page.locator('#cmdk-mask'), '命令面板打开').toBeVisible();
        await expect(
            page.locator('#cmdk-mask [data-cmdk-route="exceptions"]'),
            '命令面板不该还有异常栏'
        ).toHaveCount(0);
        await page.keyboard.press('Escape');

        assertNoConsoleErrors(expect, guard);
    });

    test('连带闸:客户规矩入口没被误伤', async ({ page }) => {
        const guard = attachConsoleGuard(page);
        await enterApp(page);

        // 知识中心受后端探针门控,关闭态本就无入口——那种账号下无从验起,跳过。
        const navKnowledge = page.locator(SIDEBAR.knowledge);
        test.skip(!(await navKnowledge.isVisible()), '该账号未开知识中心·无客户规矩入口可验');

        await navKnowledge.click();
        await page.locator('.kb-tab-bar .recon-tab-btn[data-kb-tab="rules"]').click();
        await page.locator('#kb-open-rules').click();
        await expect(
            page.locator('#rules-settings-modal'),
            '客户规矩弹窗仍可从客户知识页打开'
        ).toHaveClass(/rs-open/, { timeout: 10_000 });

        assertNoConsoleErrors(expect, guard);
    });
});
