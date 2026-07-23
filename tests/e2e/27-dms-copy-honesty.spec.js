// DMS P1 全量根治 · 主窗收口验收(打的是 build 后的 static/dist,即真实上线形态)· 常驻回归闸
// 起法:npx playwright test tests/e2e/27-dms-copy-honesty.spec.js
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8975;
const BASE = `http://127.0.0.1:${PORT}`;
const OUT = path.join(__dirname, '_artifacts', 'dms_p1_closure');
fs.mkdirSync(OUT, { recursive: true });

const EP = {
    id: 'E1',
    adapter: 'mrerp_dms',
    enabled: true,
    config: {
        admin_username_enc: 'x',
        admin_password_enc: 'y',
        booking_defaults: { booking_prefix: 'PN' },
    },
};

const LOGS = {
    items: [
        {
            id: 1,
            created_at: '2026-07-23T09:00:00Z',
            status: 'success',
            seller_name: 'สมชาย ใจดี',
            invoice_no: 'C99',
            request_body: { adapter: 'mrerp_dms', trigger: 'dms_web', mode: 'create' },
        },
        {
            id: 2,
            created_at: '2026-07-23T09:30:00Z',
            status: 'success',
            seller_name: 'มานะ รักดี',
            invoice_no: 'BK6907001',
            request_body: { adapter: 'mrerp_dms', trigger: 'line_dms', mode: 'booking' },
        },
    ],
    total: 2,
};

let server;
test.beforeAll(async () => {
    server = await localServer.start(PORT, '/static/dist/dms.html');
});
test.afterAll(() => localServer.stop(server));

async function boot(page, lang) {
    const errors = [];
    page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));
    page.on('pageerror', (e) => errors.push(String(e)));
    await page.route('**/api/**', (route) => {
        const url = route.request().url();
        const json = (o) =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(o),
            });
        if (url.includes('/api/dms/session')) return json({ ok: true, is_owner: true });
        if (url.includes('/api/erp/endpoints')) return json({ endpoints: [EP] });
        if (url.includes('/api/dms/records') || url.includes('/api/erp/logs')) return json(LOGS);
        if (url.includes('/api/me/credits'))
            return json({ has_tenant: true, is_owner: true, balance_thb: 500 });
        if (url.includes('/api/me')) return json({ id: 'owner-1', role: 'owner' });
        return json({ ok: true });
    });
    await page.addInitScript((l) => {
        try {
            localStorage.setItem('mrpilot_token', 'stub');
            localStorage.setItem('mrpilot_lang', l);
        } catch (e) {
            void e;
        }
    }, lang);
    await page.goto(`${BASE}/static/dist/dms.html`);
    await page.waitForSelector('#dmsShell.on');
    return errors;
}

test('C-2 · 录入页标题四语同义(zh 不再说「订车」)', async ({ page }) => {
    const seen = {};
    for (const lang of ['zh', 'th', 'en', 'ja']) {
        await boot(page, lang);
        const h1 = page.locator('#dx-flow-title');
        await expect(h1).toBeVisible();
        const cs = await h1.evaluate((el) => {
            const s = el.ownerDocument.defaultView.getComputedStyle(el);
            const r = el.getBoundingClientRect();
            return {
                d: s.display,
                v: s.visibility,
                w: Math.round(r.width),
                h: Math.round(r.height),
            };
        });
        expect(cs.d).not.toBe('none');
        expect(cs.v).toBe('visible');
        expect(cs.w).toBeGreaterThan(50);
        expect(cs.h).toBeGreaterThan(10);
        seen[lang] = (await h1.textContent()).trim();
        await page.screenshot({ path: path.join(OUT, `web-title-${lang}.png`) });
    }
    expect(seen.zh).not.toContain('订车');
    expect(seen.th).not.toContain('ใบจอง');
    expect(seen.en.toLowerCase()).not.toContain('booking');
    expect(seen.ja).not.toContain('予約');
    console.log('titles', JSON.stringify(seen, null, 1));
});

