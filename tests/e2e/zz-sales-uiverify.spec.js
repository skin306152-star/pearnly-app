// Pearnly E2E · 销项 PO-10 前端 UI 自查(截图 + 0 console error)
// 真站点 + 真测试账号:走每个销项屏 + 开票向导 5 步 + 设置弹窗,全程截图供布局核对。
// env-gated:无凭据(CI)优雅跳过。截图落 SALES_SHOT_DIR。
const fs = require('fs');
const path = require('path');
const { test, expect } = require('@playwright/test');
const { hasCreds, doUiLogin } = require('./_helpers/auth');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

const OUT = process.env.SALES_SHOT_DIR || path.join(process.cwd(), 'sales_uiverify');

test.describe('销项 UI 自查', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');
    test.setTimeout(120000);

    test('走每屏 + 向导 + 截图 + 无 console error', async ({ page }) => {
        const guard = attachConsoleGuard(page);
        fs.mkdirSync(OUT, { recursive: true });
        await doUiLogin(page);
        await page.waitForSelector('#sidebar', { timeout: 15000 });
        // 测试账号无活动账套 → 关掉「选择账套」弹层(选个人事务)以便后续操作不被挡
        await page.waitForTimeout(1200);
        await page.click('.ws-modal-item', { timeout: 3000 }).catch(() => {});
        await page.waitForTimeout(800);

        const go = async (route, ms = 900) => {
            await page.evaluate((r) => (globalThis.location.hash = '#/' + r), route);
            await page.waitForTimeout(ms);
        };
        const shot = async (name) => {
            await page.screenshot({ path: path.join(OUT, name + '.png'), fullPage: true });
        };
        const click = async (sel, ms = 700) => {
            await page.click(sel, { timeout: 4000 }).catch(() => {});
            await page.waitForTimeout(ms);
        };

        await go('sales-invoices');
        await shot('01-workbench');
        await go('sales-products');
        await shot('02-products');
        await go('sales-account', 1800);
        await shot('03-account');

        // 开票设置弹窗
        await go('sales-invoices');
        await click('#sx-settings-btn');
        await shot('04-settings');
        await click('#sx-set-close', 300);

        // 开票向导 5 步
        await click('#sx-new-btn', 1000);
        await shot('05-wizard-step1');
        await click('#sw-next', 500);
        await shot('06-wizard-step2-parties');
        await click('#sw-next', 500);
        await shot('07-wizard-step3-items');
        await click('#sw-addcustom', 400);
        await shot('08-wizard-step3-after-addcustom');
        await click('#sw-next', 500);
        await shot('09-wizard-step4-pay');
        await click('#sw-next', 600);
        await shot('10-wizard-step5-review');

        assertNoConsoleErrors(expect, guard);
    });
});
