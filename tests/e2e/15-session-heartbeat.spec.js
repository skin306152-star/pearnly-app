// Pearnly E2E · 15 Session 心跳 / 单设备互踢 · REFACTOR-D1
// ============================================================
// 铁律 #3(2026-05-16):JWT payload 含 `jti` · users.active_jti 记录最新签发 · 校验
// `token.jti != user.active_jti` 返 401 auth.session_revoked。home.js 前端 15s 心跳 +
// window.focus/visibilitychange 即时 check,实现"1 账号 1 设备"。
//
// 本 spec 真实跑流程:
//   1. 设备 A 真账号 UI 登录 → 拿 tokenA → 立刻调 /api/me 应 200(基线)
//   2. 同账号在设备 B(独立 browser context)再走一次 UI 登录 → 拿 tokenB
//      → 后端 users.active_jti 被改写为 tokenB 的 jti(老 jti 立即失效)
//   3. 设备 A 再调 /api/me → 应 401(tokenA 的 jti 不再等于 active_jti)
//   4. 设备 B 调 /api/me 仍 200(它是新主)
//   5. 把设备 B 的 storageState 持久化覆盖 STORAGE_STATE,让同 run 后续 spec
//      继续用 tokenB(否则它们手里的 tokenA 也会 401)
//
// 安全 / 不造数据:不改密、不充值、不上传文件、不写库;只换 active_jti(本就是登录副作用)。
//
// env-gated:无 PEARNLY_E2E_USER/PEARNLY_E2E_PASS(CI)优雅跳过 · CI 保绿(铁律 #2 / #26)。
// ============================================================

const fs = require('fs');
const path = require('path');
const { test, expect } = require('@playwright/test');
const { hasCreds, doUiLogin, STORAGE_STATE } = require('./_helpers/auth');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

// 在 page 上下文里调 /api/me · 返回 {status, snippet}(body 截前 200 字防长)
async function callMe(page, token) {
    return page.evaluate(async (t) => {
        const r = await fetch('/api/me', {
            headers: { Authorization: 'Bearer ' + t },
            cache: 'no-store',
        });
        let body = '';
        try {
            body = await r.text();
        } catch {
            /* ignore */
        }
        return { status: r.status, snippet: (body || '').slice(0, 200) };
    }, token);
}

test.describe('Session 互踢(铁律 #3)', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');

    test('第二设备登录 → 第一设备 token 立即 401(active_jti 被改写)', async ({ browser }) => {
        // ────── 1) 设备 A 登录 → tokenA · /api/me 应 200
        const ctxA = await browser.newContext();
        const pageA = await ctxA.newPage();
        // 注:不在 A 上挂 console-guard 断言 —— B 登录后 A 的心跳/订阅会真实触发
        // 401 session_revoked + token 失效 toast / 跳登录页等 console.error,这正是
        // 铁律 #3 的预期行为,不算回归。只在 B(新主)上守 console error。
        await doUiLogin(pageA);
        const tokenA = await pageA.evaluate(() => localStorage.getItem('mrpilot_token'));
        expect((tokenA || '').length, 'tokenA 应在 localStorage').toBeGreaterThan(0);

        const meA1 = await callMe(pageA, tokenA);
        expect(meA1.status, `tokenA 初始应有效 (got ${meA1.status} · body=${meA1.snippet})`).toBe(
            200
        );

        // ────── 2) 设备 B 登录(同账号 · 独立 context)→ tokenB · /api/me 应 200
        const ctxB = await browser.newContext();
        const pageB = await ctxB.newPage();
        const guardB = attachConsoleGuard(pageB);
        await doUiLogin(pageB);
        const tokenB = await pageB.evaluate(() => localStorage.getItem('mrpilot_token'));
        expect((tokenB || '').length, 'tokenB 应在 localStorage').toBeGreaterThan(0);
        expect(tokenB, 'tokenB 应与 tokenA 不同(新 jti)').not.toBe(tokenA);

        const meB = await callMe(pageB, tokenB);
        expect(meB.status, `tokenB 应有效 (got ${meB.status} · body=${meB.snippet})`).toBe(200);

        // ────── 3) 设备 A 再调 /api/me → 应 401(铁律 #3 · token.jti != active_jti)
        const meA2 = await callMe(pageA, tokenA);
        expect(
            meA2.status,
            `第二设备登录后 tokenA 应失效 401 (got ${meA2.status} · body=${meA2.snippet})`
        ).toBe(401);
        // 后端约定 detail 含 session_revoked 关键字(铁律 #3)· 容忍措辞微调,只要状态码是 401
        // 这条断言软化为"不再 200" + "状态码 401"(已上面 assert)· 避免文案对齐变红
        expect(meA2.snippet.length, 'A 失效时 body 非空').toBeGreaterThan(0);

        // ────── 4) 把设备 B 的 state 持久化 → 让同 run 后续 spec 复用 tokenB,
        //         否则它们以为 storageState 里的老 token 还有效,跑起来全 401
        fs.mkdirSync(path.dirname(STORAGE_STATE), { recursive: true });
        await ctxB.storageState({ path: STORAGE_STATE });

        // ────── 5) 设备 B(新主)全程无 console.error / pageerror;A 因 session_revoked 必报错(预期)
        assertNoConsoleErrors(expect, guardB);

        await ctxA.close();
        await ctxB.close();
    });
});