test('C-1/C-3/C-4 · 连接向导只承诺网页真做的事 + 前缀标明作用域', async ({ page }) => {
    for (const lang of ['zh', 'th']) {
        const errors = await boot(page, lang);
        await page
            .locator('[data-dx-erp-act="config"], #dx-erp-config, .dx-erp-card button')
            .first()
            .click();
        await page.waitForSelector('#dms-wizard-overlay .dms-wizard');
        const sub = await page
            .locator('#dms-wizard-overlay .dms-wizard > div')
            .nth(1)
            .textContent();
        const body = await page.locator('#dms-wizard-overlay').innerText();
        // 网页路不建订车单:副标题不许再承诺"自动建订车单"
        if (lang === 'zh') {
            expect(sub).not.toMatch(/建订车单|自动建客户、建订车单/);
            expect(body).toMatch(/LINE/); // 前缀说明点明作用域
        } else {
            expect(sub).toContain('DMS');
        }
        await page.screenshot({ path: path.join(OUT, `web-wizard-${lang}.png`) });
        expect(errors, errors.join('\n')).toEqual([]);
    }
});

test('C-3 · 连接卡状态行不再有假的「自动推送」', async ({ page }) => {
    await boot(page, 'zh');
    const card = page.locator('.dx-erp-card, [class*="dx-erp"]').first();
    await expect(card).toBeVisible();
    const txt = await card.innerText();
    expect(txt).not.toContain('自动推送');
    expect(txt).not.toContain('手动推送');
    const cs = await card.evaluate((el) => {
        const s = el.ownerDocument.defaultView.getComputedStyle(el);
        const r = el.getBoundingClientRect();
        return { d: s.display, v: s.visibility, w: Math.round(r.width) };
    });
    expect(cs.d).not.toBe('none');
    expect(cs.v).toBe('visible');
    expect(cs.w).toBeGreaterThan(100);
    await page.screenshot({ path: path.join(OUT, 'web-erp-card.png') });
});

test('C-8 · 推送记录页认得出 LINE 订车行', async ({ page }) => {
    await boot(page, 'zh');
    await page.click('.dms-nav-item[data-view="records"]');
    await page.waitForSelector('.dms-rec-row, .dms-rec-table, #dms-view-records table', {
        timeout: 10000,
    });
    const body = await page.locator('#dms-view-records').innerText();
    expect(body).toContain('订车单');
    expect(body).toContain('BK6907001');
    await page.screenshot({ path: path.join(OUT, 'web-records-booking.png'), fullPage: true });
});

test('P1-12 · 选车面板过期屏四语给出可执行指路', async ({ page }) => {
    const seen = {};
    for (const lang of ['th', 'zh', 'en', 'ja']) {
        await page.addInitScript(
            (l) => {
                try {
                    localStorage.setItem('mrpilot_lang', l);
                } catch (e) {
                    void e;
                }
            },
            (l) => l
        );
        await page.route('**/api/dms/pick/**', (route) =>
            route.fulfill({
                status: 401,
                contentType: 'application/json',
                body: JSON.stringify({ detail: 'dms_pick.expired' }),
            })
        );
        await page.addInitScript((l) => {
            try {
                localStorage.setItem('mrpilot_lang', l);
            } catch (e) {
                void e;
            }
        }, lang);
        await page.goto(`${BASE}/static/dist/dms-pick.html?t=expired`);
        await page.waitForSelector('.err, [class*="state"], body', { timeout: 10000 });
        await page.waitForTimeout(400);
        seen[lang] = await page.locator('body').innerText();
        await page.screenshot({ path: path.join(OUT, `web-pick-expired-${lang}.png`) });
    }
    // 泰语是真实用户读的那版:必须说清「不必重拍身份证」
    expect(seen.th).toMatch(/เมนู/);
    expect(seen.th).toMatch(/ไม่ต้อง.*บัตร|บัตรประชาชนซ้ำ/);
    expect(seen.zh).toMatch(/不必|无需/);
    console.log('pick-expired th =', seen.th.replace(/\n+/g, ' | ').slice(0, 400));
});
