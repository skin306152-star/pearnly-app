// Pearnly DMS · 波3/DL-8 操作员花名册 + 计费视图对齐主站 · 本地 stub 真浏览器验收(用完即删)
// ============================================================
// python http.server 静态服仓库根 + page.route stub /api/**(同 _in0d 先例)。token 预置进
// localStorage → boot 探针 200 → 进壳。覆盖:花名册 4 态(有名单/空/绑定码弹层/非 owner 藏 nav)
// + 计费(有订阅进度条 / 充值弹窗三步 / 记录明细两 tab)。断言 isVisible + 截图为证。
// 起法:npx playwright test tests/e2e/_w3_roster_billing_verify.spec.js
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8987;
const BASE = `http://127.0.0.1:${PORT}`;
const ROSTER_DIR = path.join(__dirname, '_artifacts', 'w3_roster');
const BILLING_DIR = path.join(__dirname, '_artifacts', 'w3_billing');
fs.mkdirSync(ROSTER_DIR, { recursive: true });
fs.mkdirSync(BILLING_DIR, { recursive: true });

const OPERATORS = {
    ok: true,
    items: [
        {
            user_id: 'op-1',
            display_name: 'สมชาย ขายดี',
            dms_role: 'sales',
            status: 'active',
            username: 'dmsop-1a2b3c4d',
            line_bound: true,
            line_display_name: 'Somchai',
            line_bound_at: '2026-07-18T09:00:00Z',
            endpoint_ready: true,
        },
        {
            user_id: 'op-2',
            display_name: 'มานะ อนุมัติ',
            dms_role: 'admin',
            status: 'inactive',
            username: 'dmsop-9f8e7d6c',
            line_bound: false,
            line_display_name: '',
            line_bound_at: null,
            endpoint_ready: false,
        },
    ],
};
const CREDITS = {
    has_tenant: true,
    is_owner: true,
    is_billing_exempt: false,
    balance_thb: 1234.5,
    pages_this_month: 320,
    tier_threshold: 200,
    current_rate: 0.75,
};
const SUB = {
    has_tenant: true,
    is_owner: true,
    is_billing_exempt: false,
    balance_thb: 1234.5,
    plans: [
        { code: 'S', quota: 100, fee: 150, over_rate: 1.5 },
        { code: 'M', quota: 200, fee: 250, over_rate: 1.25 },
        { code: 'L', quota: 500, fee: 500, over_rate: 1.0 },
    ],
    subscription: {
        plan_code: 'M',
        status: 'active',
        quota: 200,
        over_rate: 1.25,
        monthly_fee: 250,
        pages_used_this_cycle: 140,
        remaining: 60,
        auto_renew: true,
        cycle_start: '2026-07-01',
        cycle_end: '2026-07-31',
    },
};
const REC_USAGE = {
    rows: [
        {
            date: '2026-07-18 09:12',
            type: 'usage',
            description: 'บัตร สมชาย',
            pages: 1,
            cost_thb: 0,
        },
        {
            date: '2026-07-18 10:30',
            type: 'usage',
            description: 'ใบขับขี่',
            pages: 1,
            cost_thb: 1.5,
        },
        { date: '2026-07-01 00:00', type: 'subscription', description: 'Package M', cost_thb: 250 },
    ],
    total: 3,
    tab: 'usage',
    period: 'all',
};
const REC_TOPUP = {
    rows: [
        {
            id: 11,
            created_at: '2026-07-15 14:00',
            amount_thb: 1000,
            payer_name: 'เจ้าของ',
            status: 'approved',
        },
        {
            id: 12,
            created_at: '2026-07-16 09:00',
            amount_thb: 500,
            payer_name: '',
            status: 'pending',
        },
    ],
    total: 2,
    tab: 'topup',
    period: 'all',
};

let server;
test.beforeAll(async () => {
    server = await localServer.start(PORT, '/static/dms/dms.html');
});
test.afterAll(() => localServer.stop(server));

async function boot(page, { isOwner = true, operators = OPERATORS } = {}) {
    const errors = [];
    page.on('console', (m) => {
        if (m.type() === 'error') errors.push(m.text());
    });
    await page.route('**/api/**', (route) => {
        const url = route.request().url();
        const json = (o) =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(o),
            });
        if (url.includes('/api/dms/session'))
            return json(isOwner ? { ok: true, is_owner: true } : { ok: true, is_owner: false });
        if (url.includes('/bind-code'))
            return json({
                code: '482913',
                expires_at: new Date(Date.now() + 600000).toISOString(),
            });
        if (url.includes('/api/dms/operators')) return json(operators);
        if (url.includes('/api/me/credits')) return json(CREDITS);
        if (url.includes('/api/me/subscription')) return json(SUB);
        if (url.includes('/api/credits/records'))
            return json(url.includes('tab=topup') ? REC_TOPUP : REC_USAGE);
        if (url.includes('/api/credits/topup/request'))
            return json({ request_id: 1, status: 'pending' });
        if (url.includes('/api/me')) return json({ id: 'owner-1', role: 'owner' });
        return json({ ok: true });
    });
    await page.addInitScript(() => {
        try {
            localStorage.setItem('mrpilot_token', 'stub');
            localStorage.setItem('mrpilot_lang', 'zh');
        } catch (e) {
            void e;
        }
    });
    await page.goto(`${BASE}/static/dms/dms.html`);
    await page.waitForSelector('#dmsShell.on'); // 等 enterApp 摘门面显壳(applyOwnerNav 已跑)
    return errors;
}

