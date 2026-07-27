// /ai 空态出路(缺口 3/4)· 本地真浏览器验收(跑 static/dist 真构建产物)
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**(同
// _b1_states_local.spec.js 先例)。断言的每个选择器/文案都来自真实产物
// (ai-state.js / ai-client-wo-render.js / ai-recon-render.js / ai-i18n-empty.js),
// 不是脚本自己造出来的对象。截图存 tests/e2e/_artifacts/empty_states/。
//
// 起法:npx playwright test tests/e2e/_empty_states_local.spec.js
/* global window, document, getComputedStyle */

const { test, expect } = require('@playwright/test');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const ROOT = path.resolve(__dirname, '..', '..');
const PORT = 8991;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'empty_states');

let server;

function waitUp(url, tries = 40) {
    return new Promise((resolve, reject) => {
        const hit = (n) => {
            http.get(url, (r) => {
                r.resume();
                resolve();
            }).on('error', () => {
                if (n <= 0) return reject(new Error('server not up'));
                setTimeout(() => hit(n - 1), 150);
            });
        };
        hit(tries);
    });
}

test.beforeAll(async () => {
    server = spawn('python', ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1'], {
        cwd: ROOT,
        stdio: 'ignore',
    });
    await waitUp(`${BASE}/static/dist/ai.html`);
});

test.afterAll(() => {
    if (server) server.kill();
});

const CLIENT = { id: 9, name: 'ร้านทดสอบ', tax_id: '0105500000001' };

function json(body) {
    return { contentType: 'application/json', body: JSON.stringify(body) };
}

// orders=[] 走「本客户一张工单都没有」;给了 detail 则走单张工单的工单页。
async function boot(page, { lang = 'zh', orders = [], detail = null, hash }) {
    await page.route('**/api/me**', (r) => r.fulfill(json({ username: 'skin' })));
    await page.route('**/api/workspace/clients/9**', (r) => r.fulfill(json(CLIENT)));
    await page.route('**/api/workorder/orders**', (r) => {
        const url = r.request().url();
        const m = url.match(/\/api\/workorder\/orders\/([^/?]+)/);
        if (m && detail) return r.fulfill(json(detail));
        return r.fulfill(json({ orders }));
    });
    await page.route('**/api/**', (r) => {
        const url = r.request().url();
        if (url.includes('/api/me') || url.includes('/api/workorder/orders')) return r.fallback();
        if (url.includes('/api/workspace/clients/9')) return r.fallback();
        return r.fulfill(json({}));
    });
    await page.addInitScript(
        ([l]) => {
            window.localStorage.setItem('mrpilot_token_ai', 'tok-empty');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [lang]
    );
    await page.goto(`${BASE}/static/dist/ai.html#${hash}`);
    await page.waitForSelector('#v-client.on', { state: 'visible', timeout: 15000 });
}

// 真跑到 reconcile 才有的四清单载荷。lists 为空对象 = 四张单全空(没料可对)。
function orderDetail(over) {
    return Object.assign(
        {
            id: 'wo-1',
            period: '2569-05',
            status: 'review',
            numbers: {},
            flagged: [],
            excluded: [],
            alerts: [],
            needs: [],
            blocked_reasons: [],
            machine_actions: [],
            deliverables: [],
            bank_recon: {
                auto_matched: [],
                review: [],
                missing_invoice: [],
                unmatched_invoice: [],
                bank_item_ids: [],
                diff: { net: '0' },
            },
            shadow_draft: null,
            financials: null,
        },
        over
    );
}

test.describe('缺口 3 · 审核/交付包无工单空态点名去哪 + 给按钮', () => {
    for (const tab of ['review', 'pkg']) {
        test(`${tab} tab:文案点名「工单」· 按钮真跳工单 tab`, async ({ page }) => {
            await boot(page, { hash: `/client/9/${tab}` });
            const block = page.locator(`#cv-${tab} .state-block`);
            await expect(block).toBeVisible();
            // 点名:副文案里必须真出现 tab 名,不是含糊的「其它入口」。
            await expect(block.locator('.s')).toContainText('「工单」tab');
            await expect(block.locator('.s')).not.toContainText('其它入口');
            // 给按钮:不是纯文字,是能点的链接按钮,且指向本客户的工单 tab。
            const btn = block.locator('a.btn');
            await expect(btn).toBeVisible();
            expect(await btn.getAttribute('href')).toBe('#/client/9/wo');
            await page.screenshot({
                path: path.join(ARTIFACT_DIR, `01-${tab}-no-order-zh.png`),
                fullPage: true,
            });
            await btn.click();
            await page.waitForSelector('#cv-wo.on', { state: 'visible', timeout: 10000 });
            expect(page.url()).toContain('#/client/9/wo');
        });
    }

    test('泰语同样点名 tab 名(zh+th 两语都真出文案,不落 key 字面量)', async ({ page }) => {
        await boot(page, { lang: 'th', hash: '/client/9/review' });
        const sub = page.locator('#cv-review .state-block .s');
        await expect(sub).toContainText('«งาน»');
        await expect(sub).not.toContainText('emp_wo_none');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '02-review-no-order-th.png'),
            fullPage: true,
        });
    });
});

