/* global window, document, Node */

const path = require('path');
const fs = require('fs');
const { test, expect, devices } = require('@playwright/test');
const localServer = require('./_local_static_server');

const PORT = 8985;
const BASE = `http://127.0.0.1:${PORT}`;
const OUT = path.join(__dirname, '_artifacts', 'erp-line-intake');
fs.mkdirSync(OUT, { recursive: true });
let server;
const authBodies = [];
const previewHeaders = [];
const requestLog = [];

test.beforeAll(async () => {
    server = await localServer.start(PORT, '/static/erp-line-intake/index.html');
});
test.afterAll(() => localServer.stop(server));

function records() {
    return [
        {
            id: 'h1',
            pages: [
                {
                    page_number: 1,
                    fields: {
                        invoice_no: 'PO-001',
                        invoice_date: '2026-08-28',
                        seller_name: 'Supplier',
                        seller_tax: '0101',
                        total_amount: '107',
                        items: [
                            {
                                description: 'Widget',
                                quantity: '1',
                                unit_price: '100',
                                amount: '100',
                                posting_kind: '',
                            },
                        ],
                    },
                },
            ],
            preview_url: '/api/line/erp/draft/d1/records/h1/page/0.png',
            preview_urls: ['/api/line/erp/draft/d1/records/h1/page/0.png'],
        },
        {
            id: 'h2',
            pages: [
                {
                    page_number: 1,
                    fields: {
                        invoice_number: 'PO-002',
                        date: '2026-08-28',
                        seller_name: 'Second Supplier',
                        total_amount: '214',
                        items: [{ name: 'Gadget', qty: '2', price: '107', posting_kind: '' }],
                    },
                },
            ],
            preview_url: '/api/line/erp/draft/d1/records/h2/page/1.png',
            preview_urls: ['/api/line/erp/draft/d1/records/h2/page/1.png'],
        },
    ];
}

async function open(
    page,
    {
        putStatus = 200,
        draftRecords = records(),
        draftQuery = '?draft=d1',
        direction = 'purchase',
    } = {}
) {
    authBodies.length = 0;
    previewHeaders.length = 0;
    requestLog.length = 0;
    await page.route('https://static.line-scdn.net/**', (r) => r.abort());
    await page.addInitScript(() => {
        window.liff = {
            init: async () => {},
            isLoggedIn: () => true,
            getIDToken: () => 'test-id-token',
        };
    });
    await page.route('**/api/line/erp/liff/config', (r) =>
        r.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, data: { liff_id: 'test-liff' } }),
        })
    );
    await page.route('**/api/line/erp/liff/auth', async (r) => {
        authBodies.push(JSON.parse(r.request().postData() || '{}'));
        return r.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, data: { token: 'test-bearer' } }),
        });
    });
    await page.route('**/api/line/erp/draft/d1/**', async (route) => {
        const req = route.request();
        const pathname = new URL(req.url()).pathname;
        if (/\/records\/[^/]+\/page\/\d+\.png$/.test(pathname)) {
            previewHeaders.push(req.headers().authorization || '');
            return route.fulfill({
                status: 200,
                contentType: 'image/svg+xml',
                body: '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="960"><rect width="100%" height="100%" fill="white"/><rect x="40" y="40" width="640" height="880" rx="16" fill="none" stroke="#d7e4dc" stroke-width="4"/><text x="80" y="120" font-size="34" font-family="sans-serif" fill="#183d2b">Original invoice</text><text x="80" y="190" font-size="28" font-family="sans-serif" fill="#456">PO-001 · Supplier</text><path d="M80 250h560M80 320h560M80 390h360" stroke="#b7c9bf" stroke-width="10"/></svg>',
            });
        }
        requestLog.push({ method: req.method(), path: pathname, body: req.postData() || '' });
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true }),
        });
    });
    await page.route('**/api/line/erp/draft/d1', async (route) => {
        const req = route.request();
        requestLog.push({
            method: req.method(),
            path: new URL(req.url()).pathname,
            body: req.postData() || '',
        });
        if (req.method() === 'PUT') {
            return route.fulfill({
                status: putStatus,
                contentType: 'application/json',
                body: JSON.stringify(putStatus === 200 ? { ok: true } : { detail: 'save failed' }),
            });
        }
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                ok: true,
                data: { direction, records: draftRecords },
            }),
        });
    });
    await page.goto(`${BASE}/static/erp-line-intake/index.html${draftQuery}`);
    await expect(page.locator('#editor')).toBeVisible();
}

