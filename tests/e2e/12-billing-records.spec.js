// Pearnly E2E · 12 账单记录预览框(首页)· 2026-06-28
// ============================================================
// 首页底部记录框:三 tab(扣费/充值/识别)+ 按天/月/年筛选 + 导出全量明细。
// ① 记录框 + 三 tab(owner)+ 筛选 + 导出按钮渲染
// ② 切 tab 实时重拉(rec-body 退出 loading)
// ③ 选「月」出现月份选择器 · 数据重拉
// ④ 点导出 → 浏览器下载 .xlsx(不依赖有无数据)
//
// 多公司账号:登录后落公司选择页,先选公司。
// ============================================================

/* global window */ // page.evaluate 回调在浏览器上下文执行
const { test, expect } = require('@playwright/test');
const { hasCreds, doUiLogin } = require('./_helpers/auth');

const TARGET_COMPANY = 'มานะชัยบริการ';

async function gotoDashboard(page) {
    await doUiLogin(page);
    const chooser = page.getByText(TARGET_COMPANY, { exact: false }).first();
    if (await chooser.isVisible({ timeout: 8000 }).catch(() => false)) {
        await chooser.click();
    }
    await expect(page.locator('#sidebar'), '进主应用').toBeVisible({ timeout: 20_000 });
    await page.evaluate(() => window.routeTo && window.routeTo('dashboard'));
    await expect(page.locator('#page-dashboard'), '首页激活').toHaveClass(/active/, {
        timeout: 15_000,
    });
    await expect(page.locator('#rec-box'), '记录框').toBeVisible({ timeout: 15_000 });
}

test.describe('账单记录预览框(首页)', () => {
    test.skip(!hasCreds(), '需测试账号 · CI 无凭据时跳过');

    test('记录框:三 tab + 筛选 + 导出按钮', async ({ page }) => {
        await gotoDashboard(page);
        await expect(page.locator('#rec-tabs .rec-tab'), 'owner 三 tab').toHaveCount(3, {
            timeout: 15_000,
        });
        await expect(page.locator('#rec-period-sel'), '筛选粒度下拉').toBeVisible();
        await expect(page.locator('#rec-export-btn'), '导出按钮').toBeVisible();
        await page.screenshot({ path: 'tests/e2e/_artifacts/billing-records.png', fullPage: true });
    });

    test('切 tab(识别记录)实时重拉', async ({ page }) => {
        await gotoDashboard(page);
        await page.locator('.rec-tab[data-rec="ocr"]').click();
        await expect(page.locator('.rec-tab[data-rec="ocr"]'), '识别 tab 激活').toHaveClass(
            /active/
        );
        // 退出 loading 态(渲染出行或空态)
        await expect(page.locator('#rec-body .rec-loading'), '加载完成').toHaveCount(0, {
            timeout: 15_000,
        });
    });

    test('选「月」出现月份选择器并重拉', async ({ page }) => {
        await gotoDashboard(page);
        await page.locator('#rec-period-sel').selectOption('month');
        await expect(page.locator('#rec-date-input'), '月份选择器').toBeVisible({ timeout: 8000 });
        await expect(page.locator('#rec-body .rec-loading'), '重拉完成').toHaveCount(0, {
            timeout: 15_000,
        });
    });

    test('导出 → 下载 xlsx', async ({ page }) => {
        await gotoDashboard(page);
        const [download] = await Promise.all([
            page.waitForEvent('download', { timeout: 20_000 }),
            page.locator('#rec-export-btn').click(),
        ]);
        expect(download.suggestedFilename(), '导出文件名为 .xlsx').toContain('.xlsx');
    });

    test('充值记录行可下载凭证 PDF', async ({ page }) => {
        await gotoDashboard(page);
        await page.locator('.rec-tab[data-rec="topup"]').click();
        await expect(page.locator('#rec-body .rec-loading'), '充值加载完成').toHaveCount(0, {
            timeout: 15_000,
        });
        const dl = page.locator('.rec-dl[data-receipt]').first();
        const has = await dl.isVisible({ timeout: 5000 }).catch(() => false);
        test.skip(!has, '无充值记录 · 跳过凭证下载');
        const [download] = await Promise.all([
            page.waitForEvent('download', { timeout: 20_000 }),
            dl.click(),
        ]);
        expect(download.suggestedFilename(), '凭证文件名为 .pdf').toContain('.pdf');
    });
});
