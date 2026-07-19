/* global window, getComputedStyle */
const fs = require('fs');
const path = require('path');
const { test, expect } = require('@playwright/test');

const ROOT = path.resolve(__dirname, '../..');
const ARTIFACTS = path.join(__dirname, '_artifacts', 'gc0719_bc');

async function loadHarness(page) {
    await page.setContent('<main><section id="cv-intake" class="cview on"></section></main>');
    await page.addStyleTag({ path: path.join(ROOT, 'static', 'dist', 'ai.css') });
    await page.evaluate(() => {
        window.__AI_I18N_ZH__ = {};
        window.__AI_I18N_TH__ = {};
        window.__AI_I18N_EN__ = {};
        window.__AI_I18N_JA__ = {};
        window.AII18N = { lang: 'zh' };
        const nativeSetTimeout = window.setTimeout.bind(window);
        window.setTimeout = (fn, delay) => nativeSetTimeout(fn, Math.min(delay, 30));
        window.AI = {
            api: { mapApiErrorKey: () => 'err_generic' },
            state: {
                esc(value) {
                    return String(value == null ? '' : value)
                        .replaceAll('&', '&amp;')
                        .replaceAll('<', '&lt;')
                        .replaceAll('>', '&gt;')
                        .replaceAll('"', '&quot;');
                },
                loadingHtml: () => '<p>loading</p>',
                errorHtml: () => '<p>error</p>',
            },
            format: {
                parseAmount: (value) => Number(value),
                money: (value) => `฿${Number(value || 0).toLocaleString('en-US')}`,
                pct: (value) => `${Number(value || 0) * 100}%`,
                progressLabel: () => 'running',
            },
            router: { buildClientHash: () => '#client' },
            intakeManifest: {
                hasResumableQueue: () => false,
                resumeBannerHtml: () => '',
                passwordCardHtml: () => '',
                manifestHtml: () => '',
                failedBatchesHtml: () => '',
            },
            intakeQueue: {
                loadQueueState: () => null,
                hasDirectoryEntry: () => false,
                create: () => ({}),
            },
        };
    });
    for (const file of [
        'ai-i18n-zh.js',
        'ai-i18n-zh-2.js',
        'ai-i18n-bank-sales.js',
        'ai-bank-sales-groups.js',
        'ai-bank-sales-render.js',
        'ai-intake-render.js',
        'ai-intake-excluded.js',
        'ai-intake-bank-sales.js',
        'ai-intake.js',
    ]) {
        await page.addScriptTag({ path: path.join(ROOT, 'static', 'ai', file) });
    }
    await page.evaluate(() => {
        window.at = (key, values) => {
            let text = window.__AI_I18N_ZH__[key] || key;
            Object.entries(values || {}).forEach(([name, value]) => {
                text = text.replaceAll(`{${name}}`, value);
            });
            return text;
        };
    });
}

function row(index, group, amount) {
    return {
        fingerprint: `2569-05-${String((index % 28) + 1).padStart(2, '0')}|${amount}|${index}`,
        date: '2569-05-01',
        deposit: String(amount),
        withdrawal: '0',
        description: group === 'cash_deposit' ? 'ฝากเงินสด CDM' : `รับโอนเงิน ${index}`,
        verdict: 'pending',
        reason: 'deposit_unclassified',
        source: 'rule',
        group,
    };
}

test.beforeAll(() => fs.mkdirSync(ARTIFACTS, { recursive: true }));

