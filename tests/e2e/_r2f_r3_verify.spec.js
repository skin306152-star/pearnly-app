// R2F-R3 · 账期入口深链与进度诚实 · 本地 stub 真浏览器验收(非 CI 用例 · 用完即删,
// 同 _in0b_intake_honesty_verify.spec.js 先例)
// ============================================================
// 真渲染代码(static/dist/ai.js/ai.css/ai.html 原样加载,零改造)+ 真 DOM,只桩网络层
// (page.route 拦 /api/*)。本文件盖派单书验收断言 1-4:
//   1) 看板开单控件常显(即使当期已有单)
//   2) 档案页工单历史区能开任意历史账期单
//   3) 深链 period 保持(tab 往返 + 刷新不丢 + 角标诚实 + 上传落对单)
//   4) 单批上传也显真进度「已传 X/N」
// 5(跑批进度/409/超时)拆到 _r2f_r3_progress_verify.spec.js(轮询耗时长,独立文件不
// 拖慢本文件其它用例)。
//
// 起法:npx playwright test tests/e2e/_r2f_r3_verify.spec.js
/* global window, document */
const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8992;
const BASE = `http://127.0.0.1:${PORT}`;
const PAGE = BASE + '/static/dist/ai.html';
const ART = path.join(__dirname, '_artifacts', 'r2f_r3');
const FIXTURES = path.join(__dirname, '..', 'fixtures', 'messy_intake_pack');

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT);
});

test.afterAll(() => {
    localServer.stop(server);
});

// 佛历账期换算同 ai-board.js::currentPeriodBE 的算法(公历年 + 543),测试侧独立算一遍
// 而不是 import 前端源码——固定桩数据要跟"当月"这个会漂移的真值对齐,否则「当期已有单」
// 场景在月初/月末附近可能对不上。
function currentPeriodBE(d) {
    const dt = d || new Date();
    const y = dt.getFullYear() + 543;
    const m = String(dt.getMonth() + 1).padStart(2, '0');
    return `${y}-${m}`;
}

// 通用路由桩:table 是 "METHOD /path"(query 串已剥离)→ handler(route, req, url) 的表,
// 未命中一律回落 200 '{}'(网关探针/desk feed 等不关心具体内容的端点够用)。
async function mockRoutes(page, table, opts = {}) {
    await page.route('**/api/**', async (route) => {
        const req = route.request();
        const url = new URL(req.url());
        const key = `${req.method()} ${url.pathname}`;
        const handler = table[key];
        if (handler) return handler(route, req, url);
        return route.fulfill({ contentType: 'application/json', body: '{}' });
    });
    await page.addInitScript(
        ([lang, token]) => {
            window.localStorage.setItem('mrpilot_token_ai', token || 'tok-r2f-r3');
            window.localStorage.setItem('mrpilot_lang', lang || 'en');
        },
        [opts.lang, opts.token]
    );
}

function jsonRoute(body, status) {
    return (route) =>
        route.fulfill({
            status: status || 200,
            contentType: 'application/json',
            body: JSON.stringify(body),
        });
}

test.describe('R2F #1 → S4 · 看板开单控件收敛', () => {
    // 2026-07-17 S4 拍板:推翻 R3「常显」——活工单卡挂开单控件=邀请误开第二张(真机实测
    // 困惑),本期已有工单的卡不再渲染账期下拉+开单;无本期工单的卡保留,开单默认当月。
    // 补开历史月入口=客户档案 → 工单历史(既有,R2F #2 仍覆盖)。
    test('有单卡不渲染开单控件;无单卡保留且开单递当月', async ({ page }) => {
        const period = currentPeriodBE();
        let createCalls = [];
        await mockRoutes(page, {
            'GET /api/workorder/orders': jsonRoute({
                orders: [{ id: 'wo-1', workspace_client_id: 'c1', period, status: 'collecting' }],
            }),
            'GET /api/workspace/clients': jsonRoute({
                clients: [
                    { id: 'c1', name: 'Acme Co', tax_id: '0105551234567' },
                    { id: 'c2', name: 'Beta Ltd', tax_id: '0105557654321' },
                ],
            }),
            'POST /api/workorder/orders': async (route, req) => {
                const body = req.postDataJSON();
                createCalls.push(body);
                return route.fulfill({
                    contentType: 'application/json',
                    body: JSON.stringify({ id: 'wo-2', period: body.period, status: 'collecting' }),
                });
            },
        });
        await page.goto(`${PAGE}#/board`);
        await page.waitForSelector('.kcard', { timeout: 15000 });

        // 有单卡(c1):无 .kopen,卡片本体仍可点进客户页(控件收敛不收敛导航)。
        const withOrder = page.locator('.kcard[data-client-id="c1"]');
        await expect(withOrder).toBeVisible();
        await expect(withOrder.locator('.kopen')).toHaveCount(0);

        // 无单卡(c2):控件保留,默认账期=当月(periodOptions 首项),开单递当月。
        const openCtl = page.locator('.kcard[data-client-id="c2"] .kopen');
        await expect(openCtl).toBeVisible();
        const select = openCtl.locator('[data-role="period-select"]');
        await expect(select).toHaveValue(period);
        await page.screenshot({ path: path.join(ART, '01-board-control-converged.png') });

        await openCtl.locator('[data-action="open-order"]').click();
        await expect.poll(() => createCalls.length, { timeout: 8000 }).toBeGreaterThan(0);
        expect(createCalls[0].period).toBe(period);
        expect(createCalls[0].workspace_client_id).toBe('c2');
        expect(createCalls[0].intent).toBe('monthly_vat');
    });
});

