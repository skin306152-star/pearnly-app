/* global window, document */

const { test, expect } = require('@playwright/test');

test('采购行匹配读取统一商品目录', async ({ page }, testInfo) => {
    let catalogRequest = null;
    await page.addInitScript(() => localStorage.setItem('mrpilot_token', 'e2e-purchase-token'));
    await page.route('**/api/**', async (route) => {
        const url = new URL(route.request().url());
        if (url.pathname === '/api/sales/products') {
            catalogRequest = url.searchParams.get('q');
            await route.fulfill({
                json: {
                    ok: true,
                    data: {
                        products: [{ id: 'product-1', name_th: 'สินค้า E2E', sku: 'SKU-001' }],
                    },
                },
            });
            return;
        }
        await route.fulfill({ json: { ok: true, data: {} } });
    });

    await page.goto('/home');
    await page.waitForFunction(() => typeof window.openPurchaseMatch === 'function');
    await page.evaluate(() => {
        document.body.classList.remove('workspace-gate-preboot');
        document.getElementById('workspace-gate-root')?.remove();
        window.__purchaseMatchResult = null;
        window.openPurchaseMatch(
            { description: 'กาแฟ', qty: 2, unit_price: 80 },
            (result) => (window.__purchaseMatchResult = result)
        );
    });

    await expect(page.locator('[data-pid="product-1"]')).toContainText('สินค้า E2E');
    expect(catalogRequest).toBe('กาแฟ');
    await page.locator('[data-pid="product-1"]').click();
    await expect(page.locator('#purm-mok')).toBeEnabled();
    await page.screenshot({
        path: testInfo.outputPath('purchase-product-match.png'),
        fullPage: true,
    });
    await page.locator('#purm-mok').click();
    await expect
        .poll(() => page.evaluate(() => window.__purchaseMatchResult))
        .toMatchObject({
            product_id: 'product-1',
        });
});
