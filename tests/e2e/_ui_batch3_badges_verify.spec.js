// UI 极致线批3 · 清单 #4 队列头徽章未决数 · 本地 stub 真浏览器验收
// ============================================================
// 自起静态服(_local_static_server)+ page.route stub /api/**(同 _sa2 先例)。验收:
//   ① 裁决前:徽章按 undecided_count 显数(4×勾稽红灯 / 2×方向不明 / 60×销项票)
//   ② 部分已裁:数字掉到未决余数并追加「已裁 n」(不等引擎重跑)
//   ③ 全部已裁:徽章转灰底(.chip.n)只留「已裁 n」,不再显 0 ×
//   ④ 旧响应缺 undecided/decided 字段:回落总数显示,行为同旧版
// 截图存 tests/e2e/_artifacts/ui-batch3/(裁决前后各一张)。
//
// 起法:npx playwright test tests/e2e/_ui_batch3_badges_verify.spec.js
/* global window */

const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8989;
const BASE = `http://127.0.0.1:${PORT}`;
const PAGE = `${BASE}/static/dist/ai.html`;
const ART = path.join(__dirname, '_artifacts', 'ui-batch3');

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT);
});

test.afterAll(() => {
    localServer.stop(server);
});

// group(count, undecided, decided):undecided/decided 传 null 模拟旧响应缺字段。
function group(reason, severity, count, undecided, decided) {
    const g = { flag_reason: reason, severity, count };
    if (undecided !== null) g.undecided_count = undecided;
    if (decided !== null) g.decided_count = decided;
    return g;
}

function queueFixture(groups) {
    const total = groups.reduce((s, g) => s + g.count, 0);
    return {
        period: null,
        clients: [
            {
                workspace_client_id: 1,
                client_name: 'Sister Makeup',
                client_tax_id: '0105555167627',
                pool_pending: 0,
                orders: [
                    {
                        work_order_id: 'wo-b3',
                        workspace_client_id: 1,
                        client_name: 'Sister Makeup',
                        client_tax_id: '0105555167627',
                        period: '2569-05',
                        status: 'stuck',
                        current_step: 'reconcile',
                        updated_at: '2026-07-14T10:00:00+07:00',
                        next_due_efiling: '2569-06-15',
                        next_due_paper: '2569-06-07',
                        pool_pending: 0,
                        is_rework: false,
                        flagged_groups: groups,
                        flagged_total: total,
                        top_severity: 'crit',
                        sod: null,
                    },
                ],
            },
        ],
        flagged_items: [],
        counts: { clients: 1, orders: 1, flagged: total },
    };
}

async function boot(page, groups, lang = 'zh') {
    await page.route('**/api/**', (route) => {
        const p = new URL(route.request().url()).pathname;
        const json = (body) =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(body),
            });
        if (p === '/api/workorder/orders') return json({ orders: [], count: 0 });
        if (p === '/api/me') return json({ username: 'reviewer' });
        if (p === '/api/workorder/review-queue') return json(queueFixture(groups));
        if (p === '/api/ai/client-pool') return json({ groups: [] });
        return json({});
    });
    await page.addInitScript(
        ([l]) => {
            window.localStorage.setItem('mrpilot_token_ai', 'tok-b3');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [lang]
    );
    await page.goto(PAGE + '#/pool');
    await page.waitForSelector('.riq-wo-flags .chip', { timeout: 15000 });
}

test.describe('清单 #4 · 队列头徽章按未决数显示(本地 stub 真浏览器)', () => {
    test('裁决前:徽章显全部未决数', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await boot(page, [
            group('amount_math_fail', 'crit', 4, 4, 0),
            group('direction_ambiguous', 'warn', 2, 2, 0),
            group('sales_doc_review', 'warn', 60, 60, 0),
        ]);
        const chips = page.locator('.riq-wo-flags .chip');
        await expect(chips).toHaveCount(3);
        await expect(chips.nth(0)).toContainText('4 ×');
        await expect(chips.nth(1)).toContainText('2 ×');
        await expect(chips.nth(2)).toContainText('60 ×');
        await expect(page.locator('.riq-wo-flags')).not.toContainText('已裁');
        await page.screenshot({ path: path.join(ART, '4-badges-before.png'), fullPage: false });
    });

    test('部分已裁:数字掉到余数并追加已裁数', async ({ page }) => {
        await boot(page, [group('amount_math_fail', 'crit', 4, 1, 3)]);
        const chip = page.locator('.riq-wo-flags .chip').first();
        await expect(chip).toContainText('1 ×');
        await expect(chip).toContainText('已裁 3');
        await expect(chip).not.toHaveClass(/\bn\b/);
    });

    test('全部已裁:徽章转灰只留已裁数,不显 0 ×', async ({ page }) => {
        await boot(page, [
            group('amount_math_fail', 'crit', 4, 0, 4),
            group('direction_ambiguous', 'warn', 2, 0, 2),
            group('sales_doc_review', 'warn', 60, 0, 60),
        ]);
        const chips = page.locator('.riq-wo-flags .chip');
        await expect(chips).toHaveCount(3);
        for (let i = 0; i < 3; i++) {
            await expect(chips.nth(i)).toHaveClass(/\bn\b/);
            await expect(chips.nth(i)).toBeVisible();
        }
        await expect(chips.nth(0)).toContainText('已裁 4');
        await expect(chips.nth(2)).toContainText('已裁 60');
        await expect(page.locator('.riq-wo-flags')).not.toContainText('0 ×');
        await page.screenshot({ path: path.join(ART, '4-badges-after.png'), fullPage: false });
    });

    test('旧响应缺字段:回落总数显示', async ({ page }) => {
        await boot(page, [group('amount_math_fail', 'crit', 4, null, null)]);
        const chip = page.locator('.riq-wo-flags .chip').first();
        await expect(chip).toContainText('4 ×');
        await expect(chip).not.toContainText('已裁');
    });

    for (const lang of ['th', 'en', 'ja']) {
        test(`四语(${lang}):已裁注记不裸 key`, async ({ page }) => {
            await boot(page, [group('amount_math_fail', 'crit', 4, 0, 4)], lang);
            const text = await page.locator('.riq-wo-flags').innerText();
            expect(text).not.toContain('riq_flag_decided');
            expect(text).toContain('4');
        });
    }
});
