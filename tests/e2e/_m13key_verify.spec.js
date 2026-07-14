// M1-3KEY · 交付包页三键出口 · 本地 stub 真浏览器验收
// ============================================================
// 起法同 _uidebt0714_verify.spec.js:_local_static_server 起静态服(真 ai.js/ai.css/ai.html)+
// page.route stub /api/**。真 DOM / 真 CSS / 真点击 / 真键盘 / 真下载事件,只桩网络层。覆盖:
//   ① review 态 → 键一签批成功显名 · 键三退回后状态翻 running(键随之禁用)
//   ② 冻结(archive)单 → 键一/键三 disabled(computedStyle 抓)+「已冻结」title · 键二仍可下载
//   ③ 交付物清单渲染 shadow_workpaper 行(KIND_ORDER 补列)
//   ④ 四语按钮不裸 key
// 截图存 tests/e2e/_artifacts/m13key/。金标数字/桥翻码/Σ借=Σ贷走真库真跑(见施工记录),本
// spec 只验前端交互与四态。
/* global window, document */
const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8991;
const BASE = `http://127.0.0.1:${PORT}`;
const PAGE = `${BASE}/static/dist/ai.html`;
const ART = path.join(__dirname, '_artifacts', 'm13key');
const CLIENT_ID = '2';
const ORDER_ID = 'wo-3key';

// sub=reviewer 的假 JWT(actorLabel 回落链末端取 sub 前八位 → "reviewer"),让签批显名可断言。
const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
const TOKEN = `${b64({ alg: 'HS256' })}.${b64({ sub: 'reviewer' })}.sig`;

let server;
test.beforeAll(async () => {
    server = await localServer.start(PORT);
});
test.afterAll(() => localServer.stop(server));

const SHADOW = {
    entries: [
        {
            source: '进项票 #1',
            rule_key: 'r_purchase',
            dr_cr: 'debit',
            account_code: '5290',
            account_name: '杂项费用',
            amount: '1000.00',
        },
        {
            source: '进项票 #1',
            rule_key: 'r_purchase',
            dr_cr: 'debit',
            account_code: '1140',
            account_name: '进项税',
            amount: '70.00',
        },
        {
            source: '进项票 #1',
            rule_key: 'r_purchase',
            dr_cr: 'credit',
            account_code: '2010',
            account_name: '应付账款',
            amount: '1070.00',
        },
    ],
    accounts: [],
    trial_balance: { debit: '1070.00', credit: '1070.00', diff: '0.00', balanced: true },
};

const DELIVERABLES = [
    {
        kind: 'pp30_draft',
        has_file: true,
        numbers: { output_vat: '350.00', input_vat: '70.00', tax_due: '280.00' },
    },
    { kind: 'shadow_workpaper', has_file: true, numbers: { balanced: true, entry_count: 3 } },
    { kind: 'evidence_index', has_file: true, numbers: {} },
];

function orderDetail(status) {
    return {
        id: ORDER_ID,
        status,
        current_step: status === 'review' ? 'package' : 'reconcile',
        needs: [],
        blocked_reasons: [],
        numbers: { output_vat: '350.00', input_vat: '70.00', tax_due: '280.00', period: '2569-05' },
        shadow_draft: SHADOW,
        deliverables: DELIVERABLES.map((d) => ({ kind: d.kind, numbers: d.numbers })),
    };
}

// 有状态路由:reject 后 getOrder 翻 running(验状态机推进,键随之禁用)。initialStatus 起始态。
async function routeApi(page, { initialStatus }) {
    const state = { status: initialStatus, rejected: false, exported: false };
    await page.route('**/api/**', (route) => {
        const req = route.request();
        const u = new URL(req.url());
        const p = u.pathname;
        const json = (body, code = 200) =>
            route.fulfill({
                status: code,
                contentType: 'application/json',
                body: JSON.stringify(body),
            });

        if (p === '/api/me') return json({ username: 'reviewer' });
        if (p === '/api/workorder/orders' && u.searchParams.has('limit'))
            return json({ orders: [], count: 0 });
        if (p === `/api/workspace/clients/${CLIENT_ID}`)
            return json({ client: { id: CLIENT_ID, name: 'Sister Makeup' } });
        if (p === '/api/workorder/orders' && u.searchParams.get('client_id') === CLIENT_ID)
            return json({ orders: [{ id: ORDER_ID, period: '2569-05' }] });
        if (p === `/api/workorder/orders/${ORDER_ID}`) return json(orderDetail(state.status));
        if (p === `/api/workorder/orders/${ORDER_ID}/deliverables`)
            return json({ deliverables: DELIVERABLES });
        if (p === `/api/workorder/orders/${ORDER_ID}/review` && req.method() === 'POST')
            return json({ ok: true, event_id: 1 });
        if (p === `/api/workorder/orders/${ORDER_ID}/review-reject` && req.method() === 'POST') {
            state.rejected = true;
            state.status = 'running';
            return json({ status: 'running', reopened_steps: ['reconcile'] });
        }
        if (p === `/api/workorder/orders/${ORDER_ID}/entries-export`) {
            state.exported = true;
            return route.fulfill({
                status: 200,
                headers: {
                    'Content-Disposition':
                        "attachment; filename*=UTF-8''Sister%20Makeup_2569-05_entries.xlsx",
                },
                contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                body: Buffer.from('PK fake-xlsx-bytes'),
            });
        }
        return json({});
    });
    return state;
}

