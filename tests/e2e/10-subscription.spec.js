// Pearnly E2E · 10 订阅与计费(首页)· 2026-06-28
// ============================================================
// 首页改版为订阅与计费:顶部两卡(当前套餐|余额)+ 套餐卡 S/M/L + 计费规则 + 账单。
// ① 两卡 + 套餐卡渲染 + 截图 ② 套餐卡 hover 上浮 ③ GET /api/me/subscription 目录
// ④ 订阅 L(฿500 > 余额)→ 服务端守卫 402 → 弹充值(不真扣钱)。
//
// 本测试账号是多公司账号:登录后落「เลือกกิจการ」选择页,需先选公司才进主应用。
// 故不走 storageState helper,自带「登录 + 选公司」流程。
// ============================================================

const { test, expect } = require('@playwright/test');
const { hasCreds, doUiLogin } = require('./_helpers/auth');

const TARGET_COMPANY = 'มานะชัยบริการ'; // 截图所选公司(บริษัท มานะชัยบริการ จำกัด)

async function loginAndEnter(page) {
    await doUiLogin(page); // 填表 + 提交 + 等 token 落 localStorage
    // 多公司账号:登录后落公司选择页 · 选目标公司(单公司账号则无此页,跳过)
    const chooser = page.getByText(TARGET_COMPANY, { exact: false }).first();
    if (await chooser.isVisible({ timeout: 8000 }).catch(() => false)) {
        await chooser.click();
    }
    await expect(page.locator('#sidebar'), '进主应用').toBeVisible({ timeout: 20_000 });
}

async function gotoDashboard(page) {
    await loginAndEnter(page);
    await page.evaluate(() => window.routeTo && window.routeTo('dashboard'));
    await expect(page.locator('#page-dashboard'), '首页激活').toHaveClass(/active/, {
        timeout: 15_000,
    });
}

test.describe('订阅与计费(首页)', () => {
    test.skip(!hasCreds(), '需测试账号 · CI 无凭据时跳过');

    test('首页:顶部两卡(当前套餐|余额)+ 套餐卡 + 账单 · 旧统计卡/快捷已撤', async ({ page }) => {
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
        await expect(page.locator('#sub-plans .sub-plan'), '套餐卡三张').toHaveCount(3);
        await expect(page.locator('.sub-plan-btn').first(), '订阅按钮').toBeVisible();
        await expect(page.locator('#sub-records'), '账单容器').toBeVisible();

        // 旧 dashboard 主体应已撤掉
        await expect(page.locator('#dash-kpi-invoices'), '旧本月发票卡撤掉').toHaveCount(0);
        await expect(page.locator('.qa'), '旧快速操作撤掉').toHaveCount(0);

        await page.screenshot({
            path: 'tests/e2e/_artifacts/subscription-home.png',
            fullPage: true,
        });
    });

    test('套餐卡 hover 有动态交互(translateY 上浮)', async ({ page }) => {
        await gotoDashboard(page);
        const card = page.locator('#sub-plans .sub-plan').first();
        await expect(card).toBeVisible({ timeout: 15_000 });
        const before = await card.evaluate((el) => getComputedStyle(el).transform);
        await card.hover();
        await page.waitForTimeout(250); // 等 0.15s 过渡
        const after = await card.evaluate((el) => getComputedStyle(el).transform);
        expect(after, 'hover 后 transform 应改变(上浮)').not.toBe(before);
        await page.screenshot({ path: 'tests/e2e/_artifacts/subscription-hover.png' });
    });

    test('GET /api/me/subscription 返回 S/M/L 目录', async ({ page }) => {
        await doUiLogin(page); // 只需 token · 套餐目录不依赖已选公司(避免 sidebar flaky)
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
            return (await r.json()).balance_thb;
        });
        test.skip(balance >= 500, `余额 ฿${balance} ≥ 500 · 跳过以免真订阅扣费`);

        await page.locator('.sub-plan-btn[data-plan="L"]').click();
        await page.locator('#confirm-modal-ok').click();
        await expect(page.locator('#topup-v2-ov'), '余额不足应弹充值').toBeVisible({
            timeout: 10_000,
        });
    });
});
