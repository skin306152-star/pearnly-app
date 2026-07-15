// Pearnly AI · IN-0d · 客户名录批量导入模态 · 本地 stub 真浏览器验收(非 CI 用例 · 用完即删)
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**(同
// _k1b_fileconv_local.spec.js 先例):闸探针 200 → 客户目录页渲染,#/clients 真实
// 打开导入模态,走 上传 → 预览三态 → 确认 → 结果卡 → 客户列表刷新出现新客户 全链路。
// 验收:三态(valid/skip/error)isVisible+getComputedStyle、计数条逐项点名、四语标题
// 非原始 key、手机 390 无横溢。截图存 tests/e2e/_artifacts/in0d/。
//
// 起法:npx playwright test tests/e2e/_in0d_client_import_verify.spec.js
/* global document, window, getComputedStyle */

const { test, expect } = require('@playwright/test');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const ROOT = path.resolve(__dirname, '..', '..');
const PORT = 8983;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'in0d');

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

const PREVIEW_OK = {
    preview: [
        { row_index: 0, name: 'บริษัท อัลฟ่า จำกัด', tax_id: '0105546015062', status: 'valid' },
        { row_index: 1, name: 'บริษัท เบต้า จำกัด', tax_id: '0105551000027', status: 'valid' },
        {
            row_index: 2,
            name: 'บริษัท ซ้ำ จำกัด',
            tax_id: '0105551000019',
            status: 'skip',
            reason: 'workspace.tax_id_duplicate',
        },
        { row_index: 3, name: '', status: 'error', reason: 'client_import.err_missing_name' },
    ],
    headers: ['ชื่อลูกค้า', 'เลขประจำตัวผู้เสียภาษี'],
    matched: { name: 0, tax_id: 1 },
    truncated: false,
    total: 4,
    valid_count: 2,
    skip_count: 1,
    error_count: 1,
};

const COMMIT_OK = {
    results: [
        {
            row_index: 0,
            name: 'บริษัท อัลฟ่า จำกัด',
            tax_id: '0105546015062',
            status: 'created',
            id: 101,
        },
        {
            row_index: 1,
            name: 'บริษัท เบต้า จำกัด',
            tax_id: '0105551000027',
            status: 'created',
            id: 102,
        },
        {
            row_index: 2,
            name: 'บริษัท ซ้ำ จำกัด',
            tax_id: '0105551000019',
            status: 'skip',
            reason: 'workspace.tax_id_duplicate',
        },
        { row_index: 3, name: '', status: 'error', reason: 'client_import.err_missing_name' },
    ],
    created: 2,
    skipped: 1,
    errors: 1,
    total: 4,
};

const MATRIX_EMPTY = { clients: [], cells: [] };
const MATRIX_AFTER = {
    clients: [
        { id: 101, name: 'บริษัท อัลฟ่า จำกัด', tax_id: '0105546015062', profile_completeness: 0 },
        { id: 102, name: 'บริษัท เบต้า จำกัด', tax_id: '0105551000027', profile_completeness: 0 },
    ],
    cells: [],
};

async function bootClients(page, { lang = 'zh', parseBody = PREVIEW_OK, parseStatus = 200 } = {}) {
    let matrixCalls = 0;
    await page.route('**/api/workspace/clients/can-create**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{"allowed":true}' })
    );
    await page.route('**/api/tax-profile/matrix**', (r) => {
        matrixCalls += 1;
        const body = matrixCalls === 1 ? MATRIX_EMPTY : MATRIX_AFTER;
        return r.fulfill({ contentType: 'application/json', body: JSON.stringify(body) });
    });
    await page.route('**/api/workspace/clients/import/parse**', (r) =>
        r.fulfill({
            status: parseStatus,
            contentType: 'application/json',
            body: JSON.stringify(parseBody),
        })
    );
    await page.route('**/api/workspace/clients/import/commit**', (r) =>
        r.fulfill({ contentType: 'application/json', body: JSON.stringify(COMMIT_OK) })
    );
    await page.route('**/api/**', (r) => {
        const url = r.request().url();
        if (
            url.includes('/api/workspace/clients/can-create') ||
            url.includes('/api/tax-profile/matrix') ||
            url.includes('/api/workspace/clients/import/')
        ) {
            return r.fallback();
        }
        return r.fulfill({ contentType: 'application/json', body: '{}' });
    });
    await page.addInitScript(
        ([l]) => {
            window.localStorage.setItem('mrpilot_token', 'tok-in0d');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [lang]
    );
    await page.goto(`${BASE}/static/dist/ai.html#/clients`);
    await page.waitForSelector('#v-clients.on', { timeout: 15000 });
    await page.waitForSelector('#clientsImportBtn', { state: 'visible', timeout: 15000 });
}

