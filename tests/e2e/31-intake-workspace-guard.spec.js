// Pearnly E2E · 31 录入工作台复核屏「套账不符」非阻断横幅(检测 + 一键归入 + 保持)
// ============================================================
// 桩路数照 30-intake-convert.spec.js:token 塞 localStorage → page.route 拦 /api/** 桩契约
// 信封,本地静态服务(不连真库/真 OCR)。验的是前端检测与动作接线:横幅出现/形态、
// 建套账+归入 / 切已有套账并归入 的请求载荷、错配文件不进「确认全部」。
//
// 覆盖:
//   ① 形态2:当前套账税号 ≠ 票主税号且无匹配 → 横幅 + [建套账并归入] →
//     POST /api/workspace/clients {name,tax_id} + POST /api/workspace/rebind-history → 横幅消失
//   ② 形态1:票主税号命中我的另一套账 → 按钮是「切到…并归入」→ 只发 rebind(无 create)
//   ③ 校验位坏的税号(改末位)→ 无横幅
//   ④ 错配未处理时点「确认全部」→ convert 请求不含错配文件;点[保持当前]后再确认 → 包含
// ============================================================
/* global window, document, getComputedStyle */

const path = require('path');
const fs = require('fs');
const { test, expect } = require('@playwright/test');
const localServer = require('./_local_static_server');

const PORT = 8980;
const BASE = `http://127.0.0.1:${PORT}`;
const OUT = path.join(__dirname, '_artifacts', 'intake-workspace-guard');
fs.mkdirSync(OUT, { recursive: true });

// 当前套账 = 冰块公司(id 1 · 税号 0105546015062);票主 = 美妆店(税号 0105567178203)
const CURRENT_WS_TAX = '0105546015062';
const PARTY_TAX = '0105567178203';

// 只有当前一个套账(无匹配)→ 形态2(建档)
const CLIENTS_SINGLE = {
    clients: [{ id: 1, name: '冰块公司 Ice Co', tax_id: CURRENT_WS_TAX }],
    count: 1,
};
// 已有美妆店套账(id 2 · 税号 = 票主税号)→ 形态1(切换)
const CLIENTS_WITH_MATCH = {
    clients: [
        { id: 1, name: '冰块公司 Ice Co', tax_id: CURRENT_WS_TAX },
        { id: 2, name: '美妆店 Makeup Shop', tax_id: PARTY_TAX },
    ],
    count: 2,
};

// 美妆店销项票(方向 sales · 票主 = 卖方)· 买方税号填了 → passable(不标需确认)
function recognSales(sellerTax, historyId, filename) {
    return {
        ok: true,
        filename,
        page_count: 1,
        history_id: historyId,
        history_ids: [historyId],
        invoice_count: 1,
        confidence: 'high',
        needs_review: false,
        missed_invoice_warnings: [],
        duplicate_warnings: [],
        pages: [{ fields: {} }],
        invoices: [
            {
                history_id: historyId,
                source_index: 1,
                source_total: 1,
                page_indices: [1],
                fields: {
                    direction: 'sales',
                    seller_name: '美妆店 Makeup Shop',
                    seller_tax: sellerTax,
                    invoice_number: 'INV-' + historyId,
                    date: '2026-08-08',
                    subtotal: '100',
                    vat: '7',
                    total_amount: '107',
                    buyer_name: 'Walk-in Buyer',
                    buyer_tax: '0105561234563',
                    items: [{ name: 'Lipstick', qty: '1', price: '107' }],
                },
            },
        ],
    };
}
const RECOG_MISMATCH = recognSales(PARTY_TAX, 'h1', 'makeup-invoice.pdf');
const RECOG_NORMAL = recognSales(CURRENT_WS_TAX, 'h2', 'normal-invoice.pdf');
// 校验位坏:0105567178203 末位 3 → 4(应过不了 MOD-11)
const RECOG_BAD_CHECK = recognSales('0105567178204', 'h1', 'bad-check.pdf');

let server;
test.beforeAll(async () => {
    server = await localServer.start(PORT, '/home.html');
});
test.afterAll(() => localServer.stop(server));

let createCalls = [];
let rebindCalls = [];
let convertCalls = [];

