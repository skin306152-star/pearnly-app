// UI-DEBT-0714 · 交付包/工单页四处体验债 · 本地 stub 真浏览器验收
// ============================================================
// 自起静态服(_local_static_server)+ page.route stub /api/**(同 _mc1b2/_ui_batch3 先例):
// 真渲染代码(static/dist/ai.js/ai.css/ai.html 原样加载,零改造)+ 真 DOM + 真键盘/真点击 +
// 真 CSS,只桩网络层。覆盖派单书②③④三条(①冻结卡文件名剥壳走真实本地全栈+真库,见
// 施工记录,本 spec 不重复起真后端)。截图存 tests/e2e/_artifacts/uidebt0714/。
//
// 起法:npx playwright test tests/e2e/_uidebt0714_verify.spec.js
/* global window, document */
const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8990;
const BASE = `http://127.0.0.1:${PORT}`;
const PAGE = `${BASE}/static/dist/ai.html`;
const ART = path.join(__dirname, '_artifacts', 'uidebt0714');

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT);
});

test.afterAll(() => {
    localServer.stop(server);
});

function group(reason, severity, count, undecided, decided) {
    return {
        flag_reason: reason,
        severity,
        count,
        undecided_count: undecided,
        decided_count: decided,
    };
}

// 清单 #2 用的 /pool 队列 fixture(同 _ui_batch3_badges_verify.spec.js 先例)。
function queueFixture(groups, status) {
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
                        work_order_id: 'wo-debt2',
                        workspace_client_id: 1,
                        client_name: 'Sister Makeup',
                        client_tax_id: '0105555167627',
                        period: '2569-05',
                        status: status || 'stuck',
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

// 清单 #3/#4 共用一张缺料工单:pkg 页面 blockedHtml 里 needs=['intake_files'] 出「去收料补」,
// 点了跳收料 tab;收料 tab 的上传区分两批选文件验累积去重(needsSales=false,intake_files
// 不含 sales_summary,不弹人工填表单,单测收料区本体)。
const ORDER_ID = 'wo-debt3';
const CLIENT_ID = '2';

function orderDetailFixture() {
    return {
        id: ORDER_ID,
        status: 'stuck',
        current_step: 'reconcile',
        needs: ['intake_files'],
        blocked_reasons: [],
        numbers: {},
    };
}

// handlers: [{method, path, query?, body}]。path 精确比对 pathname;query(可选)收
// URLSearchParams 判真判假——区分同 pathname 不同用途的两条端点(gate 探针
// listOrders({limit:1}) vs 客户页 listOrders({client_id})都是 /api/workorder/orders)。
async function routeApi(page, handlers) {
    await page.route('**/api/**', (route) => {
        const req = route.request();
        const u = new URL(req.url());
        const json = (body) =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(body),
            });
        if (u.pathname === '/api/me') return json({ username: 'reviewer' });
        const hit = handlers.find((h) => {
            if (h.method !== req.method() || h.path !== u.pathname) return false;
            return h.query ? h.query(u.searchParams) : true;
        });
        if (hit) return json(hit.body);
        return json({});
    });
}

async function bootWith(page, handlers, hash, lang) {
    await routeApi(page, handlers);
    await page.addInitScript(
        ([l]) => {
            window.localStorage.setItem('mrpilot_token', 'tok-debt0714');
            window.localStorage.setItem('mrpilot_lang', l || 'zh');
        },
        [lang]
    );
    await page.goto(PAGE + hash);
}

const GATE_PROBE = {
    method: 'GET',
    path: '/api/workorder/orders',
    query: (q) => q.has('limit'),
    body: { orders: [], count: 0 },
};

function clientHandlers(deliverables) {
    const h = [
        GATE_PROBE,
        {
            method: 'GET',
            path: `/api/workspace/clients/${CLIENT_ID}`,
            body: { client: { id: CLIENT_ID, name: 'Debt Test Co' } },
        },
        {
            method: 'GET',
            path: '/api/workorder/orders',
            query: (q) => q.get('client_id') === CLIENT_ID,
            body: { orders: [{ id: ORDER_ID, period: '2569-06' }] },
        },
        {
            method: 'GET',
            path: `/api/workorder/orders/${ORDER_ID}`,
            body: orderDetailFixture(),
        },
    ];
    if (deliverables) {
        h.push({
            method: 'GET',
            path: `/api/workorder/orders/${ORDER_ID}/deliverables`,
            body: { deliverables },
        });
    }
    return h;
}

test.describe('清单 #2 · 卡住提示条读未决数(不再照总数矛盾于徽章)', () => {
    test('有未决票:提示条显示且与徽章口径一致', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await bootWith(
            page,
            [
                GATE_PROBE,
                {
                    method: 'GET',
                    path: '/api/workorder/review-queue',
                    body: queueFixture([group('amount_math_fail', 'crit', 4, 4, 0)]),
                },
                { method: 'GET', path: '/api/ai/client-pool', body: { groups: [] } },
            ],
            '#/pool'
        );
        await page.waitForSelector('.riq-wo-flags .chip', { timeout: 15000 });
        await expect(page.locator('.riq-wo-blocked-note')).toBeVisible();
        await expect(page.locator('.riq-wo-flags .chip').first()).toContainText('4 ×');
        await page.screenshot({ path: path.join(ART, '2-note-visible.png'), fullPage: false });
    });

    test('全部已裁(徽章转已裁):提示条随之消失,不再矛盾', async ({ page }) => {
        await bootWith(
            page,
            [
                GATE_PROBE,
                {
                    method: 'GET',
                    path: '/api/workorder/review-queue',
                    body: queueFixture([group('amount_math_fail', 'crit', 4, 0, 4)]),
                },
                { method: 'GET', path: '/api/ai/client-pool', body: { groups: [] } },
            ],
            '#/pool'
        );
        await page.waitForSelector('.riq-wo-flags .chip', { timeout: 15000 });
        await expect(page.locator('.riq-wo-flags .chip').first()).toContainText('已裁 4');
        await expect(page.locator('.riq-wo-blocked-note')).toHaveCount(0);
        await page.screenshot({ path: path.join(ART, '2-note-gone.png'), fullPage: false });
    });
});

