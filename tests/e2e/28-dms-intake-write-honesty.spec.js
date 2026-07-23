// 任务 C · C-6/C-7 真浏览器验收(常驻回归闸)
// ============================================================
// 主窗收口复验:直接打 build 后的 static/dist(真实上线形态)。断言两件事:
//   C-6 用户清空的地址字段 → payload 里【不含】该键(后端键在即写、空串=清空)
//   C-7 更新既有客户时联系/寄送地址镜像默认关,且开着时分区副标题直说会被覆盖
// 起法:npx playwright test tests/e2e/28-dms-intake-write-honesty.spec.js
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8976;
const BASE = `http://127.0.0.1:${PORT}`;
const ART = path.join(__dirname, '_artifacts', 'dms_p1_closure');
fs.mkdirSync(ART, { recursive: true });

const ENDPOINTS = {
    items: [
        {
            id: 'ep-1',
            name: 'MR.ERP DMS',
            adapter: 'mrerp_dms',
            enabled: true,
            config: { system_url: 'https://dms.example.com', admin_username_enc: 'x' },
        },
    ],
};

const GEO = {
    selected: {
        province_id: '10',
        district_id: '1001',
        subdistrict_id: '100101',
        zipcode_id: '10200',
    },
    text: { house_no: '12/3', moo: '4', soi: 'ซอยบัตร', road: 'ถนนบัตร' },
    provinces: [['10', 'กรุงเทพมหานคร']],
    districts: [['1001', 'ดุสิต']],
    subdistricts: [['100101', 'วชิรพยาบาล']],
    zipcodes: [['10200', '10200']],
};
const ID_CARD = {
    prefix_name: 'นาย',
    name: 'สมชาย ใจดี',
    people_id: '1101700998118',
    birthday_be: '15/05/2530',
    address: {
        house_no: '12/3',
        moo: '4',
        soi: 'ซอยบัตร',
        road: 'ถนนบัตร',
        province: 'กรุงเทพมหานคร',
        district: 'ดุสิต',
        subdistrict: 'วชิรพยาบาล',
        zipcode: '10200',
    },
};
// 既有客户:身份证地址与联系/寄送地址【不同】(真实场景:户籍 ≠ 现住/寄送)
const CURRENT_FIELDS = {
    cuscode: 'C0001',
    branch_code: '00000',
    prefix_id: '17',
    name: 'สมชาย ใจดี',
    people_id: '1101700998118',
    tax_id: '1101700998118',
    birthday_be: '15/05/2530',
    phone: '0811111111',
    house_no: '12/3',
    moo: '4',
    soi: 'ซอยเดิม',
    road: 'ถนนบัตร',
    province_id: '10',
    district_id: '1001',
    subdistrict_id: '100101',
    zipcode_id: '10200',
    province_name: 'กรุงเทพมหานคร',
    district_name: 'ดุสิต',
    subdistrict_name: 'วชิรพยาบาล',
    zipcode_name: '10200',
    house_no_ct: '99/9',
    soi_ct: 'ซอยติดต่อ',
    road_ct: 'ถนนติดต่อ',
    province_id_ct: '10',
    district_id_ct: '1001',
    subdistrict_id_ct: '100101',
    zipcode_id_ct: '10200',
    house_no_sd: '55/5',
    road_sd: 'ถนนส่งเอกสาร',
    province_id_sd: '10',
    district_id_sd: '1001',
    subdistrict_id_sd: '100101',
    zipcode_id_sd: '10200',
};

function recognizeBody(scenario) {
    const dms =
        scenario === 'exact'
            ? {
                  scenario: 'exact',
                  candidates: [
                      {
                          customer_id: '1234',
                          name: 'สมชาย ใจดี',
                          people_id: ID_CARD.people_id,
                          score: 100,
                      },
                  ],
                  match: { current_fields: CURRENT_FIELDS },
                  geo: GEO,
                  prefixes: [['17', 'นาย']],
              }
            : { scenario: 'none', candidates: [], match: {}, geo: GEO, prefixes: [['17', 'นาย']] };
    return { ok: true, needs_review: false, id_card: ID_CARD, dms };
}

let server;
const pushed = [];
test.beforeAll(async () => {
    server = await localServer.start(PORT, '/static/dist/dms.html');
});
test.afterAll(() => localServer.stop(server));

async function boot(page, scenario) {
    const errors = [];
    page.on('console', (m) => {
        if (m.type() === 'error') errors.push(m.text());
    });
    await page.route('**/api/**', (route) => {
        const url = route.request().url();
        const json = (o) =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(o),
            });
        if (url.includes('/api/dms/session')) return json({ ok: true, is_owner: true });
        if (url.includes('/api/erp/endpoints')) return json(ENDPOINTS);
        if (url.includes('/api/dms/id-card/recognize')) return json(recognizeBody(scenario));
        if (url.includes('/api/dms/id-card/push')) {
            pushed.push(JSON.parse(route.request().postData() || '{}'));
            return json({ ok: true, dms_push: { customer_id: '1234' } });
        }
        if (url.includes('/api/dms/geo')) return json({ options: [] });
        if (url.includes('/api/me')) return json({ id: 'owner-1', role: 'owner' });
        return json({ ok: true });
    });
    await page.addInitScript(() => {
        try {
            localStorage.setItem('mrpilot_token', 'stub');
            localStorage.setItem('mrpilot_lang', 'zh');
        } catch (e) {
            void e;
        }
    });
    await page.goto(`${BASE}/static/dist/dms.html`);
    await page.waitForSelector('#dmsShell.on');
    return errors;
}

