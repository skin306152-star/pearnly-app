// /ai 工作台顶部摘要行:统计 pill 不许被搜索框压住(390 四语)· 本地真浏览器验收
// ============================================================
// 2026-07-31 四语双端走查实测:390 下 en「Needs your review 1」与 th「รอคุณตัดสินใจ 1」的
// 数字整个被搜索框盖住 —— 盖掉的正好是这行唯一有信息量的部分。根因在 .toolrow 的两个
// flex 项:.sumline{flex:1;min-width:0} 允许它被压到比一颗 pill 还窄,而 .sum-pill 自己
// white-space:nowrap 压不动 —— 压不动就整颗溢出到右边,滑到 .search 底下。zh/ja 因为文案短
// 侥幸不撞,只测 zh 会漏,故本 spec 四语全跑。
//
// 判据是画出来的框(getBoundingClientRect 交集 + elementFromPoint 命中谁),不看 class 名、
// 不看 CSS 属性值 —— 「属性设了」不等于「效果对了」。
// 反证在同一份 spec 里(见「反证」describe):把 .sumline 的 min-width 用 !important 打回
// 出事前的 0,判据必须当场变红;逮不着就说明这套量法是瞎的,前面几条全绿也不算数。
//
// 跑 static/dist 真构建产物(同 _board_tools_local.spec.js 先例)· 截图存
// tests/e2e/_artifacts/ai_toolrow/。
// 起法:npx playwright test tests/e2e/_ai_toolrow_overlap_local.spec.js
/* global window, document, getComputedStyle */

const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8992;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'ai_toolrow');
const PHONE = { width: 390, height: 844 };
const DESKTOP = { width: 1280, height: 900 };
const LANGS = ['zh', 'en', 'th', 'ja'];

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT);
});

test.afterAll(() => localServer.stop(server));

const PERIOD = '2569-07';

const CLIENTS = [
    { id: 1, name: 'บริษัท เอ จำกัด' },
    { id: 2, name: 'บริษัท บี จำกัด' },
    { id: 3, name: 'บริษัท ซี จำกัด' },
];

const ORDERS = [
    { id: 'wo-2', workspace_client_id: 2, period: PERIOD, status: 'review' },
    { id: 'wo-3', workspace_client_id: 3, period: PERIOD, status: 'running' },
];

// services/workorder/review.py:review_queue() 的形状 —— pendingReviewCount 数的是这里的
// orders(status review/stuck),让「待你处理」pill 出一个非零数字(0 与 1 宽度不同)。
const QUEUE = {
    period: PERIOD,
    clients: [
        {
            workspace_client_id: 2,
            client_name: 'บริษัท บี จำกัด',
            orders: [
                {
                    work_order_id: 'wo-2',
                    workspace_client_id: 2,
                    period: PERIOD,
                    status: 'review',
                    flagged_total: 1,
                },
            ],
        },
    ],
    flagged_items: [],
    counts: { clients: 1, orders: 1, flagged: 1 },
};

const MATRIX = {
    period: PERIOD,
    clients: CLIENTS.map((c) => ({ id: c.id, name: c.name, missing_order: false })),
    obligation_codes: ['pp30'],
    obligation_labels: { pp30: { zh: '增值税', th: 'ภ.พ.30' } },
    cells: [{ client_id: 1, obligation_code: 'pp30', badge: 'pending_order' }],
};

function json(body) {
    return { contentType: 'application/json', body: JSON.stringify(body) };
}

