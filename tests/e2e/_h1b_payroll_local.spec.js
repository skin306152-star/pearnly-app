// Pearnly AI · H1b · 工资表 ภ.ง.ด.1 工具卡 · 本地 stub 真浏览器验收(非 CI 用例 · 照
// _k1b_fileconv_local.spec.js 范式)
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**:闸探针 200 →
// 进工作台,#/payroll 真渲染。验收:选客户+期间→上传→列映射确认 UI 可见→确认提交→
// 结果区(合计+issues 逐行点名)→三下载按钮可见并真触发请求;模板命中(template_hit)
// 跳过映射确认直接出结果;四语切换;手机 390 无横溢。截图存 tests/e2e/_artifacts/h1b/。
//
// 起法:npx playwright test tests/e2e/_h1b_payroll_local.spec.js
/* global document, window, getComputedStyle */

const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8982;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'h1b');

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT);
});

test.afterAll(() => {
    localServer.stop(server);
});

const CLIENTS = { clients: [{ id: 7, name: 'Sister Makeup' }] };

const PARSE_NO_TEMPLATE = {
    header: [
        'รหัสเงินได้',
        'ลำดับ',
        'เลข 13 หลัก',
        'คำนำหน้า',
        'ชื่อ',
        'นามสกุล',
        'วันที่จ่าย',
        'จำนวนเงิน',
        'ภาษีหัก',
        'เงื่อนไข',
    ],
    preview_rows: [
        ['40(1)', 1, '3650100697428', 'นางสาว', 'สมหญิง', 'ใจดี', 31052569, 13000, 0, 1],
    ],
    guessed: {
        employee_id: { column: 2, confidence: 'high', reason: '13位+mod-11通过' },
        title: { column: 3, confidence: 'high', reason: 'title tokens' },
        first_name: { column: 4, confidence: 'medium', reason: 'text col' },
        last_name: { column: 5, confidence: 'medium', reason: 'text col' },
        paid_amount: { column: 7, confidence: 'medium', reason: 'numeric salary range' },
        wht_amount: { column: 8, confidence: 'medium', reason: 'mostly zero' },
        paid_date: { column: 6, confidence: 'medium', reason: 'parses as date' },
        income_code: { column: 0, confidence: 'high', reason: 'has 40(' },
    },
    template_hit: false,
    payer_id_candidate: '0105548082417',
    required_fields: ['employee_id', 'title', 'first_name', 'last_name', 'paid_amount'],
    guessable_fields: [
        'employee_id',
        'paid_amount',
        'wht_amount',
        'title',
        'first_name',
        'last_name',
        'paid_date',
        'income_code',
    ],
    income_code: '40(1)',
    fixed_values: {},
};

const COMMIT_CLEAN = {
    row_count: 2,
    totals: { paid_amount: '25040', wht_amount: '0' },
    declared_total: '25040',
    issues: [],
    template_saved: true,
};

const COMMIT_ISSUES = {
    row_count: 2,
    totals: { paid_amount: '25040', wht_amount: '0' },
    declared_total: '25040',
    issues: [
        {
            kind: 'paid_date_out_of_period',
            field: 'paid_date',
            message: '支付日不在申报期 2569-06 内',
            row_no: 1,
            value: '2026-05-31',
        },
    ],
    template_saved: true,
};

async function bootPayroll(
    page,
    { lang = 'zh', parseBody = PARSE_NO_TEMPLATE, commitBody = COMMIT_CLEAN }
) {
    await page.route('**/api/workorder/orders**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{"orders":[]}' })
    );
    await page.route('**/api/workspace/clients**', (r) =>
        r.fulfill({ contentType: 'application/json', body: JSON.stringify(CLIENTS) })
    );
    await page.route('**/api/payroll/parse**', (r) =>
        r.fulfill({ contentType: 'application/json', body: JSON.stringify(parseBody) })
    );
    await page.route('**/api/payroll/commit**', (r) =>
        r.fulfill({ contentType: 'application/json', body: JSON.stringify(commitBody) })
    );
    await page.route('**/api/payroll/output**', (r) => {
        const url = r.request().url();
        const kind = /kind=(\w+)/.exec(url)[1];
        const mediaType =
            kind === 'keying'
                ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                : 'text/plain; charset=utf-8';
        return r.fulfill({
            status: 200,
            contentType: mediaType,
            headers: {
                'Content-Disposition': `attachment; filename="payroll.txt"; filename*=UTF-8''PND1_${kind}.txt`,
            },
            body: Buffer.from('stub-output'),
        });
    });
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
            window.localStorage.setItem('mrpilot_token_ai', 'tok-h1b');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [lang]
    );
    await page.goto(`${BASE}/static/dist/ai.html#/payroll`);
    await page.waitForSelector('#prClientSel', { timeout: 15000 });
}

async function pickClientPeriodAndUpload(page) {
    await page.selectOption('#prClientSel', '7');
    // P1-3:账期从裸文本手输换成下拉(periodOptions 生成"当月+往前 13 个月"佛历
    // YYYY-MM);2026-07 起当月为 2569-07,2569-05 在往前 13 个月窗口内必定在场。
    // selectOption 走浏览器原生 select 交互,自带 input/change 事件,不必再手工
    // press Tab 补触发(那是给裸文本输入框的 blur→change 边界情况准备的,select 不适用)。
    await page.selectOption('#prPeriodInput', '2569-05');
    await page.setInputFiles('#prFileInput', {
        name: 'payroll.xlsx',
        mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        buffer: Buffer.from('stub-xlsx'),
    });
}

