// SA-2 · EDC 聚合佐证卡 + 矩阵逾期徽章顺延 · 本地 stub 真浏览器验收
// ============================================================
// 自起静态服(_local_static_server)+ page.route stub /api/**(同 _ui1 先例)。验收:
//   ① 工单详情两张佐证卡并排真渲染(isVisible + getComputedStyle):c.1 逐票卡 + SA-2
//      EDC 收单聚合卡,后者带覆盖率事实与「仅佐证」判据行,数字与后端佐证 payload 一致
//   ② 无 edc_corroboration 时不渲染 EDC 卡(现状诚实,零假装)
//   ③ 捎带件:矩阵「风险」筛选逾期判据改读 due_efiling_deferred(周六截止顺延到周一,
//      固定时钟=周一 → 不算逾期;对照格顺延日已过 → 仍逾期)
//   ④ 390×844 无横向溢出;四语 i18n key 不裸奔
// 截图存 tests/e2e/_artifacts/sa2/(1280×900 + 390×844)。
//
// 起法:npx playwright test tests/e2e/_sa2_edc_corrob_verify.spec.js
/* global window, document */

const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8987;
const BASE = `http://127.0.0.1:${PORT}`;
const PAGE = `${BASE}/static/dist/ai.html`;
const ART = path.join(__dirname, '_artifacts', 'sa2');

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT);
});

test.afterAll(() => {
    localServer.stop(server);
});

// 后端 edc_corroboration.build_corroboration 的真实形状(SM 5月真料聚合值)。
const EDC_CRB = {
    source: 'edc_aggregate',
    invoice_count: 9,
    deduped_count: 9,
    duplicates: [],
    gross_total: '99298.00',
    net_total: '92801.87',
    vat_total: '6496.13',
    vat_method: 'aggregate_first',
    fee_missing_count: 9,
    date_from: '2026-05-10',
    date_to: '2026-05-28',
    daily: [],
    conflicts: [{ kind: 'edc_date_unresolved', refs: ['i7'] }],
    notes: ['bank_channel_absent:未提供银行入账,交叉核对与缺口探测未执行'],
    authoritative_net: '858780.16',
    authoritative_vat: '60114.61',
    gap_net: '765978.29',
    coverage: '0.1081',
    covered_state: 'amber',
};

const SALES_CRB = {
    source: 'invoice_aggregate',
    invoice_count: 60,
    deduped_count: 59,
    duplicates: ['02000101'],
    net_total: '100338.02',
    vat_total: '7023.55',
    gross_total: '107361.57',
    conservation_violations: [],
    date_from: '2026-05-01',
    date_to: '2026-05-28',
    authoritative_net: '858780.16',
    authoritative_vat: '60114.61',
    gap_net: '758442.14',
    coverage: '0.1168',
    covered_state: 'amber',
};

const ORDER_DETAIL = {
    id: 'wo-1',
    workspace_client_id: 1,
    period: '2569-05',
    intent: 'monthly_vat',
    status: 'review',
    current_step: 'review',
    progress: null,
    flagged: [],
    needs: [],
    blocked_reasons: [],
    numbers: { sales_amount: '858780.16', output_vat: '60114.61', input_vat: '29263.28' },
    bank_recon: null,
    shadow_draft: null,
    financials: null,
    sales_corroboration: SALES_CRB,
    edc_corroboration: EDC_CRB,
    deliverables: [],
};

// 捎带件用矩阵:固定时钟 2026-07-20(周一)。pp30 格截止 2026-07-18(周六)顺延到
// 07-20 → 不逾期;pnd1 格顺延日 07-17 已过 → 逾期(风险筛选唯一命中)。
const TODAY_FIXED = '2026-07-20T09:00:00+07:00';
const MATRIX = {
    period: '2569-06',
    clients: [
        {
            id: 1,
            name: 'Sat Due Shop',
            tax_id: '1111111111111',
            missing_order: false,
            profile_completeness: 1,
        },
        {
            id: 2,
            name: 'Overdue Shop',
            tax_id: '2222222222222',
            missing_order: false,
            profile_completeness: 1,
        },
    ],
    obligation_codes: ['pp30'],
    obligation_labels: { pp30: { zh: '增值税申报(PP30)' } },
    cells: [
        {
            client_id: 1,
            obligation_code: 'pp30',
            obligation_status: 'due',
            order_status: 'running',
            work_order_id: 'wo-1',
            due_paper: '2026-07-15',
            due_efiling: '2026-07-18',
            due_paper_deferred: '2026-07-15',
            due_efiling_deferred: '2026-07-20',
            badge: 'in_progress',
        },
        {
            client_id: 2,
            obligation_code: 'pp30',
            obligation_status: 'due',
            order_status: 'running',
            work_order_id: 'wo-2',
            due_paper: '2026-07-15',
            due_efiling: '2026-07-15',
            due_paper_deferred: '2026-07-15',
            due_efiling_deferred: '2026-07-17',
            badge: 'in_progress',
        },
    ],
};

function fulfillJson(route, body, status = 200) {
    return route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
}

