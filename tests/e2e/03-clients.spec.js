// Pearnly E2E · 03 客户管理(只读)· REFACTOR-D1
// ============================================================
// 进客户管理:账套主体 / 买方客户两 tab 渲染 · 列表或空状态出现(loading 解析完)·
// 搜索可用(输无配文串 → 命中 cust-no-match 空态 → 清空恢复)。
// 只读:不点新建 / 不删 / 不改 · 不造数据。
// ============================================================

const { test, expect } = require('@playwright/test');
const { hasCreds, ensureStorageState, STORAGE_STATE } = require('./_helpers/auth');
const { enterApp, openRoute } = require('./_helpers/app');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

test.describe('客户管理(只读)', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');
    test.use({ storageState: STORAGE_STATE });
    test.beforeAll(async ({ browser }) => {
        await ensureStorageState(browser);
    });

    test('两 tab 渲染 + 列表/空状态 + 搜索可用', async ({ page }) => {
        const guard = attachConsoleGuard(page);
        await enterApp(page);
        await openRoute(page, 'clients');

        // ────── tab 条 · 账套主体(默认 active)/ 买方客户
        const tabSeller = page.locator('[data-cust-tab="seller"]');
        const tabBuyer = page.locator('[data-cust-tab="buyer"]');
        await expect(tabSeller, '账套主体 tab').toBeVisible();
        await expect(tabBuyer, '买方客户 tab').toBeVisible();
        await expect(page.locator('#cust-pane-seller'), '默认 seller pane 激活').toHaveClass(
            /active/
        );

        // ────── seller 列表 loading 解析完(出现行或空态)
        await expect(
            page.locator('#cust-pane-seller :is(.cust-row, .cust-empty)').first(),
            'seller 列表渲染(行或空态)'
        ).toBeVisible({ timeout: 15_000 });

        // ────── 切买方客户 tab → pane 激活 + 列表渲染
        await tabBuyer.click();
        await expect(page.locator('#cust-pane-buyer'), 'buyer pane 激活').toHaveClass(/active/);
        await expect(
            page.locator('#cust-pane-buyer :is(.cust-row, .cust-empty)').first(),
            'buyer 列表渲染(行或空态)'
        ).toBeVisible({ timeout: 15_000 });

        // ────── 搜索可用(只读 · 用一定无配的串验证过滤逻辑跑通)
        await tabSeller.click();
        const search = page.locator('#seller-search');
        await search.fill('zzz_nomatch_pearnly_e2e_xyz');
        await expect(
            page.locator('#cust-pane-seller .cust-empty'),
            '无配关键词 → 命中空态(搜索过滤生效)'
        ).toBeVisible();
        await search.fill(''); // 清空恢复 · 不留搜索状态
        await expect(
            page.locator('#cust-pane-seller :is(.cust-row, .cust-empty)').first()
        ).toBeVisible();

        assertNoConsoleErrors(expect, guard);
    });
});
