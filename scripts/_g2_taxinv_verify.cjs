// G2 补开全式税票 · 真浏览器 E2E 验收(收银台补开视图 + 主站交易明细行内动作)。
// 真 bundle 真 DOM 真计算样式;API 打桩(仓内 stubbed 注入先例:采购 WHT E2E)。
// 断言口径:isVisible + getComputedStyle,截图落 tests/e2e/_artifacts/g2_taxinv/。
/* eslint-disable no-undef */
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');
const { serveStatic, chk, summary, bootHome } = require('./_verify_shared.cjs');

const PORT = 4873;
const SHOTS = path.resolve(__dirname, '../tests/e2e/_artifacts/g2_taxinv');
fs.mkdirSync(SHOTS, { recursive: true });

const DETAIL_S1 = {
    sale: {
        id: 's1',
        receipt_no: 'ABB-T1-2026-00187',
        doc_kind: 'abbrev_tax_invoice',
        sale_type: 'sale',
        subtotal: '1157.00',
        discount_total: '0.00',
        vat_amount: '75.69',
        grand_total: '1157.00',
        price_includes_vat: true,
        paid_total: '1157.00',
        change_amount: '0.00',
        status: 'completed',
        sold_at: '2026-08-05T14:32:00+07:00',
        full_invoice_id: null,
    },
    full_invoice: null,
    lines: [
        { id: 'l1', product_id: 'p1', qty: 1, unit_price: '250.00', line_total: '250.00' },
        { id: 'l2', product_id: 'p2', qty: 2, unit_price: '179.00', line_total: '358.00' },
    ],
    payments: [{ method: 'cash', amount: '1157.00', ref: null }],
};
const FULL_INV_S1 = { id: 'd1', doc_number: 'TIV-2026-00099', issue_date: '2026-08-05' };
const FULL_INV_S2 = { id: 'd2', doc_number: 'TIV-2026-00042', issue_date: '2026-08-05' };

function ok(data) {
    return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ok: true, data }),
    };
}

