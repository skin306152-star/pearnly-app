// Pearnly E2E · 25 完整版账号侧栏零变化(PS-2 · pos_only 精简外壳的对照组)
// ============================================================
// 纯只读:不改任何账号状态,只验证非 pos_only 账号(现状 business_type≠pos_only)的侧栏
// 行为与 pos_only 改动前完全一致——可见菜单项远超 7 个上限,且做账/报税等常规菜单正常
// 显示。用来防「pos_only 门控代码不小心影响了正常账号」这一类回归。
// ============================================================
const path = require('path');
const { test, expect } = require('@playwright/test');
const { hasCreds, ensureStorageState, STORAGE_STATE } = require('./_helpers/auth');
const { enterApp, getModules, visibleNavItems } = require('./_helpers/app');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

const OUT = path.join(process.cwd(), 'tests', 'e2e', '_artifacts', 'ps2');

test.describe('完整版账号 · pos_only 改动零回归', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');
    test.use({ storageState: STORAGE_STATE });
    test.beforeAll(async ({ browser }) => {
        await ensureStorageState(browser);
    });

    test('非 pos_only 账号 · 侧栏菜单项数 > 7 且做账/报税菜单可见', async ({ page }) => {
        const guard = attachConsoleGuard(page);
        await enterApp(page);

        const modules = await getModules(page);
        expect(modules.ok).toBe(true);
        expect(
            modules.data.business_type,
            '这条对照测试要求账号不是 pos_only(避免和 24 号 spec 的临时状态撞车)'
        ).not.toBe('pos_only');

        // 数菜单前先等 module-nav apply 完(accounting 组默认 display:none,apply 才翻开;
        // enterApp 只保证 sidebar 在,不保证模块显隐已生效——裸数是竞态)。
        const acctOn = modules.data.modules.accounting && modules.data.modules.accounting.enabled;
        if (acctOn) {
            await expect(page.locator('.nav-item[data-route="acct-review"]')).toBeVisible({
                timeout: 15000,
            });
        }

        const visible = await visibleNavItems(page);

        expect(visible.length, 'pos_only 闸不该收窄完整版菜单').toBeGreaterThan(7);

        // accounting 开(该账号默认业态 firm 全开)时做账/报税菜单应正常显示——
        // 证明 data-pos-only-hide 收口没有误伤非 pos_only 账号。
        if (acctOn) {
            expect(visible).toContain('acct-review');
            expect(visible).toContain('tax-center');
        }

        await page.screenshot({
            path: path.join(OUT, 'full_account_sidebar.png'),
            fullPage: true,
        });

        assertNoConsoleErrors(expect, guard);
    });
});