test.describe('缺口 4 · 页内小分区空态三态可分辨', () => {
    const ORDERS = [{ id: 'wo-1', period: '2569-05', status: 'review' }];

    test('没料可对 → idle:说清为什么空 + 给去收料的按钮', async ({ page }) => {
        await boot(page, { hash: '/client/9/wo', orders: ORDERS, detail: orderDetail() });
        // 四张单全空时整块面板只出一个空态(不按子清单各喊一遍)——这里顺带锁住"只有一个"。
        const empty = page.locator('#brxRoot .sec-empty');
        await expect(empty).toHaveCount(1);
        expect(await page.locator('#brxRoot .brx-section').count()).toBe(0);
        await expect(empty).toBeVisible();
        expect(await empty.getAttribute('data-state')).toBe('idle');
        await expect(empty.locator('.sec-empty-t')).toContainText('没有可对账的东西');
        // 「为什么空」必须真有一句,不是干瘪标题。
        const why = await empty.locator('.sec-empty-s').innerText();
        expect(why.length).toBeGreaterThan(20);
        const out = empty.locator('.sec-empty-a a.btn');
        expect(await out.getAttribute('href')).toBe('#/client/9/intake');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '03-recon-idle-zh.png'),
            fullPage: true,
        });
    });

    test('跑完真没有这一类 → empty:与 idle 的 data-state 和左色条都不同', async ({ page }) => {
        // 有一张单有行 → 其余单的空是真结论(empty),不再是「没料」。
        const detail = orderDetail();
        detail.bank_recon.unmatched_invoice = [
            { vendor: 'A', invoice_no: 'INV-1', amount: '100', candidate_id: 'c1' },
        ];
        await boot(page, { hash: '/client/9/wo', orders: ORDERS, detail });
        const miss = page.locator('#brxRoot [data-brx-kind="missing"] .sec-empty');
        await expect(miss).toBeVisible();
        expect(await miss.getAttribute('data-state')).toBe('empty');
        await expect(miss.locator('.sec-empty-s')).toContainText('对应票据');
        // 三态靠左侧色条区分——真取计算样式,不看类名就当数(CSS 属性生效≠效果生效)。
        const emptyBar = await miss.evaluate((el) => getComputedStyle(el).borderLeftColor);
        const idleBar = await page.evaluate(() => {
            const d = document.createElement('div');
            d.className = 'sec-empty sec-empty-idle';
            document.body.appendChild(d);
            const c = getComputedStyle(d).borderLeftColor;
            d.remove();
            return c;
        });
        expect(emptyBar).not.toBe(idleBar);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '04-recon-empty-zh.png'),
            fullPage: true,
        });
    });

    test('后台停住了 → error:改口说没跑出来 + 给断点重试', async ({ page }) => {
        const detail = orderDetail({
            status: 'stuck',
            blocked_reasons: ['ocr_timeout'],
            bank_recon: null,
            shadow_draft: null,
        });
        await boot(page, { hash: '/client/9/wo', orders: ORDERS, detail });
        const brx = page.locator('#brxRoot .sec-empty');
        await expect(brx).toBeVisible();
        expect(await brx.getAttribute('data-state')).toBe('error');
        await expect(brx.locator('.sec-empty-t')).toContainText('没跑出来');
        // 卡死时绝不能再说「不用管它,会自动生成」——那是假话。
        await expect(page.locator('#brxRoot')).not.toContainText('不用管它');
        const retry = brx.locator('button[data-action="wo-retry-stuck"]');
        await expect(retry).toBeVisible();
        // 影子底稿区同样改口。
        const sdw = page.locator('#shadowRoot .sec-empty');
        expect(await sdw.getAttribute('data-state')).toBe('error');
        await expect(page.locator('#shadowRoot')).not.toContainText('不用管它');
        // 三块面板在同一屏上下叠着,口径必须一致——报表包也不许再说「不用管它」。
        const fin = page.locator('#financialsRoot .sec-empty');
        expect(await fin.getAttribute('data-state')).toBe('error');
        await expect(page.locator('#financialsRoot')).not.toContainText('不用管它');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '05-recon-shadow-error-zh.png'),
            fullPage: true,
        });
    });
});