// 上传 → 识别 → 进入资料确认页
async function toConfirm(page) {
    await page.setInputFiles('#dx-file', {
        name: 'id.jpg',
        mimeType: 'image/jpeg',
        buffer: Buffer.from([0xff, 0xd8, 0xff, 0xd9]),
    });
    await page.click('#dx-start');
    await page.waitForSelector('#dx-go-confirm');
    await page.click('#dx-go-confirm');
    await page.waitForSelector('#dx-s-confirm.active');
}

test('C-7 · 更新既有客户:联系/寄送地址镜像默认关 · 界面显示的就是 DMS 现值', async ({ page }) => {
    const errors = await boot(page, 'exact');
    await toConfirm(page);
    await page.click('[data-tab="allfields"]');
    await page.waitForSelector('[data-sec="addr_ct"]');

    const ctSwitch = page.locator('[data-mirror="_ct"]');
    const sdSwitch = page.locator('[data-mirror="_sd"]');
    expect(await ctSwitch.isVisible()).toBe(true);
    expect(await ctSwitch.evaluate((el) => el.classList.contains('on'))).toBe(false);
    expect(await sdSwitch.evaluate((el) => el.classList.contains('on'))).toBe(false);
    // 关态开关的底色 = --line(非品牌蓝),真取计算样式而不是只看类名
    const offBg = await ctSwitch.evaluate(
        (el) => el.ownerDocument.defaultView.getComputedStyle(el).backgroundColor
    );
    expect(offBg).toBe('rgb(231, 231, 240)');

    await page.click('[data-sec="addr_ct"] .dx-fsec-h');
    await page.waitForSelector('[data-sec="addr_ct"].open');
    await expect(page.locator('#dx-f-house_no_ct')).toHaveValue('99/9');
    await expect(page.locator('#dx-f-soi_ct')).toHaveValue('ซอยติดต่อ');
    await page.screenshot({ path: path.join(ART, 'c7-mirror-off-update.png'), fullPage: true });
    expect(errors, errors.join('\n')).toEqual([]);
});

test('C-7 · 开启镜像后分区副标题直说本区会被身份证地址覆盖', async ({ page }) => {
    await boot(page, 'exact');
    await toConfirm(page);
    await page.click('[data-tab="allfields"]');
    await page.click('[data-mirror="_ct"]');
    await page.waitForSelector('[data-sec="addr_ct"] .sub.mirror');
    const note = page.locator('[data-sec="addr_ct"] .sub.mirror');
    expect(await note.isVisible()).toBe(true);
    await expect(note).toHaveText('开启时保存会用身份证地址覆盖本区');
    const color = await note.evaluate(
        (el) => el.ownerDocument.defaultView.getComputedStyle(el).color
    );
    expect(color).toBe('rgb(201, 138, 30)');
    await page.click('[data-sec="addr_ct"] .dx-fsec-h');
    await expect(page.locator('#dx-f-soi_ct')).toHaveValue('ซอยบัตร');
    await page.screenshot({ path: path.join(ART, 'c7-mirror-on-note.png'), fullPage: true });
});

test('C-7 · 新建客户仍三块地址同写(镜像默认开)', async ({ page }) => {
    await boot(page, 'none');
    await toConfirm(page);
    await page.click('[data-tab="allfields"]');
    await page.waitForSelector('[data-mirror="_ct"]');
    expect(
        await page.locator('[data-mirror="_ct"]').evaluate((el) => el.classList.contains('on'))
    ).toBe(true);
    expect(await page.locator('[data-sec="addr_ct"] .sub.mirror').isVisible()).toBe(true);
    await page.screenshot({ path: path.join(ART, 'c7-mirror-on-create.png'), fullPage: true });
});

