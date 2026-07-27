// 看板三样能力(2026-07-27 从事务所矩阵搬来:批量开单 / 三个筛选 / 缺哪张单)
// 本地真浏览器验收 —— 跑 static/dist 真构建产物,不跑源文件。
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**(同
// _empty_states_local.spec.js 先例)。断言的每个选择器/文案都来自真实产物
// (ai-board-tools-render.js / ai-board-bulk.js / ai-dashboard.js / ai-i18n-board.js),
// 不是脚本自己造出来的对象;可见性一律用 toBeVisible/isVisible 判,不看 class 名。
// 截图存 tests/e2e/_artifacts/board_tools/。
//
// 起法:npx playwright test tests/e2e/_board_tools_local.spec.js
/* global window, getComputedStyle */

const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8993;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'board_tools');

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT);
});

test.afterAll(() => localServer.stop(server));

const PERIOD = '2569-07';

// 四个客户覆盖四种真实处境:本期一张单没开(缺两项义务)/ 缺料 / 等你审 / 逾期。
const CLIENTS = [
    { id: 1, name: 'บริษัท เอ' },
    { id: 2, name: 'บริษัท บี' },
    { id: 3, name: 'บริษัท ซี' },
    { id: 4, name: 'บริษัท ดี' },
];

const ORDERS = [
    { id: 'wo-2', workspace_client_id: 2, period: PERIOD, status: 'collecting' },
    { id: 'wo-3', workspace_client_id: 3, period: PERIOD, status: 'review' },
    { id: 'wo-4', workspace_client_id: 4, period: PERIOD, status: 'collecting' },
];

const OBLIGATION_LABELS = {
    pp30: { zh: '增值税', th: 'ภ.พ.30' },
    pnd1: { zh: '预扣税', th: 'ภ.ง.ด.1' },
};

// due_efiling_deferred 早于"今天"= 逾期(客户 4);其余给一个远期日子。
const FAR = '2599-12-31';
const PAST = '2000-01-31';

const MATRIX = {
    period: PERIOD,
    clients: [
        { id: 1, name: 'บริษัท เอ', missing_order: true },
        { id: 2, name: 'บริษัท บี', missing_order: false },
        { id: 3, name: 'บริษัท ซี', missing_order: false },
        { id: 4, name: 'บริษัท ดี', missing_order: false },
    ],
    obligation_codes: ['pnd1', 'pp30'],
    obligation_labels: OBLIGATION_LABELS,
    cells: [
        { client_id: 1, obligation_code: 'pp30', badge: 'pending_order', due_efiling: FAR },
        { client_id: 1, obligation_code: 'pnd1', badge: 'pending_order', due_efiling: FAR },
        { client_id: 2, obligation_code: 'pp30', badge: 'missing_materials', due_efiling: FAR },
        { client_id: 3, obligation_code: 'pp30', badge: 'pending_review', due_efiling: FAR },
        {
            client_id: 4,
            obligation_code: 'pp30',
            badge: 'missing_materials',
            due_efiling: PAST,
            due_efiling_deferred: PAST,
        },
    ],
};

function json(body) {
    return { contentType: 'application/json', body: JSON.stringify(body) };
}