test('roster · list state (owner)', async ({ page }) => {
    const errors = await boot(page);
    await page.click('.dms-nav-item[data-view="roster"]');
    await page.waitForSelector('.dms-op-table');
    await expect(page.locator('.dms-op-badge.sales')).toBeVisible();
    await expect(page.locator('.dms-op-badge.admin')).toBeVisible();
    await expect(page.locator('.dms-op-row').filter({ hasText: 'dmsop-1a2b3c4d' })).toBeVisible();
    expect(await page.locator('[data-op-act="code"]').count()).toBe(2);
    await page.screenshot({ path: path.join(ROSTER_DIR, 'roster-list.png'), fullPage: true });
    expect(errors, errors.join('\n')).toEqual([]);
});

test('roster · empty state', async ({ page }) => {
    await boot(page, { operators: { ok: true, items: [] } });
    await page.click('.dms-nav-item[data-view="roster"]');
    await expect(page.locator('#dms-view-roster .dms-state.empty')).toBeVisible();
    await page.screenshot({ path: path.join(ROSTER_DIR, 'roster-empty.png'), fullPage: true });
});

test('roster · bind-code overlay', async ({ page }) => {
    await boot(page);
    await page.click('.dms-nav-item[data-view="roster"]');
    await page.waitForSelector('.dms-op-table');
    await page.locator('[data-op-act="code"]').first().click();
    await page.waitForSelector('.dms-op-modal .dms-line-code');
    await expect(page.locator('#dms-op-code-val')).toHaveText('482913');
    await expect(page.locator('#dms-op-code-cd')).toBeVisible();
    await page.screenshot({ path: path.join(ROSTER_DIR, 'roster-bindcode.png') });
});

test('roster · non-owner hides nav', async ({ page }) => {
    await boot(page, { isOwner: false });
    await expect(page.locator('.dms-nav-item[data-view="roster"]')).toBeHidden();
    await page.screenshot({ path: path.join(ROSTER_DIR, 'roster-nonowner.png'), fullPage: true });
});

test('billing · subscription state (progress + current disabled)', async ({ page }) => {
    const errors = await boot(page);
    await page.click('.dms-nav-item[data-view="billing"]');
    await page.waitForSelector('.dms-bill-plan-now');
    await expect(page.locator('.dms-bill-prog > span')).toBeVisible();
    await expect(page.locator('.dms-bill-sub-badge.ok')).toBeVisible();
    await expect(page.locator('.dms-bill-plan.current')).toBeVisible();
    await expect(page.locator('.dms-bill-plan.current .btn')).toBeDisabled();
    // 进度条填充宽度 = 140/200 = 70%
    const w = await page.locator('.dms-bill-prog > span').evaluate((el) => el.style.width);
    expect(w).toBe('70%');
    await page.screenshot({
        path: path.join(BILLING_DIR, 'billing-subscription.png'),
        fullPage: true,
    });
    expect(errors, errors.join('\n')).toEqual([]);
});

test('billing · topup wizard three steps', async ({ page }) => {
    await boot(page);
    await page.click('.dms-nav-item[data-view="billing"]');
    await page.waitForSelector('[data-bill-topup]');
    await page.click('[data-bill-topup]');
    await page.waitForSelector('.modal-overlay .dms-bill-steps');
    await expect(page.locator('.dms-bill-step[data-step="1"]')).toBeVisible();
    await page.screenshot({ path: path.join(BILLING_DIR, 'topup-step1.png') });
    await page.fill('#tv-amt', '1000');
    await page.click('#tv-next');
    await page.waitForSelector('.dms-bill-step[data-step="2"].on');
    await expect(page.locator('#tv-warn')).toContainText('1,000');
    await page.screenshot({ path: path.join(BILLING_DIR, 'topup-step2.png') });
    await page.click('#tv-next');
    await page.waitForSelector('.dms-bill-step[data-step="3"].on');
    await expect(page.locator('#tv-dz')).toBeVisible();
    await page.screenshot({ path: path.join(BILLING_DIR, 'topup-step3.png') });
});

test('billing · records two tabs', async ({ page }) => {
    await boot(page);
    await page.click('.dms-nav-item[data-view="billing"]');
    await page.waitForSelector('.dms-bill-rec-row');
    await expect(page.locator('.dms-bill-rec-tab.on')).toHaveText('扣费记录');
    await expect(page.locator('.dms-bill-rec-badge.free')).toBeVisible();
    await page.screenshot({ path: path.join(BILLING_DIR, 'records-usage.png'), fullPage: true });
    await page.click('[data-bill-rectab="topup"]');
    await page.waitForSelector('.dms-bill-rec-dl');
    await expect(page.locator('.dms-bill-rec-tab.on')).toHaveText('充值记录');
    await expect(page.locator('.dms-bill-rec-dl').first()).toBeVisible();
    await page.screenshot({ path: path.join(BILLING_DIR, 'records-topup.png'), fullPage: true });
});
