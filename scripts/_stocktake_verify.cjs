// Run against the local real pages router (STOCKTAKE_BASE), with API fixtures and a real EAN video.
// Uses production dictionaries and assets. LINE SDK is simulated; this does not prove native LINE acceptance.
const { chromium, expect } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const BASE = process.env.STOCKTAKE_BASE || 'http://127.0.0.1:8943';
const ART = path.resolve('tests/e2e/_artifacts/stocktake');
const taskId = 'ae5be78c-c5ce-4f30-a2c6-dd5d43090f11';
const barcode = '8850999320014';
const qrCode = 'COMPANY-QR-001';
const item = (id, loc, qty = null) => ({
    id,
    product_code: id === 'row-a' ? '0012' : '0013',
    product_name: id === 'row-a' ? 'น้ำดื่ม / 饮用水' : 'Internal QR product',
    barcode: id === 'row-a' ? barcode : qrCode,
    warehouse: 'Main',
    location: loc,
    unit: 'EA',
    book_qty: '12.500000',
    actual_qty: qty,
    difference: qty === null ? null : String(Number(qty) - 12.5),
    version: 0,
});
const initial = () => ({
    id: taskId,
    name: 'September warehouse count',
    status: 'active',
    count_mode: 'scan',
    entries: [],
    entry_total: 0,
    places: [],
    items: [item('row-a', 'A01'), item('row-b', 'A02')],
});
const json = (body, status = 200) => ({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
});
async function stub(context, state, mobile = false) {
    await context.route('**/api/**', async (route) => {
        const req = route.request();
        const p = new URL(req.url()).pathname;
        if (p.startsWith('/api/cowork/stocktakes') && !p.endsWith('/line/auth')) {
            const h = req.headers();
            assert.equal(
                h.authorization,
                mobile ? 'Bearer line-scoped-test' : 'Bearer cowork-test'
            );
            if (p !== '/api/cowork/stocktakes/workspaces')
                assert.equal(h['x-workspace-client-id'], '101');
        }
        if (p === '/api/me')
            return route.fulfill(
                json({
                    id: 'u1',
                    role: 'owner',
                    is_owner: true,
                    tenant_role: 'owner',
                    username: 'Warehouse manager',
                    is_super_admin: false,
                })
            );
        if (p === '/api/me/modules')
            return route.fulfill(
                json({ data: { modules: {}, business_type: 'firm', entry: 'cowork' } })
            );
        if (p === '/api/workspace/clients' || p === '/api/cowork/stocktakes/workspaces')
            return route.fulfill(json({ clients: [{ id: 101, name: 'Test company' }] }));
        if (p === '/api/cowork-line/intake/liff/config')
            return route.fulfill(json({ liff_id: '123-cowork' }));
        if (p === '/api/cowork/stocktakes/line/auth')
            return route.fulfill(json({ token: 'line-scoped-test' }));
        if (p === '/api/cowork/stocktakes') {
            if (req.method() === 'POST') {
                state.imported = req.postDataBuffer().toString().includes('request_id');
                return route.fulfill(json({ id: taskId }));
            }
            return route.fulfill(
                json({
                    tasks: [
                        {
                            ...state.task,
                            total: 2,
                            counted: state.task.items.filter((r) => r.actual_qty !== null).length,
                            differences: 1,
                        },
                    ],
                })
            );
        }
        if (p === '/api/cowork/stocktakes/' + taskId) return route.fulfill(json(state.task));
        if (p.endsWith('/entries') && req.method() === 'GET')
            return route.fulfill(
                json({ entries: state.task.entries, total: state.task.entry_total })
            );
        if (
            (p.includes('/items/') && p.endsWith('/entries')) ||
            (p.includes('/entries/') && req.method() === 'PATCH')
        ) {
            const body = req.postDataJSON();
            state.requests = [...(state.requests || []), body.request_id];
            if (!state.requests.slice(0, -1).includes(body.request_id)) {
                if (req.method() === 'PATCH') {
                    const entry = state.task.entries.find((e) => e.id === p.split('/').pop());
                    assert.equal(body.version, entry.version);
                    Object.assign(entry, body, { version: entry.version + 1 });
                } else {
                    const product = state.task.items.find((i) =>
                        p.includes('/items/' + i.id + '/')
                    );
                    state.task.entries.unshift({
                        ...product,
                        ...body,
                        id: body.request_id,
                        item_id: product.id,
                        voided: false,
                        counted_by_name: 'Counter',
                        counted_at: new Date().toISOString(),
                        version: 0,
                    });
                }
                state.task.entry_total = state.task.entries.length;
                for (const product of state.task.items) {
                    const active = state.task.entries.filter(
                        (e) => e.item_id === product.id && !e.voided
                    );
                    product.actual_qty = active.length
                        ? String(active.reduce((sum, e) => sum + Number(e.quantity), 0))
                        : null;
                    product.difference =
                        product.actual_qty === null
                            ? null
                            : String(Number(product.actual_qty) - 12.5);
                }
                state.task.places = state.task.entries.filter((e) => !e.voided);
            }
            if (state.failAfterWrite) {
                state.failAfterWrite = false;
                return route.abort('failed');
            }
            return route.fulfill(json({ ok: true, entry_id: body.request_id, version: 0 }));
        }
        if (p.endsWith('/close')) {
            state.task.status = 'closed';
            return route.fulfill(json({ ok: true }));
        }
        if (p.endsWith('/template') || p.endsWith('/export'))
            return route.fulfill({
                status: 200,
                contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers: { 'Content-Disposition': 'attachment; filename=stocktake.xlsx' },
                body: 'download-fixture',
            });
        return route.fulfill(json({}));
    });
}
async function text(page, key, lang = 'zh') {
    return page.evaluate(({ key, lang }) => window.I18N[lang][key], { key, lang });
}
async function main() {
    fs.mkdirSync(ART, { recursive: true });
    const browser = await chromium.launch({
        args: [
            '--use-fake-ui-for-media-stream',
            '--use-fake-device-for-media-stream',
            '--use-file-for-fake-video-capture=' +
                path.resolve(process.env.STOCKTAKE_VIDEO || '/tmp/stocktake-camera.y4m'),
        ],
    });
    try {
        const context = await browser.newContext({ viewport: { width: 1365, height: 960 } });
        await context.addInitScript(() => {
            localStorage.setItem('mrpilot_token_cowork', 'cowork-test');
            localStorage.setItem('pearnly_active_workspace_client_id_cowork', '101');
            localStorage.setItem('mrpilot_lang', 'zh');
            localStorage.setItem('pearnly_entry', 'cowork');
        });
        const state = { task: initial() };
        await stub(context, state);
        const page = await context.newPage();
        await page.goto(BASE + '/home?canonical=cowork#/stocktake');
        const host = page.locator('#page-stocktake');
        await expect(host.locator('[data-task]')).toBeVisible();
        assert.equal(new URL(page.url()).pathname, '/cowork');
        // The real Cowork sidebar includes the new item directly after reconciliation.
        assert.equal(
            await page
                .locator('[data-route="reconcile"]')
                .evaluate((el) => el.nextElementSibling.dataset.route),
            'stocktake'
        );
        await host.locator('[data-action="new"]').click();
        await expect(host.locator('dialog')).toBeVisible();
        await page.waitForTimeout(500);
        const modalBox = await host.locator('dialog').boundingBox();
        assert.ok(Math.abs(modalBox.x + modalBox.width / 2 - 1365 / 2) < 3);
        await page.screenshot({ path: path.join(ART, '01-desktop-create.png'), fullPage: true });
        await host.locator('dialog input[name="name"]').fill('September warehouse count');
        const { execFileSync } = require('node:child_process');
        const workbook = execFileSync(path.resolve('venv/bin/python'), [
            '-c',
            'import sys; from tests.unit.test_stocktake import ROW, xlsx; sys.stdout.buffer.write(xlsx([ROW]))',
        ]);
        await host.locator('dialog input[type="file"]').setInputFiles({
            name: 'stocktake.xlsx',
            mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            buffer: workbook,
        });
        await host.locator('dialog button:not([type])').click();
        await expect(host.locator('dialog')).toHaveCount(0);
        assert.equal(state.imported, true);
        await expect(host.locator('tbody tr')).toHaveCount(2);
        await expect(host.locator('[data-product-summary]')).toContainText('12.5');
        await expect(host.locator('[data-product-summary]')).not.toContainText('12.500000');
        await expect(host.locator('[data-item]')).toHaveCount(0);
        async function identify(code) {
            await host.locator('[data-code]').click();
            await page.keyboard.type(code);
            await page.keyboard.press('Enter');
            await expect(host.locator('[data-entry-quantity]')).toHaveValue('');
        }
        await identify('0012');
        await host.locator('[data-entry-quantity]').fill('0');
        await host.locator('[data-entry-warehouse]').fill('New warehouse');
        await host.locator('[data-entry-location]').fill('Shelf Z');
        state.failAfterWrite = true;
        await host.locator('[data-entry-submit]').click();
        await expect(host.locator('[data-scan-message]')).toHaveText(
            await text(page, 'st-retry-same-entry')
        );
        await expect(host.locator('[data-entry-quantity]')).toBeDisabled();
        await host.locator('[data-entry-submit]').click();
        await expect(host.locator('[data-reader]')).toBeVisible();
        assert.equal(state.requests[0], state.requests[1]);
        assert.equal(state.task.entry_total, 1);
        assert.equal(state.task.items[0].actual_qty, '0');
        await identify(barcode);
        await expect(host.locator('[data-entry-warehouse]')).toHaveValue('New warehouse');
        await expect(host.locator('[data-entry-location]')).toHaveValue('Shelf Z');
        await host.locator('[data-entry-quantity]').fill('5');
        await host.locator('[data-entry-submit]').click();
        await expect(host.locator('[data-reader]')).toBeVisible();
        assert.equal(state.task.items[0].actual_qty, '5');
        const second = state.task.entries[0].id;
        await host.locator('[data-history] summary').click();
        await host.locator(`[data-edit-entry="${second}"]`).click();
        await host.locator('[data-entry-quantity]').fill('7');
        await host.locator('[data-entry-submit]').click();
        await expect(host.locator('[data-reader]')).toBeVisible();
        assert.equal(state.task.items[0].actual_qty, '7');
        await host.locator('[data-history] summary').click();
        page.once('dialog', (dialog) => dialog.accept());
        await host.locator(`[data-void-entry="${second}"]`).click();
        await expect(host.locator('[data-reader]')).toBeVisible();
        assert.equal(state.task.items[0].actual_qty, '0');
        await host.locator('[data-report-filter]').selectOption('uncounted');
        await expect(host.locator('tbody tr')).toHaveCount(1);
        await expect(host.locator('tbody')).toContainText('Internal QR product');
        await host.locator('[data-report-filter]').selectOption('differences');
        await expect(host.locator('tbody tr')).toHaveCount(1);
        await page.screenshot({
            path: path.join(ART, '02-desktop-difference.png'),
            fullPage: true,
        });
        const dl = page.waitForEvent('download');
        await host.locator('[data-action="export"]').click();
        await dl;
        await host.locator('[data-action="close"]').click();
        await host.locator('dialog button:not([type])').click();
        await expect(host.locator('[data-action="close"]')).toHaveCount(0);
        await expect(host.locator('[data-item]')).toHaveCount(0);
        await page.evaluate(() => window.applyLang('th'));
        await expect(host.locator('h1')).toHaveText(await text(page, 'st-title', 'th'));
        // Existing legacy tasks use the same quantity display without changing identifier text.
        state.task.count_mode = 'legacy';
        Object.assign(state.task.items[0], {
            book_qty: '10.000000',
            actual_qty: '9.000000',
            difference: '-1.000000',
        });
        Object.assign(state.task.items[1], {
            book_qty: '12345678901234.123456',
            actual_qty: '0.000000',
            difference: '-12345678901234.123456',
        });
        await host.locator('[data-action="refresh"]').click();
        await expect(host.locator('[data-rows] tbody tr')).toHaveCount(2);
        const cells = await host.locator('tbody tr').allTextContents();
        assert.ok(cells[0].includes('0012'));
        assert.ok(!cells.join('').includes('.000000'));
        assert.ok(cells[1].includes('12345678901234.123456'));
        await page.screenshot({
            path: path.join(ART, '06-legacy-quantity-display.png'),
            fullPage: true,
        });
        await context.close();

        const mobile = await browser.newContext({
            viewport: { width: 390, height: 844 },
            permissions: ['camera'],
        });
        await mobile.addInitScript(() => localStorage.setItem('pearnly_lang', 'th'));
        await mobile.route('https://static.line-scdn.net/liff/edge/2/sdk.js', (r) =>
            r.fulfill({
                contentType: 'text/javascript',
                body: 'window.liff={init:async()=>{},isLoggedIn:()=>true,getIDToken:()=>"verified-by-auth-fixture"};',
            })
        );
        const mobileState = { task: initial() };
        await stub(mobile, mobileState, true);
        const phone = await mobile.newPage();
        await phone.goto(BASE + '/home?flow=cowork-stocktake&draft=list');
        const body = phone.locator('#stocktake-mobile');
        await expect(body.locator('[data-task]')).toBeVisible();
        await body.locator('[data-task]').click();
        await expect(body.locator('[data-action="new"]')).toHaveCount(0);
        // Real shared POS camera engine decodes actual EAN video via the shipped WASM decoder.
        await expect(body.locator('[data-entry-form] h3')).toHaveText('น้ำดื่ม / 饮用水', {
            timeout: 30000,
        });
        await expect(body.locator('[data-scan-camera] video')).toHaveCount(0);
        await body.locator('[data-entry-quantity]').fill('12.5');
        await phone.screenshot({ path: path.join(ART, '03-mobile-count-th.png'), fullPage: true });
        assert.ok(await phone.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        await body.locator('[data-entry-submit]').click();
        // Same physical video is still in frame: a new blank entry opens after the successful save.
        await expect(body.locator('[data-entry-quantity]')).toHaveValue('', { timeout: 30000 });
        assert.equal(mobileState.task.items[0].actual_qty, '12.5');
        assert.equal(mobileState.task.entry_total, 1);
        await body.locator('[data-entry-quantity]').fill('3');
        await phone.locator('#st-lang').selectOption('zh');
        await expect(body.locator('h1')).toHaveText(await text(phone, 'st-title'));
        await expect(body.locator('[data-entry-quantity]')).toHaveValue('3');
        // Camera denial must leave the manual entry available.
        await phone.evaluate(() => {
            navigator.mediaDevices.getUserMedia = async () => {
                throw new DOMException('Denied', 'NotAllowedError');
            };
        });
        await body.locator('[data-scan-action="cancel"]').click();
        await expect(body.locator('[data-scan-message]')).toHaveText(
            await text(phone, 'st-camera-failed')
        );
        await body.locator('[data-code]').click();
        await phone.keyboard.type(qrCode, { delay: 30 });
        await phone.keyboard.press('Enter');
        await expect(body.locator('[data-entry-form] h3')).toHaveText('Internal QR product');
        await phone.screenshot({ path: path.join(ART, '04-mobile-manual-zh.png'), fullPage: true });
        await mobile.close();
        const qrBrowser = await chromium.launch({
            args: [
                '--use-fake-ui-for-media-stream',
                '--use-fake-device-for-media-stream',
                '--use-file-for-fake-video-capture=' + path.resolve('/tmp/stocktake-qr.y4m'),
            ],
        });
        try {
            const qrContext = await qrBrowser.newContext({
                viewport: { width: 390, height: 844 },
                permissions: ['camera'],
            });
            await qrContext.addInitScript(() => {
                localStorage.setItem('mrpilot_token_cowork', 'cowork-test');
                localStorage.setItem('pearnly_active_workspace_client_id_cowork', '101');
                localStorage.setItem('mrpilot_lang', 'zh');
                localStorage.setItem('pearnly_entry', 'cowork');
            });
            await stub(qrContext, { task: initial() });
            const qrPage = await qrContext.newPage();
            await qrPage.goto(BASE + '/home?canonical=cowork#/stocktake');
            const qrHost = qrPage.locator('#page-stocktake');
            await qrHost.locator('[data-task]').click();
            await qrHost.locator('[data-scan-action="camera"]').click();
            await expect(qrHost.locator('[data-entry-form] h3')).toHaveText('Internal QR product', {
                timeout: 30000,
            });
            await expect(qrHost.locator('[data-scan-camera] video')).toHaveCount(0);
            await qrPage.screenshot({ path: path.join(ART, '05-qr-product.png'), fullPage: true });
        } finally {
            await qrBrowser.close();
        }
        console.log(
            'PASS stocktake: Cowork import, scan-first, zero, additive entries, lost-response retry, edit/void, filters, lock, export, language draft, LINE shell, real EAN and QR decoding, automatic next scan, camera cleanup and denial fallback'
        );
    } finally {
        await browser.close();
    }
}
main().catch((err) => {
    console.error(err);
    process.exitCode = 1;
});
