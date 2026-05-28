// tests/visual/baseline.spec.js · REFACTOR-WC-D5(2026-05-28 窗口 C)
//
// 10 页 screenshot baseline:登录 / 着陆 / 识别 / 历史 / 客户 / 对账 / 异常 / 设置 / 充值 / 超管
// 跑法见 tests/visual/README.md
// 凭据走 env(同 tests/e2e/01-login.spec.js 凭据 env 桥接策略)

const { test, expect } = require('@playwright/test');

const USER = process.env.PEARNLY_E2E_USER;
const PASS = process.env.PEARNLY_E2E_PASS;
const ADMIN_USER = process.env.PEARNLY_ADMIN_USER;
const ADMIN_PASS = process.env.PEARNLY_ADMIN_PASS;

const hasCreds = !!(USER && PASS);
const hasAdminCreds = !!(ADMIN_USER && ADMIN_PASS);

// 通用 mask · 替换动态内容防 baseline 抖动
const dynamicSelectors = [
    '[data-dynamic]',           // 任何标注为动态的元素(若 home.js 有标注)
    '.timestamp',                // 时间戳
    '.balance-amount',           // 余额(每次跑可能不同)
    '.notification-badge',       // 通知数量
    '[data-test-mask]',          // 显式 mask hooks
];

async function maskDynamicContent(page) {
    try {
        await page.evaluate((selectors) => {
            for (const sel of selectors) {
                document.querySelectorAll(sel).forEach((el) => {
                    el.textContent = '[masked]';
                });
            }
        }, dynamicSelectors);
    } catch (_) {
        /* silent: 页面没这些 selector 是正常的 */
    }
}

async function loginAs(page, user, pass) {
    await page.goto('/login');
    // 通用 login form selectors(若变动 · 跟 tests/e2e/01-login.spec.js 同步)
    await page.fill('input[type="email"], input[name="username"]', user);
    await page.fill('input[type="password"], input[name="password"]', pass);
    await Promise.all([
        page.waitForURL((url) => !url.pathname.startsWith('/login'), { timeout: 15_000 }).catch(() => null),
        page.click('button[type="submit"]'),
    ]);
    await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => null);
}

// ────────────────────────────────────────────────────────────────
// 公开页 · 不需要凭据
// ────────────────────────────────────────────────────────────────

test('01 · 登录页 baseline', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await maskDynamicContent(page);
    await expect(page).toHaveScreenshot('01-login.png', { fullPage: true });
});

test('02 · 着陆页 baseline', async ({ page }) => {
    // 着陆页 = 根路径(未登录访问会重定向到 /login · 那就拍 login)
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await maskDynamicContent(page);
    await expect(page).toHaveScreenshot('02-landing.png', { fullPage: true });
});

// ────────────────────────────────────────────────────────────────
// 认证页 · 需要 PEARNLY_E2E_USER / _PASS
// ────────────────────────────────────────────────────────────────

test.describe('认证后页面', () => {
    test.skip(!hasCreds, '需要 PEARNLY_E2E_USER + _PASS env 才跑');

    test.beforeEach(async ({ page }) => {
        await loginAs(page, USER, PASS);
    });

    test('03 · 识别(上传)页 baseline', async ({ page }) => {
        // 上传入口可能在 /home / / · 走 hash 路由
        await page.goto('/');
        await page.waitForLoadState('networkidle');
        // 切到上传 tab(若有 hash 路由)
        await page.evaluate(() => {
            if (typeof window.routeTo === 'function') {
                try { window.routeTo('upload'); } catch (_) { /* silent */ }
            } else {
                window.location.hash = '#upload';
            }
        });
        await page.waitForTimeout(500);
        await maskDynamicContent(page);
        await expect(page).toHaveScreenshot('03-recognize.png', { fullPage: true });
    });

    test('04 · 历史页 baseline', async ({ page }) => {
        await page.goto('/#history');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(500);
        await maskDynamicContent(page);
        await expect(page).toHaveScreenshot('04-history.png', { fullPage: true });
    });

    test('05 · 客户页 baseline', async ({ page }) => {
        await page.goto('/#clients');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(500);
        await maskDynamicContent(page);
        await expect(page).toHaveScreenshot('05-clients.png', { fullPage: true });
    });

    test('06 · 对账中心 baseline', async ({ page }) => {
        await page.goto('/#reconcile');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(500);
        await maskDynamicContent(page);
        await expect(page).toHaveScreenshot('06-reconcile.png', { fullPage: true });
    });

    test('07 · 异常中心 baseline', async ({ page }) => {
        await page.goto('/#exceptions');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(500);
        await maskDynamicContent(page);
        await expect(page).toHaveScreenshot('07-exceptions.png', { fullPage: true });
    });

    test('08 · 设置页 baseline', async ({ page }) => {
        await page.goto('/#settings');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(500);
        await maskDynamicContent(page);
        await expect(page).toHaveScreenshot('08-settings.png', { fullPage: true });
    });

    test('09 · 充值页 baseline', async ({ page }) => {
        await page.goto('/#recharge');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(500);
        await maskDynamicContent(page);
        await expect(page).toHaveScreenshot('09-recharge.png', { fullPage: true });
    });
});

// ────────────────────────────────────────────────────────────────
// 超管 admin SPA · 需要 PEARNLY_ADMIN_USER / _PASS
// ────────────────────────────────────────────────────────────────

test('10 · 超管(admin)baseline', async ({ page }) => {
    test.skip(!hasAdminCreds, '需要 PEARNLY_ADMIN_USER + _PASS env 才跑');
    await loginAs(page, ADMIN_USER, ADMIN_PASS);
    await page.goto('/admin');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(800);
    await maskDynamicContent(page);
    await expect(page).toHaveScreenshot('10-admin.png', { fullPage: true });
});
