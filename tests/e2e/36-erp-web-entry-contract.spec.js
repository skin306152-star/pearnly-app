/* global window, document */

const { test, expect, devices } = require('@playwright/test');
const path = require('path');
const fs = require('fs');
const localServer = require('./_local_static_server');

const PORT = 8986;
const BASE = `http://127.0.0.1:${PORT}`;
let server;
const OUT = path.join(__dirname, '_artifacts', 'erp-web-entry');
fs.mkdirSync(OUT, { recursive: true });
const HOME_HTML = fs.readFileSync(path.join(localServer.ROOT, 'home.html'), 'utf8');

const RECOGNIZED = {
    ok: true,
    filename: 'erp-invoice.pdf',
    page_count: 1,
    history_id: 'h1',
    history_ids: ['h1'],
    invoice_count: 1,
    confidence: 'high',
    needs_review: false,
    missed_invoice_warnings: [],
    duplicate_warnings: [],
    pages: [{ page_number: 1, fields: {} }],
    invoices: [
        {
            history_id: 'h1',
            source_index: 1,
            source_total: 1,
            page_indices: [1],
            fields: {
                direction: 'purchase',
                seller_name: 'ERP Supplier',
                seller_tax: '0107537000521',
                invoice_number: 'ERP-001',
                date: '2026-08-28',
                subtotal: '100',
                vat: '7',
                total_amount: '107',
                items: [{ name: 'Widget', qty: '1', price: '100', subtotal: '100' }],
            },
        },
    ],
};

test.beforeAll(async () => {
    server = await localServer.start(PORT, '/home.html');
});
test.afterAll(() => localServer.stop(server));

