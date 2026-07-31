// Pearnly 本机验收 · 确认放行的推送没等到回执时,失败卡说的是不是人话
// ============================================================
// 本机真栈脚本,不进 CI(需 PEARNLY_E2E_LOCAL=1 + 本机 127.0.0.1:7860 + 开发库里一条预置行,
// 建行 SQL 见 scratchpad/confirmed_unacked_seed.sql,形状逐字抄自
// agent_store.close_unacked_confirmed 真写出来的那条 UPDATE)。
//
// 验的是「至多一次的收尾摆到会计眼前长什么样」:
//   ① 摘要是本地化过的人话,且点名要核对哪一张票(不点名 = 让她把整月的票翻一遍);
//   ② 屏幕上不出现 confirmed_push_unacked / EXPRESS_MANUAL 这类机器码;
//   ③ 不许说死「写了」或「没写」—— 系统分不出来,说死「没写」她就会再推一次,那是两张;
//   ④ 泰语切过去照样是泰语。
// ============================================================

/* global document */

const { test, expect } = require('@playwright/test');
const { hasCreds } = require('./_helpers/auth');
const { enterApp, openRoute, expandAllGroups } = require('./_helpers/app');

const LOCAL = !!process.env.PEARNLY_E2E_LOCAL;
const SEEDED_INVOICE = 'IV69/09901';

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

async function reasonOf(page) {
    const card = page.locator('.erp-log-card', { hasText: SEEDED_INVOICE }).first();
    await expect(card, '预置的收尾行在列表里').toBeVisible({ timeout: 15_000 });
    const reason = card.locator('.erp-log-reason span');
    await expect(reason, '失败摘要在场').toBeVisible();
    return reason;
}

// 摘要条是单行 nowrap + ellipsis:手机宽下大半句会被省略号吃掉。逐字用 Range 量出**真正
// 看得见**的那一截 —— 断言整句里有票号是自欺,会计看不见的那半句不算说过。
async function visiblePrefix(span) {
    return span.evaluate((el) => {
        const text = el.textContent || '';
        const range = document.createRange();
        const max = el.getBoundingClientRect().width;
        for (let i = 1; i <= text.length; i++) {
            range.setStart(el.firstChild, 0);
            range.setEnd(el.firstChild, i);
            if (range.getBoundingClientRect().width > max) return text.slice(0, i - 1);
        }
        return text;
    });
}

test.describe('推送日志 · 确认推送未回执的收尾卡', () => {
    test.skip(!LOCAL, '本机真栈脚本 · 需 PEARNLY_E2E_LOCAL=1');
    test.skip(!hasCreds(), '需测试账号');

    test('人话 + 点名票号 + 不下结论 · 中泰各说各话', async ({ page }) => {
        await freshLogin(page, 'zh');
        await enterApp(page);
        // 推送日志在「销售」折叠组里,不展开点不到
        await expandAllGroups(page);
        await openRoute(page, 'push-logs');

        const zh = await (await reasonOf(page)).innerText();
        expect(zh).toContain(SEEDED_INVOICE); // ① 点名核对哪一张
        expect(zh).toContain('Express');
        expect(zh, '占位符不许原样上屏').not.toContain('{doc}');

        const body = await page.locator('body').innerText();
        expect(body, '机器码不许上屏').not.toContain('confirmed_push_unacked');
        expect(body, '哨兵前缀不许上屏').not.toContain('EXPRESS_MANUAL');

        // ③ 结果未知就得说未知:两头都不能说死
        expect(zh).toContain('可能');
        expect(zh, '不许替她断定没写').not.toMatch(/没有?写进|未写入/);

        await page.screenshot({
            path: 'tests/e2e/_artifacts/confirmed_unacked_card/02-after-zh.png',
            fullPage: false,
        });

        // ④ 手机宽:动作与票号必须落在被省略号截掉之前。首版把「去 Express 核对 IV69/…」
        // 放句尾,390 宽下整句只剩前半段描述,她看得懂发生了什么却不知道该动哪张。
        await page.setViewportSize({ width: 390, height: 780 });
        await page.waitForTimeout(500);
        const shownZh = await visiblePrefix(await reasonOf(page));
        expect(shownZh, '手机宽下票号被省略号吃掉了').toContain(SEEDED_INVOICE);
        expect(shownZh, '手机宽下没说该去哪').toContain('Express');
        await page.screenshot({
            path: 'tests/e2e/_artifacts/confirmed_unacked_card/04-after-zh-390.png',
            fullPage: false,
        });
        await page.setViewportSize({ width: 1440, height: 900 });

        // ⑤ 切泰语 · 同一张卡换一套字
        await page.evaluate(() => localStorage.setItem('mrpilot_lang', 'th'));
        await page.goto('/home');
        // 启动闸刷新后会再弹一次;这一轮它可能已被上一轮的选择记住,点不到就直接往下走。
        await page
            .locator('#workspace-gate-root [data-wsg-pick]')
            .first()
            .click({ timeout: 5_000 })
            .catch(() => {});
        await expect(page.locator('#sidebar')).toBeVisible({ timeout: 15_000 });
        await expandAllGroups(page);
        await openRoute(page, 'push-logs');

        const th = await (await reasonOf(page)).innerText();
        expect(th).toContain(SEEDED_INVOICE);
        expect(th).toContain('Express');
        expect(th, '泰语界面不该回落中文').not.toContain('可能');
        expect(th).toContain('อาจ'); // 泰语的「可能」

        await page.screenshot({
            path: 'tests/e2e/_artifacts/confirmed_unacked_card/03-after-th.png',
            fullPage: false,
        });

        await page.setViewportSize({ width: 390, height: 780 });
        await page.waitForTimeout(500);
        const shownTh = await visiblePrefix(await reasonOf(page));
        expect(shownTh, '泰语手机宽下票号被吃掉了').toContain(SEEDED_INVOICE);
        expect(shownTh).toContain('Express');
        await page.screenshot({
            path: 'tests/e2e/_artifacts/confirmed_unacked_card/05-after-th-390.png',
            fullPage: false,
        });
    });
});