async function pickFileAndOpenModal(page) {
    await page.click('#clientsImportBtn');
    await page.waitForSelector('#clientImportMask.on', { timeout: 8000 });
    await page.setInputFiles('#ciFileInput', {
        name: 'clients.xlsx',
        mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        buffer: Buffer.from('stub-xlsx'),
    });
}

test.describe('IN-0d · 客户名录批量导入(本地 stub 真浏览器)', () => {
    test('打开模态:上传区可见,点击后弹层出现(isVisible+getComputedStyle)', async ({ page }) => {
        await bootClients(page);
        const btn = page.locator('#clientsImportBtn');
        await expect(btn).toBeVisible();
        const st = await btn.evaluate((el) => {
            const s = getComputedStyle(el);
            return { display: s.display, visibility: s.visibility };
        });
        expect(st.display).not.toBe('none');
        await btn.click();
        await expect(page.locator('#clientImportMask')).toHaveClass(/\bon\b/);
        await expect(page.locator('#ciDrop')).toBeVisible();
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '01-modal-empty.png') });
    });

    test('预览三态:valid/skip/error 逐行可见 + 计数条点名', async ({ page }) => {
        await bootClients(page);
        await pickFileAndOpenModal(page);
        await expect(page.locator('.ci-row')).toHaveCount(4);
        const counts = await page.locator('.ci-counts').innerText();
        expect(counts).toContain('2');
        expect(counts).toContain('1');
        // 三态 chip 都出现且颜色可辨(isVisible + getComputedStyle,不只 grep 类名)。
        const chips = page.locator('.ci-row .chip');
        await expect(chips).toHaveCount(4);
        const chipColors = await chips.evaluateAll((els) =>
            els.map((el) => getComputedStyle(el).color)
        );
        expect(new Set(chipColors).size).toBeGreaterThan(1); // 三态颜色不该全一样
        // 错误行显示原因文案(不是裸 i18n key)。
        await expect(page.locator('.ci-reason').first()).toBeVisible();
        const reasonText = await page.locator('.ci-reason').first().innerText();
        expect(reasonText).not.toContain('client_import.err_missing_name');
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '02-preview-three-states.png') });
    });

    test('确认导入 → 结果卡 → 客户列表刷新出现新客户', async ({ page }) => {
        await bootClients(page);
        await pickFileAndOpenModal(page);
        await page.waitForSelector('[data-action="ci-confirm"]');
        const [commitReq] = await Promise.all([
            page.waitForRequest((r) => r.url().includes('/import/commit') && r.method() === 'POST'),
            page.click('[data-action="ci-confirm"]'),
        ]);
        expect(commitReq.method()).toBe('POST');
        await expect(page.locator('.ci-result-hd')).toBeVisible();
        const resultText = await page.locator('.ci-counts').innerText();
        expect(resultText).toContain('2');
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '03-result-card.png') });

        await page.click('[data-action="ci-close"]');
        await expect(page.locator('#clientImportMask')).toHaveCount(0);
        // 客户列表刷新:关闭后目录页应已重拉矩阵,出现两位新客户。
        await expect(page.locator('.cl-row')).toHaveCount(2, { timeout: 5000 });
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '04-clients-list-refreshed.png') });
    });

    test('确认按钮零 valid 行时禁用(全错误文件不该能点确认)', async ({ page }) => {
        await bootClients(page, {
            parseBody: {
                ...PREVIEW_OK,
                preview: [
                    {
                        row_index: 0,
                        name: '',
                        status: 'error',
                        reason: 'client_import.err_missing_name',
                    },
                ],
                valid_count: 0,
                skip_count: 0,
                error_count: 1,
                total: 1,
            },
        });
        await pickFileAndOpenModal(page);
        await expect(page.locator('[data-action="ci-confirm"]')).toBeDisabled();
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '05-confirm-disabled.png') });
    });

    for (const lang of ['th', 'en', 'ja']) {
        test(`四语(${lang}):标题/按钮非原始 key`, async ({ page }) => {
            await bootClients(page, { lang });
            await pickFileAndOpenModal(page);
            const title = await page.locator('.mh h3').innerText();
            expect(title).not.toContain('client_import_title');
            const confirmText = await page.locator('[data-action="ci-confirm"]').innerText();
            expect(confirmText).not.toContain('client_import_confirm_btn');
            await page.screenshot({
                path: path.join(ARTIFACT_DIR, `06-lang-${lang}.png`),
                fullPage: true,
            });
        });
    }

    test('手机 390:预览表可见 + 无横向溢出', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await bootClients(page);
        await pickFileAndOpenModal(page);
        await expect(page.locator('.ci-row').first()).toBeVisible();
        const overflow = await page.evaluate(() => document.body.scrollWidth - window.innerWidth);
        expect(overflow, '手机视口不该出横向滚动').toBeLessThanOrEqual(1);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '07-mobile-390.png'),
            fullPage: true,
        });
    });
});
