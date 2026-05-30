// Pearnly E2E · 18 改密 UI 视觉验收(A2/A3 · 主控浏览器打回项)· REFACTOR-WB-BTN
// ============================================================
// 背景:.cpw-* CSS 在 C2 拆 home.css 时整块漏迁(98f184c~1:home.css 行7443-7620),
//   导致「忘记当前密码?」链接渲染成无样式裸 button(不可见/点不到)、改密输入框是浏览器原生裸框。
//   已从原值 RESTORE 到 static/home-30-settings-modal.css(95b7b4e)。
//
// 本 spec = 主控明令的「真浏览器 isVisible + getComputedStyle」验收(grep/MODAL 不认):
//   1) 登录 → 打开设置 modal → 切到「账户安全」tab
//   2) #cpw-forgot-link 真的可见(isVisible)且是文字链接样式(有下划线)
//   3) #cpw-old(.cpw-input)getComputedStyle borderRadius === '9px'(=pill 圆角生效,非裸框 0px)
//   4) 点击 #cpw-forgot-link → #cpw-forgot-overlay 出现且可见
//
// 只读验收 · 不改密码 · 不碰账号状态(与 13-password-change 的 token 失效流互补)。
// env-gated:无凭据(CI)优雅跳过 · 保持 CI 绿(铁律 #2)。
// ============================================================

/* global window, location, getComputedStyle */
const { test, expect } = require('@playwright/test');
const { hasCreds, doUiLogin } = require('./_helpers/auth');

test.describe('改密 UI 视觉验收(A2/A3 · .cpw-* CSS restore)', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');

    test('忘记密码链接可见 + 改密框 pill 圆角 + 忘记弹窗能开', async ({ page }) => {
        await doUiLogin(page);
        expect(page.url(), '登录后应进 /home').toContain('/home');

        // ────── 1) 打开设置 modal(recon-subtab-settings.js 暴露 window.openSettingsModal)
        await page.evaluate(() => {
            if (typeof window.openSettingsModal === 'function') window.openSettingsModal();
            else location.hash = '#/settings';
        });

        // ────── 2) 切到「账户安全」tab(改密表单所在)
        const securityTab = page.locator('.settings-nav-item[data-tab="security"]').first();
        await securityTab.waitFor({ state: 'visible', timeout: 10000 });
        await securityTab.click();

        // 改密表单进场(page-settings DOM-move 进 modal · 给点时间)
        const oldInput = page.locator('#cpw-old');
        await oldInput.waitFor({ state: 'visible', timeout: 10000 });

        // ────── 3) #cpw-forgot-link 真的可见(A2 核心:漏迁前不可见)
        const forgotLink = page.locator('#cpw-forgot-link');
        await expect(
            forgotLink,
            '忘记密码链接应可见(.cpw-forgot-link CSS 已 restore)'
        ).toBeVisible();

        // 是文字链接样式:有下划线
        const deco = await forgotLink.evaluate((el) => getComputedStyle(el).textDecorationLine);
        expect(deco, `忘记链接应有下划线(got ${deco})`).toContain('underline');

        // ────── 4) #cpw-old 是 pill 圆角(A3 核心:漏迁前 borderRadius 0px 裸框)
        const radius = await oldInput.evaluate((el) => getComputedStyle(el).borderRadius);
        expect(radius, `改密输入框应 pill 圆角 9px(got ${radius} · 0px=裸框=CSS 没生效)`).toBe(
            '9px'
        );

        // ────── 5) 点击忘记链接 → #cpw-forgot-overlay 出现
        await forgotLink.click();
        const overlay = page.locator('#cpw-forgot-overlay');
        await expect(overlay, '点忘记链接后弹窗应出现').toBeVisible({ timeout: 5000 });
    });
});
