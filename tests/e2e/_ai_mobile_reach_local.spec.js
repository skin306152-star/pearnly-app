// /ai 手机端「够得着」四条(390×844)· 本地真浏览器验收 —— 跑 static/dist 真构建产物
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**(同
// _board_tools_local.spec.js 先例)。四条都来自 2026-07-30 四语双端视觉走查的实测:
//   ① /pool 整页横向滚 18px —— 顶出去的是超长文件名那两个 span.riq-item-file;
//   ② 文件名显示的是落盘存储键(<uuid>__IMG_2485.jpg),会计认不出是哪张票;
//   ③ /pool 上「复核通过 / 签批冻结 / 驳回」实测 30×254,手机上按不准;
//   ④ 客户页 tab 条第 5 个默认在屏外,深链直接落在它上面时当前项自己就被切掉。
// 量的都是画出来的框(boundingBox / getComputedStyle / scrollLeft),不看 class 名。
// 截图存 tests/e2e/_artifacts/ai_mobile_reach/,每条先拍再断言 —— 红的那一跑也留得下图。
//
// 起法:npx playwright test tests/e2e/_ai_mobile_reach_local.spec.js
/* global window, document, getComputedStyle */

const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8994;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'ai_mobile_reach');
const PHONE = { width: 390, height: 844 };

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT);
});

test.afterAll(() => localServer.stop(server));

// 落盘名格式抄自 services/workorder/storage.py:save_material —— `{uuid4().hex}__{词干}{ext}`,
// 词干经 _safe_stem 清洗后限长 60。三件覆盖三种边界:带 hash 前缀的普通名 / 带 hash 前缀的
// 顶格长名(剥完仍然长,靠 ellipsis 收)/ 用户原名里本来就有双下划线(不许被当前缀剥掉)。
const HASHED_NAME = 'IMG_2485.jpg';
const HASHED_REF = `/opt/mrpilot/storage/workorders/b2000000/wo-1/materials/3ccdcc7a71104c1b89d6eb9b75915366__${HASHED_NAME}`;
const LONG_STEM = 'ใบกำกับภาษีซื้อ_บริษัทสยามพัฒนาจำกัดมหาชน_สาขาสำนักงานใหญ่_2569';
const LONG_NAME = `${LONG_STEM}.pdf`;
const LONG_REF = `/opt/mrpilot/storage/workorders/b2000000/wo-1/materials/01dabb77d5594164900e4c58f6e7a846__${LONG_NAME}`;
const USER_UNDERSCORE_NAME = 'MAY__RECEIPT_07.jpg';
const USER_UNDERSCORE_REF = `/opt/mrpilot/storage/workorders/b2000000/wo-1/materials/${USER_UNDERSCORE_NAME}`;

const OCR_READ = {
    seller_tax: '0105500000001',
    subtotal: '1000.00',
    vat: '70.00',
    total_amount: '1070.00',
    invoice_number: 'IN26-00675',
    invoice_date: '2026-04-21',
};

// services/workorder/verdict.py:hint('ocr_low_confidence:needs_review') 的真回值。
const VERDICT_HINT = {
    narrative_key: 'verdict_ocr_low_conf',
    params: { band: 'needs_review' },
    confidence: 'low',
    severity: 'warn',
    suggested_decision: null,
};

// services/workorder/evidence.py:flagged_projection() + review_feed.enrich() 逐键。
function flaggedItem(itemId, fileRef) {
    return {
        item_id: itemId,
        file_ref: fileRef,
        kind: 'purchase_invoice',
        flag_reason: 'ocr_low_confidence:needs_review',
        ocr_read: OCR_READ,
        decision: null,
        verdict_hint: VERDICT_HINT,
        work_order_id: 'wo-1',
        client_name: 'บริษัท สยามพัฒนา จำกัด',
        period: '2569-07',
    };
}

// services/workorder/review.py:review_queue() 逐键。sod=null → 三个签批钮全出(不走 proactive
// 收起),这正是要量触控目标的那一屏。
const QUEUE = {
    period: '2569-07',
    clients: [
        {
            workspace_client_id: 9,
            client_name: 'บริษัท สยามพัฒนา จำกัด',
            client_tax_id: '0105500000001',
            orders: [
                {
                    work_order_id: 'wo-1',
                    workspace_client_id: 9,
                    client_name: 'บริษัท สยามพัฒนา จำกัด',
                    client_tax_id: '0105500000001',
                    period: '2569-07',
                    status: 'review',
                    current_step: 'reconcile',
                    updated_at: '2026-07-30T02:00:00Z',
                    next_due_efiling: '2599-12-31',
                    next_due_paper: null,
                    pool_pending: 0,
                    is_rework: false,
                    flagged_groups: [
                        {
                            flag_reason: 'ocr_low_confidence:needs_review',
                            severity: 'warn',
                            count: 3,
                            decided_count: 0,
                            undecided_count: 3,
                        },
                    ],
                    flagged_total: 3,
                    top_severity: 'warn',
                    sod: null,
                    // sod.signoff_projection() 从没签过就是 None(不是 {signed:false} ——
                    // 那个形状会被 signoffMode 判成「已复核」,三个钮里少一个)。
                    signoff: null,
                },
            ],
        },
    ],
    flagged_items: [
        flaggedItem('it-1', HASHED_REF),
        flaggedItem('it-2', LONG_REF),
        flaggedItem('it-3', USER_UNDERSCORE_REF),
    ],
    counts: { clients: 1, orders: 1, flagged: 3 },
};

