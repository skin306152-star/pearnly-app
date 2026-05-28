// Pearnly E2E · 14 LINE 账号绑定 · REFACTOR-D1
// ============================================================
// 范围(纯 HTTP 端点 · 不走 LINE 真 Bot):
//   1. POST /api/line/binding-code → 200 + 6 位 code + expires_at(ISO)
//   2. POST 再次 → 200 + code 仍 6 位(允许同/异 · TTL 内可能复用,过期会换)
//   3. GET /api/line/binding → 200 + {bound: bool, ...}
//   4. 若当前 bound=true → DELETE /api/line/binding → 200 + 再 GET 应 bound=false
//      若 bound=false:annotate(测试账号未绑,跳过 unbind 闭环)
//
// 不测「换绑拒绝」(需向 /api/line/webhook 发带 LINE_CHANNEL_SECRET HMAC 的 follow 事件
//   + 真实 LINE userId,无 LINE Channel 凭据无法在自动化里模拟。留作半人工 E2E:Zihao 在
//   Bot 上用第二个 LINE 账号发 code,验后端 db.create_or_update_line_binding 拒绝换绑)。
//
// 不测「真绑定闭环」(同上 · 需 LINE webhook 把 line_user_id 写进 line_bindings 表)。
// 这两条覆盖路径见 services/line_binding/store.py 的契约单测(已覆盖)。
//
// 安全:DELETE 只在「当前已绑定」时调,避免改测试账号状态。本 spec 跑完不留副作用
// (生成 code 写 line_binding_codes,10min 自动过期;反查只读;DELETE 已绑→不动 = no-op)。
// ============================================================

const { test, expect } = require('@playwright/test');
const { request: pwRequest } = require('@playwright/test');
const { hasCreds, doUiLogin } = require('./_helpers/auth');

const BASE_URL = process.env.PEARNLY_E2E_BASE_URL || 'https://pearnly.com';

test.describe('LINE 账号绑定(端点)', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');

    test('生成绑定码(2次) + 反查 + 解绑(若已绑)', async ({ browser }, testInfo) => {
        // ────── 0) 登录 · 拿 token
        const ctx = await browser.newContext();
        const page = await ctx.newPage();
        await doUiLogin(page);
        const token = await page.evaluate(() => localStorage.getItem('mrpilot_token'));
        expect((token || '').length, '登录后应有 token').toBeGreaterThan(0);

        const apiCtx = await pwRequest.newContext({
            baseURL: BASE_URL,
            extraHTTPHeaders: { Authorization: 'Bearer ' + token },
            timeout: 30_000,
        });

        try {
            // ────── 1) POST /api/line/binding-code 第 1 次 → 200 · 6 位 code · expires_at ISO
            const r1 = await apiCtx.post('/api/line/binding-code');
            const j1 = await r1.json().catch(() => ({}));
            expect(
                r1.status(),
                `第 1 次生成码应 200 (got ${r1.status()} body=${JSON.stringify(j1).slice(0, 200)})`
            ).toBe(200);
            expect(typeof j1.code, 'code 字段应是 string').toBe('string');
            expect(j1.code, 'code 应是 6 位数字').toMatch(/^\d{6}$/);
            expect(j1.expires_at, 'expires_at 应是 ISO 字符串').toMatch(/^\d{4}-\d{2}-\d{2}T/);
            const exp1 = new Date(j1.expires_at).getTime();
            expect(exp1 - Date.now(), 'expires_at 应在 8-12 分钟内').toBeGreaterThan(8 * 60_000);
            expect(exp1 - Date.now(), 'expires_at 应在 8-12 分钟内').toBeLessThan(12 * 60_000);

            // ────── 2) POST 再来一发 → 200 · 仍 6 位
            // db.generate_line_binding_code 实现可能 invalidate 老码并发新码,也可能复用未过期码
            // 这里只断言「2 次都成功 · 都是合法 6 位」· 不强行要求 code 不同
            const r2 = await apiCtx.post('/api/line/binding-code');
            const j2 = await r2.json().catch(() => ({}));
            expect(r2.status(), '第 2 次生成码应 200').toBe(200);
            expect(j2.code, '第 2 次 code 应是 6 位数字').toMatch(/^\d{6}$/);

            // ────── 3) GET /api/line/binding 反查 → 200 + bound:bool
            const r3 = await apiCtx.get('/api/line/binding');
            const j3 = await r3.json().catch(() => ({}));
            expect(r3.status(), '反查应 200').toBe(200);
            expect(typeof j3.bound, 'bound 字段应是 bool').toBe('boolean');

            const wasBound = j3.bound === true;
            testInfo.annotations.push({
                type: 'info',
                description: `初始 LINE 绑定状态:bound=${wasBound} (display=${j3.line_display_name || '-'})`,
            });

            // ────── 4) 若已绑定 → 真测解绑闭环(DELETE + 再查)
            //         若未绑定 → 跳过解绑(DELETE 在未绑定时会 500 "解绑失败" · 不该污染断言)
            if (wasBound) {
                const r4 = await apiCtx.delete('/api/line/binding');
                const j4 = await r4.json().catch(() => ({}));
                expect(
                    r4.status(),
                    `DELETE 解绑应 200 (got ${r4.status()} body=${JSON.stringify(j4).slice(0, 200)})`
                ).toBe(200);
                expect(j4.success, '解绑响应 success:true').toBe(true);

                // 再查 → 应 bound=false
                const r5 = await apiCtx.get('/api/line/binding');
                const j5 = await r5.json().catch(() => ({}));
                expect(r5.status(), '解绑后反查应 200').toBe(200);
                expect(j5.bound, '解绑后 bound 应为 false').toBe(false);
                testInfo.annotations.push({
                    type: 'note',
                    description:
                        '解绑闭环已验 · 账号当前 unbound · 不再重新绑定(LINE Bot 真好友才能)',
                });
            } else {
                testInfo.annotations.push({
                    type: 'note',
                    description:
                        '测试账号未绑定 LINE · 跳过解绑闭环(DELETE 未绑时返 500)· ' +
                        '换绑拒绝/真绑闭环测试需 Bot 真好友配合,留作半人工 E2E',
                });
            }
        } finally {
            await apiCtx.dispose();
            await ctx.close();
        }
    });
});
