// Pearnly E2E · 24 pos_only 收银壳 · 侧栏 + 头像菜单白名单 + 免强制选套账门(Zihao 2026-07-10)
// ============================================================
// pos_only 是运营侧显式打标的拆卖收银店壳。本测试把一个真账号临时切到 pos_only,验证:
//   ① 登录不弹「强制选套账」门,静默落套账直接进工作台(收银老板无多套账概念);
//   ② 侧栏只留【收银业务 / 公司资料 / 商品系统 / 采购系统 / 销售系统 + 底部账号块】;
//   ③ 头像菜单只留【暗夜模式 / 帮助 & 反馈 / 退出登录】(团队与权限也砍)。
//   清单外一律 isVisible=false(真浏览器 getComputedStyle,不数 class)。afterEach 幂等复原业态。
//
// 解耦要点:pos_only 后端只开 pos+inventory,却要出「采购/销售」菜单 —— 证明菜单可见性由
// 白名单写死、与模块开关脱钩。切业态用现成 owner 专属 PUT /api/me/onboarding。
// ============================================================
/* global document, window */

const path = require('path');
const { test, expect } = require('@playwright/test');
const { hasCreds, ensureStorageState, STORAGE_STATE } = require('./_helpers/auth');
const { enterApp, getModules, dismissWorkspaceModal } = require('./_helpers/app');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

const OUT = path.join(process.cwd(), 'tests', 'e2e', '_artifacts', 'nav-preset');

const SIDEBAR = {
    dashboard: '.nav-item[data-route="dashboard"]',
    cowork: '[data-collapsible="firm"]',
    products: '[data-collapsible="products"]',
    purchases: '[data-collapsible="expense"]',
    sales: '[data-collapsible="sales"]',
    accounting: '[data-collapsible="accounting"]',
    pos: '#nav-group-pos',
    clients: '.nav-item[data-route="clients"]',
    company: '.nav-item[data-route="company"]',
    exceptions: '.nav-item[data-route="exceptions"]',
    integrations: '#nav-integrations',
    enroll: '#nav-enroll',
    knowledge: '#nav-knowledge',
};
const AVATAR = {
    settings: '#avatar-menu-settings',
    console: '#avatar-menu-console',
    billing: '#avatar-menu-billing',
    shortcuts: '#avatar-menu-shortcuts',
    theme: '#avatar-menu-theme',
    help: '#avatar-menu-help',
    logout: '#avatar-menu-logout',
};

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

// 折叠组默认展开(max-height),但持久化可能收起 → 收起态子项高度 0、Playwright 判不可见。
// 本测试只断言"组是否属于白名单",与折叠无关,故先全部展开,断言才稳。
async function expandAllGroups(page) {
    await page.evaluate(() =>
        document
            .querySelectorAll('.nav-collapsible.collapsed')
            .forEach((g) => g.classList.remove('collapsed'))
    );
}

test.describe('pos_only 收银壳 · 侧栏 + 头像 + 免门', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');
    test.use({ storageState: STORAGE_STATE });

    let originalBusinessType = null;

    test.beforeAll(async ({ browser }) => {
        await ensureStorageState(browser);
    });

    test.afterEach(async ({ page }) => {
        if (originalBusinessType) await setBusinessType(page, originalBusinessType);
    });

    test('pos_only:免强制选套账门 + 侧栏 5 组 + 头像只留 3 项', async ({ page }) => {
        const guard = attachConsoleGuard(page);
        await enterApp(page);

        const before = await getModules(page);
        expect(before.ok, 'GET /api/me/modules 成功').toBe(true);
        originalBusinessType = before.data.business_type || 'firm';

        const flip = await setBusinessType(page, 'pos_only');
        expect(flip.ok, 'PUT pos_only 成功(owner 权限)').toBe(true);
        expect(flip.data.business_type).toBe('pos_only');

        // 清 sessionStorage 模拟"新登录会话"(门此时会判定强制),再全新进场——直接 goto(不用
        // enterApp 的自动关门),看 pos_only 是否被静默放行。
        await page.evaluate(() => {
            try {
                sessionStorage.clear();
            } catch {
                /* 私模 */
            }
        });
        await page.goto('/home');

        // ① 免门:侧栏可见(没被全屏门盖住)+ 套账选择列表从未弹出 + 门壳静默自解。
        await expect(page.locator('#sidebar'), '进工作台(门未拦)').toBeVisible({ timeout: 20000 });
        await expect(
            page.locator('#workspace-gate-root [data-wsg-pick]'),
            'pos_only 不该弹套账选择列表'
        ).toHaveCount(0);
        await expect(page.locator('#workspace-gate-root'), '门壳应静默消失').toHaveCount(0, {
            timeout: 10000,
        });

        // 等新代码把头像白名单写好(=module-nav 按 pos_only 跑完 · 也抓 CDN 旧缓存)。
        await page.waitForFunction(
            () => Array.isArray(window._avatarShellHide) && window._avatarShellHide.length === 4,
            null,
            { timeout: 20000 }
        );
        await dismissWorkspaceModal(page); // 登录软弹(#ws-modal)若在 → 关掉,免挡头像点击
        await expandAllGroups(page);

        // ② 侧栏白名单内可见 / 外隐藏。
        for (const key of ['pos', 'company', 'products', 'purchases', 'sales']) {
            await expect(page.locator(SIDEBAR[key]), `${key} 应可见`).toBeVisible();
        }
        for (const key of [
            'dashboard',
            'cowork',
            'accounting',
            'clients',
            'exceptions',
            'integrations',
            'enroll',
            'knowledge',
        ]) {
            await expect(page.locator(SIDEBAR[key]), `${key} 应隐藏`).toBeHidden();
        }

        // ③ 头像菜单:3 留 4 砍(团队与权限也砍)。
        await page.locator('#avatar-btn').click();
        await expect(page.locator('#avatar-popup')).toHaveClass(/show/);
        for (const key of ['theme', 'help', 'logout']) {
            await expect(page.locator(AVATAR[key]), `头像 ${key} 应可见`).toBeVisible();
        }
        for (const key of ['settings', 'billing', 'shortcuts', 'console']) {
            await expect(page.locator(AVATAR[key]), `头像 ${key} 应隐藏`).toBeHidden();
        }

        await page.screenshot({ path: path.join(OUT, 'pos_only.png'), fullPage: true });

        // 切业态过渡的诚实 403 豁免:pos_only 关掉 knowledge/recon 后 boot 探针被服务端 403 拒
        // (模块门控在工作),浏览器把 4xx 资源载入记成 console.error(消息不含 URL,无法按端点滤)。
        assertNoConsoleErrors(expect, guard, { allow: [/Failed to load resource.*403/] });
    });
});
