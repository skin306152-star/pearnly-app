// 主控 UI 验真探针(长期保留 · 非业务测试)
// ============================================================
// 用途:主控 loop 每轮复验"窗口报完成"的 UI 项 —— 真实浏览器登录 + isVisible + getComputedStyle + 截图。
//   grep 类名 / 自跑脚本断言 一律不认;只认这里抓出的渲染像素。
// 跑法(主控自己,凭据内存注入,不打印不提交):
//   $env:PEARNLY_E2E_USER='pearnly_e2e_1'; $env:PEARNLY_E2E_PASS=<内存>;
//   npx playwright test scripts/midcontrol_ui_verify.spec.js --reporter=line
// 产出:scripts/_mc_verify/ 下 *.json + *.png(gitignored · 用完看完即可)
// ============================================================
/* eslint-disable */
const { test, expect } = require('@playwright/test');
const { doUiLogin } = require('../tests/e2e/_helpers/auth');
const fs = require('fs');

const OUT = 'scripts/_mc_verify';
fs.mkdirSync(OUT, { recursive: true });
const result = { ts: new Date().toISOString(), checks: {} };
const errs = [];

test('midcontrol UI verify', async ({ page }) => {
    page.on('console', (m) => m.type() === 'error' && errs.push(m.text()));
    page.on('pageerror', (e) => errs.push('PAGEERROR: ' + e.message));

    await doUiLogin(page);
    await page.waitForTimeout(2500);

    // 关掉任何挡路弹窗(如"选择账套"——测试账号无账套时会弹)· 按 Escape + 点关闭
    for (let i = 0; i < 3; i++) {
        await page.keyboard.press('Escape').catch(() => {});
        await page.waitForTimeout(300);
    }
    await page.waitForTimeout(400);

    // ── 打开设置(头像菜单 → 设置)──
    await openSettings(page);
    await page.waitForTimeout(800);
    // 切账户安全 tab
    await clickAny(page, [
        '.settings-nav-item[data-tab="security"]',
        '.settings-nav-item[data-settings-tab="security"]',
        'text=账户安全',
        'text=บัญชี',
    ]);
    await page.waitForTimeout(1000);
    await page.screenshot({ path: `${OUT}/security.png` });

    // ── A2 忘记密码:可见 + 可点 + 点出弹窗 ──
    const link = page.locator('#cpw-forgot-link').first();
    const a2 = {
        linkCount: await page.locator('#cpw-forgot-link').count(),
        visible: false,
        clicked: false,
        overlay: false,
    };
    if (a2.linkCount > 0) {
        a2.visible = await link.isVisible().catch(() => false);
        if (a2.visible) {
            a2.clicked = await link
                .click({ timeout: 3000 })
                .then(() => true)
                .catch(() => false);
            await page.waitForTimeout(1000);
            a2.overlay = await page
                .locator('#cpw-forgot-overlay')
                .isVisible()
                .catch(() => false);
        }
    }
    result.checks.A2_forgot = { ...a2, pass: a2.visible && a2.clicked && a2.overlay };

    // 关掉弹窗(若开了)
    await page
        .locator('#cpw-forgot-cancel, #cpw-forgot-close')
        .first()
        .click()
        .catch(() => {});
    await page.waitForTimeout(400);

    // ── A3 改密输入框样式 ── (取不到不崩,记 null)
    const cs = await page
        .locator('#cpw-old')
        .first()
        .evaluate((el) => {
            const s = getComputedStyle(el);
            return {
                borderRadius: s.borderRadius,
                borderTopWidth: s.borderTopWidth,
                borderStyle: s.borderTopStyle,
                padding: s.padding,
            };
        })
        .catch((e) => ({ error: String(e).slice(0, 80) }));
    // 对照:全站标准输入框(.form-input 或 .form-input-pill,着陆/搜索框)——这里取设置内的对照若有
    result.checks.A3_input = {
        computed: cs,
        // 合格 = 有圆角(非0)且非 inset 默认边框
        pass: !!cs && cs.borderRadius !== '0px' && cs.borderStyle !== 'inset',
    };

    // ── 1b 按钮颜色:逐页抓主操作按钮 backgroundColor ──
    // 关设置
    await page
        .locator('.settings-close, [data-close-settings], text=×')
        .first()
        .click()
        .catch(() => {});
    await page.waitForTimeout(500);
    const btnChecks = [];
    // 客户管理「设为当前」
    btnChecks.push(
        await probeBtn(page, 'clients', '客户管理', ['.cust-row-btn.primary', 'text=设为当前'])
    );
    // 异常栏「批量重试」
    btnChecks.push(
        await probeBtn(page, 'exceptions', '异常', ['text=批量重试', '.exc-batch-bar button'])
    );
    result.checks.btns_1b = btnChecks;

    result.consoleErrs = errs;
    fs.writeFileSync(`${OUT}/result.json`, JSON.stringify(result, null, 2));
    expect(true).toBe(true);
});

async function probeBtn(page, route, navText, sels) {
    const out = { route, found: false, bg: null, isBlue: null };
    // 导航
    await clickAny(page, [`text=${navText}`, `[data-route="${route}"]`, `text=${route}`]);
    await page.waitForTimeout(1500);
    for (const sel of sels) {
        const el = page.locator(sel).first();
        if ((await el.count()) > 0 && (await el.isVisible().catch(() => false))) {
            out.found = true;
            out.bg = await el
                .evaluate((e) => getComputedStyle(e).backgroundColor)
                .catch(() => null);
            // 蓝 ≈ rgb(37,99,235) 系;黑 ≈ rgb(17,17,17)/rgb(0,0,0)
            out.isBlue =
                !!out.bg &&
                /rgb\(\s*(3[0-9]|4[0-9]|5[0-9])\s*,\s*(8[0-9]|9[0-9]|1[0-3][0-9])\s*,\s*(2[0-9][0-9])/.test(
                    out.bg
                );
            break;
        }
    }
    await page.screenshot({ path: `${OUT}/btn_${route}.png` });
    return out;
}

async function openSettings(page) {
    for (const sel of ['.topbar-avatar', '#topbar-avatar', 'img[alt*="avatar" i]', '.avatar']) {
        const el = page.locator(sel);
        if ((await el.count()) > 0) {
            await el
                .first()
                .click()
                .catch(() => {});
            await page.waitForTimeout(600);
            break;
        }
    }
    await clickAny(page, ['text=设置', 'text=การตั้งค่า', '[data-open-settings]']);
}

async function clickAny(page, sels) {
    for (const sel of sels) {
        const el = page.locator(sel);
        if ((await el.count()) > 0) {
            const ok = await el
                .first()
                .click({ timeout: 2000 })
                .then(() => true)
                .catch(() => false);
            if (ok) return sel;
        }
    }
    return null;
}
