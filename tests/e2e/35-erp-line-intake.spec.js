/* global window, document, getComputedStyle */

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
                        document_type: 'simplified_tax_invoice',
                        document_type_source: 'ocr',
                        seller_name: 'Supplier',
                        seller_tax: '0101',
                        payment_method: 'card',
                        payment_status: 'paid',
                        posting_payment_manual: 'cash',
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
                        document_type: 'simplified_tax_invoice',
                        document_type_source: 'ocr',
                        seller_name: 'Cowork Supplier',
                        payment_method: 'card',
                        posting_payment_manual: 'cash',
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
        confirmStatus = 'success',
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
            connection_label: 'Express',
            selected_account_key: 'MAIN-2026',
            account_choices: [
                {
                    key: 'MAIN-2025',
                    label: 'MAIN 2025',
                    root_key: '2025',
                    root_label: '2025',
                    writable: true,
                },
                {
                    key: 'MAIN-2026',
                    label: 'MAIN 2026',
                    root_key: '2026',
                    root_label: '2026',
                    writable: true,
                },
            ],
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
            connection_label: 'Express Branch',
            selected_account_key: 'BRANCH-2026',
            account_choices: [
                {
                    key: 'BRANCH-2026',
                    label: 'BRANCH 2026',
                    root_key: '2026',
                    root_label: '2026',
                    writable: true,
                },
            ],
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
            connection_label: 'MR.ERP',
            selected_account_key: 'Client A',
            account_choices: [{ key: 'Client A', label: 'Client A', writable: true }],
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
            connection_label: 'MR.ERP',
            selected_account_key: 'Client B',
            account_choices: [{ key: 'Client B', label: 'Client B', writable: true }],
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
        account_root:
            adapter === 'express'
                ? selectedTarget.account_choices.find(
                      (choice) => choice.key === selectedTarget.selected_account_key
                  ).root_key
                : null,
        account_set: selectedTarget.selected_account_key,
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
        const confirmed = pathname.endsWith('/confirm');
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                ok: true,
                data: confirmed
                    ? {
                          ok: true,
                          push_ok: confirmStatus !== 'failed',
                          status: confirmStatus,
                          push_results: [{ status: confirmStatus }],
                      }
                    : { ok: true },
            }),
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

