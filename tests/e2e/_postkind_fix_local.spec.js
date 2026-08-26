// 推送日志失败卡 · 「未指定过账去向」不再是死胡同(2026-07-31)
// ============================================================
// python http.server 静态服 static/dist/home.html + page.route stub /api/**(同
// _home_ux_fix5_local.spec.js 先例)。断言的按钮/文案/选择器全来自真构建产物
// (src/home/{erp-log-card,erp-exc-actions}.ts + static/i18n-data.js)。
//
// 喂进去的那条日志行不是手写的:tests/fixtures/postkind_escalated_log.json 由
// scripts/gen_postkind_fixture.py 跑真 mapper + 真分类器生成(reason / category /
// posting_fix 全是产品代码算出来的),脚本与夹具的一致性由
// tests/unit/test_postkind_escalate_wire.py 每次跑单测时重算比对。
//
// 修前实测(2026-07-31 · 同一 harness · 旧 bundle):卡上按钮只有「查看详情」一个
// ——status=manual 连裸重试都不渲染,摘要那句话教人回上传页重新识别(= 重扣一次 OCR 费)。
//
// 起法:npx playwright test tests/e2e/_postkind_fix_local.spec.js
/* global window, getComputedStyle */

const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8994;
const BASE = `http://127.0.0.1:${PORT}`;
const HOME = `${BASE}/static/dist/home.html`;
const ART = path.join(__dirname, '_artifacts', 'postkind_fix');
const LOG = JSON.parse(
    fs.readFileSync(path.join(__dirname, '..', 'fixtures', 'postkind_escalated_log.json'), 'utf8')
);
const LOG_ID = LOG.items[0].id;

const DESKTOP = { width: 1280, height: 900 };
const MOBILE = { width: 390, height: 844 };

let server;

test.beforeAll(async () => {
    fs.mkdirSync(ART, { recursive: true });
    server = await localServer.start(PORT, '/static/dist/home.html');
});

test.afterAll(() => localServer.stop(server));

const json = (body) => ({ contentType: 'application/json', body: JSON.stringify(body) });

const ME = { username: 'pk', role: 'owner', is_owner: true, tenant_id: 'pk-tenant' };
const SUBJECTS = [{ id: 1, name: 'Sister Makeup Steward Co., Ltd.', tax_id: '0105567178203' }];
const ENDPOINTS = [{ id: 'ep-1', name: 'Express · DATAT', adapter: 'express', config: {} }];

// 进 /home:preboot 早于 main.js 就查 token,先 addInitScript 落 localStorage;
// 套账硬门整页 visibility:hidden,必须真点一个主体过门(摘 class 量到的「可见」是假的)。
async function boot(page, { lang = 'zh', viewport = DESKTOP } = {}) {
    const posted = [];
    await page.setViewportSize(viewport);
    await page.addInitScript((l) => {
        localStorage.setItem('mrpilot_token', 'pk-stub');
        localStorage.setItem('mrpilot_lang', l);
        // Keep static home.html tests on the internal full shell.
        localStorage.setItem('pearnly_entry', 'firm');
    }, lang);
    await page.route('**/api/**', (route) => {
        const req = route.request();
        const p = new URL(req.url()).pathname;
        if (req.method() === 'POST') posted.push({ path: p, body: req.postData() });
        if (p === '/api/me') return route.fulfill(json(ME));
        if (p === '/api/workspace/clients') return route.fulfill(json({ clients: SUBJECTS }));
        if (p === '/api/erp/endpoints') return route.fulfill(json(ENDPOINTS));
        if (p === '/api/erp/logs') return route.fulfill(json(LOG));
        if (p.indexOf('/express-posting-kind') > 0)
            return route.fulfill(json({ ok: true, status: 'pending', posting_kind: 'stock' }));
        return route.fulfill(json({}));
    });
    await page.goto(HOME, { waitUntil: 'domcontentloaded' });
    await page.locator('#workspace-gate-root [data-wsg-pick]').first().click();
    await expect(page.locator('#workspace-gate-root')).toHaveCount(0, { timeout: 15_000 });
    await page.evaluate(() => {
        window.location.hash = '#/push-logs';
    });
    await expect(page.locator('#page-push-logs')).toHaveClass(/active/, { timeout: 15_000 });
    await expect(page.locator('.erp-log-card').first()).toBeVisible({ timeout: 15_000 });
    return posted;
}

