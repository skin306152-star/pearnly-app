// J-C 本地 stub 真浏览器验收(非 CI · 用完即删,同 _r2b_r4_taxid_verify 先例)。
// 真渲染 static/dist/ai.js/ai.css/ai.html(零改造)+ 真 DOM,只桩网络层(page.route)。
// 覆盖审核主路径:未判/已判计数、最新裁决、批量确认、五字段改数、方向判据、
// 最后一张自动续跑与移动端无横向溢出。lint/build/unit 由工程闸另验。
// 起法:npx playwright test tests/e2e/_jc_review_memory_verify.spec.js
/* global window */
const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8996;
const BASE = `http://127.0.0.1:${PORT}`;
const PAGE = BASE + '/static/dist/ai.html';
const ART = path.join(__dirname, '_artifacts', 'jc');

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT);
});
test.afterAll(() => localServer.stop(server));

function jsonRoute(body, status) {
    return (route) =>
        route.fulfill({
            status: status || 200,
            contentType: 'application/json',
            body: JSON.stringify(body),
        });
}

async function mount(page, table, opts = {}) {
    await page.route('**/api/**', async (route) => {
        const req = route.request();
        const url = new URL(req.url());
        const key = `${req.method()} ${url.pathname}`;
        const h = table[key];
        if (h) return h(route, req, url);
        return route.fulfill({ contentType: 'application/json', body: '{}' });
    });
    await page.addInitScript((lang) => {
        window.localStorage.setItem('mrpilot_token', 'tok-jc');
        window.localStorage.setItem('mrpilot_lang', lang || 'zh');
    }, opts.lang);
    if (opts.viewport) await page.setViewportSize(opts.viewport);
}

const CLIENT = { id: 5, name: 'Sister Makeup', tax_id: '0105567178203' };

function orderRoute(order, extra) {
    // 列表响应必须带 id/period/workspace_client_id——客户页先拿列表定位工单 id 再
    // getOrder(id),缺 id 会打到未桩的 GET .../orders/undefined,静默回落空对象。
    const listItem = {
        id: 'wo-1',
        period: '2569-05',
        workspace_client_id: 5,
        status: order.status || 'stuck',
    };
    return {
        'GET /api/workspace/clients': jsonRoute([CLIENT]),
        'GET /api/workorder/orders': jsonRoute({ orders: [listItem] }),
        'GET /api/workorder/orders/wo-1': jsonRoute(
            Object.assign(
                {
                    id: 'wo-1',
                    workspace_client_id: 5,
                    period: '2569-05',
                    status: 'stuck',
                    alerts: [],
                    needs: [],
                    blocked_reasons: [],
                    numbers: {},
                },
                order,
                extra || {}
            )
        ),
        'GET /api/workspace/clients/can-create': jsonRoute({ detail: 'authz.forbidden' }, 403),
    };
}

// ============ 断言 1:未判优先 + 已判折叠 + 计数器 + 展开改判 ============

