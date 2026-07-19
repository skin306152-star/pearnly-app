// Pearnly AI · K1b · 财务文件转换视图 · 本地 stub 真浏览器验收(非 CI 用例 · 用完即删)
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**(同
// _entry_shell_verify.spec.js 先例):闸探针 200 → 进工作台,#/fileconv 真渲染。
// 验收:四态(空/加载/结果/错误)isVisible + getComputedStyle、守恒绿横幅与黄灯逐行
// 点名(line_no/expected/actual)、no_text_layer 中性态、下载按钮 re-post ?format=xlsx、
// 四语标题非原始 key、手机 390 无横溢。截图存 tests/e2e/_artifacts/k1b/。
//
// 起法:npx playwright test tests/e2e/_k1b_fileconv_local.spec.js
/* global document, window, getComputedStyle */

const { test, expect } = require('@playwright/test');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const ROOT = path.resolve(__dirname, '..', '..');
const PORT = 8981;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'k1b');

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

const SUMMARY_OK = {
    doc_type: 'gl_ledger',
    status: 'ok',
    conserved: true,
    stats: { row_count: 735, accounts: ['1113-01'], closing_balance: '608917.35' },
    issue_count: 0,
    issues: [],
};

const SUMMARY_ISSUES = {
    doc_type: 'bank_statement',
    status: 'ok',
    conserved: false,
    stats: { row_count: 403 },
    issue_count: 2,
    issues: [
        {
            kind: 'running_balance',
            line_no: 17,
            account: '',
            message: '02/01/2569 TRF: 余额变动 ≠ 本行金额',
            expected: '1200.00',
            actual: '1300.00',
        },
        {
            kind: 'running_balance',
            line_no: 44,
            account: '',
            message: '05/01/2569 FEE: 余额变动 ≠ 本行金额',
            expected: '30.00',
            actual: '20.00',
        },
    ],
};

const SUMMARY_SCAN = {
    doc_type: '',
    status: 'no_text_layer',
    conserved: true,
    stats: { reason: '无文字层(疑扫描件)· OCR 归 K1c' },
    issue_count: 0,
    issues: [],
};

async function bootFileconv(page, { lang = 'zh', convertBody = SUMMARY_OK, convertStatus = 200 }) {
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
                        'attachment; filename="convert.xlsx"; filename*=UTF-8\'\'GL%20TTB.xlsx',
                },
                body: Buffer.from('stub-xlsx'),
            });
        }
        return r.fulfill({
            status: convertStatus,
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
            window.localStorage.setItem('mrpilot_token_ai', 'tok-k1b');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [lang]
    );
    await page.goto(`${BASE}/static/dist/ai.html#/fileconv`);
    await page.waitForSelector('#fcDrop', { timeout: 15000 });
}

async function pickPdfAndRun(page) {
    await page.setInputFiles('#fcFileInput', {
        name: 'GL TTB.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('%PDF-1.4 stub'),
    });
    await page.click('[data-action="fc-run"]');
}

