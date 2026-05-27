// Pearnly E2E · 01 登录成功(地基)· REFACTOR-D1
// ============================================================
// 真站点 + 真测试账号:走完整 UI 登录 → 进主应用 → 断言登录后特征元素可见 + 无 console.error。
// 顺带把登录态存成 storageState,供 02~09 复用(不必每个 spec 重登)。
//
// env-gated:无凭据(CI)优雅跳过 · 保持 CI 绿(铁律 #2)。
// 账号要求:普通非超管账号(超管会被 home.js 弹到 /admin/cost)。
// ============================================================

const fs = require('fs');
const path = require('path');
const { test, expect } = require('@playwright/test');
const { hasCreds, doUiLogin, STORAGE_STATE } = require('./_helpers/auth');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

test.describe('登录地基', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');

    test('真账号登录 → 进主应用 + 登录后特征元素可见 + 无 console error', async ({ page }) => {
        const guard = attachConsoleGuard(page);

        await doUiLogin(page);

        // ────── 1) 落在主应用 /home(而非超管 /admin/*)
        expect(page.url(), '登录后应进 /home(普通账号)').toContain('/home');
        expect(page.url(), '不应是超管 admin 页(测试账号须为普通账号)').not.toContain('/admin');

        // ────── 2) token 真落地 localStorage
        const token = await page.evaluate(() => localStorage.getItem('mrpilot_token'));
        expect((token || '').length, 'mrpilot_token 应存在').toBeGreaterThan(0);

        // ────── 3) 登录后特征元素可见(着陆页没有这些 · 只有进了主应用才有)
        await expect(page.locator('#sidebar'), '主应用侧栏').toBeVisible();
        await expect(page.locator('#avatar-btn'), '右上角账户头像').toBeVisible();
        await expect(
            page.locator('.nav-item[data-route="clients"]'),
            '侧栏「客户管理」入口'
        ).toBeVisible();

        // ────── 4) 存 storageState 供后续 spec 复用(含 localStorage 的 mrpilot_token)
        fs.mkdirSync(path.dirname(STORAGE_STATE), { recursive: true });
        await page.context().storageState({ path: STORAGE_STATE });

        // ────── 5) 全程无 console.error / pageerror
        assertNoConsoleErrors(expect, guard);
    });
});