async function boot(page, entry, state = {}) {
    Object.assign(state, {
        recognizes: [],
        historyPuts: 0,
        commits: 0,
        converts: 0,
        lineCodeCalls: 0,
    });
    await page.addInitScript((portal) => {
        localStorage.clear();
        sessionStorage.clear();
        localStorage.setItem('mrpilot_lang', 'zh');
        localStorage.setItem('pearnly_entry', portal);
        const tokenKey =
            portal === 'erp' || portal === 'cowork' ? `mrpilot_token_${portal}` : 'mrpilot_token';
        localStorage.setItem(tokenKey, `${portal}-e2e-token`);
        localStorage.setItem(`pearnly_active_workspace_client_id_${portal}`, '1');
    }, entry);
    await page.route(/\/erp(?:\?.*)?$/, (route) =>
        route.fulfill({ status: 200, contentType: 'text/html', body: HOME_HTML })
    );
    await page.route('https://api.qrserver.com/**', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'image/svg+xml',
            body: '<svg xmlns="http://www.w3.org/2000/svg" width="140" height="140"><rect width="140" height="140" fill="white"/><path d="M8 8h48v48H8zm76 0h48v48H84zM8 84h48v48H8zm76 0h16v16H84zm24 0h24v48h-24zM76 108h24v24H76z" fill="black"/></svg>',
        })
    );
    await page.route('**/api/**', async (route) => {
        const req = route.request();
        const pathname = new URL(req.url()).pathname;
        let status = 200;
        let body = { ok: true };
        if (pathname === '/api/ocr/recognize') {
            state.recognizes.push((req.postDataBuffer() || Buffer.alloc(0)).toString('utf8'));
            body = state.recognized || RECOGNIZED;
        } else if (pathname === '/api/history/h1' && req.method() === 'PUT') {
            state.historyPuts += 1;
            status =
                state.failSave || (state.failSaveAfterConfirm && state.historyPuts > 2) ? 500 : 200;
        } else if (pathname === '/api/ocr/commit' && req.method() === 'POST') {
            state.commits += 1;
        } else if (pathname === '/api/ocr/convert-documents') {
            state.converts += 1;
            body = {
                converted: [
                    { history_id: 'h1', doc_type: 'purchase', doc_id: 'doc-1', doc_no: 'ERP-001' },
                ],
                skipped: [],
            };
        } else if (pathname === '/api/purchase/docs') {
            body = { docs: [], summary: null };
        } else if (pathname === '/api/purchase/categories') {
            body = { categories: [] };
        } else if (pathname === '/api/sales/documents') {
            body = { documents: [] };
        } else if (pathname === '/api/workspace/clients') {
            body = { clients: [{ id: 1, name: 'ERP Branch' }] };
        } else if (pathname === '/api/me') {
            body = {
                id: 'u1',
                tenant_id: 't1',
                username: 'erp-owner',
                is_super_admin: false,
                ocr_async_web: false,
            };
        } else if (pathname === '/api/me/modules') {
            body = { data: { modules: {}, business_type: 'firm', entry } };
        } else if (pathname === '/api/erp/endpoints') {
            body = { items: [] };
        } else if (pathname === '/api/line/erp/binding') {
            body = {
                ok: true,
                data: state.lineBound
                    ? {
                          bound: true,
                          display_name: 'Zihao LINE',
                          bound_at: '2026-08-28T03:00:00Z',
                      }
                    : { bound: false },
            };
        } else if (pathname === '/api/line/erp/binding-code') {
            state.lineCodeCalls += 1;
            body = {
                ok: true,
                data: {
                    code: '482913',
                    expires_at: new Date(Date.now() + 600_000).toISOString(),
                    bot_basic_id: '@063eadty',
                    bot_friend_url: 'https://line.me/R/ti/p/@063eadty',
                },
            };
        }
        return route.fulfill({
            status,
            contentType: 'application/json',
            body: JSON.stringify(body),
        });
    });
    const canonical = entry === 'erp' || entry === 'cowork' ? `?canonical=${entry}` : '';
    await page.goto(`${BASE}/home.html${canonical}`, { waitUntil: 'domcontentloaded' });
    if (entry === 'erp' || entry === 'cowork') {
        await page.waitForURL((url) => url.pathname === `/${entry}`);
    }
    await page.waitForFunction(() => typeof window.routeTo === 'function', { timeout: 20_000 });
    await page.evaluate((portal) => {
        window._entry = portal;
        window.isOwner = () => true;
        window.getActiveWorkspaceClientId = () => 1;
        document.body.classList.remove('workspace-gate-preboot');
        document.getElementById('workspace-gate-root')?.remove();
        const style = document.createElement('style');
        style.textContent = '#ws-modal,#workspace-gate-root{display:none!important;}';
        document.head.appendChild(style);
    }, entry);
    await page.waitForFunction(() => !document.body.classList.contains('lang-switching'));
}

async function revealShell(page) {
    await page.evaluate(() => {
        document.body.classList.remove('workspace-gate-preboot', 'lang-switching');
        document
            .querySelectorAll('#workspace-gate-root,#ws-modal,.lang-switching-overlay')
            .forEach((node) => node.remove());
    });
    await page.waitForTimeout(150);
}

test('ERP purchase and sales buttons open the shared intake with an explicit direction', async ({
    page,
}) => {
    await boot(page, 'erp');

    await page.evaluate(() => window.routeTo('purchase'));
    await page.waitForSelector('#pur-record-btn');
    await page.click('#pur-record-btn');
    await page.waitForSelector('#dx-inv-drop');
    await page.click('[data-iv-dir="purchase"]');
    await expect(page.locator('[data-iv-dir="purchase"]')).toHaveClass(/active/);
    await expect(page.locator('[data-iv-dir="sales"]')).toHaveCount(0);
    await revealShell(page);
    await page.screenshot({
        path: path.join(OUT, 'purchase-entry.png'),
        fullPage: true,
        animations: 'disabled',
    });
    expect(await page.evaluate(() => sessionStorage.getItem('pearnly_erp_intake_direction'))).toBe(
        'purchase'
    );
    await expect(page.locator('[data-task="summary_batch"]')).toHaveCount(0);

    await page.evaluate(() => window.routeTo('sales-invoices'));
    await page.waitForSelector('#sx-upload-btn');
    await page.click('#sx-upload-btn');
    await page.waitForSelector('#dx-inv-drop');
    await revealShell(page);
    await page.screenshot({
        path: path.join(OUT, 'sales-entry.png'),
        fullPage: true,
        animations: 'disabled',
    });
    expect(await page.evaluate(() => sessionStorage.getItem('pearnly_erp_intake_direction'))).toBe(
        'sales'
    );
});

