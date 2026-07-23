// C-3 · 组头「全部按建议处理」不许覆盖会计已逐张改判的票 · 真浏览器验收
// ============================================================
// 真渲染代码 + 真 DOM,只桩网络层。断言落在**发出去的请求载荷**上,不是界面上看着对 ——
// 覆盖是发生在网络层的事,只看渲染看不出来。
//
// 背景:收件箱 runGroupBatch 只滤 isArchived,不滤 isDecided(ai-review-bulk.js 那条路早
// 就滤了,两处各写一份)。会计先逐张改数(E),再点组头的「全部按建议处理」,批量会把刚改
// 对的值按组模板重新发一遍盖回去 —— 改数是钱面动作,盖回去等于白改还没人知道。
// 截图存 tests/e2e/_artifacts/c3/。
/* global window */
const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');
const stub = require('./_review_queue_stub');

const PORT = 8990;
const BASE = `http://127.0.0.1:${PORT}`;
const PAGE = BASE + '/static/dist/ai.html';
const ART = path.join(__dirname, '_artifacts', 'c3');
const ORDER = 'wo-c3';

function mkItem(id, file, decision) {
    return {
        item_id: id,
        kind: 'purchase_invoice',
        status: 'flagged',
        flag_reason: 'duplicate_of:IMG_0001.jpg',
        original_name: file,
        ocr_read: {
            subtotal: '58128.57',
            vat: '4069.00',
            total_amount: '62197.57',
            invoice_number: 'IV' + id,
            seller_tax: '0735527000289',
        },
        // decision 非空 = 会计已经逐张裁过这张(后端投影)。
        decision: decision,
        // 会给批量按钮的组:高置信 + 有建议(groupCanBulk 的放行条件)。低置信组本来就
        // 不给批量,那种场景验不到本条闸。
        verdict_hint: {
            narrative_key: 'verdict_duplicate',
            params: { of: 'IMG_0001.jpg' },
            confidence: 'high',
            severity: 'crit',
            suggested_decision: 'exclude',
        },
        work_order_id: ORDER,
        client_name: 'Sister Makeup',
        period: '2569-05',
    };
}

// 同一组两张:it-done 会计已按重算改过数,it-todo 还没裁。
const DONE = mkItem('it-done', 'IMG_2647.jpg', {
    decision: 'face_value',
});
const TODO = mkItem('it-todo', 'IMG_2648.jpg', null);

function queueFixture() {
    const base = stub.queueFixture(DONE, ORDER);
    base.flagged_items = [DONE, TODO];
    const order = base.clients[0].orders[0];
    order.flagged_groups = [
        {
            flag_reason: 'duplicate_of:IMG_0001.jpg',
            severity: 'crit',
            count: 2,
            undecided_count: 1,
        },
    ];
    order.flagged_total = 2;
    base.counts.flagged = 2;
    return base;
}

let server;
let batchPayloads;

test.beforeAll(async () => {
    server = await localServer.start(PORT);
});
test.afterAll(() => localServer.stop(server));

async function boot(page) {
    batchPayloads = [];
    await page.route('**/api/**', (route) => {
        const req = route.request();
        const p = new URL(req.url()).pathname;
        if (p.endsWith('/decisions:batch')) {
            batchPayloads.push(JSON.parse(req.postData() || '{}'));
            return route.fulfill({ json: { ok: true, applied: 1 } });
        }
        if (p === '/api/ai/session') return route.fulfill({ json: { ok: true } });
        if (p === '/api/me')
            return route.fulfill({ json: { id: 'u-c3', username: 'reviewer', role: 'owner' } });
        if (p === '/api/workorder/orders')
            return route.fulfill({ json: { orders: [], count: 0, limit: 1, offset: 0 } });
        if (p === '/api/workorder/review-queue') return route.fulfill({ json: queueFixture() });
        if (p === '/api/ai/client-pool') return route.fulfill({ json: { groups: [] } });
        return route.fulfill({ status: 404, json: { detail: 'not_stubbed:' + p } });
    });
    await page.addInitScript(
        ({ token }) => {
            window.localStorage.setItem('mrpilot_token_ai', token);
            window.localStorage.setItem('mrpilot_lang', 'zh');
        },
        { token: stub.fakeToken('u-c3') }
    );
    await page.goto(PAGE);
    await page.waitForFunction(() => !!window.AI && !!window.AI.router);
    await page.evaluate(() => {
        window.location.hash = '#/pool';
    });
    await page.waitForSelector('#v-pool.on', { timeout: 15000 });
    await page.waitForSelector('.riq-item', { timeout: 10000 });
}

test.describe('C-3 · 批量处理不覆盖已裁决的票', () => {
    test('组头批量只发未裁决的那张 · 已改数的票不在载荷里', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await boot(page);
        await page.screenshot({ path: path.join(ART, 'before.png'), fullPage: true });

        // .riq-group-bulk 本身就是按钮(btn pri riq-group-bulk),不是容器。
        const bulk = page.locator('.riq-group-bulk').first();
        await expect(bulk).toBeVisible();
        await bulk.click();
        await page.waitForFunction(() => true);
        await expect.poll(() => batchPayloads.length, { timeout: 10000 }).toBeGreaterThan(0);

        const sent = batchPayloads.flatMap((p) => p.decisions || []).map((d) => d.item_id);
        // 核心断言:已裁决的那张绝不能出现在批量载荷里。
        expect(sent).not.toContain('it-done');
        expect(sent).toContain('it-todo');

        await page.screenshot({ path: path.join(ART, 'after.png'), fullPage: true });
    });

    test('组头计数只算未裁决的那张(已判的不该催人再判一次)', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await boot(page);
        const chip = await page.locator('.riq-wo-flags .chip').first().innerText();
        expect(chip).toContain('1');
        expect(chip).not.toContain('2 ');
    });
});
