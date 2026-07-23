// A-5 · 票面钱字段读不出 → 工单停机点名到票到字段 · 本地 stub 真浏览器验收
// ============================================================
// 真渲染代码(static/dist/ai.js/ai.css/ai.html 原样加载)+ 真 DOM,只桩网络层。
//
// A-5 是后端闸:reconcile_gates._face_value 判出票面钱字段「印了但读不出」→ 不计入 Σ 并
// StepResult.stuck 点名。修前 to_dec 把 "7O.00" 归 0,这张票贡献 ฿0 进项税而工单照样 ok
// 出数——少算且无人知道。本 spec 不引入新 UI,只验这条新停机原因确实摆到了会计眼前,
// 且把「机器看到的原文」也给了(会计据此判是 OCR 读花还是票本身印成这样)。
// 截图存 tests/e2e/_artifacts/a5/。
/* global window, document */
const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8995;
const BASE = `http://127.0.0.1:${PORT}`;
const PAGE = BASE + '/static/dist/ai.html';
const ART = path.join(__dirname, '_artifacts', 'a5');

// 后端 reconcile_gates._face_value 产出的原文(逐字节对齐,不臆造)。
const UNREADABLE_REASON =
    'IMG_2647.jpg(IV26-00675): 票面税额「7O.00」读不出,未计入进项税 — 请核对原票后改数或排除';

let server;
test.beforeAll(async () => {
    server = await localServer.start(PORT);
});
test.afterAll(() => localServer.stop(server));

function orderDetail() {
    return {
        id: 'wo-a5',
        status: 'stuck',
        current_step: 'reconcile',
        period: '2569-05',
        needs: [],
        blocked_reasons: [UNREADABLE_REASON],
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
        if (p === '/api/me') return json({ id: 'u-a5', username: 'reviewer', role: 'owner' });
        if (p === '/api/workspace/clients/c1')
            return json({ client: { id: 'c1', name: 'Sister Makeup' } });
        if (
            p === '/api/workorder/orders' &&
            new URL(route.request().url()).searchParams.has('client_id')
        )
            return json({ orders: [{ id: 'wo-a5', period: '2569-05' }] });
        if (p === '/api/workorder/orders')
            return json({ orders: [], count: 0, limit: 1, offset: 0 });
        if (p === '/api/workorder/orders/wo-a5') return json(orderDetail());
        return json({});
    });
    await page.addInitScript(
        ([l]) => {
            window.localStorage.setItem('mrpilot_token_ai', 'tok-a5');
            window.localStorage.setItem('mrpilot_lang', l || 'zh');
        },
        [lang]
    );
    await page.goto(`${PAGE}#/client/c1/wo`);
    await page.waitForSelector('.rv-blocked', { timeout: 15000 });
}

test.describe('A-5 · 读不出的钱字段在工单页的停机呈现', () => {
    test('停机原因摆到会计眼前 · 点名到票、到字段、带机器读到的原文', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await boot(page, 'zh');

        const blocked = page.locator('.rv-blocked');
        await expect(blocked).toBeVisible();
        await page.screenshot({ path: path.join(ART, 'zh-stuck.png'), fullPage: true });

        const text = await blocked.innerText();
        expect(text).toContain('IMG_2647.jpg'); // 点名到具体哪张票
        expect(text).toContain('税额'); // 说清是哪个字段(不甩英文键名)
        expect(text).toContain('7O.00'); // 机器读到的原文,会计一眼看出是 O 不是 0
        expect(text).toContain('未计入进项税'); // 说清后果:这笔没进合计
        expect(text).toContain('改数或排除'); // 给出可执行的下一步

        // 停机块必须真显示(不是被 CSS 藏起来的空壳)。
        const shown = await blocked.evaluate((el) => {
            const s = window.getComputedStyle(el);
            return {
                display: s.display,
                visibility: s.visibility,
                opacity: s.opacity,
                height: el.getBoundingClientRect().height,
            };
        });
        expect(shown.display).not.toBe('none');
        expect(shown.visibility).toBe('visible');
        expect(Number(shown.opacity)).toBeGreaterThan(0);
        expect(shown.height).toBeGreaterThan(0);

        // 重试出口在场:会计改完数可就地重跑,不用回头找入口。
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
