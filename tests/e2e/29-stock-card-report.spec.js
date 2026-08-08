// Pearnly E2E · 29 事务所端商品收发存报表(Stock Card · 路由 stock-card)
// ============================================================
// 后端 /api/stockcard/* 与前端并行施工,真库暂无可用测试账号(24/25 一类真登录 spec
// 需要的 hasCreds() 测试号覆盖不到这条新路由)。照 26-purchase-product-wiring.spec.js
// 的桩路数:token 塞 localStorage → page.route 拦 /api/** 桩真实契约信封 → 绕开
// workspace-gate 直接调 window.loadStockCard。验的是「前端拿到这份契约数据后渲染
// 对不对」,不是后端本身(后端另有测试)。
//
// 断言口径按 verification skill 第 3 节:三段式表头色 / 负库存行红色都现场拿
// getComputedStyle 与一个套同一 CSS 变量的探针元素比对(比"真实值"本身,不比手抄
// hex)——闸值哪天调了颜色,断言跟着走,不会因为改了色号就假红或漏判。
// ============================================================
/* global window, document, getComputedStyle */

const path = require('path');
const { test, expect } = require('@playwright/test');
const {
    attachConsoleGuard,
    assertNoConsoleErrors,
    blockCfInsights,
} = require('./_helpers/console-guard');

const OUT = path.join(process.cwd(), 'tests', 'e2e', '_artifacts', 'stock-card');

// key 忠实于真后端形状(services/stockcard/grouping.py):商品档轨 p:<id> · 名字轨 n:<清洗名>
// 且名字轨 product_id 为 null —— 旧夹具给名字轨编了个假 product_id,恰好把「归并弹窗拿
// product_id 当 value 而它恒空」的真断裂藏住了(标识符必须来自真实产物,前科见记忆)。
const PRODUCTS = [
    {
        key: 'p:WPC-001',
        product_id: 'WPC-001',
        name: 'WPC 仿木条 2 寸',
        unit: '条',
        opening_qty: null,
        in_qty: '150',
        out_qty: '60',
        bal_qty: '90',
        bal_unit_cost: '254.17',
        bal_value: '22875.30',
        negative: false,
        matched: true,
    },
    {
        key: 'p:WTR-600',
        product_id: 'WTR-600',
        name: '山牌饮用水 600ml',
        unit: '箱',
        // -30 = 模拟「计算结转」的负期初:它不是用户手填的期初,期初弹窗预填不得带上它
        // (2026-08-08 口径 · 预填只认 GET /openings 的已存用户期初)。
        opening_qty: '-30',
        in_qty: '100',
        out_qty: '130',
        bal_qty: '-30',
        bal_unit_cost: '60.00',
        bal_value: '-1800.00',
        negative: true,
        matched: true,
    },
    {
        key: 'n:กระดาษ a4',
        product_id: null,
        name: 'กระดาษ A4',
        unit: 'รีม',
        opening_qty: null,
        in_qty: '10',
        out_qty: '4',
        bal_qty: '6',
        bal_unit_cost: '95.00',
        bal_value: '570.00',
        negative: false,
        matched: false,
    },
    {
        key: 'n:กระดาษ เอ4',
        product_id: null,
        name: 'กระดาษ เอ4',
        unit: 'รีม',
        opening_qty: null,
        in_qty: '2',
        out_qty: '0',
        bal_qty: '2',
        bal_unit_cost: '95.00',
        bal_value: '190.00',
        negative: false,
        matched: false,
    },
];

const EXCLUDED = [
    {
        date: '2024-06-04',
        doc_no: 'INV-1102',
        desc: '货物运费',
        amount: '800.00',
        reason: 'service',
        side: 'purchase',
    },
    {
        date: '2024-06-06',
        doc_no: 'CS-208',
        desc: '现金票(只有总额)',
        amount: '1500.00',
        reason: 'total_only',
        side: 'sales',
    },
    {
        date: '2024-06-09',
        doc_no: 'INV-1150',
        desc: '办公耗材',
        amount: '640.00',
        reason: 'no_qty_price',
        side: 'purchase',
    },
];

