// Pearnly E2E · 32 对账中心 · 对账进行中切换类型不再卡死(2026-08-13)
// ============================================================
// 生产实锤(C 档全入口实测 entry5 TIMEOUT 的根因):银行对账还在跑(processing 视图)时
// 切到「收入对账」tab,确认「切换将清空」后 —— 旧代码不废弃在途 run:
//   ① RX.running 永远卡 true → income tab 双卡布满后「开始对账」按钮死灰;
//   ② 旧 bank job 的后台轮询收尾时把 fail/结果视图砸到 income tab 上(视图劫持)。
// 修法 = RX.runSeq 所有权票据(recon-center-x.ts):切类型/清空即 +1,在途 submit/poll
// 的续段凭票据判弃。
//
// 桩路数照 _home_ux_fix5_local.spec.js:python http.server 静态服 static/dist/home.html +
// page.route 拦 /api/**,recon submit/jobs 两端点给可控假响应把「对账进行中」钉住
// (不跑真对账·零扣费·无凭据依赖)。被验证的选择器/流程全部来自真实 bundle,桩只在网络边界。
/* global window */

const path = require('path');
const fs = require('fs');
const { test, expect } = require('@playwright/test');
const localServer = require('./_local_static_server');

const PORT = 8917;
const BASE = `http://127.0.0.1:${PORT}`;
const HOME = `${BASE}/static/dist/home.html`;
const OUT = path.join(__dirname, '_artifacts', 'recon-tab-switch');
fs.mkdirSync(OUT, { recursive: true });

let server;
test.beforeAll(async () => {
    server = await localServer.start(PORT, '/static/dist/home.html');
});
test.afterAll(() => localServer.stop(server));

const json = (body, status = 200) => ({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
});

const ME = {
    username: 'recon-e2e',
    role: 'owner',
    is_owner: true,
    can_view_history: true,
    tenant_id: 'recon-e2e-tenant',
};
const SUBJECTS = [{ id: 1, name: 'Recon E2E Co., Ltd.', tax_id: '0105567178203' }];

const FAKE_LEFT = { name: 'stmt.jpg', mimeType: 'image/jpeg', buffer: Buffer.from('e2e-stmt') };
const FAKE_RIGHT = {
    name: 'gl.xlsx',
    mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    buffer: Buffer.from('e2e-gl'),
};
const FAKE_VAT = { name: 'vat.csv', mimeType: 'text/csv', buffer: Buffer.from('a,b\n1,2') };

test('对账进行中切 income tab:确认后秒级可用·旧 job 不劫持视图', async ({ page }) => {
    // 银行对账 job 状态由测试拨杆控制:先钉 running,末段拨 failed 验「不劫持」
    let jobStatus = 'running';
    await page.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'e2e-recon-tab-token');
        localStorage.setItem('mrpilot_lang', 'zh');
    });
    await page.route('**/api/**', (route) => {
        const p = new URL(route.request().url()).pathname;
        if (p === '/api/recon/bank-v2/submit')
            return route.fulfill(json({ ok: true, job_id: 'e2e-tab-switch-job' }));
        if (p === '/api/recon/jobs/e2e-tab-switch-job')
            return route.fulfill(
                json(
                    jobStatus === 'running'
                        ? { ok: true, status: 'running', progress: { stage: 'parse' } }
                        : { ok: true, status: 'failed', error_code: 'stmt_no_rows' }
                )
            );
        if (p === '/api/me') return route.fulfill(json(ME));
        if (p === '/api/workspace/clients') return route.fulfill(json({ clients: SUBJECTS }));
        return route.fulfill(json({}));
    });

    await page.goto(HOME, { waitUntil: 'domcontentloaded' });
    // 套账硬门:真点一个主体过门(摘 class 量到的「可见」是假的)
    // SELECTOR-INDEX-OK: 桩只给了一个主体,first() 即它
    await page.locator('#workspace-gate-root [data-wsg-pick]').first().click();
    await expect(page.locator('#workspace-gate-root')).toHaveCount(0, { timeout: 15_000 });

    await page.evaluate(() => {
        window.location.hash = '#/reconcile';
    });
    await expect(page.locator('#page-reconcile')).toHaveClass(/active/, { timeout: 15_000 });
    await expect(page.locator('#rcx-card-left'), '对账页工作区已开(bank tab)').toBeVisible();

    // ── 银行对账进入 processing(假 job 钉住)──
    await page.locator('input[data-rcx-input="left"]').setInputFiles(FAKE_LEFT);
    await expect(page.locator('#rcx-card-left.rcx-loaded')).toBeVisible();
    await page.locator('input[data-rcx-input="right"]').setInputFiles(FAKE_RIGHT);
    await expect(page.locator('#rcx-card-right.rcx-loaded')).toBeVisible();
    await page.locator('#rcx-start-btn').click();
    await expect(page.locator('#rcx-processing'), '银行对账进行中').toHaveClass(/rcx-show/);

    // ── 切 income tab:有已上传文件 → 弹「切换将清空」确认(设计行为,不许静默吞) ──
    await page.locator('[data-rcx-tab="income"]').click();
    await expect(page.locator('#confirm-modal'), '切换确认弹窗').toBeVisible();
    await page.locator('#confirm-modal-ok').click();

    // 硬门①:确认后工作区秒级可见(旧代码这里 15s 等不到 → entry5 TIMEOUT)
    await expect(page.locator('#rcx-card-left'), '确认后 income 工作区立即可见').toBeVisible();
    await expect(page.locator('#rcx-tabs .rcx-seg.active')).toHaveAttribute(
        'data-rcx-tab',
        'income'
    );

    // 硬门②:income 双卡布满 → 开始按钮解锁(旧代码 RX.running 卡 true → 按钮死灰)
    await page.locator('input[data-rcx-input="left"]').setInputFiles(FAKE_RIGHT);
    await expect(page.locator('#rcx-card-left.rcx-loaded')).toBeVisible();
    await page.locator('input[data-rcx-input="right"]').setInputFiles(FAKE_VAT);
    await expect(page.locator('#rcx-card-right.rcx-loaded')).toBeVisible();
    await expect(page.locator('#rcx-start-btn'), '开始对账已解锁').toBeEnabled();
    await page.screenshot({ path: path.join(OUT, '01-income-ready-after-switch.png') });

    // 硬门③:旧 bank job 此后收尾(failed)也不许劫持 income tab 的视图。
    // 4s > 两个轮询周期(1.5s×2):旧代码在此窗口内必弹 fail 视图,修后轮询已随切换废弃。
    jobStatus = 'failed';
    await page.waitForTimeout(4000);
    await expect(page.locator('#rcx-fail'), '旧 job 失败不弹到 income tab').not.toHaveClass(
        /rcx-show/
    );
    await expect(page.locator('#rcx-workspace'), '工作区未被藏').not.toHaveClass(/rcx-hidden/);
    await expect(page.locator('#rcx-start-btn'), '开始按钮仍可用').toBeEnabled();
    await page.screenshot({ path: path.join(OUT, '02-no-stale-hijack.png') });
});
