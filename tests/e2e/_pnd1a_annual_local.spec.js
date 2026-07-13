// Pearnly AI · 批次 H 收尾件 · ภ.ง.ด.1ก 年度聚合面板 · 本地 stub 真浏览器验收(非 CI
// 用例 · 照 _h1b_payroll_local.spec.js 范式)
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**,直接进
// #/payroll(月度工具卡与年度聚合面板同页,互不依赖)。验收:年度选择器常驻可见(不依赖
// 月度上传流程)→ 选客户+年度→生成聚合→该年无数据 404 诚实报错→ 有数据出 Σ支付/Σ预扣
// + issues 逐行点名(跨月改名/年度守恒断言)→ 下载按钮真触发 GET /api/payroll/annual/
// output(kind=keying)→ 四语切换 → 手机 390 无横溢。截图存 tests/e2e/_artifacts/pnd1a/。
//
// 起法:npx playwright test tests/e2e/_pnd1a_annual_local.spec.js
/* global document, window */

const { test, expect } = require('@playwright/test');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const ROOT = path.resolve(__dirname, '..', '..');
const PORT = 8983;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'pnd1a');

let server;

function waitUp(url, tries = 40) {
    return new Promise((resolve, reject) => {
        const hit = (n) => {
            http.get(url, (r) => {
                r.resume();
                resolve();
            }).on('error', () => {
                if (n <= 0) return reject(new Error('server not up'));
                setTimeout(() => hit(n - 1), 150);
            });
        };
        hit(tries);
    });
}

test.beforeAll(async () => {
    server = spawn('python', ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1'], {
        cwd: ROOT,
        stdio: 'ignore',
    });
    await waitUp(`${BASE}/static/dist/ai.html`);
});

test.afterAll(() => {
    if (server) server.kill();
});

const CLIENTS = { clients: [{ id: 7, name: 'Sister Makeup' }] };

const SUMMARY_CLEAN = {
    employee_count: 7,
    months_present: ['2569-05', '2569-06'],
    totals: { paid_amount: '156540', wht_amount: '0' },
    issues: [],
    upload_kinds_available: ['keying'],
};

const SUMMARY_WITH_ISSUE = {
    employee_count: 7,
    months_present: ['2569-05', '2569-06'],
    totals: { paid_amount: '156540', wht_amount: '0' },
    issues: [
        {
            kind: 'cross_month_name_mismatch',
            field: 'employee_id',
            message: '同身份证跨月姓名不一致,已按最新月姓名出件',
            row_no: null,
            value: 'id=3650100697428 months=2569-05,2569-06',
        },
    ],
    upload_kinds_available: ['keying'],
};

const NO_YEAR_DATA_404 = {
    status: 404,
    body: {
        detail: {
            code: 'payroll.no_year_data',
            message: 'No payroll rows for workspace_client_id=7 tax_year=2570',
        },
    },
};

async function bootAnnual(page, { lang = 'zh', summaryBody = SUMMARY_CLEAN } = {}) {
    await page.route('**/api/workorder/orders**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{"orders":[]}' })
    );
    await page.route('**/api/workspace/clients**', (r) =>
        r.fulfill({ contentType: 'application/json', body: JSON.stringify(CLIENTS) })
    );
    await page.route('**/api/payroll/annual/summary**', (r) => {
        if (summaryBody && summaryBody.status) {
            return r.fulfill({
                status: summaryBody.status,
                contentType: 'application/json',
                body: JSON.stringify(summaryBody.body),
            });
        }
        return r.fulfill({ contentType: 'application/json', body: JSON.stringify(summaryBody) });
    });
    await page.route('**/api/payroll/annual/output**', (r) =>
        r.fulfill({
            status: 200,
            contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers: {
                'Content-Disposition':
                    'attachment; filename="payroll_annual.xlsx"; filename*=UTF-8\'\'PND1A_keying.xlsx',
            },
            body: Buffer.from('stub-annual-xlsx'),
        })
    );
    await page.route('**/api/**', (r) => {
        const url = r.request().url();
        if (
            url.includes('/api/workorder/orders') ||
            url.includes('/api/workspace/clients') ||
            url.includes('/api/payroll/')
        ) {
            return r.fallback();
        }
        return r.fulfill({ contentType: 'application/json', body: '{}' });
    });
    await page.addInitScript(
        ([l]) => {
            window.localStorage.setItem('mrpilot_token', 'tok-pnd1a');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [lang]
    );
    await page.goto(`${BASE}/static/dist/ai.html#/payroll`);
    await page.waitForSelector('#prAnnualYearInput', { timeout: 15000 });
}

// 填年度后按 Tab 触发浏览器原生 blur→change(同 _h1b_payroll_local.spec.js #prPeriodInput
// 先例:不手工派发 change 事件,免得同步 innerHTML 重建撞上仍聚焦的输入框——这是合成
// 事件才有的边界情况,真实用户改完输入框会点开别处,不会有这个问题)。
async function fillTaxYear(page, value) {
    await page.fill('#prAnnualYearInput', value);
    await page.locator('#prAnnualYearInput').press('Tab');
}

