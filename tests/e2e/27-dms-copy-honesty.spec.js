// DMS 文案诚实闸 · 只守 28-dms-intake-write-honesty 覆盖不到的两件事:四语标题、选车面板过期屏。
// (连接向导/连接卡/推送记录的文案断言在 28 里,那边是精确文案比对,别在这儿再放一份弱的。)
// 打的是 build 后的 static/dist,即真实上线形态。
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
    config: { admin_username_enc: 'x', booking_defaults: { booking_prefix: 'PN' } },
};

let server;
test.beforeAll(async () => {
    server = await localServer.start(PORT, '/static/dist/dms.html');
});
test.afterAll(() => localServer.stop(server));

async function bootShell(page, lang) {
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
        if (url.includes('/api/me')) return json({ id: 'owner-1', role: 'owner' });
        return json({ ok: true });
    });
    await setLang(page, lang);
    await page.goto(`${BASE}/static/dist/dms.html`);
    await page.waitForSelector('#dmsShell.on');
    return errors;
}

function setLang(page, lang) {
    return page.addInitScript((l) => {
        try {
            localStorage.setItem('mrpilot_token', 'stub');
            localStorage.setItem('mrpilot_lang', l);
        } catch (e) {
            void e;
        }
    }, lang);
}

test('C-2 · 录入页标题四语同义(zh 不再说「订车」——网页只建客户档)', async ({ page }) => {
    const seen = {};
    for (const lang of ['zh', 'th', 'en', 'ja']) {
        const errors = await bootShell(page, lang);
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
        expect(errors, errors.join('\n')).toEqual([]);
    }
    expect(seen.zh).not.toContain('订车');
    expect(seen.th).not.toContain('ใบจอง');
    expect(seen.en.toLowerCase()).not.toContain('booking');
    expect(seen.ja).not.toContain('予約');
});

test('P1-12 · 选车面板过期屏四语给出可执行指路(且说明不必重拍身份证)', async ({ page }) => {
    await page.route('**/api/dms/pick/**', (route) =>
        route.fulfill({
            status: 401,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'dms_pick.expired' }),
        })
    );
    const seen = {};
    for (const lang of ['th', 'zh', 'en', 'ja']) {
        await setLang(page, lang);
        await page.goto(`${BASE}/static/dist/dms-pick.html?t=expired`);
        await page.waitForSelector('.state.err');
        seen[lang] = await page.locator('.state.err').innerText();
        await page.screenshot({ path: path.join(OUT, `web-pick-expired-${lang}.png`) });
    }
    // 泰语是真实用户读的那版:得说清回 LINE 打什么词,以及不必重拍身份证(重拍要再扣一次 OCR 费)。
    expect(seen.th).toMatch(/เมนู/);
    expect(seen.th).toMatch(/ไม่ต้อง.*บัตร|บัตรประชาชนซ้ำ/);
    expect(seen.zh).toMatch(/不必|无需/);
});