async function openCowork(page, { draftRecords = coworkRecords() } = {}) {
    const requests = [];
    const previewHeaders = [];
    const records = draftRecords;
    const selection = {
        endpoint_id: 'endpoint-1',
        workspace_client_id: 69,
        adapter: 'express',
        direction: 'purchase',
        posting_kind: 'stock',
        target_label: 'Express · 69EXP',
        account_root: '2026',
        account_set: '69EXP-2026',
    };
    const targets = [
        {
            endpoint_id: 'endpoint-1',
            workspace_client_id: 69,
            adapter: 'express',
            label: 'Express · 69EXP',
            account_set_label: '69EXP',
            connection_label: 'Express',
            selected_account_key: '69EXP-2026',
            account_choices: [
                {
                    key: '69EXP-2025',
                    label: '69EXP 2025',
                    root_key: '2025',
                    root_label: '2025',
                    writable: true,
                },
                {
                    key: '69EXP-2026',
                    label: '69EXP 2026',
                    root_key: '2026',
                    root_label: '2026',
                    writable: true,
                },
            ],
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
    await expect(page.locator('[data-target-erp]')).toHaveValue('express-1:69');
    await expect(page.locator('[data-target-root]')).toHaveValue('2026');
    await expect(page.locator('[data-target-account-set]')).toHaveValue('express-1:69::MAIN-2026');
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
    await expect(page.locator('[data-review-document-open]')).toBeVisible();
    await expect(page.locator('[data-review-originals]')).toHaveCount(0);
    await expect(page.locator('[data-review-document-viewer]')).toBeHidden();
    await page.locator('[data-field="0:field:seller_name"]').fill('Edited Supplier');
    await page.locator('[data-field="0:field:total_amount"]').click();
    await expect(page.locator('[data-review-document-viewer]')).toHaveAttribute(
        'data-selected-page',
        '1'
    );
    const documentOpener = page.locator('[data-review-document-open]');
    await documentOpener.scrollIntoViewIfNeeded();
    const editorScroll = await page.evaluate(() => window.scrollY);
    await documentOpener.click();
    await expect(page.locator('[data-review-document-viewer]')).toBeVisible();
    await expect(page.locator('.review-document-page')).toHaveCount(2);
    await expect(page.locator('.review-document-page img')).toHaveCount(2);
    await expect(page.locator('[data-review-page="1"]')).toHaveClass(/is-source/);
    await expect(page.locator('[data-review-document-status]')).toContainText('2 / 2');
    await page.screenshot({ path: path.join(OUT, 'erp-mobile-pdf-viewer.png') });
    const darkColors = await page.evaluate(() => {
        document.documentElement.classList.add('dark');
        const probe = document.createElement('div');
        probe.style.background = 'var(--bg)';
        document.body.appendChild(probe);
        const colors = {
            viewer: getComputedStyle(document.querySelector('[data-review-document-viewer]'))
                .backgroundColor,
            token: getComputedStyle(probe).backgroundColor,
        };
        probe.remove();
        return colors;
    });
    expect(darkColors.viewer).toBe(darkColors.token);
    await page.screenshot({ path: path.join(OUT, 'erp-mobile-pdf-viewer-dark.png') });
    await page.evaluate(() => document.documentElement.classList.remove('dark'));
    await page.locator('[data-review-document-close]').click();
    await expect(page.locator('[data-review-document-viewer]')).toBeHidden();
    await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(editorScroll);
    await expect(page.locator('[data-field="0:field:seller_name"]')).toHaveValue('Edited Supplier');
    await page.locator('[data-field="0:field:seller_name"]').click();
    await expect(page.locator('[data-review-document-viewer]')).toHaveAttribute(
        'data-selected-page',
        '0'
    );
    const longName = 'SMR Cushion 02 รุ่นพิเศษสำหรับสาขาทดลองชื่อสินค้ายาวมาก';
    await expect(page.locator('[data-field="0:item:0:name"]')).toHaveJSProperty(
        'tagName',
        'TEXTAREA'
    );
    await page.locator('[data-field="0:item:0:name"]').fill(longName);
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
        name: longName,
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

test('editor switches ERP connections without leaking another connection account set', async ({
    page,
}) => {
    const run = await openErp(page, { adapter: 'mrerp', direction: 'sales' });
    await expect(page.locator('[data-target-erp]')).toHaveValue('mrerp-1:70');
    await expect(page.locator('[data-target-account-set] option')).toHaveCount(2);
    await expect(page.locator('[data-target-account-set]')).toHaveValue('mrerp-1:70::Client A');
    await expect(page.locator('[data-target-account-set]')).not.toContainText('Express');
    await expect(page.locator('[data-target-selection="payment"]')).toHaveValue('cash');
    await page.locator('.review-row').first().click();
    await expect(page.locator('[data-kind]')).toHaveCount(0);
    await page.locator('[data-review-back]').click();
    await page.locator('[data-target-erp]').selectOption('mrerp-2:72');
    await expect(page.locator('[data-target-account-set]')).toHaveValue('mrerp-2:72::Client B');
    await expect(page.locator('[data-target-account-set]')).not.toContainText('Client A');
    await expect(page.locator('[data-target-selection="payment"]')).toHaveValue('');
    await page.locator('[data-target-selection="payment"]').selectOption('cash');
    await expect(page.locator('[data-target-account-set]')).toHaveValue('mrerp-2:72::Client B');
    await expect(page.locator('[data-target-selection="payment"]')).toHaveValue('cash');
    await expect(page.locator('[data-kind]')).toHaveCount(0);
    await expect(page.locator('[data-review-action="confirm"]')).toBeEnabled();
    await page.locator('[data-review-action="save"]').click();
    await expect.poll(() => run.requests.filter((entry) => entry.method === 'PUT').length).toBe(1);
    const saved = JSON.parse(run.requests.find((entry) => entry.method === 'PUT').body);
    expect(saved).toMatchObject({
        endpoint_id: 'mrerp-2',
        workspace_client_id: 72,
        account_set: 'Client B',
        target_label: 'MR.ERP · Client B',
    });
});

test('both editors clear the old Express account when the year changes', async ({ browser }) => {
    for (const open of [openErp, openCowork]) {
        const page = await browser.newPage({ ...devices['iPhone 13'] });
        await open(page);
        await expect(page.locator('[data-target-erp]')).toBeVisible();
        await expect(page.locator('[data-target-root]')).toHaveValue('2026');
        await page.locator('[data-target-root]').selectOption('2025');
        await expect(page.locator('[data-target-account-set]')).toHaveValue('');
        await expect(page.locator('[data-target-account-set]')).not.toContainText('2026');
        await expect(page.locator('[data-review-action="confirm"]')).toBeDisabled();
        const account = await page
            .locator('[data-target-account-set] option:not([value=""])')
            .first()
            .getAttribute('value');
        await page.locator('[data-target-account-set]').selectOption(account);
        await expect(page.locator('[data-target-account-set]')).not.toHaveValue('');
        await page.close();
    }
});

test('both LINE editors localize system fields while preserving stored enum values', async ({
    browser,
}) => {
    const erp = await browser.newPage({ ...devices['iPhone 13'] });
    await openErp(erp);
    await erp.locator('.review-row').first().click();
    const erpDocumentType = erp.locator('[data-field="0:field:document_type"]');
    await expect(erpDocumentType).toHaveValue('simplified_tax_invoice');
    await expect(erpDocumentType.locator('option:checked')).toHaveText('ใบกำกับภาษีอย่างย่อ');
    await expect(erp.locator('[data-field="0:field:payment_method"] option:checked')).toHaveText(
        'บัตร'
    );
    await expect(
        erp.locator('[data-field="0:field:posting_payment_manual"] option:checked')
    ).toHaveText('เงินสด');
    await expect(erp.locator('[data-field*="document_type_source"]')).toHaveCount(0);
    await expect(erp.locator('body')).not.toContainText('posting_payment_manual');
    await erp.locator('#lang').selectOption('zh');
    await expect(erpDocumentType).toHaveValue('simplified_tax_invoice');
    await expect(erpDocumentType.locator('option:checked')).toHaveText('简易税票');
    await expect(erp.locator('[data-field="0:field:payment_method"] option:checked')).toHaveText(
        '银行卡'
    );
    await erp.screenshot({ path: path.join(OUT, 'erp-mobile-system-i18n-zh.png'), fullPage: true });

    const cowork = await browser.newPage({ ...devices['iPhone 13'] });
    await openCowork(cowork);
    await cowork.locator('.review-row').click();
    const coworkDocumentType = cowork.locator('[data-field="0:document_type"]');
    await expect(coworkDocumentType).toHaveValue('simplified_tax_invoice');
    await expect(coworkDocumentType.locator('option:checked')).toHaveText('ใบกำกับภาษีอย่างย่อ');
    await expect(cowork.locator('[data-field="0:payment_method"] option:checked')).toHaveText(
        'บัตร'
    );
    await expect(
        cowork.locator('[data-field="0:posting_payment_manual"] option:checked')
    ).toHaveText('เงินสด');
    await expect(cowork.locator('[data-field*="document_type_source"]')).toHaveCount(0);
    await cowork.locator('#lang').selectOption('ja');
    await expect(coworkDocumentType).toHaveValue('simplified_tax_invoice');
    await expect(coworkDocumentType.locator('option:checked')).toHaveText('簡易税務インボイス');
    await cowork.screenshot({
        path: path.join(OUT, 'cowork-mobile-system-i18n-ja.png'),
        fullPage: true,
    });
    await erp.close();
    await cowork.close();
});

test('retryable ERP result is shown as waiting instead of final failure', async ({ page }) => {
    await openErp(page, {
        adapter: 'mrerp',
        direction: 'purchase',
        confirmStatus: 'retrying',
    });
    await expect(page.locator('[data-review-action="confirm"]')).toBeEnabled();
    await page.locator('[data-review-action="confirm"]').click();
    await expect(page.locator('#state')).toContainText('รับรายการแล้ว กำลังส่งไปยัง ERP');
});

test('ERP desktop filters anomalies and uses the shared discard dialog', async ({ browser }) => {
    const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    const run = await openErp(page);
    await page.locator('#lang').selectOption('en');
    await expect(page.locator('h1')).toContainText('Review purchase documents');
    await page.locator('[data-filter="review"]').click();
    await expect(page.locator('.review-row')).toHaveCount(2);
    await page.locator('.review-row').first().click();
    const openLabel = await page.evaluate(() =>
        window.lineIntakeReviewI18n.text('en', 'openOriginal')
    );
    await expect(page.locator('[data-review-document-open]')).toContainText(openLabel);
    await page.locator('[data-review-document-open]').click();
    const viewerBox = await page.locator('[data-review-document-viewer]').boundingBox();
    expect(viewerBox).toMatchObject({ x: 0, y: 0, width: 1280, height: 800 });
    await page.screenshot({ path: path.join(OUT, 'erp-desktop-pdf-viewer.png') });
    await page.keyboard.press('Escape');
    await expect(page.locator('[data-review-document-viewer]')).toBeHidden();
    await page.locator('[data-review-back]').click();
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
    const openLabel = await page.evaluate(() =>
        window.lineIntakeReviewI18n.text('zh', 'openOriginal')
    );
    await expect(page.locator('[data-review-document-open]')).toContainText(openLabel);
    await expect(page.locator('[data-review-originals]')).toHaveCount(0);
    await page.locator('[data-review-document-open]').click();
    await expect(page.locator('[data-review-document-viewer]')).toBeVisible();
    await page.screenshot({ path: path.join(OUT, 'cowork-mobile-pdf-viewer.png') });
    await page.locator('[data-review-document-close]').click();
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

test('image originals remain inline instead of using the PDF viewer', async ({ browser }) => {
    const page = await browser.newPage({ ...devices['iPhone 13'] });
    const imageRecords = coworkRecords();
    imageRecords[0].filename = 'line-receipt.jpg';
    await openCowork(page, { draftRecords: imageRecords });
    await page.locator('.review-row').click();
    await expect(page.locator('[data-review-document-open]')).toHaveCount(0);
    await expect(page.locator('[data-review-originals]')).toBeVisible();
    await expect(page.locator('.review-original')).toHaveCount(1);
    await expect(page.locator('.review-original img')).toBeVisible();
    await page.screenshot({ path: path.join(OUT, 'cowork-mobile-image-original.png') });
    await page.close();
});

test('shared LINE target selector refreshes in place without stale-cache or click loops', async ({
    page,
}) => {
    await page.setContent('<main id="target"></main><button id="confirm">Confirm</button>');
    await page.addScriptTag({
        path: path.join(__dirname, '../../static/line-intake-review/target-select.js'),
    });
    await page.evaluate(() => {
        const target = {
            endpoint_id: 'express-1',
            workspace_client_id: 69,
            workspace_name: 'Sister Makeup',
            adapter: 'express',
            connection_label: 'Express',
            selected_account_key: 'MAIN-2026',
            account_catalog_loaded: false,
            account_choices: [
                {
                    key: 'MAIN-2026',
                    label: 'MAIN 2026',
                    root_key: '2026',
                    root_label: '2026',
                    writable: true,
                },
            ],
            selectable: true,
            configured: true,
            connection_state: 'online',
            ready_checks: { erp_connection: true, companion_online: true },
            mode_options: ['stock', 'service'],
        };
        const model = {
            targets: [target],
            selection: {
                endpoint_id: 'express-1',
                workspace_client_id: 69,
                adapter: 'express',
                direction: 'purchase',
                posting_kind: 'stock',
                account_root: '2026',
                account_set: 'MAIN-2026',
            },
        };
        const labels = {
            target: '目标',
            erp: 'ERP',
            dataRoot: '年度',
            accountSet: '套账',
            noAccountSet: '无套账',
            loadingAccounts: '正在读取最新 ERP 主档…',
            loadingAccountsLong: '仍在扫描最新 ERP 主档，请保持页面打开…',
            loadAccountsFailed: '加载失败，再点一次重试',
            direction: '业务方向',
            purchase: '采购',
            sales: '销售',
            mode: '模式',
            stock: '库存',
            service: '服务',
            connected: '已连接',
            online: '在线',
            matched: '匹配',
            preflightPending: '待检查',
            blocked: '不可用',
        };
        const escape = (value) =>
            String(value == null ? '' : value).replace(
                /[&<>"']/g,
                (char) =>
                    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]
            );
        const loads = [];
        let loadCount = 0;
        let selector;
        function render() {
            const root = document.getElementById('target');
            root.innerHTML = selector.html();
            selector.bind(root, render);
            document.getElementById('confirm').disabled = !selector.valid();
        }
        selector = window.lineIntakeTargetSelect.create({
            model: () => model,
            text: (key) => labels[key] || key,
            escape,
            loadTarget: () => {
                loadCount += 1;
                return new Promise((resolve, reject) => loads.push({ resolve, reject }));
            },
        });
        window.targetHarness = {
            fullTarget: {
                ...target,
                account_catalog_loaded: true,
                account_choices: [
                    {
                        key: 'MAIN-2024',
                        label: 'MAIN 2024',
                        root_key: '2024',
                        root_label: '2024',
                        writable: true,
                    },
                    {
                        key: 'MAIN-2026',
                        label: 'MAIN 2026',
                        root_key: '2026',
                        root_label: '2026',
                        writable: true,
                    },
                    {
                        key: 'MAIN-2025',
                        label: 'MAIN 2025',
                        root_key: '2025',
                        root_label: '2025',
                        writable: true,
                    },
                ],
            },
            loadCount: () => loadCount,
            resolve: () =>
                loads.shift().resolve({
                    target: window.targetHarness.fullTarget,
                    catalog_refresh_request_id: 'refresh-' + loadCount,
                    catalog_refresh_revision: loadCount,
                }),
            reject: () => loads.shift().reject(new Error('scan failed')),
            selection: () => ({ ...model.selection }),
        };
        render();
    });

    await expect(page.locator('[data-target-root] option')).toHaveCount(2);
    await expect(page.locator('#confirm')).toBeEnabled();
    expect(await page.evaluate(() => window.targetHarness.loadCount())).toBe(0);

    await page.locator('[data-target-root]').dispatchEvent('pointerdown');
    await expect(page.locator('.target-load-state')).toContainText('正在读取最新 ERP 主档…');
    await expect(page.locator('.target-load-state')).toHaveAttribute('role', 'status');
    await expect(page.locator('.target-load-state')).toHaveAttribute('aria-live', 'polite');
    await expect(page.locator('#confirm')).toBeDisabled();
    await expect.poll(() => page.evaluate(() => window.targetHarness.loadCount())).toBe(1);

    await page.evaluate(() => window.targetHarness.resolve());
    await expect(page.locator('.target-load-state')).toHaveCount(0);
    await expect(page.locator('[data-target-root] option')).toHaveText([
        '—',
        '2026',
        '2025',
        '2024',
    ]);
    await expect
        .poll(() => page.evaluate(() => window.targetHarness.selection()))
        .toMatchObject({
            catalog_refresh_request_id: 'refresh-1',
            catalog_refresh_revision: 1,
        });

    await page.locator('[data-target-root]').dispatchEvent('pointerdown');
    await page.locator('[data-target-root]').focus();
    await expect.poll(() => page.evaluate(() => window.targetHarness.loadCount())).toBe(1);
    await page.locator('[data-target-root]').selectOption('2025');
    await expect.poll(() => page.evaluate(() => window.targetHarness.loadCount())).toBe(1);
    await expect(page.locator('[data-target-account-set]')).toHaveValue('');

    await page.locator('[data-target-account-set]').dispatchEvent('pointerdown');
    await expect(page.locator('.target-load-state')).toContainText('正在读取最新 ERP 主档…');
    await expect.poll(() => page.evaluate(() => window.targetHarness.loadCount())).toBe(2);
    await page.evaluate(() => window.targetHarness.resolve());
    await page.locator('[data-target-account-set]').dispatchEvent('pointerdown');
    await page.locator('[data-target-account-set]').focus();
    await page.locator('[data-target-account-set]').selectOption('express-1:69::MAIN-2025');
    await expect(page.locator('#confirm')).toBeEnabled();

    await page.locator('[data-target-root]').dispatchEvent('pointerdown');
    await expect.poll(() => page.evaluate(() => window.targetHarness.loadCount())).toBe(3);
    await page.evaluate(() => window.targetHarness.reject());
    await expect(page.locator('.target-load-error')).toContainText('加载失败，再点一次重试');
    await expect(page.locator('#confirm')).toBeDisabled();
    await expect
        .poll(() => page.evaluate(() => window.targetHarness.selection().account_set))
        .toBe('MAIN-2025');
    await expect
        .poll(() => page.evaluate(() => window.targetHarness.selection()))
        .not.toHaveProperty('catalog_refresh_request_id');

    await page.locator('[data-target-root]').dispatchEvent('pointerdown');
    await expect.poll(() => page.evaluate(() => window.targetHarness.loadCount())).toBe(4);
    await page.evaluate(() => window.targetHarness.resolve());
    await expect(page.locator('.target-load-error')).toHaveCount(0);
    await expect(page.locator('#confirm')).toBeEnabled();
});

test('shared LINE target refresh aborts hung POST and status requests', async ({ page }) => {
    await page.setContent('<main></main>');
    await page.addScriptTag({
        path: path.join(__dirname, '../../static/line-intake-review/target-select.js'),
    });
    const result = await page.evaluate(async () => {
        async function run(postSucceeds) {
            let calls = 0;
            let aborted = false;
            const api = (_path, options) => {
                calls += 1;
                if (postSucceeds && calls === 1) {
                    return Promise.resolve({ request_id: 'request-1' });
                }
                return new Promise((_resolve, reject) => {
                    options.signal.addEventListener('abort', () => {
                        aborted = true;
                        reject(new DOMException('aborted', 'AbortError'));
                    });
                });
            };
            try {
                await window.lineIntakeTargetSelect.refreshTarget(api, '/refresh', {
                    requestTimeoutMs: 10,
                    timeoutMs: 100,
                });
            } catch (error) {
                return { aborted, calls, message: error.message };
            }
            return { aborted, calls, message: '' };
        }
        return { post: await run(false), status: await run(true) };
    });
    expect(result.post).toEqual({
        aborted: true,
        calls: 1,
        message: 'target_refresh_request_timeout',
    });
    expect(result.status).toEqual({
        aborted: true,
        calls: 2,
        message: 'target_refresh_request_timeout',
    });
});
