// Pearnly AI · K2 · Excel→PDF 规范输出 · 本地 stub 真浏览器验收(非 CI 用例 · 用完即删)
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**(同
// _k1b_fileconv_local.spec.js / _k1c_fileconv_ocr_local.spec.js 先例)。K2 增量验收:
// xlsx 上传放行、四态诚实(守恒过/守恒不平点名/generic 未校验声明/坏文件诚实拒)、
// 双下载按钮各自独立(?format=xlsx / ?format=pdf&lang=)、四语文案非原始 key、
// 手机 390 无横溢。截图存 tests/e2e/_artifacts/k2/。
//
// 起法:npx playwright test tests/e2e/_k2_fileconv_excel_local.spec.js
/* global document, window, getComputedStyle */

const { test, expect } = require('@playwright/test');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const ROOT = path.resolve(__dirname, '..', '..');
const PORT = 8983;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'k2');

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

// 真跑口径(services/fileconv/excel_in.py 合成金标同形):GL xlsx 期初+两行闭合。
const SUMMARY_GL_CONSERVED = {
    doc_type: 'gl_ledger',
    status: 'ok',
    conserved: true,
    stats: {
        row_count: 2,
        engine: 'excel_gl',
        sum_debit: '500.0',
        sum_credit: '200.0',
        opening_balance: '1000.0',
        closing_balance: '1300.0',
    },
    issue_count: 0,
    issues: [],
};

const SUMMARY_GL_ISSUES = {
    doc_type: 'gl_ledger',
    status: 'ok',
    conserved: false,
    stats: { row_count: 2, engine: 'excel_gl' },
    issue_count: 1,
    issues: [
        {
            kind: 'gl_balance_chain',
            line_no: 2,
            account: '',
            message: '2026-01-02 V2: 上行余额 1100.0 + 借 0 − 贷 50.0 ≠ 本行余额',
            expected: '1050.0',
            actual: '999.0',
        },
    ],
};

const SUMMARY_GENERIC = {
    doc_type: 'generic_table',
    status: 'ok',
    conserved: true, // 后端 conserved=!issues.length,generic 恒 true——前端不能借它显"通过"
    stats: { engine: 'excel_grid', sheet_count: 1 },
    issue_count: 0,
    issues: [],
};

const SUMMARY_UNSUPPORTED = {
    doc_type: '',
    status: 'unsupported_format',
    conserved: true,
    stats: { reason: 'unreadable_or_empty' },
    issue_count: 0,
    issues: [],
};

async function bootFileconv(page, { lang = 'zh', convertBody = SUMMARY_GL_CONSERVED } = {}) {
    await page.route('**/api/workorder/orders**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{"orders":[]}' })
    );
    await page.route('**/api/fileconv/convert**', (r) => {
        const url = r.request().url();
        if (url.includes('format=xlsx')) {
            return r.fulfill({
                status: 200,
                contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers: {
                    'Content-Disposition':
                        'attachment; filename="convert.xlsx"; filename*=UTF-8\'\'gl.xlsx',
                },
                body: Buffer.from('stub-xlsx'),
            });
        }
        if (url.includes('format=pdf')) {
            return r.fulfill({
                status: 200,
                contentType: 'application/pdf',
                headers: {
                    'Content-Disposition':
                        'attachment; filename="convert.pdf"; filename*=UTF-8\'\'gl.pdf',
                },
                body: Buffer.from('%PDF-stub'),
            });
        }
        return r.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(convertBody),
        });
    });
    await page.route('**/api/**', (r) => {
        const url = r.request().url();
        if (url.includes('/api/workorder/orders') || url.includes('/api/fileconv/convert')) {
            return r.fallback();
        }
        return r.fulfill({ contentType: 'application/json', body: '{}' });
    });
    await page.addInitScript(
        ([l]) => {
            window.localStorage.setItem('mrpilot_token_ai', 'tok-k2');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [lang]
    );
    await page.goto(`${BASE}/static/dist/ai.html#/fileconv`);
    await page.waitForSelector('#fcDrop', { timeout: 15000 });
}

async function pickXlsxAndRun(page, name = 'gl.xlsx') {
    await page.setInputFiles('#fcFileInput', {
        name,
        mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        buffer: Buffer.from('PK-stub-xlsx-bytes'),
    });
    await page.click('[data-action="fc-run"]');
}

