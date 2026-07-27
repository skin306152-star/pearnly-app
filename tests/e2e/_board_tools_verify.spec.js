// 看板三样能力 + 矩阵空态 · 真栈视觉验收(2026-07-27)
// ============================================================
// 真后端 127.0.0.1:7860 + 真库 docker pearnly-db + 真登录(stw_e2e / entry=ai),
// 页面走 /ai 真构建产物。断言的每个选择器/文案都来自真实产物:
//   ai-board-tools-render.js / ai-board-bulk.js / ai-dashboard.js / ai-matrix-render.js /
//   ai-i18n-board.js / ai-i18n-empty.js / static/ai/ai.html
//
// 两种取数,分得很清楚:
//   [真数据] 矩阵空态 / 矩阵 tab / 三筛选 / 缺单条(无义务名回落)—— 零 stub,打真后端。
//   [改真响应] 多选批量开单 + 缺单条列义务名 + 风险筛选命中 —— 真租户当期只有 1 家缺单、
//             没有 pending_order 格子、没有逾期格子,单靠真数据验不出来。做法是 route.fetch()
//             取真响应再改字段(字段名全是后端真返的),不自造对象。
//   批量开单的 POST 走 stub 收报文,再把收到的报文原样重放到真后端断言 200 —— 既证明
//   前端发的报文真后端认,又不给共享 dev 库塞新工单。
//
// 起法:npx playwright test tests/e2e/_board_tools_verify.spec.js
/* global window, document, getComputedStyle */

const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const BASE = process.env.PEARNLY_E2E_BASE_URL || 'http://127.0.0.1:7860';
const USER = 'stw_e2e';
const PASS = 'StwVerify#2026';
const ART = path.join(__dirname, '_artifacts', 'board_tools');
fs.mkdirSync(ART, { recursive: true });

const DESKTOP = { width: 1280, height: 900 };
const MOBILE = { width: 390, height: 844 };
// 触屏命中区规则(.kb-chip min-height:40px)挂在 @media (pointer: coarse) 上,
// 不开 hasTouch 的窗口是 fine pointer,量到的是桌面值——移动端一律带 hasTouch。
const TOUCH = { viewport: MOBILE, hasTouch: true, isMobile: true };

// 真租户当期实况(curl 取过 · 矩阵 + 逐单 detail):客户 84/85/86/87/88,当期 2569-07。
// 卡面写什么由 ai-format.js::statusChip 按逐单 detail 定,不是矩阵徽章:
//   87 collecting 无 needs        → 「等资料」
//   84/86 stuck 有 detail.needs   → 「缺料」   (矩阵徽章却是粗粒度的 pending_review)
//   85 stuck 无 needs 无待审队列   → 「等你审」
//   88 本期无工单                  → 无状态胶囊
const C_MISSING_REAL = 88; // missing_order=true 且一格义务都没物化
const C_MAT_A = 87; // 卡面「等资料」
const C_MAT_B = 84; // 卡面「缺料」
const C_REVIEW_A = 85; // 卡面「等你审」
const C_REVIEW_B = 86; // 卡面「缺料」

let TOKEN = '';

test.beforeAll(async ({ request }) => {
    const r = await request.post(`${BASE}/api/login`, {
        data: { username: USER, password: PASS, entry: 'ai' },
    });
    expect(r.status()).toBe(200);
    TOKEN = (await r.json()).token;
    expect(TOKEN.length).toBeGreaterThan(20);
});

