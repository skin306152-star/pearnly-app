// /ai 四条缺口复验 · 真浏览器 + 真后端(127.0.0.1:7860)+ 真库(docker pearnly-db)
// ============================================================
// 真登录(stw_e2e / entry=ai)、真客户、真工单详情;只有「制造失败」这一件事用 page.route,
// 且注入的 status/响应体全部先用 curl 打真后端取回来过:
//   401 → {"detail":"auth.invalid_token"}            (真机实测)
//   404 → {"detail":"workorder.not_found"}           (真机实测 · routes/workorder_routes.py:85)
//   402 → {"detail":{"code":"insufficient_balance",...}}(services/billing 统一码 ·
//          routes/recon_jobs_routes.py:_credits_precheck 的原样形状)
//   500 → {"detail":"Internal Server Error"}          (FastAPI 默认体)
//   网络断 → route.abort('failed')
// 截图存 tests/e2e/_artifacts/ai_gaps/,命名 NN-场景-语言-视口.png。
//
// 起法:PEARNLY_E2E_BASE_URL=http://127.0.0.1:7860 npx playwright test tests/e2e/_ai_gaps_verify.spec.js
/* global window, document, getComputedStyle */

const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const BASE = process.env.PEARNLY_E2E_BASE_URL || 'http://127.0.0.1:7860';
const USER = 'stw_e2e';
const PASS = 'StwVerify#2026';
const ART = path.join(__dirname, '_artifacts', 'ai_gaps');
const EVID = path.join(ART, 'evidence.json');

// 本机真栈专用:登录号 stw_e2e 只存在于本地 docker 库,CI 打的是 pearnly.com —— 那边不认
// 这个号,beforeAll 必红在 401(且五个同类脚本连打会把生产登录口的限流打到 429)。
// 本机跑法:PEARNLY_E2E_LOCAL=1 PEARNLY_E2E_BASE_URL=http://127.0.0.1:7860 npx playwright test tests/e2e/_ai_gaps_verify.spec.js
test.skip(process.env.PEARNLY_E2E_LOCAL !== '1', '需本机真栈(PEARNLY_E2E_LOCAL=1)');

// 真库里的客户(beforeAll 按真接口挑,不写死 id):零工单的那个走空态/开单失败,
// 有工单的那个走收料上传失败。
let CLIENT_NO_ORDER = null;
let CLIENT_WITH_ORDER = null;
let ORDER_ID = null;
let TOKEN = '';

fs.mkdirSync(ART, { recursive: true });
let evidence = {};
try {
    evidence = JSON.parse(fs.readFileSync(EVID, 'utf8'));
} catch (e) {
    evidence = {};
}
function record(k, v) {
    evidence[k] = v;
    fs.writeFileSync(EVID, JSON.stringify(evidence, null, 2), 'utf8');
}

const DESKTOP = { width: 1280, height: 900 };
const MOBILE = { width: 390, height: 844 };

test.beforeAll(async ({ request }) => {
    const r = await request.post(`${BASE}/api/login`, {
        data: { username: USER, password: PASS, entry: 'ai' },
    });
    expect(r.status()).toBe(200);
    TOKEN = (await r.json()).token;
    expect(TOKEN.length).toBeGreaterThan(20);

    const cs = await (
        await request.get(`${BASE}/api/workspace/clients`, {
            headers: { Authorization: 'Bearer ' + TOKEN },
        })
    ).json();
    for (const c of cs.clients) {
        const o = await (
            await request.get(`${BASE}/api/workorder/orders?client_id=${c.id}`, {
                headers: { Authorization: 'Bearer ' + TOKEN },
            })
        ).json();
        const n = (o.orders || []).length;
        if (n === 0 && CLIENT_NO_ORDER == null) CLIENT_NO_ORDER = c.id;
        if (n > 0 && CLIENT_WITH_ORDER == null) {
            CLIENT_WITH_ORDER = c.id;
            ORDER_ID = o.orders[0].id;
        }
    }
    record('fixtures', {
        clientNoOrder: CLIENT_NO_ORDER,
        clientWithOrder: CLIENT_WITH_ORDER,
        orderId: ORDER_ID,
    });
    expect(CLIENT_NO_ORDER).not.toBeNull();
    expect(CLIENT_WITH_ORDER).not.toBeNull();
});