test.describe('K2 · Excel/CSV → PDF 规范输出(本地 stub 真浏览器)', () => {
    test('xlsx 放行 · 守恒过:绿横幅 + 统计 + 两个下载按钮均可见', async ({ page }) => {
        await bootFileconv(page, {});
        await pickXlsxAndRun(page);
        await expect(page.locator('.fc-banner.g')).toBeVisible();
        await expect(page.locator('.fc-stats')).toContainText('1,300.00'); // closing_balance
        const xlsxBtn = page.locator('[data-action="fc-download-xlsx"]');
        const pdfBtn = page.locator('[data-action="fc-download-pdf"]');
        await expect(xlsxBtn).toBeVisible();
        await expect(pdfBtn).toBeVisible();
        const st = await pdfBtn.evaluate((el) => {
            const s = getComputedStyle(el);
            return { display: s.display, visibility: s.visibility };
        });
        expect(st.display).not.toBe('none');
        expect(st.visibility).toBe('visible');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '01-gl-conserved.png'),
            fullPage: true,
        });
    });

    test('xlsx 守恒不平:黄横幅逐行点名,不假成功', async ({ page }) => {
        await bootFileconv(page, { convertBody: SUMMARY_GL_ISSUES });
        await pickXlsxAndRun(page);
        await expect(page.locator('.fc-banner.w')).toBeVisible();
        await expect(page.locator('.fc-banner.g')).toHaveCount(0);
        const issue = page.locator('.fc-issue').first();
        await expect(issue).toContainText('#2');
        await expect(issue).toContainText('1050.0');
        await expect(issue).toContainText('999.0');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '02-gl-issues.png'),
            fullPage: true,
        });
    });

    test('generic 表:未做校验声明,不借 conserved 恒真假背书(无绿横幅)', async ({ page }) => {
        await bootFileconv(page, { convertBody: SUMMARY_GENERIC });
        await pickXlsxAndRun(page, 'random_sheet.xlsx');
        await expect(page.locator('.fc-banner.g')).toHaveCount(0);
        await expect(page.locator('.fc-banner.w')).toHaveCount(0);
        const banner = page.locator('.fc-banner.n');
        await expect(banner).toBeVisible();
        await expect(banner).toContainText('未做数字校验');
        // generic 仍可下载(忠实网格,不是拒绝态)。
        await expect(page.locator('[data-action="fc-download-xlsx"]')).toBeVisible();
        await expect(page.locator('[data-action="fc-download-pdf"]')).toBeVisible();
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '03-generic-no-check.png'),
            fullPage: true,
        });
    });

    test('坏文件/格式不支持:诚实拒绝,无下载按钮无绿横幅', async ({ page }) => {
        await bootFileconv(page, { convertBody: SUMMARY_UNSUPPORTED });
        await pickXlsxAndRun(page, 'corrupt.xlsx');
        await expect(page.locator('.fc-banner.n')).toBeVisible();
        await expect(page.locator('.fc-banner.g')).toHaveCount(0);
        await expect(page.locator('[data-action="fc-download-xlsx"]')).toHaveCount(0);
        await expect(page.locator('[data-action="fc-download-pdf"]')).toHaveCount(0);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '04-unsupported-format.png'),
            fullPage: true,
        });
    });

    test('.xls/.csv 客户端放行(validateFile 不挡),.docx 仍被挡', async ({ page }) => {
        await bootFileconv(page, {});
        await page.setInputFiles('#fcFileInput', {
            name: 'old.xls',
            mimeType: 'application/vnd.ms-excel',
            buffer: Buffer.from('xls-stub'),
        });
        await expect(page.locator('.intake-err')).toHaveCount(0);
        await page.setInputFiles('#fcFileInput', {
            name: 'data.csv',
            mimeType: 'text/csv',
            buffer: Buffer.from('a,b\n1,2'),
        });
        await expect(page.locator('.intake-err')).toHaveCount(0);
        await page.setInputFiles('#fcFileInput', {
            name: 'report.docx',
            mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            buffer: Buffer.from('nope'),
        });
        await expect(page.locator('.intake-err')).toBeVisible();
    });

    test('下载 Excel:真发 ?format=xlsx', async ({ page }) => {
        await bootFileconv(page, {});
        await pickXlsxAndRun(page);
        const [download, request] = await Promise.all([
            page.waitForEvent('download'),
            page.waitForRequest((r) => r.url().includes('format=xlsx')),
            page.click('[data-action="fc-download-xlsx"]'),
        ]);
        expect(request.method()).toBe('POST');
        expect(download.suggestedFilename()).toBe('gl.xlsx');
    });

    test('下载 PDF:真发 ?format=pdf&lang= 带当前 UI 语种', async ({ page }) => {
        await bootFileconv(page, { lang: 'ja' });
        await pickXlsxAndRun(page);
        const [download, request] = await Promise.all([
            page.waitForEvent('download'),
            page.waitForRequest((r) => r.url().includes('format=pdf')),
            page.click('[data-action="fc-download-pdf"]'),
        ]);
        expect(request.method()).toBe('POST');
        expect(request.url()).toContain('lang=ja');
        expect(download.suggestedFilename()).toBe('gl.pdf');
    });

    test('两个下载按钮各自独立 in-flight,点 PDF 时 Excel 按钮仍可点', async ({ page }) => {
        await bootFileconv(page, {});
        await pickXlsxAndRun(page);
        await page.unroute('**/api/fileconv/convert**');
        await page.route('**/api/fileconv/convert**', async (r) => {
            if (r.request().url().includes('format=pdf')) {
                await new Promise((res) => setTimeout(res, 700));
            }
            return r.fulfill({
                status: 200,
                contentType: 'application/pdf',
                headers: { 'Content-Disposition': 'attachment; filename="convert.pdf"' },
                body: Buffer.from('%PDF-stub'),
            });
        });
        await page.click('[data-action="fc-download-pdf"]');
        await expect(page.locator('[data-action="fc-download-pdf"]')).toBeDisabled();
        await expect(page.locator('[data-action="fc-download-xlsx"]')).toBeEnabled();
    });

    for (const lang of ['th', 'en', 'ja']) {
        test(`四语(${lang}):generic 未校验声明非原始 key`, async ({ page }) => {
            await bootFileconv(page, { lang, convertBody: SUMMARY_GENERIC });
            await pickXlsxAndRun(page);
            const genericBanner = page.locator('.fc-banner.n');
            await expect(genericBanner).toBeVisible();
            const genericText = await genericBanner.innerText();
            expect(genericText).not.toContain('fileconv_generic_no_check');
            expect(genericText.length).toBeGreaterThan(5);
            await page.screenshot({
                path: path.join(ARTIFACT_DIR, `05-lang-${lang}-generic.png`),
                fullPage: true,
            });
        });

        test(`四语(${lang}):格式不支持横幅非原始 key`, async ({ page }) => {
            await bootFileconv(page, { lang, convertBody: SUMMARY_UNSUPPORTED });
            await pickXlsxAndRun(page, 'corrupt.xlsx');
            const rejectBanner = page.locator('.fc-banner.n');
            await expect(rejectBanner).toBeVisible();
            const rejectText = await rejectBanner.innerText();
            expect(rejectText).not.toContain('fileconv_unsupported_format');
            await page.screenshot({
                path: path.join(ARTIFACT_DIR, `06-lang-${lang}-reject.png`),
                fullPage: true,
            });
        });
    }

    test('手机 390:双下载按钮纵向堆叠,无横向溢出', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await bootFileconv(page, {});
        await pickXlsxAndRun(page);
        await expect(page.locator('.fc-banner.g')).toBeVisible();
        const overflow = await page.evaluate(
            () => document.documentElement.scrollWidth - document.documentElement.clientWidth
        );
        expect(overflow).toBeLessThanOrEqual(1);
        const xlsxBtn = page.locator('[data-action="fc-download-xlsx"]');
        const pdfBtn = page.locator('[data-action="fc-download-pdf"]');
        const [xBox, pBox] = await Promise.all([xlsxBtn.boundingBox(), pdfBtn.boundingBox()]);
        expect(pBox.y).toBeGreaterThan(xBox.y); // column 布局:PDF 按钮在 Excel 按钮下方
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '07-mobile-390.png'),
            fullPage: true,
        });
    });
});