const CLIENT = { id: 9, name: 'บริษัท สยามพัฒนา จำกัด', tax_id: '0105500000001' };

function json(body) {
    return { contentType: 'application/json', body: JSON.stringify(body) };
}

async function boot(page, hash, lang = 'zh') {
    await page.setViewportSize(PHONE);
    // 一个 handler 分发全部 /api/**(Playwright 路由后注册先匹配,拆多条再加兜底会互相盖掉)。
    await page.route('**/api/**', (r) => {
        const url = r.request().url();
        if (url.includes('/api/workorder/review-queue')) return r.fulfill(json(QUEUE));
        if (url.includes('/api/workspace/clients/9')) return r.fulfill(json({ client: CLIENT }));
        if (url.includes('/api/workorder/orders')) return r.fulfill(json({ orders: [] }));
        if (url.includes('/api/me')) return r.fulfill(json({ username: 'skin' }));
        return r.fulfill(json({}));
    });
    await page.addInitScript(
        ([l]) => {
            window.localStorage.setItem('mrpilot_token_ai', 'tok-reach');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [lang]
    );
    await page.goto(`${BASE}/static/dist/ai.html#${hash}`);
}

function shot(page, name) {
    return page.screenshot({ path: path.join(ARTIFACT_DIR, name), fullPage: true });
}

// documentElement 的横向溢出(页面本体真能左右拖的像素数)。
function docOverflow(page) {
    return page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth
    );
}

test.describe('/pool 手机端', () => {
    test('页面本体零横向滚 · 文件名不越出视口', async ({ page }) => {
        await boot(page, '/pool');
        await page.waitForSelector('.riq-item-file', { state: 'visible', timeout: 15000 });
        await shot(page, '01-pool-zh-mobile390.png');

        expect(await docOverflow(page)).toBeLessThanOrEqual(1);
        // 逐个文件名量右边界:只断整页不溢出会漏掉「元素越界但祖先 overflow 藏起来了」。
        const rights = await page.locator('.riq-item-file').evaluateAll((els) =>
            els.map((el) => {
                const b = el.getBoundingClientRect();
                return { right: b.right, width: b.width };
            })
        );
        expect(rights.length).toBe(3);
        for (const r of rights) expect(r.right).toBeLessThanOrEqual(PHONE.width);
    });

    test('文件名是人看的名字:剥掉落盘 hash 前缀,长名 ellipsis + title 留全名', async ({ page }) => {
        await boot(page, '/pool');
        await page.waitForSelector('.riq-item-file', { state: 'visible', timeout: 15000 });
        const names = await page.locator('.riq-item-file').allInnerTexts();
        expect(names).toEqual([HASHED_NAME, LONG_NAME, USER_UNDERSCORE_NAME]);
        // 反面:hash 一个字符都不许留在人眼前。
        for (const n of names) expect(n).not.toContain('3ccdcc7a71104c1b89d6eb9b75915366');

        // 剥短了不等于永远不溢出:长名仍要靠 ellipsis 收口,全名挂 title 供悬停。
        const long = page.locator('.riq-item-file').nth(1);
        const css = await long.evaluate((el) => {
            const s = getComputedStyle(el);
            return { overflow: s.overflow, textOverflow: s.textOverflow, whiteSpace: s.whiteSpace };
        });
        expect(css.textOverflow).toBe('ellipsis');
        expect(css.overflow).toBe('hidden');
        expect(css.whiteSpace).toBe('nowrap');
        expect(await long.getAttribute('title')).toBe(LONG_NAME);
        // 真被裁了才算 ellipsis 有活干(否则这条断言在窄名上永远绿)。
        const clipped = await long.evaluate((el) => el.scrollWidth > el.clientWidth);
        expect(clipped).toBe(true);
    });

    test('复核通过 / 签批冻结 / 驳回 三个动作触控目标 ≥44px', async ({ page }) => {
        await boot(page, '/pool');
        await page.waitForSelector('.riq-wo-steps .btn', { state: 'visible', timeout: 15000 });
        await shot(page, '02-pool-signoff-buttons-mobile390.png');

        const btns = page.locator('.riq-wo-steps .btn');
        await expect(btns).toHaveCount(3);
        // 两件事分开验(同 _f1_steward_attach_local.spec.js:564 口径):①「设计上就是 44」看
        // CSS 意图,②「实际没被挤扁」看画出来的框。框要取整再比 —— headless 下 flex 行的
        // cross size 会落在分数上(本仓实测量到过 43.999969),拿浮点直接比 44 会随机红。
        const minHeights = await btns.evaluateAll((els) =>
            els.map((el) => getComputedStyle(el).minHeight)
        );
        expect(minHeights).toEqual(['44px', '44px', '44px']);
        const boxes = await btns.evaluateAll((els) =>
            els.map((el) => {
                const b = el.getBoundingClientRect();
                return { w: b.width, h: b.height };
            })
        );
        for (const b of boxes) {
            expect(Math.round(b.h)).toBeGreaterThanOrEqual(44);
            expect(Math.round(b.w)).toBeGreaterThanOrEqual(44);
        }
    });
});

