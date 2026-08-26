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
/* global window, document, getComputedStyle */

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

// 销项 ABB 简化税票(Sister Makeup 散客):票面无买方身份,seller_* 全对、buyer_* 留空。
// 修复前 warnFields 无条件要当前方向税号 → 空买方税号被标「需确认」,用户误以为识别失败。
const RECOG_WALKIN = {
    ok: true,
    filename: 'abb-receipt.pdf',
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
                direction: 'sales',
                document_type: 'simplified_tax_invoice',
                seller_name: 'Sister Makeup',
                seller_tax: '0105567178203',
                invoice_number: 'ABB-0001',
                date: '2026-08-08',
                subtotal: '100',
                vat: '7',
                total_amount: '107',
                buyer_name: '',
                buyer_tax: '',
                items: [{ name: 'Lipstick', qty: '1', price: '107' }],
            },
        },
    ],
};

// 完整税票:散客豁免不该放松到它头上,买方税号缺失仍须标 warn。
const RECOG_FULL_TAX = {
    ok: true,
    filename: 'full-tax-invoice.pdf',
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
                direction: 'sales',
                document_type: 'tax_invoice',
                seller_name: 'Sister Makeup',
                seller_tax: '0105567178203',
                invoice_number: 'TX-0002',
                date: '2026-08-08',
                subtotal: '100',
                vat: '7',
                total_amount: '107',
                buyer_name: 'Walk-in Customer',
                buyer_tax: '',
                items: [{ name: 'Product', qty: '1', price: '107' }],
            },
        },
    ],
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

async function stub(page, convertResult, recogn) {
    convertCalls = [];
    await page.route('**/api/**', async (route) => {
        const req = route.request();
        const u = req.url();
        if (u.includes('/api/ocr/recognize')) {
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(recogn || RECOG),
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

async function boot(page, convertResult, recogn) {
    await page.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'e2e-intake-convert-token');
        localStorage.setItem('mrpilot_lang', 'zh');
        // Keep static home.html tests on the internal full shell.
        localStorage.setItem('pearnly_entry', 'firm');
    });
    await stub(page, convertResult, recogn);
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

    test('散客票(ABB/收据):空买方不再「需确认」+ 对手方税号展示 + 现金客户徽章', async ({
        page,
    }) => {
        await boot(page, CONVERT_OK, RECOG_WALKIN);
        await page.setInputFiles('#dx-inv-file', {
            name: 'invoice.pdf',
            mimeType: 'application/pdf',
            buffer: Buffer.from('x'),
        });
        await page.waitForSelector('#dx-inv-start');
        await page.click('#dx-inv-start');
        await page.waitForSelector('#dx-s-inv-review.active', { timeout: 8000 });

        // ① 无 warn 高亮格(ABB 散客票不把空买方标「需确认」)
        await expect(page.locator('.dx-acc-item.open .dx-rv.warn')).toHaveCount(0);

        // ④ 文件行状态不含「需确认」,应为已通过检查
        const pill = page.locator('.dx-acc-row .dx-pill');
        await expect(pill).toBeVisible();
        expect(await pill.textContent()).not.toContain('需确认');
        await expect(pill).toContainText('已通过检查');

        // ② 头部散客徽章可见(getComputedStyle 确认 display 非 none)
        const badge = page.locator('.dx-inv-head .dx-badge.blue');
        await expect(badge).toHaveCount(1);
        const badgeDisplay = await badge.evaluate((el) => getComputedStyle(el).display);
        expect(badgeDisplay).not.toBe('none');

        // ③ 展开区能见到对手方(卖方)税号真实值 + 卖方税号标签
        const sellerTax = page.locator('.dx-acc-item.open input[data-iv-field$="seller_tax"]');
        await expect(sellerTax).toHaveValue('0105567178203');
        await expect(
            page.locator('.dx-acc-item.open label', { hasText: '卖方税号' })
        ).toBeVisible();
        await page.screenshot({
            path: path.join(OUT, '05-walkin-anon-buyer-badge.png'),
            fullPage: true,
        });
    });

    test('完整税票:买方税号缺失仍标 warn(散客豁免不放松)', async ({ page }) => {
        await boot(page, CONVERT_OK, RECOG_FULL_TAX);
        await page.setInputFiles('#dx-inv-file', {
            name: 'invoice.pdf',
            mimeType: 'application/pdf',
            buffer: Buffer.from('x'),
        });
        await page.click('#dx-inv-start');
        await page.waitForSelector('#dx-s-inv-review.active', { timeout: 8000 });

        // 完整税票(document_type='tax_invoice')不在散客豁免内 → 买方税号格带 .warn
        await expect(page.locator('.dx-acc-item.open .dx-rv.warn')).toHaveCount(1);
        await expect(
            page.locator('.dx-rv.warn:has(input[data-iv-field$="buyer_tax"])')
        ).toHaveCount(1);
        // 非散客票也不该出现现金客户徽章
        await expect(page.locator('.dx-inv-head .dx-badge.blue')).toHaveCount(0);
        await page.screenshot({
            path: path.join(OUT, '06-full-tax-buyer-tax-still-warn.png'),
            fullPage: true,
        });
    });
});