test.describe('推送日志 · 未指定过账去向的票就地补选重推', () => {
    test('选库存 → 重推:载荷真带上 posting_kind,不必回上传页重新识别', async ({ page }) => {
        const posted = await boot(page, { lang: 'zh' });
        const card = page.locator('.erp-log-card').first();

        // 修前这里只有「查看详情」一个按钮 —— 卡上多出一个能真解决问题的入口才算出路。
        const open = card.locator('[data-erpexc-acctfix]');
        await expect(open, '失败卡上有补选入口').toBeVisible();
        expect(await open.innerText()).toBe('选过账去向');

        const panel = page.locator(`[data-acctfix-panel="${LOG_ID}"]`);
        expect(await panel.isVisible(), '面板默认收起').toBe(false);
        await open.click();
        await expect(panel, '点开后面板真展开').toBeVisible();
        // [hidden] 与 display:flex 打过架(见 home-10-push-logs.css 注释)· 量真值不看属性。
        expect(await panel.evaluate((el) => getComputedStyle(el).display)).toBe('flex');
        const box = await panel.boundingBox();
        expect(box.height, '面板真占了高度').toBeGreaterThan(40);

        // 票面商品行必须摆在选之前:选库存/服务是会计的判断,判断要有据可依。
        const panelText = await panel.innerText();
        expect(panelText).toContain('แชมพู 500ml');
        expect(panelText).toContain('ครีมนวดผม 250ml');
        // 「选了会怎样 / 还能不能改」两句都得在场(这是会真动 Express 库存的决定)。
        expect(panelText).toContain('Express 里动库存并结转成本');
        expect(panelText).toContain('删掉那张单再重来');

        await page.screenshot({ path: path.join(ART, '01-panel-open-zh.png') });

        const sel = panel.locator('[data-postkind-select]');
        expect(await sel.locator('option').allInnerTexts()).toEqual([
            '请选择…',
            '库存 · 真实进出库',
            '服务 · 非库存',
        ]);

        // 空选提交不许静默:选错方向会真扣客户库存,宁可挡住。
        await panel.locator('[data-acctfix-submit]').click();
        expect(posted.filter((r) => r.path.indexOf('express-posting-kind') > 0)).toHaveLength(0);

        await sel.selectOption('stock');
        await panel.locator('[data-acctfix-submit]').click();
        await expect
            .poll(() => posted.filter((r) => r.path.indexOf('express-posting-kind') > 0).length)
            .toBe(1);

        const call = posted.find((r) => r.path.indexOf('express-posting-kind') > 0);
        expect(call.path).toBe(`/api/erp/logs/${LOG_ID}/express-posting-kind`);
        expect(JSON.parse(call.body)).toEqual({ posting_kind: 'stock' });

        await page.screenshot({ path: path.join(ART, '02-submitted-zh.png') });
    });

    test('屏幕上不许出现会计按不出来的东西(机器码 / 回上传页重新识别)', async ({ page }) => {
        await boot(page, { lang: 'zh' });
        await page.locator('.erp-log-card [data-erpexc-acctfix]').click();
        const body = await page.locator('body').innerText();
        expect(body, '不摆机器码').not.toContain('posting_needs_review');
        expect(body, '不摆载荷字段名').not.toContain('posting_kind');
        expect(body, '不再教人回上传页重新识别').not.toContain('重新识别推送');
    });

    // 每种语言开一个新 context:套账硬门把选中的主体记在 localStorage,同一个 page 连开
    // 第二遍就不弹门了,那样等于绕过铁律「必须真点门过去」。
    test('泰语 / 英语 / 日语各说各话', async ({ browser }) => {
        for (const [lang, openLabel, stockLabel] of [
            ['th', 'เลือกการลงบัญชี', 'สินค้าคงคลัง · เข้าออกคลังจริง'],
            ['en', 'Choose posting target', 'Stock · real inventory movement'],
            ['ja', '計上先を選ぶ', '在庫 · 実際の入出庫'],
        ]) {
            const ctx = await browser.newContext();
            const page = await ctx.newPage();
            await boot(page, { lang });
            const open = page.locator('.erp-log-card [data-erpexc-acctfix]');
            expect(await open.innerText(), `${lang} 按钮`).toBe(openLabel);
            await open.click();
            const panel = page.locator(`[data-acctfix-panel="${LOG_ID}"]`);
            await expect(panel).toBeVisible();
            expect(await panel.innerText(), `${lang} 选项`).toContain(stockLabel);
            if (lang !== 'ja') {
                expect(await panel.innerText(), `${lang} 页不该回落中文`).not.toContain('库存');
            }
            await page.screenshot({ path: path.join(ART, `03-panel-${lang}.png`) });
            await ctx.close();
        }
    });

    test('手机端 390:多出来的按钮不许挤掉买方/目标系统,面板照样够得着', async ({ browser }) => {
        const ctx = await browser.newContext();
        const page = await ctx.newPage();
        await boot(page, { lang: 'th', viewport: MOBILE });

        // 卡上多一个按钮就把这两列从 132px 挤到 40px(名字只剩两个字)· 修法是 760px 下让
        // 操作区自己占一行(home-10-push-logs.css)。这里量真宽,不看类名。
        const widths = await page
            .locator('.erp-log-card .erp-log-party span')
            .evaluateAll((els) => els.map((el) => el.getBoundingClientRect().width));
        expect(widths.length).toBe(2);
        for (const w of widths) expect(w).toBeGreaterThan(150);

        await page.locator('.erp-log-card [data-erpexc-acctfix]').click();
        const panel = page.locator(`[data-acctfix-panel="${LOG_ID}"]`);
        await expect(panel).toBeVisible();
        const box = await panel.boundingBox();
        expect(box.x, '面板没被挤出屏幕左侧').toBeGreaterThanOrEqual(0);
        expect(box.x + box.width, '面板没被挤出屏幕右侧').toBeLessThanOrEqual(MOBILE.width + 1);
        const selBox = await panel.locator('[data-postkind-select]').boundingBox();
        expect(selBox.height, '手机端下拉够得着').toBeGreaterThanOrEqual(24);
        await page.screenshot({ path: path.join(ART, '04-mobile-th.png') });
        await ctx.close();
    });
});
