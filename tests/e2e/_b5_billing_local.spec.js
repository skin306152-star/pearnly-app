// /ai 设置页计费区(B5 老站对齐 #16)· 本地真浏览器验收(跑 static/dist 真构建产物)
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**(同
// _settings_entry_local.spec.js 先例)。被断言的 DOM/CSS 全来自真产物,stub 只兜后端响应。
//
// 验收:① 老板视角设置页出「OCR 余额」面板(余额/本月用量/费率)+「充值记录」面板;
// ② 三步充值真点击走完:金额→POST request 载荷对→银行卡+复制→上传凭证→POST upload-slip
//    multipart→收尾态(人工审核文案,不冒充已入账)→关弹窗记录里出现待审核行;
// ③ 四态:接口 500 → 错误块可重试;空记录 → 指路空态;员工视角 → 不露钱不给充值按钮;
// ④ 四语切换不露原始 bill_ key。截图存 tests/e2e/_artifacts/b5_billing/。
//
// 起法:npx playwright test tests/e2e/_b5_billing_local.spec.js
/* global window */

const { test, expect } = require('@playwright/test');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const ROOT = path.resolve(__dirname, '..', '..');

// 货币前缀从真源借,不在断言里写死:฿ 与数字之间垫不垫窄空格是全站排版口径,由
// ai-format.js 单点声明(tests/unit/test_ai_money_single_exit.py 守着「别处不许自己拼」)。
// 排版口径动一次就让六条 E2E 集体变红,是断言抄了不归它管的东西。这里只管数字对不对 ——
// 小数位/千分位/负号仍写死,那才是本例要验的。
const { BAHT } = require(path.join(ROOT, 'static', 'ai', 'ai-format.js'));

const PORT = 8994;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'b5_billing');

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

const ME = { username: 'skin', email: 'skin@example.com', tenant_name: 'skin' };
const OWNER_CREDITS = {
    has_tenant: true,
    is_owner: true,
    is_billing_exempt: false,
    balance_thb: 1234.5,
    pages_this_month: 42,
    tier_threshold: 200,
    current_rate: 1.5,
    user_breakdown: [],
};

// opts.credits: /api/me/credits 响应(或 {status:500});opts.history: 记录数组。
// history 用可变引用:上传凭证后 push 一条 pending,再拉记录就能看到(模拟后端真行为)。
async function boot(page, opts = {}) {
    const state = {
        credits: opts.credits || OWNER_CREDITS,
        history: opts.history || [],
        topupRequests: [],
        uploads: [],
    };
    // Playwright 路由按注册逆序匹配(后注册先查)——泛路由先注册、具体路由后注册,
    // 否则 **/api/me** 会把 /api/me/credits 一并吞掉(首版就栽在这)。
    await page.route('**/api/**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{}' })
    );
    await page.route('**/api/me**', (r) =>
        r.fulfill({ contentType: 'application/json', body: JSON.stringify(ME) })
    );
    await page.route('**/api/workorder/orders**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{"orders":[]}' })
    );
    await page.route('**/api/me/credits**', (r) => {
        if (state.credits && state.credits.__status) {
            return r.fulfill({
                status: state.credits.__status,
                contentType: 'application/json',
                body: '{}',
            });
        }
        return r.fulfill({ contentType: 'application/json', body: JSON.stringify(state.credits) });
    });
    await page.route('**/api/credits/topup/history**', (r) =>
        r.fulfill({ contentType: 'application/json', body: JSON.stringify(state.history) })
    );
    await page.route('**/api/credits/topup/request', (r) => {
        state.topupRequests.push(r.request().postDataJSON());
        return r.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({ request_id: 77, status: 'pending' }),
        });
    });
    await page.route('**/api/credits/topup/upload-slip/**', (r) => {
        state.uploads.push({
            url: r.request().url(),
            contentType: r.request().headers()['content-type'] || '',
        });
        state.history.unshift({
            id: 77,
            amount_thb: 500,
            payer_name: 'สมชาย',
            note: '',
            status: 'pending',
            slip_path: 'slips/77.jpg',
            review_note: '',
            created_at: '2026-07-27T10:00:00',
            reviewed_at: null,
        });
        return r.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, auto_approved: false, slip_path: 'slips/77.jpg' }),
        });
    });
    await page.addInitScript(
        ([l]) => {
            window.localStorage.setItem('mrpilot_token_ai', 'tok-b5billing');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [opts.lang || 'zh']
    );
    await page.goto(`${BASE}/static/dist/ai.html#/`);
    await page.waitForSelector('#footUser', { state: 'visible', timeout: 15000 });
    await page.locator('#footUser').click();
    return state;
}

