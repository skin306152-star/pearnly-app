// /home 视觉走查五条缺陷的钉子(2026-07-30)· 本地真浏览器验收,跑 static/dist 真构建产物
// ============================================================
// python http.server 静态服 static/dist/home.html + page.route stub /api/**(同
// _empty_states_local.spec.js / _board_tools_local.spec.js 先例)。断言的选择器/文案全部
// 来自真实产物(src/home/{clients-seller,history-list,page-history,sales-workbench,
// purchase-settings}.ts + static/home-{07,29}*.css + static/pearnly-ui.css),没有脚本自造的对象。
// 几何一律 getBoundingClientRect/getComputedStyle,不看类名;截图存
// tests/e2e/_artifacts/home_ux_fix5/spec/。
//
// 钉住的五条(修前实测值写在各 test 的注释里):
//   1 客户管理手机端公司名列被压成 0px          → 三行卡片,公司名独占首行
//   2 识别记录后端 500 显示成空态(状态诚实)    → .pu-error + 重试真能救回来
//   3 识别记录没有载入中态(四态缺一)           → .pu-skeleton 骨架行
//   4 发票工作台手机端空态卡被推出屏外           → 空态卡出表格,按视口居中
//   5 采购设置「去费用数据 →」是浏览器默认蓝     → 复用 .pur .btn
//
// 起法:npx playwright test tests/e2e/_home_ux_fix5_local.spec.js
/* global window, document, getComputedStyle */

const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8996;
const BASE = `http://127.0.0.1:${PORT}`;
const HOME = `${BASE}/static/dist/home.html`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'home_ux_fix5', 'spec');

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT, '/static/dist/home.html');
});

test.afterAll(() => localServer.stop(server));

const json = (body, status = 200) => ({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
});

const ME = {
    username: 'ux5',
    role: 'owner',
    is_owner: true,
    can_view_history: true,
    tenant_id: 'ux5-tenant',
};

// 账套主体三家:名字长短各一,税号是真实位数的 13 位泰国税号(列宽是这条的考点)。
const SUBJECTS = [
    { id: 1, name: 'Sister Makeup Steward Co., Ltd.', tax_id: '0105567178203', invoice_count: 12 },
    { id: 2, name: 'B4 Push Co', tax_id: '0994000333444', invoice_count: 0 },
];

const HISTORY_ROWS = [
    {
        id: 'h1',
        created_at: '2026-07-30T09:00:00',
        filename: 'iv-001.pdf',
        invoice_no: 'IV69/00473',
        page_count: 1,
        total_amount: 1070,
        vat_amount: '74.9',
        status: 'confirmed',
        source: 'upload',
    },
];

const HISTORY_OK = {
    items: HISTORY_ROWS,
    total: HISTORY_ROWS.length,
    status_counts: { all: 1, confirmed: 1, pending: 0, failed: 0 },
};

// 进 /home:preboot 早于 main.js 就查 token,先 addInitScript 落 localStorage;
// 套账硬门整页 visibility:hidden,必须真点一个主体过门(摘 class 量到的"可见"是假的)。
async function boot(page, { lang = 'zh', api = {} } = {}) {
    await page.addInitScript(
        (a) => {
            localStorage.setItem('mrpilot_token', 'ux5-stub-token');
            localStorage.setItem('mrpilot_lang', a.lang);
            // Keep static home.html tests on the internal full shell.
            localStorage.setItem('pearnly_entry', 'firm');
        },
        { lang }
    );
    await page.route('**/api/**', (route) => {
        const p = new URL(route.request().url()).pathname;
        const hit = api[p];
        if (typeof hit === 'function') return hit(route);
        if (hit) return route.fulfill(json(hit));
        if (p === '/api/me') return route.fulfill(json(ME));
        if (p === '/api/workspace/clients') return route.fulfill(json({ clients: SUBJECTS }));
        return route.fulfill(json({}));
    });
    await page.goto(HOME, { waitUntil: 'domcontentloaded' });
    await page.locator('#workspace-gate-root [data-wsg-pick]').first().click();
    await expect(page.locator('#workspace-gate-root')).toHaveCount(0, { timeout: 15_000 });
    expect(await page.evaluate(() => document.body.className)).not.toContain(
        'workspace-gate-preboot'
    );
}

async function openRoute(page, route) {
    await page.evaluate((r) => {
        window.location.hash = '#/' + r;
    }, route);
    await expect(page.locator(`#page-${route}`)).toHaveClass(/active/, { timeout: 15_000 });
}

const boxOf = (loc) => loc.evaluate((el) => el.getBoundingClientRect().toJSON());

