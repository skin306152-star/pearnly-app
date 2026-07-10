// Pearnly E2E · 24 pos_only 精简外壳 · 侧栏菜单收干净(PS-2 · POS-体检报告 §5.3)
// ============================================================
// pos_only 是运营侧显式打标的拆卖收银店壳(不进自助业态选择器 TYPES 卡片)。本测试把
// 一个真账号临时切到 pos_only、验证侧栏可见 .nav-item ≤7 且只剩收银台入口/商品/库存/
// 简单报表/收银员管理(+ 首页 · 客户知识走独立 kbProbe 门控·不受本次改动影响),
// 截图存证,最后把业态切回原值(afterAll 幂等复原 · 不留痕)。
//
// business_type 走已有 tenant_modules 哨兵行(services/modules/store.py),不新增表;
// 切换用现成 PUT /api/me/onboarding(owner 专属)。
// ============================================================
/* global document, window, getComputedStyle */

const path = require('path');
const { test, expect } = require('@playwright/test');
const { hasCreds, ensureStorageState, STORAGE_STATE } = require('./_helpers/auth');
const { enterApp } = require('./_helpers/app');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

const OUT = path.join(process.cwd(), 'tests', 'e2e', '_artifacts', 'ps2');

// 六项目标名单(见交付报告)· 每项映射到实际侧栏节点 data-route
const EXPECTED_ROUTES = new Set([
    'dashboard', // 首页(隐含项 · 常显)
    'sales-products', // 商品(商品组内「商品数据」子项)
    'inventory', // 库存
    'sales-report', // 简单报表(销售报表)
    'pos-cashiers', // 收银员管理
    'nav-pos-switch', // 收银台入口(切到收银台)
]);

async function getModules(page) {
    return page.evaluate(async () => {
        const tok = localStorage.getItem('mrpilot_token');
        const r = await fetch('/api/me/modules', { headers: { Authorization: 'Bearer ' + tok } });
        return r.json();
    });
}

async function setBusinessType(page, businessType) {
    return page.evaluate(async (bt) => {
        const tok = localStorage.getItem('mrpilot_token');
        const r = await fetch('/api/me/onboarding', {
            method: 'PUT',
            headers: { Authorization: 'Bearer ' + tok, 'Content-Type': 'application/json' },
            body: JSON.stringify({ business_type: bt }),
        });
        return r.json();
    }, businessType);
}

async function visibleNavItems(page) {
    return page.evaluate(() =>
        Array.from(document.querySelectorAll('.nav-item'))
            .filter((el) => getComputedStyle(el).display !== 'none' && el.offsetParent !== null)
            .map((el) => el.dataset.route || el.id || '(no-route)')
    );
}

test.describe('pos_only 精简外壳 · 侧栏门控', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');
    test.use({ storageState: STORAGE_STATE });

    let originalBusinessType = null;

    test.beforeAll(async ({ browser }) => {
        await ensureStorageState(browser);
    });

    test.afterEach(async ({ page }) => {
        // 幂等复原:不管断言是否通过,都把账号切回原业态,不污染这个共用测试账号。
        if (originalBusinessType) {
            await setBusinessType(page, originalBusinessType);
        }
    });

    test('切 pos_only → 侧栏可见项 ≤7 且只留收银台/商品/库存/报表/收银员', async ({ page }) => {
        const guard = attachConsoleGuard(page);
        await enterApp(page);

        const before = await getModules(page);
        expect(before.ok, 'GET /api/me/modules 成功').toBe(true);
        originalBusinessType = before.data.business_type || 'firm';

        const flip = await setBusinessType(page, 'pos_only');
        expect(flip.ok, 'PUT pos_only 成功(owner 权限)').toBe(true);
        expect(flip.data.business_type).toBe('pos_only');

        await page.reload({ waitUntil: 'domcontentloaded' });
        await page
            .waitForFunction(() => typeof window.routeTo === 'function', null, { timeout: 20000 })
            .catch(() => {});
        await page.waitForTimeout(1500);

        const visible = await visibleNavItems(page);
        expect(
            visible.length,
            `pos_only 可见菜单项(实得:${visible.join(', ')})`
        ).toBeLessThanOrEqual(7);

        // 目标名单里的项必须都在(收银台入口/商品/库存/报表/收银员一个都不能少)
        for (const route of EXPECTED_ROUTES) {
            expect(visible, `${route} 应可见`).toContain(route);
        }
        // 30+ 会计/报税/识别/事务所菜单必须都不在
        for (const forbidden of [
            'acct-review',
            'tax-center',
            'vouchers',
            'purchase',
            'reconcile',
            'clients',
            'company',
            'exceptions',
            'integrations',
        ]) {
            expect(visible, `${forbidden} 不该出现在 pos_only 侧栏`).not.toContain(forbidden);
        }

        await page.screenshot({ path: path.join(OUT, 'pos_only_sidebar.png'), fullPage: true });

        assertNoConsoleErrors(expect, guard);
    });
});
