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

const SALES_RECORDS = [
    {
        id: 'sale-line-1',
        doc_type: 'tax_invoice',
        doc_number: 'S-2026-018',
        issue_date: '2026-08-18',
        status: 'issued',
        subtotal: '1000.00',
        grand_total: '1070.00',
        vat_amount: '70.00',
        buyer: { name: 'Customer A' },
        payment: { status: 'unpaid', paid_amount: '0' },
        ocr_history_id: 'history-sales-1',
        source: 'line_erp',
        push_status: 'not_pushed',
        lines: [
            { description: 'Coffee beans', item_type: 'goods', qty: '2', unit_price: '400' },
            { description: 'Delivery', item_type: 'service', qty: '1', unit_price: '200' },
        ],
    },
    {
        id: 'sale-web-2',
        doc_type: 'receipt',
        doc_number: 'R-2026-044',
        issue_date: '2026-08-12',
        status: 'issued',
        subtotal: '500.00',
        grand_total: '535.00',
        vat_amount: '35.00',
        buyer: { name: 'Walk-in Customer' },
        payment: { status: 'paid', paid_amount: '535' },
        ocr_history_id: 'history-sales-2',
        source: 'erp_web',
        push_status: 'success',
        lines: [{ description: 'Consulting', item_type: 'service', qty: '1', unit_price: '500' }],
    },
];

test.beforeAll(async () => {
    server = await localServer.start(PORT, '/home.html');
});
test.afterAll(() => localServer.stop(server));