test.describe('R2F #2 · 档案页开历史账期单', () => {
    test('工单历史区顶部账期选择器可开任意历史期单,开完落对单', async ({ page }) => {
        // clientId 用纯数字串(同真实 workspace_client_id 口径):openHistoryPeriodOrder
        // 走 Number(S.clientId) 同 ai-client.js::openFirstOrder 既有先例,'c1' 这类非数字
        // 串会被 Number() 转成 NaN(JSON.stringify 再吐成 null),断言过不去。
        let createCalls = [];
        await mockRoutes(page, {
            'GET /api/workspace/clients/5': jsonRoute({
                client: { id: '5', name: 'Acme Co', tax_id: '0105551234567' },
            }),
            'GET /api/workorder/orders': jsonRoute({
                orders: [{ id: 'wo-old', period: '2568-06', status: 'archive' }],
            }),
            'POST /api/workorder/orders': async (route, req) => {
                const body = req.postDataJSON();
                createCalls.push(body);
                return route.fulfill({
                    contentType: 'application/json',
                    body: JSON.stringify({
                        id: 'wo-new',
                        period: body.period,
                        status: 'collecting',
                    }),
                });
            },
        });
        await page.goto(`${PAGE}#/clients/5/history`);
        await page.waitForSelector('#v-client-archive.on', { timeout: 15000 });
        await page.waitForSelector('#cav-history [data-role="ca-period-select"]', {
            timeout: 15000,
        });

        const select = page.locator('#cav-history [data-role="ca-period-select"]');
        const btn = page.locator('#cav-history [data-action="ca-open-period-order"]');
        await expect(select).toBeVisible();
        await expect(btn).toBeVisible();
        // 历史行(2568-06)也仍要正常呈现——开单入口不取代历史列表,只是加在它上面。
        await expect(page.locator('#cav-history .dlv-line')).toContainText('2568-06');
        await page.screenshot({ path: path.join(ART, '02-archive-history-open-ctl.png') });

        // 选一个跟既有历史行不同的历史账期,开单后必须落到那一期(不是恒落最新)。
        const options = await select.locator('option').allTextContents();
        const target = options.find((o) => o !== '2568-06') || options[1];
        await select.selectOption(target);
        await btn.click();

        await expect.poll(() => createCalls.length, { timeout: 8000 }).toBeGreaterThan(0);
        expect(createCalls[0].period).toBe(target);
        expect(createCalls[0].workspace_client_id).toBe(5);

        await expect
            .poll(() => new URL(page.url()).hash, { timeout: 8000 })
            .toContain(`period=${target}`);
        expect(new URL(page.url()).hash).toContain('/client/5/wo');
        await page.screenshot({ path: path.join(ART, '03-archive-history-opened.png') });
    });

    test('该客户尚无任何工单(空态)时开单入口依旧出现', async ({ page }) => {
        await mockRoutes(page, {
            'GET /api/workspace/clients/5': jsonRoute({
                client: { id: '5', name: 'Brand New Co', tax_id: '' },
            }),
            'GET /api/workorder/orders': jsonRoute({ orders: [] }),
        });
        await page.goto(`${PAGE}#/clients/5/history`);
        await page.waitForSelector('#v-client-archive.on', { timeout: 15000 });
        await expect(page.locator('#cav-history [data-role="ca-period-select"]')).toBeVisible({
            timeout: 15000,
        });
        // 默认语种 en(mockRoutes 未传 lang 时的兜底)—— ca_history_empty_t 的英文译文。
        await expect(page.locator('#cav-history')).toContainText('No work orders yet');
        await page.screenshot({ path: path.join(ART, '04-archive-empty-still-has-ctl.png') });
    });
});

