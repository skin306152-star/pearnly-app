/* global window */

const path = require('path');
const fs = require('fs');
const { test, expect, devices } = require('@playwright/test');
const localServer = require('./_local_static_server');

const PORT = 8985;
const BASE = `http://127.0.0.1:${PORT}`;
const OUT = path.join(__dirname, '_artifacts', 'erp-line-intake');
fs.mkdirSync(OUT, { recursive: true });
let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT, '/static/erp-line-intake/index.html');
});
test.afterAll(() => localServer.stop(server));

function erpRecords() {
    return [
        {
            id: 'h1',
            filename: 'purchase-batch.pdf',
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
                { page_number: 2, fields: { total_amount: '107', items: [] } },
            ],
            preview_urls: [
                '/api/line/erp/draft/d1/records/h1/page/0.png',
                '/api/line/erp/draft/d1/records/h1/page/1.png',
            ],
        },
        {
            id: 'h2',
            filename: 'purchase-batch.pdf',
            pages: [
                {
                    page_number: 3,
                    fields: {
                        invoice_number: 'PO-002',
                        date: '2026-08-28',
                        seller_name: 'Second Supplier',
                        total_amount: '214',
                        items: [{ name: 'Gadget', qty: '2', price: '107', posting_kind: '' }],
                    },
                },
            ],
            preview_urls: ['/api/line/erp/draft/d1/records/h2/page/2.png'],
        },
    ];
}

function coworkRecords() {
    return [
        {
            id: 'c1',
            filename: 'cowork-batch.pdf',
            pages: [
                {
                    page_number: 1,
                    fields: {
                        invoice_number: 'CW-001',
                        date: '2026-09-01',
                        seller_name: 'Cowork Supplier',
                        total_amount: '320',
                        items: [{ name: '', qty: '2', price: '160', subtotal: '320' }],
                    },
                },
            ],
            preview_urls: ['/api/cowork-line/intake/draft/c1/records/c1/page/0.png'],
        },
    ];
}

async function installLiff(page) {
    await page.route('https://static.line-scdn.net/**', (route) => route.abort());
    await page.addInitScript(() => {
        window.liff = {
            init: async () => {},
            isLoggedIn: () => true,
            getIDToken: () => 'test-id-token',
        };
    });
}

function previewResponse(route, headers) {
    headers.push(route.request().headers().authorization || '');
    return route.fulfill({
        status: 200,
        contentType: 'image/svg+xml',
        body: '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="960"><rect width="100%" height="100%" fill="white"/><rect x="40" y="40" width="640" height="880" rx="16" fill="none" stroke="#d7e4dc" stroke-width="4"/><text x="80" y="120" font-size="34" font-family="sans-serif" fill="#183d2b">Original invoice</text><path d="M80 250h560M80 320h560M80 390h360" stroke="#b7c9bf" stroke-width="10"/></svg>',
    });
}

