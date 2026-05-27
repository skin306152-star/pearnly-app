// Pearnly E2E · 09 充值弹窗 · REFACTOR-D1
// ============================================================
// 首页(dashboard)点充值入口 → 充值弹窗打开 + 金额选项(฿100/500/1000/2000)可见。
//
// 边界(铁律 #3 · 绝不花真钱):
//   - 只测「弹窗打开 + 金额选项在」· 到此为止。
//   - 绝不点「下一步」(#tv2-next):step1Next 会 POST /api/credits/topup/request 创建真实
//     充值请求(造数据)· 此处止步,看完即关(#tv2-close)。
//
// 入口:dashboard 余额 KPI 卡的 #kpi-balance-topup-link(仅 owner + 非计费豁免账号显示)。
//      账号无该链接时,退而用 window._openTopupModal() 直开弹窗验证(annotation 标注)。
// ============================================================

/* global window */
const { test, expect } = require('@playwright/test');
const { hasCreds, ensureStorageState, STORAGE_STATE } = require('./_helpers/auth');
const { enterApp, openRoute } = require('./_helpers/app');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

test.describe('充值弹窗', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');
    test.use({ storageState: STORAGE_STATE });
    test.beforeAll(async ({ browser }) => {
        await ensureStorageState(browser);
    });

    test('点充值入口 → 弹窗打开 + 金额选项可见(绝不真付)', async ({ page }, testInfo) => {
        const guard = attachConsoleGuard(page);
        await enterApp(page);
        await openRoute(page, 'dashboard');

        // 余额 KPI 异步渲染 · 等充值入口链接(可能因账号 owner/豁免标记而缺)
        const link = page.locator('#kpi-balance-topup-link');
        const linkShown = await link
            .waitFor({ state: 'visible', timeout: 8_000 })
            .then(() => true)
            .catch(() => false);

        if (linkShown) {
            await link.click(); // 真实 UI 充值入口
        } else {
            // 退路:该账号无充值入口链接(非 owner / 计费豁免)· 直接验证弹窗本身
            testInfo.annotations.push({
                type: 'note',
                description: '账号无 #kpi-balance-topup-link 入口 · 改用 _openTopupModal 验证弹窗',
            });
            await page.evaluate(() => window._openTopupModal && window._openTopupModal());
        }

        // ────── 弹窗打开
        await expect(page.locator('#topup-v2-ov'), '充值弹窗打开').toBeVisible();

        // ────── 金额选项(฿100 / ฿500 / ฿1,000 / ฿2,000)
        const qamts = page.locator('#topup-v2-ov .topup-v2-qamt');
        await expect(qamts, '4 个快捷金额选项').toHaveCount(4);
        await expect(qamts.first(), '金额选项可见').toBeVisible();
        await expect(page.locator('.topup-v2-qamt[data-val="100"]'), '฿100 选项').toBeVisible();
        await expect(page.locator('.topup-v2-qamt[data-val="500"]'), '฿500 选项').toBeVisible();
        // 到此为止 · 绝不点「下一步」(会创建真实充值请求)· 关弹窗
        await page.locator('#tv2-close').click();
        await expect(page.locator('#topup-v2-ov'), '弹窗关闭').toBeHidden();

        assertNoConsoleErrors(expect, guard);
    });
});
