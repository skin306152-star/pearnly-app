/* global window, document, getComputedStyle */
const fs = require('fs');
const path = require('path');
const { test, expect } = require('@playwright/test');

const ROOT = path.resolve(__dirname, '../..');
const ARTIFACTS = path.join(__dirname, '_artifacts', 'gc0719_bc');

async function loadIntake(page) {
    await page.setContent('<main><section id="cv-intake" class="cview on"></section></main>');
    await page.addStyleTag({ path: path.join(ROOT, 'static', 'dist', 'ai.css') });
    await page.evaluate(() => {
        window.__AI_I18N_ZH__ = {};
        window.AII18N = { lang: 'zh' };
        window.AI = {
            state: {
                esc(value) {
                    return String(value == null ? '' : value)
                        .replaceAll('&', '&amp;')
                        .replaceAll('<', '&lt;')
                        .replaceAll('>', '&gt;')
                        .replaceAll('"', '&quot;');
                },
                loadingHtml() {
                    return '<p>loading</p>';
                },
                errorHtml() {
                    return '<p>error</p>';
                },
            },
            format: {
                parseAmount(value) {
                    const parsed = Number(value);
                    return Number.isFinite(parsed) ? parsed : null;
                },
                money(value) {
                    return String(value);
                },
                pct(value) {
                    return `${Number(value || 0) * 100}%`;
                },
                progressLabel() {
                    return 'running';
                },
            },
            router: { buildClientHash: () => '#client' },
            intakeManifest: {
                hasResumableQueue: () => false,
                resumeBannerHtml: () => '',
                passwordCardHtml: () => '',
                manifestHtml: () => '',
                failedBatchesHtml: () => '',
            },
            intakeBankSales: {
                create: () => ({
                    toggleFold() {},
                    decideRow() {},
                    run() {},
                    apply() {},
                }),
            },
            intakeQueue: {
                loadQueueState: () => null,
                hasDirectoryEntry: () => false,
                create: () => ({}),
            },
        };
    });
    await page.addScriptTag({ path: path.join(ROOT, 'static', 'ai', 'ai-i18n-zh-2.js') });
    await page.evaluate(() => {
        window.at = (key, values) => {
            let text = window.__AI_I18N_ZH__[key] || key;
            Object.entries(values || {}).forEach(([name, value]) => {
                text = text.replaceAll(`{${name}}`, value);
            });
            return text;
        };
    });
    await page.addScriptTag({ path: path.join(ROOT, 'static', 'ai', 'ai-bank-sales-render.js') });
    await page.addScriptTag({ path: path.join(ROOT, 'static', 'ai', 'ai-intake-render.js') });
    await page.addScriptTag({ path: path.join(ROOT, 'static', 'ai', 'ai-intake-excluded.js') });
    await page.addScriptTag({ path: path.join(ROOT, 'static', 'ai', 'ai-intake.js') });
}

test.beforeAll(() => {
    fs.mkdirSync(ARTIFACTS, { recursive: true });
});

test('excluded material is collapsed, visible on demand, and disappears after reassignment', async ({
    page,
}) => {
    await loadIntake(page);
    await page.evaluate(() => {
        let assigned = false;
        window.__decisions = [];
        const api = {
            getOrder: () =>
                Promise.resolve({
                    material_count: 1,
                    needs: [],
                    excluded: assigned
                        ? []
                        : [
                              {
                                  item_id: 'item-2501',
                                  name: 'IMG_2501.jpg',
                                  kind: 'non_tax',
                                  reason: 'no_tax_elements:payment_evidence',
                              },
                          ],
                }),
            decide: (_orderId, body) => {
                window.__decisions.push(body);
                assigned = true;
                return Promise.resolve({ ok: true });
            },
        };
        window.AI.intake.mount(api, { id: 'wo-gc-b' }, 106);
    });

    const details = page.locator('details.intake-excluded');
    await expect(details.locator('summary')).toHaveText('已排除 1 件');
    await expect(details).not.toHaveAttribute('open', '');
    await expect(page.getByText('IMG_2501.jpg')).not.toBeVisible();

    await details.locator('summary').click();
    const row = page.locator('.intake-excluded-row');
    await expect(row).toBeVisible();
    const style = await row.evaluate((element) => {
        const computed = getComputedStyle(element);
        return { display: computed.display, visibility: computed.visibility };
    });
    expect(style.display).not.toBe('none');
    expect(style.visibility).toBe('visible');
    await page.screenshot({
        path: path.join(ARTIFACTS, '01-excluded-expanded.png'),
        fullPage: true,
    });

    await row.locator('select').selectOption('bank_statement');
    await expect(page.locator('details.intake-excluded')).toHaveCount(0);
    await expect
        .poll(() => page.evaluate(() => window.__decisions))
        .toEqual([
            {
                item_id: 'item-2501',
                decision: 'assign_kind',
                kind: 'bank_statement',
            },
        ]);
});

test('missing statement dates render a visible degradation message', async ({ page }) => {
    await loadIntake(page);
    await page.evaluate(() => {
        document.body.innerHTML = '<main id="degrade"></main>';
        document.getElementById('degrade').innerHTML = window.AI.bankSalesRender.cardHtml(
            {
                applicable: true,
                reliable: false,
                rows: [],
                coverage: {
                    chain_breaks: 0,
                    unexplained_inflow: '0',
                    inflow_gap_ratio: '0',
                },
                message: {
                    zh: '银行流水未覆盖 2026-05-29, 2026-05-30, 2026-05-31，请核对或补齐对应页。',
                },
            },
            window.AI.bankSalesRender.freshUiState(),
            null,
            null
        );
    });

    const banner = page.locator('.fc-banner.w');
    await expect(banner).toBeVisible();
    await expect(banner).toContainText('2026-05-29, 2026-05-30, 2026-05-31');
    const style = await banner.evaluate((element) => {
        const computed = getComputedStyle(element);
        return { display: computed.display, visibility: computed.visibility };
    });
    expect(style.display).not.toBe('none');
    expect(style.visibility).toBe('visible');
    await page.screenshot({
        path: path.join(ARTIFACTS, '02-date-gap-degrade.png'),
        fullPage: true,
    });
});