async function boot(page, status, lang) {
    await routeApi(page, { initialStatus: status });
    await page.addInitScript(
        ([t, l]) => {
            window.localStorage.setItem('mrpilot_token', t);
            window.localStorage.setItem('mrpilot_lang', l || 'zh');
        },
        [TOKEN, lang]
    );
    await page.goto(PAGE + `#/client/${CLIENT_ID}/pkg`);
    await page.waitForSelector('.pkg-actions', { timeout: 15000 });
}

async function isEnabled(loc) {
    return loc.evaluate((el) => !el.disabled);
}

test.describe('M1-3KEY · review 态', () => {
    test('三键可用 · 键一签批显名 · 键三退回翻 running', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await boot(page, 'review');

        const sign = page.locator('[data-action="pkg-sign"]');
        const exp = page.locator('[data-action="pkg-export"]');
        const ret = page.locator('[data-action="pkg-return"]');
        await expect(sign).toBeVisible();
        expect(await isEnabled(sign)).toBe(true);
        expect(await isEnabled(exp)).toBe(true);
        expect(await isEnabled(ret)).toBe(true);
        // shadow_workpaper 行渲染(KIND_ORDER 补列)
        await expect(page.locator('.pkg-files')).toContainText('影子底稿');
        await page.screenshot({ path: path.join(ART, '1-review-three-keys.png'), fullPage: false });

        // 键一:签批 → 翻「已标记待签 · reviewer」
        await sign.click();
        const signed = page.locator('.pkg-action-row .btn.pri[disabled]');
        await expect(signed).toBeVisible();
        await expect(signed).toContainText('已标记待签');
        await expect(signed).toContainText('reviewer');
        await page.screenshot({ path: path.join(ART, '2-signed-named.png'), fullPage: false });

        // 键三:reason 弹窗 → 退回 → 状态翻 running(重拉详情后键禁用)+ 人话回执
        page.once('dialog', (d) => d.accept('税额可疑'));
        await ret.click();
        await expect(page.locator('.pkg-action-note.ok')).toContainText('已退回');
        // running 态:签批/退回键禁用(computedStyle 佐证禁用视觉)
        await expect(page.locator('[data-action="pkg-return"]')).toBeDisabled();
        await expect(page.locator('[data-action="pkg-sign"]')).toBeDisabled();
        const op = await page
            .locator('[data-action="pkg-return"]')
            .evaluate((el) => window.getComputedStyle(el).opacity);
        expect(Number(op)).toBeLessThan(1);
        await page.screenshot({ path: path.join(ART, '3-returned-running.png'), fullPage: false });
    });
});

test.describe('M1-3KEY · 冻结(archive)态', () => {
    test('键一/键三 disabled+已冻结 · 键二可下载 xlsx', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await boot(page, 'archive');

        const sign = page.locator('[data-action="pkg-sign"]');
        const exp = page.locator('[data-action="pkg-export"]');
        const ret = page.locator('[data-action="pkg-return"]');
        await expect(sign).toBeDisabled();
        await expect(ret).toBeDisabled();
        expect(await sign.getAttribute('title')).toBe('已冻结');
        expect(await isEnabled(exp)).toBe(true);
        await page.screenshot({ path: path.join(ART, '4-frozen-keys.png'), fullPage: false });

        // 键二:真下载事件(saveBlob → <a download> 点击)
        const [download] = await Promise.all([page.waitForEvent('download'), exp.click()]);
        expect(download.suggestedFilename()).toContain('entries');
        expect(download.suggestedFilename()).toContain('.xlsx');
        await page.screenshot({
            path: path.join(ART, '5-frozen-export-done.png'),
            fullPage: false,
        });
    });
});

for (const lang of ['th', 'en', 'ja']) {
    test(`四语(${lang}):三键不裸 key`, async ({ page }) => {
        await boot(page, 'review', lang);
        for (const action of ['pkg-sign', 'pkg-export', 'pkg-return']) {
            const t = (await page.locator(`[data-action="${action}"]`).innerText()).trim();
            expect(t.length).toBeGreaterThan(0);
            expect(t).not.toContain('pkg_');
        }
        if (lang === 'th') {
            await page.screenshot({ path: path.join(ART, '6-lang-th.png'), fullPage: false });
        }
    });
}

test('手机 390:三键区不横溢', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await boot(page, 'review');
    await expect(page.locator('.pkg-action-row')).toBeVisible();
    const scrollW = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientW = await page.evaluate(() => document.documentElement.clientWidth);
    expect(scrollW).toBeLessThanOrEqual(clientW + 1);
    await page.screenshot({ path: path.join(ART, '7-mobile-390.png'), fullPage: false });
});