test('mobile ERP LINE review blocks incomplete lines and renders all fields', async ({
    browser,
}) => {
    const page = await browser.newPage({ ...devices['iPhone 13'] });
    await open(page);
    await expect(page.locator('[data-field="0:seller_name"]')).toHaveValue('Supplier');
    await expect(page.locator('[data-record]')).toHaveCount(2);
    await expect.poll(() => previewHeaders.length).toBe(2);
    expect(authBodies[authBodies.length - 1]).toMatchObject({
        id_token: 'test-id-token',
        draft_id: 'd1',
    });
    await expect(page.locator('[data-kind="0:0"]')).toBeVisible();
    await page.screenshot({ path: path.join(OUT, 'mobile-review.png'), fullPage: true });
    await page.locator('[data-action="confirm"]').click();
    await expect(page.locator('#state')).toContainText('กรุณา');
    await page.locator('[data-kind="0:0"]').selectOption('stock');
    await page.locator('[data-kind="1:0"]').selectOption('service');
    await page.locator('[data-field="0:seller_name"]').fill('Edited Supplier');
    await page.locator('[data-action="confirm"]').click();
    await expect(page.locator('#state')).toContainText('ยืนยันแล้ว');
    const writes = requestLog.filter((entry) => entry.method !== 'GET');
    expect(writes.map((entry) => `${entry.method} ${entry.path}`)).toEqual([
        'PUT /api/line/erp/draft/d1',
        'POST /api/line/erp/draft/d1/confirm',
    ]);
    const saved = JSON.parse(writes[0].body);
    expect(saved.records.map((record) => record.id)).toEqual(['h1', 'h2']);
    expect(saved.records[0].pages[0].fields.seller_name).toBe('Edited Supplier');
    expect(saved.records[0].pages[0].fields.invoice_number).toBe('PO-001');
    expect(saved.records[0].pages[0].fields.items[0]).toMatchObject({
        name: 'Widget',
        qty: '1',
        price: '100',
        posting_kind: 'stock',
    });
    await page.close();
});

test('desktop supports language switching and discard action', async ({ browser }) => {
    const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    await open(page);
    await page.locator('#lang').selectOption('en');
    await expect(page.locator('h1')).toContainText('Review purchase document');
    await page.locator('[data-action="discard"]').click();
    await expect(page.locator('#discard-dialog')).toBeVisible();
    await page.locator('[data-dialog-cancel]').last().click();
    expect(requestLog.filter((entry) => entry.method !== 'GET')).toEqual([]);
    await page.locator('[data-action="discard"]').click();
    await expect(page.locator('#discard-dialog')).toBeVisible();
    await page.locator('[data-dialog-confirm]').click();
    await expect(page.locator('#state')).toContainText('Discarded');
    expect(
        requestLog
            .filter((entry) => entry.method !== 'GET')
            .map((entry) => `${entry.method} ${entry.path}`)
    ).toEqual(['POST /api/line/erp/draft/d1/discard']);
    await page.screenshot({ path: path.join(OUT, 'desktop-discarded.png'), fullPage: true });
});

test('sales review identifies the buyer first and keeps seller fields editable', async ({
    browser,
}) => {
    const draftRecords = records().slice(0, 1);
    Object.assign(draftRecords[0].pages[0].fields, {
        buyer_name: 'Customer A',
        buyer_tax: '0105559000012',
        buyer_branch: '00000',
        buyer_address: 'Bangkok',
        seller_address: 'Chiang Mai',
        document_type: 'tax_invoice',
    });
    const page = await browser.newPage({ ...devices['iPhone 13'] });
    await open(page, { direction: 'sales', draftRecords });
    await page.locator('#lang').selectOption('zh');
    await expect(page.locator('h1')).toHaveText('复核销售单据');
    await expect(page.locator('[data-field="0:buyer_name"]')).toHaveValue('Customer A');
    await expect(page.locator('[data-field="0:seller_name"]')).toHaveValue('Supplier');
    const buyerComesFirst = await page.evaluate(() => {
        const buyer = document.querySelector('[data-field="0:buyer_name"]');
        const seller = document.querySelector('[data-field="0:seller_name"]');
        return Boolean(buyer.compareDocumentPosition(seller) & Node.DOCUMENT_POSITION_FOLLOWING);
    });
    expect(buyerComesFirst).toBe(true);
    await page.screenshot({ path: path.join(OUT, 'sales-mobile-review.png'), fullPage: true });
    await page.close();
});

test('LIFF callback state keeps the ERP draft id', async ({ page }) => {
    await open(page, { draftQuery: `?liff.state=${encodeURIComponent('?draft=d1')}` });
    await expect(page.locator('[data-field="0:seller_name"]')).toHaveValue('Supplier');
});

test('failed draft save never calls confirm', async ({ page }) => {
    await open(page, { putStatus: 409 });
    await page.locator('[data-kind="0:0"]').selectOption('stock');
    await page.locator('[data-kind="1:0"]').selectOption('service');
    await page.locator('[data-action="confirm"]').click();
    await expect(page.locator('#state')).toContainText('โหลดเอกสารไม่สำเร็จ');
    const writes = requestLog.filter((entry) => entry.method !== 'GET');
    expect(writes.map((entry) => `${entry.method} ${entry.path}`)).toEqual([
        'PUT /api/line/erp/draft/d1',
    ]);
});

test('missing OCR items stay blank and require explicit user entry', async ({ page }) => {
    const draftRecords = records().slice(0, 1);
    draftRecords[0].pages[0].fields.items = [];
    await open(page, { draftRecords });
    await expect(page.locator('[data-field="0:item.0.qty"]')).toHaveValue('');
    await expect(page.locator('[data-field="0:item.0.price"]')).toHaveValue('');
    await expect(page.locator('[data-field="0:item.0.subtotal"]')).toHaveValue('');
    await page.locator('[data-action="confirm"]').click();
    await expect(page.locator('#state')).toContainText('กรุณา');
    expect(requestLog.filter((entry) => entry.method !== 'GET')).toEqual([]);
});
