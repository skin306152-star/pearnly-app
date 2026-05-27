// Pearnly E2E · 04 识别历史(只读)· REFACTOR-D1
// ============================================================
// 进历史页 → 列表渲染 → 有记录则打开一条详情抽屉(#drawer.show)。
// 三态都验:有记录(点行开抽屉)/ 空库(history-empty)/ 无权限(history-free-block)。
// 只读:不删 / 不导出 / 不改 · 抽屉看完即关。
// ============================================================

const { test, expect } = require('@playwright/test');
const { hasCreds, ensureStorageState, STORAGE_STATE } = require('./_helpers/auth');
const { enterApp, openRoute } = require('./_helpers/app');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

test.describe('识别历史(只读)', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');
    test.use({ storageState: STORAGE_STATE });
    test.beforeAll(async ({ browser }) => {
        await ensureStorageState(browser);
    });

    test('历史页渲染 + 打开一条详情抽屉(若有记录)', async ({ page }) => {
        const guard = attachConsoleGuard(page);
        await enterApp(page);
        await openRoute(page, 'history');

        // 等三态之一稳定(主列表 / 空态 / 无权限块)· 用 locator 可见性 · 不进 evaluate
        await expect
            .poll(
                async () =>
                    (await page.locator('#history-main').isVisible()) ||
                    (await page.locator('#history-empty').isVisible()) ||
                    (await page.locator('#history-free-block').isVisible()),
                { timeout: 15_000, message: '历史三态(主列表/空态/无权限)之一就绪' }
            )
            .toBe(true);

        const rows = page.locator('.history-row');
        if ((await rows.count()) > 0) {
            // ── 有记录:点第一行(避开 checkbox)→ 详情抽屉打开
            await rows.first().click();
            await expect(page.locator('#drawer'), '详情抽屉打开').toHaveClass(/show/);
            await expect(page.locator('#drawer-title'), '抽屉标题(文件名)非空').not.toBeEmpty();
            // 看完即关 · 不动数据
            await page.locator('#drawer-close').click();
            await expect(page.locator('#drawer'), '抽屉关闭').not.toHaveClass(/show/);
        } else {
            // ── 空库 / 无权限:断言对应空态可见(页面正常渲染未崩)
            await expect(
                page.locator('#history-empty, #history-free-block'),
                '空库空态或无权限块可见'
            ).toHaveCount(2); // 两个容器都在 DOM
            const emptyVisible = await page.locator('#history-empty').isVisible();
            const freeVisible = await page.locator('#history-free-block').isVisible();
            expect(emptyVisible || freeVisible, '空态或无权限块至少一个可见').toBe(true);
        }

        assertNoConsoleErrors(expect, guard);
    });
});