test.describe('/home 走查五条 · 修完的样子', () => {
    test('1 · 客户管理手机端:公司名独占首行,是这行最宽的东西', async ({ page }) => {
        // 修前实测:.cust-row 的 grid-template-columns = 0px 90px 50px 165px(th 180.312px),
        // .cust-cell-name 宽 0(left==right==29),公司名整列不可见。
        await page.setViewportSize({ width: 390, height: 844 });
        await boot(page, { lang: 'zh' });
        await openRoute(page, 'clients');
        const row = page.locator('.cust-row.seller-grid').first();
        await expect(row).toBeVisible();

        const name = row.locator('.cust-cell-name');
        const text = row.locator('.cust-name-text');
        const [rowBox, nameBox, taxBox] = await Promise.all([
            boxOf(row),
            boxOf(name),
            boxOf(row.locator('.cust-cell-tax')),
        ]);
        // 操作区自身是整行宽的格子(按钮靠右),比宽度要比按钮真正占的那一段
        const actsSpan = await row.locator('.cust-row-actions').evaluate((el) => {
            const kids = Array.from(el.children).map((k) => k.getBoundingClientRect());
            return Math.max(...kids.map((b) => b.right)) - Math.min(...kids.map((b) => b.left));
        });

        expect(nameBox.width, '公司名列有宽度').toBeGreaterThan(200);
        expect(nameBox.width, '公司名比几个操作按钮加起来还宽 = 它才是这行的主语').toBeGreaterThan(
            actsSpan
        );
        expect(nameBox.width, '公司名拿满行宽(减去左右内边距)').toBeGreaterThan(rowBox.width * 0.8);
        expect(nameBox.bottom, '公司名独占首行(税号在它下面一行)').toBeLessThanOrEqual(taxBox.top);

        // 文字没被 0 宽容器切掉(clientWidth 为 0 时 scrollWidth 仍有值,必须两个一起看)
        const textM = await text.evaluate((el) => ({
            clientW: el.clientWidth,
            scrollW: el.scrollWidth,
        }));
        expect(textM.clientW, '公司名可视宽度不为 0').toBeGreaterThan(0);

        // 表头在窄屏收起 → 发票数得自己带名字,否则是个没标签的裸数字
        expect(
            await page
                .locator('.cust-table-head.seller-grid')
                .evaluate((el) => getComputedStyle(el).display)
        ).toBe('none');
        await expect(row.locator('.cust-cell-count-label')).toBeVisible();

        const overflow = await page.evaluate(
            () => document.documentElement.scrollWidth - document.documentElement.clientWidth
        );
        expect(overflow, '整页不横向滚').toBeLessThanOrEqual(0);

        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '01-clients-zh-mobile390.png'),
            fullPage: true,
        });
    });

    test('2 · 识别记录后端 500:错误态 + 重试真能救回来,不是空态', async ({ page }) => {
        // 修前实测:/api/history 全 500 → 出「还没有记录 / 识别的发票会自动出现在这里」,
        // 四张 KPI 显 —,没有报错也没有重试。用户会以为自己的记录没了。
        let boom = true;
        let calls = 0;
        await boot(page, {
            lang: 'zh',
            api: {
                '/api/history': (route) => {
                    calls++;
                    return route.fulfill(boom ? json({ detail: 'boom' }, 500) : json(HISTORY_OK));
                },
            },
        });
        await openRoute(page, 'history');

        const err = page.locator('#history-error');
        await expect(err, '后端 500 → 错误态在场').toBeVisible({ timeout: 15_000 });
        await expect(page.locator('#history-empty'), '不许把失败画成空态').toBeHidden();
        const errText = await err.innerText();
        expect(errText.length, '错误态说了人话').toBeGreaterThan(6);
        expect(errText, '不许把 HTTP 码丢给会计看').not.toContain('500');
        const retry = page.locator('#history-retry');
        await expect(retry, '错误态必带出路').toBeVisible();

        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '02-history-500-zh.png'),
            fullPage: true,
        });

        // 出路得真管用:后端好了,点重试就该看见记录
        const before = calls;
        boom = false;
        await retry.click();
        await expect(page.locator('.history-row[data-hid="h1"]')).toBeVisible({ timeout: 15_000 });
        await expect(err).toBeHidden();
        expect(calls, '重试真的又打了一次接口').toBeGreaterThan(before);
    });

    test('3 · 识别记录载入中:骨架行占位,不是一片空白', async ({ page }) => {
        // 修前实测:延迟 /api/history 到 12s,2.5s 处 #history-tbody 的 innerHTML 长度 = 0,
        // 列表区整片空白(KPI 显 — 这点本来就诚实)。
        let release;
        const held = new Promise((r) => (release = r));
        await boot(page, {
            lang: 'zh',
            api: {
                '/api/history': async (route) => {
                    await held;
                    return route.fulfill(json(HISTORY_OK));
                },
            },
        });
        await openRoute(page, 'history');

        const skels = page.locator('#history-tbody .pu-skeleton');
        await expect(skels.first(), '载入中有骨架条').toBeVisible({ timeout: 10_000 });
        expect(await skels.count(), '骨架铺满几行').toBeGreaterThan(6);
        await expect(page.locator('#history-main'), '骨架长在真面板里(不跳版)').toBeVisible();
        await expect(page.locator('#history-tbody')).toHaveAttribute('aria-busy', 'true');
        // 骨架不许冒充真记录:.history-row 是「一条真记录」的语义,点击委托与 04-history.spec.js 都按它计数
        expect(await page.locator('#history-tbody .history-row').count(), '骨架不算记录行').toBe(0);
        // 骨架条用的是共享设计系统的令牌,不是这页自己调的灰
        const bg = await skels.first().evaluate((el) => getComputedStyle(el).backgroundColor);
        const token = await page.evaluate(() =>
            getComputedStyle(document.documentElement).getPropertyValue('--line2').trim()
        );
        expect(token, '--line2 令牌在场').not.toBe('');

        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '03-history-loading-zh.png'),
            fullPage: true,
        });
        expect(bg, '骨架底色不是透明').not.toBe('rgba(0, 0, 0, 0)');

        // 窄屏也得跟着真实行的堆叠栅格走(骨架那条选择器是并进原规则的,不是另抄一份模板)
        await page.setViewportSize({ width: 390, height: 844 });
        const cols = await page
            .locator('#history-tbody .hist-skel')
            .first()
            .evaluate((el) => getComputedStyle(el).gridTemplateColumns);
        expect(cols.split(' ').length, '窄屏骨架按三列堆叠排(与真实行同款)').toBe(3);
        // 这里不断言"整页不横向滚":1280 载入后 resize 到 390,壳里几个抽屉留着桌面尺寸不重排,
        // 量到的溢出是 resize 的假象(冷启 390 实测 overflow=0)。横向滚由用例 1 冷启 390 那条守。
        await page.setViewportSize({ width: 1280, height: 800 });

        release();
        await expect(page.locator('.history-row[data-hid="h1"]')).toBeVisible({ timeout: 15_000 });
        await expect(page.locator('#history-tbody .pu-skeleton')).toHaveCount(0);
    });

    test('4 · 发票工作台手机端:空态卡整张落在视口里', async ({ page }) => {
        // 修前实测:空态是 <td colspan=8>,按表格滚动宽度(min-width 640)居中 →
        // 「暂无发票」文字盒 left=49 right=621,视口只有 390,半张卡在屏外。
        await page.setViewportSize({ width: 390, height: 844 });
        await boot(page, { lang: 'zh', api: { '/api/sales/documents': { documents: [] } } });
        await openRoute(page, 'sales-invoices');

        const empty = page.locator('#sx-wb-empty');
        await expect(empty).toBeVisible({ timeout: 15_000 });
        const label = empty.locator('div').first();
        const [emptyBox, labelBox, vw] = await Promise.all([
            boxOf(empty),
            boxOf(label),
            page.evaluate(() => window.innerWidth),
        ]);
        expect(labelBox.left, '空态文案左边没出屏').toBeGreaterThanOrEqual(0);
        expect(labelBox.right, '空态文案右边没出屏').toBeLessThanOrEqual(vw);
        expect(emptyBox.left, '空态卡左边没出屏').toBeGreaterThanOrEqual(0);
        expect(emptyBox.right, '空态卡右边没出屏').toBeLessThanOrEqual(vw);
        expect(
            await empty.evaluate((el) => !!el.closest('table')),
            '空态卡不许再长在表格里(表格宽 640 > 视口)'
        ).toBe(false);
        expect(
            await page.locator('#sx-wb-tbl').evaluate((el) => getComputedStyle(el).display),
            '没有数据时表格收起 → 面板不横向滚'
        ).toBe('none');

        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '04-sales-empty-zh-mobile390.png'),
            fullPage: true,
        });
    });

    test('5 · 采购设置:「去费用数据 →」是本壳的按钮,不是浏览器默认蓝', async ({ page }) => {
        // 修前实测:class="cat-goto" 全站无人定义 → color rgb(0,0,238) + underline。
        await boot(page, {
            lang: 'zh',
            api: {
                '/api/purchase/settings': {
                    ok: true,
                    data: {
                        auto_book: true,
                        default_vat_rate: 7,
                        auto_stock_in: false,
                        dedupe_block: true,
                        default_due_days: 0,
                        default_wht_service_rate: 3,
                        pay_needs_approval: false,
                    },
                },
            },
        });
        await openRoute(page, 'purchase-settings');

        const link = page.locator('.pur.cfg a[href="#/expense-data"]');
        await expect(link).toBeVisible({ timeout: 15_000 });
        const s = await link.evaluate((el) => {
            const cs = getComputedStyle(el);
            return {
                color: cs.color,
                deco: cs.textDecorationLine,
                borderW: cs.borderTopWidth,
                radius: cs.borderTopLeftRadius,
                h: el.getBoundingClientRect().height,
            };
        });
        expect(s.color, '不许是 <a> 的浏览器默认蓝').not.toBe('rgb(0, 0, 238)');
        expect(s.deco, '不许挂浏览器默认下划线').toBe('none');
        expect(parseFloat(s.borderW), '按上了本壳的按钮描边').toBeGreaterThan(0);
        expect(parseFloat(s.radius), '按上了本壳的按钮圆角').toBeGreaterThan(0);
        expect(s.h, '点得着(与同屏控件同高)').toBeGreaterThanOrEqual(36);

        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '05-purchase-settings-zh.png'),
            fullPage: true,
        });
    });
});