const CARD_ROWS = [
    {
        date: '2024-06-01',
        doc_no: 'PO-6706001',
        kind: 'in',
        desc: '向供应商采购入库',
        qty: '100',
        unit_price: '250.00',
        amount: '25000.00',
        bal_qty: '100',
        bal_unit_cost: '250.00',
        bal_value: '25000.00',
    },
    {
        date: '2024-06-03',
        doc_no: 'SO-6706001',
        kind: 'out',
        desc: '销售给客户 A',
        qty: '30',
        unit_price: null,
        amount: null,
        bal_qty: '70',
        bal_unit_cost: '250.00',
        bal_value: '17500.00',
    },
    {
        date: '2024-06-05',
        doc_no: 'PO-6706002',
        kind: 'in',
        desc: '向供应商采购入库',
        qty: '50',
        unit_price: '260.00',
        amount: '13000.00',
        bal_qty: '120',
        bal_unit_cost: '254.17',
        bal_value: '30500.00',
    },
];

// captures:写路径真实出站请求(URL + 载荷)落在这,供契约断言 —— 桩只回信封,不吞形状。
async function stubApi(page, captures = {}) {
    await page.route('**/api/**', async (route) => {
        const url = new URL(route.request().url());
        const p = url.pathname;
        if (p === '/api/stockcard/status') {
            return route.fulfill({ json: { ok: true, enabled: true } });
        }
        if (p === '/api/stockcard/summary') {
            return route.fulfill({
                json: { ok: true, products: PRODUCTS, excluded_count: EXCLUDED.length },
            });
        }
        if (p === '/api/stockcard/excluded') {
            return route.fulfill({ json: { ok: true, rows: EXCLUDED } });
        }
        if (p === '/api/stockcard/card') {
            const key = url.searchParams.get('key');
            const prod = PRODUCTS.find((x) => x.key === key) || PRODUCTS[0];
            return route.fulfill({
                json: {
                    ok: true,
                    product: {
                        product_id: prod.product_id,
                        name: prod.name,
                        unit: prod.unit,
                        matched: prod.matched,
                    },
                    rows: CARD_ROWS,
                    totals: {},
                },
            });
        }
        // 期初 GET(POST 同一路径,靠方法分流):显式空桩 —— 弹窗预填回归锁用(见下),
        // 别拦到下面的 POST 分支(captures 记录出站请求那条逻辑必须保留)。
        if (p === '/api/stockcard/openings' && route.request().method() === 'GET') {
            return route.fulfill({ json: { ok: true, rows: [] } });
        }
        if (p === '/api/stockcard/openings' || p === '/api/stockcard/merge') {
            captures[p.split('/').pop()] = {
                search: url.search,
                body: route.request().postDataJSON(),
            };
            return route.fulfill({ json: { ok: true } });
        }
        // 其余 /api/**(套账/权限探针等)不是本 spec 的验证对象,给中性成功信封放行。
        return route.fulfill({ json: { ok: true, data: {} } });
    });
}

// 三段式表头色 / 负库存行红照实生效:现场建一个只套同一 CSS 变量的探针元素,
// 拿它的 computed 值当基准比对目标元素的 computed 值——比的是"同一个令牌解析出的
// 真实颜色是否真的落到了目标元素上",不是手抄一份 hex 出来猜。
// 套账硬门(workspace-gate.ts)按 /api/me/modules 的 needs_onboarding / 0 套账异步判定,
// 桩回包给不出真套账列表时门会在 boot 完成后重新盖屏——不是移一次 DOM 就完事,得连它据以
// 判断"要不要盖"的函数一起短路,否则 boot 的异步链路随时把门重新盖回来(见首次真跑复现)。
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

