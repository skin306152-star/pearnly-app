// SA-1 · 机器自动改动清单 · 本地 stub 真浏览器验收
// ============================================================
// 起法同 _m13key_verify.spec.js:_local_static_server 起静态服(真 ai.js/ai.css/ai.html)+
// page.route stub /api/**。真 DOM / 真 CSS / 真渲染,只桩网络层。
//
// stub 数据取自 SM 2569-05(工单 bd093ba9)生产库实测形状:IMG_2497 被判 non_tax 后由
// statement_sequence 自动改判回 bank_statement;两件银行流水共 2 行方向 + 1 行金额被余额链
// 改写。这些改动此前在任何界面上都不出现,本 spec 验它们现在摆在签字页上。
//
// 覆盖:① 面板可见且金边竖条生效(getComputedStyle)② 改判行文件名/kind/依据齐全
//      ③ 银行行改金额与改方向分别计数 ④ 无改动时面板整个不出现(四态诚实)⑤ 四语不裸 key
// 截图存 tests/e2e/_artifacts/sa1/。
/* global window, document */
const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8993;
const BASE = `http://127.0.0.1:${PORT}`;
const PAGE = `${BASE}/static/dist/ai.html`;
const ART = path.join(__dirname, '_artifacts', 'sa1');
const CLIENT_ID = '2';
const ORDER_ID = 'wo-sa1';

const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
const TOKEN = `${b64({ alg: 'HS256' })}.${b64({ sub: 'reviewer' })}.sig`;

let server;
test.beforeAll(async () => {
    server = await localServer.start(PORT);
});
test.afterAll(() => localServer.stop(server));

const MACHINE_ACTIONS = [
    {
        type: 'item_regrouped',
        item_id: 'e8c613e4',
        name: 'IMG_2497.jpg',
        from_kind: 'non_tax',
        to_kind: 'bank_statement',
        reason: 'statement_sequence',
        actor: 'system',
        at: '2026-07-19T08:10:31+00:00',
    },
    {
        type: 'bank_row_autocorrected',
        item_id: '5ad5d0dd',
        name: 'IMG_2485.jpg',
        row_count: 44,
        amount_rows: 0,
        direction_rows: 2,
        samples: [],
        truncated: false,
    },
    {
        type: 'bank_row_autocorrected',
        item_id: '9711e6b2',
        name: 'IMG_2488.jpg',
        row_count: 45,
        amount_rows: 1,
        direction_rows: 0,
        samples: [],
        truncated: false,
    },
];

const DELIVERABLES = [
    {
        kind: 'pp30_draft',
        has_file: true,
        numbers: { output_vat: '60073.60', input_vat: '29263.28', tax_due: '30810.32' },
    },
    { kind: 'evidence_index', has_file: true, numbers: {} },
];

function orderDetail(actions) {
    return {
        id: ORDER_ID,
        status: 'review',
        current_step: 'package',
        needs: [],
        blocked_reasons: [],
        numbers: {
            output_vat: '60073.60',
            input_vat: '29263.28',
            tax_due: '30810.32',
            period: '2569-05',
        },
        machine_actions: actions,
        deliverables: DELIVERABLES.map((d) => ({ kind: d.kind, numbers: d.numbers })),
    };
}

async function boot(page, actions, lang) {
    await page.route('**/api/**', (route) => {
        const u = new URL(route.request().url());
        const p = u.pathname;
        const json = (body) =>
            route.fulfill({
                status: 200,
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
        if (p === `/api/workorder/orders/${ORDER_ID}`) return json(orderDetail(actions));
        if (p === `/api/workorder/orders/${ORDER_ID}/deliverables`)
            return json({ deliverables: DELIVERABLES });
        return json({});
    });
    await page.addInitScript(
        ([t, l]) => {
            window.localStorage.setItem('mrpilot_token_ai', t);
            window.localStorage.setItem('mrpilot_lang', l || 'zh');
        },
        [TOKEN, lang]
    );
    await page.goto(PAGE + `#/client/${CLIENT_ID}/pkg`);
    await page.waitForSelector('.pkg-actions', { timeout: 15000 });
}

test.describe('SA-1 · 机器自动改动清单', () => {
    test('三条改动全部可见 · 金边竖条生效 · 计数分列', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await boot(page, MACHINE_ACTIONS);

        const panel = page.locator('.panel.mact');
        await expect(panel).toBeVisible();
        const rows = page.locator('.mact-row');
        await expect(rows).toHaveCount(3);

        // 金边竖条是这块面板与普通信息面板的唯一视觉区分,必须真生效而不只是类名在。
        const border = await rows.first().evaluate((el) => {
            const cs = window.getComputedStyle(el);
            return { w: cs.borderLeftWidth, style: cs.borderLeftStyle, color: cs.borderLeftColor };
        });
        expect(border.style).toBe('solid');
        expect(parseFloat(border.w)).toBeGreaterThan(0);
        expect(border.color).not.toBe('rgba(0, 0, 0, 0)');

        // kind 必须是人话:会计不认识 non_tax/bank_statement 这些后端内部词。
        const regroup = await rows.nth(0).innerText();
        expect(regroup).toContain('IMG_2497.jpg');
        expect(regroup).toContain('非税务单据');
        expect(regroup).toContain('银行流水');
        expect(regroup).not.toContain('non_tax');
        expect(regroup).not.toContain('bank_statement');
        expect(regroup).toContain('连号');

        // 只改方向的件不能显示「改写金额 0 行」,只改金额的件同理。
        const dirOnly = await rows.nth(1).innerText();
        expect(dirOnly).toContain('IMG_2485.jpg');
        expect(dirOnly).toContain('2');
        expect(dirOnly).not.toContain('改写金额');
        const amtOnly = await rows.nth(2).innerText();
        expect(amtOnly).toContain('改写金额 1 行');
        expect(amtOnly).not.toContain('改写收/付方向');

        await page.screenshot({ path: path.join(ART, 'zh-three-actions.png'), fullPage: true });
    });

    test('无改动时面板整个不出现', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await boot(page, []);
        await expect(page.locator('.panel.mact')).toHaveCount(0);
        await page.screenshot({ path: path.join(ART, 'zh-empty.png'), fullPage: true });
    });

    test('四语标题与说明不裸 key', async ({ page }) => {
        for (const lang of ['zh', 'th', 'en', 'ja']) {
            await boot(page, MACHINE_ACTIONS, lang);
            const text = await page.locator('.panel.mact .hd').innerText();
            expect(text).not.toContain('mact_');
            expect(text.trim().length).toBeGreaterThan(6);
            await page.screenshot({ path: path.join(ART, `lang-${lang}.png`) });
        }
    });

    test('手机端不横向溢出', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await boot(page, MACHINE_ACTIONS);
        await expect(page.locator('.panel.mact')).toBeVisible();
        const overflow = await page.evaluate(
            () => document.documentElement.scrollWidth > window.innerWidth + 1
        );
        expect(overflow).toBe(false);
        await page.screenshot({ path: path.join(ART, 'mobile.png'), fullPage: true });
    });
});
