// Pearnly E2E · 11 计费安全/防渗透(prod)· 2026-06-28
// ============================================================
// 钱路径渗透验证:订阅/扣费的金额与租户全由服务端决定,客户端不可伪造。
// ① 未登录 GET /api/me/subscription → 401(无凭据看不到/动不了)
// ② 未登录 POST /api/subscription/subscribe → 401(无凭据不能订阅扣钱)
// ③ 伪造套餐码(plan_code='Z')→ 400 unknown_plan(不可凭空造套餐)
// ④ 伪造廉价金额(plan_code='L' 但塞 fee/monthly_fee/amount_thb=1)→ 服务端无视客户端金额,
//    仍按目录真价 ฿500 判:余额<500 时返 402,绝不以 ฿1 成交。
// ============================================================

// page.evaluate 回调在浏览器上下文执行(fetch/localStorage 为浏览器内建全局)
const { test, expect } = require('@playwright/test');
const { hasCreds, doUiLogin } = require('./_helpers/auth');

async function callApi(page, { method, path, token, body }) {
    return page.evaluate(
        async ({ method, path, token, body }) => {
            const headers = { 'Content-Type': 'application/json' };
            if (token) headers.Authorization = 'Bearer ' + token;
            const r = await fetch(path, {
                method,
                headers,
                cache: 'no-store',
                body: body ? JSON.stringify(body) : undefined,
            });
            let json = null;
            try {
                json = await r.json();
            } catch {
                /* 非 JSON 响应 · json 保持 null */
            }
            return { status: r.status, body: json };
        },
        { method, path, token, body }
    );
}

test.describe('计费安全 / 防渗透(prod)', () => {
    test.skip(!hasCreds(), '需测试账号 · CI 无凭据时跳过');

    test('未登录不能读取/发起订阅(401)', async ({ page }) => {
        // 任一页面拿到浏览器上下文即可发 fetch · 不带 Authorization
        await page.goto('/');
        const get = await callApi(page, { method: 'GET', path: '/api/me/subscription' });
        expect(get.status, '未登录读订阅应 401').toBe(401);
        const post = await callApi(page, {
            method: 'POST',
            path: '/api/subscription/subscribe',
            body: { plan_code: 'L' },
        });
        expect(post.status, '未登录订阅应 401').toBe(401);
    });

    test('伪造套餐码 → 400(不可凭空造套餐)', async ({ page }) => {
        await doUiLogin(page);
        const token = await page.evaluate(() => localStorage.getItem('mrpilot_token'));
        const res = await callApi(page, {
            method: 'POST',
            path: '/api/subscription/subscribe',
            token,
            body: { plan_code: 'Z' },
        });
        expect(res.status, '未知套餐码应 400').toBe(400);
    });

    test('伪造廉价金额无效 · 服务端按目录真价判(余额不足仍 402)', async ({ page }) => {
        await doUiLogin(page);
        const token = await page.evaluate(() => localStorage.getItem('mrpilot_token'));
        const sub = await callApi(page, { method: 'GET', path: '/api/me/subscription', token });
        expect(sub.status).toBe(200);
        const balance = sub.body.balance_thb;
        test.skip(balance >= 500, `余额 ฿${balance} ≥ 500 · 跳过以免真订阅扣费`);

        // 客户端塞各种"便宜价"字段 · 服务端必须无视,按目录 ฿500 判 → 余额不足 402
        const res = await callApi(page, {
            method: 'POST',
            path: '/api/subscription/subscribe',
            token,
            body: {
                plan_code: 'L',
                fee: 1,
                monthly_fee: 1,
                amount_thb: 1,
                price: 1,
                balance_thb: 9999,
            },
        });
        expect(res.status, '伪造金额不应以 ฿1 成交 · 应按真价 402').toBe(402);
        expect(res.body.detail.error, 'insufficient_balance').toBe('insufficient_balance');
        expect(res.body.detail.needed_thb, '所需金额按目录真价 ฿500').toBe(500);
    });
});
