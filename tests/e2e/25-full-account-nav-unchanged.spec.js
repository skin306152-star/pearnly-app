// Pearnly E2E · 25 会计版(firm / 未选业态兜底)· 侧栏 + 头像白名单 + 强制选套账门回归
// ============================================================
// pos_only(24 号)的对照组:验证会计版 firm 壳的终版白名单(Zihao 2026-07-10),并确保
// pos_only 的"免门"改动没破坏会计版多套账用户的【强制选套账】现有行为。
//   侧栏留:首页 / Pearnly Cowork / 采购系统 / 客户 / 公司 / 异常 / 销售系统 / 集成 + 账号块;
//   收起:商品系统 / 做账 / 收银业务 / 可开启功能。
//   头像留 4:团队与权限 / 暗夜模式 / 帮助 & 反馈 / 退出登录。
//   关键解耦:firm 后端默认开 accounting,但「做账/商品」按白名单收起 —— 证明与模块开关脱钩。
// ============================================================
/* global window */

const path = require('path');
const { test, expect } = require('@playwright/test');
const { hasCreds, ensureStorageState, STORAGE_STATE } = require('./_helpers/auth');
const {
    enterApp,
    getModules,
    dismissWorkspaceModal,
    SIDEBAR,
    AVATAR,
    setBusinessType,
    expandAllGroups,
} = require('./_helpers/app');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

const OUT = path.join(process.cwd(), 'tests', 'e2e', '_artifacts', 'nav-preset');

test.describe('会计版 firm · 侧栏 + 头像 + 强制门回归', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');
    test.use({ storageState: STORAGE_STATE });

    let originalBusinessType = null;

    test.beforeAll(async ({ browser }) => {
        await ensureStorageState(browser);
    });

    test.afterEach(async ({ page }) => {
        if (originalBusinessType) await setBusinessType(page, originalBusinessType);
    });

    test('firm:侧栏 8 项白名单 + 头像留团队与权限 + 强制选套账门不破', async ({ page }) => {
        const guard = attachConsoleGuard(page);
        await enterApp(page);

        const before = await getModules(page);
        expect(before.ok, 'GET /api/me/modules 成功').toBe(true);
        originalBusinessType = before.data.business_type || 'firm';

        const flip = await setBusinessType(page, 'firm');
        expect(flip.ok, 'PUT firm 成功(owner 权限)').toBe(true);

        // 回归:清 session 模拟新登录会话后全新进场,firm 仍应【强制弹选套账门】。
        // 设计口径(workspace-gate enforceWorkspaceGate 头注 + prod 实证 2026-07-10):
        // 任何非超管账号每次新登录会话都弹,单套账也弹(列表恰一项)——pos_only 免门
        // 改动不得波及此路径。
        await page.evaluate(() => {
            try {
                sessionStorage.clear();
            } catch {
                /* 私模 */
            }
        });
        await page.goto('/home');

        const pick = page.locator('#workspace-gate-root [data-wsg-pick]').first();
        await expect(pick, 'firm 新会话应强制弹选套账门(单套账也弹)').toBeVisible({
            timeout: 20000,
        });
        await pick.click();
        await expect(page.locator('#workspace-gate-root')).toHaveCount(0, { timeout: 10000 });

        await page.waitForFunction(
            () => Array.isArray(window._avatarShellHide) && window._avatarShellHide.length === 3,
            null,
            { timeout: 20000 }
        );
        await dismissWorkspaceModal(page);
        await expandAllGroups(page);

        // 侧栏白名单内可见 / 外隐藏(做账 + 商品系统 收起 = 与模块开关解耦的铁证)。
        for (const key of [
            'dashboard',
            'cowork',
            'purchases',
            'clients',
            'company',
            'exceptions',
            'sales',
            'integrations',
        ]) {
            await expect(page.locator(SIDEBAR[key]), `${key} 应可见`).toBeVisible();
        }
        for (const key of ['products', 'accounting', 'pos', 'enroll']) {
            await expect(page.locator(SIDEBAR[key]), `${key} 应隐藏`).toBeHidden();
        }

        // 头像菜单:留 4(含团队与权限)· 砍 3(设置/账户余额/键盘快捷键)。
        await page.locator('#avatar-btn').click();
        await expect(page.locator('#avatar-popup')).toHaveClass(/show/);
        for (const key of ['console', 'theme', 'help', 'logout']) {
            await expect(page.locator(AVATAR[key]), `头像 ${key} 应可见`).toBeVisible();
        }
        for (const key of ['settings', 'billing', 'shortcuts']) {
            await expect(page.locator(AVATAR[key]), `头像 ${key} 应隐藏`).toBeHidden();
        }

        await page.screenshot({ path: path.join(OUT, 'firm.png'), fullPage: true });

        assertNoConsoleErrors(expect, guard, { allow: [/Failed to load resource.*403/] });
    });
});