test.describe('批次 H 收尾件 · ภ.ง.ด.1ก 年度聚合面板(本地 stub 真浏览器)', () => {
    test('空态:年度选择器常驻可见,不依赖月度上传流程', async ({ page }) => {
        await bootAnnual(page, {});
        const yearInput = page.locator('#prAnnualYearInput');
        await expect(yearInput).toBeVisible();
        const runBtn = page.locator('[data-action="pr-annual-summary"]');
        await expect(runBtn).toBeVisible();
        // 未选客户前,生成按钮禁用(canRun 需要 clientId)——四态诚实,不能点了假装能跑。
        await expect(runBtn).toBeDisabled();
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '01-empty-zh.png'),
            fullPage: true,
        });
    });

    test('该年无数据:选客户+年度→生成→结构化 404 诚实报错(非原始 key)', async ({ page }) => {
        await bootAnnual(page, { summaryBody: NO_YEAR_DATA_404 });
        await page.selectOption('#prClientSel', '7');
        await fillTaxYear(page, '2570');
        await page.click('[data-action="pr-annual-summary"]');
        const err = page.locator('.intake-err');
        await expect(err).toBeVisible();
        const errText = await err.innerText();
        expect(errText).not.toContain('err_payroll_no_year_data');
        expect(errText.length).toBeGreaterThan(0);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '02-no-year-data.png'),
            fullPage: true,
        });
    });

    test('有数据:Σ支付/Σ预扣 + 全过绿态清单 + 下载入口可见', async ({ page }) => {
        await bootAnnual(page, {});
        await page.selectOption('#prClientSel', '7');
        await fillTaxYear(page, '2569');
        await page.click('[data-action="pr-annual-summary"]');
        await expect(page.locator('.pr-stats')).toContainText('156,540.00');
        await expect(page.locator('.fc-clean')).toBeVisible();
        await expect(page.locator('[data-action="pr-annual-download"]')).toBeVisible();
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '03-summary-clean.png'),
            fullPage: true,
        });
    });

    test('issues 逐行点名:跨月改名不吞,非原始 kind 字符串', async ({ page }) => {
        await bootAnnual(page, { summaryBody: SUMMARY_WITH_ISSUE });
        await page.selectOption('#prClientSel', '7');
        await fillTaxYear(page, '2569');
        await page.click('[data-action="pr-annual-summary"]');
        const issue = page.locator('.pr-issue');
        await expect(issue).toHaveCount(1);
        const issueText = await issue.nth(0).innerText();
        expect(issueText).not.toContain('cross_month_name_mismatch');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '04-summary-issues.png'),
            fullPage: true,
        });
    });

    test('下载:点击真发 GET /api/payroll/annual/output?kind=keying', async ({ page }) => {
        await bootAnnual(page, {});
        await page.selectOption('#prClientSel', '7');
        await fillTaxYear(page, '2569');
        await page.click('[data-action="pr-annual-summary"]');
        await expect(page.locator('[data-action="pr-annual-download"]')).toBeVisible();
        const [download, request] = await Promise.all([
            page.waitForEvent('download'),
            page.waitForRequest(
                (r) =>
                    r.url().includes('/api/payroll/annual/output') &&
                    r.url().includes('kind=keying')
            ),
            page.click('[data-action="pr-annual-download"]'),
        ]);
        expect(request.method()).toBe('GET');
        expect(download.suggestedFilename()).toContain('keying');
    });

    for (const lang of ['th', 'en', 'ja']) {
        test(`四语(${lang}):上传件降级说明/下载按钮文案非原始 key`, async ({ page }) => {
            await bootAnnual(page, { lang });
            await page.selectOption('#prClientSel', '7');
            await fillTaxYear(page, '2569');
            await page.click('[data-action="pr-annual-summary"]');
            await expect(page.locator('.pr-stats')).toBeVisible();
            const noteText = await page.locator('.pr-payer-note').innerText();
            expect(noteText).not.toContain('payroll_annual_upload_note');
            expect(noteText.length).toBeGreaterThan(0);
            const btnText = await page.locator('[data-action="pr-annual-download"]').innerText();
            expect(btnText).not.toContain('payroll_download_annual_keying');
            await page.screenshot({
                path: path.join(ARTIFACT_DIR, `05-lang-${lang}.png`),
                fullPage: true,
            });
        });
    }

    test('手机 390:年度聚合面板可见 + 无横向溢出', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await bootAnnual(page, { summaryBody: SUMMARY_WITH_ISSUE });
        await page.selectOption('#prClientSel', '7');
        await fillTaxYear(page, '2569');
        await page.click('[data-action="pr-annual-summary"]');
        await expect(page.locator('.pr-issue')).toBeVisible();
        const overflow = await page.evaluate(() => document.body.scrollWidth - window.innerWidth);
        expect(overflow, '手机视口不该出横向滚动').toBeLessThanOrEqual(1);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '06-mobile-390.png'),
            fullPage: true,
        });
    });
});