test('客户页队列:待处理优先聚焦 + 已处理折叠 + 三段计数器 + 展开改判', async ({ page }) => {
    const decideCalls = [];
    const flagged = [
        {
            item_id: 'u1',
            kind: 'purchase_invoice',
            flag_reason: 'ocr_low_confidence',
            file_ref: '/x/u1.jpg',
            ocr_read: {
                seller_tax: '0105',
                subtotal: '100',
                vat: '7',
                total_amount: '107',
                invoice_number: 'U1',
            },
        },
        {
            item_id: 'u2',
            kind: 'purchase_invoice',
            flag_reason: 'ocr_low_confidence',
            file_ref: '/x/u2.jpg',
            ocr_read: {
                seller_tax: '0105',
                subtotal: '200',
                vat: '14',
                total_amount: '214',
                invoice_number: 'U2',
            },
        },
        {
            item_id: 'u3',
            kind: 'purchase_invoice',
            flag_reason: 'ocr_low_confidence',
            file_ref: '/x/u3.jpg',
            ocr_read: {
                seller_tax: '0105',
                subtotal: '300',
                vat: '21',
                total_amount: '321',
                invoice_number: 'U3',
            },
        },
        {
            item_id: 'd1',
            kind: 'purchase_invoice',
            flag_reason: 'ocr_low_confidence',
            file_ref: '/x/d1.jpg',
            ocr_read: {
                seller_tax: '0105',
                subtotal: '400',
                vat: '28',
                total_amount: '428',
                invoice_number: 'D1',
            },
            decision: {
                decision: 'face_value',
                values: {},
                actor: 'user:aaaaaaaa',
                at: '2026-07-16T10:00:00Z',
            },
        },
        {
            item_id: 'd2',
            kind: 'purchase_invoice',
            flag_reason: 'ocr_low_confidence',
            file_ref: '/x/d2.jpg',
            ocr_read: {
                seller_tax: '0105',
                subtotal: '500',
                vat: '35',
                total_amount: '535',
                invoice_number: 'D2',
            },
            decision: {
                decision: 'exclude',
                values: {},
                actor: 'user:bbbbbbbb',
                at: '2026-07-16T11:00:00Z',
            },
        },
    ];
    const table = orderRoute({ status: 'stuck', flagged: flagged });
    table['POST /api/workorder/orders/wo-1/decisions'] = async (route, req) => {
        decideCalls.push(JSON.parse(req.postData() || '{}'));
        return jsonRoute({ id: 'evt-1' })(route);
    };
    await mount(page, table, { lang: 'zh' });
    await page.goto(`${PAGE}#/client/5/review?period=2569-05`);

    // 首张聚焦=未判票(不是队列原始首位的 u1 也可能是 u1,后端序不变;关键是不落到已判票)。
    await expect(page.locator('#rvCounter')).toHaveText('待处理 3 · 已处理 2 · 共 5', {
        timeout: 15000,
    });
    const invnoCell = page.locator('.fldt tr', { hasText: /^票号/ });
    await expect(invnoCell).toBeVisible();

    // 已判折叠分组可见,summary 报「已裁 2 张」,默认收起(内容不可见)。
    const group = page.locator('.rv-decided-group');
    await expect(group).toBeVisible();
    await expect(group.locator('summary')).toContainText('已裁 2 张');
    const d1Row = page.locator('.rv-decided-row[data-item="d1"]');
    await expect(d1Row).toHaveCount(1);
    await expect(d1Row).not.toBeVisible();

    await page.screenshot({
        path: path.join(ART, '01-undecided-first-folded.png'),
        fullPage: true,
    });

    // 展开:两行可见,各带「已由 X 判 · 结果」。
    await group.locator('summary').click();
    await expect(d1Row).toBeVisible();
    await expect(d1Row).toContainText('已由');

    // 点「改判」→ 该票回到主聚焦流并立即显示,可再走 A/E/X(latest-wins 改判)。
    await d1Row.locator('[data-action="rv-revisit"]').click();
    await expect(page.locator('.fldt')).toContainText('D1');
    await page.keyboard.press('a');
    await expect
        .poll(() => decideCalls.find((c) => c.item_id === 'd1'), { timeout: 8000 })
        .toEqual({ item_id: 'd1', decision: 'face_value' });

    await page.screenshot({ path: path.join(ART, '02-revisit-redecided.png'), fullPage: true });
});

// ============ 断言 5(移动端):同一队列在 390×844 无横溢 ============

test('客户页队列:390×844 移动端无横溢', async ({ page }) => {
    const flagged = [
        {
            item_id: 'm1',
            kind: 'purchase_invoice',
            flag_reason: 'amount_math_fail',
            file_ref: '/x/m1.jpg',
            ocr_read: {
                seller_tax: '0105',
                subtotal: '100',
                vat: '7',
                total_amount: '107',
                invoice_number: 'M1',
            },
        },
    ];
    await mount(page, orderRoute({ status: 'stuck', flagged: flagged }), {
        lang: 'zh',
        viewport: { width: 390, height: 844 },
    });
    await page.goto(`${PAGE}#/client/5/review?period=2569-05`);
    await expect(page.locator('#rvCounter')).toBeVisible({ timeout: 15000 });
    const overflow = await page.evaluate(
        () =>
            window.document.documentElement.scrollWidth >
            window.document.documentElement.clientWidth + 1
    );
    expect(overflow).toBe(false);
    await page.screenshot({ path: path.join(ART, '03-mobile-390.png'), fullPage: true });
});

// ============ 断言 4:改数态五字段齐全，确定性建议只覆盖金额 ============

