// Pearnly E2E · 31 录入工作台复核屏自动账套归属提示
// ============================================================
// 桩路数照 30-intake-convert.spec.js:token 塞 localStorage → page.route 拦 /api/** 桩契约
// 信封,本地静态服务(不连真库/真 OCR)。验的是前端信任后端最终归属、横幅只提示、
// 不再二次创建/rebind，也不从「确认全部」里排除已自动归属的文件。
//
// 覆盖:
//   ① 后端自动新建 B → 信息横幅，无动作按钮，确认继续
//   ② 后端匹配已有 B → 信息横幅，无二次 rebind
//   ③ 后端最终归属仍是当前 A → 无横幅
//   ④ 一批 A+B →「确认全部」包含两者，无创建/rebind 请求
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
function recognSales(sellerTax, historyId, filename, workspaceId, action) {
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
        workspace_attribution: {
            requested_workspace_id: 1,
            assignments: [
                {
                    history_id: historyId,
                    workspace_id: workspaceId,
                    action,
                    workspace_name: workspaceId === 1 ? '冰块公司 Ice Co' : '美妆店 Makeup Shop',
                    subject: {
                        tax_id: sellerTax,
                        name: workspaceId === 1 ? '冰块公司 Ice Co' : '美妆店 Makeup Shop',
                    },
                },
            ],
        },
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
const RECOG_MISMATCH = recognSales(PARTY_TAX, 'h1', 'makeup-invoice.pdf', 99, 'created');
const RECOG_MATCHED = recognSales(PARTY_TAX, 'h1', 'makeup-invoice.pdf', 2, 'matched');
const RECOG_NORMAL = recognSales(CURRENT_WS_TAX, 'h2', 'normal-invoice.pdf', 1, 'matched');

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
        window._entry = 'cowork';
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

test.describe('复核屏自动账套归属提示', () => {
    test('后端自动新建并归入 → 只提示且可直接确认', async ({ page }) => {
        await boot(page, { clients: CLIENTS_SINGLE, recogn: RECOG_MISMATCH });
        await uploadAndReview(page, [pdfFile('makeup-invoice.pdf')]);

        const banner = page.locator('.dx-wsguard');
        await expect(banner).toBeVisible();
        const disp = await banner.evaluate((el) => getComputedStyle(el).display);
        expect(disp).not.toBe('none');
        await expect(banner).toContainText('0105567178203');
        await expect(banner).toContainText('已自动新建套账');
        await expect(banner).toContainText('可直接确认');
        await expect(
            page.locator('[data-wsg-create],[data-wsg-switch],[data-wsg-keep]')
        ).toHaveCount(0);
        await page.screenshot({
            path: path.join(OUT, '01-auto-created-banner.png'),
            fullPage: true,
        });

        await page.click('#dx-inv-confirm-all');
        await expect(page.locator('.dx-pill.ok')).toHaveCount(1);
        expect(convertCalls).toHaveLength(0);
        expect(createCalls).toHaveLength(0);
        expect(rebindCalls).toHaveLength(0);
    });

    test('命中已有套账 → 只显示已自动归入', async ({ page }) => {
        await boot(page, { clients: CLIENTS_WITH_MATCH, recogn: RECOG_MATCHED });
        await uploadAndReview(page, [pdfFile('makeup-invoice.pdf')]);

        const banner = page.locator('.dx-wsguard');
        await expect(banner).toBeVisible();
        await expect(banner).toContainText('已按票面主体归入套账');
        await expect(
            page.locator('[data-wsg-create],[data-wsg-switch],[data-wsg-keep]')
        ).toHaveCount(0);
        await page.screenshot({
            path: path.join(OUT, '02-auto-matched-banner.png'),
            fullPage: true,
        });
        expect(createCalls).toHaveLength(0);
        expect(rebindCalls).toHaveLength(0);
    });

    test('后端最终归属是当前套账 → 不出现横幅', async ({ page }) => {
        await boot(page, { clients: CLIENTS_SINGLE, recogn: RECOG_NORMAL });
        await uploadAndReview(page, [pdfFile('normal-invoice.pdf')]);

        await expect(page.locator('.dx-wsguard')).toHaveCount(0);
        await page.screenshot({
            path: path.join(OUT, '03-current-workspace-no-banner.png'),
            fullPage: true,
        });
    });

    test('一批分属两个套账 →「确认全部」不排除任何文件', async ({ page }) => {
        await boot(page, {
            clients: CLIENTS_SINGLE,
            recogn: RECOG_MISMATCH,
            recognTwo: RECOG_NORMAL,
        });
        await uploadAndReview(page, [pdfFile('makeup-invoice.pdf'), pdfFile('normal-invoice.pdf')]);

        const banner = page.locator('.dx-wsguard');
        await expect(banner).toBeVisible();

        await page.click('#dx-inv-confirm-all');
        await expect(page.locator('.dx-pill.ok')).toHaveCount(2);
        expect(convertCalls).toHaveLength(0);
        expect(createCalls).toHaveLength(0);
        expect(rebindCalls).toHaveLength(0);
        await page.screenshot({
            path: path.join(OUT, '04-confirm-all-no-filter.png'),
            fullPage: true,
        });
    });
});