// 当前 tab 相对 tab 条可视区的位置(负 = 被左边切掉,正 = 被右边切掉)。
function tabClip(page) {
    return page.evaluate(() => {
        const bar = document.getElementById('clientTabs');
        const btn = bar.querySelector('button.on');
        const bb = bar.getBoundingClientRect();
        const tb = btn.getBoundingClientRect();
        return {
            leftClip: bb.left - tb.left,
            rightClip: tb.right - bb.right,
            scrollLeft: bar.scrollLeft,
            scrollWidth: bar.scrollWidth,
            clientWidth: bar.clientWidth,
            label: btn.innerText.trim(),
            classes: bar.className,
            pageScrollY: window.scrollY,
        };
    });
}

test.describe('/ai 客户页 tab 条(390)', () => {
    test('深链落在最后一个 tab:进页面就把它滚进可视区 · 不动整页滚动位置', async ({ page }) => {
        await boot(page, '/client/9/profile');
        await page.waitForSelector('#v-client.on', { state: 'visible', timeout: 15000 });
        await shot(page, '03-ctabs-last-tab-mobile390.png');

        const m = await tabClip(page);
        // 前提:390 下这条 tab 条确实溢出(不溢出的话下面几条断言没有判别力)。
        expect(m.scrollWidth).toBeGreaterThan(m.clientWidth);
        expect(m.leftClip).toBeLessThanOrEqual(0);
        expect(m.rightClip).toBeLessThanOrEqual(0);
        // 滚的是 tab 条自己,不是整页(scrollIntoView 会把页面一起带跑)。
        expect(m.pageScrollY).toBe(0);
        // 左边还有没露头的 tab → 左缘提示在,右缘不该再画(已经滚到底)。
        expect(m.classes).toContain('tabs-more-l');
        expect(m.classes).not.toContain('tabs-more-r');
    });

    test('切回第一个 tab:滚回左端 · 右缘提示跟着翻过来', async ({ page }) => {
        await boot(page, '/client/9/profile');
        await page.waitForSelector('#v-client.on', { state: 'visible', timeout: 15000 });
        await page.locator('#tabIntake').click();
        // 等重画完,不等 hash —— hash 是点击回调里同步写的,hashchange 派发前它就已经变了,
        // 拿它当信号量到的是上一屏(实测偶发红:当前项还是「画像」)。
        await expect(page.locator('#tabIntake')).toHaveClass(/\bon\b/);

        const m = await tabClip(page);
        expect(m.leftClip).toBeLessThanOrEqual(0);
        expect(m.rightClip).toBeLessThanOrEqual(0);
        expect(m.scrollLeft).toBe(0);
        expect(m.classes).toContain('tabs-more-r');
        expect(m.classes).not.toContain('tabs-more-l');
        await shot(page, '04-ctabs-first-tab-mobile390.png');
    });

    test('泰语深链交付包 tab:当前项一样完整可见', async ({ page }) => {
        await boot(page, '/client/9/pkg', 'th');
        await page.waitForSelector('#v-client.on', { state: 'visible', timeout: 15000 });
        await shot(page, '05-ctabs-pkg-th-mobile390.png');

        const m = await tabClip(page);
        expect(m.scrollWidth).toBeGreaterThan(m.clientWidth);
        expect(m.leftClip).toBeLessThanOrEqual(0);
        expect(m.rightClip).toBeLessThanOrEqual(0);
        expect(m.pageScrollY).toBe(0);
    });
});