async function openErp(
    page,
    {
        putStatus = 200,
        draftRecords = erpRecords(),
        direction = 'purchase',
        adapter = 'express',
        draftQuery,
    } = {}
) {
    const requests = [];
    const authBodies = [];
    const previewHeaders = [];
    const targets = [
        {
            endpoint_id: 'express-1',
            workspace_client_id: 69,
            workspace_name: 'Sister Makeup',
            adapter: 'express',
            label: 'Express · MAIN',
            account_set_label: 'MAIN',
            selectable: true,
            configured: true,
            connection_state: 'online',
            ready_checks: {
                erp_connection: true,
                companion_online: true,
                profile_matches: true,
            },
        },
        {
            endpoint_id: 'express-2',
            workspace_client_id: 71,
            workspace_name: 'Sister Makeup Branch',
            adapter: 'express',
            label: 'Express · BRANCH',
            account_set_label: 'BRANCH',
            selectable: true,
            configured: true,
            connection_state: 'online',
            ready_checks: {
                erp_connection: true,
                companion_online: true,
                profile_matches: true,
            },
        },
        {
            endpoint_id: 'mrerp-1',
            workspace_client_id: 70,
            workspace_name: 'Accounting Client A',
            adapter: 'mrerp',
            label: 'MR.ERP · Client A',
            account_set_label: 'Client A',
            selectable: true,
            configured: true,
            connection_state: 'online',
            ready_checks: { erp_connection: true },
        },
        {
            endpoint_id: 'mrerp-2',
            workspace_client_id: 72,
            workspace_name: 'Accounting Client B',
            adapter: 'mrerp',
            label: 'MR.ERP · Client B',
            account_set_label: 'Client B',
            selectable: true,
            configured: true,
            connection_state: 'online',
            ready_checks: { erp_connection: true },
        },
    ];
    const selectedTarget = targets.find((target) => target.adapter === adapter);
    const selection = {
        endpoint_id: selectedTarget.endpoint_id,
        workspace_client_id: selectedTarget.workspace_client_id,
        adapter,
        direction,
        posting_kind: adapter === 'express' ? 'stock' : null,
        payment: adapter === 'mrerp' ? (direction === 'sales' ? 'cash' : 'credit') : null,
        target_label: selectedTarget.label,
    };
    await installLiff(page);
    await page.route('**/api/line/erp/liff/config', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, data: { liff_id: 'test-liff' } }),
        })
    );
    await page.route('**/api/line/erp/liff/auth', async (route) => {
        authBodies.push(JSON.parse(route.request().postData() || '{}'));
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, data: { token: 'test-bearer' } }),
        });
    });
    await page.route('**/api/line/erp/draft/d1/**', async (route) => {
        const request = route.request();
        const pathname = new URL(request.url()).pathname;
        if (/\/records\/[^/]+\/page\/\d+\.png$/.test(pathname)) {
            return previewResponse(route, previewHeaders);
        }
        requests.push({ method: request.method(), path: pathname, body: request.postData() || '' });
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, data: { ok: true } }),
        });
    });
    await page.route('**/api/line/erp/draft/d1', async (route) => {
        const request = route.request();
        const pathname = new URL(request.url()).pathname;
        requests.push({ method: request.method(), path: pathname, body: request.postData() || '' });
        if (request.method() === 'PUT') {
            return route.fulfill({
                status: putStatus,
                contentType: 'application/json',
                body: JSON.stringify(
                    putStatus === 200
                        ? { ok: true, data: { records: draftRecords, selection, targets } }
                        : { detail: 'save failed' }
                ),
            });
        }
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                ok: true,
                data: { direction, records: draftRecords, selection, targets },
            }),
        });
    });
    const query = draftQuery || '?flow=erp-intake&draft=d1';
    await page.goto(`${BASE}/static/erp-line-intake/index.html${query}`);
    await expect(page.locator('#editor')).toBeVisible();
    return { requests, authBodies, previewHeaders };
}

async function openCowork(page) {
    const requests = [];
    const previewHeaders = [];
    const records = coworkRecords();
    const selection = {
        endpoint_id: 'endpoint-1',
        workspace_client_id: 69,
        adapter: 'express',
        direction: 'purchase',
        posting_kind: 'stock',
        target_label: 'Express · 69EXP',
    };
    const targets = [
        {
            endpoint_id: 'endpoint-1',
            workspace_client_id: 69,
            adapter: 'express',
            label: 'Express · 69EXP',
            account_set_label: '69EXP',
            selectable: true,
            configured: true,
            connection_state: 'online',
            ready_checks: { erp_connection: true, companion_online: true },
        },
    ];
    await installLiff(page);
    await page.route('**/api/cowork-line/intake/liff/config', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, data: { liff_id: 'cowork-liff' } }),
        })
    );
    await page.route('**/api/cowork-line/intake/liff/auth', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, data: { token: 'cowork-bearer' } }),
        })
    );
    await page.route('**/api/cowork-line/intake/draft/c1/**', async (route) => {
        const request = route.request();
        const pathname = new URL(request.url()).pathname;
        if (/\/records\/[^/]+\/page\/\d+\.png$/.test(pathname)) {
            return previewResponse(route, previewHeaders);
        }
        requests.push({ method: request.method(), path: pathname, body: request.postData() || '' });
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                ok: true,
                data: { saved: true, push_ok: true, status: 'success' },
            }),
        });
    });
    await page.route('**/api/cowork-line/intake/draft/c1', async (route) => {
        const request = route.request();
        const pathname = new URL(request.url()).pathname;
        requests.push({ method: request.method(), path: pathname, body: request.postData() || '' });
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, data: { records, selection, targets } }),
        });
    });
    await page.goto(`${BASE}/static/cowork-line-intake/index.html?flow=cowork-intake&draft=c1`);
    await expect(page.locator('#editor')).toBeVisible();
    return { requests, previewHeaders };
}