test.describe('H1b · 工资表 ภ.ง.ด.1 工具卡视图(本地 stub 真浏览器)', () => {
    test('空态:导航项/客户期间选择器/上传区可见,视图互斥', async ({ page }) => {
        await bootPayroll(page, {});
        await expect(page.locator('#navPayroll')).toBeVisible();
        const drop = page.locator('#prDrop');
        await expect(drop).toBeVisible();
        const st = await drop.evaluate((el) => {
            const s = getComputedStyle(el);
            return { display: s.display, visibility: s.visibility };
        });
        expect(st.display).not.toBe('none');
        expect(st.visibility).toBe('visible');
        await expect(page.locator('#v-payroll')).toHaveClass(/\bon\b/);
        await expect(page.locator('#v-fileconv')).not.toHaveClass(/\bon\b/);
        const title = await page.locator('#v-payroll h2').innerText();
        expect(title.length).toBeGreaterThan(0);
        expect(title).not.toContain('payroll_title');
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '01-empty-zh.png'), fullPage: true });
    });

    test('列映射确认 UI:低置信/缺失字段留空强制人补,必填齐全才可提交', async ({ page }) => {
        await bootPayroll(page, {});
        await pickClientPeriodAndUpload(page);
        await expect(page.locator('.pr-map-row')).toHaveCount(8);
        // 猜列已预选,确认按钮应可点(全部必填字段都命中)。
        const confirmBtn = page.locator('[data-action="pr-confirm"]');
        await expect(confirmBtn).toBeVisible();
        await expect(confirmBtn).toBeEnabled();
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '02-mapping.png'), fullPage: true });
    });

    test('确认提交:结果区合计 + 校验全过绿横幅 + 三下载按钮可见', async ({ page }) => {
        await bootPayroll(page, {});
        await pickClientPeriodAndUpload(page);
        await page.click('[data-action="pr-confirm"]');
        await expect(page.locator('.fc-banner.g')).toBeVisible();
        await expect(page.locator('.pr-stats')).toContainText('25,040.00');
        await expect(page.locator('[data-kind="keying"]')).toBeVisible();
        await expect(page.locator('[data-kind="attach"]')).toBeVisible();
        await expect(page.locator('[data-kind="central"]')).toBeVisible();
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '03-result-clean.png'),
            fullPage: true,
        });
    });

    test('issues 逐行点名:黄灯态不假装全过,绝无绿横幅', async ({ page }) => {
        await bootPayroll(page, { commitBody: COMMIT_ISSUES });
        await pickClientPeriodAndUpload(page);
        await page.click('[data-action="pr-confirm"]');
        await expect(page.locator('.fc-banner.w')).toBeVisible();
        await expect(page.locator('.fc-banner.g')).toHaveCount(0);
        const issue = page.locator('.pr-issue');
        await expect(issue).toHaveCount(1);
        await expect(issue.nth(0)).toContainText('#1');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '04-result-issues.png'),
            fullPage: true,
        });
    });

    test('模板命中:template_hit=true 跳过映射确认直接出结果', async ({ page }) => {
        const templateHitParse = Object.assign({}, PARSE_NO_TEMPLATE, { template_hit: true });
        await bootPayroll(page, { parseBody: templateHitParse });
        await pickClientPeriodAndUpload(page);
        await expect(page.locator('.fc-banner.g')).toBeVisible({ timeout: 5000 });
        // 映射表格不该出现(自动跳过了确认这一步)。
        await expect(page.locator('.pr-map-row')).toHaveCount(0);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '05-template-hit.png'),
            fullPage: true,
        });
    });

    test('下载:点击产出按钮真发 GET /api/payroll/output', async ({ page }) => {
        await bootPayroll(page, {});
        await pickClientPeriodAndUpload(page);
        await page.click('[data-action="pr-confirm"]');
        await expect(page.locator('[data-kind="attach"]')).toBeVisible();
        const [download, request] = await Promise.all([
            page.waitForEvent('download'),
            page.waitForRequest(
                (r) => r.url().includes('/api/payroll/output') && r.url().includes('kind=attach')
            ),
            page.click('[data-kind="attach"]'),
        ]);
        expect(request.method()).toBe('GET');
        expect(download.suggestedFilename()).toContain('attach');
    });

    for (const lang of ['th', 'en', 'ja']) {
        test(`四语(${lang}):标题/横幅非原始 key`, async ({ page }) => {
            await bootPayroll(page, { lang });
            await pickClientPeriodAndUpload(page);
            await page.click('[data-action="pr-confirm"]');
            await expect(page.locator('.fc-banner.g')).toBeVisible();
            const bannerText = await page.locator('.fc-banner.g').innerText();
            expect(bannerText).not.toContain('payroll_conserved');
            const title = await page.locator('#v-payroll h2').innerText();
            expect(title).not.toContain('payroll_title');
            await page.screenshot({
                path: path.join(ARTIFACT_DIR, `06-lang-${lang}.png`),
                fullPage: true,
            });
        });
    }

    test('手机 390:结果区可见 + 无横向溢出', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await bootPayroll(page, { commitBody: COMMIT_ISSUES });
        await pickClientPeriodAndUpload(page);
        await page.click('[data-action="pr-confirm"]');
        await expect(page.locator('.fc-banner.w')).toBeVisible();
        const overflow = await page.evaluate(() => document.body.scrollWidth - window.innerWidth);
        expect(overflow, '手机视口不该出横向滚动').toBeLessThanOrEqual(1);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '07-mobile-390.png'),
            fullPage: true,
        });
    });
});
