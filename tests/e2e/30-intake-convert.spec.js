// Pearnly E2E · 30 OCR 确认 → 正式单据转换桥(intake_bridge)前端接线 + 三处 UI 拍板
// ============================================================
// 桩路数照 26-purchase-product-wiring.spec.js / scripts/_intake_invoice_verify.cjs:
// token 塞 localStorage → page.route 拦 /api/** 桩契约信封,本地静态服务(不连真库/真
// OCR)。验的是「确认按钮真调了 POST /api/ocr/convert-documents、chip 按 converted/
// skipped 如实渲染」,不是后端桥本身(后端由 tests/unit/test_intake_bridge_convert.py +
// tests/integration/test_intake_bridge_real.py 真库守)。
//
// 覆盖:
//   ① 确认全部 → 调转换桥 → 请求体带 history_ids/workspace_client_id → 绿色「已入账」chip
//   ② 结果预览默认展开全部字段(2026-08-07 拍板删了「展开全部字段」按钮,不用点)
//   ③ 识别记录页顶部「仅票据」范围条已整块删除(page-history.ts + hist-scope CSS + i18n)
// ============================================================
/* global window, document */

const path = require('path');
const fs = require('fs');
const { test, expect } = require('@playwright/test');
const localServer = require('./_local_static_server');

const PORT = 8979;
const BASE = `http://127.0.0.1:${PORT}`;
const OUT = path.join(__dirname, '_artifacts', 'intake-convert');
fs.mkdirSync(OUT, { recursive: true });

const RECOG = {
    ok: true,
    filename: 'invoice.pdf',
    page_count: 1,
    history_id: 'h1',
    history_ids: ['h1'],
    invoice_count: 1,
    confidence: 'high',
    needs_review: false,
    missed_invoice_warnings: [],
    duplicate_warnings: [],
    pages: [{ fields: {} }],
    invoices: [
        {
            history_id: 'h1',
            source_index: 1,
            source_total: 1,
            page_indices: [1],
            fields: {
                seller_name: 'Test Supplier Co',
                seller_tax: '0107537000521',
                invoice_number: 'INV-CONV-001',
                date: '2026-06-01',
                subtotal: '100',
                vat: '7',
                total_amount: '107',
                buyer_name: 'Buyer Co',
                buyer_tax: '0105561234563',
                items: [{ name: 'Widget', qty: '2', price: '50' }],
            },
        },
    ],
};

const CONVERT_OK = {
    converted: [
        { history_id: 'h1', doc_type: 'purchase', doc_id: 'doc-1', doc_no: 'INV-CONV-001' },
    ],
    skipped: [],
};

const CONVERT_SKIPPED = {
    converted: [],
    skipped: [{ history_id: 'h1', reason: 'no_direction' }],
};

let server;
test.beforeAll(async () => {
    server = await localServer.start(PORT, '/home.html');
});
test.afterAll(() => localServer.stop(server));

let convertCalls = [];

async function stub(page, convertResult) {
    convertCalls = [];
    await page.route('**/api/**', async (route) => {
        const req = route.request();
        const u = req.url();
        if (u.includes('/api/ocr/recognize')) {
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(RECOG),
            });
        }
        if (u.includes('/api/ocr/convert-documents')) {
            convertCalls.push(JSON.parse(req.postData() || '{}'));
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(convertResult),
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

async function boot(page, convertResult) {
    await page.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'e2e-intake-convert-token');
        localStorage.setItem('mrpilot_lang', 'zh');
    });
    await stub(page, convertResult);
    await page.goto(`${BASE}/home.html`, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof window.routeTo === 'function', { timeout: 20000 });
    await page.evaluate(() => {
        window.isOwner = () => true;
        window.getActiveWorkspaceClientId = () => 1;
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

test.describe('OCR 确认 → 正式单据转换桥(前端接线 + UI 拍板)', () => {
    test('确认全部 → 调转换桥 → 已入账 chip', async ({ page }) => {
        await boot(page, CONVERT_OK);
        await page.setInputFiles('#dx-inv-file', {
            name: 'invoice.pdf',
            mimeType: 'application/pdf',
            buffer: Buffer.from('x'),
        });
        await page.waitForSelector('#dx-inv-start');
        await page.click('#dx-inv-start');
        await page.waitForSelector('#dx-s-inv-review.active', { timeout: 8000 });

        // ② 结果预览默认展开全部字段:按钮已删,.dx-extra 不再需要点击才可见。
        await expect(page.locator('.dx-extra-toggle')).toHaveCount(0);
        await expect(page.locator('.dx-acc-item.open .dx-extra')).toBeVisible();
        const revCount = await page.locator('.dx-acc-item.open .dx-rv').count();
        expect(revCount, '核心+补充字段应同时可见(无需展开)').toBeGreaterThanOrEqual(9);
        await page.screenshot({
            path: path.join(OUT, '01-review-fields-expanded-by-default.png'),
            fullPage: true,
        });

        // ① 确认全部 → 触发转换桥
        const respPromise = page.waitForResponse((r) =>
            r.url().includes('/api/ocr/convert-documents')
        );
        await page.click('#dx-inv-confirm-all');
        await respPromise;
        await expect(page.locator('.dx-inv-head .dx-badge.green')).toBeVisible();
        await expect(page.locator('.dx-inv-head .dx-badge.green')).toHaveText('已入账');
        await page.screenshot({
            path: path.join(OUT, '02-confirmed-booked-chip.png'),
            fullPage: true,
        });

        expect(convertCalls.length, '确认全部应触发一次转换请求').toBe(1);
        expect(convertCalls[0].history_ids).toEqual(['h1']);
        expect(convertCalls[0].workspace_client_id).toBe(1);

        // 再次确认(如已确认过)不该重复调用同一 history_id(convertHistoryIds 按 id 去重)。
        await page.click('#dx-inv-rev-next');
        await page.waitForSelector('#dx-s-inv-submit.active', { timeout: 8000 });
        expect(convertCalls.length, 'enterSubmit 兜底调用应因已转换而不重复请求').toBe(1);
    });

    test('转换被跳过 → 琥珀色 chip 带跳过原因(四态诚实,不吞)', async ({ page }) => {
        await boot(page, CONVERT_SKIPPED);
        await page.setInputFiles('#dx-inv-file', {
            name: 'invoice.pdf',
            mimeType: 'application/pdf',
            buffer: Buffer.from('x'),
        });
        await page.click('#dx-inv-start');
        await page.waitForSelector('#dx-s-inv-review.active', { timeout: 8000 });
        const respPromise = page.waitForResponse((r) =>
            r.url().includes('/api/ocr/convert-documents')
        );
        await page.click('#dx-inv-confirm-all');
        await respPromise;
        const chip = page.locator('.dx-inv-head .dx-badge.amber');
        await expect(chip).toBeVisible();
        await expect(chip).toContainText('未入账');
        await page.screenshot({
            path: path.join(OUT, '03-skipped-reason-chip.png'),
            fullPage: true,
        });
    });

    test('识别记录页:「仅票据」范围条已整块删除', async ({ page }) => {
        await boot(page, CONVERT_OK);
        await page.route('**/api/history**', (route) =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ items: [], total: 0, status_counts: {} }),
            })
        );
        await page.evaluate(() => window.routeTo('history'));
        await page.waitForSelector('#page-history.active', { timeout: 8000 });
        await expect(page.locator('#page-history .hist-scope')).toHaveCount(0);
        await expect(page.locator('#page-history .hist-scope-tag')).toHaveCount(0);
        await page.screenshot({
            path: path.join(OUT, '04-history-banner-removed.png'),
            fullPage: true,
        });
    });
});