test('ERP finish save failure stays in review without commit or result success', async ({
    page,
}) => {
    const state = { failSaveAfterConfirm: true };
    await boot(page, 'erp', state);
    await page.evaluate(() => window.routeTo('purchase'));
    await page.waitForSelector('#pur-record-btn');
    await page.click('#pur-record-btn');
    await page.setInputFiles('#dx-inv-file', {
        name: 'erp-invoice.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('invoice'),
    });
    await page.click('#dx-inv-start');
    await page.waitForSelector('#dx-s-inv-review.active');
    await page.locator('select.dx-item-type').selectOption('stock');
    await page.click('.dx-confirm-one');
    await expect.poll(() => state.historyPuts).toBe(1);
    await expect.poll(() => state.converts).toBe(1);
    await page.click('#dx-inv-rev-next');
    await page.waitForSelector('#dx-s-inv-submit.active');
    await expect.poll(() => state.historyPuts).toBe(2);
    await page.click('#dx-inv-finish');
    await expect.poll(() => state.historyPuts).toBe(3);
    expect(state.commits).toBe(0);
    expect(state.converts).toBe(1);
    await expect(page.locator('#dx-s-inv-review')).toHaveCount(1);
    await expect(page.locator('#dx-s-success.active')).toHaveCount(0);
});

test('ERP review save failure does not create a formal document', async ({ page }) => {
    const state = { failSave: true };
    await boot(page, 'erp', state);
    await page.evaluate(() => window.routeTo('purchase'));
    await page.waitForSelector('#pur-record-btn');
    await page.click('#pur-record-btn');
    await page.setInputFiles('#dx-inv-file', {
        name: 'erp-invoice.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('invoice'),
    });
    await page.click('#dx-inv-start');
    await page.waitForSelector('#dx-s-inv-review.active');
    await page.locator('select.dx-item-type').selectOption('stock');
    await page.click('.dx-confirm-one');
    await expect.poll(() => state.historyPuts).toBe(1);
    expect(state.converts).toBe(0);
    expect(state.recognizes).toHaveLength(1);
    expect(state.recognizes[0]).toContain('name="direction"');
    expect(state.recognizes[0]).toContain('purchase');
    await expect(page.locator('.dx-acc-item.open')).toBeVisible();
    await expect(page.locator('.dx-pill')).not.toContainText('已确认');
    await revealShell(page);
    await page.screenshot({
        path: path.join(OUT, 'save-failure-review.png'),
        fullPage: true,
        animations: 'disabled',
    });
});

test('ERP web leaves missing OCR item values blank and blocks confirmation', async ({ page }) => {
    const recognized = JSON.parse(JSON.stringify(RECOGNIZED));
    recognized.invoices[0].fields.items = [];
    const state = { recognized };
    await boot(page, 'erp', state);
    await page.evaluate(() => window.routeTo('purchase'));
    await page.click('#pur-record-btn');
    await page.setInputFiles('#dx-inv-file', {
        name: 'empty-lines.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('invoice'),
    });
    await page.click('#dx-inv-start');
    await page.waitForSelector('#dx-s-inv-review.active');
    const itemValues = await page
        .locator('.dx-item-in')
        .evaluateAll((nodes) => nodes.map((node) => node.value));
    expect(itemValues).toEqual(['', '', '', '']);
    await page.click('.dx-confirm-one');
    expect(state.historyPuts).toBe(0);
    expect(state.converts).toBe(0);
});

