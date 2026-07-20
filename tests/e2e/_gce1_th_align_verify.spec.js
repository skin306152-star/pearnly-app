// GC-E-1 · 报表页钱数列表头与数据列对齐 · 本地 stub 真浏览器验收
// (同 _gcd45_wo_copy_verify.spec.js 先例:真 dist 资产 + 真 DOM,只桩 /api/*)
// 症状:td.num 靠右而表头默认靠左=「表头与内容对不齐」(试算平衡表/建议分录/科目余额,
// Zihao 红框截图)。守门:真渲染器产出的钱数列 <th> 带 num 类且 computed text-align=right。
//
// 起法:npx playwright test tests/e2e/_gce1_th_align_verify.spec.js
/* global window, document */
const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8998;
const PAGE = `http://127.0.0.1:${PORT}/static/dist/ai.html`;
const ART = path.join(__dirname, '_artifacts', 'gce1');

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT);
});

test.afterAll(() => {
    localServer.stop(server);
});

test('钱数列表头随数据右对齐(shadow/financials/vatcheck 全表)', async ({ page }) => {
    await page.route('**/api/**', (route) =>
        route.fulfill({ contentType: 'application/json', body: '{}' })
    );
    await page.addInitScript(() => {
        window.localStorage.setItem('mrpilot_token_ai', 'tok-gce1');
        window.localStorage.setItem('mrpilot_lang', 'zh');
    });
    await page.goto(`${PAGE}#/board`);
    await page.waitForFunction(() => window.AI && window.AI.shadowRender && window.at);

    const result = await page.evaluate(() => {
        const host = document.createElement('div');
        host.id = 'gce1Host';
        document.body.appendChild(host);
        const ui = {
            open: { entries: true, accounts: true, gl: true, bs: true, pl: true, tb: true },
        };
        host.innerHTML =
            window.AI.shadowRender.pageHtml(
                {
                    trial_balance: { balanced: true, diff: '0.00' },
                    entries: [
                        {
                            source: 'INV-1',
                            dr_cr: 'dr',
                            account_code: '1111',
                            account_name: 'เงินสด',
                            amount: '100.00',
                            memo: '',
                        },
                    ],
                    sources: [],
                    accounts: [
                        {
                            code: '1111',
                            name: 'เงินสด',
                            debit: '100.00',
                            credit: '0.00',
                            balance: '100.00',
                        },
                    ],
                    reconcile_gl: null,
                },
                ui
            ) +
            window.AI.financialsRender.pageHtml(
                {
                    period: '2569-05',
                    trial_balance: {
                        balanced: true,
                        debit: '100.00',
                        credit: '100.00',
                        rows: [{ code: '1111', name: 'เงินสด', debit: '100.00', credit: '0.00' }],
                    },
                    balance_sheet: {
                        balanced: true,
                        asset_total: '100.00',
                        assets: [{ code: '1111', name: 'เงินสด', amount: '100.00' }],
                        liabilities: [],
                        equity: [],
                    },
                    profit_loss: { net_profit: '0.00', revenue: [], expense: [] },
                },
                ui
            );
        const ths = Array.from(host.querySelectorAll('th.num'));
        return {
            numHeaderCount: ths.length,
            aligns: ths.map((th) => window.getComputedStyle(th).textAlign),
            tables: host.querySelectorAll('table').length,
        };
    });

    // 建议分录 1 + 科目余额 3 + 试算平衡 2 + 资产小节 1 = 至少 7 个钱数列表头
    expect(result.numHeaderCount).toBeGreaterThanOrEqual(7);
    for (const align of result.aligns) expect(align).toBe('right');
    expect(result.tables).toBeGreaterThanOrEqual(4);

    await page.locator('#gce1Host').scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(ART, '01-th-align.png'), fullPage: true });
});
