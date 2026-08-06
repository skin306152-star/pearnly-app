/*
 * scripts/_pos_vat_summary_verify.cjs · 销项汇总包下载按钮(G3)真浏览器验收
 *
 * 照 _sales_dashboard_smoke.cjs 的路数:本地静态服 + 真产物(home.html / dist/main.js /
 * dist/home.css / i18n-data.js)+ 只桩 /api/**。文案期望值现场取页面里的真 window.I18N,
 * 不注入一个字。断言:
 *   ① 走势卡工具条里的「销项汇总包」按钮真的渲染且可见
 *   ② 点击 → 真实请求带对的 workspace_client_id/month/format=xlsx → 真 download 事件 →
 *      落盘字节与桩喂的一致(不是 0 字节、不是包着 HTML 错误页的假成功)
 *   ③ 端点失败 → toast 用现有机制弹出,文案是新增 i18n 键(不是裸 pos.unexpected 兜底)
 *
 * 用法(仓库根目录): node scripts/_pos_vat_summary_verify.cjs [截图目录]
 * 退出码 0 = 全过。截图默认落 tests/e2e/_artifacts/pos_vat_summary/。
 */
const fs = require('fs');
const path = require('path');
const { startStaticServer } = require('./_smoke_server.cjs');
const { chromium } = require('@playwright/test');

const ROOT = path.resolve(__dirname, '..');
const SHOTS = path.resolve(
    process.argv[2] || path.join(ROOT, 'tests/e2e/_artifacts/pos_vat_summary')
);

const p2 = (n) => String(n).padStart(2, '0');
const TODAY = new Date();
const THIS_MONTH = `${TODAY.getFullYear()}-${p2(TODAY.getMonth() + 1)}`;

// 假 xlsx 字节:够辨认非空、够辨认字节一致即可,不需要是真 zip 结构(内容不是本脚本的职责,
// 结构 golden 由 tests/unit/test_pos_vat_summary.py 锁)。
const FAKE_XLSX = Buffer.from('PK-fake-vat-summary-xlsx-bytes-for-e2e');

const REPORT_KPI = {
    gross: '0.00',
    sales_count: 0,
    avg_ticket: '0.00',
    refund: '0.00',
    cost: '0.00',
    gross_profit: '0.00',
    cost_complete: true,
};

function reportFor(params) {
    if (params.get('sections') === 'by_day') return { by_day: [] };
    return {
        kpi: REPORT_KPI,
        by_day: [],
        by_hour: null,
        by_method: {},
        top_products: [],
        by_cashier: [],
        prev_kpi: null,
        prev_range: null,
        heat: [],
        heat_range: { from: THIS_MONTH + '-01', to: THIS_MONTH + '-14' },
        live: { last_sale_at: null, open_shift: null },
    };
}

const serve = () => startStaticServer({ root: ROOT, index: 'home.html' });

async function stubApi(page, state) {
    await page.route('https://cdnjs.cloudflare.com/**', (r) => r.abort());
    await page.route('**/api/**', async (route) => {
        const req = route.request();
        const url = new URL(req.url());
        if (url.pathname === '/api/pos/admin/report') {
            await route.fulfill({ json: { ok: true, data: reportFor(url.searchParams) } });
            return;
        }
        if (url.pathname === '/api/pos/admin/vat-summary') {
            state.calls.push({
                workspace_client_id: url.searchParams.get('workspace_client_id'),
                month: url.searchParams.get('month'),
                format: url.searchParams.get('format'),
            });
            if (state.fail) {
                await route.fulfill({ status: 500, body: 'boom' });
                return;
            }
            await route.fulfill({
                status: 200,
                headers: {
                    'content-type':
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                },
                body: FAKE_XLSX,
            });
            return;
        }
        if (url.pathname === '/api/me') {
            await route.fulfill({ json: { email: 'vatpkg@e2e', role: 'owner', plan: 'pro' } });
            return;
        }
        await route.fulfill({ json: { ok: true, data: {} } });
    });
}

