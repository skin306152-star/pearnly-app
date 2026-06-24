// E2E: Express 详情卡「默认·待核」提示 · 真站 pearnly.com 新 bundle · pearnly_e2e_3。
// 在 prod 真 bundle 上调 window.ExpressDetail.section(log):
//   account_review=true  → 渲染 .exp-je-note 待核提示(且文案是 i18n 解析后的真文,非原始键)
//   account_review=false → 不渲染待核提示(诚实:命中规则的科目不待核)
/* eslint-disable no-undef */
const { chromium } = require('playwright');
const BASE = 'https://pearnly.com';
const A = { username: 'pearnly_e2e_3', password: 'Pe@rnly-E2E-3p4' };

function log(direction, accountReview) {
    return {
        status: 'pending',
        created_at: '2026-06-24T02:00:00Z',
        request_body: {
            direction,
            doctype: direction === 'sales' ? 'IV' : 'RR',
            account_set: 'DATAT',
            base_amount: '1000.00',
            vat_amount: '70.00',
            total_amount: '1070.00',
            account_source: accountReview ? 'config_default' : 'category_map',
            account_review: accountReview,
            lines: [
                { acc: '11-04-02-00', side: 'D', amount: '1000.00', desc: 'ซื้อ' },
                { acc: '11-05-04-01', side: 'D', amount: '70.00', desc: 'ภาษีซื้อ' },
                { acc: '21-02-01-00', side: 'C', amount: '1070.00', desc: 'เจ้าหนี้' },
            ],
        },
        response_body: null,
    };
}

(async () => {
    const b = await chromium.launch();
    const p = await b.newPage();
    const tok = (await (await p.request.post(BASE + '/api/login', { data: A })).json()).token;
    await p.addInitScript((t) => localStorage.setItem('mrpilot_token', t), tok);
    await p.goto(BASE + '/home', { waitUntil: 'domcontentloaded' });
    await p.waitForFunction(
        () => window.ExpressDetail && typeof window.ExpressDetail.section === 'function',
        { timeout: 25000 }
    );
    await p.waitForFunction(() => typeof window.t === 'function', { timeout: 10000 });

    let pass = 0,
        fail = 0;
    const chk = (k, c) => {
        c ? pass++ : fail++;
        console.log((c ? 'PASS' : 'FAIL').padEnd(5), k);
    };

    const r = await p.evaluate(
        ({ purchaseReview, salesReview, ruleHit }) => {
            const sec = window.ExpressDetail.section;
            return {
                reviewText: window.t('expd-acct-review'),
                purchaseHtml: sec(purchaseReview),
                salesHtml: sec(salesReview),
                ruleHtml: sec(ruleHit),
            };
        },
        {
            purchaseReview: log('purchase', true),
            salesReview: log('sales', true),
            ruleHit: log('purchase', false),
        }
    );

    // i18n 真解析(非裸键),且非空
    chk('expd-acct-review i18n 已解析(非裸键)', r.reviewText && r.reviewText !== 'expd-acct-review');
    console.log('  待核文案=', JSON.stringify(r.reviewText));

    // account_review=true → 渲染 .exp-je-note + 含解析后的待核文案
    chk('采购待核 → 渲染 .exp-je-note', r.purchaseHtml.includes('exp-je-note'));
    chk('采购待核 → 含待核文案', r.purchaseHtml.includes(r.reviewText));
    chk('销项待核 → 渲染 .exp-je-note', r.salesHtml.includes('exp-je-note'));

    // account_review=false(规则命中) → 不渲染待核(诚实)
    chk('规则命中 → 不渲染 .exp-je-note', !r.ruleHtml.includes('exp-je-note'));

    console.log(`\n结果: ${pass} PASS · ${fail} FAIL`);
    await b.close();
    process.exit(fail ? 1 : 0);
})();
