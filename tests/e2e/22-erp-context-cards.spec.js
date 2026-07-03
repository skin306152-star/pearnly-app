// Pearnly E2E · 22 录入工作台「上下文 ERP 连接卡」守门
// ============================================================
// ERP 连接卡按任务上下文出现在录入工作台(src/home/dms-intake-erp-cards.ts):
//   发票/收据录入 → MR.ERP(财务)+ Express 两卡;身份证→DMS 客户 → MR.ERP DMS 一卡。
// 本 spec 锁「按任务联动 + 卡片在场」(确定性 · 不烧 OCR · 不依赖已配 ERP:未连接也渲染)。
// 点击开向导的行为走人工 live 验(依赖真端点/凭据),不进 CI。
// ============================================================

const { test, expect } = require('@playwright/test');
const { hasCreds, ensureStorageState, STORAGE_STATE } = require('./_helpers/auth');
const { enterApp, openRoute } = require('./_helpers/app');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

test.describe('录入工作台 · 上下文 ERP 连接卡', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');
    test.use({ storageState: STORAGE_STATE });
    test.beforeAll(async ({ browser }) => {
        await ensureStorageState(browser);
    });

    test('发票任务露 MR.ERP + Express;切身份证露 MR.ERP DMS', async ({ page }) => {
        const guard = attachConsoleGuard(page);
        await enterApp(page);
        await openRoute(page, 'dms-intake');

        const zone = page.locator('#dx-erp-cards');

        // 发票/收据录入(默认任务)→ 财务两卡
        await expect(zone.locator('.dx-erp-card[data-erp="mrerp"]'), 'MR.ERP 卡在场').toBeVisible();
        await expect(
            zone.locator('.dx-erp-card[data-erp="express"]'),
            'Express 卡在场'
        ).toBeVisible();
        await expect(zone.locator('.dx-erp-card'), '发票任务两卡').toHaveCount(2);

        // 每张卡都有动作按钮(未连接=「连接」· 已连接=「配置」· 均带 data-erp-config)。
        // 「启用/停用」toggle 仅在已配置端点时出现 → 走人工 live 验(依赖真端点),不进 CI 断言。
        await expect(
            zone.locator('.dx-erp-card[data-erp="mrerp"] [data-erp-config]'),
            'MR.ERP 卡有动作按钮'
        ).toBeVisible();
        await expect(
            zone.locator('.dx-erp-card[data-erp="express"] [data-erp-config]'),
            'Express 卡有动作按钮'
        ).toBeVisible();

        // 切「身份证→DMS 客户」任务 → 只剩 MR.ERP DMS 一卡
        await page.locator('.dx-opt[data-task="identity"]').click();
        await expect(
            zone.locator('.dx-erp-card[data-erp="mrerp_dms"]'),
            'MR.ERP DMS 卡在场'
        ).toBeVisible();
        await expect(zone.locator('.dx-erp-card'), '身份证任务一卡').toHaveCount(1);

        assertNoConsoleErrors(expect, guard);
    });
});
