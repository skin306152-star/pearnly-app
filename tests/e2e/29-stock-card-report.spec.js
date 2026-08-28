// Pearnly E2E · 29 ERP 门户商品收发存报表(Stock Card · 路由 stock-card)
// ============================================================
// 2026-08-27 口径:网页主视图 = 一次 GET /api/stockcard/report,按商品连续排列的参考图
// 原样 13 列表格(期初行 + 期间逐笔 + 该组合计),不设「汇总→单品详情」两段式、未入账
// tab、归并/规则/搜索/状态。唯一报表附加能力 = 期初库存录入。
// 沿用桩路数:token 塞 localStorage → page.route 拦 /api/** 桩真实契约信封 → 绕开
// workspace-gate 直接调 window.loadStockCard。验的是前端拿到这份契约数据后渲染对不对。
// 显式断言旧交互不存在:#stc-view-list / #stc-view-detail / #stc-back / 可点击
// .stc-row[data-stc-key] 全部为 0,且旧路由 /summary /card /excluded /merge 从不出站。
//
// 颜色断言口径按 verification skill 第 3 节:三段式表头色现场拿
// getComputedStyle 与一个套同一 CSS 变量的探针元素比对(比"同一个令牌解析出的真实颜色"
// 是否真的落到了目标元素上,不比手抄 hex)。
// ============================================================
/* global window, document, getComputedStyle */

const path = require('path');
const { test, expect } = require('@playwright/test');
const localServer = require('./_local_static_server');
const {
    attachConsoleGuard,
    assertNoConsoleErrors,
    blockCfInsights,
} = require('./_helpers/console-guard');

const PORT = 8977;
const BASE = `http://127.0.0.1:${PORT}`;
const OUT = path.join(process.cwd(), 'tests', 'e2e', '_artifacts', 'stock-card');

let server;
test.beforeAll(async () => {
    server = await localServer.start(PORT, '/static/dist/home.html');
});
test.afterAll(() => localServer.stop(server));

// key 忠实于真后端形状(services/stockcard/grouping.py):商品档轨 p:<id> · 名字轨 n:<清洗名>
// 且名字轨 product_id 为 null(在商品标题里以「—」呈现,不是假 pid)。
const GROUPS = [
    {
        product: { key: 'p:WPC-001', product_id: 'WPC-001', name: 'WPC 仿木条 2 寸', unit: '条' },
        rows: [
            {
                date: '2024-06-01',
                doc_no: '',
                kind: 'open',
                desc: '',
                qty: '10',
                unit_price: null,
                amount: null,
                bal_qty: '10',
                bal_unit_cost: '250.00',
                bal_value: '2500.00',
            },
            {
                date: '2024-06-02',
                doc_no: 'PO-6706001',
                kind: 'in',
                desc: '向供应商采购入库',
                qty: '100',
                unit_price: '250.00',
                amount: '25000.00',
                bal_qty: '110',
                bal_unit_cost: '250.00',
                bal_value: '27500.00',
            },
            {
                date: '2024-06-03',
                doc_no: 'SO-6706001',
                kind: 'out',
                desc: '销售给客户 A',
                qty: '30',
                unit_price: '250.00',
                amount: '7500.00',
                bal_qty: '80',
                bal_unit_cost: '250.00',
                bal_value: '20000.00',
            },
        ],
        totals: {
            in_qty: '100',
            in_amount: '25000.00',
            out_qty: '30',
            out_amount: '7500.00',
            bal_qty: '80',
            bal_unit_cost: '250.00',
            bal_value: '20000.00',
        },
    },
    {
        product: { key: 'p:WTR-600', product_id: 'WTR-600', name: '山牌饮用水 600ml', unit: '箱' },
        rows: [
            {
                date: '2024-06-01',
                doc_no: '',
                kind: 'open',
                desc: '',
                qty: '0',
                unit_price: null,
                amount: null,
                bal_qty: '0',
                bal_unit_cost: null,
                bal_value: null,
            },
            {
                date: '2024-06-05',
                doc_no: 'SO-6706105',
                kind: 'out',
                desc: '销售给客户 B',
                qty: '30',
                unit_price: null,
                amount: null,
                bal_qty: '-30',
                bal_unit_cost: null,
                bal_value: null,
            },
        ],
        totals: {
            in_qty: '0',
            in_amount: null,
            out_qty: '30',
            out_amount: null,
            bal_qty: '-30',
            bal_unit_cost: null,
            bal_value: null,
        },
    },
    {
        product: { key: 'n:กระดาษ a4', product_id: null, name: 'กระดาษ A4', unit: 'รีม' },
        rows: [
            {
                date: '2024-06-01',
                doc_no: '',
                kind: 'open',
                desc: '',
                qty: '0',
                unit_price: null,
                amount: null,
                bal_qty: '0',
                bal_unit_cost: null,
                bal_value: null,
            },
            {
                date: '2024-06-04',
                doc_no: 'PO-6706104',
                kind: 'in',
                desc: '向供应商采购入库',
                qty: '10',
                unit_price: '95.00',
                amount: '950.00',
                bal_qty: '10',
                bal_unit_cost: '95.00',
                bal_value: '950.00',
            },
        ],
        totals: {
            in_qty: '10',
            in_amount: '950.00',
            out_qty: '0',
            out_amount: '0',
            bal_qty: '10',
            bal_unit_cost: '95.00',
            bal_value: '950.00',
        },
    },
];

