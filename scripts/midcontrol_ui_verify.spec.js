// 主控 UI 验真探针(长期保留 · 非业务测试)
// ============================================================
// 用途:主控 loop 每轮复验"窗口报完成"的 UI 项 —— 真实浏览器登录 + isVisible + getComputedStyle + 截图。
//   grep 类名 / 自跑脚本断言 一律不认;只认这里抓出的渲染像素。
// 跑法(主控自己,凭据内存注入,不打印不提交)· 注意 playwright.config testDir=tests/e2e,
//   跑前先 copy 到 tests/e2e/ 再跑:
//     cp scripts/midcontrol_ui_verify.spec.js tests/e2e/_mc.spec.js
//     $env:PEARNLY_E2E_USER='pearnly_e2e_1'; $env:PEARNLY_E2E_PASS=<内存>;
//     npx playwright test tests/e2e/_mc.spec.js --reporter=line ; rm tests/e2e/_mc.spec.js
//   (import 路径 ./_helpers/auth 已按 tests/e2e/ 位置写)
// 产出:scripts/_mc_verify/ 下 *.json + *.png(gitignored)
// 已验证可用(2026-05-31):A2/A3 真过。关键 = openSettingsModal 直开设置绕过头像菜单 + 强制移除账套弹窗。
// ============================================================
/* eslint-disable */
/* global window, location, getComputedStyle, document */
const { test } = require('@playwright/test');
const { doUiLogin } = require('./_helpers/auth');
const fs = require('fs');

const OUT = 'scripts/_mc_verify';
fs.mkdirSync(OUT, { recursive: true });

test('midcontrol UI verify', async ({ page }) => {
    test.setTimeout(90000);
    const d = {};
    await doUiLogin(page);
    await page.waitForTimeout(1500);

    // 开设置(window.openSettingsModal 直开,绕过头像菜单)
    await page.evaluate(() => {
        if (typeof window.openSettingsModal === 'function') window.openSettingsModal();
        else location.hash = '#/settings';
    });
    await page.waitForTimeout(1000);

    // 账套选择弹窗 เลือกกิจการ(测试账号无账套时强制弹·挡住设置)→ 点"个人"再强制移除
    for (let i = 0; i < 3; i++) {
        const biz = page.getByText('งานส่วนตัว', { exact: false }).last();
        if (await biz.isVisible().catch(() => false)) {
            await biz.click({ force: true, timeout: 2000 }).catch(() => {});
            await page.waitForTimeout(1000);
        } else break;
    }
    await page
        .evaluate(() => {
            document.querySelectorAll('*').forEach((el) => {
                if (
                    el.textContent &&
                    el.textContent.includes('เลือกกิจการ') &&
                    /modal|overlay|dialog/i.test(el.className || '')
                ) {
                    el.style.display = 'none';
                }
            });
        })
        .catch(() => {});
    await page.waitForTimeout(400);

    // 重开设置 + 切账户安全 tab
    await page.evaluate(() => {
        if (typeof window.openSettingsModal === 'function') window.openSettingsModal();
    });
    await page.waitForTimeout(800);
    await page
        .locator('.settings-nav-item[data-tab="security"]')
        .first()
        .click({ force: true, timeout: 5000 })
        .catch(() => {});
    await page.waitForTimeout(800);
    const oldInput = page.locator('#cpw-old');
    await oldInput.waitFor({ state: 'visible', timeout: 6000 }).catch(() => {});
    await page.screenshot({ path: `${OUT}/A_security.png` });

    // A3 改密输入框:pill 圆角 9px + 非 inset 默认框 + 真渲染尺寸
    d.A3 = await oldInput
        .evaluate((el) => {
            const s = getComputedStyle(el);
            const r = el.getBoundingClientRect();
            return {
                borderRadius: s.borderRadius,
                borderStyle: s.borderTopStyle,
                borderColor: s.borderTopColor,
                w: Math.round(r.width),
                h: Math.round(r.height),
            };
        })
        .catch((e) => ({ error: String(e).slice(0, 80) }));

    // A2 忘记密码:可见 + 下划线 + 点击出弹窗
    const fl = page.locator('#cpw-forgot-link');
    d.A2 = { visible: await fl.isVisible().catch(() => false) };
    if (d.A2.visible) {
        d.A2.underline = await fl
            .evaluate((el) => getComputedStyle(el).textDecorationLine)
            .catch(() => null);
        d.A2.clicked = await fl
            .click({ timeout: 3000 })
            .then(() => true)
            .catch(() => false);
        await page.waitForTimeout(1000);
        d.A2.overlay = await page
            .locator('#cpw-forgot-overlay')
            .isVisible()
            .catch(() => false);
        await page.screenshot({ path: `${OUT}/B_forgot_modal.png` });
    }
    d.A2.pass = !!(d.A2.visible && d.A2.clicked && d.A2.overlay);
    d.A3.pass = !!(d.A3.borderRadius === '9px' && d.A3.borderStyle !== 'inset' && d.A3.h > 0);

    fs.writeFileSync(`${OUT}/shots.json`, JSON.stringify(d, null, 2));
});