// 真矩阵响应 → 改出「多家缺单 + 有 pending_order 义务 + 有逾期格」的处境。
// 只动值不动结构:client 的 missing_order、cells 里的 badge/due_*,全是后端真有的字段。
function patchMatrix(m) {
    const out = JSON.parse(JSON.stringify(m));
    const sample = {};
    (out.cells || []).forEach((c) => {
        if (!sample[c.obligation_code]) sample[c.obligation_code] = c;
    });
    const pendingOrder = (clientId, code) =>
        Object.assign({}, sample[code], {
            client_id: clientId,
            obligation_code: code,
            order_status: null,
            work_order_id: null,
            badge: 'pending_order',
        });
    out.clients.forEach((c) => {
        if (c.id === C_REVIEW_A) c.missing_order = true;
    });
    // 85 原有的 pp30 pending_review 与「本期一张单没开」自相矛盾,先摘掉再补 pending_order。
    out.cells = out.cells.filter(
        (c) => !(c.client_id === C_REVIEW_A && c.obligation_code === 'pp30')
    );
    // 义务名排序按截止日:pnd1(顺延 08-17)在前,pp30(顺延 08-24)在后。
    out.cells.push(
        pendingOrder(C_MISSING_REAL, 'pnd1'),
        pendingOrder(C_MISSING_REAL, 'pp30'),
        pendingOrder(C_REVIEW_A, 'pnd1'),
        pendingOrder(C_REVIEW_A, 'pp30')
    );
    // 真数据当期没有任何逾期格(截止日都在 8 月),把 86 的 pp30 拨到过去造一格。
    out.cells.forEach((c) => {
        if (c.client_id === C_REVIEW_B && c.obligation_code === 'pp30') {
            c.due_efiling = '2026-07-01';
            c.due_efiling_deferred = '2026-07-01';
        }
    });
    return out;
}

