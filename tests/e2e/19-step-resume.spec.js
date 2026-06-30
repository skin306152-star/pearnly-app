// Pearnly E2E · 19 录入工作台「续步记忆」守门 · UI-UNIFY 模块1
// ============================================================
// 续步记忆(轻量版 · src/home/step-resume.ts):localStorage 记步号,数据靠内存态。
// 软导航离开再回来 → 内存态在 → 复原到那一步;硬刷新后内存态空 → 优雅回落第 1 步。
//
// 本 spec 锁「安全降级路径」(确定性 · 不烧 OCR):有步号记忆但当前内存态不够复原该步
//   → 必须回落第 1 步 + 清掉记忆,绝不渲染一个没有数据的中间步(空白/报错)。
// 正向复原(带数据回到原步)依赖真识别,走人工 live 截图验,不进 CI(避免烧 token / flaky)。
// ============================================================

const { test, expect } = require('@playwright/test');
const { hasCreds, ensureStorageState, STORAGE_STATE } = require('./_helpers/auth');
const { enterApp, openRoute } = require('./_helpers/app');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');
const { seedStepMemo, readStepMemo } = require('./_helpers/step-resume');

test.describe('录入工作台 · 续步记忆守门', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');
    test.use({ storageState: STORAGE_STATE });
    test.beforeAll(async ({ browser }) => {
        await ensureStorageState(browser);
    });

    test('有步号记忆但内存态空 → 回落第 1 步并清记忆', async ({ page }) => {
        const guard = attachConsoleGuard(page);
        await enterApp(page);
        await openRoute(page, 'dms-intake');

        // 模拟「上一次停在第 3 步」的残留记忆(内存态此刻是空上传态 → 不该复原到第 3 步)
        await seedStepMemo(page, 'dms-intake', { step: 3, ctx: 'invoice' });

        // 离开再回来 → loadDmsIntake 走 resumeFlow:内存态不够 → resetFlow 回第 1 步
        await openRoute(page, 'history');
        await openRoute(page, 'dms-intake');

        await expect(
            page.locator('.dx-step[data-step="1"]'),
            '回落到第 1 步(步骤条 1 高亮)'
        ).toHaveClass(/active/);
        await expect(page.locator('#dx-s-upload'), '第 1 步上传态可见').toBeVisible();

        const memo = await readStepMemo(page, 'dms-intake');
        expect(memo, '降级后记忆已清掉(下次不再误复原)').toBeNull();

        assertNoConsoleErrors(expect, guard);
    });
});
