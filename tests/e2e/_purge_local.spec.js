// 按账套清空数据 · 本地真浏览器验收(跑 static/dist 真构建产物)
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**(同
// _k1b_fileconv_local.spec.js 先例)。被断言的 DOM/CSS 全来自真产物;purge 端点回的是
// 真格式的 NDJSON,验的是前端确实在按流里的行画进度,不是自己编的动画。
//
// 验收:客户页有「清除数据」按钮 → 弹窗选账套 → 确认屏显示目标与不可撤销警告 →
// 跑进度(进度条按流推进)→ 完成后重拉列表。截图存 tests/e2e/_artifacts/purge/。
//
// 起法:npx playwright test tests/e2e/_purge_local.spec.js
/* global window */

const { test, expect } = require('@playwright/test');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const ROOT = path.resolve(__dirname, '..', '..');
const PORT = 8989;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'purge');

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

const CLIENTS = [
    { id: 1, name: 'บริษัท ซินเซียร์ไอซ์ จำกัด', tax_id: '0105546015062' },
    { id: 2, name: 'บริษัท ซิสเตอร์ เมคอัพ จำกัด', tax_id: '0105567178203' },
];

const MATRIX = { period: '2569-06', clients: CLIENTS, obligation_codes: [], cells: [] };

// 真端点逐表吐一行;这里照同一格式回,前端解析路径与线上一致。
const NDJSON = [
    '{"step":"child","label":"work_order_items","deleted":12,"done":1,"total":4,"ok":true}',
    '{"step":"table","label":"ocr_history","deleted":340,"done":2,"total":4,"ok":true}',
    '{"step":"subject","label":"workspace_clients","deleted":0,"done":3,"total":4,"ok":true}',
    '{"step":"finished","deleted_total":352,"files_removed":7,"leftover":[],"ok":true}',
].join('\n');

let matrixCalls = 0;

