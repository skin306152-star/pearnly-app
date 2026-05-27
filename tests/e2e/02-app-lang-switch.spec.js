// Pearnly E2E · 02 应用内 4 语切换 · REFACTOR-D1
// ============================================================
// 登录后进 设置 → 通用,用 #general-lang 切 zh/en/th/ja:
//   - <html lang> 真变(home.js applyLang → document.documentElement.lang)
//   - 侧栏文字字符集真换(data-i18n 经 applyLang 重刷)
//   - 全程无 console.error
// 顺序末尾落 th(应用默认)· 不把账号语言偏好留在小众语言。
// ============================================================

const { test, expect } = require('@playwright/test');
const { hasCreds, ensureStorageState, STORAGE_STATE } = require('./_helpers/auth');
const { enterApp } = require('./_helpers/app');
const { attachConsoleGuard, assertNoConsoleErrors } = require('./_helpers/console-guard');
const { LANG_TEXT_OK, LANGS } = require('./_helpers/lang');

test.describe('应用内 4 语切换', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');
    test.use({ storageState: STORAGE_STATE });
    test.beforeAll(async ({ browser }) => {
        await ensureStorageState(browser);
    });

    test('设置→通用 切 zh/en/ja/th → html lang 真变 + 侧栏文字字符集真换 + 无报错', async ({
        page,
    }) => {
        const guard = attachConsoleGuard(page);
        await enterApp(page);

        // 进设置(右上角头像菜单 → 设置)· 设置以「模态」打开(openSettingsModal · 非路由页)
        await page.locator('#avatar-btn').click();
        await page.locator('#avatar-menu-settings').click();

        // 设置模态打开 → 切「通用」tab(tab 可见即模态已开)
        const generalTab = page.locator('.settings-tab[data-tab="general"]');
        await expect(generalTab, '设置模态打开 · 通用 tab 可见').toBeVisible({ timeout: 10_000 });
        await generalTab.click();
        const langSel = page.locator('#general-lang');
        await expect(langSel, '通用 tab 的语言选择器可见').toBeVisible();

        const html = page.locator('html');
        // 字符集锚点用「个人资料」设置 tab(set-tab-profile):4 语字符集全可区分 ——
        // zh 个人资料 / en Profile / th โปรไฟล์ / ja プロフィール(片假名)。
        // (不用 nav-clients:其日语「顧客管理」是纯汉字无假名,与中文无法区分。)
        const profileTab = page.locator('.settings-tab[data-tab="profile"]');

        for (const lang of LANGS) {
            await langSel.selectOption(lang);

            await expect(html, `${lang} · <html lang>`).toHaveAttribute('lang', lang);

            // 文案随语言真重渲(data-i18n=set-tab-profile · 经 applyLang 重刷)
            await expect
                .poll(
                    async () => {
                        const txt = ((await profileTab.textContent()) || '').trim();
                        return LANG_TEXT_OK[lang](txt) ? 'ok' : `bad:${txt}`;
                    },
                    { message: `${lang} · 设置「个人资料」tab 文字字符集` }
                )
                .toBe('ok');
        }

        assertNoConsoleErrors(expect, guard);
    });
});
