// Pearnly E2E · 23 汇总表 → 批量建单(录入工作台第三任务卡)真机全链
// ============================================================
// 覆盖 4 步闭环:选卡 → 上传汇总表(7-11 冰厂 xlsx)→ 列映射+批次常量(刻意留空客户税号+勾散客)
//   → 逐行预览(方向/落点徽章为后端真判 · 散客买方归一 เงินสด)→ 提交建单(账本草稿 + ocr_history)。
// 专测散客/现金票路径(不是只测有税号的顺风场景)。每步截图存档供视觉验收;全程 console guard。
// doc_no 带本次运行时间戳前缀 → 跨次运行不撞号(测试账号可反复跑)。
// ============================================================

const path = require('path');
const { test, expect } = require('@playwright/test');
const { hasCreds, ensureStorageState, STORAGE_STATE } = require('./_helpers/auth');
const { enterApp } = require('./_helpers/app');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

const FIXTURE = path.join(__dirname, '_fixtures', 'summary-7-11-ice.xlsx');
const OUT =
    process.env.SUMMARY_SHOT_DIR ||
    path.join(process.cwd(), 'tests', 'e2e', '_artifacts', 'summary');

test.describe('录入工作台 · 汇总表批量建单', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');
    test.use({ storageState: STORAGE_STATE });
    test.beforeAll(async ({ browser }) => {
        await ensureStorageState(browser);
    });

    test('汇总表 → 散客现金票批量建单全链', async ({ page }) => {
        const guard = attachConsoleGuard(page);
        const shot = (name) =>
            page.screenshot({ path: path.join(OUT, name + '.png'), fullPage: true });

        await enterApp(page);
        // 录入工作台入口在可折叠导航组内(默认收起 · 侧栏点击非本功能验收点),
        // 直接走 hash 路由进目标页,再对真实渲染的功能 UI 断言。
        await page.evaluate(() => {
            const g = globalThis;
            if (typeof g.routeTo === 'function') g.routeTo('dms-intake');
            else g.location.hash = '#/dms-intake';
        });
        await expect(page.locator('#page-dms-intake'), '录入工作台页激活').toHaveClass(/active/);

        // ── 选第三张卡(中间位)· 上传步露出 ──
        await page.locator('.dx-opt[data-task="summary_batch"]').click();
        await expect(page.locator('#dx-s-batch-up'), '上传步在场').toBeVisible();
        await expect(page.locator('.dx-opt[data-task="summary_batch"]'), '第三卡高亮').toHaveClass(
            /active/
        );
        await shot('01-task-picker');

        // ── 上传汇总表 → 解析 ──
        await page.setInputFiles('#dxb-file', FIXTURE);
        await expect(page.locator('#dxb-parse'), '解析按钮出现').toBeVisible();
        await shot('02-upload');
        await page.locator('#dxb-parse').click();
        await expect(page.locator('#dx-s-batch-map'), '映射步在场').toBeVisible();

        // ── 列映射:显式指定金额列(模拟真实用户复核自动猜列 · 不盲信启发式)──
        // 泰文表头 "ยอดเงินก่อน vat"(税前)/"ยอดเงิน vat"(税额)/"ยอดเงินรวม"(总额)。
        await page.locator('[data-col="date"]').selectOption({ label: 'วันที่' });
        await page.locator('[data-col="subtotal"]').selectOption({ label: 'ยอดเงินก่อน vat' });
        await page.locator('[data-col="vat"]').selectOption({ label: 'ยอดเงิน vat' });
        await page.locator('[data-col="total_amount"]').selectOption({ label: 'ยอดเงินรวม' });

        // ── 批次常量:刻意留空客户税号 + 勾选散客(专测现金兜底路径)──
        await page.locator('[data-bk="counterparty_name"]').fill('7-11');
        await page.locator('[data-bk="counterparty_tax"]').fill(''); // 留空
        await page.locator('[data-bk="cash_walkin"]').check();
        await page.locator('[data-bk="product_name"]').fill('น้ำแข็งแพ็ค');
        const pat = 'E2E-' + Date.now() + '-{seq}';
        await page.locator('[data-bk="doc_no_pattern"]').fill(pat);
        await shot('03-mapping');

        // ── 预览:徽章为后端真判 · 散客买方归一 เงินสด ──
        await page.locator('#dxb-to-review').click();
        await expect(page.locator('#dx-s-batch-review .dxb-tbl'), '预览表在场').toBeVisible();
        // 散客路径落地证据:表内买方显示 เงินสด(后端 mapping 归一,不是前端写死)。
        await expect(page.locator('#dx-s-batch-review .dxb-tbl'), '买方归一现金客户').toContainText(
            'เงินสด'
        );
        await expect(
            page.locator('#dx-s-batch-review .dx-badge').first(),
            '方向/落点徽章在场'
        ).toBeVisible();
        await shot('04-preview');

        // ── 提交建单 → 结果统计 ──
        await page.locator('#dxb-commit').click();
        await expect(page.locator('#dx-s-batch-submit .dxb-stats'), '结果统计在场').toBeVisible();
        // 建成数(第一格=已建单)应 > 0。
        const createdTxt = await page.locator('.dxb-stat.green b').first().innerText();
        expect(parseInt(createdTxt, 10), '至少建成一单').toBeGreaterThan(0);
        await shot('05-result');

        assertNoConsoleErrors(expect, guard);
    });
});
