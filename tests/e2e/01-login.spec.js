// Pearnly E2E · 01 登录成功(地基)· REFACTOR-D1
// ============================================================
// 真站点 + 真测试账号:走完整 UI 登录 → 过套账硬门(选第一个套账)→ 进主应用 →
// 断言登录后特征元素可见 + 无 console.error。
// 顺带把登录态存成 storageState,供 02~09 复用(不必每个 spec 重登)。
//
// 为什么登录后要先过门(2026-07-10 考古路标):26e95a7d(2026-06-12)把套账门改成
// 「每次登录强制选 · 去记住直进」——从那天起任何非超管账号(单套账也要选)登录后都
// 落在 เลือกกิจการ 选择屏,门壳把门外元素 visibility:hidden,「登录即见侧栏」的直登
// 断言必红。CI 无凭据 skip 本 spec,一个月没暴露,真跑才炸出。现语义 = 登录→过门→
// 进主应用,过门复用 _helpers/app.js 的 dismissWorkspaceGate(与 enterApp 同款)。
//
// env-gated:无凭据(CI)优雅跳过 · 保持 CI 绿(铁律 #2)。
// 账号要求:普通非超管账号(超管会被 home.js 弹到 /admin/cost)。
// ============================================================

const fs = require('fs');
const path = require('path');
const { test, expect } = require('@playwright/test');
const { hasCreds, doUiLogin, STORAGE_STATE } = require('./_helpers/auth');
const { dismissWorkspaceGate } = require('./_helpers/app');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

test.describe('登录地基', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');

    test('真账号登录 → 过套账门 → 进主应用 + 特征元素可见 + 无 console error', async ({ page }) => {
        const guard = attachConsoleGuard(page);

        await doUiLogin(page);

        // ────── 1) 落在主应用 /home(而非超管 /admin/*)
        expect(page.url(), '登录后应进 /home(普通账号)').toContain('/home');
        expect(page.url(), '不应是超管 admin 页(测试账号须为普通账号)').not.toContain('/admin');

        // ────── 2) token 真落地 localStorage
        const token = await page.evaluate(() => localStorage.getItem('mrpilot_token'));
        expect((token || '').length, 'mrpilot_token 应存在').toBeGreaterThan(0);

        // ────── 3) 过套账硬门(26e95a7d 起每次登录强制选 · 选第一个套账进场)
        await dismissWorkspaceGate(page);

        // ────── 4) 登录后特征元素可见(着陆页没有这些 · 只有过了门进主应用才有)
        await expect(page.locator('#sidebar'), '主应用侧栏').toBeVisible();
        await expect(page.locator('#avatar-btn'), '右上角账户头像').toBeVisible();
        await expect(
            page.locator('.nav-item[data-route="clients"]'),
            '侧栏「客户管理」入口'
        ).toBeVisible();

        // ────── 5) 存 storageState 供后续 spec 复用(含 localStorage 的 mrpilot_token)
        fs.mkdirSync(path.dirname(STORAGE_STATE), { recursive: true });
        await page.context().storageState({ path: STORAGE_STATE });

        // ────── 6) 全程无 console.error / pageerror
        assertNoConsoleErrors(expect, guard);
    });
});
