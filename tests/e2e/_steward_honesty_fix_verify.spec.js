// 管家诚实度四修的真浏览器验收 · 真后端 + 真库 + 真大脑,零 page.route 桩。
// 起法(本轮跑的是端口 7861 的第二实例 = 本轮代码;7860 是别的窗口在跑的旧进程):
//   PEARNLY_E2E_BASE_URL=http://127.0.0.1:7861 npx playwright test tests/e2e/_steward_honesty_fix_verify.spec.js
//
// 验的是会计眼睛真能看到的三句话:
//   ① 简报把推失败那个数说成「你自己推失败 N 条」(它只数得到本人推的,与另外三个数不同轴);
//   ② 到期清单的倒计时锚 e-Filing 顺延日,与矩阵页 isOverdue 同一把尺;
//   ③ 全所税额表与单查同一个数(compute 事件同源 —— 本单 package 没跑过,只有 compute)。
// 前置数据:给 Sister Makeup Steward 2569-07(6fd05bba-…)种了一条 compute step_done,
// 模拟「compute 跑完、package 卡住」。清掉:
//   docker exec -i pearnly-db psql -U pearnly -d pearnly -c "set app.bypass_rls='on';
//     DELETE FROM work_order_events WHERE actor='e2e:steward-fix-verify';"
/* global window, document */

const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const BASE = process.env.PEARNLY_E2E_BASE_URL || 'http://127.0.0.1:7861';
const USER = 'stw_e2e';
const PASS = 'StwVerify#2026';
const ART = path.join(__dirname, '_artifacts', 'steward_honesty_fix');
const DESKTOP = { width: 1280, height: 900 };

fs.mkdirSync(ART, { recursive: true });
let TOKEN = '';

test.beforeAll(async ({ request }) => {
    const r = await request.post(`${BASE}/api/login`, {
        data: { username: USER, password: PASS, entry: 'ai' },
    });
    expect(r.status()).toBe(200);
    TOKEN = (await r.json()).token;
    expect(TOKEN.length).toBeGreaterThan(20);
});

async function open(page) {
    await page.setViewportSize(DESKTOP);
    await page.addInitScript(
        ([t]) => {
            window.localStorage.setItem('mrpilot_token_ai', t);
            window.localStorage.setItem('mrpilot_lang', 'zh');
        },
        [TOKEN]
    );
    await page.goto(`${BASE}/ai#/steward`, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#v-steward.on', { state: 'visible', timeout: 30000 });
    await page.waitForSelector('#stwInput', { state: 'visible', timeout: 30000 });
}

// 真敲键盘(fill() 绕过真实按键 = 假绿),等真答复落地(「已开始」那条是应承不是答案)。
async function ask(page, text) {
    const before = await page.locator('.stw-msg.agent .stw-bubble').count();
    await page.locator('#stwInput').click();
    await page.keyboard.type(text, { delay: 12 });
    await page.keyboard.press('Enter');
    await page.waitForFunction(
        (n) => {
            const b = document.querySelectorAll('.stw-msg.agent .stw-bubble');
            if (b.length <= n) return false;
            return !/已开始|เริ่ม「/.test((b[b.length - 1].innerText || '').trim());
        },
        before,
        { timeout: 180000 }
    );
    return (await page.locator('.stw-msg.agent .stw-bubble').last().innerText()).trim();
}

test('开工简报说清推失败那个数是谁推的', async ({ page }) => {
    await open(page);
    const said = await ask(page, '今天先干哪个');
    await page.screenshot({ path: path.join(ART, '01-brief-push-scope-zh.png'), fullPage: true });
    expect(said).toContain('你自己推失败');
    expect(await page.locator('.stw-msg.agent .stw-bubble').last().isVisible()).toBe(true);
});

test('到期清单锚 e-Filing 顺延日', async ({ page }) => {
    await open(page);
    const said = await ask(page, '这个月还有哪些没交');
    await page.screenshot({ path: path.join(ART, '02-due-soon-efiling-zh.png'), fullPage: true });
    expect(said).toMatch(/最近一项/);
    // 表格里的截止日就是答复里那一条(左窗与气泡同一份数据)。
    const due = await page.locator('#stwLeft .stw-table tbody tr td').nth(2).innerText();
    expect(said).toContain(due.trim());
});

test('全所税额表与单查同一个数', async ({ page }) => {
    await open(page);
    const one = await ask(page, 'Sister Makeup Steward 这个月要交多少税');
    const all = await ask(page, '这个月所有客户的应交税额给我列个表');
    await page.screenshot({
        path: path.join(ART, '03-tax-matrix-same-source-zh.png'),
        fullPage: true,
    });
    expect(one).toContain('22960.00');
    expect(all).toContain('22960.00'); // package 没跑过,读交付物快照的话这里会是「还没算到」
});
