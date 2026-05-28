// Pearnly E2E · 11 充值申请 → Earn 审核 → 台账闭环 · REFACTOR-D1
// ============================================================
// 跨账号闭环测试(铁律 #26 高敏 · 自主 loop 安全替身 B):
//   - 测试账号:普通 owner(invited_by IS NULL)· env PEARNLY_E2E_USER/PASS
//   - 超管账号:Earn · env PEARNLY_ADMIN_USER/PASS
//
// 流程:
//   1. 测试账号 API 登录 → tokenUser · GET /api/me/credits 记 balance_before
//   2. 测试账号 POST /api/credits/topup/request 提交充值申请 ฿1 → request_id · status=pending
//   3. Earn 账号 API 登录(POST /api/login)→ tokenAdmin
//   4. Earn POST /api/admin/credits/topup/approve/{id} actual_amount_thb=1 → {ok, new_balance}
//   5. 测试账号再 GET /api/me/credits → balance_after === balance_before + 1
//   6. 验 new_balance(admin 返)== balance_after(user 看到)
//
// 安全 / 不真付:
//   - Pearnly 无自动支付通道 · 充值=改内部台账数字(铁律 #26)。本 spec 只改测试账号台账。
//   - 每跑 +฿1 给测试账号(可忽略 · Earn 随时能重置)。
//
// 凭据走 env / 绝不入 git:
//   - PEARNLY_E2E_USER / PEARNLY_E2E_PASS — 测试账号(owner)
//   - PEARNLY_ADMIN_USER / PEARNLY_ADMIN_PASS — Earn 超管账号
//
// owner_only:若测试账号是 employee(invited_by != NULL),credits_topup_request 返 403 →
//   spec skip + annotate。
// ============================================================

const { test, expect } = require('@playwright/test');
const { request: pwRequest } = require('@playwright/test');
const { hasCreds, doUiLogin } = require('./_helpers/auth');

const BASE_URL = process.env.PEARNLY_E2E_BASE_URL || 'https://pearnly.com';

function hasAdminCreds() {
    return !!(process.env.PEARNLY_ADMIN_USER && process.env.PEARNLY_ADMIN_PASS);
}

async function apiLogin(apiCtx, username, password) {
    const r = await apiCtx.post('/api/login', {
        data: { username, password },
    });
    const j = await r.json().catch(() => ({}));
    return { status: r.status(), body: j };
}

test.describe('充值申请 → Earn 审核 → 台账闭环(铁律 #26 高敏)', () => {
    test.skip(!hasCreds(), '需测试账号(PEARNLY_E2E_USER/PASS)· CI 无凭据时跳过');
    test.skip(!hasAdminCreds(), '需 Earn 超管(PEARNLY_ADMIN_USER/PASS)· 无则跳过');

    test('user request topup ฿1 + Earn approve + balance 真增 ฿1', async ({
        browser,
    }, testInfo) => {
        test.setTimeout(60_000);

        // ────── 1) 测试账号登录(走 UI 拿 token · 顺带验证 storage state)
        const ctx = await browser.newContext();
        const page = await ctx.newPage();
        await doUiLogin(page);
        const tokenUser = await page.evaluate(() => localStorage.getItem('mrpilot_token'));
        expect((tokenUser || '').length, '测试账号登录后应有 token').toBeGreaterThan(0);

        const apiUser = await pwRequest.newContext({
            baseURL: BASE_URL,
            extraHTTPHeaders: { Authorization: 'Bearer ' + tokenUser },
            timeout: 30_000,
        });

        try {
            // ────── 2) 基线
            const beforeR = await apiUser.get('/api/me/credits');
            const before = await beforeR.json().catch(() => ({}));
            expect(beforeR.status(), '/api/me/credits 基线 200').toBe(200);

            if (!before.has_tenant) {
                testInfo.annotations.push({
                    type: 'skip',
                    description: '测试账号无 tenant · Earn 给账号建个测试公司即可',
                });
                test.skip(true, 'no tenant');
                return;
            }
            if (before.is_owner !== true) {
                testInfo.annotations.push({
                    type: 'skip',
                    description: '测试账号非 owner(被邀员工)· 充值申请 owner_only · 换主账号',
                });
                test.skip(true, 'not owner');
                return;
            }
            const balanceBefore = Number(before.balance_thb || 0);

            // ────── 3) 创建充值申请 ฿1
            const AMOUNT = 1;
            const reqR = await apiUser.post('/api/credits/topup/request', {
                data: {
                    amount_thb: AMOUNT,
                    payer_name: 'e2e-spec11',
                    note: 'e2e auto-test · ' + new Date().toISOString(),
                },
            });
            const reqJ = await reqR.json().catch(() => ({}));
            expect(
                reqR.status(),
                `topup/request 应 200 (got ${reqR.status()} body=${JSON.stringify(reqJ).slice(0, 200)})`
            ).toBe(200);
            expect(reqJ.status, '申请初始 status=pending').toBe('pending');
            const requestId = reqJ.request_id;
            expect(typeof requestId, 'request_id 应是 number').toBe('number');

            // ────── 4) Earn 超管登录
            const adminApi = await pwRequest.newContext({ baseURL: BASE_URL, timeout: 30_000 });
            const adminLogin = await apiLogin(
                adminApi,
                process.env.PEARNLY_ADMIN_USER,
                process.env.PEARNLY_ADMIN_PASS
            );
            expect(
                adminLogin.status,
                `Earn /api/login 应 200 (got ${adminLogin.status} body=${JSON.stringify(adminLogin.body).slice(0, 200)})`
            ).toBe(200);
            const tokenAdmin = adminLogin.body.access_token;
            expect((tokenAdmin || '').length, 'Earn token 应在响应中').toBeGreaterThan(0);
            await adminApi.dispose();

            const adminApiAuth = await pwRequest.newContext({
                baseURL: BASE_URL,
                extraHTTPHeaders: { Authorization: 'Bearer ' + tokenAdmin },
                timeout: 30_000,
            });

            try {
                // ────── 5) Earn approve
                const apR = await adminApiAuth.post(
                    `/api/admin/credits/topup/approve/${requestId}`,
                    {
                        data: {
                            actual_amount_thb: AMOUNT,
                            note: 'e2e auto-approved by spec 11',
                        },
                    }
                );
                const apJ = await apR.json().catch(() => ({}));
                expect(
                    apR.status(),
                    `admin approve 应 200 (got ${apR.status()} body=${JSON.stringify(apJ).slice(0, 200)})`
                ).toBe(200);
                expect(apJ.ok, 'approve 响应 ok:true').toBe(true);
                expect(
                    Number(apJ.new_balance),
                    `admin 返 new_balance ≈ before+${AMOUNT}`
                ).toBeCloseTo(balanceBefore + AMOUNT, 1);

                // ────── 6) 测试账号视角:balance_thb 应真增 ฿AMOUNT
                const afterR = await apiUser.get('/api/me/credits');
                const after = await afterR.json().catch(() => ({}));
                expect(afterR.status(), '/api/me/credits 终态 200').toBe(200);
                expect(
                    Number(after.balance_thb),
                    `user 视角 balance 应 = before+${AMOUNT} (before=${balanceBefore} after=${after.balance_thb})`
                ).toBeCloseTo(balanceBefore + AMOUNT, 1);

                testInfo.annotations.push({
                    type: 'note',
                    description: `闭环验毕:申请#${requestId} ฿${AMOUNT} · balance ${balanceBefore} → ${after.balance_thb}`,
                });
            } finally {
                await adminApiAuth.dispose();
            }
        } finally {
            await apiUser.dispose();
            await ctx.close();
        }
    });
});
