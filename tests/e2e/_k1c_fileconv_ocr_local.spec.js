// Pearnly AI · K1c · 财务文件转换 OCR 增量 · 本地 stub 真浏览器验收(非 CI 用例 · 用完即删)
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**(同
// _k1b_fileconv_local.spec.js 先例)。K1c 增量验收:图片文件放行进 OCR 路、上传中态
// 诚实标「识别中」、ocr_incomplete/ocr_unavailable 拒绝横幅(绝无绿横幅/下载按钮)、
// closing_anchor issue 逐行点名、四语文案非原始 key、手机 390 无横溢。
// 截图存 tests/e2e/_artifacts/k1c/。
//
// 起法:npx playwright test tests/e2e/_k1c_fileconv_ocr_local.spec.js
/* global window, getComputedStyle, document */

const { test, expect } = require('@playwright/test');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const ROOT = path.resolve(__dirname, '..', '..');
const PORT = 8982;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'k1c');

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

// 真调回包同形(2026-07-13 本地真跑 bank_scb_02 两页件的实际 stats 形状)。
const SUMMARY_OCR_OK = {
    doc_type: 'bank_statement',
    status: 'ok',
    conserved: true,
    stats: {
        row_count: 11,
        opening_balance: '-35000.00',
        closing_balance: '-41356.00',
        engine: 'ocr_image_direct',
        pages: 2,
    },
    issue_count: 0,
    issues: [],
};

const SUMMARY_OCR_ANCHOR = {
    doc_type: 'bank_statement',
    status: 'ok',
    conserved: false,
    stats: { row_count: 10, engine: 'ocr_image_direct', pages: 1 },
    issue_count: 1,
    issues: [
        {
            kind: 'closing_anchor',
            line_no: 10,
            account: '',
            message: '印刷期末余额 ≠ 解析末行余额(疑漏行/截断)',
            expected: '-33481.00',
            actual: '-37880.00',
        },
    ],
};

const SUMMARY_INCOMPLETE = {
    doc_type: '',
    status: 'ocr_incomplete',
    conserved: true,
    stats: { reason: 'OCR 输出截断/不完整,拒绝出件' },
    issue_count: 0,
    issues: [],
};

const SUMMARY_UNAVAILABLE = {
    doc_type: '',
    status: 'ocr_unavailable',
    conserved: true,
    stats: { reason: 'OCR 引擎不可用' },
    issue_count: 0,
    issues: [],
};