test('客户页队列:票号日期金额五字段可改,建议值与原值来源清楚', async ({ page }) => {
    const flagged = [
        {
            item_id: 'sugg1',
            kind: 'purchase_invoice',
            flag_reason: 'amount_math_fail',
            file_ref: '/x/IMG_2647.JPG',
            ocr_read: {
                seller_tax: '0105',
                subtotal: '58048.40',
                vat: '4060.05',
                total_amount: '62108.40',
                invoice_number: 'IN26-00575',
                invoice_date: '2026-04-21',
            },
        },
        {
            item_id: 'plain1',
            kind: 'purchase_invoice',
            flag_reason: 'amount_math_fail',
            file_ref: '/x/plain.jpg',
            ocr_read: {
                seller_tax: '0105',
                subtotal: '900.00',
                vat: '63.00',
                total_amount: '963.00',
                invoice_number: 'PLAIN-1',
                invoice_date: '2026-05-03',
            },
        },
    ];
    const alerts = [
        {
            type: 'amount_read_suggested',
            item_id: 'sugg1',
            invoice_number: 'IN26-00575',
            ocr: { net: '58048.40', vat: '4060.05', grand: '62108.40' },
            suggestion: { net: '58129.35', vat: '4069.05', grand: '62198.40' },
        },
    ];
    await mount(page, orderRoute({ status: 'stuck', flagged: flagged }, { alerts: alerts }), {
        lang: 'zh',
    });
    await page.goto(`${PAGE}#/client/5/review?period=2569-05`);
    await expect(page.locator('#rvCounter')).toBeVisible({ timeout: 15000 });

    // 确定性建议只替换三个金额；票号、日期仍来自 OCR，五个字段均可编辑。
    await page.keyboard.press('e');
    await expect(page.locator('.rv-suggest-note')).toBeVisible();
    await expect(page.locator('#rvInvoiceNoInput')).toHaveValue('IN26-00575');
    await expect(page.locator('#rvInvoiceDateInput')).toHaveValue('2026-04-21');
    await expect(page.locator('#rvNetInput')).toHaveValue('58129.35');
    await expect(page.locator('#rvVatInput')).toHaveValue('4069.05');
    await expect(page.locator('#rvGrandInput')).toHaveValue('62198.40');
    await expect(page.locator('.rv-edit-original')).toHaveCount(5);
    await page.screenshot({ path: path.join(ART, '04-suggest-prefill.png'), fullPage: true });
    await page.keyboard.press('Escape');

    // 无建议也必须给出完整五字段，而不是只让人改 VAT。
    await page.keyboard.press('ArrowRight');
    await page.keyboard.press('e');
    await expect(page.locator('.rv-edit-note')).toBeVisible();
    await expect(page.locator('.rv-suggest-note')).toHaveCount(0);
    await expect(page.locator('#rvInvoiceNoInput')).toHaveValue('PLAIN-1');
    await expect(page.locator('#rvInvoiceDateInput')).toHaveValue('2026-05-03');
    await expect(page.locator('#rvNetInput')).toHaveValue('900.00');
    await expect(page.locator('#rvVatInput')).toHaveValue('63.00');
    await expect(page.locator('#rvGrandInput')).toHaveValue('963.00');
    await expect(page.locator('.rv-edit-original')).toHaveCount(5);
    await page.screenshot({ path: path.join(ART, '05-plain-five-field-form.png'), fullPage: true });
});

test('客户页队列:疑似本方销项说明具体判据,不再显示方向判不出的矛盾话术', async ({ page }) => {
    const flagged = [
        {
            item_id: 'dir1',
            kind: 'sales_doc',
            flag_reason: 'sales_direction_unhandled',
            file_ref: '/x/dir1.jpg',
            ocr_read: {
                seller_tax: '0105567178203',
                vendor: 'Sister Makeup',
                subtotal: '100',
                vat: '7',
                total_amount: '107',
                invoice_number: 'SWO2000076',
                invoice_date: '2026-05-03',
            },
            verdict_hint: {
                narrative_key: 'verdict_sales_direction',
                params: { seller_tax: '0105567178203', vendor: 'Sister Makeup' },
                confidence: 'high',
                severity: 'crit',
                suggested_decision: { decision: 'assign_kind', kind: 'sales_doc' },
            },
        },
    ];
    await mount(page, orderRoute({ status: 'stuck', flagged: flagged }), { lang: 'zh' });
    await page.goto(`${PAGE}#/client/5/review?period=2569-05`);

    const note = page.locator('.rv-dir-note');
    await expect(note).toContainText('卖方税号 0105567178203 与本账套一致', { timeout: 15000 });
    await expect(note).not.toContainText('AI 判不出是进项还是销项');
    await page.screenshot({ path: path.join(ART, '05b-direction-evidence.png'), fullPage: true });
});