// 桩 /api/** 契约信封。clients:GET 列表;recognTwo:第二份识别响应(按上传文件名分流)。
async function stub(page, opts) {
    createCalls = [];
    rebindCalls = [];
    convertCalls = [];
    const { clients, recogn, recognTwo } = opts || {};
    await page.route('**/api/**', async (route) => {
        const req = route.request();
        const u = req.url();
        const m = req.method();
        if (u.includes('/api/workspace/clients') && m === 'GET') {
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(clients || CLIENTS_SINGLE),
            });
        }
        if (u.includes('/api/workspace/clients') && m === 'POST') {
            createCalls.push(JSON.parse(req.postData() || '{}'));
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ ok: true, id: 99 }),
            });
        }
        if (u.includes('/api/workspace/rebind-history')) {
            rebindCalls.push(JSON.parse(req.postData() || '{}'));
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ ok: true, rebound: 1, skipped: [] }),
            });
        }
        if (u.includes('/api/ocr/recognize')) {
            const body = req.postData() || '';
            const payload = recognTwo
                ? body.includes('normal-invoice.pdf')
                    ? recognTwo
                    : recogn
                : recogn;
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(payload || RECOG_MISMATCH),
            });
        }
        if (u.includes('/api/ocr/convert-documents')) {
            const payload = JSON.parse(req.postData() || '{}');
            convertCalls.push(payload);
            const ids = payload.history_ids || [];
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    converted: ids.map((id) => ({
                        history_id: id,
                        doc_type: 'purchase',
                        doc_id: 'doc-' + id,
                        doc_no: 'D-' + id,
                    })),
                    skipped: [],
                }),
            });
        }
        if (u.includes('/api/erp/endpoints')) {
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ items: [] }),
            });
        }
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true }),
        });
    });
}

async function boot(page, opts) {
    await page.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'e2e-intake-wsguard-token');
        localStorage.setItem('mrpilot_lang', 'zh');
        // Keep static home.html tests on the internal full shell.
        localStorage.setItem('pearnly_entry', 'firm');
    });
    await stub(page, opts);
    await page.goto(`${BASE}/home.html`, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof window.routeTo === 'function', { timeout: 20000 });
    await page.evaluate(() => {
        window.isOwner = () => true;
        window.getActiveWorkspaceClientId = () => 1; // 当前套账恒为 id 1
        document.body.classList.remove('workspace-gate-preboot');
        document.getElementById('workspace-gate-root')?.remove();
        const st = document.createElement('style');
        st.textContent =
            '#ws-modal{display:none!important;}#workspace-gate-root{display:none!important;}';
        document.head.appendChild(st);
        window.routeTo('dms-intake');
    });
    await page.waitForSelector('#dx-inv-drop', { timeout: 8000 });
}

async function uploadAndReview(page, files) {
    await page.setInputFiles('#dx-inv-file', files);
    await page.waitForSelector('#dx-inv-start');
    await page.click('#dx-inv-start');
    await page.waitForSelector('#dx-s-inv-review.active', { timeout: 8000 });
}

function pdfFile(name) {
    return { name, mimeType: 'application/pdf', buffer: Buffer.from('x') };
}

