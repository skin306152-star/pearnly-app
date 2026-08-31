// Pearnly E2E · Cowork LINE 自助绑定入口
// 真正的 LINE 授权回跳需要真人账号，留给候选生产版本的真机验收。
/* global window */

const { test, expect } = require('@playwright/test');
const { request: pwRequest } = require('@playwright/test');
const { hasCreds, doUiLogin } = require('./_helpers/auth');

const BASE_URL = process.env.PEARNLY_E2E_BASE_URL || 'https://pearnly.com';

test.describe('Cowork LINE 自助绑定', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');

    test('状态接口 + 一次性 OAuth 入口 + 旧机器人入口关闭', async ({ browser }) => {
        const ctx = await browser.newContext();
        const page = await ctx.newPage();
        await doUiLogin(page);
        const token = await page.evaluate(() => window.session.getToken());
        expect((token || '').length, '登录后应有 token').toBeGreaterThan(0);

        const apiCtx = await pwRequest.newContext({
            baseURL: BASE_URL,
            extraHTTPHeaders: { Authorization: 'Bearer ' + token },
            timeout: 30_000,
        });

        try {
            const status = await apiCtx.get('/api/cowork-line/identity');
            const statusBody = await status.json().catch(() => ({}));
            expect(status.status(), JSON.stringify(statusBody)).toBe(200);
            expect(typeof statusBody.connected).toBe('boolean');

            if (!statusBody.connected) {
                const start = await apiCtx.post('/api/cowork-line/connect/start');
                const startBody = await start.json().catch(() => ({}));
                expect(start.status(), JSON.stringify(startBody)).toBe(200);
                expect(startBody.url).toMatch(
                    /^\/api\/auth\/line\/start\?entry=cowork&connect_token=clc_/
                );
            }

            for (const oldPath of [
                '/api/line/binding',
                '/api/line/binding-code',
                '/api/me/connect-line/start',
            ]) {
                expect((await apiCtx.get(oldPath)).status(), `${oldPath} 应已关闭`).toBe(404);
            }
        } finally {
            await apiCtx.dispose();
            await ctx.close();
        }
    });
});