test('客户页队列:最后一张保存后自动续跑并进交付包,不再要求重复点重跑', async ({ page }) => {
    let detailCalls = 0;
    let runCalls = 0;
    const decisionCalls = [];
    const flagged = [
        {
            item_id: 'last1',
            kind: 'purchase_invoice',
            flag_reason: 'ocr_low_confidence',
            file_ref: '/x/last1.jpg',
            ocr_read: {
                seller_tax: '0105',
                subtotal: '100',
                vat: '7',
                total_amount: '107',
                invoice_number: 'LAST-1',
                invoice_date: '2026-05-03',
            },
        },
    ];
    const detail = {
        id: 'wo-1',
        workspace_client_id: 5,
        period: '2569-05',
        status: 'stuck',
        alerts: [],
        needs: [],
        blocked_reasons: [],
        numbers: {},
        flagged: flagged,
    };
    const table = orderRoute(detail);
    table['GET /api/workorder/orders/wo-1'] = (route) => {
        detailCalls += 1;
        if (detailCalls === 1) return jsonRoute(detail)(route);
        if (detailCalls === 2) {
            return jsonRoute(Object.assign({}, detail, { status: 'running', flagged: [] }))(route);
        }
        return jsonRoute(Object.assign({}, detail, { status: 'archive', flagged: [] }))(route);
    };
    table['POST /api/workorder/orders/wo-1/decisions'] = async (route, req) => {
        decisionCalls.push(JSON.parse(req.postData() || '{}'));
        return jsonRoute({ id: 'evt-last' })(route);
    };
    table['POST /api/workorder/orders/wo-1/run'] = (route) => {
        runCalls += 1;
        return jsonRoute({ ok: true })(route);
    };
    await mount(page, table, { lang: 'zh' });
    await page.goto(`${PAGE}#/client/5/review?period=2569-05`);
    await expect(page.locator('#rvCounter')).toBeVisible({ timeout: 15000 });

    await page.keyboard.press('a');
    await expect.poll(() => decisionCalls.length, { timeout: 8000 }).toBe(1);
    await expect(page.locator('.rv-done')).toContainText('审核已完成，后台正在继续处理');
    await expect(page.locator('.rv-done button:disabled')).toBeVisible();
    await expect(page.locator('[data-action="rv-rerun"]')).toHaveCount(0);
    await page.screenshot({
        path: path.join(ART, '05c-last-decision-running.png'),
        fullPage: true,
    });

    await expect
        .poll(() => page.evaluate(() => window.location.hash), { timeout: 12000 })
        .toBe('#/client/5/pkg');
    expect(runCalls).toBe(0);
    expect(detailCalls).toBeGreaterThanOrEqual(3);
});

// ============ 断言 3:批量确认一步弹窗 → 落库数量断言 → 组消失;取消=零请求 ============

test('客户页队列:全部按建议处理 · 一步确认后逐张落库,组消失;取消=零请求', async ({ page }) => {
    const batchCalls = [];
    const mkItem = (id) => ({
        item_id: id,
        kind: 'purchase_invoice',
        flag_reason: 'ocr_low_confidence',
        file_ref: `/x/${id}.jpg`,
        ocr_read: {
            seller_tax: '0105',
            subtotal: '100',
            vat: '7',
            total_amount: '107',
            invoice_number: id,
        },
        verdict_hint: {
            severity: 'warn',
            confidence: 'high',
            suggested_decision: { decision: 'face_value' },
        },
    });
    const flagged = [mkItem('b1'), mkItem('b2'), mkItem('b3')];
    const table = orderRoute({ status: 'stuck', flagged: flagged });
    table['POST /api/workorder/orders/wo-1/decisions:batch'] = async (route, req) => {
        const body = JSON.parse(req.postData() || '{}');
        batchCalls.push(body);
        return jsonRoute({
            results: body.decisions.map((d) => ({ item_id: d.item_id, ok: true, event_id: 'evt' })),
            ok_count: body.decisions.length,
            fail_count: 0,
            total: body.decisions.length,
        })(route);
    };
    await mount(page, table, { lang: 'zh' });
    await page.goto(`${PAGE}#/client/5/review?period=2569-05`);

    const bulkBtn = page.locator('[data-action="rv-bulk-run"]');
    await expect(bulkBtn).toBeVisible({ timeout: 15000 });
    await expect(bulkBtn).toContainText('3');
    await page.screenshot({ path: path.join(ART, '06-bulk-banner.png'), fullPage: true });

    // 站内确认框取消 = 零请求。
    await bulkBtn.click();
    const confirm = page.locator('.rv-confirm-modal');
    await expect(confirm).toBeVisible();
    await expect(confirm).toContainText('批量处理同类票据');
    await page.screenshot({
        path: path.join(ART, '06b-bulk-confirm-modal.png'),
        fullPage: true,
    });
    await page.click('[data-action="rv-bulk-cancel"]');
    await expect(confirm).toHaveCount(0);
    expect(batchCalls.length).toBe(0);
    await expect(bulkBtn).toBeVisible();

    // 确认 → 逐张落库(数量断言)→ 主操作区清空,整组移入已处理折叠区。
    await bulkBtn.click();
    await page.click('[data-action="rv-bulk-confirm"]');
    await expect.poll(() => batchCalls.length, { timeout: 8000 }).toBe(1);
    expect(batchCalls[0].decisions).toHaveLength(3);
    expect(batchCalls[0].decisions.map((d) => d.item_id).sort()).toEqual(['b1', 'b2', 'b3']);
    expect(batchCalls[0].decisions.every((d) => d.decision === 'face_value')).toBe(true);
    await expect(page.locator('[data-action="rv-bulk-run"]')).toHaveCount(0);
    await expect(page.locator('.rv-decided-group summary')).toContainText('已裁 3 张');
    await page.screenshot({
        path: path.join(ART, '07-bulk-confirmed-group-gone.png'),
        fullPage: true,
    });
});