// created:收集批量开单真发出的 POST body,用来证明"开的是哪一期、给了哪几个客户"。
async function boot(page, { lang = 'zh', created = [], matrixFails = false } = {}) {
    // 一个 handler 分发全部 /api/**:Playwright 的路由是"后注册先匹配",分成多条再加一条
    // 兜底 catch-all 会把前面几条全盖掉(首版就这么写,整块看板一片空白)。
    await page.route('**/api/**', (r) => {
        const url = r.request().url();
        if (url.includes('/api/workorder/orders')) {
            if (r.request().method() === 'POST') {
                created.push(JSON.parse(r.request().postData() || '{}'));
                return r.fulfill(json({ id: 'wo-new' }));
            }
            const m = url.match(/\/api\/workorder\/orders\/([^/?]+)/);
            if (m) {
                const order = ORDERS.filter((o) => o.id === m[1])[0] || {};
                return r.fulfill(
                    json(
                        Object.assign(
                            { needs: [], blocked_reasons: [], flagged: [], numbers: {} },
                            order
                        )
                    )
                );
            }
            return r.fulfill(json({ orders: ORDERS }));
        }
        if (url.includes('/api/tax-profile/matrix')) {
            return matrixFails
                ? r.fulfill({ status: 500, contentType: 'application/json', body: '{}' })
                : r.fulfill(json(MATRIX));
        }
        if (url.includes('/api/workspace/clients')) return r.fulfill(json({ clients: CLIENTS }));
        if (url.includes('/api/me')) return r.fulfill(json({ username: 'skin' }));
        return r.fulfill(json({}));
    });
    await page.addInitScript(
        ([l]) => {
            window.localStorage.setItem('mrpilot_token_ai', 'tok-board');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [lang]
    );
    await page.goto(`${BASE}/static/dist/ai.html#/board`);
    await page.waitForSelector('#dashBody .kanban', { state: 'visible', timeout: 15000 });
}

function card(page, clientId) {
    return page.locator(`#dashBody .kcard[data-client-id="${clientId}"]`);
}

test.describe('缺哪张单看得见', () => {
    test('本期没开单的卡点名缺哪几项义务(不是一句「还没有工单」)', async ({ page }) => {
        await boot(page);
        const strip = card(page, 1).locator('.kmiss');
        await expect(strip).toBeVisible();
        const text = await strip.locator('.kmiss-t').innerText();
        expect(text).toContain(PERIOD);
        expect(text).toContain('增值税');
        expect(text).toContain('预扣税');
        // 干话不再出现,i18n key 也不许露脸
        await expect(card(page, 1)).not.toContainText('还没有工单');
        expect(text).not.toContain('kb_missing');
        // 已有本期工单的卡不给勾选框(批量开单对它们没有意义)
        await expect(card(page, 2).locator('.kmiss')).toHaveCount(0);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '01-missing-orders-zh.png'),
            fullPage: true,
        });
    });

    test('泰语真出泰文义务名(zh+th 两语都落地)', async ({ page }) => {
        await boot(page, { lang: 'th' });
        const text = await card(page, 1).locator('.kmiss-t').innerText();
        expect(text).toContain('ภ.พ.30');
        expect(text).toContain('ภ.ง.ด.1');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '02-missing-orders-th.png'),
            fullPage: true,
        });
    });
});