const LEGACY_ROUTES = [
    '/api/stockcard/summary',
    '/api/stockcard/card',
    '/api/stockcard/excluded',
    '/api/stockcard/merge',
];

// captures:写路径真实出站请求(URL + 载荷)落在这,供契约断言;visited 记录所有出站 /api
// 路径,末尾断言旧路由从未被调用。overrides.report = 'empty'/'error' 驱动四态测试。
async function stubApi(page, captures = {}, overrides = {}) {
    const visited = [];
    await page.route('**/api/**', async (route) => {
        const url = new URL(route.request().url());
        const p = url.pathname;
        visited.push(p);
        if (p === '/api/stockcard/status') {
            return route.fulfill({ json: { ok: true, enabled: true } });
        }
        if (p === '/api/stockcard/report') {
            if (overrides.report === 'empty') {
                return route.fulfill({ json: { ok: true, groups: [] } });
            }
            if (overrides.report === 'error') {
                return route.fulfill({
                    json: { ok: false, error: { code: 'stc.unexpected' } },
                });
            }
            return route.fulfill({ json: { ok: true, groups: overrides.groups || GROUPS } });
        }
        // 期初 GET(POST 同一路径,靠方法分流):显式空桩 —— 弹窗预填回归锁用。
        if (p === '/api/stockcard/openings' && route.request().method() === 'GET') {
            return route.fulfill({ json: { ok: true, rows: [] } });
        }
        if (p === '/api/stockcard/openings') {
            captures.openings = {
                search: url.search,
                body: route.request().postDataJSON(),
            };
            return route.fulfill({ json: { ok: true } });
        }
        // 其余 /api/**(套账/权限探针等)不是本 spec 的验证对象,给中性成功信封放行。
        return route.fulfill({ json: { ok: true, data: {} } });
    });
    return visited;
}

async function neutralizeWorkspaceGate(page) {
    await page.evaluate(() => {
        window.getActiveWorkspaceClientId = () => 1;
        window.fetchWorkspaceClients = async () => [{ id: 1, name: 'E2E Workspace' }];
        window.enforceWorkspaceGate = () => {};
        window.showWorkspaceGate = () => {};
        window.autoSatisfyWorkspaceGate = () => {};
        document.body.classList.remove('workspace-gate-preboot');
        document.getElementById('workspace-gate-root')?.remove();
    });
}