async function boot(page, lang = 'zh') {
    matrixCalls = 0;
    await page.route('**/api/**', (r) => {
        const p = new URL(r.request().url()).pathname;
        if (p.endsWith('/purge')) {
            return r.fulfill({ status: 200, contentType: 'application/x-ndjson', body: NDJSON });
        }
        if (p.endsWith('/purge-periods')) {
            return r.fulfill({
                contentType: 'application/json',
                body: '{"periods":[{"period":"2569-05","orders":2},{"period":"2569-04","orders":1}]}',
            });
        }
        if (p === '/api/tax-profile/matrix') {
            matrixCalls += 1;
            return r.fulfill({ contentType: 'application/json', body: JSON.stringify(MATRIX) });
        }
        if (p === '/api/me') {
            return r.fulfill({ contentType: 'application/json', body: '{"username":"skin"}' });
        }
        if (p === '/api/workspace/clients/can-create') {
            return r.fulfill({ contentType: 'application/json', body: '{"allowed":true}' });
        }
        if (p === '/api/workorder/orders') {
            return r.fulfill({ contentType: 'application/json', body: '{"orders":[]}' });
        }
        return r.fulfill({ contentType: 'application/json', body: '{}' });
    });
    await page.addInitScript(
        ([l]) => {
            window.localStorage.setItem('mrpilot_token_ai', 'tok-purge');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [lang]
    );
    await page.goto(`${BASE}/static/dist/ai.html#/clients`);
    await page.waitForSelector('#clientsPurgeBtn', { state: 'visible', timeout: 15000 });
}

test.describe('按账套清空数据(本地 stub · 真构建产物)', () => {
    test('客户页有「清除数据」按钮,且不挨着主 CTA', async ({ page }) => {
        await boot(page);
        const purge = page.locator('#clientsPurgeBtn');
        await expect(purge).toBeVisible();
        const pb = await purge.boundingBox();
        const nb = await page.locator('#clientsNewBtn').boundingBox();
        expect(pb.x, '破坏性按钮该在主 CTA 左侧,不挨着').toBeLessThan(nb.x);
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '01-clients-btn.png') });
    });

    test('选账套 → 确认屏点名目标 + 不可撤销警告', async ({ page }) => {
        await boot(page);
        await page.locator('#clientsPurgeBtn').click();
        await expect(page.locator('#purgeMask')).toBeVisible();

        // 没选之前「下一步」必须是禁用的,不许直接往下走
        const next = page.locator('[data-action="pg-next"]');
        await expect(next).toBeDisabled();
        await expect(page.locator('.pg-opt')).toHaveCount(2);
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '02-pick.png') });

        await page.locator('.pg-opt input[value="2"]').check();
        await expect(next).toBeEnabled();
        await next.click();

        const warn = page.locator('.pg-warn');
        await expect(warn).toBeVisible();
        // 确认屏必须点名删的是哪一家,不能只说"确定吗"
        await expect(page.locator('.pg-target')).toContainText('เมคอัพ');
        await expect(page.locator('.pg-target')).toContainText('0105567178203');
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '03-confirm.png') });
    });

    test('执行 → 进度按流推进 → 完成后重拉列表', async ({ page }) => {
        await boot(page);
        const before = matrixCalls;

        await page.locator('#clientsPurgeBtn').click();
        await page.locator('.pg-opt input[value="1"]').check();
        await page.locator('[data-action="pg-next"]').click();
        await page.locator('[data-action="pg-run"]').click();

        await expect(page.locator('.pg-done')).toBeVisible({ timeout: 15000 });
        // 数字必须来自流里的 finished 行,不是写死的
        await expect(page.locator('.pg-status')).toContainText('352');
        await expect(page.locator('.pg-status')).toContainText('7');
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '04-done.png') });

        expect(matrixCalls, '清完必须重拉矩阵,否则页面还显示清除前的旧数').toBeGreaterThan(before);

        await page.locator('[data-action="pg-finish"]').click();
        await expect(page.locator('#purgeMask')).toHaveCount(0);
    });

    // 2026-07-26 线上事故的形状:每条 DELETE 都「成功」,却漏删 1648 行子数据,界面报
    // 「清除完毕」。现在结论以删完真回数为准,有残留一律按失败红着报并列出剩几行。
    test('有残留必须报失败(不是"清除完毕"),并列出剩几行', async ({ page }) => {
        await boot(page);
        await page.route('**/api/workspace/clients/*/purge', (r) =>
            r.fulfill({
                status: 200,
                contentType: 'application/x-ndjson',
                body:
                    '{"step":"child","label":"work_order_items","deleted":0,"done":1,"total":2,"ok":true}\n' +
                    '{"step":"finished","deleted_total":0,"files_removed":0,' +
                    '"leftover":["work_order_items"],' +
                    '"leftover_detail":[{"table":"work_order_items","rows":105}],"ok":false}\n',
            })
        );
        await page.locator('#clientsPurgeBtn').click();
        await page.locator('.pg-opt input[value="1"]').check();
        await page.locator('[data-action="pg-next"]').click();
        await page.locator('[data-action="pg-run"]').click();

        await expect(page.locator('.pg-failed')).toBeVisible({ timeout: 15000 });
        await expect(page.locator('.pg-done')).toHaveCount(0, {
            timeout: 5000,
        });
        await expect(page.locator('.pg-leftover')).toContainText('work_order_items');
        await expect(page.locator('.pg-leftover'), '要说清还剩几行').toContainText('105');
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '06-leftover-failed.png') });
    });

    test('账期下拉只列真有数据的期,选了期请求必须带 period', async ({ page }) => {
        await boot(page);
        let purgeUrl = '';
        await page.route('**/purge?**', (r) => {
            purgeUrl = r.request().url();
            return r.fulfill({
                status: 200,
                contentType: 'application/x-ndjson',
                body:
                    '{"step":"table","label":"work_orders","deleted":2,"done":1,"total":2,"ok":true}\n' +
                    '{"step":"finished","deleted_total":2,"files_removed":3,"leftover":[],' +
                    '"leftover_detail":[],"period":"2569-05","ok":true}\n',
            });
        });

        await page.locator('#clientsPurgeBtn').click();
        await page.locator('.pg-opt input[value="1"]').check();
        await page.locator('[data-action="pg-next"]').click();

        // 默认「全部账期」+ 两个真账期,不摆空选项
        const sel = page.locator('#pgPeriod');
        await expect(sel).toBeVisible({ timeout: 10000 });
        await expect(sel.locator('option')).toHaveCount(3);
        await expect(sel).toHaveValue('');

        // 选了期,警告文案要换成「只清这一期」的说法
        await sel.selectOption('2569-05');
        await expect(page.locator('.pg-note')).toContainText('只清这一个账期');
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '07-period.png') });

        await page.locator('[data-action="pg-run"]').click();
        await expect(page.locator('.pg-done')).toBeVisible({ timeout: 15000 });
        expect(purgeUrl, '选了账期就必须把 period 带上,否则会清掉整个套账').toContain(
            'period=2569-05'
        );
    });

    test('不选账期 = 全部账期,请求不带 period', async ({ page }) => {
        await boot(page);
        let purgeUrl = '';
        await page.route('**/*/purge**', (r) => {
            purgeUrl = r.request().url();
            return r.fulfill({ status: 200, contentType: 'application/x-ndjson', body: NDJSON });
        });
        await page.locator('#clientsPurgeBtn').click();
        await page.locator('.pg-opt input[value="1"]').check();
        await page.locator('[data-action="pg-next"]').click();
        await expect(page.locator('#pgPeriod')).toBeVisible({ timeout: 10000 });
        await page.locator('[data-action="pg-run"]').click();
        await expect(page.locator('.pg-done')).toBeVisible({ timeout: 15000 });
        expect(purgeUrl).not.toContain('period=');
    });

    for (const lang of ['th', 'en', 'ja']) {
        test(`${lang} 不露原始 key`, async ({ page }) => {
            await boot(page, lang);
            await page.locator('#clientsPurgeBtn').click();
            await expect(page.locator('#purgeMask')).toBeVisible();
            await page.locator('.pg-opt input[value="1"]').check();
            await page.locator('[data-action="pg-next"]').click();
            const text = await page.locator('#purgeMask').innerText();
            expect(text, `${lang} 漏了翻译`).not.toContain('purge_');
            await page.screenshot({ path: path.join(ARTIFACT_DIR, `05-confirm-${lang}.png`) });
        });
    }
});
