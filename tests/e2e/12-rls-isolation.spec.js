// Pearnly E2E · 12 RLS 行级隔离 + 垂直权限 · REFACTOR-D1
// ============================================================
// 涵盖 2 层数据隔离:
//
// ① 水平 RLS 穿透(行级 · 同表内 A↔B 公司隔离)
//   走 POST /api/admin/rls/run_tests · 后端对**已 enroll 的真 tenant_isolation policy**跑 5 条
//   (B8 P4 重写:不再临时建/删 policy · 只读 · clients 永久 enroll):
//     T1 · tenant_a 不能看 tenant_b 的 client(穿透核心)
//     T2 · tenant_b 能看自己的 client(基本可用)
//     T3 · 无 tenant 上下文 · RLS 拒绝(防代码忘记 SET)
//     T4 · bypass 模式能看所有(超管/migration 通道)
//     T5 · 伪造 tenant_id(假 UUID)必须返空(防 UUID 猜测攻击)
//
//   ✅ **B8 已落地(2026-06·RLS_ROLE=pearnly_app 切最小权限角色 NOBYPASSRLS)**:get_cursor_rls
//   SET LOCAL ROLE 后 policy 强制生效,5 条全过。此前(2026-05-28)T1/T3/T5 失败是 DB role
//   BYPASSRLS 特权所致,B8 角色机制已根治。
//
//   本 spec 断言(B8 落地后收紧):
//     A. 端点可达 + 形状对(preflight.ok + tests 数组 5 条)
//     B. 5 条 ok 全 true · passed===5 · failed===0(真隔离全过)
//
// ② 垂直权限(non-admin 调 admin endpoint 应 403):
//   - GET /api/admin/rls/status
//   - POST /api/admin/rls/run_tests
//   - GET /api/admin/credits/topup/requests
//
// 用 2 套 token(测试账号 + Earn 超管),不需要自助注册第二个 owner 账号
// (服务器端 run_rls_isolation_tests 已用真 DB 里现存的两个 tenant 跑 A↔B 隔离)。
//
// 凭据:
//   PEARNLY_E2E_USER / PEARNLY_E2E_PASS — 测试账号(非超管)
//   PEARNLY_ADMIN_USER / PEARNLY_ADMIN_PASS — Earn 超管
//
// 不留副作用:clients 永久 enroll(B8)· harness 只读跑测试,不改任何表 RLS 状态。
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

test.describe('RLS 行级隔离 + 垂直权限(铁律 #26 + RLS infra)', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');
    test.skip(!hasAdminCreds(), '需 Earn 超管·无凭据时跳过');

    test('non-admin 403 + Earn 跑 RLS 5 测试(B8 落地 · passed===5 全过)', async ({
        browser,
    }, testInfo) => {
        test.setTimeout(90_000);

        // ────── 0) 测试账号登录(走 UI · 拿 token)
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

        const adminApiBare = await pwRequest.newContext({ baseURL: BASE_URL, timeout: 30_000 });
        const adminLogin = await apiLogin(
            adminApiBare,
            process.env.PEARNLY_ADMIN_USER,
            process.env.PEARNLY_ADMIN_PASS
        );
        expect(
            adminLogin.status,
            `Earn /api/login 应 200 (got ${adminLogin.status} body=${JSON.stringify(adminLogin.body).slice(0, 200)})`
        ).toBe(200);
        const tokenAdmin = adminLogin.body.access_token;
        expect((tokenAdmin || '').length, 'Earn token 应在响应中').toBeGreaterThan(0);
        await adminApiBare.dispose();

        const apiAdmin = await pwRequest.newContext({
            baseURL: BASE_URL,
            extraHTTPHeaders: { Authorization: 'Bearer ' + tokenAdmin },
            timeout: 30_000,
        });

        try {
            // ────── 1) 垂直权限 · non-admin 调 3 个 admin endpoint 应 403
            const v1 = await apiUser.get('/api/admin/rls/status');
            expect(v1.status(), 'non-admin GET /api/admin/rls/status 应 403').toBe(403);

            const v2 = await apiUser.post('/api/admin/rls/run_tests');
            expect(v2.status(), 'non-admin POST /api/admin/rls/run_tests 应 403').toBe(403);

            const v3 = await apiUser.get('/api/admin/credits/topup/requests');
            expect(v3.status(), 'non-admin GET /api/admin/credits/topup/requests 应 403').toBe(403);

            // ────── 2) Earn 调同 3 个 endpoint 应 200(对照)
            const a1 = await apiAdmin.get('/api/admin/rls/status');
            expect(a1.status(), 'Earn GET /api/admin/rls/status 应 200').toBe(200);

            const a3 = await apiAdmin.get('/api/admin/credits/topup/requests');
            expect(a3.status(), 'Earn GET /api/admin/credits/topup/requests 应 200').toBe(200);

            // ────── 3) 水平 RLS 穿透 · Earn POST /api/admin/rls/run_tests
            const rlsR = await apiAdmin.post('/api/admin/rls/run_tests', {
                timeout: 60_000,
            });
            const rls = await rlsR.json().catch(() => ({}));
            expect(
                rlsR.status(),
                `Earn 跑 RLS tests 应 200 (got ${rlsR.status()} body=${JSON.stringify(rls).slice(0, 300)})`
            ).toBe(200);

            testInfo.annotations.push({
                type: 'info',
                description: `RLS preflight: ${JSON.stringify(rls.preflight || {}).slice(0, 200)}`,
            });
            testInfo.annotations.push({
                type: 'info',
                description: `RLS tests: passed=${rls.passed} failed=${rls.failed} count=${(rls.tests || []).length}`,
            });

            // A. 端点可达 + 形状(preflight ok / 5 条 tests)
            expect(rls.preflight && rls.preflight.ok, `RLS preflight 必 OK`).toBeTruthy();
            expect(Array.isArray(rls.tests), 'tests 应为数组').toBe(true);
            expect(rls.tests.length, 'tests 应有 5 条').toBe(5);

            // B. B8 落地 · 5 条全过(真隔离)。任一失败把全部失败项打出来便于定位
            const failedTests = rls.tests.filter((t) => !t.ok);
            const failNames = failedTests.map((t) => `${t.name} (actual=${t.actual})`).join(' | ');
            expect(
                rls.passed,
                `RLS 5 条应全过 (passed=${rls.passed} failed=${rls.failed}) 失败项: ${failNames || '无'}`
            ).toBe(5);
            expect(rls.failed, `RLS failed 应为 0`).toBe(0);
            for (const t of rls.tests) {
                expect(t.ok, `${t.name} 应通过 (actual=${t.actual})`).toBe(true);
            }
        } finally {
            await apiUser.dispose();
            await apiAdmin.dispose();
            await ctx.close();
        }
    });
});
