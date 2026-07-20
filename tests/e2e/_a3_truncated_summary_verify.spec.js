// A-3 · 汇总表被截断 → 工单卡在「系统卡点」并说清原因 · 本地 stub 真浏览器验收
// ============================================================
// 真渲染代码(static/dist/ai.js/ai.css/ai.html 原样加载)+ 真 DOM,只桩网络层。
//
// A-3 是后端闸:reconcile 读到 summary parse 的 truncated=True → StepResult.stuck 点名
// (与合计行打架同级)。停机原因经既有 system_blocked_detail 模板渲染在工单页——本 spec
// 不引入新 UI 组件,只验这条新停机原因确实摆到了会计眼前(而不是像修前那样静默少算)。
// 截图存 tests/e2e/_artifacts/a3/。
/* global window, document */
const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8996;
const BASE = `http://127.0.0.1:${PORT}`;
const PAGE = BASE + '/static/dist/ai.html';
const ART = path.join(__dirname, '_artifacts', 'a3');

// 后端 reconcile_gates.total_check_reasons 对截断件产出的原文(逐字节对齐,不臆造)。
const TRUNCATED_REASON =
    'sales_rows_truncated[销项汇总-2569-05.xlsx]: 汇总表行数超解析上限被截断,' +
    '少算的行未计入销售额/销项税,且表尾合计行可能一并被截 — 请拆分该表后重传';

let server;
test.beforeAll(async () => {
    server = await localServer.start(PORT);
});
test.afterAll(() => localServer.stop(server));

function orderDetail() {
    return {
        id: 'wo-a3',
        status: 'stuck',
        current_step: 'reconcile',
        period: '2569-05',
        needs: [],
        blocked_reasons: [TRUNCATED_REASON],
        numbers: {},
        flagged: [],
    };
}

async function boot(page, lang) {
    await page.route('**/api/**', (route) => {
        const p = new URL(route.request().url()).pathname;
        const json = (b) =>
            route.fulfill({ contentType: 'application/json', body: JSON.stringify(b) });
        if (p === '/api/ai/session') return json({ ok: true });
        if (p === '/api/me') return json({ id: 'u-a3', username: 'reviewer', role: 'owner' });
        if (p === '/api/workspace/clients/c1')
            return json({ client: { id: 'c1', name: 'Sister Makeup' } });
        if (
            p === '/api/workorder/orders' &&
            new URL(route.request().url()).searchParams.has('client_id')
        )
            return json({ orders: [{ id: 'wo-a3', period: '2569-05' }] });
        if (p === '/api/workorder/orders')
            return json({ orders: [], count: 0, limit: 1, offset: 0 });
        if (p === '/api/workorder/orders/wo-a3') return json(orderDetail());
        return json({});
    });
    await page.addInitScript(
        ([l]) => {
            window.localStorage.setItem('mrpilot_token_ai', 'tok-a3');
            window.localStorage.setItem('mrpilot_lang', l || 'zh');
        },
        [lang]
    );
    await page.goto(`${PAGE}#/client/c1/wo`);
    await page.waitForSelector('.rv-blocked', { timeout: 15000 });
}

test.describe('A-3 · 截断汇总表在工单页的停机呈现', () => {
    test('停机原因摆到会计眼前 · 说清截断少算与拆表重传', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await boot(page, 'zh');

        const blocked = page.locator('.rv-blocked');
        await expect(blocked).toBeVisible();
        await page.screenshot({ path: path.join(ART, 'zh-stuck.png'), fullPage: true });

        const text = await blocked.innerText();
        expect(text).toContain('截断'); // 「被截断」这件事必须说出来
        expect(text).toContain('销项汇总-2569-05.xlsx'); // 点名到具体哪张表
        expect(text).toContain('拆分'); // 给出可执行的下一步
        // 机器前缀 sales_rows_truncated[...] 原样显示,与既有 sales_total_mismatch[...]/
        // trial_balance_unbalanced 等停机原因同一呈现口径(全站停机原因都带前缀,A-3 不另搞一套)。

        // 重试出口在场(既有 wo-retry-stuck 按钮),截断修表后可重跑。
        await expect(page.locator('[data-action="wo-retry-stuck"]')).toBeVisible();
    });

    test('手机端不横向溢出', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await boot(page, 'zh');
        await expect(page.locator('.rv-blocked')).toBeVisible();
        const overflow = await page.evaluate(
            () => document.documentElement.scrollWidth > window.innerWidth + 1
        );
        expect(overflow).toBe(false);
        await page.screenshot({ path: path.join(ART, 'mobile.png'), fullPage: true });
    });
});
