// 后台卡点上屏 · 真浏览器视觉验收(真后端 + 真库 + 真前端产物)
// =====================================================================
// 验的是 _ai_billing_wire_verify.spec.js 的 s5 证据里那一屏:
//   blocked: "后台在这里停住:insufficient_balance。…"  retryBtn: "重试"  topupLinks: 0
// 修完应当是:人话原因 + 「去充值」深链;内部成本封顶那张卡则不该出现充值按钮。
//
// 零 page.route 桩:/api/workorder/orders/{id} 由真后端按真 work_order_events 算出
// blocked_reasons,页面是 static/dist/ai.js 真产物。停机 fixture 直接落 step_stuck 事件
// (原因码是引擎写的那几个字面量),不重烧真 OCR ——本轮改的是「码怎么上屏」,不是码怎么产生;
// 码怎么产生由 tests/unit/test_workorder_billing.py 的真库扣费用例守。
//
// 起法:PEARNLY_E2E_BASE_URL=http://127.0.0.1:7860 npx playwright test tests/e2e/_ai_blocked_reasons_verify.spec.js
/* global window, document */

const { test, expect } = require('@playwright/test');
const { execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const BASE = process.env.PEARNLY_E2E_BASE_URL || 'http://127.0.0.1:7860';
const USER = 'stw_e2e';
const PASS = 'StwVerify#2026';
const TENANT = 'b2000000-0000-4000-8000-000000000001';
const CLIENT_ID = 84;
const ART = path.join(__dirname, '_artifacts', 'ai_blocked_reasons');
const EVID = path.join(ART, 'evidence.json');
const TOPUP = 'a[href="#/settings?focus=billing"]';

const DESKTOP = { width: 1280, height: 900 };
const MOBILE = { width: 390, height: 844 };

// 没被别的用例占用的账期(每个 fixture 一张单,跑完删干净)。
const CASES = {
    money: { period: '2569-11', reasons: ['ocr_quota_deferred:1', 'insufficient_balance'] },
    cap: { period: '2569-12', reasons: ['ocr_cost_cap_exceeded'] },
};

fs.mkdirSync(ART, { recursive: true });
const evidence = {};
function record(k, v) {
    evidence[k] = v;
    fs.writeFileSync(EVID, JSON.stringify(evidence, null, 2), 'utf8');
}

function psql(sql) {
    return execFileSync(
        'docker',
        ['exec', 'pearnly-db', 'psql', '-U', 'pearnly', '-d', 'pearnly', '-t', '-A', '-c', sql],
        { encoding: 'utf8' }
    ).trim();
}

function seedStuckOrder(period, reasons) {
    dropOrder(period);
    // RETURNING 的输出后面跟着 "INSERT 0 1" 状态行(-t -A 也压不掉),取首行才是 uuid。
    const id = psql(
        `insert into work_orders (tenant_id, workspace_client_id, period, intent, status, current_step) ` +
            `values ('${TENANT}', ${CLIENT_ID}, '${period}', 'monthly_vat', 'stuck', 'classify') returning id;`
    ).split('\n')[0];
    psql(
        `insert into work_order_events (tenant_id, work_order_id, step, event_type, payload, actor) ` +
            `values ('${TENANT}', '${id}', 'classify', 'step_stuck', ` +
            `'{"reasons": ${JSON.stringify(reasons)}}'::jsonb, 'system');`
    );
    return id;
}

function dropOrder(period) {
    const id = psql(
        `select id from work_orders where workspace_client_id=${CLIENT_ID} and period='${period}';`
    );
    if (!id) return;
    psql(`delete from work_order_events where work_order_id='${id}';`);
    psql(`delete from work_order_items where work_order_id='${id}';`);
    psql(`delete from work_orders where id='${id}';`);
}

let TOKEN = '';

test.beforeAll(async ({ request }) => {
    const r = await request.post(`${BASE}/api/login`, {
        data: { username: USER, password: PASS, entry: 'ai' },
    });
    expect(r.status()).toBe(200);
    TOKEN = (await r.json()).token;
});

test.afterAll(() => {
    Object.values(CASES).forEach((c) => dropOrder(c.period));
});

async function open(page, { lang, viewport, period }) {
    const errs = [];
    page.on('console', (m) => {
        if (m.type() === 'error') errs.push(m.text());
    });
    page.on('pageerror', (e) => errs.push('pageerror: ' + e.message));
    await page.setViewportSize(viewport);
    await page.addInitScript(
        ([t, l]) => {
            window.localStorage.setItem('mrpilot_token_ai', t);
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [TOKEN, lang]
    );
    await page.goto(`${BASE}/ai#/client/${CLIENT_ID}/wo?period=${period}`, {
        waitUntil: 'domcontentloaded',
    });
    return errs;
}

// 真渲染取证:文本 + 可见性 + 计算样式(CSS 属性设上了不等于按钮真看得见)。
async function cardView(page) {
    return page.evaluate((topup) => {
        const q = (s) => document.querySelector(s);
        const blocked = q('.wo-guide .rv-blocked');
        const link = q('.wo-guide ' + topup);
        const retry = q('[data-action="wo-retry-stuck"]');
        const box = link ? link.getBoundingClientRect() : null;
        const cs = link ? window.getComputedStyle(link) : null;
        return {
            blocked: blocked ? blocked.textContent.trim() : null,
            topupText: link ? link.textContent.trim() : null,
            topupHref: link ? link.getAttribute('href') : null,
            topupVisible: !!(box && box.width > 0 && box.height > 0 && cs.display !== 'none'),
            topupCount: document.querySelectorAll('.wo-guide ' + topup).length,
            retryText: retry ? retry.textContent.trim() : null,
        };
    }, TOPUP);
}

test.describe.serial('工单卡:卡点说人话 + 余额不足给出路', () => {
    for (const cfg of [
        { lang: 'zh', viewport: DESKTOP, tag: 'zh-desktop', shot: '01', word: '余额' },
        { lang: 'th', viewport: MOBILE, tag: 'th-mobile', shot: '02', word: 'เครดิต' },
    ]) {
        test(`跑一半没钱:人话原因 + 去充值(${cfg.tag})`, async ({ page }) => {
            test.setTimeout(120000);
            seedStuckOrder(CASES.money.period, CASES.money.reasons);
            const errs = await open(page, { ...cfg, period: CASES.money.period });
            await expect(page.locator('.wo-guide .rv-blocked')).toBeVisible({ timeout: 30000 });
            const view = await cardView(page);
            await page.screenshot({
                path: path.join(ART, `${cfg.shot}-余额不足卡点-${cfg.tag}.png`),
                fullPage: true,
            });
            record(`money_${cfg.tag}`, { view, consoleErrors: errs });
            // ① 生标识符一个都不许上屏(两个原因码都要说人话)
            expect(view.blocked).not.toContain('insufficient_balance');
            expect(view.blocked).not.toContain('ocr_quota_deferred');
            expect(view.blocked).toContain(cfg.word);
            // ② 出路真在屏上、真是那条深链(不是只把 CSS 属性设上)
            expect(view.topupCount).toBe(1);
            expect(view.topupVisible).toBe(true);
            expect(view.topupHref).toBe('#/settings?focus=billing');
            // ③ 重试还在(充值完就地重试),但不再是唯一出路
            expect(view.retryText).toBeTruthy();
            expect(errs).toEqual([]);
        });
    }

    test('内部成本封顶:同一段渲染,不该出现充值按钮(zh-desktop)', async ({ page }) => {
        test.setTimeout(120000);
        seedStuckOrder(CASES.cap.period, CASES.cap.reasons);
        const errs = await open(page, { lang: 'zh', viewport: DESKTOP, period: CASES.cap.period });
        await expect(page.locator('.wo-guide .rv-blocked')).toBeVisible({ timeout: 30000 });
        const view = await cardView(page);
        await page.screenshot({
            path: path.join(ART, '03-成本封顶卡点-zh-desktop.png'),
            fullPage: true,
        });
        record('cap_zh-desktop', { view, consoleErrors: errs });
        expect(view.blocked).not.toContain('ocr_cost_cap_exceeded');
        expect(view.blocked).toContain('预算');
        expect(view.topupCount).toBe(0); // 我们的预算问题不该记到用户账上
        expect(view.retryText).toBeTruthy();
        expect(errs).toEqual([]);
    });
});