test.describe('复核屏「套账不符」非阻断横幅', () => {
    test('形态2:无匹配 → 建套账并归入 → 请求载荷正确 + 横幅消失', async ({ page }) => {
        await boot(page, { clients: CLIENTS_SINGLE, recogn: RECOG_MISMATCH });
        await uploadAndReview(page, [pdfFile('makeup-invoice.pdf')]);

        const banner = page.locator('.dx-wsguard');
        await expect(banner).toBeVisible();
        const disp = await banner.evaluate((el) => getComputedStyle(el).display);
        expect(disp).not.toBe('none');
        await expect(banner).toContainText('0105567178203');
        await expect(page.locator('[data-wsg-create]')).toHaveText('建套账并归入');
        await expect(page.locator('[data-wsg-switch]')).toHaveCount(0);
        // 按钮标准化(2026-08-08):确认全部/套账横幅按钮与「全部收起」同高(标准小按钮 31px)
        const hCollapse = await page
            .locator('#dx-inv-collapse-all')
            .evaluate((el) => getComputedStyle(el).height);
        const hConfirm = await page
            .locator('#dx-inv-confirm-all')
            .evaluate((el) => getComputedStyle(el).height);
        const hCreate = await page
            .locator('[data-wsg-create]')
            .evaluate((el) => getComputedStyle(el).height);
        expect(hConfirm).toBe(hCollapse);
        expect(hCreate).toBe(hCollapse);
        await page.screenshot({
            path: path.join(OUT, '01-form2-create-banner.png'),
            fullPage: true,
        });

        const rebindPromise = page.waitForResponse((r) =>
            r.url().includes('/api/workspace/rebind-history')
        );
        await page.click('[data-wsg-create]');
        await rebindPromise;

        expect(createCalls.length).toBe(1);
        expect(createCalls[0]).toEqual({ name: '美妆店 Makeup Shop', tax_id: PARTY_TAX });
        expect(rebindCalls.length).toBe(1);
        expect(rebindCalls[0].history_ids).toEqual(['h1']);
        expect(rebindCalls[0].workspace_client_id).toBe(99);
        await expect(banner).toHaveCount(0);
    });

    test('形态1:命中已有套账 → 切到并归入,只发 rebind 不发 create', async ({ page }) => {
        await boot(page, { clients: CLIENTS_WITH_MATCH, recogn: RECOG_MISMATCH });
        await uploadAndReview(page, [pdfFile('makeup-invoice.pdf')]);

        const banner = page.locator('.dx-wsguard');
        await expect(banner).toBeVisible();
        await expect(page.locator('[data-wsg-switch]')).toHaveText(
            '切到「美妆店 Makeup Shop」并归入'
        );
        await expect(page.locator('[data-wsg-create]')).toHaveCount(0);
        await page.screenshot({
            path: path.join(OUT, '02-form1-switch-banner.png'),
            fullPage: true,
        });

        const rebindPromise = page.waitForResponse((r) =>
            r.url().includes('/api/workspace/rebind-history')
        );
        await page.click('[data-wsg-switch]');
        await rebindPromise;

        expect(rebindCalls.length).toBe(1);
        expect(rebindCalls[0].history_ids).toEqual(['h1']);
        expect(rebindCalls[0].workspace_client_id).toBe(2);
        expect(createCalls.length).toBe(0);
        await expect(banner).toHaveCount(0);
    });

    test('校验位坏的税号(改末位)→ 不出现横幅', async ({ page }) => {
        await boot(page, { clients: CLIENTS_SINGLE, recogn: RECOG_BAD_CHECK });
        await uploadAndReview(page, [pdfFile('bad-check.pdf')]);

        await expect(page.locator('.dx-wsguard')).toHaveCount(0);
        await page.screenshot({
            path: path.join(OUT, '03-invalid-tax-no-banner.png'),
            fullPage: true,
        });
    });

    test('错配未处理时「确认全部」排除错配文件;保持后再确认则包含', async ({ page }) => {
        await boot(page, {
            clients: CLIENTS_SINGLE,
            recogn: RECOG_MISMATCH,
            recognTwo: RECOG_NORMAL,
        });
        await uploadAndReview(page, [pdfFile('makeup-invoice.pdf'), pdfFile('normal-invoice.pdf')]);

        const banner = page.locator('.dx-wsguard');
        await expect(banner).toBeVisible();

        // 错配未处理:确认全部 → 只确认正常的 h2,错配的 h1 被拦下
        await page.click('#dx-inv-confirm-all');
        await expect.poll(() => convertCalls.length).toBe(1);
        expect(convertCalls[0].history_ids).not.toContain('h1');
        expect(convertCalls[0].history_ids).toContain('h2');
        await expect(banner).toBeVisible(); // 错配未处理 → 横幅还在

        // [保持当前套账] → 先把草稿真实重绑到当前套账，成功后横幅才消失。
        const keepRebind = page.waitForResponse((r) =>
            r.url().includes('/api/workspace/rebind-history')
        );
        await page.click('[data-wsg-keep]');
        await keepRebind;
        await expect(banner).toHaveCount(0);
        expect(rebindCalls.at(-1).history_ids).toEqual(['h1']);
        expect(rebindCalls.at(-1).workspace_client_id).toBe(1);
        await page.click('#dx-inv-confirm-all');
        await expect.poll(() => convertCalls.length).toBe(2);
        expect(convertCalls[1].history_ids).toContain('h1');
        await page.screenshot({
            path: path.join(OUT, '04-confirm-all-filter.png'),
            fullPage: true,
        });
    });
});