async function resolvedVar(page, cssVar) {
    return page.evaluate((v) => {
        const probe = document.createElement('div');
        probe.style.background = `var(${v})`;
        document.body.appendChild(probe);
        const c = getComputedStyle(probe).backgroundColor;
        probe.remove();
        return c;
    }, cssVar);
}

async function openReport(page, captures = {}, overrides = {}) {
    await blockCfInsights(page);
    await page.addInitScript(() => {
        localStorage.setItem('mrpilot_token_erp', 'e2e-stock-card-token');
        // 默认语言是 th(state.ts 无偏好回落)· 本测试前半段断言写死中文,固定起始语言。
        localStorage.setItem('mrpilot_lang', 'zh');
        localStorage.setItem('pearnly_entry', 'erp');
    });
    const visited = await stubApi(page, captures, overrides);
    // 本地静态服没有生产 /erp 路由；将它映射到本次提交的 home 成品，既保留真实
    // ERP pathname/会话槽，又避免 CI 在部署前拿线上旧版本断言新页面。
    await page.route(`${BASE}/erp`, (route) =>
        route.fulfill({
            path: path.join(localServer.ROOT, 'static', 'dist', 'home.html'),
            contentType: 'text/html',
        })
    );
    await page.goto(`${BASE}/erp#/stock-card`);
    await page.waitForFunction(() => window.location.pathname === '/erp');
    await page.waitForFunction(() => typeof window.loadStockCard === 'function');
    await neutralizeWorkspaceGate(page);
    await page.evaluate(() => window.routeTo('stock-card'));
    return visited;
}