test('ERP mobile list searches, opens multi-page detail, and gates batch confirm', async ({
    browser,
}) => {
    const page = await browser.newPage({ ...devices['iPhone 13'] });
    const run = await openErp(page);
    await expect(page.locator('.target-locked')).toHaveText('Express');
    await expect(page.locator('[data-target-account-set]')).toHaveValue('express-1:69');
    await expect(page.locator('[data-target-selection="posting_kind"]')).toHaveValue('stock');
    await page.screenshot({
        path: path.join(OUT, 'erp-mobile-target-selection.png'),
        fullPage: true,
    });
    await expect(page.locator('.review-row')).toHaveCount(2);
    await expect(page.locator('[data-review-action="confirm"]')).toBeDisabled();
    await page.locator('[data-review-search]').fill('Second Supplier');
    await expect(page.locator('.review-row')).toHaveCount(1);
    await page.locator('[data-review-search]').fill('');
    await page.locator('.review-row').first().click();
    await expect(page.locator('.review-original')).toHaveCount(2);
    await page.locator('[data-field="0:field:total_amount"]').click();
    await expect(page.locator('[data-review-page="1"]')).toHaveClass(/is-source/);
    await expect
        .poll(() => page.locator('[data-review-originals]').evaluate((node) => node.scrollTop))
        .toBeGreaterThan(0);
    await expect(page.locator('[data-field="0:field:seller_name"]')).toHaveValue('Supplier');
    await page.locator('[data-field="0:field:seller_name"]').click();
    await expect(page.locator('[data-review-page="0"]')).toHaveClass(/is-source/);
    await page.locator('[data-field="0:field:seller_name"]').fill('Edited Supplier');
    await page.locator('[data-kind="0:0"]').selectOption('stock');
    await page.locator('[data-review-back]').click();
    await page.locator('.review-row').nth(1).click();
    await page.locator('[data-kind="1:0"]').selectOption('service');
    await expect(page.locator('[data-review-action="confirm"]')).toBeEnabled();
    await expect(page.locator('[data-review-status]')).toHaveClass(/review-status--ready/);
    await page.screenshot({ path: path.join(OUT, 'erp-mobile-detail.png'), fullPage: true });
    await page.locator('[data-review-action="confirm"]').click();
    await expect(page.locator('#state')).toContainText('ยืนยันแล้ว');
    const writes = run.requests.filter((entry) => entry.method !== 'GET');
    expect(writes.map((entry) => `${entry.method} ${entry.path}`)).toEqual([
        'PUT /api/line/erp/draft/d1',
        'POST /api/line/erp/draft/d1/confirm',
    ]);
    const saved = JSON.parse(writes[0].body);
    expect(saved.records.map((record) => record.id)).toEqual(['h1', 'h2']);
    expect(saved.records[0].pages[0].fields.seller_name).toBe('Edited Supplier');
    expect(saved.records[0].pages[0].fields.items[0]).toMatchObject({
        name: 'Widget',
        qty: '1',
        price: '100',
        posting_kind: 'stock',
    });
    expect(saved).toMatchObject({
        endpoint_id: 'express-1',
        workspace_client_id: 69,
        direction: 'purchase',
        adapter: 'express',
        posting_kind: 'stock',
    });
    expect(run.authBodies[0]).toMatchObject({ id_token: 'test-id-token', draft_id: 'd1' });
    expect(run.previewHeaders.every((value) => value === 'Bearer test-bearer')).toBe(true);
    await page.close();
});

test('editor locks the conversation ERP and only switches its account set', async ({ page }) => {
    await openErp(page, { adapter: 'mrerp', direction: 'sales' });
    await expect(page.locator('.target-locked')).toHaveText('MR.ERP');
    await expect(page.locator('[data-target-account-set] option')).toHaveCount(2);
    await expect(page.locator('[data-target-account-set]')).toHaveValue('mrerp-1:70');
    await expect(page.locator('[data-target-account-set]')).not.toContainText('Express');
    await expect(page.locator('[data-target-selection="payment"]')).toHaveValue('cash');
    await page.locator('.review-row').first().click();
    await expect(page.locator('[data-kind]')).toHaveCount(0);
    await page.locator('[data-review-back]').click();
    await page.locator('[data-target-account-set]').selectOption('mrerp-2:72');
    await expect(page.locator('[data-target-account-set]')).toHaveValue('mrerp-2:72');
    await expect(page.locator('[data-target-selection="payment"]')).toHaveValue('cash');
    await expect(page.locator('[data-kind]')).toHaveCount(0);
    await expect(page.locator('[data-review-action="confirm"]')).toBeEnabled();
});