async function openPage(page, origin) {
    await page.goto(`${origin}/home.html`);
    await page.waitForFunction(() => typeof window.loadSalesReport === 'function');
    await page.evaluate(() => {
        document.body.classList.remove('workspace-gate-preboot');
        document.getElementById('workspace-gate-root')?.remove();
        window.getActiveWorkspaceClientId = () => 1;
        document.querySelectorAll('.page').forEach((p) => p.classList.remove('active'));
        document.getElementById('page-sales-report').classList.add('active');
        window.loadSalesReport();
    });
    await page.waitForSelector('#rep-t-vatpkg');
}

async function copyOf(page, key) {
    return page.evaluate((k) => window.I18N[window._currentLang][k], key);
}

async function shot(page, name) {
    await page.screenshot({ path: path.join(SHOTS, name), fullPage: false });
}

// ① 按钮真渲染且可见(量真几何,不 grep 类名)
async function buttonVisibleFlow(page) {
    const wantLabel = await copyOf(page, 'rep-vat-pkg');
    await page.evaluate(() =>
        document.getElementById('rep-trend-card').scrollIntoView({ block: 'center' })
    );
    const state = await page.evaluate(() => {
        const btn = document.getElementById('rep-t-vatpkg');
        const r = btn.getBoundingClientRect();
        return {
            text: btn.innerText.trim(),
            visible: r.width > 0 && r.height > 0 && getComputedStyle(btn).display !== 'none',
        };
    });
    await shot(page, '01-vatpkg-button.png');
    return { ok: state.visible && state.text === wantLabel, wantLabel, state };
}

// ② 点击 → 真实请求参数对 → 真 download 事件 → 落盘字节与桩喂的一致
async function downloadFlow(page, state) {
    const btn = page.locator('#rep-t-vatpkg');
    const [download] = await Promise.all([page.waitForEvent('download'), btn.click()]);
    const saved = path.join(SHOTS, 'downloaded.xlsx');
    await download.saveAs(saved);
    const bytes = fs.readFileSync(saved);
    const call = state.calls[state.calls.length - 1];
    return {
        ok:
            !!call &&
            call.workspace_client_id === '1' &&
            call.month === THIS_MONTH &&
            call.format === 'xlsx' &&
            download.suggestedFilename() === `pearnly_pos_vat_summary_${THIS_MONTH}.xlsx` &&
            bytes.equals(FAKE_XLSX),
        call,
        filename: download.suggestedFilename(),
        byteLength: bytes.length,
    };
}

// ③ 端点失败 → toast 弹出且文案是新 i18n 键(不是裸 pos.unexpected 兜底)
async function failureToastFlow(page, state) {
    state.fail = true;
    const wantMsg = await copyOf(page, 'rep-vat-pkg-fail');
    await page.locator('#rep-t-vatpkg').click();
    await page.waitForFunction(() => {
        const t = document.querySelector('.mp-toast.error');
        return t && t.classList.contains('show');
    });
    const toastText = await page.locator('.mp-toast.error span').innerText();
    await shot(page, '02-vatpkg-fail-toast.png');
    return { ok: toastText === wantMsg, wantMsg, toastText };
}

(async () => {
    fs.mkdirSync(SHOTS, { recursive: true });
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch();
    const page = await browser.newPage({
        viewport: { width: 1280, height: 900 },
        acceptDownloads: true,
    });
    page.on('pageerror', (e) => console.error('PAGEERROR:', e.message));
    await page.addInitScript(() => localStorage.setItem('mrpilot_token', 'vatpkg-e2e'));
    const state = { calls: [], fail: false };
    await stubApi(page, state);
    await openPage(page, origin);

    const report = {
        buttonVisibleFlow: await buttonVisibleFlow(page),
        downloadFlow: await downloadFlow(page, state),
        failureToastFlow: await failureToastFlow(page, state),
    };
    await browser.close();
    server.close();

    const failed = Object.keys(report).filter((k) => !report[k].ok);
    console.log(JSON.stringify(report, null, 2));
    console.log(failed.length ? `FAIL: ${failed.join(', ')}` : `PASS · 截图在 ${SHOTS}`);
    process.exit(failed.length ? 1 : 0);
})().catch((e) => {
    console.error('SMOKE CRASH', e);
    process.exit(2);
});