async function posSide(ctx) {
    let s1Issued = false; // POST 之后 detail 翻成已开(检验「开出后回已开过卡」链路)
    const page = await ctx.newPage();
    await page.setViewportSize({ width: 1180, height: 820 });
    await page.route('**/api/pos/**', (route) => {
        const url = route.request().url();
        const m = route.request().method();
        if (url.includes('/sales/today'))
            return route.fulfill(
                ok({
                    items: [
                        {
                            id: 's1',
                            receipt_no: 'ABB-T1-2026-00187',
                            sold_at: '2026-08-05T14:32:00+07:00',
                            grand_total: '1157.00',
                            method: 'cash',
                            mixed: false,
                            voidable: false,
                        },
                        {
                            id: 's2',
                            receipt_no: 'ABB-T1-2026-00185',
                            sold_at: '2026-08-05T11:05:00+07:00',
                            grand_total: '608.00',
                            method: 'qr',
                            mixed: false,
                            voidable: false,
                        },
                    ],
                })
            );
        if (url.includes('/tax-lookup'))
            return route.fulfill(
                ok({
                    found: true,
                    tax_id: '0107544000108',
                    name: 'บริษัท ปตท. จำกัด (มหาชน)',
                    address: '555 ถ.วิภาวดีรังสิต จตุจักร กรุงเทพฯ 10900',
                    branch_no: '00000',
                    branch_label: 'สำนักงานใหญ่',
                    vat_registered: true,
                })
            );
        if (m === 'POST' && url.includes('/sales/s1/full-tax-invoice')) {
            s1Issued = true;
            return route.fulfill(ok({ document: { ...FULL_INV_S1, doc_type: 'tax_invoice' } }));
        }
        if (url.includes('full-invoice-pdf'))
            return route.fulfill({
                status: 200,
                contentType: 'application/pdf',
                body: '%PDF-1.4 stub',
            });
        if (url.includes('/sales/by-receipt'))
            return route.fulfill(
                ok({
                    ...DETAIL_S1,
                    sale: {
                        ...DETAIL_S1.sale,
                        id: 's2',
                        receipt_no: 'ABB-T1-2026-00185',
                        full_invoice_id: 'd2',
                    },
                    full_invoice: FULL_INV_S2,
                })
            );
        if (url.includes('/sales/s1'))
            return route.fulfill(
                s1Issued
                    ? ok({
                          ...DETAIL_S1,
                          sale: { ...DETAIL_S1.sale, full_invoice_id: 'd1' },
                          full_invoice: FULL_INV_S1,
                      })
                    : ok(DETAIL_S1)
            );
        return route.fulfill(ok({}));
    });
    const errs = [];
    page.on('pageerror', (e) => errs.push(String(e)));
    await page.goto(`http://localhost:${PORT}/static/dist/pos.html`, {
        waitUntil: 'domcontentloaded',
    });
    await page.waitForFunction(() => window.POS && window.POS.taxinv && window.POS.showView);
    await page.evaluate(() => {
        window.POS.state.token = 'tok';
        window.POS.state.workspaceClientId = 7;
        window.POS.showView('taxinv');
    });

    // 1) 补开视图:今日列表可见(计算样式作证,不是 grep 类名)
    await page.waitForSelector('#taxinv-body .titem');
    chk(
        'POS 补开视图可见(display=block)',
        (await page.$eval('#view-taxinv', (el) => getComputedStyle(el).display)) === 'block'
    );
    chk('今日列表两笔', (await page.$$('#taxinv-body .titem')).length === 2);
    await page.screenshot({ path: path.join(SHOTS, 'pos-01-视图-今日列表.png') });

    // 2) 点一笔 → 弹窗(#tax-mask 已搬出 view-main:必须在 taxinv 视图下真显示)
    await page.click('#taxinv-body .titem[data-sale="s1"]');
    await page.waitForSelector('#tax-mask.show');
    const maskCss = await page.$eval('#tax-mask', (el) => {
        const cs = getComputedStyle(el);
        return { display: cs.display, position: cs.position };
    });
    chk(
        '弹窗真显示(display=flex · position=fixed · 跨视图不被吞)',
        maskCss.display === 'flex' && maskCss.position === 'fixed'
    );
    chk('弹窗引用原小票号', (await page.textContent('#tax-ref-no')).includes('ABB-T1-2026-00187'));
    await page.screenshot({ path: path.join(SHOTS, 'pos-02-弹窗-买方表单.png') });

    // 3) 税号打错一位(13 位但校验位错)→ 红态 + 提交禁用(真按键,不用 fill 假绿)
    await page.click('#tax-taxid');
    await page.keyboard.type('1234567890123');
    await page.waitForSelector('#tax-taxid-fld.bad-on');
    const badVisible = await page.$eval(
        '#tax-taxid-bad',
        (el) => getComputedStyle(el).display !== 'none'
    );
    chk('Mod-11 错号红态可见', badVisible);
    chk('错号时提交禁用', await page.$eval('#tax-submit', (b) => b.disabled));
    await page.screenshot({ path: path.join(SHOTS, 'pos-03-税号校验位错-红态.png') });

    // 4) 真号 → 绿勾 + 带出可点 → RD 回填
    await page.fill('#tax-taxid', '');
    await page.keyboard.type('0107544000108');
    await page.waitForSelector('#tax-taxid-fld.ok-on');
    chk('真号带出按钮可点', !(await page.$eval('#tax-lookup-btn', (b) => b.disabled)));
    await page.click('#tax-lookup-btn');
    await page.waitForFunction(() => document.getElementById('tax-name').value.length > 0);
    chk('RD 带出回填名称', (await page.inputValue('#tax-name')).includes('ปตท'));
    chk('RD 带出回填地址', (await page.inputValue('#tax-address')).includes('วิภาวดี'));
    await page.screenshot({ path: path.join(SHOTS, 'pos-04-税号带出回填.png') });

    // 5) 勾存档 → 开具 → 关弹窗 → 回「已开过」卡(票号来自 POST 响应后的 detail 复取)
    await page.check('#tax-save-buyer');
    await page.click('#tax-submit');
    await page.waitForSelector('#taxinv-reprint');
    chk(
        '开出后回已开过卡(票号上墙)',
        (await page.textContent('#taxinv-body')).includes('TIV-2026-00099')
    );
    await page.screenshot({ path: path.join(SHOTS, 'pos-05-开出后已开过卡.png') });

    // 6) 凭小票号召回一张已开过的 → 直接给已开过卡(不进弹窗撞 409)
    await page.click('#taxinv-back');
    await page.waitForSelector('#taxinv-body .titem');
    await page.fill('#taxinv-receipt', 'ABB-T1-2026-00185');
    await page.click('#taxinv-find-btn');
    await page.waitForSelector('#taxinv-reprint');
    chk(
        '已开过单召回给重打卡',
        (await page.textContent('#taxinv-body')).includes('TIV-2026-00042')
    );
    await page.screenshot({ path: path.join(SHOTS, 'pos-06-召回已开过-重打卡.png') });

    // 7) 四态:空态 / 错误态(改桩后 resetView)
    await page.evaluate(() => {
        window.POS.data.salesToday = async () => [];
        window.POS.taxinv.resetView();
    });
    await page.waitForFunction(() => document.querySelector('#taxinv-body .state') !== null);
    chk('空态指路文案', ((await page.textContent('#taxinv-body .state')) || '').length > 0);
    await page.screenshot({ path: path.join(SHOTS, 'pos-07-空态.png') });
    await page.evaluate(() => {
        window.POS.data.salesToday = async () => {
            throw { code: 'pos.unexpected' };
        };
        window.POS.taxinv.resetView();
    });
    await page.waitForFunction(() => {
        const el = document.querySelector('#taxinv-body .state');
        return el && el.textContent.length > 0;
    });
    await page.screenshot({ path: path.join(SHOTS, 'pos-08-错误态.png') });

    chk('POS 页零 JS 错误', errs.length === 0);
    if (errs.length) console.log(errs.slice(0, 3));
    await page.close();
}