test('non-ERP keeps the task picker and the original purchase capture route', async ({ page }) => {
    await boot(page, 'firm');
    await page.evaluate(() => window.routeTo('dms-intake'));
    await page.waitForSelector('[data-task="summary_batch"]');
    await expect(page.locator('[data-task]')).toHaveCount(2);

    await page.evaluate(() => window.routeTo('purchase'));
    await page.waitForSelector('#pur-record-btn');
    await page.click('#pur-record-btn');
    await expect(page.locator('#page-purchase-capture')).toHaveClass(/active/);
    expect(
        await page.evaluate(() => sessionStorage.getItem('pearnly_erp_intake_direction'))
    ).toBeNull();
});

test('ERP purchase entry remains touch-sized on mobile', async ({ browser }) => {
    const page = await browser.newPage({ ...devices['iPhone 13'] });
    await boot(page, 'erp');
    await page.evaluate(() => window.routeTo('purchase'));
    await page.waitForSelector('#pur-record-btn');
    await page.click('#pur-record-btn');
    await page.waitForSelector('#dx-inv-drop');
    await expect(page.locator('#dx-inv-pick')).toBeVisible();
    const tapHeight = await page
        .locator('#dx-inv-pick')
        .evaluate((node) => node.getBoundingClientRect().height);
    expect(tapHeight).toBeGreaterThanOrEqual(44);
    await revealShell(page);
    await page.screenshot({
        path: path.join(OUT, 'purchase-entry-mobile.png'),
        fullPage: true,
        animations: 'disabled',
    });
    await page.close();
});

test('ERP integration reuses the established LINE binding card with its own bot', async ({
    page,
}) => {
    const state = {};
    await boot(page, 'erp', state);
    await page.evaluate(() => window.routeTo('integrations'));
    await expect(page.locator('#erp-linebot-unbound')).toBeVisible();
    await expect(page.locator('#erp-linebot-code')).toHaveText('482913');
    await expect(page.locator('#erp-linebot-bot-id')).toHaveText('@063eadty');
    await expect(page.locator('#erp-linebot-open-line')).toHaveAttribute(
        'href',
        'https://line.me/R/ti/p/@063eadty'
    );
    await expect(page.locator('#erp-linebot-qr img')).toHaveAttribute(
        'src',
        /data=https%3A%2F%2Fline\.me%2FR%2Fti%2Fp%2F%40063eadty/
    );
    expect(state.lineCodeCalls).toBeGreaterThanOrEqual(1);
    await revealShell(page);
    await page.screenshot({
        path: path.join(OUT, 'line-binding-desktop.png'),
        fullPage: true,
        animations: 'disabled',
    });
});

test('ERP LINE binding card has a truthful bound state and touch-sized mobile actions', async ({
    browser,
}) => {
    const unboundPage = await browser.newPage({ ...devices['iPhone 13'] });
    await boot(unboundPage, 'erp');
    await unboundPage.evaluate(() => window.routeTo('integrations'));
    await expect(unboundPage.locator('#erp-linebot-code-refresh')).toBeVisible();
    const tapHeight = await unboundPage
        .locator('#erp-linebot-code-refresh')
        .evaluate((node) => node.getBoundingClientRect().height);
    expect(tapHeight).toBeGreaterThanOrEqual(44);
    await revealShell(unboundPage);
    await unboundPage.screenshot({
        path: path.join(OUT, 'line-binding-mobile.png'),
        fullPage: true,
        animations: 'disabled',
    });
    await unboundPage.close();

    const boundPage = await browser.newPage();
    await boot(boundPage, 'erp', { lineBound: true });
    await boundPage.evaluate(() => window.routeTo('integrations'));
    await expect(boundPage.locator('#erp-linebot-bound')).toBeVisible();
    await expect(boundPage.locator('#erp-linebot-bound-name')).toHaveText('Zihao LINE');
    await expect(boundPage.locator('#erp-linebot-unbound')).toBeHidden();
    await boundPage.close();
});
