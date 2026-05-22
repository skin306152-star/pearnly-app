// Pearnly · 着陆页 smoke
// 阶段 4 Task 4.2 · 第一个 E2E 烟测 · 不依赖测试账号 · 不点表单 · 不调后端
//
// 覆盖 4 件事(EXECUTION_PLAN.md Task 4.2):
//   1) 着陆页 200 + title + 顶栏 logo 渲染
//   2) 顶栏关键 CTA(登录 / 立即试用) + 语言 dropdown 可见
//   3) 4 语切换(zh/en/th/ja)· <html lang> 真变 + 顶栏文字字符集真换
//   4) 全程无 console.error / pageerror(subscribeI18n 类陷阱守门)

const { test, expect } = require('@playwright/test');

// 4 语字符集判定 · 不依赖具体词(文案可能改 · 字符集不变)
const LANG_TEXT_OK = {
  zh: (t) => /[一-鿿]/.test(t) && !/[぀-ヿ]/.test(t), // 含汉字 + 不含假名
  en: (t) => /^[\x00-\x7f]+$/.test(t) && /[A-Za-z]/.test(t),          // 纯 ASCII + 含字母
  ja: (t) => /[぀-ヿ]/.test(t),                                // 含平/片假名
  th: (t) => /[฀-๿]/.test(t),                                // 含泰文字符
};

test('着陆页 smoke · 加载 + 顶栏 + 4 语切换 + 无 console error', async ({ page }) => {
  const consoleErrors = [];
  const pageErrors = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => pageErrors.push(err.message));

  // 清 localStorage 让 applyLang() 走默认 'th' 路径 · 保证测试可重复
  await page.addInitScript(() => {
    try { localStorage.clear(); } catch (e) { /* ignore */ }
  });

  // ────── 1) 着陆页 200 + 标题 + logo 渲染
  const resp = await page.goto('/');
  expect(resp?.status(), '着陆页 HTTP 状态').toBeLessThan(400);
  await expect(page).toHaveTitle(/Pearnly/i);
  await expect(page.locator('.brand-name').first()).toBeVisible();

  // ────── 2) 顶栏关键 CTA + 语言 dropdown 可见
  await expect(
    page.locator('[data-open-auth="login"]').first(),
    '顶栏登录按钮'
  ).toBeVisible();
  await expect(
    page.locator('[data-open-auth="signup"]').first(),
    '顶栏立即试用按钮'
  ).toBeVisible();
  await expect(page.locator('#lang-dd-btn'), '语言 dropdown 按钮').toBeVisible();

  // ────── 3) 4 语切换 · html[lang] 真变 + 顶栏文字字符集真换
  const html = page.locator('html');
  const topbarLogin = page.locator('[data-i18n="topbar-login"]').first();

  for (const lang of ['zh', 'en', 'ja', 'th']) {
    await page.locator('#lang-dd-btn').click();
    await expect(
      page.locator('#lang-dd-menu'),
      `${lang} · 菜单展开`
    ).toHaveClass(/show/);

    await page.locator(`.lang-dd-item[data-lang="${lang}"]`).click();

    await expect(html, `${lang} · <html lang>`).toHaveAttribute('lang', lang);

    const txt = ((await topbarLogin.textContent()) || '').trim();
    expect(txt.length, `${lang} · 顶栏登录文字非空`).toBeGreaterThan(0);
    expect(
      LANG_TEXT_OK[lang](txt),
      `${lang} · 顶栏登录文字字符集 (got="${txt}")`
    ).toBe(true);
  }

  // ────── 4) 全程无 console.error / pageerror
  expect(
    pageErrors,
    `pageerror(uncaught JS 异常): ${pageErrors.join(' | ')}`
  ).toEqual([]);
  expect(
    consoleErrors,
    `console.error: ${consoleErrors.join(' | ')}`
  ).toEqual([]);
});