async function mainSide(ctx) {
    let issued = false;
    const { page, errs } = await bootHome(ctx, {
        port: PORT,
        lang: 'zh',
        viewport: { width: 1280, height: 840 },
        beforeGoto: async (page) => {
            await page.route('**/api/pos/admin/sales-log**', (route) =>
                route.fulfill(
                    ok({
                        items: [
                            {
                                id: 's1',
                                receipt_no: 'ABB-T1-2026-00187',
                                sold_at: '2026-08-05T14:32:00+07:00',
                                cashier_id: null,
                                cashier_name: 'มินท์',
                                items: 'Mascara x1, ลิปแมท x2',
                                qty_total: '3',
                                subtotal: '1157.00',
                                discount_total: '0',
                                vat_amount: '75.69',
                                grand_total: '1157.00',
                                paid_total: '1157.00',
                                change_amount: '0',
                                method: '现金',
                                full_invoice_id: issued ? 'd1' : null,
                                full_invoice_no: issued ? 'TIV-2026-00099' : null,
                                shift_id: null,
                                shift_opened_at: '2026-08-05T09:00:00+07:00',
                                shift_closed_at: '',
                            },
                            {
                                id: 's2',
                                receipt_no: 'ABB-T1-2026-00185',
                                sold_at: '2026-08-05T11:05:00+07:00',
                                cashier_id: null,
                                cashier_name: 'มินท์',
                                items: 'แป้งพัฟ x1',
                                qty_total: '1',
                                subtotal: '608.00',
                                discount_total: '0',
                                vat_amount: '39.77',
                                grand_total: '608.00',
                                paid_total: '608.00',
                                change_amount: '0',
                                method: 'PromptPay',
                                full_invoice_id: 'd2',
                                full_invoice_no: 'TIV-2026-00042',
                                shift_id: null,
                                shift_opened_at: '2026-08-05T09:00:00+07:00',
                                shift_closed_at: '',
                            },
                        ],
                        total: 2,
                    })
                )
            );
            await page.route('**/api/pos/admin/cashiers**', (route) =>
                route.fulfill(ok({ cashiers: [] }))
            );
            await page.route('**/api/pos/tax-lookup**', (route) =>
                route.fulfill(
                    ok({
                        found: true,
                        name: 'บริษัท เมคอัพสตูดิโอ จำกัด',
                        address: '55 ถ.สุขุมวิท กรุงเทพฯ',
                        vat_registered: true,
                    })
                )
            );
            await page.route('**/api/pos/sales/s1/full-tax-invoice', (route) => {
                issued = true;
                return route.fulfill(
                    ok({
                        document: {
                            id: 'd1',
                            doc_number: 'TIV-2026-00099',
                            doc_type: 'tax_invoice',
                        },
                    })
                );
            });
            await page.route('**/full-invoice-pdf**', (route) =>
                route.fulfill({
                    status: 200,
                    contentType: 'application/pdf',
                    body: '%PDF-1.4 stub',
                })
            );
        },
    });
    // 套账 id:activeWsId 走 window.getActiveWorkspaceClientId()(inventory-common)
    await page.evaluate(() => {
        window.getActiveWorkspaceClientId = () => 7;
    });
    await page.evaluate(() => window.routeTo && window.routeTo('pos-sales-log'));
    await page.evaluate(() => window.loadPosSalesLog && window.loadPosSalesLog());
    await page.waitForSelector('#poslog-body .tiv', { timeout: 15000 });

    chk('主站税票列:未开行有补开钮', (await page.$('#poslog-body [data-tiv-make="s1"]')) !== null);
    chk(
        '主站税票列:已开行显票号',
        ((await page.textContent('#poslog-body [data-tiv-open="s2"]')) || '').includes(
            'TIV-2026-00042'
        )
    );
    await page.screenshot({
        path: path.join(SHOTS, 'main-01-交易明细-税票列.png'),
        fullPage: false,
    });

    await page.click('#poslog-body [data-tiv-make="s1"]');
    await page.waitForSelector('#postax-mask.show');
    chk(
        '主站弹窗真显示(display=flex)',
        (await page.$eval('#postax-mask', (el) => getComputedStyle(el).display)) === 'flex'
    );
    await page.click('#postax-taxid');
    await page.keyboard.type('0107544000108');
    await page.waitForFunction(() => !document.getElementById('postax-lookup').disabled);
    await page.click('#postax-lookup');
    await page.waitForFunction(() => document.getElementById('postax-name').value.length > 0);
    chk('主站带出回填', (await page.inputValue('#postax-name')).includes('เมคอัพ'));
    await page.screenshot({ path: path.join(SHOTS, 'main-02-弹窗-带出回填.png') });

    await page.check('#postax-save');
    await page.click('#postax-go');
    await page.waitForFunction(() => {
        const b = document.querySelector('#poslog-body [data-tiv-open="s1"]');
        return b && b.textContent.includes('TIV-2026-00099');
    });
    chk('开出后行内票号即时上行', true);
    await page.screenshot({ path: path.join(SHOTS, 'main-03-开出后票号上行.png') });

    chk('主站页零 JS 错误', errs.length === 0);
    if (errs.length) console.log(errs.slice(0, 3));
    await page.close();
}

(async () => {
    const srv = await serveStatic(PORT, {
        rewrite: null,
    });
    const browser = await chromium.launch({ headless: true });
    const ctx = await browser.newContext();
    try {
        await posSide(ctx);
        await mainSide(ctx);
    } catch (e) {
        chk('E2E 未抛异常', false);
        console.error(e);
    }
    await browser.close();
    srv.close();
    process.exit(summary());
})();
