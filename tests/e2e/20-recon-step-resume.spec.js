// Pearnly E2E · 20 对账中心「续步记忆」守门 · UI-UNIFY 模块2
// ============================================================
// 对账中心续步(src/home/recon-center-x.ts):只记「结果(处理差异)」态。软导航离开再回来,
// 内存里若还留着结果 → 复原到结果态;硬刷新后 RX.result 已空 → 守门不过 → 干净回工作区。
//
// 本 spec 锁安全降级路径(确定性 · 不跑真对账):有「结果态」记忆但内存无结果
//   → 必须回工作区(不渲染一个空的结果页)+ 清记忆。
// 正向复原(带结果回到结果态)依赖真对账,走人工 live 截图验,不进 CI。
// ============================================================

const { test, expect } = require('@playwright/test');
const { hasCreds, ensureStorageState, STORAGE_STATE } = require('./_helpers/auth');
const { enterApp, openRoute } = require('./_helpers/app');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

const MEMO_KEY = 'pearnly_step_recon-center';

test.describe('对账中心 · 续步记忆守门', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');
    test.use({ storageState: STORAGE_STATE });
    test.beforeAll(async ({ browser }) => {
        await ensureStorageState(browser);
    });

    test('有结果态记忆但内存无结果 → 回工作区并清记忆', async ({ page }) => {
        const guard = attachConsoleGuard(page);
        await enterApp(page);
        await openRoute(page, 'reconcile');
        await expect(page.locator('#rcx-workspace'), '工作区可见').not.toHaveClass(/rcx-hidden/);

        // 模拟「上次停在结果态」的残留记忆(本次内存无 RX.result → 不该复原到结果页)
        await page.evaluate(
            ([k]) => localStorage.setItem(k, JSON.stringify({ step: 4, ctx: 'bank' })),
            [MEMO_KEY]
        );

        await openRoute(page, 'history');
        await openRoute(page, 'reconcile');

        await expect(page.locator('#rcx-results'), '结果页未误显').not.toHaveClass(/rcx-show/);
        await expect(page.locator('#rcx-workspace'), '回落到工作区').not.toHaveClass(/rcx-hidden/);

        const memo = await page.evaluate(([k]) => localStorage.getItem(k), [MEMO_KEY]);
        expect(memo, '降级后记忆已清掉').toBeNull();

        assertNoConsoleErrors(expect, guard);
    });
});