// ---------------------------------------------------------------- period 保持 ----

function periodPersistFixture() {
    const may = { id: 'wo-may', period: '2569-05', status: 'collecting' };
    const latest = { id: 'wo-latest', period: currentPeriodBE(), status: 'collecting' };
    return { may, latest };
}

test.describe('R2F #3 · 深链 period 保持', () => {
    test('切 tab 往返 period 不丢、角标诚实、刷新不丢', async ({ page }) => {
        const { may, latest } = periodPersistFixture();
        await mockRoutes(page, {
            'GET /api/workspace/clients/c1': jsonRoute({
                client: { id: 'c1', name: 'Acme Co', tax_id: '0105551234567' },
            }),
            'GET /api/workorder/orders': jsonRoute({ orders: [may, latest] }),
            'GET /api/workorder/orders/wo-may': jsonRoute({
                id: 'wo-may',
                period: '2569-05',
                status: 'collecting',
                needs: [],
                numbers: {},
                flagged: [],
            }),
            'GET /api/workorder/orders/wo-latest': jsonRoute({
                id: 'wo-latest',
                period: latest.period,
                status: 'collecting',
                needs: [],
                numbers: {},
                flagged: [],
            }),
        });

        await page.goto(`${PAGE}#/client/c1/intake?period=2569-05`);
        await page.waitForSelector('#v-client.on', { timeout: 15000 });
        await expect(page.locator('#periodValue')).toHaveText('2569-05', { timeout: 15000 });

        // 工单/收料/档案 tab 往返(派单书原话):每一跳都必须带住 period,角标全程 2569-05,
        // hash 也不能丢 ?period=(丢了刷新就会落回最新期,见下一断言)。
        for (const tabId of ['#tabWo', '#tabProfile', '#tabIntake']) {
            await page.click(tabId);
            await expect(page.locator('#periodValue')).toHaveText('2569-05');
            await expect.poll(() => new URL(page.url()).hash).toContain('period=2569-05');
        }
        await page.screenshot({ path: path.join(ART, '05-period-survives-tabs.png') });

        // 刷新(真实浏览器 reload,不是 SPA 内部导航)——此前 bug:tab 切换丢了 ?period=,
        // 刷新后 mount() 走"不同客户"分支 periodIndexOf(null) 落回最新期,角标撒谎显当月。
        await page.reload();
        await page.waitForSelector('#v-client.on', { timeout: 15000 });
        await expect(page.locator('#periodValue')).toHaveText('2569-05', { timeout: 15000 });
        await page.screenshot({ path: path.join(ART, '06-period-survives-reload.png') });
    });

    test('deep-link 到五月账期后上传的文件落进五月单,不是最新单', async ({ page }) => {
        const { may, latest } = periodPersistFixture();
        const materialsCalls = [];
        await mockRoutes(page, {
            'GET /api/workspace/clients/c1': jsonRoute({
                client: { id: 'c1', name: 'Acme Co', tax_id: '0105551234567' },
            }),
            'GET /api/workorder/orders': jsonRoute({ orders: [may, latest] }),
            'GET /api/workorder/orders/wo-may': jsonRoute({
                id: 'wo-may',
                period: '2569-05',
                status: 'collecting',
                needs: [],
                numbers: {},
                flagged: [],
            }),
            'GET /api/workorder/orders/wo-latest': jsonRoute({
                id: 'wo-latest',
                period: latest.period,
                status: 'collecting',
                needs: [],
                numbers: {},
                flagged: [],
            }),
            'POST /api/workorder/orders/wo-may/materials': async (route) => {
                materialsCalls.push('wo-may');
                return route.fulfill({
                    contentType: 'application/json',
                    body: JSON.stringify({ registered: [{ item_id: 'i1' }], count: 1 }),
                });
            },
            'POST /api/workorder/orders/wo-latest/materials': async (route) => {
                materialsCalls.push('wo-latest');
                return route.fulfill({
                    contentType: 'application/json',
                    body: JSON.stringify({ registered: [{ item_id: 'i1' }], count: 1 }),
                });
            },
        });

        await page.goto(`${PAGE}#/client/c1/intake?period=2569-05`);
        await page.waitForSelector('#ikDrop', { timeout: 15000 });
        await page.setInputFiles('#ikFileInput', path.join(FIXTURES, 'normal_receipt.jpg'));
        await expect(page.locator('.dz-count b')).toHaveText('1');
        await page.click('[data-action="ik-upload"]');
        await expect.poll(() => materialsCalls.length, { timeout: 8000 }).toBeGreaterThan(0);
        expect(materialsCalls).toEqual(['wo-may']); // 治 F4 料裂两单:必须落五月单,不是最新单
        await page.screenshot({
            path: path.join(ART, '07-upload-lands-in-deep-linked-period.png'),
        });
    });
});

