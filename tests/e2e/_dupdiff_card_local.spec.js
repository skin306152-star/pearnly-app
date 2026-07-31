// Pearnly 本机验收 · 推送日志失败卡认得出「同钥匙内容不同」(DUPLICATE_CONTENT_DIFFERS)
// ============================================================
// 本机真栈脚本,不进 CI(需 PEARNLY_E2E_LOCAL=1 + 本机 127.0.0.1:7860 + 开发库里一条
// 预置的 manual 日志行)。起法见 docs/ai 交接单;预置行由验收前的一条 SQL 插入,
// 载荷形状逐字抄自 companion agent_store._build_response_body + duplicate_gate.differs_meta。
//
// 验的是「小助手拒了之后会计看到什么」:
//   ① 摘要是本地化过的人话,带得上账上那张的单号与逐字段差异;
//   ② 屏幕上不出现 duplicate_confirmed —— 界面里没有那个按钮,说了就是让人照做不了;
//   ③ 泰语切过去照样是泰语,不回落成小助手那句写死中文。
// ============================================================

const { test, expect } = require('@playwright/test');
const { hasCreds } = require('./_helpers/auth');
const { enterApp, openRoute } = require('./_helpers/app');

const LOCAL = !!process.env.PEARNLY_E2E_LOCAL;
const SEEDED_INVOICE = 'IV69/00473';
const ERP_DOCNUM = 'HP690715-001';

// 本机开发库全仓只有一个测试号,第二次登录会把前一个 token 打成 401。共享的 storageState
// 缓存跨轮复用旧 token,轮到它被踢掉那一轮就红在「账号已在其他设备登录」——所以这里每轮
// 现登一次、马上用掉,不进缓存。
async function freshLogin(page, lang) {
    const resp = await page.request.post('/api/login', {
        data: { username: process.env.PEARNLY_E2E_USER, password: process.env.PEARNLY_E2E_PASS },
    });
    expect(resp.ok(), '本机真栈登录').toBeTruthy();
    const token = (await resp.json()).token;
    // 先落到同源页面再写 localStorage:home.html 的内联脚本在解析阶段就查 token,
    // 查不到当场 location.replace 去 /login。
    await page.goto('/login');
    await page.evaluate(
        ([t, l]) => {
            localStorage.setItem('mrpilot_token', t);
            localStorage.setItem('mrpilot_lang', l);
        },
        [token, lang]
    );
}

test.describe('推送日志 · 查重闸失败卡', () => {
    test.skip(!LOCAL, '本机真栈脚本 · 需 PEARNLY_E2E_LOCAL=1');
    test.skip(!hasCreds(), '需测试账号');

    test('差异摆到卡上 · 中泰各说各话 · 不提任何会计按不出来的参数', async ({ page }) => {
        // 站点默认语言是泰语,先把中文那一遍显式钉住,再切回泰语比对。
        await freshLogin(page, 'zh');
        await enterApp(page);
        await openRoute(page, 'push-logs');

        const card = page.locator('.erp-log-card', { hasText: SEEDED_INVOICE }).first();
        await expect(card, '预置的查重失败行在列表里').toBeVisible({ timeout: 15_000 });

        const reason = card.locator('.erp-log-reason span');
        await expect(reason, '失败摘要在场').toBeVisible();

        // ① 人话 + 单号 + 逐字段差异(字段名是翻过的,不是 base_amount 这种机器名)
        const zh = await reason.innerText();
        expect(zh).toContain(ERP_DOCNUM);
        expect(zh).toContain('税前金额');
        expect(zh).toContain('1,070.00');
        expect(zh).toContain('2,140.00');
        expect(zh, '机器名不许上屏').not.toContain('base_amount');

        // ② 界面上做不到的事一个字都不许说
        const body = await page.locator('body').innerText();
        expect(body, '不许出现载荷参数名').not.toContain('duplicate_confirmed');
        expect(body, '不许原样摆错误码').not.toContain('DUPLICATE_CONTENT_DIFFERS');

        await page.screenshot({
            path: 'tests/e2e/_artifacts/dupdiff_card/01-zh-desktop.png',
            fullPage: false,
        });

        // ③ 切泰语 · 同一张卡换一套字,不回落成小助手那句中文
        await page.evaluate(() => localStorage.setItem('mrpilot_lang', 'th'));
        await page.goto('/home');
        // 启动闸刷新后会再弹一次;这一轮它可能已被上一轮的选择记住,点不到就直接往下走。
        await page
            .locator('#workspace-gate-root [data-wsg-pick]')
            .first()
            .click({ timeout: 5_000 })
            .catch(() => {});
        await expect(page.locator('#sidebar')).toBeVisible({ timeout: 15_000 });
        await openRoute(page, 'push-logs');
        const thCard = page.locator('.erp-log-card', { hasText: SEEDED_INVOICE }).first();
        const th = await thCard.locator('.erp-log-reason span').innerText();
        expect(th).toContain(ERP_DOCNUM);
        expect(th).toContain('มูลค่าก่อนภาษี');
        expect(th, '泰语界面不该出现中文字段名').not.toContain('税前金额');

        await page.screenshot({
            path: 'tests/e2e/_artifacts/dupdiff_card/02-th-desktop.png',
            fullPage: false,
        });
    });
});