test.describe('ERP 门户 · 商品收发存报表(2026-08-27 长表面)', () => {
    test('桌面 · 连续多商品表 + 旧交互不存在 + 期初弹窗 + 泰语切换', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        const guard = attachConsoleGuard(page);
        const captures = {};
        const visited = await openReport(page, captures);

        // ── ① 主视图:三段式表头 + 三个商品表连续排列 ──
        await expect(page.locator('#stc-report .stc-group')).toHaveCount(3);
        const desktopScroll = await page
            .locator('#stc-report .stc-scroll')
            .first()
            .evaluate((el) => ({ client: el.clientWidth, scroll: el.scrollWidth }));
        // border-collapse 会把最右描边计入约 2px scrollWidth；内容列必须全部在首屏。
        expect(desktopScroll.scroll, '1280 桌面必须一眼看全 13 列').toBeLessThanOrEqual(
            desktopScroll.client + 2
        );
        // 商品标题只显示名称 / 编码 / 单位。
        const g1 = page.locator('#stc-report .stc-group').first();
        await expect(g1.locator('.stc-group-name')).toHaveText('WPC 仿木条 2 寸');
        await expect(g1.locator('.stc-group-code')).toHaveText('WPC-001');
        await expect(g1.locator('.stc-group-unit')).toHaveText('条');
        // 名字轨没有商品编码时不造一个「—」标签,只显示票面商品名与单位。
        const g3 = page.locator('#stc-report .stc-group').nth(2);
        await expect(g3.locator('.stc-group-name')).toHaveText('กระดาษ A4');
        await expect(g3.locator('.stc-group-code')).toHaveCount(0);
        await expect(g3.locator('.stc-group-unit')).toHaveText('รีม');

        // 每个商品表都是参考图原样 13 列表头(日期/单据号/类型/摘要 + 入/出/结存各三列)。
        const tbl = g1.locator('table');
        await expect(tbl.locator('thead .stc-grp th').nth(0)).toHaveText('日期');
        await expect(tbl.locator('thead .stc-grp th').nth(1)).toHaveText('单据号');
        await expect(tbl.locator('thead .stc-grp th').nth(2)).toHaveText('类型');
        await expect(tbl.locator('thead .stc-grp th').nth(3)).toHaveText('摘要');
        await expect(tbl.locator('thead th.stc-g-in[colspan="3"]').first()).toHaveText('入库');
        await expect(tbl.locator('thead th.stc-g-out[colspan="3"]').first()).toHaveText('出库');
        await expect(tbl.locator('thead th.stc-g-bal[colspan="3"]').first()).toHaveText('结存');
        // 日期严格按参考图日/月/佛历年,类型是普通彩色文字而不是额外胶囊组件。
        await expect(tbl.locator('tbody tr').first().locator('td').first()).toHaveText(
            '01/06/2567'
        );
        await expect(tbl.locator('tbody tr').first().locator('td').nth(2)).toContainText('期初');
        await expect(tbl.locator('.stc-chip')).toHaveCount(0);
        await expect(tbl.locator('tbody tr').nth(0)).toContainText('250.00');
        await expect(tbl.locator('tbody tr')).toHaveCount(3); // 期初 + 2 笔流水
        await expect(tbl.locator('tbody tr').nth(2)).toContainText('7,500.00');
        expect(await tbl.innerText(), '参考图金额格不额外添加泰铢符号').not.toContain('฿');
        // 末尾该商品合计。
        await expect(tbl.locator('tfoot tr')).toHaveCount(1);
        await expect(tbl.locator('tfoot tr').first()).toContainText('合计');
        // 第二商品(负库存)两行:期初 + 一笔出库。负数照实显示,不发明状态列或红底。
        const g2 = page.locator('#stc-report .stc-group').nth(1);
        await expect(g2.locator('tbody tr')).toHaveCount(2);
        await expect(g2.locator('tbody tr').nth(1)).toContainText('-30');
        await expect(page.locator('#stc-report .stc-group tbody tr.neg')).toHaveCount(0);

        // 三段式表头色:真拿 computed 值与同令牌探针比对。
        const expIn = await resolvedVar(page, '--green-700');
        const expOut = await resolvedVar(page, '--pink-800');
        const expBal = await resolvedVar(page, '--violet-800');
        const grpHead = page.locator('#stc-report .stc-group').first().locator('thead');
        expect(
            await grpHead
                .locator('th.stc-g-in')
                .first()
                .evaluate((el) => getComputedStyle(el).backgroundColor),
            '入库表头色'
        ).toBe(expIn);
        expect(
            await grpHead
                .locator('th.stc-g-out')
                .first()
                .evaluate((el) => getComputedStyle(el).backgroundColor),
            '出库表头色'
        ).toBe(expOut);
        expect(
            await grpHead
                .locator('th.stc-g-bal')
                .first()
                .evaluate((el) => getComputedStyle(el).backgroundColor),
            '结存表头色'
        ).toBe(expBal);
        // ── ② 旧「汇总→单品详情」交互不存在 ──
        await expect(page.locator('#stc-view-list')).toHaveCount(0);
        await expect(page.locator('#stc-view-detail')).toHaveCount(0);
        await expect(page.locator('#stc-back')).toHaveCount(0);
        await expect(page.locator('.stc-row[data-stc-key]')).toHaveCount(0);
        await expect(page.locator('[data-stc-merge]')).toHaveCount(0);
        await expect(page.locator('#stc-mg-mask')).toHaveCount(0);
        await expect(page.locator('#stc-tab-excluded')).toHaveCount(0);
        // 旧路由从不出站。
        expect(
            visited.some((p) => LEGACY_ROUTES.includes(p)),
            `旧路由出站: ${visited.filter((p) => LEGACY_ROUTES.includes(p)).join(', ')}`
        ).toBe(false);

        // ── ③ 不再有「未入账 / 归并 / 状态 / 点击商品查看明细 / 返回商品列表」文案 ──
        const stcText = await page.locator('#page-stock-card').innerText();
        for (const bad of ['未入账', '归并', '状态', '点击商品', '返回商品列表']) {
            expect(stcText, `不应出现旧文案「${bad}」`).not.toContain(bad);
        }

        await page.screenshot({ path: path.join(OUT, '01-desktop-report.png'), fullPage: true });

        // ── ④ 期初库存弹窗(唯一报表附加能力):按当前商品列表铺行 · 保存走真实出站契约 ──
        await page.locator('#stc-btn-opening').click();
        await expect(page.locator('#stc-op-mask')).toBeVisible();
        await expect(page.locator('#stc-op-tbl tr[data-op-key]')).toHaveCount(3);
        // 回归锁:期初预填只认 GET /openings 的已存用户期初(空桩 → 全空),不预填计算结转。
        await expect(
            page.locator('tr[data-op-key="p:WTR-600"] [data-op-qty]'),
            '计算结转的开头不预填'
        ).toHaveValue('');
        const modalWidth = await page
            .locator('#stc-op-mask .modal.stc')
            .evaluate((node) => node.getBoundingClientRect().width);
        expect(modalWidth).toBeGreaterThanOrEqual(900);
        await page.waitForTimeout(300);
        await page.screenshot({
            path: path.join(OUT, '05-opening-modal-wide.png'),
            fullPage: false,
        });
        await page.fill('tr[data-op-key="p:WPC-001"] [data-op-qty]', '5');
        await page.fill('tr[data-op-key="n:กระดาษ a4"] [data-op-qty]', '7');
        await page.locator('#stc-op-save').click();
        await expect(page.locator('#stc-op-mask')).toBeHidden();
        expect(captures.openings.search).toContain('workspace_client_id=1');
        expect(captures.openings.body.workspace_client_id).toBeUndefined();
        expect(captures.openings.body.rows).toEqual([
            expect.objectContaining({ product_id: 'WPC-001', qty: '5' }),
            expect.objectContaining({ name: 'กระดาษ a4', qty: '7' }),
        ]);

        // ── ⑤ 泰语切换:主表 / 商品标题 / 期初按钮全刷新 ──
        await page.evaluate(() => window.applyLang('th'));
        const thExpect = await page.evaluate(() => ({
            title: window.I18N.th['stc-title'],
            colIn: window.I18N.th['stc-col-in'],
            colBal: window.I18N.th['stc-col-bal'],
            btnOpening: window.I18N.th['stc-btn-opening'],
        }));
        await expect(page.locator('.stc > .stc-head .t')).toHaveText(thExpect.title);
        await expect(page.locator('#stc-report .stc-group').first().locator('thead')).toContainText(
            thExpect.colIn
        );
        await expect(page.locator('#stc-report .stc-group').first().locator('thead')).toContainText(
            thExpect.colBal
        );
        await expect(page.locator('#stc-btn-opening')).toContainText(thExpect.btnOpening);
        // 商品标题(名称/编码/单位)不因切语言丢内容。
        await expect(page.locator('#stc-report .stc-group-name').first()).toHaveText(
            'WPC 仿木条 2 寸'
        );
        await page.screenshot({ path: path.join(OUT, '05-thai.png'), fullPage: true });

        assertNoConsoleErrors(expect, guard);
    });

    test('期初库存弹窗 · 长商品名完整换行且不覆盖输入列', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        const longName =
            'แป้งฝุ่น สูตร PERFECT TRANSLUCENT LOOSE SE POWDER SPF 27 PA+++ รุ่นพิเศษสำหรับร้านค้า';
        const longGroups = [
            {
                ...GROUPS[0],
                product: { ...GROUPS[0].product, name: longName },
            },
        ];
        await openReport(page, {}, { groups: longGroups });
        await page.locator('#stc-btn-opening').click();
        const nameCell = page.locator('#stc-op-tbl .stc-op-name');
        await expect(nameCell).toHaveText(longName);
        const metrics = await nameCell.evaluate((cell) => {
            const next = cell.nextElementSibling;
            const box = cell.getBoundingClientRect();
            const nextBox = next?.getBoundingClientRect();
            const style = getComputedStyle(cell);
            return {
                whiteSpace: style.whiteSpace,
                overflowWrap: style.overflowWrap,
                fits: cell.scrollWidth <= cell.clientWidth + 1,
                noOverlap: !nextBox || box.right <= nextBox.left + 1,
                height: box.height,
            };
        });
        expect(metrics.whiteSpace).toBe('normal');
        expect(metrics.overflowWrap).toBe('anywhere');
        expect(metrics.fits, '长商品名必须完整收在商品格内').toBe(true);
        expect(metrics.noOverlap, '商品名不得覆盖数量输入列').toBe(true);
        expect(metrics.height, '长商品名应通过多行展示').toBeGreaterThan(48);
        await page.screenshot({
            path: path.join(OUT, '06-opening-long-name.png'),
            fullPage: false,
            animations: 'disabled',
        });
    });

    test('手机视口(390×844)· 页面本体不横向溢出 · 各商品表容器可横滚', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        const visited = await openReport(page);
        await expect(page.locator('#stc-report .stc-group')).toHaveCount(3);

        // 页面本体不得横向溢出(响应式硬规)· 每个商品表格容器自己横滚。
        const bodyOverflow = await page.evaluate(
            () => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1
        );
        expect(bodyOverflow, '页面本体不横向溢出').toBe(true);
        const scrollCount = await page.locator('#stc-report .stc-scroll').count();
        expect(scrollCount).toBe(3);
        const overs = await page
            .locator('#stc-report .stc-scroll')
            .evaluateAll((els) => els.map((el) => getComputedStyle(el).overflowX));
        expect(
            overs.every((v) => v === 'auto'),
            '每个商品表容器 overflowX=auto'
        ).toBe(true);
        const mobileScroll = await page
            .locator('#stc-report .stc-scroll')
            .first()
            .evaluate((el) => ({ client: el.clientWidth, scroll: el.scrollWidth }));
        expect(mobileScroll.scroll, '390 手机必须只在商品表内部横滚').toBeGreaterThan(
            mobileScroll.client
        );
        // 商品标题仍清楚可辨(名称/编码/单位可见)。
        await expect(page.locator('#stc-report .stc-group-name').first()).toBeVisible();
        await expect(page.locator('#stc-report .stc-group-code').first()).toBeVisible();
        await page.screenshot({ path: path.join(OUT, '06-mobile.png'), fullPage: true });
        // 旧交互在手机同样不存在。
        await expect(page.locator('#stc-view-list')).toHaveCount(0);
        expect(visited.some((p) => LEGACY_ROUTES.includes(p))).toBe(false);
    });

    test('四态 · 空态诚实且旧交互不存在', async ({ page }) => {
        const guard = attachConsoleGuard(page);

        // 空态:groups 为空 → 诚实说「没有」,不是报错。
        await openReport(page, {}, { report: 'empty' });
        await expect(page.locator('#stc-report .stc-state')).toBeVisible();
        await expect(page.locator('#stc-report .stc-state')).toContainText('没有已过账的商品单据');
        await expect(page.locator('#stc-report .stc-group')).toHaveCount(0);

        await expect(page.locator('#stc-view-list')).toHaveCount(0);
        await expect(page.locator('#stc-view-detail')).toHaveCount(0);
        assertNoConsoleErrors(expect, guard);
    });

    test('四态 · 错误态给重试出路且旧交互不存在', async ({ page }) => {
        const guard = attachConsoleGuard(page);

        // 失败信封 → 说这是加载失败 + 给重试出路；不额外制造浏览器网络噪音。
        await openReport(page, {}, { report: 'error' });
        await expect(page.locator('#stc-report [data-state="error"]')).toBeVisible();
        await expect(page.locator('#stc-report [data-stc-report-retry]')).toBeVisible();
        await expect(page.locator('#stc-report')).toContainText('加载失败');

        // 旧交互在错误态同样不存在。
        await expect(page.locator('#stc-view-list')).toHaveCount(0);
        await expect(page.locator('#stc-view-detail')).toHaveCount(0);
        await expect(page.locator('#stc-back')).toHaveCount(0);

        assertNoConsoleErrors(expect, guard);
    });
});