test('C-6 · 清空的地址字段不进 payload(空白不清除 DMS 原资料)', async ({ page }) => {
    pushed.length = 0;
    await boot(page, 'exact');
    await toConfirm(page);
    await page.click('[data-tab="allfields"]');
    await page.waitForSelector('#dx-f-soi');

    // 真实按键清空「巷」,不用 fill() 绕过键盘
    await page.click('#dx-f-soi');
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Delete');
    await expect(page.locator('#dx-f-soi')).toHaveValue('');
    await page.screenshot({ path: path.join(ART, 'c6-cleared-soi.png'), fullPage: true });

    await page.click('.dx-tabview.active .dx-save-btn');
    await page.waitForSelector('#dx-m-ok');
    await page.screenshot({ path: path.join(ART, 'c6-confirm-modal.png') });
    await page.click('#dx-m-ok');
    await page.waitForSelector('#dx-s-success.active');

    expect(pushed.length).toBe(1);
    const body = pushed[0];
    const idBlock = body.addresses[''];
    // 用户清空的键不发 → 后端保留 DMS 原值(文案 dx-m-o1 承诺的就是这个)
    expect(Object.prototype.hasOwnProperty.call(idBlock, 'soi')).toBe(false);
    expect(idBlock.house_no).toBe('12/3');
    // 没有身份证来源、也没填过的键(建筑/楼层/房间/村庄)同样不发
    ['building', 'floor', 'room', 'village'].forEach((k) => {
        expect(Object.prototype.hasOwnProperty.call(idBlock, k)).toBe(false);
    });
    // C-7 连带:联系/寄送地址原样回写,没被身份证地址顶掉
    expect(body.addresses._ct.house_no).toBe('99/9');
    expect(body.addresses._ct.soi).toBe('ซอยติดต่อ');
    expect(body.addresses._sd.house_no).toBe('55/5');
    fs.writeFileSync(path.join(ART, 'c6-payload.json'), JSON.stringify(body, null, 2), 'utf8');
    await page.screenshot({ path: path.join(ART, 'c6-success.png'), fullPage: true });
});

test('C-3/C-1/C-4 · 连接卡不再谎报自动推送 · 向导文案只承诺网页真做的事', async ({ page }) => {
    await boot(page, 'exact');
    await page.waitForSelector('#dx-erp-cards .dx-erp-card.is-connected');
    const status = page.locator('#dx-erp-cards .dx-erp-status');
    expect(await status.isVisible()).toBe(true);
    const statusText = (await status.textContent()).trim();
    expect(statusText).toBe('已连接 · 管理员 ✓');
    expect(statusText).not.toContain('推送');
    await page.screenshot({ path: path.join(ART, 'c3-card-status.png'), fullPage: true });

    await page.click('#dx-erp-cards [data-erp-config]');
    await page.waitForSelector('#dms-wizard-overlay .dms-wizard');
    await expect(page.locator('#dms-wizard-overlay .dms-wizard')).toContainText(
        '识别身份证 → 查重 → 建立或更新 DMS 客户档(订车单在 LINE 渠道开)'
    );
    await expect(page.locator('#dms-wizard-overlay .dms-wizard')).toContainText(
        '用于 LINE 渠道开的订车单号;网页录入不建订车单'
    );
    await page.screenshot({ path: path.join(ART, 'c1-c4-wizard.png') });
});

test('C-8 · 推送记录页认出 LINE 订车行,不再显示「—」', async ({ page }) => {
    await boot(page, 'exact');
    await page.route('**/api/dms/records*', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                items: [
                    {
                        created_at: '2026-07-23T09:00:00Z',
                        seller_name: 'สมชาย ใจดี',
                        invoice_no: 'PN2600001',
                        status: 'success',
                        operator_name: 'อาหมิง',
                        request_body: { mode: 'booking', trigger: 'line_dms' },
                    },
                    {
                        created_at: '2026-07-23T08:00:00Z',
                        seller_name: 'สมหญิง ดีมาก',
                        invoice_no: '',
                        status: 'success',
                        operator_role: 'owner',
                        request_body: { mode: 'create' },
                    },
                ],
            }),
        })
    );
    await page.click('.dms-nav-item[data-view="records"]');
    await page.waitForSelector('.dms-rec-table');
    const modes = await page.locator('.dms-rec-row:not(.head) .dms-rec-c.mode').allTextContents();
    expect(modes).toEqual(['订车单', '新建']);
    await expect(page.locator('#dms-view-records .dms-page-head p')).toHaveText(
        '身份证建/改 DMS 客户,以及 LINE 渠道订车单的推送历史'
    );
    await page.screenshot({ path: path.join(ART, 'c8-records-booking.png'), fullPage: true });
});

test('四语 · 泰文(真实用户语言)新文案落地', async ({ page }) => {
    await boot(page, 'exact');
    await page.click('[data-dms-lang="th"]');
    await page.waitForSelector('#dx-erp-cards [data-erp-config]');
    await page.click('#dx-erp-cards [data-erp-config]');
    await page.waitForSelector('#dms-wizard-overlay .dms-wizard');
    const wiz = page.locator('#dms-wizard-overlay .dms-wizard');
    await expect(wiz).toContainText(
        'อ่านบัตรประชาชน → ตรวจสอบซ้ำ → สร้างหรืออัปเดตข้อมูลลูกค้าใน DMS (ใบจองเปิดผ่าน LINE)'
    );
    await expect(wiz).toContainText(
        'ใช้กับเลขที่ใบจองที่เปิดผ่าน LINE เท่านั้น การบันทึกบนเว็บไม่สร้างใบจอง'
    );
    await page.screenshot({ path: path.join(ART, 'th-wizard.png') });
});