test('120 pending rows run in background, group-confirm, then unlock apply', async ({ page }) => {
    await loadHarness(page);
    await page.evaluate(
        ({ rows120 }) => {
            let stage = 'initial';
            let progressCall = 0;
            const remaining = rows120.slice(0, 6).map((item, index) => ({
                ...item,
                deposit: index === 0 ? '12000' : '500',
            }));
            const suggestion = (rows) => ({
                applicable: true,
                reliable: true,
                coverage: { reliable: true },
                counts: {
                    total: 120,
                    sales: stage === 'decided' ? 120 : 0,
                    pending: rows.length,
                    non_sales: 0,
                },
                rows,
                pending_groups: Object.values(
                    rows.reduce((groups, item) => {
                        groups[item.group] = groups[item.group] || {
                            key: item.group,
                            count: 0,
                            sum: 0,
                        };
                        groups[item.group].count += 1;
                        groups[item.group].sum += Number(item.deposit);
                        return groups;
                    }, {})
                ).map((group) => ({ ...group, sum: String(group.sum) })),
                gross_total: stage === 'decided' ? '14500' : '0',
                sales_amount: stage === 'decided' ? '13551.40' : '0',
                output_vat: stage === 'decided' ? '948.60' : '0',
                pending_count: rows.length,
            });
            const api = {
                getOrder: () =>
                    Promise.resolve({
                        material_count: 1,
                        needs: ['sales_summary'],
                        sales_corroboration: { net_total: '100' },
                        bank_sales_suggestion:
                            stage === 'initial'
                                ? suggestion(rows120)
                                : stage === 'judged'
                                  ? suggestion(remaining)
                                  : suggestion([]),
                    }),
                runBankSales: () => {
                    stage = 'running';
                    return Promise.resolve({ started: true, total_pending: 120 });
                },
                bankSalesProgress: () => {
                    progressCall += 1;
                    if (progressCall === 1) {
                        return Promise.resolve({
                            running: true,
                            done: 40,
                            total: 120,
                            failed_batches: 0,
                        });
                    }
                    if (progressCall === 2) {
                        return Promise.resolve({
                            running: true,
                            done: 80,
                            total: 120,
                            failed_batches: 0,
                        });
                    }
                    stage = 'judged';
                    return Promise.resolve({
                        running: false,
                        done: 114,
                        total: 120,
                        failed_batches: 0,
                    });
                },
                decideBankSalesBatch: (_orderId, decisions) => {
                    window.__batchDecisions = decisions;
                    stage = 'decided';
                    return Promise.resolve({ applied: decisions.length });
                },
            };
            window.AI.intake.mount(api, { id: 'wo-gc-c' }, 106);
        },
        {
            rows120: Array.from({ length: 120 }, (_, index) =>
                row(index, index < 60 ? 'transfer_in' : 'cash_deposit', 500)
            ),
        }
    );

    const runButton = page.locator('[data-action="bxs-run"]');
    await expect(runButton).toBeVisible();
    await expect(page.getByText('尚未形成倒推数')).toBeVisible();
    await runButton.click();
    await expect(runButton).toBeDisabled();
    await expect(runButton).toContainText('已判 40 / 共 120');
    await page.screenshot({
        path: path.join(ARTIFACTS, '03-gc-c-background-progress.png'),
        fullPage: true,
    });

    const group = page.locator('[data-bxs-group="transfer_in"]');
    await expect(group).toContainText('6 笔 · 合计');
    await expect(group.locator('.bxs-small summary')).toContainText('共 5 笔小额');
    await expect(group.locator('.brx-row')).toHaveCount(6);
    await group.locator('[data-verdict="sales"]').last().click();

    const modal = page.locator('.bxs-confirm-mask .pkg-modal');
    await expect(modal).toBeVisible();
    await expect(modal).toContainText('个人转账入账');
    await expect(modal).toContainText('6 笔');
    const modalStyle = await modal.evaluate((element) => {
        const style = getComputedStyle(element);
        return { display: style.display, visibility: style.visibility };
    });
    expect(modalStyle.display).not.toBe('none');
    expect(modalStyle.visibility).toBe('visible');
    await page.screenshot({
        path: path.join(ARTIFACTS, '04-gc-c-group-confirm.png'),
        fullPage: true,
    });

    await modal.locator('[data-action="bxs-batch-confirm"]').click();
    await expect(page.locator('[data-action="bxs-apply"]')).toBeEnabled();
    await expect(page.locator('[data-bxs-group]')).toHaveCount(0);
    await expect.poll(() => page.evaluate(() => window.__batchDecisions.length)).toBe(6);
});