test.describe('清单 #3 · 缺料卡「去收料补」跳转收料 tab', () => {
    test('needs 非空:按钮可见,点击落到收料 tab', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await bootWith(
            page,
            clientHandlers([{ kind: 'evidence_index', has_file: true, numbers: {} }]),
            `#/client/${CLIENT_ID}/pkg`
        );
        const goBtn = page.locator('[data-action="pkg-go-intake"]');
        await expect(goBtn).toBeVisible();
        await page.screenshot({
            path: path.join(ART, '3-pkg-blocked-needs-btn.png'),
            fullPage: false,
        });
        await goBtn.click();
        await expect(page).toHaveURL(new RegExp(`#/client/${CLIENT_ID}/intake$`));
        await expect(page.locator('#ikDrop')).toBeVisible();
        await page.screenshot({ path: path.join(ART, '3-landed-on-intake.png'), fullPage: false });
    });
});

test.describe('清单 #4 · 分批选择文件累积不顶替(去重按 name+size)', () => {
    test('两批选择:数量为两批之和,重复文件去重', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await bootWith(page, clientHandlers(null), `#/client/${CLIENT_ID}/intake`);
        await page.waitForSelector('#ikDrop', { timeout: 15000 });

        const fileInput = page.locator('#ikFileInput');
        await fileInput.setInputFiles([
            { name: 'a.jpg', mimeType: 'image/jpeg', buffer: Buffer.from('aaa') },
            { name: 'b.jpg', mimeType: 'image/jpeg', buffer: Buffer.from('bbb') },
        ]);
        await expect(page.locator('.dz-count b')).toHaveText('2');

        // 第二批:c.jpg 是新文件,a.jpg 同名同字节重选(去重不应重复计入)。
        await fileInput.setInputFiles([
            { name: 'c.jpg', mimeType: 'image/jpeg', buffer: Buffer.from('ccc') },
            { name: 'a.jpg', mimeType: 'image/jpeg', buffer: Buffer.from('aaa') },
        ]);
        await expect(page.locator('.dz-count b')).toHaveText('3');
        await page.screenshot({ path: path.join(ART, '4-files-accumulated.png'), fullPage: false });
    });
});

for (const lang of ['th', 'en', 'ja']) {
    test(`四语(${lang}):去收料补按钮不裸 key`, async ({ page }) => {
        await bootWith(
            page,
            clientHandlers([{ kind: 'evidence_index', has_file: true, numbers: {} }]),
            `#/client/${CLIENT_ID}/pkg`,
            lang
        );
        const btn = page.locator('[data-action="pkg-go-intake"]');
        await expect(btn).toBeVisible();
        const text = await btn.innerText();
        expect(text).not.toContain('pkg_go_intake_btn');
        expect(text.trim().length).toBeGreaterThan(0);
        if (lang === 'th') {
            await page.screenshot({
                path: path.join(ART, '6-lang-th-pkg-blocked.png'),
                fullPage: false,
            });
        }
    });
}

test.describe('手机 390 无横溢(缺料卡按钮 + 收料区累积)', () => {
    test('缺料卡「去收料补」按钮 390px 不横溢', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await bootWith(
            page,
            clientHandlers([{ kind: 'evidence_index', has_file: true, numbers: {} }]),
            `#/client/${CLIENT_ID}/pkg`
        );
        await expect(page.locator('[data-action="pkg-go-intake"]')).toBeVisible();
        const scrollW = await page.evaluate(() => document.documentElement.scrollWidth);
        const clientW = await page.evaluate(() => document.documentElement.clientWidth);
        expect(scrollW).toBeLessThanOrEqual(clientW + 1);
        await page.screenshot({
            path: path.join(ART, '5-mobile-390-pkg-blocked.png'),
            fullPage: false,
        });
    });

    test('收料区累积文件列表 390px 不横溢', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await bootWith(page, clientHandlers(null), `#/client/${CLIENT_ID}/intake`);
        await page.waitForSelector('#ikDrop', { timeout: 15000 });
        await page.locator('#ikFileInput').setInputFiles([
            { name: 'a.jpg', mimeType: 'image/jpeg', buffer: Buffer.from('aaa') },
            { name: 'b.jpg', mimeType: 'image/jpeg', buffer: Buffer.from('bbb') },
        ]);
        await expect(page.locator('.dz-count b')).toHaveText('2');
        const scrollW = await page.evaluate(() => document.documentElement.scrollWidth);
        const clientW = await page.evaluate(() => document.documentElement.clientWidth);
        expect(scrollW).toBeLessThanOrEqual(clientW + 1);
        await page.screenshot({ path: path.join(ART, '5-mobile-390-intake.png'), fullPage: false });
    });
});