// opts: { lang, hash, patch(bool), posted(array) }
async function open(page, opts) {
    const o = opts || {};
    const errs = [];
    page.on('console', (m) => {
        if (m.type() === 'error') errs.push(m.text());
    });
    page.on('pageerror', (e) => errs.push('pageerror: ' + e.message));

    if (o.patch) {
        await page.route(
            (u) => u.pathname === '/api/tax-profile/matrix',
            async (route) => {
                const res = await route.fetch();
                const real = await res.json();
                await route.fulfill({
                    contentType: 'application/json',
                    body: JSON.stringify(patchMatrix(real)),
                });
            }
        );
    }
    if (o.posted) {
        await page.route(
            (u) => u.pathname === '/api/workorder/orders',
            async (route) => {
                if (route.request().method() !== 'POST') return route.continue();
                const body = JSON.parse(route.request().postData() || '{}');
                o.posted.push(body);
                await route.fulfill({
                    contentType: 'application/json',
                    body: JSON.stringify({
                        id: '00000000-0000-4000-8000-00000000dead',
                        workspace_client_id: body.workspace_client_id,
                        period: body.period,
                        intent: body.intent,
                        status: 'collecting',
                        current_step: null,
                    }),
                });
            }
        );
    }
    await page.addInitScript(
        ([t, l]) => {
            window.localStorage.setItem('mrpilot_token_ai', t);
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [TOKEN, o.lang || 'zh']
    );
    await page.goto(`${BASE}/ai${o.hash || ''}`, { waitUntil: 'domcontentloaded' });
    return errs;
}

function card(page, clientId) {
    return page.locator(`#dashBody .kcard[data-client-id="${clientId}"]`);
}

async function waitBoard(page) {
    await page.waitForSelector('#dashBody .kanban', { state: 'visible', timeout: 20000 });
    await page.waitForSelector('#boardTools', { state: 'visible', timeout: 20000 });
}

function chip(page, name) {
    return page.locator(`#boardFilters .kb-chip[data-filter="${name}"]`);
}

async function shot(page, name) {
    await page.screenshot({ path: path.join(ART, name), fullPage: true });
}

async function noHScroll(page) {
    return page.evaluate(() => {
        const d = document.documentElement;
        return { scrollW: d.scrollWidth, clientW: d.clientWidth };
    });
}

// ---------------------------------------------------------------- 场景 1 + 2:矩阵
test.describe('矩阵(真数据)', () => {
    test.use({ viewport: DESKTOP });

    test('1a 当期无义务 → 正经空态(不是只剩一列的残缺表)· 两条出路能点', async ({ page }) => {
        await open(page, { hash: '#/' });
        // 当期 2569-07 真有 8 列义务 → 先确认表格分支是活的
        await page.waitForSelector('#matrixBody .mx-table', { state: 'visible', timeout: 20000 });
        // 切到一个真后端返 obligation_codes:[](该期一格义务都没物化)的账期
        await page.click('#matrixPeriodBtn');
        await page.click('#matrixPeriodMenu button[data-p="2569-05"]');
        const empty = page.locator('#matrixBody .mx-noobl');
        await expect(empty).toBeVisible({ timeout: 20000 });
        await expect(page.locator('#matrixBody .mx-table')).toHaveCount(0);

        const text = await empty.innerText();
        expect(text).toContain('这一期还没有义务记录');
        expect(text).not.toMatch(/emp_mx_noobl/); // i18n key 不许露脸
        expect(text.length).toBeGreaterThan(30); // 光一个标题不算"说清为什么"

        const toClients = empty.locator('a[href="#/clients"]');
        const toBoard = empty.locator('a[href="#/board"]');
        await expect(toClients).toBeVisible();
        await expect(toBoard).toBeVisible();
        // 两个按钮必须真在容器里、有面积可点(不是 0 高度的死链)
        const rects = await empty.evaluate((el) =>
            Array.prototype.map.call(el.querySelectorAll('a'), (a) => {
                const r = a.getBoundingClientRect();
                return { w: r.width, h: r.height, href: a.getAttribute('href') };
            })
        );
        rects.forEach((r) => {
            expect(r.w).toBeGreaterThan(60);
            expect(r.h).toBeGreaterThan(20);
        });
        await shot(page, '01-matrix-empty-zh-desktop.png');

        // 出路真落到路由
        await toBoard.click();
        await page.waitForSelector('#boardSection', { state: 'visible', timeout: 15000 });
        expect(page.url()).toContain('#/board');
    });

    test('1b 泰语空态整句泰文', async ({ page }) => {
        await open(page, { hash: '#/', lang: 'th' });
        await page.waitForSelector('#matrixBody .mx-table', { state: 'visible', timeout: 20000 });
        await page.click('#matrixPeriodBtn');
        await page.click('#matrixPeriodMenu button[data-p="2569-05"]');
        const empty = page.locator('#matrixBody .mx-noobl');
        await expect(empty).toBeVisible({ timeout: 20000 });
        const text = await empty.innerText();
        expect(text).toContain('งวดนี้ยังไม่มีรายการที่ต้องยื่น');
        expect(text).not.toContain('这一期');
        await shot(page, '02-matrix-empty-th-desktop.png');
    });

    test('2 矩阵 tab 还在 · 与看板能来回切', async ({ page }) => {
        await open(page, { hash: '#/board' });
        await waitBoard(page);
        await expect(page.locator('#vtMatrix')).toBeVisible();
        await expect(page.locator('#vtBoard')).toBeVisible();
        expect(await page.locator('#vtBoard').getAttribute('class')).toContain('on');

        await page.click('#vtMatrix');
        await page.waitForSelector('#matrixBody .mx-table', { state: 'visible', timeout: 20000 });
        expect(await page.locator('#matrixSection').isVisible()).toBe(true);
        expect(await page.locator('#boardSection').isVisible()).toBe(false);
        expect(await page.locator('#vtMatrix').getAttribute('class')).toContain('on');
        // 当期真数据下矩阵是完整表(客户列 + 8 个义务列),不是残缺表
        const cols = await page.locator('#matrixBody .mx-colhead').count();
        expect(cols).toBeGreaterThan(1);
        await shot(page, '03-matrix-tabs-zh-desktop.png');

        await page.click('#vtBoard');
        await waitBoard(page);
        expect(await page.locator('#boardSection').isVisible()).toBe(true);
    });
});

// ---------------------------------------------------------------- 场景 4 + 5:真数据
test.describe('看板筛选与缺单条(真数据)', () => {
    test.use({ viewport: DESKTOP });

    test('5a 本期没开单的卡有缺单条(真数据无义务物化 → 诚实回落一句)', async ({ page }) => {
        const errs = await open(page, { hash: '#/board' });
        await waitBoard(page);
        const strip = card(page, C_MISSING_REAL).locator('.kmiss');
        await expect(strip).toBeVisible();
        const text = await strip.locator('.kmiss-t').innerText();
        expect(text).toContain('2569-07');
        expect(text).not.toMatch(/kb_missing/); // i18n key 不许露脸
        // 已有本期工单的卡不给缺单条 / 勾选框
        await expect(card(page, C_MAT_A).locator('.kmiss')).toHaveCount(0);
        await expect(card(page, C_REVIEW_A).locator('.kmiss')).toHaveCount(0);
        await shot(page, '04-board-missing-real-zh-desktop.png');
        expect(errs.filter((e) => !/favicon|Failed to load resource/i.test(e))).toEqual([]);
    });

    test('4a 缺料 / 待审 各自只留命中的卡 · 列头计数跟着改', async ({ page }) => {
        await open(page, { hash: '#/board' });
        await waitBoard(page);
        const total = await page.locator('#dashBody .kcard').count();
        expect(total).toBe(5);

        await chip(page, 'missing').click();
        expect(await card(page, C_MAT_A).isVisible()).toBe(true);
        expect(await card(page, C_MAT_B).isVisible()).toBe(true);
        expect(await card(page, C_REVIEW_B).isVisible()).toBe(true);
        expect(await card(page, C_REVIEW_A).isVisible()).toBe(false);
        expect(await card(page, C_MISSING_REAL).isVisible()).toBe(false);
        // 点了「缺料」,留在屏幕上的每张卡脸上写的就得是缺料那一族的词——此前筛选吃
        // 后端粗粒度徽章,点「待审」筛出一张写着「缺料」的卡(截图 06)。
        const shownStates = await page.evaluate(() =>
            Array.prototype.filter
                .call(
                    document.querySelectorAll('#dashBody .kcard'),
                    (c) => c.style.display !== 'none'
                )
                .map((c) => (c.querySelector('.chip') || {}).textContent || '')
        );
        expect(shownStates.length).toBe(3);
        shownStates.forEach((s) => expect(['等资料', '缺料']).toContain(s));
        // 列头计数 = 各列可见卡数(数字不许撒谎)
        const counts = await page.evaluate(() =>
            Array.prototype.map.call(document.querySelectorAll('#dashBody .kcol'), (col) => ({
                shown: Array.prototype.filter.call(
                    col.querySelectorAll('.kcard'),
                    (c) => c.style.display !== 'none'
                ).length,
                badge: (col.querySelector('h4 [data-role="col-count"]') || {}).textContent,
            }))
        );
        counts.forEach((c) => expect(c.badge).toBe(String(c.shown)));
        expect(counts.reduce((a, b) => a + b.shown, 0)).toBe(3);
        // 被筛空的列与天生为空的列长得一样(都有一句话),且说的是"被筛空了"不是"没客户"
        const emptyTexts = await page.evaluate(() =>
            Array.prototype.map.call(document.querySelectorAll('#dashBody .kcol'), (col) => {
                const e = col.querySelector('[data-role="col-empty"]');
                const shown = Array.prototype.filter.call(
                    col.querySelectorAll('.kcard'),
                    (c) => c.style.display !== 'none'
                ).length;
                return {
                    shown,
                    visible: !!e && e.style.display !== 'none',
                    text: e && e.textContent,
                };
            })
        );
        emptyTexts.forEach((c) => {
            expect(c.visible).toBe(c.shown === 0);
            if (c.shown === 0) expect(c.text).toBe('这一列没有符合筛选的客户');
        });
        // 激活态得看得出来(只加 class 不换样式=状态撒谎)
        const bg = (n) => chip(page, n).evaluate((el) => getComputedStyle(el).backgroundColor);
        await expect.poll(async () => (await bg('missing')) !== (await bg('review'))).toBe(true);
        await shot(page, '05-filter-missing-zh-desktop.png');

        await chip(page, 'missing').click(); // 取消
        await chip(page, 'review').click();
        expect(await card(page, C_REVIEW_A).isVisible()).toBe(true);
        expect(await card(page, C_MAT_A).isVisible()).toBe(false);
        expect(await card(page, C_MAT_B).isVisible()).toBe(false);
        expect(await card(page, C_REVIEW_B).isVisible()).toBe(false);
        expect(await card(page, C_REVIEW_A).locator('.chip').first().innerText()).toBe('等你审');
        await shot(page, '06-filter-review-zh-desktop.png');

        // 多选是「或」不是「与」
        await chip(page, 'missing').click();
        for (const id of [C_MAT_A, C_MAT_B, C_REVIEW_A, C_REVIEW_B]) {
            expect(await card(page, id).isVisible()).toBe(true);
        }
        expect(await card(page, C_MISSING_REAL).isVisible()).toBe(false);
    });

    test('4b 筛到 0 张出空态 · 清除筛选把 chip/筛选态/搜索框一起清干净', async ({ page }) => {
        await open(page, { hash: '#/board' });
        await waitBoard(page);
        // 真数据当期截止日都在 8 月 → 风险(逾期)真的一张都不该命中
        await chip(page, 'risk').click();
        const empty = page.locator('#dashBody .kb-noresults');
        await expect(empty).toBeVisible();
        const emptyText = await empty.innerText();
        expect(emptyText).not.toMatch(/mx_no_results|mx_clear_filters/);
        expect(emptyText.length).toBeGreaterThan(10);
        // 搜索框也一起脏一下,验"三处一起清"
        await page.click('#searchInput');
        await page.keyboard.type('zzz-no-such-client');
        await expect(empty).toBeVisible();
        await shot(page, '07-filter-risk-empty-zh-desktop.png');

        await empty.locator('[data-action="clear-filters"]').click();
        await expect(page.locator('#dashBody .kb-noresults')).toHaveCount(0);
        expect(await page.inputValue('#searchInput')).toBe('');
        for (const n of ['missing', 'review', 'risk']) {
            expect(await chip(page, n).getAttribute('class')).not.toContain('on');
            expect(await chip(page, n).getAttribute('aria-pressed')).toBe('false');
        }
        expect(await page.locator('#dashBody .kcard:visible').count()).toBe(5);
    });

    test('4d 矩阵挂掉时 chip 高亮跟着筛选态一起归零(不留一颗点了会反选的亮 chip)', async ({
        page,
    }) => {
        let down = false;
        await page.route(
            (u) => u.pathname === '/api/tax-profile/matrix',
            async (route) => {
                if (!down) return route.continue();
                await route.fulfill({ status: 500, contentType: 'application/json', body: '{}' });
            }
        );
        await open(page, { hash: '#/board' });
        await waitBoard(page);
        await chip(page, 'missing').click();
        expect(await chip(page, 'missing').getAttribute('class')).toContain('on');

        down = true; // 矩阵端点挂掉,切走再切回触发重载
        await page.click('#vtMatrix');
        await page.click('#vtBoard');
        await page.waitForSelector('#dashBody .kanban', { state: 'visible', timeout: 20000 });
        await expect.poll(() => page.locator('#boardTools').isVisible()).toBe(false);
        expect(await chip(page, 'missing').getAttribute('class')).not.toContain('on');
        expect(await chip(page, 'missing').getAttribute('aria-pressed')).toBe('false');

        down = false; // 矩阵恢复:工具条回来,筛选是干净的,5 张卡一张不少
        await page.click('#vtMatrix');
        await page.click('#vtBoard');
        await waitBoard(page);
        expect(await chip(page, 'missing').getAttribute('class')).not.toContain('on');
        expect(await page.locator('#dashBody .kcard:visible').count()).toBe(5);
        await expect(page.locator('#dashBody .kb-noresults')).toHaveCount(0);
        await shot(page, '18-matrix-recovered-chips-clean-zh-desktop.png');
    });

    test('矩阵端点挂了 → 工具条整条收起,看板退回搬迁前的样子', async ({ page }) => {
        await page.route(
            (u) => u.pathname === '/api/tax-profile/matrix',
            (route) => route.fulfill({ status: 500, contentType: 'application/json', body: '{}' })
        );
        await open(page, { hash: '#/board' });
        await page.waitForSelector('#dashBody .kanban', { state: 'visible', timeout: 20000 });
        expect(await page.locator('#boardTools').isVisible()).toBe(false);
        expect(await page.locator('#boardBulkBar').isVisible()).toBe(false);
        await expect(page.locator('#dashBody .kmiss')).toHaveCount(0);
        expect(await page.locator('#dashBody .kcard').count()).toBe(5);
        await shot(page, '08-matrix-down-zh-desktop.png');
    });
});

// ---------------------------------------------------------------- 场景 3 + 5(改真响应)
test.describe('缺单条列义务名 / 风险命中 / 批量开单(改真矩阵响应)', () => {
    test.use({ viewport: DESKTOP });

    test('5b 缺单条点名缺哪几张单(按截止日排)· 泰语出泰文表号', async ({ page }) => {
        await open(page, { hash: '#/board', patch: true });
        await waitBoard(page);
        const t88 = await card(page, C_MISSING_REAL).locator('.kmiss-t').innerText();
        expect(t88).toContain('2569-07');
        expect(t88).toContain('2'); // 缺 2 张
        expect(t88).toContain('PND1');
        expect(t88).toContain('PP30');
        expect(t88.indexOf('PND1')).toBeLessThan(t88.indexOf('PP30')); // 截止日早的在前
        await expect(card(page, C_REVIEW_A).locator('.kmiss')).toBeVisible();
        await shot(page, '09-board-missing-zh-desktop.png');
    });

    test('5d 缺单条在 1280 桌面能读全(短表号不被 line-clamp 裁半句)', async ({ page }) => {
        await open(page, { hash: '#/board', patch: true });
        await waitBoard(page);
        const t = card(page, C_MISSING_REAL).locator('.kmiss-t');
        const box = await t.evaluate((el) => ({
            scrollH: el.scrollHeight,
            clientH: el.clientHeight,
            text: el.textContent,
            title: el.getAttribute('title'),
        }));
        // 招牌能力("这家还缺哪几张单")在桌面窄卡里被裁掉半句 = 等于没说
        expect(box.scrollH).toBeLessThanOrEqual(box.clientH);
        expect(box.text).toBe(box.title);
        // 取的是官方表号短码,不是后端 display_names 的长全名
        expect(box.text).not.toContain('申报');
    });

    test('5e 本期无需申报的客户不冒充缺单(不给告警条也不给勾选框)', async ({ page }) => {
        await page.route(
            (u) => u.pathname === '/api/tax-profile/matrix',
            async (route) => {
                const real = await (await route.fetch()).json();
                const m = patchMatrix(real);
                // 87 本期义务全部「无需申报」但本期没工单 —— 后端 missing_order 会是 true
                m.clients.forEach((c) => {
                    if (c.id === C_MAT_A) c.missing_order = true;
                });
                m.cells.forEach((c) => {
                    if (c.client_id === C_MAT_A) {
                        c.badge = 'no_need';
                        c.order_status = null;
                        c.work_order_id = null;
                    }
                });
                await route.fulfill({
                    contentType: 'application/json',
                    body: JSON.stringify(m),
                });
            }
        );
        await open(page, { hash: '#/board' });
        await waitBoard(page);
        await expect(card(page, C_MISSING_REAL).locator('.kmiss')).toBeVisible();
        await expect(card(page, C_MAT_A).locator('.kmiss')).toHaveCount(0);
        await expect(card(page, C_MAT_A).locator('.kb-check')).toHaveCount(0);
        await shot(page, '19-no-need-client-not-missing-zh-desktop.png');
    });

    test('5c 泰语缺单条', async ({ page }) => {
        await open(page, { hash: '#/board', patch: true, lang: 'th' });
        await waitBoard(page);
        const th = await card(page, C_MISSING_REAL).locator('.kmiss-t').innerText();
        expect(th).toContain('ภ.ง.ด.1');
        expect(th).toContain('ภ.พ.30');
        expect(th).not.toContain('还缺');
        await shot(page, '10-board-missing-th-desktop.png');
    });

    test('4c 风险(逾期)真能命中 —— 截止日读顺延后的日期', async ({ page }) => {
        await open(page, { hash: '#/board', patch: true });
        await waitBoard(page);
        await chip(page, 'risk').click();
        expect(await card(page, C_REVIEW_B).isVisible()).toBe(true); // 顺延后截止日已过
        expect(await card(page, C_MAT_A).isVisible()).toBe(false); // 同样缺料但没到期
        expect(await card(page, C_MISSING_REAL).isVisible()).toBe(false);
        await shot(page, '11-filter-risk-hit-zh-desktop.png');
    });

    test('3 多选 → 批量栏浮出带数量与账期 → 执行 → 报文真后端认', async ({ page, request }) => {
        const posted = [];
        await open(page, { hash: '#/board', patch: true, posted });
        await waitBoard(page);
        const bar = page.locator('#boardBulkBar');
        expect(await bar.isVisible()).toBe(false);

        await card(page, C_MISSING_REAL).locator('.kb-check').check();
        await expect(bar).toBeVisible();
        expect(await bar.innerText()).toContain('已选 1 家');

        await card(page, C_REVIEW_A).locator('.kb-check').check();
        const barText = await bar.innerText();
        expect(barText).toContain('已选 2 家');
        expect(barText).toContain('2569-07'); // 账期写在按钮上
        expect(barText).toContain('取消选择');
        expect(barText).not.toMatch(/kb_bulk/);
        // 吸底条不能压住看板内容:它在 dashBody 之后的正常流里,自然位置不与卡片重叠
        const geo = await page.evaluate(() => {
            const b = document.getElementById('boardBulkBar').getBoundingClientRect();
            const cards = Array.prototype.map.call(
                document.querySelectorAll('#dashBody .kcard'),
                (c) => c.getBoundingClientRect()
            );
            const covered = cards.filter((c) => c.top < b.bottom && c.bottom > b.top).length;
            return {
                bar: { top: b.top, bottom: b.bottom, h: b.height },
                vh: window.innerHeight,
                coveredCards: covered,
                totalCards: cards.length,
            };
        });
        expect(geo.bar.h).toBeGreaterThan(30);
        expect(geo.bar.bottom).toBeLessThanOrEqual(geo.vh + 1); // 真在视口内看得见
        await shot(page, '12-bulk-bar-zh-desktop.png');

        await bar.locator('[data-action="bulk-open"]').click();
        await expect(bar).toContainText('已开出 2 张单', { timeout: 15000 });
        expect(posted.length).toBe(2);
        posted.forEach((p) => {
            expect(p.period).toBe('2569-07');
            expect(p.intent).toBe('monthly_vat');
        });
        expect(posted.map((p) => p.workspace_client_id).sort()).toEqual(
            [C_MISSING_REAL, C_REVIEW_A].sort()
        );
        await shot(page, '13-bulk-result-zh-desktop.png');

        // 前端发的报文原样重放到真后端:必须 200,且幂等不新增(85 当期真已有单)。
        const before = await request.get(`${BASE}/api/workorder/orders?limit=1`, {
            headers: { Authorization: `Bearer ${TOKEN}` },
        });
        const countBefore = (await before.json()).count;
        const replay = posted.filter((p) => p.workspace_client_id === C_REVIEW_A)[0];
        const res = await request.post(`${BASE}/api/workorder/orders`, {
            headers: { Authorization: `Bearer ${TOKEN}` },
            data: replay,
        });
        expect(res.status()).toBe(200);
        const body = await res.json();
        expect(body.period).toBe('2569-07');
        expect(body.workspace_client_id).toBe(C_REVIEW_A);
        const after = await request.get(`${BASE}/api/workorder/orders?limit=1`, {
            headers: { Authorization: `Bearer ${TOKEN}` },
        });
        expect((await after.json()).count).toBe(countBefore); // 幂等:没塞新单
    });

    test('3b 勾选不把人导航进客户页(点击与空格都让路)· 取消选择收起操作条', async ({ page }) => {
        await open(page, { hash: '#/board', patch: true });
        await waitBoard(page);
        await card(page, C_MISSING_REAL).locator('.kmiss').click();
        expect(page.url()).toContain('#/board');
        expect(await card(page, C_MISSING_REAL).locator('.kb-check').isChecked()).toBe(true);

        await card(page, C_MISSING_REAL).locator('.kb-check').focus();
        await page.keyboard.press('Space');
        expect(page.url()).toContain('#/board');
        expect(await card(page, C_MISSING_REAL).locator('.kb-check').isChecked()).toBe(false);

        await card(page, C_MISSING_REAL).locator('.kb-check').check();
        await page.locator('#boardBulkBar [data-action="bulk-clear"]').click();
        expect(await page.locator('#boardBulkBar').isVisible()).toBe(false);
    });
});

// ---------------------------------------------------------------- 移动端 390×844
test.describe('移动端', () => {
    test.use(TOUCH);

    test('M1 缺单条 + 批量栏在 390 宽下不横滚 / 不遮内容', async ({ page }) => {
        const posted = [];
        await open(page, { hash: '#/board', patch: true, posted });
        await waitBoard(page);
        await expect(card(page, C_MISSING_REAL).locator('.kmiss')).toBeVisible();
        let sc = await noHScroll(page);
        expect(sc.scrollW).toBeLessThanOrEqual(sc.clientW + 1);
        await shot(page, '14-board-missing-zh-mobile.png');

        await card(page, C_MISSING_REAL).locator('.kb-check').check();
        await card(page, C_REVIEW_A).locator('.kb-check').check();
        const bar = page.locator('#boardBulkBar');
        await expect(bar).toBeVisible();
        expect(await bar.innerText()).toContain('已选 2 家');
        sc = await noHScroll(page);
        expect(sc.scrollW).toBeLessThanOrEqual(sc.clientW + 1);
        const geo = await bar.evaluate((el) => {
            const r = el.getBoundingClientRect();
            return { w: r.width, h: r.height, right: r.right, vw: window.innerWidth };
        });
        expect(geo.right).toBeLessThanOrEqual(geo.vw + 1); // 按钮没被挤出屏幕
        await page.screenshot({ path: path.join(ART, '15-bulk-bar-zh-mobile.png') });
    });

    test('M2 移动端筛选可点(触屏 40px 命中区)+ 矩阵空态', async ({ page }) => {
        await open(page, { hash: '#/board' });
        await waitBoard(page);
        const h = await chip(page, 'missing').evaluate((el) => el.getBoundingClientRect().height);
        expect(h).toBeGreaterThanOrEqual(36);
        await chip(page, 'risk').click();
        await expect(page.locator('#dashBody .kb-noresults')).toBeVisible();
        await page.screenshot({ path: path.join(ART, '16-filter-empty-zh-mobile.png') });

        await page.click('#vtMatrix');
        await page.waitForSelector('#matrixBody .mx-table', { state: 'visible', timeout: 20000 });
        await page.click('#matrixPeriodBtn');
        await page.click('#matrixPeriodMenu button[data-p="2569-05"]');
        await expect(page.locator('#matrixBody .mx-noobl')).toBeVisible({ timeout: 20000 });
        const sc = await noHScroll(page);
        expect(sc.scrollW).toBeLessThanOrEqual(sc.clientW + 1);
        await shot(page, '17-matrix-empty-zh-mobile.png');
    });
});
