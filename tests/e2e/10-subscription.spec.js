// Pearnly E2E · 10 订阅与计费(首页)· 2026-06-28
// ============================================================
// 首页改版为订阅与计费:套餐卡 S/M/L + 余额带 + 当前套餐摘要 + 账单。
// ① 渲染 + 截图(高风险:首页是登录后落地页)② GET /api/me/subscription 目录正确
// ③ 订阅 L(฿500 > 账户余额)→ 端到端走服务端余额守卫 → 402 → 弹充值(不真扣钱)。
// ============================================================

const { test, expect } = require('@playwright/test');
const { hasCreds, ensureStorageState, STORAGE_STATE } = require('./_helpers/auth');
const { enterApp } = require('./_helpers/app');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

async function gotoDashboard(page) {
    await enterApp(page);
    await page.evaluate(() => window.routeTo && window.routeTo('dashboard'));
    await expect(page.locator('#page-dashboard'), '首页激活').toHaveClass(/active/, {
        timeout: 15_000,
    });
}

test.describe('订阅与计费(首页)', () => {
    test.skip(!hasCreds(), '需测试账号 · CI 无凭据时跳过');
    test.use({ storageState: STORAGE_STATE });
    test.beforeAll(async ({ browser }) => {
        await ensureStorageState(browser);
    });

    test('首页:顶部两卡(当前套餐|余额)+ 套餐卡 + 账单 · 旧统计卡/快捷已撤', async ({ page }) => {
        const guard = attachConsoleGuard(page);
        await gotoDashboard(page);

        // 顶部两张并排卡片
        await expect(page.locator('.sub-top .sub-card'), '顶部两张卡片').toHaveCount(2, {
            timeout: 15_000,
        });
        await expect(page.locator('#sub-summary.sub-card'), '当前套餐卡').toBeVisible();
        await expect(
            page.locator('#sub-summary .sub-card-ico'),
            '当前套餐图标(王冠)'
        ).toBeVisible();
        await expect(
            page.locator('#dash-kpi-balance-card.sub-card'),
            '余额卡(owner)'
        ).toBeVisible();
        await expect(page.locator('#dash-kpi-balance'), '余额数字').toBeVisible();

        // 套餐卡 S/M/L
        const plans = page.locator('#sub-plans .sub-plan');
        await expect(plans, '套餐卡 S/M/L 三张').toHaveCount(3);
        await expect(page.locator('.sub-plan-btn').first(), '订阅按钮').toBeVisible();
        await expect(page.locator('#sub-records'), '账单容器').toBeVisible();

        // 旧 dashboard 主体应已撤掉
        await expect(page.locator('#dash-kpi-invoices'), '旧本月发票卡撤掉').toHaveCount(0);
        await expect(page.locator('.qa'), '旧快速操作撤掉').toHaveCount(0);

        await page.screenshot({
            path: 'tests/e2e/_artifacts/subscription-home.png',
            fullPage: true,
        });
        assertNoConsoleErrors(expect, guard);
    });

    test('套餐卡 hover 有动态交互(translateY 上浮)', async ({ page }) => {
        await gotoDashboard(page);
        const card = page.locator('#sub-plans .sub-plan').first();
        await expect(card).toBeVisible({ timeout: 15_000 });
        // hover 前 transform = none;hover 后 .sub-plan:hover translateY(-3px) → matrix 带位移
        const before = await card.evaluate((el) => getComputedStyle(el).transform);
        await card.hover();
        await page.waitForTimeout(250); // 等 0.15s 过渡完成
        const after = await card.evaluate((el) => getComputedStyle(el).transform);
        expect(before === 'none' || before.endsWith(', 0)')).toBeTruthy();
        expect(after, 'hover 后应有 transform 位移').not.toBe(before);
        await page.screenshot({ path: 'tests/e2e/_artifacts/subscription-hover.png' });
    });

    test('GET /api/me/subscription 返回 S/M/L 目录', async ({ page }) => {
        await enterApp(page);
        const data = await page.evaluate(async () => {
            const t = localStorage.getItem('mrpilot_token');
            const r = await fetch('/api/me/subscription', {
                headers: { Authorization: 'Bearer ' + t },
                cache: 'no-store',
            });
            return { status: r.status, body: await r.json() };
        });
        expect(data.status).toBe(200);
        expect(data.body.plans.map((p) => p.code)).toEqual(['S', 'M', 'L']);
        expect(data.body.plans[1]).toMatchObject({
            code: 'M',
            quota: 200,
            fee: 250,
            over_rate: 1.25,
        });
    });

    test('订阅 L(余额不足)→ 服务端守卫 402 → 弹充值(不真扣钱)', async ({ page }) => {
        await gotoDashboard(page);
        const balance = await page.evaluate(async () => {
            const t = localStorage.getItem('mrpilot_token');
            const r = await fetch('/api/me/subscription', {
                headers: { Authorization: 'Bearer ' + t },
                cache: 'no-store',
            });
            const j = await r.json();
            return j.balance_thb;
        });
        // L = ฿500 · 仅当余额确实 < 500 时此用例验证「余额不足」路径(防误扣)
        test.skip(balance >= 500, `余额 ฿${balance} ≥ 500 · 跳过以免真订阅扣费`);

        await page.locator('.sub-plan-btn[data-plan="L"]').click();
        await page.locator('#confirm-modal-ok').click(); // 确认弹窗
        // 余额不足 → 后端 402 → 前端 _openTopupModal → 充值浮层出现
        await expect(page.locator('#topup-v2-ov'), '余额不足应弹充值').toBeVisible({
            timeout: 10_000,
        });
    });
});
