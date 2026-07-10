// Pearnly · 着陆页 smoke
// 适配 static/landing/ 登录卡 SPA(login.html 巨石退场后 · landing.js 运行时渲染)。
// 旧版测顶栏 CTA(.brand-name / [data-open-auth]),着陆页换新后 DOM 变,此处改测 SPA 实际元素。
//
// 覆盖:
//   1) 着陆页 200 + title + landing.js SPA 渲染(品牌 logo + 登录卡 + SSO)
//   2) 4 语切换(.language-switcher button[data-lang])· 登录卡标题字符集真换
//   3) 全程无 console.error / pageerror(i18n 渲染陷阱守门)

const { test, expect } = require('@playwright/test');

// 4 语字符集判定 · 不依赖具体词(文案可能改 · 字符集不变)
const LANG_TEXT_OK = {
    zh: (t) => /[一-鿿]/.test(t) && !/[぀-ヿ]/.test(t), // 含汉字 + 不含假名
    en: (t) => /[A-Za-z]/.test(t) && !/[一-鿿぀-ヿ฀-๿]/.test(t), // 含拉丁字母 + 不含 CJK/泰(heading 带 emoji 装饰 · 不用纯 ASCII)
    ja: (t) => /[぀-ヿ]/.test(t), // 含平/片假名
    th: (t) => /[฀-๿]/.test(t), // 含泰文字符
};

test('着陆页 smoke · 加载 + SPA 渲染 + 4 语切换 + 无 console error', async ({ page }) => {
    const consoleErrors = [];
    const pageErrors = [];

    page.on('console', (msg) => {
        if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', (err) => pageErrors.push(err.message));

    await page.addInitScript(() => {
        try {
            localStorage.clear();
        } catch (e) {
            /* ignore */
        }
    });

    // ────── 1) 登录页 200 + 标题 + landing.js SPA 渲染
    // 脸0(2026-07-10):根路径 `/` 已改为品牌门户,原登录着陆页挪到 `/login` · smoke 测登录 SPA 走 /login。
    const resp = await page.goto('/login');
    expect(resp?.status(), '着陆页 HTTP 状态').toBeLessThan(400);
    await expect(page).toHaveTitle(/Pearnly/i);
    await expect(page.locator('.brand-logo').first(), '品牌 logo').toBeVisible();
    await expect(page.locator('.auth-card').first(), '登录卡').toBeVisible();
    await expect(page.locator('[data-sso="google"]').first(), 'Google SSO').toBeVisible();
    await expect(page.locator('[data-sso="line"]').first(), 'LINE SSO').toBeVisible();

    // ────── 2) 4 语切换 · 登录卡标题字符集真换
    const heading = page.locator('.auth-heading').first();
    for (const lang of ['zh', 'en', 'ja', 'th']) {
        await page.locator(`.language-switcher button[data-lang="${lang}"]`).first().click();
        const txt = ((await heading.textContent()) || '').trim();
        expect(txt.length, `${lang} · 登录卡标题非空`).toBeGreaterThan(0);
        expect(LANG_TEXT_OK[lang](txt), `${lang} · 标题字符集 (got="${txt}")`).toBe(true);
    }

    // ────── 3) 全程无 console.error / pageerror
    expect(pageErrors, `pageerror(uncaught JS 异常): ${pageErrors.join(' | ')}`).toEqual([]);
    expect(consoleErrors, `console.error: ${consoleErrors.join(' | ')}`).toEqual([]);
});
