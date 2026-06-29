// 采购设置 · 费用科目标签就地编辑 E2E(真站点 · 真账号)。
// 验证:点科目名 → 行内编辑;Esc 取消;Enter 存(id 稳定 PATCH);reload 后持久
// (依赖该科目的读路径按 id 取名 → 自动显示新名)。改完复原,prod 数据净零变化。
// 无 PEARNLY_E2E_USER/PASS(CI)优雅跳过。
/* global window, location */
const { test, expect } = require('@playwright/test');
const { doUiLogin, hasCreds } = require('./_helpers/auth');

async function ensureWorkspace(page) {
    // 工作区选择闸(workspace-gate · [data-wsg-pick])首登/reload 会弹 · 选第一个进主应用
    const pick = page.locator('[data-wsg-pick]').first();
    if (await pick.count()) {
        await pick.click().catch(() => {});
        await page.waitForTimeout(1500);
    }
}

async function gotoPurchaseSettings(page) {
    await ensureWorkspace(page);
    await page.evaluate(() => {
        window.navigateTo
            ? window.navigateTo('purchase-settings')
            : (location.hash = '#/purchase-settings');
    });
    await page.waitForSelector('#pur-cats .chip .nm', { state: 'visible', timeout: 30000 });
}

test.describe('采购设置 · 费用科目标签就地编辑', () => {
    test.skip(!hasCreds(), '需 PEARNLY_E2E_USER/PASS · CI 无凭据跳过');

    test('点名就地改 → Esc 取消 / Enter 存 → reload 持久 → 复原', async ({ page }) => {
        test.setTimeout(150000);
        await doUiLogin(page);
        await page.waitForTimeout(2000);
        await gotoPurchaseSettings(page);

        // 1) 每个标签都有可编辑名
        const nm = page.locator('#pur-cats .chip .nm[data-edit]');
        expect(await nm.count()).toBeGreaterThan(0);

        // 2) 点名 → 整 chip 变行内输入框(值=原名)
        const first = page.locator('#pur-cats .chip .nm').first();
        const orig = (await first.innerText()).trim();
        await first.click();
        const input = page.locator('#pur-cats input.addcat-input');
        await expect(input).toBeVisible();
        await expect(input).toHaveValue(orig);

        // 3) Esc 取消 → 复原(非破坏)
        await input.press('Escape');
        await expect(page.locator('#pur-cats .chip .nm').first()).toHaveText(orig);

        // 4) 改名 → Enter → 即时刷新
        const tmp = orig + '·e2e';
        await page.locator('#pur-cats .chip .nm').first().click();
        const input2 = page.locator('#pur-cats input.addcat-input');
        await input2.fill(tmp);
        await input2.press('Enter');
        await expect(page.locator(`#pur-cats .chip .nm:text-is("${tmp}")`)).toHaveCount(1, {
            timeout: 15000,
        });

        // 5) reload → 新名持久(证 id 稳定改名 · 依赖按 id 取名实时跟随)
        await page.reload();
        await gotoPurchaseSettings(page);
        await expect(page.locator(`#pur-cats .chip .nm:text-is("${tmp}")`)).toHaveCount(1);

        // 6) 复原(清理 · prod 净零变化)
        await page.locator(`#pur-cats .chip .nm:text-is("${tmp}")`).first().click();
        const input3 = page.locator('#pur-cats input.addcat-input');
        await input3.fill(orig);
        await input3.press('Enter');
        await expect(page.locator(`#pur-cats .chip .nm:text-is("${tmp}")`)).toHaveCount(0, {
            timeout: 15000,
        });
    });
});