test.describe('K1b · 财务文件转换视图(本地 stub 真浏览器)', () => {
    test('空态:导航项/上传区可见(isVisible+getComputedStyle),视图互斥', async ({ page }) => {
        await bootFileconv(page, {});
        await expect(page.locator('#navFileconv')).toBeVisible();
        const drop = page.locator('#fcDrop');
        await expect(drop).toBeVisible();
        const st = await drop.evaluate((el) => {
            const s = getComputedStyle(el);
            return { display: s.display, visibility: s.visibility };
        });
        expect(st.display).not.toBe('none');
        expect(st.visibility).toBe('visible');
        // 视图互斥:v-fileconv on,其它 off。
        await expect(page.locator('#v-fileconv')).toHaveClass(/\bon\b/);
        await expect(page.locator('#v-vatcheck')).not.toHaveClass(/\bon\b/);
        const title = await page.locator('#v-fileconv h2').innerText();
        expect(title.length).toBeGreaterThan(0);
        expect(title).not.toContain('fileconv_title');
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '01-empty-zh.png'), fullPage: true });
    });

    test('加载态:骨架条可见,完成后进守恒绿横幅结果', async ({ page }) => {
        await bootFileconv(page, {});
        // 延迟兑现让 loading 态可捕捉。
        await page.unroute('**/api/fileconv/convert**');
        await page.route('**/api/fileconv/convert**', async (r) => {
            await new Promise((res) => setTimeout(res, 800));
            r.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(SUMMARY_OK),
            });
        });
        await pickPdfAndRun(page);
        await expect(page.locator('#fcBody [data-state="loading"]')).toBeVisible();
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '02-loading.png'), fullPage: true });
        await expect(page.locator('.fc-banner.g')).toBeVisible({ timeout: 5000 });
        await expect(page.locator('.fc-banner.g')).toContainText('数字可信');
        await expect(page.locator('.fc-stats')).toContainText('608,917.35');
        // K2 起下载区拆两个独立按钮(xlsx/pdf),同 fc-run 不再共用一个 fc-download。
        await expect(page.locator('[data-action="fc-download-xlsx"]')).toBeVisible();
        await expect(page.locator('[data-action="fc-download-pdf"]')).toBeVisible();
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '03-result-conserved.png'),
            fullPage: true,
        });
    });

    test('黄灯态:issues 逐行点名 line_no+expected+actual,绝无假成功', async ({ page }) => {
        await bootFileconv(page, { convertBody: SUMMARY_ISSUES });
        await pickPdfAndRun(page);
        await expect(page.locator('.fc-banner.w')).toBeVisible();
        // 绿横幅绝不出现(状态诚实:有 issue 不显示"可信")。
        await expect(page.locator('.fc-banner.g')).toHaveCount(0);
        const issues = page.locator('.fc-issue');
        await expect(issues).toHaveCount(2);
        await expect(issues.nth(0)).toContainText('#17');
        await expect(issues.nth(0)).toContainText('1200.00');
        await expect(issues.nth(0)).toContainText('1300.00');
        await expect(issues.nth(1)).toContainText('#44');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '04-result-issues.png'),
            fullPage: true,
        });
    });

    test('no_text_layer:中性态诚实提示,无下载按钮无绿横幅', async ({ page }) => {
        await bootFileconv(page, { convertBody: SUMMARY_SCAN });
        await pickPdfAndRun(page);
        await expect(page.locator('.fc-banner.n')).toBeVisible();
        await expect(page.locator('.fc-banner.n')).toContainText('OCR');
        await expect(page.locator('.fc-banner.g')).toHaveCount(0);
        await expect(page.locator('[data-action="fc-download-xlsx"]')).toHaveCount(0);
        await expect(page.locator('[data-action="fc-download-pdf"]')).toHaveCount(0);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '05-no-text-layer.png'),
            fullPage: true,
        });
    });

    test('错误态:413 显示四语文案,上传区仍在可重试', async ({ page }) => {
        await bootFileconv(page, {
            convertBody: { detail: 'fileconv.file_too_large' },
            convertStatus: 413,
        });
        await pickPdfAndRun(page);
        await expect(page.locator('.intake-err')).toBeVisible();
        await expect(page.locator('.intake-err')).toContainText('20MB');
        await expect(page.locator('#fcDrop')).toBeVisible();
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '06-error-413.png'),
            fullPage: true,
        });
    });

    test('下载:点按钮真发 ?format=xlsx 并触发浏览器下载', async ({ page }) => {
        await bootFileconv(page, {});
        await pickPdfAndRun(page);
        await expect(page.locator('[data-action="fc-download-xlsx"]')).toBeVisible();
        const [download, request] = await Promise.all([
            page.waitForEvent('download'),
            page.waitForRequest((r) => r.url().includes('format=xlsx')),
            page.click('[data-action="fc-download-xlsx"]'),
        ]);
        expect(request.method()).toBe('POST');
        expect(download.suggestedFilename()).toBe('GL TTB.xlsx');
    });

    for (const lang of ['th', 'en', 'ja']) {
        test(`四语(${lang}):标题/横幅非原始 key`, async ({ page }) => {
            await bootFileconv(page, { lang });
            await pickPdfAndRun(page);
            await expect(page.locator('.fc-banner.g')).toBeVisible();
            const bannerText = await page.locator('.fc-banner.g').innerText();
            expect(bannerText).not.toContain('fileconv_conserved');
            const title = await page.locator('#v-fileconv h2').innerText();
            expect(title).not.toContain('fileconv_title');
            await page.screenshot({
                path: path.join(ARTIFACT_DIR, `07-lang-${lang}.png`),
                fullPage: true,
            });
        });
    }

    test('手机 390:结果区可见 + 无横向溢出', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await bootFileconv(page, { convertBody: SUMMARY_ISSUES });
        await pickPdfAndRun(page);
        await expect(page.locator('.fc-banner.w')).toBeVisible();
        const overflow = await page.evaluate(() => document.body.scrollWidth - window.innerWidth);
        expect(overflow, '手机视口不该出横向滚动').toBeLessThanOrEqual(1);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '08-mobile-390.png'),
            fullPage: true,
        });
    });
});