// ============ 断言 2:收件箱最新裁决值 + 已人工修正徽标(IMG_2647 尸检)/ 未改票=OCR 值 ============

test('收件箱:改数裁决票显最新值+已人工修正徽标,未改票显 OCR 值无徽标,已判折叠', async ({
    page,
}) => {
    const feedItem = (over) =>
        Object.assign(
            {
                item_id: 'x',
                work_order_id: 'wo-1',
                client_name: 'Sister Makeup',
                period: '2569-05',
                kind: 'purchase_invoice',
                flag_reason: 'amount_math_fail',
                file_ref: '/x/IMG_2647.JPG',
                ocr_read: {
                    seller_tax: '0105',
                    subtotal: '58048.40',
                    vat: '4060.05',
                    total_amount: '62108.40',
                    invoice_number: 'IN26-00575',
                },
                verdict_hint: { severity: 'crit', confidence: 'low' },
                decision: null,
            },
            over
        );
    const corrected = feedItem({
        item_id: 'corrected1',
        decision: {
            decision: 'recalc',
            values: { vat: '4069.05' },
            actor: 'user:ccccccccc',
            at: '2026-07-17T09:00:00Z',
        },
    });
    const plain = feedItem({ item_id: 'plain1', decision: null });
    const table = {
        'GET /api/workorder/review-queue': jsonRoute({
            period: null,
            clients: [],
            flagged_items: [corrected, plain],
            counts: { clients: 0, orders: 0, flagged: 2 },
        }),
    };
    await mount(page, table, { lang: 'zh' });
    await page.goto(`${PAGE}#/pool`);
    await page.waitForSelector('.riq-group', { timeout: 15000 });

    // 未改票(plain):OCR 值原样显示,不带「已人工修正」。
    const plainCard = page.locator('.riq-item[data-item="plain1"]');
    await expect(plainCard).toBeVisible();
    await expect(plainCard).toContainText('฿4,060.05');
    await expect(plainCard).not.toContainText('已人工修正');

    // 改数票(corrected)折叠进已判分组,默认收起。
    const group = page.locator('.riq-decided-group');
    await expect(group).toBeVisible();
    const correctedCard = page.locator('.riq-item[data-item="corrected1"]');
    await expect(correctedCard).toHaveCount(1);
    await expect(correctedCard).not.toBeVisible();

    await page.screenshot({ path: path.join(ART, '08-inbox-folded.png'), fullPage: true });

    // 展开后:显最新裁决值(4069.05)+「已人工修正」徽标,不是旧 OCR 值(4060.05)。
    await group.locator('summary').click();
    await expect(correctedCard).toBeVisible();
    await expect(correctedCard).toContainText('฿4,069.05');
    await expect(correctedCard).toContainText('已人工修正');

    await page.screenshot({ path: path.join(ART, '09-inbox-corrected-value.png'), fullPage: true });
});