test.describe('三个筛选', () => {
    async function chip(page, name) {
        return page.locator(`#boardFilters .kb-chip[data-filter="${name}"]`);
    }

    test('缺料/待审/风险各自只留命中的卡 · 列头计数跟着改', async ({ page }) => {
        await boot(page);
        await expect(page.locator('#boardTools')).toBeVisible();

        await (await chip(page, 'missing')).click();
        expect(await card(page, 2).isVisible()).toBe(true); // missing_materials
        expect(await card(page, 4).isVisible()).toBe(true); // missing_materials
        expect(await card(page, 3).isVisible()).toBe(false); // pending_review
        expect(await card(page, 1).isVisible()).toBe(false); // pending_order
        // 列头计数必须跟着筛选走(不改就是数字撒谎)
        const materialsCount = await page
            .locator('#dashBody .kcol')
            .first()
            .locator('h4 [data-role="col-count"]')
            .innerText();
        expect(materialsCount).toBe('2');
        // 色点不许被当成计数写脏(等资料列的 .dot 也叫 .n)
        expect(await page.locator('#dashBody .kcol').first().locator('h4 .dot').innerText()).toBe(
            ''
        );
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '03-filter-missing.png'),
            fullPage: true,
        });

        await (await chip(page, 'missing')).click(); // 取消
        await (await chip(page, 'review')).click();
        expect(await card(page, 3).isVisible()).toBe(true);
        expect(await card(page, 2).isVisible()).toBe(false);

        await (await chip(page, 'review')).click();
        await (await chip(page, 'risk')).click();
        expect(await card(page, 4).isVisible()).toBe(true); // 截止日已过
        expect(await card(page, 2).isVisible()).toBe(false); // 同样缺料但没到期
        // 激活态得看得出来:.on 的底色必须与未激活 chip 真的不同(只加 class 不换样式,
        // 用户根本不知道现在正被筛着,同 memory:css-property-set-is-not-effect-working)。
        // chip 有 120ms 的 background 过渡,点完立刻取色取到的是中途值(首版就这么写,
        // 断言随机红)——poll 到过渡落定再比。
        const bg = (name) =>
            page
                .locator(`#boardFilters .kb-chip[data-filter="${name}"]`)
                .evaluate((el) => getComputedStyle(el).backgroundColor);
        await expect.poll(async () => (await bg('risk')) !== (await bg('missing'))).toBe(true);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '04-filter-risk.png'),
            fullPage: true,
        });
    });

    test('筛到空有空态 + 清除筛选真把 chip 高亮/搜索框一起清干净', async ({ page }) => {
        await boot(page);
        await (await chip(page, 'review')).click();
        await page.fill('#searchInput', 'zzz-no-such-client');
        const empty = page.locator('#dashBody .kb-noresults');
        await expect(empty).toBeVisible();
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '05-filter-empty-state.png'),
            fullPage: true,
        });

        await empty.locator('[data-action="clear-filters"]').click();
        await expect(page.locator('#dashBody .kb-noresults')).toHaveCount(0);
        expect(await page.inputValue('#searchInput')).toBe('');
        expect(await (await chip(page, 'review')).getAttribute('class')).not.toContain('on');
        for (const c of CLIENTS) {
            expect(await card(page, c.id).isVisible()).toBe(true);
        }
    });
});

test.describe('批量开单', () => {
    test('勾选浮出操作条 · 显示已选数量与账期 · 一键开单真打端点', async ({ page }) => {
        const created = [];
        await boot(page, { created });
        const bar = page.locator('#boardBulkBar');
        expect(await bar.isVisible()).toBe(false);

        await card(page, 1).locator('.kmiss input').check();
        await expect(bar).toBeVisible();
        const barText = await bar.innerText();
        expect(barText).toContain('1');
        expect(barText).toContain(PERIOD); // 按钮写明开的是哪一期
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '06-bulk-bar.png'),
            fullPage: true,
        });

        await bar.locator('[data-action="bulk-open"]').click();
        await expect(bar).toContainText('1');
        expect(created).toEqual([
            { workspace_client_id: 1, period: PERIOD, intent: 'monthly_vat' },
        ]);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '07-bulk-result.png'),
            fullPage: true,
        });
    });

    test('勾选不把人导航进客户页(卡片整体可点,勾选框得让路)', async ({ page }) => {
        await boot(page);
        await card(page, 1).locator('.kmiss').click();
        expect(page.url()).toContain('#/board');
        expect(await card(page, 1).locator('.kmiss input').isChecked()).toBe(true);
    });

    test('取消选择收起操作条', async ({ page }) => {
        await boot(page);
        await card(page, 1).locator('.kmiss input').check();
        await page.locator('#boardBulkBar [data-action="bulk-clear"]').click();
        expect(await page.locator('#boardBulkBar').isVisible()).toBe(false);
    });
});

test.describe('矩阵端点挂了也不许把看板带塌', () => {
    test('工具条收起 · 卡片照常渲染 · 不出半真半假的筛选', async ({ page }) => {
        await boot(page, { matrixFails: true });
        expect(await page.locator('#boardTools').isVisible()).toBe(false);
        expect(await page.locator('#boardBulkBar').isVisible()).toBe(false);
        expect(await card(page, 2).isVisible()).toBe(true);
        await expect(card(page, 1).locator('.kmiss')).toHaveCount(0);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '08-matrix-down-degraded.png'),
            fullPage: true,
        });
    });
});