test.describe('/ai 设置页计费区(本地 stub · 真构建产物)', () => {
    test('老板视角:余额三格 + 充值按钮 + 记录空态指路', async ({ page }) => {
        await boot(page);
        const wrap = page.locator('#stBillingWrap');
        await expect(wrap.locator('.bill-balance-v')).toHaveText(`${BAHT}1,234.50`);
        await expect(wrap.locator('.wosum .cell')).toHaveCount(3);
        await expect(wrap.locator('[data-action="bill-topup"]')).toBeVisible();
        // 空态不是干巴巴"暂无数据",要指路去点充值
        await expect(wrap.locator('[data-state="empty"]')).toBeVisible();
        await expect(wrap.locator('[data-state="empty"]')).toContainText('充值');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '01-owner-balance.png'),
            fullPage: true,
        });
    });

    test('三步充值全流程:金额→银行卡→凭证→待审核落记录', async ({ page }) => {
        const state = await boot(page);
        await page.locator('[data-action="bill-topup"]').click();

        // 步1:快捷 ฿500 → 下一步,POST 载荷必须是 {amount_thb:500}
        const modal = page.locator('#billTopupMask');
        await expect(modal).toBeVisible();
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '02-step1-amount.png') });
        await modal.locator('[data-bill-amt="500"]').click();
        await expect(modal.locator('#billAmt')).toHaveValue('500');
        await modal.locator('[data-action="bill-next"]').click();
        expect(state.topupRequests).toEqual([{ amount_thb: 500 }]);

        // 步2:银行卡 + 恰好金额警示 + 复制账号
        await expect(modal.locator('.bill-bank .ba')).toHaveText('230-0-91368-4');
        await expect(modal.locator('.bill-warn')).toContainText(`${BAHT}500.00`);
        await modal.locator('[data-action="bill-copy"]').click();
        await expect(modal.locator('[data-action="bill-copy"]')).toContainText('已复制');
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '03-step2-bank.png') });
        await modal.locator('[data-action="bill-next"]').click();

        // 步3:不传凭证直接提交要被拦;传了才走 multipart 上传
        await modal.locator('[data-action="bill-next"]').click();
        await expect(modal.locator('#billErr')).toContainText('请先上传转账凭证');
        await modal.locator('#billFile').setInputFiles({
            name: 'slip.jpg',
            mimeType: 'image/jpeg',
            buffer: Buffer.from('fake-slip-bytes'),
        });
        await expect(modal.locator('#billDz')).toContainText('slip.jpg');
        await modal.locator('#billPayer').fill('สมชาย');
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '04-step3-slip.png') });
        await modal.locator('[data-action="bill-next"]').click();

        // 收尾态:人工审核文案(不许冒充已入账),multipart 真发出去了
        await expect(modal.locator('.bill-done.wait')).toBeVisible();
        await expect(modal.locator('.bill-done .msg')).toContainText('人工审核');
        expect(state.uploads).toHaveLength(1);
        expect(state.uploads[0].url).toContain('/api/credits/topup/upload-slip/77');
        expect(state.uploads[0].contentType).toContain('multipart/form-data');
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '05-done-pending.png') });

        // 关弹窗 → 记录面板出现待审核行(状态徽章走状态词典色族)
        await modal.locator('[data-action="bill-back"]').click();
        await expect(page.locator('#billTopupMask')).toHaveCount(0);
        const row = page.locator('#stBillingWrap .bill-hrow').first();
        await expect(row).toContainText(`${BAHT}500.00`);
        await expect(row.locator('.st-badge')).toHaveText('待审核');
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '06-history-pending.png'),
            fullPage: true,
        });
    });

    test('金额校验:低于 ฿10 拦下,不发请求', async ({ page }) => {
        const state = await boot(page);
        await page.locator('[data-action="bill-topup"]').click();
        const modal = page.locator('#billTopupMask');
        await modal.locator('#billAmt').fill('5');
        await modal.locator('[data-action="bill-next"]').click();
        await expect(modal.locator('#billErr')).toContainText(`${BAHT}10`);
        expect(state.topupRequests).toHaveLength(0);
    });

    test('错误态:credits 接口 500 → 错误块可重试恢复', async ({ page }) => {
        const state = await boot(page, { credits: { __status: 500 } });
        const wrap = page.locator('#stBillingWrap');
        await expect(wrap.locator('[data-state="error"]')).toBeVisible();
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '07-error-state.png') });
        state.credits = OWNER_CREDITS; // 后端恢复 → 点重试要能起死回生
        await wrap.locator('[data-action="retry"]').click();
        await expect(wrap.locator('.bill-balance-v')).toHaveText(`${BAHT}1,234.50`);
    });

    test('员工视角:不露钱、不给充值按钮、不拉记录', async ({ page }) => {
        await boot(page, { credits: { has_tenant: true, is_owner: false, my_invoice_count: 7 } });
        const wrap = page.locator('#stBillingWrap');
        await expect(wrap.locator('.bill-emp-hint')).toBeVisible();
        await expect(wrap.locator('.bill-emp-count')).toContainText('7');
        await expect(wrap.locator('[data-action="bill-topup"]')).toHaveCount(0);
        await expect(wrap.locator('.bill-balance-v')).toHaveCount(0);
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '08-employee.png') });
    });

    for (const lang of ['th', 'en', 'ja']) {
        test(`${lang} 计费区+弹窗不露原始 key`, async ({ page }) => {
            await boot(page, { lang });
            const wrap = page.locator('#stBillingWrap');
            await expect(wrap.locator('.bill-balance-v')).toBeVisible();
            expect(await wrap.innerText(), `${lang} 计费区漏翻译`).not.toContain('bill_');
            await page.locator('[data-action="bill-topup"]').click();
            const modal = page.locator('#billTopupMask');
            await expect(modal).toBeVisible();
            expect(await modal.innerText(), `${lang} 弹窗漏翻译`).not.toContain('bill_');
            await page.screenshot({ path: path.join(ARTIFACT_DIR, `09-modal-${lang}.png`) });
        });
    }
});