// 真登录态开页。viewport 必须在 goto 之前设(移动端布局是首屏算的)。
async function open(page, opts) {
    opts = opts || {};
    const errs = [];
    page.on('console', (m) => {
        if (m.type() === 'error') errs.push(m.text());
    });
    page.on('pageerror', (e) => errs.push('pageerror: ' + e.message));
    await page.setViewportSize(opts.viewport || DESKTOP);
    await page.addInitScript(
        ([t, l]) => {
            window.localStorage.setItem('mrpilot_token_ai', t);
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [TOKEN, opts.lang || 'zh']
    );
    await page.goto(`${BASE}/ai${opts.hash || ''}`, { waitUntil: 'domcontentloaded' });
    return errs;
}

// 只截停「开单」这一条 POST,其余 /api/** 照打真后端。
async function failCreateOrder(page, mode) {
    await page.route(
        (u) => u.pathname === '/api/workorder/orders',
        (r) => {
            if (r.request().method() !== 'POST') return r.fallback();
            if (mode.abort) return r.abort('failed');
            return r.fulfill({
                status: mode.status,
                contentType: 'application/json',
                body: JSON.stringify({ detail: mode.detail }),
            });
        }
    );
}

async function shot(page, name) {
    await page.screenshot({ path: path.join(ART, name), fullPage: true });
    return name;
}

const SHOTS = [];
function took(n) {
    SHOTS.push(n);
    return n;
}

// ─────────────────────────────────────────────────────────────
// 场景 1 · 开当期工单失败 → 有明确反应 · 按钮可再点 · 原因说得清
// ─────────────────────────────────────────────────────────────
test.describe('场景1 · 开当期工单失败四类各说各的', () => {
    const CASES = [
        {
            key: 'server',
            mode: { status: 500, detail: 'Internal Server Error' },
            want: '服务器出错了',
        },
        { key: 'network', mode: { abort: true }, want: '请求没发出去' },
        { key: 'auth', mode: { status: 401, detail: 'auth.invalid_token' }, want: '登录已过期' },
        {
            key: 'noaccess',
            mode: { status: 404, detail: 'workorder.not_found' },
            want: '不在你的可见范围',
        },
    ];

    CASES.forEach((c, i) => {
        test(`开单失败 ${c.key} → 就地红徽章 + 按钮回可点`, async ({ page }) => {
            test.setTimeout(90000);
            const errs = await open(page, { hash: `#/client/${CLIENT_NO_ORDER}/wo` });
            await failCreateOrder(page, c.mode);
            const btn = page.locator('[data-action="wo-open-first"]');
            await page.waitForSelector('[data-action="wo-open-first"]', {
                state: 'visible',
                timeout: 30000,
            });
            const idleLabel = (await btn.innerText()).trim();
            await btn.click();

            const note = page.locator('.order-open-empty [data-fail-slot] [role="alert"]');
            await page.waitForSelector('.order-open-empty [data-fail-slot] [role="alert"]', {
                state: 'visible',
                timeout: 20000,
            });
            await expect(note.locator('.st-badge.st-err')).toHaveText('开单没成功');
            await expect(note).toContainText(c.want);
            await expect(btn).toBeEnabled();
            expect((await btn.innerText()).trim()).toBe(idleLabel);

            // 对齐:说明位与账期表单同轴同宽(不是孤零零贴卡片左边缘)。
            const geo = await page.evaluate(() => {
                const f = document.querySelector('.order-open-empty .order-open-form');
                const s = document.querySelector('.order-open-empty [data-fail-slot]');
                const fr = f.getBoundingClientRect();
                const sr = s.getBoundingClientRect();
                return {
                    formLeft: fr.left,
                    slotLeft: sr.left,
                    formWidth: fr.width,
                    slotWidth: sr.width,
                    slotBelowForm: sr.top >= fr.bottom - 1,
                    docOverflow: document.documentElement.scrollWidth - window.innerWidth,
                };
            });
            expect(Math.abs(geo.slotLeft - geo.formLeft)).toBeLessThan(2);
            expect(Math.abs(geo.slotWidth - geo.formWidth)).toBeLessThan(2);
            expect(geo.slotBelowForm).toBe(true);
            expect(geo.docOverflow).toBeLessThanOrEqual(0);

            record(`s1_${c.key}`, {
                badge: await note.locator('.st-badge.st-err').innerText(),
                text: (await note.innerText()).trim(),
                idleLabel,
                geo,
                consoleErrors: errs,
            });
            took(await shot(page, `0${i + 1}-openorder-${c.key}-zh-desktop.png`));
        });
    });

    test('开单失败 · 泰语说的是泰语(不落 key 字面量)', async ({ page }) => {
        test.setTimeout(90000);
        const errs = await open(page, { hash: `#/client/${CLIENT_NO_ORDER}/wo`, lang: 'th' });
        await failCreateOrder(page, { status: 500, detail: 'Internal Server Error' });
        await page.waitForSelector('[data-action="wo-open-first"]', {
            state: 'visible',
            timeout: 30000,
        });
        await page.locator('[data-action="wo-open-first"]').click();
        await page.waitForSelector('.order-open-empty [data-fail-slot] [role="alert"]', {
            state: 'visible',
            timeout: 20000,
        });
        const note = page.locator('.order-open-empty [data-fail-slot] [role="alert"]');
        await expect(note.locator('.st-badge.st-err')).toHaveText('เปิดใบงานไม่สำเร็จ');
        await expect(note).toContainText('เซิร์ฟเวอร์ขัดข้อง');
        await expect(note).not.toContainText('fail_server');
        record('s1_th', { text: (await note.innerText()).trim(), consoleErrors: errs });
        took(await shot(page, '05-openorder-server-th-desktop.png'));
    });

    test('开单失败 · 再点一次先清掉上一次的说明(不叠一堆红字)', async ({ page }) => {
        test.setTimeout(90000);
        await open(page, { hash: `#/client/${CLIENT_NO_ORDER}/wo` });
        await failCreateOrder(page, { status: 500, detail: 'Internal Server Error' });
        await page.waitForSelector('[data-action="wo-open-first"]', {
            state: 'visible',
            timeout: 30000,
        });
        const btn = page.locator('[data-action="wo-open-first"]');
        await btn.click();
        await page.waitForSelector('.order-open-empty [data-fail-slot] [role="alert"]', {
            state: 'visible',
            timeout: 20000,
        });
        await btn.click();
        await page.waitForSelector('.order-open-empty [data-fail-slot] [role="alert"]', {
            state: 'visible',
            timeout: 20000,
        });
        const n = await page.locator('.order-open-empty [data-fail-slot] [role="alert"]').count();
        record('s1_reclick', { alertCount: n });
        expect(n).toBe(1);
        took(await shot(page, '06-openorder-reclick-zh-desktop.png'));
    });

    test('开单失败 · 移动端 390 不出界', async ({ page }) => {
        test.setTimeout(90000);
        await open(page, { hash: `#/client/${CLIENT_NO_ORDER}/wo`, viewport: MOBILE });
        await failCreateOrder(page, { status: 401, detail: 'auth.invalid_token' });
        await page.waitForSelector('[data-action="wo-open-first"]', {
            state: 'visible',
            timeout: 30000,
        });
        await page.locator('[data-action="wo-open-first"]').click();
        await page.waitForSelector('.order-open-empty [data-fail-slot] [role="alert"]', {
            state: 'visible',
            timeout: 20000,
        });
        const geo = await page.evaluate(() => ({
            overflow: document.documentElement.scrollWidth - window.innerWidth,
            slotRight: document
                .querySelector('.order-open-empty [data-fail-slot]')
                .getBoundingClientRect().right,
            vw: window.innerWidth,
        }));
        record('s1_mobile', geo);
        expect(geo.overflow).toBeLessThanOrEqual(0);
        expect(geo.slotRight).toBeLessThanOrEqual(geo.vw);
        took(await shot(page, '07-openorder-auth-zh-mobile.png'));
    });
});

// ─────────────────────────────────────────────────────────────
// 场景 2 · 余额不足上传失败 → 人话原因 + 「去充值」出路 · 点它真落到计费区
// ─────────────────────────────────────────────────────────────
const BALANCE_402 = {
    status: 402,
    contentType: 'application/json',
    body: JSON.stringify({
        detail: {
            code: 'insufficient_balance',
            balance: 0.0,
            estimated_cost: 4.5,
            pages_used_this_month: 0,
        },
    }),
};

async function uploadOneFile(page) {
    await page.waitForSelector('#ikFileInput', { state: 'attached', timeout: 30000 });
    await page.locator('#ikFileInput').setInputFiles({
        name: 'bill.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('%PDF-1.4 gapverify'),
    });
    await page.waitForSelector('[data-action="ik-upload"]', { state: 'visible', timeout: 20000 });
    await page.locator('[data-action="ik-upload"]').click();
}

test.describe('场景2 · 上传失败说清原因并给去充值的出路', () => {
    test('402 余额不足 → 原因 + 计数不撒谎 + 「去充值」直达计费区', async ({ page }) => {
        test.setTimeout(120000);
        const errs = await open(page, { hash: `#/client/${CLIENT_WITH_ORDER}/intake` });
        await page.route('**/materials', (r) => r.fulfill(BALANCE_402));
        await uploadOneFile(page);

        await page.waitForSelector('.needs-card [role="alert"]', {
            state: 'visible',
            timeout: 30000,
        });
        const card = page.locator('.needs-card').first();
        const alert = card.locator('[role="alert"]');
        await expect(alert.locator('.st-badge.st-err')).toHaveText('这些文件没传上去');
        await expect(alert).toContainText('OCR 余额不足');
        // 计数行不再对 402 撒谎说是网络问题。
        const cardText = (await card.innerText()).trim();
        expect(cardText).toContain('共 1 件没传成功');
        expect(cardText).not.toContain('因网络问题');
        await expect(card.locator('[data-action="ik-retry-failed"]')).toBeVisible();
        const topup = card.locator('.needs-paths a.btn.pri');
        await expect(topup).toHaveText('去充值');
        expect(await topup.getAttribute('href')).toBe('#/settings?focus=billing');
        record('s2_402', { cardText, consoleErrors: errs });
        took(await shot(page, '08-upload-402-zh-desktop.png'));

        await topup.click();
        await page.waitForSelector('#stBillingWrap', { state: 'visible', timeout: 30000 });
        // 「到了设置页」不算数,得真落在视口里看得见充值。
        const inView = await page.locator('#stBillingWrap').evaluate((el) => {
            const r = el.getBoundingClientRect();
            return {
                top: r.top,
                bottom: r.bottom,
                vh: window.innerHeight,
                visible: r.top < window.innerHeight && r.bottom > 0,
            };
        });
        record('s2_topup_landing', { url: page.url(), rect: inView });
        expect(page.url()).toContain('#/settings?focus=billing');
        expect(inView.visible).toBe(true);
        took(await shot(page, '09-topup-landing-zh-desktop.png'));
    });

    test('402 余额不足 · 泰语两行都出泰文', async ({ page }) => {
        test.setTimeout(120000);
        await open(page, { hash: `#/client/${CLIENT_WITH_ORDER}/intake`, lang: 'th' });
        await page.route('**/materials', (r) => r.fulfill(BALANCE_402));
        await uploadOneFile(page);
        await page.waitForSelector('.needs-card [role="alert"]', {
            state: 'visible',
            timeout: 30000,
        });
        const card = page.locator('.needs-card').first();
        await expect(card.locator('[role="alert"] .st-badge.st-err')).toHaveText(
            'ไฟล์เหล่านี้อัปโหลดไม่สำเร็จ'
        );
        await expect(card.locator('[role="alert"]')).toContainText('เครดิต OCR ไม่พอ');
        await expect(card.locator('.needs-paths a.btn.pri')).toHaveText('ไปเติมเงิน');
        record('s2_th', { cardText: (await card.innerText()).trim() });
        took(await shot(page, '10-upload-402-th-desktop.png'));
    });

    test('500 服务端出错 → 说服务器不说网络 · 且绝不出「去充值」', async ({ page }) => {
        test.setTimeout(120000);
        await open(page, { hash: `#/client/${CLIENT_WITH_ORDER}/intake` });
        await page.route('**/materials', (r) =>
            r.fulfill({
                status: 500,
                contentType: 'application/json',
                body: JSON.stringify({ detail: 'Internal Server Error' }),
            })
        );
        await uploadOneFile(page);
        await page.waitForSelector('.needs-card [role="alert"]', {
            state: 'visible',
            timeout: 30000,
        });
        const card = page.locator('.needs-card').first();
        const txt = (await card.innerText()).trim();
        expect(txt).toContain('服务器出错了');
        expect(txt).not.toContain('因网络问题');
        expect(await card.locator('.needs-paths a.btn.pri').count()).toBe(0);
        record('s2_500', { cardText: txt });
        took(await shot(page, '11-upload-500-zh-desktop.png'));
    });

    test('402 余额不足 · 移动端 390 按钮不出界', async ({ page }) => {
        test.setTimeout(120000);
        await open(page, { hash: `#/client/${CLIENT_WITH_ORDER}/intake`, viewport: MOBILE });
        await page.route('**/materials', (r) => r.fulfill(BALANCE_402));
        await uploadOneFile(page);
        await page.waitForSelector('.needs-card [role="alert"]', {
            state: 'visible',
            timeout: 30000,
        });
        const geo = await page.evaluate(() => {
            const a = document.querySelector('.needs-card .needs-paths a.btn.pri');
            const r = a.getBoundingClientRect();
            return {
                overflow: document.documentElement.scrollWidth - window.innerWidth,
                right: r.right,
                left: r.left,
                vw: window.innerWidth,
            };
        });
        record('s2_mobile', geo);
        expect(geo.overflow).toBeLessThanOrEqual(0);
        expect(geo.right).toBeLessThanOrEqual(geo.vw);
        expect(geo.left).toBeGreaterThanOrEqual(0);
        took(await shot(page, '12-upload-402-zh-mobile.png'));
    });
});

// ─────────────────────────────────────────────────────────────
// 场景 3 · 审核/交付包空态点名去哪 + 有按钮 · 点了真跳(零 stub · 真库零工单客户)
// ─────────────────────────────────────────────────────────────
test.describe('场景3 · 审核/交付包空态给出路(真数据零 stub)', () => {
    for (const tab of ['review', 'pkg']) {
        test(`${tab} 空态点名「工单」tab 且按钮真跳过去`, async ({ page }) => {
            test.setTimeout(90000);
            const errs = await open(page, { hash: `#/client/${CLIENT_NO_ORDER}/${tab}` });
            await page.waitForSelector(`#cv-${tab} .state-block`, {
                state: 'visible',
                timeout: 30000,
            });
            const block = page.locator(`#cv-${tab} .state-block`);
            await expect(block.locator('.t')).toHaveText('这个客户还没有工单');
            await expect(block.locator('.s')).toContainText('「工单」tab');
            const btn = block.locator('a.btn');
            await expect(btn).toBeVisible();
            expect(await btn.getAttribute('href')).toBe(`#/client/${CLIENT_NO_ORDER}/wo`);
            record(`s3_${tab}`, {
                title: await block.locator('.t').innerText(),
                sub: await block.locator('.s').innerText(),
                btn: await btn.innerText(),
                consoleErrors: errs,
            });
            took(await shot(page, `1${tab === 'review' ? 3 : 4}-${tab}-noorder-zh-desktop.png`));

            await btn.click();
            await page.waitForSelector('#cv-wo.on', { state: 'visible', timeout: 20000 });
            expect(page.url()).toContain(`#/client/${CLIENT_NO_ORDER}/wo`);
            // 跳过去落在真能开单的那张卡上,不是又一个死胡同。
            await page.waitForSelector('[data-action="wo-open-first"]', {
                state: 'visible',
                timeout: 20000,
            });
        });
    }

    test('审核空态 · 泰语点名 «งาน» 且不落 key 字面量', async ({ page }) => {
        test.setTimeout(90000);
        await open(page, { hash: `#/client/${CLIENT_NO_ORDER}/review`, lang: 'th' });
        await page.waitForSelector('#cv-review .state-block .s', {
            state: 'visible',
            timeout: 30000,
        });
        const sub = page.locator('#cv-review .state-block .s');
        await expect(sub).toContainText('«งาน»');
        await expect(sub).not.toContainText('emp_wo_none');
        await expect(page.locator('#cv-review .state-block a.btn')).toContainText('«งาน»');
        record('s3_th', { sub: await sub.innerText() });
        took(await shot(page, '15-review-noorder-th-desktop.png'));
    });

    test('审核空态 · 移动端 390 不出界', async ({ page }) => {
        test.setTimeout(90000);
        await open(page, { hash: `#/client/${CLIENT_NO_ORDER}/review`, viewport: MOBILE });
        await page.waitForSelector('#cv-review .state-block a.btn', {
            state: 'visible',
            timeout: 30000,
        });
        const geo = await page.evaluate(() => {
            const r = document
                .querySelector('#cv-review .state-block a.btn')
                .getBoundingClientRect();
            return {
                overflow: document.documentElement.scrollWidth - window.innerWidth,
                right: r.right,
                left: r.left,
                vw: window.innerWidth,
            };
        });
        record('s3_mobile', geo);
        expect(geo.overflow).toBeLessThanOrEqual(0);
        expect(geo.right).toBeLessThanOrEqual(geo.vw);
        took(await shot(page, '16-review-noorder-zh-mobile.png'));
    });
});

// ─────────────────────────────────────────────────────────────
// 场景 4 · 页内分区三态可分辨(idle / empty / error)
// 工单详情的形状取自真接口(GET /api/workorder/orders/{id} 的真响应键集),
// 只把 bank_recon 的内容换成三种真实会出现的情形。
// ─────────────────────────────────────────────────────────────
function detailFrom(real, over) {
    return Object.assign({}, real, over);
}

async function bootOrderDetail(page, over, opts) {
    opts = opts || {};
    const real = await (
        await page.request.get(`${BASE}/api/workorder/orders/${ORDER_ID}`, {
            headers: { Authorization: 'Bearer ' + TOKEN },
        })
    ).json();
    const body = JSON.stringify(detailFrom(real, over));
    await page.route(`**/api/workorder/orders/${ORDER_ID}`, (r) =>
        r.fulfill({ contentType: 'application/json', body })
    );
    await open(page, {
        hash: `#/client/${CLIENT_WITH_ORDER}/wo`,
        lang: opts.lang || 'zh',
        viewport: opts.viewport,
    });
    await page.waitForSelector('#brxRoot .panel', { state: 'visible', timeout: 30000 });
    return real;
}

const EMPTY_RECON = {
    auto_matched: [],
    review: [],
    missing_invoice: [],
    unmatched_invoice: [],
    bank_item_ids: [],
    diff: { net: '0' },
};

test.describe('场景4 · 分区空态三态可分辨', () => {
    test('idle · 跑完但没料 → 说清为什么空 + 给去收料的按钮', async ({ page }) => {
        test.setTimeout(90000);
        await bootOrderDetail(page, { bank_recon: EMPTY_RECON, status: 'review' });
        const empty = page.locator('#brxRoot .sec-empty');
        await expect(empty).toHaveCount(1);
        expect(await empty.getAttribute('data-state')).toBe('idle');
        await expect(empty.locator('.sec-empty-t')).toHaveText('这期没有可对账的东西');
        const why = (await empty.locator('.sec-empty-s').innerText()).trim();
        expect(why.length).toBeGreaterThan(20);
        const out = empty.locator('.sec-empty-a a.btn');
        expect(await out.getAttribute('href')).toBe(`#/client/${CLIENT_WITH_ORDER}/intake`);
        record('s4_idle', { why, btn: await out.innerText() });
        took(await shot(page, '17-tristate-idle-zh-desktop.png'));
    });

    test('empty · 跑完真没这一类 → data-state 与左色条都跟 idle 不同', async ({ page }) => {
        test.setTimeout(90000);
        const recon = Object.assign({}, EMPTY_RECON, {
            unmatched_invoice: [
                { vendor: 'A', invoice_no: 'INV-1', amount: '100', candidate_id: 'c1' },
            ],
        });
        await bootOrderDetail(page, { bank_recon: recon, status: 'review' });
        const miss = page.locator('#brxRoot [data-brx-kind="missing"] .sec-empty');
        await page.waitForSelector('#brxRoot [data-brx-kind="missing"] .sec-empty', {
            state: 'visible',
            timeout: 20000,
        });
        expect(await miss.getAttribute('data-state')).toBe('empty');
        await expect(miss.locator('.sec-empty-s')).toContainText('对应票据');
        const bars = await page.evaluate(() => {
            const el = document.querySelector('#brxRoot [data-brx-kind="missing"] .sec-empty');
            const emptyBar = getComputedStyle(el).borderLeftColor;
            const probe = document.createElement('div');
            probe.className = 'sec-empty sec-empty-idle';
            document.body.appendChild(probe);
            const idleBar = getComputedStyle(probe).borderLeftColor;
            probe.className = 'sec-empty sec-empty-error';
            const errBar = getComputedStyle(probe).borderLeftColor;
            probe.remove();
            return { emptyBar, idleBar, errBar };
        });
        record('s4_empty', bars);
        expect(bars.emptyBar).not.toBe(bars.idleBar);
        expect(bars.emptyBar).not.toBe(bars.errBar);
        expect(bars.idleBar).not.toBe(bars.errBar);
        took(await shot(page, '18-tristate-empty-zh-desktop.png'));
    });

    test('error · 后台停住了 → 改口说没跑出来 + 给断点重试 · 三块面板口径一致', async ({
        page,
    }) => {
        test.setTimeout(90000);
        await bootOrderDetail(page, {
            status: 'stuck',
            blocked_reasons: ['ocr_timeout'],
            bank_recon: null,
            shadow_draft: null,
            financials: null,
        });
        const brx = page.locator('#brxRoot .sec-empty');
        expect(await brx.getAttribute('data-state')).toBe('error');
        await expect(brx.locator('.sec-empty-t')).toHaveText('对账这步没跑出来');
        await expect(brx.locator('button[data-action="wo-retry-stuck"]')).toBeVisible();
        await expect(page.locator('#brxRoot')).not.toContainText('不用管它');
        const sdw = page.locator('#shadowRoot .sec-empty');
        expect(await sdw.getAttribute('data-state')).toBe('error');
        const fin = page.locator('#financialsRoot .sec-empty');
        expect(await fin.getAttribute('data-state')).toBe('error');
        await expect(page.locator('#financialsRoot')).not.toContainText('不用管它');
        record('s4_error', {
            brx: (await brx.innerText()).trim(),
            sdw: (await sdw.innerText()).trim(),
            fin: (await fin.innerText()).trim(),
        });
        took(await shot(page, '19-tristate-error-zh-desktop.png'));
    });

    test('error · 泰语三块面板都出泰文', async ({ page }) => {
        test.setTimeout(90000);
        await bootOrderDetail(
            page,
            {
                status: 'stuck',
                blocked_reasons: ['ocr_timeout'],
                bank_recon: null,
                shadow_draft: null,
                financials: null,
            },
            { lang: 'th' }
        );
        await expect(page.locator('#brxRoot .sec-empty .sec-empty-t')).toHaveText(
            'ขั้นตอนกระทบยอดยังไม่ได้ผลลัพธ์'
        );
        await expect(page.locator('#shadowRoot .sec-empty .sec-empty-t')).toHaveText(
            'ยังไม่ได้สร้างร่างบัญชีเงา'
        );
        await expect(page.locator('#financialsRoot .sec-empty .sec-empty-t')).toHaveText(
            'ยังไม่ได้สร้างชุดรายงาน'
        );
        took(await shot(page, '20-tristate-error-th-desktop.png'));
    });

    test('真库里 status=stuck 但 blocked_reasons 为空的单 → 现在说的是什么', async ({ page }) => {
        test.setTimeout(90000);
        // 零 stub:真库当前 7 张单全是 blocked_reasons=[],看看三态在真数据上到底落哪一态。
        const real = await (
            await page.request.get(`${BASE}/api/workorder/orders/${ORDER_ID}`, {
                headers: { Authorization: 'Bearer ' + TOKEN },
            })
        ).json();
        await open(page, { hash: `#/client/${CLIENT_WITH_ORDER}/wo` });
        await page.waitForSelector('#brxRoot .panel', { state: 'visible', timeout: 30000 });
        const observed = await page.evaluate(() => {
            const pick = (id) => {
                const root = document.getElementById(id);
                if (!root) return null;
                const sec = root.querySelector('.sec-empty');
                const blk = root.querySelector('.state-block');
                const el = sec || blk;
                return el
                    ? { state: el.getAttribute('data-state'), text: el.innerText.trim() }
                    : { state: null, text: root.innerText.trim().slice(0, 200) };
            };
            return {
                brx: pick('brxRoot'),
                sdw: pick('shadowRoot'),
                fin: pick('financialsRoot'),
            };
        });
        record('s4_realdata', {
            orderStatus: real.status,
            blocked_reasons: real.blocked_reasons,
            observed,
        });
        took(await shot(page, '21-tristate-realdata-zh-desktop.png'));
        // 只取证不判红:真数据落哪一态由 defects 定夺。
        expect(observed.brx).not.toBeNull();
    });

    test('error · 移动端 390 不出界', async ({ page }) => {
        test.setTimeout(90000);
        await bootOrderDetail(
            page,
            {
                status: 'stuck',
                blocked_reasons: ['ocr_timeout'],
                bank_recon: null,
                shadow_draft: null,
                financials: null,
            },
            { viewport: MOBILE }
        );
        const geo = await page.evaluate(() => {
            const r = document
                .querySelector('#brxRoot .sec-empty button[data-action="wo-retry-stuck"]')
                .getBoundingClientRect();
            return {
                overflow: document.documentElement.scrollWidth - window.innerWidth,
                right: r.right,
                vw: window.innerWidth,
            };
        });
        record('s4_mobile', geo);
        expect(geo.overflow).toBeLessThanOrEqual(0);
        expect(geo.right).toBeLessThanOrEqual(geo.vw);
        took(await shot(page, '22-tristate-error-zh-mobile.png'));
    });
});

// ─────────────────────────────────────────────────────────────
// 补验 · 目检时看到的三处可疑点,量出来当证据(只取证,判定写 defects)
// ─────────────────────────────────────────────────────────────
test.describe('补验 · 目检疑点取证', () => {
    test('真数据对账空态的「去收料」是裸链接不是设计系统按钮', async ({ page }) => {
        test.setTimeout(90000);
        await open(page, { hash: `#/client/${CLIENT_WITH_ORDER}/wo` });
        await page.waitForSelector('#brxRoot .panel', { state: 'visible', timeout: 30000 });
        const probe = await page.evaluate(() => {
            const link = document.querySelector('#brxRoot .note a');
            if (!link) return null;
            const btn = document.querySelector('#cv-wo .btn.pri, .btn.pri');
            const cs = getComputedStyle(link);
            return {
                text: link.textContent.trim(),
                className: link.className,
                color: cs.color,
                textDecoration: cs.textDecorationLine,
                background: cs.backgroundColor,
                anyBtnClassOnPage: !!btn,
            };
        });
        record('probe_bare_link', probe);
        took(await shot(page, '23-recon-barelink-zh-desktop.png'));
        expect(probe).not.toBeNull();
    });

    test('去充值深链在真会滚动的视口(390)里是否真滚到计费区', async ({ page }) => {
        test.setTimeout(120000);
        await open(page, { hash: `#/client/${CLIENT_WITH_ORDER}/intake`, viewport: MOBILE });
        await page.route('**/materials', (r) => r.fulfill(BALANCE_402));
        await uploadOneFile(page);
        await page.waitForSelector('.needs-card .needs-paths a.btn.pri', {
            state: 'visible',
            timeout: 30000,
        });
        await page.locator('.needs-card .needs-paths a.btn.pri').click();
        await page.waitForSelector('#stBillingWrap', { state: 'visible', timeout: 30000 });
        // 计费区自带轮询/异步:先等它出真内容,再量位置(骨架期量到的是假位置)。
        await page
            .waitForFunction(
                () => {
                    const w = document.getElementById('stBillingWrap');
                    return w && !w.querySelector('[data-state="loading"]');
                },
                null,
                { timeout: 20000 }
            )
            .catch(() => {});
        // 真内容落下来才把页面撑出滚动条,补滚是内容之后的一次异步重试(ai-settings.js
        // FOCUS_RETRY_MS)。骨架一消失就量 = 量在补滚之前,读到的是假的 0。
        await expect
            .poll(() => page.evaluate(() => window.scrollY), { timeout: 10000 })
            .toBeGreaterThan(0);
        const geo = await page.evaluate(() => {
            const w = document.getElementById('stBillingWrap');
            const r = w.getBoundingClientRect();
            return {
                top: r.top,
                bottom: r.bottom,
                height: r.height,
                vh: window.innerHeight,
                scrollY: window.scrollY,
                docHeight: document.documentElement.scrollHeight,
                stillSkeleton: !!w.querySelector('[data-state="loading"]'),
                inViewport: r.top < window.innerHeight && r.bottom > 0,
                fullyInViewport: r.top >= 0 && r.bottom <= window.innerHeight,
            };
        });
        record('probe_topup_mobile', geo);
        took(await shot(page, '24-topup-landing-zh-mobile.png'));
        // D1 修复后的真判据:计费区挂载时页面还撑不出滚动条,scrollIntoView 被 clamp 成
        // no-op;补滚生效才会有位移。只判 inViewport 是恒真断言(桌面整页 fit 更是假绿)。
        expect(geo.docHeight).toBeGreaterThan(geo.vh);
        expect(geo.scrollY).toBeGreaterThan(0);
        expect(geo.inViewport).toBe(true);
    });

    test('去充值深链 · 落地瞬间 vs 内容载完后的滚动位(找为什么没滚)', async ({ page }) => {
        test.setTimeout(120000);
        await open(page, { hash: `#/client/${CLIENT_WITH_ORDER}/intake`, viewport: MOBILE });
        await page.route('**/materials', (r) => r.fulfill(BALANCE_402));
        await uploadOneFile(page);
        await page.waitForSelector('.needs-card .needs-paths a.btn.pri', {
            state: 'visible',
            timeout: 30000,
        });
        await page.locator('.needs-card .needs-paths a.btn.pri').click();
        await page.waitForSelector('#stBillingWrap', { state: 'visible', timeout: 30000 });
        const atLanding = await page.evaluate(() => ({
            scrollY: window.scrollY,
            docHeight: document.documentElement.scrollHeight,
            vh: window.innerHeight,
            wrapHeight: document.getElementById('stBillingWrap').getBoundingClientRect().height,
            skeleton: !!document.querySelector('#stBillingWrap [data-state="loading"]'),
        }));
        await page.waitForTimeout(3000);
        const settled = await page.evaluate(() => {
            const r = document.getElementById('stBillingWrap').getBoundingClientRect();
            return {
                scrollY: window.scrollY,
                docHeight: document.documentElement.scrollHeight,
                vh: window.innerHeight,
                wrapHeight: r.height,
                wrapTop: r.top,
                wrapBottom: r.bottom,
                skeleton: !!document.querySelector('#stBillingWrap [data-state="loading"]'),
                fullyInViewport: r.top >= 0 && r.bottom <= window.innerHeight,
            };
        });
        // 出路的落点不是「计费区这个盒子」,是那颗「充值」按钮——它在不在视口里才算数。
        const btn = await page.evaluate(() => {
            const b = document.querySelector('[data-action="bill-topup"]');
            if (!b) return { found: false };
            const r = b.getBoundingClientRect();
            return {
                found: true,
                text: b.textContent.trim(),
                top: r.top,
                bottom: r.bottom,
                vh: window.innerHeight,
                fullyVisible: r.top >= 0 && r.bottom <= window.innerHeight,
            };
        });
        record('probe_topup_scroll_timing', {
            atLanding: atLanding,
            settled: settled,
            topupButton: btn,
        });
        took(await shot(page, '26-topup-landing-settled-zh-mobile.png'));
        // 出路的落点是那颗按钮:整颗在视口内才算「落地就看得见充值」。
        // (D1 之前:atLanding.scrollY=0 且 3 秒后仍是 0,按钮被折线切掉一半。)
        expect(btn.found).toBe(true);
        expect(settled.scrollY).toBeGreaterThan(0);
        expect(btn.fullyVisible).toBe(true);
    });

    // 分片只写了 zh+th,en/ja 靠 at() 回落 zh。回落断了就会漏 fail_*/emp_* 原始 key 到界面上。
    for (const lang of ['en', 'ja']) {
        test(`${lang} 回落不漏 key 字面量(开单失败 + 空态)`, async ({ page }) => {
            test.setTimeout(90000);
            await open(page, { hash: `#/client/${CLIENT_NO_ORDER}/wo`, lang: lang });
            await failCreateOrder(page, { status: 402, detail: { code: 'insufficient_balance' } });
            await page.waitForSelector('[data-action="wo-open-first"]', {
                state: 'visible',
                timeout: 30000,
            });
            await page.locator('[data-action="wo-open-first"]').click();
            await page.waitForSelector('.order-open-empty [data-fail-slot] [role="alert"]', {
                state: 'visible',
                timeout: 20000,
            });
            const txt = (await page.locator('.order-open-empty').innerText()).trim();
            record(`probe_fallback_${lang}`, { text: txt });
            took(await shot(page, `2${lang === 'en' ? 7 : 8}-openorder-402-${lang}-desktop.png`));
            expect(txt).not.toMatch(/fail_(network|auth|server|no_access|credits|topup|step)/);
            expect(txt).not.toMatch(/emp_wo_/);
        });
    }

    test('移动端收料区的文件行与拖拽区文案是否重叠', async ({ page }) => {
        test.setTimeout(120000);
        await open(page, { hash: `#/client/${CLIENT_WITH_ORDER}/intake`, viewport: MOBILE });
        await page.route('**/materials', (r) => r.fulfill(BALANCE_402));
        await uploadOneFile(page);
        await page.waitForSelector('.needs-card [role="alert"]', {
            state: 'visible',
            timeout: 30000,
        });
        const overlap = await page.evaluate(() => {
            const zone = document.querySelector('.ik-drop, [class*="drop"]');
            if (!zone) return { found: false };
            const rows = Array.from(zone.querySelectorAll('*')).filter(
                (e) => e.children.length === 0 && e.textContent.trim() === 'bill.pdf'
            );
            if (!rows.length) return { found: false, zoneClass: zone.className };
            const fileRect = rows[0].getBoundingClientRect();
            const texts = Array.from(zone.querySelectorAll('p, div, span')).filter((e) => {
                if (e.children.length) return false;
                const t = e.textContent.trim();
                return t.length > 8 && t !== 'bill.pdf';
            });
            const hits = texts
                .map((e) => {
                    const r = e.getBoundingClientRect();
                    const ox = Math.min(r.right, fileRect.right) - Math.max(r.left, fileRect.left);
                    const oy = Math.min(r.bottom, fileRect.bottom) - Math.max(r.top, fileRect.top);
                    return ox > 1 && oy > 1
                        ? { text: e.textContent.trim().slice(0, 40), ox: ox, oy: oy }
                        : null;
                })
                .filter(Boolean);
            return { found: true, zoneClass: zone.className, fileRect: fileRect, overlaps: hits };
        });
        record('probe_mobile_overlap', overlap);
        took(await shot(page, '25-intake-mobile-overlap-zh-mobile.png'));
    });
});

test.afterAll(() => {
    record('shots', SHOTS);
});