async function boot(page, { lang = 'zh', convertBody = SUMMARY_OCR_OK, delayMs = 0 }) {
    await page.route('**/api/workorder/orders**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{"orders":[]}' })
    );
    await page.route('**/api/fileconv/convert**', async (r) => {
        if (delayMs) await new Promise((res) => setTimeout(res, delayMs));
        r.fulfill({
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
            window.localStorage.setItem('mrpilot_token_ai', 'tok-k1c');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [lang]
    );
    await page.goto(`${BASE}/static/dist/ai.html#/fileconv`);
    await page.waitForSelector('#fcDrop', { timeout: 15000 });
}

// K1c:图片(手机拍扫描件)——1x1 真 PNG 字节。
const PNG_1PX = Buffer.from(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
    'base64'
);

async function pickImageAndRun(page, name = 'scan.jpg') {
    await page.setInputFiles('#fcFileInput', {
        name,
        mimeType: 'image/jpeg',
        buffer: PNG_1PX,
    });
    await page.click('[data-action="fc-run"]');
}

test.describe('K1c · 图片→Excel OCR 增量(本地 stub 真浏览器)', () => {
    test('图片放行 + 识别中态诚实(fc-ocr-note 可见)→ 守恒绿横幅', async ({ page }) => {
        await boot(page, { delayMs: 900 });
        await pickImageAndRun(page);
        const note = page.locator('.fc-ocr-note');
        await expect(note).toBeVisible();
        const st = await note.evaluate((el) => {
            const s = getComputedStyle(el);
            return { display: s.display, visibility: s.visibility };
        });
        expect(st.display).not.toBe('none');
        expect(st.visibility).toBe('visible');
        await expect(page.locator('#fcBody [data-state="loading"]')).toBeVisible();
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '01-ocr-running.png'),
            fullPage: true,
        });
        await expect(page.locator('.fc-banner.g')).toBeVisible({ timeout: 5000 });
        // AI.format.money 负数形态 = -฿41,356.00
        await expect(page.locator('.fc-stats')).toContainText('฿41,356.00');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '02-ocr-conserved.png'),
            fullPage: true,
        });
    });

    test('图片选择被 validateFile 放行,PDF 的识别中提示不出现', async ({ page }) => {
        await boot(page, { delayMs: 600 });
        await page.setInputFiles('#fcFileInput', {
            name: 'gl.pdf',
            mimeType: 'application/pdf',
            buffer: Buffer.from('%PDF-1.4 stub'),
        });
        await page.click('[data-action="fc-run"]');
        await expect(page.locator('#fcBody [data-state="loading"]')).toBeVisible();
        await expect(page.locator('.fc-ocr-note')).toHaveCount(0);
    });

    test('ocr_incomplete:拒绝横幅诚实,无绿横幅无下载按钮', async ({ page }) => {
        await boot(page, { convertBody: SUMMARY_INCOMPLETE });
        await pickImageAndRun(page);
        await expect(page.locator('.fc-banner.n')).toBeVisible();
        await expect(page.locator('.fc-banner.n')).toContainText('截断');
        await expect(page.locator('.fc-banner.g')).toHaveCount(0);
        await expect(page.locator('[data-action="fc-download-xlsx"]')).toHaveCount(0);
        await expect(page.locator('[data-action="fc-download-pdf"]')).toHaveCount(0);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '03-ocr-incomplete.png'),
            fullPage: true,
        });
    });

    test('ocr_unavailable:拒绝横幅诚实,无绿横幅无下载按钮', async ({ page }) => {
        await boot(page, { convertBody: SUMMARY_UNAVAILABLE });
        await pickImageAndRun(page);
        await expect(page.locator('.fc-banner.n')).toBeVisible();
        await expect(page.locator('.fc-banner.g')).toHaveCount(0);
        await expect(page.locator('[data-action="fc-download-xlsx"]')).toHaveCount(0);
        await expect(page.locator('[data-action="fc-download-pdf"]')).toHaveCount(0);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '04-ocr-unavailable.png'),
            fullPage: true,
        });
    });

    test('closing_anchor issue 逐行点名(期望/实际),黄横幅无假成功', async ({ page }) => {
        await boot(page, { convertBody: SUMMARY_OCR_ANCHOR });
        await pickImageAndRun(page);
        await expect(page.locator('.fc-banner.w')).toBeVisible();
        await expect(page.locator('.fc-banner.g')).toHaveCount(0);
        const issue = page.locator('.fc-issue').first();
        await expect(issue).toContainText('#10');
        await expect(issue).toContainText('-33481.00');
        await expect(issue).toContainText('-37880.00');
        const chip = await issue.locator('.chip').innerText();
        expect(chip).not.toContain('closing_anchor'); // 有翻译,非原始 kind
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '05-closing-anchor.png'),
            fullPage: true,
        });
    });

    test('坏类型仍被挡(txt),错误文案非原始 key', async ({ page }) => {
        await boot(page, {});
        await page.setInputFiles('#fcFileInput', {
            name: 'notes.txt',
            mimeType: 'text/plain',
            buffer: Buffer.from('hello'),
        });
        await expect(page.locator('.intake-err')).toBeVisible();
        const err = await page.locator('.intake-err').innerText();
        expect(err).not.toContain('fileconv_err_bad_type');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '06-bad-type.png'),
            fullPage: true,
        });
    });

    for (const lang of ['th', 'en', 'ja']) {
        test(`四语(${lang}):ocr_incomplete 横幅非原始 key`, async ({ page }) => {
            await boot(page, { lang, convertBody: SUMMARY_INCOMPLETE });
            await pickImageAndRun(page);
            await expect(page.locator('.fc-banner.n')).toBeVisible();
            const text = await page.locator('.fc-banner.n').innerText();
            expect(text).not.toContain('fileconv_ocr_incomplete');
            expect(text.length).toBeGreaterThan(10);
            await page.screenshot({
                path: path.join(ARTIFACT_DIR, `07-incomplete-${lang}.png`),
                fullPage: true,
            });
        });
    }

    test('手机 390:识别中态与拒绝态无横向溢出', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await boot(page, { convertBody: SUMMARY_INCOMPLETE, delayMs: 700 });
        await pickImageAndRun(page);
        await expect(page.locator('.fc-ocr-note')).toBeVisible();
        let overflow = await page.evaluate(
            () => document.documentElement.scrollWidth - document.documentElement.clientWidth
        );
        expect(overflow).toBeLessThanOrEqual(1);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '08-mobile-running.png'),
            fullPage: true,
        });
        await expect(page.locator('.fc-banner.n')).toBeVisible({ timeout: 5000 });
        overflow = await page.evaluate(
            () => document.documentElement.scrollWidth - document.documentElement.clientWidth
        );
        expect(overflow).toBeLessThanOrEqual(1);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '09-mobile-incomplete.png'),
            fullPage: true,
        });
    });
});