async function boot(page, { lang = 'zh', hash = '#/' } = {}) {
    await page.route('**/api/**', (route) => {
        const p = new URL(route.request().url()).pathname;
        if (p === '/api/workorder/orders/wo-1') return fulfillJson(route, ORDER_DETAIL);
        if (p === '/api/workorder/orders') {
            return fulfillJson(route, {
                orders: [
                    { id: 'wo-1', period: '2569-05', status: 'review', intent: 'monthly_vat' },
                ],
                count: 1,
            });
        }
        if (p === '/api/me') return fulfillJson(route, { username: 'somchai-acct' });
        if (p === '/api/tax-profile/matrix') return fulfillJson(route, MATRIX);
        if (p === '/api/workspace/clients/1') {
            return fulfillJson(route, { id: 1, name: 'Sat Due Shop', tax_id: '1111111111111' });
        }
        if (p === '/api/workspace/clients') return fulfillJson(route, { clients: MATRIX.clients });
        if (p === '/api/workspace/clients/can-create') return fulfillJson(route, { allowed: true });
        if (p === '/api/workorder/review-queue') {
            return fulfillJson(route, {
                period: null,
                clients: [],
                counts: { clients: 0, orders: 0, flagged: 0 },
            });
        }
        if (p === '/api/ai/client-pool') return fulfillJson(route, { groups: [] });
        return fulfillJson(route, {});
    });
    await page.clock.setFixedTime(new Date(TODAY_FIXED));
    await page.addInitScript(
        ([l]) => {
            window.localStorage.setItem('mrpilot_token', 'tok-sa2');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [lang]
    );
    await page.goto(PAGE + hash);
    await page.waitForSelector('.shell', { timeout: 15000 });
}

async function noHorizontalOverflow(page) {
    return page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth <= 1
    );
}

test.describe('SA-2 · EDC 聚合佐证卡 + 矩阵逾期顺延(本地 stub 真浏览器)', () => {
    test('工单详情:c.1 逐票卡与 EDC 收单聚合卡并排真渲染', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await boot(page, { hash: '#/client/1/wo' });
        await page.waitForSelector('#corrobRoot .panel.crb', { timeout: 15000 });

        const cards = page.locator('#corrobRoot .panel.crb');
        await expect(cards).toHaveCount(2);
        await expect(cards.nth(0)).toBeVisible();
        await expect(cards.nth(1)).toBeVisible();

        // EDC 卡(第二张):标题/金额/覆盖率/判据行逐项可见且非裸 key。
        const edcCard = cards.nth(1);
        await expect(edcCard.locator('h3')).toContainText('EDC 收单聚合');
        await expect(edcCard).toContainText('92,801.87');
        await expect(edcCard).toContainText('9 张结算票(计入 9)');
        await expect(edcCard).toContainText('2026-05-10 – 2026-05-28');
        await expect(edcCard).toContainText('覆盖 10.8%');
        await expect(edcCard).toContainText('聚合点名 1 项待核');
        await expect(edcCard.locator('.crb-basis')).toContainText('仅佐证');
        const display = await edcCard.evaluate((el) => window.getComputedStyle(el).display);
        expect(display).not.toBe('none');
        // 黄「覆盖不全」chip 在场(佐证不装完整)。
        await expect(edcCard.locator('.chip.w')).toContainText('覆盖不全');

        await page.screenshot({ path: path.join(ART, '01-corrob-cards-1280.png'), fullPage: true });

        await page.setViewportSize({ width: 390, height: 844 });
        expect(await noHorizontalOverflow(page)).toBe(true);
        await expect(cards.nth(1)).toBeVisible();
        await page.screenshot({ path: path.join(ART, '01-corrob-cards-390.png'), fullPage: true });
    });

    test('无 edc_corroboration 时 EDC 卡不渲染(现状诚实)', async ({ page }) => {
        ORDER_DETAIL.edc_corroboration = null;
        try {
            await page.setViewportSize({ width: 1280, height: 900 });
            await boot(page, { hash: '#/client/1/wo' });
            await page.waitForSelector('#corrobRoot .panel.crb', { timeout: 15000 });
            await expect(page.locator('#corrobRoot .panel.crb')).toHaveCount(1);
            await expect(page.locator('#corrobRoot')).not.toContainText('EDC 收单聚合');
        } finally {
            ORDER_DETAIL.edc_corroboration = EDC_CRB;
        }
    });

    test('捎带件:矩阵风险筛选按顺延后截止日判逾期(周六截止不标逾期)', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 900 });
        await boot(page);
        await page.waitForSelector('.mx-table', { timeout: 15000 });
        await expect(page.locator('.mx-row')).toHaveCount(2);

        await page.click('.mf-chip[data-filter="risk"]');
        // 周六(07-18)截止顺延到周一(07-20)=今天 → 不逾期,行被筛掉;
        // 顺延日 07-17 已过 → 逾期,行保留。
        await expect(page.locator('.mx-row[data-client-id="1"]')).toBeHidden();
        await expect(page.locator('.mx-row[data-client-id="2"]')).toBeVisible();
        await page.screenshot({
            path: path.join(ART, '02-matrix-risk-deferred.png'),
            fullPage: true,
        });

        await page.click('.mf-chip[data-filter="risk"]');
        await expect(page.locator('.mx-row[data-client-id="1"]')).toBeVisible();
    });

    for (const lang of ['th', 'en', 'ja']) {
        test(`四语(${lang}):EDC 卡文案不裸 key`, async ({ page }) => {
            await boot(page, { lang, hash: '#/client/1/wo' });
            await page.waitForSelector('#corrobRoot .panel.crb', { timeout: 15000 });
            const text = await page.locator('#corrobRoot').innerText();
            expect(text).not.toContain('crb_title_edc');
            expect(text).not.toContain('crb_tickets_edc');
            expect(text).not.toContain('crb_basis_edc');
            expect(text).not.toContain('crb_conflicts_edc');
        });
    }
});