test.describe('事务所端 · 商品收发存报表', () => {
    test('列表/单品卡/未入账/期初弹窗/泰语切换 —— 真浏览器桩数据验收', async ({ page }) => {
        const guard = attachConsoleGuard(page);
        await blockCfInsights(page);
        await page.addInitScript(() => {
            localStorage.setItem('mrpilot_token', 'e2e-stock-card-token');
            // 默认语言是 th(state.ts 无偏好回落)· 本测试前半段断言写死中文,
            // 固定起始语言避免和「⑤ 泰语切换」那段的语言状态互相干扰。
            localStorage.setItem('mrpilot_lang', 'zh');
        });
        const captures = {};
        await stubApi(page, captures);

        // 带 #/stock-card 深链进场:core-boot bootstrap 读 location.hash 决定 initialRoute
        // (core-boot.ts:415),让 SPA 自己的路由器从第一帧起就认定当前路由是 stock-card——
        // 不然直接调 window.loadStockCard() 只是手填了 DOM,routeTo 内部的 currentRoute 仍是
        // 默认 dms-intake,boot 收尾的 reloadCurrentRoute 一来就把页面切回默认路由盖掉。
        await page.goto('/home#/stock-card'); // 走服务端路由(no-cache)· 直连 /static/dist/home.html 会吃 CF 30 天 immutable 缓存的旧壳(CI 美国节点已实锤)
        await page.waitForFunction(() => typeof window.loadStockCard === 'function');
        // 绕开套账硬门(本 spec 验的是 stock-card 页面本身,不是套账选择流程)· 首帧自动路由
        // 触发的那次 loadStockCard 早于本行,用的还是未接管的 getActiveWorkspaceClientId
        // (真实值 null → 页面落"请选账套"态),接管后重调一次拿到真桩数据。
        await neutralizeWorkspaceGate(page);
        await page.evaluate(() => window.routeTo('stock-card'));

        // ── ① 列表态:四行落地(含负库存 + 两条未归并名字轨)──
        await expect(page.locator('.stc-row')).toHaveCount(4);
        const negRow = page.locator('.stc-row.neg');
        await expect(negRow).toHaveCount(1);
        await expect(negRow).toContainText('山牌饮用水');
        await expect(page.locator('.stc-chip-um')).toHaveCount(2);
        await expect(page.locator('.stc-chip-um').first()).toContainText('未归并');
        await expect(page.locator('#stc-excluded-cnt')).toHaveText('3');

        // 三段式表头 + 负库存行:真拿 computed 值与同令牌探针比对(不是看 class 在不在)。
        const inBg = await page
            .locator('.stc thead th.stc-g-in')
            .first()
            .evaluate((el) => getComputedStyle(el).backgroundColor);
        const outBg = await page
            .locator('.stc thead th.stc-g-out')
            .first()
            .evaluate((el) => getComputedStyle(el).backgroundColor);
        const balBg = await page
            .locator('.stc thead th.stc-g-bal')
            .first()
            .evaluate((el) => getComputedStyle(el).backgroundColor);
        const [expIn, expOut, expBal] = await Promise.all([
            resolvedVar(page, '--green-700'),
            resolvedVar(page, '--pink-800'),
            resolvedVar(page, '--violet-800'),
        ]);
        expect(inBg, '入库表头色 = --green-700 真实解析值').toBe(expIn);
        expect(outBg, '出库表头色 = --pink-800 真实解析值').toBe(expOut);
        expect(balBg, '结存表头色 = --violet-800 真实解析值').toBe(expBal);
        expect(new Set([inBg, outBg, balBg]).size, '三段表头三种不同颜色').toBe(3);

        // 表头对齐新标准(2026-08-08 Zihao 拍板表格对齐新标准 · DESIGN_SYSTEM §21,
        // 推翻 08-07「单列文字左/数字右」口径):表头一律居中、短内容格(数字)居中、
        // 长文本格(商品名)靠左 —— 全部量 computed 值,不看 class。
        const align = (loc) => loc.evaluate((el) => getComputedStyle(el).textAlign);
        expect(await align(page.locator('.stc thead .stc-grp th').first()), '商品表头居中').toBe(
            'center'
        );
        expect(
            await align(page.locator('.stc thead .stc-grp th.num').first()),
            '期初数字表头居中'
        ).toBe('center');
        expect(
            await align(page.locator('.stc thead th[colspan]').first()),
            '跨列色带组头居中'
        ).toBe('center');
        expect(await align(page.locator('.stc-row td').first()), '商品名格靠左').toBe('left');
        expect(await align(page.locator('.stc-row td.num').first()), '数字格居中').toBe('center');
        expect(await align(page.locator('.stc-row td.c').first()), '单位格居中').toBe('center');

        const negCellBg = await negRow
            .locator('td')
            .first()
            .evaluate((el) => getComputedStyle(el).backgroundColor);
        const expBad = await resolvedVar(page, '--bad-weak');
        expect(negCellBg, '负库存整行底色 = --bad-weak 真实解析值').toBe(expBad);
        const okRowBg = await page
            .locator('.stc-row:not(.neg)')
            .first()
            .locator('td')
            .first()
            .evaluate((el) => getComputedStyle(el).backgroundColor);
        expect(negCellBg, '负库存行底色应不同于正常行').not.toBe(okRowBg);

        await page.screenshot({ path: path.join(OUT, '01-list.png'), fullPage: true });

        // 悬停回归锁(2026-08-08):负库存行悬停整行统一亮 —— 钉死「悬停时唯独入库格
        // 不跟着亮」的复发面(旧规则 tr.neg td.stc-c-in 与悬停规则同为 (0,3,3) 且写在
        // 其后,单压入库格;已整条删除,非悬停仍整行统一红底)。
        const negInCell = negRow.locator('td.stc-c-in');
        const negInBgBefore = await negInCell.evaluate(
            (el) => getComputedStyle(el).backgroundColor
        );
        await negRow.hover();
        const negInBgHover = await negInCell.evaluate((el) => getComputedStyle(el).backgroundColor);
        const negFirstBgHover = await negRow
            .locator('td')
            .first()
            .evaluate((el) => getComputedStyle(el).backgroundColor);
        expect(negInBgHover, '悬停时入库格与同行普通格同底色(整行统一亮)').toBe(negFirstBgHover);
        expect(negInBgHover, '悬停时入库格底色确实变了(不再被单压)').not.toBe(negInBgBefore);
        await page.screenshot({ path: path.join(OUT, '07-hover-row.png'), fullPage: false });
        await page.mouse.move(0, 0);

        // ── ② 单品卡详情:点行进流水 ──
        await page.locator('.stc-row[data-stc-key="p:WPC-001"]').click();
        await expect(page.locator('#stc-view-detail')).toBeVisible();
        await expect(page.locator('#stc-view-list')).toBeHidden();
        await expect(page.locator('#stc-tbl-detail tbody tr')).toHaveCount(3);
        // 结存段内子列分隔线回归锁(2026-08-08):数量/单价/金额三子列之间至少 1px 细分隔线,
        // 不随色带底色糊成一片。
        const balMid = page.locator('#stc-tbl-detail tbody tr td.stc-c-bal').nth(1);
        const balMidBorder = await balMid.evaluate((el) => getComputedStyle(el).borderLeftWidth);
        expect(
            parseFloat(balMidBorder),
            '结存段中间子列(单价)左分隔线 ≥ 1px'
        ).toBeGreaterThanOrEqual(1);
        await expect(page.locator('#stc-det-info')).toContainText('WPC-001');
        await page.screenshot({ path: path.join(OUT, '02-detail.png'), fullPage: true });

        await page.locator('#stc-back').click();
        await expect(page.locator('#stc-view-list')).toBeVisible();

        // ── ③ 未入账清单 tab(懒加载 + 三枚举 reason)──
        await page.locator('#stc-tab-excluded').click();
        await expect(page.locator('#stc-view-excluded')).toBeVisible();
        await expect(page.locator('#stc-tbl-excluded tbody tr')).toHaveCount(3);
        await expect(page.locator('#stc-tbl-excluded')).toContainText('服务票');
        await expect(page.locator('#stc-tbl-excluded')).toContainText('汇总票');
        await expect(page.locator('#stc-tbl-excluded')).toContainText('无数量/单价');
        await page.screenshot({ path: path.join(OUT, '03-excluded.png'), fullPage: true });
        await page.locator('#stc-tab-report').click();

        // ── ④ 期初库存弹窗(按当前商品列表铺行 · 行身份双轨)──
        await page.locator('#stc-btn-opening').click();
        await expect(page.locator('#stc-op-mask')).toBeVisible();
        await expect(page.locator('#stc-op-tbl tr[data-op-key]')).toHaveCount(4);
        // 回归锁(2026-08-08):期初预填只认 GET /openings 的已存用户期初(空桩 → 全空),
        // 不预填 product.opening_qty —— 那是计算结转(-30),不是用户手填的期初。
        await expect(
            page.locator('tr[data-op-key="p:WTR-600"] [data-op-qty]'),
            '计算结转的 opening_qty 不进期初弹窗预填'
        ).toHaveValue('');
        // .modal 有 200ms 进场动画(home-05-overlays.css modalIn:透明度+缩放一起变)·
        // 截图撞在动画中途会拍到一帧半透明/未缩放到位的过渡态,看着像背景"漏"上来,
        // 实测等动画放完再截就是干净的一张,不是页面坏了。
        await page.waitForTimeout(300);
        await page.screenshot({ path: path.join(OUT, '04-opening-modal.png'), fullPage: false });
        // 填一条商品档轨 + 一条名字轨,保存后断言出站契约:workspace_client_id 走 query,
        // 行身份按轨发 product_id / name —— 名字轨发假 pid、workspace 塞 body 是
        // 2026-08-08 修掉的真断裂(上线以来这条写路径从没成功过)。
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

        // ── ⑤ 泰语切换:期望值现场从页面里的 window.I18N.th 真词典取,不自带副本 ──
        await page.evaluate(() => window.applyLang('th'));
        const thExpect = await page.evaluate(() => ({
            title: window.I18N.th['stc-title'],
            colIn: window.I18N.th['stc-col-in'],
            tabExcluded: window.I18N.th['stc-tab-excluded'],
        }));
        await expect(page.locator('.stc-head .t')).toHaveText(thExpect.title);
        await expect(page.locator('.stc thead th.stc-g-in').first()).toContainText(thExpect.colIn);
        await expect(page.locator('#stc-tab-excluded')).toContainText(thExpect.tabExcluded);
        // 回归锁:shellHtml() 整壳重渲模板里角标是写死的占位「0」,真跑一次复现过切语言后
        // 徽章从 3 被顶回 0(数据仍在,只是没在切语言这条路上重新贴回去)。
        await expect(page.locator('#stc-excluded-cnt'), '切语言后角标计数不丢').toHaveText('3');
        await page.screenshot({ path: path.join(OUT, '05-thai.png'), fullPage: true });
        await page.evaluate(() => window.applyLang('zh'));

        // ── ⑥ 归并弹窗:默认只勾入口行 + 名字轨目标代建的出站契约 ──
        await page.locator('[data-stc-merge]').first().click();
        await expect(page.locator('#stc-mg-mask')).toBeVisible();
        const mgCbs = page.locator('[data-mg-cb]');
        await expect(mgCbs).toHaveCount(2);
        await expect(mgCbs.nth(0), '入口行自己默认勾上').toBeChecked();
        await expect(mgCbs.nth(1), '其他名字默认不勾——是不是同一件货由会计定').not.toBeChecked();
        // 目标下拉 value 用归组钥匙 key(名字轨 product_id 恒空,拿它当 value 从没成功过);
        // 顺序 = 入口行 → 已建档商品 → 其余名字轨。
        const optVals = await page
            .locator('#stc-mg-target option')
            .evaluateAll((os) => os.map((o) => o.value));
        expect(optVals).toEqual(['n:กระดาษ a4', 'p:WPC-001', 'p:WTR-600', 'n:กระดาษ เอ4']);
        await mgCbs.nth(1).check();
        await page.waitForTimeout(300);
        await page.screenshot({ path: path.join(OUT, '06-merge-modal.png'), fullPage: false });
        await page.locator('#stc-mg-confirm').click();
        await expect(page.locator('#stc-mg-mask')).toBeHidden();
        expect(captures.merge.search).toContain('workspace_client_id=1');
        expect(captures.merge.body).toEqual({
            name_keys: ['กระดาษ a4', 'กระดาษ เอ4'],
            new_product_name: 'กระดาษ A4',
            unit: 'รีม',
        });

        assertNoConsoleErrors(expect, guard);
    });

    test('手机视口(390×844)· 工具栏竖排 + 表格容器独立横滚', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await blockCfInsights(page);
        await page.addInitScript(() => {
            localStorage.setItem('mrpilot_token', 'e2e-stock-card-token-mobile');
        });
        await stubApi(page);
        await page.goto('/home#/stock-card');
        await page.waitForFunction(() => typeof window.loadStockCard === 'function');
        await neutralizeWorkspaceGate(page);
        await page.evaluate(() => window.routeTo('stock-card'));
        await expect(page.locator('.stc-row')).toHaveCount(4);

        // 页面本体不得横向溢出(响应式硬规)· 表格容器自己横滚。
        const bodyOverflow = await page.evaluate(
            () => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1
        );
        expect(bodyOverflow, '页面本体不横向溢出').toBe(true);
        const scrollOverflowX = await page
            .locator('.stc-scroll')
            .first()
            .evaluate((el) => getComputedStyle(el).overflowX);
        expect(scrollOverflowX).toBe('auto');
        const toolbarDir = await page
            .locator('.stc-toolbar')
            .evaluate((el) => getComputedStyle(el).flexDirection);
        expect(toolbarDir, '≤800px 工具栏竖排').toBe('column');

        await page.screenshot({ path: path.join(OUT, '06-mobile.png'), fullPage: true });
    });
});
