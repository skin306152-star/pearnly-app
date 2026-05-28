// Pearnly E2E · 13 改密码 / 老 token 失效 · REFACTOR-D1
// ============================================================
// 铁律 v118.28.9(auth.py:139):JWT `iat` < users.password_changed_at → 401。
// 用户改密后,**所有签发于改密前**的老 token 立即失效;新密码登录拿到的新 token 才有效。
//
// 本 spec 真实跑流程(用真账号 + 真 API · 跑完恢复原密码):
//   1. 设备 A 登录 → tokenA · /api/me 200
//   2. POST /api/me/change_password(old=env, new=temp)→ 200 · password_changed_at=NOW()
//   3. tokenA 调 /api/me → 401(铁律 v118.28.9)
//   4. 新密码 UI 登录(临时覆盖 process.env.PEARNLY_E2E_PASS=temp 让 doUiLogin 用新密)
//      → tokenB / /api/me 200
//   5. 立刻 POST /api/me/change_password(old=temp, new=env)恢复(tokenB)→ 200
//   6. 验原密码仍能登录(保 env 凭据不坏)
//
// 兜底:任何中间步骤抛错,finally 用 temp 登录 + 改回 orig,把账号扯回原密码。
// 极端情况(连兜底都挂)→ 测试 fail + 控制台输出 temp_pass,人工用 Earn 重置即可。
//
// 临时密码:8+ chars · 含字母+数字(后端硬规则 auth_signup.py:2283-2286)。
//
// 边界:这条 spec 会真实改密 3 次(orig→temp→orig + 二次验证登录)· 命中 SMTP/速率闸时
// 容许失败(env-gated skip 已挡 CI · 本地由 Zihao 用 Earn 重置 / 等冷却重跑)。
// ============================================================

const { test, expect } = require('@playwright/test');
const { hasCreds, doUiLogin } = require('./_helpers/auth');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');

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

async function changePassword(page, token, oldPass, newPass) {
    return page.evaluate(
        async ({ t, o, n }) => {
            const r = await fetch('/api/me/change_password', {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + t,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ old_password: o, new_password: n }),
            });
            let body = '';
            try {
                body = await r.text();
            } catch {
                /* ignore */
            }
            return { status: r.status, snippet: (body || '').slice(0, 200) };
        },
        { t: token, o: oldPass, n: newPass }
    );
}

// 在覆盖 env 的临时窗口里跑 fn,跑完无论成功失败都恢复
async function withTempPass(tempPass, fn) {
    const saved = process.env.PEARNLY_E2E_PASS;
    process.env.PEARNLY_E2E_PASS = tempPass;
    try {
        return await fn();
    } finally {
        process.env.PEARNLY_E2E_PASS = saved;
    }
}

test.describe('改密 / 老 token 失效(铁律 v118.28.9)', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');

    test('改密后 tokenA 401 + 新密码登录通 + 末尾回滚保 env 凭据有效', async ({ browser }) => {
        const orig = process.env.PEARNLY_E2E_PASS;
        // 满足后端硬规则:≥ 8 chars · 含字母+数字 (auth_signup.py:2283-2286)
        const temp = 'Pe' + Date.now() + 'a1';
        let passwordChanged = false;

        // ────── 1) 设备 A 登录 → tokenA · /api/me 200(基线)
        const ctxA = await browser.newContext();
        const pageA = await ctxA.newPage();
        await doUiLogin(pageA);
        const tokenA = await pageA.evaluate(() => localStorage.getItem('mrpilot_token'));
        expect((tokenA || '').length, 'tokenA 应在 localStorage').toBeGreaterThan(0);
        const me1 = await callMe(pageA, tokenA);
        expect(me1.status, `tokenA 初始应 200 (got ${me1.status} · ${me1.snippet})`).toBe(200);

        try {
            // ────── 2) 改密 orig → temp(应 200)
            const ch1 = await changePassword(pageA, tokenA, orig, temp);
            expect(
                ch1.status,
                `改密 orig→temp 应 200 (got ${ch1.status} body=${ch1.snippet})`
            ).toBe(200);
            passwordChanged = true;

            // ────── 3) tokenA 现应 401(铁律 v118.28.9 · token.iat < password_changed_at)
            const me2 = await callMe(pageA, tokenA);
            expect(me2.status, `改密后 tokenA 应 401 (got ${me2.status} body=${me2.snippet})`).toBe(
                401
            );

            // ────── 4) 新密码 UI 登录通 → tokenB · /api/me 200
            const ctxB = await browser.newContext();
            const pageB = await ctxB.newPage();
            const guardB = attachConsoleGuard(pageB);
            await withTempPass(temp, async () => {
                await doUiLogin(pageB);
            });
            const tokenB = await pageB.evaluate(() => localStorage.getItem('mrpilot_token'));
            expect((tokenB || '').length, 'tokenB 应在 localStorage').toBeGreaterThan(0);
            const meB = await callMe(pageB, tokenB);
            expect(meB.status, `tokenB 应 200 (got ${meB.status} · ${meB.snippet})`).toBe(200);

            // ────── 5) 立刻回滚:temp → orig(用 tokenB)→ 200
            const ch2 = await changePassword(pageB, tokenB, temp, orig);
            expect(
                ch2.status,
                `回滚 temp→orig 应 200 (got ${ch2.status} body=${ch2.snippet})`
            ).toBe(200);
            passwordChanged = false; // 账号已回到 orig · finally 不再兜底

            // ────── 6) 验原密码仍能登录(确保 env 凭据没被自己破掉)
            const ctxC = await browser.newContext();
            const pageC = await ctxC.newPage();
            await doUiLogin(pageC); // 用 env 原密码
            const tokenC = await pageC.evaluate(() => localStorage.getItem('mrpilot_token'));
            expect((tokenC || '').length, '原密码仍能登录').toBeGreaterThan(0);

            assertNoConsoleErrors(expect, guardB);

            await ctxB.close();
            await ctxC.close();
        } finally {
            if (passwordChanged) {
                // 兜底:中途挂掉 · 账号当前是 temp · 把它扯回 orig 才能保 env 凭据
                // eslint-disable-next-line no-console -- 测试失败兜底诊断
                console.warn(`[spec-13 finally] 改密未完成回滚 · 尝试用 temp(${temp})扯回 orig`);
                try {
                    const ctxR = await browser.newContext();
                    const pageR = await ctxR.newPage();
                    await withTempPass(temp, async () => {
                        await doUiLogin(pageR);
                    });
                    const tokR = await pageR.evaluate(() => localStorage.getItem('mrpilot_token'));
                    if (tokR) {
                        await changePassword(pageR, tokR, temp, orig);
                    }
                    await ctxR.close();
                } catch (e) {
                    // eslint-disable-next-line no-console -- 终极兜底
                    console.error(
                        `[spec-13 finally] 兜底失败 · 账号可能仍是 temp_pass · ` +
                            `temp=${temp} · 用 Earn 后台重置该测试账号密码 · 错误:${e.message}`
                    );
                }
            }
            await ctxA.close();
        }
    });
});