async function boot(page, entry, state = {}) {
    if (!state.salesDocuments) state.salesDocuments = JSON.parse(JSON.stringify(SALES_RECORDS));
    Object.assign(state, {
        recognizes: [],
        historyPuts: 0,
        commits: 0,
        converts: 0,
        lineCodeCalls: 0,
        erpPushes: 0,
        erpPushBodies: [],
        salesExports: [],
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
    await page.route(/\/(?:erp|cowork)(?:\?.*)?$/, (route) =>
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
        } else if (pathname === '/api/purchase/docs/purchase-1') {
            body = {
                ok: true,
                data: {
                    doc: {
                        id: 'purchase-1',
                        doc_kind: 'purchase_invoice',
                        status: 'posted',
                        doc_no: 'P-2026-031',
                        doc_date: '2026-08-20',
                        has_vat: true,
                        currency: 'THB',
                        source: 'upload',
                        subtotal: 1000,
                        vat_amount: 70,
                        grand_total: 1070,
                        net_payable: 1070,
                        paid_amount: 0,
                        payment_status: 'unpaid',
                        ocr_history_id: 'history-purchase-1',
                    },
                    lines: [
                        {
                            id: 'line-1',
                            item_type: 'goods',
                            description: 'Coffee beans',
                            qty: 2,
                            unit_price: 500,
                            vat_rate: 7,
                        },
                    ],
                    attachments: [],
                },
            };
        } else if (pathname === '/api/purchase/categories') {
            body = { categories: [] };
        } else if (pathname === '/api/sales/documents') {
            body = { documents: state.salesDocuments || SALES_RECORDS };
        } else if (pathname === '/api/ocr/export-by-history-ids') {
            state.salesExports.push(req.postDataJSON());
            return route.fulfill({
                status: 200,
                contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                body: Buffer.from('xlsx'),
            });
        } else if (pathname.startsWith('/api/sales/documents/')) {
            const id = pathname.split('/').pop();
            body = {
                document: (state.salesDocuments || SALES_RECORDS).find((doc) => doc.id === id),
            };
        } else if (/^\/api\/history\/[^/]+\/page\/1\.png$/.test(pathname)) {
            return route.fulfill({
                status: 200,
                contentType: 'image/jpeg',
                body: fs.readFileSync(
                    path.join(
                        __dirname,
                        '..',
                        'fixtures',
                        'messy_intake_pack',
                        'normal_receipt.jpg'
                    )
                ),
            });
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
            body = {
                data: {
                    modules: state.modules || {},
                    business_type: state.businessType || 'firm',
                    entry,
                },
            };
        } else if (pathname === '/api/erp/test-connection') {
            state.mrerpTestAuth = req.headers().authorization || '';
            body = {
                ok: true,
                companies: [{ comidyear: '6', seldb: '1', label: 'TEST2019' }],
            };
        } else if (pathname === '/api/erp/endpoints' && req.method() === 'POST') {
            state.mrerpSaveAuth = req.headers().authorization || '';
            const input = req.postDataJSON();
            const saved = { id: 'mrerp-1', enabled: true, ...input };
            state.erpEndpoints = [...(state.erpEndpoints || []), saved];
            body = saved;
        } else if (pathname === '/api/erp/endpoints') {
            body = { items: state.erpEndpoints || [] };
        } else if (pathname === '/api/erp/push') {
            state.erpPushes += 1;
            state.erpPushBodies.push(req.postDataJSON());
            const response = state.erpPushResponses?.shift() || { ok: true };
            const pending = state.salesDocuments.find((doc) => doc.push_status !== 'success');
            if (pending)
                pending.push_status =
                    response.status || (response.ok === true ? 'success' : 'failed');
            body = response;
        } else if (pathname === '/api/integrations/google/status') {
            body = {
                ok: true,
                data: { configured: true, connected: false, email: '', scope: '' },
            };
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

test('ERP purchase and sales record buttons open the shared intake with an explicit direction', async ({
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
    await page.waitForSelector('#sx-new-btn');
    await expect(page.locator('#sx-upload-btn')).toHaveCount(0);
    await expect(page.locator('#sx-record-btn')).toHaveCount(0);

    await page.evaluate(() => window.routeTo('sales-records'));
    await page.waitForSelector('#sr-record-btn');
    await expect(page.locator('#sx-new-btn')).toHaveCount(0);
    await page.click('#sr-record-btn');
    await page.waitForSelector('#dx-inv-drop');
    await revealShell(page);
    await page.screenshot({
        path: path.join(OUT, 'sales-record-entry.png'),
        fullPage: true,
        animations: 'disabled',
    });
    expect(await page.evaluate(() => sessionStorage.getItem('pearnly_erp_intake_direction'))).toBe(
        'sales'
    );
});

test('ERP MR.ERP setup uses the isolated ERP session and refreshes its card immediately', async ({
    page,
}) => {
    const state = { erpEndpoints: [] };
    await boot(page, 'erp', state);
    await page.evaluate(() => {
        localStorage.setItem('mrpilot_token', 'wrong-legacy-token');
        window.routeTo('purchase');
    });
    await page.click('#pur-record-btn');
    await expect(page.locator('[data-erp="mrerp"] [data-erp-status]')).toHaveText('未连接');
    await page.click('[data-erp="mrerp"] [data-erp-config]');
    await page.fill('[data-mw-user]', 'sandbox-user');
    await page.fill('[data-mw-pass]', 'sandbox-password');
    await page.click('[data-mw-test]');
    await expect(page.locator('[data-mw-test-status]')).toContainText('1');
    await page.click('[data-mw-next]');
    await page.click('[data-mw-next]');

    await expect.poll(() => state.mrerpTestAuth).toBe('Bearer erp-e2e-token');
    await expect.poll(() => state.mrerpSaveAuth).toBe('Bearer erp-e2e-token');
    await expect(page.locator('[data-erp="mrerp"] [data-erp-status]')).toContainText('已连接');
});

test('ERP gets sales-system labels and records while POS keeps its invoicing menu', async ({
    browser,
}) => {
    const erpPage = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    const erpState = {
        businessType: 'pos_only',
        erpEndpoints: [
            { id: 'express-1', name: 'Express ERP', adapter: 'express', is_default: true },
        ],
        erpPushResponses: [{ ok: true, status: 'pending' }, { ok: true }],
    };
    await boot(erpPage, 'erp', erpState);
    await erpPage.waitForFunction(
        () => document.querySelector('#nav-sales-records')?.getBoundingClientRect().height > 0
    );
    await expect(
        erpPage.locator('[data-collapsible="sales"] > .nav-group-toggle > .nav-label')
    ).toHaveText('销售系统');
    await expect(erpPage.locator('.nav-item[data-route="sales-invoices"] .nav-label')).toHaveText(
        '销售发票'
    );
    await expect(erpPage.locator('#nav-sales-records .nav-label')).toHaveText('销售记录');
    await expect(erpPage.locator('.nav-item[data-route="sales-account"] .nav-label')).toHaveText(
        '开票资料'
    );
    expect(
        await erpPage.evaluate(() => {
            const records = document.getElementById('nav-sales-records');
            const invoices = document.querySelector('[data-route="sales-invoices"]');
            const documentPositionFollowing = 4;
            return Boolean(
                records &&
                invoices &&
                records.compareDocumentPosition(invoices) & documentPositionFollowing
            );
        }),
        'ERP 侧栏应先显示销售记录，再显示销售发票'
    ).toBe(true);
    const erpLabels = await erpPage.evaluate(() => {
        const selectors = {
            'nav-group-sales': '[data-collapsible="sales"] > .nav-group-toggle > .nav-label',
            'nav-sales-workbench-erp': '.nav-item[data-route="sales-invoices"] .nav-label',
            'nav-sales-records': '#nav-sales-records .nav-label',
            'nav-sales-account-erp': '.nav-item[data-route="sales-account"] .nav-label',
        };
        const values = {};
        for (const lang of ['zh', 'en', 'th', 'ja']) {
            window.applyLang(lang);
            values[lang] = Object.fromEntries(
                Object.entries(selectors).map(([key, selector]) => [
                    key,
                    {
                        actual: document.querySelector(selector)?.textContent,
                        expected: window.I18N[lang][key],
                    },
                ])
            );
        }
        window.applyLang('zh');
        return values;
    });
    for (const lang of ['zh', 'en', 'th', 'ja']) {
        for (const value of Object.values(erpLabels[lang])) {
            expect(value.actual).toBe(value.expected);
        }
    }
    await erpPage.evaluate(() => window.routeTo('purchase'));
    await expect(erpPage.locator('#pur-export-btn')).toBeVisible();
    await expect(erpPage.locator('#pur-record-btn')).toBeVisible();
    await expect(erpPage.locator('#page-purchase .more-wrap')).toHaveCount(0);
    await expect(erpPage.locator('#pur-line-btn')).toHaveCount(0);
    expect(
        await erpPage
            .locator('#page-purchase .acts > .btn')
            .evaluateAll((buttons) => buttons.map((button) => button.id))
    ).toEqual(['pur-export-btn', 'pur-record-btn']);
    await revealShell(erpPage);
    await erpPage.screenshot({
        path: path.join(OUT, 'purchase-records-actions.png'),
        fullPage: true,
        animations: 'disabled',
    });
    await erpPage.evaluate(() => window.routeTo('sales-records'));
    await expect(erpPage.locator('#sr-record-btn')).toBeVisible();
    await expect(erpPage.locator('#sr-export-btn')).toBeVisible();
    await expect(erpPage.locator('#page-sales-records .more-wrap')).toHaveCount(0);
    await expect(erpPage.locator('#sr-line-btn, #sr-logs-btn')).toHaveCount(0);
    expect(
        await erpPage
            .locator('#page-sales-records .acts > .btn')
            .evaluateAll((buttons) => buttons.map((button) => button.id))
    ).toEqual(['sr-export-btn', 'sr-record-btn']);
    await expect(erpPage.locator('.pur.pl.sr')).toBeVisible();
    await expect(erpPage.locator('[data-sr-doc]')).toHaveCount(2);
    await expect(erpPage.locator('#sr-body .src.line')).toHaveText('LINE 上传');
    await expect(erpPage.locator('#sr-body .src.web')).toHaveText('网页上传');
    await expect(erpPage.locator('[data-sr-push="sale-line-1"]')).toHaveText('推送 ERP');
    await erpPage.locator('[data-sr-basis="upload"]').click();
    await expect(erpPage.locator('[data-sr-basis="upload"]')).toHaveClass(/on/);
    await revealShell(erpPage);
    await erpPage.screenshot({
        path: path.join(OUT, 'sales-records-desktop.png'),
        fullPage: true,
        animations: 'disabled',
    });
    await erpPage.locator('#sr-export-btn').click();
    await expect(erpPage.locator('#page-purchase-export')).toHaveClass(/active/);
    await expect(erpPage.locator('#page-purchase-export .ph .t')).toHaveText(
        '销售记录导出 / 归档到 Google'
    );
    await expect(erpPage.locator('[data-fmt="drive"]')).toBeVisible();
    await expect(erpPage.locator('[data-fmt="sheet"]')).toHaveCount(0);
    await revealShell(erpPage);
    await erpPage.screenshot({
        path: path.join(OUT, 'sales-export-archive.png'),
        fullPage: true,
        animations: 'disabled',
    });
    await erpPage.locator('[data-fmt="excel"]').click();
    await expect.poll(() => erpState.salesExports.length).toBe(1);
    expect(erpState.salesExports[0].history_ids).toEqual(['history-sales-1', 'history-sales-2']);
    await erpPage.locator('#pex-back').click();
    await expect(erpPage.locator('#page-sales-records')).toHaveClass(/active/);
    await erpPage.locator('[data-sr-push="sale-line-1"]').click();
    await expect.poll(() => erpState.erpPushes).toBe(1);
    await expect(erpPage.locator('#mp-toast-wrap .mp-toast.info').last()).toContainText(
        '待 Agent 录入'
    );
    expect(erpState.erpPushBodies[0].operation_id).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
    );
    await erpPage.locator('[data-sr-doc="sale-line-1"]').click();
    await expect(erpPage.locator('#page-sales-record-detail')).toHaveClass(/active/);
    await expect(erpPage.locator('.srd .ph .t')).toContainText('销售单据详情');
    await expect(erpPage.locator('#srd-original-img img')).toBeVisible();
    await erpPage.waitForFunction(
        () => document.querySelector('#srd-original-img img')?.naturalWidth > 0
    );
    await expect(erpPage.locator('.srd')).toContainText('Customer A');
    await expect(erpPage.locator('.srd')).toContainText('Coffee beans');
    await expect(erpPage.locator('.srd')).toContainText('商品');
    await expect(erpPage.locator('.srd')).toContainText('服务');
    for (const invoiceAction of [
        '下载PDF',
        '打印',
        '发送给买家',
        '付款二维码',
        '复制再开',
        '红冲',
        '补开',
    ]) {
        await expect(erpPage.getByText(invoiceAction, { exact: true })).toHaveCount(0);
    }
    await revealShell(erpPage);
    await erpPage.screenshot({
        path: path.join(OUT, 'sales-record-detail.png'),
        fullPage: true,
        animations: 'disabled',
    });
    await erpPage.evaluate(() => window.openPurchaseDetail('purchase-1'));
    await expect(erpPage.locator('#pur-erp-push')).toBeVisible();
    await expect(erpPage.locator('[data-erp-push-state="not_pushed"]')).toHaveText('推送 ERP');
    await erpPage.locator('#pur-erp-push').click();
    await expect.poll(() => erpState.erpPushes).toBe(2);
    await expect(erpPage.locator('#mp-toast-wrap .mp-toast.success').last()).toContainText('成功');
    expect(erpState.erpPushBodies[1].history_id).toBe('history-purchase-1');
    expect(erpState.erpPushBodies[1].operation_id).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
    );
    await revealShell(erpPage);
    await erpPage.screenshot({
        path: path.join(OUT, 'purchase-record-detail.png'),
        fullPage: true,
        animations: 'disabled',
    });
    await erpPage.close();

    const posPage = await browser.newPage();
    await boot(posPage, 'pos', {
        businessType: 'pos_only',
        modules: { pos: { enabled: true }, inventory: { enabled: true } },
    });
    await posPage.waitForFunction(
        () =>
            document
                .querySelector('[data-collapsible="sales"] > .nav-group-toggle > .nav-label')
                ?.getAttribute('data-i18n') === 'nav-group-sales-pos'
    );
    await expect(
        posPage.locator('[data-collapsible="sales"] > .nav-group-toggle > .nav-label')
    ).toHaveText('发票系统');
    await expect(posPage.locator('.nav-item[data-route="sales-invoices"] .nav-label')).toHaveText(
        '销售发票'
    );
    await expect(posPage.locator('#nav-sales-records')).toBeHidden();
    await posPage.evaluate(() => window.routeTo('sales-invoices'));
    await expect(posPage.locator('#sx-wb-body [data-doc]')).toHaveCount(4);
    await posPage.locator('#sx-wb-body [data-doc]').first().click();
    await expect(posPage.locator('#sales-detail-mask')).toBeVisible();
    await expect(posPage.getByText('下载PDF', { exact: true })).toBeVisible();
    await posPage.close();
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

test('ERP sales cannot finish before confirmation creates the formal document', async ({
    page,
}) => {
    const state = {};
    await boot(page, 'erp', state);
    await page.evaluate(() => window.routeTo('sales-records'));
    await page.click('#sr-record-btn');
    await page.setInputFiles('#dx-inv-file', {
        name: 'erp-sales.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('sales'),
    });
    await page.click('#dx-inv-start');
    await page.waitForSelector('#dx-s-inv-review.active');
    await page.locator('select.dx-item-type').selectOption('service');

    await page.click('#dx-inv-rev-next');
    await expect(page.locator('#dx-s-inv-review.active')).toBeVisible();
    await expect(page.locator('#dx-s-inv-submit.active')).toHaveCount(0);
    expect(state.converts).toBe(0);
    expect(state.commits).toBe(0);
    await expect(page.locator('#mp-toast-wrap')).toContainText('请先逐张确认单据');
    await revealShell(page);
    await page.screenshot({
        path: path.join(OUT, 'sales-unconfirmed-blocked.png'),
        fullPage: true,
        animations: 'disabled',
    });

    await page.click('.dx-confirm-one');
    await expect.poll(() => state.converts).toBe(1);
    await page.click('#dx-inv-rev-next');
    await expect(page.locator('#dx-s-inv-submit.active')).toBeVisible();
    await page.click('#dx-inv-finish');
    await expect.poll(() => state.commits).toBe(1);
    expect(state.recognizes[0]).toContain('sales');
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

test('ERP sales records remains touch-sized on mobile', async ({ browser }) => {
    const page = await browser.newPage({ ...devices['iPhone 13'] });
    await boot(page, 'erp', { businessType: 'pos_only' });
    await page.evaluate(() => window.routeTo('sales-records'));
    await expect(page.locator('#sr-record-btn')).toBeVisible();
    const tapHeight = await page
        .locator('#sr-record-btn')
        .evaluate((node) => node.getBoundingClientRect().height);
    expect(tapHeight).toBeGreaterThanOrEqual(44);
    const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth
    );
    expect(overflow).toBeLessThanOrEqual(1);
    await revealShell(page);
    await page.screenshot({
        path: path.join(OUT, 'sales-records-mobile.png'),
        fullPage: true,
        animations: 'disabled',
    });
    await page.close();
});

test('cowork desktop and ERP mobile render the same shared Express status card', async ({
    browser,
}) => {
    const endpoint = {
        id: 'express-shared-1',
        name: 'Express Shared',
        adapter: 'express',
        enabled: true,
        shared_scope: true,
        account_set: 'TEST2026',
        connection_state: 'online',
        binding_generation: 1,
        bound_account_set: 'TEST2026',
        bound_profile_key: 'profile-1',
        live_account_set: 'TEST2026',
        live_profile_key: 'profile-1',
        agent_last_seen_at: new Date().toISOString(),
        config: {},
        last_seen_at: '2026-08-31T10:00:00Z',
        agent_version: '1.1.64',
    };
    const cases = [
        {
            entry: 'cowork',
            viewport: { width: 1280, height: 900 },
            shot: 'cowork-express-desktop.png',
        },
        { entry: 'erp', viewport: { width: 390, height: 844 }, shot: 'erp-express-mobile.png' },
    ];
    for (const item of cases) {
        const page = await browser.newPage({ viewport: item.viewport });
        await boot(page, item.entry, { erpEndpoints: [endpoint] });
        if (item.entry === 'erp') {
            await page.evaluate(() => window.routeTo('purchase'));
            await page.click('#pur-record-btn');
        } else {
            await page.evaluate(() => window.routeTo('dms-intake'));
            await page.click('[data-task="invoice"]');
        }
        const card = page.locator('[data-erp="express"]');
        await expect(card).toBeVisible();
        await expect(card.locator('[data-erp-status]')).toContainText('已连接');
        await expect(card.locator('[data-erp-status]')).toContainText('TEST2026');
        await expect(card.locator('[data-erp-toggle]')).toHaveCount(1);
        await revealShell(page);
        await page.screenshot({
            path: path.join(OUT, item.shot),
            fullPage: true,
            animations: 'disabled',
        });
        await page.close();
    }
});

test('ERP integration reuses the established LINE binding card with its own bot', async ({
    page,
}) => {
    const state = {};
    await boot(page, 'erp', state);
    await page.evaluate(() => window.routeTo('integrations'));
    await expect(page.locator('#erp-express-connect')).toHaveCount(0);
    await expect(page.getByText('第三方 ERP')).toHaveCount(0);
    await expect(page.locator('#erp-linebot-unbound')).toBeVisible();
    await expect(page.locator('#page-integrations .page-head-title')).toHaveText('LINE 集成');
    await expect(page.locator('#page-integrations .page-head-sub')).toHaveText(
        '采购与销售单据的专用上传入口'
    );
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