async function boot(page, { lang = 'zh', viewport = PHONE, hash = '#/board' } = {}) {
    await page.setViewportSize(viewport);
    // 一个 handler 分发全部 /api/**(Playwright 后注册先匹配,拆多条再加兜底会互相盖掉)。
    await page.route('**/api/**', (r) => {
        const url = r.request().url();
        if (url.includes('/api/workorder/review-queue')) return r.fulfill(json(QUEUE));
        if (url.includes('/api/workorder/orders')) {
            const m = url.match(/\/api\/workorder\/orders\/([^/?]+)/);
            if (m) {
                const order = ORDERS.filter((o) => o.id === m[1])[0] || {};
                const detail = { needs: [], blocked_reasons: [], flagged: [], numbers: {} };
                return r.fulfill(json(Object.assign(detail, order)));
            }
            return r.fulfill(json({ orders: ORDERS }));
        }
        if (url.includes('/api/tax-profile/matrix')) return r.fulfill(json(MATRIX));
        if (url.includes('/api/workspace/clients')) return r.fulfill(json({ clients: CLIENTS }));
        if (url.includes('/api/me')) return r.fulfill(json({ username: 'skin' }));
        return r.fulfill(json({}));
    });
    await page.addInitScript(
        ([l]) => {
            window.localStorage.setItem('mrpilot_token_ai', 'tok-toolrow');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [lang]
    );
    await page.goto(`${BASE}/static/dist/ai.html${hash}`);
    // 统计数字落位后再量:pill 宽度随数字位数变,量在 '—' 上等于量了另一个东西。
    await page.waitForFunction(
        () => {
            const v = document.getElementById('statClientsV');
            return v && v.textContent.trim() !== '—' && v.textContent.trim() !== '';
        },
        null,
        { timeout: 15000 }
    );
}

// 量 .toolrow 里每颗可见 pill 与搜索框的交集,以及 pill 里那个数字点上到底是谁在最上层。
// 只信框与命中,不信 class:CSS 属性生效 ≠ 效果生效。
function measure(page) {
    return page.evaluate(() => {
        const row = document.querySelector('#v-dashboard .toolrow');
        const search = row.querySelector('.search');
        const sr = search.getBoundingClientRect();
        const box = (r) => [
            Math.round(r.left),
            Math.round(r.top),
            Math.round(r.width),
            Math.round(r.height),
        ];
        const pills = [];
        row.querySelectorAll('.sum-pill').forEach((p) => {
            if (getComputedStyle(p).display === 'none') return;
            const r = p.getBoundingClientRect();
            const num = p.querySelector('b.num');
            const nr = num.getBoundingClientRect();
            const hit = document.elementFromPoint(nr.left + nr.width / 2, nr.top + nr.height / 2);
            pills.push({
                text: p.innerText.trim(),
                rect: box(r),
                overlapPx: [
                    Math.round(
                        Math.max(0, Math.min(r.right, sr.right) - Math.max(r.left, sr.left))
                    ),
                    Math.round(
                        Math.max(0, Math.min(r.bottom, sr.bottom) - Math.max(r.top, sr.top))
                    ),
                ],
                numRect: box(nr),
                numCovered: !!hit && hit !== num && !num.contains(hit),
                hitBy: hit ? hit.tagName.toLowerCase() + (hit.id ? '#' + hit.id : '') : null,
            });
        });
        return {
            searchRect: box(sr),
            sumlineRect: box(row.querySelector('.sumline').getBoundingClientRect()),
            pills,
        };
    });
}

function assertNoOverlap(m, lang) {
    for (const p of m.pills) {
        const why = `${lang} · pill「${p.text}」${JSON.stringify(p.rect)} vs 搜索框 ${JSON.stringify(m.searchRect)}`;
        expect(p.overlapPx[0] * p.overlapPx[1], `${why} 相交 ${p.overlapPx.join('×')}px`).toBe(0);
        expect(p.numCovered, `${why} 数字被 ${p.hitBy} 盖住`).toBe(false);
    }
}

test.describe('390 四语:统计 pill 与搜索框不重叠', () => {
    for (const lang of LANGS) {
        test(`${lang} · 看板`, async ({ page }) => {
            await boot(page, { lang });
            const m = await measure(page);
            await page.screenshot({
                path: path.join(ARTIFACT_DIR, `toolrow-${lang}-mobile390.png`),
            });
            expect(m.pills.length, `${lang} 一颗 pill 都没量到(选择器或渲染变了)`).toBeGreaterThan(
                0
            );
            assertNoOverlap(m, lang);
        });
    }

    // 矩阵视图比看板多一颗账期 pill(sumPeriod),挤压更狠 —— en 最长,单挑它守着。
    test('en · 事务所矩阵(多一颗账期 pill)', async ({ page }) => {
        await boot(page, { lang: 'en', hash: '#/' });
        const m = await measure(page);
        await page.screenshot({ path: path.join(ARTIFACT_DIR, 'toolrow-en-matrix-mobile390.png') });
        expect(m.pills.length).toBeGreaterThanOrEqual(4);
        assertNoOverlap(m, 'en/matrix');
    });
});

test.describe('1280 桌面不许被顺手改掉', () => {
    test('摘要行与搜索框仍同一行 · 搜索框仍在右侧', async ({ page }) => {
        await boot(page, { lang: 'en', viewport: DESKTOP });
        const m = await measure(page);
        await page.screenshot({ path: path.join(ARTIFACT_DIR, 'toolrow-en-desktop1280.png') });
        const [sx, sy, , sh] = m.searchRect;
        const [lx, ly, lw, lh] = m.sumlineRect;
        // 「同一行」判的是竖直方向真有交集(两者高度不同 · align-items:center → top 天然差
        // 几像素,拿 top 差当判据是自造假红),外加搜索框整个在摘要行右边。
        const vOverlap = Math.min(sy + sh, ly + lh) - Math.max(sy, ly);
        expect(
            vOverlap,
            `搜索框 ${JSON.stringify(m.searchRect)} 与摘要行 ${JSON.stringify(m.sumlineRect)} 竖直不相交 = 掉到下一行了`
        ).toBeGreaterThan(0);
        expect(sx, `搜索框 left=${sx} 没排在摘要行右侧(${lx}+${lw})`).toBeGreaterThanOrEqual(
            lx + lw
        );
        assertNoOverlap(m, 'en/desktop');
    });
});

test.describe('反证:把判据喂毒样本,必须当场变红', () => {
    test('把两条修复逐条打回出事前的写法 → 判据逮住重叠', async ({ page }) => {
        await boot(page, { lang: 'en' });
        // 两条一起还原才是出事前那一屏:sumline 能被压到 0(nowrap 的 pill 只好整颗溢出),
        // 且搜索框不铺满(留在 min-width:220px,与摘要行挤同一行)。只还原一条不重叠 ——
        // 说明这两条各自都在干活,不是其中一条在充数。
        await page.addStyleTag({
            content:
                '.toolrow .sumline{min-width:0 !important;}.toolrow .search{width:auto !important;}',
        });
        const m = await measure(page);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, 'toolrow-en-mobile390-counterexample.png'),
        });
        const overlapped = m.pills.filter((p) => p.overlapPx[0] * p.overlapPx[1] > 0);
        expect(overlapped.length, `毒样本下一处重叠都没量到:${JSON.stringify(m)}`).toBeGreaterThan(
            0
        );
        expect(
            m.pills.some((p) => p.numCovered),
            `毒样本下没有任何数字被盖住:${JSON.stringify(m.pills)}`
        ).toBe(true);
    });
});