test('ERP desktop filters anomalies and uses the shared discard dialog', async ({ browser }) => {
    const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    const run = await openErp(page);
    await page.locator('#lang').selectOption('en');
    await expect(page.locator('h1')).toContainText('Review purchase documents');
    await page.locator('[data-filter="review"]').click();
    await expect(page.locator('.review-row')).toHaveCount(2);
    await page.locator('[data-review-action="discard"]').click();
    await expect(page.locator('#discard-dialog')).toBeVisible();
    await page.locator('[data-dialog-cancel-button]').click();
    expect(run.requests.filter((entry) => entry.method !== 'GET')).toEqual([]);
    await page.locator('[data-review-action="discard"]').click();
    await page.locator('[data-dialog-confirm]').click();
    await expect(page.locator('#state')).toContainText('Discarded');
    await page.screenshot({ path: path.join(OUT, 'erp-desktop-discarded.png'), fullPage: true });
});

test('LIFF state restores the ERP draft only after initialization', async ({ page }) => {
    const state = encodeURIComponent('/?flow=erp-intake&draft=d1');
    const run = await openErp(page, { draftQuery: `?liff.state=${state}` });
    await expect(page.locator('.review-row')).toHaveCount(2);
    expect(run.authBodies[0].draft_id).toBe('d1');
});

test('large PDF batches render twenty rows first while search covers unloaded invoices', async ({
    page,
}) => {
    const draftRecords = Array.from({ length: 45 }, (_, index) => ({
        id: `bulk-${index + 1}`,
        pages: [
            {
                page_number: index + 1,
                fields: {
                    invoice_number: `BULK-${String(index + 1).padStart(3, '0')}`,
                    date: '2026-09-01',
                    seller_name: `Supplier ${index + 1}`,
                    total_amount: '100',
                    items: [{ name: 'Item', qty: '1', posting_kind: 'stock' }],
                },
            },
        ],
        preview_urls: [`/api/line/erp/draft/d1/records/bulk-${index + 1}/page/0.png`],
    }));
    await openErp(page, { draftRecords });
    await expect(page.locator('.review-row')).toHaveCount(20);
    await page.locator('[data-review-search]').fill('BULK-045');
    await expect(page.locator('.review-row')).toHaveCount(1);
    await expect(page.locator('.review-row')).toContainText('BULK-045');
});

test('failed ERP save never calls batch confirm', async ({ page }) => {
    const run = await openErp(page, { putStatus: 409 });
    await page.locator('.review-row').first().click();
    await page.locator('[data-kind="0:0"]').selectOption('stock');
    await page.locator('[data-review-back]').click();
    await page.locator('.review-row').nth(1).click();
    await page.locator('[data-kind="1:0"]').selectOption('service');
    await page.locator('[data-review-action="confirm"]').click();
    await expect(page.locator('#state')).toContainText('โหลดเอกสารไม่สำเร็จ');
    expect(
        run.requests
            .filter((entry) => entry.method !== 'GET')
            .map((entry) => `${entry.method} ${entry.path}`)
    ).toEqual(['PUT /api/line/erp/draft/d1']);
});

test('Cowork uses the same list, detail, anomaly gate, and batch action layout', async ({
    browser,
}) => {
    const page = await browser.newPage({ ...devices['iPhone 13'] });
    const run = await openCowork(page);
    await page.locator('#lang').selectOption('zh');
    await expect(page.locator('.review-row')).toHaveCount(1);
    await expect(page.locator('[data-review-action="confirm"]')).toBeDisabled();
    await page.locator('.review-row').click();
    await expect(page.locator('.review-original')).toHaveCount(1);
    await page.locator('[data-field="0:items:0:name"]').fill('镜片');
    await expect(page.locator('[data-review-action="confirm"]')).toBeEnabled();
    await expect(page.locator('[data-review-status]')).toContainText('已就绪');
    await page.screenshot({ path: path.join(OUT, 'cowork-mobile-detail.png'), fullPage: true });
    await page.locator('[data-review-action="confirm"]').click();
    await expect(page.locator('#state')).toContainText('已确认');
    expect(
        run.requests
            .filter((entry) => entry.method !== 'GET')
            .map((entry) => `${entry.method} ${entry.path}`)
    ).toEqual([
        'PUT /api/cowork-line/intake/draft/c1',
        'POST /api/cowork-line/intake/draft/c1/confirm',
    ]);
    expect(run.previewHeaders).toContain('Bearer cowork-bearer');
    await page.close();
});