// ---------------------------------------------------------------- 上传真进度 ----

test.describe('R2F #4 · 上传真进度(单批也显 X/N)', () => {
    test('单批 3 个文件:上传中显示「已传 X/3」而非纯转圈', async ({ page }) => {
        await mockRoutes(page, {
            'GET /api/workorder/orders': jsonRoute({
                orders: [{ id: 'wo-1', period: '2569-05' }],
            }),
            'GET /api/workorder/orders/wo-1': jsonRoute({
                id: 'wo-1',
                status: 'collecting',
                needs: [],
                numbers: {},
                flagged: [],
            }),
            'GET /api/workspace/clients/c1': jsonRoute({
                client: { id: 'c1', name: 'Acme Co' },
            }),
            // 人为延迟,给测试一个窗口在请求飞行中截取"上传中"态的文案。
            'POST /api/workorder/orders/wo-1/materials': async (route) => {
                await new Promise((r) => setTimeout(r, 900));
                return route.fulfill({
                    contentType: 'application/json',
                    body: JSON.stringify({
                        registered: [{ item_id: 'a' }, { item_id: 'b' }, { item_id: 'c' }],
                        count: 3,
                    }),
                });
            },
        });
        await page.goto(`${PAGE}#/client/c1/intake`);
        await page.waitForSelector('#ikDrop', { timeout: 15000 });
        await page.setInputFiles('#ikFileInput', [
            path.join(FIXTURES, 'normal_receipt.jpg'),
            path.join(FIXTURES, 'fake_image.jpg'),
            path.join(FIXTURES, 'pos_summary.xlsx'),
        ]);
        await expect(page.locator('.dz-count b')).toHaveText('3');
        await page.click('[data-action="ik-upload"]');

        // 请求还在飞行中(900ms 延迟内)截图 + 断言真数字「/3」出现,不是空转省略号。
        const uploadingText = page.locator('.dz-t');
        await expect(uploadingText).toContainText('/3', { timeout: 3000 });
        await page.screenshot({ path: path.join(ART, '08-upload-progress-single-batch.png') });

        // 传完后落盘态(不再转圈,进入补料后重新跑面)。
        await expect(page.locator('.rerun-card')).toBeVisible({ timeout: 8000 });
    });
});

test.describe('R2F #6 · 四语 + 手机 390', () => {
    for (const lang of ['th', 'zh', 'ja']) {
        test(`四语(${lang}):新文案非原始 key`, async ({ page }) => {
            const period = currentPeriodBE();
            await mockRoutes(
                page,
                {
                    'GET /api/workspace/clients/c1': jsonRoute({
                        client: { id: 'c1', name: 'Acme Co' },
                    }),
                    'GET /api/workorder/orders': jsonRoute({ orders: [] }),
                },
                { lang }
            );
            await page.goto(`${PAGE}#/clients/c1/history`);
            await expect(page.locator('#cav-history [data-role="ca-period-select"]')).toBeVisible({
                timeout: 15000,
            });
            const hint = await page.locator('#cav-history .needs-sub').innerText();
            expect(hint).not.toContain('ca_history_open_hint');
            expect(hint.length).toBeGreaterThan(0);
            await page.screenshot({
                path: path.join(ART, `09-lang-${lang}.png`),
                fullPage: true,
            });
        });
    }

    test('手机 390:档案页开单控件可见 + 不新增横向溢出', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await mockRoutes(page, {
            'GET /api/workspace/clients/c1': jsonRoute({ client: { id: 'c1', name: 'Acme Co' } }),
            'GET /api/workorder/orders': jsonRoute({ orders: [] }),
        });
        await page.goto(`${PAGE}#/clients/c1/history`);
        const baseline = await page.evaluate(() => document.body.scrollWidth - window.innerWidth);
        await expect(page.locator('#cav-history [data-role="ca-period-select"]')).toBeVisible({
            timeout: 15000,
        });
        const withCtl = await page.evaluate(() => document.body.scrollWidth - window.innerWidth);
        expect(withCtl - baseline, '开单控件不该比空态多出横向溢出').toBeLessThanOrEqual(1);
        const box = await page.locator('#cav-history .kopen').boundingBox();
        expect(box.x + box.width, '开单控件右边不该出视口').toBeLessThanOrEqual(390 + 1);
        await page.screenshot({
            path: path.join(ART, '10-mobile-390.png'),
            fullPage: true,
        });
    });
});
