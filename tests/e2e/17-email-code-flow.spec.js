// Pearnly E2E · 17 邮箱验证码 / 找回密码验证码 · 端点 smoke · REFACTOR-D1
// ============================================================
// 范围(端点 smoke · 不读邮件):
//   1. POST /api/auth/forgot_password 用已注册邮箱(测试账号)→ 200 {ok:true}
//   2. POST /api/auth/forgot_password 用不存在邮箱 → 200 {ok:true}(防 enumerate)
//   3. POST /api/auth/send_email_code 用已注册邮箱(测试账号)→ 409 email_already_registered
//      (证明端点真在查 DB,不是黑盒 noop)
//   4. POST /api/auth/send_email_code 邮件格式非法 → 400 email_invalid(校验生效)
//
// 这条 spec 不读邮箱(SMTP/IMAP 凭据没在 env)→ 拿不到真实 code,无法 verify 完整闭环。
// 真完整闭环(收件箱 → 提取 code → 调 verify_email_code)需要给 spec 灌 IMAP 凭据
// (PEARNLY_IMAP_HOST/USER/PASS)。目前仅 smoke,确保整条邮件验证码线没失能 / 限流配
// 置存在(已注册返 409 · 无效邮件返 400)。完整 IMAP 闭环留作后续(配 env 即可)。
//
// 不污染:
//   - forgot_password 对测试账号会真往邮箱发链接 → 我们直接抛弃(token 15min 自动失效)。
//   - send_email_code 用「已注册测试账号邮箱」一律 409 → DB 不写 email_codes 行(check 之前提前抛)。
//   - 无效邮件 400 → 同上 0 副作用。
//   - 不存在邮箱 → 早返 ok · DB 0 副作用。
//
// 安全:无登录态需求,直接 fetch 公共 API。
// env-gated:依赖 PEARNLY_E2E_USER(已注册邮箱判定)· 无凭据(CI)跳过保绿。
// ============================================================

const { test, expect } = require('@playwright/test');
const { hasCreds } = require('./_helpers/auth');

async function post(page, path, body) {
    return page.evaluate(
        async ({ p, b }) => {
            const r = await fetch(p, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(b),
                cache: 'no-store',
            });
            let bodyText = '';
            try {
                bodyText = await r.text();
            } catch {
                /* ignore */
            }
            return { status: r.status, snippet: (bodyText || '').slice(0, 300) };
        },
        { p: path, b: body }
    );
}

function uniqueFakeEmail() {
    // 随机 + 不存在的子域 · 永不冲到真账号
    const s = Math.random().toString(36).slice(2, 10);
    return `e2e-spec17-${Date.now()}-${s}@nowhere.pearnly.example`;
}

test.describe('邮箱验证码 / 找回密码 端点 smoke(铁律 v118.27.6 + forgot_password 防 enumerate)', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');

    test('4 条 smoke · forgot_password ok×2 / send_email_code 409+400', async ({ page }) => {
        // 让 fetch 有一个 origin 可用 · 着陆页就行(不点)
        await page.goto('/');

        const testEmail = process.env.PEARNLY_E2E_USER;
        const fakeEmail = uniqueFakeEmail();

        // ────── 1) forgot_password · 已注册邮箱 → 200 {ok:true}
        // 注:这会触发服务器尝试给测试账号发重置邮件 / LINE 推送 · 15min 后 token 自动失效
        // 不点链接 = 账号零影响
        const f1 = await post(page, '/api/auth/forgot_password', {
            email: testEmail,
            fingerprint: 'e2e-spec17',
        });
        expect(
            f1.status,
            `forgot_password 已注册邮箱应 200 (got ${f1.status} body=${f1.snippet})`
        ).toBe(200);
        expect(f1.snippet).toMatch(/"ok"\s*:\s*true/);

        // ────── 2) forgot_password · 不存在邮箱 → 200 {ok:true}(防 enumerate)
        const f2 = await post(page, '/api/auth/forgot_password', {
            email: fakeEmail,
            fingerprint: 'e2e-spec17',
        });
        expect(
            f2.status,
            `forgot_password 不存在邮箱也应 200 防 enumerate (got ${f2.status})`
        ).toBe(200);
        expect(f2.snippet).toMatch(/"ok"\s*:\s*true/);

        // ────── 3) send_email_code · 已注册邮箱 → 409 email_already_registered
        // 证明端点真在查 DB · 不是黑盒
        const s1 = await post(page, '/api/auth/send_email_code', {
            email: testEmail,
            purpose: 'signup',
            lang: 'zh',
        });
        expect(
            s1.status,
            `send_email_code 已注册邮箱应 409 (got ${s1.status} body=${s1.snippet})`
        ).toBe(409);
        expect(s1.snippet).toMatch(/email_already_registered/i);

        // ────── 4) send_email_code · 邮件格式非法 → 400 email_invalid
        const s2 = await post(page, '/api/auth/send_email_code', {
            email: 'not-an-email',
            purpose: 'signup',
            lang: 'zh',
        });
        expect(
            s2.status,
            `send_email_code 非法邮件应 400 (got ${s2.status} body=${s2.snippet})`
        ).toBe(400);
        expect(s2.snippet).toMatch(/email_invalid/i);
    });
});
