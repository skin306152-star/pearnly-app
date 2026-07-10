// PS-1 · POS 退货店长授权覆盖窗 · 真浏览器本地 E2E
//
// 加载真实构建产物 static/dist/pos.js,route-stub 后端把退货接口在「授权闸开·收银员无权」
// 场景下返 pos.approval_required,断言前台真弹店长授权窗(isVisible + getComputedStyle),
// 再走店长 PIN 覆盖成功。验的是前端拦截 UI 与覆盖流,后端授权判定由 unittest 覆盖。
//
// 本地起 python http.server 供源根,不依赖生产/DB。截图存 tests/e2e/_artifacts/ps1/。
/* global window, getComputedStyle */

const { test, expect } = require('@playwright/test');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const ROOT = path.resolve(__dirname, '..', '..');
const PORT = 8973;
const BASE = `http://127.0.0.1:${PORT}`;
const ART = path.join(__dirname, '_artifacts', 'ps1');

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
    await waitUp(`${BASE}/static/pos/pos.html`);
});

test.afterAll(() => {
    if (server) server.kill();
});

const RECEIPT = {
    ok: true,
    data: {
        sale: { id: 's1', receipt_no: 'R1', sold_at: new Date().toISOString(), cashier: 'Nok' },
        lines: [
            {
                sale_line_id: 'L1',
                name: { en: 'Coke', th: 'โค้ก', zh: '可乐' },
                unit_price: '15.00',
                qty: '2',
            },
        ],
        payments: [{ method: 'cash', amount: '30.00' }],
    },
};

async function stub(page) {
    await page.route('**/api/pos/cashiers**', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                ok: true,
                // 不给 color:压授权窗头像的 var(--accent) 令牌回退路径(新代码禁写死旧蓝)
                data: { cashiers: [{ id: 'mgr1', display_name: 'Manager Nok' }] },
            }),
        })
    );
    await page.route('**/api/pos/sales/by-receipt**', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(RECEIPT),
        })
    );
    await page.route('**/api/pos/sales/*/refund', (route) => {
        const body = route.request().postData() || '';
        const hasApproval = body.includes('"approval"');
        if (!hasApproval) {
            // 授权闸开 + 收银员无权 → 后端拒并要求授权
            return route.fulfill({
                status: 403,
                contentType: 'application/json',
                body: JSON.stringify({ ok: false, error: { code: 'pos.approval_required' } }),
            });
        }
        // 店长授权覆盖后放行
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                ok: true,
                data: {
                    refund_sale: { id: 'r1', receipt_no: 'RFD1', grand_total: '-15.00' },
                    stock_returned: true,
                },
            }),
        });
    });
}

test('退货被拦 → 弹店长授权窗 → PIN 覆盖成功', async ({ page }) => {
    await stub(page);
    await page.goto(`${BASE}/static/pos/pos.html`);
    await page.waitForFunction(() => window.POS && window.POS.ops && window.POS.approve);

    // 直接进退货屏(登录流非本例所验;绑定 workspace 使 allowMock 关,走 stub 真信封)。
    await page.evaluate(() => {
        window.POS.state.workspaceClientId = 7;
        window.POS.state.token = 'test-token';
        window.POS.showView('refund');
        window.POS.ops.resetRefund();
    });

    await page.fill('#refund-receipt', 'R1');
    await page.click('#refund-find-btn');

    // 原单行渲染 → 勾选一行 → 点退货
    await page.waitForSelector('#refund-body .line[data-lid="L1"]');
    await page.click('#refund-body .line[data-lid="L1"] .nm');
    await page.click('#refund-do');

    // 断言:店长授权窗真的可见(不靠 class 自欺)
    const mask = page.locator('#mgr-mask');
    await expect(mask).toBeVisible();
    const vis = await mask.evaluate((el) => {
        const cs = getComputedStyle(el);
        return {
            display: cs.display,
            visibility: cs.visibility,
            opacity: cs.opacity,
            shown: el.classList.contains('show'),
        };
    });
    expect(vis.display).toBe('flex');
    expect(vis.visibility).toBe('visible');
    expect(vis.shown).toBe(true);
    await expect(page.locator('#mgr-cashiers .mgr-ca')).toHaveCount(1);
    // 无配色收银员的头像回退 = var(--accent) 解析成主色紫(#7C4DFF),不是写死旧蓝
    const avatarBg = await page
        .locator('#mgr-cashiers .mgr-ca .av')
        .evaluate((el) => getComputedStyle(el).backgroundColor);
    expect(avatarBg).toBe('rgb(124, 77, 255)');

    await page.screenshot({ path: path.join(ART, 'approval-modal-visible.png'), fullPage: true });

    // 店长输 PIN(点自研键盘,不用 fill 绕键) → 第 4 位自动提交 → 覆盖放行
    for (const d of ['1', '2', '3', '4']) {
        await page.click(`#mgr-pad .k[data-pin="${d}"]`);
    }

    // 覆盖成功:窗关 + 回主屏
    await expect(mask).toBeHidden({ timeout: 5000 });
    await expect(page.locator('#view-main')).toHaveClass(/is-active/);
    await page.screenshot({ path: path.join(ART, 'after-approval-success.png'), fullPage: true });
});

test('取消授权窗 → 不发生退货', async ({ page }) => {
    await stub(page);
    await page.goto(`${BASE}/static/pos/pos.html`);
    await page.waitForFunction(() => window.POS && window.POS.ops && window.POS.approve);
    await page.evaluate(() => {
        window.POS.state.workspaceClientId = 7;
        window.POS.state.token = 'test-token';
        window.POS.showView('refund');
        window.POS.ops.resetRefund();
    });
    await page.fill('#refund-receipt', 'R1');
    await page.click('#refund-find-btn');
    await page.waitForSelector('#refund-body .line[data-lid="L1"]');
    await page.click('#refund-body .line[data-lid="L1"] .nm');
    await page.click('#refund-do');
    await expect(page.locator('#mgr-mask')).toBeVisible();
    await page.click('#mgr-cancel');
    await expect(page.locator('#mgr-mask')).toBeHidden();
    // 仍停在退货屏(未成功、未回主屏)
    await expect(page.locator('#view-refund')).toHaveClass(/is-active/);
});
