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
const item = (id, loc, qty = null) => ({
    id,
    product_code: '0012',
    product_name: 'น้ำดื่ม / 饮用水',
    barcode,
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
    items: [item('row-a', 'A01'), item('row-b', 'A02', '10.000000')],
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
        if (p.endsWith('/items/row-a')) {
            if (state.conflict) return route.fulfill(json({ detail: 'stocktake.conflict' }, 409));
            const body = req.postDataJSON();
            assert.equal(body.version, state.task.items[0].version);
            state.saved = body.quantity;
            Object.assign(state.task.items[0], {
                actual_qty: body.quantity,
                difference: String(Number(body.quantity) - 12.5),
                version: body.version + 1,
            });
            return route.fulfill(json({ ok: true }));
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
        await host
            .locator('dialog input[type="file"]')
            .setInputFiles({
                name: 'stocktake.xlsx',
                mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                buffer: workbook,
            });
        await host.locator('dialog button:not([type])').click();
        await expect(host.locator('dialog')).toHaveCount(0);
        assert.equal(state.imported, true);
        await expect(host.locator('tbody tr')).toHaveCount(2);
        await host.locator('[data-filter]').selectOption('uncounted');
        await expect(host.locator('tbody tr')).toHaveCount(1);
        await expect(host.locator('tbody')).toContainText(await text(page, 'st-uncounted'));
        await host.locator('[data-item="row-a"]').click();
        await expect(host.locator('[data-qty]')).toHaveValue('');
        await host.locator('[data-qty]').fill('0');
        state.conflict = true;
        await host.locator('[data-count] button:not([type])').click();
        await expect(host.locator('[data-message]')).toHaveText(
            await text(page, 'st-error-conflict')
        );
        await expect(host.locator('[data-qty]')).toHaveValue('0');
        state.conflict = false;
        await host.locator('[data-count] button:not([type])').click();
        await expect(host.locator('[data-message]')).toHaveText(await text(page, 'st-saved'));
        assert.equal(state.saved, '0');
        await host.locator('[data-filter]').selectOption('differences');
        await expect(host.locator('tbody tr')).toHaveCount(2);
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
        await body.locator('[data-action="scan"]').click();
        // Real shared POS camera engine decodes actual EAN video via the shipped WASM decoder.
        await expect(body.locator('[data-query]')).toHaveValue(barcode, { timeout: 30000 });
        await expect(body.locator('[data-message]')).toHaveText(
            await text(phone, 'st-choose-location', 'th')
        );
        await expect(body.locator('[data-camera] video')).toHaveCount(0);
        await body.locator('[data-item="row-a"]').click();
        await expect(body.locator('[data-count] h3')).toHaveText('น้ำดื่ม / 饮用水');
        await expect(body.locator('[data-variant]')).toHaveValue('row-a');
        await body.locator('[data-qty]').fill('12.5');
        await phone.screenshot({ path: path.join(ART, '03-mobile-count-th.png'), fullPage: true });
        assert.ok(await phone.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        await body.locator('[data-count] button:not([type])').click();
        await expect(body.locator('[data-message]')).toHaveText(
            await text(phone, 'st-saved', 'th')
        );
        assert.equal(mobileState.saved, '12.5');
        await phone.locator('#st-lang').selectOption('zh');
        await expect(body.locator('h1')).toHaveText(await text(phone, 'st-title'));
        await body.locator('[data-query]').click();
        await phone.keyboard.type('0012', { delay: 90 });
        await phone.keyboard.press('Enter');
        await expect(body.locator('tbody tr')).toHaveCount(2);
        // Camera denial must leave the manual entry available.
        await phone.evaluate(() => {
            navigator.mediaDevices.getUserMedia = async () => {
                throw new DOMException('Denied', 'NotAllowedError');
            };
        });
        await body.locator('[data-action="scan"]').click();
        await expect(body.locator('[data-message]')).toHaveText(
            await text(phone, 'st-camera-failed')
        );
        await phone.screenshot({ path: path.join(ART, '04-mobile-manual-zh.png'), fullPage: true });
        await mobile.close();
        console.log(
            'PASS stocktake: actual Cowork navigation, import modal, filters, zero, conflict, lock, export, i18n, LINE shell, real barcode decoding, camera cleanup and fallback'
        );
    } finally {
        await browser.close();
    }
}
main().catch((err) => {
    console.error(err);
    process.exitCode = 1;
});
